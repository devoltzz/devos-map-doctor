# The game files of each Warcraft III version from 1.24 to 1.29 (scripts and data), and which version a map was made for.
import fnmatch
import hashlib
import json
import os
import re
import struct
import sys
import zlib


HERE = os.path.dirname(os.path.abspath(__file__))

COMMON = os.path.normpath(os.path.join(HERE, '..'))
REF_ROOT = os.path.join(COMMON, 'ref')
INDEX_NAME = 'versions.json'
NATIVES_NAME = 'natives_patch.json'
SCRIPTS = ('common.j', 'blizzard.j', 'common.ai')
REFORGED = '3.0'

SOURCES = (('1.24a', 'patch'), ('1.24b', 'patch'), ('1.24c', 'patch'), ('1.24d', 'patch'), ('1.24e', 'patch'),
           ('1.25b', 'patch'), ('1.26a', 'patch'), ('1.27a', 'patch'), ('1.27b', 'patch'),
           ('1.28.5', 'folder'), ('1.29.2', 'folder'))
CLASSIC = tuple(v for v, _k in SOURCES)
RANGES = (('pre-1.24', None), ('1.24-1.28', '1.27b'), ('1.29', '1.29.2'), ('1.30+', REFORGED))
RANGE_ORDER = tuple(r for r, _v in RANGES)
FOLDER_ARCHIVES = ('War3Patch.mpq', 'War3xLocal.mpq', 'War3x.mpq', 'War3Local.mpq', 'War3.mpq', 'Deprecated.mpq')
BASE_VERSION = '1.21b_base'
BASE_FOLDER = 'Wc3_1.21b_TFT_enGB'
TOME_ARCHIVES = ('Common\\War3xLocal.mpq', 'Common\\War3Patch.mpq')
ROC_FROM = '1.28.5'
ROC_ARCHIVES = ('War3Local.mpq', 'War3.mpq')

DATA_PATTERNS = ('units\\*.slk', 'units\\*.txt', 'ui\\*.txt', 'ui\\*.slk', 'doodads\\*.slk', 'doodads\\*.txt',
                 'scripts\\*', 'terrainart\\*.slk', 'splats\\*.slk',
                 'ui\\soundinfo\\*.slk',
                 'custom_v0\\units\\*', 'custom_v1\\units\\*', 'melee_v0\\units\\*', 'melee_v1\\units\\*',
                 'custom_v0\\scripts\\*', 'custom_v1\\scripts\\*', 'melee_v0\\scripts\\*', 'melee_v1\\scripts\\*')
BALANCE = ('custom_v0', 'custom_v1', 'melee_v0', 'melee_v1')
PACK_MANIFEST = 'doctor_game_data.json'
PACK_LIST = 'paths.txt'
OBJECTS = 'objects'

MIB = 1024 * 1024
LIMITS = {'1.24a': {'map_bytes': 4 * MIB}, '1.29': {'map_bytes': 128 * MIB, 'players': 24}}
LIMIT_DEFAULT = {'map_bytes': 8 * MIB, 'players': 12, 'lua': False, 'w3i': 25, 'objects': 2}


class VersionError(Exception):
    pass


def versions():
    return list(CLASSIC)


def normalize(text):
    t = str(text or '').strip().lower().lstrip('v')
    if t in CLASSIC:
        return t
    if t in ('reforged', 'r', '3', '3.0', '3.0.0', '3.0.1', '2', '2.0') or t.startswith(('3.', '2.')):
        return REFORGED
    m = re.match(r'^1\.?(\d{2})([a-z]?)(?:\.\d+)*$', t)
    if not m:
        return None
    minor = int(m.group(1))
    if minor >= 30:
        return REFORGED
    same = [v for v in CLASSIC if _key(v)[:2] == (1, minor)]
    if not same:
        return None
    if m.group(2):
        exact = '1.%02d%s' % (minor, m.group(2))
        return exact if exact in CLASSIC else same[-1]
    return same[-1]


def _key(version):
    t = str(version).strip().lower()
    m = re.match(r'^(\d+)\.(\d+)([a-z]?)(?:\.(\d+))?', t)
    if not m:
        return (0, 0, 0)
    third = (ord(m.group(3)) - 96) if m.group(3) else int(m.group(4) or 0)
    return (int(m.group(1)), int(m.group(2)), third)


def range_of(version):
    v = normalize(version)
    if v is None or v == REFORGED:
        return REFORGED if v else None
    return '1.29' if _key(v) >= (1, 29, 0) else '1.24-1.28'


def limits(version):
    v = normalize(version)
    if v in (None, REFORGED):
        return None
    out = dict(LIMIT_DEFAULT)
    out.update(LIMITS.get(range_of(v), {}))
    out.update(LIMITS.get(v, {}))
    return out


def sources_dir():
    return os.environ.get('WC3_VERSOES_ORIGEM') or os.path.normpath(os.path.join(COMMON, '..', 'externos',
                                                                                 'wc3_versions'))


