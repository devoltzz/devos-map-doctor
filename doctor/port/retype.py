# Gives a value an old map disguised as another type (the return bug) its real type back, or carries the handle through a table.
import re


RX_ID = re.compile(r'[A-Za-z_]\w*')
RX_SIG = re.compile(r'(?m)^[ \t]*(?:constant[ \t]+)?(?:native|function)[ \t]+(\w+)[ \t]+takes[ \t]+(.*?)[ \t]+returns'
                    r'[ \t]+(\w+)')
RX_RETURN = re.compile(r'^([ \t]*return[ \t]+)(.*?)([ \t]*)$')
RX_SET = re.compile(r'^[ \t]*set[ \t]+$')
RX_LOCAL_DECL = re.compile(r'^[ \t]*local[ \t]+\w+[ \t]+$')
NEUTRAL = {'integer': '0', 'real': '0.0', 'boolean': 'false', 'string': 'null'}
TABLE_NAME = 'KK_mh_ht'
H2I = 'KKMH_h2i'
I2H = 'KKMH_i2h_'


RX_MASK = re.compile(r'"(?:[^"\\]|\\.)*"?|\'[^\']*\'?|//.*')


def bitmask(ln):
    if '"' not in ln and "'" not in ln and '//' not in ln:
        return ln

    def blank(m):
        t = m.group(0)
        if t.startswith('//'):
            return ' ' * len(t)
        end_pos = t[-1] if len(t) > 1 and t[-1] == t[0] else ''
        return t[0] + ' ' * (len(t) - 1 - len(end_pos)) + end_pos
    return RX_MASK.sub(blank, ln)


def on_close(m, i):
    d = 0
    for k in range(i, len(m)):
        c = m[k]
        if c == '(' or c == '[':
            d += 1
        elif c == ')' or c == ']':
            d -= 1
            if d == 0:
                return k
    return -1


def trim(m, s, e):
    while s < e and m[s] in ' \t':
        s += 1
    while e > s and m[e - 1] in ' \t':
        e -= 1
    return s, e


def arguments(m, i, j):
    out, d, s = [], 0, i + 1
    for k in range(i + 1, j):
        c = m[k]
        if c in '([':
            d += 1
        elif c in ')]':
            d -= 1
        elif c == ',' and d == 0:
            out.append(trim(m, s, k))
            s = k + 1
    s2, e2 = trim(m, s, j)
    if s2 < e2 or out:
        out.append((s2, e2))
    return out


def without_parens(m, s, e):
    s, e = trim(m, s, e)
    while s < e and m[s] == '(' and on_close(m, s) == e - 1:
        s, e = trim(m, s + 1, e - 1)
    return s, e


def whole_call(m, s, e):
    mm = RX_ID.match(m, s)
    if not mm or mm.end() >= e:
        return None
    k = mm.end()
    while k < e and m[k] in ' \t':
        k += 1
    if k >= e or m[k] != '(':
        return None
    j = on_close(m, k)
    if j != e - 1:
        return None
    return mm.group(0), k, j


