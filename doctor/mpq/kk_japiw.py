# The KK platform's JAPIW appendix (map files after the MPQ, plain names and raw deflate): read and written into the map.
import mmap
import os
import struct
import zlib

from doctor.mpq import mpqread
from doctor.mpq import mpq_rebuild


MPQ_MAGIC = b'MPQ\x1a'
TAG_SIZE = 12
SCAN_LIMIT = 0x10000
NAME_MAX = 0x104
SKIPPED_NAME = 'Release'
JAPIW_RECORD_CAP = 512 << 20


class JapiwError(Exception):
    pass


def _tag_at(d, pos):
    return 0x200 <= pos and pos + TAG_SIZE <= len(d) and bytes(d[pos:pos + 4]) == b'JAPI' and d[pos + 4] == ord('W')


def finds(d):
    n = min(len(d), SCAN_LIMIT)
    for h in range(0, n - 0x1F, 0x200):
        if bytes(d[h:h + 4]) != MPQ_MAGIC or bytes(d[h + 4:h + 8]) in (b'CAME', b'PACK'):
            continue
        x = struct.unpack_from('<I', d, h + 8)[0]
        if h + x <= 0x1FF:
            continue
        for pos in (h + x, x):
            if _tag_at(d, pos):
                return {'mpq': h, 'tag': pos, 'first_pos': pos + TAG_SIZE}
    return None


def _open(file_path):
    f = open(file_path, 'rb')
    try:
        return f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
    except (OSError, ValueError):
        f.close()
        raise


def _name(b):
    return b.decode('utf-8', 'surrogateescape')


def record_count(d, first_pos):
    pos = first_pos
    end_pos = len(d)
    while pos + 9 <= end_pos:
        window = bytes(d[pos:pos + min(0x200, end_pos - pos)])
        z = window.find(b'\0')
        if z < 1 or z > NAME_MAX or any(c < 0x20 for c in window[:z]) or z + 9 > len(window):
            return
        usize, csize = struct.unpack_from('<II', window, z + 1)
        data_bytes = pos + z + 9
        if csize == 0 or data_bytes + csize > end_pos:
            return
        yield _name(window[:z]), usize, csize, data_bytes
        pos = data_bytes + csize


def read_data(d, reg):
    fname, usize, csize, pos = reg
    if usize == 0:
        return b''
    if usize > JAPIW_RECORD_CAP:
        raise JapiwError('record %r: %d bytes is more than any map file' % (fname, usize))
    z = zlib.decompressobj(-15)
    try:
        out = z.decompress(bytes(d[pos:pos + csize]), usize)
    except zlib.error as e:
        raise JapiwError('record %r does not inflate: %s' % (fname, e)) from e
    if not z.eof or len(out) != usize:
        raise JapiwError('record %r: inflate gave %d of %d bytes' % (fname, len(out), usize))
    return out


def _effective_records(regs):
    seen = {}
    for r in regs:
        if r[0] == SKIPPED_NAME:
            continue
        seen[mpq_rebuild._norm(r[0]).lower()] = r
    return list(seen.values())


def info(d=None, file_path=None):
    f = None
    if d is None:
        f, d = _open(file_path)
    try:
        a = finds(d)
        if a is None:
            return None
        regs = list(record_count(d, a['first_pos']))
        ef = _effective_records(regs)
        return {'mpq': a['mpq'], 'tag': a['tag'], 'tag_hex': bytes(d[a['tag']:a['tag'] + TAG_SIZE]).hex(),
                'record_count': len(regs), 'effective': len(ef), 'bytes': sum(r[2] for r in regs),
                'plaintext': sum(r[1] for r in regs), 'skipped_release': any(r[0] == SKIPPED_NAME for r in regs),
                'name_list': [r[0] for r in ef[:20]]}
    finally:
        if f is not None:
            d.close()
            f.close()


def _safe_path(folder, fname):
    pieces = [p for p in mpq_rebuild._norm(fname).split('\\') if p not in ('', '.', '..')]
    tgt = os.path.normpath(os.path.join(folder, *pieces)) if pieces else None
    if not tgt or not os.path.abspath(tgt).startswith(os.path.abspath(folder) + os.sep):
        raise JapiwError('unsafe record name %r' % fname)
    return tgt


def extract(file_path, folder):
    f, d = _open(file_path)
    try:
        a = finds(d)
        if a is None:
            raise JapiwError('not a JAPIW map')
        regs = list(record_count(d, a['first_pos']))
        out = []
        for r in _effective_records(regs):
            data_bytes = read_data(d, r)
            tgt = _safe_path(folder, r[0])
            os.makedirs(os.path.dirname(tgt), exist_ok=True)
            with open(tgt, 'wb') as fh:
                fh.write(data_bytes)
            out.append((r[0], len(data_bytes)))
        return {'record_count': len(regs), 'file_set': out, 'bytes': sum(n for _x, n in out)}
    finally:
        d.close()
        f.close()


def to_map(file_path, output, log=None):
    log = log or (lambda *_a: None)
    f, d = _open(file_path)
    try:
        a = finds(d)
        if a is None:
            raise JapiwError('not a JAPIW map')
        regs = _effective_records(list(record_count(d, a['first_pos'])))
        if not regs:
            raise JapiwError('No JAPIW records were found in this map.')
        japiw = {r[0]: read_data(d, r) for r in regs}
    finally:
        d.close()
        f.close()
    file_ = mpqread.Archive(file_path)
    lf = file_.read('(listfile)') or b''
    externos = [n for n in lf.decode('utf-8', 'surrogateescape').replace('\r', '\n').split('\n') if n]
    exists = {mpq_rebuild._norm(n).lower() for n in externos if file_.read(n) is not None}
    replacements = {n: b for n, b in japiw.items() if mpq_rebuild._norm(n).lower() in exists}
    new_ones = {n: b for n, b in japiw.items() if n not in replacements}
    name_list = [n for n in externos if n not in ('(listfile)', '(attributes)', '(signature)')]
    mpq_rebuild.rebuild(
        file_path,
        output,
        name_list,
        replacements=replacements,
        new_ones=new_ones,
        to_remove=('(attributes)',),
        listfile=True,
        log=log,
    )
    return {'japiw': len(japiw), 'replaced': len(replacements), 'new_ones': len(new_ones), 'output': output}

