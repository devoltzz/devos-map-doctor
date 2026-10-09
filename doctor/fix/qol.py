# The quality of life edits of a map: experience, gold, lumber, item drop and craft chances, hero revive time, camera shakes, the map revealed and VIP by name, written into the map script.
import re

from doctor.fix import unprotect
from doctor.script import jass_ast
from doctor.port import swap_calls


PREFIX = 'QoL'
MARK = PREFIX + '_Init'
DEFAULTS = {'xp': 1.0, 'gold': 1.0, 'lumber': 1.0, 'respawn': 1.0, 'creep': 1.0, 'drop': 1.0, 'craft': 1.0,
            'noshake': False, 'noshake_default': False,
            'reveal': False, 'vip': False}
LIMITS = {
    'xp': (0.0, 100.0),
    'gold': (0.0, 100.0),
    'lumber': (0.0, 100.0),
    'respawn': (0.0, 10.0),
    'creep': (0.0, 10.0),
    'drop': (0.0, 100.0),
    'craft': (0.0, 100.0),
}
XP_CALLS = {'SetPlayerHandicapXP': PREFIX + '_HandicapXP', 'SetPlayerHandicapXPBJ': PREFIX + '_HandicapXPBJ',
            'AddHeroXP': PREFIX + '_AddHeroXP', 'AddHeroXPSwapped': PREFIX + '_AddHeroXPSwapped'}
SHAKE_CALLS = {'CameraSetEQNoiseForPlayer': PREFIX + '_EQNoise', 'CameraSetSourceNoise': PREFIX + '_SourceNoise',
               'CameraSetTargetNoise': PREFIX + '_TargetNoise', 'CameraSetSourceNoiseEx': PREFIX + '_SourceNoiseEx',
               'CameraSetTargetNoiseEx': PREFIX + '_TargetNoiseEx'}
FOG_CALLS = {'FogEnable': PREFIX + '_FogEnable', 'FogMaskEnable': PREFIX + '_FogMaskEnable',
             'FogEnableOn': PREFIX + '_FogEnableOn', 'FogEnableOff': PREFIX + '_FogEnableOff',
             'FogMaskEnableOn': PREFIX + '_FogMaskEnableOn', 'FogMaskEnableOff': PREFIX + '_FogMaskEnableOff'}
REVIVE = {'ReviveHero': 'ReviveHero', 'ReviveHeroLoc': 'ReviveHeroLoc'}
DIST_CALLS = {'RandomDistReset': PREFIX + '_DistReset', 'RandomDistAddItem': PREFIX + '_DistAdd'}
ALTAR = (('ReviveTimeFactor', 0.65), ('ReviveMaxTimeFactor', 2.0), ('HeroMaxReviveTime', 150.0))
MISC_FILE = 'war3mapMisc.txt'
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


RX_DELAY_IF = re.compile(r'^\s*(?:if|elseif)\s*\(?\s*(\w+)\s*(?:<=|<|==)\s*(?:0|0\.0*|\.0+)\s*\)?\s*then\s*$')
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
    wrappers = set()
    for f in funcs:
        code = [_code_part(lines[k - 1]).strip() for k in range(f.line + 1, f.end_line)]
        code = [c for c in code if c and not c.startswith('local ')]
        if f.name in revive and len(code) <= 4 and not any(w in ' '.join(code) for w in WAITS):
            wrappers.add(f.name)
    if wrappers:
        wnames = dict((n, n) for n in wrappers)
        for f in funcs:
            if f.name in wrappers:
                continue
            for k in range(f.line, f.end_line):
                l = lines[k - 1]
                if any(n in l for n in wnames) and swap_calls.sitios(l, wnames):
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

    local_timers = {}
    for f in funcs:
        for k in range(f.line + 1, f.end_line):
            l = lines[k - 1]
            if 'TimerExpireEvent' not in l:
                continue
            for name, args, _spans in _calls(l, LINKS):
                if name != 'TriggerRegisterTimerExpireEvent' or len(args) != 2:
                    continue
                trig = args[0].strip()
                if not re.match(r'^\w+$', trig):
                    continue
                rx = re.compile(
                    r'\bTriggerAdd(?:Action|Condition)\s*\(\s*%s\s*,\s*(?:Condition\s*\(\s*)?function\s+(\w+)'
                    % re.escape(trig)
                )
                for j in range(k + 1, f.end_line):
                    lj = _code_part(lines[j - 1])
                    if re.match(r'\s*set\s+%s\s*=' % re.escape(trig), lj):
                        break
                    m = rx.search(lj)
                    if m:
                        if m.group(1) in revive:
                            local_timers[(f.name, re.sub(r'\s+', '', args[1]))] = m.group(1)
                        break

    def timer_runs(expr, k):
        whole, base, literal = _timer_key(al.resolve(expr, k))
        if base in arrays and (whole in timers or not literal):
            return arrays[base]
        if whole in timers and RX_REVIVE_NAME.search(whole):
            return timers[whole]
        return None

    sites, seen, covered = [], set(), set()
    rnames = dict((n, n) for n in revive)
    for f in funcs:
        reals = [n for t, n in f.params if t == 'real']
        if not reals:
            continue
        for k in range(f.line + 1, f.end_line):
            m = RX_DELAY_IF.match(_code_part(lines[k - 1]))
            if not m or m.group(1) not in reals:
                continue
            branch, _final = _blocks(lines, k, f.end_line)
            hit = set()
            for j in branch:
                if swap_calls.sitios(lines[j - 1], REVIVE):
                    hit.add(f.name)
                elif any(n in lines[j - 1] for n in rnames):
                    hit |= set(n for _i, _j, n in swap_calls.sitios(lines[j - 1], rnames))
            if hit:
                at = max([f.line] + [d.line for d in f.locals])
                end = len(lines[at - 1].rstrip('\r\n'))
                if (at, end) not in seen:
                    seen.add((at, end))
                    covered |= hit
                    sites.append((at - 1, end, end, f.name, 'delay parameter %s of %s' % (m.group(1), f.name)))
                break
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
            elif name in ('StartTimerBJ', 'TimerStart') and args and (fn, re.sub(r'\s+', '', args[0])) in local_timers:
                callback = local_timers[(fn, re.sub(r'\s+', '', args[0]))]
                why, runs = 'timer that runs %s' % callback, {callback}
            elif name in ('StartTimerBJ', 'TimerStart') and args and timer_runs(args[0], k):
                why, runs = 'timer %s' % args[0], timer_runs(args[0], k)
            if why and (k, spans[at][0]) not in seen:
                seen.add((k, spans[at][0]))
                covered |= runs
                sites.append((k - 1, spans[at][0], spans[at][1], fn, why))
    return sites, sorted(revive - wrappers), sorted(revive - covered - wrappers)


CREEP_MAKE = {'CreateUnit': 1, 'CreateUnitAtLoc': 1, 'CreateUnitAtLocSaveLast': 1, 'CreateNUnitsAtLoc': 1,
              'CreateNUnitsAtLocFacingLocBJ': 1, 'BlzCreateUnitWithSkin': 1}
RX_POINT_VALUE = re.compile(r'\bGetUnitPointValue(?:ByType)?\s*\(')
RX_OWN_TYPE = re.compile(r'^\(?\s*GetUnitTypeId\s*\(\s*(?:GetDyingUnit|GetTriggerUnit)\s*\(\s*\)\s*\)\s*\)?$')
RX_TYPE_SET = re.compile(
    r'^\s*(?:set|local\s+integer)\s+(\w+)\s*=\s*(GetUnitTypeId\s*\(\s*(?:GetDyingUnit|GetTriggerUnit)'
    r'\s*\(\s*\)\s*\))\s*$'
)


RX_ADD_ACTION = re.compile(
    r'\bTriggerAdd(?:Action|Condition)\s*\(\s*(\w+)\s*,\s*(?:Condition\s*\(\s*)?(?:function\s+)?(\w+)'
)


def death_actions(text):
    dead = set(re.findall(r'\bTriggerRegister\w*Event\w*\s*\(\s*(\w+)\s*,[^\n]*?_DEATH\b', text))
    return set(f for t, f in RX_ADD_ACTION.findall(text) if t in dead)


