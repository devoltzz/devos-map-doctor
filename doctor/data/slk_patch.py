# Fixes the data tables of old SLK maps that Warcraft III 3.0 no longer accepts.

from doctor.data import buttonpos_fix
from doctor.fix import fdf_fix
from doctor.data import slk2skin
from doctor.data import slk_cols
from doctor.data import slk_fix
from doctor.data import slk_levels


TABLES = ('Units\\UnitData.slk', 'Units\\UnitUI.slk', 'Units\\UnitBalance.slk', 'Units\\UnitAbilities.slk',
          'Units\\UnitWeapons.slk', 'Units\\ItemData.slk', 'Units\\AbilityData.slk', 'Units\\AbilityBuffData.slk',
          'Units\\UpgradeData.slk', 'Units\\DestructableData.slk', 'Doodads\\Doodads.slk')
PROFILES = ('Units\\UnitSkin.txt', 'Units\\ItemSkin.txt', 'Units\\AbilitySkin.txt', 'Units\\UpgradeSkin.txt',
            'Units\\DestructableSkin.txt', 'Units\\MiscData.txt', 'Units\\MiscGame.txt', 'Units\\CommandFunc.txt',
            'Units\\CommandStrings.txt', 'Units\\ItemFunc.txt', 'Units\\ItemStrings.txt', 'Units\\ItemAbilityFunc.txt',
            'Units\\ItemAbilityStrings.txt', 'Units\\CommonAbilityFunc.txt', 'Units\\CommonAbilityStrings.txt') + tuple(
    'Units\\%s%s%s.txt' % (race, kind, part)
    for race in ('Campaign', 'Human', 'Orc', 'Undead', 'NightElf', 'Neutral')
    for kind in ('Unit', 'Ability', 'Upgrade') for part in ('Func', 'Strings'))
MODEL_TABLES = (('Units\\UnitUI.slk', 'unitUIID', 'Units\\UnitSkin.txt'),
                ('Units\\ItemData.slk', 'itemID', 'Units\\ItemSkin.txt'))
PROBLEMS = ('file_column', 'levels', 'buttonpos', 'fdf_comment', 'id_lists', 'quoted_numbers')
SKIN_BANNER = ('// Model paths moved out of the SLK tables by Devo\'s Map Doctor: Warcraft III 3.0 crashes on the',
               '// `file` column of UnitUI.slk and ItemData.slk and reads the model from here.')
_lines = slk_cols.lines_of
_join = slk_cols.join_lines


def _find(files, name):
    low = name.lower()
    return next((k for k in files if k.lower() == low), None)


def is_slk_map(names):
    low = set(n.lower() for n in names)
    return [t for t in TABLES + PROFILES if t.lower() in low]


def table_files(names, read):
    wanted = {}
    for n in list(names) + list(TABLES) + list(PROFILES):
        low = n.lower()
        if low.endswith('.fdf') or (low.startswith('units\\') and low.endswith(('.slk', '.txt'))) or \
                low == 'doodads\\doodads.slk':
            wanted.setdefault(low, n)
    out = {}
    for low, n in sorted(wanted.items()):
        try:
            b = read(n)
        except Exception:
            b = None
        if b:
            out[n] = b
    return out


def header(lines):
    return slk_cols.slk_columns(lines)[0]


def table(lines):
    cols = header(lines)
    rows = {}
    for _i, x, y, k in slk_cols.slk_cells(lines):
        if y is None or y < 2 or k is None:
            continue
        rows.setdefault(y, {})[cols.get(x, str(x))] = k.strip('"')
    return rows, cols


def merge_profile(b, entries, banner=SKIN_BANNER):
    if b is None:
        lines, crlf = list(banner) + [''], True
    else:
        lines, crlf = _lines(b)
    where, current = {}, None
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith('[') and s.endswith(']'):
            current = s[1:-1]
            where.setdefault(current, [i, None])
        elif current is not None and '=' in s and not s.startswith('//') and \
                s.partition('=')[0].strip().lower() == 'file' and where[current][1] is None:
            where[current][1] = i
    replace, insert, tail = {}, {}, []
    for code in sorted(entries):
        if code in where:
            head, at = where[code]
            if at is not None:
                replace[at] = 'file=' + entries[code]
            else:
                insert.setdefault(head, []).append('file=' + entries[code])
        else:
            tail += ['[%s]' % code, 'file=' + entries[code], '']
    out = []
    for i, line in enumerate(lines):
        out.append(replace.get(i, line))
        out.extend(insert.get(i, ()))
    if tail:
        while out and out[-1] == '':
            out.pop()
        out += [''] + tail
    return _join(out, crlf)


