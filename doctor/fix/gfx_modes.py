# Finds the game files a map uses that some graphics mode lacks, and copies them into the map.
import collections
import os
import re
import struct
import zlib


B = chr(92)
MODES = ('sd', 'hd', 'de')
MODE_NAMES = {'sd': 'Classic', 'hd': 'Reforged', 'de': 'Definitive Edition'}
ROOT = 'war3.w3mod:'
CHAINS = {'sd': ('',), 'hd': ('_hd.w3mod:', ''), 'de': ('_de.w3mod:', '_hd.w3mod:', '')}
PREFERENCE = ('de', 'hd', 'sd')
LIMIT = 512 * 1024 * 1024
MARGIN = 2 * 1024 * 1024
IMAGE = ('.dds', '.blp', '.tga', '.tif', '.png')
MODEL = ('.mdx', '.mdl')
SOUND = ('.flac', '.ogg', '.wav', '.mp3')
ART_EXT = IMAGE + MODEL + SOUND + ('.pkb',)
RX_PATH = re.compile(r'([A-Za-z0-9_\-\.\$ \\/]+\.(?:mdx|mdl|blp|dds|tga|tif|png|wav|mp3|flac|ogg|pkb))(?![A-Za-z0-9])',
                     re.I)
RX_FILE_MODE = re.compile(r'(?i)file(?::(sd|hd|de))?\s*=\s*(.*)$')
RX_FILE_KEY = re.compile(r'(?im)^\s*file\s*=\s*"?([^"\r\n,]+?)"?\s*$')
TEXT_EXT = ('.txt', '.slk', '.fdf', '.toc')
OBJECTS = ('w3u', 'w3t', 'w3a', 'w3b', 'w3d', 'w3h', 'w3q')
LEVELS = ('w3a', 'w3d', 'w3q')
VARIATIONS = frozenset(('dfil', 'bfil'))
BULK = 20


def _nothing(*_a, **_k):
    pass


def norm(path):
    p = (path or '').strip().strip('"').replace('/', B)
    p = re.sub(r'\\+', lambda _m: B, p)
    return p.lstrip(B).lower()


def forms(path):
    p = norm(path)
    stem, ext = os.path.splitext(p)
    if ext in IMAGE:
        return [stem + e for e in IMAGE]
    if ext in MODEL:
        return [stem + '.mdx', stem + '.mdl']
    if ext in SOUND:
        return [stem + e for e in SOUND]
    return [p]


def looks_like_art(p):
    return os.path.splitext(p)[1] in ART_EXT and ':' not in p and len(p) < 260


class Layers(object):
    def __init__(self, casc, tileset=''):
        self.casc = casc
        self.tileset = (tileset or '').lower()
        self.layer = {}
        subs = set()
        for mode in MODES:
            subs.update(self._chain(mode))
        prefixes = sorted(set(ROOT + s for s in subs), key=len, reverse=True)
        for k in casc.file_set:
            if not k.startswith(ROOT):
                continue
            for pre in prefixes:
                if k.startswith(pre):
                    rest = k[len(pre):]
                    if ':' in rest:
                        break
                    self.layer[(pre[len(ROOT):], rest)] = k
                    break

    def _chain(self, mode):
        out = []
        for s in CHAINS[mode]:
            if self.tileset:
                out.append(s + '_tilesets' + B + self.tileset + '.w3mod:')
            out += [s, s + '_locales' + B + 'enus.w3mod:']
        return out

    def find(self, path, mode):
        fs = forms(path)
        for sub in self._chain(mode):
            for f in fs:
                k = self.layer.get((sub, f))
                if k:
                    return k
        return None

    def where(self, path):
        return dict((m, k) for m in MODES for k in [self.find(path, m)] if k)

    def read(self, key):
        try:
            return self.casc.read_data(key)
        except Exception:
            return None


