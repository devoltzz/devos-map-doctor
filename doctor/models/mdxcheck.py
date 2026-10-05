# Checks the structure of an MDX model: what makes the game read outside the file.
import struct
import sys


TAGS = {
    b'VERS', b'MODL', b'SEQS', b'GLBS', b'TEXS', b'MTLS', b'GEOS', b'GEOA', b'BONE', b'LITE',
    b'HELP', b'ATCH', b'PREM', b'PRE2', b'RIBB', b'EVTS', b'CAMS', b'CLID', b'BPOS', b'FAFX',
    b'PIVT',
    b'CORN', b'LAYS', b'TXAN', b'FAXS', b'HELP', b'SNBI', b'SNBS', b'SNBV',
}
MAGICS = {b'MDLX', b'EMAM'}


def arg(fname, default_value=None):
    for a in sys.argv[1:]:
        if a.startswith('--%s=' % fname):
            return a.split('=', 1)[1]
        if a == '--%s' % fname:
            return True
    return default_value


def walk(d):
    if d[:4] not in MAGICS:
        return [], 'unknown magic %r (neither MDLX nor one of the known family)' % d[:4]
    p = 4
    chunks = []
    n = len(d)
    while p < n:
        if p + 8 > n:
            return chunks, 'chunk header cut short at %d (%d B missing)' % (p, p + 8 - n)
        tag = d[p:p + 4]
        size = struct.unpack_from('<I', d, p + 4)[0]
        if p + 8 + size > n:
            return chunks, 'chunk %r at %d runs past the file: size=%d, left=%d' % (
                tag, p, size, n - p - 8)
        chunks.append((tag, size, p + 8))
        p += 8 + size
    if p != n:
        return chunks, 'the walk ended at %d of %d B' % (p, n)
    return chunks, None

