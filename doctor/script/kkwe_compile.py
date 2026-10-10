# Compiles JASS to the bytecode of the game, to prove a decompiled script.
import re
import struct
import sys

from doctor.script import kkwe


_RX = re.compile(r'''
   (?P<ws>[ \t\r\f\v]+)
  |(?P<nl>\n)
  |(?P<comment>//[^\n]*)
  |(?P<real>\d+\.\d*|\.\d+)
  |(?P<hex>0[xX][0-9a-fA-F]+|\$[0-9a-fA-F]+)
  |(?P<int>\d+)
  |(?P<raw>'(?:\\.|[^'\\])*')
  |(?P<str>"(?:\\.|[^"\\])*")
  |(?P<id>[A-Za-z_][A-Za-z0-9_]*)
  |(?P<op>==|!=|<=|>=|[-+*/=<>()\[\],])
''', re.X | re.S)

KEYWORDS = {'globals', 'endglobals', 'constant', 'native', 'takes', 'returns', 'nothing', 'function', 'endfunction',
            'local', 'set', 'call', 'if', 'then', 'elseif', 'else', 'endif', 'loop', 'endloop', 'exitwhen', 'return',
            'type', 'extends', 'array', 'and', 'or', 'not', 'true', 'false', 'null', 'debug'}

ESCAPES = {'n': '\n', 'r': '\r', 't': '\t', 'b': '\b', 'f': '\f', '"': '"', '\\': '\\', "'": "'"}


def unescape(body):
    out = []
    i = 0
    while i < len(body):
        c = body[i]
        if c == '\\' and i + 1 < len(body):
            out.append(ESCAPES.get(body[i + 1], body[i + 1]))
            i += 2
        else:
            out.append(c)
            i += 1
    return ''.join(out)


def i32(v):
    v &= 0xFFFFFFFF
    return v - 0x100000000 if v & 0x80000000 else v


def f32_bits(body_text):
    return struct.unpack('<i', struct.pack('<f', float(body_text)))[0]


class Token(object):
    __slots__ = ('kind', 'field_value', 'ln')

    def __init__(self, kind, field_value, ln):
        self.kind, self.field_value, self.ln = kind, field_value, ln

    def __repr__(self):
        return '%s:%r@%d' % (self.kind, self.field_value, self.ln)


_NATIVE_KINDS = ('nl', 'real', 'hex', 'int', 'raw', 'str', 'id', 'op', 'end_pos')
_LEXER = []


def _native_lexer():
    if not _LEXER:
        try:
            try:
                from doctor.script import jass_native
            except ImportError:
                from doctor.script import jass_native
            _LEXER.append(jass_native.load_lexer())
        except Exception:
            _LEXER.append(None)
    return _LEXER[0]


def lex(body_text):
    native_lex = _native_lexer()
    q = native_lex(body_text, 1) if native_lex is not None else None
    if q is None:
        return lex_regex(body_text)
    toks = []
    ap = toks.append
    types = _NATIVE_KINDS
    end_pos = len(q) - 4
    for k in range(0, end_pos, 4):
        g, a, b, ln = types[q[k]], q[k + 1], q[k + 2], q[k + 3]
        if g == 'id':
            v = body_text[a:b]
            ap(Token('kw' if v in KEYWORDS else 'id', v, ln))
        elif g == 'op':
            ap(Token('op', body_text[a:b], ln))
        elif g == 'nl':
            ap(Token('nl', None, ln))
        elif g == 'int':
            v = body_text[a:b]
            ap(Token('int', i32(int(v, 8) if len(v) > 1 and v[0] == '0' else int(v)), ln))
        elif g == 'str':
            ap(Token('str', unescape(body_text[a + 1:b - 1]), ln))
        elif g == 'real':
            ap(Token('real', body_text[a:b], ln))
        elif g == 'hex':
            v = body_text[a:b]
            ap(Token('int', i32(int(v[1:] if v[0] == '$' else v[2:], 16)), ln))
        else:
            s = unescape(body_text[a + 1:b - 1])
            val = 0
            for ch in s.encode('utf-8', 'surrogateescape'):
                val = (val << 8) | ch
            ap(Token('int', i32(val), ln))
    ln = q[end_pos + 3]
    ap(Token('nl', None, ln))
    ap(Token('end_pos', None, ln))
    return toks


