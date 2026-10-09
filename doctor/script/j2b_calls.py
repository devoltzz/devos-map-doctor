# Finds the targets of the hidden calls of the newer j2b bytecode by inference, without running the map.
import bisect
import collections
import os
import re
import struct

from doctor.script import kkwe_compile as KC


FUNCTION, ENDFUNCTION, LOCAL, GLOBAL, CONSTANT, FUNCARG, POPN = 3, 4, 5, 6, 7, 8, 11
LIT, MOVRR, MOVRV, MOVRCODE, MOVRA, MOVVR, MOVAR, PUSH, POP = 12, 13, 14, 15, 16, 17, 18, 19, 20
CALLN, CALLJ, I2R, RET, LABEL, JIT, JIF, JUMP = 21, 22, 23, 39, 40, 41, 42, 43
HIDDEN = 36
BASE = {'integer': 4, 'real': 5, 'string': 6, 'boolean': 8, 'code': 3, 'nothing': 0}
ANCHORS = (MOVVR, MOVAR, RET, ENDFUNCTION)
PURE = re.compile(r'^(Get|Is|Load|Have|I2|R2|S2|Count|String|SubString|Sin|Cos|Tan|SquareRoot|Pow|Abs|Deg2Rad|'
                  r'Rad2Deg|Atan|Asin|Acos|Modulo|Player$|Convert|Bitwise)')


def code_of(t):
    return BASE.get(t, 7)


def hidden_sites(bc):
    sites = collections.defaultdict(list)
    op, b0, b1, b2, arg = bc.op, bc.b0, bc.b1, bc.b2, bc.arg
    for k in range(bc.n):
        if op[k] == HIDDEN and b0[k] == 0 and b1[k] == 0 and b2[k] == 0:
            sites[arg[k] & 0xFFFFFFFF].append(k)
    return sites


class Signatures(object):
    def __init__(self, texts):
        self.parent = {'handle': None}
        self.natives = {}
        self.functions = {}
        for text in texts:
            for it in KC.analyze(_declarations(text)):
                if it[0] == 'type':
                    self.parent.setdefault(it[1], it[2])
                elif it[0] == 'native':
                    self.natives.setdefault(it[1], ([p[0] for p in it[2]], it[3]))
                elif it[0] == 'function':
                    self.functions.setdefault(it[1], ([p[0] for p in it[2]], it[3]))

    def is_sub(self, t, ancestor):
        seen = 0
        while t is not None and seen < 64:
            if t == ancestor:
                return True
            t = self.parent.get(t)
            seen += 1
        return False

    def comparable(self, a, b):
        return self.is_sub(a, b) or self.is_sub(b, a)

    def join(self, a, b):
        if a is None:
            return b
        if b is None or self.is_sub(b, a):
            return a
        anc = []
        t = a
        while t is not None and len(anc) < 64:
            anc.append(t)
            t = self.parent.get(t)
        t = b
        while t is not None:
            if t in anc:
                return t
            t = self.parent.get(t)
        return 'handle'


def _declarations(text):
    out = []
    inside = False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith('function '):
            inside = True
            out.append(line)
            continue
        if inside:
            out.append(line)
            if s.startswith('endfunction'):
                inside = False
            continue
        if s.startswith(('type ', 'native ', 'constant native ')):
            out.append(line)
    return '\n'.join(out)


def reference_pairs(bc, texts):
    comp = KC.Compiler()
    for text in texts:
        try:
            comp.file_name(KC.analyze(text))
        except Exception:
            continue
    ref, cur = {}, None
    for b0, b1, b2, op, a in comp.ins:
        if op == FUNCTION:
            cur = str(a)
            ref[cur] = []
        if cur is not None:
            ref[cur].append((op, str(a) if isinstance(a, KC.Symbol) else a))
        if op == ENDFUNCTION:
            cur = None
    starts = {f[1]: f[0] for f in bc.functions()}
    seen = collections.defaultdict(set)
    for name, seq in ref.items():
        k0 = starts.get(name)
        if k0 is None or k0 + len(seq) > bc.n:
            continue
        found = []
        for i, (op, a) in enumerate(seq):
            k = k0 + i
            if op in (CALLN, CALLJ):
                if not (bc.op[k] == HIDDEN and bc.b0[k] == 0 and bc.b1[k] == 0 and bc.b2[k] == 0):
                    found = None
                    break
                found.append((bc.arg[k] & 0xFFFFFFFF, op, a))
            elif bc.op[k] != op:
                found = None
                break
        for t, op, a in found or ():
            seen[t].add((op, a))
    pairs = {t: next(iter(v)) for t, v in seen.items() if len(v) == 1}
    return pairs, {t: v for t, v in seen.items() if len(v) > 1}


