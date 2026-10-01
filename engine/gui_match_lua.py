# Turns the Lua of a trigger back into the GUI events, conditions and actions it came from.
import collections
import copy
import os
import re

import lua_ast
import wtg


HERE = os.path.dirname(os.path.abspath(__file__))
REF_DIR = os.path.join(HERE, '..', 'ref', '3.0')
EVENT, CONDITION, ACTION, CALL = wtg.EVENT, wtg.CONDITION, wtg.ACTION, wtg.CALL
PRESET, VARIABLE, FUNCTION, LITERAL = wtg.PRESET, wtg.VARIABLE, wtg.FUNCTION, wtg.LITERAL
COMPARISONS = {'==': '==', '~=': '!=', '<': '<', '<=': '<=', '>': '>', '>=': '>='}
ARITHMETIC = frozenset(('+', '-', '*', '/', '//'))
CUSTOM_GLOBAL = '<custom script>'
OBJECT_TYPES = (('gg_unit_', 'unit'), ('gg_rct_', 'rect'), ('gg_cam_', 'camerasetup'), ('gg_snd_', 'sound'),
                ('gg_trg_', 'trigger'), ('gg_dest_', 'destructable'), ('gg_item_', 'item'))
CALLBACK_FORMS = {'ForGroup': 'ForGroupMultiple', 'ForForce': 'ForForceMultiple',
                  'EnumDestructablesInRectAll': 'EnumDestructablesInRectAllMultiple',
                  'EnumDestructablesInCircleBJ': 'EnumDestructablesInCircleBJMultiple',
                  'EnumItemsInRectBJ': 'EnumItemsInRectBJMultiple'}
LOOP_FORMS = {'A': ('ForLoopA', 'ForLoopAMultiple'), 'B': ('ForLoopB', 'ForLoopBMultiple'),
              'Var': ('ForLoopVar', 'ForLoopVarMultiple')}
MULTIPLE_TO_ONE = dict((m, o) for o, m in list(CALLBACK_FORMS.items()) + list(LOOP_FORMS.values()))
ONE_LINE_DEFAULT = {'ForLoopA': False, 'ForLoopB': False, 'ForLoopVar': False, 'ForGroup': False, 'ForForce': False,
                    'EnumDestructablesInRectAll': False, 'EnumDestructablesInCircleBJ': False,
                    'EnumItemsInRectBJ': False}
LITERAL_TYPES = frozenset(('abilityuiyesnooption', 'disabledenabledoption', 'hideshowoption'))
PRESET_PREFERENCE = {('unitorderptarg', '"rainoffire"'): 'UnitOrderRainOfFire',
                     ('unitorderutarg', '"darkconversion"'): 'UnitOrderDarkConversionFast',
                     ('unitordernotarg', '"ravenform"'): 'UnitOrderMedivhRavenForm',
                     ('unitordernotarg', '"unravenform"'): 'UnitOrderMedivhUnRavenForm',
                     ('heroskillcode', "'ANrf'"): 'HeroSkillVarimRainOfFire'}
CUSTOM_SCRIPT_IDIOMS = frozenset(('RemoveLocation', 'DestroyGroup'))
REGISTRATION = frozenset(('CreateTrigger', 'DisableTrigger', 'TriggerAddCondition', 'TriggerAddAction'))
RX_EDITOR_HELPER = re.compile(r'^Func\d{3}(?:Func\d{3}|\d{3})*(?:C|A|\d{3})$')
RX_LINE_BREAK = re.compile(r'\r\n|\r|\n')
RX_INTEGER = re.compile(r'^-?(?:\d+|0[xX][0-9A-Fa-f]+)$')
RX_REAL = re.compile(r'^-?(?:\d+\.\d*|\.\d+)(?:[eE][-+]?\d+)?$|^-?\d+[eE][-+]?\d+$')
RAWCODE_VARIABLE_TYPE = 'unitcode'
JARRAY = {'0': 'integer', '0.0': 'real', 'false': 'boolean', '""': 'string'}


class Match(object):
    __slots__ = ('trigger', 'reason', 'helpers', 'external', 'custom_lines')

    def __init__(self, trigger=None, reason='', helpers=None, external=None, custom_lines=0):
        self.trigger = trigger
        self.reason = reason
        self.helpers = helpers or []
        self.external = external or []
        self.custom_lines = custom_lines

    def __repr__(self):
        what = ('%r, %d functions' % (self.trigger.name, len(self.trigger.functions)) if self.trigger
                else 'no model: %s' % self.reason)
        return 'Match(%s, %d helpers, %d external, %d custom lines)' % (what, len(self.helpers), len(self.external),
                                                                      self.custom_lines)


class _Fail(Exception):
    pass


def _bare(e):
    while type(e) is lua_ast.Paren:
        e = e.inner
    return e


def _name(e):
    e = _bare(e)
    return e.name if type(e) is lua_ast.Name else None


def _callee(e):
    if type(e) is lua_ast.Call and e.method is None and type(e.func) is lua_ast.Name:
        return e.func.name
    return None


def _is_literal(e, text):
    e = _bare(e) if e is not None else None
    return type(e) is lua_ast.Literal and e.text == text


def _text(node):
    return lua_ast.unparse(node)


def _same_code(a, b):
    try:
        return lua_ast.canonical(a) == lua_ast.canonical(b)
    except lua_ast.LuaSyntaxError:
        return False


def _children(n):
    t = type(n)
    if t is lua_ast.Name or t is lua_ast.Literal:
        return ()
    if t is lua_ast.Call:
        return [n.func] + list(n.args)
    if t is lua_ast.Index:
        return (n.base, n.key)
    if t is lua_ast.Binary:
        return (n.left, n.right)
    if t is lua_ast.Unary:
        return (n.operand,)
    if t is lua_ast.Paren:
        return (n.inner,)
    if t is lua_ast.Table:
        return [x for k, v in n.fields for x in ((k, v) if k is not None and not isinstance(k, str) else (v,))]
    if t is lua_ast.CallStmt:
        return (n.call,)
    if t is lua_ast.AssignStmt:
        return list(n.targets) + list(n.values)
    if t is lua_ast.LocalStmt or t is lua_ast.ReturnStmt:
        return n.values or ()
    if t is lua_ast.IfStmt:
        out = []
        for cond, body in n.branches:
            if cond is not None:
                out.append(cond)
            out.extend(body)
        return out
    if t is lua_ast.WhileStmt:
        return [n.cond] + list(n.body)
    if t is lua_ast.RepeatStmt:
        return list(n.body) + [n.cond]
    if t is lua_ast.NumericForStmt:
        return [n.start, n.stop] + ([n.step] if n.step is not None else []) + list(n.body)
    if t is lua_ast.GenericForStmt:
        return list(n.exprs) + list(n.body)
    if t in (lua_ast.FunctionStmt, lua_ast.FunctionExpr, lua_ast.DoStmt):
        return n.body
    if isinstance(n, list):
        return n
    return ()


def walk(node):
    stack = [node]
    while stack:
        n = stack.pop()
        yield n
        stack.extend(reversed(list(_children(n))))


