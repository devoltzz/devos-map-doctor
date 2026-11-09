# The encrypted game.pkg of xmload maps: decrypted and unpacked with what the map ships.
import hashlib
import io
import os
import struct



SALT = b'XMP[G-lz4-sodium-key-2026-xmlap\0'
BLX_SEED = 0x24125689
_SIGMA = b'expand 32-byte k'
_P1305 = (1 << 130) - 5


LOADER_FILES = ('luahelper.tga', 'xm.key', 'xmload.lua', 'war3map.jx')


class PackError(Exception):
    pass


def _rotl(x, n):
    return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF


def hsalsa20(key, inp):
    x = list(struct.unpack('<16I', _SIGMA[:4] + key[:16] + _SIGMA[4:8] + inp + _SIGMA[8:12] + key[16:]
                           + _SIGMA[12:]))
    for _ in range(10):
        for group in (((0, 4, 8, 12), (5, 9, 13, 1), (10, 14, 2, 6), (15, 3, 7, 11)),
                      ((0, 1, 2, 3), (5, 6, 7, 4), (10, 11, 8, 9), (15, 12, 13, 14))):
            for a, b, c, d in group:
                x[b] ^= _rotl((x[a] + x[d]) & 0xFFFFFFFF, 7)
                x[c] ^= _rotl((x[b] + x[a]) & 0xFFFFFFFF, 9)
                x[d] ^= _rotl((x[c] + x[b]) & 0xFFFFFFFF, 13)
                x[a] ^= _rotl((x[d] + x[c]) & 0xFFFFFFFF, 18)
    return struct.pack('<8I', x[0], x[5], x[10], x[15], x[6], x[7], x[8], x[9])


def poly1305(key, msg):
    r = int.from_bytes(key[:16], 'little') & 0x0FFFFFFC0FFFFFFC0FFFFFFC0FFFFFFF
    s = int.from_bytes(key[16:], 'little')
    h = 0
    for i in range(0, len(msg), 16):
        h = (h + int.from_bytes(msg[i:i + 16] + b'\x01', 'little')) * r % _P1305
    return ((h + s) & ((1 << 128) - 1)).to_bytes(16, 'little')


def open_secretbox(key, nonce, box):
    from Crypto.Cipher import Salsa20
    if len(box) < 16:
        raise PackError('box of %d B' % len(box))
    tag, cipher = box[:16], box[16:]
    stream = Salsa20.new(key=hsalsa20(key, nonce[:16]), nonce=nonce[16:24])
    mac_key = stream.encrypt(bytes(32))
    if poly1305(mac_key, cipher) != tag:
        raise PackError('wrong Poly1305 tag')
    return stream.decrypt(cipher)


