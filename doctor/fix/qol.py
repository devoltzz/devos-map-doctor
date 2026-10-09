# The quality of life edits of a map: experience, gold, lumber, item drop and craft chances, hero revive time, camera shakes, the map revealed and VIP by name, written into the map script.
import re

from doctor.fix import unprotect
from doctor.script import jass_ast
from doctor.port import swap_calls


PREFIX = 'QoL'
MARK = PREFIX + '_Init'
DEFAULTS = {
    'xp': 1.0,
    'gold': 1.0,
    'lumber': 1.0,
    'respawn': 1.0,
    'drop': 1.0,
    'craft': 1.0,
    'noshake': False,
    'noshake_default': False,
    'reveal': False,
    'vip': False,
}
LIMITS = {'xp': (0.0, 100.0), 'gold': (0.0, 100.0), 'lumber': (0.0, 100.0), 'respawn': (0.0, 10.0),
          'drop': (0.0, 100.0), 'craft': (0.0, 100.0)}
XP_CALLS = {'SetPlayerHandicapXP': PREFIX + '_HandicapXP', 'SetPlayerHandicapXPBJ': PREFIX + '_HandicapXPBJ',
            'AddHeroXP': PREFIX + '_AddHeroXP', 'AddHeroXPSwapped': PREFIX + '_AddHeroXPSwapped'}
SHAKE_CALLS = {'CameraSetEQNoiseForPlayer': PREFIX + '_EQNoise', 'CameraSetSourceNoise': PREFIX + '_SourceNoise',
               'CameraSetTargetNoise': PREFIX + '_TargetNoise', 'CameraSetSourceNoiseEx': PREFIX + '_SourceNoiseEx',
               'CameraSetTargetNoiseEx': PREFIX + '_TargetNoiseEx'}
FOG_CALLS = {'FogEnable': PREFIX + '_FogEnable', 'FogMaskEnable': PREFIX + '_FogMaskEnable',
             'FogEnableOn': PREFIX + '_FogEnableOn', 'FogEnableOff': PREFIX + '_FogEnableOff',
             'FogMaskEnableOn': PREFIX + '_FogMaskEnableOn', 'FogMaskEnableOff': PREFIX + '_FogMaskEnableOff'}
REVIVE = {'ReviveHero': 'ReviveHero', 'ReviveHeroLoc': 'ReviveHeroLoc'}
WAITS = {'TriggerSleepAction': 0, 'PolledWait': 0, 'StartTimerBJ': 2, 'TimerStart': 1}
LINKS = {'TriggerAddAction': 'TriggerAddAction', 'TriggerRegisterTimerExpireEvent': 'TriggerRegisterTimerExpireEvent',
         'TriggerRegisterTimerExpireEventBJ': 'TriggerRegisterTimerExpireEventBJ'}
SET_XP = {'SetHeroXP': 'SetHeroXP', 'SetHeroLevel': 'SetHeroLevel', 'SetHeroLevelBJ': 'SetHeroLevelBJ'}
RX_SAVE = re.compile(r'"-(?:save|load)\b', re.I)


def _nothing(*_a, **_k):
    pass


def _lines(text):
    parts = re.split(r'(\r\n?|\n)', text)
    return [parts[i] + (parts[i + 1] if i + 1 < len(parts) else '') for i in range(0, len(parts), 2)]


def _skip(line, i):
    return swap_calls.skip_string(line, i) if line[i] == '"' else swap_calls.skip_rawcode(line, i)


def _args(line, open_at):
    out = []
    depth = 0
    start = open_at + 1
    i = open_at + 1
    n = len(line)
    while i < n:
        c = line[i]
        if c in '"\'':
            i = _skip(line, i)
            continue
        if c == '/' and line.startswith('//', i):
            return None
        if c == '(':
            depth += 1
        elif c == ')':
            if depth == 0:
                if line[start:i].strip():
                    out.append((start, i))
                return out, i
            depth -= 1
        elif c == ',' and depth == 0:
            out.append((start, i))
            start = i + 1
        i += 1
    return None


def _calls(line, names):
    out = []
    for ini, fim, name in swap_calls.sitios(line, names):
        k = line.index('(', fim)
        a = _args(line, k)
        if a is None:
            continue
        spans = a[0]
        out.append((name, [line[s:e].strip() for s, e in spans], spans))
    return out


def _norm(expr):
    return re.sub(r'\s+', '', expr)


RX_SET = re.compile(r'^\s*set\s+(\w+)\s*=\s*(.+?)\s*(?://.*)?$')
RX_REVIVE_NAME = re.compile(r'reviv|respawn|resurr|rez', re.I)
RX_ALIAS = re.compile(r'^(?:\w+|\w+\[[^\[\]]*\]|function\w+)$')


class _Aliases(object):
    def __init__(self, lines, owner_start):
        self.lines = lines
        self.owner_start = owner_start
        once = {}
        for l in lines:
            m = RX_SET.match(l)
            if m:
                once.setdefault(m.group(1), []).append(m.group(2))
        self.once = dict((k, v[0]) for k, v in once.items() if len(v) == 1)

    def resolve(self, expr, k, depth=0):
        expr = _norm(expr)
        if depth > 4 or not re.match(r'^\w+$', expr):
            return expr
        start = self.owner_start.get(k)
        if start is not None:
            for j in range(k - 1, start - 1, -1):
                m = RX_SET.match(self.lines[j - 1])
                if m and m.group(1) == expr:
                    rhs = _norm(m.group(2))
                    if RX_ALIAS.match(rhs):
                        return self.resolve(rhs, j, depth + 1)
                    return '%d/%s' % (start, expr)
        if expr in self.once and RX_ALIAS.match(_norm(self.once[expr])):
            return self.resolve(self.once[expr], None, depth + 1)
        return expr


