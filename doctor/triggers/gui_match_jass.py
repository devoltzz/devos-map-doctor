# Turns the JASS of a trigger back into the GUI events, conditions and actions it came from.
import collections
import re

from doctor.script import jass_ast
from doctor.script import jass_normal
from doctor.triggers import wtg


EVENT, CONDITION, ACTION, CALL = wtg.EVENT, wtg.CONDITION, wtg.ACTION, wtg.CALL
PRESET, VARIABLE, FUNCTION, LITERAL = wtg.PRESET, wtg.VARIABLE, wtg.FUNCTION, wtg.LITERAL
COMPARISONS = frozenset(('==', '!=', '<', '<=', '>', '>='))
ARITHMETIC = frozenset(('+', '-', '*', '/'))
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
LITERAL_TYPES = frozenset(('abilityuiyesnooption', 'disabledenabledoption', 'hideshowoption'))
REGISTRATION = frozenset(('CreateTrigger', 'DisableTrigger', 'TriggerAddCondition', 'TriggerAddAction'))
RX_EDITOR_HELPER = re.compile(r'^Func\d{3}(?:Func\d{3}|\d{3})*(?:C|A|\d{3})$')
RX_TRIGGER_BANNER = re.compile(r'^//\s?Trigger:\s?(.*)$')
RX_LINE_BREAK = re.compile(r'\r\n|\r|\n')
ONE_LINE_DEFAULT = {'A': False, 'B': False, 'Var': False, 'callback': False}
CUSTOM_SCRIPT_IDIOMS = frozenset(('RemoveLocation', 'DestroyGroup'))
RAWCODE_VARIABLE_TYPE = 'unitcode'


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
    while type(e) is jass_ast.Paren:
        e = e.inner
    return e


def _text(e):
    return jass_ast.unparse(e)


def _canon(text):
    return jass_ast.canonical(text)


def _is_name(e, name=None):
    e = _bare(e)
    return type(e) is jass_ast.Name and (name is None or e.name == name)


def _editor_unescape(body):
    if '\n' in body or '\r' in body:
        return None
    if '\\' not in body:
        return body
    out = []
    i = 0
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


_ALNUM = frozenset(b'0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz')


def _identifier(name):
    ident = ''.join(chr(c) if c in _ALNUM else '_' for c in name.rstrip(' ').encode('utf-8', 'surrogateescape'))
    return ident + 'u' if ident.endswith('_') else ident


class _Knowledge(object):
    def __init__(self, td):
        self.td = td
        self.ref = jass_normal.reference()
        self.presets = {}
        self.preset_types = collections.defaultdict(list)
        by_value, by_form = collections.defaultdict(list), collections.defaultdict(list)
        for p in td.presets.values():
            key = (p.type, _canon(p.code))
            self.presets.setdefault(key, p.name)
            self.preset_types[key[1]].append(p.type)
            constant = self.ref.constants.get(p.code)
            value = jass_normal.number(constant) if constant is not None else None
            if value is not None:
                by_value[(p.type,) + value].append(p.name)
            elif type(constant) is jass_ast.Call:
                by_form[(p.type, _canon(jass_ast.unparse(constant)))].append(p.name)
        self.preset_values = dict((k, v[0]) for k, v in by_value.items() if len(v) == 1)
        self.preset_forms = dict((k, v[0]) for k, v in by_form.items() if len(v) == 1 and k not in self.presets)
        self.compares = [f for f in td.conditions.values()
                         if len(f.arg_types) == 3 and f.arg_types[1] in ('ComparisonOperator', 'EqualNotEqualOperator')]
        self.operators = {}
        for f in self.compares:
            self.operators[f.arg_types[1]] = frozenset(p.code for p in td.presets.values()
                                                      if p.type == f.arg_types[1])
        self.boolean = next((f for f in self.compares if f.arg_types[0] == 'boolean'), None)
        self.extends, self.returns, self.global_types = self.ref.extends, self.ref.returns, self.ref.global_types

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


_CACHE = {}


def _cached(kind, obj, make):
    key = (kind, id(obj))
    hit = _CACHE.get(key)
    if hit is None or hit[0] is not obj:
        if len(_CACHE) > 16:
            _CACHE.clear()
        hit = _CACHE[key] = (obj, make(obj))
    return hit[1]


def _count_references(functions):
    counts = collections.Counter()
    for f in functions.values():
        if getattr(f, 'is_native', False):
            continue
        for node in jass_ast.walk(f):
            t = type(node)
            if t is jass_ast.Call or t is jass_ast.FuncRef:
                counts[node.name] += 1
    return counts


def _references(functions):
    return _cached('refs', functions, _count_references)


def _source_lines(source):
    if source is None or isinstance(source, list):
        return source
    return _cached('lines', source, RX_LINE_BREAK.split)


def _references_in(node, functions):
    out = []
    for n in jass_ast.walk(node):
        t = type(n)
        if (t is jass_ast.Call or t is jass_ast.FuncRef) and n.name in functions and n.name not in out:
            out.append(n.name)
    return out


def script_functions(script):
    out = {}
    for f in script.functions:
        out.setdefault(f.name, f)
    return out


