# Transpiles a JASS script into Lua for Warcraft III 3.0, keeping the JASS integer and string rules.
import re
import struct


KEYWORDS = {
    'globals', 'endglobals', 'native', 'constant', 'type', 'extends', 'function', 'takes', 'returns',
    'endfunction', 'local', 'set', 'call', 'if', 'then', 'else', 'elseif', 'endif', 'loop', 'endloop',
    'exitwhen', 'return', 'debug', 'and', 'or', 'not', 'null', 'true', 'false', 'array', 'nothing',
}
LUA_KEYWORDS = {
    'and', 'break', 'do', 'else', 'elseif', 'end', 'false', 'for', 'function', 'goto', 'if', 'in', 'local',
    'nil', 'not', 'or', 'repeat', 'return', 'then', 'true', 'until', 'while',
}
PRIMITIVES = {'integer', 'real', 'string', 'boolean', 'code', 'nothing'}
LOCALS_IN_LUA = 180


class JassError(Exception):
    pass


class Tok(object):
    __slots__ = ('kind', 'val', 'line')

    def __init__(self, kind, val, line):
        self.kind = kind
        self.val = val
        self.line = line

    def __repr__(self):
        return '%s(%r)@%d' % (self.kind, self.val, self.line)


def wrap32(v):
    return ((v + 0x80000000) & 0xFFFFFFFF) - 0x80000000


_ID_RE = re.compile(r'[A-Za-z_][A-Za-z0-9_]*')
_HEX_RE = re.compile(r'0[xX][0-9A-Fa-f]+')
_NUM_RE = re.compile(r'(\d+\.\d*|\.\d+|\d+)')
_WS_RE = re.compile(r'[ \t\r]+')


def lex(src):
    toks = []
    i = 0
    n = len(src)
    line = 1
    append = toks.append
    while i < n:
        c = src[i]
        if c == '\n':
            if toks and toks[-1].kind != 'NL':
                append(Tok('NL', None, line))
            line += 1
            i += 1
            continue
        if c in ' \t\r':
            m = _WS_RE.match(src, i)
            i = m.end()
            continue
        if c == '/' and i + 1 < n and src[i + 1] == '/':
            j = src.find('\n', i)
            if j < 0:
                j = n
            i = j
            continue
        if c == '"':
            j = i + 1
            buf = []
            while True:
                if j >= n:
                    raise JassError('unterminated string on line %d' % line)
                ch = src[j]
                if ch == '\\':
                    nx = src[j + 1] if j + 1 < n else ''
                    if nx == 'n':
                        buf.append('\n')
                    elif nx == 't':
                        buf.append('\t')
                    elif nx == 'r':
                        buf.append('\r')
                    elif nx == '"':
                        buf.append('"')
                    elif nx == '\\':
                        buf.append('\\')
                    elif nx == "'":
                        buf.append("'")
                    elif nx == 'b':
                        buf.append('\b')
                    else:
                        buf.append('\\')
                        buf.append(nx)
                    j += 2
                    continue
                if ch == '"':
                    break
                if ch == '\n':
                    line += 1
                buf.append(ch)
                j += 1
            append(Tok('STR', ''.join(buf), line))
            i = j + 1
            continue
        if c == "'":
            j = src.find("'", i + 1)
            k = i + 1
            buf = []
            while True:
                if k >= n:
                    raise JassError('unterminated fourcc on line %d' % line)
                ch = src[k]
                if ch == '\\':
                    buf.append(src[k + 1])
                    k += 2
                    continue
                if ch == "'":
                    break
                buf.append(ch)
                k += 1
            s = ''.join(buf)
            b = s.encode('utf-8', 'surrogateescape')
            if len(b) == 4 and any(ch > 127 for ch in b):
                val = 0
                for ch in b:
                    val = (val * 256 + (ch - 256 if ch >= 128 else ch)) & 0xFFFFFFFF
                if val >= 0x80000000:
                    val -= 0x100000000
            elif len(b) == 4:
                val = struct.unpack('>I', b)[0]
                if val >= 0x80000000:
                    val -= 0x100000000
            elif len(b) == 1:
                val = b[0]
            else:
                raise JassError('invalid fourcc %r on line %d' % (s, line))
            append(Tok('INT', val, line))
            i = k + 1
            continue
        if c.isdigit() or (c == '.' and i + 1 < n and src[i + 1].isdigit()):
            m = _HEX_RE.match(src, i)
            if m:
                append(Tok('INT', wrap32(int(m.group(0), 16)), line))
                i = m.end()
                continue
            m = _NUM_RE.match(src, i)
            t = m.group(0)
            i = m.end()
            if '.' in t:
                append(Tok('REAL', t, line))
            else:
                if len(t) > 1 and t[0] == '0' and all(ch in '01234567' for ch in t):
                    append(Tok('INT', wrap32(int(t, 8)), line))
                else:
                    append(Tok('INT', wrap32(int(t)), line))
            continue
        if c == '$':
            m = re.compile(r'\$[0-9A-Fa-f]+').match(src, i)
            if m:
                append(Tok('INT', wrap32(int(m.group(0)[1:], 16)), line))
                i = m.end()
                continue
        m = _ID_RE.match(src, i)
        if m:
            w = m.group(0)
            i = m.end()
            if w in KEYWORDS:
                append(Tok('KW', w, line))
            else:
                append(Tok('ID', w, line))
            continue
        two = src[i:i + 2]
        if two in ('==', '!=', '<=', '>='):
            append(Tok('OP', two, line))
            i += 2
            continue
        if c in '+-*/<>=(),[]':
            append(Tok('OP', c, line))
            i += 1
            continue
        if c == '﻿':
            i += 1
            continue
        raise JassError('unexpected character %r on line %d' % (c, line))
    append(Tok('NL', None, line))
    append(Tok('EOF', None, line))
    return toks


