# The command line: the jobs of the window run from a terminal, with the flags the page shows.
import json
import os
import sys
import time


USAGE = '''Devo's Map Doctor {version}, command line

usage: doctor <command> <map> [options]

<map> is a map (.w3x, .w3m), a campaign (.w3n) or an art package (a .mix, .asi or .dll with an MPQ inside, a .mpq,
a .w3mod): a package is read as data, never run; diag, files and extract work on it.

  diag <map>                      what protects the map and what the World Editor needs (a package: what it carries)
  fix <map> [steps] [extras]      Fix map: saves <map>_fixed.w3x
  editor <map> [steps] [extras] [--editor-version=<v>]
                                  Open in World Editor: saves <map>_editor.w3x; --editor-version: the World
                                  Editor to open it in, reforged (the default), 1.24 to 1.29 (keeps the map's
                                  version), jn (the JassNative Editor: keeps the 1.27 version, with that editor's
                                  own trigger functions and variable types), or auto (the version the map was
                                  saved for)
  port <map> [--to=<version>] [--package=<name>] [--icons] [--textures] [--keep-memory] [--balance-numbers]
       [--strip-indent]
       (the icons and the textures are on, as in the window: --no-icons, --no-textures)
       [--remove-game-files] [--lossy] [--classic-effects]
                                  Port to Reforged (KK and M16 maps): saves <map>_reforged.w3x and the report;
                                  --to=<version>: to another version of the classic game instead (1.24a to
                                  1.29.2; newer or older than the map, a Reforged map included; no platform, no
                                  Lua), or to Reforged 2.0.4 (--to=2.0.4: a map made for a newer Reforged, Lua
                                  too): saves <map>_<version>.w3x;
                                  --package: the art packages the map needs, comma separated, the first wins (a
                                  .mix, .asi, .dll or .mpq, a .zip of the map's art, or a folder of loose files the
                                  map read from the game folder with "Allow Local Files");
                                  --remove-game-files: the map's images and models with the path of a game file
                                  (they replace the game's own; counted in the report either way) come out;
                                  --lossy: a map still above 512 MiB after the lossless shrink gets its biggest
                                  textures halved and its WAV sounds mono at 22 kHz until it fits;
                                  --classic-effects: the game's own effect models the map uses keep their classic
                                  (SD) look, copied into the map under new names with the references rewritten
                                  (Reforged shows their HD variant, another effect for many spells)
  check <map> [--game=<version>]  Runs on Reforged? (what crashes or misses on 3.0, and the threads of a JASS script's
                                  start that do more work than the game lets one thread do); --game=1.27 (or
                                  --version=1.27) checks an older game instead: 1.24a to 1.28.5 and 1.29.2
  cheatpacks <map>                the cheat packs the map takes, with their options
  cheat <map> --pack=<id> [--set <key>=<value> ...] [--strip-indent] [--durable]
                                  adds a cheat pack: saves <map>_<pack>.w3x; --durable: also a readable copy in
                                  the map's triggers, so the pack can survive a save in the World Editor
  qol <map>                       what the map has for each quality of life edit
  qol <map> [--xp=<x>] [--gold=<x>] [--lumber=<x>] [--drop=<x>] [--craft=<x>] [--respawn=<x>] [--creep=<x>]
            [--noshake] [--noshake-off] [--reveal] [--vip] [--strip-indent]
                                  the quality of life edits (multipliers; --respawn=0.5 halves the hero revive
                                  time, --creep=0.5 the monster respawn time): saves <map>_qol.w3x
  translation groups <map>        the files the texts come from
  translation export <map> <file.json|file.html> [--only=<group>,...] [--images]
  translation check <map> <file>  checks a translated file against the map (apply it: fix --translation=<file>)
  translation override <map> <file>
                                  for a map that must stay the original (M16 rooms): the translation in an archive
                                  of its own, saves <map>_translation.mpq with only the files outside the map
                                  checksum (the script's texts stay); a .mix loader the Doctor does not make must
                                  open it above the map (priority 17 or more), and only while that map is played
  translation machine <map> <file.json> [--quality=best|fast] [--only=<group>,...] [--images] [--keep=<file>]
                                  translates the texts into English on this computer (an open translation model,
                                  downloaded the first time) and checks the file against the map; --keep: a
                                  translation file of the map whose filled texts stay, only its empty ones are
                                  translated (a translation done in parts)
  --images (export, machine): the text drawn in the map's images too (read by OCR; the import redraws them)
  files <map>                     the files inside the map (an unnamed one as #<block>)
  extract <map> <name>... [--to=<folder>]
  extract <map> --all [--to=<folder>]
                                  every file, at its path (the unnamed ones in a folder named unnamed)
  extract <map> --models [--to=<folder>]
                                  every model with the textures and emitter models it needs, at the paths the
                                  models cite (a viewer opens them); what only the game has is listed
  script <map> [--to=<file>]      the map script (printed, or saved)
  rawcodes <map>                  the object ids with their names
  recipes <map> [--out=<file>] [--all]
                                  the item recipes the script makes (result = ingredients, with ids and names);
                                  --out writes them: .txt (one per line), .json or .csv by the extension;
                                  --all also lists one item for another and the blocks that make several items
  card <map>                      name, author, players, loading screen
  compare <map> <other map>       what differs between two maps
  diagnose <map> [--all]          the diagnostic copy: saves <map>_diag.w3x, which writes a log to
                                  CustomMapData\\DevosMapDoctor while it is played (--all: every function marked)
  diagnose <map> --init           the same, and every step of the load marked in its own file (a load that hangs)
  log [<file.pld>|<folder _init>] reads the log of a diagnostic copy (none given: the newest one the game wrote)
  replay [<file.w3g>|<folder>]    reads a replay: the players, chat, who left, sync and frame events, the checksums
                                  (none given: lists the replays the game kept)
  replay-compare <a.w3g> <b.w3g>  the first turn where the two games' state checksums differ (a desync)
  save <file.w3z|file.w3v> [--to=<folder>]
                                  reads a save game or a campaign save (the container, the map, the game); --to
                                  writes its parts
  crash [<folder|Crash.txt|War3Log.txt>] [--map=<map>]
                                  reads the game's crash report or log (none given: lists the crash reports);
                                  --map: counts that map's files at the game's own paths

Steps of fix / editor (none given: the defaults the window ticks for this map; --no-<step> drops one):
  --unprotect --fake-files --listfile --ids --data --script-back --editor-files --counts --doodads
  --gui-triggers --script-objects --safe-units
Extras of fix / editor (fix turns on by itself the ones the window ticks when its check finds them: --models
  --model-names --data-pointers --kk-textures --green-icons --fix-attributes --fix-graphics-modes --fix-requirements
  --fix-fdf; --no-<extra> leaves one out; the others are off unless given):
  --models --model-names --portraits --data-pointers --kk-textures --green-icons --uabi --preload
  --single-player --shrink --shrink-lossy --translation=<file> --strip-indent
  --fix-attributes --remove-game-files --remove-game-copies --fix-requirements --fix-fdf --null-handles --minify
  --slk-objects --fix-graphics-modes
  --portraits=stamp|upgrade --shrink-models --shrink-models-lossy --lobby-image=<picture>
  --fix-attributes         redo the file checksums
  --remove-game-files      take out the map files that replace the game's own (needs the game installed)
  --remove-game-copies     only the ones that are byte-for-byte copies of the game's file (needs the game installed)
  --fix-requirements       unlock abilities that require a tech the map lacks
  --fix-fdf                fix frame file lists
  --null-handles           null handle locals (JASS)
  --minify                 shrink the JASS script
  --slk-objects            make the editor object files from the SLK tables of an optimized map (needs the game)
  --fix-graphics-modes     copy into the map the game files that only some graphics modes have (Classic,
                           Reforged, Definitive Edition), as many as fit below 512 MB (needs the game)
  --portraits=stamp|upgrade  the black portrait fix with the model version 1800 (stamp), or also the 3.0 layout
                           (upgrade): untested in game, try one hero first
  --shrink-models          models smaller without loss; --shrink-models-lossy also drops animation keys that change
                           a movement by less than 0.05 units or a rotation by less than 0.002 rad
  --lobby-image=<picture>  your own lobby image (the minimap moves to war3mapMap_ingame.blp); untested in game
  --shrink-lossy           the shrink, and if the map is still above 512 MiB its art made smaller until it fits

--strip-indent (fix, editor, port, cheat, qol): the script without the spaces and tabs that start its lines

Everywhere: --json (what the job returned), --quiet (no progress), --help, --version
--json-schema (or: doctor schema)  the --json contract: each command's options and result keys, versioned by the
                                   "schema" number every --json result carries (readme/CLI.md)
'''

