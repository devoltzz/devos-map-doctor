# Makes the editor object data (w3u, w3t, w3a) from the SLK and TXT tables of an optimized map.
import collections
import fnmatch
import os
import re


SPECIES = ('unit', 'item', 'ability')
OBJECT_VERSION = 2
NONE_ID = '\0\0\0\0'
INT_TYPES = frozenset(('bool', 'int', 'attackBits', 'channelFlags', 'channelType', 'deathType', 'defenseTypeInt',
                       'detectionType', 'fullFlags', 'interactionFlags', 'morphFlags', 'pickFlags', 'silenceFlags',
                       'spellDetail', 'stackFlags', 'teamColor', 'versionFlags', 'techAvail'))
USE = {'unit': ('useunit', 'usehero', 'usebuilding', 'usecreep'), 'item': ('useitem',), 'ability': ()}
RX_LEVEL = re.compile(r'^(.*?)(\d+)$')


def _objetos():
    from doctor.data import objects
    return objects


INTERNAL_NAME = {('unit', 'units\\unitui.slk'): ('name',)}


def map_tables(read, names, species):
    ob = _objetos()
    cfg = ob.OBJ_KINDS[species]
    tab = {}
    for rel in cfg['slk']:
        data = read(rel)
        if not data:
            continue
        _h, rows = ob.slk.parse_slk_bytes(data)
        fora = INTERNAL_NAME.get((species, rel), ())
        for rid, row in rows.items():
            dst = tab.setdefault(rid, {})
            for k, v in row.items():
                if v != '' and v is not None and k.lower() not in fora:
                    dst[k.lower()] = v
    ids = set(tab)
    cru = {}
    lower = {n.replace('/', '\\').lower(): n for n in names}
    for pad in list(cfg['txt']) + list(cfg['locale']):
        for low in sorted(k for k in lower if fnmatch.fnmatchcase(k, pad)):
            data = read(lower[low])
            if not data:
                continue
            for sid, sec in ob._raw_ini(data).items():
                if sid not in ids:
                    continue
                dst = tab[sid]
                c = cru.setdefault(sid, {})
                for k, v in ob._variants(sec).items():
                    s = ob._unquoted(v)
                    if s == '':
                        continue
                    dst[k] = s
                    c[k] = v
    return tab, cru


def _tipo(meta_type, text):
    if meta_type in INT_TYPES:
        n = _num(text)
        return 2 if n is not None and n != int(n) else 0
    if meta_type == 'real':
        return 1
    if meta_type == 'unreal':
        return 2
    return 3


def _num(text):
    t = '' if text is None else str(text).strip()
    if t in ('', '-', '_'):
        return 0.0
    try:
        return float(t)
    except ValueError:
        return None


def _norm(text):
    t = '' if text is None else str(text).strip()
    return '' if t in ('-', '_') else t


def _equal(a, b, tipo):
    if tipo != 3:
        x, y = _num(a), _num(b)
        if x is not None and y is not None:
            return abs(x - y) < 1e-6 * max(1.0, abs(x), abs(y))
    return _norm(a) == _norm(b)


def _codes(text):
    return frozenset(x.strip() for x in str(text or '').strip('"').split(',') if x.strip())


class Columns(object):
    def __init__(self, species, meta):
        ob = _objetos()
        self.species = species
        self.simple = {}
        self.levels = {}
        self.levels_all = {}
        self.spec = {}
        self.per_level = set()
        self.multi = ob._multipart(meta)
        use = USE[species]
        for code, m in meta.items():
            flags = {k.lower(): v for k, v in m.items() if k.lower().startswith('use')}
            if use and not any(str(flags.get(u) or '0') == '1' for u in use):
                continue
            slk_name = m.get('slk') or ''
            name = (m.get('field') or '').lower()
            if not name:
                continue
            idx = ob._int(m.get('index'), -1)
            data = ob._int(m.get('data'), 0)
            rep = ob._int(m.get('repeat'), 0)
            entry = (code, idx, m.get('type'), data, rep)
            self.spec[code] = (_codes(m.get('useSpecific')), _codes(m.get('notSpecific')))
            if species == 'ability' and slk_name != 'Profile':
                col = name + (ob.LETTERS[data - 1].lower() if 0 < data <= len(ob.LETTERS) else '')
                if rep > 0:
                    self.levels.setdefault(col, entry)
                    self.levels_all.setdefault(col, []).append(entry)
                else:
                    self.simple.setdefault(col, []).append(entry)
            elif species == 'ability' and rep > 0:
                self.per_level.add(name)
                self.levels.setdefault(name + '#', entry)
                self.simple.setdefault(name, []).append(entry)
            else:
                self.simple.setdefault(name, []).append(entry)

    def applies(self, field, code):
        use, nao = self.spec.get(field, (frozenset(), frozenset()))
        return code in use if use else code not in nao

    def resolve(self, col, code=None):
        if col in self.simple:
            ents = self.simple[col]
            if code is not None and self.species == 'ability':
                ents = [e for e in ents if self.applies(e[0], code)]
            return [(c, i, 0, t, d) for c, i, t, d, _r in ents]
        m = RX_LEVEL.match(col)
        if m and m.group(1) in self.levels:
            if code is not None and self.species == 'ability':
                ents = [e for e in self.levels_all[m.group(1)] if self.applies(e[0], code)]
                if not ents:
                    return []
                c, i, t, d, _r = ents[0]
            else:
                c, i, t, d, _r = self.levels[m.group(1)]
            return [(c, i, int(m.group(2)), t, d)]
        return []


