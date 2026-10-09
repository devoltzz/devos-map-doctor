# Writes the script the World Editor generates from the map files, and fits the custom script to it.
import collections
import decimal
import math
import os
import re
import struct

from doctor.fix import inflated_counts
from doctor.triggers import gui_render


HERE = os.path.dirname(os.path.abspath(__file__))
EDITOR_3 = 7000
NEUTRAL_HOSTILE, NEUTRAL_PASSIVE = 'PLAYER_NEUTRAL_AGGRESSIVE', 'PLAYER_NEUTRAL_PASSIVE'
DEFAULT_FLOAT = 4294967296.0


class Unreadable(Exception):
    pass


class _Reader(object):
    def __init__(self, data, pos=0):
        self.data, self.pos = data, pos

    def i32(self):
        v = struct.unpack_from('<i', self.data, self.pos)[0]
        self.pos += 4
        return v

    def u32(self):
        v = struct.unpack_from('<I', self.data, self.pos)[0]
        self.pos += 4
        return v

    def f32(self):
        v = struct.unpack_from('<f', self.data, self.pos)[0]
        self.pos += 4
        return v

    def raw(self, n):
        if self.pos + n > len(self.data):
            raise Unreadable('the file ends at byte %d' % len(self.data))
        v = self.data[self.pos:self.pos + n]
        self.pos += n
        return v

    def s(self):
        e = self.data.find(b'\0', self.pos)
        if e < 0:
            raise Unreadable('a string without its NUL at byte %d' % self.pos)
        v = self.data[self.pos:e]
        self.pos = e + 1
        return v


def read_w3i(data):
    r = _Reader(data)
    try:
        m = _w3i_header(r)
    except struct.error as e:
        raise Unreadable('w3i: %s' % e)
    start = r.pos
    for hud in ((True, False) if m['version'] >= 37 else (False,)):
        r.pos = start
        try:
            _w3i_sections(r, m, hud)
        except (struct.error, Unreadable, ValueError):
            continue
        plausible = all(0 <= p['type'] <= 4 and 0 <= p['race'] <= 4 and 0 <= p['fixed_start'] <= 3
                        for p in m['players'])
        if r.pos == len(data) and plausible:
            return m
    raise Unreadable('w3i version %d does not close in a known layout' % m['version'])


def _w3i_header(r):
    m = {}
    v = m['version'] = r.i32()
    if v < 18:
        raise Unreadable('w3i version %d' % v)
    m['saves'], m['editor_version'] = r.i32(), r.i32()
    m['game_version'] = [r.i32() for _ in range(4)] if v >= 27 else None
    m['name'], m['author'], m['description'], m['players_recommended'] = r.s(), r.s(), r.s(), r.s()
    m['camera_bounds'] = [r.f32() for _ in range(8)]
    m['camera_complements'] = [r.i32() for _ in range(4)]
    m['width'], m['height'], m['flags'] = r.i32(), r.i32(), r.i32()
    m['tileset'] = r.raw(1).decode('latin-1')
    m['loading_index'] = r.i32()
    m['race_crest'] = r.i32() if v >= 37 else None
    m['loading_model'] = r.s() if v not in (18, 19) else b''
    m['loading_text'], m['loading_title'], m['loading_subtitle'] = r.s(), r.s(), r.s()
    m['game_data_set'] = r.i32()
    m['prologue_model'] = r.s() if v not in (18, 19) else b''
    m['prologue_text'], m['prologue_title'], m['prologue_subtitle'] = r.s(), r.s(), r.s()
    if v >= 19:
        m['fog'] = (r.i32(), r.f32(), r.f32(), r.f32(), r.raw(4))
    m['fog_heights'] = [r.f32() for _ in range(4)] if v >= 36 else None
    m['fog_extra'] = (r.f32(), r.i32()) if v >= 39 else None
    m['weather'] = r.raw(4) if v >= 21 else b'\0\0\0\0'
    m['sound_environment'] = r.s() if v >= 22 else b''
    m['light_environment'] = r.raw(1).decode('latin-1') if v >= 23 else '\0'
    m['water_color'] = r.raw(4) if v >= 25 else None
    m['script_language'] = r.i32() if v >= 28 else 0
    m['graphics_modes'] = r.i32() if v >= 29 else None
    m['game_data_version'] = r.i32() if v >= 30 else None
    m['camera_distances'] = [r.i32() for _ in range(2 if v == 32 else 3)] if v >= 32 else None
    m['hd_water'] = [r.i32() for _ in range(7)] + [r.raw(4)] if v >= 34 else None
    m['hd_water_envmap'] = r.i32() if v >= 35 else None
    m['minimap_alpha_color'] = r.raw(4) if v >= 38 else None
    return m


def _w3i_sections(r, m, hud):
    v = m['version']
    players = []
    for _ in range(r.i32()):
        p = {'number': r.i32(), 'type': r.i32(), 'race': r.i32()}
        p['hud'] = r.i32() if hud else None
        p['fixed_start'], p['name'], p['x'], p['y'] = r.i32(), r.s(), r.f32(), r.f32()
        p['ally_low'], p['ally_high'] = r.u32(), r.u32()
        p['enemy_low'], p['enemy_high'] = (r.u32(), r.u32()) if v >= 31 else (0, 0)
        players.append(p)
    m['players'] = players
    m['forces'] = [{'flags': r.i32(), 'players': r.u32(), 'name': r.s()} for _ in range(r.i32())]
    m['upgrades'] = [{'players': r.u32(), 'id': r.raw(4), 'level': r.i32(), 'availability': r.i32()}
                     for _ in range(r.i32())]
    m['techs'] = [{'players': r.u32(), 'id': r.raw(4)} for _ in range(r.i32())]
    groups = []
    for _ in range(r.i32()):
        g = {'number': r.i32(), 'name': r.s()}
        g['columns'] = [r.i32() for _ in range(r.i32())]
        g['rows'] = [(r.i32(), [r.raw(4) for _c in g['columns']]) for _ in range(r.i32())]
        groups.append(g)
    m['random_unit_groups'] = groups
    tables = []
    if v >= 24:
        for _ in range(r.i32()):
            t = {'number': r.i32(), 'name': r.s(), 'sets': []}
            for _s in range(r.i32()):
                t['sets'].append([(r.i32(), r.raw(4)) for _ in range(r.i32())])
            tables.append(t)
    m['random_item_tables'] = tables
    if v in (26, 27):
        m['script_language'] = r.i32()


def read_w3s(data):
    r = _Reader(data, 8)
    version, count = struct.unpack_from('<ii', data, 0)
    if version not in (1, 2, 3):
        raise Unreadable('w3s version %d' % version)
    sounds = []
    try:
        for _ in range(count):
            sounds.append(_w3s_sound(r, version))
    except struct.error as e:
        raise Unreadable('w3s: %s' % e)
    if r.pos != len(data):
        raise Unreadable('w3s: %d bytes left' % (len(data) - r.pos))
    return version, sounds


W3S_FIELDS = (('flags', 'i'), ('fade_in', 'i'), ('fade_out', 'i'), ('volume', 'i'), ('pitch', 'f'),
              ('pitch_variance', 'f'), ('priority', 'i'), ('channel', 'i'), ('min_distance', 'f'),
              ('max_distance', 'f'), ('cutoff', 'f'), ('cone_inside', 'f'), ('cone_outside', 'f'),
              ('cone_outside_volume', 'i'), ('cone_x', 'f'), ('cone_y', 'f'), ('cone_z', 'f'))
W3S_V2_FIELDS = (('name2', 's'), ('label', 's'), ('path2', 's'), ('text_key', 'i'), ('text', 's'),
                 ('speaker_key', 'i'), ('speaker', 's'), ('facial_flag', 'i'), ('facial_unit', 's'),
                 ('facial_label', 's'), ('facial_group', 's'), ('facial_path', 's'))


def _w3s_sound(r, version):
    snd = {'name': r.s(), 'path': r.s(), 'eax': r.s()}
    for key, kind in W3S_FIELDS:
        snd[key] = r.f32() if kind == 'f' else r.i32()
    if version >= 2:
        for key, kind in W3S_V2_FIELDS:
            snd[key] = r.s() if kind == 's' else r.i32()
    if version >= 3:
        snd['v3_flag'] = r.i32()
    return snd


def write_w3s(version, sounds):
    out = [struct.pack('<ii', version, len(sounds))]
    for snd in sounds:
        out.append(snd['name'] + b'\0' + snd['path'] + b'\0' + snd['eax'] + b'\0')
        for key, kind in W3S_FIELDS:
            out.append(struct.pack('<f' if kind == 'f' else '<i', snd[key]))
        if version >= 2:
            for key, kind in W3S_V2_FIELDS:
                out.append(snd[key] + b'\0' if kind == 's' else struct.pack('<i', snd[key]))
        if version >= 3:
            out.append(struct.pack('<i', snd['v3_flag']))
    return b''.join(out)


def read_doo(data):
    from doctor.fix import doodads
    try:
        d = doodads.read_data(data)
    except Exception as e:
        raise Unreadable('war3map.doo: %s' % e)
    if not d.get('on_close'):
        raise Unreadable('war3map.doo does not close in a known layout')
    v, skin = d['version_num'], d['skin']
    out = []
    for index, reg in enumerate(d['regs']):
        r = _Reader(data, reg['begin'])
        x = {'index': index, 'id': r.raw(4), 'variation': r.i32(), 'x': r.f32(), 'y': r.f32(), 'z': r.f32(),
             'angle': r.f32(), 'scale': (r.f32(), r.f32(), r.f32())}
        x['skin'] = r.raw(4) if skin else x['id']
        x['group'] = r.i32() if v >= 12 else None
        x['flags'] = r.raw(1)[0] if v >= 6 else 2
        x['life'] = r.raw(1)[0]
        x['item_table'], x['item_sets'] = -1, []
        if v >= 7:
            x['item_table'] = r.i32()
            for _s in range(r.i32()):
                x['item_sets'].append([(r.raw(4), r.i32()) for _ in range(r.i32())])
        x['color'] = r.i32() if v >= 13 else -1
        x['editor_id'] = r.i32() if v >= 4 else None
        x['pitch'] = x['roll'] = 0.0
        if v >= 12:
            x['roll'], x['pitch'] = r.f32(), r.f32()
            r.raw(4 + 36 * struct.unpack_from('<i', data, r.pos)[0])
        out.append(x)
    return v, d['subversion'], out


class Style(object):
    def __init__(self, editor):
        self.editor = editor or EDITOR_3
        e = self.editor
        self.skins = e >= 6105
        self.pitch_roll = e >= 6117
        self.colors = e >= 7000
        self.item_filter = e >= 7000
        self.race_skin = e >= 7000
        self.camera_locals = e >= 6071
        self.camera_depth = e >= 6117


EMPATE_PAR = [False]
EDITOR_EMPATE_PAR = 6116


def real(v, digits=1):
    if EMPATE_PAR[0]:
        return '%.*f' % (digits, v)
    try:
        return str(decimal.Decimal(v).quantize(decimal.Decimal(1).scaleb(-digits), rounding=decimal.ROUND_HALF_UP))
    except (decimal.InvalidOperation, ValueError, TypeError):
        return '%.*f' % (digits, v)


def rawcode(b):
    return "'%s'" % (b.decode('latin-1') if isinstance(b, bytes) else b)


def jstring(b):
    s = b.decode('utf-8', 'surrogateescape') if isinstance(b, bytes) else b
    return '"%s"' % s.replace('\\', '\\\\').replace('"', '\\"')


def identifier(name):
    if isinstance(name, bytes):
        name = name.decode('utf-8', 'surrogateescape')
    return gui_render.trigger_identifier(name)


def _call(name, *args):
    return 'call %s( %s )' % (name, ', '.join(args)) if args else 'call %s(  )' % name


