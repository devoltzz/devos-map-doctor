# Finds the model paths of a map that resolve to no file in the map or the game, and points them at the one model of the map with that name.
import collections
import os
import re
import shutil


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
RX_DOUBLED = re.compile(r'(war3mapimported[\\/])(?:war3mapimported[\\/])+', re.I)


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


def _target(pth, var, resolve, by_stem):
    if RX_DOUBLED.search(pth):
        col = RX_DOUBLED.sub(lambda m: m.group(1), pth)
        if resolve(col, var):
            return col, 'doubled'
    s = _suggest(pth, by_stem)
    if s and s != pth and resolve(s, var):
        return s, 'suggestion'
    return None, None


class _Map(object):
    def __init__(self, path, casc, p):
        from doctor.fix import game_paths
        from doctor.models import model_check
        self.error = None
        self.g = game_paths.open_game(casc)
        self.a, err = model_check._open(path)
        if self.a is None:
            self.error = err
            return
        p('Finding the file names')
        self.names = model_check._names(self.a)
        self.by_stem = collections.defaultdict(list)
        for n in self.names:
            if n.lower().endswith(('.mdx', '.mdl')):
                self.by_stem[_stem(n)].append(n)
        self.codes = model_field_codes(self.g)
        has_map = lambda c: self.a.find(c) is not None
        has_game = self.g.has if self.g is not None else None
        cache = {}

        def resolve(pth, var):
            if (pth, var) not in cache:
                cache[(pth, var)] = resolves(pth, has_map, has_game, var)
            return cache[(pth, var)]
        self.resolve = resolve

    def judge(self, pth, field):
        if is_placeholder(pth):
            return 'placeholder'
        r = self.resolve(pth, field in ('bfil', 'dfil'))
        if r:
            return r
        if self.g is None and not looks_imported(pth):
            return 'unchecked'
        return 'missing'

    def target(self, pth, field, whole):
        if (field not in self.codes and not whole) or ':' in pth:
            return None, None
        return _target(pth, field in ('bfil', 'dfil'), self.resolve, self.by_stem)


def _parts(text):
    out = []
    for raw in text.split(','):
        part = raw.strip()
        if part and part not in ('_', '-'):
            out.append((raw, part))
    return out


def scan(path, progress=None, casc=None):
    from doctor.fix import unprotect
    from doctor.data import objects
    p = progress or _nothing
    out = {'missing': [], 'examined': 0, 'by_map': 0, 'by_game': 0, 'unchecked': 0, 'game': False,
           'counts': {'missing': 0, 'placeholder': 0, 'fixable': 0}}
    m = _Map(path, casc, p)
    out['game'] = m.g is not None
    if m.a is None:
        out['error'] = m.error
        return out
    a = m.a
    uses = collections.OrderedDict()

    def consider(source, ident, field, pth, whole=False):
        key = (source, ident, field, pth)
        u = uses.setdefault(key, [0, True])
        u[0] += 1
        u[1] = u[1] and whole

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
                    for _raw, part in _parts(text):
                        if field in m.codes or RX_EXT.search(part):
                            consider(name, ident, field, part, part == text)
    p('Reading the script')
    for sname in SCRIPTS:
        d = unprotect._read(a, sname)
        if d:
            for lit in _script_literals(d.decode('utf-8', 'surrogateescape'), sname.endswith('.lua')):
                consider('script', None, None, lit)
            break
    for (source, ident, field, pth), (n, whole) in uses.items():
        out['examined'] += n
        r = m.judge(pth, field)
        if r == 'placeholder':
            out['missing'].append({'source': source, 'id': ident, 'field': field, 'path': pth, 'uses': n,
                                   'placeholder': True, 'suggestion': None, 'fixable': False, 'severity': 'info'})
            out['counts']['placeholder'] += 1
            continue
        if r in ('map', 'game', 'unchecked'):
            out['by_' + r if r != 'unchecked' else r] += n
            continue
        fixable = source != 'script' and m.target(pth, field, whole)[0] is not None
        out['missing'].append({'source': source, 'id': ident, 'field': field, 'path': pth, 'uses': n,
                               'placeholder': False, 'suggestion': _suggest(pth, m.by_stem), 'fixable': fixable,
                               'severity': 'info' if source.lower().endswith(PLACED_ONLY) else 'warning'})
        out['counts']['missing'] += 1
        out['counts']['fixable'] += 1 if fixable else 0
    out['missing'].sort(key=lambda e: (not e['placeholder'], -e['uses'], e['path'].lower()))
    return out


