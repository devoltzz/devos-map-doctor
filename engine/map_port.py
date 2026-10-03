# Ports a KK or M16 platform map to Warcraft III 3.0 in one run, with a report of what is left.
import contextlib
import io
import json
import os
import re
import hashlib
import time

import mpqread
import new
import dead_type

HERE = os.path.dirname(os.path.abspath(__file__))

TETO = 512 << 20
WARNINGS = []


class Aborts(Exception):
    pass


class Recipe(object):
    def __init__(self, **kw):
        self.__dict__.update(kw)


def _muted(f, *a, **k):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            v = f(*a, **k)
        except SystemExit as e:
            v = SystemExit(e.code)
    return v, buf.getvalue()


def _writes(file_path, data_bytes):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'wb') as f:
        f.write(data_bytes)


def _destination(root, fname):
    pieces = [p for p in fname.replace('/', '\\').split('\\') if p not in ('', '.', '..')]
    return os.path.join(root, *pieces)


HARMLESS_PROTECTIONS = ('fake_entries', 'scrambled_ids', 'fake_files')
HEADER_ONLY_PROTECTIONS = ('read_only',)


def unprotected_result(map_path, root, log):
    import unprotect
    d, _s = _muted(unprotect.diagnose, map_path)
    if isinstance(d, SystemExit) or not isinstance(d, dict):
        return map_path
    code_part = set(p['code'] for p in d.get('protections') or [])
    if 'kk_encrypted' in code_part:
        raise Aborts(
            'the map is ENCRYPTED by the KK platform: kkmap.jc is only the loader, the real map is outside the '
            'MPQ and only the KK client decrypts it, so it cannot be ported'
        )
    mpq = code_part - set(unprotect.BUTTON3_ONLY) - set(unprotect.DATA_ONLY)
    if not mpq - set(HARMLESS_PROTECTIONS):
        return map_path
    output = os.path.join(root, 'unprotected.w3x')
    options = dict((x['hash_key'], False) for x in unprotect.steps(d) if x['action_code'] == 'fix' and
                   x['hash_key'].startswith('dados:'))
    if not mpq - set(HARMLESS_PROTECTIONS) - set(HEADER_ONLY_PROTECTIONS):
        options = dict((x['hash_key'], x['hash_key'] == 'mpq') for x in unprotect.steps(d) if x['action_code'] == 'fix')
    r, _s = _muted(unprotect.unprotect, map_path, output, None, diag=d, options=options)
    if isinstance(r, dict) and r.get('status') in ('done', 'partial') and os.path.isfile(output):
        log('0. the map protection removed first (%s)' % ', '.join(sorted(mpq)))
        WARNINGS.append(
            'the map was protected (%s): the port started from the unprotected copy' % ', '.join(sorted(mpq))
        )
        return output
    raise Aborts('the map is protected (%s) and the protection could not be removed: %s'
                 % (', '.join(sorted(mpq)), (r.get('err') if isinstance(r, dict) else r)))


REF_FILES = ('common.j', 'blizzard.j', 'common.ai')


def game_reference(root, log):
    if all(os.path.isfile(os.path.join(new.REF, f)) for f in REF_FILES):
        return new.REF
    import triggerdata
    ref = os.path.join(root, 'ref')
    for f in REF_FILES:
        t = triggerdata.game_script(f)
        if not t:
            raise Aborts('the game script %s could not be read: the port needs Warcraft III 3.0 installed' % f)
        _writes(os.path.join(ref, f), t.encode('utf-8', 'surrogateescape'))
    import blizzard_map
    import layer
    import lbkkapi
    import pjass
    new.REF = layer.REF_30 = pjass.REF_30 = blizzard_map.REF_30 = lbkkapi.REF_30 = ref
    log('0. the game scripts read from the installed Warcraft III')
    return ref


def names_and_extraction(map_path, extract, log):
    import unprotect
    import new_port
    a = mpqread.Archive(map_path)
    name_list = set(unprotect.map_names(a))
    for n in list(new.ALWAYS_NAMES) + list(new_port.KNOWN_NAMES):
        if a.find(n):
            name_list.add(n)
    done = []
    for n in sorted(name_list, key=str.lower):
        try:
            d = a.read(n)
        except Exception:
            continue
        if d is None:
            continue
        _writes(_destination(extract, n), d)
        done.append(n)
    log('1. names and extraction: %d files' % len(done))
    return a, done


