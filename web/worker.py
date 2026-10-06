"""worker.py - the Python side of the site's Web Worker (1.6): the job of the page runs in `doctor_app.run_job`, the
same function the exe's worker process runs, and each event goes to the page through `emit_js` (a JSON string)
instead of a line on stdout. Loaded by `worker.js` after the engine (`engine.zip`) is unpacked into ENGINE, and by
`medicao/mede.mjs` (the measurement runs this same glue). pjass runs as pjass.wasm (`run_pjass`).

The paths the page sees are the worker's: the map under /maps (a link to the file the user picked, read without a
copy), what the user picked under /in, the outputs next to the map or under /out.
"""
import json
import os
import subprocess
import sys
import time
import traceback

ENGINE = '/home/pyodide/engine'
FOLDERS = ('/maps', '/out')
# where the engine looks for pjass.exe (next to its module): an empty stand-in, so the engine finds "the program"; the
# call itself goes to pjass.wasm (`run_pjass`)
PJASS = os.path.join(ENGINE, 'doctor', 'script', 'pjass.exe')
os.environ.setdefault('DOCTOR_CACHE', '/tmp/doctor_cache')
os.makedirs(os.environ['DOCTOR_CACHE'], exist_ok=True)


def run_pjass(cmd, kw):
    """pjass run as pjass.wasm (`runPjass` of worker.js, the WASI of wasi_mini.js): the same arguments, the files the
    arguments name read from this file system, the output as `subprocess.run` gives it."""
    import js
    from pyodide.ffi import to_js
    cwd = kw.get('cwd') or os.getcwd()
    args = [str(a) for a in cmd[1:]]
    files = {}
    for a in args:
        p = a if os.path.isabs(a) else os.path.join(cwd, a)
        if os.path.isfile(p):
            with open(p, 'rb') as f:
                files[a.lstrip('/')] = f.read()
    r = js.runPjass(to_js(args), to_js(files, dict_converter=js.Object.fromEntries))
    out, err = str(r.stdout), str(r.stderr)
    if not (kw.get('text') or kw.get('encoding') or kw.get('errors') or kw.get('universal_newlines')):
        out, err = out.encode('utf-8'), err.encode('utf-8')
    return subprocess.CompletedProcess(list(cmd), int(r.code), out, err)


_subprocess_run = subprocess.run


def subprocess_run(cmd, *args, **kw):
    """`subprocess.run` in the browser: pjass goes to pjass.wasm; anything else fails as without the program."""
    if isinstance(cmd, (list, tuple)) and cmd and os.path.basename(str(cmd[0])).lower() in ('pjass.exe', 'pjass'):
        return run_pjass(cmd, kw)
    return _subprocess_run(cmd, *args, **kw)


subprocess.run = subprocess_run


def windows_paths():
    """`os.path` with the Windows rules the engine was written for (its other side, for the file system, is
    fs_windows.js): a name from the MPQ is `Folder\\Sub\\File.ext`, and on Windows `os.path` is ntpath, which splits on
    `\\` and `/` alike -- posixpath took `ReplaceableTextures\\CommandButtons\\BTNCage` for one name and the `DISBTN`
    beside it was never found (the name recovery lost files the exe keeps). The splits (`basename`, `dirname`, `split`,
    `splitext`) are ntpath's; `join` is ntpath's for a relative name (a name from the MPQ) and posix for a path of this
    file system (it starts with `/`); the rest (`abspath`, `isabs`, `exists`...) stays posix."""
    import ntpath
    import posixpath
    import types
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
    os.path = p
    sys.modules['os.path'] = p


windows_paths()
if not os.path.isfile(PJASS):
    open(PJASS, 'wb').close()
sys.path.insert(0, ENGINE)
os.chdir(ENGINE)
sys.argv = [os.path.join(ENGINE, 'DevosMapDoctor.py')]

import DevosMapDoctor as G  # noqa: E402
from doctor.app import doctor_app as A  # noqa: E402


def files_now():
    """{path: (size, mtime)} of the files the jobs write (next to the map, under /out)."""
    seen = {}
    for top in FOLDERS:
        for root, _dirs, names in os.walk(top):
            for n in names:
                p = os.path.join(root, n)
                try:
                    st = os.stat(p)
                except OSError:
                    continue
                seen[p] = (st.st_size, st.st_mtime)
    return seen


def run(job_json, emit_js):
    """One job of the page: its events (progress, then result or error) through `emit_js`, each with the job id, and
    the files the job wrote or changed in the final event (`written`), so the page knows where to fetch them."""
    job = json.loads(job_json)
    ident = job.pop('id')
    before = files_now()

    def emit(event):
        event = dict(event, job=ident)
        emit_js(json.dumps(A._jsonable(event)))

    t0 = time.time()
    try:
        result = A.run_job(job, emit, G)
        final = {'type': 'result', 'data': result, 'seconds': round(time.time() - t0, 1)}
    except BaseException as e:  # noqa: BLE001 -- the page must hear the job end
        final = {'type': 'error', 'message': '%s: %s' % (type(e).__name__, e) if str(e) else type(e).__name__,
                 'trace': traceback.format_exc(limit=8)}
    after = files_now()
    final['written'] = sorted(p for p, st in after.items() if before.get(p) != st)
    emit(final)


def zip_folder(folder, target):
    """The folder (what "Extract selected" wrote) as one zip the page can download."""
    import zipfile
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, _dirs, names in os.walk(folder):
            for n in sorted(names):
                p = os.path.join(root, n)
                z.write(p, os.path.relpath(p, folder))
    return target


def zip_files(paths, target):
    """Several files the jobs wrote (the queue of maps in a browser that cannot write a folder) as one zip, each by its
    name; stored, not compressed again (a map is compressed already)."""
    import zipfile
    seen = set()
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_STORED) as z:
        for p in paths:
            name = os.path.basename(p)
            if name in seen or not os.path.isfile(p):
                continue
            seen.add(name)
            z.write(p, name)
    return target
