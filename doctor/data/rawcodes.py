# Every 4-byte raw code a map brings (units, items, abilities...), the id kept as BYTES: the PG family renames the objects with ids that are not ASCII.
import os
import re

from doctor.mpq import mpqread
from doctor.data import objbin
from doctor.data import slk


UNREADABLE = object()
EMPTY_ID = b'\x00\x00\x00\x00'
OBJECT_FILES = (('w3u', 'unit'), ('w3t', 'item'), ('w3a', 'ability'), ('w3b', 'destructable'), ('w3d', 'doodad'),
           ('w3h', 'buff'), ('w3q', 'upgrade'))
PREFIXES = ('war3map.', 'war3mapSkin.')
TABLES = ('Units\\UnitData.slk', 'Units\\UnitUI.slk', 'Units\\UnitBalance.slk', 'Units\\UnitAbilities.slk',
           'Units\\UnitWeapons.slk', 'Units\\ItemData.slk', 'Units\\AbilityData.slk', 'Units\\AbilityBuffData.slk',
           'Units\\UpgradeData.slk', 'Units\\DestructableData.slk', 'Doodads\\Doodads.slk',
           'Doodads\\DoodadsSkin.slk')
RACES = ('Campaign', 'Human', 'Orc', 'Undead', 'NightElf', 'Neutral')
PROFILES = tuple('Units\\%s%s%s.txt' % (race, kind_, part) for race in RACES for kind_ in ('Unit', 'Ability', 'Upgrade')
               for part in ('Func', 'Strings')) + (
    'Units\\UnitSkin.txt', 'Units\\ItemSkin.txt', 'Units\\AbilitySkin.txt', 'Units\\UpgradeSkin.txt',
    'Units\\DestructableSkin.txt', 'Units\\ItemFunc.txt', 'Units\\ItemStrings.txt', 'Units\\ItemAbilityFunc.txt',
    'Units\\ItemAbilityStrings.txt', 'Units\\CommonAbilityFunc.txt', 'Units\\CommonAbilityStrings.txt',
    'Units\\DestructableFunc.txt', 'Units\\DestructableStrings.txt', 'Units\\BuffFunc.txt', 'Units\\BuffStrings.txt',
    'Units\\UpgradeFunc.txt', 'Units\\UpgradeStrings.txt')
NOT_OBJECT = ('miscdata.txt', 'miscgame.txt', 'commandfunc.txt', 'commandstrings.txt')
CANONICAL = tuple('%s%s' % (prefix, ext) for prefix in PREFIXES for ext, _kind in OBJECT_FILES) + TABLES + PROFILES
CANONICAL_LOWER = set(name.lower() for name in CANONICAL)
RX_TABLE = re.compile(r'^(units|doodads)\\.+\.(slk|txt)$', re.I)
KIND_KEYS = (('abilitybuff', 'buff'), ('ability', 'ability'), ('destructable', 'destructable'), ('upgrade', 'upgrade'),
               ('buff', 'buff'), ('item', 'item'), ('unit', 'unit'), ('doodad', 'doodad'))
BREAKS = (('\n', '\\x0a'), ('\r', '\\x0d'), ('\x0b', '\\x0b'), ('\x0c', '\\x0c'), ('\x1c', '\\x1c'), ('\x1d', '\\x1d'),
          ('\x1e', '\\x1e'), ('\u2028', '\\u2028'), ('\u2029', '\\u2029'))


def _nothing(*_args):
    pass


def _text(b):
    return b.decode('utf-8', 'surrogateescape')


def _bytes(s):
    return s.encode('utf-8', 'surrogateescape')


def _visible(s):
    return ''.join(chr(b) if 0x20 <= b <= 0x7E else '\\x%02x' % b for b in _bytes(s))


def _not_visible(s):
    return any(b < 0x20 or b > 0x7E for b in _bytes(s))


def _line(ident):
    for c, escape in BREAKS:
        if c in ident:
            ident = ident.replace(c, escape)
    return ident


def _kind_of_name(name):
    lower = os.path.basename(name.replace('/', '\\')).lower()
    if lower in NOT_OBJECT:
        return None
    for key, kind in KIND_KEYS:
        if key in lower:
            return kind
    return None


def _read(a, name):
    try:
        if a.find(name) is None:
            return None
    except Exception:
        return None
    try:
        return a.read(name)
    except Exception:
        return UNREADABLE


def map_names(a):
    by_lower = {}
    data = _read(a, '(listfile)')
    if isinstance(data, bytes) and data:
        for line in _text(data).replace('\r\n', '\n').replace('\r', '\n').split('\n'):
            name = line.strip().replace('/', '\\')
            if name:
                by_lower.setdefault(name.lower(), name)
    for canonical in CANONICAL:
        if canonical.lower() in by_lower:
            continue
        try:
            if a.find(canonical) is not None:
                by_lower[canonical.lower()] = canonical
        except Exception:
            continue
    return by_lower


def _four_byte_ids(names):
    seen, ids, outside = set(), [], 0
    for name in names:
        b = _bytes(name)
        if len(b) != 4 or b == EMPTY_ID:
            outside += 1
        elif b not in seen:
            seen.add(b)
            ids.append(b)
    return ids, outside


def _object_ids(data, name):
    levelled = os.path.basename(name).lower() in objbin.WITH_LEVELS
    _ver, tables, _fim = objbin.read_data(data, levelled)
    seen, ids, zeros = set(), [], 0
    for table in tables:
        for old, new, _mods in table:
            for s in (new, old):
                b = s.encode('latin-1')
                if len(b) != 4 or b == EMPTY_ID:
                    zeros += 1
                elif b not in seen:
                    seen.add(b)
                    ids.append(b)
    return ids, zeros


