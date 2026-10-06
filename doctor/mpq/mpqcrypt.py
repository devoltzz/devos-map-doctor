# MPQ decryption in native code (mpqcrypt.c: a DLL in the exe, WebAssembly on the site).
import ctypes
import os
import sys


HERE = os.path.dirname(os.path.abspath(__file__))
DLL = 'mpqcrypt.dll'
def _paths():
    out = [os.environ.get('MPQCRYPT') or '', os.path.join(HERE, DLL),
           os.path.normpath(os.path.join(HERE, '..', 'cache', 'mpqcrypt', DLL))]
    if getattr(sys, '_MEIPASS', None):
        out.append(os.path.join(sys._MEIPASS, DLL))
    return [p for p in out if p]


def _through_js():
    try:
        import js
        from pyodide.ffi import to_js
    except ImportError:
        return None
    f = getattr(js, 'mpqDecrypt', None)
    if f is None:
        return None

    def decrypt(data_bytes, hash_key):
        return f(to_js(bytes(data_bytes)), hash_key & 0xFFFFFFFF).to_bytes()
    return decrypt


def load_data():
    if os.environ.get('MPQCRYPT') == '0':
        return None
    if sys.platform == 'emscripten':
        return _through_js()
    if os.name != 'nt':
        return None
    for p in _paths():
        if not os.path.isfile(p):
            continue
        try:
            dll = ctypes.CDLL(p)
            dll.mpq_decrypt.argtypes = [ctypes.c_char_p, ctypes.c_size_t, ctypes.c_uint32]
            dll.mpq_decrypt.restype = None
        except (OSError, AttributeError):
            continue

        def decrypt(data_bytes, hash_key, _f=dll.mpq_decrypt):
            data_bytes = bytes(data_bytes)
            buf = ctypes.create_string_buffer(data_bytes, len(data_bytes))
            _f(buf, len(data_bytes), hash_key & 0xFFFFFFFF)
            return buf.raw
        return decrypt
    return None