def creep_sites(text, tree):
    lines = _lines(text)
    sites = []
    dead = death_actions(text)
    funcs = _functions(tree)
    respawners, makers = set(), set()
    for f in funcs:
        body = ''.join(_code_part(lines[k - 1]) for k in range(f.line, f.end_line))
        if any(c in body for c in CREEP_MAKE) and _calls(body, CREEP_MAKE):
            makers.add(f.name)
        if 'GetExpiredTimer' in body and 'PLAYER_NEUTRAL_AGGRESSIVE' in body and any(c in body for c in CREEP_MAKE):
            for name, args, _s in _calls(body, CREEP_MAKE):
                owner = args[2] if name.startswith('CreateNUnits') else args[0] if args else ''
                kind = args[1].strip() if len(args) > 1 else ''
                if 'PLAYER_NEUTRAL_AGGRESSIVE' in owner and not re.match(r"^(?:'.{4}'|\$?\d+|0x[0-9A-Fa-f]+)$",
                                                                       kind):
                    respawners.add(f.name)
    for f in funcs:
        own, waits = set(), []
        died = f.name in dead or 'GetDyingUnit' in ''.join(lines[f.line - 1:f.end_line])
        for k in range(f.line, f.end_line):
            code = _code_part(lines[k - 1])
            m = RX_TYPE_SET.match(code)
            if m:
                own.add(m.group(1))
            if any(w in code for w in WAITS):
                for name, args, spans in _calls(code, WAITS):
                    at = WAITS[name]
                    if at >= len(spans):
                        continue
                    if RX_POINT_VALUE.search(args[at]):
                        sites.append((k - 1, spans[at][0], spans[at][1], f.name, 'point value in %s' % f.name))
                    elif name == 'TimerStart' and len(args) == 4 and args[2].strip() == 'false' and \
                            'TimerGetRemaining' not in args[1]:
                        cb = re.match(r'^function\s+(\w+)$', args[3].strip())
                        lit = re.match(r'^\(?\s*(\d*\.?\d*)\s*\)?$', args[1].strip())
                        short = bool(lit and lit.group(1) not in ('', '.') and float(lit.group(1)) < 5)
                        named = cb and RX_REVIVE_NAME.search(cb.group(1) + ' ' + args[1]) and cb.group(1) in makers
                        if cb and cb.group(1) != f.name and (cb.group(1) in respawners or named) and not short:
                            sites.append((k - 1, spans[at][0], spans[at][1], f.name,
                                          'timer that runs %s' % cb.group(1)))
                    elif name in ('TriggerSleepAction', 'PolledWait'):
                        waits.append((k - 1, spans[at][0], spans[at][1]))
            if waits and died and any(c in code for c in CREEP_MAKE):
                for name, args, _spans in _calls(code, CREEP_MAKE):
                    t = args[1].strip() if len(args) > 1 else ''
                    if RX_OWN_TYPE.match(t) or t in own:
                        sites += [(wk, s, e, f.name, 'wait in %s' % f.name) for wk, s, e in waits]
                        waits = []
                        break
    out, seen = [], set()
    for x in sites:
        if (x[0], x[1]) not in seen:
            seen.add((x[0], x[1]))
            out.append(x)
    return out


ITEM_MAKE = {'CreateItem': 1, 'CreateItemLoc': 1, 'UnitAddItemById': 1, 'UnitAddItemByIdSwapped': 1,
             'UnitAddItemToSlotById': 1, 'AddItemToStock': 1, 'AddItemToAllStock': 1, 'RandomDistChoose': 1}
ITEM_TAKE = {'RemoveItem': 1, 'UnitRemoveItem': 1, 'UnitRemoveItemFromSlot': 1, 'UnitRemoveItemSwapped': 1,
             'UnitRemoveItemFromSlotSwapped': 1}
RX_ITEM_EVENT = re.compile(r'\b(?:GetSoldItem|GetManipulatedItem)\b')
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


RX_SCALE_AFTER = re.compile(r'\s*([*/])\s*(\d+\.?\d*|\.\d+)(?![\w.])')
RX_SCALE_BEFORE = re.compile(r'(?<![\w.])(\d+\.?\d*|\.\d+)\s*\*\s*$')


def _draw_span(code, s, e, real):
    f = 1.0
    while True:
        m = re.search(r'\bI2R\s*\(\s*$', code[:s])
        a = re.match(r'\s*\)', code[e:])
        if m and a:
            s, e, real = m.start(), e + a.end(), True
            continue
        m = re.search(r'\(\s*$', code[:s])
        if m and a:
            k = m.start()
            while k > 0 and code[k - 1] in ' \t':
                k -= 1
            if k == 0 or not (code[k - 1].isalnum() or code[k - 1] == '_'):
                s, e = m.start(), e + a.end()
                continue
        m = RX_SCALE_AFTER.match(code, e)
        if m and float(m.group(2)) > 0 and (m.group(1) == '*' or real or '.' in m.group(2)):
            c = float(m.group(2))
            f = f * c if m.group(1) == '*' else f / c
            real = real or '.' in m.group(2) or m.group(1) == '/'
            e = m.end()
            continue
        m = RX_SCALE_BEFORE.search(code[:s])
        if m and float(m.group(1)) > 0:
            k = m.start()
            while k > 0 and code[k - 1] in ' \t':
                k -= 1
            if k == 0 or code[k - 1] not in '*/':
                f *= float(m.group(1))
                s = m.start()
                real = real or '.' in m.group(1)
                continue
        break
    if f == 1.0:
        return s, e, lambda x: x
    if f >= 1:
        return s, e, lambda x: '((%s) / %r)' % (x, f)
    return s, e, lambda x: '((%s) * %r)' % (x, 1 / f)


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


RX_INT_LITERAL = re.compile(r"'(?:[^'\\]|\\.){4}'|\$[0-9A-Fa-f]{1,8}\b|0[xX][0-9A-Fa-f]{1,8}\b|\b[1-9]\d{8,9}\b")


def _literal_value(tok):
    if tok[0] == "'":
        b = jass_ast._unescape(tok[1:-1]).encode('latin-1', 'replace')
        return int.from_bytes(b, 'big') if len(b) == 4 else None
    if tok[0] == '$':
        return int(tok[1:], 16)
    if tok[:2] in ('0x', '0X'):
        return int(tok[2:], 16)
    return int(tok)


def item_values(archive):
    from doctor.data import objbin
    out = set()
    for name in ('war3map.w3t', 'war3mapSkin.w3t'):
        try:
            data = unprotect._read(archive, name)
            if not data:
                continue
            _ver, tables, _end = objbin.read_data(data, False)
        except Exception:
            continue
        for table in tables:
            for old, new, _mods in table:
                for s in (new, old):
                    b = s.encode('latin-1', 'replace')
                    if len(b) == 4 and b != b'\0\0\0\0':
                        out.add(int.from_bytes(b, 'big'))
    try:
        from doctor.data import slk
        data = unprotect._read(archive, 'Units\\ItemData.slk')
        if data:
            _header, rows = slk.parse_slk_bytes(data)
            for ident in rows:
                b = ident.encode('latin-1', 'replace') if isinstance(ident, str) else bytes(ident)
                if len(b) == 4:
                    out.add(int.from_bytes(b, 'big'))
    except Exception:
        pass
    return out


ITEM_ID_ARG = {'CreateItem': 0, 'CreateItemLoc': 0, 'UnitAddItemById': 1, 'UnitAddItemByIdSwapped': 0,
               'UnitAddItemToSlotById': 1, 'AddItemToStock': 1, 'AddItemToAllStock': 0, 'RemoveItemFromStock': 1}


