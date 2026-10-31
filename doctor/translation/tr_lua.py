# Finds the screen texts of the Lua code of a map and writes their translation back.
import collections
import re

from doctor.script import lua_ast
from doctor.translation import tr_apply


TELA, CHAVE, PRUDENCIA, FORA = 'screen', 'hash_key', 'caution', 'outside'
COMPARE = frozenset(('==', '~=', '<', '>', '<=', '>='))
STOP = frozenset((',', ';', '=', 'and', 'or', 'then', 'do', 'else', 'elseif', 'end', 'return', 'local', 'if', 'while',
                  'until', 'repeat', 'in', 'for', 'function', 'goto', 'break', '::'))
OPEN = {'(': ')', '[': ']', '{': '}'}
CLOSE = {')': '(', ']': '[', '}': '{'}
KEY_FUNCTIONS = frozenset(('require', 'dofile', 'loadfile', 'load', 'loadstring', 'rawget', 'rawset', 'rawequal',
                           'module'))
STRING_FUNCTIONS = frozenset(('sub', 'find', 'match', 'gmatch', 'gsub', 'byte', 'len', 'rep', 'reverse', 'lower',
                              'upper', 'char', 'codepoint', 'offset', 'codes'))
NOT_TEXT = frozenset(('print', 'error', 'assert', 'warn', 'collectgarbage', 'tonumber', 'type', 'select'))
NOT_TEXT_PREFIX = ('log.', 'debug.', 'os.', 'io.', 'string.dump', 'package.')
RX_MODULE_NAME = re.compile(r'^[^\s.\\/]+(?:\.[^\s.\\/]+)+$')
RX_FIRST_BREAK = re.compile(r'\r\n|\n\r|\n|\r')
RX_PATTERN = re.compile(r'%[aAcClLpPuUwWbfDSGX\[\]()]|%[ds][+*-]|\[\^|\(\.[-+*]\)')


class Source(object):
    def __init__(self, file, text, module=None, base=0, close=None):
        self.file, self.text, self.module, self.base, self.close = file, text, module, base, close
        self._lex = None

    def lexed(self):
        if self._lex is None:
            self._lex = tokens(self.text)
            self._shape = structure(self._lex[0])
        return self._lex

    def shape(self):
        self.lexed()
        return self._shape


def structure(kinds):
    enc, argn, match = [-1] * len(kinds), [0] * len(kinds), {}
    stack, commas = [], [0]
    for i, k in enumerate(kinds):
        if k in CLOSE:
            if stack:
                match[stack.pop()] = i
                commas.pop()
            enc[i] = stack[-1] if stack else -1
            argn[i] = commas[-1]
            continue
        enc[i] = stack[-1] if stack else -1
        argn[i] = commas[-1]
        if k in OPEN:
            stack.append(i)
            commas.append(0)
        elif k == ',':
            commas[-1] += 1
    return enc, argn, match


def tokens(text):
    kinds, texts, _lines, offs, _comments, _ctok, strval = lua_ast._lex(text)
    values = {}
    for i, k in enumerate(kinds):
        if k in ('ERROR', 'CHAR'):
            raise lua_ast.LuaSyntaxError(_lines[i], 'not Lua (%s)' % texts[i][:40])
        if k == 'STRING':
            v = strval.get(i)
            if v is None:
                t = texts[i]
                v = lua_ast._long_value(t) if t[0] == '[' else t[1:-1]
            values[i] = v
    return kinds, texts, offs, values


def _bom(text):
    return 1 if text.startswith('﻿') else 0