def _function(name, body, locals_=(), returns='nothing'):
    lines = ['function %s takes nothing returns %s' % (name, returns)]
    lines += ['    local %s' % x for x in locals_]
    lines += [('    ' + x) if x else '' for x in body]
    lines.append('endfunction')
    return '\n'.join(lines) + '\n'


class GameData(object):
    _game = None
    TINTS = {}
    ABILITIES = {}
    ABILITY_IDS = set()
    ABILITY_FILES = ('campaign', 'common', 'human', 'item', 'neutral', 'nightelf', 'orc', 'undead')

    def __init__(self, files=None, casc=None):
        self._casc = casc
        self.files = files or {}

    @property
    def files(self):
        return self._files

    @files.setter
    def files(self, files):
        self._files = files or {}
        self.units, self.items, self.colors, self.bases, self.orders, self.dests = {}, set(), {}, {}, {}, set()
        self.tints, self.abilities = {}, {}
        self._custom()

    @classmethod
    def game(cls, casc=None):
        if cls._game is None:
            from doctor.data import slk
            units, items, colors, orders, dests = {}, set(), {}, {}, set()
            try:
                if casc is None:
                    from doctor.data import casc_wc3
                    casc = casc_wc3.CascWC3()
                _h, rows = slk.parse_slk_bytes_memo(casc.read_wc3('units\\unitbalance.slk'))
                for k, row in rows.items():
                    units[k.encode('latin-1')] = (row.get('isbldg') or '0').strip() == '1'
                _h, rows = slk.parse_slk_bytes_memo(casc.read_wc3('units\\itemdata.slk'))
                items = set(k.encode('latin-1') for k in rows)
                for k, row in rows.items():
                    colors[k.encode('latin-1')] = (_int(row.get('teamColor'), -1), _int(row.get('customTeamColor'), 0))
                _h, rows = slk.parse_slk_bytes_memo(casc.read_wc3('units\\destructabledata.slk'))
                dests = set(k.encode('latin-1') for k in rows)
                _h, rows = slk.parse_slk_bytes_memo(casc.read_wc3('units\\abilitydata.slk'))
                cls.ABILITY_IDS.update(k.encode('latin-1') for k in rows)
                _h, rows = slk.parse_slk_bytes_memo(casc.read_wc3('units\\unitabilities.slk'))
                for k, row in rows.items():
                    cls.ABILITIES[k.encode('latin-1')] = (row.get('abilList') or '').replace('"', '')
                _h, rows = slk.parse_slk_bytes_memo(casc.read_wc3('units\\unitui.slk'))
                for k, row in rows.items():
                    colors[k.encode('latin-1')] = (_int(row.get('teamColor'), -1), _int(row.get('customTeamColor'), 0))
                current = None
                for line in casc.read_wc3('units\\destructableskin.txt').decode('utf-8', 'replace').splitlines():
                    line = line.strip()
                    m = re.match(r'^\[(\w{4})\]$', line)
                    if m:
                        current = cls.TINTS.setdefault(m.group(1).encode('latin-1'), [255, 255, 255])
                    elif current is not None and line[:7] in ('colorR=', 'colorG=', 'colorB='):
                        current['RGB'.index(line[5])] = _int(line[7:], 255)
                for name in cls.ABILITY_FILES:
                    try:
                        text = casc.read_wc3('units\\%sabilityfunc.txt' % name).decode('utf-8', 'replace')
                    except Exception:
                        continue
                    current = None
                    for line in text.splitlines():
                        line = line.strip()
                        m = re.match(r'^\[(\w{4})\]$', line)
                        if m:
                            current = orders.setdefault(m.group(1).encode('latin-1'), {})
                        elif current is not None and '=' in line:
                            key, value = line.split('=', 1)
                            if key.lower() in ('order', 'orderon', 'orderoff', 'unorder'):
                                current.setdefault(key.lower(), value.strip())
            except Exception:
                pass
            cls._game = (units, items, colors, orders, dests)
        return cls._game

    OBJECT_FILES = (('war3map.w3u', 'unit', False), ('war3mapSkin.w3u', 'unit', False),
                    ('war3map.w3t', 'item', False), ('war3mapSkin.w3t', 'item', False),
                    ('war3map.w3a', 'ability', True), ('war3mapSkin.w3a', 'ability', True),
                    ('war3map.w3b', 'destructable', False), ('war3mapSkin.w3b', 'destructable', False))

    def _custom(self):
        from doctor.data import objbin
        units, _items, colors, orders, _dests = self.game(self._casc)
        for name, kind, levels in self.OBJECT_FILES:
            data = self._files.get(name)
            if not data:
                continue
            try:
                _v, tables, _p = objbin.read_data(data, levels)
            except Exception:
                continue
            for objs in tables:
                for old_text, new_text, mods in objs:
                    old = old_text.encode('latin-1')
                    ident = new_text.encode('latin-1') if new_text != '\0\0\0\0' else old
                    self.bases.setdefault(ident, old)
                    fields = dict((mid, val) for mid, _vt, _lvl, _dptr, val in mods)
                    number = dict((mid, struct.unpack('<i', val)[0]) for mid, val in fields.items()
                                  if isinstance(val, bytes) and len(val) == 4)
                    if kind == 'item':
                        self.items.add(ident)
                        color = list(self.colors.get(ident) or colors.get(old, (-1, 0)))
                        color[0], color[1] = number.get('itco', color[0]), number.get('itcc', color[1])
                        self.colors[ident] = tuple(color)
                    elif kind == 'destructable':
                        self.dests.add(ident)
                        tint = list(self.tints.get(ident) or self.TINTS.get(old, (255, 255, 255)))
                        for k, mid in enumerate(('bvcr', 'bvcg', 'bvcb')):
                            tint[k] = number.get(mid, tint[k])
                        self.tints[ident] = tuple(tint)
                    elif kind == 'ability':
                        base = self.orders.get(ident) or dict(orders.get(old, {}))
                        for mid, key in (('aord', 'order'), ('aoro', 'orderon'), ('aorf', 'orderoff'),
                                         ('aoru', 'unorder')):
                            if isinstance(fields.get(mid), bytes):
                                base[key] = fields[mid].decode('latin-1')
                                base['__mapa__'] = tuple(set(base.get('__mapa__', ())) | {key})
                        self.orders[ident] = base
                    else:
                        building = self.units.get(ident, units.get(old))
                        if 'ubdg' in number:
                            building = number['ubdg'] != 0
                        color = list(self.colors.get(ident) or colors.get(old, (-1, 0)))
                        color[0], color[1] = number.get('utco', color[0]), number.get('utcc', color[1])
                        if isinstance(fields.get('uabi'), bytes):
                            self.abilities[ident] = fields['uabi'].decode('latin-1')
                        self.units[ident] = building
                        self.colors[ident] = tuple(color)

    @property
    def available(self):
        return bool(self.game(self._casc)[0])

    def base(self, ident):
        return self.bases.get(ident, ident)

    def is_building(self, ident):
        if ident in self.units:
            return self.units[ident]
        return self.game(self._casc)[0].get(ident)

    def is_destructable(self, ident):
        dests = self.game(self._casc)[4]
        if not dests:
            return None
        return ident in self.dests or ident in dests

    def is_item(self, ident):
        units, items, _c, _o, _d = self.game(self._casc)
        if ident in self.items or ident in items:
            return True
        return False if (ident in self.units or ident in units) else None

    def team_color(self, ident):
        return self.colors.get(ident) or self.game(self._casc)[2].get(ident)

    def ability_orders(self, ident):
        return self.orders.get(ident) or self.game(self._casc)[3].get(ident)

    def is_ability(self, ident):
        self.game(self._casc)
        if ident in self.orders or ident in self.ABILITY_IDS:
            return True
        return False if self.is_building(ident) is not None else None

    def has_ability(self, ident, ability):
        self.game(self._casc)
        abilities = self.abilities.get(ident)
        if abilities is None:
            abilities = self.ABILITIES.get(self.base(ident))
        return None if abilities is None else ability in abilities.split(',')

    def tint(self, ident):
        self.game(self._casc)
        return self.tints.get(ident) or tuple(self.TINTS.get(ident, (255, 255, 255)))


def _int(text, default):
    try:
        return int(str(text).strip())
    except (TypeError, ValueError):
        return default


class Rendering(object):
    def __init__(self, style):
        self.style = style
        self.globals = []
        self._names = set()
        self.functions = collections.OrderedDict()
        self.unknown = {}
        self.notes = []

    def add(self, name, text):
        self.functions[name] = text

    def declare(self, type_, name, is_array=False, value=None):
        if name not in self._names:
            self._names.add(name)
            self.globals.append((type_, name, is_array, value))

    def declared(self):
        return [g[1] for g in self.globals]

    def globals_text(self, extra=''):
        lines = ['globals']
        for t, n, arr, v in self.globals:
            decl = '%s array' % t if arr else t
            lines.append(('    %-23s %-26s = %s' % (decl, n, v)) if v is not None else ('    %-23s %s' % (decl, n)))
        return '\n'.join(lines) + '\n' + extra + 'endglobals\n'


def read_w3c(data):
    d = inflated_counts.read_w3c(data)
    if not d or d['remaining'] != 0 or len(d['regs']) != d['declared']:
        raise Unreadable('w3c does not close')
    news, depth = d.get('layout') or (False, False)
    r = _Reader(data, 8)
    out = []
    for _ in range(d['declared']):
        c = {'x': r.f32(), 'y': r.f32(), 'z': r.f32(), 'rotation': r.f32(), 'aoa': r.f32(), 'distance': r.f32(),
             'roll': r.f32(), 'fov': r.f32(), 'far': r.f32(), 'near': r.f32()}
        c['local'] = [r.f32() for _ in range(3)] if news else [0.0, 0.0, 0.0]
        c['depth'] = [r.f32() for _ in range(3)] if depth else [0.0, 0.0, 0.0]
        c['name'] = r.s()
        c['type'] = r.i32() if depth else 0
        out.append(c)
    return d['version_num'], out


def read_w3r(data):
    d = inflated_counts.read_w3r(data)
    if d['remaining'] != 0 or len(d['regs']) != d['declared']:
        raise Unreadable('w3r does not close')
    return d['version_num'], d['regs']


def read_units(data):
    d = inflated_counts.read_units_doo(data)
    if not d.get('on_close'):
        raise Unreadable('war3mapUnits.doo does not close')
    return d['regs']


class Terrain(object):
    def __init__(self, data):
        if data[:4] != b'W3E!':
            raise Unreadable('w3e')
        r = _Reader(data, 4)
        self.size = 8 if r.i32() >= 12 else 7
        r.raw(1)
        r.i32()
        r.raw(4 * r.i32())
        r.raw(4 * r.i32())
        self.w, self.h = r.i32(), r.i32()
        self.ox, self.oy = r.f32(), r.f32()
        self.data, self.base = data, r.pos

    def point(self, i, j):
        i = min(max(i, 0), self.w - 1)
        j = min(max(j, 0), self.h - 1)
        p = self.base + self.size * (j * self.w + i)
        height = struct.unpack_from('<h', self.data, p)[0]
        layer = self.data[p + self.size - 1] & 0x0F
        return (height - 0x2000 + (layer - 2) * 0x200) / 4.0

    def height(self, x, y):
        fx, fy = (x - self.ox) / 128.0, (y - self.oy) / 128.0
        i, j = int(math.floor(fx)), int(math.floor(fy))
        dx, dy = fx - i, fy - j
        a, b = self.point(i, j), self.point(i + 1, j)
        c, d = self.point(i, j + 1), self.point(i + 1, j + 1)
        return (a * (1 - dx) + b * dx) * (1 - dy) + (c * (1 - dx) + d * dx) * dy


def region_name(reg):
    return 'gg_rct_' + identifier(reg['fname'])


