# Reads the bytecode of a map script compiled by KKWE, and recognizes the loader of an encrypted map.
import array
import struct
import sys
import zlib


MARK = b'KKWE PLUG-IN ENCRYPT JASS!'

OPS = {1: 'ENDPROGRAM', 2: 'OLDJUMP', 3: 'FUNCTION', 4: 'ENDFUNCTION', 5: 'LOCAL', 6: 'GLOBAL', 7: 'CONSTANT',
       8: 'FUNCARG', 9: 'EXTENDS', 10: 'TYPE', 11: 'POPN', 12: 'MOVRLITERAL', 13: 'MOVRR', 14: 'MOVRV',
       15: 'MOVRCODE', 16: 'MOVRA', 17: 'MOVVR', 18: 'MOVAR', 19: 'PUSH', 20: 'POP', 21: 'CALLNATIVE',
       22: 'CALLJASS', 23: 'I2R', 24: 'AND', 25: 'OR', 26: 'EQUAL', 27: 'NOTEQUAL', 28: 'LESSEREQUAL',
       29: 'GREATEREQUAL', 30: 'LESSER', 31: 'GREATER', 32: 'ADD', 33: 'SUB', 34: 'MUL', 35: 'DIV', 36: 'MOD',
       37: 'NEGATE', 38: 'NOT', 39: 'RETURN', 40: 'LABEL', 41: 'JUMPIFTRUE', 42: 'JUMPIFFALSE', 43: 'JUMP'}
OP = {v: k for k, v in OPS.items()}

TYPES = {0: 'nothing', 2: 'null', 3: 'code', 4: 'integer', 5: 'real', 6: 'string', 7: 'handle', 8: 'boolean',
         9: 'integer array', 10: 'real array', 11: 'string array', 12: 'handle array', 13: 'boolean array'}
TYPE_CODE = {'nothing': 0, 'null': 2, 'code': 3, 'integer': 4, 'real': 5, 'string': 6, 'handle': 7, 'boolean': 8}
WITH_NAME = {3, 5, 6, 7, 8, 9, 10, 14, 15, 16, 17, 18, 21, 22}


def read_container(data_bytes):
    if not data_bytes.startswith(MARK):
        raise ValueError('not a kkmap.jc (missing the marker %r)' % MARK)
    if len(data_bytes) < 48:
        raise ValueError('kkmap.jc: truncated header (%d B; the fields read go up to byte 48)' % len(data_bytes))
    if struct.unpack_from('<H', data_bytes, 26)[0] != len(MARK):
        raise ValueError('kkmap.jc: the marker size does not match')
    header, total, _one, decomp_size, nchunks = struct.unpack_from('<IIIII', data_bytes, 28)
    if total != len(data_bytes):
        raise ValueError('kkmap.jc: the header says %d B, the file has %d' % (total, len(data_bytes)))
    pos = header
    output = bytearray()
    for k in range(nchunks):
        if pos + 8 > len(data_bytes):
            raise ValueError('kkmap.jc: chunk %d runs past the end' % k)
        cs, us, _check = struct.unpack_from('<HHI', data_bytes, pos)
        o = zlib.decompressobj()
        try:
            r = o.decompress(data_bytes[pos + 8:pos + 8 + cs]) + o.flush()
        except zlib.error as e:
            raise ValueError('kkmap.jc: chunk %d does not decompress (%s)' % (k, e))
        if len(r) != us:
            raise ValueError('kkmap.jc: chunk %d gave %d B, expected %d' % (k, len(r), us))
        output += r
        pos += 8 + cs
    if pos != len(data_bytes):
        raise ValueError('kkmap.jc: the chunks end at %d, the file at %d' % (pos, len(data_bytes)))
    if len(output) < decomp_size:
        raise ValueError('kkmap.jc: decompressed %d B, the header says %d' % (len(output), decomp_size))
    return bytes(output[:decomp_size])


SOURCE_ORDER, REVERSE_ORDER, JC1_ORDER = 'source', 'reverse', 'jc1'
JC1_KEY = 0x58


