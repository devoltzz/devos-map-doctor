# Compares two versions of a map: files, map info, objects, script functions and strings.
import difflib
import math
import os
import struct

from doctor.fix import unprotect
from doctor.script import jass_ast
from doctor.script import lua_ast
from doctor.mpq import mpqdoctor
from doctor.mpq import mpqnames
from doctor.data import objbin
from doctor.data import object_names
from doctor.data import slk
from doctor.data import slk_patch
from doctor.translation import translation_io
from doctor.data import w3i


OBJECT_FILES = tuple(p + e for p in ('war3map.', 'war3mapSkin.') for e in ('w3u', 'w3t', 'w3a', 'w3b', 'w3d', 'w3h',
                                                                           'w3q'))
EXTRA_NAMES = ('scripts\\war3map.j', 'war3map.lua')
MPQ_FILE_FIX_KEY = 0x00020000


def _nothing(*_a, **_k):
    pass


def _text(s):
    if isinstance(s, bytes):
        s = s.decode('utf-8', 'surrogateescape')
    return s.encode('utf-8', 'surrogateescape').decode('utf-8', 'replace')


def _listed(a):
    listed = unprotect.listfile_names(a)
    if listed:
        return listed, 'listfile'
    return unprotect.map_names(a), 'mined'


def _names(maps):
    lists = [_listed(a) for a in maps]
    known = {}
    for n in [n for listed, _o in lists for n in listed] + list(mpqnames.BASE_NAMES) + list(mpqdoctor.PROBES) + \
            list(slk_patch.TABLES) + list(slk_patch.PROFILES) + list(EXTRA_NAMES):
        if n.lower() not in unprotect.SPECIAL_FILES:
            known.setdefault(n.upper(), n)
    out = []
    for a in maps:
        present = {}
        for key, n in known.items():
            try:
                if a.find(n):
                    present[key] = n
            except Exception:
                pass
        out.append(present)
    return out, [o for _l, o in lists]


def _block(a, name):
    r = a.find_locale(name) if a.find(name) else None
    return r[1] if r else None


def _raw(a, bi):
    off, cs, fs, fl = a.blocks[bi]
    p = (a.h.offset + off) & 0xFFFFFFFF
    return a.d[p:p + cs], fs, fl, off


def _unnamed(a, blocks):
    alive = unprotect._live_blocks(a)
    return len(alive - set(blocks))


def _files(a, b, na, nb, read_a, read_b):
    out = {'added': [], 'removed': [], 'changed': [], 'same': [], 'unreadable': []}
    used_a, used_b = [], []
    for key in sorted(set(na) | set(nb), key=lambda k: (k.lower(), k)):
        name = nb.get(key) or na.get(key)
        ba = _block(a, na[key]) if key in na else None
        bb = _block(b, nb[key]) if key in nb else None
        used_a.append(ba)
        used_b.append(bb)
        if ba is not None and bb is not None:
            ra, rb = _raw(a, ba), _raw(b, bb)
            if ra[:3] == rb[:3] and (not ra[2] & MPQ_FILE_FIX_KEY or ra[3] == rb[3]):
                out['same'].append({'name': name, 'size': ra[1]})
                continue
        da = read_a(na[key]) if key in na else None
        db = read_b(nb[key]) if key in nb else None
        if (key in na and da is None) or (key in nb and db is None):
            out['unreadable'].append(name)
        elif da is None:
            out['added'].append({'name': name, 'size': len(db)})
        elif db is None:
            out['removed'].append({'name': na[key], 'size': len(da)})
        elif da == db:
            out['same'].append({'name': name, 'size': len(da)})
        else:
            out['changed'].append({'name': name, 'size_a': len(da), 'size_b': len(db)})
    out['unnamed_a'] = _unnamed(a, used_a)
    out['unnamed_b'] = _unnamed(b, used_b)
    return out


