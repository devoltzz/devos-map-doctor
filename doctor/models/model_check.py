# Finds the imported models that crash or hang the game, and fixes the ones that can be fixed.
import os
import shutil
import struct

from doctor.fix import unprotect
from doctor.models import mdxcheck
from doctor.models import mdxdeep
from doctor.models import mdxgroups
from doctor.fix import mdx_struct
from doctor.models import mdxnodes
from doctor.mpq import mpqadd


MODEL_EXTS = ('.mdx', '.mdl')
MAGICS = mdxcheck.MAGICS
TETO = 512 << 20
FIXES = ('matrix_groups',)
PORTRAIT_VERSION = 900
PORTRAIT_STAMP = 1800


def _nothing(*_a, **_k):
    pass


def _structure(data):
    chunks, err = mdxcheck.walk_path(data)
    if not err:
        return None
    tags = [c[0] for c in chunks]
    lost = next((i for i, t in enumerate(tags) if t not in mdxcheck.TAGS), None)
    if lost and tags[lost - 1] == b'LITE' and tags[lost][:1] == b'K':
        return None
    end = chunks[-1][2] + chunks[-1][1] if chunks else 4
    left = len(data) - end
    if left < 8:
        return 'the file ends %d byte(s) into a chunk header' % left
    tag = data[end:end + 4].decode('latin-1')
    size = struct.unpack_from('<I', data, end + 4)[0]
    return 'chunk %r declares %d bytes, only %d are left' % (tag, size, left - 8)


def _holds(data, out):
    if _structure(out) or max(mdxgroups.group_stats(out), default=0) > mdxgroups.LIMIT:
        return False
    before, after = mdxdeep.deep(data), mdxdeep.deep(out)
    if len(after.get('geo_issues', ())) > len(before.get('geo_issues', ())):
        return False
    return (after.get('lint') or {}).get('face_index', 0) <= (before.get('lint') or {}).get('face_index', 0)


def _fixed(data):
    try:
        out, info = mdxgroups.fix_matrix_groups(data, so_dedup=True)
        if not info.get('above_the_limit') and _holds(data, out):
            info['method'] = 'merged'
            return out, info
        if mdxdeep.deep(data).get('max_objid', -1) >= 256:
            fewer, ninfo = mdxnodes.reduce_nodes(data, 250)
            if 'err' not in ninfo:
                out, info = mdxgroups.fix_matrix_groups(fewer, so_dedup=True)
                if not info.get('above_the_limit') and _holds(data, out):
                    info.update(method='nodes_merged', nodes_before=ninfo.get('nodes_before'),
                                nodes_after=ninfo.get('nodes_after'))
                    return out, info
        out, info = mdxgroups.fix_matrix_groups(data)
        if _holds(data, out):
            info['method'] = 'split'
            return out, info
    except Exception as e:
        _FIXED_ERROR[0] = '%s: %s' % (type(e).__name__, str(e)[:80])
    return None


_FIXED_ERROR = [None]


def _check(data):
    data = bytes(data)
    if data[:4] not in MAGICS:
        head = data[:4].decode('latin-1')
        if head.isprintable() and head.strip():
            raise ValueError('not a binary MDX model (it starts with %r)' % head)
        raise ValueError('not a binary MDX model')
    broken = _structure(data)
    if broken:
        return [{'code': 'broken_structure', 'fixable': False,
                 'text': 'Broken file structure (%s): the game crashes when it loads this model.' % broken}], None
    try:
        groups = mdxgroups.group_stats(data)
    except Exception as e:
        raise ValueError('the geosets do not parse (%s)' % (str(e)[:60] or type(e).__name__))
    over = [(i, n) for i, n in enumerate(groups) if n > mdxgroups.LIMIT]
    if not over:
        return [], None
    _FIXED_ERROR[0] = None
    fixed = _fixed(data)
    worst = max(over, key=lambda x: x[1])
    why = (' The fix failed: %s.' % _FIXED_ERROR[0]) if fixed is None and _FIXED_ERROR[0] else ''
    return [{'code': 'matrix_groups', 'fixable': fixed is not None, 'geosets': [i for i, _n in over],
             'groups': worst[1], 'text': 'Geoset %d has %d matrix groups (255 at most): the game hangs when the mouse '
                                         'is over this model.' % worst + why}], fixed


