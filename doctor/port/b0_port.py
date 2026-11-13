# The B0 loader of the port: the encrypted Lua modules listed, the plain text found by hash, the loader turned off (nothing decrypted).
import hashlib
import os
import re
import shutil
import struct


MANIFEST = 'bian\\manifest.txt'
SIGNATURE = 'bian\\manifest.sig'
PURPOSE = 'bian-release-manifest-v5'
FORMAT = '5'
B0_OID = 'pub.b0'
PE_MARKS = (b'b0_call', PURPOSE.encode('ascii'))
BENC = b'BENC'
BENC_VERSION = 1
FIELDS = {
    'G': ('group', 'version', 'kind', 'rule', 'needs'),
    'U': ('oid', 'path', 'role', 'length', 'sha256'),
    'L': ('oid', 'path', 'module', 'group', 'version', 'codec', 'plain_len', 'plain_hash', 'cipher_len', 'cipher_hash'),
    'X': ('oid', 'filename', 'profile', 'total_len', 'sha256', 'shell_len', 'shell_sha256'),
}
FIELDS['R'] = FIELDS['D'] = FIELDS['L']
INTS = ('length', 'plain_len', 'cipher_len', 'total_len', 'shell_len', 'version')
NATIVE = ('ffi', 'yasio')
BOOT_STUB = (b'-- Devo\'s Map Doctor (port): the B0 loader is off in this port; the plain require stays.\n'
             b'local M = { state = "plain", protected = false }\n'
             b'package.loaded[...] = M\n'
             b'function M.run() return true end\n'
             b'function M.show_fail() end\n'
             b'function M.fail_pack() end\n'
             b'return M\n')
RX_READ_BODY = re.compile(r'local\s+body\s*=\s*read\s*\(\s*M\.MANIFEST\s*\)')
RX_PLAIN = re.compile(r'if\s+not\s+body\s+then\s+M\.state\s*=\s*"plain"\s*;?\s*return\s+true\s+end')
RX_EMPTY_NIL = re.compile(r'#s\s*>\s*0\s+then\s+return\s+s\s+end\s+return\s+nil')
RX_REQUIRE = re.compile(r'''\brequire\s*\(?\s*(["'])([^"'\n]{1,200})\1''')
RX_PCALL_REQUIRE = re.compile(r'''\bpcall\s*\(\s*require\s*,\s*(["'])([^"'\n]{1,200})\1''')
RX_EXEC_LUA = re.compile(rb'exec-lua:\\?"?([A-Za-z0-9_.\\/]{1,120})')
SKIP_DIRS = frozenset(('.git', '__pycache__', 'node_modules'))
MAP_EXTS = ('.w3x', '.w3m')


def _int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def parse_manifest(text):
    m = {'header': {}}
    for k in FIELDS:
        m[k] = []
    for line in text.split('\n'):
        line = line.rstrip('\r')
        if not line:
            continue
        hm = re.match(r'^([a-z_]+)=(.*)$', line)
        if hm:
            m['header'][hm.group(1)] = hm.group(2)
            continue
        f = line.split('\t')
        names = FIELDS.get(f[0])
        if not names:
            continue
        row = dict(zip(names, f[1:]))
        for k in INTS:
            if k in row:
                row[k] = _int(row[k])
        m[f[0]].append(row)
    return m


def _archive(path):
    from doctor.mpq import mpqread
    return mpqread.Archive(path)


def _read(a, name):
    try:
        if a.find(name) is None:
            return None
        return a.read(name)
    except Exception:
        return None


def _manifest(a):
    body = _read(a, MANIFEST)
    if not body:
        return None
    try:
        return parse_manifest(body.decode('utf-8', 'surrogateescape'))
    except Exception:
        return None


def _is_text(b):
    return b is not None and b'\x00' not in b[:4096]