def _jass_code(e):
    e = _bare(e)
    t = type(e)
    if t is lua_ast.Name:
        return e.name
    if t is lua_ast.Literal:
        if e.kind == 'nil':
            return 'null'
        if e.kind == 'string':
            return e.text if e.text[:1] == '"' else None
        return e.text if e.kind in ('number', 'boolean') else None
    if t is lua_ast.Call:
        f = _callee(e)
        if f is None:
            return None
        if f == 'FourCC' and len(e.args) == 1:
            code = _fourcc(e.args[0])
            return None if code is None else "'%s'" % code
        args = [_jass_code(a) for a in e.args]
        return None if None in args else '%s(%s)' % (f, ','.join(args))
    if t is lua_ast.Index and not e.dot:
        base, key = _jass_code(e.base), _jass_code(e.key)
        return None if base is None or key is None else '%s[%s]' % (base, key)
    if t is lua_ast.Unary and e.op == '-':
        x = _jass_code(e.operand)
        return None if x is None else '-' + x
    return None


def _fourcc(arg):
    a = _bare(arg)
    if type(a) is not lua_ast.Literal or a.kind != 'string' or a.text[:1] != '"' or '\\' in a.text:
        return None
    return a.value if len(a.value) == 4 else None


def _editor_unescape(text):
    if text[:1] != '"' or text[-1:] != '"' or len(text) < 2:
        return None
    body = text[1:-1]
    if '\n' in body or '\r' in body:
        return None
    if '\\' not in body:
        return body
    out, i = [], 0
    while i < len(body):
        c = body[i]
        if c == '\\':
            nxt = body[i + 1:i + 2]
            if nxt not in ('\\', '"', 'n'):
                return None
            out.append('\n' if nxt == 'n' else nxt)
            i += 2
            continue
        out.append(c)
        i += 1
    return ''.join(out)


def _number_kind(text):
    if RX_INTEGER.match(text):
        return 'integer'
    return 'real' if RX_REAL.match(text) else None


def _read_ref(name):
    try:
        with open(os.path.join(REF_DIR, name), 'rb') as f:
            return f.read().decode('utf-8', 'surrogateescape')
    except OSError:
        return ''


class _Knowledge(object):
    def __init__(self, td):
        self.td = td
        self.presets = {}
        self.preset_types = collections.defaultdict(list)
        for p in td.presets.values():
            self.presets.setdefault((p.type, p.code), p.name)
            self.preset_types[p.code].append(p.type)
        for key, name in PRESET_PREFERENCE.items():
            if key in self.presets and name in td.presets:
                self.presets[key] = name
        self.compares = [f for f in td.conditions.values()
                         if len(f.arg_types) == 3 and f.arg_types[1] in ('ComparisonOperator', 'EqualNotEqualOperator')]
        self.operators = {}
        for f in self.compares:
            self.operators[f.arg_types[1]] = frozenset(p.code for p in td.presets.values() if p.type == f.arg_types[1])
        self.extends, self.returns, self.global_types = {}, {}, {}
        for name in ('common.j', 'blizzard.j'):
            text = _read_ref(name)
            for m in re.finditer(r'^\s*type\s+(\w+)\s+extends\s+(\w+)', text, re.M):
                self.extends[m.group(1)] = m.group(2)
            for m in re.finditer(r'^\s*(?:constant\s+)?(?:native|function)\s+(\w+)\s+takes\s.*?\sreturns\s+(\w+)',
                                 text, re.M):
                self.returns.setdefault(m.group(1), m.group(2))
            for block in re.findall(r'(?ms)^\s*globals\s*$(.*?)^\s*endglobals', text):
                for m in re.finditer(r'^\s*(?:constant\s+)?(\w+)\s+(?:array\s+)?(\w+)\s*(?:=|$)', block, re.M):
                    self.global_types.setdefault(m.group(2), m.group(1))

    def base(self, t):
        return self.td.base_type(t) if t else t

    def supertypes(self, t):
        out, seen = [], set()
        while t in self.extends and t not in seen:
            seen.add(t)
            t = self.extends[t]
            out.append(t)
        return out

    def preset(self, code, t):
        if code is None:
            return None
        if t is None:
            types = self.preset_types.get(code)
            return self.presets.get((types[0], code)) if types and len(set(types)) == 1 else None
        return self.presets.get((t, code))

    def calls(self, kind, script_name):
        return self.td.by_script_all.get((kind, script_name), ())


_KNOWLEDGE = {}


def _knowledge(td):
    k = _KNOWLEDGE.get(id(td))
    if k is None or k.td is not td:
        k = _KNOWLEDGE[id(td)] = _Knowledge(td)
    return k


_REFS = {}


def _references(functions):
    hit = _REFS.get(id(functions))
    if hit is not None and hit[0] is functions:
        return hit[1]
    counts = collections.Counter()
    for f in functions.values():
        for node in walk(f.body):
            if type(node) is lua_ast.Name and node.name in functions:
                counts[node.name] += 1
    if len(_REFS) > 8:
        _REFS.clear()
    _REFS[id(functions)] = (functions, counts)
    return counts


def _references_in(node, functions):
    out = []
    for n in walk(node):
        if type(n) is lua_ast.Name and n.name in functions and n.name not in out:
            out.append(n.name)
    return out


def script_functions(chunk):
    out = {}
    for s in chunk.body:
        if type(s) is lua_ast.FunctionStmt and re.match(r'^[A-Za-z_]\w*$', s.name):
            out[s.name] = s
    return out


