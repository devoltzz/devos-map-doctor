# Rebuilds the GUI triggers of a map from its script, with a round-trip proof for each one.
import bisect
import collections
import inspect
import os
import re
import tempfile
import time

import gui_render
import jass_ast
import lua_ast
import editor_prep as PE
import wtg


HERE = os.path.dirname(os.path.abspath(__file__))
REF_DIR = os.path.normpath(os.path.join(HERE, '..', 'ref', '3.0'))
JASS, LUA = 'jass', 'lua'
CATEGORY = 'Restored triggers'
ICT, RIT = 'InitCustomTriggers', 'RunInitializationTriggers'
NOTE_RENAMED = 'Restored from the map script. The original name was removed by the protector.'
NOTE_TEXT = 'Restored from the map script as text (it could not be proven as GUI): %s'
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
            r = self._refs[name] = (words & set(self.functions)) - {name}
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


def _skeleton_by_structure(src):
    sk = {'by': 'structure', 'reason': '', 'renames': {}}
    if src.lang != JASS:
        sk['reason'] = 'no editor skeleton: no InitCustomTriggers (the search by structure is for JASS)'
        return sk
    if 'main' not in src.functions:
        sk['reason'] = 'no main function'
        return sk
    funcs = collections.OrderedDict((n, _structure_body(f)) for n, f in src.functions.items())
    triggers = set(n for n, d in src.globals.items() if d.type == 'trigger' and not d.is_array)
    init_like = collections.OrderedDict()
    for n, body in funcs.items():
        m = re.search(r'^\s*set\s+(\w+)\s*=\s*CreateTrigger\s*\(\s*\)', body, re.M)
        if m and m.group(1) in triggers and ('TriggerAddAction' in body or 'TriggerAddCondition' in body):
            init_like[n] = m.group(1)
    main_calls = re.findall(r'call\s+(\w+)\s*\(', funcs['main'])

    def only(body, test):
        lines = [x.strip() for x in body.split('\n') if x.strip() and not x.strip().startswith('//')]
        return bool(lines) and all(test(x) for x in lines)

    ict = next((n for n, body in funcs.items() if n in main_calls and only(
        body, lambda x: re.match(r'call\s+(\w+)\s*\(\s*\)$', x) and
        re.match(r'call\s+(\w+)', x).group(1) in init_like)), None)
    if ict is None:
        sk['reason'] = 'no editor skeleton: no InitCustomTriggers by name or by structure'
        return sk
    rit = next((n for n, body in funcs.items() if n in main_calls and n != ict and only(
        body, lambda x: re.match(r'call\s+ConditionalTriggerExecute\s*\(\s*\w+\s*\)$', x))), None)
    called = []
    for x in re.findall(r'call\s+(\w+)\s*\(', funcs[ict]):
        if x not in called:
            called.append(x)
    ren = {}
    order = [x for x in called if x in init_like] + [x for x in init_like if x not in called]
    for k, f in enumerate(order, 1):
        ren[f] = 'InitTrig_T%03d' % k
        ren[init_like[f]] = 'gg_trg_T%03d' % k
    ren[ict] = ICT
    if rit:
        ren[rit] = RIT
    for f in order:
        base = ren[f][len('InitTrig_'):]
        seen, stack = [], [f]
        while stack:
            x = stack.pop()
            if x in seen:
                continue
            seen.append(x)
            for r in re.findall(r'\b(\w+)\b', funcs[x]):
                if r in funcs and r not in ren and r not in seen and r not in ('main', 'config'):
                    stack.append(r)
        n = 0
        for x in seen[1:]:
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
    if clash:
        sk['reason'] = 'the editor names %s already exist in the script' % ', '.join(clash[:3])
        return sk
    sk['renames'] = ren
    sk['triggers'] = [ren[f] for f in called if f in init_like]
    sk['init_custom_triggers'] = ICT
    sk['run_initialization_triggers'] = RIT if rit else None
    sk['init_globals'] = 'InitGlobals' if 'InitGlobals' in ren.values() else None
    return sk


def _rename(text, renames):
    if not renames:
        return text
    rx = re.compile(r'\b(' + '|'.join(sorted(map(re.escape, renames), key=len, reverse=True)) + r')\b')
    return rx.sub(lambda m: renames[m.group(1)], text)


