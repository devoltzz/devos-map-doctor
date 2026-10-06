# The MPQ hot loops in native code (mpqcrypt.c: a DLL in the exe, WebAssembly on the site): the decryption, the key search of nameless files, the sound sectors.
import ctypes
import os
import sys
from array import array


HERE = os.path.dirname(os.path.abspath(__file__))
DLL = 'mpqcrypt.dll'
_LOADED_DLL = [None]


def _paths():
    out = [os.environ.get('MPQCRYPT') or '', os.path.join(HERE, DLL),
           os.path.normpath(os.path.join(HERE, '..', 'cache', 'mpqcrypt', DLL))]
    if getattr(sys, '_MEIPASS', None):
        out.append(os.path.join(sys._MEIPASS, DLL))
    return [p for p in out if p]


def _disabled():
    return os.environ.get('MPQCRYPT') == '0'


def _js():
    if sys.platform != 'emscripten':
        return None
    try:
        import js
        from pyodide.ffi import to_js
    except ImportError:
        return None
    return js, to_js


def _through_js():
    j = _js()
    f = getattr(j[0], 'mpqDecrypt', None) if j else None
    if f is None:
        return None
    to_js = j[1]

    def decrypt(data_bytes, hash_key):
        return f(to_js(bytes(data_bytes)), hash_key & 0xFFFFFFFF).to_bytes()
    return decrypt


def _dll():
    if _LOADED_DLL[0] is None:
        _LOADED_DLL[0] = False
        if os.name == 'nt':
            for p in _paths():
                if not os.path.isfile(p):
                    continue
                try:
                    dll = ctypes.CDLL(p)
                    dll.mpq_decrypt.argtypes = [ctypes.c_char_p, ctypes.c_size_t, ctypes.c_uint32]
                    dll.mpq_decrypt.restype = None
                except (OSError, AttributeError):
                    continue
                _LOADED_DLL[0] = dll
                break
    return _LOADED_DLL[0]


def load_data():
    if _disabled():
        return None
    if sys.platform == 'emscripten':
        return _through_js()
    dll = _dll()
    if not dll:
        return None

    def decrypt(data_bytes, hash_key, _f=dll.mpq_decrypt):
        data_bytes = bytes(data_bytes)
        buf = ctypes.create_string_buffer(data_bytes, len(data_bytes))
        _f(buf, len(data_bytes), hash_key & 0xFFFFFFFF)
        return buf.raw
    return decrypt


def _keys_through_js():
    j = _js()
    f = getattr(j[0], 'mpqKeys', None) if j else None
    if f is None:
        return None

    def key_candidates(enc0, enc1, d0):
        v = array('I')
        v.frombytes(f(enc0, enc1, d0).to_bytes())
        return list(zip(v[0::2], v[1::2]))
    return key_candidates


def load_keys():
    if _disabled():
        return None
    if sys.platform == 'emscripten':
        return _keys_through_js()
    dll = _dll()
    if not dll:
        return None
    try:
        f = dll.mpq_key_candidates
    except AttributeError:
        return None
    f.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32)]
    f.restype = ctypes.c_int
    pair = ctypes.c_uint32 * 512

    def key_candidates(enc0, enc1, d0):
        out = pair()
        n = f(enc0, enc1, d0, out)
        return list(zip(out[0:2 * n:2], out[1:2 * n:2]))
    return key_candidates


def _sound_through_js():
    j = _js()
    fh, fa = (getattr(j[0], 'mpqHuffman', None), getattr(j[0], 'mpqAdpcm', None)) if j else (None, None)
    if fh is None or fa is None:
        return None
    to_js = j[1]

    def huffman(data_bytes, cap):
        r = fh(to_js(bytes(data_bytes)), cap)
        return None if r is None else r.to_bytes()

    def adpcm(data_bytes, channels, cap):
        r = fa(to_js(bytes(data_bytes)), channels, cap)
        return None if r is None else r.to_bytes()
    return huffman, adpcm


def load_sound():
    if _disabled():
        return None
    if sys.platform == 'emscripten':
        return _sound_through_js()
    dll = _dll()
    if not dll:
        return None
    try:
        fh, fa = dll.mpq_huffman, dll.mpq_adpcm
    except AttributeError:
        return None
    fh.argtypes = [ctypes.c_char_p, ctypes.c_size_t, ctypes.c_char_p, ctypes.c_size_t]
    fa.argtypes = [ctypes.c_char_p, ctypes.c_size_t, ctypes.c_int, ctypes.c_char_p, ctypes.c_size_t]
    fh.restype = fa.restype = ctypes.c_int

    def huffman(data_bytes, cap):
        data_bytes = bytes(data_bytes)
        out = ctypes.create_string_buffer(cap)
        r = fh(data_bytes, len(data_bytes), out, cap)
        return None if r < 0 else out.raw[:r]

    def adpcm(data_bytes, channels, cap):
        data_bytes = bytes(data_bytes)
        out = ctypes.create_string_buffer(cap)
        r = fa(data_bytes, len(data_bytes), channels, out, cap)
        return None if r < 0 else out.raw[:r]
    return huffman, adpcm

