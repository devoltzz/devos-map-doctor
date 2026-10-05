# Reads Warcraft III object data files.
import io
import os
import struct


WITH_LEVELS = ('war3map.w3a', 'war3map.w3d', 'war3map.w3q', 'war3mapskin.w3a', 'war3mapskin.w3d', 'war3mapskin.w3q')


def read_data(data, has_levels):
    ver = struct.unpack_from('<I', data, 0)[0]
    p = 4
    tables = []
    for _ in range(2):
        cnt = struct.unpack_from('<I', data, p)[0]
        p += 4
        objs = []
        for _ in range(cnt):
            old, new = data[p:p + 4], data[p + 4:p + 8]
            p += 8
            item_sets = 1
            if ver >= 3:
                item_sets = struct.unpack_from('<I', data, p)[0]
                p += 4
            mods = []
            for _ in range(item_sets):
                if ver >= 3:
                    p += 4
                nm = struct.unpack_from('<I', data, p)[0]
                p += 4
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


def rewrite(data, has_levels, change):
    ver = struct.unpack_from('<I', data, 0)[0]
    p = 4
    output, replacements = [data[:4]], 0
    for ti in range(2):
        cnt = struct.unpack_from('<I', data, p)[0]
        output.append(data[p:p + 4])
        p += 4
        for oi in range(cnt):
            item_sets = struct.unpack_from('<I', data, p + 8)[0] if ver >= 3 else 1
            output.append(data[p:p + (12 if ver >= 3 else 8)])
            p += 12 if ver >= 3 else 8
            mi = 0
            for _ in range(item_sets):
                begin = p
                if ver >= 3:
                    p += 4
                nm = struct.unpack_from('<I', data, p)[0]
                p += 4
                output.append(data[begin:p])
                for _ in range(nm):
                    begin = p
                    mid = data[p:p + 4].decode('latin1')
                    vt = struct.unpack_from('<I', data, p + 4)[0]
                    p += 8
                    if has_levels:
                        p += 8
                    if vt == 3:
                        e = data.index(b'\0', p)
                        v_start, v_end = p, e
                        p = e + 1
                    elif vt in (0, 1, 2):
                        v_start, v_end = p, p + 4
                        p += 4
                    else:
                        raise ValueError('unknown type %d in field %r' % (vt, mid))
                    p += 4
                    other_value = change(ti, oi, mi, mid, data[v_start:v_end])
                    mi += 1
                    if other_value is not None:
                        output.append(data[begin:v_start])
                        output.append(other_value)
                        output.append(data[v_end:p])
                        replacements += 1
                    else:
                        output.append(data[begin:p])
    output.append(data[p:])
    return b''.join(output), replacements


def load_data(p):
    data = io.open(p, 'rb').read()
    has = os.path.basename(p).lower() in WITH_LEVELS
    ver, tabs, consumed = read_data(data, has)
    return ver, tabs, consumed, len(data), has
