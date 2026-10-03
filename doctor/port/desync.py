# Finds and fixes the script code that would desync a multiplayer game on Warcraft III 3.0.
import hashlib
import os
import re
import struct


RX_END_GLOBALS_BLOCK = re.compile(r'(?m)^endglobals\s*$')
RX_FUNCTION = re.compile(r'(?m)^function\s+\w+\s+takes\b')
RX_FUNCTION_NAME = re.compile(r'^[ \t]*function\s+(\w+)\s+takes\b')
RX_MAIN = re.compile(r'(?m)^function main takes nothing returns nothing[ \t]*\r?$')
RX_LOCAL_LINE = re.compile(r'\n[ \t]*local\b[^\n]*')
DEFAULT_MARK = '// [framework KK] passo 3q (common/kk/desync.py): the static terrain height'
DEFAULT_MAIN_CALL = ('call KK_zt_carrega() // [framework KK] step 3q: the static terrain height (KK_z), before '
                     'of any effect')
BLOCO = 2500
Z_BASE = 4096
COLUMN_STEP = 16384
PLATFORMS = {b'OTip': 64.0, b'OTis': 32.0}
def read_w3e(file_path):
    b = open(file_path, 'rb').read()
    if b[:4] != b'W3E!':
        raise ValueError('not a war3map.w3e: %r' % b[:4])
    o = 4 + 4 + 1 + 4
    (n,) = struct.unpack_from('<i', b, o)
    o += 4 + 4 * n
    (n,) = struct.unpack_from('<i', b, o)
    o += 4 + 4 * n
    w, h = struct.unpack_from('<ii', b, o)
    o += 8
    ox, oy = struct.unpack_from('<ff', b, o)
    o += 8
    if len(b) < o + w * h * 7:
        raise ValueError('war3map.w3e truncated: %d B for %d x %d tilepoints' % (len(b), w, h))
    q = []
    for j in range(h):
        base = o + j * w * 7
        ln = []
        for i in range(w):
            p = base + i * 7
            ground = struct.unpack_from('<H', b, p)[0]
            layer = b[p + 6] & 0x0F
            ln.append(ground - 8192 + (layer - 2) * 512)
        q.append(ln)
    return w, h, ox, oy, q


def read_platforms(file_path):
    b = open(file_path, 'rb').read()
    if b[:4] != b'W3do':
        raise ValueError('not a war3map.doo')
    ver, sub, n = struct.unpack_from('<iii', b, 4)
    o = 16
    out = []
    for _ in range(n):
        tid = b[o:o + 4]
        o += 8
        x, y, z = struct.unpack_from('<fff', b, o)
        o += 16
        sx, sy, _sz = struct.unpack_from('<fff', b, o)
        o += 12 + 2 + 4
        (ns,) = struct.unpack_from('<i', b, o)
        o += 4
        for _s in range(ns):
            (ni,) = struct.unpack_from('<i', b, o)
            o += 4 + 8 * ni
        o += 4
        if tid in PLATFORMS:
            out.append((tid, x, y, z, sx, sy))
    if o > len(b):
        raise ValueError('war3map.doo read past the end')
    return out