def sources(file, text):
    if '__ydwe_fonte[' not in text:
        b = _bom(text)
        return [Source(file, text[b:], base=b)]
    kinds, texts, offs, values = tokens(text)
    out = []
    for i in range(len(kinds) - 5):
        if kinds[i] == 'NAME' and texts[i] == '__ydwe_fonte' and kinds[i + 1] == '[' and kinds[i + 2] == 'STRING' \
                and kinds[i + 3] == ']' and kinds[i + 4] == '=' and kinds[i + 5] == 'STRING' and \
                texts[i + 5][0] == '[':
            raw = texts[i + 5]
            level = raw.index('[', 1) - 1
            body = raw[level + 2:len(raw) - level - 2]
            m = RX_FIRST_BREAK.match(body)
            skip = m.end() if m else 0
            out.append(Source(file, body[skip:], module=values[i + 2], base=offs[i + 5] + level + 2 + skip,
                              close=']' + '=' * level + ']'))
    return out


def _callee(kinds, texts, p):
    j = p - 1
    if j < 0:
        return None
    if kinds[j] == 'NAME':
        parts = [texts[j]]
        while j >= 2 and kinds[j - 1] in ('.', ':') and kinds[j - 2] == 'NAME':
            parts.insert(0, texts[j - 2] + kinds[j - 1])
            j -= 2
        if j >= 1 and kinds[j - 1] in ('.', ':') and kinds[j - 2] in (')', ']', 'STRING'):
            return '?' + kinds[j - 1] + parts[-1]
        return ''.join(parts)
    if kinds[j] in (')', ']', 'STRING') and kinds[p] in ('(', 'STRING', '{'):
        return '?'
    return None


def _compared(kinds, i, j):
    for step, start, opener, closer in ((-1, i - 1, CLOSE, OPEN), (1, j + 1, OPEN, CLOSE)):
        depth, k = 0, start
        while 0 <= k < len(kinds):
            kk = kinds[k]
            if kk in opener:
                depth += 1
            elif kk in closer:
                if depth == 0:
                    break
                depth -= 1
            elif depth == 0:
                if kk in COMPARE:
                    return True
                if kk in STOP:
                    break
            k += step
    return False


def _last(name):
    return re.split(r'[.:]', name)[-1]


def _by_call(name, idx, kinds, texts, p, flow):
    last = _last(name)
    if last in KEY_FUNCTIONS:
        return CHAVE + ':' + last
    if last in ('pcall', 'xpcall') and kinds[p + 1] == 'NAME' and texts[p + 1] in KEY_FUNCTIONS:
        return CHAVE + ':' + texts[p + 1]
    if name in NOT_TEXT or name.startswith(NOT_TEXT_PREFIX):
        return FORA + ':' + name
    if last == 'format' and (name.startswith(('string.', '?')) or ':' in name):
        return TELA + ':format'
    if last in STRING_FUNCTIONS and (name.startswith(('string.', 'utf8.', '?')) or ':' in name):
        return PRUDENCIA + ':' + name
    if name.startswith('utf8.'):
        return PRUDENCIA + ':' + name
    group = tr_apply.classify_call_occurrence(last, idx)
    if group != TELA:
        return '%s:%s' % (group, last)
    if flow is not None and flow.target(last, idx):
        return PRUDENCIA + ':flow ' + last
    return TELA + ':' + name


def classify(kinds, texts, i, flow=None, shape=None):
    enc, argn, match = shape or structure(kinds)
    lo = hi = i
    while True:
        if _compared(kinds, lo, hi):
            return PRUDENCIA + ':comparison'
        nxt = hi + 1
        if nxt < len(kinds) and kinds[nxt] == ':' and nxt + 1 < len(kinds) and kinds[nxt + 1] == 'NAME' and \
                lo == hi == i:
            m = texts[nxt + 1]
            return TELA + ':format' if m == 'format' else PRUDENCIA + ':method ' + m
        if lo == hi == i and i > 0 and kinds[i - 1] in ('NAME', ')', ']'):
            name = _callee(kinds, texts, i)
            if name is not None:
                return _by_call(name, 0, kinds, texts, i - 1, flow)
        p, commas = enc[lo], argn[lo]
        if p < 0:
            return TELA + ':no call'
        if kinds[p] == '[':
            return CHAVE + ':index'
        if kinds[p] == '{':
            return TELA + ':table'
        name = _callee(kinds, texts, p)
        if name is None:
            k = match.get(p, len(kinds) - 1)
            if k + 1 < len(kinds) and kinds[k + 1] == ':' and k + 2 < len(kinds) and kinds[k + 2] == 'NAME':
                m = texts[k + 2]
                if m == 'format' and kinds[p + 1] == 'STRING' and p + 1 == i and k == i + 1:
                    return TELA + ':format'
                return PRUDENCIA + ':method ' + m
            lo, hi = p, k
            continue
        return _by_call(name, commas, kinds, texts, p, flow)


