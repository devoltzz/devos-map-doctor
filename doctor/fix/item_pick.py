# Finds the items whose model on the ground has nothing to click in Reforged graphics, and points them at a copy of the classic file.
import json
import math
import os
import re
import struct


HERE = os.path.dirname(os.path.abspath(__file__))

B = chr(92)
NAME = 'item_pick_hd.json'
SD = 'war3.w3mod:'
LAYERS = (('hd', 'war3.w3mod:_hd.w3mod:'), ('de', 'war3.w3mod:_de.w3mod:'))
OBJECTS = (('war3map.w3t', 'ifil', 'item'), ('war3mapSkin.w3t', 'ifil', 'item'),
           ('war3map.w3u', 'umdl', 'unit'), ('war3mapSkin.w3u', 'umdl', 'unit'))
TEXTS = (('Units' + B + 'ItemFunc.txt', 'item'), ('Units' + B + 'ItemSkin.txt', 'item'),
         ('Units' + B + 'ItemStrings.txt', 'item'), ('Units' + B + 'UnitSkin.txt', 'unit'))
UNIT_ABILITIES = 'Units' + B + 'UnitAbilities.slk'
CLICKED = ('units' + B, 'buildings' + B, 'objects' + B + 'inventoryitems' + B)
LOCUST = 'aloc'
FOLDER = 'war3mapImported' + B + 'PickSD'
RX_FILE = re.compile(r'^(\s*file\s*=\s*)("?)([^"\r\n]*?)("?)(\s*)$', re.I)
RX_SECTION = re.compile(r'^\s*\[([^\]]+)\]')
RX_COLOR = re.compile(r'\|c[0-9a-fA-F]{8}|\|r', re.I)
_TABLE = {}


def _nothing(*_a, **_k):
    pass


def norm(path):
    p = path.strip().replace('/', B).lstrip(B).lower()
    if p.endswith('.mdl'):
        return p[:-4] + '.mdx'
    return p if p.endswith('.mdx') else p + '.mdx'


def _box(b):
    if not b or any(math.isnan(v) or math.isinf(v) for v in b):
        return False
    lo, hi = b[1:4], b[4:7]
    return any(h > l for l, h in zip(lo, hi)) and max(abs(v) for v in lo + hi) < 1e7


def pick_area(data):
    from doctor.fix import mdx_struct
    m = mdx_struct.read(data)
    clid = sum(1 for n in m.nodes if n['kind'] == b'CLID')
    geo = False
    for g in m.geos:
        nex, at = g.get('seq_extents') or (0, 0)
        if _box(g.get('bounds')) or any(_box(struct.unpack_from('<7f', m.data, at + i * 28)) for i in range(nex)):
            geo = True
            break
    model = bool((m.modl and _box(m.modl['bounds'])) or any(_box(s['bounds']) for s in m.seqs))
    verts = sum(g['parts'].get('VRTX', (0,))[0] for g in m.geos)
    return {'collision': clid, 'geoset_box': geo, 'model_box': model, 'vertices': verts, 'pick': bool(clid or geo)}


def measure(casc, path):
    p = norm(path)
    files = getattr(casc, 'file_set', None) or {}
    if SD + p not in files:
        return None
    try:
        sd = casc.read_data(SD + p)
        out = {'sd': pick_area(sd), 'sd_bytes': sd}
        for layer, prefix in LAYERS:
            if prefix + p in files:
                d = casc.read_data(prefix + p)
                out[layer] = out['sd'] if d == sd else pick_area(d)
    except Exception:
        return None
    return out


def lost(m):
    if not m or not m['sd']['pick']:
        return ''
    return ' '.join(layer for layer, _p in LAYERS if layer in m and not m[layer]['pick'])


def affected(path, layers):
    return 'hd' in (layers or '').split() and not path.startswith(CLICKED)


def _table_path():
    try:
        from doctor.data import wc3_versions
        roots = wc3_versions._ref_roots()
    except Exception:
        roots = [os.path.normpath(os.path.join(HERE, '..', 'ref'))]
    for root in roots:
        p = os.path.join(root, NAME)
        if os.path.isfile(p):
            return p
    return None