def _timer_key(expr):
    m = re.match(r'^(\w+)\[(.*)\]$', expr)
    if not m:
        return expr, None, True
    return expr, m.group(1), bool(re.match(r'^(?:\d+|\$[0-9A-Fa-f]+|0x[0-9A-Fa-f]+)$', m.group(2)))


def _functions(tree):
    return [f for f in tree.functions if not f.is_native]


def respawn_sites(text, tree):
    lines = _lines(text)
    funcs = _functions(tree)
    owner, owner_start = {}, {}
    for f in funcs:
        for k in range(f.line, f.end_line + 1):
            owner[k] = f.name
            owner_start[k] = f.line
    al = _Aliases(lines, owner_start)
    revive = set()
    last = {}
    for f in funcs:
        for k in range(f.line, f.end_line):
            if swap_calls.sitios(lines[k - 1], REVIVE):
                revive.add(f.name)
                last[f.name] = k
    via = {}
    names = dict((n, n) for n in revive)
    for f in funcs:
        if f.name in revive:
            continue
        for k in range(f.line + 1, f.end_line):
            l = lines[k - 1]
            hit = set(n for _i, _j, n in swap_calls.sitios(l, names)) if any(n in l for n in names) else set()
            hit |= set(n for n in re.findall(r'\bfunction\s+(\w+)', l.split('//')[0]) if n in revive)
            if hit and not re.search(r'\b(?:TriggerAddAction|TimerStart|TriggerAddCondition)\s*\(', l):
                via.setdefault(f.name, set()).update(hit)
                last[f.name] = k

    def code_of(expr, k):
        m = re.match(r'^function(\w+)$', al.resolve(expr, k))
        return m.group(1) if m else None

    action_of = {}
    for k, l in enumerate(lines, 1):
        if 'TriggerAddAction' not in l:
            continue
        for name, args, _spans in _calls(l, LINKS):
            if name == 'TriggerAddAction' and len(args) == 2 and code_of(args[1], k) in revive:
                action_of.setdefault(al.resolve(args[0], k), set()).add(code_of(args[1], k))
    timers, arrays = {}, {}
    for k, l in enumerate(lines, 1):
        if 'TimerExpireEvent' not in l:
            continue
        for name, args, _spans in _calls(l, LINKS):
            if name != 'TriggerAddAction' and len(args) == 2 and al.resolve(args[0], k) in action_of:
                whole, base, _lit = _timer_key(al.resolve(args[1], k))
                runs = action_of[al.resolve(args[0], k)]
                timers.setdefault(whole, set()).update(runs)
                if base:
                    arrays.setdefault(base, set()).update(runs)

    def timer_runs(expr, k):
        whole, base, literal = _timer_key(al.resolve(expr, k))
        if base in arrays and (whole in timers or not literal):
            return arrays[base]
        if whole in timers and RX_REVIVE_NAME.search(whole):
            return timers[whole]
        return None

    sites, seen, covered = [], set(), set()
    for k, l in enumerate(lines, 1):
        if not any(w in l for w in WAITS):
            continue
        fn = owner.get(k)
        for name, args, spans in _calls(l, WAITS):
            at = WAITS[name]
            if at >= len(spans):
                continue
            why, runs = None, None
            callback = code_of(args[3], k) if name == 'TimerStart' and len(args) == 4 else None
            if fn in last and k <= last[fn] and name in ('TriggerSleepAction', 'PolledWait'):
                why, runs = 'wait in %s' % fn, ({fn} if fn in revive else set()) | via.get(fn, set())
            elif callback in revive:
                why, runs = 'timer that runs %s' % callback, {callback}
            elif name in ('StartTimerBJ', 'TimerStart') and args and timer_runs(args[0], k):
                why, runs = 'timer %s' % args[0], timer_runs(args[0], k)
            if why and (k, spans[at][0]) not in seen:
                seen.add((k, spans[at][0]))
                covered |= runs
                sites.append((k - 1, spans[at][0], spans[at][1], fn, why))
    return sites, sorted(revive), sorted(revive - covered)


ITEM_MAKE = {'CreateItem': 1, 'CreateItemLoc': 1, 'UnitAddItemById': 1, 'UnitAddItemByIdSwapped': 1,
             'UnitAddItemToSlotById': 1, 'AddItemToStock': 1, 'AddItemToAllStock': 1, 'RandomDistChoose': 1}
ITEM_TAKE = {'RemoveItem': 1, 'UnitRemoveItem': 1, 'UnitRemoveItemFromSlot': 1, 'UnitRemoveItemSwapped': 1,
             'UnitRemoveItemFromSlotSwapped': 1}
