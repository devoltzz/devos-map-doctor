# Finds and removes the lock that ends the game when a map is played alone.
import bisect
import collections
import os
import re
import shutil
import tempfile

from doctor.fix import unprotect
from doctor.script import jass_ast
from doctor.script import lua_ast
from doctor.mpq import mpqadd
from doctor.mpq import mpqdoctor
from doctor.data import object_names

HERE = os.path.dirname(os.path.abspath(__file__))
REF_30 = os.path.normpath(os.path.join(HERE, '..', 'ref', '3.0'))

R_NATIVE = 'ReloadGameCachesFromDisk'
JASS_FILES = ('war3map.j', 'scripts\\war3map.j')
LUA_FILE = 'war3map.lua'
ENDS = {'EndGame': 'ends the game', 'EndGameBJ': 'ends the game', 'CustomVictoryBJ': 'ends the game',
        'CustomDefeatBJ': 'defeats the players', 'CustomDefeatDialogBJ': 'defeats the players',
        'MeleeDoDefeat': 'defeats the players', 'RemovePlayer': 'removes the players',
        'RemovePlayerPreserveUnitsBJ': 'removes the players'}
MESSAGES = frozenset(('DisplayTextToPlayer', 'DisplayTimedTextToPlayer', 'DisplayTextToForce',
                      'DisplayTimedTextToForce', 'DisplayTimedTextFromPlayer', 'BJDebugMsg', 'QuestMessageBJ'))
RENAME = 'SetPlayerName'
QUIET = MESSAGES | frozenset((RENAME, 'PlaySoundBJ', 'StartSound', 'TriggerSleepAction', 'PolledWait', 'DoNothing',
                              'ClearTextMessages', 'ClearTextMessagesBJ', 'Player', 'GetPlayersAll', 'GetLocalPlayer',
                              'GetEnumPlayer', 'GetPlayerId', 'ConvertedPlayer', 'I2S', 'GetPlayerName'))
EXECUTORS = frozenset(('TriggerExecute', 'ConditionalTriggerExecute', 'TriggerExecuteWait', 'TriggerEvaluate'))
FOLLOW_DEPTH = 2
RX_SINGLE = re.compile(r'single[\s_-]*player|\bSP\b|\bLAN\b|offline'
                       r'|\uc2f1\uae00|\u5355\u673a|\u55ae\u6a5f|\u5355\u4eba', re.I)
RX_LOCK_MESSAGE = re.compile(r"(?:cannot|can't|can not|not|only)\b[^.!]{0,40}(?:single[\s_-]*player|offline)"
                             r"|single[\s_-]*player\b[^.!]{0,20}\b(?:not allowed|forbidden|detected|not supported)"
                             r"|\bplay(?: it)? (?:in|on|with) (?:lan|multiplayer|battle\.?net)", re.I)
RX_TRIGSTR = re.compile(r'^TRIGSTR_(\d+)$')


def _nothing(*_a, **_k):
    pass


class E(object):
    __slots__ = ('op', 'kids', 'name', 'value', 'node', 'body')

    def __init__(self, op, kids=(), name=None, value=None, node=None, body=None):
        self.op, self.kids, self.name, self.value, self.node, self.body = op, list(kids), name, value, node, body


class S(object):
    __slots__ = ('op', 'exprs', 'branches', 'body', 'name', 'line', 'node')

    def __init__(self, op, exprs=(), branches=None, body=None, name=None, line=0, node=None):
        self.op, self.exprs, self.branches, self.body, self.name = op, list(exprs), branches, body, name
        self.line, self.node = line, node


class F(object):
    __slots__ = ('name', 'params', 'locals', 'body', 'boolean', 'line')

    def __init__(self, name, params, local_names, body, boolean, line):
        self.name, self.params, self.locals, self.body, self.boolean, self.line = (name, params, set(local_names),
                                                                                   body, boolean, line)


def _jx(e):
    t = type(e)
    if t is jass_ast.Call:
        return E('call', [_jx(a) for a in e.args], name=e.name, node=e)
    if t is jass_ast.Name:
        return E('name', name=e.name, node=e)
    if t is jass_ast.Paren:
        return _jx(e.inner)
    if t is jass_ast.Unary:
        return E('not' if e.op == 'not' else 'other', [_jx(e.operand)], node=e)
    if t is jass_ast.Binary:
        return E(e.op if e.op in ('and', 'or', '==', '!=') else 'other', [_jx(e.left), _jx(e.right)], node=e)
    if t is jass_ast.Literal:
        if e.kind == 'boolean':
            return E('bool', value=e.text == 'true', node=e)
        if e.kind == 'string':
            return E('str', value=e.value, node=e)
        return E('other', node=e)
    if t is jass_ast.FuncRef:
        return E('ref', name=e.name, node=e)
    if t is jass_ast.Index:
        return E('other', [_jx(e.index)], node=e)
    return E('other', node=e)


