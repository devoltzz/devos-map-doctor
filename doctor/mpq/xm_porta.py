# The xmload map family in the port: the unpacked pack, the real script and the runtime.
import os
import re


ACTIVE = {}
ENGINE_NOTES = (
    'this map runs on the xmload engine: its game logic is ported and its frame interface is drawn on '
    'Reforged frames; the parts made with cocos2d-x inside its DLL (Cocos* natives) are not drawn',
    'the server of this map is answered on this computer as if it were there: progress is saved locally '
    '(rankings and online rewards stay empty)',
    'the natives of its DLL listed as stubs below are in part answered at run time by the runtime of this engine '
    '(the bridge between JASS and Lua, lists, big numbers, object data, unit enumeration)',
)


def ui_flags():
    if not ACTIVE:
        return {}
    return {'KK_UI_LARGA': 'true', 'KK_UI_MOUSE_POS': 'true', 'KK_UI_PAI': 'true'}


def _runtime():
    import glob
    from doctor.port import ydwe_port
    main = ydwe_port._route_data('ydwe', 'xmload.lua')
    parts = []
    for p in sorted(glob.glob(os.path.join(os.path.dirname(main), 'xmload_nat_*.lua'))) + [main]:
        with open(p, 'rb') as f:
            parts.append(f.read().rstrip(b'\r\n') + b'\n')
    return b''.join(parts)


def _modules(archive):
    from doctor.mpq import xm_pkg
    out = {}
    for name, data in xm_pkg.entries(archive):
        if not name.lower().endswith('.lua'):
            continue
        short = name[8:] if name.lower().startswith('scripts\\') else name
        out[short] = {'block_entry': 100000 + len(out), 'data_bytes': data, 'forma': 'bytecode', 'origin': 'pkg'}
    return out


DATA_EXT = (b'xmui', b'txt', b'json', b'ini', b'lni', b'xml', b'csv', b'cfg', b'dat')
DATA_FILE_MAX = 4 << 20
DATA_TOTAL_MAX = 32 << 20


def _data_files(archive, texts):
    pat = re.compile(rb'[\w\-./\\ ]{1,160}\.(?:' + b'|'.join(DATA_EXT) + rb')(?![\w])', re.I)
    names = set()
    bare = re.compile(rb'"\.(' + b'|'.join(DATA_EXT) + rb')"', re.I)
    literal = re.compile(rb'"([\w\-./\\]{1,40})"')
    for t in texts:
        for m in pat.finditer(t):
            n = m.group(0).strip().replace(b'\\\\', b'\\').replace(b'/', b'\\').lstrip(b'\\')
            if n:
                names.add(n.decode('utf-8', 'surrogateescape'))
        for m in bare.finditer(t):
            a, b = t.rfind(b'\n', 0, m.start()) + 1, t.find(b'\n', m.end())
            line = t[a:b if b >= 0 else len(t)]
            ext = m.group(1).decode('ascii')
            for lit in literal.findall(line):
                s = lit.decode('utf-8', 'surrogateescape').replace('\\\\', '\\')
                if s.startswith('.'):
                    continue
                names.add('%s.%s' % (s, ext))
                names.update('%s%d.%s' % (s, k, ext) for k in range(33))
    out, total = {}, 0
    for n in sorted(names):
        if n.lower().startswith('war3map'):
            continue
        try:
            if not archive.find(n):
                continue
            d = archive.read(n)
        except Exception:
            continue
        if d and len(d) <= DATA_FILE_MAX and total + len(d) <= DATA_TOTAL_MAX:
            out[n] = d
            total += len(d)
    return out


def _natives(script):
    text = script.decode('utf-8', 'surrogateescape') if isinstance(script, bytes) else script
    return sorted(
        set(re.findall(r'^[ \t]*(?:constant[ \t]+)?native[ \t]+(\w*XM\w*|ExecuteLuaFunc\w*)[ \t]', text, re.M))
    )