def render_regions(regions, st, terrain=None):
    body = ['']
    for reg in regions:
        var = region_name(reg)
        l, b, r, t = reg['rect']
        body.append('set %s = Rect( %s, %s, %s, %s )' % (var, real(l), real(b), real(r), real(t)))
        weather = reg.get('weather') or b'\0\0\0\0'
        if weather.strip(b'\0'):
            body.append('set we = AddWeatherEffect( %s, %s )' % (var, rawcode(weather)))
            body.append(_call('EnableWeatherEffect', 'we', 'true'))
        sound = reg.get('sound') or b''
        if sound:
            cx, cy = (l + r) / 2.0, (b + t) / 2.0
            z = terrain.height(cx, cy) if terrain is not None else 0.0
            name = sound.decode('latin-1')
            body.append(_call('SetSoundPosition', name, real(cx), real(cy), '%.1f' % z))
            body.append(_call('RegisterStackedSound', name, 'true', real(r - l), real(t - b)))
    return _function('CreateRegions', body, ('weathereffect we',))


CAMERA_FIELDS = (('ZOFFSET', 'z'), ('ROTATION', 'rotation'), ('ANGLE_OF_ATTACK', 'aoa'),
                 ('TARGET_DISTANCE', 'distance'), ('ROLL', 'roll'), ('FIELD_OF_VIEW', 'fov'), ('FARZ', 'far'))


def camera_name(cam):
    return 'gg_cam_' + identifier(cam['name'])


def render_cameras(cameras, st):
    body = ['']
    for c in cameras:
        var = camera_name(c)
        body.append('set %s = CreateCameraSetup(  )' % var)
        fields = [(f, c[k]) for f, k in CAMERA_FIELDS]
        if st.camera_locals:
            fields += [('NEARZ', c['near']), ('LOCAL_PITCH', c['local'][0]), ('LOCAL_YAW', c['local'][1]),
                       ('LOCAL_ROLL', c['local'][2])]
        if st.camera_depth:
            fields += [('DEPTH_OF_FIELD_DISTANCE', c['depth'][0]), ('DEPTH_OF_FIELD_SCALE', c['depth'][1]),
                       ('ZABSOLUTE', c['depth'][2])]
        for f, v in fields:
            body.append(_call('CameraSetupSetField', var, 'CAMERA_FIELD_' + f, real(v), '0.0'))
        body.append(_call('CameraSetupSetDestPosition', var, real(c['x']), real(c['y']), '0.0'))
        if st.camera_depth:
            body.append(_call('BlzCameraSetupSetCameraType', var, str(c['type'])))
        body.append('')
    return _function('CreateCameras', body)


def sound_is_music(snd):
    return bool(snd['flags'] & 8)


def render_sounds(sounds, st, durations=None):
    body = []
    exact = True
    for snd in sounds:
        var = snd['name'].decode('latin-1')
        path = jstring(snd['path'])
        if sound_is_music(snd):
            body.append('set %s = %s' % (var, path))
            continue
        f = snd['flags']
        body.append('set %s = CreateSound( %s, %s, %s, %s, %d, %d, %s )' % (
            var, path, _bool(f & 1), _bool(f & 2), _bool(f & 4), snd['fade_in'], snd['fade_out'], jstring(snd['eax'])))
        label = snd.get('label')
        if label:
            body.append(_call('SetSoundParamsFromLabel', var, jstring(label)))
        for key, setter in (('facial_label', 'SetSoundFacialAnimationLabel'),
                            ('facial_group', 'SetSoundFacialAnimationGroupLabel'),
                            ('facial_path', 'SetSoundFacialAnimationSetFilepath')):
            if snd.get(key):
                body.append(_call(setter, var, jstring(snd[key])))
        if snd.get('speaker_key', -1) != -1:
            body.append(_call('SetDialogueSpeakerNameKey', var, '"TRIGSTR_%d"' % snd['speaker_key']))
        if snd.get('text_key', -1) != -1:
            body.append(_call('SetDialogueTextKey', var, '"TRIGSTR_%d"' % snd['text_key']))
        ms = (durations or {}).get(var)
        if ms is None:
            exact = False
            ms = 0
        body.append(_call('SetSoundDuration', var, str(ms)))
        if snd['channel'] != -1 or not label:
            body.append(_call('SetSoundChannel', var, str(max(snd['channel'], 0))))
        if snd['volume'] != -1 or not label:
            body.append(_call('SetSoundVolume', var, str(snd['volume'])))
        if snd['pitch'] != DEFAULT_FLOAT:
            body.append(_call('SetSoundPitch', var, real(snd['pitch'])))
        if f & 2:
            if snd['min_distance'] != DEFAULT_FLOAT:
                body.append(_call('SetSoundDistances', var, real(snd['min_distance']), real(snd['max_distance'])))
            if snd['cutoff'] != DEFAULT_FLOAT:
                body.append(_call('SetSoundDistanceCutoff', var, real(snd['cutoff'])))
            if snd['cone_inside'] != DEFAULT_FLOAT:
                body.append(_call('SetSoundConeAngles', var, real(snd['cone_inside']), real(snd['cone_outside']),
                                  str(snd['cone_outside_volume'])))
            if snd['cone_x'] != DEFAULT_FLOAT:
                body.append(_call('SetSoundConeOrientation', var, real(snd['cone_x']), real(snd['cone_y']),
                                  real(snd['cone_z'])))
    return _function('InitSounds', body), exact


def _bool(v):
    return 'true' if v else 'false'


ITEM_CLASSES = dict((letter, cls) for cls, letter in inflated_counts.ITEM_CLASS_LETTER.items())


def item_code(ident, st):
    if ident == b'\0\0\0\0':
        return '-1'
    s = ident.decode('latin-1')
    if len(s) == 4 and s[0] == 'Y' and s[2] == 'I' and s[1] in ITEM_CLASSES and (s[3] == '/' or 48 <= ord(s[3]) <= 63):
        cls, level = ITEM_CLASSES[s[1]], (-1 if s[3] == '/' else ord(s[3]) - 48)
        if st.item_filter:
            return 'ChooseRandomItemExWithFilter( %s, %d, EQUIPMENT_TYPE_ANY, ITEMTAG_TYPE_ANY )' % (cls, level)
        return 'ChooseRandomItemEx( %s, %d )' % (cls, level)
    return rawcode(ident)


def render_drop(name, sets, st):
    body = ['', 'set trigWidget = bj_lastDyingWidget', 'if (trigWidget == null) then',
            '    set trigUnit = GetTriggerUnit()', 'endif', '', 'if (trigUnit != null) then',
            '    set canDrop = not IsUnitHidden(trigUnit)', '    if (canDrop and GetChangingUnit() != null) then',
            '        set canDrop = (GetChangingUnitPrevOwner() == Player(PLAYER_NEUTRAL_AGGRESSIVE))',
            '    endif', 'endif', '', 'if (canDrop) then']
    for k, items in enumerate(sets):
        body.append('    // Item set %d' % k)
        body.append('    ' + _call('RandomDistReset'))
        for ident, chance in items:
            body.append('    ' + _call('RandomDistAddItem', item_code(ident, st), str(chance)))
        rest = 100 - sum(chance for _i, chance in items)
        if 0 < rest < 100 and not st.pitch_roll:
            body.append('    ' + _call('RandomDistAddItem', '-1', str(rest)))
        body += ['    set itemID = RandomDistChoose(  )', '    if (trigUnit != null) then',
                 '        ' + _call('UnitDropItem', 'trigUnit', 'itemID'), '    else',
                 '        ' + _call('WidgetDropItem', 'trigWidget', 'itemID'), '    endif', '']
    body += ['endif', '', 'set bj_lastDyingWidget = null', 'call DestroyTrigger(GetTriggeringTrigger())']
    return _function(name, body, ('widget  trigWidget = null', 'unit    trigUnit   = null',
                                  'integer itemID     = 0', 'boolean canDrop    = true'))


_F32 = struct.Struct('<f')
_DEG_PER_RAD = _F32.unpack(_F32.pack(180.0 / math.pi))[0]


def degrees(radians):
    return real(_F32.unpack(_F32.pack(radians * _DEG_PER_RAD))[0], 3)


def unit_var(u, referenced):
    name = 'gg_unit_%s_%04d' % (u['ident'].decode('latin-1'), u['creation'])
    return name if name in referenced else 'u'


def dest_var(d, referenced):
    name = 'gg_dest_%s_%04d' % (d['id'].decode('latin-1'), d['editor_id'])
    return name if name in referenced else 'd'


def item_var(it, referenced):
    name = 'gg_item_%s_%04d' % (it['ident'].decode('latin-1'), it['creation'])
    return name if name in referenced else None


def _drop_trigger(var, function, register):
    return ['set t = CreateTrigger(  )'] + [_call(register, 't', var, e) for e in (
        ('EVENT_UNIT_DEATH', 'EVENT_UNIT_CHANGE_OWNER') if register == 'TriggerRegisterUnitEvent' else ())] + \
        ([_call('TriggerRegisterDeathEvent', 't', var), _call('TriggerAddAction', 't', 'function SaveDyingWidget')]
         if register != 'TriggerRegisterUnitEvent' else []) + [_call('TriggerAddAction', 't', 'function ' + function)]


def render_destructables(doodads, referenced, st, game=None):
    chosen = [d for d in doodads if _dest_needed(d, referenced)]
    chosen.sort(key=lambda d: d['id'])
    body = []
    for d in chosen:
        var = dest_var(d, referenced)
        dead = d['life'] == 0
        fixed_z = bool(d['flags'] & 4)
        ident = rawcode(d['id'])
        args = [ident, real(d['x']), real(d['y'])] + ([real(d['z'])] if fixed_z else []) + [degrees(d['angle'])]
        if st.pitch_roll:
            args += [degrees(d['pitch']), degrees(d['roll'])]
        args += [real(d['scale'][0], 3), str(d['variation'])]
        name = ('BlzCreateDeadDestructable' if dead else 'BlzCreateDestructable') if st.skins else \
            ('CreateDeadDestructable' if dead else 'CreateDestructable')
        if fixed_z:
            name += 'Z'
        if st.skins:
            name += 'WithSkin' + ('PitchRoll' if st.pitch_roll else '') + ('Color' if st.colors else '')
            args.append(rawcode(d['skin']))
            if st.colors:
                args.append('ConvertPlayerColor(%d)' % (24 if d['color'] == -1 else d['color']))
        body.append('set %s = %s( %s )' % (var, name, ', '.join(args)))
        if st.colors:
            tint = game.tint(d['id']) if game is not None else (255, 255, 255)
            body.append(_call('SetDestructableVertexColor', var, *[str(c) for c in tint] + ['255']))
        if 0 < d['life'] < 100:
            body.append('set life = GetDestructableLife( %s )' % var)
            body.append(_call('SetDestructableLife', var, '%s * life' % real(d['life'] / 100.0, 2)))
        if d['item_table'] != -1:
            body += _drop_trigger(var, 'ItemTable%06d_DropItems' % d['item_table'], 'TriggerRegisterDeathEvent')
        elif any(d['item_sets']):
            body += _drop_trigger(var, 'Doodad%06d_DropItems' % d['index'], 'TriggerRegisterDeathEvent')
    return _function('CreateAllDestructables', body, ('destructable d', 'trigger t', 'real life'))


def _dest_needed(d, referenced):
    if ('gg_dest_%s_%04d' % (d['id'].decode('latin-1'), d['editor_id'])) in referenced:
        return True
    if not d.get('destructable', True):
        return False
    return d['item_table'] != -1 or any(d['item_sets'])


RX_DEST_BLOCK = re.compile(r"(?m)^(?=set \w+=\w*Destructable\w*\((\w{4}),)")
RX_ITEM_BLOCK = re.compile(r"(?m)^(?=(?:set \w+=|call )\w*CreateItem\w*\((\w{4}),)")


