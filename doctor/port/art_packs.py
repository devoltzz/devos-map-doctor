# Imports the art a map asks for that only the platform packages (.mix, .asi, .mpq) have.
import collections
import os
import re
import struct

from doctor.mpq import mpqread


B = chr(92)
RX_FILE = re.compile(r'[^\x00-\x1f",=|;\r\n]+?\.(?:blp|tga|dds|mdl|mdx)(?![0-9A-Za-z])', re.I)
RX_SOUND = re.compile(r'[^\x00-\x1f",=|;\r\n]+?\.(?:wav|mp3|flac|ogg)(?![0-9A-Za-z])', re.I)
RX_LITERAL = re.compile(r'"((?:[^"\\\n]|\\.)*)"')
CHANGED_FOLDERS = [
    (
        'units\\undead\\plaguecloud\\plaguecloudcaster.mdx',
        'abilities\\spells\\undead\\plaguecloud\\plaguecloudcaster.mdx',
    ),
]
RX_CIN = re.compile(r'(?i)^(units\\\w+\\)(\w+?)cin\\(\w+cin\.mdx)$')


def norm(p):
    p = p.strip().strip('"').replace('/', B).lstrip(B)
    while B + B in p:
        p = p.replace(B + B, B)
    if p.lower().endswith('.mdl'):
        p = p[:-4] + '.mdx'
    return p


def emitters(d):
    out = []
    p = 4
    while p + 8 <= len(d):
        tag = d[p:p + 4]
        n = struct.unpack_from('<I', d, p + 4)[0]
        if tag == b'PREM':
            for m in re.finditer(rb'[\x20-\x7e]{3,259}\.(?:mdl|mdx|MDL|MDX)', d[p + 8:p + 8 + n]):
                out.append(m.group(0).decode('latin-1'))
        p += 8 + n
    return out


def mdx_references(d):
    from doctor.models import mdxtex
    try:
        return list(mdxtex.mdx_textures(d)) + emitters(d)
    except Exception:
        return []


def requested_ones(script, data_bytes=None, extract=None):
    ped = collections.defaultdict(set)
    for m in RX_LITERAL.finditer(script):
        lit = m.group(1).replace(B + B, B)
        for a in RX_FILE.finditer(lit):
            ped[norm(a.group(0))].add('script')
        for a in RX_SOUND.finditer(lit):
            ped[norm(a.group(0))].add('script (sound)')
    sources = []
    if data_bytes and os.path.isdir(data_bytes):
        sources += [os.path.join(data_bytes, f) for f in os.listdir(data_bytes)]
    if extract:
        sources += [os.path.join(extract, 'Doodads', 'Doodads.slk'), os.path.join(extract, 'war3mapSkin.txt'),
                    os.path.join(extract, 'war3mapMisc.txt')]
        if not data_bytes and os.path.isdir(os.path.join(extract, 'Units')):
            sources += [os.path.join(extract, 'Units', f) for f in os.listdir(os.path.join(extract, 'Units'))]
    for p in sources:
        if os.path.isfile(p):
            for a in RX_FILE.finditer(open(p, 'rb').read().decode('utf-8', 'surrogateescape')):
                ped[norm(a.group(0))].add(os.path.basename(p))
    if extract:
        for root, _d, fs in os.walk(extract):
            for f in fs:
                p = os.path.join(root, f)
                with open(p, 'rb') as h:
                    if h.read(4) != b'MDLX':
                        continue
                for t in mdx_references(open(p, 'rb').read()):
                    ped[norm(t)].add('a model of the map')
    return ped


def open_packs(caminhos, log=print):
    out = []
    for c in caminhos:
        try:
            a = mpqread.Archive(c)
        except BaseException as e:
            log('package %s: no MPQ inside (%s)' % (os.path.basename(c), e))
            continue
        out.append((os.path.basename(c), a))
    return out


def converte(d, new_value):
    import io
    import shutil
    import tempfile
    from PIL import Image
    from doctor.models import blpwrite
    from doctor.models import blpread
    tmp = tempfile.mkdtemp()
    try:
        if d[:4] in (b'BLP1', b'BLP2'):
            ent = os.path.join(tmp, 'x.blp')
            open(ent, 'wb').write(d)
            im, _info = blpread.read_data(ent)
        else:
            im = Image.open(io.BytesIO(d))
            im.load()
        if new_value == 'blp':
            output = os.path.join(tmp, 'x.blp')
            blpwrite.save_blp(im, output)
            return open(output, 'rb').read()
        buf = io.BytesIO()
        im.convert('RGBA').save(buf, format='TGA')
        return buf.getvalue()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def variants(p):
    out = []
    low = p.lower()
    imp = 'war3mapimported' + B
    if low.startswith(imp):
        out.append((p[len(imp):], None))
    else:
        out.append(('war3mapImported' + B + p, None))
    if low.endswith('.mdx.mdx') or low.endswith('.mdl.mdx'):
        out.append((p[:-4], None))
    base, ext = os.path.splitext(p)
    ext = ext.lower()
    if ext in ('.blp', '.tga', '.dds'):
        for other_table in ('.blp', '.tga', '.dds', '.png'):
            if other_table != ext:
                out.append((base + other_table, ext[1:] if ext in ('.blp', '.tga') else None))
    for from_, new_value in CHANGED_FOLDERS:
        if low == from_:
            out.append((new_value, None))
    m = RX_CIN.match(p)
    if m:
        out.append((m.group(1) + m.group(2) + B + m.group(3), None))
    return out


