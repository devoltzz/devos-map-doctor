# Keeps the classic (SD) look of the game's effect models a map uses: copies under new names, references rewritten.
import os
import re

from doctor.port import art_packs
from doctor.mpq import mpqread


B = chr(92)
FOLDER = 'war3mapImported' + B + 'KKSD'
OBJECTS = ('.w3a', '.w3b', '.w3d', '.w3u', '.w3t', '.w3h', '.w3q')
HD = 'war3.w3mod:_hd.w3mod:'
EFFECT_FOLDERS = ('abilities' + B, 'objects' + B + 'spawnmodels' + B)


def candidates(ped, casc, map_has, log=print):
    matches = {}
    for p in sorted(ped):
        k = p.lower()
        if not k.endswith('.mdx') or k in matches:
            continue
        if not k.startswith(EFFECT_FOLDERS):
            continue
        try:
            if map_has(p):
                continue
            sd, hd = casc.resolve(p, hd=False), casc.resolve(p, hd=True)
            if not sd or not hd or not hd.lower().startswith(HD) or sd == hd:
                continue
            sd_data, hd_data = casc.read_data(sd), casc.read_data(hd)
        except Exception as e:
            log('classic look: %s skipped (%s)' % (p, e))
            continue
        if sd_data and hd_data and sd_data != hd_data:
            matches[k] = (p, sd_data)
    return matches


def new_names(matches):
    new_ones, in_use = {}, set()
    for k in sorted(matches):
        base = os.path.splitext(matches[k][0].split(B)[-1])[0]
        fname, n = base, 1
        while fname.lower() in in_use:
            n += 1
            fname = '%s_%d' % (base, n)
        in_use.add(fname.lower())
        new_ones[k] = FOLDER + B + fname + '.mdx'
    return new_ones


def _swap(file_path, new_ones):
    return new_ones.get(art_packs.norm(file_path).lower())


def rewrite_text(body_text, new_ones):
    n = 0

    def sub(m):
        nonlocal n
        new = _swap(m.group(0), new_ones)
        if new is None:
            return m.group(0)
        n += 1
        return new
    return art_packs.RX_FILE.sub(sub, body_text), n


def rewrite_script(body_text, new_ones):
    n = 0
    if not any(os.path.basename(p.replace(B, '/'))[:-4].lower() in body_text.lower() for p in new_ones):
        return body_text, 0

    def lit(m):
        nonlocal n
        k = 0

        def sub(a):
            nonlocal k
            new = _swap(a.group(0), new_ones)
            if new is None:
                return a.group(0)
            k += 1
            return new.replace(B, B + B)
        s = art_packs.RX_FILE.sub(sub, m.group(1))
        n += k
        return m.group(0) if not k else '"' + s + '"'
    return art_packs.RX_LITERAL.sub(lit, body_text), n


def rewrite_objects(data_bytes, new_ones):
    n = 0
    for old, new in new_ones.items():
        for ext in ('.mdx', '.mdl'):
            tgt = re.escape((old[:-4] + ext).encode('latin-1', 'replace'))
            swap = new.encode('latin-1')
            data_bytes, k = re.subn(b'(?<=[\x00,])' + tgt + b'(?=[\x00,])', lambda _m: swap, data_bytes, flags=re.I)
            n += k
    return data_bytes, n


def applies(script, data_bytes, extract, map_path, dest, casc=None, log=print, sources=()):
    details = {
        'status': 'nothing',
        'models': [],
        'bytes': 0,
        'references': {'script': 0, 'data_bytes': 0, 'objects': 0},
        'reason': '',
    }
    if casc is None:
        try:
            from doctor.data import casc_wc3
            casc = casc_wc3.CascWC3()
        except Exception as e:
            details.update(status='skipped', reason='the game files cannot be read (%s)' % e)
            return details
    a = mpqread.Archive(map_path)
    with open(script, 'rb') as f:
        body_text = f.read().decode('utf-8', 'surrogateescape')
    units = os.path.join(data_bytes, 'Units') if data_bytes else None
    ped = art_packs.requested_ones(body_text, units if units and os.path.isdir(units) else None, extract)
    matches = candidates(ped, casc, lambda p: a.find(p) is not None or a.find(p[:-4] + '.mdl') is not None, log)
    if not matches:
        return details
    new_ones = new_names(matches)
    for k, (p, d) in sorted(matches.items()):
        tgt = os.path.join(dest, new_ones[k].replace(B, os.sep))
        os.makedirs(os.path.dirname(tgt), exist_ok=True)
        with open(tgt, 'wb') as f:
            f.write(d)
        details['models'].append((p, new_ones[k], len(d)))
        details['bytes'] += len(d)
    new_text, n = rewrite_script(body_text, new_ones)
    if n:
        with open(script, 'wb') as f:
            f.write(new_text.encode('utf-8', 'surrogateescape'))
    details['references']['script'] = n
    if units and os.path.isdir(units):
        for fname in sorted(os.listdir(units)):
            if fname.lower().endswith(('.slk', '.txt')):
                c = os.path.join(units, fname)
                with open(c, 'rb') as f:
                    t = f.read().decode('utf-8', 'surrogateescape')
                t2, k = rewrite_text(t, new_ones)
                if k:
                    with open(c, 'wb') as f:
                        f.write(t2.encode('utf-8', 'surrogateescape'))
                    details['references']['data_bytes'] += k
    if data_bytes:
        from doctor.port import int32_balance
        folders = [data_bytes] + [p for p in (sources or ()) if p] + [extract]
        folders = [p for p in folders if p and os.path.isdir(p)]
        name_list = {}
        for folder in folders:
            for fname in sorted(os.listdir(folder)):
                if fname.lower().startswith('war3map') and fname.lower().endswith(OBJECTS):
                    name_list.setdefault(fname.lower(), fname)
        for hash_key in sorted(name_list):
            finding = None
            for folder in folders:
                finding = int32_balance._find_ci(folder, [name_list[hash_key]])
                if finding:
                    break
            if not finding:
                continue
            with open(finding, 'rb') as f:
                d = f.read()
            d2, k = rewrite_objects(d, new_ones)
            if k:
                os.makedirs(data_bytes, exist_ok=True)
                in_data_folder = os.path.normcase(os.path.dirname(os.path.abspath(finding))) == \
                    os.path.normcase(os.path.abspath(data_bytes))
                with open(
                    finding if in_data_folder else os.path.join(data_bytes, os.path.basename(finding)), 'wb'
                ) as f:
                    f.write(d2)
                details['references']['objects'] += k
    details['status'] = 'done'
    return details