def model_version(data):
    chunks, _err = mdxcheck.walk_path(bytes(data))
    return next((struct.unpack_from('<I', data, off)[0] for tag, size, off in chunks if tag == b'VERS' and size >= 4),
                None)


def camera_at_risk(data):
    data = bytes(data)
    chunks, err = mdxcheck.walk_path(data)
    if err or data[:4] != b'MDLX':
        return False
    v = model_version(data)
    return v is not None and v < PORTRAIT_VERSION and any(t == b'CAMS' for t, _s, _o in chunks)


def drop_cameras(data):
    data = bytes(data)
    chunks, err = mdxcheck.walk_path(data)
    if err:
        return None
    cut = [(off - 8, off + size) for tag, size, off in chunks if tag == b'CAMS']
    if not cut:
        return None
    out, p = [], 0
    for a, b in cut:
        out.append(data[p:a])
        p = b
    out.append(data[p:])
    new = b''.join(out)
    chunks2, err2 = mdxcheck.walk_path(new)
    if err2 or any(t == b'CAMS' for t, _s, _o in chunks2) or len(chunks2) != len(chunks) - len(cut):
        return None
    return new


def portrait_what(param):
    key = {'stamp': 'portrait_stamp', 'upgrade': 'portrait_upgrade'}.get(param if isinstance(param, str) else '',
                                                                             'portrait_camera')
    return (key,)


def _portrait_mode(what):
    for key, mode in (('portrait_upgrade', 'upgrade'), ('portrait_stamp', 'stamp'), ('portrait_camera', 'camera')):
        if key in what:
            return mode
    return None


def stamp_version(data, version=PORTRAIT_STAMP):
    data = bytes(data)
    chunks, err = mdxcheck.walk_path(data)
    if err:
        raise ValueError(err)
    for tag, size, off in chunks:
        if tag == b'VERS' and size >= 4:
            return data[:off] + struct.pack('<I', version) + data[off + 4:]
    raise ValueError('no VERS chunk')


_TRACK_TAGS = (b'KMTF', b'KMTA', b'KMTE', b'KFC3', b'KFCA', b'KFTC')


def retag_800_layout(data):
    data = bytes(data)
    if len(data) < 16 or data[:4] != b'MDLX' or data[4:8] != b'VERS':
        return None, None
    version = struct.unpack_from('<I', data, 12)[0]
    if version <= 800:
        return None, version
    from doctor.fix import mdx_struct
    try:
        m = mdx_struct.read(data)
    except ValueError:
        return None, version
    layers = [lay for mat in m.mats for lay in mat['layers']]
    if not layers:
        return None, version
    for lay in layers:
        fim, q = lay['end'], lay['off']
        if fim - q != 28 and data[q + 28:q + 32] not in _TRACK_TAGS:
            return None, version
    return stamp_version(data, 800), version


def _layer_widening(texture):
    return struct.pack('<f3f2f2I2I', 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0, 1, max(texture, 0), 0)


_LIGHT_SHADOW = struct.pack('<6f', 0.4, 0.0, 0.0, 0.0005, 0.0, 0.00001)


def _signature(m):
    d = m.data
    return ([bytes(d[t.start:t.end]) for t in m.tracks],
            [bytes(d[g['off'] + 4:g['mats_end']]) for g in m.geos if 'mats_end' in g],
            [(t['replaceable'], t['path'], t['flags']) for t in m.texs],
            [(s['name'], s['start'], s['end'], s['bounds']) for s in m.seqs],
            [(len(mat['layers']), [(x['filter'], x['shading'], x['texture'], x['texanim'], x['coord'], x['alpha'])
                                   for x in mat['layers']]) for mat in m.mats],
            [(n['kind'], n['name'], n['id'], n['parent'], n['flags']) for n in m.nodes])


