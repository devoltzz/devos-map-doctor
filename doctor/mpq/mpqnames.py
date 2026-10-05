# Recovers file names from their hashes and from what the map itself mentions.
import array
import bisect
import os
import re
import struct
import sys
import zlib


HERE = os.path.dirname(os.path.abspath(__file__))
COMMON = os.path.dirname(HERE)
ROOT = os.path.dirname(COMMON)
CACHE = os.path.join(COMMON, 'cache')
INDEX = os.path.join(CACHE, 'names.idx')
MAGIC = b'W3XIDX1\n'


class NameIndex:
    def __init__(self, ha, hb, offs, name_list):
        self.ha = ha
        self.hb = hb
        self.offs = offs
        self.name_list = name_list

    def __len__(self):
        return len(self.ha)

    def fname(self, i):
        return self.name_list[self.offs[i]:self.offs[i + 1]].decode('utf-8', 'replace')

    def lookup(self, hA, hB):
        i = bisect.bisect_left(self.ha, hA)
        while i < len(self.ha) and self.ha[i] == hA:
            if self.hb[i] == hB:
                return self.fname(i)
            i += 1
        return None

    def lookup_a_only(self, hA):
        i = bisect.bisect_left(self.ha, hA)
        out = []
        while i < len(self.ha) and self.ha[i] == hA:
            out.append(self.fname(i))
            i += 1
        return out


def load_data(file_path=INDEX):
    if not os.path.exists(file_path):
        return None
    with open(file_path, 'rb') as fh:
        if fh.read(len(MAGIC)) != MAGIC:
            return None
        (sz,) = struct.unpack('<I', fh.read(4))
        body = zlib.decompress(fh.read())
    if len(body) != sz:
        return None
    (n,) = struct.unpack_from('<I', body, 0)
    p = 4
    ha = array.array('I')
    ha.frombytes(body[p:p + 4 * n])
    p += 4 * n
    hb = array.array('I')
    hb.frombytes(body[p:p + 4 * n])
    p += 4 * n
    offs = array.array('I')
    offs.frombytes(body[p:p + 4 * (n + 1)])
    p += 4 * (n + 1)
    return NameIndex(ha, hb, offs, body[p:])


BIG_INDEX = os.path.join(
    os.path.dirname(sys.executable)
    if getattr(sys, 'frozen', False)
    else os.path.normpath(os.path.join(HERE, '..', '..')),
    'names.npz',
)


class BigIndex(object):
    def __init__(self, file_path=BIG_INDEX):
        import numpy as np
        z = np.load(file_path)
        self.np = np
        self.hash_key = z['hash_key']
        self.h3 = z['h3']
        self.offs = z['offs']
        self.blob = z['blob'].tobytes()
        self._order3 = None

    def __len__(self):
        return len(self.hash_key)

    def fname(self, i):
        return self.blob[self.offs[i]:self.offs[i + 1]].decode('utf-8', 'surrogateescape')

    def lookup_batch(self, ha, hb):
        np = self.np
        k = (np.asarray(ha, dtype=np.uint64) << np.uint64(32)) | np.asarray(hb, dtype=np.uint64)
        pos = np.searchsorted(self.hash_key, k)
        pos[pos >= len(self.hash_key)] = 0
        return np.where(self.hash_key[pos] == k, pos, -1)

    def by_key3(self, k):
        np = self.np
        if self._order3 is None:
            self._order3 = np.argsort(self.h3, kind='stable')
            self._h3_ord = self.h3[self._order3]
        a = np.searchsorted(self._h3_ord, np.uint32(k), side='left')
        b = np.searchsorted(self._h3_ord, np.uint32(k), side='right')
        return [int(i) for i in self._order3[a:b]]


def load_big(file_path=BIG_INDEX):
    if not os.path.exists(file_path):
        return None
    return BigIndex(file_path)


EXT_EQUIV = [
    ('.w3m', '.w3x', '.mpq', '.pud'),
    ('.txt', '.ini'),
    ('.j', '.lua'),
    ('.wav', '.mp3', '.ogg'),
    ('.mdl', '.mdx'),
    ('.blp', '.tga', '.jpg', '.dds', '.gif', '.png'),
    ('.ttf', '.otf'),
]
PROTECTOR_PREFIXES = ('DIS', 'PAS', 'DISDIS', 'DISPAS')


