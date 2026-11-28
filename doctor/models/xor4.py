# The models and textures of that engine masked one byte in four (the Qimp trailer): the key from the file name, or from the file, checked by the reader.
import collections
import os
import re
import struct
import sys



L_MAX = 64
TRAILER = b'Qimp\x02'
MDX_TAGS = (b'VERS', b'MODL', b'SEQS', b'GLBS', b'MTLS', b'TEXS', b'TXAN', b'GEOS', b'GEOA', b'BONE', b'LITE', b'HELP',
            b'ATCH', b'PIVT', b'PREM', b'PRE2', b'RIBB', b'EVTS', b'CAMS', b'CLID', b'BPOS', b'FAFX', b'CORN', b'SNDS')
_BY_SUFFIX = dict((t[1:], t) for t in MDX_TAGS)


SALT = b'375g4Oi3Z'


def is_masked(d):
    if len(d) < 16 or bytes(d[-5:-1]) != TRAILER[:4]:
        return None
    if d[1:4] == b'DLX' and d[:1] != b'M':
        return 'mdx'
    if d[1:4] == b'LP1' and d[:1] != b'B':
        return 'blp'
    return 'other'


def key_from_name(fname):
    b = fname.encode('utf-8', 'surrogateescape') if isinstance(fname, str) else bytes(fname)
    b = b.rsplit(b'\\', 1)[-1]
    return bytes(c + 32 if 65 <= c <= 90 else c for c in b) + SALT


def unmask(d, P):
    out = bytearray(d[:-5])
    m = len(P)
    for i in range(0, len(out), 4):
        out[i] ^= P[i % m]
    return bytes(out)


