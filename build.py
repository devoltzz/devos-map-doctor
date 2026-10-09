# Builds the program with PyInstaller: the exe and its doctor.exe on Windows, one binary on Linux.
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(ROOT, 'doctor')
NAME = 'DevosMapDoctor'
LINUX = sys.platform.startswith('linux')
SYSTEM_LIBS = ('/lib/', '/usr/lib/', '/lib64/', '/usr/lib64/')
GUI_LIBS = re.compile(r'^lib(glib-2|gobject-2|gio-2|gmodule-2|gthread-2|girepository|mount|blkid|pcre|selinux|'
                      r'stdc\+\+|gcc_s|cairo|pixman|png16|freetype|fontconfig|harfbuzz|pango|gtk|gdk|atk|webkit|'
                      r'javascriptcore|soup|X|xcb|wayland|xkbcommon|epoxy|dbus)')
GI_MODULES = ('Gtk', 'Gdk', 'GLib', 'GObject', 'Gio', 'WebKit2', 'WebKit', 'Soup', 'JavaScriptCore', 'GdkPixbuf',
              'Pango', 'cairo', 'Atk', 'HarfBuzz', 'freetype2', 'GModule', 'xlib', 'GioUnix', 'GLibUnix',
              'Gst', 'GstBase', 'GstVideo', 'GstAudio', 'GstController', 'GstPbutils', 'GstApp')
EXCLUDE = ('cv2', 'matplotlib', 'pytest', 'setuptools', 'pip', 'unittest', 'pydoc_data', 'tkinter',
           'lupa.lua51', 'lupa.lua52', 'lupa.lua55', 'lupa.luajit20', 'lupa.luajit21')
LUA = ('lupa.lua53', 'lupa.lua54')
PACKAGES = ('numpy', 'pillow', 'pywebview', 'pythonnet', 'clr_loader', 'bottle', 'proxy_tools', 'cffi',
            'pycparser', 'typing_extensions', 'PyGObject', 'pycairo', 'zopfli', 'lupa', 'ctranslate2', 'sentencepiece')

VERSION_FILE = """VSVersionInfo(
  ffi=FixedFileInfo(filevers=({v}), prodvers=({v}), mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1,
                    subtype=0x0, date=(0, 0)),
  kids=[
    StringFileInfo([StringTable('040904B0', [
      StringStruct('FileDescription', "Devo's Map Doctor"),
      StringStruct('FileVersion', '{s}'),
      StringStruct('InternalName', '{n}'),
      StringStruct('OriginalFilename', '{n}.exe'),
      StringStruct('ProductName', "Devo's Map Doctor"),
      StringStruct('ProductVersion', '{s}')])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""


def app_version():
    text = open(os.path.join(ROOT, 'DevosMapDoctor.py'), encoding='utf-8').read()
    return re.search(r"^VERSION = '([^']+)'", text, re.M).group(1)


def notices():
    from importlib import metadata
    text = open(os.path.join(ROOT, 'THIRD_PARTY_NOTICES.md'), encoding='utf-8').read()
    parts = [text, '\n## Python %d.%d.%d\n\n' % sys.version_info[:3]]
    for p in (os.path.join(sys.base_prefix, 'LICENSE.txt'), os.path.join(os.path.dirname(os.__file__), 'LICENSE.txt'),
              '/usr/share/doc/python%d.%d/copyright' % sys.version_info[:2]):
        if os.path.isfile(p):
            parts.append(open(p, encoding='utf-8', errors='replace').read())
            break
    else:
        parts.append('Python Software Foundation License Version 2 (https://docs.python.org/3/license.html)\n')
    for name in PACKAGES:
        try:
            dist = metadata.distribution(name)
        except metadata.PackageNotFoundError:
            continue
        files = [f for f in dist.files or [] if re.search(r'(LICEN[CS]E|COPYING|NOTICE)', f.name, re.I)]
        licenses = '\n\n'.join(f.read_text(encoding='utf-8') or '' for f in files)
        declared = dist.metadata.get('License-Expression') or dist.metadata.get('License') or ''
        parts.append('\n## %s %s\n\n' % (dist.metadata['Name'], dist.version) + (licenses or declared) + '\n')
    if LINUX:
        parts.append(ZLIB_NG_LICENSE)
    return ''.join(parts)


ZLIB_NG_LICENSE = """
## zlib-ng 2.2.4 (https://github.com/zlib-ng/zlib-ng)

