# Ports a map to an older game (Reforged or a newer classic one to 1.29.2 ... 1.24a): what the older game lacks written into the script, the map info, object data, terrain and doodads in its formats.
import os
import re
import sys

from doctor.data import wc3_versions

HERE = os.path.dirname(os.path.abspath(__file__))

B = chr(92)


class Refusal(Exception):
    pass


RX_STRINGS_COMMENTS = re.compile(r'"(?:[^"\\\n]|\\.)*"|//[^\n]*')
RX_TYPE_CHECK = re.compile(r'(?m)^[ \t]*type[ \t]+(\w+)[ \t]+extends[ \t]+(\w+)')
RX_NATIVE_DECL = re.compile(
    r'(?m)^[ \t]*(?:constant[ \t]+)?native[ \t]+(\w+)[ \t]+takes[ \t]+(.+?)[ \t]+returns[ \t]+(\w+)'
)
RX_GLOBALS = re.compile(r'(?ms)^[ \t]*globals\b(.*?)^[ \t]*endglobals')
RX_DECL_LINE = re.compile(r'^[ \t]*(constant[ \t]+)?(\w+)[ \t]+(array[ \t]+)?(\w+)(?:[ \t]*=[ \t]*(.*?))?[ \t]*$')
RX_FUNCTION = re.compile(r'(?ms)^[ \t]*(?:constant[ \t]+)?function[ \t]+(\w+)[ \t]+takes[ \t]+(.+?)[ \t]+returns[ \t]+'
                         r'(\w+)[ \t]*$.*?^[ \t]*endfunction')
RX_MAP_NATIVE_DECL = re.compile(
    r'(?m)^[ \t]*(?:constant[ \t]+)?native[ \t]+(\w+)[ \t]+takes[ \t]+(.+?)[ \t]+returns[ \t]+'
    r'(\w+)[ \t]*\n?'
)
RX_IDENT = re.compile(r'\b[A-Za-z_]\w*\b')
RX_LOCAL = re.compile(r'(?m)^[ \t]*local[ \t]+\w+[ \t]+(?:array[ \t]+)?(\w+)')
BASIC_TYPES = frozenset(('integer', 'real', 'boolean', 'string', 'code', 'handle', 'nothing'))
KEYWORDS = frozenset(('function', 'takes', 'returns', 'return', 'endfunction', 'local', 'set', 'call', 'if', 'then',
                      'else', 'elseif', 'endif', 'loop', 'exitwhen', 'endloop', 'and', 'or', 'not', 'null', 'true',
                      'false', 'array', 'constant', 'native', 'type', 'extends', 'globals', 'endglobals', 'nothing',
                      'debug'))


def _without_comments(body_text):
    return RX_STRINGS_COMMENTS.sub(lambda m: m.group(0) if m.group(0).startswith('"') else '', body_text)


def _code_names(body_text):
    return set(RX_IDENT.findall(RX_STRINGS_COMMENTS.sub(' ', body_text))) - KEYWORDS


def _params(txt):
    txt = txt.strip()
    if txt == 'nothing':
        return []
    out = []
    for p in txt.split(','):
        t = p.split()
        out.append((t[0], t[1]) if len(t) == 2 else (t[0], 'p%d' % len(out)))
    return out


class GameScripts(object):
    def __init__(self, folder):
        self.folder = folder
        self.types, self.natives, self.globals_block, self.functions = {}, {}, {}, {}
        order = 0
        for file_ in ('common.j', 'blizzard.j'):
            with open(os.path.join(folder, file_), 'rb') as f:
                txt = _without_comments(f.read().decode('latin-1').replace('\r\n', '\n').replace('\r', '\n'))
            self.types.update(RX_TYPE_CHECK.findall(txt))
            for fname, ps, ret in RX_NATIVE_DECL.findall(txt):
                self.natives[fname] = (_params(ps), ret)
            for block_entry in RX_GLOBALS.findall(txt):
                for ln in block_entry.split('\n'):
                    m = RX_DECL_LINE.match(ln)
                    if not m or m.group(2) in ('globals', 'endglobals'):
                        continue
                    order += 1
                    self.globals_block[m.group(4)] = {'the_constant': bool(m.group(1)), 'kind': m.group(2),
                                                      'array': bool(m.group(3)), 'init': (m.group(5) or '').strip(),
                                                      'order': order}
            for m in RX_FUNCTION.finditer(txt):
                order += 1
                self.functions[m.group(1)] = {
                    'params': _params(m.group(2)),
                    'ret': m.group(3),
                    'body_text': m.group(0).strip('\n'),
                    'order': order,
                }
        self.name_list = (
            set(self.types) | set(self.natives) | set(self.globals_block) | set(self.functions) | BASIC_TYPES
        )
        self.ai_natives = set()
        if os.path.isfile(os.path.join(folder, 'common.ai')):
            with open(os.path.join(folder, 'common.ai'), 'rb') as f:
                self.ai_natives = set(n for n, _p, _r in RX_NATIVE_DECL.findall(
                    _without_comments(f.read().decode('latin-1').replace('\r\n', '\n').replace('\r', '\n'))))

    def dependencies(self, fname):
        if fname in self.functions:
            return _code_names(self.functions[fname]['body_text']) - {fname}
        if fname in self.natives:
            ps, ret = self.natives[fname]
            return set(t for t, _n in ps) | {ret}
        if fname in self.globals_block:
            g = self.globals_block[fname]
            return {g['kind']} | _code_names(g['init'])
        if fname in self.types:
            return {self.types[fname]}
        return set()


