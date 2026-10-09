# Finds a map whose Lua the YDWE Lua engine ran (a DLL only the old game loaded): it does not run on Reforged.
import re


RX_EXEC = re.compile(r'\b(?:AbilityId|Cheat)\s*\(\s*"exec-lua:\s*([^"\\]+?)\s*"\s*\)')
RX_LOADER = re.compile(r'StartCampaignAI\s*\([^\n]*"callback"\s*\)')
RX_TRIGGER = re.compile(r'\b(?:CreateTrigger|TimerStart)\s*\(')
FOLDERS = ('scripts\\', 'w3x2lni\\plugin\\import\\scripts\\', '')


def _module(name, read):
    base = name.replace('.', '\\')
    for folder in FOLDERS:
        for path in (folder + base + '.lua', folder + base + '\\init.lua'):
            try:
                data = read(path)
            except Exception:
                data = None
            if data:
                return {'name': path, 'bytes': len(data), 'bytecode': data[:4] == b'\x1bLua'}
    return None


def detect(script, read=None):
    entries = list(dict.fromkeys(RX_EXEC.findall(script or '')))
    if not entries:
        return None
    triggers = len(RX_TRIGGER.findall(script))
    modules = [m for m in (_module(e, read) for e in entries) if m] if read else []
    return {'entries': entries, 'loader': bool(RX_LOADER.search(script)), 'all_lua': triggers == 0,
            'triggers': triggers, 'modules': modules}


def message(found):
    lua = 'Lua modules %s' % ', '.join(found['entries'][:6])
    if any(m['bytecode'] for m in found['modules']):
        lua += ', compiled'
    if found['all_lua']:
        return ('The game of this map is Lua run by the YDWE Lua engine (%s): a DLL the map ships, which only the old '
                'game loaded, through a memory trick. Reforged cannot load it, so the map starts and nothing happens. '
                'The port turns it into a Lua map that runs those modules.' % lua)
    return ('Part of this map is Lua run by the YDWE Lua engine (%s): a DLL the map ships, which only the old game '
            'loaded. Reforged cannot load it, so what the Lua did does not happen; the rest of the map (its JASS) '
            'runs. The port turns it into a Lua map that runs those modules.' % lua)
