# Finds the abilities and items locked on 3.0 by a requirement inherited from their base object.
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


CLASSIC_ITEM_REQUIRES = frozenset(('ocor', 'ofir', 'oli2', 'olig', 'oven', 'pams', 'pclr', 'phea', 'pman', 'shea',
                                   'skul', 'spre', 'ssan', 'stwp', 'tcas', 'tgrh', 'tsct', 'wneg'))


def _items_found(objs, base, defined):
    tab = base.table('item')
    found = []
    for tabela, orig, novo, mods in objs:
        if any(mm[0] == 'ureq' for mm in mods):
            continue
        valor = str(tab.get(orig, {}).get('requires') or '').strip()
        missing = [x.strip() for x in valor.split(',') if x.strip() not in ('', '_', '-') and not defined(x.strip())]
        if missing:
            found.append((novo if novo.strip('\0') else orig, orig, valor, missing, orig in CLASSIC_ITEM_REQUIRES,
                          bool(tabela)))
    return found


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
    out = {'abilities': [], 'count': 0, 'new_count': 0, 'bases': {}, 'items': [], 'item_count': 0, 'item_new_count': 0,
           'item_bases': {}, 'game': False}
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
    w3t = unprotect._read(a, 'war3map.w3t')
    if not w3a and not w3t:
        return out
    defined = _predicate(a, base)
    errors = []
    if w3a:
        p('Reading the ability data')
        try:
            _ver, objs, _pos = objects.read_objects_bytes(w3a, True, 'war3map.w3a', with_end=True)
            found = objects.inherited_requirements(objs, base, defined, classic)
        except Exception as e:
            errors.append('war3map.w3a does not read (%s).' % e)
            found = []
        for chave, orig, valor, missing, in_classic in found:
            out['abilities'].append({'id': chave, 'base': orig, 'requires': valor, 'missing': missing,
                                     'in_classic': in_classic})
            out['bases'][orig] = out['bases'].get(orig, 0) + 1
        out['count'] = len(found)
        out['new_count'] = sum(1 for x in found if x[4] is not True)
    if w3t:
        p('Reading the item data')
        try:
            _ver, objs, _pos = objects.read_objects_bytes(w3t, False, 'war3map.w3t', with_end=True)
            found = _items_found(objs, base, defined)
        except Exception as e:
            errors.append('war3map.w3t does not read (%s).' % e)
            found = []
        for chave, orig, valor, missing, in_classic, custom in found:
            out['items'].append({'id': chave, 'base': orig, 'requires': valor, 'missing': missing,
                                 'in_classic': in_classic, 'custom': custom})
            out['item_bases'][orig] = out['item_bases'].get(orig, 0) + 1
        out['item_count'] = len(found)
        out['item_new_count'] = sum(1 for x in found if x[4] is not True)
    if errors:
        out['error'] = ' '.join(errors)
    return out


def _found(name, objs, base, defined, classic):
    from doctor.data import objects
    if name == 'war3map.w3a':
        return objects.inherited_requirements(objs, base, defined, classic)
    return _items_found(objs, base, defined)


_FILES = (('war3map.w3a', True, 'areq', 'ability', 'abilities'), ('war3map.w3t', False, 'ureq', 'item', 'items'))


def fix(path_in, path_out, progress=None, casc=None, scope='new'):
    from doctor.data import objects
    p = progress or _nothing
    res = {'state': 'failed', 'fixed': 0, 'abilities': [], 'items': [], 'ability_fixed': 0, 'item_fixed': 0,
           'lines': []}
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
    defined = _predicate(a, base)
    plan = []
    for name, nivel, field, especie, noun in _FILES:
        data = unprotect._read(a, name)
        if not data:
            continue
        try:
            ver, objs, pos = objects.read_objects_bytes(data, nivel, name, with_end=True)
            found = _found(name, objs, base, defined, classic)
        except Exception as e:
            res['error'] = '%s does not read (%s).' % (name, e)
            return res
        if scope != 'all':
            found = [x for x in found if x[4] is not True]
        if not found:
            continue
        if objects.write_objects_bytes(ver, objs, nivel) + data[pos:] != data:
            res['error'] = '%s does not come back byte for byte through the writer, so it is left alone.' % name
            return res
        lista = [(x[0], x[1], field, 3, b'', None) for x in found]
        new = objects.write_objects_bytes(ver, objects.add_modifications(objs, lista, base.metadata(especie)),
                                          nivel) + data[pos:]
        plan.append((name, nivel, noun, data, objs, pos, found, new))
    if not plan:
        res['state'] = 'nothing_to_do'
        return res
    part = model_check._part(path_out)
    try:
        for name, nivel, noun, data, objs, pos, found, new in plan:
            ids = set(x[0] for x in found)
            _ver2, objs2, pos2 = objects.read_objects_bytes(new, nivel, name, with_end=True)
            if len(objs2) != len(objs) or pos2 != len(new) - len(data) + pos:
                raise RuntimeError('the new %s does not read to its end' % name)
            changed = set()
            for o1, o2 in zip(objs, objs2):
                if o1 != o2:
                    key = o1[2] if o1[2].strip('\0') else o1[1]
                    changed.add(key)
                    if o1[:3] != o2[:3] or o2[3][:len(o1[3])] != o1[3]:
                        raise RuntimeError('%s changed beyond the end of its modifications' % key)
            if changed != ids:
                raise RuntimeError('%d %s differ, %d were listed' % (len(changed), noun, len(ids)))
            left = _found(name, objs2, base, defined, classic)
            if [x for x in left if scope == 'all' or x[4] is not True]:
                raise RuntimeError('the rule still finds %s after the fix' % noun)
        p('Writing the new map')
        shutil.copyfile(path_in, part)
        no_room = []
        with unprotect.quiet():
            mpqadd.add_files(part, [(x[0], x[7]) for x in plan], log=_nothing, no_slot=no_room)
        if no_room:
            raise RuntimeError('no room in the hash table for %s' % ', '.join(str(x) for x in no_room))
        b, err = model_check._open(part)
        if b is None:
            raise RuntimeError(err)
        written = set()
        for x in plan:
            if unprotect._read(b, x[0]) != x[7]:
                raise RuntimeError('%s was not read back fixed' % x[0])
            written.add(x[0].lower())
        for n in model_check._names(a):
            if n.lower() in written:
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
    res['state'] = 'done'
    for name, _nivel, noun, _data, _objs, _pos, found, _new in plan:
        bases = ', '.join('%s %d' % kv for kv in sorted(_count([x[1] for x in found]).items())[:6])
        res[noun] = sorted(set(x[0] for x in found))
        if noun == 'abilities':
            res['ability_fixed'] = len(found)
            res['lines'].append('%d abilities got an empty requirement, so 3.0 no longer locks them for a tech the map '
                                'does not have (%s).' % (len(found), bases))
        else:
            res['item_fixed'] = len(found)
            res['lines'].append('%d items got an empty requirement, so a shop on 3.0 no longer asks for a building or '
                                'tech the map does not have (%s).' % (len(found), bases))
    res['fixed'] = res['ability_fixed'] + res['item_fixed']
    return res


def _count(items):
    out = {}
    for x in items:
        out[x] = out.get(x, 0) + 1
    return out