def _js(s):
    t = type(s)
    if t is jass_ast.SetStmt:
        if type(s.target) is jass_ast.Name:
            return S('set', [_jx(s.value)], name=s.target.name, line=s.line, node=s)
        return S('other', [_jx(s.target), _jx(s.value)], line=s.line, node=s)
    if t is jass_ast.CallStmt:
        return S('call', [_jx(s.call)], line=s.line, node=s)
    if t is jass_ast.IfStmt:
        return S('if', branches=[(None if c is None else _jx(c), [_js(x) for x in b]) for c, b in s.branches],
                 line=s.line, node=s)
    if t is jass_ast.LoopStmt:
        return S('loop', body=[_js(x) for x in s.body], line=s.line, node=s)
    if t is jass_ast.ExitWhenStmt:
        return S('exitwhen', [_jx(s.cond)], line=s.line, node=s)
    if t is jass_ast.ReturnStmt:
        return S('return', [] if s.value is None else [_jx(s.value)], line=s.line, node=s)
    if t is jass_ast.DebugStmt:
        return _js(s.stmt)
    return S('comment', line=s.line, node=s)


def _jass_ir(tree):
    functions = {}
    for f in tree.functions:
        body = [S('local', [] if d.initializer is None else [_jx(d.initializer)], name=d.name, line=d.line, node=d)
                for d in f.locals]
        body += [_js(x) for x in f.body]
        names = [n for _t, n in f.params] + [d.name for d in f.locals]
        functions.setdefault(f.name, F(f.name, [n for _t, n in f.params], names, body, f.return_type == 'boolean',
                                       f.line))
    glob = {}
    for g in tree.globals:
        if g.type == 'boolean' and not g.is_array and not g.is_constant:
            glob[g.name] = None if g.initializer is None else _jx(g.initializer)
    return {'functions': functions, 'globals': glob, 'top': []}


def _lx(e):
    t = type(e)
    if t is lua_ast.Call:
        args = [_lx(a) for a in e.args]
        if type(e.func) is lua_ast.Name and e.method is None:
            return E('call', args, name=e.func.name, node=e)
        return E('other', [_lx(e.func)] + args, node=e)
    if t is lua_ast.Name:
        return E('name', name=e.name, node=e)
    if t is lua_ast.Paren:
        return _lx(e.inner)
    if t is lua_ast.Unary:
        return E('not' if e.op == 'not' else 'other', [_lx(e.operand)], node=e)
    if t is lua_ast.Binary:
        op = '!=' if e.op == '~=' else e.op
        return E(op if op in ('and', 'or', '==', '!=') else 'other', [_lx(e.left), _lx(e.right)], node=e)
    if t is lua_ast.Literal:
        if e.kind == 'boolean':
            return E('bool', value=bool(e.value), node=e)
        if e.kind == 'string':
            return E('str', value=e.value, node=e)
        return E('other', node=e)
    if t is lua_ast.FunctionExpr:
        return E('func', node=e, body=[_ls(x) for x in e.body])
    if t is lua_ast.Index:
        return E('other', [_lx(e.base), _lx(e.key)], node=e)
    if t is lua_ast.Table:
        kids = []
        for k, v in e.fields:
            if k is not None and not isinstance(k, str):
                kids.append(_lx(k))
            kids.append(_lx(v))
        return E('other', kids, node=e)
    return E('other', node=e)


_LUA_LOOPS = (lua_ast.WhileStmt, lua_ast.RepeatStmt, lua_ast.NumericForStmt, lua_ast.GenericForStmt, lua_ast.DoStmt)


def _ls(s):
    t = type(s)
    if t is lua_ast.LocalStmt:
        if len(s.names) == 1 and len(s.values) == 1:
            return S('local', [_lx(s.values[0])], name=s.names[0], line=s.line, node=s)
        return S('other', [_lx(v) for v in s.values], line=s.line, node=s)
    if t is lua_ast.AssignStmt:
        if len(s.targets) == 1 and len(s.values) == 1 and type(s.targets[0]) is lua_ast.Name:
            return S('set', [_lx(s.values[0])], name=s.targets[0].name, line=s.line, node=s)
        return S('other', [_lx(x) for x in list(s.targets) + list(s.values)], line=s.line, node=s)
    if t is lua_ast.CallStmt:
        return S('call', [_lx(s.call)], line=s.line, node=s)
    if t is lua_ast.IfStmt:
        return S('if', branches=[(None if c is None else _lx(c), [_ls(x) for x in b]) for c, b in s.branches],
                 line=s.line, node=s)
    if t in _LUA_LOOPS:
        ex = [getattr(s, n) for n in ('cond', 'start', 'stop', 'step') if n in t.__slots__]
        ex += list(s.exprs) if t is lua_ast.GenericForStmt else []
        return S('loop', [_lx(x) for x in ex if x is not None], body=[_ls(x) for x in s.body], line=s.line, node=s)
    if t is lua_ast.ReturnStmt:
        return S('return', [_lx(v) for v in s.values], line=s.line, node=s)
    if t is lua_ast.FunctionStmt:
        return S('def', line=s.line, node=s)
    if t in (lua_ast.BreakStmt, lua_ast.GotoStmt, lua_ast.LabelStmt):
        return S('other', line=s.line, node=s)
    return S('comment', line=s.line, node=s)


