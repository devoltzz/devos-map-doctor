# The command line: the jobs of the window run from a terminal, with the flags the page shows.
import json
import os
import sys
import time


USAGE = '''Devo's Map Doctor {version}, command line

usage: doctor <command> <map> [options]

  diag <map>                      what protects the map and what the World Editor needs
  fix <map> [steps] [extras]      Fix map: saves <map>_fixed.w3x
  editor <map> [steps] [extras]   Open in World Editor: saves <map>_editor.w3x
  port <map> [--package=<name>] [--icons] [--textures] [--keep-memory] [--balance-numbers] [--strip-indent]
                                  Port to Reforged (KK and M16 maps): saves <map>_reforged.w3x and the report
  check <map>                     Runs on Reforged? (what crashes or misses on 3.0)
  cheatpacks <map>                the cheat packs the map takes, with their options
  cheat <map> --pack=<id> [--set <key>=<value> ...] [--strip-indent]
                                  adds a cheat pack: saves <map>_<pack>.w3x
  qol <map>                       what the map has for each quality of life edit
  qol <map> [--xp=<x>] [--gold=<x>] [--lumber=<x>] [--drop=<x>] [--craft=<x>] [--respawn=<x>] [--creep=<x>]
            [--noshake] [--noshake-off] [--reveal] [--vip] [--strip-indent]
                                  the quality of life edits (multipliers; --respawn=0.5 halves the hero revive
                                  time, --creep=0.5 the monster respawn time): saves <map>_qol.w3x
  translation groups <map>        the files the texts come from
  translation export <map> <file.txt|file.html> [--only=<group>,...]
  translation check <map> <file>  checks a translated file against the map (apply it: fix --translation=<file>)
  translation machine <map> <file.json> [--quality=best|fast] [--only=<group>,...]
                                  translates the texts into English on this computer (an open translation model,
                                  downloaded the first time) and checks the file against the map
  files <map>                     the files inside the map
  extract <map> <name>... [--to=<folder>]
  script <map> [--to=<file>]      the map script (printed, or saved)
  rawcodes <map>                  the object ids with their names
  card <map>                      name, author, players, loading screen
  compare <map> <other map>       what differs between two maps

Steps of fix / editor (none given: the defaults the window ticks for this map; --no-<step> drops one):
  --unprotect --fake-files --listfile --ids --data --script-back --editor-files --counts --doodads
  --gui-triggers --script-objects --safe-units
Extras of fix / editor:
  --models --model-names --portraits --data-pointers --kk-textures --green-icons --uabi --preload
  --single-player --shrink --translation=<file> --strip-indent

--strip-indent (fix, editor, port, cheat, qol): the script without the spaces and tabs that start its lines

Everywhere: --json (what the job returned), --quiet (no progress), --help, --version
'''

STEP_FLAGS = {'mpq': 'unprotect', 'fake_list': 'fake-files', 'fake_list': 'fake-files', 'listing': 'listfile',
              'listing': 'listfile', 'ids': 'ids', 'unprotection': 'unprotect', 'unprotection': 'unprotect',
              'script_restore': 'script-back', 'script_restore': 'script-back',
              'editor_only_files': 'editor-files', 'editor_only_files': 'editor-files',
              'inflated_counts': 'counts', 'inflated_counts': 'counts', 'invalid_doodads': 'doodads',
              'invalid_doodads': 'doodads', 'gui_triggers': 'gui-triggers', 'script_objects': 'script-objects',
              'safe_units': 'safe-units'}
EXTRA_FLAGS = {'models': 'models', 'model-names': 'model_names', 'portraits': 'portraits',
               'data-pointers': 'data_pointers', 'kk-textures': 'kk_textures', 'green-icons': 'disabled_icons',
               'uabi': 'uabi', 'preload': 'preload', 'single-player': 'single_player', 'strip-indent': 'strip_indent'}
EDITOR_EXTRAS = ('single-player', 'translation', 'strip-indent')
OUTCOME_CODE = {'ok': 0, 'nothing': 0, 'partial': 3, 'failed': 1}


class UsageError(Exception):
    pass