def _destructable_blocks(canonical_text, rx=RX_DEST_BLOCK):
    body = canonical_text
    if body.endswith('\nendfunction'):
        body = body[:-len('\nendfunction')]
    parts = rx.split(body)
    head, groups = parts[0], collections.defaultdict(list)
    for k in range(1, len(parts), 2):
        groups[parts[k]].append(parts[k + 1].strip())
    return head.strip(), dict((k, sorted(v)) for k, v in groups.items()), [parts[k] for k in range(1, len(parts), 2)]


def render_items(items, referenced, st, game=None):
    body = ['']
    for it in sorted(items, key=lambda u: u['ident']):
        var = item_var(it, referenced)
        x, y = real(it['xyz'][0]), real(it['xyz'][1])
        ident = rawcode(it['ident'])
        if st.skins:
            call = 'BlzCreateItemWithSkin( %s, %s, %s, %s )' % (ident, x, y, rawcode(it['skin_id'] or it['ident']))
        else:
            call = 'CreateItem( %s, %s, %s )' % (ident, x, y)
        if st.colors:
            var = var or 'i'
            body.append('set %s = %s' % (var, call))
            color = unit_color(it, game)
            body.append(_call('SetItemColor', var, 'ConvertPlayerColor(%d)' % (24 if color == -1 else color)))
        elif var:
            body.append('set %s = %s' % (var, call))
        else:
            body.append('call ' + call)
    locals_ = ('integer itemID', 'item i') if st.colors else ('integer itemID',)
    return _function('CreateAllItems', body, locals_)


GOLD_MINES = frozenset((b'ngol', b'ugol', b'egol'))


def _ability_lines(var, abilities, game, hero=False):
    out = []
    for hid, autocast, level in abilities:
        for _k in range(level):
            out.append(_call('SelectHeroSkill', var, rawcode(hid)))
        if hero and not level:
            continue
        orders = ((game.ability_orders(hid) or game.ability_orders(game.base(hid))) if game is not None else None) or {}
        key = ('orderon' if orders.get('orderon') or 'orderon' in orders.get('__mapa__', ()) else 'order') \
            if autocast else 'orderoff'
        order = orders.get(key)
        if order is None and not autocast and game is not None and hid in game.orders and game.base(hid) != hid:
            order = ''
            orders = dict(orders, __mapa__=tuple(orders.get('__mapa__', ())) + (key,))
        if order or (order == '' and key in orders.get('__mapa__', ())):
            out.append(_call('IssueImmediateOrder', var, '"%s"' % order))
    return out


def unit_color(u, game, so_mapa=False):
    if so_mapa:
        tc = game.colors.get(u['ident']) if game is not None else None
        if tc is None:
            return u['color']
        return u['color'] if tc[1] and u['color'] != -1 else tc[0]
    tc = (game.team_color(u['ident']) or game.team_color(game.base(u['ident']))) if game is not None else None
    if tc is None:
        return u['color']
    return u['color'] if tc[1] and u['color'] != -1 else tc[0]


def unit_statements(u, index, referenced, regions, st, game=None, neutral_base=None):
    var = unit_var(u, referenced)
    out = []
    x, y, face = real(u['xyz'][0]), real(u['xyz'][1]), degrees(u['angle'])
    ident = u['ident']
    random_unit = ident in (b'uDNR', b'bDNR')
    head = []
    if random_unit:
        if u['rnd'] == 0 and u['block_entry']:
            head.append('set unitID = ChooseRandomCreep( %d )' % _signed24(u['block_entry'][0]))
        elif u['rnd'] == 1 and u['block_entry']:
            head.append('set unitID = gg_rg_%03d[%d]' % tuple(u['block_entry']))
        elif u['rnd'] == 2:
            head.append(_call('RandomDistReset'))
            for uid, chance in u['block_entry'] or ():
                head.append(_call('RandomDistAddItem', rawcode(uid), str(chance)))
            head.append('set unitID = RandomDistChoose(  )')
        created = ('BlzCreateUnitWithSkin( p, unitID, %s, %s, %s, unitID )' % (x, y, face) if st.skins else
                   'CreateUnit( p, unitID, %s, %s, %s )' % (x, y, face))
    elif ident == b'ugol':
        created = 'CreateBlightedGoldmine( p, %s, %s, %s )' % (x, y, face)
    elif st.skins:
        created = 'BlzCreateUnitWithSkin( p, %s, %s, %s, %s, %s )' % (rawcode(ident), x, y, face,
                                                                       rawcode(u['skin_id'] or ident))
    else:
        created = 'CreateUnit( p, %s, %s, %s, %s )' % (rawcode(ident), x, y, face)
    out.append('set %s = %s' % (var, created))
    base = game.base(ident) if game is not None else ident
    if base in GOLD_MINES:
        out.append(_call('SetResourceAmount', var, str(u['gold'])))
    if u['hp'] != -1:
        out.append('set life = GetUnitState( %s, UNIT_STATE_LIFE )' % var)
        out.append(_call('SetUnitState', var, 'UNIT_STATE_LIFE', '%s * life' % real(u['hp'] / 100.0, 2)))
    if u['level'] > 1:
        out.append(_call('SetHeroLevel', var, str(u['level']), 'false'))
    for stat, value in zip(('SetHeroStr', 'SetHeroAgi', 'SetHeroInt'), u['hero_attributes'] or ()):
        if value:
            out.append(_call(stat, var, str(value), 'true'))
    if u['mana'] != -1:
        out.append(_call('SetUnitState', var, 'UNIT_STATE_MANA', str(u['mana'])))
    if u['acq'] == -2.0:
        out.append(_call('SetUnitAcquireRange', var, '200.0'))
    elif u['acq'] >= 0 and not random_unit:
        out.append(_call('SetUnitAcquireRange', var, real(u['acq'])))
    out += _ability_lines(var, u['abilities'], game, ident[:1].isupper())
    if u['uprooted']:
        out.append(_call('IssueImmediateOrder', var, '"unroot"'))
    for slot, iid in u['inventory']:
        out.append(_call('UnitAddItemToSlotById', var, rawcode(iid), str(slot)))
    waygate = game.has_ability(ident, 'Awrp') if game is not None else None
    if u['waygate'] != -1 and regions is not None and waygate is not False:
        target = regions.get(u['waygate'])
        if target:
            out.append(_call('WaygateSetDestination', var, 'GetRectCenterX(%s)' % target,
                             'GetRectCenterY(%s)' % target))
            out.append(_call('WaygateActivate', var, 'true'))
    color = unit_color(u, game, so_mapa=not st.skins)
    dono = u['owner'] + 12 if neutral_base == 12 and u['owner'] >= 12 else u['owner']
    if color != -1 and color != dono:
        out.append(_call('SetUnitColor', var, 'ConvertPlayerColor(%d)' % color))
    if u['itp'] != -1:
        out += _drop_trigger(var, 'ItemTable%06d_DropItems' % u['itp'], 'TriggerRegisterUnitEvent')
    elif any(u['set_items']):
        out += _drop_trigger(var, 'Unit%06d_DropItems' % index, 'TriggerRegisterUnitEvent')
    if random_unit:
        return head + ['if ( unitID != -1 ) then'] + ['    ' + x for x in out] + ['endif']
    return out


def _signed24(v):
    return v - (1 << 24) if v & 0x800000 else v


UNIT_LOCALS = ('unit u', 'integer unitID', 'trigger t', 'real life')


def _player_function(name, player, units, referenced, regions, st, game=None, neutral_base=None):
    body = ['']
    owner = 'Player(%s)' % player
    for index, u in sorted(units, key=lambda iu: iu[1]['creation']):
        body += unit_statements(u, index, referenced, regions, st, game, neutral_base)
    return _function(name, body, ('player p = %s' % owner,) + UNIT_LOCALS)


def render_units(records, referenced, regions, st, game, neutral_base, hints=None):
    groups = collections.OrderedDict()
    hostile, passive = neutral_base, neutral_base + 3
    for index, u in enumerate(records):
        ident = u['ident']
        if ident == b'sloc' or u.get('item'):
            continue
        if ident == b'uDNR':
            building = False
        elif ident == b'bDNR':
            building = True
        else:
            building = game.is_building(ident)
            if building is None:
                building = (hints or {}).get(ident)
            if building is None:
                building = degrees(u['angle']) == '270.000'
        owner = u['owner']
        if owner == hostile:
            key = ('hostile', building)
        elif owner == passive:
            key = ('passive', building)
        else:
            key = (owner, building)
        groups.setdefault(key, []).append((index, u))
    out = []
    players = sorted(k[0] for k in groups if isinstance(k[0], int))
    seen = []
    for p in players:
        if p in seen:
            continue
        seen.append(p)
        for building in (True, False):
            if (p, building) in groups:
                name = ('CreateBuildingsForPlayer%d' if building else 'CreateUnitsForPlayer%d') % p
                out.append((name, _player_function(name, p, groups[(p, building)], referenced, regions, st, game,
                                                   neutral_base)))
    for key, name, player in ((('hostile', True), 'CreateNeutralHostileBuildings', NEUTRAL_HOSTILE),
                              (('hostile', False), 'CreateNeutralHostile', NEUTRAL_HOSTILE),
                              (('passive', True), 'CreateNeutralPassiveBuildings', NEUTRAL_PASSIVE),
                              (('passive', False), 'CreateNeutralPassive', NEUTRAL_PASSIVE)):
        if key in groups:
            out.append((name, _player_function(name, player, groups[key], referenced, regions, st, game,
                                               neutral_base)))
    names = dict(out)
    pb = [_call('CreateBuildingsForPlayer%d' % p) for p in seen if 'CreateBuildingsForPlayer%d' % p in names]
    pu = [_call('CreateUnitsForPlayer%d' % p) for p in seen if 'CreateUnitsForPlayer%d' % p in names]
    out.append(('CreatePlayerBuildings', _function('CreatePlayerBuildings', pb)))
    out.append(('CreatePlayerUnits', _function('CreatePlayerUnits', pu)))
    calls = [_call(n) for n in ('CreateNeutralHostileBuildings', 'CreateNeutralPassiveBuildings') if n in names]
    calls.append(_call('CreatePlayerBuildings'))
    calls += [_call(n) for n in ('CreateNeutralHostile', 'CreateNeutralPassive') if n in names]
    calls.append(_call('CreatePlayerUnits'))
    out.append(('CreateAllUnits', _function('CreateAllUnits', calls)))
    return out


def render_upgrades(w3i_, st):
    per = collections.OrderedDict()
    numbers = [p['number'] for p in w3i_['players']]
    for up in w3i_['upgrades']:
        for n in numbers:
            if up['players'] & (1 << n):
                levels = per.setdefault(n, collections.OrderedDict()).setdefault(up['id'], {0: [], 2: []})
                if up['availability'] in levels:
                    levels[up['availability']].append(up['level'])
    out = []
    for n in sorted(per):
        body = []
        for ident, levels in per[n].items():
            if levels[0]:
                body.append(_call('SetPlayerTechMaxAllowed', 'Player(%d)' % n, rawcode(ident), str(min(levels[0]))))
            if levels[2]:
                body.append(_call('SetPlayerTechResearched', 'Player(%d)' % n, rawcode(ident),
                                  str(max(levels[2]) + 1)))
        if body:
            out.append(('InitUpgrades_Player%d' % n, _function('InitUpgrades_Player%d' % n, body)))
    if out:
        out.append(('InitUpgrades', _function('InitUpgrades', [_call(name) for name, _t in out])))
    return out


def render_techtree(w3i_, st, game=None):
    per = collections.OrderedDict()
    numbers = [p['number'] for p in w3i_['players']]
    for tech in w3i_['techs']:
        for n in numbers:
            if tech['players'] & (1 << n):
                per.setdefault(n, []).append(tech)
    out = []
    for n in sorted(per):
        body = []
        for tech in per[n]:
            ident = rawcode(tech['id'])
            if (game.is_ability(tech['id']) if game is not None else None) is not False and (
                    tech['id'][:1] == b'A' or (game is not None and game.is_ability(tech['id']))):
                body.append(_call('SetPlayerAbilityAvailable', 'Player(%d)' % n, ident, 'false'))
            else:
                body.append(_call('SetPlayerTechMaxAllowed', 'Player(%d)' % n, ident, '0'))
        out.append(('InitTechTree_Player%d' % n, _function('InitTechTree_Player%d' % n, body)))
    if out:
        out.append(('InitTechTree', _function('InitTechTree', [_call(name) for name, _t in out])))
    return out


