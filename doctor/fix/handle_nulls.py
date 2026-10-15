# Finds the handle locals a JASS function leaves without null, and writes the missing lines.
import os
import re

from doctor.script import jass_ast


REF_30 = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ref', '3.0'))
COUNTED_ALTHOUGH_HANDLE = ('triggeraction', 'unitpool', 'itempool', 'camerasetup', 'framehandle', 'commandbuttoneffect')
FALLBACK = frozenset(
    (
        'agent',
        'event',
        'player',
        'widget',
        'unit',
        'destructable',
        'item',
        'ability',
        'buff',
        'force',
        'group',
        'trigger',
        'triggercondition',
        'timer',
        'location',
        'region',
        'rect',
        'boolexpr',
        'sound',
        'conditionfunc',
        'filterfunc',
        'effect',
        'fogmodifier',
        'dialog',
        'button',
        'quest',
        'questitem',
        'defeatcondition',
        'timerdialog',
        'leaderboard',
        'multiboard',
        'multiboarditem',
        'trackable',
        'gamecache',
        'hashtable',
        'framehandle',
    )
    + COUNTED_ALTHOUGH_HANDLE
)
RX_TYPE = re.compile(r'^[ \t]*type[ \t]+(\w+)[ \t]+extends[ \t]+(\w+)', re.M)
_TYPES = {}
LIST_MAX = 60
NULL, NONNULL, MAYBE = 'N', 'X', 'M'


def _common_text():
    try:
        with open(os.path.join(REF_30, 'common.j'), 'rb') as fh:
            return fh.read().decode('latin-1')
    except OSError:
        return None


def types(common_text=None, script_text=None):
    key = (common_text is None, hash(common_text) if common_text else 0, hash(script_text) if script_text else 0)
    if key in _TYPES:
        return _TYPES[key]
    parent = {}
    text = common_text if common_text is not None else _common_text()
    for t in (text, script_text):
        if t:
            for m in RX_TYPE.finditer(t):
                parent.setdefault(m.group(1), m.group(2))
    if not parent:
        out = FALLBACK
    else:
        out = set(COUNTED_ALTHOUGH_HANDLE)
        for name in parent:
            seen, n = set(), name
            while n in parent and n not in seen:
                seen.add(n)
                n = parent[n]
                if n == 'agent':
                    out.add(name)
                    break
        out.add('agent')
        out = frozenset(out)
    if len(_TYPES) > 8:
        _TYPES.clear()
    _TYPES[key] = out
    return out


def _is_null(e):
    return type(e) is jass_ast.Literal and e.kind == 'null' or type(e) is jass_ast.Name and e.name == 'null'


def _unparen(e):
    while type(e) is jass_ast.Paren:
        e = e.inner
    return e


def _guard(cond, tracked):
    cond = _unparen(cond)
    if type(cond) is jass_ast.Unary and cond.op == 'not':
        g = _guard(cond.operand, tracked)
        return None if g is None else (g[0], not g[1])
    if type(cond) is jass_ast.Binary and cond.op in ('==', '!='):
        a, b = _unparen(cond.left), _unparen(cond.right)
        if _is_null(b) and type(a) is jass_ast.Name and a.name in tracked:
            return a.name, cond.op == '=='
        if _is_null(a) and type(b) is jass_ast.Name and b.name in tracked:
            return b.name, cond.op == '=='
    return None


def _refine(state, cond, truth, tracked):
    g = _guard(cond, tracked)
    if g is None:
        return state
    name, is_null = g
    out = dict(state)
    out[name] = NULL if is_null == truth else NONNULL
    return out


def _join(a, b):
    out = dict(a)
    for k, v in b.items():
        w = a.get(k, NULL)
        out[k] = w if w == v else MAYBE
    return out


def _join_all(states):
    out = None
    for s in states:
        out = s if out is None else _join(out, s)
    return out