(C) 1995-2024 Jean-loup Gailly and Mark Adler

This software is provided 'as-is', without any express or implied warranty. In no event will the authors be held
liable for any damages arising from the use of this software.

Permission is granted to anyone to use this software for any purpose, including commercial applications, and to alter
it and redistribute it freely, subject to the following restrictions:

1. The origin of this software must not be misrepresented; you must not claim that you wrote the original software.
   If you use this software in a product, an acknowledgment in the product documentation would be appreciated but is
   not required.
2. Altered source versions must be plainly marked as such, and must not be misrepresented as being the original
   software.
3. This notice may not be removed or altered from any source distribution.
"""


def native_decryption():
    lib = os.path.join(ENGINE, 'mpq', 'mpqcrypt.so' if LINUX else 'mpqcrypt.dll')
    source = os.path.join(ENGINE, 'mpq', 'mpqcrypt.c')
    if os.path.isfile(lib) and os.path.getmtime(lib) >= os.path.getmtime(source):
        return
    import subprocess
    target = ['-target', 'x86_64-linux-gnu.2.17', '-fPIC'] if LINUX else ['-target', 'x86_64-windows-gnu']
    r = subprocess.run([sys.executable, '-m', 'ziglang', 'cc'] + target + ['-shared', '-O2', '-s', '-o', lib, source],
                       capture_output=True, text=True)
    if r.returncode:
        print(
            '%s could not be built (pip install ziglang): the program decrypts maps in Python' % os.path.basename(lib)
        )


def native_checks():
    lib = os.path.join(ENGINE, 'script', 'jass_checks.so' if LINUX else 'jass_checks.dll')
    crate = os.path.join(ROOT, 'native', 'jass_checks')
    newest = max(os.path.getmtime(os.path.join(crate, 'src', f)) for f in os.listdir(os.path.join(crate, 'src')))
    if os.path.isfile(lib) and os.path.getmtime(lib) >= newest:
        return
    cargo = shutil.which('cargo') or os.path.join(os.path.expanduser('~'), '.cargo', 'bin', 'cargo')
    import subprocess
    target = os.path.join(ROOT, 'build', 'cargo')
    try:
        r = subprocess.run([cargo, 'build', '--release', '--manifest-path', os.path.join(crate, 'Cargo.toml')],
                           capture_output=True, text=True, env=dict(os.environ, CARGO_TARGET_DIR=target))
    except OSError:
        r = None
    built = os.path.join(target, 'release', 'libjass_checks.so' if LINUX else 'jass_checks.dll')
    if r is not None and r.returncode == 0 and os.path.isfile(built):
        shutil.copyfile(built, lib)
    elif not os.path.isfile(lib):
        print('%s could not be built (https://rustup.rs): the program runs the script checks in Python'
              % os.path.basename(lib))


def launcher(work):
    out = os.path.join(work, 'doctor.exe')
    import subprocess

    r = subprocess.run(
        [
            sys.executable,
            '-m',
            'ziglang',
            'cc',
            '-target',
            'x86_64-windows-gnu',
            '-municode',
            '-O2',
            '-s',
            '-o',
            out,
            os.path.join(ROOT, 'launcher', 'doctor_launcher.c'),
        ],
        capture_output=True,
        text=True,
    )
    if r.returncode:
        print('doctor.exe could not be built (pip install ziglang): the exe has no command line launcher')
        return None
    return out


def linux_spec(args, work):
    from PyInstaller.utils.cliutils import makespec
    spec_args, skip = [], False
    for a in args:
        if skip:
            skip = False
        elif a in ('--workpath', '--distpath'):
            skip = True
        elif a not in ('--noconfirm', '--clean'):
            spec_args.append(a)
    sys.argv = ['pyi-makespec'] + spec_args
    makespec.run()
    spec = os.path.join(work, NAME + '.spec')
    with open(spec, encoding='utf-8') as f:
        text = f.read()
    cut = ('\nimport re as _re\n'
           'a.binaries = [b for b in a.binaries if not (str(b[1]).startswith(%r) and '
           '_re.match(%r, os.path.basename(str(b[0]))))]\n'
           'a.datas = [d for d in a.datas if not str(d[0]).startswith(\'gi_typelibs\')]\n'
           % (SYSTEM_LIBS, GUI_LIBS.pattern))
    text = text.replace('\npyz = PYZ(', cut + 'pyz = PYZ(', 1)
    if 'a.binaries = [b for b' not in text:
        raise SystemExit('the spec PyInstaller wrote has no PYZ line: cannot take the window libraries out')
    with open(spec, 'w', encoding='utf-8') as f:
        f.write('import os\n' + text)
    return spec


def main():
    import PyInstaller.__main__
    native_decryption()
    native_checks()
    version = app_version()
    numbers = (re.findall(r'\d+', version) + ['0'] * 4)[:4]
    work = os.path.join(ROOT, 'build', 'linux' if LINUX else 'windows')
    os.makedirs(work, exist_ok=True)
    icon = os.path.join(ROOT, 'assets', 'devos_map_doctor.ico')
    args = [os.path.join(ROOT, 'DevosMapDoctor.py'), '--onefile', '--noconfirm', '--clean', '--name', NAME,
            '--add-data', icon + os.pathsep + '.', '--workpath', work, '--distpath', os.path.join(ROOT, 'dist'),
            '--specpath', work, '--add-data', os.path.join(ROOT, 'ui') + os.pathsep + 'ui']
    if LINUX:
        from PIL import Image
        png = os.path.join(work, 'devos_map_doctor.png')
        with Image.open(icon) as im:
            im.save(png)
        args += ['--add-data', png + os.pathsep + '.']
    if not LINUX:
        version_file = os.path.join(work, 'version.txt')
        with open(version_file, 'w', encoding='utf-8') as f:
            f.write(VERSION_FILE.replace('{v}', ', '.join(numbers)).replace('{s}', version).replace('{n}', NAME))
        args += ['--windowed', '--icon', icon, '--version-file', version_file]
        doctor = launcher(work)
        if doctor:
            args += ['--add-binary', doctor + os.pathsep + '.']
    native = ('.so',) if LINUX else ('.exe', '.dll')
    other = ('.exe', '.dll') if LINUX else ('.so',)
    for folder, dirs, files in os.walk(ENGINE):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        rel = os.path.relpath(folder, ROOT)
        for f in sorted(files):
            if f.endswith('.py'):
                name = f[:-3]
                package = rel.replace(os.sep, '.')
                args += ['--hidden-import', package if name == '__init__' else package + '.' + name]
            elif f.endswith(native) or (LINUX and f == 'pjass'):
                args += ['--add-binary', os.path.join(folder, f) + os.pathsep + rel]
            elif f.endswith(other):
                continue
            elif not f.endswith('.pyc'):
                args += ['--add-data', os.path.join(folder, f) + os.pathsep + rel]
    pjass_name = 'pjass' if LINUX else 'pjass.exe'
    pjass = os.environ.get('PJASS')
    if pjass and os.path.isfile(pjass):
        args += ['--add-binary', pjass + os.pathsep + os.path.join('doctor', 'script')]
    elif not os.path.isfile(os.path.join(ENGINE, 'script', pjass_name)):
        print('%s not found (doctor/script/%s or PJASS): the program cannot port maps' % (pjass_name, pjass_name))
    for module in EXCLUDE:
        args += ['--exclude-module', module]
    for module in LUA:
        args += ['--hidden-import', module]
    if LINUX:
        for module in GI_MODULES:
            args += ['--exclude-module', 'gi.repository.' + module]
        args += ['--collect-submodules', 'gi']
        PyInstaller.__main__.run([linux_spec(args, work), '--noconfirm', '--clean', '--workpath', work,
                                  '--distpath', os.path.join(ROOT, 'dist')])
    else:
        PyInstaller.__main__.run(args)
    notices_name = 'THIRD_PARTY_NOTICES-linux.txt' if LINUX else 'THIRD_PARTY_NOTICES.txt'
    with open(os.path.join(ROOT, 'dist', notices_name), 'w', encoding='utf-8') as f:
        f.write(notices())
    index = os.path.join(ROOT, 'names.npz')
    if os.path.isfile(index):
        shutil.copyfile(index, os.path.join(ROOT, 'dist', 'names.npz'))
    else:
        print('names.npz not found: download it from the latest release to ship it with the exe')
    print('built', os.path.join(ROOT, 'dist', NAME + ('' if LINUX else '.exe')))


if __name__ == '__main__':
    main()
