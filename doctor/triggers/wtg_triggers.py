# Checks war3map.wtg against the game's TriggerData.txt.
import struct


SECTIONS = {'TriggerEvents': 'event', 'TriggerConditions': 'condition', 'TriggerActions': 'action',
            'TriggerCalls': 'call'}
ECA_TYPE = {0: 'event', 1: 'condition', 2: 'action', 3: 'call'}
_CACHE = {}


def arities(body_text):
    d = dict((v, {}) for v in SECTIONS.values())
    sec = None
    for ln in body_text.splitlines():
        s = ln.strip()
        if not s or s.startswith('//'):
            continue
        if s.startswith('[') and s.endswith(']'):
            sec = SECTIONS.get(s[1:-1])
            continue
        if sec is None or '=' not in s:
            continue
        k, v = s.split('=', 1)
        k = k.strip()
        if not k or k.startswith('_') or k in d[sec]:
            continue
        fields = [x.strip() for x in v.split(',')]
        args = fields[3:] if sec == 'call' else fields[1:]
        d[sec][k] = len([x for x in args if x and x != 'nothing'])
    return d


def game_arities(game=None):
    if game in _CACHE:
        return _CACHE[game]
    arity = None
    try:
        from doctor.data import casc_wc3
        c = casc_wc3.CascWC3(game) if game else casc_wc3.CascWC3()
        b = c.read_wc3('ui\\triggerdata.txt')
        if b:
            arity = arities(b.decode('utf-8', 'replace'))
    except Exception:
        arity = None
    _CACHE[game] = arity
    return arity


class _Unknown(Exception):
    pass


class _Reader(object):
    def __init__(self, b, arity):
        self.b, self.arity, self.p = b, arity, 0
        self.unknowns = []

    def u(self, fmt):
        v = struct.unpack_from('<' + fmt, self.b, self.p)
        self.p += struct.calcsize('<' + fmt)
        return v[0] if len(v) == 1 else v

    def z(self):
        e = self.b.index(b'\x00', self.p)
        s = self.b[self.p:e]
        self.p = e + 1
        return s.decode('utf-8', 'replace')

    def parameter(self):
        self.u('i')
        self.z()
        if self.u('i') == 1:
            self.eca(False)
        if self.u('i') == 1:
            self.parameter()

    def eca(self, child):
        kind = self.u('i')
        if child:
            self.u('i')
        fname = self.z()
        self.u('i')
        t = ECA_TYPE.get(kind)
        if t is None or fname not in self.arity[t]:
            self.unknowns.append('%s:%s' % (t or kind, fname))
            raise _Unknown(fname)
        for _i in range(self.arity[t][fname]):
            self.parameter()
        for _i in range(self.u('i')):
            self.eca(True)

    def trigger(self, new):
        self.z()
        self.z()
        self.u('i')
        if new:
            self.u('I')
        self.u('iiiii')
        for _i in range(self.u('i')):
            self.eca(False)

    def read_data(self):
        b = self.b
        if b[:4] != b'WTG!':
            raise ValueError('does not start with WTG!')
        self.p = 4
        ver = self.u('I')
        new = ver == 0x80000004
        if not new and ver != 7:
            return {'version_num': ver, 'unchecked': True}
        trigger_list = 0
        if not new:
            for _i in range(self.u('i')):
                self.u('i')
                self.z()
                self.u('i')
            if self.u('i') != 2:
                raise ValueError('the variables marker is not 2')
            nvars = self.u('i')
            for _i in range(nvars):
                self.z()
                self.z()
                self.u('iiii')
                self.z()
            for _i in range(self.u('i')):
                self.trigger(False)
                trigger_list += 1
        else:
            self.u('I')
            self.u('IIII')
            for _k in range(5):
                self.u('I')
                for _j in range(self.u('I')):
                    self.u('I')
            self.u('II')
            if self.u('i') != 2:
                raise ValueError('the variables marker is not 2')
            nvars = self.u('i')
            for _i in range(nvars):
                self.z()
                self.z()
                self.u('iiii')
                self.z()
                self.u('II')
            nel = self.u('I') - 1
            self.u('ii')
            self.z()
            self.u('iii')
            for _i in range(nel):
                cl = self.u('i')
                if cl == 4:
                    self.u('i')
                    self.z()
                    self.u('i')
                    self.u('i')
                    self.u('I')
                elif cl in (8, 16, 32):
                    self.trigger(True)
                    trigger_list += 1
                elif cl == 64:
                    self.u('I')
                    self.z()
                    self.u('I')
                else:
                    raise ValueError('element of class %d' % cl)
        return {
            'version_num': '1.31' if new else 7,
            'vars': nvars,
            'trigger_list': trigger_list,
            'on_close': self.p == len(b),
        }


def verify(b, arity):
    r = _Reader(b, arity)
    out = {'unknowns': [], 'err': None, 'on_close': None}
    try:
        out.update(r.read_data())
    except _Unknown:
        out['err'] = 'unknown function'
    except (ValueError, IndexError, struct.error) as e:
        out['err'] = str(e)[:120] or type(e).__name__
    out['unknowns'] = r.unknowns
    return out


def needs_regeneration(b, arity=None):
    arity = arity if arity is not None else game_arities()
    if not arity or not b:
        return None
    c = verify(b, arity)
    if c.get('unchecked'):
        return None
    if c['unknowns']:
        return 'function missing from the game TriggerData: %s' % ', '.join(c['unknowns'][:3])
    if c['err']:
        return 'war3map.wtg cannot be read: %s' % c['err']
    if not c.get('on_close'):
        return 'war3map.wtg does not end at the last byte'
    return None
