"""build_site.py - the Devo's Map Doctor site (the Doctor in the browser), built from a release of the program.

  python web/build_site.py --engine=<release folder> --out=<folder> [--ui=<page folder>] [--pjass=<pjass.wasm>]
         [--data=<game data pack>] [--index=<names.npz>] [--pyodide=<node_modules/pyodide>] [--wheels=<cache folder>]
         [--repository=owner/name] [--zip=<site zip>] [--mpqcrypt=<mpqcrypt.wasm>]

What goes in <out>:
  index.html, app.css, app.js...   the program's page (`ui/`), with config.js (the version, the repository) and the
                                   bridge (ponte.js) before app.js, the web app manifest and the icons
  ponte.js, worker.js, worker.py   the bridge from the page to the Web Workers and their Python side
  fila.js                          the queue of several maps
  wasi_mini.js, fs_windows.js      the WASI that runs pjass.wasm, and the Windows path rules
  about.html, about.js             About and privacy
  engine.zip                       the engine: DevosMapDoctor.py and doctor/ (no pjass.exe)
  pjass.wasm                       pjass as WebAssembly (build_pjass.py)
  mpqcrypt.js, mpqcrypt.wasm       the MPQ decryption in native code (--mpqcrypt, or built from the engine's
                                   doctor/mpq/mpqcrypt.c with zig)
  pyodide/                         Pyodide from npm and the numpy and Pillow wheels (downloaded once into --wheels and
                                   checked against the sha256 of pyodide-lock.json): the site loads nothing from a CDN
  sw.js                            the service worker (offline): the version and the file list written in
  data/game_data.zip               the game data pack (casc_wc3's `pacote`), only with --data: the host serves it
                                   from a folder of its own (deploy/), it is never in the zip
  names.npz                        the file name index, only with --index
--zip writes the site (without data/) as one zip and its .sha256, for the release.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
WEB_FILES = ('ponte.js', 'fila.js', 'worker.js', 'worker.py', 'wasi_mini.js', 'fs_windows.js', 'mpqcrypt.js',
             'about.html', 'about.js')
PACKAGES = ('numpy', 'pillow')
CORE = ('pyodide.js', 'pyodide.mjs', 'pyodide.asm.mjs', 'pyodide.asm.wasm', 'python_stdlib.zip', 'pyodide-lock.json')
# a map above this needs more memory than a browser gives a page (measured: 238 MiB takes 1.5 GiB of the 4 GiB a
# WebAssembly memory can have)
SIZE_LIMIT = 450 * 1024 * 1024
THEME = '#121418'
# what the service worker does not keep at install: the game data (the host's own folder) and the index (62 MB, only
# when the page asks for it)
OPTIONAL = ('data/game_data.zip',)
NOT_CACHED = ('sw.js', 'names.npz')


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def engine_version(engine):
    with open(os.path.join(engine, 'DevosMapDoctor.py'), encoding='utf-8') as f:
        m = re.search(r"^VERSION = '([^']+)'", f.read(), re.M)
    if not m:
        raise SystemExit('build_site: no VERSION in %s' % os.path.join(engine, 'DevosMapDoctor.py'))
    return m.group(1)


def engine_zip(engine, target):
    n = 0
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as z:
        z.write(os.path.join(engine, 'DevosMapDoctor.py'), 'DevosMapDoctor.py')
        for root, dirs, files in os.walk(os.path.join(engine, 'doctor')):
            dirs[:] = sorted(d for d in dirs if d not in ('__pycache__', 'cache'))
            for f in sorted(files):
                if f.endswith(('.exe', '.pyc', '.dll')):
                    continue
                p = os.path.join(root, f)
                z.write(p, os.path.relpath(p, engine).replace(os.sep, '/'))
                n += 1
    return n + 1


def pyodide(source, target, wheels):
    """Pyodide's core and the wheels of PACKAGES (and what they depend on). -> the Pyodide version."""
    if not os.path.isfile(os.path.join(source, 'pyodide-lock.json')):
        raise SystemExit('build_site: no Pyodide in %s (npm install in web/)' % source)
    with open(os.path.join(source, 'package.json'), encoding='utf-8') as f:
        version = json.load(f)['version']
    with open(os.path.join(source, 'pyodide-lock.json'), encoding='utf-8') as f:
        lock = json.load(f)['packages']
    os.makedirs(target, exist_ok=True)
    for n in CORE:
        shutil.copyfile(os.path.join(source, n), os.path.join(target, n))
    os.makedirs(wheels, exist_ok=True)
    todo, done = list(PACKAGES), set()
    while todo:
        name = todo.pop()
        if name in done:
            continue
        done.add(name)
        p = lock[name]
        todo += p.get('depends', [])
        local = os.path.join(wheels, p['file_name'])
        if not os.path.isfile(local) or sha256(local) != p['sha256']:
            url = 'https://cdn.jsdelivr.net/pyodide/v%s/full/%s' % (version, p['file_name'])
            print('downloading %s' % url)
            with urllib.request.urlopen(url, timeout=120) as r, open(local + '.part', 'wb') as f:
                shutil.copyfileobj(r, f)
            if sha256(local + '.part') != p['sha256']:
                os.remove(local + '.part')
                raise SystemExit('build_site: %s does not match the sha256 of the lock' % p['file_name'])
            os.replace(local + '.part', local)
        shutil.copyfile(local, os.path.join(target, p['file_name']))
    return version


