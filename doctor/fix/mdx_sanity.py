# Checks MDX models: references, animation tracks, geometry, the version an older game loads.
import math
import os
import struct

from doctor.fix import mdx_struct
from doctor.models import mdxcheck


GUESSED_MAX_VERTICES = 7433
TEXTURE_EXTS = ('.blp', '.tga', '.tif', '.dds')
KNOWN_REPLACEABLE = (0, 1, 2, 11, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37)
MAX_EXAMPLES = 3


class _Found(object):
    def __init__(self):
        self.by = {}
        self.order = []

    def add(self, code, level, text, example=None):
        e = self.by.get(code)
        if e is None:
            e = self.by[code] = {'code': code, 'level': level, 'text': text, 'count': 0, 'examples': []}
            self.order.append(code)
        e['count'] += 1
        if example and len(e['examples']) < MAX_EXAMPLES:
            e['examples'].append(example)

    def result(self):
        out = []
        for code in self.order:
            e = self.by[code]
            e['text'] = e['text'] % {'n': e['count']} if '%(n)' in e['text'] else e['text']
            out.append(e)
        return out


def _bounds_problem(b):
    if any(not math.isfinite(v) for v in b):
        return 'nan'
    if all(v >= 3.0e38 for v in b[1:4]) and all(v <= -3.0e38 for v in b[4:7]):
        return None
    if b[0] < 0 or b[1] > b[4] or b[2] > b[5] or b[3] > b[6]:
        return 'inverted'
    return None


def _floats(data, off, n):
    import numpy as np
    return np.frombuffer(data, dtype='<f4', count=n, offset=off)


def check(data, version=None):
    data = bytes(data)
    m = mdx_struct.read(data)
    f = _Found()
    game = _classic(version)
    if m.notes:
        f.add('mdx_unread', 'info', 'Part of the model could not be read (%s): the checks that need it were skipped.'
              % m.notes[0], m.notes[0])
    _header(m, f, game)
    _textures(m, f)
    _materials(m, f)
    _geosets(m, f, game)
    _references(m, f)
    _tracks(m, f)
    return f.result()


def _classic(version):
    if not version:
        return False
    from doctor.data import wc3_versions
    v = wc3_versions.normalize(version)
    return bool(v) and v != wc3_versions.REFORGED


def _header(m, f, game):
    if m.version not in mdxcheck.VERSIONS:
        f.add('mdx_version', 'info', 'The model version %s is not one the archive knows (800 to 1800).' % m.version)
    elif game and m.version != 800:
        f.add('mdx_version_classic', 'warning',
              'The model is version %d: the game before Reforged reads version 800 only (the format documentation), '
              'so it should not load it.' % m.version)
    boxes = [('sequence "%s"' % s['name'], s['bounds']) for s in m.seqs]
    if m.modl:
        boxes.insert(0, ('the model', m.modl['bounds']))
    for where, b in boxes:
        why = _bounds_problem(b)
        if why == 'nan':
            f.add('mdx_extent_nan', 'warning', '%(n)d bounds with a NaN or an infinity.', where)
        elif why:
            f.add('mdx_extent', 'info', '%(n)d bounds that are not a box (a negative radius or a minimum above its '
                  'maximum).', where)
    for i, s in enumerate(m.seqs):
        if s['end'] <= s['start']:
            f.add('mdx_sequence_length', 'info', '%(n)d sequence(s) with no length or a negative one.',
                  '"%s" %d..%d' % (s['name'], s['start'], s['end']))
        if m.version == 800:
            for j in range(i):
                o = m.seqs[j]
                if s['start'] == o['start'] or s['start'] < o['end']:
                    f.add('mdx_sequence_overlap', 'warning' if game else 'info',
                          '%(n)d sequence(s) start at or before the end of an earlier one (version 800).',
                          '"%s" and "%s"' % (s['name'], o['name']))
                    break
    for i, g in enumerate(m.glbs):
        if g == 0:
            f.add('mdx_track_duplicate', 'info', 'A global sequence of length 0.', 'global sequence %d' % i)


def _textures(m, f):
    for i, t in enumerate(m.texs):
        path = t['path'].lower()
        ext = os.path.splitext(path)[1]
        if path and ext not in TEXTURE_EXTS:
            f.add('mdx_texture_path', 'warning', '%(n)d texture path(s) that are not .blp, .tga, .tif or .dds.',
                  'texture %d "%s"' % (i, t['path'][:60]))
        if t['replaceable'] not in KNOWN_REPLACEABLE:
            f.add('mdx_texture_replaceable', 'info', '%(n)d texture(s) with a replaceable id the archive does not know '
                  '(nothing is behind it).', 'texture %d id %d' % (i, t['replaceable']))


