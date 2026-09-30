# Cuts the setup functions of the editor back out of an optimized main and names the placed objects.
import collections
import os
import re
import struct

import jass_ast as existing
import jass_normal
from jass_normal import bare


ORDER = ('sounds', 'regions', 'cameras', 'tech', 'destructables', 'items', 'units')
FUNCTIONS = {'sounds': 'InitSounds', 'regions': 'CreateRegions', 'cameras': 'CreateCameras',
             'destructables': 'CreateAllDestructables', 'items': 'CreateAllItems', 'units': 'CreateAllUnits'}
BOUNDARY = ('ConfigureNeutralVictim', 'InitBlizzard')
RX_SOUND_CALL = re.compile(r'^SetSound(?!Position$)\w+$')
REGION_CALLS = frozenset(('EnableWeatherEffect', 'SetSoundPosition', 'RegisterStackedSound'))
RX_CAMERA_CALL = re.compile(r'^(?:Blz)?CameraSetup\w+$')
TECH_CALLS = frozenset(('SetPlayerTechResearched', 'SetPlayerTechMaxAllowed', 'SetPlayerAbilityAvailable'))
RX_DESTRUCTABLE = re.compile(r'^(?:Blz)?Create(?:Dead)?Destructable(?:Z)?(?:WithSkin)?$')
ITEM_CREATE = frozenset(('CreateItem', 'BlzCreateItemWithSkin'))
UNIT_CREATE = frozenset(('CreateUnit', 'BlzCreateUnitWithSkin', 'CreateBlightedGoldmine'))
DROP_CALLS = frozenset(('TriggerRegisterDeathEvent', 'TriggerRegisterUnitEvent', 'TriggerAddAction'))
RX_UNIT_CALL = re.compile(
    r'^(?:SetUnit\w+|SetHero\w+|SelectHeroSkill|IssueImmediateOrder(?:ById)?|UnitAddItem\w*|SetResourceAmount'
    r'|WaygateSetDestination|WaygateActivate|RandomDist\w+|SetItem\w+|UnitAddAbility|UnitRemoveAbility)$')
UNIT_VALUES = frozenset(('Player', 'ChooseRandomCreep', 'ChooseRandomNPBuilding', 'GetUnitState', 'RandomDistChoose',
                         'CreateTrigger', 'GetUnitTypeId'))
RX_IDENT_NOISE = re.compile(r'[^A-Za-z0-9_]')
EDITOR_NAMES = re.compile(r'^(?:InitTrig_\w+|InitCustomTriggers|InitGlobals|RunInitializationTriggers)$')


def _value_call(s):
    if type(s) is not existing.SetStmt:
        return None
    v = bare(s.value)
    return v if type(v) is existing.Call else None


def _target(s):
    if type(s) is not existing.SetStmt:
        return None
    t = bare(s.target)
    while type(t) is existing.Index:
        t = bare(t.base)
    return t.name if type(t) is existing.Name else None


class _Script(object):
    def __init__(self, text):
        self.text = text
        self.tree = existing.parse(text)
        self.functions = collections.OrderedDict((f.name, f) for f in self.tree.functions)
        self.globals = dict((g.name, g) for g in self.tree.globals)
        self.lines = text.split('\n')
        self.assigned = collections.Counter()
        for f in self.tree.functions:
            for x in existing.walk(f):
                if type(x) is existing.SetStmt:
                    name = _target(x)
                    if name is not None:
                        self.assigned[name] += 1
        self._creates = {}

    def creates(self, name, seen=None):
        if name in self._creates:
            return self._creates[name]
        seen = seen if seen is not None else set()
        out = set()
        f = self.functions.get(name)
        if f is None or name in seen:
            return out
        seen.add(name)
        for x in existing.walk(f):
            if type(x) is not existing.Call:
                continue
            if x.name == 'CreateSound':
                out.add('sounds')
            elif x.name == 'Rect':
                out.add('regions')
            elif x.name == 'CreateCameraSetup':
                out.add('cameras')
            elif RX_DESTRUCTABLE.match(x.name):
                out.add('destructables')
            elif x.name in ITEM_CREATE:
                out.add('items')
            elif x.name in UNIT_CREATE:
                out.add('units')
            elif x.name == 'CreateTrigger' and not any(
                    type(y) is existing.Call and y.name in ('TriggerRegisterDeathEvent', 'TriggerRegisterUnitEvent')
                    for y in existing.walk(f)):
                out.add('other')
            elif not x.args and x.name in self.functions:
                out |= self.creates(x.name, seen)
        self._creates[name] = out
        return out


