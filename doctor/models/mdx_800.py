# Writes an MDX model of version 900 or later as version 800, the one the game before Reforged reads.
import struct

from doctor.fix import mdx_struct


LAYER_TRACKS_800 = ('KMTF', 'KMTA')
LIGHT_TRACKS_800 = ('KLAS', 'KLAE', 'KLAC', 'KLAI', 'KLBI', 'KLBC', 'KLAV')
LIGHT_800 = 44
DROP = (b'FAFX', b'BPOS')


def _chunk(tag, body):
    return tag + struct.pack('<I', len(body)) + body


def _tracks_in(m, lo, hi, tags, first_only=()):
    out, seen = [], set()
    for t in sorted((t for t in m.tracks if lo <= t.start and t.end <= hi), key=lambda t: t.start):
        if t.tag in tags and not (t.tag in first_only and t.tag in seen):
            out.append(m.data[t.start:t.end])
            seen.add(t.tag)
    return b''.join(out)


def _materials(m, info):
    d = m.data
    out = []
    for mat in m.mats:
        layers = mat['layers']
        hd = mat['shader'].lower().startswith('shader_hd') or any(
            l['slots'] and struct.unpack_from('<I', d, l['off'] + 52)[0] != 0 for l in layers)
        if hd and len(layers) > 1:
            info['hd_layers_dropped'] += len(layers) - 1
            layers = layers[:1]
        elif hd:
            info['hd_materials'] += 1
        lays = []
        for l in layers:
            tex = l['slots'][0][0] if l['slots'] else l['texture']
            tracks = _tracks_in(m, l['off'], l['end'], LAYER_TRACKS_800, first_only=('KMTF',))
            body = struct.pack('<IIiiIf', l['filter'], l['shading'], tex, l['texanim'], l['coord'], l['alpha'])
            lays.append(struct.pack('<I', 4 + len(body) + len(tracks)) + body + tracks)
        body = (
            struct.pack('<iI', mat['priority'], mat['flags']) + b'LAYS' + struct.pack('<I', len(lays)) + b''.join(lays)
        )
        out.append(struct.pack('<I', 4 + len(body)) + body)
    return b''.join(out)


def _groups_from_skin(m, g):
    d = m.data
    nv = g['parts']['VRTX'][0]
    cnt, at, width = g['skin']
    if width != 1 or cnt != 8 * nv:
        raise ValueError('a SKIN of %d entries of %d bytes for %d vertices' % (cnt, width, nv))
    mats_n, mats_at = g['parts']['MATS']
    mats = list(struct.unpack_from('<%dI' % mats_n, d, mats_at))
    mtgc_n, mtgc_at = g['parts']['MTGC']
    sizes = list(struct.unpack_from('<%dI' % mtgc_n, d, mtgc_at))
    if any(s != 1 for s in sizes):
        raise ValueError('a SKIN geoset whose matrix groups are not one bone each')
    groups, index, gndx = [], {}, bytearray()
    for v in range(nv):
        bones = d[at + 8 * v:at + 8 * v + 4]
        weights = d[at + 8 * v + 4:at + 8 * v + 8]
        key = tuple(sorted(set(mats[b] for b, w in zip(bones, weights) if w and b < len(mats)))) or (mats[0],)
        if key not in index:
            index[key] = len(groups)
            groups.append(key)
        gndx.append(index[key])
        if len(groups) > 256:
            raise ValueError('more than 256 vertex groups from the SKIN')
    flat = [b for k in groups for b in k]
    return (b'GNDX' + struct.pack('<I', nv) + bytes(gndx),
            b'MTGC' + struct.pack('<I', len(groups)) + struct.pack('<%dI' % len(groups), *[len(k) for k in groups]),
            b'MATS' + struct.pack('<I', len(flat)) + struct.pack('<%dI' % len(flat), *flat), len(groups))


