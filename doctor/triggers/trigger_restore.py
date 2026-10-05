# Rebuilds the GUI triggers of a map from its script, with a round-trip proof for each one.
import bisect
import collections
import inspect
import os
import re
import tempfile
import time

from doctor.triggers import gui_render
from doctor.script import jass_ast
from doctor.script import jass_normal
from doctor.script import jass_setup
from doctor.script import lua_ast
from doctor.fix import editor_prep as PE
from doctor.triggers import wtg


HERE = os.path.dirname(os.path.abspath(__file__))
REF_DIR = os.path.normpath(os.path.join(HERE, '..', 'ref', '3.0'))
JASS, LUA = 'jass', 'lua'
CATEGORY = 'Restored triggers'
ICT, RIT = 'InitCustomTriggers', 'RunInitializationTriggers'
NOTE_RENAMED = 'Restored from the map script. The original name was removed by the protector.'
NOTE_TEXT = 'Restored from the map script as text (it could not be proven as GUI): %s'
NOTE_CUSTOM = 'Restored from the map script as text: its actions are code the trigger editor has no action for.'
ONLY_CUSTOM = 'every action is custom script'
NOTE_DISABLED = 'Disabled in the original map: the script keeps only its name.'
NOTE_INIT = ('Restored from the map script: what the InitTrig_ of %s did besides registering the trigger, run first '
             'at map initialization.')
EDITOR_GENERATED = re.compile(
    r'(?:InitGlobals|InitSounds|CreateRegions|CreateCameras|CreateAllDestructables|CreateAllItems|CreateAllUnits'
    r'|CreateUnitsForPlayer\d+|CreateBuildingsForPlayer\d+|CreateNeutralHostile(?:Buildings)?'
    r'|CreateNeutralPassive(?:Buildings)?|CreatePlayerBuildings|CreatePlayerUnits|InitTechTree(?:_Player\d+)?'
    r'|InitUpgrades(?:_Player\d+)?|InitCustomPlayerSlots|InitCustomTeams|InitAllyPriorities|Unit\d+_DropItems'
    r'|ItemTable\w*_DropItems|Doodad\d+_DropItems|main|config)$')
OBJECT_PREFIXES = ('gg_unit_', 'gg_rct_', 'gg_cam_', 'gg_snd_', 'gg_dest_', 'gg_item_')
RX_WORD = re.compile(r'[A-Za-z_]\w*')
RX_STRING_OR_COMMENT = re.compile(r'("(?:[^"\\]|\\.)*")|//[^\n]*')
RX_BANNER = re.compile(r'^//\s?Trigger:\s?(.*)$')
REGISTRATION_CALLS = re.compile(r'^(?:TriggerRegister\w+|TriggerAddCondition|TriggerAddAction|DisableTrigger)$')


class Restoration(object):
    def __init__(self, lang):
        self.ok = False
        self.reason = ''
        self.lang = lang
        self.triggers = None
        self.wtg = b''
        self.wct = b''
        self.header = ''
        self.expected_script = ''
        self.proofs = {}
        self.report = {}

    def __repr__(self):
        if self.reason:
            return 'Restoration(%s, not restorable: %s)' % (self.lang, self.reason)
        r = self.report
        return 'Restoration(%s, ok=%s, %d GUI, %d text, %d variables)' % (
            self.lang, self.ok, r.get('gui', 0), len(r.get('text', ())), r.get('variables', 0))


class _Fn(object):
    __slots__ = ('name', 'node', 'start', 'end', 'lead', 'text')

    def __init__(self, name, node, start, end, lead, text):
        self.name, self.node, self.start, self.end, self.lead, self.text = name, node, start, end, lead, text


class _Decl(object):
    __slots__ = ('name', 'type', 'is_array', 'is_constant', 'value', 'start', 'end', 'text', 'block')

    def __init__(self, name, type_, is_array, is_constant, value, start, end, text, block=None):
        self.name, self.type, self.is_array, self.is_constant = name, type_, is_array, is_constant
        self.value, self.start, self.end, self.text, self.block = value, start, end, text, block


def _normalize(script):
    if isinstance(script, (bytes, bytearray)):
        script = bytes(script).decode('utf-8', 'surrogateescape')
    script = script.replace('\r\n', '\n').replace('\r', '\n')
    if script.startswith('\ufeff'):
        script = script[1:]
    elif script.startswith('\xef\xbb\xbf'):
        script = script[3:]
    return script


def _line_starts(text):
    starts = [0]
    starts.extend(m.end() for m in re.finditer('\n', text))
    return starts


def _line_span(starts, text, first, last):
    a = starts[first - 1] if first - 1 < len(starts) else len(text)
    b = starts[last] if last < len(starts) else len(text)
    return a, b


class _Source(object):
    def __init__(self, text, lang):
        self.text, self.lang = text, lang
        self.functions = collections.OrderedDict()
        self.duplicates = []
        self.globals = collections.OrderedDict()
        self.blocks = []
        self.starts = _line_starts(text)
        if lang == LUA:
            self.tree = lua_ast.parse(text)
            self._lua()
        else:
            self.tree = jass_ast.parse(text)
            self._jass()
        self.texts = dict((n, f.text) for n, f in self.functions.items())
        self._names = frozenset(self.functions)
        self._refs = {}

    def _add(self, fn):
        if fn.name in self.functions:
            self.duplicates.append(fn.name)
            if self.lang == LUA:
                self.functions[fn.name] = fn
        else:
            self.functions[fn.name] = fn

    def _jass(self):
        tree, text, starts = self.tree, self.text, self.starts
        comment_lines = sorted(c.line for c in tree.comments)
        prev_end = 0
        for item in tree.items:
            t = type(item)
            last = item.end_line if t in (jass_ast.Function, jass_ast.Globals) else item.line
            i = bisect.bisect_right(comment_lines, prev_end)
            lead_line = comment_lines[i] if i < len(comment_lines) and comment_lines[i] < item.line else item.line
            if t is jass_ast.Function and not item.is_native:
                a, b = _line_span(starts, text, item.line, last)
                self._add(_Fn(item.name, item, a, b, starts[lead_line - 1], text[a:b]))
            elif t is jass_ast.Globals:
                block = _line_span(starts, text, item.line, last)
                self.blocks.append(block)
                for d in item.decls:
                    init = None if d.initializer is None else jass_ast.unparse(d.initializer)
                    a, b = _line_span(starts, text, d.line, d.line + (init or '').count('\n'))
                    if d.name not in self.globals:
                        self.globals[d.name] = _Decl(d.name, d.type, bool(d.is_array), bool(d.is_constant), init,
                                                     a, b, text[a:b], block)
            prev_end = last

    def _lua(self):
        text, starts = self.text, self.starts
        for s in self.tree.body:
            t = type(s)
            if t is lua_ast.FunctionStmt and re.match(r'^[A-Za-z_]\w*$', s.name) and not s.is_local:
                a, b = s.span
                lead = a
                if s.leading_comments:
                    line = min(c.line for c in s.leading_comments)
                    ls = starts[line - 1]
                    first = min(s.leading_comments, key=lambda c: c.line)
                    k = text.find(first.text, ls)
                    if k >= 0 and not text[ls:k].strip():
                        lead = ls
                self._add(_Fn(s.name, s, a, b, lead, text[a:b]))
            elif (t is lua_ast.AssignStmt and len(s.targets) == 1 and len(s.values) == 1 and
                  type(s.targets[0]) is lua_ast.Name):
                name = s.targets[0].name
                if name not in self.globals:
                    a, b = s.span
                    self.globals[name] = _Decl(name, None, False, False, lua_ast.canonical(s.values[0]), a, b,
                                               text[a:b])

    def refs(self, name):
        r = self._refs.get(name)
        if r is None:
            words = set(RX_WORD.findall(_code_only(self.texts[name], self.lang)))
            r = self._refs[name] = (words & self._names) - {name}
        return r

    def calls(self, name):
        f = self.functions.get(name)
        if f is None:
            return None
        out = []
        if self.lang == LUA:
            for s in f.node.body:
                if type(s) is not lua_ast.CallStmt or type(s.call.func) is not lua_ast.Name or s.call.method:
                    return None
                out.append((s.call.func.name, [lua_ast.canonical(a) for a in s.call.args]))
            return out
        if f.node.locals:
            return None
        for s in f.node.body:
            if type(s) is jass_ast.CommentStmt:
                continue
            if type(s) is not jass_ast.CallStmt:
                return None
            out.append((s.call.name, [jass_ast.unparse(a) for a in s.call.args]))
        return out