def resolve(map_path, pacotes, ped, in_game, log=print):
    import_it, missing_items, seen = {}, {}, set()
    work_queue = list(ped)

    def acha(p):
        for pack_name, art_pack in pacotes:
            if art_pack.find(p):
                return pack_name, art_pack, p
            if p.lower().endswith('.mdx') and art_pack.find(p[:-4] + '.mdl'):
                return pack_name, art_pack, p[:-4] + '.mdl'
        return None

    while work_queue:
        p = work_queue.pop()
        k = p.lower()
        if k in seen:
            continue
        seen.add(k)
        if map_path.find(p) or in_game(p):
            continue
        origin = acha(p)
        conv = None
        if origin is None:
            for height, c in variants(p):
                if map_path.find(height):
                    origin = ('map', map_path, height)
                elif in_game(height):
                    origin = ('game', None, height)
                else:
                    origin = acha(height)
                if origin:
                    conv = c
                    break
        if origin is None:
            missing_items[p] = ped.get(p, {'an imported model'})
            continue
        import_it[p] = origin + (conv,)
        if p.lower().endswith('.mdx') and origin[1] is not None:
            d = origin[1].read(origin[2]) or b''
            for t in mdx_references(d):
                t = norm(t)
                ped[t].add('imported model ' + p)
                work_queue.append(t)
    return import_it, missing_items


def import_it(map_path, pacotes, script, dest, data_bytes=None, extract=None, casc=None, log=print):
    import shutil
    a = mpqread.Archive(map_path)
    art_pack = open_packs(pacotes, log)
    if casc is None:
        try:
            from doctor.data import casc_wc3
            casc = casc_wc3.CascWC3()
        except Exception as e:
            log('the game files cannot be read (%s): everything the map lacks is looked up in the packages' % e)
            casc = None

    def in_game(p):
        if casc is None:
            return False
        try:
            if casc.resolve(p):
                return True
            base, ext = os.path.splitext(p)
            if ext.lower() in ('.blp', '.tga') and casc.resolve(base + '.dds'):
                return True
            return ext.lower() in ('.wav', '.mp3') and bool(casc.resolve(base + '.flac'))
        except Exception:
            return False

    def read_game(p):
        try:
            return casc.read_wc3(p)
        except Exception:
            return None

    ped = requested_ones(script, data_bytes, extract)
    imp, missing_items = resolve(a, art_pack, ped, in_game, log)
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    details = {
        'imported': 0,
        'missing_items': sorted(missing_items, key=str.lower),
        'bytes': 0,
        'by_pack': collections.Counter(),
        'warnings': [],
        'manifest': [],
    }
    from doctor.models import mdxfix
    for p in sorted(imp, key=str.lower):
        source, file_, cpath, conv = imp[p]
        d = read_game(cpath) if source == 'game' else (file_.read(cpath) or b'')
        if not d:
            details['missing_items'].append(p)
            continue
        if conv in ('blp', 'tga') and not cpath.lower().endswith('.' + conv):
            try:
                d = converte(d, conv)
            except Exception as e:
                details['warnings'].append('%s: the image could not be converted (%s)' % (p, e))
                continue
        if p.lower().endswith('.mdx'):
            if d[:4] != b'MDLX':
                details['warnings'].append('%s: %s is not a binary model' % (p, cpath))
                continue
            new, n = mdxfix.fix_geoa_alfa(d)
            if n:
                d = new
            details['warnings'] += check_mdx(p, d)
        tgt = os.path.join(dest, *[x for x in p.split(B) if x])
        os.makedirs(os.path.dirname(tgt), exist_ok=True)
        with open(tgt, 'wb') as f:
            f.write(d)
        details['imported'] += 1
        details['bytes'] += len(d)
        details['by_pack'][source] += 1
        details['manifest'].append((p, source, cpath, len(d), '; '.join(sorted(ped.get(p, set())))[:200]))
    details['by_pack'] = dict(details['by_pack'])
    details['missing_items'] = sorted(set(details['missing_items']), key=str.lower)
    log('art from packages: %d file(s) imported (%.1f MB; %s); %d asked for and found nowhere'
        % (details['imported'], details['bytes'] / 1e6, details['by_pack'], len(details['missing_items'])))
    return details


def check_mdx(p, d):
    out = []
    try:
        from doctor.models import mdxgroups
        gs = mdxgroups.group_stats(d)
        if gs and max(gs) >= 256:
            out.append('%s: a geoset with %d matrix groups (the hover can freeze the game)' % (p, max(gs)))
    except Exception:
        pass
    try:
        from doctor.models import mdxdeep
        r = mdxdeep.deep(d)
        if r.get('max_objid', -1) >= 256:
            out.append('%s: objectId %d (>= 256 corrupts the geometry)' % (p, r['max_objid']))
    except Exception:
        pass
    return out


def write_manifest(details, file_path):
    with open(file_path, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('path\tsource\tpath_in_source\tbytes\tasked_by\n')
        for x in details['manifest']:
            fh.write('%s\t%s\t%s\t%d\t%s\n' % x)
        for p in details['missing_items']:
            fh.write('%s\tMISSING\t\t0\t\n' % p)
