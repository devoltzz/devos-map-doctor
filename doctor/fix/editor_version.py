# What the World Editor of 1.24 to 1.29 reads, and the game files of each version, for Open in World Editor keeping the map in its version.
import os
import re
import struct



HERE = os.path.dirname(os.path.abspath(__file__))
VERSIONS = ('1.24', '1.25', '1.26', '1.27', '1.28', '1.29')
REFORGED = 'reforged'

ARCHIVES = ('War3Patch.mpq', 'War3xLocal.mpq', 'War3x.mpq', 'War3Local.mpq', 'War3.mpq', 'Deprecated.mpq')
PATCH_ARCHIVE = 'Patch_War3x.mpq'
BNUPDATE_HEADER = 24
BNUPDATE_WHOLE = 1

TRIGGER_DATA = 'UI\\TriggerData.txt'
COMMON_J = 'Scripts\\common.j'
BLIZZARD_J = 'Scripts\\Blizzard.j'

_BASE = {'w3i': 25, 'wtg': 7, 'wct': 1, 'objects': 2, 'w3s': 1, 'w3r': 5, 'w3c': 0, 'w3e': 11, 'imp': 1,
         'jasshelper': False, 'lua': False}
PROFILES = {
    '1.24': dict(_BASE, editor=6052, players=12, label='World Editor 1.24'),
    '1.25': dict(_BASE, editor=6052, players=12, label='World Editor 1.25'),
    '1.26': dict(_BASE, editor=6052, players=12, label='World Editor 1.26'),
    '1.27': dict(_BASE, editor=6052, players=12, label='World Editor 1.27'),
    '1.28': dict(_BASE, editor=6059, players=12, label='World Editor 1.28'),
    '1.29': dict(_BASE, editor=6060, players=24, label='World Editor 1.29'),
}
GUESS = ((6052, '1.27'), (6059, '1.28'), (6060, '1.29'))
OBJECT_FILES = ('war3map.w3u', 'war3map.w3t', 'war3map.w3a', 'war3map.w3b', 'war3map.w3d', 'war3map.w3q',
                'war3map.w3h')
SKIN_FILES = tuple(n.replace('war3map.', 'war3mapSkin.') for n in OBJECT_FILES)


def normalize(version):
    if version is None:
        return None
    v = str(version).strip().lower()
    if v in ('', REFORGED):
        return None
    if v == 'auto':
        return 'auto'
    from doctor.data import wc3_versions
    exact = wc3_versions.normalize(v)
    if exact == wc3_versions.REFORGED:
        return None
    if exact not in wc3_versions.CLASSIC:
        raise ValueError('no World Editor version %r here: %s (or reforged)' % (version, ', '.join(VERSIONS)))
    return exact


def family(version):
    return normalize(version)[:4]


def profile(version):
    v = normalize(version)
    if not v or v == 'auto' or family(v) not in PROFILES:
        raise ValueError('no profile for %r' % (version,))
    return dict(PROFILES[family(v)], version=v, family=family(v), files_at=where(v))


def versions_root():
    env = os.environ.get('WC3_VERSOES')
    if env:
        return env if os.path.isdir(env) else None
    d = HERE
    for _ in range(8):
        cand = os.path.join(d, 'externos', 'wc3_versions')
        if os.path.isdir(cand):
            return cand
        up = os.path.dirname(d)
        if up == d:
            break
        d = up
    return None


def _from_packs(version, name):
    from doctor.data import wc3_versions
    try:
        return wc3_versions.read(version, name)
    except Exception:
        return None


_ARCHIVES = {}


def _archive(path):
    a = _ARCHIVES.get(path)
    if a is None:
        from doctor.mpq import mpqread
        a = _ARCHIVES[path] = mpqread.Archive(path)
    return a


def bnupdate_whole(data):
    if not data or len(data) < BNUPDATE_HEADER or data[:3] != b'\x18\x00\x04':
        return None
    if data[3] != BNUPDATE_WHOLE:
        return None
    size = struct.unpack_from('<I', data, 12)[0]
    body = data[BNUPDATE_HEADER:]
    return body if len(body) == size else None


def _from_installers(version, name):
    root = versions_root()
    if not root:
        return None
    folder = os.path.join(root, version)
    patch = os.path.join(folder, PATCH_ARCHIVE)
    if os.path.isfile(patch):
        a = _archive(patch)
        base = name.replace('/', '\\').split('\\')[-1]
        return bnupdate_whole(a.read(base)) if a.find(base) else None
    for arch in ARCHIVES:
        p = os.path.join(folder, arch)
        if os.path.isfile(p):
            a = _archive(p)
            if a.find(name):
                return a.read(name)
    return None