def lex_regex(body_text):
    toks = []
    ln = 1
    pos = 0
    n = len(body_text)
    while pos < n:
        m = _RX.match(body_text, pos)
        if not m:
            raise SyntaxError('line %d: unexpected character %r' % (ln, body_text[pos]))
        g = m.lastgroup
        v = m.group(g)
        pos = m.end()
        if g == 'ws' or g == 'comment':
            continue
        if g == 'nl':
            if toks and toks[-1].kind != 'nl':
                toks.append(Token('nl', None, ln))
            ln += 1
            continue
        if g == 'real':
            toks.append(Token('real', v, ln))
        elif g == 'hex':
            toks.append(Token('int', i32(int(v[1:] if v[0] == '$' else v[2:], 16)), ln))
        elif g == 'int':
            toks.append(Token('int', i32(int(v, 8) if len(v) > 1 and v[0] == '0' else int(v)), ln))
        elif g == 'raw':
            s = unescape(v[1:-1])
            val = 0
            for ch in s.encode('utf-8', 'surrogateescape'):
                val = (val << 8) | ch
            toks.append(Token('int', i32(val), ln))
        elif g == 'str':
            toks.append(Token('str', unescape(v[1:-1]), ln))
            ln += v.count('\n')
        elif g == 'id':
            toks.append(Token('kw' if v in KEYWORDS else 'id', v, ln))
        else:
            toks.append(Token('op', v, ln))
    toks.append(Token('nl', None, ln))
    toks.append(Token('end_pos', None, ln))
    return toks


