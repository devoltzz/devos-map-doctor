# Writes a GUI trigger as the script the World Editor would generate (JASS or Lua).
import collections
import re
import sys



JASS, LUA = 'jass', 'lua'
BANNER = '//' + '=' * 75
_ALNUM = frozenset(b'0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz')
RX_REF = re.compile(r'\b((?:Init)?Trig_\w+)')


def trigger_identifier(name):
    data = name.rstrip(' ').encode('utf-8', 'surrogateescape')
    ident = ''.join(chr(c) if c in _ALNUM else '_' for c in data)
    return ident + 'u' if ident.endswith('_') else ident


_JASS_TOKEN = re.compile(
    r'[ \t\ufeff]*(//[^\r\n]*|\r\n?|\n|"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'|[A-Za-z_]\w*'
    r'|0[xX][0-9A-Fa-f]+|\$[0-9A-Fa-f]+|\d+\.\d*|\.\d+|\d+|[=!<>]=|[^ \t\ufeff])', re.S)
_LUA_TOKEN = re.compile(
    r'[ \t\ufeff]*(--\[(=*)\[.*?\]\2\]|--[^\r\n]*|\r\n?|\n|\[(=*)\[.*?\]\3\]|"(?:[^"\\\r\n]|\\.)*"'
    r'|\'(?:[^\'\\\r\n]|\\.)*\'|[A-Za-z_]\w*|0[xX][0-9A-Fa-f]+|\d+\.\d*(?:[eE][-+]?\d+)?|\.\d+|\d+'
    r'|\.\.\.?|[=~<>]=|::|//|[^ \t\ufeff])', re.S)
_RX_JASS_FUNCTION = re.compile(
    r'(?ms)^[ \t]*(?:constant[ \t]+)?function[ \t]+(\w+)[ \t]+takes\b.*?^[ \t]*endfunction\b[^\r\n]*')
_WORD_CHARS = frozenset('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_0123456789')
_RX_BREAK = re.compile(r'\r\n?|\n')
_RX_RAWCODE = re.compile(r"'[A-Za-z0-9]{4}'$")
_RX_REAL = re.compile(r'(\d*)\.(\d*)$')


def tokens(text, lang=JASS):
    if lang == LUA:
        raw, comment = [m[0] for m in _LUA_TOKEN.findall(text)], '--'
    else:
        raw, comment = _JASS_TOKEN.findall(text), '//'
    out = []
    for t in raw:
        if t in ('\n', '\r\n', '\r'):
            out.append('\n')
        elif t[:2] == comment:
            out.extend('\n' for _i in _RX_BREAK.findall(t))
        else:
            out.append(t)
    return out


def _is_string(t):
    c = t[:1]
    return c == '"' or (c == "'" and len(t) > 1) or (c == '[' and re.match(r'\[=*\[', t) is not None)


def _norm_literal(t):
    c = t[:1]
    if c == "'":
        return t[1:-1] if len(t) == 6 and _RX_RAWCODE.match(t) and not t[1].isdigit() else t
    if c == '$':
        return '0x' + t[1:]
    if (c.isdigit() or c == '.') and '.' in t and t != '.':
        m = _RX_REAL.match(t)
        if m:
            return (m.group(1) or '0') + '.' + m.group(2).rstrip('0')
    return t


_KEYWORDS = frozenset(('if', 'elseif', 'not', 'and', 'or', 'return', 'exitwhen', 'then', 'else', 'set', 'call',
                       'while', 'until', 'do', 'local', 'in'))


def _close(toks, i, open_='(', close_=')'):
    depth = 0
    for j in range(i, len(toks)):
        if toks[j] == open_:
            depth += 1
        elif toks[j] == close_:
            depth -= 1
            if depth == 0:
                return j
    return -1


def _is_word(t):
    return t[:1] in _WORD_CHARS


def _is_atom(ts):
    if len(ts) == 1:
        return ts[0] not in ('not', '-', '#', '\n') and (_is_word(ts[0]) or _is_string(ts[0]) or ts[0][:1] in '.$')
    return (len(ts) >= 4 and _is_word(ts[0]) and not ts[0][0].isdigit() and ts[1] == '[' and
            _close(ts, 1, '[', ']') == len(ts) - 1)


def _call_paren(toks, i):
    prev = toks[i - 1] if i > 0 else ''
    return (_is_word(prev) and prev not in _KEYWORDS) or prev in (')', ']')


def _strip_parens(toks):
    i = 0
    while i < len(toks):
        if toks[i] == '(':
            j = _close(toks, i)
            inner = toks[i + 1:j] if j > 0 else []
            if inner and inner[0] == '(' and _close(inner, 0) == len(inner) - 1:
                del toks[j - 1]
                del toks[i + 1]
                continue
            if inner and not _call_paren(toks, i) and _is_atom(inner):
                del toks[j]
                del toks[i]
                i = max(i - 1, 0)
                continue
        i += 1
    return toks


_LUA_KEYWORDS = frozenset(('and', 'break', 'do', 'else', 'elseif', 'end', 'false', 'for', 'function', 'goto', 'if',
                           'in', 'local', 'nil', 'not', 'or', 'repeat', 'return', 'then', 'true', 'until', 'while'))
_LUA_STATEMENT = frozenset(('if', 'while', 'for', 'return', 'local', 'function', 'repeat', 'break', 'end', 'else',
                            'elseif', 'until', 'goto'))


