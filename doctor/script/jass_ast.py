# Parses JASS into a syntax tree that keeps every literal and comment.
import contextlib
import gc
import os
import re
import sys



HERE = os.path.dirname(os.path.abspath(__file__))
KEYWORDS = frozenset((
    'globals', 'endglobals', 'native', 'constant', 'type', 'extends', 'function', 'endfunction', 'takes', 'returns',
    'nothing', 'local', 'array', 'set', 'call', 'if', 'then', 'elseif', 'else', 'endif', 'loop', 'endloop',
    'exitwhen', 'return', 'debug', 'and', 'or', 'not', 'true', 'false', 'null'))

_TOKEN_BODY = (r'[A-Za-z_][A-Za-z0-9_]*+|[(),]|\r\n?|\n|[=!<>]=|<comment>[-+*/<>=\[\]]'
               r'|0[xX][0-9A-Fa-f]++|\$[0-9A-Fa-f]++|[0-9]++\.[0-9]*+|\.[0-9]++|[0-9]++'
               r'|"[^"\\]*(?:\\.[^"\\]*)*"|' r"'[^'\\]*(?:\\.[^'\\]*)*'" r'|[^ \t\N{BYTE ORDER MARK}]')
_TOKEN_RE = re.compile(r'[ \t\N{BYTE ORDER MARK}]*+(' + _TOKEN_BODY.replace('<comment>', r'//[^\r\n]*+|') + ')',
                       re.S)
_CANON_RE = re.compile(r'(?:[ \t\N{BYTE ORDER MARK}]++|//[^\r\n]*+)*+(' + _TOKEN_BODY.replace('<comment>', '') + ')',
                       re.S)
_NL = frozenset(('\n', '\r\n', '\r'))
_EOF = '\x00<eof>'
_BOM = '\N{BYTE ORDER MARK}'
_LINE_BREAK_RE = re.compile(r'\r\n?|\n')
_WORD_START = frozenset('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_')
_NUMBER_START = frozenset('0123456789.$')
_BINARY_PRECEDENCE = {'and': 1, 'or': 2, '==': 3, '!=': 3, '<': 3, '<=': 3, '>': 3, '>=': 3,
                      '+': 5, '-': 5, '*': 6, '/': 6}
_NOT_OPERAND = 5
_STRING_ESCAPES = {'n': '\n', 't': '\t', 'r': '\r', 'b': '\b', 'f': '\f', '"': '"', '\\': '\\', "'": "'"}


class JassSyntaxError(Exception):
    def __init__(self, line, message):
        Exception.__init__(self, 'line %d: %s' % (line, message))
        self.line = line
        self.message = message


def tokenize(text):
    return _TOKEN_RE.findall(text)


def _line_breaks(token):
    if '\n' not in token and '\r' not in token:
        return 0
    return len(_LINE_BREAK_RE.findall(token))


class Node(object):
    __slots__ = ()
    _fields = ()

    def __repr__(self):
        return '%s(%s)' % (type(self).__name__, ', '.join('%s=%r' % (f, getattr(self, f)) for f in self._fields))


class Expr(Node):
    __slots__ = ('line',)


class Name(Expr):
    __slots__ = ('name',)
    _fields = ('name',)

    def __init__(self, name, line=0):
        self.name = name
        self.line = line


class Index(Expr):
    __slots__ = ('base', 'index')
    _fields = ('base', 'index')

    def __init__(self, base, index, line=0):
        self.base = base
        self.index = index
        self.line = line


class Call(Expr):
    __slots__ = ('name', 'args')
    _fields = ('name', 'args')

    def __init__(self, name, args, line=0):
        self.name = name
        self.args = args
        self.line = line


class FuncRef(Expr):
    __slots__ = ('name',)
    _fields = ('name',)

    def __init__(self, name, line=0):
        self.name = name
        self.line = line


class Literal(Expr):
    __slots__ = ('kind', 'text')
    _fields = ('kind', 'text')

    def __init__(self, kind, text, line=0):
        self.kind = kind
        self.text = text
        self.line = line

    @property
    def value(self):
        return literal_value(self.kind, self.text)


class Unary(Expr):
    __slots__ = ('op', 'operand')
    _fields = ('op', 'operand')

    def __init__(self, op, operand, line=0):
        self.op = op
        self.operand = operand
        self.line = line


class Binary(Expr):
    __slots__ = ('op', 'left', 'right')
    _fields = ('op', 'left', 'right')

    def __init__(self, op, left, right, line=0):
        self.op = op
        self.left = left
        self.right = right
        self.line = line


class Paren(Expr):
    __slots__ = ('inner',)
    _fields = ('inner',)

    def __init__(self, inner, line=0):
        self.inner = inner
        self.line = line


def _wrap32(v):
    return ((v + 0x80000000) & 0xFFFFFFFF) - 0x80000000


def _unescape(body):
    out = []
    start = 0
    i = body.find('\\')
    while 0 <= i < len(body) - 1:
        out.append(body[start:i])
        c = body[i + 1]
        out.append(_STRING_ESCAPES.get(c, c))
        start = i + 2
        i = body.find('\\', start)
    out.append(body[start:])
    return ''.join(out)


def literal_value(kind, text):
    if kind == 'integer':
        if text[0] == '$':
            return _wrap32(int(text[1:], 16))
        if text[:2] in ('0x', '0X'):
            return _wrap32(int(text[2:], 16))
        if len(text) > 1 and text[0] == '0':
            try:
                return _wrap32(int(text, 8))
            except ValueError:
                pass
        return _wrap32(int(text))
    if kind == 'real':
        return float(text if text[0] != '.' else '0' + text)
    if kind == 'string':
        return _unescape(text[1:-1])
    if kind == 'rawcode':
        v = 0
        for b in _unescape(text[1:-1]).encode('utf-8', 'surrogateescape'):
            v = (v * 256 + (b - 256 if b >= 128 else b)) & 0xFFFFFFFF
        return _wrap32(v)
    if kind == 'boolean':
        return text == 'true'
    return None


