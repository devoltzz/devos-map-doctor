# Reads a precompiled Lua 5.3 chunk: its functions, constants and instructions.
import struct


SIGNATURE = b'\x1bLua'


class Reader(object):
    def __init__(self, data):
        if data[:4] != SIGNATURE or len(data) < 18 or data[4] != 0x53:
            raise ValueError('not a Lua 5.3 chunk (%r)' % data[:6])
        self.d = data
        self.sint, self.ssize, self.sinstr, self.sinteger, self.snumber = data[12:17]
        self.i = 17 + self.sinteger + self.snumber + 1

    def byte(self):
        v = self.d[self.i]
        self.i += 1
        return v

    def raw(self, n):
        if self.i + n > len(self.d):
            raise ValueError('the chunk ends early (%d of %d)' % (self.i + n, len(self.d)))
        v = self.d[self.i:self.i + n]
        self.i += n
        return v

    def int(self):
        return int.from_bytes(self.raw(self.sint), 'little', signed=True)

    def size(self):
        return int.from_bytes(self.raw(self.ssize), 'little')

    def string(self):
        n = self.byte()
        if n == 0:
            return None
        if n == 0xFF:
            n = self.size()
        return self.raw(n - 1)

    def function(self, parent_source=None):
        f = {'source': self.string() or parent_source}
        f['line'], f['lastline'] = self.int(), self.int()
        f['params'], f['vararg'], f['stack'] = self.byte(), self.byte(), self.byte()
        f['code'] = [int.from_bytes(self.raw(self.sinstr), 'little') for _ in range(self.int())]
        consts = []
        for _ in range(self.int()):
            t = self.byte()
            if t == 0:
                consts.append(None)
            elif t == 1:
                consts.append(bool(self.byte()))
            elif t == 3:
                consts.append(struct.unpack('<d', self.raw(8))[0])
            elif t == 0x13:
                consts.append(int.from_bytes(self.raw(self.sinteger), 'little', signed=True))
            elif t in (4, 0x14):
                consts.append(self.string())
            else:
                raise ValueError('constant of type %d at byte %d' % (t, self.i))
        f['consts'] = consts
        f['upvals'] = [(self.byte(), self.byte()) for _ in range(self.int())]
        f['protos'] = [self.function(f['source']) for _ in range(self.int())]
        f['lineinfo'] = [self.int() for _ in range(self.int())]
        f['locvars'] = [(self.string(), self.int(), self.int()) for _ in range(self.int())]
        f['upnames'] = [self.string() for _ in range(self.int())]
        return f


def load(data):
    r = Reader(data)
    f = r.function()
    return f, r.i == len(data)


def walk(f):
    yield f
    for p in f['protos']:
        yield from walk(p)


def strings(f):
    return [c for g in walk(f) for c in g['consts'] if isinstance(c, bytes)]
