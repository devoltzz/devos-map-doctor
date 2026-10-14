# Reads the game's crash report and log: the module it closed in, the models it could not create, the interface frames it refused.
import collections
import os
import re



FRAME_NAME_MAX = 62
RX_TAG = re.compile(r'^<([\w.]+)>(.*)$')
RX_ADDR = re.compile(r'DBG-ADDR<([0-9A-Fa-f]+)>\("([^"]*)"\)')
RX_SUMMARY = re.compile(r'^(\w+) \((.*?)\)')
RX_LOGLINE = re.compile(r'^\d+/\d+ \d+:\d+:\d+\.\d+\s+(.*)$')
RX_FDF_LONG = re.compile(r'^\(([^)]*?)//(\d+)\) Error, framename "([^"]*)" is too long!')
RX_FRAME_DUP = re.compile(r'Error, frame "([^"]*)" already encountered!')
RX_MODEL = re.compile(r'^model creation failed - (.*)$')
RX_LEVEL = re.compile(r'^\[Out of Bound Level\] Unit: (.*?), level: (\d+), maxLevel: (\d+)')
RX_MAP = re.compile(r'^(?:Opening map|Played) - ?(.*)$|^Played (.*)$')
RX_DESYNC = re.compile(r'Network desync on turn (\d+) in game ([^\r\n]+)')
RX_DESYNC_BLOCK = re.compile(r'\[Desync - (\d+) - Turn\((\d+)\) = (\d+)\]')
RX_DESYNC_ENTRY = re.compile(r'#(\d+)#:\s*(0x[0-9A-Fa-f]+)')
RX_C_BUILD = re.compile(r'Warcraft III\s*\(build\s*(\d+)\)', re.I)
RX_C_INSTR = re.compile(r"The instruction at\s+'?0x([0-9A-Fa-f]+)'?\s+referenced memory at\s+'?0x([0-9A-Fa-f]+)'?"
                        r"(?:\.\s*The memory could not be\s+'?(\w+)'?)?", re.I)
RX_C_KIND = re.compile(r'\b(EXCEPTION_[A-Z_]+|[A-Z_]*ACCESS_VIOLATION|STACK_OVERFLOW|INT_DIVIDE_BY_ZERO|'
                       r'ILLEGAL_INSTRUCTION|PRIV_INSTRUCTION)\b')
RX_C_GAMEDLL = re.compile(r'0x([0-9A-Fa-f]+)(?:[^\n]*?0x([0-9A-Fa-f]+))?[^\n]*?:[^\n]*?Game\.dll', re.I)
RX_C_REG = re.compile(r'\b(E?[A-D]X|E?SI|E?DI|E?BP|E?SP|EIP|EFLAGS)\s*[=:]\s*(?:0x)?([0-9A-Fa-f]{8})\b')
RX_C_DUMP = re.compile(r'^\s*(?:0x)?([0-9A-Fa-f]{4,8}):?\s+((?:[0-9A-Fa-f]{2}\s+){15}[0-9A-Fa-f]{2})\b')
GAME_DLL_BASE = 0x6F000000
GAME_DLL_SIZE = 0xBB5000


def _documents():
    from doctor.fix import diagnose
    return diagnose.documents()


def errors_folder():
    return os.path.join(_documents(), 'Warcraft III', 'Errors')


def current_log():
    return os.path.join(_documents(), 'Warcraft III', 'Logs', 'War3Log.txt')


def _read_text(p):
    with open(p, 'rb') as f:
        return f.read().decode('utf-8', 'replace')


def _desync_files(p):
    return [f for f in os.listdir(p) if f.lower() == 'desync.txt' or f.lower().endswith('_desync.log')]


