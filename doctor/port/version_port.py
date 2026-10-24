# Ports a map between versions of the classic game (1.24a to 1.29.2), up or down: the return bug by its equivalent, the names the newer game also declares renamed, the script checked with its scripts.
import os
import re
import time

from doctor.data import wc3_versions


REFORGED = wc3_versions.REFORGED
B = chr(92)
SCRIPT_NAMES = ('war3map.j', 'scripts' + B + 'war3map.j')
BLIZZARD_NAMES = ('scripts' + B + 'blizzard.j',)


class Refusal(Exception):
    pass


class _Done(Exception):
    pass


CEILINGS = {'1.24-1.28': '1.28.5', '1.29': '1.29.2'}


def within_range(detail, tgt):
    cap = CEILINGS.get(detail.get('range'))
    if not cap or detail.get('return_bug'):
        return False
    return wc3_versions._key(floor_version(detail)) <= wc3_versions._key(tgt) <= wc3_versions._key(cap)


def targets():
    return [REFORGED] + list(reversed(wc3_versions.versions()))


def floor_version(detail):
    band = detail.get('range')
    if band == '1.30+':
        return REFORGED
    base = '1.29.2' if band == '1.29' else wc3_versions.versions()[0]
    m = detail.get('minimum')
    if m:
        cand = [v for v in wc3_versions.versions() if wc3_versions._key(v) >= wc3_versions._key(m)]
        if not cand:
            return REFORGED
        if wc3_versions._key(cand[0]) > wc3_versions._key(base):
            base = cand[0]
    return base


def _open(map_path):
    from doctor.mpq import mpqread
    return mpqread.Archive(map_path)


def _read(a, name_list):
    for n in name_list:
        try:
            d = a.read(n)
        except Exception:
            d = None
        if d is not None:
            return n, d
    return None, None


def _ref_text(version_num):
    folder = wc3_versions.scripts_dir(version_num)
    if not folder:
        raise Refusal('the game scripts of %s are not in this program' % version_num)
    txt = ''
    for f in ('common.j', 'blizzard.j'):
        with open(os.path.join(folder, f), 'rb') as fh:
            txt += '\n' + fh.read().decode('latin-1')
    return folder, txt


def plataforma(body_text, version_num):
    from doctor.port import new
    folder = wc3_versions.scripts_dir(version_num)
    if not folder:
        return []
    ref = set()
    for f in ('common.j', 'common.ai'):
        p = os.path.join(folder, f)
        if os.path.isfile(p):
            ref |= set(new.natives_of(open(p, 'rb').read().decode('latin-1')))
    return sorted(n for n in new.natives_of(body_text) if n not in ref)


def _reason(detail, floor_v, plat, lua, byte_size, tgt, no_script=False):
    if tgt == REFORGED:
        return None
    if no_script:
        return 'the script cannot be read by its name (a protected map): unprotect it first with Fix map, then port'
    if lua:
        return 'the script is Lua, which only 1.31 and later run: Reforged only'
    if plat and not (detail.get('range') == '1.30+' and is_downport(floor_v, tgt)):
        return 'the map uses %d native(s) of a platform client (%s): Reforged only' % (
            len(plat), ', '.join(plat[:4]) + (', ...' if len(plat) > 4 else ''))
    lim = wc3_versions.limits(tgt) or {}
    n_players = detail.get('players')
    if n_players and lim.get('players') and n_players > lim['players']:
        return 'the map has %d player slots and %s has %d' % (n_players, tgt, lim['players'])
    return None


def is_downport(floor_v, tgt):
    return floor_v == REFORGED or wc3_versions._key(tgt) < wc3_versions._key(floor_v)


def size_warning(byte_size, tgt):
    from doctor.data import map_size
    lim = wc3_versions.limits(tgt) or {}
    return map_size.version_warning(byte_size, tgt, lim.get('map_bytes'))


