# Finds the levelled object fields whose data pointer differs between levels, and aligns them.
import os
import shutil
import struct

from doctor.fix import unprotect


FILES = ('war3map.w3a', 'war3map.w3d', 'war3map.w3q', 'war3mapSkin.w3a', 'war3mapSkin.w3d', 'war3mapSkin.w3q')
VERSIONS = (2, 3)


def _nothing(*_a, **_k):
    pass


def walk(data):
    ver = struct.unpack_from('<I', data, 0)[0]
    if ver not in VERSIONS:
        raise ValueError('object file version %d' % ver)
    p = 4
    for _table in range(2):
        n = struct.unpack_from('<I', data, p)[0]
        p += 4
        for _ in range(n):
            old, new = data[p:p + 4].decode('latin-1'), data[p + 4:p + 8].decode('latin-1')
            ident = new if new.strip('\0') else old
            p += 8
            sets = 1
            if ver >= 3:
                sets = struct.unpack_from('<I', data, p)[0]
                p += 4
            for _s in range(sets):
                if ver >= 3:
                    p += 4
                nm = struct.unpack_from('<I', data, p)[0]
                p += 4
                for _m in range(nm):
                    field = data[p:p + 4].decode('latin-1')
                    vt = struct.unpack_from('<I', data, p + 4)[0]
                    level, pointer = struct.unpack_from('<II', data, p + 8)
                    yield ident, field, level, pointer, p + 12
                    p += 16
                    if vt == 3:
                        p = data.index(b'\0', p) + 1
                    elif vt in (0, 1, 2):
                        p += 4
                    else:
                        raise ValueError('value type %d in field %r of %r' % (vt, field, ident))
                    p += 4
    if p > len(data) or data[p:].strip(b'\0'):
        raise ValueError('the file does not close (%d of %d bytes)' % (p, len(data)))


def _fields(data):
    fields = {}
    for ident, field, level, pointer, off in walk(data):
        fields.setdefault((ident, field), []).append((level, pointer, off))
    out = []
    for (ident, field), rows in fields.items():
        ptrs = set(p for _l, p, _o in rows)
        if len(ptrs) < 2:
            continue
        nonzero = ptrs - {0}
        levels = [l for l, _p, _o in rows]
        good = next(iter(nonzero)) if len(nonzero) == 1 and len(set(levels)) == len(levels) else None
        out.append((ident, field, rows, good))
    return out


def scan_bytes(data):
    return [{'object': ident, 'field': field, 'pointers': [[l, p] for l, p, _o in rows], 'fix': good}
            for ident, field, rows, good in _fields(data)]


def fix_bytes(data):
    out = bytearray(data)
    n = 0
    for _ident, _field, rows, good in _fields(data):
        if good is None:
            continue
        for _l, p, off in rows:
            if p == 0:
                struct.pack_into('<I', out, off, good)
                n += 1
    return bytes(out), n


def _read(a, name):
    return unprotect._read(a, name)


def scan(path):
    out = {'files': {}, 'fixable': 0, 'ambiguous': 0}
    try:
        a = unprotect._open(path)
    except BaseException as e:
        if isinstance(e, KeyboardInterrupt):
            raise
        out['error'] = 'The map does not open (%s).' % unprotect._error(e)
        return out
    for name in FILES:
        d = _read(a, name)
        if not d:
            continue
        try:
            found = scan_bytes(d)
        except (ValueError, struct.error):
            continue
        if found:
            out['files'][name] = found
            out['fixable'] += sum(1 for x in found if x['fix'] is not None)
            out['ambiguous'] += sum(1 for x in found if x['fix'] is None)
    return out


def fix(path_in, path_out, progress=None):
    p = progress or _nothing
    res = {'state': 'failed', 'fixed': 0, 'files': [], 'checked': 0}
    if os.path.abspath(path_in) == os.path.abspath(path_out):
        res['error'] = 'The output must be a new file.'
        return res
    from doctor.mpq import mpqadd
    from doctor.models import model_check
    p('Reading the map')
    a, err = model_check._open(path_in)
    if a is None:
        res['error'] = err
        return res
    repl = []
    for name in FILES:
        d = _read(a, name)
        if not d:
            continue
        try:
            new, n = fix_bytes(d)
        except (ValueError, struct.error):
            continue
        if n:
            repl.append((name, new))
            res['fixed'] += n
            res['files'].append({'file': name, 'pointers': n})
    if not repl:
        res['state'] = 'nothing_to_do'
        return res
    names = model_check._names(a)
    part = model_check._part(path_out)
    try:
        p('Writing the new map')
        shutil.copyfile(path_in, part)
        no_room = []
        with unprotect.quiet():
            mpqadd.add_files(part, repl, log=_nothing, no_slot=no_room)
        if no_room:
            raise RuntimeError('no room in the hash table for %s' % ', '.join(no_room))
        b, err = model_check._open(part)
        if b is None:
            raise RuntimeError(err)
        for name, new in repl:
            back = _read(b, name)
            if back != new or fix_bytes(back)[1]:
                raise RuntimeError('%s was not read back fixed' % name)
        done = set(n.lower() for n, _d in repl)
        for n in names:
            if n.lower() in done:
                continue
            x = _read(a, n)
            if x is not None:
                if _read(b, n) != x:
                    raise RuntimeError('%s changed' % n)
                res['checked'] += 1
        del a, b
        os.replace(part, path_out)
    except Exception as e:
        try:
            os.remove(part)
        except OSError:
            pass
        res.update(error='The check of the new map failed (%s).' % (str(e) or type(e).__name__), fixed=0, files=[])
        return res
    res['state'] = 'done'
    res['lines'] = ['%s: %d data pointers set to the one their other levels use.' % (f['file'], f['pointers'])
                    for f in res['files']]
    return res
