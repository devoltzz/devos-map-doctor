# The item recipes a map script makes (the result, the ingredients with their ids and names, gold, lumber and level), from its triggers and the tables of the recipe libraries, written to a file.
import csv
import io
import json
import os
import re


REMOVE_CALLS = ('RemoveItem',)
CREATE_CALLS = {'UnitAddItemById': 1, 'UnitAddItemByIdSwapped': 0, 'UnitAddItemToSlotById': 1, 'CreateItem': 0,
                'CreateItemLoc': 0}
SLOT_CALLS = ('UnitItemInSlot', 'UnitItemInSlotBJ')
EFFECT_CALLS = frozenset(('RemoveItem', 'SetItemCharges', 'SetPlayerStateBJ', 'SetPlayerState', 'AdjustPlayerStateBJ',
                          'AdjustPlayerStateSimpleBJ') + tuple(CREATE_CALLS))
ITEM_OF_TYPE = ('GetItemOfTypeFromUnitBJ', 'YDWEGetItemOfTypeFromUnitBJNull')
RX_ITEM_OF_TYPE = re.compile(r'(?i)item_?of_?type|item_?by_?type|get_?item_?from_?type')
MANIPULATED = ('GetManipulatedItem', 'GetSoldItem', 'GetOrderTargetItem', 'GetSpellTargetItem')
GOLD, LUMBER = 'PLAYER_STATE_RESOURCE_GOLD', 'PLAYER_STATE_RESOURCE_LUMBER'
COMPARE = ('==', '!=', '<', '<=', '>', '>=')
FLIP = {'==': '==', '!=': '!=', '<': '>', '<=': '>=', '>': '<', '>=': '<='}
NEGATE = {'==': '!=', '!=': '==', '<': '>=', '<=': '>', '>': '<=', '>=': '<'}
MAX_DEPTH = 4
MAX_CALL_WALKS = 20000
MAX_FACT_WALKS = 400000
MAX_TURNS = 24
KINDS_SHOWN = ('recipe', 'upgrade')
EVENTS = {'EVENT_PLAYER_UNIT_PICKUP_ITEM': 'acquires an item', 'EVENT_UNIT_PICKUP_ITEM': 'acquires an item',
          'EVENT_PLAYER_UNIT_USE_ITEM': 'uses an item', 'EVENT_UNIT_USE_ITEM': 'uses an item',
          'EVENT_PLAYER_UNIT_DROP_ITEM': 'loses an item', 'EVENT_PLAYER_UNIT_SELL_ITEM': 'sells an item',
          'EVENT_PLAYER_UNIT_PAWN_ITEM': 'pawns an item', 'EVENT_PLAYER_UNIT_SPELL_EFFECT': 'casts a spell',
          'EVENT_PLAYER_UNIT_SPELL_CAST': 'casts a spell', 'EVENT_PLAYER_UNIT_ISSUED_TARGET_ORDER': 'is ordered',
          'EVENT_PLAYER_UNIT_ISSUED_ORDER': 'is ordered', 'EVENT_PLAYER_UNIT_ISSUED_POINT_ORDER': 'is ordered',
          'EVENT_PLAYER_UNIT_SPELL_ENDCAST': 'casts a spell', 'EVENT_PLAYER_UNIT_SPELL_CHANNEL': 'casts a spell'}

RX_RECIPE_NAME = re.compile(r'(?i)recipe|combin|craft|merge|mix|fusion|forge|synth|compose|assembl|upgrade|'
                            u'합성|조합|제작|강화|合成|配方')
RX_RESULT_STRONG = re.compile(r'(?i)^(result|res(ult)?_?(item|id|type)|product|end_?tem|end_?item|combined(_?item)?|'
                              r'output(_?item)?|crafted(_?item)?|final_?item|new_?item|made_?item|target_?item|'
                              r'item_?result|reward_?item)$')
RX_RESULT_WEAK = re.compile(r'(?i)^(res|new|out|target|reward|make|made|final|goal|r)$')
RX_INGREDIENT = re.compile(r'(?i)^(m|mat|mats|material|tem|item|itm|ing|ingredient|req|required|need|src|source|part|'
                           r'comp|component|piece|reagent|i|id|it)_?(\d+)$')
RX_COUNT = re.compile(r'(?i)^(n|c|cnt|count|num|amount|qty|charge|charges)_?(\d+)$')
RX_COUNT_OF = re.compile(r'(?i)^(.*?\d+)_?(char|chars|charge|charges|count|cnt|num|n|qty)$')
RX_GOLD = re.compile(r'(?i)^(g|gold|goldcost|gold_cost|cost|price)$')
RX_LUMBER = re.compile(r'(?i)^(l|lumber|wood|lumbercost|lumber_cost)$')
RX_CHANCE = re.compile(r'(?i)^(p|prob|chance|rate|percent)$')
RX_RESULT_COUNT = re.compile(r'(?i)^(rn|result_?count|result_?n|res_?n|amount)$')
BUILDERS = {'ItemCombine_NewF': {'new': 0},
            'ItemCombine_AddF': {'chain': 0, 'item': 1, 'count': 2},
            's__sjRecipe_Reg': {'new': 1, 'result_count': 2},
            's__sjRecipe_Add': {'chain': 0, 'item': 2, 'count': 3},
            's__sjRecipe_Gold': {'chain': 0, 'gold': 1},
            's__sjRecipe_Lumber': {'chain': 0, 'lumber': 1},
            's__sjRecipe_Prob': {'chain': 0, 'chance': 1}}
FORMULAS = {'YDWENewItemsFormula': (12, [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9), (10, 11)])}
STAGED = {'NewItemGroup': 0}


def id_of_int(v):
    b = (v & 0xFFFFFFFF).to_bytes(4, 'big')
    if b'\x00' in b:
        return None
    return b.decode('latin-1')


def id_text(ident):
    return ''.join(c if ' ' <= c <= '~' and c != '\\' else '\\x%02x' % ord(c) for c in ident)


UNK = ('?',)


class Func(object):
    __slots__ = ('name', 'params', 'body', 'line', 'types', 'returns')

    def __init__(self, name, params, body, line, types=None, returns=None):
        self.name, self.params, self.body, self.line = name, params, body, line
        self.types, self.returns = types, returns


def _fold(op, a, b):
    if a[0] == 'k' and b[0] == 'k' and a[2] in ('raw', 'int') and b[2] in ('raw', 'int'):
        if op == '+':
            return ('k', (a[1] + b[1]) & 0xFFFFFFFF, 'int')
        if op == '-':
            return ('k', (a[1] - b[1]) & 0xFFFFFFFF, 'int')
    return ('b', op, a, b)


def _neg(x):
    if x[0] == 'k' and x[2] in ('raw', 'int'):
        return ('k', (-x[1]) & 0xFFFFFFFF, 'int')
    if x[0] == 'k' and x[2] == 'real':
        return ('k', -x[1], 'real')
    return ('u', '-', x)


