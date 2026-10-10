# Applies translated texts to the script and the data files of a map.
import collections
import json
import os
import re
from collections import Counter


HERE = os.path.dirname(os.path.abspath(__file__))
TR = os.environ.get('TR_DIR') or os.path.join(HERE, 'tr')
BUILD = os.path.join(TR, 'build')
from doctor.translation import kr_inventory as ki
from doctor.translation import tr_extract as tx


def load_translations():
    tr = {}
    for fn in ('reuso.json', 'glossary.json', 'bulk.json', 'repair.json', 'manual.json'):
        p = os.path.join(TR, fn)
        if os.path.exists(p):
            tr.update(json.load(open(p, encoding='utf-8')))
    return tr


ALL_OS_ARGUMENTS = object()

_KINDS_HASHTABLE = (
    'Str', 'Integer', 'Real', 'Boolean', 'UnitHandle', 'ItemHandle', 'AbilityHandle',
    'TimerHandle', 'TriggerHandle', 'TriggerConditionHandle', 'TriggerActionHandle',
    'TriggerEventHandle', 'ForceHandle', 'GroupHandle', 'LocationHandle', 'RectHandle',
    'BooleanExprHandle', 'SoundHandle', 'EffectHandle', 'UnitPoolHandle', 'ItemPoolHandle',
    'QuestHandle', 'QuestItemHandle', 'DefeatConditionHandle', 'TimerDialogHandle',
    'LeaderboardHandle', 'LeaderboardItemHandle', 'TrackableHandle', 'DialogHandle',
    'ButtonHandle', 'TextTagHandle', 'LightningHandle', 'ImageHandle', 'UbersplatHandle',
    'RegionHandle', 'FogStateHandle', 'FogModifierHandle', 'AgentHandle', 'HashtableHandle',
)
ARGUMENTS_KEY = {}
for _t in _KINDS_HASHTABLE:
    for _p in ('Save', 'Load', 'HaveSaved', 'RemoveSaved'):
        ARGUMENTS_KEY[_p + _t] = frozenset((1, 2))
ARGUMENTS_KEY['FlushChildHashtable'] = frozenset((1,))
ARGUMENTS_KEY['FlushParentHashtable'] = frozenset()
for _t in ('Integer', 'Real', 'Boolean', 'String', 'Unit'):
    for _p in ('Store', 'GetStored', 'HaveStored', 'FlushStored', 'SyncStored'):
        ARGUMENTS_KEY[_p + _t] = frozenset((1, 2))
ARGUMENTS_KEY['RestoreUnit'] = frozenset((1, 2))
ARGUMENTS_KEY['FlushStoredMission'] = frozenset((1,))
ARGUMENTS_KEY['InitGameCache'] = frozenset((0,))
for _t in ('Integer', 'Real', 'Boolean', 'String', 'Unit'):
    ARGUMENTS_KEY['Store%sBJ' % _t] = frozenset((1, 2))
    ARGUMENTS_KEY['GetStored%sBJ' % _t] = frozenset((0, 1))
for _f in ('RestoreUnitLocFacingAngleBJ', 'RestoreUnitLocFacingPointBJ'):
    ARGUMENTS_KEY[_f] = frozenset((0, 1))
ARGUMENTS_KEY['HaveStoredValue'] = frozenset((0, 2))
ARGUMENTS_KEY['FlushStoredMissionBJ'] = frozenset((0,))
ARGUMENTS_KEY['InitGameCacheBJ'] = frozenset((0,))
for _f in ('YDWESaveStringByString', 'YDWESaveStringByInteger',
           'YDWEGetStringByString', 'YDWEGetStringByInteger',
           'YDWEHaveSavedIntegerByString', 'YDWEHaveSavedIntegerByInteger',
           'YDWEFlushStoredIntegerByString', 'YDWEFlushStoredIntegerByInteger'):
    ARGUMENTS_KEY[_f] = frozenset((0, 1))
ARGUMENTS_KEY['YDWEFlushMissionByString'] = frozenset((0,))
ARGUMENTS_KEY['YDWEFlushMissionByInteger'] = frozenset((0,))
PREFIXES_KEY = ('DzAPI_Map_', 'JNObject', 'JNDaily', 'JNRPG', 'JNSetLog', 'JNMapServerLog', 'JNPublicMapServerLog')
PREFIXES_KEY_ARGS = {
    'DzSync': frozenset((0,)),
    'DzTriggerRegisterSyncData': frozenset((1,)),
}
FRAME_NAMES = frozenset((
    'DzCreateFrameByTagName', 'DzCreateFrame', 'BlzCreateFrame', 'BlzCreateFrameByType',
    'BlzCreateSimpleFrame', 'BlzGetFrameByName', 'BlzFrameGetName', 'BlzFrameFindByName',
    'DzFrameFindByName', 'DzFrameFindByNameEx',
))
for _f in FRAME_NAMES:
    ARGUMENTS_KEY[_f] = ALL_OS_ARGUMENTS
