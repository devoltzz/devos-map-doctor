# The UjAPI route of the port: a map made for the UjAPI (the Unryze JASS API for patches 1.24-1.28) gets its natives declared and its constants and types mapped to Warcraft III 3.0.
import collections
import os
import re


HERE = os.path.dirname(os.path.abspath(__file__))
COMPAT = os.path.join(HERE, 'compat')
API_J = os.path.join(COMPAT, 'ujapi_api.j')
EQ_J = os.path.join(COMPAT, 'nat_ujapi_eq.j')
IMPL_J = os.path.join(COMPAT, 'nat_ujapi.j')
REF_30 = os.path.normpath(os.path.join(HERE, '..', 'ref', '3.0'))
ARCHIVE_ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
BASE_127 = os.path.join(ARCHIVE_ROOT, 'terceiros', 'w3x2lni-2.7.3', 'data', 'enUS-1.27.1', 'mpq', 'Scripts', 'Common.j')
UJAPI_DEFAULT = os.path.join(ARCHIVE_ROOT, 'terceiros', 'unryze', 'UjAPI', 'uJAPIFiles')

RX_NATIVE = re.compile(r'(?m)^[ \t]*(constant[ \t]+)?native[ \t]+(\w+)[ \t]+takes[ \t]+(.+?)[ \t]+returns[ \t]+(\w+)')
RX_FUNC = re.compile(r'(?m)^[ \t]*(?:constant[ \t]+)?function[ \t]+(\w+)[ \t]+takes[ \t]+(.+?)[ \t]+returns[ \t]+(\w+)')
RX_TYPE_CHECK = re.compile(r'(?m)^[ \t]*type[ \t]+(\w+)[ \t]+extends[ \t]+(\w+)')
RX_GLOBALS = re.compile(r'(?ms)^[ \t]*globals\b[^\n]*\n(.*?)^[ \t]*endglobals\b')
RX_CONST = re.compile(r'^[ \t]*constant[ \t]+(\w+)[ \t]+(\w+)[ \t]*=[ \t]*(.*?)[ \t]*$')
RX_VAR = re.compile(r'^[ \t]*(?:constant[ \t]+)?(\w+)[ \t]+(?:array[ \t]+)?(\w+)')
RX_SECTION = re.compile(r'^//[ \t]*([A-Z][\w /]*?API(?:[ \t]+(?:Main|Basic))?|Jass Operations)[ \t]*(?:$|\||\()')
RX_TOKEN = re.compile(r'"(?:[^"\\]|\\.)*"|\'(?:[^\'\\\n]|\\.)*\'|//[^\n]*|[A-Za-z_]\w*')

INTEGER_TYPES = (
    'projectiletype',
    'mappedfield',
    'mappedtype',
    'attachmenttype',
    'bonetype',
    'cursoranimtype',
    'flagtype',
    'layoutstyleflag',
    'gridstyleflag',
    'layerstyleflag',
    'controlstyleflag',
    'framestate',
    'abilitytype',
    'itemdisableflag',
    'pathingaitype',
    'collisiontype',
    'damageflag',
    'spriteflag',
    'bonusattribute',
    'timetype',
    'variabletype',
    'renderstage',
    'connectiontype',
    'tradestate',
)
OBJECT_TYPES = (
    'war3image',
    'sprite',
    'projectile',
    'doodad',
    'handlelist',
    'textfilehandle',
    'orderhandle',
    'camerahandle',
)
UNPAIRED_TYPES = (
    'agentdatafield',
    'widgetintegerfield',
    'widgetrealfield',
    'widgetbooleanfield',
    'widgetstringfield',
    'destructableintegerfield',
    'destructablerealfield',
    'destructablebooleanfield',
    'destructablestringfield',
    'jassthread',
)
ALIAS = dict(
    [(t, 'integer') for t in INTEGER_TYPES]
    + [(t, 'agent') for t in OBJECT_TYPES]
    + [(t, 'handle') for t in UNPAIRED_TYPES]
)
CALL_VALUE = {'GetTextTagLimit': '100', 'GetJassArrayLimit': '32768'}
NEUTRAL = {'integer': '0', 'real': '0.0', 'boolean': 'false', 'string': '""'}

