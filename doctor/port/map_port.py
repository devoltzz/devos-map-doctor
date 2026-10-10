# Ports a KK or M16 platform map to Warcraft III 3.0 in one run, with a report of what is left.
import collections
import contextlib
import io
import json
import os
import re
import hashlib
import time

from doctor.mpq import mpqread
from doctor.port import new
from doctor.port import dead_type

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
    from doctor.fix import unprotect
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
    from doctor.triggers import triggerdata
    ref = os.path.join(root, 'ref')
    for f in REF_FILES:
        t = triggerdata.game_script(f)
        if not t:
            raise Aborts('the game script %s could not be read: the port needs Warcraft III 3.0 installed' % f)
        _writes(os.path.join(ref, f), t.encode('utf-8', 'surrogateescape'))
    from doctor.port import blizzard_map
    from doctor.port import layer
    from doctor.port import lbkkapi
    from doctor.script import pjass
    new.REF = layer.REF_30 = pjass.REF_30 = blizzard_map.REF_30 = lbkkapi.REF_30 = ref
    log('0. the game scripts read from the installed Warcraft III')
    return ref


def lua_route(a, raw_data, body_text, scripts_dir, log):
    from doctor.script import ydwe_lua
    from doctor.port import ydwe_modules
    from doctor.port import ydwe_port
    finding = ydwe_lua.detect(body_text)
    if not finding:
        return None, raw_data, body_text
    col = ydwe_modules.collect(a, finding['entries'], log=log)
    if not col['lua_modules']:
        finding['modules'] = []
        msg = ('the map calls the YDWE Lua engine (%s) but its Lua modules are not in the archive, so there is nothing '
               'to port' % ', '.join(finding['entries'][:6]))
        if finding['all_lua']:
            raise Aborts(msg)
        WARNINGS.append(msg + '; the rest of the map (its JASS) runs')
        return None, raw_data, body_text
    largest_dll = max([len(d) for _b, d in col['dll']] or [0])
    if finding['all_lua'] and len(col['lua_modules']) <= 3 and largest_dll >= (1 << 20):
        raise Aborts('the game of this map is native code in a DLL the map ships (%.1f MB), loaded by its Lua (%s): '
                     'Reforged cannot load a DLL, so the ported map would start and nothing would happen'
                     % (largest_dll / 1048576.0, ', '.join(sorted(col['lua_modules'])[:3])))
    body_text, added = ydwe_port.declare_natives(body_text, col['lua_modules'], log)
    col['originals'] = ydwe_modules.originals(a, body_text, col)
    if col['originals']:
        log('   %d file(s) of the original the script hashes by name (its tamper check): %s'
            % (len(col['originals']), ', '.join(sorted(col['originals'])[:6])))
    new_raw = os.path.join(scripts_dir, 'war3map.j')
    if added or os.path.normcase(os.path.abspath(raw_data)) != os.path.normcase(os.path.abspath(new_raw)):
        _writes(new_raw, body_text.encode('latin-1'))
        raw_data = new_raw
    log('2b. the YDWE Lua engine: entries %s; %d Lua module(s) found, %d without a name; the map is ported as a Lua '
        'map' % (', '.join(finding['entries'][:6]), len(col['lua_modules']), len(col['unnamed'])))
    if col['unnamed']:
        WARNINGS.append('%d Lua block(s) of the map could not be named (no debug name, no name the Lua cites): if a '
                        'module loads one of them by a name built at run time, that part does not run'
                        % len(col['unnamed']))
    return {'finding': finding, 'collect': col, 'natives': added}, raw_data, body_text


def own_scripts(extract, name_list=('blizzard.j',)):
    out = []
    for d in os.listdir(extract) if os.path.isdir(extract) else ():
        folder = os.path.join(extract, d)
        if d.lower() != 'scripts' or not os.path.isdir(folder):
            continue
        for f in os.listdir(folder):
            if f.lower() in name_list:
                out.append(open(os.path.join(folder, f), 'rb').read().decode('latin-1'))
    return out


def ujapi_route(extract, raw_data, body_text, scripts_dir, log):
    from doctor.port import ujapi
    new_text, info = ujapi.prepare(body_text, extras=own_scripts(extract))
    if not info:
        return None, raw_data, body_text
    new_raw = os.path.join(scripts_dir, 'war3map.j')
    _writes(new_raw, new_text.encode('latin-1'))
    log(
        '2c. UjAPI map (the Unryze JASS API %s): %d native(s) declared for the layer, %d constant(s) and %d type(s) '
        'mapped to Reforged'
        % (info['version_num'], len(info['natives']), len(info['w3p_constants']), len(info['types']))
    )
    WARNINGS.extend(ujapi.warnings(info, new_text))
    return info, new_raw, new_text


