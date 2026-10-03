# Adds what the World Editor needs to open a protected or optimized map.
import os
import re
import struct
import shutil

import mpq_rebuild
import mpqadd
import mpqdoctor
import mpqnames
import mpqread
import w3i
import inflated_counts
import doodads
import duplicate_textures
import jpeg_flat
import skin_split
import wtg_triggers


CRLF = '\r\n'
RX_NATIVE = re.compile(r'^war3(map|campaign)(skin)?((\.(w[a-zA-Z0-9]{2}|doo|shd|mmp|j|imp))|misc\.txt|\.txt|map\.blp|'
                       r'units\.doo|extra\.txt)$', re.I)
SPECIAL_FILES = {'(listfile)', '(attributes)', '(signature)', 'scripts\\war3map.j', 'conversation.json'}
EDITOR_ESSENTIALS = ('war3map.wtg', 'war3map.wct', 'war3map.imp')
ENGINE_TEXTURES = ('Textures\\white.blp',)

EXTRA_JASSHELPER = b'[MapExtraInfo]\nEnableJassHelper=true\n\n'
KNOWN_W3I = 33


def enable_jasshelper(extra):
    if not extra:
        return EXTRA_JASSHELPER, True
    body_text = extra.decode('latin-1')
    eol = '\r\n' if '\r\n' in body_text else '\n'
    line_list = body_text.split(eol)
    for i, line in enumerate(line_list):
        if line.strip().lower().startswith('enablejasshelper='):
            if line.strip().lower() == 'enablejasshelper=true':
                return extra, False
            line_list[i] = 'EnableJassHelper=true'
            return eol.join(line_list).encode('latin-1'), True
    for i, line in enumerate(line_list):
        if line.strip().lower() == '[mapextrainfo]':
            line_list.insert(i + 1, 'EnableJassHelper=true')
            return eol.join(line_list).encode('latin-1'), True
    return (body_text.rstrip(eol) + eol + '[MapExtraInfo]' + eol + 'EnableJassHelper=true' + eol).encode(
        'latin-1'
    ), True


def fix_w3i(b, sobe=False):
    new, report, tail = _fix_w3i(b)
    if sobe:
        new, report = raise_w3i(new, report)
    return new, report, tail


W3I_RAISED_TO = 31
W3I_GDV_TFT = 1
W3I_MODES = 3


def raise_w3i(b, report):
    try:
        m = w3i.parse(b)
    except Exception:
        return b, report
    v = m['version']
    if v >= W3I_RAISED_TO:
        return b, report
    n_players = [(p['number'], p['type'], p['race'], p['fixed_start']) for p in m['players']]
    m['supported_modes'] = W3I_MODES
    m['game_data_version'] = W3I_GDV_TFT
    new = w3i.write(m, version=W3I_RAISED_TO)
    m2 = w3i.parse(new)
    if (m2['version'] != W3I_RAISED_TO or m2['game_data_version'] != W3I_GDV_TFT or m2.get('_tail')
            or [(p['number'], p['type'], p['race'], p['fixed_start']) for p in m2['players']] != n_players
            or w3i.write(m2) != new):
        raise ValueError('w3i v%d -> v%d: the new one does not round-trip' % (v, W3I_RAISED_TO))
    return new, '%s; v%d -> v%d, game_data_version %d (TFT), supported_modes %d (%d -> %d B)' % (
        report, v, W3I_RAISED_TO, W3I_GDV_TFT, W3I_MODES, len(b), len(new))


def _fix_w3i(b):
    try:
        m = w3i.parse(b)
        if w3i.write(m) == b and not m.get('_tail'):
            return b, 'intact (read with an exact round trip)', False
    except Exception:
        m = None
    v = struct.unpack_from('<i', b, 0)[0]
    if m is None and v > KNOWN_W3I:
        return b, 'new_version %d (an editor newer than the reader): left as is' % v, False
    if b[-1:] == b'\xff':
        n = 4 if v >= 25 else 3
        new = b[:-1] + b'\x00' * (4 * n)
        try:
            m = w3i.parse(new)
            if w3i.write(m) == new and not m.get('_tail'):
                return (
                    new,
                    'the truncated tail (0xFF) became %d zero counters (%d -> %d B)' % (n, len(b), len(new)),
                    True,
                )
        except Exception:
            pass
    m, deviations = w3i.parse_tolerant(b)
    type0 = [p for p in m['players'] if p['type'] == 0]
    if type0:
        m['players'] = [p for p in m['players'] if p['type'] != 0]
    new = w3i.write(m)
    m2 = w3i.parse(new)
    if w3i.write(m2) != new or m2.get('_tail'):
        raise ValueError('w3i version %d: the rewritten file does not round-trip yet' % v)
    return (
        new,
        (
            'rewritten in the editor format (%s%s; %d -> %d B)'
            % (
                ', '.join(deviations) or 'no deviations',
                '; %d player(s) of type 0 removed' % len(type0) if type0 else '',
                len(b),
                len(new),
            )
        ),
        bool({'tail_ff', 'truncated_tail'} & set(deviations)),
    )


def empty_w3r():
    return struct.pack('<ii', 5, 0)


def empty_w3c():
    return struct.pack('<ii', 0, 0)


def empty_w3s():
    return struct.pack('<ii', 3, 0)


def empty_mmp():
    return struct.pack('<ii', 0, 0)


def _game_is_132(b_w3i):
    if not b_w3i:
        return None
    try:
        gv = w3i.parse(b_w3i).get('game_version')
    except Exception:
        return None
    if not gv or len(gv) < 2:
        return None
    return (gv[0] * 100 + gv[1]) >= 132


