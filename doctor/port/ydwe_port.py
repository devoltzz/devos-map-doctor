# The Lua route of the port: a YDWE Lua engine map becomes a Reforged Lua map (the JASS transpiled, the engine runtime, the modules translated).
import os
import re
import sys


HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(os.path.dirname(HERE), 'ref', '3.0')
TYPE_CODE = {'integer': 'I', 'real': 'R', 'string': 'S', 'boolean': 'B', 'code': 'C', 'nothing': 'V'}
RX_NATIVE = re.compile(r'(?m)^[ \t]*(?:constant[ \t]+)?native[ \t]+([A-Za-z_]\w*)[ \t]+takes\b[^\n]*')
RX_DEF = re.compile(r'(?m)^[ \t]*(?:constant[ \t]+)?(?:native|function)[ \t]+([A-Za-z_]\w*)[ \t]+takes\b')
ROOT_CREATORS = ('InitHashtable', 'CreateTrigger', 'CreateGroup', 'CreateTimer', 'Location', 'Rect', 'CreateForce',
                 'CreateRegion', 'Condition', 'Filter', 'DialogCreate', 'CreateTimerDialog', 'CreateMultiboard',
                 'CreateLeaderboard', 'CreateQuest', 'InitGameCache', 'CreateSound', 'CreateSoundFromLabel',
                 'CreateMIDISound', 'CreateUnit', 'CreateItem', 'CreateFogModifierRect', 'CreateImage',
                 'CreateTextTag')


def _ref(fname):
    try:
        from doctor.port import new
        return os.path.join(new.REF, fname)
    except Exception:
        return os.path.join(REF, fname)


def _route_data(*pieces):
    cands = [os.path.join(HERE, *pieces), os.path.join(HERE, pieces[-1])]
    if getattr(sys, '_MEIPASS', None):
        cands.append(os.path.join(sys._MEIPASS, pieces[-1]))
    return next((c for c in cands if os.path.isfile(c)), cands[0])


def hash_key(fname):
    return re.sub('[A-Z]', lambda m: m.group(0).lower(), fname.replace('/', '\\'))


def _read(p):
    return open(p, 'rb').read().decode('utf-8', 'surrogateescape')


def _lua_str(s):
    from doctor.script import jass2lua
    return jass2lua.lua_string(s)


def _long_string(body_text):
    body_text = body_text + '\n'
    n = 0
    while (']' + '=' * n + ']') in body_text:
        n += 1
    return '[' + '=' * n + '[\n' + body_text + ']' + '=' * n + ']'


def platform_natives():
    out = {}
    for m in RX_NATIVE.finditer(_read(_route_data('..', 'script', 'kk_natives.j'))):
        out.setdefault(m.group(1), m.group(0).strip())
    import glob
    for p in sorted(glob.glob(os.path.join(HERE, 'compat', '*.j'))):
        for m in re.finditer(
            r'(?m)^[ \t]*function[ \t]+((?:Dz|EX|YDWE|KK|JN)\w*)[ \t]+(takes\b[^\n]*?returns[ \t]+\w+)', _read(p)
        ):
            out.setdefault(m.group(1), 'native %s %s' % (m.group(1), m.group(2).strip()))
    return out


def cited_names(lua_modules):
    from doctor.script import lua_bytecode
    out = set()
    for m in lua_modules.values():
        if m['forma'] == 'bytecode':
            try:
                fn, _ = lua_bytecode.load(m['data_bytes'])
            except Exception:
                continue
            out.update(c.decode('latin-1') for c in lua_bytecode.strings(fn) if re.match(rb'^[A-Za-z_]\w{2,60}$', c))
        else:
            out.update(re.findall(r'\b([A-Za-z_]\w{2,60})\b', m['data_bytes'].decode('utf-8', 'replace')))
    return out


