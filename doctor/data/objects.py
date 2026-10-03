# Reads and rewrites the object data files of a map (war3map.w3u, .w3t, .w3a...).
import collections
import decimal
import fnmatch
import importlib.util
import os
import re
import struct
import sys


HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = HERE


def common_module(fname):
    hash_key = '_kk_' + fname
    mod = sys.modules.get(hash_key)
    if mod is None and getattr(sys, 'frozen', False) and not os.path.isfile(os.path.join(SCRIPTS, fname + '.py')):
        mod = sys.modules[hash_key] = importlib.import_module('doctor.data.' + fname)
    if mod is None:
        spec = importlib.util.spec_from_file_location(hash_key, os.path.join(SCRIPTS, fname + '.py'))
        mod = importlib.util.module_from_spec(spec)
        sys.modules[hash_key] = mod
        spec.loader.exec_module(mod)
    return mod


slk = common_module('slk')

WITH_LEVELS = ('.w3a', '.w3d', '.w3q')
WITHOUT_LEVELS = ('.w3u', '.w3t', '.w3b', '.w3h')
VERSIONS = (1, 2)


class ObjectError(Exception):
    pass


def uses_levels(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext in WITH_LEVELS:
        return True
    if ext in WITHOUT_LEVELS:
        return False
    raise ObjectError('cannot tell whether %s has levels (extension %r): pass with_levels=' % (file_path, ext))


def read_objects_bytes(d, with_levels, fname='(bytes)', with_end=False):
    if len(d) < 12:
        raise ObjectError('%s: short file (%d bytes)' % (fname, len(d)))
    ver = struct.unpack_from('<I', d, 0)[0]
    if ver not in VERSIONS:
        raise ObjectError('%s: version %d not supported (measured in the collection: %s; the Reforged version 3 '
                          'has a different layout per object)' % (fname, ver, VERSIONS))
    pos = 4
    objects = []
    try:
        for table in (0, 1):
            n = struct.unpack_from('<I', d, pos)[0]
            pos += 4
            for _ in range(n):
                orig = d[pos:pos + 4].decode('latin-1')
                new = d[pos + 4:pos + 8].decode('latin-1')
                cnt = struct.unpack_from('<I', d, pos + 8)[0]
                pos += 12
                mods = []
                for _ in range(cnt):
                    field_id = d[pos:pos + 4].decode('latin-1')
                    kind = struct.unpack_from('<I', d, pos + 4)[0]
                    pos += 8
                    level = pointer = 0
                    if with_levels:
                        level, pointer = struct.unpack_from('<II', d, pos)
                        pos += 8
                    if kind == 0:
                        val = struct.unpack_from('<i', d, pos)[0]
                        pos += 4
                    elif kind in (1, 2):
                        val = struct.unpack_from('<f', d, pos)[0]
                        pos += 4
                    elif kind == 3:
                        e = d.index(b'\0', pos)
                        val = d[pos:e]
                        pos = e + 1
                    else:
                        raise ObjectError('%s: value type %d in field %r of object %r (byte %d): the '
                                          'file is not of this format or the level decision is '
                                          'wrong (with_levels=%s)' % (fname, kind, field_id, new or orig,
                                                                      pos - 8, with_levels))
                    end_pos = d[pos:pos + 4]
                    pos += 4
                    if with_end:
                        if len(end_pos) != 4:
                            raise ValueError('truncated end of record')
                        mods.append((field_id, kind, level, pointer, val, end_pos))
                    else:
                        mods.append((field_id, kind, level, pointer, val))
                objects.append((table, orig, new, mods))
    except (struct.error, ValueError) as e:
        raise ObjectError('%s: the file ended in the middle of an object (byte %d of %d; with_levels=%s): %s'
                          % (fname, pos, len(d), with_levels, e))
    if pos > len(d):
        raise ObjectError('%s: read %d bytes past the end (with_levels=%s)' % (fname, pos - len(d), with_levels))
    if pos != len(d) and d[pos:].strip(b'\0'):
        raise ObjectError('%s: %d bytes left over after the last object (with_levels=%s)'
                          % (fname, len(d) - pos, with_levels))
    return ver, objects, pos


def read_objects(file_path, with_levels=None, with_end=False):
    if with_levels is None:
        with_levels = uses_levels(file_path)
    d = open(file_path, 'rb').read()
    return read_objects_bytes(d, with_levels, fname=os.path.basename(file_path), with_end=with_end)


def write_objects_bytes(ver, objects, with_levels):
    if ver not in VERSIONS:
        raise ObjectError('write: version %r not supported (%s)' % (ver, VERSIONS))
    out = [struct.pack('<I', ver)]
    for table in (0, 1):
        cluster = [o for o in objects if o[0] == table]
        out.append(struct.pack('<I', len(cluster)))
        for _t, orig, new, mods in cluster:
            ids = (orig + new).encode('latin-1')
            if len(ids) != 8:
                raise ObjectError('write: ids %r/%r do not have 4 characters each' % (orig, new))
            out.append(ids + struct.pack('<I', len(mods)))
            for m in mods:
                field_id, kind, level, pointer, val = m[:5]
                end_pos = m[5] if len(m) > 5 else b'\0\0\0\0'
                field_bytes = field_id.encode('latin-1')
                if len(field_bytes) != 4 or len(end_pos) != 4:
                    raise ObjectError(
                        'write: field %r or end %r of object %r malformed' % (field_id, end_pos, new or orig)
                    )
                out.append(field_bytes + struct.pack('<I', kind))
                if with_levels:
                    out.append(struct.pack('<II', level, pointer))
                if kind == 0:
                    if not isinstance(val, int):
                        raise ObjectError('write: %r of %r is type 0 (int) and got %r' % (field_id, new or orig, val))
                    out.append(struct.pack('<i', val))
                elif kind in (1, 2):
                    out.append(struct.pack('<f', float(val)))
                elif kind == 3:
                    if not isinstance(val, (bytes, bytearray)) or b'\0' in val:
                        raise ObjectError('write: %r of %r is type 3 (text as bytes, without \\0) and got %r'
                                          % (field_id, new or orig, val))
                    out.append(bytes(val) + b'\0')
                else:
                    raise ObjectError('write: value type %r in field %r of object %r' % (kind, field_id, new or orig))
                out.append(end_pos)
    return b''.join(out)


def legacy_value(kind, val):
    if kind == 0:
        return str(val)
    if kind in (1, 2):
        return repr(val)
    return val.decode('utf-8', 'surrogateescape')


def parse_w3x_objects(path, legacy_key=False, with_levels=None):
    if not os.path.exists(path):
        return {}
    _ver, objects, _pos = read_objects(path, with_levels)
    out = {}
    for _table, orig, new, mods in objects:
        if legacy_key:
            hash_key = orig if orig.strip('\0') else new
            rec = out.setdefault(hash_key, {})
            if orig.strip('\0'):
                rec['_base'] = new
        else:
            hash_key = new if new.strip('\0') else orig
            rec = out.setdefault(hash_key, {})
            if new.strip('\0'):
                rec['_base'] = orig
        for field_id, kind, level, _ptr, val in mods:
            rec[(field_id, level)] = legacy_value(kind, val)
    return out


def short_real(f):
    if f != f or f in (float('inf'), float('-inf')):
        return repr(f)
    tgt = struct.unpack('<f', struct.pack('<f', f))[0]
    s = repr(f)
    for digits in range(1, 10):
        t = '%.*g' % (digits, f)
        if struct.unpack('<f', struct.pack('<f', float(t)))[0] == tgt:
            s = t
            break
    s = format(decimal.Decimal(s), 'f')
    if '.' in s:
        s = s.rstrip('0').rstrip('.')
    return '0' if s in ('', '-0') else s


RX_TRIGSTR = re.compile(r'^TRIGSTR_(\d+)$')


def read_wts(file_path):
    return dict(common_module('wts_refs').read_wts(file_path))


def resolve_trigstr(body_text, wts, missed=None):
    m = RX_TRIGSTR.match(body_text)
    if not m:
        return body_text
    n = int(m.group(1))
    if n in wts:
        return wts[n]
    if missed is not None:
        missed.add(n)
    return body_text


def render(kind, val, wts=None, missed=None, count=None):
    if kind == 0:
        return str(val)
    if kind in (1, 2):
        return short_real(val)
    s = val.decode('utf-8', 'surrogateescape')
    r = resolve_trigstr(s, wts or {}, missed)
    if count is not None and r is not s:
        count['trigstr'] += 1
    return r


def w3i_balance(w3i_path):
    try:
        m = common_module('w3i').parse(open(w3i_path, 'rb').read())
    except Exception as e:
        return 'custom_v1', 'w3i unreadable (%s: %s): custom_v1 (TFT custom map)' % (type(e).__name__, e)
    melee = bool(m.get('flags', 0) & 0x0004)
    data_set = m.get('game_data_set', 0) or 0
    version_num = m.get('game_data_version', 1)
    if version_num not in (0, 1):
        version_num = 1
    if data_set == 0:
        kind = 'melee' if melee else 'custom'
    elif data_set == 1:
        kind = 'custom'
    elif data_set == 2:
        kind = 'melee'
    else:
        kind = 'custom'
    reason = ('w3i version %d, flags 0x%X (%s), game_data_set %d, data %s'
              % (m.get('version', 0), m.get('flags', 0), 'melee' if melee else 'custom', data_set,
                 'v%d' % version_num + ('' if 'game_data_version' in m else ' (w3i < 31: TFT)')))
    if kind == 'melee' and version_num == 1:
        return None, reason + ' -> the base (TFT melee)'
    return '%s_v%d' % (kind, version_num), reason + ' -> %s_v%d' % (kind, version_num)


OBJ_KINDS = {
    'unit': {
        'slk': ['units\\unitdata.slk', 'units\\unitbalance.slk', 'units\\unitui.slk',
                'units\\unitweapons.slk', 'units\\unitabilities.slk'],
        'txt': ['units\\*unitfunc.txt', 'units\\unitweaponsfunc.txt', 'units\\unitskin.txt',
                'units\\unitweaponsskin.txt'],
        'locale': ['units\\*unitstrings.txt', 'units\\unitskinstrings.txt'],
        'meta': 'units\\unitmetadata.slk',
        'map_path': 'war3map.w3u',
    },
    'item': {
        'slk': ['units\\itemdata.slk'],
        'txt': ['units\\itemfunc.txt', 'units\\itemskin.txt'],
        'locale': ['units\\itemstrings.txt', 'units\\itemskinstrings.txt'],
        'meta': 'units\\unitmetadata.slk',
        'map_path': 'war3map.w3t',
    },
    'ability': {
        'slk': ['units\\abilitydata.slk'],
        'txt': ['units\\*abilityfunc.txt', 'units\\abilityskin.txt'],
        'locale': ['units\\*abilitystrings.txt', 'units\\abilityskinstrings.txt'],
        'meta': 'units\\abilitymetadata.slk',
        'map_path': 'war3map.w3a',
    },
}
LETTERS = 'ABCDEFGHIJ'


def _unquoted(v):
    if len(v) >= 2 and v[0] == '"' and v[-1] == '"':
        return v[1:-1]
    return v


def _raw_ini(raw):
    txt = raw.decode('utf-8', 'surrogateescape')
    out = {}
    cur = None
    for ln in txt.split('\n'):
        ln = ln.rstrip('\r')
        if not ln or ln.startswith('//') or ln.startswith(';'):
            continue
        m = re.match(r'^\[([^\]]+)\]\s*$', ln)
        if m:
            cur = out.setdefault(m.group(1), {})
            continue
        if cur is None or '=' not in ln:
            continue
        k, v = ln.split('=', 1)
        cur[k.strip().lower()] = v.strip()
    return out


def _variants(sec):
    out = {}
    sd = {}
    for k, v in sec.items():
        if ':' in k:
            base, var = k.split(':', 1)
            if var == 'sd':
                sd[base] = v
            continue
        out[k] = v
    for k, v in sd.items():
        out.setdefault(k, v)
    return out


def _split_levels(field_value):
    pieces, buf, inside = [], [], False
    for c in field_value:
        if c == '"':
            inside = not inside
            buf.append(c)
        elif c == ',' and not inside:
            pieces.append(''.join(buf))
            buf = []
        else:
            buf.append(c)
    pieces.append(''.join(buf))
    return pieces


def _int(v, default_value):
    try:
        return int(str(v).strip())
    except (TypeError, ValueError):
        return default_value


def value_levels(raw_data, n_levels):
    if raw_data is None or raw_data == '':
        return []
    pieces = _split_levels(raw_data)
    quoted = all(len(p.strip()) >= 2 and p.strip()[0] == '"' and p.strip()[-1] == '"' for p in pieces)
    if len(pieces) > 1 and (quoted or len(pieces) == _int(n_levels, 0)):
        return [_unquoted(p.strip()) for p in pieces]
    return [_unquoted(raw_data)]


class GameBase(object):
    def __init__(self, casc=None, game=None, balance='custom_v1', locale='enus'):
        casc_wc3 = common_module('casc_wc3')
        self.casc = casc if casc is not None else casc_wc3.CascWC3(game or casc_wc3.DEFAULT_GAME)
        self.balance = balance or None
        self.locale = (locale or 'enus').lower()
        self.read_count = []
        self.warnings = []
        self._tab = {}
        self._raw = {}
        self._meta = {}

    def _has(self, cpath):
        return cpath.lower() in self.casc.file_set

    def resolve(self, details):
        details = details.replace('/', '\\').lower()
        cands = []
        if self.balance:
            cands.append('war3.w3mod:_balance\\%s.w3mod:%s' % (self.balance, details))
        cands.append('war3.w3mod:' + details)
        for c in cands:
            if self._has(c):
                return c
        return None

    def resolve_locale(self, details):
        c = 'war3.w3mod:_locales\\%s.w3mod:%s' % (self.locale, details.replace('/', '\\').lower())
        return c if self._has(c) else None

    def _names(self, default_value, locale=False):
        details = default_value.replace('/', '\\').lower()
        cut = min([i for i in (details.find('*'), details.find('?'), details.find('[')) if i >= 0] or [len(details)])
        literal = details[:cut]
        if locale:
            prefixes = ['war3.w3mod:_locales\\%s.w3mod:' % self.locale]
        else:
            prefixes = ['war3.w3mod:']
            if self.balance:
                prefixes.append('war3.w3mod:_balance\\%s.w3mod:' % self.balance)
        name_list = set()
        for pre in prefixes:
            first_pos = pre + literal
            for k in self.casc.file_set:
                if k.startswith(first_pos):
                    rest = k[len(pre):]
                    if ':' not in rest and fnmatch.fnmatchcase(rest, details):
                        name_list.add(rest)
        return sorted(name_list)

    def read_data(self, cpath):
        self.read_count.append(cpath)
        return self.casc.read_data(cpath)

    def metadata(self, obj_kind):
        details = OBJ_KINDS[obj_kind]['meta']
        if details not in self._meta:
            cpath = self.resolve(details)
            if cpath is None:
                raise ObjectError('the CASC has no %s' % details)
            _h, rows = slk.parse_slk_bytes(self.read_data(cpath))
            self._meta[details] = rows
        return self._meta[details]

    def table(self, obj_kind):
        if obj_kind in self._tab:
            return self._tab[obj_kind]
        cfg = OBJ_KINDS[obj_kind]
        tab = {}
        for details in cfg['slk']:
            cpath = self.resolve(details)
            if cpath is None:
                self.warnings.append('the CASC has no %s' % details)
                continue
            _h, rows = slk.parse_slk_bytes(self.read_data(cpath))
            for rid, row in rows.items():
                dst = tab.setdefault(rid, {})
                for k, v in row.items():
                    if v != '' and v is not None:
                        dst[k.lower()] = v
        ids = set(tab)
        raw_data = {}
        sources = []
        for pad in cfg['txt']:
            sources += [self.resolve(n) for n in self._names(pad)]
        for pad in cfg['locale']:
            sources += [self.resolve_locale(n) for n in self._names(pad, locale=True)]
        for cpath in sources:
            if cpath is None:
                continue
            for sid, sec in _raw_ini(self.read_data(cpath)).items():
                if sid not in ids:
                    continue
                dst = tab[sid]
                c = raw_data.setdefault(sid, {})
                for k, v in _variants(sec).items():
                    s = _unquoted(v)
                    if s == '':
                        continue
                    dst[k] = s
                    c[k] = v
        self._tab[obj_kind] = tab
        self._raw[obj_kind] = raw_data
        return tab

    def raw_data(self, obj_kind):
        self.table(obj_kind)
        return self._raw[obj_kind]


def _multipart(meta):
    clusters = collections.defaultdict(set)
    for m in meta.values():
        idx = _int(m.get('index'), -1)
        if idx >= 0:
            clusters[((m.get('slk') or ''), (m.get('field') or '').lower())].add(idx)
    return set(k for k, v in clusters.items() if len(v) > 1)


def _tips_per_level(meta):
    return set((m.get('field') or '').lower() for m in meta.values()
               if (m.get('slk') or '') == 'Profile' and _int(m.get('repeat'), 0) > 0)


def apply_modifications(obj_kind, rec, raw_data, mods, meta, multi, per_level, wts, details):
    level_list = {}
    for field_id, kind, level, _ptr, val in mods:
        m = meta.get(field_id)
        if m is None:
            details['unknown_fields'][field_id] += 1
            continue
        s = render(kind, val, wts, details['missing_trigstr'], details['count'])
        fname = (m.get('field') or '').lower()
        origin = m.get('slk') or ''
        idx = _int(m.get('index'), -1)
        rep = _int(m.get('repeat'), 0)
        if obj_kind == 'ability' and origin != 'Profile':
            datum = _int(m.get('data'), 0)
            col = fname + (LETTERS[datum - 1].lower() if 0 < datum <= len(LETTERS) else '')
            if rep > 0:
                col += str(max(level, 1))
            rec[col] = s
        elif obj_kind == 'ability' and fname in per_level:
            listing = level_list.get(fname)
            if listing is None:
                listing = level_list[fname] = value_levels(raw_data.get(fname), rec.get('levels'))
            i = max(level, 1) - 1
            while len(listing) <= i:
                listing.append('')
            listing[i] = s
        elif (origin, fname) in multi and idx >= 0:
            pieces = rec.get(fname, '').split(',') if rec.get(fname) else []
            while len(pieces) <= idx:
                pieces.append('')
            pieces[idx] = s
            rec[fname] = ','.join(pieces)
        else:
            rec[fname] = s
    return level_list


def w3u_tables(folder, base=None, balance='auto', locale='enus', game=None, wts=None, allowed=None,
               stats=None):
    details = stats if stats is not None else {}
    if wts is None:
        p = os.path.join(folder, 'war3map.wts')
        wts = read_wts(p) if os.path.isfile(p) else {}
        details['wts'] = p if os.path.isfile(p) else None
    elif isinstance(wts, str):
        details['wts'] = wts
        wts = read_wts(wts)
    if base is None:
        if balance == 'auto':
            balance, reason = w3i_balance(os.path.join(folder, 'war3map.w3i'))
        else:
            reason = 'chosen in the call'
        details['balance_reason'] = reason
        base = GameBase(game=game, balance=balance, locale=locale)
    details['balance'] = base.balance
    details['locale'] = base.locale
    details['casc'] = getattr(base.casc, 'version_num', '?')
    details['wts_texts'] = len(wts)
    details.setdefault('unknown_fields', collections.Counter())
    details.setdefault('missing_trigstr', set())
    details.setdefault('count', collections.Counter())
    details.setdefault('objects', {})
    output = {}
    for obj_kind in ('unit', 'ability', 'item'):
        default_value = base.table(obj_kind)
        raw_base = base.raw_data(obj_kind)
        meta = base.metadata(obj_kind)
        multi = _multipart(meta)
        per_level = _tips_per_level(meta) if obj_kind == 'ability' else set()
        tab = dict((k, dict(v)) for k, v in default_value.items())
        obj_levels = {}
        bases = {}
        ro = {'game_base': len(default_value), 'originals': 0, 'new_ones': 0, 'mods': 0, 'no_base': []}
        file_ = os.path.join(folder, OBJ_KINDS[obj_kind]['map_path'])
        if os.path.isfile(file_):
            _ver, objects, _pos = read_objects(file_)
            for table, orig, new, mods in objects:
                hash_key = new if new.strip('\0') else orig
                if orig not in default_value:
                    ro['no_base'].append((hash_key, orig))
                rec = dict(default_value.get(orig, {}))
                obj_levels[hash_key] = apply_modifications(obj_kind, rec, raw_base.get(orig, {}), mods, meta,
                                                           multi, per_level, wts, details)
                bases[hash_key] = orig
                tab[hash_key] = rec
                ro['new_ones' if table else 'originals'] += 1
                ro['mods'] += len(mods)
        if obj_kind == 'ability':
            for aid, rec in tab.items():
                touched = obj_levels.get(aid, {})
                raw_data = raw_base.get(bases.get(aid, aid), {})
                for fname in per_level:
                    listing = touched.get(fname)
                    if listing is None:
                        if fname not in raw_data:
                            continue
                        listing = value_levels(raw_data[fname], rec.get('levels'))
                    if not listing:
                        continue
                    rec[fname] = listing[0]
                    if len(listing) > 1:
                        rec[fname + '_lv'] = list(listing)
                    else:
                        rec.pop(fname + '_lv', None)
        if allowed is not None:
            ok = allowed.get(obj_kind, set())
            for rid in list(tab):
                tab[rid] = dict((k, v) for k, v in tab[rid].items()
                                if k in ok or (k.endswith('_lv') and k[:-3] in ok))
        details['objects'][obj_kind] = ro
        output[obj_kind] = tab
    details['casc_read'] = list(base.read_count)
    details['warnings'] = list(base.warnings)
    return output['unit'], output['ability'], output['item']


METADATA_TYPE = {'int': 0, 'bool': 0, 'real': 1, 'unreal': 2, 'itemClass': 3, 'techList': 3, 'string': 3,
                 'stringList': 3, 'unitList': 3, 'abilityList': 3, 'itemList': 3, 'upgradeList': 3,
                 'model': 3, 'icon': 3}


def _normal(field_value, kind):
    v = (
        ''
        if field_value is None
        else (','.join(field_value) if isinstance(field_value, list) else str(field_value)).strip()
    )
    if v in ('-', '_'):
        v = ''
    if kind == 0:
        try:
            return int(float(v)) if v else 0
        except ValueError:
            return v
    if kind in (1, 2):
        try:
            return float(v) if v else 0.0
        except ValueError:
            return v
    return v


def _typed_value(normal, kind):
    if kind == 0:
        return int(normal)
    if kind in (1, 2):
        return float(normal)
    return str(normal).encode('utf-8')


def divergent_inheritance(objects, obj_kind, codes, current, classic):
    meta = current.metadata(obj_kind)
    current_tab, classic_tab = current.table(obj_kind), classic.table(obj_kind)
    fields = []
    for code_part in codes:
        m = meta.get(code_part)
        if m is None:
            raise ObjectError('inheritance: the metadata of %s has no field %r' % (obj_kind, code_part))
        if _int(m.get('repeat'), 0) > 0:
            raise ObjectError(
                'inheritance: %r is a per-level field (repeat=%s): not supported' % (code_part, m.get('repeat'))
            )
        kind = METADATA_TYPE.get(m.get('type'))
        if kind is None:
            raise ObjectError(
                'inheritance: type %r of field %r is outside the METADATA_TYPE table' % (m.get('type'), code_part)
            )
        fields.append((code_part, (m.get('field') or '').lower(), kind))
    listing, no_classic = [], []
    for _table, orig, new, mods in objects:
        hash_key = new if new.strip('\0') else orig
        save = set(mm[0] for mm in mods)
        if orig not in classic_tab:
            no_classic.append((hash_key, orig))
            continue
        for code_part, fname, kind in fields:
            if code_part in save:
                continue
            current_val = _normal(current_tab.get(orig, {}).get(fname), kind)
            classic_val = _normal(classic_tab.get(orig, {}).get(fname), kind)
            if current_val != classic_val:
                listing.append((hash_key, orig, code_part, kind, _typed_value(classic_val, kind), current_val))
    return listing, no_classic


def add_modifications(objects, listing, meta=None):
    by_id = collections.defaultdict(list)
    for hash_key, _orig, code_part, kind, field_value, _current_val in listing:
        by_id[hash_key].append((code_part, kind, field_value))
    output = []
    for table, orig, new, mods in objects:
        hash_key = new if new.strip('\0') else orig
        extra = [(code_part, kind, 0, _int((meta or {}).get(code_part, {}).get('data'), 0), field_value, b'\0\0\0\0')
                 for code_part, kind, field_value in by_id.get(hash_key, [])]
        output.append((table, orig, new, list(mods) + extra))
    return output

