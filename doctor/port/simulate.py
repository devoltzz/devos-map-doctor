# Runs a YDWE Lua engine map in a simulated game for a few seconds, to collect the frame definition files the map writes while it runs.
import os
import re
import shutil
import sys


HERE = os.path.dirname(os.path.abspath(__file__))
def _arg(fname, default_value=None, argv=None):
    for a in (argv if argv is not None else sys.argv[1:]):
        if a.startswith('--%s=' % fname):
            return a.split('=', 1)[1]
    return default_value


POST_CO = b'''
local co = __LENV and __LENV.coroutine
if co then
  local cria, embrulha = co.create, co.wrap
  local function herda(c)
    local h, m, n = debug.gethook()
    if h then debug.sethook(c, h, m, n) end
    return c
  end
  co.create = function(f) return herda(cria(f)) end
  co.wrap = function(f)
    local c = herda(cria(f))
    return function(...)
      local r = table.pack(coroutine.resume(c, ...))
      if not r[1] then error(r[2], 0) end
      return table.unpack(r, 2, r.n)
    end
  end
end
'''

POST_LOG = b'''
local antigo = __logerr
__logerr = function(msg, fn) __sim_anota(msg) if antigo then pcall(antigo, msg, fn) end end
'''

POST_CONSOLE = b'''
__sim_console = {}
local function escreve(...)
  if #__sim_console >= 400 then return end
  local t = table.pack(...)
  for i = 1, t.n do t[i] = tostring(t[i]) end
  __sim_console[#__sim_console + 1] = table.concat(t, " ", 1, t.n)
end
if __ydwe_libs and __ydwe_libs["jass.console"] then __ydwe_libs["jass.console"].write = escreve end
if __LENV then __LENV.print = escreve end
'''


LUA32 = os.path.normpath(os.path.join(HERE, '..', '..', 'cache', 'lua32',
                                      'lua53_32.exe' if os.name == 'nt' else 'lua53_32'))


def _lit(v):
    if v is None:
        return b'nil'
    if isinstance(v, bool):
        return b'true' if v else b'false'
    if isinstance(v, (int, float)):
        return repr(v).encode()
    b = v if isinstance(v, (bytes, bytearray)) else str(v).encode('utf-8', 'surrogateescape')
    out = bytearray(b'"')
    for c in b:
        if c == 0x22 or c == 0x5C:
            out += b'\\' + bytes([c])
        elif c < 32 or c == 127:
            out += b'\\%03d' % c
        else:
            out.append(c)
    return bytes(out + b'"')


class _Same(object):
    def __eq__(self, o):
        return True

    def __ne__(self, o):
        return False


class _Globals(object):
    def __init__(self, gr):
        object.__setattr__(self, '_gr', gr)

    def __setattr__(self, fname, field_value):
        self._gr.pieces.append(b'%s = %s\n' % (fname.encode(), _lit(field_value)))

    def __getattr__(self, fname):
        return lambda *a: _Same()


class _Function(object):
    def __init__(self, gr, expr):
        self.gr, self.expr = gr, expr if isinstance(expr, bytes) else expr.encode('utf-8', 'surrogateescape')

    def __call__(self, *args):
        self.gr.pieces.append(b'do local __f = (' + self.expr + b') __f(' + b', '.join(_lit(a) for a in args) +
                              b') end\n')
        return None


class Recorder(object):
    def __init__(self, *a, **k):
        self.pieces = []

    def execute(self, code):
        b = code if isinstance(code, bytes) else code.encode('utf-8', 'surrogateescape')
        self.pieces.append(b'do local __f = assert(load(' + _lit(b) + b', "=sim", "t")) __f() end\n')

    def eval(self, expr):
        return _Function(self, expr)

    def globals(self):
        return _Globals(self)

    def body_text(self):
        return b''.join(self.pieces)


class _Module32(object):
    LuaRuntime = Recorder


END32 = b'''
local function linha(s) return (tostring(s):gsub("[\\r\\n]+", " | ")) end
local fh = assert(io.open(__SIM_MAPA, "rb"))
local texto = fh:read("a")
fh:close()
local f, e = load(texto, "=war3map.lua", "t")
if not f then __SAIDA:write("\\n@@erro\\tcompile: " .. linha(e)) return end
local ok, e2 = xpcall(f, debug.traceback)
if not ok then __SAIDA:write("\\n@@erro\\t" .. linha(e2)) return end
'''

