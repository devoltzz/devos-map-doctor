# Turns the bytecode of a compiled map script (KKWE, j2b) back into JASS.
import array
import collections
import copy
import os
import re
import struct
import sys

from doctor.script import kkwe
from doctor.script import kkwe_compile as KC

HERE = os.path.dirname(os.path.abspath(__file__))

DEFAULT_NATIVES = os.path.join(HERE, 'kk_natives.j')

LIT, MOVRR, MOVRV, MOVRCODE, MOVRA, MOVVR, MOVAR = 12, 13, 14, 15, 16, 17, 18
PUSH, POP, CALLN, CALLJ, I2R, NEG, NOT, RET, LABEL, JIT, JIF, JUMP = 19, 20, 21, 22, 23, 37, 38, 39, 40, 41, 42, 43
FUNCTION, ENDFUNCTION, LOCAL, GLOBAL, CONSTANT, FUNCARG, POPN = 3, 4, 5, 6, 7, 8, 11
EXTENDS_OP, TYPE_OP = 9, 10
BINOP = {26: '==', 27: '!=', 28: '<=', 29: '>=', 30: '<', 31: '>', 32: '+', 33: '-', 34: '*', 35: '/'}
BASIC = {0: 'nothing', 3: 'code', 4: 'integer', 5: 'real', 6: 'string', 7: 'handle', 8: 'boolean'}


class DecompileError(Exception):
    pass


class NotExpression(Exception):
    pass


class Reference(object):
    def __init__(self, common, blizzard, extra_natives, map_own=''):
        self.parent = {'handle': None}
        self.natives = {}
        self.funcs = {}
        self.globals_block = {}
        for body_text in (common, blizzard):
            for it in KC.analyze(body_text):
                if it[0] == 'type':
                    self.parent[it[1]] = it[2]
                elif it[0] == 'native':
                    self.natives[it[1]] = (it[2], it[3])
                elif it[0] == 'function':
                    self.funcs[it[1]] = (it[2], it[3])
                elif it[0] == 'globals':
                    for _c, t, is_array, n, _e in it[1]:
                        self.globals_block[n] = (t, is_array)
        self.extra = {}
        self.extra_text = {}
        self.extra_types = collections.OrderedDict()
        self.bytecode_type_list = []
        for body_text, own in ((map_own, True), (extra_natives, False)):
            for ln in body_text.splitlines():
                s = ln.strip()
                if s.startswith('type '):
                    it = KC.analyze(s)[0]
                    if it[1] not in self.parent:
                        self.parent[it[1]] = it[2]
                        self.extra_types[it[1]] = it[2]
                    continue
                if s.startswith('native ') or s.startswith('constant native '):
                    it = KC.analyze(s)[0]
                    signature = (it[2], it[3])
                    if it[1] in self.extra:
                        continue
                    if own and self.natives.get(it[1]) == signature:
                        continue
                    if own or it[1] not in self.natives:
                        self.extra[it[1]] = signature
                        self.extra_text[it[1]] = ' '.join(s.split()) if own else s

    def bytecode_types(self, bc):
        for k in [i for i, op in enumerate(bc.op) if op == EXTENDS_OP]:
            if k + 1 < bc.n and bc.op[k + 1] == TYPE_OP:
                fname, parent = bc.fname(bc.arg[k + 1]), bc.fname(bc.arg[k])
                if fname not in self.parent or fname in self.extra_types:
                    self.parent.setdefault(fname, parent)
                    self.extra_types[fname] = self.parent[fname]
                    if fname not in self.bytecode_type_list:
                        self.bytecode_type_list.append(fname)

    def type_lines(self, body_text):
        wanted = list(self.bytecode_type_list) + [t for t in self.extra_types if t not in self.bytecode_type_list and
                                             re.search(r'\b%s\b' % re.escape(t), body_text)]
        output, seen_types = [], set()

        def place(t):
            if t in seen_types or t not in self.extra_types:
                return
            place(self.extra_types[t])
            seen_types.add(t)
            output.append('type %s extends %s' % (t, self.extra_types[t]))
        for t in wanted:
            place(t)
        return output

    def native(self, fname):
        if fname in self.extra:
            return self.extra[fname]
        if fname in self.natives:
            return self.natives[fname]
        raise DecompileError('the signature of the native %s is not known (it is not in kk_natives.j)' % fname)

    def from_game(self, fname):
        return fname in self.natives and fname not in self.extra

    def signature(self, fname):
        if fname in self.extra:
            return self.extra[fname]
        if fname in self.funcs:
            return self.funcs[fname]
        return self.native(fname)

    def is_handle(self, t):
        return t in self.parent

    def ancestors(self, t):
        out = []
        while t is not None:
            out.append(t)
            t = self.parent.get(t)
        return out

    def sub(self, a, b):
        return b in self.ancestors(a)

    def lub(self, a, b):
        if a is None:
            return b
        if b is None:
            return a
        anc = self.ancestors(a)
        for t in self.ancestors(b):
            if t in anc:
                return t
        return 'handle'

    def glb(self, a, b):
        if a is None:
            return b
        if b is None:
            return a
        if self.sub(a, b):
            return a
        if self.sub(b, a):
            return b
        return None


class Function(object):
    def __init__(self, fname, ret, params, k):
        self.fname = fname
        self.ret = ret
        self.params = params
        self.body = []
        self.local_vars = {}
        self.k = k
        self.of_globals = False