class _Flow(object):
    def __init__(self, tracked):
        self.tracked = tracked
        self.exits = []

    def block(self, stmts, state, loops, record):
        for s in stmts:
            t = type(s)
            if t is jass_ast.SetStmt:
                if type(s.target) is jass_ast.Name and s.target.name in self.tracked:
                    state = dict(state)
                    state[s.target.name] = NULL if _is_null(s.value) else NONNULL
            elif t is jass_ast.ReturnStmt:
                if record:
                    self.exits.append(('return', s.line, s, state))
                return None
            elif t is jass_ast.IfStmt:
                state = self.branches(s, state, loops, record)
                if state is None:
                    return None
            elif t is jass_ast.LoopStmt:
                state = self.loop(s, state, loops, record)
                if state is None:
                    return None
            elif t is jass_ast.ExitWhenStmt:
                if loops:
                    loops[-1].append(_refine(state, s.cond, True, self.tracked))
                state = _refine(state, s.cond, False, self.tracked)
            elif t is jass_ast.DebugStmt:
                inner = s.stmt
                if type(inner) is jass_ast.SetStmt or type(inner) is jass_ast.CallStmt:
                    after = self.block([inner], state, loops, False)
                    state = _join(state, after) if after is not None else state
        return state

    def branches(self, s, state, loops, record):
        cur = state
        results = []
        has_else = False
        for cond, body in s.branches:
            if cond is None:
                has_else = True
                bstate = cur
            else:
                bstate = _refine(cur, cond, True, self.tracked)
            end = self.block(body, bstate, loops, record)
            if end is not None:
                results.append(end)
            if cond is not None:
                cur = _refine(cur, cond, False, self.tracked)
        if not has_else:
            results.append(cur)
        return _join_all(results)

    def loop(self, s, state, loops, record):
        exits = []
        if not record:
            self.block(s.body, state, loops + [exits], False)
            return _join_all(exits)
        end = self.block(s.body, state, loops + [exits], False)
        start = state if end is None else _join(state, end)
        exits = []
        end = self.block(s.body, start, loops + [exits], record)
        return _join_all(exits)


def _locals_of(f, ntypes):
    out, lines = {}, {}
    for d in f.locals:
        if not d.is_array and d.type in ntypes:
            out[d.name] = d.type
            lines[d.name] = d.line
    return out, lines


def _initial(f, tracked):
    state = {}
    for d in f.locals:
        if d.name in tracked:
            state[d.name] = NULL if d.initializer is None or _is_null(d.initializer) else NONNULL
    return state


def _reads(e):
    return set(n.name for n in jass_ast.walk(e) if type(n) is jass_ast.Name)


def function_leaks(f, ntypes):
    tracked, decl = _locals_of(f, ntypes)
    if not tracked:
        return []
    flow = _Flow(tracked)
    end = flow.block(f.body, _initial(f, tracked), [], True)
    if end is not None:
        flow.exits.append(('end', f.end_line, None, end))
    out = []
    for kind, line, stmt, state in flow.exits:
        reads = _reads(stmt.value) if stmt is not None and stmt.value is not None else ()
        for name, st in state.items():
            if st != NULL:
                out.append({'local': name, 'type': tracked[name], 'kind': kind, 'line': line,
                            'decl_line': decl[name], 'returned': name in reads, 'stmt': stmt})
    return out