def declare_natives(body_text, lua_modules, log=None):
    log = log or (lambda s: None)
    plat = platform_natives()
    existing = set(RX_DEF.findall(body_text)) | set(RX_DEF.findall(_read(_ref('common.j'))))
    existing |= set(RX_DEF.findall(_read(_ref('blizzard.j'))))
    added = sorted(n for n in cited_names(lua_modules) if n in plat and n not in existing)
    if not added:
        return body_text, []
    block_entry = '\n'.join(plat[n] for n in added) + '\n'
    m = re.search(r'(?m)^[ \t]*endglobals\b[^\n]*\n', body_text)
    if m:
        body_text = body_text[:m.end()] + block_entry + body_text[m.end():]
    else:
        m = re.search(r'(?m)^[ \t]*(?:constant[ \t]+)?function[ \t]', body_text)
        i = m.start() if m else len(body_text)
        body_text = body_text[:i] + block_entry + body_text[i:]
    log('   %d platform native(s) the Lua calls declared for the layer' % len(added))
    return body_text, added


def blizzard_globals():
    t = _read(_ref('blizzard.j'))
    m = re.search(r'(?ms)^[ \t]*globals[ \t]*$(.*?)^[ \t]*endglobals', t)
    name_list = set()
    for line in (m.group(1).split('\n') if m else []):
        line = line.split('//')[0].strip()
        mm = re.match(r'^(?:constant\s+)?\w+\s+(?:array\s+)?([A-Za-z_]\w*)', line)
        if mm:
            name_list.add(mm.group(1))
    return name_list


def pin_root(lua_globals):
    default_value = re.compile(r'^([ \t]*)([A-Za-z_][A-Za-z0-9_]*(?:\[[^\]]+\])?)[ \t]*=[ \t]*(' +
                               '|'.join(ROOT_CREATORS) + r')\(')
    output = []
    for ln in lua_globals.split('\n'):
        output.append(ln)
        m = default_value.match(ln)
        if m:
            output.append('%s__fixa_raiz(%s)' % (m.group(1), m.group(2)))
    return '\n'.join(output)


RX_GLOBAL_CALL = re.compile(r'(?<![\w.:])([A-Za-z_][A-Za-z0-9_]*)[ \t]*\(')
RX_LUA_NAME = re.compile(r'[A-Za-z_][A-Za-z0-9_]*')


def defer_initials(lua_globals):
    root, deferred_ones, name_list = [], [], set()
    last_unit = root
    for ln in lua_globals.split('\n'):
        if ln.strip() and not re.match(r'^[ \t]*[A-Za-z_][A-Za-z0-9_]*(?:\[[^\]]*\])?[ \t]*(?:=|\()', ln):
            last_unit.append(ln)
            continue
        calls = [c for c in RX_GLOBAL_CALL.findall(ln) if not c.startswith('__arr_')]
        if calls or (name_list and any(n in name_list for n in RX_LUA_NAME.findall(ln))):
            last_unit = deferred_ones
            deferred_ones.append(ln)
            m = re.match(r'^[ \t]*([A-Za-z_][A-Za-z0-9_]*)', ln)
            if m:
                name_list.add(m.group(1))
        else:
            last_unit = root
            root.append(ln)
    return '\n'.join(root), '\n'.join(deferred_ones)


RX_FUNCTION = re.compile(
    r'(?m)^[ \t]*(?:constant[ \t]+)?function[ \t]+(\w+)[ \t]+takes[^\n]*\n((?:(?![ \t]*endfunction\b)'
    r'[^\n]*\n)*?)[ \t]*endfunction'
)
RX_MARK_LINE = re.compile(r'^(?:call\s+GetTriggeringTrigger\s*\(\s*\)|return\b.*)$')
RX_NEUTRAL_RETURN = re.compile(r'^return(?:\s+(?:0|0\.0*|\.0+|null|false|""))?$')
RX_JAPI_FAMILY = re.compile(r'^(?:Frame|EX|Get(?:Game|Glue)UI|CreateFrame|CreateSimpleFrame|DestroyFrame)')


def markers(final_j):
    defs = set(m.group(1) for m in RX_FUNCTION.finditer(final_j))
    out = {}
    for m in RX_FUNCTION.finditer(final_j):
        body = [line.strip() for line in m.group(2).split('\n') if line.strip() and not line.strip().startswith('//')]
        n = m.group(1)
        tgt = next((a for a in ('kkc_' + n, 'Dz' + n) if a in defs), None)
        if body and re.match(r'^call\s+GetTriggeringTrigger\s*\(\s*\)$', body[0]):
            if all(RX_MARK_LINE.match(line) for line in body):
                out[n] = tgt
        elif all(RX_NEUTRAL_RETURN.match(line) for line in body) and (tgt or RX_JAPI_FAMILY.match(n)):
            out[n] = tgt
    return out