class Decompiler(object):
    def __init__(self, bc, ref):
        self.bc = bc
        self.ref = ref
        op, arg = bc.op, bc.arg
        self.label_pos = {}
        self.jumps = collections.defaultdict(list)
        for k in range(bc.n):
            o = op[k]
            if o == LABEL:
                self.label_pos[arg[k]] = k
            elif o == JUMP:
                self.jumps[arg[k]].append(k)
        self.arity = {}
        k = 0
        while k < bc.n:
            if op[k] == FUNCTION:
                n = 0
                while op[k + 1 + n] == FUNCARG:
                    n += 1
                self.arity[bc.fname(arg[k])] = n
            k += 1

    def literal(self, k):
        b1, a = self.bc.b1[k], self.bc.arg[k]
        if b1 == 4:
            return ('int', a)
        if b1 == 5:
            return ('realbits', a)
        if b1 == 6:
            return ('str', self.bc.fname(a)) if a else ('null', 6)
        if b1 == 8:
            return ('bool', a)
        if b1 in (2, 3, 7):
            if a:
                raise DecompileError('instruction %d: literal of type %d with value %d' % (k, b1, a))
            return ('null', b1)
        raise DecompileError('instruction %d: literal of type %d' % (k, b1))

    def function(self, k):
        bc = self.bc
        if bc.op[k] != FUNCTION:
            raise DecompileError('instruction %d is not FUNCTION' % k)
        fname = bc.fname(bc.arg[k])
        params = []
        j = k + 1
        while bc.op[j] == FUNCARG:
            params.append((bc.b2[j], bc.fname(bc.arg[j])))
            j += 1
        f = Function(fname, bc.b2[k], params, k)
        end_pos = j
        while bc.op[end_pos] != ENDFUNCTION:
            end_pos += 1
        f.of_globals = fname == '<init>' or (not params and j < end_pos and bc.op[j] in (GLOBAL, CONSTANT))
        if f.of_globals:
            if bc.op[end_pos - 1] != RET:
                raise DecompileError('%s at %d: unexpected end' % (fname, k))
            body_end = end_pos - 1
        else:
            if not (
                bc.op[end_pos - 1] == RET
                and bc.op[end_pos - 2] == LIT
                and bc.b1[end_pos - 2] == 0
                and bc.b2[end_pos - 2] == 0
            ):
                raise DecompileError('%s at %d: without the standard end (LITERAL nothing; RETURN)' % (fname, k))
            body_end = end_pos - 2
        self.f = f
        self.regs = {}
        self.stack = []
        self.pend = collections.OrderedDict()
        self.execute(j, body_end, f.body, None, False)
        self.flush(f.body)
        if self.stack:
            raise DecompileError('%s: the stack ended with %d items' % (fname, len(self.stack)))
        return f, end_pos + 1

    def read_data(self, r):
        if r not in self.regs:
            raise DecompileError('%s: register r%02x read without a value' % (self.f.fname, r))
        self.pend.pop(r, None)
        return self.regs[r]

    def write(self, r, e, call_expr=False, dest=None, expr_mode=False):
        if r in self.pend:
            if dest is None or expr_mode:
                raise NotExpression()
            while self.pend:
                rr, (ee, ch) = self.pend.popitem(last=False)
                dest.append(('call', ee[1], ee[2]) if ch else ('if', [(ee, [])], None))
                if rr == r:
                    break
        self.regs[r] = e
        self.pend[r] = (e, call_expr)

    def flush(self, body, expr_mode=False):
        if self.pend and expr_mode:
            raise NotExpression()
        while self.pend:
            _r, (e, ch) = self.pend.popitem(last=False)
            body.append(('call', e[1], e[2]) if ch else ('if', [(e, [])], None))

    def is_andor(self, k):
        bc = self.bc
        L = bc.arg[k]
        p = self.label_pos.get(L)
        if p is None or p <= k + 1 or p + 2 >= bc.n:
            return None
        if bc.op[p - 1] != JUMP or bc.op[p + 1] != LIT or bc.b1[p + 1] != 8 or bc.op[p + 2] != LABEL:
            return None
        if bc.arg[p + 2] != bc.arg[p - 1]:
            return None
        v = bc.arg[p + 1]
        if (bc.op[k] == JIF and v != 0) or (bc.op[k] == JIT and v != 1):
            return None
        return p

    def execute(self, k, end_pos, body, loop_exit, expr_mode):
        bc = self.bc
        op, b0s, b1s, b2s, args = bc.op, bc.b0, bc.b1, bc.b2, bc.arg
        f = self.f
        while k < end_pos:
            o = op[k]
            b0, b1, b2, a = b0s[k], b1s[k], b2s[k], args[k]
            if o == LIT:
                self.write(b2, self.literal(k), dest=body, expr_mode=expr_mode)
            elif o == MOVRV:
                self.write(b2, ('var', bc.fname(a)), dest=body, expr_mode=expr_mode)
            elif o == MOVRA:
                i = self.read_data(b1)
                self.write(b2, ('idx', bc.fname(a), i), dest=body, expr_mode=expr_mode)
            elif o == MOVRCODE:
                self.write(b2, ('code', bc.fname(a)), dest=body, expr_mode=expr_mode)
            elif o == PUSH:
                self.stack.append(self.read_data(b2))
            elif o == POP:
                if not self.stack:
                    raise DecompileError('%s at %d: POP with an empty stack' % (f.fname, k))
                self.write(b2, self.stack.pop(), dest=body, expr_mode=expr_mode)
            elif o in BINOP:
                left = self.read_data(b1)
                right = self.read_data(b0)
                self.write(b2, ('bin', BINOP[o], left, right), dest=body, expr_mode=expr_mode)
            elif o == I2R:
                if not stray_i2r(bc, k):
                    self.write(b2, self.read_data(b2), dest=body, expr_mode=expr_mode)
            elif o == NEG:
                self.write(b2, ('neg', self.read_data(b2)), dest=body, expr_mode=expr_mode)
            elif o == NOT:
                self.write(b2, ('not', self.read_data(b2)), dest=body, expr_mode=expr_mode)
            elif o == CALLN or o == CALLJ:
                fname = bc.fname(a)
                if o == CALLN:
                    n = len(self.ref.native(fname)[0])
                else:
                    n = 0
                    if k + 1 < end_pos and op[k + 1] == POPN:
                        n = b2s[k + 1]
                    expected_len = self.arity.get(fname)
                    if expected_len is None or expected_len != n:
                        raise DecompileError('%s at %d: CALLJASS %s with %d arguments, the function has %s'
                                             % (f.fname, k, fname, n, expected_len))
                if len(self.stack) < n:
                    raise DecompileError('%s at %d: %s takes %d arguments, the stack has %d'
                                         % (f.fname, k, fname, n, len(self.stack)))
                arguments = self.stack[len(self.stack) - n:] if n else []
                del self.stack[len(self.stack) - n:]
                self.write(0, ('call', fname, arguments), call_expr=True, dest=body, expr_mode=expr_mode)
                if o == CALLJ and n:
                    k += 1
            elif o == MOVVR:
                e = self.read_data(b2)
                if expr_mode:
                    raise NotExpression()
                self.flush(body)
                fname = bc.fname(a)
                if body and body[-1][0] in ('local', 'global') and body[-1][2] == fname and body[-1][4] is None:
                    body[-1] = body[-1][:4] + (e,)
                else:
                    body.append(('set', fname, e))
            elif o == MOVAR:
                v = self.read_data(b1)
                i = self.read_data(b2)
                if expr_mode:
                    raise NotExpression()
                self.flush(body)
                body.append(('set_array', bc.fname(a), i, v))
            elif o == MOVRR:
                if b2 != 0 or k + 1 >= end_pos or op[k + 1] != RET:
                    raise DecompileError('%s at %d: MOVRR outside a `return`' % (f.fname, k))
                e = self.read_data(b1)
                if expr_mode:
                    raise NotExpression()
                self.flush(body)
                body.append(('return', e))
                k += 1
            elif o == RET:
                if expr_mode:
                    raise NotExpression()
                self.flush(body)
                body.append(('return', None))
            elif o == LOCAL or o == GLOBAL or o == CONSTANT:
                if expr_mode:
                    raise NotExpression()
                self.flush(body)
                fname = bc.fname(a)
                if o == LOCAL:
                    f.local_vars[fname] = b2
                    body.append(('local', b2, fname, False, None))
                else:
                    body.append(('global', b2, fname, o == CONSTANT, None))
            elif o == JIF or o == JIT:
                p = self.is_andor(k)
                done = False
                if p is not None and any(r != b2 for r in self.pend):
                    if expr_mode:
                        raise NotExpression()
                    cond = self.pend.pop(b2)
                    self.flush(body)
                    self.pend[b2] = cond
                if p is not None:
                    saved = (dict(self.regs), list(self.stack), collections.OrderedDict(self.pend))
                    left = self.read_data(b2)
                    try:
                        self.execute(k + 1, p - 1, body, loop_exit, True)
                        rr = b2s[p + 1]
                        if rr not in self.pend or list(self.pend)[-1] != rr:
                            raise NotExpression()
                        right = self.read_data(rr)
                        self.write(rr, ('bin', 'and' if o == JIF else 'or', left, right), dest=body,
                                   expr_mode=expr_mode)
                        k = p + 3
                        done = True
                    except NotExpression:
                        self.regs, self.stack, self.pend = saved
                if done:
                    continue
                if expr_mode:
                    raise NotExpression()
                c = self.read_data(b2)
                self.flush(body)
                if o == JIT:
                    if a != loop_exit:
                        raise DecompileError('%s at %d: JUMPIFTRUE to L%d outside a loop/and/or' % (f.fname, k, a))
                    body.append(('exitwhen', c))
                else:
                    p = self.label_pos.get(a)
                    if p is None or p <= k or op[p - 1] != JUMP:
                        raise DecompileError('%s at %d: `if` without the JUMP before the label L%d' % (f.fname, k, a))
                    lb = args[p - 1]
                    q = self.label_pos.get(lb)
                    if q is None or q < p:
                        raise DecompileError('%s at %d: `if` without the end label L%d' % (f.fname, k, lb))
                    then_body, else_body = [], []
                    self.execute(k + 1, p - 1, then_body, loop_exit, False)
                    self.flush(then_body)
                    self.execute(p + 1, q, else_body, loop_exit, False)
                    self.flush(else_body)
                    if len(else_body) == 1 and else_body[0][0] == 'if':
                        body.append(('if', [(c, then_body)] + else_body[0][1], else_body[0][2]))
                    else:
                        body.append(('if', [(c, then_body)], else_body or None))
                    k = q + 1
                    continue
            elif o == LABEL:
                if expr_mode:
                    raise NotExpression()
                self.flush(body)
                closings = self.jumps.get(a, [])
                if len(closings) != 1 or closings[0] <= k or op[closings[0] + 1] != LABEL:
                    raise DecompileError('%s at %d: loop L%d without its end' % (f.fname, k, a))
                j = closings[0]
                lb = args[j + 1]
                loop_body = []
                self.execute(k + 1, j, loop_body, lb, False)
                self.flush(loop_body)
                body.append(('loop', loop_body))
                k = j + 2
                continue
            else:
                raise DecompileError('%s at %d: unexpected instruction %s' % (f.fname, k, kkwe.OPS.get(o, o)))
            k += 1


