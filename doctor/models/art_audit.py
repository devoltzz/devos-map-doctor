# Lists the art a map asks for and where it is: in the map, in the game, or nowhere.
import collections
import os
import re
import struct

from doctor.mpq import mpqread
from doctor.models import mdxtex
from doctor.port import name_without_dot


B = chr(92)
RX_ART = r'blp|tga|dds|mdl|mdx'
RX_SOUNDS = r'wav|mp3|flac|ogg'
MAP_DATA = ['war3map.w3u', 'war3map.w3t', 'war3map.w3a', 'war3map.w3b', 'war3map.w3d', 'war3map.w3h', 'war3map.w3q',
            'war3map.wts', 'war3mapSkin.txt', 'war3mapMisc.txt', 'war3map.w3i',
            'war3mapSkin.w3u', 'war3mapSkin.w3t', 'war3mapSkin.w3a', 'war3mapSkin.w3b', 'war3mapSkin.w3d',
            'war3mapSkin.w3h', 'war3mapSkin.w3q']
UNITS = [
    'UnitUI.slk',
    'UnitData.slk',
    'ItemData.slk',
    'AbilityData.slk',
    'DestructableData.slk',
    'UnitSkin.txt',
    'ItemSkin.txt',
    'AbilitySkin.txt',
    'CampaignUnitStrings.txt',
    'CampaignUnitFunc.txt',
    'CampaignAbilityStrings.txt',
    'CampaignAbilityFunc.txt',
    'CampaignUpgradeStrings.txt',
    'CampaignUpgradeFunc.txt',
    'CommonAbilityStrings.txt',
    'CommonAbilityFunc.txt',
    'HumanUnitStrings.txt',
    'HumanUnitFunc.txt',
    'HumanAbilityStrings.txt',
    'HumanAbilityFunc.txt',
    'OrcUnitStrings.txt',
    'OrcUnitFunc.txt',
    'OrcAbilityStrings.txt',
    'OrcAbilityFunc.txt',
    'UndeadUnitStrings.txt',
    'UndeadUnitFunc.txt',
    'UndeadAbilityStrings.txt',
    'UndeadAbilityFunc.txt',
    'NightElfUnitStrings.txt',
    'NightElfUnitFunc.txt',
    'NightElfAbilityStrings.txt',
    'NightElfAbilityFunc.txt',
    'NeutralUnitStrings.txt',
    'NeutralUnitFunc.txt',
    'NeutralAbilityStrings.txt',
    'NeutralAbilityFunc.txt',
    'ItemStrings.txt',
    'ItemFunc.txt',
    'ItemAbilityStrings.txt',
    'ItemAbilityFunc.txt',
]


def norm(p):
    p = p.strip().strip('"').replace('/', B).lstrip(B)
    while B + B in p:
        p = p.replace(B + B, B)
    return p


def emitters(d):
    out = []
    p = 4
    while p + 8 <= len(d):
        tag = d[p:p + 4]
        n = struct.unpack_from('<I', d, p + 4)[0]
        if tag == b'PREM':
            q, end_pos = p + 8, p + 8 + n
            while q + 8 <= end_pos:
                sz, no = struct.unpack_from('<II', d, q)
                r = q + 4 + no + 16
                if sz <= 0 or no < 96 or r + 260 > q + sz:
                    break
                cpath = d[r:r + 260].split(b'\0')[0].decode('latin-1')
                if cpath:
                    out.append(cpath)
                q += sz
        p += 8 + n
    return out


class MapArchive(object):
    def __init__(self, file_path):
        self.a = mpqread.Archive(file_path)

    def finds(self, p):
        try:
            if self.a.find(p):
                return p
            if p.lower().endswith('.mdl') and self.a.find(p[:-4] + '.mdx'):
                return p[:-4] + '.mdx'
        except Exception:
            return None
        return None

    def read_data(self, p):
        try:
            return self.a.read(p)
        except Exception:
            return None


class ClassicArchives(object):
    def __init__(self, folder):
        from doctor.data import wc3_versions
        present_keys = {f.lower(): f for f in os.listdir(folder)}
        self.mpqs = []
        for fname in wc3_versions.FOLDER_ARCHIVES:
            f = present_keys.get(fname.lower())
            if f:
                self.mpqs.append((f, mpqread.Archive(os.path.join(folder, f))))
        if not self.mpqs:
            raise ValueError(
                'no MPQ of the classic game in %s (%s)' % (folder, ', '.join(wc3_versions.FOLDER_ARCHIVES))
            )

    def read_data(self, p):
        cands = [p] + ([p[:-4] + '.mdx'] if p.lower().endswith('.mdl') else [])
        for mpq_name, a in self.mpqs:
            for c in cands:
                try:
                    d = a.read(c)
                except Exception:
                    d = None
                if d:
                    return mpq_name, c, d
        return None


