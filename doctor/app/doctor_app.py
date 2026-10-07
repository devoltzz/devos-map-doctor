# The window: the HTML page in WebView2, and the worker process that runs each job.
import base64
import hashlib
import json
import os
import pickle
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import urllib.parse
import webbrowser


HERE = os.path.dirname(os.path.abspath(__file__))
APP = "Devo's Map Doctor"
MAP_TYPES = ('Warcraft III maps and campaigns (*.w3x;*.w3m;*.w3n)', 'All files (*.*)')
NO_WINDOW = 0x08000000


def ui_folder():
    bases = [getattr(sys, '_MEIPASS', None), os.path.dirname(os.path.abspath(sys.argv[0])), HERE]
    for base in bases:
        for name in ('ui', 'doctor_ui'):
            if base and os.path.isfile(os.path.join(base, name, 'index.html')):
                return os.path.join(base, name)
    raise OSError('the interface files (ui/index.html) are missing')


def settings_path():
    if sys.platform.startswith('linux'):
        base = os.environ.get('XDG_CONFIG_HOME') or os.path.join(os.path.expanduser('~'), '.config')
    else:
        base = os.environ.get('APPDATA') or os.path.expanduser('~')
    return os.path.join(base, 'DevosMapDoctor', 'settings.json')


def load_settings():
    try:
        with open(settings_path(), encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_settings(data):
    p = settings_path()
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p + '.new', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1)
    os.replace(p + '.new', p)


def worker_command():
    if getattr(sys, 'frozen', False):
        return [sys.executable, '--worker']
    return [sys.executable, os.path.abspath(sys.argv[0]), '--worker']


def _cache_file(path):
    st = os.stat(path)
    key = hashlib.sha1(('%s|%d|%d' % (os.path.abspath(path).lower(), st.st_size, int(st.st_mtime))).encode())
    key = key.hexdigest()
    folder = os.environ.get('DOCTOR_CACHE') or os.path.join(tempfile.gettempdir(), 'devos_map_doctor_ui')
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, 'diag_%s.pickle' % key)


def cached_diagnosis(D, path, progress):
    p = _cache_file(path)
    try:
        with open(p, 'rb') as f:
            return pickle.load(f)
    except (OSError, pickle.PickleError, EOFError, AttributeError, ImportError):
        pass
    d = D.diagnose(path, progress)
    try:
        with open(p + '.new', 'wb') as f:
            pickle.dump(d, f)
        os.replace(p + '.new', p)
    except (OSError, pickle.PickleError, TypeError):
        pass
    return d


def _jsonable(x):
    if isinstance(x, dict):
        return dict((str(k), _jsonable(v)) for k, v in x.items())
    if isinstance(x, (list, tuple, set, frozenset)):
        return [_jsonable(v) for v in x]
    if isinstance(x, bytes):
        return base64.b64encode(x).decode('ascii')
    if isinstance(x, (str, int, float, bool)) or x is None:
        return x
    return str(x)


STYLE = {'heading': 'title', 'heading2': 'subtitle', 'ok': 'good', 'warning': 'warn', 'invalid': 'bad', 'info': 'info',
         'file_path': 'path'}
PAGE_STYLES = frozenset(STYLE.values())
OUTCOME = {'done': 'ok', 'partial': 'partial', 'nothing_to_do': 'nothing', 'nothing_selected': 'nothing'}
VERDICT = {'yes': 'v-yes', 'probably': 'v-probably', 'node': 'v-no', 'unknown': 'v-unknown'}
SCRIPT_LABEL = {'jass': 'JASS', 'lua': 'Lua', 'kkwe': 'KK compiled (KKWE)', 'j2b': 'KK compiled and encrypted (j2b)',
                'kk_encrypted': 'KK encrypted outside the map', 'none': 'none'}
