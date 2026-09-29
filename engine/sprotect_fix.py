# Undoes the SProtect scrambling of the file tables.
import os
import struct
import sys


MPQ_MAGIC = b'MPQ\x1a'
HASH_TABLE_INDEX, HASH_NAME_A, HASH_NAME_B, HASH_FILE_KEY = 0, 1, 2, 3
MPQ_FILE_COMPRESS = 0x00000200
MPQ_FILE_SINGLE_UNIT = 0x01000000
MPQ_FILE_EXISTS = 0x80000000

CRYPT = []


def init_crypt():
    seed = 0x00100001
    table = [0] * 0x500
    for i in range(0x100):
        idx = i
        for _ in range(5):
            seed = (seed * 125 + 3) % 0x2AAAAB
            t1 = (seed & 0xFFFF) << 0x10
            seed = (seed * 125 + 3) % 0x2AAAAB
            t2 = seed & 0xFFFF
            table[idx] = t1 | t2
            idx += 0x100
    return table


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
    out = bytearray()
    for v in struct.unpack('<%dI' % (len(data) // 4), data[:len(data) // 4 * 4]):
        seed = (seed + CRYPT[0x400 + (key & 0xFF)]) & 0xFFFFFFFF
        ch = v ^ ((key + seed) & 0xFFFFFFFF)
        key = (((~key << 0x15) + 0x11111111) | (key >> 0x0B)) & 0xFFFFFFFF
        seed = (ch + seed + (seed << 5) + 3) & 0xFFFFFFFF
        out += struct.pack('<I', ch)
    return bytes(out)


def encrypt(data, key):
    seed = 0xEEEEEEEE
    out = bytearray()
    for ch in struct.unpack('<%dI' % (len(data) // 4), data[:len(data) // 4 * 4]):
        seed = (seed + CRYPT[0x400 + (key & 0xFF)]) & 0xFFFFFFFF
        v = ch ^ ((key + seed) & 0xFFFFFFFF)
        key = (((~key << 0x15) + 0x11111111) | (key >> 0x0B)) & 0xFFFFFFFF
        seed = (ch + seed + (seed << 5) + 3) & 0xFFFFFFFF
        out += struct.pack('<I', v)
    return bytes(out)


def find_mpq(buf):
    for off in range(0, min(len(buf) - 4, 0x1000), 0x200):
        if buf[off:off + 4] == MPQ_MAGIC:
            return off
    return None


def looks_like_sector_table(buf, pos, psize, usize, sector):
    n = (usize + sector - 1) // sector
    if n < 1 or pos + 4 > len(buf):
        return False
    first = struct.unpack_from('<I', buf, pos)[0]
    if first != (n + 1) * 4 or first > psize:
        return False
    last = struct.unpack_from('<I', buf, pos + n * 4)[0]
    return last <= psize + 64


def fix(path, out_path):
    buf = bytearray(open(path, 'rb').read())
    off = find_mpq(buf)
    if off is None:
        sys.exit('no MPQ header found (is this a .w3x?)')

    magic, hsize, asize, ver, bshift, hpos, bpos, hcount, bcount = \
        struct.unpack_from('<4sIIHHIIII', buf, off)
    print('MPQ at 0x%X' % off)
    print('  headerSize = 0x%08X (%s)' % (hsize, buf[off + 4:off + 8]))
    print('  archiveSize = 0x%08X (%s)' % (asize, buf[off + 8:off + 12]))
    print('  blockSize shift = %d, hashTablePos = %d, blockTablePos = %d' % (bshift, hpos, bpos))
    print('  hashTableSize = %d, blockTableSize = %d' % (hcount, bcount))

    if ver != 0:
        sys.exit('only MPQ version 0 (v1) is supported; this one is %d' % ver)

    sector = (0x200 << ((bshift & 0xFF) & 0x1F)) & 0xFFFFFFFF
    hkey = hash_string('(hash table)', HASH_FILE_KEY)
    bkey = hash_string('(block table)', HASH_FILE_KEY)

    htab = bytearray(decrypt(bytes(buf[off + hpos:off + hpos + hcount * 16]), hkey))
    fixed_hash = 0
    for i in range(hcount):
        n1, n2, loc, plat, bi = struct.unpack_from('<IIHHI', htab, i * 16)
        if n1 == 0xFFFFFFFF and n2 == 0xFFFFFFFF and bi == 0xFFFFFFFF:
            continue
        if bi == 0xFFFFFFFE:
            continue
        if bi >= bcount:
            bi &= 0x00FFFFFF
        if loc != 0 or plat != 0 or bi != struct.unpack_from('<I', htab, i * 16 + 12)[0]:
            fixed_hash += 1
        struct.pack_into('<IIHHI', htab, i * 16, n1, n2, 0, 0, bi)
    print('  hash entries repaired: %d' % fixed_hash)

    HEADER_V1 = 0x20
    btab_pos = bpos
    overlap = 0
    if btab_pos < HEADER_V1:
        overlap = max(0, min(HEADER_V1, btab_pos + bcount * 16) - btab_pos)
    btab = bytearray(decrypt(bytes(buf[off + btab_pos:off + btab_pos + bcount * 16]), bkey))

    fixed_block = 0
    for i in range(bcount):
        fpos, psize, usize, flags = struct.unpack_from('<4I', btab, i * 16)
        if i * 16 < overlap:
            struct.pack_into('<4I', btab, i * 16, 0, 0, 0, 0)
            continue
        if not (flags & MPQ_FILE_EXISTS) or usize == 0:
            continue
        if flags & MPQ_FILE_SINGLE_UNIT and flags & MPQ_FILE_COMPRESS:
            if looks_like_sector_table(buf, off + fpos, psize, usize, sector):
                flags &= ~MPQ_FILE_SINGLE_UNIT
                fixed_block += 1
        struct.pack_into('<4I', btab, i * 16, fpos, psize, usize, flags)
    print('  block entries repaired: %d (first %d entries blanked, they were under the header)'
          % (fixed_block, overlap // 16))

    new_bpos = len(buf) - off
    buf += encrypt(bytes(btab), bkey)
    buf[off + hpos:off + hpos + hcount * 16] = encrypt(bytes(htab), hkey)

    struct.pack_into('<4sIIHHIIII', buf, off,
                     MPQ_MAGIC, 0x20, len(buf) - off, 0, bshift,
                     hpos, new_bpos, hcount, bcount)

    if not out_path:
        base, ext = os.path.splitext(path)
        out_path = base + '_fixed' + ext
    open(out_path, 'wb').write(buf)
    print('written: %s (%d bytes)' % (out_path, len(buf)))
