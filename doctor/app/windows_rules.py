# On Linux, the Windows rules for paths (case, the backslash) in the process that runs a job.
import builtins
import io
import os
import subprocess
import sys


_APPLIED = [False]
_LISTING = {}
_os_stat, _os_listdir, _os_path_lexists, _posix_join = os.stat, os.listdir, os.path.lexists, os.path.join


def _real_names(folder):
    try:
        st = _os_stat(folder)
    except OSError:
        return {}
    got = _LISTING.get(folder)
    if got and got[0] == st.st_mtime_ns:
        return got[1]
    try:
        names = _os_listdir(folder)
    except OSError:
        return {}
    low = {}
    for n in sorted(names):
        low.setdefault(n.lower(), n)
    _LISTING[folder] = (st.st_mtime_ns, low)
    return low


def resolve(path):
    if isinstance(path, os.PathLike):
        path = os.fspath(path)
    if not isinstance(path, str) or not path:
        return path
    if path.startswith('/') and '\\' in path:
        path = path.replace('\\', '/')
    if _os_path_lexists(path):
        return path
    absolute = path.startswith('/')
    parts = [p for p in path.split('/') if p not in ('', '.')]
    cur = '/' if absolute else '.'
    for i, part in enumerate(parts):
        nxt = _posix_join(cur, part)
        if part == '..' or _os_path_lexists(nxt):
            cur = nxt
            continue
        real = _real_names(cur).get(part.lower())
        if real is None:
            return _posix_join(cur, *parts[i:]) if absolute else path
        cur = _posix_join(cur, real)
    return cur if absolute else (cur[2:] if cur.startswith('./') else cur)


def _ntfs_order(names):
    return sorted(names, key=lambda n: (n.upper() if isinstance(n, str) else n.upper(), n))


class _Scandir:
    def __init__(self, entries):
        self._entries = entries

    def __iter__(self):
        return iter(self._entries)

    def __next__(self):
        if not self._entries:
            raise StopIteration
        return self._entries.pop(0)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def close(self):
        self._entries = []


def _wrap(fn, *positions):
    def wrapped(*args, **kw):
        if kw.get('dir_fd') is not None or kw.get('src_dir_fd') is not None:
            return fn(*args, **kw)
        if positions:
            args = list(args)
            for k in positions:
                if k < len(args):
                    args[k] = resolve(args[k])
        for k in ('src', 'dst', 'path', 'file'):
            if k in kw:
                kw[k] = resolve(kw[k])
        return fn(*args, **kw)
    wrapped.__wrapped__ = fn
    return wrapped


def apply():
    if _APPLIED[0] or not sys.platform.startswith('linux'):
        return False
    _APPLIED[0] = True
    import ntpath
    import posixpath
    import types
    global _os_stat, _os_listdir, _os_path_lexists, _posix_join
    real_lstat = os.lstat

    def lexists(path):
        try:
            real_lstat(path)
        except (OSError, ValueError):
            return False
        return True
    _os_stat, _os_listdir, _os_path_lexists, _posix_join = os.stat, os.listdir, lexists, posixpath.join

    p = types.ModuleType('os.path')
    p.__dict__.update(posixpath.__dict__)
    p.basename, p.dirname, p.split, p.splitext = ntpath.basename, ntpath.dirname, ntpath.split, ntpath.splitext

    def join(a, *parts):
        allp = [os.fspath(a)] + [os.fspath(x) for x in parts]
        if any(isinstance(x, bytes) for x in allp):
            return posixpath.join(*allp)
        start = max((i for i, x in enumerate(allp) if x.startswith('/')), default=None)
        if start is not None:
            return posixpath.join(*allp[start:])
        return ntpath.join(*allp)
    p.join = join
    p.normcase = lambda s: s.lower() if isinstance(s, str) else os.fspath(s).lower()
    os.path = p
    sys.modules['os.path'] = p

    for name in ('stat', 'lstat', 'mkdir', 'rmdir', 'remove', 'unlink', 'utime', 'chmod', 'access', 'truncate',
                 'open', 'readlink'):
        if hasattr(os, name):
            setattr(os, name, _wrap(getattr(os, name), 0))
    for name in ('rename', 'replace', 'link', 'symlink'):
        if hasattr(os, name):
            setattr(os, name, _wrap(getattr(os, name), 0, 1))
    real_listdir, real_scandir = os.listdir, os.scandir

    def listdir(path='.'):
        return _ntfs_order(real_listdir(resolve(path) if not isinstance(path, int) else path))

    def scandir(path='.'):
        with real_scandir(resolve(path) if not isinstance(path, int) else path) as it:
            entries = list(it)
        return _Scandir(sorted(entries, key=lambda e: (e.name.upper(), e.name)))
    os.listdir, os.scandir = listdir, scandir
    builtins.open = io.open = _wrap(builtins.open, 0)

    real_popen_init = subprocess.Popen.__init__

    def popen_init(self, args, *a, **kw):
        if isinstance(args, (list, tuple)):
            args = [resolve(x) if isinstance(x, str) and x.startswith('/') else x for x in args]
        return real_popen_init(self, args, *a, **kw)
    subprocess.Popen.__init__ = popen_init
    return True