STEP_TEXT = {
    'mpq': ('Remove the MPQ protection', 'Header, file tables and the read-only tricks.'),
    'fake_list': ('Remove the fake files', 'Junk the protector added.'),
    'listing': ('Write a real file list', 'A (listfile) with every real name.'),
    'ids': ('Restore the object ids', 'The ids scrambled in the map data.'),
    'dados:file_column': ('Move the models out of the file column', 'Crashes 3.0 on the first unit.'),
    'dados:levels': ('Add ability levels 5 and 6', 'Copies of level 4.'),
    'dados:buttonpos': ('Complete half-written button positions', 'Like Buttonpos=,2.'),
    'dados:fdf_comment': ('Remove the stray */ in frame files', '3.0 closes on the loading screen.'),
    'dados:id_lists': ('Remove the |n from ability lists', '3.0 reads a nonexistent ability.'),
    'dados:quoted_numbers': ('Turn numbers stored as text back into numbers', 'Not a crash, cleaned up as well.'),
    'unprotection': ('Remove the protection first', 'The steps of "Fix map" the editor needs.'),
    'script_restore': ('Turn the compiled script back into JASS', 'The editor cannot read the KK bytecode.'),
    'editor_only_files': ('Add the files only the editor reads',
                          'Map info, triggers, import list and JassHelper.'),
    'inflated_counts': ('Fix the counters that hang the editor', 'Huge counts in the editor files.'),
    'invalid_doodads': ('Remove the doodads whose id does not exist', 'The editor 3.0 crashes on them.'),
    'gui_triggers': ('Restore the triggers as GUI', 'Off: the whole script goes to the custom script.'),
    'script_objects': ('Place what the script creates',
                       'Units, items, regions, cameras and sounds the script creates.'),
    'safe_units': ('Leave out the units that crash the editor', 'Off: every unit is placed, also the bad ones.'),
}
REASON_TEXT = {
    'editor_requires': 'Required: the editor cannot open the map without it.',
    'editor_crashes': 'Required: the editor 3.0 crashes or hangs without it.',
    'editor_is_ready': 'Not needed: the map already opens.',
    'no_protection': 'Not needed: no MPQ protection.',
    'no_fakes': 'Not needed: no fake files.',
    'no_ids': 'Not needed: no scrambled ids.',
    'not_compiled': 'Not needed: the script is not compiled.',
    'not_needed': 'Not needed for this map.',
    'tables_ok': 'Not needed: the tables are fine.',
}


def page_lines(lines):
    return [[STYLE.get(style) or (style if style in PAGE_STYLES else 'info'), text] for style, text in lines]


def page_steps(D, d):
    out = []
    for x in D.steps(d):
        label, detail = STEP_TEXT.get(x['hash_key'], (x['hash_key'], ''))
        why = REASON_TEXT.get(x['reason']) if x['reason'] else None
        out.append(
            {
                'action': x['action_code'],
                'key': x['hash_key'],
                'label': label,
                'detail': detail,
                'on': x['default_on'],
                'locked': x['locked'],
                'applies': x['applies'],
                'why': why,
                'group': 'data' if x['hash_key'].startswith('dados:') else 'main',
            }
        )
    return out


NOTICE_CODES = ('ntfs_copy',)


def page_summary(D, d):
    codes = sorted(set(p['code'] for p in d.get('protections') or []))
    data = [c for c in codes if c in D.DATA_ONLY]
    return {'codes': codes, 'data_problems': len(data), 'slk': list(d.get('slk') or []),
            'protected': any(c not in D.BUTTON3_ONLY and c not in D.DATA_ONLY and c not in NOTICE_CODES
                             for c in codes),
            'editor_ready': (d.get('editor') or {}).get('status') == 'ready', 'script': d.get('script'),
            'script_label': SCRIPT_LABEL.get(d.get('script')) or (d.get('script') and 'unknown'),
            'can_fix': d.get('fixable') == 'yes', 'campaign': bool(d.get('campaign_info'))}


def page_changes(r, kind, extras=None):
    files, notes = [], []
    if kind == 'fix':
        steps = r.get('steps') or {}
        rep = steps.get('repair') or {}
        if 'repair' in steps or steps.get('sprotect') or steps.get('sector_bytes'):
            files.append({'file': 'MPQ header and file tables', 'how': 'rewritten', 'why': 'the protection removed'})
        fakes = (rep.get('junk_blocks') or 0) + (rep.get('deleted_aliases') or 0)
        if fakes:
            files.append({'file': '%d fake files' % fakes, 'how': 'removed', 'why': 'junk a protector added'})
        data = steps.get('data_bytes') or {}
        for name in data.get('modified') or []:
            files.append({'file': name, 'how': 'added' if name in (data.get('new_ones') or []) else 'changed',
                          'why': '3.0 data fix'})
        if steps.get('ids'):
            files.append({'file': 'object data and script', 'how': 'changed', 'why': 'object ids restored'})
        if steps.get('listing'):
            files.append({'file': '(listfile)', 'how': 'added', 'why': 'the real file list'})
        same = (r.get('content') or {}).get('identical')
        if same is not None:
            notes.append('%d files identical to the original.' % same)
    else:
        rep = r.get('editor') or {}
        for name in rep.get('replaced') or []:
            files.append({'file': name, 'how': 'changed', 'why': 'for the editor'})
        for name in rep.get('new_ones') or []:
            files.append({'file': name, 'how': 'added', 'why': 'editor-only'})
    for extra in ((extras or {}).get('reports') or {}):
        files.append({'file': EXTRA_NAME.get(extra, extra), 'how': 'applied', 'why': 'an extra'})
    return {'files': files, 'notes': notes}


