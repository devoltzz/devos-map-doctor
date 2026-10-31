# Reads war3map.doo and checks every doodad id against the game data.
import os
import re
import struct



_GAME_CACHE = {}


class FormatError(Exception):
    pass


def _tail_ok(tail):
    if not tail:
        return True
    if len(tail) < 8:
        return False
    _v, c = struct.unpack_from('<ii', tail, 0)
    if c < 0 or c > 1 << 20:
        return False
    return 8 + 16 * c == len(tail)


def read_data(b, skin=None):
    if b[:4] != b'W3do':
        raise FormatError('missing W3do')
    try:
        ver, sub = struct.unpack_from('<ii', b, 4)
        n = struct.unpack_from('<I', b, 12)[0]
    except struct.error:
        raise FormatError('short header (%d bytes)' % len(b))
    first = None
    for attempt in ((False, True) if skin is None else (bool(skin),)):
        try:
            regs, p = [], 16
            for _i in range(n):
                begin = p
                ident = b[p:p + 4]
                id_positions = [begin]
                p += 4 + 4 + 12 + 4 + 12
                if attempt:
                    id_positions.append(p)
                    p += 4
                if ver >= 12:
                    p += 4
                if ver >= 6:
                    p += 1
                p += 1
                if ver >= 8:
                    n_sets = struct.unpack_from('<I', b, p + 4)[0]
                    p += 8
                    if n_sets > 64:
                        raise FormatError('record %d: %d item sets' % (_i, n_sets))
                    for _k in range(n_sets):
                        k = struct.unpack_from('<I', b, p)[0]
                        if k > 64:
                            raise FormatError('record %d: %d items' % (_i, k))
                        id_positions.extend(p + 4 + 8 * j for j in range(k))
                        p += 4 + 8 * k
                if ver >= 13:
                    p += 4
                editor_id = None
                if ver >= 4:
                    editor_id = struct.unpack_from('<I', b, p)[0]
                    p += 4
                if ver >= 12:
                    p += 4 + 4
                    lights = struct.unpack_from('<I', b, p)[0]
                    p += 4
                    if lights > 64:
                        raise FormatError('record %d: %d lights' % (_i, lights))
                    p += 36 * lights
                if p > len(b):
                    raise FormatError('record %d runs past the end of the file' % _i)
                regs.append(
                    {'id': ident, 'begin': begin, 'sz': p - begin, 'editor_id': editor_id, 'id_positions': id_positions}
                )
            tail = b[p:]
            d = {'version_num': ver, 'subversion': sub, 'skin': attempt, 'regs': regs, 'tail': tail,
                 'on_close': _tail_ok(tail)}
            if d['on_close']:
                return d
            if first is None:
                first = d
        except (FormatError, struct.error):
            continue
    if first is not None:
        return first
    raise FormatError('does not fit any layout (version %d/%d)' % (ver, sub))


def ids(b, d=None):
    d = d or read_data(b)
    out = {}
    for r in d['regs']:
        out[r['id']] = out.get(r['id'], 0) + 1
    return out


SLK_TABLES = ('Doodads\\Doodads.slk', 'Units\\DestructableData.slk')
RX_ID_SLK = (re.compile(rb'K"([A-Za-z][A-Za-z0-9_]{3})"'), re.compile(rb'(?m)^([A-Za-z][A-Za-z0-9_]{3});'))


def map_ids(a, name_list=('war3map.w3d', 'war3map.w3b'), slk=SLK_TABLES):
    out = set()
    for fname in name_list:
        try:
            b = a.read(fname)
        except Exception:
            b = None
        if not b:
            continue
        for m in re.finditer(rb'[A-Za-z][A-Za-z0-9_]{3}', b):
            out.add(m.group(0))
    for fname in slk:
        try:
            b = a.read(fname)
        except Exception:
            b = None
        for rx in RX_ID_SLK if b else ():
            out.update(m.group(1) for m in rx.finditer(b))
    return out


