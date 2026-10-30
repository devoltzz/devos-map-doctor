# Devo's Map Doctor: the window, the text mode and the result texts.
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
from doctor.fix import unprotect as D

VERSION = '1.10.2'

STAGES = {
    'read_map': 'Reading the map...',
    'ntfs': 'Undoing the NTFS compression...',
    'carver': 'Rebuilding the archive from the file data...',
    'tables': 'Checking the MPQ archive...',
    'fake_files': 'Checking for fake files...',
    'counts': 'Checking the editor counters...',
    'name_list': 'Recovering file names...',
    'sector_bytes': 'Rewriting the archive with 4 KB sectors...',
    'sprotect': 'Undoing the SProtect scrambling...',
    'repair': 'Fixing the MPQ header...',
    'listing': 'Writing a real file list...',
    'ids': 'Restoring the object IDs...',
    'data_bytes': 'Fixing the data tables for Reforged 3.0...',
    'script': 'Turning the script back into JASS...',
    'editor': 'Preparing the map for the World Editor...',
    'download': 'Downloading the game files of the old versions (4 MB, once)...',
    'slk_objects': 'Making the editor object files from the SLK tables...',
    'save': 'Saving...',
    'verify': 'Checking the result...',
    'extra_models': 'Fixing the models...',
    'extra_model_names': 'Naming the models...',
    'extra_portraits': 'Removing the portrait cameras...',
    'extra_data_pointers': 'Aligning the data pointers...',
    'extra_kk_textures': 'Decrypting the KK textures...',
    'extra_disabled_icons': 'Making the disabled icons...',
    'extra_uabi': 'Moving the ability lists to the script...',
    'extra_preload': 'Preloading the first seconds...',
    'extra_single_player': 'Allowing single player...',
    'extra_card': 'Writing the map card...',
    'extra_translation': 'Applying the translation...',
    'extra_strip_indent': 'Removing the script indentation...',
    'extra_shrink': 'Making the map smaller...',
    'extra_attributes': 'Redoing the file checksums...',
    'extra_game_overrides': 'Checking the game file overrides...',
    'extra_graphics_modes': 'Importing the game files of the other graphics modes...',
    'extra_requirements': 'Checking the requirements...',
    'extra_fdf': 'Checking the frame definitions...',
    'extra_null_handles': 'Nulling the handles the script leaks...',
    'extra_minify': 'Minifying the script...',
    'extra_shrink_models': 'Shrinking the models...',
    'extra_lobby_image': 'Writing the lobby image...',
    'extra_slk_objects': 'Making the editor object files from the SLK tables...',
}

MARKS = {'vexorian': ' (VxOP mark)', 'w3p': ' (w3p mark)', 'pg2': ' (PG2 mark)', 'sprotect': ' (SProtect)'}
NO_ENCRYPTION = 'Ask the author for a copy without the KK encryption (other versions reach Maps\\dz as plain archives).'
COMPILED = {'kkwe': 'kkmap.jc (KKWE)', 'j2b': 'war3map.bin (j2b)'}

COUNT = {
    'war3map.w3r': ('region file', 'region', 'regions', 'Loading Rects'),
    'war3map.w3c': ('camera file', 'camera', 'cameras', 'Loading Cameras'),
    'war3map.w3s': ('sound file', 'sound', 'sounds', 'Loading Sounds'),
    'war3mapUnits.doo': ('unit file', 'unit', 'units', 'Loading Units'),
    'war3map.wtg': ('trigger file', 'trigger', 'triggers', 'Loading Triggers'),
    'war3map.wct': ('trigger text file', 'trigger text', 'trigger texts', 'Loading Triggers'),
    'war3map.imp': ('import list', 'imported file', 'imported files', 'the imported file list'),
    'war3map.mmp': ('minimap icon file', 'minimap icon', 'minimap icons', 'Loading Minimap Icons'),
    'war3map.doo': ('doodad file', 'doodad', 'doodads', 'Loading Doodads'),
}


def mb(n):
    return '%.1f MB' % (n / 1e6)


def num(n):
    return '{:,}'.format(n)


def pluralize(n, singular, plural):
    return '%s %s' % (num(n), singular if n == 1 else plural)


def _reason(code, field_value):
    return {
        'version_num': 'format version %d, must be 0' % field_value,
        'bad_header_size': 'header size 0x%08X, must be 0x20' % (field_value & 0xFFFFFFFF),
        'hash_position': 'bad hash table position',
        'block_position': 'block table before the header',
        'sector_bytes': 'garbage in the sector size field',
    }.get(code, code)


def _short_names(file_set):
    name_list = [a.replace('/', '\\').split('\\')[-1] for a in file_set or []]
    return (
        name_list[0]
        if len(name_list) == 1
        else ', '.join(name_list[:-1]) + ' and ' + name_list[-1]
        if name_list
        else ''
    )


def describe_data(p):
    c, n, where = p['code'], p.get('n', 0), _short_names(p.get('file_set'))
    if c == 'slk_file_column':
        return '%s: %s in the `file` column; 3.0 crashes on it.' % (where, pluralize(n, 'model', 'models'))
    if c == 'slk_levels':
        return '%s has no columns for ability levels 5 and 6: in 3.0 their values read as 0.' % where
    if c == 'slk_buttonpos':
        return ('%s half written in %s (like Buttonpos=,2): completed to (0,2).'
                % (pluralize(n, 'command button position', 'command button positions'), where))
    if c == 'fdf_stray_comment':
        return ('%s in %s that closes no /*: 3.0 rejects the file on the loading screen.'
                % (pluralize(n, 'stray */', 'stray */'), where))
    if c == 'slk_id_list':
        return ('%s in %s end in |n: 3.0 reads an ability that does not exist.'
                % (pluralize(n, 'list of abilities', 'lists of abilities'), where))
    if c == 'slk_quoted_numbers':
        return ('%s stored as text in %s: not a crash, cleaned up as well.'
                % (pluralize(n, 'number', 'numbers'), where))
    return c