class Stmt(Node):
    __slots__ = ('line', 'comment', 'leading_comments')


class SetStmt(Stmt):
    __slots__ = ('target', 'value')
    _fields = ('target', 'value')

    def __init__(self, target, value, line=0):
        self.target = target
        self.value = value
        self.line = line
        self.comment = None
        self.leading_comments = []


class CallStmt(Stmt):
    __slots__ = ('call',)
    _fields = ('call',)

    def __init__(self, call, line=0):
        self.call = call
        self.line = line
        self.comment = None
        self.leading_comments = []


class IfStmt(Stmt):
    __slots__ = ('branches', 'branch_lines', 'branch_comments', 'end_line', 'end_comment')
    _fields = ('branches',)

    def __init__(self, branches, line=0):
        self.branches = branches
        self.line = line
        self.comment = None
        self.leading_comments = []
        self.branch_lines = []
        self.branch_comments = []
        self.end_line = line
        self.end_comment = None


class LoopStmt(Stmt):
    __slots__ = ('body', 'end_line', 'end_comment')
    _fields = ('body',)

    def __init__(self, body, line=0):
        self.body = body
        self.line = line
        self.comment = None
        self.leading_comments = []
        self.end_line = line
        self.end_comment = None


class ExitWhenStmt(Stmt):
    __slots__ = ('cond',)
    _fields = ('cond',)

    def __init__(self, cond, line=0):
        self.cond = cond
        self.line = line
        self.comment = None
        self.leading_comments = []


class ReturnStmt(Stmt):
    __slots__ = ('value',)
    _fields = ('value',)

    def __init__(self, value, line=0):
        self.value = value
        self.line = line
        self.comment = None
        self.leading_comments = []


class CommentStmt(Stmt):
    __slots__ = ('text',)
    _fields = ('text',)

    def __init__(self, text, line=0):
        self.text = text
        self.line = line
        self.comment = None
        self.leading_comments = []


class DebugStmt(Stmt):
    __slots__ = ('stmt',)
    _fields = ('stmt',)

    def __init__(self, stmt, line=0):
        self.stmt = stmt
        self.line = line
        self.comment = None
        self.leading_comments = []


class GlobalDecl(Node):
    __slots__ = ('name', 'type', 'is_array', 'is_constant', 'initializer', 'line', 'comment', 'leading_comments')
    _fields = ('name', 'type', 'is_array', 'is_constant', 'initializer')

    def __init__(self, name, type_, is_array, is_constant, initializer, line=0):
        self.name = name
        self.type = type_
        self.is_array = is_array
        self.is_constant = is_constant
        self.initializer = initializer
        self.line = line
        self.comment = None
        self.leading_comments = []


class LocalDecl(Node):
    __slots__ = ('name', 'type', 'is_array', 'initializer', 'line', 'comment', 'leading_comments')
    _fields = ('name', 'type', 'is_array', 'initializer')

    def __init__(self, name, type_, is_array, initializer, line=0):
        self.name = name
        self.type = type_
        self.is_array = is_array
        self.initializer = initializer
        self.line = line
        self.comment = None
        self.leading_comments = []


class TypeDecl(Node):
    __slots__ = ('name', 'base', 'line', 'comment', 'leading_comments')
    _fields = ('name', 'base')

    def __init__(self, name, base, line=0):
        self.name = name
        self.base = base
        self.line = line
        self.comment = None
        self.leading_comments = []


class Globals(Node):
    __slots__ = ('decls', 'line', 'end_line', 'comment', 'end_comment', 'leading_comments', 'end_comments')
    _fields = ('decls',)

    def __init__(self, line=0):
        self.decls = []
        self.line = line
        self.end_line = line
        self.comment = None
        self.end_comment = None
        self.leading_comments = []
        self.end_comments = []


class Function(Node):
    __slots__ = ('name', 'params', 'return_type', 'locals', 'body', 'line', 'end_line', 'is_native', 'is_constant',
                 'comment', 'end_comment', 'leading_comments')
    _fields = ('name', 'params', 'return_type', 'is_native')

    def __init__(self, name='', line=0, is_native=False, is_constant=False):
        self.name = name
        self.params = []
        self.return_type = 'nothing'
        self.locals = []
        self.body = []
        self.line = line
        self.end_line = line
        self.is_native = is_native
        self.is_constant = is_constant
        self.comment = None
        self.end_comment = None
        self.leading_comments = []


class Script(Node):
    __slots__ = ('items', 'globals', 'functions', 'types', 'natives', 'comments', 'function_index', 'global_index',
                 'end_comments')
    _fields = ('items',)

    def __init__(self):
        self.items = []
        self.globals = []
        self.functions = []
        self.types = []
        self.natives = []
        self.comments = []
        self.function_index = {}
        self.global_index = {}
        self.end_comments = []


_END_FUNCTION = frozenset(('endfunction',))
_END_IF = frozenset(('elseif', 'else', 'endif'))
_END_ELSE = frozenset(('endif',))
_END_LOOP = frozenset(('endloop',))
_BLOCK_WORDS = frozenset(('endfunction', 'endif', 'endloop', 'else', 'elseif', 'globals', 'endglobals', 'function',
                          'native', 'type', 'constant'))
_CLOSERS = {Function: ('endfunction', 'function'), IfStmt: ('endif', 'if'), LoopStmt: ('endloop', 'loop')}


