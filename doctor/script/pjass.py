# Runs pjass, the JASS syntax checker, over a script and the game scripts.
import os
import re
import subprocess
import sys


PJASS_NAME = 'pjass' if sys.platform.startswith('linux') else 'pjass.exe'
PJASS_NEXT_TO_MODULE = os.path.join(os.path.dirname(os.path.abspath(__file__)), PJASS_NAME)
PJASS_DEFAULT = PJASS_NEXT_TO_MODULE if os.path.isfile(PJASS_NEXT_TO_MODULE) else os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', '..', 'terceiros', 'ffmpeg', 'bin', 'pjass.exe'))
REF_30 = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ref', '3.0'))


def exe(pjass=None):
    return pjass or os.environ.get('PJASS') or PJASS_DEFAULT


_GAME_SCRIPTS_DIR = {}


def game_scripts_dir(ref_dir=None):
    ref_dir = ref_dir or REF_30
    if all(os.path.isfile(os.path.join(ref_dir, f)) for f in ('common.j', 'blizzard.j')):
        return ref_dir
    if 'folder' not in _GAME_SCRIPTS_DIR:
        scripts = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts'))
        import tempfile
        from doctor.triggers import triggerdata
        texts = dict((f, triggerdata.game_script(f)) for f in ('common.j', 'blizzard.j'))
        folder = None
        if all(texts.values()):
            folder = tempfile.mkdtemp(prefix='devos_game_scripts_')
            for f, t in texts.items():
                with open(os.path.join(folder, f), 'wb') as fh:
                    fh.write(t.encode('utf-8', 'surrogateescape'))
        _GAME_SCRIPTS_DIR['folder'] = folder
    return _GAME_SCRIPTS_DIR['folder']


def default_ref(root=None):
    return REF_30


def prepare(origin, fname, tmp):
    if not os.path.isfile(origin):
        return None, 0
    txt = open(origin, 'rb').read()
    if txt.startswith(b'\xef\xbb\xbf'):
        txt = txt[3:]
    txt = txt.replace(b'\r\n', b'\n').replace(b'\r', b'\n')
    if not os.path.isdir(tmp):
        os.makedirs(tmp)
    dst = os.path.join(tmp, fname)
    open(dst, 'wb').write(txt)
    return dst, txt.count(b'\n') + 1


def _opt(argv, fname, default_value=None):
    for a in argv:
        if a.startswith('--' + fname + '='):
            return a[len(fname) + 3:]
    return default_value


RX_WHERE = re.compile(r'^(?:[A-Za-z]:)?[^:]*:\d+:')
RX_TOTAL = re.compile(r'(?:failed with|Parse failed:) (\d+) errors?')