ALLOCATING = (LIT, MOVRV, MOVRCODE, MOVRA, POP)
WITH_LABEL = (LABEL, JIT, JIF, JUMP)


def map_region(bc, ref):
    fs = bc.functions()
    begin = None
    real_one = False
    for k, fname in fs:
        if fname != '<init>':
            real_one = True
        elif real_one:
            begin = k
            break
    if begin is None:
        last_pos = None
        for k, fname in fs:
            if fname in ref.funcs:
                last_pos = k
            elif last_pos is not None and fname != '<init>':
                break
        if last_pos is None:
            raise DecompileError('the Blizzard.j functions are not in the bytecode')
        k = last_pos
        while bc.op[k] != ENDFUNCTION:
            k += 1
        begin = k + 1
    end_pos = bc.n
    while end_pos > 0 and bc.op[end_pos - 1] != 1:
        end_pos -= 1
    map_region.last_start = begin
    return begin, end_pos - 1


def _allocated(bc, segment):
    return [bc.b2[k] for k in range(segment[0], segment[1]) if bc.op[k] in ALLOCATING and bc.b2[k]]


def _reversed_functions(bc, ref):
    fs = bc.functions()
    bounds = [(k, fs[i + 1][0] if i + 1 < len(fs) else bc.n) for i, (k, _n) in enumerate(fs)]
    cut = len(fs)
    while cut > 0 and fs[cut - 1][1] in ref.funcs:
        cut -= 1
    map_path = bounds[:cut]
    if not map_path:
        raise DecompileError('the bytecode has no function of the map (only the Blizzard.j ones)')
    of_globals = [t for t in map_path if t[0] + 1 < t[1] and bc.op[t[0] + 1] in (GLOBAL, CONSTANT)]
    order = of_globals + [t for t in reversed(map_path) if t not in of_globals]
    before = next((a[-1] for a in (_allocated(bc, t) for t in bounds[cut:]) if a), None)
    after_diag = next((a[0] for a in (_allocated(bc, t) for t in order) if a), None)
    if before is not None and after_diag is not None and before % 255 + 1 != after_diag and of_globals:
        bliz_ini = next((a[0] for a in (_allocated(bc, t) for t in reversed(bounds[cut:])) if a), None)
        glob_end = next((a[-1] for a in (_allocated(bc, t) for t in reversed(of_globals)) if a), None)
        rest = next((a[0] for a in (_allocated(bc, t) for t in order if t not in of_globals) if a), None)
        if glob_end is not None and bliz_ini == glob_end % 255 + 1 and (rest is None or before % 255 + 1 == rest):
            after_diag = before % 255 + 1
    if before is not None and after_diag is not None and before % 255 + 1 != after_diag:
        raise DecompileError('the boundary between Blizzard.j and the map does not match: Blizzard.j ends at register '
                             '%d and the map (%s) starts at %d' % (before, bc.fname(bc.arg[order[0][0]]), after_diag))
    return order


BLOCK_ENDS = (LABEL, JIT, JIF, JUMP, RET, 4)


def stray_i2r(bc, k):
    return bc.op[k] == I2R and bc.b2[k] == 0 and k + 1 < bc.n and bc.op[k + 1] in BLOCK_ENDS


def map_functions(bc, ref):
    if bc.order == kkwe.REVERSE_ORDER:
        return _reversed_functions(bc, ref)
    begin, end_pos = map_region(bc, ref)
    segments = []
    k = begin
    while k < end_pos:
        if bc.op[k] != FUNCTION:
            raise DecompileError('instruction %d: expected FUNCTION, got %s' % (k, kkwe.OPS.get(bc.op[k])))
        j = k
        while bc.op[j] != ENDFUNCTION:
            j += 1
        segments.append((k, j + 1))
        k = j + 1
    return segments


def decompile(bc, ref):
    d = Decompiler(bc, ref)
    segments = map_functions(bc, ref)
    if not segments:
        raise DecompileError('the bytecode has no function of the map (only the Blizzard.j ones)')
    globals_block = []
    funcs = []
    for begin, _stop in segments:
        f, _next = d.function(begin)
        if f.of_globals:
            for c in f.body:
                if c[0] != 'global':
                    raise DecompileError('%s of the map with the statement %r' % (f.fname, c[0]))
                globals_block.append((c[1], c[2], c[3], c[4]))
        else:
            funcs.append(f)
    used_entries = []
    visited = set()
    for begin, end_pos in segments:
        for k in range(begin, end_pos):
            if bc.op[k] == CALLN:
                n = bc.fname(bc.arg[k])
                if n not in visited and not ref.from_game(n):
                    visited.add(n)
                    used_entries.append(n)
    return globals_block, funcs, used_entries, (min(t[0] for t in segments), max(t[1] for t in segments))


def is_hook(f):
    c = f.body
    if not c or c[0] != ('call', 'GetTriggeringTrigger', []):
        return False
    if len(c) == 1:
        return True
    return len(c) == 2 and c[1][0] == 'return' and (c[1][1] is None or c[1][1][0] in ('int', 'realbits', 'str', 'bool',
                                                                                     'null'))