class _Parser(object):
    __slots__ = ('toks', 'i', 'line')

    def __init__(self, text):
        toks = _TOKEN_RE.findall(text)
        toks.append(_EOF)
        self.toks = toks
        self.i = 0
        self.line = 1

    def error(self, message):
        raise JassSyntaxError(self.line, message)

    def found(self):
        t = self.toks[self.i]
        if t == _EOF:
            return 'end of file'
        if t in _NL:
            return 'end of line'
        return repr(t)

    def expect(self, value):
        if self.toks[self.i] != value:
            self.error('expected %r, found %s' % (value, self.found()))
        self.i += 1

    def identifier(self):
        t = self.toks[self.i]
        if t[0] in _WORD_START and t not in KEYWORDS:
            self.i += 1
            return t
        self.error('expected a name, found %s' % self.found())

    def end_of_line(self):
        toks = self.toks
        t = toks[self.i]
        comment = None
        if t[:2] == '//':
            comment = t
            self.i += 1
            t = toks[self.i]
        if t in _NL:
            self.i += 1
            self.line += 1
        elif t != _EOF:
            self.error('unexpected %s' % self.found())
        return comment

    def script(self):
        toks = self.toks
        s = Script()
        pending = []
        while True:
            t = toks[self.i]
            if t in _NL:
                self.i += 1
                self.line += 1
                continue
            if t == _EOF:
                break
            if t[:2] == '//':
                s.comments.append(CommentStmt(t, self.line))
                pending.append(t)
                self.i += 1
                self.end_of_line()
                continue
            line = self.line
            is_constant = t == 'constant'
            if is_constant:
                self.i += 1
                t = toks[self.i]
            if t == 'function':
                item = self.function(line, is_constant)
                s.functions.append(item)
            elif t == 'native':
                item = self.native(line, is_constant)
                s.natives.append(item)
            elif t == 'globals' and not is_constant:
                item = self.globals_block()
                s.globals.extend(item.decls)
            elif t == 'type' and not is_constant:
                item = self.type_decl()
                s.types.append(item)
            else:
                self.error('unexpected %s at the top level' % self.found())
            item.leading_comments = pending
            pending = []
            s.items.append(item)
        s.end_comments = pending
        for f in s.natives + s.functions:
            s.function_index.setdefault(f.name, f)
        for g in s.globals:
            s.global_index.setdefault(g.name, g)
        return s

    def type_decl(self):
        line = self.line
        self.i += 1
        name = self.identifier()
        self.expect('extends')
        d = TypeDecl(name, self.identifier(), line)
        d.comment = self.end_of_line()
        return d

    def globals_block(self):
        toks = self.toks
        g = Globals(self.line)
        self.i += 1
        g.comment = self.end_of_line()
        pending = []
        while True:
            t = toks[self.i]
            if t in _NL:
                self.i += 1
                self.line += 1
                continue
            if t[:2] == '//':
                pending.append(t)
                self.i += 1
                self.end_of_line()
                continue
            if t == 'endglobals':
                g.end_line = self.line
                g.end_comments = pending
                self.i += 1
                g.end_comment = self.end_of_line()
                return g
            if t == _EOF:
                self.error('missing endglobals (the block opens at line %d)' % g.line)
            line = self.line
            is_constant = t == 'constant'
            if is_constant:
                self.i += 1
            type_ = self.identifier()
            is_array = toks[self.i] == 'array'
            if is_array:
                self.i += 1
            name = self.identifier()
            init = None
            if toks[self.i] == '=':
                self.i += 1
                init = self.expression(0)
            d = GlobalDecl(name, type_, is_array, is_constant, init, line)
            d.leading_comments = pending
            pending = []
            d.comment = self.end_of_line()
            g.decls.append(d)

    def signature(self, f):
        toks = self.toks
        f.name = self.identifier()
        self.expect('takes')
        if toks[self.i] == 'nothing':
            self.i += 1
        else:
            while True:
                ptype = self.identifier()
                f.params.append((ptype, self.identifier()))
                if toks[self.i] != ',':
                    break
                self.i += 1
        self.expect('returns')
        if toks[self.i] == 'nothing':
            self.i += 1
        else:
            f.return_type = self.identifier()
        f.comment = self.end_of_line()

    def native(self, line, is_constant):
        self.i += 1
        f = Function('', line, True, is_constant)
        self.signature(f)
        return f

    def function(self, line, is_constant):
        toks = self.toks
        self.i += 1
        f = Function('', line, False, is_constant)
        self.signature(f)
        pending = []
        while True:
            t = toks[self.i]
            if t in _NL:
                self.i += 1
                self.line += 1
            elif t[:2] == '//':
                pending.append(CommentStmt(t, self.line))
                self.i += 1
                self.end_of_line()
            elif t == 'local':
                d = self.local_decl()
                d.leading_comments = [c.text for c in pending]
                pending = []
                f.locals.append(d)
            else:
                break
        f.body = self.block(pending, _END_FUNCTION, f)
        f.end_line = self.line
        self.i += 1
        f.end_comment = self.end_of_line()
        return f

    def local_decl(self):
        toks = self.toks
        line = self.line
        self.i += 1
        type_ = self.identifier()
        is_array = toks[self.i] == 'array'
        if is_array:
            self.i += 1
        name = self.identifier()
        init = None
        if toks[self.i] == '=':
            self.i += 1
            init = self.expression(0)
        d = LocalDecl(name, type_, is_array, init, line)
        d.comment = self.end_of_line()
        return d

    def block(self, body, enders, opener):
        toks = self.toks
        handlers = _STATEMENTS
        while True:
            t = toks[self.i]
            if t in _NL:
                self.i += 1
                self.line += 1
                continue
            h = handlers.get(t)
            if h is not None:
                body.append(h(self))
            elif t in enders:
                return body
            elif t[:2] == '//':
                body.append(CommentStmt(t, self.line))
                self.i += 1
                self.end_of_line()
            elif t == 'local':
                self.error('local declaration after the first statement')
            elif t == _EOF or t in _BLOCK_WORDS:
                end, what = _CLOSERS[type(opener)]
                self.error('missing %s for the %s at line %d, found %s' % (end, what, opener.line, self.found()))
            else:
                self.error('unexpected %s at the start of a statement' % self.found())

    def set_stmt(self):
        line = self.line
        self.i += 1
        target = Name(self.identifier(), line)
        if self.toks[self.i] == '[':
            self.i += 1
            target = Index(target, self.expression(0), line)
            self.expect(']')
        self.expect('=')
        s = SetStmt(target, self.expression(0), line)
        s.comment = self.end_of_line()
        return s

    def call_stmt(self):
        line = self.line
        self.i += 1
        name = self.identifier()
        self.expect('(')
        s = CallStmt(Call(name, self.arguments(), line), line)
        s.comment = self.end_of_line()
        return s

    def if_stmt(self):
        toks = self.toks
        line = self.line
        self.i += 1
        cond = self.expression(0)
        self.expect('then')
        s = IfStmt([], line)
        s.comment = self.end_of_line()
        s.branch_lines.append(line)
        s.branch_comments.append(s.comment)
        s.branches.append((cond, self.block([], _END_IF, s)))
        while True:
            t = toks[self.i]
            branch_line = self.line
            self.i += 1
            if t == 'elseif':
                cond = self.expression(0)
                self.expect('then')
                s.branch_comments.append(self.end_of_line())
                s.branch_lines.append(branch_line)
                s.branches.append((cond, self.block([], _END_IF, s)))
            elif t == 'else':
                s.branch_comments.append(self.end_of_line())
                s.branch_lines.append(branch_line)
                s.branches.append((None, self.block([], _END_ELSE, s)))
            else:
                s.end_line = branch_line
                s.end_comment = self.end_of_line()
                return s

    def loop_stmt(self):
        line = self.line
        self.i += 1
        s = LoopStmt([], line)
        s.comment = self.end_of_line()
        self.block(s.body, _END_LOOP, s)
        s.end_line = self.line
        self.i += 1
        s.end_comment = self.end_of_line()
        return s

    def exitwhen_stmt(self):
        line = self.line
        self.i += 1
        s = ExitWhenStmt(self.expression(0), line)
        s.comment = self.end_of_line()
        return s

    def return_stmt(self):
        line = self.line
        self.i += 1
        t = self.toks[self.i]
        value = None
        if t not in _NL and t != _EOF and t[:2] != '//':
            value = self.expression(0)
        s = ReturnStmt(value, line)
        s.comment = self.end_of_line()
        return s

    def debug_stmt(self):
        line = self.line
        self.i += 1
        h = _STATEMENTS.get(self.toks[self.i])
        if h is None or h is _Parser.debug_stmt:
            self.error('expected a statement after debug, found %s' % self.found())
        return DebugStmt(h(self), line)

    def expression(self, min_precedence):
        left = self.unary()
        op = self.toks[self.i]
        p = _BINARY_PRECEDENCE.get(op)
        while p is not None and p >= min_precedence:
            self.i += 1
            left = Binary(op, left, self.expression(p + 1), left.line)
            op = self.toks[self.i]
            p = _BINARY_PRECEDENCE.get(op)
        return left

    def unary(self):
        toks = self.toks
        i = self.i
        t = toks[i]
        c = t[0]
        if c in _WORD_START and t not in KEYWORDS:
            nxt = toks[i + 1]
            if nxt == '(':
                line = self.line
                self.i = i + 2
                return Call(t, self.arguments(), line)
            if nxt == '[':
                line = self.line
                self.i = i + 2
                index = Index(Name(t, line), self.expression(0), line)
                self.expect(']')
                return index
            self.i = i + 1
            return Name(t, self.line)
        line = self.line
        if t == '(':
            self.i = i + 1
            inner = self.expression(0)
            self.expect(')')
            return Paren(inner, line)
        if '0' <= c <= '9' or c in _NUMBER_START and len(t) > 1:
            self.i = i + 1
            return Literal('real' if '.' in t else 'integer', t, line)
        if c == '"' or c == "'":
            if len(t) < 2:
                self.error('unterminated %s literal' % ('string' if c == '"' else 'rawcode'))
            self.i = i + 1
            if '\n' in t or '\r' in t:
                self.line += _line_breaks(t)
            return Literal('string' if c == '"' else 'rawcode', t, line)
        if t == 'not':
            self.i = i + 1
            return Unary('not', self.expression(_NOT_OPERAND), line)
        if t == '-' or t == '+':
            self.i = i + 1
            return Unary(t, self.unary(), line)
        if t == 'true' or t == 'false':
            self.i = i + 1
            return Literal('boolean', t, line)
        if t == 'null':
            self.i = i + 1
            return Literal('null', t, line)
        if t == 'function':
            self.i = i + 1
            return FuncRef(self.identifier(), line)
        self.error('unexpected %s in an expression' % self.found())

    def arguments(self):
        toks = self.toks
        if toks[self.i] == ')':
            self.i += 1
            return []
        args = [self.expression(0)]
        while True:
            t = toks[self.i]
            if t == ',':
                self.i += 1
                args.append(self.expression(0))
            elif t == ')':
                self.i += 1
                return args
            else:
                self.error('expected , or ) in the arguments, found %s' % self.found())