def empty_units_doo(w3i_version=None, current=None, game_132=None):
    version_num, subversion, _skin = inflated_counts.units_layout(current, w3i_version, game_132)
    return b'W3do' + struct.pack('<iii', version_num, subversion, 0)


def single_category_wtg(fname='Map Script', index_=0):
    return (b'WTG!' + struct.pack('<ii', 7, 1) +
            struct.pack('<i', index_) + fname.encode('utf-8') + b'\x00' + struct.pack('<i', 0) +
            struct.pack('<ii', 2, 0) + struct.pack('<i', 0))


def wct(code, comment_text='', n_triggers=0):
    c = code.encode('latin-1')
    out = struct.pack('<i', 1) + comment_text.encode('utf-8') + b'\x00'
    out += (struct.pack('<i', len(c) + 1) + c + b'\x00') if c else struct.pack('<i', 0)
    return out + struct.pack('<i', n_triggers) + struct.pack('<i', 0) * n_triggers


def imp(name_list):
    out = struct.pack('<ii', 1, len(name_list))
    for n in name_list:
        out += b'\x0d' + n.encode('utf-8', 'surrogateescape') + b'\x00'
    return out


IMPORTED_FOLDER = 'war3mapImported\\'


def read_imp(b):
    return _read_imp(b)[:2]


def _read_imp(b):
    version_num, n = struct.unpack_from('<ii', b, 0)
    p, out = 8, []
    for _ in range(n):
        f = b.index(b'\0', p + 1)
        out.append((b[p], b[p + 1:f].decode('utf-8', 'surrogateescape')))
        p = f + 1
    return version_num, out, p


def missing_from_imp(b, imported):
    _version, hash_entries = read_imp(b)
    listed = set()
    for _mark, fname in hash_entries:
        fname = fname.replace('/', '\\').upper()
        listed.add(fname)
        listed.add(IMPORTED_FOLDER.upper() + fname)
    return [n for n in imported if n.replace('/', '\\').upper() not in listed]


def unnamed(a, name_list):
    comment = set()
    for n in list(name_list) + sorted(SPECIAL_FILES):
        r = a.find(n)
        if r:
            comment.add(r[1])
    out = {'models': 0, 'images': 0, 'others': 0}
    for bi in mpqnames.unnamed_blocks(a, comment):
        if not a.blocks[bi][2] or a.validate(bi)[0] != 'ok':
            continue
        begin_pos = (mpqnames.read_unnamed(a, bi, whole=False) or b'')[:4]
        out[
            'models' if begin_pos == b'MDLX' else 'images' if begin_pos in (b'BLP1', b'BLP2', b'DDS ') else 'others'
        ] += 1
    return out


def imp_with(b, missing_items):
    version_num, hash_entries, end_pos = _read_imp(b)
    return (
        struct.pack('<ii', version_num, len(hash_entries) + len(missing_items)) + b[8:end_pos] + imp(missing_items)[8:]
    )


RX_FUNCTION = re.compile(r'(?ms)^[ \t]*function[ \t]+(\w+)[ \t]+takes.*?^[ \t]*endfunction[ \t]*(?://[^\n]*)?$\n?')


class ScriptCutOff(ValueError):
    pass


def split_script(body_text):
    g = re.search(r'(?ms)\A(.*?)^[ \t]*globals[ \t]*\n(.*?)^[ \t]*endglobals[ \t]*\n', body_text)
    if not g and not re.search(r'(?m)^[ \t]*globals\b', body_text):
        globals_block, rest = '', body_text
    elif not g or g.group(1).strip():
        raise ValueError(
            'the script does not start with the globals block (%r comes before it)' % (g.group(1)[:80] if g else '?')
        )
    else:
        globals_block = g.group(2)
        rest = body_text[g.end():]
    bodies = {}
    for fname in ('main', 'config'):
        ms = [m for m in RX_FUNCTION.finditer(rest) if m.group(1) == fname]
        if not ms:
            signatures = list(re.finditer(r'(?m)^[ \t]*function[ \t]+%s[ \t]+takes' % fname, rest))
            if not signatures or not re.search(r'(?m)^[ \t]*endfunction\b', rest[signatures[-1].end():]):
                raise ScriptCutOff('function %s: the script ends before it' % fname)
        if len(ms) != 1:
            raise ValueError('function %s: %d definitions' % (fname, len(ms)))
        m = ms[0]
        line_list = m.group(0).split('\n')
        if not re.match(r'^[ \t]*function[ \t]+%s[ \t]+takes[ \t]+nothing[ \t]+returns[ \t]+nothing[ \t]*(?://.*)?$'
                        % fname, line_list[0]):
            raise ValueError('function %s with an unexpected signature: %r' % (fname, line_list[0]))
        body = '\n'.join(line_list[1:])
        body = body[:body.rstrip().rfind('endfunction')]
        bodies[fname] = body
        rest = rest[:m.start()] + rest[m.end():]
    return globals_block, rest, bodies['main'], bodies['config']


RX_LEADING_COMMENT = re.compile(r'(?:[ \t]*(?://[^\n]*|(?:constant[ \t]+)?native[ \t][^\n]*|type[ \t][^\n]*)?\n)*')


