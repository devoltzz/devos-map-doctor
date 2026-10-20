# Loads the native sector encoder (zopfli and zlib-ng) when it ships next to the program; without it the Python encoder runs.
import ctypes
import os
import subprocess
import sys
from array import array


HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, 'setor512.c')
THIRD_PARTY = os.path.normpath(os.path.join(HERE, '..', '..', 'terceiros'))
DEFAULT_OUTPUT = os.path.normpath(os.path.join(HERE, '..', 'cache', 'sector512_native'))
DLL = 'setor512.so' if sys.platform.startswith('linux') else 'setor512.dll'
WASM = 'setor512.wasm'
VERSION = 'zopfli=1.0.3|zlib-ng=2.2.4'
MODES = {'zopfli': 0, 'zlib9': 1}
ZOPFLI = ('blocksplitter.c', 'cache.c', 'deflate.c', 'hash.c', 'katajainen.c', 'lz77.c', 'squeeze.c', 'tree.c',
          'util.c', 'zlib_container.c', 'gzip_container.c', 'zopfli_lib.c')
ZLIB_NG = ('adler32.c', 'compress.c', 'crc32.c', 'crc32_braid_comb.c', 'deflate.c', 'deflate_fast.c', 'deflate_huff.c',
           'deflate_medium.c', 'deflate_quick.c', 'deflate_rle.c', 'deflate_slow.c', 'deflate_stored.c', 'functable.c',
           'insert_string.c', 'insert_string_roll.c', 'trees.c', 'zutil.c', 'cpu_features.c')
DEFS = ('-DZLIB_COMPAT', '-DWITH_ALL_FALLBACKS', '-DHAVE_ATTRIBUTE_ALIGNED')
_NAT = [None]


def sources(terceiros=THIRD_PARTY):
    zop = os.path.join(terceiros, 'zopfli', 'src', 'zopfli')
    zng = os.path.join(terceiros, 'zlib-ng')
    if not os.path.isfile(os.path.join(zop, 'zopfli.h')):
        raise SystemExit('sector512_native: no zopfli in %s' % zop)
    h = os.path.join(zng, 'zlib.h.in')
    if not os.path.isfile(h) or '#define ZLIBNG_VERSION "2.2.4"' not in open(h, encoding='utf-8').read():
        raise SystemExit(
            'sector512_native: the zlib-ng in %s is not 2.2.4 (the one of CPython 3.14: 2.3.3 gives other bytes)' % zng
        )
    cs = [SOURCE] + [os.path.join(zop, f) for f in ZOPFLI] + [os.path.join(zng, f) for f in ZLIB_NG]
    cs += sorted(os.path.join(zng, 'arch', 'generic', f) for f in os.listdir(os.path.join(zng, 'arch', 'generic'))
                 if f.endswith('.c'))
    return [c for c in cs if os.path.isfile(c)], [zop, zng]