RX_DEATH = re.compile(r'\b(?:GetDyingUnit|GetKillingUnit|GetDyingItem)\b')
RANDOM = {'GetRandomInt': 'GetRandomInt', 'GetRandomReal': 'GetRandomReal'}
OPS = {'<': 1, '<=': 2, '>': 3, '>=': 4, '==': 5, '!=': 6}
FLIP = {'<': '>', '<=': '>=', '>': '<', '>=': '<=', '==': '==', '!=': '!='}
RX_OP_AFTER = re.compile(r'\s*(<=|>=|==|!=|<|>)')
RX_OP_BEFORE = re.compile(r'(<=|>=|==|!=|<|>)\s*$')
RX_RANDOM_SET = re.compile(r'^\s*set\s+([\w\[\]().+\-* ]+?)\s*=\s*(GetRandom(?:Int|Real))\s*\((.*)\)\s*(?://.*)?$')
STOP_WORDS = ('and', 'or', 'then', 'not', 'if', 'elseif', 'return')


def _code_part(line):
    i, n = 0, len(line)
    while i < n:
        c = line[i]
        if c in '"\'':
            i = _skip(line, i)
            continue
        if c == '/' and line.startswith('//', i):
            return line[:i]
        i += 1
    return line.rstrip('\r\n')


def _operand_after(code, i):
    while i < len(code) and code[i] in ' \t':
        i += 1
    start, depth, j = i, 0, i
    while j < len(code):
        c = code[j]
        if c in '"\'':
            j = _skip(code, j)
            continue
        if c == '(':
            depth += 1
        elif c in '),':
            if depth == 0:
                break
            if c == ')':
                depth -= 1
        elif depth == 0 and (c.isalpha()) and (j == 0 or not (code[j - 1].isalnum() or code[j - 1] == '_')):
            m = re.match(r'(and|or|then)\b', code[j:])
            if m:
                break
        j += 1
    end = j
    while end > start and code[end - 1] in ' \t':
        end -= 1
    return (start, end) if end > start else None


def _operand_before(code, i):
    end = i
    while end > 0 and code[end - 1] in ' \t':
        end -= 1
    depth, j = 0, end - 1
    while j >= 0:
        c = code[j]
        if c == ')':
            depth += 1
        elif c in '(,':
            if depth == 0:
                break
            if c == '(':
                depth -= 1
        elif c in '"\'':
            return None
        elif c == '=' and depth == 0 and (j == 0 or code[j - 1] not in '<>=!') and \
                (j + 1 >= len(code) or code[j + 1] != '='):
            break
        elif depth == 0 and c.isalpha():
            k = j
            while k > 0 and (code[k - 1].isalnum() or code[k - 1] == '_'):
                k -= 1
            if code[k : j + 1] in STOP_WORDS and (
                j + 1 >= len(code) or not (code[j + 1].isalnum() or code[j + 1] == '_')
            ):
                break
            j = k
        j -= 1
    start = j + 1
    while start < end and code[start] in ' \t':
        start += 1
    return (start, end) if end > start else None


def _alone_before(code, i):
    k = i
    while k > 0 and code[k - 1] in ' \t':
        k -= 1
    if k == 0 or code[k - 1] in '(,':
        return True
    m = re.search(r'(\w+)$', code[:k])
    return bool(m and m.group(1) in STOP_WORDS)


def _alone_after(code, i):
    k = i
    while k < len(code) and code[k] in ' \t':
        k += 1
    return k >= len(code) or code[k] in '),' or bool(re.match(r'(and|or|then)\b', code[k:]))


def _comparisons(code, spans):
    out = []
    for s, e in spans:
        m = RX_OP_AFTER.match(code, e)
        if m and _alone_before(code, s):
            o = _operand_after(code, m.end())
            if o:
                out.append((s, o[1], m.group(1), code[o[0]:o[1]]))
            continue
        m = RX_OP_BEFORE.search(code[:s])
        if m and _alone_after(code, e):
            o = _operand_before(code, m.start())
            if o:
                out.append((o[0], e, FLIP[m.group(1)], code[o[0]:o[1]]))
    return out


def _blocks(lines, k, end):
    depth, branch, final, where = 0, [], [], 'branch'
    for j in range(k + 1, end + 1):
        s = _code_part(lines[j - 1]).strip()
        if re.match(r'if\b', s) and not re.match(r'if\b.*\bendif\b', s):
            depth += 1
        elif s.startswith('endif'):
            if depth == 0:
                break
            depth -= 1
        elif depth == 0 and re.match(r'elseif\b', s):
            where = 'skip'
            continue
        elif depth == 0 and re.match(r'else\b', s):
            where = 'else'
            continue
        if where == 'branch':
            branch.append(j)
        elif where == 'else':
            final.append(j)
    return branch, final


