# Builds dist/DevosMapDoctor.exe (one file, no console) with PyInstaller.
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(ROOT, 'engine')
NAME = 'DevosMapDoctor'
EXCLUDE = ('cv2', 'lupa', 'matplotlib', 'pytest', 'setuptools', 'pip', 'unittest', 'pydoc_data', 'tkinter')
# the packages inside the exe, whose licenses go to THIRD_PARTY_NOTICES.txt
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
    # Adds the licenses of the embedded Python and of each bundled package to the ones of the source tree.
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
            '--specpath', work, '--add-data', os.path.join(ROOT, 'ui') + os.pathsep + 'ui']
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