def _fits(script, kind, s, locals_):
    t = type(s)
    call = s.call if t is existing.CallStmt else _value_call(s)
    name = call.name if call is not None else None
    if kind == 'sounds':
        if t is existing.SetStmt:
            v = bare(s.value)
            return name == 'CreateSound' or (type(v) is existing.Literal and v.kind == 'string' and
                                            getattr(script.globals.get(_target(s)), 'type', None) == 'string')
        return t is existing.CallStmt and bool(RX_SOUND_CALL.match(name))
    if kind == 'regions':
        if t is existing.SetStmt:
            return name in ('Rect', 'AddWeatherEffect')
        return t is existing.CallStmt and name in REGION_CALLS
    if kind == 'cameras':
        return (t is existing.SetStmt and name == 'CreateCameraSetup') or (t is existing.CallStmt and
                                                                   bool(RX_CAMERA_CALL.match(name)))
    if kind == 'tech':
        return t is existing.CallStmt and name in TECH_CALLS
    if kind == 'destructables':
        if t is existing.SetStmt:
            return name is not None and (bool(RX_DESTRUCTABLE.match(name)) or name == 'GetDestructableLife' or
                                         (name == 'CreateTrigger' and _target(s) in locals_))
        return t is existing.CallStmt and (name == 'SetDestructableLife' or name in DROP_CALLS)
    if kind == 'items':
        return name in ITEM_CREATE
    if kind == 'units':
        if t is existing.SetStmt:
            if name in UNIT_CREATE:
                return True
            return _target(s) in locals_ and (name in UNIT_VALUES or number_or_name(s.value))
        if t is existing.CallStmt:
            if not call.args and name in script.functions:
                return script.creates(name) == {'units'}
            return bool(RX_UNIT_CALL.match(name)) or name in DROP_CALLS
        if t is existing.IfStmt:
            return all(_fits(script, 'units', x, locals_) for _c, body in s.branches for x in body
                       if type(x) is not existing.CommentStmt)
    return False


def number_or_name(e):
    e = bare(e)
    return jass_normal.number(e) is not None or type(e) is existing.Name


def _mentions(node, names):
    return set(x.name for x in existing.walk(node) if type(x) is existing.Name and x.name in names)


def _read_first(stmts, names, assigned=None):
    assigned = assigned if assigned is not None else set()
    out = set()
    for s in stmts:
        t = type(s)
        if t is existing.CommentStmt:
            continue
        if t is existing.SetStmt:
            target = bare(s.target)
            out |= _mentions(s.value, names) - assigned
            if type(target) is existing.Name:
                if target.name in names:
                    assigned.add(target.name)
            else:
                out |= _mentions(target, names) - assigned
        elif t is existing.IfStmt:
            after = None
            for cond, body in s.branches:
                if cond is not None:
                    out |= _mentions(cond, names) - assigned
                inner = set(assigned)
                out |= _read_first(body, names, inner)
                after = inner if after is None else after & inner
            if s.branches and s.branches[-1][0] is None and after is not None:
                assigned |= after
        elif t is existing.LoopStmt:
            out |= _read_first(s.body, names, set(assigned))
        else:
            out |= _mentions(s, names) - assigned
    return out


def _runs(script, main):
    body = [s for s in main.body if type(s) is not existing.CommentStmt]
    boundary = next((k for k, s in enumerate(body) if type(s) is existing.CallStmt and s.call.name in BOUNDARY), None)
    if boundary is None:
        return {}, body, None
    locals_ = set(d.name for d in main.locals)
    found, at = collections.OrderedDict(), 0
    broken = set()
    for k in range(boundary):
        kind = next((ORDER[j] for j in range(at, len(ORDER)) if _fits(script, ORDER[j], body[k], locals_)), None)
        if kind is None:
            continue
        at = ORDER.index(kind)
        if kind in found:
            if found[kind][1] != k:
                broken.add(kind)
            found[kind] = (found[kind][0], k + 1)
        else:
            found[kind] = (k, k + 1)
    for kind in broken:
        del found[kind]
    return found, body, boundary


def _role_calls(script, body, boundary):
    out = collections.OrderedDict()
    for s in body[:boundary]:
        if type(s) is not existing.CallStmt or s.call.args or s.call.name not in script.functions:
            continue
        kinds = script.creates(s.call.name)
        if len(kinds) == 1:
            out.setdefault(next(iter(kinds)), []).append(s.call.name)
    return dict((k, v[0]) for k, v in out.items() if len(v) == 1 and k in FUNCTIONS)