def build_lua_route(r, lua, original, extract, log, details):
    from doctor.port import ydwe_port
    from doctor.port import slk_tables
    final = open(os.path.join(r.OUT, 'war3map.j'), 'rb').read().decode('utf-8', 'surrogateescape')
    slk_lua = ''
    try:
        _mode_of, u, ab, it = slk_tables.build_auto_tables(extract)
        file_path = os.path.join(r.OUT, 'slk_data.lua')
        _muted(slk_tables.write_lua, file_path, u, ab, it)
        slk_lua = open(file_path, 'rb').read().decode('utf-8', 'surrogateescape')
    except Exception as e:
        WARNINGS.append('the object data tables of jass.slk could not be built (%s: %s): the Lua reads empty tables'
                        % (type(e).__name__, e))
    lado = os.path.join(r.OUT, 'layer_stubs.json')
    stubs = json.load(open(lado, encoding='utf-8')) if os.path.isfile(lado) else []
    body_text, info = ydwe_port.build_lua(
        final,
        lua['collect'],
        slk_lua,
        log=log,
        extract=extract,
        scale_factors=lua.get('scale_factors'),
        translation=lua.get('translation'),
        stubs=stubs,
    )
    if info['translation_errors']:
        WARNINGS.append('%d Lua module(s) could not be translated from bytecode: %s'
                        % (len(info['translation_errors']), '; '.join(info['translation_errors'][:4])))
    if not ydwe_port.has_lua():
        WARNINGS.append(
            'the Lua script of the port was not checked (no Lua 5.3 here: pip install lupa), and Lua modules '
            'with Chinese identifiers stay as they are, which Reforged does not load'
        )
    err = ydwe_port.verify(body_text)
    if err:
        _writes(os.path.join(r.OUT, '_war3map_falha.lua'), body_text.encode('utf-8', 'surrogateescape'))
        raise Aborts('the Lua script of the port %s' % err)
    lua_p = os.path.join(r.OUT, 'war3map.lua')
    _writes(lua_p, body_text.encode('utf-8', 'surrogateescape'))
    w3i = mpqread.Archive(original).read('war3map.w3i')
    if not w3i:
        raise Aborts('the map has no war3map.w3i to switch the script language to Lua')
    w3i_p = os.path.join(r.OUT, 'war3map.w3i')
    _writes(w3i_p, ydwe_port.w3i_lua(w3i))
    details['lua'] = {'lua_modules': info['lua_modules'], 'functions': info['functions'], 'bytes': info['bytes'],
                      'unnamed': len(lua['collect']['unnamed']), 'declared_natives': len(lua['natives']),
                      'hash_entries': lua['finding']['entries']}
    log('5b. war3map.lua: %d JASS function(s), %d Lua module(s), %.1f MB; checked (compiles, the main chunk loads)'
        % (info['functions'], info['lua_modules'], info['bytes'] / 1048576.0))
    output = [('war3map.lua', lua_p), ('war3map.w3i', w3i_p)]
    textures = []
    try:
        generated = ydwe_port.generated_files(lua_p, log=log, extract=extract, textures=textures)
    except Exception as e:
        generated = {}
        WARNINGS.append('the frame definitions the map writes at run time could not be collected (%s: %s): its custom '
                        'interface may not show' % (type(e).__name__, e))
    missing_ones = (
        ydwe_port.missing_textures(textures, extract, generated, log=log, map_path=mpqread.Archive(original))
        if textures
        else []
    )
    if missing_ones:
        generated[ydwe_port.TRANSPARENT] = ydwe_port.transparent_tga()
        body_text += ydwe_port.missing_table(missing_ones)
        _writes(lua_p, body_text.encode('utf-8', 'surrogateescape'))
        log('   %d texture path(s) the map puts on its frames exist neither in the map nor in the game: drawn '
            'transparent (%s)' % (len(missing_ones), ', '.join(missing_ones[:8])))
        details['lua']['missing_textures'] = missing_ones
    if generated:
        folder = os.path.join(r.OUT, 'generated')
        os.makedirs(folder, exist_ok=True)
        for fname, data_bytes in sorted(generated.items()):
            p = os.path.join(folder, fname.replace('\\', '__').replace('/', '__'))
            _writes(p, data_bytes)
            output.append((fname, p))
        log('   %d file(s) the map writes at run time (frame definitions) put in the map: %s'
            % (len(generated), ', '.join(sorted(generated))))
        details['lua']['generated'] = sorted(generated)
    return output


def names_and_extraction(map_path, extract, log):
    from doctor.fix import unprotect
    from doctor.port import new_port
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
    from doctor.script import kkwe as _kkwe
    from doctor.script import kkwe_decompile
    from doctor.triggers import triggerdata
    common, blizzard = triggerdata.game_script('common.j'), triggerdata.game_script('blizzard.j')
    if not common or not blizzard:
        raise Aborts('the map script is compiled bytecode and the game scripts (common.j, Blizzard.j) could not be '
                     'read: Warcraft III has to be installed to decompile it')
    if j2b:
        from doctor.script import j2b as _j2b
        data_bytes = a.read('war3map.bin')
        if not data_bytes:
            raise Aborts('the war3map.j loads war3map.bin, which is missing')
        try:
            from doctor.script import j2b_calls as _j2b_calls
            bc = _j2b.bytecode(data_bytes, reference=_j2b_calls.reference_texts(common, blizzard, raw_bytes))
        except _j2b.J2bError as e:
            raise Aborts('war3map.bin: %s' % e)
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
    grafts = details.get('grafts_of') or []
    if grafts:
        WARNINGS.append(
            '%d function(s) of the compiled script were made by another compiler and pasted in later (%s): '
            'they came back to JASS checked statement by statement, not instruction by instruction. Check '
            'what they do: on one map they were chat commands that give gold' % (len(grafts), ', '.join(grafts[:6]))
        )
    constant_calls = details.get('constant_calls') or {}
    if constant_calls:
        WARNINGS.append(
            '%d call(s) in %d function(s) had been replaced by constants inside the compiled script (%s): the '
            'map evaluates their arguments and uses a fixed value instead of calling. They came back to JASS '
            'as that constant, checked statement by statement'
            % (sum(constant_calls.values()), len(constant_calls), ', '.join(sorted(constant_calls)[:6]))
        )
    compared = details.get('constant_comparisons') or {}
    if compared:
        WARNINGS.append('%d comparison(s) in %d function(s) had been replaced by a constant inside the compiled script '
                        '(%s): they came back to JASS as that constant, checked statement by statement'
                        % (sum(compared.values()), len(compared), ', '.join(sorted(compared)[:6])))
    removed = details.get('removed_conditions') or {}
    if removed:
        WARNINGS.append('%d if(s) in %d function(s) had their condition removed from the compiled script (%s): their '
                        'block always runs. They came back to JASS that way, checked statement by statement'
                        % (sum(removed.values()), len(removed), ', '.join(sorted(removed)[:6])))
    from doctor.fix import editor_prep
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
    from doctor.port import field_table
    from doctor.port import slk_dynamic
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