def boot_falls_back(text):
    if not RX_READ_BODY.search(text):
        return False, 'the boot does not read the manifest through read(M.MANIFEST)'
    if not RX_PLAIN.search(text):
        return False, 'the boot has no "if not body then M.state = \\"plain\\"; return true" path'
    if not RX_EMPTY_NIL.search(text):
        return False, 'the boot reads an empty file as an empty string, not nil'
    return True, 'an empty manifest reads as nil and run() takes the plain path (state = "plain", returns true)'


def detect(path):
    out = {'present': False, 'manifest': None, 'modules': [], 'boot_info': None, 'b0_block': None, 'b0_pe': False,
           'fallback': None, 'reason': None}
    try:
        a = _archive(path)
    except Exception as e:
        out['reason'] = 'the archive does not read: %s' % e
        return out
    m = _manifest(a)
    if m is None:
        out['reason'] = 'no %s' % MANIFEST
        return out
    h = m['header']
    b0 = next((u for u in m['U'] if u.get('oid') == B0_OID), None)
    out['manifest'] = {'header': {k: h.get(k) for k in ('format', 'purpose', 'product_id', 'build', 'entries')},
                       'counts': {k: len(m[k]) for k in FIELDS}}
    out['modules'] = [x['module'] for x in m['L']]
    if b0:
        e = a.find(b0['path'])
        out['b0_block'] = e[1] if e else None
        data = _read(a, b0['path'])
        out['b0_pe'] = bool(data and data[:2] == b'MZ' and all(k in data for k in PE_MARKS))
    out['present'] = bool(h.get('format') == FORMAT and h.get('purpose') == PURPOSE and b0 and
                          (out['b0_pe'] or out['b0_block'] is not None))
    if not out['present']:
        out['reason'] = 'the manifest is not a B0 release manifest (format %s, %s)' % (
            h.get('format'),
            h.get('purpose'),
        )
        return out
    for u in m['U']:
        if not str(u.get('path', '')).lower().endswith('.lua'):
            continue
        t = _read(a, u['path'])
        if _is_text(t) and b'M.MANIFEST' in t and b'manifest.txt' in t:
            out['boot_info'] = u['path']
            out['fallback'] = boot_falls_back(t.decode('utf-8', 'surrogateescape'))
            break
    return out


def inventory(path):
    a = _archive(path)
    m = _manifest(a) or {'L': []}
    out = []
    for x in m['L']:
        data = _read(a, x['path'])
        row = dict((k, x.get(k)) for k in ('oid', 'path', 'module', 'group', 'plain_len', 'plain_hash', 'cipher_len',
                                            'cipher_hash'))
        row['existe_no_mpq'] = data is not None
        row['size'] = len(data) if data is not None else None
        row['benc_ok'] = bool(data is not None and len(data) >= 8 and data[:4] == BENC and
                              struct.unpack_from('<I', data, 4)[0] == BENC_VERSION and len(data) == x.get('cipher_len'))
        row['cipher_hash_ok'] = bool(data is not None and hashlib.sha256(data).hexdigest() == x.get('cipher_hash'))
        out.append(row)
    return out


def default_roots(path):
    out = [os.path.dirname(os.path.abspath(path))]
    seen, uniq = set(), []
    for p in out:
        k = os.path.normcase(os.path.abspath(p))
        if os.path.isdir(p) and k not in seen:
            seen.add(k)
            uniq.append(p)
    return uniq


def _linked(path):
    try:
        return os.path.islink(path) or (hasattr(os.path, 'isjunction') and os.path.isjunction(path))
    except OSError:
        return True


def _first_visit(seen, path):
    try:
        k = os.path.normcase(os.path.realpath(path))
    except OSError:
        return False
    if k in seen:
        return False
    seen.add(k)
    return True


def _sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def module_path(module):
    return module.replace('.', '\\') + '.lua'