RACES = {0: 'RACE_PREF_RANDOM', 1: 'RACE_PREF_HUMAN', 2: 'RACE_PREF_ORC', 3: 'RACE_PREF_UNDEAD',
         4: 'RACE_PREF_NIGHTELF'}
CONTROLLERS = {1: 'MAP_CONTROL_USER', 2: 'MAP_CONTROL_COMPUTER', 3: 'MAP_CONTROL_NEUTRAL',
               4: 'MAP_CONTROL_RESCUABLE'}
FORCE_ALLIED, FORCE_VICTORY, FORCE_VISION, FORCE_CONTROL, FORCE_FULL_CONTROL = 1, 2, 8, 16, 32


def render_player_slots(w3i_, st):
    body = ['']
    for k, p in enumerate(w3i_['players']):
        n = 'Player(%d)' % p['number']
        body.append('// Player %d' % p['number'])
        body.append(_call('SetPlayerStartLocation', n, str(k)))
        if p['fixed_start'] & 1:
            body.append(_call('ForcePlayerStartLocation', n, str(k)))
        body.append(_call('SetPlayerColor', n, 'ConvertPlayerColor(%d)' % p['number']))
        body.append(_call('SetPlayerRacePreference', n, RACES.get(p['race'], 'RACE_PREF_RANDOM')))
        if st.race_skin:
            body.append(_call('SetPlayerRaceSkin', n, 'RACE_PREF_USER_SELECTABLE'))
        body.append(_call('SetPlayerRaceSelectable', n, _bool(p['race'] == 0 or p['fixed_start'] & 2 or
                                                              not (w3i_.get('flags', 0) & 0x40))))
        body.append(_call('SetPlayerController', n, CONTROLLERS.get(p['type'], 'MAP_CONTROL_USER')))
        if p['type'] == 4:
            for q in w3i_['players']:
                if q['type'] == 1:
                    body.append(_call('SetPlayerAlliance', n, 'Player(%d)' % q['number'], 'ALLIANCE_RESCUABLE', 'true'))
        body.append('')
    return _function('InitCustomPlayerSlots', body)


def _force_players(w3i_, force):
    return [p['number'] for p in w3i_['players'] if force['players'] & (1 << p['number'])]


def render_teams(w3i_, st):
    body = []
    k = -1
    for f in w3i_['forces']:
        members = _force_players(w3i_, f)
        if not members:
            continue
        k += 1
        body.append('// Force: %s' % f['name'].decode('utf-8', 'surrogateescape'))
        for n in members:
            body.append(_call('SetPlayerTeam', 'Player(%d)' % n, str(k)))
            if f['flags'] & FORCE_VICTORY:
                body.append(_call('SetPlayerState', 'Player(%d)' % n, 'PLAYER_STATE_ALLIED_VICTORY', '1'))
        body.append('')
        for flag, title, setter in ((FORCE_ALLIED, 'Allied', 'SetPlayerAllianceStateAllyBJ'),
                                    (FORCE_VISION, 'Shared Vision', 'SetPlayerAllianceStateVisionBJ'),
                                    (FORCE_CONTROL, 'Shared Control', 'SetPlayerAllianceStateControlBJ'),
                                    (FORCE_FULL_CONTROL, 'Advanced Control', 'SetPlayerAllianceStateFullControlBJ')):
            if f['flags'] & flag:
                body.append('//   %s' % title)
                for a in members:
                    for b in members:
                        if a != b:
                            body.append(_call(setter, 'Player(%d)' % a, 'Player(%d)' % b, 'true'))
                body.append('')
    return _function('InitCustomTeams', body)


def ally_priority_lines(w3i_):
    players = w3i_['players']
    body = []
    for k, p in enumerate(players):
        for count_fn, prio_fn, low, high in (('SetStartLocPrioCount', 'SetStartLocPrio', 'ally_low', 'ally_high'),
                                             ('SetEnemyStartLocPrioCount', 'SetEnemyStartLocPrio', 'enemy_low',
                                              'enemy_high')):
            named = [(j, q) for j, q in enumerate(players) if (p[low] | p[high]) & (1 << q['number'])]
            if not named:
                continue
            body.append('')
            body.append(_call(count_fn, str(k), str(len(named))))
            slot = 0
            for j, q in named:
                if q is p:
                    continue
                prio = 'MAP_LOC_PRIO_LOW' if p[low] & (1 << q['number']) else 'MAP_LOC_PRIO_HIGH'
                body.append(_call(prio_fn, str(k), str(slot), str(j), prio))
                slot += 1
    return body


def render_ally_priorities(w3i_, st):
    return _function('InitAllyPriorities', ally_priority_lines(w3i_))


TERRAIN_LIGHTS = {'A': 'Ashenvale', 'C': 'Felwood', 'X': 'Dalaran', 'J': 'Dalaran', 'D': 'Dungeon', 'G': 'Underground',
                  'u': 'Underground', 'P': 'Dalaran'}
AMBIENCE = {'L': 'LordaeronSummer', 'F': 'LordaeronFall', 'W': 'LordaeronWinter', 'B': 'Barrens', 'A': 'Ashenvale',
            'C': 'Felwood', 'N': 'Northrend', 'Y': 'CityScape', 'X': 'Dalaran', 'V': 'Village', 'Q': 'VillageFall',
            'D': 'Dungeon', 'G': 'Dungeon', 'Z': 'SunkenRuins', 'I': 'IceCrown', 'O': 'BlackCitadel',
            'K': 'BlackCitadel', 'J': 'DalaranRuins', 'E': 'DungeonCave'}
FLAG_CUSTOM_FORCES = 0x40
FLAG_TERRAIN_FOG, FLAG_WATER_TINT = 0x2000, 0x10000


DNC_GUID = {'u': ('57bbe30b-ffae-4b08-a82a-4efc1fb02dbd.mdl', '4dd55159-b249-4499-a0d1-e163854c068d.mdl')}
TERRAIN_LIGHTS['R'] = 'Dalaran'


def _dnc(letter, kind):
    if letter in DNC_GUID:
        return DNC_GUID[letter][0 if kind == 'Terrain' else 1]
    name = TERRAIN_LIGHTS.get(letter, 'Lordaeron')
    return 'Environment\\\\DNC\\\\DNC%s\\\\DNC%s%s\\\\DNC%s%s.mdl' % (name, name, kind, name, kind)


def render_main(w3i_, present, st, terrain=None):
    b = w3i_['camera_bounds']
    left, bottom, right, top = b[0] - 512, b[1] - 256, b[2] + 512, b[3] + 256
    m = ('%s + GetCameraMargin(CAMERA_MARGIN_LEFT)' % real(left),
         '%s + GetCameraMargin(CAMERA_MARGIN_BOTTOM)' % real(bottom),
         '%s - GetCameraMargin(CAMERA_MARGIN_RIGHT)' % real(right),
         '%s - GetCameraMargin(CAMERA_MARGIN_TOP)' % real(top))
    locals_ = []
    body = [_call('SetCameraBounds', m[0], m[1], m[2], m[3], m[0], m[3], m[2], m[1])]
    light = w3i_['light_environment'] if w3i_['light_environment'] not in ('\0', '') else w3i_['tileset']
    body.append(_call('SetDayNightModels', '"%s"' % _dnc(light, 'Terrain'), '"%s"' % _dnc(light, 'Unit')))
    fog = w3i_.get('fog')
    if fog and w3i_['flags'] & FLAG_TERRAIN_FOG:
        c = fog[4]
        rgb = (real(c[2] / 255.0, 3), real(c[1] / 255.0, 3), real(c[0] / 255.0, 3))
        heights = w3i_.get('fog_heights')
        if heights:
            body.append(_call('SetTerrainFogExV', str(fog[0]), real(fog[1]), real(fog[2]), real(fog[3], 3),
                              *[real(h) for h in heights] + list(rgb)))
        else:
            body.append(_call('SetTerrainFogEx', str(fog[0]), real(fog[1]), real(fog[2]), real(fog[3], 3), *rgb))
        extra = w3i_.get('fog_extra')
        if extra:
            body.append(_call('BlzSetTerrainFogMaxLinearDensity', real(extra[0])))
            body.append(_call('BlzSetTerrainFogDrawOverSky', _bool(extra[1])))
    water = w3i_.get('water_color')
    if water and w3i_['flags'] & FLAG_WATER_TINT:
        body.append(_call('SetWaterBaseColor', str(water[2]), str(water[1]), str(water[0]), str(water[3])))
    hd = w3i_.get('hd_water')
    if hd:
        color = hd[7]
        body.append(_call('SetHDWaterParamsEx', str(color[2]), str(color[1]), str(color[0]), 'false', str(hd[5]),
                          str(hd[0]), str(hd[1]), str(hd[2]), str(hd[3]), str(hd[4]), str(hd[6]),
                          str(w3i_.get('hd_water_envmap') or 0)))
    weather = w3i_.get('weather') or b'\0\0\0\0'
    if weather.strip(b'\0') and terrain is not None:
        locals_.append('weathereffect we')
        rect = 'Rect(%s,%s,%s,%s)' % (real(terrain.ox), real(terrain.oy), real(terrain.ox + (terrain.w - 1) * 128),
                                      real(terrain.oy + (terrain.h - 1) * 128))
        body.append('set we = AddWeatherEffect( %s, %s )' % (rect, rawcode(weather)))
        body.append(_call('EnableWeatherEffect', 'we', 'true'))
    env = w3i_['sound_environment'].decode('latin-1') or 'Default'
    body.append(_call('NewSoundEnvironment', '"%s"' % env))
    amb = AMBIENCE.get(w3i_['tileset'], 'LordaeronSummer')
    body.append(_call('SetAmbientDaySound', '"%sDay"' % amb))
    body.append(_call('SetAmbientNightSound', '"%sNight"' % amb))
    body.append(_call('SetMapMusic', '"Music"', 'true', '0'))
    for name in ('InitSounds', 'CreateRegions', 'CreateCameras', 'InitUpgrades', 'InitTechTree',
                 'CreateAllDestructables', 'CreateAllItems', 'CreateAllUnits'):
        if name in present:
            body.append(_call(name))
    body.append(_call('InitBlizzard'))
    for name in ('InitGlobals', 'InitCustomTriggers', 'RunInitializationTriggers'):
        if name in present:
            body.append(_call(name))
    body.append('')
    return _function('main', body, locals_)


def render_config(w3i_, present, st):
    players = w3i_['players']
    flags = w3i_['flags']
    body = [_call('SetMapName', jstring(w3i_['name'])), _call('SetMapDescription', jstring(w3i_['description'])),
            _call('SetPlayers', str(len(players))), _call('SetTeams', str(len(players))),
            _call('SetGamePlacement', 'MAP_PLACEMENT_TEAMS_TOGETHER' if sum(p['type'] == 1 for p in players) > 1
                  else 'MAP_PLACEMENT_USE_MAP_SETTINGS'), '']
    for k, p in enumerate(players):
        body.append(_call('DefineStartLocation', str(k), real(p['x']), real(p['y'])))
    body += ['', '// Player setup', _call('InitCustomPlayerSlots')]
    if flags & FLAG_CUSTOM_FORCES:
        body.append(_call('InitCustomTeams'))
    else:
        for p in players:
            body.append(_call('SetPlayerSlotAvailable', 'Player(%d)' % p['number'], 'MAP_CONTROL_USER'))
        body.append(_call('InitGenericPlayerSlots'))
    if 'InitAllyPriorities' in present:
        body.append(_call('InitAllyPriorities'))
    return _function('config', body)


