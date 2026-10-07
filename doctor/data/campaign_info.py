# Reads and writes war3campaign.w3f, the info of a campaign: its name and its maps.
import struct



FILE = 'war3campaign.w3f'
WTS = 'war3campaign.wts'
RACES = {0: 'human', 1: 'orc', 2: 'undead', 3: 'night elf'}


class _Reader(object):
    def __init__(self, data):
        self.d, self.p = data, 0

    def i32(self):
        v = struct.unpack_from('<i', self.d, self.p)[0]
        self.p += 4
        return v

    def f32(self):
        v = struct.unpack_from('<f', self.d, self.p)[0]
        self.p += 4
        return v

    def raw(self, n):
        if self.p + n > len(self.d):
            raise ValueError('the file ends inside a field')
        v = self.d[self.p:self.p + n]
        self.p += n
        return v

    def s(self):
        e = self.d.index(b'\0', self.p)
        v = self.d[self.p:e]
        self.p = e + 1
        return v


def parse(data):
    r = _Reader(bytes(data))
    try:
        m = {'version': r.i32()}
        if m['version'] not in (1, 2, 3):
            raise ValueError('war3campaign.w3f version %d' % m['version'])
        m['campaign_version'], m['editor_version'] = r.i32(), r.i32()
        m['name'], m['difficulty'], m['author'], m['description'] = r.s(), r.s(), r.s(), r.s()
        m['flags'], m['background_number'] = r.i32(), r.i32()
        m['background_path'], m['minimap_path'] = r.s(), r.s()
        m['ambient_sound_number'], m['ambient_sound_path'] = r.i32(), r.s()
        m['fog'] = [r.i32(), r.f32(), r.f32(), r.f32(), r.raw(4)]
        m['race'] = r.i32()
        if m['version'] >= 3:
            m['fog_v3'] = [r.f32(), r.f32(), r.f32(), r.f32(), r.f32(), r.i32()]
        if m['version'] >= 2:
            m['background_version'] = r.i32()
        m['buttons'] = []
        for _ in range(_count(r)):
            m['buttons'].append({'visible': r.i32(), 'chapter': r.s(), 'title': r.s(), 'map': r.s()})
        m['maps'] = []
        for _ in range(_count(r)):
            m['maps'].append({'unk': r.s(), 'map': r.s()})
    except (struct.error, IndexError) as e:
        raise ValueError('war3campaign.w3f does not read: %s' % e)
    if r.p != len(r.d):
        raise ValueError('war3campaign.w3f: %d bytes after the last map' % (len(r.d) - r.p))
    return m


def _count(r):
    n = r.i32()
    if not 0 <= n <= 1000:
        raise ValueError('implausible count %d' % n)
    return n


def write(m):
    v = m['version']
    out = [struct.pack('<iii', v, m['campaign_version'], m['editor_version'])]
    for k in ('name', 'difficulty', 'author', 'description'):
        out.append(m[k] + b'\0')
    out.append(struct.pack('<ii', m['flags'], m['background_number']))
    out.append(m['background_path'] + b'\0' + m['minimap_path'] + b'\0')
    out.append(struct.pack('<i', m['ambient_sound_number']) + m['ambient_sound_path'] + b'\0')
    f = m['fog']
    out.append(struct.pack('<ifff', f[0], f[1], f[2], f[3]) + f[4])
    out.append(struct.pack('<i', m['race']))
    if v >= 3:
        out.append(struct.pack('<fffffi', *m['fog_v3']))
    if v >= 2:
        out.append(struct.pack('<i', m['background_version']))
    out.append(struct.pack('<i', len(m['buttons'])))
    for b in m['buttons']:
        out.append(struct.pack('<i', b['visible']) + b['chapter'] + b'\0' + b['title'] + b'\0' + b['map'] + b'\0')
    out.append(struct.pack('<i', len(m['maps'])))
    for x in m['maps']:
        out.append(x['unk'] + b'\0' + x['map'] + b'\0')
    return b''.join(out)


def _text(b):
    for enc in ('utf-8', 'gbk', 'latin-1'):
        try:
            return b.decode(enc)
        except UnicodeDecodeError:
            continue
    return b.decode('latin-1')


def read(path):
    from doctor.fix import unprotect
    try:
        a = unprotect._open(path)
    except BaseException as e:
        if isinstance(e, KeyboardInterrupt):
            raise
        return {'error': 'The campaign does not open (%s).' % unprotect._error(e)}
    data = unprotect._read(a, FILE)
    if data is None:
        return None
    try:
        m = parse(data)
    except ValueError as e:
        return {'error': str(e)}
    from doctor.viewers import map_card
    strings = map_card.wts_strings(unprotect._read(a, WTS))

    def t(b):
        return map_card._resolve(b, strings)[0]
    return {'name': t(m['name']), 'author': t(m['author']), 'difficulty': t(m['difficulty']),
            'description': t(m['description']), 'race': RACES.get(m['race'], str(m['race'])),
            'version': m['version'],
            'maps': [{'title': t(b['title']), 'chapter': t(b['chapter']), 'file': _text(b['map'])}
                     for b in m['buttons']]}
