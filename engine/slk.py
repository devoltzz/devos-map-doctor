# Reads SLK tables.
import re



def parse_slk_bytes(raw):
    txt = raw.decode('utf-8', 'surrogateescape')
    header = {}
    rows = {}
    cur_y = 0
    cells = {}
    for line in txt.split('\n'):
        line = line.rstrip('\r')
        if not line.startswith('C;') and not line.startswith('F;'):
            continue
        if line.startswith('F;'):
            continue
        x = None
        y = None
        k = None
        parts = line[2:].split(';')
        rebuilt = []
        buf = None
        for p in parts:
            if buf is not None:
                buf += ';' + p
                if buf.count('"') % 2 == 0:
                    rebuilt.append(buf)
                    buf = None
                continue
            if p.startswith('K"') and p.count('"') % 2 == 1:
                buf = p
                continue
            rebuilt.append(p)
        if buf is not None:
            rebuilt.append(buf)
        for p in rebuilt:
            if p.startswith('X'):
                x = int(p[1:])
            elif p.startswith('Y'):
                y = int(p[1:])
            elif p.startswith('K'):
                k = p[1:]
                if len(k) >= 2 and k[0] == '"' and k[-1] == '"':
                    k = k[1:-1]
        if y is not None:
            cur_y = y
        if x is None or k is None:
            continue
        cells.setdefault(cur_y, {})[x] = k
    if 1 not in cells:
        return [], {}
    header = cells[1]
    maxx = max(header)
    hdr = [header.get(i, '') for i in range(1, maxx + 1)]
    for y in sorted(cells):
        if y == 1:
            continue
        row = cells[y]
        rid = row.get(1)
        if rid is None:
            continue
        d = {}
        for x, v in row.items():
            name = header.get(x)
            if name:
                d[name] = v
        rows[rid] = d
    return hdr, rows


def parse_ini_bytes(raw):
    txt = raw.decode('utf-8', 'surrogateescape')
    data = {}
    cur = None
    for line in txt.split('\n'):
        line = line.rstrip('\r')
        if not line or line.startswith('//') or line.startswith(';'):
            continue
        m = re.match(r'^\[([^\]]+)\]\s*$', line)
        if m:
            cur = m.group(1)
            data.setdefault(cur, {})
            continue
        if cur is None:
            continue
        if '=' not in line:
            continue
        k, v = line.split('=', 1)
        k = k.strip()
        v = v.strip()
        if len(v) >= 2 and v[0] == '"' and v[-1] == '"':
            v = v[1:-1]
        data[cur][k] = v
    return data