def map_part(root, compat, extract, raw_data, body_text, diag, heading, log, memory_hacks=None):
    for p in new.inclusion_points():
        _writes(os.path.join(compat, 'kk_%s.j' % p), b'')
    value_list = {'NOME': heading, 'DATA': time.strftime('%d/%m/%Y'),
                  'N_SEQ': len(re.findall(r'\b(?:DzSetEffectAnimation|EXSetEffectAnimation)\s*\(', body_text)),
                  'N_ANIM': len(re.findall(r'\bSetUnitAnimationByIndex\s*\(', body_text))}
    new.save(os.path.join(compat, 'out_seqs.j'), new.model('out_seqs.j', value_list))
    new.save(os.path.join(compat, 'out_anim_names.j'), new.model('out_anim_names.j', value_list))
    blz = False
    own = dict((f.lower(), os.path.join(extract, d, f)) for d in os.listdir(extract)
               if d.lower() == 'scripts' and os.path.isdir(os.path.join(extract, d))
               for f in os.listdir(os.path.join(extract, d)))
    from doctor.port import blizzard_map
    if 'blizzard.j' in own:
        without_127 = not os.path.isfile(blizzard_map.VANILLA)
        base = os.path.join(new.REF, 'blizzard.j') if without_127 else None
        blz_part, blz_info = blizzard_map.extract_parts(own['blizzard.j'], raw_data, vanilla=base)
        failures = [] if without_127 else blizzard_map.failures_of(blz_info)
        if failures:
            WARNINGS.append(
                "the map's own Scripts\\Blizzard.j changes functions of the game, and Reforged uses its own: "
                + ' | '.join(failures)[:400]
            )
        if blz_part and memory_hacks:
            from doctor.port import lbkkapi
            from doctor.port import memory_hacks as _memhacks
            blz_part, info_mem = _memhacks.applies(blz_part, lbkkapi.read_reference(), equivalents=True,
                                                   neutralize=(memory_hacks == 'neutralize'), suffix='_b')
            memory_warnings(info_mem)
        if blz_part:
            new.save(os.path.join(compat, 'out_blizzard_mapa.j'), blz_part)
            blz = True
    engine_lines = [
        m.group(0).strip() for m in new.RX_NATIVE.finditer(body_text) if m.group(1) in diag['engine_outside']
    ]
    new.save(os.path.join(compat, 'part_0_map_natives.j'),
             '// the engine natives the map declares\n' + ''.join(line + '\n' for line in engine_lines))
    from doctor.port import channel_table
    _v, output = _muted(channel_table.gera, extract, os.path.join(compat, 'out_profile_slots.j'), 'auto')
    if (_v.code if isinstance(_v, SystemExit) else _v):
        raise Aborts('the save channel table: %s' % re.sub(r'\s*\n\s*', ' | ', output.strip()[-300:]))
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
        'KK_UI_MSG': 'true',
        'KK_Z_4': 'true',
        'KK_EST_14': new.reads_state_14(body_text),
        'KK_UI_ALFA': new.ui_alpha(body_text),
        'KK_SYNC_VAZIO': new.empty_sync(body_text),
    }
    pair['KK_UI_SISTEMA'] = 'true'
    pair['KK_UI_CICLO'] = 'true'
    pair['KK_UI_MOUSE_POS'] = new.ui_mouse_pos(body_text)
    pair['KK_UI_BORDAS'] = new.ui_borders(body_text)
    pair['KK_UI_RETRATO'] = new.ui_portrait(body_text)
    atk = new.covered_attack(extract)
    pair['KK_CMD_ATAQUE'] = 'true' if atk else 'false'
    if atk:
        pair['KK_CMD_ATAQUE_LISTA'] = atk[:1000].rsplit(',', 1)[0] if len(atk) > 1000 else atk
    pair['KK_EST_VIDA_GRANDE'] = new.big_life(extract)
    pair['KK_DZ_REAL'] = 'true'
    pair['KK_SRV_BACKEND'] = 'true'
    pair.update(new.hero_xp(extract, body_text))
    key_codes = new.queried_keys(body_text)
    pair['KK_TECLAS'] = 'true' if key_codes else 'false'
    if key_codes:
        pair['KK_TECLAS_LISTA'] = key_codes
    buttons = new.fdf_buttons(extract, body_text)
    pair['KK_UI_BOTOES'] = 'true' if buttons else 'false'
    if buttons:
        pair.update(new.buttons_in_chunks(buttons))
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
            'KK_JN_USE': new.jnuse_gate(body_text), 'KK_JN_CONEXAO': "'BNET'", 'KK_JN_HOST': 'false',
            'KK_JN_INIT_ZERO': new.jninit_gate(body_text),
            'KK_JN_PLUGIN': 'true' if new.jnplugin_gate(body_text) is not None else 'false',
            'KK_JN_INIT2': 'true' if re.search(r'\bnative\s+JNObjectUserInit2\b', body_text) else 'false',
            'KK_JN_REGEX': new.jnregex_gate(body_text),
            'KK_JN_CARTAO': new.card_gate(body_text),
        })
        pair.update(dict((k, v) for k, v in new.JN_PARAMETERS.items() if not k.startswith('_')))
        if new.jnplugin_gate(body_text) is not None:
            pair['KK_JN_PLUGIN_VER'] = str(new.jnplugin_gate(body_text))
        new.save(os.path.join(compat, 'kk_sv_prepara_tde.j'), '    call KKJN_init()\n')
    new.save(os.path.join(root, 'port', 'kk_parametros.json'), json.dumps(pair, ensure_ascii=False, indent=1) + '\n')
    log('4. the map part of the layer: %d natives of the engine, save folder %r%s'
        % (len(engine_lines), pair['KK_SAVE_RAIZ'], ' (M16 route)' if diag['jn'] else ''))
    return blz, pair