_LUA_STMT_FIELDS = ('values', 'targets', 'call', 'cond', 'exprs', 'start', 'stop', 'step')


def _lua_nodes(body):
    stack = list(body)
    while stack:
        s = stack.pop()
        yield s
        t = type(s)
        if t is lua_ast.IfStmt:
            for _c, b in s.branches:
                stack.extend(b)
        elif t in _LUA_LOOPS or t is lua_ast.FunctionStmt:
            stack.extend(s.body)
        todo = []
        for n in _LUA_STMT_FIELDS:
            if n in t.__slots__ and getattr(s, n) is not None:
                v = getattr(s, n)
                todo.extend(v if isinstance(v, (list, tuple)) else [v])
        if t is lua_ast.IfStmt:
            todo.extend(c for c, _b in s.branches if c is not None)
        while todo:
            x = todo.pop()
            k = type(x)
            if k is lua_ast.FunctionExpr:
                yield x
                stack.extend(x.body)
            elif k is lua_ast.Call:
                todo.append(x.func)
                todo.extend(x.args)
            elif k is lua_ast.Binary:
                todo.extend((x.left, x.right))
            elif k is lua_ast.Unary:
                todo.append(x.operand)
            elif k is lua_ast.Paren:
                todo.append(x.inner)
            elif k is lua_ast.Index:
                todo.extend((x.base, x.key))
            elif k is lua_ast.Table:
                todo.extend(v for _k, v in x.fields)
                todo.extend(k2 for k2, _v in x.fields if k2 is not None and not isinstance(k2, str))


def _lua_declared(body):
    out = set()
    for s in _lua_nodes(body):
        t = type(s)
        if t is lua_ast.LocalStmt or t is lua_ast.GenericForStmt:
            out.update(s.names)
        elif t is lua_ast.NumericForStmt:
            out.add(s.var)
        elif t is lua_ast.FunctionStmt:
            out.update(s.params)
            if s.is_local:
                out.add(s.name)
        elif t is lua_ast.FunctionExpr:
            out.update(s.params)
    return out


def _lua_ir(chunk):
    declared = _lua_declared(chunk.body)
    functions = {}
    for s in chunk.body:
        if type(s) is lua_ast.FunctionStmt and not s.is_local and re.match(r'[A-Za-z_]\w*\Z', s.name):
            functions[s.name] = F(s.name, list(s.params), _lua_declared(s.body) | set(s.params),
                                  [_ls(x) for x in s.body], True, s.line)
    glob = {}
    for s in _lua_nodes(chunk.body):
        if type(s) is lua_ast.AssignStmt:
            for tg in s.targets:
                if type(tg) is lua_ast.Name and tg.name not in declared:
                    glob[tg.name] = None
    top = F('(main chunk)', [], set(), [_ls(x) for x in chunk.body], False, 1)
    top.locals = set(n for x in chunk.body if type(x) is lua_ast.LocalStmt for n in x.names)
    return {'functions': functions, 'globals': glob, 'top': [top]}


def _stmt_exprs(s):
    return s.exprs + ([c for c, _b in s.branches if c is not None] if s.op == 'if' else [])


def _stmt_bodies(s):
    if s.op == 'if':
        return [b for _c, b in s.branches]
    return [s.body] if s.op == 'loop' else []


def _deep(body, inline=False):
    stack = list(reversed(body))
    while stack:
        s = stack.pop()
        yield s
        for b in reversed(_stmt_bodies(s)):
            stack.extend(reversed(b))
        if inline:
            for e in _stmt_exprs(s):
                for x in _exprs(e):
                    if x.op == 'func':
                        stack.extend(reversed(x.body))


def _exprs(e):
    stack = [e]
    while stack:
        x = stack.pop()
        yield x
        stack.extend(reversed(x.kids))


def _exits(body):
    rest = [s for s in body if s.op != 'comment']
    return bool(rest) and rest[-1].op == 'return'


LABEL_ORDER = ('ends the game', 'defeats the players', 'removes the players', 'renames the players',
               'shows a single player message')


