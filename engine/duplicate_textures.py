# Finds identical imported textures and makes each one a different file.
import hashlib


EXTENSIONS = ('.blp', '.dds')


def _by_size(a, name_list):
    out, seen, block_list = {}, set(), set()
    for n in name_list:
        low = n.lower()
        if not low.endswith(EXTENSIONS) or low in seen:
            continue
        seen.add(low)
        try:
            f = a.find(n)
        except Exception:
            f = None
        if not f or f[1] >= len(a.blocks) or f[1] in block_list:
            continue
        block_list.add(f[1])
        out.setdefault(a.blocks[f[1]][2], []).append((n, f[1]))
    return out


def _read(a, fname, block_entry):
    try:
        return a.read(fname, bi=block_entry)
    except Exception:
        return None


def clusters(a, name_list):
    out = []
    for sz, ns in _by_size(a, name_list).items():
        if len(ns) < 2 or not sz:
            continue
        by_h = {}
        for n, bi in ns:
            b = _read(a, n, bi)
            if b:
                by_h.setdefault(hashlib.sha1(b).digest(), []).append(n)
        out += [sorted(g, key=lambda n: (n.lower(), n)) for g in by_h.values() if len(g) > 1]
    return sorted(out, key=lambda g: (g[0].lower(), g))


def make_distinct(a, name_list, gs=None):
    gs = clusters(a, name_list) if gs is None else gs
    if not gs:
        return {}, []
    sz = _by_size(a, name_list)
    occupied = {}

    def exists(b):
        t = len(b)
        if t not in occupied:
            occupied[t] = set()
            for n, bi in sz.get(t, []):
                x = _read(a, n, bi)
                if x is not None:
                    occupied[t].add(hashlib.sha1(x).digest())
        return hashlib.sha1(b).digest() in occupied[t]

    new_ones, report = {}, []
    for g in gs:
        base = _read(a, g[0], a.find(g[0])[1])
        if base is None:
            continue
        modified = []
        k = 0
        for n in g:
            k += 1
            b = base + b'\0' * k
            while exists(b):
                k += 1
                b = base + b'\0' * k
            occupied.setdefault(len(b), set()).add(hashlib.sha1(b).digest())
            new_ones[n] = b
            modified.append(n)
        report.append({'cluster': list(g), 'modified': modified, 'byte_size': len(base)})
    return new_ones, report