REASONS = {
    'Typecasting API Main': 'converts integers or memory addresses to handles: Reforged has no typecast',
    'Typecasting API Basic': 'converts integers to handles: Reforged has no typecast',
    'Jass Data API': 'reads or writes the JASS VM by name: Reforged has no such access',
    'Jass VM API': 'drives the JASS VM (threads, globals by name, op limit): Reforged has no such access',
    'Jass Operations': 'drives the JASS VM: Reforged has no such access',
    'Debug API': 'debug output of the DLL',
    'Text File API': 'reads and writes files on disk: Reforged has only the Preload save',
    'Misc API': 'engine settings the DLL exposes (no Reforged native)',
    'Terrain API': 'terrain internals the DLL exposes (no Reforged native)',
    'Map API': 'map file internals the DLL exposes',
    'Time API': 'the computer clock: Reforged has no such native (and it would desync)',
    'Benchmark API': 'the computer clock: Reforged has no such native',
    'Aspect Ratio API': 'the window shape: Reforged has no such native',
    'Screen API': 'the window: Reforged has no such native',
    'Axis API': 'world/screen projection: Reforged has no such native',
    'Window API': 'the window: Reforged has no such native',
    'Cursor API': 'the cursor sprite: Reforged has no such native',
    'Mouse API': 'mouse state the DLL reads (Reforged has only the mouse events and BlzGetTriggerPlayerMouse*)',
    'Game API': 'engine settings the DLL exposes (no Reforged native)',
    'Chat API': 'the chat box internals: Reforged has only BlzDisplayChatMessage',
    'Handle API': 'handle internals (reference counts, addresses): Reforged has no such access',
    'AntiHack API': 'the DLL anti-cheat: there is no such thing in Reforged',
    'Sprite API': 'the sprite (a bare model) has no Reforged type: use a special effect',
    'Doodad API': 'the doodad as an object has no Reforged type (Reforged has only the doodad animation by area)',
    'War3Image API': 'the war3image (the base of every model object) has no Reforged type',
    'Projectile API': 'the projectile (missile) has no Reforged type',
    'Trackable API': 'trackable internals the DLL exposes (no Reforged native)',
    'Handle List API': 'the handle list has no Reforged type (use a group, a force or a hashtable)',
    'Camera API': 'the camera object has no Reforged type (Reforged has the camera setup and the local camera)',
    'Order API': 'the order object has no Reforged type',
    'Buff API': 'buff internals the DLL exposes: Reforged has only the buff level and the ability fields',
    'Ability API': 'the object-data (base) fields by id and the ability internals: Reforged edits the fields of an '
                   'ability a unit has, not the type',
    'Item API': 'item internals and the object-data fields by id: Reforged has only the fields of an item instance',
    'Unit API': 'unit internals the DLL exposes (no Reforged native)',
    'Widget API': 'the widget as a model object (position, scale, model, animation): Reforged has it per unit or '
                  'effect only',
    'Destructable API': 'the destructable as a model object and its fields: Reforged has no destructable fields',
    'SpecialEffect API': 'effect internals Reforged does not expose',
    'Frame API': 'frame internals of the classic UI Reforged does not expose',
    'Frame Sprite API': 'the sprite of a frame has no Reforged type',
    'TextTag API': 'text tag getters and setters Reforged does not have',
    'Lightning API': 'lightning getters and setters Reforged does not have',
    'Image API': 'image getters and setters Reforged does not have',
    'Gathering API': 'the harvest, mine and train internals the DLL exposes',
    'Inventory API': 'the inventory internals the DLL exposes (Reforged has 6 slots and UnitInventorySize)',
    'Force API': 'force internals the DLL exposes',
    'Player API': 'player internals the DLL exposes (host, mute, APM, pathing)',
    'Player Trade Event API': 'the trade event of UjAPI: Reforged has no such event',
    'Player Minimap Ping Event API': 'the minimap ping event of UjAPI: Reforged has no such event',
    'Variable Sync API': 'the UjAPI sync of variables: use BlzSendSyncData (the Prefix Sync API is ported)',
    'Hashtable Sync API': 'the UjAPI sync of hashtables: use BlzSendSyncData (the Prefix Sync API is ported)',
    'Mouse Event API': 'the mouse move event of UjAPI: Reforged has only EVENT_PLAYER_MOUSE_MOVE and its getters',
    'Damage Event API': 'the damage flags and extra values UjAPI adds: Reforged has the damage, the types and the '
                        'attack flag',
    'Unit Timed Life API': 'unit internals the DLL exposes (timed life, ghost, reveal, resistances)',
    'Timer API': 'timer internals the DLL exposes (pause state, period, callback)',
    'Trigger API': 'trigger internals the DLL exposes (event lists, hack events)',
}
DEFAULT_REASON = 'no Reforged native does this, and it cannot be written in JASS over the Reforged natives'


