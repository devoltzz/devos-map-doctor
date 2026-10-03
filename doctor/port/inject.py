# Puts the port layer inside the map script and checks that nothing of the map was lost.
import hashlib
import os
import re
import sys

from doctor.port import layer as _layer


ROOT = None
J = None
DEFAULT_LAYER = None
EXTRACT = None
REF = None
MAP_NATIVES = None
PROBE_NAMES = ('DB_slk_get', 'DzFrameSetText', 'EXSetEffectSize')
NO_STUB = set()
LAYER_GLOBALS_ON_TOP = False

MINI = {
    'natives': (b'//@@CAMADA_INLINE_NATIVES_INI', b'//@@CAMADA_INLINE_NATIVES_FIM'),
    'globals_block': (b'//@@CAMADA_INLINE_GLOBALS_INI', b'//@@CAMADA_INLINE_GLOBALS_FIM'),
    'functions': (b'//@@CAMADA_INLINE_FUNCTIONS_INI', b'//@@CAMADA_INLINE_FUNCTIONS_FIM'),
}
NOTA = {
    'natives': b'// [rota JASS inline] as 2 nativas do MOTOR que a referencia 3.0 nao publica.',
    'globals_block': b'// [rota JASS inline] as variaveis da NOSSA camada, fundidas no unico `globals`.',
    'functions': b'// [rota JASS inline] as funcoes da NOSSA camada, antes de qualquer funcao da autora.',
}

RX_NATIVE = re.compile(rb'^\s*(?:constant\s+)?native\s+([A-Za-z_]\w*)\s+takes\s')
RX_FUNCTION = re.compile(rb'^\s*function\s+([A-Za-z_]\w*)\s+takes\s')
RX_FUNC_DEF_B = re.compile(rb'^\s*function\s+([A-Za-z_]\w*)\s+takes\s')

_RX_GLOBAL_REF = [None]


def configure_layer(root, ref=None, j=None, layer_file=None, extract=None, map_natives=None, probes=None, no_stub=(),
                    layer_globals_on_top=False):
    global ROOT, J, DEFAULT_LAYER, EXTRACT, REF, MAP_NATIVES, PROBE_NAMES, NO_STUB, LAYER_GLOBALS_ON_TOP
    NO_STUB = set(no_stub or ())
    LAYER_GLOBALS_ON_TOP = bool(layer_globals_on_top)
    ROOT = os.path.abspath(root)
    J = j or os.path.join(ROOT, 'scripts', 'war3map.j')
    DEFAULT_LAYER = layer_file or os.path.join(ROOT, 'port', 'out', 'camada_nossa.j')
    EXTRACT = extract or os.path.join(ROOT, 'port', 'extract', 'war3map.j')
    REF = ref or _layer.REF_30
    MAP_NATIVES = map_natives or os.path.join(ROOT, 'port', 'compat', 'part_0_map_natives.j')
    if probes is not None:
        PROBE_NAMES = tuple(probes)
    _RX_GLOBAL_REF[0] = None


def _demand_check():
    if ROOT is None:
        raise SystemExit('inject: call configura(root) first (or --raiz= on the command line)')


def rx_global_ref():
    _demand_check()
    if _RX_GLOBAL_REF[0] is None:
        comment = open(os.path.join(REF, 'common.j'), 'rb').read().decode('latin-1')
        types = set(re.findall(r'(?m)^type\s+([A-Za-z_]\w*)\s+extends', comment))
        types |= {'integer', 'real', 'boolean', 'string', 'code', 'handle'}
        _RX_GLOBAL_REF[0] = re.compile(
            r'^\s*(?:constant\s+)?(?:' + '|'.join(sorted(types)) +
            r')\s+(?:array\s+)?[A-Za-z_]\w*\s*(?:=[^\r\n]*)?$')
    return _RX_GLOBAL_REF[0]


def sha(b):
    return hashlib.sha256(b).hexdigest()


def arg(fname, default_value=None, argv=None):
    for a in (sys.argv if argv is None else argv):
        if a.startswith('--' + fname + '='):
            return a[len(fname) + 3:]
    return default_value


def line_list(b):
    return b.splitlines(keepends=True)


def no_end(line):
    return line.rstrip(b'\r\n')


def names_of(rx, ls):
    return [m.group(1).decode('latin-1') for m in (rx.match(no_end(line)) for line in ls) if m]