class _Analysis(object):
    def __init__(self, ir, language, strings=None):
        self.lang = language
        self.funcs = ir['functions']
        self.units = list(self.funcs.values()) + ir['top']
        self.globals = ir['globals']
        self.strings = strings or {}
        self.inline = language == 'lua'
        self.alias_funcs, self.alias_vars = {}, {}
        self._triggers = None
        self.sets = {}
        for f in self.units:
            for s in _deep(f.body, inline=self.inline):
                if s.op in ('set', 'local'):
                    key = (f.name, s.name) if s.name in f.locals else s.name
                    if isinstance(key, tuple) or key in self.globals:
                        self.sets.setdefault(key, []).append((s.exprs[0] if s.exprs else None, f))
        self._aliases()

    def term(self, e, f):
        if e.op == 'call' and not e.kids:
            if e.name == R_NATIVE:
                return 'call', False
            v = self.alias_funcs.get(e.name)
            if v is not None and (f is None or e.name not in f.locals):
                return 'call', v
        elif e.op == 'name':
            key = (f.name, e.name) if f is not None and e.name in f.locals else e.name
            v = self.alias_vars.get(key)
            if v is not None:
                return 'var', v
        return None

    def terms_in(self, e, f):
        out = []
        stack = [e]
        while stack:
            x = stack.pop()
            t = self.term(x, f)
            if t is not None:
                out.append((x, t[1]))
            else:
                stack.extend(reversed(x.kids))
        return out

    def value(self, e, f, sp):
        t = self.term(e, f)
        if t is not None:
            if not sp:
                return t[1]
            return (not t[1]) if t[0] == 'call' else None
        op = e.op
        if op == 'bool':
            return e.value
        if op == 'not':
            v = self.value(e.kids[0], f, sp)
            return None if v is None else not v
        if op in ('and', 'or', '==', '!='):
            a, b = self.value(e.kids[0], f, sp), self.value(e.kids[1], f, sp)
            if op == 'and':
                return False if (a is False or b is False) else (True if (a and b) else None)
            if op == 'or':
                return True if (a is True or b is True) else (False if (a is False and b is False) else None)
            if a is None or b is None:
                return None
            return (a == b) if op == '==' else (a != b)
        return None

    def _decided(self, e, f):
        sp, mp = self.value(e, f, True), self.value(e, f, False)
        return mp if (sp is not None and mp is not None and sp != mp) else None

    def _returns(self, body, f, sp):
        for s in [x for x in body if x.op != 'comment']:
            if s.op == 'return':
                return self.value(s.exprs[0], f, sp) if len(s.exprs) == 1 else None
            if s.op != 'if':
                return None
            for cond, b in s.branches:
                v = True if cond is None else self.value(cond, f, sp)
                if v is None:
                    return None
                if v:
                    if [x for x in b if x.op != 'comment']:
                        return self._returns(b, f, sp)
                    break
        return None

    def _aliases(self):
        for _round in range(6):
            before = (dict(self.alias_funcs), dict(self.alias_vars))
            for f in self.funcs.values():
                if f.params or not f.boolean or [s for s in f.body if s.op == 'local']:
                    continue
                sp, mp = self._returns(f.body, f, True), self._returns(f.body, f, False)
                if sp is not None and mp is not None and sp != mp:
                    self.alias_funcs[f.name] = mp
            for key, values in self.sets.items():
                init = None if isinstance(key, tuple) else self.globals.get(key)
                mp, ok = None, True
                decided = []
                for e, f in values + ([(init, None)] if init is not None else []):
                    if e is None:
                        continue
                    d = self._decided(e, f) if e.op != 'bool' else None
                    if d is not None:
                        decided.append(d)
                if not decided or len(set(decided)) != 1:
                    continue
                mp = decided[0]
                if not isinstance(key, tuple) and init is None and mp is not False:
                    continue
                for e, f in values + ([(init, None)] if init is not None else []):
                    if e is None:
                        ok = ok and mp is False
                    elif e.op == 'bool':
                        ok = ok and e.value == mp
                    else:
                        ok = ok and self._decided(e, f) == mp
                if ok:
                    self.alias_vars[key] = mp
            if (dict(self.alias_funcs), dict(self.alias_vars)) == before:
                break

    @property
    def triggers(self):
        if self._triggers is None:
            self._triggers = self._trigger_actions()
        return self._triggers

    def _trigger_actions(self):
        out = {}
        for f in self.units:
            for s in _deep(f.body, inline=self.inline):
                for e in _stmt_exprs(s):
                    for x in _exprs(e):
                        if x.op == 'call' and x.name == 'TriggerAddAction' and len(x.kids) == 2 and \
                                x.kids[0].op == 'name':
                            a = x.kids[1]
                            if a.op in ('ref', 'name') and a.name in self.funcs:
                                out.setdefault(x.kids[0].name, []).append(a.name)
                            elif a.op == 'func':
                                out.setdefault(x.kids[0].name, []).append(a)
        return out

    def scan(self):
        sites, others = [], []
        for f in self.units:
            if f.name not in self.alias_funcs:
                self._scan_body(f, f.body, [], sites, others)
        return sites, others

    def _scan_body(self, f, body, path, sites, others):
        for k, s in enumerate(body):
            here = path + [(body, k)]
            if s.op == 'if':
                terms = [(i, self.terms_in(c, f)) for i, (c, _b) in enumerate(s.branches) if c is not None]
                terms = [(i, t) for i, t in terms if t]
                if terms:
                    self._decision(f, s, here, terms, sites, others)
            else:
                found = [t for e in _stmt_exprs(s) for t in self.terms_in(e, f)]
                found += [x for e in _stmt_exprs(s) for x in _exprs(e) if x.op in ('ref', 'name') and
                          x.name in self.alias_funcs and x.name not in f.locals]
                if found and not self._alias_use(f, s):
                    bare = s.op == 'call' and s.exprs[0].op == 'call' and s.exprs[0].name == R_NATIVE
                    others.append({'function': f.name, 'line': s.line, 'kind': 'reload' if bare else 'unfollowed'})
            for b in _stmt_bodies(s):
                self._scan_body(f, b, here, sites, others)
            if self.inline:
                for e in _stmt_exprs(s):
                    for x in _exprs(e):
                        if x.op == 'func':
                            self._scan_body(f, x.body, [], sites, others)

    def _alias_use(self, f, s):
        if s.op in ('set', 'local'):
            return ((f.name, s.name) if s.name in f.locals else s.name) in self.alias_vars
        return s.op == 'return' and f.name in self.alias_funcs

    def _taken(self, branches, f, sp):
        out, reach = [], 'yes'
        for cond, _body in branches:
            if reach == 'node':
                out.append('node')
                continue
            v = True if cond is None else self.value(cond, f, sp)
            if v is True:
                out.append(reach)
                reach = 'node'
            elif v is False:
                out.append('node')
            else:
                out.append('maybe')
                reach = 'maybe'
        return out

    def _decision(self, f, s, path, terms, sites, others):
        branches = list(s.branches)
        if branches[-1][0] is not None:
            branches.append((None, []))
        tsp, tmp = self._taken(branches, f, True), self._taken(branches, f, False)
        regions = [b for (_c, b), a, m in zip(branches, tsp, tmp) if m == 'node' and a != 'node']
        mp_live = [b for (_c, b), m in zip(branches, tmp) if m != 'node']
        sp_live = [b for (_c, b), a in zip(branches, tsp) if a != 'node']
        if mp_live and all(_exits(b) for b in mp_live) and any(not _exits(b) for b in sp_live):
            body, k = path[-1]
            regions.append(body[k + 1:])
        use = {'function': f.name, 'line': s.line}
        if not regions:
            use['kind'] = 'branch' if tsp == tmp else 'unfollowed'
            others.append(use)
            return
        labels = self._locks(regions, f)
        if any(lb in ENDS.values() for lb in labels) or (self._only_message(regions, f) and self._lock_message):
            use.update({'what': ', '.join(lb for lb in LABEL_ORDER if lb in labels), '_stmt': s, '_terms': terms})
            sites.append(use)
        else:
            use['kind'] = 'branch'
            others.append(use)

    def _text(self, e):
        if e.op != 'str' or not isinstance(e.value, str):
            return None
        m = RX_TRIGSTR.match(e.value)
        return self.strings.get(int(m.group(1)), '') if m else e.value

    def _locks(self, regions, f):
        labels = set()
        self._lock_message = False
        seen = set()

        def follow(name, depth):
            if depth < FOLLOW_DEPTH and name in self.funcs and name not in seen:
                seen.add(name)
                visit(self.funcs[name].body, depth + 1, self.funcs[name])

        def visit(body, depth, fn):
            for st in _deep(body):
                for e in _stmt_exprs(st):
                    for x in _exprs(e):
                        if x.op == 'call':
                            if x.name in ENDS:
                                labels.add(ENDS[x.name])
                            elif x.name == RENAME:
                                labels.add('renames the players')
                            elif x.name in MESSAGES:
                                for a in x.kids:
                                    t = self._text(a)
                                    if t and RX_SINGLE.search(t):
                                        labels.add('shows a single player message')
                                        self._lock_message = self._lock_message or bool(RX_LOCK_MESSAGE.search(t))
                            elif x.name in EXECUTORS and x.kids and x.kids[0].op == 'name':
                                for target in self.triggers.get(x.kids[0].name, ()):
                                    if isinstance(target, str):
                                        follow(target, depth)
                                    else:
                                        visit(target.body, depth, fn)
                            elif x.name == 'ExecuteFunc' and x.kids and self._text(x.kids[0]):
                                follow(self._text(x.kids[0]), depth)
                            elif x.name in self.funcs and x.name not in fn.locals:
                                follow(x.name, depth)
                        elif x.op == 'ref' or (x.op == 'name' and self.lang == 'lua' and x.name not in fn.locals):
                            follow(x.name, depth)
                        elif x.op == 'func':
                            visit(x.body, depth, fn)

        for b in regions:
            visit(b, 0, f)
        return labels

    def _only_message(self, regions, f):
        for b in regions:
            for st in _deep(b):
                if st.op in ('comment', 'loop', 'exitwhen', 'if'):
                    pass
                elif st.op in ('set', 'local'):
                    if st.name not in f.locals:
                        return False
                elif st.op != 'call':
                    return False
                for e in _stmt_exprs(st):
                    for x in _exprs(e):
                        if x.op in ('call', 'func', 'ref') and (x.op != 'call' or x.name not in QUIET):
                            return False
        return True


