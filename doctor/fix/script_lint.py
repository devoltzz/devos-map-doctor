# Lint rules for JASS: loops, dead code, unused names, renamed natives, the old item type numbers.
import os
import re

from doctor.script import jass_ast


REF_30 = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ref', '3.0'))
LIST_MAX = 40
SEVERITY = {'loop_no_exit': 'warning', 'loop_static_exit': 'warning', 'dead_code': 'info', 'unused_local': 'info',
            'unused_function': 'info', 'recursion': 'info', 'local_shadows_param': 'warning',
            'local_shadows_global': 'info', 'item_type_literal': 'info', 'renamed_native': 'warning'}
RULES = tuple(SEVERITY)
SLEEP_NATIVES = frozenset(('TriggerSleepAction', 'PolledWait', 'TriggerWaitForSound', 'WaitForSoundBJ',
                           'TriggerSyncReady', 'SyncSelections', 'TriggerSyncStart', 'TriggerWaitOnSleeps'))
NATIVE_RENAMES = (
    ('SetUnitBaseDamage', 'BlzSetUnitBaseDamage'), ('GetUnitBaseDamage', 'BlzGetUnitBaseDamage'),
    ('SetUnitDiceNumber', 'BlzSetUnitDiceNumber'), ('GetUnitDiceNumber', 'BlzGetUnitDiceNumber'),
    ('SetUnitDiceSides', 'BlzSetUnitDiceSides'), ('GetUnitDiceSides', 'BlzGetUnitDiceSides'),
    ('SetUnitAttackCooldown', 'BlzSetUnitAttackCooldown'), ('GetUnitAttackCooldown', 'BlzGetUnitAttackCooldown'),
    ('SetUnitArmor', 'BlzSetUnitArmor'), ('GetUnitArmor', 'BlzGetUnitArmor'))
ITEM_TYPE_NAMES = {7: ('ITEM_TYPE_UNKNOWN', 'ITEM_TYPE_EQUIPMENT'), 8: ('ITEM_TYPE_ANY', 'ITEM_TYPE_UNKNOWN')}
_REF = {}


def ref_natives():
    if 'natives' not in _REF:
        try:
            with open(os.path.join(REF_30, 'common.j'), 'rb') as fh:
                _REF['natives'] = frozenset(re.findall(r'^[ \t]*(?:constant[ \t]+)?native[ \t]+(\w+)',
                                                       fh.read().decode('latin-1'), re.M))
        except OSError:
            _REF['natives'] = frozenset()
    return _REF['natives']


def _is_true(e):
    return type(e) is jass_ast.Literal and e.text == 'true' or type(e) is jass_ast.Name and e.name == 'true'


def _is_literal_name(n):
    return n in ('true', 'false', 'null')


def _calls(node):
    return [n for n in jass_ast.walk(node) if type(n) is jass_ast.Call]


def _names(node):
    return [n.name for n in jass_ast.walk(node) if type(n) is jass_ast.Name]


def _walk_all(stmts):
    for st in stmts:
        for n in jass_ast.walk(st):
            yield n


def _set_bases(stmts):
    out = set()
    for st in _walk_all(stmts):
        if type(st) is jass_ast.SetStmt:
            t = st.target.base if type(st.target) is jass_ast.Index else st.target
            if type(t) is jass_ast.Name:
                out.add(t.name)
    return out


def _own_exits(body):
    out = []
    stack = list(body)
    while stack:
        s = stack.pop()
        t = type(s)
        if t is jass_ast.ExitWhenStmt:
            out.append(s)
        elif t is jass_ast.IfStmt:
            for _c, b in s.branches:
                stack.extend(b)
        elif t is jass_ast.DebugStmt:
            stack.append(s.stmt)
    return out


def _has_return(body):
    return any(type(n) is jass_ast.ReturnStmt for n in _walk_all(body))


def sleepers(tree):
    funcs = dict((f.name, f) for f in tree.functions)
    direct, edges = set(), dict((n, set()) for n in funcs)
    for f in tree.functions:
        for c in _calls(f):
            if c.name in SLEEP_NATIVES:
                direct.add(f.name)
            elif c.name in funcs:
                edges[f.name].add(c.name)
    rev = {}
    for a, bs in edges.items():
        for b in bs:
            rev.setdefault(b, set()).add(a)
    out, stack = set(direct), list(direct)
    while stack:
        n = stack.pop()
        for m in rev.get(n, ()):
            if m not in out:
                out.add(m)
                stack.append(m)
    return out


