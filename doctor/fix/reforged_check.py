# Tells whether a map runs on Warcraft III 3.0, from the problems measured on real maps.
import os
import re

from doctor.fix import unprotect
from doctor.script import jass_ast
from doctor.script import lua_ast
from doctor.models import model_check
from doctor.script import missing_natives
from doctor.fix import single_player


REF_30 = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ref', '3.0'))
MAX_MAP = 512 * 1024 * 1024
PLATFORM_FAMILIES = frozenset(lbl for lbl, _rx in missing_natives.FAMILIES
                              if not lbl.startswith(('Blizzard', 'jass do acervo')))
KK_FAMILY = 'KK platform (KK*)'
RX_KK = re.compile(r'KK[A-Z]\w*\Z')
HIDDEN_NATIVES = frozenset((
    'BlzDeleteHeroAbility', 'BlzGetDestructableSkin', 'BlzGetHeroPrimaryStat', 'BlzGetHeroPrimaryStatById',
    'BlzGetHeroStat', 'BlzGetUnitArmorType', 'BlzGetUnitMovementType', 'BlzSetCameraGuardBand',
    'BlzSetDestructableSkin', 'BlzSetHeroPrimaryStat', 'BlzSetHeroStatEx', 'BlzSetUnitMovementType',
    'ClearStackedSound', 'ClearStackedSoundRect', 'DebugBreak', 'DialogSetAsync', 'GetPlayerStartLocationX',
    'GetPlayerStartLocationY', 'SetCinematicSceneWithSkinId', 'SetSoundFacialAnimationPlaybackMode', 'SetStackedSound',
    'SetStackedSoundRect'))
PROTECTIONS = ('fake_header', 'missing_hm3w', 'read_only', 'virtual_tables', 'sprotect', 'full_hash_table', 'alias',
               'fake_entries', 'fake_files', 'game_only_reads', 'script_decoy', 'locale_decoy',
               'scrambled_ids', 'sector512')
SEVERITIES = ('blocker', 'warning', 'info')
_REF = {}


def _nothing(*_a, **_k):
    pass


def _item(code, severity, text, fix, **data):
    out = {'code': code, 'severity': severity, 'text': text, 'fix': fix}
    if data:
        out['data'] = data
    return out


def _mb(n):
    return '%.1f MB' % (n / 1048576.0)


def reference():
    if not _REF:
        from doctor.triggers import triggerdata
        _REF['globals'] = set()
        for key, name in (('natives', 'common.j'), ('ai_natives', 'common.ai'), ('functions', 'blizzard.j')):
            path = os.path.join(REF_30, name)
            text = jass_ast.read_script(path) if os.path.isfile(path) else triggerdata.game_script(name)
            if not text:
                raise FileNotFoundError('the Warcraft III 3.0 %s: no copy and no installed game' % name)
            tree = jass_ast.parse(text)
            src = tree.functions if key == 'functions' else tree.natives
            _REF[key] = dict((f.name, len(f.params)) for f in src)
            if key != 'ai_natives':
                _REF['globals'].update(g.name for g in tree.globals)
        _REF['hidden'] = HIDDEN_NATIVES
    return _REF


def family(name):
    f = missing_natives.family(name)
    return KK_FAMILY if f == 'other_entries' and RX_KK.match(name) else f


def is_platform(name):
    return family(name) in PLATFORM_FAMILIES or family(name) == KK_FAMILY


def _names(rows, limit=30):
    return sorted(rows, key=lambda r: (-r['uses'], r['name']))[:limit]