def _result(language=None, file=None):
    return {'found': False, 'language': language, 'file': file, 'sites': [], 'other_uses': [], 'notes': [],
            'reason': None}


def _analyze(text, language, strings=None, tree=None):
    res = _result(language)
    if R_NATIVE not in text:
        return res, [], tree
    try:
        if tree is None:
            tree = jass_ast.parse(text) if language == 'jass' else lua_ast.parse(text)
        ir = _jass_ir(tree) if language == 'jass' else _lua_ir(tree)
    except (jass_ast.JassSyntaxError, lua_ast.LuaSyntaxError) as e:
        res['reason'] = 'The script does not parse (%s).' % e
        return res, [], None
    an = _Analysis(ir, language, strings)
    sites, others = an.scan()
    res['sites'] = [dict((k, v) for k, v in x.items() if not k.startswith('_')) for x in sites]
    res['other_uses'] = others
    res['found'] = bool(sites)
    if sites and re.search(r'(?<![\w.])Cheat\s*\(', text):
        res['notes'].append('The script also calls Cheat(), another test that works only in single player; it is '
                            'left as it is.')
    return res, sites, tree


def analyze(text, language, strings=None, tree=None):
    return _analyze(text, language, strings, tree)[0]


def script_of(a):
    j_name = j = None
    for n in JASS_FILES:
        b = unprotect._read(a, n)
        if b is not None:
            j_name, j = n, b
            break
    lang = unprotect.language_from_w3i(unprotect._read(a, 'war3map.w3i'))
    out = {'language': None, 'file': None, 'bytes': None, 'copies': [], 'compiled': False}
    if a.find(LUA_FILE) and (lang == 1 or j is None):
        out.update({'language': 'lua', 'file': LUA_FILE, 'bytes': unprotect._read(a, LUA_FILE)})
    elif j is not None:
        compiled = (len(j) < 450 and bool(a.find('kkmap.jc'))) or unprotect.script_j2b(a, j)
        copies = [n for n in JASS_FILES if n != j_name and a.find(n) and unprotect._read(a, n) == j]
        out.update({'language': 'jass', 'file': j_name, 'bytes': j, 'copies': copies, 'compiled': bool(compiled)})
    return out