def _loops(f, waits, funcs, globals_, out):
    for loop in (n for n in jass_ast.walk(f) if type(n) is jass_ast.LoopStmt):
        body = loop.body
        exits = _own_exits(body)
        calls = [c for st in body for c in _calls(st)]
        yields = any(c.name in SLEEP_NATIVES or c.name in waits for c in calls)
        ret = _has_return(body)
        if not exits:
            if not ret and not yields:
                out.append({'rule': 'loop_no_exit', 'function': f.name, 'line': loop.line,
                            'text': 'a loop with no exitwhen, no return and no wait: nothing ends it'})
            continue
        if ret or yields:
            continue
        assigned = _set_bases(body)
        static, mentioned_globals = True, False
        for e in exits:
            if _is_true(e.cond) or any(type(n) is jass_ast.Call for n in jass_ast.walk(e.cond)):
                static = False
                break
            names = [n for n in _names(e.cond) if not _is_literal_name(n)]
            if any(n in assigned for n in names):
                static = False
                break
            if any(n in globals_ for n in names):
                mentioned_globals = True
        if not static:
            continue
        if mentioned_globals and any(c.name in funcs or c.name == 'ExecuteFunc' for c in calls):
            continue
        out.append({'rule': 'loop_static_exit', 'function': f.name, 'line': loop.line,
                    'condition': jass_ast._ue(exits[0].cond)[:100],
                    'text': 'the exit condition reads nothing the loop changes: if it is false when the loop starts, '
                            'the loop never ends'})


def _dead(stmts, f, out):
    seen_return = False
    for s in stmts:
        t = type(s)
        if t is jass_ast.CommentStmt:
            continue
        if seen_return:
            out.append({'rule': 'dead_code', 'function': f.name, 'line': s.line,
                        'text': 'statements after a return never run'})
            return
        if t is jass_ast.ReturnStmt:
            seen_return = True
        elif t is jass_ast.IfStmt:
            for _c, b in s.branches:
                _dead(b, f, out)
        elif t is jass_ast.LoopStmt:
            _dead(s.body, f, out)


def _locals(f, globals_, out):
    if not f.locals:
        return
    reads, targets = set(), set()
    for n in jass_ast.walk(f):
        if type(n) is jass_ast.SetStmt:
            t = n.target.base if type(n.target) is jass_ast.Index else n.target
            if type(t) is jass_ast.Name:
                targets.add(id(t))
    assigned = set()
    for n in jass_ast.walk(f):
        if type(n) is jass_ast.Name:
            if id(n) in targets:
                assigned.add(n.name)
            else:
                reads.add(n.name)
    params = set(nm for _t, nm in f.params)
    for d in f.locals:
        if d.name in params:
            out.append({'rule': 'local_shadows_param', 'function': f.name, 'line': d.line, 'local': d.name,
                        'text': 'local %s has the name of a parameter (pjass: "already defined")' % d.name})
        elif d.name in globals_:
            out.append({'rule': 'local_shadows_global', 'function': f.name, 'line': d.line, 'local': d.name,
                        'text': 'local %s hides the global of the same name' % d.name})
        if d.name not in reads:
            kind = 'never_read' if d.name in assigned or d.initializer is not None else 'unused'
            out.append({'rule': 'unused_local', 'function': f.name, 'line': d.line, 'local': d.name, 'kind': kind,
                        'text': 'local %s is %s' % (d.name, 'only set, never read' if kind == 'never_read'
                                                    else 'never used')})


def _unreachable(tree, funcs):
    edges = dict((n, set()) for n in funcs)
    dynamic = False
    str_names = set()
    for f in tree.functions:
        for n in jass_ast.walk(f):
            t = type(n)
            if t is jass_ast.Call:
                if n.name in funcs:
                    edges[f.name].add(n.name)
                elif n.name == 'ExecuteFunc':
                    a = n.args[0] if n.args else None
                    if type(a) is jass_ast.Literal and a.kind == 'string':
                        edges[f.name].add(a.value)
                    else:
                        dynamic = True
            elif t is jass_ast.FuncRef:
                edges[f.name].add(n.name)
            elif t is jass_ast.Literal and n.kind == 'string' and n.text[1:-1] in funcs:
                edges[f.name].add(n.text[1:-1])
    roots = [n for n in ('main', 'config') if n in funcs]
    for g in tree.globals:
        if g.initializer is not None:
            for n in jass_ast.walk(g.initializer):
                if type(n) is jass_ast.FuncRef and n.name in funcs:
                    roots.append(n.name)
    seen, stack = set(), list(roots)
    while stack:
        n = stack.pop()
        if n in seen or n not in funcs:
            continue
        seen.add(n)
        stack.extend(edges.get(n, ()))
    return [n for n in funcs if n not in seen], dynamic