def link_markers(mark_map):
    line_list = ['__ydwe_marcadores = {']
    line_list += ['[%s]=%s,' % (_lua_str(n), _lua_str(a) if a else 'false') for n, a in sorted(mark_map.items())]
    line_list += ['}', '''for n, alvo in pairs(__ydwe_marcadores) do
  local f = rawget(JENV, n)
  if alvo and type(rawget(JENV, alvo)) == "function" then
    rawset(JENV, n, rawget(JENV, alvo))
  elseif __ydwe_japi_extra[n] then
    rawset(JENV, n, __ydwe_japi_extra[n])
  elseif type(f) == "function" then
    rawset(JENV, n, function(...)
      local k = "marcador." .. n
      __ydwe_ausente[k] = (__ydwe_ausente[k] or 0) + 1
      return f(...)
    end)
  end
end''']
    return '\n'.join(line_list) + '\n'


RX_LONG_BRACKET = re.compile(rb'\[(=*)\[')


def _non_ascii_ids(body_text):
    out = []
    i, n = 0, len(body_text)
    while i < n:
        c = body_text[i]
        if c == 0x2D and body_text[i + 1:i + 2] == b'-':
            m = RX_LONG_BRACKET.match(body_text, i + 2)
            if m:
                end_pos = body_text.find(b']' + m.group(1) + b']', m.end())
                i = n if end_pos < 0 else end_pos + len(m.group(1)) + 2
            else:
                end_pos = body_text.find(b'\n', i)
                i = n if end_pos < 0 else end_pos + 1
        elif c in (0x22, 0x27):
            j = i + 1
            while j < n and body_text[j] != c:
                j += 2 if body_text[j] == 0x5C else 1
            i = j + 1
        elif c == 0x5B and RX_LONG_BRACKET.match(body_text, i):
            m = RX_LONG_BRACKET.match(body_text, i)
            end_pos = body_text.find(b']' + m.group(1) + b']', m.end())
            i = n if end_pos < 0 else end_pos + len(m.group(1)) + 2
        elif c == 0x5F or 0x41 <= c <= 0x5A or 0x61 <= c <= 0x7A or c >= 0x80:
            j = i
            while j < n and (body_text[j] == 0x5F or 0x30 <= body_text[j] <= 0x39 or 0x41 <= body_text[j] <= 0x5A
                             or 0x61 <= body_text[j] <= 0x7A or body_text[j] >= 0x80):
                j += 1
            if any(b >= 0x80 for b in body_text[i:j]):
                out.append((i, j))
            i = j
        elif 0x30 <= c <= 0x39:
            j = i
            while j < n and (body_text[j:j + 1].isalnum() or body_text[j] in b'._'):
                j += 1
            i = j
        else:
            i += 1
    return out


def utf8_text_to_source(data_bytes, fname):
    from doctor.script import lua53_translate
    body_text = data_bytes[3:] if data_bytes[:3] == b'\xef\xbb\xbf' else data_bytes
    if not has_lua() or _compile_check(body_text.decode('utf-8', 'surrogateescape')):
        return None
    segments = _non_ascii_ids(body_text)
    if not segments:
        return None
    mark, name_list, pieces, end_pos = {}, {}, [], 0
    for i, j in segments:
        ident = body_text[i:j]
        if ident not in mark:
            mark[ident] = b'__ydwe_u%d__' % len(mark)
            name_list[mark[ident].decode()] = ident
        pieces += [body_text[end_pos:i], mark[ident]]
        end_pos = j
    pieces.append(body_text[end_pos:])
    new = b''.join(pieces)
    L = _runtime()
    dump = L.eval('function(s) local f = load(s, "=m", "t") if not f then return nil end return string.dump(f) end')
    bc = dump(new)
    if bc is None:
        return None
    src = lua53_translate.translate(bytes(bc), fname)
    for m, ident in name_list.items():
        src = src.replace('"%s"' % m, lua53_translate.literal(ident))
    return src


