# The script chain of a port: every step from the map script to the one that passes the compiler.
import collections
import hashlib
import json
import os
import re
import sys
import time

from doctor.port import layer
from doctor.port import class1
from doctor.port import desync
from doctor.port import effects
from doctor.port import statuses
from doctor.port import lbkkapi
from doctor.port import memory_hacks
from doctor.port import typecast
from doctor.port import shadowed
from doctor.port import dead_type
from doctor.port import save_wiring
from doctor.port import return_fixes
from doctor.port import inject
from doctor.port import engine
from doctor.port import natives
from doctor.script import pjass
from doctor.port import field_table
from doctor.port import char_table
from doctor.port import ui_local


RX_STRINGHASH = re.compile(r'StringHash\("((?:[^"\\]|\\.)*)"\)')


def sha(t):
    return hashlib.sha256(t.encode('latin-1')).hexdigest()[:16]


def aborts(stage, failures):
    print('\nABORT at %s:' % stage)
    for f in failures:
        print('  ' + str(f))
    sys.exit(1)


def to_utf8(t):
    return t.encode('latin-1').decode('utf-8', 'surrogateescape')


def from_utf8(t):
    return t.encode('utf-8', 'surrogateescape').decode('latin-1')


def needs_locking(exp_len):
    if exp_len is None:
        return True
    if isinstance(exp_len, dict):
        return any(needs_locking(v) for v in exp_len.values())
    return False


def report_measures(exp_len, medidas):
    keys = [k for k in medidas if k not in exp_len or needs_locking(exp_len.get(k))]
    if not keys:
        return
    print(
        '\nMEASURES (the expected ones without a lock: %s). The measured block, to paste in the EXPECTED of the recipe:'
        % ', '.join(keys)
    )
    print('ESPERADAS = {')
    for k, v in medidas.items():
        print('    %r: %r,%s' % (k, v, '' if k in keys else '   # already locked'))
    print('}')
    print('MEDIDAS_JSON: %s' % json.dumps(medidas, ensure_ascii=True, sort_keys=False))


def verify(stage, expected_one, medida):
    if expected_one is None:
        print('   (MEASURED, no lock: %s = %s)' % (stage, medida))
        return
    if expected_one != medida:
        aborts(stage, ['measured %s, expected %s' % (medida, expected_one)])


def traduz(r, body_text, raw_data):
    tr_dir = getattr(r, 'TR_DIR', None)
    if not tr_dir or not os.path.isfile(os.path.join(tr_dir, 'strings.json')):
        print('3h: no dictionary (%s) -- the script comes out untranslated' % tr_dir)
        return body_text, 0
    os.environ['TR_DIR'] = tr_dir
    from doctor.translation import tr_apply as ta
    entries = json.load(open(os.path.join(tr_dir, 'strings.json'), encoding='utf-8'))
    tr = ta.load_translations()
    all_entries = {}
    if getattr(r, 'TR_EXTRAS', False):
        extras, all_entries = ta.load_extras(), ta.load_all()
        tr.update(ta.extras_by_id(entries, extras))
        tr.update(ta.extras_by_id(entries, all_entries))
        by_text_map = ta.translation_map(entries, tr, extras)
        new, _cats_, _details, n = ta.apply_by_occurrence(to_utf8(body_text), by_text_map, False, all_entries)
    else:
        by_text_map = ta.translation_map(entries, tr)
        new, _cats_, _details, n = ta.apply_by_occurrence(to_utf8(body_text), by_text_map)
    new = from_utf8(new)
    if getattr(r, 'TR_LOCK_STRINGHASH', True):
        before = collections.Counter(RX_STRINGHASH.findall(to_utf8(body_text)))
        after_diag = collections.Counter(RX_STRINGHASH.findall(to_utf8(new)))
        outside = sorted(k for k in (before - after_diag) if k not in all_entries)
        if outside:
            aborts('3h (translation)', ['%d StringHash argument(s) changed outside texto_en_todas.json: %s'
                                        % (len(outside), ', '.join(outside[:8]))])
    untouchable = os.path.join(tr_dir, 'intocaveis.json')
    if os.path.isfile(untouchable):
        doc = json.load(open(untouchable, encoding='utf-8'))
        fallen = []
        for lit in doc['protected_literals']:
            try:
                b = lit.encode('utf-8').decode('latin-1')
            except UnicodeEncodeError:
                b = lit
            tgt = b if '"' in b else '"' + b + '"'
            if new.count(tgt) < raw_data.count(tgt):
                fallen.append((lit, raw_data.count(tgt), new.count(tgt)))
        if fallen:
            aborts('3h (protected literals)', ['%r: %d -> %d' % c for c in fallen])
        print('3h translation: %d swaps; the %d protected literals checked, 0 fell'
              % (n, len(doc['protected_literals'])))
    else:
        print('3h translation: %d on-screen occurrences translated (the StringHash keys checked: equal)' % n)
    return new, n


