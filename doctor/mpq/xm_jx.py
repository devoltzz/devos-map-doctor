# The tokenized script war3map.jx of xmload maps turned back into JASS text.
import struct
import zlib


KEYWORDS = (
    'boolean',
    'code',
    'handle',
    'integer',
    'null',
    'real',
    'string',
    'and',
    'array',
    'call',
    'constant',
    'debug',
    'else',
    'elseif',
    'endfunction',
    'endglobals',
    'endif',
    'endloop',
    'exitwhen',
    'extends',
    'false',
    'function',
    'globals',
    'if',
    'local',
    'loop',
    'native',
    'not',
    'nothing',
    'or',
    'return',
    'returns',
    'set',
    'takes',
    'then',
    'true',
    'type',
    '==',
    '!=',
    '<=',
    '>=',
)
CHARS = frozenset(b'=()+-*/<>[],')
AMBIGUOUS = frozenset((0x28, 0x29, 0x2A, 0x2B, 0x2D, 0x2E, 0x2F))
NAME, STRING, INT, OCTAL, HEX, DOLLAR, REAL, RAWCODE = 0x29, 0x30, 0x2A, 0x2B, 0x2C, 0x2D, 0x2E, 0x2F


class JxError(Exception):
    pass


def real_text(bits):
    v = struct.unpack('<f', struct.pack('<I', bits))[0]
    for d in range(1, 12):
        s = '%.*f' % (d, v)
        if struct.pack('<f', float(s)) == struct.pack('<I', bits):
            return s
    return '%.9f' % v


def rawcode_text(v):
    b = struct.pack('>I', v).lstrip(b'\0') or b'\0'
    t = b.decode('latin-1').replace('\\', '\\\\').replace("'", "\\'")
    return "'%s'" % t


def parse(data):
    if data[:4] != b'JB2+':
        raise JxError('not JB2+: %r' % data[:4])
    size = struct.unpack_from('<I', data, 4)[0]
    try:
        table = zlib.decompress(data[8:8 + size])
    except zlib.error as e:
        raise JxError('the names do not inflate: %s' % e)
    count = struct.unpack_from('<I', table, 0)[0]
    names = table[4:].split(b'\0')[:count]
    if len(names) != count:
        raise JxError('names: %d of %d' % (len(names), count))
    r = data[8 + size:]
    p, n, out = 0, len(r), []

    def boolean_after_comma(q):
        return q + 5 <= n and r[q + 2] == 0 and r[q + 3] == NAME and r[q + 4] in (0, 0x10)

    def word_at(q):
        return q + 6 <= n and struct.unpack_from('<I', r, q + 2)[0] < count

    while p < n:
        b = r[p]
        low = r[p + 1] if p + 1 < n else 0
        if b == NAME and low in (0, 0x10) and word_at(p):
            pass
        elif b == HEX and low == 0 and not boolean_after_comma(p):
            pass
        elif b in CHARS and (b not in AMBIGUOUS or low != 0 or b == NAME):
            out.append(('word', chr(b)))
            p += 1
            continue
        if p + 2 > n:
            raise JxError('the stream ends inside a token at %d' % p)
        t = struct.unpack_from('<H', r, p)[0]
        p += 2
        if t == 0xFFFF:
            break
        if t == 0x8000:
            p += 4
            if p > n:
                raise JxError('the stream ends inside a comment')
            continue
        k = t & 0xFF
        if t >> 8 not in (0, 0x10):
            raise JxError('token %#x at %d' % (t, p - 2))
        if k == 0x33:
            out.append(('nl', ''))
        elif k == 0x34:
            out.append(('file', ''))
        elif k in (0x32, 0x35):
            pass
        elif k < len(KEYWORDS):
            out.append(('word', KEYWORDS[k]))
        elif k in (NAME, STRING, INT, OCTAL, HEX, DOLLAR, REAL, RAWCODE):
            if p + 4 > n:
                raise JxError('the stream ends inside a literal at %d' % p)
            v = struct.unpack_from('<I', r, p)[0]
            p += 4
            if k in (NAME, STRING):
                if v >= count:
                    raise JxError('index %d of %d at %d' % (v, count, p - 4))
                t2 = names[v].decode('utf-8', 'surrogateescape')
                out.append(('name', t2) if k == NAME else ('string', '"%s"' % t2))
            elif k == REAL:
                out.append(('number', real_text(v)))
            elif k == RAWCODE:
                out.append(('number', rawcode_text(v)))
            elif k == HEX:
                out.append(('number', '0x%X' % v))
            elif k == DOLLAR:
                out.append(('number', '$%X' % v))
            elif k == OCTAL:
                out.append(('number', ('0%o' % v) if v else '0'))
            else:
                out.append(('number', str(v - (1 << 32) if v >> 31 else v)))
        else:
            raise JxError('unknown token %#x at %d' % (t, p - 2))
    return names, out


def to_text(tokens):
    lines, line = [], []
    for kind, value in tokens:
        if kind == 'file':
            continue
        if kind == 'nl':
            if line:
                lines.append(' '.join(line))
                line = []
        else:
            line.append(value)
    if line:
        lines.append(' '.join(line))
    return ('\n'.join(lines) + '\n').encode('utf-8', 'surrogateescape')


def decode(data):
    return to_text(parse(data)[1])


def map_script(data, shell):
    _names, tokens = parse(data)
    marks = [i for i, (kind, _v) in enumerate(tokens) if kind == 'file']
    if len(marks) < 2:
        raise JxError('the stream has %d file boundaries' % len(marks))
    text = to_text(tokens[marks[-2] + 1:marks[-1]])
    shell = shell.replace(b'\r\n', b'\n')
    start, conf = shell.find(b'function InitCustomPlayerSlots'), shell.find(b'function config takes')
    main = shell.find(b'function main takes')
    if start < 0 or conf < 0 or main < start:
        raise JxError('the shell war3map.j has not the setup functions')
    empty = b'function config takes nothing returns nothing\nendfunction\n'
    if text.count(empty) != 1:
        raise JxError('the tokenized config is not the empty one')
    text = text.replace(empty, shell[conf:].rstrip() + b'\n')
    head = b'function main takes nothing returns nothing\n'
    if text.count(head) != 1:
        raise JxError('no main in the stream')
    return text.replace(head, shell[start:main] + head)

