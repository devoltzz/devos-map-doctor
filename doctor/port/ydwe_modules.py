# Finds the Lua modules of a YDWE Lua engine map (Lua 5.3 bytecode or text) and the name each one is required by.
import re

from doctor.script import lua_bytecode


ENGINE_TEMPLATES = ('?.lua', '?\\init.lua', 'scripts\\?.lua', 'scripts\\?\\init.lua', 'script\\?.lua',
                    'script\\?\\init.lua', 'w3x2lni\\plugin\\import\\scripts\\?.lua')
RX_TEXT = re.compile(rb'^(?:\xef\xbb\xbf)?\s*(?:--|local\s|require\s*[\(\'"]|function\s|return\s|if\s|for\s|'
                     rb'[A-Za-z_\x80-\xff][\w.\x80-\xff]*\s*[=(:\[])')
RX_NAME_TOKEN = re.compile(r'^[^\s\\/:*?"<>|\x00-\x1f]{1,80}$')
DATA_EXTS = ('.ini', '.txt', '.json', '.lni', '.xml', '.slk', '.cfg', '.csv', '.lua', '.dat')
RX_CITED_FILE = re.compile(r'[\\/][^\\/]*\.[A-Za-z]\w{1,11}$')
EXT_MEDIA = ('.mdx', '.mdl', '.blp', '.tga', '.dds', '.png', '.jpg', '.mp3', '.wav', '.ogg', '.flac', '.mpq', '.w3x',
             '.w3m', '.dll', '.exe', '.ttf', '.lua')
DATA_CAP = 4 << 20


def _decode_name(b):
    return b.decode('utf-8', 'surrogateescape')


def _spellings(fname):
    if fname.isascii():
        return [fname]
    out = [fname]
    b = fname.encode('utf-8', 'surrogateescape')
    if max(b, default=0) < 0x80:
        return out
    try:
        out.append(b.decode('gbk'))
    except UnicodeDecodeError:
        pass
    try:
        out.append(b.decode('utf-8').encode('gbk').decode('utf-8', 'surrogateescape'))
    except (UnicodeDecodeError, UnicodeEncodeError):
        pass
    return list(dict.fromkeys(out))


_PAIR_TABLE = {}