READERS = [_from_packs, _from_installers]


def game_file(version, name):
    v = normalize(version)
    for reader in READERS:
        data = reader(v, name)
        if data is not None:
            return data
    return None


def where(version):
    from doctor.data import wc3_versions
    v = normalize(version)
    try:
        d = wc3_versions.pack_dir(v)
    except Exception:
        d = None
    if d:
        return d
    root = versions_root()
    return os.path.join(root, v) if root else None


_TD = {}


def trigger_data(version):
    from doctor.triggers import triggerdata
    v = normalize(version)
    td = _TD.get(v)
    if td is None:
        data = game_file(v, TRIGGER_DATA)
        if not data:
            raise FileNotFoundError('UI\\TriggerData.txt of Warcraft III %s: not found (%s)' % (v, where(v)))
        td = _TD[v] = triggerdata._from_bytes(data, 'Warcraft III %s' % v, triggerdata.CACHE_DIR)
    return td


def trigger_data_text(version):
    data = game_file(version, TRIGGER_DATA)
    return data.decode('utf-8', 'replace') if data else None


SOUND_TABLES = ('AbilitySounds.slk', 'AmbienceSounds.slk', 'AnimSounds.slk', 'DialogSounds.slk', 'UISounds.slk',
                'UnitAckSounds.slk', 'UnitCombatSounds.slk')
_LABELS = {}


def sound_labels(version):
    from doctor.data import slk
    v = normalize(version)
    out = _LABELS.get(v)
    if out is None:
        out = {}
        for table in SOUND_TABLES:
            data = game_file(v, 'UI\\SoundInfo\\' + table)
            if not data:
                continue
            _header, rows = slk.parse_slk_bytes(data)
            for label, row in rows.items():
                base = (row.get('DirectoryBase') or '').strip('"').replace('/', '\\')
                if base and not base.endswith('\\'):
                    base += '\\'
                for f in (row.get('FileNames') or '').strip('"').split(','):
                    f = f.strip()
                    if not f or not label or label == 'SoundName':
                        continue
                    path = (base + f).replace('/', '\\').lower()
                    out.setdefault(path, label)
        _LABELS[v] = out
    return out


def cache_root():
    from doctor.triggers import triggerdata
    return os.path.join(os.environ.get('DOCTOR_CACHE') or triggerdata.CACHE_DIR, 'editor_version')


def scripts_dir(version):
    from doctor.data import wc3_versions
    v = normalize(version)
    try:
        folder = wc3_versions.scripts_dir(v)
    except Exception:
        folder = None
    if folder and all(os.path.isfile(os.path.join(folder, f)) for f in ('common.j', 'blizzard.j')):
        return folder
    out = os.path.join(cache_root(), v)
    for name, path in (('common.j', COMMON_J), ('blizzard.j', BLIZZARD_J)):
        data = game_file(v, path)
        if not data:
            raise FileNotFoundError('%s of Warcraft III %s: not found (%s)' % (path, v, where(v)))
        target = os.path.join(out, name)
        try:
            with open(target, 'rb') as f:
                same = f.read() == data
        except OSError:
            same = False
        if not same:
            os.makedirs(out, exist_ok=True)
            tmp = '%s.%d.tmp' % (target, os.getpid())
            with open(tmp, 'wb') as f:
                f.write(data)
            os.replace(tmp, target)
    return out


def available(version):
    try:
        v = normalize(version)
        return all(game_file(v, n) for n in (TRIGGER_DATA, COMMON_J, BLIZZARD_J))
    except Exception:
        return False


def guess(w3i_bytes):
    if not w3i_bytes or len(w3i_bytes) < 12:
        return None, 'no war3map.w3i'
    fmt, _saves, editor = struct.unpack_from('<iii', w3i_bytes, 0)
    if fmt >= 28:
        return None, 'war3map.w3i version %d, editor %d: saved by World Editor 1.31 or newer' % (fmt, editor)
    if fmt not in (18, 25):
        return None, 'war3map.w3i version %d: not known' % fmt
    for top, v in GUESS:
        if editor <= top:
            return normalize(v), 'war3map.w3i version %d, editor %d' % (fmt, editor)
    return None, 'war3map.w3i version %d, editor %d: 1.30, which has no game files here' % (fmt, editor)


RANGE_EDITOR = {'1.24-1.28': None, '1.29': '1.29'}