class _Matcher(object):
    def __init__(self, functions, td, globals_types, prefix=None, source=None):
        self.functions = functions
        self.source = source
        self.td = td
        self.k = _knowledge(td)
        self.types = globals_types or {}
        self.refs = _references(functions)
        self.prefix = prefix
        self.used = []
        self.used_set = set()
        self.custom = 0
        self.loose = []

    def mark(self):
        return len(self.used), self.custom, len(self.loose)

    def reset(self, m):
        for name in self.used[m[0]:]:
            self.used_set.discard(name)
        del self.used[m[0]:]
        self.custom = m[1]
        del self.loose[m[2]:]

    def helper(self, name):
        f = self.functions.get(name) if name else None
        if (f is None or f.params or f.is_vararg or name in self.used_set or self.refs.get(name, 0) != 1):
            return None
        self.used.append(name)
        self.used_set.add(name)
        return f

    def hint(self, name):
        if self.prefix and name and name.startswith(self.prefix) and RX_EDITOR_HELPER.match(name[len(self.prefix):]):
            return 'digits' if name[-1].isdigit() else name[-1]
        return None

    def one_line(self, a):
        if a.name not in self.td.multiple:
            return a
        one = MULTIPLE_TO_ONE.get(a.name)
        child = self.one_line(a.children[0]) if one in self.td.actions and len(a.children) == 1 else None
        if child is None:
            return None
        inner = wtg.Function(child.kind, child.name, child.enabled, child.params, None, child.children)
        return wtg.Function(a.kind, one, a.enabled, list(a.params) + [wtg.Parameter(FUNCTION, 'DoNothing',
                                                                                    function=inner)])

    def var_type(self, name):
        t = self.types.get(name)
        if t is None and name.startswith('udg_'):
            t = self.types.get(name[4:])
        if t is None:
            for prefix, gui_type in OBJECT_TYPES:
                if name.startswith(prefix):
                    return gui_type
        return t

    def fits(self, actual, expected):
        if actual == CUSTOM_GLOBAL:
            return False
        if actual is None or expected is None or expected in ('AnyGlobal', 'Null', 'AnyType'):
            return True
        a, x = self.k.base(actual), self.k.base(expected)
        if a == x or actual == expected:
            return True
        return x in self.k.supertypes(a)

    def type_of(self, e):
        e = _bare(e)
        t = type(e)
        if t is lua_ast.Name:
            n = e.name
            if n.startswith(('udg_', 'gg_')) or n in self.types:
                return self.var_type(n)
            types = self.k.preset_types.get(n)
            if types and len(set(types)) == 1:
                return types[0]
            return self.k.global_types.get(n)
        if t is lua_ast.Index:
            return self.type_of(e.base)
        if t is lua_ast.Literal:
            if e.kind == 'number':
                return _number_kind(e.text)
            return {'string': 'string', 'boolean': 'boolean'}.get(e.kind)
        if t is lua_ast.Unary:
            return 'boolean' if e.op == 'not' else self.type_of(e.operand)
        if t is lua_ast.Call:
            name = _callee(e)
            if name is None or name == 'FourCC':
                return None
            for c in self.k.calls('call', name):
                if len(c.arg_types) == len(e.args):
                    return c.return_type
            return self.k.returns.get(name)
        if t is lua_ast.Binary:
            if e.op in ARITHMETIC:
                return self.type_of(e.left) or self.type_of(e.right)
            return 'string' if e.op == '..' else 'boolean'
        return None

    def param(self, e, t):
        e = _bare(e)
        if t == 'code':
            return self.code_param(e)
        if t == 'boolexpr':
            return self.boolexpr_param(e)
        if t == 'boolcall':
            return self.boolcall_param(e)
        if t == 'VarAsString_Real':
            return self.var_as_string(e)
        if t in ('eventcall', 'scriptcode'):
            return None
        cls = type(e)
        if cls is lua_ast.Name:
            return self.name_param(e, t)
        if cls is lua_ast.Literal:
            return self.literal_param(e, t)
        if cls is lua_ast.Call:
            if _callee(e) == 'FourCC':
                return self.rawcode_param(e, t)
            return self.call_param(e, t)
        if cls is lua_ast.Index:
            return self.index_param(e, t)
        if cls is lua_ast.Binary and (e.op in ARITHMETIC or e.op == '..'):
            return self.arithmetic_param(e, t)
        if cls is lua_ast.Unary and e.op == '-':
            inner = e.operand
            if type(inner) is lua_ast.Literal and inner.kind == 'number':
                return self.number_param(e, '-' + inner.text, t)
        return None

    def number_param(self, e, text, t):
        p = self.preset_param(e, t)
        if p is not None:
            return p
        base = self.k.base(t)
        kind = _number_kind(text)
        if kind is None or (t is not None and base not in ('integer', 'real')):
            return None
        if kind == 'real' and base == 'integer':
            return None
        return wtg.Parameter(LITERAL, text)

    def preset_param(self, e, t):
        if t in LITERAL_TYPES:
            return None
        name = self.k.preset(_jass_code(e), t)
        if name is None and t is not None and self.k.base(t) == 'string' and _is_literal(e, '""'):
            name = self.k.preset('null', t)
        return None if name is None else wtg.Parameter(PRESET, name)

    def variable_name(self, n):
        if n.startswith('udg_') and len(n) > 4:
            return n[4:]
        return n if n.startswith('gg_') else None

    def name_param(self, e, t):
        n = e.name
        v = self.variable_name(n)
        if v is None:
            return self.preset_param(e, t)
        vt = self.var_type(n)
        if n.startswith('gg_snd_') and n not in self.types and t is not None and self.k.base(t) == 'string':
            vt = t
        return wtg.Parameter(VARIABLE, v) if self.fits(vt, t) else None

    def index_param(self, e, t):
        p = self.preset_param(e, t)
        if p is not None:
            return p
        base = _bare(e.base)
        v = self.variable_name(base.name) if type(base) is lua_ast.Name and not e.dot else None
        if v is None or not self.fits(self.var_type(base.name), t):
            return None
        m = self.mark()
        index = self.param(e.key, 'integer')
        if index is None:
            self.reset(m)
            return None
        return wtg.Parameter(VARIABLE, v, index=index)

    def literal_param(self, e, t):
        if e.kind == 'number':
            return self.number_param(e, e.text, t)
        p = self.preset_param(e, t)
        if p is not None:
            return p
        base = self.k.base(t)
        if e.kind == 'string':
            if t is not None and base != 'string':
                return None
            value = _editor_unescape(e.text)
            return None if value is None else wtg.Parameter(LITERAL, value)
        if e.kind == 'boolean':
            if t is not None and base != 'boolean':
                return None
            return wtg.Parameter(LITERAL, e.text)
        return None

    def rawcode_param(self, e, t):
        p = self.preset_param(e, t)
        if p is not None:
            return p
        code = _fourcc(e.args[0]) if len(e.args) == 1 else None
        if code is None or RX_INTEGER.match(code):
            return None
        if t is not None and (self.k.base(t) != 'integer' or t in ('integer', 'integervar')):
            return None
        return wtg.Parameter(LITERAL, code)

    def call_param(self, e, t):
        p = self.preset_param(e, t)
        if p is not None:
            return p
        f = self.call_function(e, t)
        return None if f is None else wtg.Parameter(FUNCTION, f.name, function=f)

    def call_function(self, e, t):
        name = _callee(e)
        if name is None:
            return None
        cands = [c for c in self.k.calls('call', name) if len(c.arg_types) == len(e.args) and
                 c.name not in ('OperatorInt', 'OperatorReal', 'OperatorString') and
                 (t is None or self.fits(c.return_type, t))]
        if t is not None and len(cands) > 1:
            cands.sort(key=lambda c: c.return_type != t)
        for c in cands:
            params = self.params(e.args, c.arg_types)
            if params is not None:
                return wtg.Function(CALL, c.name, 1, params)
        return None

    def params(self, args, types):
        m = self.mark()
        out = []
        for a, t in zip(args, types):
            p = self.param(a, t)
            if p is None:
                self.reset(m)
                return None
            out.append(p)
        return out

    def arithmetic_param(self, e, t):
        if e.op == '..':
            if t is not None and self.k.base(t) != 'string':
                return None
            name, op = 'OperatorString', None
        else:
            base = self.k.base(t) if t is not None else None
            if base not in ('integer', 'real'):
                guess = self.type_of(e)
                base = self.k.base(guess) if guess else ('integer' if e.op == '//' else 'real' if e.op == '/' else None)
                if t is not None and not self.fits(base, t):
                    return None
            if base == 'integer' and e.op != '/':
                name = 'OperatorInt'
            elif base == 'real' and e.op != '//':
                name = 'OperatorReal'
            else:
                return None
            op = self.k.preset('/' if e.op == '//' else e.op, 'ArithmeticOperator')
            if op is None:
                return None
        f = self.td.calls.get(name)
        if f is None:
            return None
        params = self.params((e.left, e.right), [f.arg_types[0], f.arg_types[-1]])
        if params is None:
            return None
        if op is not None:
            params.insert(1, wtg.Parameter(PRESET, op))
        return wtg.Parameter(FUNCTION, name, function=wtg.Function(CALL, name, 1, params))

    def var_as_string(self, e):
        if type(e) is lua_ast.Literal and e.kind == 'string':
            body = _editor_unescape(e.text)
            if body is not None and re.match(r'^udg_\w+$', body):
                return wtg.Parameter(VARIABLE, body[4:])
        return None

    def code_param(self, e):
        if type(e) is not lua_ast.Name:
            return None
        m = self.mark()
        f = self.helper(e.name)
        if f is None:
            return None
        acts = self.actions(f.body)
        single = self.one_line(acts[0]) if len(acts) == 1 else None
        if single is None:
            self.reset(m)
            return None
        return wtg.Parameter(FUNCTION, 'DoNothing', function=single)

    def condition_helper(self, name):
        m = self.mark()
        f = self.helper(name)
        if f is None:
            return None
        body = f.body
        if len(body) != 1 or type(body[0]) is not lua_ast.ReturnStmt or len(body[0].values) != 1:
            self.reset(m)
            return None
        cond = self.condition(body[0].values[0])
        if cond is None:
            self.reset(m)
        return cond

    def boolexpr_param(self, e):
        if _callee(e) == 'Condition' and len(e.args) == 1 and type(_bare(e.args[0])) is lua_ast.Name:
            cond = self.condition_helper(_bare(e.args[0]).name)
            if cond is not None:
                return wtg.Parameter(FUNCTION, '', function=cond)
        return None

    def boolcall_param(self, e):
        name = _callee(e)
        if name is not None and not e.args:
            cond = self.condition_helper(name)
            if cond is not None:
                return wtg.Parameter(FUNCTION, '', function=cond)
        return None

    def condition(self, e):
        e = _bare(e)
        cls = type(e)
        if cls is lua_ast.Binary and e.op in COMPARISONS:
            return self.comparison(e)
        name = _callee(e) if cls is lua_ast.Call else None
        if name is None:
            return None
        if not e.args:
            multiple = self.multiple_condition(name)
            if multiple is not None:
                return multiple
        for c in self.k.calls('condition', name):
            if len(c.arg_types) == len(e.args) and c.name not in self.td.multiple:
                params = self.params(e.args, c.arg_types)
                if params is not None:
                    return wtg.Function(CONDITION, c.name, 1, params)
        return None

    def compare_order(self, e):
        firm, loose = [], []
        for x in (e.left, e.right):
            t = self.type_of(x)
            if t:
                (loose if type(_bare(x)) is lua_ast.Literal else firm).append(t)
        bases = set(self.k.base(t) for t in firm + loose)

        def score(f):
            t = f.arg_types[0]
            if t in firm:
                return firm.index(t)
            if t in loose:
                return 2
            if self.k.base(t) in bases:
                return 3 if t in bases else 4
            return 5
        return sorted(self.k.compares, key=score)

    def comparison(self, e):
        op_code = COMPARISONS[e.op]
        for f in self.compare_order(e):
            op_type = f.arg_types[1]
            if op_code not in self.k.operators.get(op_type, ()):
                continue
            op = self.k.preset(op_code, op_type)
            m = self.mark()
            a = self.param(e.left, f.arg_types[0])
            if a is None:
                continue
            b = self.param(e.right, f.arg_types[2])
            if b is None:
                self.reset(m)
                continue
            return wtg.Function(CONDITION, f.name, 1, [a, wtg.Parameter(PRESET, op), b])
        return None

    def multiple_condition(self, name):
        m = self.mark()
        f = self.helper(name)
        if f is None:
            return None
        for kind, fail, ok in (('AndMultiple', 'false', 'true'), ('OrMultiple', 'true', 'false')):
            if kind not in self.td.conditions:
                continue
            tests = _tests(f.body, fail, ok, negated=kind == 'AndMultiple')
            if tests is None:
                continue
            m2 = self.mark()
            children = []
            for x in tests:
                c = self.condition(x)
                if c is None:
                    break
                c.branch = 0
                children.append(c)
            else:
                return wtg.Function(CONDITION, kind, 1, [], None, children)
            self.reset(m2)
        self.reset(m)
        return None

    def custom_line(self, text, node=None):
        self.custom += 1
        if node is not None:
            self.loose.extend(_references_in(node, self.functions))
        return wtg.Function(ACTION, 'CustomScriptCode', 1, [wtg.Parameter(LITERAL, text)])

    def comments(self, comments):
        out = []
        for c in comments:
            for line in c.value.replace('\r\n', '\n').replace('\r', '\n').split('\n'):
                line = line[1:] if line[:1] == ' ' else line
                out.append(wtg.Function(ACTION, 'CommentString', 1, [wtg.Parameter(LITERAL, line.rstrip())]))
        return out

    def custom_stmt(self, s):
        c = copy.copy(s)
        c.leading_comments = c.inner_comments = ()
        text = lua_ast.unparse(c)
        if self.source is not None and s.span:
            written = self.source[s.span[0]:s.span[1]]
            if written != text and _same_code(written, text):
                text = written
        text = text.rstrip()
        multiline = any(type(n) is lua_ast.Literal and n.kind == 'string' and ('\n' in n.text or '\r' in n.text)
                        for n in walk(s))
        out = [self.custom_line(text)] if multiline else [
            self.custom_line(line.strip()) for line in RX_LINE_BREAK.split(text) if line.strip()]
        self.loose.extend(_references_in(s, self.functions))
        return out

    def custom_block(self, s):
        t = type(s)
        out = []
        if t is lua_ast.IfStmt:
            for k, (cond, body) in enumerate(s.branches):
                head = 'else' if cond is None else '%s %s then' % ('elseif' if k else 'if', _text(cond))
                out.append(self.custom_line(head, cond))
                out.extend(self.actions(body))
            tail = 'end'
        elif t is lua_ast.WhileStmt:
            out.append(self.custom_line('while %s do' % _text(s.cond), s.cond))
            out.extend(self.actions(s.body))
            tail = 'end'
        elif t is lua_ast.NumericForStmt:
            head = 'for %s = %s, %s' % (s.var, _text(s.start), _text(s.stop))
            head += ', %s do' % _text(s.step) if s.step is not None else ' do'
            for e in (s.start, s.stop, s.step):
                if e is not None:
                    self.loose.extend(_references_in(e, self.functions))
            out.append(self.custom_line(head))
            out.extend(self.actions(s.body))
            tail = 'end'
        elif t is lua_ast.GenericForStmt:
            head = 'for %s in %s do' % (', '.join(s.names), ', '.join(_text(x) for x in s.exprs))
            for e in s.exprs:
                self.loose.extend(_references_in(e, self.functions))
            out.append(self.custom_line(head))
            out.extend(self.actions(s.body))
            tail = 'end'
        elif t is lua_ast.DoStmt:
            out.append(self.custom_line('do'))
            out.extend(self.actions(s.body))
            tail = 'end'
        else:
            out.append(self.custom_line('repeat'))
            out.extend(self.actions(s.body))
            out.append(self.custom_line('until %s' % _text(s.cond), s.cond))
            return out
        out.append(self.custom_line(tail))
        return out

    def actions(self, stmts):
        out = []
        i = 0
        while i < len(stmts):
            s = stmts[i]
            out.extend(self.comments(s.leading_comments))
            used, acts = self.statement(stmts, i)
            out.extend(acts)
            i += used
        out.extend(self.comments(getattr(stmts, 'end_comments', ()) or ()))
        return out

    def statement(self, stmts, i):
        s = stmts[i]
        t = type(s)
        a = None
        if t is lua_ast.AssignStmt:
            loop = self.for_loop(stmts, i)
            if loop is not None:
                return loop
            a = self.set_variable(s)
        elif t is lua_ast.CallStmt:
            a = self.call_action(s.call)
        elif t is lua_ast.IfStmt:
            a = self.if_action(s)
            if a is None:
                return 1, self.custom_block(s)
        elif t is lua_ast.WhileStmt:
            a = self.wait_for_condition(s)
            if a is None:
                return 1, self.custom_block(s)
        elif t in (lua_ast.NumericForStmt, lua_ast.GenericForStmt, lua_ast.DoStmt, lua_ast.RepeatStmt):
            return 1, self.custom_block(s)
        elif t is lua_ast.ReturnStmt and not s.values and 'ReturnAction' in self.td.actions:
            a = wtg.Function(ACTION, 'ReturnAction', 1, [])
        if a is None:
            return 1, self.custom_stmt(s)
        return 1, [a]

    def set_variable(self, s):
        if 'SetVariable' not in self.td.actions or len(s.targets) != 1 or len(s.values) != 1:
            return None
        target = s.targets[0]
        base = target.base if type(target) is lua_ast.Index and not target.dot else target
        name = base.name if type(base) is lua_ast.Name else None
        if name is None or not name.startswith('udg_'):
            return None
        m = self.mark()
        var = self.param(target, None)
        if var is None:
            return None
        value = self.param(s.values[0], self.var_type(name))
        if value is None:
            self.reset(m)
            return None
        return wtg.Function(ACTION, 'SetVariable', 1, [var, value])

    def callback_order(self, cands, ref):
        hint = self.hint(ref)
        one = [c for c in cands if c.name in CALLBACK_FORMS]
        multi = [c for c in cands if c.name in CALLBACK_FORMS.values()]
        rest = [c for c in cands if c not in one and c not in multi]
        if hint == 'A':
            first = multi + one
        elif hint == 'digits':
            first = one + multi
        else:
            default = ONE_LINE_DEFAULT.get(one[0].name if one else '', False)
            first = one + multi if default else multi + one
        return first + rest

    def call_action(self, call):
        name = _callee(call)
        if name is None or name in CUSTOM_SCRIPT_IDIOMS:
            return None
        cands = list(self.k.calls('action', name))
        ref = _name(call.args[-1]) if call.args else None
        if ref is not None and ref in self.functions and any(c.name in CALLBACK_FORMS for c in cands):
            cands = self.callback_order(cands, ref)
        for c in cands:
            if c.name in self.td.multiple:
                if c.name not in CALLBACK_FORMS.values() or ref not in self.functions:
                    continue
                if len(call.args) != len(c.arg_types) + 1:
                    continue
                m = self.mark()
                params = self.params(call.args[:-1], c.arg_types)
                if params is None:
                    continue
                f = self.helper(ref)
                if f is None:
                    self.reset(m)
                    continue
                children = self.actions(f.body)
                for x in children:
                    x.branch = 0
                return wtg.Function(ACTION, c.name, 1, params, None, children)
            if len(call.args) == len(c.arg_types):
                params = self.params(call.args, c.arg_types)
                if params is not None:
                    return wtg.Function(ACTION, c.name, 1, params)
        if 'AddTriggerEvent' in self.td.actions and call.args:
            for c in self.k.calls('event', name):
                if len(c.arg_types) + 1 != len(call.args):
                    continue
                m = self.mark()
                trig = self.param(call.args[0], 'trigger')
                params = self.params(call.args[1:], c.arg_types) if trig is not None else None
                if params is None:
                    self.reset(m)
                    continue
                event = wtg.Function(EVENT, c.name, 1, params)
                return wtg.Function(ACTION, 'AddTriggerEvent', 1, [trig, wtg.Parameter(FUNCTION, '', function=event)])
        return None

    def for_loop(self, stmts, i):
        s = stmts[i]
        if len(s.targets) != 1 or len(s.values) != 1:
            return None
        target = s.targets[0]
        tname = _name(target)
        if tname in ('bj_forLoopAIndex', 'bj_forLoopBIndex'):
            letter = tname[10]
            if i + 2 >= len(stmts) or type(stmts[i + 1]) is not lua_ast.AssignStmt:
                return None
            s1, loop = stmts[i + 1], stmts[i + 2]
            if (len(s1.targets) != 1 or len(s1.values) != 1 or _name(s1.targets[0]) != tname + 'End' or
                    type(loop) is not lua_ast.WhileStmt or s1.leading_comments or loop.leading_comments):
                return None
            index_code, used = tname, 3
            starts = [(s.values[0], 'integer'), (s1.values[0], 'integer')]
        else:
            base = target.base if type(target) is lua_ast.Index and not target.dot else target
            if _name(base) is None or not _name(base).startswith('udg_'):
                return None
            letter = 'Var'
            if i + 1 >= len(stmts) or type(stmts[i + 1]) is not lua_ast.WhileStmt or stmts[i + 1].leading_comments:
                return None
            loop, index_code, used = stmts[i + 1], _jass_code(target), 2
            starts = [(target, 'integervar'), (s.values[0], 'integer')]
        body = loop.body
        if not _is_literal(loop.cond, 'true') or len(body) < 2 or getattr(body, 'end_comments', ()):
            return None
        test = body[0]
        if (type(test) is not lua_ast.IfStmt or len(test.branches) != 1 or len(test.branches[0][1]) != 1 or
                type(test.branches[0][1][0]) is not lua_ast.BreakStmt):
            return None
        cond = _bare(test.branches[0][0])
        if type(cond) is not lua_ast.Binary or cond.op != '>' or _jass_code(cond.left) != index_code:
            return None
        if letter != 'Var' and _name(cond.right) != index_code + 'End':
            return None
        step = body[-1]
        inc = _bare(step.values[0]) if type(step) is lua_ast.AssignStmt and len(step.values) == 1 else None
        if (inc is None or len(step.targets) != 1 or _jass_code(step.targets[0]) != index_code or
                type(inc) is not lua_ast.Binary or inc.op != '+' or _jass_code(inc.left) != index_code or
                not _is_literal(inc.right, '1') or step.leading_comments):
            return None
        if letter == 'Var':
            starts.append((cond.right, 'integer'))
        one, multiple = LOOP_FORMS[letter]
        if multiple not in self.td.actions:
            return None
        params = self.params([e for e, _t in starts], [t for _e, t in starts])
        if params is None:
            return None
        acts = self.actions(body[1:-1])
        if (len(acts) == 1 and acts[0].name not in self.td.multiple and ONE_LINE_DEFAULT.get(one) and
                one in self.td.actions):
            params.append(wtg.Parameter(FUNCTION, 'DoNothing', function=acts[0]))
            return used, [wtg.Function(ACTION, one, 1, params)]
        for a in acts:
            a.branch = 0
        return used, [wtg.Function(ACTION, multiple, 1, params, None, acts)]

    def wait_for_condition(self, s):
        body = s.body
        if (not _is_literal(s.cond, 'true') or len(body) != 2 or type(body[0]) is not lua_ast.IfStmt or
                type(body[1]) is not lua_ast.CallStmt or 'WaitForCondition' not in self.td.actions):
            return None
        test = body[0]
        if (len(test.branches) != 1 or len(test.branches[0][1]) != 1 or
                type(test.branches[0][1][0]) is not lua_ast.BreakStmt):
            return None
        sleep = body[1].call
        if _callee(sleep) != 'TriggerSleepAction' or len(sleep.args) != 1:
            return None
        wait = _bare(sleep.args[0])
        if (_callee(wait) != 'RMaxBJ' or len(wait.args) != 2 or
                _name(wait.args[0]) != 'bj_WAIT_FOR_COND_MIN_INTERVAL'):
            return None
        m = self.mark()
        cond = self.boolcall_param(_bare(test.branches[0][0]))
        if cond is None:
            return None
        interval = self.param(wait.args[1], self.td.actions['WaitForCondition'].arg_types[1])
        if interval is None:
            self.reset(m)
            return None
        return wtg.Function(ACTION, 'WaitForCondition', 1, [cond, interval])

    def if_action(self, s):
        if len(s.branches) != 2 or s.branches[1][0] is not None:
            return None
        cond = _bare(s.branches[0][0])
        name = _callee(cond)
        if name is None or cond.args:
            return None
        m = self.mark()
        f = self.helper(name)
        if f is None:
            return None
        tests = _tests(f.body, 'false', 'true', negated=True)
        if tests is not None and 'IfThenElseMultiple' in self.td.actions:
            children = []
            for x in tests:
                c = self.condition(x)
                if c is None:
                    self.reset(m)
                    return None
                c.branch = 0
                children.append(c)
            for branch, (_c, body) in ((1, s.branches[0]), (2, s.branches[1])):
                for a in self.actions(body):
                    a.branch = branch
                    children.append(a)
            return wtg.Function(ACTION, 'IfThenElseMultiple', 1, [], None, children)
        body = f.body
        if (len(body) == 1 and type(body[0]) is lua_ast.ReturnStmt and len(body[0].values) == 1 and
                'IfThenElse' in self.td.actions):
            c = self.condition(body[0].values[0])
            if c is not None:
                sides = [[self.one_line(a) for a in self.actions(b)] for _c, b in s.branches]
                if all(len(x) <= 1 and None not in x for x in sides):
                    params = [wtg.Parameter(FUNCTION, 'DoNothing', function=x[0] if x else wtg.Function(
                        ACTION, 'CommentString', 1, [wtg.Parameter(LITERAL, '')])) for x in sides]
                    return wtg.Function(ACTION, 'IfThenElse', 1, [wtg.Parameter(FUNCTION, '', function=c)] + params)
        self.reset(m)
        return None

    def event(self, call):
        for c in self.k.calls('event', _callee(call)):
            if len(c.arg_types) + 1 == len(call.args):
                params = self.params(call.args[1:], c.arg_types)
                if params is not None:
                    return wtg.Function(EVENT, c.name, 1, params)
        return None


