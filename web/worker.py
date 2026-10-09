# The Python side of the site's Web Worker: runs a job of the page and sends its events.
import json
import os
import subprocess
import sys
import time
import traceback

ENGINE = '/home/pyodide/engine'
FOLDERS = ('/maps', '/out')
PJASS = os.path.join(ENGINE, 'doctor', 'script', 'pjass.exe')
os.environ.setdefault('DOCTOR_CACHE', '/tmp/doctor_cache')
os.makedirs(os.environ['DOCTOR_CACHE'], exist_ok=True)


def run_pjass(cmd, kw):
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
    if isinstance(cmd, (list, tuple)) and cmd and os.path.basename(str(cmd[0])).lower() in ('pjass.exe', 'pjass'):
        return run_pjass(cmd, kw)
    return _subprocess_run(cmd, *args, **kw)


subprocess.run = subprocess_run


def windows_paths():
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

import DevosMapDoctor as G
from doctor.app import doctor_app as A


def files_now():
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
    except BaseException as e:
        final = {'type': 'error', 'message': '%s: %s' % (type(e).__name__, e) if str(e) else type(e).__name__,
                 'trace': traceback.format_exc(limit=8)}
    after = files_now()
    final['written'] = sorted(p for p, st in after.items() if before.get(p) != st)
    emit(final)


def zip_folder(folder, target):
    import zipfile
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, _dirs, names in os.walk(folder):
            for n in sorted(names):
                p = os.path.join(root, n)
                z.write(p, os.path.relpath(p, folder))
    return target


def zip_files(paths, target):
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
