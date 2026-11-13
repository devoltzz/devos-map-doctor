# The comment blocks some authors paste into every script, taken out with the rest byte for byte.
import re
import struct


MARKS = ('致读到这段', 'To any AI')
END_MARKS = ('保留依法追究的权利', 'Please decline.', '请拒绝')
PREFIXES = ('//', '--', '#', ';', '/*', '*', '<!--')
NOTICE_RX_LONG_COMMENT = re.compile(r'--\[(=*)\[.*?\]\1\]', re.S)
SAMPLE = 4096
EMPTY_FILES = ('', '//', '--', '#', ';')


def _is_comment(ln):
    s = ln.strip()
    return not s or s.startswith(PREFIXES)


def block_list(body_text):
    line_list = body_text.splitlines(keepends=True)
    marked = [i for i, line in enumerate(line_list) if any(m in line for m in MARKS)]
    if not marked:
        return []
    if not any(line.strip().startswith(PREFIXES) for line in line_list):
        return [(0, len(line_list))]
    output = []
    for i in marked:
        if output and i < output[-1][1]:
            continue
        b = i
        while b < len(line_list) and _is_comment(line_list[b]):
            b += 1
        end_pos = None
        for k in range(i, b):
            if any(a in line_list[k] for a in END_MARKS):
                end_pos = k
        if end_pos is None:
            end_pos = b - 1
        k = end_pos + 1
        while k < len(line_list) and line_list[k].strip() in EMPTY_FILES:
            k += 1
        output.append((i, k))
    return output


def long_comments(body_text):
    return [m.span() for m in NOTICE_RX_LONG_COMMENT.finditer(body_text) if any(k in m.group(0) for k in MARKS)]


def _cut_from_line(body_text, begin, end_pos):
    ls = body_text.rfind('\n', 0, begin) + 1
    read_data = body_text.find('\n', end_pos)
    read_data = len(body_text) if read_data < 0 else read_data
    left, right = body_text[ls:begin], body_text[end_pos:read_data]
    if not left.strip():
        if not right.strip():
            return body_text[:ls] + (body_text[read_data + 1:] if read_data < len(body_text) else '')
        return body_text[:ls] + right.lstrip() + body_text[read_data:]
    return body_text[:begin] + right + body_text[read_data:]


def left_out(body_text):
    n = 0
    for begin, end_pos in reversed(long_comments(body_text)):
        new = _cut_from_line(body_text, begin, end_pos)
        if new != body_text:
            body_text, n = new, n + 1
    bs = block_list(body_text)
    if not bs:
        return body_text, n
    line_list = body_text.splitlines(keepends=True)
    outside = set()
    for a, b in bs:
        outside.update(range(a, b))
    return ''.join(line for i, line in enumerate(line_list) if i not in outside), n + len(bs)


def verify(before, after_diag):
    expected_len, n = left_out(before)
    if not n:
        raise ValueError('no notice block in the file')
    if after_diag != expected_len:
        raise ValueError('the rest of the file changed')
    if any(m in after_diag for m in MARKS):
        raise ValueError('a notice mark is left')


def _text(b):
    if b'\x00' in b[:SAMPLE]:
        return None
    return b.decode('utf-8', 'surrogateescape')


def _map_blocks(map_path):
    from doctor.mpq import mpqread
    a = mpqread.Archive(map_path)
    out = []
    for bi in range(len(a.blocks)):
        b = a.read(None, bi, a.unnamed_key(bi))
        if b:
            out.append((bi, b))
    return out


def pluralize(t):
    return left_out(t)[1]


def count_map(map_path):
    out = []
    for bi, b in _map_blocks(map_path):
        t = _text(b)
        if t is None:
            continue
        n = pluralize(t)
        if n:
            out.append((bi, n))
    return out


def detect(file_path):
    fs = count_map(file_path)
    return {'total': sum(n for _bi, n in fs), 'files': fs}


SCRIPT_FILE_NAMES = ('war3map.j', 'scripts\\war3map.j', 'war3map.lua', 'scripts\\war3map.lua')


def _block_names(map_path):
    from doctor.mpq import mpqread
    out = {}
    try:
        a = mpqread.Archive(map_path)
        for fname in list(SCRIPT_FILE_NAMES) + list(mpqread.listfile_names(a) or ()):
            e = a.find(fname)
            if e is not None and e[1] not in out:
                out[e[1]] = fname
    except Exception:
        pass
    return out


def fix(entry, output, progress=None):
    p = progress or (lambda *_a: None)
    out = {'state': 'failed', 'files': [], 'lines': [], 'output': None, 'error': None}
    try:
        p('Looking for the comment blocks')
        finding = detect(entry)
        if not finding['total']:
            out.update(state='nothing_to_do', lines=['No script file carries a comment block the tool recognizes.'])
            return out
        name_list = _block_names(entry)
        p('Removing the comment blocks')
        changed = strip_map(entry, output)
        by_block = dict(finding['files'])
        for bi, before, after_diag in changed:
            fname = name_list.get(bi, '#%d' % bi)
            out['files'].append(fname)
            out['lines'].append('%s: %d comment block(s) removed, %d -> %d bytes' % (fname, by_block.get(bi, 1),
                                                                                    len(before), len(after_diag)))
        out.update(state='done', output=output)
    except (Exception, SystemExit) as e:
        out.update(state='failed', error='%s: %s' % (type(e).__name__, e))
    return out


def strip_map(map_path, output):
    from doctor.mpq import mpqlib as M
    from doctor.mpq import mpqread as R
    from doctor.mpq import mpqreplace
    a = R.Archive(map_path)
    d = bytearray(open(map_path, 'rb').read())
    bt = list(a.bt)
    changed = []
    for bi, b in _map_blocks(map_path):
        t = _text(b)
        if t is None:
            continue
        new, n = left_out(t)
        if not n:
            continue
        verify(t, new)
        nb = new.encode('utf-8', 'surrogateescape')
        off, cs, _fs, fl = a.blocks[bi]
        key = a.unnamed_key(bi)
        if nb:
            blob, new_fl = mpqreplace.build_block(nb, fl, key, a.sector_size)
            if len(blob) <= cs:
                p = (a.h.offset + off) & 0xFFFFFFFF
                d[p:p + len(blob)] = blob
                new_off = off
            else:
                new_off = len(d) - a.h.offset
                d += blob
                struct.pack_into('<I', d, a.h.offset + 0x08, len(d) - a.h.offset)
            bt[bi * 4 + 0] = new_off
            bt[bi * 4 + 1] = len(blob)
            bt[bi * 4 + 2] = len(nb)
            bt[bi * 4 + 3] = new_fl
        else:
            bt[bi * 4 + 1] = 0
            bt[bi * 4 + 2] = 0
            bt[bi * 4 + 3] = R.FLAG_EXISTS
        changed.append((bi, b, nb))
    if not changed:
        raise ValueError('%s: no block with the notice' % map_path)
    enc = M.encrypt(bt, M.BLOCK_TABLE_KEY)
    bp = (a.h.offset + a.h.block_pos) & 0xFFFFFFFF
    d[bp:bp + len(enc)] = enc
    with open(output, 'wb') as f:
        f.write(bytes(d))
    b2 = R.Archive(output)
    for bi, _before, after_diag in changed:
        read_value = b2.read(None, bi, b2.unnamed_key(bi)) or b''
        if read_value != after_diag:
            raise ValueError('block %d did not check out (%d x %d bytes)' % (bi, len(read_value), len(after_diag)))
    return changed