def item_typing(lines, funcs, item_vals):
    vals = set(item_vals or ())
    names = dict((f.name, f.name) for f in funcs)
    by = dict((f.name, f) for f in funcs)
    codes = [_code_part(l) for l in lines]
    for c in codes:
        if not any(n in c for n in ITEM_ID_ARG):
            continue
        for ini, fim, name in swap_calls.sitios(c, ITEM_ID_ARG):
            a = _args(c, c.index('(', fim))
            if a and len(a[0]) > ITEM_ID_ARG[name]:
                s, e = a[0][ITEM_ID_ARG[name]]
                m = RX_INT_LITERAL.fullmatch(c[s:e].strip())
                if m:
                    vals.add(_literal_value(m.group(0)))

    def literal(code):
        return any(_literal_value(m.group(0)) in vals for m in RX_INT_LITERAL.finditer(code))

    glob, local = set(), dict((f.name, set()) for f in funcs)
    own = {}
    for f in funcs:
        own[f.name] = set(n for _t, n in f.params) | set(d.name for d in f.locals)

    def typed(expr, fname):
        e = expr.strip()
        m = RX_INT_LITERAL.fullmatch(e)
        if m:
            return _literal_value(m.group(0)) in vals
        m = re.match(r'^(\w+)(?:\s*\[.*\])?$', e)
        if not m:
            return False
        n = m.group(1)
        return n in local[fname] if n in own[fname] else n in glob

    if not vals:
        return literal, local, dict((f.name, set()) for f in funcs)
    for _round in range(4):
        before = len(glob) + sum(len(x) for x in local.values())
        for f in funcs:
            for k in range(f.line, f.end_line):
                c = codes[k - 1]
                if '=' in c:
                    m = re.match(r'\s*(?:set|local\s+\w+)\s+(\w+)\s*(?:\[.*?\])?\s*=\s*(.+?)\s*$', c)
                    if m and typed(m.group(2), f.name):
                        (local[f.name] if m.group(1) in own[f.name] else glob).add(m.group(1))
                if '(' in c:
                    for ini, fim, name in swap_calls.sitios(c, names):
                        g = by[name]
                        if not g.params:
                            continue
                        a = _args(c, c.index('(', fim))
                        if not a:
                            continue
                        for i, (s, e) in enumerate(a[0][:len(g.params)]):
                            if typed(c[s:e], f.name):
                                local[name].add(g.params[i][1])
        if len(glob) + sum(len(x) for x in local.values()) == before:
            break
    out = dict((f.name, local[f.name] | glob) for f in funcs)
    tables = dict((f.name, set()) for f in funcs)
    for f in funcs:
        mine = set(d.name for d in f.locals)
        for k in range(f.line, f.end_line):
            c = codes[k - 1]
            m = re.match(r'\s*(?:set|local\s+\w+)\s+(\w+)\s*=\s*(\w+)\s*\[', c)
            if m and m.group(1) in mine and m.group(2) in glob:
                tables[f.name].add(m.group(1))
    return literal, out, tables


def _handles_item(code, names):
    c = code.strip()
    if not (c.startswith('call ') or c.startswith('set ')):
        return False
    return bool(names & set(re.findall(r'[A-Za-z_]\w*', c)))


def chance_sites(text, tree, item_vals=None):
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
    _literal, _typed, tables = item_typing(lines, funcs, item_vals)
    keeps = set(f.name for f in funcs if f.name not in makes and tables.get(f.name) and
                'GetRandom' in ''.join(body(f)) and
                any(_handles_item(_code_part(l), tables[f.name]) for l in body(f)))

    def creates(line_numbers, f=None):
        for j in line_numbers:
            l = lines[j - 1]
            if swap_calls.sitios(l, ITEM_MAKE) or (any(n in l for n in mk) and swap_calls.sitios(l, mk)):
                return True
            if f is not None and f.name in keeps and _handles_item(_code_part(l), tables[f.name]):
                return True
        return False

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
        yes, other = creates(branch, f), creates(final, f)
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

    upgrades = set(f.name for f in funcs if f.name not in makes and f.name not in keeps and
                   RX_ITEM_EVENT.search(''.join(body(f))) and 'GetRandom' in ''.join(body(f)))

    def upgrade(f, k, op, cs, ce):
        code = _code_part(lines[k - 1])
        s = code.strip()
        if op not in ('<', '<=') or not re.match(r'if\b', s):
            return None
        cond = re.sub(r'^\s*if\b|\bthen\s*$', '', code).strip()
        while cond.startswith('(') and cond.endswith(')') and (_args(cond, 0) or (0, -1))[1] == len(cond) - 1:
            cond = cond[1:-1].strip()
        if cond != code[cs:ce].strip():
            return None
        branch, final = _blocks(lines, k, f.end_line)
        if not any(_code_part(lines[j - 1]).strip() for j in branch) or \
                not any(_code_part(lines[j - 1]).strip() for j in final):
            return None
        return False

    out, groups = [], {}
    for f in funcs:
        owners = []
        if f.name in makes or f.name in keeps or f.name in upgrades:
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
                    ds, de, conv = _draw_span(code, ini_, a[1] + 1, name == 'GetRandomReal')
                    for cs, ce, op, x in _comparisons(code, [(ds, de)]):
                        found.append((cs, ce, op, conv(x), code[ini_:a[1] + 1], lo, hi, name == 'GetRandomInt', None))
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
                up = False
                if f.name in makes or f.name in keeps:
                    d, kf = direction(f, k), f
                elif owners[-1][0] is not f:
                    d, kf = owners[-1][2], owners[-1][0]
                else:
                    d, kf, up = upgrade(f, k, op, cs, ce), f, True
                if d is None or (op in ('==', '!=') and not is_int):
                    continue
                kind = 'craft' if up else kind_of(kf)
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


RESTORE_CALLS = {'AdjustPlayerStateBJ': PREFIX + '_RestoreAdjust', 'SetPlayerStateBJ': PREFIX + '_RestoreSetBJ',
                 'SetPlayerState': PREFIX + '_RestoreSet'}


def restore_sites(text):
    out = []
    for k, l in enumerate(_lines(text)):
        if 'S2I' not in l or 'PLAYER_STATE_RESOURCE_' not in l:
            continue
        code = _code_part(l)
        for ini, fim, name in swap_calls.sitios(code, RESTORE_CALLS):
            a = _args(code, code.index('(', fim))
            if a is None or len(a[0]) != 3:
                continue
            args = [code[x:y] for x, y in a[0]]
            if any(re.search(r'\bS2I\s*\(', x) for x in args) and \
                    any(re.search(r'\bPLAYER_STATE_RESOURCE_(?:GOLD|LUMBER)\b', x) for x in args):
                out.append((k, ini, fim, RESTORE_CALLS[name]))
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


def dist_items(text):
    n = 0
    for l in _lines(text):
        if 'RandomDistAddItem' not in l:
            continue
        code = _code_part(l)
        for _i, fim, _n in swap_calls.sitios(code, {'RandomDistAddItem': 1}):
            a = _args(code, code.index('(', fim))
            if a and a[0] and code[a[0][0][0]:a[0][0][1]].strip().replace(' ', '') not in ('-1', '(-1)'):
                n += 1
    return n