def data_done(steps):
    details = (steps.get('data_bytes') or {}).get('report') or {}
    out = []
    x = details.get('file_column')
    if x:
        out.append('Moved %s in %s to UnitSkin.txt and ItemSkin.txt.'
                   % (pluralize(sum(x.values()), 'model path', 'model paths'), _short_names(x)))
    x = details.get('levels')
    if x:
        out.append('Added the columns for ability levels 5 and 6 to %s (%s).'
                   % (_short_names(x), pluralize(sum(x.values()), 'column', 'columns')))
    x = details.get('buttonpos')
    if x:
        out.append('Completed %s in %s.' % (pluralize(sum(x.values()), 'half-written button position',
                                                      'half-written button positions'), _short_names(x)))
    x = details.get('fdf_comment')
    if x:
        out.append('Removed %s from %s.' % (pluralize(sum(x.values()), 'stray */', 'stray */'), _short_names(x)))
    x = details.get('id_lists')
    if x:
        out.append(
            'Removed the |n from %s in %s.'
            % (pluralize(sum(x.values()), 'list of abilities', 'lists of abilities'), _short_names(x))
        )
    x = details.get('quoted_numbers')
    if x:
        out.append('Turned %s back into numbers in %s.'
                   % (pluralize(sum(x.values()), 'value stored as text', 'values stored as text'), _short_names(x)))
    return out


def describe(p):
    c = p['code']
    if c == 'ntfs_copy':
        lost = p.get('lost') or 0
        if not lost:
            return 'Not a protection: a copy of a compressed NTFS file.'
        pieces = ['%s short' % pluralize(lost, 'byte', 'bytes')]
        if p.get('tables_rebuilt'):
            pieces.append('%s rebuilt' % pluralize(p['tables_rebuilt'], 'table entry', 'table entries'))
        return 'Not a protection: a compressed NTFS copy (%s).' % '; '.join(pieces)
    if c == 'fake_header':
        return ('%s before the real one: tools that stop at the first header read garbage.'
                % ('A fake MPQ header sits' if p['n'] == 1 else '%s fake MPQ headers sit' % num(p['n'])))
    if c == 'missing_hm3w':
        return {'mpq_at_zero': 'The map header (HM3W) is missing: the archive starts at byte 0.',
                'user_data': 'The map header (HM3W) was replaced by an MPQ "user data" block.'}.get(
            p.get('first_pos'), 'The map header (HM3W) is missing.')
    if c == 'read_only':
        return ('MPQ Editor read-only: the header was tampered with%s (%s).'
                % (MARKS.get(p.get('mark'), ''), '; '.join(_reason(k, v) for k, v in p['reasons'])))
    if c == 'virtual_tables':
        return 'Virtual file tables (PG2): the index names are decoys.'
    if c == 'sprotect':
        return 'SProtect: %s of the %s file entries are scrambled.' % (num(p['marked']), num(p['used_entries']))
    if c == 'kk_encrypted':
        return ('Encrypted by the KK platform: %s of the map is stored outside the MPQ archive.'
                % mb(p.get('outside', 0)))
    if c == 'kk_virtual_mpq':
        return ('%s hidden after the MPQ (KK virtual MPQ, %s): "files" lists them and "extract" takes them out.'
                % (pluralize(p.get('file_set', 0), 'file', 'files'), mb(p.get('byte_size', 0))))
    if c == 'script_kkwe':
        return ('Compiled script (KKWE): the real script is kkmap.jc (%s) as bytecode.' % mb(p.get('byte_size', 0)))
    if c == 'script_j2b':
        return ('Compiled script (j2b): the real script is war3map.bin (%s) as bytecode.' % mb(p.get('byte_size', 0)))
    if c == 'full_hash_table':
        return 'The file index is 100%% full (%s entries): the MPQ Editor cannot add files.' % num(p['hash_entries'])
    if c == 'unreadable_tables':
        cv = p.get('carver') or {}
        if cv.get('w3i') and cv.get('script'):
            return ('File tables scrambled (%s entries), but %s found by content (%s encrypted).'
                    % (num(p.get('hash_entries', 0)), pluralize(cv.get('file_set') or 0, 'file was', 'files were'),
                       num(cv.get('encrypted_count') or 0)))
        return ('File tables scrambled (%s entries): nothing is readable, not even by content.'
                % num(p.get('hash_entries', 0)))
    if c == 'alias':
        if p['block_list'] == 1:
            return '1 file also answers to extra fake names (up to %s).' % num(max(1, p['maximum'] - 1))
        return ('%s files also answer to extra fake names (up to %s each).'
                % (num(p['block_list']), num(max(1, p['maximum'] - 1))))
    if c == 'fake_entries':
        return '%s to data that does not exist.' % pluralize(p['n'], 'file entry points', 'file entries point')
    if c == 'fake_files':
        return ('At least %s that the game never reads: they make the MPQ Editor slow or freeze.'
                % pluralize(p['n'], 'fake file', 'fake files'))
    if c == 'game_only_reads':
        return ('%s that only the game can read: the size or a sector is broken on purpose.'
                % pluralize(p['n'], 'File', 'Files'))
    if c == 'script_decoy':
        return 'A decoy scripts\\war3map.j (unreadable) sits next to the real script.'
    if c == 'sector512':
        return ('The MPQ sectors are 512 bytes (wSectorSize 0): old StormLib tools refuse the map; the MPQ Editor of '
                '03/10/2026 opens it.')
    if c == 'lua_wc3fuscator':
        return 'Lua script obfuscated by WC3Fuscator 2.1.'
    if c == 'lua_layers':
        return 'Lua script wrapped in loader layers (WC3Fuscator kind).'
    if c == 'locale_decoy':
        name_list = p.get('name_list') or []
        return ('%s stored only under the language codes, with a decoy under the neutral entry%s.'
                % (pluralize(p['n'], 'file is', 'files are'), ' (%s)' % ', '.join(name_list[:2]) if name_list else ''))
    if c == 'scrambled_ids':
        return ('%s object IDs were scrambled; the script reaches them by %s disguised sums.%s'
                % (num(p['n']), num(p.get('sums', 0)),
                   '' if p.get('fixable') else ' (This is a Lua map: they cannot be restored.)'))
    if c == 'invalid_doodad':
        return ('%s an object ID that does not exist (%s): the World Editor crashes on it.'
                % (pluralize(p.get('n', 0), 'doodad uses', 'doodads use'),
                   ', '.join((p.get('examples') or [])[:3]) or '?'))
    if c in D.DATA_ONLY:
        return describe_data(p)
    if c == 'inflated_counts':
        _, singular, plural, _where = COUNT.get(p['file_name'], ('file', 'record', 'records', p['file_name']))
        if p.get('reason') == 'odd_version':
            return ('%s is in a format no real map uses (%s): the editor hangs.'
                    % (p['file_name'], p.get('detail') or '?'))
        if p.get('declared') is None or p.get('reason') == 'empty':
            return 'The %s is empty or truncated: the editor cannot read it.' % p['file_name']
        d = '%s claims %s %s' % (p['file_name'], num(p['declared']), plural)
        if p.get('read_count'):
            d += ', only %s read' % pluralize(p['read_count'], singular, plural)
        d += ': the editor hangs.'
        if p.get('game'):
            d += ' Not repaired: the game reads it.'
        return d
    return c


