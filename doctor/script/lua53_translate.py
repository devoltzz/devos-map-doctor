# Turns a precompiled Lua 5.3 chunk back into Lua source that runs the same, one statement per instruction.
import math

from doctor.script import lua_bytecode


FIELDS_PER_FLUSH = 50
MAX_LOCAL_REGS = 190

(MOVE, LOADK, LOADKX, LOADBOOL, LOADNIL, GETUPVAL, GETTABUP, GETTABLE, SETTABUP, SETUPVAL, SETTABLE, NEWTABLE, SELF,
 ADD, SUB, MUL, MOD, POW, DIV, IDIV, BAND, BOR, BXOR, SHL, SHR, UNM, BNOT, NOT, LEN, CONCAT, JMP, EQ, LT, LE, TEST,
 TESTSET, CALL, TAILCALL, RETURN, FORLOOP, FORPREP, TFORCALL, TFORLOOP, SETLIST, CLOSURE, VARARG, EXTRAARG) = range(47)
KK_YDWE_OPCODES = {27: 0, 26: 1, 29: 2, 28: 3, 31: 4, 30: 5, 33: 6, 32: 7, 35: 8, 34: 9, 37: 10, 36: 11, 39: 12, 38: 13,
                   41: 14, 40: 15, 43: 16, 42: 17, 45: 18, 44: 19, 1: 20, 2: 21, 0: 22, 4: 23, 3: 24, 6: 25, 5: 26,
                   8: 27, 7: 28, 10: 29, 9: 30, 12: 31, 11: 32, 14: 33, 13: 34, 16: 35, 15: 36, 18: 37, 17: 38, 20: 39,
                   19: 40, 21: 41, 22: 42, 24: 43, 23: 44, 46: 45, 25: 46}
assert sorted(KK_YDWE_OPCODES) == list(range(47)) and sorted(KK_YDWE_OPCODES.values()) == list(range(47))


def opcode_table(main):
    last = set(g['code'][-1] & 0x3F for g in lua_bytecode.walk(main) if g['code'])
    if last == {38}:
        return 'standard'
    if last == {17}:
        return 'kk_ydwe'
    return None


def renumber(main, table):
    if table == 'standard':
        return main
    for g in lua_bytecode.walk(main):
        g['code'] = [(i & ~0x3F) | KK_YDWE_OPCODES[i & 0x3F] for i in g['code']]
    return main


ARITH = {ADD: '+', SUB: '-', MUL: '*', MOD: '%', POW: '^', DIV: '/', IDIV: '//', BAND: '&', BOR: '|', BXOR: '~',
         SHL: '<<', SHR: '>>'}
UNARY = {UNM: '-', BNOT: '~', NOT: 'not ', LEN: '#'}
COMPARE = {EQ: '==', LT: '<', LE: '<='}

PRELUDE = r'''local __mt, __tonumber, __floor, __ceil, __maxi, __mini, __error, __select =
  math.type, tonumber, math.floor, math.ceil, math.maxinteger, math.mininteger, error, select
local function __toint(v, mode)
  -- luaV_tointeger: an integer, or a float/string with an exact integer value (mode 1: floor, 2: ceil)
  if __mt(v) == 'integer' then return v end
  local n = __tonumber(v)
  if n == nil then return nil end
  if __mt(n) == 'integer' then return n end
  if n ~= n then return nil end
  local f = (mode == 2) and __ceil(n) or __floor(n)
  if f ~= f or f >= 2^63 or f < -2^63 then return nil end
  return __mt(f) == 'integer' and f or math.tointeger(f)
end
local function __forprep(init, limit, step)
  if __mt(init) == 'integer' and __mt(step) == 'integer' then
    local stop = false
    local il = __toint(limit, step < 0 and 2 or 1)
    if il == nil then
      local n = __tonumber(limit)
      if n ~= nil then
        if 0 < n then il = __maxi; if step < 0 then stop = true end
        else il = __mini; if step >= 0 then stop = true end end
      end
    end
    if il ~= nil then
      if stop then init = 0 end
      return init - step, il, step
    end
  end
  local nl = __tonumber(limit)
  if nl == nil then __error("'for' limit must be a number", 2) end
  local ns = __tonumber(step)
  if ns == nil then __error("'for' step must be a number", 2) end
  local ni = __tonumber(init)
  if ni == nil then __error("'for' initial value must be a number", 2) end
  return (ni + 0.0) - (ns + 0.0), nl + 0.0, ns + 0.0
end
local function __setlist(t, base, ...)
  for i = 1, __select('#', ...) do t[base + i] = (__select(i, ...)) end
end
local F = {}
'''


