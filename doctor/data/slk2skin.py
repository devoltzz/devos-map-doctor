# Reads the model paths from the file column of the unit and item SLK tables.
import io
import os
import re
import sys

from doctor.data import slk_cols as C

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))

EN = os.path.join(ROOT, 'port', 'out', 'extract_en', 'units')
ORIG_UNITS = os.path.join(ROOT, 'port', 'extract', 'units')


def read_models(p, id_column, model_column):
    return models_of(C.read_data(p)[0], id_column, model_column)


def models_of(line_list, id_column, model_column):
    col, _ = C.slk_columns(line_list)
    inv = {v.lower(): k for k, v in col.items()}
    x_id, x_file = inv.get(id_column.lower()), inv.get(model_column.lower())
    if x_file is None:
        return {}, col
    if x_id is None:
        return None, col
    cur_x = cur_y = None
    ids, files = {}, {}
    for line in line_list:
        if not line.startswith('C;'):
            continue
        x = y = k = None
        for c in C.slk_fields(line):
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
        if k is None or cur_y == 1:
            continue
        if cur_x == x_id:
            ids[cur_y] = k.strip('"')
        elif cur_x == x_file:
            files[cur_y] = k.strip('"')
    return {uid: files[y] for y, uid in ids.items() if files.get(y)}, col


def write_skin(dest, models, heading):
    line_list = ['// %s' % heading,
                 '// Written by slk2skin: the model left the `file` column of the SLK, which',
                 '// crashes Warcraft 3.0, and now lives here, where the current version reads it.',
                 '']
    for uid in sorted(models):
        line_list += ['[%s]' % uid, 'file=%s' % models[uid], '']
    io.open(dest, 'wb').write(('\r\n'.join(line_list)).encode('utf-8', 'surrogateescape'))
    return len(models)


def main():
    global EN, ORIG_UNITS
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if args:
        EN = args[0]
        ORIG_UNITS = next((a.split('=', 1)[1] for a in sys.argv[1:] if a.startswith('--orig=')), args[0])
    total = 0
    for slk, id_column, dest, heading in (
            ('unitui.slk', 'unitUIID', 'UnitSkin.txt', 'Unit models'),
            ('itemdata.slk', 'itemID', 'ItemSkin.txt', 'Item models')):
        p_en = os.path.join(EN, slk)
        p_orig = os.path.join(ORIG_UNITS, slk)
        if not os.path.isfile(p_en) and not os.path.isfile(p_orig):
            print('%-14s is not in the map: nothing to move' % slk)
            continue
        source = p_en
        _, col = read_models(p_en, id_column, 'file')
        if 'file' not in [v.lower() for v in col.values()]:
            source = p_orig
            print('%s of extract_en already lacks the column; reading from port/extract' % slk)
        models, col = read_models(source, id_column, 'file')
        tgt = os.path.join(EN, dest)
        if models is None:
            print('%-14s without the %s column: the file column stays as it is' % (slk, id_column))
            continue
        if not models and os.path.isfile(tgt) and os.path.getsize(tgt):
            print('%-14s has no model column and %s is already written: kept' % (slk, dest))
            continue
        n = write_skin(tgt, models, heading)
        print('%-14s -> %-14s %d models' % (slk, dest, n))
        keep_names = set(v for v in col.values() if v.lower() != 'file')
        cols = C.filter_columns(source, p_en, keep_names)
        print('%-14s rewritten without the model column: %d columns' % (slk, cols))
        total += n
    print('total models moved:', total)


if __name__ == '__main__':
    main()