def recipe(root, raw_data, diag, blz, no_dot_name_list, heading):
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
        PARTS=new.layer_parts(bool(diag['jn']), blz, bool(diag.get('ujapi'))),
        EXPECTED=dict(new.EMPTY_EXPECTED),
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
        from doctor.port import slk_data

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
        from doctor.port import classic_data
        if no_dot_name_list:
            WARNINGS.append(
                '%d model(s) with dots in the name: the script now loads the copies Reforged accepts, but the '
                'object data (w3u/w3t/w3a...) still asks for the dotted names, which Reforged does not load; '
                'change those model paths in the object editor: %s'
                % (len(no_dot_name_list), '; '.join(sorted(no_dot_name_list))[:300])
            )
        regras = tuple((file_, entry, obj_kind, dict((c, None) for c in locks))
                       for file_, entry, obj_kind, locks in
                       classic_data.regras_padrao(extract, os.path.join(root, 'port', 'out', 'extract_en')))

        def _pixel_data():
            return classic_data.applies(regras, root, data_bytes, expected_count=None, write_out=True)
        r.data_report = classic_data.report_data
    r.data_bytes = _pixel_data
    return r


def run_chain(r):
    from doctor.port import chain
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
    if isinstance(v, SystemExit) and not g:
        code_part = v.code
        raise Aborts(
            'the script chain stopped: %s'
            % (
                code_part
                if isinstance(code_part, str) and code_part.strip()
                else 'exit %s: %s' % (code_part, re.sub(r'\s*\n\s*', ' | ', output.strip()[-300:]))
            )
        )
    return ok, g1, g2, output


PJASS_RUNTIME_ONLY = ('is uninitialized', 'String literals over 1023 chars')
RX_PJASS_LINE = re.compile(r'(?m)^(?:.*?[\\/\s])?(?:war3map|blizzard)\.j:\d+(?: \(de \d+\))?: (.+)$')
RX_PJASS_TOTAL = re.compile(r'Parse failed: (\d+) errors? total')


def pjass_errors(chain_log):
    seen = []
    for m in RX_PJASS_LINE.finditer(chain_log):
        if m.group(1).strip() not in seen:
            seen.append(m.group(1).strip())
    return seen


def only_execution_errors(chain_log):
    line_list = [m.group(1).strip() for m in RX_PJASS_LINE.finditer(chain_log)]
    total = sum(int(x) for x in RX_PJASS_TOTAL.findall(chain_log))
    return bool(line_list) and total == len(line_list) and 'IGNORED by the pragma' not in chain_log and \
        all(any(x in e for x in PJASS_RUNTIME_ONLY) for e in line_list)


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


