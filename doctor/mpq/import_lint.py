# Finds the imported files the World Editor would drop, the game would never load, or that replace a game file.
import os

from doctor.fix import unprotect
from doctor.data import map_formats


CODES = ('not_in_imp', 'odd_extension', 'game_file')
GAME_EXTENSIONS = frozenset((
    '.mdx', '.mdl', '.blp', '.tga', '.dds', '.jpg', '.jpeg', '.png', '.bmp',
    '.wav', '.mp3', '.ogg', '.flac',
    '.ttf', '.otf',
    '.fdf', '.toc', '.txt', '.slk', '.ini', '.j', '.lua', '.ai', '.pld', '.wts',
    '.json', '.mp4', '.webm', '.avi',
    '.jc', '.bin',
    '.w3e', '.w3i', '.wtg', '.wct', '.w3u', '.w3t', '.w3a', '.w3b', '.w3d', '.w3h', '.w3q', '.w3c', '.w3r', '.w3s',
    '.doo', '.wpm', '.shd', '.mmp', '.imp', '.w3l', '.w3grp', '.soundasset', '.w3mod', '.w3x', '.w3m'))
ASSET_EXTENSIONS = ('.mdx', '.mdl', '.blp', '.tga', '.dds', '.wav', '.mp3', '.ogg', '.flac')
_CASC = []


def _nothing(*_a, **_k):
    pass


def game_storage():
    if not _CASC:
        try:
            from doctor.data import casc_wc3
            with unprotect.quiet():
                _CASC.append(casc_wc3.CascWC3())
        except Exception:
            _CASC.append(None)
    return _CASC[0]


def lint(path, progress=None, casc=None):
    p = progress or _nothing
    out = {'files': {}, 'counts': dict((c, 0) for c in CODES), 'imp': False, 'game': False}
    try:
        a = unprotect._open(path)
    except BaseException as e:
        if isinstance(e, KeyboardInterrupt):
            raise
        out['error'] = 'The map does not open (%s).' % unprotect._error(e)
        return out
    from doctor.models import model_check
    from doctor.mpq import mpqnames
    from doctor.fix import editor_prep
    p('Finding the file names')
    names = [n for n in model_check._names(a) if not map_formats.is_standard(n)]
    names = [n for n in names if unprotect._valid_for_game(a, n) is not None]
    by_game = set(n.lower() for n in mpqnames.GAME_NAMES)
    flags = {}

    def flag(n, code):
        flags.setdefault(n, []).append(code)
        out['counts'][code] += 1

    imp = unprotect._read(a, 'war3map.imp')
    if imp:
        try:
            outside = editor_prep.missing_from_imp(imp, [n for n in names if n.lower() not in by_game])
            out['imp'] = True
            for n in outside:
                flag(n, 'not_in_imp')
        except Exception:
            pass
    for n in names:
        ext = os.path.splitext(n)[1].lower()
        if ext not in GAME_EXTENSIONS:
            flag(n, 'odd_extension')
    c = casc if casc is not None else game_storage()
    if c is not None:
        out['game'] = True
        p('Comparing with the game files')
        for n in names:
            if n.lower().endswith(ASSET_EXTENSIONS) and n.lower() not in by_game:
                try:
                    if c.resolve(n) is not None:
                        flag(n, 'game_file')
                except Exception:
                    pass
    out['files'] = flags
    return out
