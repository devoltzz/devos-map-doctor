# Finds what a map's own Blizzard.j changes or adds to the game's.
import os
import re


HERE = os.path.dirname(os.path.abspath(__file__))
VANILLA = os.path.normpath(os.path.join(HERE, '..', 'ref', '1.24', 'blizzard.j'))
REF_30 = os.path.normpath(os.path.join(HERE, '..', 'ref', '3.0'))

RX_FUNC = re.compile(
    r'^[ \t]*(constant[ \t]+)?function[ \t]+(\w+)[ \t]+takes\b.*?^[ \t]*endfunction[ \t]*(?://[^\n]*)?$', re.M | re.S
)
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


RX_SET_NULL = re.compile(r'^set (\w+) = null$')
RX_LOCAL = re.compile(r'^local (\w+) (?:array )?(\w+)(?: = (.+))?$')
RX_SET = re.compile(r'^set (\w+) = (.+)$')
EQUIVALENTS = {
    'BJDebugMsg': ['function BJDebugMsg takes string msg returns nothing\n'
                   'call DisplayTimedTextToPlayer(GetLocalPlayer(),0,0,60,msg)\nendfunction'],
}


def _code(body_text):
    output = []
    for line in body_text.split('\n'):
        toks = [t for t in RX_TOK.findall(line) if not t.startswith('//')]
        if toks:
            output.append(' '.join(toks))
    return output


def _quote_it(ln, fname):
    return re.search(r'(?<!\w)%s(?!\w)' % re.escape(fname), ln) is not None


def _null_of(ln, name_list):
    m = RX_SET_NULL.match(ln)
    return m.group(1) if m and m.group(1) in name_list else None


def free_temporaries(mv, mf, extra_v, script):
    cited = set(RX_IDENT.findall(script))
    cand = dict((g, RX_DECL_LINE.match(extra_v[g]).group(1)) for g in extra_v
                if g not in cited and RX_DECL_LINE.match(extra_v[g]))
    if not cand:
        return {}
    for f in mf.values():
        line_list = _code(f)[1:]
        for g in [x for x in set(RX_IDENT.findall(f)) if x in cand]:
            first = next((line for line in line_list if _quote_it(line, g)), None)
            s = RX_SET.match(first) if first else None
            if not (s and s.group(1) == g and not _quote_it(s.group(2), g)):
                cand.pop(g, None)
    return cand


def undo_leak_fix(func, free_slots=None):
    free_slots = free_slots or {}
    line_list = _code(func)
    if len(line_list) < 2:
        return func
    local_vars = set()
    m = re.search(r'(?<!\w)takes (.*?) returns(?!\w)', line_list[0])
    if m and m.group(1).strip() != 'nothing':
        for p in m.group(1).split(','):
            ps = p.split()
            if len(ps) == 2:
                local_vars.add(ps[1])
    for line in line_list:
        d = RX_LOCAL.match(line)
        if d:
            local_vars.add(d.group(2))
    changed = True
    while changed:
        changed = False
        max_depth, profs = 0, []
        for line in line_list:
            if line == 'loop':
                max_depth += 1
            profs.append(max_depth)
            if line == 'endloop':
                max_depth -= 1
        for i in range(len(line_list) - 1, 0, -1):
            fname = _null_of(line_list[i], local_vars)
            if not fname:
                continue
            j = i + 1
            while j < len(line_list) and _null_of(line_list[j], local_vars):
                j += 1
            next_item = line_list[j] if j < len(line_list) else 'endfunction'
            out_path = (
                next_item == 'endfunction' or next_item == 'return' or next_item.startswith('return ')
            ) and not _quote_it(next_item, fname)
            after_diag = [x for x in line_list[i + 1:] if _null_of(x, local_vars) != fname]
            if out_path or (profs[i] == 0 and not any(_quote_it(x, fname) for x in after_diag)):
                del line_list[i]
                changed = True
        for i in range(len(line_list) - 2, 0, -1):
            s = RX_SET.match(line_list[i])
            if not s or line_list[i + 1] != 'return ' + s.group(1) or _quote_it(s.group(2), s.group(1)):
                continue
            t = s.group(1)
            if t in free_slots:
                line_list[i:i + 2] = ['return ' + s.group(2)]
                changed = True
            elif t in local_vars:
                decl = [k for k, x in enumerate(line_list) if RX_LOCAL.match(x) and RX_LOCAL.match(x).group(2) == t]
                pairs = [k for k in range(1, len(line_list) - 1) if RX_SET.match(line_list[k]) and
                         RX_SET.match(line_list[k]).group(1) == t and line_list[k + 1] == 'return ' + t and
                         not _quote_it(RX_SET.match(line_list[k]).group(2), t)]
                in_use = set(decl) | set(pairs) | set(k + 1 for k in pairs)
                if len(decl) == 1 and RX_LOCAL.match(line_list[decl[0]]).group(3) is None and \
                        not any(_quote_it(x, t) for k, x in enumerate(line_list) if k not in in_use):
                    for k in sorted(pairs, reverse=True):
                        line_list[k:k + 2] = ['return ' + RX_SET.match(line_list[k]).group(2)]
                    del line_list[decl[0]]
                    local_vars.discard(t)
                    changed = True
                    break
        for i in range(len(line_list) - 2, 0, -1):
            d = RX_LOCAL.match(line_list[i])
            if d and d.group(3) is not None and line_list[i + 1] == 'return ' + d.group(2) and \
                    not any(_quote_it(x, d.group(2)) for k, x in enumerate(line_list) if k not in (i, i + 1)):
                line_list[i:i + 2] = ['return ' + d.group(3)]
                local_vars.discard(d.group(2))
                changed = True
        k = 1
        while k < len(line_list) and RX_LOCAL.match(line_list[k]):
            k += 1
        s = RX_SET.match(line_list[k]) if k < len(line_list) else None
        if s and s.group(1) in free_slots and s.group(1) not in local_vars and not _quote_it(s.group(2), s.group(1)):
            line_list[k] = 'local %s %s = %s' % (free_slots[s.group(1)], s.group(1), s.group(2))
            local_vars.add(s.group(1))
            changed = True
        for i in range(len(line_list) - 2, 0, -1):
            s = RX_SET.match(line_list[i])
            if (
                s
                and s.group(2) in local_vars
                and s.group(1) not in local_vars
                and line_list[i + 1] == 'return ' + s.group(1)
            ):
                line_list[i + 1] = 'return ' + s.group(2)
                changed = True
    return '\n'.join(line_list)


def leak_only(fname, map_func, game_func, free_slots=None):
    tgt = normalize(game_func)
    if normalize(undo_leak_fix(map_func, free_slots)) == tgt:
        return True
    map_n = normalize(map_func)
    return any(normalize(v) == map_n for v in EQUIVALENTS.get(fname, ()))


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
    changed_textures = sorted(k for k in mf if k in vf and normalize(mf[k]) != normalize(vf[k]))
    free_slots = free_temporaries(mv, mf, extra_v, scr) if changed_textures else {}
    info['leak_functions'] = [k for k in changed_textures if leak_only(k, mf[k], vf[k], free_slots)]
    info['changed_functions'] = [k for k in changed_textures if k not in set(info['leak_functions'])]
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