def walk_expr(e, visit):
    visit(e)
    k = e[0]
    if k == 'idx':
        walk_expr(e[2], visit)
    elif k == 'call':
        for a in e[2]:
            walk_expr(a, visit)
    elif k in ('neg', 'not'):
        walk_expr(e[1], visit)
    elif k == 'bin':
        walk_expr(e[2], visit)
        walk_expr(e[3], visit)


def walk_cmds(cmds, visit_cmd):
    for c in cmds:
        visit_cmd(c)
        if c[0] == 'if':
            for _cond, body in c[1]:
                walk_cmds(body, visit_cmd)
            if c[2]:
                walk_cmds(c[2], visit_cmd)
        elif c[0] == 'loop':
            walk_cmds(c[1], visit_cmd)


class Inference(object):
    def __init__(self, ref, globals_block, funcs):
        self.ref = ref
        self.funcs = {f.fname: f for f in funcs}
        self.g_code = {n: c for c, n, _k, _e in globals_block}
        self.orig_t = collections.defaultdict(set)
        self.orig_n = collections.defaultdict(set)
        self.dst_t = collections.defaultdict(set)
        self.dst_n = collections.defaultdict(set)
        self.nodes = set()
        for c, n, _k, _e in globals_block:
            if c in (7, 12):
                self.nodes.add(('g', n))
        for f in funcs:
            for c, n in f.params:
                if c == 7:
                    self.nodes.add(('line', f.fname, n))
            for n, c in f.local_vars.items():
                if c in (7, 12):
                    self.nodes.add(('line', f.fname, n))
            if f.ret == 7:
                self.nodes.add(('r', f.fname))
        self.flows = []

    def expr_type(self, e, f):
        k = e[0]
        if k in ('var', 'idx'):
            n = e[1]
            if f is not None and ('line', f.fname, n) in self.nodes:
                return ('node', ('line', f.fname, n))
            if f is not None and (n in f.local_vars or n in dict((p[1], p[0]) for p in f.params)):
                return None
            if ('g', n) in self.nodes:
                return ('node', ('g', n))
            if n in self.g_code:
                return None
            if n in self.ref.globals_block:
                t = self.ref.globals_block[n][0]
                return ('t', t) if self.ref.is_handle(t) else None
            return None
        if k == 'call':
            n = e[1]
            if n in self.funcs:
                return ('node', ('r', n)) if ('r', n) in self.nodes else None
            t = self.ref.signature(n)[1]
            return ('t', t) if self.ref.is_handle(t) else None
        return None

    def var_target(self, n, f):
        if f is not None and ('line', f.fname, n) in self.nodes:
            return ('node', ('line', f.fname, n))
        if f is not None and (n in f.local_vars or n in dict((p[1], p[0]) for p in f.params)):
            return None
        if ('g', n) in self.nodes:
            return ('node', ('g', n))
        if n in self.g_code:
            return None
        if n in self.ref.globals_block:
            t = self.ref.globals_block[n][0]
            return ('t', t) if self.ref.is_handle(t) else None
        return None

    def flow(self, orig, dst, where):
        if orig is None or dst is None:
            return
        self.flows.append((orig, dst, where))
        if dst[0] == 'node':
            if orig[0] == 'node':
                self.orig_n[dst[1]].add(orig[1])
                self.dst_n[orig[1]].add(dst[1])
            else:
                self.orig_t[dst[1]].add(orig[1])
        elif orig[0] == 'node':
            self.dst_t[orig[1]].add(dst[1])

    def collect(self, globals_block):
        for _c, n, _k, e in globals_block:
            if e is not None:
                self.expr(e, None)
                self.flow(self.expr_type(e, None), self.var_target(n, None), 'global ' + n)
        for f in self.funcs.values():
            def visit(c, f=f):
                k = c[0]
                if k == 'local' and c[4] is not None:
                    self.expr(c[4], f)
                    self.flow(self.expr_type(c[4], f), self.var_target(c[2], f), f.fname)
                elif k == 'set':
                    self.expr(c[2], f)
                    self.flow(self.expr_type(c[2], f), self.var_target(c[1], f), f.fname)
                elif k == 'set_array':
                    self.expr(c[2], f)
                    self.expr(c[3], f)
                    self.flow(self.expr_type(c[3], f), self.var_target(c[1], f), f.fname)
                elif k == 'call':
                    self.expr(('call', c[1], c[2]), f)
                elif k == 'if':
                    for cond, _body in c[1]:
                        self.expr(cond, f)
                elif k == 'exitwhen':
                    self.expr(c[1], f)
                elif k == 'return' and c[1] is not None:
                    self.expr(c[1], f)
                    if ('r', f.fname) in self.nodes:
                        self.flow(self.expr_type(c[1], f), ('node', ('r', f.fname)), f.fname)
            walk_cmds(f.body, visit)

    def pin_hook_types(self, funcs):
        for f in funcs:
            if not is_hook(f) or f.fname not in self.ref.extra:
                continue
            params, ret = self.ref.extra[f.fname]
            if len(params) != len(f.params):
                continue
            for (c, pn), (t, _n) in zip(f.params, params):
                node = ('line', f.fname, pn)
                if c == 7 and node in self.nodes and self.ref.is_handle(t):
                    self.flow(('t', t), ('node', node), 'hook %s' % f.fname)
                    self.flow(('node', node), ('t', t), 'hook %s' % f.fname)
            if ('r', f.fname) in self.nodes and self.ref.is_handle(ret):
                self.flow(('t', ret), ('node', ('r', f.fname)), 'hook %s' % f.fname)
                self.flow(('node', ('r', f.fname)), ('t', ret), 'hook %s' % f.fname)

    def expr(self, e, f):
        def visit(x):
            if x[0] == 'call':
                n = x[1]
                if n in self.funcs:
                    g = self.funcs[n]
                    for (c, pn), a in zip(g.params, x[2]):
                        if c == 7:
                            self.flow(self.expr_type(a, f), ('node', ('line', n, pn)), 'arg %s' % n)
                else:
                    params = self.ref.signature(n)[0]
                    for (t, _pn), a in zip(params, x[2]):
                        if self.ref.is_handle(t):
                            self.flow(self.expr_type(a, f), ('t', t), 'arg %s' % n)
        walk_expr(e, visit)

    def resolve(self):
        ref = self.ref
        kind = {}
        while True:
            changed = True
            while changed:
                changed = False
                for node in self.nodes:
                    t = kind.get(node)
                    for x in self.orig_t.get(node, ()):
                        t = ref.lub(t, x)
                    for o in self.orig_n.get(node, ()):
                        if o in kind:
                            t = ref.lub(t, kind[o])
                    if t is not None and t != kind.get(node):
                        kind[node] = t
                        changed = True
            cand = {}
            without_type = sorted((node for node in self.nodes if node not in kind), key=repr)
            for node in without_type:
                t = None
                for x in sorted(self.dst_t.get(node, ())):
                    t = x if t is None else (ref.glb(t, x) or t)
                if t is not None:
                    cand[node] = t
            changed = True
            while changed:
                changed = False
                for node in without_type:
                    t = cand.get(node)
                    for d in sorted(self.dst_n.get(node, ()), key=repr):
                        td = kind.get(d) or cand.get(d)
                        if td is not None:
                            t = td if t is None else (ref.glb(t, td) or t)
                    if t is not None and t != cand.get(node):
                        cand[node] = t
                        changed = True
            new_ones = 0
            for node in without_type:
                if node in cand:
                    kind[node] = cand[node]
                    new_ones += 1
            if not new_ones:
                break
        for node in self.nodes:
            kind.setdefault(node, 'handle')
        self.kind = kind
        bad_ones = []
        for orig, dst, where in self.flows:
            a = kind[orig[1]] if orig[0] == 'node' else orig[1]
            b = kind[dst[1]] if dst[0] == 'node' else dst[1]
            if not ref.sub(a, b):
                bad_ones.append((where, orig, dst, a, b))
        self.bad_ones = bad_ones
        return kind