def parse(argv):
    pos, opts = [], {}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ('-h', '--help'):
            opts['help'] = True
        elif a == '--set':
            if i + 1 >= len(argv):
                raise UsageError('--set needs <key>=<value>')
            opts.setdefault('set', []).append(argv[i + 1])
            i += 1
        elif a.startswith('--'):
            name, eq, value = a[2:].partition('=')
            if eq:
                opts[name] = value
            elif name.startswith('no-'):
                opts[name[3:]] = False
            else:
                opts[name] = True
        else:
            pos.append(a)
        i += 1
    return pos, opts


def step_flag(key):
    if key.startswith(('dados:', 'data:')):
        return 'data'
    return STEP_FLAGS.get(key) or key.replace('_', '-').replace(':', '-')


def pick_steps(steps, action, opts):
    mine = [s for s in steps if s['action'] == action]
    known = set(step_flag(s['key']) for s in mine)
    named = [f for f, v in opts.items() if v is True and f in known]
    out = {}
    for s in mine:
        flag = step_flag(s['key'])
        if s['locked']:
            out[s['key']] = s['applies']
        elif named:
            out[s['key']] = s['applies'] and flag in named
        else:
            out[s['key']] = s['applies'] and s['on'] and opts.get(flag) is not False
    return out


def pick_extras(action, opts):
    extras = {}
    for flag, key in EXTRA_FLAGS.items():
        if opts.get(flag) is True and (action == 'fix' or flag in EDITOR_EXTRAS):
            extras[key] = True
    if isinstance(opts.get('translation'), str):
        if not os.path.isfile(opts['translation']):
            raise UsageError('no such translation file: %s' % opts['translation'])
        extras['translation'] = os.path.abspath(opts['translation'])
    if opts.get('shrink') is True and action == 'fix':
        extras['shrink'] = {'recompress': True, 'blp': True, 'dedup': True}
    return extras


class Out:
    def __init__(self, quiet):
        self.quiet = quiet
        self.tty = hasattr(sys.stderr, 'isatty') and sys.stderr.isatty()
        self.last = ''
        for stream in (sys.stdout, sys.stderr):
            try:
                stream.reconfigure(encoding='utf-8', errors='replace')
            except (AttributeError, ValueError):
                pass

    def event(self, ev):
        if self.quiet or ev.get('type') != 'progress':
            return
        label = str(ev.get('label') or '').strip()
        if not label or label == self.last:
            return
        self.last = label
        if self.tty:
            sys.stderr.write('\r\x1b[2K' + label[:100])
        else:
            sys.stderr.write(label + '\n')
        sys.stderr.flush()

    def done(self):
        if self.tty and self.last and not self.quiet:
            sys.stderr.write('\r\x1b[2K')
            sys.stderr.flush()
        self.last = ''


def print_lines(lines):
    for style, text in lines or []:
        if style == 'title':
            print('== %s' % text)
        elif style == 'subtitle':
            print('-- %s' % text)
        else:
            print(text)


def print_changes(changes):
    files = (changes or {}).get('files') or []
    if files:
        print('\nWhat changed:')
        width = min(40, max(len(str(f.get('file', ''))) for f in files))
        for f in files:
            print('  %-*s  %-10s  %s' % (width, f.get('file', ''), f.get('how', ''), f.get('why', '')))
    for note in (changes or {}).get('notes') or []:
        print(note)