def _ends_expression(t):
    return t in (')', ']', '}', 'nil', 'true', 'false', 'end') or _is_string(t) or (
        _is_word(t) and t not in _LUA_KEYWORDS)


def _statement_ends(toks, k, lang):
    if k >= len(toks) or toks[k] in ('\n', ';'):
        return True
    t = toks[k]
    return lang == LUA and (t in _LUA_STATEMENT or (_is_word(t) and not t[0].isdigit() and t not in _LUA_KEYWORDS))


def _strip_right_sides(toks, lang):
    i = 1
    while i < len(toks):
        if toks[i] == '(' and toks[i - 1] in ('=', 'return'):
            j = _close(toks, i)
            if j > 0 and _statement_ends(toks, j + 1, lang):
                del toks[j]
                del toks[i]
                continue
        i += 1
    return toks


def _lines(toks):
    out, cur = [], []
    for t in toks:
        if t == '\n' or t == ';':
            if cur:
                out.append(cur)
            cur = []
        else:
            cur.append(t)
    if cur:
        out.append(cur)
    return out


def _lua_lines(toks):
    out, cur = [], []
    for t in toks:
        if t in ('\n', ';'):
            continue
        if cur and (t in _LUA_STATEMENT or (_is_word(t) and not t[0].isdigit() and t not in _LUA_KEYWORDS and
                                            _ends_expression(cur[-1]))):
            out.append(cur)
            cur = []
        cur.append(t)
        if t in ('then', 'do', 'else'):
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def _join(toks):
    out, word = [], False
    for t in toks:
        if word and t[:1] in _WORD_CHARS:
            out.append(' ')
        out.append(t)
        word = t[-1:] in _WORD_CHARS
    return ''.join(out)


def _function_spans(toks, lang):
    spans = []
    i, n = 0, len(toks)
    while i < n:
        j = i + 1 if toks[i] in ('constant', 'local') and toks[i + 1:i + 2] == ['function'] else i
        follow = 'takes' if lang == JASS else '('
        if toks[j] == 'function' and j + 2 < n and _is_word(toks[j + 1]) and toks[j + 2] == follow:
            end = _block_end(toks, j, lang)
            if end < 0:
                break
            spans.append((toks[j + 1], i, end))
            i = end
            continue
        i += 1
    return spans


def _block_end(toks, i, lang):
    if lang == JASS:
        for j in range(i + 1, len(toks)):
            if toks[j] == 'endfunction':
                return j + 1
            if toks[j] == 'function' and toks[j - 1] == '\n':
                return -1
        return -1
    depth = 0
    for j in range(i, len(toks)):
        t = toks[j]
        if t in ('function', 'if', 'do', 'repeat'):
            depth += 1
        elif t in ('end', 'until'):
            depth -= 1
            if depth == 0:
                return j + 1
    return -1


def split_functions(text, lang=JASS):
    if lang == JASS:
        return dict((m.group(1), m.group(0)) for m in _RX_JASS_FUNCTION.finditer(text))
    out = {}
    marks = [(m.group(1), m.start(1), m.end(1)) for m in _LUA_TOKEN.finditer(text)]
    depth, start, name = 0, None, None
    for k, (t, s, e) in enumerate(marks):
        if t in ('function', 'if', 'do', 'repeat'):
            if depth == 0 and t == 'function' and k + 2 < len(marks) and _is_word(marks[k + 1][0]) and (
                    marks[k + 2][0] == '('):
                name = marks[k + 1][0]
                start = marks[k - 1][1] if k > 0 and marks[k - 1][0] == 'local' else s
            depth += 1
        elif t in ('end', 'until'):
            depth -= 1
            if depth == 0 and name is not None:
                out[name] = text[start:e]
                name = None
            depth = max(depth, 0)
    return out


def closure(functions_by_name, root):
    seen, order, stack = set(), [], [root]
    while stack:
        name = stack.pop()
        if name in seen or name not in functions_by_name:
            continue
        seen.add(name)
        order.append(name)
        stack.extend(reversed(RX_REF.findall(_code_only(functions_by_name[name]))))
    return order


def _code_only(text):
    comment = r'//[^\r\n]*' if 'endfunction' in text else r'//[^\r\n]*|--[^\r\n]*'
    return re.sub(comment + r'|"(?:[^"\\\r\n]|\\.)*"', ' ', text)


def _simple_expr(body, lang):
    b = [t for t in body if t != '\n']
    if b[:1] == ['constant']:
        b = b[1:]
    if lang == JASS:
        head, tail = b[2:6], b[-1:]
        if head != ['takes', 'nothing', 'returns', 'boolean'] or tail != ['endfunction'] or b[6:7] != ['return']:
            return None
        expr = b[7:-1]
    else:
        if b[2:4] != ['(', ')'] or b[4:5] != ['return'] or b[-1:] != ['end']:
            return None
        expr = b[5:-1]
        if expr[-1:] == [';']:
            expr = expr[:-1]
    statement = ('return', 'end', 'local', 'set', 'call', 'if', 'loop') + (('function',) if lang == LUA else ())
    if not expr or any(t in statement for t in expr):
        return None
    return expr


