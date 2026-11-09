# The compact MDB3 models of xmload maps turned back into MDX.
import math
import struct


VERSION_KEY = 0x34968729
Q16 = 1.0 / 65535.0
FOURCC = {1: b'ATCH', 2: b'BONE', 3: b'CAMS', 4: b'CLID', 5: b'EVTS', 6: b'GEOA', 7: b'GEOS', 8: b'GLBS', 9: b'HELP',
          0x0A: b'LITE', 0x0B: b'MODL', 0x0C: b'MTLS', 0x0D: b'PIVT', 0x0E: b'PRE2', 0x0F: b'PREM', 0x10: b'RIBB',
          0x11: b'SEQS', 0x12: b'SNDS', 0x14: b'TEXS', 0x15: b'TXAN', 0x16: b'VERS'}
NODE_BITS = {b'BONE': 0x100, b'HELP': 0, b'EVTS': 0x400}


class Mdb3Error(Exception):
    pass


class Reader(object):
    __slots__ = ('b', 'p')

    def __init__(self, b, p=0):
        self.b, self.p = b, p

    def take(self, n):
        if self.p + n > len(self.b):
            raise Mdb3Error('the file ends at %d, %d B asked' % (self.p, n))
        v = self.b[self.p:self.p + n]
        self.p += n
        return v

    def u8(self):
        return self.take(1)[0]

    def u16(self):
        return struct.unpack('<H', self.take(2))[0]

    def u32(self):
        return struct.unpack('<I', self.take(4))[0]

    def name(self):
        return self.take(self.u8())


def _padded(text, n):
    if len(text) > n:
        raise Mdb3Error('name of %d B in a field of %d' % (len(text), n))
    return text + bytes(n - len(text))


def _unquant(l, low, span):
    return [struct.pack('<f', u * Q16 * r + m) for u, r, m in zip(struct.unpack('<%dH' % len(low), l), span, low)]


def track(r, fourcc, comps, quantized):
    n = r.u16()
    if n == 0:
        return b''
    interp = r.u8()
    gseq = r.take(4)
    tangents = interp > 1
    out = bytearray(fourcc + struct.pack('<II', n, interp) + gseq)
    if quantized and n >= 5:
        low = struct.unpack('<%df' % comps, r.take(4 * comps))
        span = struct.unpack('<%df' % comps, r.take(4 * comps))
        for _ in range(n):
            out += r.take(4)
            for _v in range(3 if tangents else 1):
                out += b''.join(_unquant(r.take(2 * comps), low, span))
    else:
        out += r.take(n * (4 + 4 * comps * (3 if tangents else 1)))
    return bytes(out)


NODE_TRACKS = {1: (b'KGTR', 3, True), 2: (b'KGRT', 4, True), 3: (b'KGSC', 3, True)}
TXAN_TRACKS = {1: (b'KTAT', 3, True), 2: (b'KTAR', 4, True), 3: (b'KTAS', 3, True)}
GEOA_TRACKS = {1: (b'KGAO', 1, False), 2: (b'KGAC', 3, False)}


def tracks_until(r, end, table, where):
    body = bytearray()
    while r.p < end:
        t = r.u8()
        if t not in table:
            raise Mdb3Error('%s: unknown track %d' % (where, t))
        body += track(r, *table[t])
    if r.p != end:
        raise Mdb3Error('%s: past its size' % where)
    return bytes(body)


def node(r, fourcc):
    start = r.p
    inclusive = r.u32()
    end = start + inclusive
    name = r.name()
    object_id, parent = r.take(4), r.take(4)
    flags = r.u8() | NODE_BITS.get(fourcc, 0)
    return (_padded(name, 80), object_id, parent, flags), end


def build_node(fields, tracks):
    name, object_id, parent, flags = fields
    return struct.pack('<I', 96 + len(tracks)) + name + object_id + parent + struct.pack('<I', flags) + tracks


def sec_modl(r, length):
    n, m = length & 0xFF, (length >> 16) & 0xFFFF
    name, anim = r.take(n), r.take(m)
    return _padded(name, 80) + _padded(anim, 260) + r.take(4 + 12 + 12 + 4)


def sec_seqs(r, length):
    out = bytearray()
    for _ in range(length):
        name = r.name()
        inicio_a_sync = r.take(24)
        raio = r.take(4)
        out += _padded(name, 80) + inicio_a_sync + raio + r.take(24)
    return bytes(out)