SKELETON_NAMES = (r'InitGlobals', r'InitCustomTriggers', r'RunInitializationTriggers', r'InitCustomPlayerSlots',
                  r'InitCustomTeams', r'InitAllyPriorities', r'CreateAllUnits', r'CreateUnitsForPlayer\d+',
                  r'CreateNeutralHostile', r'CreateNeutralPassiveBuildings', r'CreateNeutralPassive',
                  r'CreatePlayerBuildings', r'CreatePlayerUnits', r'Unit\d+_DropItems', r'ItemTable\w*_DropItems',
                  r'CreateRegions', r'CreateCameras',
                  r'InitSounds', r'CreateAllDestructables', r'CreateAllItems', r'CreateBuildingsForPlayer\d+',
                  r'CreateNeutralHostileBuildings', r'Doodad\d+_DropItems', r'InitTechTree(?:_Player\d+)?',
                  r'InitUpgrades(?:_Player\d+)?')
RX_SKELETON = re.compile(r'\b(' + '|'.join(SKELETON_NAMES) + r')\b')
RX_DEFINE = re.compile(r'(?m)^[ \t]*function[ \t]+(\w+)[ \t]+takes')
SKELETON_PREFIX = 'devo_'


def skeleton_names(body_text):
    return sorted(n for n in set(RX_DEFINE.findall(body_text)) if RX_SKELETON.fullmatch(n))


def rename_skeleton(body_text, name_list=None):
    defined = skeleton_names(body_text) if name_list is None else list(name_list)
    if not defined:
        return body_text
    rx = re.compile(r'\b(' + '|'.join(re.escape(n) for n in sorted(defined, key=len, reverse=True)) + r')\b')
    return rx.sub(lambda m: SKELETON_PREFIX + m.group(1), body_text)


def split_comment(body_text):
    m = RX_LEADING_COMMENT.match(body_text)
    return body_text[:m.end()], body_text[m.end():]


def custom_script(body_text, inject=True):
    prefix, body_text = split_comment(body_text)
    globals_block, functions, main, config = split_script(body_text)
    defined = skeleton_names(body_text)
    functions, main, config = (rename_skeleton(functions, defined), rename_skeleton(main, defined),
                               rename_skeleton(config, defined))
    warning = jass_warning(main)
    block_entry = ('globals\n' + globals_block + 'endglobals\n') if globals_block.strip() else ''
    cs = (prefix + block_entry + functions + ('' if functions.endswith('\n') else '\n') +
          '//! inject main\n' + mark_dovjassinit(main) + warning + '//! endinject\n' +
          '//! inject config\n' + config + '//! endinject\n')
    if not inject:
        cs = prefix + block_entry + functions + ('' if functions.endswith('\n') else '\n') + EDITOR_JASS_NOTE
    assembled = (prefix + block_entry + functions + ('' if functions.endswith('\n') else '\n') +
                 'function main takes nothing returns nothing\n' + main + 'endfunction\n' +
                 'function config takes nothing returns nothing\n' + config + 'endfunction\n')
    return cs.replace('\n', CRLF), assembled


RX_INITBLIZZARD = re.compile(r'^[ \t]*call[ \t]+InitBlizzard[ \t]*\([ \t]*\)[ \t]*$', re.I | re.M)
DOVJASSINIT = '//! dovjassinit\n'


def mark_dovjassinit(main):
    if 'dovjassinit' in main:
        return main
    m = RX_INITBLIZZARD.search(main)
    if m:
        return main[:m.end()] + '\n' + DOVJASSINIT + main[m.end():].lstrip('\n')
    return DOVJASSINIT + main


EDITOR_CALLS = ('CreateAllUnits', 'CreateRegions', 'InitCustomTriggers', 'RunInitializationTriggers')


def jass_warning(main):
    chama = set(m.group(1) for m in re.finditer(r'\bcall[ \t]+(?:devo_)?(\w+)[ \t]*\(', main))
    missing_items = [n for n in EDITOR_CALLS if n not in chama]
    if missing_items:
        pede = ("A unit, region or trigger you add in the editor only runs\n"
                "// if main calls it: add %s at the end here (the editor generates those functions).\n"
                % ' and '.join('call %s()' % n for n in missing_items))
    else:
        pede = ("main already calls everything the editor generates (%s):\n"
                "// a unit, region or trigger you add in the editor runs without changing anything here.\n"
                % ', '.join(EDITOR_CALLS))
    return (
        "// The map's ORIGINAL main and config, through JassHelper (//! inject): saving from the World Editor with\n"
        "// JassHelper ENABLED builds the same script again. "
        + pede
        + "// The map's own copies of the functions the editor also generates (InitGlobals, CreateAllUnits, ...) are\n"
        "// prefixed with \"devo_\" here: two functions with the same name do not compile.\n"
    )


EDITOR_JASS_NOTE = (
    "// The map's main and config are the ones the World Editor writes (the same code), so there is no\n"
    "// //! inject here. The map's own copies of other functions the editor also generates keep the\n"
    "// \"devo_\" prefix: two functions with the same name do not compile.\n"
)
LUA_WARNING = (
    "-- The map's ORIGINAL script, whole, inside do ... end. When you save, the World Editor writes this custom script\n"
    "-- into war3map.lua and adds its own main() and config() after it; the local _ENV line at the end sends\n"
    "-- those to a separate table, so the game still runs the map's own main() and config(). A unit, region or\n"
    "-- trigger you add in the editor only runs if the map's main() calls it.\n"
)
ENV_LINE = 'local _ENV = setmetatable({}, {__index = _G})\n'


def custom_script_lua(body_text):
    return LUA_WARNING + 'do\n' + body_text + ('' if body_text.endswith('\n') else '\n') + 'end\n' + ENV_LINE


