# The KK platform's CAME container (the whole map encrypted with AES-256-GCM + zstd outside the MPQ): the key from the SDK inside the map, every file decrypted, named and written into a normal map.
import hashlib
import json
import mmap
import os
import shutil
import struct
import zlib

from doctor.mpq import mpqlib as M
from doctor.mpq import mpqread
from doctor.mpq import kk_mpqpack
from doctor.mpq import mpq_rebuild

HERE = os.path.dirname(os.path.abspath(__file__))
KK = os.path.normpath(os.path.join(HERE, '..', 'kk'))

CAME = b'MPQ\x1aCAME'
MPQ_MAGIC = b'MPQ\x1a'
SCAN_LIMIT = 0x10000
SECTOR = 0x1000
KEY_BLOCK = 0x3C
KEY_SIZE = 32
PROFILES = {
    '9422dd88709e69456993c17a8f63b4df31c912b279ceda96309de51a784f94c0': ('TestMap0.099', 0x4056B2),
    '27a5c298f6d8547bc1d0dd2661a00e2bac412a0ef9c900e6f8219488e00ec7af': ('A0F79 CAME', 0x3C0220),
    '471a076048e14bce9e579118560a54c51d892723c545afb7527a9876a95ed12a': ('Online_J (Themida SDK)', 0x3821A4),
    '90c4c56bd5c5828df81c473f04cf68544fde662a6e6e117186706ae48c654522': ('CAME SDK (auto, .rdata)', 0x3C52A0),
}
CACHE = os.environ.get('KK_CAME_CACHE') or os.path.join(HERE, '..', 'cache', 'came_sdk.json')


class CameError(Exception):
    pass


def _libs():
    try:
        from compression import zstd
    except ImportError:
        try:
            import zstandard as zstd
        except ImportError as e:
            raise CameError(
                'zstd is missing (the Python 3.14 stdlib has it): python -m pip install -r requirements.txt'
            ) from e
    try:
        from Crypto.Cipher import AES
    except ImportError as e:
        raise CameError('missing %s: python -m pip install -r requirements.txt' % e.name) from e
    return zstd, AES


def _zstd_decompress(zstd, data_bytes):
    if getattr(zstd, '__name__', '') == 'compression.zstd':
        return zstd.decompress(data_bytes)
    return zstd.ZstdDecompressor().decompress(data_bytes)


def is_came(d):
    return layout(d) is not None


def _i32(d, off):
    return struct.unpack_from('<i', d, off)[0]


def layout(d, base=None):
    if base is None:
        base = _find_header(d)
    if base is None or base < 0 or len(d) < base + 0x20:
        return None
    if bytes(d[base:base + 8]) != CAME:
        return None
    record_count = struct.unpack_from('<I', d, base + 8)[0]
    hpos = _i32(d, base + 0x10)
    bpos = _i32(d, base + 0x14)
    hn, bn = struct.unpack_from('<II', d, base + 0x18)
    hash_abs = (base + hpos) & 0xFFFFFFFF
    block_abs = (base + bpos) & 0xFFFFFFFF
    if not (0 < hn <= 0x10000 and 0 < bn <= 0x10000):
        return None
    if hash_abs < KEY_BLOCK or block_abs < 0 or record_count < 0x200:
        return None
    if hash_abs + hn * 16 > len(d) or block_abs + bn * 16 > len(d) or record_count >= len(d):
        return None
    end_pos = len(d)
    if len(d) >= 0x74 and bytes(d[-0x74:-0x70]) == b'MHAU':
        n_trailer = struct.unpack_from('<I', d, len(d) - 0x74 + 8)[0]
        candidate = len(d) - 0x74 - n_trailer * 4 - 28
        if record_count < candidate <= len(d):
            end_pos = candidate
    return {'base': base, 'record_count': record_count, 'hash_abs': hash_abs, 'block_abs': block_abs,
            'hash_n': hn, 'block_n': bn, 'end_pos': end_pos}


