# Puts back into the script the texts and numbers a platform DLL filled in at startup from a hidden Lua table (the script without texts of its own).
import base64
import itertools
import re

from doctor.script import lua_bytecode
from doctor.script import lua53_translate


RX_DECL_LINE = re.compile(r'(?m)^[ \t]*hashtable[ \t]+(\w+)[ \t]*=[ \t]*InitHashtable[ \t]*\([ \t]*\)')
RX_B64 = re.compile(rb'[A-Za-z0-9+/]+={0,2}')
LUA_B64 = b'G0x1YVM'
FLAG_EXISTS = 0x80000000
FLAG_ENCRYPT = 0x00010000
MAX_MIDDLE = 7
DLLS = ['wenhao_plugin.tga']


class TableError(ValueError):
    pass


def detect(body_text):
    for m in RX_DECL_LINE.finditer(body_text):
        ht = m.group(1)
        if ('LoadStr(%s,LoadInteger(%s,0,' % (ht, ht)) in body_text and ('SaveStr(%s,' % ht) not in body_text:
            return ht
    return None


def rx_reads(ht):
    return (re.compile(r'LoadStr\(%s,LoadInteger\(%s,0,(\d+)\),(\d+)\)' % (ht, ht)),
            re.compile(r'LoadInteger\(%s,0,(\d+)\)' % ht))


def chunks(file_):
    out = {}
    for bi in range(file_.h.block_n):
        fl = file_.blocks[bi][3] if bi < len(file_.blocks) else 0
        if not (fl & FLAG_EXISTS) or fl == 0xFFFFFFFF or fl & FLAG_ENCRYPT:
            continue
        try:
            d = file_.read(None, bi=bi)
        except Exception:
            continue
        if d and RX_B64.fullmatch(d):
            out[bi] = d
    return out


def _simulate(main, ht):
    lt = lua53_translate
    strs, ints = [], []
    for g in lua_bytecode.walk(main):
        k = g['consts']
        reg = {}

        def rk(c):
            return ('k', k[c & 0xFF]) if c & 0x100 else reg.get(c)
        code = g['code']
        for pc, ins in enumerate(code):
            op, a = ins & 0x3F, (ins >> 6) & 0xFF
            c, b, bx = (ins >> 14) & 0x1FF, (ins >> 23) & 0x1FF, (ins >> 14) & 0x3FFFF
            if op == lt.LOADK:
                reg[a] = ('k', k[bx])
            elif op == lt.LOADKX:
                reg[a] = ('k', k[code[pc + 1] >> 6]) if pc + 1 < len(code) else None
            elif op == lt.MOVE:
                reg[a] = reg.get(b)
            elif op == lt.GETTABUP:
                ch = rk(c)
                reg[a] = ('g', ch[1]) if ch and ch[0] == 'k' and isinstance(ch[1], bytes) else None
            elif op == lt.CALL:
                f = reg.get(a)
                fname = f[1] if f and f[0] == 'g' else None
                if fname in (b'SaveStr', b'SaveInteger', b'SaveReal', b'SaveBoolean'):
                    args = [reg.get(a + 1 + i) for i in range(max(b - 1, 0))]
                    if not args or args[0] != ('g', ht.encode()):
                        pass
                    elif fname not in (b'SaveStr', b'SaveInteger') or b != 5 or any(
                            x is None or x[0] != 'k' for x in args[1:]):
                        raise TableError('a write to %s that is not a constant (%s, pc %d)' % (ht, fname.decode(), pc))
                    else:
                        v = tuple(x[1] for x in args[1:])
                        (strs if fname == b'SaveStr' else ints).append(v)
                for r in range(a, a + 256):
                    reg.pop(r, None)
            elif op in (lt.JMP, lt.EQ, lt.LT, lt.LE, lt.TEST, lt.FORLOOP, lt.FORPREP, lt.TFORLOOP):
                reg.clear()
            elif op not in (lt.SETTABUP, lt.SETTABLE, lt.SETLIST, lt.RETURN, lt.EXTRAARG):
                reg[a] = None
    return strs, ints