def _cycles(tree, funcs):
    edges = {}
    for f in tree.functions:
        edges[f.name] = sorted(set(c.name for c in _calls(f) if c.name in funcs))
    index, low, on, stack, comps = {}, {}, set(), [], []
    counter = [0]
    for root in funcs:
        if root in index:
            continue
        work = [(root, 0)]
        while work:
            v, i = work.pop()
            if i == 0:
                index[v] = low[v] = counter[0]
                counter[0] += 1
                stack.append(v)
                on.add(v)
            nxt = edges.get(v, [])
            if i < len(nxt):
                work.append((v, i + 1))
                w = nxt[i]
                if w not in index:
                    work.append((w, 0))
                elif w in on:
                    low[v] = min(low[v], index[w])
            else:
                if low[v] == index[v]:
                    comp = []
                    while True:
                        w = stack.pop()
                        on.discard(w)
                        comp.append(w)
                        if w == v:
                            break
                    if len(comp) > 1 or v in edges.get(v, ()):
                        comps.append(sorted(comp))
                if work:
                    parent = work[-1][0]
                    low[parent] = min(low[parent], low[v])
    return comps


def renamed_natives(tree, declared=None, ref=None):
    declared = declared if declared is not None else set(f.name for f in tree.functions) | \
        set(f.name for f in tree.natives)
    ref = ref if ref is not None else ref_natives()
    wanted = dict((o, n) for o, n in NATIVE_RENAMES if o not in declared and o not in ref and (not ref or n in ref))
    if not wanted:
        return []
    found = {}
    for n in jass_ast.walk(tree):
        if type(n) is jass_ast.Call and n.name in wanted:
            r = found.setdefault(n.name, {'old': n.name, 'new': wanted[n.name], 'count': 0, 'line': n.line})
            r['count'] += 1
    return sorted(found.values(), key=lambda r: r['line'])


def lint(text_or_tree, ref=None):
    if isinstance(text_or_tree, jass_ast.Script):
        tree = text_or_tree
    else:
        try:
            tree = jass_ast.parse(text_or_tree)
        except jass_ast.JassSyntaxError as e:
            return {'language': 'jass', 'error': 'The script does not parse (%s).' % e}
    funcs = dict((f.name, f) for f in tree.functions)
    globals_ = set(g.name for g in tree.globals)
    waits = sleepers(tree)
    findings = []
    for f in tree.functions:
        _loops(f, waits, funcs, globals_, findings)
        _dead(f.body, f, findings)
        _locals(f, globals_, findings)
        for c in _calls(f):
            if c.name == 'ConvertItemType' and len(c.args) == 1 and type(c.args[0]) is jass_ast.Literal and \
                    c.args[0].kind == 'integer' and c.args[0].value in ITEM_TYPE_NAMES:
                v = c.args[0].value
                old, new = ITEM_TYPE_NAMES[v]
                findings.append({'rule': 'item_type_literal', 'function': f.name, 'line': c.line or f.line, 'value': v,
                                 'text': 'ConvertItemType(%d) is %s in 3.0 and was %s before' % (v, new, old)})
    dead, dynamic = _unreachable(tree, funcs)
    if not dynamic:
        for n in dead:
            findings.append({'rule': 'unused_function', 'function': n, 'line': funcs[n].line,
                             'text': 'nothing reaches %s from main or config' % n})
    for comp in _cycles(tree, funcs):
        findings.append({'rule': 'recursion', 'function': comp[0], 'line': funcs[comp[0]].line, 'functions': comp[:8],
                         'text': ('%s calls itself' % comp[0]) if len(comp) == 1 else
                         'these functions call each other in a cycle: %s' % ', '.join(comp[:6])})
    for r in renamed_natives(tree, ref=ref):
        findings.append(
            {
                'rule': 'renamed_native',
                'function': None,
                'line': r['line'],
                'old': r['old'],
                'new': r['new'],
                'count': r['count'],
                'text': '%s was renamed %s in the PTR 1.29 (%d calls)' % (r['old'], r['new'], r['count']),
            }
        )
    for x in findings:
        x['severity'] = SEVERITY[x['rule']]
    counts = dict((r, 0) for r in RULES)
    for x in findings:
        counts[x['rule']] += 1
    kept, per = [], {}
    for x in sorted(findings, key=lambda x: (RULES.index(x['rule']), x['line'])):
        per[x['rule']] = per.get(x['rule'], 0) + 1
        if per[x['rule']] <= LIST_MAX:
            kept.append(x)
    out = {'language': 'jass', 'findings': kept, 'counts': counts, 'dynamic_execute': dynamic}
    out['lines'] = summary(out)
    return out


