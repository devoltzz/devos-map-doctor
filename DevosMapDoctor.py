# Devo's Map Doctor: the window, the text mode and the result texts.
import os
import queue
import sys
import threading
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
if not getattr(sys, 'frozen', False):
    sys.path.insert(0, os.path.join(HERE, 'engine'))
import unprotect as D
import updater

APP = "Devo's Map Doctor"
VERSION = '1.0'

STAGES = {
    'read_map': 'Reading the map...',
    'ntfs': 'Undoing the NTFS compression left inside the copied file...',
    'carver': 'Rebuilding the archive from the file data (its file tables are unreadable)...',
    'tables': 'Checking the MPQ archive...',
    'fake_files': 'Checking every file entry for fake files...',
    'counts': 'Checking the editor files for an inflated counter...',
    'name_list': 'Recovering file names (this can take a few minutes on big maps)...',
    'sector_bytes': 'Rewriting the archive with normal 4 KB sectors...',
    'sprotect': 'Undoing the SProtect scrambling...',
    'repair': 'Fixing the MPQ header and removing fake files...',
    'listing': 'Writing a real file list...',
    'ids': 'Restoring the scrambled object IDs...',
    'editor': 'Adding what the World Editor needs...',
    'save': 'Saving...',
    'verify': 'Checking the result...',
}

MARKS = {'vexorian': ' (the mark of the Vexorian map optimizer, "VxOP")', 'w3p': ' (the mark of the w3p protector)',
         'pg2': ' (the mark of the PG2 protector)', 'sprotect': ' (the mark of SProtect)'}

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
        'version_num': 'the format version is %d (it must be 0)' % field_value,
        'bad_header_size': 'the header size is 0x%08X (it must be 0x20)' % (field_value & 0xFFFFFFFF),
        'hash_position': 'the position of the hash table is invalid',
        'block_position': 'the position of the block table is invalid (before the header)',
        'sector_bytes': 'the sector size field has garbage in it',
    }.get(code, code)


