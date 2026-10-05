# Reads and reduces the nodes of an MDX model.
import struct


NODE_CHUNKS = (b'BONE', b'HELP', b'ATCH', b'CLID', b'EVTS', b'LITE', b'PREM', b'PRE2', b'RIBB')


def parse_chunks(data):
    p = 4
    chunks = []
    while p + 8 <= len(data):
        tag = data[p:p + 4]
        size = struct.unpack_from('<I', data, p + 4)[0]
        chunks.append([tag, bytearray(data[p + 8:p + 8 + size])])
        p += 8 + size
    return chunks


def iter_entries(tag, body):
    q = 0
    n = len(body)
    while q + 4 <= n:
        if tag == b'BONE':
            ns = struct.unpack_from('<I', body, q)[0]
            if ns < 96 or q + ns + 8 > n:
                break
            yield q, ns + 8, q
            q += ns + 8
        elif tag == b'HELP':
            ns = struct.unpack_from('<I', body, q)[0]
            if ns < 96 or q + ns > n:
                break
            yield q, ns, q
            q += ns
        elif tag == b'CLID':
            ns = struct.unpack_from('<I', body, q)[0]
            if ns < 96 or q + ns + 4 > n:
                break
            typ = struct.unpack_from('<I', body, q + ns)[0]
            extra = 4 + (12 if typ == 2 else 24) + (4 if typ in (2, 3) else 0)
            yield q, ns + extra, q
            q += ns + extra
        elif tag == b'EVTS':
            ns = struct.unpack_from('<I', body, q)[0]
            if ns < 96 or q + ns > n:
                break
            r = q + ns
            extra = 0
            if body[r:r + 4] == b'KEVT':
                cnt = struct.unpack_from('<I', body, r + 4)[0]
                extra = 12 + cnt * 4
            yield q, ns + extra, q
            q += ns + extra
        else:
            total = struct.unpack_from('<I', body, q)[0]
            if total < 100 or q + total > n:
                break
            yield q, total, q + 4
            q += total


def split_geosets(geos):
    out = []
    q = 0
    while q + 4 <= len(geos):
        gsize = struct.unpack_from('<I', geos, q)[0]
        if gsize < 4 or q + gsize > len(geos):
            break
        out.append(bytearray(geos[q + 4:q + gsize]))
        q += gsize
    return out


def geoset_parts(g):
    parts = {}
    r = 0
    while r + 8 <= len(g):
        t = bytes(g[r:r + 4])
        cnt = struct.unpack_from('<I', g, r + 4)[0]
        if t in (b'VRTX', b'NRMS'):
            sz = cnt * 12
        elif t in (b'PTYP', b'PCNT', b'MTGC', b'MATS'):
            sz = cnt * 4
        elif t == b'PVTX':
            sz = cnt * 2
        elif t == b'GNDX':
            sz = cnt
        else:
            break
        parts[t] = (r, cnt, r + 8, sz)
        r += 8 + sz
        if t == b'MATS':
            return parts, r
    raise ValueError("geoset without MATS")