class Bytecode(object):
    def __init__(self, payload, order=SOURCE_ORDER):
        self.order = order
        if len(payload) < 8:
            raise ValueError('bytecode: %d B are not enough for the header' % len(payload))
        rest, dw = struct.unpack_from('<II', payload, 0)
        if rest + 4 != len(payload) or dw % 2 or 8 + dw * 4 + 4 > len(payload):
            raise ValueError('bytecode: header %d/%d does not add up to %d B' % (rest, dw, len(payload)))
        self.n = dw // 2
        code_part = payload[8:8 + dw * 4]
        self.b0 = code_part[0::8]
        self.b1 = code_part[1::8]
        self.b2 = code_part[2::8]
        self.op = code_part[3::8]
        words = array.array('i')
        words.frombytes(code_part)
        if sys.byteorder != 'little':
            words.byteswap()
        self.arg = words[1::2]
        p = 8 + dw * 4
        nn = struct.unpack_from('<I', payload, p)[0]
        pieces = payload[p + 4:].split(b'\x00')
        if pieces and pieces[-1] == b'':
            pieces = pieces[:-1]
        if len(pieces) + 1 != nn and len(pieces) != nn:
            raise ValueError('bytecode: the table says %d names, found %d' % (nn, len(pieces)))
        self.name_list = [x.decode('utf-8', 'surrogateescape') for x in pieces]

    def fname(self, k):
        return self.name_list[k - 1] if 1 <= k <= len(self.name_list) else '#%d' % k

    def instruction(self, k):
        return self.b0[k], self.b1[k], self.b2[k], self.op[k], self.arg[k]

    def functions(self):
        f3 = OP['FUNCTION']
        return [(k, self.fname(self.arg[k])) for k in range(self.n) if self.op[k] == f3]

    def real(self, k):
        return struct.unpack('<f', struct.pack('<i', self.arg[k]))[0]

    def render(self, k):
        b0, b1, b2, op, arg = self.instruction(k)
        o = OPS.get(op, '?%02x' % op)
        t = TYPES.get
        if op == 12:
            if b1 == 6:
                v = repr(self.fname(arg))
            elif b1 == 5:
                v = repr(self.real(k))
            else:
                v = str(arg)
            return '%-12s r%02x <- %s %s' % (o, b2, t(b1, b1), v)
        if op in (5, 6, 7):
            return '%-12s %s %s' % (o, t(b2, b2), self.fname(arg))
        if op == 8:
            return '%-12s #%d %s %s' % (o, b1, t(b2, b2), self.fname(arg))
        if op == 3:
            return '%-12s %s returns %s' % (o, self.fname(arg), t(b2, b2))
        if op in (9, 10):
            return '%-12s %s' % (o, self.fname(arg))
        if op == 14:
            return '%-12s r%02x <- %s (%s)' % (o, b2, self.fname(arg), t(b1, b1))
        if op == 16:
            return '%-12s r%02x <- %s[r%02x] (%s)' % (o, b2, self.fname(arg), b1, t(b0, b0))
        if op == 15:
            return '%-12s r%02x <- function %s' % (o, b2, self.fname(arg))
        if op == 17:
            return '%-12s %s <- r%02x' % (o, self.fname(arg), b2)
        if op == 18:
            return '%-12s %s[r%02x] <- r%02x' % (o, self.fname(arg), b2, b1)
        if op in (19, 20, 23, 37, 38):
            return '%-12s r%02x' % (o, b2)
        if op in (21, 22):
            return '%-12s %s' % (o, self.fname(arg))
        if op == 11:
            return '%-12s %d' % (o, b2)
        if 24 <= op <= 36:
            return '%-12s r%02x <- r%02x , r%02x' % (o, b2, b1, b0)
        if op in (40, 41, 42, 43):
            return '%-12s L%d%s' % (o, arg, (' (r%02x)' % b2) if op in (41, 42) else '')
        if op == 13:
            return '%-12s r%02x <- r%02x' % (o, b2, b1)
        return '%-12s %d  (%02x %02x %02x)' % (o, arg, b0, b1, b2)


