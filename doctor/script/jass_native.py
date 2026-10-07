# Runs the script checks in native code (native/jass_checks, Rust) when its library is there.
import ctypes
import json
import os
import sys


HERE = os.path.dirname(os.path.abspath(__file__))
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
                _LOADED_DLL[0] = dll
                break
    return _LOADED_DLL[0]


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