def _inline_simple(toks, lang):
    spans = _function_spans(toks, lang)
    simple = {}
    headers = set()
    for name, s, e in spans:
        headers.add(s + 1 if toks[s] == 'function' else s + 2)
        ex = _simple_expr(toks[s:e], lang)
        if ex is not None:
            simple[name] = ex
    if not simple:
        return toks

    def subst(seq, offset=None):
        out, i = [], 0
        while i < len(seq):
            t = seq[i]
            if (t in simple and seq[i + 1:i + 3] == ['(', ')'] and not (i > 0 and seq[i - 1] == 'function') and
                    (offset is None or offset + i not in headers)):
                ex = simple[t]
                out.extend(ex if ex[0] == '(' and _close(ex, 0) == len(ex) - 1 else ['('] + ex + [')'])
                i += 3
                continue
            out.append(t)
            i += 1
        return out

    for _i in range(8):
        new = dict((n, subst(e)) for n, e in simple.items())
        if new == simple:
            break
        simple = new
    valued, called = set(), set()
    for i, t in enumerate(toks):
        if t in simple and i not in headers:
            if lang == JASS and i > 0 and toks[i - 1] == 'function':
                valued.add(t)
            elif lang == LUA and toks[i + 1:i + 2] != ['('] and not (i > 0 and toks[i - 1] == 'function'):
                valued.add(t)
            elif toks[i + 1:i + 3] == ['(', ')']:
                called.add(t)
    out, pos = [], 0
    for name, s, e in spans:
        out.extend(subst(toks[pos:s], pos))
        if name not in simple or name in valued or name not in called:
            out.extend(subst(toks[s:e], s))
        pos = e
    out.extend(subst(toks[pos:], pos))
    return out


def _self_trigger(toks):
    for i, t in enumerate(toks):
        if t == 'function' and toks[i + 1:i + 2] and toks[i + 1].startswith('InitTrig_'):
            return toks[i + 1][len('InitTrig_'):]
    for i, t in enumerate(toks):
        if t.startswith('gg_trg_') and toks[i + 1:i + 3] == ['=', 'CreateTrigger']:
            return t[len('gg_trg_'):]
    return None


def _jass_parens(script):
    from doctor.script import jass_ast as existing

    def expr(e):
        t = type(e)
        if t is existing.Paren:
            return expr(e.inner)
        if t is existing.Binary:
            left, right = expr(e.left), expr(e.right)
            if e.op == '+' and all(type(x) is existing.Literal and x.kind == 'string' for x in (left, right)):
                return existing.Literal('string', left.text[:-1] + right.text[1:])
            return existing.Paren(existing.Binary(e.op, left, right))
        if t is existing.Unary:
            return existing.Unary(e.op, expr(e.operand))
        if t is existing.Call:
            return existing.Call(e.name, [expr(a) for a in e.args])
        if t is existing.Index:
            return existing.Index(expr(e.base), expr(e.index))
        return e

    def stmt(s):
        t = type(s)
        if t is existing.SetStmt:
            s.target, s.value = expr(s.target), expr(s.value)
        elif t is existing.CallStmt:
            s.call = expr(s.call)
        elif t is existing.IfStmt:
            s.branches = [(None if c is None else expr(c), body) for c, body in s.branches]
            for _c, body in s.branches:
                for x in body:
                    stmt(x)
        elif t is existing.LoopStmt:
            for x in s.body:
                stmt(x)
        elif t is existing.ExitWhenStmt:
            s.cond = expr(s.cond)
        elif t is existing.ReturnStmt and s.value is not None:
            s.value = expr(s.value)
        elif t is existing.DebugStmt:
            stmt(s.stmt)

    for item in script.items:
        decls = (
            item.decls if type(item) is existing.Globals else item.locals if type(item) is existing.Function else [item]
        )
        for d in decls:
            if getattr(d, 'initializer', None) is not None:
                d.initializer = expr(d.initializer)
        for s in (item.body if type(item) is existing.Function and not item.is_native else ()):
            stmt(s)


def _lua_parens(body):
    from doctor.script import lua_ast as la

    def values(vs, targets=None):
        out = [expr(v) for v in vs[:-1]]
        if vs:
            last, inner = vs[-1], vs[-1]
            while type(inner) is la.Paren:
                inner = inner.inner
            cuts = type(inner) is la.Call or (type(inner) is la.Literal and inner.kind == 'vararg')
            keep = cuts and type(last) is la.Paren and (targets is None or targets > len(vs))
            out.append(la.Paren(expr(inner)) if keep else expr(last))
        return out

    def expr(e):
        t = type(e)
        if t is la.Paren:
            return expr(e.inner)
        if t is la.Binary:
            left, right = expr(e.left), expr(e.right)
            if e.op == '..' and all(type(x) is la.Literal and x.kind == 'string' for x in (left, right)):
                quoted = all((x.text or '')[:1] == '"' for x in (left, right))
                return la.Literal('string', left.text[:-1] + right.text[1:] if quoted else None,
                                  left.value + right.value)
            return la.Paren(la.Binary(e.op, left, right))
        if t is la.Unary:
            return la.Unary(e.op, expr(e.operand))
        if t is la.Call:
            return la.Call(expr(e.func), values(e.args), e.method)
        if t is la.Index:
            return la.Index(expr(e.base), expr(e.key), e.dot)
        if t is la.Table:
            positional = [k for k, (key, _v) in enumerate(e.fields) if key is None]
            last = positional[-1] if positional else -1
            return la.Table([(key if key is None or isinstance(key, str) else expr(key),
                              values([v])[0] if k == last else expr(v)) for k, (key, v) in enumerate(e.fields)])
        if t is la.FunctionExpr:
            block(e.body)
        return e

    def block(stmts):
        for s in stmts:
            t = type(s)
            if t is la.LocalStmt:
                s.values = values(s.values, len(s.names))
            elif t is la.AssignStmt:
                s.targets, s.values = [expr(x) for x in s.targets], values(s.values, len(s.targets))
            elif t is la.CallStmt:
                s.call = expr(s.call)
            elif t is la.ReturnStmt:
                s.values = values(s.values)
            elif t is la.IfStmt:
                s.branches = [(None if c is None else expr(c), b) for c, b in s.branches]
                for _c, b in s.branches:
                    block(b)
            elif t in (la.WhileStmt, la.RepeatStmt):
                s.cond = expr(s.cond)
                block(s.body)
            elif t is la.NumericForStmt:
                s.start, s.stop = expr(s.start), expr(s.stop)
                s.step = None if s.step is None else expr(s.step)
                block(s.body)
            elif t is la.GenericForStmt:
                s.exprs = values(s.exprs, 3)
                block(s.body)
            elif t in (la.FunctionStmt, la.DoStmt):
                block(s.body)

    block(body)