def _pairs_of(a):
    k = id(a)
    p = _PAIR_TABLE.get(k)
    if p is None or p[0] is not a:
        ht = a.ht
        p = (a, set((ht[4 * i], ht[4 * i + 1]) for i in range(len(ht) // 4) if ht[4 * i + 3] < 0xFFFFFFFE))
        _PAIR_TABLE.clear()
        _PAIR_TABLE[k] = p
    return p[1]


_VAR = {}


def _variants(s):
    v = _VAR.get(s, False)
    if v is not False:
        return v
    if s.isascii():
        v = None
    else:
        b = s.encode('utf-8', 'surrogateescape')
        v = {'raw_data': s}
        try:
            v['g'] = b.decode('gbk')
        except UnicodeDecodeError:
            pass
        try:
            v['u'] = b.decode('utf-8').encode('gbk').decode('utf-8', 'surrogateescape')
        except (UnicodeDecodeError, UnicodeEncodeError):
            pass
    if len(_VAR) > 400000:
        _VAR.clear()
    _VAR[s] = v
    return v


def _combine(pieces):
    vs = [_variants(p) for p in pieces]
    if all(v is None for v in vs):
        return [''.join(pieces)]
    label_set = None
    for v in vs:
        if v is not None:
            label_set = set(v) if label_set is None else label_set & set(v)
    return list(dict.fromkeys(''.join(p if v is None else v[r] for p, v in zip(pieces, vs))
                              for r in ('raw_data', 'g', 'u') if r in label_set))


def existing_ones(a, cands):
    from doctor.mpq import mpqlib
    pairs = _pairs_of(a)
    listing = [(''.join(c), g) if isinstance(c, tuple) else (c, g)
               for c in cands for g in (_combine(c) if isinstance(c, tuple) else _spellings(c))]
    if not listing:
        return []
    bs = [g.replace('/', '\\').encode('utf-8', 'surrogateescape') for _c, g in listing]
    h1 = mpqlib.hashstr_batch(bs, 1)
    h2 = mpqlib.hashstr_batch(bs, 2)
    return [listing[i] for i in range(len(listing)) if (int(h1[i]), int(h2[i])) in pairs]


_LABEL_CODE = {'raw_data': 0, 'g': 1, 'u': 2}
_SEARCH = []


def _native_search():
    if not _SEARCH:
        try:
            from doctor.script import jass_native
            _SEARCH.append(jass_native.load_names())
        except Exception:
            _SEARCH.append(None)
    return _SEARCH[0]


def existing_product(a, folders, name_list, exts):
    lookup = _native_search()
    if lookup is None:
        return existing_ones(a, [(p, n, e) for p in folders for n in name_list for e in exts])

    def item_entries(listing):
        out = []
        for s in listing:
            v = _variants(s)
            if v is None:
                out.append(s.encode('ascii'))
            else:
                out.append(dict((_LABEL_CODE[r], g.replace('/', '\\').encode('utf-8', 'surrogateescape'))
                                for r, g in v.items()))
        return out
    matches = lookup(item_entries(folders), item_entries(name_list), item_entries(exts), _pairs_of(a))
    if matches is None:
        return existing_ones(a, [(p, n, e) for p in folders for n in name_list for e in exts])
    label_set = dict((v, k) for k, v in _LABEL_CODE.items())
    out = []
    for i, j, k, r in sorted(matches):
        pieces = (folders[i], name_list[j], exts[k])
        g = ''.join(p if _variants(p) is None else _variants(p)[label_set[r]] for p in pieces)
        out.append((''.join(pieces), g))
    return out


def _block_of_name(a, fname, spelling=False):
    from doctor.mpq import mpqlib
    pairs = _pairs_of(a)
    for g in _spellings(fname):
        gb = g.replace('/', '\\')
        if (mpqlib.hashstr(gb, 1), mpqlib.hashstr(gb, 2)) not in pairs:
            continue
        try:
            r = a.find(g)
        except Exception:
            r = None
        if r is not None:
            return (r[1], g) if spelling else r[1]
    return (None, None) if spelling else None


def name_from_source(source):
    if not source:
        return None
    t = _decode_name(source.lstrip(b'@=')).replace('/', '\\')
    low = t.lower()
    i = low.rfind('\\map\\')
    if i >= 0:
        return t[i + 5:]
    return t.rsplit('\\', 1)[-1]


def _classify(d):
    if d[:4] == b'\x1bLua':
        return 'bytecode'
    if d[:2] == b'MZ':
        return 'dll'
    if b'\x00' not in d[:4096] and RX_TEXT.match(d[:300]):
        try:
            d[:65536].decode('utf-8')
        except UnicodeDecodeError as e:
            if not (len(d) > 65536 and e.start >= 65536 - 3):
                return None
        if b'end' in d or b'return' in d or _compile_lua(d):
            return 'body_text'
    return None


_LUA = []


def _compile_lua(d):
    try:
        if not _LUA:
            from lupa import lua53
            L = lua53.LuaRuntime(encoding=None)
            _LUA.append(L.eval('function(s) return load(s, "=m", "t", {}) ~= nil end'))
        if _LUA[0](d):
            return True
        from doctor.port import ydwe_port
        segments = ydwe_port._non_ascii_ids(d)
        if not segments:
            return False
        pieces, end_pos = [], 0
        for n, (i, j) in enumerate(segments):
            pieces += [d[end_pos:i], b'__ydwe_u%d__' % n]
            end_pos = j
        pieces.append(d[end_pos:])
        return bool(_LUA[0](b''.join(pieces)))
    except Exception:
        return False


def _text_strings(d):
    return [m.group(2) for m in re.finditer(rb'(["\'])((?:(?!\1)[^\\\r\n]|\\.){1,120})\1', d)]


def collect(a, hash_entries=(), log=None):
    from doctor.mpq import mpqnames
    log = log or (lambda s: None)
    block_list = {}
    dll = []
    for bi in a.pointed_blocks():
        d = mpqnames.read_unnamed(a, bi, whole=True)
        if d is None:
            continue
        if not d:
            block_list[bi] = ('body_text', b'')
            continue
        forma = _classify(d)
        if forma == 'dll':
            dll.append((bi, d))
        elif forma:
            block_list[bi] = (forma, d)
    name_list = {}
    origin = {}
    cited = set(hash_entries)
    paths = set()
    templates = list(ENGINE_TEMPLATES)
    for bi, (forma, d) in sorted(block_list.items()):
        if forma == 'bytecode':
            try:
                fn, _ = lua_bytecode.load(d)
            except Exception as e:
                log('   block %d: bytecode that does not load (%s)' % (bi, e))
                continue
            consts = lua_bytecode.strings(fn)
            n = name_from_source(fn.get('source'))
            if n:
                name_list.setdefault(bi, n)
                origin.setdefault(bi, 'debug')
        else:
            consts = _text_strings(d)
        for c in consts:
            t = _decode_name(c)
            if '?' in t and ('.lua' in t or ';' in t):
                for m in t.split(';'):
                    m = m.strip().replace('/', '\\')
                    if (
                        m.count('?') == 1
                        and m.endswith('.lua')
                        and ':' not in m
                        and '%' not in m
                        and m not in templates
                    ):
                        templates.append(m)
            elif RX_NAME_TOKEN.match(t) and not t.lower().endswith(('.mdx', '.mdl', '.blp', '.tga', '.mp3', '.wav')):
                cited.add(t)
            elif ('\\' in t or '/' in t) and len(t) < 400 and t.rstrip(';').endswith(('\\', '/')):
                paths.add(t)
            elif ('\\' in t or '/' in t) and len(t) < 260 and RX_CITED_FILE.search(t) and \
                    not t.lower().endswith(EXT_MEDIA):
                paths.add(t)
    for bi, n in list(name_list.items()):
        b, g = _block_of_name(a, n, spelling=True)
        if b is not None and b != bi:
            del name_list[bi]
            origin.pop(bi, None)
        elif b == bi:
            name_list[bi] = g
            origin[bi] = 'debug+hash'
    from_block = dict((b, n) for b, n in name_list.items())

    def try_batch(cands, matches=None):
        achou = 0
        for _c, g in (existing_ones(a, cands) if matches is None else matches):
            try:
                r = a.find(g)
            except Exception:
                r = None
            if r is not None and r[1] in block_list and (r[1] not in from_block or origin.get(r[1]) == 'debug'):
                from_block[r[1]] = g
                origin[r[1]] = 'hash'
                achou += 1
        return achou
    cands = []
    for c in sorted(cited):
        base = c.replace('.', '\\') if not c.lower().endswith('.lua') else c[:-4].replace('.', '\\')
        for m in templates:
            cands.append(m.replace('?', base))
            cands.append(m.replace('?', c))
    try_batch(cands)
    file_set = _storm_data(a, cited, block_list, paths, templates)
    from_data = set()
    for d in file_set.values():
        t = d.decode('utf-8', 'surrogateescape')
        from_data.update(m.group(1) or m.group(2) or m.group(3) for m in re.finditer(
            r'''^\s*\[\s*(?:"([^"\r\n]+)"|'([^'\r\n]+)'|([^\]\r\n]+?))\s*\]''', t, re.M))
        from_data.update(m.group(2) for m in re.finditer(r'''(["'])([^"'\r\n\\]{1,40})\1''', t))
    short_names = set(c for c in cited | from_data if '\\' not in c and '/' not in c and len(c) <= 40)
    short_names |= set((c[:-4] if c.lower().endswith('.lua') else c).replace('.', '\\') for c in cited
                       if '.' in c.strip('.') and '\\' not in c and '/' not in c and len(c) <= 60)
    short_names = sorted(short_names)
    prefixes = set(c.replace('.', '\\').rstrip('\\') for c in cited if c.endswith(('.', '\\', '/')) and len(c) > 1)
    visited = set()
    for _run_once in range(6):
        folders = set(n.rsplit('\\', 1)[0] for n in from_block.values() if '\\' in n)
        for p in prefixes:
            for m in templates:
                if m.endswith('?.lua'):
                    folders.add((m[:-5] + p).strip('\\'))
        added = folders - visited
        if not added or len(from_block) == len(block_list):
            break
        visited |= added
        matches = existing_product(a, [p + '\\' for p in sorted(added)], short_names, ['.lua', '\\init.lua'])
        if not try_batch(None, matches):
            break
    lua_modules = {}
    for bi, (forma, d) in sorted(block_list.items()):
        n = from_block.get(bi)
        if n is None:
            continue
        hash_key = n.replace('/', '\\')
        if hash_key.lower() in (k.lower() for k in lua_modules):
            continue
        lua_modules[hash_key] = {'block_entry': bi, 'data_bytes': d, 'forma': forma, 'origin': origin.get(bi, '?')}
    unnamed = sorted(bi for bi in block_list if bi not in from_block and block_list[bi][1])
    log(
        '   Lua modules: %d named (%d by debug info, %d by the MPQ hash), %d without a name; %d DLL(s); %d data '
        'file(s) for jass.storm'
        % (
            len(lua_modules),
            sum(1 for m in lua_modules.values() if m['origin'].startswith('debug')),
            sum(1 for m in lua_modules.values() if m['origin'] == 'hash'),
            len(unnamed),
            len(dll),
            len(file_set),
        )
    )
    return {'lua_modules': lua_modules, 'unnamed': unnamed, 'dll': dll, 'templates': templates, 'file_set': file_set}


RX_JASS_LITERAL = re.compile(r'"((?:[^"\\\r\n]|\\.){1,260})"')
ORIGINAL_CAP = 256 << 20


def originals(a, jass_text, col):
    import hashlib
    served = set(k.lower() for k in col.get('file_set', {}))
    cands = sorted(set(m.group(1).replace('\\\\', '\\') for m in RX_JASS_LITERAL.finditer(jass_text)
                       if '\n' not in m.group(1) and ' ' not in m.group(1).strip()))
    out = {}
    for c, g in existing_ones(a, cands):
        k = g.replace('/', '\\')
        if k.lower() in served or k.lower().endswith(('.mdx', '.mdl', '.blp', '.tga', '.mp3', '.wav', '.dds')):
            continue
        try:
            d = a.read(g)
        except Exception:
            d = None
        if d is None or len(d) > ORIGINAL_CAP:
            continue
        out[c] = (hashlib.sha1(d).hexdigest(), hashlib.md5(d).hexdigest())
    return out


def _cited_folders(paths, templates):
    import ntpath
    roots = set([''])
    for m in templates:
        for end_pos in ('?\\init.lua', '?.lua'):
            if m.endswith(end_pos):
                roots.add(m[:-len(end_pos)])
    out = set()
    for c in paths:
        for part in c.split(';'):
            part = part.strip().replace('/', '\\')
            if not part.endswith('\\') or ':' in part.replace('$MapPath$', ''):
                continue
            for r in (roots if '$' in part else ('',)):
                p = re.sub(r'\$[^$]*\$', lambda _m: r, part)
                p = ntpath.normpath(p) if p.strip('\\') else ''
                if p.startswith('..') or p == '.':
                    continue
                out.add(p.rstrip('\\') + '\\' if p else '')
    return sorted(out)


def _storm_data(a, cited, block_list, paths=(), templates=ENGINE_TEMPLATES):
    out = {}
    seen = set()
    total = [0]

    def take_batch(cands, matches=None):
        new_ones = []
        if matches is None:
            matches = existing_ones(a, [c if isinstance(c, tuple) else c.replace('/', '\\') for c in cands])
        for c, g in matches:
            if g.lower() in seen or g.lower().startswith('war3map'):
                continue
            seen.add(g.lower())
            try:
                r = a.find(g)
                d = a.read(g) if r is not None and r[1] not in block_list else None
            except Exception:
                d = None
            if d and len(d) <= DATA_CAP and total[0] + len(d) <= 4 * DATA_CAP:
                out[g] = d
                total[0] += len(d)
                new_ones.append((c, g))
        return new_ones
    take_batch([c for c in sorted(cited) if c.lower().endswith(DATA_EXTS)])
    roots = set([''])
    for m in templates:
        for end_pos in ('?\\init.lua', '?.lua'):
            if m.endswith(end_pos):
                roots.add(m[:-len(end_pos)])
    with_folder = sorted(set(c.replace('/', '\\').lstrip('\\') for c in paths
                             if not c.rstrip(';').endswith(('\\', '/')) and '$' not in c and ':' not in c))
    subfolders = []
    if with_folder:
        for _c, g in take_batch([r + c for c in with_folder for r in sorted(roots)]):
            if g.lower().endswith('.iniconfig') and g in out:
                p = g[:g.rfind('\\') + 1]
                for ln in out[g].decode('utf-8', 'surrogateescape').splitlines():
                    ln = ln.strip().replace('/', '\\').strip('\\')
                    if ln:
                        subfolders.append(p + ln + '\\')
    folders = _cited_folders([c for c in paths if '$' in c], templates)
    name_list = set(c for c in cited if len(c) <= 24 and '.' not in c) | set([''])
    work_queue = list(folders) + subfolders
    visited = set()
    while work_queue and len(visited) < 400:
        batch = sorted(set(work_queue) - visited)
        work_queue = []
        visited.update(batch)
        matches = take_batch(None, existing_product(a, batch, sorted(name_list), ['.ini', '.config']))
        while matches:
            new_ones = []
            for c, g in matches:
                if not g.lower().endswith('.config'):
                    continue
                p = c[:c.rfind('\\') + 1]
                for ln in out[g].decode('utf-8', 'surrogateescape').splitlines():
                    ln = ln.strip().replace('/', '\\').strip('\\')
                    if not ln:
                        continue
                    sub = ln.rsplit('\\', 1)
                    name_list.add(sub[-1])
                    if len(sub) == 2:
                        work_queue.append(p + sub[0] + '\\')
                    new_ones += [(p, ln, ext) for ext in ('.ini', '.config')]
            matches = take_batch(new_ones)
    return out