def plaintext_index(path, roots=None, inv=None, maps=None, progress=None):
    p = progress or (lambda *_x: None)
    inv = inventory(path) if inv is None else inv
    by_hash = dict((x['plain_hash'], x) for x in inv if x.get('plain_hash'))
    sizes = set(x['plain_len'] for x in inv if x.get('plain_len'))
    names = {}
    for x in inv:
        for n in (x['oid'], x['module'], x['module'] + '.lua', module_path(x['module']).split('\\')[-1]):
            names.setdefault(n.lower(), []).append(x)
    suffix = dict((x['oid'], os.path.normcase(module_path(x['module']).replace('\\', os.sep))) for x in inv)
    found, mismatch = {}, {}
    det = {'scanned': 0, 'maps': 0, 'mismatch': mismatch, 'roots': []}
    roots = default_roots(path) if roots is None else roots
    seen_dirs = set()
    skip = SKIP_DIRS
    for root in roots:
        det['roots'].append(root)
        p('Looking for the plaintext in %s' % root)
        for dirpath, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in skip and not _linked(os.path.join(dirpath, d))
                       and _first_visit(seen_dirs, os.path.join(dirpath, d))]
            for fn in files:
                full = os.path.join(dirpath, fn)
                low = fn.lower()
                if low.endswith(MAP_EXTS):
                    continue
                try:
                    size = os.path.getsize(full)
                except OSError:
                    continue
                by_name = names.get(low) or []
                if by_name:
                    nf = os.path.normcase(full)
                    by_name = [y for y in by_name if low in (y['oid'].lower(), y['module'].lower(),
                                                             y['module'].lower() + '.lua')
                               or nf.endswith(os.sep + suffix[y['oid']])]
                if size not in sizes and not by_name:
                    continue
                det['scanned'] += 1
                try:
                    h = _sha(full)
                except OSError:
                    continue
                x = by_hash.get(h)
                if x and x['plain_len'] == size and x['oid'] not in found:
                    found[x['oid']] = full
                for y in by_name:
                    if y['oid'] not in found and h != y['plain_hash']:
                        mismatch.setdefault(y['oid'], []).append(full)
    for mp in list(maps or ()):
        try:
            a = _archive(mp)
        except Exception:
            continue
        det['maps'] += 1
        for x in inv:
            if x['oid'] in found:
                continue
            data = _read(a, module_path(x['module']))
            if data is None:
                continue
            if len(data) == x['plain_len'] and hashlib.sha256(data).hexdigest() == x['plain_hash']:
                found[x['oid']] = '%s|%s' % (mp, module_path(x['module']))
            else:
                mismatch.setdefault(x['oid'], []).append('%s|%s' % (mp, module_path(x['module'])))
    return found, det


def read_plaintext(where):
    if '|' in where:
        mp, name = where.split('|', 1)
        return _read(_archive(mp), name)
    with open(where, 'rb') as f:
        return f.read()


def _requires(text):
    out = []
    for rx in (RX_REQUIRE, RX_PCALL_REQUIRE):
        out += [m.group(2) for m in rx.finditer(text)]
    return list(dict.fromkeys(out))


def require_graph(path, inv=None, plaintexts=None):
    a = _archive(path)
    m = _manifest(a) or {'U': [], 'L': []}
    inv = inventory(path) if inv is None else inv
    by_module = dict((x['module'], x) for x in inv)
    public = {}
    for u in m['U']:
        if u.get('role') in ('public_lua', 'callback') or str(u.get('path', '')).lower().endswith('.lua'):
            t = _read(a, u['path'])
            if _is_text(t):
                public[u['path']] = t.decode('utf-8', 'surrogateescape')
    public_modules = set(os.path.splitext(k)[0].replace('\\', '.') for k in public)
    entries = []
    for name in ('war3map.j', 'war3map.bin', 'scripts\\war3map.j'):
        b = _read(a, name)
        if b:
            entries += [e.decode('latin-1').replace('/', '.').replace('\\', '.') for e in RX_EXEC_LUA.findall(b)]
    entries = list(dict.fromkeys(entries))
    edges, required, outside = {}, set(), []
    queue = list(public.items())
    done = set()
    while queue:
        who, text = queue.pop(0)
        if who in done:
            continue
        done.add(who)
        reqs = _requires(text)
        edges[who] = reqs
        for r in reqs:
            if r in NATIVE or r.startswith('jass.') or r in public_modules:
                continue
            x = by_module.get(r)
            if x is None:
                if r not in outside:
                    outside.append(r)
                continue
            if x['oid'] in required:
                continue
            required.add(x['oid'])
            where = (plaintexts or {}).get(x['oid'])
            if where:
                try:
                    b = read_plaintext(where)
                except OSError:
                    b = None
                if _is_text(b):
                    queue.append((x['module'], b.decode('utf-8', 'surrogateescape')))
    return {'entries': entries, 'required': required, 'edges': edges, 'outside': outside,
            'public': sorted(public)}


