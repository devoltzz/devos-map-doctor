# Finds the handle leaks of a JASS script, weighed by how often they run, and its unset globals.

from doctor.script import jass_ast


HEATS = ('hot', 'repeat', 'once', 'unused')
CREATORS = {}
for _n in ('Location', 'GetUnitLoc', 'GetSpellTargetLoc', 'GetOrderPointLoc', 'GetRectCenter', 'GetRandomLocInRect',
           'PolarProjectionBJ', 'OffsetLocation', 'GetUnitRallyPoint', 'GetPlayerStartLocationLoc',
           'GetCameraTargetPositionLoc', 'GetCameraEyePositionLoc', 'CameraSetupGetDestPositionLoc',
           'GetDestructableLoc', 'GetItemLoc', 'GetLocationOf', 'MoveLocation_never'):
    CREATORS[_n] = ('location', 'RemoveLocation')
for _n in ('CreateGroup', 'GetUnitsInRangeOfLocAll', 'GetUnitsInRangeOfLocMatching', 'GetUnitsInRectAll',
           'GetUnitsInRectMatching', 'GetUnitsInRectOfPlayer', 'GetUnitsOfPlayerAll', 'GetUnitsOfPlayerMatching',
           'GetUnitsOfPlayerAndTypeId', 'GetUnitsOfTypeIdAll', 'GetUnitsSelectedAll', 'GetRandomSubGroup'):
    CREATORS[_n] = ('group', 'DestroyGroup')
for _n in ('CreateForce', 'GetPlayersAllies', 'GetPlayersEnemies', 'GetPlayersMatching', 'GetPlayersByMapControl',
           'GetForceOfPlayer'):
    CREATORS[_n] = ('force', 'DestroyForce')
for _n in ('AddSpecialEffect', 'AddSpecialEffectLoc', 'AddSpecialEffectTarget', 'AddSpellEffect',
           'AddSpellEffectLoc', 'AddSpellEffectById', 'AddSpellEffectByIdLoc', 'AddSpellEffectTarget',
           'AddSpellEffectTargetById'):
    CREATORS[_n] = ('effect', 'DestroyEffect')
CREATORS.pop('MoveLocation_never', None)
DESTROYERS = frozenset(d for _k, d in CREATORS.values())
INLINE_KINDS = ('location', 'group', 'force')
SYNC_CALLBACKS = frozenset(('ForGroup', 'ForGroupBJ', 'ForForce', 'EnumDestructablesInRect', 'EnumItemsInRect',
                            'GroupEnumUnitsInRange', 'GroupEnumUnitsInRangeOfLoc', 'GroupEnumUnitsInRect',
                            'GroupEnumUnitsOfPlayer', 'GroupEnumUnitsOfType', 'GroupEnumUnitsSelected',
                            'GroupEnumUnitsInRangeCounted', 'GroupEnumUnitsInRectCounted', 'ForceEnumPlayers',
                            'ForceEnumAllies', 'ForceEnumEnemies', 'EnumDestructablesInRectAll',
                            'EnumItemsInRectBJ', 'Filter', 'Condition', 'GetUnitsInRangeOfLocMatching',
                            'GetUnitsInRectMatching', 'GetUnitsOfPlayerMatching', 'GetPlayersMatching',
                            'ForGroupBJ'))
START = (('InitGlobals', 'init_globals_not_called'), ('RunInitializationTriggers', 'init_triggers_not_called'))
LIST_MAX = 40


def _text(e):
    try:
        return jass_ast._ue(e)
    except Exception:
        return '?'


def _refs(e):
    return [n.name for n in jass_ast.walk(e) if type(n) is jass_ast.FuncRef]


def _calls(node):
    return [n for n in jass_ast.walk(node) if type(n) is jass_ast.Call]


def _is_true(e):
    return type(e) is jass_ast.Literal and e.text == 'true' or type(e) is jass_ast.Name and e.name == 'true'