def skeleton(script, lang=JASS):
    lang = LUA if lang == LUA else JASS
    if isinstance(script, _Source):
        src = script
    else:
        try:
            src = _Source(_normalize(script), lang)
        except (jass_ast.JassSyntaxError, lua_ast.LuaSyntaxError) as e:
            return {'by': None, 'reason': 'the script does not parse: %s' % e, 'renames': {}}
    sk = _skeleton_by_name(src)
    if sk is None:
        sk = _skeleton_by_structure(src)
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
            names = dict((i, i[len('InitTrig_'):]) for i in sk['triggers'])
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
    edits, made = [], []
    for init in sk['triggers']:
        f = src.functions[init]
        node = f.node
        if node.locals or node.params:
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
        return src.text, [], 'no InitTrig_ does more than register'
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
            matcher = __import__(name)
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
    def __init__(self, src, td, lang, mod, nodes, gtypes, mt_vars, own, header, rit_idents, all_idents, var_names):
        self.src, self.td, self.lang, self.mod, self.nodes = src, td, lang, mod, nodes
        self.gtypes, self.mt_vars, self.own, self.header = gtypes, mt_vars, own, header
        self.rit_idents, self.all_idents, self.var_names = rit_idents, all_idents, var_names
        self.source_kw = False
        if mod is not None:
            try:
                self.source_kw = 'source' in inspect.signature(mod.match_trigger).parameters
            except (TypeError, ValueError):
                pass
        self.words = collections.Counter(RX_WORD.findall(src.text))
        self.owner = {}
        for i, fs in own.items():
            for f in fs:
                self.owner[f] = i


def _gui(ctx, d, obfuscated):
    src, td, lang = ctx.src, ctx.td, ctx.lang
    kw = {'source': src.text} if ctx.source_kw else {}
    try:
        m = ctx.mod.match_trigger(ctx.nodes, d.init, td, ctx.gtypes, d.name, **kw)
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
    merged = dict(src.texts, **rendered)
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
    return ''


def _text_trigger(ctx, d, obfuscated, reason):
    src = ctx.src
    desc = _banner(src, d.own)[1] or (NOTE_TEXT % reason)
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
    wanted = set(enabled) | set(disabled)
    declared = [n[len('gg_trg_'):] for n in src.globals if n.startswith('gg_trg_') and n[len('gg_trg_'):] in wanted]
    if [x for x in declared if x in set(enabled)] == enabled:
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


def _event_keys(t, text, td, lang):
    keys = set()
    if t.is_text:
        for name, codes in _text_events(text, lang):
            keys.update(codes or (name,))
        return keys
    for f in t.functions:
        if f.kind == wtg.EVENT and f.enabled and f.name != 'MapInitializationEvent':
            codes = [td.presets[p.value].code for p in f.params if p.kind == wtg.PRESET and p.value in td.presets and
                     td.presets[p.value].code.startswith('EVENT_')]
            fd = td.events.get(f.name)
            keys.update(codes or ((fd.script_name if fd is not None else f.name),))
    return keys


def categorize(mt, td, texts=None, lang=JASS):
    texts = list(texts) if texts is not None else [None] * len(mt.triggers)
    names = [_category(t, x, td, lang) for t, x in zip(mt.triggers, texts)]
    used = [c for c in CATEGORIES if c in names]
    mt.categories = [wtg.Category(k, c, 0) for k, c in enumerate(used)]
    index = dict((c, k) for k, c in enumerate(used))
    for t, c in zip(mt.triggers, names):
        t.category_id = index[c]
    keys = [_event_keys(t, x, td, lang) if t.enabled and not t.is_comment else set()
            for t, x in zip(mt.triggers, texts)]
    pairs = sum(1 for i in range(len(names)) for j in range(i + 1, len(names))
                if index[names[i]] > index[names[j]] and keys[i] & keys[j])
    return collections.OrderedDict((c, names.count(c)) for c in used), pairs