STEP_FLAGS = {'mpq': 'unprotect', 'fake_list': 'fake-files', 'fake_list': 'fake-files', 'listing': 'listfile',
              'listing': 'listfile', 'ids': 'ids', 'unprotection': 'unprotect', 'unprotection': 'unprotect',
              'script_restore': 'script-back', 'script_restore': 'script-back',
              'editor_only_files': 'editor-files', 'editor_only_files': 'editor-files',
              'inflated_counts': 'counts', 'inflated_counts': 'counts', 'invalid_doodads': 'doodads',
              'invalid_doodads': 'doodads', 'gui_triggers': 'gui-triggers', 'script_objects': 'script-objects',
              'safe_units': 'safe-units'}
EXTRA_FLAGS = {
    'models': 'models',
    'model-names': 'model_names',
    'portraits': 'portraits',
    'data-pointers': 'data_pointers',
    'kk-textures': 'kk_textures',
    'green-icons': 'disabled_icons',
    'uabi': 'uabi',
    'preload': 'preload',
    'single-player': 'single_player',
    'strip-indent': 'strip_indent',
    'fix-attributes': 'attributes',
    'remove-game-files': 'game_overrides',
    'fix-requirements': 'requirements',
    'fix-fdf': 'fdf',
    'null-handles': 'null_handles',
    'minify': 'minify',
    'slk-objects': 'slk_objects',
    'fix-graphics-modes': 'graphics_modes',
}
EDITOR_EXTRAS = ('single-player', 'translation', 'strip-indent')
OUTCOME_CODE = {'ok': 0, 'nothing': 0, 'partial': 3, 'failed': 1}


class UsageError(Exception):
    pass


class _Opts(dict):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.seen = set()

    def get(self, k, d=None):
        self.seen.add(k)
        return super().get(k, d)

    def __getitem__(self, k):
        self.seen.add(k)
        return super().__getitem__(k)

    def __contains__(self, k):
        self.seen.add(k)
        return super().__contains__(k)


def parse(argv):
    pos, opts = [], _Opts()
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
    if key in ('duplicate_textures', 'duplicate_textures'):
        return 'identical-textures'
    return STEP_FLAGS.get(key) or key.replace('_', '-').replace(':', '-')


def pick_steps(steps, action, opts):
    mine = [s for s in steps if s['action'] == action]
    known = set(step_flag(s['key']) for s in mine)
    named = [f for f in sorted(known) if opts.get(f) is True]
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


DEFAULT_EXTRAS = (('models', 'models', 'models'), ('model-names', 'model_names', 'model_names'),
                  ('data-pointers', 'data_pointers', 'data_pointers'), ('kk-textures', 'kk_textures', 'kk_textures'),
                  ('green-icons', 'disabled_icons', 'disabled_icons'), ('fix-attributes', 'attributes', 'attributes'),
                  ('fix-graphics-modes', 'graphics_modes', 'graphics_modes'),
                  ('fix-requirements', 'requirements', 'requirements'), ('fix-fdf', 'fdf', 'fdf'))


