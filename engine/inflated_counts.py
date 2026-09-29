# Finds and fixes inflated record counters in the files only the World Editor reads.
import os
import re
import struct



DOES_NOT_FIT = 'does_not_fit'
SHORT_READ = 'short_read'
EMPTY = 'empty'
ODD_VERSION = 'odd_version'

FILES = ('war3map.w3r', 'war3map.w3c', 'war3map.w3s', 'war3mapUnits.doo', 'war3map.wtg', 'war3map.wct',
         'war3map.imp', 'war3map.mmp')
REPORTED_ONLY = ('war3map.doo', 'war3map.w3e', 'war3map.w3i')
NO_REWRITE = ('war3map.wtg', 'war3mapUnits.doo')


class End(Exception):
    pass


class FormatError(Exception):
    pass


class Reader(object):
    def __init__(self, b, o=0):
        self.b, self.o = b, o

    def remaining(self):
        return len(self.b) - self.o

    def _require(self, n):
        if self.remaining() < n:
            raise End('%d B missing' % (n - self.remaining()))

    def i32(self):
        self._require(4)
        v = struct.unpack_from('<i', self.b, self.o)[0]
        self.o += 4
        return v

    def u32(self):
        self._require(4)
        v = struct.unpack_from('<I', self.b, self.o)[0]
        self.o += 4
        return v

    def f32(self):
        self._require(4)
        v = struct.unpack_from('<f', self.b, self.o)[0]
        self.o += 4
        return v

    def bs(self, n):
        self._require(n)
        v = self.b[self.o:self.o + n]
        self.o += n
        return v

    def s(self, cap=4096):
        e = self.b.find(b'\x00', self.o)
        if e < 0 or e - self.o > cap:
            raise End('string without NUL (or longer than %d B)' % cap)
        v = self.b[self.o:e]
        self.o = e + 1
        return v


def ascii_mark(v):
    b = struct.pack('<I', v & 0xFFFFFFFF)
    return b.decode('ascii') if all(32 <= c < 127 for c in b) else None


def _res(regs, declared, r, minimum, header, count_pos, **extra):
    d = {
        'regs': regs,
        'declared': declared,
        'remaining': r.remaining(),
        'end_pos': r.o,
        'minimum': minimum,
        'header': header,
        'count_pos': count_pos,
        'available': len(r.b) - header,
    }
    d.update(extra)
    return d


def min_w3r(v):
    n = 16 + 1
    n += 4 if v >= 1 else 0
    n += 4 if v >= 3 else 0
    n += 1 if v >= 4 else 0
    n += 4 if v >= 5 else 0
    n += 8 if v >= 7 else 0
    return n


def read_region(r, v):
    reg = {}
    if v >= 2:
        reg['rect'] = [r.f32() for _ in range(4)]
    else:
        reg['rect'] = [float(r.i32()) for _ in range(4)]
    reg['fname'] = r.s()
    if v >= 1:
        reg['creation'] = r.i32()
    if v >= 3:
        reg['weather'] = r.bs(4)
    if v >= 4:
        reg['sound'] = r.s()
    if v >= 5:
        reg['color'] = r.bs(4)
    if v >= 7:
        r.i32()
        r.i32()
    return reg


def read_w3r(b):
    r = Reader(b, 8)
    v, n = struct.unpack_from('<II', b, 0)
    regs = []
    for _ in range(min(n, 1 << 20)):
        try:
            regs.append(read_region(r, v))
        except End:
            break
    return _res(regs, n, r, min_w3r(v), 8, 4, version_num=v)


def write_w3r(regions, v=5):
    out = [struct.pack('<ii', v, len(regions))]
    for x in regions:
        out.append(struct.pack('<4f', *[float(c) for c in x['rect']]))
        fname = x.get('fname') or ''
        out.append((fname.encode('utf-8', 'replace') if isinstance(fname, str) else fname) + b'\x00')
        out.append(struct.pack('<i', int(x.get('creation', 0))))
        out.append(x.get('weather') or b'\x00' * 4)
        sound = x.get('sound') or b''
        out.append((sound.encode('utf-8', 'replace') if isinstance(sound, str) else sound) + b'\x00')
        out.append(x.get('color') or bytes((0xFF, 0x80, 0x80, 0xFF)))
    return b''.join(out)


def min_w3c(v, new_ones=True, dof=None):
    if dof is None:
        return min(min_w3c(v, new_ones, True), min_w3c(v, new_ones, False))
    n = 10 * 4 + 1
    n += 12 if new_ones else 0
    n += (12 + 4) if (dof and v >= 3) else 0
    return n


def read_camera(r, v, new_ones, dof=True):
    cpath = {'tgt': [r.f32() for _ in range(2)], 'z': r.f32(), 'rotation': r.f32(), 'angle': r.f32(),
             'target_distance': r.f32(), 'roll': r.f32(), 'fov': r.f32(), 'far': r.f32(), 'near': r.f32()}
    if new_ones:
        cpath['local'] = [r.f32() for _ in range(3)]
    if dof and v >= 3:
        cpath['dof'] = [r.f32() for _ in range(3)]
    cpath['fname'] = r.s()
    if dof and v >= 3:
        r.i32()
    return cpath