def altar_misc(data, factor):
    text = data.decode('utf-8', 'surrogateescape') if data else ''
    nl = '\r\n' if '\r\n' in text or not text else '\n'
    lines = text.split(nl) if text else []
    sec = next((i for i, l in enumerate(lines) if l.strip().lower() == '[misc]'), None)
    if sec is None:
        lines = (lines + [''] if lines and lines[-1].strip() else lines) + ['[Misc]']
        sec = len(lines) - 1
    end = next((i for i in range(sec + 1, len(lines)) if lines[i].strip().startswith('[')), len(lines))
    while end > sec + 1 and not lines[end - 1].strip():
        end -= 1
    changes = {}
    for key, default in ALTAR:
        at = next((i for i in range(sec + 1, end) if lines[i].split('=', 1)[0].strip().lower() == key.lower()), None)
        old = default
        if at is not None:
            try:
                old = float(lines[at].split('=', 1)[1].split('//')[0].strip())
            except ValueError:
                old = default
        new = old * factor
        txt = '%s=%s' % (key, ('%.4f' % new).rstrip('0').rstrip('.') or '0')
        if at is None:
            lines.insert(end, txt)
            end += 1
        else:
            lines[at] = txt
        changes[key] = (old, new)
    out = nl.join(lines)
    if not out.endswith(nl):
        out += nl
    return out.encode('utf-8', 'surrogateescape'), changes


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
    if sc['language'] == 'lua' and sc['bytes'] is not None:
        text = sc['bytes'].decode('utf-8', 'surrogateescape')
        if MARK in text:
            out['reason'] = 'The map already has the QoL edits of the Doctor: edit the original map instead.'
            out['done'] = True
        elif '__ydwe' in text:
            out['reason'] = (
                'The map is a KK map ported by the Doctor\'s Lua route: its natives run inside the port\'s '
                'runtime, which the QoL edits do not reach yet. Edit the original map before the port.'
            )
        else:
            out['supported'] = True
            out['found'] = lua_found(text)
        return out
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
    chances = chance_sites(text, tree, item_values(_a))
    out['supported'] = True
    out['found'] = {
        'xp_calls': _count(text, XP_CALLS),
        'xp_set': _count(text, SET_XP),
        'gold_script': len(re.findall(r'PLAYER_STATE_RESOURCE_(?:GOLD|LUMBER)', text)),
        'save_load': bool(RX_SAVE.search(text) or restore_sites(text)),
        'shake_calls': _count(text, SHAKE_CALLS),
        'fog_calls': _count(text, FOG_CALLS),
        'revive_functions': len(revive),
        'revive_waits': len(sites),
        'revive_untouched': untouched[:20],
        'creep_waits': len(creep_sites(text, tree)),
        'drop_chances': sum(1 for c in chances if c[4] == 'drop'),
        'drop_tables': dist_items(text),
        'craft_chances': sum(1 for c in chances if c[4] == 'craft'),
        'vip_names': sorted(set(v[4] for v in vip_sites(text)))[:30],
        'vip_checks': len(vip_sites(text)),
        'kk_mall': bool(re.search(r'DzAPI_Map_(?:HasMallItem|GetMapLevel|GetPlatformVIP|IsPlatformVIP)', text)),
    }
    return out


LUA_HEAD = """-- Devo's Map Doctor: the quality of life edits (the QoL tab).
QoL = {xp = %(xp)s, gold = %(gold)s, lumber = %(lumber)s, drop = %(drop)s, craft = %(craft)s, respawn = %(respawn)s,
  creep = %(creep)s,
  reveal = %(reveal)s, noshake = %(noshake)s, still = {}, last = {}, dsum = 0}
do
  local Q = QoL
  -- the item rolls: the share of the draw that makes the item times m (100%% at most), as QoL_RollI/R of the JASS maps
  local function trunc(r) if r >= 0 then return math.floor(r) else return math.ceil(r) end end
  function Q.rollI(v, lo, hi, x, op, inv, m)
    lo, hi = trunc(lo), trunc(hi)
    local n = hi - lo + 1
    if n <= 0 then return false end
    local s
    if op == 1 then s = trunc(x - 0.0001) - lo + 1
    elseif op == 2 then s = trunc(x) - lo + 1
    elseif op == 3 then s = hi - trunc(x)
    elseif op == 4 then s = hi - trunc(x - 0.0001)
    elseif op == 5 then s = (x >= lo and x <= hi) and 1 or 0
    else s = (x >= lo and x <= hi) and n - 1 or n end
    s = math.max(0, math.min(n, s))
    local t
    if inv then t = n - trunc(math.min(n, (n - s) * m + 0.5)) else t = trunc(math.min(n, s * m + 0.5)) end
    return v - lo < t
  end
  function Q.rollR(v, lo, hi, x, op, inv, m)
    local n = hi - lo
    if n <= 0 then return false end
    local s
    if op <= 2 then s = x - lo else s = hi - x end
    s = math.max(0, math.min(n, s))
    if inv then s = n - math.min(n, (n - s) * m) else s = math.min(n, s * m) end
    return v - lo < s
  end
  if Q.xp ~= 1 then
    local handicap, add = SetPlayerHandicapXP, AddHeroXP
    SetPlayerHandicapXP = function(p, v) handicap(p, v * Q.xp) end
    AddHeroXP = function(u, n, show)
      if n > 0 then n = math.floor(math.min(n * Q.xp, 2000000000.0)) end
      add(u, n, show)
    end
  end
  if Q.drop ~= 1 then
    local reset, additem = RandomDistReset, RandomDistAddItem
    RandomDistReset = function() Q.dsum = 0 reset() end
    RandomDistAddItem = function(id, w)
      if id == -1 then
        w = math.max(0, w - math.floor(Q.dsum * (Q.drop - 1)))
      else
        Q.dsum = Q.dsum + w
        w = math.floor(math.min(w * Q.drop, 1000000) + 0.5)
      end
      additem(id, w)
    end
  end
  if Q.noshake then
    for _, name in ipairs({'CameraSetSourceNoise', 'CameraSetTargetNoise', 'CameraSetSourceNoiseEx',
                           'CameraSetTargetNoiseEx', 'CameraSetEQNoiseForPlayer'}) do
      local f = _G[name]
      _G[name] = function(...) if not Q.still[GetPlayerId(GetLocalPlayer())] then f(...) end end
    end
  end
  if Q.reveal then
    local fog, mask = FogEnable, FogMaskEnable
    FogEnable = function() fog(false) end
    FogMaskEnable = function() mask(false) end
  end
end
"""
LUA_TAIL = """
-- Devo's Map Doctor: the quality of life edits, started after the map's own main.
function QoL_Init()
  local Q = QoL
  for i = 0, bj_MAX_PLAYERS - 1 do
    if Q.xp ~= 1 then SetPlayerHandicapXP(Player(i), GetPlayerHandicapXP(Player(i))) end
  end
  if Q.gold ~= 1 or Q.lumber ~= 1 then
    local t = CreateTrigger()
    for i = 0, bj_MAX_PLAYERS - 1 do
      local p = Player(i)
      Q.last[i * 2] = GetPlayerState(p, PLAYER_STATE_RESOURCE_GOLD)
      Q.last[i * 2 + 1] = GetPlayerState(p, PLAYER_STATE_RESOURCE_LUMBER)
      TriggerRegisterPlayerStateEvent(t, p, PLAYER_STATE_RESOURCE_GOLD, GREATER_THAN_OR_EQUAL, 0)
      TriggerRegisterPlayerStateEvent(t, p, PLAYER_STATE_RESOURCE_LUMBER, GREATER_THAN_OR_EQUAL, 0)
    end
    TriggerAddAction(t, function()
      local p, s = GetTriggerPlayer(), GetEventPlayerState()
      local k, m = GetPlayerId(p) * 2, Q.gold
      if s == PLAYER_STATE_RESOURCE_LUMBER then k, m = k + 1, Q.lumber end
      local v = GetPlayerState(p, s)
      local last = Q.last[k] or v
      if v > last and m ~= 1 then
        v = math.floor(math.max(math.min(last + (v - last) * m, 1000000000), 0))
        Q.last[k] = v
        DisableTrigger(GetTriggeringTrigger())
        SetPlayerState(p, s, v)
        EnableTrigger(GetTriggeringTrigger())
      end
      Q.last[k] = GetPlayerState(p, s)
    end)
  end
  if Q.noshake then
    local t = CreateTrigger()
    for i = 0, bj_MAX_PLAYERS - 1 do
      Q.still[i] = %(noshake_default)s
      TriggerRegisterPlayerChatEvent(t, Player(i), "-noshake", true)
    end
    TriggerAddAction(t, function()
      local p = GetTriggerPlayer()
      local k = GetPlayerId(p)
      Q.still[k] = not Q.still[k]
      if Q.still[k] then
        if GetLocalPlayer() == p then
          CameraSetSourceNoise(0, 0)
          CameraSetTargetNoise(0, 0)
        end
        DisplayTimedTextToPlayer(p, 0, 0, 5, "Camera shakes off (-noshake turns them back on).")
      else
        DisplayTimedTextToPlayer(p, 0, 0, 5, "Camera shakes on.")
      end
    end)
  end
  if Q.reveal then
    FogEnable(false)
    FogMaskEnable(false)
  end
end
do
  local map_main = main
  function main()
    if map_main then map_main() end
    QoL_Init()
  end
end
"""
RX_LUA_NAME = re.compile(r'GetPlayerName\s*\(([^()]*(?:\([^()]*\)[^()]*)*)\)\s*(==|~=)\s*(["\'])((?:\\.|(?!\3).)*)\3')