def default_extras(path, opts, run):
    wanted = [x for x in DEFAULT_EXTRAS if opts.get(x[0]) is not False]
    if not wanted:
        return {}
    try:
        r = run({'task': 'reforged', 'map': path}) or {}
    except Exception as e:
        sys.stderr.write('doctor: the check that picks the default extras failed (%s): none of them runs\n' % e)
        return {}
    return dict((key, True) for _flag, found, key in wanted if ((r.get(found) or {}).get('fixable')))


def pick_extras(action, opts):
    extras = {}
    for flag, key in EXTRA_FLAGS.items():
        if opts.get(flag) is True and (action == 'fix' or flag in EDITOR_EXTRAS):
            extras[key] = True
    if action == 'fix' and opts.get('remove-game-copies') is True and not extras.get('game_overrides'):
        extras['game_overrides'] = 'identical'
    if opts.get('translation') is True:
        raise UsageError('--translation needs =<file>')
    if isinstance(opts.get('translation'), str):
        if not os.path.isfile(opts['translation']):
            raise UsageError('no such translation file: %s' % opts['translation'])
        extras['translation'] = os.path.abspath(opts['translation'])
    if isinstance(opts.get('portraits'), str) and action == 'fix':
        if opts['portraits'] not in ('stamp', 'upgrade'):
            raise UsageError('--portraits takes stamp or upgrade (or nothing)')
        extras['portraits'] = opts['portraits']
    if (opts.get('shrink-models') is True or opts.get('shrink-models-lossy') is True) and action == 'fix':
        extras['shrink_models'] = {'lossy': opts.get('shrink-models-lossy') is True}
    if isinstance(opts.get('lobby-image'), str) and action == 'fix':
        if not os.path.isfile(opts['lobby-image']):
            raise UsageError('no such picture: %s' % opts['lobby-image'])
        extras['lobby_image'] = os.path.abspath(opts['lobby-image'])
    if (opts.get('shrink') is True or opts.get('shrink-lossy') is True) and action == 'fix':
        extras['shrink'] = {'recompress': True, 'blp': True, 'dedup': True}
        if opts.get('shrink-lossy') is True:
            extras['shrink']['lossy'] = True
    return extras