def _reparenthesized(toks, lang, inline=False):
    from doctor.script import jass_ast
    from doctor.script import lua_ast
    text = ' '.join(toks)
    old = sys.getrecursionlimit()
    sys.setrecursionlimit(max(old, 20000))
    try:
        if lang == LUA:
            chunk = lua_ast.parse(text)
            _lua_parens(chunk.body)
            out = lua_ast.unparse(chunk)
        else:
            from doctor.script import jass_normal
            script = jass_normal.normalize(jass_ast.parse(text), inline=inline)
            _jass_parens(script)
            out = jass_ast.unparse(script, comments=False)
    except (jass_ast.JassSyntaxError, lua_ast.LuaSyntaxError, RecursionError):
        return None
    finally:
        sys.setrecursionlimit(old)
    return tokens(out, lang)


_CANONICAL = {}
CANONICAL_CACHE = 20000


_NATIVE = [None]


def _native():
    if _NATIVE[0] is None:
        try:
            from doctor.script import jass_native
            _NATIVE[0] = jass_native.load_canonical() or False
        except Exception:
            _NATIVE[0] = False
    return _NATIVE[0]


def canonical(text, lang=JASS, inline=True, self_name=None):
    k = (text, lang, inline, self_name)
    out = _CANONICAL.get(k)
    if out is None:
        nat = _native()
        out = nat(text, lang, inline, self_name) if nat else None
        if out is None:
            out = _canonical(text, lang, inline, self_name)
        if len(_CANONICAL) >= CANONICAL_CACHE:
            _CANONICAL.clear()
        _CANONICAL[k] = out
    return out


def _canonical(text, lang=JASS, inline=True, self_name=None):
    toks = tokens(text, lang)
    tree = _reparenthesized(toks, lang, inline) if lang == JASS else None
    if tree is None and inline:
        toks = _inline_simple(toks, lang)
    if lang == LUA:
        tree = _reparenthesized(toks, lang)
    if self_name is None:
        self_name = _self_trigger(toks)
    own = 'gg_trg_' + self_name if self_name else None
    names = {}
    out = []
    for t in (toks if tree is None else tree):
        if t.startswith(('Trig_', 'InitTrig_')) and _is_word(t):
            t = names.setdefault(t, 'F%d' % (len(names) + 1))
        elif t == own:
            t = 'gg_trg_SELF'
        else:
            t = _norm_literal(t)
        out.append(t)
    if tree is None:
        out = _strip_parens(_strip_right_sides(out, lang))
    return '\n'.join(_join(line) for line in (_lua_lines(out) if lang == LUA else _lines(out)))


PRESET, VARIABLE, FUNCTION, LITERAL = 0, 1, 2, 3
COMMENT_ITEM = 16
EVENT, CONDITION, ACTION, CALL = 0, 1, 2, 3
CALLBACK_MULTIPLE = frozenset(('ForGroupMultiple', 'ForForceMultiple', 'EnumDestructablesInRectAllMultiple',
                               'EnumDestructablesInCircleBJMultiple', 'EnumItemsInRectBJMultiple'))
FOR_LOOPS = {'ForLoopA': 'A', 'ForLoopB': 'B', 'ForLoopAMultiple': 'A', 'ForLoopBMultiple': 'B'}
ARITHMETIC = frozenset(('OperatorInt', 'OperatorReal', 'OperatorString'))
OBJECT_TYPES = (('gg_unit_', 'unit'), ('gg_rct_', 'rect'), ('gg_cam_', 'camerasetup'), ('gg_snd_', 'sound'),
                ('gg_trg_', 'trigger'), ('gg_dest_', 'destructable'), ('gg_item_', 'item'))
RX_INTEGER = re.compile(r'^-?(?:\d+|0[xX][0-9A-Fa-f]+|\$[0-9A-Fa-f]+)$')


def _escape(s):
    return s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')


def _multiple_groups(f):
    groups = {}
    for k, c in enumerate(f.children, 1):
        groups.setdefault(c.branch or 0, []).append((k, c))
    return groups