def _decode(i):
    op = i & 0x3F
    a = (i >> 6) & 0xFF
    c = (i >> 14) & 0x1FF
    b = (i >> 23) & 0x1FF
    bx = (i >> 14) & 0x3FFFF
    return op, a, b, c, bx, bx - 131071, i >> 6


def literal(v):
    if v is None:
        return 'nil'
    if v is True:
        return 'true'
    if v is False:
        return 'false'
    if isinstance(v, int):
        if v == -2 ** 63:
            return 'math.mininteger'
        if not -2 ** 31 < v < 2 ** 31:
            return '0x%x' % (v & 0xFFFFFFFFFFFFFFFF)
        return '%d' % v if v >= 0 else '(%d)' % v
    if isinstance(v, float):
        if v != v:
            return '(0/0)'
        if v == math.inf:
            return '(1/0)'
        if v == -math.inf:
            return '(-1/0)'
        if v == 0.0:
            return '(-0.0)' if math.copysign(1.0, v) < 0 else '0.0'
        s = repr(v)
        if 'e' not in s and '.' not in s and 'inf' not in s:
            s += '.0'
        return s if v > 0 else '(%s)' % s
    if isinstance(v, bytes):
        out = ['"']
        for ch in v:
            if ch == 0x22:
                out.append('\\"')
            elif ch == 0x5C:
                out.append('\\\\')
            elif 0x20 <= ch < 0x7F:
                out.append(chr(ch))
            elif ch == 0x0A:
                out.append('\\n')
            else:
                out.append('\\%03d' % ch)
        out.append('"')
        return ''.join(out)
    raise ValueError('constant of type %r' % type(v))


class TranslateError(Exception):
    pass


class _Proto(object):
    def __init__(self, f, ident, child_ids):
        self.f = f
        self.id = ident
        self.child_ids = child_ids


def _number(main):
    out = []

    def visit(f):
        me = len(out)
        out.append(None)
        kids = [visit(p) for p in f['protos']]
        out[me] = _Proto(f, me, kids)
        return me
    visit(main)
    return out


