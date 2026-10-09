# Decrypts war3map.bin, the map script as encrypted bytecode (the j2b protection).
import bz2
import hashlib
import re
import struct

from doctor.script import kkwe


MAGIC = b'2SAJ'
HEADER = 12
HEADER_3RAW = 16
DELTA = 0x9E3779B9
_HIDDEN_CALL = b'\x00\x00\x00\x24'
TABLE = bytes.fromhex(
    '8e142799fdaac708d5e63e1ff6bb55da75a04a6ae8bd97ffde9bbc9f818aa146'
    '6e0be363767a6c5d88d369cac347b92583aba23fa6417cbae5ac95017ecf09c1'
    'd96270718ddb05022487ef54c6d43730d01bcb7bb8e4d8ec49ceaddc13a994c4'
    '8f39ae0d1852dd0e78faf58558d2af6da4b2533b51a550befc2df411489816f1'
    '86df3d665e442e2f36076b178b294cb6e2895fe7cda721e14dc965edfeee9c23'
    '337db7049e9a2a40b3105bf382771c92204e1e572272068c672c73fb59c20abf'
    '795cf90c281a126874341942b1c084f838f0159d60f23a6fb490eb911d7f3561'
    '5a320356a3c52b93800f4b43f7a8e03c96d16426d745cc4fc8b0e9b500d631ea'
    '000080')
WORDS = struct.unpack('<256I', b''.join(TABLE[i:i + 4] for i in range(256)))
STEPS = ((0x1C, 0xD8), (0x18, 0xD4), (0x0C, 0xC8), (0x04, 0xB8))
MASK = 0xFFFFFFFF


class J2bError(ValueError):
    pass


MAGIC_PLAIN = b'SSAJ'


def is_j2b(data):
    return data[:4] in (MAGIC, MAGIC_PLAIN) and len(data) >= HEADER


def _rol(value, bits):
    return ((value << bits) | (value >> (32 - bits))) & MASK


def _step(state1, state2):
    index = []
    for i, (back, gain) in enumerate(STEPS):
        b = (state2 >> (8 * i)) & 0xFF
        index.append(b - back if b >= back else b + gain)
    mixed = _rol(WORDS[index[1]], 3) ^ _rol(WORDS[index[2]], 2) ^ WORDS[index[0]] ^ _rol(WORDS[index[3]], 1)
    return (state1 + mixed) & MASK, index[3] << 24 | index[2] << 16 | index[1] << 8 | index[0]


def keystream(seed1, seed2, count):
    keys = []
    for _ in range(count):
        seed1, seed2 = _step(seed1, seed2)
        keys.append((seed1 + seed2) & MASK)
    return keys


