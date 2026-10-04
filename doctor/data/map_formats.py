# Names the files a map is made of, and reads and writes the placement files byte for byte.
import struct



FILES = {
    'war3map.j': ('the map script (JASS)', 'game', 'classic'),
    'war3map.lua': ('the map script (Lua)', 'game', '1.31'),
    'scripts\\war3map.j': ('the map script, in the folder the old game also reads', 'game', 'classic'),
    'war3map.w3i': ('the map info: name, players, forces, loading screen', 'both', 'classic'),
    'war3map.wts': ('the strings the other files point to (TRIGSTR_)', 'both', 'classic'),
    'war3map.wtg': ('the triggers as the editor shows them', 'editor', 'classic'),
    'war3map.wct': ('the custom text of the triggers', 'editor', 'classic'),
    'war3map.w3e': ('the terrain: heights, tiles, water, cliffs', 'both', 'classic'),
    'war3map.wpm': ('the pathing map', 'game', 'classic'),
    'war3map.shd': ('the shadow map', 'game', 'classic'),
    'war3map.mmp': ('the minimap icons', 'game', 'classic'),
    'war3map.doo': ('the doodads and destructables placed on the map', 'both', 'classic'),
    'war3mapunits.doo': ('the units and items placed in the editor', 'editor', 'classic'),
    'war3map.w3r': ('the regions', 'editor', 'classic'),
    'war3map.w3c': ('the cameras', 'editor', 'classic'),
    'war3map.w3s': ('the sounds', 'editor', 'classic'),
    'war3map.imp': ('the import list (what the editor keeps when it saves)', 'editor', 'classic'),
    'war3map.w3u': ('the unit object data', 'both', 'classic'),
    'war3map.w3t': ('the item object data', 'both', 'classic'),
    'war3map.w3a': ('the ability object data', 'both', 'classic'),
    'war3map.w3b': ('the destructable object data', 'both', 'classic'),
    'war3map.w3d': ('the doodad object data', 'both', 'classic'),
    'war3map.w3h': ('the buff object data', 'both', 'classic'),
    'war3map.w3q': ('the upgrade object data', 'both', 'classic'),
    'war3mapmisc.txt': ('the gameplay constants', 'game', 'classic'),
    'war3mapskin.txt': ('the interface constants', 'game', 'classic'),
    'war3mapextra.txt': ('the sky, the fog and the weather', 'game', 'classic'),
    'war3mapmap.blp': ('the minimap image', 'game', 'classic'),
    'war3mappreview.tga': ('the preview image of the lobby', 'game', 'classic'),
    'war3mappath.tga': ('the pathing image of old maps', 'game', 'classic'),
    'war3mapskin.w3u': ('the unit art (Reforged skin data)', 'both', '1.32'),
    'war3mapskin.w3t': ('the item art (Reforged skin data)', 'both', '1.32'),
    'war3mapskin.w3a': ('the ability art (Reforged skin data)', 'both', '1.32'),
    'war3mapskin.w3b': ('the destructable art (Reforged skin data)', 'both', '1.32'),
    'war3mapskin.w3d': ('the doodad art (Reforged skin data)', 'both', '1.32'),
    'war3mapskin.w3h': ('the buff art (Reforged skin data)', 'both', '1.32'),
    'war3mapskin.w3q': ('the upgrade art (Reforged skin data)', 'both', '1.32'),
    'conversation.json': ('the FaceFX conversations of the cinematics', 'game', '1.32'),
    'war3map.w3l': ('the lights', 'both', '2.0'),
    'war3mappostprocessing.txt': ('the post processing settings', 'game', '2.0'),
    'war3map.w3grp': ('the groups of the 2.0 editor', 'editor', '2.0'),
    'war3map.soundasset': ('the sound assets of the 2.0 editor', 'both', '2.0'),
    '(listfile)': ('the list of the file names in the archive', 'tools', 'classic'),
    '(attributes)': ('the checksums and dates of the files', 'tools', 'classic'),
    '(signature)': ('the signature of a Blizzard map', 'game', 'classic'),
}
LOCALES = ('deDE', 'enUS', 'esES', 'esMX', 'frFR', 'itIT', 'jaJP', 'koKR', 'plPL', 'ptBR', 'ruRU', 'zhCN', 'zhTW')
LOCALE_DIR = '_Locales\\'
LOCALE_FILES = ('war3map.wts', 'war3map.w3i', 'war3mapSkin.txt', 'war3mapMisc.txt', 'war3mapMap.blp',
                'war3mapPreview.tga', 'conversation.json')