def translate_modules(lua_modules, log=None):
    from doctor.script import lua53_translate
    out, error_list = [], []
    for fname, m in sorted(lua_modules.items()):
        k = hash_key(fname)
        if m['forma'] == 'bytecode':
            try:
                src = lua53_translate.translate(m['data_bytes'], fname)
            except Exception as e:
                error_list.append('%s: %s' % (fname, e))
                continue
            out.append((k, 'b', src))
        else:
            try:
                src = utf8_text_to_source(m['data_bytes'], fname)
            except Exception as e:
                error_list.append('%s: %s' % (fname, e))
                src = None
            if src is not None:
                out.append((k, 'b', src))
            else:
                out.append((k, 't', m['data_bytes'].decode('utf-8', 'surrogateescape').lstrip('﻿')))
    if log:
        log('   %d module(s) translated to Lua source (%.1f MB), %d failed'
            % (len(out), sum(len(s) for _c, _f, s in out) / 1048576.0, len(error_list)))
    return out, error_list


def _start(body_text, out):
    sec = None
    for ln in body_text.splitlines():
        line = ln.strip()
        if not line or line.startswith('//') or line.startswith(';'):
            continue
        m = re.match(r'^\[(.+)\]$', line)
        if m:
            sec = out.setdefault(m.group(1), {})
        elif sec is not None and '=' in line:
            k, v = line.split('=', 1)
            sec[re.sub('[A-Z]', lambda c: c.group(0).lower(), k.strip())] = v.strip()
    return out


def misc_lua(extract=None, log=None):
    sections = {}
    try:
        from doctor.data import objects
        base = objects.GameBase()
        for details in ('units\\miscdata.txt', 'units\\miscgame.txt'):
            cpath = base.resolve(details)
            if cpath:
                _start(base.read_data(cpath).decode('utf-8', 'surrogateescape').lstrip('﻿'), sections)
    except Exception as e:
        if log:
            log('   jass.slk misc: the game data could not be read (%s: %s)' % (type(e).__name__, e))
    p = extract and os.path.join(extract, 'war3mapMisc.txt')
    if p and os.path.isfile(p):
        _start(_read(p).lstrip('﻿'), sections)
    if not sections:
        return ''
    line_list = ['__slk_raw = __slk_raw or {}', '__slk_raw.misc = {']
    for sec, fields in sorted(sections.items()):
        line_list.append('[%s]={%s},' % (_lua_str(sec), ','.join('[%s]=%s' % (_lua_str(k), _lua_str(v))
                                                          for k, v in sorted(fields.items()))))
    line_list.append('}')
    return '\n'.join(line_list) + '\n'