def _find_header(d):
    n = min(len(d), SCAN_LIMIT)
    b = bytes(d[:n])
    for off in range(0, n - 8, 0x200):
        if b[off:off + 8] == CAME:
            return off
    return b.find(CAME)


def block_list(d, lay):
    raw = bytes(d[lay['block_abs']:lay['block_abs'] + lay['block_n'] * 16])
    bt = M.decrypt_bytes(raw, M.hashstr('(block table)', 3))
    return [struct.unpack_from('<4I', bt, i * 16) for i in range(lay['block_n'])]


def decompress_zstd(raw, size):
    if not raw:
        return b''
    nsec = (size + SECTOR - 1) // SECTOR
    if len(raw) < (nsec + 1) * 4:
        return None
    offs = struct.unpack_from('<%dI' % (nsec + 1), raw, 0)
    out = bytearray()
    for i in range(nsec):
        a, b = offs[i], offs[i + 1]
        if b < a or b > len(raw):
            return None
        ch = raw[a:b]
        want = min(SECTOR, size - i * SECTOR)
        if not ch:
            return None
        if len(ch) == want:
            out += ch
            continue
        mask = ch[0]
        try:
            if mask & 0x02:
                out += zlib.decompress(ch[1:])
            elif mask & 0x08:
                import bz2
                out += bz2.decompress(ch[1:])
            elif mask == 0:
                out += ch[1:]
            else:
                return None
        except Exception:
            return None
    return bytes(out[:size])


def find_pe(d, lay, progress=None):
    for i, (off, csize, size, flags) in enumerate(block_list(d, lay)):
        if flags & 0x00010000 or not size or size > 0x20000000:
            continue
        a = lay['base'] + off
        if a + csize > len(d):
            continue
        pe = decompress_zstd(bytes(d[a:a + csize]), size)
        if pe and pe[:2] == b'MZ':
            return {'block_entry': i, 'pe': pe, 'sha256': hashlib.sha256(pe).hexdigest()}
    return None


def pe_sections(pe):
    if len(pe) < 0x40 or pe[:2] != b'MZ':
        return []
    e = struct.unpack_from('<I', pe, 0x3C)[0]
    if e + 0x18 > len(pe) or pe[e:e + 4] != b'PE\0\0':
        return []
    nsec = struct.unpack_from('<H', pe, e + 6)[0]
    optsz = struct.unpack_from('<H', pe, e + 0x14)[0]
    off = e + 0x18 + optsz
    out = []
    for i in range(nsec):
        s = off + i * 0x28
        if s + 0x28 > len(pe):
            break
        fname = pe[s:s + 8].rstrip(b'\0').decode('latin1', 'replace')
        vsize, va, rsize, rptr = struct.unpack_from('<4I', pe, s + 8)
        chars = struct.unpack_from('<I', pe, s + 0x24)[0]
        out.append({'fname': fname, 'va': va, 'vsize': vsize, 'rsize': rsize, 'rptr': rptr, 'chars': chars})
    return out


def kek_at_rva(pe, rva):
    for s in pe_sections(pe):
        if s['va'] <= rva < s['va'] + max(s['rsize'], s['vsize']):
            fo = s['rptr'] + (rva - s['va'])
            if fo + KEY_SIZE <= len(pe):
                return pe[fo:fo + KEY_SIZE], fo
    return None, None