def _table_ids(data, name):
    if name.lower().endswith('.slk'):
        _header, rows = slk.parse_slk_bytes(data)
        return _four_byte_ids(list(rows))
    return _four_byte_ids(list(slk.parse_ini_bytes(data)))


def extract(path, progress=None):
    p = progress or _nothing
    r = {'kinds': [], 'total': 0, 'text': '', 'duplicates': [], 'note': '', 'error': None}
    p('read_map')
    try:
        a = mpqread.Archive(path)
    except (Exception, SystemExit) as e:
        r['error'] = 'cannot read the map: %s' % (str(e).strip() or type(e).__name__)
        return r
    by_lower = map_names(a)
    sources = []
    p('objects')
    for prefix in PREFIXES:
        for ext, kind in OBJECT_FILES:
            name = by_lower.get((prefix + ext).lower())
            if name:
                sources.append((name, kind, True))
    p('tables')
    for canonical in TABLES + PROFILES:
        name = by_lower.get(canonical.lower())
        if name:
            sources.append((name, _kind_of_name(name), False))
    ignored = []
    for lower in sorted(by_lower):
        name = by_lower[lower]
        if lower in CANONICAL_LOWER or not RX_TABLE.match(name):
            continue
        kind = _kind_of_name(name)
        if kind:
            sources.append((name, kind, False))
        else:
            ignored.append(name)
    kinds, unreadable = [], []
    order, kind_of_id, sources_of_id = [], {}, {}
    zeros = not_four = 0
    for name, kind, object_class in sources:
        data = _read(a, name)
        if data is UNREADABLE:
            unreadable.append(name)
            continue
        if not data:
            continue
        try:
            ids, dropped = _object_ids(data, name) if object_class else _table_ids(data, name)
        except Exception as e:
            unreadable.append('%s (%s)' % (name, str(e)[:60]))
            continue
        if object_class:
            zeros += dropped
        else:
            not_four += dropped
        if not ids:
            continue
        id_texts = [_text(b) for b in ids]
        kinds.append({'kind': kind, 'source': name, 'ids': id_texts, 'count': len(id_texts),
                      'ansii': sum(1 for b in ids if _not_visible(_text(b)))})
        for ident in id_texts:
            if ident in kind_of_id:
                sources_of_id[ident].append(name)
            else:
                kind_of_id[ident] = kind
                order.append(ident)
                sources_of_id[ident] = [name]
    r['kinds'] = kinds
    r['duplicates'] = [{'id': ident, 'kind': kind_of_id[ident], 'sources': sources_of_id[ident]}
                       for ident in order if len(sources_of_id[ident]) > 1]
    r['text'] = ''.join('%s\t%s\n' % (kind_of_id[ident], _line(ident)) for ident in order)
    r['total'] = len(order)
    breaks = sum(1 for ident in order if any(c in ident for c, _e in BREAKS))
    parts = [
        'Read only from the map itself: the object files (war3map.w3u/w3t/w3a/w3b/w3d/w3h/w3q and the war3mapSkin '
        'twins) and the Units\\*/Doodads\\* .slk/.txt tables the map carries. The tables of the installed game are not '
        'read, so an id that exists only in the game is not listed.',
        'Rawcodes the script builds at run time (a JASS/Lua \'xxxx\' literal, the sum of two rawcodes, a number) are '
        'not read: this is the bytes of the map files, not the script.',
        'A table row counts as an id only when its name is exactly 4 bytes; the zero-filled id slot is not an id.',
        '\'ansii\' counts the ids of a source with a byte outside printable ASCII (0x20..0x7E): the PG family ships '
        'ids of control bytes and every one of them is kept byte for byte (the text is utf-8/surrogateescape, so '
        'ident.encode(\'utf-8\', \'surrogateescape\') is the id of the file).',
        'An id in more than one source is listed once, in the first source that has it, and every source of it is in '
        'duplicates.',
        'The kind of a Units\\*.txt profile comes from the file name: Units\\CommonAbilityStrings.txt mixes ability '
        'and buff ids under the ability kind, and Units\\AbilityBuffData.slk is the table that declares the buffs.',
    ]
    if zeros:
        parts.append('%d id slot(s) were zero-filled.' % zeros)
    if not_four:
        parts.append('%d row(s) of a table were not a 4-byte name and stayed out.' % not_four)
    if ignored:
        parts.append('Not an object table, stayed out: %s.' % ', '.join(_visible(n) for n in ignored))
    if unreadable:
        parts.append('Could not be read: %s.' % ', '.join(_visible(n) for n in unreadable))
    if breaks:
        parts.append('%d id(s) carry a byte Python reads as a line break and are written as \\xNN in text, so one line '
                      'holds one id; ids and the json keep the byte as it is.' % breaks)
    r['note'] = ' '.join(parts)
    return r


def unique_ids(r):
    order, seen = [], set()
    for k in r['kinds']:
        for ident in k['ids']:
            if ident not in seen:
                seen.add(ident)
                order.append(ident)
    return order


def report(r, path):
    print('%s: %d source(s), %d unique id(s)' % (os.path.basename(path), len(r['kinds']), r['total']))
    width = max([len(_visible(k['source'])) for k in r['kinds']] + [6])
    for k in r['kinds']:
        print('  %-13s %-*s %6d id(s) %6d not plain ASCII'
              % (k['kind'], width, _visible(k['source']), k['count'], k['ansii']))
    outside = [ident for ident in unique_ids(r) if _not_visible(ident)]
    print('ids with a byte outside printable ASCII: %d' % len(outside))
    if outside:
        print('examples (escaped): %s' % ', '.join(_visible(ident) for ident in outside[:8]))
    print('ids in more than one source: %d' % len(r['duplicates']))
    print('note: %s' % r['note'])