_STATEMENTS = {'set': _Parser.set_stmt, 'call': _Parser.call_stmt, 'if': _Parser.if_stmt, 'loop': _Parser.loop_stmt,
               'exitwhen': _Parser.exitwhen_stmt, 'return': _Parser.return_stmt, 'debug': _Parser.debug_stmt}


@contextlib.contextmanager
def _tree_work():
    if sys.getrecursionlimit() < 20000:
        sys.setrecursionlimit(20000)
    enabled = gc.isenabled()
    gc.disable()
    try:
        yield
    finally:
        if enabled:
            gc.enable()


def parse(text):
    if text[:1] == _BOM:
        text = text[1:]
    with _tree_work():
        if len(text) >= NATIVE_MIN:
            tree = _parse_native(text)
            if tree is not None:
                return tree
        return _Parser(text).script()


NATIVE_MIN = 16384
_NATIVE = [None]
_KINDS = ('integer', 'real', 'string', 'rawcode', 'boolean', 'null')
_OPS = ('and', 'or', '==', '!=', '<', '<=', '>', '>=', '+', '-', '*', '/', 'not')
_ESCAPED_BOM = b'\xef\xbb\xbf'


def _native():
    if _NATIVE[0] is None:
        _NATIVE[0] = False
        if os.environ.get('JASS_NATIVE') != '0' and sys.platform != 'emscripten':
            try:
                import ctypes
                from doctor.script import jass_native
                dll = jass_native._dll()
                if dll and hasattr(dll, 'jass_parse_tree'):
                    f = dll.jass_parse_tree
                    f.argtypes = [ctypes.c_char_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_void_p),
                                  ctypes.POINTER(ctypes.c_size_t)]
                    f.restype = ctypes.c_int
                    _NATIVE[0] = (f, dll.jass_free, ctypes)
            except Exception:
                _NATIVE[0] = False
    return _NATIVE[0]