def _tests(body, fail, ok, negated):
    if not body or getattr(body, 'end_comments', ()):
        return None
    last = body[-1]
    if type(last) is not lua_ast.ReturnStmt or len(last.values) != 1 or not _is_literal(last.values[0], ok):
        return None
    out = []
    for s in body[:-1]:
        if type(s) is not lua_ast.IfStmt or len(s.branches) != 1:
            return None
        cond, then = s.branches[0]
        if (len(then) != 1 or type(then[0]) is not lua_ast.ReturnStmt or len(then[0].values) != 1 or
                not _is_literal(then[0].values[0], fail)):
            return None
        cond = _bare(cond)
        if negated:
            if type(cond) is not lua_ast.Unary or cond.op != 'not':
                return None
            cond = cond.operand
        out.append(cond)
    return out


def _first_line(s):
    return lua_ast.unparse(s).split('\n')[0].strip()[:120]


def _init_statements(init):
    if init.params or init.is_vararg:
        raise _Fail('no InitTrig shape: parameters')
    body = init.body
    if not body or type(body[0]) is not lua_ast.AssignStmt or len(body[0].targets) != 1:
        raise _Fail('no InitTrig shape: no <trigger> = CreateTrigger()')
    first = body[0]
    trig = _name(first.targets[0]) if type(first.targets[0]) is lua_ast.Name else None
    value = _bare(first.values[0]) if len(first.values) == 1 else None
    if trig is None or _callee(value) != 'CreateTrigger' or value.args:
        raise _Fail('no InitTrig shape: no <trigger> = CreateTrigger()')
    i, off, events, cond, act = 1, False, [], None, None

    def call(k, name=None):
        s = body[k] if k < len(body) else None
        if type(s) is not lua_ast.CallStmt or _callee(s.call) is None or not s.call.args:
            return None
        if type(s.call.args[0]) is not lua_ast.Name or s.call.args[0].name != trig:
            return None
        return s.call if name is None or _callee(s.call) == name else None

    if call(i, 'DisableTrigger') and len(body[i].call.args) == 1:
        off, i = True, i + 1
    while call(i) and _callee(body[i].call) not in REGISTRATION:
        events.append(body[i].call)
        i += 1
    c = call(i, 'TriggerAddCondition')
    if c:
        arg = _bare(c.args[1]) if len(c.args) == 2 else None
        if _callee(arg) != 'Condition' or len(arg.args) != 1 or type(arg.args[0]) is not lua_ast.Name:
            raise _Fail('conditions not a Condition(F)')
        cond, i = arg.args[0].name, i + 1
    c = call(i, 'TriggerAddAction')
    if c and (len(c.args) != 2 or type(c.args[1]) is not lua_ast.Name):
        raise _Fail('actions not a function name: %s' % _first_line(body[i]))
    if not c:
        raise _Fail('InitTrig does more than register: %s' % _first_line(body[i]) if i < len(body) else
                    'no TriggerAddAction')
    act, i = c.args[1].name, i + 1
    if i < len(body):
        raise _Fail('InitTrig does more than register: %s' % _first_line(body[i]))
    return trig, off, events, cond, act