def folders(limit=20):
    base = errors_folder()
    out = []
    if not os.path.isdir(base):
        return out
    for d in os.listdir(base):
        p = os.path.join(base, d)
        if not os.path.isdir(p):
            continue
        crash = os.path.join(p, 'Crash.txt')
        if os.path.isfile(crash):
            out.append({'path': p, 'name': d, 'type': 'crash', 'modified': os.path.getmtime(crash)})
            continue
        try:
            ds = _desync_files(p)
        except OSError:
            continue
        if ds:
            out.append({'path': p, 'name': d, 'type': 'desync',
                        'modified': max(os.path.getmtime(os.path.join(p, f)) for f in ds)})
    out.sort(key=lambda x: -x['modified'])
    out = out[:limit]
    for x in out:
        x['replay'] = os.path.isfile(os.path.join(x['path'], 'TempReplay.w3g'))
        if x['type'] == 'crash':
            try:
                c = parse_crash(_read_text(os.path.join(x['path'], 'Crash.txt')))
                x['kind'] = c['exception'].get('kind')
                x['module'] = c['exception'].get('module')
            except OSError:
                pass
        else:
            x['kind'] = 'NETWORK_DESYNC'
            try:
                dt = os.path.join(x['path'], 'Desync.txt')
                if os.path.isfile(dt):
                    x['turn'] = (parse_desync(_read_text(dt)) or {}).get('turn')
            except OSError:
                pass
        lp = os.path.join(x['path'], 'War3Log.txt')
        if os.path.isfile(lp):
            try:
                x['map'] = parse_log(_read_text(lp))['map']
            except OSError:
                pass
    return out


def parse_crash(t):
    if '<Exception.Summary:>' not in t and ('The instruction at' in t or RX_C_BUILD.search(t)):
        return _classic_as_crash(parse_classic(t), t)
    out = {'build': None, 'exception': {}, 'memory': {}, 'stack': []}
    lines = t.splitlines()
    block = None
    for l in lines:
        s = l.strip()
        if s == '<Exception.Summary:>':
            block = 'summary'
            continue
        if s == '<Exception.Assertion:>':
            block = 'stack'
            continue
        if s.startswith('<:'):
            block = None
            continue
        if block == 'summary' and s:
            m = RX_SUMMARY.match(s)
            if m:
                out['exception'].update(kind=m.group(1), what=m.group(2))
            mods = [x[1] for x in RX_ADDR.findall(s)]
            if mods:
                out['exception']['module'] = mods[0] or '(no module)'
            continue
        if block == 'stack':
            for _a, mod in RX_ADDR.findall(s):
                out['stack'].append(mod or '(no module)')
            continue
        m = RX_TAG.match(s)
        if m:
            k, v = m.group(1), m.group(2).strip()
            if k == 'Exception.BuildNumber':
                out['build'] = v
            elif k.startswith('Mem.'):
                mm = re.match(r'(\d+)\s*MB', v)
                if mm:
                    out['memory'][k[4:]] = int(mm.group(1))
    seen = []
    for m in out['stack']:
        if not seen or seen[-1] != m:
            seen.append(m)
    out['exception']['modules'] = seen[:12]
    return out


def _build_patch(build):
    try:
        import json
        with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ref',
                               'game_builds.json'), encoding='utf-8') as f:
            for row in json.load(f)['builds']:
                if row[3].rsplit('.', 1)[-1] == str(build):
                    return '%s (%s)' % (row[3], row[2].replace('v', '').replace('_', '.'))
    except (OSError, ValueError, KeyError, IndexError):
        pass
    return None