def _empty_blocks(path, names):
    from doctor.mpq import mpqlib as M
    from doctor.mpq import mpqread as R
    a = R.Archive(path)
    d = bytearray(open(path, 'rb').read())
    bt = list(a.bt)
    done = []
    for name in names:
        e = a.find(name)
        if e is None:
            continue
        bi = e[1]
        bt[bi * 4 + 1] = 0
        bt[bi * 4 + 2] = 0
        bt[bi * 4 + 3] = R.FLAG_EXISTS
        done.append(name)
    if not done:
        return done
    enc = M.encrypt(bt, M.BLOCK_TABLE_KEY)
    bp = (a.h.offset + a.h.block_pos) & 0xFFFFFFFF
    d[bp:bp + len(enc)] = enc
    with open(path, 'wb') as f:
        f.write(bytes(d))
    b2 = R.Archive(path)
    for name in done:
        if b2.read(name):
            raise ValueError('%s did not come out empty' % name)
    return done


def prepare(path, out, progress=None, plaintexts=None):
    p = progress or (lambda *_x: None)
    if os.path.normcase(os.path.abspath(path)) == os.path.normcase(os.path.abspath(out)):
        raise ValueError('the output is the map itself')
    det = detect(path)
    res = {'state': 'nothing_to_do', 'emptied': [], 'stub': False, 'fallback': det.get('fallback'), 'inserted': [],
           'output': None, 'detect': det}
    if not det['present']:
        return res
    from doctor.mpq import mpqadd
    if mpqadd.format(path) != 0:
        raise ValueError('the archive is not a plain MPQ v1 (%s): unprotect it first' % mpqadd.format(path, True)[1])
    p('Removing the B0 loader')
    shutil.copyfile(path, out)
    try:
        res['emptied'] = _empty_blocks(out, (MANIFEST, SIGNATURE))
        repl = []
        if det['boot_info'] and not (det['fallback'] or (False,))[0]:
            repl.append((det['boot_info'], BOOT_STUB))
            res['stub'] = True
        if plaintexts:
            inv = dict((x['oid'], x) for x in inventory(path))
            for oid, where in sorted(plaintexts.items()):
                x = inv.get(oid)
                b = read_plaintext(where) if x else None
                if b is None or len(b) != x['plain_len'] or hashlib.sha256(b).hexdigest() != x['plain_hash']:
                    continue
                repl.append((module_path(x['module']), b))
                res['inserted'].append({'oid': oid, 'module': x['module'], 'path': module_path(x['module']),
                                        'source': where})
        if repl:
            p('Writing the plain modules')
            mpqadd.add_files(out, repl, log=lambda *_x: None)
        a = _archive(out)
        if _read(a, MANIFEST):
            raise ValueError('the manifest is still there')
        for name, data in repl:
            if _read(a, name) != data:
                raise ValueError('%s did not read back' % name)
    except BaseException:
        try:
            os.remove(out)
        except OSError:
            pass
        raise
    res.update(state='done', output=out)
    return res