NOT_DONE = object()


def _native_bytes(text):
    try:
        b = text.encode('latin-1')
        if _ESCAPED_BOM not in b:
            return b, True
    except UnicodeEncodeError:
        pass
    try:
        b = text.encode('utf-8', 'surrogateescape')
    except UnicodeEncodeError:
        return None
    if b.decode('utf-8', 'surrogateescape') != text:
        return None
    return b, False


def _parse_native(text):
    nat = _native()
    if not nat:
        return None
    enc = _native_bytes(text)
    if enc is None:
        return None
    f, free, ctypes = nat
    data, latin = enc
    p, n = ctypes.c_void_p(), ctypes.c_size_t()
    if f(data, len(data), ctypes.byref(p), ctypes.byref(n)) != 0:
        return None
    try:
        buf = ctypes.string_at(p.value, n.value)
    finally:
        free(p, n.value)
    return _decode_tree(buf, latin)


def _decode_tree(buf, latin):
    import array
    import collections
    import itertools
    count = int.from_bytes(buf[:4], 'little')
    offs = array.array('I')
    offs.frombytes(buf[4:8 + 4 * count])
    if sys.byteorder != 'little':
        offs.byteswap()
    start = 8 + 4 * count
    end = start + offs[-1]
    if latin:
        blob = buf[start:end].decode('latin-1')
        strs = [None] + [blob[offs[k]:offs[k + 1]] for k in range(count)]
    else:
        blob = buf[start:end]
        strs = [None] + [blob[offs[k]:offs[k + 1]].decode('utf-8', 'surrogateescape') for k in range(count)]
    del blob
    v = array.array('i')
    v.frombytes(buf[(end + 3) & ~3:])
    if sys.byteorder != 'little':
        v.byteswap()
    v = v.tolist()
    sget = strs.__getitem__
    objs = [None]
    get = objs.__getitem__
    kinds, ops = _KINDS, _OPS
    drain = collections.deque(maxlen=0).extend
    repeat = itertools.repeat
    accumulate = itertools.accumulate

    def comments(group, cols):
        if any(cols):
            drain(map(setattr, group, repeat('comment'), map(sget, cols)))

    def lists(kd, counts):
        flat = list(map(get, kd))
        ends = list(accumulate(counts))
        return map(flat.__getitem__, map(slice, [0] + ends[:-1], ends))

    ngroups = v[0]
    i = 1
    for _g in range(ngroups):
        ty, n, ns, nk = v[i:i + 4]
        i += 4
        sc = v[i:i + ns]
        i += ns
        kd = v[i:i + nk]
        i += nk
        if ty == 1:
            objs += map(Name, map(sget, sc[0::2]), sc[1::2])
        elif ty == 3:
            objs += map(Literal, map(kinds.__getitem__, sc[0::3]), map(sget, sc[1::3]), sc[2::3])
        elif ty == 2:
            objs += map(Call, map(sget, sc[0::3]), lists(kd, sc[2::3]), sc[1::3])
        elif ty == 4:
            objs += map(Binary, map(ops.__getitem__, sc[0::2]), map(get, kd[0::2]), map(get, kd[1::2]), sc[1::2])
        elif ty == 11 or ty == 12 or ty == 13:
            group = list(map(CallStmt if ty == 11 else ExitWhenStmt if ty == 12 else ReturnStmt, map(get, kd),
                             sc[0::2]))
            comments(group, sc[1::2])
            objs += group
        elif ty == 10:
            group = list(map(SetStmt, map(get, kd[0::2]), map(get, kd[1::2]), sc[0::2]))
            comments(group, sc[1::2])
            objs += group
        elif ty == 6:
            objs += map(Paren, map(get, kd), sc)
        elif ty == 5:
            objs += map(Unary, map(ops.__getitem__, sc[0::2]), map(get, kd), sc[1::2])
        elif ty == 7:
            objs += map(Index, map(get, kd[0::2]), map(get, kd[1::2]), sc)
        elif ty == 8:
            objs += map(FuncRef, map(sget, sc[0::2]), sc[1::2])
        elif ty == 14:
            objs += map(CommentStmt, map(sget, sc[0::2]), sc[1::2])
        elif ty == 15:
            objs += map(DebugStmt, map(get, kd), sc)
        elif ty == 20 or ty == 21:
            p = 0
            for k in range(n):
                if ty == 20:
                    name, type_, is_array, line, comment = sc[p:p + 5]
                    p += 5
                    d = LocalDecl(strs[name], strs[type_], bool(is_array), objs[kd[k]], line)
                else:
                    name, type_, is_array, is_constant, line, comment = sc[p:p + 6]
                    p += 6
                    d = GlobalDecl(strs[name], strs[type_], bool(is_array), bool(is_constant), objs[kd[k]], line)
                d.comment = strs[comment]
                m = sc[p]
                if m:
                    d.leading_comments = list(map(sget, sc[p + 1:p + 1 + m]))
                p += 1 + m
                objs.append(d)
        elif ty == 16:
            group = list(map(LoopStmt, lists(kd, sc[4::5]), sc[0::5]))
            comments(group, sc[1::5])
            drain(map(setattr, group, repeat('end_line'), sc[2::5]))
            if any(sc[3::5]):
                drain(map(setattr, group, repeat('end_comment'), map(sget, sc[3::5])))
            objs += group
        elif ty == 17:
            p = q = 0
            for _k in range(n):
                line, comment, end_line, end_comment, nb = sc[p:p + 5]
                p += 5
                s = IfStmt([], line)
                s.comment = strs[comment]
                s.end_line = end_line
                s.end_comment = strs[end_comment]
                branches = s.branches
                for _b in range(nb):
                    has, nbody, bline, bcomment = sc[p:p + 4]
                    p += 4
                    cond = None
                    if has:
                        cond = objs[kd[q]]
                        q += 1
                    branches.append((cond, list(map(get, kd[q:q + nbody]))))
                    q += nbody
                    s.branch_lines.append(bline)
                    s.branch_comments.append(strs[bcomment])
                objs.append(s)
        elif ty == 22:
            p = q = 0
            for _k in range(n):
                name, line, end_line, is_native, is_constant, comment, end_comment, ret, nparams = sc[p:p + 9]
                p += 9
                f = Function(strs[name], line, bool(is_native), bool(is_constant))
                f.end_line = end_line
                f.comment = strs[comment]
                f.end_comment = strs[end_comment]
                f.return_type = strs[ret]
                if nparams:
                    pv = sc[p:p + 2 * nparams]
                    f.params = list(zip(map(sget, pv[0::2]), map(sget, pv[1::2])))
                    p += 2 * nparams
                m = sc[p]
                if m:
                    f.leading_comments = list(map(sget, sc[p + 1:p + 1 + m]))
                p += 1 + m
                nlocals, nbody = sc[p], sc[p + 1]
                p += 2
                if nlocals:
                    f.locals = list(map(get, kd[q:q + nlocals]))
                    q += nlocals
                if nbody:
                    f.body = list(map(get, kd[q:q + nbody]))
                    q += nbody
                objs.append(f)
        elif ty == 23:
            p = q = 0
            for _k in range(n):
                g = Globals(sc[p])
                g.end_line = sc[p + 1]
                g.comment = strs[sc[p + 2]]
                g.end_comment = strs[sc[p + 3]]
                p += 4
                m = sc[p]
                if m:
                    g.end_comments = list(map(sget, sc[p + 1:p + 1 + m]))
                p += 1 + m
                m = sc[p]
                if m:
                    g.leading_comments = list(map(sget, sc[p + 1:p + 1 + m]))
                p += 1 + m
                m = sc[p]
                p += 1
                if m:
                    g.decls = list(map(get, kd[q:q + m]))
                    q += m
                objs.append(g)
        elif ty == 24:
            p = 0
            for _k in range(n):
                d = TypeDecl(strs[sc[p]], strs[sc[p + 1]], sc[p + 2])
                d.comment = strs[sc[p + 3]]
                m = sc[p + 4]
                if m:
                    d.leading_comments = list(map(sget, sc[p + 5:p + 5 + m]))
                p += 5 + m
                objs.append(d)
        else:
            raise ValueError('jass_ast: a native tree stream with node type %r' % (ty,))
    s = Script()
    k = v[i]
    i += 1
    s.comments = list(map(CommentStmt, map(sget, v[i:i + 2 * k:2]), v[i + 1:i + 2 * k:2]))
    i += 2 * k
    k = v[i]
    s.end_comments = list(map(sget, v[i + 1:i + 1 + k]))
    i += 1 + k
    k = v[i]
    s.items = list(map(get, v[i + 1:i + 1 + k]))
    for item in s.items:
        t = type(item)
        if t is Function:
            (s.natives if item.is_native else s.functions).append(item)
        elif t is Globals:
            s.globals.extend(item.decls)
        else:
            s.types.append(item)
    for f in s.natives + s.functions:
        s.function_index.setdefault(f.name, f)
    for g in s.globals:
        s.global_index.setdefault(g.name, g)
    return s