def _leaf(v):
    if isinstance(v, bytes):
        s = v.decode('utf-8', 'replace')
        if any(ord(c) < 32 and c not in '\r\n\t' for c in s) or '\ufffd' in s:
            return v.hex()
        return s
    return v


def _flatten(prefix, v, out):
    if isinstance(v, dict):
        for k in v:
            if k != '_tail':
                _flatten('%s.%s' % (prefix, k) if prefix else k, v[k], out)
    elif isinstance(v, (list, tuple)):
        out[prefix + '.count'] = len(v)
        for i, x in enumerate(v):
            _flatten('%s[%d]' % (prefix, i), x, out)
    else:
        out[prefix] = _leaf(v)


def _info(da, db):
    res = {'changed': [], 'error': None}
    flat = []
    for d in (da, db):
        f = {}
        if d:
            try:
                _flatten('', w3i.parse_or_tolerant(d), f)
            except Exception as e:
                res['error'] = 'war3map.w3i unreadable (%s)' % translation_io._error(e)
        flat.append(f)
    for k in sorted(set(flat[0]) | set(flat[1])):
        x, y = flat[0].get(k), flat[1].get(k)
        if x != y:
            res['changed'].append({'field': k, 'a': x, 'b': y})
    return res


def _value(vt, val):
    if vt == 3:
        return _text(val)
    if vt == 0:
        return struct.unpack('<i', val)[0]
    x = struct.unpack('<f', val)[0]
    return x if math.isfinite(x) else repr(x)


def _objects_of(data, levels):
    out = {}
    _v, tables, _end = objbin.read_data(data, levels)
    for ti, table in enumerate(tables):
        for old, new, mods in table:
            ident = new if ti == 1 else old
            fields = out.setdefault(ident, (old, {}))[1]
            for mid, vt, lvl, _dptr, val in mods:
                fields[(mid, lvl or 0)] = _value(vt, val)
    return out


def _rows_compare(ra, rb, names, bases=None):
    bases = bases or {}
    res = {'added': [], 'removed': [], 'changed': [], 'error': None}

    def row(ident):
        r = {'id': ident, 'name': names.get(ident)}
        if bases.get(ident, ident) != ident:
            r['base'] = bases[ident]
        return r
    for ident in sorted(set(ra) | set(rb)):
        if ident not in ra:
            res['added'].append(row(ident))
        elif ident not in rb:
            res['removed'].append(row(ident))
        elif ra[ident] != rb[ident]:
            fa, fb = ra[ident], rb[ident]
            fields = []
            for k in sorted(set(fa) | set(fb), key=lambda k: k if isinstance(k, tuple) else (k, 0)):
                if fa.get(k) != fb.get(k):
                    field, level = k if isinstance(k, tuple) else (k, 0)
                    fields.append({'field': field, 'level': level or None, 'a': fa.get(k), 'b': fb.get(k)})
            res['changed'].append(dict(row(ident), fields=fields))
    return res