def _materials(m, f):
    ntex, nanim = len(m.texs), len(m.txan)
    for i, mat in enumerate(m.mats):
        if not mat['layers']:
            continue
        for k, lay in enumerate(mat['layers']):
            where = 'material %d layer %d' % (i, k)
            tex = [lay['texture']] if not lay['slots'] else [x[0] for x in lay['slots']]
            for t in lay['tracks']:
                if t.tag == 'KMTF':
                    tex = [struct.unpack_from('<i', m.data, t.body + r * t.stride + 4)[0] for r in range(t.count)]
            if any(x < 0 or x >= ntex for x in tex if x != -1) or (tex == [-1] and not lay['tracks']):
                f.add('mdx_layer_texture', 'warning', '%(n)d layer(s) name a texture the model does not have.', where)
            if lay['texanim'] != -1 and not 0 <= lay['texanim'] < nanim:
                f.add('mdx_layer_texanim', 'warning', '%(n)d layer(s) name a texture animation the model does not '
                      'have.', where)
            if lay['filter'] > 6:
                f.add('mdx_layer_filter', 'info', '%(n)d layer(s) with a filter mode above 6.', where)


def _geosets(m, f, game):
    import numpy as np
    d = m.data
    nmat = len(m.mats)
    nodes = len(m.nodes)
    bones = set(n['id'] for n in m.nodes if n['kind'] == b'BONE')
    ids = set(n['id'] for n in m.nodes)
    for gi, g in enumerate(m.geos):
        parts = g['parts']
        where = 'geoset %d' % gi
        if 'VRTX' not in parts or 'MATS' not in parts:
            continue
        nv = parts['VRTX'][0]
        if g.get('uvas') is not None and g['material'] >= nmat:
            f.add('mdx_geoset_material', 'warning', '%(n)d geoset(s) name a material the model does not have.', where)
        if nv:
            v = _floats(d, parts['VRTX'][1], nv * 3)
            if not np.isfinite(v).all():
                f.add('mdx_geoset_nan', 'warning', '%(n)d geoset(s) have a vertex or a normal that is a NaN or an '
                      'infinity.', where)
            elif 'NRMS' in parts and parts['NRMS'][0] == nv and not np.isfinite(_floats(d, parts['NRMS'][1],
                                                                                          nv * 3)).all():
                f.add('mdx_geoset_nan', 'warning', '%(n)d geoset(s) have a vertex or a normal that is a NaN or an '
                      'infinity.', where)
        npv = parts['PVTX'][0]
        if npv == 0:
            f.add('mdx_geoset_empty', 'info', '%(n)d geoset(s) with no faces.', where)
        else:
            idx = np.frombuffer(d, dtype='<u2', count=npv, offset=parts['PVTX'][1])
            if int(idx.max()) >= nv:
                f.add('mdx_geoset_index', 'warning', '%(n)d geoset(s) have a triangle index at or above the vertex '
                      'count.', '%s: index %d, %d vertices' % (where, int(idx.max()), nv))
            pcnt = parts['PCNT']
            total = int(np.frombuffer(d, dtype='<u4', count=pcnt[0], offset=pcnt[1]).sum()) if pcnt[0] else 0
            if npv % 3 or total != npv:
                f.add('mdx_geoset_faces', 'warning', '%(n)d geoset(s) whose face lists disagree.',
                      '%s: %d indices, counts add up to %d' % (where, npv, total))
        classic = g.get('skin') is None
        if classic and nv >= GUESSED_MAX_VERTICES:
            f.add('mdx_geoset_big', 'warning' if game else 'info',
                  '%(n)d geoset(s) of the classic skinning have 7,433 vertices or more: the old game rendered them '
                  'bugged, as the mdx-m3-viewer author measured (not checked on 3.0).', '%s: %d vertices' % (where, nv))
        if classic and parts['GNDX'][0] == nv and nv and parts['MTGC'][0]:
            gn = np.frombuffer(d, dtype='u1', count=nv, offset=parts['GNDX'][1])
            if int(gn.max()) >= parts['MTGC'][0]:
                f.add('mdx_vertex_group', 'warning', '%(n)d geoset(s) have a vertex in a matrix group they do not '
                      'have.', '%s: group %d of %d' % (where, int(gn.max()), parts['MTGC'][0]))
        if g.get('skin') and nv:
            cnt, off, width = g['skin']
            if cnt == nv * 8:
                a = np.frombuffer(d, dtype='<u2' if width == 2 else 'u1', count=cnt, offset=off).reshape(nv, 8)
                w = a[:, 4:].astype(np.int32)
                s = w.sum(axis=1)
                bad = int((s != 255).sum())
                far = int(((a[:, :4] >= nodes) & (w > 0)).sum()) if nodes else 0
                if bad or far:
                    f.add('mdx_skin', 'warning', '%(n)d geoset(s) have SKIN vertices whose weights do not add up to '
                          '255 (or that have none) or whose bone is past the nodes.',
                          '%s: %d vertices off 255, %d bone indices past %d nodes' % (where, bad, far, nodes))
        if classic and parts['MATS'][0] and ids:
            ms = np.frombuffer(d, dtype='<u4', count=parts['MATS'][0], offset=parts['MATS'][1])
            if any(int(x) not in ids for x in np.unique(ms)):
                f.add('mdx_vertex_group', 'warning', '%(n)d geoset(s) have a vertex in a matrix group they do not '
                      'have.', '%s: a matrix names a node that does not exist' % where)