def parse_classic(t):
    out = {'build': None, 'patch': None, 'kind': None, 'instruction': None, 'memory': None, 'access': None,
           'game_dll': None, 'fault_rva': None, 'fault_in_game_dll': None, 'registers': [], 'stack': [], 'rvas': []}
    m = RX_C_BUILD.search(t)
    if m:
        out['build'] = m.group(1)
        out['patch'] = _build_patch(m.group(1))
    m = RX_C_KIND.search(t)
    if m:
        out['kind'] = m.group(1)
    m = RX_C_INSTR.search(t)
    if m:
        out['instruction'] = int(m.group(1), 16)
        out['memory'] = int(m.group(2), 16)
        out['access'] = (m.group(3) or '').lower() or None
    base, size, assumed = GAME_DLL_BASE, GAME_DLL_SIZE, True
    m = RX_C_GAMEDLL.search(t)
    if m:
        base = int(m.group(1), 16)
        assumed = True
        if m.group(2):
            second = int(m.group(2), 16)
            if second > base:
                size, assumed = second - base, False
            elif 0 < second < 0x4000000:
                size, assumed = second, False
    out['game_dll'] = {'base': base, 'size': size, 'size_assumed': assumed, 'found': bool(m)}

    def rva(v):
        return v - base if base + 0x1000 <= v < base + size else None

    if out['instruction'] is not None:
        out['fault_rva'] = rva(out['instruction'])
        out['fault_in_game_dll'] = out['fault_rva'] is not None
    skip = False
    seen = set()
    for l in t.splitlines():
        if 'Loaded Modules' in l:
            skip = True
        if skip:
            if 'Memory Dump' in l:
                skip = False
            continue
        for name, val in RX_C_REG.findall(l):
            v = int(val, 16)
            r = rva(v)
            if r is not None:
                out['registers'].append((name, v, r))
                seen.add(r)
        dm = RX_C_DUMP.match(l)
        if dm:
            addr = int(dm.group(1), 16)
            raw = bytes.fromhex(dm.group(2).replace(' ', '').replace('\t', ''))
            for i in range(0, 16, 4):
                v = int.from_bytes(raw[i:i + 4], 'little')
                r = rva(v)
                if r is not None:
                    out['stack'].append((addr + i, v, r))
                    seen.add(r)
    order = []
    for _a, _v, r in out['stack']:
        if r not in order:
            order.append(r)
    out['rvas'] = order
    return out


def _classic_as_crash(c, t):
    mod = None
    if c['fault_in_game_dll']:
        mod = 'Game.dll'
    elif c['instruction'] is not None:
        mod = '(not Game.dll)'
    what = ''
    if c['instruction'] is not None:
        what = 'instruction 0x%08X%s' % (c['instruction'], ' = Game.dll+0x%X' % c['fault_rva'] if c['fault_in_game_dll']
                                         else '')
        if c['memory'] is not None:
            what += ', memory 0x%08X%s' % (c['memory'], ' (%s)' % c['access'] if c['access'] else '')
    return {'build': c['build'], 'exception': {'kind': c['kind'] or 'EXCEPTION', 'what': what, 'module': mod,
                                               'modules': ['Game.dll'] if c['fault_in_game_dll'] else []},
            'memory': {}, 'stack': [], 'classic': c}


def parse_desync(t):
    m = RX_DESYNC.search(t)
    if not m:
        return None

    def tag(key):
        mm = re.search(r'<' + re.escape(key) + r'>\s*([^\r\n]+)', t)
        return mm.group(1).strip() if mm else None

    return {'turn': int(m.group(1)), 'game': m.group(2).strip(), 'map': tag('Map'), 'map_hash': tag('MapHash'),
            'build': tag('Exception.BuildNumber')}


def _tag_name(n):
    try:
        return n.to_bytes(4, 'big').decode('ascii')
    except (OverflowError, UnicodeDecodeError):
        return str(n)


def parse_desync_log(t):
    heads = list(RX_DESYNC_BLOCK.finditer(t))
    out = {}
    for i, h in enumerate(heads):
        body = t[h.end():heads[i + 1].start() if i + 1 < len(heads) else len(t)]
        out.setdefault(int(h.group(2)), []).append(
            {'tag': _tag_name(int(h.group(1))), 'value': int(h.group(3)),
             'entries': dict((int(k), v) for k, v in RX_DESYNC_ENTRY.findall(body))})
    return out


def compare_desync(a, b, limit=8):
    pa = parse_desync_log(_read_text(a)) if isinstance(a, str) else a
    pb = parse_desync_log(_read_text(b)) if isinstance(b, str) else b
    common = sorted(set(pa) & set(pb))
    diffs = []
    for turn in common:
        xa, xb = pa[turn], pb[turn]
        if len(xa) != len(xb) or [x['tag'] for x in xa] != [x['tag'] for x in xb]:
            continue
        for x, y in zip(xa, xb):
            if x['value'] == y['value'] and x['entries'] == y['entries']:
                continue
            ks = sorted(set(x['entries']) | set(y['entries']))
            ent = [{'index': k, 'a': x['entries'].get(k), 'b': y['entries'].get(k)} for k in ks
                   if x['entries'].get(k) != y['entries'].get(k)]
            diffs.append({'turn': turn, 'tag': x['tag'], 'a': x['value'], 'b': y['value'], 'entries': ent[:limit]})
    if not common:
        txt = 'The two logs have no turn in common (not the same game, or the logs cover different turns).'
    elif not diffs:
        txt = 'The %d turn(s) both logs have are identical.' % len(common)
    else:
        first = diffs[0]
        txt = ('The first difference: turn %d, category "%s" (%d against %d)%s.' % (
            first['turn'], first['tag'], first['a'], first['b'],
            '; entries ' + ', '.join('#%d %s/%s' % (e['index'], e['a'], e['b']) for e in first['entries'][:4])
            if first['entries'] else ''))
    return {'turns': common, 'differences': diffs, 'text': txt}