def map_script(a, extract, scripts_dir, log):
    ext_j = os.path.join(extract, 'war3map.j')
    if not os.path.isfile(ext_j) and os.path.isfile(os.path.join(extract, 'scripts', 'war3map.j')):
        ext_j = os.path.join(extract, 'scripts', 'war3map.j')
    if not os.path.isfile(ext_j):
        if os.path.isfile(os.path.join(extract, 'war3map.lua')):
            raise Aborts('the map is Lua (war3map.lua): the KK/M16 port is for JASS maps')
        raise Aborts('the map has no war3map.j')
    raw_bytes = open(ext_j, 'rb').read()
    j2b = b'"war3map.bin"' in raw_bytes and b'do_script' in raw_bytes
    kkmap = os.path.join(extract, 'kkmap.jc')
    kkwe = not j2b and len(raw_bytes) < 4096 and (b'KKWE' in raw_bytes or os.path.isfile(kkmap))
    if not j2b and not kkwe:
        return ext_j, 'jass'
    import kkwe as _kkwe
    import kkwe_decompile
    import triggerdata
    common, blizzard = triggerdata.game_script('common.j'), triggerdata.game_script('blizzard.j')
    if not common or not blizzard:
        raise Aborts('the map script is compiled bytecode and the game scripts (common.j, Blizzard.j) could not be '
                     'read: Warcraft III has to be installed to decompile it')
    if j2b:
        import j2b as _j2b
        data_bytes = a.read('war3map.bin')
        if not data_bytes:
            raise Aborts('the war3map.j loads war3map.bin, which is missing')
        bc = _j2b.bytecode(data_bytes)
        map_own = raw_bytes.decode('utf-8', 'surrogateescape')
        forma = 'j2b'
    else:
        if not os.path.isfile(kkmap):
            raise Aborts('the war3map.j is the KKWE stub and kkmap.jc is missing')
        container = _kkwe.read_container(open(kkmap, 'rb').read())
        loader, hook = _kkwe.is_loader(_kkwe.load_data(kkmap))
        if loader:
            raise Aborts('the map is ENCRYPTED by the KK platform: kkmap.jc is only the loader (Preloader(%r)); the '
                         'real map is outside the MPQ and cannot be ported' % hook)
        bc = _kkwe.Bytecode(container)
        map_own = ''
        forma = 'kkwe'
    try:
        (body_text, details), _output = _muted(
            kkwe_decompile.recover, bc, common, blizzard, None, map_own, no_clash=True
        )
    except kkwe_decompile.DecompileError as e:
        raise Aborts('the compiled script did not come back to JASS: %s' % e)
    import editor_prep
    body_text, _real_ones = editor_prep.real_literal_return(body_text)
    raw_data = os.path.join(scripts_dir, 'war3map.j')
    _writes(raw_data, body_text.encode('utf-8', 'surrogateescape'))
    log(
        '2. script: %s bytecode back to JASS (%d functions, proved by recompiling)'
        % (forma, details.get('functions', 0))
    )
    return raw_data, forma


def diagnostico(body_text, extract):
    ref = new.REF
    ref_common = new.natives_of(open(os.path.join(ref, 'common.j'), encoding='utf-8', errors='replace').read())
    ai_ref = new.natives_of(open(os.path.join(ref, 'common.ai'), encoding='utf-8', errors='replace').read())
    map_own = new.natives_of(body_text)
    plataforma = sorted(n for n in map_own if n not in ref_common and n not in ai_ref)
    layer = new.layer_functions()
    jn_funcs = set(new.RX_FUNCTION.findall(open(os.path.join(HERE, 'compat', 'kk_jn.j'), encoding='utf-8').read()))
    units = os.path.join(extract, 'Units')
    slk = os.path.isdir(units) and any(f.lower().endswith('.slk') and os.path.getsize(os.path.join(units, f))
                                       for f in os.listdir(units))
    import field_table
    import slk_dynamic
    map_fields, sitios, _f = field_table.script_fields(body_text)
    fields_list = sorted('%s.%s' % (t, c) for t, cs in map_fields.items() for c in cs)
    dynamic_map, embrulhos = slk_dynamic.dynamic_fields(body_text)
    for tab, cs in sorted(dynamic_map.items()):
        fields_list += sorted('%s.%s' % (tab, c) for c in cs if '%s.%s' % (tab, c) not in fields_list)
    return {
        'engine_outside': sorted(n for n in map_own if n in ai_ref and n not in ref_common),
        'plataforma': plataforma,
        'implemented_count': [n for n in plataforma if n in layer],
        'jn': sorted(n for n in plataforma if n in jn_funcs),
        'slk': slk,
        'fields': fields_list + [c for c in new.LAYER_FIELDS if c.lower() not in set(x.lower() for x in fields_list)],
        'exec_sites': sum(sitios.values()),
        'slk_wrappers': embrulhos,
    }