_GAME_SCRIPTS = {}


def ruler(folder):
    if folder not in _GAME_SCRIPTS:
        _GAME_SCRIPTS[folder] = GameScripts(folder)
    return _GAME_SCRIPTS[folder]


EMULATED = {
    'BlzCreateUnitWithSkin': ['return CreateUnit({0}, {1}, {2}, {3}, {4})'],
    'BlzCreateItemWithSkin': ['return CreateItem({0}, {1}, {2})'],
    'BlzGetUnitSkin': ['return GetUnitTypeId({0})'],
    'BlzGetItemSkin': ['return GetItemTypeId({0})'],
    'GetBJMaxPlayers': ['return bj_MAX_PLAYERS'],
    'GetBJMaxPlayerSlots': ['return bj_MAX_PLAYER_SLOTS'],
    'GetBJPlayerNeutralVictim': ['return bj_PLAYER_NEUTRAL_VICTIM'],
    'GetBJPlayerNeutralExtra': ['return bj_PLAYER_NEUTRAL_EXTRA'],
    'GetPlayerNeutralAggressive': ['return PLAYER_NEUTRAL_AGGRESSIVE'],
    'GetPlayerNeutralPassive': ['return PLAYER_NEUTRAL_PASSIVE'],
    'BlzGetUnitMaxHP': ['return R2I(GetUnitState({0}, UNIT_STATE_MAX_LIFE))'],
    'BlzGetUnitMaxMana': ['return R2I(GetUnitState({0}, UNIT_STATE_MAX_MANA))'],
    'BlzGroupGetSize': ['return CountUnitsInGroup({0})'],
    'BlzSetUnitFacingEx': ['call SetUnitFacing({0}, {1})'],
    'BlzPauseUnitEx': ['call PauseUnit({0}, {1})'],
    'BlzGetLocale': ['return "enUS"'],
    'BlzIsLocalClientActive': ['return true'],
    'BlzGetEventDamageTarget': ['return GetTriggerUnit()'],
    'BlzDecPlayerTechResearched': [
        'call SetPlayerTechResearched({0}, {1}, IMaxBJ(0, GetPlayerTechCount({0}, {1}, true) - {2}))'
    ],
    'BlzConvertColor': ['return {0} * 0x1000000 + {1} * 0x10000 + {2} * 0x100 + {3}'],
    'BlzGetUnitZ': [
        'local location l = Location(GetUnitX({0}), GetUnitY({0}))',
        'local real z = GetLocationZ(l) + GetUnitFlyHeight({0})',
        'call RemoveLocation(l)',
        'set l = null',
        'return z',
    ],
    'BlzGetLocalUnitZ': [
        'local location l = Location(GetUnitX({0}), GetUnitY({0}))',
        'local real z = GetLocationZ(l) + GetUnitFlyHeight({0})',
        'call RemoveLocation(l)',
        'set l = null',
        'return z',
    ],
    'BlzGroupUnitAt': [
        'local group c = CreateGroup()',
        'local unit u = null',
        'local integer i = {1}',
        'call GroupAddGroup({0}, c)',
        'loop',
        '    set u = FirstOfGroup(c)',
        '    exitwhen u == null or i <= 0',
        '    call GroupRemoveUnit(c, u)',
        '    set i = i - 1',
        'endloop',
        'call DestroyGroup(c)',
        'set c = null',
        'return u',
    ],
    'SetTerrainFogExV': ['call SetTerrainFogEx({0}, {1}, {2}, {3}, {8}, {9}, {10})'],
    'ChooseRandomItemExWithFilter': ['return ChooseRandomItemEx({0}, {1})'],
    'ChooseRandomItemExWithFilterAndIncludes': ['return ChooseRandomItemEx({0}, {1})'],
}


def _bit_op_body(bit_cond, sign_cond):
    return [
        'local integer r = 0',
        'local integer b = 1',
        'local integer i = 0',
        'local integer x = {0}',
        'local integer y = {1}',
        'local integer sx = 0',
        'local integer sy = 0',
        'if x < 0 then',
        '    set x = x + 2147483647 + 1',
        '    set sx = 1',
        'endif',
        'if y < 0 then',
        '    set y = y + 2147483647 + 1',
        '    set sy = 1',
        'endif',
        'loop',
        '    exitwhen i == 31',
        '    if %s then' % bit_cond,
        '        set r = r + b',
        '    endif',
        '    set x = x / 2',
        '    set y = y / 2',
        '    set b = b * 2',
        '    set i = i + 1',
        'endloop',
        'if %s then' % sign_cond,
        '    set r = r - 2147483647 - 1',
        'endif',
        'return r',
    ]


EMULATED['BlzBitAnd'] = _bit_op_body('x - x / 2 * 2 == 1 and y - y / 2 * 2 == 1', 'sx == 1 and sy == 1')
EMULATED['BlzBitOr'] = _bit_op_body('x - x / 2 * 2 == 1 or y - y / 2 * 2 == 1', 'sx == 1 or sy == 1')
EMULATED['BlzBitXor'] = _bit_op_body('x - x / 2 * 2 != y - y / 2 * 2', 'sx != sy')
NEUTRAL = {'integer': '0', 'real': '0.0', 'boolean': 'false', 'string': '""'}
RX_DESTRUCTABLE = re.compile(r'^BlzCreate(Dead)?Destructable(Z)?(WithSkin)?(?:PitchRoll|WithColor|Color)*$')


