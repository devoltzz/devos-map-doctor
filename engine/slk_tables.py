# Reads the object fields of a map from its SLK, text and object files.
import os
import re

import objects

slk = objects.slk

UNIT_FIELDS = set('''file name propernames art primary hp manan def dmgplus1 rangen1 cool1 acquire abillist
modelscale bountyplus collision spd level goldcost race movetp str agi int dice1 sides1 deftype atktype1 weaptp1
tilesets hostilepal hideherobar unitclass specialart missileart ubertip tip hotkey weapson sight regenhp regenmana
formation points scale isbldg type sort mindmg1 maxdmg1 avgdmg1 dmgpt1 backsw1 unitsound moveheight movefloor
sortui sortbalance sortweap sortabil heroabillist buttonpos casttime
red green blue'''.split())
ABILITY_FIELDS = set('''code buffid1 buffid2 hotkey cool1 cool2 cost1 cost2 item hero levels rng1 area1 dur1 herodur1
unitid1 efctid1 name art tip ubertip untip unubertip researchtip researchubertip researchart unart buttonpos
order orderoff orderon unorder race checkdep reqlevel targs1 cast1 priority missileart effectart targetart
casterart specialart lightningeffect'''.split())
for L in '1234':
    for c in 'ABCDEFGHI':
        ABILITY_FIELDS.add('data%s%s' % (c.lower(), L))
ITEM_FIELDS = set('''name art goldcost lumbercost uses class abillist level oldlevel tip ubertip description hotkey
cooldownid file scale selsize usable droppable pawnable sellable perishable hp armor stockmax stockregen stockstart
powerup drop pickrandom ignorecd prio colorr colorg colorb requires'''.split())
DEFAULT_FIELDS = {'unit': UNIT_FIELDS, 'ability': ABILITY_FIELDS, 'item': ITEM_FIELDS}


def merge(dst, src, allowed_keys):
    for k, v in src.items():
        lk = k.lower()
        if lk in allowed_keys and v != '' and v is not None:
            dst[lk] = v


def parse_w3x_objects(path, legacy_key=False):
    return objects.parse_w3x_objects(path, legacy_key=legacy_key)


def _split_levels(field_value):
    pieces, buf, inside = [], [], False
    for c in field_value:
        if c == '"':
            inside = not inside
            buf.append(c)
        elif c == ',' and not inside:
            pieces.append(''.join(buf))
            buf = []
        else:
            buf.append(c)
    pieces.append(''.join(buf))
    return pieces


def _unquoted(s):
    s = s.strip()
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        return s[1:-1]
    return s


LV_MARK = re.compile(r'Lv\.\s*(\d+)')


def _list_by_level(raw_parts, levels):
    try:
        n = int(str(levels).strip())
    except (TypeError, ValueError):
        return False
    if n <= 1 or len(raw_parts) != n:
        return False
    for i, part in enumerate(raw_parts, 1):
        m = LV_MARK.search(part)
        if m is None or int(m.group(1)) != i:
            return False
    return True


def hint_per_level(units_folder, abils, fields=('tip', 'ubertip')):
    n = 0
    for fn in sorted(os.listdir(units_folder)):
        if not fn.lower().endswith('abilitystrings.txt'):
            continue
        current = None
        raw = open(os.path.join(units_folder, fn), 'rb').read().decode('utf-8', 'surrogateescape')
        for ln in raw.split('\n'):
            ln = ln.rstrip('\r')
            s = ln.strip()
            if s.startswith('[') and s.endswith(']'):
                current = s[1:-1]
                continue
            if current is None or '=' not in ln:
                continue
            k, v = ln.split('=', 1)
            k = k.strip().lower()
            if k not in fields or current not in abils:
                continue
            raw_parts = _split_levels(v.strip())
            between_quotes = all(p.strip().startswith('"') and p.strip().endswith('"')
                                 and len(p.strip()) >= 2 for p in raw_parts)
            if len(raw_parts) <= 1 or not (between_quotes
                                           or _list_by_level(raw_parts, abils[current].get('levels'))):
                continue
            pieces = [_unquoted(p) for p in raw_parts]
            abils[current][k] = pieces[0]
            abils[current][k + '_lv'] = pieces
            n += 1
    if n:
        print('per-level hint: %d field(s) with more than one level' % n)
    return n


def w3u_models(ext, legacy_key=False):
    p = os.path.join(ext, 'war3map.w3u')
    if not os.path.exists(p):
        return {}
    try:
        _ver, objs, _pos = objects.read_objects(p, with_levels=False)
    except objects.ObjectError as e:
        print('warning: war3map.w3u cannot be read (%s)' % e)
        return {}
    out = {}
    for _table, orig, new, mods in objs:
        if legacy_key:
            hash_key = orig
        else:
            hash_key = new if new.strip('\0') else orig
        for field_id, kind, _level, _ptr, val in mods:
            if field_id == 'umdl' and kind == 3:
                out[hash_key] = val.decode('utf-8', 'surrogateescape')
    return out