def map_part(root, compat, extract, raw_data, body_text, diag, heading, log):
    for p in new.inclusion_points():
        _writes(os.path.join(compat, 'kk_%s.j' % p), b'')
    valores = {'NOME': heading, 'DATA': time.strftime('%d/%m/%Y'),
               'N_SEQ': len(re.findall(r'\b(?:DzSetEffectAnimation|EXSetEffectAnimation)\s*\(', body_text)),
               'N_ANIM': len(re.findall(r'\bSetUnitAnimationByIndex\s*\(', body_text))}
    new.save(os.path.join(compat, 'out_seqs.j'), new.model('out_seqs.j', valores))
    new.save(os.path.join(compat, 'out_anim_nomes.j'), new.model('out_anim_nomes.j', valores))
    blz = False
    proprios = dict((f.lower(), os.path.join(extract, d, f)) for d in os.listdir(extract)
                    if d.lower() == 'scripts' and os.path.isdir(os.path.join(extract, d))
                    for f in os.listdir(os.path.join(extract, d)))
    import blizzard_map
    if 'blizzard.j' in proprios and not os.path.isfile(blizzard_map.VANILLA):
        WARNINGS.append("the map has its own Scripts\\Blizzard.j; without the Blizzard.j of patch 1.27 to compare it "
                        "with, its changes were not carried over (Reforged uses its own Blizzard.j)")
    elif 'blizzard.j' in proprios:
        blz_part, blz_info = blizzard_map.extract_parts(proprios['blizzard.j'], raw_data)
        failures = blizzard_map.failures_of(blz_info)
        if failures:
            WARNINGS.append(
                "the map's own Scripts\\Blizzard.j changes functions of the game, and Reforged uses its own: "
                + ' | '.join(failures)[:400]
            )
        if blz_part:
            new.save(os.path.join(compat, 'out_blizzard_mapa.j'), blz_part)
            blz = True
    engine_lines = [
        m.group(0).strip() for m in new.RX_NATIVE.finditer(body_text) if m.group(1) in diag['engine_outside']
    ]
    new.save(os.path.join(compat, 'parte_0_mapa_natives.j'),
             '// the engine natives the map declares\n' + ''.join(line + '\n' for line in engine_lines))
    import channel_table
    _v, output = _muted(channel_table.gera, extract, os.path.join(compat, 'out_perfil_slots.j'), 'auto')
    if isinstance(_v, SystemExit) and _v.code:
        raise Aborts('the save channel table: %s' % output.strip()[-300:])
    base_save = re.sub(r'[^A-Za-z0-9]', '', heading) or 'Map'
    pre = base_save[:2].lower()
    jpeg_seed = hashlib.sha256(('devo-port|' + base_save).encode('utf-8')).hexdigest()
    pair = {
        'KK_SAVE_RAIZ': base_save + '\\\\',
        'KK_SAVE_SEGREDO': '%s|%s.blob.v1|%s|opaque-profile|port' % (base_save, pre, jpeg_seed[:24]),
        'KK_SAVE_ENV': jpeg_seed[24:32],
        'KK_SAVE_CH_BLOB': pre + '.blob.v1', 'KK_SAVE_CH_ENV': pre + '.env.v1', 'KK_SAVE_CH_IV': pre + '.iv.v1',
        'KK_SAVE_CH_LEN': pre + '.len.v1', 'KK_SAVE_CH_N': pre + '.n.v1', 'KK_SAVE_CH_SIG': pre + '.sig.v1',
        'KK_SAVE_CH_GEN': pre + '.gen.v1',
        'KK_CAR_LIGADO': 'false',
        'KK_UI_ANCORA': 'true',
        'KK_Z_4': 'true',
    }
    if diag['jn']:
        found_key = channel_table.jn_ability(extract)
        if not found_key:
            raise Aborts('M16 save: no ability A??? with Tip and Ubertip to carry the save channel')
        ability_id, _fields = found_key
        saved = new.return_literal(body_text, ('JNObjectCharacterSave', 'JNObjectUserSave'))
        diario = new.return_literal(body_text, ('JNDailyCheckToday',))
        pair.update({
            'KK_JN_PASTA': base_save + '\\\\',
            'KK_JN_HABILIDADE': "'%s'" % ability_id,
            'KK_JN_SALVO': saved if saved is not None else '|cff00ff00Save OK|r',
            'KK_JN_DIARIO': diario if diario is not None else 'Checked',
            'KK_JN_USE': 'false', 'KK_JN_CONEXAO': "'BNET'", 'KK_JN_HOST': 'false',
        })
        pair.update(dict((k, v) for k, v in new.JN_PARAMETERS.items() if not k.startswith('_')))
        new.save(os.path.join(compat, 'kk_sv_prepara_tde.j'), '    call KKJN_init()\n')
    new.save(os.path.join(root, 'port', 'kk_parametros.json'), json.dumps(pair, ensure_ascii=False, indent=1) + '\n')
    log('4. the map part of the layer: %d natives of the engine, save folder %r%s'
        % (len(engine_lines), pair['KK_SAVE_RAIZ'], ' (M16 route)' if diag['jn'] else ''))
    return blz, pair


