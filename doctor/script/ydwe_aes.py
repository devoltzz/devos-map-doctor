# The encrypted Lua modules of a YDWE Lua engine map (base64 of AES-128-ECB): the key chain found in the map itself.
import base64
import hashlib
import re



ROOTS = (b'smz#@$#%!@)%!(*!_$!&',)
B64 = frozenset(b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=\r\n')
RX_KEY = re.compile(rb'^[0-9A-Za-z]{8,31}$')
KEY_SIZE = 44


def _aes(hash_key):
    from Crypto.Cipher import AES
    return AES.new(hashlib.md5(hash_key).digest(), AES.MODE_ECB)


def _b64(d):
    t = bytes(d).strip()
    if len(t) < 24 or not all(c in B64 for c in t[:512]) or not all(c in B64 for c in t[-64:]):
        return None
    try:
        ct = base64.b64decode(t.replace(b'\r', b'').replace(b'\n', b''), validate=True)
    except ValueError:
        return None
    return ct if ct and len(ct) % 16 == 0 else None


def looks_ciphered(d):
    return _b64(d) is not None


def _key_of(d, hash_key):
    ct = _b64(d)
    if ct is None or len(ct) != 32:
        return None
    pt = _aes(hash_key).decrypt(ct).rstrip(b'\0')
    return pt if RX_KEY.match(pt) else None


def _shape_ok(p):
    if p[:4] == b'\x1bLua':
        return True
    if b'\x00' in p[:4096]:
        return False
    try:
        p[:4096].decode('utf-8')
    except UnicodeDecodeError as e:
        if e.start < len(p[:4096]) - 3:
            try:
                p[:4096].decode('gbk')
            except UnicodeDecodeError:
                return False
    return True


def _open(ct, hash_key):
    pt = _aes(hash_key).decrypt(ct)
    n = int.from_bytes(pt[:4], 'little')
    if n > len(pt) - 4 or len(pt) - 4 - n >= 16 + 4 or pt[4 + n:].strip(b'\0'):
        return None
    return pt[4:4 + n]


def keys(blobs, roots=ROOTS):
    known = list(roots)
    short_names = [d for d in blobs.values() if len(bytes(d).strip()) == KEY_SIZE]
    changed = True
    while changed:
        changed = False
        for d in short_names:
            for k in list(known):
                n = _key_of(d, k)
                if n and n not in known:
                    known.append(n)
                    changed = True
    return known


def decipher(d, ks):
    ct = _b64(d)
    if ct is None or len(ct) < 32:
        return None, None
    for k in reversed(ks):
        p = _open(ct, k)
        if p is not None and _shape_ok(p):
            return p, k
    return None, None


def map_own(a, block_list=None, log=None):
    from doctor.mpq import mpqnames
    if block_list is None:
        block_list = {}
        for bi in a.pointed_blocks():
            d = mpqnames.read_unnamed(a, bi, whole=True)
            if d and looks_ciphered(d):
                block_list[bi] = d
    blobs = dict((bi, d) for bi, d in block_list.items() if looks_ciphered(d))
    out = {'keys': [], 'lua_modules': {}}
    if not blobs:
        return out
    ks = keys(blobs)
    out['keys'] = ks
    for bi, d in blobs.items():
        if len(bytes(d).strip()) == KEY_SIZE:
            continue
        p, _k = decipher(d, ks)
        if p is not None:
            out['lua_modules'][bi] = p
    if log:
        log('   ydwe_aes: %d key(s) in the chain, %d of %d ciphered blocks opened'
            % (len(ks), len(out['lua_modules']), len(blobs)))
    return out