def _references(m, f):
    ntex, nmat, ngeo = len(m.texs), len(m.mats), len(m.geos)
    for i, a in enumerate(m.geoa):
        if a['geoset'] != -1 and not 0 <= a['geoset'] < ngeo:
            f.add('mdx_ref_geoset', 'warning', '%(n)d geoset animation(s) name a geoset the model does not have.',
                  'geoset animation %d -> geoset %d' % (i, a['geoset']))
    for n in m.nodes:
        if n['kind'] == b'PRE2' and 'texture' in n:
            if n['texture'] >= ntex:
                f.add('mdx_emitter_texture', 'warning', '%(n)d particle emitter(s) name a texture the model does not '
                      'have.', n['owner'])
            if not 0 <= n['time_middle'] <= 1:
                f.add('mdx_emitter_time', 'info', '%(n)d particle emitter(s) have timeMiddle outside 0..1.',
                      '%s: %s' % (n['owner'], n['time_middle']))
            if n.get('xyquad') and (n['speed'] == 0 or n['latitude'] == 0):
                f.add('mdx_emitter_xyquad', 'info', '%(n)d XY quad emitter(s) have no speed or no latitude.',
                      n['owner'])
        elif n['kind'] == b'RIBB' and 'material' in n and n['material'] >= nmat:
            f.add('mdx_ribbon_material', 'warning', '%(n)d ribbon emitter(s) name a material the model does not have.',
                  n['owner'])


def _tracks(m, f):
    d = m.data
    nglbs = len(m.glbs)
    seqs = [(s['start'], s['end'], s['name']) for s in m.seqs]
    for t in m.tracks:
        if t.gseq != -1 and not 0 <= t.gseq < nglbs:
            f.add('mdx_track_global_seq', 'warning', '%(n)d track(s) are on a global sequence the model does not have.',
                  '%s %s -> global sequence %d' % (t.owner, t.tag, t.gseq))
        if t.count == 0:
            f.add('mdx_track_duplicate', 'info', '%(n)d empty track(s), repeated or negative frames.',
                  '%s %s: no keys' % (t.owner, t.tag))
            continue
        fr = t.frames
        back = next((i for i in range(1, len(fr)) if fr[i] < fr[i - 1]), None)
        if back is not None:
            f.add('mdx_track_order', 'warning', '%(n)d track(s) have keys that go back in time.',
                  '%s %s: key %d at frame %d after frame %d' % (t.owner, t.tag, back, fr[back], fr[back - 1]))
        elif any(fr[i] == fr[i - 1] for i in range(1, len(fr))) or fr[0] < 0:
            f.add('mdx_track_duplicate', 'info', '%(n)d empty track(s), repeated or negative frames.',
                  '%s %s: repeated or negative frame' % (t.owner, t.tag))
        if t.event or t.interp == 0 or t.gseq != -1 or back is not None or t.count < 2:
            continue
        stride = t.stride
        for s0, s1, name in seqs:
            ks = [i for i, x in enumerate(fr) if s0 <= x <= s1]
            if len(ks) < 2 or fr[ks[0]] == s0:
                continue
            first = d[t.body + ks[0] * stride + 4:t.body + ks[0] * stride + 4 + 4 * t.words]
            last = d[t.body + ks[-1] * stride + 4:t.body + ks[-1] * stride + 4 + 4 * t.words]
            if first != last:
                f.add('mdx_track_opening', 'info',
                      '%(n)d track(s) have no key at the start of a sequence where their values differ at its ends '
                      '(bugged warping with negative interpolations, as the mdx-m3-viewer author puts it).',
                      '%s %s in "%s" (starts at %d, first key %d)' % (t.owner, t.tag, name, s0, fr[ks[0]]))
                break