class Out:
    def __init__(self, quiet):
        self.quiet = quiet
        self.err = sys.stderr
        self.tty = hasattr(self.err, 'isatty') and self.err.isatty()
        self.last = ''
        self.shown = ''
        for stream in (sys.stdout, sys.stderr):
            try:
                stream.reconfigure(encoding='utf-8', errors='replace')
            except (AttributeError, ValueError):
                pass

    def event(self, ev):
        if self.quiet or ev.get('type') != 'progress':
            return
        label = str(ev.get('label') or '').strip()
        if not label:
            return
        line = label + (' %d/%d' % (ev['done'], ev['total']) if ev.get('total') else '')
        if self.tty:
            if line == self.shown:
                return
            self.shown = line
            self.err.write('\r\x1b[2K' + line[:100])
        else:
            if label == self.last:
                return
            self.err.write(label + '\n')
        self.last = label
        self.err.flush()

    def done(self):
        if self.tty and self.last and not self.quiet:
            self.err.write('\r\x1b[2K')
            self.err.flush()
        self.last = self.shown = ''


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
    if command == 'replay list':
        for x in r.get('replays') or []:
            print('%s  %s  %d bytes' % (x.get('path'), x.get('kind'), x.get('bytes') or 0))
        return
    if command == 'replay compare':
        print(r.get('text') or r.get('error') or '')
        return
    if command in ('log', 'crash', 'replay'):
        print(r.get('text') or r.get('error') or '')
        return
    if command == 'save':
        for line in r.get('lines') or []:
            print(line)
        for p in r.get('written') or []:
            print('  ' + p)
        return
    if command == 'crash list':
        reports = r.get('reports') or []
        if not reports:
            print('No crash report in %s' % r.get('folder'))
        for x in reports:
            print('%s  %s in %s  %s' % (x.get('path'), x.get('kind'), x.get('module'), x.get('map') or ''))
        if r.get('log'):
            print('The game\'s log: %s' % r['log'])
        return
    if command in ('diag', 'fix', 'editor', 'port', 'cheat', 'qol apply', 'diagnose'):
        print_lines(r.get('lines'))
        if command in ('fix', 'editor'):
            print_changes(r.get('changes'))
        if command == 'port' and r.get('report'):
            print('\nReport: %s' % r['report'])
        return
    if command == 'check':
        game = r.get('version') or '3.0'
        print('Runs on %s? %s' % ('Reforged' if game == '3.0' else 'Warcraft III ' + game, r.get('verdict')))
        made = r.get('made_for') or {}
        if made.get('label'):
            print('Made for: %s (%s)' % (made['label'], '; '.join(made.get('reasons') or [])))
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
        if r.get('error'):
            print(r['error'])
        for f in r.get('files') or []:
            print('%10d  %-8s  %s' % (f.get('size') or 0, f.get('kind') or '', f.get('name')))
        for f in r.get('unnamed') or []:
            print('%10d  %-8s  #%s  (no name%s)' % (f.get('size') or 0, f.get('kind') or '', f.get('block'),
                                                   ', ' + f['ext'] if f.get('ext') else ''))
        hidden = r.get('hidden') or []
        for f in hidden:
            print('%10d  %-8s  %s' % (f.get('size') or 0, 'hidden', f.get('name')))
        print('%d files' % (r.get('total') or 0) + (', %d hidden (KK virtual MPQ): extract --all writes them under '
                                                      'hidden\\' % len(hidden) if hidden else ''))
        return
    if command == 'rawcodes':
        if r.get('error'):
            print(r['error'])
        sys.stdout.write(r.get('text') or '')
        return
    if command == 'recipes':
        if r.get('error'):
            print(r['error'])
        sys.stdout.write(r.get('text') or '')
        return
    if command == 'translation groups':
        if r.get('error'):
            print(r['error'])
        for g in r.get('groups') or []:
            print('%-24s %5d  %s' % (g.get('key'), g.get('count') or 0, g.get('label')))
        if r.get('script_note'):
            print(r['script_note'])
        return
    if command == 'translation export':
        if r.get('error'):
            print(r['error'])
        else:
            print('Exported %d texts to %s' % (r.get('entries') or 0, r.get('file')))
        if r.get('script_note'):
            print(r['script_note'])
        return
    if command == 'translation machine':
        if r.get('error'):
            print(r['error'])
            return
        print('Translated %d of %d texts into English (%s, from %s) in %s s: %s' % (
            r.get('translated') or 0, r.get('entries') or 0, r.get('model'), r.get('language'), r.get('seconds'),
            r.get('file')))
        if r.get('kept'):
            print('  %d of them kept from the file given with --keep' % r['kept'])
        for why, n in sorted((r.get('rejected') or {}).items()):
            print('  %d left in the original: %s' % (n, why))
        im = r.get('images') or {}
        if im:
            print(
                '  %d text(s) in images%s' % (im.get('entries') or 0, (': ' + im['error']) if im.get('error') else '')
            )
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
    if command == 'translation override':
        if r.get('state') == 'failed':
            print(r.get('error'))
            return
        if r.get('state') == 'done':
            print('Saved %d texts in %d files as: %s' % (r.get('applied') or 0, len(r.get('files') or []),
                                                          r.get('output')))
            for name in r.get('files') or []:
                print('  %s' % name)
        else:
            print('No translation can go in the archive.')
        held = {'script': 'in the script, which the map checksum covers',
                'checksum': 'in object data the map checksum covers', 'compared': 'compared by the script'}
        for why, n in sorted((r.get('held') or {}).items()):
            print('%d translated texts stay in the original: %s' % (n, held.get(why, why)))
        if r.get('rejected'):
            print('%d rejected (translation check lists them)' % len(r['rejected']))
        m = r.get('map_texts') or {}
        if m:
            print(
                'An archive can carry %d of the %d texts of this map.' % (m.get('reachable') or 0, m.get('total') or 0)
            )
        if r.get('state') == 'done':
            print('The map is not touched. A .mix loader (not made by the Doctor) must open the archive above the map '
                  '(priority 17 or more; the game opens the map at 16); while it is loaded it replaces the same files '
                  'of every map.')
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
    if command == 'extract all':
        for f in r.get('failed') or []:
            print('not written: %s (%s)' % (f.get('name'), f.get('reason')))
        for f in r.get('exists') or []:
            print('%s: a different file is already there, left as it was' % f.get('name'))
        if r.get('error'):
            print(r['error'])
            return
        print('Extracted %d of %d files to %s (%d already there, %d left as they were, %d failed).' % (
            len(r.get('written') or []), len(r.get('written') or []) + len(r.get('same') or []) +
            len(r.get('exists') or []) + len(r.get('failed') or []), r.get('out_dir'), len(r.get('same') or []),
            len(r.get('exists') or []), len(r.get('failed') or [])))
        if r.get('kind') in ('models', 'model'):
            print('%d models with %d textures and other files they need.' % (r.get('models') or 0,
                                                                             r.get('textures') or 0))
            outside = r.get('outside') or []
            if outside:
                print('%d paths the models cite are not in the file (the game has them, or they are missing):'
                      % len(outside))
                for x in outside[:40]:
                    print('  ' + x)
                if len(outside) > 40:
                    print('  ... (--json lists them all)')
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
        if r.get('ok') is False:
            print(r.get('message') or r.get('error'))
            return
        for k in ('name', 'author', 'players_suggested', 'description'):
            if r.get(k):
                print('%s: %s' % (k.replace('_', ' ').capitalize(), r[k]))
        return
    if r.get('lines'):
        print_lines(r['lines'])
        return
    print(json.dumps(r, ensure_ascii=False, indent=1, default=str))


def editor_version_flag(command, opts):
    value = opts.get('editor-version')
    if value is None or value is False:
        return None
    if command != 'editor':
        raise UsageError('--editor-version is an option of editor')
    if value is True:
        raise UsageError('--editor-version needs a value: reforged, auto, jn or 1.24 to 1.29')
    from doctor.fix import editor_version
    try:
        v = editor_version.normalize(value)
    except ValueError as e:
        raise UsageError(str(e))
    return v


def need(pos, n, what):
    if len(pos) < n:
        raise UsageError('missing %s' % what)
    for p in pos[1:2]:
        if not os.path.isfile(p):
            raise UsageError('no such %s: %s' % ('map' if what.startswith('<map') else 'file', p))