def read_layer(file_path, failures):
    if not os.path.isfile(file_path):
        failures.append('layer not found: %s' % file_path)
        return None
    b = open(file_path, 'rb').read()
    ls = line_list(b)
    pos = {}
    for hash_key, (begin, end_pos) in _layer.MARKS.items():
        i = [k for k, line in enumerate(ls) if no_end(line) == begin.encode('latin-1')]
        f = [k for k, line in enumerate(ls) if no_end(line) == end_pos.encode('latin-1')]
        if len(i) != 1 or len(f) != 1:
            failures.append('layer: marker %s appears %d time(s) and %s %d (expected 1 and 1)'
                            % (begin, len(i), end_pos, len(f)))
            return None
        if f[0] <= i[0]:
            failures.append('layer: the end marker of %s comes BEFORE the start one' % hash_key)
            return None
        pos[hash_key] = (i[0], f[0])
    if not (pos['natives'][0] < pos['globals_block'][0] < pos['functions'][0]):
        failures.append('layer: the sections are not in the order natives < globals < functions: %s' % pos)
        return None
    sec = {}
    for hash_key, (i, f) in pos.items():
        body = [line for line in ls[i + 1:f]]
        while body and not no_end(body[-1]).strip():
            body.pop()
        sec[hash_key] = body
    return sec


def engine_names():
    _demand_check()

    def read_data(p):
        return open(p, 'rb').read().decode('latin-1')
    d = set(re.findall(r'(?m)^\s*(?:constant\s+)?(?:native|function)\s+([A-Za-z_]\w*)\s+takes',
                       read_data(os.path.join(REF, 'common.j'))))
    d |= set(re.findall(r'(?m)^\s*(?:constant\s+)?(?:native|function)\s+([A-Za-z_]\w*)\s+takes',
                        read_data(os.path.join(REF, 'blizzard.j'))))
    return d


def global_names(ls):
    outside = []
    for line in ls:
        s = no_end(line).decode('latin-1')
        if s.strip().startswith('//') or not s.strip():
            continue
        no_comment = s.split('//')[0].rstrip() if '//' in s else s
        m = rx_global_ref().match(no_comment)
        if not m:
            outside.append((s, 'does not match a variable declaration'))
            continue
        outside.append((s, None))
    name_list = set()
    for s, err in outside:
        if err:
            continue
        m = re.match(r'\s*(?:constant\s+)?\w+\s+(?:array\s+)?([A-Za-z_]\w*)', s)
        if m:
            name_list.add(m.group(1))
    return name_list, [s for s, e in outside if e]


def strip_injection(b, failures):
    ls = line_list(b)
    matches = {}
    for hash_key, (begin, end_pos) in MINI.items():
        i = [k for k, line in enumerate(ls) if no_end(line) == begin]
        f = [k for k, line in enumerate(ls) if no_end(line) == end_pos]
        if len(i) > 1 or len(f) > 1:
            failures.append('injection marker %s repeated (%d start, %d end)'
                            % (hash_key, len(i), len(f)))
            return None, 0, 0
        if len(i) != len(f):
            failures.append('injection marker %s unpaired (%d start, %d end)'
                            % (hash_key, len(i), len(f)))
            return None, 0, 0
        matches[hash_key] = (i, f)
    ranges = []
    for hash_key, (i, f) in matches.items():
        if i:
            ranges.append((i[0], f[0], hash_key))
    ranges.sort()
    n_rem = 0
    for begin, end_pos, hash_key in reversed(ranges):
        extra = end_pos + 1 if end_pos + 1 < len(ls) and not no_end(ls[end_pos + 1]).strip() else end_pos
        n_rem += extra - begin + 1
        del ls[begin:extra + 1]
    return b''.join(ls), n_rem, len(ranges)


