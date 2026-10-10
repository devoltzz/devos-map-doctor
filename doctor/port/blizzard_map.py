# Finds what a map's own Blizzard.j changes or adds to the game's.
import os
import re


HERE = os.path.dirname(os.path.abspath(__file__))
ARCHIVE_ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
VANILLA = os.path.join(
    ARCHIVE_ROOT, 'terceiros', 'w3x2lni-2.7.3', 'data', 'enUS-1.27.1', 'mpq', 'Scripts', 'Blizzard.j'
)
REF_30 = os.path.join(ARCHIVE_ROOT, 'common', 'ref', '3.0')

RX_FUNC = re.compile(r'^[ \t]*(constant[ \t]+)?function[ \t]+(\w+)[ \t]+takes\b.*?^[ \t]*endfunction[ \t]*$',
                     re.M | re.S)
RX_NATIVE = re.compile(r'^[ \t]*(?:constant[ \t]+)?native[ \t]+(\w+)', re.M)
RX_GLOBALS = re.compile(r'^[ \t]*globals[ \t]*$(.*?)^[ \t]*endglobals[ \t]*$', re.M | re.S)
RX_DECL_LINE = re.compile(r'^\s*(?:constant\s+)?(\w+)\s+(?:array\s+)?(\w+)')
RX_TYPE = re.compile(r'^[ \t]*type[ \t]+(\w+)', re.M)
RX_IDENT = re.compile(r'[A-Za-z_]\w*')
RX_TOK = re.compile(r'"(?:\\.|[^"\\\n])*"|//[^\n]*|\'[^\'\n]*\'|\$[0-9A-Fa-f]+|0[xX][0-9A-Fa-f]+|\d+\.\d*|\.\d+|\d+|'
                    r'[A-Za-z_]\w*|==|!=|<=|>=|\S')


def read_data(file_path):
    d = open(file_path, 'rb').read()
    if d.startswith(b'\xef\xbb\xbf'):
        d = d[3:]
    return d.decode('utf-8', 'surrogateescape').replace('\r\n', '\n').replace('\r', '\n')


def pieces(body_text):
    variables = {}
    m = RX_GLOBALS.search(body_text)
    if m:
        for line in m.group(1).split('\n'):
            s = re.sub(r'//.*', '', line).strip()
            d = RX_DECL_LINE.match(s)
            if d:
                variables[d.group(2)] = s
    functions = {f.group(2): f.group(0) for f in RX_FUNC.finditer(body_text)}
    return variables, functions, RX_NATIVE.findall(body_text)


def _value(tok):
    if tok.startswith("'"):
        v = 0
        for c in tok[1:-1].encode('latin-1', 'replace'):
            v = v * 256 + c
        return ('n', float(v))
    if tok.startswith('$'):
        return ('n', float(int(tok[1:], 16)))
    if tok[:2] in ('0x', '0X'):
        return ('n', float(int(tok, 16)))
    if tok.isdigit():
        return ('n', float(int(tok, 8) if len(tok) > 1 and tok[0] == '0' else int(tok)))
    if re.match(r'^(\d+\.\d*|\.\d+)$', tok):
        return ('n', float(tok))
    return tok


def normalize(body_text):
    toks = [t for t in RX_TOK.findall(body_text) if not t.startswith('//')]
    toks = [_value(t) for t in toks]
    toks = [t for i, t in enumerate(toks) if not (t == 'else' and i + 1 < len(toks) and toks[i + 1] == 'endif')]
    nameless = []
    i = 0
    while i < len(toks):
        if i + 1 < len(toks) and (toks[i], toks[i + 1]) in (('==', 'true'), ('!=', 'false')):
            i += 2
            continue
        nameless.append(toks[i])
        i += 1
    toks = nameless
    name_list = {}
    for i, t in enumerate(toks):
        if t == 'takes':
            j = i + 1
            while j + 1 < len(toks) and toks[j] != 'returns':
                if toks[j] != 'nothing' and toks[j] != ',' and toks[j + 1] not in (',', 'returns'):
                    name_list.setdefault(toks[j + 1], '_p%d' % len(name_list))
                j += 1
        elif t == 'local' and i + 2 < len(toks):
            k = i + 3 if toks[i + 2] == 'array' else i + 2
            if k < len(toks):
                name_list.setdefault(toks[k], '_l%d' % len(name_list))
    return [name_list.get(t, t) if isinstance(t, str) else t for t in toks]