def initialization_event(td=None):
    return wtg.Function(EVENT, 'MapInitializationEvent', 1, [])


def match_trigger(functions, init_name, td, globals_types=None, name=None, source=None):
    init = functions.get(init_name)
    if init is None or type(init) is not lua_ast.FunctionStmt:
        return Match(None, 'no function %s' % init_name)
    try:
        trig, off, event_calls, cond_name, act_name = _init_statements(init)
        prefix = act_name[:-7] if act_name.endswith('_Actions') else None
        m = _Matcher(functions, td, globals_types, prefix, source)
        events = []
        for call in event_calls:
            e = m.event(call)
            if e is None:
                raise _Fail('event %s: no GUI event matches' % _text(call)[:120])
            events.append(e)
        conditions = []
        if cond_name is not None:
            f = m.helper(cond_name)
            tests = _tests(f.body, 'false', 'true', negated=True) if f is not None else None
            if tests is None:
                raise _Fail('conditions not a Trig_Conditions: %s' % cond_name)
            for x in tests:
                c = m.condition(x)
                if c is None:
                    raise _Fail('condition not GUI: %s' % _text(x)[:120])
                conditions.append(c)
        f = m.helper(act_name)
        if f is None:
            raise _Fail('actions not a Trig_Actions: %s' % act_name)
        actions = m.actions(f.body)
    except _Fail as e:
        return Match(None, str(e), [init_name])
    except RecursionError:
        return Match(None, 'nested too deep', [init_name])
    except Exception as e:
        return Match(None, 'matcher error: %s: %s' % (type(e).__name__, e), [init_name])
    helpers = [init_name] + m.used
    covered = set(helpers)
    external, stack = [], list(reversed(m.loose))
    while stack:
        n = stack.pop()
        if n in covered or n in external or n not in functions:
            continue
        external.append(n)
        stack.extend(reversed(_references_in(functions[n].body, functions)))
    if name is None:
        name = init_name[9:] if init_name.startswith('InitTrig_') else init_name
    t = wtg.Trigger(name, '', 0, 1, 0, 1 if off else 0, 0, 0, events + conditions + actions)
    return Match(t, '', helpers, external, m.custom)


