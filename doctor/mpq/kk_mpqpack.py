# The files the KK platform hides after the MPQ archive: found, decrypted, named, listed and extracted.
import lzma
import os
import struct

from doctor.mpq import mpqlib as M


MPQ_MAGIC = b'MPQ\x1a'
KEY_LEN = 511
KEY_BLOCK = 512
PROBE_BYTES = 4 << 20
STANDARD_NAMES = (
    'war3map.j', 'scripts\\war3map.j', 'war3map.lua', 'war3map.w3i', 'war3map.w3e', 'war3map.wts', 'war3map.wtg',
    'war3map.wct', 'war3map.w3r', 'war3map.w3c', 'war3map.w3s', 'war3map.doo', 'war3mapUnits.doo', 'war3map.w3u',
    'war3map.w3t', 'war3map.w3a', 'war3map.w3b', 'war3map.w3d', 'war3map.w3h', 'war3map.w3q', 'war3map.mmp',
    'war3map.shd', 'war3map.wpm', 'war3mapMap.blp', 'war3mapMap.tga', 'war3mapPreview.tga', 'war3mapSkin.txt',
    'war3mapMisc.txt', 'war3mapExtra.txt', 'war3map.imp', '(listfile)', '(attributes)', '(signature)', 'kkmap.jc',
    'Units\\UnitData.slk', 'Units\\AbilityData.slk', 'Units\\ItemData.slk', 'Units\\UnitUI.slk',
    'Units\\UnitBalance.slk', 'Units\\UnitWeapons.slk', 'Units\\UnitAbilities.slk', 'Units\\UpgradeData.slk',
    'Units\\DestructableData.slk', 'Doodads\\Doodads.slk', 'Units\\AbilityBuffData.slk',
)
_MINE_EXT = ('.j', '.lua', '.w3i', '.imp', '.txt', '.slk', '.mdx', '.mdl', '.fdf', '.toc', '.doo', '.w3u', '.w3t',
             '.w3a', '.w3b', '.w3d', '.w3h', '.w3q', '.wts', '.ini', '.jc')