def build_job(command, pos, opts, run):
    if command == 'diag':
        need(pos, 2, '<map>')
        return 'diag', {'task': 'open', 'map': pos[1]}
    if command in ('fix', 'editor'):
        need(pos, 2, '<map>')
        version = editor_version_flag(command, opts)
        extras = pick_extras(command, opts)
        opened = run({'task': 'open', 'map': pos[1]})
        if command == 'fix':
            extras = dict(default_extras(pos[1], opts, run), **extras)
        job = {'task': command, 'map': pos[1], 'options': pick_steps(opened['steps'], command, opts),
               'extras': extras}
        if version:
            job['editor_version'] = version
        return command, job
    if command == 'port':
        need(pos, 2, '<map>')
        packages = [p for p in str(opts.get('package') or '').split(',') if p] if opts.get('package') else []
        return 'port', {'task': 'port', 'map': pos[1], 'packages': packages,
                        'memory': not opts.get('keep-memory'), 'icons': opts.get('icons') is not False,
                        'textures': opts.get('textures') is not False, 'balance': bool(opts.get('balance-numbers')),
                        'strip_indent': opts.get('strip-indent') is True,
                        'game_files': bool(opts.get('remove-game-files')), 'lossy': bool(opts.get('lossy')),
                        'classic': bool(opts.get('classic-effects')),
                        'to': opts.get('to') if isinstance(opts.get('to'), str) else ''}
    if command == 'check':
        need(pos, 2, '<map>')
        job = {'task': 'reforged', 'map': pos[1]}
        game = opts.get('game') if isinstance(opts.get('game'), str) else \
            opts.get('version') if isinstance(opts.get('version'), str) else None
        if game:
            from doctor.data import wc3_versions
            v = wc3_versions.normalize(game)
            if v is None:
                raise UsageError('unknown game version %r: %s or 3.0' % (game, ', '.join(wc3_versions.versions())))
            if v in wc3_versions.REFORGED_OLD:
                raise UsageError('check --game=%s: the check knows 3.0 and the classic games; port the map to %s '
                                 '(port <map> --to=%s) and read its report' % (game, v, v))
            if v != wc3_versions.REFORGED:
                job['version'] = v
        return 'check', job
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
                         'strip_indent': opts.get('strip-indent') is True, 'durable': opts.get('durable') is True}
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
            if opts.get('only') is True:
                raise UsageError('--only needs =<group>[,<group>...]')
            only = [x for x in str(opts['only']).split(',') if x] if isinstance(opts.get('only'), str) else None
            return 'translation export', {'task': 'translation_export', 'map': rest[1],
                                          'file': os.path.abspath(rest[2]), 'only': only,
                                          'images': opts.get('images') is True}
        if sub == 'check':
            need(rest, 3, '<map> <file>')
            return 'translation check', {'task': 'translation_check', 'map': rest[1], 'file': os.path.abspath(rest[2])}
        if sub == 'override':
            need(rest, 3, '<map> <file>')
            return 'translation override', {'task': 'translation_override', 'map': rest[1],
                                            'file': os.path.abspath(rest[2])}
        if sub == 'machine':
            need(rest, 3, '<map> <file.json>')
            if opts.get('only') is True:
                raise UsageError('--only needs =<group>[,<group>...]')
            only = [x for x in str(opts['only']).split(',') if x] if isinstance(opts.get('only'), str) else None
            quality = opts.get('quality') if isinstance(opts.get('quality'), str) else 'best'
            if quality not in ('best', 'fast'):
                raise UsageError('--quality=best or --quality=fast')
            keep = opts.get('keep')
            if keep is True:
                raise UsageError('--keep needs =<translation file>')
            if isinstance(keep, str) and not os.path.isfile(keep):
                raise UsageError('no such translation file: %s' % keep)
            return 'translation machine', {'task': 'translation_machine', 'map': rest[1],
                                           'file': os.path.abspath(rest[2]), 'only': only, 'quality': quality,
                                           'images': opts.get('images') is True,
                                           'keep': os.path.abspath(keep) if isinstance(keep, str) else None}
        raise UsageError('translation groups | export | check | override | machine')
    if command == 'files':
        need(pos, 2, '<map>')
        return 'files', {'task': 'files', 'map': pos[1]}
    if command == 'extract':
        every = opts.get('all') is True or opts.get('models') is True
        need(pos, 2 if every else 3, '<map>' if every else '<map> <name> (or --all, --models)')
        folder = os.path.abspath(opts['to']) if isinstance(opts.get('to'), str) else \
            os.path.splitext(os.path.abspath(pos[1]))[0] + ('_models' if opts.get('models') is True else '_files')
        if every:
            if len(pos) > 2:
                raise UsageError('--all and --models take no file names')
            return 'extract all', {'task': 'extract_all', 'map': pos[1], 'folder': folder,
                                   'kind': 'models' if opts.get('models') is True else None}
        return 'extract', {'task': 'extract', 'map': pos[1], 'names': pos[2:], 'folder': folder}
    if command == 'script':
        need(pos, 2, '<map>')
        return 'script', {'task': 'script', 'map': pos[1]}
    if command == 'rawcodes':
        need(pos, 2, '<map>')
        return 'rawcodes', {'task': 'rawcodes', 'map': pos[1]}
    if command == 'recipes':
        need(pos, 2, '<map>')
        if opts.get('out') is True:
            raise UsageError('--out needs a file: --out=<file.txt|.json|.csv>')
        return 'recipes', {'task': 'recipes', 'map': pos[1], 'all': opts.get('all') is True}
    if command == 'card':
        need(pos, 2, '<map>')
        return 'card', {'task': 'card', 'map': pos[1]}
    if command == 'compare':
        need(pos, 3, '<map> <other map>')
        if not os.path.isfile(pos[2]):
            raise UsageError('no such map: %s' % pos[2])
        return 'compare', {'task': 'compare', 'map': pos[1], 'other': pos[2]}
    if command == 'diagnose':
        need(pos, 2, '<map>')
        mode = 'all' if opts.get('all') is True else 'init' if opts.get('init') is True else 'entry'
        return 'diagnose', {'task': 'diag_make', 'map': pos[1], 'mode': mode}
    if command == 'replay':
        if len(pos) == 1:
            return 'replay list', {'task': 'replay_list'}
        return 'replay', {'task': 'replay_read', 'file': os.path.abspath(pos[1])}
    if command == 'save':
        need(pos, 2, '<file.w3z|file.w3v>')
        folder = os.path.abspath(opts['to']) if isinstance(opts.get('to'), str) else None
        return 'save', {'task': 'save_read', 'file': os.path.abspath(pos[1]), 'folder': folder}
    if command == 'replay-compare':
        need(pos, 3, '<a.w3g> <b.w3g>')
        return 'replay compare', {'task': 'replay_compare', 'a': os.path.abspath(pos[1]), 'b': os.path.abspath(pos[2])}
    if command == 'log':
        if len(pos) > 1:
            return 'log', {'task': 'diag_read', 'file': os.path.abspath(pos[1])}
        from doctor.fix import diagnose
        logs = diagnose.logs(1)
        if not logs:
            raise UsageError('no diagnostic log in %s: give the file' % diagnose.log_folder())
        return 'log', {'task': 'diag_read', 'file': logs[0]['path']}
    if command == 'crash':
        if len(pos) == 1:
            return 'crash list', {'task': 'crash_list'}
        mapa = opts.get('map') if isinstance(opts.get('map'), str) else None
        return 'crash', {'task': 'crash_read', 'file': os.path.abspath(pos[1]), 'map': mapa, 'check_map': bool(mapa)}
    raise UsageError('unknown command %r' % command)