class GameArchives(object):
    def __init__(self, folder=None):
        from doctor.data import casc_wc3
        self.c = casc_wc3.CascWC3(folder) if folder else casc_wc3.CascWC3()
        self._by_name = None

    def finds(self, p):
        base, ext = os.path.splitext(p)
        e = ext.lower()
        cands = [p]
        if e in ('.blp', '.tga'):
            cands.append(base + '.dds')
        if e in ('.wav', '.mp3'):
            cands.append(base + '.flac')
        for c in cands:
            r = self.c.resolve(c)
            if r:
                return r
        return None

    def by_name(self, fname):
        if self._by_name is None:
            self._by_name = collections.defaultdict(list)
            for k, v in self.c.file_set.items():
                self._by_name[os.path.splitext(k.rsplit(B, 1)[-1].rsplit(':', 1)[-1])[0]].append(v[0])
        kind = TYPE_CODE.get(os.path.splitext(fname)[1].lower())
        out = [c for c in self._by_name.get(os.path.splitext(fname.lower())[0], [])
               if TYPE_CODE.get(os.path.splitext(c)[1].lower()) == kind]
        return sorted(out, key=lambda c: (c.lower().count('.w3mod:'), c.lower()))


TYPE_CODE = {'.blp': 'texture', '.dds': 'texture', '.tga': 'texture', '.mdl': 'model', '.mdx': 'model',
             '.wav': 'sound', '.mp3': 'sound', '.flac': 'sound', '.ogg': 'sound'}


def converte(d, new_value):
    import io
    import shutil
    import tempfile
    if new_value not in ('.blp', '.tga'):
        return d
    from PIL import Image
    from doctor.models import blpwrite
    from doctor.models import blpread
    tmp = tempfile.mkdtemp(prefix='arte_audita_')
    try:
        if d[:4] in (b'BLP1', b'BLP2'):
            if new_value == '.blp':
                return d
            ent = os.path.join(tmp, 'x.blp')
            open(ent, 'wb').write(d)
            im, _info = blpread.read_data(ent)
        else:
            im = Image.open(io.BytesIO(d))
            im.load()
        if new_value == '.blp':
            output = os.path.join(tmp, 'x.blp')
            blpwrite.save_blp(im.convert('RGBA'), output)
            return open(output, 'rb').read()
        buf = io.BytesIO()
        im.convert('RGBA').save(buf, format='TGA')
        return buf.getvalue()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def requested_ones(map_path, script, folders, rx):
    ped = collections.defaultdict(set)

    def sweep(body_text, label, literais):
        if literais:
            for m in re.finditer(r'"((?:[^"\\\n]|\\.)*)"', body_text):
                for a in rx.finditer(m.group(1).replace(B + B, B)):
                    ped[norm(a.group(0))].add(label)
        else:
            for a in rx.finditer(body_text):
                ped[norm(a.group(0))].add(label)
    if script:
        t = open(script, 'rb').read() if os.path.isfile(script) else None
    else:
        t = None
        for n in ('war3map.j', 'scripts' + B + 'war3map.j'):
            if map_path.finds(n):
                t = map_path.read_data(n)
                break
    if t:
        sweep(t.decode('utf-8', 'surrogateescape'), 'script', True)
    if folders:
        for folder in folders:
            for root, _d, fs in os.walk(folder):
                for f in fs:
                    d = open(os.path.join(root, f), 'rb').read()
                    sweep(d.decode('utf-8', 'surrogateescape'), f, False)
    else:
        for n in MAP_DATA + ['Units' + B + u for u in UNITS] + ['Doodads' + B + 'Doodads.slk']:
            if map_path.finds(n):
                d = map_path.read_data(n)
                if d:
                    sweep(d.decode('utf-8', 'surrogateescape'), n.rsplit(B, 1)[-1], False)
    return ped


def model_warnings(d, fname):
    from doctor.models import mdxfix
    from doctor.models import mdxgroups
    from doctor.models import mdxdeep
    from doctor.models import mdxcheck
    av = []
    if name_without_dot.many_dots(fname):
        av.append('name with several dots')
    if d[:4] != b'MDLX':
        return av + ['not a binary MDX (%r)' % d[:4]]
    _ch, err = mdxcheck.walk_path(d)
    if err:
        av.append('structure: ' + err)
        return av
    try:
        if mdxfix.fix_geoa_alfa(d)[1]:
            av.append('GEOA with negative alpha')
        gs = mdxgroups.group_stats(d)
        if gs and max(gs) >= 256:
            av.append('geoset with %d matrix groups' % max(gs))
        r = mdxdeep.deep(d)
        if r.get('max_objid', -1) >= 256:
            av.append('objectId %d' % r.get('max_objid'))
    except Exception as e:
        av.append('read error: %s' % str(e)[:60])
    return av


