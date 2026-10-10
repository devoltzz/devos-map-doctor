# Gives back the name of the models the "Model_Encrypt" tool renamed, and rewrites the citations.
import hashlib
import os
import re
import shutil

from doctor.fix import unprotect
from doctor.mpq import mpqnames


MARK = '\u4f53'
MARK_BYTES = (MARK.encode('utf-8'), MARK.encode('gbk'))
MODEL_EXTS = ('.mdl', '.mdx')
CITED_EXTS = ('.j', '.lua', '.ini', '.slk', '.txt', '.fdf', '.imp', '.wtg', '.w3u', '.w3t', '.w3b', '.w3d', '.w3a',
              '.w3h', '.w3q')
LISTFILE = '(listfile)'
RX_MARK_B = re.compile(rb'^(?P<base>.+?)(?P<mark>' + b'|'.join(MARK_BYTES) +
                       rb')(?P<portrait>_portrait)?\.(?P<ext>mdl|mdx)$', re.I)
_RX_CHARS = rb'A-Za-z0-9_\-\\/\. \[\]\(\)\+!#\$%&@\^~{}=\x80-\xff'
RX_CITED_B = re.compile(rb'[' + _RX_CHARS + rb']{3,180}?(?:' + b'|'.join(MARK_BYTES) + rb')(?:_portrait)?\.(?:mdl|mdx)',
                        re.I)
RX_CITED_ANY_B = re.compile(rb'[' + _RX_CHARS + rb'|]{3,180}?\.(?:mdl|mdx)', re.I)
RX_MODEL_B = re.compile(rb'^(?P<stem>.*?)(?P<portrait>_portrait)?\.(?P<ext>mdl|mdx)$', re.I)
_RX_EXT_B = re.compile(rb'\.md[lx]', re.I)
_CITED_BEFORE = 180
_CITED_TAIL = max(len(m) for m in MARK_BYTES) + len(b'_portrait') + len(b'.mdx')


def _windows(anchors, before, after, size):
    out = []
    for p in anchors:
        a, b = max(0, p - before), min(size, p + after)
        if out and a <= out[-1][1]:
            if b > out[-1][1]:
                out[-1][1] = b
        else:
            out.append([a, b])
    return out


def _mark_positions(data):
    out = []
    for mk in MARK_BYTES:
        i = data.find(mk)
        while i >= 0:
            out.append(i)
            i = data.find(mk, i + 1)
    return sorted(out)


def _finditer_cited(data):
    for a, b in _windows(_mark_positions(data), _CITED_BEFORE, _CITED_TAIL, len(data)):
        yield from RX_CITED_B.finditer(data, a, b)


def _finditer_cited_any(data):
    pos = [m.start() for m in _RX_EXT_B.finditer(data)]
    for a, b in _windows(pos, _CITED_BEFORE, 4, len(data)):
        yield from RX_CITED_ANY_B.finditer(data, a, b)


def _split_bytes(name):
    b = name.encode('utf-8', 'surrogateescape')
    i = max(b.rfind(b'\\'), b.rfind(b'/'))
    return b[:i + 1], b[i + 1:]


def _parts(name):
    folder, base = _split_bytes(name)
    m = RX_MARK_B.match(base)
    if m is None:
        return None
    return (folder.decode('utf-8', 'surrogateescape'), m.group('base').decode('utf-8', 'surrogateescape'),
            (m.group('portrait') or b'').decode('ascii'), m.group('ext').decode('ascii'))


def marked(name):
    return _parts(name) is not None


def not_utf8(name):
    try:
        name.encode('utf-8', 'surrogateescape').decode('utf-8')
    except UnicodeDecodeError:
        return True
    return False


def _other_ext(name):
    low = name[-4:].lower()
    return name[:-4] + {'.mdl': '.mdx', '.mdx': '.mdl'}[low] if low in MODEL_EXTS else None


def ascii_name(name):
    folder, base = _split_bytes(name)
    m = RX_MODEL_B.match(base)
    if m is None:
        return None
    try:
        folder_s = folder.decode('utf-8')
    except UnicodeDecodeError:
        folder_s = ''
    h = hashlib.md5((folder + m.group('stem')).lower()).hexdigest()[:12]
    return '%sobf_%s%s.%s' % (folder_s, h, (m.group('portrait') or b'').decode('ascii'), m.group('ext').decode('ascii'))