def _branch_children(n):
    out = []
    for cond, body in n.branches:
        if cond is not None:
            out.append(cond)
        out.extend(body)
    return out


_CHILDREN = {
    Script: lambda n: n.items,
    Globals: lambda n: n.decls,
    Function: lambda n: n.locals + n.body,
    TypeDecl: lambda n: [],
    GlobalDecl: lambda n: [] if n.initializer is None else [n.initializer],
    LocalDecl: lambda n: [] if n.initializer is None else [n.initializer],
    SetStmt: lambda n: [n.target, n.value],
    CallStmt: lambda n: [n.call],
    IfStmt: _branch_children,
    LoopStmt: lambda n: n.body,
    ExitWhenStmt: lambda n: [n.cond],
    ReturnStmt: lambda n: [] if n.value is None else [n.value],
    CommentStmt: lambda n: [],
    DebugStmt: lambda n: [n.stmt],
    Name: lambda n: [],
    Index: lambda n: [n.base, n.index],
    Call: lambda n: n.args,
    FuncRef: lambda n: [],
    Literal: lambda n: [],
    Unary: lambda n: [n.operand],
    Binary: lambda n: [n.left, n.right],
    Paren: lambda n: [n.inner],
}


def children(node):
    return list(_CHILDREN[type(node)](node))


_STACKED = {
    Script: lambda n: n.items[::-1],
    Globals: lambda n: n.decls[::-1],
    Function: lambda n: (n.locals + n.body)[::-1],
    TypeDecl: None,
    GlobalDecl: lambda n: () if n.initializer is None else (n.initializer,),
    LocalDecl: lambda n: () if n.initializer is None else (n.initializer,),
    SetStmt: lambda n: (n.value, n.target),
    CallStmt: lambda n: (n.call,),
    IfStmt: lambda n: _branch_children(n)[::-1],
    LoopStmt: lambda n: n.body[::-1],
    ExitWhenStmt: lambda n: (n.cond,),
    ReturnStmt: lambda n: () if n.value is None else (n.value,),
    CommentStmt: None,
    DebugStmt: lambda n: (n.stmt,),
    Name: None,
    Index: lambda n: (n.index, n.base),
    Call: lambda n: n.args[::-1],
    FuncRef: None,
    Literal: None,
    Unary: lambda n: (n.operand,),
    Binary: lambda n: (n.right, n.left),
    Paren: lambda n: (n.inner,),
}


