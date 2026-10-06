# Builds dist/DevosMapDoctor.exe (one file, no console) with PyInstaller.
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(ROOT, 'doctor')
NAME = 'DevosMapDoctor'
EXCLUDE = ('cv2', 'lupa', 'matplotlib', 'pytest', 'setuptools', 'pip', 'unittest', 'pydoc_data', 'tkinter')
PACKAGES = ('numpy', 'pillow', 'pywebview', 'pythonnet', 'clr_loader', 'bottle', 'proxy_tools', 'cffi',
            'pycparser', 'typing_extensions')

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
    parts.append(open(os.path.join(sys.base_prefix, 'LICENSE.txt'), encoding='utf-8', errors='replace').read())
    for name in PACKAGES:
        try:
            dist = metadata.distribution(name)
        except metadata.PackageNotFoundError:
            continue
        files = [f for f in dist.files or [] if re.search(r'(LICEN[CS]E|COPYING|NOTICE)', f.name, re.I)]
        licenses = '\n\n'.join(f.read_text(encoding='utf-8') or '' for f in files)
        declared = dist.metadata.get('License-Expression') or dist.metadata.get('License') or ''
        parts.append('\n## %s %s\n\n' % (dist.metadata['Name'], dist.version) + (licenses or declared) + '\n')
    return ''.join(parts)


def native_decryption():
    # the MPQ's hot loops in native code (doctor/mpq/mpqcrypt.c: the decryption, the key search, the sound sectors):
    # built with zig from pip when missing or older than the source (a DLL from an earlier version lacks what the new
    # source added); without it the exe does it all in Python, the same bytes
    dll = os.path.join(ENGINE, 'mpq', 'mpqcrypt.dll')
    source = os.path.join(ENGINE, 'mpq', 'mpqcrypt.c')
    if os.path.isfile(dll) and os.path.getmtime(dll) >= os.path.getmtime(source):
        return
    import subprocess
    r = subprocess.run([sys.executable, '-m', 'ziglang', 'cc', '-target', 'x86_64-windows-gnu', '-shared', '-O2', '-s',
                        '-o', dll, source], capture_output=True, text=True)
    if r.returncode:
        print('mpqcrypt.dll could not be built (pip install ziglang): the exe decrypts maps in Python')


def main():
    import PyInstaller.__main__
    native_decryption()
    version = app_version()
    numbers = (re.findall(r'\d+', version) + ['0'] * 4)[:4]
    work = os.path.join(ROOT, 'build')
    os.makedirs(work, exist_ok=True)
    version_file = os.path.join(work, 'version.txt')
    with open(version_file, 'w', encoding='utf-8') as f:
        f.write(VERSION_FILE.replace('{v}', ', '.join(numbers)).replace('{s}', version).replace('{n}', NAME))
    icon = os.path.join(ROOT, 'assets', 'devos_map_doctor.ico')
    args = [os.path.join(ROOT, 'DevosMapDoctor.py'), '--onefile', '--windowed', '--noconfirm', '--clean',
            '--name', NAME, '--icon', icon, '--add-data', icon + os.pathsep + '.',
            '--version-file', version_file, '--workpath', work, '--distpath', os.path.join(ROOT, 'dist'),
            '--specpath', work, '--add-data', os.path.join(ROOT, 'ui') + os.pathsep + 'ui']
    for folder, dirs, files in os.walk(ENGINE):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        rel = os.path.relpath(folder, ROOT)
        for f in sorted(files):
            if f.endswith('.py'):
                name = f[:-3]
                package = rel.replace(os.sep, '.')
                args += ['--hidden-import', package if name == '__init__' else package + '.' + name]
            elif f.endswith(('.exe', '.dll')):
                args += ['--add-binary', os.path.join(folder, f) + os.pathsep + rel]
            elif not f.endswith('.pyc'):
                args += ['--add-data', os.path.join(folder, f) + os.pathsep + rel]
    pjass = os.environ.get('PJASS')
    if pjass and os.path.isfile(pjass):
        args += ['--add-binary', pjass + os.pathsep + os.path.join('doctor', 'script')]
    elif not os.path.isfile(os.path.join(ENGINE, 'script', 'pjass.exe')):
        print('pjass.exe not found (doctor/script/pjass.exe or PJASS): the exe cannot port maps')
    for module in EXCLUDE:
        args += ['--exclude-module', module]
    PyInstaller.__main__.run(args)
    with open(os.path.join(ROOT, 'dist', 'THIRD_PARTY_NOTICES.txt'), 'w', encoding='utf-8') as f:
        f.write(notices())
    index = os.path.join(ROOT, 'names.npz')
    if os.path.isfile(index):
        shutil.copyfile(index, os.path.join(ROOT, 'dist', 'names.npz'))
    else:
        print('names.npz not found: download it from the latest release to ship it with the exe')
    print('built', os.path.join(ROOT, 'dist', NAME + '.exe'))


if __name__ == '__main__':
    main()