def receita(root, raw_data, diag, blz, no_dot_name_list, heading):
    extract = os.path.join(root, 'port', 'extract')
    out = os.path.join(root, 'port', 'out', 'kk')
    data_bytes = os.path.join(out, 'data_bytes')
    r = Recipe(
        ROOT=root,
        CRU=raw_data,
        EXTRACT=extract,
        COMPAT=os.path.join(root, 'port', 'kk', 'compat'),
        OUT=out,
        DATA=data_bytes,
        TABLE_SOURCE=data_bytes if diag['slk'] else extract,
        DESYNC_EXT=extract,
        TR_DIR=os.path.join(root, 'port', 'tools', 'tr'),
        GENERATOR='porta.py (%s)' % heading,
        NO_DOT=no_dot_name_list,
        LEVEL_FIELDS=diag['fields'],
        PARTES=new.layer_parts(bool(diag['jn']), blz),
        ESPERADAS=dict(new.EMPTY_EXPECTED),
        UI_FIXED=True,
        UI_TOLERANT=True,
        CLASS1_TOLERANT=True,
        SAVE_WIRING=not diag['jn'],
        LAYER_GLOBALS_ON_TOP=blz,
        SLK_BY_NAME='EXExecuteScript' in diag['plataforma'] and 'EXExecuteScript' not in diag['implemented_count'],
    )
    if os.path.normcase(raw_data) != os.path.normcase(os.path.join(extract, 'war3map.j')):
        r.NATIVES_SOURCE = raw_data
    if diag['slk']:
        import slk_data

        def _pixel_data():
            f, info = _slk_data()
            WARNINGS.extend(info.get('warnings') or [])
            return f, info

        def _slk_data():
            return slk_data.applies(
                extract,
                data_bytes,
                raw_data,
                os.path.join(r.COMPAT, 'kk_morph_chaos.j'),
                tr_dir=r.TR_DIR,
                expected_count={'slk': None, 'fake_b': None, 'models': None, 'chaos': None},
                no_dot=no_dot_name_list,
                tolerant_mode=True,
            )
        r.data_report = slk_data.report_data
    else:
        import classic_data
        regras = tuple((file_, entry, obj_kind, dict((c, None) for c in locks))
                       for file_, entry, obj_kind, locks in
                       classic_data.regras_padrao(extract, os.path.join(root, 'port', 'out', 'extract_en')))

        def _pixel_data():
            return classic_data.applies(regras, root, data_bytes, expected_count=None, gravar=True)
        r.data_report = classic_data.report_data
    r.data_bytes = _pixel_data
    return r


def run_chain(r):
    import chain
    v, output = _muted(chain.assemble, r, [])
    open(os.path.join(r.ROOT, 'port', 'out', 'cadeia.log'), 'w', encoding='utf-8').write(output)
    g = re.search(r'G1 (PASS|FAIL) \| G2 (PASS|FAIL)', output)
    abort_match = re.search(r'ABORT at ([^\n]*)\n((?:  [^\n]*\n)*)', output)
    g1 = g.group(1) == 'PASS' if g else False
    g2 = g.group(2) == 'PASS' if g else False
    ok = g1 and g2 and not isinstance(v, SystemExit)
    if abort_match:
        raise Aborts(
            'the script chain stopped at %s: %s' % (abort_match.group(1).strip(), abort_match.group(2).strip()[:400])
        )
    return ok, g1, g2, output


PJASS_RUNTIME_ONLY = ('is uninitialized', 'String literals over 1023 chars')


def pjass_errors(log_cadeia):
    seen = []
    for m in re.finditer(r'(?m)^(?:.*?[\\/\s])?(?:war3map|blizzard)\.j:\d+: (.+)$', log_cadeia):
        if m.group(1) not in seen:
            seen.append(m.group(1).strip())
    return seen