def _byte_indices(np, b, back, gain, count):
    sequence, seen = [], {}
    while b not in seen and len(sequence) < count:
        seen[b] = len(sequence)
        b = b - back if b >= back else b + gain
        sequence.append(b)
    if len(sequence) < count:
        start = seen[b]
        cycle = np.array(sequence[start:], dtype=np.uint32)
        lead = np.array(sequence[:start], dtype=np.uint32)
        sequence = np.concatenate([lead, np.tile(cycle, (count - start) // len(cycle) + 1)])
    return np.asarray(sequence[:count], dtype=np.uint32)


def _keys(seed1, seed2, count):
    try:
        import numpy as np
    except ImportError:
        return struct.pack('<%dI' % count, *keystream(seed1, seed2, count))
    words = np.array(WORDS, dtype=np.uint32)
    index = [_byte_indices(np, (seed2 >> (8 * i)) & 0xFF, STEPS[i][0], STEPS[i][1], count) for i in range(4)]
    value = [words[x] for x in index]

    def rol(a, bits):
        return (a << np.uint32(bits)) | (a >> np.uint32(32 - bits))

    mixed = rol(value[1], 3) ^ rol(value[2], 2) ^ value[0] ^ rol(value[3], 1)
    state1 = (np.cumsum(mixed, dtype=np.uint64) + np.uint64(seed1)).astype(np.uint32)
    state2 = (index[3] << np.uint32(24)) | (index[2] << np.uint32(16)) | (index[1] << np.uint32(8)) | index[0]
    return (state1 + state2).astype('<u4').tobytes()


def _xor(body, seed1, seed2):
    count = (len(body) + 3) // 4
    keys = _keys(seed1, seed2, count)
    padded = body + bytes(-len(body) % 4)
    return (int.from_bytes(padded, 'little') ^ int.from_bytes(keys, 'little')).to_bytes(len(padded),
                                                                                        'little')[:len(body)]


def is_3raw(data):
    return (data[:4] == MAGIC and len(data) >= HEADER_3RAW + 8 and (len(data) - HEADER_3RAW) % 4 == 0
            and struct.unpack_from('<I', data, 12)[0] == len(data) - HEADER_3RAW)


def _key_3raw(value):
    return struct.unpack('<4I', hashlib.md5(str(value).encode()).hexdigest()[:16].encode())


def _xxtea(v, k, decrypt):
    n = len(v)
    rounds = 6 + 52 // n
    keys = [[k[p ^ e] for p in range(4)] for e in range(4)]
    if decrypt:
        s = (rounds * DELTA) & MASK
        y = v[0]
        for _ in range(rounds):
            kp = keys[(s >> 2) & 3]
            for p in range(n - 1, 0, -1):
                z = v[p - 1]
                y = v[p] = (
                    v[p] - ((((z >> 5) ^ (y << 2)) + ((y >> 3) ^ (z << 4))) ^ ((s ^ y) + (kp[p & 3] ^ z)))
                ) & MASK
            z = v[n - 1]
            y = v[0] = (v[0] - ((((z >> 5) ^ (y << 2)) + ((y >> 3) ^ (z << 4))) ^ ((s ^ y) + (kp[0] ^ z)))) & MASK
            s = (s - DELTA) & MASK
    else:
        s = 0
        z = v[n - 1]
        for _ in range(rounds):
            s = (s + DELTA) & MASK
            kp = keys[(s >> 2) & 3]
            for p in range(n - 1):
                y = v[p + 1]
                z = v[p] = (
                    v[p] + ((((z >> 5) ^ (y << 2)) + ((y >> 3) ^ (z << 4))) ^ ((s ^ y) + (kp[p & 3] ^ z)))
                ) & MASK
            y = v[0]
            z = v[n - 1] = (v[n - 1] + ((((z >> 5) ^ (y << 2)) + ((y >> 3) ^ (z << 4)))
                                        ^ ((s ^ y) + (kp[(n - 1) & 3] ^ z)))) & MASK
    return v


def _decrypt_3raw(data):
    value = struct.unpack_from('<Q', data, 4)[0]
    body = data[HEADER_3RAW:]
    words = _xxtea(list(struct.unpack('<%dI' % (len(body) // 4), body)), _key_3raw(value), True)
    size = words[-1]
    room = 4 * (len(words) - 1)
    if not room - 3 <= size <= room:
        raise J2bError('"2SAJ3raw": the XXTEA data does not end in its own length (another key?)')
    plain = struct.pack('<%dI' % (len(words) - 1), *words[:-1])[:size]
    if plain[:3] == b'BZh':
        try:
            plain = bz2.decompress(plain)
        except (OSError, ValueError) as e:
            raise J2bError('"2SAJ3raw": the bzip2 stream does not decompress (%s)' % e)
    return plain


RX_PRIMEIRO_NOME = re.compile(rb'[A-Za-z_][A-Za-z0-9_]{0,80}\x00')


def is_plain(data):
    if not is_j2b(data) or len(data) < 16:
        return False
    if data[:4] == MAGIC_PLAIN:
        return True
    count = struct.unpack_from('<I', data, 4)[0]
    return 0 < count < len(data) // 2 and RX_PRIMEIRO_NOME.match(data, 8) is not None


def decrypt(data):
    if not is_j2b(data):
        raise J2bError('not a j2b file (no "2SAJ" at the start)')
    if is_3raw(data):
        return _decrypt_3raw(data)
    if is_plain(data):
        return data[4:]
    seed1, seed2 = struct.unpack_from('<II', data, 4)
    return _xor(data[HEADER:], seed1, seed2)


def encrypt(plain, seed1, seed2):
    return MAGIC + struct.pack('<II', seed1 & MASK, seed2 & MASK) + _xor(plain, seed1 & MASK, seed2 & MASK)


def split(plain):
    if len(plain) < 4:
        raise J2bError('the plain data is empty')
    count = struct.unpack_from('<I', plain, 0)[0]
    at = 4
    for _ in range(count):
        at = plain.find(b'\0', at) + 1
        if at <= 0:
            raise J2bError('the name table says %d names and ends before that' % count)
    if (len(plain) - at) % 8:
        raise J2bError('%d bytes after the names: not a whole number of 8-byte instructions' % (len(plain) - at))
    return plain[4:at], count, plain[at:]


def join(names, count, code):
    return struct.pack('<I', count) + names + code


def hidden_calls(code):
    return sum(1 for m in re.finditer(b'(?=' + re.escape(_HIDDEN_CALL) + b')', code) if m.start() % 8 == 0)


def _make(code, count, names):
    body = struct.pack('<I', len(code) // 4) + code + struct.pack('<I', count) + names
    return kkwe.Bytecode(struct.pack('<I', len(body)) + body, kkwe.REVERSE_ORDER)


def bytecode(data, allow_hidden=False, reference=None, scripts=(), log=None):
    names, count, code = split(decrypt(data) if is_j2b(data) else data)
    hidden = 0 if allow_hidden else hidden_calls(code)
    if hidden and reference:
        from doctor.script import j2b_calls
        study = _make(code, count, names)
        mapping, report = j2b_calls.resolve(study, list(reference), log=log, scripts=scripts)
        if report['open']:
            raise J2bError('war3map.bin decrypts, but %d of its %d calls are hidden behind tokens; %d of the %d tokens '
                           'were resolved from the evidence, %d (%d calls) stay open (kk-plataforma.md 15.2.1)'
                           % (report['calls'], report['calls'], report['resolved'], report['tokens'], report['open'],
                              report['open_calls']))
        code = j2b_calls.restore(code, study.name_list, mapping, set(f[1] for f in study.functions()))
        hidden = hidden_calls(code)
    if hidden:
        raise J2bError('war3map.bin decrypts, but %d of its calls are hidden: opcode 36 with no register and a 32-bit '
                       'token in place of the function, which this tool cannot resolve yet (kk-plataforma.md 15.2)'
                       % hidden)
    return _make(code, count, names)