def chunk(file_, ht):
    ps = chunks(file_)
    first_pieces = [bi for bi, d in ps.items() if d.startswith(LUA_B64)]
    if len(first_pieces) != 1:
        raise TableError('%d base64 piece(s) start with the Lua 5.3 header (1 expected)' % len(first_pieces))
    rest = [bi for bi in sorted(ps) if bi != first_pieces[0]]
    if not rest:
        candidates = [()]
        last = []
    else:
        with_padding = [bi for bi in rest if ps[bi].endswith(b'=')]
        short_record = min(len(ps[bi]) for bi in rest)
        short_names = [bi for bi in rest if len(ps[bi]) == short_record]
        last = with_padding if len(with_padding) == 1 else (short_names if len(short_names) == 1 else [])
        middle = [bi for bi in rest if bi not in last]
        if len(middle) > MAX_MIDDLE:
            raise TableError('%d pieces without a known order (the limit is %d)' % (len(middle), MAX_MIDDLE))
        candidates = itertools.permutations(middle)
    proven = []
    for perm in candidates:
        order = first_pieces + list(perm) + last
        try:
            data_bytes = base64.b64decode(b''.join(ps[bi] for bi in order), validate=True)
            main, whole = lua_bytecode.load(data_bytes)
        except Exception:
            continue
        if not whole:
            continue
        table = lua53_translate.opcode_table(main)
        if table is None:
            continue
        try:
            lua53_translate.translate(data_bytes, 'text_table')
            lua53_translate.renumber(main, table)
            strs, ints = _simulate(main, ht)
        except Exception:
            continue
        children = [f for _, f, _ in strs]
        if not strs or children != sorted(children):
            continue
        proven.append((data_bytes, order, strs, ints))
    if len(proven) != 1:
        raise TableError('%d arrangement(s) of the %d base64 pieces prove out (1 expected)' % (len(proven), len(ps)))
    return proven[0]


ESCAPES = {0x5C: b'\\\\', 0x22: b'\\"', 0x0A: b'\\n', 0x0D: b'\\r', 0x09: b'\\t'}


def literal(s):
    truncated = False
    while True:
        try:
            s.decode('utf-8')
            break
        except UnicodeDecodeError as e:
            if e.end < len(s) or e.start < len(s) - 3:
                raise TableError('text that is not UTF-8 in the middle: %r' % s[:60])
            s, truncated = s[:e.start], True
    return '"' + b''.join(ESCAPES.get(c, bytes([c])) for c in s).decode('latin-1') + '"', truncated


def whole(v):
    v &= 0xFFFFFFFF
    v = v - 0x100000000 if v >= 0x80000000 else v
    return '(%d)' % v if v < 0 else str(v)


def recover(body_text, ht, strs, ints):
    vi = {}
    for parent, n, v in ints:
        if parent != 0 or n in vi:
            raise TableError('SaveInteger(%s, %r, %r) outside the form (0, a unique n)' % (ht, parent, n))
        vi[n] = v
    vs = {}
    for parent, child, s in strs:
        if (parent, child) in vs:
            raise TableError('SaveStr(%s, %r, %r) repeated' % (ht, parent, child))
        vs[(parent, child)] = s
    rs, ri = rx_reads(ht)
    info = {'hashtable': ht, 'texts': len(vs), 'integers': len(vi), 'str_swaps': 0, 'int_swaps': 0, 'cut_texts': 0}
    missing = []

    def swap_str(m):
        hash_key = (vi.get(int(m.group(1))), int(m.group(2)))
        if hash_key not in vs:
            missing.append(m.group(0))
            return m.group(0)
        lit, truncated = literal(vs[hash_key])
        info['str_swaps'] += 1
        info['cut_texts'] += truncated
        return lit

    def swap_int(m):
        n = int(m.group(1))
        if n not in vi:
            missing.append(m.group(0))
            return m.group(0)
        info['int_swaps'] += 1
        return whole(vi[n])
    t = rs.sub(swap_str, body_text)
    t = ri.sub(swap_int, t)
    if missing:
        raise TableError('%d read(s) of %s with no value in the table: %s' % (len(missing), ht, missing[:3]))
    leftover = len(re.findall(r'\b%s\b' % ht, t))
    if leftover != 1:
        raise TableError(
            '%s is left %d time(s) in the script after the swap (1 expected: the declaration)' % (ht, leftover)
        )
    return t, info


def prepare(body_text, map_path):
    ht = detect(body_text)
    if not ht:
        return body_text, None
    from doctor.mpq import mpqread
    _, order, strs, ints = chunk(mpqread.Archive(map_path), ht)
    t, info = recover(body_text, ht, strs, ints)
    info['chunks'] = order
    return t, info


def report_data(info):
    if info:
        print(
            'table %s: %d text(s) and %d integer(s) from the Lua bytecode (pieces %s); %d LoadStr and %d LoadInteger replaced '
            'by the literal; %d text(s) cut in the middle of a character'
            % (
                info['hashtable'],
                info['texts'],
                info['integers'],
                info['chunks'],
                info['str_swaps'],
                info['int_swaps'],
                info['cut_texts'],
            )
        )
