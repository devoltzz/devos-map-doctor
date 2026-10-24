# Lists the art a map asks for and where it is: in the map, in the game, or nowhere.
import collections
import os
import re
import struct



B = chr(92)
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


def _s(x):
    return x.encode('utf-8', 'surrogateescape').decode('utf-8', 'replace')