def compile_lua(code):
    try:
        from lupa import lua53
    except Exception:
        return 'no_lupa'
    L = lua53.LuaRuntime(register_eval=False)
    f = L.eval('function(s) local f, e = load(s, "=war3map.lua", "t") return e end')
    return f(code)


def _code(body_text):
    prefix, body_text = split_comment(body_text)
    line_list = [line.strip() for line in body_text.split('\n')]
    code_part = [line for line in line_list if line.strip() and not line.strip().startswith('//')]
    globals_block, functions, current = [], [], None
    inside_globals = False
    for line in code_part:
        s = line.strip()
        if current is None and not inside_globals and re.match(r'^globals\b', s):
            inside_globals = True
            continue
        if inside_globals:
            if re.match(r'^endglobals\b', s):
                inside_globals = False
            else:
                globals_block.append(line)
            continue
        m = re.match(r'^(?:constant\s+)?function\s+(\w+)\s+takes\b', s)
        if m and current is None:
            current = (m.group(1), [line])
            continue
        if current is not None:
            current[1].append(line)
            if re.match(r'^endfunction\b', s):
                functions.append(current)
                current = None
            continue
        globals_block.append(line)
    return globals_block, functions


def same_code(assembled, original):
    g1, f1 = _code(assembled)
    g2, f2 = _code(original)
    end_pos = [f for f in f2 if f[0] in ('main', 'config')]
    end_pos.sort(key=lambda f: 0 if f[0] == 'main' else 1)
    return g1 == g2 and f1 == [f for f in f2 if f[0] not in ('main', 'config')] + end_pos


def to_standard_script(body_text, b_w3i, log=print, doo=None):
    try:
        import jass_normal
        import trigger_restore
    except ImportError:
        return body_text, None, None
    try:
        n_players = jass_normal.players_of(struct.unpack_from('<i', b_w3i, 8)[0]) if b_w3i else None
    except struct.error:
        n_players = None
    try:
        new, report = trigger_restore.standard_script(body_text, n_players, log, doo)
        report['line_list'] = trigger_restore.optimizer_lines(report)
        return new, report, n_players
    except Exception as e:
        log('standard script: %s: %s' % (type(e).__name__, e))
        return body_text, None, n_players


def restore_triggers(body_text, is_lua, log=print, file_set=None, n_players=None, default_value=None, read_data=None):
    try:
        import trigger_restore
    except ImportError:
        return None
    try:
        name_list = None
        if read_data is not None:
            try:
                import object_names
                name_list = lambda: object_names.names(read_data)
            except ImportError:
                name_list = None
        r = trigger_restore.restore(body_text, 'lua' if is_lua else 'jass', log=log, editor_files=file_set,
                                    players=n_players, standard=default_value, object_names=name_list)
    except Exception as e:
        log('trigger_restore: %s: %s' % (type(e).__name__, e))
        return {'used': False, 'reason': 'failed: %s: %s' % (type(e).__name__, e)}, None, None, None
    if r is None:
        return None
    went_ok, reason, wtg_b, wct_b, header_text, rep, proof_results, summary = trigger_restore.outcome(r)
    as_text = rep.get('text', ())
    info = {
        'used': bool(went_ok and not reason),
        'reason': reason,
        'proof_results': proof_results,
        'gui': rep.get('gui', 0),
        'as_text': len(as_text) if isinstance(as_text, (list, tuple)) else as_text,
        'variable_count': rep.get('variables', 0),
        'custom_line_count': rep.get('custom_lines', 0),
        'clean_gui': rep.get('gui_clean', 0),
        'custom_only': rep.get('only_custom', 0),
        'helpers': list(rep.get('external_to_header') or []),
        'init_trigger_names': list(rep.get('init_triggers') or []),
        'names_obfuscated': bool(rep.get('obfuscated')),
        'disabled_triggers': len(rep.get('disabled') or ()),
        'object_globals': list(rep.get('object_globals_used') or []),
        'name_conflicts': list(rep.get('editor_name_conflicts') or []),
        'summary': list(summary),
    }
    if rep.get('editor_save') is not None:
        info['editor_fit'] = dict(rep['editor_save'])
    if not info['used'] and not info['reason']:
        info['reason'] = 'proofs: ' + ', '.join(k for k, ok in proof_results.items() if ok is False)
    return info, wtg_b, wct_b, header_text


COMPILED_SCRIPT = {'kkwe': 'kkmap.jc', 'j2b': 'war3map.bin'}
RX_PJASS_WHERE = re.compile(r'^.*?war3map\.j:\d+:\s*')


class ScriptNotRestored(ValueError):
    pass


RX_REAL_FUNCTION = re.compile(r'^\s*(?:constant\s+)?function\s+\w+\s+takes\b.*\breturns\s+real\s*$')
RX_INTEGER_RETURN = re.compile(r'^(\s*return\s+)(-?\d+)(\s*(?://.*)?)$')


def real_literal_return(body_text):
    line_list = body_text.split('\n')
    real, n = False, 0
    for i, ln in enumerate(line_list):
        s = ln.strip()
        if s.startswith('function ') or s.startswith('constant function '):
            real = bool(RX_REAL_FUNCTION.match(ln))
        elif s.startswith('endfunction'):
            real = False
        elif real:
            m = RX_INTEGER_RETURN.match(ln)
            if m:
                line_list[i] = '%s%s.0%s' % (m.group(1), m.group(2), m.group(3))
                n += 1
    return ('\n'.join(line_list), n) if n else (body_text, 0)