def read_map(path):
    a = unprotect._open(path)
    sc = script_of(a)
    strings = object_names.strings(unprotect._read(a, 'war3map.wts'))
    return a, sc, strings


def _find(path):
    try:
        a, sc, strings = read_map(path)
    except BaseException as e:
        if isinstance(e, KeyboardInterrupt):
            raise
        res = _result()
        res['reason'] = 'The map cannot be read (%s).' % unprotect._error(e)
        return res, [], None, None, None, None, None
    res = _result(sc['language'], sc['file'])
    if sc['language'] is None:
        res['reason'] = 'The map has no script.'
    elif sc['bytes'] is None:
        res['reason'] = 'The script cannot be read.'
    elif sc['compiled']:
        res['reason'] = 'The script is compiled (the KK platform bytecode), so it cannot be checked.'
    if res['reason']:
        return res, [], None, None, sc, a, strings
    text = sc['bytes'].decode('utf-8', 'surrogateescape')
    out, sites, tree = _analyze(text, sc['language'], strings)
    out['file'] = sc['file']
    return out, sites, tree, text, sc, a, strings


def find(path):
    return _find(path)[0]


class _Refused(Exception):
    pass


def _wrapped(term_text, mp):
    return '(' + term_text + (' or true)' if mp else ' and false)')


def _jass_spans(line, terms):
    spans, pos = [], 0
    for tok in jass_ast.tokenize(line):
        while pos < len(line) and line[pos] in ' \t\ufeff':
            pos += 1
        if not line.startswith(tok, pos):
            return None
        spans.append((tok, pos))
        pos += len(tok)
    words = [t for t, _p in spans]
    if not words or words[0] not in ('if', 'elseif') or 'then' not in words:
        return None
    cond = spans[1:words.index('then')]
    names = set(x.name for x, _mp in terms)
    found = []
    for i, (tok, p) in enumerate(cond):
        if tok in names:
            nxt = [t for t, _p in cond[i + 1:i + 3]]
            if nxt == ['(', ')']:
                found.append((tok, 'call', p, cond[i + 2][1] + 1))
            elif not nxt or nxt[0] not in ('(', '['):
                found.append((tok, 'name', p, p + len(tok)))
    if [(n, o) for n, o, _s, _e in found] != [(x.name, x.op) for x, _mp in terms]:
        return None
    return [(s, e, mp) for (_n, _o, s, e), (_x, mp) in zip(found, terms)]


def _patch_jass(text, sites):
    parts = re.split(r'(\r\n|\r|\n)', text)
    lines = parts[0::2]
    edits = {}
    for site in sites:
        node = site['_stmt'].node
        for k, terms in site['_terms']:
            ln = node.branch_lines[k]
            spans = _jass_spans(lines[ln - 1], terms) if 0 < ln <= len(lines) else None
            if spans is None:
                raise _Refused('The condition at line %d could not be matched to its text.' % ln)
            edits.setdefault(ln - 1, (site['function'], []))[1].extend(spans)
    changes = []
    for i in sorted(edits):
        fn, spans = edits[i]
        before = line = lines[i]
        for start, end, mp in sorted(spans, reverse=True):
            line = line[:start] + _wrapped(line[start:end], mp) + line[end:]
        lines[i] = line
        changes.append({'function': fn, 'line': i + 1, 'before': before.strip(), 'after': line.strip()})
    parts[0::2] = lines
    return ''.join(parts), changes