def build_lua(final_j, collect, slk_lua='', log=None, extract=None, scale_factors=None, translation=None, stubs=None):
    from doctor.script import jass2lua
    log = log or (lambda s: None)
    tr = jass2lua.Transpiler(_read(_ref('common.j')), _read(_ref('blizzard.j')), final_j)
    res = tr.run()
    log('   JASS -> Lua: %d function(s), %d EXExecuteScript literal(s), %d embedded Lua chunk(s), %d warning(s)'
        % (len(res['func_names']), len(res['exs_literals']), len(res['luachunks']), len(res['warnings'])))
    sig = ['__sig = {']
    for fname, (params, ret) in sorted(tr.sigs.items()):
        sig.append(
            '[%s]="%s|%s",'
            % (_lua_str(fname), TYPE_CODE.get(ret, 'H'), ','.join(TYPE_CODE.get(p, 'H') for p in params))
        )
    sig.append('}')
    conv = dict(
        (m.group(2), m.group(1))
        for m in re.finditer(
            r'(?m)^\s*(?:constant\s+)?native\s+(Convert\w+)\s+takes\s+integer\s+\w+\s+returns\s+(\w+)',
            _read(_ref('common.j')),
        )
    )
    sig.append('__sig_enum = {')
    for fname, (params, ret) in sorted(tr.sigs.items()):
        pos = ['[%d]="%s"' % (i + 1, conv[p]) for i, p in enumerate(params) if p in conv]
        if ret in conv:
            pos.append('ret=true')
        if pos:
            sig.append('[%s]={%s},' % (_lua_str(fname), ','.join(pos)))
    sig.append('}')
    enum_globals = sorted(set(m.group(2) for m in re.finditer(r'(?m)^\s*constant\s+(\w+)\s+(\w+)\s*=',
                                                               _read(_ref('common.j'))) if m.group(1) in conv))
    sig.append('__enum_globais = {%s}' % ', '.join('[%s]=true' % _lua_str(n) for n in enum_globals))
    hg = ['__handle_globals = {'] + ['[%s]=%s,' % (_lua_str(k), _lua_str(v))
                                     for k, v in sorted(res['handle_globals'].items())] + ['}']
    arrays = sorted(g.name for g in tr.prog.globals if g.is_array and g.type not in jass2lua.PRIMITIVES)
    ha = ['__handle_arrays = {'] + ['[%s]=true,' % _lua_str(n) for n in arrays] + ['}']
    translated, error_list = translate_modules(collect['lua_modules'], log)
    sources = ['__ydwe_fonte, __ydwe_forma, __ydwe_dados = {}, {}, {}']
    for k, forma, src in translated:
        sources.append('__ydwe_forma[%s] = "%s"' % (_lua_str(k), forma))
        sources.append('__ydwe_fonte[%s] = %s' % (_lua_str(k), _long_string(src)))
    for fname, data_bytes in sorted(collect.get('file_set', {}).items()):
        sources.append('__ydwe_dados[%s] = %s' % (_lua_str(hash_key(fname)),
                                                  _lua_str(data_bytes.decode('utf-8', 'surrogateescape'))))
    sources.append('__ydwe_moldes = {%s}' % ', '.join(_lua_str(m) for m in collect.get('templates', ())))
    defined_ones = set(re.findall(r'(?m)^[ \t]*function[ \t]+(\w+)[ \t]+takes\b', final_j))
    sources.append('__ydwe_plataforma = {%s}' % ', '.join(
        '[%s]=true' % _lua_str(n) for n in sorted(set(platform_natives()) & defined_ones)))
    sources.append('__ydwe_stubs = {%s}' % ', '.join('[%s]=true' % _lua_str(n) for n in sorted(set(stubs or ()))))
    sources.append('__ydwe_original = {%s}' % ', '.join(
        '[%s] = {%s, %s}' % (_lua_str(hash_key(n)), _lua_str(s1), _lua_str(m5))
        for n, (s1, m5) in sorted((collect.get('originals') or {}).items())))
    segments = ['__exs_fn, __luachunk_fn = {}, {}', 'do', 'local __EF, __LF = __exs_fn, __luachunk_fn',
                'local _ENV = __LENV']
    invalid_count = 0
    for tab, listing in (('__EF', res['exs_literals']), ('__LF', res['luachunks'])):
        for i, c in enumerate(listing):
            if _compile_check('return ' + c):
                segments.append('%s[%d] = function()\nreturn %s\nend' % (tab, i, c))
            elif _compile_check(c):
                segments.append('%s[%d] = function()\n%s\nend' % (tab, i, c))
            else:
                invalid_count += 1
                segments.append('%s[%d] = function() return nil end' % (tab, i))
    if invalid_count:
        log('   %d EXExecuteScript text(s) that are not valid Lua (the old engine did not run them either)'
            % invalid_count)
    segments.append('end')
    bj = sorted(blizzard_globals())
    g_root, g_deferred = defer_initials(pin_root(res['lua_globals']))
    pieces = [
        '-- war3map.lua: port of a YDWE Lua engine map (Devo\'s Map Doctor)\n',
        '\n'.join(sig), '\n', '\n'.join(hg), '\n', '\n'.join(ha), '\n',
        slk_lua or '__slk_raw = {}\n', '\n', misc_lua(extract, log), '\n',
        _read(_route_data('simulator', 'rt_core.lua')), '\n',
        '\n'.join(sources), '\n',
        '__ydwe_i32 = {%s}\n' % ', '.join('%s = %r' % (d, float(f)) for d, f in sorted((scale_factors or {}).items())
                                         if f and f != 1),
        '__ydwe_traducao = {%s}\n' % ', '.join('[%s]=%s' % (_lua_str(k), _lua_str(v))
                                              for k, v in sorted((translation or {}).items()) if k and v),
        _read(_route_data('ydwe', 'bignum.lua')), '\n',
        _read(_route_data('ydwe', 'motor.lua')), '\n',
        '\n'.join(segments), '\n',
        '__ydwe_bj = {%s}\n' % ', '.join('[%s]=true' % _lua_str(n) for n in bj),
        '''
local __G = _G
local JENV = {}
for k, v in pairs(__G) do if not __ydwe_bj[k] then JENV[k] = v end end
JENV._G = JENV
setmetatable(JENV, { __index = __G, __newindex = function(t, k, v)
  if __ydwe_bj[k] then __G[k] = v else rawset(t, k, v) end
end })
__JENV = JENV
local _ENV = JENV
''',
        res['lua_functions'], '\n', link_markers(markers(final_j)),
        '\n-- globals\n', g_root,
        '\n-- the globals whose initial value calls a function: run by main, never at map load\n'
        'local function __ydwe_init_globais()\n', g_deferred, '\nend\n',
        '''

rawset(__G, "config", function() config() end)
rawset(__G, "main", function()
  __ydwe_init_globais()
  if __ydwe_ponte_mouse then __ydwe_ponte_mouse() end
  BlzLoadTOCFile("devos\\\\kk_modelos.toc")
  -- the os.clock timer lives in _G (the runtime reads it there; _ENV here is the JASS one)
  rawset(__G, "__clock_timer", CreateTimer())
  TimerStart(__G.__clock_timer, 1000000.0, false, nil)
  __fixa_raiz(__G.__clock_timer)
  __register_handle_globals()
  rawset(__G, "__ydwe_main_rodou", true)
  main()
end)
''']
    body_text = ''.join(pieces)
    info = {'functions': len(res['func_names']), 'lua_modules': len(translated), 'translation_errors': error_list,
            'jass2lua_warnings': res['warnings'][:50], 'bytes': len(body_text.encode('utf-8', 'surrogateescape'))}
    return body_text, info