def clean_name(name):
    part = _parts(name)
    if part is None:
        return ascii_name(name) if not_utf8(name) else None
    return '%s%s%s.%s' % part


def _readings(raw):
    s = raw.decode('utf-8', 'surrogateescape').strip('"\' \t\r\n\x00')
    out = [s]
    if '=' in s:
        out.append(s.rsplit('=', 1)[-1].strip())
    if ' ' in s:
        pal = s.split(' ')
        i = next((k for k, p in enumerate(pal) if '\\' in p), None)
        if i:
            out.append(' '.join(pal[i:]))
        out.append(pal[-1])
    out += [x.replace('\\\\', '\\') for x in out if '\\\\' in x]
    return [x for x in dict.fromkeys(out) if x]


def _is_model(name, data):
    if not data:
        return False
    if name.lower().endswith('.mdx'):
        return data[:4] == b'MDLX'
    head = data[:4096]
    return b'\0' not in head and b'Version' in head


def _citation_files(a, names=()):
    out, seen = [], set()
    candidates = list(names) + unprotect.listfile_names(a) + list(mpqnames.BASE_NAMES) + list(mpqnames.GAME_NAMES)
    for n in candidates + [LISTFILE]:
        k = n.lower()
        if k in seen:
            continue
        seen.add(k)
        if k != LISTFILE and os.path.splitext(n)[1].lower() not in CITED_EXTS:
            continue
        data = unprotect._read(a, n)
        if data:
            out.append((n, data))
    return out


def _marked_names(a, names=()):
    out = []
    for n in names:
        if marked(n) and a.find(n):
            out.append(n)
    for _n, data in _citation_files(a, names):
        for m in _finditer_cited(data):
            for cand in _readings(m.group(0)):
                if marked(cand) and a.find(cand):
                    out.append(cand)
        for m in _finditer_cited_any(data):
            if not any(b >= 0x80 for b in m.group(0)):
                continue
            for cand in _readings(m.group(0)):
                if not not_utf8(cand):
                    continue
                for c in (cand, _other_ext(cand)):
                    if c and a.find(c):
                        out.append(c)
                        break
    return list(dict.fromkeys(out))


def _scan_in(a, names=()):
    out = {'renamed': [], 'collisions': [], 'checked': 0}
    seen = set()
    for n in _marked_names(a, names):
        r = a.find(n)
        if not r or r[1] in seen:
            continue
        seen.add(r[1])
        data = unprotect._read(a, n)
        if not _is_model(n, data):
            continue
        out['checked'] += 1
        c = clean_name(n)
        if a.find(c):
            out['collisions'].append((n, c))
            continue
        out['renamed'].append((n, c))
    return out


def scan(path, progress=None):
    p = progress or (lambda *_a: None)
    out = {'renamed': [], 'collisions': [], 'checked': 0, 'error': None}
    p('Reading the map')
    try:
        a = unprotect._open(path)
    except BaseException as e:
        out['error'] = unprotect._error(e)
        return out
    p('Looking for the encrypted names')
    out.update(_scan_in(a))
    return out


def _pairs(a, base):
    pairs = list(base['renamed'])
    seen = set(pairs)
    n_port = 0
    for old, clean in list(pairs):
        part = _parts(old)
        if part is None and not_utf8(old):
            mo, mc = RX_MODEL_B.match(_split_bytes(old)[1]), RX_MODEL_B.match(_split_bytes(clean)[1])
            if mo and mc and not mo.group('portrait'):
                fo = _split_bytes(old)[0].decode('utf-8', 'surrogateescape')
                fc = _split_bytes(clean)[0].decode('utf-8', 'surrogateescape')
                for ext in MODEL_EXTS:
                    po = '%s%s_portrait%s' % (fo, mo.group('stem').decode('utf-8', 'surrogateescape'), ext)
                    pn = '%s%s_portrait%s' % (fc, mc.group('stem').decode('ascii'), ext)
                    if (po, pn) in seen or not a.find(po) or a.find(pn):
                        continue
                    seen.add((po, pn))
                    pairs.append((po, pn))
                    n_port += 1
            continue
        if part is None or part[2]:
            continue
        folder, base_name, _port, _ext = part
        for ext in MODEL_EXTS:
            po = '%s%s%s_portrait%s' % (folder, base_name, MARK, ext)
            pn = '%s%s_portrait%s' % (folder, base_name, ext)
            if (po, pn) in seen or not a.find(po) or a.find(pn):
                continue
            seen.add((po, pn))
            pairs.append((po, pn))
            n_port += 1
    return pairs, n_port