def build_w3x(original, output, r, to_remove, no_dot_list, log, name_list=(), script=None):
    from doctor.port import map_path
    from doctor.port import name_without_dot
    item_entries = list(script) if script else [('war3map.j', os.path.join(r.OUT, 'war3map.j'))]
    by_name = {}
    for folder in (os.path.join(r.OUT, 'arte'), r.DATA):
        if os.path.isdir(folder):
            for base, _d, fs in os.walk(folder):
                for f in sorted(fs):
                    p = os.path.join(base, f)
                    n = os.path.relpath(p, folder).replace(os.sep, '\\')
                    if n.lower() not in ('war3map.j', 'war3map.w3i', 'war3map_src.j', 'war3map.lua'):
                        by_name[n.lower()] = (n, p)
    item_entries.extend(by_name[k] for k in sorted(by_name))
    copies, gaps = name_without_dot.copies(mpqread.Archive(original), no_dot_list)
    if gaps:
        WARNINGS.append('%d model(s) with dots in the name could not be copied under a name Reforged loads: %s'
                        % (len(gaps), '; '.join(gaps)[:300]))
    item_entries.extend(copies)
    entra = [
        (n, v) for n, v, status_kind, _t in map_path.classify_items(item_entries, original) if status_kind != 'equal'
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
    from doctor.fix import shrink
    smaller = os.path.splitext(output)[0] + '.small' + os.path.splitext(output)[1]
    log('6. the map is above 512 MiB: making it smaller, losing nothing (this is slow)')
    r, _s = _muted(shrink.shrink, output, smaller)
    if isinstance(r, dict) and r.get('state') == 'done' and os.path.isfile(smaller):
        os.replace(smaller, output)
        sz = os.path.getsize(output)
        WARNINGS.append('the map was above 512 MiB and was made smaller without loss: %.1f MiB' % (sz / 1048576.0))
    elif os.path.exists(smaller):
        os.remove(smaller)
    return sz, TETO - sz


RX_TRIG = re.compile(r'^Trig_(.+?)_?(?:Actions|Conditions|Func\d+\w*)$')


def stubs_and_dependents(r, decl_order):
    lado = os.path.join(r.OUT, 'layer_stubs.json')
    if os.path.isfile(lado):
        stubs = set(json.load(open(lado, encoding='utf-8')))
    else:
        layer_text = open(os.path.join(r.OUT, 'camada.j'), 'rb').read().decode('latin-1')
        i = layer_text.find('STUBS:')
        stubs = set(re.findall(r'(?m)^function\s+(\w+)\s+takes', layer_text[i:])) if i >= 0 else set()
    stubs &= set(decl_order)
    if not stubs:
        return []
    pre = open(os.path.join(r.OUT, 'war3map_pre_injecao.j'), 'rb').read().decode('latin-1')
    fs = dead_type.functions(pre)
    alive = dead_type.live_ones(pre, fs)
    rx = re.compile(r'\b(%s)\s*\(' % '|'.join(map(re.escape, sorted(stubs))))
    who = {}
    for f, a, b in fs:
        if f in alive:
            for n, k in collections.Counter(rx.findall(pre[a:b])).items():
                who.setdefault(n, {})[f] = k
    out = []
    for n in sorted(who):
        trigger_list = sorted(set(m.group(1).rstrip('_') for f in who[n] for m in [RX_TRIG.match(f)] if m))
        out.append(
            {'native': n, 'calls': sum(who[n].values()), 'functions': sorted(who[n]), 'trigger_list': trigger_list}
        )
    out.sort(key=lambda x: (-x['calls'], x['native']))
    return out


def speed_cap(r, extract, body_text, log):
    requested = new.speed_cap(body_text)
    if not requested:
        return None
    from doctor.port import int32_balance
    raw, origin = None, None
    for folder in (r.DATA, os.path.join(r.ROOT, 'port', 'out', 'extract_en'), extract):
        p = int32_balance._find_ci(folder, ['war3mapMisc.txt']) if os.path.isdir(folder) else None
        if p and os.path.getsize(p):
            raw, origin = open(p, 'rb').read(), p
            break
    txt = raw.decode('utf-8', 'surrogateescape') if raw else ''
    before, sec = 522.0, None
    for ln in txt.split('\n'):
        s = ln.strip()
        m = re.match(r'^\[(.+)\]$', s)
        if m:
            sec = m.group(1).strip().lower()
        elif sec == 'misc' and s.split('=', 1)[0].strip() == 'MaxUnitSpeed' and '=' in s:
            try:
                before = float(s.split('=', 1)[1].strip())
            except ValueError:
                pass
    info = {'requested': requested, 'before': before, 'saved': requested > before}
    if info['saved']:
        dest = origin if origin and os.path.dirname(origin) == r.DATA else os.path.join(r.DATA, 'war3mapMisc.txt')
        _writes(dest, int32_balance._misc_text(txt, {'MaxUnitSpeed': requested}).encode('utf-8', 'surrogateescape'))
        log('5. the movement speed cap: MaxUnitSpeed %g -> %g (the map raised it through the memory of patch 1.28)'
            % (before, requested))
    return info


def close_toc(r, extract, log):
    out = []
    for base, _d, fs in os.walk(extract):
        for f in sorted(fs):
            if not f.lower().endswith('.toc'):
                continue
            p = os.path.join(base, f)
            data_bytes = open(p, 'rb').read()
            if not data_bytes.strip():
                continue
            if b'\r\n' in data_bytes:
                if data_bytes.endswith(b'\r\n'):
                    continue
                new_t = data_bytes.rstrip(b'\r\n') + b'\r\n'
            elif b'\n' in data_bytes:
                if data_bytes.endswith(b'\n\n'):
                    continue
                new_t = data_bytes.rstrip(b'\r\n') + b'\n\n'
            else:
                new_t = data_bytes + b'\r\n\r\n'
            rel_name = os.path.relpath(p, extract)
            _writes(os.path.join(r.DATA, rel_name), new_t)
            out.append(rel_name.replace(os.sep, '\\'))
    if out:
        log('5. the TOC file(s) end their last line the way Reforged needs (without it the last FDF is skipped): %s'
            % ', '.join(out))
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
                                  'UjAPI (the Unryze JASS API %s): %d native(s), %d constant(s) and %d type(s) of it '
                                  'mapped to Reforged' % (d['ujapi']['version_num'], d['ujapi']['natives'],
                                                          d['ujapi']['w3p_constants'], len(d['ujapi']['types']))
                                  if d.get('ujapi') else
                                  'KK (DzAPI/japi)' if d['plataforma'] else 'none'),
              '- object data: %s' % ('SLK tables' if d['slk'] else 'w3u/w3t/w3a over the game data'),
              '- platform natives declared: %d; implemented by the port layer: %d'
              % (len(d['plataforma']), len(d['implemented_count'])),
              '- EXExecuteScript sites: %d' % d['exec_sites']]
        fp = details.get('made_for')
        if fp and fp.get('label'):
            L.append('- made for: %s (%s)' % (fp['label'], (fp.get('reasons') or ['-'])[0]))
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
    vel = details.get('speed')
    if vel:
        L += ['', 'Movement speed cap', '-' * 18,
              ('- the map raised it to %g at run time through the memory of patch 1.28, which Reforged does not allow: '
               'MaxUnitSpeed is now %g in the gameplay constants (war3mapMisc.txt; it was %g)'
               % (vel['requested'], vel['requested'], vel['before'])) if vel['saved'] else
              ('- the map raises it to %g at run time; the gameplay constants already have MaxUnitSpeed %g'
               % (vel['requested'], vel['before']))]
    if details.get('numbers'):
        from doctor.port import int32_balance
        L += [''] + int32_balance.report_lines(details['numbers'])
    if details.get('warnings'):
        L += ['', 'Warnings', '-' * 8] + ['- ' + a for a in details['warnings']]
    if details.get('checks'):
        L += ['', 'Script checks of the ported script (handle leaks, start-up, globals never set)', '-' * 30] + [
            '- ' + a for a in details['checks']
        ]
    st = details.get('stubs')
    if st is not None:
        L += ['', 'Natives left as STUBS that the map CALLS (%d)' % len(st), '-' * 44]
        if not st:
            L.append('- none: every platform native the map calls has a body in the port layer')
        for s in st:
            L.append('- %s: %d call(s) in %s%s' % (
                s['native'], s['calls'], ', '.join(s['functions'][:6]) + (' ...' if len(s['functions']) > 6 else ''),
                ('; trigger(s): ' + ', '.join(s['trigger_list'][:6])) if s['trigger_list'] else ''))
        if st:
            L.append('A stub compiles and returns the neutral value (0, false, "", null): implement the native, or '
                     'change what depends on it, if that part of the map matters.')
    if not details.get('output'):
        return '\n'.join(L) + '\n'
    L += ['', 'Check in game', '-' * 13,
          '- the save and the load (the platform save became a local save in CustomMapData); two players, to see that '
          'loading does not desync',
          '- the menus and panels the platform drew (shop, lobby, F-keys) and the map frames (DzFrame -> BlzFrame)',
          '- every feature listed under the stubs above']
    if d and d.get('ujapi'):
        L += ['- the UjAPI parts: the frames, the damage and key events, and the objects Reforged has no type for '
              '(sprites, doodads, projectiles, handle lists) -- those natives are stubs and do nothing']
    return '\n'.join(L) + '\n'


