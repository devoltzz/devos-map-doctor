# Adds collision shapes to MDX models that have none and fixes zeroed model extents.
import struct



def parse_chunks(data):
    if data[:4] != b'MDLX':
        raise ValueError("not MDX")
    p = 4
    chunks = []
    while p + 8 <= len(data):
        tag = data[p:p + 4]
        size = struct.unpack_from('<I', data, p + 4)[0]
        if p + 8 + size > len(data):
            raise ValueError("chunk %r overflows the file" % tag)
        chunks.append([tag, bytearray(data[p + 8:p + 8 + size])])
        p += 8 + size
    return chunks


def fix_geoa_alfa(data):
    chunks = parse_chunks(data)
    geoa = next((c[1] for c in chunks if c[0] == b'GEOA'), None)
    if geoa is None:
        return data, 0
    n = 0
    q = 0
    while q + 28 <= len(geoa):
        inc = struct.unpack_from('<I', geoa, q)[0]
        if inc < 28 or q + inc > len(geoa):
            break
        alfa = struct.unpack_from('<f', geoa, q + 4)[0]
        has_kgao = False
        r = q + 28
        while r + 16 <= q + inc:
            tag = bytes(geoa[r:r + 4])
            if tag not in (b'KGAO', b'KGAC'):
                break
            nk, interp = struct.unpack_from('<II', geoa, r + 4)
            width = 4 if tag == b'KGAO' else 12
            has_kgao = has_kgao or tag == b'KGAO'
            r += 16 + nk * (4 + width * (3 if interp > 1 else 1))
        if alfa < 0 and not has_kgao:
            struct.pack_into('<f', geoa, q + 4, 1.0)
            n += 1
        q += inc
    if not n:
        return data, 0
    return b'MDLX' + b''.join(c[0] + struct.pack('<I', len(c[1])) + bytes(c[1]) for c in chunks), n