def describe(p):
    c = p['code']
    if c == 'ntfs_copy':
        lost = p.get('lost') or 0
        extra = ''
        if lost:
            extra = (' The copy stopped %s short, at the end of the file tables: %s rebuilt from the files themselves.'
                     % (pluralize(lost, 'byte', 'bytes'),
                        pluralize(p.get('tables_rebuilt') or 0, 'table entry was', 'table entries were')))
        return ('Not a protection: this file was copied from a compressed NTFS folder without being decompressed, so '
                'the compressed data of its last part is still inside it. The map is read from the decompressed data.'
                + extra)
    if c == 'fake_header':
        return ('%s before the real one: tools that stop at the first header read garbage.'
                % ('A fake MPQ header sits' if p['n'] == 1 else '%s fake MPQ headers sit' % num(p['n'])))
    if c == 'missing_hm3w':
        return {
            'mpq_at_zero': 'The map header (HM3W) is missing: the archive starts at the very first byte.',
            'user_data': 'The map header (HM3W) was replaced by an MPQ "user data" block.',
        }.get(
            p.get('first_pos'), 'The map header (HM3W) is missing.'
        ) + ' The World Editor and the map list of the game read it.'
    if c == 'read_only':
        return ('The MPQ header was tampered with, so the MPQ Editor opens the map read-only%s: %s.'
                % (MARKS.get(p.get('mark'), ''), '; '.join(_reason(k, v) for k, v in p['reasons'])))
    if c == 'virtual_tables':
        return ('Virtual file tables (the PG2 protector): the file tables do not really exist, and every file name is '
                'repeated several times as decoys.')
    if c == 'sprotect':
        return 'SProtect: %s of the %s file entries are scrambled.' % (num(p['marked']), num(p['used_entries']))
    if c == 'kk_encrypted':
        return ('Encrypted by the KK platform: %s of the real map (script, terrain, objects, models) is stored '
                'encrypted outside the MPQ archive, and only the KK client can decrypt it.' % mb(p.get('outside', 0)))
    if c == 'full_hash_table':
        return 'The file index is 100%% full (%s entries): the MPQ Editor cannot add files.' % num(p['hash_entries'])
    if c == 'unreadable_tables':
        cv = p.get('carver') or {}
        if cv.get('w3i') and cv.get('script'):
            return ('The file tables of this map are scrambled (none of the %s entries leads to a readable file), but '
                    'the files themselves are intact: %s found by their content (%s encrypted). "Remove protection" '
                    'rebuilds the map around them with new file tables.'
                    % (num(p.get('hash_entries', 0)), pluralize(cv.get('file_set') or 0, 'file was', 'files were'),
                       num(cv.get('encrypted_count') or 0)))
        return ('The file tables of this map are scrambled: none of the %s entries points to a file that can be read, '
                'and not even a search by content finds the map info and the script. Nothing can be recovered from it.'
                % num(p.get('hash_entries', 0)))
    if c == 'alias':
        if p['block_list'] == 1:
            return ('1 file has extra fake names pointing to it (%s in all): the MPQ Editor lists every one.'
                    % num(p['maximum']))
        return ('%s files have extra fake names pointing to them (up to %s each): the MPQ Editor lists every one.'
                % (num(p['block_list']), num(p['maximum'])))
    if c == 'fake_entries':
        return '%s to data that does not exist.' % pluralize(p['n'], 'file entry points', 'file entries point')
    if c == 'fake_files':
        return ('At least %s that the game never reads: they make the MPQ Editor slow or freeze.'
                % pluralize(p['n'], 'fake file', 'fake files'))
    if c == 'game_only_reads':
        return ('%s that only the game can read: their stored size or a sector is broken on purpose, so the MPQ '
                "Editor can't open or compact them." % pluralize(p['n'], 'File', 'Files'))
    if c == 'script_decoy':
        return 'A decoy scripts\\war3map.j (unreadable) sits next to the real script.'
    if c == 'sector512':
        return ('The MPQ sectors are 512 bytes (wSectorSize 0): the game loads the map, but the MPQ Editor and every '
                'tool built on StormLib refuse to open it ("bad format").')
    if c == 'locale_decoy':
        name_list = p.get('name_list') or []
        return ('%s hidden behind language entries: the real %s stored only under the game\'s language codes, and a '
                'decoy that nothing can read sits under the neutral entry that the World Editor and MPQ tools open%s.'
                % (pluralize(p['n'], 'file is', 'files are'), 'file is' if p['n'] == 1 else 'files are',
                   ' (%s)' % ', '.join(name_list[:4]) if name_list else ''))
    if c == 'scrambled_ids':
        return ('%s object IDs (units, items, abilities) were scrambled into unreadable characters, and the script '
                'reaches them through %s disguised sums.%s'
                % (num(p['n']), num(p.get('sums', 0)),
                   '' if p.get('fixable') else ' (This is a Lua map: they cannot be restored.)'))
    if c == 'invalid_doodad':
        return ('%s an object ID that does not exist in the game data nor in the map\'s own object data (%s%s). '
                'The game draws nothing for them and the World Editor reports "Invalid object ID" and crashes while '
                'opening the map. They are removed in button 3.'
                % (pluralize(p.get('n', 0), 'doodad placed in the map uses', 'doodads placed in the map use'),
                   ', '.join(p.get('examples') or []) or '?', '...' if len(p.get('ids') or []) > 5 else ''))
    if c == 'inflated_counts':
        label, singular, plural, where = COUNT.get(p['file_name'], ('file', 'record', 'records', p['file_name']))
        if p.get('reason') == 'odd_version':
            return ('The %s (%s) is in a format no real map uses (%s): the World Editor hangs or shows no %s. '
                    'It is rebuilt from the script.' % (label, p['file_name'], p.get('detail') or '?', plural))
        if p.get('declared') is None or p.get('reason') == 'empty':
            return ('The %s (%s) is empty or truncated: the map has no usable %s in it, and the World Editor '
                    'cannot read it.' % (label, p['file_name'], plural))
        d = 'The %s (%s) claims %s %s' % (label, p['file_name'], num(p['declared']), plural)
        if p.get('mark'):
            d += ' (the old "%s" count)' % p['mark']
        if p.get('read_count'):
            d += ', and only %s read cleanly' % pluralize(p['read_count'], singular, plural)
        d += ': the World Editor hangs on "%s".' % where
        if p.get('game'):
            d += ' The game reads this file too, so it is not repaired here.'
        return d
    return c


def incomplete(inc):
    if not inc:
        return 'it ends before its file tables'
    return ('its MPQ header says the file tables end at byte %s, but the file has %s bytes -- %s bytes are missing'
            % (num(inc.get('end_of_tables', 0)), num(inc.get('byte_size', 0)), num(inc.get('missing_items', 0))))


def name_of(d):
    return d.get('fname') or os.path.basename(d['file_name'])