def read_w3c(b):
    v, n = struct.unpack_from('<II', b, 0)
    best = None
    for new_ones in (False, True):
        for dof in (False, True):
            if dof and v < 3:
                continue
            r = Reader(b, 8)
            regs = []
            for _ in range(min(n, 1 << 20)):
                try:
                    regs.append(read_camera(r, v, new_ones, dof))
                except End:
                    break
            cand = _res(regs, n, r, min_w3c(v, new_ones, dof), 8, 4, version_num=v, layout=(new_ones, dof))
            if r.remaining() == 0 and len(regs) == n:
                return cand
            if best is None or (0 <= cand['remaining'] < best['remaining']):
                best = cand
    return best


def write_w3c(cameras, version_num=0, new_ones=False, dof=False):
    out = [struct.pack('<ii', version_num, len(cameras))]
    for c in cameras:
        out.append(struct.pack('<10f', c['tgt'][0], c['tgt'][1], c.get('z', 0.0), c.get('rotation', 0.0),
                               c.get('angle', 0.0), c.get('target_distance', 0.0), c.get('roll', 0.0),
                               c.get('fov', 0.0), c.get('far', 0.0), c.get('near', 100.0)))
        if new_ones:
            out.append(struct.pack('<3f', *(c.get('local') or [0.0, 0.0, 0.0])))
        if dof and version_num >= 3:
            out.append(struct.pack('<3f', *(c.get('dof') or [0.0, 0.0, 0.0])))
        fname = c.get('fname') or b''
        out.append((fname.encode('utf-8', 'replace') if isinstance(fname, str) else fname) + b'\x00')
        if dof and version_num >= 3:
            out.append(struct.pack('<i', 0))
    return b''.join(out)


def _min_sound(v):
    n = 3 + 17 * 4
    n += (8 + 11) if v > 1 else 0
    n += 5 if v > 2 else 0
    return n


def read_sound(r, v):
    sound = {'fname': r.s(), 'file_path': r.s(), 'eax': r.s(), 'flags': r.i32()}
    for _c in range(3):
        r.i32()
    r.f32()
    r.f32()
    r.i32()
    r.i32()
    for _c in range(3):
        r.f32()
    for _c in range(2):
        r.f32()
    r.i32()
    for _c in range(3):
        r.f32()
    if v > 1:
        r.s()
        r.s()
        r.s()
        r.i32()
        r.s()
        r.i32()
        r.s()
        r.bs(3)
        r.s()
        r.s()
        r.s()
        r.s()
    if v > 2:
        r.bs(1)
        r.i32()
    return sound


def read_w3s(b):
    r = Reader(b, 8)
    v, n = struct.unpack_from('<II', b, 0)
    sounds = []
    for _ in range(min(n, 1 << 20)):
        try:
            sounds.append(read_sound(r, v))
        except End:
            break
    return _res(sounds, n, r, _min_sound(v), 8, 4, version_num=v)


def read_imp(b):
    r = Reader(b, 8)
    v, n = struct.unpack_from('<II', b, 0)
    item_entries = []
    for _ in range(min(n, 1 << 20)):
        try:
            item_entries.append({'kind': r.bs(1)[0], 'file_path': r.s()})
        except End:
            break
    return _res(item_entries, n, r, 2, 8, 4, version_num=v)


def read_mmp(b):
    r = Reader(b, 8)
    v, n = struct.unpack_from('<II', b, 0)
    icons = []
    for _ in range(min(n, 1 << 20)):
        try:
            icons.append({'kind': r.i32(), 'x': r.i32(), 'y': r.i32(), 'color': r.bs(4)})
        except End:
            break
    return _res(icons, n, r, 16, 8, 4, version_num=v)


def read_wct(b):
    if len(b) < 4:
        raise FormatError('too short')
    r = Reader(b, 0)
    ver = r.u32()
    if ver == 0:
        declared = r.i32()
        header, count_pos = 8, 4
    elif ver == 1:
        r.s()
        sz = r.i32()
        if sz:
            r.bs(sz)
        declared = r.i32()
        header, count_pos = r.o, r.o - 4
    elif ver & 0x80000000:
        if ver not in (0x80000001, 0x80000004):
            raise FormatError('unknown subversion 0x%08X' % ver)
        if r.u32() != 1:
            raise FormatError('subversion without version 1')
        r.s()
        sz = r.i32()
        if sz:
            r.bs(sz)
        header, count_pos = r.o, None
        trigger_list = []
        while r.remaining() > 0:
            t = r.i32()
            if t:
                r.bs(t)
            trigger_list.append(t)
        return _res(trigger_list, len(trigger_list), r, 4, header, count_pos, version_num=1, subversion=ver)
    else:
        raise FormatError('unknown version %d' % ver)
    trigger_list = []
    for _ in range(min(declared, 1 << 20)):
        try:
            t = r.i32()
            if t:
                r.bs(t)
        except End:
            break
        trigger_list.append(t)
    return _res(trigger_list, declared, r, 4, header, count_pos, version_num=ver)