class _Jass(object):
    def __init__(self, J):
        self.J = J

    def expr(self, e):
        J = self.J
        t = type(e)
        if t is J.Paren:
            return self.expr(e.inner)
        if t is J.Literal:
            k = e.kind
            if k in ('rawcode', 'integer'):
                return ('k', e.value & 0xFFFFFFFF, 'raw' if k == 'rawcode' else 'int')
            if k == 'real':
                return ('k', e.value, 'real')
            if k == 'string':
                return ('k', e.value, 'str')
            if k == 'boolean':
                return ('k', e.value, 'bool')
            return ('k', None, 'null')
        if t is J.Name:
            return ('n', e.name)
        if t is J.Call:
            return ('c', e.name, [self.expr(a) for a in e.args])
        if t is J.Index:
            return ('i', e.base.name if hasattr(e.base, 'name') else str(e.base), self.expr(e.index))
        if t is J.Binary:
            return _fold(e.op, self.expr(e.left), self.expr(e.right))
        if t is J.Unary:
            x = self.expr(e.operand)
            if e.op == '-':
                return _neg(x)
            return x if e.op == '+' else ('u', e.op, x)
        if t is J.FuncRef:
            return ('f', e.name)
        return UNK

    def block(self, stmts):
        J = self.J
        out = []
        for s in stmts:
            t = type(s)
            if t is J.CallStmt:
                out.append(('call', s.line, self.expr(s.call)))
            elif t is J.SetStmt:
                out.append(('set', s.line, self.expr(s.target), self.expr(s.value)))
            elif t is J.IfStmt:
                out.append(('if', s.line, [(self.expr(c) if c is not None else None, self.block(b))
                                           for c, b in s.branches]))
            elif t is J.LoopStmt:
                out.append(('loop', s.line, self.block(s.body), None, None, None))
            elif t is J.ExitWhenStmt:
                out.append(('exit', s.line, self.expr(s.cond)))
            elif t is J.ReturnStmt:
                out.append(('ret', s.line, self.expr(s.value) if s.value is not None else None))
        return out

    def script(self, tree):
        funcs = {}
        for f in tree.functions:
            body = [('set', d.line, ('n', d.name), self.expr(d.initializer)) for d in f.locals
                    if d.initializer is not None and not d.is_array]
            body.extend(self.block(f.body))
            funcs.setdefault(f.name, Func(f.name, [p[1] for p in f.params], body, f.line, [p[0] for p in f.params],
                                          f.return_type))
        names = set(g.name for g in tree.globals)
        inits = dict((g.name, self.expr(g.initializer)) for g in tree.globals
                     if g.initializer is not None and not g.is_array)
        return funcs, constants(funcs, names, inits)


def constants(funcs, globals_, inits):
    sets = {}
    for f in funcs.values():
        for s in _all_stmts(f.body):
            if s[0] != 'set':
                continue
            t = s[2]
            if t[0] == 'n' and t[1] in globals_:
                sets.setdefault(t[1], []).append(s[3])
            elif t[0] == 'i' and t[1] in globals_:
                i = t[2]
                key = (
                    t[1] + '[' + _key(('k', i[1], 'int')) + ']'
                    if i[0] == 'k' and i[2] in ('int', 'raw')
                    else t[1] + '[?]'
                )
                sets.setdefault(key, []).append(s[3])
    out = {}
    for name, v in inits.items():
        if v[0] == 'k' and v[2] in ('raw', 'int') and name not in sets:
            out[name] = v
    for key, values in sets.items():
        if (
            len(values) == 1
            and values[0][0] == 'k'
            and values[0][2] in ('raw', 'int')
            and not key.endswith('[?]')
            and (key.split('[')[0] + '[?]') not in sets
            and (key in out or key not in inits)
        ):
            out[key] = values[0]
    return out


class _Lua(object):
    def __init__(self, L):
        self.L = L

    def name_of(self, e):
        L = self.L
        if type(e) is L.Name:
            return e.name
        if type(e) is L.Index and e.dot and type(e.key) is L.Literal:
            base = self.name_of(e.base)
            return base + '.' + str(e.key.value) if base else None
        return None

    def expr(self, e):
        L = self.L
        t = type(e)
        if t is L.Paren:
            return self.expr(e.inner)
        if t is L.Literal:
            if e.kind == 'number':
                if isinstance(e.value, int):
                    return ('k', e.value & 0xFFFFFFFF, 'int')
                return ('k', e.value, 'real')
            if e.kind == 'string':
                return ('k', e.value, 'str')
            if e.kind == 'boolean':
                return ('k', e.value, 'bool')
            return ('k', None, 'null')
        if t is L.Name:
            return ('n', e.name)
        if t is L.Call:
            name = self.name_of(e.func) if e.method is None else None
            args = [self.expr(a) for a in e.args]
            if name == 'FourCC' and len(args) == 1 and args[0][0] == 'k' and args[0][2] == 'str':
                b = args[0][1].encode('utf-8', 'surrogateescape')
                if len(b) == 4:
                    return ('k', int.from_bytes(b, 'big'), 'raw')
            return ('c', name or '?', args)
        if t is L.Index:
            n = self.name_of(e)
            if n:
                return ('n', n)
            base = self.name_of(e.base)
            return ('i', base, self.expr(e.key)) if base else UNK
        if t is L.Binary:
            return _fold('!=' if e.op == '~=' else e.op, self.expr(e.left), self.expr(e.right))
        if t is L.Unary:
            x = self.expr(e.operand)
            return _neg(x) if e.op == '-' else ('u', e.op, x)
        return UNK

    def block(self, stmts, funcs):
        L = self.L
        out = []
        for s in stmts:
            t = type(s)
            if t is L.CallStmt:
                out.append(('call', s.line, self.expr(s.call)))
            elif t is L.AssignStmt or t is L.LocalStmt:
                targets = s.targets if t is L.AssignStmt else [L.Name(n, s.line) for n in s.names]
                for k, target in enumerate(targets):
                    value = s.values[k] if k < len(s.values) else None
                    if type(value) is L.FunctionExpr:
                        name = self.name_of(target)
                        if name:
                            self.function(name, value.params, value.body, s.line, funcs)
                        continue
                    if value is not None:
                        out.append(('set', s.line, self.expr(target), self.expr(value)))
            elif t is L.FunctionStmt:
                self.function(s.name, s.params, s.body, s.line, funcs)
            elif t is L.IfStmt:
                out.append(('if', s.line, [(self.expr(c) if c is not None else None, self.block(b, funcs))
                                           for c, b in s.branches]))
            elif t is L.NumericForStmt:
                count, start = None, None
                a, b = self.expr(s.start), self.expr(s.stop)
                if a[0] == 'k' and b[0] == 'k' and a[2] == b[2] == 'int' and s.step is None:
                    n = b[1] - a[1] + 1
                    count, start = (n, a[1]) if 0 < n <= 64 else (None, None)
                var = s.var if isinstance(s.var, str) else getattr(s.var, 'name', None)
                out.append(('loop', s.line, self.block(s.body, funcs), count, var, start))
            elif t in (L.WhileStmt, L.GenericForStmt, L.RepeatStmt):
                out.append(('loop', s.line, self.block(s.body, funcs), None, None, None))
            elif t is L.DoStmt:
                out.extend(self.block(s.body, funcs))
            elif t is L.ReturnStmt:
                out.append(('ret', s.line, self.expr(s.values[0]) if s.values else None))
        return out

    def function(self, name, params, body, line, funcs):
        names = [p if isinstance(p, str) else getattr(p, 'name', str(p)) for p in params]
        funcs[name] = Func(name, names, self.block(body, funcs), line)

    def script(self, chunk):
        funcs = {}
        top = self.block(chunk.body, funcs)
        funcs.setdefault('<main>', Func('<main>', [], top, 1))
        return funcs, {}