_CASED = dict((n.lower(), n) for n in (
    'war3map.j', 'war3map.lua', 'Scripts\\war3map.j', 'war3map.w3i', 'war3map.wts', 'war3map.wtg', 'war3map.wct',
    'war3map.w3e', 'war3map.wpm', 'war3map.shd', 'war3map.mmp', 'war3map.doo', 'war3mapUnits.doo', 'war3map.w3r',
    'war3map.w3c', 'war3map.w3s', 'war3map.imp', 'war3map.w3u', 'war3map.w3t', 'war3map.w3a', 'war3map.w3b',
    'war3map.w3d', 'war3map.w3h', 'war3map.w3q', 'war3mapMisc.txt', 'war3mapSkin.txt', 'war3mapExtra.txt',
    'war3mapMap.blp', 'war3mapPreview.tga', 'war3mapPath.tga', 'war3mapSkin.w3u', 'war3mapSkin.w3t',
    'war3mapSkin.w3a', 'war3mapSkin.w3b', 'war3mapSkin.w3d', 'war3mapSkin.w3h', 'war3mapSkin.w3q',
    'conversation.json', 'war3map.w3l', 'war3mapPostProcessing.txt', 'war3map.w3grp', 'war3map.soundasset',
    '(listfile)', '(attributes)', '(signature)'))


def split_locale(name):
    n = name.replace('/', '\\')
    if n.lower().startswith(LOCALE_DIR.lower()):
        rest = n[len(LOCALE_DIR):]
        head, _sep, inner = rest.partition('\\')
        if head.lower().endswith('.w3mod') and inner:
            return head[:-6], inner
    return None, n


def describe(name):
    loc, inner = split_locale(name)
    f = FILES.get(inner.lower())
    if f is None:
        return None
    out = {'what': f[0], 'read_by': f[1], 'era': f[2], 'locale': loc}
    if loc:
        out['what'] = '%s, for the %s language' % (f[0], loc)
        out['era'] = '2.0'
    return out


def is_standard(name):
    return describe(name) is not None


def standard_names(locales=True):
    out = list(_CASED.values())
    if locales:
        out += ['%s%s.w3mod\\%s' % (LOCALE_DIR, loc, n) for loc in LOCALES for n in LOCALE_FILES]
    return out


class Unreadable(ValueError):
    pass


class Table(object):
    def __init__(self, kind, head, records, tail, count_at, fields, **info):
        self.kind = kind
        self.head = bytes(head)
        self.records = [bytearray(r) for r in records]
        self.tail = bytes(tail)
        self.count_at = count_at
        self.fields = fields
        self.info = info

    def __len__(self):
        return len(self.records)

    def get(self, i, field):
        off, fmt = self.fields[field]
        v = struct.unpack_from(fmt, self.records[i], off)
        return v[0] if len(v) == 1 else v

    def set(self, i, field, value):
        off, fmt = self.fields[field]
        struct.pack_into(fmt, self.records[i], off, *(value if isinstance(value, (tuple, list)) else (value,)))

    def remove(self, keep):
        old = self.records
        kept = [r for i, r in enumerate(old) if keep(self, i)]
        self.records = kept
        return len(old) - len(kept)

    def write(self):
        head = bytearray(self.head)
        if self.count_at is not None:
            struct.pack_into('<I', head, self.count_at, len(self.records))
        return bytes(head) + b''.join(bytes(r) for r in self.records) + self.tail


class Grid(Table):
    def __init__(self, kind, head, body, stride, tail, fields, **info):
        self.kind = kind
        self.head = bytes(head)
        self.body = bytearray(body)
        self.stride = stride
        self.tail = bytes(tail)
        self.count_at = None
        self.fields = fields
        self.info = info

    def __len__(self):
        return len(self.body) // self.stride

    def get(self, i, field):
        off, fmt = self.fields[field]
        v = struct.unpack_from(fmt, self.body, i * self.stride + off)
        return v[0] if len(v) == 1 else v

    def set(self, i, field, value):
        off, fmt = self.fields[field]
        struct.pack_into(fmt, self.body, i * self.stride + off,
                         *(value if isinstance(value, (tuple, list)) else (value,)))

    def remove(self, keep):
        raise TypeError('the %s cells are a grid: none can be removed' % self.kind)

    def write(self):
        return self.head + bytes(self.body) + self.tail


PLACED = {'id': (0, '4s'), 'variation': (4, '<i'), 'x': (8, '<f'), 'y': (12, '<f'), 'z': (16, '<f'),
          'angle': (20, '<f'), 'scale': (24, '<3f')}


def read_doo(data):
    from doctor.fix import doodads
    try:
        d = doodads.read_data(data)
    except (doodads.FormatError, struct.error) as e:
        raise Unreadable(str(e))
    if not d.get('on_close'):
        raise Unreadable('war3map.doo does not close')
    end = d['regs'][-1]['begin'] + d['regs'][-1]['sz'] if d['regs'] else 16
    if data[end:] != d['tail']:
        raise Unreadable('war3map.doo: the tail does not follow the last record')
    return Table('doo', data[:16], [data[r['begin']:r['begin'] + r['sz']] for r in d['regs']], d['tail'], 12, PLACED,
                 version=d['version_num'], subversion=d['subversion'], skin=d['skin'])