def jass_items(tree, own_blizzard=None):
    try:
        ref = reference()
    except FileNotFoundError:
        return [_item('reference_missing', 'info', 'The natives were not checked: the scripts of Warcraft III 3.0 were '
                      'not found (the game is not installed here).', 'none')]
    declared = dict((f.name, len(f.params)) for f in tree.natives)
    defined = dict((f.name, len(f.params)) for f in tree.functions)
    uses, bad_args, team_zero = {}, {}, 0
    for n in jass_ast.walk(tree):
        t = type(n)
        if t is jass_ast.Call or t is jass_ast.FuncRef:
            uses[n.name] = uses.get(n.name, 0) + 1
            if t is jass_ast.Call:
                want = defined.get(n.name, declared.get(n.name, ref['natives'].get(n.name,
                                                                                  ref['functions'].get(n.name))))
                if want is not None and want != len(n.args):
                    bad_args.setdefault(n.name, [want, len(n.args), 0])[2] += 1
        elif t is jass_ast.Binary and n.op in ('==', '!=', '<', '>', '<=', '>='):
            sides = (n.left.inner if type(n.left) is jass_ast.Paren else n.left,
                     n.right.inner if type(n.right) is jass_ast.Paren else n.right)
            if any(type(s) is jass_ast.Call and s.name == 'GetPlayerTeam' for s in sides) and \
                    any(type(s) is jass_ast.Literal and s.kind == 'integer' and s.value == 0 for s in sides):
                team_zero += 1
    items = []
    hidden = [n for n in declared if n in ref['hidden'] and n not in ref['natives']]
    missing = [n for n in declared if n not in ref['natives'] and n not in ref['ai_natives'] and n not in hidden]
    unknown = [n for n in uses if n not in defined and n not in declared and n not in ref['natives'] and
               n not in ref['functions']]
    platform = [{'name': n, 'family': family(n), 'uses': uses.get(n, 0)} for n in missing + unknown if is_platform(n)]
    if platform:
        fams = {}
        for r in platform:
            fams[r['family']] = fams.get(r['family'], 0) + 1
        items.append(_item('platform_natives', 'blocker', 'The script uses %d natives of a platform client (KK/DzAPI, '
                           'JAPI, JN or YDWE), called %d times. The game does not have them, so the map needs a port.'
                           % (len(platform), sum(r['uses'] for r in platform)), 'port', families=fams,
                           natives=_names(platform)))
    other = [{'name': n, 'uses': uses.get(n, 0)} for n in missing if not is_platform(n)]
    if other:
        items.append(_item('missing_natives', 'blocker', 'The script declares %d natives the game does not have, so '
                           'it does not compile.' % len(other), 'none', natives=_names(other)))
    if hidden:
        items.append(_item('hidden_natives', 'info', 'The script declares %d natives the game has but does not '
                           'publish (like BlzSetDestructableSkin). They work while the game keeps them.' % len(hidden),
                           'none', natives=_names([{'name': n, 'uses': uses.get(n, 0)} for n in hidden])))
    own = missing_natives.declara_functions(own_blizzard) if own_blizzard else {}
    rest = [n for n in unknown if not is_platform(n)]
    from_own = [{'name': n, 'uses': uses[n]} for n in rest if n in own]
    if from_own:
        items.append(_item('own_blizzard_j', 'blocker', 'The map brings its own Scripts\\Blizzard.j, which 3.0 does '
                           'not load, and the script calls %d functions that only that file has.' % len(from_own),
                           'port', functions=_names(from_own)))
    nowhere = [{'name': n, 'uses': uses[n]} for n in rest if n not in own]
    if nowhere:
        items.append(_item('undeclared_functions', 'blocker', 'The script calls %d functions that nothing declares, '
                           'so it does not compile.' % len(nowhere), 'none', functions=_names(nowhere)))
    again = sorted(set(g.name for g in tree.globals if g.name in ref['globals']) |
                   set(n for n in list(defined) + list(declared) if n in ref['natives'] or n in ref['functions']))
    if again:
        items.append(_item('redeclared_names', 'blocker', 'The script declares again %d names the 3.0 common.j or '
                           'blizzard.j already has (like EVENT_PLAYER_UNIT_DAMAGED), so it does not compile.'
                           % len(again), 'port', names=again[:30]))
    if bad_args:
        rows = [{'name': n, 'takes': w, 'given': g, 'uses': k} for n, (w, g, k) in bad_args.items()]
        items.append(_item('wrong_arguments', 'blocker', 'The script calls %d functions with a number of arguments the '
                           'game does not take (like the JAPI SetUnitMoveSpeed with three), so it does not compile.'
                           % len(rows), 'port', functions=_names(rows)))
    if team_zero:
        items.append(_item('neutral_team_zero', 'info', 'The script compares a player\'s team with 0 (%d times). In '
                           '3.0 the neutral players are on team 0: if one of these checks is meant for the neutral '
                           'monsters, kills give no experience, gold or items.' % team_zero, 'port', count=team_zero))
    return items