class Program(object):
    def __init__(self, line_list, ref, ref_text):
        from doctor.port import memory_hacks as _m
        from doctor.port import shadowed as _s
        self.ref = ref
        self.line_list = line_list
        self.masks = [bitmask(line) for line in line_list]
        for k, inside in enumerate(_m.starts_in_string(line_list)):
            if inside:
                line = line_list[k]
                j = 0
                while j < len(line) and line[j] != '"':
                    j += 2 if line[j] == '\\' else 1
                self.masks[k] = ' ' * len(line) if j >= len(line) else ' ' * (j + 1) + bitmask(line[j + 1:])
        self.sig = {}
        for n, ps, r in RX_SIG.findall(ref_text):
            self.sig[n] = (_params(ps), r)
        self.global_type_map = dict((n, t) for n, (t, _v) in _s.reference_declarations(ref_text).items())
        self.garrays = set(re.findall(r'(?m)^[ \t]*(?:constant[ \t]+)?\w+[ \t]+array[ \t]+(\w+)', ref_text))
        gt, gv, self.block_entry = _m._globals(line_list)
        self.global_type_map.update(gt)
        self.garrays |= gv
        self.map_globals = set(gt)
        self.fs = _m._functions(line_list)
        self.by_name = {}
        for f in self.fs:
            begin, end_pos, _r, fname, ps, ret = f
            self.sig[fname] = ([p[0] for p in ps], ret)
            self.by_name[fname] = f
        for k, line in enumerate(line_list):
            if 'native' in line:
                mm = re.match(
                    r'^[ \t]*(?:constant[ \t]+)?native[ \t]+(\w+)[ \t]+takes[ \t]+(.*?)[ \t]+returns[ \t]+(\w+)', line
                )
                if mm:
                    self.sig[mm.group(1)] = (_params(mm.group(2)), mm.group(3))
        self.local_vars = {}
        self.owner = [None] * len(line_list)
        for i, (begin, end_pos, _r, fname, ps, ret) in enumerate(self.fs):
            loc = {}
            for k in range(begin + 1, end_pos):
                self.owner[k] = i
                mm = _m.RX_LOCAL.match(line_list[k])
                if mm:
                    loc[mm.group(2)] = (
                        mm.group(1),
                        k,
                        bool(re.match(r'^[ \t]*local[ \t]+\w+[ \t]+array\b', line_list[k])),
                    )
            self.local_vars[fname] = loc
            self.owner[begin] = i

    def words(self):
        return '\n'.join(self.masks)

    def var_type(self, fname, f):
        if f is not None:
            fn = self.fs[f]
            loc = self.local_vars[fn[3]]
            if fname in loc:
                return loc[fname][0]
            for t, n in fn[4]:
                if n == fname:
                    return t
        return self.global_type_map.get(fname)

    def kind(self, k, s, e):
        m, o = self.masks[k], self.line_list[k]
        s, e = without_parens(m, s, e)
        if s >= e:
            return None
        t = m[s:e]
        if t == 'null':
            return 'null'
        if t in ('true', 'false') or t.startswith('not ') or t.startswith('not('):
            return 'boolean'
        txt = o[s:e]
        if re.fullmatch(r'-?[ \t]*(?:0[xX][0-9a-fA-F]+|\$[0-9a-fA-F]+|\d+)', txt) or re.fullmatch(r"'[^']*'", txt):
            return 'integer'
        if re.fullmatch(r'-?[ \t]*(?:\d+\.\d*|\.\d+)', txt):
            return 'real'
        if re.fullmatch(r'"(?:[^"\\]|\\.)*"', txt):
            return 'string'
        mm = re.fullmatch(r'function[ \t]+(\w+)', t)
        if mm:
            return 'code'
        if RX_ID.fullmatch(t):
            return self.var_type(t, self.owner[k])
        mm = RX_ID.match(m, s)
        if mm:
            j = mm.end()
            while j < e and m[j] in ' \t':
                j += 1
            if j < e and m[j] == '[' and on_close(m, j) == e - 1:
                return self.var_type(mm.group(0), self.owner[k])
            if j < e and m[j] == '(' and on_close(m, j) == e - 1:
                sig = self.sig.get(mm.group(0))
                return sig[1] if sig else None
        return None

    def calls(self, fname):
        out = []
        rx = re.compile(r'\b%s[ \t]*\(' % re.escape(fname))
        for k, m in enumerate(self.masks):
            if fname not in m:
                continue
            for mm in rx.finditer(m):
                if re.search(r'\bfunction[ \t]+$', m[:mm.start()]):
                    continue
                p = mm.end() - 1
                j = on_close(m, p)
                if j > 0:
                    out.append((k, mm.start(), p, j))
        return out


def _params(ps):
    ps = ps.strip()
    if ps == 'nothing':
        return []
    return [p.split()[-2] for p in ps.split(',') if len(p.split()) >= 2]


def _body(line_list, begin, end_pos):
    out = []
    for k in range(begin + 1, end_pos):
        t = line_list[k].split('//')[0].strip()
        if t:
            out.append((k, t))
    return out


def pure_casts(pg):
    out = {}
    for begin, end_pos, _r, fname, ps, ret in pg.fs:
        if len(ps) != 1 or ret == 'nothing':
            continue
        body = _body(pg.line_list, begin, end_pos)
        if not body:
            continue
        mm = re.fullmatch(r'return[ \t]+\(*[ \t]*(\w+)[ \t]*\)*', body[0][1])
        if not mm or mm.group(1) != ps[0][1]:
            continue
        if any(not t.startswith('return') for _k, t in body[1:]):
            continue
        p = ps[0][0]
        if pg.ref.fits(p, ret) or (p == 'integer' and ret == 'real'):
            continue
        out[fname] = (p, ret)
    return out