def heat_of(tree):
    funcs = dict((f.name, f) for f in tree.functions)
    edges = dict((n, set()) for n in funcs)
    hot_roots, cb_roots = set(), set()
    trig_actions, periodic = {}, set()
    for f in tree.functions:
        for c in _calls(f):
            if c.name in funcs:
                edges[f.name].add(c.name)
            elif c.name == 'ExecuteFunc' and c.args and type(c.args[0]) is jass_ast.Literal and \
                    c.args[0].kind == 'string':
                target = c.args[0].value
                if target in funcs:
                    edges[f.name].add(target)
            if c.name in ('TriggerAddAction', 'TriggerAddCondition') and len(c.args) == 2:
                trig_actions.setdefault(_text(c.args[0]), set()).update(_refs(c.args[1]))
            elif c.name == 'TriggerRegisterTimerEvent' and len(c.args) == 3 and _is_true(c.args[2]):
                periodic.add(_text(c.args[0]))
            elif c.name == 'TriggerRegisterTimerEventPeriodic' and c.args:
                periodic.add(_text(c.args[0]))
            elif c.name == 'TimerStart' and len(c.args) == 4 and _is_true(c.args[2]):
                hot_roots.update(_refs(c.args[3]))
            if c.name in SYNC_CALLBACKS:
                for a in c.args:
                    edges[f.name].update(r for r in _refs(a) if r in funcs)
            else:
                for a in c.args:
                    if type(a) is jass_ast.FuncRef or type(a) is jass_ast.Call and a.name in ('Condition', 'Filter'):
                        cb_roots.update(r for r in _refs(a) if r in funcs)
        for st in jass_ast.walk(f):
            if type(st) is jass_ast.SetStmt:
                cb_roots.update(r for r in _refs(st.value) if r in funcs)
    for trig in periodic:
        hot_roots.update(trig_actions.get(trig, ()))
    for acts in trig_actions.values():
        cb_roots.update(acts)

    def reach(roots):
        seen, stack = set(), [r for r in roots if r in funcs]
        while stack:
            n = stack.pop()
            if n in seen:
                continue
            seen.add(n)
            stack.extend(edges.get(n, ()))
        return seen

    hot = reach(hot_roots)
    rep = reach(cb_roots)
    once = reach([n for n in ('main', 'config') if n in funcs])
    return dict((n, 'hot' if n in hot else 'repeat' if n in rep else 'once' if n in once else 'unused')
                for n in funcs)


def _leaks(f, map_funcs, globals_):
    out = []
    want_destroy = any(type(s) is jass_ast.SetStmt and _text(s.target) == 'bj_wantDestroyGroup' and _is_true(s.value)
                       for s in jass_ast.walk(f))
    locals_ = dict((l.name, l) for l in f.locals)
    created = {}
    escaped = set()
    for st in jass_ast.walk(f):
        t = type(st)
        if t is jass_ast.CallStmt and st.call.name in CREATORS:
            out.append({'rule': 'discarded', 'creator': st.call.name, 'line': st.line})
        if t is jass_ast.LocalDecl and st.initializer is not None and type(st.initializer) is jass_ast.Call and \
                st.initializer.name in CREATORS:
            created[st.name] = (st.initializer.name, st.line)
        if t is jass_ast.SetStmt:
            tgt = _text(st.target)
            if type(st.value) is jass_ast.Call and st.value.name in CREATORS and tgt in locals_:
                created.setdefault(tgt, (st.value.name, st.line))
            if type(st.value) is jass_ast.Name and st.value.name in locals_ and tgt not in locals_:
                escaped.add(st.value.name)
        if t is jass_ast.ReturnStmt and st.value is not None:
            escaped.update(n.name for n in jass_ast.walk(st.value) if type(n) is jass_ast.Name)
        if t is jass_ast.Call:
            for a in st.args:
                if type(a) is jass_ast.Call and a.name in CREATORS:
                    kind, destroyer = CREATORS[a.name]
                    if kind in INLINE_KINDS and st.name != destroyer and st.name not in CREATORS and \
                            not (kind == 'group' and want_destroy):
                        out.append({'rule': 'inline', 'creator': a.name, 'line': a.line or st.line, 'into': st.name})
            names = [a.name for a in st.args if type(a) is jass_ast.Name and a.name in locals_]
            if st.name in DESTROYERS or st.name in map_funcs or st.name.startswith('Save') or \
                    st.name in ('ExecuteFunc',):
                escaped.update(names)
    for name, (creator, line) in created.items():
        if name not in escaped:
            out.append({'rule': 'never_destroyed', 'creator': creator, 'line': line, 'local': name})
    return out