def apply_platforms(q, w, h, ox, oy, platforms):
    n_platforms = 0
    raised_ones = set()
    chao = [ln[:] for ln in q]
    for tid, x, y, z, sx, sy in platforms:
        i0 = int(round((x - ox) / 128.0))
        j0 = int(round((y - oy) / 128.0))
        if not (0 <= i0 < w and 0 <= j0 < h):
            continue
        zq = int(round(z * 4.0))
        if zq <= chao[j0][i0] + 4:
            continue
        n_platforms += 1
        mx = PLATFORMS[tid] * abs(sx)
        my = PLATFORMS[tid] * abs(sy)
        for j in range(max(0, int((y - my - oy) // 128.0)), min(h - 1, int((y + my - oy) // 128.0) + 1) + 1):
            ty = oy + 128.0 * j
            if abs(ty - y) > my + 1e-3:
                continue
            for i in range(max(0, int((x - mx - ox) // 128.0)), min(w - 1, int((x + mx - ox) // 128.0) + 1) + 1):
                tx = ox + 128.0 * i
                if abs(tx - x) > mx + 1e-3:
                    continue
                if zq > q[j][i]:
                    q[j][i] = zq
                    raised_ones.add((i, j))
    return n_platforms, len(raised_ones)


OUT_OF_RANGE = [0]


def segments(q):
    runs, idx = [], []
    OUT_OF_RANGE[0] = 0
    for ln in q:
        idx.append(len(runs))
        prev_item = None
        for i, v in enumerate(ln):
            if not (0 <= v + Z_BASE < COLUMN_STEP):
                v = max(-Z_BASE, min(COLUMN_STEP - 1 - Z_BASE, v))
                ln[i] = v
                OUT_OF_RANGE[0] += 1
            if v != prev_item:
                runs.append(i * COLUMN_STEP + v + Z_BASE)
                prev_item = v
    idx.append(len(runs))
    return runs, idx


def table_z(runs, idx, w, h, ox, oy, x, y):
    def pair(i, j):
        lo, hi = idx[j], idx[j + 1] - 1
        end_pos = hi
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if runs[mid] // COLUMN_STEP <= i:
                lo = mid
            else:
                hi = mid - 1
        current_val = runs[lo] % COLUMN_STEP
        byte_total = current_val
        if lo < end_pos and runs[lo + 1] // COLUMN_STEP <= i + 1:
            byte_total = runs[lo + 1] % COLUMN_STEP
        return current_val, byte_total
    fx = min(max((x - ox) / 128.0, 0.0), float(w - 1))
    fy = min(max((y - oy) / 128.0, 0.0), float(h - 1))
    i = min(int(fx), w - 2)
    j = min(int(fy), h - 2)
    fx -= i
    fy -= j
    current_val, byte_total = pair(i, j)
    a = current_val + (byte_total - current_val) * fx
    current_val, byte_total = pair(i, j + 1)
    b = current_val + (byte_total - current_val) * fx
    return (a + (b - a) * fy - Z_BASE) * 0.25


def verify(runs, idx, w, h, ox, oy, q, failures):
    wrong_ones = 0
    for j in range(h - 1):
        for i in range(w - 1):
            z = table_z(runs, idx, w, h, ox, oy, ox + 128.0 * i, oy + 128.0 * j)
            if abs(z - q[j][i] / 4.0) > 1e-6:
                wrong_ones += 1
    if wrong_ones:
        failures.append('the table returns a different height at %d tilepoints' % wrong_ones)
    return wrong_ones


def block_grid(ext, extract=None):
    cpath = os.path.join(ext, 'war3map.w3e')
    if not os.path.isfile(cpath) and extract:
        cpath = os.path.join(extract, 'war3map.w3e')
    doo = os.path.join(ext, 'war3map.doo')
    if not os.path.isfile(doo) and extract:
        doo = os.path.join(extract, 'war3map.doo')
    w, h, ox, oy, q = read_w3e(cpath)
    platforms = read_platforms(doo)
    n_platforms, n_tilepoints = apply_platforms(q, w, h, ox, oy, platforms)
    sha = hashlib.sha256(open(cpath, 'rb').read() + open(doo, 'rb').read()).hexdigest()[:16]
    return w, h, ox, oy, q, n_platforms, n_tilepoints, len(platforms), sha


def table_text(w, h, ox, oy, runs, idx, mark=DEFAULT_MARK):
    L = [
        mark + ' (KK_z)',
        '// GENERATED from the war3map.w3e + war3map.doo of the delivery (%d x %d tilepoints, corner (%.1f, %.1f)): %d pieces of'
        % (w, h, ox, oy, len(runs)),
        '// same height, each one `column*16384 + height in quarters + 4096`; `DB_zi[j]` = the first stretch of the row',
        '// j. Each block in its own thread (`ExecuteFunc`); `DB_z_pronto` only with the whole table.',
    ]
    name_list = []
    for b0 in range(0, len(runs), BLOCO):
        fname = 'KK_zt_%d' % (b0 // BLOCO)
        name_list.append(fname)
        L.append('function %s takes nothing returns nothing' % fname)
        end_pos = min(b0 + BLOCO, len(runs))
        for k in range(b0, end_pos):
            L.append('    set DB_zr%d[%d]=%d' % (k // 32768, k % 32768, runs[k]))
        L.append('    set DB_z_n=DB_z_n+%d' % (end_pos - b0))
        L.append('endfunction')
    name_list.append('KK_zt_linhas')
    L.append('function KK_zt_linhas takes nothing returns nothing')
    for j, v in enumerate(idx):
        L.append('    set DB_zi[%d]=%d' % (j, v))
    L.append('    set DB_z_n=DB_z_n+%d' % len(idx))
    L.append('endfunction')
    total = len(runs) + len(idx)
    L.append('function KK_zt_carrega takes nothing returns nothing')
    L.append('    set DB_z_n=0')
    for n in name_list:
        L.append('    call ExecuteFunc("%s")' % n)
    L.append('    if DB_z_n==%d then' % total)
    L.append('        set DB_z_ox=%s' % repr(float(ox)))
    L.append('        set DB_z_oy=%s' % repr(float(oy)))
    L.append('        set DB_z_w=%d' % w)
    L.append('        set DB_z_h=%d' % h)
    L.append('        set DB_z_pronto=true')
    L.append('    endif')
    L.append('endfunction')
    return '\n'.join(L) + '\n', len(name_list)


_AUTHOR_MAP = {}


def map_functions(raw_data):
    if raw_data not in _AUTHOR_MAP:
        t = open(raw_data, 'rb').read().decode('utf-8', 'surrogateescape')
        _AUTHOR_MAP[raw_data] = set(re.findall(r'(?m)^[ \t]*function\s+(\w+)\s+takes', t))
    return _AUTHOR_MAP[raw_data]


def troca_leituras(body_text, raw_data):
    autora = map_functions(raw_data)
    line_list = body_text.split('\n')
    fn = None
    replacements = voo = 0
    by_function = {}
    outside = {}
    for k, line in enumerate(line_list):
        m = RX_FUNCTION_NAME.match(line)
        if m:
            fn = m.group(1)
        n = line.count('GetLocationZ(')
        if not n:
            continue
        if fn not in autora:
            outside[fn] = outside.get(fn, 0) + n
            continue
        if 'SetUnitFlyHeight(' in line:
            voo += n
            continue
        line_list[k] = line.replace('GetLocationZ(', 'KK_zl(')
        replacements += n
        by_function[fn] = by_function.get(fn, 0) + n
    return '\n'.join(line_list), replacements, voo, by_function, outside


def applies(body_text, cfg, to_report=False):
    failures = []
    info = {'failures': failures, 'done': False}
    if 'function KK_zt_carrega takes' in body_text:
        return body_text, info
    exp_len = cfg.get('expected_count') or {}
    body_text, replacements, voo, by_function, outside = troca_leituras(body_text, cfg['raw_data'])
    info.update({'replacements': replacements, 'voo': voo, 'swapped_functions': len(by_function), 'outside': outside})
    if (exp_len.get('replacements') is not None and replacements != exp_len['replacements']) or (
        exp_len.get('voo') is not None and voo != exp_len['voo']
    ):
        failures.append('height reads: %d swapped (measured %s) and %d flight-height kept (measured %s)'
                        % (replacements, exp_len.get('replacements'), voo, exp_len.get('voo')))
    try:
        w, h, ox, oy, q, n_platforms, n_tilepoints, n_platform_total, sha = block_grid(cfg['ext'], cfg.get('extract'))
    except (OSError, ValueError, struct.error) as e:
        failures.append('terrain: %s' % e)
        return body_text, info
    runs, idx = segments(q)
    if OUT_OF_RANGE[0]:
        info['out_of_range'] = OUT_OF_RANGE[0]
        print(
            'WARNING 3q: %d tilepoint(s) with height outside the encodable range, at the edge of the range'
            % OUT_OF_RANGE[0]
        )
    info.update({'w': w, 'h': h, 'ox': ox, 'oy': oy, 'segments': len(runs), 'sha': sha, 'platforms': n_platforms,
                 'platforms_total': n_platform_total, 'platform_tilepoints': n_tilepoints})
    if (exp_len.get('line_list') is not None and h != exp_len['line_list']) or (exp_len.get('segments') is not None
                                                                                and len(runs) != exp_len['segments']):
        failures.append('table: %d lines / %d chunks, measured is %s / %s (new terrain? `--mede`)'
                        % (h, len(runs), exp_len.get('line_list'), exp_len.get('segments')))
    if (exp_len.get('platforms') is not None and n_platforms != exp_len['platforms']) or (
            exp_len.get('platform_tilepoints') is not None and n_tilepoints != exp_len['platform_tilepoints']):
        failures.append('platforms: %d above the ground rising %d tilepoints, measured is %s / %s'
                        % (n_platforms, n_tilepoints, exp_len.get('platforms'), exp_len.get('platform_tilepoints')))
    if len(runs) > 131072:
        failures.append('table: %d runs do not fit in four arrays' % len(runs))
    elif len(runs) > 65536:
        info['vectors'] = 4
    info['wrong_ones'] = verify(runs, idx, w, h, ox, oy, q, failures)
    block_entry, n_funcs = table_text(w, h, ox, oy, runs, idx, cfg.get('mark', DEFAULT_MARK))
    info['functions'] = n_funcs
    if 'StringHash(' in block_entry:
        failures.append('the injected text has StringHash( (the 3k would count extra)')
    if cfg.get('copy'):
        try:
            os.makedirs(os.path.dirname(cfg['copy']), exist_ok=True)
            open(cfg['copy'], 'w', encoding='utf-8', newline='\n').write(block_entry)
        except OSError:
            pass
    m = RX_END_GLOBALS_BLOCK.search(body_text)
    if not m:
        failures.append('could not find endglobals')
        return body_text, info
    f = RX_FUNCTION.search(body_text, m.end())
    if not f:
        failures.append('did not find a function after the endglobals')
        return body_text, info
    body_text = body_text[:f.start()] + block_entry + '\n' + body_text[f.start():]
    matches = list(RX_MAIN.finditer(body_text))
    if len(matches) != 1:
        failures.append('function main: %d, expected 1' % len(matches))
        return body_text, info
    line_end = matches[0].end()
    cr = '\r' if body_text[line_end - 1:line_end] == '\r' else ''
    pos = line_end
    while True:
        m_local = RX_LOCAL_LINE.match(body_text, pos)
        if not m_local:
            break
        pos = m_local.end()
    body_text = body_text[:pos] + '\n\t' + cfg.get('main_call', DEFAULT_MAIN_CALL) + cr + body_text[pos:]
    info['done'] = True
    if to_report and not failures:
        report_data(info)
    return body_text, info


def report_data(info):
    print(
        'static terrain height (3q): table %s (%d x %d tilepoints + %d walkable platforms above the ground, %d '
        'snippets, %d load functions, %d tilepoints checked wrong); %d GetLocationZ reads of the author -> '
        'KK_zl in %d functions, %d conversions to dummy flight height kept; outside the author (another owner): %s'
        % (
            info.get('sha'),
            info.get('w', 0),
            info.get('h', 0),
            info.get('platforms', 0),
            info.get('segments', 0),
            info.get('functions', 0),
            info.get('wrong_ones', -1),
            info.get('replacements', 0),
            info.get('swapped_functions', 0),
            info.get('voo', 0),
            info.get('outside'),
        )
    )