def parse_log(t):
    out = {'map': None, 'maps': [], 'models': collections.Counter(), 'frames_long': {},
           'frames_dup': collections.Counter(), 'levels': {}}
    for raw in t.splitlines():
        m = RX_LOGLINE.match(raw)
        l = (m.group(1) if m else raw).strip()
        if not l:
            continue
        mm = RX_MAP.match(l)
        if mm:
            p = (mm.group(1) or mm.group(2) or '').strip()
            if p and not p.startswith('Maps/') and ':' in p[:3]:
                out['map'] = p
                if p not in out['maps']:
                    out['maps'].append(p)
            continue
        mm = RX_MODEL.match(l)
        if mm:
            out['models'][mm.group(1).strip()] += 1
            continue
        mm = RX_FDF_LONG.match(l)
        if mm:
            out['frames_long'].setdefault(mm.group(3), (mm.group(1), int(mm.group(2))))
            continue
        mm = RX_FRAME_DUP.search(l)
        if mm:
            out['frames_dup'][mm.group(1)] += 1
            continue
        mm = RX_LEVEL.match(l)
        if mm:
            out['levels'][mm.group(1)] = (int(mm.group(2)), int(mm.group(3)))
    return out


def game_overrides(map_path, limit=30):
    from doctor.port import game_files
    try:
        names = game_files.shadowed(map_path)
    except Exception:
        return None
    return {'count': len(names), 'folders': game_files.count_by_folder(names), 'sample': list(names)[:limit]}


def read(path, map_path=None):
    out = {'path': path, 'crash': None, 'log': None, 'desync': None, 'replay': None, 'overrides': None,
           'findings': [], 'error': None}
    crash_txt = log_txt = desync_txt = replay = None
    folder = None
    if os.path.isdir(path):
        folder = path
        crash_txt = os.path.join(path, 'Crash.txt')
        log_txt = os.path.join(path, 'War3Log.txt')
        desync_txt = os.path.join(path, 'Desync.txt')
    elif os.path.basename(path).lower() == 'crash.txt':
        folder = os.path.dirname(path)
        crash_txt = path
        log_txt = os.path.join(folder, 'War3Log.txt')
        desync_txt = os.path.join(folder, 'Desync.txt')
    elif os.path.basename(path).lower() == 'desync.txt' or path.lower().endswith('_desync.log'):
        folder = os.path.dirname(path)
        desync_txt = path if path.lower().endswith('.txt') else os.path.join(folder, 'Desync.txt')
        log_txt = os.path.join(folder, 'War3Log.txt')
    else:
        log_txt = path
    if folder and os.path.isfile(os.path.join(folder, 'TempReplay.w3g')):
        replay = os.path.join(folder, 'TempReplay.w3g')
    try:
        if crash_txt and os.path.isfile(crash_txt):
            out['crash'] = parse_crash(_read_text(crash_txt))
        if log_txt and os.path.isfile(log_txt):
            out['log'] = parse_log(_read_text(log_txt))
        if desync_txt and os.path.isfile(desync_txt):
            out['desync'] = parse_desync(_read_text(desync_txt))
        if folder:
            logs = [f for f in os.listdir(folder) if f.lower().endswith('_desync.log')]
            if logs and out['desync'] is None:
                out['desync'] = {'turn': None, 'game': None, 'map': None, 'map_hash': None, 'build': None}
            if logs and out['desync'] is not None:
                out['desync']['logs'] = sorted(logs)
                t = parse_desync_log(_read_text(os.path.join(folder, logs[0])))
                out['desync']['turns'] = sorted(t)
                out['desync']['tags'] = sorted(set(b['tag'] for v in t.values() for b in v))
    except OSError as e:
        out['error'] = 'The report could not be read: %s' % e
        return out
    if replay:
        try:
            from doctor.fix import replay_read
            rr = replay_read.read(replay)
            if not rr.get('error'):
                out['replay'] = rr
        except Exception:
            pass
    if not out['crash'] and not out['log'] and not out['desync']:
        out['error'] = 'Neither a Crash.txt, a Desync.txt nor a War3Log.txt was found there.'
        return out
    ex = (out['crash'] or {}).get('exception') or {}
    if ex.get('module', '').lower() == 'clientsdk.dll' and map_path and os.path.isfile(map_path):
        out['overrides'] = game_overrides(map_path)
    out['findings'] = _findings(out)
    return out


