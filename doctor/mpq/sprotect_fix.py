# Undoes the SProtect scrambling of the file tables.
import os
import struct
import sys

from doctor.mpq import mpqlib as _ML

MPQ_MAGIC = b'MPQ\x1a'
HASH_TABLE_INDEX, HASH_NAME_A, HASH_NAME_B, HASH_FILE_KEY = 0, 1, 2, 3
MPQ_FILE_COMPRESS = 0x00000200
MPQ_FILE_SINGLE_UNIT = 0x01000000
MPQ_FILE_EXISTS = 0x80000000
CRYPT = _ML.CRYPT
MPQ_UPPERCASE = _ML.MPQ_UPPERCASE
hash_string = _ML.hashstr
decrypt = _ML.decrypt_bytes
encrypt = _ML.encrypt_bytes


def init_crypt():
    return _ML.CRYPT


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