def model_items(path, progress=None):
    r = model_check.scan(path, progress)
    if r.get('error'):
        return [], 0
    hang = [m['file'] for m in r['models'] if any(x['code'] == 'matrix_groups' for x in m['problems'])]
    fixable = all(x.get('fixable') for m in r['models'] for x in m['problems'] if x['code'] == 'matrix_groups')
    broken = [m['file'] for m in r['models'] if any(x['code'] == 'broken_structure' for x in m['problems'])]
    items = []
    if hang:
        items.append(_item('model_matrix_groups', 'blocker', '%d models have a geoset with more than 255 matrix '
                           'groups: the game hangs when the mouse is over them.%s' % (
                               len(hang), ' The Doctor fixes them.' if fixable else ''), 'doctor' if fixable else
                           'none', models=hang[:30]))
    if broken:
        items.append(_item('model_broken', 'blocker', '%d models have a broken file structure: the game crashes when '
                           'it loads them.' % len(broken), 'none', models=broken[:30]))
    portraits = r.get('portraits') or []
    if portraits:
        items.append(
            _item(
                'portrait_camera',
                'info',
                '%d portrait models have a camera from a model version below 900: '
                'reported to show a black portrait in 3.0. The Doctor can remove those cameras (check the '
                'portraits in game).' % len(portraits),
                'doctor',
                models=portraits[:30],
            )
        )
    from doctor.fix import model_names
    enc = model_names.scan(path)
    if enc.get('renamed'):
        items.append(_item('model_names', 'info', '%d model names carry the suffix the "Model_Encrypt" tool adds '
                           '(`体`): the files were renamed and the map cites the new name. The Doctor can give them '
                           'their name back.' % len(enc['renamed']), 'doctor',
                           names=[list(x) for x in enc['renamed'][:30]],
                           collisions=[list(x) for x in enc.get('collisions') or []][:10]))
    return items, r['checked']


def object_items(path):
    from doctor.fix import data_pointers
    from doctor.fix import uabi_runtime
    items = []
    dp = data_pointers.scan(path)
    if dp.get('fixable'):
        rows = [{'file': f, 'object': x['object'], 'field': x['field']} for f, xs in dp['files'].items() for x in xs
                if x['fix'] is not None]
        items.append(_item('data_pointers', 'warning', '%d levelled fields of the object data point to another data '
                           'column on some levels: on those levels the field the author meant keeps its base value. '
                           'The Doctor sets them to the column the other levels use.' % dp['fixable'], 'doctor',
                           fields=rows[:30]))
    ua = uabi_runtime.scan(path)
    if ua.get('risky'):
        items.append(_item('uabi_distinct', 'warning', 'The unit types carry %d distinct abilities in their normal '
                           'ability lists. Players report that a map with about 2,000 drops almost every game on '
                           'Reforged, and that the same abilities added by the script do not. %s' % (
                               ua['distinct'], 'The Doctor can move the lists to the script.' if not ua['slk'] else
                               'The lists are in the SLK tables, which the Doctor does not move.'),
                           'none' if ua['slk'] else 'doctor', distinct=ua['distinct'], references=ua['references']))
    return items


def import_items(path):
    from doctor.mpq import import_lint
    r = import_lint.lint(path)
    c = r.get('counts') or {}
    if r.get('error') or not any(c.values()):
        return []
    parts = []
    if c.get('not_in_imp'):
        parts.append('%d are not in the import list, so the World Editor drops them when it saves' % c['not_in_imp'])
    if c.get('odd_extension'):
        parts.append('%d are of a type the game does not load' % c['odd_extension'])
    if c.get('game_file'):
        parts.append('%d replace a file of the game' % c['game_file'])
    return [_item('import_lint', 'info', 'Of the imported files, %s.' % '; '.join(parts), 'none', counts=c,
                  files=sorted(r['files'])[:30])]


