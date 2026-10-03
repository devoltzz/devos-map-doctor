# Checks the nodes, geosets and sequences of an MDX model in depth.
import math
import struct

from doctor.models import mdxnodes as mn



def bad(v):
    return math.isnan(v) or math.isinf(v) or abs(v) > 1e7


def deep(data):
    r = {}
    chunks = mn.parse_chunks(data)
    tags = [c[0] for c in chunks]
    r['chunks'] = ' '.join(t.decode('latin-1') for t in tags)
    nodes = {}
    for tag, body in chunks:
        if tag in mn.NODE_CHUNKS:
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
        if tag in mn.NODE_CHUNKS:
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
    if geos_body is not None:
        gsets = mn.split_geosets(geos_body)
        ngeos = len(gsets)
        nmat = 0
        mtls = next((b for t, b in chunks if t == b'MTLS'), None)
        if mtls is not None:
            q = 0
            while q + 4 <= len(mtls):
                q += struct.unpack_from('<I', mtls, q)[0]
                nmat += 1
        for gi, g in enumerate(gsets):
            try:
                parts, after = mn.geoset_parts(g)
            except Exception as e:
                geo_issues.append('g%d:parse:%s' % (gi, e))
                continue
            nv = parts[b'VRTX'][1]
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
            if len(gndx) != nv:
                geo_issues.append('g%d:gndx%d!=vrtx%d' % (gi, len(gndx), nv))
            if gndx and max(gndx) >= nmtgc:
                geo_issues.append('g%d:gndx_max%d>=mtgc%d' % (gi, max(gndx), nmtgc))
            if any(m not in nodes for m in mats):
                geo_issues.append('g%d:mats_invalid' % gi)
            if any(nodes[m][0] != b'BONE' for m in mats if m in nodes):
                geo_issues.append('g%d:mats_nonbone' % gi)
            matid, selg, self_ = struct.unpack_from('<III', g, after)
            ext = struct.unpack_from('<7f', g, after + 12)
            next_ = struct.unpack_from('<I', g, after + 40)[0]
            if matid >= nmat:
                geo_issues.append('g%d:matid%d>=nmat%d' % (gi, matid, nmat))
            if self_ & 4:
                geo_issues.append('g%d:unselectable' % gi)
            if any(bad(x) for x in ext):
                geo_issues.append('g%d:extents_ruins' % gi)
            if all(abs(x) < 1e-6 for x in ext):
                geo_issues.append('g%d:extents_zero' % gi)
            p2 = after + 44 + next_ * 28
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
            q += struct.unpack_from('<I', geoa, q)[0]
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
        sz = struct.unpack_from('<I', cams, q)[0]
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
    r['version'] = next((struct.unpack_from('<I', b, 0)[0] for t, b in chunks if t == b'VERS'), None)
    return r