class _Syntax(object):
    def __init__(self, td, lang):
        self.td, self.lang = td, lang
        self.lua = lang == LUA

    def rawcode(self, code):
        return 'FourCC("%s")' % code if self.lua else "'%s'" % code

    def script_code(self, code):
        if not self.lua:
            return code
        if code == 'null':
            return 'nil'
        if code == '!=':
            return '~='
        m = re.match(r"^'(.{4})'$", code)
        return self.rawcode(m.group(1)) if m else code

    def preset(self, name, gui_type):
        preset = self.td.presets.get(name)
        if preset is None:
            return name
        if self.lua and preset.code == 'null' and gui_type and self.td.base_type(gui_type) == 'string':
            return '""'
        return self.script_code(preset.code)

    def literal(self, text, gui_type):
        base = self.td.base_type(gui_type) if gui_type else None
        if gui_type == 'scriptcode':
            return text
        if base == 'string':
            return '"%s"' % _escape(text)
        if base == 'integer' and gui_type != 'integer' and (not RX_INTEGER.match(text) or
                                                             (len(text) == 4 and text.isalnum())):
            return self.rawcode(text)
        return text


class _Trigger(_Syntax):
    def __init__(self, trigger, td, mt, lang):
        _Syntax.__init__(self, td, lang)
        self.trigger = trigger
        self.id = trigger_identifier(trigger.name)
        self.prefix = 'Trig_%s_' % self.id
        self.functions = []
        self.var_types = dict((v.name, v.type) for v in (mt.variables if mt is not None else ()))

    def define(self, name, returns, body):
        if self.lua:
            lines = ['function %s()' % name] + [line for _d, line in body] + ['end']
        else:
            lines = ['function %s takes nothing returns %s' % (name, 'boolean' if returns else 'nothing')]
            lines += [('    ' * d + line) if line else '' for d, line in body] + ['endfunction']
        self.functions.append((name, '\n'.join(lines)))
        return name

    def ref(self, name):
        return name if self.lua else 'function ' + name

    def call(self, name, args):
        return '%s(%s)' % (name, ', '.join(args)) if self.lua else 'call %s(%s)' % (name, ', '.join(args))

    def assign(self, lhs, rhs):
        return '%s = %s' % (lhs, rhs) if self.lua else 'set %s = %s' % (lhs, rhs)

    def paren(self, text):
        return '(%s)' % text if self.lua else '( %s )' % text

    def if_open(self, cond):
        return 'if (%s) then' % cond if self.lua else 'if ( %s ) then' % cond

    def end_if(self):
        return 'end' if self.lua else 'endif'

    def arg_types(self, f):
        fd = self.td.get(f.kind, f.name)
        return list(fd.arg_types) if fd is not None else []

    def script_name(self, f):
        fd = self.td.get(f.kind, f.name)
        return fd.script_name if fd is not None else f.name

    def variable_type(self, name):
        if name in self.var_types:
            return self.var_types[name]
        for prefix, gui_type in OBJECT_TYPES:
            if name.startswith(prefix):
                return gui_type
        return None

    def variable(self, p, path):
        name = p.value if p.value.startswith('gg_') else 'udg_' + p.value
        if p.index is not None:
            name += '[%s]' % self.value(p.index, 'integer', path)
        return name

    def value(self, p, gui_type, path):
        if p.kind == PRESET:
            return self.preset(p.value, gui_type)
        if p.kind == VARIABLE:
            if gui_type == 'VarAsString_Real':
                return '"%s"' % self.variable(p, path)
            return self.variable(p, path)
        if p.kind == LITERAL:
            return self.literal(p.value, gui_type)
        if p.kind == FUNCTION and p.function is not None:
            return self.function_value(p.function, gui_type, path)
        return ''

    def function_value(self, f, gui_type, path):
        if gui_type == 'boolexpr':
            name = self.define(self.prefix + path, True, [(1, 'return ' + self.condition(f, path))])
            return 'Condition(%s)' % self.ref(name)
        if gui_type == 'boolcall':
            name = self.define(self.prefix + path, True, [(1, 'return ' + self.condition(f, path))])
            return name + '()'
        if gui_type == 'code':
            name = self.define(self.prefix + path, False, self.statements(f, path, 1))
            return self.ref(name)
        if f.kind == CONDITION:
            return self.condition(f, path)
        return self.expression(f, path)

    def args(self, f, path, skip=()):
        types = self.arg_types(f)
        return [self.value(p, types[i] if i < len(types) else None, path + '%03d' % (i + 1))
                for i, p in enumerate(f.params) if i not in skip]

    def expression(self, f, path):
        if f.name in ARITHMETIC:
            types = self.arg_types(f)
            a = self.value(f.params[0], types[0], path + '001')
            if f.name == 'OperatorString':
                b = self.value(f.params[1], types[1], path + '002')
                return self.paren('%s %s %s' % (a, '..' if self.lua else '+', b))
            op = self.value(f.params[1], types[1], path + '002')
            b = self.value(f.params[2], types[2], path + '003')
            if self.lua and op == '/' and f.name == 'OperatorInt':
                op = '//'
            return self.paren('%s %s %s' % (a, op, b))
        return '%s(%s)' % (self.script_name(f), ', '.join(self.args(f, path)))

    def condition(self, f, path):
        if f.name.startswith('OperatorCompare') and len(f.params) == 3:
            types = self.arg_types(f)
            a = self.value(f.params[0], types[0], path + '001')
            op = self.value(f.params[1], types[1], path + '002')
            b = self.value(f.params[2], types[2], path + '003')
            return self.paren('%s %s %s' % (a, op, b))
        if f.name in ('AndMultiple', 'OrMultiple'):
            return self.multiple_condition(f, path) + '()'
        return self.expression(f, path)

    def multiple_condition(self, f, path):
        body = []
        for k, c in _multiple_groups(f).get(0, []):
            if not c.enabled:
                continue
            cond = self.condition(c, path + 'Func%03d' % k)
            if f.name == 'OrMultiple':
                body += [(1, self.if_open(cond) if not self.lua else 'if %s then' % cond), (2, 'return true'),
                         (1, self.end_if())]
            else:
                body += [(1, self.if_open('not ' + cond)), (2, 'return false'), (1, self.end_if())]
        body.append((1, 'return false' if f.name == 'OrMultiple' else 'return true'))
        return self.define(self.prefix + path + 'C', True, body)

    def statements(self, f, path, depth):
        if not f.enabled:
            return []
        name = f.name
        if name == 'CommentString':
            return [] if self.lua else [(depth, '// ' + f.params[0].value)]
        if name == 'CustomScriptCode':
            return [(depth, f.params[0].value)]
        if name == 'ReturnAction':
            return [(depth, 'return ' if self.lua else 'return')]
        if name == 'SetVariable':
            var = f.params[0]
            lhs = self.variable(var, path + '001')
            rhs = self.value(f.params[1], self.variable_type(var.value), path + '002')
            return [(depth, self.assign(lhs, rhs))]
        if name == 'IfThenElseMultiple':
            return self.if_multiple(f, path, depth)
        if name == 'IfThenElse':
            return self.if_one_line(f, path, depth)
        if name in FOR_LOOPS or name in ('ForLoopVar', 'ForLoopVarMultiple'):
            return self.for_loop(f, path, depth)
        if name in CALLBACK_MULTIPLE:
            args = self.args(f, path)
            callback = self.define(self.prefix + path + 'A', False, self.block(f.children, path, 1))
            return [(depth, self.call(self.script_name(f), args + [self.ref(callback)]))]
        if name == 'WaitForCondition':
            return self.wait_for_condition(f, path, depth)
        if name == 'AddTriggerEvent' and len(f.params) == 2 and f.params[1].function is not None:
            event = f.params[1].function
            trig = self.value(f.params[0], 'trigger', path + '001')
            return [(depth, self.call(self.script_name(event), [trig] + self.args(event, path + '002')))]
        line = self.call(self.script_name(f), self.args(f, path))
        self.orphans(f, path)
        return [(depth, line)]

    def orphans(self, f, path):
        for k, c in enumerate(f.children, 1):
            if (c.branch or 0) == 0 and c.kind == CONDITION:
                if c.enabled:
                    self.condition(c, path + 'Func%03d' % k)
            else:
                self.statements(c, path + 'Func%03d' % k, 1)

    def block(self, children, path, depth, branch=None):
        out = []
        for k, c in enumerate(children, 1):
            if branch is None or (c.branch or 0) == branch:
                out += self.statements(c, path + 'Func%03d' % k, depth)
        return out

    def if_multiple(self, f, path, depth):
        body, then, other = [], [], []
        for k, c in enumerate(f.children, 1):
            sub = path + 'Func%03d' % k
            if (c.branch or 0) == 0:
                if c.enabled:
                    body += [(1, self.if_open('not ' + self.condition(c, sub))), (2, 'return false'),
                             (1, self.end_if())]
            else:
                (then if c.branch == 1 else other).extend(self.statements(c, sub, depth + 1))
        body.append((1, 'return true'))
        cond = self.define(self.prefix + path + 'C', True, body)
        return [(depth, self.if_open(cond + '()'))] + then + [(depth, 'else')] + other + [(depth, self.end_if())]

    def if_one_line(self, f, path, depth):
        cond = self.value(f.params[0], 'boolcall', path + '001')
        then = self.inline_action(f.params[1], path + '002', depth + 1)
        other = self.inline_action(f.params[2], path + '003', depth + 1)
        return [(depth, self.if_open(cond))] + then + [(depth, 'else')] + other + [(depth, self.end_if())]

    def inline_action(self, p, path, depth):
        return self.statements(p.function, path, depth) if p.kind == FUNCTION and p.function is not None else []

    def for_loop(self, f, path, depth):
        types = self.arg_types(f)
        if f.name.startswith('ForLoopVar'):
            index = end_name = self.variable(f.params[0], path + '001')
            start = self.value(f.params[1], types[1], path + '002')
            end = self.value(f.params[2], types[2], path + '003')
            head = [(depth, self.assign(index, start))]
        else:
            index = 'bj_forLoop%sIndex' % FOR_LOOPS[f.name]
            end_name = index + 'End'
            start = self.value(f.params[0], types[0], path + '001')
            end = self.value(f.params[1], types[1], path + '002')
            head = [(depth, self.assign(index, start)), (depth, self.assign(end_name, end))]
        if f.name.endswith('Multiple'):
            body = self.block(f.children, path, depth + 1)
        else:
            k = len(f.params)
            body = self.inline_action(f.params[k - 1], path + '%03d' % k, depth + 1)
        limit = end if f.name.startswith('ForLoopVar') else end_name
        step = self.assign(index, '%s + 1' % index)
        if self.lua:
            test = [(depth + 1, 'if (%s > %s) then break end' % (index, limit))]
            return head + [(depth, 'while (true) do')] + test + body + [(depth + 1, step), (depth, 'end')]
        return (head + [(depth, 'loop'), (depth + 1, 'exitwhen %s > %s' % (index, limit))] + body +
                [(depth + 1, step), (depth, 'endloop')])

    def wait_for_condition(self, f, path, depth):
        cond = self.value(f.params[0], 'boolcall', path + '001')
        sleep = self.call('TriggerSleepAction', ['RMaxBJ(bj_WAIT_FOR_COND_MIN_INTERVAL, %s)' % self.value(
            f.params[1], self.arg_types(f)[1], path + '002')])
        if self.lua:
            return [(depth, 'while (true) do'), (depth + 1, 'if (%s) then break end' % self.paren(cond)),
                    (depth + 1, sleep), (depth, 'end')]
        return [(depth, 'loop'), (depth + 1, 'exitwhen %s' % self.paren(cond)), (depth + 1, sleep),
                (depth, 'endloop')]

    def render(self):
        t = self.trigger
        path_of = dict((id(f), 'Func%03d' % k) for k, f in enumerate(t.functions, 1))
        conditions = [f for f in t.functions if f.kind == CONDITION and f.enabled]
        actions = [f for f in t.functions if f.kind == ACTION]
        events = [f for f in t.functions if f.kind == EVENT and f.enabled]
        cond_name = None
        if conditions:
            body = []
            for f in conditions:
                body += [(1, self.if_open('not ' + self.condition(f, path_of[id(f)]))), (2, 'return false'),
                         (1, self.end_if())]
            body.append((1, 'return true'))
            cond_name = self.define(self.prefix + 'Conditions', True, body)
        body = []
        for f in actions:
            body += self.statements(f, path_of[id(f)], 1)
        action_name = self.define(self.prefix + 'Actions', False, body)
        own = 'gg_trg_' + self.id
        init = [(1, self.assign(own, 'CreateTrigger()'))]
        if t.initially_off:
            init.append((1, self.call('DisableTrigger', [own])))
        for f in events:
            if f.name != 'MapInitializationEvent':
                init.append((1, self.call(self.script_name(f), [own] + self.args(f, path_of[id(f)]))))
        if cond_name:
            init.append((1, self.call('TriggerAddCondition', [own, 'Condition(%s)' % self.ref(cond_name)])))
        init.append((1, self.call('TriggerAddAction', [own, self.ref(action_name)])))
        self.define('InitTrig_' + self.id, False, init)
        return self.functions


