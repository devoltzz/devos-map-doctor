# Changes the type of a unit on Warcraft III 3.0 with one chaos ability per target type.
import io
import re

import slk_cols as C


RX_FUNC = re.compile(r'(?m)^function (\w+) takes')
RX_RAW = re.compile(r"^'([0-9A-Za-z]{4})'$")


def on_close(s, i):
    max_depth = 1
    n = len(s)
    while i < n:
        c = s[i]
        if c == '"':
            i += 1
            while i < n and s[i] != '"':
                i += 2 if s[i] == '\\' else 1
        elif c == "'":
            j = s.find("'", i + 1)
            i = j if j > 0 else i
        elif c == '(':
            max_depth += 1
        elif c == ')':
            max_depth -= 1
            if max_depth == 0:
                return i
        i += 1
    return -1


def arguments(s):
    out, max_depth, begin, i = [], 0, 0, 0
    while i < len(s):
        c = s[i]
        if c == '"':
            i += 1
            while i < len(s) and s[i] != '"':
                i += 2 if s[i] == '\\' else 1
        elif c == "'":
            j = s.find("'", i + 1)
            i = j if j > 0 else i
        elif c == '(':
            max_depth += 1
        elif c == ')':
            max_depth -= 1
        elif c == ',' and max_depth == 0:
            out.append(s[begin:i].strip())
            begin = i + 1
        i += 1
    out.append(s[begin:].strip())
    return out


def _calls(body, fname):
    out = []
    for m in re.finditer(r'\b%s\(' % re.escape(fname), body):
        a = m.end()
        b = on_close(body, a)
        if b < 0:
            continue
        out.append(arguments(body[a:b]))
    return out


def targets(body_text, native='DzSetUnitID'):
    starts = [(m.start(), m.group(1)) for m in RX_FUNC.finditer(body_text)] + [(len(body_text), None)]
    all_items, sitios, failures = set(), [], []
    for k in range(len(starts) - 1):
        begin, fname = starts[k]
        body = body_text[begin:starts[k + 1][0]]
        chamadas = _calls(body, native)
        if not chamadas:
            continue
        for args in chamadas:
            if len(args) != 2:
                failures.append('%s: %s with %d arguments' % (fname, native, len(args)))
                continue
            arg = args[1]
            h = re.match(r'^(?:\$|0[xX])([0-9A-Fa-f]{8})$', arg.strip())
            if h:
                raw_data = bytes.fromhex(h.group(1))
                if all(48 <= c <= 57 or 65 <= c <= 90 or 97 <= c <= 122 for c in raw_data):
                    arg = "'%s'" % raw_data.decode('ascii')
            m = RX_RAW.match(arg)
            if m:
                sitios.append((fname, arg, {m.group(1)}))
                all_items.add(m.group(1))
                continue
            d = re.match(r'^LoadInteger\((\w+), (.*), (0x[0-9A-Fa-f]+|-?\d+)\)$', arg)
            if not d:
                failures.append('%s: target that is neither a rawcode nor a YDWE LoadInteger: %s' % (fname, arg[:120]))
                continue
            tab, hash_key = d.group(1), d.group(3)
            vals = set()
            for s in _calls(body, 'SaveInteger'):
                if len(s) == 4 and s[0] == tab and s[2] == hash_key:
                    r = RX_RAW.match(s[3])
                    if r:
                        vals.add(r.group(1))
                    elif s[3].startswith('GetUnitTypeId('):
                        continue
                    else:
                        failures.append(
                            '%s: the dynamic target gets a value that is not a rawcode: %s' % (fname, s[3][:80])
                        )
            if not vals:
                failures.append(
                    '%s: dynamic target without a literal SaveInteger in the function (%s)' % (fname, arg[:120])
                )
            sitios.append((fname, arg, vals))
            all_items |= vals
    return sorted(all_items), sitios, failures


COLUMNS = [('alias', '"%(alias)s"'), ('code', '"Acha"'), ('race', '"other"'), ('levels', '1'), ('targs1', '"_"'),
           ('Cast1', '0'), ('Dur1', '0'), ('HeroDur1', '0'), ('Cool1', '0'), ('Cost1', '0'), ('Area1', '0'),
           ('Rng1', '0'), ('UnitID1', '"%(tgt)s"')]


def slk_ids(file_path):
    line_list, _ = C.read_data(file_path)
    col, _ = C.slk_columns(line_list)
    x_alias = next(x for x, n in col.items() if n.lower() == 'alias')
    ids = set()
    for _i, x, y, k in C.slk_cells(line_list):
        if x == x_alias and y and y > 1 and k:
            ids.add(k.strip('"'))
    return ids


def aliases(n, existing_ones, prefix='K9'):
    if n <= 0:
        return []
    out = []
    dig = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    for c1 in dig:
        for c2 in dig:
            a = prefix + c1 + c2
            if a not in existing_ones:
                out.append(a)
            if len(out) == n:
                return out
    raise ValueError('no free alias with the prefix %s' % prefix)


def add_levels(slk, strings, pairs):
    line_list, crlf = C.read_data(slk)
    col, _ = C.slk_columns(line_list)
    by_name = {n.lower(): x for x, n in col.items()}
    if not pairs:
        return 0, 0
    missing_items = [c for c in ('alias', 'code', 'UnitID1') if c.lower() not in by_name]
    if missing_items:
        raise ValueError('AbilityData.slk without the columns %s' % missing_items)
    existing_ones = slk_ids(slk)
    new_ones = [(a, t) for a, t in pairs if a not in existing_ones]
    if new_ones:
        bi = [i for i, line in enumerate(line_list) if line.startswith('B;')]
        if len(bi) != 1:
            raise ValueError('AbilityData.slk with %d B records (normalize first: slk_normaliza.py)' % len(bi))
        b = line_list[bi[0]]
        mx = int(re.search(r'X(\d+)', b).group(1))
        my = int(re.search(r'Y(\d+)', b).group(1))
        end_pos = max(i for i, line in enumerate(line_list) if line.strip() == 'E')
        extra = []
        y = my
        for a, t in new_ones:
            y += 1
            for fname, mold in COLUMNS:
                if fname.lower() not in by_name:
                    continue
                extra.append('C;X%d;Y%d;K%s' % (by_name[fname.lower()], y, mold % {'alias': a, 'tgt': t}))
        line_list = line_list[:end_pos] + extra + line_list[end_pos:]
        line_list[bi[0]] = 'B;X%d;Y%d;D0' % (mx, y)
        io.open(slk, 'wb').write(('\r\n' if crlf else '\n').join(line_list).encode('utf-8', 'surrogateescape'))
    txt = io.open(strings, 'rb').read().decode('utf-8', 'surrogateescape')
    nl = '\r\n' if '\r\n' in txt else '\n'
    sections = [(a, t) for a, t in pairs if ('[%s]' % a) not in txt]
    if sections:
        if not txt.endswith(nl):
            txt += nl
        for a, t in sections:
            txt += '[%s]%sArt=,%s' % (a, nl, nl)
        io.open(strings, 'wb').write(txt.encode('utf-8', 'surrogateescape'))
    return len(new_ones), len(sections)


def segment(pairs):
    out = []
    for i, (a, t) in enumerate(pairs):
        out.append("    %s alvo=='%s' then" % ('if' if i == 0 else 'elseif', t))
        out.append("        return '%s'" % a)
    if pairs:
        out.append('    endif')
    return ''.join(line + '\n' for line in out)