def analyze(text_or_tree, types_=None, heat=True, common_text=None):
    if isinstance(text_or_tree, jass_ast.Script):
        tree, text = text_or_tree, None
    else:
        text = text_or_tree
        try:
            tree = jass_ast.parse(text)
        except jass_ast.JassSyntaxError as e:
            return {'language': 'jass', 'error': 'The script does not parse (%s).' % e}
    ntypes = types_ or types(common_text, text)
    heats = {}
    if heat:
        try:
            from doctor.script import script_checks
            heats = script_checks.heat_of(tree)
        except Exception:
            heats = {}
    leaks, n_locals, n_funcs = [], 0, 0
    for f in tree.functions:
        tracked, _decl = _locals_of(f, ntypes)
        if not tracked:
            continue
        n_locals += len(tracked)
        found = function_leaks(f, ntypes)
        if found:
            n_funcs += 1
        for x in found:
            x.pop('stmt', None)
            x['function'] = f.name
            x['heat'] = heats.get(f.name)
            leaks.append(x)
    counts = {'leaks': len(leaks), 'locals': n_locals, 'functions': n_funcs,
              'locals_leaking': len(set((x['function'], x['local']) for x in leaks))}
    for h in ('hot', 'repeat', 'once', 'unused'):
        counts[h] = len(set((x['function'], x['local']) for x in leaks if x['heat'] == h))
    order = {'hot': 0, 'repeat': 1, 'once': 2, 'unused': 3, None: 4}
    leaks.sort(key=lambda x: (order[x['heat']], x['line']))
    out = {'language': 'jass', 'leaks': leaks[:LIST_MAX * 5], 'counts': counts}
    out['lines'] = summary(out)
    return out


def summary(r):
    if r.get('error'):
        return [r['error']]
    c = r['counts']
    if not c['leaks']:
        return ['No handle local is left set when its function ends.']
    out = ['%d handle locals in %d functions are not set to null when the function ends (%d on a periodic timer, %d on '
           'an event): each keeps its object\'s handle id from being recycled.' % (
               c['locals_leaking'], c['functions'], c['hot'], c['repeat'])]
    seen = set()
    for x in r['leaks']:
        k = (x['function'], x['local'])
        if k in seen or x['heat'] not in ('hot', 'repeat'):
            continue
        seen.add(k)
        out.append('  line %d, %s: local %s (%s).' % (x['line'], x['function'], x['local'], x['type']))
        if len(seen) >= 8:
            break
    return out


def reforged_items(r, item=None):
    if r.get('error') or not r.get('counts') or not r['counts']['leaks']:
        return []
    c = r['counts']
    text = ('%d handle locals in %d functions are not set to null when the function ends (%d on a periodic timer, '
            '%d on an event): each keeps its object\'s handle id from being recycled. The Fix map option "Null handle '
            'locals" writes the missing lines.' % (c['locals_leaking'], c['functions'], c['hot'], c['repeat']))
    make = item or (lambda code, sev, text_, fix, **data: dict(code=code, severity=sev, text=text_, fix=fix, data=data))
    return [make('handle_locals_not_nulled', 'info', text, 'doctor', locals=c['locals_leaking'],
                 functions=c['functions'], hot=c['hot'], repeat=c['repeat'])]


_LINE_RE = re.compile(r'[^\r\n]*(?:\r\n|\r|\n|\Z)')


def _split(text):
    out = _LINE_RE.findall(text)
    if out and out[-1] == '':
        out.pop()
    return out


def _eol(text):
    m = re.search(r'\r\n|\r|\n', text)
    return m.group(0) if m else '\n'


def _indent(line):
    return line[:len(line) - len(line.lstrip(' \t'))]


def _body_indent(f, lines):
    for node in list(f.locals) + list(f.body):
        n = getattr(node, 'line', 0)
        if 0 < n <= len(lines) and lines[n - 1].strip() and not lines[n - 1].lstrip().startswith('function'):
            return _indent(lines[n - 1])
    return '    '


def _free_name(text, base):
    name, k = base, 0
    while re.search(r'\b' + re.escape(name) + r'\b', text):
        k += 1
        name = '%s_%d' % (base, k)
    return name


