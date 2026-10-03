# Moves the model fields of the object files to the skin files, as the World Editor 3.0 saves them.
import collections
import struct


MOVE = {'w3u': ('umdl',), 'w3t': ('ifil',)}
LEVELS = ('w3a', 'w3d', 'w3q')


def _mods(d, p, n, levels):
    out = []
    for _ in range(n):
        start = p
        field, kind = d[p:p + 4].decode('latin-1'), struct.unpack_from('<I', d, p + 4)[0]
        p += 16 if levels else 8
        if kind == 3:
            p = d.index(b'\0', p) + 1
        elif kind in (0, 1, 2):
            p += 4
        else:
            raise ValueError('value type %d in field %r' % (kind, field))
        p += 4
        out.append((field, start, p))
    return out, p


def _parse(d, levels):
    version = struct.unpack_from('<I', d, 0)[0]
    p, objects = 4, []
    for table in (0, 1):
        count = struct.unpack_from('<I', d, p)[0]
        p += 4
        for _ in range(count):
            ids, p = d[p:p + 8], p + 8
            sets = []
            if version >= 3:
                n_sets = struct.unpack_from('<I', d, p)[0]
                p += 4
                for _s in range(n_sets):
                    flag, n = struct.unpack_from('<II', d, p)
                    mods, p = _mods(d, p + 8, n, levels)
                    sets.append((flag, mods))
            else:
                n = struct.unpack_from('<I', d, p)[0]
                mods, p = _mods(d, p + 4, n, levels)
                sets.append((None, mods))
            objects.append((table, ids, sets))
    return version, objects, p


def _write(version, objects, d, keep):
    out = [struct.pack('<I', version)]
    for table in (0, 1):
        group = [o for o in objects if o[0] == table]
        out.append(struct.pack('<I', len(group)))
        for _t, ids, sets in group:
            out.append(ids)
            if version >= 3:
                out.append(struct.pack('<I', len(sets)))
            for flag, mods in sets:
                kept = [(s, e) for f, s, e in mods if keep(f)]
                if version >= 3:
                    out.append(struct.pack('<I', flag))
                out.append(struct.pack('<I', len(kept)))
                out.extend(d[s:e] for s, e in kept)
    return b''.join(out)


def _skin(objects, d, fields):
    out = [struct.pack('<I', 3)]
    for table in (0, 1):
        rows = []
        for t, ids, sets in objects:
            if t != table:
                continue
            by_flag = collections.OrderedDict()
            for flag, mods in sets:
                moved = [(s, e) for f, s, e in mods if f in fields]
                if moved:
                    by_flag.setdefault(flag or 0, []).extend(moved)
            if by_flag:
                rows.append((ids, by_flag))
        out.append(struct.pack('<I', len(rows)))
        for ids, by_flag in rows:
            out.append(ids + struct.pack('<I', len(by_flag)))
            for flag, moved in by_flag.items():
                out.append(struct.pack('<II', flag, len(moved)))
                out.extend(d[s:e] for s, e in moved)
    return b''.join(out)


def _content(data, levels):
    from doctor.data import objbin
    _v, tables, end = objbin.read_data(data, levels)
    if end != len(data):
        raise ValueError('the file does not close (%d of %d bytes)' % (end, len(data)))
    out = collections.defaultdict(collections.Counter)
    for rows in tables:
        for old, new, mods in rows:
            out[old + new].update((m[0], m[2], m[4]) for m in mods)
    return out


def split(files):
    out = {}
    for ext, fields in MOVE.items():
        classic, skin = 'war3map.' + ext, 'war3mapSkin.' + ext
        d = files.get(classic)
        if not d or files.get(skin) is not None:
            continue
        levels = ext in LEVELS
        try:
            version, objects, end = _parse(d, levels)
        except (ValueError, IndexError, struct.error):
            continue
        if end != len(d) or not any(
            f in fields for _t, _i, sets in objects for _fl, mods in sets for f, _s, _e in mods
        ):
            continue
        new_classic = _write(version, objects, d, lambda f: f not in fields)
        new_skin = _skin(objects, d, fields)
        try:
            before = _content(d, levels)
            after = _content(new_classic, levels)
            for ids, c in _content(new_skin, levels).items():
                after[ids].update(c)
        except (ValueError, IndexError, struct.error):
            continue
        if before != after:
            continue
        out[classic], out[skin] = new_classic, new_skin
    return out