def show(command, r):
    if command in ('diag', 'fix', 'editor', 'port', 'cheat', 'qol apply'):
        print_lines(r.get('lines'))
        if command in ('fix', 'editor'):
            print_changes(r.get('changes'))
        if command == 'port' and r.get('report'):
            print('\nReport: %s' % r['report'])
        return
    if command == 'check':
        print('Runs on Reforged? %s' % r.get('verdict'))
        for it in r.get('items') or []:
            print('  [%s] %s' % (it.get('severity'), it.get('text')))
        return
    if command == 'cheatpacks':
        if r.get('error'):
            print(r['error'])
        print('Script: %s (%s)' % (r.get('script'), r.get('language')))
        for p in r.get('packs') or []:
            print('\n%s  %s%s  (%s)' % (p['id'], p.get('title'), '  [default]' if p.get('default') else '',
                                       p.get('needs')))
            for o in p.get('options') or []:
                print('    --set %s=%s   %s' % (o.get('key'), o.get('default'), o.get('label')))
        return
    if command == 'qol':
        if not r.get('supported'):
            print(r.get('reason') or 'The map cannot take the QoL edits.')
            return
        print('Script: %s (%s)' % (r.get('script'), r.get('language')))
        for k, v in (r.get('found') or {}).items():
            print('  %-18s %s' % (k, ', '.join(v) if isinstance(v, list) else v))
        return
    if command == 'files':
        for f in r.get('files') or []:
            print('%10d  %-8s  %s' % (f.get('size') or 0, f.get('kind') or '', f.get('name')))
        for f in r.get('unnamed') or []:
            print('%10d  %-8s  (block %s, no name%s)' % (f.get('size') or 0, f.get('kind') or '', f.get('block'),
                                                        ', ' + f['ext'] if f.get('ext') else ''))
        print('%d files' % (r.get('total') or 0))
        return
    if command == 'rawcodes':
        sys.stdout.write(r.get('text') or '')
        return
    if command == 'translation groups':
        for g in r.get('groups') or []:
            print('%-24s %5d  %s' % (g.get('key'), g.get('count') or 0, g.get('label')))
        return
    if command == 'translation export':
        if r.get('error'):
            print(r['error'])
        else:
            print('Exported %d texts to %s' % (r.get('entries') or 0, r.get('file')))
        return
    if command == 'translation machine':
        if r.get('error'):
            print(r['error'])
            return
        print('Translated %d of %d texts into English (%s, from %s) in %s s: %s' % (
            r.get('translated') or 0, r.get('entries') or 0, r.get('model'), r.get('language'), r.get('seconds'),
            r.get('file')))
        for why, n in sorted((r.get('rejected') or {}).items()):
            print('  %d left in the original: %s' % (n, why))
        c = r.get('check') or {}
        print('%d pass the checks' % (c.get('ok') or 0))
        return
    if command == 'translation check':
        if r.get('error'):
            print(r['error'])
            return
        print('%d translated, %d still empty, %d rejected, %d not in this map' % (
            r.get('ok') or 0, r.get('empty') or 0, len(r.get('rejected') or []), len(r.get('unknown') or [])))
        for x in (r.get('rejected') or [])[:20]:
            print('  rejected: %s' % (x if isinstance(x, str) else json.dumps(x, ensure_ascii=False)[:200]))
        return
    if command == 'compare':
        if r.get('error'):
            print(r['error'])
        f = r.get('files') or {}
        for k in ('added', 'removed', 'changed'):
            for x in f.get(k) or []:
                print('%-8s %s' % (k, x.get('name')))
        print('%d files the same' % len(f.get('same') or []))
        s = r.get('script') or {}
        for k in ('added', 'removed', 'changed'):
            if s.get(k):
                print('script: %d functions %s' % (len(s[k]), k))
        for part in ('info', 'strings'):
            n = sum(len((r.get(part) or {}).get(k) or []) for k in ('added', 'removed', 'changed'))
            if n:
                print('%s: %d differences' % (part, n))
        if r.get('objects'):
            print('objects: %d kinds differ (--json has them)' % len(r['objects']))
        return
    if command == 'extract':
        for w in r.get('written') or []:
            print('%s -> %s' % (w.get('name'), os.path.join(r.get('out_dir') or '', w.get('path') or '')))
        for w in r.get('same') or []:
            print('%s: already there, the same' % w.get('name'))
        for f in r.get('failed') or []:
            print('not written: %s (%s)' % (f.get('name'), f.get('reason')))
        for f in r.get('exists') or []:
            print('%s: a different file is already there, left as it was' % f.get('name'))
        if r.get('error'):
            print(r['error'])
        return
    if command == 'card':
        for k in ('name', 'author', 'players_suggested', 'description'):
            if r.get(k):
                print('%s: %s' % (k.replace('_', ' ').capitalize(), r[k]))
        return
    if r.get('lines'):
        print_lines(r['lines'])
        return
    print(json.dumps(r, ensure_ascii=False, indent=1, default=str))


def need(pos, n, what):
    if len(pos) < n:
        raise UsageError('missing %s' % what)
    for p in pos[1:2]:
        if not os.path.isfile(p):
            raise UsageError('no such map: %s' % p)