PACK_ZIP = 'wc3_versions.zip'
_DATA = {}
DATA_URL = 'https://doctor.devoltz.party/data/' + PACK_ZIP
DATA_ZIP = {'size': 4054218, 'sha256': '286d059fec9ecd64e9e4498d29a6f2d0533228ce43fa6587249b88e9dc89453d'}
_DOWNLOAD = {}


def user_data_dir():
    if sys.platform.startswith('linux'):
        base = os.environ.get('XDG_DATA_HOME') or os.path.join(os.path.expanduser('~'), '.local', 'share')
    else:
        base = os.environ.get('LOCALAPPDATA') or os.environ.get('APPDATA') or os.path.expanduser('~')
    return os.path.join(base, 'DevosMapDoctor', 'wc3_versions')


def download(progress=None):
    import hashlib
    import shutil
    import urllib.request
    p = progress or (lambda s: None)
    d = user_data_dir()
    os.makedirs(os.path.dirname(d), exist_ok=True)
    part = d + '.zip.part'
    url = os.environ.get('WC3_VERSOES_URL') or DATA_URL
    h = hashlib.sha256()
    got = 0
    p('Downloading the game files of the old versions (%d MB)' % (DATA_ZIP['size'] >> 20))
    if os.path.isfile(url):
        src = open(url, 'rb')
    else:
        try:
            from doctor.translation.machine_translate import _ssl_context
            ctx = _ssl_context()
        except Exception:
            ctx = None
        src = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'DevosMapDoctor'}), timeout=60,
                                     context=ctx)
    try:
        with src, open(part, 'wb') as out:
            while True:
                chunk = src.read(1 << 20)
                if not chunk:
                    break
                out.write(chunk)
                h.update(chunk)
                got += len(chunk)
        if not os.environ.get('WC3_VERSOES_URL') and (got != DATA_ZIP['size'] or h.hexdigest() != DATA_ZIP['sha256']):
            raise OSError('the download of %s is incomplete or damaged' % PACK_ZIP)
        if os.path.isdir(d):
            shutil.rmtree(d, ignore_errors=True)
        unpack(part, d)
    finally:
        if os.path.exists(part):
            os.remove(part)
    _DATA['dir'] = d
    return d


def ensure(progress=None):
    if os.path.isdir(os.path.join(data_dir(), OBJECTS)):
        return True
    if 'failed' in _DOWNLOAD or os.environ.get('WC3_VERSOES_DADOS'):
        return False
    try:
        download(progress)
        return True
    except Exception as e:
        _DOWNLOAD['failed'] = str(e)
        return False


def data_dir():
    env = os.environ.get('WC3_VERSOES_DADOS')
    if env:
        return env
    if 'dir' in _DATA:
        return _DATA['dir']
    if getattr(sys, 'frozen', False):
        d = os.path.join(os.path.dirname(os.path.abspath(sys.executable)), 'wc3_versions')
        if not os.path.isdir(os.path.join(d, OBJECTS)) and os.path.isdir(os.path.join(user_data_dir(), OBJECTS)):
            d = user_data_dir()
    else:
        d = os.path.join(COMMON, 'cache', 'wc3_versions')
    _DATA['dir'] = d
    zipped = os.path.join(os.path.dirname(d), PACK_ZIP)
    if not os.path.isdir(os.path.join(d, OBJECTS)) and os.path.isfile(zipped):
        import tempfile
        cache = os.path.join(os.environ.get('DOCTOR_CACHE') or os.path.join(tempfile.gettempdir(),
                                                                             'devos_map_doctor_ui'), 'wc3_versions')
        for target in (d, cache):
            try:
                if not os.path.isdir(os.path.join(target, OBJECTS)):
                    unpack(zipped, target)
                _DATA['dir'] = target
                break
            except Exception:
                continue
    return _DATA['dir']


def _ref_roots():
    roots = [REF_ROOT]
    if getattr(sys, 'frozen', False):
        roots.append(os.path.join(os.path.dirname(os.path.abspath(sys.executable)), 'ref'))
    roots.append(os.path.join(data_dir(), 'ref'))
    return roots


_INDEX = {}


def index():
    if 'i' not in _INDEX:
        _INDEX['i'] = {}
        for root in _ref_roots():
            p = os.path.join(root, INDEX_NAME)
            if os.path.isfile(p):
                with open(p, encoding='utf-8') as f:
                    _INDEX['i'] = json.load(f)
                break
    return _INDEX['i']


def scripts_name(version):
    v = normalize(version)
    if v == REFORGED:
        return REFORGED
    return ((index().get('versions') or {}).get(v) or {}).get('scripts')


def scripts_dir(version):
    name = scripts_name(version)
    if not name:
        return None
    for root in _ref_roots():
        d = os.path.join(root, name)
        if all(os.path.isfile(os.path.join(d, f)) for f in SCRIPTS[:2]):
            return d
    return None


def pack_dir(version):
    v = normalize(version)
    if v in (None, REFORGED):
        return None
    if getattr(sys, 'frozen', False):
        ensure()
    d = os.path.join(data_dir(), v)
    return d if os.path.isfile(os.path.join(d, PACK_MANIFEST)) else None