def _all_stmts(body):
    stack = list(reversed(body))
    while stack:
        s = stack.pop()
        yield s
        if s[0] == 'if':
            for _c, b in reversed(s[2]):
                stack.extend(reversed(b))
        elif s[0] == 'loop':
            stack.extend(reversed(s[2]))


def _walk_expr(e):
    stack = [e]
    while stack:
        x = stack.pop()
        yield x
        k = x[0]
        if k == 'c':
            stack.extend(x[2])
        elif k == 'b':
            stack.append(x[3])
            stack.append(x[2])
        elif k in ('u', 'i'):
            stack.append(x[2])


def _key(e):
    return repr(e)


def _shape(e, depth=0):
    if e[0] == 'k':
        return e
    if e[0] == 'c' and depth < 6:
        return ('c', e[1], [_shape(a, depth + 1) for a in e[2]])
    return UNK


class Effects(object):
    __slots__ = ('removes', 'creates', 'gold', 'lumber', 'lines', 'facts', 'env')

    def __init__(self):
        self.removes, self.creates, self.gold, self.lumber, self.lines = {}, {}, 0, 0, []
        self.facts = self.env = None

    @staticmethod
    def add(table, t, n):
        if t in table:
            table[t] = None if table[t] is None or n is None else table[t] + n
        else:
            table[t] = n

    def merge(self, o, mult=1):
        for t, n in o.removes.items():
            self.add(self.removes, t, None if n is None or mult is None else n * mult)
        for t, n in o.creates.items():
            self.add(self.creates, t, None if n is None or mult is None else n * mult)
        self.gold += o.gold * (mult or 1)
        self.lumber += o.lumber * (mult or 1)
        self.lines.extend(o.lines)


class Facts(object):
    __slots__ = ('has', 'slots', 'manip', 'gold', 'lumber', 'level', 'any')

    def __init__(self):
        self.has, self.slots, self.manip = {}, {}, set()
        self.gold = self.lumber = self.level = 0
        self.any = False

    def copy(self):
        f = Facts()
        f.has, f.slots, f.manip = dict(self.has), dict(self.slots), set(self.manip)
        f.gold, f.lumber, f.level, f.any = self.gold, self.lumber, self.level, self.any
        return f

    def need(self, t, n=1):
        self.has[t] = max(self.has.get(t, 0), n)

    def update(self, o):
        for t, n in o.has.items():
            self.need(t, n)
        self.slots.update(o.slots)
        self.manip |= o.manip
        self.gold = max(self.gold, o.gold)
        self.lumber = max(self.lumber, o.lumber)
        self.level = max(self.level, o.level)
        self.any = self.any or o.any

    def items(self):
        return bool(self.has or self.slots or self.manip)

    def weak(self):
        if self.items():
            self.any = True
        self.gold = self.lumber = self.level = 0
        return self

    def types(self):
        return set(self.has) | set(self.slots.values()) | self.manip


def _resource(e):
    if e[0] == 'n' and e[1] in (GOLD, LUMBER):
        return 'gold' if e[1] == GOLD else 'lumber'
    return None


def _player_state(e):
    if e[0] == 'c' and e[1] == 'GetPlayerState' and len(e[2]) == 2:
        return _resource(e[2][1])
    return None