def check_text(text):
    try:
        tree = jass_ast.parse(text)
    except jass_ast.JassSyntaxError as e:
        return {'language': 'jass', 'error': 'The script does not parse (%s).' % e}
    heat = heat_of(tree)
    map_funcs = set(heat)
    globals_ = dict((g.name, g) for g in tree.globals)
    leaks = []
    for f in tree.functions:
        for x in _leaks(f, map_funcs, globals_):
            x['function'] = f.name
            x['heat'] = heat[f.name]
            leaks.append(x)
    leaks.sort(key=lambda x: (HEATS.index(x['heat']), x['line']))
    called = set()
    for n in jass_ast.walk(tree):
        if type(n) is jass_ast.Call:
            called.add(n.name)
            if n.name == 'ExecuteFunc' and n.args and type(n.args[0]) is jass_ast.Literal:
                called.add(n.args[0].value)
        elif type(n) is jass_ast.FuncRef:
            called.add(n.name)
    start = [{'code': code, 'name': name} for name, code in START if name in map_funcs and name not in called]
    assigned, reads, targets = set(), {}, set()
    for f in tree.functions:
        for n in jass_ast.walk(f):
            if type(n) is jass_ast.SetStmt:
                tgt = n.target.base if type(n.target) is jass_ast.Index else n.target
                if type(tgt) is jass_ast.Name:
                    assigned.add(tgt.name)
                    targets.add(id(tgt))
        for n in jass_ast.walk(f):
            if type(n) is jass_ast.Name and n.name in globals_ and id(n) not in targets:
                reads[n.name] = reads.get(n.name, 0) + 1
    never = [{'name': g.name, 'type': g.type + (' array' if g.is_array else ''), 'reads': reads[g.name]}
             for g in tree.globals if not g.is_constant and g.initializer is None and g.name in reads and
             g.name not in assigned]
    never.sort(key=lambda x: (-x['reads'], x['name']))
    counts = {'leaks': len(leaks), 'never_assigned': len(never), 'start': len(start)}
    for h in HEATS:
        counts['leaks_' + h] = sum(1 for x in leaks if x['heat'] == h)
    out = {'language': 'jass', 'leaks': leaks[:LIST_MAX * 5], 'start': start, 'never_assigned': never[:LIST_MAX],
           'heat': dict((h, sum(1 for v in heat.values() if v == h)) for h in HEATS), 'counts': counts}
    out['lines'] = summary(out)
    return out


RULE_TEXT = {'discarded': 'created and thrown away', 'inline': 'created inside a call and never destroyed',
             'never_destroyed': 'kept in a local and never destroyed'}
HEAT_TEXT = {'hot': 'on a periodic timer', 'repeat': 'on an event', 'once': 'once, at the start', 'unused': 'never'}


def summary(r):
    if r.get('error'):
        return [r['error']]
    c = r['counts']
    out = []
    if c['leaks']:
        out.append('%d handle leaks: %d run on a periodic timer, %d on an event, %d once at the start, %d in code that '
                   'never runs.' % (c['leaks'], c['leaks_hot'], c['leaks_repeat'], c['leaks_once'], c['leaks_unused']))
        for x in [x for x in r['leaks'] if x['heat'] in ('hot', 'repeat')][:10]:
            out.append('  line %d, %s: %s %s (runs %s).' % (x['line'], x['function'], x['creator'],
                                                             RULE_TEXT[x['rule']], HEAT_TEXT[x['heat']]))
    else:
        out.append('No handle leak the text proves.')
    for s in r['start']:
        out.append('%s is defined and nothing calls it: %s.' % (s['name'], 'every variable reads as its default'
                                                                if s['code'] == 'init_globals_not_called' else
                                                                'the "Map Initialization" triggers never run'))
    if c['never_assigned']:
        out.append('%d globals are read and never set (always the default value): %s.' % (
            c['never_assigned'], ', '.join(x['name'] for x in r['never_assigned'][:8]) +
            (', ...' if c['never_assigned'] > 8 else '')))
    return out


def check(path):
    if path.lower().endswith(('.j', '.ai', '.lua')):
        text = jass_ast.read_script(path)
        lang = 'lua' if path.lower().endswith('.lua') else 'jass'
    else:
        from doctor.fix import single_player
        try:
            _a, sc, _strings = single_player.read_map(path)
        except BaseException as e:
            if isinstance(e, KeyboardInterrupt):
                raise
            return {'error': 'The map cannot be read (%s).' % e, 'lines': ['The map cannot be read.']}
        if sc['bytes'] is None:
            return {'error': 'The map has no script to check.', 'lines': ['The map has no script to check.']}
        lang = sc['language']
        text = sc['bytes'].decode('utf-8', 'surrogateescape')
    if lang != 'jass':
        return {'language': lang, 'lines': ['The script checks read JASS; this script is %s.' % lang]}
    return check_text(text)