def read_wtg(b):
    if b[:4] != b'WTG!':
        raise FormatError('missing WTG!')
    r = Reader(b, 4)
    ver = r.u32()
    if ver & 0x80000000:
        if ver not in (0x80000001, 0x80000004):
            raise FormatError('unknown new format 0x%08X' % ver)
        ver = r.u32()
        for _c in range(4):
            r.u32()
        minimum = 17
    elif ver in (3, 4, 6, 7):
        minimum = 9
    else:
        raise FormatError('unknown version %d' % ver)
    n = r.u32()
    return _res([], n, r, minimum, r.o, r.o - 4, version_num=ver, no_records=True)


def read_units_record(b, p, ver, sub, skin=False):
    if ver == 7 and sub == 9:
        modern, skin = False, False
    elif ver == 8 and sub == 11:
        modern = True
    elif ver == 13 and sub == 9:
        raise FormatError('version 13/9 (the new World Editor) has not been measured yet')
    else:
        raise FormatError('unknown version %d/%d' % (ver, sub))
    o = p + 36 + (4 if skin else 0)
    if o + 7 > len(b):
        raise End('ended in the record header (byte %d)' % p)
    d = {'p': p, 'ident': b[p:p + 4], 'skin': skin, 'modern': modern, 'flags': b[o],
         'owner': struct.unpack_from('<h', b, o + 1)[0]}
    o += 7
    if o + 8 > len(b):
        raise End('ended before the hp (byte %d)' % p)
    d['hp'], d['mana'] = struct.unpack_from('<2i', b, o)
    o += 8
    d['itp'] = -1
    if modern:
        d['itp'] = struct.unpack_from('<i', b, o)[0] if o + 4 <= len(b) else -1
        o += 4
    if o + 4 > len(b):
        raise End('ended before the item sets (byte %d)' % p)
    d['item_sets'] = struct.unpack_from('<i', b, o)[0]
    if not 0 <= d['item_sets'] <= 32:
        raise End('item sets %d' % d['item_sets'])
    o += 4
    item_entries = 0
    for _k in range(d['item_sets']):
        if o + 4 > len(b):
            raise End('ended in an item set (byte %d)' % p)
        k = struct.unpack_from('<i', b, o)[0]
        if not 0 <= k <= 64:
            raise End('set with %d items' % k)
        item_entries += k
        o += 4 + 8 * k
    d['item_entries'] = item_entries
    if o + 12 > len(b):
        raise End('ended before the gold (byte %d)' % p)
    d['gold'] = struct.unpack_from('<i', b, o)[0]
    d['acq'] = struct.unpack_from('<f', b, o + 4)[0]
    d['level'] = struct.unpack_from('<i', b, o + 8)[0]
    o += 12
    if modern:
        o += 12
    if o + 4 > len(b):
        raise End('ended before the inventory (byte %d)' % p)
    d['inv'] = struct.unpack_from('<i', b, o)[0]
    if not 0 <= d['inv'] <= 64:
        raise End('inventory with %d items' % d['inv'])
    o += 4 + 8 * d['inv']
    if o + 4 > len(b):
        raise End('ended before the abilities (byte %d)' % p)
    d['habs'] = struct.unpack_from('<i', b, o)[0]
    if not 0 <= d['habs'] <= 64:
        raise End('unit with %d abilities' % d['habs'])
    o += 4 + 12 * d['habs']
    if o + 4 > len(b):
        raise End('ended before is_random (byte %d)' % p)
    d['rnd'] = struct.unpack_from('<i', b, o)[0]
    o += 4
    if d['rnd'] == 0:
        o += 4
    elif d['rnd'] == 1:
        o += 8
    elif d['rnd'] == 2:
        if o + 4 > len(b):
            raise End('ended in the random table (byte %d)' % p)
        k = struct.unpack_from('<i', b, o)[0]
        if not 0 <= k <= 256:
            raise End('random table of %d' % k)
        o += 4 + 8 * k
    elif d['rnd'] != -1:
        raise End('is_random %d' % d['rnd'])
    if o + 12 > len(b):
        raise End('ended before the end of the record (byte %d)' % p)
    d['color'], d['waygate'], d['creation'] = struct.unpack_from('<3i', b, o)
    d['sz'] = (o + 12) - p
    return d


def read_units_doo(b):
    if b[:4] != b'W3do':
        raise FormatError('missing W3do')
    ver, sub = struct.unpack_from('<ii', b, 4)
    n = struct.unpack_from('<I', b, 12)[0]
    skins = (False,) if (ver, sub) == (7, 9) else (False, True)
    best = None
    for skin in skins:
        regs, o, err = [], 16, None
        for _i in range(n):
            try:
                d = read_units_record(b, o, ver, sub, skin)
            except (End, struct.error) as e:
                err = e
                break
            regs.append(d)
            o += d['sz']
        on_close = err is None and o == len(b)
        if on_close:
            minimum = (91, 111, 115)[0 if (ver, sub) == (7, 9) else (2 if skin else 1)]
            return _res(regs, n, Reader(b, o), minimum, 16, 12, version_num=(ver, sub), on_close=True,
                        layout='%d/%d%s' % (ver, sub, '+skin' if skin else ''), skin=skin)
        if best is None or len(regs) > len(best[0]):
            best = (regs, o, skin)
    regs, o, skin = best
    minimum = (91, 111, 115)[0 if (ver, sub) == (7, 9) else (2 if skin else 1)]
    return _res(regs, n, Reader(b, o), minimum, 16, 12, version_num=(ver, sub), on_close=False,
                layout='%d/%d%s' % (ver, sub, '+skin' if skin else ''), skin=skin)