def real_text(bits):
    v = struct.unpack('<f', struct.pack('<i', bits))[0]
    for d in range(1, 80):
        s = '%.*f' % (d, v)
        if KC.f32_bits(s) == bits:
            return s
    raise DecompileError('real without a text: %08x' % (bits & 0xFFFFFFFF))


def int_text(v):
    b = struct.pack('>I', v & 0xFFFFFFFF)
    if v >= 0x01000000 and all(48 <= c <= 57 or 65 <= c <= 90 or 97 <= c <= 122 for c in b):
        return "'%s'" % b.decode('ascii')
    if v < 0 or v >= 0x10000000:
        return '0x%08X' % (v & 0xFFFFFFFF)
    return str(v)


def str_text(s):
    out = []
    for ch in s:
        if ch == '\\':
            out.append('\\\\')
        elif ch == '"':
            out.append('\\"')
        elif ch == '\n':
            out.append('\\n')
        elif ch == '\r':
            out.append('\\r')
        elif ch == '\t':
            out.append('\\t')
        else:
            out.append(ch)
    return '"' + ''.join(out) + '"'


LEVEL = {'and': 1, 'or': 1, '==': 2, '!=': 2, '<': 2, '>': 2, '<=': 2, '>=': 2, '+': 3, '-': 3, '*': 4, '/': 4}


def expr_text(e):
    k = e[0]
    if k == 'int':
        return int_text(e[1])
    if k == 'realbits':
        return real_text(e[1])
    if k == 'str':
        return str_text(e[1])
    if k == 'bool':
        return 'true' if e[1] else 'false'
    if k == 'null':
        return 'null'
    if k == 'var':
        return e[1]
    if k == 'idx':
        return '%s[%s]' % (e[1], expr_text(e[2]))
    if k == 'call':
        return '%s(%s)' % (e[1], ', '.join(expr_text(a) for a in e[2]))
    if k == 'code':
        return 'function ' + e[1]
    if k == 'neg':
        x = e[1]
        return '-' + (('(%s)' % expr_text(x)) if x[0] in ('bin', 'neg', 'not') else expr_text(x))
    if k == 'not':
        x = e[1]
        return 'not ' + (('(%s)' % expr_text(x)) if x[0] in ('bin', 'neg', 'not') else expr_text(x))
    if k == 'bin':
        op, left, right = e[1], e[2], e[3]
        n = LEVEL[op]
        te, td = expr_text(left), expr_text(right)
        if left[0] == 'bin':
            ne = LEVEL[left[1]]
            if ne < n or (n == 1 and ne == 1) or (n == 2 and ne == 2):
                te = '(%s)' % te
        elif left[0] == 'not' or (left[0] == 'neg' and left[1][0] in ('bin', 'neg', 'not')):
            te = '(%s)' % te
        if right[0] == 'bin':
            nd = LEVEL[right[1]]
            if nd < n or (nd == n and not (n == 1 and right[1] == op)):
                td = '(%s)' % td
        elif right[0] == 'neg' or (right[0] == 'not' and n != 1):
            td = '(%s)' % td
        return '%s %s %s' % (te, op, td)
    raise DecompileError('expression %r' % (e,))


class Printer(object):
    def __init__(self, ref, inference):
        self.ref = ref
        self.inf = inference

    def type_name(self, code_part, node):
        base = code_part - 5 if code_part >= 9 else code_part
        if base == 7:
            t = self.inf.kind.get(node, 'handle') if node else 'handle'
        else:
            t = BASIC[base]
        return t

    def statements(self, cmds, f, evidence, line_list):
        pad = '    ' * evidence
        for c in cmds:
            k = c[0]
            if k == 'local':
                code_part, n, _v, e = c[1], c[2], c[3], c[4]
                t = self.type_name(code_part, ('line', f.fname, n))
                if code_part >= 9:
                    line_list.append('%slocal %s array %s' % (pad, t, n))
                elif e is not None:
                    line_list.append('%slocal %s %s = %s' % (pad, t, n, expr_text(e)))
                else:
                    line_list.append('%slocal %s %s' % (pad, t, n))
            elif k == 'set':
                line_list.append('%sset %s = %s' % (pad, c[1], expr_text(c[2])))
            elif k == 'set_array':
                line_list.append('%sset %s[%s] = %s' % (pad, c[1], expr_text(c[2]), expr_text(c[3])))
            elif k == 'call':
                line_list.append('%scall %s(%s)' % (pad, c[1], ', '.join(expr_text(a) for a in c[2])))
            elif k == 'return':
                line_list.append('%sreturn%s' % (pad, (' ' + expr_text(c[1])) if c[1] is not None else ''))
            elif k == 'exitwhen':
                line_list.append('%sexitwhen %s' % (pad, expr_text(c[1])))
            elif k == 'loop':
                line_list.append('%sloop' % pad)
                self.statements(c[1], f, evidence + 1, line_list)
                line_list.append('%sendloop' % pad)
            elif k == 'if':
                for i, (cond, body) in enumerate(c[1]):
                    line_list.append('%s%s %s then' % (pad, 'if' if i == 0 else 'elseif', expr_text(cond)))
                    self.statements(body, f, evidence + 1, line_list)
                if c[2]:
                    line_list.append('%selse' % pad)
                    self.statements(c[2], f, evidence + 1, line_list)
                line_list.append('%sendif' % pad)
            else:
                raise DecompileError('statement %r' % (k,))

    def signature(self, f):
        if f.params:
            ps = ', '.join('%s %s' % (self.type_name(c, ('line', f.fname, pn)), pn) for c, pn in f.params)
        else:
            ps = 'nothing'
        ret = self.type_name(f.ret, ('r', f.fname)) if f.ret else 'nothing'
        return '%s takes %s returns %s' % (f.fname, ps, ret)

    def program(self, globals_block, funcs, natives, header_text, hooks=(), outside=()):
        funcs = [f for f in funcs if f.fname not in outside] if outside else funcs
        header = list(header_text)
        line_list = []
        line_list.append('globals')
        for code_part, n, const, e in globals_block:
            t = self.type_name(code_part, ('g', n))
            if code_part >= 9:
                line_list.append('    %s array %s' % (t, n))
            elif e is not None:
                line_list.append('    %s%s %s = %s' % ('constant ' if const else '', t, n, expr_text(e)))
            else:
                line_list.append('    %s %s' % (t, n))
        line_list.append('endglobals')
        line_list.append('')
        for n in natives:
            line_list.append(self.ref.extra_text[n])
        hooks = set(hooks)
        for f in funcs:
            if f.fname in hooks:
                line_list.append('native ' + self.signature(f))
        line_list.append('')
        for f in funcs:
            if f.fname in hooks:
                continue
            line_list.append('function ' + self.signature(f))
            self.statements(f.body, f, 1, line_list)
            line_list.append('endfunction')
            line_list.append('')
        body = '\n'.join(line_list)
        types = self.ref.type_lines(body)
        return '\n'.join(header + types + ([''] if types else []) + [body])


