# Runs the script checks in native code (native/jass_checks, Rust) when its library is there.
import ctypes
import json
import os
import shutil
import subprocess
import sys


HERE = os.path.dirname(os.path.abspath(__file__))
CRATE = os.path.normpath(os.path.join(HERE, '..', 'native', 'jass_checks'))
DLL = 'jass_checks.so' if sys.platform.startswith('linux') else 'jass_checks.dll'
_LOADED_DLL = [None]


def _paths():
    out = [os.environ.get('JASS_NATIVE') or '', os.path.join(HERE, DLL),
           os.path.normpath(os.path.join(HERE, '..', 'cache', 'jass_checks', DLL))]
    if getattr(sys, '_MEIPASS', None):
        out.append(os.path.join(sys._MEIPASS, DLL))
    return [p for p in out if p and p != '0']


def _dll():
    if _LOADED_DLL[0] is None:
        _LOADED_DLL[0] = False
        if os.name == 'nt' or sys.platform.startswith('linux'):
            for p in _paths():
                if not os.path.isfile(p):
                    continue
                try:
                    dll = ctypes.CDLL(p)
                    dll.jass_checks.argtypes = [ctypes.c_char_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_void_p),
                                                ctypes.POINTER(ctypes.c_size_t)]
                    dll.jass_checks.restype = ctypes.c_int
                    dll.jass_free.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
                    dll.jass_free.restype = None
                except (OSError, AttributeError):
                    continue
                try:
                    dll.mpq_name_search.argtypes = [ctypes.c_char_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint64),
                                                    ctypes.c_size_t, ctypes.POINTER(ctypes.c_void_p),
                                                    ctypes.POINTER(ctypes.c_size_t)]
                    dll.mpq_name_search.restype = ctypes.c_int
                except AttributeError:
                    pass
                _LOADED_DLL[0] = dll
                break
    return _LOADED_DLL[0]


def load_names():
    if os.environ.get('JASS_NATIVE') == '0' or sys.platform == 'emscripten':
        return None
    dll = _dll()
    if not dll or not hasattr(dll, 'mpq_name_search') or dll.mpq_name_search.restype is not ctypes.c_int:
        return None
    import struct

    def listing(item_entries, out):
        out.append(struct.pack('<I', len(item_entries)))
        for it in item_entries:
            if isinstance(it, (bytes, bytearray)):
                out.append(b'\x80' + struct.pack('<I', len(it)) + bytes(it))
            else:
                flags = 0
                for r in it:
                    flags |= 1 << r
                out.append(bytes([flags]))
                for r in sorted(it):
                    out.append(struct.pack('<I', len(it[r])) + bytes(it[r]))

    def lookup(folders, name_list, exts, pairs, _f=dll.mpq_name_search, _free=dll.jass_free):
        pieces = []
        for item_entries in (folders, name_list, exts):
            listing(item_entries, pieces)
        buf = b''.join(pieces)
        keys = sorted(set((h1 << 32) | h2 for h1, h2 in pairs))
        arr = (ctypes.c_uint64 * len(keys))(*keys)
        p, n = ctypes.c_void_p(), ctypes.c_size_t()
        if _f(buf, len(buf), arr, len(keys), ctypes.byref(p), ctypes.byref(n)) != 0:
            return None
        try:
            raw = ctypes.string_at(p.value, n.value * 16) if n.value else b''
        finally:
            _free(p, n.value * 16)
        vals = struct.unpack('<%dI' % (4 * n.value), raw)
        return [tuple(vals[i:i + 4]) for i in range(0, len(vals), 4)]
    return lookup