_LUA = []


def has_lua():
    try:
        return True
    except ImportError:
        return False


def _runtime():
    if not _LUA:
        from lupa import lua53
        _LUA.append(lua53.LuaRuntime(encoding=None))
    return _LUA[0]


def _compile_check(src):
    if not has_lua():
        return True
    L = _runtime()
    f = L.eval('function(s) local f, e = load(s, "=x", "t", {}) if f then return nil end return e end')
    return f(src.encode('utf-8', 'surrogateescape')) is None


def verify(body_text, common_module=None):
    if not has_lua():
        return None
    from lupa import lua53
    L = lua53.LuaRuntime(encoding=None)
    data_bytes = body_text.encode('utf-8', 'surrogateescape')
    chk = L.eval('function(s) local f, e = load(s, "=war3map.lua", "t") if f then return nil end return e end')
    e = chk(data_bytes)
    if e is not None:
        return 'does not compile: %s' % (e.decode('utf-8', 'replace') if isinstance(e, bytes) else e)
    common_module = common_module or _read(_ref('common.j'))
    nat = re.findall(r'^\s*(?:constant\s+)?native\s+([A-Za-z_]\w*)\s+takes[^\n]*?returns\s+(\w+)', common_module, re.M)
    consts = re.findall(r'^\s*constant\s+\w+\s+([A-Z_][A-Z0-9_]*)\s*=', common_module, re.M)
    line_list = ['io = nil', 'require = nil', 'dofile = nil', 'loadfile = nil']
    for n, kind in nat:
        v = {'integer': '0', 'real': '0.0', 'boolean': 'false', 'string': '""', 'nothing': 'nil'}.get(kind, '{}')
        line_list.append('%s = function(...) return %s end' % (n, v))
    line_list += ['%s = 0' % c for c in consts]
    env_fn = L.eval('function(setup, src) local ok, e = pcall(function() '
                    'local f = assert(load(setup, "=setup", "t")) f() '
                    'local g = assert(load(src, "=war3map.lua", "t")) g() end) '
                    'if ok then return nil end return tostring(e) end')
    e = env_fn('\n'.join(line_list).encode('utf-8'), data_bytes)
    if e is not None:
        return 'the main chunk does not load: %s' % (e.decode('utf-8', 'replace') if isinstance(e, bytes) else e)[:600]
    return None