JSON_SCHEMA = 1
GLOBAL_OPTIONS = {'json': {'kind': 'flag', 'about': 'print the result as one JSON object on stdout'},
                  'quiet': {'kind': 'flag', 'about': 'no progress on stderr'},
                  'help': {'kind': 'flag', 'about': 'the usage (also -h)'},
                  'version': {'kind': 'flag', 'about': 'the program version (with --json: the envelope only)'},
                  'json-schema': {'kind': 'flag', 'about': 'this contract as JSON (also the command: schema)'}}
ENVELOPE = {'schema': 'integer', 'doctor_version': 'string', 'command': 'string', 'exit_code': 'integer'}
FAILURE = {'outcome': 'string', 'error': 'string', 'error_kind': 'string'}
OUTCOMES = ('ok', 'nothing', 'partial', 'failed')
DIAG_FAILED = ('not_a_map', 'incomplete', 'cannot_read', 'unreadable')
EXIT_CODES = {'0': 'done, or nothing to do', '1': 'failed', '2': 'wrong command line', '3': 'done with leftovers',
              '130': 'cancelled'}
_WRITES = {'outcome': 'string', 'file': 'string|null', 'lines': 'array'}
_STEP_NAMES = sorted(set(STEP_FLAGS.values()) | {'data', 'identical-textures'})


def _steps():
    return dict((f, {'kind': 'step'}) for f in _STEP_NAMES)


def _flags(*names):
    return dict((n, {'kind': 'flag'}) for n in names)


def _value(about, values=None):
    v = {'kind': 'value', 'about': about}
    if values:
        v['values'] = list(values)
    return v


def _fix_options():
    o = _steps()
    o.update(_flags(*EXTRA_FLAGS))
    o.update(_flags('remove-game-copies', 'shrink', 'shrink-lossy', 'shrink-models', 'shrink-models-lossy'))
    o['portraits'] = {'kind': 'flag-or-value', 'values': ['stamp', 'upgrade']}
    o['translation'] = _value('a translation file of the map')
    o['lobby-image'] = _value('a picture')
    return o


def _editor_options():
    o = _steps()
    o.update(_flags(*[f for f in EDITOR_EXTRAS if f in EXTRA_FLAGS]))
    o['translation'] = _value('a translation file of the map')
    o['editor-version'] = _value('the World Editor to open the map in',
                                 ['reforged', 'auto', 'jn', '1.24', '1.25', '1.26', '1.27', '1.28', '1.29'])
    return o