LABEL = {'loop_no_exit': 'loops that nothing ends', 'loop_static_exit': 'loops whose exit condition cannot change',
         'dead_code': 'blocks with code after a return', 'unused_local': 'locals never read',
         'unused_function': 'functions nothing reaches', 'recursion': 'call cycles',
         'local_shadows_param': 'locals named like a parameter', 'local_shadows_global': 'locals hiding a global',
         'item_type_literal': 'ConvertItemType calls with the old numbers of 7 and 8',
         'renamed_native': 'calls to natives renamed in 1.29'}


def summary(r):
    if r.get('error'):
        return [r['error']]
    out = []
    for rule in RULES:
        n = r['counts'][rule]
        if n:
            ex = [x for x in r['findings'] if x['rule'] == rule][:3]
            where = '; '.join('line %d%s' % (x['line'], (' in ' + x['function']) if x.get('function') else '')
                              for x in ex)
            out.append('%d %s (%s%s).' % (n, LABEL[rule], where, ', ...' if n > len(ex) else ''))
    if r.get('dynamic_execute'):
        out.append('The script runs ExecuteFunc with a name it builds: unused functions are not listed.')
    return out or ['No lint finding.']


def reforged_items(r, made_for_old=False, item=None):
    make = item or (lambda code, sev, text_, fix, **data: dict(code=code, severity=sev, text=text_, fix=fix, data=data))
    out = []
    if r.get('error'):
        return out
    c = r['counts']
    if c['item_type_literal']:
        xs = [x for x in r['findings'] if x['rule'] == 'item_type_literal']
        out.append(
            make(
                'item_type_numbers',
                'warning' if made_for_old else 'info',
                'ConvertItemType is called with the number %s (%d times): 3.0 inserted ITEM_TYPE_EQUIPMENT as 7, '
                'so 7 and 8 meant ITEM_TYPE_UNKNOWN and ITEM_TYPE_ANY before 3.0 and now mean '
                'ITEM_TYPE_EQUIPMENT and ITEM_TYPE_UNKNOWN. Use the constants.'
                % ('/'.join(str(v) for v in sorted(set(x['value'] for x in xs))), c['item_type_literal']),
                'none',
                count=c['item_type_literal'],
            )
        )
    if c['renamed_native']:
        xs = [x for x in r['findings'] if x['rule'] == 'renamed_native']
        out.append(make('renamed_natives', 'warning',
                        'The script calls natives of the PTR 1.29 under their old name: %s. The game declares them '
                        'with the Blz prefix (the calls need the new name).' % ', '.join(
                            '%s -> %s' % (x['old'], x['new']) for x in xs[:6]),
                        'none', count=sum(x['count'] for x in xs)))
    return out


def check(path):
    if path.lower().endswith(('.j', '.ai')):
        return lint(jass_ast.read_script(path))
    from doctor.fix import single_player
    try:
        _a, sc, _s = single_player.read_map(path)
    except BaseException as e:
        if isinstance(e, KeyboardInterrupt):
            raise
        return {'error': 'The map cannot be read (%s).' % e, 'lines': ['The map cannot be read.']}
    if sc['bytes'] is None or sc['language'] != 'jass':
        return {'error': 'The map has no JASS script.', 'lines': ['The map has no JASS script.']}
    return lint(sc['bytes'].decode('latin-1'))
