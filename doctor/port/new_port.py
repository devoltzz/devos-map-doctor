# The file names every map has.
import io
import os
import subprocess
import sys


HERE = os.path.dirname(os.path.abspath(__file__))
COMMON = os.path.dirname(HERE)
ROOT = os.path.dirname(COMMON)
KNOWN_NAMES = (
    'war3map.j', 'war3map.w3i', 'war3map.wts', 'war3map.w3a', 'war3map.w3t',
    'war3map.w3u', 'war3map.w3d', 'war3map.w3b', 'war3map.w3h', 'war3map.w3q',
    'war3map.w3e', 'war3map.wpm', 'war3map.doo', 'war3map.shd', 'war3map.mmp',
    'war3map.imp', 'war3mapMisc.txt', 'war3mapSkin.txt', 'war3mapMap.blp',
    'war3mapPreview.tga',
    'units\\unitdata.slk', 'units\\unitbalance.slk', 'units\\unitui.slk',
    'units\\unitweapons.slk', 'units\\unitabilities.slk', 'units\\abilitydata.slk',
    'units\\itemdata.slk', 'units\\itemfunc.txt', 'units\\itemstrings.txt',
    'units\\campaignunitstrings.txt', 'units\\campaignabilitystrings.txt',
    'units\\humanunitstrings.txt', 'units\\humanabilitystrings.txt',
    'units\\nightelfunitstrings.txt', 'units\\nightelfabilitystrings.txt',
    'units\\orcbunitstrings.txt', 'units\\orcunitstrings.txt',
    'units\\undeadunitstrings.txt', 'units\\undeadabilitystrings.txt',
    'units\\neutralunitstrings.txt', 'units\\neutralabilitystrings.txt',
    'units\\commandstrings.txt', 'units\\commonabilitystrings.txt',
)

FAMILIES = [
    ('JN*',        r'\bJN[A-Z]\w*'),
    ('DzAPI (Dz*)', r'\bDz[A-Z]\w*'),
    ('M16 (EX*)',  r'\bEX[A-Z]\w*'),
    ('YDWE',       r'\bYDWE\w*'),
    ('JAPI',       r'\bjapi\w*|\bJapi\w*'),
    ('Reforged (Blz*)', r'\bBlz[A-Z]\w*'),
]


def run(cmd, cwd=None):
    env = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                       encoding='utf-8', errors='replace', env=env)
    return r.returncode, (r.stdout or '') + (r.stderr or '')


def read_data(p, method='r'):
    with io.open(p, encoding='utf-8', errors='replace', newline='') as fh:
        return fh.read()


def write_text(p, body_text):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with io.open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(body_text)


def diagnostico(map_path, tmp_dest):
    d = {'file_name': os.path.basename(map_path), 'bytes': os.path.getsize(map_path)}

    rc, output = run([sys.executable, os.path.join(HERE, 'mpqdoctor.py'), map_path])
    d['mpqdoctor_ok'] = (rc == 0)
    d['is_malformed'] = 'MALFORMED: no' not in output
    d['header'] = ''
    d['decoys'] = []
    for ln in output.splitlines():
        if ln.strip().startswith('header'):
            d['header'] = ln.split(':', 1)[-1].strip()
        if 'isca' in ln.lower():
            d['decoys'].append(ln.strip())
    d['mpqdoctor_output'] = output

    os.makedirs(tmp_dest, exist_ok=True)
    run([sys.executable, os.path.join(HERE, 'mpqextract.py'), map_path, tmp_dest, '(listfile)'])
    p_listfile = os.path.join(tmp_dest, '(listfile)')
    name_list = []
    d['listfile_util'] = False
    if os.path.exists(p_listfile):
        content = read_data(p_listfile)
        name_list = [line.strip() for line in content.splitlines() if line.strip()]
        if len(content) < 200 and len(name_list) < 5:
            d['listfile'] = 'fake (%d bytes, %d junk lines)' % (len(content), len(name_list))
            name_list = []
        else:
            d['listfile'] = 'real (%d names)' % len(name_list)
            d['listfile_util'] = True
    else:
        d['listfile'] = 'absent'
    d['listfile_entries'] = name_list
    return d

