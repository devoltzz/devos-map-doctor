# The layered Lua loader format (key, base64, sums) that the WC3Fuscator reader takes apart.
import base64
import os
import re
import sys

from doctor.script import lua_ast


ALPHABET_B64 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
LEHMER = 65537
DEFAULT_REF = next(
    (
        p
        for p in (
            os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ref', '3.0')),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ref', '3.0'),
        )
        if os.path.isfile(os.path.join(p, 'common.j'))
    ),
    os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ref', '3.0')),
)
def arg(fname, default_value=None, argv=None):
    for a in (sys.argv if argv is None else argv)[1:]:
        if a.startswith('--%s=' % fname):
            return a.split('=', 1)[1]
    return default_value


def flag(fname, argv=None):
    return ('--%s' % fname) in (sys.argv if argv is None else argv)[1:]


def lehmer_key(jpeg_seed, n):
    x = jpeg_seed
    out = []
    for _ in range(n):
        x = (x * 75 + 74) % LEHMER
        b = x % 256
        out.append(b if b else 1)
    return out


_RX_ONLY_B64 = re.compile(r'[A-Za-z0-9+/]*')
_ADD_TABLES = {}


def _add_table(k):
    t = _ADD_TABLES.get(k)
    if t is None:
        t = _ADD_TABLES[k] = bytes((v + k) & 0xFF for v in range(256))
    return t


def add_key(data_bytes, hash_key, sign=1):
    n = len(hash_key)
    out = bytearray(data_bytes)
    for j in range(min(n, len(out))):
        out[j::n] = out[j::n].translate(_add_table((sign * hash_key[j]) & 0xFF))
    return bytes(out)


def b64_decode(s):
    if not _RX_ONLY_B64.fullmatch(s):
        return _b64_decode_py(s)
    cut = len(s) - len(s) % 4 if len(s) % 4 == 1 else len(s)
    return base64.b64decode(s[:cut] + '=' * (-cut % 4))