EXTRA_DONE = {
    'models': 'Fixed the imported models that crash the game.',
    'model_names': 'Gave the models their name back.',
    'portraits': 'Removed the portrait cameras (check the portraits in game).',
    'data_pointers': 'Aligned the data pointers of the levelled fields.',
    'kk_textures': 'Decrypted the textures of the KK platform (BLX1).',
    'disabled_icons': 'Made the disabled art of the imported icons (no more green buttons).',
    'uabi': 'Moved the unit ability lists to the script (test the map before sharing it).',
    'preload': 'Preloaded the models and abilities of the first seconds.',
    'single_player': 'The map no longer ends the game in single player.',
    'card': 'Wrote the map card changes.',
    'translation': 'Applied the translation.',
    'shrink': 'Made the map smaller.',
}
EXTRA_NAME = {
    'models': 'the model fixes',
    'model_names': 'the model names',
    'portraits': 'the portrait cameras',
    'data_pointers': 'the data pointers',
    'kk_textures': 'the KK textures',
    'disabled_icons': 'the disabled icons',
    'uabi': 'the ability lists',
    'preload': 'the early preload',
    'single_player': 'single player',
    'card': 'the map card changes',
    'translation': 'the translation',
    'shrink': 'the shrink',
}
BEFORE_EDITOR = ('models', 'single_player', 'card', 'translation')


def extra_lines(x):
    out = []
    for extra, rep in (x or {}).get('reports', {}).items():
        out.append(('ok', '  - ' + EXTRA_DONE.get(extra, extra)))
        for line in (rep or {}).get('lines') or (rep or {}).get('summary_lines') or []:
            out.append(('info', '      ' + str(line)))
    for extra, why in (x or {}).get('failures', {}).items():
        out.append(('warning', '  - Not applied, %s: %s' % (EXTRA_NAME.get(extra, extra), why)))
    return out


def run_action(D, G, job, path, task, progress, emit):
    d = cached_diagnosis(D, path, progress)
    options = job.get('options') or None
    extras = dict((k, v) for k, v in (job.get('extras') or {}).items() if v)
    out = D.free_output(path, '_fixed' if task == 'fix' else '_editor')
    emit({'type': 'output', 'path': out})
    x = None
    if task == 'fix':
        r = D.unprotect(path, out, progress, diag=d, options=options)
        worked = r.get('status') in ('done', 'partial')
        if extras and (worked or r.get('status') in ('nothing_to_do', 'nothing_selected')):
            x = D.apply_extras(r['output'] if worked else path, part_of(out), extras, progress)
            if x['output']:
                os.replace(part_of(out), out)
                r['output'] = out
        lines = G.unprotection_text(r) if worked or not (x and x['output']) else \
            [('heading', 'Fix map: %s' % os.path.basename(path)), ('file_path', 'Saved as: %s' % out), ('', '')]
        if x and x['output'] and not worked:
            r['status'] = 'done'
    else:
        before = dict((k, v) for k, v in extras.items() if k in BEFORE_EDITOR)
        if before:
            tmp = tempfile.mkdtemp(prefix='devos_map_doctor_editor_')
            try:
                base, r1 = path, None
                if set(p['code'] for p in d['protections']) - set(D.BUTTON3_ONLY) - set(D.DATA_ONLY):
                    r1 = D.unprotect(path, os.path.join(tmp, 'unprotected.w3x'), progress, diag=d, options=options)
                    if r1.get('status') in ('done', 'partial'):
                        base = r1['output']
                x = D.apply_extras(base, os.path.join(tmp, 'extras.w3x'), before, progress)
                if x['output']:
                    base = x['output']
                r = D.prepare_for_editor(base, out, progress, options=options)
                r['before'] = d
                if r1 is not None:
                    r['unprotection'] = r1
            finally:
                shutil.rmtree(tmp, ignore_errors=True)
        else:
            r = D.prepare_for_editor(path, out, progress, diag=d, options=options)
        lines = G.editor_text(r)
    if x:
        lines = lines + [('', ''), ('heading2', 'Extras:')] + extra_lines(x)
    return {'lines': page_lines(lines), 'file': r.get('output'), 'outcome': OUTCOME.get(r.get('status'), 'failed'),
            'changes': page_changes(r, task, x)}


