# Recognizes the encrypted script loader of the KK platform.
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
def read_container(data_bytes):
    if not data_bytes.startswith(MARK):
        raise ValueError('not a kkmap.jc (missing the marker %r)' % MARK)
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
        r = o.decompress(data_bytes[pos + 8:pos + 8 + cs]) + o.flush()
        if len(r) != us:
            raise ValueError('kkmap.jc: chunk %d gave %d B, expected %d' % (k, len(r), us))
        output += r
        pos += 8 + cs
    if pos != len(data_bytes):
        raise ValueError('kkmap.jc: the chunks end at %d, the file at %d' % (pos, len(data_bytes)))
    if len(output) < decomp_size:
        raise ValueError('kkmap.jc: decompressed %d B, the header says %d' % (len(output), decomp_size))
    return bytes(output[:decomp_size])


class Bytecode(object):
    def __init__(self, payload):
        rest, dw = struct.unpack_from('<II', payload, 0)
        if rest + 4 != len(payload) or dw % 2:
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


def load_data(file_path):
    with open(file_path, 'rb') as fh:
        d = fh.read()
    return Bytecode(read_container(d) if d.startswith(MARK) else d)