def casc_path(mpq_path):
    p = mpq_path.replace('/', '\\').lstrip('\\')
    head, sep, rest = p.partition('\\')
    if sep and head.lower() in BALANCE:
        return 'war3.w3mod:_balance\\%s.w3mod:%s' % (head.lower(), rest)
    return 'war3.w3mod:' + p


_GAMES = {}


def game(version):
    d = pack_dir(version)
    if d is None:
        return None
    if d not in _GAMES:
        from doctor.data import casc_wc3
        _GAMES[d] = casc_wc3.CascWC3(d)
    return _GAMES[d]


def read(version, path):
    v = normalize(version)
    if v is None:
        raise VersionError('unknown version: %r' % (version,))
    g = game(v) if v != REFORGED else None
    if g is not None:
        key = casc_path(path).lower()
        if key in g.file_set:
            try:
                return g.read_data(key)
            except Exception:
                return None
    low = path.replace('/', '\\').lower()
    if low.startswith('scripts\\') and low[8:] in SCRIPTS:
        d = scripts_dir(v)
        if d:
            with open(os.path.join(d, low[8:]), 'rb') as f:
                return f.read()
    return None


def pack_patterns_match(mpq_path):
    low = mpq_path.replace('/', '\\').lower()
    for pat in DATA_PATTERNS:
        if low.count('\\') == pat.count('\\') and fnmatch.fnmatchcase(low, pat):
            return True
    return False


BNU_HEADER = struct.Struct('<HBBIIIQ')
BNU_WHOLE, BNU_BSDIFF = 1, 4


def bnupdate_header(entry):
    if len(entry) < BNU_HEADER.size:
        return None
    hsize, magic, kind, crc, src, dst, ft = BNU_HEADER.unpack_from(entry, 0)
    if hsize != BNU_HEADER.size or magic != 4 or kind not in (BNU_WHOLE, BNU_BSDIFF):
        return None
    return {'kind': kind, 'source_crc': crc, 'source_size': src, 'size': dst, 'filetime': ft}


def rle_unpack(data, offset=0):
    size = struct.unpack_from('<I', data, offset)[0]
    out = bytearray(size)
    p, q, end = offset + 4, 0, len(data)
    while p < end and q < size:
        b = data[p]
        p += 1
        if b & 0x80:
            n = min((b & 0x7F) + 1, size - q, end - p)
            out[q:q + n] = data[p:p + n]
            q += n
            p += n
        else:
            q += b + 1
    return bytes(out)


def _add(a, b):
    try:
        import numpy
        return (numpy.frombuffer(a, numpy.uint8) + numpy.frombuffer(b, numpy.uint8)).tobytes()
    except ImportError:
        return bytes((x + y) & 0xFF for x, y in zip(a, b))


def bsdiff40(patch, old):
    if patch[:8] != b'BSDIFF40':
        raise VersionError('not a BSDIFF40 patch')
    ctrl_size, data_size, new_size = struct.unpack_from('<QQQ', patch, 8)
    c, d = 32, 32 + ctrl_size
    x = d + data_size
    new = bytearray(new_size)
    no = oo = 0
    lo = len(old)
    while no < new_size:
        if c + 12 > 32 + ctrl_size:
            raise VersionError('BSDIFF40: the control block ends before the new file')
        add, mov, move = struct.unpack_from('<III', patch, c)
        c += 12
        if no + add > new_size:
            raise VersionError('BSDIFF40: data past the new size')
        block = patch[d:d + add]
        d += add
        if oo < 0:
            raise VersionError('BSDIFF40: the old offset went below zero')
        both = max(0, min(add, lo - oo))
        new[no:no + add] = block
        if both:
            new[no:no + both] = _add(block[:both], old[oo:oo + both])
        no += add
        oo += add
        if no + mov > new_size:
            raise VersionError('BSDIFF40: extra past the new size')
        new[no:no + mov] = patch[x:x + mov]
        x += mov
        no += mov
        oo += -(move & 0x7FFFFFFF) if move & 0x80000000 else move
    return bytes(new)


def bnupdate_apply(entry, source=None):
    h = bnupdate_header(entry)
    if h is None:
        raise VersionError('no BNUpdate header')
    if h['kind'] == BNU_WHOLE:
        out = entry[BNU_HEADER.size:]
    else:
        if source is None:
            raise VersionError('a BSDIFF entry needs its source file')
        if len(source) != h['source_size'] or zlib.crc32(source) & 0xFFFFFFFF != h['source_crc']:
            raise VersionError('the source is not the one the diff was made on (size or CRC32)')
        out = bsdiff40(rle_unpack(entry, BNU_HEADER.size), source)
    if len(out) != h['size']:
        raise VersionError('the result has %d bytes, the header says %d' % (len(out), h['size']))
    return out


def _quiet():
    import contextlib
    import io
    return contextlib.redirect_stdout(io.StringIO())


def _open_mpq(path):
    from doctor.mpq import mpqread
    with _quiet():
        return mpqread.Archive(path)