def _lua_conditions(kinds, texts, offs, start, end):
    i = bisect.bisect_left(offs, start)
    if i >= len(kinds) or kinds[i] != 'if':
        return None
    ranges, depth, head = [], 0, None
    for j in range(i, len(kinds)):
        if offs[j] >= end:
            break
        k = kinds[j]
        if k in ('if', 'function', 'do', 'repeat'):
            depth += 1
            if depth == 1:
                head = j + 1
        elif k in ('end', 'until'):
            depth -= 1
            if depth == 0:
                break
        elif depth == 1 and k == 'elseif':
            head = j + 1
        elif depth == 1 and k == 'else':
            ranges.append(None)
        elif depth == 1 and k == 'then' and head is not None:
            ranges.append((head, j))
            head = None
    return ranges


def _patch_lua(text, sites):
    kinds, texts, lines, offs = lua_ast._lex(text)[:4]
    edits, changes = [], []
    for site in sites:
        node = site['_stmt'].node
        ranges = _lua_conditions(kinds, texts, offs, node.span[0], node.span[1]) if node.span else None
        if ranges is None or len(ranges) != len(node.branches):
            raise _Refused('The condition at line %d could not be matched to its text.' % node.line)
        for k, terms in site['_terms']:
            a, b = ranges[k]
            names = set(x.name for x, _mp in terms)
            found = []
            for j in range(a, b):
                if kinds[j] != 'NAME' or texts[j] not in names or (j > 0 and texts[j - 1] in ('.', ':')):
                    continue
                if texts[j + 1] == '(' and texts[j + 2] == ')':
                    found.append((texts[j], 'call', offs[j], offs[j + 2] + 1))
                elif texts[j + 1] not in ('(', '.', ':', '[', '{') and kinds[j + 1] != 'STRING':
                    found.append((texts[j], 'name', offs[j], offs[j] + len(texts[j])))
            if [(n, o) for n, o, _s, _e in found] != [(x.name, x.op) for x, _mp in terms]:
                raise _Refused('The condition at line %d could not be matched to its text.' % lines[a])
            for (_n, _o, s, e), (_x, mp) in zip(found, terms):
                edits.append((s, e, mp, site['function'], lines[a]))
    out = text
    for s, e, mp, _fn, _ln in sorted(edits, reverse=True):
        out = out[:s] + _wrapped(out[s:e], mp) + out[e:]
    for s, e, mp, fn, ln in sorted(edits):
        changes.append({'function': fn, 'line': ln, 'before': text[s:e], 'after': _wrapped(text[s:e], mp)})
    return out, changes


def _wrap_nodes(e, targets, lang):
    mod = jass_ast if lang == 'jass' else lua_ast
    if id(e) in targets:
        mp = targets[id(e)]
        lit = mod.Literal('boolean', 'true' if mp else 'false') if lang == 'jass' else \
            mod.Literal('boolean', 'true' if mp else 'false', mp)
        return mod.Paren(mod.Binary('or' if mp else 'and', e, lit))
    t = type(e)
    if t is mod.Call:
        e.args = [_wrap_nodes(x, targets, lang) for x in e.args]
    elif t is mod.Paren:
        e.inner = _wrap_nodes(e.inner, targets, lang)
    elif t is mod.Unary:
        e.operand = _wrap_nodes(e.operand, targets, lang)
    elif t is mod.Binary:
        e.left, e.right = _wrap_nodes(e.left, targets, lang), _wrap_nodes(e.right, targets, lang)
    elif t is mod.Index:
        if lang == 'jass':
            e.index = _wrap_nodes(e.index, targets, lang)
        else:
            e.base, e.key = _wrap_nodes(e.base, targets, lang), _wrap_nodes(e.key, targets, lang)
    return e


RX_PJASS_LINE = re.compile(r'^\S+:\d+:\s*')


def _pjass(old_bytes, new_bytes):
    pj = jass_ast._load_pjass()
    if pj is None:
        return {'state': 'skipped', 'note': 'pjass was not found'}
    tmp = tempfile.mkdtemp(prefix='single_player_')
    try:
        res = []
        for tag, data in (('a', old_bytes), ('b', new_bytes)):
            src = os.path.join(tmp, tag + '.j')
            with open(src, 'wb') as fh:
                fh.write(data)
            ref = pj.game_scripts_dir(REF_30) or REF_30
            r = pj.run_action([(os.path.join(ref, 'common.j'), 'common.j'), (os.path.join(ref, 'blizzard.j'),
                         'blizzard.j'), (src, 'war3map.j')], tmp=os.path.join(tmp, tag))
            if r.get('missing') or (r['rc'] == 2 and not r['line_list']):
                return {'state': 'skipped', 'note': 'the game scripts (common.j, blizzard.j) were not found'}
            lines = [ln.replace(os.path.join(tmp, tag), '') for ln in r['line_list']]
            msgs = collections.Counter(RX_PJASS_LINE.sub('', ln) for ln in lines)
            res.append((r['rc'] == 0 and not r['error_list'] and not r['warnings'], (r['rc'], msgs),
                        'exit %d, %d errors, %d warnings, %d lines of output' % (
                            r['rc'], len(r['error_list']), len(r['warnings']), len(r['line_list']))))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    (ok_a, out_a, d_a), (ok_b, out_b, d_b) = res
    state = ('passed' if ok_b else 'failed') if ok_a else ('original_fails' if out_b == out_a else 'failed')
    return {'state': state, 'original': d_a, 'new': d_b}


