# Checks the nodes, geosets and sequences of an MDX model in depth.
import math
import struct

from doctor.models import mdxnodes as mn


NODE_CHUNKS = mn.NODE_CHUNKS + (b'CORN',)
CAMERA_MASK = 0x00FFFFFF
LINT_EXAMPLES = 3
def bad(v):
    return math.isnan(v) or math.isinf(v) or abs(v) > 1e7


def deep(data, lint=True):
    r = {}
    chunks = mn.parse_chunks(data)
    version = next((struct.unpack_from('<I', b, 0)[0] for t, b in chunks if t == b'VERS' and len(b) >= 4), None)
    placed = None
    model = None
    if lint or (version is not None and version >= 900):
        try:
            from doctor.fix import mdx_struct
            model = mdx_struct.read(data)
        except Exception:
            model = None
    if version is not None and version >= 900 and model is not None:
        placed = model.geos
    tags = [c[0] for c in chunks]
    r['chunks'] = ' '.join(t.decode('latin-1') for t in tags)
    nodes = {}
    for tag, body in chunks:
        if tag in NODE_CHUNKS:
            for off, tot, noff in mn.iter_entries(tag, body):
                oid, pid, fl = struct.unpack_from('<III', body, noff + 84)
                nodes[oid] = (tag, pid, fl)
    n = len(nodes)
    r['nodes'] = n
    r['max_objid'] = max(nodes) if nodes else -1
    r['dup_objid'] = 0
    seen = set()
    dups = 0
    for tag, body in chunks:
        if tag in NODE_CHUNKS:
            for off, tot, noff in mn.iter_entries(tag, body):
                oid = struct.unpack_from('<I', body, noff + 84)[0]
                if oid in seen:
                    dups += 1
                seen.add(oid)
    r['dup_objid'] = dups
    r['bad_parent'] = sum(1 for o, (t, p, f) in nodes.items() if p != 0xFFFFFFFF and p not in nodes)
    r['self_parent'] = sum(1 for o, (t, p, f) in nodes.items() if p == o)
    cycles = 0
    maxdepth = 0
    for o in nodes:
        seenp = set()
        cur = o
        d = 0
        while cur != 0xFFFFFFFF and cur in nodes:
            if cur in seenp:
                cycles += 1
                break
            seenp.add(cur)
            cur = nodes[cur][1]
            d += 1
            if d > 10000:
                cycles += 1
                break
        maxdepth = max(maxdepth, d)
    r['parent_cycles'] = cycles
    r['max_depth'] = maxdepth
    pivots = next((len(b) // 12 for t, b in chunks if t == b'PIVT'), 0)
    r['pivots'] = pivots
    r['pivot_mismatch'] = pivots != n
    exp = {
        b'BONE': 0x100,
        b'LITE': 0x200,
        b'EVTS': 0x400,
        b'ATCH': 0x800,
        b'PREM': 0x1000,
        b'PRE2': 0x1000,
        b'CLID': 0x2000,
        b'RIBB': 0x4000,
    }
    r['flag_mismatch'] = sum(1 for o, (t, p, f) in nodes.items() if t in exp and not (f & exp[t]))
    r['helper_with_typeflag'] = sum(1 for o, (t, p, f) in nodes.items() if t == b'HELP' and (f & 0x7F00))
    ngeos = 0
    geos_body = next((b for t, b in chunks if t == b'GEOS'), None)
    geo_issues = []
    geo_meta = []
    if geos_body is not None:
        gsets = mn.split_geosets(geos_body)
        ngeos = len(gsets)
        nmat = 0
        mtls = next((b for t, b in chunks if t == b'MTLS'), None)
        if mtls is not None:
            q = 0
            while q + 4 <= len(mtls):
                sz = struct.unpack_from('<I', mtls, q)[0]
                if sz < 4 or q + sz > len(mtls):
                    break
                q += sz
                nmat += 1
        for gi, g in enumerate(gsets):
            try:
                parts, after = mn.geoset_parts(g)
            except Exception as e:
                geo_issues.append('g%d:parse:%s' % (gi, e))
                continue
            nv = parts[b'VRTX'][1]
            info = placed[gi] if placed is not None and gi < len(placed) and placed[gi].get('uvas') else None
            nn = parts[b'NRMS'][1] if b'NRMS' in parts else -1
            ptyp = struct.unpack_from('<%dI' % parts[b'PTYP'][1], g, parts[b'PTYP'][2]) if b'PTYP' in parts else ()
            pcnt = struct.unpack_from('<%dI' % parts[b'PCNT'][1], g, parts[b'PCNT'][2]) if b'PCNT' in parts else ()
            npv = parts[b'PVTX'][1]
            gndx = g[parts[b'GNDX'][2]:parts[b'GNDX'][2] + parts[b'GNDX'][3]]
            nmtgc = parts[b'MTGC'][1]
            mats = struct.unpack_from('<%dI' % parts[b'MATS'][1], g, parts[b'MATS'][2])
            if nn != nv:
                geo_issues.append('g%d:nrms%d!=vrtx%d' % (gi, nn, nv))
            if any(t != 4 for t in ptyp):
                geo_issues.append('g%d:ptyp%s' % (gi, ptyp))
            if sum(pcnt) != npv:
                geo_issues.append('g%d:pcnt%d!=pvtx%d' % (gi, sum(pcnt), npv))
            if npv % 3:
                geo_issues.append('g%d:pvtx_nao_mult3' % gi)
            hd = info is not None and info.get('skin') is not None
            if len(gndx) != nv and not hd:
                geo_issues.append('g%d:gndx%d!=vrtx%d' % (gi, len(gndx), nv))
            if gndx and max(gndx) >= nmtgc:
                geo_issues.append('g%d:gndx_max%d>=mtgc%d' % (gi, max(gndx), nmtgc))
            if any(m not in nodes for m in mats):
                geo_issues.append('g%d:mats_invalid' % gi)
            if any(nodes[m][0] != b'BONE' for m in mats if m in nodes):
                geo_issues.append('g%d:mats_nonbone' % gi)
            matid, selg, self_ = struct.unpack_from('<III', g, after)
            lod = 84 if info is not None and info['lod'] else 0
            ext = struct.unpack_from('<7f', g, after + 12 + lod)
            next_ = struct.unpack_from('<I', g, after + 40 + lod)[0]
            if matid >= nmat:
                geo_issues.append('g%d:matid%d>=nmat%d' % (gi, matid, nmat))
            if self_ & 4:
                geo_issues.append('g%d:unselectable' % gi)
            if any(bad(x) for x in ext):
                geo_issues.append('g%d:extents_ruins' % gi)
            if all(abs(x) < 1e-6 for x in ext) and (version or 800) < 900:
                geo_issues.append('g%d:extents_zero' % gi)
            p2 = after + 44 + lod + next_ * 28
            if info is not None:
                p2 = info['tail_at'] - (info['off'] + 4)
            geo_meta.append((gi, g, parts, p2, nv))
            if g[p2:p2 + 4] != b'UVAS':
                geo_issues.append('g%d:sem_UVAS' % gi)
            else:
                nuv = struct.unpack_from('<I', g, p2 + 4)[0]
                p3 = p2 + 8
                for k in range(nuv):
                    if g[p3:p3 + 4] != b'UVBS':
                        geo_issues.append('g%d:UVBS_ausente' % gi)
                        break
                    c2 = struct.unpack_from('<I', g, p3 + 4)[0]
                    if c2 != nv:
                        geo_issues.append('g%d:uvbs%d!=vrtx%d' % (gi, c2, nv))
                    p3 += 8 + c2 * 8
    r['geosets'] = ngeos
    r['geo_issues'] = geo_issues[:8]
    ngeoa = 0
    geoa = next((b for t, b in chunks if t == b'GEOA'), None)
    if geoa is not None:
        q = 0
        while q + 4 <= len(geoa):
            sz = struct.unpack_from('<I', geoa, q)[0]
            if sz < 28 or q + sz > len(geoa):
                break
            q += sz
            ngeoa += 1
    bad_gid = 0
    bad_gaid = 0
    for tag, body in chunks:
        if tag == b'BONE':
            for off, tot, noff in mn.iter_entries(tag, body):
                ns = struct.unpack_from('<I', body, noff)[0]
                gid, gaid = struct.unpack_from('<II', body, noff + ns)
                if gid != 0xFFFFFFFF and gid >= ngeos:
                    bad_gid += 1
                if gaid != 0xFFFFFFFF and gaid >= ngeoa:
                    bad_gaid += 1
    r['bone_bad_geosetId'] = bad_gid
    r['bone_bad_geosetAnimId'] = bad_gaid
    seqs = next((b for t, b in chunks if t == b'SEQS'), b'')
    sq = []
    for i in range(len(seqs) // 132):
        nm = seqs[i * 132:i * 132 + 80].split(b'\0')[0].decode('latin-1', 'replace')
        s, e = struct.unpack_from('<II', seqs, i * 132 + 80)
        ms, fl, rar, sync = struct.unpack_from('<fIfI', seqs, i * 132 + 88)
        rad = struct.unpack_from('<f', seqs, i * 132 + 104)[0]
        mn_ = struct.unpack_from('<3f', seqs, i * 132 + 108)
        mx_ = struct.unpack_from('<3f', seqs, i * 132 + 120)
        sq.append((nm, s, e, ms, fl, rar, sync, rad, mn_, mx_))
    r['seqs'] = len(sq)
    r['seq_bad_interval'] = sum(1 for x in sq if x[2] <= x[1])
    r['seq_bad_extents'] = sum(1 for x in sq if bad(x[7]) or any(bad(v) for v in x[8] + x[9]) or x[7] <= 0)
    r['seq_flags_odd'] = sorted(set(x[4] for x in sq if x[4] not in (0, 1)))
    r['seq_overlap'] = 0
    ivs = sorted((x[1], x[2]) for x in sq)
    for a, b in zip(ivs, ivs[1:]):
        if b[0] < a[1]:
            r['seq_overlap'] += 1
    r['seq_names'] = [x[0] for x in sq][:20]
    r['has_stand'] = any(x[0].lower().startswith('stand') for x in sq)
    r['has_death'] = any(x[0].lower().startswith('death') for x in sq)
    atch = []
    for tag, body in chunks:
        if tag == b'ATCH':
            for off, tot, noff in mn.iter_entries(tag, body):
                ns = struct.unpack_from('<I', body, noff)[0]
                path = body[noff + ns:noff + ns + 260].split(b'\0')[0].decode('latin-1', 'replace')
                aid = struct.unpack_from('<I', body, noff + ns + 260)[0]
                name = body[noff + 4:noff + 84].split(b'\0')[0].decode('latin-1', 'replace')
                atch.append((name, path, aid))
    r['attachments'] = len(atch)
    r['attach_with_path'] = [a for a in atch if a[1]]
    r['attach_names'] = [a[0] for a in atch][:12]
    cams = next((b for t, b in chunks if t == b'CAMS'), b'')
    r['cams'] = 0
    q = 0
    while q + 4 <= len(cams):
        sz = struct.unpack_from('<I', cams, q)[0] & CAMERA_MASK
        if sz < 4 or q + sz > len(cams):
            break
        r['cams'] += 1
        vals = struct.unpack_from('<7f', cams, q + 84)
        if any(bad(v) for v in vals):
            r['cam_bad'] = True
        q += sz
    texs = next((b for t, b in chunks if t == b'TEXS'), b'')
    r['textures'] = len(texs) // 268
    r['tex_flags'] = sorted(set(struct.unpack_from('<I', texs, k * 268 + 264)[0] for k in range(len(texs) // 268)))
    r['tex_repl'] = sorted(set(struct.unpack_from('<I', texs, k * 268)[0] for k in range(len(texs) // 268)))
    modl = next((b for t, b in chunks if t == b'MODL'), None)
    if modl is not None:
        ext = struct.unpack_from('<7f', modl, 340)
        r['modl_ext_zero'] = all(abs(v) < 1e-6 for v in ext)
        r['modl_ext_bad'] = any(bad(v) for v in ext)
        r['modl_blend'] = struct.unpack_from('<I', modl, 368)[0]
        r['modl_anim_file'] = modl[80:340].split(b'\0')[0].decode('latin-1', 'replace')
    r['version'] = version
    if lint:
        _lint(r, data, model, geo_meta)
    return r


def _lint(r, data, model, geo_meta):
    lint = {}
    examples = {}

    def add(code, n, example):
        if n:
            lint[code] = lint.get(code, 0) + n
            ex = examples.setdefault(code, [])
            if len(ex) < LINT_EXAMPLES:
                ex.append(example)

    try:
        import numpy as np
    except ImportError:
        r['lint_skipped'] = 'numpy is missing'
        return
    for gi, g, parts, p2, nv in geo_meta:
        where = 'g%d' % gi
        v = n = None
        if nv and b'VRTX' in parts and parts[b'VRTX'][2] + nv * 12 <= len(g):
            v = np.frombuffer(g, dtype='<f4', count=nv * 3, offset=parts[b'VRTX'][2]).reshape(nv, 3)
            bad_v = ~_ok(np, v).all(axis=1)
            add('vertex_bad', int(bad_v.sum()), '%s: %d of %d vertices' % (where, int(bad_v.sum()), nv))
        nn = parts[b'NRMS'][1] if b'NRMS' in parts else 0
        if nn and parts[b'NRMS'][2] + nn * 12 <= len(g):
            n = np.frombuffer(g, dtype='<f4', count=nn * 3, offset=parts[b'NRMS'][2]).reshape(nn, 3)
            good = _ok(np, n).all(axis=1)
            add('normal_bad', int((~good).sum()), '%s: %d of %d normals' % (where, int((~good).sum()), nn))
            txt_ln = np.sqrt((n[good].astype(np.float64) ** 2).sum(axis=1))
            zero = int((txt_ln < 1e-6).sum())
            add('normal_zero', zero, '%s: %d of %d normals' % (where, zero, nn))
        if g[p2:p2 + 4] == b'UVAS':
            p3 = p2 + 8
            for _k in range(struct.unpack_from('<I', g, p2 + 4)[0]):
                if g[p3:p3 + 4] != b'UVBS':
                    break
                c2 = struct.unpack_from('<I', g, p3 + 4)[0]
                if p3 + 8 + c2 * 8 > len(g):
                    break
                uv = np.frombuffer(g, dtype='<f4', count=c2 * 2, offset=p3 + 8).reshape(c2, 2)
                bad_uv = int((~_ok(np, uv).all(axis=1)).sum())
                add('uv_bad', bad_uv, '%s: %d of %d UVs' % (where, bad_uv, c2))
                p3 += 8 + c2 * 8
        npv = parts[b'PVTX'][1] if b'PVTX' in parts else 0
        if npv and parts[b'PVTX'][2] + npv * 2 <= len(g):
            idx = np.frombuffer(g, dtype='<u2', count=npv, offset=parts[b'PVTX'][2])
            past = int((idx >= nv).sum())
            add('face_index', past, '%s: index %d, %d vertices' % (where, int(idx.max()), nv))
            if v is not None and npv >= 3:
                tri = idx[:npv - npv % 3].reshape(-1, 3)
                tri = tri[(tri < nv).all(axis=1)]
                a, b, c = (v[tri[:, k]].astype(np.float64) for k in range(3))
                area = np.sqrt((np.cross(b - a, c - a) ** 2).sum(axis=1))
                with np.errstate(invalid='ignore'):
                    flat = int((area <= 1e-9).sum())
                add('face_degenerate', flat, '%s: %d of %d triangles' % (where, flat, len(tri)))
    if model is None:
        if geo_meta:
            r['lint_skipped'] = 'the model could not be read whole (mdx_struct): SKIN, tracks and textures unchecked'
    else:
        _lint_model(np, data, model, geo_meta, add)
    if lint:
        r['lint'] = lint
        r['lint_examples'] = examples


def _ok(np, a):
    with np.errstate(invalid='ignore'):
        return np.isfinite(a) & (np.abs(a) <= 1e7)


def _lint_model(np, data, model, geo_meta, add):
    ids = set(nd['id'] for nd in model.nodes)
    for gi, g, parts, _p2, nv in geo_meta:
        geo = model.geos[gi] if gi < len(model.geos) else None
        if not geo or not geo.get('skin') or not nv:
            continue
        cnt, off, width = geo['skin']
        if cnt != nv * 8 or off + cnt * width > len(data):
            add('skin_size', 1, 'g%d: %d SKIN elements, %d vertices' % (gi, cnt, nv))
            continue
        a = np.frombuffer(data, dtype='<u2' if width == 2 else 'u1', count=cnt, offset=off).reshape(nv, 8)
        bones = a[:, :4].astype(np.int64)
        w = a[:, 4:].astype(np.int64)
        off255 = int((w.sum(axis=1) != 255).sum())
        add('skin_weight', off255, 'g%d: %d of %d vertices' % (gi, off255, nv))
        mats = list(struct.unpack_from('<%dI' % parts[b'MATS'][1], g, parts[b'MATS'][2])) if b'MATS' in parts else []
        used = bones[w > 0]
        far = int((used >= len(mats)).sum())
        add('skin_bone', far, 'g%d: bone %d of a %d-bone list' % (gi, int(used.max()) if used.size else 0, len(mats)))
        if mats:
            undefined = sorted(set(mats[int(b)] for b in np.unique(used) if b < len(mats)) - ids)
            add('skin_node', len(undefined), 'g%d: node %s' % (gi, undefined[:3]))
    for t in model.tracks:
        if t.event or t.kind != 'f' or not t.count:
            continue
        end = t.body + t.count * t.stride
        if end > len(data):
            continue
        k = np.frombuffer(data, dtype='<f4', count=t.count * t.stride // 4, offset=t.body).reshape(t.count, -1)[:, 1:]
        bad_k = int((~np.isfinite(k).all(axis=1)).sum())
        add('track_bad', bad_k, '%s %s: %d of %d keys' % (t.owner, t.tag, bad_k, t.count))
    ntex = len(model.texs)
    if ntex:
        used = set()
        for mat in model.mats:
            for lay in mat['layers']:
                if lay['slots']:
                    used.update(x[0] for x in lay['slots'])
                else:
                    used.add(lay['texture'])
                for t in lay['tracks']:
                    if t.tag == 'KMTF' and t.body + t.count * t.stride <= len(data):
                        used.update(
                            struct.unpack_from('<i', data, t.body + q * t.stride + 4)[0] for q in range(t.count)
                        )
        for nd in model.nodes:
            if 'texture' in nd:
                used.add(nd['texture'])
        loose = [i for i in range(ntex) if i not in used]
        add('texture_unused', len(loose), 'texture %s' % ', '.join(
            '%d "%s"' % (i, model.texs[i]['path'][:50] or 'replaceable %d' % model.texs[i]['replaceable'])
            for i in loose[:3]))
