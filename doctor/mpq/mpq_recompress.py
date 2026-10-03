# Compresses MPQ sectors with the best available deflate encoder (used by the shrink).
import struct
import zlib


try:
    import zopfli.zlib as _zopfli
except ImportError:
    _zopfli = None
try:
    import deflate as _libdeflate
except ImportError:
    _libdeflate = None

SECTOR_NEW = 512
SLICE = 128
CODIFICADORES = ('auto', 'zopfli', 'libdeflate', 'zlib9', 'zlib6')


def _table_crypt():
    seed = 0x00100001
    tbl = [0] * 0x500
    for i in range(0x100):
        idx = i
        for _ in range(5):
            seed = (seed * 125 + 3) % 0x2AAAAB
            t1 = (seed & 0xFFFF) << 0x10
            seed = (seed * 125 + 3) % 0x2AAAAB
            t2 = seed & 0xFFFF
            tbl[idx] = t1 | t2
            idx += 0x100
    return tbl


CRYPT = _table_crypt()


MPQ_UPPERCASE = bytes(c - 32 if 0x61 <= c <= 0x7A else (0x5C if c == 0x2F else c) for c in range(256))


def hash_string(s, htype):
    seed1, seed2 = 0x7FED7FED, 0xEEEEEEEE
    b = s if isinstance(s, (bytes, bytearray)) else s.encode('utf-8', 'surrogateescape')
    for ch in b.translate(MPQ_UPPERCASE):
        seed1 = (CRYPT[(htype << 8) + ch] ^ ((seed1 + seed2) & 0xFFFFFFFF)) & 0xFFFFFFFF
        seed2 = (ch + seed1 + seed2 + (seed2 << 5) + 3) & 0xFFFFFFFF
    return seed1


def decrypt(data, key):
    seed = 0xEEEEEEEE
    out = bytearray(len(data))
    n = len(data) // 4
    for i in range(n):
        seed = (seed + CRYPT[0x400 + (key & 0xFF)]) & 0xFFFFFFFF
        ch = struct.unpack_from('<I', data, i * 4)[0] ^ ((key + seed) & 0xFFFFFFFF)
        struct.pack_into('<I', out, i * 4, ch & 0xFFFFFFFF)
        key = (((~key << 0x15) + 0x11111111) | (key >> 0x0B)) & 0xFFFFFFFF
        seed = (ch + seed + (seed << 5) + 3) & 0xFFFFFFFF
    out[n * 4:] = data[n * 4:]
    return bytes(out)


def encrypt(data, key):
    seed = 0xEEEEEEEE
    out = bytearray(len(data))
    n = len(data) // 4
    for i in range(n):
        seed = (seed + CRYPT[0x400 + (key & 0xFF)]) & 0xFFFFFFFF
        ch = struct.unpack_from('<I', data, i * 4)[0]
        struct.pack_into('<I', out, i * 4, (ch ^ ((key + seed) & 0xFFFFFFFF)) & 0xFFFFFFFF)
        key = (((~key << 0x15) + 0x11111111) | (key >> 0x0B)) & 0xFFFFFFFF
        seed = (ch + seed + (seed << 5) + 3) & 0xFFFFFFFF
    out[n * 4:] = data[n * 4:]
    return bytes(out)


SPECIAL_FILES = ('(listfile)', '(attributes)', '(signature)')


def resolve_encoder(code_part):
    if code_part not in CODIFICADORES:
        raise SystemExit('--codificador=%s: use one of %s' % (code_part, ', '.join(CODIFICADORES)))
    if code_part == 'auto':
        code_part = 'zopfli' if _zopfli else 'libdeflate' if _libdeflate else 'zlib9'
        if code_part != 'zopfli':
            print(
                'NOTE: zopfli is not installed (pip install zopfli deflate): using %s, the map comes out bigger'
                % code_part
            )
    if code_part == 'zopfli' and not _zopfli:
        raise SystemExit('--codificador=zopfli without the zopfli package (pip install zopfli)')
    if code_part == 'libdeflate' and not _libdeflate:
        raise SystemExit('--codificador=libdeflate without the deflate package (pip install deflate)')
    return code_part


def signature(code_part, margem):
    def version_num(pkg):
        try:
            from importlib.metadata import version
            return version(pkg)
        except Exception:
            return '?'
    pieces = ['setor512/2', code_part, 'zlib=%s' % zlib.ZLIB_RUNTIME_VERSION]
    if code_part in ('zopfli', 'libdeflate'):
        pieces.append('deflate=%s' % version_num('deflate'))
    if code_part == 'zopfli':
        pieces += ['zopfli=%s' % version_num('zopfli'), 'margem=%d' % margem]
    return '|'.join(pieces)


def encode_sector(s, code_part, margem=8):
    L = len(s)
    if code_part == 'zlib6':
        z = zlib.compress(s, 6)
    else:
        z = zlib.compress(s, 9)
        if code_part in ('zopfli', 'libdeflate') and _libdeflate:
            z2 = _libdeflate.zlib_compress(s, 12)
            if len(z2) < len(z):
                z = z2
        if code_part == 'zopfli' and (margem < 0 or 1 + len(z) < L + margem):
            z3 = _zopfli.compress(s, numiterations=15, blocksplitting=False)
            if len(z3) < len(z):
                z = z3
    return b'\x02' + z if 1 + len(z) < L else s


def _slice(job):
    data_bytes, code_part, margem = job[:3]
    sector_bytes = job[3] if len(job) > 3 else SECTOR_NEW
    return [
        encode_sector(data_bytes[i : i + sector_bytes], code_part, margem)
        for i in range(0, len(data_bytes), sector_bytes)
    ]


def build_block(pieces):
    offs = []
    pos = 4 * (len(pieces) + 1)
    for p in pieces:
        offs.append(pos)
        pos += len(p)
    offs.append(pos)
    return struct.pack('<%dI' % len(offs), *offs) + b''.join(pieces)


def pack_file(content, sector_bytes=SECTOR_NEW, encoder='zlib6', margem=8):
    assert sector_bytes == SECTOR_NEW
    code_part = resolve_encoder(encoder)
    return build_block(_slice((content, code_part, margem)))


def _blp_um(content):
    from doctor.models import blp_huffman
    return blp_huffman.otimiza_blp(content)


def _e_blp_jpeg(c):
    return len(c) > 160 and c[:8] == b'BLP1\x00\x00\x00\x00'