END32_AFTER = b'''
for _, etapa in ipairs({ "config", "main" }) do
  local g = rawget(_G, etapa)
  if type(g) ~= "function" then __SAIDA:write("\\n@@erro_" .. etapa .. "\\tno " .. etapa)
  else
    local ok, e = xpcall(g, debug.traceback)
    if not ok then __SAIDA:write("\\n@@erro_" .. etapa .. "\\t" .. linha(e)) end
  end
end
local ok, e = xpcall(__mock_advance, debug.traceback, __SIM_SEGUNDOS, 0.05)
if not ok then __SAIDA:write("\\n@@erro_tempo\\t" .. linha(e)) end
for _, k in ipairs(__sim_ordem) do __SAIDA:write("\\n@@err\\t" .. __sim_erros[k] .. "\\t" .. linha(k) .. "\\t" .. linha(__sim_texto[k])) end
for _, v in pairs(__ydwe_execs or {}) do __SAIDA:write("\\n@@exec\\t" .. linha(v)) end
for _, v in pairs(__ydwe_carregados or {}) do __SAIDA:write("\\n@@carregado\\t" .. linha(v)) end
for k, v in pairs(__ydwe_ausente or {}) do __SAIDA:write("\\n@@ausente\\t" .. linha(k) .. "\\t" .. v) end
for k, v in pairs(__ydwe_falta or {}) do __SAIDA:write("\\n@@falta\\t" .. linha(k) .. "\\t" .. v) end
'''


def _run32(lua, file_path, seconds, log, details):
    import subprocess
    import tempfile
    if not os.path.isfile(LUA32):
        details['err'] = 'no 32-bit Lua (%s): build it from terceiros/lua-5.3.6 with -DLUA_32BITS' % LUA32
        return details
    body_text = (
        b'local __SAIDA = io.stdout\n'
        + lua.body_text()
        + b'__SIM_MAPA = '
        + _lit(os.path.abspath(file_path))
        + b'\n__SIM_SEGUNDOS = '
        + _lit(float(seconds))
        + b'\n'
        + END32
        + b'do '
        + POST_CO
        + b' end\ndo '
        + POST_LOG
        + b' end\ndo '
        + POST_CONSOLE
        + b' end\n'
        + END32_AFTER
    )
    fd, file_ = tempfile.mkstemp(suffix='.lua', prefix='sim32_')
    with os.fdopen(fd, 'wb') as f:
        f.write(body_text)
    try:
        r = subprocess.run([LUA32, file_], capture_output=True)
    finally:
        if os.environ.get('SIM32_GUARDA'):
            shutil.move(file_, os.environ["SIM32_GUARDA"])
        else:
            os.remove(file_)
    output = r.stdout.decode('utf-8', 'surrogateescape').split('\n')
    if r.returncode:
        details['err'] = 'lua32 exit %d: %s' % (r.returncode, r.stderr.decode('utf-8', 'replace')[-1500:])
    details.update(
        execs=[], carregados=[], missing_ones=[], missing_items={}, error_list=[], erros_texto=[], console=[]
    )
    for line in output:
        p = line.rstrip('\r').split('\t')
        if p[0] in ('@@erro', '@@erro_config', '@@erro_main', '@@erro_tempo'):
            details[p[0][2:]] = p[1] if len(p) > 1 else ''
        elif p[0] == '@@err' and len(p) >= 4:
            details['error_list'].append((p[2], int(p[1])))
            details['erros_texto'].append(p[3])
        elif p[0] == '@@exec':
            details['execs'].append(p[1])
        elif p[0] == '@@carregado':
            details['carregados'].append(p[1])
        elif p[0] == '@@ausente' and len(p) >= 3:
            details['missing_ones'].append((p[1], int(float(p[2]))))
        elif p[0] == '@@falta' and len(p) >= 3:
            details['missing_items'][p[1]] = int(float(p[2]))
    details['missing_ones'].sort(key=lambda kv: -kv[1])
    details['lua'] = '32-bit'
    return details