def _mmss(ms):
    s = int((ms or 0) // 1000)
    return '%d:%02d' % (s // 60, s % 60)


def _classic_findings(c):
    k = c['classic']
    f = []
    where = ('Game.dll+0x%X' % k['fault_rva'] if k['fault_in_game_dll'] else
             ('0x%08X (not inside Game.dll: another module, or the report has no Game.dll range)' % k['instruction']
              if k['instruction'] is not None else 'an unknown place'))
    acc = ''
    if k['memory'] is not None:
        acc = ', %s address 0x%08X%s' % ({'read': 'reading', 'written': 'writing', 'write': 'writing'}.get(
            k['access'], k['access'] or 'accessing'), k['memory'],
                                         ' (a null pointer or close to it)' if k['memory'] < 0x10000 else '')
    f.append(('bad', 'The game closed: %s at %s%s.' % (k['kind'] or 'exception', where, acc)))
    f.append(('muted', 'Game version: build %s%s.' % (k['build'] or '?',
                                                      ' = %s' % k['patch'] if k['patch'] else '')))
    if k['instruction'] is None:
        f.append(
            (
                'warn',
                'The line that starts with "The instruction at" was not found: this is not the classic report layout the '
                'reader knows, so only the build was read.',
            )
        )
    g = k['game_dll']
    if not g['found']:
        f.append(('muted', 'Game.dll is not in the module list: its base is assumed to be 0x%08X.' % g['base']))
    elif g['size_assumed']:
        f.append(('muted', 'Game.dll\'s size is not in the report: 0x%X is assumed (the size of the 1.26a image).'
                  % g['size']))
    if k['rvas']:
        f.append(('muted', 'Code addresses found on the stack (the memory dump read as 32-bit words, nearest first; '
                           'some are old): %s. The Doctor has no table of Game.dll functions: compare these offsets '
                           'with the community\'s lists of the same build.' % ', '.join(
                               'Game.dll+0x%X' % x for x in k['rvas'][:10])))
    elif k['registers']:
        f.append(('muted', 'Code addresses in the registers: %s.' % ', '.join(
            '%s=Game.dll+0x%X' % (n, x) for n, _v, x in k['registers'][:6])))
    return f


def _findings(r):
    f = []
    c, lg = r['crash'], r['log']
    if lg and lg.get('map'):
        f.append(('muted', 'The map: %s' % lg['map']))
    d = r.get('desync')
    if d:
        if d.get('turn') is not None:
            f.append(('bad', 'Network desync on turn %d%s: this machine\'s game state stopped matching another '
                             'machine\'s.' % (d['turn'], ' (game "%s")' % d['game'] if d.get('game') else '')))
        else:
            f.append(('bad', 'The folder holds a desync log but no Desync.txt.'))
        if d.get('tags'):
            f.append(('muted', 'The log covers turn(s) %s; categories: %s. One machine\'s file only says what changed '
                               'there: keep the files of ALL the machines of the game and compare them '
                               '(`crash_report.py compare a_Desync.log b_Desync.log`).' % (
                                   ', '.join(str(x) for x in d['turns'][:6]), ', '.join(d['tags']))))
        if d.get('map'):
            f.append(
                ('muted', 'The map: %s%s.' % (d['map'], ' (hash %s)' % d['map_hash'] if d.get('map_hash') else ''))
            )
    if c and c.get('classic'):
        f += _classic_findings(c)
    elif c:
        ex = c['exception']
        mod = ex.get('module') or '?'
        f.append(('bad', 'The game closed: %s in %s (%s).' % (ex.get('kind', '?'), mod, ex.get('what', '')[:160])))
        if mod.lower() == 'clientsdk.dll':
            ov = r.get('overrides')
            tail = ''
            if ov is not None:
                tail = (' The open map carries %d file(s) at the game\'s own paths (%s): port it again with "Remove '
                        'the game\'s own files" (or remove them) and test again.'
                        % (ov['count'], ', '.join('%s %d' % kv for kv in ov['folders'][:4]))
                        if ov['count'] else ' The open map carries no file at the game\'s own paths, so the cause is '
                                            'another one.')
            f.append(('warn', 'A crash in ClientSdk.dll on the main thread was caused, in a measured case, by the map '
                              'carrying the game\'s own textures and icons at the game\'s paths (they replace '
                              'Reforged\'s).' + tail))
        elif ex.get('kind') == 'ACCESS_VIOLATION' and 'execute address' in ex.get('what', '') and mod == '(no module)':
            f.append(
                (
                    'warn',
                    'The game jumped to an address no code lives at: memory was probably corrupted before. Make a '
                    'diagnostic copy of the map to see what it was doing a second before the crash.',
                )
            )
        else:
            f.append(('muted', 'The modules on the stack: %s.' % ', '.join(ex.get('modules') or [])))
        mem = c.get('memory') or {}
        if mem.get('Committed', 0) > 12000:
            f.append(('warn', 'The game had %d MB committed: the map may run out of memory.' % mem['Committed']))
    rp = r.get('replay')
    if rp:
        f.append(('muted', 'The game saved the players\' actions in TempReplay.w3g (%d turns, %s of game time): '
                           'open it with the replay reader.' % (rp['turns'], _mmss(rp['stats'].get('last_turn_ms')))))
        f += [x for x in rp['findings'] if x[0] == 'warn' or x[1].startswith('The game closed')]
    if lg:
        empties = ('', '.mdl.mdl', '.mdl', '.mdx')
        bad = [(p, n) for p, n in lg['models'].most_common() if p not in empties]
        empty = sum(lg['models'].get(p, 0) for p in empties)
        if bad:
            f.append(('warn', '%d model(s) could not be created (%d times): %s.' % (
                len(bad), sum(n for _p, n in bad), ', '.join('%s (%d)' % (p[:80], n) for p, n in bad[:6]))))
        if empty:
            f.append(('muted', '%d effect(s) or unit(s) asked for an EMPTY model path (shown as ".mdl.mdl"): a model '
                               'field or a script string with no model.' % empty))
        if lg['frames_long']:
            files = collections.Counter(v[0] for v in lg['frames_long'].values())
            f.append(('bad', '%d interface frame(s) were not created: their names are longer than %d characters '
                             '(in %s). Code that uses them gets nothing.' % (
                                 len(lg['frames_long']), FRAME_NAME_MAX,
                                 ', '.join('%s (%d)' % kv for kv in files.most_common(4)))))
        if lg['frames_dup']:
            f.append(('muted', '%d interface frame(s) are defined twice (the first definition stays).'
                      % len(lg['frames_dup'])))
        if lg['levels']:
            f.append(('muted', '%d unit(s) were set above their maximum level: %s.' % (
                len(lg['levels']), ', '.join('%s %d/%d' % (u, a, b) for u, (a, b) in list(lg['levels'].items())[:4]))))
    if not f:
        f.append(('ok', 'Nothing the Doctor knows was found.'))
    return f


def text(r):
    if r.get('error'):
        return r['error']
    out = ['Crash report: %s' % r['path']]
    out += ['- ' + t for _s, t in r['findings']]
    lg = r.get('log') or {}
    if lg.get('frames_long'):
        out.append('Frames with names that are too long (file:line name):')
        out += ['  %s:%d %s' % (v[0], v[1], k) for k, v in list(lg['frames_long'].items())[:30]]
    ov = r.get('overrides') or {}
    if ov.get('sample'):
        out.append('Files at the game\'s own paths (a sample):')
        out += ['  ' + s for s in ov['sample']]
    return '\n'.join(out)