def memhack_outside(body_text, tgt):
    try:
        from doctor.port import memhack_ui
        libs = (memhack_ui.detect_memhack(body_text) or {}).get('libraries') or {}
    except Exception:
        return None
    for rot in libs:
        m = re.search(r'(1\.\d\d[a-z]?(?:\.\d+)?)\s*-\s*(1\.\d\d[a-z]?(?:\.\d+)?)', str(rot))
        if not m:
            continue
        lo, hi = wc3_versions.normalize(m.group(1)), wc3_versions.normalize(m.group(2))
        if lo and hi and not (wc3_versions._key(lo) <= wc3_versions._key(tgt) <= wc3_versions._key(hi)):
            return (
                "the map carries %s, a memory hack library made for %s to %s: on %s what it does through the game's "
                "memory will not work (the game may close)" % (rot, m.group(1), m.group(2), tgt)
            )
    return None


def analyze(map_path):
    a = _open(map_path)
    _n, lua = _read(a, ('war3map.lua',))
    _n, j = _read(a, SCRIPT_NAMES)
    body_text = j.decode('latin-1').replace('\r\n', '\n').replace('\r', '\n') if j is not None else ''
    lang, src = ('lua', lua.decode('utf-8', 'surrogateescape')) if lua is not None else \
        ('jass', j.decode('utf-8', 'surrogateescape')) if j is not None else (None, None)
    obj = dict((n, _read(a, (n,))[1]) for n in wc3_versions.OBJECT_FILES)
    detail = wc3_versions.detect_parts(_read(a, ('war3map.w3i',))[1], src, lang, obj, _read(a, ('war3map.wtg',))[1],
                                       os.path.getsize(map_path))
    floor_v = floor_version(detail)
    plat = plataforma(body_text, wc3_versions.versions()[-1]) if body_text else []
    sz = os.path.getsize(map_path)
    nameless = j is None and lua is None
    return {
        'origin': detail,
        'floor_version': floor_v,
        'plataforma': plat,
        'lua': lua is not None,
        'no_script': nameless,
        'targets': dict((v, _reason(detail, floor_v, plat, lua is not None, sz, v, nameless)) for v in targets()),
    }


def transform(body_text, target_v, map_version):
    folder, ref_text = _ref_text(target_v)
    new_text = body_text
    chg = {}
    warnings = []
    from doctor.port import shadowed
    new_text, info = shadowed.applies(new_text, ref_dir=folder, version_num=map_version)
    if info.get('failures'):
        raise Refusal('names of the map that %s also declares, with another type: %s'
                      % (target_v, '; '.join(info['failures'][:4])))
    chg['name_list'] = {'removed_ones': list(info.get('removed_ones') or []),
                        'renamed_list': list(info.get('renamed_list') or []) +
                        [(n, 'function', '') for n in info.get('functions') or []]}
    from doctor.port import return_fixes
    new_text, info = return_fixes.applies(new_text)
    chg['return_fixes'] = (info.get('real_blocks', 0) + info.get('codes', 0) + info.get('shadows', 0) +
                           info.get('empty_files', 0))
    from doctor.port import memory_hacks
    new_text, info = memory_hacks.applies(new_text, ref_text, equivalents=True, neutralize=True)
    bridge = info.get('bridge') or {}
    chg['memory_hacks'] = {
        'conversions': len(info.get('conversions') or []) + len(bridge.get('expressions') or []),
        'retyped_vars': len(bridge.get('retyped_vars') or []),
        'neutrals': len(info.get('neutrals') or []) + len(info.get('arrays') or {}) + len(info.get('codes') or []),
        'no_use': len(info.get('no_use') or []),
        'effects': len(info.get('effects') or [])}
    outside = memhack_outside(body_text, target_v)
    if outside:
        warnings.append(outside)
    return new_text, chg, warnings


