# Finds the model paths of a map that resolve to no file in the map or the game.
import collections
import re


SPECIES = (('war3map.w3u', 'war3mapSkin.w3u', 'units\\unitmetadata.slk'),
           ('war3map.w3t', 'war3mapSkin.w3t', 'units\\unitmetadata.slk'),
           ('war3map.w3a', 'war3mapSkin.w3a', 'units\\abilitymetadata.slk'),
           ('war3map.w3h', 'war3mapSkin.w3h', 'units\\abilitybuffmetadata.slk'),
           ('war3map.w3b', 'war3mapSkin.w3b', 'units\\destructablemetadata.slk'),
           ('war3map.w3d', 'war3mapSkin.w3d', 'doodads\\doodadmetadata.slk'),
           ('war3map.w3q', 'war3mapSkin.w3q', 'units\\upgrademetadata.slk'))
FALLBACK_FIELDS = frozenset(('umdl', 'ua1m', 'ua2m', 'uspa', 'utaa', 'umd1', 'umd2', 'ifil', 'bfil', 'dfil', 'acat',
                             'atat', 'asat', 'aeat', 'aaea', 'amat', 'ftat', 'fsat', 'feat', 'fmat'))
PLACED_ONLY = ('.w3b', '.w3d')
SKIP_FIELDS = frozenset(('upor', 'bgpm'))
SCRIPTS = ('war3map.j', 'war3map.lua', 'scripts\\war3map.j', 'scripts\\war3map.lua')
RX_EXT = re.compile(r'\.(mdl|mdx)\s*\Z', re.I)
RX_ANYEXT = re.compile(r'\.(mdl|mdx)', re.I)
RX_JASS = re.compile(r'"((?:[^"\\\r\n]|\\.)*)"')
RX_LUA = re.compile(r'"((?:[^"\\\r\n]|\\.)*)"|\'((?:[^\'\\\r\n]|\\.)*)\'')
PREFIXES = ('wos_', 'jy-', 'wos_jy-')


def _nothing(*_a, **_k):
    pass


def candidates(path, variations=False):
    p = path.strip().replace('/', '\\').lstrip('\\')
    stem = RX_EXT.sub('', p)
    out = [p, stem + '.mdx', stem + '.mdl']
    if variations:
        out += [stem + str(n) + e for n in (0, 1) for e in ('.mdx', '.mdl')]
    return out


def is_placeholder(path):
    f = path.replace('/', '\\').split('\\')[-1]
    return RX_ANYEXT.sub('', f).strip() in ('', '_', '-')


def looks_imported(path):
    return 'war3mapimported' in path.lower() or '\\' not in path.replace('/', '\\')


def resolves(path, has_in_map, has_in_game, variations=False):
    cs = candidates(path, variations)
    if any(has_in_map(c) for c in cs):
        return 'map'
    if not looks_imported(path) and has_in_game is not None and any(has_in_game(c) for c in cs):
        return 'game'
    return None


def _stem(path):
    f = path.strip().replace('/', '\\').split('\\')[-1]
    return RX_EXT.sub('', f).strip().lower()


def _suggest(path, by_stem):
    s = _stem(path)
    variants = {s}
    for pre in PREFIXES:
        variants.add(pre + s)
        if s.startswith(pre):
            variants.add(s[len(pre):])
    for v in list(variants):
        if v.startswith('wos_'):
            variants.add('wos_jy-' + v[4:])
    hits = sorted(set(h for v in variants for h in by_stem.get(v, ())), key=str.lower)
    if len(hits) != 1:
        return None
    m = RX_EXT.search(path)
    return RX_EXT.sub(m.group(0).strip() if m else '', hits[0]) if m else RX_EXT.sub('', hits[0])


def model_field_codes(game):
    codes = set(FALLBACK_FIELDS)
    if game is None:
        return codes
    from doctor.data import slk
    for _a, _b, meta in SPECIES:
        d = game.read(meta)
        if not d:
            continue
        try:
            rows = slk.parse_slk_bytes(d)[1]
        except Exception:
            continue
        for k, r in rows.items():
            if str(r.get('type')) in ('model', 'modelList'):
                codes.add(k)
    return codes - SKIP_FIELDS