RX_VERSION = re.compile(r'(?i)[\s_.-]+(?:v?\d[\w.]*|fix\w*|beta\w*|test\w*|event|ver\w*|final|kr\w*|cn|en|e\d\w*|'
                        r'\[[^\]]*\]|\([^)]*\))$')
RX_GLUED = re.compile(r'(?<![\s_.-][vV])(?<=[A-Za-z])\d+(?:\.\d+)+\w*$')


def port_checks(original, output, details):
    try:
        from doctor.fix import uabi_runtime
        u = uabi_runtime.scan(original)
        if u.get('risky'):
            WARNINGS.append('the unit types carry %d distinct abilities in their normal ability lists (uabi): players '
                            'report that about 2,000 drop games on Reforged; "Fix map" can move the lists to the script'
                            % u['distinct'])
    except Exception:
        pass
    try:
        from doctor.script import script_checks
        sc = script_checks.check(output)
        if sc.get('language') == 'jass' and not sc.get('error'):
            details['checks'] = sc['lines']
    except Exception:
        pass


def made_for(extract, body_text):
    try:
        from doctor.data import wc3_versions
        w3i = os.path.join(extract, 'war3map.w3i')
        data_bytes = open(w3i, 'rb').read() if os.path.isfile(w3i) else None
        return wc3_versions.detect_parts(data_bytes, body_text, 'jass')
    except Exception:
        return None


def name_warnings(info):
    if not info:
        return
    born_at = dict((n, (p, d)) for n, _e, p, d in info.get('born') or [])

    def label(n):
        p, d = born_at.get(n, (None, False))
        return '%s (Reforged has it since %s)' % (n, p) if p and d else n
    name_list = [n for n in info.get('functions') or [] if not n.endswith('(reserved by pjass)')]
    name_list += [n for n, _t, _r in info.get('renamed_list') or []]
    if name_list:
        WARNINGS.append(
            '%d name(s) of the map are also names of the newer game (a native, function or global Reforged '
            'created after the map was made): the map\'s own were renamed to kkm_<name> everywhere, '
            'ExecuteFunc("...") included: %s' % (len(name_list), ', '.join(label(n) for n in name_list[:12]))
        )
    if info.get('removed_ones'):
        WARNINGS.append('%d global(s) the map declares with the same name and type as a Reforged constant were removed '
                        '(the map now uses the Reforged value): %s'
                        % (len(info['removed_ones']), ', '.join('%s (map %s, Reforged %s)' % (n, v or '-', r or '-')
                                                                for n, _t, v, r in info['removed_ones'][:8])))