def applies(map_bytes, sec, failures):
    _demand_check()
    ls = line_list(map_bytes)
    line_end = b'\r\n' if map_bytes.count(b'\r\n') * 2 > map_bytes.count(b'\n') else b'\n'

    ig = [k for k, line in enumerate(ls) if no_end(line).strip() == b'globals']
    ie = [k for k, line in enumerate(ls) if no_end(line).strip() == b'endglobals']
    if len(ig) != 1:
        failures.append('%d `globals` lines in war3map.j (expected 1)' % len(ig))
    if len(ie) != 1:
        failures.append('%d `endglobals` lines in war3map.j (expected 1)' % len(ie))
    if len(ig) != 1 or len(ie) != 1:
        return None, {}
    ig, ie = ig[0], ie[0]
    if not ig < ie:
        failures.append('`globals` (line %d) after the `endglobals` (line %d)' % (ig + 1, ie + 1))
        return None, {}
    ifx = [k for k, line in enumerate(ls) if RX_FUNCTION.match(no_end(line))]
    if not ifx:
        failures.append('could not find ANY `function` in war3map.j')
        return None, {}
    ifx = ifx[0]
    if not ie < ifx:
        failures.append('the `endglobals` (line %d) comes after the 1st `function` (line %d)'
                        % (ie + 1, ifx + 1))
        return None, {}
    before_globals = names_of(RX_NATIVE, ls[:ig])
    after_func = names_of(RX_NATIVE, ls[ifx:])
    if before_globals and names_of(RX_NATIVE, sec['natives']):
        failures.append('%d `native` BEFORE the `globals` (%s): injecting ours would go into the middle '
                        'delas' % (len(before_globals), ', '.join(before_globals[:5])))
    else:
        before_globals = []
    if after_func:
        failures.append('%d `native` AFTER the 1st `function` (%s): "Native declared after '
                        'functions" -- the map is already broken before the injection'
                        % (len(after_func), ', '.join(after_func[:5])))
    if before_globals or after_func:
        return None, {}

    engine = engine_names()
    native_names = names_of(RX_NATIVE, sec['natives'])
    engine_cols = [n for n in native_names if n in engine]
    if engine_cols:
        failures.append('natives of the layer that the ENGINE already defines (%s): "already defined"'
                        % ', '.join(engine_cols))
    if any(RX_FUNC_DEF_B.match(no_end(line)) for line in sec['natives']):
        failures.append('the NATIVES section of the layer has a `function` in the middle: wrong order')

    func_names = names_of(RX_FUNC_DEF_B, sec['functions'])
    if not func_names:
        failures.append('the FUNCTIONS section of the layer has no `function`')
    dup = sorted({n for n in func_names if func_names.count(n) > 1})
    if dup:
        failures.append('repeated functions INSIDE the layer: %s' % ', '.join(dup[:10]))
    map_func_names = set(names_of(RX_FUNC_DEF_B, ls))
    map_column = sorted(set(func_names) & map_func_names)
    if map_column:
        failures.append('%d functions of the layer with the SAME name as a map function: %s'
                        % (len(map_column), ', '.join(map_column[:10])))
    engine_col_f = sorted(set(func_names) & engine)
    if engine_col_f:
        failures.append('%d layer functions that the ENGINE already defines: %s'
                        % (len(engine_col_f), ', '.join(engine_col_f[:10])))

    g_nomes, bad_globals = global_names(sec['globals_block'])
    if bad_globals:
        failures.append('%d line(s) of the GLOBALS section that are not a variable declaration (e.g.: %s)'
                        % (len(bad_globals), bad_globals[0][:70]))
    map_globals = set()
    for line in ls[ig:ie]:
        s = no_end(line).decode('latin-1')
        m = re.match(r'\s*(?:constant\s+)?\w+\s+(?:array\s+)?([A-Za-z_]\w*)', s.split('//')[0])
        if m and rx_global_ref().match(s.split('//')[0].rstrip()):
            map_globals.add(m.group(1))
    col_g = sorted(g_nomes & map_globals)
    if col_g:
        failures.append('%d variables of the layer with the SAME name as a map variable: %s'
                        % (len(col_g), ', '.join(col_g[:10])))

    taken_out = []
    if os.path.isfile(EXTRACT):
        t = open(EXTRACT, 'rb').read()
        taken_out = [n for n in names_of(RX_NATIVE, line_list(t))]
        in_layer = set()
        if os.path.isfile(MAP_NATIVES):
            in_layer = set(names_of(RX_NATIVE, line_list(open(MAP_NATIVES, 'rb').read())))
        expected_count = [n for n in taken_out if n not in in_layer and n not in NO_STUB]
        final_text = b'\n'.join(ls).decode('latin-1')
        left_over = sorted(n for n in NO_STUB if re.search(r'\b%s\b' % re.escape(n), final_text))
        if left_over:
            failures.append(
                '%d native(s) of the dead type still in the script: %s' % (len(left_over), ', '.join(left_over[:10]))
            )
        faltando = sorted(set(expected_count) - set(func_names))
        if faltando:
            failures.append('%d of the %d removed natives are NOT defined in the layer: %s'
                            % (len(faltando), len(expected_count), ', '.join(faltando[:10])))
        came_back = sorted(set(expected_count) & set(names_of(RX_NATIVE, ls)))
        if came_back:
            failures.append('%d emulated natives WENT BACK to being `native` in war3map.j: %s'
                            % (len(came_back), ', '.join(came_back[:10])))
        removals_report = (len(taken_out), len(expected_count), len(in_layer))
    else:
        removals_report = (0, 0, 0)
        print('WARNING: no %s -- cannot check the removed natives' % EXTRACT)

    if failures:
        return None, {}

    def block_entry(hash_key):
        begin, end_pos = MINI[hash_key]
        return ([begin + line_end, NOTA[hash_key] + line_end] +
                [no_end(line) + line_end for line in sec[hash_key]] +
                [end_pos + line_end, line_end])

    new_ones = list(ls)
    new_ones[ifx:ifx] = block_entry('functions')
    if LAYER_GLOBALS_ON_TOP:
        new_ones[ig + 1:ig + 1] = block_entry('globals_block')
    else:
        new_ones[ie:ie] = block_entry('globals_block')
    new_ones[ig:ig] = block_entry('natives')
    new = b''.join(new_ones)
    report = {
        'natives': len(native_names),
        'globals_block': len(sec['globals_block']),
        'functions': len(func_names),
        'lines_added': len(line_list(new)) - len(ls),
        'taken_out': removals_report,
        'ancoras': (ig + 1, ie + 1, ifx + 1),
        'line_end': 'CRLF' if line_end == b'\r\n' else 'LF',
    }
    return new, report


