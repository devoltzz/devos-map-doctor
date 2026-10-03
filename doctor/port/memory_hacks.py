# Gives the memory hacks of patch 1.2x their Reforged equivalent, or neutralizes them.
import re


RX_FUNC = re.compile(r'^([ \t]*)(?:constant[ \t]+)?function[ \t]+(\w+)[ \t]+takes[ \t]+(.*?)[ \t]+returns[ \t]+(\w+)')
RX_END = re.compile(r'^[ \t]*endfunction\b')
RX_LOCAL = re.compile(r'^[ \t]*local[ \t]+(\w+)[ \t]+(?:array[ \t]+)?(\w+)')
RX_RETURN_ID = re.compile(r'^[ \t]*return[ \t]+\(*[ \t]*([A-Za-z_]\w*)[ \t]*\)*[ \t]*(?://.*)?$')
RX_GLOBAL = re.compile(r'^[ \t]*(?:constant[ \t]+)?(\w+)[ \t]+(array[ \t]+)?([A-Za-z_]\w*)')
NEUTRAL = {'integer': '0', 'real': '0.0', 'boolean': 'false', 'string': 'null'}
VAZIA = 'KKMH_vazio'
TABLE_NAME = 'KK_mh_ht'
EFFECT_FUNCTIONS = {
    'SetSpecialEffectColor': (4, 'call BlzSetSpecialEffectColor({0}, {1}, {2}, {3})'),
    'JNSetSpecialEffectScale': (2, 'call BlzSetSpecialEffectScale({0}, {1})'),
    'JNSetSpecialEffectPosition': (4, 'call BlzSetSpecialEffectPosition({0}, {1}, {2}, {3})'),
    'JNSetSpecialEffectHeight': (2, 'call BlzSetSpecialEffectHeight({0}, {1})'),
    'JNSetSpecialEffectTimeScale': (2, 'call BlzSetSpecialEffectTimeScale({0}, {1})'),
    'JNSetSpecialEffectOrientation': (4, 'call BlzSetSpecialEffectOrientation({0}, {1}, {2}, {3})'),
    'JNSetSpecialEffectYaw': (2, 'call BlzSetSpecialEffectYaw({0}, {1})'),
    'JNSetSpecialEffectPitch': (2, 'call BlzSetSpecialEffectPitch({0}, {1})'),
    'JNSetSpecialEffectRoll': (2, 'call BlzSetSpecialEffectRoll({0}, {1})'),
    'JNSetSpecialEffectX': (2, 'call BlzSetSpecialEffectX({0}, {1})'),
    'JNSetSpecialEffectY': (2, 'call BlzSetSpecialEffectY({0}, {1})'),
    'JNSetSpecialEffectZ': (2, 'call BlzSetSpecialEffectZ({0}, {1})'),
    'JNSetSpecialEffectPositionLoc': (2, 'call BlzSetSpecialEffectPositionLoc({0}, {1})'),
    'JNGetLocalSpecialEffectX': (1, 'return BlzGetLocalSpecialEffectX({0})'),
    'JNGetLocalSpecialEffectY': (1, 'return BlzGetLocalSpecialEffectY({0})'),
    'JNGetLocalSpecialEffectZ': (1, 'return BlzGetLocalSpecialEffectZ({0})'),
}


class Reference(object):
    def __init__(self, ref_text):
        self.parent = dict(re.findall(r'(?m)^[ \t]*type[ \t]+(\w+)[ \t]+extends[ \t]+(\w+)', ref_text))
        self.savers = dict(
            (t, 'Save%sHandle' % n)
            for n, t in re.findall(
                r'(?m)^[ \t]*native[ \t]+Save(\w+)Handle[ \t]+takes[ \t]+hashtable[ \t]+\w+[ \t]*,[ \t]*integer[ \t]+\w+[ \t]*,'
                r'[ \t]*integer[ \t]+\w+[ \t]*,[ \t]*(\w+)',
                ref_text,
            )
        )
        self.load_data = dict(
            (t, 'Load%sHandle' % n)
            for n, t in re.findall(
                r'(?m)^[ \t]*native[ \t]+Load(\w+)Handle[ \t]+takes[ \t]+hashtable[ \t]+\w+[ \t]*,[ \t]*integer[ \t]+\w+[ \t]*,'
                r'[ \t]*integer[ \t]+\w+[ \t]+returns[ \t]+(\w+)',
                ref_text,
            )
        )
        self.natives = set(re.findall(r'(?m)^[ \t]*(?:constant[ \t]+)?native[ \t]+(\w+)', ref_text))

    def handle(self, t):
        return t == 'handle' or t in self.parent

    def fits(self, from_, new_value):
        if from_ == new_value:
            return True
        if self.handle(from_) and self.handle(new_value):
            t = from_
            while t in self.parent:
                t = self.parent[t]
                if t == new_value:
                    return True
            return new_value == 'handle' and from_ != 'handle'
        return False