def table():
    if 't' not in _TABLE:
        p = _table_path()
        data = {}
        if p:
            with open(p, encoding='utf-8') as f:
                data = json.load(f).get('models') or {}
        _TABLE['t'] = data
    return _TABLE['t']


def _text(v):
    return v.decode('utf-8', 'surrogateescape') if isinstance(v, (bytes, bytearray)) else str(v)


def _abilities_table(data):
    if not data:
        return {}
    try:
        from doctor.data import slk
        rows = slk.parse_slk_bytes(data)[1]
    except Exception:
        return {}
    return dict((k, str(r.get('abilList') or '')) for k, r in rows.items())


def _is_locust(abilities):
    return LOCUST in [a.strip().strip('"').lower() for a in (abilities or '').split(',')]


def ground_models(read, game=None):
    from doctor.data import objbin
    found, unit_abil, unit_base = [], {}, {}
    for name, field, kind in OBJECTS:
        d = read(name)
        if not d:
            continue
        try:
            _v, tables, _n = objbin.read_data(d, False)
        except Exception:
            continue
        for objs in tables:
            for orig, new, mods in objs:
                ident = new if new.strip('\0') else orig
                if kind == 'unit':
                    unit_base.setdefault(ident, orig)
                for f, k, _l, _d, value in mods:
                    if k != 3:
                        continue
                    if f == field and _text(value).strip():
                        found.append((kind, name, ident, _text(value).strip()))
                    elif f == 'uabi' and kind == 'unit':
                        unit_abil[ident] = _text(value)
    for name, kind in TEXTS:
        d = read(name)
        if not d:
            continue
        section = None
        for line in _text(d).splitlines():
            m = RX_SECTION.match(line)
            if m:
                section = m.group(1).strip()
                continue
            f = RX_FILE.match(line)
            if f and section and f.group(3).strip():
                found.append((kind, name, section, f.group(3).strip()))
    if not any(kind == 'unit' for kind, _s, _i, _p in found):
        return found, []
    tables = [_abilities_table(read(UNIT_ABILITIES))]
    if game is not None:
        try:
            tables.append(_abilities_table(game.read(UNIT_ABILITIES.lower())))
        except Exception:
            pass

    def abilities(u):
        if u in unit_abil:
            return unit_abil[u]
        for key in (u, unit_base.get(u)):
            for t in tables:
                if key and key in t:
                    return t[key]
        return ''
    models, locust = [], []
    for kind, source, ident, path in found:
        if kind == 'unit' and _is_locust(abilities(ident)):
            locust.append((source, ident, path))
        else:
            models.append((kind, source, ident, path))
    return models, locust


def _of_game(path, has_in_map):
    from doctor.fix import model_paths
    return not model_paths.looks_imported(path) and not any(has_in_map(c) for c in model_paths.candidates(path))


def judge(paths, casc=None):
    out, how = {}, 'table'
    t = table()
    for p in sorted(set(paths)):
        m = measure(casc, p) if casc is not None else None
        if m is not None:
            how = 'game'
            if affected(p, lost(m)):
                out[p] = lost(m)
        elif affected(p, t.get(p)):
            out[p] = t[p]
    return out, how


def scan(path, progress=None, casc=None):
    from doctor.fix import unprotect
    from doctor.fix import game_paths
    from doctor.models import model_check
    from doctor.data import object_names
    p = progress or _nothing
    out = {'items': [], 'models': {}, 'locust': 0, 'measured': 'table', 'examined': 0}
    a, err = model_check._open(path)
    if a is None:
        out['error'] = err
        return out
    p('Reading the items and units')
    read = lambda n: unprotect._read(a, n)
    g = game_paths.open_game(casc)
    found, locust = ground_models(read, g)
    out['examined'] = len(found) + len(locust)
    has = lambda c: a.find(c) is not None
    game = [x for x in found if _of_game(x[3], has)]
    locust = [x for x in locust if _of_game(x[2], has)]
    if not game:
        return out
    verdicts, out['measured'] = judge([norm(w) for _k, _s, _i, w in game] + [norm(w) for _s, _i, w in locust],
                                      g.casc if g is not None else None)
    if not verdicts:
        return out
    out['locust'] = len(set(i for _s, i, w in locust if norm(w) in verdicts))
    try:
        names = object_names.names(read, game=False)
    except Exception:
        names = {}
    seen = set()
    for kind, source, ident, written in game:
        k = norm(written)
        if k in verdicts and (kind, ident, k) not in seen:
            seen.add((kind, ident, k))
            out['items'].append({'kind': kind, 'id': ident, 'name': RX_COLOR.sub('', names.get(ident) or '').strip(),
                                 'path': written, 'source': source, 'layers': verdicts[k]})
    out['models'] = dict((k, v) for k, v in verdicts.items() if any(norm(x['path']) == k for x in out['items']))
    return out