def write_port_failure(report, message, trace=''):
    try:
        with open(report, 'w', encoding='utf-8', newline='\r\n') as f:
            f.write('Port to Reforged 3.0 - report\n' + '=' * 30 + '\n\nResult: stopped\n\nThe port stopped: %s\n'
                    % message)
            if trace:
                f.write('\nWhat the program saw last:\n' + trace.rstrip() + '\n')
    except OSError:
        pass


def page_stub(s):
    return {'native': s.get('native'), 'calls': s.get('calls') or 0, 'functions': list(s.get('functions') or []),
            'triggers': list(s.get('trigger_list') or [])}


def run_port(D, G, path, progress, emit, packages=(), memory=True, icons=False, textures=False):
    from doctor.port import map_port
    out = D.free_output(path, '_reforged')
    emit({'type': 'output', 'path': out})
    report = os.path.splitext(out)[0] + '.report.txt'
    work = tempfile.mkdtemp(prefix='devos_map_doctor_port_')
    try:
        try:
            r = map_port.map_port(path, os.path.join(work, 'port'), out, report, log=progress, packages=list(packages),
                                  memory_hacks='neutralize' if memory else 'equivalents')
        except BaseException as e:
            import traceback
            write_port_failure(report, '%s: %s' % (type(e).__name__, e), traceback.format_exc()[-3000:])
            raise
        if r.get('err'):
            chain = os.path.join(work, 'port', 'port', 'out', 'cadeia.log')
            if os.path.isfile(chain):
                log = os.path.splitext(out)[0] + '.chain.log'
                shutil.copyfile(chain, log)
                r['log'] = log
    finally:
        shutil.rmtree(work, ignore_errors=True)
    ported = r.get('resultado', '').startswith('ported')
    lines = page_lines(G.port_text(r))
    if ported and textures:
        lines += port_step(r['output'], progress, 'kk_textures', None)
    if ported and icons:
        lines += port_step(r['output'], progress, 'disabled_icons', 'Every imported icon already has its disabled art.')
    return {'lines': lines, 'file': r.get('output') if ported else None, 'report': report,
            'outcome': 'ok' if ported else 'failed',
            'port': {'g1': r.get('g1'), 'g2': r.get('g2'), 'stubs': [page_stub(s) for s in r.get('stubs') or []],
                     'warnings': r.get('warnings') or [], 'error': r.get('err'), 'log': r.get('log'),
                     'removed': (r.get('dead_type') or {}).get('types') or [], 'form': r.get('forma'),
                     'jn': bool((r.get('diagnostico') or {}).get('jn')),
                     'implemented': len((r.get('diagnostico') or {}).get('implemented_count') or []),
                     'declared': len((r.get('diagnostico') or {}).get('plataforma') or []),
                     'size': r.get('bytes'), 'seconds': r.get('seconds')}}


def port_step(out, progress, module, nothing):
    tmp = os.path.splitext(out)[0] + '.' + module + os.path.splitext(out)[1]
    try:
        try:
            if module == 'kk_textures':
                from doctor.fix import kk_textures as extra
            else:
                from doctor.fix import disabled_icons as extra
            rel = extra.fix(out, tmp, progress)
        except Exception as e:
            rel = {'state': 'failed', 'error': '%s: %s' % (type(e).__name__, e)}
        if rel.get('state') == 'done':
            os.replace(tmp, out)
            return [['good', x] for x in rel.get('lines') or []]
        if rel.get('state') == 'nothing_to_do':
            return [['good', nothing]] if nothing else []
        return [['warn', '%s were not made: %s' % (EXTRA_NAME.get(module, module).capitalize(),
                                                    rel.get('error') or 'nothing was written')]]
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def run_job(job, emit, G):
    from doctor.fix import unprotect as D

    task, path = job['task'], job.get('map')

    def progress(code):
        emit({'type': 'progress', 'label': G.STAGES.get(code, code) if isinstance(code, str) else str(code)})

    if task == 'open':
        d = cached_diagnosis(D, path, progress)
        return {'map': os.path.abspath(path), 'name': os.path.basename(path), 'size': os.path.getsize(path),
                'lines': page_lines(G.diagnosis_text(d)), 'steps': page_steps(D, d),
                'summary': page_summary(D, d)}
    if task in ('fix', 'editor'):
        return run_action(D, G, job, path, task, progress, emit)
    if task == 'port':
        return run_port(D, G, path, progress, emit, job.get('packages') or [], job.get('memory', True),
                        job.get('icons', False), job.get('textures', False))
    if task == 'cheatpack_inject':
        return _cheatpack_inject(job, progress, emit)
    tool = TOOLS.get(task)
    if tool is None:
        raise ValueError('unknown task %r' % task)
    return tool(job, progress)