def icons(engine, out):
    """icon-192.png and icon-256.png from the program's icon (assets/devos_map_doctor.ico, 256 px at most)."""
    from PIL import Image
    ico = os.path.join(engine, 'assets', 'devos_map_doctor.ico')
    if not os.path.isfile(ico):
        raise SystemExit('build_site: no %s' % ico)
    img = Image.open(ico)
    img.size = max(img.info.get('sizes') or [img.size])
    img = img.convert('RGBA')
    img.save(os.path.join(out, 'icon-256.png'))
    img.resize((192, 192), Image.LANCZOS).save(os.path.join(out, 'icon-192.png'))


def page(ui, out, config):
    for n in os.listdir(ui):
        p = os.path.join(ui, n)
        if os.path.isfile(p) and n != 'index.html':
            shutil.copyfile(p, os.path.join(out, n))
        elif os.path.isdir(p):
            shutil.copytree(p, os.path.join(out, n), dirs_exist_ok=True)
    with open(os.path.join(ui, 'index.html'), encoding='utf-8') as f:
        html = f.read()
    script, css = '<script src="app.js"></script>', '<link rel="stylesheet" href="app.css">'
    if html.count(script) != 1 or html.count(css) != 1:
        raise SystemExit('build_site: the page changed (no single %s or %s)' % (script, css))
    html = html.replace(script, '<script src="config.js"></script>\n<script src="ponte.js"></script>\n' + script +
                        '\n<script src="fila.js"></script>')
    html = html.replace(css, css + '\n<link rel="manifest" href="manifest.webmanifest">\n<link rel="icon" '
                        'href="icon-192.png">\n<meta name="theme-color" content="%s">' % THEME)
    with open(os.path.join(out, 'index.html'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(html)
    with open(os.path.join(out, 'config.js'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('window.DOCTOR_WEB = %s;\n' % json.dumps(config, indent=1))
    for n in WEB_FILES:
        shutil.copyfile(os.path.join(HERE, n), os.path.join(out, n))
    manifest = {'name': "Devo's Map Doctor", 'short_name': 'Map Doctor', 'start_url': './', 'scope': './',
                'display': 'standalone', 'background_color': THEME, 'theme_color': THEME,
                'description': 'Fix, open in the World Editor and port Warcraft III maps, in the browser.',
                'icons': [{'src': 'icon-192.png', 'sizes': '192x192', 'type': 'image/png'},
                          {'src': 'icon-256.png', 'sizes': '256x256', 'type': 'image/png'}]}
    with open(os.path.join(out, 'manifest.webmanifest'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(manifest, f, indent=1)


def service_worker(out, version):
    """sw.js with the version (the engine's and a hash of every file) and the list of what it keeps at install."""
    files = []
    h = hashlib.sha256()
    for root, dirs, names in os.walk(out):
        dirs.sort()
        for n in sorted(names):
            rel = os.path.relpath(os.path.join(root, n), out).replace(os.sep, '/')
            if rel in NOT_CACHED or rel in OPTIONAL:
                continue
            files.append(rel)
            h.update(rel.encode() + b'\0' + sha256(os.path.join(root, n)).encode())
    with open(os.path.join(HERE, 'sw.js'), encoding='utf-8') as f:
        text = f.read()
    tag = '%s-%s' % (version, h.hexdigest()[:10])
    text = text.replace('__VERSION__', tag).replace('__ASSETS__', json.dumps(['./'] + files))
    text = text.replace('__OPTIONAL__', json.dumps(list(OPTIONAL)))
    with open(os.path.join(out, 'sw.js'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)
    return tag


def site_zip(out, target):
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, dirs, names in os.walk(out):
            dirs[:] = sorted(d for d in dirs if os.path.relpath(os.path.join(root, d), out) != 'data')
            for n in sorted(names):
                p = os.path.join(root, n)
                z.write(p, os.path.relpath(p, out).replace(os.sep, '/'))
    with open(target + '.sha256', 'w', encoding='utf-8', newline='\n') as f:
        f.write('%s  %s\n' % (sha256(target), os.path.basename(target)))


def native_decryption(engine, out, wasm=None):
    """mpqcrypt.wasm: the given one, or built from the engine's doctor/mpq/mpqcrypt.c with zig from pip (the MPQ
    decryption in native code, ~200x the Python loop; without it the engine decrypts in Python, the same bytes)."""
    target = os.path.join(out, 'mpqcrypt.wasm')
    if wasm:
        shutil.copyfile(wasm, target)
        return
    source = os.path.join(engine, 'doctor', 'mpq', 'mpqcrypt.c')
    if not os.path.isfile(source):
        print('build_site: no doctor/mpq/mpqcrypt.c: the site decrypts maps in Python (slow on encrypted maps)')
        return
    r = subprocess.run([sys.executable, '-m', 'ziglang', 'cc', '-target', 'wasm32-freestanding', '-nostdlib',
                        '-Wl,--no-entry', '-O2', '-s', '-o', target, source], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit('build_site: zig could not build mpqcrypt.wasm\n%s%s' % (r.stdout, r.stderr))


def build(engine, out, ui=None, pjass=None, data=None, index=None, pyodide_dir=None, wheels=None, repository=None,
          zip_path=None, mpqcrypt=None):
    """-> {'version', 'cache', 'files', 'pyodide'}."""
    engine = os.path.abspath(engine)
    if not os.path.isfile(os.path.join(engine, 'DevosMapDoctor.py')):
        raise SystemExit('build_site: %s is not a release (no DevosMapDoctor.py)' % engine)
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(out)
    version = engine_version(engine)
    config = {'version': version, 'repository': repository, 'sizeLimit': SIZE_LIMIT}
    page(ui or os.path.join(engine, 'ui'), out, config)
    icons(engine, out)
    n_engine = engine_zip(engine, os.path.join(out, 'engine.zip'))
    if not pjass or not os.path.isfile(pjass):
        raise SystemExit('build_site: no pjass.wasm (build_pjass.py): the port, the GUI triggers and the cheat packs '
                         'need it')
    shutil.copyfile(pjass, os.path.join(out, 'pjass.wasm'))
    native_decryption(engine, out, mpqcrypt)
    py_version = pyodide(pyodide_dir or os.path.join(HERE, 'node_modules', 'pyodide'), os.path.join(out, 'pyodide'),
                         wheels or os.path.join(HERE, 'wheels'))
    if data:
        if not os.path.isfile(os.path.join(data, 'doctor_game_data.json')):
            raise SystemExit('build_site: %s is not a game data pack' % data)
        os.makedirs(os.path.join(out, 'data'), exist_ok=True)
        with zipfile.ZipFile(os.path.join(out, 'data', 'game_data.zip'), 'w', zipfile.ZIP_DEFLATED) as z:
            for root, dirs, names in os.walk(data):
                dirs.sort()
                for n in sorted(names):
                    p = os.path.join(root, n)
                    z.write(p, os.path.relpath(p, data).replace(os.sep, '/'))
    if index:
        shutil.copyfile(index, os.path.join(out, 'names.npz'))
    tag = service_worker(out, version)
    if zip_path:
        site_zip(out, zip_path)
    return {'version': version, 'cache': tag, 'engine_files': n_engine, 'pyodide': py_version}


def main(argv):
    op = dict((a[2:].split('=', 1) + [''])[:2] for a in argv if a.startswith('--'))
    if not op.get('engine') or not op.get('out'):
        print(__doc__)
        return 2
    r = build(op['engine'], os.path.abspath(op['out']), op.get('ui'), op.get('pjass'), op.get('data'), op.get('index'),
              op.get('pyodide'), op.get('wheels'), op.get('repository'), op.get('zip'), op.get('mpqcrypt'))
    print('site %s (cache %s, Pyodide %s, %d engine files) -> %s' % (r['version'], r['cache'], r['pyodide'],
                                                                    r['engine_files'], op['out']))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