def _lua_code_lines(text):
    out = []
    for l in _lines(text):
        q, i = None, 0
        while i < len(l):
            c = l[i]
            if q:
                if c == '\\':
                    i += 2
                    continue
                if c == q:
                    q = None
            elif c in '"\'':
                q = c
            elif l.startswith('--', i):
                l = l[:i]
                break
            i += 1
        out.append(l)
    return out


def lua_count(text, names):
    rx = re.compile(r'(?<![\w.:])(?:%s)\s*\(' % '|'.join(map(re.escape, names)))
    return sum(len(rx.findall(l)) for l in _lua_code_lines(text))


def lua_vip_sites(text):
    out = []
    for k, l in enumerate(_lua_code_lines(text)):
        for m in RX_LUA_NAME.finditer(l):
            if 'WorldEdit' in m.group(4):
                continue
            out.append((k, m.start(), m.end(), 'true' if m.group(2) == '==' else 'false', m.group(4)))
    return out


class _LuaCode:
    def __init__(self, text):
        from doctor.script import lua_ast
        self.text = text
        self.chunk = lua_ast.parse(text)
        kinds, self.toks, _lines, self.offs = lua_ast._lex(text)[:4]
        self.kinds = kinds
        self.funcs = []
        self.named = {}
        self.nodes = {}
        self._walk(self.chunk.body, '(main chunk)', None, [])

    def _walk(self, block, name, span, own):
        if not own and name is not None:
            self.funcs.append((name, own, span))
        for st in block:
            own.append(st)
            sp = st.span or span
            if type(st).__name__ == 'FunctionStmt':
                mine = []
                self.funcs.append((st.name, mine, st.span))
                self.named.setdefault(st.name, mine)
                self.nodes.setdefault(st.name, st)
                self._walk(st.body, None, st.span, mine)
                continue
            for e in self._exprs(st):
                self._funcs_in(e, sp)
            for b in self._blocks(st):
                self._walk(b, None, sp, own)

    @staticmethod
    def _blocks(st):
        t = type(st).__name__
        if t == 'IfStmt':
            return [b for _c, b in st.branches]
        if t in ('WhileStmt', 'NumericForStmt', 'GenericForStmt', 'RepeatStmt', 'DoStmt'):
            return [st.body]
        return []

    @staticmethod
    def _exprs(st):
        t = type(st).__name__
        if t == 'LocalStmt':
            return list(st.values or [])
        if t == 'AssignStmt':
            return list(st.targets) + list(st.values)
        if t == 'CallStmt':
            return [st.call]
        if t == 'IfStmt':
            return [c for c, _b in st.branches if c is not None]
        if t in ('WhileStmt', 'RepeatStmt'):
            return [st.cond]
        if t == 'NumericForStmt':
            return [x for x in (st.start, st.stop, st.step) if x is not None]
        if t == 'GenericForStmt':
            return list(st.exprs)
        if t == 'ReturnStmt':
            return list(st.values or [])
        return []

    def _funcs_in(self, e, span):
        stack = [e]
        while stack:
            x = stack.pop()
            if x is None or isinstance(x, (str, int, float, bool)):
                continue
            if isinstance(x, (list, tuple)):
                stack.extend(x)
                continue
            t = type(x).__name__
            if t == 'FunctionExpr':
                mine = []
                self.funcs.append(('function at line %d' % x.line, mine, span))
                self._walk(x.body, None, span, mine)
                continue
            for f in getattr(type(x), '__slots__', ()):
                if f != 'line':
                    stack.append(getattr(x, f, None))

    @staticmethod
    def calls_in(e):
        out, stack = [], [e]
        while stack:
            x = stack.pop()
            if x is None or isinstance(x, (str, int, float, bool)):
                continue
            if isinstance(x, (list, tuple)):
                stack.extend(x)
                continue
            t = type(x).__name__
            if t == 'FunctionExpr':
                continue
            if t == 'Call' and type(x.func).__name__ == 'Name':
                out.append(x.func.name)
            for f in getattr(type(x), '__slots__', ()):
                if f != 'line' and not (t == 'FunctionStmt' and f == 'body'):
                    stack.append(getattr(x, f, None))
        return out

    def names_in(self, e):
        out, stack = [], [e]
        while stack:
            x = stack.pop()
            if x is None or isinstance(x, (str, int, float, bool)):
                continue
            if isinstance(x, (list, tuple)):
                stack.extend(x)
                continue
            if type(x).__name__ == 'Name':
                out.append(x.name)
            for f in getattr(type(x), '__slots__', ()):
                if f != 'line':
                    stack.append(getattr(x, f, None))
        return out

    def tok_at(self, off):
        import bisect
        return bisect.bisect_left(self.offs, off)

    def tok_end(self, i):
        return self.offs[i] + len(self.toks[i])

    def match(self, i):
        pair = {'(': ')', '[': ']', '{': '}'}
        o, c, d = self.toks[i], pair[self.toks[i]], 0
        for j in range(i, len(self.toks)):
            if self.kinds[j] in ('STRING', 'NUMBER', 'NAME'):
                continue
            if self.toks[j] == o:
                d += 1
            elif self.toks[j] == c:
                d -= 1
                if d == 0:
                    return j
        return None

    def conditions(self, st):
        i = self.tok_at(st.span[0])
        out, depth, start = [], 0, None
        if self.toks[i] != 'if':
            return None
        start = i + 1
        for j in range(i + 1, len(self.toks)):
            t, k = self.toks[j], self.kinds[j]
            if k in ('STRING', 'NUMBER', 'NAME'):
                continue
            if start is not None:
                if t == 'then' and depth == 0:
                    out.append((start, j))
                    start = None
                elif t == 'function':
                    depth += 1
                elif t == 'end':
                    depth -= 1
                continue
            if t in ('function', 'do', 'if', 'repeat'):
                depth += 1
            elif t in ('end', 'until'):
                if depth == 0:
                    break
                depth -= 1
            elif t == 'elseif' and depth == 0:
                start = j + 1
        return out

    def args(self, i):
        e = self.match(i)
        if e is None:
            return None
        out, d, a = [], 0, i + 1
        for j in range(i + 1, e):
            t = self.toks[j]
            if self.kinds[j] in ('STRING', 'NUMBER', 'NAME'):
                continue
            if t in ('(', '[', '{'):
                d += 1
            elif t in (')', ']', '}'):
                d -= 1
            elif t == ',' and d == 0:
                out.append((a, j))
                a = j + 1
        if a < e:
            out.append((a, e))
        return out

    def src(self, a, b):
        return self.text[self.offs[a]:self.tok_end(b - 1)] if b > a else ''

    def random_call(self, a, b):
        if b - a >= 3 and self.toks[a] in ('GetRandomInt', 'GetRandomReal') and self.toks[a + 1] == '(':
            p = a + 1
            kind = 'I' if self.toks[a] == 'GetRandomInt' else 'R'
        elif b - a >= 5 and self.toks[a:a + 3] == ['math', '.', 'random'] and self.toks[a + 3] == '(':
            p, kind = a + 3, 'I'
        else:
            return None
        if self.match(p) != b - 1:
            return None
        ar = self.args(p)
        if any(self.toks[j] == '(' for x, y in ar for j in range(x, y)):
            return None
        if self.toks[a] == 'math':
            if not ar:
                return 'R', '0', '1'
            if len(ar) == 1:
                return 'I', '1', self.src(*ar[0])
        if len(ar) != 2:
            return None
        return kind, self.src(*ar[0]), self.src(*ar[1])


LUA_CMP = {'<': '<', '<=': '<=', '>': '>', '>=': '>=', '==': '==', '~=': '!='}
LUA_ITEM_MAKE = frozenset(ITEM_MAKE) | frozenset(('BlzCreateItemWithSkin', 'AddItemToStockBJ', 'AddItemToAllStockBJ',
                                                  'CreateItemLocBJ'))
LUA_WAITS = ('TriggerSleepAction', 'PolledWait')


