# Compresses MPQ sectors with the best available deflate encoder (used by the shrink).
import hashlib
import os
import re
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


from doctor.mpq import mpqlib as _ML
CRYPT = _ML.CRYPT
MPQ_UPPERCASE = _ML.MPQ_UPPERCASE
hash_string = _ML.hashstr
decrypt = _ML.decrypt_bytes
encrypt = _ML.encrypt_bytes


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


class Cache:
    def __init__(self, folder):
        self.folder = folder
        self.in_use = set()

    def _path_of(self, inv_slot, hash_key):
        return os.path.join(self.folder, inv_slot, hash_key[:2], hash_key)

    def read_data(self, inv_slot, hash_key):
        if not self.folder:
            return None
        p = self._path_of(inv_slot, hash_key)
        if os.path.exists(p):
            self.in_use.add(os.path.normcase(os.path.abspath(p)))
            with open(p, 'rb') as fh:
                return fh.read()
        return None

    def save(self, inv_slot, hash_key, data_bytes):
        if not self.folder:
            return
        p = self._path_of(inv_slot, hash_key)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        tmp = p + '.tmp%d' % os.getpid()
        with open(tmp, 'wb') as fh:
            fh.write(data_bytes)
        os.replace(tmp, p)
        self.in_use.add(os.path.normcase(os.path.abspath(p)))

    def prune(self):
        if not self.folder or not os.path.isdir(self.folder):
            return 0, 0
        n = sz = 0
        for root, _, files_ in os.walk(self.folder):
            for f in files_:
                if not re.fullmatch(r'[0-9a-f]{40}', f) or os.path.basename(root) != f[:2]:
                    continue
                p = os.path.normcase(os.path.abspath(os.path.join(root, f)))
                if p not in self.in_use:
                    sz += os.path.getsize(p)
                    os.remove(p)
                    n += 1
        return n, sz


def _key(data_bytes, enc_signature):
    return hashlib.sha1(data_bytes + b'\0' + enc_signature.encode('ascii')).hexdigest()


def _blp_um(content):
    from doctor.models import blp_huffman
    return blp_huffman.otimiza_blp(content)


def _e_blp_jpeg(c):
    return len(c) > 160 and c[:8] == b'BLP1\x00\x00\x00\x00'