def _emulate_destructable(fname, ps, args, tgt=None):
    m = RX_DESTRUCTABLE.match(fname)
    if not m:
        return None
    name_list = [n for _t, n in ps]
    wanted = ['objectid', 'x', 'y'] + (['z'] if m.group(2) else []) + ['face', 'scale', 'variation']
    if not all(q in name_list for q in wanted):
        return None
    with_skin = 'BlzCreate%sDestructable%sWithSkin' % ('Dead' if m.group(1) else '', 'Z' if m.group(2) else '')
    if tgt is not None and with_skin in tgt.natives and with_skin != fname and 'skinId' in name_list:
        return ['return %s(%s)' % (with_skin, ', '.join(args[name_list.index(q)] for q in wanted + ['skinId']))]
    return ['return Create%sDestructable%s(%s)' % ('Dead' if m.group(1) else '', 'Z' if m.group(2) else '',
                                                  ', '.join(args[name_list.index(q)] for q in wanted))]


def neutral_value(kind):
    return NEUTRAL.get(kind, 'null')


DAMAGE_EVENTS = ('EVENT_PLAYER_UNIT_DAMAGED', 'EVENT_PLAYER_UNIT_DAMAGING')
DAMAGE_GLOBALS = ['trigger array dv_dmg_trig', 'integer dv_dmg_n = 0', 'group dv_dmg_seen = null',
                  'trigger dv_dmg_enter = null']
DAMAGE_FUNCTIONS = '''function dv_dmg_add_unit takes unit u returns nothing
    local integer i = 0
    if u == null or IsUnitInGroup(u, dv_dmg_seen) then
        return
    endif
    call GroupAddUnit(dv_dmg_seen, u)
    loop
        exitwhen i >= dv_dmg_n
        call TriggerRegisterUnitEvent(dv_dmg_trig[i], u, EVENT_UNIT_DAMAGED)
        set i = i + 1
    endloop
endfunction
function dv_dmg_on_enter takes nothing returns nothing
    call dv_dmg_add_unit(GetTriggerUnit())
endfunction
function dv_dmg_pick takes nothing returns nothing
    call dv_dmg_add_unit(GetEnumUnit())
endfunction
function dv_dmg_register_seen takes nothing returns nothing
    call TriggerRegisterUnitEvent(dv_dmg_trig[dv_dmg_n - 1], GetEnumUnit(), EVENT_UNIT_DAMAGED)
endfunction
function dv_dmg_register takes trigger t returns event
    local integer i = 0
    local group g
    loop
        exitwhen i >= dv_dmg_n
        if dv_dmg_trig[i] == t then
            return null
        endif
        set i = i + 1
    endloop
    if dv_dmg_seen == null then
        set dv_dmg_seen = CreateGroup()
    endif
    set dv_dmg_trig[dv_dmg_n] = t
    set dv_dmg_n = dv_dmg_n + 1
    call ForGroup(dv_dmg_seen, function dv_dmg_register_seen)
    if dv_dmg_enter == null then
        set dv_dmg_enter = CreateTrigger()
        call TriggerRegisterEnterRectSimple(dv_dmg_enter, GetWorldBounds())
        call TriggerAddAction(dv_dmg_enter, function dv_dmg_on_enter)
        set g = CreateGroup()
        call GroupEnumUnitsInRect(g, GetWorldBounds(), null)
        call ForGroup(g, function dv_dmg_pick)
        call DestroyGroup(g)
        set g = null
    endif
    return null
endfunction'''
RX_EVENT_REGISTRATION = re.compile(r'\b(TriggerRegisterAnyUnitEventBJ|TriggerRegisterPlayerUnitEvent)[ \t]*\(')


def damage_event(body_text):
    from doctor.fix import inflated_counts
    n = 0
    spans = _mask(body_text)
    out, p = [], 0
    for m in RX_EVENT_REGISTRATION.finditer(body_text):
        if m.start() < p or any(a <= m.start() < b for a, b in spans):
            continue
        args, end_pos = inflated_counts._jass_args(body_text, m.end() - 1)
        if not args:
            continue
        ev = args[1] if m.group(1) == 'TriggerRegisterAnyUnitEventBJ' else (args[2] if len(args) > 2 else '')
        if ev.strip() not in DAMAGE_EVENTS:
            continue
        out.append(body_text[p:m.start()])
        out.append('dv_dmg_register(%s)' % args[0])
        p = end_pos
        n += 1
    out.append(body_text[p:])
    return ''.join(out), n


def _mask(body_text):
    return [m.span() for m in RX_STRINGS_COMMENTS.finditer(body_text)]


def _replace_in_code(body_text, rx, fn):
    spans = _mask(body_text)
    out, p, k = [], 0, 0
    for m in rx.finditer(body_text):
        while k < len(spans) and spans[k][1] <= m.start():
            k += 1
        if k < len(spans) and spans[k][0] <= m.start() < spans[k][1]:
            continue
        out.append(body_text[p:m.start()])
        out.append(fn(m))
        p = m.end()
    out.append(body_text[p:])
    return ''.join(out)


RX_PLAYER_CALL = re.compile(r'\b(Player|ConvertedPlayer)[ \t]*\([ \t]*(\d+)[ \t]*\)')
NEUTRALS_24 = {24: 12, 25: 13, 26: 14, 27: 15}
RX_CAMERA_FIELD = re.compile(r'(?m)^[ \t]*(?:call[ \t]+)?CameraSetupSetField[ \t]*\([^\n]*?\b(CAMERA_FIELD_\w+)\b'
                             r'[^\n]*\n')