_ARCHIVE = {
    'ntfs_copy': ('ntfs_copy', 'blocker', 'The file was copied with the bytes of the NTFS compression inside, so the '
                  'archive does not read. The Doctor restores it.', 'doctor'),
    'unreadable_tables': ('unreadable_tables', 'blocker', 'No entry of the archive tables points to a file the game '
                          'would read.', 'none'),
    'kk_encrypted': ('kk_encrypted', 'blocker', 'The map is encrypted by the KK platform: its real content is outside '
                     'the archive and only the platform client opens it. It cannot be ported.', 'none'),
    'script_kkwe': ('kk_compiled_script', 'blocker', 'The script is KKWE bytecode (kkmap.jc), which only the KK '
                    'platform client runs. The Doctor turns it back into JASS for the editor; the map then needs a '
                    'port.', 'port'),
    'script_j2b': ('kk_compiled_script', 'blocker', 'The script is j2b bytecode (war3map.bin), which only the KK '
                   'platform plugin runs. The Doctor turns it back into JASS for the editor; the map then needs a '
                   'port.', 'port'),
}
_SLK = {
    'slk_file_column': (
        'slk_file_column',
        'blocker',
        'Units\\UnitUI.slk or ItemData.slk still has the "file" column: '
        '3.0 crashes on the first unit or item created (section 2).',
    ),
    'fdf_stray_comment': (
        'fdf_comment',
        'blocker',
        'A .fdf file closes a comment that was never opened: 3.0 closes on the loading screen (section 1).',
    ),
    'slk_levels': (
        'slk_levels',
        'warning',
        'Units\\AbilityData.slk stops at level 4: every field of levels 5 and 6 '
        'reads empty, and those skills vanish (section 6).',
    ),
    'slk_id_list': (
        'slk_id_lists',
        'warning',
        'A list of ids in the SLK tables has a "|n" inside: 3.0 stops reading '
        'there, so a unit or item points to an ability that does not exist.',
    ),
    'slk_buttonpos': (
        'slk_button_position',
        'warning',
        'Button positions in Units\\*.txt are written in half '
        '(Buttonpos=,2): 3.0 no longer completes them (section 4).',
    ),
    'slk_quoted_numbers': (
        'slk_quoted_numbers',
        'info',
        'Numbers written as text in the SLK tables (walk="280."): not a crash, cleaned as well (section 3).',
    ),
}


def _finish(res, unknown):
    items = res['items']
    items.sort(key=lambda x: SEVERITIES.index(x['severity']))
    sev = set(x['severity'] for x in items)
    res['verdict'] = ('node' if 'blocker' in sev else 'unknown' if unknown else 'probably' if 'warning' in sev
                      else 'yes')
    return res


def _script_items(src, diag, progress):
    p = progress
    items = []
    try:
        a, sc, strings = single_player.read_map(src)
    except BaseException as e:
        if isinstance(e, KeyboardInterrupt):
            raise
        return [_item('unreadable', 'warning', 'The archive cannot be read (%s).' % unprotect._error(e), 'none')], True
    lang = diag.get('script')
    if sc['bytes'] is None or sc['language'] != lang:
        return [_item('script_unreadable', 'warning', 'The script cannot be read.', 'none')], True
    p('Reading the script')
    text = sc['bytes'].decode('utf-8', 'surrogateescape')
    tree = None
    try:
        tree = jass_ast.parse(text) if lang == 'jass' else lua_ast.parse(text)
    except (jass_ast.JassSyntaxError, lua_ast.LuaSyntaxError) as e:
        vjass = lang == 'jass' and re.search(r'(?m)^\s*(?:scope|library|struct|interface|module)\s+\w', text)
        if vjass:
            items.append(_item('script_vjass', 'blocker', 'The script still has vJass code (scope, library, struct) '
                               'that was never compiled, so the game cannot run it (%s).' % e, 'none'))
        else:
            items.append(_item('script_syntax', 'blocker', 'The %s script does not compile (%s).' % (
                'JASS' if lang == 'jass' else 'Lua', e), 'none'))
    if tree is not None and lang == 'jass':
        p('Checking the natives')
        own = unprotect._read(a, 'scripts\\blizzard.j')
        items += jass_items(tree, own.decode('latin-1') if own else None)
    if tree is not None:
        sp = single_player.analyze(text, lang, strings, tree)
        if sp['found']:
            items.append(_item('single_player_lock', 'warning', 'The map ends the game in single player mode. Since '
                               '3.0 there is no LAN, so playing alone is single player: the Doctor can unlock it.',
                               'doctor', sites=sp['sites']))
    return items, False