def reference_names(ref):
    name_list = set()
    for file_ in ('common.j', 'blizzard.j'):
        t = read_data(os.path.join(ref, file_))
        v, f, n = pieces(t)
        name_list |= set(v) | set(f) | set(n) | set(RX_TYPE.findall(t))
    return name_list


def extract_parts(map_bj, script, vanilla=None, ref=None):
    map_script_text = read_data(map_bj)
    van_t = read_data(vanilla or VANILLA)
    scr = read_data(script)
    mv, mf, mn = pieces(map_script_text)
    vv, vf, _vn = pieces(van_t)
    info = {'map_func_names': len(mf), 'map_variables': len(mv), 'natives': sorted(mn)}
    extra_v = {k: v for k, v in mv.items() if k not in vv}
    extra_f = {k: v for k, v in mf.items() if k not in vf}
    info['extra_functions'] = len(extra_f)
    info['extra_variables'] = len(extra_v)
    info['changed_functions'] = sorted(k for k in mf if k in vf and normalize(mf[k]) != normalize(vf[k]))
    info['changed_variables'] = sorted(k for k in mv if k in vv and normalize(mv[k]) != normalize(vv[k]))
    info['missing_from_game'] = sorted(set(vf) - set(mf))
    info['colisoes'] = sorted((set(extra_v) | set(extra_f)) & reference_names(ref or REF_30))
    extra_count = set(extra_v) | set(extra_f)
    work_queue = sorted(set(RX_IDENT.findall(scr)) & extra_count)
    in_use = set()
    while work_queue:
        n = work_queue.pop()
        if n in in_use:
            continue
        in_use.add(n)
        body = extra_f.get(n) or extra_v.get(n) or ''
        work_queue.extend(sorted((set(RX_IDENT.findall(body)) & extra_count) - in_use))
    info['reached_functions'] = sorted(n for n in in_use if n in extra_f)
    info['reached_variables'] = sorted(n for n in in_use if n in extra_v)
    all_entries = dict(mf)
    work_queue = sorted(set(RX_IDENT.findall(scr)) & set(all_entries))
    acquire_range = set()
    while work_queue:
        n = work_queue.pop()
        if n in acquire_range:
            continue
        acquire_range.add(n)
        work_queue.extend(sorted((set(RX_IDENT.findall(all_entries[n])) & set(all_entries)) - acquire_range))
    info['changed_functions_outside'] = [n for n in info['changed_functions'] if n not in acquire_range]
    info['changed_functions'] = [n for n in info['changed_functions'] if n in acquire_range]
    if not in_use:
        return None, info
    line_list = [
        '// ==============================================================================================',
        '// the OWN Scripts\\Blizzard.j of the map: whatever it has beyond that of the game and war3map.j reaches',
        '// (common/kk/blizzard_mapa.py: %d of %d functions and %d of %d variables extra; Reforged does not honor the'
        % (len(info['reached_functions']), len(extra_f), len(info['reached_variables']), len(extra_v)),
        '// blizzard.j of the map). Generated: do not edit by hand.',
        '// ==============================================================================================',
    ]
    for k in mv:
        if k in in_use and k in extra_v:
            line_list.append(extra_v[k])
    for k in mf:
        if k in in_use and k in extra_f:
            line_list.append(re.sub(r'^([ \t]*)constant[ \t]+function', r'\1function', extra_f[k]))
    return '\n'.join(line_list) + '\n', info


def failures_of(info):
    f = []
    if info['natives']:
        f.append(
            'the Blizzard.j of the map declares native (%s): only the engine gives them'
            % ', '.join(info['natives'][:8])
        )
    if info['colisoes']:
        f.append('more names than Reforged 3.0 already has: %s' % ', '.join(info['colisoes'][:12]))
    if info['changed_functions'] or info['changed_variables']:
        f.append(
            'the Blizzard.j of the map CHANGED %d function(s) and %d variable(s) of the game (Reforged uses its own): %s'
            % (
                len(info['changed_functions']),
                len(info['changed_variables']),
                ', '.join((info['changed_functions'] + info['changed_variables'])[:12]),
            )
        )
    return f