class Parser(object):
    def __init__(self, toks):
        self.t = toks
        self.p = 0

    def ve(self, k=0):
        return self.t[self.p + k]

    def advance(self):
        tk = self.t[self.p]
        self.p += 1
        return tk

    def is_at(self, kind, field_value=None, k=0):
        tk = self.t[self.p + k]
        return tk.kind == kind and (field_value is None or tk.field_value == field_value)

    def expect(self, kind, field_value=None):
        tk = self.advance()
        if tk.kind != kind or (field_value is not None and tk.field_value != field_value):
            raise SyntaxError(
                'line %d: expected %s %r, got %s %r' % (tk.ln, kind, field_value, tk.kind, tk.field_value)
            )
        return tk

    def skip_nl(self):
        while self.is_at('nl'):
            self.p += 1

    def end_of_line(self):
        self.expect('nl')

    def program(self):
        item_entries = []
        self.skip_nl()
        while not self.is_at('end_pos'):
            if self.is_at('kw', 'type'):
                self.advance()
                fname = self.expect('id').field_value
                self.expect('kw', 'extends')
                parent = self.advance().field_value
                self.end_of_line()
                item_entries.append(('type', fname, parent))
            elif self.is_at('kw', 'globals'):
                item_entries.append(self.globals_block())
            elif self.is_at('kw', 'native') or (self.is_at('kw', 'constant') and self.is_at('kw', 'native', 1)):
                if self.is_at('kw', 'constant'):
                    self.advance()
                self.advance()
                fname = self.expect('id').field_value
                params, ret = self.signature()
                self.end_of_line()
                item_entries.append(('native', fname, params, ret))
            elif self.is_at('kw', 'function') or (self.is_at('kw', 'constant') and self.is_at('kw', 'function', 1)):
                item_entries.append(self.function())
            else:
                tk = self.ve()
                raise SyntaxError('line %d: unexpected at the top level: %s %r' % (tk.ln, tk.kind, tk.field_value))
            self.skip_nl()
        return item_entries

    def typed_name(self):
        tk = self.advance()
        if tk.kind not in ('id', 'kw'):
            raise SyntaxError('line %d: expected a type' % tk.ln)
        return tk.field_value

    def signature(self):
        self.expect('kw', 'takes')
        params = []
        if self.is_at('kw', 'nothing'):
            self.advance()
        else:
            while True:
                t = self.typed_name()
                n = self.expect('id').field_value
                params.append((t, n))
                if self.is_at('op', ','):
                    self.advance()
                    continue
                break
        self.expect('kw', 'returns')
        ret = self.typed_name()
        return params, ret

    def globals_block(self):
        self.expect('kw', 'globals')
        self.end_of_line()
        decl = []
        self.skip_nl()
        while not self.is_at('kw', 'endglobals'):
            const = False
            if self.is_at('kw', 'constant'):
                self.advance()
                const = True
            t = self.typed_name()
            is_array = False
            if self.is_at('kw', 'array'):
                self.advance()
                is_array = True
            n = self.expect('id').field_value
            e = None
            if self.is_at('op', '='):
                self.advance()
                e = self.expr()
            self.end_of_line()
            decl.append((const, t, is_array, n, e))
            self.skip_nl()
        self.advance()
        self.end_of_line()
        return ('globals', decl)

    def function(self):
        if self.is_at('kw', 'constant'):
            self.advance()
        self.expect('kw', 'function')
        fname = self.expect('id').field_value
        params, ret = self.signature()
        self.end_of_line()
        body = self.block_entry(('endfunction',))
        self.expect('kw', 'endfunction')
        self.end_of_line()
        return ('function', fname, params, ret, body)

    def block_entry(self, ends):
        cmds = []
        self.skip_nl()
        while not (self.ve().kind == 'kw' and self.ve().field_value in ends):
            cmds.append(self.statement())
            self.skip_nl()
        return cmds

    def statement(self):
        tk = self.ve()
        if tk.kind == 'kw' and tk.field_value == 'debug':
            self.advance()
            return ('debug', self.statement())
        if tk.kind != 'kw':
            raise SyntaxError('line %d: unexpected statement %r' % (tk.ln, tk.field_value))
        k = tk.field_value
        if k == 'local':
            self.advance()
            t = self.typed_name()
            is_array = False
            if self.is_at('kw', 'array'):
                self.advance()
                is_array = True
            n = self.expect('id').field_value
            e = None
            if self.is_at('op', '='):
                self.advance()
                e = self.expr()
            self.end_of_line()
            return ('local', t, n, is_array, e)
        if k == 'set':
            self.advance()
            n = self.expect('id').field_value
            if self.is_at('op', '['):
                self.advance()
                i = self.expr()
                self.expect('op', ']')
                self.expect('op', '=')
                e = self.expr()
                self.end_of_line()
                return ('set_array', n, i, e)
            self.expect('op', '=')
            e = self.expr()
            self.end_of_line()
            return ('set', n, e)
        if k == 'call':
            self.advance()
            n = self.expect('id').field_value
            args = self.arguments()
            self.end_of_line()
            return ('call', n, args)
        if k == 'if':
            self.advance()
            branches = []
            c = self.expr()
            self.expect('kw', 'then')
            self.end_of_line()
            body = self.block_entry(('elseif', 'else', 'endif'))
            branches.append((c, body))
            else_body = None
            while True:
                if self.is_at('kw', 'elseif'):
                    self.advance()
                    c = self.expr()
                    self.expect('kw', 'then')
                    self.end_of_line()
                    body = self.block_entry(('elseif', 'else', 'endif'))
                    branches.append((c, body))
                    continue
                if self.is_at('kw', 'else'):
                    self.advance()
                    self.end_of_line()
                    else_body = self.block_entry(('endif',))
                self.expect('kw', 'endif')
                self.end_of_line()
                break
            return ('if', branches, else_body)
        if k == 'loop':
            self.advance()
            self.end_of_line()
            body = self.block_entry(('endloop',))
            self.expect('kw', 'endloop')
            self.end_of_line()
            return ('loop', body)
        if k == 'exitwhen':
            self.advance()
            e = self.expr()
            self.end_of_line()
            return ('exitwhen', e)
        if k == 'return':
            self.advance()
            if self.is_at('nl'):
                self.end_of_line()
                return ('return', None)
            e = self.expr()
            self.end_of_line()
            return ('return', e)
        raise SyntaxError('line %d: unexpected statement %r' % (tk.ln, k))

    def arguments(self):
        self.expect('op', '(')
        args = []
        if self.is_at('op', ')'):
            self.advance()
            return args
        while True:
            args.append(self.expr())
            if self.is_at('op', ','):
                self.advance()
                continue
            self.expect('op', ')')
            return args

    def expr(self):
        left = self.comparison()
        if self.is_at('kw', 'and') or self.is_at('kw', 'or'):
            op = self.advance().field_value
            return ('bin', op, left, self.expr())
        return left

    def comparison(self):
        left = self.sum_expr()
        while self.is_at('op') and self.ve().field_value in ('==', '!=', '<', '>', '<=', '>='):
            op = self.advance().field_value
            left = ('bin', op, left, self.sum_expr())
        return left

    def sum_expr(self):
        left = self.product()
        while self.is_at('op', '+') or self.is_at('op', '-'):
            op = self.advance().field_value
            left = ('bin', op, left, self.product())
        return left

    def product(self):
        left = self.unary()
        while self.is_at('op', '*') or self.is_at('op', '/'):
            op = self.advance().field_value
            left = ('bin', op, left, self.unary())
        return left

    def unary(self):
        if self.is_at('op', '-'):
            self.advance()
            return ('neg', self.unary())
        if self.is_at('op', '+'):
            self.advance()
            return self.unary()
        if self.is_at('kw', 'not'):
            self.advance()
            return ('not', self.unary())
        return self.primary()

    def primary(self):
        tk = self.advance()
        if tk.kind == 'int':
            return ('int', tk.field_value)
        if tk.kind == 'real':
            return ('real', tk.field_value)
        if tk.kind == 'str':
            return ('str', tk.field_value)
        if tk.kind == 'kw':
            if tk.field_value == 'true':
                return ('bool', 1)
            if tk.field_value == 'false':
                return ('bool', 0)
            if tk.field_value == 'null':
                return ('null',)
            if tk.field_value == 'function':
                return ('code', self.expect('id').field_value)
        if tk.kind == 'op' and tk.field_value == '(':
            e = self.expr()
            self.expect('op', ')')
            return e
        if tk.kind == 'id':
            if self.is_at('op', '('):
                return ('call', tk.field_value, self.arguments())
            if self.is_at('op', '['):
                self.advance()
                i = self.expr()
                self.expect('op', ']')
                return ('idx', tk.field_value, i)
            return ('var', tk.field_value)
        raise SyntaxError('line %d: unexpected expression %s %r' % (tk.ln, tk.kind, tk.field_value))


