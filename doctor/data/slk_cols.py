# Reads the cells of an SLK table and removes columns from it.
import io
import os
import re
import struct
import sys



def read_data(p):
    return lines_of(io.open(p, 'rb').read())


def lines_of(data_bytes):
    txt = data_bytes.decode('utf-8', 'surrogateescape')
    txt = txt.replace('\r\r\n', '\r\n')
    return txt.replace('\r\n', '\n').split('\n'), ('\r\n' in txt)


def join_lines(line_list, crlf):
    return (('\r\n' if crlf else '\n').join(line_list)).encode('utf-8', 'surrogateescape')


def slk_fields(ln):
    out = []
    buf = None
    for p in ln.split(';')[1:]:
        if buf is not None:
            buf += ';' + p
            if buf.count('"') % 2 == 0:
                out.append(buf)
                buf = None
        elif p.startswith('K"') and p.count('"') % 2 == 1:
            buf = p
        else:
            out.append(p)
    if buf is not None:
        out.append(buf)
    return out


_NAT = [None]
_NONE = -(1 << 63)


def _native_sound():
    if os.environ.get('JASS_NATIVE') == '0' or sys.platform == 'emscripten':
        return None
    if _NAT[0] is None:
        _NAT[0] = False
        try:
            import ctypes
            from doctor.script import jass_native
            dll = jass_native._dll()
            if dll and hasattr(dll, 'slk_pass'):
                f = dll.slk_pass
                f.argtypes = [ctypes.c_uint32, ctypes.c_char_p, ctypes.c_size_t, ctypes.c_char_p, ctypes.c_size_t,
                              ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_size_t)]
                f.restype = ctypes.c_int
                _NAT[0] = (f, dll.jass_free)
        except Exception:
            _NAT[0] = False
    return _NAT[0] or None


def _text(line_list):
    if not _native_sound():
        return None
    try:
        t = '\n'.join(line_list)
        if t.count('\n') != len(line_list) - 1:
            return None
        b = t.encode('utf-8', 'surrogateescape')
        if not b.isascii() and b.decode('utf-8', 'surrogateescape') != t:
            return None
    except (TypeError, UnicodeError):
        return None
    return b


class _Reader(object):
    __slots__ = ('b', 'p')

    def __init__(self, b):
        self.b, self.p = b, 0

    def int(self):
        v = struct.unpack_from('<q', self.b, self.p)[0]
        self.p += 8
        return None if v == _NONE else v

    def body_text(self):
        n = struct.unpack_from('<I', self.b, self.p)[0]
        self.p += 4 + n
        return self.b[self.p - n:self.p].decode('utf-8', 'surrogateescape')

    def line_list(self):
        n = self.int()
        t = self.body_text()
        return t.split('\n') if n else []


def _ints(*vs):
    return struct.pack('<%dq' % len(vs), *(_NONE if v is None else v for v in vs))


def _call(op, b, arg=b''):
    nat = _native_sound()
    if not nat or b is None:
        return None
    import ctypes
    f, free = nat
    p, n = ctypes.c_void_p(), ctypes.c_size_t()
    if f(op, b, len(b), arg, len(arg), ctypes.byref(p), ctypes.byref(n)) != 0:
        return None
    try:
        raw = ctypes.string_at(p.value, n.value) if n.value else b''
    finally:
        free(p, n.value)
    return _Reader(raw)


def _step(op, line_list, arg=b''):
    return _call(op, _text(line_list), arg)


RX_X = re.compile(r'X(\d+)')
RX_Y = re.compile(r'Y(\d+)')


def slk_cells(line_list):
    cur_x = cur_y = None
    for i, line in enumerate(line_list):
        if not line.startswith('C;'):
            continue
        x = y = k = None
        for c in (slk_fields(line) if '"' in line else line.split(';')[1:]):
            c0 = c[:1]
            if c0 == 'X' and c[1:2].isdigit():
                x = int(RX_X.match(c).group(1))
            elif c0 == 'Y' and c[1:2].isdigit():
                y = int(RX_Y.match(c).group(1))
            elif c0 == 'K':
                k = c[1:]
        if x is not None:
            cur_x = x
        if y is not None:
            cur_y = y
        yield i, cur_x, cur_y, k


def slk_columns(line_list):
    r = _step(4, line_list)
    if r is not None:
        out = {}
        for _ in range(r.int()):
            x = r.int()
            out[x] = r.body_text()
        return out, set(r.int() for _ in range(r.int()))
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
    if None not in new_x:
        pairs = []
        for x in new_x:
            pairs += [x, new_x[x]]
        r = _step(5, line_list, _ints(n, len(new_x), *pairs))
        if r is not None:
            return r.line_list(), n
    output = []
    cur_x = cur_y = None
    for line in line_list:
        if not line.startswith('C;'):
            output.append(line)
            continue
        fields = slk_fields(line) if '"' in line else line.split(';')[1:]
        x = y = None
        for c in fields:
            if c.startswith('X') and c[1:2].isdigit():
                x = int(RX_X.match(c).group(1))
            elif c.startswith('Y') and c[1:2].isdigit():
                y = int(RX_Y.match(c).group(1))
        if x is not None:
            cur_x = x
        if y is not None:
            cur_y = y
        if cur_x not in new_x:
            continue
        k = None
        for c in fields:
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