FUNCTIONS_CAUTION = ('SubString', 'SubStringBJ', 'StringLength', 'StringLengthBJ')
ARGUMENTS_KEY['BlzSendSyncData'] = frozenset((0,))
ARGUMENTS_KEY['BlzTriggerRegisterPlayerSyncEvent'] = frozenset((2,))
ARGUMENTS_KEY['ExecuteFunc'] = frozenset((0,))
TEXT_SEARCH = {'JNStringContains': 1, 'JNStringCount': 1, 'JNStringPos': 1, 'JNStringRegex': 1,
               'JNStringSplit': 1, 'JNStringReplace': 1}
RX_LETTER = re.compile(r'[^\W\d_]')


RX_MARKUP = re.compile(r'#\w+|\|[cC][0-9a-fA-F]{8}|\|[rRnN]|<[^<>]*>|%\w|\\[nrt"\\]')


RX_REGEX_OPERATOR = re.compile(r'\\+[A-Za-z]|\\+.|[()\[\]|*+?.{}^$]')


def searched(args_end, w3p_constants=None, regex=False):
    m = re.match(r'\s*,\s*("(?:[^"\\]|\\.)*"|[^,()]+)', args_end)
    if not m:
        return True
    arg = m.group(1).strip()
    if arg.startswith('"'):
        body_text = arg[1:-1]
    elif w3p_constants and arg in w3p_constants:
        body_text = w3p_constants[arg]
    else:
        return True
    chunks = RX_REGEX_OPERATOR.split(body_text) if regex else [body_text]
    chunks = tuple(('within', x) for x in chunks if RX_LETTER.search(RX_MARKUP.sub('', x)))
    return chunks or None


def _find(lookup, lit):
    return lookup is True or any((x in lit) if k == 'within' else (lit == x) for k, x in lookup)


def call_envolvente(before):
    max_depth = virgulas = 0
    i = len(before) - 1
    while i >= 0:
        c = before[i]
        if c == ')':
            max_depth += 1
        elif c == '(':
            if max_depth == 0:
                j = i - 1
                while j >= 0 and (before[j].isalnum() or before[j] in '_$'):
                    j -= 1
                fname = before[j + 1:i]
                if fname:
                    return fname, virgulas
            else:
                max_depth -= 1
        elif c == ',' and max_depth == 0:
            virgulas += 1
        i -= 1
    return None, None


def classifica_occurrence(line_str, pos, lit, caution_as_screen=False, script_flow=None, ln=None):
    before = line_str[max(0, pos - 400):pos]
    after_diag = line_str[pos + len(lit) + 2:pos + len(lit) + 13]
    if re.search(r'[=!]=\s*$', before) or after_diag.lstrip().startswith(('==', '!=')):
        return 'caution:comparison'
    fn, idx = call_envolvente(before)
    if script_flow is not None and ln is not None:
        tgt = script_flow.dest(line_str, pos, lit, fn, idx, ln)
        if tgt:
            return 'caution:flow ' + tgt
    if fn is None:
        return 'screen:no call (assignment/list)'
    if fn in TEXT_SEARCH:
        if idx == TEXT_SEARCH[fn]:
            return 'caution:' + fn
        if idx == 0 and fn != 'JNStringReplace':
            tgt = searched(
                line_str[pos + len(lit) + 2 : pos + len(lit) + 402],
                script_flow.w3p_constants if script_flow else None,
                fn == 'JNStringRegex',
            )
            if tgt is not None and _find(tgt, lit):
                return 'caution:' + fn
        return 'screen:' + fn
    if fn == 'StringHash':
        return 'hash_key:StringHash'
    if fn in FUNCTIONS_CAUTION:
        return 'caution:' + fn
    if fn in ARGUMENTS_KEY:
        keys = ARGUMENTS_KEY[fn]
        if keys is ALL_OS_ARGUMENTS or idx in keys:
            return 'hash_key:' + fn
        return 'screen:' + fn
    for p in PREFIXES_KEY:
        if fn.startswith(p):
            return 'hash_key:' + fn
    for p, idxs in PREFIXES_KEY_ARGS.items():
        if fn.startswith(p) and idx in idxs:
            return 'hash_key:' + fn
    return 'screen:' + fn


def apply_by_occurrence(body_text, by_text, caution_as_screen=False, all_entries=None):
    line_list, sep = tx.line_break(body_text, jass=True)
    cats, detail, n = apply_by_occurrence_lines(line_list, by_text, caution_as_screen, all_entries)
    return sep.join(line_list), cats, detail, n