def _objects(d, levels):
    from doctor.data import skin_split
    _v, objs, _end = skin_split._parse(d, levels)
    out = []
    for table, ids, sets in objs:
        vals = []
        for _flag, mods in sets:
            for field, start, end in mods:
                p = start + (16 if levels else 8)
                kind = struct.unpack_from('<I', d, start + 4)[0]
                if kind == 3:
                    vals.append((field, d[p:end - 4].split(b'\0', 1)[0].decode('utf-8', 'replace')))
        out.append((table, ids[:4].decode('latin-1'), ids[4:8].decode('latin-1'), vals))
    return out


def _model_paths(field, value, nvar=None):
    from doctor.fix import model_paths
    out = []
    for part in value.split(','):
        p = norm(part)
        if not p or p in ('.mdl', '.mdx', '_', 'none'):
            continue
        ext = os.path.splitext(p)[1]
        if ext not in ART_EXT:
            if field not in model_paths.FALLBACK_FIELDS or ext:
                continue
            p += '.mdx'
            ext = '.mdx'
        if field in VARIATIONS and ext in MODEL:
            stem = os.path.splitext(p)[0]
            out.append(stem + '.mdx')
            out += [stem + str(i) + '.mdx' for i in range(max(1, nvar or 1))]
        else:
            out.append(p)
    return out


def _slk_rows(data, key_col, cols):
    from doctor.data import slk_cols
    line_list, _crlf = slk_cols.lines_of(data)
    names = {}
    grid = collections.defaultdict(dict)
    for _i, x, y, k in slk_cols.slk_cells(line_list):
        if k is None or x is None or y is None:
            continue
        v = k.strip('"')
        if y == 1:
            names[x] = v
        else:
            grid[y][x] = v
    inv = dict((v, k) for k, v in names.items())
    if key_col not in inv:
        return {}
    out = {}
    for _y, row in grid.items():
        rid = row.get(inv[key_col])
        if rid:
            out[rid] = dict((c, row.get(inv[c])) for c in cols if c in inv)
    return out


def _ini_files(text):
    out = {}
    sec = None
    for line in text.splitlines():
        s = line.strip()
        if s.startswith('[') and ']' in s:
            sec = s[1:s.index(']')]
            continue
        m = RX_FILE_MODE.match(s)
        if sec and m:
            out.setdefault(sec, {}).setdefault((m.group(1) or '').lower(), m.group(2).strip().strip('"'))
    return out


def _per_mode(value):
    if not isinstance(value, dict):
        return dict((m, value) for m in MODES)
    return dict((m, value.get(m) or value.get('')) for m in MODES if value.get(m) or value.get(''))


def _game_tables(casc):
    out = {}
    for name, key, nvar in (('doodads' + B + 'doodads.slk', 'doodID', 'numVar'),
                            ('units' + B + 'destructabledata.slk', 'DestructableID', 'numVar')):
        try:
            rows = _slk_rows(casc.read_data(ROOT + name), key, ('file', nvar))
        except Exception:
            continue
        for rid, r in rows.items():
            if r.get('file'):
                try:
                    n = int(float(r.get(nvar) or 1))
                except ValueError:
                    n = 1
                out[rid] = ('dfil', r['file'], n)
    try:
        for rid, f in _ini_files(
            casc.read_data(ROOT + 'units' + B + 'unitskin.txt').decode('utf-8', 'replace')
        ).items():
            out.setdefault(rid, ('umdl', f, 1))
    except Exception:
        pass
    return out


def _add_base(add, base, src):
    field, value, nvar = base
    per = _per_mode(value)
    every = len(set(per.values())) == 1 and len(per) == len(MODES)
    for mode, v in sorted(per.items()):
        for path in _model_paths(field, v, nvar):
            add(path, src if every else '@%s %s' % (mode, src))