SCRIPTS_FOLDER_FILES = ('Scripts\\war3map.j', 'Scripts\\Blizzard.j', 'Scripts\\common.j', 'Scripts\\common.ai')


def scripts_folder_files(original, name_list=()):
    a = mpqread.Archive(original)
    out, seen = [], set()
    for n in list(name_list) + list(SCRIPTS_FOLDER_FILES):
        n = n.replace('/', '\\')
        if n.lower().startswith('scripts\\') and n.lower() not in seen and a.find(n):
            seen.add(n.lower())
            out.append(n)
    return sorted(out, key=str.lower)


def build_w3x(original, output, r, to_remove, no_dot_list, log, name_list=()):
    import map_path
    import name_without_dot
    item_entries = [('war3map.j', os.path.join(r.OUT, 'war3map.j'))]
    by_name = {}
    for folder in (os.path.join(r.OUT, 'arte'), r.DATA):
        if os.path.isdir(folder):
            for base, _d, fs in os.walk(folder):
                for f in sorted(fs):
                    p = os.path.join(base, f)
                    n = os.path.relpath(p, folder).replace(os.sep, '\\')
                    if n.lower() not in ('war3map.j', 'war3map.w3i', 'war3map_src.j'):
                        by_name[n.lower()] = (n, p)
    item_entries.extend(by_name[k] for k in sorted(by_name))
    copies, gaps = name_without_dot.copies(mpqread.Archive(original), no_dot_list)
    if gaps:
        WARNINGS.append('%d model(s) with dots in the name could not be copied under a name Reforged loads: %s'
                        % (len(gaps), '; '.join(gaps)[:300]))
    item_entries.extend(copies)
    entra = [
        (n, v) for n, v, status_kind, _t in map_path.classify_items(item_entries, original) if status_kind != 'igual'
    ]
    part = os.path.splitext(output)[0] + '.part' + os.path.splitext(output)[1]
    if os.path.exists(part):
        os.remove(part)
    try:
        v, _s = _muted(map_path.attach, original, part, entra, to_delete=to_remove, log=lambda s: None)
        failures = ['the appender stopped: %s' % v] if isinstance(v, SystemExit) else \
            map_path.verify(part, entra, missing_ones=to_remove)
    except Exception as e:
        failures = ['the appender stopped: %s: %s' % (type(e).__name__, e)]
    if failures:
        if os.path.exists(part):
            os.remove(part)
        a = mpqread.Archive(original)
        data_bytes = dict((n, map_path.content(v)) for n, v in entra)
        replacements = dict((n, d) for n, d in data_bytes.items() if a.find(n))
        new_ones = dict((n, d) for n, d in data_bytes.items() if not a.find(n))
        details, _s = _muted(
            map_path.rebuild,
            original,
            part,
            list(name_list) + list(data_bytes),
            replacements=replacements,
            new_ones=new_ones,
            to_remove=to_remove,
            hash_factor=2,
            log=lambda s: None,
        )
        if isinstance(details, SystemExit) or details.get('error_list'):
            raise Aborts('the ported map does not read back: %s' % '; '.join(
                (failures + (details.get('error_list') or []) if isinstance(details, dict) else failures)[:5]))
        log('6. the archive was rewritten (the original could not take the new files in place: %s)' % failures[0])
    sz, slack = map_path.cap(part)
    os.replace(part, output)
    log('6. the map: %d file(s) replaced or added, %.1f MiB' % (len(entra), sz / 1048576.0))
    return sz, slack, [n for n, _v in entra]


def shrinks(output, sz, log):
    import shrink
    menor = os.path.splitext(output)[0] + '.small' + os.path.splitext(output)[1]
    log('6. the map is above 512 MiB: making it smaller, losing nothing (this is slow)')
    r, _s = _muted(shrink.shrink, output, menor)
    if isinstance(r, dict) and r.get('state') == 'done' and os.path.isfile(menor):
        os.replace(menor, output)
        sz = os.path.getsize(output)
        WARNINGS.append('the map was above 512 MiB and was made smaller without loss: %.1f MiB' % (sz / 1048576.0))
    elif os.path.exists(menor):
        os.remove(menor)
    return sz, TETO - sz


RX_TRIG = re.compile(r'^Trig_(.+?)_?(?:Actions|Conditions|Func\d+\w*)$')