def _pjass_check(body_text, clashes):
    try:
        import pjass
    except ImportError as e:
        return True, 'skipped: %s' % e
    exe = pjass.exe()
    if not os.path.isfile(exe):
        return True, 'skipped: no pjass at %s' % exe
    import tempfile
    tmp = tempfile.mkdtemp('', 'devos_map_doctor_pjass_')
    try:
        origin = os.path.join(tmp, 'script.j')
        with open(origin, 'wb') as f:
            f.write(body_text.encode('utf-8', 'surrogateescape'))
        ref = pjass.default_ref()
        r = pjass.run_action(
            [
                (os.path.join(ref, 'common.j'), 'common.j'),
                (os.path.join(ref, 'blizzard.j'), 'Blizzard.j'),
                (origin, 'war3map.j'),
            ],
            tmp=os.path.join(tmp, 'pjass'),
        )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if r.get('missing'):
        return True, 'skipped: no %s' % os.path.basename(r['missing'])
    error_list = [RX_PJASS_WHERE.sub('', line) for line in r['line_list'] if RX_PJASS_WHERE.match(line)]
    rx = re.compile(r'\b(%s)\b.*al+ready defined' % '|'.join(re.escape(c) for c in clashes)) if clashes else None
    others = [e for e in error_list if not (rx and rx.search(e))]
    return not others, 'rc=%s, %d error(s)%s' % (
        r['rc'],
        len(error_list),
        ': ' + '; '.join(others[:3]) if others else '',
    )


def script_restore(entry, output, kind, log=print):
    try:
        import j2b
        import kkwe
        import kkwe_decompile
        import triggerdata
    except ImportError as e:
        raise ScriptNotRestored('the decompiler is not part of this build (%s)' % e)
    compiled = COMPILED_SCRIPT[kind]
    a = mpqread.Archive(entry)
    j_name = 'war3map.j' if a.find('war3map.j') else 'scripts\\war3map.j'
    try:
        shell = a.read(j_name) or b''
        data_bytes = a.read(compiled)
    except Exception as e:
        raise ScriptNotRestored('%s cannot be read (%s)' % (compiled, e))
    if not data_bytes:
        raise ScriptNotRestored('%s is missing or empty' % compiled)
    common, blizzard = triggerdata.game_script('common.j'), triggerdata.game_script('blizzard.j')
    if not common or not blizzard:
        raise ScriptNotRestored(
            'the game scripts (common.j and blizzard.j) could not be read: the decompiler takes the '
            'signature of every native from them, so Warcraft III has to be installed'
        )
    try:
        if kind == 'j2b':
            bc = j2b.bytecode(data_bytes)
            map_own = shell.decode('utf-8', 'surrogateescape')
        else:
            bc = kkwe.Bytecode(kkwe.read_container(data_bytes))
            map_own = ''
        body_text, details = kkwe_decompile.recover(bc, common, blizzard, None, map_own, no_clash=True)
    except kkwe_decompile.DecompileError as e:
        raise ScriptNotRestored(str(e))
    except OSError as e:
        raise ScriptNotRestored('a file of the decompiler is missing (%s)' % e)
    except (ValueError, struct.error, IndexError) as e:
        raise ScriptNotRestored('%s is not in the format this tool reads (%s)' % (compiled, e))
    rename_items = details.get('global_clashes') or []
    if rename_items:
        body_text = rename_skeleton(body_text, rename_items)
        details['renamed'] = list(rename_items)
    body_text, details['real_returns'] = real_literal_return(body_text)
    ok, details['pjass'] = _pjass_check(body_text, [c for c in details['clashes'] if c not in rename_items])
    log('script back (%s): %d instructions, %d functions; %d global(s) renamed; pjass %s'
        % (kind, details['instructions'], details['functions'], len(rename_items), details['pjass']))
    if not ok:
        raise ScriptNotRestored(
            'the script came back, but the Reforged compiler (pjass) rejects it: %s' % details['pjass']
        )
    new = body_text.encode('utf-8', 'surrogateescape')
    shutil.copyfile(entry, output)
    no_slot = []
    mpqadd.add_files(output, [(j_name, new)], to_delete=[compiled], log=log, no_slot=no_slot)
    s = mpqread.Archive(output)
    if no_slot or s.read(j_name) != new or s.find(compiled):
        raise ScriptNotRestored('the new %s could not be written into the map' % j_name)
    details.update({'kind': kind, 'file_name': compiled, 'bytes': len(new)})
    return details


EDITOR_FILE_NAMES = ('war3map.w3i', 'war3map.w3r', 'war3map.w3c', 'war3map.w3s', 'war3mapUnits.doo', 'war3map.doo',
                     'war3map.w3e', 'war3map.w3u', 'war3mapSkin.w3u', 'war3map.w3t', 'war3mapSkin.w3t',
                     'war3map.w3a', 'war3mapSkin.w3a', 'war3map.w3b', 'war3mapSkin.w3b')


def fit_to_editor(header_text, file_set, original, log=print):
    try:
        import editor_render
        import triggerdata
    except ImportError:
        return None
    try:
        td = triggerdata.load()
        return editor_render.outcome(editor_render.fit(header_text, file_set, td, original=original, log=log), td)
    except Exception as e:
        log('editor_render: %s: %s' % (type(e).__name__, e))
        return None


