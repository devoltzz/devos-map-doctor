# Finds the pause, the taken control or the cinematic mode a script turns on and never undoes.

from doctor.script import jass_ast


SEVERITY = {'pause_game': 'warning', 'user_control': 'warning', 'cinematic_mode': 'warning',
            'pause_all_units': 'warning', 'pause_unit': 'info', 'unit_time_scale': 'info'}
RULES = tuple(SEVERITY)
LIST_MAX = 40

T, F, Z, NZ, X = 'true', 'false', 'zero', 'nonzero', 'x'
LOCKS = {
    'pause_game': [('PauseGame', 0, (T,)), ('PauseGameOn', None, ())],
    'user_control': [('EnableUserControl', 0, (F,)), ('SetUserControlForceOff', None, ())],
    'cinematic_mode': [('CinematicModeBJ', 0, (T,)), ('CinematicModeExBJ', 0, (T,))],
    'pause_all_units': [('PauseAllUnitsBJ', 0, (T,))],
    'pause_unit': [('PauseUnit', 1, (T,)), ('PauseUnitBJ', 0, (T,))],
    'unit_time_scale': [('SetUnitTimeScale', 1, (Z,)), ('SetUnitTimeScalePercent', 1, (Z,))],
}
RESTORES = {
    'pause_game': [('PauseGame', 0, (F, X)), ('PauseGameOff', None, ())],
    'user_control': [('EnableUserControl', 0, (T, X)), ('SetUserControlForceOn', None, ()),
                     ('CinematicModeBJ', 0, (F, X)), ('CinematicModeExBJ', 0, (F, X))],
    'cinematic_mode': [('CinematicModeBJ', 0, (F, X)), ('CinematicModeExBJ', 0, (F, X)), ('ShowInterface', 0, (T, X)),
                       ('ShowInterfaceForceOn', None, ()), ('EnableUserControl', 0, (T, X)),
                       ('SetUserControlForceOn', None, ())],
    'pause_all_units': [('PauseAllUnitsBJ', 0, (F, X))],
    'pause_unit': [('PauseUnit', 1, (F, X)), ('PauseUnitBJ', 0, (F, X)), ('PauseAllUnitsBJ', 0, (F, X))],
    'unit_time_scale': [('SetUnitTimeScale', 1, (NZ, X)), ('SetUnitTimeScalePercent', 1, (NZ, X))],
}
END_GAME = frozenset(('EndGame', 'CustomVictoryBJ', 'CustomDefeatBJ', 'CustomVictoryDialogBJ', 'CustomDefeatDialogBJ',
                      'CustomVictorySkipBJ', 'MeleeVictoryDialogBJ', 'MeleeDefeatDialogBJ', 'RemovePlayer',
                      'EndGameBJ', 'RestartGame', 'FinishSaveGame_never'))
WATCHED = frozenset(c for table in (LOCKS, RESTORES) for specs in table.values() for c, _i, _v in specs) | END_GAME
LOCK_TEXT = {'pause_game': 'pauses the game', 'user_control': 'takes the control away from the players',
             'cinematic_mode': 'turns the cinematic mode on', 'pause_all_units': 'pauses every unit',
             'pause_unit': 'pauses a unit', 'unit_time_scale': 'sets a unit\'s time scale to 0'}
RESTORE_TEXT = {'pause_game': 'PauseGame(false)', 'user_control': 'EnableUserControl(true)',
                'cinematic_mode': 'CinematicModeBJ(false, ...)', 'pause_all_units': 'PauseAllUnitsBJ(false)',
                'pause_unit': 'PauseUnit(u, false)', 'unit_time_scale': 'SetUnitTimeScale(u, <non-zero>)'}


def _nothing(*_a, **_k):
    pass


def _number(text):
    try:
        t = text.strip().lower()
        if t.startswith('$'):
            return int(t[1:], 16)
        if t.startswith('0x'):
            return int(t, 16)
        if t.startswith("'"):
            return None
        return float(t)
    except ValueError:
        return None