def variants(fname, cap=48, rounds=3):
    fname = fname.strip()
    if not fname:
        return set()
    current = {fname}
    direct = set()
    for r in range(rounds):
        new = set(current)
        for n in sorted(current):
            if r and len(new) >= cap:
                break
            root, ext = os.path.splitext(n)
            e = ext.lower()
            for cluster in EXT_EQUIV:
                if e in cluster:
                    for height in cluster:
                        if height != e:
                            new.add(root + height)
            base = os.path.basename(root)
            folder = os.path.dirname(root)
            for p in PROTECTOR_PREFIXES:
                if base.upper().startswith(p):
                    new.add(os.path.join(folder, base[len(p):].lstrip('_- ')) + ext)
                else:
                    new.add(os.path.join(folder, p + base) + ext)
                    new.add(os.path.join(folder, p + '_' + base) + ext)
            if not root.upper().endswith('_PORTRAIT'):
                new.add(root + '_PORTRAIT' + ext)
        if r == 0:
            direct = set(new)
        if new == current or len(new) >= cap:
            current = new
            break
        current = new
    if len(direct) >= cap:
        output = {n for n in sorted(direct)[:cap] if n}
    else:
        rest = sorted(current - direct)
        output = {n for n in list(direct) + rest[:cap - len(direct)] if n}
    root, ext = os.path.splitext(fname)
    if ext.lower() == '.mdl' and not root.upper().endswith('_PORTRAIT'):
        output.add(root + '_PORTRAIT.mdx')
    return output


_EXTENSIONS_B = (
    rb'(?:mdx|mdl|blp|tga|jpg|dds|gif|png|wav|mp3|ogg|ttf|otf|fdf|toc|slk|ini|txt|'
    rb'j|lua|w3a|w3t|w3u|w3d|w3b|w3h|w3q|w3i|w3e|w3r|w3c|w3s|wts|doo|shd|wpm|mmp|imp|pld)')
RE_PATH_B = re.compile(
    rb'[A-Za-z0-9_\-\\/\.\[\(!#$%&@^~{=][A-Za-z0-9_\-\\/\. \[\]\(\)\+!#$%&@^~{}=]{0,180}?\.' + _EXTENSIONS_B,
    re.I)
RE_EXTENSION_B = re.compile(rb'\.' + _EXTENSIONS_B, re.I)
RE_EXTENSION_NUL_B = re.compile(rb'\.' + _EXTENSIONS_B + rb'(?=\x00)', re.I)
PATH_REACH = 181
PATH_EXT_MAX = 3
RE_REQUIRE_B = re.compile(rb'''require\s*\(?\s*['"]([\w.\-/\\ ]{1,120})['"]''')


def _paths(data_bytes):
    segments = []
    for m in RE_EXTENSION_B.finditer(data_bytes):
        s, e = max(0, m.start() - PATH_REACH), m.start() + 1 + PATH_EXT_MAX
        if segments and s <= segments[-1][1]:
            segments[-1][1] = e
        else:
            segments.append([s, e])
    for s, e in segments:
        yield from RE_PATH_B.finditer(data_bytes, s, min(e, len(data_bytes)))


def nul_values(data_bytes):
    out = set()
    for m in RE_EXTENSION_NUL_B.finditer(data_bytes):
        i = m.start()
        j = i
        lim = max(0, i - 200)
        while j > lim and 0x20 <= data_bytes[j - 1] <= 0x7e:
            j -= 1
        if j < i and j > 0 and data_bytes[j - 1] == 0:
            out.add(data_bytes[j:m.end()])
    return out


def mdx_textures(data_bytes):
    out = set()
    i = data_bytes.find(b'TEXS')
    if i < 0 or i + 8 > len(data_bytes):
        return out
    sz = int.from_bytes(data_bytes[i + 4:i + 8], 'little')
    if sz % 268 or i + 8 + sz > len(data_bytes):
        return out
    for k in range(i + 8, i + 8 + sz, 268):
        c = data_bytes[k + 4:k + 264].split(b'\0')[0].decode('latin-1', 'replace').replace('/', '\\').strip()
        if c:
            out.add(c)
    return out