def incomplete(inc):
    if not inc:
        return 'the file ends before its file tables'
    return ('the file tables end at byte %s and the file has %s (%s missing)'
            % (num(inc.get('end_of_tables', 0)), num(inc.get('byte_size', 0)), num(inc.get('missing_items', 0))))


def name_of(d):
    return d.get('fname') or os.path.basename(d['file_name'])


def package_text(d):
    pk = d.get('is_pack') or {}
    ext = pk.get('extension') or ''
    n, named = pluralize(pk.get('file_set') or 0, 'file', 'files'), num(pk.get('named') or 0)
    if pk.get('format') == 'pe' and ext in D.PACKAGE_EXTENSIONS:
        out = [('ok', 'Art package (a DLL with an MPQ inside, %s): %s, %s named.' % (ext, n, named))]
    elif pk.get('format') == 'pe':
        out = [('ok', 'Art package (a DLL with an MPQ inside, like a .mix, renamed %s): %s, %s named.'
                % (ext or 'without an extension', n, named))]
    elif ext in D.PACKAGE_EXTENSIONS:
        out = [('ok', 'Art package (an MPQ archive, %s): %s, %s named.' % (ext, n, named))]
    else:
        out = [('ok', 'Art package (an MPQ archive with no map inside): %s, %s named.' % (n, named))]
    out.append(('info', 'Inside: %s, %s, %s.' % (pluralize(pk.get('models') or 0, 'model', 'models'),
                                                 pluralize(pk.get('images') or 0, 'image', 'images'),
                                                 pluralize(pk.get('sounds') or 0, 'sound', 'sounds'))))
    if pk.get('err'):
        out.append(('warning', 'The file list could not be read: %s.' % pk['err']))
    out.append(('', ''))
    out.append(('ok', 'It is not a map: open the Files tab to see and extract its files.'))
    return out


NO_EDIT_TEXT = 'Not allowed to edit'


def diagnosis_text(d):
    if d['fixable'] == 'is_pack':
        return [
            ('heading', 'Diagnosis: %s' % os.path.basename(d['file_name'])),
            ('info', 'File: %s  (%s)' % (os.path.basename(d['file_name']), mb(d['byte_size']))),
            ('', ''),
        ] + package_text(d)
    out = [('heading', 'Diagnosis: %s' % os.path.basename(d['file_name'])),
           ('info', 'Map: %s  (%s)' % (name_of(d), mb(d['byte_size'])))]
    if d['fixable'] == 'not_a_map':
        return out + [('invalid', 'Not a Warcraft III map: no MPQ archive inside.')]
    if d['fixable'] == 'incomplete':
        return out + [('invalid', 'Incomplete map file: %s.' % incomplete(d.get('incomplete'))),
                      ('info', 'Get a complete copy of the map.')]
    if d['fixable'] == 'cannot_read':
        if d.get('no_edit'):
            return out + [('invalid', NO_EDIT_TEXT)]
        return out + [('invalid', 'The MPQ archive could not be read (%s).' % d.get('err'))]
    out.append(('', ''))
    protections = [p for p in d['protections'] if p['code'] not in D.DATA_ONLY]
    data_bytes = [p for p in d['protections'] if p['code'] in D.DATA_ONLY]
    if d.get('no_edit'):
        out.append(('invalid', NO_EDIT_TEXT))
        if protections:
            out += [('', ''), ('heading2', 'Protection found:')] + [
                ('warning', '  - ' + describe(p)) for p in protections
            ]
        return out
    if not protections:
        out.append(('ok', 'No MPQ protection found.'))
    else:
        out.append(('heading2', 'Protection found:'))
        for p in protections:
            out.append(('warning', '  - ' + describe(p)))
        out.append(('', ''))
        if d['fixable'] == 'impossible':
            out.append(('invalid', "This map cannot be unprotected: the real map is not inside this file."))
            out.append(('info', NO_ENCRYPTION))
        elif set(p['code'] for p in protections) <= set(D.BUTTON3_ONLY):
            out.append(('ok', 'Can be fixed: click "Open in World Editor".'))
        else:
            out.append(('ok', 'Can be fixed: click "Fix map".'))
    if d.get('slk'):
        out.append(('info', 'SLK mode: %s data table files.' % num(len(d['slk']))))
    if d.get('jassnative'):
        out.append(('info', 'Compiled in the JassNative Editor.'))
    if d.get('repacker'):
        out.append(
            ('info', 'Repacked by %s: the script and the editor files may have been regenerated.' % d['repacker'])
        )
    if data_bytes:
        out.append(('', ''))
        out.append(('heading2', 'Needs fixing for Reforged 3.0:'))
        for p in data_bytes:
            out.append(('warning', '  - ' + describe(p)))
        out.append(('', ''))
        out.append(('ok', 'Both actions fix it.'))
    lf = d.get('listfile')
    if lf:
        if lf['status'] == 'ok':
            out.append(('info', 'File list: complete (%s).' % pluralize(lf['file_set'], 'file', 'files')))
        elif lf['status'] == 'absent':
            out.append(('info', 'File list: missing (%s without a name).' % pluralize(lf['file_set'], 'file', 'files')))
        else:
            out.append(('info', 'File list: %s of %s files are named.' % (num(lf['named']), num(lf['file_set']))))
    out.append(('', ''))
    ed = d['editor']
    status = ed.get('status')
    map_list = (d.get('campaign_info') or {}).get('map_list') or []
    if d.get('kind') == 'campaign_info':
        ready_count = sum(1 for m in map_list if m.get('editor') == 'ready')
        out.append(('info', 'Campaign: %s inside, %s ready for the editor.'
                    % (pluralize(len(map_list), 'map', 'maps'), num(ready_count))))
    if status == 'ready':
        out.append(('ok', 'World Editor: the %s already opens.'
                    % ('campaign' if d.get('kind') == 'campaign_info' else 'map')))
    elif status == 'campaign_needs_work':
        for m in map_list:
            if m.get('editor') != 'ready':
                out.append(
                    (
                        'warning',
                        '  - %s: %s'
                        % (
                            m['fname'],
                            'needs work (%s)' % ', '.join(m.get('protections') or [])
                            if m.get('editor') == 'needs_work'
                            else editor_reason(m.get('editor')),
                        ),
                    )
                )
        out.append(('ok', 'Click "Open in World Editor".'))
    elif status == 'needs_work':
        gaps = []
        blocking = set(p['code'] for p in d['protections']) & set(D.EDITOR_BLOCKERS)
        if blocking - {'script_kkwe', 'script_j2b'}:
            gaps.append('the protection removed')
        if blocking & {'script_kkwe', 'script_j2b'}:
            gaps.append('the script back into JASS')
        if ed.get('w3i') == 'truncated':
            gaps.append('war3map.w3i restored')
        if ed.get('trigger_list'):
            gaps.append('the YDWE triggers rewritten')
        for missing in gaps:
            out.append(('warning', 'World Editor: needs %s.' % missing))
        if not gaps:
            out.append(('warning', 'World Editor: needs the fixes above.'))
        if ed.get('missing_items'):
            missing_items = list(ed['missing_items'])
            if len(missing_items) > 4:
                out.append(
                    (
                        'warning',
                        'World Editor: missing %s (+%d more).' % (', '.join(missing_items[:4]), len(missing_items) - 4),
                    )
                )
            else:
                out.append(('warning', 'World Editor: missing %s.' % ', '.join(missing_items)))
        out.append(('ok', 'Click "Open in World Editor".'))
    else:
        out.append(('invalid', 'World Editor: ' + editor_reason(status)))
    if ed.get('duplicate_textures'):
        copies = sum(len(g) - 1 for g in ed['duplicate_textures'])
        out.append(('info', 'One imported texture is a copy of another one (harmless; "Make the map smaller, '
                    'losing nothing" stores them once).' if copies == 1 else '%s imported textures are copies of other '
                    'ones (harmless; "Make the map smaller, losing nothing" stores them once).' % num(copies)))
    return out


