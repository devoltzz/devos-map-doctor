# Reads the textures, materials and geosets of an MDX model.
import os
import struct


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))

def read_chunks(data, begin, end_pos):
    p = begin
    while p + 8 <= end_pos:
        tag = data[p:p + 4].decode('latin-1')
        n = struct.unpack_from('<I', data, p + 4)[0]
        yield tag, p + 8, n
        p += 8 + n


def cstr(b):
    i = b.find(b'\x00')
    return (b if i < 0 else b[:i]).decode('latin-1')


def read_textures(data, off, n):
    output = []
    for i in range(n // 268):
        p = off + i * 268
        rid = struct.unpack_from('<I', data, p)[0]
        file_path = cstr(data[p + 4:p + 264])
        flags = struct.unpack_from('<I', data, p + 264)[0]
        output.append({'i': i, 'repl': rid, 'path': file_path, 'flags': flags})
    return output


def read_materials(data, off, n, version_num):
    mats = []
    p = off
    end_pos = off + n
    while p + 4 <= end_pos:
        inc = struct.unpack_from('<I', data, p)[0]
        if inc <= 0:
            break
        q = p + 4
        prio = struct.unpack_from('<i', data, q)[0]
        flags = struct.unpack_from('<I', data, q + 4)[0]
        q += 8
        if version_num >= 900:
            q += 80
        if data[q:q + 4] != b'LAYS':
            mats.append({'prio': prio, 'flags': flags, 'lays': [], 'err': 'no LAYS'})
            p += inc
            continue
        nlay = struct.unpack_from('<I', data, q + 4)[0]
        q += 8
        layers = []
        for _ in range(nlay):
            linc = struct.unpack_from('<I', data, q)[0]
            filtro, shade, texid, texanim, coord = struct.unpack_from('<5I', data, q + 4)
            alfa = struct.unpack_from('<f', data, q + 24)[0]
            layers.append({'filtro': filtro, 'shade': shade, 'tex': texid,
                           'texanim': texanim, 'coord': coord, 'alfa': alfa})
            q += linc
        mats.append({'prio': prio, 'flags': flags, 'lays': layers, 'err': ''})
        p += inc
    return mats


def read_geoset_materials(data, off, n):
    output = []
    p = off
    end_pos = off + n
    while p + 4 <= end_pos:
        inc = struct.unpack_from('<I', data, p)[0]
        if inc <= 0:
            break
        q = p + 4
        nv = 0
        if data[q:q + 4] == b'VRTX':
            nv = struct.unpack_from('<I', data, q + 4)[0]
            q += 8 + nv * 12
            if data[q:q + 4] == b'NRMS':
                nn = struct.unpack_from('<I', data, q + 4)[0]
                q += 8 + nn * 12
            if data[q:q + 4] == b'PTYP':
                c = struct.unpack_from('<I', data, q + 4)[0]
                q += 8 + c * 4
            if data[q:q + 4] == b'PCNT':
                c = struct.unpack_from('<I', data, q + 4)[0]
                q += 8 + c * 4
            if data[q:q + 4] == b'PVTX':
                c = struct.unpack_from('<I', data, q + 4)[0]
                q += 8 + c * 2
            if data[q:q + 4] == b'GNDX':
                c = struct.unpack_from('<I', data, q + 4)[0]
                q += 8 + c
            if data[q:q + 4] == b'MTGC':
                c = struct.unpack_from('<I', data, q + 4)[0]
                q += 8 + c * 4
            if data[q:q + 4] == b'MATS':
                c = struct.unpack_from('<I', data, q + 4)[0]
                q += 8 + c * 4
            mid = struct.unpack_from('<I', data, q)[0]
            output.append((mid, nv))
        p += inc
    return output


def exists(present, p):
    if not p:
        return False
    q = p.lower().replace('/', '\\').lstrip('\\')
    if q in present:
        return True
    base = os.path.splitext(q)[0]
    return any(base + e in present for e in ('.blp', '.tga', '.dds', '.mdx', '.mdl'))