def chance_sites(text, tree):
    lines = _lines(text)
    funcs = _functions(tree)
    by_name = dict((f.name, f) for f in funcs)

    def body(f):
        return lines[f.line - 1:f.end_line]

    makes = set(f.name for f in funcs if any(swap_calls.sitios(l, ITEM_MAKE) for l in body(f)))
    for _round in range(2):
        names = dict((n, n) for n in makes)
        makes |= set(f.name for f in funcs if f.name not in makes and
                     any(any(n in l for n in names) and swap_calls.sitios(l, names) for l in body(f)))
    mk = dict((n, n) for n in makes)

    def creates(line_numbers):
        return any(swap_calls.sitios(lines[j - 1], ITEM_MAKE) or
                   (any(n in lines[j - 1] for n in mk) and swap_calls.sitios(lines[j - 1], mk))
                   for j in line_numbers)

    def kind_of(f):
        src = ''.join(body(f))
        if RX_DEATH.search(src):
            return 'drop'
        if any(swap_calls.sitios(l, ITEM_TAKE) for l in body(f)):
            return 'craft'
        return 'drop'

    def direction(f, k):
        s = _code_part(lines[k - 1]).strip()
        if not re.match(r'(?:if|elseif)\b', s):
            return None
        branch, final = _blocks(lines, k, f.end_line)
        yes, other = creates(branch), creates(final)
        if yes and not other:
            return False
        if other and not yes and not re.match(r'elseif\b', s):
            return True
        return None

    conds = {}
    for f in funcs:
        if f.name not in makes:
            continue
        for k in range(f.line + 1, f.end_line):
            l = lines[k - 1]
            if '()' not in l:
                continue
            for m in re.finditer(r'\b(\w+)\s*\(\s*\)', _code_part(l)):
                g = by_name.get(m.group(1))
                if g is None or g.return_type != 'boolean' or g.params:
                    continue
                d = direction(f, k)
                if d is not None:
                    conds.setdefault(g.name, []).append((f, k, d))
    codes = {}

    def code_at(j):
        c = codes.get(j)
        if c is None:
            c = codes[j] = _code_part(lines[j - 1])
        return c

    drawn = {}

    def draws(g):
        d = drawn.get(g.name)
        if d is None:
            d = drawn[g.name] = []
            for j in range(g.line + 1, g.end_line):
                if 'GetRandom' not in lines[j - 1]:
                    continue
                m = RX_RANDOM_SET.match(code_at(j))
                if not m:
                    continue
                arg = '(' + m.group(3) + ')'
                a = _args(arg, 0)
                if a is None or len(a[0]) != 2:
                    continue
                lo, hi = (arg[x:y].strip() for x, y in a[0])
                d.append((j, m.group(1).strip(), m.group(2) == 'GetRandomInt', lo, hi))
        return d

    out, groups = [], {}
    for f in funcs:
        owners = []
        if f.name in makes:
            owners.append((f, None, None))
        if f.name in conds:
            ds = set(d for _c, _k, d in conds[f.name])
            if len(ds) == 1:
                owners += [(c, k, d) for c, k, d in conds[f.name]]
        if not owners:
            continue
        for k in range(f.line + 1, f.end_line):
            code = code_at(k)
            if not code.strip() or not any(c in code for c in '<>=!'):
                continue
            found = []
            if 'GetRandom' in code:
                for ini_, fim_, name in swap_calls.sitios(code, RANDOM):
                    a = _args(code, code.index('(', fim_))
                    if a is None or len(a[0]) != 2:
                        continue
                    lo, hi = (code[x:y].strip() for x, y in a[0])
                    for cs, ce, op, x in _comparisons(code, [(ini_, a[1] + 1)]):
                        found.append((cs, ce, op, x, code[ini_:a[1] + 1], lo, hi, name == 'GetRandomInt', None))
            for c, ck, _d in owners:
                upto = k if c is f else ck
                for j, var, is_int, lo, hi in reversed(draws(c)):
                    if j >= upto or var not in code:
                        continue
                    if code.lstrip().startswith('set ' + var):
                        break
                    spans = [(mm.start(), mm.end()) for mm in re.finditer(re.escape(var) + r'(?![\w\[])', code)
                             if mm.start() == 0 or not (code[mm.start() - 1].isalnum() or code[mm.start() - 1] == '_')]
                    for cs, ce, op, x in _comparisons(code, spans):
                        found.append((cs, ce, op, x, var, lo, hi, is_int, (c.name, j)))
                    break
            for cs, ce, op, x, v, lo, hi, is_int, group in found:
                if f.name in makes:
                    d, kf = direction(f, k), f
                else:
                    d, kf = owners[-1][2], owners[-1][0]
                if d is None or (op in ('==', '!=') and not is_int):
                    continue
                kind = kind_of(kf)
                rep = 'QoL_Roll%s(%s, %s, %s, %s, %d, %s, QoL_%s)' % ('I' if is_int else 'R', v, lo, hi, x, OPS[op],
                                                                       'true' if d else 'false', kind)
                out.append((k - 1, cs, ce, rep, kind, f.name))
                if group:
                    groups.setdefault(group, []).append((len(out) - 1, op, x, lo, hi))
    drop_idx = set()
    for group, cmps in groups.items():
        rows = [out[i][0] for i, *_r in cmps]
        if len(rows) != len(set(rows)) or sum(1 for _i, op, _x, _lo, _hi in cmps if op == '==') >= 2:
            drop_idx |= set(i for i, *_r in cmps)
            continue
        try:
            lo, hi = int(cmps[0][3]), int(cmps[0][4])
            n = hi - lo + 1
            cover = 0
            for _i, op, x, _lo, _hi in cmps:
                x = float(x)
                cover = max(cover, {'<': x - lo, '<=': x - lo + 1, '>': hi - x, '>=': hi - x + 1, '==': 1,
                                    '!=': n - 1}[op])
            if len(cmps) > 1 and sum(1 for _i, op, *_r in cmps if op in ('==', '!=')) == 0 and cover >= n:
                drop_idx |= set(i for i, *_r in cmps)
        except ValueError:
            pass
    out = [x for i, x in enumerate(out) if i not in drop_idx]
    keep, taken = [], {}
    for s in sorted(out, key=lambda x: (x[0], x[1])):
        prev = taken.get(s[0], -1)
        if s[1] >= prev:
            keep.append(s)
            taken[s[0]] = s[2]
    return keep


NAME_CALLS = {'GetPlayerName': 'GetPlayerName', 'StringCase': 'StringCase'}