def sec_glbs(r, length):
    if length % 3:
        raise Mdb3Error('GLBS of %d B' % length)
    return b''.join(r.take(3) + b'\0' for _ in range(length // 3))


def sec_texs(r, length):
    out = bytearray()
    for _ in range(length & 0xFFFF):
        name = r.name()
        out += r.take(4) + _padded(name, 260) + r.take(4)
    return bytes(out)


def sec_snds(r, length):
    out = bytearray()
    for _ in range(length):
        name = r.name()
        out += _padded(name, 260) + r.take(12)
    return bytes(out)


def items_until(r, length, fn):
    end = r.p + length
    out = bytearray()
    while r.p < end:
        out += fn(r)
    if r.p != end:
        raise Mdb3Error('section past its size')
    return bytes(out)


def one_bone(r):
    fields, end = node(r, b'BONE')
    tracks = tracks_until(r, end, NODE_TRACKS, 'BONE')
    return build_node(fields, tracks) + r.take(8)


def one_help(r):
    fields, end = node(r, b'HELP')
    return build_node(fields, tracks_until(r, end, NODE_TRACKS, 'HELP'))


def sec_evts(r, length):
    sec_end = r.p + length
    out = bytearray()
    while r.p < sec_end:
        fields, end = node(r, b'EVTS')
        out += build_node(fields, tracks_until(r, end, NODE_TRACKS, 'EVTS'))
        if r.p < sec_end and r.b[r.p:r.p + 4] == b'KEVT':
            r.take(4)
            n = r.u32()
            out += b'KEVT' + struct.pack('<I', n) + r.take(4 + 4 * n)
    if r.p != sec_end:
        raise Mdb3Error('EVTS past its size')
    return bytes(out)


def one_geoa(r):
    start = r.p
    inclusive = r.u32()
    head = r.take(24)
    tracks = tracks_until(r, start + inclusive, GEOA_TRACKS, 'GEOA')
    return struct.pack('<I', 28 + len(tracks)) + head + tracks


def one_txan(r):
    start = r.p
    inclusive = r.u32()
    tracks = tracks_until(r, start + inclusive, TXAN_TRACKS, 'TXAN')
    return struct.pack('<I', 4 + len(tracks)) + tracks


def _id(r, esperado):
    i = r.u8()
    if i != esperado:
        raise Mdb3Error('GEOS: section %d instead of %d' % (i, esperado))


def _octahedron(u):
    y0 = (u & 0xFFFF) / 65535.0 * 2 - 1
    x0 = (u >> 16) / 65535.0 * 2 - 1
    ax, ay = abs(x0), abs(y0)
    z = 1 - ax - ay
    x, y = x0, y0
    if z < 0:
        x = (1 - ay) * (1.0 if x0 >= 0 else -1.0)
        y = (1 - ax) * (1.0 if y0 >= 0 else -1.0)
    d = math.sqrt(x * x + y * y + z * z) or 1.0
    return struct.pack('<3f', x / d, y / d, z / d)


def _list16(r, number, fourcc):
    _id(r, number)
    n = r.u16()
    return (
        fourcc + struct.pack('<I', n) + b''.join(struct.pack('<I', v) for v in struct.unpack('<%dH' % n, r.take(2 * n)))
    )


def one_geos(r):
    start = r.p
    inclusive = r.u32()
    end = start + inclusive
    out = bytearray()
    _id(r, 1)
    n = r.u16()
    low = struct.unpack('<3f', r.take(12))
    span = struct.unpack('<3f', r.take(12))
    out += b'VRTX' + struct.pack('<I', n)
    for _ in range(n):
        out += b''.join(_unquant(r.take(6), low, span))
    _id(r, 2)
    n = r.u16()
    out += b'NRMS' + struct.pack('<I', n)
    out += b''.join(_octahedron(v) for v in struct.unpack('<%dI' % n, r.take(4 * n)))
    _id(r, 3)
    n = r.u16()
    out += b'PTYP' + struct.pack('<I', n) + struct.pack('<I', 4) * n
    _id(r, 4)
    n = r.u16()
    out += b'PCNT' + struct.pack('<I', n) + r.take(4 * n)
    _id(r, 5)
    n = r.u16()
    out += b'PVTX' + struct.pack('<I', n) + r.take(2 * n)
    _id(r, 6)
    n = r.u16()
    out += b'GNDX' + struct.pack('<I', n) + r.take(n)
    out += _list16(r, 7, b'MTGC')
    out += _list16(r, 8, b'MATS')
    out += r.take(4 + 4 + 4 + 4 + 12 + 12)
    extents = r.u32()
    out += struct.pack('<I', extents) + r.take(extents * 28)
    while r.p < end:
        t = r.u8()
        if t != 9:
            raise Mdb3Error('GEOS: last block %d' % t)
        sets = r.u16()
        out += b'UVAS' + struct.pack('<I', sets)
        for _ in range(sets):
            if r.u8() != 10:
                raise Mdb3Error('GEOS: UVBS expected')
            n = r.u16()
            out += b'UVBS' + struct.pack('<I', n)
            for u, v in zip(*[iter(struct.unpack('<%dH' % (2 * n), r.take(4 * n)))] * 2):
                out += struct.pack('<2f', u * Q16 * 4.0 - 2.0, v * Q16 * 4.0 - 2.0)
    if r.p != end:
        raise Mdb3Error('GEOS past its size')
    return struct.pack('<I', 4 + len(out)) + bytes(out)


COMPACT = {b'MODL': sec_modl, b'SEQS': sec_seqs, b'GLBS': sec_glbs, b'TEXS': sec_texs, b'SNDS': sec_snds,
             b'EVTS': sec_evts}
PER_ITEM = {b'BONE': one_bone, b'HELP': one_help, b'GEOA': one_geoa, b'TXAN': one_txan, b'GEOS': one_geos}


def convert(b):
    if b[:4] != b'MDB3':
        raise Mdb3Error('not MDB3: %r' % b[:4])
    r = Reader(b, 4)
    out = bytearray(b'MDLX')
    while r.p < len(b):
        t = r.u8()
        if t == 0x16:
            version = r.u32() ^ VERSION_KEY
            out += b'VERS' + struct.pack('<II', 4, version)
            continue
        if t not in FOURCC:
            raise Mdb3Error('tag %#x at %d' % (t, r.p - 1))
        length = r.u32()
        cc = FOURCC[t]
        if cc in COMPACT:
            body = COMPACT[cc](r, length)
        elif cc in PER_ITEM:
            body = items_until(r, length, PER_ITEM[cc])
        else:
            body = r.take(length)
        out += cc + struct.pack('<I', len(body)) + body
    return bytes(out)