def mine_bytes(data_bytes):
    out = set()
    if data_bytes[:4] == b'MDLX':
        out |= mdx_textures(data_bytes)
    if b'\x00' in data_bytes:
        out.update(v.decode('latin-1').replace('/', '\\') for v in nul_values(data_bytes))
    for m in _paths(data_bytes):
        s = m.group(0).decode('latin-1', 'replace').replace('/', '\\').strip()
        s = s.strip('"\' \t\r\n\x00')
        if not s or re.search(r'\.\.[\\/]', s):
            continue
        readings = [s]
        if '=' in s:
            readings.append(s.rsplit('=', 1)[-1].strip())
        if ' ' in s:
            words = s.split(' ')
            i = next((k for k, p in enumerate(words) if '\\' in p), None)
            if i:
                readings.append(' '.join(words[i:]))
            readings.append(words[-1])
        for s in readings:
            if not s:
                continue
            out.add(s)
            u = re.sub(r'\\{2,}', lambda _m: '\\', s)
            if u != s:
                out.add(u)
    if b'require' in data_bytes:
        for m in RE_REQUIRE_B.finditer(data_bytes):
            module = m.group(1).decode('latin-1').replace('/', '\\')
            file_path = module.replace('.', '\\')
            out.update((file_path + '.lua', file_path + '\\init.lua', module + '.lua'))
    return out


EXT_TO_MINE = frozenset((
    '.j', '.lua', '.txt', '.ini', '.slk', '.wts', '.w3i', '.doo', '.wtg', '.wct',
    '.imp', '.mdx', '.mdl', '.fdf', '.toc', '.pld', '.json', '.xml', '.html',
    '.w3a', '.w3t', '.w3u', '.w3d', '.w3b', '.w3h', '.w3q', '.w3e', '.w3r',
    '.w3c', '.w3s', '.wpm', '.mmp',
))


def _with_hash_entry(a, name_list):
    ht = getattr(a, 'ht', None)
    n_ht = getattr(a, 'hash_n_read', None)
    if not name_list or ht is None or n_ht is None:
        return name_list
    from doctor.mpq import mpqlib as M
    pairs = set(zip(ht[0:4 * n_ht:4], ht[1:4 * n_ht:4]))
    enc = [n.encode('utf-8', 'surrogateescape') for n in name_list]
    h1, h2 = M.hashstr_batch(enc, 1), M.hashstr_batch(enc, 2)
    return [n for n, x, y in zip(name_list, h1, h2) if (int(x), int(y)) in pairs]


def referenced_closure(a, seeds=None, log=None):
    if seeds is None:
        seeds = list(BASE_NAMES) + ['scripts\\war3map.j', 'war3map.imp', 'war3mapSkin.txt', 'war3mapMisc.txt',
                                    'war3mapPath.tga', 'war3map.w3s', 'war3mapUnits.doo']
        from doctor.data import map_formats
        seeds += [n for n in map_formats.standard_names() if n.startswith(map_formats.LOCALE_DIR)]
    seen = {}
    work_queue = []
    keys = set()

    def accept(n, from_game=False):
        k = n.upper()
        if k in keys:
            return
        r = a.find(n)
        ok = bool(r) and is_valid_name(a, r[1], n)
        if r and not ok and hasattr(a, 'find_locale'):
            r2 = a.find_locale(n)
            if r2 and r2[1] != r[1] and is_valid_name(a, r2[1], n):
                r, ok = r2, True
        if ok:
            if from_game:
                try:
                    d = a.read(n, bi=r[1])
                except Exception:
                    return
                if not d or not content_matches(n, d):
                    return
            keys.add(k)
            seen[n] = r[1]
            work_queue.append(n)

    for n in seeds:
        accept(n.replace('/', '\\'))
    for n in GAME_NAMES:
        accept(n, from_game=True)
    round_num = 0
    while work_queue:
        round_num += 1
        current, work_queue[:] = list(work_queue), []
        candidates = set()
        for n in current:
            try:
                d = a.read(n, bi=seen[n])
            except Exception:
                continue
            if d:
                candidates |= mine_bytes(d[:16 * 1048576])
        expanded = set()
        for c in candidates:
            expanded |= variants(c)
        for c in _with_hash_entry(a, [c for c in sorted(expanded) if c not in seen]):
            accept(c)
        if log:
            log(
                'closure, round %d: %d candidates, +%d referenced (total %d)'
                % (round_num, len(expanded), len(work_queue), len(seen))
            )
    return seen