def _lua_strip(lc, a, b):
    neg = 0
    while b - a >= 2:
        if lc.toks[a] == 'not' and lc.toks[a + 1] == '(' and lc.match(a + 1) == b - 1:
            neg, a, b = neg + 1, a + 2, b - 1
        elif lc.toks[a] == '(' and lc.match(a) == b - 1:
            a, b = a + 1, b - 1
        else:
            break
    return a, b, neg


def _lua_compare(lc, a, b):
    d, ops = 0, []
    for j in range(a, b):
        t = lc.toks[j]
        if lc.kinds[j] in ('STRING', 'NUMBER', 'NAME'):
            continue
        if t in ('(', '[', '{'):
            d += 1
        elif t in (')', ']', '}'):
            d -= 1
        elif d == 0 and t in ('and', 'or'):
            return None
        elif d == 0 and t in LUA_CMP:
            ops.append(j)
    if len(ops) != 1:
        return None
    o = ops[0]
    return (a, o), lc.toks[o], (o + 1, b)


def lua_chance_sites(lc):
    makers = set(LUA_ITEM_MAKE)
    for name, own, _sp in lc.funcs:
        if name in lc.named and any(set(lc.calls_in(st)) & LUA_ITEM_MAKE for st in own):
            makers.add(name)
    conds = {}
    for name, node in lc.nodes.items():
        if len(node.body) != 2:
            continue
        a, r = node.body
        if type(a).__name__ != 'IfStmt' or type(r).__name__ != 'ReturnStmt' or len(a.branches) != 1:
            continue
        body = a.branches[0][1]
        if len(body) != 1 or type(body[0]).__name__ != 'ReturnStmt':
            continue
        if [lc.src(*_r) for _r in [(lc.tok_at(body[0].span[0]) + 1, lc.tok_at(body[0].span[1]))]] != ['false'] or \
                lc.text[r.span[0]:r.span[1]].split() != ['return', 'true']:
            continue
        cs = lc.conditions(a)
        if cs:
            conds[name] = cs[0]

    def creates(block):
        return any(set(lc.calls_in(st)) & makers for st in _flat(block))

    out, seen = [], {}
    for name, own, span in lc.funcs:
        ctx = lc.text[span[0]:span[1]] if span else ''
        kind = 'drop' if RX_DEATH.search(ctx) else 'craft' if any(
            set(lc.calls_in(st)) & set(ITEM_TAKE) for st in own) else 'drop'
        draws = {}
        for st in _flat(own):
            t = type(st).__name__
            if t in ('LocalStmt', 'AssignStmt') and st.span:
                tg = st.names if t == 'LocalStmt' else st.targets
                if len(tg) == 1 and len(st.values or []) == 1:
                    n = tg[0] if isinstance(tg[0], str) else getattr(tg[0], 'name', None)
                    i = lc.tok_at(st.span[0])
                    eq = next((j for j in range(i, lc.tok_at(st.span[1])) if lc.toks[j] == '='), None)
                    rc = lc.random_call(eq + 1, lc.tok_at(st.span[1])) if eq is not None else None
                    if n and rc:
                        draws.setdefault(n, []).append((st.span[0], rc))
                    elif n in draws:
                        draws[n].append((st.span[0], None))
            if t != 'IfStmt' or not st.span:
                continue
            branches = st.branches
            final = [b for c, b in branches if c is None]
            if final and creates(final[0]):
                continue
            cs = lc.conditions(st)
            if not cs or len(cs) != len([c for c, _b in branches if c is not None]):
                continue
            eqs = 0
            todo = []
            for (c, b), (a0, b0) in zip([x for x in branches if x[0] is not None], cs):
                a1, b1, neg = _lua_strip(lc, a0, b0)
                target = None
                if creates(b):
                    if b1 - a1 >= 3 and lc.kinds[a1] == 'NAME' and lc.toks[a1] in conds and lc.toks[a1 + 1] == '(' \
                            and lc.match(a1 + 1) == b1 - 1:
                        ca, cb = conds[lc.toks[a1]]
                        ca, cb, cneg = _lua_strip(lc, ca, cb)
                        want = (cneg % 2 == 1) == (neg % 2 == 0)
                        target = (ca, cb, not want, lc.toks[a1])
                    else:
                        target = (a1, b1, neg % 2 == 1, name)
                if target is None:
                    continue
                ta, tb, inv, fn = target
                cmp = _lua_compare(lc, ta, tb)
                if cmp is None:
                    continue
                (la, lb), op, (ra, rb) = cmp
                where = lc.offs[ta]
                side = None
                for (xa, xb), flip in (((la, lb), False), ((ra, rb), True)):
                    rc = lc.random_call(xa, xb)
                    if rc is None and xb - xa == 1 and lc.toks[xa] in draws:
                        last = [d for d in draws[lc.toks[xa]] if d[0] < where]
                        rc = last[-1][1] if last and fn == name else None
                    if rc:
                        side = (xa, xb, flip, rc)
                        break
                if side is None:
                    continue
                xa, xb, flip, (rk, lo, hi) = side
                other = (ra, rb) if not flip else (la, lb)
                o = LUA_CMP[op]
                if flip:
                    o = FLIP[o]
                if o in ('==', '!='):
                    eqs += 1
                todo.append((lc.offs[ta], lc.tok_end(tb - 1), 'QoL.roll%s(%s, %s, %s, (%s), %d, %s, QoL.%s)' % (
                    rk, lc.src(xa, xb), lo, hi, lc.src(*other), OPS[o], 'true' if inv else 'false', kind), kind, fn))
            if eqs >= 2:
                continue
            for x in todo:
                k = (x[0], x[1])
                if k in seen:
                    if seen[k] != x[2]:
                        out = [y for y in out if (y[0], y[1]) != k]
                    continue
                seen[k] = x[2]
                out.append(x)
    return out


def _flat(block):
    out, stack = [], list(reversed(block))
    while stack:
        st = stack.pop()
        out.append(st)
        for b in reversed(_LuaCode._blocks(st)):
            stack.extend(reversed(b))
    return out


def lua_respawn_sites(lc):
    revive = set()
    for name, own, _sp in lc.funcs:
        if any(set(lc.calls_in(st)) & set(REVIVE) for st in own):
            revive.add(name)
    sites, done, untouched, covered = [], set(), [], set()

    def waits_before(own, at, fn):
        n = 0
        for st in own:
            if type(st).__name__ != 'CallStmt' or not st.span or st.span[0] >= at:
                continue
            c = st.call
            if type(c.func).__name__ == 'Name' and c.func.name in LUA_WAITS and len(c.args) == 1:
                i = lc.tok_at(st.span[0])
                ar = lc.args(i + 1) if lc.toks[i + 1] == '(' else None
                if ar and len(ar) == 1 and st.span not in done:
                    done.add(st.span)
                    a, b = ar[0]
                    sites.append((lc.offs[a], lc.tok_end(b - 1), '(%s) * QoL.respawn' % lc.src(a, b), fn,
                                  'wait in %s' % fn))
                    n += 1
        return n

    for name, own, _sp in lc.funcs:
        flat = _flat(own)
        n = 0
        for st in flat:
            if not st.span:
                continue
            called = set(lc.calls_in(st))
            passed = set(lc.names_in(st)) & revive
            if called & set(REVIVE) or (passed and name not in revive):
                k = waits_before(flat, st.span[0], name)
                if k and passed:
                    covered.update(passed)
                n += k
            if type(st).__name__ == 'CallStmt' and type(st.call.func).__name__ == 'Name' and \
                    st.call.func.name == 'TimerStart' and len(st.call.args) == 4:
                cb = st.call.args[3]
                hit = (type(cb).__name__ == 'Name' and cb.name in revive) or (
                    type(cb).__name__ == 'FunctionExpr' and any(set(lc.calls_in(x)) & set(REVIVE)
                                                                 for x in _flat(cb.body)))
                i = lc.tok_at(st.span[0])
                ar = lc.args(i + 1) if lc.toks[i + 1] == '(' else None
                if hit and ar and len(ar) == 4 and lc.src(*ar[2]).strip() == 'false' and st.span not in done:
                    done.add(st.span)
                    a, b = ar[1]
                    cbn = cb.name if type(cb).__name__ == 'Name' else 'function at line %d' % cb.line
                    sites.append((lc.offs[a], lc.tok_end(b - 1), '(%s) * QoL.respawn' % lc.src(a, b), name,
                                  'timer that runs %s' % cbn))
                    covered.add(cbn)
                    n += 1
        if name in revive and not n:
            untouched.append(name)
    return sites, sorted(revive), [u for u in untouched if u not in covered]


