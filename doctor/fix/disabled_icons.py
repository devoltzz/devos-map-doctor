# Makes the disabled art (DISBTN) of the imported icons, which the game draws green without it.
import os
import shutil
import struct
import tempfile

from doctor.fix import unprotect


DISABLED_FOLDER = 'ReplaceableTextures\\CommandButtonsDisabled\\'
OBJECT_FIELDS = {'w3u': (b'uico',), 'w3t': (b'iico',), 'w3a': (b'aart', b'arar', b'auar'), 'w3q': (b'gar1',)}
LEVELLED = ('w3a', 'w3d', 'w3q')
OBJECT_FILES = tuple('%s.%s' % (base, ext) for base in ('war3map', 'war3mapSkin') for ext in OBJECT_FIELDS)
TXT_KEYS = ('art', 'researchart', 'unart')
IMAGE_EXTS = ('.blp', '.dds', '.tga', '.png', '.jpg', '.jpeg')
DARKEN, GREY = 0.50, 0.70
QUALITY = 100


def _nothing(*_a, **_k):
    pass


def object_strings(data, levelled):
    ver = struct.unpack_from('<I', data, 0)[0]
    if ver not in (1, 2, 3):
        raise ValueError('object file version %d' % ver)
    p = 4
    for _table in range(2):
        n = struct.unpack_from('<I', data, p)[0]
        p += 4
        for _ in range(n):
            old, new = data[p:p + 4].decode('latin-1'), data[p + 4:p + 8].decode('latin-1')
            ident = new if new.strip('\0') else old
            p += 8
            sets = 1
            if ver >= 3:
                sets = struct.unpack_from('<I', data, p)[0]
                p += 4
            for _s in range(sets):
                if ver >= 3:
                    p += 4
                nm = struct.unpack_from('<I', data, p)[0]
                p += 4
                for _m in range(nm):
                    field = data[p:p + 4]
                    vt = struct.unpack_from('<I', data, p + 4)[0]
                    p += 16 if levelled else 8
                    if vt == 3:
                        end = data.index(b'\0', p)
                        yield ident, field, data[p:end]
                        p = end + 1
                    elif vt in (0, 1, 2):
                        p += 4
                    else:
                        raise ValueError('value type %d in field %r of %r' % (vt, field, ident))
                    p += 4
    if p > len(data) or data[p:].strip(b'\0'):
        raise ValueError('the file does not close (%d of %d bytes)' % (p, len(data)))


def txt_strings(data):
    section = ''
    for line in data.decode('utf-8', 'surrogateescape').splitlines():
        line = line.strip()
        if line.startswith('[') and line.endswith(']'):
            section = line[1:-1]
        elif '=' in line and not line.startswith('//'):
            key, value = line.split('=', 1)
            if key.strip().lower() in TXT_KEYS:
                yield section, key.strip(), value.strip()


def _paths(value):
    if isinstance(value, bytes):
        value = value.decode('utf-8', 'surrogateescape')
    out = []
    for part in value.split(','):
        part = part.strip().strip('"').strip().replace('/', '\\')
        if not part or part.upper().startswith('TRIGSTR_'):
            continue
        if not os.path.splitext(part)[1]:
            part += '.blp'
        out.append(part)
    return out


def disabled_path(icon):
    return DISABLED_FOLDER + 'DIS' + icon.replace('/', '\\').rsplit('\\', 1)[-1]


def icons(a, names):
    out = {}

    def add(value, where):
        for icon in _paths(value):
            out.setdefault(icon, []).append(where)

    for name in OBJECT_FILES:
        data = unprotect._read(a, name)
        if not data:
            continue
        ext = name.rsplit('.', 1)[1]
        try:
            for ident, field, value in object_strings(data, ext in LEVELLED):
                if field in OBJECT_FIELDS[ext]:
                    add(value, '%s %s %s' % (name, ident, field.decode('latin-1')))
        except (ValueError, struct.error):
            continue
    tables = sorted(n for n in names if n.lower().endswith('.txt') and
                    (n.lower().startswith('units\\') or n.lower() == 'war3mapskin.txt'))
    for name in tables:
        data = unprotect._read(a, name)
        if data:
            for section, key, value in txt_strings(data):
                add(value, '%s [%s] %s' % (name, section, key))
    return out


_CASC = []


def game_storage():
    if not _CASC:
        try:
            from doctor.data import casc_wc3
            with unprotect.quiet():
                _CASC.append(casc_wc3.CascWC3())
        except Exception:
            _CASC.append(None)
    return _CASC[0]


def _in_game(casc, path):
    if casc is None:
        return False
    base = os.path.splitext(path)[0]
    for ext in ('.blp', '.dds'):
        try:
            if casc.resolve(base + ext) is not None:
                return True
        except Exception:
            pass
    return False


def _readable(data, name):
    from doctor.viewers import map_card
    if not data:
        return 'the file does not read'
    try:
        map_card.decode(data, name)
        return ''
    except Exception as e:
        return (str(e) or type(e).__name__)[:80]


def _plan(a, names, casc):
    cited = icons(a, names)
    counts = {'icons': 0, 'present': 0, 'game': 0}
    taken, missing, collisions, unreadable = {}, [], [], []
    for icon in sorted(cited, key=str.lower):
        if not icon.lower().endswith(IMAGE_EXTS) or not a.find(icon):
            continue
        counts['icons'] += 1
        dis = disabled_path(icon)
        if a.find(dis):
            counts['present'] += 1
            continue
        if _in_game(casc, dis):
            counts['game'] += 1
            continue
        key = dis.lower()
        if key in taken:
            collisions.append([icon, taken[key]])
            continue
        data = unprotect._read(a, icon)
        why = _readable(data, icon)
        if why:
            unreadable.append([icon, why])
            continue
        taken[key] = icon
        missing.append((icon, dis, cited[icon], data))
    return missing, counts, collisions, unreadable