def apply_by_occurrence_lines(
    line_list, by_text, caution_as_screen=False, all_entries=None, protected=None, script_flow=None
):
    all_entries = all_entries or {}
    cats = Counter()
    detail = {}
    n = 0
    inside = tx.lines_protected(line_list, tx.functions_protected(TR) if protected is None else protected)
    for line_no, line in enumerate(line_list):
        lits = ki.literals(line)
        if not lits:
            continue
        if inside and inside[line_no]:
            for pos, lit in lits:
                if lit in by_text:
                    cats['datum:protected function'] += 1
                    detail.setdefault(lit, Counter())['datum'] += 1
            continue
        out, last, changed = [], 0, False
        for pos, lit in lits:
            en = by_text.get(lit)
            if en is None:
                key2 = lit.encode('utf-8', 'surrogateescape').decode('utf-8', 'replace')
                en = by_text.get(key2)
            if en is None:
                continue
            cat = 'all_entries:explicit decision' if lit in all_entries else \
                classifica_occurrence(line, pos, lit, caution_as_screen, script_flow, line_no)
            cluster = cat.split(':', 1)[0]
            cats[cat] += 1
            d = detail.setdefault(lit, Counter())
            d[cluster] += 1
            if cluster in ('screen', 'all_entries') or (cluster == 'caution' and caution_as_screen):
                out.append(line[last:pos + 1])
                out.append(en)
                last = pos + 1 + len(lit)
                changed = True
                n += 1
        if changed:
            out.append(line[last:])
            line_list[line_no] = ''.join(out)
    return cats, detail, n


RX_HEADER = re.compile(r'\s*(?:constant\s+)?function\s+(\w+)\s+takes\s+(.*?)\s+returns\s+(\w+)')
RX_END_FUNCTION = re.compile(r'\s*endfunction\b')
RX_STRING_LOCAL = re.compile(r'\s*local\s+string\s+(?:array\s+)?(\w+)')
RX_STRING_GLOBAL = re.compile(r'\s*(?:constant\s+)?string\s+(?:array\s+)?(\w+)')
RX_TARGET = re.compile(
    r'\s*(?:set\s+(\w+)\s*(\[[^\]]*\])?\s*|local\s+string\s+(\w+)\s*|(?:constant\s+)?string\s+(\w+)\s*)'
    r'=(?!=)'
)
RX_FIXED_INDEX = re.compile(r"\[\s*(\d+|\$[0-9A-Fa-f]+|0[xX][0-9A-Fa-f]+|'[^']{1,4}')\s*\]$")
RX_IDENT = re.compile(r'[A-Za-z_]\w*')
RX_LOAD = re.compile(r'\s*LoadStr\s*\(\s*(\w+)')
RX_STRING_CONSTANT = re.compile(r'\s*constant\s+string\s+(\w+)\s*=\s*"((?:[^"\\]|\\.)*)"\s*$')
_INDEX = r'(\[(?:[^\[\]]|\[[^\[\]]*\])*\])'
RX_OPERAND_AFTER = re.compile(r'\s*(?:[=!]=)\s*(?:(""|null\b)|("x*")|(\w+)\s*' + _INDEX +
                              r'?\s*(?=$|\)|then\b|and\b|or\b))')
RX_OPERAND_BEFORE = re.compile(r'(?:(""|\bnull)|("x*")|(\w+)\s*' + _INDEX + r'?)\s*$')
PASS_ALONG = frozenset(('StringCase', 'JNStringTrim', 'JNStringTrimStart', 'JNStringTrimEnd'))
EVERYTHING = True
RX_KEY_LINE = re.compile(r'Hash|Save|Load|Store|Stored|HaveS|Remove|Flush|Restore|Sync|DzAPI|JN|Frame|ExecuteFunc|'
                         r'GameCache')


def _target(m):
    a = RX_TARGET.match(m)
    if not a:
        return None
    return (a.group(1) or a.group(3) or a.group(4)), a.group(2), a.end()


def _mask(line_str):
    lits = ki.literals(line_str)
    if not lits:
        out = line_str
    else:
        pieces, last = [], 0
        for pos, lit in lits:
            pieces.append(line_str[last:pos + 1])
            pieces.append('x' * len(lit))
            last = pos + 1 + len(lit)
        pieces.append(line_str[last:])
        out = ''.join(pieces)
    c = out.find('//')
    return out if c < 0 else out[:c] + ' ' * (len(out) - c)


def _call_with_position(before):
    max_depth = virgulas = 0
    i = len(before) - 1
    while i >= 0:
        c = before[i]
        if c == ')':
            max_depth += 1
        elif c == '(':
            if max_depth == 0:
                j = i - 1
                while j >= 0 and (before[j].isalnum() or before[j] in '_$'):
                    j -= 1
                if j + 1 < i:
                    return before[j + 1:i], virgulas, j + 1
            else:
                max_depth -= 1
        elif c == ',' and max_depth == 0:
            virgulas += 1
        i -= 1
    return None, None, None