def has_slk(ext):
    U = os.path.join(ext, 'units')
    return os.path.isdir(U) and any(f.lower().endswith('.slk') for f in os.listdir(U))


def _slk_or_empty(U, fn):
    p = os.path.join(U, fn)
    if not os.path.isfile(p):
        print('WARNING: the map has no Units\\%s: the table is left without those records' % fn)
        return [], {}
    return slk.parse_slk(p)


def build_tables(ext, legacy_key=False):
    U = os.path.join(ext, 'units')
    units = {}
    for fn in ('unitdata.slk', 'unitbalance.slk', 'unitui.slk', 'unitweapons.slk', 'unitabilities.slk'):
        hdr, rows = _slk_or_empty(U, fn)
        for rid, row in rows.items():
            merge(units.setdefault(rid, {}), row, UNIT_FIELDS)
    mdl = w3u_models(ext, legacy_key=legacy_key)
    for rid, file_path in mdl.items():
        units.setdefault(rid, {})['file'] = file_path
    if mdl:
        print('models coming from war3map.w3u:', len(mdl))
    for fn in os.listdir(U):
        if (fn.lower().endswith('unitstrings.txt') or fn.lower().endswith('unitfunc.txt')
                or fn.lower() == 'unitskin.txt'):
            for rid, row in slk.parse_ini(os.path.join(U, fn)).items():
                merge(units.setdefault(rid, {}), row, UNIT_FIELDS)
    abils = {}
    hdr, rows = _slk_or_empty(U, 'abilitydata.slk')
    for rid, row in rows.items():
        merge(abils.setdefault(rid, {}), row, ABILITY_FIELDS)
    for fn in os.listdir(U):
        if fn.lower().endswith('abilitystrings.txt') or fn.lower().endswith('abilityfunc.txt'):
            for rid, row in slk.parse_ini(os.path.join(U, fn)).items():
                merge(abils.setdefault(rid, {}), row, ABILITY_FIELDS)
    w3a = parse_w3x_objects(os.path.join(ext, 'war3map.w3a'), legacy_key=legacy_key)
    W3A_MAP = {'aord': 'order', 'aoro': 'orderoff', 'aoru': 'unorder', 'aorf': 'orderon',
               'anam': 'name', 'aart': 'art', 'atp1': 'tip', 'aub1': 'ubertip', 'aut1': 'untip', 'auu1': 'unubertip',
               'ahky': 'hotkey', 'abuf': 'buffid', 'acdn': 'cool', 'amcs': 'cost', 'alev': 'levels', 'aran': 'rng',
               'aare': 'area', 'adur': 'dur', 'ahdu': 'herodur'}
    for oid, rec in w3a.items():
        dst = abils.setdefault(oid, {})
        for k, v in rec.items():
            if k == '_base':
                continue
            mid, lvl = k
            name = W3A_MAP.get(mid)
            if name is None:
                continue
            if name in ('order', 'orderoff', 'unorder', 'orderon', 'name', 'art', 'hotkey', 'levels'):
                dst[name] = v
            elif lvl <= 4:
                dst['%s%d' % (name, max(lvl, 1))] = v
    hint_per_level(U, abils)
    items = {}
    hdr, rows = _slk_or_empty(U, 'itemdata.slk')
    for rid, row in rows.items():
        merge(items.setdefault(rid, {}), row, ITEM_FIELDS)
    for fn in os.listdir(U):
        if fn.lower() in ('itemstrings.txt', 'itemfunc.txt', 'itemskin.txt'):
            for rid, row in slk.parse_ini(os.path.join(U, fn)).items():
                merge(items.setdefault(rid, {}), row, ITEM_FIELDS)
    return units, abils, items


def allowed_with(extras=None):
    out = dict((t, set(c)) for t, c in DEFAULT_FIELDS.items())
    for t, cs in (extras or {}).items():
        out.setdefault(t, set()).update(c.lower() for c in cs)
    return out


def build_auto_tables(ext, method='auto', extras=None, stats=None, legacy_key=False, **w3u):
    if method == 'auto':
        method = 'slk' if has_slk(ext) else 'w3u'
    if method == 'slk':
        u, a, i = build_tables(ext, legacy_key=legacy_key)
        return 'slk', u, a, i
    if method != 'w3u':
        raise ValueError('unknown mode: %r (slk, w3u or auto)' % method)
    u, a, i = objects.w3u_tables(ext, allowed=allowed_with(extras), stats=stats, **w3u)
    return 'w3u', u, a, i

