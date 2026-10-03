# Finds and fixes the geosets with too many matrix groups, which hang the game.
import math
import struct

from doctor.models import mdxnodes as mn


LIMIT = 255


def geoset_full(g):
    parts, after = mn.geoset_parts(g)
    d = {}
    nv = parts[b'VRTX'][1]
    d['vrtx'] = struct.unpack_from('<%df' % (nv * 3), g, parts[b'VRTX'][2])
    d['nrms'] = struct.unpack_from('<%df' % (parts[b'NRMS'][1] * 3), g, parts[b'NRMS'][2]) if b'NRMS' in parts else None
    d['ptyp'] = struct.unpack_from('<%dI' % parts[b'PTYP'][1], g, parts[b'PTYP'][2])
    d['pcnt'] = struct.unpack_from('<%dI' % parts[b'PCNT'][1], g, parts[b'PCNT'][2])
    d['pvtx'] = struct.unpack_from('<%dH' % parts[b'PVTX'][1], g, parts[b'PVTX'][2])
    d['gndx'] = list(g[parts[b'GNDX'][2]:parts[b'GNDX'][2] + parts[b'GNDX'][3]])
    mtgc = struct.unpack_from('<%dI' % parts[b'MTGC'][1], g, parts[b'MTGC'][2])
    mats = struct.unpack_from('<%dI' % parts[b'MATS'][1], g, parts[b'MATS'][2])
    groups = []
    k = 0
    for c in mtgc:
        groups.append(tuple(mats[k:k + c]))
        k += c
    d['groups'] = groups
    d['matid'], d['selgroup'], d['selflags'] = struct.unpack_from('<III', g, after)
    d['ext'] = struct.unpack_from('<7f', g, after + 12)
    next_ = struct.unpack_from('<I', g, after + 40)[0]
    d['seqext'] = g[after + 44:after + 44 + next_ * 28]
    p2 = after + 44 + next_ * 28
    if g[p2:p2 + 4] != b'UVAS':
        raise ValueError('geoset without UVAS')
    nuv = struct.unpack_from('<I', g, p2 + 4)[0]
    p3 = p2 + 8
    uvs = []
    for k in range(nuv):
        if g[p3:p3 + 4] != b'UVBS':
            raise ValueError('UVBS ausente')
        c2 = struct.unpack_from('<I', g, p3 + 4)[0]
        uvs.append(struct.unpack_from('<%df' % (c2 * 2), g, p3 + 8))
        p3 += 8 + c2 * 8
    d['uvs'] = uvs
    d['tail'] = g[p3:]
    return d