def _read_mpq(archive, name):
    try:
        with _quiet():
            return archive.read(name)
    except Exception:
        return None


def _listfile(archive):
    d = _read_mpq(archive, '(listfile)')
    if not d:
        return []
    return [n for n in d.decode('latin-1').replace('\r', '\n').split('\n') if n.strip()]


class MpqChain(object):
    def __init__(self, paths):
        self.paths = [p for p in paths if os.path.isfile(p)]
        self.archives = [_open_mpq(p) for p in self.paths]
        self._names = None

    def names(self):
        if self._names is None:
            self._names = {}
            for a in self.archives:
                for n in _listfile(a):
                    self._names.setdefault(n.lower(), n)
        return self._names

    def read(self, path):
        for a in self.archives:
            d = _read_mpq(a, path)
            if d is not None:
                return d
        return None

    def with_crc(self, path, crc, size):
        for a in self.archives:
            d = _read_mpq(a, path)
            if d is not None and len(d) == size and zlib.crc32(d) & 0xFFFFFFFF == crc:
                return d
        return None


def _tome_archive(sources, work, inner):
    out = os.path.join(work, '1.21b_' + inner.split('\\')[-1])
    if not os.path.isfile(out):
        tome = _open_mpq(os.path.join(sources, BASE_VERSION, BASE_FOLDER, 'Installer Tome.mpq'))
        data = _read_mpq(tome, inner)
        if data is None:
            raise VersionError('the Installer Tome.mpq has no %s' % inner)
        os.makedirs(work, exist_ok=True)
        with open(out + '.part', 'wb') as f:
            f.write(data)
        os.replace(out + '.part', out)
    return out


class Base(object):
    def __init__(self, sources, work):
        local = _tome_archive(sources, work, TOME_ARCHIVES[0])
        old_patch = _tome_archive(sources, work, TOME_ARCHIVES[1])
        war3x = os.path.join(sources, BASE_VERSION, BASE_FOLDER, 'Common', 'War3x.mpq')
        self.tft = MpqChain([local, war3x])
        self.extra = MpqChain([old_patch])
        self.roc = MpqChain([os.path.join(sources, ROC_FROM, n) for n in ROC_ARCHIVES])

    def names(self):
        out = dict(self.roc.names())
        out.update(self.tft.names())
        return out

    def read(self, path):
        d = self.tft.read(path)
        if d is not None:
            return d, False
        d = self.roc.read(path)
        return d, d is not None

    def source(self, path, crc, size):
        for chain in (self.tft, self.extra, self.roc):
            d = chain.with_crc(path, crc, size)
            if d is not None:
                return d
        return None


class PatchVersion(object):
    def __init__(self, version, sources, base):
        self.version = version
        folder = os.path.join(sources, version)
        self.archive = _open_mpq(os.path.join(folder, 'Patch_War3x.mpq'))
        self.base = base
        self.entries = {}
        raw = _read_mpq(self.archive, 'patch.lst') or b''
        for line in raw.decode('latin-1').replace('\r', '\n').split('\n'):
            parts = line.split(';')
            if len(parts) >= 2 and parts[0].strip() and parts[1].strip():
                self.entries[parts[0].strip().lower()] = (parts[0].strip(), parts[1].strip())
        if not self.entries:
            raise VersionError('%s: the patch has no patch.lst' % version)
        self.approximate = []
        self.decoded = {}
        self.failed = []

    def names(self):
        out = self.base.names()
        out.update((k, v[0]) for k, v in self.entries.items())
        return out

    def read(self, path):
        low = path.replace('/', '\\').lower()
        ent = self.entries.get(low)
        if ent is None:
            d, approx = self.base.read(path)
            if approx:
                self.approximate.append(path)
            return d
        entry = _read_mpq(self.archive, ent[1])
        if entry is None:
            self.failed.append((path, 'the patch lists it but has no entry %s' % ent[1]))
            return None
        h = bnupdate_header(entry)
        if h is None:
            self.failed.append((path, 'no BNUpdate header'))
            return None
        src = None
        if h['kind'] == BNU_BSDIFF:
            src = self.base.source(ent[0], h['source_crc'], h['source_size'])
            if src is None:
                self.failed.append((path, 'no base file with the CRC32 %08X' % h['source_crc']))
                return None
        out = bnupdate_apply(entry, src)
        self.decoded[low] = (h['size'], h['filetime'], hashlib.sha1(out).hexdigest(), h['kind'])
        return out


class FolderVersion(object):
    def __init__(self, version, sources):
        self.version = version
        self.chain = MpqChain([os.path.join(sources, version, n) for n in FOLDER_ARCHIVES])
        if not self.chain.archives:
            raise VersionError('%s: no MPQ in %s' % (version, os.path.join(sources, version)))
        self.approximate, self.decoded, self.failed = [], {}, []

    def names(self):
        return self.chain.names()

    def read(self, path):
        return self.chain.read(path)


def _sha1(b):
    return hashlib.sha1(b).hexdigest()