def _jass_value(e):
    while type(e) is jass_ast.Paren:
        e = e.inner
    if type(e) is jass_ast.Name and e.name in ('true', 'false'):
        return T if e.name == 'true' else F
    if type(e) is jass_ast.Literal:
        if e.text in ('true', 'false'):
            return T if e.text == 'true' else F
        if e.kind in ('integer', 'real'):
            v = _number(e.text)
            if v is not None:
                return Z if v == 0 else NZ
    if type(e) is jass_ast.Unary and e.op == '-':
        v = _jass_value(e.operand)
        if v in (Z, NZ):
            return v
    return X


def _lua_value(e):
    from doctor.script import lua_ast
    while isinstance(e, lua_ast.Paren):
        e = e.inner
    if isinstance(e, lua_ast.Literal):
        if e.kind == 'boolean':
            return T if e.value else F
        if e.kind == 'number' and isinstance(e.value, (int, float)):
            return Z if e.value == 0 else NZ
    if isinstance(e, lua_ast.Unary) and e.op == '-':
        v = _lua_value(e.operand)
        if v in (Z, NZ):
            return v
    return X


def _classify(name, values):
    def match(specs):
        out = []
        for rule, spec in specs.items():
            for callee, idx, accepted in spec:
                if callee != name:
                    continue
                if idx is None or (idx < len(values) and values[idx] in accepted):
                    out.append(rule)
                    break
        return out
    return match(LOCKS), match(RESTORES)


def _findings(calls, reachable, everything):
    locks, restores = [], {}
    ends = sorted(set(name for fn, _l, name, _v in calls if name in END_GAME and reachable(fn)))
    for fn, line, name, values in calls:
        lk, rs = _classify(name, values)
        for rule in rs:
            restores.setdefault(rule, []).append((fn, reachable(fn)))
        if lk and reachable(fn):
            for rule in lk:
                locks.append((rule, fn, line, name))
    out = []
    for rule, fn, line, name in locks:
        seen = restores.get(rule, [])
        if everything and seen or any(r for _f, r in seen):
            continue
        detail = '%s %s (%s) and %s calls %s: nothing restores it' % (
            fn or 'the script', LOCK_TEXT[rule], name,
            'nothing in the script' if everything else 'no reachable function of the script', RESTORE_TEXT[rule])
        dead = sorted(set(f for f, _r in seen))
        if dead:
            detail += '; the only restore is in %s, which nothing reaches' % ', '.join(dead[:4])
        severity = SEVERITY[rule]
        if ends and severity == 'warning':
            severity = 'info'
            detail += ' (the script also ends the game with %s: a freeze before the end screen is the usual shape)' % (
                ', '.join(ends[:3]))
        out.append({'rule': rule, 'function': fn, 'line': line, 'severity': severity, 'detail': detail})
    out.sort(key=lambda x: (RULES.index(x['rule']), x['line'] or 0))
    return out


def _result(findings, script, error=None):
    counts = dict((r, 0) for r in RULES)
    for x in findings:
        counts[x['rule']] += 1
    r = {'findings': findings[:LIST_MAX * len(RULES)], 'counts': counts, 'script': script}
    if error:
        r['error'] = error
    return r


def _scan_jass(text):
    try:
        tree = jass_ast.parse(text, vjass=True)
    except jass_ast.JassSyntaxError as e:
        return _result([], 'jass', 'The script does not parse (%s).' % e)
    return scan_jass_tree(tree)


def scan_jass_tree(tree):
    from doctor.fix import script_lint
    unused, dynamic = script_lint._unreachable(tree, dict((f.name, f) for f in tree.functions))
    unused = set(unused)
    calls = []
    for f in tree.functions:
        for n in jass_ast.walk(f):
            if type(n) is not jass_ast.Call:
                continue
            if n.name in WATCHED:
                calls.append((f.name, n.line, n.name, [_jass_value(a) for a in n.args]))
    if dynamic:
        def reachable(fn):
            return True
    else:
        def reachable(fn):
            return fn not in unused
    return _result(_findings(calls, reachable, dynamic), 'jass')