def _cite(data, pairs):
    out = data
    variants = []
    for old, clean in pairs:
        variants.append((old, clean))
        if not_utf8(old) and _other_ext(old) and _other_ext(clean):
            variants.append((_other_ext(old), _other_ext(clean)))
    for o, c in sorted(variants, key=lambda p: -len(p[0].encode('utf-8', 'surrogateescape'))):
        for vo, vn in ((o, c), (o.replace('\\', '/'), c.replace('\\', '/')),
                       (o.replace('\\', '\\\\'), c.replace('\\', '\\\\'))):
            b_old = vo.encode('utf-8', 'surrogateescape')
            if b_old in out:
                out = out.replace(b_old, vn.encode('utf-8', 'surrogateescape'))
    return out


def fix(path_in, path_out, progress=None):
    p = progress or (lambda *_a: None)
    rep = {'renamed': [], 'files': [], 'portraits': 0, 'note': None, 'error': None}
    if os.path.normcase(os.path.abspath(path_in)) == os.path.normcase(os.path.abspath(path_out)):
        rep['error'] = 'the output must be a new file'
        return rep
    try:
        a = unprotect._open(path_in)
    except BaseException as e:
        rep['error'] = unprotect._error(e)
        return rep
    p('Looking for the encrypted names')
    base = _scan_in(a)
    pairs, rep['portraits'] = _pairs(a, base)
    if not pairs:
        rep['note'] = 'no model name carries the mark'
        shutil.copyfile(path_in, path_out)
        return rep
    p('Rewriting the names in the map files')
    repl, touched = [], []
    for n, data in _citation_files(a):
        new_data = _cite(data, pairs)
        if new_data != data:
            repl.append((n, new_data))
            touched.append(n)
    data = {}
    for old, clean in pairs:
        data[old] = unprotect._read(a, old)
        if data[old] is None:
            rep['error'] = 'the model %s does not read' % old
            return rep
        repl.append((clean, data[old]))
    p('Writing the map')
    part = unprotect._part(path_out)
    try:
        shutil.copyfile(path_in, part)
        from doctor.mpq import mpqadd
        with unprotect.quiet():
            mpqadd.add_files(part, repl, to_delete=[old for old, _c in pairs], log=lambda *_a: None)
    except (Exception, SystemExit) as e:
        _remove(part)
        rep['error'] = 'the map could not be written (%s)' % unprotect._error(e)
        return rep
    p('Checking the result')
    problems = []
    try:
        b = unprotect._open(part)
    except BaseException as e:
        problems.append('the output does not open (%s)' % unprotect._error(e))
        b = None
    if b is not None:
        for old, clean in pairs:
            if b.find(old):
                problems.append('the marked name %s is still there' % old)
            if unprotect._read(b, clean) != data[old]:
                problems.append('%s does not read the same bytes' % clean)
        for old, _c in pairs:
            for vo in (old, old.replace('\\', '/'), old.replace('\\', '\\\\')):
                b_old = vo.encode('utf-8', 'surrogateescape')
                for n in touched:
                    if b_old in (unprotect._read(b, n) or b''):
                        problems.append('%s is still cited in %s' % (old, n))
        with unprotect.quiet():
            c = unprotect.check_content(path_in, part, exclude=touched)
        if c['different'] or c['missing_items']:
            problems.append(
                'the check: %d file(s) different, %d missing' % (len(c['different']), len(c['missing_items']))
            )
    del b
    if problems:
        _remove(part)
        rep['error'] = '; '.join(problems[:4])
        return rep
    os.replace(part, path_out)
    rep['renamed'] = pairs
    rep['files'] = touched
    return rep


def _remove(path):
    try:
        if os.path.isfile(path):
            os.remove(path)
    except OSError:
        pass
