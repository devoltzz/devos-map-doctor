# Copies of the models shown in interface frames, turned to face the screen.
import struct

from doctor.models import mdxcheck


CAMERA_SIZE = 120
TEXTURE_SIZE = 268


def _walk(data):
    chunks, err = mdxcheck.walk_path(data)
    if err:
        raise ValueError('the model chunks do not close: %s' % err)
    return chunks


def cameras(data):
    out = []
    for tag, size, off in _walk(data):
        if tag != b'CAMS':
            continue
        q, end = off, off + size
        while q + CAMERA_SIZE <= end:
            sz = struct.unpack_from('<I', data, q)[0] & 0xFFFFFF
            if sz < CAMERA_SIZE or q + sz > end:
                break
            name = data[q + 4:q + 84].split(b'\0', 1)[0].decode('latin-1')
            pos = struct.unpack_from('<3f', data, q + 84)
            fov, _far, _near = struct.unpack_from('<3f', data, q + 96)
            tgt = struct.unpack_from('<3f', data, q + 108)
            out.append((name, pos, tgt, fov))
            q += sz
    return out


def without_glow(data, transparent='devos\\transparente.tga',
                 team='ReplaceableTextures\\TeamColor\\TeamColor00.blp'):
    chunks = _walk(data)
    buf = bytearray(data)
    n = 0
    for tag, size, off in chunks:
        if tag != b'TEXS':
            continue
        for k in range(size // TEXTURE_SIZE):
            p = off + k * TEXTURE_SIZE
            rid = struct.unpack_from('<I', buf, p)[0]
            if rid not in (1, 2):
                continue
            path = (transparent if rid == 2 else team).encode('ascii')[:259].ljust(260, b'\0')
            struct.pack_into('<I', buf, p, 0)
            buf[p + 4:p + 264] = path
            n += 1
    new = bytes(buf)
    _walk(new)
    return new, n


NODE_AT_START = (b'BONE', b'HELP', b'EVTS', b'CLID')
NODE_AFTER_SIZE = (b'LITE', b'ATCH', b'PREM', b'PRE2', b'RIBB', b'CORN')
CLID_SIZE = {0: 24, 1: 24, 2: 16, 3: 28}


def _nodes(data, chunks):
    out = []
    for tag, size, off in chunks:
        if tag not in NODE_AT_START and tag not in NODE_AFTER_SIZE:
            continue
        q, end = off, off + size
        while q < end:
            if tag in NODE_AFTER_SIZE:
                total = struct.unpack_from('<I', data, q)[0]
                out.append((tag, q + 4))
                if total < 4 + 96:
                    raise ValueError('a %s entry of %d bytes' % (tag.decode(), total))
                q += total
                continue
            nsz = struct.unpack_from('<I', data, q)[0]
            if nsz < 96:
                raise ValueError('a %s node of %d bytes' % (tag.decode(), nsz))
            out.append((tag, q))
            q += nsz
            if tag == b'BONE':
                q += 8
            elif tag == b'EVTS' and data[q:q + 4] == b'KEVT':
                q += 12 + 4 * struct.unpack_from('<I', data, q + 4)[0]
            elif tag == b'CLID':
                kind = struct.unpack_from('<I', data, q)[0]
                if kind not in CLID_SIZE:
                    raise ValueError('a collision shape of type %d' % kind)
                q += 4 + CLID_SIZE[kind]
        if q != end:
            raise ValueError('the %s chunk does not close on its entries' % tag.decode())
    return out


def view_matrix(direction):
    dx, dy, dz = (float(v) for v in direction)
    n = (dx * dx + dy * dy + dz * dz) ** 0.5
    if n < 1e-9:
        raise ValueError('a camera with no direction')
    b = (dx / n, dy / n, dz / n)
    f = (-b[0], -b[1], -b[2])
    r = (f[1], -f[0], 0.0)
    nr = (r[0] * r[0] + r[1] * r[1]) ** 0.5
    if nr < 1e-6:
        raise ValueError('a camera looking straight down or up: the model already shows that way')
    r = (r[0] / nr, r[1] / nr, 0.0)
    u = (r[1] * f[2] - r[2] * f[1], r[2] * f[0] - r[0] * f[2], r[0] * f[1] - r[1] * f[0])
    return (r, u, b)


def _quaternion(m):
    (m00, m01, m02), (m10, m11, m12), (m20, m21, m22) = m
    tr = m00 + m11 + m22
    if tr > 0:
        s = (tr + 1.0) ** 0.5 * 2
        return ((m21 - m12) / s, (m02 - m20) / s, (m10 - m01) / s, 0.25 * s)
    if m00 > m11 and m00 > m22:
        s = (1.0 + m00 - m11 - m22) ** 0.5 * 2
        return (0.25 * s, (m01 + m10) / s, (m02 + m20) / s, (m21 - m12) / s)
    if m11 > m22:
        s = (1.0 + m11 - m00 - m22) ** 0.5 * 2
        return ((m01 + m10) / s, 0.25 * s, (m12 + m21) / s, (m02 - m20) / s)
    s = (1.0 + m22 - m00 - m11) ** 0.5 * 2
    return ((m02 + m20) / s, (m12 + m21) / s, 0.25 * s, (m10 - m01) / s)


def _extent(buf, p, m):
    mn = struct.unpack_from('<3f', buf, p + 4)
    mx = struct.unpack_from('<3f', buf, p + 16)
    if mn == mx:
        return
    corner_points = [(a, b, c) for a in (mn[0], mx[0]) for b in (mn[1], mx[1]) for c in (mn[2], mx[2])]
    rot = [tuple(sum(m[i][k] * c[k] for k in range(3)) for i in range(3)) for c in corner_points]
    struct.pack_into('<3f', buf, p + 4, *(min(c[i] for c in rot) for i in range(3)))
    struct.pack_into('<3f', buf, p + 16, *(max(c[i] for c in rot) for i in range(3)))


def facing_screen(data, direction=(1.0, 0.0, 0.0), name='DevoUIRoot'):
    chunks = _walk(data)
    tags = [c[0] for c in chunks]
    if b'BONE' not in tags or b'PIVT' not in tags:
        raise ValueError('a model with no bones or pivots')
    m = view_matrix(direction)
    q = _quaternion(m)
    nodes = _nodes(data, chunks)
    ids = sorted(struct.unpack_from('<i', data, o + 84)[0] for _t, o in nodes)
    if ids != list(range(len(nodes))):
        raise ValueError('object ids that are not 0..n-1')
    bone_nodes = [o for t, o in nodes if t == b'BONE']
    new_object_id = len(bone_nodes)
    if sorted(struct.unpack_from('<i', data, o + 84)[0] for o in bone_nodes) != list(range(new_object_id)):
        raise ValueError('bones that are not the first object ids')
    pivt = next(c for c in chunks if c[0] == b'PIVT')
    if pivt[1] != 12 * len(nodes):
        raise ValueError('%d pivots for %d nodes' % (pivt[1] // 12, len(nodes)))
    buf = bytearray(data)
    for _t, o in nodes:
        oid, parent = struct.unpack_from('<ii', buf, o + 84)
        if oid >= new_object_id:
            struct.pack_into('<i', buf, o + 84, oid + 1)
        if parent == -1:
            struct.pack_into('<i', buf, o + 88, new_object_id)
        elif parent >= new_object_id:
            struct.pack_into('<i', buf, o + 88, parent + 1)
    for tag, size, off in chunks:
        if tag == b'MODL' and size >= 368:
            _extent(buf, off + 340, m)
        elif tag == b'SEQS':
            for k in range(size // 132):
                _extent(buf, off + k * 132 + 104, m)
    glbs = next((c for c in chunks if c[0] == b'GLBS'), None)
    n_glbs = glbs[1] // 4 if glbs else 0
    anim_track = b'KGRT' + struct.pack('<IIi', 1, 0, n_glbs) + struct.pack('<I4f', 0, *q)
    node_body = name.encode('ascii')[:79].ljust(80, b'\0') + struct.pack('<iiI', new_object_id, -1, 0x100) + anim_track
    bone_node = struct.pack('<I', 4 + len(node_body)) + node_body + struct.pack('<ii', -1, -1)
    out = []
    for tag, size, off in chunks:
        body = bytes(buf[off:off + size])
        if tag == b'BONE':
            body += bone_node
        elif tag == b'PIVT':
            body = body[:12 * new_object_id] + struct.pack('<3f', 0, 0, 0) + body[12 * new_object_id:]
        elif tag == b'BPOS':
            n = struct.unpack_from('<I', body, 0)[0]
            ident = struct.pack('<12f', 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0)
            body = struct.pack('<I', n + 1) + body[4:4 + 48 * new_object_id] + ident + body[4 + 48 * new_object_id:]
        elif tag == b'GLBS':
            body += struct.pack('<I', 1000)
        out.append(tag + struct.pack('<I', len(body)) + body)
        if glbs is None and tag == (b'SEQS' if b'SEQS' in tags else b'MODL'):
            out.append(b'GLBS' + struct.pack('<II', 4, 1000))
    new = bytes(buf[:4]) + b''.join(out)
    _walk(new)
    if len(_nodes(new, _walk(new))) != len(nodes) + 1:
        raise ValueError('the turned copy does not have one node more')
    return new


def is_world_model(data, limit=2.0):
    try:
        chunks = _walk(data)
    except ValueError:
        return False
    for tag, size, off in chunks:
        if tag != b'GEOS':
            continue
        q, end = off, off + size
        while q + 12 <= end:
            sz = struct.unpack_from('<I', data, q)[0]
            if data[q + 4:q + 8] != b'VRTX' or sz < 12:
                return False
            nv = struct.unpack_from('<I', data, q + 8)[0]
            vs = struct.unpack_from('<%df' % (nv * 3), data, q + 12)
            if vs and max(abs(v) for v in vs) > limit:
                return True
            q += sz
    return False