def units_layout(b, w3i_version=None, game_132=None):
    file_ = None
    if b and len(b) >= 16 and b[:4] == b'W3do':
        file_ = struct.unpack_from('<ii', b, 4)
    if _is_132(game_132, w3i_version):
        if file_ == (8, 11):
            try:
                return 8, 11, bool(read_units_doo(b).get('skin'))
            except (FormatError, End, struct.error):
                pass
        return 8, 11, True
    if file_ == (7, 9):
        return 7, 9, False
    if file_ == (8, 11):
        try:
            return 8, 11, bool(read_units_doo(b).get('skin'))
        except (FormatError, End, struct.error):
            return 8, 11, _is_132(game_132, w3i_version)
    if w3i_version and w3i_version <= 25:
        return 7, 9, False
    return 8, 11, _is_132(game_132, w3i_version)


def _is_132(game_132, w3i_version):
    if game_132 is not None:
        return bool(game_132)
    return bool(w3i_version and w3i_version >= 31)


def player_count(w3i_version=None):
    return 24 if (w3i_version or 0) >= 31 else 12


_READERS = {'war3map.w3r': read_w3r, 'war3map.w3c': read_w3c, 'war3map.w3s': read_w3s, 'war3map.imp': read_imp,
            'war3map.mmp': read_mmp, 'war3map.wct': read_wct, 'war3map.wtg': read_wtg,
            'war3mapUnits.doo': read_units_doo}


def analyze(fname, b):
    if b is None:
        return None
    if not b or (len(b) < 8 and fname != 'war3map.wct'):
        return {'file_name': fname, 'declared': None, 'read_count': 0, 'mark': None, 'reason': EMPTY, 'minimum': None,
                'remaining': 0, 'available': 0, 'byte_size': len(b), 'game': fname in REPORTED_ONLY}
    try:
        if fname in _READERS:
            x = _READERS[fname](b)
        elif fname == 'war3map.doo':
            x = _res([], struct.unpack_from('<I', b, 12)[0], Reader(b, 16), 42, 16, 12, no_records=True)
        else:
            return None
    except FormatError as e:
        if fname == 'war3mapUnits.doo' and b[:4] == b'W3do':
            return {'file_name': fname, 'declared': struct.unpack_from('<I', b, 12)[0], 'read_count': 0, 'mark': None,
                    'reason': ODD_VERSION, 'minimum': None, 'remaining': None, 'available': None,
                    'byte_size': len(b), 'detail': str(e), 'game': False}
        return None
    except (End, struct.error) as e:
        return {'file_name': fname, 'declared': None, 'read_count': 0, 'mark': None, 'reason': EMPTY, 'minimum': None,
                'remaining': None, 'available': None, 'byte_size': len(b), 'detail': str(e),
                'game': fname in REPORTED_ONLY}
    finding = {'file_name': fname, 'declared': x['declared'], 'read_count': len(x['regs']),
               'mark': ascii_mark(x['declared']), 'minimum': x['minimum'], 'remaining': x['remaining'],
               'available': x['available'], 'byte_size': len(b), 'reason': None, 'game': fname in REPORTED_ONLY}
    if not x.get('no_records') and len(x['regs']) == x['declared'] and x['remaining'] == 0:
        return None
    if x['minimum'] and x['declared'] * x['minimum'] > x['available']:
        finding['reason'] = DOES_NOT_FIT
    elif not x.get('no_records') and len(x['regs']) < x['declared']:
        finding['reason'] = SHORT_READ
    else:
        return None
    return finding


def analyze_map(a, editor_only=True):
    name_list = list(FILES) + ([] if editor_only else list(REPORTED_ONLY))
    out = []
    for fname in name_list:
        try:
            b = a.read(fname)
        except Exception:
            b = None
        x = analyze(fname, b)
        if x:
            out.append(x)
    return out


def _rewrite(b, x, new_n):
    if x.get('count_pos') is None:
        return None
    return b[:x['count_pos']] + struct.pack('<i', new_n) + b[x['header']:x['end_pos']]