def read_units_doo(data):
    from doctor.fix import inflated_counts
    try:
        d = inflated_counts.read_units_doo(data)
    except Exception as e:
        raise Unreadable(str(e))
    if not d.get('on_close') or d['declared'] != len(d['regs']):
        raise Unreadable('war3mapUnits.doo does not close')
    recs, p = [], 16
    for r in d['regs']:
        recs.append(data[p:p + r['sz']])
        p += r['sz']
    return Table('units_doo', data[:16], recs, data[p:], 12, PLACED, layout=d.get('layout'))


REGION = {'left': (0, '<f'), 'bottom': (4, '<f'), 'right': (8, '<f'), 'top': (12, '<f')}


def _cstr_end(data, p):
    return data.index(b'\0', p) + 1


def read_w3r(data):
    try:
        v, n = struct.unpack_from('<iI', data, 0)
        if not 0 <= v <= 7 or n > len(data):
            raise Unreadable('w3r version %d, %d regions' % (v, n))
        p, recs = 8, []
        for _ in range(n):
            s = p
            p = _cstr_end(data, p + 16)
            p += (4 if v >= 1 else 0) + (4 if v >= 3 else 0)
            if v >= 4:
                p = _cstr_end(data, p)
            p += (4 if v >= 5 else 0) + (8 if v >= 7 else 0)
            if p > len(data):
                raise Unreadable('w3r: a region runs past the end')
            recs.append(data[s:p])
    except (struct.error, ValueError) as e:
        raise Unreadable('w3r: %s' % e)
    return Table('w3r', data[:8], recs, data[p:], 4, REGION, version=v)


def read_imp(data):
    try:
        v, n = struct.unpack_from('<iI', data, 0)
        if n > len(data):
            raise Unreadable('imp: %d entries' % n)
        p, recs = 8, []
        for _ in range(n):
            s = p
            p = _cstr_end(data, p + 1)
            recs.append(data[s:p])
    except (struct.error, ValueError) as e:
        raise Unreadable('imp: %s' % e)
    return Table('imp', data[:8], recs, data[p:], 4, {'flag': (0, 'B')}, version=v)


def read_wpm(data):
    if data[:4] != b'MP3W' or len(data) < 16:
        raise Unreadable('wpm without MP3W')
    v, w, h = struct.unpack_from('<iII', data, 4)
    if w * h > len(data) - 16:
        raise Unreadable('wpm: %dx%d cells in %d bytes' % (w, h, len(data)))
    return Grid('wpm', data[:16], data[16:16 + w * h], 1, data[16 + w * h:], {'flags': (0, 'B')}, version=v,
                width=w, height=h)


def read_w3e(data):
    if data[:4] != b'W3E!':
        raise Unreadable('w3e without W3E!')
    try:
        v = struct.unpack_from('<i', data, 4)[0]
        p = 8 + 1 + 4
        nt = struct.unpack_from('<I', data, p)[0]
        p += 4 + 4 * nt
        nc = struct.unpack_from('<I', data, p)[0]
        p += 4 + 4 * nc
        w, h = struct.unpack_from('<II', data, p)
        p += 8 + 8
    except struct.error as e:
        raise Unreadable('w3e: %s' % e)
    if not w or not h or nt > 64 or nc > 64:
        raise Unreadable('w3e: %d ground and %d cliff tiles, %dx%d points' % (nt, nc, w, h))
    rest = len(data) - p
    size = 7 if v == 11 else rest // (w * h) if rest % (w * h) == 0 else 7
    if size * w * h > rest:
        raise Unreadable('w3e: %dx%d points of %d bytes in %d bytes' % (w, h, size, rest))
    return Grid('w3e', data[:p], data[p:p + size * w * h], size, data[p + size * w * h:],
                {'height': (0, '<h'), 'water': (2, '<h')}, version=v, width=w, height=h)


class _Sounds(object):
    def __init__(self, data):
        from doctor.triggers import editor_render
        try:
            self.version, self.sounds = editor_render.read_w3s(data)
        except Exception as e:
            raise Unreadable('w3s: %s' % e)
        self.kind = 'w3s'

    def __len__(self):
        return len(self.sounds)

    def write(self):
        from doctor.triggers import editor_render
        return editor_render.write_w3s(self.version, self.sounds)


READERS = {'war3map.doo': read_doo, 'war3mapunits.doo': read_units_doo, 'war3map.w3r': read_w3r,
           'war3map.imp': read_imp, 'war3map.wpm': read_wpm, 'war3map.w3e': read_w3e, 'war3map.w3s': _Sounds}


def read(name, data):
    f = READERS.get(split_locale(name)[1].lower())
    return f(data) if f else None