def _b64_decode_py(s):
    x = dict((ord(ch), i) for i, ch in enumerate(ALPHABET_B64))
    out = bytearray()
    for i in range(0, len(s), 4):
        a = x.get(ord(s[i])) if i < len(s) else None
        b = x.get(ord(s[i + 1])) if i + 1 < len(s) else None
        c = x.get(ord(s[i + 2])) if i + 2 < len(s) else None
        d = x.get(ord(s[i + 3])) if i + 3 < len(s) else None
        if a is None or b is None:
            break
        out.append((a * 4 + b // 16) & 0xff)
        if c is not None:
            out.append(((b % 16) * 16 + c // 4) & 0xff)
            if d is not None:
                out.append(((c % 4) * 64 + d) & 0xff)
    return bytes(out)


_SAL = (75, 74)
STRING_MOD = 32749


def value_of(index_, digits_str):
    a, b = _SAL
    x = (index_ * a + b) % STRING_MOD
    out = bytearray()
    for i in range(0, len(digits_str), 3):
        out.append((int(digits_str[i:i + 3]) - 100 - x % 256) % 256)
        q = (x * x) % STRING_MOD
        x = (q + a * x + b) % STRING_MOD
    return bytes(out).decode('utf-8', 'surrogateescape')


def renomeia(chunk, g, keep_names, log=print):
    reverse = {}
    globals_block = set()
    local_vars = set()
    scopes = [{}]
    label_set = [{}]

    def resolve(fname):
        for e in reversed(scopes):
            if fname in e:
                return e[fname]
        return None

    def declare(fname):
        local_vars.add(fname)
        if fname in keep_names:
            scopes[-1][fname] = fname
            return fname
        new = g.new()
        scopes[-1][fname] = new
        reverse[new] = fname
        return new

    def expr(e):
        t = type(e)
        if t is lua_ast.Name:
            new = resolve(e.name)
            if new is not None:
                e.name = new
            else:
                globals_block.add(e.name)
        elif t is lua_ast.Index:
            expr(e.base)
            expr(e.key)
        elif t is lua_ast.Call:
            expr(e.func)
            for a in e.args:
                expr(a)
        elif t is lua_ast.Unary:
            expr(e.operand)
        elif t is lua_ast.Binary:
            expr(e.left)
            expr(e.right)
        elif t is lua_ast.Paren:
            expr(e.inner)
        elif t is lua_ast.Table:
            for k, v in e.fields:
                if k is not None and type(k) is not str:
                    expr(k)
                expr(v)
        elif t is lua_ast.FunctionExpr:
            scopes.append({})
            label_set.append({})
            for i, p in enumerate(e.params):
                e.params[i] = declare(p)
            block_entry(e.body)
            scopes.pop()
            label_set.pop()

    def label_text(fname):
        if fname not in label_set[-1]:
            if fname in keep_names:
                label_set[-1][fname] = fname
            else:
                new = g.new()
                label_set[-1][fname] = new
                reverse[new] = fname
                local_vars.add(fname)
        return label_set[-1][fname]

    def block_entry(b):
        for s in b:
            t = type(s)
            if t is lua_ast.LocalStmt:
                for v in s.values:
                    expr(v)
                for i, n in enumerate(s.names):
                    s.names[i] = declare(n)
            elif t is lua_ast.AssignStmt:
                for x in s.targets:
                    expr(x)
                for v in s.values:
                    expr(v)
            elif t is lua_ast.CallStmt:
                expr(s.call)
            elif t is lua_ast.ReturnStmt:
                for v in s.values:
                    expr(v)
            elif t is lua_ast.FunctionStmt:
                if s.is_local:
                    s.name = declare(s.name)
                else:
                    base = re.split(r'[.:]', s.name, maxsplit=1)[0]
                    if base != s.name:
                        new = resolve(base)
                        if new is not None:
                            s.name = new + s.name[len(base):]
                        else:
                            globals_block.add(base)
                    else:
                        new = resolve(s.name)
                        if new is not None:
                            s.name = new
                        else:
                            globals_block.add(s.name)
                scopes.append({})
                label_set.append({})
                if ':' in s.name:
                    scopes[-1]['self'] = 'self'
                for i, p in enumerate(s.params):
                    s.params[i] = declare(p)
                block_entry(s.body)
                scopes.pop()
                label_set.pop()
            elif t is lua_ast.IfStmt:
                for cond, block_body in s.branches:
                    if cond is not None:
                        expr(cond)
                    scopes.append({})
                    block_entry(block_body)
                    scopes.pop()
            elif t is lua_ast.WhileStmt:
                expr(s.cond)
                scopes.append({})
                block_entry(s.body)
                scopes.pop()
            elif t is lua_ast.NumericForStmt:
                expr(s.start)
                expr(s.stop)
                if s.step is not None:
                    expr(s.step)
                scopes.append({})
                s.var = declare(s.var)
                block_entry(s.body)
                scopes.pop()
            elif t is lua_ast.GenericForStmt:
                for x in s.exprs:
                    expr(x)
                scopes.append({})
                for i, n in enumerate(s.names):
                    s.names[i] = declare(n)
                block_entry(s.body)
                scopes.pop()
            elif t is lua_ast.RepeatStmt:
                scopes.append({})
                block_entry(s.body)
                expr(s.cond)
                scopes.pop()
            elif t is lua_ast.DoStmt:
                scopes.append({})
                block_entry(s.body)
                scopes.pop()
            elif t is lua_ast.GotoStmt:
                s.label = label_text(s.label)
            elif t is lua_ast.LabelStmt:
                s.name = label_text(s.name)

    block_entry(chunk.body)
    return reverse, globals_block, local_vars


def _restore_decl(s, r_name):
    t = type(s)
    if t is lua_ast.LocalStmt or t is lua_ast.AssignStmt or t is lua_ast.ReturnStmt:
        s.values = [_restore_expr(v, r_name) for v in s.values]
        if t is lua_ast.AssignStmt:
            s.targets = [_restore_expr(v, r_name) for v in s.targets]
    elif t is lua_ast.CallStmt:
        s.call = _restore_expr(s.call, r_name)
    elif t is lua_ast.FunctionStmt:
        for x in s.body:
            _restore_decl(x, r_name)
    elif t is lua_ast.IfStmt:
        for n, (cond, block_body) in enumerate(s.branches):
            if cond is not None:
                s.branches[n] = (_restore_expr(cond, r_name), block_body)
            for x in block_body:
                _restore_decl(x, r_name)
    elif t is lua_ast.WhileStmt:
        s.cond = _restore_expr(s.cond, r_name)
        for x in s.body:
            _restore_decl(x, r_name)
    elif t is lua_ast.NumericForStmt:
        s.start, s.stop = _restore_expr(s.start, r_name), _restore_expr(s.stop, r_name)
        if s.step is not None:
            s.step = _restore_expr(s.step, r_name)
        for x in s.body:
            _restore_decl(x, r_name)
    elif t is lua_ast.GenericForStmt:
        s.exprs = [_restore_expr(x, r_name) for x in s.exprs]
        for x in s.body:
            _restore_decl(x, r_name)
    elif t is lua_ast.RepeatStmt:
        for x in s.body:
            _restore_decl(x, r_name)
        s.cond = _restore_expr(s.cond, r_name)
    elif t is lua_ast.DoStmt:
        for x in s.body:
            _restore_decl(x, r_name)


def _restore_expr(e, r_name):
    t = type(e)
    if t is lua_ast.Call:
        if type(e.func) is lua_ast.Name and e.func.name == r_name and len(e.args) == 2 \
                and type(e.args[0]) is lua_ast.Literal and e.args[0].kind == 'number' \
                and type(e.args[1]) is lua_ast.Literal and e.args[1].kind == 'string':
            return lua_ast.Literal('string', None, value_of(int(e.args[0].value), e.args[1].value))
        e.func = _restore_expr(e.func, r_name)
        e.args = [_restore_expr(a, r_name) for a in e.args]
        return e
    if t is lua_ast.Index:
        e.base = _restore_expr(e.base, r_name)
        e.key = _restore_expr(e.key, r_name)
        return e
    if t is lua_ast.Unary:
        e.operand = _restore_expr(e.operand, r_name)
        return e
    if t is lua_ast.Binary:
        e.left = _restore_expr(e.left, r_name)
        e.right = _restore_expr(e.right, r_name)
        return e
    if t is lua_ast.Paren:
        e.inner = _restore_expr(e.inner, r_name)
        return e
    if t is lua_ast.Table:
        field_list = []
        for k, v in e.fields:
            if k is not None and type(k) is not str:
                k = _restore_expr(k, r_name)
            field_list.append((k, _restore_expr(v, r_name)))
        e.fields[:] = field_list
        return e
    if t is lua_ast.FunctionExpr:
        for x in e.body:
            _restore_decl(x, r_name)
        return e
    return e


def _norm_decl(s):
    t = type(s)
    if t in (lua_ast.LocalStmt, lua_ast.AssignStmt, lua_ast.ReturnStmt):
        for v in s.values:
            _norm_expr(v)
        if t is lua_ast.AssignStmt:
            for v in s.targets:
                _norm_expr(v)
    elif t is lua_ast.CallStmt:
        _norm_expr(s.call)
    elif t is lua_ast.FunctionStmt:
        for x in s.body:
            _norm_decl(x)
    elif t is lua_ast.IfStmt:
        for cond, block_body in s.branches:
            if cond is not None:
                _norm_expr(cond)
            for x in block_body:
                _norm_decl(x)
    elif t is lua_ast.WhileStmt:
        _norm_expr(s.cond)
        for x in s.body:
            _norm_decl(x)
    elif t is lua_ast.NumericForStmt:
        for e in (s.start, s.stop) + ((s.step,) if s.step is not None else ()):
            _norm_expr(e)
        for x in s.body:
            _norm_decl(x)
    elif t is lua_ast.GenericForStmt:
        for e in s.exprs:
            _norm_expr(e)
        for x in s.body:
            _norm_decl(x)
    elif t is lua_ast.RepeatStmt:
        for x in s.body:
            _norm_decl(x)
        _norm_expr(s.cond)
    elif t is lua_ast.DoStmt:
        for x in s.body:
            _norm_decl(x)


def _norm_expr(e):
    t = type(e)
    if t is lua_ast.Literal:
        if e.kind == 'string':
            e.text = None
        return
    if t is lua_ast.Index:
        _norm_expr(e.base)
        _norm_expr(e.key)
        if e.dot and type(e.key) is lua_ast.Literal and e.key.kind == 'string':
            e.dot = False
        return
    if t is lua_ast.Call:
        _norm_expr(e.func)
        for a in e.args:
            _norm_expr(a)
        return
    if t is lua_ast.Unary:
        _norm_expr(e.operand)
        return
    if t is lua_ast.Binary:
        _norm_expr(e.left)
        _norm_expr(e.right)
        return
    if t is lua_ast.Paren:
        _norm_expr(e.inner)
        return
    if t is lua_ast.Table:
        field_list = []
        for k, v in e.fields:
            if type(k) is str:
                k = lua_ast.Literal('string', None, k)
            elif k is not None:
                _norm_expr(k)
            _norm_expr(v)
            field_list.append((k, v))
        e.fields[:] = field_list
        return
    if t is lua_ast.FunctionExpr:
        for x in e.body:
            _norm_decl(x)


class _Links(lua_ast._Parser):
    def __init__(self, body_text):
        lua_ast._Parser.__init__(self, body_text)
        self.n_decl = 0
        self.links = []

    def _new_localvar(self, name, attrib=None):
        lua_ast._Parser._new_localvar(self, name, attrib)
        self.n_decl += 1
        self.fs.actvar[-1].append(self.n_decl)

    def _singlevar(self, name):
        fs = self.fs
        stack = fs.vars.get(name)
        var = fs.actvar[stack[-1]] if stack else self._resolve(fs, name)
        ln = self.l[self.i - 1]
        if var is lua_ast._GLOBAL:
            env = self._resolve(fs, '_ENV')
            self.links.append(('global', name, env[2] if len(env) > 2 else 0, ln))
        else:
            self.links.append(('local', var[2] if len(var) > 2 else 0, ln))


class _BindingsOnly(object):
    __slots__ = ('links', 'n_decl')

    def __init__(self, links, n_decl):
        self.links, self.n_decl = links, n_decl


def _link(body_text):
    old = sys.getrecursionlimit()
    if old < lua_ast._RECURSION:
        sys.setrecursionlimit(lua_ast._RECURSION)
    try:
        p = _Links(body_text)
        script_tree = p.chunk()
        return script_tree, _BindingsOnly(p.links, p.n_decl)
    finally:
        if old < lua_ast._RECURSION:
            sys.setrecursionlimit(old)