def final_report(b, sec):
    fun = set(names_of(RX_FUNC_DEF_B, line_list(b)))
    print('  layer signatures present in war3map.j: %d of %d'
          % (len(fun & set(names_of(RX_FUNC_DEF_B, sec['functions']))),
             len(names_of(RX_FUNC_DEF_B, sec['functions']))))
    for n in PROBE_NAMES:
        print('    %-22s %s' % (n, 'is_present' if n in fun else 'ABSENT'))
    return fun


def main(argv=None):
    _demand_check()
    argv = sys.argv[1:] if argv is None else list(argv)
    apply = '--apply' in argv or any(a.startswith('--apply=') for a in argv)
    undo = '--desfaz' in argv
    tgt = arg('apply', None, argv)
    entry = arg('j', J, argv)
    output = arg('output', tgt or entry, argv)
    layer = arg('layer', DEFAULT_LAYER, argv)
    print('input   : %s' % entry)
    print('layer   : %s' % layer)
    print('output  : %s%s' % (output, '' if apply else '(--so\' check only: not writing)'))

    if not os.path.isfile(entry):
        print('MISSING war3map.j: %s' % entry)
        return 2

    failures = []
    sec = None
    if not undo:
        sec = read_layer(layer, failures)
        if sec is None:
            for f in failures:
                print('FAIL: ' + f)
            print('\nABORTED while reading the layer.')
            return 1
        for hash_key in ('natives', 'globals_block', 'functions'):
            print('  section %-8s %7d lines' % (hash_key, len(sec[hash_key])))

    b = open(entry, 'rb').read()
    print()
    print('=== war3map.j: state BEFORE ===')
    print('  %d B  %d linhas  sha256 %s' % (len(b), len(line_list(b)), sha(b)))

    b_clean, n_rem, n_blocks = strip_injection(b, failures)
    if b_clean is None:
        for f in failures:
            print('FAIL: ' + f)
        return 1
    if failures:
        for f in failures:
            print('FAIL: ' + f)
        return 1
    if n_blocks:
        print('  previous injection found: %d block(s), %d line(s) removed (idempotence)'
              % (n_blocks, n_rem))

    if undo:
        new, report = b_clean, {'natives': 0, 'globals_block': 0, 'functions': 0, 'lines_added': -n_rem}
    else:
        new, report = applies(b_clean, sec, failures)
        if new is None:
            print()
            print('=== LOCKS ===')
            for f in failures:
                print('  FAIL: ' + f)
            print('\nABORTED: NOTHING injected. The `war3map.j` stays as it was.')
            return 1

    print()
    print('=== locks ===')
    if report.get('taken_out'):
        r = report['taken_out']
        print('  natives declared in the extraction: %d | removed (emulated): %d | from the engine (remain'
              '`native`): %d' % r)
    if report.get('ancoras'):
        print('  anchors (1-based, in the CLEAN file): `globals`=%d  `endglobals`=%d  1st `function`=%d'
              % report['ancoras'])
    print('  collisions with the engine / with the map: 0 (checked name by name)')
    if not undo:
        print('  injected: %d native | %d lines of globals | %d functions | +%d lines (%s)'
              % (report['natives'], report['globals_block'], report['functions'],
                 report['lines_added'], report['line_end']))

    if not undo:
        print()
        print('=== proof that the layer is REALLY inside ===')
        final_report(new, sec)

    print()
    print('=== war3map.j: state AFTER ===')
    print('  %d B  %d linhas  sha256 %s' % (len(new), len(line_list(new)), sha(new)))

    if not apply:
        print('\n(--so\' check only: nothing written)')
        return 0
    if new == b:
        print('\nno change: %s stays byte for byte equal (idempotent)' % output)
        return 0
    open(output, 'wb').write(new)
    print('written: %s' % output)
    return 0


def _cli(argv):
    root = arg('root', None, argv)
    if not root:
        print(__doc__)
        print('MISSING --raiz=<project>')
        return 2
    configure_layer(root)
    return main([a for a in argv if not a.startswith('--root=')])


if __name__ == '__main__':
    sys.exit(_cli(sys.argv[1:]))