def game_ids(game=None, hd=False, version_num=None):
    hash_key = (game, hd, version_num)
    if hash_key in _GAME_CACHE:
        return _GAME_CACHE[hash_key]
    if version_num:
        matches = set()
        try:
            from doctor.data import wc3_versions
            for fname in ('doodads\\doodads.slk', 'units\\destructabledata.slk'):
                b = wc3_versions.read(version_num, fname)
                if not b:
                    matches = set()
                    break
                for m in re.finditer(rb'K"([A-Za-z][A-Za-z0-9_]{3})"', b):
                    matches.add(m.group(1))
                for m in re.finditer(rb'(?m)^([A-Za-z][A-Za-z0-9_]{3});', b):
                    matches.add(m.group(1))
        except Exception:
            matches = set()
        if matches:
            _GAME_CACHE[hash_key] = matches
        return matches
    disk_path = _ids_file(game, hd)
    if disk_path and os.path.isfile(disk_path):
        try:
            with open(disk_path, 'rb') as f:
                matches = set(x for x in f.read().split(b'\n') if x)
            _GAME_CACHE[hash_key] = matches
            return matches
        except OSError:
            pass
    matches = set()
    try:
        from doctor.data import casc_wc3
        c = casc_wc3.CascWC3(game) if game else casc_wc3.CascWC3()
        for fname in ('doodads\\doodads.slk', 'units\\destructabledata.slk'):
            try:
                b = c.read_wc3(fname, hd=hd)
            except Exception:
                b = None
            if not b:
                matches = set()
                break
            for m in re.finditer(rb'K"([A-Za-z][A-Za-z0-9_]{3})"', b):
                matches.add(m.group(1))
            for m in re.finditer(rb'(?m)^([A-Za-z][A-Za-z0-9_]{3});', b):
                matches.add(m.group(1))
    except Exception:
        matches = set()
    if matches:
        _GAME_CACHE[hash_key] = matches
    if disk_path and matches:
        try:
            os.makedirs(os.path.dirname(disk_path), exist_ok=True)
            with open(disk_path + '.part', 'wb') as f:
                f.write(b'\n'.join(sorted(matches)))
            os.replace(disk_path + '.part', disk_path)
        except OSError:
            pass
    return matches


def _ids_file(game, hd):
    try:
        from doctor.data import casc_wc3
        import hashlib
        import tempfile
        folder = game or casc_wc3.DEFAULT_GAME
        with open(os.path.join(folder, '.build.info'), 'rb') as f:
            build = hashlib.sha1(f.read() + folder.encode('utf-8', 'replace')).hexdigest()[:16]
    except Exception:
        return None
    base = os.environ.get('DOCTOR_CACHE') or os.path.join(tempfile.gettempdir(), 'devos_map_doctor_ui')
    return os.path.join(base, 'doodad_ids_%s%s.txt' % (build + '_v2', '_hd' if hd else ''))


def invalid_ids(b, valid_ids, d=None):
    d = d or read_data(b)
    if not d.get('on_close'):
        return []
    return sorted(((k.decode('latin-1'), v) for k, v in ids(b, d).items() if k not in valid_ids),
                  key=lambda kv: -kv[1])


RENAMED_IDS = {b'NSra': b'NSr0', b'ASbl': b'ASHB', b'DTsb': b'DTs0'}


def rename_ids(b, valid_ids, d=None):
    swap = dict((v, n) for v, n in RENAMED_IDS.items() if v not in valid_ids and n in valid_ids)
    if not swap:
        return b, []
    d = d or read_data(b)
    if not d.get('on_close'):
        return b, []
    counted = [r['begin'] for r in d['regs']]
    if d['tail']:
        base = len(b) - len(d['tail'])
        counted += [base + 8 + 16 * i for i in range(struct.unpack_from('<i', d['tail'], 4)[0])]
    skins = [r['id_positions'][1] for r in d['regs'] if d['skin'] and len(r['id_positions']) > 1]
    out, done = bytearray(b), {}
    for p in counted:
        old = bytes(b[p:p + 4])
        if old in swap:
            out[p:p + 4] = swap[old]
            done[old] = done.get(old, 0) + 1
    for p in skins:
        old = bytes(b[p:p + 4])
        if old in swap:
            out[p:p + 4] = swap[old]
    return bytes(out), sorted(((k, swap[k], v) for k, v in done.items()), key=lambda x: -x[2])