def _put_object(data_root, blob):
    sha = _sha1(blob)
    p = os.path.join(data_root, OBJECTS, sha)
    if not os.path.isfile(p):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p + '.part', 'wb') as f:
            f.write(blob)
        os.replace(p + '.part', p)
    return sha


def _write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


def _scripts_folder_name(first_version, taken):
    k = _key(first_version)
    short = '%d.%02d' % (k[0], k[1])
    return first_version if short in taken else short


def build(versions=None, sources=None, data=None, ref=None, work=None, log=print, jassdoc=None):
    sources = sources or sources_dir()
    data = data or data_dir()
    ref = ref or REF_ROOT
    work = work or os.path.join(COMMON, 'cache', 'wc3_versoes_work')
    wanted = [normalize(v) for v in versions] if versions else list(CLASSIC)
    if None in wanted or REFORGED in wanted:
        raise VersionError('build takes classic versions only: %s' % ', '.join(CLASSIC))
    order = [v for v in CLASSIC if v in wanted]
    report = {'versions': {}, 'scripts': {}, 'cross_check': {'equal': 0, 'different': []}}
    base = None
    whole_127b = {}
    decoded_all = {}
    scripts_by_version = {}
    for v in order:
        kind = dict(SOURCES)[v]
        log('%s: reading the %s' % (v, 'patch over the 1.21b base' if kind == 'patch' else 'game folder'))
        if kind == 'patch':
            if base is None:
                base = Base(sources, work)
            src = PatchVersion(v, sources, base)
        else:
            src = FolderVersion(v, sources)
        names = src.names()
        objects, md5s, total = {}, {}, 0
        for low in sorted(names):
            path = names[low]
            if not pack_patterns_match(path):
                continue
            blob = src.read(path)
            if blob is None:
                continue
            key = casc_path(path).lower()
            objects[key] = _put_object(data, blob)
            md5s[key] = hashlib.md5(blob).hexdigest()
            total += len(blob)
        scripts = {}
        for f in SCRIPTS:
            blob = src.read('Scripts\\' + f)
            if blob is None:
                raise VersionError('%s has no Scripts\\%s' % (v, f))
            scripts[f] = blob
        scripts_by_version[v] = scripts
        paths = sorted(set(casc_path(n) for n in names.values()), key=str.lower)
        folder = os.path.join(data, v)
        _write_text(os.path.join(folder, PACK_LIST), '\n'.join(paths) + '\n')
        manifest = {'version': v, 'build_key': 'mpq-' + v, 'total': len(paths), 'patterns': list(DATA_PATTERNS),
                    'bytes': total, 'files': md5s, 'objects': objects, 'store': '../' + OBJECTS,
                    'approximate': sorted(set(casc_path(p) for p in src.approximate), key=str.lower)}
        _write_text(os.path.join(folder, PACK_MANIFEST), json.dumps(manifest, indent=1, sort_keys=True) + '\n')
        decoded_all[v] = dict(src.decoded)
        if v == '1.27b':
            whole_127b = dict((k, x) for k, x in src.decoded.items() if x[3] == BNU_WHOLE)
        report['versions'][v] = {'files': len(objects), 'bytes': total, 'paths': len(paths),
                                 'approximate': len(manifest['approximate']), 'failed': list(src.failed),
                                 'diffs': sum(1 for x in src.decoded.values() if x[3] == BNU_BSDIFF),
                                 'whole': sum(1 for x in src.decoded.values() if x[3] == BNU_WHOLE)}
        log('  %d files (%.1f MB), %d paths, %d diffs applied, %d whole, %d approximate, %d failed' % (
            len(objects), total / 1048576.0, len(paths), report['versions'][v]['diffs'],
            report['versions'][v]['whole'], len(manifest['approximate']), len(src.failed)))
    for v, dec in decoded_all.items():
        if v == '1.27b':
            continue
        for low, (size, ft, sha, kind) in dec.items():
            w = whole_127b.get(low)
            if w and kind == BNU_BSDIFF and (w[0], w[1]) == (size, ft):
                if w[2] == sha:
                    report['cross_check']['equal'] += 1
                else:
                    report['cross_check']['different'].append('%s %s' % (v, low))
    log('cross check against the whole files of 1.27b: %d equal, %d different' % (
        report['cross_check']['equal'], len(report['cross_check']['different'])))
    idx = index_from_disk(ref)
    groups = {}
    for v in order:
        sig = tuple(_sha1(scripts_by_version[v][f]) for f in SCRIPTS)
        groups.setdefault(sig, []).append(v)
    known = dict((tuple(x[f] for f in SCRIPTS), name) for name, x in (idx.get('scripts') or {}).items())
    for sig, vs in groups.items():
        name = known.get(sig) or _scripts_folder_name(vs[0], set(known.values()) | set(idx.get('scripts') or {}))
        known[sig] = name
        for root in (os.path.join(ref, name), os.path.join(data, 'ref', name)):
            os.makedirs(root, exist_ok=True)
            for f in SCRIPTS:
                with open(os.path.join(root, f), 'wb') as fh:
                    fh.write(scripts_by_version[vs[0]][f])
        idx.setdefault('scripts', {})[name] = dict(zip(SCRIPTS, sig))
        for v in vs:
            idx.setdefault('versions', {})[v] = {'scripts': name, 'range': range_of(v)}
        report['scripts'][name] = vs
        log('scripts %s: %s' % (name, ', '.join(vs)))
    idx['versions'] = dict(sorted(idx.get('versions', {}).items(), key=lambda kv: _key(kv[0])))
    idx['scripts'] = dict(sorted(idx['scripts'].items()))
    text = json.dumps(idx, indent=1) + '\n'
    _write_text(os.path.join(ref, INDEX_NAME), text)
    _write_text(os.path.join(data, 'ref', INDEX_NAME), text)
    _INDEX.clear()
    table, notes = natives_table(ref, jassdoc)
    if table:
        text = json.dumps(table, indent=0, sort_keys=True) + '\n'
        _write_text(os.path.join(ref, NATIVES_NAME), text)
        _write_text(os.path.join(data, 'ref', NATIVES_NAME), text)
        _NATIVES.clear()
    report['natives'] = notes
    log('natives ruler: %s' % notes)
    return report


