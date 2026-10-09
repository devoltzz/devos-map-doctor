# Gives every model a map script sets on a unit its own unit type, so Warcraft III 3.0 can show it.
import io
import os
import re

from doctor.data import slk_cols as C
from doctor.port import morph_chaos


RX_SET_MODEL = re.compile(r'\bDzSetUnitModel\s*\(')
RX_LITERAL = re.compile(r'"((?:[^"\\]|\\.)*)"')
ID_COLUMNS = {'unitdata.slk': 'unitID', 'unitui.slk': 'unitUIID', 'unitbalance.slk': 'unitBalanceID',
              'unitweapons.slk': 'unitWeapID', 'unitabilities.slk': 'unitAbilID'}
OVERRIDES = {'unitui.slk': {'modelScale': '1', 'scale': '1', 'red': '255', 'green': '255', 'blue': '255'},
             'unitabilities.slk': {'abilList': '"_"', 'heroAbilList': '"_"'}}
PREFIX = 'z'
DIGITS = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
RX_CARRIER_B = re.compile(rb'(?=(' + PREFIX.encode('ascii') + rb'[0-9A-Z]{3}))')
OBJECT_EXTS = ('.w3u', '.w3t', '.w3a', '.w3b', '.w3d', '.w3h', '.w3q')


def _unescape(s):
    return re.sub(r'\\(.)', r'\1', s)


def key(path):
    p = path.replace('/', '\\').lower()
    return p[:-4] if p[-4:] in ('.mdl', '.mdx') else p


def script_models(body_text):
    out = []
    for m in RX_SET_MODEL.finditer(body_text):
        end = morph_chaos.on_close(body_text, m.end())
        if end < 0:
            continue
        args = morph_chaos.arguments(body_text[m.end():end])
        if len(args) != 2:
            continue
        lit = RX_LITERAL.fullmatch(args[1].strip())
        if lit:
            p = _unescape(lit.group(1))
            if p.strip():
                out.append(p)
    return list(dict.fromkeys(out))


def _files(units):
    return dict((f.lower(), os.path.join(units, f)) for f in os.listdir(units) if f.lower() in ID_COLUMNS)


def _rows(line_list, id_column):
    col, _ = C.slk_columns(line_list)
    x_id = next((x for x, n in col.items() if n.lower() == id_column.lower()), None)
    if x_id is None:
        return col, None, {}, {}
    ids, cells = {}, {}
    for _i, x, y, k in C.slk_cells(line_list):
        if y is None or y < 2 or k is None:
            continue
        cells.setdefault(y, []).append((x, k))
        if x == x_id:
            ids[k.strip('"')] = y
    return col, x_id, ids, cells


def taken_ids(units, body_text, extract=None):
    out = set()
    blobs = [body_text.encode('utf-8', 'surrogateescape')]
    folders = [units] + ([extract, os.path.join(extract, 'Units'), os.path.join(extract, 'units')] if extract else [])
    for d in dict.fromkeys(os.path.normcase(os.path.abspath(x)) for x in folders):
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            low = f.lower()
            if low.endswith(('.slk', '.txt')) or (low.startswith('war3map') and low.endswith(OBJECT_EXTS)):
                blobs.append(open(os.path.join(d, f), 'rb').read())
    for b in blobs:
        out.update(m.decode('latin-1') for m in RX_CARRIER_B.findall(b))
    return out


def _new_ids(n, taken):
    out = []
    if n <= 0:
        return out
    for a in DIGITS:
        for b in DIGITS:
            for c in DIGITS:
                cand = PREFIX + a + b + c
                if cand not in taken:
                    out.append(cand)
                if len(out) == n:
                    return out
    raise ValueError('no free unit id for the model carriers')


def template_unit(tables):
    with_id = [t for t in tables.values() if t[4] is not None]
    if not with_id:
        return None
    common = set(with_id[0][5])
    for t in with_id[1:]:
        common &= set(t[5])
    cols = [(t, dict((n.lower(), x) for x, n in t[3].items())) for t in with_id]

    def field(u, name):
        for t, c in cols:
            x = c.get(name.lower())
            if x is not None:
                return next((k.strip('"') for x2, k in t[6].get(t[5][u], []) if x2 == x), '')
        return ''
    plain = [u for u in sorted(common) if u[:1].islower() and not u.startswith(PREFIX)
             and field(u, 'isbldg') in ('', '0') and field(u, 'buildingShadow') in ('', '_')
             and field(u, 'uberSplat') in ('', '_')]
    return next((u for u in plain if field(u, 'movetp') == 'foot'), None) or next(iter(plain), None)


def add(units, body_text, extract=None, write=True):
    info = {'carriers': [], 'models': 0, 'template': None}
    files = _files(units)
    if 'unitui.slk' not in files or 'unitdata.slk' not in files:
        return info
    models = script_models(body_text)
    info['models'] = len(models)
    if not models:
        return info
    tables = {}
    for name, path in files.items():
        line_list, crlf = C.read_data(path)
        tables[name] = (path, line_list, crlf) + _rows(line_list, ID_COLUMNS[name])
    ui = tables['unitui.slk']
    col_ui = dict((n.lower(), x) for x, n in ui[3].items())
    if 'file' not in col_ui or ui[4] is None:
        return info
    template = template_unit(tables)
    if template is None:
        return info
    info['template'] = template
    taken = taken_ids(units, body_text, extract)
    for t in tables.values():
        taken |= set(t[5])
    seen, wanted = set(), []
    for p in models:
        k = key(p)
        if k not in seen:
            seen.add(k)
            wanted.append(p)
    pairs = list(zip(_new_ids(len(wanted), taken), wanted))
    info['carriers'] = pairs
    if not write:
        return info
    for name, (path, line_list, crlf, col, x_id, row_ids, cells) in tables.items():
        if x_id is None:
            continue
        by_name = dict((n.lower(), x) for x, n in col.items())
        over = dict((by_name[c.lower()], v) for c, v in OVERRIDES.get(name, {}).items() if c.lower() in by_name)
        bi = [i for i, line in enumerate(line_list) if line.startswith('B;')]
        if len(bi) != 1:
            raise ValueError('%s with %d B records (normalize it first)' % (name, len(bi)))
        mx = int(re.search(r'X(\d+)', line_list[bi[0]]).group(1))
        my = max(int(re.search(r'Y(\d+)', line_list[bi[0]]).group(1)), max(cells) if cells else 1)
        end_pos = max(i for i, line in enumerate(line_list) if line.strip() == 'E')
        template_cells = dict(cells.get(row_ids[template], []))
        extra = []
        y = my
        for new_id, model in pairs:
            y += 1
            row = dict(template_cells)
            row[x_id] = '"%s"' % new_id
            row.update(over)
            if name == 'unitui.slk':
                row[col_ui['file']] = '"%s"' % model
            for x in sorted(row):
                extra.append('C;X%d;Y%d;K%s' % (x, y, row[x]))
        line_list = line_list[:end_pos] + extra + line_list[end_pos:]
        line_list[bi[0]] = 'B;X%d;Y%d;D0' % (mx, y)
        io.open(path, 'wb').write(C.join_lines(line_list, crlf))
    return info