def is_loader(bc):
    bodies = {}
    fs = bc.functions()
    for j, (k, fname) in enumerate(fs):
        end_pos = fs[j + 1][0] if j + 1 < len(fs) else bc.n
        bodies[fname] = range(k + 1, end_pos)
    if 'main' not in bodies and 'config' in bodies and any(
            bc.op[k] == OP['CALLNATIVE'] and bc.fname(bc.arg[k]) == 'DzSetMemory' for k in range(bc.n)):
        return True, None
    if 'main' not in bodies or 'config' not in bodies:
        return False, None
    main_calls = [k for k in bodies['main'] if bc.op[k] in (OP['CALLNATIVE'], OP['CALLJASS'])]
    literal = None
    last = None
    for k in bodies['config']:
        if bc.op[k] == OP['MOVRLITERAL'] and bc.b1[k] == TYPE_CODE['string']:
            last = bc.fname(bc.arg[k])
        elif bc.op[k] == OP['CALLNATIVE'] and bc.fname(bc.arg[k]) == 'Preloader':
            literal = last
    return not main_calls and literal is not None, literal


def is_jc(payload):
    if len(payload) < 12:
        return False
    rest, dw = struct.unpack_from('<II', payload, 0)
    return rest + 4 == len(payload) and dw % 2 == 0 and 8 + dw * 4 + 4 <= len(payload)


def decipher_jc1(payload, hash_key=JC1_KEY):
    c = payload[4:]
    if not c:
        return bytes(payload)
    prev_item = bytes([hash_key]) + c[:-1]
    p = bytearray((int.from_bytes(c, 'little') ^ int.from_bytes(prev_item, 'little')).to_bytes(len(c), 'little'))
    i = c.find(b'\x00')
    while i != -1:
        j = i
        while j < len(c) and c[j] == 0:
            j += 1
        if i == 0:
            k = hash_key
            for m in range(0, min(j + 1, len(c))):
                p[m] = c[m] ^ k
        else:
            k = c[i - 1]
            for m in range(i + 1, min(j + 1, len(c))):
                p[m] = c[m] ^ k
        i = c.find(b'\x00', j)
    return payload[:4] + bytes(p)


def jc1_to_jc(plaintext):
    if len(plaintext) < 8:
        raise ValueError('kkmap.jc1: %d B are not enough for the header' % len(plaintext))
    rest, n = struct.unpack_from('<II', plaintext, 0)
    if rest + 4 != len(plaintext):
        raise ValueError('kkmap.jc1: the header says %d B, the plain data has %d' % (rest + 4, len(plaintext)))
    name_list = [None] * n
    p = 8
    for _ in range(n):
        if p + 4 > len(plaintext):
            raise ValueError('kkmap.jc1: the name table runs past the end')
        i = struct.unpack_from('<I', plaintext, p)[0]
        f = plaintext.find(b'\x00', p + 4)
        if f < 0 or not 1 <= i <= n or name_list[i - 1] is not None:
            raise ValueError('kkmap.jc1: the name entry at %d does not end (id %d of %d)' % (p, i, n))
        name_list[i - 1] = plaintext[p + 4:f]
        p = f + 1
    code_part = plaintext[p:]
    if len(code_part) % 8:
        raise ValueError('kkmap.jc1: the code has %d B, not a multiple of 8' % len(code_part))
    body = (
        struct.pack('<I', len(code_part) // 4)
        + code_part
        + struct.pack('<I', n)
        + b''.join(x + b'\x00' for x in name_list)
    )
    return struct.pack('<I', len(body)) + body


def bytecode(data_bytes):
    d = read_container(data_bytes) if data_bytes.startswith(MARK) else data_bytes
    if is_jc(d):
        try:
            return Bytecode(d)
        except ValueError:
            pass
    try:
        conv = jc1_to_jc(decipher_jc1(d))
    except ValueError as e:
        raise ValueError('neither kkmap.jc nor kkmap.jc1 (%s)' % e)
    return Bytecode(conv, JC1_ORDER)


def load_data(file_path):
    with open(file_path, 'rb') as fh:
        return bytecode(fh.read())


FILES = ('kkmap.jc', 'kkmap.jc1')


def file_in_map(a):
    for n in FILES:
        if a.find(n):
            return n
    return None