def prepare_map_copy(map_path, work, log=print):
    from doctor.mpq import mpqread
    from doctor.mpq import xm_jx
    from doctor.mpq import xm_pkg
    ACTIVE.clear()
    archive = mpqread.Archive(map_path)
    if not xm_pkg.opens(archive):
        return _prepare_loose(map_path, archive, work, log)
    base = os.path.join(work, 'xm_base.w3x')
    r = xm_pkg.unpack_to_map(map_path, base, False, log=lambda s: None, real_script=True)
    script = xm_jx.map_script(archive.read('war3map.jx'), archive.read('war3map.j'))
    ACTIVE['modules'] = _modules(archive)
    ACTIVE['natives'] = _natives(script)
    ACTIVE['files'] = _data_files(
        mpqread.Archive(base), [script] + [m['data_bytes'] for m in ACTIVE['modules'].values()]
    )
    log(
        '0b. xmload map: %d files unpacked from game.pkg, the real script (%d B) back from war3map.jx'
        % (r['files'], len(script))
    )
    return base


def _prepare_loose(map_path, archive, work, log):
    from doctor.mpq import xm_jx
    from doctor.mpq import xm_pkg
    if not xm_pkg.opens_loose(archive):
        return None
    base = os.path.join(work, 'xm_base.w3x')
    try:
        r = xm_pkg.loose_to_map(map_path, base, log=lambda s: None, real_script=True)
        script = xm_jx.map_script(archive.read('war3map.jx'), archive.read('war3map.j'))
    except (xm_pkg.PackError, xm_jx.JxError) as e:
        log('0b. xmload map, loose form: not opened (%s)' % e)
        if os.path.isfile(base):
            os.remove(base)
        return None
    modules = {}
    for name in sorted(r['lua']):
        modules[name] = {
            'block_entry': 100000 + len(modules),
            'data_bytes': r['lua'][name],
            'forma': 'bytecode',
            'origin': 'pkg',
        }
    ACTIVE['modules'] = modules
    ACTIVE['natives'] = _natives(script)
    ACTIVE['files'] = _data_files(archive, [script] + [m['data_bytes'] for m in modules.values()])
    log('0b. xmload map, loose form (no game.pkg): %d files opened in the MPQ (%s), %d Lua modules, the real script '
        '(%d B) back from war3map.jx' % (r['files'], ', '.join('%s %d' % kv for kv in sorted(r['by_type'].items())),
                                        len(modules), len(script)))
    if r['unnamed']:
        log('   %d LuaB module(s) with no debug name left out' % len(r['unnamed']))
    if ACTIVE['files']:
        log(
            '   %d data file(s) its Lua reads by io.open, embedded: %s'
            % (len(ACTIVE['files']), ', '.join(sorted(ACTIVE['files'])[:8]))
        )
    return base


def finish_map(out, log=print):
    if not ACTIVE:
        return 0
    from doctor.port import game_files
    names = game_files.shadowed(out)
    if names:
        game_files.remove(out, names)
    log('6b. %d file(s) at the paths of the game itself taken out' % len(names))
    return len(names)


def apply_modules(collected, entries):
    if not ACTIVE:
        return False
    modules = dict(ACTIVE['modules'])
    names = 'local XM_NATIVES = {%s}\n' % ', '.join("'%s'" % n for n in ACTIVE.get('natives', ()))
    modules['__xm_runtime.lua'] = {
        'block_entry': 89999,
        'data_bytes': names.encode('ascii') + _runtime(),
        'forma': 'body_text',
        'origin': 'runtime',
    }
    for n, entry in enumerate(entries or ()):
        key = entry.replace('.', '\\') + '.lua'
        real = key if key in modules else None
        target = 'main' if entry == 'hotupdate' and 'main.lua' in modules else None
        if real and target is None:
            alias = '__xm_entry\\' + key
            modules[alias] = modules[real]
            target = '__xm_entry.' + entry
        if target is None:
            continue
        text = "require '__xm_runtime'\nreturn require '%s'\n" % target
        modules[key] = {
            'block_entry': 90000 + n,
            'data_bytes': text.encode('ascii'),
            'forma': 'body_text',
            'origin': 'runtime',
        }
    collected['lua_modules'] = modules
    files = dict(collected.get('file_set') or {})
    files.update(ACTIVE.get('files') or {})
    collected['file_set'] = files
    collected['dll'] = []
    collected['unnamed'] = []
    return True