def index_from_disk(ref):
    p = os.path.join(ref, INDEX_NAME)
    if os.path.isfile(p):
        with open(p, encoding='utf-8') as f:
            return json.load(f)
    return {}


RX_DECL = re.compile(r'^\s*(?:constant\s+)?native\s+(\w+)|^\s*function\s+(\w+)|^\s*type\s+(\w+)|'
                     r'^\s*(?:constant\s+)?\w+\s+(?:array\s+)?(\w+)\s*=')
RX_NATIVE = re.compile(r'(?m)^\s*(?:constant\s+)?native\s+(\w+)')
RX_FUNCTION = re.compile(r'(?m)^\s*function\s+(\w+)')
JASSDOC = os.path.normpath(os.path.join(COMMON, '..', 'terceiros', 'jassdoc'))


def _jassdoc_patches(path):
    out = {}
    patch = None
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            m = re.search(r'@patch\s+(\S+)', line)
            if m:
                patch = m.group(1)
                continue
            if patch is None or line.lstrip().startswith(('//', '/**', '*')):
                continue
            d = RX_DECL.match(line)
            if d:
                name = next(g for g in d.groups() if g)
                out.setdefault(name, patch)
                patch = None
    return out


def _declared(folder):
    names = set()
    for f in SCRIPTS:
        p = os.path.join(folder, f)
        if os.path.isfile(p):
            with open(p, encoding='latin-1') as fh:
                t = fh.read()
            names.update(RX_NATIVE.findall(t))
            names.update(RX_FUNCTION.findall(t))
    return names


def natives_table(ref=None, jassdoc=None):
    ref = ref or REF_ROOT
    jassdoc = jassdoc or JASSDOC
    doc = {}
    for f in ('common.j', 'Blizzard.j', 'common.ai'):
        p = os.path.join(jassdoc, f)
        if os.path.isfile(p):
            for k, v in _jassdoc_patches(p).items():
                doc.setdefault(k, v)
    if not doc:
        return None, 'no jassdoc in %s: the ruler was not made' % jassdoc
    idx = index_from_disk(ref)
    first = {}
    for name, x in sorted((idx.get('scripts') or {}).items(), key=lambda kv: _key(kv[0])):
        first_version = min((v for v, y in (idx.get('versions') or {}).items() if y.get('scripts') == name), key=_key)
        for n in _declared(os.path.join(ref, name)):
            if n not in first or _key(first_version) < _key(first[n]):
                first[n] = first_version
    corrected, undated = 0, 0
    table = dict(doc)
    for n, v in first.items():
        if n not in table:
            table[n] = v
        elif _key(table[n]) > _key(v):
            table[n] = v
            corrected += 1
    for n in _declared(os.path.join(ref, REFORGED)):
        if n not in table:
            table[n] = '1.30'
            undated += 1
    out = {}
    for n, v in table.items():
        out.setdefault(v, []).append(n)
    for v in out:
        out[v].sort()
    return {'patches': out}, '%d names, %d dated by our scripts, %d only in 3.0 without a jassdoc date' % (
        len(table), corrected, undated)


_NATIVES = {}


def natives_patches():
    if 't' not in _NATIVES:
        _NATIVES['t'] = {}
        for root in _ref_roots():
            p = os.path.join(root, NATIVES_NAME)
            if os.path.isfile(p):
                with open(p, encoding='utf-8') as f:
                    t = json.load(f)
                _NATIVES['t'] = dict((n, v) for v, ns in (t.get('patches') or {}).items() for n in ns)
                break
    return _NATIVES['t']


def first_patch(name):
    return natives_patches().get(name)