class Analysis(object):
    def __init__(self, funcs, consts, known_ids=None):
        self.funcs = funcs
        self.consts = consts
        self.known = known_ids
        self.sites = []
        self.others = {}
        self.walks = 0
        self.fact_walks = 0
        self._const_depth = 0
        self._unrolling = False
        self._call_memo = {}
        self._facts_memo = {}
        self._reads = {}
        self._returns_memo = {}
        self.triggers = {}
        self._bind_triggers()
        self._touch_memo = {}
        self.touches, self.makes = self._reach()

    def _reach(self):
        direct, makes, callees = set(), set(), {}
        for f in self.funcs.values():
            mine = callees[f.name] = set()
            for s in _all_stmts(f.body):
                if s[0] not in ('call', 'set'):
                    continue
                expr = s[2] if s[0] == 'call' else s[3]
                if s[0] == 'call' and expr[0] == 'c' and expr[1] in self.funcs and self.funcs[expr[1]].params:
                    mine.add(expr[1])
                for e in _walk_expr(expr):
                    if e[0] == 'c' and e[1] in EFFECT_CALLS:
                        direct.add(f.name)
                        if e[1] in CREATE_CALLS:
                            makes.add(f.name)
        touches = set(direct)
        changed = True
        while changed:
            changed = False
            for name, mine in callees.items():
                if name not in touches and mine & touches:
                    touches.add(name)
                    changed = True
                if name not in makes and mine & makes:
                    makes.add(name)
                    changed = True
        return touches, makes

    def body_touches(self, body):
        key = id(body)
        memo = self._touch_memo.get(key)
        if memo is None:
            memo = False
            for s in _all_stmts(body):
                if s[0] not in ('call', 'set'):
                    continue
                expr = s[2] if s[0] == 'call' else s[3]
                if s[0] == 'call' and expr[0] == 'c' and expr[1] in self.touches and self.funcs[expr[1]].params:
                    memo = True
                    break
                if any(e[0] == 'c' and e[1] in EFFECT_CALLS for e in _walk_expr(expr)):
                    memo = True
                    break
            self._touch_memo[key] = (body, memo)
        else:
            memo = memo[1]
        return memo

    def _fn_value(self, e):
        if e[0] in ('f', 'n') and e[1] in self.funcs:
            return e[1]
        return None

    def _bind_triggers(self):
        by_trigger = {}
        for f in self.funcs.values():
            for s in _all_stmts(f.body):
                if s[0] != 'call' or s[2][0] != 'c' or not s[2][2]:
                    continue
                name, args = s[2][1], s[2][2]
                if not (name.startswith('TriggerRegister') or name in ('TriggerAddAction', 'TriggerAddCondition')):
                    continue
                t = by_trigger.setdefault(_key(args[0]), {'conditions': [], 'actions': [], 'events': [],
                                                          'var': args[0]})
                if name == 'TriggerAddAction' and len(args) == 2:
                    fn = self._fn_value(args[1])
                    if fn:
                        t['actions'].append(fn)
                elif name == 'TriggerAddCondition' and len(args) == 2:
                    a = args[1]
                    if a[0] == 'c' and a[1] in ('Condition', 'Filter') and a[2]:
                        a = a[2][0]
                    fn = self._fn_value(a)
                    if fn:
                        t['conditions'].append(fn)
                else:
                    for a in args[1:]:
                        if a[0] == 'n' and a[1] in EVENTS and EVENTS[a[1]] not in t['events']:
                            t['events'].append(EVENTS[a[1]])
                    if name == 'TriggerRegisterPlayerChatEvent' and len(args) >= 3 and args[2][0] == 'k' \
                            and isinstance(args[2][1], str):
                        chat = 'types "%s"' % args[2][1]
                        if chat not in t['events']:
                            t['events'].append(chat)
        for t in by_trigger.values():
            var = t['var']
            label = var[1][7:] if var[0] == 'n' and var[1].startswith('gg_trg_') else None
            for a in t['actions']:
                info = self.triggers.setdefault(a, {'conditions': [], 'trigger': label, 'events': []})
                info['conditions'].extend(c for c in t['conditions'] if c not in info['conditions'])
                info['events'].extend(e for e in t['events'] if e not in info['events'])

    def index_key(self, name, index, env):
        c = self.const(index, env)
        return name + '[' + (_key(('k', c & 0xFFFFFFFF, 'int')) if c is not None else _key(self.value(index, env))) \
            + ']'

    def value(self, e, env):
        k = e[0]
        if k == 'n':
            v = env.get(e[1])
            if v is not None:
                return v
            return self.consts.get(e[1], e)
        if k == 'i':
            key = self.index_key(e[1], e[2], env)
            v = env.get(key)
            if v is not None:
                return v
            return self.consts.get(key, e)
        return e

    def settled(self, e, env, name):
        v = self.value(e, env)
        if v[0] == 'k':
            return v
        c = self.const(v, env)
        if c is not None:
            return ('k', c & 0xFFFFFFFF, 'int')
        for x in _walk_expr(v):
            if x[0] in ('n', 'i') and x[1] == name:
                return UNK
        return v

    def const(self, e, env, depth=0):
        if self._const_depth > 24:
            return None
        self._const_depth += 1
        try:
            e = self.value(e, env) if e[0] in ('n', 'i') else e
            if e[0] == 'k' and e[2] in ('int', 'raw'):
                return e[1] - 0x100000000 if e[1] >= 0x80000000 else e[1]
            if e[0] == 'b' and e[1] in ('+', '-', '*') and depth < 8:
                a = self.const(e[2], env, depth + 1)
                b = self.const(e[3], env, depth + 1) if a is not None else None
                if b is not None:
                    return a + b if e[1] == '+' else a - b if e[1] == '-' else a * b
            return None
        finally:
            self._const_depth -= 1

    def item_id(self, e, env):
        e = self.value(e, env)
        if e[0] == 'b':
            c = self.const(e, env)
            e = ('k', c & 0xFFFFFFFF, 'int') if c is not None else e
        if e[0] == 'k' and e[2] in ('raw', 'int'):
            ident = id_of_int(e[1])
            if ident is None:
                return None
            if e[2] == 'int' and (self.known is None or ident not in self.known):
                return None
            return ident
        return None

    def number(self, e, env):
        e = self.value(e, env)
        if e[0] == 'k' and e[2] == 'real' and isinstance(e[1], (int, float)):
            return e[1]
        return self.const(e, env)

    def item_of(self, e, env, facts, depth=0):
        e = self.value(e, env)
        if e[0] != 'c':
            return None
        name, args = e[1], e[2]
        if name in ITEM_OF_TYPE and len(args) == 2:
            return self.item_id(args[1], env)
        if name in MANIPULATED:
            return next(iter(facts.manip)) if len(facts.manip) == 1 else None
        if name in SLOT_CALLS and len(args) == 2:
            return facts.slots.get(self.index_key('', args[1], env))
        f = self.funcs.get(name)
        if f is not None and f.params and depth < 2:
            r = self.returns_item(f)
            if isinstance(r, int):
                return self.item_id(args[r], env) if r < len(args) else None
            return r
        return None

    def returns_item(self, f):
        if f.name in self._returns_memo:
            return self._returns_memo[f.name]
        self._returns_memo[f.name] = None
        r = None
        if (
            RX_ITEM_OF_TYPE.search(f.name)
            and f.types
            and f.returns == 'item'
            and 'unit' in f.types
            and f.types.count('integer') == 1
        ):
            r = f.types.index('integer')
        else:
            marks = [('k', 0x01010100 + i, 'int') for i in range(len(f.params))]
            env = self.bind(f, marks, {})
            found = set()
            for s in _all_stmts(f.body):
                if s[0] == 'ret' and s[2] is not None:
                    e = self.value(s[2], env)
                    if e[0] == 'k' and e[2] == 'null':
                        continue
                    if e[0] == 'c' and e[1] in ITEM_OF_TYPE and len(e[2]) == 2:
                        v = self.value(e[2][1], env)
                        found.add(marks.index(v) if v in marks else self.item_id(v, env))
                    else:
                        found.add(None)
            r = found.pop() if len(found) == 1 else None
        self._returns_memo[f.name] = r
        return r

    def bind(self, f, args, env):
        out = dict((k, v) for k, v in env.items() if k.split('[', 1)[0] not in f.params) if env else {}
        for i, p in enumerate(f.params):
            out[p] = args[i] if i < len(args) else UNK
        return out

    def facts(self, cond, env, out, depth=0, negated=False):
        if cond is None or depth > 12:
            return
        k = cond[0]
        if k == 'u' and cond[1] == 'not':
            return self.facts(cond[2], env, out, depth + 1, not negated)
        if k == 'b' and cond[1] in ('and', 'or'):
            if (cond[1] == 'and') != negated:
                self.facts(cond[2], env, out, depth + 1, negated)
                self.facts(cond[3], env, out, depth + 1, negated)
            else:
                sub = Facts()
                self.facts(cond[2], env, sub, depth + 1, negated)
                self.facts(cond[3], env, sub, depth + 1, negated)
                out.update(sub.weak())
            return
        if k == 'b' and cond[1] in COMPARE:
            op, a, b = (NEGATE[cond[1]] if negated else cond[1]), cond[2], cond[3]
            for x, y in ((a, b), (b, a)):
                y = self.value(y, env)
                if y[0] == 'k' and y[2] == 'bool' and op in ('==', '!='):
                    holds = (op == '==') == bool(y[1])
                    return self.facts(x, env, out, depth + 1, not holds)
            return self._compare(op, a, b, env, out, depth)
        if negated or k != 'c':
            return
        name, args = cond[1], cond[2]
        if name == 'UnitHasItemOfTypeBJ' and len(args) == 2:
            t = self.item_id(args[1], env)
            if t is not None:
                out.need(t)
            return
        if name == 'UnitHasItem' and len(args) == 2:
            t = self.item_of(args[1], env, out)
            if t is not None:
                out.need(t)
            return
        f = self.funcs.get(name)
        if f is not None and depth < 10:
            out.update(self.call_facts(f, [self.value(a, env) for a in args], env, depth + 1))

    def _compare(self, op, a, b, env, out, depth):
        if self.number(a, env) is not None and self.number(b, env) is None:
            a, b, op = b, a, FLIP[op]
        for x, y in ((a, b), (b, a)):
            xv = self.value(x, env)
            if op == '==' and xv[0] == 'c' and xv[1] == 'GetItemTypeId' and len(xv[2]) == 1:
                t = self.item_id(y, env)
                if t is None:
                    continue
                item = self.value(xv[2][0], env)
                if item[0] == 'c' and item[1] in MANIPULATED:
                    out.manip.add(t)
                elif item[0] == 'c' and item[1] in SLOT_CALLS and len(item[2]) == 2:
                    out.slots[self.index_key('', item[2][1], env)] = t
                else:
                    out.need(t)
                return
            if op == '!=' and xv[0] == 'c' and xv[1] in ITEM_OF_TYPE and len(xv[2]) == 2:
                yv = self.value(y, env)
                if yv[0] == 'k' and yv[2] == 'null':
                    t = self.item_id(xv[2][1], env)
                    if t is not None:
                        out.need(t)
                    return
        if op not in ('>', '>=', '=='):
            return
        n = self.number(b, env)
        if n is None:
            return
        n = int(n) + (1 if op == '>' else 0)
        av = self.value(a, env)
        res = _player_state(av)
        if res:
            setattr(out, res, max(getattr(out, res), n))
        elif av[0] == 'c' and av[1] in ('GetHeroLevel', 'GetUnitLevel'):
            out.level = max(out.level, n)
        elif av[0] == 'c' and av[1] == 'GetItemCharges' and len(av[2]) == 1 and n >= 1:
            t = self.item_of(av[2][0], env, out)
            if t is not None:
                out.need(t, n)
        elif av[0] == 'c' and av[1] == 'GetInventoryIndexOfItemTypeBJ' and len(av[2]) == 2 and n >= 1:
            t = self.item_id(av[2][1], env)
            if t is not None:
                out.need(t)
        elif av[0] == 'c' and av[1] in self.funcs and n >= 1 and depth < 10:
            bound = self.call_facts(self.funcs[av[1]], [self.value(x, env) for x in av[2]], env, depth + 1)
            types = bound.types()
            if len(types) == 1:
                out.need(types.pop(), n)

    def call_facts(self, f, vals, env, depth=0):
        reads = self.reads(f)
        key = None
        if reads is not None:
            seen = tuple(sorted((k, _key(v)) for k, v in env.items() if k.split('[', 1)[0] in reads)) if env else ()
            key = (f.name, _key(vals), seen)
            memo = self._facts_memo.get(key)
            if memo is not None:
                return memo
        out = Facts()
        if depth > 10 or self.fact_walks >= MAX_FACT_WALKS:
            return out
        self.fact_walks += 1
        self._body_facts(f.body, self.bind(f, vals, env), out, depth)
        if key is not None:
            self._facts_memo[key] = out
        return out

    def reads(self, f):
        memo = self._reads.get(f.name, False)
        if memo is not False:
            return memo
        names, seen, stack = set(), set(), [f.name]
        while stack and len(seen) <= 200:
            g = self.funcs.get(stack.pop())
            if g is None or g.name in seen:
                continue
            seen.add(g.name)
            for st in _all_stmts(g.body):
                for x in st[2:]:
                    if not isinstance(x, tuple) or not x or not isinstance(x[0], str):
                        continue
                    for e in _walk_expr(x):
                        if e[0] in ('n', 'i'):
                            names.add(e[1])
                        elif e[0] in ('c', 'f') and e[1] in self.funcs:
                            stack.append(e[1])
                if st[0] == 'if':
                    for cond, _b in st[2]:
                        if cond is not None:
                            for e in _walk_expr(cond):
                                if e[0] in ('n', 'i'):
                                    names.add(e[1])
                                elif e[0] in ('c', 'f') and e[1] in self.funcs:
                                    stack.append(e[1])
        r = frozenset(names) if not stack else None
        self._reads[f.name] = r
        return r

    def _body_facts(self, body, env, out, depth):
        env = dict(env)
        for s in body:
            if s[0] == 'set' and s[2][0] == 'n':
                env[s[2][1]] = self.settled(s[3], env, s[2][1])
            elif s[0] == 'if':
                for cond, b in s[2]:
                    if cond is None:
                        continue
                    r = b[0][2] if len(b) == 1 and b[0][0] == 'ret' else None
                    rv = self.value(r, env) if r is not None else None
                    if rv is not None and rv[0] == 'k' and rv[2] == 'bool' and rv[1] is False:
                        self.facts(cond, env, out, depth + 1, negated=True)
                        continue
                    holds = self.truth(cond, env)
                    if holds:
                        self._body_facts(b, env, out, depth + 1)
                    elif holds is None:
                        sub = Facts()
                        self.facts(cond, env, sub, depth + 1)
                        if depth < 10:
                            self._body_facts(b, env, sub, depth + 1)
                        out.update(sub.weak())
            elif s[0] == 'ret' and s[2] is not None:
                rv = self.value(s[2], env)
                if rv[0] != 'k':
                    self.facts(rv, env, out, depth + 1)
            elif s[0] == 'loop':
                self._body_facts(s[2], env, out, depth)

    def stmt_effects(self, s, env, facts, eff, depth):
        expr = s[2] if s[0] == 'call' else s[3]
        for e in _walk_expr(expr):
            if e[0] != 'c':
                continue
            name, args = e[1], e[2]
            if name in REMOVE_CALLS and len(args) == 1:
                t = self.item_of(args[0], env, facts)
                if t is not None:
                    eff.add(eff.removes, t, 1)
                    eff.lines.append(s[1])
            elif name in CREATE_CALLS and len(args) > CREATE_CALLS[name]:
                t = self.item_id(args[CREATE_CALLS[name]], env)
                if t is not None:
                    eff.add(eff.creates, t, 1)
                    eff.lines.append(s[1])
            elif name == 'SetItemCharges' and len(args) == 2:
                v = args[1]
                if v[0] == 'b' and v[1] == '-' and v[2][0] == 'c' and v[2][1] == 'GetItemCharges':
                    n = self.number(v[3], env)
                    t = self.item_of(args[0], env, facts)
                    if t is not None and n is not None and n > 0:
                        eff.add(eff.removes, t, int(n))
                        eff.lines.append(s[1])
            elif name in ('SetPlayerStateBJ', 'SetPlayerState') and len(args) == 3:
                res, v = _resource(args[1]), args[2]
                if res and v[0] == 'b' and v[1] == '-' and _player_state(v[2]) == res:
                    n = self.number(v[3], env)
                    if n is not None and n > 0:
                        setattr(eff, res, getattr(eff, res) + int(n))
            elif name in ('AdjustPlayerStateBJ', 'AdjustPlayerStateSimpleBJ') and len(args) == 3:
                amount, res = (args[0], _resource(args[2])) if name == 'AdjustPlayerStateBJ' else \
                    (args[2], _resource(args[1]))
                n = self.number(amount, env)
                if res and n is not None and n < 0:
                    setattr(eff, res, getattr(eff, res) - int(n))
            elif e is expr and s[0] == 'call' and depth < MAX_DEPTH and name in self.touches:
                f = self.funcs.get(name)
                if f is not None and f.params:
                    eff.merge(self.call_effects(f, [self.value(a, env) for a in args], depth + 1, s[1]))

    def call_effects(self, f, vals, depth, line):
        key = (f.name, _key([_shape(v) for v in vals]))
        memo = self._call_memo.get(key)
        if memo is not None:
            return memo
        if self.walks >= MAX_CALL_WALKS:
            return Effects()
        self.walks += 1
        self._call_memo[key] = Effects()
        info = {'function': f.name, 'line': f.line, 'via_line': line}
        eff = self.block(f.body, self.bind(f, vals, {}), Facts(), depth, info)
        self._call_memo[key] = eff
        return eff

    def loop(self, s, env, facts, depth, info):
        body, count, var, start = s[2], s[3], s[4], s[5]
        turns = None
        if self._unrolling or not self.body_touches(body):
            pass
        elif count and var and count <= MAX_TURNS:
            turns = []
            env1 = dict(env)
            self._unrolling = True
            try:
                for k in range(count):
                    env1[var] = ('k', (start + k) & 0xFFFFFFFF, 'int')
                    turns.append(self.block(body, env1, facts, depth, info))
            finally:
                self._unrolling = False
        elif body and body[0][0] == 'exit':
            turns = []
            env1 = dict(env)
            self._unrolling = True
            try:
                for _ in range(MAX_TURNS + 1):
                    stop = self.truth(body[0][2], env1)
                    if stop is None:
                        turns = None
                        break
                    if stop:
                        break
                    be = self.block(body[1:], env1, facts, depth, info)
                    turns.append(be)
                    env1 = be.env
                else:
                    turns = None
            finally:
                self._unrolling = False
        out = Effects()
        if turns is None:
            out.merge(self.block(body, env, facts, depth, info), None)
            return out
        seen = {}
        for be in turns:
            out.merge(be)
            for t in be.removes:
                seen[t] = seen.get(t, 0) + 1
        for t, n in seen.items():
            if n > 1:
                out.removes[t] = None
        return out

    def truth(self, cond, env):
        if cond[0] != 'b' or cond[1] not in COMPARE:
            return None
        a, b = self.const(cond[2], env), self.const(cond[3], env)
        if a is None or b is None:
            return None
        return {'==': a == b, '!=': a != b, '<': a < b, '<=': a <= b, '>': a > b, '>=': a >= b}[cond[1]]

    def block(self, body, env, facts, depth, info):
        eff = Effects()
        facts = facts.copy()
        env = dict(env)
        for s in body:
            k = s[0]
            if k == 'set':
                self.stmt_effects(s, env, facts, eff, depth)
                target = s[2]
                if target[0] == 'n':
                    env[target[1]] = self.settled(s[3], env, target[1])
                elif target[0] == 'i':
                    env[self.index_key(target[1], target[2], env)] = self.settled(s[3], env, target[1])
            elif k == 'call':
                self.stmt_effects(s, env, facts, eff, depth)
            elif k == 'loop':
                eff.merge(self.loop(s, env, facts, depth, info))
            elif k == 'exit':
                continue
            elif k == 'if':
                branches = s[2]
                last = branches[0][1][-1] if branches[0][1] else None
                if len(branches) == 1 and last is not None and last[0] == 'ret' and \
                        not any(x[0] == 'call' for x in branches[0][1][:-1]):
                    self.facts(branches[0][0], env, facts, negated=True)
                    continue
                made, open_before, certain, closed = [], False, None, branches[-1][0] is None
                for cond, b in branches:
                    holds = self.truth(cond, env) if cond is not None else True
                    if holds is False:
                        continue
                    if holds is True and not open_before:
                        certain = b
                        break
                    open_before = True
                    sub, own = facts.copy(), Facts()
                    if cond is not None:
                        self.facts(cond, env, own)
                        sub.update(own)
                    be = self.block(b, env, sub, depth, info)
                    made.append(be)
                    self.site(be, be.facts, dict(info, line=s[1]))
                    if cond is not None and own.items() and not be.creates and be.removes:
                        for t, n in be.removes.items():
                            eff.add(eff.removes, t, None if own.slots else n)
                        eff.lines.extend(be.lines)
                    if holds is True:
                        closed = True
                        break
                if certain is not None:
                    be = self.block(certain, env, facts, depth, info)
                    eff.merge(be)
                    env, facts = be.env, be.facts
                elif closed and made:
                    common = set(made[0].creates)
                    for be in made[1:]:
                        common &= set(be.creates)
                    for t in common:
                        eff.add(eff.creates, t, min(be.creates[t] or 1 for be in made))
        eff.facts = facts
        eff.env = env
        return eff

    def site(self, eff, facts, info):
        if eff.creates and eff.removes:
            self.sites.append((eff, facts, info))

    def run(self):
        for f in list(self.funcs.values()):
            if f.params or f.name not in self.makes:
                continue
            facts = Facts()
            info = {'function': f.name, 'line': f.line}
            t = self.triggers.get(f.name)
            if t:
                info['trigger'] = t['trigger']
                info['events'] = t['events']
                for c in t['conditions']:
                    facts.update(self.call_facts(self.funcs[c], [], {}))
            eff = self.block(f.body, {}, facts, 0, info)
            self.site(eff, eff.facts, info)
        return self.sites