PURE_NATIVES = frozenset((
    'Player', 'GetTriggerPlayer', 'GetOwningPlayer', 'GetLocalPlayer', 'GetEnumPlayer', 'GetFilterPlayer',
    'ConvertedPlayer', 'GetConvertedPlayerId', 'GetPlayerId', 'GetHandleId', 'GetTriggeringTrigger', 'GetExpiredTimer',
    'GetTriggerUnit', 'GetEnumUnit', 'GetFilterUnit', 'GetPlayerName', 'I2S', 'S2I', 'R2S', 'R2I', 'I2R', 'S2R',
    'StringHash', 'LoadInteger', 'LoadReal', 'LoadStr', 'LoadBoolean', 'LoadPlayerHandle', 'LoadUnitHandle',
    'GetUnitTypeId', 'GetItemTypeId', 'GetPlayerController', 'GetPlayerSlotState', 'StringLength', 'SubString',
    'GetUnitUserData', 'GetItemUserData', 'StringHashBJ'))
_WRITES = frozenset((LIT, MOVRV, MOVRCODE, MOVRA, I2R, NEG, NOT, POP, 24, 25, 36)) | frozenset(BINOP)


def _dropped_arguments(bc, ref, p):
    return _dead_code(bc, ref, p - 2, bc.b2[p])


def _dead_code(bc, ref, j, need_stack):
    need_regs, take = set(), []
    if bc.op[j] in _WRITES and bc.b2[j] != 0:
        need_regs.add(bc.b2[j])
    elif bc.op[j] == CALLN or (bc.op[j] == POPN and j >= 1 and bc.op[j - 1] == CALLJ):
        need_regs.add(0)
    while need_stack or need_regs:
        if j < 0:
            return None, 'ran out of code'
        o, b0, b1, b2 = bc.op[j], bc.b0[j], bc.b1[j], bc.b2[j]
        if o == PUSH and need_stack:
            need_stack -= 1
            need_regs.add(b2)
        elif o in (LIT, MOVRV, MOVRCODE) and b2 in need_regs:
            need_regs.discard(b2)
        elif o == MOVRA and b2 in need_regs:
            need_regs.discard(b2)
            need_regs.add(b1)
        elif (o in BINOP or o in (24, 25, 36)) and b2 in need_regs:
            need_regs.discard(b2)
            need_regs.update((b0, b1))
        elif o in (I2R, NEG, NOT) and b2 in need_regs:
            pass
        elif o == POP and b2 in need_regs:
            need_regs.discard(b2)
            need_stack += 1
        elif o == CALLN and 0 in need_regs:
            fname = bc.fname(bc.arg[j])
            if fname not in PURE_NATIVES:
                return None, 'an argument calls %s' % fname
            need_regs.discard(0)
            need_stack += len(ref.native(fname)[0])
        elif o == POPN and 0 in need_regs and j >= 1 and bc.op[j - 1] == CALLJ:
            fname = bc.fname(bc.arg[j - 1])
            if fname not in PURE_NATIVES:
                return None, 'an argument calls %s' % fname
            need_regs.discard(0)
            need_stack += bc.b2[j]
            take.extend((j, j - 1))
            j -= 2
            continue
        elif o == POPN and 0 in need_regs and j >= 1 and bc.op[j - 1] == LIT and bc.b2[j - 1] == 0:
            need_regs.discard(0)
            need_stack += bc.b2[j]
            take.extend((j, j - 1))
            j -= 2
            if j >= 0 and bc.op[j] == LIT and bc.b2[j] != 0 and bc.b2[j] not in need_regs:
                take.append(j)
                j -= 1
            continue
        else:
            return None, '%s inside the dropped arguments' % kkwe.OPS.get(o, o)
        take.append(j)
        j -= 1
    return take, None


def _result_unused(bc, k):
    j = k + 1
    while j < bc.n:
        o, b0, b1, b2 = bc.op[j], bc.b0[j], bc.b1[j], bc.b2[j]
        if (o == LIT and b2 == 0) or o in (CALLN, CALLJ):
            return True
        if o in (LIT, MOVRV, MOVRCODE) and b2 != 0:
            pass
        elif o in (PUSH, POP) and b2 != 0:
            pass
        elif o == MOVRA and b2 != 0 and b1 != 0:
            pass
        elif (o in BINOP or o in (24, 25, 36)) and 0 not in (b0, b1, b2):
            pass
        else:
            return False
        j += 1
    return False


def strip_constant_calls(bc, ref):
    drop, found, skipped = set(), collections.Counter(), []
    fstart, fname = 0, None
    for k in range(bc.n):
        o = bc.op[k]
        if o == FUNCTION:
            fstart, fname = k, bc.fname(bc.arg[k])
        if o != POPN or k < 1 or bc.op[k - 1] == CALLJ:
            continue
        if bc.op[k - 1] != LIT or bc.b2[k - 1] != 0:
            skipped.append((fname, k, 'POPN not after a constant into the result register'))
            continue
        take, why = _dropped_arguments(bc, ref, k)
        if take is None or (take and min(take) <= fstart):
            skipped.append((fname, k, why or 'reaches the function header'))
            continue
        drop.update(take)
        drop.add(k)
        if _result_unused(bc, k):
            drop.add(k - 1)
        found[fname] += 1
    fname = None
    for k in range(bc.n - 1):
        if bc.op[k] == FUNCTION:
            fname = bc.fname(bc.arg[k])
        if bc.op[k] == LIT and bc.b2[k] == 0 and bc.op[k + 1] in (MOVVR, MOVAR, PUSH):
            found[fname] += 1
    comparisons = collections.Counter()
    fname = None
    for k in range(2, bc.n):
        if bc.op[k] == FUNCTION:
            fname = bc.fname(bc.arg[k])
        if bc.op[k] == LIT and bc.op[k - 1] == POP and bc.b2[k] == bc.b2[k - 1] and bc.b2[k] != 0:
            take, why = _dead_code(bc, ref, k - 2, 1)
            if take is None or k - 1 in drop or any(x in drop for x in take):
                skipped.append((fname, k, why or 'overlaps another patched site'))
                continue
            drop.update(take)
            drop.add(k - 1)
            comparisons[fname] += 1
    targets = collections.Counter(bc.arg[k] for k in range(bc.n) if bc.op[k] in (JIT, JIF, JUMP))
    conditions = collections.Counter()
    fname = None
    for k in range(1, bc.n - 1):
        if bc.op[k] == FUNCTION:
            fname = bc.fname(bc.arg[k])
        if (bc.op[k] == LABEL and targets[bc.arg[k]] == 0 and bc.op[k - 1] == JUMP and bc.op[k + 1] == LABEL
                and bc.arg[k + 1] == bc.arg[k - 1] and targets[bc.arg[k + 1]] == 1):
            drop.update((k - 1, k, k + 1))
            conditions[fname] += 1
    if drop:
        keep = [k for k in range(bc.n) if k not in drop]
        bc.b0 = bytes(bytearray(bc.b0[k] for k in keep))
        bc.b1 = bytes(bytearray(bc.b1[k] for k in keep))
        bc.b2 = bytes(bytearray(bc.b2[k] for k in keep))
        bc.op = bytes(bytearray(bc.op[k] for k in keep))
        bc.arg = array.array('i', (bc.arg[k] for k in keep))
        bc.n = len(keep)
    if found:
        b1, arg, fname = bytearray(bc.b1), bc.arg, None
        for k in range(bc.n - 1):
            if bc.op[k] == FUNCTION:
                fname = bc.fname(bc.arg[k])
            if (fname in found and bc.op[k] == LIT and bc.b2[k] == 0 and b1[k] == 4 and bc.op[k + 1] in (JIT, JIF)
                    and bc.b2[k + 1] == 0):
                b1[k] = 8
                arg[k] = 1 if arg[k] else 0
        bc.b1 = bytes(b1)
    bc.constant_calls = dict(found)
    bc.removed_conditions = dict(conditions)
    bc.constant_comparisons = dict(comparisons)
    return dict(found), skipped