def fixable(fname, b, script=None, context=None):
    x = analyze(fname, b)
    if not x:
        return b, {'file_name': fname, 'declared': None, 'read_count': None, 'new': None, 'from_script': False,
                   'reason': 'bom', 'report': '%s: was already fine' % fname}
    if x.get('game'):
        return None, {'file_name': fname, 'reason': 'game', 'report': '%s: the GAME reads it' % fname}
    if x['reason'] == EMPTY:
        done = _from_script(fname, script, x, context=context)
        if done:
            return done
        new = _empty(fname, b, {'version_num': None, 'count_pos': None})
        return (new, {'file_name': fname, 'declared': None, 'read_count': 0, 'new': 0, 'from_script': False,
                      'reason': EMPTY, 'report': '%s: empty (does not even have the header)' % fname}) if new else \
            (None, {'file_name': fname, 'reason': EMPTY, 'report': '%s: empty, no rewrite' % fname})
    try:
        d = _READERS[fname](b)
    except (End, FormatError, struct.error) as e:
        done = _from_script(fname, script, x, x.get('declared'), context)
        if done:
            done[1]['reason'] = x['reason']
            return done
        return None, {'file_name': fname, 'reason': 'err', 'report': '%s: %s' % (fname, e)}
    read_count, declared = len(d['regs']), d['declared']
    if not read_count:
        done = _from_script(fname, script, x, declared, context)
        if done:
            return done
    if read_count:
        return _rewrite(b, d, read_count), {
            'file_name': fname,
            'declared': declared,
            'read_count': read_count,
            'new': read_count,
            'from_script': False,
            'reason': x['reason'],
            'report': ('%s: count %s -> %d (the records that read cleanly)' % (fname, declared, read_count)),
        }
    if fname in NO_REWRITE:
        return None, {'file_name': fname, 'reason': 'no_rewrite',
                      'report': ('%s: the records cannot be read one by one (the parameter count comes from '
                                 'triggerdata.txt) and the script creates nothing' % fname)}
    new = _empty(fname, b, d)
    if new is None:
        return None, {'file_name': fname, 'reason': 'no_rewrite', 'report': '%s: no rewrite' % fname}
    return new, {'file_name': fname, 'declared': declared, 'read_count': 0, 'new': 0, 'from_script': False,
                 'reason': x['reason'],
                 'report': '%s: empty (declared %s and no record can be read)' % (fname, declared)}


def _map_models(a):
    import objbin
    out = {}
    for file_name, field_id, with_levels in (('war3map.w3u', 'umdl', False), ('war3map.w3b', 'bfil', False),
                                             ('war3map.w3d', 'dfil', True)):
        b = a.read(file_name)
        if not b:
            continue
        try:
            _v, tables, _p = objbin.read_data(b, with_levels)
        except Exception:
            continue
        for objs in tables:
            for _old_id, new, mods in objs:
                for mid, _vt, _lvl, _dptr, val in mods:
                    if mid.strip('\x00') == field_id and isinstance(val, bytes) and val:
                        out[new] = val.decode('latin-1')
    return out


def _in_map(a, fname):
    if not fname:
        return False
    root, ext = os.path.splitext(fname)
    for c in (fname, root + ('.mdx' if ext.lower() == '.mdl' else '.mdl')):
        try:
            if a.find(c):
                return True
        except Exception:
            pass
    return False


def risky_units(a, units):
    import doodads
    models = _map_models(a)
    placed = set()
    try:
        b = a.read('war3map.doo')
        if b:
            for r in doodads.read_data(b)['regs']:
                ident = r.get('id') or r.get('ident')
                if ident:
                    placed.add(ident.decode('latin-1'))
    except Exception:
        placed = set()
    from_doodads = set(models[i].lower() for i in placed if i in models)
    staying, removed = [], {}
    for u in units:
        ident = u['id'].decode('latin-1') if isinstance(u['id'], bytes) else u['id']
        m = models.get(ident)
        if m and _in_map(a, m) and m.lower() not in from_doodads:
            removed[ident] = removed.get(ident, 0) + 1
            continue
        staying.append(u)
    return staying, removed


def _from_script(fname, script, x, declared=None, context=None):
    for file_, extract, write, singular, plural, where in FROM_SCRIPT:
        if file_ != fname or not script:
            continue
        context = context or {}
        item_entries = extract(script)
        if not item_entries:
            return None
        if fname == 'war3mapUnits.doo':
            version_num, subversion, skin = units_layout(context.get('current'), context.get('w3i'),
                                                      context.get('game_132'))
            item_entries = script_units(script, player_count(context.get('w3i')))
            if not item_entries:
                return None
            removed = {}
            if context.get('mpq') is not None and context.get('safe_units', True):
                item_entries, removed = risky_units(context['mpq'], item_entries)
            data_bytes = write(item_entries, version_num, subversion, skin)
            report = ('%s: %d %s from `%s` in the script (layout %d/%d%s, %d players)'
                      % (fname, len(item_entries), plural, where, version_num, subversion, '+skin' if skin else '',
                         player_count(context.get('w3i'))))
            if removed:
                report += ('; %d NOT restored because they are risky (the model is a map file that no '
                           'placed doodad uses: the 3.0 editor crashes when it reads a map file after releasing the '
                           'file on the 2nd opening): %s'
                           % (sum(removed.values()),
                              ', '.join('%s x%d' % (k, v) for k, v in sorted(removed.items())[:6]) +
                              ('...' if len(removed) > 6 else '')))
            return data_bytes, {
                'file_name': fname,
                'declared': declared,
                'read_count': 0,
                'new': len(item_entries),
                'from_script': True,
                'reason': x.get('reason'),
                'where': where,
                'singular': singular,
                'plural': plural,
                'removed_risky': removed or None,
                'layout': '%d/%d%s' % (version_num, subversion, '+skin' if skin else ''),
                'report': report,
            }
        return write(item_entries), {
            'file_name': fname,
            'declared': declared,
            'read_count': 0,
            'new': len(item_entries),
            'from_script': True,
            'reason': x.get('reason'),
            'where': where,
            'singular': singular,
            'plural': plural,
            'report': ('%s: %d %s from `%s` in the script' % (fname, len(item_entries), plural, where)),
        }
    return None