class Registrations(object):
    def __init__(self, an):
        self.an = an
        self.found = []
        self._roles = {}

    def roles(self, f):
        if f.name in self._roles:
            return self._roles[f.name]
        names = f.params
        result = [i for i, p in enumerate(names) if RX_RESULT_STRONG.match(p)]
        if not result and RX_RECIPE_NAME.search(f.name):
            result = [i for i, p in enumerate(names) if RX_RESULT_WEAK.match(p)]
        roles = None
        if len(result) == 1:
            roles = {result[0]: ('result', None)}
            ingredients = {}
            for i, p in enumerate(names):
                m = RX_INGREDIENT.match(p)
                if m and i not in roles:
                    roles[i] = ('item', None)
                    ingredients[p.lower()] = i
                    ingredients.setdefault(m.group(2), i)
            if not ingredients:
                roles = None
            else:
                for i, p in enumerate(names):
                    if i in roles:
                        continue
                    m = RX_COUNT_OF.match(p)
                    if m and m.group(1).lower() in ingredients:
                        roles[i] = ('count', ingredients[m.group(1).lower()])
                        continue
                    m = RX_COUNT.match(p)
                    if m and m.group(2) in ingredients:
                        roles[i] = ('count', ingredients[m.group(2)])
                    elif RX_GOLD.match(p):
                        roles[i] = ('gold', None)
                    elif RX_LUMBER.match(p):
                        roles[i] = ('lumber', None)
                    elif RX_CHANCE.match(p):
                        roles[i] = ('chance', None)
                    elif RX_RESULT_COUNT.match(p):
                        roles[i] = ('result_count', None)
        self._roles[f.name] = roles
        return roles

    def run(self):
        an = self.an
        for f in an.funcs.values():
            staged = {}
            for s in _all_stmts(f.body):
                if s[0] == 'set' and s[2][0] == 'i':
                    idx = an.number(s[2][2], {})
                    t = an.item_id(s[3], {})
                    if isinstance(idx, int) and t is not None:
                        staged.setdefault(s[2][1], {})[idx] = (t, s[1])
                    continue
                if s[0] != 'call' or s[2][0] != 'c':
                    continue
                name, args = s[2][1], s[2][2]
                commit = name if not args else (args[0][1] if name == 'ExecuteFunc' and args and args[0][0] == 'k'
                                                 else None)
                if commit in STAGED and staged:
                    self.commit(staged, STAGED[commit], f, s[1], commit)
                    staged = {}
                    continue
                self.call(s[2], f, s[1])

    def commit(self, staged, result_index, f, line, via):
        for _array, table in staged.items():
            if result_index not in table or len(table) < 2:
                continue
            results = {table[result_index][0]: 1}
            ingredients = {}
            for i, (t, _l) in sorted(table.items()):
                if i != result_index:
                    Effects.add(ingredients, t, 1)
            self.found.append((results, ingredients, {}, {'function': f.name, 'line': line, 'via': via}))

    def call(self, e, f, line):
        an = self.an
        name, args = e[1], e[2]
        if name in FORMULAS:
            res_i, pairs = FORMULAS[name]
            t = an.item_id(args[res_i], {}) if res_i < len(args) else None
            ingredients = {}
            for i, c in pairs:
                n = an.number(args[c], {}) if c < len(args) else None
                it = an.item_id(args[i], {}) if i < len(args) else None
                if it is not None and n and n > 0:
                    Effects.add(ingredients, it, int(n))
            if t is not None and ingredients:
                self.found.append(({t: 1}, ingredients, {}, {'function': f.name, 'line': line, 'via': name}))
            return
        if name in BUILDERS:
            rec = self.chain(e)
            if rec and rec[0] and rec[1]:
                self.found.append((rec[0], rec[1], rec[2], {'function': f.name, 'line': line, 'via': name}))
            return
        g = an.funcs.get(name)
        if g is None or not g.params or len(args) < 2:
            return
        roles = self.roles(g)
        if not roles:
            return
        results, ingredients, extra = {}, {}, {}
        counts = dict((pair, i) for i, (role, pair) in roles.items() if role == 'count')
        for i, (role, pair) in roles.items():
            if i >= len(args):
                continue
            if role == 'result':
                t = an.item_id(args[i], {})
                if t is not None:
                    results[t] = 1
            elif role == 'item':
                t = an.item_id(args[i], {})
                if t is None:
                    continue
                n = an.number(args[counts[i]], {}) if i in counts and counts[i] < len(args) else None
                Effects.add(ingredients, t, int(n) if n and n > 0 else 1)
            elif role in ('gold', 'lumber', 'chance'):
                n = an.number(args[i], {})
                if n:
                    extra[role] = n
            elif role == 'result_count':
                n = an.number(args[i], {})
                if n and n > 1:
                    extra['result_count'] = int(n)
        if results and ingredients:
            if extra.get('result_count'):
                results = dict((t, extra['result_count']) for t in results)
            self.found.append((results, ingredients, extra, {'function': f.name, 'line': line, 'via': name}))

    def chain(self, e, depth=0):
        if depth > 40 or e[0] != 'c' or e[1] not in BUILDERS:
            return None
        an = self.an
        spec, args = BUILDERS[e[1]], e[2]
        if 'new' in spec:
            if spec['new'] >= len(args):
                return None
            t = an.item_id(args[spec['new']], {})
            if t is None:
                return None
            n = an.number(args[spec['result_count']], {}) if 'result_count' in spec and \
                spec['result_count'] < len(args) else None
            return ({t: int(n) if n and n > 1 else 1}, {}, {})
        if spec.get('chain', 0) >= len(args):
            return None
        inner = self.chain(args[spec['chain']], depth + 1)
        if inner is None:
            return None
        results, ingredients, extra = inner
        if 'item' in spec and spec['item'] < len(args):
            t = an.item_id(args[spec['item']], {})
            if t is None:
                return None
            n = an.number(args[spec['count']], {}) if 'count' in spec and spec['count'] < len(args) else None
            Effects.add(ingredients, t, int(n) if n and n > 0 else 1)
        for role in ('gold', 'lumber', 'chance'):
            if role in spec and spec[role] < len(args):
                n = an.number(args[spec[role]], {})
                if n:
                    extra[role] = n
        return results, ingredients, extra