def lz4_block(src, size):
    out = bytearray()
    i, n = 0, len(src)
    try:
        while i < n:
            token = src[i]
            i += 1
            lit = token >> 4
            if lit == 15:
                while True:
                    b = src[i]
                    i += 1
                    lit += b
                    if b != 255:
                        break
            out += src[i:i + lit]
            i += lit
            if i >= n:
                break
            dist = src[i] | src[i + 1] << 8
            i += 2
            match = token & 15
            if match == 15:
                while True:
                    b = src[i]
                    i += 1
                    match += b
                    if b != 255:
                        break
            match += 4
            if dist == 0 or dist > len(out) or len(out) + match > size:
                raise PackError('LZ4: copy outside the block')
            start = len(out) - dist
            if dist >= match:
                out += out[start:start + match]
            else:
                piece = bytes(out[start:])
                out += (piece * (match // dist + 1))[:match]
    except IndexError:
        raise PackError('LZ4: truncated block')
    if len(out) != size:
        raise PackError('LZ4: %d B instead of %d' % (len(out), size))
    return bytes(out)


def undo_blx(data):
    import numpy as np
    n = (len(data) - 4) >> 2
    cipher = np.frombuffer(data, dtype='<u4', count=n, offset=4)
    turns = np.arange(n, dtype=np.uint32) * 2 % 32
    seed = np.uint32((len(data) ^ BLX_SEED) & 0xFFFFFFFF)
    keys_ = np.where(turns == 0, seed, (seed << turns) | (seed >> ((32 - turns) % 32)))
    plain = np.bitwise_xor.accumulate(cipher ^ keys_)
    out = plain.astype('<u4').tobytes()
    tail = data[4 + n * 4:]
    if tail:
        last = int(plain[-1]) if n else 0
        key = _rotl_n(int(seed), 2 * n % 32)
        word = int.from_bytes(tail + bytes(4 - len(tail)), 'little') ^ last ^ key
        out += word.to_bytes(4, 'little')[:len(tail)]
    return b'BLP1' + out


def _rotl_n(x, n):
    return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF if n else x


def keys(script_jx):
    k0 = hashlib.sha256(script_jx).digest()
    return hashlib.sha256(SALT + k0 + b'idx').digest()[:16], hashlib.sha256(SALT + k0 + b'dat').digest()


def read_index(head, index_key):
    from Crypto.Cipher import AES
    if len(head) < 36:
        raise PackError('game.pkg is too short')
    nonce, length = head[:12], struct.unpack_from('<Q', head, 12)[0]
    if length < 24 or 20 + length > len(head):
        raise PackError('the index size (%d) does not fit in the file' % length)
    block = head[20:20 + length]
    try:
        plain = AES.new(index_key, AES.MODE_GCM, nonce=nonce).decrypt_and_verify(block[:-16], block[-16:])
    except ValueError:
        raise PackError('the index tag does not verify: another salt, another war3map.jx or a game.pem in the map')
    count = struct.unpack_from('<Q', plain, 0)[0]
    p, items = 8, []
    try:
        for _ in range(count):
            n = struct.unpack_from('<I', plain, p)[0]
            name = plain[p + 4:p + 4 + n]
            p += 4 + n
            usize, csize, disk, offset, flags = struct.unpack_from('<5I', plain, p)
            item_nonce = plain[p + 20:p + 44]
            p += 44
            items.append((name, usize, csize, disk, offset, flags, item_nonce))
    except struct.error:
        raise PackError('the index ends before its %d entries' % count)
    if p != len(plain):
        raise PackError('%d B left in the index' % (len(plain) - p))
    return items


def open_item(stream_in, entry, data_key):
    name, usize, _csize, disk, offset, flags, nonce = entry
    stream_in.seek(offset)
    box = stream_in.read(disk)
    if len(box) != disk:
        raise PackError('%r: truncated' % name)
    plain = open_secretbox(data_key, nonce, box)
    data = lz4_block(plain, usize) if flags & 1 else plain
    if len(data) != usize:
        raise PackError('%r: %d B instead of %d' % (name, len(data), usize))
    if data[:4] == b'LuaC':
        return open_luac(data)
    if data[:4] == b'BLX1':
        return undo_blx(data)
    if data[:4] == b'MDB3':
        from doctor.mpq import xm_mdb3
        try:
            return xm_mdb3.convert(data)
        except (xm_mdb3.Mdb3Error, struct.error):
            return data
    return data


def xxtea_decrypt(data, key):
    k = struct.unpack('<4I', key.ljust(16, b'\0')[:16])
    n = len(data) // 4
    if n < 2:
        raise PackError('XXTEA: too short')
    v = list(struct.unpack('<%dI' % n, data[:n * 4]))
    last, mask, delta = n - 1, 0xFFFFFFFF, 0x9E3779B9
    total = ((6 + 52 // n) * delta) & mask
    y = v[0]
    while total:
        e = (total >> 2) & 3
        for x in range(last, 0, -1):
            z = v[x - 1]
            y = v[x] = (
                v[x] - ((((z >> 5) ^ (y << 2)) + ((y >> 3) ^ (z << 4))) ^ ((total ^ y) + (k[(x & 3) ^ e] ^ z)))
            ) & mask
        z = v[last]
        y = v[0] = (v[0] - ((((z >> 5) ^ (y << 2)) + ((y >> 3) ^ (z << 4))) ^ ((total ^ y) + (k[e] ^ z)))) & mask
        total = (total - delta) & mask
    plain = struct.pack('<%dI' % n, *v)
    size = v[last]
    if not 0 <= size <= last * 4:
        raise PackError('XXTEA: wrong key')
    return plain[:size]


def xxtea_keys(dll):
    import re

    marks = [
        (m.group(1) or m.group(2))[0] if m.group(1) or m.group(2) else 0
        for m in re.finditer(rb'\x34(.)|\x80\xf3(.)', dll, re.S)
    ]
    first = [m.group(2) is not None for m in re.finditer(rb'\x34(.)|\x80\xf3(.)', dll, re.S)]
    values = bytes(marks)
    out = []
    for at in [m.start() for m in re.finditer(b'XMPKG', values)]:
        for i in range(at + 5, min(at + 405, len(values) - 16)):
            word = values[i:i + 16]
            if first[i] and not any(first[i + 1:i + 16]) and word.isalnum() and word not in out:
                out.append(word)
    return out


def xmpkg_zip(package, dll):
    import zipfile
    for key in xxtea_keys(dll or b''):
        try:
            plain = xxtea_decrypt(package[5:], key)
        except PackError:
            continue
        if plain[:4] == b'PK\x03\x04':
            return zipfile.ZipFile(io.BytesIO(plain))
    raise PackError('XMPKG: no key of the DLL opens it')


def entries(archive):
    package = archive.read('game.pkg')
    if package[:5] == b'XMPKG':
        z = xmpkg_zip(package, archive.read('luahelper.tga') if archive.find('luahelper.tga') else None)
        return [(i.filename.replace('/', chr(92)), z.read(i)) for i in z.infolist() if not i.is_dir()]
    index_key, data_key = keys(archive.read('war3map.jx'))
    stream = io.BytesIO(package)
    return [(item[0].decode('utf-8', 'surrogateescape').replace('/', chr(92)), open_item(stream, item, data_key))
            for item in read_index(package, index_key)]


def open_luac(data):
    from Crypto.Cipher import ChaCha20_Poly1305
    inner = hashlib.blake2b(b'XMLua', digest_size=32).digest()
    key = hashlib.blake2b(b'XMData', digest_size=32, key=inner).digest()
    try:
        return ChaCha20_Poly1305.new(key=key, nonce=data[4:16]).decrypt_and_verify(data[16:-16], data[-16:])
    except ValueError:
        raise PackError('LuaC: wrong tag')


def safe_path(folder, name):
    text = name.decode('utf-8', 'replace').replace('\\', '/')
    parts = [p for p in text.split('/') if p not in ('', '.')]
    if not parts or '..' in parts or any(':' in p or any(ord(c) < 32 or c in '<>"|?*' for c in p) for p in parts):
        raise PackError('unsafe name in the package: %r' % name)
    return os.path.join(folder, *parts)


def extract(map_path, folder=None, log=print):
    import collections
    from doctor.mpq import mpqread
    a = mpqread.Archive(map_path)
    if not opens(a):
        raise PackError('the map has no war3map.jx and game.pkg this reads')
    items = entries(a)
    r = {'files': len(items), 'bytes': sum(len(d) for _n, d in items), 'by_signature': collections.Counter(),
         'by_type': collections.Counter(os.path.splitext(n)[1].lower() for n, _d in items)}
    if folder is None:
        return r
    for k, (name, data) in enumerate(items):
        dest = safe_path(folder, name.encode('utf-8', 'surrogateescape'))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, 'wb') as s:
            s.write(data)
        r['by_signature'][data[:4]] += 1
        if k and k % 500 == 0:
            log('   %d/%d' % (k, len(items)))
    return r


def opens(archive):
    try:
        if not archive.find('war3map.jx') or not archive.find('game.pkg'):
            return False
        package = archive.read('game.pkg')
        if package[:5] == b'XMPKG':
            return bool(archive.find('luahelper.tga')) and xmpkg_zip(package, archive.read('luahelper.tga')) is not None
        read_index(package, keys(archive.read('war3map.jx'))[0])
        return True
    except (PackError, struct.error):
        return False


def unpack_to_map(map_path, out, keep_package=False, log=print, real_script=False):
    import io
    from doctor.mpq import mpq_rebuild
    from doctor.mpq import mpqread
    a = mpqread.Archive(map_path)
    if not opens(a):
        raise PackError('the map has no war3map.jx and game.pkg this reads')
    items = entries(a)
    added, replaced = {}, {}
    for name, data in items:
        (replaced if a.find(name) else added)[name] = data
    removed = () if keep_package else ('game.pkg',)
    slots = a.hash_n
    factor = 1
    while slots * factor < 2 * (len(added) + len(replaced) + a.block_n):
        factor *= 2
    mpq_rebuild.rebuild(map_path, out, [], replaced, added, removed, log=lambda s: None, hash_factor=factor)
    b = mpqread.Archive(out)
    for name, data in list(replaced.items()) + list(added.items()):
        if b.read(name) != data:
            raise PackError('%s did not read back equal' % name)
    if bool(b.find('game.pkg')) != bool(keep_package):
        raise PackError('game.pkg is not as requested')
    script = None
    if real_script and not keep_package:
        from doctor.mpq import mpqadd
        from doctor.mpq import xm_jx
        script = xm_jx.map_script(a.read('war3map.jx'), a.read('war3map.j'))
        mpqadd.add_files(
            out, [('war3map.j', script)], to_delete=[n for n in LOADER_FILES if b.find(n)], log=lambda s: None
        )
    return {'files': len(items), 'replaced': len(replaced), 'added': len(added), 'package_kept': bool(keep_package),
            'bytes': os.path.getsize(out), 'real_script': len(script) if script else 0}