def fix_file_column(files, cur, report):
    for slk, id_col, skin in MODEL_TABLES:
        name = _find(cur, slk)
        if not name:
            continue
        lines, crlf = _lines(cur[name])
        models, cols = slk2skin.models_of(lines, id_col, 'file')
        if 'file' not in [c.lower() for c in cols.values()]:
            continue
        if models is None:
            report.setdefault('file_column', {})[name] = 0
            report.setdefault('notes', []).append('%s: no %s column, so the file column stays' % (name, id_col))
            continue
        skin_name = _find(cur, skin) or skin
        cur[skin_name] = merge_profile(cur.get(skin_name), models)
        keep = set(c for c in cols.values() if c.lower() != 'file')
        cur[name] = _join(slk_cols.filter_lines(lines, keep)[0], crlf)
        report.setdefault('file_column', {})[name] = len(models)


def _each_slk(cur, report, key, fix):
    for name in sorted(cur):
        if not name.lower().endswith('.slk'):
            continue
        lines, crlf = _lines(cur[name])
        n = len(fix(lines))
        if n:
            cur[name] = _join(lines, crlf)
            report.setdefault(key, {})[name] = n


def fix_quoted_numbers(files, cur, report):
    _each_slk(cur, report, 'quoted_numbers', lambda lines: slk_fix.fix_numbers(lines)[0])


def fix_id_lists(files, cur, report):
    _each_slk(cur, report, 'id_lists', slk_fix.strip_id_lists)


def fix_buttonpos(files, cur, report):
    for name in sorted(cur):
        low = name.lower()
        if not (low.startswith('units\\') and low.endswith('.txt')):
            continue
        lines, crlf = _lines(cur[name])
        n = buttonpos_fix.complete_lines(lines)
        if n:
            cur[name] = _join(lines, crlf)
            report.setdefault('buttonpos', {})[name] = n


def fix_fdf_comment(files, cur, report):
    for name in sorted(cur):
        if not name.lower().endswith('.fdf'):
            continue
        b, removed, _open = fdf_fix.fixable(cur[name])
        if removed:
            cur[name] = b
            report.setdefault('fdf_comment', {})[name] = len(removed)


def fix_levels(files, cur, report):
    name = _find(cur, 'Units\\AbilityData.slk')
    if not name:
        return
    lines, crlf = _lines(cur[name])
    if not header(lines):
        return
    r = slk_levels.add_levels(lines)
    if r and r['plain_name']:
        cur[name] = _join(r['line_list'], crlf)
        report.setdefault('levels', {})[name] = len(r['plain_name']) * len(slk_levels.NEW_LEVELS)


FIXES = (('file_column', fix_file_column), ('quoted_numbers', fix_quoted_numbers), ('id_lists', fix_id_lists),
         ('buttonpos', fix_buttonpos), ('fdf_comment', fix_fdf_comment), ('levels', fix_levels))


_CACHE = []
CACHE_SIZE = 2


def _key(files, only):
    import hashlib
    h = hashlib.blake2b(digest_size=20)
    for n in sorted(files):
        b = files[n]
        h.update(n.encode('utf-8', 'surrogateescape') + b'\0' + (b'-' if b is None else b'%d\0' % len(b) + b))
    return (h.digest(), None if only is None else tuple(sorted(only)))


def patch(files, only=None):
    import copy
    key = _key(files, only)
    for k, res in _CACHE:
        if k == key:
            return copy.deepcopy(res)
    res = _patch(files, only)
    _CACHE.insert(0, (key, copy.deepcopy(res)))
    del _CACHE[CACHE_SIZE:]
    return res


def _patch(files, only=None):
    cur = dict(files)
    report = {}
    for key, fix in FIXES:
        if only is None or key in only:
            fix(files, cur, report)
    changed = dict((n, b) for n, b in cur.items() if files.get(n) != b)
    return changed, report


def scan(files):
    _changed, report = patch(files)
    return dict((k, sum(v.values())) for k, v in report.items() if k in PROBLEMS)