def _lua_calls(tree):
    from doctor.script import lua_ast
    from doctor.script import lua_desync
    out = []
    stack = [(tree.body, None)]
    while stack:
        node, fn = stack.pop()
        if isinstance(node, (list, tuple)):
            stack.extend((x, fn) for x in reversed(node))
            continue
        if isinstance(node, (str, int, float, bool)) or node is None or not hasattr(type(node), '__slots__'):
            continue
        if isinstance(node, lua_ast.FunctionStmt):
            nm = node.name if isinstance(node.name, str) else getattr(node.name, 'name', None)
            fn = nm or fn
        if isinstance(node, lua_ast.Call):
            name = lua_desync._call_name(node)
            if name in WATCHED:
                out.append((fn, node.line, name, [_lua_value(a) for a in (node.args or ())]))
        for cls in type(node).__mro__:
            for slot in getattr(cls, '__slots__', ()):
                if slot in ('line', 'comment', 'leading_comments', 'inner_comments', 'span', 'text'):
                    continue
                v = getattr(node, slot, None)
                if isinstance(v, (list, tuple)) or hasattr(type(v), '__slots__') and not isinstance(v, str):
                    stack.append((v, fn))
    return out


def _scan_lua(text):
    from doctor.script import lua_ast
    try:
        tree = lua_ast.parse(text)
    except lua_ast.LuaSyntaxError as e:
        return _result([], 'lua', 'The script does not parse (%s).' % e)
    return scan_lua_tree(tree)


def scan_lua_tree(tree):
    return _result(_findings(_lua_calls(tree), lambda fn: True, True), 'lua')


RULE_PHRASE = {'pause_game': 'pauses the game', 'user_control': 'takes the control away from the players',
               'cinematic_mode': 'turns the cinematic mode on', 'pause_all_units': 'pauses every unit',
               'pause_unit': 'pauses a unit', 'unit_time_scale': 'freezes the animation of a unit'}


def reforged_items(result, item, limit=5):
    xs = (result or {}).get('findings') or []
    out = []
    for severity, code in (('warning', 'script_lock'), ('info', 'script_lock_info')):
        ys = [x for x in xs if x['severity'] == severity]
        if not ys:
            continue
        what = ', '.join(sorted(set(RULE_PHRASE.get(x['rule'], x['rule']) for x in ys)))
        where = ', '.join('%s (line %d)' % (x['function'], x['line']) for x in ys[:limit])
        if severity == 'warning':
            text = ('The script %s and no function the map can reach ever undoes it, so the game may stay locked: %s%s.'
                    % (what, where, ', ...' if len(ys) > limit else ''))
        else:
            text = ('The script %s for good (%s%s); this is usually on purpose (a statue, a freeze before the end '
                    'screen).' % (what, where, ', ...' if len(ys) > limit else ''))
        out.append(item(code, severity, text, 'none', count=len(ys),
                        sites=[dict((k, x[k]) for k in ('rule', 'function', 'line')) for x in ys[:limit]]))
    return out


def scan_text(text, language='jass'):
    if language == 'lua':
        return _scan_lua(text)
    return _scan_jass(text)


def scan(path, progress=None):
    progress = progress or _nothing
    if path.lower().endswith(('.j', '.ai', '.lua')):
        text = jass_ast.read_script(path)
        return scan_text(text, 'lua' if path.lower().endswith('.lua') else 'jass')
    from doctor.fix import single_player
    progress('Reading the map script')
    try:
        _a, sc, _strings = single_player.read_map(path)
    except BaseException as e:
        if isinstance(e, KeyboardInterrupt):
            raise
        return _result([], None, 'The map cannot be read (%s).' % e)
    if sc['language'] is None or sc['bytes'] is None:
        return _result([], sc['language'], 'The map has no script to check.')
    if sc.get('compiled'):
        return _result([], sc['language'],
                       'The script is compiled (the KK platform bytecode), so it cannot be checked.')
    progress('Checking the script for locks')
    return scan_text(sc['bytes'].decode('utf-8', 'surrogateescape'), sc['language'])