_RECURSION = 20000


def analyze(body_text):
    old = sys.getrecursionlimit()
    if old < _RECURSION:
        sys.setrecursionlimit(_RECURSION)
    try:
        return Parser(lex(body_text)).program()
    finally:
        if old < _RECURSION:
            sys.setrecursionlimit(old)


BASIC_TYPES = {'integer': 4, 'real': 5, 'string': 6, 'boolean': 8, 'code': 3, 'nothing': 0, 'handle': 7}


class Symbol(str):
    pass


class Compiler(object):
    def __init__(self):
        self.ins = []
        self.reg = 0
        self.rot = 0
        self.globals_block = {}
        self.funcs = {}
        self.local_vars = None
        self.ret = None
        self.init_name = '<init>'
        self.after_init = None
        self.isolate = {}

    def emit(self, op, b0=0, b1=0, b2=0, arg=0):
        self.ins.append((b0, b1, b2, op, arg))

    def new_reg(self):
        self.reg = self.reg % 255 + 1
        return self.reg

    def new_label(self):
        self.rot += 1
        return self.rot

    @staticmethod
    def code_part(kind):
        return BASIC_TYPES.get(kind, 7)

    def var(self, fname):
        if self.local_vars is not None and fname in self.local_vars:
            return self.local_vars[fname]
        if fname in self.globals_block:
            return self.globals_block[fname]
        raise NameError('unknown variable: %s' % fname)

    def i2r(self, reg, kind, tgt):
        if kind == 'integer' and tgt == 'real':
            self.emit(23, b2=reg)
            return 'real'
        return kind

    def expr(self, e, tgt=None):
        k = e[0]
        if k == 'int':
            r = self.new_reg()
            self.emit(12, b1=4, b2=r, arg=e[1])
            return r, 'integer'
        if k == 'real':
            r = self.new_reg()
            self.emit(12, b1=5, b2=r, arg=f32_bits(e[1]))
            return r, 'real'
        if k == 'str':
            r = self.new_reg()
            self.emit(12, b1=6, b2=r, arg=('s', e[1]))
            return r, 'string'
        if k == 'bool':
            r = self.new_reg()
            self.emit(12, b1=8, b2=r, arg=e[1])
            return r, 'boolean'
        if k == 'null':
            r = self.new_reg()
            self.emit(12, b1=2, b2=r, arg=0)
            return r, 'null'
        if k == 'var':
            t, _v = self.var(e[1])
            r = self.new_reg()
            self.emit(14, b1=self.code_part(t), b2=r, arg=Symbol(e[1]))
            return r, t
        if k == 'idx':
            t, _v = self.var(e[1])
            ri, ti = self.expr(e[2])
            r = self.new_reg()
            self.emit(16, b0=self.code_part(t), b1=ri, b2=r, arg=Symbol(e[1]))
            return r, t
        if k == 'code':
            r = self.new_reg()
            self.emit(15, b1=3, b2=r, arg=Symbol(e[1]))
            return r, 'code'
        if k == 'call':
            return 0, self.call_expr(e[1], e[2])
        if k == 'neg':
            r, t = self.expr(e[1])
            self.emit(37, b2=r)
            return r, t
        if k == 'not':
            r, t = self.expr(e[1])
            self.emit(38, b2=r)
            return r, 'boolean'
        if k == 'bin':
            return self.binary(e[1], e[2], e[3])
        raise ValueError('expression %r' % (e,))

    OPBIN = {'==': 26, '!=': 27, '<=': 28, '>=': 29, '<': 30, '>': 31, '+': 32, '-': 33, '*': 34, '/': 35}

    def binary(self, op, left, right):
        if op in ('and', 'or'):
            rl, _tl = self.expr(left)
            lc = self.new_label()
            self.emit(42 if op == 'and' else 41, b2=rl, arg=lc)
            rr, _tr = self.expr(right)
            lf = self.new_label()
            self.emit(43, arg=lf)
            self.emit(40, arg=lc)
            self.emit(12, b1=8, b2=rr, arg=0 if op == 'and' else 1)
            self.emit(40, arg=lf)
            return rr, 'boolean'
        right_type = self.type_of(right) if left[0] == 'null' and op in ('==', '!=') else None
        if right_type and right_type != 'null':
            rl, tl = self.new_reg(), right_type
            self.emit(12, b1=self.code_part(right_type), b2=rl, arg=0)
        else:
            rl, tl = self.expr(left)
        type_l = tl
        tr_prev = self.type_of(right)
        if tl == 'integer' and tr_prev == 'real':
            self.emit(23, b2=rl)
            type_l = 'real'
        self.emit(19, b2=rl)
        if right[0] == 'null' and op in ('==', '!='):
            rr = self.new_reg()
            self.emit(12, b1=self.code_part(tl), b2=rr, arg=0)
            tr = tl
        else:
            rr, tr = self.expr(right)
        if tr == 'integer' and type_l == 'real':
            self.emit(23, b2=rr)
            tr = 'real'
        p = self.new_reg()
        self.emit(20, b2=p)
        self.emit(self.OPBIN[op], b0=rr, b1=p, b2=p)
        if op in ('==', '!=', '<=', '>=', '<', '>'):
            return p, 'boolean'
        if type_l == 'real' or tr == 'real':
            return p, 'real'
        if type_l == 'string':
            return p, 'string'
        return p, type_l

    def type_of(self, e):
        k = e[0]
        if k == 'int':
            return 'integer'
        if k == 'real':
            return 'real'
        if k == 'str':
            return 'string'
        if k == 'bool':
            return 'boolean'
        if k == 'null':
            return 'null'
        if k in ('var', 'idx'):
            return self.var(e[1])[0]
        if k == 'code':
            return 'code'
        if k == 'call':
            return self.funcs[e[1]][1]
        if k == 'neg':
            return self.type_of(e[1])
        if k == 'not':
            return 'boolean'
        if k == 'bin':
            op = e[1]
            if op in ('and', 'or', '==', '!=', '<=', '>=', '<', '>'):
                return 'boolean'
            a, b = self.type_of(e[2]), self.type_of(e[3])
            if 'real' in (a, b):
                return 'real'
            return a
        raise ValueError(e)

    def call_expr(self, fname, args):
        if fname not in self.funcs:
            raise NameError('unknown function: %s' % fname)
        params, ret, native = self.funcs[fname]
        for k, a in enumerate(args):
            r, t = self.expr(a)
            if k < len(params):
                self.i2r(r, t, params[k][0])
            self.emit(19, b2=r)
        if native:
            self.emit(21, arg=Symbol(fname))
        else:
            self.emit(22, arg=Symbol(fname))
            if args:
                self.emit(11, b2=len(args))
        return ret

    def statements(self, cmds, loop_end):
        for c in cmds:
            self.statement(c, loop_end)

    def statement(self, c, loop_end):
        k = c[0]
        if k == 'local':
            _, t, n, is_array, e = c
            self.local_vars[n] = (t, is_array)
            self.emit(5, b2=self.code_part(t) + (5 if is_array else 0), arg=Symbol(n))
            if e is not None:
                r, te = self.expr(e)
                self.i2r(r, te, t)
                self.emit(17, b2=r, arg=Symbol(n))
            return
        if k == 'set':
            t, _v = self.var(c[1])
            r, te = self.expr(c[2])
            self.i2r(r, te, t)
            self.emit(17, b2=r, arg=Symbol(c[1]))
            return
        if k == 'set_array':
            t, _v = self.var(c[1])
            ri, _ti = self.expr(c[2])
            self.emit(19, b2=ri)
            rv, tv = self.expr(c[3])
            self.i2r(rv, tv, t)
            p = self.new_reg()
            self.emit(20, b2=p)
            self.emit(18, b1=rv, b2=p, arg=Symbol(c[1]))
            return
        if k == 'call':
            self.call_expr(c[1], c[2])
            return
        if k == 'if':
            branches, else_body = c[1], c[2]
            self.if_cmd(branches, else_body, loop_end)
            return
        if k == 'loop':
            begin = self.new_label()
            end_pos = self.new_label()
            self.emit(40, arg=begin)
            self.statements(c[1], end_pos)
            self.emit(43, arg=begin)
            self.emit(40, arg=end_pos)
            return
        if k == 'exitwhen':
            r, _t = self.expr(c[1])
            self.emit(41, b2=r, arg=loop_end)
            return
        if k == 'return':
            if c[1] is not None:
                r, _t = self.expr(c[1])
                self.emit(13, b1=r, b2=0)
            self.emit(39)
            return
        if k == 'debug':
            return
        raise ValueError('statement %r' % (c,))

    def if_cmd(self, branches, else_body, loop_end):
        cond, body = branches[0]
        r, _t = self.expr(cond)
        if not body and len(branches) == 1 and not else_body:
            return
        l_else = self.new_label()
        l_end = self.new_label()
        self.emit(42, b2=r, arg=l_else)
        self.statements(body, loop_end)
        self.emit(43, arg=l_end)
        self.emit(40, arg=l_else)
        if len(branches) > 1:
            self.if_cmd(branches[1:], else_body, loop_end)
        elif else_body:
            self.statements(else_body, loop_end)
        self.emit(40, arg=l_end)

    def declare(self, item_entries):
        for it in item_entries:
            if it[0] == 'native':
                self.funcs[it[1]] = (it[2], it[3], True)
            elif it[0] == 'function':
                self.funcs[it[1]] = (it[2], it[3], False)

    def declare_all(self, item_entries):
        self.declare(item_entries)
        for it in item_entries:
            if it[0] == 'globals':
                for _const, t, is_array, n, _e in it[1]:
                    self.globals_block[n] = (t, is_array)

    def file_name(self, item_entries):
        self.declare(item_entries)
        for it in item_entries:
            k = it[0]
            if k == 'type':
                self.emit(9, arg=Symbol(it[2]))
                self.emit(10, arg=Symbol(it[1]))
            elif k == 'globals':
                self.emit(3, arg=Symbol(self.init_name))
                self.local_vars = None
                for const, t, is_array, n, e in it[1]:
                    self.globals_block[n] = (t, is_array)
                    self.emit(7 if const else 6, b2=self.code_part(t) + (5 if is_array else 0), arg=Symbol(n))
                    if e is not None:
                        r, te = self.expr(e)
                        self.i2r(r, te, t)
                        self.emit(17, b2=r, arg=Symbol(n))
                self.emit(39)
                self.emit(4)
                if self.after_init:
                    self.reg = self.after_init[0]
                    if self.after_init[1] is not None:
                        self.rot = self.after_init[1]
            elif k == 'function':
                _, fname, params, ret, body = it
                saved = (self.reg, self.rot) if fname in self.isolate else None
                if saved:
                    self.reg = 0
                self.emit(3, b2=self.code_part(ret), arg=Symbol(fname))
                self.local_vars = {}
                self.ret = ret
                for i, (t, n) in enumerate(params):
                    self.local_vars[n] = (t, False)
                    self.emit(8, b1=len(params) - i, b2=self.code_part(t), arg=Symbol(n))
                self.statements(body, None)
                self.emit(12)
                self.emit(39)
                self.emit(4)
                self.local_vars = None
                if saved:
                    self.reg, self.rot = self.isolate[fname] or saved

    def end_pos(self):
        self.emit(1)