def balance_of(w3i_bytes):
    import tempfile
    ob = _objetos()
    if not w3i_bytes:
        return 'custom_v1'
    fd, tmp = tempfile.mkstemp(suffix='.w3i', prefix='slk_objects_')
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(w3i_bytes)
        return ob.w3i_balance(tmp)[0]
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass


def _row_fields(cols, row, code=None):
    mapped, unmapped = [], []
    for col, text in row.items():
        if col.endswith('_lv'):
            continue
        r = cols.resolve(col, code)
        if r:
            mapped.append((col, text, r))
        else:
            unmapped.append(col)
    return mapped, unmapped


def _parts(text):
    return text.split(',') if text else []


def _mods_of(species, cols, meta, row, cru_row, base_row, base_cru, rep, code=None):
    ob = _objetos()
    out = []
    mapped, unmapped = _row_fields(cols, row, code if species == 'ability' else None)
    for col in unmapped:
        rep['unmapped'][col] += 1
    listed = set()
    for col, text, targets in mapped:
        for code, idx, level, mtype, data in targets:
            if species == 'ability' and col in cols.per_level:
                if (col, code) in listed:
                    continue
                listed.add((col, code))
                mine = ob.value_levels((cru_row or {}).get(col), row.get('levels'))
                theirs = ob.value_levels((base_cru or {}).get(col), base_row.get('levels')) if base_row else []
                for i, v in enumerate(mine):
                    if i < len(theirs) and _norm(theirs[i]) == _norm(v):
                        continue
                    out.append((code, 3, i + 1, 0, _value(3, v, True)))
                continue
            btext = base_row.get(col) if base_row else None
            part = text
            if idx >= 0 and (meta[code].get('slk') or '', col) in cols.multi:
                mine, theirs = _parts(text), _parts(btext)
                part = mine[idx] if idx < len(mine) else ''
                btext = theirs[idx] if idx < len(theirs) else ''
            tipo = _tipo(mtype, part)
            if base_row is not None and _equal(part, btext, tipo):
                continue
            out.append((code, tipo, level, data, _value(tipo, part, (meta[code].get('slk') or '') == 'Profile')))
    final = []
    taken = set()
    for m in out:
        k = (m[0], m[2])
        if k in taken:
            rep['twins'] += 1
            continue
        taken.add(k)
        final.append(m)
    return final


def _value(tipo, text, profile=False):
    t = _norm(text)
    if tipo == 3 and profile:
        t = t.replace('|n', '\r\n')
    if tipo == 0:
        n = _num(t)
        return int(n) if n is not None else 0
    if tipo in (1, 2):
        n = _num(t)
        return float(n) if n is not None else 0.0
    return t.encode('utf-8', 'surrogateescape').replace(b'\0', b'')


def _prepare_base(base_tab, cols):
    return {k: {c: _norm(v) for c, v in row.items() if _norm(v) != ''} for k, row in base_tab.items()}


def infer_parent(row, base_norm, candidates=None):
    mine = {c: _norm(v) for c, v in row.items() if _norm(v) != '' and not c.endswith('_lv')}
    best = (None, -1, 0)
    for k in (candidates if candidates is not None else sorted(base_norm)):
        b = base_norm[k]
        eq = sum(1 for c, v in mine.items() if b.get(c) == v)
        if eq > best[1]:
            best = (k, eq, len(mine))
    return best


