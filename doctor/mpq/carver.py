# Rebuilds an MPQ archive from its file data when the file tables are unreadable.
import collections
import os
import re
import struct

from doctor.mpq import mpqlib as M
from doctor.mpq import mpqread


TABLE_MAX = 0x4000
MAX_MEMBERS = 20000
READ_LIMIT = 64 << 20


class Member(object):
    __slots__ = ('pos', 'sz', 'offs', 'hash_key', 'data_bytes', 'err', 'fname', 'how', 'kind')

    def __init__(self, pos, sz, offs=None, hash_key=None):
        self.pos, self.sz, self.offs, self.hash_key = pos, sz, offs, hash_key
        self.data_bytes = self.err = self.fname = self.how = self.kind = None

    @property
    def encrypted(self):
        return self.hash_key is not None

    @property
    def is_compressed(self):
        return self.offs is not None


def _u32(d, i):
    return struct.unpack_from('<I', d, i)[0]


def _valid_offs(offs, sector_bytes, begin, end_pos):
    if offs[-1] <= offs[0] or begin + offs[-1] > end_pos:
        return False
    for a, b in zip(offs, offs[1:]):
        if b < a or b - a > sector_bytes:
            return False
    return True


def plain_member(d, base, pos, sector_bytes, end_pos):
    begin = base + pos
    if begin + 8 > end_pos:
        return None
    first = _u32(d, begin)
    if first < 8 or first % 4 or first > TABLE_MAX or begin + first > end_pos:
        return None
    offs = struct.unpack_from('<%dI' % (first // 4), d, begin)
    if not _valid_offs(offs, sector_bytes, begin, end_pos):
        return None
    return Member(pos, offs[-1], offs, None)


_NP = None


def _np():
    global _NP
    if _NP is None:
        import numpy as np
        _NP = (np, np.array(M.CRYPT[0x400:0x500], dtype=np.uint32))
    return _NP


def encrypted_member(d, base, pos, sector_bytes, end_pos):
    begin = base + pos
    if begin + 8 > end_pos:
        return None
    np, cr = _np()
    e0, e1 = struct.unpack_from('<II', d, begin)
    lim = min(TABLE_MAX, end_pos - begin)
    if lim < 8:
        return None
    F = np.arange(8, lim + 1, 4, dtype=np.uint64)
    k12 = ((np.uint64(e0) ^ F) - np.uint64(0xEEEEEEEE)) & np.uint64(0xFFFFFFFF)
    K = (k12[:, None] - cr.astype(np.uint64)[None, :]) & np.uint64(0xFFFFFFFF)
    ok = (K & np.uint64(0xFF)) == np.arange(256, dtype=np.uint64)[None, :]
    fi, ii = np.nonzero(ok)
    if not len(fi):
        return None
    K = K[fi, ii].astype(np.uint64)
    Fv = F[fi]
    seed0 = (np.uint64(0xEEEEEEEE) + cr.astype(np.uint64)[ii]) & np.uint64(0xFFFFFFFF)
    K2 = ((((~K & np.uint64(0xFFFFFFFF)) << np.uint64(0x15)) & np.uint64(0xFFFFFFFF)) + np.uint64(0x11111111)) \
        & np.uint64(0xFFFFFFFF) | (K >> np.uint64(0x0B))
    seed1 = (Fv + seed0 + ((seed0 << np.uint64(5)) & np.uint64(0xFFFFFFFF)) + np.uint64(3)) & np.uint64(0xFFFFFFFF)
    seed1 = (seed1 + cr.astype(np.uint64)[(K2 & np.uint64(0xFF)).astype(np.int64)]) & np.uint64(0xFFFFFFFF)
    pt1 = np.uint64(e1) ^ ((K2 + seed1) & np.uint64(0xFFFFFFFF))
    good_mask = (pt1 > Fv) & (pt1 <= Fv + np.uint64(sector_bytes))
    cands = []
    for k, f in zip(K[good_mask], Fv[good_mask]):
        k, f = int(k), int(f)
        tb = M.decrypt_bytes(d[begin:begin + f], k)
        offs = struct.unpack_from('<%dI' % (f // 4), tb, 0)
        if offs[0] == f and _valid_offs(offs, sector_bytes, begin, end_pos):
            m = Member(pos, offs[-1], offs, (k + 1) & 0xFFFFFFFF)
            if _first_sector_ok(d, base, m, sector_bytes, strict=True):
                return m
            cands.append(m)
    return cands[0] if cands else None


def member_at(d, base, pos, sector_bytes, end_pos):
    return plain_member(d, base, pos, sector_bytes, end_pos) or encrypted_member(d, base, pos, sector_bytes, end_pos)


def read_member(d, base, m, sector_bytes):
    begin = base + m.pos
    if not m.is_compressed:
        raw_bytes = d[begin:begin + m.sz]
        if m.hash_key is None:
            return bytes(raw_bytes)
        return b''.join(M.decrypt_bytes(raw_bytes[i:i + sector_bytes], (m.hash_key + k) & 0xFFFFFFFF)
                        for k, i in enumerate(range(0, len(raw_bytes), sector_bytes)))
    out = bytearray()
    ns = len(m.offs) - 1
    for i in range(ns):
        c = d[begin + m.offs[i]:begin + m.offs[i + 1]]
        if m.hash_key is not None:
            c = M.decrypt_bytes(c, (m.hash_key + i) & 0xFFFFFFFF)
        if len(c) >= sector_bytes:
            out += c[:sector_bytes]
            continue
        if not c:
            continue
        if i == ns - 1 and c[0] == 0 and not _implode(c):
            out += c
            continue
        try:
            x = mpqread.decompress_sector(c, sector_bytes)
        except Exception:
            if i < ns - 1:
                raise
            x = _last_sector(c)
        if i == ns - 1 and len(x) <= len(c):
            x = c
        out += x
        if len(out) > READ_LIMIT:
            raise ValueError('member larger than %d MB' % (READ_LIMIT >> 20))
    return bytes(out)


def _implode(c):
    from doctor.mpq import pkware
    return pkware.is_implode(c)


def _last_sector(c):
    from doctor.mpq import pkware
    if pkware.is_implode(c):
        try:
            return pkware.decompress(c, expected=None)
        except Exception:
            pass
    return c


RX_TEXT = re.compile(rb'[\t\r\n\x20-\x7e\x80-\xff]*')


def _text_end(d, begin, end_pos):
    m = RX_TEXT.match(d, begin, min(end_pos, begin + (4 << 20)))
    until = m.end() if m else begin
    cands = [until] + [begin + 1 + k for k in range(until - begin - 1, -1, -1) if d[begin + k] == 0x0A]
    return list(dict.fromkeys(c for c in cands if c > begin))


def _editor_file_end(d, begin, end_pos):
    out = []
    try:
        from doctor.fix import inflated_counts
    except Exception:
        return out
    chunk_size = d[begin:min(end_pos, begin + (1 << 20))]
    try:
        v, n = struct.unpack_from('<II', chunk_size, 0)
        if n and n < 4096:
            for new_ones in (False, True):
                for dof in (False, True):
                    if dof and v < 3:
                        continue
                    r = inflated_counts.Reader(chunk_size, 8)
                    try:
                        for _ in range(n):
                            inflated_counts.read_camera(r, v, new_ones, dof)
                        out.append(begin + r.o)
                    except Exception:
                        pass
    except Exception:
        pass
    for fname in ('war3map.w3r', 'war3map.w3s', 'war3map.imp', 'war3map.mmp', 'war3map.w3c'):
        try:
            x = inflated_counts._READERS[fname](chunk_size)
        except Exception:
            continue
        if x.get('declared') and len(x['regs']) == x['declared'] and x.get('end_pos'):
            out.append(begin + x['end_pos'])
    return list(dict.fromkeys(out))


def next_member(d, base, pos, sector_bytes, end_pos, window=1 << 20, depth=0):
    begin = base + pos
    ends = _editor_file_end(d, begin, end_pos) + _text_end(d, begin, end_pos)[:64]
    for q in ends:
        m = member_at(d, base, q - base, sector_bytes, end_pos)
        if m and _first_sector_ok(d, base, m, sector_bytes):
            return [q - base]
    if depth < 4:
        for q in ends[:8]:
            if q >= end_pos - 8:
                continue
            r = next_member(d, base, q - base, sector_bytes, end_pos, window, depth + 1)
            if r:
                return [q - base] + r
    if depth:
        return None
    np, _cr = _np()
    end_j = min(end_pos, begin + window)
    if end_j - begin < 16:
        return None
    a = np.frombuffer(d, dtype=np.uint8, count=end_j - begin, offset=begin).astype(np.uint32)
    v = a[:-7] | (a[1:-6] << 8) | (a[2:-5] << 16) | (a[3:-4] << 24)
    w = a[4:-3] | (a[5:-2] << 8) | (a[6:-1] << 16) | (a[7:] << 24)
    cand = np.nonzero((v >= 8) & (v <= TABLE_MAX) & ((v & 3) == 0) & (w > v) & (w - v <= sector_bytes))[0]
    for k in cand[:4096]:
        q = begin + int(k)
        if q <= begin:
            continue
        m = plain_member(d, base, q - base, sector_bytes, end_pos)
        if m and _first_sector_ok(d, base, m, sector_bytes):
            return [q - base]
    return None


def _first_sector_ok(d, base, m, sector_bytes, strict=False):
    begin = base + m.pos
    c = d[begin + m.offs[0]:begin + m.offs[1]]
    if m.hash_key is not None:
        c = M.decrypt_bytes(c, m.hash_key)
    if len(c) >= sector_bytes:
        return not strict
    try:
        return bool(mpqread.decompress_sector(c, sector_bytes))
    except Exception:
        return not strict and len(m.offs) == 2


def walk(d, h, data_end=None, first_pos=0x20):
    base = h.offset
    sector_bytes = M.header_sector(h.block_shift)
    end_pos = data_end or len(d)
    pos, members, holes = first_pos, [], []
    while base + pos + 8 <= end_pos and len(members) < MAX_MEMBERS:
        m = member_at(d, base, pos, sector_bytes, end_pos)
        if m:
            members.append(m)
            pos += m.sz
            continue
        cuts = next_member(d, base, pos, sector_bytes, end_pos)
        if cuts is None:
            holes.append((pos, end_pos - base))
            break
        for q in cuts:
            members.append(Member(pos, q - pos))
            pos = q
    return members, holes


def _text(b, n=4096):
    return b[:n].decode('utf-8', 'replace')


TEXT_CONTROL_CHARS = frozenset((27, 30, 31))


def _is_text(b):
    header = b[:4096]
    return bool(header) and not any(c < 9 or 13 < c < 32 for c in header if c not in TEXT_CONTROL_CHARS)


RX_FIELD = re.compile(rb'([a-z][a-zA-Z0-9]{3})[\x00-\xff]\x00\x00\x00')


def _field_prefixes(b):
    return collections.Counter(chr(m.group(1)[0]) for m in RX_FIELD.finditer(b[:65536]))


RX_LEVEL_FIELD = re.compile(
    rb'([A-Za-z][A-Za-z0-9]{3})[\x00-\xff]\x00\x00\x00[\x00-\x0f]\x00\x00\x00[\x00-\x03]\x00\x00\x00'
)


def object_type(b):
    letters = _field_prefixes(b)
    for letter, _c in letters.most_common(3):
        if letter in OBJECT_BY_LETTER:
            return OBJECT_BY_LETTER[letter]
    level = collections.Counter(chr(m.group(1)[0]) for m in RX_LEVEL_FIELD.finditer(b[:65536]))
    tn = sum(level.values())
    if not tn:
        return None
    if level.get('d', 0) * 2 >= tn:
        return 'war3map.w3d'
    if level.get('g', 0) * 2 >= tn:
        return 'war3map.w3q'
    return 'war3map.w3a'


EDITOR_EMPTY_FILES = {b'\0\0\0\0': ('war3map.w3c', 'war3map.wct', 'war3map.mmp'),
                      b'\x05\0\0\0': ('war3map.w3r',),
                      b'\x01\0\0\0': ('war3map.imp', 'war3map.w3s', 'war3map.wct'),
                      b'\x02\0\0\0': ('war3map.w3s',), b'\x03\0\0\0': ('war3map.w3s',)}


OBJECT_BY_LETTER = {'u': 'war3map.w3u', 'i': 'war3map.w3t', 'b': 'war3map.w3b', 'd': 'war3map.w3d',
                    'f': 'war3map.w3h', 'g': 'war3map.w3q', 'a': 'war3map.w3a'}


def identify(b, w3e_dims=None):
    if not b:
        return None, '.bin', 'empty'
    c4 = b[:4]
    if c4 == b'W3E!':
        return 'war3map.w3e', '.w3e', 'w3e'
    if c4 == b'MP3W':
        return 'war3map.wpm', '.wpm', 'wpm'
    if c4 == b'WTG!':
        return 'war3map.wtg', '.wtg', 'wtg'
    if c4 == b'W3do':
        try:
            from doctor.fix import inflated_counts
            x = inflated_counts.read_units_doo(b)
            if x.get('on_close'):
                return 'war3mapUnits.doo', '.doo', 'units_doo'
        except Exception:
            pass
        return 'war3map.doo', '.doo', 'doo'
    if c4 == b'MDLX':
        return None, '.mdx', 'mdx'
    if c4 in (b'BLP1', b'BLP2'):
        try:
            w, hh = struct.unpack_from('<II', b, 12 if c4 == b'BLP1' else 12)
        except struct.error:
            w = hh = 0
        return None, '.blp', 'blp_%dx%d' % (w, hh)
    if c4 == b'RIFF':
        return None, '.wav', 'wav'
    if c4[:3] == b'ID3' or c4[:2] in (b'\xff\xfb', b'\xff\xf3', b'\xff\xf2'):
        return None, '.mp3', 'mp3'
    if c4 == b'DDS ':
        return None, '.dds', 'dds'
    if c4[:2] == b'MZ':
        return None, '.dll', 'pe'
    if b.endswith(b'TRUEVISION-XFILE.\x00'):
        return None, '.tga', 'tga'
    if len(b) > 18 and b[1] == 0 and b[2] in (2, 10) and b[3:7] == b'\0' * 4 and b[16] in (24, 32):
        w, hh = struct.unpack_from('<HH', b, 12)
        if 0 < w <= 4096 and 0 < hh <= 4096:
            return None, '.tga', 'tga'
    if len(b) >= 8:
        v = struct.unpack_from('<i', b, 0)[0]
        if v in (18, 25, 28, 31, 32, 33) and len(b) < 400000:
            try:
                from doctor.data import w3i
                m = w3i.parse_or_tolerant(b)
                if m.get('players') is not None:
                    return 'war3map.w3i', '.w3i', 'w3i'
            except Exception:
                pass
    t = b.lstrip(b'\xef\xbb\xbf')
    if _is_text(t):
        s = _text(t, 1 << 20).replace('\r\n', '\n').replace('\r', '\n')
        if re.search(r'(?m)^\s*function\s+main\s+takes\s+nothing\s+returns\s+nothing', s) or \
                (re.search(r'(?m)^\s*endglobals\b', s) and re.search(r'(?m)^\s*function\s+\w+\s+takes', s)):
            return 'war3map.j', '.j', 'jass'
        if re.search(r'(?m)^\s*function\s+main\s*\(\s*\)', s) and re.search(r'(?m)^\s*end\b', s):
            return 'war3map.lua', '.lua', 'lua'
        if s.startswith('STRING ') or '\nSTRING ' in s[:200]:
            return 'war3map.wts', '.wts', 'wts'
        if s.startswith('[Misc]'):
            return 'war3mapMisc.txt', '.txt', 'misc'
        if s.startswith('[MapExtraInfo]'):
            return 'war3mapExtra.txt', '.txt', 'extra'
        if s.startswith('[CustomSkin]') or s.startswith('[FrameDef]'):
            return 'war3mapSkin.txt', '.txt', 'skin'
        line_list = [line.strip() for line in s.splitlines() if line.strip() and line.strip() not in MPQ_NAMES]
        if (
            line_list
            and sum(1 for line in line_list if re.search(r'\.[A-Za-z0-9]{1,4}$', line)) >= 0.9 * len(line_list)
            and any(line.lower().startswith('war3map') for line in line_list)
        ):
            return '(listfile)', '.txt', 'listfile'
        return None, '.txt', 'body_text'
    if len(b) >= 8 and set(b[:4096]) <= {0, 0xFF} and w3e_dims and len(b) == w3e_dims[0] * w3e_dims[1] * 16:
        return 'war3map.shd', '.shd', 'shd'
    if len(b) == 8 and b[4:] == b'\0\0\0\0' and b[:4] in EDITOR_EMPTY_FILES:
        fname = EDITOR_EMPTY_FILES[b[:4]][0]
        return fname, os.path.splitext(fname)[1], 'empty_editor'
    if len(b) >= 8:
        v, n = struct.unpack_from('<ii', b, 0)
        if v == 0 and n >= 0 and len(b) == 8 + 16 * n:
            return 'war3map.mmp', '.mmp', 'mmp'
        if v == 100 and 0 <= n <= 15:
            return '(attributes)', '.bin', 'attributes'
        try:
            from doctor.fix import inflated_counts
            for fname in ('war3map.w3r', 'war3map.w3c', 'war3map.w3s', 'war3map.imp'):
                try:
                    x = inflated_counts._READERS[fname](b)
                except Exception:
                    continue
                if x.get('declared') and len(x['regs']) == x['declared'] and not x.get('remaining'):
                    return fname, os.path.splitext(fname)[1], fname.split('.')[-1]
            if v in (0, 1) or v in (-0x7FFFFFFF, -0x7FFFFFFC):
                try:
                    x = inflated_counts.read_wct(b)
                    if not x.get('remaining') and len(x['regs']) == x['declared'] and (x['declared'] or len(b) > 8):
                        return 'war3map.wct', '.wct', 'wct'
                except Exception:
                    pass
        except Exception:
            pass
        if v in (1, 2, 3) and 0 <= n < 100000:
            fname = object_type(b[8:])
            if fname:
                return fname, os.path.splitext(fname)[1], 'object_data'
    if len(b) > 1000 and set(b[:4096]) <= {0, 0xFF}:
        return 'war3map.shd', '.shd', 'shd'
    return None, '.bin', 'bin'


def _plain_name(fname):
    return fname.replace('/', '\\').rsplit('\\', 1)[-1]


def candidate_keys(m, fs):
    k = m.hash_key
    return {k, (((k ^ fs) & 0xFFFFFFFF) - m.pos) & 0xFFFFFFFF}


def _mined(members):
    from doctor.mpq import mpqnames
    out = set()
    for m in members:
        if m.data_bytes and m.kind in (
            'jass',
            'lua',
            'object_data',
            'mdx',
            'imp',
            'w3i',
            'wts',
            'body_text',
            'misc',
            'skin',
            'doo',
        ):
            try:
                out |= mpqnames.mine_bytes(m.data_bytes[:16 << 20])
            except Exception:
                pass
    return out


def assign_names(members, index_=None, log=None):
    in_use = set()
    for m in members:
        if m.data_bytes is None:
            continue
        fname, _ext, kind = identify(m.data_bytes)
        m.kind = kind
        if fname and fname.upper() not in in_use:
            m.fname, m.how = fname, 'content'
            in_use.add(fname.upper())
    known = set()
    for m in members:
        if m.fname == '(listfile)' and m.data_bytes:
            known |= set(
                line.strip() for line in m.data_bytes.decode('utf-8', 'surrogateescape').splitlines() if line.strip()
            )
    old_list = set(n.upper() for n in known)
    known |= _mined(members)
    by_h3 = collections.defaultdict(set)
    if known:
        listing = sorted(known)
        plain_names = [_plain_name(n).encode('utf-8', 'surrogateescape') for n in listing]
        for n, h in zip(listing, M.hashstr_batch(plain_names, 3)):
            by_h3[int(h)].add(n)
    for m in members:
        if m.fname or m.data_bytes is None or not m.encrypted:
            continue
        fs = len(m.data_bytes)
        matches = set()
        for k in candidate_keys(m, fs):
            matches |= by_h3.get(k, set())
            if index_ is not None:
                matches |= set(index_.fname(i) for i in index_.by_key3(k))
        _name, ext, _t = identify(m.data_bytes)
        good = [n for n in matches if n.upper() not in in_use and not RX_BAD_NAME.search(n) and
                (ext == '.bin' or os.path.splitext(n)[1].lower() in _EXTS_BY_KIND.get(ext, (ext,)))]
        if good:
            cited = set(x.upper() for x in known)
            good.sort(key=lambda n: (n.upper() not in DEFAULT_UPPER, n.upper() not in cited, n.count('\\'),
                                     n.lower()))
            chosen = good[0]
            m.fname, m.how = chosen, 'hash_key'
            in_use.add(chosen.upper())
    free_slots = collections.defaultdict(list)
    for n in sorted(known):
        if n.upper() not in in_use:
            free_slots[os.path.splitext(n)[1].lower()].append(n)
    nameless = collections.defaultdict(list)
    for m in members:
        if m.fname or m.data_bytes is None:
            continue
        _name, ext, _t = identify(m.data_bytes)
        nameless[ext].append(m)
    for ext, ms in nameless.items():
        cands = [n for e in _EXTS_BY_KIND.get(ext, (ext,)) for n in free_slots.get(e, [])]
        if ext == '.mdx':
            for m in ms:
                modl = _mdx_name(m.data_bytes)
                if modl:
                    tgt = [n for n in cands if os.path.splitext(_plain_name(n))[0].lower() == modl.lower()
                           and n.upper() not in in_use]
                    if len(tgt) == 1:
                        m.fname, m.how = tgt[0], 'listing'
                        in_use.add(tgt[0].upper())
            ms = [m for m in ms if not m.fname]
            cands = [n for n in cands if n.upper() not in in_use]
        same_ones = [n for n in free_slots.get(ext, []) if n.upper() not in in_use]
        from_list = sorted(set(n for n in same_ones if n.upper() in old_list), key=lambda n: n.upper())
        if len(ms) == 1 and len(set(n.upper() for n in from_list)) == 1:
            ms[0].fname, ms[0].how = from_list[0], 'listing'
            in_use.add(from_list[0].upper())
        elif len(ms) == 1 and len(same_ones) == 1:
            ms[0].fname, ms[0].how = same_ones[0], 'listing'
            in_use.add(same_ones[0].upper())
        elif len(ms) == 1 and len(cands) == 1:
            ms[0].fname, ms[0].how = cands[0], 'listing'
            in_use.add(cands[0].upper())
    imp = next((x for x in members if x.fname == 'war3map.imp' and x.data_bytes), None)
    if imp is not None:
        imp_names = [n for n in _imp_names(imp.data_bytes) if n.upper() not in in_use]
        leftover = [x for x in members if x.data_bytes is not None and not x.fname and not x.encrypted]
        if imp_names and len(imp_names) == len(leftover):
            ok = all(os.path.splitext(n)[1].lower() in
                     _EXTS_BY_KIND.get(identify(x.data_bytes)[1], (identify(x.data_bytes)[1],))
                     for n, x in zip(imp_names, leftover))
            if ok:
                for n, x in zip(imp_names, leftover):
                    x.fname, x.how = n, 'imp_order'
                    in_use.add(n.upper())
    k = 0
    for m in members:
        if m.data_bytes is None or m.fname:
            continue
        _name, ext, _t = identify(m.data_bytes)
        m.fname, m.how = 'war3mapImported\\carved\\%04d%s' % (k, ext), 'unnamed'
        k += 1
    return members


RX_BAD_NAME = re.compile(r'[<>|"?*\x00-\x1f]|^\s|\s$')
DEFAULT_UPPER = frozenset(n.upper() for n in (
    'war3map.j', 'war3map.lua', 'war3map.w3i', 'war3map.wts', 'war3map.wtg', 'war3map.wct', 'war3map.w3e',
    'war3map.w3a', 'war3map.w3b', 'war3map.w3d', 'war3map.w3h', 'war3map.w3q', 'war3map.w3t', 'war3map.w3u',
    'war3map.w3c', 'war3map.w3s', 'war3map.w3r', 'war3map.wpm', 'war3map.doo', 'war3map.shd', 'war3map.mmp',
    'war3map.imp', 'war3mapMisc.txt', 'war3mapSkin.txt', 'war3mapExtra.txt', 'war3mapUnits.doo', 'war3mapMap.blp',
    'war3mapMap.tga', 'war3mapPreview.tga', 'war3mapPath.tga', 'Scripts\\war3map.j', '(listfile)', '(attributes)'))

_EXTS_BY_KIND = {'.blp': ('.blp', '.tga', '.jpg', '.dds'), '.tga': ('.tga', '.blp'), '.mdx': ('.mdx', '.mdl'),
                 '.wav': ('.wav', '.mp3', '.ogg'), '.mp3': ('.mp3', '.wav'), '.txt': ('.txt', '.ini', '.slk', '.fdf',
                                                                                          '.toc', '.ai', '.pld'),
                 '.j': ('.j',), '.lua': ('.lua',), '.dll': ('.dll', '.exe', '.mix', '.asi')}


def _imp_names(b):
    out = []
    try:
        _v, n = struct.unpack_from('<ii', b, 0)
        p = 8
        for _ in range(n):
            kind = b[p]
            e = b.index(b'\0', p + 1)
            fname = b[p + 1:e].decode('utf-8', 'surrogateescape').replace('/', '\\')
            p = e + 1
            if kind in (5, 8) and '\\' not in fname:
                fname = 'war3mapImported\\' + fname
            out.append(fname)
    except Exception:
        pass
    return out


def _mdx_name(b):
    i = b.find(b'MODL')
    if i < 0 or i + 8 + 80 > len(b):
        return None
    n = b[i + 8:i + 8 + 80].split(b'\0')[0].decode('latin-1', 'replace').strip()
    return n or None


BLOCK_EXISTS, BLOCK_COMPRESS, BLOCK_ENCRYPTION, BLOCK_FIX = 0x80000000, 0x00000200, 0x00010000, 0x00020000
BLOCK_IMPLODE = 0x00000100


def is_imploded(d, base, m, sector_bytes, fs):
    from doctor.mpq import pkware
    begin = base + m.pos
    for i in range(len(m.offs) - 1):
        c = d[begin + m.offs[i]:begin + m.offs[i + 1]]
        if m.hash_key is not None:
            c = M.decrypt_bytes(c, (m.hash_key + i) & 0xFFFFFFFF)
        if 0 < len(c) < min(sector_bytes, fs - i * sector_bytes):
            return not pkware.has_mask(c) and pkware.is_implode(c)
    return False
OBJECTS_UPPER = frozenset(n.upper() for n in OBJECT_BY_LETTER.values())
MPQ_NAMES = ('(listfile)', '(attributes)', '(signature)')


def _kind_matches(fname, m):
    if m.encrypted:
        h3 = M.hashstr(_plain_name(fname), 3)
        return h3 in candidate_keys(m, len(m.data_bytes))
    default_value, ext, kind = identify(m.data_bytes)
    if default_value:
        if kind == 'empty_editor':
            return fname.lower() in EDITOR_EMPTY_FILES.get(m.data_bytes[:4], ())
        if kind == 'object_data':
            return fname.upper() in OBJECTS_UPPER
        return _plain_name(default_value).upper() == _plain_name(fname).upper() or (
            fname.lower().endswith('.txt') and ext == '.txt'
        )
    e = os.path.splitext(fname)[1].lower()
    return ext == '.bin' or e in _EXTS_BY_KIND.get(ext, (ext,)) or fname.lower() in MPQ_NAMES


def _intact(pos, n, loss_start):
    if pos + 16 * n <= loss_start:
        return n
    return max(0, (loss_start - pos) // 16) if loss_start > pos else 0


def repair_tables(d, loss_start, fname=None, index_='auto'):
    details = {'lost_blocks': 0, 'lost_slots': 0, 'rebuilt': 0, 'no_member': [], 'leftover_count': 0, 'how': {},
               'inserted': 0, 'unnamed': 0}
    h, _p = M.find_header(d, fname)
    if h is None:
        details['err'] = 'no MPQ header'
        return None, details
    base = h.offset
    sector_bytes = M.header_sector(h.block_shift)
    hn, bn = h.hash_n & 0x0FFFFFFF, h.block_n & 0x0FFFFFFF
    hp, bp = (base + h.hash_pos) & 0xFFFFFFFF, (base + h.block_pos) & 0xFFFFFFFF
    if not hn or not bn or hn & (hn - 1) or hp + 16 * hn > len(d) or bp + 16 * bn > len(d):
        details['err'] = 'table outside the file'
        return None, details
    hs_ok, good = _intact(hp, hn, loss_start), _intact(bp, bn, loss_start)
    details['lost_blocks'], details['lost_slots'] = bn - good, hn - hs_ok
    if good == bn and hs_ok == hn:
        return d, details
    if hs_ok == 0:
        details['err'] = 'the whole hash table was lost'
        return None, details
    ht = list(struct.unpack('<%dI' % (4 * hn), M.decrypt_bytes(d[hp:hp + 16 * hn], M.hashstr('(hash table)', 3))))
    bt = list(struct.unpack('<%dI' % (4 * bn), M.decrypt_bytes(d[bp:bp + 16 * bn], M.hashstr('(block table)', 3))))
    refs = collections.defaultdict(set)
    pointed_to = set()
    for s in range(hs_ok):
        a1, a2, _lp, bi = ht[4 * s:4 * s + 4]
        if bi < bn:
            pointed_to.add(bi)
            if bi >= good:
                refs[bi].add((a1, a2))
    t = [x for x in (hp, bp) if base + 0x20 < x <= len(d)]
    data_end = min(t) if t else len(d)
    members, occupied = [], []
    for i in range(good):
        pos, cs, _fs, fl = bt[4 * i:4 * i + 4]
        if not fl & BLOCK_EXISTS or not cs or base + pos + cs > data_end:
            continue
        occupied.append((pos, pos + cs))
        m = member_at(d, base, pos, sector_bytes, data_end) if fl & 0x0000FF00 else None
        if m is None and not fl & BLOCK_ENCRYPTION:
            m = Member(pos, cs)
        if m is not None:
            members.append(m)
    holes = []
    cursor = 0x20
    for begin, end_pos in sorted(occupied) + [(data_end - base, data_end - base)]:
        if begin - cursor >= 8:
            walked, new_holes = walk(d, h, base + begin, first_pos=cursor)
            members += walked
            holes += new_holes
        cursor = max(cursor, end_pos)
    members.sort(key=lambda m: m.pos)
    details['holes'] = holes
    for m in members:
        try:
            m.data_bytes = read_member(d, base, m, sector_bytes)
        except Exception as e:
            m.err = str(e)[:80]
    if index_ == 'auto':
        from doctor.mpq import mpqnames
        index_ = mpqnames.load_big()
    assign_names(members, index_)
    by_pos = dict((m.pos, m) for m in members)
    good_positions = set(bt[4 * i] for i in range(good) if bt[4 * i + 3] & BLOCK_EXISTS)
    free_slots = [m for m in members if m.pos not in good_positions and m.data_bytes is not None]
    cands = set(MPQ_NAMES) | set(DEFAULT_UPPER)
    listing = set()
    for m in members:
        if m.fname and m.how != 'unnamed':
            cands.add(m.fname)
        if m.fname == '(listfile)' and m.data_bytes:
            listing |= set(x.strip() for x in m.data_bytes.decode('utf-8', 'surrogateescape').splitlines() if x.strip())
    cands |= listing | _mined(members)
    cands = sorted(cands)
    enc = [n.encode('utf-8', 'surrogateescape') for n in cands]
    by_pair = {}
    for n, a1, a2 in zip(cands, M.hashstr_batch(enc, 1), M.hashstr_batch(enc, 2)):
        by_pair.setdefault((int(a1), int(a2)), n)
    if index_ is not None and refs:
        pairs = sorted(set(p for ps in refs.values() for p in ps) - set(by_pair))
        if pairs:
            matches = index_.lookup_batch([p[0] for p in pairs], [p[1] for p in pairs])
            for p, i in zip(pairs, matches):
                if i >= 0:
                    by_pair[p] = index_.fname(int(i))
    name_list = {}
    for bi, ps in refs.items():
        for p in sorted(ps):
            if p in by_pair:
                name_list[bi] = by_pair[p]
                break
    assigned = {}
    in_use = set()
    for bi, nm in sorted(name_list.items()):
        m = next((m for m in free_slots if id(m) not in in_use and m.fname and m.how != 'unnamed' and
                  (m.fname.upper() == nm.upper() or (m.how == 'content' and
                                                     _plain_name(m.fname).upper() == _plain_name(nm).upper()))), None)
        if m is None:
            h3 = M.hashstr(_plain_name(nm), 3)
            m = next((m for m in free_slots if id(m) not in in_use and m.encrypted and
                      h3 in candidate_keys(m, len(m.data_bytes))), None)
        if m is not None:
            assigned[bi] = m
            in_use.add(id(m))
            details['how'][bi] = 'fname'
    rest_bi = [bi for bi in range(good, bn) if bi not in assigned and (bi in refs or hs_ok < hn)]
    rest_m = [m for m in free_slots if id(m) not in in_use]
    k = 0
    for bi in rest_bi:
        while k < len(rest_m) and bi in name_list and not _kind_matches(name_list[bi], rest_m[k]):
            k += 1
        if k >= len(rest_m):
            break
        assigned[bi] = rest_m[k]
        in_use.add(id(rest_m[k]))
        details['how'][bi] = 'order'
        k += 1
    for bi in range(good, bn):
        m = assigned.get(bi)
        if m is None:
            bt[4 * bi:4 * bi + 4] = [0, 0, 0, 0]
            if bi in refs:
                details['no_member'].append(bi)
            continue
        fs = len(m.data_bytes)
        fl = BLOCK_EXISTS
        if m.is_compressed:
            fl |= BLOCK_IMPLODE if is_imploded(d, base, m, sector_bytes, fs) else BLOCK_COMPRESS
        if m.encrypted:
            fl |= BLOCK_ENCRYPTION
            nm = name_list.get(bi) or (m.fname if m.how not in ('unnamed', None) else None)
            if nm:
                h3 = M.hashstr(_plain_name(nm), 3)
                if h3 != m.hash_key and ((h3 + m.pos) ^ fs) & 0xFFFFFFFF == m.hash_key:
                    fl |= BLOCK_FIX
            else:
                details.setdefault('unnamed_encrypted', []).append(bi)
        bt[4 * bi:4 * bi + 4] = [m.pos, m.sz, fs, fl]
        details['rebuilt'] += 1
    details['leftover_count'] = sum(1 for m in free_slots if id(m) not in in_use)
    details['name_list'] = dict((bi, name_list[bi]) for bi in sorted(name_list))
    if hs_ok < hn:
        existing = set((ht[4 * s], ht[4 * s + 1]) for s in range(hs_ok) if ht[4 * s + 3] < bn)
        orphan_blocks = [bi for bi in range(bn) if bt[4 * bi + 3] & BLOCK_EXISTS and bi not in pointed_to]
        orphan_names = {}
        taken = set(n.upper() for n in name_list.values())
        nameless = []
        for bi in orphan_blocks:
            m = assigned.get(bi) or by_pos.get(bt[4 * bi])
            if m is not None and m.data_bytes is not None and m.fname and m.how != 'unnamed' and \
                    m.fname.upper() not in taken:
                orphan_names[bi] = m.fname
                taken.add(m.fname.upper())
            else:
                nameless.append((bi, m))
        for bi, m in nameless:
            options = (
                [
                    n
                    for n in listing
                    if n.upper() not in taken
                    and m is not None
                    and m.data_bytes is not None
                    and _kind_matches(n, m)
                    and (M.hashstr(n, 1), M.hashstr(n, 2)) not in existing
                ]
                if m is not None
                else []
            )
            if len(options) != 1:
                details['unnamed'] += 1
                continue
            orphan_names[bi] = options[0]
            taken.add(options[0].upper())
        used_entries = set()
        for bi, nm in sorted(orphan_names.items()):
            s = M.hashstr(nm, 0) & (hn - 1)
            for _k in range(hn):
                free = (s >= hs_ok and s not in used_entries) or (s < hs_ok and ht[4 * s + 3] == 0xFFFFFFFF)
                if free:
                    ht[4 * s:4 * s + 4] = [M.hashstr(nm, 1), M.hashstr(nm, 2), 0, bi]
                    used_entries.add(s)
                    details['inserted'] += 1
                    break
                s = (s + 1) & (hn - 1)
        for s in range(hs_ok, hn):
            if s not in used_entries:
                ht[4 * s:4 * s + 4] = [0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFE]
        details['inserted_names'] = dict((bi, orphan_names[bi]) for bi in sorted(orphan_names))
    out = bytearray(d)
    tb = M.encrypt(bt, M.hashstr('(block table)', 3))
    out[bp:bp + len(tb)] = tb
    if hs_ok < hn:
        th = M.encrypt(ht, M.hashstr('(hash table)', 3))
        out[hp:hp + len(th)] = th
    return bytes(out), details


def carve(file_path, output=None, index_='auto', log=None):
    d = open(file_path, 'rb').read()
    h, _p = M.find_header(d, file_path)
    if h is None:
        return {'err': 'no MPQ header'}
    base = h.offset
    sector_bytes = M.header_sector(h.block_shift)
    t = [x for x in ((base + h.hash_pos) & 0xFFFFFFFF, (base + h.block_pos) & 0xFFFFFFFF) if base + 0x20 < x <= len(d)]
    end_pos = min(t) if t else len(d)
    members, holes = walk(d, h, end_pos)
    details = {
        'file_name': file_path,
        'members': len(members),
        'encrypted_count': sum(1 for m in members if m.encrypted),
        'uncompressed': sum(1 for m in members if not m.is_compressed),
        'holes': holes,
        'end_of_walk': base + (members[-1].pos + members[-1].sz if members else 0x20),
        'end_of_data': end_pos,
    }
    for m in members:
        try:
            m.data_bytes = read_member(d, base, m, sector_bytes)
        except Exception as e:
            m.err = str(e)[:80]
    if index_ == 'auto':
        from doctor.mpq import mpqnames
        index_ = mpqnames.load_big()
    assign_names(members, index_, log)
    how = collections.Counter(m.how for m in members if m.data_bytes is not None)
    details['name_list'] = dict(how)
    details['unreadable_items'] = sum(1 for m in members if m.data_bytes is None)
    file_set = collections.OrderedDict()
    for m in members:
        if m.data_bytes is not None and m.fname and m.fname.upper() not in (x.upper() for x in file_set):
            file_set[m.fname] = m.data_bytes
    details['file_set'] = len(file_set)
    default_value = ('war3map.w3i', 'war3map.w3e', 'war3map.j', 'war3map.lua', 'war3map.wts', 'war3map.doo',
                     'war3mapUnits.doo', 'war3map.wpm', 'war3map.shd', 'war3map.w3u', 'war3map.w3t', 'war3map.w3a')
    present = set(n.upper() for n in file_set)
    details['default_value'] = [n for n in default_value if n.upper() in present]
    details['missing_script'] = not ({'WAR3MAP.J', 'WAR3MAP.LUA'} & present)
    details['missing_w3i'] = 'WAR3MAP.W3I' not in present
    if output:
        from doctor.mpq import mpq_rebuild
        header = d[:base] if d[:4] == b'HM3W' and base >= 0x200 else b''
        if not header:
            try:
                from doctor.mpq import mpqdoctor

                class _A(object):
                    pass
                fake_archive = _A()
                fake_archive.read = lambda n: file_set.get(n)
                header = mpqdoctor.build_hm3w(fake_archive)[0]
            except Exception:
                header = b'HM3W' + b'\0' * (0x200 - 4)
        r = mpq_rebuild.write_mpq(output, file_set, map_header=header[:0x200] if len(header) >= 0x200 else header)
        details['output'] = output
        details['bytes'] = r['bytes']
        details['write_errors'] = r['error_list']
    return details