def _card(job, progress):
    from doctor.viewers import map_card
    return map_card.read(job['map'], progress)


def _card_image(job, progress):
    from doctor.viewers import map_card
    return map_card.image(job['map'], job.get('which') or 'minimap')


def _gradient(job, progress):
    from doctor.viewers import map_card
    return map_card.gradient(job['text'], job['colors'])


def _reforged(job, progress):
    from doctor.fix import unprotect as D
    from doctor.fix import reforged_check
    r = reforged_check.check(job['map'], progress, diag=cached_diagnosis(D, job['map'], progress))
    items = dict((x['code'], x) for x in r.get('items') or [])
    lock, groups = items.get('single_player_lock'), items.get('model_matrix_groups')
    r['verdict_code'] = VERDICT.get(r.get('verdict'), 'v-unknown')
    r['single_player'] = {'found': bool(lock and lock.get('fix') == 'doctor')}
    r['models'] = {'fixable': len((groups.get('data') or {}).get('models') or []) if groups and
                   groups.get('fix') == 'doctor' else 0}
    portraits, pointers, uabi = items.get('portrait_camera'), items.get('data_pointers'), items.get('uabi_distinct')
    runs = r.get('verdict') != 'node'
    from doctor.mpq import mpqadd
    writable = mpqadd.format(job['map']) == 0 or 'protected_archive' in items
    if not writable:
        r['models'] = {'fixable': 0}
        portraits = pointers = None
        runs = False
    r['portraits'] = {'fixable': len((portraits.get('data') or {}).get('models') or []) if portraits else 0}
    _mn = items.get('model_names')
    r['model_names'] = {'fixable': len(((_mn.get('data') or {}).get('names') or [])) if _mn else 0}
    r['data_pointers'] = {'fixable': len((pointers.get('data') or {}).get('fields') or []) if pointers else 0}
    textures = items.get('kk_textures')
    r['kk_textures'] = {'fixable': (textures.get('data') or {}).get('count', 0) if textures and writable else 0}
    icons = items.get('disabled_icons')
    r['disabled_icons'] = {'fixable': (icons.get('data') or {}).get('count', 0) if icons and writable else 0}
    r['uabi'] = {'distinct': (uabi.get('data') or {}).get('distinct', 0) if uabi and uabi.get('fix') == 'doctor' and
                 runs else 0}
    r['preload'] = {'units': 0, 'abilities': 0}
    if r.get('script') == 'jass' and runs:
        from doctor.fix import early_preload
        try:
            pr = early_preload.scan(job['map'])
            r['preload'] = {'units': len(pr.get('units') or []), 'abilities': len(pr.get('abilities') or [])}
        except Exception:
            pass
    return r


def _files(job, progress):
    from doctor.mpq import import_lint
    from doctor.viewers import map_files
    r = map_files.list_files(job['map'], progress)
    if not r.get('error'):
        lint = import_lint.lint(job['map'], progress)
        r['lint'] = lint.get('files') or {}
        r['lint_counts'] = lint.get('counts') or {}
    return r


def _preview(job, progress):
    from doctor.viewers import map_files
    return map_files.preview(job['map'], job['name'])


def _rawcodes(job, progress):
    from doctor.data import rawcodes
    progress('Reading the raw codes')
    return rawcodes.extract(job['map'])


def _extract(job, progress):
    from doctor.viewers import map_files
    return map_files.extract(job['map'], job['names'], job['folder'], progress)


def _script(job, progress):
    from doctor.viewers import map_files
    return map_files.script(job['map'])


def _script_checks(job, progress):
    from doctor.script import script_checks
    progress('Checking the script')
    return script_checks.check(job['map'])