def _compiled_functions(base_texts, script):
    cache = os.environ.get('J2B_CALLS_CACHE')
    if cache:
        import hashlib
        import pickle
        h = hashlib.sha1()
        for text in list(base_texts) + [script]:
            h.update(text.encode('utf-8', 'surrogateescape'))
        path = os.path.join(cache, h.hexdigest() + '.pkl')
        if os.path.isfile(path):
            with open(path, 'rb') as f:
                return pickle.load(f)
        out = _compiled_functions_now(base_texts, script)
        os.makedirs(cache, exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump(out, f)
        return out
    return _compiled_functions_now(base_texts, script)


def _compiled_functions_now(base_texts, script):
    comp = KC.Compiler()
    try:
        for text in base_texts:
            comp.declare_all(KC.analyze(text))
        comp.file_name(KC.analyze(script))
    except Exception:
        return {}
    out, cur, ops, calls = {}, None, None, None
    for _b0, _b1, _b2, op, a in comp.ins:
        if op == FUNCTION:
            cur, ops, calls = str(a), bytearray(), []
        if cur is None:
            continue
        if op in (CALLN, CALLJ):
            ops.append(HIDDEN)
            calls.append((op, str(a)))
        else:
            ops.append(op)
        if op == ENDFUNCTION:
            out[cur] = (bytes(ops), calls)
            cur = None
    return out


def corpus_pairs(bc, base_texts, scripts, known, log=None):
    say = log or (lambda *a: None)
    starts = {f[1]: f[0] for f in bc.functions()}
    mine = {}
    for name, k0 in starts.items():
        ops, toks = bytearray(), []
        k = k0
        while True:
            o = bc.op[k]
            if o == HIDDEN and bc.b0[k] == 0 and bc.b1[k] == 0 and bc.b2[k] == 0:
                toks.append(bc.arg[k] & 0xFFFFFFFF)
            ops.append(o)
            if o == ENDFUNCTION:
                break
            k += 1
        mine[name] = (bytes(ops), toks)
    candidates = []
    bigrams = collections.Counter()
    for i, script in enumerate(scripts):
        for name, (ops, calls) in _compiled_functions(base_texts, script).items():
            for (_o1, c1), (_o2, c2) in zip(calls, calls[1:]):
                bigrams[c1, c2] += 1
            m = mine.get(name)
            if m is None or m[0] != ops or len(m[1]) != len(calls) or not calls:
                continue
            candidates.append((name, [(t, op, callee) for t, (op, callee) in zip(m[1], calls)]))
    say('corpus: %d function bodies equal to the bytecode' % len(candidates))
    added = 0
    while True:
        votes = collections.defaultdict(set)
        for name, items in candidates:
            check = [(t, c) for t, _op, c in items if t in known]
            if not check or any(known[t] != c for t, c in check):
                continue
            for t, _op, c in items:
                if t not in known:
                    votes[t].add(c)
        taken = set(known.values())
        new = {t: next(iter(v)) for t, v in votes.items() if len(v) == 1 and next(iter(v)) not in taken}
        twice = {n for n, c in collections.Counter(new.values()).items() if c > 1}
        new = {t: n for t, n in new.items() if n not in twice}
        if not new:
            break
        known.update(new)
        added += len(new)
    say('corpus: %d tokens added' % added)
    return added, bigrams


class Analysis(object):
    def __init__(self, bc):
        self.bc = bc
        self.sites = hidden_sites(bc)
        op, b2, arg = bc.op, bc.b2, bc.arg
        self.starts = [k for k in range(bc.n) if op[k] == FUNCTION]
        self.fname = {k: bc.fname(arg[k]) for k in self.starts}
        self.start_of = {v: k for k, v in self.fname.items()}
        self.fparams = {}
        for k in self.starts:
            ps = []
            j = k + 1
            while op[j] == FUNCARG:
                ps.append((b2[j], arg[j]))
                j += 1
            self.fparams[k] = ps
        self.gcode = {}
        for k in range(bc.n):
            if op[k] in (GLOBAL, CONSTANT):
                self.gcode[arg[k]] = b2[k]
        self.in_expr = set()
        cond = collections.defaultdict(list)
        for k in range(bc.n):
            if op[k] in (JIT, JIF):
                cond[arg[k]].append(k)
        for k in range(1, bc.n - 2):
            if (op[k] == LABEL and op[k - 1] == JUMP and op[k + 1] == LIT and bc.b1[k + 1] == 8
                    and op[k + 2] == LABEL and arg[k - 1] == arg[k + 2]):
                self.in_expr.update((k - 1, k, k + 2))
                self.in_expr.update(cond.get(arg[k], ()))
        self.popn = {}
        for t, ks in self.sites.items():
            c = collections.Counter(b2[k + 1] if op[k + 1] == POPN else -1 for k in ks)
            self.popn[t] = c

    def hidden_in(self, start, end):
        bc = self.bc
        for k in range(start, end):
            if bc.op[k] == HIDDEN and bc.b0[k] == 0 and bc.b1[k] == 0 and bc.b2[k] == 0:
                yield k

    def caller(self, k):
        return self.starts[bisect.bisect_right(self.starts, k) - 1]

    def is_jass(self, t):
        return any(x >= 0 for x in self.popn[t])

    def simulate(self, arity, ret_code):
        bc = self.bc
        op, b0, b1, b2, arg = bc.op, bc.b0, bc.b1, bc.b2, bc.arg
        in_expr = self.in_expr
        args = collections.defaultdict(list)
        equations = collections.defaultdict(collections.Counter)
        dest = collections.defaultdict(list)
        assign = collections.defaultdict(list)
        for s in self.starts:
            k = s + 1
            local = {}
            for code, a in self.fparams[s]:
                local[a] = code
                k += 1
            stack = []
            reg = {}
            pend = []
            while op[k] != ENDFUNCTION:
                o = op[k]
                if o == LOCAL:
                    local[arg[k]] = b2[k]
                elif o == LIT:
                    reg[b2[k]] = ('line', b1[k])
                elif o == MOVRV or o == MOVRA:
                    a = arg[k]
                    if o == MOVRA:
                        idx = reg.get(b1[k])
                        if idx is not None and idx[0] == 'r':
                            dest[idx[1]].append(('c', 4))
                    if a in local:
                        code, key = local[a], (s, a)
                    else:
                        code, key = self.gcode.get(a, b1[k] if o == MOVRV else b0[k]), a
                    reg[b2[k]] = ('v', key, code - 5 if code >= 9 else code)
                elif o == MOVRCODE:
                    reg[b2[k]] = ('line', 3)
                elif o == MOVRR:
                    reg[b2[k]] = reg.get(b1[k], ('line', -1))
                elif o == PUSH:
                    stack.append(reg.get(b2[k], ('line', -1)))
                elif o == POP:
                    reg[b2[k]] = stack.pop() if stack else ('line', -1)
                elif o == I2R:
                    reg[b2[k]] = ('line', 5)
                elif o in (24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35):
                    x = reg.get(b1[k], ('line', -1))
                    y = reg.get(b0[k], ('line', -1))
                    cx, cy = _code(x, ret_code), _code(y, ret_code)
                    for p, q in ((x, cy), (y, cx)):
                        if p[0] == 'r' and q not in (-1, 0):
                            dest[p[1]].append(('c', 8 if o in (24, 25) else q))
                    if o <= 31:
                        reg[b2[k]] = ('line', 8)
                    else:
                        reg[b2[k]] = ('line', 5 if 5 in (cx, cy) else cx)
                elif o == 38:
                    src = reg.get(b2[k])
                    if src is not None and src[0] == 'r':
                        dest[src[1]].append(('c', 8))
                    reg[b2[k]] = ('line', 8)
                elif o == 37:
                    src = reg.get(b2[k], ('line', -1))
                    if src[0] == 'r':
                        dest[src[1]].append(('n',))
                    reg[b2[k]] = ('line', _code(src, ret_code))
                elif o == POPN:
                    del stack[max(0, len(stack) - b2[k]):]
                elif o == MOVVR or o == MOVAR:
                    a = arg[k]
                    key = (s, a) if a in local else a
                    if o == MOVAR:
                        idx = reg.get(b2[k])
                        if idx is not None and idx[0] == 'r':
                            dest[idx[1]].append(('c', 4))
                        src = reg.get(b1[k])
                    else:
                        src = reg.get(b2[k])
                    if src is not None:
                        assign[key].append(src)
                        if src[0] == 'r':
                            code = local.get(a, self.gcode.get(a, 0))
                            dest[src[1]].append(('v', key, code - 5 if code >= 9 else code, k))
                elif o in (JIT, JIF):
                    src = reg.get(b2[k])
                    if src is not None and src[0] == 'r':
                        dest[src[1]].append(('b',))
                elif o == HIDDEN and b0[k] == 0 and b1[k] == 0 and b2[k] == 0:
                    t = arg[k] & 0xFFFFFFFF
                    a = arity.get(t)
                    if a is not None:
                        if a <= len(stack):
                            if not pend:
                                args[t].append((s, stack[len(stack) - a:]))
                            if op[k + 1] != POPN:
                                del stack[len(stack) - a:]
                    else:
                        pend.append((t, len(stack), list(stack)))
                    reg[0] = ('r', t)
                if o == RET and op[k - 1] == MOVRR and b2[k - 1] == 0:
                    src = reg.get(0)
                    if src is not None and src[0] == 'r' and b2[s] not in (0,):
                        dest[src[1]].append(('c', b2[s]))
                if o in ANCHORS or (o in (JIT, JIF, JUMP, LABEL) and k not in in_expr):
                    if pend:
                        excess = len(stack)
                        equations[tuple(sorted(p[0] for p in pend))][excess] += 1
                        if len(pend) == 1:
                            t, depth, snap = pend[0]
                            if 0 <= excess <= depth:
                                args[t].append((s, snap[depth - excess:]))
                    stack, pend = [], []
                k += 1
        return args, equations, dest, assign


def _code(src, ret_code):
    if src[0] == 'line':
        return src[1]
    if src[0] == 'v':
        return src[2]
    return ret_code.get(src[1], -1)


def resolve(bc, texts, log=None, holdout=None, scripts=()):
    say = log or (lambda *a: None)
    sig = Signatures(texts)
    an = Analysis(bc)
    pairs, conflicts = reference_pairs(bc, texts)
    names = set(bc.name_list)
    res = {t: name for t, (_op, name) in pairs.items() if not holdout or t not in holdout}
    say('reference: %d tokens (%d conflicting)' % (len(res), len(conflicts)))
    bigrams = collections.Counter()
    if scripts:
        _n, bigrams = corpus_pairs(bc, texts[:2], scripts, res, log=say)
    by_context = {}

    def full_sig(name):
        if name in sig.natives:
            return sig.natives[name]
        if name in sig.functions:
            return sig.functions[name]
        s = an.start_of.get(name)
        if s is None:
            return None
        ret = {0: 'nothing', 3: 'code', 4: 'integer', 5: 'real', 6: 'string', 7: 'handle', 8: 'boolean'}.get(
            an.bc.b2[s], 'handle')
        return [('p', (s, a), c) for c, a in an.fparams[s]], ret

    arity, ret_code = {}, {}

    def learn(t, name):
        fs = full_sig(name)
        if fs:
            arity[t] = len(fs[0])
            ret_code[t] = code_of(fs[1])

    for t, name in res.items():
        learn(t, name)
    for t in an.sites:
        if t not in arity:
            v = [x for x in an.popn[t] if x >= 0]
            if v:
                arity[t] = v[0]
    pool_n = [n for n in sig.natives if n in names]
    pool_j = [n for n in an.start_of]
    neighbours = collections.defaultdict(list)
    for s_i, s in enumerate(an.starts):
        end = an.starts[s_i + 1] if s_i + 1 < len(an.starts) else bc.n
        ks = [k for k in an.hidden_in(s, end)]
        for i, k in enumerate(ks):
            t = bc.arg[k] & 0xFFFFFFFF
            neighbours[t].append((bc.arg[ks[i - 1]] & 0xFFFFFFFF if i else None,
                                  bc.arg[ks[i + 1]] & 0xFFFFFFFF if i + 1 < len(ks) else None))
    options = {}
    for round_ in range(60):
        args, equations, dest, assign = an.simulate(arity, ret_code)
        _solve_arities(equations, arity, options)
        lo, hi = {}, {}
        for key, srcs in assign.items():
            for src in srcs:
                if src[0] == 'r' and src[1] in res:
                    fs = full_sig(res[src[1]])
                    if fs and isinstance(fs[1], str) and code_of(fs[1]) == 7:
                        lo[key] = sig.join(lo.get(key), fs[1])
        for t, sites in args.items():
            if t not in res:
                continue
            fs = full_sig(res[t])
            if not fs:
                continue
            for _s, srcs in sites:
                if len(srcs) != len(fs[0]):
                    continue
                for src, p in zip(srcs, fs[0]):
                    if src[0] == 'v' and isinstance(p, str) and code_of(p) == 7:
                        h = hi.get(src[1])
                        if h is None or sig.is_sub(p, h):
                            hi[src[1]] = p
                    elif src[0] == 'r' and src[1] not in res:
                        if isinstance(p, str):
                            dest[src[1]].append(('p', p))
                        else:
                            dest[src[1]].append(('c', p[2]))
        used = set(dest)
        for _t, sites_ in args.items():
            for _s, srcs in sites_:
                for src in srcs:
                    if src[0] == 'r':
                        used.add(src[1])
        before = (len(res), len(arity))
        taken = set(res.values())
        open_ = [t for t in an.sites if t not in res]
        cands = {}
        for t in open_:
            jass = an.is_jass(t)
            a = arity.get(t)
            pool = pool_j if jass else (pool_n + ([n for n in pool_j] if a in (0, None) else []))
            callers = [an.caller(k) for k in an.sites[t]]
            last_caller = max(callers)
            out = []
            for name in pool:
                if name in taken:
                    continue
                fs = full_sig(name)
                if fs is None:
                    continue
                ps, rt = fs
                if a is not None and len(ps) != a:
                    continue
                if name in an.start_of and an.start_of[name] < last_caller:
                    continue
                if not _fits(sig, ps, rt, t, args.get(t, ()), dest.get(t, ()), lo, hi, res, full_sig):
                    continue
                if t not in used and len(an.sites[t]) >= 3 and rt != 'nothing' and PURE.match(name):
                    continue
                out.append(name)
            cands[t] = out
            if a is None and out:
                arities = set(len(full_sig(n)[0]) for n in out)
                options[t] = set(arities)
                if len(arities) == 1:
                    arity[t] = arities.pop()
        changed = True
        while changed:
            changed = False
            taken = set(res.values())
            for t, cs in cands.items():
                if t in res:
                    continue
                cs = [c for c in cs if c not in taken]
                cands[t] = cs
                if len(cs) == 1:
                    res[t] = cs[0]
                    taken.add(cs[0])
                    learn(t, cs[0])
                    changed = True
        say('round %d: %d resolved, %d arities' % (round_, len(res), len(arity)))
        if (len(res), len(arity)) == before and round_ > 1:
            picked = _by_context(cands, res, neighbours, bigrams)
            if not picked:
                break
            for t, name in picked.items():
                res[t] = name
                by_context[t] = name
                learn(t, name)
            say('context: %d picked' % len(picked))
    open_ = {t: cands.get(t, []) for t in an.sites if t not in res}

    def check(t, name):
        fs = full_sig(name)
        if fs is None:
            return 'no signature'
        if arity.get(t) is not None and len(fs[0]) != arity[t]:
            return 'arity %d, the calls take %d' % (len(fs[0]), arity[t])
        last = max(an.caller(k) for k in an.sites[t])
        if name in an.start_of and an.start_of[name] < last:
            return 'defined at %d, called from %s at %d' % (an.start_of[name], an.fname[last], last)
        for s, srcs in args.get(t, ()):
            if len(srcs) != len(fs[0]):
                return 'a site in %s pushes %d' % (an.fname[s], len(srcs))
            for i, (src, p) in enumerate(zip(srcs, fs[0])):
                if not _arg_fits(sig, src, p, lo, hi, res, full_sig):
                    return 'argument %d in %s: %r against %r (lo %r, hi %r)' % (
                        i, an.fname[s], src, p, lo.get(src[1]) if src[0] == 'v' else None,
                        hi.get(src[1]) if src[0] == 'v' else None)
        if not _fits(sig, fs[0], fs[1], t, (), dest.get(t, ()), lo, hi, res, full_sig):
            return 'the result: %r against %r' % (fs[1], collections.Counter(
                d[:1] + d[2:3] for d in dest.get(t, ())).most_common(6))
        return 'fits' + (' (taken by another token)' if name in set(res.values()) else '')

    report = {
        'check': check,
        'arity': arity,
        'analysis': an,
        'by_context': by_context,
        'tokens': len(an.sites),
        'reference': len(pairs),
        'resolved': len(res),
        'open': len(open_),
        'calls': sum(len(v) for v in an.sites.values()),
        'open_calls': sum(len(an.sites[t]) for t in open_),
        'candidates': open_,
        'conflicts': conflicts,
    }
    return res, report


CONTEXT_MIN, CONTEXT_RATIO, CONTEXT_SITES = 50, 10, 10


def _by_context(cands, res, neighbours, bigrams):
    if not bigrams:
        return {}
    best = {}
    for t, cs in cands.items():
        if t in res or len(cs) < 2 or len(neighbours.get(t, ())) < CONTEXT_SITES:
            continue
        score = collections.Counter()
        for prev, nxt in neighbours.get(t, ()):
            p = res.get(prev) if prev is not None else None
            n = res.get(nxt) if nxt is not None else None
            for c in cs:
                if p:
                    score[c] += bigrams.get((p, c), 0)
                if n:
                    score[c] += bigrams.get((c, n), 0)
        if not score:
            continue
        top = score.most_common(2)
        first = top[0][1]
        second = top[1][1] if len(top) > 1 else 0
        if first >= CONTEXT_MIN and first >= CONTEXT_RATIO * max(second, 1):
            best[t] = (top[0][0], first)
    by_name = collections.defaultdict(list)
    for t, (name, sc) in best.items():
        by_name[name].append((sc, t))
    return {max(v)[1]: name for name, v in by_name.items() if len(v) == 1 or max(v)[0] >= 4 * sorted(v)[-2][0]}


def _solve_arities(equations, arity, options=None):
    while True:
        votes = collections.defaultdict(collections.Counter)
        for toks, excesses in equations.items():
            unknown = [t for t in toks if t not in arity]
            if not unknown or len(set(unknown)) != 1:
                continue
            known = sum(arity[t] for t in toks if t in arity)
            for ex, cnt in excesses.items():
                rest = ex - known
                if rest >= 0 and rest % len(unknown) == 0:
                    votes[unknown[0]][rest // len(unknown)] += cnt
                else:
                    votes[unknown[0]][-1] += cnt
        added = 0
        for t, c in votes.items():
            a, cnt = c.most_common(1)[0]
            if a >= 0 and cnt * 4 >= 3 * sum(c.values()):
                arity[t] = a
                added += 1
        if not added and options:
            added = _solve_by_options(equations, arity, options)
        if not added:
            return


def _solve_by_options(equations, arity, options):
    import itertools
    found = collections.defaultdict(collections.Counter)
    for toks, excesses in equations.items():
        unknown = sorted(set(t for t in toks if t not in arity))
        if len(unknown) < 2 or len(excesses) != 1:
            continue
        sets = [sorted(options.get(t, range(13))) for t in unknown]
        size = 1
        for s in sets:
            size *= len(s)
        if size > 20000:
            continue
        mult = [toks.count(t) for t in unknown]
        known = sum(arity[t] for t in toks if t in arity)
        ex = next(iter(excesses)) - known
        fits = [combo for combo in itertools.product(*sets) if sum(m * a for m, a in zip(mult, combo)) == ex]
        if len(fits) == 1:
            for t, a in zip(unknown, fits[0]):
                found[t][a] += 1
    added = 0
    for t, c in found.items():
        if len(c) == 1:
            arity[t] = next(iter(c))
            added += 1
    return added


def _fits(sig, ps, rt, t, sites, dests, lo, hi, res, full_sig):
    rc = code_of(rt) if isinstance(rt, str) else 7
    for _s, srcs in sites:
        if len(srcs) != len(ps):
            return False
        for src, p in zip(srcs, ps):
            if not _arg_fits(sig, src, p, lo, hi, res, full_sig):
                return False
    for d in dests:
        if d[0] == 'b':
            if rc != 8:
                return False
        elif d[0] == 'n':
            if rc not in (4, 5):
                return False
        elif d[0] == 'c':
            c = d[1]
            if c == 2:
                if rc not in (3, 6, 7):
                    return False
            elif c != rc and not (c in (4, 5) and rc in (4, 5)):
                return False
        elif d[0] == 'p':
            if rc != code_of(d[1]) and not (rc == 4 and code_of(d[1]) == 5):
                return False
            if rc == 7 and isinstance(rt, str) and rt != 'handle' and not sig.is_sub(rt, d[1]):
                return False
        else:
            code = d[2]
            if rc == 0:
                return False
            if code != rc and not (code == 5 and rc == 4) and code not in (0, -1):
                return False
            if rc == 7 and isinstance(rt, str) and d[1] in hi and not sig.is_sub(rt, hi[d[1]]):
                if not sig.comparable(rt, hi[d[1]]):
                    return False
    return True


def _arg_fits(sig, src, p, lo, hi, res, full_sig):
    if isinstance(p, tuple):
        pc, ptype = p[2], hi.get(p[1])
    else:
        pc, ptype = code_of(p), (p if code_of(p) == 7 else None)
    if src[0] == 'line':
        c = src[1]
        if c == -1 or c == pc:
            return True
        return c == 2 and pc in (3, 6, 7)
    if src[0] == 'v':
        if src[2] != pc and not (src[2] == 4 and pc == 5 and False):
            return False
        if ptype and pc == 7:
            low = lo.get(src[1])
            if low and not sig.is_sub(low, ptype):
                return False
            high = hi.get(src[1])
            if high and not sig.comparable(high, ptype):
                return False
        return True
    other = res.get(src[1])
    if other is None:
        return True
    fs = full_sig(other)
    if not fs:
        return True
    r = fs[1]
    rc = code_of(r) if isinstance(r, str) else 7
    if rc != pc:
        return False
    if ptype and pc == 7 and isinstance(r, str) and r != 'handle':
        return sig.is_sub(r, ptype)
    return True


def restore(code, names, mapping, functions):
    first = {}
    for i, n in enumerate(names):
        first.setdefault(n, i + 1)
    out = bytearray(code)
    for k in range(0, len(code) - 7, 8):
        if code[k:k + 4] != b'\x00\x00\x00\x24':
            continue
        t = struct.unpack_from('<I', code, k + 4)[0]
        name = mapping.get(t)
        if name is None or name not in first:
            continue
        out[k + 3] = CALLJ if name in functions else CALLN
        struct.pack_into('<I', out, k + 4, first[name])
    return bytes(out)


def reference_texts(common, blizzard, shell):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kk_natives.j')
    extra = open(path, 'rb').read().decode('utf-8', 'surrogateescape') if os.path.isfile(path) else ''
    if isinstance(shell, bytes):
        shell = shell.decode('utf-8', 'surrogateescape')
    return [common, blizzard, shell or '', extra]

