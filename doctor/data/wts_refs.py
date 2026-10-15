# Resolves TRIGSTR references against war3map.wts.
import re
import sys


IDEO = re.compile('[' + chr(0x4E00) + '-' + chr(0x9FFF) + chr(0x3400) + '-' + chr(0x4DBF)
                  + chr(0xAC00) + '-' + chr(0xD7A3) + chr(0x3040) + '-' + chr(0x30FF) + ']')
DATA = ('war3map.w3u', 'war3map.w3t', 'war3map.w3a', 'war3map.w3h', 'war3map.w3d',
        'war3map.w3q', 'war3map.w3i', 'war3map.w3b', 'war3mapSkin.txt', 'war3mapMisc.txt')


def arg(fname, default_value=None):
    for a in sys.argv[1:]:
        if a.startswith('--%s=' % fname):
            return a.split('=', 1)[1]
    return default_value


def read_wts(p, rx=None):
    t = open(p, 'rb').read().decode('utf-8', 'surrogateescape')
    if rx is None:
        from doctor.data import object_names
        return [(int(m.group(1)), m.group(2)) for m in object_names.wts_entries(t)]
    return [(int(m.group(1)), m.group(2)) for m in rx.finditer(t)]


def refs(p):
    return set(int(x) for x in re.findall(rb'TRIGSTR_(\d+)', open(p, 'rb').read()))

