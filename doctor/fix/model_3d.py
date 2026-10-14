# The 3D preview of a model: the model and its textures decoded to RGBA for the page.
import os
import struct

from doctor.viewers import map_files


MODEL_MAX = 16 << 20
TOTAL_MAX = 48 << 20
SIDES = (512, 256, 128, 64)
VERSIONS = (800, 1100)


def _version(data):
    if data[:8] == b'MDLXVERS' and len(data) >= 16:
        return struct.unpack_from('<I', data, 12)[0]
    return None


def payload(path, name, max_side=SIDES[0]):
    out = {'name': name, 'size': None, 'version': None, 'drawable': False, 'reason': None, 'model': None,
           'textures': {}, 'outside': [], 'error': None}
    try:
        a, _notes = map_files._open(path)
        data, _bi = map_files._read(a, name)
        out['size'] = len(data)
        if map_files._content_kind(name, data)[0] != 'model':
            out['error'] = '%s is not a model' % name
            return out
        if len(data) > MODEL_MAX:
            out['reason'] = 'the model is larger than %d MB' % (MODEL_MAX >> 20)
            return out
        out['version'] = _version(data)
        if out['version'] is not None and not VERSIONS[0] <= out['version'] <= VERSIONS[1]:
            out['reason'] = ('model version %d: the 3D preview draws versions %d to %d'
                             % (out['version'], VERSIONS[0], VERSIONS[1]))
            return out
        out['drawable'] = True
        out['model'] = map_files._b64(data)
        listing = map_files.list_files(path)
        by_base = {}
        for f in listing.get('files') or []:
            by_base.setdefault(f['name'].rsplit('\\', 1)[-1].upper(), []).append(f['name'])
        found = []
        for ref in map_files.model_refs(data):
            if ref.lower().endswith(('.mdx', '.mdl')):
                continue
            got = map_files._resolve(a, ref, name, by_base)
            if got is None:
                out['outside'].append(ref)
                continue
            try:
                found.append((ref, map_files._read(a, got[0])[0], os.path.splitext(got[0])[1].lower()))
            except Exception as e:
                out['outside'].append('%s (%s)' % (ref, map_files._error(e)))
        for side in SIDES:
            total, textures, bad = 0, {}, []
            for ref, tex, ext in found:
                try:
                    im = map_files._image(tex, ext, 0, side, 'rgba')
                except Exception as e:
                    bad.append('%s (%s)' % (ref, map_files._error(e)))
                    continue
                total += im['width'] * im['height'] * 4
                textures[ref] = {'width': im['width'], 'height': im['height'], 'rgba': im['rgba']}
            if total <= TOTAL_MAX or side == SIDES[-1]:
                out['textures'] = textures
                out['outside'] += bad
                break
    except (Exception, SystemExit) as e:
        out['error'] = map_files._error(e)
    return out