def without_camera_fields(body_text, origin, tgt):
    missing_items = set(n for n in origin.globals_block if n.startswith('CAMERA_FIELD_') and n not in tgt.globals_block)
    if not missing_items:
        return body_text, 0
    n = [0]

    def left_out(m):
        if m.group(1) not in missing_items:
            return m.group(0)
        n[0] += 1
        return ''
    return _replace_in_code(body_text, RX_CAMERA_FIELD, left_out), n[0]


def layer(body_text, source_dir, target_dir, source_player_slots=24, target_slots=12, camera_fields=False,
          hidden=False):
    origin, tgt = ruler(source_dir), ruler(target_dir)
    original = body_text
    nl = '\r\n' if '\r\n' in body_text else '\r' if '\r' in body_text else '\n'
    body_text = body_text.replace('\r\n', '\n').replace('\r', '\n')
    n_cam = 0
    if camera_fields:
        body_text, n_cam = without_camera_fields(body_text, origin, tgt)
    in_use, defined, _natives_declared = wc3_versions.script_names(body_text)
    missing = set()
    pend = [n for n in in_use if n not in defined and n not in tgt.name_list and n in origin.name_list]
    while pend:
        n = pend.pop()
        if n in missing:
            continue
        missing.add(n)
        for d in origin.dependencies(n):
            if d not in tgt.name_list and d in origin.name_list and d not in defined and d not in missing:
                pend.append(d)
    info = {'types': {}, 'emulated': [], 'neutrals': [], 'copied': [], 'w3p_constants': [], 'neutral_constants': [],
            'n_players': 0, 'cameras': n_cam}

    def target_type(t):
        seen = set()
        while t not in tgt.types and t not in BASIC_TYPES and t not in seen:
            seen.add(t)
            t = origin.types.get(t, 'handle')
        return t
    types = dict((t, target_type(t)) for t in sorted(missing) if t in origin.types)
    info['types'] = types
    rx_types = (
        re.compile(r'\b(%s)\b' % '|'.join(map(re.escape, sorted(types, key=len, reverse=True)))) if types else None
    )

    def with_types(s):
        return _replace_in_code(s, rx_types, lambda m: types[m.group(1)]) if rx_types else s
    declaradas = []
    mantidas = []

    def left_out(m):
        if m.group(1) in tgt.natives or m.group(1) in tgt.ai_natives:
            return m.group(0)
        if hidden and m.group(1) not in origin.natives and m.group(1) not in origin.ai_natives:
            mantidas.append(m.group(1))
            return m.group(0)
        declaradas.append((m.group(1), _params(m.group(2)), m.group(3)))
        return ''
    body_text = _replace_in_code(body_text, RX_MAP_NATIVE_DECL, left_out)
    info['damage'] = 0
    if any(e in missing for e in DAMAGE_EVENTS):
        body_text, info['damage'] = damage_event(body_text)
    used_after = _code_names(body_text)
    info['declaradas'] = [n for n, _p, _r in declaradas]
    info['hidden'] = sorted(set(mantidas))
    info['declared_used'] = [n for n, _p, _r in declaradas if n in used_after]
    globals_of_map = set()
    for block_entry in RX_GLOBALS.findall(_without_comments(body_text)):
        for ln in block_entry.split('\n'):
            m = RX_DECL_LINE.match(ln)
            if m:
                globals_of_map.add(m.group(4))
    g_lines = []
    done = set()
    for fname in sorted(
        (n for n in missing if n in origin.globals_block), key=lambda n: origin.globals_block[n]['order']
    ):
        g = origin.globals_block[fname]
        t = target_type(g['kind'])
        if g['array']:
            g_lines.append('%s array %s' % (t, fname))
        else:
            init = g['init']
            if init and not all(d in tgt.name_list or d in done for d in _code_names(init)):
                init = neutral_value(t)
                info['neutral_constants'].append(fname)
            elif init:
                init = with_types(init)
                info['w3p_constants'].append(fname)
            g_lines.append('%s%s %s%s' % ('constant ' if g['the_constant'] and init else '', t, fname,
                                          (' = ' + init) if init else ''))
        done.add(fname)
    f_lines = []
    if info['damage']:
        g_lines += DAMAGE_GLOBALS
        f_lines += DAMAGE_FUNCTIONS.split('\n')
    signatures = dict((n, origin.natives[n]) for n in missing if n in origin.natives)
    signatures.update((n, (ps, ret)) for n, ps, ret in declaradas if n in info['declared_used'])
    for fname in sorted(signatures):
        ps, ret = signatures[fname]
        ret_t = target_type(ret)
        args = ['dv_a%d' % i for i in range(len(ps))]
        header = 'function %s takes %s returns %s' % (
            fname, ', '.join('%s %s' % (target_type(t), a) for (t, _n), a in zip(ps, args)) or 'nothing', ret_t)
        body = EMULATED.get(fname)
        destr = _emulate_destructable(fname, ps, args, tgt)
        if destr:
            f_lines += [header] + ['    ' + c for c in destr] + ['endfunction']
            info['emulated'].append(fname)
        elif body and all(('{%d}' % i) not in ''.join(body) for i in range(len(ps), 10)):
            def place(c):
                for i, a_ in enumerate(args):
                    c = c.replace('{%d}' % i, a_)
                return '    ' + with_types(c)
            f_lines += [header] + [place(c) for c in body] + ['endfunction']
            info['emulated'].append(fname)
        else:
            f_lines += (
                [header] + (['    return %s' % neutral_value(ret_t)] if ret_t != 'nothing' else []) + ['endfunction']
            )
            info['neutrals'].append(fname)
    for fname in sorted((n for n in missing if n in origin.functions), key=lambda n: origin.functions[n]['order']):
        fx = origin.functions[fname]
        body = with_types(fx['body_text'])
        clashing = (set(n for _t, n in fx['params']) | set(RX_LOCAL.findall(body))) & globals_of_map
        if clashing:
            rx_c = re.compile(r'\b(%s)\b' % '|'.join(map(re.escape, sorted(clashing))))
            body = _replace_in_code(body, rx_c, lambda m: 'dv_' + m.group(1))
        f_lines += body.split('\n')
        info['copied'].append(fname)
    new = with_types(body_text)
    if source_player_slots > target_slots:
        def remap_neutral(m):
            n = int(m.group(2))
            base = n - 1 if m.group(1) == 'ConvertedPlayer' else n
            if base not in NEUTRALS_24:
                return m.group(0)
            info['n_players'] += 1
            return '%s(%d)' % (m.group(1), NEUTRALS_24[base] + (1 if m.group(1) == 'ConvertedPlayer' else 0))
        new = _replace_in_code(new, RX_PLAYER_CALL, remap_neutral)
    if not g_lines and not f_lines:
        if not (n_cam or declaradas or info['damage'] or info['n_players'] or types):
            return original, info
        return new.replace('\n', nl), info
    mark = '//' + ' Devo\'s Map Doctor: what this older game does not have (port to an older game)'
    m = re.search(r'(?m)^[ \t]*globals[ \t]*$', new)
    if m:
        end_pos = re.compile(r'(?m)^[ \t]*endglobals[ \t]*$').search(new, m.end())
        if not end_pos:
            raise Refusal('the script has a globals block without endglobals')
        g_start = new.index('\n', m.start()) + 1
        g_text = '\n'.join([mark] + g_lines) + '\n' if g_lines else ''
        new = new[:g_start] + g_text + new[g_start:]
        after_diag = end_pos.end() + len(g_text)
    else:
        new = ('\n'.join(['globals', mark] + g_lines + ['endglobals']) + '\n' if g_lines else '') + new
        after_diag = 0
    if f_lines:
        f = re.compile(r'(?m)^[ \t]*(?:constant[ \t]+)?function[ \t]').search(new, after_diag)
        pos = f.start() if f else len(new)
        new = new[:pos] + '\n'.join([mark] + f_lines) + '\n' + new[pos:]
    return new.replace('\n', nl), info