def load_canonical():
    if os.environ.get('JASS_NATIVE') == '0' or sys.platform == 'emscripten':
        return None
    dll = _dll()
    if not dll or not hasattr(dll, 'gui_canonical') or not hasattr(dll, 'canon_jass_reference'):
        return None
    vp, sz = ctypes.c_void_p, ctypes.c_size_t
    if dll.gui_canonical.restype is not ctypes.c_int:
        dll.gui_canonical.argtypes = [ctypes.c_char_p, sz, ctypes.c_int, ctypes.c_int, ctypes.c_char_p, sz,
                                      ctypes.POINTER(vp), ctypes.POINTER(sz)]
        dll.gui_canonical.restype = ctypes.c_int
        dll.canon_jass_reference.argtypes = [ctypes.c_char_p, sz, ctypes.c_char_p, sz]
        dll.canon_jass_reference.restype = ctypes.c_int
    is_ready = [False]

    def canon(body_text, lang, inline, self_name, _f=dll.gui_canonical, _free=dll.jass_free):
        if lang != 'lua' and not is_ready[0]:
            from doctor.triggers import triggerdata
            c, b = (triggerdata.game_script(n).encode('utf-8', 'surrogateescape') for n in ('common.j', 'blizzard.j'))
            if dll.canon_jass_reference(c, len(c), b, len(b)) != 0:
                return None
            is_ready[0] = True
        t = body_text.encode('utf-8', 'surrogateescape')
        s = None if self_name is None else self_name.encode('utf-8', 'surrogateescape')
        p, n = vp(), sz()
        if _f(t, len(t), 1 if lang == 'lua' else 0, 1 if inline else 0, s, len(s or b''), ctypes.byref(p),
              ctypes.byref(n)) != 0:
            return None
        try:
            return ctypes.string_at(p.value, n.value).decode('utf-8', 'surrogateescape')
        finally:
            _free(p, n.value)
    return canon


def load_standard():
    if os.environ.get('JASS_NATIVE') == '0' or sys.platform == 'emscripten':
        return None
    dll = _dll()
    if not dll or not hasattr(dll, 'jass_standard_globals') or not hasattr(dll, 'jass_game_calls'):
        return None
    vp, sz = ctypes.c_void_p, ctypes.c_size_t
    if dll.jass_game_calls.restype is not ctypes.c_int:
        dll.jass_standard_globals.argtypes = [ctypes.c_char_p, sz, ctypes.POINTER(vp), ctypes.POINTER(sz)]
        dll.jass_standard_globals.restype = ctypes.c_int
        dll.jass_game_calls.argtypes = [ctypes.c_char_p, sz, ctypes.c_char_p, sz, ctypes.POINTER(vp),
                                        ctypes.POINTER(sz)]
        dll.jass_game_calls.restype = ctypes.c_int
    import struct

    def lists_out(buf, k, how_many):
        out = []
        for _q in range(how_many):
            n = struct.unpack_from('<I', buf, k)[0]
            k += 4
            item_entries = []
            for _i in range(n):
                m = struct.unpack_from('<I', buf, k)[0]
                item_entries.append(bytes(buf[k + 4:k + 4 + m]))
                k += 4 + m
            out.append(item_entries)
        return out, k

    def receive(f, *args):
        p, n = vp(), sz()
        if f(*(args + (ctypes.byref(p), ctypes.byref(n)))) != 0:
            return None
        try:
            return ctypes.string_at(p.value, n.value)
        finally:
            dll.jass_free(p, n.value)

    def globals_block(data_bytes):
        buf = receive(dll.jass_standard_globals, data_bytes, len(data_bytes))
        return None if buf is None else tuple(lists_out(buf, 0, 2)[0])

    def calls(data_bytes, name_list):
        table = b''.join(a + b'\t' + b + b'\n' for a, b in name_list.items())
        buf = receive(dll.jass_game_calls, data_bytes, len(data_bytes), table, len(table))
        if buf is None:
            return None
        (in_use,), k = lists_out(buf, 4, 1)
        return buf[k:], struct.unpack_from('<I', buf, 0)[0], set(in_use)
    return globals_block, calls


def load_data():
    if os.environ.get('JASS_NATIVE') == '0' or sys.platform == 'emscripten':
        return None
    dll = _dll()
    if not dll:
        return None

    def run_checks(body_text, _f=dll.jass_checks, _free=dll.jass_free):
        b = body_text.encode('utf-8', 'surrogatepass') if isinstance(body_text, str) else bytes(body_text)
        p, n = ctypes.c_void_p(), ctypes.c_size_t()
        if _f(b, len(b), ctypes.byref(p), ctypes.byref(n)) != 0:
            return None
        try:
            return json.loads(ctypes.string_at(p.value, n.value).decode('utf-8'))
        finally:
            _free(p, n.value)
    return run_checks