def _script_literals(text, lua):
    out = []
    rx = RX_LUA if lua else RX_JASS
    for m in rx.finditer(text):
        s = next((g for g in m.groups() if g is not None), '')
        if not RX_EXT.search(s):
            continue
        b = m.start() - 1
        while b >= 0 and text[b] in ' \t':
            b -= 1
        e = m.end()
        while e < len(text) and text[e] in ' \t':
            e += 1
        joined = (b >= 0 and text[b] == '+') or (e < len(text) and text[e] == '+') or \
                 (lua and text[e:e + 2] == '..') or (lua and b >= 1 and text[b - 1:b + 1] == '..')
        if not joined:
            out.append(s.replace('\\\\', '\\').replace('\\"', '"').replace("\\'", "'"))
    return out


def scan(path, progress=None, casc=None):
    from doctor.fix import unprotect
    from doctor.fix import game_paths
    from doctor.models import model_check
    from doctor.data import objects
    p = progress or _nothing
    out = {'missing': [], 'examined': 0, 'by_map': 0, 'by_game': 0, 'unchecked': 0, 'game': False,
           'counts': {'missing': 0, 'placeholder': 0}}
    g = game_paths.open_game(casc)
    out['game'] = g is not None
    a, err = model_check._open(path)
    if a is None:
        out['error'] = err
        return out
    p('Finding the file names')
    models = [n for n in model_check._names(a) if n.lower().endswith(('.mdx', '.mdl'))]
    by_stem = collections.defaultdict(list)
    for n in models:
        by_stem[_stem(n)].append(n)
    codes = model_field_codes(g)
    uses = collections.OrderedDict()

    def consider(source, ident, field, pth, n=1):
        key = (source, ident, field, pth)
        uses[key] = uses.get(key, 0) + n

    p('Reading the object data')
    for plain, skin, _meta in SPECIES:
        for name in (plain, skin):
            d = unprotect._read(a, name)
            if not d:
                continue
            try:
                _v, objs, _pos = objects.read_objects_bytes(d, objects.uses_levels(name), name)
            except Exception:
                continue
            for _t, orig, novo, mods in objs:
                ident = novo if novo.strip('\0') else orig
                for mm in mods:
                    field, vt, val = mm[0], mm[1], mm[4]
                    if vt != 3 or field in SKIP_FIELDS:
                        continue
                    text = val.decode('utf-8', 'surrogateescape') if isinstance(val, (bytes, bytearray)) else str(val)
                    for part in text.split(','):
                        part = part.strip()
                        if not part or part in ('_', '-'):
                            continue
                        if field in codes or RX_EXT.search(part):
                            consider(name, ident, field, part)
    p('Reading the script')
    for sname in SCRIPTS:
        d = unprotect._read(a, sname)
        if d:
            for lit in _script_literals(d.decode('utf-8', 'surrogateescape'), sname.endswith('.lua')):
                consider('script', None, None, lit)
            break
    has_map = lambda c: a.find(c) is not None
    has_game = g.has if g is not None else None
    cache = {}
    for (source, ident, field, pth), n in uses.items():
        out['examined'] += n
        if is_placeholder(pth):
            out['missing'].append({'source': source, 'id': ident, 'field': field, 'path': pth, 'uses': n,
                                   'placeholder': True, 'suggestion': None, 'severity': 'info'})
            out['counts']['placeholder'] += 1
            continue
        var = field in ('bfil', 'dfil')
        if (pth, var) not in cache:
            cache[(pth, var)] = resolves(pth, has_map, has_game, var)
        r = cache[(pth, var)]
        if r == 'map':
            out['by_map'] += n
            continue
        if r == 'game':
            out['by_game'] += n
            continue
        if g is None and not looks_imported(pth):
            out['unchecked'] += n
            continue
        out['missing'].append({'source': source, 'id': ident, 'field': field, 'path': pth, 'uses': n,
                               'placeholder': False, 'suggestion': _suggest(pth, by_stem),
                               'severity': 'info' if source.lower().endswith(PLACED_ONLY) else 'warning'})
        out['counts']['missing'] += 1
    out['missing'].sort(key=lambda m: (not m['placeholder'], -m['uses'], m['path'].lower()))
    return out