def version_lines(r):
    ev = (r.get('editor') or {}).get('editor_target') or {}
    if not ev:
        return []
    if ev.get('editor_profile') == 'jn':
        return jassnative_lines(r, ev)
    out = [('info', 'Made for World Editor %s: the map keeps its version (war3map.w3i, triggers and object data in the '
                    'formats that editor reads).' % ev.get('version_num'))]
    out.extend(mark_lines(r))
    if ev.get('needs_jasshelper'):
        out.append(('warning', 'World Editor %s has no JassHelper: the custom script uses //! inject or globals of its '
                               'own, so save the map with Jass NewGen Pack or WEX.' % ev.get('version_num')))
    else:
        out.append(('info', 'World Editor %s saves it without JassHelper.' % ev.get('version_num')))
    for warning in ev.get('warnings') or []:
        out.append(('warning', 'Check in World Editor %s: %s.' % (ev.get('version_num'), warning)))
    missing_items = ev.get('missing_functions') or []
    if missing_items:
        out.append(
            (
                'warning',
                'The script calls %s that Warcraft III %s does not have (%s%s): the editor will not save '
                'it as it is.'
                % (
                    pluralize(len(missing_items), 'function', 'functions'),
                    ev.get('version_num'),
                    ', '.join(missing_items[:3]),
                    '...' if len(missing_items) > 3 else '',
                ),
            )
        )
    return out


def mark_lines(r):
    jn = (r.get('editor') or {}).get('jassnative') or {}
    if jn.get('removed'):
        return [('info', 'The REFORGED_MODE line left the map script and the custom script: the JassNative Editor '
                         'writes it again on every save.')]
    if jn:
        return [('warning', 'The script keeps its REFORGED_MODE line (%s): the JassNative Editor writes another one on '
                            'save, so the map does not save there as it is.' % jn.get('reason'))]
    return []


def jassnative_lines(r, ev):
    out = [('info', 'Made for the JassNative Editor: the map keeps its version (1.27), and the triggers use that '
                    "editor's own functions and variable types.")]
    out.extend(mark_lines(r))
    for warning in ev.get('warnings') or []:
        out.append(('warning', 'Check in the JassNative Editor: %s.' % warning))
    missing_items = ev.get('missing_functions') or []
    if missing_items:
        out.append(
            (
                'warning',
                'The script calls %s that Warcraft III %s does not have (%s%s): the editor will not save '
                'it as it is.'
                % (
                    pluralize(len(missing_items), 'function', 'functions'),
                    '1.27',
                    ', '.join(missing_items[:3]),
                    '...' if len(missing_items) > 3 else '',
                ),
            )
        )
    return out


def editor_reason(status):
    return {
        'script_kkwe': 'the script is compiled (KKWE) and the editor cannot read it.',
        'script_j2b': 'the script is compiled and encrypted (j2b) and the editor cannot read it.',
        'script_none': 'the map has no script.',
        'script_cut_off': 'the map script is cut off (the map file is incomplete).',
        'script_kk_encrypted': 'the real map is encrypted outside this file (KK platform).',
        'impossible': 'the real map is encrypted outside this file (KK platform).',
        'unreadable': 'the file tables are scrambled and no name resolves.',
        'is_pack': 'this is an art package, not a map.',
        'w3i_unreadable': 'war3map.w3i is in a format the Doctor cannot read.',
        'w3i_missing': 'war3map.w3i is missing.',
    }.get(status, status)


def _fixes_done(details, steps, before):
    out = []
    if steps.get('ntfs'):
        nt = steps['ntfs']
        tab = nt.get('tables') or {}
        out.append('Decompressed the NTFS data inside the file%s.'
                   % ('; rebuilt the %s cut by the copy' % pluralize(tab.get('rebuilt') or 0, 'table entry',
                                                                     'table entries')
                      if tab.get('rebuilt') else ''))
    if steps.get('carver'):
        cv = steps['carver']
        name_list = cv.get('name_list') or {}
        extra = ', %s unnamed' % num(name_list['unnamed']) if name_list.get('unnamed') else ''
        out.append('Rebuilt the map from its files: %s found by content%s.'
                   % (pluralize(cv.get('file_set') or 0, 'file', 'files'), extra))
    if steps.get('sprotect'):
        out.append('Undid the SProtect scrambling.')
    if details.get('new_tables'):
        out.append('Rebuilt the file tables with %s (no decoys).'
                   % pluralize(details['new_tables'], 'real file', 'real files'))
    if steps.get('sector_bytes'):
        out.append('Rewrote the archive with 4 KB sectors.')
    if details.get('locale_decoys'):
        out.append('Brought back %s hidden behind language entries.'
                   % pluralize(details['locale_decoys'], 'file', 'files'))
    if details.get('fake_zeroed'):
        out.append('Disabled the fake MPQ header.' if details['fake_zeroed'] == 1 else
                   'Disabled %s fake MPQ headers.' % num(details['fake_zeroed']))
    fields = [c[0] for c in details.get('fields') or []]
    if 'dwHeaderSize' in fields or 'wFormatVersion' in fields or 'wSectorSize' in fields or \
            details.get('block_table_moved') or details.get('hash_table_moved'):
        out.append('Fixed the MPQ header.')
    if details.get('hm3w') in ('written', 'prefixed'):
        out.append('Added the map header (HM3W).')
    if details.get('junk_blocks'):
        out.append('Removed %s.' % pluralize(details['junk_blocks'], 'fake file', 'fake files'))
    if details.get('deleted_aliases'):
        out.append('Removed %s.' % pluralize(details['deleted_aliases'], 'fake file name', 'fake file names'))
    listing = steps.get('listing') or {}
    if listing.get('fake_count'):
        out.append(
            'Removed %s to missing data.'
            % pluralize(listing['fake_count'], 'entry that pointed', 'entries that pointed')
        )
    if listing.get('listfile'):
        out.append('Wrote a real file list with %s.' % pluralize(listing['listfile'], 'name', 'names'))
    if listing.get('rewritten'):
        out.append('Rewrote %s that only the game could read.' % pluralize(len(listing['rewritten']), 'file', 'files'))
    if steps.get('ids'):
        out.append('Replaced %s with clean ones (the script was updated).'
                   % pluralize(steps['ids'], 'scrambled object ID', 'scrambled object IDs'))
    return out or ['Fixed the MPQ archive.']