def _source(path, diag, codes):
    src = diag.get('restored')
    if src and os.path.isfile(src):
        return src
    if 'ntfs_copy' in codes:
        try:
            with unprotect.quiet():
                src = unprotect.restore_copy(path)[0]
        except Exception:
            src = None
        if src:
            return src
    return path


def check(path, progress=None, diag=None):
    p = progress or _nothing
    res = {'verdict': None, 'items': [], 'script': None, 'size': None, 'models': 0}
    items = res['items']
    p('Reading the archive')
    if diag is None:
        try:
            with unprotect.quiet():
                diag = unprotect.diagnose(path)
        except Exception as e:
            items.append(_item('unreadable', 'warning', 'The file cannot be read (%s).' % unprotect._error(e), 'none'))
            return _finish(res, True)
    res['script'], res['size'] = diag.get('script'), diag.get('byte_size')
    state = diag.get('fixable')
    if state == 'not_a_map':
        items.append(_item('not_a_map', 'warning', 'The file is not a Warcraft III map.', 'none'))
        return _finish(res, True)
    if state == 'cannot_read':
        items.append(_item('unreadable', 'warning', 'The archive cannot be read (%s).' % diag.get('err'), 'none'))
        return _finish(res, True)
    if state == 'incomplete':
        items.append(_item('truncated', 'blocker', 'The file is cut short: the end of the archive, where its tables '
                           'are, is missing. Only a complete copy can run.', 'none'))
        return _finish(res, False)
    if (res['size'] or 0) > MAX_MAP:
        items.append(_item('map_too_large', 'blocker', 'The map is %s; the game does not list maps above 512 MiB.'
                           % _mb(res['size']), 'none', size=res['size']))
    prot = diag.get('protections') or []
    codes = [x['code'] for x in prot]
    for x in prot:
        if x['code'] in _ARCHIVE:
            code, sev, text, fix = _ARCHIVE[x['code']]
            if x['code'] == 'unreadable_tables' and unprotect.is_carvable(diag):
                text, fix = text + ' The files are in the archive: the Doctor rebuilds it.', 'doctor'
            items.append(_item(code, sev, text, fix))
    protections = [c for c in PROTECTIONS if c in codes]
    if protections:
        items.append(_item('protected_archive', 'info', 'The archive is protected against editing tools. The game '
                           'still reads it; the Doctor removes the protection, which only matters to open or change '
                           'the map.', 'doctor', protections=protections))
    for x in prot:
        if x['code'] in _SLK:
            code, sev, text = _SLK[x['code']]
            items.append(_item(code, sev, text, 'doctor', count=x.get('n'), files=x.get('file_set')))
    if diag.get('kind') == 'campaign_info':
        items.append(_item('campaign', 'info', 'This is a campaign: check each of its maps on its own.', 'none'))
        return _finish(res, True)
    unknown = False
    src = _source(path, diag, codes)
    if res['script'] in ('jass', 'lua'):
        try:
            found, unknown = _script_items(src, diag, p)
        except Exception as e:
            found, unknown = [_item('script_unreadable', 'warning', 'The script could not be checked (%s).'
                                    % unprotect._error(e), 'none')], True
        items += found
    elif res['script'] is None and not any(x['severity'] == 'blocker' for x in items):
        items.append(_item('no_script', 'warning', 'The map has no script the game can find.', 'none'))
        unknown = True
    if res['script'] != 'kk_encrypted' and not unknown:
        found, res['models'] = model_items(src, p)
        items += found
        p('Checking the object data')
        items += object_items(src)
        p('Checking the imported files')
        items += import_items(src)
    return _finish(res, unknown)
