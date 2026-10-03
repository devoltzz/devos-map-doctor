# Gives models with dots in the file name a copy under a name Warcraft III 3.0 loads.
import re


B = chr(92)


def many_dots(file_path):
    base = file_path.replace('/', B).split(B)[-1]
    return base.count('.') > 1


def alias_name(file_path):
    c = file_path.replace('/', B)
    folder, _, base = c.rpartition(B)
    fname, _, ext = base.rpartition('.')
    new = fname.replace('.', '_') + '.' + ext
    return (folder + B + new) if folder else new


def map_models(name_list):
    listing = {}
    seen = set()
    for n in sorted(name_list, key=lambda x: (x.lower(), x)):
        if not n.lower().endswith(('.mdx', '.mdl')) or not many_dots(n):
            continue
        orig = n[:-4] + '.mdx'
        if orig.lower() in seen:
            continue
        seen.add(orig.lower())
        listing[orig] = alias_name(orig)
    return listing


def copies(archive, map_path):
    output, gaps = [], []
    for orig, new in sorted(map_path.items()):
        d = None
        for n in (orig, orig[:-4] + '.mdl'):
            try:
                d = archive.read(n) if archive.find(n) else None
            except Exception:
                d = None
            if d:
                break
        if not d or d[:4] != b'MDLX':
            gaps.append('%s (%s)' % (orig, 'is not in the map' if not d else 'not binary MDX'))
            continue
        output.append((new, d))
    return output, gaps


def _rx(map_path, sep):
    alternatives = [re.escape(o[:-4].replace(B, sep)) for o in sorted(map_path, key=len, reverse=True)]
    return re.compile(r'(?i)(?<![0-9A-Za-z_\-.])(' + '|'.join(alternatives) + r')\.(mdl|mdx)(?![0-9A-Za-z_])')


def swap(body_text, map_path, sep=B):
    by_base = dict((o[:-4].lower(), a[:-4]) for o, a in map_path.items())
    tally = dict((o, 0) for o in map_path)
    if not map_path:
        return body_text, tally

    def sub(m):
        base = m.group(1).replace(sep, B).lower()
        orig = next(o for o in map_path if o[:-4].lower() == base)
        tally[orig] += 1
        return by_base[base].replace(B, sep) + '.' + m.group(2)
    return _rx(map_path, sep).sub(sub, body_text), tally