def control_rawcodes(body_text):
    n = [0]

    def swap(m):
        s = m.group(1)
        if s is None or not any(ord(c) < 32 for c in s):
            return m.group(0)
        n[0] += 1
        return str(int.from_bytes(s.encode('latin-1'), 'big'))
    new = re.sub(r"'([^']{4})'", swap, body_text)
    return new, n[0]


RX_LOOSE_CONTROL = re.compile(r'"(?:\\.|[^"\\])*"|\'[^\']*\'|//[^\n]*|[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')
CONTROL_BYTE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')


def loose_control_bytes(body_text):
    n = [0]

    def swap(m):
        s = m.group(0)
        if s[0] in '"\'':
            return s
        new = CONTROL_BYTE.sub(' ', s)
        n[0] += sum(1 for a, b in zip(s, new) if a != b)
        return new
    new = RX_LOOSE_CONTROL.sub(swap, body_text)
    return new, n[0]


def assemble(r, argv=None):
    argv = sys.argv[1:] if argv is None else argv
    t0 = time.time()
    exp_len = r.EXPECTED
    table = os.path.join(r.OUT, 'slk_campos_tabela.j')
    blizzard = os.path.join(r.OUT, 'blizzard.j')
    layer_path = os.path.join(r.OUT, 'camada.j')
    pre = os.path.join(r.OUT, 'war3map_pre_injecao.j')
    final = os.path.join(r.OUT, 'war3map.j')
    chars = os.path.join(r.COMPAT, 'out_sh_chars.j')
    map_natives = os.path.join(r.COMPAT, 'part_0_map_natives.j')
    os.makedirs(r.OUT, exist_ok=True)
    medidas = collections.OrderedDict()
    raw_data = open(r.CRU, 'rb').read().decode('latin-1')
    print('raw: %s (%d B, %d lines, sha %s)' % (r.CRU, len(raw_data), raw_data.count('\n'), sha(raw_data)))
    raw_data, n_rc = control_rawcodes(raw_data)
    if n_rc:
        print('0a: %d rawcode(s) with a control byte became a number' % n_rc)
    raw_data, n_ctl = loose_control_bytes(raw_data)
    if n_ctl:
        print('0a: %d loose control byte(s) in the code became spaces' % n_ctl)
    loose_ones = len(re.findall(r'\r(?!\n)', raw_data))
    if loose_ones:
        raw_data = re.sub(r'\r(?!\n)', '\n', raw_data)
        print('0a: %d lone CR line ending(s) became LF' % loose_ones)
    t = raw_data

    if hasattr(r, 'data_bytes'):
        failures, info = r.data_bytes()
        if failures:
            aborts('0b (data)', failures)
        if hasattr(r, 'data_report'):
            r.data_report(info)
        if isinstance(info, dict) and 'medidas' in info:
            medidas['data_bytes'] = info['medidas']

    t, info = lbkkapi.applies(t)
    if info['failures']:
        aborts('0c (LBKKAPI x common.j 3.0)', info['failures'])
    print('0c LBKKAPI: %s -- %s' % (info['status'], info['detail']))
    verify('0c lbkkapi', exp_len.get('lbkkapi'), info['removed_ones'])
    medidas['lbkkapi'] = info['removed_ones']

    t, info = typecast.applies(t)
    if info['failures']:
        aborts('0d (typecast)', info['failures'])
    typecast.report_data(info)
    verify('0d typecast', exp_len.get('typecast'), info['rewrites'])
    medidas['typecast'] = info['rewrites']

    t, info = shadowed.applies(t)
    if info['failures']:
        aborts('0e (redeclared globals)', info['failures'])
    shadowed.report_data(info)
    verify('0e shadowed', exp_len.get('shadowed'), len(info['removed_ones']))
    medidas['shadowed'] = len(info['removed_ones'])

    t, info = dead_type.applies(t, dead_type.engine_types(
        open(os.path.join(layer.REF_30, 'common.j'), 'rb').read().decode('latin-1')))
    if info['failures']:
        aborts('0f (dead type)', info['failures'])
    dead_type.report_data(info)
    no_stub = list(info['natives'])
    if 'dead_type' in exp_len or info['types']:
        verify('0f dead type', exp_len.get('dead_type'), len(info['functions']))
        medidas['dead_type'] = len(info['functions'])

    t, info = return_fixes.applies(t)
    return_fixes.report_data(info)
    if 'return_fixes' in exp_len or info['real_blocks'] or info['codes'] or info['shadows']:
        verify('0g returns', exp_len.get('return_fixes'), info['real_blocks'] + info['codes'] + info['shadows'])
        medidas['return_fixes'] = info['real_blocks'] + info['codes'] + info['shadows']

    memory_level = getattr(r, 'MEMORY_LEVEL', None)
    if memory_level:
        t, info = memory_hacks.applies(t, lbkkapi.read_reference(), equivalents=True,
                                       neutralize=(memory_level == 'neutralize'))
        memory_hacks.report_data(info)
        r.MEMORY_INFO = info

    failures, _info, _pixel_data = field_table.run_action(r.TABLE_SOURCE, table, r.LEVEL_FIELDS,
                                                          controle=getattr(r, 'CONTROL_TABLE', True),
                                                          by_name=getattr(r, 'SLK_BY_NAME', False))
    if failures:
        aborts('1 (3d table)', failures)

    t, info = class1.applies(t, table=table, expected_count=exp_len['class1'],
                             tolerant_mode=getattr(r, 'CLASS1_TOLERANT', False))
    if info['by_class'].get('class 1 in game'):
        print(
            '3d: %d class 1 site(s) with the field or the id only in the game: the EXExecuteScript of the game answers'
            % info['by_class']['class 1 in game']
        )
    if info['failures']:
        aborts('2 (3d)', info['failures'])
    print('3d: %d EXExecuteScript -> DB_slk_get' % info['swapped'])
    medidas['class1'] = info['swapped']

    t, n = r.traduz(t, raw_data) if hasattr(r, 'traduz') else traduz(r, t, raw_data)
    verify('3h swaps', exp_len.get('translation'), n)
    medidas['translation'] = n

    listing = getattr(r, 'NO_DOT', None)
    if listing:
        from doctor.port import name_without_dot

        lat = dict(
            (o.encode('utf-8').decode('latin-1'), n.encode('utf-8').decode('latin-1')) for o, n in listing.items()
        )
        t, tally = name_without_dot.swap(t, lat, sep=chr(92) * 2)
        n = sum(tally.values())
        print('4a no_dot: %d model literal(s) with several dots -> the alias %s'
              % (n, dict((k, v) for k, v in tally.items() if v)))
        verify('4a no_dot', exp_len.get('no_dot'), n)
        medidas['no_dot'] = n

    if hasattr(r, 'decisoes'):
        t, details = r.decisoes(t)
        print('user decisions and fixes of the original map: %s' % details)

    if getattr(r, 'CHAT_NORMAL', False):
        n = t.count('GetEventPlayerChatString()')
        t = t.replace('GetEventPlayerChatString()', 'KK_chat()')
        print('4c chat: %d chat read(s) -> KK_chat() (the command is case-insensitive)' % n)
        verify('4c chat', exp_len.get('chat'), n)
        medidas['chat'] = n

    t, info = effects.applies(t, expected_count=exp_len['effects'])
    if info['failures']:
        aborts('5 (3f)', info['failures'])
    print('3f: %s' % {k: v for k, v in info.items() if k not in ('failures',)})
    medidas['effects'] = dict(info['by_native'])
    t, info = statuses.applies(t, expected_count=exp_len['statuses'])
    if info['failures']:
        aborts('6 (3g)', info['failures'])
    print('3g: %s' % {k: v for k, v in info.items() if k not in ('failures',)})
    medidas['statuses'] = dict(info['by_category'])

    if hasattr(r, 'wiring'):
        t, info = r.wiring(t)
        if info['failures']:
            aborts('7 (wiring)', info['failures'])

    if getattr(r, 'SAVE_WIRING', False):
        t, info = save_wiring.applies(t)
        if info['failures']:
            aborts('7c (save wiring)', info['failures'])
        save_wiring.report_data(info)

    t, info = engine.applies(t, expected_count=exp_len['engine'])
    if info['failures']:
        aborts('7b (engine)', info['failures'])
    engine.report_data(info)
    medidas['engine'] = dict((k, info[k]) for k in ('destroy_timer', 'dead_unit', 'damage_target', 'target_damage_bj',
                                                  'damage_dealt'))

    t, info = ui_local.applies(t, exp_len['ui_local'], fixed_ones=getattr(r, 'UI_FIXED', False),
                               tolerant_mode=getattr(r, 'UI_TOLERANT', False))
    if info.get('outside'):
        print(
            'WARNING 3n: %d interface event record(s) without literal `sync`/`code` were left without the local wrapper: %s'
            % (len(info['outside']), '; '.join(info['outside'][:5]))
        )
    if info['failures']:
        aborts('8 (3n)', info['failures'])
    ui_local.report_data(info)
    medidas['ui_local'] = dict(
        (k, info[k]) for k in ('local_vars', 'functions', 'synchronous_ones', 'quadro', 'boot_info')
    )

    cfg = {'ext': r.DESYNC_EXT, 'extract': r.EXTRACT, 'raw_data': r.CRU, 'copy': os.path.join(r.OUT, 'mapa_terreno.j'),
           'expected_count': exp_len['desync']}
    t, info = desync.applies(t, cfg)
    if info['failures']:
        aborts('9 (3q)', info['failures'])
    desync.report_data(info)
    medidas['desync'] = {
        'replacements': info['replacements'],
        'voo': info['voo'],
        'line_list': info['h'],
        'segments': info['segments'],
        'platforms': info['platforms'],
        'platform_tilepoints': info['platform_tilepoints'],
    }

    source = ['--source=' + r.NATIVES_SOURCE] if getattr(r, 'NATIVES_SOURCE', None) else []
    layer.configure_layer(r.ROOT, r.PARTS, compat=r.COMPAT, out=r.OUT, output=blizzard, analise=r.OUT,
                          map_natives=map_natives, generator=r.GENERATOR, no_stub=no_stub)
    texts = [to_utf8(t)] + [layer.read_part_utf8(p) for p in layer.layer_files()
                            if os.path.basename(p) != os.path.basename(chars)]
    n_chars, sha_chars = char_table.make_table(texts, chars, generator=r.GENERATOR)
    print('DB_SH character table: %d characters -> %s (sha %s)' % (n_chars, chars, sha_chars))
    rc = layer.main(['--no-pjass', '--output=' + blizzard] + source)
    if rc:
        aborts('11 (blizzard.j of the layer)', ['camada.main returned %s' % rc])
    blz = open(blizzard, 'rb').read().decode('latin-1')
    t, info = natives.drop_emulated(t, natives.defined_in_layer(blz))
    if info['failures']:
        aborts('11 (strip the emulated natives)', info['failures'])
    natives.report_strip(info, r.CRU)
    t, info = natives.inject_engine(t, open(map_natives, 'rb').read().decode('latin-1'))
    if info['failures']:
        aborts('11 (the natives of the engine)', info['failures'])
    natives.report_engine(info)
    open(pre, 'wb').write(t.encode('latin-1'))
    print('pre-injection: %s (%d B, sha %s)' % (pre, len(t), sha(t)))
    rc = layer.main(['--layer=' + layer_path] + source)
    if rc:
        aborts('12 (the layer in 3 sections)', ['camada.main returned %s' % rc])
    inject.configure_layer(r.ROOT, j=pre, layer_file=layer_path, extract=r.CRU, map_natives=map_natives,
                           no_stub=no_stub, layer_globals_on_top=getattr(r, 'LAYER_GLOBALS_ON_TOP', False))
    rc = inject.main(['--apply', '--j=' + pre, '--output=' + final, '--layer=' + layer_path])
    if rc:
        aborts('12 (injection)', ['injeta.main returned %s' % rc])
    end_pos = open(final, 'rb').read().decode('latin-1')
    print('FINAL: %s (%d B, sha %s)' % (final, len(end_pos), sha(end_pos)))
    report_measures(exp_len, medidas)
    if '--no-pjass' not in argv:
        tmp = os.path.join(r.OUT, '_pjass')
        print('\n### GATE G1 (the blizzard.j of the layer and the war3map.j PRE-injection)')
        g1 = pjass.main(['--conjunto', '--j=' + pre, '--blizzard=' + blizzard], root=r.ROOT, tmp=tmp)
        print('\n### GATE G2 (the blizzard.j OF THE GAME + the war3map.j WITH the layer)')
        g2 = pjass.main(['--j=' + final], root=r.ROOT, tmp=tmp)
        print('\nG1 %s | G2 %s' % ('PASS' if g1 == 0 else 'FAIL', 'PASS' if g2 == 0 else 'FAIL'))
        if g1 or g2:
            sys.exit(1)
    print('\ndone in %.0f s' % (time.time() - t0))
    return 0