def _function(pr):
    f = pr.f
    code = f['code']
    consts = f['consts']
    n = len(code)
    stack = max(f['stack'], f['params'], 2)
    captured = set()
    for i in code:
        op, a, b, c, bx, sbx, ax = _decode(i)
        if op == CLOSURE:
            child = f['protos'][bx]
            for instack, idx in child['upvals']:
                if instack:
                    captured.add(idx)

    def R(k):
        if k in captured:
            return 'b%d[1]' % k
        if k >= MAX_LOCAL_REGS:
            return 'X[%d]' % k
        return 'r%d' % k

    def K(k):
        return literal(consts[k])

    def RK(x):
        return K(x & 0xFF) if x & 0x100 else R(x)

    def regs(a, count):
        return [R(a + k) for k in range(count)]

    targets = set()
    for pc, i in enumerate(code):
        op, a, b, c, bx, sbx, ax = _decode(i)
        if op in (JMP, FORLOOP, FORPREP, TFORLOOP):
            targets.add(pc + 1 + sbx)
        elif op in (EQ, LT, LE, TEST, TESTSET):
            targets.add(pc + 2)
        elif op == LOADBOOL and c:
            targets.add(pc + 2)
    out = []
    params = ['r%d' % k if k not in captured else 'p%d' % k for k in range(f['params'])]
    if f['vararg']:
        params.append('...')
    out.append('F[%d] = function(U) return function(%s)' % (pr.id, ', '.join(params)))
    local_regs = [k for k in range(f['params'], min(stack, MAX_LOCAL_REGS)) if k not in captured]
    for k in range(0, len(local_regs), 60):
        out.append('local ' + ', '.join('r%d' % r for r in local_regs[k:k + 60]))
    if stack > MAX_LOCAL_REGS:
        out.append('local X = {}')
    boxes = sorted(captured)
    for k in boxes:
        if k < f['params']:
            out.append('local b%d = {p%d}' % (k, k))
        else:
            out.append('local b%d = {}' % k)
    pending = None
    skip = set()

    def close_from(a):
        return ' '.join('b%d = {b%d[1]}' % (k, k) for k in boxes if k >= a)

    def args(first, count_or_open):
        if count_or_open is None:
            if pending is None:
                raise TranslateError('open argument list without a pending result at pc %d' % pc)
            start, expr = pending
            return [R(k) for k in range(first, start)] + [expr]
        return [R(k) for k in range(first, first + count_or_open)]

    for pc, i in enumerate(code):
        if pc in skip:
            continue
        op, a, b, c, bx, sbx, ax = _decode(i)
        if pc in targets:
            if pending is not None:
                raise TranslateError('a jump lands inside an open result list at pc %d' % pc)
            out.append('::L%d::' % pc)
        s = None
        if op == MOVE:
            s = '%s = %s' % (R(a), R(b))
        elif op == LOADK:
            s = '%s = %s' % (R(a), K(bx))
        elif op == LOADKX:
            nxt = _decode(code[pc + 1])
            if nxt[0] != EXTRAARG:
                raise TranslateError('LOADKX without EXTRAARG at pc %d' % pc)
            s = '%s = %s' % (R(a), K(nxt[6]))
            skip.add(pc + 1)
        elif op == LOADBOOL:
            s = '%s = %s' % (R(a), 'true' if b else 'false')
            if c:
                s += ' goto L%d' % (pc + 2)
        elif op == LOADNIL:
            s = ' '.join('%s = nil' % R(a + k) for k in range(b + 1))
        elif op == GETUPVAL:
            s = '%s = U[%d][1]' % (R(a), b + 1)
        elif op == GETTABUP:
            s = '%s = U[%d][1][%s]' % (R(a), b + 1, RK(c))
        elif op == GETTABLE:
            s = '%s = %s[%s]' % (R(a), R(b), RK(c))
        elif op == SETTABUP:
            s = 'U[%d][1][%s] = %s' % (a + 1, RK(b), RK(c))
        elif op == SETUPVAL:
            s = 'U[%d][1] = %s' % (b + 1, R(a))
        elif op == SETTABLE:
            s = '%s[%s] = %s' % (R(a), RK(b), RK(c))
        elif op == NEWTABLE:
            s = '%s = {}' % R(a)
        elif op == SELF:
            s = '%s = %s %s = %s[%s]' % (R(a + 1), R(b), R(a), R(a + 1), RK(c))
        elif op in ARITH:
            s = '%s = %s %s %s' % (R(a), RK(b), ARITH[op], RK(c))
        elif op in UNARY:
            s = '%s = %s%s' % (R(a), UNARY[op], R(b))
        elif op == CONCAT:
            s = '%s = %s' % (R(a), ' .. '.join(R(k) for k in range(b, c + 1)))
        elif op == JMP:
            pre = close_from(a - 1) if a else ''
            s = (pre + ' ' if pre else '') + 'goto L%d' % (pc + 1 + sbx)
        elif op in COMPARE:
            cond = '%s %s %s' % (RK(b), COMPARE[op], RK(c))
            s = ('if not (%s) then goto L%d end' if a else 'if %s then goto L%d end') % (cond, pc + 2)
        elif op == TEST:
            s = ('if not %s then goto L%d end' if c else 'if %s then goto L%d end') % (R(a), pc + 2)
        elif op == TESTSET:
            s = ('if %s then %s = %s else goto L%d end' if c else 'if not %s then %s = %s else goto L%d end') % (
                R(b), R(a), R(b), pc + 2)
        elif op in (CALL, TAILCALL):
            argl = args(a + 1, None if b == 0 else b - 1)
            if b == 0:
                pending = None
            call = '%s(%s)' % (R(a), ', '.join(argl))
            if op == TAILCALL:
                s = 'do return %s end' % call
                if pc + 1 < n and _decode(code[pc + 1])[0] == RETURN and pc + 1 not in targets:
                    skip.add(pc + 1)
            elif c == 0:
                pending = (a, call)
                continue
            elif c == 1:
                s = call
            else:
                s = '%s = %s' % (', '.join(regs(a, c - 1)), call)
        elif op == RETURN:
            if b == 0:
                vals = args(a, None)
                pending = None
            else:
                vals = regs(a, b - 1)
            s = 'do return %s end' % ', '.join(vals) if vals else 'do return end'
        elif op == FORPREP:
            s = '%s, %s, %s = __forprep(%s, %s, %s) goto L%d' % (R(a), R(a + 1), R(a + 2), R(a), R(a + 1), R(a + 2),
                                                                   pc + 1 + sbx)
        elif op == FORLOOP:
            ra, lim, step, ext = R(a), R(a + 1), R(a + 2), R(a + 3)
            s = ('%s = %s + %s if (0 < %s and %s <= %s) or (not (0 < %s) and %s <= %s) then %s = %s goto L%d end'
                 % (ra, ra, step, step, ra, lim, step, lim, ra, ext, ra, pc + 1 + sbx))
        elif op == TFORCALL:
            s = '%s = %s(%s, %s)' % (', '.join(regs(a + 3, c)), R(a), R(a + 1), R(a + 2))
        elif op == TFORLOOP:
            s = 'if %s ~= nil then %s = %s goto L%d end' % (R(a + 1), R(a), R(a + 1), pc + 1 + sbx)
        elif op == SETLIST:
            if c == 0:
                nxt = _decode(code[pc + 1])
                if nxt[0] != EXTRAARG:
                    raise TranslateError('SETLIST without EXTRAARG at pc %d' % pc)
                c = nxt[6]
                skip.add(pc + 1)
            base = (c - 1) * FIELDS_PER_FLUSH
            if b == 0:
                vals = args(a + 1, None)
                pending = None
                s = '__setlist(%s, %d, %s)' % (R(a), base, ', '.join(vals))
            else:
                s = ' '.join('%s[%d] = %s' % (R(a), base + k, R(a + k)) for k in range(1, b + 1))
        elif op == CLOSURE:
            child = f['protos'][bx]
            ups = []
            for instack, idx in child['upvals']:
                ups.append('b%d' % idx if instack else 'U[%d]' % (idx + 1))
            s = '%s = F[%d]({%s})' % (R(a), pr.child_ids[bx], ', '.join(ups))
        elif op == VARARG:
            if b == 0:
                pending = (a, '...')
                continue
            s = '%s = ...' % ', '.join(regs(a, b - 1))
        elif op == EXTRAARG:
            raise TranslateError('EXTRAARG alone at pc %d' % pc)
        else:
            raise TranslateError('unknown opcode %d at pc %d' % (op, pc))
        if pending is not None:
            raise TranslateError('an open result list at pc %d is not taken by the next instruction' % (pc - 1))
        out.append(s)
    if pending is not None:
        raise TranslateError('the function ends with an open result list')
    if n and _decode(code[-1])[0] not in (RETURN, TAILCALL, JMP):
        out.append('do return end')
    out.append('end end')
    return '\n'.join(out)


def translate(data, name='chunk'):
    main, whole = lua_bytecode.load(data)
    if not whole:
        raise TranslateError('%s: bytes left after the chunk' % name)
    table = opcode_table(main)
    if table is None:
        raise TranslateError('%s: the opcode numbering is neither standard Lua 5.3 nor the KK YDWE engine one' % name)
    renumber(main, table)
    protos = _number(main)
    parts = ['-- %s: translated from Lua 5.3 bytecode (%d functions)' % (name, len(protos)), PRELUDE]
    for pr in protos:
        parts.append(_function(pr))
    if len(main['upvals']) != 1:
        raise TranslateError(
            '%s: the main function has %d upvalues (one, _ENV, expected)' % (name, len(main['upvals']))
        )
    parts.append('return function(ENV, ...) return F[0]({{ENV}})(...) end')
    return '\n'.join(parts) + '\n'
