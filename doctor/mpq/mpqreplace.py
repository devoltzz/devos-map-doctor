# Replaces one file inside the map archive, in place when it fits, and reads it back.
import os
import struct
import zlib

from doctor.mpq import mpqlib as M
from doctor.mpq import mpqread as R


Z = 0x02


def crypt(buf, key):
    return M.encrypt_bytes(buf, key)


def build_block(data, fl, key, sec):
    fl = (fl & ~0x0000FF00) | 0x00000200
    compressed = True
    nsec = (len(data) + sec - 1) // sec
    chunks = []
    for s in range(nsec):
        part = data[s * sec:(s + 1) * sec]
        comp = zlib.compress(part, 9)
        chunks.append(b'\x02' + comp if len(comp) + 1 < len(part) else part)

    table = []
    pos = (nsec + 1) * 4
    for c in chunks:
        table.append(pos)
        pos += len(c)
    table.append(pos)
    blob = struct.pack('<%dI' % (nsec + 1), *table) + b''.join(chunks)

    if key is not None:
        head = crypt(blob[:(nsec + 1) * 4], (key - 1) & 0xFFFFFFFF)
        body = bytearray()
        for i, c in enumerate(chunks):
            body += crypt(c, (key + i) & 0xFFFFFFFF)
        blob = head + bytes(body)
    return blob, fl


def swap(map_path, fname, data_bytes, out, bi=None, hash_key=None):
    d = bytearray(open(map_path, 'rb').read())
    ar = R.Archive(map_path)
    if bi is None:
        r = ar.find(fname)
        if not r:
            raise KeyError('"%s" is not in the map' % fname)
        bi = r[1]
    else:
        r = (None, bi)
    off, cs, fs, fl = ar.blocks[bi]
    key = None
    if fl & R.FLAG_ENCRYPT:
        if fl & R.FLAG_FIXKEY:
            raise SystemExit('file encrypted with FIX_KEY: not implemented')
        if hash_key is not None:
            key = hash_key
        elif fname:
            key = M.hashstr(os.path.basename(fname.replace('/', '\\')), 3)
        else:
            raise SystemExit('block %d is encrypted and has no name: pass the key (unnamed_key)' % bi)

    blob, new_fl = build_block(data_bytes, fl, key, ar.sector_size)
    if len(blob) <= cs:
        p = (ar.h.offset + off) & 0xFFFFFFFF
        d[p:p + len(blob)] = blob
        new_off = off
        in_place = True
        leftover = cs - len(blob)
    else:
        new_off = len(d) - ar.h.offset
        d += blob
        struct.pack_into('<I', d, ar.h.offset + 0x08, len(d) - ar.h.offset)
        in_place = False
        leftover = 0

    bt = list(ar.bt)
    bt[bi * 4 + 0] = new_off
    bt[bi * 4 + 1] = len(blob)
    bt[bi * 4 + 2] = len(data_bytes)
    bt[bi * 4 + 3] = new_fl
    enc = M.encrypt(bt, M.BLOCK_TABLE_KEY)
    bp = (ar.h.offset + ar.h.block_pos) & 0xFFFFFFFF
    d[bp:bp + len(enc)] = enc
    open(out, 'wb').write(bytes(d))

    got = R.Archive(out).read(fname) if r[0] is not None else R.Archive(out).read(fname or '', bi=bi, hash_key=key)
    return {'bi': bi, 'slot': r[0], 'old_off': off, 'old_cs': cs, 'old_fs': fs, 'flags': fl,
            'new_offset': new_off, 'leftover': leftover, 'new_flags': new_fl, 'blob': len(blob),
            'in_place': in_place, 'ok': got == data_bytes}