def arg_of(bc, k):
    op, b1 = bc.op[k], bc.b1[k]
    a = bc.arg[k]
    if op in kkwe.WITH_NAME:
        return Symbol(bc.fname(a))
    if op == 12 and b1 == 6 and a:
        return ('s', bc.fname(a))
    return a


def compare(bc, ins, begin=0, maximum=10, real_blocks=None, where=None):
    diffs = []
    identical = 0
    for j, (b0, b1, b2, op, arg) in enumerate(ins):
        if where is not None:
            if j >= len(where):
                diffs.append((bc.n, 'the bytecode ended'))
                break
            k = where[j]
        else:
            k = begin + j
        if k >= bc.n:
            diffs.append((k, 'the bytecode ended'))
            break
        orig = (bc.b0[k], bc.b1[k], bc.b2[k], bc.op[k], arg_of(bc, k))
        mine = (b0, b1, b2, op, arg)
        if orig == mine:
            identical += 1
            continue
        if real_blocks is not None and op == 12 and b1 == 5 and orig[:4] == mine[:4]:
            real_blocks.append((k, orig[4], arg))
            identical += 1
            continue
        diffs.append((k, orig, mine))
        if len(diffs) >= maximum:
            break
    return identical, diffs


def function_of(bc, k):
    for x in range(k, -1, -1):
        if bc.op[x] == 3:
            return bc.fname(bc.arg[x])
    return '?'