def stubs_and_dependents(r, decl_order):
    layer_text = open(os.path.join(r.OUT, 'camada.j'), 'rb').read().decode('latin-1')
    i = layer_text.find('STUBS:')
    stubs = set(re.findall(r'(?m)^function\s+(\w+)\s+takes', layer_text[i:])) if i >= 0 else set()
    stubs &= set(decl_order)
    pre = open(os.path.join(r.OUT, 'war3map_pre_injecao.j'), 'rb').read().decode('latin-1')
    fs = dead_type.functions(pre)
    alive = dead_type.live_ones(pre, fs)
    out = []
    for n in sorted(stubs):
        rx = re.compile(r'\b%s\s*\(' % re.escape(n))
        who = {}
        for f, a, b in fs:
            if f in alive:
                k = len(rx.findall(pre[a:b]))
                if k:
                    who[f] = k
        if not who:
            continue
        trigger_list = sorted(set(m.group(1).rstrip('_') for f in who for m in [RX_TRIG.match(f)] if m))
        out.append({'native': n, 'chamadas': sum(who.values()), 'functions': sorted(who), 'trigger_list': trigger_list})
    out.sort(key=lambda x: (-x['chamadas'], x['native']))
    return out


def report_text(details):
    L = ['Port to Reforged 3.0 - report', '=' * 30, '',
         'Map: %s' % details['map_path'], 'Result: %s' % details['resultado'], '']
    if details.get('output'):
        L.append('Ported map: %s (%.1f MiB)' % (details['output'], details.get('bytes', 0) / 1048576.0))
    if details.get('err'):
        L += ['', 'The port stopped: %s' % details['err']]
    d = details.get('diagnostico')
    if d:
        L += ['', 'What the map is', '-' * 15,
              '- script: %s' % {'jass': 'JASS (war3map.j)', 'kkwe': 'KKWE bytecode (kkmap.jc) decompiled and proved',
                                'j2b': 'j2b bytecode (war3map.bin) decompiled and proved'}[details['forma']],
              '- platform: %s' % ('M16 (JN): the platform save is ported to a local save' if d['jn'] else
                                  'KK (DzAPI/japi)' if d['plataforma'] else 'none'),
              '- object data: %s' % ('SLK tables' if d['slk'] else 'w3u/w3t/w3a over the game data'),
              '- platform natives declared: %d; implemented by the port layer: %d'
              % (len(d['plataforma']), len(d['implemented_count'])),
              '- EXExecuteScript sites: %d' % d['exec_sites']]
    if 'g1' in details:
        L += ['', 'Compiler gates (pjass of Reforged 3.0)', '-' * 38,
              '- G1 (the layer with the map script): %s' % ('PASS' if details['g1'] else 'FAIL'),
              '- G2 (the final script with the game Blizzard.j): %s' % ('PASS' if details['g2'] else 'FAIL')]
    ar = details.get('arte')
    if ar:
        L += ['', 'Art from the packages', '-' * 21,
              '- %d file(s) imported (%.1f MB) from %s; %d asked for and found nowhere (the map, the game or the '
              'packages)' % (ar['imported'], ar['bytes'] / 1e6, ', '.join('%s: %d' % kv for kv in
                                                                           sorted(ar['by_pack'].items())) or '-',
                              ar['missing_items'])]
    tm = details.get('dead_type')
    if tm and tm.get('types'):
        L += ['', 'Removed (dead platform code)', '-' * 28,
              '- the type(s) %s, used only by code nothing calls: %d function(s), %d global(s), %d native(s)'
              % (', '.join(tm['types']), len(tm['functions']), len(tm['globals_block']), len(tm['natives']))]
    if details.get('warnings'):
        L += ['', 'Warnings', '-' * 8] + ['- ' + a for a in details['warnings']]
    st = details.get('stubs')
    if st is not None:
        L += ['', 'Natives left as STUBS that the map CALLS (%d)' % len(st), '-' * 44]
        if not st:
            L.append('- none: every platform native the map calls has a body in the port layer')
        for s in st:
            L.append('- %s: %d call(s) in %s%s' % (
                s['native'], s['chamadas'], ', '.join(s['functions'][:6]) + (' ...' if len(s['functions']) > 6 else ''),
                ('; trigger(s): ' + ', '.join(s['trigger_list'][:6])) if s['trigger_list'] else ''))
        if st:
            L.append('A stub compiles and returns the neutral value (0, false, "", null): implement the native, or '
                     'change what depends on it, if that part of the map matters.')
    L += ['', 'Check in game', '-' * 13,
          '- the save and the load (the platform save became a local save in CustomMapData); two players, to see that '
          'loading does not desync',
          '- the menus and panels the platform drew (shop, lobby, F-keys) and the map frames (DzFrame -> BlzFrame)',
          '- every feature listed under the stubs above']
    return '\n'.join(L) + '\n'