def references(a, names, casc=None, progress=None):
    from doctor.fix import unprotect
    from doctor.viewers import map_files
    p = progress or _nothing
    refs = collections.defaultdict(set)

    def add(path, src):
        n = norm(path)
        if looks_like_art(n):
            refs[n].add(src)

    by_lower = dict((n.lower(), n) for n in names)
    models = [n for n in names if os.path.splitext(n)[1].lower() in MODEL]
    for i, n in enumerate(models):
        if i % 200 == 0:
            p('Reading the models %d/%d' % (i, len(models)))
        d = unprotect._read(a, n)
        if not d:
            continue
        try:
            for r in map_files.model_refs(d):
                add(r, 'model')
        except Exception:
            continue
    p('Reading the object data')
    tables = _game_tables(casc) if casc is not None else {}
    custom = {}
    nvars = {}
    for kind in OBJECTS:
        for name in ('war3map.' + kind, 'war3mapSkin.' + kind):
            d = unprotect._read(a, name)
            if not d:
                continue
            try:
                objs = _objects(d, kind in LEVELS)
            except Exception:
                continue
            for table, parent, new, vals in objs:
                oid = new if table == 1 and new.strip('\0') else parent
                ent = custom.setdefault(oid, [parent, {}])
                for field, value in vals:
                    ent[1][field] = value
                    if field in ('dvar', 'bvar'):
                        try:
                            nvars[oid] = int(value)
                        except ValueError:
                            pass
    for oid, (parent, fields) in custom.items():
        for field, value in fields.items():
            for path in _model_paths(field, value, nvars.get(oid)):
                add(path, 'object:' + oid)
        base = tables.get(parent)
        if base and base[0] not in fields and not ({'dfil', 'bfil', 'umdl'} & set(fields)):
            _add_base(add, base, 'object:' + oid)
    doo = unprotect._read(a, 'war3map.doo')
    if doo and tables:
        try:
            from doctor.fix import doodads
            for rid in doodads.ids(doo):
                rid = rid.decode('latin-1')
                if rid in custom or rid not in tables:
                    continue
                _add_base(add, tables[rid], 'placed:' + rid)
        except Exception:
            pass
    for n in names:
        low = n.lower()
        if not (low.endswith(TEXT_EXT) and (low.startswith(('units' + B, 'ui' + B, 'terrainart' + B, 'doodads' + B,
                                                              'war3mapimported' + B, 'splats' + B))
                                            or low in ('war3mapskin.txt', 'war3mapmisc.txt'))):
            continue
        d = unprotect._read(a, n)
        if not d:
            continue
        t = d.decode('utf-8', 'replace')
        for m in RX_PATH.finditer(t):
            add(m.group(1), os.path.basename(low))
        for m in RX_FILE_KEY.finditer(t):
            v = m.group(1).strip()
            if v and not os.path.splitext(v)[1]:
                add(v + '.mdx', os.path.basename(low))
    w3i = unprotect._read(a, 'war3map.w3i')
    if w3i:
        try:
            from doctor.data import w3i as w3imod
            m = w3imod.parse(w3i)
            for k in ('loading_model', 'prologue_model'):
                v = m.get(k)
                if isinstance(v, bytes):
                    v = v.decode('utf-8', 'replace')
                if v:
                    add(v if os.path.splitext(v)[1] else v + '.mdx', 'w3i')
        except Exception:
            pass
    return refs, by_lower


def _tileset(a):
    from doctor.fix import unprotect
    d = unprotect._read(a, 'war3map.w3i')
    try:
        from doctor.data import w3i as w3imod
        return (w3imod.parse(d).get('tileset') or b'').decode('latin-1').strip('\0')
    except Exception:
        return ''


def terrain(a, casc=None):
    from doctor.fix import unprotect
    w3e = unprotect._read(a, 'war3map.w3e')
    if not w3e or w3e[:4] != b'W3E!' or len(w3e) < 17:
        return []
    try:
        n = struct.unpack_from('<i', w3e, 13)[0]
        ground = [w3e[17 + 4 * i:21 + 4 * i].decode('latin-1') for i in range(n)]
        p = 17 + 4 * n
        nc = struct.unpack_from('<i', w3e, p)[0]
        cliffs = [w3e[p + 4 + 4 * i:p + 8 + 4 * i].decode('latin-1') for i in range(nc)]
    except (struct.error, ValueError):
        return []
    out = []
    for table, key, d_col, f_col, ids, kind in (
            ('TerrainArt' + B + 'Terrain.slk', 'tileID', 'dir', 'file', ground, 'tile'),
            ('TerrainArt' + B + 'CliffTypes.slk', 'cliffID', 'texDir', 'texFile', cliffs, 'cliff')):
        rows = {}
        if casc is not None:
            try:
                rows = _slk_rows(casc.read_data(ROOT + table.lower()), key, (d_col, f_col))
            except Exception:
                rows = {}
        mine = unprotect._read(a, table)
        if mine:
            try:
                rows.update(_slk_rows(mine, key, (d_col, f_col)))
            except Exception:
                pass
        for tid in ids:
            r = rows.get(tid) or {}
            if r.get(d_col) and r.get(f_col):
                out.append((r[d_col].rstrip(B) + B + r[f_col], kind, tid))
    return out