def grafts_of(bc, segments):
    out, prev_reg = [], None
    for begin, end_pos in segments:
        if bc.op[begin] != FUNCTION:
            continue
        regs = [bc.b2[k] for k in range(begin, end_pos) if bc.op[k] in ALLOCATING and bc.b2[k]]
        if regs and regs[0] == 1 and prev_reg not in (None, 255):
            out.append(bc.fname(bc.arg[begin]))
        elif regs:
            prev_reg = regs[-1]
    patched = set()
    for kind in ('constant_calls', 'removed_conditions', 'constant_comparisons'):
        patched |= set(getattr(bc, kind, None) or ())
    if patched:
        out += [bc.fname(bc.arg[b]) for b, _e in segments
                if bc.op[b] == FUNCTION and bc.fname(bc.arg[b]) in patched and bc.fname(bc.arg[b]) not in out]
    return out


def resume_at(bc, segments, fname):
    after_diag = False
    reg = rot = None
    for begin, end_pos in segments:
        if bc.op[begin] == FUNCTION and bc.fname(bc.arg[begin]) == fname:
            after_diag = True
            continue
        if not after_diag or bc.op[begin] == FUNCTION and bc.fname(bc.arg[begin]) in ():
            continue
        if reg is None:
            reg = next((bc.b2[k] for k in range(begin, end_pos) if bc.op[k] in ALLOCATING and bc.b2[k]), None)
        if rot is None:
            labels = [bc.arg[k] for k in range(begin, end_pos) if bc.op[k] in WITH_LABEL]
            rot = min(labels) if labels else None
        if reg is not None and rot is not None:
            break
    if reg is None or rot is None:
        return None
    return reg - 1, rot - 1


CLOSES_STATEMENT = (MOVVR, MOVAR, RET, LABEL, JIT, JIF, JUMP)


def statements_of(item_entries):
    clusters, current, rot = [], [], {}
    for _b0, b1, b2, op, arg in item_entries:
        if op in (PUSH, POP):
            continue
        if op in (LABEL, JIT, JIF, JUMP):
            arg = rot.setdefault(arg, len(rot))
        if op == LIT:
            tok = (op, b1, arg)
        elif op in (FUNCTION, LOCAL, GLOBAL, CONSTANT, FUNCARG):
            tok = (op, b2, arg)
        else:
            tok = (op, arg)
        current.append(repr(tok))
        if op in CLOSES_STATEMENT:
            clusters.append(sorted(current))
            current = []
    if current:
        clusters.append(sorted(current))
    return clusters


def _segmentos(seq, is_function, name_of):
    out = [(None, [])]
    for x in seq:
        if is_function(x):
            out.append((name_of(x), []))
        out[-1][1].append(x)
    return out


def prove_map(bc, ref, common, blizzard, map_text, maximum=5):
    segments = map_functions(bc, ref)
    where = [k for begin, end_pos in segments for k in range(begin, end_pos) if not stray_i2r(bc, k)]
    grafts = grafts_of(bc, segments)
    c = KC.Compiler()
    c.isolate = dict((n, resume_at(bc, segments, n)) for n in grafts)
    for body_text in (common, blizzard):
        c.declare_all(KC.analyze(body_text))
    reg = next((bc.b2[k] for k in where if bc.op[k] in ALLOCATING and bc.b2[k]), None)
    rot = next((bc.arg[k] for k in where if bc.op[k] in WITH_LABEL), None)
    c.reg = reg - 1 if reg else 0
    c.rot = rot - 1 if rot else 0
    if segments and segments[0][0] + 1 < segments[0][1] and bc.op[segments[0][0] + 1] in (GLOBAL, CONSTANT):
        c.init_name = bc.fname(bc.arg[segments[0][0]])
        rest = [k for begin, end_pos in segments[1:] for k in range(begin, end_pos) if not stray_i2r(bc, k)]
        reg2 = next((bc.b2[k] for k in rest if bc.op[k] in ALLOCATING and bc.b2[k]), None)
        label2 = next((bc.arg[k] for k in rest if bc.op[k] in WITH_LABEL), None)
        init_end = [k for k in range(segments[0][0], segments[0][1])]
        reg1 = [bc.b2[k] for k in init_end if bc.op[k] in ALLOCATING and bc.b2[k]]
        label1 = [bc.arg[k] for k in init_end if bc.op[k] in WITH_LABEL]
        if reg2 is not None and reg1 and reg1[-1] % 255 + 1 != reg2:
            c.after_init = (
                reg2 - 1,
                (label2 - 1) if label2 is not None and label1 and label1[-1] + 1 != label2 else None,
            )
    c.file_name([it for it in KC.analyze(map_text) if it[0] != 'type'])
    ins, only_problems = c.ins, where
    structure = []
    if grafts:
        outside = set(grafts)
        orig = _segmentos(where, lambda k: bc.op[k] == FUNCTION, lambda k: bc.fname(bc.arg[k]))
        mine = _segmentos(c.ins, lambda x: x[3] == FUNCTION, lambda x: str(x[4]))
        my_parts = dict((n, item_entries) for n, item_entries in mine if n in outside)
        for n, ks in orig:
            if n in outside:
                a = [(bc.b0[k], bc.b1[k], bc.b2[k], bc.op[k], KC.arg_of(bc, k)) for k in ks]
                if n not in my_parts or statements_of(a) != statements_of(my_parts[n]):
                    structure.append((ks[0], 'graft', n))
        only_problems = [k for n, ks in orig if n not in outside for k in ks]
        ins = [x for n, item_entries in mine if n not in outside for x in item_entries]
    real_blocks = []
    identical, diffs = KC.compare(bc, ins, maximum=maximum, real_blocks=real_blocks, where=only_problems)
    return len(ins), len(only_problems), identical, structure + diffs, real_blocks, c, grafts


def cited(globals_block, funcs):
    called, codes, texts = set(), set(), set()

    def visit(e):
        if e[0] == 'call':
            called.add(e[1])
        elif e[0] == 'code':
            codes.add(e[1])
        elif e[0] == 'str':
            texts.add(e[1])

    def statement(c):
        k = c[0]
        if k == 'call':
            called.add(c[1])
            for a in c[2]:
                walk_expr(a, visit)
        elif k in ('local', 'global') and c[4] is not None:
            walk_expr(c[4], visit)
        elif k == 'set':
            walk_expr(c[2], visit)
        elif k == 'set_array':
            walk_expr(c[2], visit)
            walk_expr(c[3], visit)
        elif k == 'if':
            for cond, _body in c[1]:
                walk_expr(cond, visit)
        elif k in ('exitwhen', 'return') and c[1] is not None:
            walk_expr(c[1], visit)

    for _code, _n, _const, e in globals_block:
        if e is not None:
            walk_expr(e, visit)
    for f in funcs:
        walk_cmds(f.body, statement)
    return called, codes, texts