EVAL_GENERATED = r'''
local dir = %s
local n = 0
for k, h in pairs(__ydwe_salvos_hist or {}) do
  n = n + 1
  local f = io.open(dir .. "/" .. n .. ".nome", "wb") f:write(k) f:close()
  for i = 1, #h do
    local g = io.open(dir .. "/" .. n .. "." .. i .. ".v", "wb") g:write(h[i]) g:close()
  end
end
local m = io.open(dir .. "/modelos.txt", "wb")
for k in pairs(__ydwe_modelos_usados or {}) do m:write(k, "\n") end
m:close()
local t = io.open(dir .. "/texturas.txt", "wb")
for k in pairs(__ydwe_texturas_usadas or {}) do t:write(k, "\n") end
t:close()
return n
'''

RX_GAME_TEMPLATE = re.compile(r'(?i)template|^(?:esc|script|glue|battlenet|standard|options|upkeep|resource|console|'
                              r'menu|dialog|tooltip|leaderboard|multiboard)')
CLICKABLE_FDF = ('GLUETEXTBUTTON', 'GLUEBUTTON', 'BUTTON', 'TEXTBUTTON', 'CHECKBOX', 'GLUECHECKBOX', 'POPUPMENU',
                 'GLUEPOPUPMENU', 'SLIDER', 'MENU', 'EDITBOX', 'GLUEEDITBOX')
FDF_FALLBACK = 'devos\\kk_modelos.fdf'
TOC_FALLBACK = 'devos\\kk_modelos.toc'


def fallback_templates(in_use, fdfs):
    defined = set()
    for t in fdfs:
        defined |= set(re.findall(r'(?i)Frame\s+"\w+"\s+"([^"]+)"', t))
    missing_items = {}
    for u in in_use:
        kind, _, fname = u.partition('|')
        if fname and fname not in defined and not RX_GAME_TEMPLATE.search(fname) and re.match(r'^[A-Za-z_]\w*$', fname):
            missing_items.setdefault(fname, kind)
    line_list = []
    for fname, kind in sorted(missing_items.items()):
        body = '    ControlStyle "AUTOTRACK",\n' if kind.upper() in CLICKABLE_FDF else ''
        line_list.append('Frame "%s" "%s" {\n%s}\n' % (kind.upper(), fname, body))
    return ''.join(line_list)


def join_versions(versions):
    if all(versions[i + 1].startswith(versions[i]) for i in range(len(versions) - 1)):
        return versions[-1]
    out, seen = [], set()
    for v in versions:
        if v not in seen:
            seen.add(v)
            out.append(v)
    return b''.join(out)