REFERENCE_CODES = ('mdx_geoset_index', 'mdx_geoset_nan', 'mdx_geoset_faces', 'mdx_geoset_material', 'mdx_layer_texture',
                   'mdx_layer_texanim', 'mdx_ref_geoset', 'mdx_emitter_texture', 'mdx_ribbon_material',
                   'mdx_track_global_seq', 'mdx_skin', 'mdx_vertex_group', 'mdx_extent_nan', 'mdx_texture_path')
TRACK_CODES = ('mdx_track_order', 'mdx_track_opening', 'mdx_track_duplicate')
PHRASE = {
    'mdx_geoset_index': 'a triangle past its vertices',
    'mdx_geoset_nan': 'a vertex that is not a number',
    'mdx_geoset_faces': 'face lists that disagree',
    'mdx_geoset_material': 'a material the model does not have',
    'mdx_layer_texture': 'a texture the model does not have',
    'mdx_layer_texanim': 'a texture animation the model does not have',
    'mdx_ref_geoset': 'a geoset animation of a missing geoset',
    'mdx_emitter_texture': 'an emitter with a missing texture',
    'mdx_ribbon_material': 'a ribbon with a missing material',
    'mdx_track_global_seq': 'a track on a missing global sequence',
    'mdx_skin': 'SKIN weights that do not add up',
    'mdx_vertex_group': 'a vertex in a matrix group that does not exist',
    'mdx_extent_nan': 'bounds that are not numbers',
    'mdx_texture_path': 'a texture path that is not an image file',
}


def summary(result, version=None):
    by = result.get('by_code') or {}

    def files(codes):
        seen = []
        for c in codes:
            for f in by.get(c, ()):
                if f not in seen:
                    seen.append(f)
        return seen
    out = []
    refs = files(REFERENCE_CODES)
    if refs:
        parts = ['%s (%d)' % (PHRASE[c], len(by[c])) for c in REFERENCE_CODES if by.get(c)]
        out.append({'code': 'model_references', 'severity': 'warning', 'files': refs[:30], 'count': len(refs),
                    'text': '%d models have data that points at something they do not have, or a number that is not '
                            'one: %s. Not measured as a crash; it is what the model checkers of other tools report.'
                            % (len(refs), ', '.join(parts))})
    ver = files(('mdx_version_classic',))
    if ver:
        out.append(
            {
                'code': 'model_version',
                'severity': 'warning',
                'files': ver[:30],
                'count': len(ver),
                'text': '%d models are not version 800: the game before Reforged reads version 800 only, so it should '
                'not load them.' % len(ver),
            }
        )
    tracks = files(TRACK_CODES)
    if tracks:
        out.append({'code': 'model_tracks', 'severity': 'info', 'files': tracks[:30], 'count': len(tracks),
                    'text': '%d models have animation keys out of order, repeated, or without a key at the start of a '
                            'sequence (the mdx-m3-viewer sanity test calls the last one "bugged warping").'
                            % len(tracks)})
    rest = [c for c in by if c not in REFERENCE_CODES and c not in TRACK_CODES and c != 'mdx_version_classic']
    odd = files(sorted(rest))
    if odd:
        out.append({'code': 'model_odd', 'severity': 'info', 'files': odd[:30], 'count': len(odd),
                    'text': '%d models have oddities (%s): sequences with no length or overlapping, empty bounds, '
                            'emitter settings, geosets of the classic skinning with 7,433 vertices or more.'
                            % (len(odd), ', '.join(sorted(c[4:] for c in rest)))})
    return out


def scan_map(path, version=None, progress=None):
    from doctor.models import model_check
    p = progress or (lambda *_a, **_k: None)
    out = {'checked': 0, 'models': [], 'by_code': {}, 'skipped': []}
    p('Reading the map')
    a, err = model_check._open(path)
    if a is None:
        out['error'] = err
        return out
    p('Finding the file names')
    for name, _bi, data in model_check._models(a, sorted(set(model_check._names(a))), p):
        if data is None:
            out['skipped'].append({'file': name, 'reason': 'cannot be read'})
            continue
        if data[:4] not in mdxcheck.MAGICS:
            out['skipped'].append({'file': name, 'reason': 'not a binary MDX model'})
            continue
        try:
            issues = check(data, version)
        except (ValueError, struct.error) as e:
            out['skipped'].append({'file': name, 'reason': str(e)[:80]})
            continue
        out['checked'] += 1
        if issues:
            out['models'].append({'file': name, 'issues': issues})
            for code in sorted(set(i['code'] for i in issues)):
                out['by_code'].setdefault(code, []).append(name)
    p('Done')
    return out