def walk(node):
    stack = [node]
    pop, extend, stacked = stack.pop, stack.extend, _STACKED.__getitem__
    while stack:
        n = pop()
        yield n
        f = stacked(type(n))
        if f is not None:
            extend(f(n))


_ASSOCIATIVE = frozenset(('+', '*', 'and', 'or'))


def _needs_parens(child, parent, right):
    p, q = _BINARY_PRECEDENCE[child.op], _BINARY_PRECEDENCE[parent.op]
    return p < q or (right and p == q and not (child.op == parent.op and child.op in _ASSOCIATIVE))


def _ue(e):
    t = type(e)
    if t is Name:
        return e.name
    if t is Call:
        return e.name + '(' + ', '.join([_ue(a) for a in e.args]) + ')'
    if t is Literal:
        return e.text
    if t is Binary:
        chain = []
        while type(e) is Binary:
            chain.append(e)
            e = e.left
        chain.reverse()
        text = _ue(e)
        if type(e) is Binary and _needs_parens(e, chain[0], False):
            text = '(' + text + ')'
        for k, b in enumerate(chain):
            right = _ue(b.right)
            if type(b.right) is Binary and _needs_parens(b.right, b, True):
                right = '(' + right + ')'
            text = text + ' ' + b.op + ' ' + right
            if k + 1 < len(chain) and _needs_parens(b, chain[k + 1], False):
                text = '(' + text + ')'
        return text
    if t is Paren:
        return '(' + _ue(e.inner) + ')'
    if t is Index:
        return _ue(e.base) + '[' + _ue(e.index) + ']'
    if t is Unary:
        inner = _ue(e.operand)
        if type(e.operand) is Binary and (e.op != 'not' or _BINARY_PRECEDENCE[e.operand.op] < _NOT_OPERAND):
            inner = '(' + inner + ')'
        return ('not ' if e.op == 'not' else e.op) + inner
    if t is FuncRef:
        return 'function ' + e.name
    raise TypeError('not a JASS expression: %r' % (e,))


def _with_comment(text, comment, comments):
    return text + ' ' + comment if comment and comments else text


def _decl_text(d):
    head = ('constant ' if getattr(d, 'is_constant', False) else '') + d.type + (' array ' if d.is_array else ' ')
    head += d.name
    if d.initializer is not None:
        head += ' = ' + _ue(d.initializer)
    return head


def _signature_text(f):
    params = ', '.join(t + ' ' + n for t, n in f.params) if f.params else 'nothing'
    return ('constant ' if f.is_constant else '') + ('native ' if f.is_native else 'function ') + f.name + \
        ' takes ' + params + ' returns ' + f.return_type


def _unparse_stmt(s, ind, out, comments, prefix=''):
    if comments:
        for c in s.leading_comments:
            out.append(ind + c)
    t = type(s)
    if t is CallStmt:
        text = 'call ' + _ue(s.call)
    elif t is SetStmt:
        text = 'set ' + _ue(s.target) + ' = ' + _ue(s.value)
    elif t is IfStmt:
        inner = ind + '    '
        for k, (cond, body) in enumerate(s.branches):
            if k == 0:
                head = prefix + 'if ' + _ue(cond) + ' then'
            elif cond is None:
                head = 'else'
            else:
                head = 'elseif ' + _ue(cond) + ' then'
            c = s.comment if k == 0 else s.branch_comments[k] if k < len(s.branch_comments) else None
            out.append(ind + _with_comment(head, c, comments))
            for b in body:
                _unparse_stmt(b, inner, out, comments)
        out.append(ind + _with_comment('endif', s.end_comment, comments))
        return
    elif t is LoopStmt:
        out.append(ind + _with_comment(prefix + 'loop', s.comment, comments))
        inner = ind + '    '
        for b in s.body:
            _unparse_stmt(b, inner, out, comments)
        out.append(ind + _with_comment('endloop', s.end_comment, comments))
        return
    elif t is ExitWhenStmt:
        text = 'exitwhen ' + _ue(s.cond)
    elif t is ReturnStmt:
        text = 'return' if s.value is None else 'return ' + _ue(s.value)
    elif t is CommentStmt:
        if comments:
            out.append(ind + s.text)
        return
    elif t is DebugStmt:
        _unparse_stmt(s.stmt, ind, out, comments, prefix + 'debug ')
        return
    else:
        raise TypeError('not a JASS statement: %r' % (s,))
    out.append(ind + _with_comment(prefix + text, s.comment, comments))


def _unparse_item(item, out, comments):
    if comments:
        out.extend(item.leading_comments)
    t = type(item)
    if t is Function:
        out.append(_with_comment(_signature_text(item), item.comment, comments))
        if item.is_native:
            return
        for d in item.locals:
            if comments:
                out.extend('    ' + c for c in d.leading_comments)
            out.append(_with_comment('    local ' + _decl_text(d), d.comment, comments))
        for s in item.body:
            _unparse_stmt(s, '    ', out, comments)
        out.append(_with_comment('endfunction', item.end_comment, comments))
    elif t is Globals:
        out.append(_with_comment('globals', item.comment, comments))
        for d in item.decls:
            if comments:
                out.extend('    ' + c for c in d.leading_comments)
            out.append(_with_comment('    ' + _decl_text(d), d.comment, comments))
        if comments:
            out.extend('    ' + c for c in item.end_comments)
        out.append(_with_comment('endglobals', item.end_comment, comments))
    elif t is TypeDecl:
        out.append(_with_comment('type ' + item.name + ' extends ' + item.base, item.comment, comments))
    elif t is GlobalDecl:
        out.append(_with_comment(_decl_text(item), item.comment, comments))
    elif t is LocalDecl:
        out.append(_with_comment('local ' + _decl_text(item), item.comment, comments))
    else:
        raise TypeError('not a JASS declaration: %r' % (item,))