def map_port(map_path, tgt, output, stats=None, log=print):
    t0 = time.time()
    details = {
        'map_path': map_path,
        'tgt': tgt,
        'output': output,
        'resultado': None,
        'refusal': None,
        'changes': {},
        'pjass': None,
    }
    try:
        target_v = wc3_versions.normalize(tgt)
        if target_v is None:
            raise Refusal('unknown game version: %s' % tgt)
        if target_v == REFORGED:
            raise Refusal('porting to Reforged is the Reforged port (porta.py), not this one')
        details['tgt'] = target_v
        an = analyze(map_path)
        details['origin'] = an['origin']
        details['floor_version'] = an['floor_version']
        reason = (
            an['targets'].get(target_v)
            if target_v in an['targets']
            else _reason(
                an['origin'],
                an['floor_version'],
                an['plataforma'],
                an['lua'],
                os.path.getsize(map_path),
                target_v,
                an['no_script'],
            )
        )
        if reason:
            raise Refusal(reason)
        warning = size_warning(os.path.getsize(map_path), target_v)
        if warning:
            details.setdefault('warnings', []).append(warning)
        import shutil
        if os.path.abspath(output) == os.path.abspath(map_path):
            raise Refusal('the output is the map itself')
        if is_downport(an['floor_version'], target_v):
            from doctor.port import version_downport
            log('port to %s (older than the map): %s (made for %s)' % (target_v, os.path.basename(map_path),
                                                                      an['origin'].get('label')))
            try:
                d = version_downport.port_down(map_path, target_v, output, an, log=log)
            except version_downport.Refusal as e:
                raise Refusal(str(e))
            details['downport'] = d
            details['pjass'] = d['pjass']
            details['changes'].update(d['changes'])
            if d['warnings']:
                details.setdefault('warnings', []).extend(d['warnings'])
            details['resultado'] = 'ported'
            details['bytes'] = os.path.getsize(output)
            raise _Done()
        if within_range(an['origin'], target_v):
            shutil.copyfile(map_path, output)
            details['resultado'] = 'already runs'
            details['inside'] = True
            details['bytes'] = os.path.getsize(output)
            raise _Done()
        a = _open(map_path)
        j_name, j = _read(a, SCRIPT_NAMES)
        if j is None:
            raise Refusal('the map has no war3map.j that can be read')
        _nb, blizz = _read(a, BLIZZARD_NAMES)
        body_text = j.decode('latin-1')
        log('port to %s: %s (made for %s)' % (target_v, os.path.basename(map_path), an['origin'].get('label')))
        new_text, chg, warnings = transform(body_text, target_v, an['origin'].get('version'))
        details['changes'].update(chg)
        if warnings:
            details.setdefault('warnings', []).extend(warnings)
        new_b = new_text.encode('latin-1')
        pj = wc3_versions.pjass_check(new_b, target_v, own_blizzard=blizz)
        details['pjass'] = pj
        if pj.get('skipped'):
            details.setdefault('warnings', []).append('pjass was not run (%s)' % pj['skipped'])
        elif pj.get('rc') != 0 or pj.get('errors'):
            raise Refusal(
                'the script does not compile on %s after the port: %s'
                % (target_v, '; '.join(str(e) for e in (pj.get('errors') or [])[:5]) or 'rc %s' % pj.get('rc'))
            )
        from doctor.port import map_path as _map_mod
        if new_b == j:
            shutil.copyfile(map_path, output)
            details['resultado'] = 'already runs'
        else:
            _map_mod.attach(map_path, output, [(j_name, new_b)], log=lambda s: None)
            details['resultado'] = 'ported'
        details['bytes'] = os.path.getsize(output)
    except _Done:
        pass
    except Refusal as e:
        details['resultado'] = 'refused'
        details['refusal'] = str(e)
    except Exception as e:
        details['resultado'] = 'failed'
        details['refusal'] = '%s: %s' % (type(e).__name__, e)
    details['seconds'] = round(time.time() - t0, 1)
    if stats:
        with open(stats, 'w', encoding='utf-8') as f:
            f.write(report_text(details))
    return details