RX_VERSION = re.compile(r'(?i)[\s_.-]+(?:v?\d[\w.]*|fix\w*|beta\w*|test\w*|event|ver\w*|final|kr\w*|cn|en|e\d\w*|'
                        r'\[[^\]]*\]|\([^)]*\))$')


def stable_title(fname):
    n = fname
    while True:
        m = RX_VERSION.search(n)
        if not m or m.start() == 0:
            break
        n = n[:m.start()]
    n = re.sub(r'(?<=[A-Za-z])\d+(?:\.\d+)+\w*$', '', n)
    n = re.sub(r'[^A-Za-z0-9 ]+', ' ', n.replace('_', ' ')).strip()
    return re.sub(r'\s+', ' ', n) or re.sub(r'[^A-Za-z0-9]+', ' ', fname).strip() or 'Map'


def map_port(map_path, work, output=None, stats=None, heading=None, log=print, pacotes=(), shrink_large=True):
    t0 = time.time()
    map_path = os.path.abspath(map_path)
    base = os.path.splitext(map_path)[0]
    output = os.path.abspath(output or base + '_reforged.w3x')
    stats = stats or os.path.splitext(output)[0] + '.report.txt'
    heading = heading or stable_title(os.path.splitext(os.path.basename(map_path))[0])
    del WARNINGS[:]
    details = {'map_path': map_path, 'resultado': 'stopped', 'work': work, 'warnings': WARNINGS}
    if os.path.isdir(work) and os.listdir(work):
        details['err'] = 'the work folder is not empty: %s' % work
        return _closes(details, stats, log)
    root = os.path.abspath(work)
    for p in ('port/extract', 'port/tools/tr', 'port/kk/compat', 'port/analysis', 'port/out/kk', 'scripts'):
        os.makedirs(os.path.join(root, *p.split('/')), exist_ok=True)
    extract = os.path.join(root, 'port', 'extract')
    compat = os.path.join(root, 'port', 'kk', 'compat')
    try:
        import pjass
        if not os.path.isfile(pjass.exe()):
            raise Aborts('pjass.exe was not found (%s): the port checks the script with it '
                         '(https://github.com/lep/pjass)' % pjass.exe())
        game_reference(root, log)
        original = map_path
        import mpqdoctor
        sp, _m, _u = mpqdoctor.is_sprotect(mpqread.Archive(original))
        if sp:
            import sprotect_fix
            sprotect_fix.CRYPT = sprotect_fix.init_crypt()
            original = os.path.join(root, 'sprotect_fix.w3x')
            _muted(sprotect_fix.fix, map_path, original)
            log('0. SProtect undone')
        else:
            original = unprotected_result(map_path, root, log)
        a, name_list = names_and_extraction(original, extract, log)
        raw_data, forma = map_script(a, extract, os.path.join(root, 'scripts'), log)
        details['forma'] = forma
        body_text = re.sub(r'\r(?!\n)', '\n', open(raw_data, 'rb').read().decode('latin-1'))
        diag = diagnostico(body_text, extract)
        details['diagnostico'] = diag
        log('3. diagnosis: %d platform natives (%d with a body in the layer), %s, %s data'
            % (len(diag['plataforma']), len(diag['implemented_count']), 'M16/JN' if diag['jn'] else 'KK',
               'SLK' if diag['slk'] else 'w3u'))
        blz, _pair = map_part(root, compat, extract, raw_data, body_text, diag, heading, log)
        import name_without_dot
        listing = name_without_dot.map_models(set(name_list))
        r = receita(root, raw_data, diag, blz, listing, heading)
        log('5. the script chain (this is the long step)')
        ok, g1, g2, log_cadeia = run_chain(r)
        if not ok:
            error_list = pjass_errors(log_cadeia)
            if error_list and all(any(x in e for x in PJASS_RUNTIME_ONLY) for e in error_list) and \
                    os.path.isfile(os.path.join(r.OUT, 'war3map.j')):
                WARNINGS.append("pjass found only run-time problems of the map's own code, which the old game had too "
                                "(the script loads): %s" % '; '.join(error_list[:4]))
                ok = g1 = g2 = True
        details.update(g1=g1, g2=g2)
        m = re.search(r'(?m)^WARNING 3n: (\d+) interface event record', log_cadeia)
        if m:
            WARNINGS.append('%s interface event registration(s) get the handler through a variable: they run on every '
                            'machine, without the local-only wrapper (check those menus in game)' % m.group(1))
        m = re.search(r'(?m)^AVISO: (\d+) funcao\(oes\) da camada com o nome de uma funcao do mapa[^:]*: (.*)$',
                      log_cadeia)
        if m:
            WARNINGS.append(
                "%s function(s) of the map have the name of a port layer function; the map's own are kept: %s"
                % (m.group(1), m.group(2).split(': ', 1)[-1])
            )
        m0f = re.search(r'0f dead type: (\d+) type', log_cadeia)
        decl, order = __import__('layer').map_native_declarations(raw_data)
        details['dead_type'] = dead_type.applies(body_text, dead_type.engine_types(
            open(os.path.join(new.REF, 'common.j'), 'rb').read().decode('latin-1')))[1] if m0f else {}
        details['stubs'] = stubs_and_dependents(r, order)
        log('   G1 %s | G2 %s; %d stub(s) called by the map' % ('PASS' if g1 else 'FAIL', 'PASS' if g2 else 'FAIL',
                                                              len(details['stubs'])))
        if not ok:
            error_list = pjass_errors(log_cadeia)
            details['pjass'] = error_list
            if any('Index missing for array variable' in e for e in error_list):
                raise Aborts('the map uses a JASS memory exploit (an array read as a value: the typecast of the '
                             'patch 1.2x memory hacks), which Reforged blocks: %s' % error_list[0])
            if error_list and all(e.startswith('Cannot convert returned value from') for e in error_list):
                raise Aborts('the map uses the JASS return bug (a function that returns a value of another type: the '
                             'typecast of patch 1.2x), which Reforged blocks: %s' % '; '.join(error_list[:3]))
            raise Aborts('the compiler gates did not pass (G1 %s, G2 %s): %s'
                         % ('PASS' if g1 else 'FAIL', 'PASS' if g2 else 'FAIL', '; '.join(error_list[:3]) or
                            os.path.join(root, 'port', 'out', 'cadeia.log')))
        if pacotes:
            import art_packs
            script = open(os.path.join(r.OUT, 'war3map_pre_injecao.j'), 'rb').read().decode('utf-8', 'surrogateescape')
            arte, _s = _muted(art_packs.import_it, original, list(pacotes), script, os.path.join(r.OUT, 'arte'),
                              data_bytes=os.path.join(r.DATA, 'Units'), extract=extract, log=lambda s: None)
            if isinstance(arte, SystemExit):
                WARNINGS.append('the art packages could not be read: %s' % arte)
            else:
                art_packs.write_manifest(arte, os.path.join(root, 'port', 'out', 'arte_manifesto.tsv'))
                details['arte'] = {
                    'imported': arte['imported'],
                    'bytes': arte['bytes'],
                    'missing_items': len(arte['missing_items']),
                    'by_pack': arte['by_pack'],
                }
                WARNINGS.extend(arte['warnings'][:20])
                log('6. art from %d package(s): %d file(s) imported, %d still missing'
                    % (len(pacotes), arte['imported'], len(arte['missing_items'])))
        to_remove = ['kkmap.jc'] if forma == 'kkwe' else (['war3map.bin'] if forma == 'j2b' else [])
        scripts_folder = scripts_folder_files(original, name_list)
        if scripts_folder:
            to_remove += scripts_folder
            log('6. the Scripts folder of the original removed: %s' % ', '.join(scripts_folder))
        sz, slack, entrou = build_w3x(original, output, r, to_remove, listing, log, name_list=name_list)
        if slack < 0 and shrink_large:
            sz, slack = shrinks(output, sz, log)
        details.update(output=output, bytes=sz, slack=slack, file_set=entrou,
                       resultado='ported' if slack >= 0 else 'ported, but above the 512 MiB the game opens')
    except Aborts as e:
        details['err'] = str(e)
    except Exception as e:
        import traceback
        details['err'] = '%s: %s' % (type(e).__name__, e)
        details['traceback'] = traceback.format_exc()[-2000:]
    details['segundos'] = round(time.time() - t0, 1)
    return _closes(details, stats, log)


def _closes(details, stats, log):
    details['stats'] = stats
    try:
        with open(stats, 'w', encoding='utf-8', newline='\r\n') as f:
            f.write(report_text(details))
    except OSError as e:
        details['report_error'] = str(e)
    log('%s%s' % (details['resultado'], (': ' + details['err']) if details.get('err') else ''))
    return details