def vip_sites(text):
    out = []
    for k, l in enumerate(_lines(text)):
        if 'GetPlayerName' not in l or '"' not in l:
            continue
        code = _code_part(l)
        spans = []
        for ini, fim, name in swap_calls.sitios(code, NAME_CALLS):
            a = _args(code, code.index('(', fim))
            if a is None or not a[0]:
                continue
            first = code[a[0][0][0]:a[0][0][1]].strip()
            if name == 'GetPlayerName' or first.startswith('GetPlayerName'):
                spans.append((ini, a[1] + 1))
        spans = [s for s in spans if not any(o != s and o[0] <= s[0] and s[1] <= o[1] for o in spans)]
        for cs, ce, op, x in _comparisons(code, spans):
            if op in ('==', '!=') and re.match(r'^"(?:[^"\\]|\\.)*"$', x.strip()) and 'WorldEdit' not in x:
                out.append((k, cs, ce, '(true)' if op == '==' else '(false)', x.strip()[1:-1]))
    return out


def _apply_edits(text, edits):
    lines = _lines(text)
    by_line = {}
    for k, s, e, rep in edits:
        by_line.setdefault(k, []).append((s, e, rep))
    for k, xs in by_line.items():
        l = lines[k]
        for s, e, rep in sorted(xs, reverse=True):
            l = l[:s] + rep + l[e:]
        lines[k] = l
    return ''.join(lines)


ROLL = '''function QoL_RollI takes integer v, integer lo, integer hi, real x, integer op, boolean inv, real m returns boolean
    local integer n = hi - lo + 1
    local integer s = 0
    local integer t
    if n <= 0 then
        return false
    endif
    if op == 1 then
        set s = R2I(x - 0.0001) - lo + 1
    elseif op == 2 then
        set s = R2I(x) - lo + 1
    elseif op == 3 then
        set s = hi - R2I(x)
    elseif op == 4 then
        set s = hi - R2I(x - 0.0001)
    elseif op == 5 then
        if x >= lo and x <= hi then
            set s = 1
        endif
    else
        set s = n
        if x >= lo and x <= hi then
            set s = n - 1
        endif
    endif
    set s = IMaxBJ(0, IMinBJ(n, s))
    if inv then
        set t = n - R2I(RMinBJ(I2R(n), I2R(n - s) * m + 0.5))
    else
        set t = R2I(RMinBJ(I2R(n), I2R(s) * m + 0.5))
    endif
    return v - lo < t
endfunction
function QoL_RollR takes real v, real lo, real hi, real x, integer op, boolean inv, real m returns boolean
    local real n = hi - lo
    local real s
    if n <= 0 then
        return false
    endif
    if op <= 2 then
        set s = x - lo
    else
        set s = hi - x
    endif
    set s = RMaxBJ(0, RMinBJ(n, s))
    if inv then
        set s = n - RMinBJ(n, (n - s) * m)
    else
        set s = RMinBJ(n, s * m)
    endif
    return v - lo < s
endfunction'''


def _count(text, calls):
    return sum(swap_calls.pluralize(text, calls).values())


def _read(path):
    from doctor.fix import single_player
    a, sc, _strings = single_player.read_map(path)
    return a, sc


def scan(path):
    out = {'language': None, 'script': None, 'supported': False, 'reason': None, 'defaults': dict(DEFAULTS)}
    try:
        _a, sc = _read(path)
    except BaseException as e:
        if isinstance(e, KeyboardInterrupt):
            raise
        out['reason'] = 'The map cannot be read (%s).' % unprotect._error(e)
        return out
    out['language'], out['script'] = sc['language'], sc['file']
    if sc['language'] != 'jass' or sc['compiled'] or sc['bytes'] is None:
        out['reason'] = ('The script is compiled by the KK platform: port the map first.' if sc['compiled'] else
                         'This version edits JASS scripts; the map script is %s.' % (sc['language'] or 'unreadable'))
        return out
    text = sc['bytes'].decode('utf-8', 'surrogateescape')
    if MARK in text:
        out['reason'] = 'The map already has the QoL edits of the Doctor: edit the original map instead.'
        out['done'] = True
        return out
    try:
        tree = jass_ast.parse(text)
    except jass_ast.JassSyntaxError as e:
        out['reason'] = 'The script does not parse (%s).' % e
        if re.search(r'(?m)^\s*(?:scope|library|struct|interface|module)\s+\w', text):
            try:
                detail = jass_ast.vjass_summary(jass_ast.parse_vjass(text))
            except jass_ast.JassSyntaxError as ev:
                detail = 'vJass: %s' % ev
            out['reason'] = ('The script still has vJass code (scope, library, struct) that was never compiled, so '
                             'the game cannot run it (%s).' % detail)
        return out
    sites, revive, untouched = respawn_sites(text, tree)
    chances = chance_sites(text, tree)
    out['supported'] = True
    out['found'] = {
        'xp_calls': _count(text, XP_CALLS),
        'xp_set': _count(text, SET_XP),
        'gold_script': len(re.findall(r'PLAYER_STATE_RESOURCE_(?:GOLD|LUMBER)', text)),
        'save_load': bool(RX_SAVE.search(text)),
        'shake_calls': _count(text, SHAKE_CALLS),
        'fog_calls': _count(text, FOG_CALLS),
        'revive_functions': len(revive),
        'revive_waits': len(sites),
        'revive_untouched': untouched[:20],
        'drop_chances': sum(1 for c in chances if c[4] == 'drop'),
        'craft_chances': sum(1 for c in chances if c[4] == 'craft'),
        'vip_names': sorted(set(v[4] for v in vip_sites(text)))[:30],
        'vip_checks': len(vip_sites(text)),
        'kk_mall': bool(re.search(r'DzAPI_Map_(?:HasMallItem|GetMapLevel|GetPlatformVIP|IsPlatformVIP)', text)),
    }
    return out


