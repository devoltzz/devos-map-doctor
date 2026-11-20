# Finds and removes the map files that replace the game's own icons, textures and models.
import collections
import os


IMAGE_EXTS = ('.blp', '.tga', '.dds')
TEMPLATE = ('.mdx', '.mdl')
BULK = 50
ICON_FOLDERS = ('replaceabletextures\\commandbuttons', 'replaceabletextures\\passivebuttons')


def candidates(game_path):
    fname = game_path.split(':')[-1].replace('/', '\\')
    base, ext = os.path.splitext(fname)
    ext = ext.lower()
    if ext in IMAGE_EXTS:
        return [base + e for e in IMAGE_EXTS]
    if ext in TEMPLATE:
        return [base + e for e in TEMPLATE]
    return []


def shadowed(map_path, casc=None):
    from doctor.mpq import mpqread
    if casc is None:
        from doctor.data import casc_wc3
        casc = casc_wc3.CascWC3()
    a = mpqread.Archive(map_path) if isinstance(map_path, str) else map_path
    seen = set()
    matches = []
    for k in casc.file_set:
        for cn in candidates(k):
            hash_key = cn.lower()
            if hash_key in seen:
                continue
            seen.add(hash_key)
            try:
                if a.find(cn) is not None:
                    matches.append(cn)
            except Exception:
                pass
    return sorted(matches, key=str.lower)


def count_by_folder(name_list):
    return collections.Counter('\\'.join(n.split('\\')[:-1]) or '.' for n in name_list).most_common()


def remove(map_path, name_list):
    if not name_list:
        return 0
    from doctor.mpq import mpqadd
    mpqadd.add_files(map_path, [], list(name_list), log=lambda *a: None)
    return len(name_list)


def _nothing(*_a, **_k):
    pass


def classe(fname):
    n = fname.replace('/', '\\').lstrip('\\').lower()
    if n.startswith('ui\\'):
        return 'ui'
    if n.startswith(ICON_FOLDERS):
        return 'icons'
    return 'other'


def _game_forms(fname):
    base, ext = os.path.splitext(fname.replace('/', '\\').lstrip('\\').lower())
    if ext in IMAGE_EXTS:
        return [base + e for e in IMAGE_EXTS]
    if ext in TEMPLATE:
        return [base + e for e in TEMPLATE]
    return []


PICTURE_SIDE = 32
PICTURE_LIMIT = 10.0


