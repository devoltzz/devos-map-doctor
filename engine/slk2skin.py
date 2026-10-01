# Reads the model paths from the file column of the unit and item SLK tables.
import re

import slk_cols as C


def models_of(line_list, id_column, model_column):
    col, _ = C.slk_columns(line_list)
    inv = {v.lower(): k for k, v in col.items()}
    x_id, x_file = inv.get(id_column.lower()), inv.get(model_column.lower())
    if x_id is None or x_file is None:
        return {}, col
    cur_x = cur_y = None
    ids, files = {}, {}
    for line in line_list:
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
        if k is None or cur_y == 1:
            continue
        if cur_x == x_id:
            ids[cur_y] = k.strip('"')
        elif cur_x == x_file:
            files[cur_y] = k.strip('"')
    return {uid: files[y] for y, uid in ids.items() if files.get(y)}, col

