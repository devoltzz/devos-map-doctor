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
NAME_MAX = 300


RX_DRIVE = re.compile(rb'^[A-Za-z]:[\\/]*')
FORBIDDEN = frozenset(b'"*?<>|')


def _sanitize(n):
    n = RX_DRIVE.sub(b'', n).lstrip(b'\\/')
    if not n or n.endswith((b'\\', b'/')) or n.lower().startswith(b'~unknowns') or FORBIDDEN.intersection(n) or \
            b'\xef\xbf\xbd' in n:
        return b''
    return n


WARCRAFT_EXTS = frozenset(e.encode() for e in (
    'mdx mdl blp tga dds jpg jpeg png gif bmp psd ico tif tiff webp '
    'wav mp3 flac ogg mid midi dls aif aiff avi ttf otf fnt woff '
    'j ai lua txt slk fdf toc pld wts wai ini html htm xml json csv js css md cfg log lst '
    'ts '
    'w3a w3b w3c w3d w3e w3f w3g w3h w3i w3l w3m w3n w3o w3q w3r w3s w3t w3u w3x w3z w3grp '
    'wct wtg wpm doo mmp shd imp mpq frag vert material mrf ifl flt m3d '
    'exe dll asi mix bin dat db jc key sign gid ccd ax b00 bak cmd clh exp jx lnk pkg was xlsx 3ds xxx iniconfig '
    'manifest zip rar 7z').split())
def add_levels(name_list, origin=BIG_INDEX, dest=None, log=None):
    import numpy as np
    from doctor.mpq import mpqlib as M
    z = np.load(origin)
    hash_key, h3, offs, blob = z['hash_key'], z['h3'], z['offs'], z['blob'].tobytes()
    new_ones, seen = [], set()
    for n in name_list:
        b = n if isinstance(n, (bytes, bytearray)) else n.encode('utf-8', 'surrogateescape')
        b = _sanitize(bytes(b).strip(b' \t\r\n'))
        if not b or len(b) > NAME_MAX or any(c < 0x20 for c in b):
            continue
        b = b.replace(b'/', b'\\').lstrip(b'\\')
        k = b.translate(M.MPQ_UPPERCASE)
        if k in seen:
            continue
        seen.add(k)
        new_ones.append(b)
    if not new_ones:
        return 0, len(hash_key)
    h1 = np.asarray(M.hashstr_batch(new_ones, 1), dtype=np.uint64)
    h2 = np.asarray(M.hashstr_batch(new_ones, 2), dtype=np.uint64)
    key_new = (h1 << np.uint64(32)) | h2
    pos = np.searchsorted(hash_key, key_new)
    pos[pos >= len(hash_key)] = 0
    missing = hash_key[pos] != key_new if len(hash_key) else np.ones(len(key_new), dtype=bool)
    new_ones = [n for n, f in zip(new_ones, missing) if f]
    key_new = key_new[missing]
    if not new_ones:
        return 0, len(hash_key)
    h3_new = np.asarray(
        M.hashstr_batch([n.replace(b'/', b'\\').rsplit(b'\\', 1)[-1] for n in new_ones], 3), dtype=np.uint32
    )
    all_items = [blob[offs[i]:offs[i + 1]] for i in range(len(hash_key))] + new_ones
    key2 = np.concatenate([hash_key, key_new])
    h3_all = np.concatenate([h3.astype(np.uint32), h3_new])
    order = np.argsort(key2, kind='stable')
    key2, h3_all = key2[order], h3_all[order]
    unique = np.ones(len(key2), dtype=bool)
    unique[1:] = key2[1:] != key2[:-1]
    order, key2, h3_all = order[unique], key2[unique], h3_all[unique]
    sz = np.fromiter((len(all_items[i]) for i in order), dtype=np.int64, count=len(order))
    offs_all = np.zeros(len(order) + 1, dtype=np.int64)
    np.cumsum(sz, out=offs_all[1:])
    blob_all = np.frombuffer(b''.join(all_items[i] for i in order), dtype=np.uint8)
    np.savez_compressed(dest or origin, hash_key=key2, h3=h3_all, offs=offs_all, blob=blob_all)
    if log:
        log('index: +%d names (%d in all) -> %s' % (len(new_ones), len(key2), dest or origin))
    return len(new_ones), len(key2)


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
    ('.wav', '.mp3', '.ogg', '.flac', '.aif', '.aiff'),
    ('.mdl', '.mdx'),
    ('.blp', '.tga', '.jpg', '.dds', '.gif', '.png'),
    ('.ttf', '.otf', '.woff'),
]
PROTECTOR_PREFIXES = ('DIS', 'PAS', 'DISDIS', 'DISPAS')
_EXT_EQUIV_OF = {}
for _g in EXT_EQUIV:
    for _e in _g:
        _EXT_EQUIV_OF.setdefault(_e, tuple(x for _g2 in EXT_EQUIV if _e in _g2 for x in _g2 if x != _e))