def _picture(data_bytes, fname):
    import io
    from PIL import Image
    try:
        if data_bytes[:4] == b'DDS ' or os.path.splitext(fname)[1].lower() in ('.dds', '.tga'):
            im = Image.open(io.BytesIO(data_bytes))
            im.load()
        else:
            from doctor.models import blpread
            im, _info = blpread.read_bytes(data_bytes)
        im = im.convert('RGBA').resize((PICTURE_SIDE, PICTURE_SIDE))
    except Exception:
        return None
    px = []
    for r, gr, b, al in im.getdata():
        px.append((r * al // 255, gr * al // 255, b * al // 255, al))
    return px


def picture_difference(mine, game, map_file_name='', game_file_name=''):
    a = _picture(mine, map_file_name)
    b = _picture(game, game_file_name)
    if a is None or b is None:
        return None
    total = 0
    for p, q in zip(a, b):
        total += abs(p[0] - q[0]) + abs(p[1] - q[1]) + abs(p[2] - q[2]) + abs(p[3] - q[3])
    return total / (4.0 * len(a))


def own_art(a, name_list, g):
    from doctor.fix import unprotect
    have = g.names()
    own = []
    for n in name_list:
        if os.path.splitext(n)[1].lower() not in IMAGE_EXTS or classe(n) == 'ui':
            continue
        mine = unprotect._read(a, n)
        if not mine:
            continue
        game = None
        for f in _game_forms(n):
            if f in have:
                game = g.read(f)
                if game:
                    break
        if not game:
            continue
        d = picture_difference(mine, game, n, f)
        if d is not None and d > PICTURE_LIMIT:
            own.append(n)
    return own


def kept_line(name_list):
    return '%d images stayed: they are the map\'s own art under a game file\'s name (their picture is not the ' \
           'game\'s) (%s).' % (len(name_list), ', '.join('%s %d' % (f, n) for f, n in count_by_folder(name_list)[:4]))


def _all_modes(fname, g):
    try:
        from doctor.fix import gfx_modes
        lay = getattr(g, '_gfx_layers', None)
        if lay is None:
            lay = g._gfx_layers = gfx_modes.Layers(g.casc)
        return len(lay.where(fname)) == len(gfx_modes.MODES)
    except Exception:
        return True


def scan(map_path, progress=None, casc=None):
    from doctor.fix import unprotect
    from doctor.fix import game_paths
    from doctor.models import model_check
    p = progress or _nothing
    out = {'files': [], 'counts': {'ui': 0, 'icons': 0, 'other': 0, 'identical': 0}, 'folders': [], 'severity': None,
           'game': False, 'identical': [], 'different': [], 'unknown': []}
    g = game_paths.open_game(casc)
    if g is None:
        return out
    out['game'] = True
    a, err = model_check._open(map_path) if isinstance(map_path, str) else (map_path, None)
    if a is None:
        out['error'] = err
        return out
    p('Finding the file names')
    have = g.names()
    for n in model_check._names(a):
        if any(c in have for c in _game_forms(n)) and unprotect._valid_for_game(a, n) is not None:
            out['files'].append(n)
            out['counts'][classe(n)] += 1
    out['files'].sort(key=str.lower)
    out['folders'] = count_by_folder(out['files'])
    if out['files']:
        out['severity'] = 'warning' if out['counts']['ui'] or len(out['files']) >= BULK else 'info'
    out['identical'], out['different'], out['unknown'] = [], [], []
    if out['files']:
        p('Comparing the content with the game files')
    for n in out['files']:
        hash_key = n.replace('/', '\\').lstrip('\\').lower()
        game = g.read(n) if hash_key in have else None
        if game is None:
            out['unknown'].append(n)
            continue
        mine = unprotect._read(a, n)
        if mine == game and not _all_modes(n, g):
            out['different'].append(n)
            continue
        (out['identical'] if mine == game else out['different']).append(n)
    out['counts']['identical'] = len(out['identical'])
    return out


def _imp_without(data_bytes, name_list):
    from doctor.fix import no_use
    return no_use.imp_without(data_bytes, name_list)


def fix(entry, output, progress=None, casc=None, scope='all'):
    import shutil
    from doctor.fix import unprotect
    from doctor.models import model_check
    from doctor.mpq import mpqadd
    p = progress or _nothing
    res = {'state': 'failed', 'removed': 0, 'folders': [], 'lines': []}
    if os.path.normcase(os.path.abspath(entry)) == os.path.normcase(os.path.abspath(output)):
        res['error'] = 'The output must be a new file.'
        return res
    r = scan(entry, p, casc)
    if r.get('error'):
        res['error'] = r['error']
        return res
    own = []
    if scope == 'identical':
        name_list = list(r.get('identical') or [])
    else:
        name_list = [n for n in r['files'] if scope != 'ui' or classe(n) == 'ui']
        if scope == 'all' and name_list:
            from doctor.fix import game_paths
            p('Comparing the pictures with the game\'s')
            a0, _err = model_check._open(entry)
            g = game_paths.open_game(casc)
            if a0 is not None and g is not None:
                own = own_art(a0, name_list, g)
            del a0
            outside = set(own)
            name_list = [n for n in name_list if n not in outside]
    res['kept'] = len(own)
    res['kept_folders'] = count_by_folder(own)[:6]
    if not name_list:
        res['state'] = 'nothing_to_do'
        res['reason'] = ('The map has no file that is a byte-for-byte copy of a game file.' if scope == 'identical' else
                         'The map has no UI file with the path of a game file.' if scope == 'ui' else
                         'The map has no file with the path of a game file.')
        if own:
            res['reason'] = kept_line(own)
        return res
    a, err = model_check._open(entry)
    if a is None:
        res['error'] = err
        return res
    all_items = model_check._names(a)
    imp = unprotect._read(a, 'war3map.imp')
    repl = []
    if imp:
        new_imp, _n = _imp_without(imp, name_list)
        if new_imp != imp:
            repl.append(('war3map.imp', new_imp))
    part = model_check._part(output)
    try:
        p('Writing the new map')
        shutil.copyfile(entry, part)
        no_place = []
        with unprotect.quiet():
            mpqadd.add_files(part, repl, list(name_list), log=_nothing, no_slot=no_place)
        if no_place:
            raise RuntimeError('no room in the hash table for %s' % ', '.join(no_place))
        b, err = model_check._open(part)
        if b is None:
            raise RuntimeError(err)
        for n in name_list:
            if unprotect._read(b, n) is not None:
                raise RuntimeError('%s is still in the map' % n)
        unprotect.check_untouched(a, b, all_items, list(name_list) + [n for n, _d in repl])
        for n, d in repl:
            if unprotect._read(b, n) != d:
                raise RuntimeError('%s was not read back' % n)
        del a, b
        os.replace(part, output)
    except Exception as e:
        try:
            os.remove(part)
        except OSError:
            pass
        res['error'] = 'The check of the new map failed (%s).' % (str(e) or type(e).__name__)
        return res
    res.update(state='done', removed=len(name_list), folders=count_by_folder(name_list)[:6])
    res['lines'] = [
        '%d files that %s left the map (%s).'
        % (
            len(name_list),
            'were byte-for-byte copies of a game file' if scope == 'identical' else 'had the path of a game file',
            ', '.join('%s %d' % (f, n) for f, n in res['folders'][:4]),
        )
    ]
    if own:
        res['lines'].append(kept_line(own))
    return res
