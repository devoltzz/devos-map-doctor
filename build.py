# Builds dist/DevosMapDoctor.exe (one file, no console) with PyInstaller.
import glob
import os
import re
import shutil
import sys
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(ROOT, 'engine')
NAME = 'DevosMapDoctor'
EXCLUDE = ('PIL', 'cv2', 'lupa', 'matplotlib', 'pytest', 'setuptools', 'pip', 'unittest', 'pydoc_data')

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
    # Adds the licenses of the embedded Python and Tcl/Tk to the ones of the source tree.
    text = open(os.path.join(ROOT, 'THIRD_PARTY_NOTICES.md'), encoding='utf-8').read()
    parts = [text, '\n## Python %d.%d.%d\n\n' % sys.version_info[:3]]
    parts.append(open(os.path.join(sys.base_prefix, 'LICENSE.txt'), encoding='utf-8', errors='replace').read())
    for pattern, inner in (('libtcl*.zip', 'tcl_library/license.terms'), ('libtk*.zip', 'tk_library/license.terms')):
        for z in sorted(glob.glob(os.path.join(sys.base_prefix, 'tcl', pattern))):
            with zipfile.ZipFile(z) as f:
                parts.append('\n## %s\n\n' % inner.split('_')[0].upper() + f.read(inner).decode('utf-8', 'replace'))
            break
    return ''.join(parts)


def main():
    import PyInstaller.__main__
    version = app_version()
    numbers = (re.findall(r'\d+', version) + ['0'] * 4)[:4]
    work = os.path.join(ROOT, 'build')
    os.makedirs(work, exist_ok=True)
    version_file = os.path.join(work, 'version.txt')
    with open(version_file, 'w', encoding='utf-8') as f:
        f.write(VERSION_FILE.replace('{v}', ', '.join(numbers)).replace('{s}', version).replace('{n}', NAME))
    icon = os.path.join(ROOT, 'assets', 'devos_map_doctor.ico')
    args = [os.path.join(ROOT, 'DevosMapDoctor.py'), '--onefile', '--windowed', '--noconfirm', '--clean',
            '--name', NAME, '--icon', icon, '--add-data', icon + os.pathsep + '.', '--paths', ENGINE,
            '--version-file', version_file, '--workpath', work, '--distpath', os.path.join(ROOT, 'dist'),
            '--specpath', work]
    for module in sorted(f[:-3] for f in os.listdir(ENGINE) if f.endswith('.py')):
        args += ['--hidden-import', module]
    for data in sorted(f for f in os.listdir(ENGINE) if f.endswith('.j')):
        args += ['--add-data', os.path.join(ENGINE, data) + os.pathsep + '.']
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