def applies(d, hash_key):
    out = bytearray(d)
    L = len(hash_key)
    for j in range(0, (len(out) + 3) // 4):
        out[4 * j] ^= hash_key[j % L]
    return bytes(out)


def _weak(d):
    return [(j, d[4 * j]) for j in range(1, len(d) // 4) if d[4 * j + 1:4 * j + 4] == b'\0\0\0']


def _strong_mdx(d):
    n = len(d)

    def tags_at(q):
        if q == n:
            return True
        if q + 8 > n:
            return False
        if q % 4 == 0:
            return bytes(d[q + 1:q + 4]) in _BY_SUFFIX
        return bytes(d[q:q + 4]) in MDX_TAGS

    def advance(p, max_depth):
        if p == n:
            return []
        if max_depth > 4000 or not tags_at(p):
            return None
        obs = []
        if p % 4 == 0:
            obs.append((p // 4, d[p] ^ _BY_SUFFIX[bytes(d[p + 1:p + 4])][0]))
        field_id = bytearray(d[p + 4:p + 8])
        k = (4 - (p + 4) % 4) % 4
        cands = []
        for v in range(256):
            field_id[k] = v
            q = p + 8 + struct.unpack('<I', bytes(field_id))[0]
            if tags_at(q):
                cands.append((v, q))
        for v, q in cands:
            rest = advance(q, max_depth + 1)
            if rest is not None:
                return obs + [((p + 4 + k) // 4, d[p + 4 + k] ^ v)] + rest
        return None

    sys.setrecursionlimit(max(sys.getrecursionlimit(), 20000))
    r = advance(4, 0)
    return [(0, d[0] ^ ord('M'))] + (r or [])


def _strong_blp(d):
    obs = [(0, d[0] ^ ord('B'))]
    if d[5:8] == b'\0\0\0':
        pass
    for j in range(40, len(d) // 4 - 1):
        if d[4 * j + 3] == 0xFF:
            obs.append((j + 1, d[4 * j + 4]))
    return obs


def _resolve(n4, strong, weak, Lmax=L_MAX):
    for L in range(1, Lmax + 1):
        votes = collections.defaultdict(collections.Counter)
        conflict = False
        fixed_ones = {}
        for j, v in strong:
            r = j % L
            if r in fixed_ones and fixed_ones[r] != v:
                conflict = True
                break
            fixed_ones[r] = v
        if conflict:
            continue
        for j, v in weak:
            votes[j % L][v] += 1
        hash_key = bytearray(L)
        ok = True
        for r in range(L):
            if r in fixed_ones:
                hash_key[r] = fixed_ones[r]
                continue
            c = votes.get(r)
            if not c:
                ok = False
                break
            (v, a), = c.most_common(1)
            if a < 2 or a < 0.6 * sum(c.values()):
                ok = False
                break
            hash_key[r] = v
        if ok and L <= n4:
            yield L, bytes(hash_key)


def _check_mdx(c):
    if c[:4] != b'MDLX':
        return False
    n, p = len(c), 4
    vers = None
    while p < n:
        if p + 8 > n or bytes(c[p:p + 4]) not in MDX_TAGS:
            return False
        sz = struct.unpack_from('<I', c, p + 4)[0]
        if c[p:p + 4] == b'VERS' and sz == 4:
            vers = struct.unpack_from('<I', c, p + 8)[0]
        p += 8 + sz
    return p == n and vers in (800, 900, 1000, 1100)


def _check_blp(c):
    if c[:4] != b'BLP1':
        return False
    try:
        from doctor.models import blpread
        info = blpread.header_bytes(c)
        blpread._data_bytes(c, info, 0)
        return True
    except Exception:
        return False


POW2 = frozenset(1 << i for i in range(8))
JPEG_MARKERS = (0x00, 0xC0, 0xC2, 0xC4, 0xDA, 0xD9, 0xD8, 0xDB, 0xDD, 0xFE, 0xE0) + tuple(range(0xD0, 0xD8))
ASCII_LETTERS = frozenset(b'abcdefghijklmnopqrstuvwxyz0123456789_-. ()')
NAME_LETTERS = frozenset(b'abcdefghijklmnopqrstuvwxyz0123456789_-. ()[]#&+,=@~!$%^{}\'') | frozenset(range(0x80, 0x100))


def _restore_blp(d, cap=200000, with_prior=False, letters=None):
    import itertools
    n = len(d)
    if n < 170 or d[161] != 0xD8:
        return None, None, 'not a JPEG BLP1 (paletted: not handled)'

    def hi(o):
        return struct.unpack_from('<I', d, o)[0] >> 8
    strong = [(0, d[0] ^ ord('B')), (40, d[160] ^ 0xFF)]
    if d[162:164] == b'\xff\xdb' and d[165] == 0x43:
        strong.append((41, d[164]))
    for o, v in ((n - 2, 0xFF), (n - 1, 0xD9)):
        if o % 4 == 0:
            strong.append((o // 4, d[o] ^ v))
    in_use = [i for i in range(16) if i == 0 or hi(28 + 4 * i) or hi(92 + 4 * i)]
    for i in range(16):
        if i not in in_use:
            strong += [(7 + i, d[28 + 4 * i]), (23 + i, d[92 + 4 * i])]
    begin = ((hi(28) + 1) << 8) + 3
    vote_obs = [(j + 1, d[4 * j + 4]) for j in range(begin // 4, n // 4 - 1) if d[4 * j + 3] == 0xFF]
    nameless = {1: frozenset((0,)), 2: frozenset((0, 1, 4, 8)), 6: frozenset((0, 1))}
    for j in (3, 4):
        if hi(4 * j) == 0:
            nameless[j] = POW2

    def chain_ok(c):
        offs = [struct.unpack_from('<I', c, 28 + 4 * i)[0] for i in in_use]
        sizes = [struct.unpack_from('<I', c, 92 + 4 * i)[0] for i in in_use]
        h = struct.unpack_from('<I', c, 156)[0]
        if offs[0] != 160 + h:
            return False
        for a in range(len(offs) - 1):
            if offs[a] + sizes[a] != offs[a + 1]:
                return False
        return offs[-1] + sizes[-1] == n
    import math
    tail = b'.blp' + SALT
    if with_prior:
        forms = []
        for m in range(len(tail) + 1, 120):
            Lm = m // math.gcd(4, m)
            s0 = m - len(tail)
            fx = {}
            for r in range(Lm):
                q = (4 * r) % m
                if q >= s0:
                    fx[r] = tail[q - s0]
            forms.append((Lm, fx))
    else:
        forms = [(L, {}) for L in range(1, L_MAX + 1)]
    for L, fixed0 in forms:
        fixed_ones = dict(fixed0)
        invalid = False
        for j, v in strong:
            if fixed_ones.setdefault(j % L, v) != v:
                invalid = True
                break
        if invalid:
            continue
        votes = collections.defaultdict(collections.Counter)
        nobs = collections.Counter()
        for j, v in vote_obs:
            nobs[j % L] += 1
            for m in JPEG_MARKERS:
                votes[j % L][v ^ m] += 1
        options = []
        for r in range(L):
            if r in fixed_ones:
                options.append((fixed_ones[r],))
                continue
            cand = set(letters or NAME_LETTERS) if with_prior else set(range(256))
            for j in range(1, 40):
                if j % L == r and j in nameless:
                    cand &= set(x ^ d[4 * j] for x in nameless[j])
            c = votes.get(r)
            if c:
                topo = max(c[v] for v in cand) if cand else 0
                if topo >= max(2, 0.8 * nobs[r]):
                    cand = set(v for v in cand if c[v] == topo)
            if not cand:
                invalid = True
                break
            options.append(tuple(sorted(cand)))
        if invalid:
            continue
        total = 1
        for o in options:
            total *= len(o)
        if total > cap:
            continue
        for hash_key in itertools.product(*options):
            hash_key = bytes(hash_key)
            header = applies(d[:160], hash_key)
            if not chain_ok(header + d[160:]):
                continue
            c = applies(d, hash_key)
            if _check_blp(c):
                return c, L, hash_key
    return None, None, 'no key the reader accepts (%d strong, %d stuffing votes)' % (len(strong), len(vote_obs))


def restore(d, attempts=6, fname=None):
    kind = is_masked(d)
    info = {'kind': kind, 'L': None, 'hash_key': None, 'reason': None, 'by_name': False}
    if kind is None:
        info['reason'] = 'not masked'
        return None, info
    if fname:
        P = key_from_name(fname)
        c = unmask(d, P)
        if kind == 'other' or (_check_mdx if kind == 'mdx' else _check_blp)(c):
            info.update(hash_key=P.decode('latin-1'), L=len(P), by_name=True)
            return c, info
    if kind == 'other':
        info['reason'] = 'masked file of another type: only its name gives the key'
        return None, info
    d = bytes(d[:-len(TRAILER)])
    if kind == 'blp':
        c, L, hash_key = _restore_blp(d, cap=4096)
        if c is None:
            c, L, hash_key = _restore_blp(d, with_prior=True)
        if c is None:
            c, L, hash_key = _restore_blp(d, cap=3000000, with_prior=True, letters=ASCII_LETTERS)
            if c is not None:
                info['prior'] = True
        if c is None:
            info['reason'] = hash_key
            return None, info
        info.update(L=L, hash_key=hash_key.decode('latin-1'))
        return c, info
    strong = _strong_mdx(d) if kind == 'mdx' else _strong_blp(d)
    weak = _weak(d)
    verify = _check_mdx if kind == 'mdx' else _check_blp
    n = 0
    for L, hash_key in _resolve(len(d) // 4, strong, weak):
        c = applies(d, hash_key)
        if verify(c):
            info.update(L=L, hash_key=hash_key.decode('latin-1'))
            return c, info
        n += 1
        if n >= attempts:
            break
    info['reason'] = 'no key the reader accepts (%d strong, %d weak observations)' % (len(strong), len(weak))
    return None, info


def probe(a, sample_size=400):
    from doctor.mpq import mpqnames
    from doctor.script import ydwe_aes
    achou = {'assets': False, 'lua': False}
    for i, bi in enumerate(sorted(a.pointed_blocks())):
        if i >= sample_size or all(achou.values()):
            break
        d = mpqnames.read_unnamed(a, bi, whole=True)
        if not d:
            continue
        if is_masked(d):
            achou['assets'] = True
        elif d[:1] != b'\x1b' and ydwe_aes.looks_ciphered(d):
            achou['lua'] = True
    return achou if any(achou.values()) else None


def has_masked(a, sample_size=400):
    from doctor.mpq import mpqnames
    for i, bi in enumerate(sorted(a.pointed_blocks())):
        if i >= sample_size:
            break
        d = mpqnames.read_unnamed(a, bi, whole=True)
        if d and is_masked(d):
            return True
    return False


RX_W3P_PATH = re.compile(rb'[\x21-\x7e\x80-\xff ]{1,160}?\.(?:mdx|mdl|blp|tga|dds|wav|mp3|ogg|flac)', re.I)
_EXT_SWAP = {'.mdl': '.mdx', '.tga': '.blp', '.dds': '.blp'}


def _variants(t):
    t = t.replace('/', '\\').strip().strip('"\'')
    out = set()
    for x in (t, t.lstrip('\\'), t.split('"')[-1], t.split('\0')[-1], t.split('=')[-1]):
        x = x.strip()
        if '.' not in x[-6:]:
            continue
        b, e = x[:-4], x[-4:].lower()
        out |= {x, b + e, b + _EXT_SWAP.get(e, e)}
    return out


def harvest_names(a, known, texts):
    new_ones = {}
    seen = set()
    for t in texts:
        for m in RX_W3P_PATH.findall(bytes(t)):
            s = m.decode('utf-8', 'surrogateescape')
            if s in seen:
                continue
            seen.add(s)
            for v in _variants(s):
                try:
                    r = a.find(v)
                except Exception:
                    r = None
                if r and r[1] not in known and r[1] not in new_ones:
                    new_ones[r[1]] = v
    return new_ones


RX_NUMBER = re.compile(r'(\d+)(?!.*\d)')
_PATTERN_EXTS = ('.blp', '.mdx', '.tga', '.dds', '.png', '.mdl')


def names_by_pattern(a, known, targets, cap=4000000):
    targets = set(targets)
    cands = set()
    for n in known.values():
        d, _, base = n.replace('/', '\\').rpartition('\\')
        d = d + '\\' if d else ''
        stem, ext = (base[:-4], base[-4:]) if '.' in base[-5:] else (base, '')
        for e in set(_PATTERN_EXTS) | {ext}:
            cands.add(d + stem + e)
        for from_, new_value in (
            ('commandbuttons\\', 'commandbuttonsdisabled\\'),
            ('commandbuttonsdisabled\\', 'commandbuttons\\'),
        ):
            if d.lower().endswith(from_):
                dd = d[:len(d) - len(from_)] + new_value
                for st in (stem[3:] if stem.lower().startswith('btn') else stem,
                           stem[6:] if stem.lower().startswith(('disbtn', 'pasbtn')) else stem):
                    for pre in ('BTN', 'DISBTN', 'PASBTN'):
                        cands.add(dd + pre + st + ext)
        for st in ('DIS' + stem, stem[3:] if stem.upper().startswith('DIS') else None):
            if st:
                cands.add(d + st + ext)
        if d.lower().startswith('war3mapimported\\'):
            cands.add(d[16:] + base)
        else:
            cands.add('war3mapImported\\' + d + base)
    patterns = set()
    for n in list(known.values()):
        m = RX_NUMBER.search(n)
        if m and len(m.group(1)) <= 3:
            patterns.add((n[:m.start()], len(m.group(1)), n[m.end():]))
    for pre, w, suf in patterns:
        if len(cands) > cap:
            break
        for k in range(10 ** w):
            cands.add('%s%0*d%s' % (pre, w, k, suf))
            if w > 1 and k < 10 ** (w - 1):
                cands.add('%s%d%s' % (pre, k, suf))
    new_ones = {}
    for c in cands:
        try:
            r = a.find(c)
        except Exception:
            r = None
        if r and r[1] in targets and r[1] not in known and r[1] not in new_ones:
            new_ones[r[1]] = c
    return new_ones


def to_map(entry, output, log=None):
    from doctor.mpq import mpq_rebuild
    from doctor.mpq import mpqnames
    from doctor.mpq import mpqread
    a = mpqread.Archive(entry)
    listing = mpqread.listfile_names(a)
    name_list = {}
    for n in listing:
        r = a.find(n)
        if r:
            name_list[r[1]] = n
    masked, texts = [], []
    for bi in sorted(a.pointed_blocks()):
        d = mpqnames.read_unnamed(a, bi, whole=True)
        if not d:
            continue
        if is_masked(d):
            masked.append(bi)
        elif len(d) < (32 << 20):
            texts.append(d)
    try:
        from doctor.script import ydwe_aes
        texts += list(ydwe_aes.map_own(a)['lua_modules'].values())
    except Exception:
        pass
    name_list.update(harvest_names(a, name_list, texts))
    del texts
    for _goes_back in range(3):
        unclosed = []
        for bi in masked:
            d = mpqnames.read_unnamed(a, bi, whole=True)
            if is_masked(d) != 'mdx':
                continue
            c, _i = restore(d, fname=name_list.get(bi))
            if c is not None:
                unclosed.append(c)
        more = harvest_names(a, name_list, unclosed)
        more.update(
            names_by_pattern(
                a, dict(list(name_list.items()) + list(more.items())), [bi for bi in masked if bi not in name_list]
            )
        )
        name_list.update(more)
        if not more:
            break
    tally = collections.Counter()

    def swap(bi, d):
        if not is_masked(d):
            return d
        c, info = restore(d, fname=name_list.get(bi))
        tally[(info['kind'], c is not None)] += 1
        tally['by_name'] += bool(info.get('by_name'))
        return c if c is not None else d
    mpq_rebuild.rebuild(entry, output, sorted(set(listing) | set(name_list.values())), log=lambda s: None,
                        transform=swap)
    out = dict((t, (tally[(t, True)], tally[(t, False)])) for t in ('mdx', 'blp', 'other'))
    out['by_name'] = tally['by_name']
    out['name_list'] = len(name_list)
    if log:
        log('0c. masked models/textures (Qimp): %d of %d MDX and %d of %d BLP restored in place (%d by their name)'
            % (out['mdx'][0], sum(out['mdx']), out['blp'][0], sum(out['blp']), out['by_name']))
    return out


def prepare_map_copy(map_path, work, log=print):
    from doctor.mpq import mpqread
    if not has_masked(mpqread.Archive(map_path)):
        return None, None
    base = os.path.join(work, 'xor4_base.w3x')
    return base, to_map(map_path, base, log)