def _change(text, language, sites, tree, strings):
    new, changes = (_patch_jass if language == 'jass' else _patch_lua)(text, sites)
    try:
        new_tree = jass_ast.parse(new) if language == 'jass' else lua_ast.parse(new)
    except (jass_ast.JassSyntaxError, lua_ast.LuaSyntaxError) as e:
        raise _Refused('The changed script does not parse (%s).' % e)
    for site in sites:
        node = site['_stmt'].node
        targets = dict((id(x.node), mp) for _k, terms in site['_terms'] for x, mp in terms)
        node.branches[:] = [(c if c is None else _wrap_nodes(c, targets, language), b) for c, b in node.branches]
    mod = jass_ast if language == 'jass' else lua_ast
    if mod.canonical(tree) != mod.canonical(new_tree):
        raise _Refused('The changed script is not the old one with only the conditions changed.')
    again = _analyze(new, language, strings, new_tree)[0]
    if again['found'] or again['reason']:
        raise _Refused('The changed script still ends the game in single player.')
    proof = {'parses': True, 'same_tree': True, 'sites_left': 0, 'terms': sum(len(t) for s in sites
                                                                             for _k, t in s['_terms'])}
    if language == 'jass':
        old_lines, new_lines = re.split(r'\r\n|\r|\n', text), re.split(r'\r\n|\r|\n', new)
        moved = [i + 1 for i, (x, y) in enumerate(zip(old_lines, new_lines)) if x != y]
        if len(old_lines) != len(new_lines) or moved != [c['line'] for c in changes]:
            raise _Refused('The changed script differs from the old one outside the conditions.')
        proof['lines_changed'] = len(moved)
    return new, changes, proof


def unlock(path_in, path_out, progress=None):
    p = progress or _nothing
    rep = {'state': None, 'reason': None, 'language': None, 'file': None, 'sites': [], 'changes': [], 'proof': {},
           'notes': [], 'output': None}

    def stop(state, why):
        rep['state'], rep['reason'] = state, why
        return rep

    if os.path.abspath(path_out) == os.path.abspath(path_in):
        return stop('refused', 'The output must be a new file.')
    p('Reading the map')
    res, sites, tree, text, sc, a, strings = _find(path_in)
    rep.update({'language': res['language'], 'file': res['file'], 'sites': res['sites'], 'notes': res['notes']})
    if res['reason']:
        return stop('refused', res['reason'])
    if not sites:
        return stop('nothing', 'The map does not end the game in single player.')
    with unprotect.quiet():
        protected = a.is_malformed or mpqdoctor.virtual_tables(a) or mpqdoctor.is_sprotect(a)[0]
    if protected:
        return stop('refused', 'The archive is protected: remove the protection first.')
    p('Changing the script')
    try:
        new, changes, proof = _change(text, sc['language'], sites, tree, strings)
    except _Refused as e:
        return stop('refused', str(e))
    new_bytes = new.encode('utf-8', 'surrogateescape')
    rep['changes'], rep['proof'] = changes, proof
    if sc['language'] == 'jass':
        p('Running pjass')
        proof['pjass'] = _pjass(sc['bytes'], new_bytes)
        if proof['pjass']['state'] == 'failed':
            return stop('refused', 'pjass does not accept the changed script (%s).' % proof['pjass']['new'])
    p('Writing the map')
    names = [sc['file']] + sc['copies']
    part = unprotect._part(path_out)
    try:
        shutil.copyfile(path_in, part)
        no_room = []
        with unprotect.quiet():
            mpqadd.add_files(part, [(n, new_bytes) for n in names], all_entries=True, log=_nothing, no_slot=no_room)
        if no_room:
            raise RuntimeError('no room in the hash table for %s' % ', '.join(no_room))
        p('Checking the written map')
        b = unprotect._open(part)
        for n in names:
            if unprotect._read(b, n) != new_bytes:
                raise RuntimeError('%s is not read back as written' % n)
        del b
        with unprotect.quiet():
            same = unprotect.check_content(path_in, part, exclude=names)
        if same['different'] or same['missing_items']:
            raise RuntimeError('other files changed: %s' % ', '.join((same['different'] + same['missing_items'])[:5]))
        if _find(part)[0]['found']:
            raise RuntimeError('the written map still ends the game in single player')
        os.replace(part, path_out)
    except Exception as e:
        try:
            os.remove(part)
        except OSError:
            pass
        return stop('failed', 'The map could not be written (%s).' % unprotect._error(e))
    proof['map'] = {'script_read_back': True, 'same_files': same['identical'], 'sites_left': 0}
    rep['state'], rep['output'] = 'done', os.path.abspath(path_out)
    return rep