class _Matcher(object):
    def __init__(self, functions, td, globals_types, prefix=None, lines=None, relaxed=False):
        self.functions = functions
        self.lines = lines
        self.relaxed = relaxed
        self.td = td
        self.k = _knowledge(td)
        self.types = globals_types or {}
        self.refs = _references(functions)
        self.prefix = prefix
        self.used = []
        self.used_set = set()
        self.custom = 0
        self.loose = []
        self.depth = 0

    def mark(self):
        return len(self.used), self.custom, len(self.loose)

    def reset(self, m):
        for name in self.used[m[0]:]:
            self.used_set.discard(name)
        del self.used[m[0]:]
        self.custom = m[1]
        del self.loose[m[2]:]

    def helper(self, name, returns):
        f = self.functions.get(name)
        if (f is None or getattr(f, 'is_native', False) or f.params or name in self.used_set or
                self.refs.get(name, 0) != 1 or (f.return_type == 'boolean') != (returns == 'boolean')):
            return None
        self.used.append(name)
        self.used_set.add(name)
        return f

    def hint(self, name):
        if self.prefix and name.startswith(self.prefix) and RX_EDITOR_HELPER.match(name[len(self.prefix):]):
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
        if t is jass_ast.Name:
            n = e.name
            if n.startswith(('udg_', 'gg_')) or n in self.types:
                return self.var_type(n)
            types = self.k.preset_types.get(n)
            if types and len(set(types)) == 1:
                return types[0]
            return self.k.global_types.get(n)
        if t is jass_ast.Index:
            return self.type_of(e.base)
        if t is jass_ast.Literal:
            return {'integer': 'integer', 'real': 'real', 'string': 'string', 'boolean': 'boolean'}.get(e.kind)
        if t is jass_ast.Unary:
            return 'boolean' if e.op == 'not' else self.type_of(e.operand)
        if t is jass_ast.Call:
            for c in self.k.calls('call', e.name):
                if len(c.arg_types) == len(e.args):
                    return c.return_type
            return self.k.returns.get(e.name)
        if t is jass_ast.Binary:
            if e.op in ARITHMETIC:
                return self.type_of(e.left) or self.type_of(e.right)
            return 'boolean'
        return None

    def param(self, e, t, again=True):
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
        p = None
        if cls is jass_ast.Name:
            p = self.name_param(e, t)
        elif cls is jass_ast.Literal:
            p = self.literal_param(e, e.kind, t)
        elif cls is jass_ast.Call:
            p = self.call_param(e, t)
        elif cls is jass_ast.Index:
            p = self.index_param(e, t)
        elif cls is jass_ast.Binary and e.op in ARITHMETIC:
            p = self.arithmetic_param(e, t)
        elif cls is jass_ast.Unary and e.op == '-':
            inner = _bare(e.operand)
            if type(inner) is jass_ast.Literal and inner.kind in ('integer', 'real') and inner is e.operand:
                p = self.literal_param(e, inner.kind, t)
        if p is None and again and self.relaxed and cls is not jass_ast.Literal:
            p = self.uninlined(e, t)
        return p

    def uninlined(self, e, t):
        ref = self.k.ref
        if type(e) is jass_ast.Name:
            for fn in ref.returned_by.get(e.name, ()):
                for c in self.k.calls('call', fn):
                    if not c.arg_types and (t is None or self.fits(c.return_type, t)):
                        return wtg.Parameter(FUNCTION, c.name, function=wtg.Function(CALL, c.name, 1, []))
            return None
        if self.depth >= 12:
            return None
        n = _bare(jass_normal.normal_expr(e, ref))
        self.depth += 1
        try:
            if _canon(_text(n)) != _canon(_text(e)):
                m = self.mark()
                p = self.param(n, t, False)
                if p is not None:
                    return p
                self.reset(m)
            for one, body in ref.wrappers().get(jass_normal.head(n), ()):
                if one.statement or not any(len(c.arg_types) == len(one.params)
                                            for c in self.k.calls('call', one.name)):
                    continue
                bound = jass_normal.unify(body, n, set(one.params))
                call = None if bound is None else jass_ast.Call(one.name, [bound[x] for x in one.params])
                if call is None or not jass_normal.same(jass_normal.normal_expr(call, ref), n):
                    continue
                m = self.mark()
                f = self.call_function(call, t)
                if f is not None:
                    return wtg.Parameter(FUNCTION, f.name, function=f)
                self.reset(m)
        finally:
            self.depth -= 1
        return None

    def rewrapped(self, call, kind):
        ref = self.k.ref
        n = _bare(jass_normal.normal_expr(call, ref))
        out = []
        for one, body in ref.wrappers().get(jass_normal.head(n), ()):
            if not self.k.calls(kind, one.name):
                continue
            bound = jass_normal.unify(body, n, set(one.params))
            other = None if bound is None else jass_ast.Call(one.name, [bound[x] for x in one.params])
            if other is not None and jass_normal.same(jass_normal.normal_expr(other, ref), n):
                out.append(other)
        return out

    def preset_param(self, e, t):
        if t in LITERAL_TYPES:
            return None
        code = _canon(_text(e))
        name = self.k.preset(code, t)
        if name is None and self.relaxed and t is not None:
            value = jass_normal.number(e)
            if value is None:
                name = self.k.preset_forms.get((t, code))
            elif self.k.base(t) != t:
                name = self.k.preset_values.get((t,) + value)
        return None if name is None else wtg.Parameter(PRESET, name)

    def name_param(self, e, t):
        n = e.name
        if n.startswith('udg_') or n.startswith('gg_'):
            if not self.fits(self.var_type(n), t):
                return None
            return wtg.Parameter(VARIABLE, n[4:] if n.startswith('udg_') else n)
        return self.preset_param(e, t)

    def index_param(self, e, t):
        p = self.preset_param(e, t)
        if p is not None:
            return p
        base = _bare(e.base)
        if type(base) is not jass_ast.Name or not base.name.startswith(('udg_', 'gg_')):
            return None
        if not self.fits(self.var_type(base.name), t):
            return None
        m = self.mark()
        index = self.param(e.index, 'integer')
        if index is None:
            self.reset(m)
            return None
        n = base.name
        return wtg.Parameter(VARIABLE, n[4:] if n.startswith('udg_') else n, index=index)

    def literal_param(self, e, kind, t):
        p = self.preset_param(e, t)
        if p is not None:
            return p
        base = self.k.base(t)
        text = _text(e)
        if kind == 'string':
            if t is not None and base != 'string':
                return None
            value = _editor_unescape(text[1:-1])
            return None if value is None else wtg.Parameter(LITERAL, value)
        if kind == 'rawcode' and len(text) == 3 and self.relaxed and t is not None and base in ('integer', 'real'):
            return wtg.Parameter(LITERAL, str(jass_normal.number(e)[1]))
        if kind == 'rawcode':
            if t is not None and (base != 'integer' or t in ('integer', 'integervar')):
                return None
            body = text[1:-1]
            return None if '\\' in body else wtg.Parameter(LITERAL, body)
        if kind in ('integer', 'real'):
            if t is not None and base not in ('integer', 'real'):
                return None
            if kind == 'real' and base == 'integer':
                return None
            return wtg.Parameter(LITERAL, text if not self.relaxed else _plain_number(
                e, kind, text, base == 'integer' and t not in (None, 'integer', 'integervar')))
        if kind == 'boolean':
            if t is not None and base != 'boolean':
                return None
            return wtg.Parameter(LITERAL, text)
        return None

    def call_param(self, e, t):
        p = self.preset_param(e, t)
        if p is not None:
            return p
        f = self.call_function(e, t)
        return None if f is None else wtg.Parameter(FUNCTION, f.name, function=f)

    def call_function(self, e, t):
        cands = [c for c in self.k.calls('call', e.name) if len(c.arg_types) == len(e.args) and
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
        base = self.k.base(t)
        if base not in ('integer', 'real', 'string'):
            guess = self.type_of(e)
            base = self.k.base(guess) if guess else None
            if t is not None and not self.fits(base, t):
                return None
        op = None
        if base == 'string':
            if e.op != '+':
                return None
            name = 'OperatorString'
        elif base in ('integer', 'real'):
            name = 'OperatorInt' if base == 'integer' else 'OperatorReal'
            op = self.k.preset(e.op, 'ArithmeticOperator')
            if op is None:
                return None
        else:
            return None
        f = self.td.calls.get(name)
        if f is None:
            return None
        params = self.params((e.left, e.right), [f.arg_types[0], f.arg_types[-1]])
        if params is None:
            return None
        if name != 'OperatorString':
            params.insert(1, wtg.Parameter(PRESET, op))
        return wtg.Parameter(FUNCTION, name, function=wtg.Function(CALL, name, 1, params))

    def var_as_string(self, e):
        if type(e) is jass_ast.Literal and e.kind == 'string':
            body = e.text[1:-1]
            if re.match(r'^udg_\w+$', body):
                return wtg.Parameter(VARIABLE, body[4:])
        return None

    def code_param(self, e):
        if type(e) is not jass_ast.FuncRef:
            return None
        m = self.mark()
        f = self.helper(e.name, 'nothing')
        if f is None:
            return None
        acts = self.body_actions(f)
        single = self.one_line(acts[0]) if len(acts) == 1 else None
        if single is None:
            self.reset(m)
            return None
        return wtg.Parameter(FUNCTION, 'DoNothing', function=single)

    def condition_helper(self, name):
        m = self.mark()
        f = self.helper(name, 'boolean')
        if f is None:
            return None
        if f.locals or len(f.body) != 1 or type(f.body[0]) is not jass_ast.ReturnStmt or f.body[0].value is None:
            self.reset(m)
            return None
        cond = self.condition(f.body[0].value)
        if cond is None:
            self.reset(m)
        return cond

    def boolexpr_param(self, e):
        if (type(e) is jass_ast.Call and e.name == 'Condition' and len(e.args) == 1 and
                type(_bare(e.args[0])) is jass_ast.FuncRef):
            cond = self.condition_helper(_bare(e.args[0]).name)
            if cond is not None:
                return wtg.Parameter(FUNCTION, '', function=cond)
        return None

    def boolcall_param(self, e):
        cond = self.condition_helper(e.name) if type(e) is jass_ast.Call and not e.args else None
        if cond is None:
            cond = self.condition(e)
        return None if cond is None else wtg.Parameter(FUNCTION, '', function=cond)

    def condition(self, e):
        e = _bare(e)
        cls = type(e)
        if cls is jass_ast.Binary and e.op in COMPARISONS:
            c = self.comparison(e)
            return c if c is not None or not self.relaxed or e.op not in ('==', '!=') else self.null_condition(e)
        if cls is jass_ast.Call:
            if not e.args:
                multiple = self.multiple_condition(e.name)
                if multiple is not None:
                    return multiple
            for c in self.k.calls('condition', e.name):
                if len(c.arg_types) == len(e.args) and c.name not in self.td.multiple:
                    params = self.params(e.args, c.arg_types)
                    if params is not None:
                        return wtg.Function(CONDITION, c.name, 1, params)
        if cls is jass_ast.Literal and e.kind == 'boolean':
            kind = 'AndMultiple' if e.text == 'true' else 'OrMultiple'
            if kind in self.td.conditions:
                return wtg.Function(CONDITION, kind, 1, [], None, [])
        if not self.relaxed:
            return None
        if cls is jass_ast.Binary and e.op in ('and', 'or'):
            return self.chain_condition(e)
        return self.boolean_condition(e)

    def chain_condition(self, e):
        kind = 'AndMultiple' if e.op == 'and' else 'OrMultiple'
        if kind not in self.td.conditions:
            return None
        m = self.mark()
        children = []
        for x in _chain(e, e.op):
            c = self.condition(x)
            if c is None:
                self.reset(m)
                return None
            c.branch = 0
            children.append(c)
        return wtg.Function(CONDITION, kind, 1, [], None, children)

    def null_condition(self, e):
        for a, b in ((e.left, e.right), (e.right, e.left)):
            a, b = _bare(a), _bare(b)
            if type(b) is not jass_ast.Literal or b.kind != 'null' or self.k.base(self.type_of(a)) != 'boolean':
                continue
            if e.op == '!=':
                return self.condition(a)
            if type(a) in (jass_ast.Call, jass_ast.Name, jass_ast.Index):
                return self.boolean_condition(jass_ast.Unary('not', a))
        return None

    def boolean_condition(self, e):
        f = self.k.boolean
        if f is None:
            return None
        value = 'true'
        if type(e) is jass_ast.Unary and e.op == 'not':
            e, value = _bare(e.operand), 'false'
        if type(e) not in (jass_ast.Call, jass_ast.Name, jass_ast.Index):
            return None
        op = self.k.preset('==', f.arg_types[1])
        m = self.mark()
        a = self.param(e, f.arg_types[0])
        b = self.param(jass_ast.Literal('boolean', value), f.arg_types[2]) if a is not None and op else None
        if b is None:
            self.reset(m)
            return None
        return wtg.Function(CONDITION, f.name, 1, [a, wtg.Parameter(PRESET, op), b])

    def compare_order(self, e):
        strong, weak = [], []
        for x in (e.left, e.right):
            t = self.type_of(x)
            if t:
                x = _bare(x)
                literal = type(x) is jass_ast.Literal or type(x) is jass_ast.Unary and type(
                    _bare(x.operand)) is jass_ast.Literal
                (weak if literal else strong).append(t)
        bases = set(self.k.base(t) for t in strong + weak)

        def score(f):
            t = f.arg_types[0]
            if t in strong:
                return 0
            if t in weak:
                return 1
            if self.k.base(t) in bases:
                return 2 if t in bases else 3
            return 4
        return sorted(self.k.compares, key=score)

    def comparison(self, e):
        for f in self.compare_order(e):
            op_type = f.arg_types[1]
            if e.op not in self.k.operators.get(op_type, ()):
                continue
            op = self.k.preset(e.op, op_type)
            m = self.mark()
            a = self.param(e.left, f.arg_types[0])
            if a is None:
                self.reset(m)
                continue
            b = self.param(e.right, f.arg_types[2])
            if b is None:
                self.reset(m)
                continue
            return wtg.Function(CONDITION, f.name, 1, [a, wtg.Parameter(PRESET, op), b])
        return None

    def multiple_condition(self, name):
        m = self.mark()
        f = self.helper(name, 'boolean')
        if f is None:
            return None
        for kind, fail, ok in (('AndMultiple', 'false', 'true'), ('OrMultiple', 'true', 'false')):
            if kind not in self.td.conditions:
                continue
            tests = _tests(f, fail, ok, negated=kind == 'AndMultiple', folded=self.relaxed)
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

    def custom_line(self, text, node=None, line=0):
        self.custom += 1
        if node is not None:
            self.loose.extend(_references_in(node, self.functions))
        if self.lines is not None and 0 < line <= len(self.lines):
            source = self.lines[line - 1].lstrip(' \t')
            if source != text and _canon(source) == _canon(text):
                text = source
        return wtg.Function(ACTION, 'CustomScriptCode', 1, [wtg.Parameter(LITERAL, text)])

    def custom_stmt(self, s):
        lines = jass_ast.unparse(s).rstrip('\n').split('\n')
        if len(lines) == 1:
            return [self.custom_line(lines[0], s, s.line)]
        self.loose.extend(_references_in(s, self.functions))
        return [self.custom_line(x.strip()) for x in lines]

    def custom_block(self, s, bodies=None):
        out = []
        if type(s) is jass_ast.IfStmt:
            for k, (cond, body) in enumerate(s.branches):
                head = 'else' if cond is None else '%s %s then' % ('if' if k == 0 else 'elseif', _text(cond))
                comment = s.branch_comments[k] if k < len(s.branch_comments) else None
                line = s.branch_lines[k] if k < len(s.branch_lines) else 0
                out.append(self.custom_line(head + (' ' + comment if comment else ''), cond, line))
                out.extend(bodies[k] if bodies is not None else self.actions(body))
            out.append(self.custom_line('endif' + (' ' + s.end_comment if s.end_comment else ''), None, s.end_line))
        else:
            out.append(self.custom_line('loop' + (' ' + s.comment if s.comment else ''), None, s.line))
            out.extend(self.actions(s.body))
            out.append(self.custom_line('endloop' + (' ' + s.end_comment if s.end_comment else ''), None,
                                        s.end_line))
        return out

    def body_actions(self, f):
        out = []
        for d in f.locals:
            for c in d.leading_comments:
                out.append(self.comment(c))
            text = jass_ast.unparse(d, comments=False).rstrip('\n') + (' ' + d.comment if d.comment else '')
            out.append(self.custom_line(text, d, d.line))
        return out + self.actions(f.body)

    def comment(self, text):
        if 'CommentString' not in self.td.actions:
            return self.custom_line(text)
        return wtg.Function(ACTION, 'CommentString', 1, [wtg.Parameter(LITERAL, text[3:] if text[2:3] == ' '
                                                                        else text[2:])])

    def actions(self, stmts):
        out = []
        i = 0
        while i < len(stmts):
            used, acts = self.statement(stmts, i)
            out.extend(acts)
            i += used
        return out

    def statement(self, stmts, i):
        s = stmts[i]
        t = type(s)
        if t is jass_ast.CommentStmt:
            return 1, [self.comment(s.text)]
        if t is jass_ast.SetStmt:
            loop = self.for_loop(stmts, i)
            if loop is not None:
                return loop
            a = self.set_variable(s)
        elif t is jass_ast.CallStmt:
            a = self.call_action(s.call)
        elif t is jass_ast.IfStmt:
            bodies = [self.actions(body) for _c, body in s.branches]
            a = self.if_action(s, bodies)
            if a is None:
                return 1, self.custom_block(s, bodies)
        elif t is jass_ast.LoopStmt:
            a = self.wait_for_condition(s)
            if a is None:
                return 1, self.custom_block(s)
        elif t is jass_ast.ReturnStmt and s.value is None and 'ReturnAction' in self.td.actions:
            a = wtg.Function(ACTION, 'ReturnAction', 1, [])
        else:
            a = None
        if a is None:
            return 1, self.custom_stmt(s)
        return 1, [a]

    def set_variable(self, s):
        if 'SetVariable' not in self.td.actions:
            return None
        target = _bare(s.target)
        name = target.name if type(target) is jass_ast.Name else _bare(target.base).name
        if not name.startswith('udg_'):
            return None
        m = self.mark()
        var = self.param(target, None)
        if var is None:
            return None
        t = self.var_type(name)
        value = self.param(s.value, t if t else None)
        if value is None:
            self.reset(m)
            return None
        return wtg.Function(ACTION, 'SetVariable', 1, [var, value])

    def call_action(self, call, again=True):
        if call.name in CUSTOM_SCRIPT_IDIOMS:
            return None
        a = self.plain_action(call)
        if a is None and again and self.relaxed:
            for other in self.rewrapped(call, 'action') + self.rewrapped(call, 'event'):
                m = self.mark()
                a = self.plain_action(other)
                if a is not None:
                    break
                self.reset(m)
        return a

    def plain_action(self, call):
        cands = self.k.calls('action', call.name)
        ref = _bare(call.args[-1]) if call.args else None
        if type(ref) is jass_ast.FuncRef:
            one = next((c for c in cands if c.name in CALLBACK_FORMS), None)
            multiple = next((c for c in cands if c.name in CALLBACK_FORMS.values()), None)
            if one is not None or multiple is not None:
                a = self.callback_action(call, ref, one, multiple)
                if a is not None:
                    return a
        for c in cands:
            if c.name not in self.td.multiple and len(call.args) == len(c.arg_types):
                params = self.params(call.args, c.arg_types)
                if params is not None:
                    return wtg.Function(ACTION, c.name, 1, params)
        if 'AddTriggerEvent' in self.td.actions and call.args:
            for c in self.k.calls('event', call.name):
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

    def callback_action(self, call, ref, one, multiple):
        types = multiple.arg_types if multiple is not None else one.arg_types[:-1]
        if len(call.args) != len(types) + 1:
            return None
        m = self.mark()
        params = self.params(call.args[:-1], types)
        f = self.helper(ref.name, 'nothing') if params is not None else None
        if f is None:
            self.reset(m)
            return None
        acts = self.body_actions(f)
        hint = self.hint(ref.name)
        one_line = hint == 'digits' if hint else ONE_LINE_DEFAULT['callback']
        single = self.one_line(acts[0]) if one is not None and len(acts) == 1 else None
        if single is not None and (one_line or multiple is None):
            return wtg.Function(ACTION, one.name, 1, params + [wtg.Parameter(FUNCTION, 'DoNothing', function=single)])
        if multiple is None:
            self.reset(m)
            return None
        for a in acts:
            a.branch = 0
        return wtg.Function(ACTION, multiple.name, 1, params, None, acts)

    def for_loop(self, stmts, i):
        s = stmts[i]
        target = _bare(s.target)
        if type(target) is jass_ast.Name and target.name in ('bj_forLoopAIndex', 'bj_forLoopBIndex'):
            letter = target.name[10]
            if i + 2 >= len(stmts) or type(stmts[i + 1]) is not jass_ast.SetStmt:
                return None
            s1, loop = stmts[i + 1], stmts[i + 2]
            if not _is_name(s1.target, target.name + 'End') or type(loop) is not jass_ast.LoopStmt:
                return None
            index_text, limit, used = target.name, jass_ast.Name(target.name + 'End'), 3
            starts = [(s.value, 'integer'), (s1.value, 'integer')]
        elif (type(target) is jass_ast.Name and target.name.startswith('udg_') or type(target) is jass_ast.Index and
              _is_name(target.base) and _bare(target.base).name.startswith('udg_')):
            letter = 'Var'
            if i + 1 >= len(stmts) or type(stmts[i + 1]) is not jass_ast.LoopStmt:
                return None
            loop, index_text, limit, used = stmts[i + 1], _canon(_text(target)), None, 2
            starts = [(target, 'integervar'), (s.value, 'integer')]
        else:
            return None
        body = loop.body
        if len(body) < 2 or type(body[0]) is not jass_ast.ExitWhenStmt or type(body[-1]) is not jass_ast.SetStmt:
            return None
        test = _bare(body[0].cond)
        if type(test) is not jass_ast.Binary or test.op != '>' or _canon(_text(_bare(test.left))) != _canon(
                index_text if letter != 'Var' else _text(target)):
            return None
        if limit is not None and not _is_name(test.right, limit.name):
            return None
        step = body[-1]
        inc = _bare(step.value)
        if (_canon(_text(_bare(step.target))) != _canon(_text(_bare(test.left))) or type(inc) is not jass_ast.Binary
                or inc.op != '+' or _canon(_text(_bare(inc.left))) != _canon(_text(_bare(test.left))) or
                not _is_literal(inc.right, '1')):
            return None
        if letter == 'Var':
            starts.append((test.right, 'integer'))
        one, multiple = LOOP_FORMS[letter]
        if multiple not in self.td.actions:
            return None
        params = self.params([e for e, _t in starts], [t for _e, t in starts])
        if params is None:
            return None
        acts = self.actions(body[1:-1])
        if (len(acts) == 1 and acts[0].name not in self.td.multiple and ONE_LINE_DEFAULT.get(letter) and
                one in self.td.actions):
            params.append(wtg.Parameter(FUNCTION, 'DoNothing', function=acts[0]))
            return used, [wtg.Function(ACTION, one, 1, params)]
        for a in acts:
            a.branch = 0
        return used, [wtg.Function(ACTION, multiple, 1, params, None, acts)]

    def wait_for_condition(self, s):
        body = s.body
        if len(body) != 2 or type(body[0]) is not jass_ast.ExitWhenStmt or type(body[1]) is not jass_ast.CallStmt:
            return None
        sleep = body[1].call
        if sleep.name != 'TriggerSleepAction' or len(sleep.args) != 1 or 'WaitForCondition' not in self.td.actions:
            return None
        wait = _bare(sleep.args[0])
        if (type(wait) is not jass_ast.Call or wait.name != 'RMaxBJ' or len(wait.args) != 2 or
                not _is_name(wait.args[0], 'bj_WAIT_FOR_COND_MIN_INTERVAL')):
            return None
        m = self.mark()
        cond = self.boolcall_param(_bare(body[0].cond))
        if cond is None:
            return None
        interval = self.param(wait.args[1], self.td.actions['WaitForCondition'].arg_types[1])
        if interval is None:
            self.reset(m)
            return None
        return wtg.Function(ACTION, 'WaitForCondition', 1, [cond, interval])

    def if_action(self, s, bodies):
        if len(s.branches) == 1 and self.relaxed:
            bodies = [bodies[0], []]
        elif len(s.branches) != 2 or s.branches[1][0] is not None:
            return None
        cond = _bare(s.branches[0][0])
        then, other = bodies
        m = self.mark()
        f = self.helper(cond.name, 'boolean') if type(cond) is jass_ast.Call and not cond.args else None
        tests = _tests(f, 'false', 'true', negated=True) if f is not None else [] if _is_literal(cond, 'true') else None
        if tests is not None and 'IfThenElseMultiple' in self.td.actions:
            children = []
            for x in tests:
                c = self.condition(x)
                if c is None:
                    self.reset(m)
                    return None
                c.branch = 0
                children.append(c)
            for branch, acts in ((1, then), (2, other)):
                for a in acts:
                    a.branch = branch
                    children.append(a)
            return wtg.Function(ACTION, 'IfThenElseMultiple', 1, [], None, children)
        if f is None:
            expr = cond
        elif not f.locals and len(f.body) == 1 and type(f.body[0]) is jass_ast.ReturnStmt:
            expr = f.body[0].value
        else:
            expr = None
        sides = [self.one_line(x[0]) for x in (then, other) if len(x) == 1]
        if expr is not None and 'IfThenElse' in self.td.actions and len(sides) == 2 and None not in sides:
            c = self.condition(expr)
            if c is not None:
                return wtg.Function(ACTION, 'IfThenElse', 1, [
                    wtg.Parameter(FUNCTION, '', function=c), wtg.Parameter(FUNCTION, 'DoNothing', function=sides[0]),
                    wtg.Parameter(FUNCTION, 'DoNothing', function=sides[1])])
        if expr is not None and self.relaxed and 'IfThenElseMultiple' in self.td.actions:
            children = []
            for x in _chain(_bare(expr), 'and'):
                c = self.condition(x)
                if c is None:
                    self.reset(m)
                    return None
                c.branch = 0
                children.append(c)
            for branch, acts in ((1, then), (2, other)):
                for a in acts:
                    a.branch = branch
                    children.append(a)
            return wtg.Function(ACTION, 'IfThenElseMultiple', 1, [], None, children)
        self.reset(m)
        return None

    def event(self, call, again=True):
        for c in self.k.calls('event', call.name):
            if len(c.arg_types) + 1 == len(call.args):
                params = self.params(call.args[1:], c.arg_types)
                if params is not None:
                    return wtg.Function(EVENT, c.name, 1, params)
        for other in (self.rewrapped(call, 'event') if again and self.relaxed else ()):
            e = self.event(other, False)
            if e is not None:
                return e
        return None


RX_DECIMAL = re.compile(r'^-?\d+$')
RX_REAL = re.compile(r'^-?\d+\.\d+$')


def _plain_number(e, kind, text, code):
    text = text.replace(' ', '')
    if kind == 'integer':
        value = jass_normal.number(e)
        if value is None:
            return text
        if code:
            spelled = jass_normal.integer_text(value[1])
            if spelled[0] == "'":
                return spelled[1:-1]
        return text if RX_DECIMAL.match(text) and not (len(text.lstrip('-')) > 1 and text.lstrip('-')[0] == '0') \
            else str(value[1])
    if RX_REAL.match(text):
        return text
    sign = '-' if text.startswith('-') else ''
    body = text.lstrip('-')
    if body.startswith('.'):
        body = '0' + body
    if body.endswith('.'):
        body += '0'
    return sign + body


def _tests(f, fail, ok, negated, folded=False):
    if f.locals or not f.body:
        return None
    last = f.body[-1]
    body = [s for s in f.body if type(s) is not jass_ast.CommentStmt]
    if (folded and len(body) == 1 and type(last) is jass_ast.ReturnStmt and last.value is not None and
            type(_bare(last.value)) is not jass_ast.Literal):
        return _chain(_bare(last.value), 'and' if negated else 'or')
    if type(last) is not jass_ast.ReturnStmt or not _is_literal(last.value, ok):
        return None
    out = []
    for s in f.body[:-1]:
        if type(s) is not jass_ast.IfStmt or len(s.branches) != 1:
            return None
        cond, body = s.branches[0]
        if len(body) != 1 or type(body[0]) is not jass_ast.ReturnStmt or not _is_literal(body[0].value, fail):
            return None
        cond = _bare(cond)
        if negated:
            if type(cond) is not jass_ast.Unary or cond.op != 'not':
                return None
            cond = cond.operand
        out.append(cond)
    return out


def _chain(e, op):
    e = _bare(e)
    if type(e) is jass_ast.Binary and e.op == op:
        return _chain(e.left, op) + _chain(e.right, op)
    return [e]


def _is_literal(e, text):
    e = _bare(e) if e is not None else None
    return type(e) is jass_ast.Literal and e.text == text


def _banner(functions, names):
    first = min((functions[n] for n in names if n in functions), key=lambda f: f.line, default=None)
    comments = list(getattr(first, 'leading_comments', None) or ())
    for k, c in enumerate(comments):
        m = RX_TRIGGER_BANNER.match(c)
        if m:
            rest = comments[k + 1:]
            desc = []
            if rest and rest[0].rstrip() == '//':
                for c2 in rest[1:]:
                    if c2.startswith('//=='):
                        break
                    desc.append(c2[3:] if c2[2:3] == ' ' else c2[2:])
            return m.group(1), '\r\n'.join(desc)
    return None, ''


def _init_statements(init):
    if init.params or init.return_type != 'nothing' or init.locals:
        raise _Fail('no InitTrig shape: %s' % ('locals' if init.locals else 'parameters or a return type'))
    body = [s for s in init.body if type(s) is not jass_ast.CommentStmt]
    if not body or type(body[0]) is not jass_ast.SetStmt or not _is_name(body[0].target):
        raise _Fail('no InitTrig shape: no set <trigger> = CreateTrigger()')
    value = _bare(body[0].value)
    if type(value) is not jass_ast.Call or value.name != 'CreateTrigger' or value.args:
        raise _Fail('no InitTrig shape: no set <trigger> = CreateTrigger()')
    trig = _bare(body[0].target).name
    i, off, events, cond, act = 1, False, [], None, None

    def call(k, name=None):
        s = body[k] if k < len(body) else None
        if type(s) is not jass_ast.CallStmt or not s.call.args or not _is_name(s.call.args[0], trig):
            return None
        return s.call if name is None or s.call.name == name else None

    if call(i, 'DisableTrigger') and len(body[i].call.args) == 1:
        off, i = True, i + 1
    while call(i) and body[i].call.name not in REGISTRATION:
        events.append(body[i].call)
        i += 1
    c = call(i, 'TriggerAddCondition')
    if c:
        arg = _bare(c.args[1]) if len(c.args) == 2 else None
        if (type(arg) is not jass_ast.Call or arg.name != 'Condition' or len(arg.args) != 1 or
                type(_bare(arg.args[0])) is not jass_ast.FuncRef):
            raise _Fail('conditions not a Condition(function F)')
        cond, i = _bare(arg.args[0]).name, i + 1
    c = call(i, 'TriggerAddAction')
    if not c or len(c.args) != 2 or type(_bare(c.args[1])) is not jass_ast.FuncRef:
        raise _Fail('InitTrig does more than register: %s' % _first_line(body[i]) if i < len(body) else
                    'no TriggerAddAction')
    act, i = _bare(c.args[1]).name, i + 1
    if i < len(body):
        raise _Fail('InitTrig does more than register: %s' % _first_line(body[i]))
    return trig, off, events, cond, act


def _first_line(s):
    return jass_ast.unparse(s).split('\n')[0].strip()[:120]


def match_trigger(functions, init_name, td, globals_types=None, name=None, source=None, relaxed=False):
    init = functions.get(init_name)
    if init is None or getattr(init, 'is_native', False):
        return Match(None, 'no function %s' % init_name)
    try:
        trig, off, event_calls, cond_name, act_name = _init_statements(init)
        prefix = act_name[:-7] if act_name.endswith('_Actions') else None
        m = _Matcher(functions, td, globals_types, prefix, _source_lines(source), relaxed)
        events = []
        for call in event_calls:
            e = m.event(call)
            if e is None:
                raise _Fail('event %s: no GUI event matches' % _text(call)[:120])
            events.append(e)
        conditions = []
        if cond_name is not None:
            f = m.helper(cond_name, 'boolean')
            tests = _tests(f, 'false', 'true', negated=True, folded=relaxed) if f is not None else None
            if tests is None:
                raise _Fail('conditions not a Trig_Conditions: %s' % cond_name)
            for x in tests:
                c = m.condition(x)
                if c is None:
                    raise _Fail('condition not GUI: %s' % _text(x)[:120])
                conditions.append(c)
        f = m.helper(act_name, 'nothing')
        if f is None:
            raise _Fail('actions not a Trig_Actions: %s' % act_name)
        actions = m.body_actions(f)
    except _Fail as e:
        return Match(None, str(e), [init_name])
    helpers = [init_name] + m.used
    covered = set(helpers)
    external, stack = [], list(reversed(m.loose))
    while stack:
        n = stack.pop()
        if n in covered or n in external or n not in functions or getattr(functions[n], 'is_native', False):
            continue
        external.append(n)
        stack.extend(reversed(_references_in(functions[n], functions)))
    banner, description = _banner(functions, helpers)
    if name is None:
        ident = init_name[9:] if init_name.startswith('InitTrig_') else None
        name = banner if banner is not None and ident in (None, _identifier(banner)) else ident or init_name
    t = wtg.Trigger(name, description, 0, 1, 0, 1 if off else 0, 0, 0, events + conditions + actions)
    return Match(t, '', helpers, external, m.custom)


def _gui_types(functions, td, types, initialized):
    k = _knowledge(td)
    evidence = collections.defaultdict(collections.Counter)

    def var_of(e):
        e = _bare(e)
        if type(e) is jass_ast.Index:
            e = _bare(e.base)
        return e.name if type(e) is jass_ast.Name and types.get(e.name) == 'integer' else None

    def returned(e):
        e = _bare(e)
        if type(e) is jass_ast.Call:
            for c in k.calls('call', e.name):
                if len(c.arg_types) == len(e.args):
                    return c.return_type
        if type(e) is jass_ast.Literal and e.kind == 'rawcode':
            return '<rawcode>'
        return None

    for f in functions.values():
        for node in jass_ast.walk(f):
            t = type(node)
            if t is jass_ast.Call:
                for kind, skip in (('action', 0), ('call', 0), ('event', 1), ('condition', 0)):
                    for c in k.calls(kind, node.name):
                        n = len(c.arg_types) + skip
                        if n != len(node.args) and not (c.name in CALLBACK_FORMS.values() and n + 1 == len(node.args)):
                            continue
                        for a, at in zip(node.args[skip:], c.arg_types):
                            v = var_of(a)
                            if v:
                                evidence[v][at] += 1
            elif t is jass_ast.SetStmt:
                v = var_of(node.target)
                r = returned(node.value) if v else None
                if r:
                    evidence[v][r] += 1
            elif t is jass_ast.Binary and node.op in COMPARISONS:
                for a, b in ((node.left, node.right), (node.right, node.left)):
                    v = var_of(a)
                    r = returned(b) if v else None
                    if r:
                        evidence[v][r] += 1
    out = {}
    for v, jass_type in types.items():
        if jass_type != 'integer' or not v.startswith('udg_'):
            continue
        ev = evidence.get(v, {})
        codes = collections.Counter(dict((t, n) for t, n in ev.items()
                                         if t not in ('integer', 'integervar', '<rawcode>') and t in td.types and
                                         td.base_type(t) == 'integer' and td.types[t].can_be_global))
        if codes:
            out[v] = (codes.most_common(1)[0][0], 'uses')
        elif initialized is not None and v not in initialized:
            out[v] = (RAWCODE_VARIABLE_TYPE, 'no InitGlobals line')
        elif ev.get('<rawcode>'):
            out[v] = (RAWCODE_VARIABLE_TYPE, 'rawcode value')
        else:
            out[v] = ('integer', 'uses' if ev else 'default')
    return out


def _init_values(script):
    f = next((x for x in script.functions if x.name == 'InitGlobals'), None)
    values, sizes = {}, {}
    for s in (f.body if f is not None else ()):
        if type(s) is jass_ast.SetStmt and _is_name(s.target):
            values.setdefault(_bare(s.target).name, s.value)
        elif type(s) is jass_ast.LoopStmt and len(s.body) == 3:
            ew, st, inc = s.body
            test = _bare(ew.cond) if type(ew) is jass_ast.ExitWhenStmt else None
            target = _bare(st.target) if type(st) is jass_ast.SetStmt else None
            if (type(test) is jass_ast.Binary and test.op == '>' and type(_bare(test.right)) is jass_ast.Literal and
                    _bare(test.right).kind == 'integer' and type(target) is jass_ast.Index and
                    _is_name(target.base) and type(inc) is jass_ast.SetStmt):
                name = _bare(target.base).name
                sizes.setdefault(name, _bare(test.right).value)
                values.setdefault(name, st.value)
    return values, sizes


def match_globals(script, td):
    types = dict((g.name, g.type) for g in script.globals)
    functions = script_functions(script)
    values, sizes = _init_values(script)
    has_init = any(f.name == 'InitGlobals' for f in script.functions)
    gui = _gui_types(functions, td, types, values if has_init else None)
    gui_of = dict((n, gui[n][0] if n in gui else t) for n, t in types.items() if n.startswith('udg_'))
    m = _Matcher(functions, td, dict(types, **gui_of))
    out = []
    for g in script.globals:
        if not g.name.startswith('udg_') or g.is_constant:
            continue
        t = gui_of[g.name]
        v = wtg.Variable(g.name[4:], t, 1 if g.is_array else 0, sizes.get(g.name, 1) if g.is_array else 1)
        e = values.get(g.name)
        if e is not None:
            default = td.type_defaults.get(t)
            if default is None and td.base_type(t) == 'string':
                default = '""'
            if default is None or _canon(_text(_bare(e))) != _canon(default):
                p = m.param(e, t)
                if p is not None and p.kind in (PRESET, LITERAL):
                    v.initialized, v.initial_value = 1, p.value
        out.append(v)
    return out, types


_ONE_TO_MULTIPLE = dict(list(CALLBACK_FORMS.items()) + list(LOOP_FORMS.values()))
_RX_INTEGER = re.compile(r'^-?(?:\d+|0[xX][0-9A-Fa-f]+|\$[0-9A-Fa-f]+)$')


def _rendered(td, p, t):
    if p.kind == PRESET:
        pr = td.presets.get(p.value)
        return pr.code if pr is not None else p.value
    base = td.base_type(t) if t else None
    if t == 'scriptcode' or base not in ('string', 'integer') or t == 'integer' or (
            base == 'integer' and _RX_INTEGER.match(p.value)):
        return p.value
    if base == 'string':
        return '"%s"' % p.value.replace('\\', '\\\\').replace('"', '\\"')
    return "'%s'" % p.value


def _ftree(td, f, eq, var_types):
    fd = td.get(f.kind, f.name)
    types = list(fd.arg_types) if fd is not None else []
    params = []
    for k, p in enumerate(f.params):
        t = types[k] if k < len(types) else None
        if f.name == 'SetVariable' and k == 1:
            t = var_types.get(f.params[0].value)
        params.append(_ptree(td, p, t, eq, var_types))
    kids = sorted((c for c in f.children if c.enabled or not eq), key=lambda c: c.branch or 0)
    name = f.name
    if eq and name in _ONE_TO_MULTIPLE and f.params and f.params[-1].function is not None:
        child = f.params[-1].function
        name, params = _ONE_TO_MULTIPLE[name], params[:-1]
        kids = [wtg.Function(child.kind, child.name, child.enabled, child.params, 0, child.children)]
    return (f.kind, name, f.enabled, tuple(params), f.branch, tuple(_ftree(td, c, eq, var_types) for c in kids))


def _ptree(td, p, t, eq, var_types):
    kind, value = p.kind, p.value
    if eq and kind == FUNCTION:
        value = ''
    elif eq and kind in (PRESET, LITERAL):
        kind, value = 'text', _rendered(td, p, t)
    return (kind, value, _ftree(td, p.function, eq, var_types) if p.function is not None else None,
            _ptree(td, p.index, 'integer', eq, var_types) if p.index is not None else None)


def _dump(f, indent, out):
    branch = '' if f.branch is None else '[%d] ' % f.branch
    out.append('%s%s%s %s%s' % (indent, branch, wtg.KINDS[f.kind], f.name, '' if f.enabled else ' (disabled)'))
    for p in f.params:
        _dump_param(p, indent + '    ', out)
    for c in f.children:
        _dump(c, indent + '  ', out)


def _dump_param(p, indent, out):
    what = {PRESET: 'preset', VARIABLE: 'variable', FUNCTION: 'function', LITERAL: 'literal'}.get(p.kind, 'unset')
    out.append('%s%s %r' % (indent, what, p.value))
    if p.function is not None:
        _dump(p.function, indent + '  > ', out)
    if p.index is not None:
        out.append(indent + '  [index]')
        _dump_param(p.index, indent + '    ', out)


def describe(match):
    if match.trigger is None:
        return 'no model: %s' % match.reason
    t = match.trigger
    out = ['trigger %r%s%s' % (t.name, ' (initially off)' if t.initially_off else '',
                               '\n  description %r' % t.description if t.description else '')]
    for f in t.functions:
        _dump(f, '  ', out)
    out.append('helpers: %s' % ', '.join(match.helpers))
    if match.external:
        out.append('external: %s' % ', '.join(match.external))
    out.append('custom script lines: %d' % match.custom_lines)
    return '\n'.join(out)