CONTRACT = (
    ('diag', 'diag <map>', {},
     {'map': 'string', 'name': 'string', 'size': 'integer', 'lines': 'array', 'steps': 'array', 'summary': 'object',
      'editor_version': 'object', 'state': 'string|null?'}),
    ('fix', 'fix <map> [steps] [extras]', _fix_options(), dict(_WRITES, changes='object')),
    ('editor', 'editor <map> [steps] [extras] [--editor-version=<v>]', _editor_options(),
     dict(_WRITES, changes='object')),
    ('port', 'port <map> [options]',
     dict(_flags('icons', 'textures', 'keep-memory', 'balance-numbers', 'strip-indent', 'remove-game-files', 'lossy',
                 'classic-effects'),
          to=_value('a game version: 1.24a to 1.29.2, 2.0.4 (none: Reforged 3.0)'),
          package=_value('art packages, comma separated')),
     dict(_WRITES, report='string', port='object')),
    ('check', 'check <map> [--game=<version>]', {'game': _value('1.24a to 1.28.5, 1.29.2 or 3.0')},
     {'verdict': 'string', 'verdict_code': 'string', 'items': 'array', 'version': 'string',
      'made_for': 'object|null', 'versions': 'array'}),
    ('cheatpacks', 'cheatpacks <map>', {},
     {'language': 'string|null', 'script': 'string|null', 'packs': 'array', 'error': 'string|null'}),
    ('cheat', 'cheat <map> --pack=<id> [--set <key>=<value> ...]',
     dict(_flags('strip-indent', 'durable'), pack=_value('a pack id (cheatpacks lists them)'),
          set={'kind': 'repeat', 'about': '<key>=<value>'}),
     dict(_WRITES, pack='string|null')),
    ('qol', 'qol <map>', {},
     {'supported': 'boolean', 'reason': 'string|null', 'language': 'string|null', 'script': 'string|null',
      'found': 'object?'}),
    ('qol apply', 'qol <map> --xp=<x> ... (any edit given)',
     dict(dict((k, _value('a multiplier')) for k in ('xp', 'gold', 'lumber', 'drop', 'craft', 'respawn', 'creep')),
          **_flags('noshake', 'noshake-off', 'reveal', 'vip', 'strip-indent')),
     dict(_WRITES, state='string|null')),
    ('translation groups', 'translation groups <map>', {},
     {'groups': 'array', 'entries': 'integer', 'error': 'string|null'}),
    ('translation export', 'translation export <map> <file.json|file.html>',
     dict(_flags('images'), only=_value('groups, comma separated')),
     {'state': 'string|null', 'file': 'string|null', 'entries': 'integer', 'error': 'string|null'}),
    ('translation check', 'translation check <map> <file>', {},
     {'ok': 'integer', 'empty': 'integer', 'rejected': 'array', 'unknown': 'array', 'error': 'string|null'}),
    ('translation override', 'translation override <map> <file>', {},
     {'state': 'string|null', 'output': 'string|null', 'applied': 'integer', 'files': 'array', 'error': 'string|null'}),
    ('translation machine', 'translation machine <map> <file.json>',
     dict(_flags('images'), only=_value('groups, comma separated'), quality=_value('the model', ['best', 'fast']),
          keep=_value('a translation file whose filled texts stay')),
     {'state': 'string|null?', 'translated': 'integer?', 'entries': 'integer?', 'file': 'string|null?',
      'error': 'string|null?'}),
    ('files', 'files <map>', {},
     {'files': 'array', 'unnamed': 'array', 'total': 'integer', 'error': 'string|null', 'hidden': 'array?'}),
    ('extract', 'extract <map> <name>... [--to=<folder>]', {'to': _value('the folder')},
     {'out_dir': 'string', 'written': 'array', 'same': 'array', 'exists': 'array', 'failed': 'array',
      'error': 'string|null'}),
    ('extract all', 'extract <map> --all|--models [--to=<folder>]',
     dict(_flags('all', 'models'), to=_value('the folder')),
     {'out_dir': 'string', 'written': 'array', 'same': 'array', 'exists': 'array', 'failed': 'array',
      'kind': 'string|null', 'total': 'integer', 'models': 'integer', 'textures': 'integer', 'outside': 'array',
      'error': 'string|null'}),
    ('script', 'script <map> [--to=<file>]', {'to': _value('a file')},
     {'language': 'string', 'text': 'string', 'size': 'integer', 'error': 'string|null'}),
    ('rawcodes', 'rawcodes <map>', {}, {'total': 'integer', 'text': 'string', 'error': 'string|null'}),
    ('recipes', 'recipes <map> [--out=<file>] [--all]', dict(_flags('all'), out=_value('a .txt, .json or .csv file')),
     {'recipes': 'array', 'text': 'string', 'csv': 'string', 'json': 'string', 'error': 'string|null'}),
    ('card', 'card <map>', {}, {'name': 'string?', 'author': 'string?', 'players_suggested': 'string?'}),
    ('compare', 'compare <map> <other map>', {},
     {'files': 'object', 'script': 'object', 'info': 'object', 'strings': 'object', 'objects': 'object',
      'error': 'string|null'}),
    ('diagnose', 'diagnose <map> [--all|--init]', _flags('all', 'init'), dict(_WRITES)),
    ('log', 'log [<file.pld>|<folder _init>]', {}, {'text': 'string?', 'error': 'string|null?'}),
    ('crash list', 'crash', {}, {'folder': 'string', 'reports': 'array', 'log': 'string|null'}),
    ('crash', 'crash <folder|Crash.txt|War3Log.txt> [--map=<map>]', {'map': _value('a map')},
     {'text': 'string?', 'error': 'string|null?'}),
    ('replay list', 'replay', {}, {'replays': 'array'}),
    ('replay', 'replay <file.w3g|folder>', {}, {'text': 'string?', 'error': 'string|null?'}),
    ('replay compare', 'replay-compare <a.w3g> <b.w3g>', {}, {'text': 'string?'}),
    ('save', 'save <file.w3z|file.w3v> [--to=<folder>]', {'to': _value('a folder')},
     {'lines': 'array', 'ok': 'boolean', 'written': 'array'}),
)
ALIASES = {'check': {'version': 'game'}}
CONTRACT_BY_NAME = dict((c[0], c) for c in CONTRACT)


def contract(version=''):
    commands = []
    for name, usage, options, result in CONTRACT:
        x = {'command': name, 'usage': 'doctor ' + usage, 'options': options, 'result': result}
        if ALIASES.get(name):
            x['aliases'] = ALIASES[name]
        commands.append(x)
    return {'schema': JSON_SCHEMA, 'doctor_version': version, 'command': 'schema', 'exit_code': 0,
            'envelope': ENVELOPE, 'failure': FAILURE, 'outcomes': list(OUTCOMES), 'exit_codes': EXIT_CODES,
            'global_options': GLOBAL_OPTIONS,
            'refusal': {'error': 'string', 'outcome': 'string', 'no_edit': 'boolean?', 'package': 'boolean?'},
            'types': 'string, integer, number, boolean, array, object; "x|null" may be null; a trailing "?": the key '
                     'may be missing; keys not listed may appear',
            'commands': commands}


def envelope(r, version, command, code):
    from doctor.app import doctor_app
    out = doctor_app._jsonable(r) if isinstance(r, dict) else {'result': doctor_app._jsonable(r)}
    out.update(schema=JSON_SCHEMA, doctor_version=version, command=command, exit_code=code)
    return out


def failure(version, command, error, kind, code):
    return {'schema': JSON_SCHEMA, 'doctor_version': version, 'command': command, 'exit_code': code,
            'outcome': 'failed', 'error': error, 'error_kind': kind}


_MISSING = object()


def print_json(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=1))