def upgrade_layout(data):
    data = bytes(data)
    m = mdx_struct.read(data)
    if m.version >= PORTRAIT_VERSION:
        raise ValueError('version %d is not an 800 layout' % m.version)
    if m.notes:
        raise ValueError('the model does not read cleanly (%s)' % m.notes[0])
    edits = []
    for n in m.nodes:
        if n['kind'] == b'LITE':
            at = n['end']
            if n.get('type') not in (0, 1, 2) or n['entry_end'] - at < 44:
                raise ValueError('a light does not read as the 800 layout')
            edits.append((at + 4, at + 4, struct.pack('<I', 0)))
            edits.append((at + 44, at + 44, _LIGHT_SHADOW))
    for g in m.geos:
        if g.get('uvas') is None or g.get('lod'):
            raise ValueError('a geoset does not read as the 800 layout')
        edits.append((g['lod_at'], g['lod_at'], bytes(84)))
    for mat in m.mats:
        for lay in mat['layers']:
            if lay['end'] - lay['off'] < 28 or any(t.start < lay['off'] + 28 for t in lay['tracks']):
                raise ValueError('a layer does not read as the 800 layout')
            edits.append((lay['off'] + 28, lay['off'] + 28, _layer_widening(lay['texture'])))
    vers = next(off for tag, _s, off in m.chunks if tag == b'VERS')
    edits.append((vers, vers + 4, struct.pack('<I', PORTRAIT_STAMP)))
    new = mdx_struct.edit(data, m, edits)
    back = mdx_struct.read(new)
    if back.version != PORTRAIT_STAMP or back.notes or _signature(back) != _signature(m):
        raise ValueError('the widened model does not read back as the original')
    if any(g.get('lod') is not True for g in back.geos) or len(back.geos) != len(m.geos):
        raise ValueError('the widened geosets do not read back')
    return new


def portrait_models(a):
    from doctor.fix import inflated_counts
    out = {}
    try:
        with unprotect.quiet():
            paths = inflated_counts._map_models(a)
    except Exception:
        return out
    for vals in paths.values():
        for v in vals:
            v = v.replace('/', '\\').strip()
            root, ext = os.path.splitext(v)
            if ext.lower() not in MODEL_EXTS and ext:
                continue
            for c in (root + '_Portrait.mdx', root + '.mdx', root + '.mdl'):
                try:
                    if a.find(c):
                        out.setdefault(c, v)
                        break
                except Exception:
                    pass
    return out


def check_model(data):
    return _check(data)[0]


def portrait_variant_at_risk(data, name=None):
    v = model_version(bytes(data))
    if v is None or v >= PORTRAIT_VERSION:
        return False
    stem = os.path.splitext(str(name or '').replace('/', '\\').rsplit('\\', 1)[-1].lower())[0]
    return camera_at_risk(data) or stem.endswith('_portrait')


def portrait_left(data, mode):
    data = bytes(data)
    chunks, err = mdxcheck.walk_path(data)
    if err or any(t == b'CAMS' for t, _s, _o in chunks):
        return True
    return mode != 'camera' and model_version(data) != PORTRAIT_STAMP


def fix_model(data, what=FIXES, name=None):
    mode = _portrait_mode(what)
    if mode in ('stamp', 'upgrade'):
        return _fix_variant(data, mode, name)
    if mode:
        if not camera_at_risk(data):
            return None, {'problems': [], 'fixed': []}
        new = drop_cameras(data)
        if new is None or camera_at_risk(new) or _structure(new):
            return None, {'problems': ['portrait_camera'], 'fixed': [], 'error': 'the camera could not be removed'}
        return new, {'problems': ['portrait_camera'], 'fixed': ['portrait_camera'], 'method': 'camera_removed',
                     'version': model_version(data), 'size_before': len(data), 'size_after': len(new)}
    problems, fixed = _check(data)
    details = {'problems': [p['code'] for p in problems], 'fixed': []}
    if fixed is None:
        return None, details
    out, info = fixed
    after = check_model(out)
    if after:
        details['error'] = 'the fix did not hold: %s' % ', '.join(p['code'] for p in after)
        return None, details
    details.update(
        {
            'fixed': ['matrix_groups'],
            'method': info['method'],
            'groups_before': list(info.get('before') or ()),
            'groups_after': list(info.get('after_diag') or ()),
            'size_before': len(data),
            'size_after': len(out),
        }
    )
    if info['method'] == 'nodes_merged':
        details.update(nodes_before=info['nodes_before'], nodes_after=info['nodes_after'])
    return out, details