def _closes(m, opens, a='(', f=')'):
    max_depth = 0
    for i in range(opens, len(m)):
        if m[i] == a:
            max_depth += 1
        elif m[i] == f:
            max_depth -= 1
            if max_depth == 0:
                return i + 1
    return len(m)


class ScriptFlow(object):
    def __init__(self, line_list, outside=None):
        self.outside = outside
        self.functions = {}
        self.of_line = []
        self.globals_block = set()
        self.w3p_constants = {}
        current = None
        for i, line in enumerate(line_list):
            if outside and outside[i]:
                self.of_line.append(None)
                continue
            m = RX_HEADER.match(line)
            if m:
                current = m.group(1)
                params = {}
                if m.group(2).strip() != 'nothing':
                    for k, p in enumerate(m.group(2).split(',')):
                        t = p.split()
                        if len(t) >= 2 and t[0] == 'string':
                            params[t[-1]] = k
                self.functions[current] = {'params': params, 'body_text': m.group(3) == 'string', 'local_vars': set()}
            elif current is None:
                g = RX_STRING_GLOBAL.match(line)
                if g:
                    self.globals_block.add(g.group(1))
                    c = RX_STRING_CONSTANT.match(line)
                    if c:
                        self.w3p_constants[c.group(1)] = c.group(2)
            else:
                g = RX_STRING_LOCAL.match(line)
                if g:
                    self.functions[current]['local_vars'].add(g.group(1))
            self.of_line.append(current)
            if current is not None and RX_END_FUNCTION.match(line):
                current = None
        edges = collections.defaultdict(set)
        marks = {}
        comparados = []
        self.origin = {}
        self.marked_compared = []
        value_list = collections.defaultdict(set)
        impure = set()
        returning = set(f for f, d in self.functions.items() if d['body_text'])
        masks = {}
        loads = []
        self.literal_keys = set()
        assignments = collections.defaultdict(list)
        for i, line in enumerate(line_list):
            if (outside and outside[i]) or RX_HEADER.match(line):
                continue
            fn = self.of_line[i]
            m = masks[i] = _mask(line)
            if '"' in line and RX_KEY_LINE.search(line):
                for pos, lit in ki.literals(line):
                    if classifica_occurrence(line, pos, lit).startswith('hash_key'):
                        self.literal_keys.add(lit)
            tgt = _target(m)
            if tgt:
                at_target = self._node(tgt[0], fn, tgt[1], write_site=True)
                if at_target is not None:
                    lit = re.match(r'\s*"(x*)"\s*$', m[tgt[2]:])
                    if lit:
                        value_list[at_target].add(line[tgt[2] + lit.start(1):tgt[2] + lit.end(1)])
                    else:
                        impure.add(at_target)
                    if at_target[0] == 'v' and len(at_target) == 2:
                        assignments[(fn, tgt[0])].append(i)
                    load_of = RX_LOAD.match(m[tgt[2]:])
                    if load_of:
                        loads.append((('ht', load_of.group(1)), at_target))
        times = collections.Counter()
        for (_fn, fname), ls in assignments.items():
            if _fn is not None:
                times[fname] += len(ls)
        self._temporaries = set(no[1] for no in impure if no[0] == 'v' and len(no) == 2) | \
            set(n for n, k in times.items() if k > 1 and n not in self.w3p_constants)
        temp_uses = collections.defaultdict(list)
        the_whole = collections.defaultdict(set)
        temp_entries = []
        for i, line in enumerate(line_list):
            if i not in masks:
                continue
            fn = self.of_line[i]
            m = masks[i]
            tgt = _target(m)
            for mo in RX_IDENT.finditer(m):
                fname = mo.group(0)
                begin, end_pos = mo.start(), mo.end()
                if tgt and end_pos <= tgt[2] and fname == tgt[0]:
                    continue
                index_ = None
                if m[end_pos:end_pos + 1] == '[':
                    f2 = _closes(m, end_pos, '[', ']')
                    index_, end_pos = m[end_pos:f2], f2
                no = self._node(fname, fn, index_)
                if no is None:
                    if fname in returning and m[end_pos:end_pos + 1] == '(':
                        no = ('r', fname)
                        end_pos = _closes(m, end_pos)
                    else:
                        continue
                use_of = self._use(line, m, begin, end_pos, fn, 0)
                if use_of is None:
                    continue
                if use_of[0] == 'flow':
                    the_whole[no].add(use_of[1])
                if self._temporary(no):
                    temp_uses[(fn, no[1])].append((i, use_of))
                    continue
                if use_of[0] == 'flow' and self._temporary(use_of[1]):
                    temp_entries.append((no, fn, i, use_of[1][1]))
                    self.origin.setdefault(('t', no), i)
                    continue
                if use_of[0] == 'flow':
                    if use_of[1] != no:
                        edges[no].add(use_of[1])
                elif use_of[0] == 'cmp':
                    comparados.append((no, use_of[1]))
                    self.origin.setdefault(no, i)
                else:
                    self._mark(marks, no, use_of[1])
                    self.origin.setdefault(no, i)
        for table, no in loads:
            the_whole[table].add(no)
        elements = collections.defaultdict(set)
        for no in list(edges) + [b for bs in edges.values() for b in bs] + list(marks) + \
                [x for pair in comparados for x in pair]:
            if no and no[0] == 'v' and len(no) == 3:
                elements[no[1]].add(no[2])
        for no in list(the_whole) + [b for bs in the_whole.values() for b in bs]:
            if no and no[0] == 'v' and len(no) == 3:
                elements[no[1]].add(no[2])
        for fname, ks in elements.items():
            for k in ks:
                if k not in ('*', '*w'):
                    for g in (edges, the_whole):
                        g[('v', fname, k)].add(('v', fname, '*'))
                        g[('v', fname, '*w')].add(('v', fname, k))
            for g in (edges, the_whole):
                g[('v', fname, '*w')].add(('v', fname, '*'))
        acquire_range = {}

        def reaches(a, b):
            if a not in acquire_range:
                seen, stack = {a}, [a]
                while stack:
                    for x in the_whole.get(stack.pop(), ()):
                        if x not in seen:
                            seen.add(x)
                            stack.append(x)
                acquire_range[a] = seen
            return b in acquire_range[a]

        tables = {}

        def the_constant(no):
            if no is None or no[0] not in ('v', 'line') or no in impure:
                return None
            vs = set(value_list.get(no, ()))
            if no[0] == 'v' and len(no) == 3 and no[2] == '*':
                if not tables:
                    for x in impure:
                        if x[0] == 'v' and len(x) == 3:
                            tables[x[1]] = None
                    for x, v in value_list.items():
                        if x[0] == 'v' and len(x) == 3 and tables.get(x[1], set()) is not None:
                            tables.setdefault(x[1], set()).update(v)
                    tables[None] = None
                return tables.get(no[1]) or None
            if no[0] == 'v' and len(no) == 3:
                if no[2] == '*w':
                    return None
                write_site = ('v', no[1], '*w')
                if write_site in impure:
                    return None
                vs |= value_list.get(write_site, set())
            return vs or None
        externals = set(self._externals(line_list, masks))
        stack = list(externals)
        while stack:
            for x in the_whole.get(stack.pop(), ()):
                if x not in externals:
                    externals.add(x)
                    stack.append(x)
        self.externals = externals
        for a, b in comparados:
            if b is not None and (reaches(a, b) or reaches(b, a)):
                continue
            if b is not None and a not in externals and b not in externals and \
                    not (b[0] == 'v' and len(b) == 3 and ('v', b[1], '*w') in externals):
                continue
            vs = the_constant(b)
            self._mark(marks, a, EVERYTHING if vs is None else tuple(('==', v) for v in vs))
            self.marked_compared.append((a, b))
        self.edges = edges
        goes_back = collections.defaultdict(set)
        for a, bs in edges.items():
            for b in bs:
                goes_back[b].add(a)
        self.sensitive = {}

        def propagate(added):
            stack = []
            for no, what in added.items():
                if self._mark(self.sensitive, no, what):
                    stack.append(no)
            while stack:
                b = stack.pop()
                for a in goes_back.get(b, ()):
                    if self._mark(self.sensitive, a, self.sensitive[b]):
                        stack.append(a)
        propagate(marks)
        self._temp_uses, self._assignments = temp_uses, assignments
        self._constant = the_constant
        for _goes_back in range(2):
            self._temp_memo = {}
            added = {}
            for no, fn, i, fname in temp_entries:
                what = self.sensitive_temp(fn, fname, i)
                if what is not None:
                    self._mark(added, no, what)
            propagate(added)
        self._temp_memo = {}

    def finds(self, lookup, lit):
        if lookup is EVERYTHING:
            return True
        return any((lit in self.literal_keys) if k == 'hash_key' else (x in lit) if k == 'within' else (lit == x)
                   for k, x in lookup)

    def _externals(self, line_list, masks):
        out = []
        for i, m in masks.items():
            fn = self.of_line[i]
            tgt = _target(m)
            if tgt:
                no = self._node(tgt[0], fn, tgt[1], write_site=True)
                if no is not None and not RX_LOAD.match(m[tgt[2]:]) and not self._pure(m[tgt[2]:], fn):
                    out.append(no)
            r = re.match(r'\s*return\b(.*)$', m)
            if r and fn is not None and self.functions[fn]['body_text'] and not self._pure(r.group(1), fn):
                out.append(('r', fn))
            if '(' not in m:
                continue
            for mo in RX_IDENT.finditer(m):
                f = mo.group(0)
                d = self.functions.get(f)
                if f == 'SaveStr' and m[mo.end():mo.end() + 1] == '(':
                    d = {'params': {'table': 3}}
                if not d or not d['params'] or m[mo.end():mo.end() + 1] != '(':
                    continue
                end_pos = _closes(m, mo.end())
                args, max_depth, begin = [], 0, mo.end() + 1
                for k in range(mo.end() + 1, end_pos - 1):
                    c = m[k]
                    if c in '([':
                        max_depth += 1
                    elif c in ')]':
                        max_depth -= 1
                    elif c == ',' and max_depth == 0:
                        args.append(m[begin:k])
                        begin = k + 1
                args.append(m[begin:end_pos - 1])
                for idx in d['params'].values():
                    if idx < len(args) and not self._pure(args[idx], fn):
                        out.append(('ht', args[0].strip()) if f == 'SaveStr' else ('p', f, idx))
        return out

    def _pure(self, expr, fn):
        e = expr.strip()
        if not e:
            return True
        e = re.sub(r"'[^']*'", '0', e)
        previous = None
        while previous != e:
            previous = e
            e = re.sub(r'\[[^\[\]]*\]', '', e)
            e = re.sub(
                r'\b(?:I2S|R2S|R2SW|S2I|S2R|I2R|R2I|StringLength|GetPlayerId|GetConvertedPlayerId)\s*\([^()]*\)', '0', e
            )
        for mo in RX_IDENT.finditer(e):
            fname = mo.group(0)
            before = e[mo.start() - 1:mo.start()]
            if fname in ('and', 'or', 'not', 'true', 'false', 'null', 'then') or before == '$' or before.isdigit():
                continue
            if e[mo.end():mo.end() + 1] == '(':
                if fname in self.functions:
                    continue
                if fname in ('StringCase', 'JNStringTrim', 'JNStringTrimStart', 'JNStringTrimEnd'):
                    continue
                return False
            if self._node(fname, fn) is not None or fname.isdigit():
                continue
            if re.match(r'\d', fname) or re.match(r'x+$', fname):
                continue
            return False
        return True

    def _temporary(self, no):
        return no is not None and no[0] == 'v' and len(no) == 2 and no[1] in self._temporaries

    def sensitive_temp(self, fn, fname, line_str, saved=0):
        hash_key = (fn, fname, line_str)
        if hash_key in self._temp_memo:
            return self._temp_memo[hash_key]
        self._temp_memo[hash_key] = None
        if fn is None or saved > 20:
            return None
        next_one = min([j for j in self._assignments.get((fn, fname), ()) if j > line_str] or [10 ** 9])
        combined = {}
        for j, use_of in self._temp_uses.get((fn, fname), ()):
            if not line_str < j <= next_one:
                continue
            if use_of[0] == 'mark':
                self._mark(combined, 'x', use_of[1])
            elif use_of[0] == 'cmp':
                vs = self._constant(use_of[1])
                self._mark(combined, 'x', EVERYTHING if vs is None else tuple(('==', v) for v in vs))
            elif use_of[0] == 'flow':
                tgt = use_of[1]
                what = self.sensitive_temp(fn, tgt[1], j, saved + 1) if self._temporary(tgt) else \
                    self.sensitive.get(tgt)
                if what is not None:
                    self._mark(combined, 'x', what)
        self._temp_memo[hash_key] = combined.get('x')
        return self._temp_memo[hash_key]

    @staticmethod
    def _mark(where, no, what):
        before = where.get(no)
        if before is EVERYTHING:
            return False
        if what is EVERYTHING:
            where[no] = EVERYTHING
            return True
        new = (before or frozenset()) | frozenset(what)
        if new == before:
            return False
        where[no] = new
        return True

    def _node(self, fname, fn, index_=None, write_site=False):
        if fn is not None:
            d = self.functions[fn]
            if fname in d['params']:
                return ('p', fn, d['params'][fname])
            if fname in d['local_vars']:
                return ('line', fn, fname)
        if fname in self.globals_block:
            if index_ is None:
                return ('v', fname)
            k = RX_FIXED_INDEX.match(index_.strip())
            if k:
                return ('v', fname, k.group(1).lower())
            return ('v', fname, '*w' if write_site else '*')
        return None

    def _comparison(self, m, begin, end_pos, fn):
        before = m[max(0, begin - 400):begin]
        op = re.search(r'([=!]=)\s*$', before)
        table = re.search(r'\bLoadStr\s*\(\s*(\w+)[^()]*\)\s*$', before[:op.start()]) if op else \
            re.match(r'\s*[=!]=\s*LoadStr\s*\(\s*(\w+)', m[end_pos:end_pos + 80])
        if table:
            return ('cmp', ('ht', table.group(1)))
        if op:
            o = RX_OPERAND_BEFORE.search(before[:op.start()])
        else:
            o = RX_OPERAND_AFTER.match(m[end_pos:end_pos + 400])
            if not o and not m[end_pos:end_pos + 12].lstrip().startswith(('==', '!=')):
                return None
        if o and o.group(1):
            return ('empty',)
        if o and o.group(2):
            base = (max(0, begin - 400) if op else end_pos)
            return ('equal', self._raw_line[base + o.start(2) + 1:base + o.end(2) - 1])
        if o and o.group(3):
            return ('cmp', self._node(o.group(3), fn, o.group(4)))
        return ('cmp', None)

    def _use(self, line, m, begin, end_pos, fn, max_depth):
        self._raw_line = line
        c = self._comparison(m, begin, end_pos, fn)
        if c is not None:
            if c[0] == 'equal':
                return ('mark', (('==', c[1]),))
            return None if c[0] == 'empty' else c
        before = m[max(0, begin - 400):begin]
        fname, idx, where = _call_with_position(before)
        if fname is None:
            tgt = _target(m)
            if tgt and tgt[2] <= begin:
                no = self._node(tgt[0], fn, tgt[1], write_site=True)
                return ('flow', no) if no else None
            if fn is not None and self.functions[fn]['body_text'] and re.match(r'\s*return\b', m):
                return ('flow', ('r', fn))
            return None
        if fname in TEXT_SEARCH:
            if idx == TEXT_SEARCH[fname]:
                return ('mark', EVERYTHING)
            if idx == 0 and fname != 'JNStringReplace':
                tgt = searched(line[end_pos:end_pos + 400], self.w3p_constants, fname == 'JNStringRegex')
                return None if tgt is None else ('mark', tgt)
        if fname in self.functions:
            return ('flow', ('p', fname, idx)) if idx in self.functions[fname]['params'].values() else None
        if fname == 'SaveStr' and idx == 3:
            t = re.match(r'\s*\(\s*(\w+)', m[begin - len(before) + where + len(fname):])
            if t:
                return ('flow', ('ht', t.group(1)))
        if idx >= 2 and fname.startswith(PREFIXES_KEY):
            return None
        if classify_call_occurrence(fname, idx) in ('hash_key', 'caution') and fname not in FUNCTIONS_CAUTION:
            if fname in FRAME_NAMES or fname == 'ExecuteFunc' or fname.startswith(PREFIXES_KEY):
                return ('mark', EVERYTHING)
            return ('mark', (('hash_key', ''),))
        c0 = begin - len(before) + where
        if fname in ('SubString', 'SubStringBJ') and idx == 0:
            c = self._comparison(m, c0, _closes(m, c0 + len(fname)), fn)
            if c is None or c[0] == 'empty':
                return None
            if c[0] == 'equal':
                return ('mark', (('within', c[1]),)) if RX_LETTER.search(RX_MARKUP.sub('', c[1])) else None
            return ('mark', EVERYTHING)
        if (fname in PASS_ALONG or (fname == 'JNStringReplace' and idx in (0, 2))) and max_depth < 8:
            return self._use(line, m, c0, _closes(m, c0 + len(fname)), fn, max_depth + 1)
        return None

    def dest(self, line_str, pos, lit, fn, idx, ln):
        if ln >= len(self.of_line) or (self.outside and self.outside[ln]):
            return ''
        current = self.of_line[ln]
        if fn is None:
            m = _mask(line_str)
            tgt = _target(m)
            if tgt and tgt[2] <= pos:
                no = self._node(tgt[0], current, tgt[1], write_site=True)
                label = tgt[0] + (tgt[1] if tgt[1] and no and len(no) == 3 and no[2] != '*w' else '')
                if self._temporary(no):
                    s = self.sensitive_temp(current, tgt[0], ln)
                    return label if s is not None and self.finds(s, lit) else ''
            elif current is not None and re.match(r'\s*return\b', m):
                no, label = ('r', current), 'return of ' + current
            else:
                return ''
        elif fn in self.functions:
            no, label = ('p', fn, idx), '%s#%d' % (fn, idx)
        else:
            return ''
        s = self.sensitive.get(no)
        if s is None or not self.finds(s, lit):
            return ''
        return label


