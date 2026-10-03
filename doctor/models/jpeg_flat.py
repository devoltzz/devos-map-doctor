# Tells whether a texture is plain white by its JPEG coefficients, without decoding the image.
import struct


SOF_OK = (0xC0, 0xC1, 0xC2)


class _Bits(object):
    __slots__ = ('d', 'p', 'acc', 'n')

    def __init__(self, d, p):
        self.d, self.p, self.acc, self.n = d, p, 0, 0

    def bits(self, k):
        while self.n < k:
            b = self.d[self.p]
            if b == 0xFF:
                if self.d[self.p + 1] != 0x00:
                    raise ValueError('marker inside the entropy data')
                self.p += 2
            else:
                self.p += 1
            self.acc = ((self.acc << 8) | b) & 0xFFFFFFFFFFFF
            self.n += 8
        self.n -= k
        return (self.acc >> self.n) & ((1 << k) - 1)

    def align(self):
        self.n = self.acc = 0


def _table(counts, symbols):
    code, k = 0, 0
    maxcode, valptr, mincode = [-1] * 18, [0] * 17, [0] * 17
    for n in range(1, 17):
        c = counts[n - 1]
        if c:
            valptr[n], mincode[n] = k, code
            code += c
            k += c
            maxcode[n] = code - 1
        code <<= 1
    return maxcode, valptr, mincode, symbols


def _decode(bits, t):
    maxcode, valptr, mincode, symbols = t
    code, n = bits.bits(1), 1
    while code > maxcode[n]:
        code = (code << 1) | bits.bits(1)
        n += 1
        if n > 16:
            raise ValueError('bad Huffman code')
    return symbols[valptr[n] + code - mincode[n]]


def _extend(v, s):
    return v - (1 << s) + 1 if s and v < (1 << (s - 1)) else v


def flat_dc(jpeg):
    d = bytes(jpeg)
    if d[:2] != b'\xff\xd8':
        return None
    quant, comps, tables = {}, {}, {}
    restart, width, height, dcs = 0, 0, 0, {}
    p = 2
    try:
        while p + 4 <= len(d):
            if d[p] != 0xFF:
                return None
            mk = d[p + 1]
            if mk == 0xFF or mk == 0x01 or 0xD0 <= mk <= 0xD8:
                p += 2 if mk != 0xFF else 1
                continue
            if mk == 0xD9:
                break
            size = struct.unpack_from('>H', d, p + 2)[0]
            seg, p = d[p + 4:p + 2 + size], p + 2 + size
            if mk == 0xDB:
                q = 0
                while q < len(seg):
                    wide, tq = seg[q] >> 4, seg[q] & 15
                    quant[tq] = struct.unpack_from('>H', seg, q + 1)[0] if wide else seg[q + 1]
                    q += 1 + 64 * (2 if wide else 1)
            elif 0xC0 <= mk <= 0xCF and mk not in (0xC4, 0xC8, 0xCC):
                if mk not in SOF_OK or seg[0] != 8:
                    return None
                height, width = struct.unpack_from('>HH', seg, 1)
                for i in range(seg[5]):
                    cid, hv, tq = seg[6 + 3 * i:9 + 3 * i]
                    if hv != 0x11:
                        return None
                    comps[cid] = (i, tq)
            elif mk == 0xC4:
                q = 0
                while q < len(seg):
                    counts = list(seg[q + 1:q + 17])
                    n = sum(counts)
                    tables[(seg[q] >> 4, seg[q] & 15)] = _table(counts, list(seg[q + 17:q + 17 + n]))
                    q += 17 + n
            elif mk == 0xDD:
                restart = struct.unpack_from('>H', seg, 0)[0]
            elif mk == 0xDA:
                if not comps or not width:
                    return None
                p = _scan(d, p, seg, comps, tables, restart, (width + 7) // 8 * ((height + 7) // 8), dcs)
                if p is None:
                    return None
        if not dcs or any(i not in quant for i in (t for _c, t in comps.values())):
            return None
        return dict((comps[c][0], min(v) * quant[comps[c][1]] / 8.0 + 128) for c, v in dcs.items())
    except (IndexError, KeyError, ValueError, struct.error):
        return None


def _scan(d, p, seg, comps, tables, restart, blocks, dcs):
    ns = seg[0]
    order = [(seg[1 + 2 * i], seg[2 + 2 * i] >> 4, seg[2 + 2 * i] & 15) for i in range(ns)]
    ss, se, ah, al = seg[1 + 2 * ns], seg[2 + 2 * ns], seg[3 + 2 * ns] >> 4, seg[3 + 2 * ns] & 15
    bits = _Bits(d, p)
    pred = dict((c, 0) for c, _t, _a in order)
    eobrun = 0
    for mcu in range(blocks):
        if restart and mcu and mcu % restart == 0:
            bits.align()
            if d[bits.p] != 0xFF or not 0xD0 <= d[bits.p + 1] <= 0xD7:
                raise ValueError('restart marker expected')
            bits.p += 2
            pred = dict((c, 0) for c, _t, _a in order)
            eobrun = 0
        for cid, td, ta in order:
            if ss == 0:
                values = dcs.setdefault(cid, [0] * blocks)
                if ah:
                    values[mcu] |= bits.bits(1) << al
                else:
                    s = _decode(bits, tables[(0, td)])
                    pred[cid] += _extend(bits.bits(s), s)
                    values[mcu] = pred[cid] << al
                if se == 0:
                    continue
            if eobrun:
                eobrun -= 1
                continue
            k = max(ss, 1)
            while k <= se:
                rs = _decode(bits, tables[(1, ta)])
                r, s = rs >> 4, rs & 15
                if s:
                    return None
                if r == 15:
                    k += 16
                    continue
                if ss:
                    eobrun = (1 << r) - 1 + (bits.bits(r) if r else 0)
                elif r:
                    return None
                break
    bits.align()
    q = bits.p
    while q + 1 < len(d) and not (d[q] == 0xFF and d[q + 1] not in (0x00,) and not 0xD0 <= d[q + 1] <= 0xD7):
        q += 1
    return q


def blp_is_white(data):
    b = bytes(data)
    try:
        if b[:4] != b'BLP1':
            return False
        kind, alpha, w, h = struct.unpack_from('<4I', b, 4)
        offsets = struct.unpack_from('<16I', b, 28)
        sizes = struct.unpack_from('<16I', b, 92)
        mips = [(o, s) for o, s in zip(offsets, sizes) if o and s]
        if not mips:
            return False
        if kind == 1:
            palette = [b[156 + 4 * i:160 + 4 * i][:3 if not alpha else 4] for i in range(256)]
            mw, mh = w, h
            for o, _s in mips:
                n = mw * mh
                used = set(b[o:o + n])
                mask = b[o + n:o + n + (n * alpha + 7) // 8]
                if len(b) < o + n or not used or any(palette[i].strip(b'\xff') for i in used):
                    return False
                if alpha and (len(mask) != (n * alpha + 7) // 8 or mask.strip(b'\xff')):
                    return False
                mw, mh = max(1, mw // 2), max(1, mh // 2)
            return True
        if kind != 0:
            return False
        head = b[160:160 + struct.unpack_from('<I', b, 156)[0]]
        for o, s in mips:
            flat = flat_dc(head + b[o:o + s])
            if flat is None or len(flat) < 3:
                return False
            if any(flat.get(i, 0) < 255 for i in range(4 if alpha else 3)):
                return False
        return True
    except (struct.error, IndexError):
        return False