def _real(v):
    return '%.4f' % float(v)


def options_of(options):
    out = dict(DEFAULTS)
    for k, v in (options or {}).items():
        if k not in DEFAULTS or v is None or v == '':
            continue
        if isinstance(DEFAULTS[k], bool):
            out[k] = str(v).lower() in ('1', 'true', 'yes', 'on')
        else:
            lo, hi = LIMITS[k]
            out[k] = min(hi, max(lo, float(v)))
    return out


def layer(o):
    g, f, init = [], [], []
    players = '    loop\n        exitwhen i >= bj_MAX_PLAYERS\n%s        set i = i + 1\n    endloop\n    set i = 0\n'
    if o['xp'] != 1:
        g.append('    real QoL_xp = %s' % _real(o['xp']))
        f.append('''function QoL_HandicapXP takes player p, real v returns nothing
    call SetPlayerHandicapXP(p, v * QoL_xp)
endfunction
function QoL_HandicapXPBJ takes player p, real percent returns nothing
    call SetPlayerHandicapXPBJ(p, percent * QoL_xp)
endfunction
function QoL_AddHeroXP takes unit u, integer n, boolean show returns nothing
    if n > 0 then
        set n = R2I(RMinBJ(I2R(n) * QoL_xp, 2000000000.))
    endif
    call AddHeroXP(u, n, show)
endfunction
function QoL_AddHeroXPSwapped takes integer n, unit u, boolean show returns nothing
    call QoL_AddHeroXP(u, n, show)
endfunction''')
        init.append(players % '        call SetPlayerHandicapXP(Player(i), GetPlayerHandicapXP(Player(i)) * QoL_xp)\n')
    if o['gold'] != 1 or o['lumber'] != 1:
        g += ['    real QoL_gold = %s' % _real(o['gold']), '    real QoL_lumber = %s' % _real(o['lumber']),
              '    integer array QoL_last']
        f.append('''function QoL_Gain takes nothing returns nothing
    local player p = GetTriggerPlayer()
    local playerstate s = GetEventPlayerState()
    local integer k = GetPlayerId(p) * 2
    local real m = QoL_gold
    local integer v = GetPlayerState(p, s)
    if s == PLAYER_STATE_RESOURCE_LUMBER then
        set k = k + 1
        set m = QoL_lumber
    endif
    if v > QoL_last[k] and m != 1. then
        set v = R2I(RMaxBJ(RMinBJ(I2R(QoL_last[k]) + I2R(v - QoL_last[k]) * m, 1000000000.), 0.))
        set QoL_last[k] = v
        call DisableTrigger(GetTriggeringTrigger())
        call SetPlayerState(p, s, v)
        call EnableTrigger(GetTriggeringTrigger())
    endif
    set QoL_last[k] = GetPlayerState(p, s)
    set p = null
    set s = null
endfunction''')
        init.append('    set t = CreateTrigger()\n' + players % (
            '        set QoL_last[i * 2] = GetPlayerState(Player(i), PLAYER_STATE_RESOURCE_GOLD)\n'
            '        set QoL_last[i * 2 + 1] = GetPlayerState(Player(i), PLAYER_STATE_RESOURCE_LUMBER)\n'
            '        call TriggerRegisterPlayerStateEvent(t, Player(i), PLAYER_STATE_RESOURCE_GOLD, '
            'GREATER_THAN_OR_EQUAL, 0)\n'
            '        call TriggerRegisterPlayerStateEvent(t, Player(i), PLAYER_STATE_RESOURCE_LUMBER, '
            'GREATER_THAN_OR_EQUAL, 0)\n') + '    call TriggerAddAction(t, function QoL_Gain)\n')
    if o['respawn'] != 1:
        g.append('    real QoL_respawn = %s' % _real(o['respawn']))
    if o['drop'] != 1 or o['craft'] != 1:
        g += ['    real QoL_drop = %s' % _real(o['drop']), '    real QoL_craft = %s' % _real(o['craft'])]
        f.append(ROLL)
    if o['noshake'] or o['noshake_default']:
        g.append('    boolean array QoL_still')
        f.append('''function QoL_EQNoise takes player p, real m returns nothing
    if not QoL_still[GetPlayerId(p)] then
        call CameraSetEQNoiseForPlayer(p, m)
    endif
endfunction
function QoL_SourceNoise takes real m, real v returns nothing
    if not QoL_still[GetPlayerId(GetLocalPlayer())] then
        call CameraSetSourceNoise(m, v)
    endif
endfunction
function QoL_TargetNoise takes real m, real v returns nothing
    if not QoL_still[GetPlayerId(GetLocalPlayer())] then
        call CameraSetTargetNoise(m, v)
    endif
endfunction
function QoL_SourceNoiseEx takes real m, real v, boolean b returns nothing
    if not QoL_still[GetPlayerId(GetLocalPlayer())] then
        call CameraSetSourceNoiseEx(m, v, b)
    endif
endfunction
function QoL_TargetNoiseEx takes real m, real v, boolean b returns nothing
    if not QoL_still[GetPlayerId(GetLocalPlayer())] then
        call CameraSetTargetNoiseEx(m, v, b)
    endif
endfunction
function QoL_NoShake takes nothing returns nothing
    local integer k = GetPlayerId(GetTriggerPlayer())
    set QoL_still[k] = not QoL_still[k]
    if QoL_still[k] then
        if GetLocalPlayer() == GetTriggerPlayer() then
            call CameraSetSourceNoise(0, 0)
            call CameraSetTargetNoise(0, 0)
        endif
        call DisplayTimedTextToPlayer(GetTriggerPlayer(), 0, 0, 5, "Camera shakes off (-noshake turns them back on).")
    else
        call DisplayTimedTextToPlayer(GetTriggerPlayer(), 0, 0, 5, "Camera shakes on.")
    endif
endfunction''')
        init.append('    set t = CreateTrigger()\n' + players % (
            ('        set QoL_still[i] = true\n' if o['noshake_default'] else '') +
            '        call TriggerRegisterPlayerChatEvent(t, Player(i), "-noshake", true)\n') +
            '    call TriggerAddAction(t, function QoL_NoShake)\n')
    if o['reveal']:
        f.append('''function QoL_FogEnable takes boolean b returns nothing
    call FogEnable(false)
endfunction
function QoL_FogMaskEnable takes boolean b returns nothing
    call FogMaskEnable(false)
endfunction
function QoL_FogEnableOn takes nothing returns nothing
    call FogEnable(false)
endfunction
function QoL_FogEnableOff takes nothing returns nothing
    call FogEnable(false)
endfunction
function QoL_FogMaskEnableOn takes nothing returns nothing
    call FogMaskEnable(false)
endfunction
function QoL_FogMaskEnableOff takes nothing returns nothing
    call FogMaskEnable(false)
endfunction''')
        init.append('    call FogEnable(false)\n    call FogMaskEnable(false)\n')
    head = ['//===========================================================================',
            "// Devo's Map Doctor: the quality of life edits (the QoL tab).",
            '//===========================================================================']
    body = '\n'.join(head + f) + '\n' if f else '\n'.join(head) + '\n'
    body += ('function QoL_Init takes nothing returns nothing\n    local integer i = 0\n    local trigger t = null\n' +
             ''.join(init) + '    set t = null\nendfunction\n')
    return g, body, ['    call QoL_Init()']