def reduce_nodes(data, target=250):
    chunks = parse_chunks(data)
    info = {}
    nodes = {}
    for tag, body in chunks:
        if tag in NODE_CHUNKS:
            for off, tot, noff in iter_entries(tag, body):
                oid, pid, fl = struct.unpack_from('<III', body, noff + 84)
                nodes[oid] = (tag, pid, fl)
    total = len(nodes)
    info['nodes_before'] = total
    if total <= target:
        info['action_code'] = 'nada a fazer'
        return data, info
    if max(nodes) != total - 1:
        info['warning'] = 'objectIds not contiguous (max %d, total %d)' % (max(nodes), total)
    geos_i = next(i for i, c in enumerate(chunks) if c[0] == b'GEOS')
    gsets = split_geosets(chunks[geos_i][1])
    vcount = {}
    for g in gsets:
        parts, _ = geoset_parts(g)
        gndx = g[parts[b'GNDX'][2]:parts[b'GNDX'][2] + parts[b'GNDX'][3]]
        mtgc = struct.unpack_from('<%dI' % parts[b'MTGC'][1], g, parts[b'MTGC'][2])
        mats = struct.unpack_from('<%dI' % parts[b'MATS'][1], g, parts[b'MATS'][2])
        groups = []
        k = 0
        for c in mtgc:
            groups.append(mats[k:k + c])
            k += c
        for gi in gndx:
            for b in groups[gi]:
                vcount[b] = vcount.get(b, 0) + 1
    children = {}
    for oid, (tag, pid, fl) in nodes.items():
        children.setdefault(pid, []).append(oid)
    bones = [oid for oid, (tag, pid, fl) in nodes.items() if tag == b'BONE' and pid != 0xFFFFFFFF]
    need = total - target
    deleted = set()
    order = sorted(bones, key=lambda o: (vcount.get(o, 0), -o))
    for o in order:
        if len(deleted) >= need:
            break
        if all(ch in deleted for ch in children.get(o, [])):
            deleted.add(o)
    if len(deleted) < need:
        for o in order:
            if len(deleted) >= need:
                break
            deleted.add(o)
    if len(deleted) < need:
        info['err'] = 'not enough bones to remove'
        return data, info

    def ancestor(o):
        seen = 0
        while o in deleted and seen < 10000:
            o = nodes[o][1]
            seen += 1
        return o

    survivors = sorted(o for o in nodes if o not in deleted)
    newid = {o: i for i, o in enumerate(survivors)}

    def remap(o):
        if o == 0xFFFFFFFF:
            return o
        return newid[ancestor(o)]

    first_bone = next(o for o in survivors if nodes[o][0] == b'BONE')

    def remap_mats(o):
        a = o
        seen = 0
        while seen < 10000 and a != 0xFFFFFFFF and (a in deleted or nodes[a][0] != b'BONE'):
            a = nodes[a][1]
            seen += 1
        if a == 0xFFFFFFFF or a not in newid:
            a = first_bone
        return newid[a]

    info['deleted_slots'] = len(deleted)
    info['vertices_afetados'] = sum(vcount.get(o, 0) for o in deleted)
    for c in chunks:
        tag, body = c
        if tag not in NODE_CHUNKS:
            continue
        out = bytearray()
        for off, tot, noff in iter_entries(tag, body):
            oid, pid = struct.unpack_from('<II', body, noff + 84)
            if oid in deleted:
                continue
            entry = bytearray(body[off:off + tot])
            struct.pack_into('<II', entry, noff - off + 84, newid[oid], remap(pid))
            out += entry
        c[1] = out
    for c in chunks:
        if c[0] == b'PIVT':
            piv = c[1]
            newpiv = bytearray()
            for o in survivors:
                newpiv += piv[o * 12:o * 12 + 12] if o * 12 + 12 <= len(piv) else struct.pack('<3f', 0, 0, 0)
            c[1] = newpiv
    newgeos = bytearray()
    for g in gsets:
        parts, after = geoset_parts(g)
        mtgc = struct.unpack_from('<%dI' % parts[b'MTGC'][1], g, parts[b'MTGC'][2])
        mats = struct.unpack_from('<%dI' % parts[b'MATS'][1], g, parts[b'MATS'][2])
        groups = []
        k = 0
        for cnt in mtgc:
            grp = []
            for b in mats[k:k + cnt]:
                nb = remap_mats(b)
                if nb not in grp:
                    grp.append(nb)
            groups.append(grp)
            k += cnt
        flat = [b for grp in groups for b in grp]
        rebuilt = bytearray(g[:parts[b'MTGC'][0]])
        rebuilt += (
            b'MTGC' + struct.pack('<I', len(groups)) + struct.pack('<%dI' % len(groups), *[len(x) for x in groups])
        )
        rebuilt += b'MATS' + struct.pack('<I', len(flat)) + struct.pack('<%dI' % len(flat), *flat)
        rebuilt += g[after:]
        newgeos += struct.pack('<I', len(rebuilt) + 4) + rebuilt
    chunks[geos_i][1] = newgeos
    info['nodes_after'] = len(survivors)
    out = b'MDLX' + b''.join(c[0] + struct.pack('<I', len(c[1])) + bytes(c[1]) for c in chunks)
    return out, info