def _objects(read_a, read_b, na, nb):
    out = {}
    names = {}
    for read in (read_a, read_b):
        try:
            names.update(object_names.names(read, game=False))
        except Exception:
            pass
    for name in OBJECT_FILES:
        da, db = read_a(name), read_b(name)
        if not da and not db:
            continue
        levels = name.lower() in objbin.WITH_LEVELS
        tables, bases, error = [], {}, None
        for d in (da, db):
            try:
                objects = _objects_of(d, levels) if d else {}
            except Exception as e:
                objects = {}
                error = 'unreadable (%s)' % translation_io._error(e)
            bases.update((k, v[0]) for k, v in objects.items())
            tables.append(dict((k, v[1]) for k, v in objects.items()))
        res = _rows_compare(tables[0], tables[1], names, bases)
        res['error'] = error
        if res['added'] or res['removed'] or res['changed'] or error:
            out[name] = res
    files_a = slk_patch.table_files(list(na.values()), read_a)
    files_b = slk_patch.table_files(list(nb.values()), read_b)
    by_key = {}
    for f in (files_a, files_b):
        for n in f:
            by_key.setdefault(n.lower(), n)
    for low, name in sorted(by_key.items()):
        if not low.endswith(('.slk', '.txt')):
            continue
        da = next((v for k, v in files_a.items() if k.lower() == low), None)
        db = next((v for k, v in files_b.items() if k.lower() == low), None)
        if da == db:
            continue
        tables, error = [], None
        for d in (da, db):
            try:
                if not d:
                    tables.append({})
                elif low.endswith('.slk'):
                    tables.append(dict((_text(k), dict((_text(c), _text(x)) for c, x in v.items()))
                                       for k, v in slk.parse_slk_bytes(d)[1].items()))
                else:
                    tables.append(dict((_text(k), dict((_text(c), _text(x)) for c, x in v.items()))
                                       for k, v in slk.parse_ini_bytes(d).items()))
            except Exception as e:
                tables.append({})
                error = 'unreadable (%s)' % translation_io._error(e)
        res = _rows_compare(tables[0], tables[1], names)
        res['error'] = error
        if res['added'] or res['removed'] or res['changed'] or error:
            out[name] = res
    return out


def _changed_lines(a, b):
    n = 0
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op != 'equal':
            n += max(i2 - i1, j2 - j1)
    return n


def _jass_parts(text):
    s = jass_ast.parse(text)
    functions = {}
    for f in s.functions:
        c = jass_ast.canonical(f)
        functions.setdefault(f.name, (c, c.splitlines()))
    globals_ = {}
    for g in s.globals:
        init = jass_ast.unparse(g.initializer) if g.initializer is not None else None
        globals_.setdefault(g.name, (g.type, g.is_array, g.is_constant, init))
    return functions, globals_


def _lua_parts(text):
    chunk = lua_ast.parse(text)
    functions = {}
    for name, node in chunk.functions.items():
        functions[name] = (lua_ast.canonical(node), lua_ast.unparse(node).splitlines())
    return functions, {}


def _script(a, b, read_a, read_b):
    res = {'language_a': None, 'language_b': None, 'added': [], 'removed': [], 'changed': [],
           'globals': {'added': [], 'removed': [], 'changed': []}, 'error': None}
    sides = []
    for arch, read, key in ((a, read_a, 'language_a'), (b, read_b, 'language_b')):
        lang, _name, data = translation_io.script_language(arch, read)
        res[key] = lang
        sides.append((lang, data))
    if sides[0][0] != sides[1][0]:
        res['error'] = 'the two maps have different scripts (%s, %s)' % (sides[0][0], sides[1][0])
        return res
    lang = sides[0][0]
    if lang not in ('jass', 'lua'):
        if sides[0][1] != sides[1][1]:
            res['error'] = 'the script (%s) cannot be compared by function' % lang
        return res
    if sides[0][1] == sides[1][1]:
        return res
    parts = []
    for _lang, data in sides:
        text = data.decode('utf-8', 'surrogateescape')
        try:
            parts.append(_jass_parts(text) if lang == 'jass' else _lua_parts(text))
        except Exception as e:
            res['error'] = 'the script cannot be parsed (%s)' % translation_io._error(e)
            return res
    (fa, ga), (fb, gb) = parts
    for name in sorted(set(fa) | set(fb)):
        if name not in fa:
            res['added'].append({'name': name, 'lines': len(fb[name][1])})
        elif name not in fb:
            res['removed'].append({'name': name, 'lines': len(fa[name][1])})
        elif fa[name][0] != fb[name][0]:
            res['changed'].append({'name': name, 'lines_a': len(fa[name][1]), 'lines_b': len(fb[name][1]),
                                   'lines_changed': _changed_lines(fa[name][1], fb[name][1])})
    for name in sorted(set(ga) | set(gb)):
        if name not in ga:
            res['globals']['added'].append(name)
        elif name not in gb:
            res['globals']['removed'].append(name)
        elif ga[name] != gb[name]:
            res['globals']['changed'].append(name)
    return res