def build_job(command, pos, opts, run):
    if command == 'diag':
        need(pos, 2, '<map>')
        return 'diag', {'task': 'open', 'map': pos[1]}
    if command in ('fix', 'editor'):
        need(pos, 2, '<map>')
        opened = run({'task': 'open', 'map': pos[1]})
        return command, {'task': command, 'map': pos[1], 'options': pick_steps(opened['steps'], command, opts),
                         'extras': pick_extras(command, opts)}
    if command == 'port':
        need(pos, 2, '<map>')
        packages = [p for p in str(opts.get('package') or '').split(',') if p] if opts.get('package') else []
        return 'port', {'task': 'port', 'map': pos[1], 'packages': packages,
                        'memory': not opts.get('keep-memory'), 'icons': bool(opts.get('icons')),
                        'textures': bool(opts.get('textures')), 'balance': bool(opts.get('balance-numbers')),
                        'strip_indent': opts.get('strip-indent') is True}
    if command == 'check':
        need(pos, 2, '<map>')
        return 'check', {'task': 'reforged', 'map': pos[1]}
    if command == 'cheatpacks':
        need(pos, 2, '<map>')
        return 'cheatpacks', {'task': 'cheatpacks', 'map': pos[1]}
    if command == 'cheat':
        need(pos, 2, '<map>')
        if not isinstance(opts.get('pack'), str):
            raise UsageError('cheat needs --pack=<id> (doctor cheatpacks <map> lists them)')
        options = {}
        for kv in opts.get('set') or []:
            k, eq, v = kv.partition('=')
            if not eq:
                raise UsageError('--set takes <key>=<value>, not %r' % kv)
            options[k] = {'true': True, 'false': False}.get(v.lower(), v)
        return 'cheat', {'task': 'cheatpack_inject', 'map': pos[1], 'pack': opts['pack'], 'options': options,
                         'strip_indent': opts.get('strip-indent') is True}
    if command == 'qol':
        need(pos, 2, '<map>')
        options = {}
        for k in ('xp', 'gold', 'lumber', 'drop', 'craft', 'respawn', 'creep'):
            if k in opts:
                try:
                    options[k] = float(opts[k])
                except (TypeError, ValueError):
                    raise UsageError('--%s takes a number, not %r' % (k, opts[k]))
        for flag, key in (('noshake', 'noshake'), ('noshake-off', 'noshake_default'), ('reveal', 'reveal'),
                          ('vip', 'vip')):
            if opts.get(flag) is True:
                options[key] = True
        if not options:
            return 'qol', {'task': 'qol', 'map': pos[1]}
        return 'qol apply', {'task': 'qol_apply', 'map': pos[1], 'options': options,
                             'strip_indent': opts.get('strip-indent') is True}
    if command == 'translation':
        sub = pos[1] if len(pos) > 1 else None
        rest = pos[1:]
        if sub == 'groups':
            need(rest, 2, '<map>')
            return 'translation groups', {'task': 'translation_groups', 'map': rest[1]}
        if sub == 'export':
            need(rest, 3, '<map> <file>')
            only = [x for x in str(opts['only']).split(',') if x] if isinstance(opts.get('only'), str) else None
            return 'translation export', {'task': 'translation_export', 'map': rest[1],
                                          'file': os.path.abspath(rest[2]), 'only': only}
        if sub == 'check':
            need(rest, 3, '<map> <file>')
            return 'translation check', {'task': 'translation_check', 'map': rest[1], 'file': os.path.abspath(rest[2])}
        if sub == 'machine':
            need(rest, 3, '<map> <file.json>')
            only = [x for x in str(opts['only']).split(',') if x] if isinstance(opts.get('only'), str) else None
            quality = opts.get('quality') if isinstance(opts.get('quality'), str) else 'best'
            if quality not in ('best', 'fast'):
                raise UsageError('--quality=best or --quality=fast')
            return 'translation machine', {'task': 'translation_machine', 'map': rest[1],
                                           'file': os.path.abspath(rest[2]), 'only': only, 'quality': quality}
        raise UsageError('translation groups | export | check | machine')
    if command == 'files':
        need(pos, 2, '<map>')
        return 'files', {'task': 'files', 'map': pos[1]}
    if command == 'extract':
        need(pos, 3, '<map> <name>')
        folder = os.path.abspath(opts['to']) if isinstance(opts.get('to'), str) else \
            os.path.splitext(os.path.abspath(pos[1]))[0] + '_files'
        return 'extract', {'task': 'extract', 'map': pos[1], 'names': pos[2:], 'folder': folder}
    if command == 'script':
        need(pos, 2, '<map>')
        return 'script', {'task': 'script', 'map': pos[1]}
    if command == 'rawcodes':
        need(pos, 2, '<map>')
        return 'rawcodes', {'task': 'rawcodes', 'map': pos[1]}
    if command == 'card':
        need(pos, 2, '<map>')
        return 'card', {'task': 'card', 'map': pos[1]}
    if command == 'compare':
        need(pos, 3, '<map> <other map>')
        if not os.path.isfile(pos[2]):
            raise UsageError('no such map: %s' % pos[2])
        return 'compare', {'task': 'compare', 'map': pos[1], 'other': pos[2]}
    raise UsageError('unknown command %r' % command)