def _identifier(text):
    return RX_IDENT_NOISE.sub('_', text).strip('_') or 'x'


def _rawcode(e):
    value = jass_normal.number(e)
    text = jass_normal.integer_text(value[1]) if value is not None and value[0] == 'integer' else ''
    return text[1:-1] if len(text) == 6 and text[0] == "'" else None


def destructable_numbers(doo):
    out = {}
    if not doo:
        return out
    try:
        import doodads
        data = doodads.read_data(doo)
    except Exception:
        return out
    if not data.get('on_close'):
        return out
    for r in data['regs']:
        if r.get('editor_id') is None:
            continue
        x, y = struct.unpack_from('<2f', doo, r['begin'] + 8)
        key = (r['id'].decode('latin-1'), int(round(x)), int(round(y)))
        out[key] = None if key in out else r['editor_id']
    return out


def _object_names(script, statements, doo_numbers):
    taken = set(script.globals) | set(script.functions)
    out = {}

    def give(old, new):
        if old in out or old.startswith(('gg_', 'udg_', 'bj_')) or script.assigned[old] != 1 or \
                old not in script.globals or script.globals[old].is_array:
            return False
        if new in taken:
            return False
        taken.add(new)
        out[old] = new
        return True

    count = collections.Counter()
    for s in statements.get('sounds', ()):
        call = _value_call(s)
        v = bare(s.value) if type(s) is existing.SetStmt else None
        path = None
        if (
            call is not None
            and call.name == 'CreateSound'
            and call.args
            and type(bare(call.args[0])) is existing.Literal
        ):
            path = bare(call.args[0]).value
        elif type(v) is existing.Literal and v.kind == 'string':
            path = v.value
        if path:
            stem = _identifier(os.path.splitext(re.split(r'[\\/]', str(path))[-1])[0])
            name, k = 'gg_snd_' + stem, 1
            while name in taken:
                k += 1
                name = 'gg_snd_%s%d' % (stem, k)
            give(_target(s), name)
    for s in statements.get('regions', ()):
        call = _value_call(s)
        if call is not None and call.name == 'Rect':
            count['regions'] += 1
            give(_target(s), 'gg_rct_Region_%03d' % count['regions'])
    for s in statements.get('cameras', ()):
        call = _value_call(s)
        if call is not None and call.name == 'CreateCameraSetup':
            count['cameras'] += 1
            give(_target(s), 'gg_cam_Camera_%03d' % count['cameras'])
    for s in statements.get('destructables', ()):
        call = _value_call(s)
        if call is None or not RX_DESTRUCTABLE.match(call.name) or len(call.args) < 3:
            continue
        code, x, y = _rawcode(call.args[0]), jass_normal.number(call.args[1]), jass_normal.number(call.args[2])
        if code is None or x is None or y is None:
            continue
        number = doo_numbers.get((code, int(round(x[1])), int(round(y[1]))))
        if number is not None:
            give(_target(s), 'gg_dest_%s_%04d' % (code, number))
    number = 0
    for kind, prefix, at in (('units', 'gg_unit_', 1), ('items', 'gg_item_', 0)):
        for s in statements.get(kind, ()):
            call = _value_call(s)
            if call is None or call.name not in (UNIT_CREATE if kind == 'units' else ITEM_CREATE) or \
                    len(call.args) <= at:
                continue
            code = _rawcode(call.args[at]) if call.name != 'CreateBlightedGoldmine' else 'ugol'
            if code is not None and give(_target(s), '%s%s_%04d' % (prefix, code, number)):
                number += 1
    return out


def _all_statements(f):
    return [x for x in existing.walk(f) if isinstance(x, existing.Stmt) and type(x) is not existing.CommentStmt]


def _renamed(text, names):
    if not names:
        return text
    own = {}
    for f in existing.parse(text).functions:
        mine = (set(p for _t, p in f.params) | set(d.name for d in f.locals)) & set(names)
        if mine:
            for k in range(f.line, f.end_line + 1):
                own[k] = mine
    parts, last, line = [], 0, 1
    for m in existing._TOKEN_RE.finditer(text):
        tok = m.group(1)
        if tok in names and tok not in own.get(line, ()):
            parts.append(text[last:m.start(1)])
            parts.append(names[tok])
            last = m.end(1)
        line += existing._line_breaks(tok)
    parts.append(text[last:])
    return ''.join(parts)