RX_JASS_NOISE = re.compile(r'//[^\n]*|"(?:[^"\\\n]|\\.)*"|\'[^\'\n]*\'')
RX_IDENT = re.compile(r'\b[A-Za-z_]\w*\b')
RX_RETURN_BUG = re.compile(r'(?m)^\s*function\s+\w+\s+takes\s+\w+\s+\w+\s+returns\s+\w+\s*\n\s*return\s+\w+\s*\n\s*'
                           r'return\s+(?:0|null|0\.0|false|"")\s*\n\s*endfunction')
EDITOR_129 = 6060


RX_GLOBALS = re.compile(r'(?ms)^\s*globals\b(.*?)^\s*endglobals')
RX_GLOBAL = re.compile(r'(?m)^\s*(?:constant\s+)?\w+\s+(?:array\s+)?(\w+)')


def script_names(text):
    clean = RX_JASS_NOISE.sub(' ', text.replace('\r\n', '\n').replace('\r', '\n'))
    defined = set(RX_FUNCTION.findall(clean))
    for block in RX_GLOBALS.findall(clean):
        defined.update(RX_GLOBAL.findall(block))
    return set(RX_IDENT.findall(clean)), defined, set(RX_NATIVE.findall(clean))


def _bump(state, rng, reason):
    state['reasons'].append(reason)
    if RANGE_ORDER.index(rng) > RANGE_ORDER.index(state['range']):
        state['range'] = rng


def _range_of_patch(patch):
    k = _key(patch)
    if k >= (1, 30, 0):
        return '1.30+'
    if k >= (1, 29, 0):
        return '1.29'
    return '1.24-1.28'


def detect_parts(w3i_bytes=None, script=None, language=None, objects=None, wtg=None, size=None, platform=None):
    st = {'range': '1.24-1.28', 'reasons': [], 'minimum': None, 'w3i': None, 'players': None, 'return_bug': False}
    if w3i_bytes:
        try:
            from doctor.data import w3i
            m = w3i.parse_or_tolerant(w3i_bytes)
        except Exception:
            m = None
        if m:
            fmt, editor = m.get('version'), m.get('editor_version')
            gv = m.get('game_version')
            st['w3i'] = {'format': fmt, 'editor': editor, 'game': '.'.join(str(x) for x in gv) if gv else None}
            st['players'] = len(m.get('players') or [])
            if gv and fmt >= 28:
                game_text = '.'.join(str(x) for x in gv)
                _bump(st, '1.30+' if tuple(gv[:2]) >= (1, 30) else _range_of_patch(game_text),
                      'the map info (w3i format %d) was saved by the %s World Editor' % (fmt, game_text))
            elif fmt == 18:
                st['reasons'].append('the map info is in the Reign of Chaos format (w3i 18)')
            elif fmt is not None and fmt >= 28:
                _bump(st, '1.30+', 'the map info is in format %d, which 1.31 and later write' % fmt)
            if fmt is not None and fmt < 28 and editor and editor >= EDITOR_129:
                _bump(st, '1.29', 'saved by World Editor %d (1.29 or newer)' % editor)
            if st['players'] and st['players'] > 12:
                _bump(st, '1.29', '%d player slots: more than 12 came with 1.29' % st['players'])
    if platform:
        st['reasons'].append(platform)
    platform = 1 if platform else 0
    if language == 'lua':
        _bump(st, '1.30+', 'the script is Lua, which came with 1.31')
    elif script:
        used, defined, declared = script_names(script)
        table = natives_patches()
        newest, newest_name = None, None
        later = {}
        own = len([n for n in declared if n not in table])
        platform += own
        if own:
            st['reasons'].append('the script declares %d natives no Blizzard game has (a platform client: KK, JAPI, '
                                 'JN, YDWE)' % own)
        for n in sorted(used - defined):
            p = table.get(n)
            if p is None:
                continue
            if newest is None or _key(p) > _key(newest):
                newest, newest_name = p, n
            if _key(p) >= (1, 29, 0):
                later.setdefault(_range_of_patch(p), []).append(n)
        if newest:
            st['minimum'] = newest
        for rng in ('1.29', '1.30+'):
            if later.get(rng):
                names = sorted(later[rng])
                _bump(st, rng, 'the script uses %d natives or constants that came in %s or later (%s)' % (
                    len(names), '1.29' if rng == '1.29' else '1.30', ', '.join(names[:5]) +
                    (', ...' if len(names) > 5 else '')))
        if RX_RETURN_BUG.search(script):
            st['return_bug'] = True
            if st['range'] == '1.24-1.28' and (newest is None or _key(newest) < (1, 24, 1)):
                st['range'] = 'pre-1.24'
                st['reasons'].append('the script uses the return bug (a handle returned as an integer), which only '
                                     '1.23 and older run')
            else:
                st['reasons'].append('the script has a return bug function, which 1.24 and later refuse')
        if newest and not later and newest_name:
            st['reasons'].append('the newest native it uses is %s (%s)' % (newest_name, newest))
    for name, data in sorted((objects or {}).items()):
        if data and len(data) >= 4 and struct.unpack_from('<i', data, 0)[0] >= 3:
            _bump(st, '1.30+', '%s is in the object data format 3 (1.33 and later)' % name)
            break
    if wtg and len(wtg) >= 8 and wtg[:4] == b'WTG!' and struct.unpack_from('<I', wtg, 4)[0] & 0x80000000:
        _bump(st, '1.30+', 'the triggers (war3map.wtg) are in the format of 1.31 and later')
    if size and size > LIMIT_DEFAULT['map_bytes']:
        st['reasons'].append('the map is %.1f MB, above the 8 MB of 1.24 to 1.28: %s' % (
            size / 1048576.0, 'the platform client lifts that limit' if platform else
            'made for 1.29 or later, or for a client or loader that lifts the limit'))
    if not st['reasons']:
        st['reasons'].append('nothing newer than the 1.24 to 1.28 game was found')
    st['version'] = dict(RANGES).get(st['range'])
    st['label'] = {'pre-1.24': '1.23 or older', '1.24-1.28': '1.24 to 1.28', '1.29': '1.29',
                   '1.30+': '1.30 or newer (Reforged)'}[st['range']]
    return st