RX_LUA_NOISE = re.compile(r'--\[(=*)\[.*?\]\1\]|--[^\n]*|\[(=*)\[.*?\]\2\]|"(?:[^"\\\n]|\\.)*"|\'(?:[^\'\\\n]|\\.)*\'',
                          re.S)
RX_LUA_DEF = re.compile(r'(?m)^[ \t]*(?:function[ \t]+([A-Za-z_]\w*)[ \t]*\(|([A-Za-z_]\w*)[ \t]*=[^=])')
LUA_NEUTRAL = {'integer': '0', 'real': '0.0', 'boolean': 'false', 'string': '""'}


def _lua_names(body_text):
    clean = RX_LUA_NOISE.sub(' ', body_text)
    in_use = set(RX_IDENT.findall(clean))
    defined = set(a or b for a, b in RX_LUA_DEF.findall(clean))
    return in_use, defined


def _lua_line(c):
    c = c.strip()
    if c.startswith('call '):
        return c[5:]
    if c.startswith('return ') and not re.search(r'\b(?:set|local|loop|if)\b', c):
        return c
    return None


def lua_layer(body_text, source_dir, target_dir):
    origin, tgt = ruler(source_dir), ruler(target_dir)
    original = body_text
    nl = '\r\n' if '\r\n' in body_text else '\n'
    body_text = body_text.replace('\r\n', '\n')
    body_text, n_cam = without_camera_fields(body_text, origin, tgt)
    in_use, defined = _lua_names(body_text)
    missing = set()
    pend = [n for n in in_use if n not in defined and n not in tgt.name_list and n in origin.name_list]
    while pend:
        n = pend.pop()
        if n in missing:
            continue
        missing.add(n)
        for d in origin.dependencies(n):
            if d not in tgt.name_list and d in origin.name_list and d not in defined and d not in missing:
                pend.append(d)
    info = {
        'emulated': [],
        'neutrals': [],
        'copied': [],
        'w3p_constants': [],
        'neutral_constants': [],
        'cameras': n_cam,
    }
    line_list = []
    done = set()
    for fname in sorted(
        (n for n in missing if n in origin.globals_block), key=lambda n: origin.globals_block[n]['order']
    ):
        g = origin.globals_block[fname]
        init = g['init']
        if g['array']:
            field_value = '{}'
        elif init and re.match(r'^[\w().,\s+\-]*$', init) and all(d in tgt.name_list or d in done or
                                                                   re.match(r'^\d', d) for d in _code_names(init)):
            field_value = re.sub(r'\bnull\b', 'nil', init)
            info['w3p_constants'].append(fname)
        else:
            field_value = LUA_NEUTRAL.get(g['kind'], 'nil')
            info['neutral_constants'].append(fname)
        line_list.append('if %s == nil then %s = %s end' % (fname, fname, field_value))
        done.add(fname)
    for fname in sorted(n for n in missing if n in origin.natives):
        ps, ret = origin.natives[fname]
        args = ['a%d' % i for i in range(len(ps))]
        body = None
        destr = _emulate_destructable(fname, ps, args, tgt)
        source = destr or EMULATED.get(fname)
        if source and len(source) == 1 and all(('{%d}' % i) not in source[0] for i in range(len(ps), 10)):
            c = source[0]
            for i, a_ in enumerate(args):
                c = c.replace('{%d}' % i, a_)
            body = _lua_line(c)
        if body:
            info['emulated'].append(fname)
        else:
            body = ('return %s' % LUA_NEUTRAL.get(ret, 'nil')) if ret != 'nothing' else ''
            info['neutrals'].append(fname)
        line_list.append('if %s == nil then %s = function(%s) %s end end' % (fname, fname, ', '.join(args), body))
    for fname in sorted((n for n in missing if n in origin.functions), key=lambda n: origin.functions[n]['order']):
        fx = origin.functions[fname]
        args = [n for _t, n in fx['params']]
        body = ('return %s' % LUA_NEUTRAL.get(fx['ret'], 'nil')) if fx['ret'] != 'nothing' else ''
        line_list.append('if %s == nil then %s = function(%s) %s end end' % (fname, fname, ', '.join(args), body))
        info['neutrals'].append(fname)
    if not line_list:
        return (body_text.replace('\n', nl) if n_cam else original), info
    mark = '-- Devo\'s Map Doctor: what this older game does not have (port to an older game)'
    new = '\n'.join([mark] + line_list + ['-- end of what this older game does not have']) + '\n' + body_text
    return new.replace('\n', nl), info


