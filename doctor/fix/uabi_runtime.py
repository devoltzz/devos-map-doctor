# Moves the normal ability lists of the unit types from the object data to the script.
import re

from doctor.fix import unprotect


DISTINCT_WARNING = 2000
KEEP = frozenset(('Aloc',))
CHUNK = 300
PREFIX = 'dmd_uabi'
RX_ID = re.compile(r'\A[\x21-\x7e]{4}\Z')


def _nothing(*_a, **_k):
    pass


def _lists(w3u):
    from doctor.data import objbin
    _v, tabs, _p = objbin.read_data(w3u, False)
    out = []
    for ti, objs in enumerate(tabs):
        for oi, (old, new, mods) in enumerate(objs):
            ident = new if new.strip('\0') else old
            for mi, (mid, vt, _l, _d, val) in enumerate(mods):
                if mid == 'uabi' and vt == 3:
                    ids = [x.strip() for x in val.decode('latin-1').split(',') if x.strip()]
                    out.append((ti, oi, mi, ident, ids))
    return out


def _slk_lists(slk_bytes):
    from doctor.data import slk
    out = {}
    for ident, campos in slk.parse_slk_bytes(slk_bytes)[1].items():
        v = str(campos.get('abilList') or campos.get('abillist') or '').strip('"')
        ids = [x.strip() for x in v.split(',') if x.strip() and x.strip() != '_']
        if ids:
            out[ident] = ids
    return out


def scan(path):
    out = {'types': 0, 'references': 0, 'distinct': 0, 'slk': False, 'risky': False, 'top': []}
    try:
        a = unprotect._open(path)
    except BaseException as e:
        if isinstance(e, KeyboardInterrupt):
            raise
        out['error'] = 'The map does not open (%s).' % unprotect._error(e)
        return out
    uses = {}
    w3u = unprotect._read(a, 'war3map.w3u')
    if w3u:
        try:
            for _t, _o, _m, _ident, ids in _lists(w3u):
                out['types'] += 1
                for x in ids:
                    uses[x] = uses.get(x, 0) + 1
        except Exception:
            pass
    s = unprotect._read(a, 'Units\\UnitAbilities.slk')
    if s:
        try:
            got = _slk_lists(s)
        except Exception:
            got = {}
        if got:
            out['slk'] = True
            for ids in got.values():
                out['types'] += 1
                for x in ids:
                    uses[x] = uses.get(x, 0) + 1
    out['references'] = sum(uses.values())
    out['distinct'] = len(uses)
    out['risky'] = out['distinct'] >= DISTINCT_WARNING
    out['top'] = [[k, v] for k, v in sorted(uses.items(), key=lambda kv: (-kv[1], kv[0]))[:10]]
    return out


def _morph_targets(w3a):
    from doctor.data import objbin
    out = set()
    if not w3a:
        return out
    try:
        _v, tabs, _p = objbin.read_data(w3a, True)
    except Exception:
        return out
    for objs in tabs:
        for _old, _new, mods in objs:
            for _mid, vt, _l, _d, val in mods:
                if vt == 3:
                    out.update(x.strip() for x in val.decode('latin-1').split(',') if RX_ID.match(x.strip()))
    return out


def _raw(ident):
    return "'%s'" % ident


def script_parts(moves):
    g = ['    hashtable %s_ht = InitHashtable()' % PREFIX, '    group %s_g = CreateGroup()' % PREFIX]
    f = ['//===========================================================================',
         "// Devo's Map Doctor: the normal abilities of each unit type (uabi), added by the script as each unit is",
         '// created instead of by the object data.',
         '//===========================================================================']
    calls = []
    for t, ids in moves:
        calls.append('    call SaveInteger(%s_ht, %s, 0, %d)' % (PREFIX, _raw(t), len(ids)))
        for i, x in enumerate(ids):
            calls.append('    call SaveInteger(%s_ht, %s, %d, %s)' % (PREFIX, _raw(t), i + 1, _raw(x)))
    chunks = [calls[i:i + CHUNK] for i in range(0, len(calls), CHUNK)] or [[]]
    for k, body in enumerate(chunks):
        f.append('function %s_Data%d takes nothing returns nothing' % (PREFIX, k))
        f += body
        f.append('endfunction')
    f += ['function %s_Give takes unit u returns nothing' % PREFIX,
          '    local integer t = GetUnitTypeId(u)',
          '    local integer n = LoadInteger(%s_ht, t, 0)' % PREFIX,
          '    local integer i = 1',
          '    local integer a',
          '    loop',
          '        exitwhen i > n',
          '        set a = LoadInteger(%s_ht, t, i)' % PREFIX,
          '        if GetUnitAbilityLevel(u, a) == 0 then',
          '            call UnitAddAbility(u, a)',
          '            call UnitMakeAbilityPermanent(u, true, a)',
          '        endif',
          '        set i = i + 1',
          '    endloop',
          'endfunction',
          'function %s_Enters takes nothing returns boolean' % PREFIX,
          '    call %s_Give(GetFilterUnit())' % PREFIX,
          '    return false',
          'endfunction',
          'function %s_Sweep takes nothing returns nothing' % PREFIX,
          '    local unit u',
          '    call GroupEnumUnitsInRect(%s_g, GetWorldBounds(), null)' % PREFIX,
          '    loop',
          '        set u = FirstOfGroup(%s_g)' % PREFIX,
          '        exitwhen u == null',
          '        call GroupRemoveUnit(%s_g, u)' % PREFIX,
          '        call %s_Give(u)' % PREFIX,
          '    endloop',
          'endfunction',
          'function %s_Init takes nothing returns nothing' % PREFIX,
          '    local region r = CreateRegion()']
    for k in range(len(chunks)):
        f.append('    call ExecuteFunc("%s_Data%d")' % (PREFIX, k))
    f += ['    call RegionAddRect(r, GetWorldBounds())',
          '    call TriggerRegisterEnterRegion(CreateTrigger(), r, Filter(function %s_Enters))' % PREFIX,
          'endfunction']
    return g, '\n'.join(f) + '\n', ['    call %s_Init()' % PREFIX], ['    call %s_Sweep()' % PREFIX]