def _map_has(path, mode, in_map):
    folders = [s.replace(':', B) for s in CHAINS[mode] if s]
    for f in forms(path):
        if f in in_map or any(d + f in in_map for d in folders):
            return True
    return False


def _terrain_missing(stem, mode, in_map, layers):
    s = norm(stem)
    want = [s + '.dds'] if mode == 'sd' else [s + '_diffuse.dds', s + '.dds']
    for w in want:
        if _map_has(w, mode, in_map) or layers.find(w, mode):
            return False
    return True


def _model_refs(data, cache, key):
    from doctor.viewers import map_files
    if key in cache:
        return cache[key]
    out = []
    if data:
        try:
            out = [r for r in (norm(x) for x in map_files.model_refs(data)) if looks_like_art(r)]
        except Exception:
            out = []
    cache[key] = out
    return out


class Analysis(object):
    def __init__(self, refs, by_lower, layers, added=None, cache=None, ground=None):
        self.layers = layers
        self.cache = {} if cache is None else cache
        self.missing = dict((m, {}) for m in MODES)
        self.where = {}
        self.nowhere = set()
        self.examined = set()
        self.derive = {}
        self.ground = list(ground or [])
        added = added or {}
        in_map = set(by_lower)
        for k in added:
            in_map.update(forms(k))
        base = collections.defaultdict(set)
        for r, s in refs.items():
            base[r].update(s)
        for k, d in added.items():
            if os.path.splitext(k)[1] in MODEL:
                for r in _model_refs(d, self.cache, 'added:%s:%d:%d' % (k, len(d), zlib.crc32(d))):
                    base[r].add('imported ' + k)
        for mode in MODES:
            self._mode(mode, base, in_map)
        for stem, kind, tid in self.ground:
            for mode in MODES:
                if not _terrain_missing(stem, mode, in_map, layers):
                    continue
                diffuse = norm(stem) + '_diffuse.dds'
                if mode == 'sd' and layers.where(diffuse):
                    path = norm(stem) + '.blp'
                    self.missing[mode].setdefault(path, set()).add('terrain %s %s' % (kind, tid))
                    self.derive[path] = (stem, diffuse)
                elif layers.where(norm(stem) + '.dds'):
                    path = norm(stem) + '.dds'
                    self.missing[mode].setdefault(path, set()).add('terrain %s %s' % (kind, tid))

    def _mode(self, mode, base, in_map):
        queue = list(base.items())
        seen = set()
        while queue:
            path, srcs = queue.pop()
            if srcs and all(x.startswith('@') for x in srcs):
                if not any(x.startswith('@%s ' % mode) for x in srcs):
                    continue
                srcs = set(x.split(' ', 1)[1] for x in srcs if x.startswith('@%s ' % mode))
            key = forms(path)[0]
            if key in seen:
                if path in self.missing[mode]:
                    self.missing[mode][path].update(srcs)
                continue
            seen.add(key)
            self.examined.add(key)
            if _map_has(path, mode, in_map):
                continue
            ck = self.layers.find(path, mode)
            if ck is None:
                w = self.where.get(key)
                if w is None:
                    w = self.where[key] = self.layers.where(path)
                if w:
                    self.missing[mode][path] = set(srcs)
                else:
                    self.nowhere.add(key)
                continue
            if os.path.splitext(path)[1] in MODEL:
                for r in _model_refs(None if ck in self.cache else self.layers.read(ck), self.cache, ck):
                    queue.append((r, set(['game model ' + path])))

    def counts(self):
        return dict((m, len(self.missing[m])) for m in MODES)

    def modes_ok(self):
        return [m for m in MODES if not self.missing[m]]

    def reference(self):
        c = self.counts()
        return min(MODES, key=lambda m: (c[m], PREFERENCE.index(m)))