OBJECT_FILES = ('war3map.w3u', 'war3map.w3t', 'war3map.w3a', 'war3map.w3b', 'war3map.w3d', 'war3map.w3h',
                'war3map.w3q')


def detect(path):
    a = _open_mpq(path)

    def rd(n):
        return _read_mpq(a, n)
    lang, script = None, None
    lua = rd('war3map.lua')
    if lua is not None:
        lang, script = 'lua', lua.decode('utf-8', 'surrogateescape')
    else:
        j = rd('war3map.j') or rd('scripts\\war3map.j')
        if j is not None:
            lang, script = 'jass', j.decode('utf-8', 'surrogateescape')
    objects = dict((n, rd(n)) for n in OBJECT_FILES)
    return detect_parts(rd('war3map.w3i'), script, lang, objects, rd('war3map.wtg'), os.path.getsize(path))


def pjass_check(script, version, own_blizzard=None):
    import shutil
    import tempfile
    folder = scripts_dir(version)
    if folder is None:
        return {'skipped': 'no scripts of %s' % version}
    try:
        from doctor.script import jass_ast
        pj = jass_ast._load_pjass()
    except Exception as e:
        return {'skipped': 'pjass: %s' % e}
    if pj is None:
        return {'skipped': 'no pjass'}
    tmp = tempfile.mkdtemp(prefix='wc3_versions_')
    try:
        files = []
        with open(os.path.join(folder, 'blizzard.j'), 'rb') as f:
            blizzard = f.read()
        with open(os.path.join(folder, 'common.j'), 'rb') as f:
            common = f.read()
        for name, blob in (('common.j', common), ('Blizzard.j', own_blizzard or blizzard), ('war3map.j', script)):
            p = os.path.join(tmp, name)
            with open(p, 'wb') as f:
                f.write(lf_outside_rawcodes(blob))
            files.append(p)
        r = pj.compiles(files, tmp=tmp)
        return {'rc': r['rc'], 'errors': list(r['error_list']), 'warnings': list(r['warnings'])}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


RX_LINE_BREAKS = re.compile(rb"//[^\r\n]*|\"(?:[^\"\\\r\n]|\\.)*\"|'[^']{1,4}'|\r\n|\r")


def lf_outside_rawcodes(blob):
    if not isinstance(blob, bytes):
        blob = blob.encode('utf-8', 'surrogateescape')
    if blob.startswith(b'\xef\xbb\xbf'):
        blob = blob[3:]
    return RX_LINE_BREAKS.sub(lambda m: b'\n' if m.group(0) in (b'\r\n', b'\r') else m.group(0), blob)


def pack(to, data=None):
    import zipfile
    data = data or data_dir()
    n = 0
    with zipfile.ZipFile(to + '.part', 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for dirpath, _dirs, files in os.walk(data):
            for f in sorted(files):
                if f.endswith('.part'):
                    continue
                full = os.path.join(dirpath, f)
                z.write(full, os.path.relpath(full, data).replace('\\', '/'))
                n += 1
    os.replace(to + '.part', to)
    return {'files': n, 'bytes': os.path.getsize(to)}


def unpack(zip_path, data=None):
    import shutil
    import zipfile
    data = data or data_dir()
    n = 0
    fresh = not os.path.exists(data)
    out_dir = data + '.part' if fresh else data
    if fresh and os.path.isdir(out_dir):
        shutil.rmtree(out_dir, ignore_errors=True)
    with zipfile.ZipFile(zip_path) as z:
        for info in z.infolist():
            name = info.filename
            if name.startswith(('/', '\\')) or '..' in name.replace('\\', '/').split('/') or ':' in name:
                raise VersionError('a name outside the data folder in the zip: %s' % name)
            if name.endswith('/'):
                continue
            dst = os.path.join(out_dir, *name.split('/'))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with z.open(info) as src, open(dst + '.part', 'wb') as out:
                out.write(src.read())
            os.replace(dst + '.part', dst)
            n += 1
    if fresh:
        os.rename(out_dir, data)
    _GAMES.clear()
    _INDEX.clear()
    _NATIVES.clear()
    return {'files': n}