def _rename(text, calls):
    new, info = swap_calls.applies(text, calls)
    if info['failures']:
        raise ValueError('; '.join(info['failures']))
    return new, info['swapped']


def edit(text, o, rep):
    from doctor.fix import map_rewrite
    done = {}
    tree = jass_ast.parse(text)
    clash = sorted(n for n in tree.function_index if n.startswith(PREFIX + '_'))
    if clash:
        raise ValueError('the script already declares %s' % ', '.join(clash[:3]))
    edits = []
    if o['respawn'] != 1:
        sites, revive, untouched = respawn_sites(text, tree)
        lines = _lines(text)
        edits += [(k, s, e, ' (' + lines[k][s:e].strip() + ') * QoL_respawn') for k, s, e, _fn, _why in sites]
        rep['respawn'] = {'sites': [(fn, why) for _k, _s, _e, fn, why in sites], 'revive': revive,
                          'untouched': untouched}
    if o['drop'] != 1 or o['craft'] != 1:
        chances = [c for c in chance_sites(text, tree) if o[c[4]] != 1]
        edits += [(k, s, e, r) for k, s, e, r, _kind, _fn in chances]
        rep['chances'] = [(kind, fn) for _k, _s, _e, _r, kind, fn in chances]
    if o['vip']:
        vips = vip_sites(text)
        edits += [(k, s, e, r) for k, s, e, r, _n in vips]
        rep['vip'] = sorted(set(n for _k, _s, _e, _r, n in vips))
        done['vip'] = len(vips)
    taken = {}
    for k, s, e, _r in sorted(edits):
        if s < taken.get(k, -1):
            raise ValueError('two edits overlap on line %d' % (k + 1))
        taken[k] = e
    text = _apply_edits(text, edits)
    if o['xp'] != 1:
        text, done['xp'] = _rename(text, XP_CALLS)
    if o['noshake'] or o['noshake_default']:
        text, done['shake'] = _rename(text, SHAKE_CALLS)
    if o['reveal']:
        text, done['fog'] = _rename(text, FOG_CALLS)
    tree = jass_ast.parse(text)
    g, f, end = layer(o)
    first = min((x.line for x in _functions(tree)), default=None)
    if first is None:
        raise ValueError('the script has no function')
    lines = _lines(text)
    nl = '\r\n' if text.count('\r\n') * 2 > text.count('\n') else '\n'
    lines[first - 1:first - 1] = [l + nl for l in f.rstrip('\n').split('\n')]
    text = ''.join(lines)
    new_text = map_rewrite.insert(text, jass_ast.parse(text), g, '', (), end)
    jass_ast.parse(new_text)
    return new_text, done