def lua_compiles(body_text):
    try:
        from doctor.script import lua_ast
    except ImportError:
        return None
    try:
        lua_ast.parse(body_text)
        return None
    except Exception as e:
        return str(e)[:200]


RX_PJASS_ERROR_LINE = re.compile(r'^[^:\n]+:\d+:\s*')


def _without_line(err):
    return RX_PJASS_ERROR_LINE.sub('', str(err)).strip()


def _read(a, name_list):
    for n in name_list:
        try:
            d = a.read(n)
        except Exception:
            d = None
        if d is not None:
            return n, d
    return None, None


def _replace_in_place(output, fn):
    tmp = os.path.splitext(output)[0] + '.etapa' + os.path.splitext(output)[1]
    try:
        r = fn(output, tmp)
        os.replace(tmp, output)
        return r
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def complete_listfile(output):
    from doctor.fix import unprotect
    from doctor.models import model_check
    from doctor.mpq import mpqadd
    a, _err = model_check._open(output)
    if a is None:
        return 0
    with unprotect.quiet():
        if unprotect._listfile_status(a)['status'] == 'ok':
            return 0
        matches = unprotect.map_names(a)
    try:
        lst = (a.read('(listfile)') or b'').decode('utf-8', 'surrogateescape')
    except Exception:
        lst = ''
    name_list = [n for n in re.split('[\r\n]+', lst) if n.strip()]
    seen = set(n.lower() for n in name_list)
    new_ones = []
    for n in matches:
        if n.lower() in seen or n.startswith('('):
            continue
        try:
            if unprotect._read(a, n) is not None:
                new_ones.append(n)
                seen.add(n.lower())
        except Exception:
            continue
    if new_ones:
        try:
            mpqadd.add_files(
                output,
                [('(listfile)', '\r\n'.join(name_list + new_ones).encode('utf-8', 'surrogateescape') + b'\r\n')],
                log=lambda *x: None,
            )
        except SystemExit:
            return 0
    return len(new_ones)


def models_800(entry, output):
    import shutil
    from doctor.models import mdx_800
    from doctor.models import model_check
    from doctor.mpq import mpqadd
    shutil.copyfile(entry, output)
    out = {'converted': 0, 'rejected': {}}
    a, _err = model_check._open(entry)
    if a is None:
        return out
    write_out = []
    for fname, _bi, data_bytes in model_check._models(a, model_check._names(a), lambda *x: None):
        v = model_check.model_version(data_bytes) if data_bytes and fname.lower().endswith('.mdx') else None
        if not v or v <= 800:
            continue
        try:
            new, _info = mdx_800.convert(data_bytes)
        except Exception as e:
            out['rejected'][fname] = (v, str(e)[:100])
            continue
        write_out.append((fname, new))
    if write_out:
        mpqadd.add_files(output, write_out, log=lambda *x: None)
    out['converted'] = len(write_out)
    return out