def load_lexer():
    if os.environ.get('JASS_NATIVE') == '0' or sys.platform == 'emscripten':
        return None
    dll = _dll()
    if not dll or not hasattr(dll, 'jass_lex'):
        return None
    vp, sz = ctypes.c_void_p, ctypes.c_size_t
    if dll.jass_lex.restype is not ctypes.c_int:
        dll.jass_lex.argtypes = [ctypes.c_char_p, sz, ctypes.c_int, ctypes.POINTER(vp), ctypes.POINTER(sz)]
        dll.jass_lex.restype = ctypes.c_int
    import array

    def lex(body_text, method, _f=dll.jass_lex, _free=dll.jass_free):
        b = body_text.encode('utf-32-le', 'surrogatepass')
        p, n = vp(), sz()
        if _f(b, len(b), method, ctypes.byref(p), ctypes.byref(n)) != 0:
            return None
        try:
            buf = ctypes.string_at(p.value, n.value) if n.value else b''
        finally:
            _free(p, n.value)
        if method == 0:
            k = int.from_bytes(buf[:4], 'little')
            ends = array.array('I')
            ends.frombytes(buf[4 + k:4 + 5 * k])
            if sys.byteorder != 'little':
                ends.byteswap()
            return buf[4:4 + k], ends
        quads = array.array('I')
        quads.frombytes(buf)
        if sys.byteorder != 'little':
            quads.byteswap()
        return quads
    return lex


def _cargo():
    c = shutil.which('cargo')
    if c:
        return c
    c = os.path.join(os.path.expanduser('~'), '.cargo', 'bin', 'cargo' + ('.exe' if os.name == 'nt' else ''))
    if os.path.isfile(c):
        return c
    raise SystemExit('jass_native: cargo not found (Rust: https://rustup.rs)')


def _linux_linker(folder):
    os.makedirs(folder, exist_ok=True)
    cmd = os.path.join(folder, 'zig_linux_cc.cmd')
    with open(cmd, 'w', encoding='ascii', newline='\r\n') as f:
        f.write('@echo off\n"%s" -m ziglang cc -target x86_64-linux-gnu.2.17 %%*\n' % sys.executable)
    return cmd


def compiles(output, linux=False):
    os.makedirs(output, exist_ok=True)
    target_dir = os.path.normpath(os.path.join(HERE, '..', 'cache', 'native_target'))
    env = dict(os.environ, CARGO_TARGET_DIR=target_dir)
    done = []
    targets = [(None, 'jass_checks.dll' if os.name == 'nt' else 'libjass_checks.so', DLL)]
    if linux and os.name == 'nt':
        targets.append(('x86_64-unknown-linux-gnu', 'libjass_checks.so', 'jass_checks.so'))
        env['CARGO_TARGET_X86_64_UNKNOWN_LINUX_GNU_LINKER'] = _linux_linker(os.path.join(target_dir, 'linker'))
    for tgt, fname, dest in targets:
        cmd = [_cargo(), 'build', '--release', '--manifest-path', os.path.join(CRATE, 'Cargo.toml')]
        if tgt:
            cmd += ['--target', tgt]
        r = subprocess.run(cmd, env=env, capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode:
            raise SystemExit('jass_native: cargo stopped (%s)\n%s%s' % (tgt or 'host', r.stdout, r.stderr))
        origin = os.path.join(target_dir, *([tgt] if tgt else []), 'release', fname)
        shutil.copyfile(origin, os.path.join(output, dest))
        done.append(os.path.join(output, dest))
    return done


def _scripts(paths):
    for c in paths:
        if os.path.isdir(c):
            for d, _ds, fs in os.walk(c):
                for f in sorted(fs):
                    if f.lower().endswith('.j'):
                        yield os.path.join(d, f)
        else:
            yield c


def verify(paths):
    import time
    from doctor.script import jass_ast
    from doctor.script import script_checks
    run_checks = load_data()
    if run_checks is None:
        raise SystemExit('jass_native: no library (build it first)')
    bad_ones, python_time, tn = 0, 0.0, 0.0
    for p in _scripts(paths):
        body_text = jass_ast.read_script(p) if p.lower().endswith('.j') else open(p, encoding='utf-8').read()
        t = time.perf_counter()
        python_result = script_checks.check_text(body_text, native=False)
        python_time += time.perf_counter() - t
        t = time.perf_counter()
        native_result = run_checks(body_text)
        tn += time.perf_counter() - t
        python_result.pop('lines', None)
        python_result.pop('language', None)
        if native_result is None and 'error' in python_result:
            continue
        if native_result != python_result:
            bad_ones += 1
            print('DIFFERS %s' % p)
            for k in sorted(set(python_result) | set(native_result or {})):
                if (native_result or {}).get(k) != python_result.get(k):
                    print('  %s: python %s\n  %s  rust   %s' % (k, json.dumps(python_result.get(k))[:300], ' ' * len(k),
                                                                 json.dumps((native_result or {}).get(k))[:300]))
    print(
        'Python %.2f s, Rust %.2f s (%.0fx); differences %d' % (python_time, tn, python_time / max(tn, 1e-9), bad_ones)
    )
    return bad_ones