RX_OBJECT_NAME = re.compile(r'\bgg_(?:unit|item|dest)_\w{4}_\d+\b')


def referenced_objects(mt, texts=None, header=None, enabled_only=True):
    from doctor.triggers import wtg
    out, seen = [], set()

    def add(name):
        if name not in seen:
            seen.add(name)
            out.append(name)

    def walk(functions):
        for f in functions:
            if enabled_only and not f.enabled:
                continue
            for p in f.params:
                while p is not None:
                    if p.kind == wtg.VARIABLE and p.value.startswith('gg_'):
                        add(p.value)
                    if p.function is not None:
                        walk([p.function])
                    p = p.index
            walk(f.children)

    triggers = mt.triggers if mt is not None else ()
    for k, t in enumerate(triggers):
        if t.is_comment or (enabled_only and not t.enabled):
            continue
        walk(t.functions)
        text = texts[k] if texts and k < len(texts) else None
        if t.is_text and text:
            for n in RX_OBJECT_NAME.findall(text):
                add(n)
    if header:
        for n in RX_OBJECT_NAME.findall(header):
            add(n)
    return out


EDITOR_FILES = ('war3map.w3i', 'war3map.w3r', 'war3map.w3c', 'war3map.w3s', 'war3mapUnits.doo', 'war3map.doo',
                'war3map.w3e', 'war3map.wtg', 'war3map.wct') + tuple(name for name, _k, _l in GameData.OBJECT_FILES)


def map_files(archive):
    out = {}
    for name in EDITOR_FILES:
        try:
            data = archive.read(name)
        except Exception:
            data = None
        if data is not None:
            out[name] = data
    return out


def _triggers(files, td, mt, texts, header):
    if mt is not None or not files.get('war3map.wtg') or td is None:
        return mt, texts, header
    from doctor.triggers import wtg
    try:
        mt = wtg.read_wtg(files['war3map.wtg'], td, script_fallback=True)
        ct = wtg.read_wct(files['war3map.wct']) if files.get('war3map.wct') else None
        texts = wtg.trigger_texts(mt, ct) if ct is not None else [None] * len(mt.triggers)
        if header is None and ct is not None:
            header = ct.header
        if mt.sub_version is not None:
            names = _trigger_globals(mt, td)
            mt, texts = _classico(mt, texts)
            mt.trigger_globals = names
    except Exception:
        return None, None, header
    return mt, texts, header


def _classico(mt, texts):
    from doctor.triggers import wtg
    por_obj = dict((id(t), tx) for t, tx in zip(mt.triggers, texts or ()))
    ordem = [(c, item) for c, item, _p in wtg.tree(mt) if c in (wtg.GUI, wtg.COMMENT, wtg.SCRIPT)]
    novo = wtg.to_classic(mt)
    novo.tree_order = True
    alinhados = [por_obj.get(id(item)) for _c, item in ordem]
    if len(alinhados) != len(novo.triggers):
        return novo, [None] * len(novo.triggers)
    for (c, _item), t in zip(ordem, novo.triggers):
        if c == wtg.SCRIPT:
            t.script_item = True
    return novo, alinhados


def _trigger_globals(mt, td):
    return re.findall(r'\b(gg_trg_\w+)\s*=', gui_render.render_globals(mt, td, 'jass'))


def _items_and_units(records, game):
    marked = []
    for u in records:
        is_item = game.is_item(u['ident']) if u['ident'] not in (b'sloc', b'uDNR', b'bDNR') else False
        if is_item is None:
            is_item = u['gold'] == 0 and u['acq'] == 0.0 and u['level'] == 0 and u['ident'] != b'sloc'
        marked.append(dict(u, item=bool(is_item)))
    return marked, [u for u in marked if u['item']], [u for u in marked if not u['item'] and u['ident'] != b'sloc']


def render(files, td=None, editor=None, game=None, mt=None, texts=None, durations=None, hints=None, header=None):
    w3i_ = None
    try:
        w3i_ = read_w3i(files['war3map.w3i'])
    except (KeyError, Unreadable):
        pass
    st = Style(editor or (w3i_ or {}).get('editor_version'))
    EMPATE_PAR[0] = (editor or (w3i_ or {}).get('editor_version') or 0) >= EDITOR_EMPATE_PAR
    out = Rendering(st)
    if w3i_ is None:
        out.unknown['w3i'] = 'war3map.w3i unreadable'
    game = game or GameData(files)
    mt, texts, header = _triggers(files, td, mt, texts, header)
    referenced = referenced_objects(mt, texts, header)
    named = referenced_objects(mt, texts, header, enabled_only=False)
    regions, cameras, sounds, units, doodads = [], [], [], [], []
    for name, reader, key in (('war3map.w3r', read_w3r, 'regions'), ('war3map.w3c', read_w3c, 'cameras'),
                              ('war3map.w3s', read_w3s, 'sounds'), ('war3mapUnits.doo', read_units, 'units'),
                              ('war3map.doo', read_doo, 'doodads')):
        if not files.get(name):
            continue
        try:
            got = reader(files[name])
        except (Unreadable, inflated_counts.FormatError, inflated_counts.End, struct.error) as e:
            out.unknown[key] = '%s: %s' % (name, e)
            continue
        if key == 'regions':
            regions = got[1]
        elif key == 'cameras':
            cameras = got[1]
        elif key == 'sounds':
            sounds = got[1]
        elif key == 'units':
            units = got
        else:
            doodads = got[2]
    for d in doodads:
        d['destructable'] = game.is_destructable(d['id'])
        if d['destructable'] is None:
            d['destructable'] = True
    terrain = None
    if files.get('war3map.w3e'):
        try:
            terrain = Terrain(files['war3map.w3e'])
        except (Unreadable, struct.error):
            terrain = None
    units, items, placed = _items_and_units(units, game)
    owners = set(u['owner'] for u in placed)
    neutral_base = 24 if (any(o >= 24 for o in owners) or (w3i_ or {}).get('version', 31) >= 31) else 12
    if mt is not None:
        for line in gui_render.render_globals(mt, td, 'jass').split('\n'):
            m = re.match(r'\s*(\w+(?: array)?)\s+(udg_\w+)(?:\s*=\s*(.*))?$', line)
            if m:
                out.declare(m.group(1).replace(' array', ''), m.group(2), m.group(1).endswith(' array'), m.group(3))
    for reg in regions:
        out.declare('rect', region_name(reg), False, 'null')
    for cam in cameras:
        out.declare('camerasetup', camera_name(cam), False, 'null')
    for snd in sounds:
        music = sound_is_music(snd)
        out.declare('string' if music else 'sound', snd['name'].decode('latin-1'), False, None if music else 'null')
    if mt is not None:
        for name in getattr(mt, 'trigger_globals', None) or _trigger_globals(mt, td):
            out.declare('trigger', name, False, 'null')
    units_by_name = dict(('gg_unit_%s_%04d' % (u['ident'].decode('latin-1'), u['creation']), u) for u in placed)
    items_by_name = dict(('gg_item_%s_%04d' % (u['ident'].decode('latin-1'), u['creation']), u) for u in items)
    dests_by_name = dict(('gg_dest_%s_%04d' % (d['id'].decode('latin-1'), d['editor_id']), d) for d in doodads)
    for name in named:
        for prefix, table, type_ in (('gg_unit_', units_by_name, 'unit'), ('gg_item_', items_by_name, 'item'),
                                     ('gg_dest_', dests_by_name, 'destructable')):
            if name.startswith(prefix) and name in table:
                out.declare(type_, name, False, 'null')
    if mt is not None and mt.variables:
        out.add('InitGlobals', gui_render.render_init_globals(mt, td, 'jass'))
    if w3i_ is not None:
        for table in w3i_['random_item_tables']:
            if not table['sets']:
                continue
            sets = [[(ident, chance) for chance, ident in s] for s in table['sets']]
            out.add('ItemTable%06d_DropItems' % table['number'],
                    render_drop('ItemTable%06d_DropItems' % table['number'], sets, st))
    for index, u in enumerate(units):
        if not u['item'] and u['itp'] == -1 and any(u['set_items']):
            out.add('Unit%06d_DropItems' % index, render_drop('Unit%06d_DropItems' % index, u['set_items'], st))
    for d in doodads:
        if d['item_table'] == -1 and any(d['item_sets']) and d.get('destructable', True):
            out.add('Doodad%06d_DropItems' % d['index'], render_drop('Doodad%06d_DropItems' % d['index'],
                                                                      d['item_sets'], st))
    if sounds:
        text, exact = render_sounds(sounds, st, durations)
        out.add('InitSounds', text)
        if not exact:
            out.unknown['InitSounds'] = 'the sound durations (the editor measures the audio files)'
    if any(_dest_needed(d, referenced) for d in doodads):
        out.add('CreateAllDestructables', render_destructables(doodads, referenced, st, game))
    if items:
        out.add('CreateAllItems', render_items(items, referenced, st, game))
    region_vars = dict((reg['creation'], region_name(reg)) for reg in regions)
    if placed:
        for name, text in render_units(units, referenced, region_vars, st, game, neutral_base, hints):
            out.add(name, text)
    if regions:
        out.add('CreateRegions', render_regions(regions, st, terrain))
    if cameras:
        out.add('CreateCameras', render_cameras(cameras, st))
    if mt is not None:
        out.add('InitCustomTriggers', gui_render.render_init_custom_triggers(mt, 'jass', True, texts=texts))
        rit = gui_render.render_run_initialization_triggers(mt, 'jass', True)
        if rit:
            out.add('RunInitializationTriggers', rit)
    if w3i_ is not None:
        for name, text in render_upgrades(w3i_, st) + render_techtree(w3i_, st, game):
            out.add(name, text)
        out.add('InitCustomPlayerSlots', render_player_slots(w3i_, st))
        out.add('InitCustomTeams', render_teams(w3i_, st))
        if ally_priority_lines(w3i_):
            out.add('InitAllyPriorities', render_ally_priorities(w3i_, st))
        present = set(out.functions)
        out.add('main', render_main(w3i_, present, st, terrain))
        out.add('config', render_config(w3i_, present, st))
    out.w3i = w3i_
    return out


RX_ONE_CALL = re.compile(r'^\s*call\s+(\w+)\s*\(\s*\)\s*(?://[^\n]*)?$')


def _body_lines(text):
    lines = [l.strip() for l in text.split('\n')]
    code = [l for l in lines if l and not l.startswith('//')]
    return code[1:-1] if len(code) >= 2 else []


def inline_one_liners(text, functions):
    out = []
    for line in text.split('\n'):
        m = RX_ONE_CALL.match(line)
        seen = set()
        while m and m.group(1) in functions and m.group(1) not in seen:
            seen.add(m.group(1))
            body = _body_lines(functions[m.group(1)])
            if len(body) != 1 or not body[0].startswith('call '):
                break
            line = '    ' + body[0]
            m = RX_ONE_CALL.match(line)
        out.append(line)
    return '\n'.join(out)


def canonical_function(text, functions=None):
    return gui_render.canonical(inline_one_liners(text, functions or {}), 'jass', True)


def same_function(rendered, original, rendered_all=None, original_all=None, name=None):
    a = canonical_function(rendered, rendered_all)
    b = canonical_function(original, original_all)
    if a == b:
        return True
    if name == 'main':
        sem = RX_MAIN_JASSHELPER.sub('', original)
        if sem != original and canonical_function(sem, original_all) == a:
            return True
    if 'l__' in original:
        sem = re.sub(r'\bl__(\w+)', r'\1', original)
        if canonical_function(sem, original_all) == a:
            return True
    if name == 'InitCustomTriggers' and '// INLINED!!' in original and original_all:
        if canonical_function(rendered, original_all) == b:
            return True
    if name in ('CreateAllDestructables', 'CreateAllItems'):
        rx = RX_DEST_BLOCK if name == 'CreateAllDestructables' else RX_ITEM_BLOCK
        ha, ga, oa = _destructable_blocks(a, rx)
        hb, gb, ob = _destructable_blocks(b, rx)
        return ha == hb and ga == gb and _runs(oa) == _runs(ob)
    return False