class Node(object):
    __slots__ = ('k', 'a', 'b', 'c', 'line')

    def __init__(self, k, a=None, b=None, c=None, line=0):
        self.k = k
        self.a = a
        self.b = b
        self.c = c
        self.line = line

    def __repr__(self):
        return 'Node(%s,%r,%r,%r)' % (self.k, self.a, self.b, self.c)


class Func(object):
    def __init__(self, name, params, ret, line):
        self.name = name
        self.params = params
        self.ret = ret
        self.line = line
        self.body = []
        self.is_native = False


class GlobalDecl(object):
    __slots__ = ('type', 'name', 'is_array', 'is_const', 'init', 'line')

    def __init__(self, type_, name, is_array, is_const, init, line):
        self.type = type_
        self.name = name
        self.is_array = is_array
        self.is_const = is_const
        self.init = init
        self.line = line


class Parser(object):
    def __init__(self, toks):
        self.toks = toks
        self.i = 0
        self.globals = []
        self.natives = {}
        self.functions = []
        self.types = {}

    def peek(self, off=0):
        return self.toks[self.i + off]

    def next(self):
        t = self.toks[self.i]
        self.i += 1
        return t

    def accept(self, kind, val=None):
        t = self.toks[self.i]
        if t.kind == kind and (val is None or t.val == val):
            self.i += 1
            return t
        return None

    def expect(self, kind, val=None):
        t = self.toks[self.i]
        if t.kind == kind and (val is None or t.val == val):
            self.i += 1
            return t
        raise JassError('expected %s %r, found %r on line %d' % (kind, val, t, t.line))

    def skip_nl(self):
        while self.toks[self.i].kind == 'NL':
            self.i += 1

    def parse(self):
        while True:
            self.skip_nl()
            t = self.peek()
            if t.kind == 'EOF':
                break
            if t.kind == 'KW' and t.val == 'globals':
                self.next()
                self.parse_globals()
            elif t.kind == 'KW' and t.val == 'type':
                self.next()
                name = self.expect('ID').val
                self.expect('KW', 'extends')
                base = self.next().val
                self.types[name] = base
                self.expect('NL')
            elif t.kind == 'KW' and t.val in ('native', 'constant', 'function'):
                self.parse_function()
            else:
                raise JassError('unexpected token at the top level: %r' % t)
        return self

    def parse_type(self):
        t = self.next()
        if t.kind == 'ID' or (t.kind == 'KW' and t.val == 'nothing'):
            return t.val
        raise JassError('type expected, found %r on line %d' % (t, t.line))

    def parse_globals(self):
        while True:
            self.skip_nl()
            t = self.peek()
            if t.kind == 'KW' and t.val == 'endglobals':
                self.next()
                self.expect('NL')
                return
            is_const = bool(self.accept('KW', 'constant'))
            type_ = self.parse_type()
            is_array = bool(self.accept('KW', 'array'))
            name = self.expect('ID').val
            init = None
            if self.accept('OP', '='):
                init = self.parse_expr()
            self.expect('NL')
            self.globals.append(GlobalDecl(type_, name, is_array, is_const, init, t.line))

    def parse_params(self):
        params = []
        if self.accept('KW', 'nothing'):
            return params
        while True:
            type_ = self.parse_type()
            name = self.expect('ID').val
            params.append((type_, name))
            if not self.accept('OP', ','):
                break
        return params

    def parse_function(self):
        self.accept('KW', 'constant')
        t = self.next()
        if t.kind == 'KW' and t.val == 'native':
            name = self.expect('ID').val
            self.expect('KW', 'takes')
            params = self.parse_params()
            self.expect('KW', 'returns')
            ret = self.parse_type()
            self.expect('NL')
            f = Func(name, params, ret, t.line)
            f.is_native = True
            self.natives[name] = f
            return
        if not (t.kind == 'KW' and t.val == 'function'):
            raise JassError('function expected on line %d' % t.line)
        name = self.expect('ID').val
        self.expect('KW', 'takes')
        params = self.parse_params()
        self.expect('KW', 'returns')
        ret = self.parse_type()
        self.expect('NL')
        f = Func(name, params, ret, t.line)
        f.body = self.parse_block(('endfunction',))
        self.expect('KW', 'endfunction')
        self.accept('NL')
        self.functions.append(f)

    def parse_block(self, terminators):
        stmts = []
        while True:
            self.skip_nl()
            t = self.peek()
            if t.kind == 'KW' and t.val in terminators:
                return stmts
            if t.kind == 'EOF':
                raise JassError('unexpected end, expected %s' % (terminators,))
            stmts.append(self.parse_stmt())

    def parse_stmt(self):
        t = self.next()
        line = t.line
        if t.kind == 'KW' and t.val == 'debug':
            t = self.next()
        if t.kind != 'KW':
            raise JassError('statement expected, found %r on line %d' % (t, t.line))
        v = t.val
        if v == 'local':
            type_ = self.parse_type()
            is_array = bool(self.accept('KW', 'array'))
            name = self.expect('ID').val
            init = None
            if self.accept('OP', '='):
                init = self.parse_expr()
            self.expect('NL')
            return Node('LOCAL', type_, name, (is_array, init), line)
        if v == 'set':
            name = self.expect('ID').val
            idx = None
            if self.accept('OP', '['):
                idx = self.parse_expr()
                self.expect('OP', ']')
            self.expect('OP', '=')
            e = self.parse_expr()
            self.expect('NL')
            return Node('SET', name, idx, e, line)
        if v == 'call':
            e = self.parse_expr()
            self.expect('NL')
            return Node('CALLS', e, None, None, line)
        if v == 'if':
            branches = []
            cond = self.parse_expr()
            self.expect('KW', 'then')
            self.expect('NL')
            body = self.parse_block(('elseif', 'else', 'endif'))
            branches.append((cond, body))
            els = None
            while True:
                t2 = self.next()
                if t2.val == 'elseif':
                    cond = self.parse_expr()
                    self.expect('KW', 'then')
                    self.expect('NL')
                    body = self.parse_block(('elseif', 'else', 'endif'))
                    branches.append((cond, body))
                elif t2.val == 'else':
                    self.expect('NL')
                    els = self.parse_block(('endif',))
                    self.expect('KW', 'endif')
                    self.expect('NL')
                    break
                elif t2.val == 'endif':
                    self.expect('NL')
                    break
                else:
                    raise JassError('malformed if on line %d' % t2.line)
            return Node('IF', branches, els, None, line)
        if v == 'loop':
            self.expect('NL')
            body = self.parse_block(('endloop',))
            self.expect('KW', 'endloop')
            self.expect('NL')
            return Node('LOOP', body, None, None, line)
        if v == 'exitwhen':
            e = self.parse_expr()
            self.expect('NL')
            return Node('EXIT', e, None, None, line)
        if v == 'return':
            if self.peek().kind == 'NL':
                self.next()
                return Node('RET', None, None, None, line)
            e = self.parse_expr()
            self.expect('NL')
            return Node('RET', e, None, None, line)
        raise JassError('unknown statement %r on line %d' % (v, line))

    def parse_expr(self):
        return self.parse_or()

    def parse_or(self):
        e = self.parse_and()
        while self.peek().kind == 'KW' and self.peek().val == 'or':
            t = self.next()
            r = self.parse_and()
            e = Node('BIN', 'or', e, r, t.line)
        return e

    def parse_and(self):
        e = self.parse_cmp()
        while self.peek().kind == 'KW' and self.peek().val == 'and':
            t = self.next()
            r = self.parse_cmp()
            e = Node('BIN', 'and', e, r, t.line)
        return e

    def parse_cmp(self):
        e = self.parse_add()
        while self.peek().kind == 'OP' and self.peek().val in ('==', '!=', '<', '<=', '>', '>='):
            t = self.next()
            r = self.parse_add()
            e = Node('BIN', t.val, e, r, t.line)
        return e

    def parse_add(self):
        e = self.parse_mul()
        while self.peek().kind == 'OP' and self.peek().val in ('+', '-'):
            t = self.next()
            r = self.parse_mul()
            e = Node('BIN', t.val, e, r, t.line)
        return e

    def parse_mul(self):
        e = self.parse_unary()
        while self.peek().kind == 'OP' and self.peek().val in ('*', '/'):
            t = self.next()
            r = self.parse_unary()
            e = Node('BIN', t.val, e, r, t.line)
        return e

    def parse_unary(self):
        t = self.peek()
        if t.kind == 'OP' and t.val == '-':
            self.next()
            e = self.parse_unary()
            return Node('UN', '-', e, None, t.line)
        if t.kind == 'OP' and t.val == '+':
            self.next()
            return self.parse_unary()
        if t.kind == 'KW' and t.val == 'not':
            self.next()
            e = self.parse_unary()
            return Node('UN', 'not', e, None, t.line)
        return self.parse_primary()

    def parse_primary(self):
        t = self.next()
        if t.kind == 'INT':
            return Node('INT', t.val, None, None, t.line)
        if t.kind == 'REAL':
            return Node('REAL', t.val, None, None, t.line)
        if t.kind == 'STR':
            return Node('STR', t.val, None, None, t.line)
        if t.kind == 'KW':
            if t.val == 'true':
                return Node('BOOL', True, None, None, t.line)
            if t.val == 'false':
                return Node('BOOL', False, None, None, t.line)
            if t.val == 'null':
                return Node('NULL', None, None, None, t.line)
            if t.val == 'function':
                name = self.expect('ID').val
                return Node('FREF', name, None, None, t.line)
            raise JassError('unexpected keyword %r on line %d' % (t.val, t.line))
        if t.kind == 'OP' and t.val == '(':
            e = self.parse_expr()
            self.expect('OP', ')')
            return e
        if t.kind == 'ID':
            name = t.val
            if self.accept('OP', '('):
                args = []
                if not self.accept('OP', ')'):
                    while True:
                        args.append(self.parse_expr())
                        if self.accept('OP', ')'):
                            break
                        self.expect('OP', ',')
                return Node('CALL', name, args, None, t.line)
            if self.accept('OP', '['):
                idx = self.parse_expr()
                self.expect('OP', ']')
                return Node('IDX', name, idx, None, t.line)
            return Node('ID', name, None, None, t.line)
        raise JassError('invalid expression %r on line %d' % (t, t.line))