_VARIANTS_MEMO = {}
_VARIANTS_MEMO_CAP = 200000


def variants(fname, cap=48, rounds=3):
    hash_key = (fname, cap, rounds)
    seq = _VARIANTS_MEMO.get(hash_key)
    if seq is None:
        if len(_VARIANTS_MEMO) >= _VARIANTS_MEMO_CAP:
            _VARIANTS_MEMO.clear()
        seq = _VARIANTS_MEMO[hash_key] = _variants_seq(fname, cap, rounds)
    return set(seq)


def _variants_seq(fname, cap=48, rounds=3):
    fname = fname.strip()
    if not fname:
        return ()
    fast_path = ':' not in fname and '/' not in fname and fname[:2] != '\\\\'
    join_lines = None if fast_path else os.path.join
    split, splitext = os.path.split, os.path.splitext
    equivalents = _EXT_EQUIV_OF
    current = {fname}
    direct = set()
    for r in range(rounds):
        new = set(current)
        add = new.add
        for n in sorted(current):
            if r and len(new) >= cap:
                break
            root, ext = splitext(n)
            e = ext.lower()
            for height in equivalents.get(e, ()):
                add(root + height)
            folder, base = split(root)
            if join_lines is None:
                pre = folder if not folder or folder[-1] == '\\' else folder + '\\'
            base_upper = base.upper()
            for p in PROTECTOR_PREFIXES:
                if base_upper.startswith(p):
                    x = base[len(p):].lstrip('_- ')
                    add((pre + x if join_lines is None else join_lines(folder, x)) + ext)
                elif join_lines is None:
                    add(pre + p + base + ext)
                    add(pre + p + '_' + base + ext)
                else:
                    add(join_lines(folder, p + base) + ext)
                    add(join_lines(folder, p + '_' + base) + ext)
            if not root.upper().endswith('_PORTRAIT'):
                add(root + '_PORTRAIT' + ext)
        if r == 0:
            direct = set(new)
        if new == current or len(new) >= cap:
            current = new
            break
        current = new
    if len(direct) >= cap:
        output = [n for n in sorted(direct)[:cap] if n]
    else:
        rest = sorted(current - direct)
        output = [n for n in list(direct) + rest[:cap - len(direct)] if n]
    root, ext = os.path.splitext(fname)
    if ext.lower() == '.mdl' and not root.upper().endswith('_PORTRAIT'):
        output.append(root + '_PORTRAIT.mdx')
    return tuple(output)


_EXTENSIONS_B = (
    rb'(?:mdx|mdl|blp|tga|jpg|dds|gif|png|wav|mp3|ogg|flac|aiff|aif|ttf|otf|woff|fdf|toc|slk|ini|txt|'
    rb'j|lua|w3a|w3t|w3u|w3d|w3b|w3h|w3q|w3i|w3e|w3r|w3c|w3s|wts|doo|shd|wpm|mmp|imp|pld)')