def read_data(file_path):
    with open(file_path, 'rb') as f:
        return f.read().decode('utf-8', 'replace').replace('\r\n', '\n').replace('\r', '\n')


def _args(txt):
    txt = txt.strip()
    if txt == 'nothing':
        return []
    out = []
    for a in txt.split(','):
        p = a.split()
        out.append((p[0], p[1] if len(p) > 1 else 'a%d' % (len(out) + 1)))
    return out


def _no_comment(line):
    m = None
    for m in RX_TOKEN.finditer(line):
        if m.group(0).startswith('//'):
            return line[:m.start()].rstrip()
    return line.rstrip()


def definitions(body_text):
    nat = dict((m.group(2), (_args(m.group(3)), m.group(4))) for m in RX_NATIVE.finditer(body_text))
    fun = dict((m.group(1), (_args(m.group(2)), m.group(3))) for m in RX_FUNC.finditer(body_text))
    glo = {}
    for block_entry in RX_GLOBALS.findall(body_text):
        for line in block_entry.split('\n'):
            line = _no_comment(line)
            m = RX_CONST.match(line)
            if m:
                glo[m.group(2)] = (m.group(1), m.group(3))
                continue
            m = RX_VAR.match(line)
            if m and m.group(1) not in ('endglobals', 'globals'):
                glo[m.group(2)] = (m.group(1), None)
    return {'natives': nat, 'functions': fun, 'types': dict(RX_TYPE_CHECK.findall(body_text)), 'globals_block': glo}


_CACHE = {}


def game_reference(ref=None):
    if ref is None:
        try:
            from doctor.port import new
            ref = new.REF
        except Exception:
            ref = REF_30
    if ref not in _CACHE:
        c = definitions(read_data(os.path.join(ref, 'common.j')))
        b = definitions(read_data(os.path.join(ref, 'blizzard.j')))
        c['functions'] = b['functions']
        c['bj_globals'] = b['globals_block']
        _CACHE[ref] = c
    return _CACHE[ref]


def read_api(file_path=API_J):
    if file_path in _CACHE:
        return _CACHE[file_path]
    t = read_data(file_path)
    d = definitions(t)
    family, current = {}, ''
    for line in t.split('\n'):
        if line.startswith('//@ujapi '):
            current = line[len('//@ujapi '):].strip()
            continue
        m = RX_NATIVE.match(line)
        if m:
            family[m.group(2)] = current
    v = re.search(r'(?m)^//@ujapi_versao (\S+)', t)
    api = {'version_num': v.group(1) if v else '?', 'types': d['types'], 'natives': d['natives'], 'family': family,
           'w3p_constants': dict((k, v) for k, v in d['globals_block'].items() if v[1] is not None)}
    _CACHE[file_path] = api
    return api


def reforged_type(t):
    return ALIAS.get(t, t)


def signature(fname, args, ret, word='native'):
    return '%s %s takes %s returns %s' % (
        word, fname, ', '.join('%s %s' % (reforged_type(a), n) for a, n in args) if args else 'nothing',
        reforged_type(ret))


SUBSECTIONS = ('Base Field API', 'Field API', 'Normal API', 'Placement API', 'Trigger Item API')


def _ujapi_families(body_text):
    fam, current = {}, 'Game Constants'
    for line in body_text.split('\n'):
        m = RX_SECTION.match(line.strip())
        if m:
            fname = m.group(1).strip()
            if fname not in SUBSECTIONS and not re.search(r'\b(?:the|of|for)\b', fname):
                current = fname
            continue
        m = RX_NATIVE.match(line)
        if m:
            fam[m.group(2)] = current
    return fam


def _ujapi_version(folder):
    logs = os.path.join(folder, 'Changelogs')
    vs = []
    for f in os.listdir(logs) if os.path.isdir(logs) else ():
        m = re.match(r'UjAPI v([\d.]+)\.txt$', f)
        if m:
            vs.append(tuple(int(x) for x in m.group(1).split('.')))
    return '.'.join(map(str, max(vs))) if vs else '?'