def _cache_read():
    try:
        with open(CACHE, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _cache_write(sha, fname, rva, kek):
    c = _cache_read()
    c[sha] = {'fname': fname, 'rva': rva, 'kek': kek.hex() if kek else None}
    try:
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        with open(CACHE, 'w', encoding='utf-8') as f:
            json.dump(c, f, indent=1, sort_keys=True)
    except OSError:
        pass


def unwrap(blob, kek):
    if len(blob) != KEY_BLOCK:
        return None
    _z, AES = _libs()
    nonce, ct, tag = blob[:12], blob[12:44], blob[44:60]
    try:
        c = AES.new(kek, AES.MODE_GCM, nonce=nonce)
        return c.decrypt_and_verify(ct, tag)
    except ValueError:
        return None


def search_kek(pe, blob, progress=None, out_limit=None):
    _, AES = _libs()

    def tries(kek):
        nonce, ct, tag = blob[:12], blob[12:44], blob[44:60]
        try:
            c = AES.new(kek, AES.MODE_GCM, nonce=nonce)
            return c.decrypt_and_verify(ct, tag)
        except ValueError:
            return None

    secs = [s for s in pe_sections(pe) if (s['chars'] & 0x40000000) and s['rsize'] >= KEY_SIZE]
    order = ([s for s in secs if not (s['chars'] & 0x80000000) and not (s['chars'] & 0x20000000)],
             [s for s in secs if not (s['chars'] & 0x80000000) and (s['chars'] & 0x20000000)],
             [s for s in secs if s['chars'] & 0x80000000])
    seen = 0
    for cluster in order:
        for s in cluster:
            begin = s['rptr']
            end_pos = min(s['rptr'] + s['rsize'], len(pe)) - KEY_SIZE
            if end_pos <= begin:
                continue
            for fo in range(begin, end_pos + 1, 4):
                seen += 1
                if out_limit and seen > out_limit:
                    return None, None
                window = pe[fo:fo + KEY_SIZE]
                if tries(window):
                    return window, s['va'] + (fo - s['rptr'])
            if progress and seen % 20000 == 0:
                progress('key search: %d windows' % seen)
    return None, None


def _blobs(d, lay, out_limit=0x10000):
    fixed_kek = lay['hash_abs'] - KEY_BLOCK
    if 0 <= fixed_kek <= len(d) - KEY_BLOCK:
        yield fixed_kek
    begin = max(0, lay['base'] - out_limit)
    for o in range(begin, max(0, lay['base'] - KEY_BLOCK + 1)):
        if o != fixed_kek:
            yield o
    if lay['hash_abs'] > lay['base']:
        begin = max(lay['base'], lay['hash_abs'] - out_limit, KEY_BLOCK)
        for o in range(begin, lay['hash_abs'] - KEY_BLOCK):
            if o != fixed_kek:
                yield o


def hash_key(d, lay, progress=None, pe_info=None):
    blobs = list(_blobs(d, lay))
    if not blobs:
        raise CameError('no blob window before the header/hash table')
    info = pe_info or find_pe(d, lay)
    if not info:
        raise CameError('no SDK PE among the blocks of the container: nowhere to take the key from')
    pe, sha = info['pe'], info['sha256']
    editor_profile = PROFILES.get(sha)
    cache = _cache_read().get(sha)

    def open_blob(kek):
        for o in blobs:
            k = unwrap(bytes(d[o:o + KEY_BLOCK]), kek)
            if k:
                return k, o
        return None, None

    if editor_profile:
        kek, _fo = kek_at_rva(pe, editor_profile[1])
        if kek:
            k, o = open_blob(kek)
            if k:
                return {
                    'key': k,
                    'kek': kek,
                    'kek_rva': editor_profile[1],
                    'sdk': editor_profile[0],
                    'origin': 'editor_profile',
                    'blob': o,
                }
    if cache:
        try:
            kek = bytes.fromhex(cache['kek']) if cache.get('kek') else None
        except ValueError:
            kek = None
        if kek:
            k, o = open_blob(kek)
            if k:
                return {'key': k, 'kek': kek, 'kek_rva': cache.get('rva'), 'sdk': cache.get('fname'),
                        'origin': 'cache', 'blob': o}
    if progress:
        progress('CAME: the SDK %s is not in the table; searching for the key' % sha[:12])
    blob = bytes(d[blobs[0]:blobs[0] + KEY_BLOCK])
    kek, rva = search_kek(pe, blob, progress)
    if not kek:
        raise CameError('the KEK is not in the readable sections of the SDK (sha256 %s)' % sha)
    k = unwrap(blob, kek)
    if not k:
        raise CameError('the KEK found at RVA 0x%X does not open the blob' % rva)
    _cache_write(sha, 'auto (RVA 0x%X)' % rva, rva, kek)
    return {'key': k, 'kek': kek, 'kek_rva': rva, 'sdk': 'auto (RVA 0x%X)' % rva, 'origin': 'lookup',
            'blob': blobs[0]}


def record_count(d, lay, out_limit=None):
    pos = lay['record_count']
    end_pos = lay.get('end_pos', len(d))
    n = 0
    while pos + 12 <= end_pos:
        a, b, size = struct.unpack_from('<3I', d, pos)
        if size < 0x1C or pos + 12 + size > end_pos:
            return
        yield a, b, size, pos + 12
        pos += 12 + size
        n += 1
        if out_limit and n >= out_limit:
            return


def read_record(d, a, b, size, pos, key):
    zstd, AES = _libs()
    nonce = bytes(d[pos:pos + 12])
    ct = bytes(d[pos + 12:pos + size - 16])
    tag = bytes(d[pos + size - 16:pos + size])
    try:
        c = AES.new(key, AES.MODE_GCM, nonce=nonce)
        c.update(struct.pack('<II', a, b))
        plain = c.decrypt_and_verify(ct, tag)
    except ValueError:
        return None
    try:
        return _zstd_decompress(zstd, plain)
    except zstd.ZstdError:
        return None


def info(d=None, file_path=None):
    closed = False
    if d is None:
        f = open(file_path, 'rb')
        d = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        closed = True
    try:
        lay = layout(d)
        if lay is None:
            return None
        n = total = 0
        for _a, _b, size, _pos in record_count(d, lay):
            n += 1
            total += size
        pe = find_pe(d, lay)
        sdk = None
        key_state = 'lookup'
        if pe:
            editor_profile = PROFILES.get(pe['sha256'])
            sdk = {
                'sha256': pe['sha256'],
                'fname': editor_profile[0] if editor_profile else 'unknown',
                'rva': editor_profile[1] if editor_profile else None,
                'byte_size': len(pe['pe']),
                'block_entry': pe['block_entry'],
            }
            if editor_profile or _cache_read().get(pe['sha256']):
                key_state = 'editor_profile' if editor_profile else 'cache'
        return {'base': lay['base'], 'record_count': n, 'bytes': total, 'sdk': sdk, 'hash_key': key_state,
                'hash_n': lay['hash_n'], 'block_n': lay['block_n'], 'first_pos': lay['record_count']}
    finally:
        if closed:
            d.close()


def _pairs_of(file_path):
    f = open(file_path, 'rb')
    d = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
    lay = layout(d)
    if lay is None:
        d.close()
        f.close()
        raise CameError('not a CAME container')
    return d, f, lay


def extract(file_path, folder, name_list=(), index=True, progress=None):
    _z, _AES = _libs()
    d, f, lay = _pairs_of(file_path)
    try:
        tmp = os.path.join(folder, '_came_raw')
        os.makedirs(tmp, exist_ok=True)
        ch = hash_key(d, lay, progress)
        pairs = []
        for i, (a, b, size, pos) in enumerate(record_count(d, lay)):
            plain = read_record(d, a, b, size, pos, ch['key'])
            if plain is None:
                raise CameError('record %d (hash %08X %08X) does not decrypt: the key is wrong' % (i, a, b))
            with open(os.path.join(tmp, '%08d' % i), 'wb') as fh:
                fh.write(plain)
            pairs.append((a, b, len(plain)))
            if progress and i % 500 == 0:
                progress('decrypt: %d records' % (i + 1))
        hash_pairs = [(a, b) for a, b, _s in pairs]
        named = kk_mpqpack.name_records(hash_pairs, name_list, index)
        mined = set()
        for _run_once in range(6):
            new_ones = set()
            for i, (a, b, _s) in enumerate(pairs):
                n = named.get((a, b))
                if n and (a, b) not in mined and os.path.splitext(n)[1].lower() in kk_mpqpack._MINE_EXT:
                    mined.add((a, b))
                    new_ones |= kk_mpqpack._mine(n, open(os.path.join(tmp, '%08d' % i), 'rb').read())
            new_ones -= mined
            if not new_ones:
                break
            more = kk_mpqpack.name_records([h for h in hash_pairs if h not in named], (), False, new_ones)
            if not more:
                break
            named.update(more)
        written = set()
        file_set = []
        unnamed = 0
        unres = []
        for i, (a, b, size) in enumerate(pairs):
            src = os.path.join(tmp, '%08d' % i)
            n = named.get((a, b))
            if n is None:
                unnamed += 1
                n = os.path.join('unknown_files', '%08X_%08X.%s' % (a, b, _ext_from_content(src)))
                unres.append((a, b, size))
            dst = kk_mpqpack._destination(folder, tmp, n, written)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            os.replace(src, dst)
            file_set.append((os.path.relpath(dst, folder).replace(os.sep, '\\'), os.path.getsize(dst)))
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, '_unresolved.txt'), 'w', encoding='utf-8') as fh:
            fh.write('# records whose names are not stored anywhere in the map\n')
            fh.write('# hashA hashB  (use these to match against a listfile later)\n')
            for a, b, size in unres:
                fh.write('%08X %08X %d\n' % (a, b, size))
        return {
            'record_count': len(pairs),
            'named': len(pairs) - unnamed,
            'bytes': sum(s for _a, _b, s in pairs),
            'file_set': file_set,
            'unnamed': unnamed,
            'pairs': [(a, b) for a, b, _s in pairs],
            'hash_key': {'sdk': ch['sdk'], 'origin': ch['origin'], 'kek_rva': ch['kek_rva'], 'blob': ch.get('blob')},
        }
    finally:
        shutil.rmtree(os.path.join(folder, '_came_raw'), ignore_errors=True)
        d.close()
        f.close()