def prepare(entry, output, extra_names=(), log=print, method='attach', safe_units=True, extra_ids=(),
            options=None):
    def step_on(hash_key):
        return options is None or options.get(hash_key, True) is not False
    a = mpqread.Archive(entry)
    details = {}
    b_w3i = a.read('war3map.w3i')
    new_w3i, details['w3i'], details['w3i_tail'] = fix_w3i(b_w3i, sobe=True)
    w3i_era = _fix_w3i(b_w3i)[0]
    details['w3i_raised'] = new_w3i != w3i_era
    try:
        lang = w3i.parse(new_w3i).get('script_language')
    except Exception:
        lang = None
    is_lua = bool(a.find('war3map.lua')) and (lang == 1 or not (a.find('war3map.j') or a.find('scripts\\war3map.j')))
    details['lua'] = is_lua
    if is_lua:
        j_source = 'war3map.lua'
    else:
        j_source = 'war3map.j' if a.find('war3map.j') else 'scripts\\war3map.j'
    raw_bytes = a.read(j_source)
    if raw_bytes is None:
        raise ValueError('the map has no war3map.j (nor scripts\\war3map.j, nor war3map.lua)')
    body_text = raw_bytes.decode('latin-1').replace('\r\n', '\n').replace('\r', '\n')
    details['bom'] = body_text.startswith('\xef\xbb\xbf')
    if details['bom']:
        body_text = body_text[3:]
    default_value, details['n_players'] = None, None
    if not is_lua:
        body_text, default_value, details['n_players'] = to_standard_script(body_text, b_w3i, log,
                                                         a.read('war3map.doo') if a.find('war3map.doo') else None)
        details['optimizer'] = default_value
    expected_len = body_text
    counts = inflated_counts.analyze_map(a)
    broken = dict((x['file_name'], x) for x in counts)
    details['count'] = []
    trigger_list = bool(set(broken) & {'war3map.wtg', 'war3map.wct'}) or \
        not (a.find('war3map.wtg') and a.find('war3map.wct'))
    if not trigger_list:
        try:
            reason = wtg_triggers.needs_regeneration(a.read('war3map.wtg'))
        except Exception:
            reason = None
        if reason:
            trigger_list = True
            details['regenerated_triggers'] = reason
    name_list = set(n for n in extra_names if a.find(n))
    lf = a.read('(listfile)') or b''
    name_list.update(n for n in lf.decode('utf-8', 'replace').splitlines() if n.strip() and a.find(n.strip()))
    imported = sorted((n for n in name_list if n.lower() not in {x.lower() for x in SPECIAL_FILES}
                       and not RX_NATIVE.match(n.split('\\')[-1]) and a.read(n) is not None),
                      key=lambda n: (n.lower(), n))
    engine = []
    for t in ENGINE_TEXTURES:
        try:
            if a.find(t) and jpeg_flat.blp_is_white(a.read(t) or b''):
                engine.append(t)
        except Exception as e:
            log('%s: %s' % (t, e))
    if engine:
        left_out = set(x.lower() for x in engine)
        name_list = set(n for n in name_list if n.lower() not in left_out)
        imported = [n for n in imported if n.lower() not in left_out]
        details['engine_textures'] = engine
    new_ones = {}
    missing_items = []
    replacements = {} if new_w3i == b_w3i else {'war3map.w3i': new_w3i}
    try:
        skin_files = skin_split.split(dict((n, a.read(n)) for n in ('war3map.w3u', 'war3map.w3t', 'war3mapSkin.w3u',
                                                                    'war3mapSkin.w3t') if a.find(n)))
    except Exception as e:
        skin_files = {}
        log('skin: %s' % e)
    for n in sorted(skin_files):
        if a.find(n):
            replacements[n] = skin_files[n]
        else:
            new_ones[n] = skin_files[n]
            missing_items.append(n)
    if skin_files:
        details['skin'] = sorted(n for n in skin_files if n.startswith('war3mapSkin'))
    try:
        w3i_version = struct.unpack_from('<i', w3i_era, 0)[0] if w3i_era else None
    except struct.error:
        w3i_version = None
    try:
        editor_w3i = w3i.parse(w3i_era).get('editor_version')
    except Exception:
        editor_w3i = None
    context = {'w3i': w3i_version, 'game_132': _game_is_132(w3i_era), 'mpq': a,
               'safe_units': safe_units, 'editor_w3i': editor_w3i, 'file_set': replacements}
    try:
        _bd = a.read('war3map.doo')
        if _bd:
            _valid = doodads.game_ids() | doodads.map_ids(a) | set(extra_ids)
            if _valid:
                _new_doo, _bad = doodads.without_invalid_ids(_bd, _valid)
                if _bad:
                    replacements['war3map.doo'] = _new_doo
                    details['doodads'] = [{'id': k.decode('latin-1'), 'n': v} for k, v in _bad]
                    details['doodads_outside'] = sum(v for _k, v in _bad)
    except Exception as e:
        log('war3map.doo: %s' % e)
    try:
        _duplicates, details['duplicate_textures'] = duplicate_textures.make_distinct(
            a, sorted(name_list, key=lambda n: (n.lower(), n))
        )
        replacements.update(_duplicates)
    except Exception as e:
        details['duplicate_textures'] = []
        log('duplicate textures: %s' % e)
    EMPTY_FILES = {
        'war3map.w3r': empty_w3r,
        'war3map.w3c': empty_w3c,
        'war3map.w3s': empty_w3s,
        'war3map.mmp': empty_mmp,
    }

    def empty_file(fname, b):
        if fname == 'war3mapUnits.doo':
            return empty_units_doo(context.get('w3i'), b, context.get('game_132'))
        return EMPTY_FILES[fname]()

    for fname in sorted(n for n in broken if n not in ('war3map.wtg', 'war3map.wct')):
        data_bytes, done = inflated_counts.fixable(fname, a.read(fname), script=body_text,
                                                   context=dict(context, current=a.read(fname)))
        if data_bytes is None and broken[fname]['reason'] == inflated_counts.EMPTY and \
                (fname in EMPTY_FILES or fname == 'war3mapUnits.doo'):
            data_bytes, done = empty_file(fname, a.read(fname)), {
                'file_name': fname, 'declared': None, 'read_count': 0, 'new': 0, 'from_script': False,
                'reason': inflated_counts.EMPTY, 'report': '%s: empty (not even the header)' % fname}
        if data_bytes is None:
            continue
        replacements[fname] = data_bytes
        details['count'].append(done)
    for n in ('war3map.w3s', 'war3map.w3r', 'war3map.w3c', 'war3mapUnits.doo'):
        if n in replacements:
            continue
        present = inflated_counts.count_in_file(n, a)
        done = inflated_counts.fix_from_script(n, body_text, context=dict(context, current=a.read(n))) \
            if step_on('script_objects') else None
        if done and done[1]['new'] and (not a.find(n) or present is None or done[1]['new'] > present):
            data_bytes, info = done
            info['reason'] = 'was_missing' if not a.find(n) else ('empty' if present == 0 else 'missing_objects')
            info['in_file'] = present
            if a.find(n):
                replacements[n] = data_bytes
            else:
                new_ones[n] = data_bytes
                missing_items.append(n)
            details['count'].append(info)
            continue
        if not a.find(n) and n != 'war3map.w3s':
            new_ones[n] = empty_file(n, None)
            missing_items.append(n)
    for info in details['count']:
        where = replacements if 'war3map.w3r' in replacements else new_ones
        if info.get('file_name') == 'war3map.w3r' and info.get('from_script') and 'war3map.w3r' in where:
            w3s_final = replacements.get('war3map.w3s', new_ones.get('war3map.w3s', a.read('war3map.w3s')))
            where['war3map.w3r'], info['sounds_dropped'] = inflated_counts.w3r_without_outside_sounds(
                where['war3map.w3r'], w3s_final
            )
    editor_file_set = {}
    for n in EDITOR_FILE_NAMES:
        data_bytes = replacements.get(n, new_ones.get(n))
        if data_bytes is None and a.find(n):
            data_bytes = a.read(n)
        if data_bytes is not None:
            editor_file_set[n] = data_bytes
    lua_error = None
    fit_wtg = None
    def read_file(fname):
        data_bytes = replacements.get(fname, new_ones.get(fname))
        return data_bytes if data_bytes is not None else (a.read(fname) if a.find(fname) else None)

    restoration = None
    if trigger_list and step_on('gui_triggers'):
        restoration = (
            restore_triggers(raw_bytes[3:] if details['bom'] else raw_bytes, is_lua, log, editor_file_set)
            if is_lua
            else restore_triggers(
                body_text.encode('latin-1'),
                is_lua,
                log,
                editor_file_set,
                details['n_players'],
                default_value,
                read_file,
            )
        )
    restored = restoration is not None and restoration[0].get('used', False)
    if restoration is not None:
        details['restoration'] = restoration[0]
    if trigger_list and restored:
        cs, assembled = restoration[3], expected_len
        if is_lua:
            lua_error = compile_lua(cs)
        details['script'] = ('%s, %d B; the triggers restored in the editor: %d as GUI, %d as text, %d variables; the '
                             'header (the script without them) in the custom script' % (
                             j_source, len(raw_bytes), restoration[0]['gui'], restoration[0]['as_text'],
                             restoration[0]['variable_count']))
    elif trigger_list and is_lua:
        cs, assembled = custom_script_lua(body_text), body_text
        lua_error = compile_lua(cs)
        details['script'] = (
            '%s, %d B (Lua): the whole script in the custom script, in `do ... end`, and the `local _ENV` at the end; '
            'compiles in Lua 5.3: %s'
            % (
                j_source,
                len(raw_bytes),
                'yes'
                if lua_error is None
                else 'not verified (without lupa)'
                if lua_error == 'no_lupa'
                else 'NO (%s)' % lua_error,
            )
        )
    elif trigger_list:
        expected_len = rename_skeleton(body_text)
        cs, assembled = custom_script(body_text)
        renamed = len(skeleton_names(body_text))
        details['script'] = (
            '%s, %d B; the %d names the editor skeleton also defines were prefixed with `%s` (without that, the '
            'JassHelper refuses to compile: "Function redeclared: InitGlobals"); the script built by '
            'JassHelper is %s the original'
            % (
                j_source,
                len(raw_bytes),
                renamed,
                SKELETON_PREFIX,
                'IDENTICAL to'
                if assembled == expected_len
                else 'the SAME CODE as (only the comments move around)'
                if same_code(assembled, expected_len)
                else 'DIFFERENT from',
            )
        )
        adjustment = fit_to_editor(expected_len, editor_file_set, body_text, log)
        if adjustment is not None:
            details['editor_fit'] = adjustment[6]
            if adjustment[0]:
                cs, assembled, fit_wtg = custom_script(adjustment[2], adjustment[3])[0], expected_len, adjustment[4]
                details['script'] += (
                    '; fitted to the editor (%s): %d globals and %d functions stay with it, proven by '
                    'pjass and by the functions the game runs'
                    % (adjustment[1], len(adjustment[6]['dropped']), len(adjustment[6]['replaced']))
                )
    else:
        cs, assembled = None, body_text
        details['script'] = '%s, %d B; the map already has war3map.wtg and war3map.wct: its own are kept' % (
            j_source,
            len(raw_bytes),
        )
    details['replaced'] = []
    if trigger_list:
        if restored:
            pair = (('war3map.wtg', restoration[1]), ('war3map.wct', restoration[2]))
        else:
            pair = (('war3map.wtg', fit_wtg or single_category_wtg()),
                    ('war3map.wct', wct(cs.replace('\r\n', '\n').replace('\n', CRLF),
                                        n_triggers=1 if fit_wtg else 0)))
        for n, data_bytes in pair:
            if a.find(n):
                replacements[n] = data_bytes
                details['replaced'].append(n)
            else:
                new_ones[n] = data_bytes
                missing_items.append(n)
        for fname in sorted(set(broken) & {'war3map.wtg', 'war3map.wct'}):
            details['count'].append(
                {
                    'file_name': fname,
                    'declared': broken[fname]['declared'],
                    'read_count': broken[fname]['read_count'],
                    'new': None,
                    'from_script': True,
                    'reason': broken[fname]['reason'],
                    'pair': True,
                    'report': ('%s: the wtg/wct pair regenerated, with the map script in the custom script' % fname),
                }
            )
    else:
        details['wct'] = 'the map already has war3map.wtg and war3map.wct: keeping its own'
    if not a.find('war3map.imp'):
        new_ones['war3map.imp'] = imp(imported)
        missing_items.append('war3map.imp')
    else:
        b_imp = a.read('war3map.imp') or b''
        try:
            outside = missing_from_imp(b_imp, imported)
            new_imp = imp_with(b_imp, outside) if outside else None
        except Exception as e:
            log('war3map.imp: %s' % e)
            outside, new_imp = list(imported), imp(imported)
        if new_imp is not None:
            replacements['war3map.imp'] = new_imp
            details['imp_added'] = len(outside)
    try:
        details['unnamed'] = unnamed(a, name_list)
    except Exception as e:
        log('unnamed: %s' % e)
    if trigger_list and not is_lua:
        extra, changed = enable_jasshelper(a.read('war3mapExtra.txt') if a.find('war3mapExtra.txt') else b'')
        if changed:
            if a.find('war3mapExtra.txt'):
                replacements['war3mapExtra.txt'] = extra
                details['replaced'].append('war3mapExtra.txt')
            else:
                new_ones['war3mapExtra.txt'] = extra
                missing_items.append('war3mapExtra.txt')
            details['jasshelper'] = 'enabled in war3mapExtra.txt'
    details['new_ones'] = missing_items
    details['imported'] = len(imported)
    all_items = sorted(name_list | set(new_ones) | set(replacements), key=lambda n: (n.lower(), n))
    if method == 'rebuild':
        r = mpq_rebuild.rebuild(entry, output, all_items, replacements=replacements, new_ones=new_ones,
                                to_remove=['(attributes)'] + engine, sector_shift=3, level=6, log=log)
    else:
        listfile = (CRLF.join(n for n in all_items if n not in ('(listfile)', '(attributes)')) + CRLF).encode(
            'utf-8', 'surrogateescape')
        replacements['(listfile)'] = listfile
        shutil.copyfile(entry, output)
        order = ('war3map.wtg', 'war3map.wct', 'war3map.imp', 'war3mapExtra.txt', '(listfile)', 'war3map.w3r',
                 'war3map.w3c', 'war3mapUnits.doo')
        combined = dict(replacements)
        combined.update(new_ones)
        free_slots = mpqdoctor.analyze_tables(a)['free_slots']
        tight = free_slots <= len(combined) + 1
        if tight:
            work_queue = sorted(combined.items(), key=lambda kv: (order.index(kv[0]) if kv[0] in order else len(order),
                                                                  kv[0].lower()))
        else:
            work_queue = sorted(replacements.items()) + sorted(new_ones.items())
        no_slot = []
        sz = mpqadd.add_files(
            output,
            work_queue,
            to_delete=(['(attributes)'] if a.find('(attributes)') else []) + engine,
            fake_count=tight,
            no_slot=no_slot,
            log=log,
            grow=sorted(name_list, key=lambda n: (n.lower(), n)) if tight else None,
        )
        r = {'method': 'attach', 'byte_size': sz, 'attached': len(work_queue) - len(no_slot), 'error_list': [],
             'no_slot': no_slot, 'free_slots': free_slots}
        if no_slot:
            details['no_slot'] = no_slot
            essential = [n for n in no_slot if n in EDITOR_ESSENTIALS]
            if essential:
                r['error_list'].append(
                    'the hash table of the map is full (%d entries, %d free) and there is no slot '
                    'for %s: without it the editor does not open the map (or loses the imported files on save)'
                    % (a.hash_n_read, free_slots, ', '.join(essential))
                )
    details['mpq'] = r
    s = mpqread.Archive(output)
    failures = []
    for n, d in list(new_ones.items()) + list(replacements.items()):
        if n in (r.get('no_slot') or ()):
            continue
        if s.read(n) != d:
            failures.append('%s: differs when read back' % n)
    if s.read(j_source) != raw_bytes:
        failures.append('%s: the game script changed' % j_source)
    failures.extend('%s: still in the map' % n for n in engine if s.find(n))
    try:
        w3i.parse(s.read('war3map.w3i'))
    except Exception as e:
        if not details['w3i'].startswith('new_version'):
            failures.append('w3i cannot be read: %s' % e)
    if assembled != expected_len and not same_code(assembled, expected_len):
        failures.append('the script JassHelper would build differs from the original')
    if lua_error not in (None, 'no_lupa'):
        failures.append('the Lua custom script does not compile: %s' % lua_error)
    details['failures'] = failures + list(r.get('error_list') or [])
    return details, assembled