def fix_text(text, types_=None, common_text=None):
    rep = {'state': 'nothing_to_do', 'reason': None, 'nulls': 0, 'functions': 0, 'temps': [], 'skipped': 0}
    try:
        tree = jass_ast.parse(text)
    except jass_ast.JassSyntaxError as e:
        rep.update(state='failed', reason='The script does not parse (%s).' % e)
        return text, rep
    ntypes = types_ or types(common_text, text)
    lines = _split(text)
    eol = _eol(text)
    before, after = {}, {}
    temps = {}
    changed = set()

    def temp(rtype):
        if rtype not in temps:
            temps[rtype] = _free_name(text, 'nl__' + rtype)
        return temps[rtype]

    for f in tree.functions:
        tracked, _decl = _locals_of(f, ntypes)
        if not tracked:
            continue
        found = function_leaks(f, ntypes)
        if not found:
            continue
        by_exit = {}
        for x in found:
            by_exit.setdefault((x['kind'], x['line']), []).append(x)
        for (kind, line), xs in sorted(by_exit.items(), key=lambda kv: kv[0][1]):
            if line < 1 or line > len(lines):
                rep['skipped'] += len(xs)
                continue
            src = lines[line - 1]
            ind = _indent(src)
            names = sorted(set(x['local'] for x in xs), key=lambda n: [d.name for d in f.locals].index(n))
            nulls = [ind + 'set ' + n + ' = null' for n in names]
            if kind == 'end':
                if src.strip().split('//')[0].strip() != 'endfunction':
                    rep['skipped'] += len(xs)
                    continue
                ind = _body_indent(f, lines)
                before.setdefault(line, []).extend(ind + 'set ' + n + ' = null' for n in names)
                rep['nulls'] += len(names)
                changed.add(f.name)
                continue
            head = src.strip()
            if not head.startswith('return') or (len(head) > 6 and head[6] not in ' \t/('):
                rep['skipped'] += len(xs)
                continue
            stmt = xs[0].get('stmt')
            if any(x['returned'] for x in xs) or (stmt is not None and stmt.value is not None and
                                                  _reads(stmt.value) & set(names)):
                if f.return_type in ('nothing',):
                    rep['skipped'] += len(xs)
                    continue
                g = temp(f.return_type)
                comment = ('' if not stmt.comment else ' ' + stmt.comment)
                after[line] = ([ind + 'set ' + g + ' = ' + jass_ast._ue(stmt.value)] + nulls +
                               [ind + 'return ' + g + comment])
            else:
                before.setdefault(line, []).extend(nulls)
            rep['nulls'] += len(names)
            changed.add(f.name)
    if not rep['nulls']:
        if rep['skipped']:
            rep['reason'] = '%d exits could not be edited by line.' % rep['skipped']
        return text, rep
    if temps:
        decls = [ind_ + t + ' ' + g for t, g in sorted(temps.items()) for ind_ in ['    ']]
        end_globals = next((i + 1 for i, ln in enumerate(lines) if ln.strip().split('//')[0].strip() == 'endglobals'),
                           None)
        if end_globals is not None:
            before.setdefault(end_globals, [])
            before[end_globals] = decls + before[end_globals]
        else:
            first = next((i + 1 for i, ln in enumerate(lines)
                          if re.match(r'[ \t]*(?:constant[ \t]+)?function[ \t]', ln)), None)
            if first is None:
                rep.update(state='failed', reason='There is no place for the global the returns go through.')
                return text, rep
            before.setdefault(first, [])
            before[first] = ['globals'] + decls + ['endglobals'] + before[first]
    out = []
    for i, ln in enumerate(lines, 1):
        for extra in before.get(i, ()):
            out.append(extra + eol)
        if i in after:
            tail = re.search(r'(?:\r\n|\r|\n)\Z', ln)
            repl = after[i]
            out.append(eol.join(repl) + (tail.group(0) if tail else ''))
        else:
            out.append(ln)
    new = ''.join(out)
    try:
        jass_ast.parse(new)
    except jass_ast.JassSyntaxError as e:
        rep.update(state='failed', reason='The fixed script does not parse (%s): kept as it was.' % e)
        return text, rep
    rep.update(state='done', functions=len(changed), temps=sorted(temps.values()))
    return new, rep


def _pjass(text, common=None, blizzard=None, pjass=None, workdir=None):
    import tempfile
    from doctor.script import pjass as pj
    ref = pj.REF_30
    tmp = workdir or tempfile.mkdtemp(prefix='handle_nulls_')
    os.makedirs(tmp, exist_ok=True)
    path = os.path.join(tmp, 'war3map.j')
    try:
        with open(path, 'wb') as fh:
            fh.write(text.encode('latin-1') if isinstance(text, str) else text)
        res = pj.run_action([(common or os.path.join(ref, 'common.j'), 'common.j'),
                             (blizzard or os.path.join(ref, 'blizzard.j'), 'blizzard.j'), (path, 'war3map.j')],
                            pjass=pjass, tmp=tmp)
    finally:
        if workdir is None:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)
    return res