def classify_call_occurrence(fn, idx):
    if fn == 'StringHash':
        return 'hash_key'
    if fn in FUNCTIONS_CAUTION:
        return 'caution'
    if fn in ARGUMENTS_KEY:
        keys = ARGUMENTS_KEY[fn]
        return 'hash_key' if keys is ALL_OS_ARGUMENTS or idx in keys else 'screen'
    for p in PREFIXES_KEY:
        if fn.startswith(p):
            return 'hash_key'
    for p, idxs in PREFIXES_KEY_ARGS.items():
        if fn.startswith(p) and idx in idxs:
            return 'hash_key'
    return 'screen'


def load_extras():
    p = os.path.join(TR, 'texto_en_extra.json')
    if not os.path.exists(p):
        return {}
    d = json.load(open(p, encoding='utf-8'))
    return dict((k, v) for k, v in d.items() if not k.startswith('_'))


def load_all():
    p = os.path.join(TR, 'texto_en_todas.json')
    if not os.path.exists(p):
        return {}
    d = json.load(open(p, encoding='utf-8'))
    return dict((k, v) for k, v in d.items() if not k.startswith('_'))


def extras_by_id(entries, extras):
    output = {}
    for e in entries:
        if e.get('text') in extras:
            output[e['id']] = extras[e['text']]
    return output