def _triggers(job, progress):
    from doctor.viewers import map_files
    return map_files.triggers(job['map'], progress)


def _cheatpacks(job, progress):
    from doctor.fix import cheatpacks
    progress('Reading the cheat packs')
    return cheatpacks.list_packs(job['map'])


def _cheatpack_inject(job, progress, emit=lambda event: None):
    from doctor.fix import cheatpacks
    from doctor.fix import unprotect as D
    out = D.free_output(job['map'], '_' + str(job.get('pack') or 'cheat'))
    emit({'type': 'output', 'path': out})
    r = cheatpacks.inject(job['map'], out, job.get('pack'), job.get('options') or {}, progress)
    return {'lines': page_lines(r.get('lines') or []), 'file': r.get('file'), 'pack': r.get('pack'),
            'outcome': 'ok' if r.get('file') else 'failed', 'syntax': r.get('syntax'),
            'script': r.get('script'), 'options': r.get('options')}


def _translation_export(job, progress):
    from doctor.translation import translation_io
    only = job.get('only')
    if job['file'].lower().endswith(('.html', '.htm')):
        return translation_io.export_html(job['map'], job['file'], progress, only)
    return translation_io.export(job['map'], job['file'], progress, only)


def _translation_groups(job, progress):
    from doctor.translation import translation_io
    return translation_io.groups(job['map'], progress)


def _translation_check(job, progress):
    from doctor.translation import translation_io
    return translation_io.check(job['map'], job['file'], progress)


def _compare(job, progress):
    from doctor.viewers import map_compare
    return map_compare.compare(job['map'], job['other'], progress)


TOOLS = {'card': _card, 'card_image': _card_image, 'gradient': _gradient, 'reforged': _reforged, 'files': _files,
         'preview': _preview, 'extract': _extract, 'script': _script, 'script_checks': _script_checks,
         'triggers': _triggers, 'cheatpacks': _cheatpacks, 'cheatpack_inject': _cheatpack_inject,
         'rawcodes': _rawcodes,
         'translation_export': _translation_export, 'translation_groups': _translation_groups,
         'translation_check': _translation_check, 'compare': _compare}


def worker_main(window=None):
    window = window or sys.modules['__main__']
    from doctor.app import windows_rules
    windows_rules.apply()
    out = os.fdopen(os.dup(1), 'w', encoding='utf-8', newline='\n')
    sys.stdout = sys.stderr
    lock = threading.Lock()

    def emit(event):
        with lock:
            out.write(json.dumps(_jsonable(event)) + '\n')
            out.flush()

    try:
        job = json.loads(sys.stdin.buffer.read().decode('utf-8'))
        t0 = time.time()
        result = run_job(job, emit, window)
        emit({'type': 'result', 'data': result, 'seconds': round(time.time() - t0, 1)})
        return 0
    except BaseException as e:
        emit({'type': 'error', 'message': '%s: %s' % (type(e).__name__, e) if str(e) else type(e).__name__,
              'trace': traceback.format_exc(limit=8)})
        return 1
    finally:
        out.flush()


CACHE = os.path.join(tempfile.gettempdir(), 'devos_map_doctor_ui')


def cache_folder(version):
    keep = 'v%s' % version
    folder = os.path.join(CACHE, keep)
    try:
        os.makedirs(folder, exist_ok=True)
        for name in os.listdir(CACHE):
            p = os.path.join(CACHE, name)
            if name == keep:
                continue
            if os.path.isdir(p):
                shutil.rmtree(p, ignore_errors=True)
            else:
                try:
                    os.remove(p)
                except OSError:
                    pass
    except OSError:
        pass
    return folder


def part_of(output):
    base, ext = os.path.splitext(output)
    return base + '.part' + (ext or '.w3x')


class Job:
    def __init__(self, ident, task):
        self.ident, self.task = ident, task
        self.proc = None
        self.tmp = tempfile.mkdtemp(prefix='devos_map_doctor_job_')
        self.output = None
        self.cancelled = False
        self.started = time.time()