def _shape(pg, f, casts):
    begin, end_pos, _r, fname, ps, ret = f
    if fname in casts:
        return 'cast'
    if not ps:
        return 'getter'
    return 'body'


def program_census(pg):
    casts = pure_casts(pg)
    out = []
    for i, f in enumerate(pg.fs):
        begin, end_pos, _r, fname, ps, ret = f
        if ret == 'nothing':
            continue
        for k in range(begin + 1, end_pos):
            m = pg.masks[k]
            if 'return' not in m:
                continue
            mm = RX_RETURN.match(m)
            if not mm:
                continue
            s, e = mm.end(1), mm.end(2)
            t = pg.kind(k, s, e)
            if t is None or t == 'null' or pg.ref.fits(t, ret) or (t == 'integer' and ret == 'real'):
                continue
            if t == 'null' and (pg.ref.handle(ret) or ret in ('string', 'code')):
                continue
            out.append((fname, _shape(pg, f, casts), t, ret, k + 1))
    return out


def classe(ref, from_, new_value):
    h1, h2 = ref.handle(from_), ref.handle(new_value)
    if h1 and h2:
        return 'handle->handle'
    if h1 and new_value == 'integer':
        return 'handle->integer'
    if from_ == 'integer' and h2:
        return 'integer->handle'
    if h1 or h2:
        return '%s->%s' % ('handle' if h1 else from_, 'handle' if h2 else new_value)
    return '%s->%s' % (from_, new_value)


class _Slot(object):
    def __init__(self, kind, fname, decl, function=None, idx=None):
        self.kind = kind
        self.fname = fname
        self.decl = decl
        self.function = function
        self.idx = idx
        self.evidence = set()
        self.requires = set()
        self.replacements = []
        self.invalid = None

    def hash_key(self):
        return (self.kind, self.fname, self.function, self.idx)


def _var_occurrences(pg, fname, functions):
    rx = re.compile(r'(?<![\w$])%s\b' % re.escape(fname))
    out = []
    if functions is None:
        ks = [
            k for k in range(len(pg.line_list)) if not (pg.block_entry and pg.block_entry[0] <= k <= pg.block_entry[1])
        ]
    else:
        ks = []
        for i in functions:
            begin, end_pos = pg.fs[i][0], pg.fs[i][1]
            ks.extend(range(begin + 1, end_pos))
    for k in ks:
        m = pg.masks[k]
        if fname not in m:
            continue
        for mm in rx.finditer(m):
            s, e = mm.start(), mm.end()
            if s > 0 and m[s - 1] == '.':
                continue
            j = e
            while j < len(m) and m[j] in ' \t':
                j += 1
            if j < len(m) and m[j] == '[':
                fj = on_close(m, j)
                if fj > 0:
                    e = fj + 1
            out.append((k, s, e))
    return out


def _value_use(pg, slot, k, s, e, casts, func_ret):
    m = pg.masks[k]
    T = slot.decl
    ref = pg.ref
    before = m[:s].rstrip()
    after_diag = m[e:].lstrip()
    if before.endswith('(') and (after_diag.startswith(')') or after_diag.startswith(',')) or \
            before.endswith(',') and (after_diag.startswith(')') or after_diag.startswith(',')):
        d, p = 0, s - 1
        while p >= 0:
            c = m[p]
            if c in ')]':
                d += 1
            elif c in '([':
                if d == 0:
                    break
                d -= 1
            p -= 1
        if p < 0 or m[p] != '(':
            slot.invalid = 'line %d' % (k + 1)
            return
        q = p - 1
        while q >= 0 and m[q] in ' \t':
            q -= 1
        mm = re.search(r'([A-Za-z_]\w*)$', m[:q + 1])
        if not mm:
            slot.invalid = 'line %d' % (k + 1)
            return
        fname = mm.group(1)
        j = on_close(m, p)
        args = arguments(m, p, j)
        idx = next((i for i, (a, b) in enumerate(args) if a == s and b == e), None)
        if idx is None:
            slot.invalid = 'line %d' % (k + 1)
            return
        if fname in casts and len(args) == 1:
            P, R = casts[fname]
            if ref.handle(P) and ref.handle(R) and ref.fits(T, P):
                slot.evidence.add(R)
                slot.replacements.append((k, mm.start(), j + 1, pg.line_list[k][s:e]))
                return
            if ref.handle(P) and ref.fits(T, P):
                slot.requires.add(P)
                return
        sig = pg.sig.get(fname)
        if sig and idx < len(sig[0]) and ref.handle(sig[0][idx]) and ref.fits(T, sig[0][idx]) and \
                sig[0][idx] in ('handle', 'agent'):
            slot.requires.add(sig[0][idx])
            return
        slot.invalid = 'line %d: %s(...)' % (k + 1, fname)
        return
    if re.fullmatch(r'[ \t]*return', before) and not after_diag:
        Q = func_ret
        if Q and ref.handle(Q) and not ref.fits(T, Q):
            slot.evidence.add(Q)
            return
        if Q in ('handle', 'agent') and ref.fits(T, Q):
            slot.requires.add(Q)
            return
        slot.invalid = 'line %d: return' % (k + 1)
        return
    if re.match(r'^(==|!=)[ \t]*null\b', after_diag) or re.search(r'\bnull[ \t]*(==|!=)$', before):
        return
    slot.invalid = 'line %d' % (k + 1)


