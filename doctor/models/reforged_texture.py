# Large RLE TGA textures saved uncompressed so Reforged draws them.
import os
import re
import shutil
import struct



RLE_LIMIT = 600000


def without_rle(data_bytes, out_limit=RLE_LIMIT):
    if not data_bytes or len(data_bytes) < 18 or data_bytes[2] not in (9, 10, 11):
        return None
    w, h = struct.unpack_from('<HH', data_bytes, 12)
    if w * h <= out_limit:
        return None
    from doctor.viewers import map_card
    w, h, rgba, _fmt = map_card.tga_decode(data_bytes)
    return map_card.tga_bytes(w, h, rgba)


def map_own(name_list, ler, log=None, out_limit=RLE_LIMIT):
    out = {}
    seen = set()
    failures = []
    for n in name_list:
        k = n.replace('/', '\\').lower()
        if not k.endswith('.tga') or k in seen:
            continue
        seen.add(k)
        try:
            tga_uncompressed = without_rle(ler(n), out_limit)
        except Exception as e:
            failures.append('%s (%s)' % (n, type(e).__name__))
            tga_uncompressed = None
        if tga_uncompressed is not None:
            out[n] = tga_uncompressed
    if log and out:
        log('   %d large RLE TGA texture(s) saved uncompressed (Reforged draws them white): %s'
            % (len(out), ', '.join(sorted(out)[:6])))
    if log and failures:
        log('   %d TGA texture(s) could not be read and stay as they are (one may show white): %s'
            % (len(failures), ', '.join(failures[:6])))
    return out


CONSOLE_RACES = ('Human', 'Orc', 'NightElf', 'Undead', 'Forsaken')
CONSOLE_EXTENSIONS = ('blp', 'dds', 'tga')
EDITOR_WITH_PIECES = 6060


def editor_of_map(ler):
    try:
        d = ler('war3map.w3i')
    except Exception:
        return None
    return struct.unpack_from('<i', d, 8)[0] if d and len(d) >= 12 else None


def console_piece(race_name, n, ext='blp'):
    return 'UI\\Console\\%s\\%sUITile%02d.%s' % (race_name, race_name, n, ext)


def transparent_blp():
    from PIL import Image
    from doctor.models import blpwrite
    im = Image.new('RGBA', (512, 512), (255, 255, 255, 0))
    return blpwrite.blp_jpeg_bytes(im, 100, 8, True, None, [1] * 64)[1]


def _console_of_skin(body_text):
    out = {}
    outside = object()
    sec = outside
    races = dict((x.lower(), x) for x in CONSOLE_RACES)
    for ln in body_text.split('\n'):
        s = ln.strip()
        if s.startswith('['):
            n = s.strip('[]').strip().lower()
            sec = None if n == 'customskin' else ('Human' if n == 'default' else races.get(n, outside))
            continue
        m = re.match(r'(?i)consoletexture(\d\d)\s*=', s)
        if m and sec is not outside:
            out.setdefault(sec, set()).add(int(m.group(1)))
    return out


def console_pieces(present, skin=None, editor=None):
    if editor is not None and editor >= EDITOR_WITH_PIECES:
        return []
    sk = _console_of_skin(skin) if skin else {}
    overall = sk.get(None, set())
    out = []
    for race_name in CONSOLE_RACES:
        nums = overall | sk.get(race_name, set())

        def has_piece(n, race_name=race_name, nums=nums):
            return n in nums or any(present(console_piece(race_name, n, e)) for e in CONSOLE_EXTENSIONS)
        if any(has_piece(n) for n in (1, 2, 3, 4)):
            out += [console_piece(race_name, n) for n in (5, 6) if not has_piece(n)]
    return out


def console_of_map(ler, skin=None, log=None):
    def present(fname):
        try:
            return bool(ler(fname))
        except Exception:
            return False
    piece_list = console_pieces(present, skin, editor_of_map(ler))
    if not piece_list:
        return {}
    blp = transparent_blp()
    if log:
        log('   %d console piece(s) that the game draws beside the map\'s own console since 1.29 made transparent: %s'
            % (len(piece_list), ', '.join(piece_list)))
    return dict((p, blp) for p in piece_list)


def console_of_file(file_path):
    from doctor.mpq import mpqread
    a = mpqread.Archive(file_path)

    def ler(fname):
        try:
            return a.read(fname)
        except Exception:
            return None
    skin = ler('war3mapSkin.txt')
    return console_pieces(lambda fname: bool(ler(fname)), skin.decode('utf-8', 'replace') if skin else None,
                          editor_of_map(ler))


def _no_progress(*_a, **_k):
    return None


def console_fix(entry, output, progress=None):
    p = progress or _no_progress
    res = {'state': 'failed', 'written': []}
    if os.path.normcase(os.path.abspath(entry)) == os.path.normcase(os.path.abspath(output)):
        res['error'] = 'The output must be a new file.'
        return res
    from doctor.fix import unprotect
    from doctor.models import model_check
    from doctor.mpq import mpqadd
    from doctor.fix import editor_prep
    p('Reading the map')
    a, err = model_check._open(entry)
    if a is None:
        res['error'] = err
        return res
    name_list = model_check._names(a)
    skin = unprotect._read(a, 'war3mapSkin.txt')
    replacements = console_of_map(lambda n: unprotect._read(a, n), skin.decode('utf-8', 'replace') if skin else None)
    if not replacements:
        res['state'] = 'nothing_to_do'
        return res
    repl = sorted(replacements.items())
    new_ones = [n for n, _d in repl]
    extra = []
    listfile = unprotect._read(a, '(listfile)')
    if listfile is not None:
        eol = b'\r\n' if b'\r\n' in listfile or not listfile else b'\n'
        body = listfile if not listfile or listfile.endswith(b'\n') else listfile + eol
        extra.append(('(listfile)', body + eol.join(n.encode('utf-8') for n in new_ones) + eol))
    imp = unprotect._read(a, 'war3map.imp')
    if imp:
        try:
            extra.append(('war3map.imp', editor_prep.imp_with(imp, new_ones)))
        except (ValueError, struct.error):
            pass
    part = model_check._part(output)
    try:
        p('Writing the new map')
        shutil.copyfile(entry, part)
        no_place = []
        with unprotect.quiet():
            mpqadd.add_files(part, repl + extra, log=_no_progress, no_slot=no_place, grow=list(name_list))
        if no_place:
            raise RuntimeError('no room in the hash table for %s' % ', '.join(no_place[:5]))
        p('Checking the new map')
        b, err = model_check._open(part)
        if b is None:
            raise RuntimeError(err)
        for fname, data_bytes in repl + extra:
            if unprotect._read(b, fname) != data_bytes:
                raise RuntimeError('%s was not read back' % fname)
        unprotect.check_untouched(a, b, name_list, [n for n, _d in repl + extra])
        del a, b
        os.replace(part, output)
    except Exception as e:
        try:
            os.remove(part)
        except OSError:
            pass
        res['error'] = 'The check of the new map failed (%s).' % (str(e) or type(e).__name__)
        return res
    res['state'] = 'done'
    res['written'] = new_ones
    res['lines'] = ['%d console pieces that the game draws beside the map\'s own console since 1.29 made transparent '
                    '(they showed the stone of the default console over the map\'s interface).' % len(new_ones)]
    return res