def _banner(trigger, lang):
    lines = [BANNER, '// Trigger: ' + trigger.name]
    if trigger.description:
        lines.append('//')
        lines += [('// ' + x).rstrip() for x in re.split(r'\r\n?|\n', trigger.description)]
    lines.append(BANNER)
    return [] if lang == LUA else lines


def render_trigger(trigger, td, mt, lang=JASS, text=None):
    lang = LUA if lang == LUA else JASS
    if trigger.is_comment:
        return ''
    if trigger.is_text:
        body = text if text is not None else getattr(trigger, 'text', None) or ''
        return body if lang == LUA else '\n'.join(_banner(trigger, lang)) + '\n' + body
    functions = _Trigger(trigger, td, mt, lang).render()
    if lang == LUA:
        return '\n\n'.join(t for _n, t in functions) + '\n'
    out = _banner(trigger, lang)
    for name, text_ in functions:
        if name.startswith('InitTrig_'):
            out.append(BANNER)
        out.append(text_)
        out.append('')
    return '\n'.join(out)


def _script_type(td, gui_type):
    return td.base_type(gui_type) if gui_type in td.types else gui_type


def _default(td, v, lua):
    syntax = _Syntax(td, LUA if lua else JASS)
    base = _script_type(td, v.type)
    if v.initialized and v.initial_value != '':
        if v.initial_value in td.presets:
            return syntax.preset(v.initial_value, v.type)
        return syntax.literal(v.initial_value, v.type)
    if v.type in td.type_defaults:
        value = td.type_defaults[v.type]
        return '0.0' if lua and base == 'real' and value == '0' else syntax.script_code(value)
    if base == 'string':
        return '""'
    return None


