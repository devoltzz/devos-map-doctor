# Preloads, under the loading screen, the units and abilities a map uses in its first seconds.
import re

from doctor.fix import unprotect
from doctor.script import jass_ast


WINDOW = 5.0
CHUNK = 60
PREFIX = 'dmd_preload'
CARRIER = 'hpea'
NEUTRAL = 'Player(PLAYER_NEUTRAL_PASSIVE)'
RX_ID = re.compile(r'\A[\x21-\x7e]{4}\Z')


def _nothing(*_a, **_k):
    pass


def _num(e):
    if type(e) is jass_ast.Literal and e.kind in ('integer', 'real'):
        try:
            return float(e.value)
        except (TypeError, ValueError):
            return None
    return None


def _false(e):
    return type(e) is jass_ast.Literal and e.text == 'false' or type(e) is jass_ast.Name and e.name == 'false'


def entries(tree):
    from doctor.script import script_checks
    trig = {}
    out = []
    timers = []
    heat = script_checks.heat_of(tree)
    for f in tree.functions:
        start = heat.get(f.name) == 'once'
        for c in script_checks._calls(f):
            if c.name in ('TriggerAddAction', 'TriggerAddCondition') and len(c.args) == 2:
                trig.setdefault(script_checks._text(c.args[0]), set()).update(script_checks._refs(c.args[1]))
            elif c.name == 'TriggerRegisterTimerEvent' and len(c.args) == 3 and _false(c.args[2]):
                timers.append((script_checks._text(c.args[0]), _num(c.args[1])))
            elif c.name == 'TriggerRegisterTimerEventSingle' and len(c.args) == 2:
                timers.append((script_checks._text(c.args[0]), _num(c.args[1])))
            elif c.name == 'TimerStart' and len(c.args) == 4 and _false(c.args[2]) and start:
                s = _num(c.args[1])
                if s is not None and s <= WINDOW:
                    out += [(r, s) for r in script_checks._refs(c.args[3])]
    for t, s in timers:
        if s is not None and s <= WINDOW:
            out += [(r, s) for r in sorted(trig.get(t, ()))]
    funcs = set(f.name for f in tree.functions)
    seen, res = set(), []
    for r, s in out:
        if r in funcs and r not in seen:
            seen.add(r)
            res.append((r, s))
    return res


def _reached(tree, roots):
    from doctor.script import script_checks
    funcs = dict((f.name, f) for f in tree.functions)
    seen, stack = set(), list(roots)
    while stack:
        n = stack.pop()
        if n in seen or n not in funcs:
            continue
        seen.add(n)
        for c in script_checks._calls(funcs[n]):
            if c.name in funcs:
                stack.append(c.name)
            elif c.name == 'ExecuteFunc' and c.args and type(c.args[0]) is jass_ast.Literal and \
                    c.args[0].kind == 'string':
                stack.append(c.args[0].value)
            if c.name in script_checks.SYNC_CALLBACKS:
                for a in c.args:
                    stack.extend(script_checks._refs(a))
    return [funcs[n] for n in seen]


def _rawcodes(tree, funcs):
    holds = {}
    for g in tree.globals:
        if g.initializer is not None and type(g.initializer) is jass_ast.Literal and g.initializer.kind == 'rawcode':
            holds.setdefault(g.name, set()).add(g.initializer.value)
    for f in tree.functions:
        for st in jass_ast.walk(f):
            if type(st) is jass_ast.SetStmt and type(st.target) in (jass_ast.Name, jass_ast.Index) and \
                    type(st.value) is jass_ast.Literal and st.value.kind == 'rawcode':
                base = st.target.base if type(st.target) is jass_ast.Index else st.target
                holds.setdefault(base.name, set()).add(st.value.value)
    out = set()
    for f in funcs:
        for n in jass_ast.walk(f):
            if type(n) is jass_ast.Literal and n.kind == 'rawcode':
                out.add(n.value)
            elif type(n) is jass_ast.Name and n.name in holds:
                out.update(holds[n.name])
    return out


def _ids(value):
    if isinstance(value, int):
        try:
            return value.to_bytes(4, 'big').decode('latin-1')
        except OverflowError:
            return None
    return value


def map_objects(a):
    from doctor.data import objbin
    out = []
    for name, lv in (('war3map.w3u', False), ('war3map.w3a', True)):
        ids = set()
        b = unprotect._read(a, name)
        if b:
            try:
                _v, tabs, _p = objbin.read_data(b, lv)
                for objs in tabs:
                    for old, new, _m in objs:
                        ids.add(new if new.strip('\0') else old)
            except Exception:
                pass
        out.append(ids)
    return out[0], out[1]


def _scan(a, text):
    try:
        tree = jass_ast.parse(text)
    except jass_ast.JassSyntaxError as e:
        return None, {'entries': [], 'units': [], 'abilities': [], 'reason': 'The script does not parse (%s).' % e}
    ent = entries(tree)
    codes = set(filter(None, (_ids(v) for v in _rawcodes(tree, _reached(tree, [f for f, _s in ent])))))
    units, abils = map_objects(a)
    return tree, {'entries': [{'function': f, 'seconds': s} for f, s in ent],
                  'units': sorted(codes & units), 'abilities': sorted(codes & abils)}