def new_names(spelled):
    out, used = {}, set()
    for k in sorted(spelled):
        base = os.path.splitext(spelled[k].replace('/', B).split(B)[-1].strip())[0]
        stem, n = base, 1
        while stem.lower() in used:
            n += 1
            stem = '%s_%d' % (base, n)
        used.add(stem.lower())
        out[k] = FOLDER + B + stem + '.mdx'
    return out


def rewrite_objects(data, new, field='ifil', ids=None):
    from doctor.data import objbin
    order = None
    if ids is not None:
        _v, tables, _n = objbin.read_data(data, False)
        order = [[(nw if nw.strip('\0') else o) for o, nw, _m in objs] for objs in tables]

    def change(t, o, _m, f, value):
        if f != field or (order is not None and order[t][o] not in ids):
            return None
        k = norm(_text(value)) if _text(value).strip() else None
        return new[k].encode('ascii') if k in new else None
    return objbin.rewrite(data, False, change)


def rewrite_text(text, new, ids=None):
    n = 0
    section = None
    lines = text.splitlines(True)
    for i, line in enumerate(lines):
        body = line.rstrip('\r\n')
        m = RX_SECTION.match(body)
        if m:
            section = m.group(1).strip()
            continue
        f = RX_FILE.match(body)
        if not f or not f.group(3).strip() or (ids is not None and section not in ids):
            continue
        k = norm(f.group(3))
        if k in new:
            lines[i] = f.group(1) + f.group(2) + new[k] + f.group(4) + f.group(5) + line[len(body):]
            n += 1
    return ''.join(lines), n


def fix(read, has_in_map, casc=None, log=_nothing):
    rel = {'state': 'nothing', 'reason': '', 'files': {}, 'models': {}, 'paths': {}, 'items': []}
    if casc is None:
        try:
            from doctor.data import casc_wc3
            casc = casc_wc3.CascWC3()
        except Exception as e:
            casc = e
    game = None
    if not isinstance(casc, Exception):
        try:
            from doctor.fix import game_paths
            game = game_paths.GameFiles(casc)
        except Exception:
            game = None
    models, _locust = ground_models(read, game)
    found = [x for x in models if _of_game(x[3], has_in_map)]
    if not found:
        return rel
    wanted = sorted(set(norm(w) for _k, _s, _i, w in found))
    if isinstance(casc, Exception):
        if any(affected(k, table().get(k)) for k in wanted):
            rel.update(state='skipped', reason='the game files cannot be read (%s)' % casc)
        return rel
    copies = {}
    for k in wanted:
        m = measure(casc, k)
        if affected(k, lost(m)):
            copies[k] = m['sd_bytes']
        elif m is None and affected(k, table().get(k)):
            log('pick: %s is in the list but the game file does not read' % k)
    if not copies:
        return rel
    spelled = {}
    for _k, _s, _i, w in found:
        spelled.setdefault(norm(w), w)
    rel['paths'] = new_names(dict((k, spelled[k]) for k in copies))
    for k, d in copies.items():
        rel['models'][rel['paths'][k]] = d
    units = set(i for kind, _s, i, w in found if kind == 'unit' and norm(w) in copies)
    for name, field, kind in OBJECTS:
        d = read(name)
        if d:
            nd, n = rewrite_objects(d, rel['paths'], field, None if kind == 'item' else units)
            if n:
                rel['files'][name] = nd
    for name, kind in TEXTS:
        d = read(name)
        if d:
            t, n = rewrite_text(_text(d), rel['paths'], None if kind == 'item' else units)
            if n:
                rel['files'][name] = t.encode('utf-8', 'surrogateescape')
    rel['items'] = [(kind, s, i, norm(w)) for kind, s, i, w in found if norm(w) in copies]
    rel['state'] = 'done'
    return rel
