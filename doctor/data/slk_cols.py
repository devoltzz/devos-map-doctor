# Reads the cells of an SLK table and removes columns from it.
import io
import re



def read_data(p):
    return lines_of(io.open(p, 'rb').read())


def lines_of(data_bytes):
    txt = data_bytes.decode('utf-8', 'surrogateescape')
    txt = txt.replace('\r\r\n', '\r\n')
    return txt.replace('\r\n', '\n').split('\n'), ('\r\n' in txt)


def join_lines(line_list, crlf):
    return (('\r\n' if crlf else '\n').join(line_list)).encode('utf-8', 'surrogateescape')


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
        yield i, cur_x, cur_y, k


def slk_columns(line_list):
    out = {}
    empty_columns = set()
    used_entries = set()
    for _, x, y, k in slk_cells(line_list):
        if y == 1 and k:
            out[x] = k.strip('"')
        elif y and y > 1 and k is not None:
            used_entries.add(x)
    for x in out:
        if x not in used_entries:
            empty_columns.add(x)
    return out, empty_columns


def filter_columns(origin, dest, keep_names):
    line_list, crlf = read_data(origin)
    output, n = filter_lines(line_list, keep_names)
    io.open(dest, 'wb').write(join_lines(output, crlf))
    return n


def filter_lines(line_list, keep_names):
    col, _ = slk_columns(line_list)
    new_x = {}
    n = 0
    for x in sorted(col):
        if col[x] in keep_names:
            n += 1
            new_x[x] = n
    output = []
    cur_x = cur_y = None
    for line in line_list:
        if not line.startswith('C;'):
            output.append(line)
            continue
        x = y = None
        for c in line.split(';')[1:]:
            if c.startswith('X') and c[1:2].isdigit():
                x = int(re.match(r'X(\d+)', c).group(1))
            elif c.startswith('Y') and c[1:2].isdigit():
                y = int(re.match(r'Y(\d+)', c).group(1))
        if x is not None:
            cur_x = x
        if y is not None:
            cur_y = y
        if cur_x not in new_x:
            continue
        k = None
        for c in line.split(';')[1:]:
            if c.startswith('K'):
                k = c[1:]
        if k is None:
            continue
        output.append('C;X%d;Y%d;K%s' % (new_x[cur_x], cur_y, k))
    for i, line in enumerate(output):
        if line.startswith('B;'):
            output[i] = re.sub(r'X\d+', 'X%d' % n, line, count=1)
            break
    return output, n