SIGNATURES = {'.blp': (b'BLP1', b'BLP2'), '.mdx': (b'MDLX',), '.w3x': (b'HM3W',), '.w3m': (b'HM3W',),
              '.w3n': (b'HM3W', b'MPQ\x1a'),
              '.wav': (b'RIFF',), '.mp3': (b'ID3', b'\xff\xfb', b'\xff\xf3', b'\xff\xf2'), '.jpg': (b'\xff\xd8\xff',),
              '.dds': (b'DDS ',), '.exe': (b'MZ',), '.dll': (b'MZ',), '.asi': (b'MZ',), '.mix': (b'MZ',),
              '.m3d': (b'MZ',), '.flt': (b'MZ',), '.ogg': (b'OggS',), '.png': (b'\x89PNG',),
              '.gif': (b'GIF87a', b'GIF89a'), '.zip': (b'PK\x03\x04',), '.rar': (b'Rar!',), '.7z': (b'7z\xbc\xaf',)}
EXT_TEXT = frozenset(('.ai', '.j', '.txt', '.fdf', '.toc', '.slk', '.html', '.pld', '.lua', '.ini', '.js', '.css',
                      '.wai', '.htm', '.xml', '.json', '.md', '.csv'))


def looks_random(data_bytes, n=4096):
    header = data_bytes[:n]
    if len(header) < 1024:
        return False
    expected_len = len(header) / 256.0
    tally = [0] * 256
    for c in header:
        tally[c] += 1
    return sum((x - expected_len) ** 2 for x in tally) / expected_len < 400


def content_matches(fname, data_bytes, raw_data=False):
    ext = os.path.splitext(fname)[1].lower()
    if ext in SIGNATURES:
        return data_bytes.startswith(SIGNATURES[ext])
    if ext in EXT_TEXT:
        header = data_bytes[:4096]
        if any(header.startswith(s) for ss in SIGNATURES.values() for s in ss):
            return False
        return not any(c < 9 or 13 < c < 32 for c in header if c not in (27, 30, 31))
    return not (raw_data and looks_random(data_bytes))


def read_by_name(a, bi, fname):
    try:
        data_bytes = a.read(fname, bi=bi)
    except Exception:
        return False
    return data_bytes is not None and len(data_bytes) == a.blocks[bi][2] and content_matches(fname, data_bytes)


def is_valid_name(a, bi, fname):
    from doctor.mpq import mpqread
    v, detail = a.validate(bi, fname)
    if v != 'ok':
        return v == 'invalid' and read_by_name(a, bi, fname)
    if detail in mpqread.VALID_FOR_GAME:
        try:
            return content_matches(fname, a.read(fname, bi=bi) or b'')
        except Exception:
            return False
    return True


LEFTOVER_CATEGORIES = ('leftovers', 'invalid_decoy', 'alias_decoy', 'empty_decoy', 'wrong_type_decoy', 'no_block')


def dictionary_leftovers(a, closure, name_list):
    cat = dict.fromkeys(LEFTOVER_CATEGORIES, 0)
    accepted = {}
    intervals = sorted(a.interval(bi, n) for n, bi in closure.items())
    starts = [iv[0] for iv in intervals]
    max_end = []
    m = -1
    for iv in intervals:
        m = max(m, iv[1])
        max_end.append(m)
    closure_blocks = set(closure.values())
    keys = set(n.upper() for n in closure)
    for n in dict.fromkeys(x.replace('/', '\\') for x in name_list):
        k = n.upper()
        if k in keys or n in ('(listfile)', '(signature)', '(attributes)'):
            continue
        keys.add(k)
        r = a.find(n)
        if not r:
            cat['no_block'] += 1
            continue
        if a.validate(r[1], n)[0] != 'ok':
            cat['invalid_decoy'] += 1
            continue
        begin, end_pos = a.interval(r[1], n)
        j = bisect.bisect_right(starts, end_pos - 1) - 1
        if r[1] in closure_blocks or (j >= 0 and end_pos > begin and max_end[j] > begin):
            cat['alias_decoy'] += 1
            continue
        d = a.read(n, bi=r[1])
        if not d:
            cat['empty_decoy'] += 1
            continue
        if not content_matches(n, d):
            cat['wrong_type_decoy'] += 1
            continue
        accepted[n] = r[1]
        cat['leftovers'] += 1
    return accepted, cat


