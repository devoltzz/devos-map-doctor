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
    ver, sub = struct.unpack_from('<ii', b, 4)
    n = struct.unpack_from('<I', b, 12)[0]
    first = None
    for attempt in ((False, True) if skin is None else (bool(skin),)):
        try:
            regs, p = [], 16
            for _i in range(n):
                begin = p
                ident = b[p:p + 4]
                p += 4 + 4 + 12 + 4 + 12
                if attempt:
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
                regs.append({'id': ident, 'begin': begin, 'sz': p - begin, 'editor_id': editor_id})
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


def game_ids(game=None, hd=False):
    hash_key = (game, hd)
    if hash_key in _GAME_CACHE:
        return _GAME_CACHE[hash_key]
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
                continue
            for m in re.finditer(rb'K"([A-Za-z][A-Za-z0-9_]{3})"', b):
                matches.add(m.group(1))
            for m in re.finditer(rb'(?m)^([A-Za-z][A-Za-z0-9_]{3});', b):
                matches.add(m.group(1))
    except Exception:
        matches = set()
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
    return os.path.join(base, 'doodad_ids_%s%s.txt' % (build, '_hd' if hd else ''))


def invalid_ids(b, valid_ids, d=None):
    d = d or read_data(b)
    if not d.get('on_close'):
        return []
    return sorted(((k.decode('latin-1'), v) for k, v in ids(b, d).items() if k not in valid_ids),
                  key=lambda kv: -kv[1])


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