def _assignment(pg, slot, k, s_rhs, e_rhs, casts):
    m = pg.masks[k]
    s, e = without_parens(m, s_rhs, e_rhs)
    if m[s:e] == 'null':
        return
    ch = whole_call(m, s, e)
    if ch and ch[0] in casts:
        P, R = casts[ch[0]]
        args = arguments(m, ch[1], ch[2])
        if len(args) == 1 and pg.ref.handle(P) and pg.ref.handle(R) and pg.ref.fits(R, slot.decl):
            a, b = args[0]
            slot.evidence.add(P)
            slot.replacements.append((k, s, e, pg.line_list[k][a:b]))
            return
    slot.invalid = 'line %d: assigned' % (k + 1)


def _analyze_var(pg, slot, casts):
    functions = None if slot.kind == 'g' else [slot.function]
    for k, s, e in _var_occurrences(pg, slot.fname, functions):
        if slot.invalid:
            return
        f = pg.owner[k]
        if slot.kind == 'g' and f is not None and pg.var_type(slot.fname, f) is not None and \
                (slot.fname in pg.local_vars[pg.fs[f][3]] or any(n == slot.fname for _t, n in pg.fs[f][4])):
            continue
        m = pg.masks[k]
        if k == pg.fs[f][0] if f is not None else False:
            continue
        before = m[:s]
        if RX_SET.match(before) or RX_LOCAL_DECL.match(before):
            after_diag = m[e:]
            mm = re.match(r'^[ \t]*=', after_diag)
            if not mm:
                if RX_LOCAL_DECL.match(before):
                    continue
                slot.invalid = 'line %d' % (k + 1)
                return
            if '[' in m[s:e] and slot.kind == 'g' and slot.fname not in pg.garrays:
                slot.invalid = 'line %d' % (k + 1)
                return
            _assignment(pg, slot, k, e + mm.end(), len(m.rstrip()), casts)
            continue
        _value_use(pg, slot, k, s, e, casts, pg.fs[f][5] if f is not None else None)


def _analyze_param(pg, slot, casts):
    _analyze_var(pg, slot, casts)
    if slot.invalid:
        return
    f_name = pg.fs[slot.function][3]
    if re.search(r'\bfunction[ \t]+%s\b' % re.escape(f_name), pg.words()):
        slot.invalid = 'function %s' % f_name
        return
    for k, _n, p, j in pg.calls(f_name):
        args = arguments(pg.masks[k], p, j)
        if slot.idx >= len(args):
            slot.invalid = 'line %d' % (k + 1)
            return
        a, b = args[slot.idx]
        _assignment(pg, slot, k, a, b, casts)
        if slot.invalid:
            return