def _functions(line_list):
    out = []
    i = 0
    while i < len(line_list):
        m = RX_FUNC.match(line_list[i])
        if m:
            j = i + 1
            while j < len(line_list) and not RX_END.match(line_list[j]):
                j += 1
            ps = [] if m.group(3).strip() == 'nothing' else [tuple(p.split()[-2:]) for p in m.group(3).split(',')]
            out.append((i, j, m.group(1), m.group(2), ps, m.group(4)))
            i = j
        i += 1
    return out


def _globals(line_list):
    begin = next((k for k, line in enumerate(line_list) if line.strip() == 'globals'), None)
    end_pos = next((k for k, line in enumerate(line_list) if line.strip() == 'endglobals'), None)
    types, vectors = {}, set()
    if begin is None or end_pos is None:
        inside = False
        for line in line_list:
            if RX_FUNC.match(line):
                inside = True
            elif RX_END.match(line):
                inside = False
            elif not inside:
                m = RX_GLOBAL.match(line.split('//')[0])
                if m and m.group(1) not in ('function', 'native', 'type', 'local', 'set', 'call', 'return'):
                    types[m.group(3)] = m.group(1)
                    if m.group(2):
                        vectors.add(m.group(3))
        return types, vectors, None
    for line in line_list[begin + 1:end_pos]:
        m = RX_GLOBAL.match(line.split('//')[0])
        if m and m.group(1) not in ('function', 'native', 'type'):
            types[m.group(3)] = m.group(1)
            if m.group(2):
                vectors.add(m.group(3))
    return types, vectors, (begin, end_pos)


def _conversion_body(ref, p, r, pack_name):
    lazy_init = ['if %s == null then' % TABLE_NAME, '    set %s = InitHashtable()' % TABLE_NAME, 'endif']
    if p == 'boolean' and r == 'integer':
        return ['if %s then' % pack_name, '    return 1', 'endif', 'return 0']
    if p == 'integer' and r == 'boolean':
        return ['return %s != 0' % pack_name]
    if p == 'real' and r == 'integer':
        return ['return R2I(%s)' % pack_name]
    if p == 'integer' and r == 'real':
        return ['return I2R(%s)' % pack_name]
    if p == 'string' and r == 'integer':
        return lazy_init + ['call SaveStr(%s, 1, StringHash(%s), %s)' % (TABLE_NAME, pack_name, pack_name),
                            'return StringHash(%s)' % pack_name]
    if p == 'integer' and r == 'string':
        return lazy_init + ['return LoadStr(%s, 1, %s)' % (TABLE_NAME, pack_name)]
    if p == 'code' and r == 'integer':
        return ['return 0']
    if p == 'integer' and r == 'code':
        return ['return function %s' % VAZIA]
    if ref.handle(p) and r == 'integer':
        savers = ref.savers.get(p)
        saved = (
            lazy_init + ['call %s(%s, 0, GetHandleId(%s), %s)' % (savers, TABLE_NAME, pack_name, pack_name)]
            if savers
            else []
        )
        return saved + ['return GetHandleId(%s)' % pack_name]
    if p == 'integer' and ref.handle(r) and ref.load_data.get(r):
        return lazy_init + ['return %s(%s, 0, %s)' % (ref.load_data[r], TABLE_NAME, pack_name)]
    return None


def _code_only(ln, fn):
    out, i, n, begin = [], 0, len(ln), 0
    while i < n:
        c = ln[i]
        if c == '"' or c == "'":
            out.append(fn(ln[begin:i]))
            k = i + 1
            while k < n and ln[k] != c:
                k += 2 if ln[k] == '\\' else 1
            out.append(ln[i:k + 1])
            i = begin = k + 1
            continue
        if ln.startswith('//', i):
            break
        i += 1
    out.append(fn(ln[begin:i]) + ln[i:])
    return ''.join(out)


