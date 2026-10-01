# Completes the half-written command button positions of the unit and ability text files.
import io


def complete(field_value):
    v = field_value.strip()
    if v == '':
        return '0,0'
    if ',' not in v:
        return v + ',0'
    x, _, y = v.partition(',')
    x, y = x.strip(), y.strip()
    return (x or '0') + ',' + (y or '0')


LEARN = {}


def insert_missing(line_list):
    output, sec, buf, n = [], None, [], 0

    def on_close():
        nonlocal n
        if sec in LEARN and not any(
                line.partition('=')[0].strip().lower() == 'researchbuttonpos' for line in buf):
            for j, line in enumerate(buf):
                if line.partition('=')[0].strip().lower() == 'buttonpos':
                    buf.insert(j + 1, 'Researchbuttonpos=' + LEARN[sec])
                    n += 1
                    break
        output.extend(buf)

    for line in line_list:
        if line.startswith('['):
            on_close()
            buf = []
            sec = line.strip()[1:-1]
            output.append(line)
            continue
        if sec is None:
            output.append(line)
        else:
            buf.append(line)
    on_close()
    return output, n


def complete_lines(line_list):
    n = 0
    for i, line in enumerate(line_list):
        if '=' not in line or line.startswith('['):
            continue
        k, _, v = line.partition('=')
        if not k.strip().lower().endswith('buttonpos'):
            continue
        new = complete(v)
        if new != v.strip():
            line_list[i] = k + '=' + new
            n += 1
    return n


def fixable(p):
    txt = io.open(p, encoding='utf-8', newline='', errors='surrogateescape').read()
    crlf = '\r\n' in txt
    line_list = txt.replace('\r\n', '\n').split('\n')
    n = 0
    line_list, n = insert_missing(line_list)
    n += complete_lines(line_list)
    if n:
        io.open(p, 'wb').write((('\r\n' if crlf else '\n').join(line_list)).encode('utf-8', 'surrogateescape'))
    return n
