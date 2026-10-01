# Finds the imported models that crash or hang the game, and fixes the ones that can be fixed.
import os
import shutil
import struct

import unprotect
import mdxcheck
import mdxdeep
import mdxgroups
import mdxnodes
import mpqadd


MODEL_EXTS = ('.mdx', '.mdl')
MAGICS = mdxcheck.MAGICS
TETO = 512 << 20


def _nothing(*_a, **_k):
    pass


def _structure(data):
    chunks, err = mdxcheck.walk(data)
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
    return len(mdxdeep.deep(out).get('geo_issues', ())) <= len(mdxdeep.deep(data).get('geo_issues', ()))


def _fixed(data):
    try:
        out, info = mdxgroups.fix_matrix_groups(data, so_dedup=True)
        if not info.get('above_do_limit') and _holds(data, out):
            info['method'] = 'merged'
            return out, info
        if mdxdeep.deep(data).get('max_objid', -1) >= 256:
            fewer, ninfo = mdxnodes.reduce_nodes(data, 250)
            if 'err' not in ninfo:
                out, info = mdxgroups.fix_matrix_groups(fewer, so_dedup=True)
                if not info.get('above_do_limit') and _holds(data, out):
                    info.update(method='nodes_merged', nodes_before=ninfo.get('nodes_before'),
                                nodes_after=ninfo.get('nodes_after'))
                    return out, info
        out, info = mdxgroups.fix_matrix_groups(data)
        if _holds(data, out):
            info['method'] = 'split'
            return out, info
    except Exception:
        pass
    return None


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
    fixed = _fixed(data)
    worst = max(over, key=lambda x: x[1])
    return [{'code': 'matrix_groups', 'fixable': fixed is not None, 'geosets': [i for i, _n in over],
             'groups': worst[1], 'text': 'Geoset %d has %d matrix groups (255 at most): the game hangs when the mouse '
                                         'is over this model.' % worst}], fixed


def check_model(data):
    return _check(data)[0]


def fix_model(data):
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


def scan(path, progress=None):
    p = progress or _nothing
    out = {'models': [], 'checked': 0, 'skipped': []}
    p('Reading the map')
    a, err = _open(path)
    if a is None:
        out['error'] = err
        return out
    p('Finding the file names')
    for name, _bi, data in _models(a, _names(a), p):
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
    for i, blk in enumerate(a.blocks):
        if i in blocks:
            continue
        if i >= len(b.blocks) or b.blocks[i] != blk:
            return 'block %d changed' % i
        if blk[3] & 0x80000000 and blk[1]:
            pos = (a.h.offset + blk[0]) & 0xFFFFFFFF
            end = min(pos + blk[1], len(a.d))
            if a.d[pos:end] != b.d[pos:end]:
                return 'the stored bytes of block %d changed' % i
    return ''


def fix(path_in, path_out, files=None, progress=None):
    p = progress or _nothing
    res = {'state': 'failed', 'fixed': [], 'not_fixed': [], 'checked': 0}
    if os.path.abspath(path_in) == os.path.abspath(path_out):
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
            new, details = fix_model(data)
        except ValueError as e:
            if wanted is not None:
                res['not_fixed'].append({'file': name, 'reason': str(e)})
            continue
        if new is None:
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
    part = _part(path_out)
    try:
        p('Writing the new map')
        shutil.copyfile(path_in, part)
        sem_slot = []
        with unprotect.quiet():
            mpqadd.add_files(part, repl, log=_nothing, sem_slot=sem_slot)
        if sem_slot:
            raise RuntimeError('no room in the hash table for %s' % ', '.join(sem_slot))
        p('Checking the new map')
        b, err = _open(part)
        if b is None:
            raise RuntimeError(err)
        for name, new in repl:
            if unprotect._read(b, name) != new or check_model(new):
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
            res['warning'] = 'The new map is over 512 MiB: the game does not list it. Shrink it.'
    except Exception as e:
        if os.path.exists(part):
            os.remove(part)
        res['error'] = 'The check of the new map failed (%s).' % (str(e) or type(e).__name__)
        res['fixed'] = []
        return res
    res['state'] = 'done'
    p('Done')
    return res