def generated_files(lua_p, seconds=15.0, log=None, extract=None, textures=None):
    import shutil
    import tempfile
    import simulate
    folder = tempfile.mkdtemp(prefix='ydwe_generated_')
    try:
        details = simulate.simulate(lua_p, seconds, 1, log=lambda *a: None,
                                    eval_code=EVAL_GENERATED % _lua_str(folder.replace('\\', '/')))
        out = {}
        for file_ in os.listdir(folder):
            if not file_.endswith('.nome'):
                continue
            n = file_[:-5]
            fname = open(os.path.join(folder, file_), 'rb').read().decode('utf-8', 'surrogateescape')
            versions, i = [], 1
            while os.path.isfile(os.path.join(folder, '%s.%d.v' % (n, i))):
                versions.append(open(os.path.join(folder, '%s.%d.v' % (n, i)), 'rb').read())
                i += 1
            if versions:
                out[fname] = join_versions(versions)
        in_use = []
        if os.path.isfile(os.path.join(folder, 'modelos.txt')):
            in_use = [
                line
                for line in open(os.path.join(folder, 'modelos.txt'), encoding='utf-8', errors='replace')
                .read()
                .splitlines()
                if line
            ]
        if textures is not None and os.path.isfile(os.path.join(folder, 'texturas.txt')):
            textures.extend(line for line in open(os.path.join(folder, 'texturas.txt'), 'rb').read()
                            .decode('utf-8', 'surrogateescape').splitlines() if line)
        fdfs = [v.decode('utf-8', 'replace') for k, v in out.items() if k.lower().endswith('.fdf')]
        if extract and os.path.isdir(extract):
            for root, _d, files_ in os.walk(extract):
                for a in files_:
                    if a.lower().endswith('.fdf'):
                        fdfs.append(open(os.path.join(root, a), 'rb').read().decode('utf-8', 'replace'))
        fallback_fdf = fallback_templates(in_use, fdfs)
        if fallback_fdf:
            out[FDF_FALLBACK] = fallback_fdf.encode('utf-8')
            out[TOC_FALLBACK] = (FDF_FALLBACK + '\r\n').encode('utf-8')
            if log:
                log('   %d frame template(s) the map asks for and no FDF of it defines: defined in %s'
                    % (fallback_fdf.count('Frame "'), FDF_FALLBACK))
        if log and (details.get('err') or details.get('main_error')):
            log('   the simulation that collects the generated files stopped: %s'
                % str(details.get('err') or details.get('main_error'))[:300])
        return out
    finally:
        shutil.rmtree(folder, ignore_errors=True)


TRANSPARENT = 'devos\\transparente.tga'


def transparent_tga():
    import struct
    return struct.pack('<BBBHHBHHHHBB', 0, 0, 2, 0, 0, 0, 0, 0, 2, 2, 32, 0x28) + b'\0' * 16


def missing_textures(used_entries, extract=None, generated=(), casc=None, log=None, map_path=None):
    in_map = set(n.replace('/', '\\').lower() for n in generated)
    if extract and os.path.isdir(extract):
        for root, _d, files_ in os.walk(extract):
            for a in files_:
                in_map.add(os.path.relpath(os.path.join(root, a), extract).replace('/', '\\').lower())
    if casc is None:
        try:
            from doctor.data import casc_wc3
            casc = casc_wc3.CascWC3()
        except Exception as e:
            casc = False
            if log:
                log('   the game is not installed here (%s): only marker texture names count as missing' % e)
    out = []
    for p in sorted(set(used_entries)):
        k = p.replace('/', '\\').lower()
        if not k or k == TRANSPARENT:
            continue
        alternatives = [k] + ([k[:-4] + '.mdx'] if k.endswith('.mdl') else [])
        alternatives += [x[:-4] + '.dds' for x in alternatives if x.endswith(('.blp', '.tga'))]
        if any(x in in_map for x in alternatives):
            continue
        if map_path is not None and any(map_path.find(x) is not None for x in alternatives):
            continue
        if casc:
            if any(('war3.w3mod:' + x) in casc.file_set or ('war3.w3mod:_hd.w3mod:' + x) in casc.file_set
                   for x in alternatives):
                continue
        elif '.' in k.rsplit('\\', 1)[-1]:
            continue
        out.append(p)
    return out


def missing_table(missing_ones):
    return ('\nrawset(__G, "__ydwe_transparente", %s)\nrawset(__G, "__ydwe_textura_ausente", {%s})\n'
            % (_lua_str(TRANSPARENT), ', '.join('[%s]=true' % _lua_str(p.lower()) for p in missing_ones)))


def w3i_lua(data_bytes):
    from doctor.data import w3i
    from doctor.fix import editor_prep
    m = w3i.parse_or_tolerant(data_bytes)
    m['script_language'] = 1
    ver = max(m['version'], editor_prep.W3I_RAISED_TO)
    if 'game_version' not in m:
        m['game_version'] = [1, 31, 1, 12173]
    m.setdefault('supported_modes', editor_prep.W3I_MODES)
    m.setdefault('game_data_version', editor_prep.W3I_GDV_TFT)
    return w3i.write(m, ver)