def _declared(td, v, lua):
    base = _script_type(td, v.type)
    if v.is_array:
        if not lua:
            return None
        return {'integer': '__jarray(0)', 'real': '__jarray(0.0)', 'boolean': '__jarray(false)',
                'string': '__jarray("")'}.get(base, '{}')
    if base == 'string':
        return '""' if lua else None
    return {'boolean': 'false', 'integer': '0', 'real': '0.0' if lua else '0'}.get(base, 'nil' if lua else 'null')


def _enabled_triggers(mt, editor=False):
    out = [(k, t) for k, t in enumerate(mt.triggers) if t.enabled and not t.is_comment]
    if editor and not getattr(mt, 'tree_order', False):
        place = dict((c.id, k) for k, c in enumerate(mt.categories))
        out.sort(key=lambda kt: (place.get(kt[1].category_id, len(place)), kt[0]))
    return [t for _k, t in out]


def render_globals(mt, td, lang=JASS):
    lua = lang == LUA
    comment_items = set(id(item) for c, item in (mt.elements or ()) if c == COMMENT_ITEM)
    idents, seen = [], set()
    for t in mt.triggers:
        ident = trigger_identifier(t.name)
        if ident not in seen and id(t) not in comment_items:
            idents.append(ident)
            seen.add(ident)
    if lua:
        lines = ['udg_%s = %s' % (v.name, _declared(td, v, True)) for v in mt.variables]
        return '\n'.join(lines + ['gg_trg_%s = nil' % i for i in idents]) + '\n'
    lines = ['globals', '    // User-defined']
    for v in mt.variables:
        decl = '%s array' % _script_type(td, v.type) if v.is_array else _script_type(td, v.type)
        init = _declared(td, v, False)
        lines.append(('    %-23s %-26s = %s' % (decl, 'udg_' + v.name, init)) if init is not None else
                     ('    %-23s %s' % (decl, 'udg_' + v.name)))
    lines += ['', '    // Generated']
    lines += ['    %-23s %-26s = null' % ('trigger', 'gg_trg_' + i) for i in idents]
    return '\n'.join(lines + ['endglobals']) + '\n'