def _ext_from_content(file_path):
    with open(file_path, 'rb') as fh:
        h = fh.read(16)
    for sig, ext in ((b'MDLX', 'mdx'), (b'BLP1', 'blp'), (b'BLP2', 'blp'), (b'RIFF', 'wav'), (b'PNG', 'png'),
                     (b'\xff\xd8\xff', 'jpg'), (b'ID3', 'mp3'), (b'OggS', 'ogg'), (b'fLaC', 'flac'),
                     (b'W3E!', 'w3e'), (b'HM3W', 'w3x'), (b'PK\x03\x04', 'zip'), (b'7z\xbc\xaf', '7z'),
                     (b'\x1f\x8b', 'gz'), (b'BZh', 'bz2'), (b'\x28\xb5\x2f\xfd', 'zst'), (b'DDS ', 'dds'),
                     (b'\x89PNG', 'png')):
        if h.startswith(sig):
            return ext
    return 'bin'


def _map_header(file_path):
    with open(file_path, 'rb') as fh:
        header = fh.read(0x200)
    if len(header) < 0x200 or header[:4] != b'HM3W':
        return b'HM3W' + bytes(508)
    return header


def _write_map(output, item_entries, map_header, sector_shift=3, level=6, all_items=False):
    sector_bytes = 512 << sector_shift
    special_names = ('(listfile)', '(attributes)', '(signature)')
    name_list = sorted(
        {n for n, _h, _p in item_entries if n not in special_names and not n.lower().startswith('unknown_files\\')},
        key=lambda n: (n.lower(), n),
    )
    if '(listfile)' not in {n for n, _h, _p in item_entries}:
        item_entries = list(item_entries) + [('(listfile)', None, None)]
    hm = 16
    tgt = (len(item_entries) + max(64, len(item_entries) // 16)) if all_items else 2 * len(item_entries)
    while hm < tgt:
        hm <<= 1
    map_header = bytes(map_header)
    if len(map_header) % 0x200:
        map_header += b'\0' * (0x200 - len(map_header) % 0x200)
    with open(output, 'wb') as out:
        out.write(map_header)
        out.write(bytes(32))
        data_bytes = 0
        blocks_v = []
        hash_entries = []
        for fname, hashes, file_path in sorted(item_entries, key=lambda x: (x[0].lower(), x[0])):
            if fname == '(listfile)':
                body_text = ('\r\n'.join(name_list) + '\r\n').encode('utf-8', 'surrogateescape')
                body, fl = mpq_rebuild.pack_file(body_text, sector_bytes, level)
                raw_bytes = len(body_text)
                hashes = (M.hashstr('(listfile)', 1), M.hashstr('(listfile)', 2))
            else:
                with open(file_path, 'rb') as fh:
                    data_f = fh.read()
                body, fl = mpq_rebuild.pack_file(data_f, sector_bytes, level)
                raw_bytes = len(data_f)
                if hashes is None:
                    hashes = (M.hashstr(fname, 1), M.hashstr(fname, 2))
            blocks_v.append((32 + data_bytes, len(body), raw_bytes, fl or mpq_rebuild.F_EXISTS))
            out.write(body)
            data_bytes += len(body)
            hash_entries.append((fname, hashes, len(blocks_v) - 1))
        if all_items:
            tab = [(0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFE)] * hm
            for i, (_name, (h1, h2), bi) in enumerate(hash_entries):
                tab[i] = (h1, h2, 0, bi)
            hv = [v for t in tab for v in t]
        else:
            tab = [None] * hm
            for _name, (h1, h2), bi in hash_entries:
                i0 = M.hashstr(_name, 0) & (hm - 1)
                for k in range(hm):
                    i = (i0 + k) & (hm - 1)
                    if tab[i] is None:
                        tab[i] = (h1, h2, bi)
                        break
            hv = []
            for t in tab:
                hv += [0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF] if t is None else [t[0], t[1], 0, t[2]]
        bv = [v for b in blocks_v for v in b]
        hash_pos = 32 + data_bytes
        block_pos = hash_pos + 16 * hm
        total = block_pos + 16 * len(blocks_v)
        out.write(M.encrypt(hv, M.HASH_TABLE_KEY))
        out.write(M.encrypt(bv, M.BLOCK_TABLE_KEY))
        out.seek(len(map_header))
        out.write(struct.pack('<4sIIHHIIII', MPQ_MAGIC, 32, total, 0, sector_shift, hash_pos, block_pos, hm,
                              len(blocks_v)))
    return {'file_set': len(item_entries), 'bytes': os.path.getsize(output), 'all_items': all_items,
            'index_': {n: bi for n, _h, bi in hash_entries}}


def to_map(file_path, output, name_list=(), index=True, progress=None, all_items=False):
    import tempfile
    tmp = tempfile.mkdtemp(prefix='devos_came_')
    try:
        r = extract(file_path, tmp, name_list, index, progress)
        item_entries = []
        for (fname, _size), (a, b) in zip(r['file_set'], r['pairs']):
            if fname.lower().startswith('unknown_files\\') and not all_items:
                continue
            item_entries.append((fname, (a, b), os.path.join(tmp, fname.replace('\\', os.sep))))
        if progress:
            progress('writes the map: %d files (%s)' % (
                len(item_entries), ('%d unnamed go in by hash' % r['unnamed']) if all_items
                else ('%d unnamed are left out' % r['unnamed'])))
        w = _write_map(output, item_entries, _map_header(file_path), all_items=all_items)
        b = mpqread.Archive(output)
        error_list = []
        for fname, _h, p in item_entries:
            with open(p, 'rb') as fh:
                plaintext = fh.read()
            if b.read('', bi=w['index_'][fname]) != plaintext:
                error_list.append(fname)
            elif not fname.lower().startswith('unknown_files\\') and b.read(fname) != plaintext:
                error_list.append(fname + ' (by name)')
        r.update(
            {
                'output': os.path.abspath(output),
                'arquivos_no_mapa': len(item_entries),
                'all_items': all_items,
                'error_list': error_list,
            }
        )
        return r
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