def _common_failures(r, verb):
    e = r['status']
    if e == 'not_a_map':
        return [('invalid', 'Not a Warcraft III map: no MPQ archive inside.')]
    if e == 'cannot_read':
        return [('invalid', 'The MPQ archive could not be read (%s).' % (r['before'] or {}).get('err'))]
    if e == 'impossible':
        return [('invalid', "This map cannot be %s: the real map is encrypted outside it (KK platform)." % verb),
                ('info', 'No file was written.'),
                ('info', NO_ENCRYPTION)]
    if e == 'incomplete':
        return [('invalid', "This map cannot be %s: the file is incomplete." % verb),
                ('info', '%s.' % incomplete((r.get('before') or {}).get('incomplete'))),
                ('info', 'Get a complete copy.')]
    if e == 'unreadable':
        return [('invalid', "This map cannot be %s: %s" % (verb, editor_reason('unreadable')))]
    if e == 'is_pack':
        return [('invalid', "This file cannot be %s: it is an art package, not a map." % verb),
                ('info', 'No file was written.'),
                ('info', 'Open the Files tab to see and extract its files: Extract all, Extract models.')]
    if e == 'failed':
        out = [('invalid', 'Something went wrong: nothing was saved, your map is unchanged.')]
        err = r.get('err') or ''
        content = r.get('content') or {}
        if content.get('different') or content.get('missing_items'):
            out.append(('warning', 'The final check found a changed file: post the diagnosis text to add this case.'))
        if 'PermissionError' in err:
            out.append(('warning', 'The copy could not be written there: try another folder.'))
        return out + [('info', 'Details: %s' % r.get('err'))]
    return None


def unprotection_text(r):
    d = r['before']
    out = [('heading', 'Fix map: %s' % os.path.basename(d['file_name']))]
    failure = _common_failures(r, 'unprotected')
    if failure:
        return out + failure
    if r['status'] == 'nothing_to_do':
        if r.get('for_button3'):
            return out + [('ok', 'Nothing to remove in the MPQ archive. No file was written.'),
                          ('info', 'The World Editor problems above are fixed by "Open in World Editor".')]
        return out + [('ok', 'No protection found: nothing to remove. No file was written.')]
    if r['status'] == 'nothing_selected':
        return out + [('ok', 'All steps turned off: nothing to do. No file was written.')]
    data_only = [k for k in r['steps'] if k != 'data_bytes'] == []
    if data_only:
        out.append(('ok', 'Fixed for Reforged 3.0.' if r['status'] == 'done' else
                    'Fixed for Reforged 3.0, with leftovers (see below).'))
    else:
        out.append(('ok', 'Protection removed.' if r['status'] == 'done' else
                    'Protection removed, with leftovers (see below).'))
    out.append(('file_path', 'Saved as: %s' % r['output']))
    out.append(('', ''))
    if not data_only:
        for line in _fixes_done(r['steps'].get('repair') or {}, r['steps'], d):
            out.append(('info', '  - ' + line))
    for line in data_done(r['steps']):
        out.append(('info', '  - ' + line))
    c = r.get('content') or {}
    if c.get('identical'):
        on_purpose = []
        if r['steps'].get('ids'):
            on_purpose.append('the new object ids')
        if (r['steps'].get('data_bytes') or {}).get('modified'):
            on_purpose.append('the data tables')
        out.append(('info', '  - Checked: %s identical%s.'
                    % (pluralize(c['identical'], 'file', 'files'),
                       ' (%s changed on purpose)' % '; '.join(on_purpose) if on_purpose else '')))
    after_diag = (r.get('after_diag') or {}).get('protections') or []
    button3 = [p for p in after_diag if p['code'] in D.BUTTON3_ONLY]
    left_out = set(r.get('left_out') or [])
    unresolved = [p for p in after_diag if p['code'] not in D.BUTTON3_ONLY and p['code'] not in D.DATA_ONLY and
                  p['code'] not in left_out]
    for p in after_diag:
        if p['code'] in left_out:
            out.append(('info', '  - Left as you chose: ' + describe(p)))
        elif p['code'] in D.DATA_ONLY:
            out.append(('warning', '  - Not fixed: ' + describe(p)))
    if button3:
        out.append(('', ''))
        out.append(('info', 'Left for "Open in World Editor":'))
        for p in button3:
            out.append(('info', '  - ' + describe(p)))
    if unresolved:
        out.append(('', ''))
        out.append(('warning', 'Still present:'))
        for p in unresolved:
            out.append(('warning', '  - ' + describe(p)))
        if any(p['code'] == 'alias' for p in unresolved):
            out.append(('info', '  Kept: without the real name, dropping the wrong one breaks the map.'))
    return out


def port_text(r):
    from doctor.port import map_port
    out = []
    for ln in map_port.report_text(r).splitlines():
        if not ln.strip() or set(ln.strip()) <= {'-', '='}:
            continue
        if ln.startswith('- '):
            out.append(('warning' if 'FAIL' in ln else 'info', '  ' + ln))
        elif ln.startswith(('Result:', 'Ported map:')):
            out.append(('ok' if r.get('resultado', '').startswith('ported') else 'invalid', ln))
        elif ln.startswith('The port stopped'):
            out.append(('invalid', ln))
        elif ln.startswith('A stub compiles'):
            out.append(('info', '  ' + ln))
        else:
            out.append(('heading' if not out else 'heading2', ln))
    return out