def allowed_options(command):
    spec = CONTRACT_BY_NAME.get(command)
    return set(spec[2] if spec else ()) | set(ALIASES.get(command) or ()) | set(GLOBAL_OPTIONS)


def outcome_code(command, r):
    if 'outcome' in (r or {}):
        return OUTCOME_CODE.get(r['outcome'], 1)
    if (r or {}).get('error') or (r or {}).get('state') == 'failed':
        return 1
    if command == 'diag' and (r or {}).get('state') in DIAG_FAILED:
        return 1
    if command == 'check' and (r or {}).get('verdict') == 'no':
        return 1
    return 0


def save_text(path, text, newline='\n'):
    path = os.path.abspath(path)
    part = path + '.part'
    try:
        with open(part, 'w', encoding='utf-8', newline=newline) as f:
            f.write(text)
        os.replace(part, path)
    except BaseException:
        try:
            os.remove(part)
        except OSError:
            pass
        raise
    return path


def save_output(command, r, opts):
    if (r or {}).get('error'):
        return None
    if command == 'recipes' and isinstance(opts.get('out'), str):
        low = opts['out'].lower()
        data = r.get('json') if low.endswith('.json') else r.get('csv') if low.endswith('.csv') else r.get('text')
        return save_text(opts['out'], data or '', newline='')
    if command == 'script' and isinstance(opts.get('to'), str) and r.get('text'):
        return save_text(opts['to'], r['text'], newline='\r\n' if r.get('line_endings') == 'crlf' else '\n')
    return None


def script_notes(r, saved):
    if r.get('note'):
        sys.stderr.write('doctor: %s\n' % r['note'])
    if r.get('truncated'):
        sys.stderr.write(
            'doctor: the script has %d bytes and only its first part was %s; extract <map> %s writes it '
            'whole\n' % (r.get('size') or 0, 'saved' if saved else 'printed', r.get('name') or 'war3map.j')
        )


def main(argv, window, version=''):
    from doctor.app import doctor_app
    from doctor.app import windows_rules
    windows_rules.apply()
    argv = list(argv)
    try:
        pos, opts = parse(argv)
    except UsageError as e:
        sys.stderr.write('doctor: %s\n' % e)
        if '--json' in argv:
            print_json(failure(version, '', str(e), 'usage', 2))
        return 2
    as_json = bool(opts.get('json'))
    if opts.get('json-schema') is True or (pos and pos[0] == 'schema'):
        print_json(contract(version))
        return 0
    if opts.get('version') is True or (opts.get('version') and not (pos and pos[0] == 'check')):
        if as_json:
            print_json({'schema': JSON_SCHEMA, 'doctor_version': version, 'command': 'version', 'exit_code': 0})
        else:
            print(version)
        return 0
    if opts.get('help') or not pos:
        sys.stdout.write(USAGE.replace('{version}', version))
        return 0 if opts.get('help') else 2
    asked = ' '.join(pos[:2]) if pos[0] == 'translation' and len(pos) > 1 else pos[0]
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

    def stopped(e, name):
        if isinstance(e, KeyboardInterrupt):
            sys.stderr.write('doctor: cancelled\n')
            if as_json:
                print_json(failure(version, name, 'cancelled', 'cancelled', 130))
            return 130
        sys.stderr.write('doctor: %s failed: %s: %s\n' % (pos[0], type(e).__name__, e))
        if os.environ.get('DOCTOR_TRACE'):
            raise e
        if as_json:
            print_json(failure(version, name, '%s: %s' % (type(e).__name__, e), 'exception', 1))
        return 1

    try:
        command, job = build_job(pos[0], pos, opts, run)
        asked = command
        allowed = allowed_options(command)
        unknown = sorted(k for k in opts if k not in GLOBAL_OPTIONS and (
            k not in allowed or (k not in opts.seen and k not in ('out', 'to'))))
        if unknown:
            named = ', '.join('--' + k for k in unknown)
            if command in ('fix', 'editor'):
                sys.stderr.write('doctor: not used (no such step or extra for this map, or a typo): %s\n' % named)
            else:
                raise UsageError('unknown option%s: %s' % ('s' if len(unknown) > 1 else '', named))
    except UsageError as e:
        sys.stderr.write('doctor: %s\n(doctor --help lists the commands)\n' % e)
        if as_json:
            print_json(failure(version, asked, str(e), 'usage', 2))
        return 2
    except (KeyboardInterrupt, Exception) as e:
        return stopped(e, asked)
    t0 = time.time()
    try:
        r = run(job)
    except (KeyboardInterrupt, Exception) as e:
        return stopped(e, command)
    refused = (r or {}).get('package') or (r or {}).get('no_edit')
    try:
        saved = None if refused else save_output(command, r, opts)
    except OSError as e:
        message = 'cannot write %s: %s' % (os.path.abspath(opts['out' if command == 'recipes' else 'to']),
                                           e.strerror or e)
        sys.stderr.write('doctor: %s\n' % message)
        if as_json:
            print_json(failure(version, command, message, 'exception', 1))
        return 1
    if command == 'script' and not as_json and not refused:
        script_notes(r, saved)
    if as_json:
        result = envelope(r, version, command, outcome_code(command, r))
        if saved:
            result['saved'] = saved
        print_json(result)
    elif refused:
        print(r.get('error'))
    elif command == 'recipes' and saved:
        print('%d recipes saved as: %s' % (len(r.get('recipes') or []), saved))
    elif command == 'script' and saved:
        print('Saved as: %s' % saved)
    elif command == 'script':
        if not isinstance(opts.get('to'), str):
            sys.stdout.write(r.get('text') or '')
        if r.get('error'):
            print(r['error'])
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
        try:
            os.remove(dst + '.new')
        except OSError:
            pass