def prove(before, after, pjass=None, workdir=None, run_main=True, budget=400000, seconds=15.0):
    out = {'ok': True, 'pjass': {}, 'eval': {}}
    a = _pjass(before, pjass=pjass, workdir=workdir and os.path.join(workdir, 'a'))
    b = _pjass(after, pjass=pjass, workdir=workdir and os.path.join(workdir, 'b'))
    na, nb = len(a['error_list']) + len(a['warnings']), len(b['error_list']) + len(b['warnings'])
    out['pjass'] = {'before': na, 'after': nb, 'rc_before': a['rc'], 'rc_after': b['rc'],
                    'first_errors': (b['error_list'] or b['warnings'])[:5]}
    if nb > na or (a['rc'] == 0 and b['rc'] != 0):
        out['ok'] = False
    if run_main:
        from doctor.script import jass_eval
        data_a = before.encode('latin-1') if isinstance(before, str) else before
        data_b = after.encode('latin-1') if isinstance(after, str) else after
        ia = jass_eval.run(data_a, budget=budget, seconds=seconds)
        ib = jass_eval.run(data_b, budget=budget, seconds=seconds)

        def plain(it):
            return dict((k, v) for k, v in it.globals.items()
                        if isinstance(v, (int, float, bool, str)) and not isinstance(v, jass_eval.Handle))
        same_unknown = ia.unknown == ib.unknown
        same_crashes = ia.crashes == ib.crashes
        pa, pb = plain(ia), plain(ib)
        extra = [k for k in pb if k not in pa and k.startswith('nl__')]
        same_globals = all(pa.get(k) == pb.get(k) for k in pa)
        out['eval'] = {'unknown_same': same_unknown, 'crashes_same': same_crashes, 'globals_same': same_globals,
                       'globals': len(pa), 'stopped_before': ia.stopped, 'stopped_after': ib.stopped,
                       'steps_before': ia.steps, 'steps_after': ib.steps, 'temps_seen': len(extra)}
        if not (same_unknown and same_crashes and same_globals) or (ia.stopped is None) != (ib.stopped is None):
            out['ok'] = False
    return out


def fix(path_in, path_out, progress=None):
    from doctor.fix import script_rewrite

    def transform(text, language):
        if language != 'jass':
            return text, {'state': 'nothing_to_do', 'reason': 'The script is %s, not JASS.' % language}
        new, rep = fix_text(text)
        if rep['state'] == 'done':
            pj = prove(text, new, run_main=False)
            rep['pjass'] = pj['pjass']
            if not pj['ok']:
                return text, {
                    'state': 'refused',
                    'reason': 'pjass finds more errors in the fixed script: kept as it was.',
                    'nulls': 0,
                }
        return new, rep

    def line(name, r):
        return '%s: %d "set x = null" lines written in %d functions%s.' % (
            name, r['nulls'], r['functions'], (', %d exits left as they are' % r['skipped']) if r['skipped'] else '')
    return script_rewrite.rewrite(path_in, path_out, transform, progress, line)


def check(path):
    if path.lower().endswith(('.j', '.ai')):
        return analyze(jass_ast.read_script(path))
    from doctor.fix import single_player
    try:
        _a, sc, _s = single_player.read_map(path)
    except BaseException as e:
        if isinstance(e, KeyboardInterrupt):
            raise
        return {'error': 'The map cannot be read (%s).' % e, 'lines': ['The map cannot be read.']}
    if sc['bytes'] is None or sc['language'] != 'jass':
        return {'error': 'The map has no JASS script.', 'lines': ['The map has no JASS script.']}
    return analyze(sc['bytes'].decode('latin-1'))