def _declarations(chunk):
    out = collections.OrderedDict()
    for s in chunk.body:
        if type(s) is not lua_ast.AssignStmt:
            continue
        for target, value in zip(s.targets, s.values):
            n = target.name if type(target) is lua_ast.Name else None
            if n and n.startswith('udg_') and len(n) > 4 and n not in out:
                out[n] = value
    return out


def _declared_kind(value):
    e = _bare(value)
    t = type(e)
    if t is lua_ast.Literal:
        if e.kind == 'number':
            return _number_kind(e.text), False
        return {'nil': None, 'boolean': 'boolean', 'string': 'string'}.get(e.kind), False
    if t is lua_ast.Table and not e.fields:
        return None, True
    if _callee(e) == '__jarray' and len(e.args) == 1:
        return JARRAY.get(_text(_bare(e.args[0]))), True
    return None, False


def _integer(text):
    try:
        return int(text, 16) if text[:2] in ('0x', '0X') else int(text)
    except ValueError:
        return None


def _init_values(chunk):
    f = next((s for s in reversed(chunk.body) if type(s) is lua_ast.FunctionStmt and s.name == 'InitGlobals'), None)
    values, sizes = {}, {}
    for s in (f.body if f is not None else ()):
        if type(s) is lua_ast.AssignStmt and len(s.targets) == 1 and len(s.values) == 1:
            n = s.targets[0].name if type(s.targets[0]) is lua_ast.Name else None
            if n and n.startswith('udg_'):
                values.setdefault(n, s.values[0])
        elif type(s) is lua_ast.WhileStmt and len(s.body) == 3:
            test, st, inc = s.body
            cond = _bare(test.branches[0][0]) if type(test) is lua_ast.IfStmt and len(test.branches) == 1 else None
            target = st.targets[0] if type(st) is lua_ast.AssignStmt and len(st.targets) == 1 else None
            size = _bare(cond.right) if type(cond) is lua_ast.Binary and cond.op == '>' else None
            n = _name(target.base) if type(target) is lua_ast.Index and not target.dot else None
            if (type(size) is lua_ast.Literal and size.kind == 'number' and _integer(size.text) is not None and
                    n and n.startswith('udg_') and type(inc) is lua_ast.AssignStmt):
                sizes.setdefault(n, _integer(size.text))
                values.setdefault(n, st.values[0])
    return values, sizes, f is not None