def fix_from_script(fname, script, reason='was_missing', context=None):
    return _from_script(fname, script, {'reason': reason}, context=context)


def count_in_file(fname, a):
    try:
        b = a.read(fname)
    except Exception:
        b = None
    if b is None:
        return None
    if not b:
        return 0
    try:
        if fname == 'war3mapUnits.doo':
            if b[:4] != b'W3do':
                return None
            try:
                d = read_units_doo(b)
                if d.get('on_close'):
                    return len(d['regs'])
            except (End, FormatError, struct.error):
                pass
            return struct.unpack_from('<I', b, 12)[0]
        reader = _READERS.get(fname)
        return len(reader(b)['regs']) if reader else None
    except (End, FormatError, struct.error):
        return None


def _empty(fname, b, d):
    v = d.get('version_num')
    if fname == 'war3map.w3r':
        return struct.pack('<ii', v if v else 5, 0)
    if fname == 'war3map.w3c':
        return struct.pack('<ii', v if v else 0, 0)
    if fname == 'war3map.w3s':
        return struct.pack('<ii', v if v else 3, 0)
    if fname == 'war3map.imp':
        return struct.pack('<ii', 1, 0)
    if fname == 'war3map.mmp':
        return struct.pack('<ii', 0, 0)
    if fname == 'war3map.wct':
        if d.get('count_pos') is None:
            return b
        return b[:d['count_pos']] + struct.pack('<i', 0)
    return None


def _num(t):
    s = (t or '').strip().replace(' ', '')
    if s.startswith('+'):
        s = s[1:]
    return float(s)


def _var_name(fname, prefix=''):
    if prefix and fname.startswith(prefix):
        fname = fname[len(prefix):]
    return fname.replace('_', ' ')


RX_RECT = re.compile(r'gg_rct_([A-Za-z0-9_]+)\s*=\s*Rect\(\s*([^)]*)\)')
RX_RECT_JASS = re.compile(r'set\s+gg_rct_([A-Za-z0-9_]+)\s*=\s*Rect\(\s*([^)]*)\)')
RX_WEATHER = re.compile(r'AddWeatherEffect\(\s*gg_rct_([A-Za-z0-9_]+)\s*,\s*'
                        r'(?:FourCC\(\s*[\'"](.{1,4})[\'"]\s*\)|\'(.{1,4})\')')
RX_SOUND_POS = re.compile(r'SetSoundPosition\(\s*(gg_snd_[A-Za-z0-9_]+)\s*,\s*'
                          r'([-+0-9.eE]+)\s*,\s*([-+0-9.eE]+)')
RX_STACKED_SOUND = re.compile(r'RegisterStackedSound\(\s*(gg_snd_[A-Za-z0-9_]+)\s*,\s*\w+\s*,\s*'
                              r'([-+0-9.eE]+)\s*,\s*([-+0-9.eE]+)')


def script_regions(body_text):
    if not body_text:
        return []
    hits, order = {}, []
    for rx in (RX_RECT_JASS, RX_RECT):
        for m in rx.finditer(body_text):
            fname = m.group(1)
            if fname in hits:
                continue
            nums = []
            for p in m.group(2).split(','):
                try:
                    nums.append(_num(p))
                except ValueError:
                    nums = []
                    break
            if len(nums) != 4:
                continue
            hits[fname] = {'rect': nums, 'fname': _var_name(fname), 'creation': len(order),
                           'weather': b'\x00' * 4, 'sound': b'', 'color': bytes((0xFF, 0x80, 0x80, 0xFF))}
            order.append(fname)
    if not order:
        return []
    for m in RX_WEATHER.finditer(body_text):
        if m.group(1) in hits:
            hits[m.group(1)]['weather'] = (m.group(2) or m.group(3) or '').encode('latin-1')[:4].ljust(4, b'\x00')
    for m in RX_SOUND_POS.finditer(body_text):
        try:
            x, y = _num(m.group(2)), _num(m.group(3))
        except ValueError:
            continue
        for reg in hits.values():
            r = reg['rect']
            if abs((r[0] + r[2]) / 2.0 - x) < 0.5 and abs((r[1] + r[3]) / 2.0 - y) < 0.5:
                reg['sound'] = m.group(1).encode('latin-1')
                break
    for m in RX_STACKED_SOUND.finditer(body_text):
        try:
            width, height = _num(m.group(2)), _num(m.group(3))
        except ValueError:
            continue
        for reg in hits.values():
            r = reg['rect']
            if abs((r[2] - r[0]) - width) < 0.5 and abs((r[3] - r[1]) - height) < 0.5:
                reg['sound'] = m.group(1).encode('latin-1')
                break
    return [hits[n] for n in order]


