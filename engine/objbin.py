# Reads Warcraft III object data files.
import io
import os
import struct


WITH_LEVELS = ('war3map.w3a', 'war3map.w3d', 'war3map.w3q')


def read_data(data, has_levels):
    ver = struct.unpack_from('<I', data, 0)[0]
    p = 4
    tables = []
    for _ in range(2):
        cnt = struct.unpack_from('<I', data, p)[0]
        p += 4
        objs = []
        for _ in range(cnt):
            old, new, nm = data[p:p + 4], data[p + 4:p + 8], struct.unpack_from('<I', data, p + 8)[0]
            p += 12
            mods = []
            for _ in range(nm):
                mid, vt = data[p:p + 4], struct.unpack_from('<I', data, p + 4)[0]
                p += 8
                lvl = dptr = None
                if has_levels:
                    lvl, dptr = struct.unpack_from('<II', data, p)
                    p += 8
                if vt == 3:
                    e = data.index(b'\0', p)
                    val = data[p:e]
                    p = e + 1
                elif vt in (0, 1, 2):
                    val = data[p:p + 4]
                    p += 4
                else:
                    raise ValueError('unknown type %d in field %r' % (vt, mid))
                p += 4
                mods.append((mid.decode('latin1'), vt, lvl, dptr, val))
            objs.append((old.decode('latin1'), new.decode('latin1'), mods))
        tables.append(objs)
    return ver, tables, p


def load_data(p):
    data = io.open(p, 'rb').read()
    has = os.path.basename(p).lower() in WITH_LEVELS
    ver, tabs, consumed = read_data(data, has)
    return ver, tabs, consumed, len(data), has