DISABLED_FOLDER = 'ReplaceableTextures\\CommandButtonsDisabled\\'
IMAGE_EXT = ('.blp', '.tga', '.dds')
MODEL_EXT = ('.mdx', '.mdl')
IMPORTED_FOLDERS = ('', 'war3mapImported\\')
DERIVED_LIMIT = 3000000
UNNAMED_TEXT_MAX = 8 << 20


def mdx_inner_name(data_bytes):
    if data_bytes[:4] != b'MDLX':
        return ''
    p = 4
    while p + 8 <= len(data_bytes):
        sz = int.from_bytes(data_bytes[p + 4:p + 8], 'little')
        if data_bytes[p:p + 4] == b'MODL':
            return data_bytes[p + 8:p + 88].split(b'\0')[0].decode('latin-1', 'replace').strip()
        p += 8 + sz
    return ''


def unnamed_blocks(a, with_name):
    return [bi for bi in a.pointed_blocks() if bi not in with_name]


def read_unnamed(a, bi, whole=True):
    from doctor.mpq import mpqread
    try:
        if a.blocks[bi][3] & mpqread.FLAG_ENCRYPT:
            hash_key = a.unnamed_key(bi)
            return a.read(None, bi=bi, hash_key=hash_key) if hash_key is not None else None
        if whole:
            return a.read(None, bi=bi)
        v, begin_pos = a.validate_light(bi, None)
        return begin_pos if v == 'ok' else None
    except Exception:
        return None


def derived_names(a, name_list, log=None):
    from doctor.mpq import mpqread
    known = {}
    for n in name_list:
        r = a.find(n)
        if r:
            known.setdefault(n.replace('/', '\\'), r[1])
    with_name = set(known.values())
    with_name.update(r[1] for r in (a.find(n) for n in ('(listfile)', '(attributes)', '(signature)')) if r)
    nameless = set(unnamed_blocks(a, with_name))
    if not nameless:
        return {}
    keys = set(n.upper() for n in known)
    models = {}
    from_texts = set()
    for bi in sorted(nameless):
        d = read_unnamed(a, bi, whole=False)
        if not d:
            continue
        model = d[:4] == b'MDLX'
        body_text = not model and a.blocks[bi][2] <= UNNAMED_TEXT_MAX and content_matches('x.txt', d[:4096])
        if not model and not body_text:
            continue
        if not a.blocks[bi][3] & mpqread.FLAG_ENCRYPT:
            d = read_unnamed(a, bi)
        if d and model:
            models[bi] = (mdx_inner_name(d), sorted(mdx_textures(d)))
        elif d:
            for c in mine_bytes(d):
                from_texts |= variants(c)
    matches = {}
    tested = set()

    def try_names(candidates):
        cand = sorted(set(c for c in candidates if c and c.upper() not in keys) - tested)[:DERIVED_LIMIT]
        tested.update(cand)
        opens = [c for c in _with_hash_entry(a, cand) if (a.find(c) or (None, None))[1] in nameless]
        if not opens:
            return []
        accepted, _cat = dictionary_leftovers(a, dict(known, **matches), opens)
        for n in sorted(accepted):
            matches[n] = accepted[n]
            keys.add(n.upper())
            nameless.discard(accepted[n])
        return sorted(accepted)

    def folder(n):
        return n.rsplit('\\', 1)[0] + '\\' if '\\' in n else ''

    cand = []
    for n in known:
        root, ext = os.path.splitext(n.rsplit('\\', 1)[-1])
        if ext.lower() in IMAGE_EXT and not root.upper().startswith('DIS'):
            cand.extend(DISABLED_FOLDER + 'DIS' + root + e for e in IMAGE_EXT)
    cand.extend(from_texts)
    new_ones = try_names(cand)
    model_folders = set(IMPORTED_FOLDERS) | set(folder(n) for n in known if n.lower().endswith(MODEL_EXT))
    round_num = 0
    while True:
        round_num += 1
        cand = []
        for bi, (inner, textures) in sorted(models.items()):
            if bi not in nameless:
                continue
            folders = model_folders | set(folder(t) for t in textures)
            for base in sorted({inner, inner.replace(' ', ''), inner.replace(' ', '_')} - {''}):
                for p in sorted(folders):
                    cand.append(p + base + '.mdx')
                    if not base.upper().endswith('_PORTRAIT'):
                        cand.append(p + base + '_Portrait.mdx')
        for _inner, textures in models.values():
            for t in textures:
                cand.extend(variants(t))
                cand.extend(p + t.rsplit('\\', 1)[-1] for p in IMPORTED_FOLDERS)
        for n in new_ones:
            if os.path.splitext(n)[1].lower() not in EXT_TO_MINE:
                continue
            try:
                d = a.read(n, bi=matches[n])
            except Exception:
                continue
            for c in mine_bytes((d or b'')[:16 * 1048576]):
                cand.extend(variants(c))
        new_ones = try_names(cand)
        if log:
            log('unnamed, round %d: %d candidates, +%d (total %d, %d left)' % (round_num, len(set(cand)), len(new_ones),
                                                                                  len(matches), len(nameless)))
        if not new_ones:
            return matches