def _analyze_ret(pg, slot, casts):
    begin, end_pos, _r, f_name, _ps, _ret = pg.fs[slot.function]
    for k in range(begin + 1, end_pos):
        m = pg.masks[k]
        mm = RX_RETURN.match(m)
        if mm and 'return' in m:
            _assignment(pg, slot, k, mm.end(1), mm.end(2), casts)
            if slot.invalid:
                return
    for k, n0, p, j in pg.calls(f_name):
        m = pg.masks[k]
        if re.match(r'^[ \t]*call[ \t]+$', m[:n0]) and not m[j + 1:].strip():
            continue
        _value_use(pg, slot, k, n0, j + 1, casts, pg.fs[pg.owner[k]][5] if pg.owner[k] is not None else None)
        if slot.invalid:
            return
    if re.search(r'\bfunction[ \t]+%s\b' % re.escape(f_name), pg.words()):
        slot.invalid = 'function %s' % f_name


def _candidates(pg, casts):
    h2h = dict((n, pr) for n, pr in casts.items() if pg.ref.handle(pr[0]) and pg.ref.handle(pr[1]))
    cands = {}

    def var_slot(fname, f):
        if f is not None:
            fn = pg.fs[f]
            if fname in pg.local_vars[fn[3]]:
                return _Slot('line', fname, pg.local_vars[fn[3]][fname][0], f)
            for i, (t, n) in enumerate(fn[4]):
                if n == fname:
                    return _Slot('p', fname, t, f, i)
        if fname in pg.map_globals:
            return _Slot('g', fname, pg.global_type_map[fname])
        return None

    def place(sl):
        if sl is not None and pg.ref.handle(sl.decl):
            cands.setdefault(sl.hash_key(), sl)

    for c in h2h:
        for k, n0, p, j in pg.calls(c):
            m = pg.masks[k]
            f = pg.owner[k]
            args = arguments(m, p, j)
            if len(args) != 1:
                continue
            a, b = without_parens(m, *args[0])
            t = m[a:b]
            mm = re.fullmatch(r'([A-Za-z_]\w*)(?:[ \t]*\[.*\])?', t)
            if mm:
                place(var_slot(mm.group(1), f))
            ch = whole_call(m, a, b)
            if ch and ch[0] in pg.by_name and ch[0] not in casts:
                place(_Slot('r', ch[0], pg.by_name[ch[0]][5], pg.fs.index(pg.by_name[ch[0]])))
            before = m[:n0]
            mm = re.match(r'^[ \t]*(?:set|local[ \t]+\w+)[ \t]+([A-Za-z_]\w*)(?:[ \t]*\[.*\])?[ \t]*=[ \t]*$', before)
            if mm and not m[j + 1:].strip():
                place(var_slot(mm.group(1), f))
            if re.fullmatch(r'[ \t]*return[ \t]+', before) and not m[j + 1:].strip() and f is not None and \
                    pg.fs[f][3] not in casts:
                place(_Slot('r', pg.fs[f][3], pg.fs[f][5], f))
            d, q = 0, n0 - 1
            while q >= 0:
                cc = m[q]
                if cc in ')]':
                    d += 1
                elif cc in '([':
                    if d == 0:
                        break
                    d -= 1
                q -= 1
            if q >= 0 and m[q] == '(':
                mm = re.search(r'([A-Za-z_]\w*)[ \t]*$', m[:q])
                if mm and mm.group(1) in pg.by_name and mm.group(1) not in casts:
                    jj = on_close(m, q)
                    aa = arguments(m, q, jj)
                    idx = next((i for i, (x, y) in enumerate(aa) if x == n0 and y == j + 1), None)
                    if idx is not None:
                        fn = pg.by_name[mm.group(1)]
                        if idx < len(fn[4]):
                            place(_Slot('p', fn[4][idx][1], fn[4][idx][0], pg.fs.index(fn), idx))
    for i, (begin, end_pos, _r, fname, ps, ret) in enumerate(pg.fs):
        if not pg.ref.handle(ret) or fname in casts:
            continue
        for k in range(begin + 1, end_pos):
            mm = re.match(r'^[ \t]*return[ \t]+\(*[ \t]*([A-Za-z_]\w*)[ \t]*\)*[ \t]*$', pg.masks[k])
            if not mm:
                continue
            t = pg.var_type(mm.group(1), i)
            if t and pg.ref.handle(t) and not pg.ref.fits(t, ret):
                place(var_slot(mm.group(1), i))
    return cands