def lua_creep_sites(lc):
    out, seen = [], set()
    dead = death_actions(lc.text)
    for name, own, span in lc.funcs:
        types, waits = set(), []
        died = name in dead or (span is not None and 'GetDyingUnit' in lc.text[span[0]:span[1]])
        for st in own:
            if not st.span:
                continue
            t = type(st).__name__
            src = lc.text[st.span[0]:st.span[1]]
            if t in ('LocalStmt', 'AssignStmt'):
                m = re.match(r'^(?:local\s+)?(\w+)\s*=\s*(.+)$', src.strip(), re.S)
                if m and RX_OWN_TYPE.match(m.group(2).strip()):
                    types.add(m.group(1))
            if t != 'CallStmt' or type(st.call.func).__name__ != 'Name':
                continue
            fn = st.call.func.name
            i = lc.tok_at(st.span[0])
            ar = lc.args(i + 1) if lc.toks[i + 1] == '(' else None
            if not ar:
                continue
            at = {'TriggerSleepAction': 0, 'PolledWait': 0, 'TimerStart': 1, 'StartTimerBJ': 2}.get(fn)
            if at is not None and at < len(ar):
                a, b = ar[at]
                arg = lc.src(a, b)
                if RX_POINT_VALUE.search(arg):
                    if st.span not in seen:
                        seen.add(st.span)
                        out.append((lc.offs[a], lc.tok_end(b - 1), '(%s) * QoL.creep' % arg, name,
                                    'point value in %s' % name))
                elif fn in ('TriggerSleepAction', 'PolledWait'):
                    waits.append((st.span, a, b))
            if fn in CREEP_MAKE and waits and died and len(ar) > 1:
                ty = lc.src(*ar[1]).strip()
                if RX_OWN_TYPE.match(ty) or ty in types:
                    for sp, a, b in waits:
                        if sp not in seen:
                            seen.add(sp)
                            out.append((lc.offs[a], lc.tok_end(b - 1), '(%s) * QoL.creep' % lc.src(a, b), name,
                                        'wait in %s' % name))
                    waits = []
    return out


def lua_found(text):
    vips = lua_vip_sites(text)
    out = {'lua': True, 'xp_calls': lua_count(text, ('AddHeroXP', 'SetPlayerHandicapXP', 'SetPlayerHandicapXPBJ',
                                                     'AddHeroXPSwapped')),
            'xp_set': lua_count(text, ('SetHeroXP', 'SetHeroLevel', 'SetHeroLevelBJ')),
            'gold_script': len(re.findall(r'PLAYER_STATE_RESOURCE_(?:GOLD|LUMBER)', text)),
            'save_load': bool(RX_SAVE.search(text)),
            'shake_calls': lua_count(text, tuple(SHAKE_CALLS)), 'fog_calls': lua_count(text, tuple(FOG_CALLS)),
            'drop_tables': lua_count(text, ('RandomDistAddItem',)),
            'vip_names': sorted(set(v[4] for v in vips))[:30], 'vip_checks': len(vips), 'kk_mall': False,
            'revive_functions': 0, 'revive_waits': 0, 'revive_untouched': [], 'drop_chances': 0, 'craft_chances': 0}
    try:
        lc = _LuaCode(text)
    except Exception:
        return out
    sites, revive, untouched = lua_respawn_sites(lc)
    chances = lua_chance_sites(lc)
    out.update(revive_functions=len(revive), revive_waits=len(sites), revive_untouched=untouched[:12],
               creep_waits=len(lua_creep_sites(lc)),
               drop_chances=sum(1 for c in chances if c[3] == 'drop'),
               craft_chances=sum(1 for c in chances if c[3] == 'craft'))
    return out


def _lua_bool(b):
    return 'true' if b else 'false'


def lua_edit(text, o, rep):
    done = {}
    if o['respawn'] != 1 or o['creep'] != 1 or o['drop'] != 1 or o['craft'] != 1:
        lc = _LuaCode(text)
        edits = []
        if o['creep'] != 1:
            cs = lua_creep_sites(lc)
            edits += [(a, b, r) for a, b, r, _f, _w in cs]
            rep['creep'] = [(f, w) for _a, _b, _r, f, w in cs]
        if o['respawn'] != 1:
            sites, revive, untouched = lua_respawn_sites(lc)
            taken_c = set((a, b) for a, b, _r in edits)
            sites = [x for x in sites if (x[0], x[1]) not in taken_c]
            edits += [(a, b, r) for a, b, r, _f, _w in sites]
            rep['respawn'] = {'sites': [(f, w) for _a, _b, _r, f, w in sites], 'revive': revive,
                              'untouched': untouched}
        if o['drop'] != 1 or o['craft'] != 1:
            ch = [c for c in lua_chance_sites(lc) if o[c[3]] != 1]
            edits += [(a, b, r) for a, b, r, _k, _f in ch]
            rep['chances'] = [(k, f) for _a, _b, _r, k, f in ch]
        for a, b, r in sorted(edits, reverse=True):
            text = text[:a] + r + text[b:]
    if o['vip']:
        vips = lua_vip_sites(text)
        text = _apply_edits(text, [(k, s, e, r) for k, s, e, r, _n in vips])
        rep['vip'] = sorted(set(n for _k, _s, _e, _r, n in vips))
        done['vip'] = len(vips)
    if o['xp'] != 1:
        done['xp'] = lua_count(text, ('AddHeroXP', 'SetPlayerHandicapXP', 'SetPlayerHandicapXPBJ', 'AddHeroXPSwapped'))
    if o['drop'] != 1:
        done['dist'] = lua_count(text, ('RandomDistAddItem',))
    if o['noshake'] or o['noshake_default']:
        done['shake'] = lua_count(text, tuple(SHAKE_CALLS))
    if o['reveal']:
        done['fog'] = lua_count(text, tuple(FOG_CALLS))
    v = {'xp': _real(o['xp']), 'gold': _real(o['gold']), 'lumber': _real(o['lumber']), 'drop': _real(o['drop']),
         'craft': _real(o['craft']), 'respawn': _real(o['respawn']), 'creep': _real(o['creep']),
         'reveal': _lua_bool(o['reveal']), 'noshake': _lua_bool(o['noshake'] or o['noshake_default']),
         'noshake_default': _lua_bool(o['noshake_default'])}
    nl = '\r\n' if text.count('\r\n') * 2 > text.count('\n') else '\n'
    head = (LUA_HEAD % v).replace('\n', nl)
    tail = (LUA_TAIL % v).replace('\n', nl)
    from doctor.script import lua_ast
    new = head + text + ('' if text.endswith(('\n', '\r')) else nl) + tail
    try:
        lua_ast.parse(new)
    except lua_ast.LuaSyntaxError:
        new = (head + 'local QoL_ret = table.pack((function(...)' + nl + text + nl + 'end)(...))' + nl + tail +
               'return table.unpack(QoL_ret, 1, QoL_ret.n)' + nl)
        lua_ast.parse(new)
    return new, done


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
              '    integer array QoL_last', '    boolean QoL_hold = false']
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
    if v > QoL_last[k] and m != 1. and not QoL_hold then
        set v = R2I(RMaxBJ(RMinBJ(I2R(QoL_last[k]) + I2R(v - QoL_last[k]) * m, 1000000000.), 0.))
        set QoL_last[k] = v
        call DisableTrigger(GetTriggeringTrigger())
        call SetPlayerState(p, s, v)
        call EnableTrigger(GetTriggeringTrigger())
    endif
    set QoL_last[k] = GetPlayerState(p, s)
    set p = null
    set s = null
endfunction
function QoL_Keep takes player p, playerstate s returns nothing
    if s == PLAYER_STATE_RESOURCE_GOLD then
        set QoL_last[GetPlayerId(p) * 2] = GetPlayerState(p, s)
    elseif s == PLAYER_STATE_RESOURCE_LUMBER then
        set QoL_last[GetPlayerId(p) * 2 + 1] = GetPlayerState(p, s)
    endif
