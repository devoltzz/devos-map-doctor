# The disk cache of the Doctor: the file names of a map, the game file tree and the parsed game tables, kept while the files do not change.
import hashlib
import os
import pickle
import time


PREFIX = 'devos_'
KEEP_DAYS = 30
SWEEP_ABOVE = 600
_SWEPT = []


def folder():
    p = os.environ.get('DOCTOR_CACHE')
    if not p:
        return None
    try:
        os.makedirs(p, exist_ok=True)
    except OSError:
        return None
    return p


def key(*parts):
    h = hashlib.sha1()
    for x in parts:
        if isinstance(x, bytes):
            h.update(b'b' + x)
        else:
            h.update(repr(x).encode('utf-8', 'surrogateescape'))
        h.update(b'\0')
    return h.hexdigest()[:24]


def file_key(path, sample=None):
    st = os.stat(path)
    return key(os.path.abspath(path).lower(), st.st_size, int(st.st_mtime), sample)


def _path(kind, k):
    base = folder()
    if base is None:
        return None
    return os.path.join(base, '%s%s_%s.pickle' % (PREFIX, kind, k))


def load(kind, k):
    p = _path(kind, k)
    if p is None:
        return None
    try:
        with open(p, 'rb') as f:
            value = pickle.load(f)
        try:
            os.utime(p, None)
        except OSError:
            pass
        return value
    except (OSError, EOFError, pickle.PickleError, AttributeError, ImportError, ValueError, TypeError):
        return None


def save(kind, k, value):
    p = _path(kind, k)
    if p is None:
        return False
    try:
        with open(p + '.new', 'wb') as f:
            pickle.dump(value, f, protocol=pickle.HIGHEST_PROTOCOL)
        os.replace(p + '.new', p)
    except (OSError, pickle.PickleError, TypeError, AttributeError):
        try:
            os.remove(p + '.new')
        except OSError:
            pass
        return False
    if not _SWEPT:
        _SWEPT.append(True)
        _sweep()
    return True


def _sweep():
    base = folder()
    if base is None:
        return
    try:
        names = [n for n in os.listdir(base) if n.startswith(PREFIX) and n.endswith('.pickle')]
        if len(names) <= SWEEP_ABOVE:
            return
        limit = time.time() - KEEP_DAYS * 86400
        for n in names:
            p = os.path.join(base, n)
            try:
                if os.stat(p).st_mtime < limit:
                    os.remove(p)
            except OSError:
                pass
    except OSError:
        pass