def media_step(output, tgt, warnings, log=print):
    from doctor.fix import downgrade
    k = wc3_versions._key(tgt)
    out = {}
    complete_listfile(output)
    if k < downgrade.FIRST_PATCH['model']:
        r = _replace_in_place(output, models_800)
        if r['converted']:
            out['models'] = r['converted']
        warnings += [
            'the model %s was left in version %s (%s)' % (n, v, e) for n, (v, e) in sorted(r['rejected'].items())
        ]
    if k < downgrade.FIRST_PATCH['dds']:
        from doctor.models import dds_to_blp
        try:
            r = _replace_in_place(output, lambda e, s: dds_to_blp.converte(e, s, log=lambda *x: None))
            if r.get('replaced'):
                out['dds'] = r['replaced']
        except SystemExit as e:
            warnings.append('the DDS textures were left as they are (%s)' % str(e.code)[:150])
    types = tuple(t for t in ('flac', 'ogg') if k < downgrade.FIRST_PATCH[t])
    if types:
        from doctor.models import classic_sound
        try:
            r = _replace_in_place(output, lambda e, s: classic_sound.converte(e, s, log=lambda *x: None, types=types))
            if r.get('replaced'):
                out['sounds'] = r['replaced']
            if r.get('no_ffmpeg'):
                warnings.append('%d FLAC/OGG sound(s) were left as they are: converting them to MP3 needs ffmpeg'
                                % r['sounds'])
        except SystemExit as e:
            warnings.append('the FLAC/OGG sounds were left as they are (%s)' % str(e.code)[:150])
    return out


def source_dir(detail):
    if detail.get('range') == '1.30+':
        return os.path.join(os.path.dirname(HERE), 'ref', '3.0')
    folder = wc3_versions.scripts_dir(detail.get('version') or '1.24a')
    return folder or os.path.join(os.path.dirname(HERE), 'ref', '3.0')