def gera(ujapi_folder=UJAPI_DEFAULT, base=BASE_127, output=API_J, eq=EQ_J, ref=REF_30):
    ujc = read_data(os.path.join(ujapi_folder, 'common.j'))
    fam = _ujapi_families(read_data(os.path.join(ujapi_folder, 'UjAPI.j')))
    U, B = definitions(ujc), definitions(read_data(base))
    version_num = _ujapi_version(os.path.join(ujapi_folder))
    L = ['// ==============================================================================================',
         '// GENERATED by ujapi.py: what the common.j of UjAPI %s has and the one of 1.26/1.27 does not.' % version_num,
         '// NOT a part of the layer (no part list names it): it is the DATA of the UjAPI route (ujapi.py).',
         '// Fonte: https://github.com/UnryzeC/UjAPI (uJAPIFiles/common.j e UjAPI.j).',
         '// MIT License, Copyright (c) 2022 Sandro Takaishvili. Permission is hereby granted, free of charge, to any',
         '// person obtaining a copy of this software and associated documentation files (the "Software"), to deal in',
         '// the Software without restriction (...). The above copyright notice and this permission notice shall be',
         '// included in all copies or substantial portions of the Software. THE SOFTWARE IS PROVIDED "AS IS".',
         '// ==============================================================================================',
         '//@ujapi_versao %s' % version_num]
    types = [(n, p) for n, p in U['types'].items() if n not in B['types']]
    L += ['type %s extends %s' % python_time for python_time in types]
    L.append('globals')
    consts = [(n, v) for n, v in U['globals_block'].items() if n not in B['globals_block'] and v[1] is not None]
    L += ['    constant %s %s = %s' % (v[0], n, v[1]) for n, v in consts]
    L.append('endglobals')
    nats = [(n, v) for n, v in U['natives'].items() if n not in B['natives']]
    by_family = collections.OrderedDict()
    for n, v in nats:
        by_family.setdefault(fam.get(n, 'Reforged natives (Blz)'), []).append((n, v))
    for f, listing in by_family.items():
        L.append('//@ujapi %s' % f)
        for n, (args, ret) in listing:
            L.append('native %s takes %s returns %s' % (
                n, ', '.join('%s %s' % a for a in args) if args else 'nothing', ret))
    with open(output, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')
    _CACHE.pop(output, None)
    n_eq = make_equivalents(read_api(output), game_reference(ref), eq)
    return len(types), len(consts), len(nats), n_eq


def _name_tokens(n):
    n = re.sub(r'^Blz', '', n)
    return tuple(
        sorted({'colour': 'color'}.get(x.lower(), x.lower()) for x in re.findall(r'[A-Z][a-z0-9]*|[a-z0-9]+', n))
    )


NOT_EQUIVALENT = set()


def candidates(api, ref):
    idx = collections.defaultdict(list)
    for n in ref['natives']:
        idx[_name_tokens(n)].append(n)
    out = {}
    for n, (args, ret) in sorted(api['natives'].items()):
        if n in ref['natives'] or n in NOT_EQUIVALENT:
            continue
        sig = ([reforged_type(t) for t, _x in args], reforged_type(ret))
        for m in idx.get(_name_tokens(n), ()):
            rargs, rret = ref['natives'][m]
            if ([t for t, _x in rargs], rret) == sig:
                out[n] = m
                break
    return out


def make_equivalents(api, ref, output=EQ_J):
    cands = candidates(api, ref)
    by_hand = set(part_functions((IMPL_J,)))
    L = [
        '// ==============================================================================================',
        '// KK FRAMEWORK, the UjAPI route (the CONDITIONAL NATIVES part `KKN:nat_ujapi_eq.j`, see the docstring of',
        '// `layer.py`). GENERATED by ujapi.py: do not edit by hand (a wrong pair goes to the',
        '// `NOT_EQUIVALENT` of ujapi.py; a body written by hand goes to `nat_ujapi.j`, which wins over this one).',
        '// Each function is the UjAPI native Reforged has under ANOTHER name with the same signature, or the Convert* of',
        '// a type the route turns into integer (the identity). Only what the map declares `native` goes in.',
        '// ==============================================================================================',
    ]
    n = 0
    for fname, (args, ret) in sorted(api['natives'].items()):
        body = None
        if fname in by_hand:
            continue
        if fname in cands:
            call_expr = '%s(%s)' % (cands[fname], ', '.join(x for _t, x in args))
            body = ('    call %s' % call_expr) if ret == 'nothing' else ('    return %s' % call_expr)
        elif re.match(r'Convert\w+$', fname) and reforged_type(ret) == 'integer' and ret != 'integer' and \
                [reforged_type(t) for t, _x in args] == ['integer']:
            body = '    return %s' % args[0][1]
        if body is None:
            continue
        L += ['', 'function %s takes %s returns %s' % (
            fname, ', '.join('%s %s' % (reforged_type(t), x) for t, x in args) or 'nothing', reforged_type(ret)),
            body, 'endfunction']
        n += 1
    with open(output, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')
    return n


ROUTE_PARTS = tuple(
    os.path.join(COMPAT, f)
    for f in (
        'nat_blizzard.j',
        'nat_shop.j',
        'nat_dzapi.j',
        'nat_relatives.j',
        'nat_emulated.j',
        'nat_ujapi.j',
        'nat_ujapi_eq.j',
    )
)


def part_functions(pieces=ROUTE_PARTS):
    out = {}
    for p in pieces:
        if not os.path.isfile(p):
            continue
        t = read_data(p)
        for m in re.finditer(r'(?ms)^function[ \t]+(\w+)[ \t]+takes[^\n]*\n(.*?)^endfunction', t):
            out.setdefault(m.group(1), (os.path.basename(p), m.group(2)))
    return out


def classify_items(api=None, ref=None):
    api = api or read_api()
    ref = ref or game_reference()
    bodies = part_functions()
    base = set(n for n in ref['natives'] if not n.startswith('Blz'))
    out = {}
    for n, (args, ret) in api['natives'].items():
        if n in ref['natives']:
            rargs, rret = ref['natives'][n]
            same = ([t for t, _x in rargs], rret) == ([t for t, _x in args], ret)
            out[n] = ('direct', '') if same else ('stub', 'Reforged has %s with another signature' % n)
            continue
        if n in bodies:
            file_, body = bodies[n]
            called = set(re.findall(r'\b([A-Za-z_]\w*)\s*\(', body))
            blz = sorted(c for c in called if c in ref['natives'] and c not in base)
            out[n] = ('equivalent', ', '.join(blz)) if blz else ('implemented', file_)
            continue
        fam = api['family'].get(n, '')
        objects = [t for t, _x in args + [(ret, '')] if t in OBJECT_TYPES]
        if objects and fam not in REASONS:
            out[n] = ('stub', 'the %s type has no Reforged counterpart' % objects[0])
        else:
            out[n] = ('stub', REASONS.get(fam.split(' | ')[0], DEFAULT_REASON))
    return out


def summary(cl=None):
    cl = cl or classify_items()
    return collections.Counter(c for c, _d in cl.values())


def _code(body_text):
    def swap(m):
        s = m.group(0)
        if s[0] in '"\'/':
            return re.sub(r'[^\n]', ' ', s)
        return s
    return RX_TOKEN.sub(swap, body_text)


def _lf(body_text):
    return re.sub(r'\r(?!\n)', '\n', body_text)


RX_LOCAL = re.compile(r'\blocal[ \t]+(\w+)[ \t]+(?:array[ \t]+)?(\w+)')
RX_SIGNATURE = re.compile(r'\btakes[ \t]+(.*?)[ \t]+returns[ \t]+(\w+)')


def uses(body_text, api=None, ref=None, extras=()):
    api = api or read_api()
    ref = ref or game_reference()
    code_part = _code(_lf(body_text))
    d = definitions(code_part)
    defined = set(d['natives']) | set(d['functions']) | set(d['globals_block'])
    for e in extras:
        from_ = definitions(_code(_lf(e)))
        defined |= set(from_['natives']) | set(from_['functions']) | set(from_['globals_block'])
    in_type_position = set()
    for m in RX_LOCAL.finditer(code_part):
        in_type_position.add(m.group(1))
        defined.add(m.group(2))
    for m in RX_SIGNATURE.finditer(code_part):
        in_type_position.add(m.group(2))
        for t, x in _args(m.group(1)):
            in_type_position.add(t)
            defined.add(x)
    in_type_position |= set(t for t, _v in d['globals_block'].values())
    in_type_position |= set(d['types'].values())
    ids = collections.Counter(re.findall(r'[A-Za-z_]\w*', code_part))
    calls = set(re.findall(r'\b([A-Za-z_]\w*)[ \t]*\(', code_part)) | set(
        re.findall(r'\bfunction[ \t]+(\w+)', code_part)
    )
    ref_types = set(ref['types']) | {'integer', 'real', 'boolean', 'string', 'handle', 'code', 'nothing'}
    types = sorted(t for t in in_type_position if t in api['types'] and t not in ref_types)
    natives = sorted(n for n in calls if n in api['natives'] and n not in ref['natives'] and n not in defined)
    w3p_constants = sorted(n for n in ids if n in api['w3p_constants'] and n not in ref['globals_block'] and
                           n not in ref['bj_globals'] and n not in defined)
    return {'types': types, 'natives': natives, 'w3p_constants': w3p_constants, 'defined': defined,
            'declared_types': sorted(t for t in d['types'] if t in api['types'] and t not in ref_types)}


def detect(body_text, api=None, ref=None, extras=()):
    u = uses(body_text, api, ref, extras)
    return u if (u['types'] or u['natives'] or u['w3p_constants']) else None


def _int(v):
    v = v.strip()
    try:
        if v.startswith('$'):
            return int(v[1:], 16)
        if v.lower().startswith('0x'):
            return int(v, 16)
        if v.startswith("'") and v.endswith("'"):
            r = 0
            for c in v[1:-1]:
                r = r * 256 + ord(c)
            return r
        return int(v)
    except ValueError:
        return None


def reforged_values(ref):
    out = collections.defaultdict(dict)
    for n, (_t, v) in ref['globals_block'].items():
        m = re.match(r'(Convert\w+)\((.*)\)$', v or '')
        if m and _int(m.group(2)) is not None:
            out[m.group(1)][_int(m.group(2))] = n
    return out


SAME_THING = {
    'ORIGIN_FRAME_CONSOLE_UI': 'ORIGIN_FRAME_SIMPLE_UI_PARENT',
    'ORIGIN_FRAME_BUFF_BAR': 'ORIGIN_FRAME_UNIT_PANEL_BUFF_BAR',
    'ORIGIN_FRAME_BUFF_BAR_TEXT': 'ORIGIN_FRAME_UNIT_PANEL_BUFF_BAR_LABEL',
    'FRAMEEVENT_FRAME_ITEM_CHANGED': 'FRAMEEVENT_POPUPMENU_ITEM_CHANGED',
}


def constant_value(fname, api, ref, colisoes=None):
    kind, field_value = api['w3p_constants'][fname]
    tr = reforged_type(kind)
    if fname in SAME_THING and SAME_THING[fname] in ref['globals_block']:
        return tr, SAME_THING[fname], 'the same thing on Reforged is %s' % SAME_THING[fname]
    m = re.match(r'(\w+)\((.*)\)$', field_value)
    if not m:
        if re.match(r'^[-\w.$\']+$', field_value) and not re.search(
            r'[A-Za-z_]\w*', field_value.replace('0x', '').replace('$', '')
        ):
            return tr, field_value, None
        return tr, NEUTRAL.get(tr, 'null'), 'the UjAPI value %s is not a literal' % field_value
    func, arg = m.group(1), m.group(2).strip()
    if func in CALL_VALUE:
        return tr, CALL_VALUE[func], 'the Reforged limit (%s on UjAPI)' % func
    if tr == 'integer' and func not in ref['natives']:
        return tr, arg, None
    if func in ref['natives']:
        in_use = (colisoes or reforged_values(ref)).get(func, {})
        k = _int(arg)
        if k is not None and k in in_use and in_use[k] != fname:
            if func.endswith('Field'):
                return tr, in_use[k], 'the same field on Reforged is %s' % in_use[k]
            return tr, 'null', 'UjAPI number %s is %s on Reforged' % (arg, in_use[k])
        return tr, field_value, None
    return tr, NEUTRAL.get(tr, 'null'), 'no Reforged converter %s' % func


def _insert_globals(body_text, line_list):
    if not line_list:
        return body_text
    block_entry = ''.join('    %s\n' % line for line in line_list)
    m = re.search(r'(?m)^[ \t]*globals\b[^\n]*\n', _code(body_text))
    if m:
        return body_text[:m.end()] + block_entry + body_text[m.end():]
    m = re.search(r'(?m)^[ \t]*(?:constant[ \t]+)?(?:native|function)[ \t]', _code(body_text))
    i = m.start() if m else len(body_text)
    return body_text[:i] + 'globals\n' + block_entry + 'endglobals\n' + body_text[i:]


def _insert_natives(body_text, line_list):
    if not line_list:
        return body_text
    block_entry = ''.join(line + '\n' for line in line_list)
    code_part = _code(body_text)
    m = re.search(r'(?m)^[ \t]*endglobals\b[^\n]*\n', code_part)
    if m:
        return body_text[:m.end()] + block_entry + body_text[m.end():]
    m = re.search(r'(?m)^[ \t]*(?:constant[ \t]+)?function[ \t]', code_part)
    i = m.start() if m else len(body_text)
    return body_text[:i] + block_entry + body_text[i:]


def prepare(body_text, api=None, ref=None, extras=()):
    api = api or read_api()
    ref = ref or game_reference()
    u = detect(body_text, api, ref, extras)
    if not u:
        return body_text, None
    alias = dict((t, reforged_type(t)) for t in u['types'] + u['declared_types'])
    notes = []
    t = _lf(body_text)
    if u['declared_types']:
        rx = re.compile(r'(?m)^[ \t]*type[ \t]+(%s)[ \t]+extends[ \t]+\w+[^\n]*\n' % '|'.join(u['declared_types']))
        t = rx.sub('', t)
    if alias:
        def swap(m):
            s = m.group(0)
            return alias.get(s, s) if s[0] not in '"\'/' else s
        t = RX_TOKEN.sub(swap, t)
    colisoes = reforged_values(ref)
    consts, line_list = {}, []
    for n in u['w3p_constants']:
        tr, v, score = constant_value(n, api, ref, colisoes)
        consts[n] = v
        line_list.append('constant %s %s = %s' % (tr, n, v))
        if score:
            notes.append('%s: %s' % (n, score))
    t = _insert_globals(t, line_list)
    decl = []
    for n in u['natives']:
        args, ret = api['natives'][n]
        decl.append(signature(n, args, ret))
    t = _insert_natives(t, decl)
    leftover = set(re.findall(r'[A-Za-z_]\w*', _code(t))) & set(alias)
    if leftover:
        raise ValueError('ujapi.prepara: the UjAPI type(s) %s are still in the script' % ', '.join(sorted(leftover)))
    return t, {
        'types': alias,
        'natives': u['natives'],
        'w3p_constants': consts,
        'notes': notes,
        'version_num': api['version_num'],
    }


NATIVE_WARNINGS = (
    (('EnableOperationLimit', 'SetOperationLimit'),
     'the map turns off or raises the JASS operation limit (UjAPI %s): on Reforged a long loop in one thread stops '
     'silently at the normal limit; check the start-up and the heavy systems'),
    (('SetMoveSpeedMaxAllowed', 'SetMoveSpeedMinAllowed', 'SetAttackSpeedMaxBonus', 'SetAttackSpeedMinBonus',
      'SetVisionMax'),
     'the map changes engine caps (UjAPI %s): Reforged keeps its own (movement 522, attack speed bonus, sight), so '
     'what was above them is lost'),
    (('TextFile', 'RunJassScript', 'RunJassScriptFromFile', 'ExecuteFuncEx', 'CallNative',
      'CallFunction', 'GetCodeByName'),
     'the map runs code or reads files by name at run time (UjAPI %s): those natives are stubs, so what they loaded '
     'does not exist on Reforged'),
    (('AntiHack',),
     'the map turns on the UjAPI anti-cheat (%s): it does not exist on Reforged (the natives are stubs)'),
)


def warnings(info, body_text=''):
    out = []
    used_entries = set(info.get('natives') or ())
    for name_list, msg in NATIVE_WARNINGS:
        hits = sorted(n for n in used_entries if any(n.startswith(x) for x in name_list))
        if hits:
            out.append(msg % ', '.join(hits))
    nulls = sorted(n for n, v in (info.get('w3p_constants') or {}).items() if v == 'null')
    if nulls:
        out.append('%d UjAPI constant(s) use a number that means something else on Reforged, so they became null (an '
                   'event registered with one of them never fires): %s' % (len(nulls), ', '.join(nulls[:12])))
    if re.search(r'\bJASS_MAX_ARRAY_SIZE\b', _code(body_text)) or 'GetJassArrayLimit' in used_entries:
        out.append('the map reads JASS_MAX_ARRAY_SIZE: UjAPI arrays go up to 262144 entries, Reforged arrays to 32768; '
                   'an index above that is lost')
    return out

