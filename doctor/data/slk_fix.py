# Turns numbers stored as text back into numbers in SLK tables, and removes the |n from lists of ids.
import io
import os
import re
import sys
from collections import defaultdict

from doctor.data import slk_cols


RE_NUMBER = re.compile(r'^-?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?$')
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
        for c in (slk_cols.slk_fields(line) if '"' in line else line.split(';')[1:]):
            c0 = c[:1]
            if c0 == 'X' and c[1:2].isdigit():
                x = int(slk_cols.RX_X.match(c).group(1))
            elif c0 == 'Y' and c[1:2].isdigit():
                y = int(slk_cols.RX_Y.match(c).group(1))
            elif c0 == 'K':
                k = c[1:]
        if x is not None:
            cur_x = x
        if y is not None:
            cur_y = y
        if k is not None:
            yield i, cur_x, cur_y, k


def _apply(line_list, r):
    for _ in range(r.int()):
        i = r.int()
        line_list[i] = r.body_text()
    return [(r.int(), r.int(), r.body_text(), r.body_text()) for _ in range(r.int())]


def strip_id_lists(line_list):
    b = slk_cols._text(line_list)
    r = slk_cols._call(2, b)
    if r is not None:
        name_list = dict((r.int(), r.body_text()) for _ in range(r.int()))
        tgt = [x for x, fname in name_list.items() if RE_ID_LIST_COLUMN.match(fname)]
        if not tgt:
            return []
        r = slk_cols._call(3, b, slk_cols._ints(len(tgt), *tgt))
        if r is not None:
            return _apply(line_list, r)
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
    r = slk_cols._step(1, line_list)
    if r is not None:
        numeric_columns = set(r.int() for _ in range(r.int()))
        return _apply(line_list, r), numeric_columns
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
        if not RE_NUMBER.match(body):
            continue
        new = body.rstrip('.') if body.endswith('.') else body
        if new == '' or new == '-':
            new = '0'
        before = line_list[i]
        line_list[i] = before.replace('K' + v, 'K' + new, 1)
        replacements.append((y, x, v, new))
    return replacements, numeric_columns


def main():
    if '--todos' in sys.argv:
        args = [a for a in sys.argv[1:] if not a.startswith('--')]
        src_path, dst = args[0], args[1]
        total = 0
        for f in sorted(os.listdir(src_path)):
            if not f.lower().endswith('.slk'):
                continue
            replacements, _ = fixable(os.path.join(src_path, f), os.path.join(dst, f))
            print('%-24s %d cell(s) fixed' % (f, len(replacements)))
            total += len(replacements)
        print('total:', total)
        return

    origin = sys.argv[1]
    dest = sys.argv[2] if len(sys.argv) > 2 else None
    replacements, numeric_columns = fixable(origin, dest)
    n_lists = sum(1 for _, _, v, _ in replacements if '|n' in v)
    print('%s: %d numeric columns, %d cell(s) fixed (%d number(s) as text, %d id list(s) with |n)'
          % (origin, len(numeric_columns), len(replacements), len(replacements) - n_lists, n_lists))
    touched_lines = sorted(set(y for y, _, _, _ in replacements))
    if touched_lines:
        print('lines touched: %d (from %d to %d)' % (len(touched_lines), touched_lines[0], touched_lines[-1]))
        for y, x, v, new in replacements[:6]:
            print('   line %-5d column %-3d %s -> %s' % (y, x, v, new))


if __name__ == '__main__':
    main()