def editor_text(r):
    d = r['before']
    out = [('heading', 'Open in World Editor: %s' % os.path.basename(d['file_name']))]
    failure = _common_failures(r, 'prepared for the World Editor')
    if failure:
        return out + failure
    if r['status'] == 'nothing_to_do':
        return out + [('ok', 'Nothing to do: the map already opens. No file was written.')]
    if r['status'] == 'script_not_restored':
        return out + [('invalid', 'Not possible: the compiled script (%s) cannot be turned back into JASS. '
                                  'Nothing was saved.' % COMPILED.get(d.get('script'), 'the bytecode')),
                      ('info', 'Why: %s' % r.get('err'))]
    if r['status'] in ('script_lua', 'script_kkwe', 'script_j2b', 'script_none', 'script_cut_off', 'w3i_unreadable',
                       'w3i_missing', 'unreadable'):
        return out + [('invalid', 'Not possible: ' + editor_reason(r['status']))]
    version_num = r.get('editor_version_used')
    if r['status'] == 'wrong_editor_version':
        return out + [
            ('invalid', 'Not possible in World Editor %s: %s. Nothing was saved.' % (version_num, r.get('err'))),
            ('info', 'Choose the Reforged World Editor: the map belongs to a newer editor than %s.' % version_num),
        ]
    if r['status'] == 'no_version_files':
        return out + [('invalid', 'The game files of Warcraft III %s are missing (%s): the Doctor checks the triggers '
                                  'against them. Nothing was saved.' % (version_num, r.get('err')))]
    out.append(('ok', 'Ready for the World Editor.' if r['status'] == 'done' else
                'Ready for the World Editor, with leftovers (see below).'))
    out.append(('file_path', 'Saved as: %s' % r['output']))
    out.extend(version_lines(r))
    sl = r.get('slk_objects')
    if sl:
        if sl.get('state') == 'done':
            out.append(('info', '  - The map keeps its objects in SLK tables, which no World Editor reads: the editor '
                                'object files were made from them (%s).' % ', '.join(sl.get('written') or [])))
            for _st, _tx in sl.get('lines') or []:
                out.append(('info', '      ' + _tx))
        elif sl.get('state') != 'nothing_to_do':
            why = sl.get('reason') or sl.get('error') or '; '.join(
                _tx.rstrip('.') for _st, _tx in sl.get('lines') or [] if _st == 'bad') or '; '.join(
                _tx.rstrip('.') for _st, _tx in sl.get('lines') or [] if _st == 'warn') or sl.get('state')
            out.append(
                (
                    'warning',
                    '  - The map keeps its objects in SLK tables, and the editor object files could not be '
                    'made from them: %s. The editor will show the units as "Object ID".' % why,
                )
            )
    ren = (r.get('editor') or {}).get('renamed_locals') or []
    if ren:
        out.append(
            (
                'info',
                '  - %s renamed inside %s (JassHelper refuses a local named like a function or a '
                'global; the game does not).'
                % (
                    pluralize(len(ren), 'local variable', 'local variables'),
                    pluralize(len(set(x[0] for x in ren)), 'function', 'functions'),
                ),
            )
        )
    kept = (r.get('editor') or {}).get('kept_locals') or []
    if kept:
        out.append(('warning', '  - %s kept the name of a global array (%s): that is how a memory library reads the '
                               "array's address in the game. JassHelper may refuse it when you save; renaming it would "
                               'stop the map in the game.' % (pluralize(len(kept), 'local variable', 'local variables'),
                                                           ', '.join(sorted(set(x[1] for x in kept))[:3]))))
    out.append(('', ''))
    if (r.get('editor') or {}).get('campaign_info'):
        for m in r['editor'].get('map_list') or []:
            out.append(
                (
                    'info' if m['status'] in ('done', 'partial') else 'warning',
                    '  - %s: %s'
                    % (
                        m['fname'],
                        {'done': 'prepared for the editor', 'partial': 'prepared, with leftovers'}.get(
                            m['status'], 'not possible (%s)' % editor_reason(m['status'])
                        ),
                    ),
                )
            )
        return out
    unprot = r.get('unprotection')
    if unprot and unprot.get('status') in ('done', 'partial'):
        if [k for k in unprot['steps'] if k != 'data_bytes']:
            out.append(('info', '  - First removed the protection:'))
            for line in _fixes_done(unprot['steps'].get('repair') or {}, unprot['steps'], d):
                out.append(('info', '      ' + line))
        for line in data_done(unprot['steps']):
            out.append(('info', '  - ' + line))
    details = r.get('editor') or {}
    sv = details.get('script_restore') or {}
    if sv:
        out.append(('info', '  - Turned the script back into JASS (%s): %s, %s.'
                    % ('KKWE' if sv.get('kind') == 'kkwe' else 'j2b',
                       pluralize(sv.get('functions', 0), 'function', 'functions'),
                       pluralize(sv.get('globals_block', 0), 'global', 'globals'))))
        pj = str(sv.get('pjass') or '')
        out.append(('info', '      Proved: compiled again, it gives the same %s instructions%s.'
                    % (num(sv.get('instructions', 0)),
                       '' if pj.startswith('skipped') else '; pjass finds no error')))
        if sv.get('hooks'):
            out.append(('info', '      %s plugin functions came back as native declarations.'
                        % pluralize(sv['hooks'], 'function', 'functions')))
        if sv.get('hooks_left_out'):
            outside = sv['hooks_left_out']
            out.append(('info', '      Left out %s whose name Reforged declares itself (%s%s).'
                        % (num(len(outside)), ', '.join(outside[:2]), '...' if len(outside) > 2 else '')))
        if sv.get('clashes'):
            ch = sv['clashes']
            out.append(('warning', '      %s the script defines %s also defined by Reforged (%s%s).'
                        % (pluralize(len(ch), 'name', 'names'), 'is' if len(ch) == 1 else 'are', ', '.join(ch[:2]),
                           '...' if len(ch) > 2 else '')))
    if details.get('regenerated_triggers'):
        out.append(('info', '  - The YDWE triggers went to the map script in the custom script.'))
    if details.get('w3i_tail'):
        out.append(('info', '  - Restored the cut end of war3map.w3i.'))
    if details.get('w3i_raised'):
        out.append(('info', '  - war3map.w3i saved as version 31 (TFT).'))
    if str(details.get('w3i') or '').startswith('new_version'):
        out.append(('info', '  - war3map.w3i is newer: left as it is.'))
    mentioned = set()
    for x in details.get('count') or []:
        label, singular, plural, _where = COUNT.get(x['file_name'], ('file', 'record', 'records', ''))
        mentioned.add(x['file_name'])
        where = x.get('where') or ''
        if x.get('pair'):
            out.append(('info', '  - Rebuilt war3map.wtg and war3map.wct from the map script.'))
        elif x.get('from_script'):
            where = x.get('where') or ''
            before = x.get('in_file')
            if x.get('reason') == 'odd_version':
                out.append(('info', '  - Rebuilt %s from the %s in the script (a format no real map uses).'
                            % (x['file_name'], where)))
            elif x.get('reason') in ('does_not_fit', 'short_read'):
                out.append(('info', '  - Rebuilt %s from the %s in the script: it claimed %s.'
                            % (x['file_name'], where, num(x['declared']) if x.get('declared') is not None else 'none')))
            elif before is None:
                out.append(('info', '  - Added the %s from the script (%s).' % (plural, where)))
            else:
                out.append(('info', '  - Placed the %s from the script (%s): the file had %s.'
                            % (pluralize(x['new'], singular, plural), where,
                               pluralize(before, singular, plural) if before else 'none')))
            if x.get('placed_items') or x.get('with_abilities'):
                pieces = []
                if x.get('placed_items'):
                    pieces.append(pluralize(x['placed_items'], 'item on the ground', 'items on the ground'))
                if x.get('with_abilities'):
                    pieces.append('%s with the abilities and inventory the script gives them'
                                  % pluralize(x['with_abilities'], 'hero', 'heroes'))
                out.append(('info', '      Among them, %s.' % ' and '.join(pieces)))
            if x.get('removed_risky'):
                n = sum(x['removed_risky'].values())
                out.append(('info', '  - Left out %s: their model (a map file no doodad uses) crashes 3.0.'
                            % pluralize(n, 'unit', 'units')))
        elif x.get('declared') is None or x.get('reason') == 'empty':
            out.append(('info', '  - Replaced the empty/truncated %s (%s) with an empty one.'
                        % (label, x['file_name'])))
        else:
            out.append(('info', '  - Rewrote the %s (%s) with the %s that read cleanly: it claimed %s.'
                        % (label, x['file_name'], pluralize(x['new'], singular, plural), num(x['declared']))))
    generated = [n for n in details.get('new_ones') or [] if n in ('war3map.wtg', 'war3map.wct')] + list(
        details.get('replaced') or []
    )
    others = [n for n in details.get('new_ones') or []
              if n not in ('war3map.wtg', 'war3map.wct', 'war3map.imp') and n not in mentioned]
    if others:
        out.append(('info', '  - Editor-only files: %s.' % ', '.join(others)))
    if details.get('script_at_root'):
        out.append(('info', '  - The map script moved from the scripts folder to war3map.j, the only place the World '
                            'Editor reads it.'))
    if details.get('no_slot'):
        outside = list(details['no_slot'])
        essential = [n for n in outside if n in ('war3map.wtg', 'war3map.wct', 'war3map.imp')]
        out.append(('warning', '  - The file index is 100%% full: no room for %s.' % ', '.join(outside)))
        if essential:
            out.append(('invalid', '      Send me this map: the editor needs %s.' % ', '.join(essential)))
        else:
            out.append(('info', '      The editor creates them when you save.'))
    lua = bool(details.get('lua'))
    restoration = details.get('restoration') or {}
    restored = bool(generated and restoration.get('used'))
    if restored:
        out.append(('info', '  - Restored the triggers: %s as GUI, %s as custom text, %s.'
                    % (pluralize(restoration.get('gui', 0), 'trigger', 'triggers'),
                       pluralize(restoration.get('as_text', 0), 'trigger', 'triggers'),
                       pluralize(restoration.get('variable_count', 0), 'variable', 'variables'))))
        if restoration.get('names_obfuscated'):
            out.append(('info', '      The script names were scrambled: the triggers are named after what fires them.'))
        for ln in (restoration.get('summary') or [])[1:]:
            out.append(('info', '      ' + ln.strip()))
        if restoration.get('helpers'):
            out.append(('info', '      %s went to the custom script header.'
                        % pluralize(len(restoration['helpers']), 'helper function', 'helper functions')))
        out.append(('info', '  - The rest of the script is in the custom script of the trigger editor%s.'
                    % (', inside do ... end' if lua else '')))
    elif generated and restoration.get('reason'):
        out.append(('info', '  - The triggers went to the custom script (not restorable as GUI).'))
        out.append(('info', '      Because: %s' % restoration['reason']))
    if generated and lua and not restored:
        out.append(('info', '  - The whole Lua script went to the custom script (do ... end).'))
    elif generated and not restored and not restoration.get('reason'):
        out.append(('info', '  - The whole script went to the custom script.'))
    if generated and not restored:
        for ln in (details.get('optimizer') or {}).get('line_list') or []:
            out.append(('info', '  - ' + ln))
    if 'war3map.imp' in (details.get('new_ones') or []):
        out.append(('info', '  - Listed %s, so the editor keeps them.'
                    % pluralize(details.get('imported', 0), 'imported file', 'imported files')))
    elif details.get('imp_added'):
        out.append(('info', '  - Added %s to war3map.imp: the editor keeps only listed files.'
                    % pluralize(details['imp_added'], 'file', 'files')))
    unnamed = details.get('unnamed') or {}
    if sum(unnamed.values()):
        pieces = [pluralize(unnamed[k], singular, plural) for k, singular, plural in (
            ('models', 'model', 'models'), ('images', 'image', 'images'), ('others', 'other file', 'other files'))
            if unnamed.get(k)]
        n = sum(unnamed.values())
        out.append(('warning', '  - %s in the map %s no recoverable name (%s): the editor drops them.'
                    % (pluralize(n, 'file', 'files'), 'has' if n == 1 else 'have', ', '.join(pieces))))
    for _warning in (details.get('warnings') or [])[:8]:
        out.append(('warning', '  - A step was skipped: %s' % _warning))
    out.append(('', ''))
    out.append(('info', 'Good to know:'))
    ev = details.get('editor_target') or {}
    if lua:
        out.append(('info', '  - Test the map after saving it from the editor.'))
    elif ev.get('editor_profile') == 'jn':
        out.append(
            (
                'info',
                '  - Save it with JassHelper on and the Reforged mode off (the defaults); if the map will go '
                'to Reforged later, turn off "StringHash 미리 계산" (StringHash precalculation) first.',
            )
        )
    elif ev and not ev.get('needs_jasshelper'):
        out.append(('info', '  - World Editor %s saves it as it is: no JassHelper needed.' % ev.get('version_num')))
    elif ev:
        out.append(('info', '  - Save it with JassHelper enabled (Jass NewGen Pack or WEX on World Editor %s).'
                    % ev.get('version_num')))
    else:
        out.append(('info', '  - Keep JassHelper enabled (the default) when you save the map.'))
    if sv.get('natives') or sv.get('hooks'):
        out.append(('info', '  - The script declares %s only the KK platform provides: the map will not run until they '
                            'are ported.' % pluralize(sv.get('natives', 0) + sv.get('hooks', 0), 'native', 'natives')))
    if generated:
        placed_files = set(x['file_name'] for x in details.get('count') or [] if x.get('from_script'))
        if not placed_files:
            out.append(('info', '  - Units, regions and sounds the script creates do not show in the editor.'))
    if details.get('renamed_doodads'):
        out.append(
            (
                'info',
                '  - Gave %s the ID the game renamed it to (%s).'
                % (
                    pluralize(sum(x['n'] for x in details['renamed_doodads']), 'doodad', 'doodads'),
                    ', '.join(
                        '%s -> %s x%d' % (x['from_'], x['new_value'], x['n']) for x in details['renamed_doodads']
                    ),
                ),
            )
        )
    if details.get('doodad_parents_renamed'):
        out.append(('info', '  - Based %s on the ID the game renamed its parent to (%s).'
                    % (pluralize(len(details['doodad_parents_renamed']), 'object', 'objects'),
                       ', '.join('%s: %s -> %s' % (x['object_data'], x['from_'], x['new_value'])
                                 for x in details['doodad_parents_renamed'][:4]))))
    if details.get('doodads_outside'):
        out.append(('info', '  - Removed %s whose object ID does not exist (%s).'
                    % (pluralize(details['doodads_outside'], 'doodad', 'doodads'),
                       ', '.join('%s x%d' % (x['id'], x['n']) for x in (details.get('doodads') or [])[:2]))))
    if details.get('skin'):
        out.append(('info', '  - Moved the models to the skin files (%s).' % ', '.join(details['skin'])))
    if details.get('engine_textures'):
        out.append(('info', '  - Left the map\'s %s out of the editor copy (3.0 crashed on it).'
                    % ', '.join(details['engine_textures'])))
    clusters = details.get('duplicate_textures') or []
    changed_textures = [m for g in clusters for m in g['modified']]
    if changed_textures:
        seen = []
        for m in changed_textures:
            b = os.path.basename(m.replace('\\', '/'))
            if b not in seen:
                seen.append(b)
        out.append(('info', '  - Rewrote %s in %s (%s): no two are the same file now.'
                    % (pluralize(len(changed_textures), 'imported texture', 'imported textures'),
                       pluralize(len(clusters), 'group', 'groups'),
                       ', '.join(seen[:2]) + ('...' if len(seen) > 2 else ''))))
    unresolved = (r.get('after_diag') or {}).get('protections') or []
    if unresolved:
        out.append(('warning', 'Still present:'))
        for p in unresolved:
            out.append(('warning', '  - ' + describe(p)))
    return out


