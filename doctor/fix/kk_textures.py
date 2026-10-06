# Writes the textures the KK platform encrypted (BLX1) back as the plain BLP the game reads.
import os
import shutil

from doctor.fix import unprotect


MAGIC = b'BLX1'


def _nothing(*_a, **_k):
    pass


def _encrypted(a, names):
    out, seen = [], set()
    for n in names:
        if n.lower() in seen:
            continue
        seen.add(n.lower())
        d = unprotect._read(a, n)
        if d and d[:4] == MAGIC:
            out.append((n, d))
    return out


def scan(path):
    out = {'files': [], 'count': 0, 'error': None}
    from doctor.models import model_check
    a, err = model_check._open(path)
    if a is None:
        out['error'] = err
        return out
    out['files'] = [n for n, _d in _encrypted(a, model_check._names(a))]
    out['count'] = len(out['files'])
    return out


def fix(path_in, path_out, progress=None):
    p = progress or _nothing
    res = {'state': 'failed', 'written': [], 'failed': [], 'checked': 0}
    if os.path.abspath(path_in) == os.path.abspath(path_out):
        res['error'] = 'The output must be a new file.'
        return res
    from doctor.models import blpread
    from doctor.models import model_check
    from doctor.mpq import mpqadd
    p('Reading the map')
    a, err = model_check._open(path_in)
    if a is None:
        res['error'] = err
        return res
    names = model_check._names(a)
    found = _encrypted(a, names)
    if not found:
        res['state'] = 'nothing_to_do'
        return res
    p('Decrypting %d textures' % len(found))
    repl = []
    for name, data in found:
        try:
            plain = blpread.decrypt_blx(data)
            blpread.read_bytes(plain)
            repl.append((name, plain))
        except Exception as e:
            res['failed'].append([name, (str(e) or type(e).__name__)[:80]])
    if not repl:
        res['state'] = 'nothing_to_do'
        return res
    part = model_check._part(path_out)
    try:
        p('Writing the new map')
        shutil.copyfile(path_in, part)
        no_room = []
        with unprotect.quiet():
            mpqadd.add_files(part, repl, log=_nothing, no_slot=no_room, grow=list(names))
        if no_room:
            raise RuntimeError('no room in the hash table for %s' % ', '.join(no_room[:5]))
        p('Checking the new map')
        b, err = model_check._open(part)
        if b is None:
            raise RuntimeError(err)
        for name, data in repl:
            if unprotect._read(b, name) != data:
                raise RuntimeError('%s was not read back' % name)
        done = set(n.lower() for n, _d in repl)
        for n in names:
            if n.lower() in done:
                continue
            x = unprotect._read(a, n)
            if x is not None:
                if unprotect._read(b, n) != x:
                    raise RuntimeError('%s changed' % n)
                res['checked'] += 1
        del a, b
        os.replace(part, path_out)
    except Exception as e:
        try:
            os.remove(part)
        except OSError:
            pass
        res.update(error='The check of the new map failed (%s).' % (str(e) or type(e).__name__), written=[])
        return res
    res['state'] = 'done'
    res['written'] = [n for n, _d in repl]
    res['lines'] = ['%d textures encrypted by the KK platform were written back as plain BLP, so the game shows them.'
                    % len(repl)]
    if res['failed']:
        res['lines'].append('%d encrypted textures were left as they are: they did not decrypt.' % len(res['failed']))
    return res