def _fix_variant(data, mode, name=None):
    data = bytes(data)
    if not portrait_variant_at_risk(data, name):
        return None, {'problems': [], 'fixed': []}
    key = 'portrait_' + mode
    cam = camera_at_risk(data)
    problems = ['portrait_camera' if cam else 'portrait_version']
    try:
        new = drop_cameras(data) if cam else data
        if new is None:
            raise ValueError('the camera could not be removed')
        new = upgrade_layout(new) if mode == 'upgrade' else stamp_version(new)
    except ValueError as e:
        return None, {'problems': problems, 'fixed': [], 'error': str(e)}
    if portrait_left(new, mode) or _structure(new):
        return None, {'problems': problems, 'fixed': [], 'error': 'the model did not read back fixed'}
    return new, {'problems': problems, 'fixed': [key], 'method': {'stamp': 'camera_removed_stamped',
                                                                   'upgrade': 'camera_removed_upgraded'}[mode],
                 'version': model_version(data), 'size_before': len(data), 'size_after': len(new)}


def _names(a):
    with unprotect.quiet():
        if unprotect._listfile_status(a)['status'] == 'ok':
            return unprotect.listfile_names(a)
        return unprotect.map_names(a)


def _models(a, names, progress):
    models = [n for n in names if n.lower().endswith(MODEL_EXTS)]
    seen = set()
    for k, n in enumerate(models):
        if k % 100 == 0:
            progress('Checking models %d/%d' % (k, len(models)))
        r = None
        try:
            r = a.find_locale(n) if a.find(n) else None
        except Exception:
            r = None
        if r is None or r[1] in seen:
            continue
        seen.add(r[1])
        yield n, r[1], unprotect._read(a, n)


def _open(path):
    try:
        return unprotect._open(path), None
    except BaseException as e:
        if isinstance(e, KeyboardInterrupt):
            raise
        return None, 'The map does not open (%s).' % (str(e) or type(e).__name__)


LINT_EXTRA = {'uv_bad': ('mdx_uv_nan', 'a UV coordinate that is not a number or is absurdly far'),
              'track_bad': ('mdx_track_nan', 'an animation key (a value or a tangent) that is not a number')}


def _lint_extra(data):
    try:
        lint = mdxdeep.deep(data).get('lint') or {}
    except Exception:
        return []
    return [{'code': LINT_EXTRA[c][0], 'level': 'warning', 'text': '%d x %s' % (n, LINT_EXTRA[c][1]), 'count': n,
             'examples': []} for c, n in sorted(lint.items()) if c in LINT_EXTRA]


def scan(path, progress=None, sanity=False, version=None):
    p = progress or _nothing
    out = {'models': [], 'checked': 0, 'skipped': []}
    if sanity:
        from doctor.fix import mdx_sanity
        out['sanity'] = {'checked': 0, 'models': [], 'by_code': {}, 'skipped': []}
    p('Reading the map')
    a, err = _open(path)
    if a is None:
        out['error'] = err
        return out
    p('Finding the file names')
    portraits = dict((k.lower(), k) for k in portrait_models(a))
    out['portraits'] = []
    for name, _bi, data in _models(a, sorted(set(_names(a)) | set(portraits.values())), p):
        if data is None:
            out['skipped'].append({'file': name, 'reason': 'cannot be read'})
            continue
        try:
            problems = check_model(data)
        except ValueError as e:
            out['skipped'].append({'file': name, 'reason': str(e)})
            continue
        out['checked'] += 1
        if problems:
            out['models'].append({'file': name, 'problems': problems})
        if name.lower() in portraits and camera_at_risk(data):
            out['portraits'].append(name)
        if sanity:
            try:
                issues = mdx_sanity.check(data, version)
            except (ValueError, struct.error, IndexError) as e:
                out['sanity']['skipped'].append({'file': name, 'reason': str(e)[:80]})
                continue
            out['sanity']['checked'] += 1
            issues = issues + _lint_extra(data)
            if issues:
                out['sanity']['models'].append({'file': name, 'issues': issues})
                for code in sorted(set(i['code'] for i in issues)):
                    out['sanity']['by_code'].setdefault(code, []).append(name)
    p('Done')
    return out


def _part(path):
    base, ext = os.path.splitext(path)
    return base + '.part' + (ext or '.w3x')


def _same_except(a, b, blocks, slots):
    if b.h.offset != a.h.offset or b.sector_size != a.sector_size or b.hash_n_read != a.hash_n_read:
        return 'the archive header moved'
    for j in range(a.hash_n_read):
        if j not in slots and a.ht[j * 4:j * 4 + 4] != b.ht[j * 4:j * 4 + 4]:
            return 'hash table entry %d changed' % j
    vivos = unprotect._live_blocks(a)
    for i, blk in enumerate(a.blocks):
        if i in blocks or i not in vivos:
            continue
        if i >= len(b.blocks) or b.blocks[i] != blk:
            return 'block %d changed' % i
        if blk[3] & 0x80000000 and blk[1]:
            pos = (a.h.offset + blk[0]) & 0xFFFFFFFF
            end = min(pos + blk[1], len(a.d))
            if a.d[pos:end] != b.d[pos:end]:
                return 'the stored bytes of block %d changed' % i
    return ''