def execute(action_code, map_path, progress=None, safe_units=True):
    if action_code == 'diag':
        return diagnosis_text(D.diagnose(map_path, progress))
    from doctor.fix import no_edit
    if no_edit.read(map_path):
        return [('heading', os.path.basename(map_path)), ('invalid', NO_EDIT_TEXT)]
    if action_code == 'unprotect':
        return unprotection_text(D.unprotect(map_path, D.free_output(map_path, '_fixed'), progress))
    return editor_text(D.prepare_for_editor(map_path, D.free_output(map_path, '_editor'), progress,
                                            safe_units=safe_units))


def window(initial_map_path=None):
    from doctor.app import doctor_app
    try:
        import updater
    except ImportError:
        updater = None
    try:
        icon_file = icon_ico()
    except OSError:
        icon_file = None
    if updater is not None:
        updater.cleanup()
    from doctor.app import doctor_cli
    doctor_cli.install_launcher()
    doctor_app.run(VERSION, initial_map_path, updater, icon_file)


def icon_ico():
    base = getattr(sys, '_MEIPASS', os.path.join(HERE, 'assets'))
    p = os.path.join(base, 'devos_map_doctor.ico')
    if sys.platform.startswith('linux'):
        p = os.path.splitext(p)[0] + '.png'
    if not os.path.isfile(p):
        raise OSError('no icon')
    return p