def compiles(paths, pjass=None, tmp=None):
    if tmp:
        paths = [os.path.relpath(c, tmp) if os.path.dirname(os.path.abspath(c)) == os.path.abspath(tmp) else c
                 for c in paths]
    r = subprocess.run([exe(pjass)] + list(paths), capture_output=True, text=True,
                       errors='replace', cwd=tmp, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    out = (r.stdout or '') + (r.stderr or '')
    line_list = [line for line in out.splitlines() if line.strip()]
    warnings = [line for line in line_list if 'warning' in line.lower()]
    error_list = [line for line in line_list if line not in warnings and
                  (RX_WHERE.match(line) or RX_TOTAL.search(line) or re.search(r'\b(error|Error)\b', line))]
    others = [line for line in line_list if line not in error_list and line not in warnings]
    totals = [int(m.group(1)) for m in (RX_TOTAL.search(line) for line in line_list) if m]
    for line in line_list:
        m = re.search(r'(\d+) errors? ignored', line)
        if m and int(m.group(1)) > 0:
            error_list.append(
                '%s error(s) IGNORED by the pragma //# +nosemanticerror: the game does not know the pragma and refuses'
                'the script (step 0d, common/kk/typecast.py, rewrites the functions)' % m.group(1)
            )
    return {
        'rc': r.returncode,
        'line_list': line_list,
        'error_list': error_list,
        'warnings': warnings,
        'others': others,
        'total': max(totals) if totals else None,
    }


def run_action(sources, pjass=None, tmp=None):
    paths = []
    line_counts = {}
    for orig, fname in sources:
        dst, n = prepare(orig, fname, tmp)
        if dst is None:
            return {'missing': orig, 'rc': 2, 'line_list': [], 'error_list': [], 'warnings': [], 'others': [],
                    'line_counts': line_counts}
        paths.append(dst)
        line_counts[fname] = (orig, n)
    res = compiles(paths, pjass=pjass, tmp=tmp)
    res.update({'missing': None, 'line_counts': line_counts})
    return res


def main(argv=None, root=None, ref=None, pjass=None, tmp=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    root = _opt(argv, 'root', root)
    ref = _opt(argv, 'ref', ref)
    pjass = _opt(argv, 'pjass', pjass)
    tmp = _opt(argv, 'tmp', tmp)
    if root is None:
        needs_work = [('ref', ref), ('tmp', tmp), ('j', _opt(argv, 'j'))]
        if '--conjunto' in argv:
            needs_work.append(('blizzard', _opt(argv, 'blizzard')))
        missing_items = [n for n, v in needs_work if v is None]
        if missing_items:
            print(__doc__)
            print('MISSING --raiz=<project> (or %s)' % ' '.join('--%s=' % n for n in missing_items))
            return 2
    if ref is None:
        ref = default_ref(root)
    if tmp is None:
        tmp = os.path.join(root, 'port', 'out', '_pjass')
    tmp = os.path.abspath(tmp)

    blizz_src = _opt(argv, 'blizzard')
    if not blizz_src:
        blizz_src = (os.path.join(root, 'scripts', 'blizzard.j') if '--conjunto' in argv
                     else os.path.join(ref, 'blizzard.j'))
    map_src = _opt(argv, 'j')
    if not map_src:
        map_src = os.path.join(root, 'scripts', 'war3map.j')
    sources = [
        (os.path.join(ref, 'common.j'), 'common.j'),
        (blizz_src, 'blizzard.j'),
        (map_src, 'war3map.j'),
    ]
    if '--conjunto' in argv and os.path.isfile(map_src):
        with open(map_src, 'rb') as fh:
            if b'//@@CAMADA_INLINE_' in fh.read():
                print('*** WARNING: %s ALREADY has the layer INSIDE (markers //@@CAMADA_INLINE_*).' % map_src)
                print('*** The G1 gate (--conjunto, with OUR blizzard.j) is against the PRE-injection:')
                print('***   --j=port/out/war3map_pre_injecao.j')
                print(
                    '*** G2 (the one that decides) is this file with the blizzard.j OF THE GAME (without --conjunto).'
                )
    paths = []
    line_counts = {}
    for orig, fname in sources:
        dst, n = prepare(orig, fname, tmp)
        if dst is None:
            print('MISSING: %s' % orig)
            return 2
        paths.append(dst)
        line_counts[fname] = (orig, n)
        print('%-11s %8d lines  %s' % (fname, n, orig))

    res = compiles(paths, pjass=pjass, tmp=tmp)

    def traduz(line):
        m = re.match(r'^([^()]+)\((\d+)\):\s*(.*)$', line) or re.match(r'^((?:[A-Za-z]:)?[^:]*):(\d+):\s*(.*)$', line)
        if not m:
            return line
        file_, ln, msg = m.group(1), int(m.group(2)), m.group(3)
        base = os.path.basename(file_)
        if base in line_counts:
            return '%s:%d (de %d): %s' % (base, ln, line_counts[base][1], msg)
        return line

    line_list, error_list, warnings, others = res['line_list'], res['error_list'], res['warnings'], res['others']
    print('\n---- pjass exit %d ----' % res['rc'])
    print('output lines: %d   errors: %d   warnings: %d   others: %d'
          % (len(line_list), len(error_list), len(warnings), len(others)))
    if others:
        print('\n-- summary --')
        for line in others[-12:]:
            print('  ' + traduz(line))
    if error_list:
        print('\n-- ERRORS (%d) --' % len(error_list))
        for line in error_list:
            print('  ' + traduz(line))
    if warnings:
        print('\n-- WARNINGS (first 60) --')
        for line in warnings[:60]:
            print('  ' + traduz(line))
    return 0 if (res['rc'] == 0 and not warnings and not error_list) else 1


if __name__ == '__main__':
    sys.exit(main())