def _restore(res, text, td, init_per_trigger, say, matcher):
    lang = res.lang
    rep = res.report
    t0 = time.time()
    if td is None:
        import triggerdata
        td = triggerdata.load()
    try:
        src = _Source(text, lang)
    except (jass_ast.JassSyntaxError, lua_ast.LuaSyntaxError) as e:
        res.reason = 'the script does not parse: %s' % e
        return res
    sk = skeleton(src, lang)
    rep['skeleton'] = dict((k, sk.get(k)) for k in ('by', 'init_custom_triggers', 'run_initialization_triggers',
                                                   'init_globals', 'main', 'config'))
    if sk['reason']:
        res.reason = sk['reason']
        return res
    obfuscated = sk['by'] == 'structure'
    rep['obfuscated'] = obfuscated
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
    own, header, problems = _ownership(src, inits)
    if problems:
        res.reason = 'the custom script cannot be separated from the triggers: %s' % problems[0]
        return res
    mt_vars = wtg.MapTriggers(categories=[wtg.Category(0, CATEGORY, 0)], variables=wtg_vars)
    ctx = _Context(src, td, lang, mod, nodes, gtypes, mt_vars, own, header, set(rit_idents), set(order),
                   set(v.name for v in wtg_vars))
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
            pos = dict((n, k) for k, n in enumerate(src.functions))
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
    _assemble(res, src, td, mt, texts, header_text, decisions)
    rep['gui'] = sum(1 for d in decisions.values() if d.kind == 'gui')
    rep['text'] = [{'name': d.name, 'reason': d.reason} for d in decisions.values() if d.kind == 'text']
    rep['disabled'] = [x for x in order if x not in decisions]
    rep['custom_lines'] = sum(d.custom for d in decisions.values() if d.kind == 'gui')
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
        import pjass
    except ImportError as e:
        return True, 'skipped: %s' % e
    exe = pjass.exe()
    if not os.path.isfile(exe):
        return True, 'skipped: no pjass at %s' % exe
    tmp = tempfile.mkdtemp(prefix='trigger_restore_')
    try:
        out = {}
        for tag, code in (('expected', expected), ('original', original)):
            path = os.path.join(tmp, tag + '.j')
            with open(path, 'wb') as f:
                f.write(code.encode('utf-8', 'surrogateescape'))
            out[tag] = pjass.run_action([(os.path.join(REF_DIR, 'common.j'), 'common.j'),
                                         (os.path.join(REF_DIR, 'blizzard.j'), 'Blizzard.j'),
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


def _assemble(res, src, td, mt, texts, header_text, decisions):
    lang, proofs, rep = res.lang, res.proofs, res.report
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
    for n in header_names:
        places[n].append('custom script')
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
        cs, _montado = PE.custom_script(header_text)
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
    else:
        a = _lua_compiles(res.header, 'the custom script')
        b = _lua_compiles(res.expected_script, 'the expected script')
        proofs['lua_compiles'] = (a[0] and b[0], a[1] if not a[0] or b[1].startswith('skipped') else b[1])
        proofs['lua_env'] = _lua_env_proof(header_text, private, mt, td, texts, gsrc)
    res.ok = all(ok for ok, _d in proofs.values())


def restore(script_text, lang=JASS, td=None, init_per_trigger=True, log=None, matcher=None):
    lang = LUA if lang == LUA else JASS
    res = Restoration(lang)
    try:
        return _restore(res, _normalize(script_text), td, init_per_trigger, log or (lambda *a: None), matcher)
    except Exception as e:
        import traceback
        res.ok = False
        res.reason = 'internal error: %s: %s' % (type(e).__name__, str(e)[:200])
        res.report['traceback'] = traceback.format_exc()[-3000:]
        return res


def outcome(res):
    proofs = dict((k, bool(v[0]) if isinstance(v, (tuple, list)) else bool(v)) for k, v in (res.proofs or {}).items())
    return (bool(res.ok), res.reason or '', res.wtg, res.wct, res.header, dict(res.report or {}), proofs, summary(res))


def summary(res):
    if res.reason:
        return ['Triggers: not restored (%s); the script stays in the custom script.' % res.reason]
    r = res.report
    lines = ['Triggers restored from the %s script: %d GUI, %d as text%s, %d variables%s.' % (
        'Lua' if res.lang == LUA else 'JASS', r.get('gui', 0), len(r.get('text', ())),
        ', %d disabled (only the name)' % len(r['disabled']) if r.get('disabled') else '', r.get('variables', 0),
        '; the names were remade (the protector removed them)' if r.get('obfuscated') else '')]
    cats = r.get('categories') or {}
    if cats:
        lines.append('Grouped into %d categories: %s' % (len(cats), ', '.join('%s %d' % kv for kv in cats.items())))
    text = r.get('text', ())
    for t in text[:10]:
        lines.append('  text: %s (%s)' % (t['name'], t['reason'][:100]))
    if len(text) > 10:
        lines.append('  ... and %d more text triggers' % (len(text) - 10))
    made = r.get('init_triggers', ())
    if made:
        lines.append('  %d new initialization trigger(s), what an InitTrig_ did besides registering, run first: %s%s'
                     % (len(made), ', '.join(made[:5]), ', ...' if len(made) > 5 else ''))
    bad = [k for k, (ok, _d) in res.proofs.items() if not ok]
    lines.append('Proofs: %s' % ('all passed' if not bad else 'FAILED: ' + ', '.join(bad)))
    return lines