def fix(path_in, path_out, progress=None):
    from doctor.script import jass_ast
    from doctor.fix import map_rewrite
    from doctor.data import objbin
    from doctor.fix import single_player
    p = progress or _nothing
    rep = {'state': 'failed', 'moved': 0, 'references': 0, 'kept': [], 'lines': []}

    def stop(state, why):
        rep['state'] = state
        rep['error' if state == 'failed' else 'reason'] = why
        return rep

    p('Reading the map')
    try:
        a, sc, _strings = single_player.read_map(path_in)
    except BaseException as e:
        if isinstance(e, KeyboardInterrupt):
            raise
        return stop('failed', 'The map cannot be read (%s).' % unprotect._error(e))
    if sc['language'] != 'jass' or sc['compiled'] or sc['bytes'] is None:
        return stop('refused', 'Only a JASS script can take the abilities (this one is %s).' % (sc['language'] or
                                                                                               'missing'))
    w3u = unprotect._read(a, 'war3map.w3u')
    if not w3u:
        return stop('nothing_to_do', 'The map has no war3map.w3u.')
    try:
        lists = _lists(w3u)
    except Exception as e:
        return stop('refused', 'war3map.w3u does not read (%s).' % e)
    morphs = _morph_targets(unprotect._read(a, 'war3map.w3a'))
    moves, empty = [], set()
    for ti, oi, mi, ident, ids in lists:
        if not ids:
            continue
        if ident in morphs:
            rep['kept'].append({'type': ident, 'why': 'an ability can morph a unit into it'})
            continue
        if any(x in KEEP or not RX_ID.match(x) for x in ids):
            rep['kept'].append({'type': ident, 'why': 'its list has Aloc or an id that is not 4 characters'})
            continue
        moves.append((ident, ids))
        empty.add((ti, oi, mi))
    if not moves:
        return stop('nothing_to_do', 'No unit type list can move.')
    new_w3u, n = objbin.reescreve(w3u, False, lambda ti, oi, mi, _mid, _v: b'' if (ti, oi, mi) in empty else None)
    if n != len(empty):
        return stop('failed', 'war3map.w3u: %d of %d lists emptied.' % (n, len(empty)))
    text = sc['bytes'].decode('utf-8', 'surrogateescape')
    if PREFIX + '_Init' in text:
        return stop('nothing_to_do', 'The script already adds the lists.')
    try:
        tree = jass_ast.parse(text)
        g, f, top, end = script_parts(moves)
        new_text = map_rewrite.insert(text, tree, g, f, top, end)
        jass_ast.parse(new_text)
    except (ValueError, jass_ast.JassSyntaxError) as e:
        return stop('refused', 'The script cannot take the code (%s).' % e)
    new_bytes = new_text.encode('utf-8', 'surrogateescape')
    p('Running pjass')
    rep['pjass'] = map_rewrite.gate(sc['bytes'], new_bytes)
    if rep['pjass']['state'] == 'failed':
        return stop('refused', 'pjass does not accept the changed script (%s).' % rep['pjass'].get('new'))

    def check(part):
        b = unprotect._open(part)
        if any(ids for _t, _o, _m, _i, ids in _lists(unprotect._read(b, 'war3map.w3u'))
               if (_t, _o, _m) in empty):
            raise RuntimeError('a moved list is still in war3map.w3u')

    try:
        files = [(sc['file'], new_bytes)] + [(c, new_bytes) for c in sc['copies']] + [('war3map.w3u', new_w3u)]
        done = map_rewrite.write(path_in, path_out, files, p, check)
    except Exception as e:
        return stop('failed', 'The map could not be written (%s).' % unprotect._error(e))
    rep.update(state='done', moved=len(moves), references=sum(len(ids) for _t, ids in moves),
               same_files=done['same_files'])
    rep['lines'] = ['%d unit types get their %d normal abilities from the script as each unit is created (%d stay in '
                    'the object data). Test the map before sharing it.' % (rep['moved'], rep['references'],
                                                                           len(rep['kept']))]
    return rep
