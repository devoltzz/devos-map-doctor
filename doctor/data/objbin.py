# Reads Warcraft III object data files.
import io
import os
import struct


WITH_LEVELS = ('war3map.w3a', 'war3map.w3d', 'war3map.w3q', 'war3mapskin.w3a', 'war3mapskin.w3d', 'war3mapskin.w3q')


_U = struct.Struct('<I').unpack_from
_UU = struct.Struct('<II').unpack_from
_CT = struct.Struct('<4sI').unpack_from


def read_data(data, has_levels):
    try:
        return _read_fast(data, has_levels)
    except Exception:
        return _read_slow(data, has_levels)


def _read_fast(data, has_levels):
    u, uu, ct = _U, _UU, _CT
    idx = data.index
    ver = u(data, 0)[0]
    p = 4
    tables = []
    for _ in range(2):
        cnt = u(data, p)[0]
        p += 4
        objs = []
        for _ in range(cnt):
            old, new = data[p:p + 4], data[p + 4:p + 8]
            p += 8
            item_sets = 1
            if ver >= 3:
                item_sets = u(data, p)[0]
                p += 4
            mods = []
            ap = mods.append
            for _ in range(item_sets):
                if ver >= 3:
                    p += 4
                nm = u(data, p)[0]
                p += 4
                for _ in range(nm):
                    mid, vt = ct(data, p)
                    p += 8
                    lvl = dptr = None
                    if has_levels:
                        lvl, dptr = uu(data, p)
                        p += 8
                    if vt == 3:
                        e = idx(b'\0', p)
                        val = data[p:e]
                        p = e + 1
                    elif vt == 0 or vt == 1 or vt == 2:
                        val = data[p:p + 4]
                        p += 4
                    else:
                        raise ValueError(vt)
                    p += 4
                    ap((mid.decode('latin1'), vt, lvl, dptr, val))
            objs.append((old.decode('latin1'), new.decode('latin1'), mods))
        tables.append(objs)
    return ver, tables, p


def _read_slow(data, has_levels):
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
                        if vt == 3:
                            if b'\0' in other_value:
                                raise ValueError('field %r: the new text cannot hold a NUL character' % mid)
                        elif len(other_value) != v_end - v_start:
                            raise ValueError('field %r: the new value must keep its %d bytes' % (mid, v_end - v_start))
                        output.append(data[begin:v_start])
                        output.append(other_value)
                        output.append(data[v_end:p])
                        replacements += 1
                    else:
                        output.append(data[begin:p])
    output.append(data[p:])
    return b''.join(output), replacements


def add_levels(data, has_levels, objects):
    ver, tabs, end_pos = read_data(data, has_levels)
    existing_ones = {o[1] for t in tabs for o in t}
    p = _end_of_table(data, has_levels, ver, 4)
    n = struct.unpack_from('<I', data, p)[0]
    body = []
    for base, new_id, mods in objects:
        if new_id in existing_ones:
            raise ValueError('object %r already exists' % new_id)
        existing_ones.add(new_id)
        b = [base.encode('latin1'), new_id.encode('latin1')]
        if ver >= 3:
            b.append(struct.pack('<II', 1, 0))
        b.append(struct.pack('<I', len(mods)))
        for m in mods:
            field_id, kind, field_value = m[:3]
            b.append(field_id.encode('latin1') + struct.pack('<I', kind))
            if has_levels:
                b.append(struct.pack('<II', m[3] if len(m) > 3 else 0, m[4] if len(m) > 4 else 0))
            if kind == 3:
                v = field_value.encode('utf-8') if isinstance(field_value, str) else field_value
                if b'\0' in v:
                    raise ValueError('field %r: text with a NUL' % field_id)
                b.append(v + b'\0')
            else:
                if len(field_value) != 4:
                    raise ValueError('field %r: the value needs 4 bytes' % field_id)
                b.append(field_value)
            b.append(b'\0\0\0\0')
        body.append(b''.join(b))
    output = data[:p] + struct.pack('<I', n + len(objects)) + data[p + 4:end_pos] + b''.join(body) + data[end_pos:]
    v2, t2, _ = read_data(output, has_levels)
    if [o[1] for o in t2[1][-len(objects):]] != [o[1] for o in objects] or len(t2[0]) != len(tabs[0]):
        raise ValueError('the file with the new objects does not read back the same')
    return output


def _end_of_table(data, has_levels, ver, p):
    cnt = struct.unpack_from('<I', data, p)[0]
    p += 4
    for _ in range(cnt):
        p += 8
        item_sets = 1
        if ver >= 3:
            item_sets = struct.unpack_from('<I', data, p)[0]
            p += 4
        for _ in range(item_sets):
            if ver >= 3:
                p += 4
            nm = struct.unpack_from('<I', data, p)[0]
            p += 4
            for _ in range(nm):
                vt = struct.unpack_from('<I', data, p + 4)[0]
                p += 8 + (8 if has_levels else 0)
                p = data.index(b'\0', p) + 1 if vt == 3 else p + 4
                p += 4
    return p


def load_data(p):
    data = io.open(p, 'rb').read()
    has = os.path.basename(p).lower() in WITH_LEVELS
    ver, tabs, consumed = read_data(data, has)
    return ver, tabs, consumed, len(data), has