def fix(path_in, path_out, options=None, progress=None):
    from doctor.fix import map_rewrite
    p = progress or _nothing
    o = options_of(options)
    rep = {'state': 'failed', 'lines': [], 'options': o}

    def stop(state, why):
        rep['state'] = state
        rep['lines'] = [('bad' if state == 'failed' else 'warn', why)]
        return rep

    if o == DEFAULTS:
        return stop('nothing_to_do', 'No QoL edit was chosen.')
    p('Reading the map')
    try:
        _a, sc = _read(path_in)
    except BaseException as e:
        if isinstance(e, KeyboardInterrupt):
            raise
        return stop('failed', 'The map cannot be read (%s).' % unprotect._error(e))
    if sc['language'] != 'jass' or sc['compiled'] or sc['bytes'] is None:
        return stop('refused', 'This version edits JASS scripts only (the map script is %s).'
                    % ('compiled by the KK platform: port it first' if sc['compiled'] else sc['language'] or
                       'unreadable'))
    text = sc['bytes'].decode('utf-8', 'surrogateescape')
    if MARK in text:
        return stop('refused', 'The map already has the QoL edits of the Doctor: edit the original map instead.')
    p('Editing the script')
    try:
        new_text, done = edit(text, o, rep)
    except (ValueError, jass_ast.JassSyntaxError) as e:
        return stop('refused', 'The script cannot take the QoL edits (%s).' % e)
    new_bytes = new_text.encode('utf-8', 'surrogateescape')
    p('Running pjass')
    rep['pjass'] = map_rewrite.gate(sc['bytes'], new_bytes)
    if rep['pjass']['state'] == 'failed':
        return stop('refused', 'pjass does not accept the edited script (%s).' % rep['pjass'].get('new'))
    try:
        w = map_rewrite.write(path_in, path_out, [(sc['file'], new_bytes)] + [(c, new_bytes) for c in sc['copies']], p)
    except Exception as e:
        return stop('failed', 'The map could not be written (%s).' % unprotect._error(e))
    rep.update(state='done', file=path_out, same_files=w['same_files'], script=sc['file'])
    rep['lines'] = report(o, done, rep, text)
    return rep


def report(o, done, rep, text):
    out = [('title', 'QoL edits written'),
           ('good', 'The script went back into the map; every other file is the same (%d).' % rep['same_files'])]
    pj = rep.get('pjass') or {}
    if pj.get('state') == 'passed':
        out.append(('good', 'pjass accepts the edited script.'))
    elif pj.get('state') == 'original_fails':
        out.append(('warn', 'pjass already refused the original script; the edits add no new complaint.'))
    elif pj.get('state') == 'skipped':
        out.append(('warn', pj.get('note') or 'pjass was not found'))
    if o['xp'] != 1:
        out.append(('info', 'Experience x%g: the XP handicap of every player (kills), and %d call(s) of the map that '
                            'give XP or set the handicap.' % (o['xp'], done.get('xp', 0))))
        n = _count(text, SET_XP)
        if n:
            out.append(('warn', '%d call(s) set a hero\'s XP or level directly (a custom XP system): those are left '
                                'as they are.' % n))
    if o['gold'] != 1 or o['lumber'] != 1:
        out.append(('info', 'Gold x%g, lumber x%g, on every gain of every player.' % (o['gold'], o['lumber'])))
        if RX_SAVE.search(text):
            out.append(('warn', 'The map has a save/load code: gold a load gives back is a gain too, and gets '
                                'multiplied.'))
    if o['respawn'] != 1:
        r = rep.get('respawn') or {}
        sites = r.get('sites') or []
        if sites:
            out.append(('info', 'Hero revive time x%g: %d wait(s) or timer(s) in %d place(s).'
                        % (o['respawn'], len(sites), len(set(fn for fn, _w in sites)))))
            for fn, why in sites[:12]:
                out.append(('info', '  %s' % why))
        else:
            out.append(('warn', 'Hero revive time: no wait or timer of a revive was found (%d function(s) revive).'
                        % len(r.get('revive') or [])))
        if r.get('untouched'):
            out.append(('warn', 'Revive with nothing to shorten in: %s.' % ', '.join(r['untouched'][:8])))
    if o['noshake'] or o['noshake_default']:
        out.append(('info', '-noshake turns the camera shakes off and on (%d call(s) of the map rerouted)%s.'
                    % (done.get('shake', 0), '; every player starts with them off' if o['noshake_default'] else '')))
    if o['reveal']:
        out.append(('info', 'The map is revealed from the start (%d fog call(s) of the map rerouted).'
                    % done.get('fog', 0)))
    if o['drop'] != 1 or o['craft'] != 1:
        ch = rep.get('chances') or []
        for kind in ('drop', 'craft'):
            if o[kind] == 1:
                continue
            n = [fn for k, fn in ch if k == kind]
            if n:
                out.append(('info', '%s chance x%g: %d roll(s) in %d function(s).'
                            % ('Item drop' if kind == 'drop' else 'Craft success', o[kind], len(n), len(set(n)))))
            else:
                out.append(('warn', '%s chance: no roll of the map was found to change.'
                            % ('Item drop' if kind == 'drop' else 'Craft success')))
    if o['vip']:
        if done.get('vip'):
            out.append(('info', 'VIP for everyone: %d check(s) of a player name answer as for a listed name (%s).'
                        % (done['vip'], ', '.join((rep.get('vip') or [])[:8]))))
            out.append(
                ('warn', "The same name checks may guard the author's own commands: those open to everyone too.")
            )
        else:
            out.append(('warn', 'VIP: no check of a player name against a list was found.'))
    out.append(('warn', 'Test the map in game before sharing it.'))
    return out