def _short_list(name_list, n=8):
    name_list = list(name_list)
    return ', '.join(name_list[:n]) + (', ... (%d in all)' % len(name_list) if len(name_list) > n else '')


def downport_lines(d, tgt):
    L = []
    m = d.get('changes') or {}
    w = m.get('w3i') or {}
    if w and w.get('from_') != w.get('new_value'):
        L.append(
            '- map info: format %s -> %s%s'
            % (w['from_'], w['new_value'], ('; flags cleared: %s' % ', '.join(w['flags'])) if w.get('flags') else '')
        )
    s = m.get('script') or {}
    if s.get('emulated'):
        L.append('- %d native(s) of the newer game given their %s equivalent: %s' % (len(s['emulated']), tgt,
                                                                                    _short_list(s['emulated'])))
    if s.get('neutrals'):
        L.append('- %d native(s) of the newer game that %s does not have were made NEUTRAL (they compile and do '
                 'nothing, so what they did is lost): %s' % (len(s['neutrals']), tgt, _short_list(s['neutrals'])))
    if s.get('declaradas'):
        L.append(
            '- %d native(s) the map declares that %s does not have (natives of the newer game outside its common.j) '
            'taken out of the script%s: %s'
            % (
                len(s['declaradas']),
                tgt,
                (' (%d called, given the equivalent or made neutral above)' % len(s['declared_used']))
                if s.get('declared_used')
                else ' (never called)',
                _short_list(s['declaradas']),
            )
        )
    if s.get('copied'):
        L.append('- %d function(s) of the newer blizzard.j copied into the script: %s' % (len(s['copied']),
                                                                                         _short_list(s['copied'])))
    if s.get('types'):
        L.append('- %d type(s) of the newer game written as the one %s has: %s' % (
            len(s['types']), tgt, _short_list('%s -> %s' % kv for kv in sorted(s['types'].items()))))
    if s.get('w3p_constants') or s.get('neutral_constants'):
        L.append(
            '- %d constant(s) of the newer game copied (a number the older engine does not know: the event or '
            'option does nothing there)%s'
            % (
                len(s.get('w3p_constants') or []),
                (
                    '; %d made neutral (null or 0): %s'
                    % (len(s['neutral_constants']), _short_list(s['neutral_constants']))
                )
                if s.get('neutral_constants')
                else '',
            )
        )
    if s.get('damage'):
        L.append('- %d registration(s) of the any-unit damage event of 1.31 given the classic damage detection (each '
                 'unit on the map gets the unit damage event; the damaging event fires after the damage)' % s['damage'])
    if s.get('n_players'):
        L.append('- %d neutral player number(s) of the 24 player game (24 to 27) written as the 12 player ones (12 to '
                 '15)' % s['n_players'])
    for kind, info in sorted((m.get('objects') or {}).items()):
        L.append('- war3map.%s: version 2 (%d object(s)%s)' % (kind, info['objects'], ('; %d merged and %d added from '
                 'war3mapSkin.%s' % (info['merged'], info['added'], kind)) if info['merged'] or info['added'] else ''))
    if m.get('w3e'):
        L.append('- war3map.w3e: the terrain in version 11 (%d points, from version %d)' % (m['w3e']['points'],
                                                                                        m['w3e']['from']))
    doo = m.get('doo')
    if doo:
        v, sub, skin = doo['from']
        L.append('- war3map.doo: %d doodad(s) in the classic layout (from version %d.%d%s)' % (
            doo['records'], v, sub, ' with the skin field' if skin else ''))
    g = m.get('trigger_list')
    if g:
        L.append('- the triggers in the classic format the World Editor of %s reads%s%s' % (
            tgt, ('; %d GUI trigger(s) with functions it does not know written as custom text: %s'
                  % (len(g['to_text']), _short_list(g['to_text']))) if g.get('to_text') else '',
            ('; %d variable(s) of a type it does not have written as handle: %s'
             % (len(g['var_types']), _short_list(sorted(g['var_types'])))) if g.get('var_types') else ''))
    for fname, o in sorted((m.get('editor') or {}).items()):
        L.append('- %s: %s' % (fname, o))
    if m.get('models'):
        L.append('- %d model(s) of version 900 or later written as version 800 (an HD material keeps only its diffuse '
                 'map)' % m['models'])
    if m.get('dds'):
        L.append('- %d DDS texture(s) written as BLP, the references moved to the new names' % m['dds'])
    if m.get('sounds'):
        L.append('- %d FLAC/OGG sound(s) written as MP3, the references moved to the new names' % m['sounds'])
    for e in d.get('editor') or []:
        L.append('Note: the %s World Editor: %s' % (tgt, e))
    return L