RE_PATH_B = re.compile(
    rb'[A-Za-z0-9_\-\\/\.\[\(!#$%&@^~{=][A-Za-z0-9_\-\\/\. \[\]\(\)\+!#$%&@^~{}=]{0,180}?\.' + _EXTENSIONS_B,
    re.I)
RE_EXTENSION_B = re.compile(rb'\.' + _EXTENSIONS_B, re.I)
RE_EXTENSION_NUL_B = re.compile(rb'\.' + _EXTENSIONS_B + rb'(?=\x00)', re.I)
PATH_REACH = 181
PATH_EXT_MAX = 4
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


EXT_MODEL_TEXTURE = ('.mdx', '.mdl', '.blp', '.tga', '.dds', '.jpg')


def slk_dir_file(data_bytes):
    out = set()
    if not data_bytes.startswith(b'ID;'):
        return out
    try:
        from doctor.data import slk
        slk_columns, rows = slk.parse_slk_bytes(data_bytes)
    except Exception:
        return out
    cols = {str(c).lower(): c for c in slk_columns}
    cd, cf = cols.get('dir'), cols.get('file')
    if cd is None or cf is None:
        return out
    for row in rows.values():
        d = (row.get(cd) or '').strip().strip('"').replace('/', '\\').strip('\\')
        f = (row.get(cf) or '').strip().strip('"').replace('/', '\\').strip('\\')
        if not d or not f or d == '-' or f == '-' or f == '_':
            continue
        file_path = d + '\\' + f
        out.add(file_path)
        root = os.path.splitext(file_path)[0] if os.path.splitext(f)[1].lower() in EXT_MODEL_TEXTURE else file_path
        out.update(root + e for e in EXT_MODEL_TEXTURE)
        out.update(file_path + e for e in EXT_MODEL_TEXTURE)
    return out


def mine_bytes(data_bytes):
    out = set()
    if data_bytes[:4] == b'MDLX':
        out |= mdx_textures(data_bytes)
    elif data_bytes[:3] == b'ID;':
        out |= slk_dir_file(data_bytes)
    if b'\x00' in data_bytes:
        out.update(v.decode('latin-1').replace('/', '\\') for v in nul_values(data_bytes))
    out = set(n for n in out if not re.search(r'\.\.[\\/]', n))
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


def _pairs_of_hash(a, ht, n_ht):
    cache = getattr(a, '_hash_pairs', None)
    if cache is None or cache[0] != n_ht or cache[1] is not ht:
        cache = (n_ht, ht, set(zip(ht[0:4 * n_ht:4], ht[1:4 * n_ht:4])))
        try:
            a._hash_pairs = cache
        except AttributeError:
            pass
    return cache[2]


def _with_hash_entry(a, name_list):
    ht = getattr(a, 'ht', None)
    n_ht = getattr(a, 'hash_n_read', None)
    if not name_list or ht is None or n_ht is None:
        return name_list
    from doctor.mpq import mpqlib as M
    pairs = _pairs_of_hash(a, ht, n_ht)
    enc = [n.encode('utf-8', 'surrogateescape') for n in name_list]
    h1, h2 = M.hashstr_batch(enc, 1), M.hashstr_batch(enc, 2)
    return [n for n, x, y in zip(name_list, h1, h2) if (int(x), int(y)) in pairs]


def referenced_closure(a, seeds=None, log=None, mines=None):
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
            if mines is not None and not mines(n):
                continue
            try:
                d = a.read(n, bi=seen[n])
            except Exception:
                continue
            if d:
                candidates |= mine_bytes(d[:16 * 1048576])
                if n.lower().endswith('war3map.lua') and d[:5] == b'--W3P':
                    try:
                        from doctor.mpq import w3protect
                        candidates |= set(w3protect.paths(d))
                    except Exception:
                        pass
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