def obfuscated(script):
    own = [n for n in script.globals if not n.startswith(('gg_', 'udg_', 'bj_'))]
    if len(own) >= 10 and sum(1 for n in own if len(n) <= 4) >= 0.6 * len(own):
        return True
    return not any(n.startswith(('gg_', 'udg_')) for n in script.globals) and not any(
        EDITOR_NAMES.match(n) for n in script.functions)


def setup(text, doo=None):
    report = {'functions': {}, 'objects': {}, 'skipped': {}}
    try:
        script = _Script(text)
    except existing.JassSyntaxError:
        return text, report
    main = script.functions.get('main')
    if main is None or main.params:
        return text, report
    runs, body, boundary = _runs(script, main)
    if boundary is None:
        return text, report
    roles = _role_calls(script, body, boundary)
    locals_ = collections.OrderedDict((d.name, d) for d in main.locals)
    names = set(locals_)
    taken = set(script.functions) | set(script.globals)
    statements = {}
    cuts = []
    for kind, (first, end) in runs.items():
        if kind not in FUNCTIONS:
            continue
        run = body[first:end]
        statements[kind] = [
            x for s in run for x in ([s] if type(s) is not existing.IfStmt else [s] + _all_statements_of(s))
        ]
        name = FUNCTIONS[kind]
        if kind == 'units' and all(type(s) is existing.CallStmt and not s.call.args and s.call.name in script.functions
                                   for s in run) and len(run) == 1:
            continue
        if name in taken:
            report['skipped'][kind] = 'the script already has %s' % name
            continue
        used = set().union(*[_mentions(s, names) for s in run]) if run else set()
        inflow = _read_first(run, names)
        outflow = _read_first(body[end:], names) & used
        bad = [x for x in used if locals_[x].is_array]
        if inflow or outflow or bad:
            report['skipped'][kind] = 'the local %s of main carries a value across' % sorted(inflow | outflow |
                                                                                           set(bad))[0]
            continue
        cuts.append((kind, name, first, end, [x for x in locals_ if x in used]))
        taken.add(name)
    for kind, function in roles.items():
        statements.setdefault(kind, []).extend(_all_statements(script.functions[function]))
    for s in statements.get('units', [])[:]:
        if type(s) is existing.CallStmt and not s.call.args and s.call.name in script.functions:
            seen, queue = set(), [s.call.name]
            while queue:
                f = queue.pop(0)
                if f in seen or f not in script.functions:
                    continue
                seen.add(f)
                for x in _all_statements(script.functions[f]):
                    statements['units'].append(x)
                    if type(x) is existing.CallStmt and not x.call.args:
                        queue.append(x.call.name)
    renames = {}
    for kind, function in roles.items():
        name = FUNCTIONS[kind]
        if function != name and name not in taken and kind not in dict((c[0], 1) for c in cuts):
            renames[function] = name
            taken.add(name)
            report['functions'][name] = function
    if obfuscated(script):
        objects = _object_names(script, statements, destructable_numbers(doo))
        for old, new in objects.items():
            kind = new.split('_')[1]
            report['objects'][kind] = report['objects'].get(kind, 0) + 1
        renames.update(objects)
    out = text
    if cuts:
        out = _cut(script, main, body, cuts)
        for kind, name, first, end, _used in cuts:
            report['functions'][name] = end - first
    if renames:
        out = _renamed(out, renames)
    return out, report


def _all_statements_of(s):
    return [
        x
        for x in existing.walk(s)
        if isinstance(x, existing.Stmt) and type(x) is not existing.CommentStmt and x is not s
    ]


def _cut(script, main, body, cuts):
    lines = list(script.lines)
    all_body = list(main.body)
    types = dict((d.name, d.type) for d in main.locals)

    def first_line(k):
        if k >= len(body):
            return main.end_line
        i = all_body.index(body[k])
        line = body[k].line
        while i > 0 and type(all_body[i - 1]) is existing.CommentStmt:
            i -= 1
            line = all_body[i].line
        return line

    functions, edits = [], []
    for _kind, name, first, end, used in cuts:
        a, b = first_line(first) - 1, first_line(end) - 1
        indent = re.match(r'[ \t]*', lines[a]).group(0)
        functions.append('\n'.join(['function %s takes nothing returns nothing' % name] +
                                   ['%slocal %s %s' % (indent, types[x], x) for x in used] + lines[a:b] +
                                   ['endfunction']))
        edits.append((a, b, '%scall %s()' % (indent, name)))
    for a, b, call in sorted(edits, reverse=True):
        lines[a:b] = [call]
    at = main.line - 1
    return '\n'.join(lines[:at] + functions + lines[at:])