def _item(t, n, names):
    return {'id': t, 'id_text': id_text(t), 'name': names.get(t), 'count': n}


def _source(info):
    out = {'function': info.get('function'), 'line': info.get('line')}
    if info.get('trigger'):
        out['trigger'] = info['trigger']
    if info.get('events'):
        out['events'] = list(info['events'])
    if info.get('via'):
        out['via'] = info['via']
    if info.get('via_line'):
        out['call_line'] = info['via_line']
    return out


def _kind(ingredients, kept, gold, lumber, results):
    if len(results) > 1:
        return 'several'
    units = sum(n if n else 2 for n in ingredients.values())
    if len(ingredients) >= 2 or units >= 2:
        return 'recipe'
    if gold or lumber or kept:
        return 'upgrade'
    return 'exchange'


def recipes_of(sites, regs, names, others, all_kinds=False):
    out, seen = [], {}

    def add(results, ingredients, kept, extra, info, pattern, checked):
        kind = _kind(ingredients, kept, extra.get('gold'), extra.get('lumber'), results)
        if kind not in KINDS_SHOWN and not all_kinds:
            others['left out: ' + {'exchange': 'one item for another, nothing else',
                                   'several': 'the block makes several different items'}[kind]] = \
                others.get('left out: ' + {'exchange': 'one item for another, nothing else',
                                           'several': 'the block makes several different items'}[kind], 0) + 1
            return
        key = (tuple(sorted(results.items(), key=str)), tuple(sorted(ingredients.items(), key=str)),
               tuple(sorted(kept.items(), key=str)), extra.get('gold') or 0, extra.get('lumber') or 0,
               extra.get('level') or 0)
        src = _source(info)
        if key in seen:
            r = seen[key]
            if src not in r['sources']:
                r['sources'].append(src)
            for it in r['ingredients']:
                it['checked'] = it['checked'] or it['id'] in checked
            return
        r = {'results': [_item(t, n, names) for t, n in sorted(results.items())],
             'ingredients': [dict(_item(t, n, names), checked=t in checked) for t, n in sorted(ingredients.items())],
             'kept': [_item(t, n, names) for t, n in sorted(kept.items())],
             'gold': int(extra.get('gold') or 0), 'lumber': int(extra.get('lumber') or 0),
             'level': int(extra.get('level') or 0), 'chance': extra.get('chance'), 'kind': kind, 'pattern': pattern,
             'sources': [src]}
        seen[key] = r
        out.append(r)

    for eff, facts, info in sites:
        removes, creates = dict(eff.removes), dict(eff.creates)
        for t in removes:
            asked = facts.has.get(t, 0)
            if asked and (removes[t] is None or asked > removes[t]):
                removes[t] = asked
        for t in set(removes) & set(creates):
            r, c = removes[t], creates[t]
            if r is not None and c is not None and r > c:
                removes[t] = r - c
                del creates[t]
            elif r is not None and c is not None and c > r:
                creates[t] = c - r
                del removes[t]
            else:
                del removes[t], creates[t]
        results, ingredients = creates, removes
        if not results or not ingredients:
            why = 'left out: the block makes the type it takes'
            others[why] = others.get(why, 0) + 1
            continue
        tested = facts.types()
        kept = dict((t, n) for t, n in facts.has.items() if t not in ingredients and t not in results
                    and not facts.any)
        extra = {'gold': max(eff.gold, facts.gold), 'lumber': max(eff.lumber, facts.lumber), 'level': facts.level}
        add(results, ingredients, kept, extra, info, 'trigger', tested)
    for results, ingredients, extra, info in regs:
        results = dict((t, n) for t, n in results.items() if t not in ingredients)
        if not results:
            continue
        add(results, ingredients, {}, extra, info, 'registration', set(ingredients))
    out.sort(key=lambda r: (r['sources'][0].get('line') or 0, r['results'][0]['id']))
    return out