def fix(path_in, path_out, files=None, progress=None, what=FIXES, transform=None):
    p = progress or _nothing
    res = {'state': 'failed', 'fixed': [], 'not_fixed': [], 'checked': 0}
    if os.path.normcase(os.path.abspath(path_in)) == os.path.normcase(os.path.abspath(path_out)):
        res['error'] = 'The output must be a new file.'
        return res
    p('Reading the map')
    a, err = _open(path_in)
    if a is None:
        res['error'] = err
        return res
    p('Finding the file names')
    names = _names(a)
    wanted = None if files is None else dict((f.replace('/', '\\').lower(), f) for f in files)
    mode = _portrait_mode(what)
    if mode:
        pm = portrait_models(a)
        names = sorted(set(names) | set(pm))
        if wanted is None:
            wanted = dict((f.lower(), f) for f in pm)
            if not wanted:
                res['state'] = 'nothing_to_do'
                return res
    repl, blocks, slots, seen = [], set(), set(), set()
    for name, bi, data in _models(a, names, p):
        if wanted is not None and name.lower() not in wanted:
            continue
        seen.add(name.lower())
        if data is None:
            if wanted is not None:
                res['not_fixed'].append({'file': name, 'reason': 'cannot be read'})
            continue
        try:
            new, details = transform(name, data) if transform else fix_model(data, what, name)
        except ValueError as e:
            if wanted is not None:
                res['not_fixed'].append({'file': name, 'reason': str(e)})
            continue
        if new is None:
            if mode and files is None and not details['problems']:
                continue
            if details['problems'] or wanted is not None:
                res['not_fixed'].append({'file': name, 'reason': details.get('error') or (
                    'no fixer for: %s' % ', '.join(details['problems']) if details['problems'] else 'nothing to fix')})
            continue
        repl.append((name, new))
        blocks.add(bi)
        slots.update(e[0] for e in a.hash_entries(name))
        res['fixed'].append(dict(details, file=name))
    for f in sorted(set(wanted or ()) - seen):
        res['not_fixed'].append({'file': wanted[f], 'reason': 'not a model of this map'})
    if not repl:
        res['state'] = 'nothing_to_do'
        return res
    r = a.find('(attributes)')
    if r:
        blocks.add(r[1])
        slots.update(e[0] for e in a.hash_entries('(attributes)'))
    part = _part(path_out)
    try:
        p('Writing the new map')
        shutil.copyfile(path_in, part)
        no_room = []
        with unprotect.quiet():
            mpqadd.add_files(part, repl, log=_nothing, no_slot=no_room)
        if no_room:
            raise RuntimeError('no room in the hash table for %s' % ', '.join(no_room))
        p('Checking the new map')
        b, err = _open(part)
        if b is None:
            raise RuntimeError(err)
        for name, new in repl:
            left = False if transform else portrait_left(new, mode) if mode else check_model(new)
            if unprotect._read(b, name) != new or left:
                raise RuntimeError('%s was not read back fixed' % name)
        why = _same_except(a, b, blocks, slots)
        if why:
            raise RuntimeError(why)
        fixed = set(n.lower() for n, _d in repl)
        for n in names:
            if n.lower() in fixed:
                continue
            x = unprotect._read(a, n)
            if x is not None:
                if unprotect._read(b, n) != x:
                    raise RuntimeError('%s changed' % n)
                res['checked'] += 1
        del a, b
        os.replace(part, path_out)
        if os.path.getsize(path_out) > TETO:
            res['warning'] = (
                'The new map is over 512 MiB: the game does not list it. Run "Make the map smaller, losing nothing" on it.'
            )
    except Exception as e:
        a = b = None
        try:
            os.remove(part)
        except OSError:
            pass
        res['error'] = 'The check of the new map failed (%s).' % (str(e) or type(e).__name__)
        res['fixed'] = []
        return res
    res['state'] = 'done'
    p('Done')
    return res