def _geosets(m, info):
    d = m.data
    out = []
    for g in m.geos:
        if 'tail_at' not in g or 'mats_end' not in g:
            raise ValueError('a geoset that does not parse')
        vrtx_at = g['parts']['VRTX'][1] - 8
        gndx_at = g['parts']['GNDX'][1] - 8
        parts = d[vrtx_at:gndx_at]
        if g['skin'] and g['parts']['GNDX'][0] == 0:
            gn, mt, ma, n = _groups_from_skin(m, g)
            parts += gn + mt + ma
            info['skin_geosets'] += 1
            info['skin_groups'] += n
        else:
            parts += d[gndx_at:g['mats_end']]
        q = g['mats_end']
        head = d[q:q + 12]
        nex, ext_at = g['seq_extents']
        bounds_at = ext_at - 32
        body = parts + head + d[bounds_at:ext_at + 28 * nex] + d[g['tail_at']:g['end']]
        out.append(struct.pack('<I', 4 + len(body)) + body)
    return b''.join(out)


def _lights(m, size, off):
    d = m.data
    out = []
    for n in (x for x in m.nodes if x['kind'] == b'LITE'):
        node = d[n['off']:n['end']]
        first = n['end']
        fixed = d[first:first + LIGHT_800]
        tracks = _tracks_in(m, first, n['entry_end'], LIGHT_TRACKS_800)
        body = node + fixed + tracks
        out.append(struct.pack('<I', 4 + len(body)) + body)
    return b''.join(out)


def _cameras(m):
    d = bytearray()
    for c in m.cams:
        e = bytearray(m.data[c['off']:c['end']])
        struct.pack_into('<I', e, 0, (c['end'] - c['off']))
        d += e
    return bytes(d)


def _popcorns_as_helpers(m):
    out = []
    for n in (x for x in m.nodes if x['kind'] == b'CORN'):
        node = bytearray(m.data[n['off']:n['end']])
        struct.pack_into('<I', node, 92, n['flags'] & 0xFF)
        out.append(bytes(node))
    return b''.join(out)


def convert(data):
    m = mdx_struct.read(data)
    if m.version is None or m.version <= 800:
        return data, {'from': m.version, 'changed': False}
    if m.notes:
        raise ValueError('the model does not read cleanly: %s' % m.notes[0])
    info = {'from': m.version, 'changed': True, 'hd_layers_dropped': 0, 'hd_materials': 0, 'skin_geosets': 0,
            'skin_groups': 0, 'dropped': [], 'popcorns': 0}
    out = [b'MDLX']
    helpers_extra = _popcorns_as_helpers(m)
    info['popcorns'] = sum(1 for x in m.nodes if x['kind'] == b'CORN')
    had_help = any(t == b'HELP' for t, _s, _o in m.chunks)
    for tag, size, off in m.chunks:
        body = data[off:off + size]
        if tag == b'VERS':
            body = struct.pack('<I', 800)
        elif tag == b'MTLS':
            body = _materials(m, info)
        elif tag == b'GEOS':
            body = _geosets(m, info)
        elif tag == b'LITE':
            body = _lights(m, size, off)
        elif tag == b'CAMS':
            body = _cameras(m)
        elif tag == b'HELP' and helpers_extra:
            body = body + helpers_extra
        elif tag == b'CORN':
            if not had_help:
                out.append(_chunk(b'HELP', helpers_extra))
            continue
        elif tag in DROP:
            info['dropped'].append(tag.decode())
            continue
        out.append(_chunk(tag, body))
    new = b''.join(out)
    back = mdx_struct.read(new)
    if back.version != 800 or back.notes or len(back.texs) != len(m.texs) or len(back.mats) != len(m.mats) or \
            len(back.geos) != len(m.geos) or len(back.nodes) != len(m.nodes) or \
            any('tail_at' not in g for g in back.geos) or back.pivots != m.pivots:
        raise ValueError('the version 800 model does not read back the same (%s)' % (back.notes[:1] or
                         'version %s, %d/%d geosets, %d/%d nodes' % (back.version, len(back.geos), len(m.geos),
                                                                    len(back.nodes), len(m.nodes))))
    return new, info