def memory_warnings(info):
    if not info:
        return
    bridge = info.get('bridge') or {}
    if bridge.get('retyped_vars') or bridge.get('agents') or bridge.get('expressions'):
        pieces = []
        if bridge.get('retyped_vars'):
            pieces.append('%d variable(s), parameter(s) or return(s) that carried a handle disguised as another type '
                          'now have the real type (%s)' % (len(bridge['retyped_vars']), ', '.join(
                              '%s %s: %s -> %s' % x for x in bridge['retyped_vars'][:6])))
        if bridge.get('agents'):
            pieces.append('%d handle parameter(s) became agent so the handle table keeps the real handle for the '
                          'integer-to-handle casts (%s)' % (len(bridge['agents']), ', '.join(
                              '%s.%s' % x for x in bridge['agents'][:6])))
        if bridge.get('expressions'):
            pieces.append('%d return(s) of another type go through the handle table (%s)' % (
                len(bridge['expressions']), ', '.join(sorted(set(n for n, _d, _p in bridge['expressions']))[:8])))
        WARNINGS.append('the return bug of patch 1.23 and older was adapted: ' + '; '.join(pieces))
    if info.get('no_use'):
        WARNINGS.append('%d typecast function(s) of the return bug have no use left after that and only compile now: %s'
                        % (len(info['no_use']), ', '.join(info['no_use'][:12])))
    mh = info.get('memhack') or {}
    if mh.get('translated'):
        WARNINGS.append(
            '%d function(s) of the MemHackAPI (the patch 1.24-1.28 memory hack) now use the Reforged natives '
            'by what they do (frames, special effects, unit and ability fields): %s'
            % (len(mh['translated']), ', '.join(mh['translated'][:16]))
        )
    mu = info.get('memui') or {}
    if mu.get('translated') or mu.get('readings'):
        WARNINGS.append(
            'the memory UI library of the M16 maps (MemUI) now works through the DzAPI of the port layer and '
            'the Reforged natives: %d function(s) (%s) and %d direct read(s) of the mouse/window address; the '
            'game console, the buff bar, the textures and the game message frames stay where the game puts '
            'them (check the custom interface in game)'
            % (len(mu.get('translated') or []), ', '.join((mu.get('translated') or [])[:12]), mu.get('readings') or 0)
        )
    if info['conversions']:
        WARNINGS.append(
            '%d typecast function(s) of the patch 1.2x memory hacks (the return bug) now use the Reforged '
            'equivalent: %s' % (len(info['conversions']), ', '.join(n for n, _p, _r in info['conversions'][:12]))
        )
    if info['effects']:
        WARNINGS.append(
            '%d special effect function(s) the map wrote over the game memory now use the Reforged natives: %s'
            % (len(info['effects']), ', '.join(info['effects'][:12]))
        )
    lost_blocks = sorted(set(re.sub(r'^l__(\w+?)__MemoryBlock.*$', r'\1', n) for n in info['arrays']))
    neutral_expr = bridge.get('neutral_expr') or []
    if info['arrays'] or info['codes'] or info['neutrals'] or neutral_expr:
        WARNINGS.append(
            'the map reads and writes the memory of the patch 1.28 game (memory hacks), which Reforged does '
            'not have: %d memory address read(s), %d code reference(s) and %d typecast function(s) were '
            'neutralized, so what depended on that memory does not work%s; check those features in game'
            % (
                sum(info['arrays'].values()),
                len(info['codes']),
                len(info['neutrals']) + len(set(n for n, _d, _p in neutral_expr)),
                (' (' + ', '.join(lost_blocks[:10]) + ')')
                if lost_blocks
                else (' (' + ', '.join((info['neutrals'] + [n for n, _d, _p in neutral_expr])[:10]) + ')')
                if info['neutrals'] or neutral_expr
                else '',
            )
        )


def stable_title(fname):
    n = RX_GLUED.sub('', fname)
    while True:
        m = RX_VERSION.search(n)
        if not m or m.start() == 0:
            break
        n = RX_GLUED.sub('', n[:m.start()])
    without_version = re.sub(r'\s+', ' ', n.replace('_', ' ')).strip()
    n = re.sub(r'[^A-Za-z0-9 ]+', ' ', n.replace('_', ' ')).strip()
    n = re.sub(r'\s+', ' ', n) or re.sub(r'[^A-Za-z0-9]+', ' ', fname).strip()
    has_letter = bool(re.search(r'[A-Za-z]', n))
    if not has_letter or any(c.isalpha() and ord(c) > 127 for c in without_version):
        return (n if has_letter else 'Map') + hashlib.sha256(
            without_version.encode('utf-8', 'surrogateescape')
        ).hexdigest()[:8]
    return n