def occurrences(source, flow=None):
    kinds, texts, offs, values = source.lexed()
    shape = source.shape()
    out = []
    for i, k in enumerate(kinds):
        if k == 'STRING':
            out.append((i, offs[i], offs[i] + len(texts[i]), values[i], classify(kinds, texts, i, flow, shape)))
    return out


_END_SCOPE = object()
_NOT_CHILDREN = frozenset(('line', 'comment', 'leading_comments', 'inner_comments', 'span', 'end_comments'))
_CHILDREN = {}


def _children(cls):
    names = _CHILDREN.get(cls)
    if names is None:
        names = _CHILDREN[cls] = tuple(s for c in cls.__mro__ for s in getattr(c, '__slots__', ())
                                       if s not in _NOT_CHILDREN)
    return names


def _call_name(call):
    f = call.func
    parts = []
    while isinstance(f, lua_ast.Index) and isinstance(f.key, lua_ast.Literal) and f.key.kind == 'string':
        parts.insert(0, f.key.value)
        f = f.base
    if isinstance(f, lua_ast.Name):
        parts.insert(0, f.name)
    elif parts:
        parts.insert(0, '?')
    name = '.'.join(parts)
    if call.method:
        name = (name + ':' if name else '?:') + call.method
    return name


def _function_name(target):
    if isinstance(target, lua_ast.Name):
        return target.name
    if isinstance(target, lua_ast.Index) and isinstance(target.key, lua_ast.Literal) and target.key.kind == 'string':
        return target.key.value
    return None


def _plain(e):
    while True:
        t = type(e)
        if t is lua_ast.Paren:
            e = e.inner
        elif t is lua_ast.Binary and e.op == '..':
            return _plain(e.left) or _plain(e.right)
        else:
            return e.name if t is lua_ast.Name else None


def _uses(n):
    t = type(n)
    if t is lua_ast.Binary:
        return (_plain(n.left), _plain(n.right)) if n.op in COMPARE else ()
    if t is lua_ast.Index:
        return () if n.dot else (_plain(n.key),)
    if t is lua_ast.Table:
        return tuple(_plain(k) for k, _v in n.fields if isinstance(k, lua_ast.Node))
    if t is lua_ast.Call:
        cname = _call_name(n)
        last = _last(cname) if cname else ''
        if n.method in STRING_FUNCTIONS and type(n.func) is lua_ast.Name:
            return (n.func.name,)
        if last in KEY_FUNCTIONS or (last in STRING_FUNCTIONS and cname.startswith(('string.', 'utf8.'))):
            return tuple(_plain(a) for a in n.args)
        if last:
            return tuple(_plain(a) for k, a in enumerate(n.args)
                         if tr_apply.classify_call_occurrence(last, k) != TELA)
    return ()