def _variable_of(e):
    e = _bare(e)
    if type(e) is lua_ast.Index and not e.dot:
        e = _bare(e.base)
    return e.name if type(e) is lua_ast.Name and e.name.startswith('udg_') else None


def _evidence(functions, td, k):
    evidence = collections.defaultdict(collections.Counter)
    links = []

    def returned(e):
        e = _bare(e)
        name = _callee(e) if type(e) is lua_ast.Call else None
        if name == 'FourCC':
            return '<rawcode>'
        if name is not None:
            for c in k.calls('call', name):
                if len(c.arg_types) == len(e.args):
                    return c.return_type
            if name in k.returns:
                return k.returns[name]
        if type(e) is lua_ast.Literal:
            return '<null>' if e.kind == 'nil' else None
        if type(e) is lua_ast.Name:
            for prefix, gui_type in OBJECT_TYPES:
                if e.name.startswith(prefix) and prefix != 'gg_snd_':
                    return gui_type
        code = _jass_code(e)
        types = set(t for t in k.preset_types.get(code, ()) if t in td.types and td.types[t].can_be_global)
        return types.pop() if len(types) == 1 else None

    def link(a, b):
        v, w = _variable_of(a), _variable_of(b)
        if v and w and v != w:
            links.append((v, w))

    for f in functions.values():
        for node in walk(f.body):
            t = type(node)
            if t is lua_ast.Call and type(node.func) is lua_ast.Name:
                for kind, skip in (('action', 0), ('call', 0), ('event', 1), ('condition', 0)):
                    for c in k.calls(kind, node.func.name):
                        n = len(c.arg_types) + skip
                        if n != len(node.args) and not (c.name in CALLBACK_FORMS.values() and n + 1 == len(node.args)):
                            continue
                        for a, at in zip(node.args[skip:], c.arg_types):
                            v = _variable_of(a)
                            if v:
                                evidence[v][at] += 1
            elif t is lua_ast.AssignStmt and len(node.targets) == 1 and len(node.values) == 1:
                v = _variable_of(node.targets[0])
                r = returned(node.values[0]) if v else None
                if r:
                    evidence[v][r] += 1
                link(node.targets[0], node.values[0])
            elif t is lua_ast.Binary and node.op in COMPARISONS:
                for a, b in ((node.left, node.right), (node.right, node.left)):
                    v = _variable_of(a)
                    r = returned(b) if v else None
                    if r:
                        evidence[v][r] += 1
                link(node.left, node.right)
    return evidence, links


def _pick(td, k, counts, base):
    cands = collections.Counter()
    for t, n in counts.items():
        tt = td.types.get(t)
        if tt is None or not tt.can_be_global or t == 'handle':
            continue
        b = td.base_type(t)
        if (base is None and b in ('integer', 'real', 'boolean', 'string', 'code')) or (base is not None and b != base):
            continue
        cands[t] += n
    if not cands:
        return None
    return max(cands, key=lambda t: (cands[t], len(k.supertypes(t))))


def _lua_default(td, t):
    d = td.type_defaults.get(t)
    if d is None:
        return '""' if td.base_type(t) == 'string' else None
    return '0.0' if td.base_type(t) == 'real' and d == '0' else d


def _variable_type(td, k, value, init, ev, has_init):
    base = _declared_kind(value)[0]
    init_code = _jass_code(init) if init is not None else None
    if base in ('boolean', 'real'):
        return base, 'declaration'
    if base == 'integer':
        custom = _pick(td, k, dict((t, n) for t, n in ev.items() if t not in ('integer', 'integervar')), 'integer')
        if custom:
            return custom, 'uses'
        if ev.get('<rawcode>') or (has_init and init is None) or (init_code or '').startswith("'"):
            return RAWCODE_VARIABLE_TYPE, 'default'
        return 'integer', 'declaration'
    if base == 'string':
        custom = _pick(td, k, dict((t, n) for t, n in ev.items() if t != 'string'), 'string')
        return (custom, 'uses') if custom else ('string', 'declaration')
    defaults = dict((code, t) for t, code in td.type_defaults.items() if code.endswith(')'))
    if init_code in defaults:
        return defaults[init_code], 'InitGlobals'
    if init_code:
        types = set(t for t in k.preset_types.get(init_code, ()) if t in td.types and td.types[t].can_be_global)
        if len(types) == 1:
            return types.pop(), 'InitGlobals'
    t = _pick(td, k, ev, None)
    if t:
        return t, 'uses'
    return ('unit', 'default') if ev.get('<null>') else ('handle', 'undecided')


def _script_kind(td, t):
    base = td.base_type(t)
    return base if base in ('integer', 'real', 'boolean', 'string') else None