def report(det, inv=None, index=None, graph=None, prep=None, details=None):
    out = {'counts': {}, 'modules': [], 'lines': []}
    if not det or not det.get('present'):
        out['lines'].append('B0 loader: not in this map, nothing to do.')
        return out
    inv = inv or []
    index = index or {}
    req = (graph or {}).get('required') or set()
    rows = []
    for x in inv:
        st = 'plaintext' if x['oid'] in index else ('blocked' if x['oid'] in req else 'not_referenced')
        rows.append(dict(x, status=st, source=index.get(x['oid'])))
    c = det['manifest']['counts']
    n = {'L': len(inv), 'required': len(req), 'plaintext': sum(1 for r in rows if r['status'] == 'plaintext'),
         'blocked': sum(1 for r in rows if r['status'] == 'blocked'),
         'not_referenced': sum(1 for r in rows if r['status'] == 'not_referenced'),
         'benc_ok': sum(1 for r in rows if r['benc_ok']), 'in_mpq': sum(1 for r in rows if r['existe_no_mpq']),
         'R': c.get('R', 0), 'D': c.get('D', 0), 'X': c.get('X', 0), 'U': c.get('U', 0)}
    out['counts'], out['modules'] = n, rows
    L = out['lines']
    h = det['manifest']['header']
    L.append('B0 loader: %s %s (manifest format %s, %s).' % (h.get('product_id') or '?', h.get('build') or '',
                                                             h.get('format'), h.get('purpose')))
    if prep:
        if prep.get('state') == 'done':
            how = (
                'the boot %s was replaced by a minimal one that installs no require' % det.get('boot_info')
                if prep.get('stub')
                else 'the boot %s takes its plain path: %s'
                % (det.get('boot_info'), (prep.get('fallback') or ('', ''))[1])
            )
            L.append('  The loader is off: %s emptied; %s. Nothing was re-signed, patched or decrypted.'
                     % (' and '.join(prep.get('emptied') or []), how))
        for i in prep.get('inserted') or []:
            L.append('  Plain module written: %s at %s (from %s).' % (i['module'], i['path'], i['source']))
    L.append('  Lua modules (L): %d, %d in the archive, %d with a valid BENC container of the listed size.'
             % (n['L'], n['in_mpq'], n['benc_ok']))
    L.append('  Required by the readable code: %d; plaintext found: %d; blocked: %d; not referenced: %d.'
             % (n['required'], n['plaintext'], n['blocked'], n['not_referenced']))
    if n['blocked'] or n['not_referenced']:
        L.append('  Blocked = plaintext not found: the module is only AES-GCM ciphertext and the key comes from the '
                 'author\'s server, so the port runs without it. Not referenced = no readable code requires it (the '
                 'encrypted modules may).')
    if details:
        L.append(
            '  Searched %d candidate file(s) and %d map(s) in: %s.'
            % (details.get('scanned', 0), details.get('maps', 0), '; '.join(details.get('roots') or []) or '-')
        )
        if details.get('mismatch'):
            L.append('  %d module(s) have a file with the right name but other content (not used).'
                     % len(details['mismatch']))
    if n['R'] or n['D'] or n['X']:
        L.append('  Also encrypted and left as they are: %d resource(s) (R), %d native DLL(s) (D), %d outside pack(s) '
                 '(X): what they hold is missing from the port.' % (n['R'], n['D'], n['X']))
    for r in rows:
        if r['status'] == 'blocked':
            L.append('    blocked  %s  %s  group %s  plain %s B %s  cipher %s B: plaintext not found'
                     % (r['oid'], r['module'], r['group'], r['plain_len'], r['plain_hash'], r['cipher_len']))
    for r in rows:
        if r['status'] == 'plaintext':
            L.append('    found    %s  %s  <- %s' % (r['oid'], r['module'], r['source']))
    nr = [r['module'] for r in rows if r['status'] == 'not_referenced']
    if nr:
        L.append('    not referenced (%d): %s%s' % (len(nr), ', '.join(nr[:40]), ', ...' if len(nr) > 40 else ''))
    return out


def run(path, out=None, roots=None, progress=None, maps=None):
    det = detect(path)
    if not det['present']:
        return {'detect': det, 'report': report(det)}
    inv = inventory(path)
    index, details = plaintext_index(path, roots, inv, maps, progress)
    graph = require_graph(path, inv, index)
    prep = prepare(path, out, progress, index) if out else None
    return {'detect': det, 'inventory': inv, 'index': index, 'details': details, 'graph': graph, 'prepare': prep,
            'report': report(det, inv, index, graph, prep, details)}