def made_for(path, w3i_bytes=None):
    try:
        from doctor.data import wc3_versions
        d = wc3_versions.detect(path)
    except Exception:
        d = None
    if not d or not d.get('range'):
        return guess(w3i_bytes)
    rng = d['range']
    why = '; '.join(d.get('reasons') or []) or rng
    if rng not in RANGE_EDITOR:
        return None, why
    if RANGE_EDITOR[rng]:
        return normalize(RANGE_EDITOR[rng]), why
    v, _w = guess(w3i_bytes)
    return (v if v and v[:4] != '1.29' else normalize('1.27')), why


def _version_of(data):
    return struct.unpack_from('<i', data, 0)[0] if data and len(data) >= 4 else None


def check_map(version, read):
    p = profile(version)
    blocks, warnings, regen = [], [], None
    w3i_b = read('war3map.w3i')
    fmt = _version_of(w3i_b)
    if fmt is not None and fmt > p['w3i']:
        _v, why = guess(w3i_b)
        blocks.append(('newer_map', 'the map was saved by a newer World Editor (%s); open it with the Reforged route'
                       % why))
    lua = read('war3map.lua') is not None
    jass = read('war3map.j') is not None or read('scripts\\war3map.j') is not None
    language = None
    if w3i_b and fmt is not None and fmt >= 28:
        try:
            from doctor.data import w3i
            language = w3i.parse(w3i_b).get('script_language')
        except Exception:
            language = None
    if language == 1 or (lua and not jass):
        blocks.append(('lua', 'the map script is Lua: the World Editor reads Lua from 1.31 on'))
    newer = sorted(n for n in OBJECT_FILES if (_version_of(read(n)) or 0) > p['objects'])
    if newer:
        blocks.append(('newer_objects', 'object data in version 3 (Reforged 1.32+): %s' % ', '.join(newer)))
    skins = [n for n in SKIN_FILES if read(n) is not None]
    if skins:
        blocks.append(('skin_files', 'Reforged skin files (1.32+): %s' % ', '.join(skins)))
    w3e = read('war3map.w3e')
    if w3e and len(w3e) >= 8 and w3e[:4] == b'W3E!':
        v = struct.unpack_from('<i', w3e, 4)[0]
        if v > p['w3e']:
            warnings.append(('w3e', 'war3map.w3e is version %d; the editor of %s writes %d (not converted)'
                             % (v, p['version'], p['w3e'])))
    if w3i_b and fmt in (18, 25):
        try:
            from doctor.data import w3i
            n = len(w3i.parse(w3i_b)['players'])
        except Exception:
            n = 0
        if n > p['players']:
            warnings.append(('players', 'the map has %d player slots; the editor of %s has %d'
                             % (n, p['version'], p['players'])))
    wtg_b = read('war3map.wtg')
    if wtg_b and len(wtg_b) >= 8 and wtg_b[:4] == b'WTG!' and struct.unpack_from('<I', wtg_b, 4)[0] & 0x80000000:
        regen = 'war3map.wtg in the 1.31 format: the editor of %s reads the classic one (version 7)' % p['version']
    return {'blocks': blocks, 'warnings': warnings, 'regenerate_triggers': regen}


RX_DEFINED = re.compile(r'(?m)^[ \t]*(?:constant[ \t]+)?(?:native|function)[ \t]+(\w+)[ \t]+takes\b')
RX_CALLED = re.compile(r'\b([A-Za-z]\w*)[ \t]*\(')
RX_NOISE = re.compile(r'//[^\n]*|"(?:[^"\\\n]|\\.)*"|\'(?:[^\'\\\n]|\\.)*\'')


def _defined(text):
    return set(RX_DEFINED.findall(text or ''))


_GAME_NAMES = {}


def game_names(version):
    key = version or REFORGED
    names = _GAME_NAMES.get(key)
    if names is None:
        if version is None:
            from doctor.triggers import triggerdata
            texts = [triggerdata.game_script(n) for n in ('common.j', 'blizzard.j')]
        else:
            texts = [(game_file(version, n) or b'').decode('latin-1') for n in (COMMON_J, BLIZZARD_J)]
        names = _GAME_NAMES[key] = frozenset().union(*(_defined(t) for t in texts))
    return names


def missing_natives(version, script):
    code = RX_NOISE.sub(' ', script or '')
    called = set(RX_CALLED.findall(code)) - _defined(code)
    mine = game_names(normalize(version))
    newer = game_names(None)
    return sorted(n for n in called if n in newer and n not in mine)
