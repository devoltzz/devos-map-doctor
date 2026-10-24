# Removes or empties the files only the World Editor reads, when the game does not need them.
import re



SCRIPTS = ('war3map.j', 'scripts\\war3map.j', 'war3map.lua')
def _read(a, fname):
    try:
        return a.read(fname) if a.find(fname) else None
    except Exception:
        return None


def _script(a):
    for fname in SCRIPTS:
        d = _read(a, fname)
        if d:
            return fname, d
    return None, None


def map_names(a):
    from doctor.data import map_formats
    try:
        lst = a.read('(listfile)') or b''
    except Exception:
        lst = b''
    name_list = [n for n in re.split('[\r\n]+', lst.decode('utf-8', 'surrogateescape')) if n.strip()]
    seen = set(n.lower() for n in name_list)
    for n in map_formats.standard_names():
        if n.lower() not in seen and a.find(n):
            name_list.append(n)
            seen.add(n.lower())
    return name_list