def _xor(data, key, phase=0):
    n = len(data)
    if not n:
        return b''
    k = len(key)
    phase %= k
    rep = (key[phase:] + key * (n // k + 2))[:n]
    return (int.from_bytes(data, 'little') ^ int.from_bytes(rep, 'little')).to_bytes(n, 'little')


def _hashes(name):
    return M.hashstr(name, 1), M.hashstr(name, 2)


def _lzma_head_ok(fmt, head):
    if fmt == 'xz':
        return head[:6] == b'\xfd7zXZ\x00'
    if len(head) < 5 or head[0] >= 9 * 5 * 5 or head[0] % 9 + head[0] // 9 % 5 > 4:
        return False
    d = struct.unpack_from('<I', head, 1)[0]
    if not (1 << 12) <= d <= (1 << 30):
        return False
    if fmt == 'alone' and len(head) >= 13:
        n = struct.unpack_from('<Q', head, 5)[0]
        return n == 0xFFFFFFFFFFFFFFFF or n < (1 << 34)
    return True


def _decompressor(fmt, head):
    if fmt == 'alone':
        return lzma.LZMADecompressor(lzma.FORMAT_ALONE), 0
    if fmt == 'xz':
        return lzma.LZMADecompressor(lzma.FORMAT_XZ), 0
    p = head[0]
    lc, p = p % 9, p // 9
    lp, pb = p % 5, p // 5
    d = max(struct.unpack_from('<I', head, 1)[0], 1 << 12)
    f = [{'id': lzma.FILTER_LZMA1, 'lc': lc, 'lp': lp, 'pb': pb, 'dict_size': d}]
    return lzma.LZMADecompressor(lzma.FORMAT_RAW, filters=f), 5


def _decode(plain, fmt):
    try:
        dec, skip = _decompressor(fmt, plain[:13])
        out = dec.decompress(plain[skip:])
    except (lzma.LZMAError, ValueError, MemoryError):
        return None, None
    if dec.eof:
        return out, len(plain) - len(dec.unused_data)
    return out, None


class Layout:
    __slots__ = ('stream', 'key', 'kb_off', 'phase', 'fmt', 'k0', 'k1', 'k2', 'how', 'measured')

    def __init__(self, **kw):
        for s in self.__slots__:
            setattr(self, s, kw.get(s))

    def __repr__(self):
        k = lambda v: 'None' if v is None else '0x%08X' % v
        return (
            'Layout(stream=0x%X, key_block=0x%X, phase=%s, lzma=%s, k0=%s, k1=%s, k2=%s, measured_layout=%s, how=%s)'
            % (
                self.stream,
                self.kb_off,
                self.phase,
                self.fmt,
                k(self.k0),
                k(self.k1),
                k(self.k2),
                self.measured,
                self.how,
            )
        )


def _phase(mode, payload_pos, stream):
    return 0 if mode == 'record' else (payload_pos - stream if mode == 'stream' else payload_pos)


def _record(c, pos, lay):
    if pos + 12 > len(c):
        return None
    e0, e1, es = struct.unpack_from('<III', c, pos)
    p = pos + 12
    ph = _phase(lay.phase, p, lay.stream)
    if lay.k2 is not None:
        size = es ^ lay.k2
        if size == 0 or p + size > len(c):
            return None
        out, used = _decode(_xor(c[p:p + size], lay.key, ph), lay.fmt)
        if out is None or (used is not None and used > size):
            return None
        return e0, e1, size, out, p + size
    out, used = _decode(_xor(c[p:p + PROBE_BYTES], lay.key, ph), lay.fmt)
    if out is None or used is None:
        return None
    return e0, e1, used, out, p + used, es ^ used


def _header(c, pos, lay):
    if pos + 12 > len(c):
        return None
    e0, e1, es = struct.unpack_from('<III', c, pos)
    size = es ^ lay.k2
    if size == 0 or pos + 12 + size > len(c):
        return None
    return e0, e1, size, None, pos + 12 + size


def _chain(c, lay, limit=3):
    n, pos = 0, lay.stream
    while n < limit:
        r = _record(c, pos, lay)
        if r is None or not r[3]:
            break
        n += 1
        pos = r[4]
        if pos == len(c):
            return n, True
    return n, pos == len(c)


def _try(c, s, kb_off, kb, keys=('0', '1'), phases=('record', 'stream', 'absolute'), fmts=('alone', 'props5', 'xz'),
         k2_fallback=True):
    if s + 25 > len(c):
        return None
    for kname in keys:
        key = kb[:KEY_LEN] if kname == '0' else kb[1:]
        for phase in phases:
            p = s + 12
            for fmt in fmts:
                if not _lzma_head_ok(fmt, _xor(c[p:p + 13], key, _phase(phase, p, s))):
                    continue
                lay = Layout(stream=s, key=key, kb_off=kb_off, phase=phase, fmt=fmt,
                             how='key kb[%s:%s], k2 from the LZMA end' % (kname, 511 + int(kname)))
                r = _record(c, s, lay)
                k2s = [r[5]] if r else []
                if not r and k2_fallback:
                    es = struct.unpack_from('<I', c, s + 8)[0]
                    k2s = []
                    for i in (254, 0, 508) + tuple(range(0, KEY_BLOCK - 3)):
                        k2 = struct.unpack_from('<I', kb, i)[0]
                        size = es ^ k2
                        if k2 in k2s or not 0 < size <= len(c) - p:
                            continue
                        try:
                            dec, skip = _decompressor(fmt, _xor(c[p:p + 13], key, _phase(phase, p, s)))
                            dec.decompress(_xor(c[p:p + min(size, 1 << 20)], key, _phase(phase, p, s))[skip:], 1 << 16)
                        except (lzma.LZMAError, ValueError):
                            continue
                        k2s.append(k2)
                    lay.how = 'key kb[%s:%s], k2 = a key-block u32' % (kname, 511 + int(kname))
                for k2 in k2s:
                    lay.k2 = k2
                    n, ends = _chain(c, lay)
                    if n >= 3 or (n >= 1 and ends):
                        return lay
                lay.k2 = None
    return None


def _mpq_header(d):
    o = 0
    while o + 32 <= len(d):
        if d[o:o + 4] == MPQ_MAGIC:
            asz, _v, _bs, hto, bto, hn, bn = struct.unpack_from('<IHHIIII', d, o + 8)
            return o, asz, hto, bto, hn & 0x0FFFFFFF, bn & 0x0FFFFFFF
        o += 512
    return None


def _candidates(d):
    h = _mpq_header(d)
    if not h:
        return [], []
    o, asz, hto, bto, hn, bn = h
    ht = (o + hto) & 0xFFFFFFFF
    bt = (o + bto) & 0xFFFFFFFF
    streams = [asz, o + asz]
    try:
        if 0 <= bt and bt + 16 * bn <= len(d) and bn:
            vals = M.decrypt(d[bt:bt + 16 * bn], M.BLOCK_TABLE_KEY)
            ends = [o + vals[i] + vals[i + 1] for i in range(0, len(vals), 4) if vals[i + 3] & 0x80000000]
            if ends:
                e = max(ends)
                streams += [e + 16 * (hn + bn), e, e + 16 * hn]
    except Exception:
        pass
    streams += [ht + 16 * hn, bt + 16 * bn]
    seen, st = set(), []
    for s in streams:
        if 0 < s < len(d) - 25 and s not in seen:
            seen.add(s)
            st.append(s)
    kbs = []
    if 512 <= ht - KEY_BLOCK and ht <= len(d):
        kbs.append(ht - KEY_BLOCK)
    if o - 512 <= 8192:
        kbs += [x for x in range(512, max(512, o - KEY_BLOCK + 1)) if x not in kbs]
    return st, kbs


def probe_map(d, names=(), index=True, deep=False):
    st, kbs = _candidates(d)
    lay = None
    if st and kbs:
        kb = d[kbs[0]:kbs[0] + KEY_BLOCK]
        for s in st:
            lay = _try(d, s, kbs[0], kb, keys=('0',), phases=('record',), fmts=('alone',), k2_fallback=False)
            if lay:
                break
        if not lay and deep:
            for s in st:
                for kbo in kbs:
                    lay = _try(d, s, kbo, d[kbo:kbo + KEY_BLOCK])
                    if lay:
                        break
                if lay:
                    break
    if lay is None:
        return None
    kb = d[lay.kb_off:lay.kb_off + KEY_BLOCK]
    _name_keys(d, lay, kb, names)
    lay.measured = (lay.kb_off == kbs[0] and lay.phase == 'record' and lay.fmt == 'alone'
                    and lay.key == kb[:KEY_LEN] and lay.k2 == struct.unpack_from('<I', kb, 254)[0]
                    and lay.k0 == struct.unpack_from('<I', kb, 0)[0] and lay.k1 == struct.unpack_from('<I', kb, 508)[0])
    return lay


def _name_keys(c, lay, kb, names):
    recs = [(e0, e1) for e0, e1, *_ in records(c, lay, decode=False)]
    if not recs:
        return
    hs = {}
    for n in list(STANDARD_NAMES) + list(names):
        hs.setdefault(_hashes(n), n)
    has = {h[0] for h in hs}
    dw = [struct.unpack_from('<I', kb, i)[0] for i in range(0, KEY_BLOCK - 3)]
    pref = [dw[0], dw[508]] + dw
    best = (0, None, None)
    for k0 in pref:
        hit = [(e0 ^ k0, e1) for e0, e1 in recs if e0 ^ k0 in has]
        if len(hit) < 2:
            continue
        for k1 in pref:
            n = sum((a, e1 ^ k1) in hs for a, e1 in hit)
            if n > best[0]:
                best = (n, k0, k1)
        if best[0] >= 2:
            break
    if best[0] < 2:
        votes = {}
        for e0, e1 in recs:
            for n in STANDARD_NAMES:
                a, b = _hashes(n)
                votes[(e0 ^ a, e1 ^ b)] = votes.get((e0 ^ a, e1 ^ b), 0) + 1
        if votes:
            (k0, k1), n = max(votes.items(), key=lambda kv: kv[1])
            if n >= 2:
                best = (n, k0, k1)
    lay.k0, lay.k1 = best[1], best[2]


def records(c, lay, decode=True):
    pos = lay.stream
    while True:
        r = _record(c, pos, lay) if decode else _header(c, pos, lay)
        if r is None:
            return
        yield r[:5]
        pos = r[4]


def _outer_names(path):
    try:
        from doctor.mpq import mpqread
        lf = mpqread.Archive(path).read('(listfile)')
    except Exception:
        return []
    return [n for n in (lf or b'').decode('utf-8', 'replace').replace('\r', '\n').split('\n') if n]


def name_records(pairs, names=(), index=True, mined=()):
    want = set(pairs)
    out = {}
    for n in list(STANDARD_NAMES) + list(names) + list(mined):
        for cand, bar in ((n, False), (n, True)) if '/' in n else ((n, False),):
            h = (M.hashstr(cand, 1, bar), M.hashstr(cand, 2, bar))
            if h in want and h not in out:
                out[h] = n.replace('/', '\\') if bar else n
    if index and len(out) < len(want):
        try:
            from doctor.mpq import mpqnames
            g = mpqnames.load_big()
        except Exception:
            g = None
        if g is not None:
            rest = [h for h in want if h not in out]
            idx = g.lookup_batch([h[0] for h in rest], [h[1] for h in rest])
            for h, i in zip(rest, idx):
                if i >= 0:
                    out[h] = g.fname(int(i))
    return out


def _mine(name, data):
    try:
        from doctor.mpq import mpqnames
        return mpqnames.mine_bytes(data)
    except Exception:
        return set()


def _fallback_name(i, h):
    return 'File%08d_%08X_%08X.xxx' % (i, h[0], h[1])


def unpack(path_or_bytes, names=(), index=True, layout=None, deep=False):
    d = open(path_or_bytes, 'rb').read() if isinstance(path_or_bytes, str) else bytes(path_or_bytes)
    if isinstance(path_or_bytes, str):
        names = list(names) + _outer_names(path_or_bytes)
    lay = layout or probe_map(d, names, index, deep)
    if lay is None:
        return {}
    recs = []
    for i, (e0, e1, _s, data, _n) in enumerate(records(d, lay)):
        h = (e0 ^ lay.k0, e1 ^ lay.k1) if lay.k0 is not None else (e0, e1)
        recs.append((h, data))
    named = _iterate_names(recs, names, index)
    return {named.get(h) or _fallback_name(i, h): data for i, (h, data) in enumerate(recs)}


def _iterate_names(recs, names, index):
    pairs = [h for h, _ in recs]
    named = name_records(pairs, names, index)
    mined_from, mined = set(), set()
    while True:
        new = set()
        for h, data in recs:
            n = named.get(h)
            if n and h not in mined_from and os.path.splitext(n)[1].lower() in _MINE_EXT and data:
                mined_from.add(h)
                new |= _mine(n, data)
        new -= mined
        if not new:
            return named
        mined |= new
        more = name_records([h for h in pairs if h not in named], (), False, new)
        if not more:
            return named
        named.update(more)


def extract(path, out_dir, names=(), index=True, progress=None, deep=False):
    d = open(path, 'rb').read()
    names = list(names) + _outer_names(path)
    lay = probe_map(d, names, index, deep)
    if lay is None:
        return {'records': 0, 'named': 0, 'bytes': 0, 'layout': None, 'files': []}
    heads = [(e0, e1) for e0, e1, *_ in records(d, lay, decode=False)]
    pairs = [(e0 ^ lay.k0, e1 ^ lay.k1) if lay.k0 is not None else (e0, e1) for e0, e1 in heads]
    named = name_records(pairs, names, index)
    tmp = os.path.join(out_dir, '_kk_mpqpack_raw')
    os.makedirs(tmp, exist_ok=True)
    keep, total = [], 0
    for i, (_e0, _e1, _s, data, _n) in enumerate(records(d, lay)):
        h = pairs[i]
        total += len(data)
        with open(os.path.join(tmp, '%08d' % i), 'wb') as f:
            f.write(data)
        n = named.get(h)
        if n is None or os.path.splitext(n)[1].lower() in _MINE_EXT:
            keep.append(i)
        if progress and i % 500 == 0:
            progress('record %d/%d' % (i, len(pairs)))
    mined_from, mined = set(), set()
    while True:
        new = set()
        for i in keep:
            n = named.get(pairs[i])
            if n and i not in mined_from and os.path.splitext(n)[1].lower() in _MINE_EXT:
                mined_from.add(i)
                new |= _mine(n, open(os.path.join(tmp, '%08d' % i), 'rb').read())
        new -= mined
        if not new:
            break
        mined |= new
        more = name_records([h for h in pairs if h not in named], (), False, new)
        if not more:
            break
        named.update(more)
    files = []
    for i, h in enumerate(pairs):
        n = named.get(h) or _fallback_name(i, h)
        dst = os.path.join(out_dir, *n.replace('/', '\\').split('\\'))
        os.makedirs(os.path.dirname(dst) or out_dir, exist_ok=True)
        if os.path.exists(dst):
            os.remove(dst)
        os.rename(os.path.join(tmp, '%08d' % i), dst)
        files.append((n, os.path.getsize(dst)))
    os.rmdir(tmp)
    return {'records': len(pairs), 'named': sum(1 for h in pairs if h in named), 'bytes': total, 'layout': lay,
            'files': files}