def retype_carriers(pg, casts, info):
    cands = _candidates(pg, casts)
    good = []
    for sl in cands.values():
        if sl.kind in ('g', 'line'):
            _analyze_var(pg, sl, casts)
        elif sl.kind == 'p':
            _analyze_param(pg, sl, casts)
        else:
            _analyze_ret(pg, sl, casts)
        if sl.invalid:
            info['kept_neutral'].append((sl.kind, sl.fname, sl.decl, sl.invalid))
            continue
        if len(sl.evidence) != 1:
            if sl.evidence:
                info['kept_neutral'].append((sl.kind, sl.fname, sl.decl, 'different real types: %s'
                                             % ', '.join(sorted(sl.evidence))))
            continue
        new = next(iter(sl.evidence))
        if new == sl.decl or not all(pg.ref.fits(new, x) for x in sl.requires):
            continue
        good.append((sl, new))
    seen = {}
    for sl, _n in good:
        for k, s, e, _t in sl.replacements:
            seen.setdefault((k, s), []).append(sl.hash_key())
    clash = set(c for v in seen.values() if len(set(v)) > 1 for c in v)
    replacements = []
    for sl, new in good:
        if sl.hash_key() in clash:
            info['kept_neutral'].append((sl.kind, sl.fname, sl.decl, 'the same cast of another carrier'))
            continue
        replacements.extend(sl.replacements)
        replacements.extend(_declaration(pg, sl, new))
        where = {'g': 'global', 'line': 'local', 'p': 'parameter', 'r': 'return'}[sl.kind]
        fname = sl.fname if sl.kind == 'g' else '%s.%s' % (pg.fs[sl.function][3], sl.fname if sl.kind != 'r' else '')
        info['retyped_vars'].append((where, fname.rstrip('.'), sl.decl, new))
    _apply_swaps(pg, replacements)
    return bool(replacements)


def _declaration(pg, sl, new):
    if sl.kind == 'g':
        a, b = pg.block_entry if pg.block_entry else (0, len(pg.line_list))
        for k in range(a, b + 1):
            m = pg.masks[k]
            mm = re.match(r'^([ \t]*(?:constant[ \t]+)?)(\w+)([ \t]+(?:array[ \t]+)?)%s\b' % re.escape(sl.fname), m)
            if mm and mm.group(2) == sl.decl:
                return [(k, mm.start(2), mm.end(2), new)]
        return []
    if sl.kind == 'line':
        k = pg.local_vars[pg.fs[sl.function][3]][sl.fname][1]
        mm = re.match(r'^([ \t]*local[ \t]+)(\w+)', pg.masks[k])
        return [(k, mm.start(2), mm.end(2), new)]
    k = pg.fs[sl.function][0]
    m = pg.masks[k]
    if sl.kind == 'r':
        mm = re.search(r'\breturns[ \t]+(\w+)', m)
        return [(k, mm.start(1), mm.end(1), new)]
    mm = re.search(r'\btakes[ \t]+(.*?)[ \t]+returns\b', m)
    pos = mm.start(1)
    for i, p in enumerate(mm.group(1).split(',')):
        if i == sl.idx:
            t = re.match(r'([ \t]*)(\w+)', p)
            return [(k, pos + t.start(2), pos + t.end(2), new)]
        pos += len(p) + 1
    return []


def _apply_swaps(pg, replacements):
    by_line = {}
    for t in replacements:
        by_line.setdefault(t[0], []).append(t)
    for k, ts in by_line.items():
        ts = sorted(set(ts), key=lambda t: (t[1], -t[2]))
        outside = []
        for t in ts:
            if outside and t[1] >= outside[-1][1] and t[2] <= outside[-1][2]:
                parent = outside[-1]
                parent_start = parent[1]
                former_id = pg.line_list[k][parent[1]:parent[2]]
                details = former_id[t[1] - parent_start:t[2] - parent_start]
                if details in parent[3]:
                    outside[-1] = (k, parent[1], parent[2], parent[3].replace(details, t[3], 1))
                continue
            outside.append(t)
        line = pg.line_list[k]
        for _k, s, e, txt in sorted(outside, key=lambda t: -t[1]):
            line = line[:s] + txt + line[e:]
        pg.line_list[k] = line
        pg.masks[k] = bitmask(line)