def port_down(map_path, tgt, output, an, log=print):
    from doctor.fix import downgrade
    from doctor.mpq import mpqread
    from doctor.port import map_path as _map_mod
    detail = an['origin']
    lim = wc3_versions.limits(tgt) or {}
    game = wc3_versions.reforged_game(tgt)
    if wc3_versions.is_reforged(tgt) and not game:
        raise Refusal('the data of Warcraft III %s (common/ref, game.json) are not in this program' % tgt)
    a = mpqread.Archive(map_path)
    j_name, j = _read(a, ('war3map.j', 'scripts' + B + 'war3map.j'))
    lua_name, lua = _read(a, ('war3map.lua',)) if game else (None, None)
    if j is None and lua is None:
        raise Refusal('the map has no war3map.j that can be read (a Lua script only runs on 1.31 and later)')
    _nb, blizz = _read(a, ('scripts' + B + 'blizzard.j',))
    chg, warnings, new_ones, to_delete = {}, [], [], []
    w3i_b = _read(a, ('war3map.w3i',))[1]
    if w3i_b is None:
        raise Refusal('the map has no war3map.w3i')
    try:
        new_w3i, plain_name = downgrade.downgrade_w3i(w3i_b, tgt)
    except downgrade.Refused as e:
        raise Refusal(str(e))
    except ValueError as e:
        raise Refusal('the map info: %s' % e)
    except Exception as e:
        raise Refusal('the map info does not read (%s): a protected map? Unprotect it first with Fix map, then port'
                      % str(e)[:80])
    if new_w3i != w3i_b:
        new_ones.append(('war3map.w3i', new_w3i))
    chg['w3i'] = {
        'from_': plain_name['from'],
        'new_value': plain_name['target'] if new_w3i != w3i_b else plain_name['from'],
        'flags': plain_name['cleared_flags'],
        'fields': sorted(set(plain_name['dropped'])),
    }
    warnings += plain_name['warnings']
    source_slots = 24 if detail.get('range') in ('1.29', '1.30+') else 12
    if lua is not None:
        body_text = lua.decode('utf-8', 'surrogateescape')
        new_text, info = lua_layer(body_text, source_dir(detail), wc3_versions.scripts_dir(tgt))
        err = lua_compiles(new_text)
        if err:
            raise Refusal('the Lua script does not read after the port: %s' % err)
        chg['script'] = dict(info, lua=True)
        new_b = new_text.encode('utf-8', 'surrogateescape')
        pj = {'lua': True}
        if new_b != lua:
            new_ones.append((lua_name, new_b))
    else:
        body_text = j.decode('latin-1')
        new_text, info = layer(body_text, source_dir(detail), wc3_versions.scripts_dir(tgt), source_slots,
                               lim.get('players', 12), camera_fields=bool(game), hidden=bool(game))
        if info.get('hidden'):
            warnings.append(
                'the map declares %d native(s) no common.j has (hidden natives of the game): %s. They stay: '
                'if %s does not have one, it refuses the map'
                % (len(info['hidden']), ', '.join(info['hidden'][:8]), tgt)
            )
        if not game:
            from doctor.port import return_fixes
            new_text, _r = return_fixes.applies(new_text)
        chg['script'] = info
        new_b = new_text.encode('latin-1')
        pj = wc3_versions.pjass_check(new_b, tgt, own_blizzard=blizz)
    script_text = body_text
    if lua is not None:
        pass
    elif pj.get('skipped'):
        warnings.append('pjass was not run (%s)' % pj['skipped'])
    elif pj.get('rc') != 0 or pj.get('errors'):
        orig = wc3_versions.pjass_check(
            j, detail.get('version') if detail.get('range') != '1.30+' else wc3_versions.REFORGED, own_blizzard=blizz
        )
        existing = set(_without_line(e) for e in orig.get('errors') or [] if RX_PJASS_ERROR_LINE.match(str(e)))
        new_errors = [
            e for e in pj.get('errors') or [] if RX_PJASS_ERROR_LINE.match(str(e)) and _without_line(e) not in existing
        ]
        if new_errors or not any(RX_PJASS_ERROR_LINE.match(str(e)) for e in pj.get('errors') or []):
            raise Refusal('the script does not compile on %s after the port: %s'
                          % (tgt, '; '.join(str(e) for e in (new_errors or pj.get('errors') or [])[:5])
                             or 'rc %s' % pj.get('rc')))
        warnings.append('pjass finds in the script what it already found in the original (%d): %s'
                        % (len(existing), '; '.join(sorted(existing))[:300]))
        pj = dict(pj, in_original=sorted(existing))
    if lua is None and new_b != j:
        new_ones.append((j_name, new_b))
    objects = {}
    for k in downgrade.OBJECT_KINDS:
        for n in ('war3map.' + k, 'war3mapSkin.' + k):
            d = _read(a, (n,))[1]
            if d is not None:
                objects[n] = d
    try:
        if game:
            obj_new, obj_info = downgrade.downgrade_objects_reforged(objects, game)
        else:
            obj_new, obj_info = downgrade.downgrade_objects(objects)
    except ValueError as e:
        raise Refusal('the object data: %s' % e)
    for n, d in sorted(obj_new.items()):
        if d is None:
            to_delete.append(n)
        else:
            new_ones.append((n, d))
    if game:
        chg['reforged_objects'] = obj_info
        bases = sorted(
            set((new_object_id, base) for r in obj_info.values() for new_object_id, base in r['unknown_bases'])
        )
        if bases:
            warnings.append('%d object(s) of the map are based on objects that %s does not have (they will not work '
                            'there): %s' % (len(bases), tgt, ', '.join(('%s (%s)' % (n_, b_)) if n_ else b_
                                                                        for n_, b_ in bases[:12]) +
                                            (', ...' if len(bases) > 12 else '')))
    else:
        chg['objects'] = obj_info
    doo = _read(a, ('war3map.doo',))[1]
    if doo is not None:
        try:
            doo_new, doo_info = downgrade.downgrade_doo(doo, keep_skin=bool(game))
        except ValueError as e:
            doo_new, doo_info = doo, None
            warnings.append('war3map.doo was left as it is (%s): if it is in a newer layout, %s will not show the '
                            'doodads' % (e, tgt))
        if doo_new != doo:
            new_ones.append(('war3map.doo', doo_new))
            chg['doo'] = doo_info
    w3e = _read(a, ('war3map.w3e',))[1] if not game else None
    if w3e is not None:
        try:
            w3e_new, w3e_info = downgrade.downgrade_w3e(w3e)
        except ValueError as e:
            raise Refusal('the terrain: %s' % e)
        if w3e_new != w3e:
            new_ones.append(('war3map.w3e', w3e_new))
            chg['w3e'] = w3e_info
    ed = dict((n, d) for n, d in ((n, _read(a, (n,))[1]) for n in ('war3map.w3s', 'war3map.w3c', 'war3map.w3r',
                                                                   'war3mapUnits.doo')) if d is not None)
    ed_new, ed_done, ed_left = downgrade.downgrade_editor_files(ed, source_slots > lim.get('players', 12),
                                                                reforged=bool(game))
    new_ones += sorted(ed_new.items())
    if ed_done:
        chg['editor'] = ed_done
    warnings += ['%s was left as it is (%s): the World Editor of %s may not read it' % (n, e, tgt)
                 for n, e in sorted(ed_left.items())]
    wtg_b, wct_b = _read(a, ('war3map.wtg',))[1], _read(a, ('war3map.wct',))[1]
    if wtg_b:
        if getattr(sys, 'frozen', False):
            wc3_versions.ensure(lambda s: None)
        try:
            trig_pair = downgrade.downgrade_triggers(wtg_b, wct_b, tgt)
        except Exception as e:
            trig_pair = None
            warnings.append('the triggers were left as they are (%s): the World Editor of %s may not read them '
                            '(Fix map, Open in World Editor rebuilds them for that editor)' % (str(e)[:120], tgt))
        if trig_pair:
            new_ones += [('war3map.wtg', trig_pair[0]), ('war3map.wct', trig_pair[1])]
            chg['trigger_list'] = trig_pair[2]
    if game:
        def rd(n):
            return _read(a, (n,))[1]
        tally = downgrade.reforged_content(rd, game, script_text)
        chg['content'] = tally
        for hash_key, label in (('doodads', 'doodad/destructable type(s) placed on the map'),
                                ('units', 'unit/item type(s) placed on the map'),
                                ('terrain', 'ground or cliff tile(s) of the terrain'),
                                ('weather', 'weather effect(s) the script creates'),
                                ('files', 'game file(s) the map cites')):
            if tally.get(hash_key):
                warnings.append('%d %s that %s does not have (they will be missing there): %s' % (
                    len(tally[hash_key]), label, tgt, ', '.join(tally[hash_key][:10]) +
                    (', ...' if len(tally[hash_key]) > 10 else '')))
    log('port to %s (older): %d file(s) rewritten, %d removed' % (tgt, len(new_ones), len(to_delete)))
    _map_mod.attach(map_path, output, new_ones, to_delete=to_delete, log=lambda s: None)
    if not game:
        chg.update(media_step(output, tgt, warnings, log))
    for it in downgrade.media_items(output, tgt):
        warnings.append(it['text'])
    try:
        editor = downgrade.remaining(output, tgt)
    except Exception:
        editor = []
    return {
        'changes': chg,
        'warnings': warnings,
        'pjass': pj,
        'file_set': [n for n, _d in new_ones],
        'deleted_slots': to_delete,
        'editor': ['%s: %s' % (c, t) for c, t in editor],
    }