def check_hooks(faithful, body_text, hooks, outside=()):
    hooks = set(hooks)
    outside = set(outside)
    a, b = KC.analyze(faithful), KC.analyze(body_text)
    nats = {}
    rest = []
    for it in b:
        if it[0] == 'native' and it[1] in hooks:
            nats[it[1]] = (it[2], it[3])
        else:
            rest.append(it)
    expected_len = []
    for it in a:
        if it[0] == 'function' and it[1] in outside:
            continue
        if it[0] == 'function' and it[1] in hooks:
            if nats.pop(it[1], None) != (it[2], it[3]):
                return 'the hook %s did not become the `native` of the same signature' % it[1]
        else:
            expected_len.append(it)
    if nats:
        return 'extra `native`: %s' % ', '.join(sorted(nats)[:5])
    if expected_len != rest:
        return 'the delivered text differs from the faithful one outside the hooks'
    return None


HEADER_LINES = (
    '// war3map.j restored from the compiled script of the map (the bytecode of the game\'s script engine).',
    '// The names are the original ones; comments do not exist in the bytecode; the type of each handle was',
    '// worked out from how it is used. Proof: this text, compiled again, gives the same instructions.',
    '',
)


def recover(bc, common, blizzard, extra_natives=None, map_own='', header_text=HEADER_LINES, no_clash=False):
    old = sys.getrecursionlimit()
    if old < KC._RECURSION:
        sys.setrecursionlimit(KC._RECURSION)
    try:
        return _decompile(bc, common, blizzard, extra_natives, map_own, header_text, no_clash)
    except RecursionError:
        raise DecompileError('the script does not come back: an expression of the map is too deep (RecursionError)')
    finally:
        if old < KC._RECURSION:
            sys.setrecursionlimit(old)


def restore_jumps(bc):
    op, arg = bc.op, bc.arg
    pos, targets = {}, collections.Counter()
    for k in range(bc.n):
        if op[k] == LABEL:
            pos[arg[k]] = k
        elif op[k] in (JUMP, JIF, JIT):
            targets[arg[k]] += 1
    where = []
    for k in range(bc.n):
        if op[k] != JIF:
            continue
        la = arg[k]
        p = pos.get(la)
        if p is None or p <= k + 1 or p + 1 >= bc.n or op[p - 1] == JUMP:
            continue
        if op[p + 1] == LABEL and arg[p + 1] == la - 1 and not targets.get(la - 1):
            where.append(p)
    if not where:
        return bc, []
    new = copy.copy(bc)
    b0, b1, b2, ops, args = bytearray(), bytearray(), bytearray(), bytearray(), array.array('i')
    cut = 0
    for p in where:
        b0 += bc.b0[cut:p]
        b1 += bc.b1[cut:p]
        b2 += bc.b2[cut:p]
        ops += bc.op[cut:p]
        args.extend(bc.arg[cut:p])
        b0.append(0)
        b1.append(0)
        b2.append(0)
        ops.append(JUMP)
        args.append(bc.arg[p] - 1)
        cut = p
    b0 += bc.b0[cut:]
    b1 += bc.b1[cut:]
    b2 += bc.b2[cut:]
    ops += bc.op[cut:]
    args.extend(bc.arg[cut:])
    new.b0, new.b1, new.b2, new.op, new.arg = bytes(b0), bytes(b1), bytes(b2), bytes(ops), args
    new.n = len(ops)
    return new, where


def _decompile(bc, common, blizzard, extra_natives, map_own, header_text, no_clash):
    bc, restored_jumps = restore_jumps(bc)
    if extra_natives is None:
        with open(DEFAULT_NATIVES, 'rb') as fh:
            extra_natives = fh.read().decode('utf-8', 'surrogateescape')
    ref = Reference(common, blizzard, extra_natives, map_own)
    ref.bytecode_types(bc)
    constant_calls, constants_skipped = strip_constant_calls(bc, ref)
    try:
        globals_block, funcs, natives, _region = decompile(bc, ref)
    except (IndexError, KeyError, struct.error, RecursionError) as e:
        raise DecompileError('the bytecode cannot be read (%s: %s)' % (type(e).__name__, e))
    inf = Inference(ref, globals_block, funcs)
    inf.collect(globals_block)
    if bc.order == kkwe.REVERSE_ORDER:
        inf.pin_hook_types(funcs)
    types = inf.resolve()
    imp = Printer(ref, inf)
    faithful = imp.program(globals_block, funcs, natives, list(header_text))
    try:
        n, total, identical, diffs, real_blocks, _c, grafted = prove_map(bc, ref, common, blizzard, faithful)
    except (SyntaxError, NameError, ValueError, KeyError, RecursionError) as e:
        raise DecompileError('the restored script does not compile again (%s: %s)' % (type(e).__name__, e))
    if diffs or real_blocks or n != total:
        where = ''
        if diffs:
            d = diffs[0]
            where = ' (the first one at instruction %d, function %s)' % (d[0], KC.function_of(bc, min(d[0], bc.n - 1)))
        raise DecompileError(
            'the proof fails: the restored script compiles to %d instructions and the map has %d; %d '
            'equal, %d real literals with another value%s' % (n, total, identical, len(real_blocks), where)
        )
    called, codes, texts = cited(globals_block, funcs)
    if bc.order == kkwe.REVERSE_ORDER:
        hooks = [f.fname for f in funcs if is_hook(f) and f.fname not in codes and f.fname not in texts]
    else:
        hooks = [f.fname for f in funcs if is_hook(f) and f.ret == 3 and f.fname not in codes and
                 f.fname not in texts]
    from_game = set(ref.natives) | set(ref.funcs)
    outside = [g for g in hooks if no_clash and g not in called and g in from_game]
    body_text = faithful
    if hooks:
        body_text = imp.program(globals_block, funcs, natives, list(header_text), hooks, outside)
        invalid = check_hooks(faithful, body_text, hooks, outside)
        if invalid:
            raise DecompileError(invalid)
    clashes = sorted(set([f.fname for f in funcs if f.fname in from_game and f.fname not in outside] +
                         [n for n in natives if n in from_game] +
                         [n for _c, n, _k, _e in globals_block if n in ref.globals_block or n in from_game]))
    global_clashes = sorted(set(n for _c, n, _k, _e in globals_block if n in ref.globals_block or n in from_game))
    return body_text, {'instructions': total, 'globals_block': len(globals_block), 'functions': len(funcs) - len(hooks),
                       'natives': len(natives), 'hooks': len(hooks) - len(outside), 'hooks_left_out': outside,
                       'clashes': clashes, 'global_clashes': global_clashes, 'handles': len(types),
                       'bad_flows': len(inf.bad_ones), 'jumps_restored': len(restored_jumps),
                       'grafts_of': [g for g in grafted if g not in constant_calls and g not in bc.removed_conditions
                                     and g not in bc.constant_comparisons],
                       'constant_calls': constant_calls, 'constant_calls_skipped': constants_skipped,
                       'removed_conditions': bc.removed_conditions, 'constant_comparisons': bc.constant_comparisons}