def simulate(file_path, seconds=30.0, n_players=1, log=print, eval_code=None, lua32=False):
    import locale
    if lua32:
        L = _Module32()
    else:
        import lupa.lua53 as L
    from doctor.port import mock_dispatch as PDM
    from doctor.script.jass2lua import lua_string as jass_str
    locale.setlocale(locale.LC_ALL, 'C')
    common_src = PDM.read_data(PDM.COMMON)
    blizz_src = PDM.read_data(PDM.BLIZZ)
    lua = PDM.load_engine(L, common_src, blizz_src, 'ignora')
    g = lua.globals()
    lua.execute(('function GetPlayerSlotState(p) if p ~= nil and p.id < %d then return PLAYER_SLOT_STATE_PLAYING end '
                 'return PLAYER_SLOT_STATE_EMPTY end' % n_players).encode('utf-8'))
    lua.execute(('function GetPlayerController(p) if p ~= nil and p.id < %d then return MAP_CONTROL_USER end '
                 'return MAP_CONTROL_COMPUTER end' % n_players).encode('utf-8'))
    lua.execute(b'''
__sim_erros, __sim_ordem, __sim_texto = {}, {}, {}
local function anota(msg)
  msg = tostring(msg)
  local k = msg:match("^[^\\n]*") or msg
  k = k:gsub(":%d+:", ":?:")
  local n = __sim_erros[k]
  if n == nil then __sim_ordem[#__sim_ordem + 1] = k __sim_erros[k] = 1 __sim_texto[k] = msg:sub(1, 12000) else __sim_erros[k] = n + 1 end
end
__sim_anota = anota
''')
    lua.execute(b'''
local em_thread = setmetatable({}, { __mode = "k" })
local cria, retoma, rende, status, corrente = coroutine.create, coroutine.resume, coroutine.yield, coroutine.status,
  coroutine.running
local function segue(co, ok, tag, s)
  if not ok then error(tag, 0) end
  if status(co) == "suspended" and tag == "__sleep" then
    local t = CreateTimer()
    TimerStart(t, math.max(tonumber(s) or 0, 0.05), false, function()
      DestroyTimer(t)
      segue(co, retoma(co))
    end)
  end
end
local function como_thread(f)
  if type(f) ~= "function" then return f end
  return function(...)
    local co = cria(f)
    em_thread[co] = true
    -- o vigia (o teto de instrucoes, o de memoria) e' por thread: a corrotina herda o de quem a cria
    local h, m, c = debug.gethook()
    if h then debug.sethook(co, h, m, c) end
    segue(co, retoma(co, ...))
  end
end
local add = TriggerAddAction
TriggerAddAction = function(t, f) return add(t, como_thread(f)) end
function TriggerSleepAction(s)
  local co = corrente()
  if co and em_thread[co] then rende("__sleep", s) end
end
''')
    lua.execute(b'''
local function estoura() error("watchdog: callback above " .. (__SIM_TETO or 2000000000) .. " instructions", 0) end
-- o teto de memoria (`--teto-mem=MB`): conferido a cada milhao de instrucoes, com onde o codigo estava
local n_mem = 0
local function memoria()
  n_mem = n_mem + 1
  if __SIM_MEM and collectgarbage("count") > __SIM_MEM * 1024 then
    error("watchdog: memory above " .. __SIM_MEM .. " MB at " .. debug.traceback("", 2), 0)
  end
  if n_mem * 1000000 > (__SIM_TETO or 2000000000) then estoura() end
end
function __wd_on()
  if __SIM_MEM then n_mem = 0 debug.sethook(memoria, "", 1000000) return end
  debug.sethook(estoura, "", __SIM_TETO or 2000000000)
end
''')
    cap = _arg('cap', None)
    if cap:
        lua.globals().__SIM_TETO = int(float(cap))
    if _arg('teto-mem', None):
        lua.globals().__SIM_MEM = int(float(_arg('teto-mem', None)))
    if _arg('level_list', None):
        lua.globals().__SIM_NIVEIS = int(_arg('level_list', None))
    if '--amostra' in sys.argv:
        lua.execute(b'''
__sim_amostras = {}
local n = 0
local function amostra()
  n = n + 1
  local partes = {}
  for nivel = 2, (__SIM_NIVEIS or 4) do
    local d = debug.getinfo(nivel, "Sl")
    if not d then break end
    partes[#partes + 1] = d.short_src .. ":" .. tostring(d.currentline)
  end
  local k = table.concat(partes, " < ")
  __sim_amostras[k] = (__sim_amostras[k] or 0) + 1
  if n * 1000000 > (__SIM_TETO or 2000000000) then error("watchdog: callback above the ceiling", 0) end
  if __SIM_MEM and collectgarbage("count") > __SIM_MEM * 1024 then
    error("watchdog: memory above " .. __SIM_MEM .. " MB at " .. debug.traceback("", 2), 0)
  end
end
function __wd_on() n = 0 debug.sethook(amostra, "", 1000000) end
''')
    lua.execute(b'''
local pai0 = BlzFrameGetParent
BlzFrameGetParent = function(f)
  local p = pai0(f)
  if p == nil and f ~= nil then
    local ui = BlzGetOriginFrame(ORIGIN_FRAME_GAME_UI, 0)
    if ui ~= f then p = ui end
  end
  return p
end
local por_nome = {}
BlzGetFrameByName = function(n, i)
  local k = tostring(n) .. ":" .. tostring(i)
  local f = por_nome[k]
  if not f then f = BlzCreateFrameByType("FRAME", n, BlzGetOriginFrame(ORIGIN_FRAME_GAME_UI, 0), "", i or 0) por_nome[k] = f end
  return f
end
''')
    empty = {'integer': '0', 'real': '0.0', 'boolean': 'false', 'string': '""', 'nothing': 'nil'}
    line_list = []
    for m in re.finditer(r'(?m)^\s*(?:constant\s+)?native\s+(\w+)\s+takes\s+(.*?)\s+returns\s+(\w+)', common_src):
        fname, takes, ret = m.groups()
        ps = [] if takes.strip() == 'nothing' else [p.split()[0] for p in takes.split(',')]
        hs = [i + 1 for i, t in enumerate(ps) if t not in empty and t != 'code']
        if hs:
            line_list.append(
                '__sim_nulo(%s, {%s}, %s)' % (jass_str(fname), ','.join(map(str, hs)), empty.get(ret, 'nil'))
            )
    lua.execute(('''
local function __sim_nulo(nome, hs, padrao)
  local f = rawget(_G, nome)
  if type(f) ~= "function" then return end
  -- e o handle de OUTRO tipo (o item passado como unidade): o jogo confere o tipo e devolve o vazio; o mock indexava o
  -- campo que nao existe
  rawset(_G, nome, function(...)
    local ok, r = pcall(f, ...)
    if ok then return r end
    for i = 1, #hs do
      if select(hs[i], ...) == nil then return padrao end
    end
    if type(r) == "string" and r:find("attempt to index", 1, true) then return padrao end
    error(r, 0)
  end)
end
''' + '\n'.join(line_list)).encode('utf-8'))
    enums = set(m.group(1) for m in re.finditer(
        r'(?m)^\s*(?:constant\s+)?native\s+Convert\w+\s+takes\s+integer\s+\w+\s+returns\s+(\w+)', common_src))
    pais = dict(re.findall(r'(?m)^\s*type\s+(\w+)\s+extends\s+(\w+)', common_src))
    types = ['__sim_pais = {%s}' % ', '.join('[%s]=%s' % (jass_str(k), jass_str(v)) for k, v in sorted(pais.items()))]
    for m in re.finditer(r'(?m)^\s*(?:constant\s+)?native\s+(\w+)\s+takes\s+(.*?)\s+returns\s+(\w+)', common_src):
        fname, takes = m.group(1), m.group(2)
        ps = [] if takes.strip() == 'nothing' else [x.split()[0] for x in takes.split(',')]
        pos = ['[%d]=%s' % (i + 1, jass_str(t)) for i, t in enumerate(ps)
               if t in enums or (t in pais and t not in ('handle', 'code')) or t == 'integer']
        if pos:
            types.append('__sim_tipo(%s, {%s})' % (jass_str(fname), ','.join(pos)))
    lua.execute(('''
local function __sim_tipo(nome, pos)
  local f = rawget(_G, nome)
  if type(f) ~= "function" then return end
  rawset(_G, nome, function(...)
    for i, t in pairs(pos) do
      local v = select(i, ...)
      if t == "integer" then
        if math.type(v) == "float" and math.tointeger(v) == nil then
          error(string.format("bad argument #%d to '%s' (number has no integer representation)", i, nome), 2)
        end
        goto proximo
      end
      local ok = false
      if type(v) == "table" then
        local k = v.__kind
        if k == "frame" then k = "framehandle" end       -- o unico nome do motor simulado que nao e' o do common.j
        while k ~= nil do
          if k == t then ok = true break end
          k = __sim_pais[k]
        end
      end
      if v ~= nil and not ok then
        local got = type(v) == "table" and tostring(v.__kind) or (type(v) .. " " .. tostring(v))
        error(string.format("bad argument #%d to '%s' (%s expected, got %s)", i, nome, t, got), 2)
      end
      ::proximo::
    end
    return f(...)
  end)
end
''' + '\n'.join(types)).encode('utf-8'))
    details = {'map_path': file_path, 'seconds': seconds}
    if lua32:
        return _run32(lua, file_path, seconds, log, details)
    body_text = open(file_path, 'rb').read()
    load_data = lua.eval(
        'function(s) local f, e = load(s, "=war3map.lua", "t") if not f then return "compile: " .. '
        'tostring(e) end local ok, e2 = xpcall(f, debug.traceback) if not ok then return tostring(e2) end '
        'return nil end'
    )
    err = load_data(body_text)
    if err:
        details['err'] = 'main chunk: %s' % err
        return details
    lua.execute(POST_CO)
    lua.execute(POST_LOG)
    lua.execute(POST_CONSOLE)
    pre = _arg('pre', None)
    if pre:
        e = load_data(open(pre, 'rb').read())
        if e:
            details['erro_pre'] = str(e)
    run_action = lua.eval(
        'function(nome) local f = rawget(_G, nome) if type(f) ~= "function" then return "no " .. nome end '
        'local ok, e = xpcall(f, debug.traceback) if not ok then return tostring(e) end return nil end'
    )
    for stage in ('config', 'main'):
        e = run_action(stage)
        if e:
            details['erro_' + stage] = str(e)[:3000]
            log('%s: ERROR %s' % (stage, str(e)[:600]))
    avanca = lua.eval('function(s) local ok, e = xpcall(__mock_advance, debug.traceback, s, 0.05) '
                      'if not ok then return tostring(e) end return nil end')
    e = avanca(float(seconds))
    if e:
        details['erro_tempo'] = str(e)[:3000]
    if eval_code:
        f = lua.eval(
            'function(s) local f, e = load(s, "=eval", "t") if not f then return "compile: " .. tostring(e) end '
            'local r = table.pack(xpcall(f, debug.traceback)) for i = 1, r.n do r[i] = tostring(r[i]) end '
            'return table.concat(r, " | ", 1, r.n) end'
        )
        details['_eval'] = f(eval_code.encode('utf-8'))
    if g.__sim_amostras:
        am = lua.eval('function(t) local o = {} for k, v in pairs(t) do o[#o + 1] = v .. "\\t" .. k end '
                      'return table.concat(o, "\\n") end')(g.__sim_amostras)
        details['samples'] = sorted(
            ((int(line.split('\t', 1)[0]), line.split('\t', 1)[1]) for line in _t(am).split('\n') if line), reverse=True
        )[:30]
    join_console = lua.eval('function(t) local o = {} for i = 1, #t do local s = tostring(t[i]) '
                            'if not utf8.len(s) then s = s:gsub("[\\128-\\255]", function(c) '
                            'return string.format("\\\\x%02X", c:byte()) end) end o[#o + 1] = s end '
                            'return table.concat(o, "\\n") end')
    details['console'] = _t(join_console(g.__sim_console)).split('\n') if g.__sim_console else []
    details['execs'] = list(g.__ydwe_execs.values()) if g.__ydwe_execs else []
    details['carregados'] = list(g.__ydwe_carregados.values()) if g.__ydwe_carregados else []
    missing_n = g.__ydwe_ausente
    details['missing_ones'] = sorted(missing_n.items(), key=lambda kv: -kv[1]) if missing_n else []
    missing = g.__ydwe_falta
    listing = lua.eval('function(t) local o = {} for k, v in pairs(t) do '
                       'local s = utf8.len(k) and k or (k:gsub("[\\128-\\255]", function(c) '
                       'return string.format("\\\\x%02X", c:byte()) end)) '
                       'o[#o + 1] = s .. "\\t" .. v end return table.concat(o, "\\n") end')(missing) if missing else ''
    details['missing_items'] = dict(
        (line.rsplit('\t', 1)[0], int(line.rsplit('\t', 1)[1])) for line in listing.split('\n') if '\t' in line
    )
    order = list(g.__sim_ordem.values())
    details['error_list'] = [(k, g.__sim_erros[k]) for k in order]
    details['erros_texto'] = [g.__sim_texto[k] for k in order]
    return details


def _t(v):
    return v.decode('utf-8', 'replace') if isinstance(v, bytes) else v