def parse_script(text, language):
    if language == 'lua':
        from doctor.script import lua_ast
        return _Lua(lua_ast).script(lua_ast.parse(text))
    from doctor.script import jass_ast
    return _Jass(jass_ast).script(jass_ast.parse(text, vjass=True))


def find_text(text, language='jass', names=None, known_ids=None, all_kinds=False):
    names = names or {}
    funcs, consts = parse_script(text, language)
    an = Analysis(funcs, consts, known_ids if known_ids is not None else (set(names) or None))
    sites = an.run()
    reg = Registrations(an)
    reg.run()
    others = dict(an.others)
    recipes = recipes_of(sites, reg.found, names, others, all_kinds)
    for x in recipes:
        x['line'] = line_of(x)
        x['where'] = where_of(x)
    counts, kinds = {}, {}
    for r in recipes:
        counts[r['pattern']] = counts.get(r['pattern'], 0) + 1
        kinds[r['kind']] = kinds.get(r['kind'], 0) + 1
    return {'recipes': recipes, 'counts': counts, 'kinds': kinds, 'others': others, 'language': language,
            'functions': len(funcs), 'note': '', 'error': None}


def _nothing(*_a):
    pass


def find(path, progress=None, game_names=True, all_kinds=False):
    p = progress or _nothing
    out = {'map': os.path.abspath(path), 'recipes': [], 'counts': {}, 'kinds': {}, 'others': {}, 'language': None,
           'note': '', 'error': None}
    try:
        p('Reading the script')
        names, read = {}, None
        low = path.lower()
        if low.endswith(('.j', '.lua', '.txt')):
            with open(path, 'rb') as fh:
                data = fh.read()
            language = 'lua' if low.endswith('.lua') or (low.endswith('.txt') and b'function ' in data[:4096]
                                                          and b'endfunction' not in data) else 'jass'
            note = ''
        else:
            from doctor.fix import unprotect
            from doctor.viewers import map_files
            a, notes = map_files._open(path)
            language, _name, data, note, _compiled = map_files._script_file(a)
            note = ' '.join(list(notes) + [note]).strip()

            def read(name):
                return unprotect._read(a, name)
        out['language'], out['note'] = language, note
        if language not in ('jass', 'lua') or not data:
            out['error'] = note or 'The map has no script to read.'
            return out
        if read is not None or game_names:
            p('Reading the object names')
            from doctor.data import object_names
            try:
                names = object_names.names(read or (lambda _n: None), game=game_names)
            except Exception:
                names = {}
        p('Looking for the recipes')
        text = data.decode('utf-8', 'surrogateescape')
        if text[:1] == '﻿':
            text = text[1:]
        r = find_text(text, language, names, set(names) or None, all_kinds)
        r.update(map=out['map'], note=note)
        return r
    except (Exception, SystemExit) as e:
        out['error'] = '%s: %s' % (type(e).__name__, e)
        return out