def unparse(node, comments=True):
    with _tree_work():
        if isinstance(node, Expr):
            return _ue(node)
        out = []
        if isinstance(node, Script):
            for k, item in enumerate(node.items):
                if k and type(item) is Function and not item.is_native:
                    out.append('')
                _unparse_item(item, out, comments)
            if comments:
                out.extend(node.end_comments)
        elif isinstance(node, Stmt):
            _unparse_stmt(node, '', out, comments)
        else:
            _unparse_item(node, out, comments)
        out.append('')
        return '\n'.join(out)


_WORD_END_CHARS = frozenset('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.')
_WORD_BEGIN_CHARS = _WORD_END_CHARS | frozenset('$')
_LITERAL_SPLIT_RE = re.compile(r'''"([^"\\]*(?:\\.[^"\\]*)*)"|'([^'\\]*(?:\\.[^'\\]*)*)'|//[^\r\n]*+''', re.S)
_SPACE_RUN_RE = re.compile(r'  ++')
_LONE_SPACE_RE = re.compile(r' (?:(?<![A-Za-z0-9_.] )|(?![A-Za-z0-9_.$]))')
_ONE_TOKEN_RUN_RE = re.compile(r'[A-Za-z0-9_.$](?:(?<=[A-Za-z_])[A-Za-z0-9_]*+|(?<=\$)[0-9A-Fa-f]++'
                               r'|(?<=0)[xX][0-9A-Fa-f]++|(?<=[0-9])[0-9]*+\.[0-9]*+|(?<=\.)[0-9]++|(?<=[0-9])[0-9]*+)'
                               r'(?![A-Za-z0-9_.$])')
_WORD_CHAR_RE = re.compile(r'[A-Za-z0-9_.$]')


def _canonical_tokens(text):
    lines = []
    cur = []
    prev = ''
    for t in _CANON_RE.findall(text + '\n'):
        if t in _NL:
            if cur:
                lines.append(''.join(cur))
                cur = []
            prev = ''
            continue
        if prev and prev[-1] in _WORD_END_CHARS and t[0] in _WORD_BEGIN_CHARS:
            cur.append(' ')
        cur.append(t)
        prev = t
    if cur:
        lines.append(''.join(cur))
    return '\n'.join(lines)


def _canonical_fast(text):
    if '\x03' in text:
        return None
    parts = _LITERAL_SPLIT_RE.split(text)
    literals = []
    marks = []
    for s, r in zip(parts[1::3], parts[2::3]):
        if s is not None:
            literals.append('"' + s + '"')
            marks.append('\x03')
        elif r is not None:
            literals.append("'" + r + "'")
            marks.append('\x03')
        else:
            marks.append('')
    out = [None] * (2 * len(marks) + 1)
    out[0::2] = parts[0::3]
    out[1::2] = marks
    code = ''.join(out)
    if _WORD_CHAR_RE.search(_ONE_TOKEN_RUN_RE.sub('', code)):
        return None
    if '\t' in code or _BOM in code:
        code = code.replace('\t', ' ').replace(_BOM, ' ')
    code = _LONE_SPACE_RE.sub('', _SPACE_RUN_RE.sub(' ', code))
    if '\r' in code:
        code = code.replace('\r\n', '\n').replace('\r', '\n')
    code = '\n'.join(filter(None, code.split('\n')))
    if not literals:
        return code
    pieces = code.split('\x03')
    out = [None] * (2 * len(pieces) - 1)
    out[0::2] = pieces
    out[1::2] = literals
    return ''.join(out)


def canonical(text_or_node):
    if isinstance(text_or_node, Node):
        text = unparse(text_or_node, comments=False)
    else:
        text = text_or_node
    fast = _canonical_fast(text)
    return _canonical_tokens(text) if fast is None else fast


_COMMENT_RE = re.compile(r'''"[^"\\]*(?:\\.[^"\\]*)*"|'[^'\\]*(?:\\.[^'\\]*)*'|/(/[^\r\n]*+)''', re.S)


def comments_of(text):
    return ['/' + c for c in _COMMENT_RE.findall(text) if c]


def read_script(path):
    with open(path, 'rb') as fh:
        return fh.read().decode('utf-8', 'surrogateescape')


def _first_difference(a, b):
    la, lb = a.split('\n'), b.split('\n')
    k = next((k for k in range(min(len(la), len(lb))) if la[k] != lb[k]), min(len(la), len(lb)))
    return k + 1, la[k] if k < len(la) else '<end>', lb[k] if k < len(lb) else '<end>'


def check_text(text):
    try:
        s = parse(text)
    except JassSyntaxError as e:
        return False, 'syntax error at ' + str(e)
    out = unparse(s)
    a, b = canonical(text), canonical(out)
    if a != b:
        return False, 'canonical line %d differs: %r != %r' % _first_difference(a, b)
    ca, cb = comments_of(text), comments_of(out)
    if ca != cb:
        k = next((k for k in range(min(len(ca), len(cb))) if ca[k] != cb[k]), min(len(ca), len(cb)))
        return False, 'comment %d differs (%d comments, %d after the round trip)' % (k + 1, len(ca), len(cb))
    return True, '%d functions, %d natives, %d globals, %d comments' % (len(s.functions), len(s.natives),
                                                                        len(s.globals), len(ca))


def _load_pjass():
    path = os.path.join(HERE, '..', 'kk', 'pjass.py')
    if not os.path.isfile(path):
        return None
    import importlib.util
    spec = importlib.util.spec_from_file_location('jass_ast_pjass', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod if os.path.isfile(mod.exe()) else None

