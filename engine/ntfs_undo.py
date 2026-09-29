# Undoes the NTFS (LZNT1) compression left inside badly copied map files.
import struct


UNIT = 0x10000
CHUNK_SIZE = 0x1000
STRIDE = CHUNK_SIZE + 2


def lznt1_chunk(body, partial=False):
    out = bytearray()
    i, n = 0, len(body)
    while i < n:
        flags = body[i]
        i += 1
        for bit in range(8):
            if i >= n:
                break
            if not (flags >> bit) & 1:
                out.append(body[i])
                i += 1
                continue
            if i + 1 >= n:
                if partial:
                    return bytes(out)
                raise ValueError('truncated copy')
            tok = body[i] | (body[i + 1] << 8)
            i += 2
            p = len(out) - 1
            bitmask, shift = 0xFFF, 12
            while p >= 0x10:
                bitmask >>= 1
                shift -= 1
                p >>= 1
            sz = (tok & bitmask) + 3
            from_ = (tok >> shift) + 1
            if from_ > len(out):
                raise ValueError('copy before the start')
            begin = len(out) - from_
            for k in range(sz):
                out.append(out[begin + k])
        if len(out) > CHUNK_SIZE:
            raise ValueError('chunk larger than 4 KB')
    return bytes(out)


def lznt1_unit(d, pos, end_pos):
    out = bytearray()
    p = pos
    n = 0
    while len(out) < UNIT and p + 2 <= end_pos:
        header = d[p] | (d[p + 1] << 8)
        if header == 0:
            break
        if (header >> 12) & 7 != 3:
            return None
        body = (header & 0xFFF) + 1
        truncated = p + 2 + body > end_pos
        if truncated and end_pos < len(d):
            return None
        raw_bytes = d[p + 2:min(p + 2 + body, end_pos)]
        try:
            x = lznt1_chunk(raw_bytes, partial=truncated) if header & 0x8000 else bytes(raw_bytes)
        except ValueError:
            return None
        if n and len(out) % CHUNK_SIZE:
            return None
        out += x
        n += 1
        p += 2 + body
        if truncated:
            return bytes(out), True
    if n < 2 and not (n == 1 and len(out) < CHUNK_SIZE):
        return None
    return bytes(out), False


def plausible_tables(d, fname=None):
    import mpqlib as M
    h, _p = M.find_header(d, fname)
    if h is None:
        return None
    hn, bn = h.hash_n & 0x0FFFFFFF, h.block_n & 0x0FFFFFFF
    hp = (h.offset + h.hash_pos) & 0xFFFFFFFF
    if not hn or hn > 1 << 20 or hp + 16 * hn > len(d):
        return None
    t = M.decrypt_bytes(d[hp:hp + 16 * hn], M.hashstr('(hash table)', 3))
    block_list = struct.unpack('<%dI' % (4 * hn), t)[3::4]
    return sum(1 for b in block_list if b >= 0xFFFFFFFE or b < bn) / float(hn)


def detect(d):
    ff = None
    i = d.find(b'\xff\x3f')
    seen = 0
    while i >= 0 and seen < 1 << 16:
        if d[i + STRIDE:i + STRIDE + 2] == b'\xff\x3f' and d[i + 2 * STRIDE:i + 2 * STRIDE + 2] == b'\xff\x3f':
            ff = i
            break
        i = d.find(b'\xff\x3f', i + 1)
        seen += 1
    last_pos = (len(d) - 1) // UNIT * UNIT if d else 0
    last_unit = bool(d) and lznt1_unit(d, last_pos, len(d)) is not None
    if ff is None and not last_unit:
        return None
    return {'ff3f': ff, 'last_unit': last_unit}


def undo_accepted(before, after_diag, three_ff3f):
    best = after_diag is not None and after_diag >= 0.9 and (before is None or before < 0.9)
    jump = after_diag is not None and (before or 0) < 0.1 and after_diag - (before or 0) >= 0.25
    return best or jump or (three_ff3f and (after_diag or 0) >= (before or 0))


def undo(d, fname=None):
    details = {'units': 0, 'lznt1': 0, 'raw': 0, 'lost': 0, 'grown': 0}
    evidence = detect(d)
    if evidence is None:
        details['err'] = 'no sign found (FF 3F every 4,098 bytes, or the last unit in LZNT1)'
        return None, details
    out = bytearray()
    for pos in range(0, len(d), UNIT):
        end_pos = min(pos + UNIT, len(d))
        last_unit = end_pos == len(d)
        details['units'] += 1
        u = lznt1_unit(d, pos, end_pos)
        if u is None or (not last_unit and len(u[0]) != UNIT):
            out += d[pos:end_pos]
            details['raw'] += 1
            continue
        data_bytes, truncated = u
        details['lznt1'] += 1
        missing = (end_pos - pos) - len(data_bytes)
        if missing > 0 and truncated:
            out += data_bytes + b'\0' * missing
            details['lost'] += missing
        else:
            out += data_bytes
            details['grown'] += max(0, -missing)
            details['shrunk'] = details.get('shrunk', 0) + max(0, missing)
    details['bytes'] = len(out)
    if details['lznt1'] == 0:
        details['err'] = 'sign found, but no LZNT1 unit'
        return None, details
    before, after_diag = plausible_tables(d, fname), plausible_tables(bytes(out), fname)
    details['plausible'] = {'copy': before, 'undone': after_diag}
    if not undo_accepted(before, after_diag, evidence['ff3f'] is not None):
        details['err'] = 'the MPQ after the undo reads no better than the copy (hash table %s -> %s)' % (
            before,
            after_diag,
        )
        return None, details
    return bytes(out), details