DOODAD_OBJECT_FILES = ('war3map.w3d', 'war3map.w3b', 'war3mapSkin.w3d', 'war3mapSkin.w3b')


def _objects():
    try:
        from doctor.data import objects
    except ImportError:
        from doctor.data import objects
    return objects


def defined_ids(a, name_list=('war3map.w3d', 'war3map.w3b'), slk=SLK_TABLES):
    objects = _objects()
    out = set()
    for fname in name_list:
        try:
            b = a.read(fname)
        except Exception:
            b = None
        if not b:
            continue
        try:
            _v, objs, _p = objects.read_objects_bytes(b, objects.uses_levels(fname), fname=fname)
        except objects.ObjectError:
            out.update(m.group(0) for m in re.finditer(rb'[A-Za-z][A-Za-z0-9_]{3}', b))
            continue
        out.update(n.encode('latin-1') for t, _o, n, _m in objs if t == 1)
    for fname in slk:
        try:
            b = a.read(fname)
        except Exception:
            b = None
        for rx in RX_ID_SLK if b else ():
            out.update(m.group(1) for m in rx.finditer(b))
    return out


def drop_legacy(valid_ids, defined):
    return set(v for v in valid_ids if v not in RENAMED_IDS or v in defined)


def rename_parents(file_set, valid_ids, placed=()):
    swap = dict((v.decode('latin-1'), n.decode('latin-1')) for v, n in RENAMED_IDS.items()
                if v not in valid_ids and n in valid_ids)
    if not swap:
        return {}, [], []
    objects = _objects()
    placed_files = set(x.decode('latin-1') if isinstance(x, bytes) else x for x in placed)
    new_ones, done, stayed = {}, [], []
    for fname in DOODAD_OBJECT_FILES:
        d = file_set.get(fname)
        if not d:
            continue
        level = objects.uses_levels(fname)
        try:
            ver, objs, _p = objects.read_objects_bytes(d, level, fname=fname, with_end=True)
        except objects.ObjectError:
            stayed.append((fname, '*', 'the object file does not read'))
            continue
        modified_ids = set(o for t, o, _n, _m in objs if t == 0)
        output, changed = [], False
        for t, o, n, m in objs:
            if o in swap:
                if t == 0 and o not in placed_files:
                    pass
                elif t == 0 and swap[o] in modified_ids:
                    stayed.append((fname, o, 'the file also modifies %s' % swap[o]))
                elif t == 0 and swap[o] in placed_files:
                    stayed.append((fname, o, 'the map places %s' % swap[o]))
                else:
                    done.append((fname, t, o, swap[o], n.strip('\0') or o))
                    o, changed = swap[o], True
            output.append((t, o, n, m))
        if changed:
            new_ones[fname] = objects.write_objects_bytes(ver, output, level)
    return new_ones, done, stayed


def without_invalid_ids(b, valid_ids, d=None):
    d = d or read_data(b)
    if not d.get('on_close'):
        return b, []
    from doctor.data import map_formats
    try:
        t = map_formats.read_doo(b)
    except map_formats.Unreadable:
        return b, []
    bad_ones = {}

    def keep(tab, i):
        ident = bytes(tab.records[i][:4])
        if ident in valid_ids:
            return True
        bad_ones[ident] = bad_ones.get(ident, 0) + 1
        return False

    t.remove(keep)
    if not bad_ones:
        return b, []
    return t.write(), sorted(bad_ones.items(), key=lambda kv: -kv[1])