def applies(body_text, ref_text, equivalents=True, neutralize=False, suffix=''):
    info = {'conversions': [], 'effects': [], 'arrays': {}, 'codes': [], 'neutrals': []}
    if not equivalents and not neutralize:
        return body_text, info
    ref = Reference(ref_text)
    line_list = body_text.split('\n')
    cr = [line.endswith('\r') for line in line_list]
    line_list = [line.rstrip('\r') for line in line_list]
    global_type_map, vectors, block_entry = _globals(line_list)
    fs = _functions(line_list)
    signature = dict((fname, ps) for _i, _f, _r, fname, ps, _ret in fs)
    replacements = {}
    needs_empty = needs_table = False
    for begin, end_pos, indent_trim, fname, ps, ret in fs:
        body = line_list[begin + 1:end_pos]
        if (
            equivalents
            and fname in EFFECT_FUNCTIONS
            and len(ps) == EFFECT_FUNCTIONS[fname][0]
            and fname not in ref.natives
        ):
            nat = re.match(r'(?:call|return) (\w+)', EFFECT_FUNCTIONS[fname][1]).group(1)
            if nat in ref.natives:
                replacements[begin] = (end_pos, ['    ' + EFFECT_FUNCTIONS[fname][1].format(*[p[1] for p in ps])])
                info['effects'].append(fname)
                continue
        if ret == 'nothing':
            continue
        local_vars = {}
        for line in body:
            m = RX_LOCAL.match(line)
            if m:
                local_vars[m.group(2)] = m.group(1)
        types = dict(global_type_map)
        types.update(dict((n, t) for t, n in ps))
        types.update(local_vars)
        invalid = False
        for line in body:
            m = RX_RETURN_ID.match(line)
            if m and m.group(1) in types and not ref.fits(types[m.group(1)], ret):
                invalid = True
                break
        if not invalid:
            continue
        new = None
        if equivalents and len(ps) == 1:
            new = _conversion_body(ref, ps[0][0], ret, ps[0][1])
            if new is not None:
                info['conversions'].append((fname, ps[0][0], ret))
        if new is None and neutralize:
            new = ['return function %s' % VAZIA] if ret == 'code' else ['return %s' % NEUTRAL.get(ret, 'null')]
            info['neutrals'].append(fname)
        if new is None:
            continue
        needs_empty |= any(VAZIA in line for line in new)
        needs_table |= any(TABLE_NAME in line for line in new)
        replacements[begin] = (end_pos, ['    ' + line for line in new])
    for begin in sorted(replacements, reverse=True):
        end_pos, added = replacements[begin]
        line_list[begin + 1:end_pos] = added
        cr[begin + 1:end_pos] = [cr[begin]] * len(added)
    if neutralize:
        _g, vectors, block_entry = _globals(line_list)
        if vectors:
            for begin, end_pos, _r, _n, ps, _ret in _functions(line_list):
                proprios = set(p[1] for p in ps)
                for line in line_list[begin + 1:end_pos]:
                    m = RX_LOCAL.match(line)
                    if m:
                        proprios.add(m.group(2))
                tgt = sorted(vectors - proprios)
                if not tgt:
                    continue
                rx = re.compile(r'\b(%s)\b(?![ \t]*\[)' % '|'.join(map(re.escape, tgt)))
                for k in range(begin + 1, end_pos):
                    line = line_list[k]
                    if not rx.search(line) or RX_LOCAL.match(line):
                        continue

                    def zero_out(seg, rx=rx):
                        for m in rx.finditer(seg):
                            info['arrays'][m.group(1)] = info['arrays'].get(m.group(1), 0) + 1
                        return rx.sub('0', seg)
                    line_list[k] = _code_only(line, zero_out)
        with_params = set(n for n, ps in signature.items() if ps)
        if with_params:
            rx_func_ref = re.compile(r'\bfunction[ \t]+(%s)\b' % '|'.join(map(re.escape, sorted(with_params))))
            for k, line in enumerate(line_list):
                if RX_FUNC.match(line) or not rx_func_ref.search(line):
                    continue

                def empty_code(seg):
                    for m in rx_func_ref.finditer(seg):
                        info['codes'].append(m.group(1))
                    return rx_func_ref.sub('function %s' % VAZIA, seg)
                line_list[k] = _code_only(line, empty_code)
                needs_empty = True
    body_text = '\n'.join(line + ('\r' if c else '') for line, c in zip(line_list, cr))
    nl = '\r\n' if '\r\n' in body_text else '\n'
    if needs_table and not re.search(r'(?m)^[ \t]*hashtable[ \t]+%s\b' % TABLE_NAME, body_text):
        m = re.search(r'(?m)^[ \t]*globals[ \t]*\r?$', body_text)
        if m:
            body_text = body_text[:m.end()] + nl + 'hashtable %s = null' % TABLE_NAME + body_text[m.end():]
        else:
            m = re.search(r'(?m)^[ \t]*(?:constant[ \t]+)?function[ \t]', body_text)
            if m:
                body_text = body_text[:m.start()] + 'hashtable %s = null' % TABLE_NAME + nl + body_text[m.start():]
    if needs_empty and not re.search(r'(?m)^[ \t]*function[ \t]+%s[ \t]' % VAZIA, body_text):
        m = re.search(r'(?m)^[ \t]*(?:constant[ \t]+)?function[ \t]', body_text)
        if m:
            body_text = (
                body_text[: m.start()]
                + 'function %s takes nothing returns nothing%sendfunction%s' % (VAZIA, nl, nl)
                + body_text[m.start() :]
            )
    if suffix:
        body_text = re.sub(r'\b(%s|%s)\b' % (VAZIA, TABLE_NAME), r'\g<1>' + suffix, body_text)
    return body_text, info


def report_data(info):
    pieces = []
    if info['conversions']:
        pieces.append('%d return bug conversion function(s) with the 3.0 equivalent' % len(info['conversions']))
    if info['effects']:
        pieces.append('%d effect function(s) through the Blz native' % len(info['effects']))
    if info['arrays']:
        pieces.append('%d array read(s) as an address -> 0' % sum(info['arrays'].values()))
    if info['codes']:
        pieces.append('%d code reference(s) to a function with parameters -> empty' % len(info['codes']))
    if info['neutrals']:
        pieces.append('%d return bug(s) without an equivalent -> the neutral value' % len(info['neutrals']))
    print('0h memory: ' + ('; '.join(pieces) if pieces else 'no memory hack'))