def _no_console():
    missed = False
    for fname in ('stdout', 'stderr'):
        if getattr(sys, fname) is None:
            setattr(sys, fname, open(os.devnull, 'w', encoding='utf-8'))
            missed = True
    return missed


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    missed = _no_console()
    if '--worker' in argv:
        from doctor.app import doctor_app
        return doctor_app.worker_main(sys.modules[__name__])
    from doctor.app import doctor_cli
    if missed and argv and '--cli' not in argv and os.path.isabs(argv[0]) and not os.path.isfile(argv[0]):
        window(None)
        return 0
    cli_only = ('--help', '-h', '--version', '--json-schema')
    if '--cli' in argv or (argv and not argv[0].startswith('--') and not os.path.isfile(argv[0])) or \
            (argv and argv[0] in cli_only) or \
            (argv and any(a in cli_only for a in argv) and all(a in cli_only + ('--json', '--quiet') for a in argv)):
        return doctor_cli.main([a for a in argv if a != '--cli'], sys.modules[__name__], VERSION)
    if '--text' in argv:
        log = next((a.split('=', 1)[1] for a in argv if a.startswith('--log=')), None)
        out = open(log, 'w', encoding='utf-8') if log else sys.stdout
        try:
            out.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass
        args = [a for a in argv if not a.startswith('--')]
        if not args or not os.path.isfile(args[0]):
            print('usage: --text <map.w3x> [--unprotect] [--editor] [--log=<file>]', file=out)
            if log:
                out.close()
            return 2
        map_path = args[0]
        action_codes = (
            ['diag'] + (['unprotect'] if '--unprotect' in argv else []) + (['editor'] if '--editor' in argv else [])
        )
        safe_units = '--units=all' not in argv
        try:
            for action_code in action_codes:
                for st, txt in execute(
                    action_code,
                    map_path,
                    progress=lambda c: print('   [%s]' % STAGES.get(c, c), file=out),
                    safe_units=safe_units,
                ):
                    print(('## ' if st == 'heading' else '') + txt, file=out)
                print(file=out)
        finally:
            if log:
                out.close()
        return 0
    args = [a for a in argv if not a.startswith('--')]
    window(os.path.normpath(args[0]) if args and os.path.isfile(args[0]) else None)
    return 0


if __name__ == '__main__':
    sys.exit(main())