def _propagate(td, decls, types, sources, links):
    firm = ('declaration', 'InitGlobals', 'uses', 'linked')
    for _pass in range(8):
        changed = False
        for a, b in links + [(b, a) for a, b in links]:
            if a in decls and b in decls and sources[a] not in firm and sources[b] in firm and types[a] != types[b]:
                if _declared_kind(decls[a])[0] == _script_kind(td, types[b]):
                    types[a], sources[a], changed = types[b], 'linked', True
        if not changed:
            break


def _derive_globals(chunk, td):
    functions = script_functions(chunk)
    k = _knowledge(td)
    evidence, links = _evidence(functions, td, k)
    values, sizes, has_init = _init_values(chunk)
    decls = _declarations(chunk)
    types, sources = {}, {}
    for n, value in decls.items():
        types[n], sources[n] = _variable_type(td, k, value, values.get(n), evidence.get(n, {}), has_init)
    _propagate(td, decls, types, sources, links)
    m = _Matcher(functions, td, types)
    out = []
    for n, value in decls.items():
        t = types[n]
        is_array = _declared_kind(value)[1]
        v = wtg.Variable(n[4:], t, 1 if is_array else 0, sizes.get(n, 1) if is_array else 1)
        e = values.get(n)
        if e is not None and _jass_code(e) != _lua_default(td, t):
            p = m.param(e, t)
            if p is not None and p.kind in (PRESET, LITERAL):
                v.initialized, v.initial_value = 1, p.value
        out.append(v)
    return out, types, sources


def match_globals(chunk, td):
    variables, types, _sources = _derive_globals(chunk, td)
    return variables, types


def _escape(s):
    return s.replace('\\', '\\\\').replace('"', '\\"')


def _param_text(p, t, td):
    base = td.base_type(t) if t else None
    if p.kind == PRESET:
        preset = td.presets.get(p.value)
        code = preset.code if preset is not None else p.value
        return '""' if code == 'null' and base == 'string' else code
    if p.kind == LITERAL:
        if base == 'string':
            return '"%s"' % _escape(p.value)
        if base == 'integer' and t not in ('integer', 'integervar') and not RX_INTEGER.match(p.value):
            return "'%s'" % p.value
        return p.value
    if p.kind == VARIABLE:
        return p.value if p.value.startswith('gg_') else 'udg_' + p.value
    return '<unset>'


def _visible(fs):
    return [f for f in fs if f is not None and f.enabled and f.name != 'CommentString']


def _norm_function(f, td, var_types):
    fd = td.get(f.kind, f.name)
    types = list(fd.arg_types) if fd is not None else []
    name, params, children = f.name, list(f.params), _visible(f.children) if f.name in td.multiple else []
    if name in CALLBACK_FORMS or name in ('ForLoopA', 'ForLoopB', 'ForLoopVar'):
        act = params[-1].function if params and params[-1].kind == FUNCTION else None
        params, types, children = params[:-1], types[:-1], _visible([act])
        name = CALLBACK_FORMS.get(name) or name + 'Multiple'
        fd = td.get(f.kind, name) or fd
    key = 'OperatorCompare' if name.startswith('OperatorCompare') else (fd.script_name if fd is not None else name)
    out = []
    for i, p in enumerate(params):
        t = types[i] if i < len(types) else None
        if name == 'SetVariable' and i == 1:
            t = var_types.get(params[0].value)
        out.append(_norm_param(p, t, td, var_types))
    groups = collections.defaultdict(list)
    for c in children:
        groups[c.branch or 0].append(_norm_function(c, td, var_types))
    return (f.kind, key, tuple(out), tuple(sorted((b, tuple(v)) for b, v in groups.items())))


def _norm_param(p, t, td, var_types):
    if p.kind == FUNCTION and p.function is not None:
        if not _visible([p.function]):
            return ('nothing',)
        return ('f', _norm_function(p.function, td, var_types))
    index = _norm_param(p.index, 'integer', td, var_types) if p.index is not None else None
    return ('t', _param_text(p, t, td), index)


def _as_shown(fs, top=True, td=None):
    out = []
    for f in sorted(fs, key=(lambda f: f.kind) if top else (lambda f: f.branch or 0)):
        if td is not None and not _visible([f]):
            continue
        children = f.children if td is None or f.name in td.multiple else []
        out.append(wtg.Function(f.kind, f.name, f.enabled, [_param_as_shown(p, td) for p in f.params], f.branch,
                                _as_shown(children, False, td)))
    return out


def _param_as_shown(p, td=None):
    f = p.function
    if f is not None:
        children = f.children if td is None or f.name in td.multiple else []
        f = wtg.Function(f.kind, f.name, f.enabled, [_param_as_shown(x, td) for x in f.params], f.branch,
                         _as_shown(children, False, td))
    return wtg.Parameter(p.kind, p.value, f, _param_as_shown(p.index, td) if p.index is not None else None)


_KIND_NAMES = {PRESET: 'preset', VARIABLE: 'variable', FUNCTION: 'function', LITERAL: 'literal', -1: 'unset'}


def _shape(name):
    return 'OperatorCompare*' if name.startswith('OperatorCompare') else name


def _first_difference(a, b, td, where='trigger'):
    for k in range(max(len(a), len(b))):
        x = a[k] if k < len(a) else None
        y = b[k] if k < len(b) else None
        at = '%s.%d' % (where, k + 1)
        if x is None or y is None:
            z = y if x is None else x
            what = ('disabled function' if not z.enabled else 'CommentString' if z.name == 'CommentString' else
                    'function')
            return ('%s only in the %s' % (what, 'wtg' if x is None else 'model'), '%s %s' % (at, z.name))
        if x.name != y.name or x.kind != y.kind:
            if not y.enabled or y.name == 'CommentString':
                what = 'disabled function' if not y.enabled else 'CommentString'
                return ('%s only in the wtg' % what, '%s %s' % (at, y.name))
            return ('function %s vs %s' % (_shape(x.name), _shape(y.name)), '%s %s / %s' % (at, x.name, y.name))
        if x.enabled != y.enabled or x.branch != y.branch:
            return ('enabled or branch', '%s %s' % (at, x.name))
        for i, (p, q) in enumerate(zip(x.params, y.params)):
            d = _param_difference(p, q, td, '%s %s p%d' % (at, x.name, i + 1))
            if d:
                return d
        d = _first_difference(x.children, y.children, td, '%s %s' % (at, x.name))
        if d:
            return d
    return None


def _param_difference(p, q, td, at):
    if p.kind != q.kind:
        return ('param %s vs %s' % (_KIND_NAMES.get(p.kind), _KIND_NAMES.get(q.kind)),
                '%s: %r / %r' % (at, p.value, q.value))
    if p.kind == FUNCTION and p.function is not None and q.function is not None:
        d = _first_difference([p.function], [q.function], td, at)
        if d:
            return d
        if p.value != q.value:
            return ('stored value of a nested function %r vs %r' % (p.value[:12], q.value[:12]), at)
        return None
    if p.value != q.value:
        cls = 'value'
        if p.kind == PRESET:
            a, b = td.presets.get(p.value), td.presets.get(q.value)
            cls = 'another preset of the same code' if a and b and a.code == b.code else 'preset'
        return (cls, '%s: %r / %r' % (at, p.value, q.value))
    if (p.index is None) != (q.index is None):
        return ('array index', at)
    if p.index is not None:
        return _param_difference(p.index, q.index, td, at + '[]')
    return None


def _read(path):
    with open(path, 'rb') as f:
        return f.read()