def report_text(details):
    o = details.get('origin') or {}
    L = [
        'Port to %s' % details.get('tgt'),
        '=' * (8 + len(str(details.get('tgt')))),
        '',
        'Map: %s' % os.path.basename(str(details.get('map_path'))),
        'Made for: %s%s'
        % (
            o.get('label') or '?',
            (' (runs on %s and later)' % details['floor_version'])
            if details.get('floor_version') and details['floor_version'] != REFORGED
            else '',
        ),
    ]
    for r in (o.get('reasons') or [])[:6]:
        L.append('  - %s' % r)
    L.append('')
    res = details.get('resultado')
    if res == 'refused':
        L.append('NOT PORTED: %s' % details.get('refusal'))
    elif res == 'failed':
        L.append('FAILED: %s' % details.get('refusal'))
    else:
        m = details.get('changes') or {}
        if res == 'already runs' and details.get('inside'):
            L.append('The map was made for %s, which includes %s: it runs there as it is. The copy is the same map.'
                     % (o.get('label'), details['tgt']))
        elif res == 'already runs':
            L.append(
                'The map already runs on %s: nothing in it had to change. The copy is the same map.' % details['tgt']
            )
        else:
            L.append('Ported: %s' % details.get('output'))
        if details.get('downport'):
            L += downport_lines(details['downport'], details['tgt'])
        nm = m.get('name_list') or {}
        if nm.get('renamed_list') or nm.get('removed_ones'):
            L.append(
                '- names of the map that %s also declares: %d renamed (kkm_), %d declarations dropped (the game\'s '
                'own is the same)'
                % (details['tgt'], len(nm.get('renamed_list') or []), len(nm.get('removed_ones') or []))
            )
        if m.get('return_fixes'):
            L.append(
                '- %d return(s) the old compiler accepted, written the way %s reads them'
                % (m['return_fixes'], details['tgt'])
            )
        me = m.get('memory_hacks') or {}
        if me.get('conversions') or me.get('retyped_vars'):
            L.append('- return bug: %d conversion(s) given their equivalent (GetHandleId and a table), %d variable(s) '
                     'given their real type' % (me.get('conversions', 0), me.get('retyped_vars', 0)))
        if me.get('no_use'):
            L.append(
                '- %d cast function(s) the retyping left unused were removed (nothing stops working)' % me['no_use']
            )
        if me.get('neutrals'):
            L.append(
                '- %d memory hack(s) or return bug use(s) with no equivalent on %s were made NEUTRAL: they compile '
                'and do nothing, so what they did is lost' % (me['neutrals'], details['tgt'])
            )
        pj = details.get('pjass')
        if pj is None:
            pass
        elif pj.get('skipped'):
            L.append('- the script was NOT checked (%s)' % pj['skipped'])
        else:
            L.append('- the script compiles with the game scripts of %s (pjass)' % details['tgt'])
    for a in details.get('warnings') or []:
        L.append('Note: %s' % a)
    return '\n'.join(L) + '\n'