def _headers(terceiros, folder):
    zng = os.path.join(terceiros, 'zlib-ng')
    os.makedirs(folder, exist_ok=True)
    for a, b in (('zlib.h.in', 'zlib.h'), ('zconf.h.in', 'zconf.h')):
        with open(os.path.join(zng, a), encoding='utf-8') as f:
            t = f.read().replace('@ZLIB_SYMBOL_PREFIX@', '')
        with open(os.path.join(folder, b), 'w', encoding='utf-8', newline='\n') as f:
            f.write(t)
    with open(os.path.join(zng, 'zlib_name_mangling.h.empty'), encoding='utf-8') as f:
        t = f.read()
    with open(os.path.join(folder, 'zlib_name_mangling.h'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(t)
    return folder


def compiles(output=DEFAULT_OUTPUT, terceiros=THIRD_PARTY, targets=('dll', 'only_problems', 'wasm')):
    cs, incs = sources(terceiros)
    inc = _headers(terceiros, os.path.join(output, '_inc'))
    zig = [sys.executable, '-m', 'ziglang', 'cc']
    chosen = {'dll': (os.path.join(output, 'setor512.dll'), ['-target', 'x86_64-windows-gnu'], ['-shared']),
              'only_problems': (os.path.join(output, 'setor512.so'), ['-target', 'x86_64-linux-gnu.2.17', '-fPIC',
                                                          '-DHAVE_POSIX_MEMALIGN'], ['-shared']),
              'wasm': (os.path.join(output, WASM), ['-target', 'wasm32-wasi', '-mexec-model=reactor',
                                                    '-DHAVE_POSIX_MEMALIGN'], [])}
    done = []
    for build_target in targets:
        dest, tgt, step_on = chosen[build_target]
        obj = os.path.join(output, '_obj_' + build_target)
        os.makedirs(obj, exist_ok=True)
        objs = []
        for i, c in enumerate(cs):
            o = os.path.join(obj, '%02d_%s.o' % (i, os.path.basename(c)))
            zop, zng = incs
            ics = ([zop] if c.startswith(zop) else [inc, zng] if c.startswith(zng) else [inc, zng, zop])
            r = subprocess.run(zig + tgt + ['-O2', '-c', '-o', o, c] + list(DEFS) + ['-I' + p for p in ics],
                               capture_output=True, text=True)
            if r.returncode:
                raise SystemExit(
                    'sector512_native: zig stopped at %s (%s)\n%s' % (os.path.basename(c), build_target, r.stderr)
                )
            objs.append(o)
        r = subprocess.run(zig + tgt + step_on + ['-O2', '-s', '-o', dest] + objs, capture_output=True, text=True)
        if r.returncode:
            raise SystemExit('sector512_native: zig did not link %s\n%s' % (dest, r.stderr))
        done.append(dest)
    return done


def _paths():
    out = [os.environ.get('SECTOR512_NATIVE') or '', os.path.join(HERE, DLL), os.path.join(DEFAULT_OUTPUT, DLL)]
    if getattr(sys, '_MEIPASS', None):
        out.append(os.path.join(sys._MEIPASS, DLL))
    return [p for p in out if p and p != '0']


def _through_js():
    try:
        import js
        from pyodide.ffi import to_js
    except ImportError:
        return None
    f = getattr(js, 's512Fatia', None)
    if f is None:
        return None

    def sector_slice(data_bytes, sector_bytes, margem, method):
        n = (len(data_bytes) + sector_bytes - 1) // sector_bytes
        if not n:
            return []
        r = f(to_js(bytes(data_bytes)), sector_bytes, margem, MODES[method])
        if r is None:
            return None
        b = r.to_bytes()
        lens = array('I')
        lens.frombytes(b[:4 * n])
        if sys.byteorder != 'little':
            lens.byteswap()
        out, pos = [], 4 * n
        for k in lens:
            out.append(b[pos:pos + k])
            pos += k
        return out
    return sector_slice


def _by_dll():
    if not (os.name == 'nt' or sys.platform.startswith('linux')):
        return None
    for p in _paths():
        if not os.path.isfile(p):
            continue
        try:
            dll = ctypes.CDLL(p)
            f = dll.s512_fatia
        except (OSError, AttributeError):
            continue
        f.argtypes = [ctypes.c_char_p, ctypes.c_size_t, ctypes.c_size_t, ctypes.c_int, ctypes.c_int, ctypes.c_void_p,
                      ctypes.c_void_p]
        f.restype = ctypes.c_long

        def sector_slice(data_bytes, sector_bytes, margem, method, _f=f):
            data_bytes = bytes(data_bytes)
            n = (len(data_bytes) + sector_bytes - 1) // sector_bytes
            if not n:
                return []
            out = ctypes.create_string_buffer(len(data_bytes))
            lens = array('I', bytes(4 * n))
            k = _f(data_bytes, len(data_bytes), sector_bytes, margem, MODES[method], out, lens.buffer_info()[0])
            if k != n:
                return None
            raw, pieces, pos = out.raw, [], 0
            for t in lens:
                pieces.append(raw[pos:pos + t])
                pos += t
            return pieces
        return sector_slice
    return None


def load_data():
    if os.environ.get('SECTOR512_NATIVE') == '0':
        return None
    if sys.platform == 'emscripten':
        return _through_js()
    if _NAT[0] is None:
        _NAT[0] = _by_dll() or False
    return _NAT[0] or None


def verify(sample_size=None):
    import zlib
    import zopfli.zlib as zz
    if 'zlib-ng' not in zlib.ZLIB_RUNTIME_VERSION:
        raise SystemExit('check: the zlib of this Python is %s, not the zlib-ng of the Windows CPython 3.14'
                         % zlib.ZLIB_RUNTIME_VERSION)
    sector_slice = load_data()
    if sector_slice is None:
        raise SystemExit('check: no native library (build it first)')
    if sample_size is None:
        sample_size = b''.join(open(os.path.join(HERE, f), 'rb').read() for f in sorted(os.listdir(HERE))
                               if f.endswith(('.py', '.c', '.j')))[:3 << 20]
    diffs = n = 0
    for method in ('zopfli', 'zlib9'):
        nat = sector_slice(sample_size, 512, 8, method)
        for i, part in enumerate(nat):
            s = sample_size[i * 512:(i + 1) * 512]
            z = zlib.compress(s, 9)
            if method == 'zopfli' and 1 + len(z) < len(s) + 8:
                z3 = zz.compress(s, numiterations=15, blocksplitting=False)
                if len(z3) < len(z):
                    z = z3
            python_result = b'\x02' + z if 1 + len(z) < len(s) else s
            diffs += python_result != part
            n += 1
    return n, diffs