def diagnosis_text(d):
    out = [('heading', 'Diagnosis: %s' % os.path.basename(d['file_name'])),
           ('info', 'Map: %s  (%s)' % (name_of(d), mb(d['byte_size'])))]
    if d['fixable'] == 'not_a_map':
        return out + [('invalid', 'This file is not a Warcraft III map: there is no MPQ archive inside it.')]
    if d['fixable'] == 'incomplete':
        return out + [
            (
                'invalid',
                'This map file is incomplete: %s. That is a cut download (or a copy that was cut short), '
                'not a protection, and nothing in it can be fixed: get a complete copy of the map.'
                % incomplete(d.get('incomplete')),
            )
        ]
    if d['fixable'] == 'cannot_read':
        return out + [('invalid', 'The MPQ archive could not be read (%s).' % d.get('err'))]
    out.append(('', ''))
    if not d['protections']:
        out.append(('ok', 'No MPQ protection found.'))
    else:
        out.append(('heading2', 'Protection found:'))
        for p in d['protections']:
            out.append(('warning', '  - ' + describe(p)))
        out.append(('', ''))
        if d['fixable'] == 'impossible':
            out.append(
                (
                    'invalid',
                    "This map can't be unprotected: the real map is not inside this file. Ask for a copy of the "
                    'map without the KK encryption.',
                )
            )
        else:
            out.append(('ok', 'Devo\'s Map Doctor can remove it: click "Remove protection".'))
    lf = d.get('listfile')
    if lf:
        if lf['status'] == 'ok':
            out.append(('info', 'File list: complete (%s).' % pluralize(lf['file_set'], 'file', 'files')))
        elif lf['status'] == 'absent':
            out.append(
                ('info', 'File list: missing (%s no name).' % pluralize(lf['file_set'], 'file has', 'files have'))
            )
        else:
            out.append(('info', 'File list: %s of %s files are named.' % (num(lf['named']), num(lf['file_set']))))
    out.append(('', ''))
    ed = d['editor']
    status = ed.get('status')
    map_list = (d.get('campaign_info') or {}).get('map_list') or []
    if d.get('kind') == 'campaign_info':
        ready_count = sum(1 for m in map_list if m.get('editor') == 'ready')
        out.append(('info', 'Campaign: %s inside (%s already open%s in the World Editor).'
                    % (pluralize(len(map_list), 'map', 'maps'), num(ready_count), 's' if ready_count == 1 else '')))
    if status == 'ready':
        out.append(('ok', 'World Editor: the %s already has everything the editor needs.'
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
        out.append(('ok', 'Click "Make it open in World Editor": each map above is prepared inside the campaign.'))
    elif status == 'needs_work':
        gaps = []
        if set(p['code'] for p in d['protections']) & set(D.EDITOR_BLOCKERS):
            gaps.append('the protection has to go first')
        if ed.get('w3i') == 'truncated':
            gaps.append('the end of the map info file (war3map.w3i) was cut off')
        if ed.get('missing_items'):
            gaps.append('these editor files are missing: %s' % ', '.join(ed['missing_items']))
        if ed.get('trigger_list'):
            gaps.append('the map\'s triggers use functions the World Editor 3.0 does not have (made with YDWE or '
                        'another extended editor), so the editor cannot read them')
        if ed.get('duplicate_textures'):
            copies = sum(len(g) - 1 for g in ed['duplicate_textures'])
            gaps.append('%s an exact copy of another one under a different name (%s), and the World Editor 3.0 '
                        'crashes while it finishes opening a map that loads them'
                        % (pluralize(copies, 'imported texture is', 'imported textures are'),
                           ', '.join(os.path.basename(g[-1].replace('\\', '/')) for g in ed['duplicate_textures'][:3]) +
                           ('...' if len(ed['duplicate_textures']) > 3 else '')))
        out.append(('warning', 'World Editor: the map will not open yet (%s).' % '; '.join(gaps or ['see above'])))
        out.append(('ok', 'Click "Make it open in World Editor".'))
    else:
        out.append(('invalid', 'World Editor: ' + editor_reason(status)))
    return out


def editor_reason(status):
    return {
        'script_kkwe': 'the script is compiled by KKWE (kkmap.jc), which the World Editor cannot read.',
        'script_none': 'the map has no script.',
        'script_cut_off': 'the map script is cut off before its end (the map file is incomplete), so there is nothing '
        'to put in the trigger editor.',
        'script_kk_encrypted': 'the real map is encrypted outside this file (KK platform).',
        'impossible': 'the real map is encrypted outside this file (KK platform).',
        'unreadable': 'the file tables of this map are scrambled: nothing in it can be read (no file name resolves), so '
        'there is nothing to fix here.',
        'w3i_unreadable': 'the map info file (war3map.w3i) is in a format this tool cannot read.',
        'w3i_missing': 'the map info file (war3map.w3i) is missing.',
    }.get(status, status)


def _fixes_done(details, steps, before):
    out = []
    if steps.get('ntfs'):
        nt = steps['ntfs']
        tab = nt.get('tables') or {}
        out.append(
            'Decompressed the NTFS data left inside the file%s.'
            % (
                '; the file tables cut by the copy were rebuilt (%s)'
                % pluralize(tab.get('rebuilt') or 0, 'entry', 'entries')
                if tab.get('rebuilt')
                else ''
            )
        )
    if steps.get('carver'):
        cv = steps['carver']
        name_list = cv.get('name_list') or {}
        out.append(
            'Rebuilt the map from its files, found by their content: %s (%s named by content, %s by their '
            'encryption key, %s from the map\'s own lists%s).'
            % (
                pluralize(cv.get('file_set') or 0, 'file', 'files'),
                num(name_list.get('content', 0)),
                num(name_list.get('hash_key', 0)),
                num(name_list.get('listing', 0) + name_list.get('imp_order', 0)),
                '; %s kept with a placeholder name under war3mapImported\\carved' % num(name_list['unnamed'])
                if name_list.get('unnamed')
                else '',
            )
        )
    if steps.get('sprotect'):
        out.append('Undid the SProtect scrambling of the file entries.')
    if details.get('new_tables'):
        out.append('Rebuilt the file tables with the %s (the decoys are gone).'
                   % pluralize(details['new_tables'], 'real file', 'real files'))
    if steps.get('sector_bytes'):
        out.append('Rewrote the archive with normal 4 KB sectors: the MPQ Editor can open it now.')
    if details.get('locale_decoys'):
        out.append('Brought back %s hidden behind language entries: every program now reads the real one.'
                   % pluralize(details['locale_decoys'], 'file', 'files'))
    if details.get('fake_zeroed'):
        out.append('Disabled the fake MPQ header.' if details['fake_zeroed'] == 1 else
                   'Disabled %s fake MPQ headers.' % num(details['fake_zeroed']))
    fields = [c[0] for c in details.get('fields') or []]
    if 'dwHeaderSize' in fields or 'wFormatVersion' in fields or 'wSectorSize' in fields or \
            details.get('block_table_moved') or details.get('hash_table_moved'):
        out.append('Fixed the MPQ header: the MPQ Editor opens the map in edit mode now.')
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
        out.append('Rewrote %s that only the game could read, so the MPQ Editor opens and compacts them.'
                   % pluralize(len(listing['rewritten']), 'file', 'files'))
    if steps.get('ids'):
        out.append('Replaced %s with clean ones (the script was updated to match).'
                   % pluralize(steps['ids'], 'scrambled object ID', 'scrambled object IDs'))
    return out or ['Fixed the MPQ archive.']


def _common_failures(r, verb):
    e = r['status']
    if e == 'not_a_map':
        return [('invalid', 'This file is not a Warcraft III map: there is no MPQ archive inside it.')]
    if e == 'cannot_read':
        return [('invalid', 'The MPQ archive could not be read (%s).' % (r['before'] or {}).get('err'))]
    if e == 'impossible':
        return [
            (
                'invalid',
                "This map can't be %s: the real map (script, terrain, objects, models) is encrypted outside "
                'the MPQ archive by the KK platform. Ask for a copy of the map without the KK encryption.' % verb,
            )
        ]
    if e == 'incomplete':
        return [('invalid', "This map can't be %s: the file is incomplete (%s). Get a complete copy of the map."
                 % (verb, incomplete((r.get('before') or {}).get('incomplete'))))]
    if e == 'unreadable':
        return [('invalid', "This map can't be %s: %s" % (verb, editor_reason('unreadable')))]
    if e == 'failed':
        out = [('invalid', 'Something went wrong, so nothing was saved. Your original map was not changed.')]
        err = r.get('err') or ''
        content = r.get('content') or {}
        if content.get('different') or content.get('missing_items'):
            out.append(
                (
                    'warning',
                    'The final check caught a problem: after the fix, a file no longer read back identical '
                    'to the original. This map uses a trick this version does not handle yet. Please post '
                    'the diagnosis text so it can be added.',
                )
            )
        if 'PermissionError' in err:
            out.append(
                (
                    'warning',
                    'The new copy could not be written next to the map. Copy the map to a folder you can '
                    'write to (your Desktop, for example) and try again.',
                )
            )
        return out + [('info', 'Details: %s' % r.get('err'))]
    return None


def unprotection_text(r):
    d = r['before']
    out = [('heading', 'Remove protection: %s' % os.path.basename(d['file_name']))]
    failure = _common_failures(r, 'unprotected')
    if failure:
        return out + failure
    if r['status'] == 'nothing_to_do':
        if r.get('for_button3'):
            return out + [
                ('ok', 'Nothing to remove in the MPQ archive. No file was written.'),
                ('info', 'The World Editor problems found above are fixed by "Make it open in World Editor".'),
            ]
        return out + [('ok', 'No protection found: nothing to remove. No file was written.')]
    out.append(('ok', 'Protection removed.' if r['status'] == 'done' else
                'Protection removed, with some leftovers (see below).'))
    out.append(('file_path', 'Saved as: %s' % r['output']))
    out.append(('', ''))
    for line in _fixes_done(r['steps'].get('repair') or {}, r['steps'], d):
        out.append(('info', '  - ' + line))
    c = r.get('content') or {}
    if c.get('identical'):
        out.append(
            (
                'info',
                '  - Checked: %s identical to the original%s.'
                % (
                    pluralize(c['identical'], 'file reads back', 'files read back'),
                    ' (the object data and the script changed on purpose: the new IDs)'
                    if r['steps'].get('ids')
                    else '',
                ),
            )
        )
    after_diag = (r.get('after_diag') or {}).get('protections') or []
    button3 = [p for p in after_diag if p['code'] in D.BUTTON3_ONLY]
    unresolved = [p for p in after_diag if p['code'] not in D.BUTTON3_ONLY]
    if button3:
        out.append(('', ''))
        out.append(('info', 'Left for "Make it open in World Editor" (this button keeps every map file identical):'))
        for p in button3:
            out.append(('info', '  - ' + describe(p)))
    if unresolved:
        out.append(('', ''))
        out.append(('warning', 'Still present (these need file names that the map does not reveal):'))
        for p in unresolved:
            out.append(('warning', '  - ' + describe(p)))
        if any(p['code'] == 'alias' for p in unresolved):
            out.append(
                (
                    'info',
                    '  These names were kept on purpose: without the real file name there is no way to tell '
                    'which one the game uses, and removing the wrong one would break the map.',
                )
            )
    return out


def editor_text(r):
    d = r['before']
    out = [('heading', 'Make it open in World Editor: %s' % os.path.basename(d['file_name']))]
    failure = _common_failures(r, 'prepared for the World Editor')
    if failure:
        return out + failure
    if r['status'] == 'nothing_to_do':
        return out + [('ok', 'The map already opens in the World Editor: nothing to do. No file was written.')]
    if r['status'] in ('script_lua', 'script_kkwe', 'script_none', 'script_cut_off', 'w3i_unreadable', 'w3i_missing',
                       'unreadable'):
        return out + [('invalid', 'Not possible: ' + editor_reason(r['status']))]
    out.append(('ok', 'Ready for the World Editor.' if r['status'] == 'done' else
                'Prepared for the World Editor, with some leftovers (see below).'))
    out.append(('file_path', 'Saved as: %s' % r['output']))
    out.append(('', ''))
    if (r.get('editor') or {}).get('campaign_info'):
        for m in r['editor'].get('map_list') or []:
            out.append(
                (
                    'info' if m['status'] in ('done', 'partial') else 'warning',
                    '  - %s: %s'
                    % (
                        m['fname'],
                        {'done': 'prepared for the World Editor', 'partial': 'prepared, with some leftovers'}.get(
                            m['status'], 'not possible (%s)' % editor_reason(m['status'])
                        ),
                    ),
                )
            )
        return out
    unprot = r.get('unprotection')
    if unprot:
        out.append(('info', '  - First removed the protection:'))
        for line in _fixes_done(unprot['steps'].get('repair') or {}, unprot['steps'], d):
            out.append(('info', '      ' + line))
    details = r.get('editor') or {}
    if details.get('regenerated_triggers'):
        out.append(('info', '  - The map\'s triggers used functions the World Editor 3.0 does not have (YDWE or '
                            'another extended editor): they were replaced by the map script in the custom script, so '
                            'the editor opens the map and saving keeps the same code.'))
    if details.get('w3i_tail'):
        out.append(('info', '  - Restored the cut-off end of the map info file (war3map.w3i).'))
    mentioned = set()
    for x in details.get('count') or []:
        label, singular, plural, _where = COUNT.get(x['file_name'], ('file', 'record', 'records', ''))
        mentioned.add(x['file_name'])
        where = x.get('where') or ''
        if x.get('pair'):
            out.append(('info', '  - Rebuilt the trigger files (war3map.wtg and war3map.wct) from the map script: the '
                                'counter the editor was reading was broken.'))
        elif x.get('from_script'):
            where = x.get('where') or ''
            before = x.get('in_file')
            if x.get('reason') == 'odd_version':
                out.append(('info', '  - Rebuilt the %s (%s) from the %s in the map script: it was in a format no '
                                    'real map uses (%s), which is what made the editor hang on it. The %s are there '
                                    'now.' % (label, x['file_name'], where, x.get('detail') or '?', plural)))
            elif x.get('reason') in ('does_not_fit', 'short_read'):
                out.append(('info', '  - Rebuilt the %s (%s) from the %s in the map script: it claimed %s. The editor '
                                    'shows the %s now.'
                            % (label, x['file_name'], where, num(x['declared']) if x.get('declared') is not None
                               else 'none', plural)))
            elif before is None:
                out.append(('info', '  - Added the %s the map script creates (%s): the editor shows them now.'
                            % (plural, where)))
            else:
                out.append(('info', '  - Placed the %s the map script creates (%s): the file only had %s. The World '
                                    'Editor shows them now.'
                            % (pluralize(x['new'], singular, plural), where,
                               pluralize(before, singular, plural) if before else 'none')))
            if x.get('removed_risky'):
                n = sum(x['removed_risky'].values())
                out.append(('info', '  - Left out %s of those, whose model is a file inside this map that no doodad '
                                    'uses (%s): the World Editor 3.0 crashes while it reads a map file right after '
                                    'opening the map a second time, and those are the units that make it read one '
                                    'that late. The map itself does not change: the game creates every unit from '
                                    'the script.'
                            % (pluralize(n, 'unit', 'units'),
                               ', '.join('%s x%d' % (k, v) for k, v in sorted(x['removed_risky'].items())[:4]) +
                               ('...' if len(x['removed_risky']) > 4 else ''))))
        elif x.get('declared') is None or x.get('reason') == 'empty':
            out.append(('info', '  - Replaced the empty/truncated %s (%s) with an empty one the editor can read.'
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
        out.append(('info', '  - Added the editor-only files: %s.' % ', '.join(others)))
    if details.get('no_slot'):
        outside = list(details['no_slot'])
        essential = [n for n in outside if n in ('war3map.wtg', 'war3map.wct', 'war3map.imp')]
        out.append(
            ('warning', '  - The file index of this map is 100%% full: there was no room for %s.' % ', '.join(outside))
        )
        if essential:
            out.append(('invalid', '      %s is needed for the editor to open (and to keep the imported files when you '
                                   'save): send me this map.' % ', '.join(essential)))
        else:
            out.append(('info', '      The editor creates these files by itself when you save, so the map opens and '
                                'saves without them.'))
    lua = bool(details.get('lua'))
    if generated and lua:
        out.append(('info', '  - Placed the whole map script (Lua) in the custom script of the trigger editor, inside '
                            'do ... end. When you save, the editor adds its own main and config after it; the last '
                            'line of the custom script keeps the map\'s own ones running.'))
    elif generated:
        out.append(('info', '  - Placed the whole map script in the custom script of the trigger editor (//! inject '
                            'main / config): saving with JassHelper enabled builds the same script again. The '
                            'functions the editor also creates (InitGlobals, CreateAllUnits, the unit creation of '
                            'each player...) are named "devo_..." there: two functions with the same name do not '
                            'compile, and the editor refused to open the script with "Function redeclared".'))
    if 'war3map.imp' in (details.get('new_ones') or []):
        out.append(('info', '  - Listed %s, so the editor keeps them when you save.'
                    % pluralize(details.get('imported', 0), 'imported file', 'imported files')))
    out.append(('', ''))
    out.append(('info', 'Good to know:'))
    if lua:
        out.append(('info', '  - Lua maps are new since version 1.1: after saving from the editor, test the map, and '
                            'please report anything that breaks.'))
    else:
        out.append(('info', '  - Keep JassHelper enabled (the default) when you save the map.'))
    if generated:
        placed_files = set(x['file_name'] for x in details.get('count') or [] if x.get('from_script'))
        if placed_files:
            out.append(('info', '  - Units, regions and sounds that the script creates used to stay out of the editor: '
                                'the ones listed above are there now. The items and abilities of a unit, and the '
                                'sounds, still only exist in the game.'))
        else:
            out.append(('info', '  - Units, regions and sounds that the script creates do not show in the editor, but '
                                'the game still creates them.'))
    if details.get('doodads_outside'):
        out.append(('info', '  - Removed %s whose object ID does not exist in the game data (%s): the game '
                            'draws nothing for them and they made the World Editor crash while opening the map.'
                    % (pluralize(details['doodads_outside'], 'doodad', 'doodads'),
                       ', '.join('%s x%d' % (x['id'], x['n']) for x in (details.get('doodads') or [])[:4]))))
    clusters = details.get('duplicate_textures') or []
    changed_textures = [m for g in clusters for m in g['modified']]
    if changed_textures:
        seen = []
        for m in changed_textures:
            b = os.path.basename(m.replace('\\', '/'))
            if b not in seen:
                seen.append(b)
        out.append(('info', '  - Rewrote %s in %s (%s), each one with a few zero bytes at the end: the World Editor '
                            '3.0 crashed while it finished opening a map that loads two identical textures, and it '
                            'reads only one of them. Neither the game nor the editor reads the extra bytes: the image '
                            'is exactly the same.'
                    % (pluralize(len(changed_textures), 'imported texture', 'imported textures'),
                       pluralize(len(clusters), 'group', 'groups'),
                       ', '.join(seen[:4]) + ('...' if len(seen) > 4 else ''))))
    unresolved = (r.get('after_diag') or {}).get('protections') or []
    if unresolved:
        out.append(('warning', 'Still present:'))
        for p in unresolved:
            out.append(('warning', '  - ' + describe(p)))
    return out


def execute(action_code, map_path, progress=None, safe_units=True):
    if action_code == 'diag':
        return diagnosis_text(D.diagnose(map_path, progress))
    if action_code == 'unprotect':
        return unprotection_text(D.unprotect(map_path, D.free_output(map_path, '_unprotected'), progress))
    return editor_text(D.prepare_for_editor(map_path, D.free_output(map_path, '_editor'), progress,
                                            safe_units=safe_units))


def window(initial_map_path=None):
    import tkinter as tk
    from tkinter import filedialog, font, ttk
    from tkinter.scrolledtext import ScrolledText

    root = tk.Tk()
    root.title(APP)
    root.minsize(760, 540)
    root.geometry('880x620')
    try:
        root.iconbitmap(default=icon_ico())
    except Exception:
        pass
    work_queue = queue.Queue()
    status = {'busy': False}
    map_path_var = tk.StringVar(value=initial_map_path or '')
    status_var = tk.StringVar(value='Select a Warcraft III map or campaign (.w3x / .w3m / .w3n) to start.')

    base = font.nametofont('TkDefaultFont')
    base.configure(size=10)
    bold_font = base.copy()
    bold_font.configure(weight='bold')
    heading_font = base.copy()
    heading_font.configure(size=13, weight='bold')

    header = ttk.Frame(root, padding=(14, 12, 14, 4))
    header.pack(fill='x')
    ttk.Label(header, text=APP, font=heading_font).pack(side='left')
    ttk.Label(header, text='  diagnose and remove Warcraft III map protections', foreground='#666').pack(side='left')

    ln = ttk.Frame(root, padding=(14, 6, 14, 6))
    ln.pack(fill='x')
    ttk.Label(ln, text='Map:').pack(side='left')
    ent = ttk.Entry(ln, textvariable=map_path_var, state='readonly')
    ent.pack(side='left', fill='x', expand=True, padx=(6, 6))
    b_choose = ttk.Button(ln, text='Select map...', command=lambda: choose())
    b_choose.pack(side='left')

    buttons = ttk.Frame(root, padding=(14, 4, 14, 8))
    buttons.pack(fill='x')
    tag = ttk.Style()
    tag.configure('Big.TButton', font=bold_font, padding=(10, 10))
    b1 = ttk.Button(buttons, text='1   Diagnose protection', style='Big.TButton', command=lambda: run_action('diag'))
    b2 = ttk.Button(buttons, text='2   Remove protection', style='Big.TButton', command=lambda: run_action('unprotect'))
    b3 = ttk.Button(
        buttons, text='3   Make it open in World Editor', style='Big.TButton', command=lambda: run_action('editor')
    )
    for i, b in enumerate((b1, b2, b3)):
        b.grid(row=0, column=i, sticky='ew', padx=(0 if i == 0 else 8, 0))
        buttons.columnconfigure(i, weight=1)

    log = ScrolledText(root, wrap='word', height=20, relief='flat', borderwidth=1, padx=12, pady=10,
                       font=base, background='#fbfbfb')
    log.pack(fill='both', expand=True, padx=14)
    log.tag_configure('heading', font=heading_font, spacing1=6, spacing3=4)
    log.tag_configure('heading2', font=bold_font)
    log.tag_configure('ok', foreground='#1b7f3a', font=bold_font)
    log.tag_configure('warning', foreground='#a35a00')
    log.tag_configure('invalid', foreground='#b3261e', font=bold_font)
    log.tag_configure('info', foreground='#222')
    log.tag_configure('file_path', foreground='#1a4fa0')
    log.configure(state='disabled')

    footer = ttk.Frame(root, padding=(14, 6, 14, 10))
    footer.pack(fill='x')
    bar = ttk.Progressbar(footer, mode='determinate', length=160, value=0)
    bar.pack(side='left')
    ttk.Label(footer, textvariable=status_var).pack(side='left', padx=(10, 0))
    ttk.Label(footer, text='v%s  -  your original map is never changed' % VERSION, foreground='#888').pack(side='right')

    def write(line_list):
        log.configure(state='normal')
        if log.index('end-1c') != '1.0':
            log.insert('end', '\n')
        for st, txt in line_list:
            log.insert('end', txt + '\n', st or ())
        log.configure(state='disabled')
        log.see('end')

    def enable(yes):
        for b in (b1, b2, b3, b_choose):
            b.configure(state='normal' if yes else 'disabled')

    def choose():
        begin = os.path.dirname(map_path_var.get()) if map_path_var.get() else None
        p = filedialog.askopenfilename(
            title='Select a Warcraft III map',
            initialdir=begin,
            filetypes=[('Warcraft III maps and campaigns', '*.w3x *.w3m *.w3n'), ('All files', '*.*')],
        )
        if p:
            map_path_var.set(os.path.normpath(p))
            status_var.set('Ready. Choose an action.')

    def run_action(action_code):
        map_path = map_path_var.get()
        if status['busy']:
            return
        if not map_path or not os.path.isfile(map_path):
            choose()
            map_path = map_path_var.get()
            if not map_path or not os.path.isfile(map_path):
                return
        status['busy'] = True
        enable(False)
        bar.configure(mode='indeterminate')
        bar.start(12)
        status_var.set('Working...')

        def work():
            try:
                line_list = execute(action_code, map_path, progress=lambda c: work_queue.put(('stage', c)))
            except Exception as e:
                line_list = [('invalid', 'Unexpected error: %s' % e),
                             ('info', 'Your original map was not changed.'),
                             ('info', traceback.format_exc(limit=3))]
            work_queue.put(('end_pos', line_list))
        threading.Thread(target=work, daemon=True).start()

    def poll():
        try:
            while True:
                kind, datum = work_queue.get_nowait()
                if kind == 'stage':
                    status_var.set(STAGES.get(datum, 'Working...'))
                elif kind == 'version_num':
                    offer(datum)
                elif kind == 'offer_index':
                    offer_index(datum)
                elif kind == 'message':
                    status_var.set(datum)
                else:
                    write(datum)
                    bar.stop()
                    bar.configure(mode='determinate', value=0)
                    status['busy'] = False
                    enable(True)
                    status_var.set('Done.')
        except queue.Empty:
            pass
        root.after(120, poll)

    def on_close():
        if status['busy']:
            from tkinter import messagebox
            if not messagebox.askyesno(APP, 'A task is still running. Close anyway? (Your original map is safe.)'):
                return
        root.destroy()

    root.protocol('WM_DELETE_WINDOW', on_close)
    write([('heading', 'Welcome'),
           ('info', '1. Select a Warcraft III map.'),
           ('info', '2. "Diagnose protection" tells you what was done to it.'),
           ('info', '3. "Remove protection" saves an unprotected copy next to it (fake files removed too), which the '
                    'MPQ Editor opens in edit mode.'),
           ('info', '4. "Make it open in World Editor" saves a copy the World Editor can open.'),
           ('info', 'Your original map is never changed.')])
    if initial_map_path:
        status_var.set('Ready. Choose an action.')

    def new_version(release):
        work_queue.put(('version_num', release))

    def offer(release):
        from tkinter import messagebox
        body_text = 'Version %s of %s is available (you have %s).\n\nDownload and install it now?' % (
            release['version'].lstrip('vV'), APP, VERSION)
        if not messagebox.askyesno(APP, body_text):
            return
        status_var.set('Downloading the new version...')
        root.update_idletasks()
        try:
            if updater.install(release):
                root.destroy()
        except Exception as e:
            messagebox.showerror(APP, 'The update failed: %s\n\nThe release page will open instead.' % e)
            updater.open_page(release)
        status_var.set('Ready.')

    def index_missing(release):
        work_queue.put(('offer_index', release))

    def offer_index(release):
        from tkinter import messagebox

        body_text = (
            'The file name index (names.npz, %s) is %s. With it, the Doctor names more of the files it finds in '
            'maps whose file tables are damaged.\n\nDownload it now?'
            % (mb(release.get('index_size') or 0), 'out of date' if os.path.isfile(updater.index_path()) else 'missing')
        )
        if not messagebox.askyesno(APP, body_text):
            return
        status_var.set('Downloading the file name index...')

        def fetch():
            try:
                updater.download_index(release)
                work_queue.put(('message', 'The file name index is ready.'))
            except Exception as e:
                work_queue.put(('message', 'The file name index could not be downloaded: %s' % e))
        threading.Thread(target=fetch, daemon=True).start()

    if updater.enabled(sys.argv):
        updater.check(VERSION, new_version, index_missing)
    poll()
    root.mainloop()


def icon_ico():
    base = getattr(sys, '_MEIPASS', os.path.join(HERE, 'assets'))
    p = os.path.join(base, 'devos_map_doctor.ico')
    if not os.path.isfile(p):
        raise OSError('no icon')
    return p


def _no_console():
    for fname in ('stdout', 'stderr'):
        if getattr(sys, fname) is None:
            setattr(sys, fname, open(os.devnull, 'w', encoding='utf-8'))


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    _no_console()
    updater.cleanup()
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
            return 2
        map_path = args[0]
        action_codes = (
            ['diag'] + (['unprotect'] if '--unprotect' in argv else []) + (['editor'] if '--editor' in argv else [])
        )
        safe_units = '--units=all' not in argv
        for action_code in action_codes:
            for st, txt in execute(
                action_code,
                map_path,
                progress=lambda c: print('   [%s]' % STAGES.get(c, c), file=out),
                safe_units=safe_units,
            ):
                print(('## ' if st == 'heading' else '') + txt, file=out)
            print(file=out)
        if log:
            out.close()
        return 0
    args = [a for a in argv if not a.startswith('--')]
    window(os.path.normpath(args[0]) if args and os.path.isfile(args[0]) else None)
    return 0


if __name__ == '__main__':
    sys.exit(main())