CAMERA_FIELDS = {'CAMERA_FIELD_ZOFFSET': 'z', 'CAMERA_FIELD_ROTATION': 'rotation',
                 'CAMERA_FIELD_ANGLE_OF_ATTACK': 'angle', 'CAMERA_FIELD_TARGET_DISTANCE': 'target_distance',
                 'CAMERA_FIELD_ROLL': 'roll', 'CAMERA_FIELD_FIELD_OF_VIEW': 'fov',
                 'CAMERA_FIELD_FARZ': 'far', 'CAMERA_FIELD_NEARZ': 'near',
                 'CAMERA_FIELD_LOCAL_PITCH': 'local0', 'CAMERA_FIELD_LOCAL_YAW': 'local1',
                 'CAMERA_FIELD_LOCAL_ROLL': 'local2'}
RX_CAM = re.compile(r'(gg_cam_[A-Za-z0-9_]+)\s*=\s*CreateCameraSetup\(')
RX_CAM_FIELD = re.compile(r'CameraSetupSetField\(\s*(gg_cam_[A-Za-z0-9_]+)\s*,\s*(CAMERA_FIELD_[A-Z_]+)\s*,\s*([^,]+),')
RX_CAM_POS = re.compile(r'CameraSetupSetDestPosition\(\s*(gg_cam_[A-Za-z0-9_]+)\s*,\s*([^,]+),\s*([^,]+),')


def cameras_from_script(body_text):
    if not body_text:
        return []
    hits, order = {}, []
    for m in RX_CAM.finditer(body_text):
        fname = m.group(1)
        if fname in hits:
            continue
        hits[fname] = {'fname': _var_name(fname, 'gg_cam_'), 'tgt': [0.0, 0.0], 'z': 0.0, 'rotation': 0.0,
                       'angle': 0.0, 'target_distance': 0.0, 'roll': 0.0, 'fov': 0.0, 'far': 0.0, 'near': 100.0}
        order.append(fname)
    for m in RX_CAM_FIELD.finditer(body_text):
        c, field_id = hits.get(m.group(1)), CAMERA_FIELDS.get(m.group(2))
        if not c or not field_id:
            continue
        try:
            v = _num(m.group(3))
        except ValueError:
            continue
        if field_id.startswith('local'):
            c.setdefault('local', [0.0, 0.0, 0.0])[int(field_id[-1])] = v
        else:
            c[field_id] = v
    for m in RX_CAM_POS.finditer(body_text):
        c = hits.get(m.group(1))
        if not c:
            continue
        try:
            c['tgt'] = [_num(m.group(2)), _num(m.group(3))]
        except ValueError:
            pass
    return [hits[n] for n in order]


UNIT_FUNCTIONS = ('CreateAllUnits', 'CreateNeutralPassiveBuildings', 'CreatePlayerBuildings',
                  'CreateNeutralHostile', 'CreateNeutralPassive', 'CreatePlayerUnits')


def neutral_owners(how_many=None, reforged=True):
    p = 24 if reforged else (how_many or 12)
    return {'PLAYER_NEUTRAL_AGGRESSIVE': p, 'PLAYER_NEUTRAL_PASSIVE': p + 3,
            'PLAYER_NEUTRAL': p + 3}


RX_UNIT = re.compile(r'(?:BlzCreateUnitWithSkin|CreateUnit)\(\s*([^,()]+?|Player\([^)]*\))\s*,\s*'
                     r'(?:FourCC\(\s*[\'"](.{1,4})[\'"]\s*\)|\'(.{1,4})\')\s*,\s*'
                     r'([^,]+?)\s*,\s*([^,]+?)\s*,\s*([^,)]+)'
                     r'(?:\s*,\s*(?:FourCC\(\s*[\'"](.{1,4})[\'"]\s*\)|[\'"](.{1,4})[\'"]))?')
RX_PLAYER_VAR = re.compile(r'(?:local\s+)?([A-Za-z_]\w*)\s*=\s*Player\(\s*(\w+|\d+)\s*\)')
RX_START = re.compile(r'DefineStartLocation\(\s*(\d+)\s*,\s*([-+0-9.eE\s]+?)\s*,\s*([-+0-9.eE\s]+?)\s*\)')
RX_GOLD = re.compile(r'SetResourceAmount\(\s*\w+\s*,\s*(\d+)\s*\)')
RX_CAMP = re.compile(r'SetUnitAcquireRange\s*\(')


RX_ANY_FUNCTION = re.compile(r'function\s+([A-Za-z_]\w*)\b\s*[\(t]')


def _function_marks(body_text, chosen=None):
    out = []
    for m in RX_ANY_FUNCTION.finditer(body_text):
        j = m.start() - 1
        while j >= 0 and body_text[j] in ' \t':
            j -= 1
        if j >= 0 and body_text[j] not in ';\r\n':
            continue
        if chosen is None or m.group(1) in chosen:
            out.append((m.start(), m.group(1)))
    return out


