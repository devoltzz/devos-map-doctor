# Finds the abilities locked on 3.0 by a requirement inherited from their base ability.
import os
import shutil

from doctor.fix import unprotect


OBJECT_FILES = ('war3map.w3u', 'war3map.w3t', 'war3map.w3b', 'war3map.w3d', 'war3map.w3a', 'war3map.w3h',
                'war3map.w3q')


def _nothing(*_a, **_k):
    pass


def _ids_of(data, name):
    from doctor.data import objects
    _ver, objs, _pos = objects.read_objects_bytes(data, objects.uses_levels(name), name, with_end=True)
    ids = set()
    for _t, orig, novo, _m in objs:
        ids.add(orig.lower())
        if novo.strip('\0'):
            ids.add(novo.lower())
    return ids


def _slk_ids(data):
    from doctor.data import slk
    try:
        return set(k.lower() for k in slk.parse_slk_bytes(data)[1])
    except Exception:
        return set()


def _defined_by_map(a):
    ids = set()
    for name in OBJECT_FILES:
        d = unprotect._read(a, name)
        if d:
            try:
                ids |= _ids_of(d, name)
            except Exception:
                pass
    up = unprotect._read(a, 'Units\\UpgradeData.slk')
    un = unprotect._read(a, 'Units\\UnitData.slk')
    for d in (up, un):
        if d:
            ids |= _slk_ids(d)
    return ids, up is not None, un is not None


def _predicate(a, base):
    ids, _up_slk, _unit_slk = _defined_by_map(a)

    def defined(x):
        return x.lower() in ids
    return defined


def _base(casc):
    from doctor.data import objects
    if casc is None:
        from doctor.mpq import import_lint
        casc = import_lint.game_storage()
    if casc is None:
        return None, None
    return objects.GameBase(casc=casc, balance=None), objects.GameBase(casc=casc, balance='custom_v1')


def scan(path, progress=None, casc=None):
    from doctor.data import objects
    p = progress or _nothing
    out = {'abilities': [], 'count': 0, 'new_count': 0, 'bases': {}, 'game': False}
    base, classic = _base(casc)
    if base is None:
        return out
    out['game'] = True
    try:
        a = unprotect._open(path)
    except BaseException as e:
        if isinstance(e, KeyboardInterrupt):
            raise
        out['error'] = 'The map does not open (%s).' % unprotect._error(e)
        return out
    w3a = unprotect._read(a, 'war3map.w3a')
    if not w3a:
        return out
    p('Reading the ability data')
    try:
        _ver, objs, _pos = objects.read_objects_bytes(w3a, True, 'war3map.w3a', with_end=True)
        found = objects.inherited_requirements(objs, base, _predicate(a, base), classic)
    except Exception as e:
        out['error'] = 'war3map.w3a does not read (%s).' % e
        return out
    for chave, orig, valor, missing, in_classic in found:
        out['abilities'].append({'id': chave, 'base': orig, 'requires': valor, 'missing': missing,
                                 'in_classic': in_classic})
        out['bases'][orig] = out['bases'].get(orig, 0) + 1
    out['count'] = len(found)
    out['new_count'] = sum(1 for x in found if x[4] is not True)
    return out


def fix(path_in, path_out, progress=None, casc=None, scope='new'):
    from doctor.data import objects
    p = progress or _nothing
    res = {'state': 'failed', 'fixed': 0, 'abilities': [], 'lines': []}
    if os.path.abspath(path_in) == os.path.abspath(path_out):
        res['error'] = 'The output must be a new file.'
        return res
    from doctor.models import model_check
    from doctor.mpq import mpqadd
    base, classic = _base(casc)
    if base is None:
        res['error'] = 'The game files are not installed here, and the requirements are read from them.'
        return res
    p('Reading the map')
    a, err = model_check._open(path_in)
    if a is None:
        res['error'] = err
        return res
    w3a = unprotect._read(a, 'war3map.w3a')
    if not w3a:
        res['state'] = 'nothing_to_do'
        return res
    try:
        ver, objs, pos = objects.read_objects_bytes(w3a, True, 'war3map.w3a', with_end=True)
        if objects.write_objects_bytes(ver, objs, True) + w3a[pos:] != w3a:
            res['error'] = 'war3map.w3a does not come back byte for byte through the writer, so it is left alone.'
            return res
        found = objects.inherited_requirements(objs, base, _predicate(a, base), classic)
    except Exception as e:
        res['error'] = 'war3map.w3a does not read (%s).' % e
        return res
    if scope != 'all':
        found = [x for x in found if x[4] is not True]
    if not found:
        res['state'] = 'nothing_to_do'
        return res
    meta = base.metadata('ability')
    lista = [(chave, orig, 'areq', 3, b'', None) for chave, orig, _v, _m, _c in found]
    new = objects.write_objects_bytes(ver, objects.add_modifications(objs, lista, meta), True) + w3a[pos:]
    ids = set(x[0] for x in found)
    part = model_check._part(path_out)
    try:
        ver2, objs2, pos2 = objects.read_objects_bytes(new, True, 'war3map.w3a', with_end=True)
        if len(objs2) != len(objs) or pos2 != len(new) - len(w3a) + pos:
            raise RuntimeError('the new war3map.w3a does not read to its end')
        changed = set()
        for o1, o2 in zip(objs, objs2):
            if o1 != o2:
                key = o1[2] if o1[2].strip('\0') else o1[1]
                changed.add(key)
                if o1[:3] != o2[:3] or o2[3][:len(o1[3])] != o1[3]:
                    raise RuntimeError('%s changed beyond the end of its modifications' % key)
        if changed != ids:
            raise RuntimeError('%d abilities differ, %d were listed' % (len(changed), len(ids)))
        left = objects.inherited_requirements(objs2, base, _predicate(a, base), classic)
        if [x for x in left if scope == 'all' or x[4] is not True]:
            raise RuntimeError('the rule still finds abilities after the fix')
        p('Writing the new map')
        shutil.copyfile(path_in, part)
        no_room = []
        with unprotect.quiet():
            mpqadd.add_files(part, [('war3map.w3a', new)], log=_nothing, no_slot=no_room)
        if no_room:
            raise RuntimeError('no room in the hash table for war3map.w3a')
        b, err = model_check._open(part)
        if b is None:
            raise RuntimeError(err)
        if unprotect._read(b, 'war3map.w3a') != new:
            raise RuntimeError('war3map.w3a was not read back fixed')
        for n in model_check._names(a):
            if n.lower() == 'war3map.w3a':
                continue
            x = unprotect._read(a, n)
            if x is not None and unprotect._read(b, n) != x:
                raise RuntimeError('%s changed' % n)
        del a, b
        os.replace(part, path_out)
    except Exception as e:
        try:
            os.remove(part)
        except OSError:
            pass
        res['error'] = 'The check of the new map failed (%s).' % (str(e) or type(e).__name__)
        return res
    res.update(state='done', fixed=len(found), abilities=sorted(ids))
    res['lines'] = ['%d abilities got an empty requirement, so 3.0 no longer locks them for a tech the map does not '
                    'have (%s).' % (len(found), ', '.join('%s %d' % kv for kv in sorted(
                        _count([x[1] for x in found]).items())[:6]))]
    return res


def _count(items):
    out = {}
    for x in items:
        out[x] = out.get(x, 0) + 1
    return out