def _rewrite_file(m, name, data):
    from doctor.data import objects
    lvl = objects.uses_levels(name)
    ver, objs, pos = objects.read_objects_bytes(data, lvl, name, with_end=True)
    changes = []
    planned = {}
    novos = []
    for i, (t, orig, novo, mods) in enumerate(objs):
        ident = novo if novo.strip('\0') else orig
        new_mods = None
        for j, mm in enumerate(mods):
            field, vt, val = mm[0], mm[1], mm[4]
            if vt != 3 or field in SKIP_FIELDS:
                continue
            text = val.decode('utf-8', 'surrogateescape')
            pieces = text.split(',')
            touched = False
            for k, raw in enumerate(pieces):
                part = raw.strip()
                if not part or part in ('_', '-') or not (field in m.codes or RX_EXT.search(part)):
                    continue
                if m.judge(part, field) != 'missing':
                    continue
                to, rule = m.target(part, field, part == text)
                if to is None:
                    continue
                pieces[k] = raw.replace(part, to, 1)
                changes.append((ident, field, part, to, rule))
                touched = True
            if not touched:
                continue
            nv = ','.join(pieces).encode('utf-8', 'surrogateescape')
            if b'\0' in nv:
                raise RuntimeError('a rewritten value of %s has a NUL' % name)
            if new_mods is None:
                new_mods = list(mods)
            new_mods[j] = (mm[0], mm[1], mm[2], mm[3], nv) + tuple(mm[5:])
            planned[(i, j)] = nv
        novos.append((t, orig, novo, objects.with_item_sets(new_mods, mods)) if new_mods is not None
                     else (t, orig, novo, mods))
    if not planned:
        return None, [], {}
    if objects.write_objects_bytes(ver, objs, lvl) + data[pos:] != data:
        raise RuntimeError('%s does not come back byte for byte through the writer, so it is left alone' % name)
    new = objects.write_objects_bytes(ver, novos, lvl) + data[pos:]
    ver2, objs2, pos2 = objects.read_objects_bytes(new, lvl, name, with_end=True)
    if ver2 != ver or len(objs2) != len(objs) or pos2 != len(new) - len(data) + pos:
        raise RuntimeError('the new %s does not read to its end' % name)
    for i, (o1, o2) in enumerate(zip(objs, objs2)):
        if o1[:3] != o2[:3] or len(o1[3]) != len(o2[3]) or objects.item_sets(o1[3]) != objects.item_sets(o2[3]):
            raise RuntimeError('object %s of %s changed its shape' % (o1[2] if o1[2].strip('\0') else o1[1], name))
        for j, (m1, m2) in enumerate(zip(o1[3], o2[3])):
            if (i, j) in planned:
                if m1[:4] != m2[:4] or m1[5:] != m2[5:] or m2[4] != planned[(i, j)]:
                    raise RuntimeError('a rewritten modification of %s did not come back as written' % name)
            elif m1 != m2:
                raise RuntimeError('a modification of %s that was not listed changed' % name)
    return new, changes, planned


def fix(path_in, path_out, progress=None, casc=None):
    from doctor.fix import unprotect
    from doctor.models import model_check
    from doctor.mpq import mpqadd
    p = progress or _nothing
    res = {'state': 'failed', 'fixed': [], 'count': 0, 'files': [], 'lines': []}
    if os.path.abspath(path_in) == os.path.abspath(path_out):
        res['error'] = 'The output must be a new file.'
        return res
    p('Reading the map')
    m = _Map(path_in, casc, p)
    if m.a is None:
        res['error'] = m.error
        return res
    a = m.a
    p('Reading the object data')
    writes = []
    changes = []
    skipped = []
    for plain, skin, _meta in SPECIES:
        for name in (plain, skin):
            d = unprotect._read(a, name)
            if not d:
                continue
            try:
                new, ch, _pl = _rewrite_file(m, name, d)
            except Exception as e:
                skipped.append((name, str(e) or type(e).__name__))
                continue
            if new is not None:
                writes.append((name, new))
                changes += [(name,) + c for c in ch]
    res['skipped'] = [{'file': n, 'reason': w} for n, w in skipped]
    if not writes:
        if skipped:
            res['error'] = 'The object data does not read (%s: %s).' % skipped[0]
            return res
        res['state'] = 'nothing_to_do'
        return res
    agg = collections.OrderedDict()
    for name, ident, field, frm, to, rule in changes:
        key = (name, ident, field, frm)
        if key not in agg:
            agg[key] = {'source': name, 'id': ident, 'field': field, 'from': frm, 'to': to, 'rule': rule, 'uses': 0}
        agg[key]['uses'] += 1
    part = model_check._part(path_out)
    written = dict((n.lower(), d) for n, d in writes)
    try:
        p('Writing the new map')
        shutil.copyfile(path_in, part)
        no_room = []
        with unprotect.quiet():
            mpqadd.add_files(part, writes, log=_nothing, no_slot=no_room)
        if no_room:
            raise RuntimeError('no room in the hash table for %s' % ', '.join(no_room))
        p('Checking the new map')
        b, err = model_check._open(part)
        if b is None:
            raise RuntimeError(err)
        for n, d in writes:
            if unprotect._read(b, n) != d:
                raise RuntimeError('%s was not read back fixed' % n)
        for n in m.names:
            if n.lower() in written or n.lower() == '(attributes)':
                continue
            x = unprotect._read(a, n)
            if x is not None and unprotect._read(b, n) != x:
                raise RuntimeError('%s changed' % n)
        del a, b
        m.a = None
        os.replace(part, path_out)
    except Exception as e:
        try:
            os.remove(part)
        except OSError:
            pass
        res['error'] = 'The check of the new map failed (%s).' % (str(e) or type(e).__name__)
        return res
    fixed = list(agg.values())
    nd = sum(1 for x in fixed if x['rule'] == 'doubled')
    res.update(state='done', fixed=fixed, count=len(fixed), files=[n for n, _d in writes])
    res['lines'] = ['Model paths of the object data that now point to a model the map has: %d (%d with a doubled '
                    'war3mapImported folder, %d by the only model of that name).' % (len(fixed), nd, len(fixed) - nd)]
    if skipped:
        res['lines'].append('Object files left as they are, since they do not read: %s.'
                            % ', '.join(n for n, _w in skipped))
    return res