def render_init_globals(mt, td, lang=JASS):
    lua = lang == LUA
    if not mt.variables:
        return ''
    body = []
    arrays = any(v.is_array for v in mt.variables)
    for v in mt.variables:
        value = _default(td, v, lua)
        if value is None:
            continue
        name = 'udg_' + v.name
        if not v.is_array:
            body.append(('%s = %s' if lua else '    set %s = %s') % (name, value))
            continue
        if lua:
            body += ['i = 0', 'while (true) do', 'if ((i > %d)) then break end' % v.array_size,
                     '%s[i] = %s' % (name, value), 'i = i + 1', 'end']
        else:
            body += ['    set i = 0', '    loop', '        exitwhen (i > %d)' % v.array_size,
                     '        set %s[i] = %s' % (name, value), '        set i = i + 1', '    endloop', '']
    if lua:
        head = ['function InitGlobals()'] + (['local i = 0', ''] if arrays else [])
        return '\n'.join(head + body + ['end']) + '\n'
    head = ['function InitGlobals takes nothing returns nothing'] + (['    local integer i = 0'] if arrays else [])
    return '\n'.join(head + body + ['endfunction']) + '\n'


def render_init_custom_triggers(mt, lang=JASS, editor=False, texts=None):
    sem_init = set()
    if texts is not None and len(texts) == len(mt.triggers):
        for t, tx in zip(mt.triggers, texts):
            if t.is_text and tx is not None:
                i = trigger_identifier(t.name)
                padrao = (
                    r'\bfunction\s+InitTrig_%s\b' if lang != LUA else r'\bInitTrig_%s\s*=|\bfunction\s+InitTrig_%s\b'
                )
                if not re.search(padrao.replace('%s', re.escape(i)), tx):
                    sem_init.add(id(t))
    if lang == LUA:
        idents = [trigger_identifier(t.name) for t in _enabled_triggers(mt, editor)
                  if id(t) not in sem_init and not getattr(t, 'script_item', False)]
        return '\n'.join(['function InitCustomTriggers()'] + ['InitTrig_%s()' % i for i in idents] + ['end']) + '\n'
    linhas = [('    //Function not found: call InitTrig_%s()' if id(t) in sem_init else '    call InitTrig_%s()')
              % trigger_identifier(t.name) for t in _enabled_triggers(mt, editor)
              if not getattr(t, 'script_item', False)]
    return '\n'.join([BANNER, 'function InitCustomTriggers takes nothing returns nothing'] + linhas +
                     ['endfunction']) + '\n'


def initialization_triggers(mt, editor=False):
    out = []
    for t in _enabled_triggers(mt, editor):
        event = any(f.kind == EVENT and f.name == 'MapInitializationEvent' and f.enabled for f in t.functions)
        if (event or (t.run_on_init and t.is_text)) and not t.initially_off:
            out.append(t)
    return out


def render_run_initialization_triggers(mt, lang=JASS, editor=False):
    idents = [trigger_identifier(t.name) for t in initialization_triggers(mt, editor)]
    if not idents:
        return ''
    if lang == LUA:
        return '\n'.join(['function RunInitializationTriggers()'] +
                         ['ConditionalTriggerExecute(gg_trg_%s)' % i for i in idents] + ['end']) + '\n'
    return '\n'.join([BANNER, 'function RunInitializationTriggers takes nothing returns nothing'] +
                     ['    call ConditionalTriggerExecute(gg_trg_%s)' % i for i in idents] + ['endfunction']) + '\n'


def compare_trigger(trigger, td, mt, script, lang=JASS, text=None, functions=None):
    real = functions if functions is not None else split_functions(script, lang)
    root = 'InitTrig_' + trigger_identifier(trigger.name)
    mine = split_functions(render_trigger(trigger, td, mt, lang, text), lang)
    for name in closure(collections.ChainMap(mine, real), root):
        if name not in mine:
            mine[name] = real[name]
    a = canonical('\n'.join(mine[n] for n in closure(mine, root)), lang, self_name=root[9:])
    b = canonical('\n'.join(real[n] for n in closure(real, root)), lang, self_name=root[9:])
    return a == b, a, b


def _read(path, mode='rb'):
    with open(path, mode) as f:
        return f.read()