def agents(pg, casts, info):
    ref = pg.ref
    tgt = [(n, 0) for n, (P, R) in casts.items() if P == 'handle' and (R == 'integer' or (ref.handle(R) and
                                                                                            ref.fits(R, 'agent')))]
    for begin, end_pos, _r, fname, ps, ret in pg.fs:
        if fname in casts or not (ret == 'integer' or (ref.handle(ret) and ref.fits(ret, 'agent'))):
            continue
        hs = dict((n, i) for i, (t, n) in enumerate(ps) if t == 'handle')
        if not hs:
            continue
        for k in range(begin + 1, end_pos):
            mm = re.match(r'^[ \t]*return[ \t]+\(*[ \t]*([A-Za-z_]\w*)[ \t]*\)*[ \t]*$', pg.masks[k])
            if mm and mm.group(1) in hs and mm.group(1) not in pg.local_vars[fname]:
                tgt.append((fname, hs[mm.group(1)]))
    if not tgt:
        return False
    cand = {}
    work_queue = list(tgt)
    while work_queue:
        f, idx = work_queue.pop()
        if (f, idx) in cand:
            continue
        deps = []
        fn = pg.by_name[f]
        pname = fn[4][idx][1]
        begin, end_pos = fn[0], fn[1]
        if any(re.match(r'^[ \t]*set[ \t]+%s\b' % re.escape(pname), pg.masks[k]) for k in range(begin + 1, end_pos)):
            cand[(f, idx)] = None
            continue
        ok = True
        for k, _n, p, j in pg.calls(f):
            m = pg.masks[k]
            args = arguments(m, p, j)
            if idx >= len(args):
                ok = False
                break
            a, b = without_parens(m, *args[idx])
            t = pg.kind(k, a, b)
            if t == 'null' or (t and ref.handle(t) and ref.fits(t, 'agent')):
                continue
            g = pg.owner[k]
            if t == 'handle' and g is not None and RX_ID.fullmatch(m[a:b]):
                gfn = pg.fs[g]
                ii = next((i for i, (tt, nn) in enumerate(gfn[4]) if nn == m[a:b] and tt == 'handle'), None)
                if ii is not None and m[a:b] not in pg.local_vars[gfn[3]]:
                    deps.append((gfn[3], ii))
                    work_queue.append((gfn[3], ii))
                    continue
            ok = False
            break
        cand[(f, idx)] = deps if ok else None
    good = set(c for c, d in cand.items() if d is not None)
    changed = True
    while changed:
        changed = False
        for c in list(good):
            if any(d not in good for d in cand[c]):
                good.discard(c)
                changed = True
    for n, i in tgt:
        if (n, i) not in good:
            info['non_agents'].append(n)
    replacements = []
    for f, idx in sorted(good):
        sl = _Slot('p', pg.by_name[f][4][idx][1], 'handle', pg.fs.index(pg.by_name[f]), idx)
        replacements.extend(_declaration(pg, sl, 'agent'))
        info['agents'].append((f, sl.fname))
    _apply_swaps(pg, replacements)
    return bool(replacements)


def expressions(pg, casts, info, neutralize, savers):
    ref = pg.ref
    for i, (begin, end_pos, _r, fname, ps, ret) in enumerate(pg.fs):
        if ret == 'nothing' or fname in casts:
            continue
        if len(ps) == 1 and all(t.startswith('return') for _k, t in _body(pg.line_list, begin, end_pos)):
            continue
        for k in range(begin + 1, end_pos):
            m = pg.masks[k]
            if 'return' not in m:
                continue
            mm = RX_RETURN.match(m)
            if not mm:
                continue
            s, e = mm.end(1), mm.end(2)
            t = pg.kind(k, s, e)
            if t is None or t == 'null' or ref.fits(t, ret) or (t == 'integer' and ret == 'real'):
                continue
            expr = pg.line_list[k][s:e]
            new = None
            if t == 'integer' and ref.handle(ret) and ref.load_data.get(ret):
                new = '%s%s(%s)' % (I2H, ret, expr)
                info['helpers'].add(ret)
            elif ref.handle(t) and ret == 'integer':
                if ref.fits(t, 'agent') and savers:
                    new = '%s(%s)' % (H2I, expr)
                    info['helpers'].add(H2I)
                else:
                    new = 'GetHandleId(%s)' % expr
            elif ref.handle(t) and ref.handle(ret) and ref.fits(ret, t) and ref.fits(t, 'agent') and \
                    ref.load_data.get(ret):
                new = '%s%s(%s(%s))' % (I2H, ret, H2I, expr)
                info['helpers'].update((ret, H2I))
            elif t == 'string' and ret == 'integer':
                new = 'KKMH_s2i(%s)' % expr
                info['helpers'].add('KKMH_s2i')
            elif t == 'integer' and ret == 'string':
                new = 'KKMH_i2s(%s)' % expr
                info['helpers'].add('KKMH_i2s')
            elif t == 'boolean' and ret == 'integer':
                new = 'KKMH_b2i(%s)' % expr
                info['helpers'].add('KKMH_b2i')
            elif t == 'integer' and ret == 'boolean':
                new = '(%s) != 0' % expr
            elif t == 'real' and ret == 'integer':
                new = 'R2I(%s)' % expr
            if new is None:
                if not neutralize:
                    continue
                new = 'function KKMH_vazio' if ret == 'code' else NEUTRAL.get(ret, 'null')
                info['neutral_expr'].append((fname, t, ret))
                info['empty_code'] = info.get('empty_code') or ret == 'code'
            else:
                info['expressions'].append((fname, t, ret))
            pg.line_list[k] = pg.line_list[k][:s] + new + pg.line_list[k][e:]
            pg.masks[k] = bitmask(pg.line_list[k])


