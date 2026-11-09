# The xmload map family in the port: the unpacked pack, the real script and the runtime.
import os
import re


ACTIVE = {}
ENGINE_NOTES = (
    'this map runs on the xmload engine: its game logic is ported, but its interface (cocos2d-x inside its DLL) '
    'is not drawn on Reforged, so its windows and menus do not appear',
    'the server of this map is answered on this computer with empty data: what depends on it (saved progress, '
    'rankings, rewards) does not work',
    'the natives of its DLL listed as stubs below are in part answered at run time by the runtime of this engine '
    '(the bridge between JASS and Lua, lists, big numbers, object data, unit enumeration)',
)


def _runtime():
    from doctor.port import ydwe_port
    with open(ydwe_port._route_data('ydwe', 'xmload.lua'), 'rb') as f:
        return f.read()


def _modules(archive):
    from doctor.mpq import xm_pkg
    out = {}
    for name, data in xm_pkg.entries(archive):
        if not name.lower().endswith('.lua'):
            continue
        short = name[8:] if name.lower().startswith('scripts\\') else name
        out[short] = {'block_entry': 100000 + len(out), 'data_bytes': data, 'forma': 'bytecode', 'origin': 'pkg'}
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
        return None
    base = os.path.join(work, 'xm_base.w3x')
    r = xm_pkg.unpack_to_map(map_path, base, False, log=lambda s: None, real_script=True)
    script = xm_jx.map_script(archive.read('war3map.jx'), archive.read('war3map.j'))
    ACTIVE['modules'] = _modules(archive)
    ACTIVE['natives'] = _natives(script)
    log(
        '0b. xmload map: %d files unpacked from game.pkg, the real script (%d B) back from war3map.jx'
        % (r['files'], len(script))
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
    collected['dll'] = []
    collected['unnamed'] = []
    return True
