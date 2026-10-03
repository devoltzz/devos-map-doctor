# Adds the columns of ability levels 5 and 6 to AbilityData.slk, as copies of level 4.
import io
import os
import re
import sys

from doctor.data import slk_cols as C

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))

LEVEL_FIELDS = ['Area', 'BuffID', 'Cast', 'Cool', 'Cost',
                'DataA', 'DataB', 'DataC', 'DataD', 'DataE', 'DataF', 'DataG', 'DataH', 'DataI',
                'Dur', 'EfctID', 'HeroDur', 'Rng', 'UnitID', 'targs']
NEW_LEVELS = (5, 6)


def resolve(line_list):
    out = []
    cx = cy = None
    for i, line in enumerate(line_list):
        if not line.startswith('C;'):
            continue
        x = y = k = None
        for f in line.split(';')[1:]:
            if f[:1] == 'X' and f[1:2].isdigit():
                x = int(re.match(r'X(\d+)', f).group(1))
            elif f[:1] == 'Y' and f[1:2].isdigit():
                y = int(re.match(r'Y(\d+)', f).group(1))
            elif f[:1] == 'K':
                k = f[1:]
        if x is not None:
            cx = x
        if y is not None:
            cy = y
        out.append((i, cx, cy, k))
    return out


def add_levels(line_list):
    col, _ = C.slk_columns(line_list)
    if not col:
        return None
    inv = dict((v, x) for x, v in col.items())
    if any(('%s5' % c) in inv for c in LEVEL_FIELDS):
        return None

    next_item = max(col)
    plain_name = []
    warnings = []
    for c in LEVEL_FIELDS:
        x4 = inv.get('%s4' % c)
        if x4 is None:
            warnings.append(c)
            continue
        new_ones = []
        for n in NEW_LEVELS:
            next_item += 1
            new_ones.append((next_item, '%s%d' % (c, n)))
        plain_name.append((x4, new_ones))

    resolved = resolve(line_list)
    level4 = {}
    for _, x, y, k in resolved:
        if k is not None and y is not None and y > 1:
            level4[(y, x)] = k

    def new_cells(y):
        out = []
        for x4, new_ones in plain_name:
            for xn, fname in new_ones:
                if y == 1:
                    out.append('C;X%d;Y1;K"%s"' % (xn, fname))
                else:
                    k = level4.get((y, x4))
                    if k is not None:
                        out.append('C;X%d;Y%d;K%s' % (xn, y, k))
        return out

    by_index = dict((i, (x, y, k)) for i, x, y, k in resolved)
    output = []
    current_row = None
    copied = 0
    for i, line in enumerate(line_list):
        if i in by_index:
            x, y, k = by_index[i]
            if current_row is not None and y != current_row:
                added = new_cells(current_row)
                copied += len(added)
                output.extend(added)
            current_row = y
            if k is not None:
                output.append('C;X%d;Y%d;K%s' % (x, y, k))
        else:
            if line.startswith('E') and current_row is not None:
                added = new_cells(current_row)
                copied += len(added)
                output.extend(added)
                current_row = None
            output.append(line)
    if current_row is not None:
        added = new_cells(current_row)
        copied += len(added)
        output.extend(added)

    for i, line in enumerate(output):
        if line.startswith('B;'):
            output[i] = re.sub(r'X\d+', 'X%d' % next_item, line, count=1)
            break
    return {
        'line_list': output,
        'plain_name': plain_name,
        'copied': copied,
        'next_item': next_item,
        'warnings': warnings,
    }


def main():
    p = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'port', 'out', 'extract_en', 'units',
                                                          'abilitydata.slk')
    line_list, crlf = C.read_data(p)
    r = add_levels(line_list)
    if r is None:
        print('%s already has level 5 columns; nothing to do' % p)
        return
    for c in r['warnings']:
        print('warning: column %s4 does not exist, field skipped' % c)
    io.open(p, 'wb').write((('\r\n' if crlf else '\n').join(r['line_list'])).encode('utf-8', 'surrogateescape'))
    print(
        '%s: %d new columns (%d fields x levels %s), %d cells copied from level 4, B;X%d'
        % (
            p,
            len(r['plain_name']) * len(NEW_LEVELS),
            len(r['plain_name']),
            '/'.join(map(str, NEW_LEVELS)),
            r['copied'],
            r['next_item'],
        )
    )


if __name__ == '__main__':
    main()
