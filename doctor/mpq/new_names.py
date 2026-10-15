# Finds the file names of a map that the shared name list lacks, and writes the issue that shares them.

from doctor.mpq import mpqlib
from doctor.mpq import mpqnames
from doctor.mpq import mpqread


SPECIAL_FILES = ('(listfile)', '(attributes)', '(signature)')
URL_CAP = 7000
IN_BODY = 150
_INDEX = [None, False]


def _index():
    if not _INDEX[1]:
        _INDEX[1] = True
        try:
            _INDEX[0] = mpqnames.load_big()
        except Exception:
            _INDEX[0] = None
    return _INDEX[0]


def new_to_list(map_path, name_list=None):
    idx = _index()
    out = {'index': idx is not None, 'names': [], 'count': 0, 'skipped': 0}
    if idx is None:
        return out
    a = mpqread.Archive(map_path) if isinstance(map_path, str) else map_path
    if name_list is None:
        from doctor.fix import unprotect
        name_list = unprotect.map_names(a)
    cand = []
    for n in name_list:
        if not isinstance(n, str) or not n.strip() or n.lower() in SPECIAL_FILES or a.find(n) is None:
            continue
        cand.append(n)
    if not cand:
        return out
    bs = [n.encode('utf-8', 'surrogateescape') for n in cand]
    pos = idx.lookup_batch(mpqlib.hashstr_batch(bs, 1), mpqlib.hashstr_batch(bs, 2))
    new_ones, seen = [], set()
    for n, p in zip(cand, pos):
        if int(p) >= 0:
            continue
        try:
            n.encode('utf-8')
        except UnicodeEncodeError:
            out['skipped'] += 1
            continue
        n = n.replace('/', '\\').lstrip('\\')
        k = n.upper()
        if k in seen:
            continue
        seen.add(k)
        new_ones.append(n)
    out['names'] = sorted(new_ones, key=str.lower)
    out['count'] = len(out['names'])
    return out


def body(name_list, version_num='', file_name=None):
    line_list = [
        'File names found in a map that the shared name list did not have. Devo\'s Map Doctor %s collected them '
        'when the map was opened; only the names of the files inside the map are listed (not the map\'s name, '
        'nor where it is).' % (version_num or '')
    ]
    if file_name:
        line_list += [
            '',
            'The list has %d names, too many for this page: the whole list is in the file `%s`, next to the '
            'map. Please drag that file into this issue; the first %d names follow.'
            % (len(name_list), file_name, min(IN_BODY, len(name_list))),
        ]
        name_list = name_list[:IN_BODY]
    line_list += ['', '```'] + list(name_list) + ['```', '']
    return '\n'.join(line_list)