def build_geoset(d):
    nv = len(d['vrtx']) // 3
    out = bytearray()
    out += b'VRTX' + struct.pack('<I', nv) + struct.pack('<%df' % (nv * 3), *d['vrtx'])
    if d['nrms'] is not None:
        out += b'NRMS' + struct.pack('<I', nv) + struct.pack('<%df' % (nv * 3), *d['nrms'])
    out += b'PTYP' + struct.pack('<I', len(d['ptyp'])) + struct.pack('<%dI' % len(d['ptyp']), *d['ptyp'])
    out += b'PCNT' + struct.pack('<I', len(d['pcnt'])) + struct.pack('<%dI' % len(d['pcnt']), *d['pcnt'])
    out += b'PVTX' + struct.pack('<I', len(d['pvtx'])) + struct.pack('<%dH' % len(d['pvtx']), *d['pvtx'])
    out += b'GNDX' + struct.pack('<I', len(d['gndx'])) + bytes(d['gndx'])
    out += (
        b'MTGC'
        + struct.pack('<I', len(d['groups']))
        + struct.pack('<%dI' % len(d['groups']), *[len(x) for x in d['groups']])
    )
    flat = [b for grp in d['groups'] for b in grp]
    out += b'MATS' + struct.pack('<I', len(flat)) + struct.pack('<%dI' % len(flat), *flat)
    out += struct.pack('<III', d['matid'], d['selgroup'], d['selflags'])
    out += struct.pack('<7f', *d['ext'])
    out += struct.pack('<I', len(d['seqext']) // 28) + bytes(d['seqext'])
    out += b'UVAS' + struct.pack('<I', len(d['uvs']))
    for uv in d['uvs']:
        out += b'UVBS' + struct.pack('<I', nv) + struct.pack('<%df' % (nv * 2), *uv)
    out += bytes(d['tail'])
    return struct.pack('<I', len(out) + 4) + out


def extents_of(vrtx):
    xs = vrtx[0::3]
    ys = vrtx[1::3]
    zs = vrtx[2::3]
    mn_ = (min(xs), min(ys), min(zs))
    mx_ = (max(xs), max(ys), max(zs))
    r = math.sqrt(sum((mx_[i] - mn_[i]) ** 2 for i in range(3))) / 2.0
    return (r,) + mn_ + mx_


def dedupe_groups(d):
    used = set(d['gndx'])
    key2new = {}
    newgroups = []
    remap = {}
    for gi, grp in enumerate(d['groups']):
        if gi not in used:
            continue
        key = tuple(sorted(set(grp)))
        if key not in key2new:
            key2new[key] = len(newgroups)
            newgroups.append(key)
        remap[gi] = key2new[key]
    d['gndx'] = [remap[g] for g in d['gndx']]
    d['groups'] = newgroups
    return d


def split_geoset(d):
    idx = d['pvtx']
    ntri = len(idx) // 3
    halves = [range(0, ntri // 2), range(ntri // 2, ntri)]
    outs = []
    for h in halves:
        tris = [idx[t * 3:t * 3 + 3] for t in h]
        used = sorted(set(i for tri in tris for i in tri))
        vmap = {old: new for new, old in enumerate(used)}
        e = dict(d)
        e['vrtx'] = [d['vrtx'][i * 3 + k] for i in used for k in range(3)]
        e['nrms'] = [d['nrms'][i * 3 + k] for i in used for k in range(3)] if d['nrms'] is not None else None
        e['uvs'] = [[uv[i * 2 + k] for i in used for k in range(2)] for uv in d['uvs']]
        e['pvtx'] = [vmap[i] for tri in tris for i in tri]
        e['ptyp'] = (4,)
        e['pcnt'] = (len(e['pvtx']),)
        e['gndx'] = [d['gndx'][i] for i in used]
        e['groups'] = list(d['groups'])
        e = dedupe_groups(e)
        e['ext'] = extents_of(e['vrtx'])
        outs.append(e)
    return outs


def group_stats(data):
    chunks = mn.parse_chunks(data)
    geos = next((b for t, b in chunks if t == b'GEOS'), None)
    if geos is None:
        return []
    res = []
    for g in mn.split_geosets(geos):
        parts, after = mn.geoset_parts(g)
        res.append(parts[b'MTGC'][1])
    return res


def fix_matrix_groups(data, limit=LIMIT, so_dedup=False):
    chunks = mn.parse_chunks(data)
    geos_i = next((i for i, c in enumerate(chunks) if c[0] == b'GEOS'), None)
    info = {'before': [], 'after_diag': []}
    if geos_i is None:
        return data, info
    gsets = mn.split_geosets(chunks[geos_i][1])
    info['before'] = [struct.unpack_from('<I', g, mn.geoset_parts(g)[0][b'MTGC'][0] + 4)[0] for g in gsets]
    if max(info['before'], default=0) <= limit:
        info['action_code'] = 'nada a fazer'
        return data, info
    info['so_dedup'] = so_dedup
    info['above_do_limit'] = []
    newsets = []
    extra = []
    for gi, g in enumerate(gsets):
        cnt = info['before'][gi]
        if cnt <= limit:
            newsets.append((bytes(g), gi))
            continue
        d = dedupe_groups(geoset_full(g))
        if len(d['groups']) <= limit:
            newsets.append((build_geoset(d)[4:], gi))
            continue
        if so_dedup:
            info['above_do_limit'].append({'geoset': gi, 'clusters': len(d['groups'])})
            newsets.append((bytes(g), gi))
            continue
        parts = [d]
        for _ in range(8):
            if all(len(p['groups']) <= limit for p in parts):
                break
            nxt = []
            for p in parts:
                nxt += split_geoset(p) if len(p['groups']) > limit else [p]
            parts = nxt
        if any(len(p['groups']) > limit for p in parts):
            raise ValueError('geoset %d: the groups could not be reduced' % gi)
        newsets.append((build_geoset(parts[0])[4:], gi))
        for p in parts[1:]:
            extra.append((build_geoset(p)[4:], gi))
    allsets = newsets + extra
    body = bytearray()
    for g, origin in allsets:
        body += struct.pack('<I', len(g) + 4) + g
    chunks[geos_i][1] = body
    info['after_diag'] = [
        struct.unpack_from('<I', g, mn.geoset_parts(bytearray(g))[0][b'MTGC'][0] + 4)[0] for g, o in allsets
    ]
    info['geosets'] = (len(gsets), len(allsets))
    geoa_i = next((i for i, c in enumerate(chunks) if c[0] == b'GEOA'), None)
    if geoa_i is not None and extra:
        ga = chunks[geoa_i][1]
        entries = []
        q = 0
        while q + 4 <= len(ga):
            sz = struct.unpack_from('<I', ga, q)[0]
            if sz < 28:
                break
            entries.append(bytearray(ga[q:q + sz]))
            q += sz
        newga = bytearray()
        for e in entries:
            newga += e
        for k, (g, origin) in enumerate(extra):
            newid = len(newsets) + k
            for e in entries:
                if struct.unpack_from('<I', e, 24)[0] == origin:
                    e2 = bytearray(e)
                    struct.pack_into('<I', e2, 24, newid)
                    newga += e2
        chunks[geoa_i][1] = newga
        info['geoa_replicadas'] = len(newga) > len(ga)
    out = b'MDLX' + b''.join(c[0] + struct.pack('<I', len(c[1])) + bytes(c[1]) for c in chunks)
    return out, info