def scan(path):
    from doctor.fix import single_player
    try:
        a, sc, _strings = single_player.read_map(path)
    except BaseException as e:
        if isinstance(e, KeyboardInterrupt):
            raise
        return {'entries': [], 'units': [], 'abilities': [], 'reason': 'The map cannot be read (%s).' % e}
    if sc['language'] != 'jass' or sc['compiled'] or sc['bytes'] is None:
        return {'entries': [], 'units': [], 'abilities': [], 'reason': 'Only a JASS script is read.'}
    return _scan(a, sc['bytes'].decode('utf-8', 'surrogateescape'))[1]


def script_parts(units, abilities):
    stmts = []
    for u in units:
        stmts.append("    call RemoveUnit(CreateUnit(%s, '%s', 0, 0, 0))" % (NEUTRAL, u))
    if abilities:
        stmts.append("    set %s_u = CreateUnit(%s, '%s', 0, 0, 0)" % (PREFIX, NEUTRAL, CARRIER))
        for x in abilities:
            stmts.append("    call UnitAddAbility(%s_u, '%s')" % (PREFIX, x))
            stmts.append("    call UnitRemoveAbility(%s_u, '%s')" % (PREFIX, x))
        stmts.append('    call RemoveUnit(%s_u)' % PREFIX)
        stmts.append('    set %s_u = null' % PREFIX)
    f = ['//===========================================================================',
         "// Devo's Map Doctor: the models and abilities the map uses in its first seconds, loaded under the",
         '// loading screen and removed again.',
         '//===========================================================================']
    chunks = [stmts[i:i + CHUNK] for i in range(0, len(stmts), CHUNK)]
    for k, body in enumerate(chunks):
        f.append('function %s_%d takes nothing returns nothing' % (PREFIX, k))
        f += body
        f.append('endfunction')
    f.append('function %s takes nothing returns nothing' % PREFIX)
    f += ['    call ExecuteFunc("%s_%d")' % (PREFIX, k) for k in range(len(chunks))]
    f.append('endfunction')
    return ['    unit %s_u = null' % PREFIX], '\n'.join(f) + '\n', ['    call %s()' % PREFIX]


def fix(path_in, path_out, progress=None):
    from doctor.fix import map_rewrite
    from doctor.fix import single_player
    p = progress or _nothing
    rep = {'state': 'failed', 'units': [], 'abilities': [], 'lines': []}

    def stop(state, why):
        rep['state'] = state
        rep['error' if state == 'failed' else 'reason'] = why
        return rep

    p('Reading the map')
    try:
        a, sc, _strings = single_player.read_map(path_in)
    except BaseException as e:
        if isinstance(e, KeyboardInterrupt):
            raise
        return stop('failed', 'The map cannot be read (%s).' % unprotect._error(e))
    if sc['language'] != 'jass' or sc['compiled'] or sc['bytes'] is None:
        return stop('refused', 'Only a JASS script can take the preload.')
    text = sc['bytes'].decode('utf-8', 'surrogateescape')
    if PREFIX + '_u' in text:
        return stop('nothing_to_do', 'The script already preloads.')
    tree, s = _scan(a, text)
    if tree is None:
        return stop('refused', s['reason'])
    rep['units'], rep['abilities'], rep['entries'] = s['units'], s['abilities'], s['entries']
    units = [x for x in s['units'] if RX_ID.match(x)]
    abilities = [x for x in s['abilities'] if RX_ID.match(x)]
    skipped = [x for x in s['units'] + s['abilities'] if not RX_ID.match(x)]
    if skipped:
        rep['skipped'] = {'ids': skipped, 'why': 'not 4 printable ASCII characters, so no rawcode can name them'}
    if not units and not abilities:
        return stop('nothing_to_do', 'Nothing the map defines is used in its first seconds.')
    try:
        g, f, top = script_parts(units, abilities)
        new_text = map_rewrite.insert(text, tree, g, f, top)
        jass_ast.parse(new_text)
    except (ValueError, jass_ast.JassSyntaxError) as e:
        return stop('refused', 'The script cannot take the code (%s).' % e)
    new_bytes = new_text.encode('utf-8', 'surrogateescape')
    p('Running pjass')
    rep['pjass'] = map_rewrite.gate(sc['bytes'], new_bytes)
    if rep['pjass']['state'] == 'failed':
        return stop('refused', 'pjass does not accept the changed script (%s).' % rep['pjass'].get('new'))
    try:
        done = map_rewrite.write(path_in, path_out, [(sc['file'], new_bytes)] +
                                 [(c, new_bytes) for c in sc['copies']], p)
    except Exception as e:
        return stop('failed', 'The map could not be written (%s).' % unprotect._error(e))
    rep.update(state='done', same_files=done['same_files'])
    rep['lines'] = ['%d unit types and %d abilities used in the first %g seconds are loaded under the loading '
                    'screen. Test the map before sharing it.' % (len(units), len(abilities), WINDOW)]
    if skipped:
        rep['lines'].append('%d id(s) stay out: not 4 printable ASCII characters, so no rawcode can name them.'
                            % len(skipped))
    return rep