def outcome_code(command, r):
    if 'outcome' in (r or {}):
        return OUTCOME_CODE.get(r['outcome'], 1)
    if (r or {}).get('error') or (r or {}).get('state') == 'failed':
        return 1
    return 0


def main(argv, window, version=''):
    from doctor.app import doctor_app
    from doctor.app import windows_rules
    windows_rules.apply()
    try:
        pos, opts = parse(list(argv))
    except UsageError as e:
        sys.stderr.write('doctor: %s\n' % e)
        return 2
    if opts.get('version'):
        print(version)
        return 0
    if opts.get('help') or not pos:
        sys.stdout.write(USAGE.replace('{version}', version))
        return 0 if opts.get('help') else 2
    out = Out(bool(opts.get('quiet')) or bool(opts.get('json')) and not sys.stderr.isatty())
    if version and not os.environ.get('DOCTOR_CACHE'):
        os.environ['DOCTOR_CACHE'] = doctor_app.cache_folder(version)

    def run(job):
        real = sys.stdout
        sys.stdout = open(os.devnull, 'w', encoding='utf-8') if out.quiet else sys.stderr
        try:
            return doctor_app.run_job(job, out.event, window)
        finally:
            if sys.stdout is not sys.stderr:
                sys.stdout.close()
            sys.stdout = real
            out.done()

    try:
        command, job = build_job(pos[0], pos, opts, run)
    except UsageError as e:
        sys.stderr.write('doctor: %s\n(doctor --help lists the commands)\n' % e)
        return 2
    t0 = time.time()
    try:
        r = run(job)
    except KeyboardInterrupt:
        sys.stderr.write('doctor: cancelled\n')
        return 130
    except Exception as e:
        sys.stderr.write('doctor: %s failed: %s: %s\n' % (pos[0], type(e).__name__, e))
        if os.environ.get('DOCTOR_TRACE'):
            raise
        return 1
    if opts.get('json'):
        print(json.dumps(doctor_app._jsonable(r), ensure_ascii=False, indent=1))
    elif command == 'script' and isinstance(opts.get('to'), str):
        with open(opts['to'], 'w', encoding='utf-8', newline='') as f:
            f.write(r.get('text') or '')
        print('Saved as: %s' % os.path.abspath(opts['to']))
    elif command == 'script':
        sys.stdout.write(r.get('text') or r.get('error') or '')
    else:
        show(command, r)
    sys.stdout.flush()
    if not opts.get('quiet') and not opts.get('json'):
        sys.stderr.write('(%.1f s)\n' % (time.time() - t0))
    return outcome_code(command, r)


def install_launcher():
    if os.name != 'nt' or not getattr(sys, 'frozen', False):
        return
    src = os.path.join(getattr(sys, '_MEIPASS', ''), 'doctor.exe')
    dst = os.path.join(os.path.dirname(sys.executable), 'doctor.exe')
    try:
        with open(src, 'rb') as f:
            blob = f.read()
        if os.path.isfile(dst):
            with open(dst, 'rb') as f:
                if f.read() == blob:
                    return
        with open(dst + '.new', 'wb') as f:
            f.write(blob)
        os.replace(dst + '.new', dst)
    except OSError:
        pass