def convert(read, names, species, base, w3i=None, progress=None):
    ob = _objetos()
    p = progress or (lambda *_a, **_k: None)
    cfg = ob.OBJ_KINDS[species]
    rep = {'rows': 0, 'unchanged': 0, 'originals': 0, 'new': 0, 'mods': 0, 'parent_code': 0, 'parent_inferred': 0,
           'parent_equal_columns': 0, 'parent_columns': 0, 'unmapped': collections.Counter(), 'twins': 0}
    p('Reading the %s tables' % species)
    tab, cru = map_tables(read, names, species)
    out = {'file': cfg['map_path'], 'bytes': None, 'objects': [], 'report': rep}
    if not tab:
        return out
    meta = base.metadata(species)
    cols = Columns(species, meta)
    base_tab = base.table(species)
    base_cru = base.raw_data(species)
    base_norm = _prepare_base(base_tab, cols)
    rep['rows'] = len(tab)
    objs = []
    for k, rid in enumerate(sorted(tab)):
        if k % 200 == 0:
            p('Converting %s %d/%d' % (species, k, len(tab)))
        row = tab[rid]
        if rid in base_tab:
            mods = _mods_of(species, cols, meta, row, cru.get(rid), base_tab[rid], base_cru.get(rid), rep, rid)
            if not mods:
                rep['unchanged'] += 1
                continue
            objs.append((0, rid, NONE_ID, mods))
            rep['originals'] += 1
        else:
            code = row.get('code') if species == 'ability' else None
            if code and code in base_tab:
                parent = code
                rep['parent_code'] += 1
            else:
                parent, eq, total = infer_parent(row, base_norm)
                rep['parent_inferred'] += 1
                rep['parent_equal_columns'] += max(eq, 0)
                rep['parent_columns'] += total
                if parent is None:
                    continue
            mods = _mods_of(species, cols, meta, row, cru.get(rid), base_tab[parent], base_cru.get(parent), rep,
                            parent)
            objs.append((1, parent, rid, mods))
            rep['new'] += 1
        rep['mods'] += len(objs[-1][3])
    def _ids_ok(o):
        return _id_ok(o[1]) and (o[0] == 0 or _id_ok(o[2]))
    ruins = [o for o in objs if not _ids_ok(o)]
    if ruins:
        rep['skipped_ids'] = [o[1] if o[0] == 0 else o[2] for o in ruins][:20]
        rep['skipped'] = len(ruins)
        objs = [o for o in objs if _ids_ok(o)]
    out['objects'] = objs
    if objs:
        out['bytes'] = ob.write_objects_bytes(OBJECT_VERSION, objs, ob.uses_levels(cfg['map_path']))
    return out


def merge_new(data, name, objects):
    ob = _objetos()
    levels = ob.uses_levels(name)
    ver, had, _n = ob.read_objects_bytes(data, levels, name, True)
    seen = set((o[2] if o[0] == 1 else o[1]).lower() for o in had)
    added = [o for o in objects if o[0] == 1 and o[2].lower() not in seen]
    out = {'bytes': None, 'added': [o[2] for o in added], 'kept': len(had), 'version': ver}
    if added and ver <= 2:
        out['bytes'] = ob.write_objects_bytes(ver, list(had) + added, levels)
    return out


def _id_ok(s):
    return isinstance(s, str) and len(s) == 4 and all(0x20 <= ord(c) < 0x100 for c in s)


OTHER_TABLES = (
    ('upgrade', 'units\\upgradedata.slk', 'war3map.w3q'),
    ('buff', 'units\\abilitybuffdata.slk', 'war3map.w3h'),
    ('destructable', 'units\\destructabledata.slk', 'war3map.w3b'),
    ('doodad', 'doodads\\doodads.slk', 'war3map.w3d'),
)


def compare(objs, real_objects):
    mine = {(n if n.strip('\0') else o): (t, o, n, m) for t, o, n, m in objs}
    r = collections.Counter()
    for t, o, n, m in real_objects:
        key = n if n.strip('\0') else o
        r['objects_real'] += 1
        got = mine.get(key)
        if got is None:
            continue
        r['objects_found'] += 1
        if got[0] == t and got[1] == o:
            r['parent_same'] += 1
        mm = {(x[0], x[2]): x[4] for x in got[3]}
        for x in m:
            r['fields_real'] += 1
            v = mm.get((x[0], x[2]))
            if v is None:
                continue
            if v == x[4] or (isinstance(v, (int, float)) and isinstance(x[4], (int, float)) and abs(v - x[4]) < 1e-3):
                r['fields_same'] += 1
            else:
                r['fields_other_value'] += 1
    return dict(r)