def fix_value(en, entry):
    if '"' not in (entry.get('text') or ''):
        en = en.replace('"', "'")
    if entry.get('quoted'):
        return '"' + en + '"'
    if ',' in en and not entry.get('comma'):
        return '"' + en + '"'
    return en


def apply_txt(root, entries, tr, stats):
    by_file = {}
    for e in entries:
        if e['src'].endswith('.txt') and e['id'] in tr:
            by_file.setdefault(e['src'], {})[e['line']] = (e, tr[e['id']])
    for details, lines_map in by_file.items():
        src = tx.read_text(os.path.join(root, details))
        lines, sep = tx.line_break(src)
        n = 0
        for line_no, (e, en) in lines_map.items():
            mk = re.match(r'^([A-Za-z0-9_]+)=(.*)$', lines[line_no])
            assert mk and mk.group(1) == e['key'], (details, line_no, e['key'])
            lines[line_no] = '%s=%s' % (e['key'], fix_value(en, e))
            n += 1
        out = os.path.join(BUILD, details.replace('/', os.sep))
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, 'wb').write(sep.join(lines).encode('utf-8', 'surrogateescape'))
        stats[details] = n


def apply_misc(root, entries, tr, stats):
    for fn in ('war3mapMisc.txt', 'war3mapSkin.txt'):
        p = os.path.join(root, fn)
        if not os.path.exists(p):
            continue
        lines, sep = tx.line_break(tx.read_text(p))
        n = 0
        for e in entries:
            if e['src'] == fn and e['id'] in tr:
                lines[e['line']] = '%s=%s' % (e['key'], tr[e['id']].replace('"', "'"))
                n += 1
        open(os.path.join(BUILD, fn), 'wb').write(sep.join(lines).encode('utf-8', 'surrogateescape'))
        stats[fn] = n
    p = os.path.join(root, 'war3map.wts')
    if os.path.exists(p):
        t = tx.read_text(p)
        n = 0
        for e in entries:
            if e['src'] == 'war3map.wts' and e['id'] in tr:
                num = e['key'].split()[1]
                t, k = re.subn(
                    r'(STRING %s\s*(?://[^\n]*\n)?\s*\{\r?\n)(.*?)(\r?\n\})' % num,
                    lambda m: m.group(1) + tr[e['id']] + m.group(3),
                    t,
                    count=1,
                    flags=re.S,
                )
                n += k
        open(os.path.join(BUILD, 'war3map.wts'), 'wb').write(t.encode('utf-8', 'surrogateescape'))
        stats['war3map.wts'] = n
    p = os.path.join(root, 'war3map.w3i')
    if os.path.exists(p):
        w = open(p, 'rb').read()
        q = 12
        parts = [w[:12]]
        for lab in ('name', 'author', 'description', 'players'):
            e = w.index(b'\0', q)
            s = w[q:e]
            key = 'w3i:' + lab
            if key in tr:
                s = tr[key].encode('utf-8')
            parts.append(s + b'\0')
            q = e + 1
        fixed = 32 + 16 + 8 + 4 + 1 + 4
        parts.append(w[q:q + fixed])
        q += fixed
        for lab in ('loading_model', 'loading_text', 'loading_title', 'loading_sub'):
            e = w.index(b'\0', q)
            s = w[q:e]
            key = 'w3i:' + lab
            if key in tr:
                s = tr[key].encode('utf-8')
            parts.append(s + b'\0')
            q = e + 1
        parts.append(w[q:])
        open(os.path.join(BUILD, 'war3map.w3i'), 'wb').write(b''.join(parts))
        stats['war3map.w3i'] = sum(1 for k in tr if k.startswith('w3i:'))


def translation_map(entries, tr, extras=None):
    by_text = {}
    for e in entries:
        if e['src'] == 'war3map.j' and e['kind'] in ('script', 'command') and e['id'] in tr:
            by_text[e['text']] = tr[e['id']]
    for k, v in (extras or {}).items():
        by_text.setdefault(k, v)
    return by_text

