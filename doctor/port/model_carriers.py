# Gives every model the script sets with DzSetUnitModel a unit type of its own (a "carrier").
# Reforged cannot put a model on a unit; the port borrows the skin of a unit type with that model (BlzSetUnitSkin).
# Without a type of its own the model either has no type at all (the unit does not change) or shares one with other
# types, and the first of them brings its own scale, tint and portrait. A carrier is a copy of a plain unit with
# neutral scale and tint, no abilities and that model. Its id is an ordinary lowercase one starting with PREFIX
# (never a hero); the port layer's model index prefers those ids over map types that share the model.
import io
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
        inner = body_text[m.end():end]
        args = morph_chaos.arguments(inner)
        if len(args) != 2:
            continue
        lit = RX_LITERAL.fullmatch(args[1].strip())
        if lit:
            p = _unescape(lit.group(1))
            if p.strip():
                out.append(p)
    return list(dict.fromkeys(out))


def _files(units):
    import os
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


def _new_ids(n, taken):
    out = []
    for a in DIGITS:
        for b in DIGITS:
            for c in DIGITS:
                cand = PREFIX + a + b + c
                if cand not in taken:
                    out.append(cand)
                if len(out) == n:
                    return out
    raise ValueError('no free unit id for the model carriers')


def add(units, body_text):
    info = {'carriers': [], 'models': 0, 'template': None}
    files = _files(units)
    if 'unitui.slk' not in files or 'unitdata.slk' not in files:
        return info
    tables = {}
    for name, path in files.items():
        line_list, crlf = C.read_data(path)
        tables[name] = (path, line_list, crlf) + _rows(line_list, ID_COLUMNS[name])
    models = script_models(body_text)
    info['models'] = len(models)
    if not models:
        return info
    ui = tables['unitui.slk']
    col_ui = dict((n.lower(), x) for x, n in ui[3].items())
    if 'file' not in col_ui:
        return info
    # the template: an ordinary walking ground unit (not a hero, not a building) present in every unit table
    common = set(ui[5])
    for name, t in tables.items():
        common &= set(t[5])
    data = tables['unitdata.slk']
    col_data = dict((n.lower(), x) for x, n in data[3].items())

    def field(u, name):
        x = col_data.get(name.lower())
        return next((k.strip('"') for x2, k in data[6].get(data[5][u], []) if x2 == x), '') if x else ''
    plain = [u for u in sorted(common) if u[:1].islower() and not u.startswith(PREFIX)]
    template = next((u for u in plain if field(u, 'movetp') == 'foot' and field(u, 'isbldg') in ('', '0')), None) \
        or next(iter(plain), None)
    if template is None:
        return info
    info['template'] = template
    taken = set()
    for t in tables.values():
        taken |= set(t[5])
    seen, wanted = set(), []
    for p in models:
        k = key(p)
        if k not in seen:
            seen.add(k)
            wanted.append(p)
    ids = _new_ids(len(wanted), taken)
    pairs = list(zip(ids, wanted))
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
    info['carriers'] = pairs
    return info