SIGNATURES = {'.blp': (b'BLP1', b'BLP2', b'BLX1'), '.mdx': (b'MDLX',), '.w3x': (b'HM3W',), '.w3m': (b'HM3W',),
              '.w3n': (b'HM3W', b'MPQ\x1a'),
              '.wav': (b'RIFF',), '.mp3': (b'ID3', b'\xff\xfb', b'\xff\xf3', b'\xff\xf2'), '.jpg': (b'\xff\xd8\xff',),
              '.dds': (b'DDS ',), '.exe': (b'MZ',), '.dll': (b'MZ',), '.asi': (b'MZ',), '.mix': (b'MZ',),
              '.m3d': (b'MZ',), '.flt': (b'MZ',), '.ogg': (b'OggS',), '.png': (b'\x89PNG',),
              '.flac': (b'fLaC', b'ID3'), '.aif': (b'FORM',), '.aiff': (b'FORM',), '.woff': (b'wOFF',),
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


RX_LITERAL = re.compile(rb'"((?:[^"\\\n]|\\.){1,160})"')
RX_PREFIX_MATCH = re.compile(r'^[A-Za-z0-9_\-.()\[\]]+(?:[\\/][A-Za-z0-9_\-. ()\[\]]*)+$')
RX_HAS_EXT = re.compile(r'\.[A-Za-z0-9]{2,4}$')
NUMBERED_CAP = 1000


def path_prefixes(data_bytes):
    from doctor.mpq import w3protect
    lits = [w3protect.lua_literal(m.group(1)) for m in RX_LITERAL.finditer(data_bytes)]
    if w3protect.is_w3p(data_bytes):
        lits.extend(w3protect.texts(data_bytes))
    out = set()
    for b in lits:
        if len(b) > 120:
            continue
        s = b.decode('latin-1')
        if RX_PREFIX_MATCH.match(s) and not RX_HAS_EXT.search(s) and any(c.isalpha() for c in s):
            out.add(s.replace('/', '\\'))
    return out


def numbered(prefixes, extensions):
    nums = [str(i) for i in range(NUMBERED_CAP)] + ['%02d' % i for i in range(10)] + ['%03d' % i for i in range(100)]
    return [p + n + e for p in sorted(prefixes) for n in nums for e in extensions]


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


CROSS_FOLDERS = ('', 'scripts', 'Fonts', 'war3mapImported', 'ReplaceableTextures\\CommandButtons',
                 'ReplaceableTextures\\CommandButtonsDisabled', 'ReplaceableTextures\\PassiveButtons')
CROSS_CAP = 2000000
CROSS_BATCH = 250000


def crossed_folders(name_list):
    visited = {}
    use_of = {}
    for n in CROSS_FOLDERS:
        visited.setdefault(n.upper(), n)
    for n in name_list:
        pieces = n.replace('/', '\\').strip('\\').split('\\')[:-1]
        for i in range(1, len(pieces) + 1):
            folder = '\\'.join(pieces[:i])
            k = folder.upper()
            if not folder:
                continue
            visited.setdefault(k, folder)
            use_of[k] = use_of.get(k, 0) + 1
    fixed_set = [visited[n.upper()] for n in CROSS_FOLDERS]
    rest = sorted((k for k in visited if k not in {f.upper() for f in fixed_set}), key=lambda k: (-use_of.get(k, 0), k))
    return fixed_set + [visited[k] for k in rest]


def crossed_bases(name_list):
    visited = {}
    for n in name_list:
        b = n.replace('/', '\\').rsplit('\\', 1)[-1].strip()
        if b and RX_HAS_EXT.search(b):
            visited.setdefault(b.upper(), b)
    return [visited[k] for k in sorted(visited)]


def cross_scan(a, bases, folders, cap=CROSS_CAP, existing=None, log=None):
    ht = getattr(a, 'ht', None)
    n_ht = getattr(a, 'hash_n_read', None)
    if not bases or not folders or ht is None or n_ht is None:
        return []
    from doctor.mpq import mpqlib as M
    pairs = _pairs_of_hash(a, ht, n_ht)
    existing = existing or ()
    matches = []
    batch = []
    done = 0

    def flush():
        enc = [n.encode('utf-8', 'surrogateescape') for n in batch]
        h1, h2 = M.hashstr_batch(enc, 1), M.hashstr_batch(enc, 2)
        matches.extend(n for n, x, y in zip(batch, h1, h2) if (int(x), int(y)) in pairs)
        del batch[:]

    for folder in folders:
        prefix = folder + '\\' if folder else ''
        for b in bases:
            if done >= cap:
                break
            n = prefix + b
            if n.upper() in existing:
                continue
            batch.append(n)
            done += 1
            if len(batch) >= CROSS_BATCH:
                flush()
        if done >= cap:
            break
    if batch:
        flush()
    if log and done >= cap:
        log('cross scan: cut at %d pairs (%d folders x %d names)' % (cap, len(folders), len(bases)))
    return matches


SPACE_SUFFIXES = (' ', '  ')


def with_trailing_space(a, name_list, suffixes=SPACE_SUFFIXES):
    cand = [n.rstrip(' ') + suf for n in name_list if RX_HAS_EXT.search(n.rstrip(' ')) for suf in suffixes]
    return _with_hash_entry(a, cand)


def derived_names(a, name_list, log=None, crossed=True):
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
    ok_bases, ok_folders = [], []
    seen_bases, seen_folders = set(), set()

    def cross_pair(cited, log=log):
        if not crossed:
            return []
        new_b = [b for b in crossed_bases(cited) if b.upper() not in seen_bases]
        all_p = crossed_folders(list(known) + list(matches))
        new_p = [p for p in all_p if p.upper() not in seen_folders]
        if not new_b and not new_p:
            return []
        seen_bases.update(b.upper() for b in new_b)
        seen_folders.update(p.upper() for p in new_p)
        achou = cross_scan(a, ok_bases + new_b, new_p, existing=keys, log=log)
        achou += cross_scan(a, new_b, ok_folders, existing=keys, log=log)
        achou += with_trailing_space(a, [c for c in cited if c.upper() not in keys])
        ok_bases.extend(new_b)
        ok_folders.extend(new_p)
        return achou

    def try_names(candidates):
        new_c = set(candidates)
        new_c.difference_update(tested)
        cand = sorted(c for c in new_c if c and c.upper() not in keys)[:DERIVED_LIMIT]
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
        if ext.lower() in ('.fdf', '.toc'):
            cand.append(n[:-4] + ('.toc' if ext.lower() == '.fdf' else '.fdf'))
    prefixes = set()
    for n in known:
        if n.lower().rsplit('\\', 1)[-1] in ('war3map.lua', 'war3map.j'):
            try:
                prefixes |= path_prefixes(a.read(n, bi=known[n]) or b'')
            except Exception:
                pass
    cand.extend(numbered(prefixes, MODEL_EXT + IMAGE_EXT))
    cand.extend(from_texts)
    cited = set(from_texts)
    for _inner, textures in models.values():
        cited.update(textures)
    new_ones = try_names(cand)
    new_ones = new_ones + try_names(cross_pair(cited))
    model_folders = set(IMPORTED_FOLDERS) | set(folder(n) for n in known if n.lower().endswith(MODEL_EXT))
    round_num = 0
    new_cited = set()
    while True:
        round_num += 1
        cand = []
        for bi, (inner, textures) in sorted(models.items()):
            if bi not in nameless:
                continue
            folders = model_folders | set(folder(t) for t in textures)
            by_textures = {os.path.splitext(t.rsplit('\\', 1)[-1])[0] for t in textures}
            for base in sorted(({inner, inner.replace(' ', ''), inner.replace(' ', '_')} | by_textures) - {''}):
                for p in sorted(folders):
                    cand.append(p + base + '.mdx')
                    if not base.upper().endswith('_PORTRAIT'):
                        cand.append(p + base + '_Portrait.mdx')
        visited = set()
        for _inner, textures in models.values():
            for t in textures:
                if t in visited:
                    continue
                visited.add(t)
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
                new_cited.add(c)
        new_ones = try_names(cand)
        new_ones = new_ones + try_names(cross_pair(new_cited))
        new_cited = set()
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