def fix(path_in, path_out, progress=None, base=None, species=SPECIES):
    from doctor.fix import unprotect
    from doctor.fix import map_rewrite
    from doctor.models import model_check
    p = progress or (lambda *_a, **_k: None)
    rep = {'state': 'failed', 'lines': [], 'species': {}, 'written': []}

    def stop(state, why):
        rep['state'] = state
        rep['lines'] = [('bad' if state == 'failed' else 'warn', why)]
        return rep

    if os.path.abspath(path_in) == os.path.abspath(path_out):
        return stop('failed', 'The output must be a new file.')
    p('Reading the map')
    a, err = model_check._open(path_in)
    if a is None:
        return stop('failed', err)
    ob = _objetos()

    def read(n):
        try:
            return unprotect._read(a, n)
        except BaseException as e:
            if isinstance(e, KeyboardInterrupt):
                raise
            return None

    todo = [
        s for s in species if not read(ob.OBJ_KINDS[s]['map_path']) and any(read(r) for r in ob.OBJ_KINDS[s]['slk'])
    ]
    partial = [s for s in species if s not in todo and read(ob.OBJ_KINDS[s]['map_path']) and
               any(read(r) for r in ob.OBJ_KINDS[s]['slk'])]
    outras = [(k, t) for k, t, f in OTHER_TABLES if read(t) and not read(f)]
    if not todo and not partial:
        if outras:
            return stop(
                'nothing_to_do',
                'The map has no unit, item or ability SLK table that lacks its object file. Its '
                '%s tables are not converted by this version: they stay in the SLK, which the game reads and the '
                'editor does not.' % ', '.join(k for k, _t in outras),
            )
        return stop('nothing_to_do', 'The map has no SLK tables that lack their object file.')
    p('Finding the file names')
    names = model_check._names(a)
    if base is None:
        try:
            base = ob.GameBase(balance=balance_of(read('war3map.w3i')))
        except Exception as e:
            return stop('refused', 'The game data is needed to tell what the map changed, and it cannot be read (%s).'
                        % str(e)[:80])
    files = []
    rep['lines'].append(('title', 'Object files made from the SLK tables'))
    for s in todo:
        try:
            r = convert(read, names, s, base, progress=p)
        except Exception as e:
            rep['lines'].append(('bad', '%s: not converted (%s).' % (s, str(e)[:100])))
            continue
        rep['species'][s] = r['report']
        if r['bytes'] is None:
            rep['lines'].append(('info', '%s: the tables hold nothing the game does not already have.' % s))
            continue
        files.append((r['file'], r['bytes']))
        x = r['report']
        rep['lines'].append(
            (
                'good',
                '%s: %s, %d new and %d changed objects, %d modifications (parents: %d from the code '
                'column, %d by the most equal fields).'
                % (s, r['file'], x['new'], x['originals'], x['mods'], x['parent_code'], x['parent_inferred']),
            )
        )
        if x.get('skipped'):
            rep['lines'].append(('warn', '%s: %d row(s) whose id is not a 4-character code were skipped (%s).' % (
                s, x['skipped'], ', '.join(repr(i) for i in x['skipped_ids'][:5]))))
        unm = [
            (c, n)
            for c, n in x['unmapped'].most_common()
            if not c.lower().endswith('id')
            and c.lower() not in ('alias', 'code', 'comment', 'comments', 'sort', 'version')
        ]
        if unm:
            rep['lines'].append(('info', '%s: %d columns have no field code in the game\'s metadata, skipped (%s).' % (
                s, len(unm), ', '.join(c for c, _n in unm[:5]))))
    for s in partial:
        fname = ob.OBJ_KINDS[s]['map_path']
        try:
            r = convert(read, names, s, base, progress=p)
            m = merge_new(read(fname), fname, r['objects'])
        except Exception as e:
            rep['lines'].append(('bad', '%s: the new objects only the SLK tables hold were not added to %s (%s).' % (
                s, fname, str(e)[:100])))
            continue
        if not m['added']:
            continue
        rep['species'][s] = dict(r['report'], kept=m['kept'], added=len(m['added']))
        if m['bytes'] is None:
            rep['lines'].append(
                (
                    'warn',
                    '%s: %s is in the Reforged format (version %d) and lacks %d new objects of the '
                    'SLK tables, which were not added.' % (s, fname, m['version'], len(m['added'])),
                )
            )
            continue
        files.append((fname, m['bytes']))
        rep['lines'].append(
            (
                'good',
                '%s: %s kept as the map has it (%d objects), plus %d new objects only the SLK '
                'tables held (%s).'
                % (
                    s,
                    fname,
                    m['kept'],
                    len(m['added']),
                    ', '.join(m['added'][:6]) + ('...' if len(m['added']) > 6 else ''),
                ),
            )
        )
    if outras:
        rep['lines'].append(
            (
                'warn',
                'The %s tables of the map are not converted by this version (units, items and '
                'abilities only): their objects stay in the SLK, which the game reads and the editor '
                'does not.' % ', '.join(k for k, _t in outras),
            )
        )
    if not files:
        rep['state'] = 'failed' if any(k == 'bad' for k, _t in rep['lines']) else 'nothing_to_do'
        return rep
    try:
        w = map_rewrite.write(path_in, path_out, files, p)
    except Exception as e:
        return stop('failed', 'The map could not be written (%s).' % unprotect._error(e))
    rep.update(state='done', file=path_out, same_files=w['same_files'], written=[n for n, _b in files])
    rep['lines'].append(
        (
            'warn',
            'The parent of a unit or an item is a guess (the SLK does not keep it): the objects are '
            'what the tables hold, but the "based on" unit in the editor may not be the one the author used.',
        )
    )
    return rep
