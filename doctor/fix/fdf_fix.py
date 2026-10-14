# Removes a */ that closes no comment from a frame definition file (.fdf).
def fixable(data_bytes):
    out = bytearray()
    removed = []
    i = 0
    n = len(data_bytes)
    status = 'normal'
    block_start = None
    while i < n:
        c = data_bytes[i:i + 1]
        d = data_bytes[i:i + 2]
        if status == 'normal':
            if d == b'//':
                status = 'ln'
                out += d
                i += 2
                continue
            if d == b'/*':
                status = 'block_entry'
                block_start = i
                out += d
                i += 2
                continue
            if d == b'*/':
                removed.append(i)
                i += 2
                continue
            if c == b'"':
                status = 'body_text'
            out += c
            i += 1
            continue
        if status == 'ln':
            if c in (b'\n', b'\r'):
                status = 'normal'
            out += c
            i += 1
            continue
        if status == 'block_entry':
            if d == b'*/':
                status = 'normal'
                out += d
                i += 2
                continue
            out += c
            i += 1
            continue
        if c == b'"' or c in (b'\n', b'\r'):
            status = 'normal'
        out += c
        i += 1
    unclosed = [block_start] if status == 'block_entry' else []
    return bytes(out), removed, unclosed


def fix_toc(data_bytes):
    if not data_bytes or data_bytes.endswith((b'\n', b'\r')):
        return data_bytes, False
    eol = b'\r\n' if b'\r\n' in data_bytes else (b'\n' if b'\n' in data_bytes else b'\r\n')
    return data_bytes + eol + eol, True