def audit(map_file_path, script=None, folders=None, sounds=False, with_game=True, game=None, copies=None, log=print,
          classic=None, others=None):
    rx = re.compile(
        r'[^\x00-\x1f",=|;\r\n]{1,260}?\.(?:%s)(?![0-9A-Za-z])' % (RX_ART + ('|' + RX_SOUNDS if sounds else '')), re.I
    )
    map_path = MapArchive(map_file_path)
    jg = GameArchives(game) if with_game else None
    cl = ClassicArchives(classic) if classic else None
    other_maps = [(os.path.basename(m), MapArchive(m)) for m in (others or [])]
    ped = requested_ones(map_path, script, folders, rx)
    work_queue = list(ped)
    seen = set()
    where = {}
    warnings = {}
    variation = {}
    while work_queue:
        p = work_queue.pop()
        k = p.lower()
        if k in seen:
            continue
        seen.add(k)
        map_name = map_path.finds(p)
        if map_name:
            where[k] = 'map_path'
            if map_name.lower().endswith('.mdx'):
                d = map_path.read_data(map_name) or b''
                warnings[k] = model_warnings(d, map_name)
                if d[:4] == b'MDLX':
                    try:
                        children = mdxtex.mdx_textures(d) + emitters(d)
                    except Exception:
                        children = []
                    for t in children:
                        t = norm(t)
                        if t:
                            ped[t].add('model ' + map_name)
                            work_queue.append(t)
            continue
        if jg and jg.finds(p):
            where[k] = 'game'
            continue
        root, ext = os.path.splitext(p)
        trunk = root.rsplit(B, 1)[-1].lower()
        if trunk in ('', 'none', '_', '.mdl', '.mdx'):
            where[k] = 'empty'
            continue
        if ext.lower() in ('.mdl', '.mdx'):
            var = root + '0' + ext
            if map_path.finds(var):
                where[k] = 'map_path'
                variation[k] = var
                continue
            if jg and jg.finds(var):
                where[k] = 'game'
                variation[k] = var
                continue
        where[k] = 'MISSING'
    line_list = []
    done_names = {}
    for p in sorted(ped, key=str.lower):
        height = 'variacao:' + variation[p.lower()] if p.lower() in variation else ''
        alt_content = None
        if where.get(p.lower()) == 'MISSING':
            base = p.rsplit(B, 1)[-1]
            in_map = [
                n
                for n in (base, 'war3mapImported' + B + base)
                if map_path.finds(n)
                and TYPE_CODE.get(os.path.splitext(n)[1].lower()) == TYPE_CODE.get(os.path.splitext(p)[1].lower())
            ]
            found_classic = cl.read_data(p) if cl else None
            found_other = None
            if not found_classic:
                for other_name, other in other_maps:
                    n_other = other.finds(p)
                    d_other = other.read_data(n_other) if n_other else None
                    if d_other:
                        found_other = other_name, n_other, d_other
                        break
            if found_classic:
                height = 'classico:%s:%s' % (found_classic[0], found_classic[1])
                if copies:
                    alt_content = found_classic[2], os.path.splitext(found_classic[1])[1].lower()
            elif found_other:
                height = 'mapa:%s:%s' % (found_other[0], found_other[1])
                if copies:
                    alt_content = found_other[2], os.path.splitext(found_other[1])[1].lower()
            elif in_map:
                height = 'mapa:' + in_map[0]
                if copies:
                    alt_content = map_path.read_data(map_path.finds(in_map[0])), os.path.splitext(in_map[0])[1].lower()
            elif jg:
                cands = jg.by_name(base)
                if cands:
                    height = 'jogo:' + cands[0] + (' (+%d)' % (len(cands) - 1) if len(cands) > 1 else '')
                    if copies:
                        try:
                            alt_content = jg.c.read_data(cands[0]), os.path.splitext(cands[0])[1].lower()
                        except Exception:
                            alt_content = None
        if copies and alt_content and alt_content[0] and p.lower() not in done_names:
            fname = p[:-4] + '.mdx' if p.lower().endswith('.mdl') else p
            pieces = [x for x in fname.split(B) if x and x not in ('.', '..') and ':' not in x]
            if not pieces:
                continue
            dest = os.path.join(copies, *pieces)
            try:
                d = converte(alt_content[0], os.path.splitext(p)[1].lower()) \
                    if alt_content[1] != os.path.splitext(p)[1].lower() else alt_content[0]
                os.makedirs(os.path.dirname(dest) or '.', exist_ok=True)
                open(dest, 'wb').write(d)
                done_names[p.lower()] = (dest, len(d))
                height += ' [copied]'
            except Exception as e:
                height += ' [copy failed: %s]' % str(e)[:40]
        line_list.append((p, where.get(p.lower(), '?'), height, '; '.join(warnings.get(p.lower(), [])),
                          '; '.join(sorted(ped[p]))[:300]))
    summary = collections.Counter(x[1] for x in line_list)
    warning_summary = collections.Counter()
    for x in line_list:
        for a in x[3].split('; '):
            if a:
                warning_summary[a.split(':')[0] if a.startswith(('structure', 'err')) else
                                re.sub(r'\d+', 'N', a)] += 1
    return line_list, {'where': dict(summary), 'warnings': dict(warning_summary)}


def _s(x):
    return x.encode('utf-8', 'surrogateescape').decode('utf-8', 'replace')