def _label(it):
    name = it.get('name') or '?'
    return '%s (%s)' % (name, it['id_text'])


def _amount(it):
    n = it.get('count')
    if n is None:
        return 'all of '
    return '%dx ' % n if n > 1 else ''


def line_of(r):
    left = ' + '.join(_amount(it) + _label(it) for it in r['results'])
    right = ' + '.join(_amount(it) + _label(it) + ('' if it['checked'] else ' [not tested]')
                       for it in r['ingredients'])
    extra = []
    if r['gold']:
        extra.append('+ %d gold' % r['gold'])
    if r['lumber']:
        extra.append('+ %d lumber' % r['lumber'])
    needs = ['%s%s kept' % (_amount(it), _label(it)) for it in r['kept']]
    if r['level']:
        needs.append('level %d' % r['level'])
    if needs:
        extra.append('needs ' + ', '.join(needs))
    if r.get('chance') and r['chance'] != 100:
        extra.append('%s%% chance' % ('%g' % r['chance']))
    return '%s = %s%s' % (left, right, ''.join(' [%s]' % x for x in extra))


def _where(src):
    parts = []
    if src.get('trigger'):
        parts.append('trigger %s' % src['trigger'])
    if src.get('function') and not src.get('trigger'):
        parts.append(src['function'])
    if src.get('via'):
        parts.append('via %s' % src['via'])
    if src.get('line'):
        parts.append('line %d' % (src.get('call_line') or src['line']))
    if src.get('events'):
        parts.append('when a unit ' + ' / '.join(src['events']))
    return ', '.join(parts)


def where_of(x, most=4):
    src = x['sources']
    return '; '.join(_where(s) for s in src[:most]) + (' (and %d more)' % (len(src) - most) if len(src) > most else '')


def text(r):
    out = ["Recipes of %s" % os.path.basename(r.get('map') or 'the script'),
           "Devo's Map Doctor, found in the map script (%s)." % (r.get('language') or '?')]
    if r.get('error'):
        out.append(r['error'])
        return '\n'.join(out) + '\n'
    recipes = r.get('recipes') or []
    out.append('%d recipe%s' % (len(recipes), '' if len(recipes) == 1 else 's'))
    out.append('')
    for x in recipes:
        out.append(line_of(x))
        out.append('    ' + where_of(x))
    if r.get('others'):
        out.append('')
        out.append('Not listed:')
        for why, n in sorted(r['others'].items()):
            out.append('  %d %s' % (n, why))
    return '\n'.join(out) + '\n'


def csv_text(r):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator='\n')
    w.writerow(['result_id', 'result_name', 'result_count', 'ingredients', 'ingredient_names', 'gold', 'lumber',
                'level', 'kept', 'chance', 'kind', 'pattern', 'where'])
    for x in r.get('recipes') or []:
        res = x['results'][0]
        w.writerow([' + '.join(it['id_text'] for it in x['results']),
                    ' + '.join(it.get('name') or '' for it in x['results']),
                    res['count'] if res['count'] is not None else '',
                    '; '.join('%s x %s' % (it['id_text'], it['count'] if it['count'] is not None else 'all')
                              for it in x['ingredients']),
                    '; '.join(it.get('name') or '' for it in x['ingredients']),
                    x['gold'] or '', x['lumber'] or '', x['level'] or '',
                    '; '.join(it['id_text'] for it in x['kept']), x.get('chance') or '', x['kind'], x['pattern'],
                    ' | '.join(_where(s) for s in x['sources'])])
    return buf.getvalue()


def json_text(r):
    keep = dict((k, r.get(k)) for k in ('map', 'language', 'counts', 'kinds', 'others', 'note', 'error'))
    keep['recipes'] = r.get('recipes') or []
    return json.dumps(keep, ensure_ascii=False, indent=1) + '\n'


def file_text(r, path):
    low = path.lower()
    if low.endswith('.json'):
        return json_text(r)
    if low.endswith('.csv'):
        return csv_text(r)
    return text(r)


def write(r, path):
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(file_text(r, path))
    return os.path.abspath(path)