def scan(path):
    out = {'missing': [], 'icons': 0, 'present': 0, 'game': 0, 'collisions': [], 'unreadable': [], 'error': None}
    from doctor.models import model_check
    a, err = model_check._open(path)
    if a is None:
        out['error'] = err
        return out
    missing, counts, collisions, unreadable = _plan(a, model_check._names(a), game_storage())
    out.update(counts)
    out['collisions'] = collisions
    out['unreadable'] = unreadable
    out['missing'] = [{'icon': i, 'disabled': d, 'uses': len(u)} for i, d, u, _b in missing]
    return out


def darken(im, factor, grey, side):
    from PIL import Image
    im = im.convert('RGBA')
    if im.size != (side, side):
        im = im.resize((side, side), Image.LANCZOS)
    r, g, b, a = im.split()
    grey_im = im.convert('L')
    table = [max(0, min(255, int(round(v * factor)))) for v in range(256)]

    def mix(c):
        return Image.blend(c, grey_im, grey).point(table)
    return Image.merge('RGBA', (mix(r), mix(g), mix(b), a))


def make_disabled(data, name=''):
    from doctor.models import blpwrite
    from doctor.viewers import map_card
    from PIL import Image
    w, h, rgba, _fmt = map_card.decode(data, name)
    im = Image.frombytes('RGBA', (w, h), rgba)
    side = w if w == h and 64 <= w <= 256 else 64
    dark = darken(im, DARKEN, GREY, side)
    fd, tmp = tempfile.mkstemp(suffix='.blp')
    os.close(fd)
    try:
        blpwrite.save_blp(dark, tmp, quality=QUALITY, alpha_bits=0, extra=5)
        with open(tmp, 'rb') as f:
            return f.read()
    finally:
        os.remove(tmp)


def fix(path_in, path_out, progress=None):
    p = progress or _nothing
    res = {'state': 'failed', 'written': [], 'failed': [], 'checked': 0, 'collisions': [], 'unreadable': []}
    if os.path.abspath(path_in) == os.path.abspath(path_out):
        res['error'] = 'The output must be a new file.'
        return res
    from doctor.models import model_check
    from doctor.mpq import mpqadd
    from doctor.fix import editor_prep
    p('Reading the map')
    a, err = model_check._open(path_in)
    if a is None:
        res['error'] = err
        return res
    names = model_check._names(a)
    missing, _counts, res['collisions'], res['unreadable'] = _plan(a, names, game_storage())
    if not missing:
        res['state'] = 'nothing_to_do'
        return res
    p('Making %d disabled icons' % len(missing))
    repl = []
    for icon, dis, _uses, data in missing:
        try:
            repl.append((dis, make_disabled(data, icon)))
        except Exception as e:
            res['failed'].append([icon, str(e)[:80] or type(e).__name__])
    if not repl:
        res['state'] = 'nothing_to_do'
        return res
    new_names = [n for n, _d in repl]
    extra = []
    listfile = unprotect._read(a, '(listfile)')
    if listfile is not None:
        eol = b'\r\n' if b'\r\n' in listfile or not listfile else b'\n'
        body = listfile if not listfile or listfile.endswith(b'\n') else listfile + eol
        extra.append(('(listfile)', body + eol.join(n.encode('utf-8') for n in new_names) + eol))
    imp = unprotect._read(a, 'war3map.imp')
    if imp:
        try:
            extra.append(('war3map.imp', editor_prep.imp_with(imp, new_names)))
        except (ValueError, struct.error):
            pass
    part = model_check._part(path_out)
    try:
        p('Writing the new map')
        shutil.copyfile(path_in, part)
        no_room = []
        with unprotect.quiet():
            mpqadd.add_files(part, repl + extra, log=_nothing, no_slot=no_room, grow=list(names))
        if no_room:
            raise RuntimeError('no room in the hash table for %s' % ', '.join(no_room[:5]))
        p('Checking the new map')
        b, err = model_check._open(part)
        if b is None:
            raise RuntimeError(err)
        for name, data in repl + extra:
            if unprotect._read(b, name) != data:
                raise RuntimeError('%s was not read back' % name)
        done = set(n.lower() for n, _d in repl + extra)
        for n in names:
            if n.lower() in done:
                continue
            x = unprotect._read(a, n)
            if x is not None:
                if unprotect._read(b, n) != x:
                    raise RuntimeError('%s changed' % n)
                res['checked'] += 1
        del a, b
        os.replace(part, path_out)
    except Exception as e:
        try:
            os.remove(part)
        except OSError:
            pass
        res.update(error='The check of the new map failed (%s).' % (str(e) or type(e).__name__), written=[])
        return res
    res['state'] = 'done'
    res['written'] = new_names
    res['lines'] = ['%d imported icons got their disabled art (they were drawn green where the game shows them '
                    'disabled).' % len(new_names)]
    left = len(res['failed']) + len(res['unreadable'])
    if left:
        res['lines'].append('%d icons were left as they are: their image does not read (an encrypted or unknown '
                            'format).' % left)
    if res['collisions']:
        res['lines'].append('%d icons share the file name of another icon, so the game shows the same disabled art '
                            'for them.' % len(res['collisions']))
    return res