class Flow(object):
    def __init__(self, chunks):
        self.flagged = collections.defaultdict(set)
        for chunk in chunks:
            self._pass(chunk.body)

    def _pass(self, root):
        named = {}
        scopes = []
        stack = [root]
        while stack:
            n = stack.pop()
            if n is _END_SCOPE:
                scopes.pop()
                continue
            t = type(n)
            if t is list or t is tuple or t is lua_ast.Block:
                stack.extend(n)
                continue
            if not isinstance(n, lua_ast.Node):
                continue
            if t is lua_ast.AssignStmt or t is lua_ast.LocalStmt:
                targets = n.targets if t is lua_ast.AssignStmt else [lua_ast.Name(x) for x in n.names]
                for tg, v in zip(targets, n.values or ()):
                    if type(v) is lua_ast.FunctionExpr:
                        nm = _function_name(tg)
                        if nm:
                            named[id(v)] = nm
            elif t is lua_ast.Table:
                for k, v in n.fields:
                    if isinstance(k, str) and type(v) is lua_ast.FunctionExpr:
                        named[id(v)] = k
            if t is lua_ast.FunctionStmt or t is lua_ast.FunctionExpr:
                name = _last(n.name) if t is lua_ast.FunctionStmt else named.get(id(n))
                scopes.append((name, dict((p, i) for i, p in enumerate(n.params or ()))))
                stack.append(_END_SCOPE)
            elif scopes:
                for h in _uses(n):
                    if not h:
                        continue
                    for name, index in reversed(scopes):
                        if h in index:
                            if name:
                                self.flagged[name].add(index[h])
                            break
            for s in _children(t):
                v = getattr(n, s, None)
                if v is not None and not isinstance(v, (str, int, float, bool)):
                    stack.append(v)

    def target(self, name, idx):
        return idx in self.flagged.get(name, ())


def flow_of(srcs):
    chunks = []
    for s in srcs:
        try:
            chunks.append(lua_ast.parse(s.text))
        except (lua_ast.LuaSyntaxError, RecursionError):
            continue
    return Flow(chunks)


def module_like(value):
    return bool(RX_MODULE_NAME.match(value))


def pattern_like(value):
    return bool(RX_PATTERN.search(value))


_ESCAPES = {'\\': '\\\\', '\n': '\\n', '\r': '\\r', '\t': '\\t', '\a': '\\a', '\b': '\\b', '\f': '\\f', '\v': '\\v',
            '\x00': '\\0'}


def quote(value, raw, bracket=False):
    if raw[0] == '[' and not bracket:
        level = raw.index('[', 1) - 1
        lead = raw[level + 2:level + 3] in ('\n', '\r') or value.startswith(('\n', '\r'))
        while (']' + '=' * level + ']') in value + ']':
            level += 1
        return '[' + '=' * level + '[' + ('\n' if lead else '') + value + ']' + '=' * level + ']'
    q = '"' if raw[0] == '[' else raw[0]
    out = []
    for c in value:
        if c == ']' and bracket:
            out.append('\\093')
        elif c == q:
            out.append('\\' + q)
        elif c in _ESCAPES:
            out.append(_ESCAPES[c])
        elif ord(c) < 32 or ord(c) == 127:
            out.append('\\%03d' % ord(c))
        else:
            out.append(c)
    return q + ''.join(out) + q


def apply(source, by_value):
    kinds, texts, offs, values = source.lexed()
    out, last, n = [], 0, collections.Counter()
    for i, k in enumerate(kinds):
        if k == 'STRING' and values[i] in by_value:
            lit = quote(by_value[values[i]], texts[i])
            if source.close and source.close in lit:
                lit = quote(by_value[values[i]], texts[i], bracket=True)
            out += [source.text[last:offs[i]], lit]
            last = offs[i] + len(texts[i])
            n[values[i]] += 1
    out.append(source.text[last:])
    new = ''.join(out)
    if source.close and source.close in new:
        raise ValueError('%s: a translation closes the long string the module is kept in' % source.module)
    return new, n


def readback(before, after, by_value):
    k1, t1, _o1, v1 = tokens(before)
    k2, t2, _o2, v2 = tokens(after)
    if k1 != k2:
        return ['the tokens changed (%d -> %d)' % (len(k1), len(k2))]
    bad = []
    for i, k in enumerate(k1):
        if k == 'STRING' and v1[i] in by_value:
            if v2[i] != by_value[v1[i]]:
                bad.append('literal %r reads %r' % (v1[i][:30], v2[i][:30]))
        elif t1[i] != t2[i]:
            bad.append('token %d changed: %r -> %r' % (i, t1[i][:30], t2[i][:30]))
        if len(bad) > 5:
            break
    return bad