def _strings(da, db):
    sa, sb = object_names.strings(da), object_names.strings(db)
    res = {'added': [], 'removed': [], 'changed': []}
    for n in sorted(set(sa) | set(sb)):
        if n not in sa:
            res['added'].append({'id': n, 'text': _text(sb[n])})
        elif n not in sb:
            res['removed'].append({'id': n, 'text': _text(sa[n])})
        elif sa[n] != sb[n]:
            res['changed'].append({'id': n, 'a': _text(sa[n]), 'b': _text(sb[n])})
    return res


def _side(path, a, origin, script):
    return {'path': path, 'size': len(a.d), 'names_from': origin, 'script': script}


def compare(path_a, path_b, progress=None):
    p = progress or _nothing
    res = {'a': None, 'b': None, 'files': None, 'info': None, 'objects': None, 'script': None, 'strings': None,
           'error': None}
    try:
        p('reading maps')
        archives = []
        for path in (path_a, path_b):
            try:
                archives.append(translation_io._open(path))
            except (Exception, SystemExit) as e:
                raise RuntimeError('cannot read %s (%s)' % (os.path.basename(path), translation_io._error(e)))
        a, b = archives

        def read_a(name):
            return translation_io._read_uncached(a, name)

        def read_b(name):
            return translation_io._read_uncached(b, name)
        p('file names')
        with unprotect.quiet():
            (na, nb), (oa, ob) = _names((a, b))
        p('files')
        res['files'] = _files(a, b, na, nb, read_a, read_b)
        p('map info')
        res['info'] = _info(read_a('war3map.w3i'), read_b('war3map.w3i'))
        p('object data')
        res['objects'] = _objects(read_a, read_b, na, nb)
        p('script')
        res['script'] = _script(a, b, read_a, read_b)
        p('strings')
        res['strings'] = _strings(read_a('war3map.wts'), read_b('war3map.wts'))
        res['a'] = _side(path_a, a, oa, res['script']['language_a'])
        res['b'] = _side(path_b, b, ob, res['script']['language_b'])
    except Exception as e:
        res['error'] = translation_io._error(e)
    return res


def summary(res):
    if res['error'] and not res['files']:
        return ['error: ' + res['error']]
    f = res['files']
    out = ['files: %d added, %d removed, %d changed, %d same (unnamed: %d / %d)' % (
        len(f['added']), len(f['removed']), len(f['changed']), len(f['same']), f['unnamed_a'], f['unnamed_b'])]
    out += ['   changed %s (%d -> %d bytes)' % (x['name'], x['size_a'], x['size_b']) for x in f['changed'][:15]]
    out.append('map info: %d fields differ%s' % (len(res['info']['changed']),
                                                  ' (%s)' % res['info']['error'] if res['info']['error'] else ''))
    for name, o in sorted((res['objects'] or {}).items()):
        out.append('%s: %d added, %d removed, %d changed%s' % (name, len(o['added']), len(o['removed']),
                                                              len(o['changed']), ' (%s)' % o['error'] if o['error']
                                                              else ''))
    s = res['script'] or {}
    if s:
        out.append('script (%s): %d functions added, %d removed, %d changed; globals %d/%d/%d%s' % (
            s['language_b'], len(s['added']), len(s['removed']), len(s['changed']), len(s['globals']['added']),
            len(s['globals']['removed']), len(s['globals']['changed']), ' (%s)' % s['error'] if s['error'] else ''))
    st = res['strings'] or {}
    if st:
        out.append('strings: %d added, %d removed, %d changed' % (len(st['added']), len(st['removed']),
                                                                 len(st['changed'])))
    if res['error']:
        out.append('error: ' + res['error'])
    return out