def map_port(map_path, work, output=None, stats=None, heading=None, log=print, packages=(), shrink_large=True,
             memory_hacks='neutralize', balance_numbers=False, lua_translation=None):
    t0 = time.time()
    map_path = os.path.abspath(map_path)
    base = os.path.splitext(map_path)[0]
    output = os.path.abspath(output or base + '_reforged.w3x')
    stats = stats or os.path.splitext(output)[0] + '.report.txt'
    heading = heading or stable_title(os.path.splitext(os.path.basename(map_path))[0])
    del WARNINGS[:]
    details = {'map_path': map_path, 'resultado': 'stopped', 'work': work, 'warnings': []}
    root = os.path.abspath(work)
    extract = os.path.join(root, 'port', 'extract')
    compat = os.path.join(root, 'port', 'kk', 'compat')
    try:
        if os.path.isdir(work) and os.listdir(work):
            raise Aborts('the work folder is not empty: %s' % work)
        for p in ('port/extract', 'port/tools/tr', 'port/kk/compat', 'port/analysis', 'port/out/kk', 'scripts'):
            os.makedirs(os.path.join(root, *p.split('/')), exist_ok=True)
        from doctor.script import pjass
        if not os.path.isfile(pjass.exe()):
            raise Aborts('pjass.exe was not found (%s): the port checks the script with it '
                         '(https://github.com/lep/pjass)' % pjass.exe())
        game_reference(root, log)
        original = map_path
        from doctor.mpq import mpqdoctor
        sp, _m, _u = mpqdoctor.is_sprotect(mpqread.Archive(original))
        if sp:
            from doctor.mpq import sprotect_fix
            sprotect_fix.CRYPT = sprotect_fix.init_crypt()
            original = os.path.join(root, 'sprotect_fix.w3x')
            v, _s = _muted(sprotect_fix.fix, map_path, original)
            if isinstance(v, SystemExit):
                raise Aborts('SProtect: %s' % v.code)
            log('0. SProtect undone')
        else:
            original = unprotected_result(map_path, root, log)
        a, name_list = names_and_extraction(original, extract, log)
        raw_data, forma = map_script(a, extract, os.path.join(root, 'scripts'), log)
        details['forma'] = forma
        body_text = re.sub(r'\r(?!\n)', '\n', open(raw_data, 'rb').read().decode('latin-1'))
        lua, raw_data, body_text = lua_route(a, raw_data, body_text, os.path.join(root, 'scripts'), log)
        uj, raw_data, body_text = ujapi_route(extract, raw_data, body_text, os.path.join(root, 'scripts'), log)
        diag = diagnostico(body_text, extract)
        if uj:
            diag['ujapi'] = {
                'version_num': uj['version_num'],
                'natives': len(uj['natives']),
                'w3p_constants': len(uj['w3p_constants']),
                'types': sorted(uj['types']),
            }
        details['diagnostico'] = diag
        details['made_for'] = made_for(extract, body_text)
        from doctor.port import memhack_ui
        details['memhack'] = memhack_ui.detect_memhack(body_text)
        mh_warning = memhack_ui.warning(details['memhack'])
        if mh_warning:
            WARNINGS.append(mh_warning)
        log('3. diagnosis: %d platform natives (%d with a body in the layer), %s, %s data'
            % (len(diag['plataforma']), len(diag['implemented_count']), 'M16/JN' if diag['jn'] else
               'UjAPI' if diag.get('ujapi') else 'KK',
               'SLK' if diag['slk'] else 'w3u'))
        blz, _pair = map_part(root, compat, extract, raw_data, body_text, diag, heading, log, memory_hacks=memory_hacks)
        from doctor.port import name_without_dot
        listing = name_without_dot.map_models(set(name_list))
        r = recipe(root, raw_data, diag, blz, listing, heading)
        r.MEMORY_LEVEL = memory_hacks
        from doctor.port import shadowed
        r.MAP_VERSION = shadowed.RANGE_CAP.get((details.get('made_for') or {}).get('range'))
        log('5. the script chain (this is the long step)')
        ok, g1, g2, chain_log = run_chain(r)
        if not ok:
            error_list = pjass_errors(chain_log)
            if error_list and only_execution_errors(chain_log) and os.path.isfile(os.path.join(r.OUT, 'war3map.j')):
                WARNINGS.append("pjass found only run-time problems of the map's own code, which the old game had too "
                                "(the script loads): %s" % '; '.join(error_list[:4]))
                ok = g1 = g2 = True
        details.update(g1=g1, g2=g2)
        m = re.search(r'(?m)^WARNING 3n: (\d+) interface event record', chain_log)
        if m:
            WARNINGS.append('%s interface event registration(s) get the handler through a variable: they run on every '
                            'machine, without the local-only wrapper (check those menus in game)' % m.group(1))
        m = re.search(
            r'(?m)^WARNING: (\d+) function\(s\) of the layer with the name of a function of the map[^:]*: (.*)$',
            chain_log,
        )
        if m:
            WARNINGS.append(
                "%s function(s) of the map have the name of a port layer function; the map's own are kept: %s"
                % (m.group(1), m.group(2).split(': ', 1)[-1])
            )
        m0f = re.search(r'0f dead type: (\d+) type', chain_log)
        decl, order = __import__('doctor.port.layer', fromlist=['layer']).map_native_declarations(raw_data)
        details['dead_type'] = dead_type.applies(body_text, dead_type.engine_types(
            open(os.path.join(new.REF, 'common.j'), 'rb').read().decode('latin-1')))[1] if m0f else {}
        details['stubs'] = stubs_and_dependents(r, order)
        memory_warnings(getattr(r, 'MEMORY_INFO', None))
        name_warnings(getattr(r, 'SHADOWED_INFO', None))
        log('   G1 %s | G2 %s; %d stub(s) called by the map' % ('PASS' if g1 else 'FAIL', 'PASS' if g2 else 'FAIL',
                                                              len(details['stubs'])))
        if not ok:
            error_list = pjass_errors(chain_log)
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
        details['speed'] = speed_cap(r, extract, body_text, log)
        details['toc'] = close_toc(r, extract, log)
        if details['toc']:
            WARNINGS.append('%d TOC file(s) got the line ending Reforged needs to load the last FDF of the list: %s'
                            % (len(details['toc']), ', '.join(details['toc'][:6])))
        if balance_numbers:
            from doctor.port import int32_balance
            details['numbers'] = int32_balance.port_step(r, extract, log)
            WARNINGS.extend(details['numbers'].get('warnings') or [])
            if lua and details['numbers'].get('state') == 'scaled':
                lua['scale_factors'] = dict(details['numbers'].get('factors') or {})
        if packages:
            from doctor.port import art_packs
            script = open(os.path.join(r.OUT, 'war3map_pre_injecao.j'), 'rb').read().decode('utf-8', 'surrogateescape')
            arte, _s = _muted(art_packs.import_it, original, list(packages), script, os.path.join(r.OUT, 'arte'),
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
                    % (len(packages), arte['imported'], len(arte['missing_items'])))
        to_remove = ['kkmap.jc'] if forma == 'kkwe' else (['war3map.bin'] if forma == 'j2b' else [])
        scripts_folder = scripts_folder_files(original, name_list)
        if scripts_folder:
            to_remove += scripts_folder
            log('6. the Scripts folder of the original removed: %s' % ', '.join(scripts_folder))
        script = None
        if lua:
            lua['translation'] = lua_translation
            script = build_lua_route(r, lua, original, extract, log, details)
            to_remove += [
                n for n in ('war3map.j', 'scripts\\war3map.j') if a.find(n) is not None and n not in to_remove
            ]
        sz, slack, entrou = build_w3x(original, output, r, to_remove, listing, log, name_list=name_list, script=script)
        if slack < 0 and shrink_large:
            sz, slack = shrinks(output, sz, log)
        port_checks(original, output, details)
        details.update(output=output, bytes=sz, slack=slack, file_set=entrou,
                       resultado='ported' if slack >= 0 else 'ported, but above the 512 MiB the game opens')
    except Aborts as e:
        details['err'] = str(e)
    except Exception as e:
        import traceback
        details['err'] = '%s: %s' % (type(e).__name__, e)
        details['traceback'] = traceback.format_exc()[-2000:]
    details['seconds'] = round(time.time() - t0, 1)
    details['warnings'] = list(WARNINGS)
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