RX_MAIN_JASSHELPER = re.compile(
    r'(?m)^(?:[ \t]*call[ \t]+(?:ExecuteFunc[ \t]*\([ \t]*"\w+"[ \t]*\)|\w+__\w+[ \t]*\([ \t]*\))'
    r'[ \t]*|call[ \t][^\n]*)\n'
)


def _runs(ids):
    out = []
    for i in ids:
        if not out or out[-1] != i:
            out.append(i)
    return out


def family(name):
    return re.sub(r'\d+', 'N', name)


EDITOR_CONFIG = frozenset(('DefineStartLocation', 'InitAllyPriorities', 'InitCustomPlayerSlots', 'InitCustomTeams',
                           'InitGenericPlayerSlots', 'SetGamePlacement', 'SetMapDescription', 'SetMapName',
                           'SetPlayerSlotAvailable', 'SetPlayers', 'SetTeams'))


def _config_editado(texto):
    chamadas = set(re.findall(r'(?m)^\s*call\s+(\w+)\s*\(', re.sub(r'//[^\n]*', '', texto or '')))
    return bool(chamadas - EDITOR_CONFIG)


def compare(rendering, script):
    if isinstance(script, bytes):
        script = script.decode('utf-8', 'surrogateescape')
    script = script.replace('\r\n', '\n')
    theirs = gui_render.split_functions(script, 'jass')
    mine = dict(rendering.functions)
    out = collections.OrderedDict()
    for name, text in rendering.functions.items():
        if name not in theirs:
            out[name] = 'missing'
        else:
            out[name] = 'equal' if same_function(text, theirs[name], mine, theirs, name) else 'differs'
            if out[name] == 'differs' and name == 'config' and _config_editado(theirs[name]):
                out[name] = 'edited'
    return out


OBJECT_TRIGGER = 'Custom script objects'
OBJECT_NOTE = ('Names the placed units, items and destructibles the custom script uses: the World Editor declares the '
               'gg_ variable of a placed object only when a trigger names it. Disabled: it never runs.')
DEVO = 'devo_'
NEVER_TWIN = frozenset(('InitSounds',))
AFTER_HEADER = re.compile(r'(?:InitCustomTriggers|RunInitializationTriggers|InitUpgrades\w*|InitTechTree\w*|'
                          r'InitCustomPlayerSlots|InitCustomTeams|InitAllyPriorities|main|config)$')
RX_JASS_NOISE = re.compile(r'//[^\n]*|"(?:[^"\\\n]|\\.)*"|\'(?:[^\'\\\n]|\\.)*\'')
RX_STRING = re.compile(r'"((?:[^"\\\n]|\\.)*)"')
RX_WORD = re.compile(r'[A-Za-z_]\w*')
REF_DIR = os.path.normpath(os.path.join(HERE, '..', 'ref', '3.0'))


class Fit(object):
    def __init__(self):
        self.ok = False
        self.level = ''
        self.header = None
        self.inject = True
        self.dropped = []
        self.replaced = []
        self.objects = []
        self.triggers = None
        self.texts = None
        self.script = ''
        self.proofs = {}
        self.notes = []
        self.reason = ''
        self.lines = (0, 0)


RX_VJASS_OPEN = re.compile(r'[ \t]*(?:(?:private|public)[ \t]+)?'
                           r'(?:scope|library|library_once|struct|module|interface)\b')
RX_VJASS_CLOSE = re.compile(r'[ \t]*end(?:scope|library|struct|module|interface)\b')


def mask_vjass(text):
    lines = text.split('\n')
    if not any(RX_VJASS_OPEN.match(line) for line in lines):
        return text
    depth = 0
    for k, line in enumerate(lines):
        if RX_VJASS_OPEN.match(line):
            depth += 1
        if depth:
            lines[k] = ' ' * len(line)
            if RX_VJASS_CLOSE.match(line):
                depth -= 1
    return '\n'.join(lines)


class _Header(object):
    def __init__(self, text):
        import bisect
        from doctor.script import jass_ast
        self.text = text
        self.masked = text = mask_vjass(text)
        tree = jass_ast.parse(text)
        starts = [0] + [m.end() for m in re.finditer('\n', text)]

        def span(first, last):
            a = starts[first - 1] if first - 1 < len(starts) else len(text)
            b = starts[last] if last < len(starts) else len(text)
            return a, b

        self.decls = collections.OrderedDict()
        self.functions = collections.OrderedDict()
        self.natives, self.types, self.blocks = [], [], []
        comments = sorted(c.line for c in tree.comments)
        prev = 0
        for item in tree.items:
            kind = type(item).__name__
            last = item.end_line if kind in ('Function', 'Globals') else item.line
            if kind == 'Globals':
                block = span(item.line, last)
                self.blocks.append(block)
                for d in item.decls:
                    value = None if d.initializer is None else jass_ast.unparse(d.initializer)
                    self.decls.setdefault(d.name, (d.type, bool(d.is_array), bool(d.is_constant), value,
                                                   span(d.line, d.line + (value or '').count('\n')), block))
            elif kind == 'Function' and item.is_native:
                self.natives.append(span(item.line, last))
            elif kind == 'Function':
                k = bisect.bisect_right(comments, prev)
                lead = comments[k] if k < len(comments) and comments[k] < item.line else item.line
                a, b = span(item.line, last)
                self.functions.setdefault(item.name, (starts[lead - 1], a, b))
            elif kind == 'TypeDecl':
                self.types.append(span(item.line, last))
            prev = last

    def function_text(self, name):
        _lead, a, b = self.functions[name]
        return self.masked[a:b]


def _cut(text, spans):
    out, pos = [], 0
    for a, b in sorted(set(spans)):
        a = max(a, pos)
        if b <= a:
            continue
        out.append(text[pos:a])
        pos = b
    out.append(text[pos:])
    return ''.join(out)


def _renamer(names, prefix=DEVO):
    if not names:
        return lambda text: text
    rx = re.compile(r'\b%s(%s)\b' % (re.escape(prefix), '|'.join(sorted(map(re.escape, names), key=len,
                                                                           reverse=True))))
    return lambda text: rx.sub(lambda m: m.group(1), text)


def function_refs(text, names):
    code = RX_JASS_NOISE.sub(' ', text)
    out = set(RX_WORD.findall(code)) & names
    out.update(s for s in RX_STRING.findall(text) if s in names)
    return out


def placed_objects(files, game):
    out = {}
    if files.get('war3mapUnits.doo'):
        try:
            _marked, items, units = _items_and_units(read_units(files['war3mapUnits.doo']), game)
        except (Unreadable, inflated_counts.FormatError, inflated_counts.End, struct.error):
            items, units = [], []
        for u in units:
            out['gg_unit_%s_%04d' % (u['ident'].decode('latin-1'), u['creation'])] = 'unit'
        for u in items:
            out['gg_item_%s_%04d' % (u['ident'].decode('latin-1'), u['creation'])] = 'item'
    if files.get('war3map.doo'):
        try:
            for d in read_doo(files['war3map.doo'])[2]:
                out['gg_dest_%s_%04d' % (d['id'].decode('latin-1'), d['editor_id'])] = 'destructable'
        except (Unreadable, struct.error):
            pass
    return out


def named_by_triggers(mt, texts):
    out = set(referenced_objects(mt, None, None, enabled_only=False)) if mt is not None else set()
    for k, t in enumerate(mt.triggers if mt is not None else ()):
        text = texts[k] if texts and k < len(texts) else None
        if t.is_text and t.enabled and text:
            out.update(RX_OBJECT_NAME.findall(RX_JASS_NOISE.sub(' ', text)))
    return set(n for n in out if n.startswith(('gg_unit_', 'gg_item_', 'gg_dest_')))


def object_trigger(names, taken=()):
    from doctor.triggers import wtg
    actions = []
    for n in names:
        if n.startswith('gg_unit_'):
            actions.append(wtg.Function(wtg.ACTION, 'ResetUnitAnimation', 1, [wtg.Parameter(wtg.VARIABLE, n)]))
        elif n.startswith('gg_item_'):
            actions.append(wtg.Function(wtg.ACTION, 'SetItemVisibleBJ', 1, [wtg.Parameter(wtg.PRESET, 'ShowHideShow'),
                                                                          wtg.Parameter(wtg.VARIABLE, n)]))
        elif n.startswith('gg_dest_'):
            actions.append(wtg.Function(wtg.ACTION, 'SetDestAnimationSpeedPercent', 1,
                                        [wtg.Parameter(wtg.VARIABLE, n), wtg.Parameter(wtg.LITERAL, '100')]))
    name, k = OBJECT_TRIGGER, 2
    while gui_render.trigger_identifier(name) in taken or 'gg_trg_' + gui_render.trigger_identifier(name) in taken:
        name, k = '%s %d' % (OBJECT_TRIGGER, k), k + 1
    return wtg.Trigger(name, OBJECT_NOTE, 0, 0, 0, 0, 0, 0, actions)


def triggers_code(mt, td, texts=None):
    out = []
    for k, t in enumerate(mt.triggers if mt is not None else ()):
        if t.enabled and not t.is_comment:
            text = texts[k] if texts and k < len(texts) else None
            code = gui_render.render_trigger(t, td, mt, 'jass', text)
            out.append(code if code.endswith('\n') else code + '\n')
    return ''.join(out)


def _line(text):
    return text if text.endswith('\n') else text + '\n'


def editor_script(rendering, header, dropped=(), replaced=(), inject=True, triggers=''):
    back = _renamer(replaced)
    text = header.masked
    gone_decls = set(dropped)
    decls = ''.join(back(text[slice(*d[4])]) for n, d in header.decls.items() if n not in gone_decls)
    types = ''.join(text[a:b] for a, b in header.types)
    natives = ''.join(_line(text[a:b]) for a, b in header.natives)
    gone = set(DEVO + x for x in replaced) | {'main', 'config'}
    functions = ''.join(_line(back(text[lead:b])) for n, (lead, _a, b) in header.functions.items() if n not in gone)
    early = [_line(t) for n, t in rendering.functions.items() if not AFTER_HEADER.match(n)]
    late = [_line(t) for n, t in rendering.functions.items() if AFTER_HEADER.match(n) and n not in ('main', 'config')]
    injected = ('main', 'config') if inject is True else tuple(inject or ())
    ends = []
    for n in ('main', 'config'):
        if n in injected and n in header.functions:
            ends.append(_line(back(header.function_text(n))))
        elif n in rendering.functions:
            ends.append(_line(rendering.functions[n]))
    return ''.join([types, rendering.globals_text(decls), natives] + early + [functions, triggers] + late + ends)


def fitted_header(header, dropped=(), replaced=()):
    spans = [header.decls[n][4] for n in dropped if n in header.decls]
    gone = set(dropped)
    for block in header.blocks:
        inside = [n for n, d in header.decls.items() if d[5] == block]
        if inside and all(n in gone for n in inside):
            spans.append(block)
    for x in replaced:
        lead, _a, b = header.functions[DEVO + x]
        spans.append((lead, b))
    return _renamer(replaced)(_cut(header.text, spans))


def _same_declaration(header_decl, editor_decl):
    type_, is_array, constant, value, _span, _block = header_decl
    etype, _name, earray, evalue = editor_decl
    if constant or type_ != etype or bool(is_array) != bool(earray):
        return False
    return _value(value) == _value(evalue)


def _value(v):
    return None if v in (None, 'null') else re.sub(r'\s+', '', v)


