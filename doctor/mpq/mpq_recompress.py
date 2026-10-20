# Compresses MPQ sectors with the best available deflate encoder (used by the shrink).
import hashlib
import os
import re
import struct
import sys
import time
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


_NATIVE_SOUND = [None]


def _native_codec(code_part):
    if code_part not in ('zopfli', 'zlib9') or _libdeflate is not None:
        return None
    if _zopfli is not None and 'zlib-ng' in zlib.ZLIB_RUNTIME_VERSION:
        return None
    if _NATIVE_SOUND[0] is None or sys.platform == 'emscripten':
        try:
            from doctor.mpq import sector512_native
            _NATIVE_SOUND[0] = sector512_native.load_data() or False
        except Exception:
            _NATIVE_SOUND[0] = False
    return _NATIVE_SOUND[0] or None


def resolve_encoder(code_part):
    if code_part not in CODIFICADORES:
        raise SystemExit('--codificador=%s: use one of %s' % (code_part, ', '.join(CODIFICADORES)))
    if code_part == 'auto':
        code_part = 'zopfli' if (_zopfli or _native_codec('zopfli')) else 'libdeflate' if _libdeflate else 'zlib9'
        if code_part != 'zopfli':
            print(
                'NOTE: zopfli is not installed (pip install zopfli deflate): using %s, the map comes out bigger'
                % code_part
            )
    if code_part == 'zopfli' and not (_zopfli or _native_codec('zopfli')):
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
    if _native_codec(code_part):
        from doctor.mpq import sector512_native
        return '|'.join(['setor512/2', code_part, 'native', sector512_native.VERSION] +
                        (['margem=%d' % margem] if code_part == 'zopfli' else []))
    pieces = ['setor512/2', code_part, 'zlib=%s' % zlib.ZLIB_RUNTIME_VERSION]
    if code_part in ('zopfli', 'libdeflate'):
        pieces.append('deflate=%s' % version_num('deflate'))
    if code_part == 'zopfli':
        pieces += ['zopfli=%s' % version_num('zopfli'), 'margem=%d' % margem]
    return '|'.join(pieces)


def encode_sector(s, code_part, margem=8):
    L = len(s)
    nat = _native_codec(code_part) if L else None
    if nat:
        r = nat(s, L, margem, code_part)
        if r is not None:
            return r[0]
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
    nat = _native_codec(code_part)
    if nat:
        r = nat(data_bytes, sector_bytes, margem, code_part)
        if r is not None:
            return r
    return [
        encode_sector(data_bytes[i : i + sector_bytes], code_part, margem)
        for i in range(0, len(data_bytes), sector_bytes)
    ]


class _Threads:
    def __init__(self, n):
        from concurrent.futures import ThreadPoolExecutor
        self.ex = ThreadPoolExecutor(n)

    def imap(self, fn, item_entries, chunksize=1):
        return self.ex.map(fn, item_entries)

    imap_unordered = imap

    def close(self):
        self.ex.shutdown(wait=True)

    def join(self):
        pass


def open_pool(n):
    if n <= 1 or sys.platform == 'emscripten':
        return None
    if getattr(sys, 'frozen', False):
        return _Threads(n)
    import multiprocessing as mp
    return mp.Pool(n)


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

    ATTEMPTS = 5

    def read_data(self, inv_slot, hash_key):
        if not self.folder:
            return None
        p = self._path_of(inv_slot, hash_key)
        for k in range(self.ATTEMPTS):
            if not os.path.exists(p):
                return None
            try:
                with open(p, 'rb') as fh:
                    data_bytes = fh.read()
            except PermissionError:
                time.sleep(0.02 * (k + 1))
                continue
            self.in_use.add(os.path.normcase(os.path.abspath(p)))
            return data_bytes
        return None

    def save(self, inv_slot, hash_key, data_bytes):
        if not self.folder:
            return
        p = self._path_of(inv_slot, hash_key)
        mark = os.path.normcase(os.path.abspath(p))
        if os.path.isfile(p):
            self.in_use.add(mark)
            return
        os.makedirs(os.path.dirname(p), exist_ok=True)
        tmp = p + '.tmp%d' % os.getpid()
        with open(tmp, 'wb') as fh:
            fh.write(data_bytes)
        for k in range(self.ATTEMPTS):
            try:
                os.replace(tmp, p)
                break
            except PermissionError:
                if os.path.isfile(p):
                    try:
                        os.remove(tmp)
                    except OSError:
                        pass
                    break
                if k == self.ATTEMPTS - 1:
                    raise
                time.sleep(0.02 * (k + 1))
        self.in_use.add(mark)

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

