# Turns numbers stored as text back into numbers in SLK tables, and removes the |n from lists of ids.
import io
import re
from collections import defaultdict


RE_NUM = re.compile(r'^-?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?$')
RE_ID_LIST_COLUMN = re.compile(r'^(abilList|heroAbilList|abilSkinList|heroAbilSkinList|auto|cooldownID|upgrades|'
                               r'Requires\d*|Builds|Sellitems|Sellunits|Makeitems|Trains|Researches|'
                               r'Upgrade|DependencyOr|UnitID\d+|BuffID\d+|EfctID\d+)$', re.I)
RE_ID_WITH_N = re.compile(r'^(\s*[A-Za-z0-9]{4})(?:\|n)+(\s*)$')


def slk_cells(line_list):
    cur_x = cur_y = None
    for i, line in enumerate(line_list):
        if not line.startswith('C;'):
            continue
        x = y = k = None
        for c in line.split(';')[1:]:
            if c.startswith('X') and c[1:2].isdigit():
                x = int(re.match(r'X(\d+)', c).group(1))
            elif c.startswith('Y') and c[1:2].isdigit():
                y = int(re.match(r'Y(\d+)', c).group(1))
            elif c.startswith('K'):
                k = c[1:]
        if x is not None:
            cur_x = x
        if y is not None:
            cur_y = y
        if k is not None:
            yield i, cur_x, cur_y, k


def strip_id_lists(line_list):
    name_list = {}
    for _, x, y, v in slk_cells(line_list):
        if y == 1:
            name_list[x] = v.strip('"')
    replacements = []
    for i, x, y, v in slk_cells(line_list):
        if y == 1 or not v.startswith('"') or '|n' not in v or not RE_ID_LIST_COLUMN.match(name_list.get(x, '')):
            continue
        pieces = v[1:-1].split(',') if v.endswith('"') and len(v) > 1 else None
        if pieces is None:
            continue
        added = [RE_ID_WITH_N.sub(r'\1\2', p) for p in pieces]
        if added == pieces:
            continue
        new = '"' + ','.join(added) + '"'
        line_list[i] = line_list[i].replace('K' + v, 'K' + new, 1)
        replacements.append((y, x, v, new))
    return replacements


def fixable(origin, dest=None):
    raw_bytes = io.open(origin, 'rb').read()
    txt = raw_bytes.decode('utf-8', 'surrogateescape')
    crlf = '\r\n' in txt
    line_list = txt.replace('\r\n', '\n').split('\n')
    replacements, numeric_columns = fix_numbers(line_list)
    replacements += strip_id_lists(line_list)

    if dest is None:
        dest = origin
    output = ('\r\n' if crlf else '\n').join(line_list)
    io.open(dest, 'wb').write(output.encode('utf-8', 'surrogateescape'))
    return replacements, numeric_columns


def fix_numbers(line_list):
    pluralize = defaultdict(lambda: [0, 0])
    for _, x, y, v in slk_cells(line_list):
        if y == 1:
            continue
        if v.startswith('"'):
            pluralize[x][1] += 1
        else:
            pluralize[x][0] += 1
    numeric_columns = set(x for x, (n, t) in pluralize.items() if n >= 10 and n > t * 9)

    replacements = []
    for i, x, y, v in slk_cells(line_list):
        if y == 1 or x not in numeric_columns or not v.startswith('"'):
            continue
        body = v.strip('"')
        if not RE_NUM.match(body):
            continue
        new = body.rstrip('.') if body.endswith('.') else body
        if new == '' or new == '-':
            new = '0'
        before = line_list[i]
        line_list[i] = before.replace('K' + v, 'K' + new, 1)
        replacements.append((y, x, v, new))
    return replacements, numeric_columns