def helpers(ref, chosen):
    lazy_init = ['    if %s == null then' % TABLE_NAME, '        set %s = InitHashtable()' % TABLE_NAME, '    endif']
    out = []
    if H2I in chosen:
        out += (
            ['function %s takes agent h returns integer' % H2I]
            + lazy_init
            + [
                '    call SaveAgentHandle(%s, 0, GetHandleId(h), h)' % TABLE_NAME,
                '    return GetHandleId(h)',
                'endfunction',
            ]
        )
    if 'KKMH_s2i' in chosen:
        out += ['function KKMH_s2i takes string s returns integer'] + lazy_init + [
            '    call SaveStr(%s, 1, StringHash(s), s)' % TABLE_NAME, '    return StringHash(s)', 'endfunction']
    if 'KKMH_i2s' in chosen:
        out += ['function KKMH_i2s takes integer i returns string'] + lazy_init + [
            '    return LoadStr(%s, 1, i)' % TABLE_NAME, 'endfunction']
    if 'KKMH_b2i' in chosen:
        out += ['function KKMH_b2i takes boolean b returns integer', '    if b then', '        return 1', '    endif',
                '    return 0', 'endfunction']
    for t in sorted(q for q in chosen if not q.startswith('KKMH_')):
        out += ['function %s%s takes integer i returns %s' % (I2H, t, t)] + lazy_init + [
            '    return %s(%s, 0, i)' % (ref.load_data[t], TABLE_NAME), 'endfunction']
    return out


def new_info():
    return {'retyped_vars': [], 'kept_neutral': [], 'agents': [], 'non_agents': [], 'expressions': [],
            'neutral_expr': [], 'helpers': set(), 'casts': {}}


def applies(line_list, ref, ref_text, neutralize=False):
    info = new_info()
    if not any('return' in line for line in line_list):
        return info
    pg = Program(line_list, ref, ref_text)
    casts = pure_casts(pg)
    info['casts'] = dict(casts)
    if not casts and not program_census(pg):
        return info
    if casts and retype_carriers(pg, casts, info):
        pg = Program(line_list, ref, ref_text)
    goes_back = any(P == 'integer' and ref.handle(R) for P, R in casts.values()) or any(
        t == 'integer' and ref.handle(r) for _f, _fo, t, r, _l in program_census(pg))
    if goes_back and agents(pg, casts, info):
        pg = Program(line_list, ref, ref_text)
    expressions(pg, casts, info, neutralize, savers=goes_back)
    return info


def report_data(info):
    pieces = []
    if info['retyped_vars']:
        pieces.append('%d return bug carrier(s) with the real type: %s' % (
            len(info['retyped_vars']), ', '.join('%s %s %s->%s' % x for x in info['retyped_vars'][:8])))
    if info['agents']:
        pieces.append('%d handle parameter(s) -> agent (the real handle goes to the table): %s' % (
            len(info['agents']), ', '.join('%s.%s' % x for x in info['agents'][:8])))
    if info['expressions']:
        pieces.append('%d return(s) of another type through the table' % len(info['expressions']))
    if info['neutral_expr']:
        pieces.append('%d return(s) without an equivalent -> neutral' % len(info['neutral_expr']))
    if pieces:
        print('0h bridge: ' + '; '.join(pieces))