def _twins(rendering, header, reference):
    devo = set(n[len(DEVO):] for n in header.functions if n.startswith(DEVO))
    back = _renamer(devo)
    theirs = dict((n, back(t)) for n, t in reference.items() if not n.startswith(DEVO))
    theirs.update((n[len(DEVO):], back(t)) for n, t in reference.items() if n.startswith(DEVO))
    out = {}
    for x, text in rendering.functions.items():
        if x in devo and x not in NEVER_TWIN and x not in ('main', 'config'):
            out[x] = same_function(text, theirs.get(x, ''), rendering.functions, theirs, x)
    for x in ('main', 'config'):
        if x in rendering.functions and x in theirs:
            out[x] = same_function(rendering.functions[x], theirs[x], rendering.functions, theirs, x)
    return out


def _replaceable(equal, header, reference, blocked):
    devo_names = set(n for n in header.functions if n.startswith(DEVO))
    keep = set(x for x, same in equal.items() if same and x not in ('main', 'config') and x not in blocked)
    changed = True
    while changed:
        changed = False
        for x in sorted(keep):
            calls = function_refs(reference.get(DEVO + x, ''), devo_names)
            if any(c[len(DEVO):] not in keep for c in calls):
                keep.discard(x)
                changed = True
    return keep


ORDER_BY_FOLDER = ('InitCustomTriggers', 'RunInitializationTriggers')


def _same_calls(a, b):
    def calls(text):
        return sorted(x.strip() for x in text.split('\n') if x.strip())

    return calls(a) == calls(b)


def runs_original(script, reference, replaced=()):
    mine = gui_render.split_functions(script, 'jass')
    theirs = reference if isinstance(reference, dict) else gui_render.split_functions(reference, 'jass')
    to_ref = dict((x, DEVO + x) for x in replaced)
    if replaced:
        rx = re.compile(r'\b(%s)\b' % '|'.join(sorted(map(re.escape, replaced), key=len, reverse=True)))
        mine = dict((to_ref.get(n, n), rx.sub(lambda m: to_ref[m.group(1)], t)) for n, t in mine.items())
    names = set(mine)
    seen, stack, problems, compared = set(), ['main', 'config'], [], 0
    while stack:
        n = stack.pop()
        if n in seen or n not in mine:
            continue
        seen.add(n)
        if n not in theirs:
            problems.append('%s is not in the reference script' % n)
            continue
        if mine[n] != theirs[n]:
            compared += 1
            if n in ORDER_BY_FOLDER and _same_calls(mine[n], theirs[n]):
                pass
            elif canonical_function(mine[n], mine) != canonical_function(theirs[n], theirs):
                problems.append('%s differs' % n)
        stack.extend(sorted(function_refs(mine[n], names) - seen))
    detail = '%d functions reached from main and config, %d compared as code' % (len(seen), compared)
    if problems:
        detail = '%d differences: %s' % (len(problems), '; '.join(problems[:3]))
    return not problems, detail


RX_PJASS_WHERE = re.compile(r'^(?:[A-Za-z]:)?[^:]*:\d+:\s*')


def pjass_run(scripts):
    import shutil
    import tempfile
    try:
        from doctor.script import pjass
    except ImportError:
        return None
    if not os.path.isfile(pjass.exe()):
        return None
    tmp = tempfile.mkdtemp(prefix='editor_render_')
    out = {}
    try:
        for tag, code in scripts.items():
            path = os.path.join(tmp, tag + '.j')
            with open(path, 'wb') as f:
                f.write(code.encode('utf-8', 'surrogateescape'))
            ref = pjass.game_scripts_dir(REF_DIR) or REF_DIR
            r = pjass.run_action([(os.path.join(ref, 'common.j'), 'common.j'),
                                  (os.path.join(ref, 'blizzard.j'), 'Blizzard.j'), (path, 'war3map.j')],
                                 tmp=os.path.join(tmp, tag))
            out[tag] = (r['rc'], collections.Counter(RX_PJASS_WHERE.sub('', x) for x in r['line_list']
                                                     if RX_PJASS_WHERE.match(x)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out


def _pjass_proof(scripts, original_errors):
    runs = pjass_run(scripts)
    if runs is None:
        return True, 'skipped: no pjass'
    new = collections.Counter()
    for tag, (rc, errors) in runs.items():
        new.update(errors - (original_errors or collections.Counter()))
        if rc != 0 and not errors and not original_errors:
            new['pjass stopped with rc=%d' % rc] += 1
    n = max(sum(errors.values()) for _rc, errors in runs.values())
    ok = not new
    detail = '%d error(s)%s' % (n, '' if not original_errors else ' (the original script has %d)'
                                % sum(original_errors.values()))
    if new:
        detail += '; new: %s' % ' | '.join(list(new)[:3])
    return ok, detail


def fit(header, files, td, mt=None, texts=None, reference=None, original=None, casc=None, editor=EDITOR_3,
        triggers=None, log=None):
    say = log or (lambda *a: None)
    out = Fit()
    try:
        return _fit(out, header, files, td, mt, texts, reference, original, casc, editor, triggers, say)
    except Exception as e:
        import traceback
        out.ok = False
        out.reason = 'internal error: %s: %s' % (type(e).__name__, str(e)[:200])
        out.notes.append(traceback.format_exc()[-2000:])
        return out


def _fit(out, header_text, files, td, mt, texts, reference, original, casc, editor, triggers, say):
    import dataclasses
    from doctor.script import jass_ast
    from doctor.triggers import wtg
    try:
        header = _Header(header_text)
    except jass_ast.JassSyntaxError as e:
        out.reason = 'the custom script does not parse: %s' % e
        return out
    out.lines = (header_text.count('\n'), header_text.count('\n'))
    reference = gui_render.split_functions(reference if reference is not None else header_text, 'jass')
    game = GameData(files, casc)
    placed = placed_objects(files, game)
    texts = list(texts) if texts is not None else [None] * len(mt.triggers if mt is not None else ())
    known = named_by_triggers(mt, texts)
    out.objects = [n for n in header.decls if n in placed and n not in known]
    if mt is None:
        mt = wtg.MapTriggers(7, None, 2, [wtg.Category(0, 'Map Script', 0)], [], [])
    if out.objects:
        taken = set(gui_render.trigger_identifier(t.name) for t in mt.triggers) | set(header.decls)
        trigger = object_trigger(out.objects, taken)
        trigger.category_id = mt.categories[-1].id if mt.categories else 0
        mt = dataclasses.replace(mt, triggers=list(mt.triggers) + [trigger])
        texts = texts + [None]
    out.triggers, out.texts = mt, texts
    hints = building_hints('\n'.join(reference.values()))
    renders = [render(files, td, editor, game, mt, texts, hints=hints, header=h) for h in (None, header_text)]
    if renders[1].functions == renders[0].functions and renders[1].declared() == renders[0].declared():
        renders = renders[:1]
    declared = collections.OrderedDict()
    for r in renders:
        for g in r.globals:
            declared.setdefault(g[1], g)
    out.dropped = [n for n in header.decls if n in declared]
    bad = [n for n in out.dropped if not _same_declaration(header.decls[n], declared[n])]
    if bad:
        d = header.decls[bad[0]]
        e = declared[bad[0]]
        out.reason = ('the editor declares %s as %s%s = %s, the custom script as %s%s%s = %s' % (
            bad[0], e[0], ' array' if e[2] else '', e[3], 'constant ' if d[2] else '', d[0], ' array' if d[1] else '',
            d[3]))
        return out
    code = triggers if triggers is not None else triggers_code(mt, td, texts)
    devo_names = set(n for n in header.functions if n.startswith(DEVO))
    blocked = set(n[len(DEVO):] for n in function_refs(code, devo_names))
    for n in header.functions:
        if n not in ('main', 'config'):
            blocked.update(c[len(DEVO):] for c in function_refs(header.function_text(n), devo_names)
                           if AFTER_HEADER.match(c[len(DEVO):]))
    equal = {}
    for r in renders:
        for x, same in _twins(r, header, reference).items():
            equal[x] = equal.get(x, True) and same
    keep = _replaceable(equal, header, reference, blocked)
    ends = all(equal.get(x) for x in ('main', 'config')) and all(
        n[len(DEVO):] in keep for x in ('main', 'config') for n in function_refs(reference.get(x, ''), devo_names))
    plans = []
    if keep and ends:
        plans.append(('editor main', sorted(keep), False))
    if keep:
        plans.append(('twins', sorted(keep), True))
    plans.append(('globals', [], True))
    original_errors = None
    if isinstance(original, bytes):
        original = original.decode('utf-8', 'surrogateescape')
    if original is not None:
        runs = pjass_run({'original': mask_vjass(original)})
        original_errors = runs['original'][1] if runs else None
    if header.masked != header.text:
        out.notes.append('the custom script has vJass blocks: JassHelper compiles them on save, pjass reads the rest '
                         '(and the original script the same way)')
    reasons = []
    for level, replaced, inject in plans:
        scripts = dict(('script%d' % k, editor_script(r, header, out.dropped, replaced, inject, code))
                       for k, r in enumerate(renders))
        proofs = collections.OrderedDict()
        proofs['editor_save_pjass'] = _pjass_proof(scripts, original_errors)
        runs = [runs_original(s, reference, replaced) for s in scripts.values()]
        proofs['editor_save_runs_original'] = (all(ok for ok, _d in runs), next((d for ok, d in runs if not ok),
                                                                                 runs[0][1]))
        if all(ok for ok, _d in proofs.values()):
            out.ok, out.level, out.inject, out.replaced = True, level, inject, replaced
            out.header = fitted_header(header, out.dropped, replaced)
            out.script = scripts['script0']
            out.proofs = proofs
            ends_lines = 0 if inject else sum(header.function_text(n).count('\n') + 1 for n in ('main', 'config')
                                              if n in header.functions)
            out.lines = (header_text.count('\n'), out.header.count('\n') - ends_lines)
            out.reason = '; '.join(reasons)
            say('fit: %s, %d globals and %d functions left to the editor, %d objects named' % (
                level, len(out.dropped), len(replaced), len(out.objects)))
            return out
        reasons.append('%s: %s' % (level, '; '.join(d for ok, d in proofs.values() if not ok)))
        out.proofs = proofs
    out.reason = '; '.join(reasons)
    return out


def outcome(fit_, td=None):
    wtg_bytes = None
    if fit_.ok and fit_.objects and td is not None:
        from doctor.triggers import wtg
        wtg_bytes = wtg.write_wtg(fit_.triggers, td)
    report = {'level': fit_.level, 'dropped': list(fit_.dropped), 'replaced': list(fit_.replaced),
              'objects': list(fit_.objects), 'inject': fit_.inject, 'lines': list(fit_.lines), 'reason': fit_.reason,
              'proofs': dict((k, d) for k, (_ok, d) in fit_.proofs.items())}
    return (fit_.ok, fit_.level, fit_.header, fit_.inject, wtg_bytes, fit_.script, report,
            dict((k, bool(ok)) for k, (ok, _d) in fit_.proofs.items()))


RX_CREATED_ID = re.compile(r"(?:CreateUnit|BlzCreateUnitWithSkin)\s*\(\s*\w+\s*,\s*'(.{4})'")


def building_hints(script):
    if isinstance(script, bytes):
        script = script.decode('utf-8', 'surrogateescape')
    out = {}
    for name, text in gui_render.split_functions(script.replace('\r\n', '\n'), 'jass').items():
        if not re.match(r'^Create(?:BuildingsForPlayer\d+|UnitsForPlayer\d+|Neutral\w+)$', name):
            continue
        building = 'Buildings' in name
        for m in RX_CREATED_ID.finditer(text):
            out.setdefault(m.group(1).encode('latin-1'), building)
    return out


ERAS = ((6105, 'classic'), (6117, '1.32'), (7000, '2.0'), (1 << 30, '3.0'))
def era(editor):
    return next(name for limit, name in ERAS if editor < limit)