endfunction
function QoL_RestoreAdjust takes integer d, player p, playerstate s returns nothing
    set QoL_hold = true
    call AdjustPlayerStateBJ(d, p, s)
    set QoL_hold = false
    call QoL_Keep(p, s)
endfunction
function QoL_RestoreSetBJ takes player p, playerstate s, integer v returns nothing
    set QoL_hold = true
    call SetPlayerStateBJ(p, s, v)
    set QoL_hold = false
    call QoL_Keep(p, s)
endfunction
function QoL_RestoreSet takes player p, playerstate s, integer v returns nothing
    set QoL_hold = true
    call SetPlayerState(p, s, v)
    set QoL_hold = false
    call QoL_Keep(p, s)
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
    if o['creep'] != 1:
        g.append('    real QoL_creep = %s' % _real(o['creep']))
    if o['drop'] != 1 or o['craft'] != 1:
        g += ['    real QoL_drop = %s' % _real(o['drop']), '    real QoL_craft = %s' % _real(o['craft']),
              '    integer QoL_dsum = 0']
        f.append(ROLL)
        f.append('''function QoL_DistReset takes nothing returns nothing
    set QoL_dsum = 0
    call RandomDistReset()
endfunction
function QoL_DistAdd takes integer id, integer w returns nothing
    if id == -1 then
        set w = IMaxBJ(0, w - R2I(I2R(QoL_dsum) * (QoL_drop - 1.)))
    else
        set QoL_dsum = QoL_dsum + w
        set w = R2I(RMinBJ(I2R(w) * QoL_drop, 1000000.) + 0.5)
    endif
    call RandomDistAddItem(id, w)
endfunction''')
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


def edit(text, o, rep, item_vals=None):
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
        nl = '\r\n' if text.count('\r\n') * 2 > text.count('\n') else '\n'
        for k, s, e, _fn, why in sites:
            if why.startswith('delay parameter '):
                p = why.split()[2]
                edits.append((k, s, e, nl + 'set %s = (%s) * QoL_respawn' % (p, p)))
            else:
                edits.append((k, s, e, ' (' + lines[k][s:e].strip() + ') * QoL_respawn'))
        rep['respawn'] = {'sites': [(fn, why) for _k, _s, _e, fn, why in sites], 'revive': revive,
                          'untouched': untouched}
    if o['creep'] != 1:
        taken_r = set((k, s) for k, s, *_r in edits)
        cs = [c for c in creep_sites(text, tree) if (c[0], c[1]) not in taken_r]
        lines = _lines(text)
        edits += [(k, s, e, ' (' + lines[k][s:e].strip() + ') * QoL_creep') for k, s, e, _fn, _w in cs]
        rep['creep'] = [(fn, why) for _k, _s, _e, fn, why in cs]
    if o['drop'] != 1 or o['craft'] != 1:
        chances = [c for c in chance_sites(text, tree, item_vals) if o[c[4]] != 1]
        edits += [(k, s, e, r) for k, s, e, r, _kind, _fn in chances]
        rep['chances'] = [(kind, fn) for _k, _s, _e, _r, kind, fn in chances]
    if o['gold'] != 1 or o['lumber'] != 1:
        rs = restore_sites(text)
        edits += rs
        if rs:
            done['restore'] = len(rs)
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
    if o['drop'] != 1 and dist_items(text):
        done['dist'] = dist_items(text)
        text, _n = _rename(text, DIST_CALLS)
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
    lua = sc['language'] == 'lua' and sc['bytes'] is not None
    if not lua and (sc['language'] != 'jass' or sc['compiled'] or sc['bytes'] is None):
        return stop('refused', 'This version edits JASS and Lua scripts (the map script is %s).'
                    % ('compiled by the KK platform: port it first' if sc['compiled'] else sc['language'] or
                       'unreadable'))
    text = sc['bytes'].decode('utf-8', 'surrogateescape')
    if MARK in text:
        return stop('refused', 'The map already has the QoL edits of the Doctor: edit the original map instead.')
    if lua and '__ydwe' in text:
        return stop('refused', 'The map is a KK map ported by the Doctor\'s Lua route: edit the original map before '
                               'the port.')
    p('Editing the script')
    try:
        if lua:
            new_text, done = lua_edit(text, o, rep)
        else:
            new_text, done = edit(text, o, rep, item_values(_a))
    except Exception as e:
        return stop('refused', 'The script cannot take the QoL edits (%s).' % e)
    new_bytes = new_text.encode('utf-8', 'surrogateescape')
    if lua:
        rep['pjass'] = {'state': 'lua'}
    else:
        p('Running pjass')
        rep['pjass'] = map_rewrite.gate(sc['bytes'], new_bytes)
        if rep['pjass']['state'] == 'failed':
            return stop('refused', 'pjass does not accept the edited script (%s).' % rep['pjass'].get('new'))
    files = [(sc['file'], new_bytes)] + [(c, new_bytes) for c in sc['copies']]
    if o['respawn'] != 1:
        misc, rep['altar'] = altar_misc(unprotect._read(_a, MISC_FILE), o['respawn'])
        files.append((MISC_FILE, misc))
    try:
        w = map_rewrite.write(path_in, path_out, files, p)
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
    elif pj.get('state') == 'lua':
        out.append(('good', 'The edited Lua script parses.'))
    if o['xp'] != 1:
        out.append(('info', 'Experience x%g: the XP handicap of every player (kills), and %d call(s) of the map that '
                            'give XP or set the handicap.' % (o['xp'], done.get('xp', 0))))
        n = _count(text, SET_XP)
        if n:
            out.append(('warn', '%d call(s) set a hero\'s XP or level directly (a custom XP system): those are left '
                                'as they are.' % n))
    if o['gold'] != 1 or o['lumber'] != 1:
        out.append(('info', 'Gold x%g, lumber x%g, on every gain of every player.' % (o['gold'], o['lumber'])))
        if done.get('restore'):
            out.append(('info', 'The gold and lumber a load gives back from the save are not multiplied (%d place(s)).'
                        % done['restore']))
        elif RX_SAVE.search(text):
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
        alt = rep.get('altar') or {}
        if alt:
            out.append(('info', 'Revive at an altar x%g (the gameplay constants): %s.' % (o['respawn'], ', '.join(
                '%s %g -> %g' % (k, alt[k][0], alt[k][1]) for k, _d in ALTAR if k in alt))))
    if o['creep'] != 1:
        cs = rep.get('creep') or []
        if cs:
            out.append(('info', 'Monster respawn time x%g: %d wait(s) or timer(s) in %d place(s).'
                        % (o['creep'], len(cs), len(set(fn for fn, _w in cs)))))
            for fn, why in cs[:12]:
                out.append(('info', '  %s' % why))
        else:
            out.append(('warn', 'Monster respawn time: no wait or timer of a monster respawn was found.'))
    if o['noshake'] or o['noshake_default']:
        out.append(('info', '-noshake turns the camera shakes off and on (%d call(s) of the map rerouted)%s.'
                    % (done.get('shake', 0), '; every player starts with them off' if o['noshake_default'] else '')))
    if o['reveal']:
        out.append(('info', 'The map is revealed from the start (%d fog call(s) of the map rerouted).'
                    % done.get('fog', 0)))
    if o['drop'] != 1 and done.get('dist'):
        out.append(('info', 'Item drop x%g in the item tables of the World Editor: %d item(s), the "nothing" share '
                            'gives up what they take.' % (o['drop'], done['dist'])))
    if o['drop'] != 1 or o['craft'] != 1:
        ch = rep.get('chances') or []
        for kind in ('drop', 'craft'):
            if o[kind] == 1:
                continue
            n = [fn for k, fn in ch if k == kind]
            if n:
                out.append(('info', '%s chance x%g: %d roll(s) in %d function(s).'
                            % ('Item drop' if kind == 'drop' else 'Craft success', o[kind], len(n), len(set(n)))))
            elif not (kind == 'drop' and done.get('dist')):
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