class Api:
    def __init__(self, version, initial_map=None, updater=None):
        self._window = None
        self._version = version
        self._initial = initial_map
        self._updater = updater
        self._cache = cache_folder(version)
        self._jobs = {}
        self._next = 0
        self._lock = threading.Lock()

    def hello(self):
        repo = getattr(self._updater, 'REPOSITORY', None)
        return {'version': self._version, 'app': APP, 'map': self._initial, 'settings': load_settings(),
                'repository': None if not repo or repo.startswith('OWNER/') else repo}

    def save_settings(self, data):
        save_settings(data)
        return True

    def _dialog(self, kind, **kw):
        r = self._window.create_file_dialog(kind, **kw)
        if not r:
            return None
        return os.path.normpath(r if isinstance(r, str) else r[0])

    def pick_map(self):
        import webview
        return self._dialog(webview.FileDialog.OPEN, file_types=MAP_TYPES)

    def pick_file(self, kind):
        import webview
        types = {'translation': ('Translation files (*.json;*.html;*.htm)', 'All files (*.*)'),
                 'package': ('Art packages (*.mix;*.asi;*.dll;*.mpq)', 'All files (*.*)'),
                 'image': ('Images (*.png;*.jpg;*.jpeg;*.bmp;*.tga;*.blp)', 'All files (*.*)'),
                 'map': MAP_TYPES}.get(kind, ('All files (*.*)',))
        return self._dialog(webview.FileDialog.OPEN, file_types=types)

    def pick_save(self, suggested, kind):
        import webview
        types = {'translation': ('Translation files (*.json)',),
                 'translation_html': ('Web page for machine translation (*.html)',),
                 'script': ('Scripts (*.j;*.lua)', 'All files (*.*)')}.get(kind, ('All files (*.*)',))
        return self._dialog(webview.FileDialog.SAVE, save_filename=suggested or '', file_types=types)

    def pick_folder(self):
        import webview
        return self._dialog(webview.FileDialog.FOLDER)

    def read_file(self, path):
        with open(path, 'rb') as f:
            return base64.b64encode(f.read(32 << 20)).decode('ascii')

    def write_text(self, path, text):
        with open(path, 'w', encoding='utf-8', newline='') as f:
            f.write(text)
        return True

    def open_folder(self, path):
        if not path or not os.path.exists(path):
            return False
        if os.name == 'nt':
            subprocess.Popen(['explorer', '/select,', os.path.normpath(path)])
            return True
        folder = path if os.path.isdir(path) else os.path.dirname(os.path.abspath(path))
        try:
            subprocess.Popen(['xdg-open', folder], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError:
            return False
        return True

    def open_url(self, url):
        if isinstance(url, str) and url.startswith('https://'):
            webbrowser.open(url)
            return True
        return False

    def report_problem(self, title, body):
        repo = self.hello()['repository']
        if not repo:
            return False
        query = urllib.parse.urlencode({'title': title[:200], 'body': body[:6000]})
        webbrowser.open('https://github.com/%s/issues/new?%s' % (repo, query))
        return True

    def start(self, task, params=None):
        with self._lock:
            self._next += 1
            ident = 'job%d' % self._next
        job = Job(ident, task)
        self._jobs[ident] = job
        env = dict(os.environ, TEMP=job.tmp, TMP=job.tmp, DOCTOR_CACHE=self._cache, PYTHONIOENCODING='utf-8',
                   PYTHONUTF8='1')
        log = open(os.path.join(job.tmp, 'worker.log'), 'wb')
        job.proc = subprocess.Popen(worker_command(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log,
                                    env=env, creationflags=NO_WINDOW if os.name == 'nt' else 0)
        job.proc.stdin.write(json.dumps(dict(params or {}, task=task)).encode('utf-8'))
        job.proc.stdin.close()
        threading.Thread(target=self._read, args=(job, log), daemon=True).start()
        return ident

    def _read(self, job, log):
        final = None
        try:
            for line in job.proc.stdout:
                try:
                    ev = json.loads(line.decode('utf-8'))
                except ValueError:
                    continue
                if not isinstance(ev, dict):
                    continue
                if ev.get('type') == 'output':
                    job.output = ev.get('path')
                    continue
                ev['job'] = job.ident
                if ev.get('type') in ('result', 'error'):
                    final = ev
                else:
                    self._push(ev)
            code = job.proc.wait()
            log.close()
            if job.cancelled:
                final = {'type': 'cancelled', 'job': job.ident}
                if job.output:
                    self._drop_part(job)
                    final['kept'] = os.path.isfile(job.output)
                    final['output'] = job.output
            elif final is None:
                try:
                    with open(os.path.join(job.tmp, 'worker.log'), 'rb') as f:
                        tail = f.read()[-1500:].decode('utf-8', 'replace')
                except OSError:
                    tail = ''
                final = {'type': 'error', 'job': job.ident, 'message': 'The worker stopped (exit code %s).' % code,
                         'trace': tail}
                if job.output:
                    self._drop_part(job)
                if job.task == 'port' and job.output:
                    write_port_failure(os.path.splitext(job.output)[0] + '.report.txt', final['message'], tail)
        except Exception as e:
            try:
                job.proc.kill()
            except OSError:
                pass
            final = {'type': 'error', 'job': job.ident, 'trace': traceback.format_exc(limit=8),
                     'message': 'The window could not read the worker (%s: %s).' % (type(e).__name__, e)}
        finally:
            try:
                log.close()
            except OSError:
                pass
            if final is None:
                final = {'type': 'error', 'job': job.ident, 'message': 'The worker stopped without a result.'}
            final['elapsed'] = round(time.time() - job.started, 1)
            shutil.rmtree(job.tmp, ignore_errors=True)
            self._jobs.pop(job.ident, None)
            self._push(final)

    @staticmethod
    def _drop_part(job):
        try:
            os.remove(part_of(job.output))
        except OSError:
            pass

    def _push(self, ev):
        if self._window is None:
            return
        try:
            self._window.evaluate_js('window.doctor && window.doctor.onEvent(%s)' % json.dumps(ev))
        except Exception:
            pass

    def cancel(self, ident):
        job = self._jobs.get(ident)
        if job is None or job.proc is None:
            return False
        job.cancelled = True
        try:
            job.proc.kill()
        except OSError:
            pass
        return True

    def busy(self):
        return sorted(self._jobs)

    def check_update(self):
        u = self._updater
        if u is None or not u.enabled(sys.argv):
            return False
        u.check(self._version, lambda r: self._push({'type': 'update', 'release': r}),
                lambda r: self._push({'type': 'index', 'release': r, 'missing': not os.path.isfile(u.index_path())}))
        return True

    def install_update(self, release):
        try:
            if self._updater.install(release):
                self._window.destroy()
            return True
        except Exception as e:
            self._updater.open_page(release)
            return str(e)

    def download_index(self, release):
        def work():
            try:
                self._updater.download_index(release)
                self._push({'type': 'index_done'})
            except Exception as e:
                self._push({'type': 'index_failed', 'message': str(e)})
        threading.Thread(target=work, daemon=True).start()
        return True


def run(version, initial_map=None, updater=None, icon=None):
    import webview
    from webview.dom import DOMEventHandler

    api = Api(version, initial_map, updater)
    window = webview.create_window(APP, url=os.path.join(ui_folder(), 'index.html'), js_api=api, width=1200,
                                   height=840, min_size=(940, 620), background_color='#121418', text_select=True)
    api._window = window

    def closing():
        for ident in list(api._jobs):
            api.cancel(ident)

    def dropped(e):
        files = (e.get('dataTransfer') or {}).get('files') or []
        path = files[0].get('pywebviewFullPath') if files else None
        if path:
            api._push({'type': 'dropped', 'path': path})

    def loaded():
        try:
            window.dom.document.events.dragover += DOMEventHandler(lambda e: None, True, True)
            window.dom.document.events.drop += DOMEventHandler(dropped, True, True)
        except Exception:
            pass

    window.events.closing += closing
    window.events.loaded += loaded
    if os.name == 'nt':
        webview.start(gui='edgechromium', icon=icon)
    else:
        try:
            import gi
            gi.require_version('Gtk', '3.0')
        except (ImportError, ValueError) as e:
            raise SystemExit(LINUX_WINDOW_MISSING % e)
        if getattr(sys, 'frozen', False):
            if os.environ.get('LD_LIBRARY_PATH_ORIG') is not None:
                os.environ['LD_LIBRARY_PATH'] = os.environ['LD_LIBRARY_PATH_ORIG']
            else:
                os.environ.pop('LD_LIBRARY_PATH', None)
        webview.start(gui='gtk', icon=icon)


LINUX_WINDOW_MISSING = '''The window needs GTK and WebKitGTK, which this system does not have (%s).

  Debian, Ubuntu, Mint:  sudo apt install libgirepository-1.0-1 gir1.2-gtk-3.0 gir1.2-webkit2-4.1
  Fedora:                sudo dnf install gobject-introspection gtk3 webkit2gtk4.1
  Arch:                  sudo pacman -S gobject-introspection gtk3 webkit2gtk-4.1

Without the window, the command line does everything the window does: DevosMapDoctor --help'''