def lua_string(s):
    out = ['"']
    for ch in s:
        o = ord(ch)
        if ch == '"':
            out.append('\\"')
        elif ch == '\\':
            out.append('\\\\')
        elif ch == '\n':
            out.append('\\n')
        elif ch == '\r':
            out.append('\\r')
        elif ch == '\t':
            out.append('\\t')
        elif o < 32 or o == 127:
            out.append('\\%d' % o)
        else:
            out.append(ch)
    out.append('"')
    return ''.join(out)


def real_literal(text):
    if text.startswith('.'):
        text = '0' + text
    if text.endswith('.'):
        text = text + '0'
    return text


class Transpiler(object):
    CAT_MAX = 50

    def __init__(self, common_src, blizzard_src, map_src, overrides=None, drop_functions=None, translate=None):
        self.common_src = common_src
        self.blizzard_src = blizzard_src
        self.map_src = map_src
        self.overrides = overrides or {}
        self.translate = translate or {}
        self.translated_count = 0
        self.drop_functions = set(drop_functions or [])
        self.sigs = {}
        self.gtypes = {}
        self.warnings = []
        self.luachunks = []
        self.exs_literals = []
        self.map_natives = {}
        self.func_names = []

    def load_reference(self, src):
        p = Parser(lex(src)).parse()
        for g in p.globals:
            self.gtypes[g.name] = (g.type, g.is_array)
        for name, f in p.natives.items():
            self.sigs[name] = ([t for t, _ in f.params], f.ret)
        for f in p.functions:
            self.sigs[f.name] = ([t for t, _ in f.params], f.ret)

    def run(self):
        self.load_reference(self.common_src)
        self.load_reference(self.blizzard_src)
        p = Parser(lex(self.map_src)).parse()
        self.prog = p
        for name, f in p.natives.items():
            self.sigs[name] = ([t for t, _ in f.params], f.ret)
            self.map_natives[name] = f
        for f in p.functions:
            self.sigs[f.name] = ([t for t, _ in f.params], f.ret)
        self.map_globals = {}
        for g in p.globals:
            self.gtypes[g.name] = (g.type, g.is_array)
            self.map_globals[g.name] = g
        funcs_out = []
        for f in p.functions:
            if f.name in self.drop_functions:
                continue
            funcs_out.append(self.emit_function(f))
            self.func_names.append(f.name)
        missing_overrides = [n for n in self.overrides if n not in set(self.func_names)]
        self.missing_overrides = sorted(missing_overrides)
        if missing_overrides:
            self.warn('OVERRIDE without a matching function in the map: %s' % ', '.join(sorted(missing_overrides)))
        globals_out = self.emit_globals(p.globals)
        handle_globals = {}
        for g in p.globals:
            if g.type not in PRIMITIVES and not g.is_array:
                handle_globals[g.name] = g.type
        return {
            'lua_functions': '\n'.join(funcs_out),
            'lua_globals': globals_out,
            'luachunks': self.luachunks,
            'exs_literals': self.exs_literals,
            'handle_globals': handle_globals,
            'func_names': self.func_names,
            'overrides_without_target': self.missing_overrides,
            'warnings': self.warnings,
            'map_natives': {n: ([t for t, _ in f.params], f.ret) for n, f in self.map_natives.items()},
        }

    def local_type(self, name):
        if name in self.scope:
            return self.scope[name]
        return None

    def var_type(self, name):
        t = self.local_type(name)
        if t is not None:
            return t
        g = self.gtypes.get(name)
        if g:
            return g
        return ('unknown', False)

    def etype(self, e):
        k = e.k
        if k == 'INT':
            return 'integer'
        if k == 'REAL':
            return 'real'
        if k == 'STR':
            return 'string'
        if k == 'BOOL':
            return 'boolean'
        if k == 'NULL':
            return 'null'
        if k == 'ID':
            t, arr = self.var_type(e.a)
            if t == 'unknown':
                self.warn('unknown type for %s (line %d)' % (e.a, e.line))
            return t
        if k == 'IDX':
            t, arr = self.var_type(e.a)
            if t == 'unknown':
                self.warn('unknown type for array %s (line %d)' % (e.a, e.line))
            return t
        if k == 'CALL':
            s = self.sigs.get(e.a)
            if not s:
                self.warn('unknown function %s (line %d)' % (e.a, e.line))
                return 'unknown'
            return s[1]
        if k == 'FREF':
            return 'code'
        if k == 'UN':
            if e.a == 'not':
                return 'boolean'
            return self.etype(e.b)
        if k == 'BIN':
            op = e.a
            if op in ('==', '!=', '<', '<=', '>', '>=', 'and', 'or'):
                return 'boolean'
            ta = self.etype(e.b)
            tb = self.etype(e.c)
            if op == '+':
                if ta == 'string' or tb == 'string':
                    return 'string'
            if ta == 'real' or tb == 'real':
                return 'real'
            if ta == 'integer' and tb == 'integer':
                return 'integer'
            if ta == 'unknown' or tb == 'unknown':
                return 'unknown'
            return 'real'
        return 'unknown'

    def warn(self, msg):
        if len(self.warnings) < 500:
            self.warnings.append(msg)

    def name(self, n):
        base = n + '_' if n in LUA_KEYWORDS else n
        if n in getattr(self, 'spill', ()):
            return '__L.' + base
        return base

    def flatten_cat(self, e, out):
        if e.k == 'BIN' and e.a == '+' and self.is_string_add(e):
            self.flatten_cat(e.b, out)
            self.flatten_cat(e.c, out)
        else:
            out.append(e)

    def is_string_add(self, e):
        ta = self.etype(e.b)
        tb = self.etype(e.c)
        return ta == 'string' or tb == 'string' or (ta == 'null' and tb == 'null')

    def translate_literal(self, txt):
        if self.translate:
            t = self.translate.get(txt)
            if t is not None:
                self.translated_count += 1
                return t
        return txt

    def expr(self, e):
        k = e.k
        if k == 'INT':
            return str(e.a) if e.a >= 0 else '(%d)' % e.a
        if k == 'REAL':
            return real_literal(e.a)
        if k == 'STR':
            return lua_string(self.translate_literal(e.a))
        if k == 'BOOL':
            return 'true' if e.a else 'false'
        if k == 'NULL':
            return 'nil'
        if k == 'ID':
            return self.name(e.a)
        if k == 'IDX':
            return '%s[%s]' % (self.name(e.a), self.expr(e.b))
        if k == 'FREF':
            return self.name(e.a)
        if k == 'CALL':
            return self.call_expr(e)
        if k == 'UN':
            if e.a == 'not':
                return '(not %s)' % self.expr(e.b)
            return '(-%s)' % self.expr(e.b)
        if k == 'BIN':
            op = e.a
            if op == '+':
                if self.is_string_add(e):
                    parts = []
                    self.flatten_cat(e, parts)
                    return self.emit_cat(parts)
                ta = self.etype(e.b)
                tb = self.etype(e.c)
                if ta == 'integer' and tb == 'integer' and not (self.small_lit(e.b) or self.small_lit(e.c)):
                    return '__iadd(%s, %s)' % (self.expr(e.b), self.expr(e.c))
                return '(%s + %s)' % (self.expr(e.b), self.expr(e.c))
            if op == '-':
                ta = self.etype(e.b)
                tb = self.etype(e.c)
                if ta == 'integer' and tb == 'integer' and not (self.small_lit(e.b) or self.small_lit(e.c)):
                    return '__isub(%s, %s)' % (self.expr(e.b), self.expr(e.c))
                return '(%s - %s)' % (self.expr(e.b), self.expr(e.c))
            if op == '*':
                ta = self.etype(e.b)
                tb = self.etype(e.c)
                if ta == 'integer' and tb == 'integer':
                    return '__imul(%s, %s)' % (self.expr(e.b), self.expr(e.c))
                return '(%s * %s)' % (self.expr(e.b), self.expr(e.c))
            if op == '/':
                ta = self.etype(e.b)
                tb = self.etype(e.c)
                if ta == 'integer' and tb == 'integer':
                    return '__idiv(%s, %s)' % (self.expr(e.b), self.expr(e.c))
                if e.c.k in ('INT', 'REAL') and float(e.c.a) != 0.0:
                    return '(%s / %s)' % (self.expr(e.b), self.expr(e.c))
                return '__div(%s, %s)' % (self.expr(e.b), self.expr(e.c))
            if op in ('==', '!='):
                ta = self.etype(e.b)
                tb = self.etype(e.c)
                left = self.null_for(tb) if e.b.k == 'NULL' else self.expr(e.b)
                right = self.null_for(ta) if e.c.k == 'NULL' else self.expr(e.c)
                return '(%s %s %s)' % (left, '==' if op == '==' else '~=', right)
            if op in ('<', '<=', '>', '>='):
                return '(%s %s %s)' % (self.expr(e.b), op, self.expr(e.c))
            if op == 'and':
                return '(%s and %s)' % (self.expr(e.b), self.expr(e.c))
            if op == 'or':
                return '(%s or %s)' % (self.expr(e.b), self.expr(e.c))
            raise JassError('operator %r' % op)
        raise JassError('expression node %r' % k)

    def emit_cat(self, parts):
        if len(parts) <= self.CAT_MAX:
            return '__cat(%s)' % ', '.join(self.expr(p) for p in parts)
        chunks = []
        for i in range(0, len(parts), self.CAT_MAX):
            chunks.append('__cat(%s)' % ', '.join(self.expr(p) for p in parts[i:i + self.CAT_MAX]))
        return '__cat(%s)' % ', '.join(chunks)

    @staticmethod
    def small_lit(e):
        return e.k == 'INT' and -1048576 < e.a < 1048576

    def null_for(self, type_):
        if type_ == 'integer':
            return '0'
        if type_ == 'real':
            return '0.0'
        if type_ == 'boolean':
            return 'false'
        return 'nil'

    def expr_as(self, e, type_):
        if e.k == 'NULL':
            return self.null_for(type_)
        return self.expr(e)

    def call_expr(self, e):
        name = e.a
        if name == 'EXExecuteScript' and len(e.b) == 1 and e.b[0].k == 'STR':
            idx = len(self.exs_literals)
            self.exs_literals.append(e.b[0].a)
            return '__exs(%d)' % idx
        sig = self.sigs.get(name)
        parts = []
        for i, a in enumerate(e.b):
            if a.k == 'NULL' and sig and i < len(sig[0]):
                parts.append(self.null_for(sig[0][i]))
            else:
                parts.append(self.expr(a))
        return '%s(%s)' % (self.name(name), ', '.join(parts))

    def default_for(self, type_):
        if type_ == 'integer':
            return '0'
        if type_ == 'real':
            return '0.0'
        if type_ == 'boolean':
            return 'false'
        return None

    def array_ctor(self, type_):
        if type_ == 'integer':
            return '__arr_i()'
        if type_ == 'real':
            return '__arr_r()'
        if type_ == 'boolean':
            return '__arr_b()'
        return '{}'

    def emit_globals(self, globs):
        self.scope = {}
        out = []
        for g in globs:
            n = self.name(g.name)
            if g.is_array:
                out.append('%s = %s' % (n, self.array_ctor(g.type)))
                continue
            if g.init is not None:
                out.append('%s = %s' % (n, self.expr_as(g.init, g.type)))
                continue
            d = self.default_for(g.type)
            if d is not None:
                out.append('%s = %s' % (n, d))
        return '\n'.join(out)

    def emit_function(self, f):
        self.scope = {}
        self.cur_func = f
        self.spill = set()
        for t, n in f.params:
            self.scope[n] = (t, False)
        params = ', '.join(self.name(n) for _, n in f.params)
        head = 'function %s(%s)' % (self.name(f.name), params)
        if f.name in self.overrides:
            body = self.overrides[f.name]
            return '-- @jass %d (override)\n%s\n%s\nend' % (f.line, head, body)
        lines = ['-- @jass %d' % f.line, head]
        local_vars = [s.b for s in f.body if s.k == 'LOCAL']
        if len(f.params) + len(local_vars) > LOCALS_IN_LUA:
            self.spill = set(local_vars[max(0, LOCALS_IN_LUA - len(f.params)):])
            lines.append('  local __L = {}')
        self.emit_block(f.body, lines, 1, is_function_body=True)
        lines.append('end')
        return '\n'.join(lines)

    def emit_block(self, stmts, lines, depth, is_function_body=False):
        evidence = '  ' * depth
        stmts = self.fold_luachunks(stmts)
        n = len(stmts)
        for i, s in enumerate(stmts):
            k = s.k
            last = (i == n - 1)
            if k == 'LOCAL':
                type_, name = s.a, s.b
                is_array, init = s.c
                self.scope[name] = (type_, is_array)
                ln = self.name(name)
                decl = '' if name in self.spill else 'local '
                if is_array:
                    lines.append('%s%s%s = %s' % (evidence, decl, ln, self.array_ctor(type_)))
                elif init is not None:
                    lines.append('%s%s%s = %s' % (evidence, decl, ln, self.expr_as(init, type_)))
                else:
                    d = self.default_for(type_)
                    if d is not None:
                        lines.append('%s%s%s = %s' % (evidence, decl, ln, d))
                    elif decl:
                        lines.append('%slocal %s' % (evidence, ln))
            elif k == 'SET':
                vtype = self.var_type(s.a)[0]
                if s.b is None:
                    lines.append('%s%s = %s' % (evidence, self.name(s.a), self.expr_as(s.c, vtype)))
                else:
                    lines.append('%s%s[%s] = %s' % (evidence, self.name(s.a), self.expr(s.b), self.expr_as(s.c, vtype)))
            elif k == 'CALLS':
                e = s.a
                if e.k != 'CALL':
                    raise JassError('call without a function call on line %d' % s.line)
                lines.append('%s%s' % (evidence, self.call_expr(e)))
            elif k == 'LUACHUNK':
                lines.append('%s__luachunk(%d)' % (evidence, s.a))
            elif k == 'IF':
                first = True
                for cond, body in s.a:
                    kw = 'if' if first else 'elseif'
                    first = False
                    lines.append('%s%s %s then' % (evidence, kw, self.expr(cond)))
                    self.emit_block(body, lines, depth + 1)
                if s.b is not None:
                    lines.append('%selse' % evidence)
                    self.emit_block(s.b, lines, depth + 1)
                lines.append('%send' % evidence)
            elif k == 'LOOP':
                lines.append('%swhile true do' % evidence)
                self.emit_block(s.a, lines, depth + 1)
                lines.append('%send' % evidence)
            elif k == 'EXIT':
                lines.append('%sif %s then break end' % (evidence, self.expr(s.a)))
            elif k == 'RET':
                if s.a is None:
                    r = 'return'
                else:
                    r = 'return %s' % self.expr_as(s.a, self.cur_func.ret)
                if last:
                    lines.append('%s%s' % (evidence, r))
                else:
                    lines.append('%sdo %s end' % (evidence, r))
            else:
                raise JassError('unknown statement %r' % k)

    LUA_LOAD_FORMS = (
        ('lua_load([=[', ']=]'),
        ('lua_load(string.sub([====[!', '!]====]'),
    )

    def _lua_load_parts(self, e):
        if e.k != 'CALL' or e.a != 'EXExecuteScript' or len(e.b) != 1:
            return None
        arg = e.b[0]
        parts = []

        def flat(x):
            if x.k == 'BIN' and x.a == '+':
                flat(x.b)
                flat(x.c)
            else:
                parts.append(x)
        flat(arg)
        if len(parts) != 3:
            return None
        a, b, c = parts
        if a.k != 'STR' or b.k != 'ID' or c.k != 'STR':
            return None
        for pre, suf in self.LUA_LOAD_FORMS:
            if a.a.startswith(pre) and c.a.startswith(suf):
                return (b.a, 'true' in c.a)
        return None

    def fold_luachunks(self, stmts):
        out = []
        pending = {}
        i = 0
        n = len(stmts)
        while i < n:
            s = stmts[i]
            if s.k == 'SET' and s.b is None and s.c.k == 'STR':
                var = s.a
                nxt = stmts[i + 1] if i + 1 < n else None
                lp = self._lua_load_parts(nxt.a) if (nxt is not None and nxt.k == 'CALLS') else None
                if lp and lp[0] == var:
                    pending[var] = pending.get(var, '') + self.translate_literal(s.c.a)
                    if lp[1]:
                        idx = len(self.luachunks)
                        self.luachunks.append(pending.pop(var))
                        out.append(Node('LUACHUNK', idx, None, None, s.line))
                    i += 2
                    continue
            if s.k == 'LOCAL' and s.c[1] is not None and s.c[1].k == 'STR':
                var = s.b
                nxt = stmts[i + 1] if i + 1 < n else None
                lp = self._lua_load_parts(nxt.a) if (nxt is not None and nxt.k == 'CALLS') else None
                if lp and lp[0] == var:
                    out.append(Node('LOCAL', s.a, s.b, (False, None), s.line))
                    pending[var] = pending.get(var, '') + self.translate_literal(s.c[1].a)
                    if lp[1]:
                        idx = len(self.luachunks)
                        self.luachunks.append(pending.pop(var))
                        out.append(Node('LUACHUNK', idx, None, None, s.line))
                    i += 2
                    continue
            out.append(s)
            i += 1
        if pending:
            for var, code in pending.items():
                self.warn('lua_load without an end for %s in function %s' % (var, self.cur_func.name))
                idx = len(self.luachunks)
                self.luachunks.append(code)
                out.append(Node('LUACHUNK', idx, None, None, 0))
        return out


def read_text(path):
    return open(path, 'rb').read().decode('utf-8', 'surrogateescape')