def _bodies_of(body_text):
    targets = _function_marks(body_text, UNIT_FUNCTIONS)
    if not targets:
        return
    all_entries = [p for p, _n in _function_marks(body_text)]
    for begin, fname in targets:
        following = [p for p in all_entries if p > begin]
        yield fname, body_text[begin:following[0] if following else len(body_text)]


def _script_owner(body_text, neutral_players):
    map_path = {}
    for var, val in RX_PLAYER_VAR.findall(body_text):
        v = neutral_players.get(val.strip(), None)
        if v is None:
            try:
                v = int(val)
            except ValueError:
                v = None
        if v is not None:
            map_path.setdefault(var, set()).add(v)
    return dict((k, sorted(v)[0]) for k, v in map_path.items() if len(v) == 1)


def _owner(who, owners, neutral_players):
    if who.startswith('Player('):
        arg = who[7:].rstrip(')').strip()
        v = neutral_players.get(arg)
        if v is None:
            try:
                v = int(arg)
            except ValueError:
                v = None
        return v
    return owners.get(who)


def script_units(body_text, how_many=12, reforged=True):
    if not body_text:
        return []
    neutral_players = neutral_owners(how_many, reforged)
    out = []
    for m in RX_START.finditer(body_text):
        try:
            owner, x, y = int(m.group(1)), _num(m.group(2)), _num(m.group(3))
        except ValueError:
            continue
        out.append({'id': b'sloc', 'x': x, 'y': y, 'rotation': 1.5 * 3.14159265358979, 'owner': owner})
    overall = _script_owner(body_text, neutral_players)
    for _name, body in _bodies_of(body_text):
        owners = dict(overall)
        owners.update(_script_owner(body, neutral_players))
        matches = list(RX_UNIT.finditer(body))
        for k, m in enumerate(matches):
            ident = m.group(2) or m.group(3) or ''
            owner = _owner(m.group(1).strip(), owners, neutral_players)
            if owner is None or len(ident) != 4:
                continue
            try:
                x, y, rot = _num(m.group(4)), _num(m.group(5)), _num(m.group(6))
            except ValueError:
                continue
            u = {'id': ident.encode('latin-1'), 'x': x, 'y': y,
                 'rotation': rot * 3.14159265358979 / 180.0, 'owner': owner}
            skin_id = m.group(7) or m.group(8)
            if skin_id and len(skin_id) == 4:
                u['skin_id'] = skin_id.encode('latin-1')
            end_pos = matches[k + 1].start() if k + 1 < len(matches) else len(body)
            segment = body[m.end():end_pos]
            for field_value in RX_GOLD.findall(segment):
                u['gold'] = int(field_value)
                break
            if RX_CAMP.search(segment):
                u['campaign_info'] = True
            out.append(u)
    return out


def write_units_doo(units, version_num=7, subversion=9, skin=False):
    modern = (version_num, subversion) != (7, 9)
    out = [b'W3do' + struct.pack('<iiI', version_num, subversion, len(units))]
    for i, u in enumerate(units):
        ident = u['id'] if isinstance(u['id'], bytes) else u['id'].encode('latin-1')
        ident = ident[:4].ljust(4, b'\x00')
        start_location = ident == b'sloc'
        out.append(ident)
        out.append(struct.pack('<i', 0))
        out.append(struct.pack('<3f', float(u['x']), float(u['y']), float(u.get('z', 0.0))))
        out.append(struct.pack('<f', float(u.get('rotation', 0.0))))
        out.append(struct.pack('<3f', 1.0, 1.0, 1.0))
        if skin:
            skin_id = u.get('skin_id')
            if skin_id:
                skin_id = skin_id if isinstance(skin_id, bytes) else skin_id.encode('latin-1')
                out.append(skin_id[:4].ljust(4, b'\x00'))
            else:
                out.append(ident)
        out.append(bytes((2,)))
        out.append(struct.pack('<h', int(u.get('owner', 0))))
        out.append(struct.pack('<i', 0))
        out.append(struct.pack('<ii', 0 if start_location else -1, 0 if start_location else -1))
        if modern:
            out.append(struct.pack('<i', -1))
        out.append(struct.pack('<i', 0))
        gold = 0 if start_location else int(u.get('gold', 12500))
        out.append(struct.pack('<i', gold))
        acq = 0.0 if start_location else (-2.0 if u.get('campaign_info') else -1.0)
        out.append(struct.pack('<f', acq))
        out.append(struct.pack('<i', 0 if start_location else 1))
        if modern:
            out.append(struct.pack('<3i', 0, 0, 0))
        out.append(struct.pack('<2i', 0, 0))
        if modern:
            out.append(struct.pack('<5i', 0, 1, -1, -1, int(u.get('creation', 1000 + i))))
        else:
            out.append(struct.pack('<4i', -1, -1, -1, int(u.get('creation', 1000 + i))))
    return b''.join(out)


FROM_SCRIPT = (('war3map.w3r', script_regions, write_w3r, 'region', 'regions', 'CreateRegions()'),
               ('war3map.w3c', cameras_from_script, write_w3c, 'camera', 'cameras', 'CreateCameras()'),
               ('war3mapUnits.doo', script_units, write_units_doo, 'unit', 'units',
                'CreateAllUnits()'))