def _analyse(a, names, layers, progress=None):
    p = progress or _nothing
    refs, by_lower = references(a, names, layers.casc, p)
    p('Looking the paths up in the game layers')
    cache = game_refs(layers.casc)
    n = len(cache)
    an = Analysis(refs, by_lower, layers, cache=cache, ground=terrain(a, layers.casc))
    if len(cache) != n:
        _save_game_refs(layers.casc, cache)
    return refs, by_lower, an


_GAME_REFS = {}


def _game_refs_key(casc):
    from doctor.data import memo
    return memo.key('gfx_modes', 1, getattr(casc, 'game', ''), getattr(casc, 'build_key', ''))


def game_refs(casc):
    key = id(casc)
    if key not in _GAME_REFS:
        got = None
        try:
            from doctor.data import memo
            got = memo.load('gfxrefs', _game_refs_key(casc))
        except Exception:
            got = None
        _GAME_REFS[key] = got if isinstance(got, dict) else {}
    return _GAME_REFS[key]


def _save_game_refs(casc, cache):
    try:
        from doctor.data import memo
        memo.save('gfxrefs', _game_refs_key(casc), dict((k, v) for k, v in cache.items() if not k.startswith('added:')))
    except Exception:
        pass


TERRAIN_SCALE = 4


def classic_tile(diffuse_dds, scale=TERRAIN_SCALE):
    import io
    from doctor.models import blpwrite
    from PIL import Image
    im = Image.open(io.BytesIO(diffuse_dds))
    im.load()
    im = im.convert('RGBA')
    size = (max(16, im.size[0] // scale), max(16, im.size[1] // scale))
    if im.size != size:
        im = im.resize(size, Image.LANCZOS)
    return blpwrite.blp_jpeg_bytes(im, 90, alpha_bits=8)[1]


def _open_game(casc=None):
    if casc is not None:
        return casc
    try:
        from doctor.data import casc_wc3
        return casc_wc3.CascWC3()
    except Exception:
        return None


def _kinds(paths):
    c = collections.Counter()
    for x in paths:
        e = os.path.splitext(x)[1]
        c['models' if e in MODEL else 'textures' if e in IMAGE else 'sounds' if e in SOUND else 'other'] += 1
    return c


def _same_file(casc, k1, k2):
    e1, e2 = casc.file_set.get(k1.lower()), casc.file_set.get(k2.lower())
    return bool(e1 and e2) and [s[2] for s in e1[1]] == [s[2] for s in e2[1]]


def scan(path, progress=None, casc=None):
    from doctor.models import model_check
    p = progress or _nothing
    out = {'modes_ok': list(MODES), 'missing': dict((m, []) for m in MODES), 'reference': None,
           'fixable': dict((m, 0) for m in MODES), 'nowhere': 0, 'examined': 0, 'sources': {}, 'counts': {},
           'severity': None, 'game': False, 'lines': []}
    casc = _open_game(casc)
    if casc is None:
        return out
    out['game'] = True
    a, err = model_check._open(path)
    if a is None:
        out['error'] = err
        return out
    names = model_check._names(a)
    layers = Layers(casc, _tileset(a))
    _refs, _by, an = _analyse(a, names, layers, p)
    counts, ok = an.counts(), an.modes_ok()
    out.update(modes_ok=ok, missing=dict((m, sorted(an.missing[m])) for m in MODES), fixable=counts,
               nowhere=len(an.nowhere), examined=len(an.examined), reference=an.reference() if len(ok) < len(MODES)
               else None)
    src = {}
    for m in MODES:
        for x, s in an.missing[m].items():
            src.setdefault(x, set()).update(s)
    out['sources'] = dict((k, sorted(v)) for k, v in sorted(src.items()))
    out['counts'] = dict((m, dict(_kinds(an.missing[m]))) for m in MODES)
    if len(ok) < len(MODES):
        heavy = any(out['counts'][m].get('models') for m in MODES) or any(
            s.startswith('terrain ') for m in MODES for ss in an.missing[m].values() for s in ss) or max(
            counts.values()) >= BULK
        out['severity'] = 'warning' if heavy else 'info'
        for m in MODES:
            if counts[m]:
                k = out['counts'][m]
                out['lines'].append('With the %s graphics, %d game files the map uses are missing (%s): what uses '
                                    'them is drawn without them.' % (MODE_NAMES[m], counts[m], ', '.join(
                                        '%d %s' % (n, w) for w, n in sorted(k.items()))))
        ground = sorted(set(s.split(' ', 2)[2] for x, ss in an.missing['sd'].items() for s in ss
                            if s.startswith('terrain ')))
        if ground:
            out['terrain'] = ground
            out['lines'].append('%d terrain tiles and cliffs of the map (%s) have no Classic graphics texture in the '
                                'game, only the Reforged one.' % (len(ground), ', '.join(ground[:8])))
        raw = 0
        for x in src:
            k = layers.where(x).get(out['reference']) or next(iter(layers.where(x).values()), None)
            ent = casc.file_set.get((k or '').lower())
            if ent and ent[1]:
                try:
                    raw += max(o + t for o, t, _e in ent[1])
                except (TypeError, ValueError):
                    pass
        out['bytes'] = raw
        out['room'] = max(0, LIMIT - MARGIN - os.path.getsize(path))
        out['lines'].append(
            'The map was made for the %s graphics. Fix map can import the missing files (at least %.0f MB '
            'before compression; the map can grow %.0f MB more) so the other graphics modes find them.'
            % (MODE_NAMES[out['reference']], raw / 1048576.0, out['room'] / 1048576.0)
        )
    return out


class Item(object):
    def __init__(self, name, src, data, modes, sources, derived=False):
        self.name, self.src, self.data = name, src, data
        self.modes, self.sources = set(modes), set(sources)
        ext = os.path.splitext(name)[1].lower()
        self.kind = 'terrain' if derived else 'model' if ext in MODEL else 'texture' if ext in IMAGE else 'other'
        parents = [s[len('imported '):] for s in self.sources if s.startswith('imported ')]
        self.parents = parents if len(parents) == len(self.sources) else []
        self.packed = None

    def rank(self):
        low = self.name.lower()
        suffix = next((i for i, s in enumerate(('_emissive', '_orm', '_normal'), 1) if s in low), 0)
        return (('terrain', 'model', 'other', 'texture').index(self.kind), -len(self.modes), suffix, len(self.data))

    def packed_size(self):
        if self.packed is None:
            import zlib
            self.packed = len(zlib.compress(self.data, 6))
        return self.packed


def plan(a, names, layers, modes=None, progress=None):
    p = progress or _nothing
    want = [m for m in (modes or MODES) if m in MODES]
    refs, by_lower, first = _analyse(a, names, layers, p)
    best = first.reference()
    items, cache, an = collections.OrderedDict(), first.cache, first
    for _round in range(12):
        the_whole = sorted(set(x for m in want for x in an.missing[m]))
        if not the_whole:
            break
        p('Reading the game files (%d)' % (len(items) + len(the_whole)))
        for x in the_whole:
            derived = an.derive.get(x)
            w = layers.where(derived[1] if derived else x)
            if not w:
                continue
            src = w.get(best) or next(w[m] for m in PREFERENCE if m in w)
            d = layers.read(src)
            if d is None:
                raise RuntimeError('the game file %s does not read' % src)
            need = [m for m in want if x in an.missing[m]]
            srcs = set()
            for m in need:
                srcs.update(an.missing[m][x])
            if derived:
                it = Item(derived[0] + '.blp', src, classic_tile(d), need, srcs, derived=True)
            else:
                it = Item((layers.casc.file_set.get(src.lower()) or (src,))[0].split(':')[-1], src, d, need, srcs)
            items[it.name] = it
        an = Analysis(refs, by_lower, layers, dict((k, v.data) for k, v in items.items()), cache, first.ground)
    return list(items.values()), best, first, an


def choose(items, room):
    chosen, left, used, names = [], [], 0, set()
    for it in sorted(items, key=Item.rank):
        if it.parents and not any(norm(x) in names for x in it.parents):
            left.append(it)
            continue
        cost = it.packed_size() if room is not None else 0
        if room is not None and used + cost > room:
            left.append(it)
            continue
        used += cost
        chosen.append(it)
        names.add(norm(it.name))
    return chosen, left


def fix(path_in, path_out, progress=None, casc=None, modes=None, budget=True):
    import shutil
    from doctor.fix import unprotect
    from doctor.models import model_check
    from doctor.mpq import mpqadd
    from doctor.fix import editor_prep
    p = progress or _nothing
    res = {'state': 'failed', 'imported': 0, 'bytes': 0, 'size_before': 0, 'size_after': 0, 'modes_ok': [],
           'partial': False, 'left': {}, 'lines': []}
    if os.path.normcase(os.path.abspath(path_in)) == os.path.normcase(os.path.abspath(path_out)):
        res['error'] = 'The output must be a new file.'
        return res
    want = [m for m in (modes or MODES) if m in MODES]
    casc = _open_game(casc)
    if casc is None:
        res['state'] = 'refused'
        res['reason'] = 'Warcraft III (Reforged) is not installed here: the missing files come from it.'
        return res
    a, err = model_check._open(path_in)
    if a is None:
        res['error'] = err
        return res
    names = model_check._names(a)
    layers = Layers(casc, _tileset(a))
    try:
        items, best, first, after = plan(a, names, layers, want, p)
    except Exception as e:
        res['error'] = 'The game files did not read (%s).' % (str(e) or type(e).__name__)
        return res
    res['modes_ok'] = first.modes_ok()
    res['reference'] = best
    if not items:
        res['state'] = 'nothing_to_do'
        res['reason'] = 'Every graphics mode finds the game files the map uses.'
        return res
    res['size_before'] = os.path.getsize(path_in)
    room = LIMIT - MARGIN - res['size_before']
    p('Measuring the size')
    total = sum(it.packed_size() for it in items)
    if total > room and not budget:
        res['state'] = 'refused'
        res['reason'] = (
            'The map would grow from %.1f MB to about %.1f MB, above the 512 MB the game lists. Repair one '
            'graphics mode at a time, or make the map smaller first.'
            % (res['size_before'] / 1048576.0, (res['size_before'] + total) / 1048576.0)
        )
        return res
    chosen, left = choose(items, room if total > room else None)
    if not chosen:
        res['state'] = 'refused'
        res['reason'] = ('The map is %.1f MB: none of the %d missing game files fits below the 512 MB the game lists.'
                         % (res['size_before'] / 1048576.0, len(items)))
        return res
    replaced = collections.Counter()
    for it in chosen:
        for m in MODES:
            k = layers.find(it.name, m)
            if k and not _same_file(casc, k, it.src):
                replaced[m] += 1
    files = sorted(((it.name, it.data) for it in chosen), key=lambda x: x[0].lower())
    imp = unprotect._read(a, 'war3map.imp')
    if imp:
        try:
            missing_items = editor_prep.missing_from_imp(imp, [n for n, _d in files])
            if missing_items:
                files.append(('war3map.imp', editor_prep.imp_with(imp, missing_items)))
        except Exception:
            pass
    part = model_check._part(path_out)
    try:
        p('Writing the new map')
        shutil.copyfile(path_in, part)
        no_place = []
        with unprotect.quiet():
            mpqadd.add_files(part, files, (), log=_nothing, no_slot=no_place, grow=list(names))
        if no_place:
            raise RuntimeError('no room in the hash table for %d files' % len(no_place))
        if os.path.getsize(part) > LIMIT:
            raise RuntimeError('the map would be %.1f MB' % (os.path.getsize(part) / 1048576.0))
        b, err = model_check._open(part)
        if b is None:
            raise RuntimeError(err)
        p('Checking the new map')
        for n, d in files:
            if unprotect._read(b, n) != d:
                raise RuntimeError('%s was not read back' % n)
        unprotect.check_untouched(a, b, names, [n for n, _d in files])
        _r, _bl, an2 = _analyse(b, model_check._names(b), layers)
        put = set()
        for it in chosen:
            put.update(forms(it.name))
        wrong = [x for m in want for x in an2.missing[m] if any(f in put for f in forms(x))]
        if wrong:
            raise RuntimeError('%s is still missing' % wrong[0])
        if not left:
            still = [m for m in want if an2.missing[m]]
            if still:
                raise RuntimeError('still missing with %s' % ', '.join(
                    '%s (%d)' % (m, len(an2.missing[m])) for m in still))
        ok2 = an2.modes_ok()
        res['left'] = dict((m, len(an2.missing[m])) for m in want if an2.missing[m])
        del a, b
        os.replace(part, path_out)
    except Exception as e:
        try:
            os.remove(part)
        except OSError:
            pass
        res['error'] = 'The check of the new map failed (%s).' % (str(e) or type(e).__name__)
        return res
    before = list(res['modes_ok'])
    res['modes_ok_before'] = before
    res.update(state='done', imported=len(chosen), bytes=sum(len(it.data) for it in chosen),
               size_after=os.path.getsize(path_out), modes_ok=ok2, replaced=dict(replaced), partial=bool(left))
    k = collections.Counter(it.kind for it in chosen)
    words = {'terrain': 'terrain textures', 'model': 'models', 'texture': 'textures', 'other': 'other files'}
    res['lines'] = ['%d game files of the %s graphics were imported into the map (%s), +%.1f MB.' % (
        len(chosen), MODE_NAMES[best], ', '.join('%d %s' % (n, words[w]) for w, n in sorted(k.items())),
        (res['size_after'] - res['size_before']) / 1048576.0)]
    if len(ok2) > len(before):
        res['lines'].append('The map now finds every game file it uses with the %s graphics.' % ', '.join(
            MODE_NAMES[m] for m in ok2))
    if left:
        res['lines'].append(
            '%d more files did not fit below the 512 MB the game lists (%s still miss some: %s).'
            % (
                len(left),
                ' and '.join(MODE_NAMES[m] for m in sorted(res['left'], key=MODES.index)),
                ', '.join(
                    '%s %d' % (MODE_NAMES[m], n)
                    for m, n in sorted(res['left'].items(), key=lambda x: MODES.index(x[0]))
                ),
            )
        )
    if replaced:
        res['lines'].append('Where a graphics mode had its own file at one of those paths it now shows the %s one (%s).'
                            % (MODE_NAMES[best], ', '.join('%s %d' % (MODE_NAMES[m], n)
                                                           for m, n in sorted(replaced.items(),
                                                                              key=lambda x: MODES.index(x[0])))))
    return res


MODE_BITS = {'sd': 1, 'hd': 2, 'de': 4}
ALL_MODES = 7


def lobby_lock(data):
    try:
        from doctor.data import w3i
        m = w3i.parse(data)
    except Exception:
        return None
    modes = m.get('supported_modes')
    return modes if isinstance(modes, int) and modes and modes & 3 != 3 else None


def lobby_unlock(data):
    from doctor.data import w3i
    if lobby_lock(data) is None:
        return None
    m = w3i.parse(data)
    if w3i.write(m) != data:
        return None
    modes = m['supported_modes'] | ALL_MODES
    unlocked = w3i.write(dict(m, supported_modes=modes))
    if len(unlocked) != len(data) or sum(1 for a, b in zip(unlocked, data) if a != b) > 4 or \
            w3i.parse(unlocked).get('supported_modes') != modes:
        return None
    return unlocked


def lobby_modes(modes):
    names = [MODE_NAMES[m] for m in MODES if modes & MODE_BITS[m]]
    return ' and '.join([', '.join(names[:-1])] + names[-1:]) if len(names) > 1 else (names or ['no'])[0]