def full_closure(a, seeds=None, log=None):
    closure = referenced_closure(a, seeds, log)
    for n, bi in sorted(derived_names(a, closure, log).items()):
        closure.setdefault(n, bi)
    return closure


BASE_NAMES = (
    'war3map.j', 'war3map.lua', 'war3map.w3i', 'war3map.wts', 'war3map.wtg',
    'war3map.wct', 'war3map.w3e', 'war3map.w3a', 'war3map.w3b', 'war3map.w3d',
    'war3map.w3h', 'war3map.w3q', 'war3map.w3t', 'war3map.w3u', 'war3map.w3c',
    'war3map.w3s', 'war3map.w3r', 'war3map.wpm', 'war3map.doo', 'war3map.shd',
    'war3map.mmp', 'war3map.imp', 'war3mapMisc.txt', 'war3mapSkin.txt',
    'war3mapExtra.txt', 'war3MapUnits.doo', 'war3mapMap.blp', 'war3mapPreview.tga',
    'war3mapSkin.w3u', 'war3mapSkin.w3t', 'war3mapSkin.w3a', 'war3mapSkin.w3b', 'war3mapSkin.w3d', 'war3mapSkin.w3h',
    'war3mapSkin.w3q',
    'conversation.json', 'war3map.w3l', 'war3mapPostProcessing.txt', 'war3map.w3grp', 'war3map.soundasset',
)

GAME_NAMES = tuple(
    [
        'Scripts\\Blizzard.j',
        'Scripts\\common.j',
        'Units\\MiscData.txt',
        'Units\\MiscGame.txt',
        'UI\\MiscData.txt',
        'Doodads\\Doodads.slk',
    ]
    + [
        'Units\\%s.slk' % n
        for n in (
            'UnitData',
            'UnitUI',
            'UnitBalance',
            'UnitAbilities',
            'UnitWeapons',
            'ItemData',
            'AbilityData',
            'AbilityBuffData',
            'UpgradeData',
            'DestructableData',
        )
    ]
    + [
        'Units\\%s%s%s.txt' % (r, t, s)
        for r in ('Campaign', 'Human', 'Orc', 'Undead', 'NightElf', 'Neutral')
        for t in ('Unit', 'Ability', 'Upgrade')
        for s in ('Func', 'Strings')
    ]
    + [
        'Units\\%s.txt' % n
        for n in (
            'ItemFunc',
            'ItemStrings',
            'ItemAbilityFunc',
            'ItemAbilityStrings',
            'CommonAbilityFunc',
            'CommonAbilityStrings',
            'CommandFunc',
            'CommandStrings',
        )
    ]
    + ['Units\\%sSkin.txt' % n for n in ('Unit', 'Item', 'Ability', 'Upgrade', 'Destructable')]
    + ['Doodads\\DoodadSkins.txt']
)