RX_JASS_NOISE = re.compile(r'//[^\n]*|"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'', re.S)
RX_LUA_NOISE = re.compile(r'--\[(=*)\[.*?\]\1\]|--[^\n]*|\[(=*)\[.*?\]\2\]|"(?:[^"\\\n]|\\.)*"|\'(?:[^\'\\\n]|\\.)*\'',
                          re.S)


def _code_only(text, lang):
    return (RX_LUA_NOISE if lang == LUA else RX_JASS_NOISE).sub(' ', text)


def _identifier_ok(name, ident):
    return bool(name) and gui_render.trigger_identifier(name) == ident


def _banner(src, names):
    fns = [src.functions[n] for n in names if n in src.functions]
    if not fns or src.lang == LUA:
        return None, ''
    comments = [c.rstrip() for c in (min(fns, key=lambda f: f.start).node.leading_comments or ())]
    for k, c in enumerate(comments):
        m = RX_BANNER.match(c)
        if m:
            desc = []
            rest = comments[k + 1:]
            if rest and rest[0] == '//':
                for c2 in rest[1:]:
                    if c2.startswith('//=='):
                        break
                    desc.append(c2[3:] if c2[2:3] == ' ' else c2[2:])
            return m.group(1), '\r\n'.join(desc)
    return None, ''


def _skeleton_by_name(src):
    fns = src.functions
    if ICT not in fns:
        return None
    sk = {'by': 'name', 'reason': '', 'renames': {}}
    calls = src.calls(ICT)
    if calls is None:
        sk['reason'] = 'InitCustomTriggers does more than call the InitTrig_ functions'
        return sk
    inits = []
    for callee, args in calls:
        if args or not callee.startswith('InitTrig_') or callee not in fns or callee in inits:
            sk['reason'] = 'InitCustomTriggers calls %s, not a trigger InitTrig_' % callee
            return sk
        inits.append(callee)
    sk['triggers'] = inits
    sk['init_custom_triggers'] = ICT
    sk['run_initialization_triggers'] = RIT if RIT in fns else None
    sk['init_globals'] = 'InitGlobals' if 'InitGlobals' in fns else None
    return sk


def _structure_body(f):
    lines = f.text.split('\n')
    while lines and not lines[-1].strip():
        lines.pop()
    return '\n'.join(lines[1:-1]) + '\n' if len(lines) > 2 else ''


RX_CREATE_TRIGGER = re.compile(r'^\s*set\s+(\w+)\s*=\s*CreateTrigger\s*\(\s*\)', re.M)
NO_SKELETON = 'no editor skeleton: no InitCustomTriggers by name or by structure'


def _creates_trigger(body, triggers, first=True):
    made = [m.group(1) for m in RX_CREATE_TRIGGER.finditer(body)]
    found = next((x for x in made if x in triggers), None)
    if found is None or (first and made[0] != found):
        return None
    return found if 'TriggerAddAction' in body or 'TriggerAddCondition' in body else None


LABEL_LIMIT = 48
RX_LABEL_NOISE = re.compile(r"[^A-Za-z0-9 '.,!?+&-]")
RX_CAMEL = re.compile(r'[A-Z][a-z0-9]+|[A-Z]+(?![a-z])')
RX_REGISTRATION_NAME = re.compile(r'^(?:Blz)?TriggerRegister\w+$')
REGION_EVENTS = ('TriggerRegisterEnterRectSimple', 'TriggerRegisterLeaveRectSimple', 'TriggerRegisterEnterRegion',
                 'TriggerRegisterLeaveRegion')
TIMER_EVENTS = ('TriggerRegisterTimerEventPeriodic', 'TriggerRegisterTimerEventSingle', 'TriggerRegisterTimerEvent')
EVENT_LABELS = {'TriggerRegisterDeathEvent': 'Destructible Dies', 'TriggerRegisterDialogEvent': 'Dialog Click',
                'TriggerRegisterDialogEventBJ': 'Dialog Click', 'TriggerRegisterDialogButtonEvent': 'Dialog Button',
                'TriggerRegisterUnitInRange': 'Unit In Range', 'TriggerRegisterUnitInRangeSimple': 'Unit In Range',
                'TriggerRegisterPlayerSelectionEventBJ': 'Unit Selection',
                'TriggerRegisterGameStateEventTimeOfDay': 'Time Of Day',
                'TriggerRegisterUnitLifeEvent': 'Unit Life', 'TriggerRegisterUnitManaEvent': 'Unit Mana',
                'TriggerRegisterUnitStateEvent': 'Unit State'}
SETUP_CODE = 'Map Setup Code'


def _label(text):
    text = ' '.join(RX_LABEL_NOISE.sub(' ', text).split())
    if len(text) > LABEL_LIMIT:
        text = text[:LABEL_LIMIT + 1].rsplit(' ', 1)[0].rstrip(" .,!?+&-'")
    return text


def _event_label(call, regions):
    name = call.name
    args = [jass_normal.bare(a) for a in call.args]
    codes = [a.name for a in args if type(a) is jass_ast.Name and a.name.startswith('EVENT_')]
    if name == 'TriggerRegisterPlayerChatEvent' and len(args) > 2 and type(args[2]) is jass_ast.Literal and \
            args[2].kind == 'string':
        said = ' '.join(str(args[2].value).split())
        return 'Chat ' + (said.lstrip('-!/.').strip() or said)
    if codes:
        words = codes[0].split('_')[1:]
        if words[:2] in (['PLAYER', 'UNIT'], ['PLAYER', 'HERO']):
            words = words[1:]
        return ' '.join(w.capitalize() for w in words)
    if name in REGION_EVENTS:
        rect = args[1].name if len(args) > 1 and type(args[1]) is jass_ast.Name else None
        return '%s Region%s' % ('Enter' if 'Enter' in name else 'Leave',
                                '' if rect is None else ' %03d' % regions.setdefault(rect, len(regions) + 1))
    if name in TIMER_EVENTS:
        periodic = 'Periodic' in name or (len(args) > 2 and type(args[2]) is jass_ast.Literal and
                                          args[2].text == 'true')
        seconds = jass_normal.number(args[1]) if len(args) > 1 else None
        return ('Every' if periodic else 'Elapsed') + ('' if seconds is None else ' %g Seconds' % seconds[1])
    if name in ('TriggerRegisterTimerExpireEventBJ', 'TriggerRegisterTimerExpireEvent'):
        return 'Timer Expires'
    if name == 'BlzTriggerRegisterPlayerKeyEvent':
        key = next((a.name for a in args if type(a) is jass_ast.Name and a.name.startswith('OSKEY_')), None)
        return 'Key' + ('' if key is None else ' ' + key[len('OSKEY_'):].capitalize())
    if name in EVENT_LABELS:
        return EVENT_LABELS[name]
    words = [w for w in RX_CAMEL.findall(re.sub(r'^(?:Blz)?TriggerRegister', '', name))
             if w not in ('BJ', 'Simple', 'Event')]
    return ' '.join(words) or name


def _condition_object(src, name, object_names):
    seen, queue = set(), [name]
    while queue:
        x = queue.pop(0)
        if x in seen or x not in src.functions:
            continue
        seen.add(x)
        for node in jass_ast.walk(src.functions[x].node):
            if type(node) is jass_ast.Literal and node.kind in ('rawcode', 'integer'):
                value = jass_normal.number(node)
                code = jass_normal.integer_text(value[1]) if value is not None else ''
                if code[:1] == "'" and code[1:-1] in object_names:
                    return object_names[code[1:-1]]
            elif type(node) is jass_ast.Call and node.name in src.functions:
                queue.append(node.name)
    return None


def _trigger_labels(src, order, init_like, reach, rit_globals, object_names):
    regions, labels = {}, {}
    for f in order:
        if f not in init_like:
            labels[f] = SETUP_CODE
            continue
        calls = [x for x in jass_ast.walk(src.functions[f].node) if type(x) is jass_ast.Call]
        events = [x for x in calls if RX_REGISTRATION_NAME.match(x.name)]
        if not events:
            if init_like[f] in rit_globals:
                labels[f] = 'Map Initialization'
            continue
        label = _event_label(events[0], regions)
        condition = next((r.name for x in calls if x.name == 'TriggerAddCondition' for r in jass_ast.walk(x)
                          if type(r) is jass_ast.FuncRef), None)
        thing = None
        if condition and object_names and not label.startswith('Chat '):
            thing = _condition_object(src, condition, object_names)
        labels[f] = label if not thing else '%s %s' % (label, thing)
    named_by = collections.defaultdict(set)
    globals_ = dict((g, f) for f, g in init_like.items())
    for f in order:
        for x in reach.get(f, ()):
            for word in set(RX_WORD.findall(_code_only(src.texts[x], JASS))):
                if word in globals_ and globals_[word] != f:
                    named_by[globals_[word]].add(f)
    for f in order:
        users = named_by.get(f, ())
        if f not in labels and len(users) == 1:
            user = next(iter(users))
            if user in labels and labels[user] != SETUP_CODE and not labels[user].startswith('Run By '):
                labels[f] = 'Run By ' + labels[user]
    return labels


def _named_triggers(order, labels):
    clean = dict((f, _label(x)) for f, x in labels.items())
    count = collections.Counter(x for x in clean.values() if x)
    used, taken, out = collections.Counter(), set(), []
    for k, f in enumerate(order, 1):
        label = clean.get(f)
        name = 'T%03d' % k
        if label:
            if count[label] > 1:
                used[label] += 1
                label = '%s %0*d' % (label, max(2, len(str(count[label]))), used[label])
            if gui_render.trigger_identifier(label).lower() not in taken:
                name = label
        taken.add(gui_render.trigger_identifier(name).lower())
        out.append(name)
    return out


def _skeleton_by_structure(src, extras=(), object_names=None):
    sk = {'by': 'structure', 'reason': '', 'renames': {}}
    if src.lang != JASS:
        sk['reason'] = 'no editor skeleton: no InitCustomTriggers (the search by structure is for JASS)'
        return sk
    if 'main' not in src.functions:
        sk['reason'] = 'no main function'
        return sk
    funcs = collections.OrderedDict((n, _structure_body(f)) for n, f in src.functions.items())
    triggers = set(n for n, d in src.globals.items() if d.type == 'trigger' and not d.is_array)
    init_like, loose = collections.OrderedDict(), {}
    for n, body in funcs.items():
        if n in ('main', 'config'):
            continue
        t = _creates_trigger(body, triggers)
        if t:
            init_like[n] = t
        else:
            t = _creates_trigger(body, triggers, False)
            if t:
                loose[n] = t
    main_calls = re.findall(r'call\s+(\w+)\s*\(', funcs['main'])
    main_called = set(main_calls)
    inits = set(init_like) | set(loose) | set(extras)

    def only(body, test):
        lines = [x.strip() for x in body.split('\n') if x.strip() and not x.strip().startswith('//')]
        return bool(lines) and all(test(x) for x in lines)

    ict = next((n for n, body in funcs.items() if n in main_called and only(
        body, lambda x: re.match(r'call\s+(\w+)\s*\(\s*\)$', x) and
        re.match(r'call\s+(\w+)', x).group(1) in inits)), None)
    if ict is None:
        sk['reason'] = NO_SKELETON
        return sk
    rit = next((n for n, body in funcs.items() if n in main_called and n != ict and only(
        body, lambda x: re.match(r'call\s+ConditionalTriggerExecute\s*\(\s*\w+\s*\)$', x))), None)
    if rit is None:
        run = re.search(r'call\s+%s\s*\(\s*\)[^\n]*\n((?:\s*call\s+ConditionalTriggerExecute\s*\(\s*\w+\s*\)[^\n]*\n)+)'
                        % re.escape(ict), funcs['main'])
        ran = re.findall(r'ConditionalTriggerExecute\s*\(\s*(\w+)\s*\)', run.group(1)) if run else None
        rit = next((n for n, body in funcs.items() if n not in main_called and n not in (ict, 'main') and ran and
                    re.findall(r'call\s+ConditionalTriggerExecute\s*\(\s*(\w+)\s*\)', body) == ran and only(
                        body, lambda x: re.match(r'call\s+ConditionalTriggerExecute\s*\(\s*\w+\s*\)$', x))), None)
    called = []
    for x in re.findall(r'call\s+(\w+)\s*\(', funcs[ict]):
        if x not in called:
            called.append(x)
            if x in loose:
                init_like[x] = loose[x]
    inits = set(init_like) | set(extras)
    ren = {}
    order = [x for x in called if x in inits] + [x for x in init_like if x not in called]
    apart = set(order) | set(init_like.values()) | {ict, rit, 'main', 'config'}
    reach, claimed = {}, set()
    for f in order:
        seen, stack = [], [f]
        while stack:
            x = stack.pop()
            if x in seen:
                continue
            seen.append(x)
            for r in re.findall(r'\b(\w+)\b', funcs[x]):
                if r in funcs and r not in apart and r not in claimed and r not in seen:
                    stack.append(r)
        reach[f] = seen
        claimed.update(seen[1:])
    rit_globals = set(re.findall(r'ConditionalTriggerExecute\s*\(\s*(\w+)\s*\)', funcs[rit])) if rit else set()
    if callable(object_names):
        try:
            object_names = object_names()
        except Exception:
            object_names = None
    names = _named_triggers(order, _trigger_labels(src, order, init_like, reach, rit_globals, object_names or {}))
    idents = [gui_render.trigger_identifier(x) for x in names]
    sk['labels'] = {}
    for f, name, ident in zip(order, names, idents):
        ren[f] = 'InitTrig_' + ident
        sk['labels'][ren[f]] = name
        if f in init_like:
            ren[init_like[f]] = 'gg_trg_' + ident
    ren[ict] = ICT
    if rit:
        ren[rit] = RIT
    for f, base in zip(order, idents):
        n = 0
        for x in reach[f][1:]:
            if x in ren:
                continue
            n += 1
            boolean = src.functions[x].node.return_type == 'boolean'
            ren[x] = ('Trig_%s_Aux%03d' % (base, n)) if (n > 1 or boolean) else ('Trig_%s_Actions' % base)
    for n in src.globals:
        if n not in ren and not n.startswith(('bj_', 'gg_', 'udg_')):
            ren[n] = 'udg_' + n
    if ict in main_calls:
        i = main_calls.index(ict)
        if i > 0 and main_calls[i - 1] in funcs and main_calls[i - 1] not in ren:
            ren[main_calls[i - 1]] = 'InitGlobals'
    clash = sorted(set(ren.values()) & (set(src.functions) | set(src.globals)) - set(ren))
    twice = [x for x, k in collections.Counter(ren.values()).items() if k > 1]
    if clash or twice:
        sk['reason'] = 'the editor names %s already exist in the script' % ', '.join((clash + twice)[:3])
        return sk
    sk['renames'] = ren
    sk['triggers'] = [ren[f] for f in called if f in inits]
    sk['init_custom_triggers'] = ICT
    sk['run_initialization_triggers'] = RIT if rit else None
    sk['init_globals'] = 'InitGlobals' if 'InitGlobals' in ren.values() else None
    return sk


RX_RENAME = re.compile(r'"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\'|//[^\r\n]*|\$[0-9A-Fa-f]+|'
                       r'0[xX][0-9A-Fa-f]+|[0-9]+\.[0-9]*|\.[0-9]+|[0-9]+|[A-Za-z_][A-Za-z0-9_]*|[(),]', re.S)
RX_ARGUMENT_END = re.compile(r'[ \t]*[,)]')
NAME_ARGUMENTS = {'ExecuteFunc': 0, 'TriggerRegisterVariableEvent': 1}


def _rename(text, renames):
    if not renames:
        return text
    out, pos, calls, prev = [], 0, [], ''
    for m in RX_RENAME.finditer(text):
        tok = m.group(0)
        c = tok[0]
        new = None
        if c == '(':
            calls.append([prev, 0])
        elif c == ',':
            if calls:
                calls[-1][1] += 1
        elif c == ')':
            if calls:
                calls.pop()
        elif c == '"':
            if (calls and NAME_ARGUMENTS.get(calls[-1][0]) == calls[-1][1] and tok[1:-1] in renames and
                    prev in ('(', ',') and RX_ARGUMENT_END.match(text, m.end())):
                new = '"%s"' % renames[tok[1:-1]]
        elif c.isalpha() or c == '_':
            new = renames.get(tok)
        if new is not None:
            out.append(text[pos:m.start()])
            out.append(new)
            pos = m.end()
        prev = tok
    out.append(text[pos:])
    return ''.join(out)


TRIGGER_SETUP = re.compile(r'^(?:TriggerRegister\w+|BlzTriggerRegister\w+|TriggerAddCondition|TriggerAddAction'
                           r'|DisableTrigger)$')


def _plain(e):
    while type(e) is jass_ast.Paren:
        e = e.inner
    return e


def _is_create(s):
    if type(s) is jass_ast.SetStmt and type(s.target) is jass_ast.Name:
        v = _plain(s.value)
        if type(v) is jass_ast.Call and v.name == 'CreateTrigger' and not v.args:
            return s.target.name
    return None


def _editor_handler(call):
    if len(call.args) != 2:
        return False
    h = _plain(call.args[1])
    if call.name == 'TriggerAddAction':
        return type(h) is jass_ast.FuncRef
    return (type(h) is jass_ast.Call and h.name in ('Condition', 'Filter') and len(h.args) == 1 and
            type(_plain(h.args[0])) is jass_ast.FuncRef)


def _touch(s, names):
    used = frozenset(x.name for x in jass_ast.walk(s) if type(x) is jass_ast.Name and x.name in names)
    if used and type(s) is jass_ast.SetStmt and type(s.target) is jass_ast.Name and s.target.name in used and \
            not any(type(x) is jass_ast.Name and x.name == s.target.name for x in jass_ast.walk(s.value)):
        return used, s.target.name
    return used, None


def _read_first(touches):
    seen, bad = set(), set()
    for used, assigned in touches:
        new = used - seen
        if new:
            bad |= new - {assigned}
            seen |= new
    return bad


def _literal_decl(d):
    v = None if d.initializer is None else _plain(d.initializer)
    if type(v) is jass_ast.Unary and v.op in '-+':
        v = _plain(v.operand)
    return v is None or type(v) is jass_ast.Literal


def _returns(stmts):
    return any(type(x) is jass_ast.ReturnStmt for s in stmts for x in jass_ast.walk(s))


def _assigned(stmts):
    out = set()
    for s in stmts:
        for x in jass_ast.walk(s):
            if type(x) is jass_ast.SetStmt:
                t = _plain(x.target)
                t = _plain(t.base) if type(t) is jass_ast.Index else t
                if type(t) is jass_ast.Name:
                    out.add(t.name)
    return out


def _wrapper_names(src, firsts, idents):
    taken = set(src.functions) | set(src.globals)
    out = []
    for s in firsts:
        base = gui_render.trigger_identifier(s.call.name if type(s) is jass_ast.CallStmt else 'Init')
        ident, k = base, 1
        while ident in idents or 'InitTrig_' + ident in taken or 'gg_trg_' + ident in taken:
            k += 1
            ident = '%s_%d' % (base, k)
        idents.add(ident)
        out.append(ident)
    return out


def _declared(src, text, wanted):
    edits = []
    for x, nxt, last in wanted:
        d = src.globals.get(nxt) if nxt else None
        at = d.start if d is not None else (src.globals[last].end if last in src.globals else None)
        if at is not None:
            edits.append((at, x))
    for _k, (at, x) in sorted(enumerate(edits), key=lambda e: (e[1][0], e[0]), reverse=True):
        text = text[:at] + '    trigger gg_trg_%s = null\n' % x + text[at:]
    return text, ['gg_trg_' + x for _a, x in edits]


def _inlined_setup(src):
    main = src.functions.get('main')
    if src.lang != JASS or main is None or not main.node.body or main.node.params:
        return None, ''
    node, text, starts = main.node, src.text, src.starts
    body = [s for s in node.body if type(s) is not jass_ast.CommentStmt]
    n = len(body)
    triggers = set(x for x, d in src.globals.items() if d.type == 'trigger' and not d.is_array)
    ours = set(x for x in triggers if not x.startswith('bj_'))
    locs = collections.OrderedDict((d.name, d) for d in node.locals)

    def on(s):
        if type(s) is jass_ast.CallStmt and TRIGGER_SETUP.match(s.call.name) and s.call.args and \
                type(s.call.args[0]) is jass_ast.Name:
            return s.call.args[0].name
        return None

    def extent(c, t, limit):
        regs = [k for k in range(c + 1, limit) if on(body[k]) == t]
        ok = any(body[k].call.name in ('TriggerAddAction', 'TriggerAddCondition') and _editor_handler(body[k].call)
                 for k in regs)
        return (regs[-1] + 1 if regs else c + 1), ok

    made = [(k, _is_create(s)) for k, s in enumerate(body)]
    made = [(k, t) for k, t in made if t in ours]
    blocks = []
    for i, (c, t) in enumerate(made):
        e, ok = extent(c, t, made[i + 1][0] if i + 1 < len(made) else n)
        if ok:
            blocks.append([c, e, t])
    if not blocks:
        return None, ''
    for i, b in enumerate(blocks):
        b[1] = extent(b[0], b[2], blocks[i + 1][0] if i + 1 < len(blocks) else n)[0]
    twice = [t for t, k in collections.Counter(b[2] for b in blocks).items() if k > 1]
    if twice:
        return None, 'main creates the trigger %s twice' % twice[0]
    touches = [_touch(s, locs) for s in body]
    creates = [any(_is_create(x) not in (None,) + tuple(locs) for x in jass_ast.walk(s)
                   if type(x) is jass_ast.SetStmt) for s in body]

    def reads(a, b):
        return _read_first(touches[a:b])

    def called(k):
        s = body[k]
        if type(s) is not jass_ast.CallStmt or s.call.args or s.call.name in ('main', 'config'):
            return None
        f = src.functions.get(s.call.name)
        return None if f is None else _creates_trigger(_structure_body(f), triggers)

    def head(c, e, lo):
        for a in range(c, lo - 1, -1):
            if a < c and creates[a]:
                return None
            if not reads(a, e):
                return a
        return None

    def initializers(s, lo, e, prev):
        while s > lo and touches[s - 1][1] and not creates[s - 1] and not reads(s - 1, e) and \
                not any(touches[s - 1][1] in touches[k][0] for k in range(prev, s - 1)):
            s -= 1
        return s

    def tail(a, e, limit):
        seen = set()
        for k in range(a, limit):
            used, assigned = touches[k]
            new = used - seen
            if new - {assigned} and k >= e:
                return k
            seen |= new
        return limit

    def between(x, y):
        out = []
        for k in range(x, y):
            t = called(k)
            if t:
                out.append(('call', k, k + 1, t))
            elif out and out[-1][0] == 'wrap' and out[-1][2] == k:
                out[-1] = ('wrap', out[-1][1], k + 1, None)
            else:
                out.append(('wrap', k, k + 1, None))
        return out

    entries, why = [], 'the setup inlined into main reads a local of main before setting it: %s'
    c, e, t = blocks[0]
    a = head(c, e, 0)
    if a is None:
        return None, why % ', '.join(sorted(reads(c, e)))
    a = start = initializers(a, 0, e, 0)
    while start > 0 and called(start - 1):
        start -= 1
    entries.extend(('call', k, k + 1, called(k)) for k in range(start, a))
    for (c, e, t), (c2, e2, _t) in zip(blocks, blocks[1:]):
        low = max([e] + [k + 1 for k in range(e, c2) if creates[k]])
        s = next((x for x in range(min(tail(a, e, c2), c2), low - 1, -1) if not reads(x, e2)), None)
        if s is None and low > e:
            low = e
            s = next((x for x in range(min(tail(a, e, c2), c2), low - 1, -1) if not reads(x, e2)), None)
        if s is None:
            return None, why % ', '.join(sorted(reads(e, e2)))
        s = initializers(s, low, e2, a)
        last = max([k + 1 for k in range(e, s) if touches[k][0]] + [e])
        first = min([k for k in range(s, c2) if touches[k][0]] + [c2])
        entries.append(('group', a, last, t))
        entries.extend(between(last, first))
        a = first
    c, e, t = blocks[-1]

    def cte(k):
        s = body[k]
        if type(s) is jass_ast.CallStmt and s.call.name == 'ConditionalTriggerExecute' and len(s.call.args) == 1 and \
                type(s.call.args[0]) is jass_ast.Name:
            return s.call.args[0].name
        return None

    q = next((k for k in range(e, n) if cte(k)), None)
    rit = []
    if q is not None:
        last = max([k + 1 for k in range(e, q) if touches[k][0]] + [e])
        done = set(x[3] for x in entries if x[3]) | {t} | set(called(k) for k in range(last, q) if called(k))
        if tail(a, e, last) == last and cte(q) in done:
            entries.append(('group', a, last, t))
            entries.extend(between(last, q))
            end = after = q
            while after < n and cte(after) in done:
                after += 1
            rit = list(range(q, after))
        else:
            q = None
    if q is None:
        entries.append(('group', a, e, t))
        end = e
        while end < n and called(end):
            end += 1
        entries.extend(('call', k, k + 1, called(k)) for k in range(e, end))
        after = end
    if _returns(body[start:end]):
        return None, 'main returns inside the trigger setup inlined into it'
    groups = [x for x in entries if x[0] == 'group']
    used = [set().union(*[touches[k][0] for k in range(g[1], g[2])]) for g in groups]
    moved = set().union(*used)
    bad = [x for x in moved if locs[x].is_array or not _literal_decl(locs[x])]
    if bad:
        return None, 'the setup inlined into main uses its local %s, which cannot move (%s)' % (
            bad[0], 'an array' if locs[bad[0]].is_array else 'set by a call at the start of main')
    bad = _read_first(touches[after:]) & moved
    if bad:
        return None, 'main reads its local %s after the setup inlined into it, which set it' % sorted(bad)[0]
    in_main = set().union(*[touches[k][0] for k in list(range(start)) + list(range(after, n))])
    wraps = [x for x in entries if x[0] == 'wrap']
    ran = [('ConditionalTriggerExecute', [cte(k)]) for k in rit]
    words = collections.Counter(RX_WORD.findall(_code_only(text, JASS))) if rit else {}
    reused = next((f for f in src.functions if f != 'main' and words.get(f) == 1 and src.calls(f) == ran), None)
    idents = [re.match(r'gg_trg_(\w+)$', g[3]) for g in groups]
    taken = set(src.functions) | set(src.globals)
    by = 'name'
    if (None not in idents and all(_identifier_ok(m.group(1), m.group(1)) for m in idents) and
            all(body[x[1]].call.name.startswith('InitTrig_') for x in entries if x[0] == 'call')):
        names = ['InitTrig_' + m.group(1) for m in idents]
        known = set(m.group(1) for m in idents) | set(body[x[1]].call.name[9:] for x in entries if x[0] == 'call')
        wrap_names = ['InitTrig_' + x for x in _wrapper_names(src, [body[w[1]] for w in wraps], known)]
        ict, rit_name = ICT, (RIT if rit else None)
        if len(set(names)) < len(names) or (set(names) | {ict, rit_name}) & (taken - {reused}):
            by = 'structure'
    else:
        by = 'structure'
    if by == 'structure':
        names = ['devo_it%03d' % k for k in range(1, len(groups) + 1)]
        wrap_names = ['devo_ix%03d' % k for k in range(1, len(wraps) + 1)]
        ict, rit_name = 'devo_ict', ('devo_rit' if rit else None)
        clash = sorted((set(names) | set(wrap_names) | {ict, rit_name}) & taken)
        if clash:
            return None, 'the script already has %s' % clash[0]
    if reused:
        rit_name = reused

    def off(k):
        return starts[(body[k].line if k < n else node.end_line) - 1]

    decl = {}
    for d in node.locals:
        a0, b0 = _line_span(starts, text, d.line, d.line + (
            0 if d.initializer is None else jass_ast.unparse(d.initializer).count('\n')))
        decl[d.name] = (a0, b0)
    gi, wi, ui = iter(names), iter(wrap_names), iter(used)
    functions, calls, wanted = [], [], []
    for i, (kind, a0, b0, t) in enumerate(entries):
        if kind == 'call':
            calls.append(body[a0].call.name)
            continue
        name = next(gi) if kind == 'group' else next(wi)
        u = next(ui) if kind == 'group' else ()
        calls.append(name)
        functions.append('function %s takes nothing returns nothing\n%s%sendfunction\n' % (
            name, ''.join(text[decl[x][0]:decl[x][1]] for x in locs if x in u), text[off(a0):off(b0)]))
        if kind == 'wrap' and by == 'name':
            nxt = next((x[3] for x in entries[i + 1:] if x[3]), None)
            wanted.append((name[9:], nxt, next((x[3] for x in reversed(entries[:i]) if x[3]), None)))
    functions.append('function %s takes nothing returns nothing\n%sendfunction\n' % (
        ict, ''.join('    call %s()\n' % x for x in calls)))
    if rit and not reused:
        functions.append('function %s takes nothing returns nothing\n%sendfunction\n' % (
            rit_name, ''.join('    call ConditionalTriggerExecute(%s)\n' % cte(k) for k in rit)))
    top_line = node.body[0].line
    only_moved = [decl[x] for x in moved - in_main]
    top = _remove_spans(text[main.start:starts[top_line - 1]], [(a0 - main.start, b0 - main.start)
                                                                 for a0, b0 in only_moved])
    new_main = (top + text[starts[top_line - 1]:off(start)] + '    call %s()\n' % ict +
                ('    call %s()\n' % rit_name if rit else '') + text[off(after):off(n)] + text[off(n):main.end])
    head_text, added = _declared(src, text[:main.lead], wanted)
    new = head_text + '\n'.join(functions) + '\n' + text[main.lead:main.start] + new_main + text[main.end:]
    extras = sum(1 for (kind, a0, b0, t) in groups
                 if any(_is_create(body[k]) != t and on(body[k]) != t for k in range(a0, b0)))
    info = {'host': 'main', 'proof': 'main_inlined', 'by': by, 'triggers': len(entries),
            'calls': sum(1 for x in entries if x[0] == 'call'), 'wrappers': wrap_names, 'with_extras': extras,
            'locals': sorted(moved), 'rit': len(rit), 'text': new, 'ict': ict, 'rit_name': rit_name,
            'new': names + wrap_names + [ict] + ([rit_name] if rit and not reused else []), 'added_globals': added,
            'reused': [reused] if reused else [], 'original': src}
    return new, info


DEFERRED = frozenset(('TriggerAddAction', 'TriggerAddCondition', 'TimerStart'))
RX_EXECUTE = re.compile(r'ExecuteFunc\s*\(\s*"(\w+)"\s*\)')


def _runs_now(src, s):
    roots = set()
    deferred = type(s) is jass_ast.CallStmt and s.call.name in DEFERRED
    for x in jass_ast.walk(s):
        if type(x) is jass_ast.Call and x.name in src.functions:
            roots.add(x.name)
        elif type(x) is jass_ast.FuncRef and not deferred and x.name in src.functions:
            roots.add(x.name)
        elif type(x) is jass_ast.Literal and x.kind == 'string' and x.text[1:-1] in src.functions:
            roots.add(x.text[1:-1])
    seen, stack = set(), list(roots)
    while stack:
        f = stack.pop()
        if f in seen:
            continue
        seen.add(f)
        stack.extend(src.refs(f) - seen)
        stack.extend(x for x in RX_EXECUTE.findall(src.texts[f]) if x in src.functions and x not in seen)
    return seen


def _late_created(src):
    main = src.functions.get('main')
    if src.lang != JASS or main is None:
        return None
    made = [n for n, d in src.globals.items() if d.type == 'trigger' and not d.is_array and not d.is_constant and
            d.value is not None and re.sub(r'\s+', '', d.value) == 'CreateTrigger()']
    if not made:
        return None
    wanted = set(made)
    body = [x for x in main.node.body if type(x) is not jass_ast.CommentStmt]
    first, early, words = {}, set(), {}
    for k, st in enumerate(body):
        names = set(x.name for x in jass_ast.walk(st) if type(x) is jass_ast.Name and x.name in wanted)
        for t in names:
            if t in first:
                continue
            setup = (type(st) is jass_ast.CallStmt and TRIGGER_SETUP.match(st.call.name) and st.call.args and
                     type(st.call.args[0]) is jass_ast.Name and st.call.args[0].name == t)
            first[t] = k if setup and names == {t} and t not in early else None
        for f in _runs_now(src, st):
            if f not in words:
                words[f] = set(RX_WORD.findall(_code_only(src.texts[f], JASS))) & wanted
            early |= words[f]
    moved = [t for t in made if first.get(t) is not None]
    if not moved:
        return None
    lines = src.text.split('\n')
    inserts = collections.defaultdict(list)
    for t in moved:
        inserts[body[first[t]].line].append(t)
    for line in sorted(inserts, reverse=True):
        indent = re.match(r'[ \t]*', lines[line - 1]).group(0)
        lines[line - 1:line - 1] = ['%sset %s=CreateTrigger()' % (indent, t) for t in inserts[line]]
    text = '\n'.join(lines)
    edits = []
    for t in moved:
        d = src.globals[t]
        new = re.sub(r'=\s*CreateTrigger\s*\(\s*\)', '=null', d.text, 1)
        if new == d.text:
            return None
        edits.append((d.start, d.end, new))
    for a, b, new in sorted(edits, reverse=True):
        text = text[:a] + new + text[b:]
    return {'original': src, 'source': _Source(text, JASS), 'moved': moved}


def _late_created_proof(info):
    orig, new, moved = info['original'], info['source'], set(info['moved'])
    problems = []
    for name, d in orig.globals.items():
        e = new.globals.get(name)
        if e is None:
            problems.append('global %s is gone' % name)
        elif name in moved:
            if (e.value or '').strip() != 'null' or re.sub(r'\s+', '', d.value or '') != 'CreateTrigger()':
                problems.append('global %s: %r' % (name, e.text.strip()))
        elif e.text != d.text:
            problems.append('global %s changed' % name)
    changed = [f for f, x in orig.texts.items() if f != 'main' and new.texts.get(f) != x]
    if changed or set(new.functions) != set(orig.functions):
        problems.append('functions changed: %s' % ', '.join(changed[:3]))
    old = [x for x in orig.functions['main'].node.body if type(x) is not jass_ast.CommentStmt]
    body = [x for x in new.functions['main'].node.body if type(x) is not jass_ast.CommentStmt]
    kept, created = [], {}
    for st in body:
        t = _is_create(st)
        if t in moved and t not in created:
            created[t] = len(kept)
        else:
            kept.append(st)
    if [jass_ast.canonical(x) for x in kept] != [jass_ast.canonical(x) for x in old]:
        problems.append('main without the moved creations is not the original main')
    if set(created) != moved:
        problems.append('%d creations for %d triggers' % (len(created), len(moved)))
    early = set()
    for k, st in enumerate(old):
        named = set(x.name for x in jass_ast.walk(st) if type(x) is jass_ast.Name and x.name in moved)
        for t in named:
            if created.get(t, -1) > k:
                problems.append('%s is named before it is created' % t)
            elif created.get(t) == k and t in early:
                problems.append('%s is named by code that runs before its creation' % t)
        for f in _runs_now(orig, st):
            early |= set(RX_WORD.findall(_code_only(orig.texts[f], JASS))) & moved
    ok, pj = _pjass_proof(new.text, orig.text)
    if not ok:
        problems.append('pjass: %s' % pj)
    if problems:
        return False, '%d differences: %s' % (len(problems), '; '.join(problems[:3]))
    return True, ('%d triggers created where they are declared are created where main sets them up; no code that runs '
                  'before names them; pjass %s' % (len(moved), pj))


def _init_extras(src):
    f = src.functions.get(ICT)
    if src.lang != JASS or f is None or f.node.params:
        return None, ''
    node, text, starts = f.node, src.text, src.starts
    body = [s for s in node.body if type(s) is not jass_ast.CommentStmt]
    seen, entries = [], []
    for k, s in enumerate(body):
        name = s.call.name if type(s) is jass_ast.CallStmt and not s.call.args else None
        if name and name.startswith('InitTrig_') and name in src.functions and name not in seen:
            seen.append(name)
            entries.append(('call', k, k + 1, 'gg_trg_' + name[9:]))
        elif entries and entries[-1][0] == 'wrap' and entries[-1][2] == k:
            entries[-1] = ('wrap', entries[-1][1], k + 1, None)
        else:
            entries.append(('wrap', k, k + 1, None))
    wraps = [x for x in entries if x[0] == 'wrap']
    if not wraps or not seen:
        return None, ''
    if node.locals:
        return None, 'InitCustomTriggers has locals'
    if _returns(body):
        return None, 'InitCustomTriggers returns early'
    known = set(x[9:] for x in seen) | set(x[7:] for x in src.globals if x.startswith('gg_trg_'))
    wrap_names = ['InitTrig_' + x for x in _wrapper_names(src, [body[w[1]] for w in wraps], known)]

    def off(k):
        return starts[(body[k].line if k < len(body) else node.end_line) - 1]

    functions, wanted, parts, pos = [], [], [], f.start
    wi = iter(wrap_names)
    for i, (kind, a0, b0, t) in enumerate(entries):
        if kind != 'wrap':
            continue
        name = next(wi)
        functions.append('function %s takes nothing returns nothing\n%sendfunction\n' % (name, text[off(a0):off(b0)]))
        parts.extend([text[pos:off(a0)], '    call %s()\n' % name])
        pos = off(b0)
        wanted.append((name[9:], next((x[3] for x in entries[i + 1:] if x[3]), None),
                       next((x[3] for x in reversed(entries[:i]) if x[3]), None)))
    parts.append(text[pos:f.end])
    head_text, added = _declared(src, text[:f.lead], wanted)
    new = head_text + '\n'.join(functions) + '\n' + text[f.lead:f.start] + ''.join(parts) + text[f.end:]
    info = {'host': ICT, 'proof': 'ict_extras', 'by': 'name', 'triggers': len(wraps), 'calls': len(seen),
            'wrappers': wrap_names, 'with_extras': 0, 'locals': [], 'rit': 0, 'text': new,
            'moved': [jass_ast.unparse(body[k], comments=False).strip()[:60] for w in wraps for k in range(w[1], w[2])],
            'new': wrap_names, 'added_globals': added, 'original': src}
    return new, info


def _rebuilt_proof(info):
    orig, new, host = info['original'], info['source'], info['host']
    added = set(info['new'])
    back_in = added | set(info.get('reused') or ())
    problems = []

    def stmts(name):
        return [s for s in new.functions[name].node.body if type(s) is not jass_ast.CommentStmt]

    def inline(ss):
        out = []
        for s in ss:
            name = s.call.name if type(s) is jass_ast.CallStmt and not s.call.args else None
            out.extend(inline(stmts(name)) if name in back_in else [s])
        return out

    back = inline(stmts(host))
    a = '\n'.join(jass_ast.canonical(s) for s in back)
    b = '\n'.join(jass_ast.canonical(s) for s in orig.functions[host].node.body
                  if type(s) is not jass_ast.CommentStmt)
    if a != b:
        problems.append('%s inlined back differs: %s' % (host, _first_difference(a, b)))

    def decls(name):
        return dict((d.name, jass_ast.canonical(jass_ast.unparse(d, comments=False)))
                    for d in new.functions[name].node.locals)

    old = dict((d.name, jass_ast.canonical(jass_ast.unparse(d, comments=False)))
               for d in orig.functions[host].node.locals)
    mine = decls(host)
    seen, shared = set(mine), set()
    for g in sorted(added):
        mg = decls(g)
        seen |= set(mg)
        shared |= set(mg) & set(mine)
        if any(old.get(x) != v for x, v in mg.items()):
            problems.append('%s declares a local %s does not have' % (g, host))
        bad = _read_first([_touch(s, mg) for s in stmts(g)])
        if bad:
            problems.append('%s reads its local %s before setting it' % (g, sorted(bad)[0]))
    if any(old.get(x) != v for x, v in mine.items()) or seen != set(old):
        problems.append('the locals of %s are not the original ones' % host)
    body = stmts(host)
    k = next((i for i, s in enumerate(body) if type(s) is jass_ast.CallStmt and s.call.name in added), len(body))
    bad = _read_first([_touch(s, shared) for s in body[k + 1:]])
    if bad:
        problems.append('%s reads %s after the moved code, which set it' % (host, sorted(bad)[0]))
    if set(new.functions) - set(orig.functions) != added:
        problems.append('functions added: %s' % ', '.join(sorted(set(new.functions) - set(orig.functions))[:3]))
    changed = [f for f, x in orig.texts.items() if f != host and new.texts.get(f) != x]
    if changed:
        problems.append('functions changed: %s' % ', '.join(changed[:3]))
    extra = set(info['added_globals'])
    if [(x, d.text) for x, d in orig.globals.items()] != [(x, d.text) for x, d in new.globals.items()
                                                          if x not in extra]:
        problems.append('the globals changed')
    ok, pj = _pjass_proof(new.text, orig.text)
    if not ok:
        problems.append('pjass: %s' % pj)
    if problems:
        return False, '%d differences: %s' % (len(problems), '; '.join(problems[:3]))
    return True, ('%s with the %d rebuilt triggers put back inline equals the original (%d statements)%s; pjass %s' % (
        host, info['triggers'], len(back), ', %d locals moved (%s)' % (len(info['locals']), ', '.join(
            info['locals'][:5])) if info['locals'] else '', pj))


def _rebuilt_restore(res, info, init_per_trigger):
    res.proofs[info['proof']] = _rebuilt_proof(info)
    res.report['rebuilt'] = dict((k, len(info[k]) if k == 'wrappers' else info[k]) for k in (
        'host', 'by', 'triggers', 'calls', 'wrappers', 'with_extras', 'locals', 'rit') + (
        ('moved',) if 'moved' in info else ()))
    return info['source'].text, info['source'], init_per_trigger and info['host'] != 'main'


def _rebuilt(sk, src, rebuild, what, object_names=None):
    text, info = rebuild(src)
    if text is None:
        if info:
            sk['reason'] += '; %s' % info
        return sk, src
    new = _Source(text, JASS)
    ren = {}
    if info['by'] == 'name':
        sk2 = _skeleton_by_name(new) or {'reason': 'no InitCustomTriggers'}
    else:
        sk2 = _skeleton_by_structure(new, info['wrappers'], object_names)
        ren = sk2.get('renames') or {}
        if not sk2['reason'] and (ren.get(info['ict']) != ICT or info['rit_name'] and ren.get(info['rit_name']) != RIT):
            sk2['reason'] = 'the search by structure did not take the rebuilt InitCustomTriggers'
    if sk2['reason']:
        sk['reason'] += '; %s, %s' % (what, sk2['reason'])
        return sk, src
    info['source'] = new
    sk2['rebuilt'] = info
    sk2['wrappers'] = [ren.get(x, x) for x in info['wrappers']]
    return sk2, new


WURST = 'compiled by WurstScript: it has no editor triggers'


def _is_wurst(text, lang):
    return lang == LUA and '__wurst_' in text and len(set(re.findall(r'\b__wurst_\w+', _code_only(text, lang)))) >= 3


def _is_typescript(text, lang):
    return lang == LUA and '__TS__' in text and len(set(re.findall(r'\b__TS__\w+', _code_only(text, lang)))) >= 3


def skeleton(script, lang=JASS, object_names=None):
    lang = LUA if lang == LUA else JASS
    if isinstance(script, _Source):
        src = script
    else:
        try:
            src = _Source(_normalize(script), lang)
        except (jass_ast.JassSyntaxError, lua_ast.LuaSyntaxError) as e:
            return {'by': None, 'reason': 'the script does not parse: %s' % e, 'renames': {}}
    sk = _skeleton_by_name(src)
    if sk is not None and sk['reason']:
        sk, src = _rebuilt(sk, src, _init_extras, 'with the code that is not an InitTrig_ made triggers')
    elif sk is None:
        sk = _skeleton_by_structure(src, (), object_names)
        if sk['reason'] == NO_SKELETON:
            late = _late_created(src)
            sk, src = _rebuilt(sk, late['source'] if late else src, _inlined_setup,
                               'with the trigger setup inlined into main rebuilt', object_names)
            if late and sk.get('rebuilt'):
                sk['late_created'] = late
        elif _is_wurst(src.text, src.lang):
            sk['reason'] = WURST
    sk.setdefault('by', None)
    sk['main'] = 'main' if 'main' in src.functions else None
    sk['config'] = 'config' if 'config' in src.functions else None
    if not sk['reason'] and not (sk['main'] and sk['config']):
        sk['reason'] = 'the script has no %s function' % ('main' if not sk['main'] else 'config')
    if not sk['reason']:
        dup = sorted(set(src.duplicates) & (set(sk['triggers']) | {ICT, RIT, 'main', 'config'}))
        if dup:
            sk['reason'] = '%s defined twice' % dup[0]
    names = {}
    if not sk['reason']:
        if sk['by'] == 'structure':
            labels = sk.get('labels') or {}
            names = dict((i, labels[i] if _identifier_ok(labels.get(i), i[len('InitTrig_'):]) else
                          i[len('InitTrig_'):]) for i in sk['triggers'])
        else:
            for i in sk['triggers']:
                ident = i[len('InitTrig_'):]
                banner = _banner(src, gui_render.closure(src.texts, i))[0]
                names[i] = banner if _identifier_ok(banner, ident) else ident
    sk['names'] = names
    for key in ('triggers', 'init_custom_triggers', 'run_initialization_triggers', 'init_globals'):
        sk.setdefault(key, [] if key == 'triggers' else None)
    return sk


def _is_registration(s):
    t = type(s)
    if t is jass_ast.SetStmt:
        v = s.value
        while type(v) is jass_ast.Paren:
            v = v.inner
        return (type(s.target) is jass_ast.Name and s.target.name.startswith('gg_trg_') and
                type(v) is jass_ast.Call and v.name == 'CreateTrigger' and not v.args)
    return t is jass_ast.CallStmt and bool(REGISTRATION_CALLS.match(s.call.name))


def _indented(stmts, depth=1):
    out = []
    for s in stmts:
        out.extend('    ' * depth + x if x else '' for x in jass_ast.unparse(s).rstrip('\n').split('\n'))
    return out


def _init_per_trigger(src, sk, names):
    rit = sk.get('run_initialization_triggers')
    if src.lang != JASS:
        return src.text, [], 'JASS only'
    if not rit:
        return src.text, [], 'no RunInitializationTriggers to run the new triggers'
    body = [s for s in src.functions['main'].node.body if type(s) is not jass_ast.CommentStmt]
    calls = [s.call.name if type(s) is jass_ast.CallStmt else None for s in body]
    k = calls.index(sk['init_custom_triggers']) if sk['init_custom_triggers'] in calls else -1
    if k < 0 or calls[k + 1:k + 2] != [rit]:
        return src.text, [], 'main does not call RunInitializationTriggers right after InitCustomTriggers'
    edits, made, held = [], [], 0
    for init in sk['triggers']:
        f = src.functions[init]
        node = f.node
        if node.locals or node.params or init in sk.get('wrappers', ()):
            continue
        move = [s for s in node.body if type(s) is not jass_ast.CommentStmt and not _is_registration(s)]
        if not move:
            continue
        ident = init[len('InitTrig_'):]
        new = ident + '_Init'
        if ('InitTrig_' + new in src.functions or 'Trig_%s_Actions' % new in src.functions or
                'gg_trg_' + new in src.globals):
            continue
        keep = [s for s in node.body if s not in move]
        assigned = _assigned(move)
        if _returns(move) or any(_touch(s, assigned)[0] for s in keep):
            held += 1
            continue
        header = f.text.split('\n', 1)[0]
        code = ['function Trig_%s_Actions takes nothing returns nothing' % new] + _indented(move) + ['endfunction', '',
                'function InitTrig_%s takes nothing returns nothing' % new,
                '    set gg_trg_%s = CreateTrigger(  )' % new,
                '    call TriggerAddAction( gg_trg_%s, function Trig_%s_Actions )' % (new, new), 'endfunction', '',
                header] + _indented(keep) + ['endfunction', '']
        edits.append((f.start, f.end, '\n'.join(code)))
        name = names.get(init, ident)
        name = name + (' Init' if ' ' in name else '_Init')
        made.append((new, name if gui_render.trigger_identifier(name) == new else new))
    if not made:
        return src.text, [], ('%d InitTrig_ kept whole (a registration reads what the other code sets, or it returns)'
                              % held if held else 'no InitTrig_ does more than register')
    text = src.text
    g0 = src.blocks[0][0] if src.blocks else None
    if g0 is None:
        return src.text, [], 'no globals block'
    at = text.index('\n', g0) + 1
    edits.append((at, at, ''.join('    trigger gg_trg_%s = null\n' % n for n, _x in made)))
    for fname, line in ((sk['init_custom_triggers'], '    call InitTrig_%s()\n'),
                        (rit, '    call ConditionalTriggerExecute(gg_trg_%s)\n')):
        at = text.index('\n', src.functions[fname].start) + 1
        edits.append((at, at, ''.join(line % n for n, _x in made)))
    for a, b, rep in sorted(edits, key=lambda e: (e[0], e[1]), reverse=True):
        text = text[:a] + rep + text[b:]
    return text, made, ''


def _ownership(src, inits):
    roots = set(inits)
    others = dict((n, t) for n, t in src.texts.items() if n not in roots)
    reach = {}
    for i in inits:
        others[i] = src.texts[i]
        reach[i] = gui_render.closure(others, i)
        del others[i]
    owners = collections.defaultdict(set)
    for i, fs in reach.items():
        for f in fs:
            owners[f].add(i)
    header = set(f for f in src.functions if f not in owners) - {ICT, RIT}
    header |= set(f for f, o in owners.items() if len(o) > 1)
    problems = []
    changed = True
    while changed:
        changed = False
        for f in sorted(header):
            if f in ('main', 'config'):
                continue
            for g in src.refs(f):
                if g in (ICT, RIT) and src.lang == JASS:
                    problems.append('%s calls %s, which the editor writes after the triggers' % (f, g))
                elif g in owners and g not in header:
                    if g in roots:
                        problems.append('%s calls the trigger function %s' % (f, g))
                        continue
                    header.add(g)
                    changed = True
    own = dict((i, [f for f in reach[i] if f not in header]) for i in inits)
    return own, header, sorted(set(problems))


def _load_matcher(lang, matcher=None):
    name = 'gui_match_lua' if lang == LUA else 'gui_match_jass'
    if matcher is None:
        try:
            matcher = __import__('doctor.triggers.' + name, fromlist=[name])
        except Exception as e:
            return None, '%s: %s: %s' % (name, type(e).__name__, e)
    lacks = [f for f in ('match_trigger', 'match_globals', 'script_functions') if not hasattr(matcher, f)]
    if lacks:
        return None, '%s has no %s' % (getattr(matcher, '__name__', name), ', '.join(lacks))
    return matcher, ''


def _number(text):
    try:
        return float(int(text, 0)) if re.match(r'^-?(?:0[xX][0-9A-Fa-f]+|\d+)$', text) else float(text)
    except ValueError:
        return None


def _value_key(value, lang):
    if value is None:
        return None
    v = value.strip()
    if v.startswith('$'):
        v = '0x' + v[1:]
    n = _number(v.rstrip('.') if re.match(r'^-?\d+\.$', v) else v)
    if n is not None:
        return ('number', n)
    return ('code', gui_render.canonical(v, lang, False))


def _decl_key(d, lang):
    return (d.type, d.is_array, d.is_constant, _value_key(d.value, lang))


def _editor_declarations(variables, td, lang):
    mt = wtg.MapTriggers(variables=list(variables))
    text = gui_render.render_globals(mt, td, lang)
    src = _Source(text, lang)
    return dict((n, d) for n, d in src.globals.items() if n.startswith('udg_'))


def _same_declaration(orig, mine, lang):
    if orig is None or mine is None:
        return False, False
    if _decl_key(orig, lang) == _decl_key(mine, lang):
        return True, False
    if lang == JASS and orig.value is None and (orig.type, orig.is_array, orig.is_constant) == (
            mine.type, mine.is_array, mine.is_constant):
        return True, True
    return False, False


def _usable_variables(variables, src, td, lang):
    usable, kept, initialized = [], {}, []
    good = []
    for v in variables:
        n = 'udg_' + v.name
        tt = td.types.get(v.type)
        d = src.globals.get(n)
        if d is None:
            kept[n] = 'not declared at the top of the script'
        elif d.is_constant:
            kept[n] = 'a constant'
        elif tt is None or not tt.can_be_global:
            kept[n] = 'type %s is not a GUI variable type' % v.type
        else:
            good.append(v)
    mine = _editor_declarations(good, td, lang) if good else {}
    for v in good:
        n = 'udg_' + v.name
        same, normalized = _same_declaration(src.globals[n], mine.get(n), lang)
        if not same:
            kept[n] = 'the editor would declare %r, the script has %r' % (
                (mine[n].text.strip() if n in mine else '?'), src.globals[n].text.strip())
            continue
        if normalized:
            initialized.append(n)
        usable.append(v)
    return usable, kept, initialized


def _drop_empty_custom(functions):
    n, i = 0, 0
    while i < len(functions):
        f = functions[i]
        if f.name == 'CustomScriptCode' and len(f.params) == 1 and not f.params[0].value.strip():
            del functions[i]
            n += 1
            continue
        n += _drop_empty_custom(f.children)
        for p in f.params:
            while p is not None:
                if p.function is not None:
                    n += _drop_empty_custom(p.function.children)
                p = p.index
        i += 1
    return n


def _variable_refs(trigger):
    out = []
    for f in wtg.iter_functions(trigger.functions):
        for p in f.params:
            while p is not None:
                if p.kind == wtg.VARIABLE and p.value:
                    out.append(p.value)
                p = p.index
    return out


def _has_event(trigger, name, enabled=False):
    return any(f.kind == wtg.EVENT and f.name == name and (f.enabled or not enabled) for f in trigger.functions)


def _first_difference(a, b):
    x, y = a.split('\n'), b.split('\n')
    k = next((i for i in range(min(len(x), len(y))) if x[i] != y[i]), min(len(x), len(y)))
    return 'line %d: %r / %r' % (k + 1, x[k][:90] if k < len(x) else '<end>', y[k][:90] if k < len(y) else '<end>')


class _Decision(object):
    __slots__ = ('init', 'ident', 'name', 'kind', 'trigger', 'covered', 'external', 'own', 'reason', 'custom', 'empty',
                 'rendered')

    def __init__(self, init, name, own):
        self.init, self.ident, self.name, self.own = init, init[len('InitTrig_'):], name, list(own)
        self.kind, self.trigger, self.covered, self.external = 'text', None, set(), []
        self.reason, self.custom, self.empty, self.rendered = '', 0, 0, []


class _Context(object):
    def __init__(self, src, td, lang, mod, nodes, gtypes, mt_vars, own, header, rit_idents, all_idents, var_names,
                 relaxed=False):
        self.src, self.td, self.lang, self.mod, self.nodes = src, td, lang, mod, nodes
        self.gtypes, self.mt_vars, self.own, self.header = gtypes, mt_vars, own, header
        self.rit_idents, self.all_idents, self.var_names = rit_idents, all_idents, var_names
        self.kw = {}
        if mod is not None:
            try:
                accepted = inspect.signature(mod.match_trigger).parameters
            except (TypeError, ValueError):
                accepted = ()
            if 'source' in accepted:
                self.kw['source'] = src.text
            if relaxed and 'relaxed' in accepted:
                self.kw['relaxed'] = True
        self.words = collections.Counter(RX_WORD.findall(src.text))
        self.owner = {}
        for i, fs in own.items():
            for f in fs:
                self.owner[f] = i


def _gui(ctx, d, obfuscated):
    src, td, lang = ctx.src, ctx.td, ctx.lang
    try:
        m = ctx.mod.match_trigger(ctx.nodes, d.init, td, ctx.gtypes, d.name, **ctx.kw)
    except Exception as e:
        return 'matcher error: %s: %s' % (type(e).__name__, str(e)[:120])
    if m is None or m.trigger is None:
        return (getattr(m, 'reason', '') or 'no GUI form')[:200]
    t = m.trigger
    t.name = d.name
    banner_desc = _banner(src, d.own)[1]
    t.description = (m.trigger.description or banner_desc or (NOTE_RENAMED if obfuscated else ''))
    t.enabled, t.is_comment, t.is_text, t.run_on_init, t.category_id = 1, 0, 0, 0, 0
    d.empty = _drop_empty_custom(t.functions)
    actions = [f for f in t.functions if f.kind == wtg.ACTION]
    if actions and all(f.name == 'CustomScriptCode' for f in actions):
        return ONLY_CUSTOM
    covered = set(m.helpers) | {d.init}
    outside = sorted(covered - set(d.own))
    if outside:
        return 'the model takes %s, which is not only this trigger\'s' % outside[0]
    for v in _variable_refs(t):
        if v.startswith('gg_trg_'):
            if v[len('gg_trg_'):] not in ctx.all_idents:
                return 'refers to %s, a trigger the wtg does not have' % v
        elif v.startswith('gg_'):
            if v not in src.globals:
                return 'refers to %s, which the script does not declare' % v
        elif v not in ctx.var_names:
            return 'refers to udg_%s, which stays in the custom script' % v
    in_rit = d.ident in ctx.rit_idents
    if in_rit and t.initially_off:
        return 'RunInitializationTriggers runs it, but it starts turned off'
    if in_rit and not _has_event(t, 'MapInitializationEvent'):
        event = getattr(ctx.mod, 'initialization_event', None)
        t.functions.insert(0, event(td) if event else wtg.Function(wtg.EVENT, 'MapInitializationEvent', 1, []))
    if not in_rit and not t.initially_off and _has_event(t, 'MapInitializationEvent', True):
        return 'a Map Initialization event that RunInitializationTriggers does not run'
    try:
        equal, a, b = gui_render.compare_trigger(t, td, ctx.mt_vars, None, lang, functions=src.texts)
        rendered = gui_render.split_functions(gui_render.render_trigger(t, td, ctx.mt_vars, lang), lang)
    except Exception as e:
        return 'render error: %s: %s' % (type(e).__name__, str(e)[:120])
    root = 'InitTrig_' + d.ident
    if root not in rendered:
        return 'the render has no %s' % root
    merged = collections.ChainMap(rendered, src.texts)
    pulled = [n for n in gui_render.closure(merged, root) if n not in rendered]
    if not equal:
        return 'the round trip differs (%s)' % _first_difference(a, b)
    for n in pulled:
        if n in covered:
            return 'the render calls %s, which it replaces' % n
        if n not in ctx.header and ctx.owner.get(n) not in (None, d.init):
            return 'the render calls %s, a function of another trigger' % n
    external = [n for n in pulled if n not in ctx.header]
    lost = set(d.own) - covered - set(external)
    if lost:
        return 'the model leaves %s out' % sorted(lost)[0]
    orphans = set(n for n in rendered if n in src.functions and n not in covered and n in ctx.header and
                  ctx.words[n] == 1)
    covered = covered | orphans
    clash = sorted(set(rendered) & (set(src.functions) - covered))
    if clash:
        return 'the render defines %s, which the script already has' % clash[0]
    counts = collections.Counter()
    for f in covered:
        counts.update(RX_WORD.findall(src.texts[f]))
    for n in sorted(covered - set(rendered)):
        if ctx.words[n] > counts[n]:
            return 'the script refers to %s elsewhere (the render names it differently)' % n
    seen, stack = set(), list(external)
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.add(n)
        for g in src.refs(n):
            if g in covered:
                return 'the helper %s moved to the custom script calls %s, which the render replaces' % (n, g)
            if g not in ctx.header and ctx.owner.get(g) not in (None, d.init):
                return 'the helper %s moved to the custom script calls %s of another trigger' % (n, g)
            stack.append(g)
    d.kind, d.trigger, d.covered, d.external = 'gui', t, covered, external
    d.custom, d.rendered = getattr(m, 'custom_lines', 0), sorted(rendered)
    ctx.header -= orphans
    return ''


def _text_trigger(ctx, d, obfuscated, reason):
    src = ctx.src
    desc = _banner(src, d.own)[1] or (NOTE_CUSTOM if reason == ONLY_CUSTOM else NOTE_TEXT % reason)
    d.kind, d.reason = 'text', reason
    d.trigger = wtg.Trigger(d.name, desc, 0, 1, 1, 0, 1 if d.ident in ctx.rit_idents else 0, 0, [])
    d.covered, d.external = set(d.own), []


def _rit_idents(src, rit):
    if not rit:
        return []
    calls = src.calls(rit)
    if calls is None:
        return None
    out = []
    for callee, args in calls:
        if callee != 'ConditionalTriggerExecute' or len(args) != 1 or not re.match(r'^gg_trg_\w+$', args[0].strip()):
            return None
        out.append(args[0].strip()[len('gg_trg_'):])
    return out


def _trigger_order(src, inits, disabled):
    enabled = [i[len('InitTrig_'):] for i in inits]
    wanted_enabled = set(enabled)
    wanted = wanted_enabled | set(disabled)
    declared = [n[len('gg_trg_'):] for n in src.globals if n.startswith('gg_trg_') and n[len('gg_trg_'):] in wanted]
    if [x for x in declared if x in wanted_enabled] == enabled:
        return declared, disabled
    return enabled, []


def _remove_spans(text, spans):
    out, pos = [], 0
    for a, b in sorted(set(spans)):
        if a < pos:
            a = pos
        if b <= a:
            continue
        out.append(text[pos:a])
        pos = b
    out.append(text[pos:])
    return ''.join(out)


def _header_text(src, removed_functions, removed_globals):
    spans = [(src.functions[n].lead, src.functions[n].end) for n in removed_functions if n in src.functions]
    blocks = collections.defaultdict(list)
    for n, d in src.globals.items():
        blocks[d.block].append(n)
    for n in removed_globals:
        d = src.globals.get(n)
        if d is not None:
            spans.append((d.start, d.end))
    for block, names in blocks.items():
        if block is not None and names and all(n in removed_globals for n in names):
            spans.append(block)
    return _remove_spans(src.text, spans)


LUA_NOTE = ("-- The map's script without its triggers, inside do ... end. When you save, the World Editor writes the\n"
            "-- triggers, InitCustomTriggers and RunInitializationTriggers after this custom script, and its own\n"
            "-- main() and config() at the end. The last lines send the editor's copies of the functions defined here\n"
            "-- (main, config, ...) to a separate table, so the game still runs the map's own; the rest goes to _G.\n")


def lua_custom_script(header, private):
    names = ', '.join('%s = true' % n for n in sorted(private))
    return (LUA_NOTE + 'do\n' + header + ('' if header.endswith('\n') else '\n') + 'end\n' +
            'local __devo_private = {%s}\n' % names + 'local __devo_editor = {}\n' +
            'local _ENV = setmetatable({}, {__index = _G, __newindex = function(_, k, v) if __devo_private[k] then '
            '__devo_editor[k] = v else _G[k] = v end end})\n')


def lua_final_return(text):
    body = lua_ast.parse(text).body
    if not body or type(body[-1]) is not lua_ast.ReturnStmt:
        return text, ''
    a, b = body[-1].span
    values = text[a:b].strip()[len('return'):].strip().rstrip(';').strip()
    new = 'local __devo_return = %s' % values if values else ''
    return text[:a] + new + text[b:], '%r became %r' % (text[a:b].strip(), new)


def _lua_top_locals(text):
    out = set()
    for s in lua_ast.parse(text).body:
        if type(s) is lua_ast.LocalStmt:
            out.update(s.names)
        elif type(s) is lua_ast.FunctionStmt and s.is_local:
            out.add(s.name)
    return out


def _crlf(text):
    return text.replace('\r\n', '\n').replace('\n', '\r\n')


CATEGORIES = ('Map initialization', 'Chat commands', 'Region events', 'Unit events', 'Player events', 'Timers',
              'Game events', 'Destructible events', 'Dialogs', 'Other events', 'Run by other triggers', 'Disabled',
              'Comments')
EVENT_CATEGORIES = {'TC_UNIT': 'Unit events', 'TC_PLAYER': 'Player events', 'TC_TIME': 'Timers',
                    'TC_GAME': 'Game events', 'TC_DESTRUCT': 'Destructible events', 'TC_DIALOG': 'Dialogs'}
RX_REGISTER = re.compile(r'\b(TriggerRegister\w+)\s*\(([^\n]*)')


def _event_category(name, td):
    if name == 'TriggerRegisterPlayerChatEvent':
        return 'Chat commands'
    if name in ('TriggerRegisterEnterRectSimple', 'TriggerRegisterLeaveRectSimple'):
        return 'Region events'
    f = td.events.get(name)
    return EVENT_CATEGORIES.get(f.category, 'Other events') if f is not None else 'Other events'


def _text_events(text, lang):
    code = _code_only(text or '', lang)
    fns = gui_render.split_functions(code, lang)
    inits = [t for n, t in fns.items() if n.startswith('InitTrig_')]
    return [(m.group(1), tuple(re.findall(r'\bEVENT_\w+', m.group(2)))) for part in inits + [code]
            for m in RX_REGISTER.finditer(part)]


def _category(t, text, td, lang):
    if t.is_comment:
        return 'Comments'
    if not t.enabled:
        return 'Disabled'
    if t.is_text:
        if t.run_on_init:
            return 'Map initialization'
        found = _text_events(text, lang)
        for script_name, _codes in found:
            f = td.by_script.get(('event', script_name))
            if f is not None:
                return _event_category(f.name, td)
        return 'Other events' if found else 'Run by other triggers'
    events = [f for f in t.functions if f.kind == wtg.EVENT and f.enabled]
    if any(f.name == 'MapInitializationEvent' for f in events):
        return 'Map initialization'
    return _event_category(events[0].name, td) if events else 'Run by other triggers'


FOLDER_LIMIT = 24
FAMILY_BY_FUNCTION = tuple((re.compile(rx), family) for rx, family in (
    (r'^TriggerRegisterTimer|^TriggerRegisterGameStateEvent', 'TIMER'),
    (r'^TriggerRegisterPlayerChatEvent', 'CHAT'),
    (r'^TriggerRegisterDialog', 'DIALOG'),
    (r'^TriggerRegister(?:Enter|Leave)(?:Rect|Region)', 'REGION'),
    (r'^TriggerRegisterUnitInRange', 'RANGE'),
    (r'^TriggerRegisterVariableEvent', 'VARIABLE'),
    (r'^TriggerRegisterDeathEvent|^TriggerRegisterDestDeath', 'DEST_DEATH'),
    (r'^TriggerRegisterUnit(?:State|Life|Mana)Event', 'UNIT_STATE'),
    (r'^TriggerRegisterTrackable', 'TRACKABLE'),
    (r'^BlzTriggerRegisterPlayerKeyEvent', 'KEY'),
    (r'^BlzTriggerRegisterFrameEvent', 'FRAME'),
    (r'^BlzTriggerRegisterPlayerSyncEvent', 'SYNC')))
FAMILY_BY_CODE = {'EVENT_GAME_TIMER_EXPIRED': 'TIMER', 'EVENT_GAME_STATE_LIMIT': 'TIMER',
                  'EVENT_GAME_ENTER_REGION': 'REGION', 'EVENT_GAME_LEAVE_REGION': 'REGION',
                  'EVENT_GAME_VARIABLE_LIMIT': 'VARIABLE', 'EVENT_UNIT_STATE_LIMIT': 'UNIT_STATE',
                  'EVENT_PLAYER_CHAT': 'CHAT', 'EVENT_DIALOG_BUTTON_CLICK': 'DIALOG', 'EVENT_DIALOG_CLICK': 'DIALOG',
                  'EVENT_GAME_TRACKABLE_HIT': 'TRACKABLE', 'EVENT_GAME_TRACKABLE_TRACK': 'TRACKABLE'}
RX_UNIT_EVENT = re.compile(r'^EVENT_(?:PLAYER_UNIT|UNIT|PLAYER_HERO|UNIT_HERO|WIDGET)_(\w+)$')
RX_REGISTRATION = re.compile(r'\b((?:Blz)?TriggerRegister\w+)\s*\(([^\n]*)')
RX_EVENT_CODE = re.compile(r'\bEVENT_\w+')
EVENT_TYPES = frozenset(('gameevent', 'playerevent', 'playerunitevent', 'unitevent', 'widgetevent', 'dialogevent'))
REGISTRATION_ONLY = re.compile(
    r'^(?:(?:Blz)?TriggerRegister\w+|TriggerAddAction|TriggerAddCondition|DisableTrigger|CreateTrigger|Player|Condition'
    r'|Filter|CreateRegion|RegionAddRect|Rect|GetPlayableMapRect|GetEntireMapRect|GetWorldBounds|ConvertedPlayer'
    r'|GetConvertedPlayerId|GetPlayerId|Convert\w+|I2S|I2R|R2I|S2I)$')


def _code_family(code):
    if code in FAMILY_BY_CODE:
        return FAMILY_BY_CODE[code]
    m = RX_UNIT_EVENT.match(code)
    if m:
        return 'U:' + ('HERO_' if '_HERO_' in code else '') + m.group(1)
    if code.startswith('EVENT_PLAYER_ARROW_'):
        return 'ARROW'
    return code


_FUNCTION_FAMILIES = {}


def _function_families(name):
    out = _FUNCTION_FAMILIES.get(name)
    if out is None:
        out = set(family for rx, family in FAMILY_BY_FUNCTION if rx.match(name))
        if not out:
            f = jass_normal.reference().functions.get(name)
            if f is not None:
                out = set(_code_family(x.name) for x in jass_ast.walk(f) if type(x) is jass_ast.Name and
                          x.name.startswith('EVENT_'))
        if not out:
            out = {'F:' + name}
        _FUNCTION_FAMILIES[name] = out
    return out


def _takes_event(name):
    ref = jass_normal.reference()
    f = ref.functions.get(name)
    if f is not None:
        return any(t in EVENT_TYPES for t, _n in f.params)
    return name in ('TriggerRegisterGameEvent', 'TriggerRegisterPlayerEvent', 'TriggerRegisterPlayerUnitEvent',
                    'TriggerRegisterUnitEvent', 'TriggerRegisterFilterUnitEvent')


def _registers_only(node, own, others, functions, depth=0):
    names = set(d.name for d in node.locals) | set(p for _t, p in node.params)

    def plain(e):
        for x in jass_ast.walk(e):
            if type(x) is jass_ast.Call and not REGISTRATION_ONLY.match(x.name):
                return False
            if type(x) is jass_ast.Name and x.name in others:
                return False
        return True

    def walk(stmts):
        for st in stmts:
            t = type(st)
            if t is jass_ast.CommentStmt:
                continue
            if t is jass_ast.SetStmt:
                target = st.target
                while type(target) in (jass_ast.Paren, jass_ast.Index):
                    target = target.inner if type(target) is jass_ast.Paren else target.base
                mine = type(target) is jass_ast.Name and (target.name in names or target.name == own or (
                    target.name.startswith('gg_trg_') and target.name not in others))
                if not mine or not plain(st.value) or not plain(st.target):
                    return False
            elif t is jass_ast.CallStmt:
                callee = functions.get(st.call.name)
                if callee is not None and not st.call.args and not callee.params and depth < 4:
                    if not _registers_only(callee, own, others, functions, depth + 1):
                        return False
                elif not plain(st.call):
                    return False
            elif t is jass_ast.IfStmt:
                for c, body in st.branches:
                    if (c is not None and not plain(c)) or not walk(body):
                        return False
            elif t is jass_ast.LoopStmt:
                if not walk(st.body):
                    return False
            elif t is jass_ast.ExitWhenStmt:
                if not plain(st.cond):
                    return False
            else:
                return False
        return True

    return all(d.initializer is None or plain(d.initializer) for d in node.locals) and walk(node.body)


def _order_info(t, text, td, lang, others=frozenset()):
    if not t.enabled or t.is_comment:
        return set(), False
    keys = set()
    if t.is_text:
        if t.run_on_init:
            keys.add('INIT')
        raw = text or ''
        barrier = True
        if lang == JASS:
            try:
                functions = dict((f.name, f) for f in jass_ast.parse(raw).functions)
            except jass_ast.JassSyntaxError:
                functions = {}
            own = 'gg_trg_' + gui_render.trigger_identifier(t.name)
            inits = [f for name, f in functions.items() if name.startswith('InitTrig_')]
            barrier = not inits or not all(_registers_only(f, own, others - {own}, functions) for f in inits)
        for m in RX_REGISTRATION.finditer(_code_only(raw, lang)):
            codes = RX_EVENT_CODE.findall(m.group(2))
            if codes:
                keys.update(_code_family(c) for c in codes)
                if 'EVENT_WIDGET_DEATH' in codes:
                    keys.add('DEST_DEATH')
            elif _takes_event(m.group(1)):
                barrier = True
            else:
                keys.update(_function_families(m.group(1)))
                if m.group(1) == 'TriggerRegisterDeathEvent':
                    keys.add('U:DEATH')
        return keys, barrier
    for f in t.functions:
        if f.kind != wtg.EVENT or not f.enabled:
            continue
        if f.name == 'MapInitializationEvent':
            keys.add('INIT')
            continue
        codes = [td.presets[p.value].code for p in f.params if p.kind == wtg.PRESET and p.value in td.presets and
                 td.presets[p.value].code.startswith('EVENT_')]
        if codes:
            keys.update(_code_family(c) for c in codes)
        else:
            fd = td.events.get(f.name)
            keys.update(_function_families(fd.script_name if fd is not None and fd.script_name else f.name))
    return keys, False


def _interact(a, b):
    (keys_a, barrier_a), (keys_b, barrier_b) = a, b
    return bool(keys_a & keys_b) or barrier_a or barrier_b


def _folder_kinds(t, text, td, lang):
    out = [_category(t, text, td, lang)]
    if t.enabled and not t.is_comment and not t.is_text:
        for f in t.functions:
            if f.kind == wtg.EVENT and f.enabled and f.name != 'MapInitializationEvent':
                c = _event_category(f.name, td)
                if c not in out:
                    out.append(c)
    return out


def editor_order(mt):
    place = dict((c.id, k) for k, c in enumerate(mt.categories))
    return sorted(range(len(mt.triggers)), key=lambda k: (place.get(mt.triggers[k].category_id, len(place)), k))


def _folders(kinds, info, live, seed):
    folders = [[c, set(), False, False] for c in seed]
    where = []
    for k, (mine, (keys, barrier)) in enumerate(zip(kinds, info)):
        chosen = None
        for kind in mine:
            i = next((i for i in range(len(folders) - 1, -1, -1) if folders[i][0] == kind), None)
            if i is None:
                continue
            if not live[k] or not any((keys & f[1]) or (barrier and f[3]) or f[2] for f in folders[i + 1:]):
                chosen = i
                break
        if chosen is None:
            folders.append([mine[0], set(), False, False])
            chosen = len(folders) - 1
        if live[k]:
            f = folders[chosen]
            f[1] |= keys
            f[2] = f[2] or barrier
            f[3] = True
        where.append(chosen)
    return where, folders


def categorize(mt, td, texts=None, lang=JASS):
    texts = list(texts) if texts is not None else [None] * len(mt.triggers)
    globals_ = frozenset('gg_trg_' + gui_render.trigger_identifier(t.name) for t in mt.triggers)
    kinds = [_folder_kinds(t, x, td, lang) for t, x in zip(mt.triggers, texts)]
    info = [_order_info(t, x, td, lang, globals_) for t, x in zip(mt.triggers, texts)]
    live = [t.enabled and not t.is_comment for t in mt.triggers]
    first = [k[0] for k in kinds]
    seeds = [[c for c in CATEGORIES if c in first], list(collections.OrderedDict.fromkeys(first))]
    where, folders = min((_folders(kinds, info, live, seed) for seed in seeds), key=lambda r: len(set(r[0])))
    used = sorted(set(where))
    if len(used) > FOLDER_LIMIT:
        mt.categories = [wtg.Category(0, CATEGORY, 0)]
        for t in mt.triggers:
            t.category_id = 0
        return collections.OrderedDict([(CATEGORY, len(mt.triggers))]), 0
    names, seen = {}, collections.Counter()
    for i in used:
        seen[folders[i][0]] += 1
        names[i] = folders[i][0] if seen[folders[i][0]] == 1 else '%s (%d)' % (folders[i][0], seen[folders[i][0]])
    index = dict((i, k) for k, i in enumerate(used))
    mt.categories = [wtg.Category(index[i], names[i], 0) for i in used]
    for t, i in zip(mt.triggers, where):
        t.category_id = index[i]
    order = editor_order(mt)
    place = dict((k, i) for i, k in enumerate(order))
    pairs = sum(1 for x in range(len(order)) for y in range(x + 1, len(order))
                if place[x] > place[y] and live[x] and live[y] and _interact(info[x], info[y]))
    return collections.OrderedDict((names[i], where.count(i)) for i in used), pairs


def _restore(res, text, td, init_per_trigger, say, matcher, editor_files=None, object_names=None):
    lang = res.lang
    rep = res.report
    t0 = time.time()
    if td is None:
        from doctor.triggers import triggerdata
        td = triggerdata.load()
    try:
        src = _Source(text, lang)
    except (jass_ast.JassSyntaxError, lua_ast.LuaSyntaxError) as e:
        res.reason = 'the script does not parse: %s' % e
        return res
    sk = skeleton(src, lang, object_names)
    rep['skeleton'] = dict((k, sk.get(k)) for k in ('by', 'init_custom_triggers', 'run_initialization_triggers',
                                                   'init_globals', 'main', 'config'))
    if sk['reason']:
        res.reason = sk['reason']
        return res
    if sk.get('late_created'):
        res.proofs['created_in_main'] = _late_created_proof(sk['late_created'])
        rep['late_created'] = len(sk['late_created']['moved'])
    if sk.get('rebuilt'):
        text, src, init_per_trigger = _rebuilt_restore(res, sk['rebuilt'], init_per_trigger)
    obfuscated = sk['by'] == 'structure'
    rep['obfuscated'] = obfuscated
    rep['labelled'] = sum(1 for i, name in (sk.get('names') or {}).items() if name != i[len('InitTrig_'):])
    rep['renamed'] = len(sk['renames'])
    if obfuscated:
        rep['skeleton']['found_as'] = dict((new, old) for old, new in sk['renames'].items()
                                           if new in (ICT, RIT, 'InitGlobals'))
    names = dict(sk['names'])
    if sk['renames']:
        text = _rename(text, sk['renames'])
        src = _Source(text, lang)
        say('skeleton by structure: %d names remade in the editor pattern' % len(sk['renames']))
    inits = list(sk['triggers'])
    made = []
    if init_per_trigger:
        text2, made, note = _init_per_trigger(src, sk, names)
        rep['init_per_trigger'] = note or 'done'
        if made:
            text = text2
            src = _Source(text, lang)
            for new, name in made:
                names['InitTrig_' + new] = name
            inits = ['InitTrig_' + new for new, _n in made] + inits
            say('init per trigger: %s' % ', '.join(n for n, _x in made))
    rep['init_triggers'] = [name for _n, name in made]
    pre = src
    devo = []
    if lang == JASS:
        devo = [n for n in PE.skeleton_names(text) if n not in (ICT, RIT)]
        if devo:
            text = PE.rename_skeleton(text, devo)
            src = _Source(text, lang)
    rep['devo_renamed'] = devo
    rit_idents = _rit_idents(src, sk['run_initialization_triggers'])
    if rit_idents is None:
        res.reason = 'RunInitializationTriggers does more than run triggers'
        return res
    idents = [i[len('InitTrig_'):] for i in inits]
    disabled = []
    if sk['by'] == 'name':
        for n, d in src.globals.items():
            x = n[len('gg_trg_'):]
            if (n.startswith('gg_trg_') and d.type in ('trigger', None) and not d.is_array and not d.is_constant and
                    x not in idents and 'InitTrig_' + x not in src.functions and d.value in (None, 'null', 'nil') and
                    _identifier_ok(x, x)):
                disabled.append(x)
    order, disabled = _trigger_order(src, inits, disabled)
    missing = [x for x in rit_idents if x not in idents]
    if missing:
        res.reason = 'RunInitializationTriggers runs gg_trg_%s, which InitCustomTriggers does not create' % missing[0]
        return res
    mod, why = _load_matcher(lang, matcher)
    nodes = {}
    if mod is not None:
        try:
            nodes = mod.script_functions(src.tree)
        except Exception as e:
            mod, why = None, 'script_functions: %s: %s' % (type(e).__name__, e)
    rep['matcher'] = why or getattr(mod, '__name__', 'given')
    variables, vtypes = [], {}
    if mod is not None:
        try:
            variables, vtypes = mod.match_globals(pre.tree, td)
        except Exception as e:
            rep['match_globals_error'] = '%s: %s' % (type(e).__name__, e)
    wtg_vars, kept_vars, initialized = _usable_variables(variables, src, td, lang)
    rep['variables_in_header'] = kept_vars
    rep['declarations_initialized'] = initialized
    gtypes = dict(vtypes)
    gtypes.update(('udg_' + v.name, v.type) for v in wtg_vars)
    custom = getattr(mod, 'CUSTOM_GLOBAL', None)
    if custom:
        gtypes.update((n, custom) for n in kept_vars)
    own, header, problems = _ownership(src, inits)
    if problems:
        res.reason = 'the custom script cannot be separated from the triggers: %s' % problems[0]
        return res
    mt_vars = wtg.MapTriggers(categories=[wtg.Category(0, CATEGORY, 0)], variables=wtg_vars)
    rep['optimized'] = bool(obfuscated or (rep.get('rebuilt') or {}).get('host') == 'main' or
                            (rep.get('optimizer') or {}).get('copies'))
    ctx = _Context(src, td, lang, mod, nodes, gtypes, mt_vars, own, header, set(rit_idents), set(order),
                   set(v.name for v in wtg_vars), rep['optimized'])
    decisions = collections.OrderedDict()
    for init in inits:
        d = _Decision(init, names.get(init) or init[len('InitTrig_'):], own[init])
        why_text = 'no matcher (%s)' % why if mod is None else _gui(ctx, d, obfuscated)
        if why_text:
            _text_trigger(ctx, d, obfuscated, why_text)
        else:
            ctx.header.update(d.external)
        decisions[d.ident] = d
    triggers = []
    texts = []
    pos = dict((n, k) for k, n in enumerate(src.functions))
    for x in order:
        d = decisions.get(x)
        if d is None:
            triggers.append(wtg.Trigger(x, NOTE_DISABLED, 0, 0, 0, 0, 0, 0, []))
            texts.append(None)
            continue
        if d.init in ['InitTrig_' + n for n, _y in made] and d.kind == 'gui':
            d.trigger.description = NOTE_INIT % d.name[:-len('_Init')] if d.trigger.description in (
                '', NOTE_RENAMED) else d.trigger.description
        triggers.append(d.trigger)
        if d.kind == 'text':
            texts.append(''.join(src.texts[f].rstrip('\n') + '\n' for f in sorted(d.own, key=pos.get)))
        else:
            texts.append(None)
    mt = wtg.MapTriggers(7, None, 2, [wtg.Category(0, CATEGORY, 0)], wtg_vars, triggers)
    rep['categories'], rep['category_order_risk'] = categorize(mt, td, texts, lang)
    res.triggers = mt
    removed = set([ICT, RIT])
    for d in decisions.values():
        removed |= (d.covered if d.kind == 'gui' else set(d.own))
    removed_globals = set('udg_' + v.name for v in wtg_vars) | set('gg_trg_' + x for x in order)
    header_text = _header_text(src, removed, removed_globals)
    rep['timing_decide'] = round(time.time() - t0, 3)
    _assemble(res, src, td, mt, texts, header_text, decisions, editor_files)
    rep['gui'] = sum(1 for d in decisions.values() if d.kind == 'gui')
    rep['text'] = [{'name': d.name, 'reason': d.reason} for d in decisions.values() if d.kind == 'text']
    rep['disabled'] = [x for x in order if x not in decisions]
    rep['custom_lines'] = sum(d.custom for d in decisions.values() if d.kind == 'gui')
    rep['gui_clean'] = sum(1 for d in decisions.values() if d.kind == 'gui' and not d.custom)
    rep['only_custom'] = sum(1 for d in decisions.values() if d.kind == 'text' and d.reason == ONLY_CUSTOM)
    rep['empty_custom_removed'] = sum(d.empty for d in decisions.values())
    rep['variables'] = len(wtg_vars)
    rep['external_to_header'] = sorted(set(n for d in decisions.values() for n in d.external))
    rep['object_globals_used'] = sorted(set(v for d in decisions.values() if d.kind == 'gui'
                                            for v in _variable_refs(d.trigger) if v.startswith(OBJECT_PREFIXES)))
    rep['time'] = round(time.time() - t0, 3)
    return res


EDITOR_MAIN_LUA = ('function main()\n    InitBlizzard()\n    InitGlobals()\n    InitCustomTriggers()\n'
                   '    RunInitializationTriggers()\nend\n\nfunction config()\nend\n')


def _triggers_code(mt, td, texts, lang):
    out = []
    for t, tx in zip(mt.triggers, texts):
        if t.enabled and not t.is_comment:
            code = gui_render.render_trigger(t, td, mt, lang, tx)
            out.append(code if code.endswith('\n') else code + '\n')
    return ''.join(out)


RX_NATIVE_LINE = re.compile(r'(?m)^[ \t]*(?:constant[ \t]+)?native[ \t][^\n]*\n?')
RX_GLOBALS_BLOCK = re.compile(r'(?ms)^[ \t]*globals[ \t]*(?://[^\n]*)?\n(.*?)^[ \t]*endglobals[ \t]*(?://[^\n]*)?\n?')


def _expected_jass(mt, td, header_text, texts):
    prefix, rest = PE.split_comment(header_text)
    globais, funcoes, main, config = PE.split_script(rest)
    globais += ''.join(m.group(1) for m in RX_GLOBALS_BLOCK.finditer(funcoes))
    funcoes = RX_GLOBALS_BLOCK.sub('', funcoes)
    natives = ''.join(m.group(0) for m in RX_NATIVE_LINE.finditer(funcoes))
    funcoes = RX_NATIVE_LINE.sub('', funcoes)
    eg = gui_render.render_globals(mt, td, JASS)
    k = eg.rindex('endglobals')
    return ''.join([prefix, eg[:k], globais, eg[k:], natives, gui_render.render_init_globals(mt, td, JASS), funcoes,
                    '' if funcoes.endswith('\n') else '\n', _triggers_code(mt, td, texts, JASS),
                    gui_render.render_init_custom_triggers(mt, JASS),
                    gui_render.render_run_initialization_triggers(mt, JASS),
                    'function main takes nothing returns nothing\n', PE.mark_dovjassinit(main), 'endfunction\n',
                    'function config takes nothing returns nothing\n', config, 'endfunction\n'])


def _generated_lua(mt, td, texts):
    return ''.join([gui_render.render_init_globals(mt, td, LUA), _triggers_code(mt, td, texts, LUA),
                    gui_render.render_init_custom_triggers(mt, LUA),
                    gui_render.render_run_initialization_triggers(mt, LUA)])


def _effective_lua(header_src, generated_src, private):
    fns = dict(header_src.texts)
    twice = []
    for n, t in generated_src.texts.items():
        if n in private:
            continue
        if n in fns and n not in ('InitGlobals',):
            twice.append(n)
        fns[n] = t
    return fns, twice


def _closure_text(fns, root):
    return '\n'.join(fns[n] for n in gui_render.closure(fns, root))


def _same_closure(fns_a, fns_b, root, ident, lang):
    ca = gui_render.canonical(_closure_text(fns_a, root), lang, True, ident)
    cb = gui_render.canonical(_closure_text(fns_b, root), lang, True, ident)
    return ca == cb, ('' if ca == cb else _first_difference(ca, cb))


def _expected_proof(src, fns, globs, twice, decisions, header_names, lang, idents=()):
    problems = []
    if twice:
        problems.append('defined twice: %s' % ', '.join(sorted(twice)[:3]))
    orig = src.texts
    for d in decisions.values():
        if d.init not in fns:
            problems.append('trigger %s: no %s' % (d.name, d.init))
            continue
        same, diff = _same_closure(fns, orig, d.init, d.ident, lang)
        if not same:
            problems.append('trigger %s: %s' % (d.name, diff))
    for n in sorted(header_names | (set((ICT, RIT)) & set(orig))):
        if n not in fns:
            problems.append('%s is missing' % n)
        elif gui_render.canonical(fns[n], lang, False) != gui_render.canonical(orig[n], lang, False):
            problems.append('%s differs: %s' % (n, _first_difference(gui_render.canonical(fns[n], lang, False),
                                                                      gui_render.canonical(orig[n], lang, False))))
    rendered = set(n for d in decisions.values() if d.kind == 'gui' for n in d.rendered)
    covered = set(n for d in decisions.values() if d.kind == 'gui' for n in d.covered)
    extra = sorted(set(fns) - set(orig) - rendered - {'InitGlobals'})
    lost = sorted(set(orig) - set(fns) - covered)
    if extra:
        problems.append('functions the original does not have: %s' % ', '.join(extra[:3]))
    if lost:
        problems.append('functions lost: %s' % ', '.join(lost[:3]))
    normalized = 0
    for n, d in src.globals.items():
        e = globs.get(n)
        same, norm = _same_declaration(d, e, lang)
        if not same:
            problems.append('global %s: %r / %r' % (n, e.text.strip() if e else None, d.text.strip()))
        normalized += norm
    added = 0
    for n in sorted(set(globs) - set(src.globals)):
        if n.startswith('gg_trg_') and n[len('gg_trg_'):] in idents and not re.search(r'\b%s\b' % n, src.text):
            added += 1
        else:
            problems.append('global %s is not in the original' % n)
    detail = ('%d triggers, %d custom script functions, %d globals equal to the original%s%s' % (
        len(decisions), len(header_names), len(src.globals),
        '' if not normalized else ' (%d declared without a value get the editor\'s default)' % normalized,
        '' if not added else '; %d gg_trg_ the editor adds for triggers the original never names' % added))
    if problems:
        detail = '%d differences: %s' % (len(problems), '; '.join(problems[:3]))
    return not problems, detail, problems


RX_PJASS_WHERE = re.compile(r'^(?:[A-Za-z]:)?[^:]*:\d+:\s*')


def _pjass_errors(result):
    return collections.Counter(RX_PJASS_WHERE.sub('', x) for x in result['line_list'] if RX_PJASS_WHERE.match(x))


def _pjass_proof(expected, original):
    try:
        from doctor.script import pjass
    except ImportError as e:
        return True, 'skipped: %s' % e
    exe = pjass.exe()
    if not os.path.isfile(exe):
        return True, 'skipped: no pjass at %s' % exe
    ref = pjass.game_scripts_dir(REF_DIR)
    if not ref:
        return True, 'skipped: no 3.0 common.j/Blizzard.j to compile against'
    tmp = tempfile.mkdtemp(prefix='trigger_restore_')
    try:
        out = {}
        for tag, code in (('expected', expected), ('original', original)):
            path = os.path.join(tmp, tag + '.j')
            with open(path, 'wb') as f:
                f.write(code.encode('utf-8', 'surrogateescape'))
            out[tag] = pjass.run_action([(os.path.join(ref, 'common.j'), 'common.j'),
                                         (os.path.join(ref, 'blizzard.j'), 'Blizzard.j'),
                                         (path, 'war3map.j')], tmp=os.path.join(tmp, tag))
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    e, o = _pjass_errors(out['expected']), _pjass_errors(out['original'])
    new = e - o
    ok = not new and (out['expected']['rc'] == 0 or out['original']['rc'] != 0)
    detail = 'rc=%s, %d error(s) (the original: rc=%s, %d)' % (out['expected']['rc'], sum(e.values()),
                                                             out['original']['rc'], sum(o.values()))
    if new:
        detail += '; new: %s' % ' | '.join(list(new)[:3])
    return ok, detail


def _lua_compiles(code, what):
    err = PE.compile_lua(code)
    if err == 'no_lupa':
        return True, 'skipped: no lupa'
    return err is None, '%s compiles in Lua 5.3' % what if err is None else '%s: %s' % (what, err)


LUA_SANDBOX = r'''
return function(chunk, idents, probe_var)
  local stub
  local smt = {}
  stub = setmetatable({}, smt)
  smt.__index = function(t, k) if type(k) == 'string' then return stub end return nil end
  smt.__newindex = function() end
  smt.__call = function() return stub end
  for _, op in ipairs({'__add', '__sub', '__mul', '__div', '__mod', '__pow', '__unm', '__idiv', '__band', '__bor',
                       '__bxor', '__shl', '__shr', '__bnot'}) do smt[op] = function() return 0 end end
  smt.__concat = function(a, b) return (type(a) == 'string' and a or '') .. (type(b) == 'string' and b or '') end
  smt.__lt = function() return false end
  smt.__le = function() return false end
  smt.__len = function() return 0 end
  local base = {string = string, math = math, table = table, setmetatable = setmetatable, getmetatable = getmetatable,
    rawset = rawset, rawget = rawget, rawequal = rawequal, rawlen = rawlen, pairs = pairs, ipairs = ipairs,
    next = next, type = type, tostring = tostring, tonumber = tonumber, select = select, error = error,
    pcall = pcall, xpcall = xpcall, assert = assert, print = function() end, coroutine = coroutine, utf8 = utf8}
  local G = {}
  setmetatable(G, {__index = function(t, k) local v = base[k] if v ~= nil then return v end return stub end})
  G._G = G
  local r = {}
  debug.sethook(function() error('the sandbox ran too long') end, '', 20000000)
  local f, err = load(chunk, '=war3map.lua', 't', G)
  if not f then debug.sethook() r.error = 'compile: ' .. tostring(err) return r end
  local ok, e = pcall(f)
  if not ok then debug.sethook() r.error = 'load: ' .. tostring(e) return r end
  local main = rawget(G, 'main')
  r.ict = rawget(G, 'InitCustomTriggers') ~= nil
  local missing = {}
  for _, x in ipairs(idents) do if rawget(G, 'InitTrig_' .. x) == nil then missing[#missing + 1] = x end end
  r.missing = table.concat(missing, ' ')
  if main then
    local ok2, e2 = pcall(main)
    r.main_error = ok2 and '' or tostring(e2)
  else
    r.main_error = 'no main in _G'
  end
  r.marker = rawget(G, '__devo_marker') == true
  local unset = {}
  for _, x in ipairs(idents) do if rawget(G, 'gg_trg_' .. x) == nil then unset[#unset + 1] = x end end
  r.unset = table.concat(unset, ' ')
  r.by = 'main'
  if #unset > 0 and rawget(G, 'InitCustomTriggers') then
    pcall(rawget(G, 'InitCustomTriggers'))
    local still = {}
    for _, x in ipairs(idents) do if rawget(G, 'gg_trg_' .. x) == nil then still[#still + 1] = x end end
    r.unset = table.concat(still, ' ')
    r.by = 'InitCustomTriggers'
  end
  local w = rawget(G, '__devo_probe_write')
  if w then pcall(w) end
  r.write = rawget(G, probe_var) == 12345
  local rd = rawget(G, '__devo_probe_read')
  r.read = rd ~= nil and main ~= nil and rd() == main
  debug.sethook()
  return r
end
'''


def _lua_env_proof(header_text, private, mt, td, texts, generated_src):
    try:
        from lupa import lua53
    except Exception:
        return True, 'skipped: no lupa'
    code_only = _code_only(''.join(generated_src.texts.values()), LUA)
    if private:
        hit = re.search(r'(?<![\w.:])(%s)\s*=(?!=)' % '|'.join(sorted(map(re.escape, private))), code_only)
        if hit:
            return False, 'the triggers assign %s, which the custom script routes apart' % hit.group(1)
    hsrc = _Source(header_text, LUA)
    marked = header_text
    fn = hsrc.functions.get('main')
    m = re.compile(r'function\s+main\s*\(\s*\)').match(header_text, fn.start) if fn else None
    if m:
        marked = header_text[:m.end()] + ' __devo_marker = true; ' + header_text[m.end():]
    probe = 'udg_' + mt.variables[0].name if mt.variables else 'udg___devo_probe'
    chunk = ''.join([gui_render.render_globals(mt, td, LUA), lua_custom_script(marked, private),
                     _generated_lua(mt, td, texts), EDITOR_MAIN_LUA,
                     'function __devo_probe_write()\n    %s = 12345\nend\n' % probe,
                     'function __devo_probe_read()\n    return main\nend\n'])
    idents = [gui_render.trigger_identifier(t.name) for t in mt.triggers if t.enabled and not t.is_comment]
    try:
        lua = lua53.LuaRuntime(register_eval=False, unpack_returned_tuples=True)
        run = lua.execute(LUA_SANDBOX)
        r = run(chunk.encode('utf-8', 'surrogateescape'), lua.table_from(idents), probe)
        r = dict((k, r[k]) for k in r)
    except Exception as e:
        return False, 'the sandbox failed: %s: %s' % (type(e).__name__, str(e)[:200])
    r = dict((k, v.decode('utf-8', 'replace') if isinstance(v, bytes) else v) for k, v in r.items())
    if r.get('error'):
        return False, r['error'][:200]
    checks = [('the map\'s main runs from _G', bool(r.get('marker')) or not m),
              ('InitCustomTriggers in _G', bool(r.get('ict'))),
              ('every InitTrig_ in _G', not r.get('missing')),
              ('the triggers created (by %s)' % r.get('by'), not r.get('unset')),
              ('a global written after the _ENV line reaches _G', bool(r.get('write'))),
              ('main read after the _ENV line is the map\'s', bool(r.get('read')))]
    bad = [c for c, ok in checks if not ok]
    detail = '%d triggers; %s%s' % (len(idents), '; '.join(c for c, _ok in checks) if not bad else
                                    'FAILED: ' + '; '.join(bad),
                                    '; main stopped early in the sandbox: %s' % r['main_error'][:80]
                                    if r.get('main_error') else '')
    return not bad, detail


def _editor_fit(res, src, td, mt, texts, header_text, editor_files):
    from doctor.triggers import editor_render
    reference = _expected_jass(mt, td, header_text, texts)
    f = editor_render.fit(header_text, editor_files, td, mt, texts, reference=reference, original=src.text,
                          triggers=_triggers_code(mt, td, texts, JASS))
    res.report['editor_save'] = {'ok': f.ok, 'level': f.level, 'globals_to_editor': len(f.dropped),
                                 'functions_to_editor': list(f.replaced), 'objects_named': len(f.objects),
                                 'inject': f.inject, 'lines': list(f.lines), 'reason': f.reason, 'notes': f.notes[:3]}
    return f if f.ok else None


def _assemble(res, src, td, mt, texts, header_text, decisions, editor_files=None):
    lang, proofs, rep = res.lang, res.proofs, res.report
    fitted = _editor_fit(res, src, td, mt, texts, header_text, editor_files) if (
        lang == JASS and editor_files is not None) else None
    if fitted is not None and fitted.objects:
        mt, texts = fitted.triggers, fitted.texts
        res.triggers = mt
        rep['categories'], rep['category_order_risk'] = categorize(mt, td, texts, lang)
    try:
        res.wtg = wtg.write_wtg(mt, td)
        back = wtg.read_wtg(res.wtg, td)
        ecas = wtg.count_ecas(back)[0]
        proofs['wtg_reread'] = (back == mt, '%s B, classic v7, %d triggers, %d variables, %d ECAs, read to the last '
                                'byte%s' % (format(len(res.wtg), ','), len(back.triggers), len(back.variables), ecas,
                                            '' if back == mt else ': the model read back DIFFERS'))
    except Exception as e:
        proofs['wtg_reread'] = (False, '%s: %s' % (type(e).__name__, e))
    try:
        hsrc = _Source(header_text, lang)
    except (jass_ast.JassSyntaxError, lua_ast.LuaSyntaxError) as e:
        proofs['partition'] = (False, 'the custom script does not parse: %s' % e)
        return
    header_names = set(hsrc.functions)
    places = collections.defaultdict(list)
    to_editor = set() if fitted is None else set(PE.SKELETON_PREFIX + x for x in fitted.replaced) | (
        set() if fitted.inject else {'main', 'config'})
    for n in header_names:
        places[n].append('editor' if n in to_editor else 'custom script')
    for d in decisions.values():
        for f in (d.covered if d.kind == 'gui' else d.own):
            places[f].append('%s %s' % (d.kind, d.name))
    for f in (ICT, RIT):
        if f in src.functions:
            places[f].append('editor')
    lost = sorted(set(src.functions) - set(places))
    twice = sorted(n for n, p in places.items() if len(p) > 1)
    extra = sorted(set(places) - set(src.functions))
    kinds = collections.Counter(p[0].split(' ')[0] for p in places.values())
    proofs['partition'] = (not lost and not twice and not extra and not hsrc.duplicates, (
        '%d functions = %d in the custom script + %d in GUI triggers + %d in text triggers + %d the editor writes' % (
            len(src.functions), kinds['custom'], kinds['gui'], kinds['text'], kinds['editor']) +
        ''.join('; %s: %s' % (k, ', '.join(v[:3])) for k, v in (('lost', lost), ('twice', twice), ('extra', extra))
                if v)))
    if lang == JASS:
        cs, _assembled = PE.custom_script(header_text) if fitted is None else PE.custom_script(fitted.header,
                                                                                           fitted.inject)
        res.header = cs.replace('\r\n', '\n')
    else:
        private = set(n for n in header_names if EDITOR_GENERATED.match(n) or PE.RX_SKELETON.fullmatch(n))
        private |= {'main', 'config'}
        rep['lua_private'] = sorted(private)
        header_text, rep['lua_final_return'] = lua_final_return(header_text)
        res.header = lua_custom_script(header_text, private)
        locals_ = _lua_top_locals(header_text)
        used = set()
        for d in decisions.values():
            for f in (d.covered if d.kind == 'gui' else d.own):
                used |= set(RX_WORD.findall(_code_only(src.texts[f], LUA))) & locals_
        proofs['lua_locals'] = (not used, 'no trigger uses a local of the custom script' if not used else
                                'the triggers use locals of the custom script: %s' % ', '.join(sorted(used)[:5]))
    ct = wtg.CustomText(False, '', _crlf(res.header), [None if t is None else _crlf(t) for t in texts], 1)
    res.wct = wtg.write_wct(ct)
    rep['percent_lines'] = 0 if lang != JASS else sum(
        1 for line in RX_STRING_OR_COMMENT.sub(lambda m: m.group(1) or '', res.header).split('\n') if '%' in line)
    rep['header_functions'] = len(header_names)
    conflicts = sorted(n for n in header_names if EDITOR_GENERATED.match(n) and n not in ('main', 'config'))
    rep['editor_name_conflicts'] = conflicts
    if lang == JASS:
        res.expected_script = _expected_jass(mt, td, header_text, texts)
        try:
            esrc = _Source(res.expected_script, JASS)
            fns, globs, dup = esrc.texts, esrc.globals, esrc.duplicates
        except jass_ast.JassSyntaxError as e:
            proofs['expected_equals_original'] = (False, 'the expected script does not parse: %s' % e)
            fns = None
    else:
        generated = _generated_lua(mt, td, texts)
        res.expected_script = ''.join([gui_render.render_globals(mt, td, LUA), res.header, generated, EDITOR_MAIN_LUA])
        try:
            gsrc = _Source(generated, LUA)
        except lua_ast.LuaSyntaxError as e:
            proofs['expected_equals_original'] = (False, 'the triggers the editor writes do not parse: %s' % e)
            res.ok = False
            return
        fns, dup = _effective_lua(hsrc, gsrc, private)
        esrc = _Source(gui_render.render_globals(mt, td, LUA), LUA)
        globs = dict(hsrc.globals)
        globs.update(esrc.globals)
    if fns is not None:
        idents = set(gui_render.trigger_identifier(t.name) for t in mt.triggers)
        ok, detail, problems = _expected_proof(src, fns, globs, dup, decisions, header_names, lang, idents)
        proofs['expected_equals_original'] = (ok, detail)
        rep['expected_differences'] = problems[:20]
    if lang == JASS:
        proofs['pjass'] = _pjass_proof(res.expected_script, src.text)
        if fitted is not None:
            res.expected_script = fitted.script
            proofs.update(fitted.proofs)
    else:
        a = _lua_compiles(res.header, 'the custom script')
        b = _lua_compiles(res.expected_script, 'the expected script')
        proofs['lua_compiles'] = (a[0] and b[0], a[1] if not a[0] or b[1].startswith('skipped') else b[1])
        proofs['lua_env'] = _lua_env_proof(header_text, private, mt, td, texts, gsrc)
    swapped = rep.get('category_order_risk', 0)
    proofs['editor_order'] = (not swapped, (
        'the editor writes InitCustomTriggers folder by folder: in %d folder(s), no two triggers that share an event '
        '(or run at map initialization) change places' % len(rep.get('categories') or ()) if not swapped else
        '%d pair(s) of triggers that share an event would change places in InitCustomTriggers' % swapped))
    res.ok = all(ok for ok, _d in proofs.values())


def standard_script(text, players=None, say=None, doo=None):
    try:
        new, rep = jass_normal.standard(text, players)
        new, rep['setup'] = jass_setup.setup(new, doo)
    except Exception as e:
        return text, {'error': '%s: %s' % (type(e).__name__, str(e)[:200]), 'changed': False}
    rep['changed'] = new != text
    if not rep['changed']:
        return text, rep
    ok, rep['pjass'] = _pjass_proof(new, text)
    if not ok:
        rep['refused'], rep['changed'] = True, False
        return text, rep
    if rep['copies'] and say:
        say('optimizer: %d copies of game functions put back (%d calls)' % (len(rep['copies']), rep['calls']))
    return new, rep


def restore(script_text, lang=JASS, td=None, init_per_trigger=True, log=None, matcher=None, editor_files=None,
            players=None, standard=None, object_names=None):
    lang = LUA if lang == LUA else JASS
    res = Restoration(lang)
    say = log or (lambda *a: None)
    try:
        text = _normalize(script_text)
        if lang == JASS:
            if standard is None:
                text, standard = standard_script(text, players, say)
            res.report['optimizer'] = standard
            if standard.get('changed'):
                res.proofs['standard_library'] = (True, (
                    '%d calls of %d copies of game functions renamed, %d neutral players by their constant; pjass: %s'
                    % (standard.get('calls', 0), len(standard.get('copies') or ()),
                       standard.get('neutral_players', 0), standard.get('pjass'))))
        return _restore(res, text, td, init_per_trigger, say, matcher, editor_files, object_names)
    except Exception as e:
        import traceback
        res.ok = False
        res.reason = 'internal error: %s: %s' % (type(e).__name__, str(e)[:200])
        res.report['traceback'] = traceback.format_exc()[-3000:]
        return res


def outcome(res):
    proofs = dict((k, bool(v[0]) if isinstance(v, (tuple, list)) else bool(v)) for k, v in (res.proofs or {}).items())
    return (bool(res.ok), res.reason or '', res.wtg, res.wct, res.header, dict(res.report or {}), proofs, summary(res))


def optimizer_lines(o):
    lines = []
    if o.get('copies') and not o.get('refused'):
        names = sorted(set(o['copies'].values()))
        lines.append('The script had its own copy of %d game function%s (%s%s), left by an optimizer or by the editor '
                     'that built the map: %d call%s the game\'s own again%s.'
                     % (len(names), '' if len(names) == 1 else 's', ', '.join(names[:4]),
                        ', ...' if len(names) > 4 else '', o.get('calls', 0),
                        ' uses' if o.get('calls', 0) == 1 else 's use', '' if not o.get('versions') else
                        '; %d of the copies did the same work another way' % len(o['versions'])))
    made = (o.get('setup') or {}).get('functions') or {}
    named = (o.get('setup') or {}).get('objects') or {}
    if made and not o.get('refused'):
        cut = sorted(k for k, v in made.items() if isinstance(v, int))
        lines.append('The setup functions of the editor are functions again (%s)%s.' % (
            ', '.join(sorted(made)), '' if not cut else ': an optimizer had dissolved %s into main'
            % ', '.join(cut)))
    if named and not o.get('refused'):
        words = {'snd': 'sounds', 'rct': 'regions', 'cpath': 'cameras', 'dst': 'destructibles', 'unit': 'units',
                 'item': 'items'}
        lines.append('The placed objects the triggers use have the editor\'s names again (gg_rct_Region_001...): %s.'
                     % ', '.join('%d %s' % (n, words.get(k, k)) for k, n in sorted(named.items())))
    if o.get('neutral_players') and not o.get('refused'):
        lines.append('This is a map of 12 players: %d places named a neutral player by its number (Player(12) to '
                     'Player(15)) and now use its constant, which stays right when the World Editor saves the map for '
                     '24 players. Code that counts players another way (a loop to 12 or 16) still needs a look.'
                     % o['neutral_players'])
    return lines


def summary(res):
    if res.reason:
        return ['Triggers: not restored (%s); the script stays in the custom script.' % res.reason] + \
            optimizer_lines((res.report or {}).get('optimizer') or {})
    r = res.report
    lines = ['Triggers restored from the %s script: %d GUI, %d as text%s, %d variables%s.' % (
        'Lua' if res.lang == LUA else 'JASS', r.get('gui', 0), len(r.get('text', ())),
        ', %d disabled (only the name)' % len(r['disabled']) if r.get('disabled') else '', r.get('variables', 0),
        '' if not r.get('obfuscated') else '; the protector removed the names: %d triggers are named after what fires '
        'them, %d keep a number' % (r.get('labelled', 0), r.get('gui', 0) + len(r.get('text', ())) -
                                    r.get('labelled', 0)))]
    if r.get('gui'):
        mixed = r['gui'] - r.get('gui_clean', 0)
        lines.append('Of the GUI triggers, %d have every action as a GUI action%s.' % (
            r.get('gui_clean', 0), '' if not mixed else '; the other %d keep %d lines of custom script among their '
            'actions (code the trigger editor has no action for)' % (mixed, r.get('custom_lines', 0))))
    if _is_typescript(res.header or '', res.lang):
        lines.append('Most of the map\'s code was compiled from TypeScript (TypeScriptToLua): it was never editor '
                     'triggers, so it stays in the custom script.')
    lines.extend(optimizer_lines(r.get('optimizer') or {}))
    rb = r.get('rebuilt')
    if rb and rb['host'] == 'main':
        lines.append('The trigger setup was inlined into main by an optimizer: %d triggers were rebuilt from it (%s)%s.'
                     % (rb['triggers'], 'their names are lost' if rb['by'] == 'structure' else
                        'the names from the gg_trg_ globals', ', with %d text trigger(s) for the code that ran '
                        'between two setups' % rb['wrappers'] if rb['wrappers'] else ''))
    elif rb:
        lines.append('InitCustomTriggers also ran code that is not a trigger\'s InitTrig_ (%s): %d text trigger(s) run '
                     'it at the same place.' % (', '.join(rb.get('moved', ())[:3]), rb['triggers']))
    cats = r.get('categories') or {}
    if len(cats) > 1:
        lines.append('Grouped into %d folders by what fires them, in an order that keeps the triggers of one event as '
                     'the script creates them (the World Editor writes the triggers folder by folder): %s'
                     % (len(cats), ', '.join('%s %d' % kv for kv in cats.items())))
    elif list(cats) == [CATEGORY] and sum(cats.values()) > 1:
        lines.append('All the triggers are in one folder: grouped by what fires them, the World Editor would write '
                     'them in another order than the script creates them.')
    text = [t for t in r.get('text', ()) if t['reason'] != ONLY_CUSTOM]
    if r.get('only_custom'):
        lines.append('  %d of the text triggers %s code from start to end (every action was custom script).'
                     % (r['only_custom'], 'is' if r['only_custom'] == 1 else 'are'))
    for t in text[:10]:
        lines.append('  text: %s (%s)' % (t['name'], t['reason'][:100]))
    if len(text) > 10:
        lines.append('  ... and %d more text triggers' % (len(text) - 10))
    made = r.get('init_triggers', ())
    if made:
        lines.append('  %d new initialization trigger(s), what an InitTrig_ did besides registering, run first: %s%s'
                     % (len(made), ', '.join(made[:5]), ', ...' if len(made) > 5 else ''))
    if r.get('percent_lines'):
        lines.append('%d line(s) of the custom script have a %% inside a text: in the one map saved by the World '
                     'Editor 3.0 that was measured, those %% were gone from the saved script (a text "50%%" became '
                     '"50"). After you save, check one of them.' % r['percent_lines'])
    fit = r.get('editor_save')
    if fit and fit.get('ok'):
        lines.append('Saving from the World Editor proven: the script it writes compiles and runs the map\'s own code; '
                     '%d globals and %d functions it writes itself left the custom script%s%s.' % (
                         fit['globals_to_editor'], len(fit['functions_to_editor']),
                         '' if fit['inject'] else ', main and config too',
                         '' if not fit['objects_named'] else '; %d placed objects named in the disabled trigger %r'
                         % (fit['objects_named'], 'Custom script objects')))
    elif fit:
        lines.append('Saving from the World Editor not proven (%s): the custom script stays as before.'
                     % (fit.get('reason') or '?')[:160])
    bad = [k for k, (ok, _d) in res.proofs.items() if not ok]
    lines.append('Proofs: %s' % ('all passed' if not bad else 'FAILED: ' + ', '.join(bad)))
    return lines

