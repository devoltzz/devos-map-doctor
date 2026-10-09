





do
local G = _G
local type, tostring, pairs, ipairs, rawget, rawset, setmetatable, select, pcall, xpcall, error, load =
      type, tostring, pairs, ipairs, rawget, rawset, setmetatable, select, pcall, xpcall, error, load
local unpack = table.unpack
local sfind, ssub, sgsub, sgmatch = string.find, string.sub, string.gsub, string.gmatch


local schar, sbyte = string.char, string.byte
local function slower(s) return (sgsub(s, "[A-Z]", function(c) return schar(sbyte(c) + 32) end)) end
__ydwe_minusculas = slower

__ydwe_fonte = __ydwe_fonte or {}
__ydwe_forma = __ydwe_forma or {}
__ydwe_dados = __ydwe_dados or {}
__ydwe_moldes = __ydwe_moldes or {}
__ydwe_falta = {}
__ydwe_carregados = {}

local function chave(n)
  n = sgsub(n, "/", "\\")
  return slower(n)
end

local function errh(e)
  if debug and debug.traceback then return tostring(debug.traceback(e, 2)) end
  return tostring(e)
end




local LENV = {}
for _, k in ipairs({ "assert", "error", "ipairs", "next", "pairs", "pcall", "print", "rawequal", "rawget", "rawlen",
    "rawset", "select", "setmetatable", "getmetatable", "tonumber", "tostring", "type", "xpcall", "string", "table",
    "math", "coroutine", "utf8", "os", "debug", "collectgarbage" }) do
  LENV[k] = rawget(G, k)
end



for _, k in ipairs({ "math", "table", "os", "coroutine", "utf8" }) do
  local orig = rawget(G, k)
  if type(orig) == "table" then
    local copia = {}
    for nome, v in pairs(orig) do copia[nome] = v end
    LENV[k] = copia
  end
end

do
  local m = LENV.math
  local semente = 0
  local rs = m.randomseed
  m.randomseed = function(s, ...)
    semente = tonumber(s) or 0
    if rs then return rs(s, ...) end
  end
  m.getrandomseed = function() return semente end





  local rnd = m.random
  local function por_float(a, b, erro)
    if type(a) ~= "number" or type(b) ~= "number" then error(erro, 3) end
    a, b = math.ceil(a), math.floor(b)
    if a > b then error(erro, 3) end
    local x = math.floor(a + rnd() * ((b + 0.0) - a + 1.0))
    if x < a then x = a elseif x > b then x = b end
    return math.tointeger(x) or x
  end
  m.random = function(...)
    local n = select("#", ...)
    if n == 0 then return rnd() end
    local ok, r = pcall(rnd, ...)
    if ok then return r end
    if n == 1 then return por_float(1, (...), r) end
    local a, b = ...
    return por_float(a, b, r)
  end
end





if math.maxinteger < 2^40 then
  local s0 = rawget(G, "string")
  local function fmt(f) return type(f) == "string" and (sgsub(f, "([iI])8", "%14")) or f end
  local proprio = {
    pack = function(f, ...) return s0.pack(fmt(f), ...) end,
    unpack = function(f, ...) return s0.unpack(fmt(f), ...) end,
    packsize = function(f) return s0.packsize(fmt(f)) end,
  }
  LENV.string = setmetatable(proprio, { __index = s0, __newindex = function(_, k, v) s0[k] = v end })
end


do
  local d = rawget(G, "debug")
  if type(d) == "table" then
    local copia = {}
    for nome, v in pairs(d) do copia[nome] = v end
    copia.sethook = function() end
    copia.gethook = function() return nil end
    LENV.debug = copia
  end
end
LENV._G = LENV
LENV._VERSION = "Lua 5.3"
LENV.print = function(...) end
LENV.collectgarbage = function(op) if op == "count" then return 0, 0 end return 0 end
__LENV = LENV

local function lload(chunk, nome, modo, ...)
  local env = LENV
  if select("#", ...) > 0 then env = ... end
  if type(chunk) == "string" and ssub(chunk, 1, 4) == "\27Lua" then return nil, "binary chunk not supported" end
  return load(chunk, nome, "t", env)
end
LENV.load = lload
LENV.loadstring = nil
LENV.dofile = function(n) error("dofile: no file system", 2) end
LENV.loadfile = function(n) return nil, "no file system" end
LENV.io = { open = function() return nil, "no file system" end, lines = function() return function() return nil end end,
            write = function() end, read = function() return nil end, close = function() end,
            stdout = { write = function() end }, stderr = { write = function() end } }




local package = { loaded = {}, preload = {}, path = "?.lua;?\\init.lua", cpath = "", config = "\\\n;\n?\n!\n-\n",
                  searchers = {} }
LENV.package = package

local function acha(nome)
  local base = sgsub(nome, "%.", "\\")
  local function tenta(molde)
    local k = chave((sgsub(molde, "%?", (sgsub(base, "%%", "%%%%")))))
    if __ydwe_forma[k] then return k end
    k = chave((sgsub(molde, "%?", (sgsub(nome, "%%", "%%%%")))))
    if __ydwe_forma[k] then return k end
  end
  local p = package.path
  if type(p) == "string" then
    for molde in sgmatch(p, "[^;]+") do
      local k = tenta(molde)
      if k then return k end
    end
  end
  for i = 1, #__ydwe_moldes do
    local k = tenta(__ydwe_moldes[i])
    if k then return k end
  end
  local k = chave(nome)
  if __ydwe_forma[k] then return k end
  return nil
end
__ydwe_acha = acha

local compilado = {}
local function compila(k)
  local f = compilado[k]
  if f then return f end
  local src = __ydwe_fonte[k]
  if src == nil then return nil, "no source" end
  local g, e
  if __ydwe_forma[k] == "t" then
    g, e = load(src, "@" .. k, "t", LENV)
    if not g then return nil, e end
    f = function(_, ...) return g(...) end
  else
    g, e = load(src, "@" .. k, "t", G)
    if not g then return nil, e end
    f = g()
  end
  compilado[k] = f
  __ydwe_fonte[k] = nil
  return f
end

local ja_logado = {}
local function require(nome)
  if type(nome) ~= "string" then error("bad argument #1 to 'require' (string expected)", 2) end
  local m = package.loaded[nome]
  if m ~= nil then return m end
  local pre = package.preload[nome]
  if pre ~= nil then
    local r = pre(nome)
    if r == nil then r = package.loaded[nome] end
    if r == nil then r = true end
    package.loaded[nome] = r
    return r
  end
  local k = acha(nome)
  if k == nil then
    __ydwe_falta[nome] = (__ydwe_falta[nome] or 0) + 1
    error("module '" .. nome .. "' not found", 2)
  end
  local f, e = compila(k)
  if not f then error("module '" .. nome .. "': " .. tostring(e), 2) end
  __ydwe_carregados[#__ydwe_carregados + 1] = nome

  local ok, r = xpcall(f, errh, LENV, nome, k)
  if not ok then
    local linha = string.match(tostring(r), "^[^\n]*")
    if not ja_logado[linha] then
      ja_logado[linha] = true
      __logerr("require " .. nome .. ": " .. tostring(r))
    end
    error(r, 0)
  end
  if r == nil then r = package.loaded[nome] end
  if r == nil then r = true end
  package.loaded[nome] = r
  return r
end
LENV.require = require
__ydwe_require = require


local function stub_do_modulo(k)
  return "return __ydwe_roda(" .. string.format("%q", k) .. ", ...)"
end
function __ydwe_roda(k, ...)
  local f, e = compila(k)
  if not f then error(e, 2) end
  return f(LENV, ...)
end
LENV.__ydwe_roda = __ydwe_roda




local h2i, i2h = __h2i, __i2hf
local parse_sig = __parse_sig





local gid_nativo = (__rawnat and __rawnat["GetHandleId"]) or rawget(G, "GetHandleId")
local function enum_id(v)
  if v == nil then return 0 end
  if type(v) == "number" then return v end
  return gid_nativo(v) or 0
end
__ydwe_enum_id = enum_id

local vazio_de = { I = 0, R = 0.0, B = false, S = "", H = 0 }
local function para_lua(nome, f)
  local sg = parse_sig(nome)
  if not sg then
    return function(...)
      local r = f(...)
      if type(r) == "userdata" then return h2i(r) end
      return r
    end
  end
  local params, n, retH = sg.params, sg.n, (sg.ret == "H")


  local enums = __sig_enum and __sig_enum[nome]
  local conv_cache = {}
  local function enum_de(cv, v)
    local c = conv_cache[cv]
    if c == nil then c = {} conv_cache[cv] = c end
    local h = c[v]
    if h == nil then
      local f = rawget(G, cv)
      if type(f) ~= "function" then return v end
      h = f(math.tointeger(v) or v)
      c[v] = h
    end
    return h
  end



  local algum = false
  for i = 1, n do
    local p = params[i]
    if p == "H" or p == "I" or p == "R" or p == "B" then algum = true end
  end
  if not algum then
    if retH and enums and enums.ret then return function(...) return enum_id(f(...)) end end
    if retH then return function(...) return h2i(f(...)) end end
    return f
  end
  return function(...)
    local a = { ... }
    for i = 1, n do
      local p, v = params[i], a[i]
      if p == "H" then
        if enums and enums[i] and type(v) == "number" then a[i] = enum_de(enums[i], v) else a[i] = i2h(v) end
      elseif p == "I" then
        if type(v) == "string" then a[i] = string2id(v) elseif v == nil then a[i] = 0
        elseif math.type(v) == "float" then



          local t = v >= 0 and math.floor(v) or math.ceil(v)
          a[i] = math.tointeger(t) or 0
        end
      elseif p == "R" then
        if v == nil then a[i] = 0.0 end
      elseif p == "B" then
        a[i] = v and true or false
      end
    end



    local ok, r = pcall(f, unpack(a, 1, n))
    if not ok then
      if type(r) == "string" and sfind(r, "bad argument", 1, true) and sfind(r, " expected", 1, true) then
        local k = "wrong handle type." .. tostring(nome)
        __ydwe_ausente[k] = (__ydwe_ausente[k] or 0) + 1
        return vazio_de[sg.ret]
      end
      error(r, 0)
    end
    if retH and enums and enums.ret then return enum_id(r) end
    if retH then return h2i(r) end
    return r
  end
end

local function para_jass(nome, f)
  local sg = parse_sig(nome)
  if not sg then return f end
  local params, n, retH = sg.params, sg.n, (sg.ret == "H")
  return function(...)
    local a = { ... }
    for i = 1, n do if params[i] == "H" then a[i] = h2i(a[i]) end end
    local r = f(unpack(a, 1, n))
    if retH then return i2h(r) end
    return r
  end
end
__ydwe_para_lua, __ydwe_para_jass = para_lua, para_jass




local i32_conv = {}
do
  local F = __ydwe_i32 or {}
  local C, A, T = F.combat or 1, F.armor or 1, F.attribute or 1
  local function vital(s)
    return s == UNIT_STATE_LIFE or s == UNIT_STATE_MAX_LIFE or s == UNIT_STATE_MANA or s == UNIT_STATE_MAX_MANA
  end
  local function baixa(v, f, vida)
    v = (tonumber(v) or 0) / f
    if vida and v > 0 and v < 1 then v = 1 end
    return v
  end
  local function int(x) return math.tointeger(math.floor(x + 0.5)) or 0 end
  local function def(nome, fazer) local f = rawget(G, nome) if type(f) == "function" then i32_conv[nome] = fazer(f) end end
  if C ~= 1 then
    def("GetUnitState", function(f) return function(u, s) local v = f(u, s) if vital(s) then return v * C end return v end end)
    def("SetUnitState", function(f) return function(u, s, v)
      if vital(s) then v = baixa(v, C, s == UNIT_STATE_LIFE) end
      return f(u, s, v)
    end end)
    def("GetWidgetLife", function(f) return function(w) return f(w) * C end end)
    def("SetWidgetLife", function(f) return function(w, v) return f(w, baixa(v, C, true)) end end)
    def("GetDestructableLife", function(f) return function(d) return f(d) * C end end)
    def("SetDestructableLife", function(f) return function(d, v) return f(d, baixa(v, C, true)) end end)
    def("GetDestructableMaxLife", function(f) return function(d) return f(d) * C end end)
    def("SetDestructableMaxLife", function(f) return function(d, v) return f(d, baixa(v, C, true)) end end)
    def("GetEventDamage", function(f) return function() return f() * C end end)
    def("BlzSetEventDamage", function(f) return function(v) return f((tonumber(v) or 0) / C) end end)
    def("UnitDamageTarget", function(f) return function(u, t, v, ...) return f(u, t, (tonumber(v) or 0) / C, ...) end end)
    def("UnitDamagePoint", function(f) return function(u, d, r, x, y, v, ...)
      return f(u, d, r, x, y, (tonumber(v) or 0) / C, ...)
    end end)
    def("BlzGetUnitMaxHP", function(f) return function(u) return int(f(u) * C) end end)
    def("BlzSetUnitMaxHP", function(f) return function(u, v) return f(u, int(baixa(v, C, true))) end end)
    def("BlzGetUnitMaxMana", function(f) return function(u) return int(f(u) * C) end end)
    def("BlzSetUnitMaxMana", function(f) return function(u, v) return f(u, int((tonumber(v) or 0) / C)) end end)
    def("BlzGetUnitBaseDamage", function(f) return function(u, i) return int(f(u, i) * C) end end)
    def("BlzSetUnitBaseDamage", function(f) return function(u, v, i) return f(u, int((tonumber(v) or 0) / C), i) end end)
  end
  if A ~= 1 then
    def("BlzGetUnitArmor", function(f) return function(u) return f(u) * A end end)
    def("BlzSetUnitArmor", function(f) return function(u, v) return f(u, (tonumber(v) or 0) / A) end end)
  end
  if T ~= 1 then
    for _, n in ipairs({ "GetHeroStr", "GetHeroAgi", "GetHeroInt" }) do
      def(n, function(f) return function(u, b) return int(f(u, b) * T) end end)
    end
    for _, n in ipairs({ "SetHeroStr", "SetHeroAgi", "SetHeroInt" }) do
      def(n, function(f) return function(u, v, p) return f(u, int((tonumber(v) or 0) / T), p) end end)
    end
  end
end
__ydwe_i32_conv = i32_conv

local function do_jass(nome)
  local c = i32_conv[nome]
  if c then return c end
  local env = __JENV
  local v = env and rawget(env, nome)
  if v == nil then v = rawget(G, nome) end
  return v
end


__ydwe_ausente = {}
local function ausente(lib, nome)
  local k = lib .. "." .. tostring(nome)
  __ydwe_ausente[k] = (__ydwe_ausente[k] or 0) + 1
end
local function tabela_de_funcoes(achar, lib)
  return setmetatable({}, { __index = function(t, nome)
    local v, assina = achar(nome)
    if v == nil then ausente(lib, nome) return nil end
    if type(v) ~= "function" then
      if __enum_globais and __enum_globais[nome] then return enum_id(v) end
      return v
    end
    local w = para_lua(assina or nome, v)
    rawset(t, nome, w)
    return w
  end })
end



local smatch_ = string.match
local inertes = {}

local japi_registrada = {}
__ydwe_japi_registrada = japi_registrada
local function inerte_japi(nome)
  local f = inertes[nome]
  if f == nil then
    local k = "inerte." .. tostring(nome)
    f = function()
      __ydwe_ausente[k] = (__ydwe_ausente[k] or 0) + 1
      return 0
    end
    inertes[nome] = f
  end
  return f
end


local CRIA_QUADRO = { DzCreateFrameByTagName = 3, DzCreateFrame = 2, DzCreateSimpleFrame = 2 }
local function pai_padrao(nome, f)
  local pos = CRIA_QUADRO[nome]
  if not pos or type(f) ~= "function" then return f end
  return function(...)
    local a = table.pack(...)
    if a[pos] == nil or a[pos] == 0 then
      local ui = do_jass("DzGetGameUI")
      if type(ui) == "function" then a[pos] = ui() end
    end
    return f(table.unpack(a, 1, math.max(a.n, pos)))
  end
end
local function do_japi(nome)
  local v = do_jass(nome)


  if v ~= nil and __ydwe_stubs and __ydwe_stubs[nome] and type(nome) == "string" then
    local dz = do_jass("Dz" .. nome)
    if dz ~= nil and not __ydwe_stubs["Dz" .. nome] then return pai_padrao("Dz" .. nome, dz), "Dz" .. nome end
    local extra = __ydwe_japi_extra and __ydwe_japi_extra[nome]
    if extra ~= nil then return extra, nome end
  end
  if v ~= nil then
    if CRIA_QUADRO[nome] then return pai_padrao(nome, v), nome end
    if type(nome) == "string" and CRIA_QUADRO["Dz" .. nome] and v == do_jass("Dz" .. nome) then
      return pai_padrao("Dz" .. nome, v), nome
    end
    return v, nome
  end
  if type(nome) == "string" then
    v = do_jass("Dz" .. nome)
    if v ~= nil then return pai_padrao("Dz" .. nome, v), "Dz" .. nome end
    v = __ydwe_japi_extra and __ydwe_japi_extra[nome]
    if v ~= nil then return v, nome end



    if japi_registrada[nome] then return nil end


    return inerte_japi(nome), nome
  end
  return nil
end
__ydwe_do_japi = do_japi

local japi = tabela_de_funcoes(do_japi, "japi")
local dzapi = tabela_de_funcoes(do_japi, "dzapi")
local ai = tabela_de_funcoes(function(n) return rawget(G, n) end, "ai")

__ydwe_plataforma = __ydwe_plataforma or {}

local function nativa_comum(n)
  local v = i32_conv[n] or rawget(G, n)
  if v == nil and __ydwe_plataforma[n] and __JENV then v = rawget(__JENV, n) end
  return v
end
local comum = tabela_de_funcoes(nativa_comum, "common")


getmetatable(comum).__pairs = function(t)
  local nomes, i = {}, 0
  for n in pairs(__sig or {}) do
    if type(rawget(G, n)) == "function" or (__ydwe_plataforma[n] and type(nativa_comum(n)) == "function") then
      nomes[#nomes + 1] = n
    end
  end
  table.sort(nomes)
  return function()
    i = i + 1
    local n = nomes[i]
    if n == nil then return nil end
    return n, t[n]
  end, t, nil
end


local code = setmetatable({}, {
  __index = function(t, nome)
    local v = do_jass(nome)
    if type(v) ~= "function" then return v end
    return para_lua(nome, v)
  end,
  __newindex = function(t, nome, f)
    local env = __JENV or G
    if type(f) == "function" then
      rawset(env, nome, __wrap(para_jass(nome, f)))
    else
      rawset(env, nome, f)
    end
  end,
})


local gl_arr_cache = {}
local function arr_handle(nome, arr)
  local c = gl_arr_cache[nome]
  if c and c.arr == arr then return c.proxy end
  local proxy = setmetatable({}, {
    __index = function(_, i) return h2i(arr[i]) end,
    __newindex = function(_, i, v) if type(v) == "number" then v = i2h(v) end arr[i] = v end,
  })
  gl_arr_cache[nome] = { arr = arr, proxy = proxy }
  return proxy
end
local globals = setmetatable({}, {
  __index = function(t, k)
    local env = __JENV
    if env == nil then return nil end
    local v = env[k]
    if __enum_globais and __enum_globais[k] then return enum_id(v) end
    if __handle_globals[k] then

      if v ~= nil and type(v) ~= "number" then return h2i(v) end
      return v or 0
    end
    if __handle_arrays and __handle_arrays[k] and type(v) == "table" then return arr_handle(k, v) end
    return v
  end,
  __newindex = function(t, k, v)
    local env = __JENV
    if env == nil then return end
    if __handle_globals[k] and type(v) == "number" then v = i2h(v) end
    env[k] = v
  end,


  __pairs = function(t)


    local nomes, vistos, i = { }, { _G = true, _ENV = true, _VERSION = true }, 0
    local function junta(env, so_do_mapa)
      if type(env) ~= "table" then return end
      for k, v in next, env do
        local tv = type(v)
        if type(k) == "string" and not vistos[k] and tv ~= "function" and smatch_(k, "^[%a_][%w_]*$")
            and string.sub(k, 1, 2) ~= "__" and (tv ~= "table" or (so_do_mapa and rawget(G, k) == nil))
            and (not so_do_mapa or rawget(G, k) == nil) then
          vistos[k] = true
          nomes[#nomes + 1] = k
        end
      end
    end
    junta(__JENV, true)
    junta(G, false)
    table.sort(nomes)
    return function()
      i = i + 1
      local n = nomes[i]
      if n == nil then return nil end
      return n, t[n]
    end, t, nil
  end,
})


local function slk_view(raw)
  local cache = {}
  local recmt = { __index = function(t, k)
    local rec = rawget(t, "__rec")
    if type(k) == "string" then return rec[slower(k)] end
    return rec[k]
  end, __pairs = function(t) return next, rawget(t, "__rec"), nil end }
  local function reg(sid)
    local c = cache[sid]
    if c ~= nil then return c or nil end
    local rec = raw[sid]
    if rec == nil then cache[sid] = false return nil end
    c = setmetatable({ __rec = rec }, recmt)
    cache[sid] = c
    return c
  end
  return setmetatable({}, {
    __index = function(t, id) return reg(__id2s(id)) end,
    __pairs = function(t)
      local k = nil
      return function()
        k = next(raw, k)
        if k == nil then return nil end
        return k, reg(k)
      end, t, nil
    end,
  })
end
local slkraw = __slk_raw or {}
local slk = {}
for _, tipo in ipairs({ "unit", "ability", "item", "buff", "upgrade", "doodad", "destructable", "misc" }) do
  slkraw[tipo] = slkraw[tipo] or {}
  slk[tipo] = slk_view(slkraw[tipo])
end


local salvos = {}
__ydwe_salvos_hist = __ydwe_salvos_hist or {}

__ydwe_original = __ydwe_original or {}
local MARCA_ORIGINAL = "--ydwe-original:"

function __ydwe_original_de(s, qual)
  if type(s) ~= "string" or ssub(s, 1, #MARCA_ORIGINAL) ~= MARCA_ORIGINAL then return nil end
  local fim = sfind(s, "\n", #MARCA_ORIGINAL + 1, true)
  local e = fim and __ydwe_original[ssub(s, #MARCA_ORIGINAL + 1, fim - 1)]
  if not e then return nil end
  if qual == 2 then return e[2] end
  return (sgsub(e[1], "%x%x", function(h) return string.char(tonumber(h, 16)) end))
end
local storm = {
  load = function(nome)
    if type(nome) ~= "string" then return nil end
    local k = chave(nome)
    if salvos[k] ~= nil then return salvos[k] end
    local d = __ydwe_dados[k]
    if d ~= nil then return d end



    local marca = __ydwe_original[k] ~= nil and (MARCA_ORIGINAL .. k .. "\n") or ""
    if __ydwe_forma[k] ~= nil then return marca .. stub_do_modulo(k) end
    if marca ~= "" then return marca end
    return nil
  end,
  save = function(nome, dado)
    if type(nome) ~= "string" then return false end
    local k = chave(nome)
    salvos[k] = dado



    local lk = string.lower(k)
    if type(dado) == "string" and (ssub(lk, -4) == ".fdf" or ssub(lk, -4) == ".toc") then
      local h = __ydwe_salvos_hist[k]
      if h == nil then h = {} __ydwe_salvos_hist[k] = h end
      h[#h + 1] = dado
    end
    return true
  end,
  remove = function(nome) if type(nome) == "string" then salvos[chave(nome)] = nil end return true end,
}
storm.has = function(nome) return storm.load(nome) ~= nil end
storm.import = storm.load
storm.extract = function() return false end


local teclas = { BACKSPACE = 8, TAB = 9, ENTER = 13, RETURN = 13, SHIFT = 16, CTRL = 17, ALT = 18, PAUSE = 19,
  CAPSLOCK = 20, ESC = 27, ESCAPE = 27, SPACE = 32, PAGEUP = 33, PAGEDOWN = 34, END = 35, HOME = 36, LEFT = 37,
  UP = 38, RIGHT = 39, DOWN = 40, INSERT = 45, DELETE = 46 }
for i = 0, 9 do teclas[tostring(i)] = 48 + i end
for i = 65, 90 do teclas[string.char(i)] = i end
for i = 1, 12 do teclas["F" .. i] = 111 + i end
local message = {}
message.keyboard = message.keyboard or teclas
message.mouse = message.mouse or { LEFT = 1, RIGHT = 2, MIDDLE = 4 }
message.selection = message.selection or function()
  local u = __sel_first and __sel_first(GetLocalPlayer())
  if u == nil then return 0 end
  return GetHandleId(u)
end
message.button = message.button or function() return nil end
message.order_immediate = message.order_immediate or function(order, flag)
  if __local_order then __local_order("immediate", order, 0, 0, nil, flag) end
end
message.order_point = message.order_point or function(order, x, y, flag)
  if __local_order then __local_order("point", order, x, y, nil, flag) end
end
message.order_target = message.order_target or function(order, x, y, target, flag)
  if __local_order then __local_order("target", order, x, y, target, flag) end
end
message.order_enable_debug = function() end

message.load_window_infos = function() return {} end

message.origin_load = function(nome) return storm.load(nome) end

message.get_select_list = function()
  local u = message.selection()
  if u and u ~= 0 then return { u } end
  return {}
end




local function camera_local()
  if GetCameraEyePositionX == nil or GetCameraField == nil or CAMERA_FIELD_FIELD_OF_VIEW == nil then return nil end
  local ex, ey, ez = GetCameraEyePositionX(), GetCameraEyePositionY(), GetCameraEyePositionZ()
  local fx, fy, fz = GetCameraTargetPositionX() - ex, GetCameraTargetPositionY() - ey, GetCameraTargetPositionZ() - ez
  local nf = math.sqrt(fx * fx + fy * fy + fz * fz)
  if not nf or nf < 1e-6 then return nil end
  fx, fy, fz = fx / nf, fy / nf, fz / nf

  local rx, ry = fy, -fx
  local nr = math.sqrt(rx * rx + ry * ry)
  if nr < 1e-6 then return nil end
  rx, ry = rx / nr, ry / nr
  local ux, uy, uz = ry * fz, -rx * fz, rx * fy - ry * fx
  local t = math.tan((GetCameraField(CAMERA_FIELD_FIELD_OF_VIEW) or 1.22) / 2)
  if not t or t <= 0 then return nil end
  return { ex = ex, ey = ey, ez = ez, fx = fx, fy = fy, fz = fz, rx = rx, ry = ry, ux = ux, uy = uy, uz = uz, t = t,
           dist = nf }
end
message.world_to_screen = function(x, y, z)
  local c = camera_local()
  if c == nil then return nil end
  local vx, vy, vz = (x or 0) - c.ex, (y or 0) - c.ey, (z or 0) - c.ez
  local d = vx * c.fx + vy * c.fy + vz * c.fz
  if d <= 1e-3 then return nil end
  local sx = (vx * c.rx + vy * c.ry) / (d * c.t)
  local sy = (vx * c.ux + vy * c.uy + vz * c.uz) / (d * c.t)
  return 0.4 + sx * 0.4, 0.3 + sy * 0.4, c.dist / d
end

message.screen_to_world = function(sx, sy)
  local c = camera_local()
  if c == nil then return nil end
  local a, b = ((sx or 0.4) - 0.4) / 0.4 * c.t, ((sy or 0.3) - 0.3) / 0.4 * c.t
  local dx, dy, dz = c.fx + a * c.rx + b * c.ux, c.fy + a * c.ry + b * c.uy, c.fz + b * c.uz
  if dz >= -1e-6 then return nil end
  local k = -c.ez / dz
  return c.ex + k * dx, c.ey + k * dy, 0.0
end


local dbg = __dbg or {}
dbg.handle_ref = dbg.handle_ref or function() end
dbg.handle_unref = dbg.handle_unref or function() end
dbg.gchash = dbg.gchash or function() end
dbg.currentpos = dbg.currentpos or function() return "" end
dbg.handledef = function(h) return nil end
dbg.handlemax = function() return 0 end
dbg.handlecount = function() return 0 end
dbg.h2i = function(h) return h2i(h) end
dbg.i2h = function(i) return i end
dbg.functiondef = function() return nil end
dbg.globaldef = function() return nil end
dbg.handle_type = function() return nil end


local runtime = __rt_runtime or { handle_level = 0, sleep = false, console = false, version = 2 }
runtime.handle_level = runtime.handle_level or 0
local console = { write = function(...) end, read = function() return nil end, enable = false }
local log = { path = "log\\ydwe.log", level = "error" }
for _, n in ipairs({ "trace", "debug", "info", "warn", "error", "fatal" }) do
  log[n] = function(...) end
end
setmetatable(log, { __call = function() end })






local lni = {}
do
  local sbyte, smatch = string.byte, string.match
  local ESC = { n = "\n", t = "\t", r = "\r", a = "\a", b = "\b", f = "\f", v = "\v", ["\\"] = "\\", ['"'] = '"',
                ["'"] = "'", ["\n"] = "\n" }
  local function apara(s) return (sgsub(sgsub(s, "^[ \t\r\n]+", ""), "[ \t\r\n]+$", "")) end
  local function analisa(buf, nome, main)
    local i, n = 1, #buf
    if ssub(buf, 1, 3) == "\239\187\191" then i = 4 end
    local function erro(msg) error(string.format("lni %s: %s (byte %d)", tostring(nome), msg, i), 0) end
    local function pula()
      while i <= n do
        local c = sbyte(buf, i)
        if c == 32 or c == 9 or c == 13 or c == 10 then
          i = i + 1
        elseif c == 45 and sbyte(buf, i + 1) == 45 then
          local e = sfind(buf, "\n", i, true)
          i = e and e + 1 or n + 1
        else
          break
        end
      end
    end
    local function longa()
      local _, e, eq = sfind(buf, "^%[(=*)%[", i)
      if not e then return nil end
      local fecha = "]" .. eq .. "]"
      local a = e + 1
      if sbyte(buf, a) == 13 then a = a + 1 end
      if sbyte(buf, a) == 10 then a = a + 1 end
      local f = sfind(buf, fecha, a, true)
      if not f then erro("unfinished long string") end
      i = f + #fecha
      return ssub(buf, a, f - 1)
    end
    local function curta(q)
      local out = {}
      i = i + 1
      while true do
        local c = ssub(buf, i, i)
        if c == "" then erro("unfinished string") end
        if c == q then i = i + 1 break end
        if c == "\\" then
          local d = ssub(buf, i + 1, i + 1)
          local num = smatch(buf, "^%d%d?%d?", i + 1)
          if num then
            out[#out + 1] = schar(tonumber(num))
            i = i + 1 + #num
          else
            out[#out + 1] = ESC[d] or d
            i = i + 2
          end
        else
          out[#out + 1] = c
          i = i + 1
        end
      end
      return table.concat(out)
    end
    local function chave()
      local q = ssub(buf, i, i)
      local salvo = i
      if q == "'" or q == '"' then
        local k = curta(q)
        local _, e = sfind(buf, "^[ \t\r\n]*=", i)
        if e and ssub(buf, e + 1, e + 1) ~= "=" then i = e + 1 return k end
        i = salvo
        return nil
      end
      local k, e = smatch(buf, "^([^ \t\r\n=,{}%[%]'\"]+)[ \t\r\n]*=()", i)
      if k and ssub(buf, e, e) ~= "=" then
        i = e
        return tonumber(k) or k
      end
      return nil
    end
    local valor
    local function tabela()
      i = i + 1
      local t, idx = {}, 0
      while true do
        pula()
        local c = ssub(buf, i, i)
        if c == "" then erro("unfinished table") end
        if c == "}" then i = i + 1 break end
        if c == "," or c == ";" then
          i = i + 1
        else
          local k = chave()
          if k ~= nil then
            t[k] = valor(true)
          else
            idx = idx + 1
            t[idx] = valor(true)
          end
        end
      end
      return t
    end
    valor = function(em_tabela)
      pula()
      local c = ssub(buf, i, i)
      if c == "{" then return tabela() end
      if c == "'" or c == '"' then return curta(c) end
      if c == "[" then
        local s = longa()
        if s then return s end
      end
      local cru = smatch(buf, em_tabela and "^[^,;}\r\n]*" or "^[^\r\n]*", i) or ""
      i = i + #cru
      local corte = sfind(cru, "--", 1, true)
      if corte then cru = ssub(cru, 1, corte - 1) end
      cru = apara(cru)
      if cru == "true" then return true end
      if cru == "false" then return false end
      if cru == "nil" then return nil end
      local num = tonumber(cru)
      if num ~= nil then return num end
      return cru
    end
    local cur = nil
    while true do
      pula()
      if i > n then break end
      local c = ssub(buf, i, i)
      if c == "[" then
        local q = ssub(buf, i + 1, i + 1)
        local sec
        if q == "'" or q == '"' then
          i = i + 1
          sec = curta(q)
          local _, e = sfind(buf, "^[ \t\r\n]*%]", i)
          if not e then erro("unfinished section name") end
          i = e + 1
        else
          local s = smatch(buf, "^%[([^%]\r\n]*)%]", i)
          if not s then erro("bad section") end
          i = i + #s + 2
          sec = apara(s)
        end
        cur = main[sec]
        if type(cur) ~= "table" then cur = {} main[sec] = cur end
      else
        local k = chave()
        if k == nil then
          local fim = sfind(buf, "\n", i, true)
          i = fim and fim + 1 or n + 1
        else
          local v = valor(false)
          if cur then cur[k] = v else main[k] = v end
        end
      end
    end
    return main
  end
  function lni.load(conteudo, nome, envs, ...)
    local main, default, enum
    if type(envs) == "table" and (envs[1] ~= nil or envs[2] ~= nil or envs[3] ~= nil) then
      main, default, enum = envs[1], envs[2], envs[3]
    elseif type(envs) == "table" and select("#", ...) == 0 and next(envs) ~= nil then
      main = envs
    end
    main = main or {}
    if type(conteudo) == "string" then analisa(conteudo, nome, main) end
    return main, default or {}, enum or {}
  end
  lni.loader = lni.load
  lni.searcher = function() return nil end
  lni.packager = function(_, ...) return ... end
  lni.set_marco = function() end
  lni.init = function() end
  setmetatable(lni, { __call = function(_, ...) return lni.load(...) end })
end

local bignum = __ydwe_bignum or {}


local function inerte(nome)
  local mt = {}
  mt.__index = function(t, k) return inerte(nome .. "." .. tostring(k)) end
  mt.__call = function() return 0 end
  return setmetatable({}, mt)
end


local function nulo(nome)
  local mt = {}
  mt.__index = function(t, k) return nulo(nome .. "." .. tostring(k)) end
  mt.__call = function()
    __ydwe_ausente[nome] = (__ydwe_ausente[nome] or 0) + 1
    return nulo(nome)
  end
  return setmetatable({}, mt)
end

local function memoria()
  return setmetatable({}, { __index = function() return 0 end, __newindex = function() end })
end
local ffi = { cdef = function() end, C = inerte("ffi.C"), load = function(n) return inerte("ffi." .. tostring(n)) end,
              new = function() return memoria() end, cast = function() return memoria() end,
              string = function() return "" end,
              typeof = function() return function() return {} end end, sizeof = function() return 4 end,
              copy = function() end, fill = function() end, gc = function(v) return v end, os = "Windows",
              arch = "x86", abi = function() return false end, istype = function() return false end }


local function anota_ausente(t, lib, funcao)


  local idx = function(_, k)
    ausente(lib, k)
    if funcao and k ~= "hook" and type(k) == "string" then return inerte_japi(lib .. "." .. k) end
    return nil
  end
  local mt = getmetatable(t)
  if mt == nil then
    setmetatable(t, { __index = idx })
  elseif mt.__index == nil then
    mt.__index = idx
  end
end
anota_ausente(message, "message", true)





do
  local instalado = false
  local TECLAS = { 8, 9, 13, 27, 32, 33, 34, 35, 36, 37, 38, 39, 40, 45, 46 }
  for c = 48, 57 do TECLAS[#TECLAS + 1] = c end
  for c = 65, 90 do TECLAS[#TECLAS + 1] = c end
  for c = 96, 105 do TECLAS[#TECLAS + 1] = c end
  for c = 112, 123 do TECLAS[#TECLAS + 1] = c end
  local METAS = { 0, 1, 2, 4 }
  local function chama(msg)
    local h = rawget(message, "hook")
    if type(h) ~= "function" then return end
    local ok, e = xpcall(h, errh, msg)
    if not ok then __logerr("message.hook: " .. tostring(e)) end
  end
  local function instala()
    if instalado then return end
    instalado = true
    local ok_api = pcall(function()
      local tk, tm = CreateTrigger(), CreateTrigger()
      __fixa_raiz(tk)
      __fixa_raiz(tm)
      local tipos = {}
      for _, c in ipairs(TECLAS) do tipos[#tipos + 1] = { c, ConvertOsKeyType(c) } end
      for i = 0, bj_MAX_PLAYER_SLOTS - 1 do
        local p = Player(i)
        if GetPlayerController(p) == MAP_CONTROL_USER and GetPlayerSlotState(p) == PLAYER_SLOT_STATE_PLAYING then
          for _, t in ipairs(tipos) do
            for _, m in ipairs(METAS) do
              BlzTriggerRegisterPlayerKeyEvent(tk, p, t[2], m, true)
              BlzTriggerRegisterPlayerKeyEvent(tk, p, t[2], m, false)
            end
          end
          TriggerRegisterPlayerEvent(tm, p, EVENT_PLAYER_MOUSE_DOWN)
          TriggerRegisterPlayerEvent(tm, p, EVENT_PLAYER_MOUSE_UP)
        end
      end
      TriggerAddAction(tk, function()
        if GetTriggerPlayer() ~= GetLocalPlayer() then return end
        local k, code = BlzGetTriggerPlayerKey(), 0
        for _, t in ipairs(tipos) do if t[2] == k then code = t[1] break end end
        chama({ type = BlzGetTriggerPlayerIsKeyDown() and "key_down" or "key_up", code = code,
                state = BlzGetTriggerPlayerMetaKey() })
      end)
      TriggerAddAction(tm, function()
        if GetTriggerPlayer() ~= GetLocalPlayer() then return end
        local b, code = BlzGetTriggerPlayerMouseButton(), 1
        if b == MOUSE_BUTTON_TYPE_RIGHT then code = 2 elseif b == MOUSE_BUTTON_TYPE_MIDDLE then code = 4 end
        chama({ type = GetTriggerEventId() == EVENT_PLAYER_MOUSE_DOWN and "mouse_down" or "mouse_up", code = code,
                state = 0, x = BlzGetTriggerPlayerMouseX(), y = BlzGetTriggerPlayerMouseY() })
      end)
    end)
    if not ok_api then __logerr("message.hook: the key events could not be registered") end
  end
  local mt = getmetatable(message)
  mt.__newindex = function(t, k, v)
    rawset(t, k, v)
    if k == "hook" and type(v) == "function" then instala() end
  end
end
anota_ausente(dbg, "debug", true)
anota_ausente(runtime, "runtime")
anota_ausente(console, "console")
anota_ausente(storm, "storm")

setmetatable(LENV, { __index = function(_, k) ausente("_G", k) return nil end })
do
  local jc = __jass
  local mt = getmetatable(jc)
  local idx = mt and mt.__index
  if type(idx) == "function" then
    mt.__index = function(t, k)
      local v = idx(t, k)
      if v == nil then ausente("common", k) end
      return v
    end
  end
end
package.loaded["jass.common"] = comum


package.preload["_require"] = function() return true end
package.preload["_curpath"] = function() return true end


if __ydwe_forma["plugin_main.lua"] == nil then package.preload["plugin_main"] = function() return true end end
package.loaded["jass.japi"] = japi
package.loaded["jass.dzapi"] = dzapi
package.loaded["jass.ai"] = ai
package.loaded["jass.code"] = code
package.loaded["jass.hook"] = __hook
package.loaded["jass.globals"] = globals
package.loaded["jass.slk"] = slk
package.loaded["jass.debug"] = dbg
package.loaded["jass.runtime"] = runtime
package.loaded["jass.console"] = console
package.loaded["jass.storm"] = storm
package.loaded["jass.message"] = message
package.loaded["jass.bignum"] = bignum
package.loaded["jass.lni"] = lni
package.loaded["jass.log"] = log


if rawget(LENV, "log") == nil then rawset(LENV, "log", log) end


if rawget(LENV, "error_handle") == nil then
  rawset(LENV, "error_handle", function(msg)
    if __logerr then __logerr(debug.traceback(tostring(msg), 2)) end
    return msg
  end)
end
package.loaded["jass.dll"] = inerte("jass.dll")
package.loaded["yasio"] = nulo("yasio")
package.loaded["ffi"] = ffi
package.loaded["io"] = LENV.io
package.loaded["string"] = string
package.loaded["table"] = LENV.table
package.loaded["math"] = LENV.math
package.loaded["coroutine"] = LENV.coroutine
package.loaded["os"] = LENV.os
package.loaded["debug"] = LENV.debug
package.loaded["utf8"] = LENV.utf8
package.loaded["_G"] = LENV
__ydwe_libs = package.loaded



__ydwe_japi_extra = {}
do
  local X = __ydwe_japi_extra
  local function fh(id)
    local f = __JENV and rawget(__JENV, "DB_fh")
    if f == nil or id == nil or id == 0 then return nil end
    return f(id)
  end
  X.FrameSetLevel = function(f, l) local h = fh(f) if h then BlzFrameSetLevel(h, l) end end
  X.FrameSetWidth = function(f, w) local h = fh(f) if h then BlzFrameSetSize(h, w, BlzFrameGetHeight(h)) end end
  X.FrameSetHeight = function(f, v) local h = fh(f) if h then BlzFrameSetSize(h, BlzFrameGetWidth(h), v) end end
  X.FrameGetWidth = function(f) local h = fh(f) if h then return BlzFrameGetWidth(h) end return 0.0 end
  X.FrameGetHeight = function(f) local h = fh(f) if h then return BlzFrameGetHeight(h) end return 0.0 end


  X.FrameGetUnitButton = function()
    local o = __JENV and rawget(__JENV, "DB_origin")
    if o and ORIGIN_FRAME_PORTRAIT then return o(ORIGIN_FRAME_PORTRAIT, 0) end
    return 0
  end
  X.FrameSetModelScale = function(f, a, b, c) local h = fh(f) if h then BlzFrameSetScale(h, a or 1.0) end end
  X.FrameSetModelSize = function(f, s) local h = fh(f) if h then BlzFrameSetScale(h, s or 1.0) end end
  X.FrameSetTextFont = function(f, font, altura, flags) local h = fh(f) if h then BlzFrameSetFont(h, font, altura, flags or 0) end end
  X.FrameSetEditFocus = function(f, v) local h = fh(f) if h and BlzFrameSetFocus then BlzFrameSetFocus(h, v) end end
  X.DestroySimpleFrame = function(f) local h = fh(f) if h then BlzDestroyFrame(h) end end
  X.GetTargetObject = function() return BlzGetMouseFocusUnit() end


  local function selecionada()
    local f = __JENV and rawget(__JENV, "DzGetSelectedLeaderUnit")
    if type(f) == "function" then return f() end
    return nil
  end
  X.GetRealSelectUnit = selecionada
  X.GetPlayerSelectedUnit = function(p)
    if p == nil or p == GetLocalPlayer() then return selecionada() end
    return nil
  end
  X.SetOwner = function() end
  X.RegisterMessageEvent = function() end
  X.GetGameVersion = function() return 7000 end
  X.GetPluginVersion = function() return 0 end
  X.GetFps = function() return 60.0 end
  X.ShowFpsText = function() end
  X.GetMapName = function() return "" end
  X.GetMapPath = function() return "" end
  X.GetWar3Path = function() return "" end
  X.GetChatState = function() return false end
  X.SetHeroLevels = function() end
  X.EnableWideScreen = function() end
  X.VirtualMpqRegisterPath = function() end
  X.UnlockFps = function() end
  X.UnlockBlpSize = function() end
  X.EXSetItemColor = function() end



  X.EXBlendButtonIcon = function(base, icone, saida)
    if type(saida) ~= "string" then return false end
    local origem = (type(icone) == "string" and icone ~= "") and icone or base
    if type(origem) ~= "string" then return false end
    __ydwe_textura_apelido[saida] = __ydwe_textura_apelido[origem] or origem
    __ydwe_textura_apelido[string.lower(saida)] = __ydwe_textura_apelido[saida]
    return true
  end
  X.FrameGetModelAnimationName = function() return "" end
  for _, n in ipairs({ "FrameSetModelRotateX", "FrameSetModelRotateY", "FrameSetModelRotateZ", "FrameSetModelXY",
      "FrameSetModelColor", "FrameSetModelTexture", "FrameSetModelSpeed", "FrameSetAnimationByIndex",
      "FrameSetButtonCooldownModelSize", "FrameSetTextFontSpacing", "FrameSetSimpleFrameParent" }) do
    X[n] = function() end
  end
  X.RegisterFrameEvent = function() end

  local n_modelo = 0
  X.FrameAddModel = function(pai)
    local criar = __JENV and rawget(__JENV, "DzCreateFrameByTagName")
    if not criar then return 0 end
    n_modelo = n_modelo + 1
    return criar("SPRITE", "ydwe_model_" .. n_modelo, pai or 0, "", 0)
  end

  X.GetUnitAddress = function(u) if type(u) == "number" then return u end return u and GetHandleId(u) or 0 end

  X.FrameGetTextWidth = function(f)
    local h = fh(f)
    local t = h and BlzFrameGetText(h) or ""
    local n = utf8.len(t or "") or #(t or "")
    return n * 0.0075
  end
  X.FrameGetTextHeight = function(f)
    local h = fh(f)
    local t = h and BlzFrameGetText(h) or ""
    local linhas = 1
    for _ in sgmatch(t or "", "|n") do linhas = linhas + 1 end
    return linhas * 0.012
  end

  X.EXSetEffectVisible = function(e, v)
    local h = __i2hf(e)
    if h then BlzSetSpecialEffectAlpha(h, v and 255 or 0) end
  end
  X.FrameGetModelX = function() return 0.0 end
  X.FrameGetModelY = function() return 0.0 end
  X.FrameGetModelSize = function() return 1.0 end
  X.FrameGetModelSpeed = function() return 1.0 end
  X.GetTriggerMessage = function() return "" end
  X.SendCustomMessage = function() end



  X.GetUserId = function()
    local ok, nome = pcall(GetPlayerName, GetLocalPlayer())
    local h = (ok and type(nome) == "string") and StringHash(nome) or 0
    return 10000000 + ((h & 0x3FFFFFFF) % 89999999)
  end


  for _, n in ipairs({ "EXDclareButtonIcon", "EXBlpRect", "EXBlpSector", "EXPolygon", "EXClear",
      "png2tga_file" }) do
    X[n] = function() return false end
  end
  X.md5 = function(s) return __ydwe_original_de(s, 2) or __ydwe_md5(tostring(s or "")) end
  X.MD5 = X.md5
end





do
  local tab = rawget(G, "__ydwe_traducao")
  if type(tab) == "table" and next(tab) ~= nil then
    local maior = 0
    for k in pairs(tab) do if #k > maior then maior = #k end end
    local function largo(s, i)
      local b = sbyte(s, i)
      if b and b >= 226 and b <= 239 then return 3 end
      if b == 194 and sbyte(s, i + 1) == 183 then return 2 end
      return 0
    end
    local function troca_trecho(t)
      local r = tab[t]
      if r then return r end
      local out, i, n = {}, 1, #t
      while i <= n do
        local achou = nil
        local j = math.min(n, i + maior - 1)
        while j > i do
          local v = tab[ssub(t, i, j)]
          if v then achou = j break end
          j = j - 1
        end
        if achou then
          local v = tab[ssub(t, i, achou)]

          local ant = out[#out]
          if ant and sfind(ant, "[%w%)%]]$") and sfind(v, "^[%w%(%[]") then out[#out + 1] = " " end
          out[#out + 1] = v
          i = achou + 1
        else
          local l = largo(t, i)
          if l == 0 then l = 1 end
          out[#out + 1] = ssub(t, i, i + l - 1)
          i = i + l
        end
      end
      return table.concat(out)
    end
    local function traduz(s)
      if type(s) ~= "string" or not sfind(s, "[\194\226-\239]") then return s end
      local out, i, n, ini = {}, 1, #s, nil
      while i <= n do
        local l = largo(s, i)
        if l > 0 then
          if not ini then ini = i end
          i = i + l
        else
          if ini then out[#out + 1] = troca_trecho(ssub(s, ini, i - 1)) ini = nil end
          out[#out + 1] = ssub(s, i, i)
          i = i + 1
        end
      end
      if ini then out[#out + 1] = troca_trecho(ssub(s, ini, n)) end
      return table.concat(out)
    end
    __ydwe_traduz = traduz

    local onde = { BlzFrameSetText = 2, BlzFrameAddText = 2, DisplayTextToPlayer = 4, DisplayTimedTextToPlayer = 5,
      DisplayTimedTextFromPlayer = 5, SetTextTagText = 2, DialogSetMessage = 2, DialogAddButton = 2,
      DialogAddQuitButton = 3, MultiboardSetTitleText = 2, MultiboardSetItemValue = 2, LeaderboardSetLabel = 2,
      QuestSetTitle = 2, QuestSetDescription = 2, QuestItemSetDescription = 2, BlzSetUnitName = 2,
      BlzSetHeroProperName = 2, BlzSetItemName = 2, BlzSetItemTooltip = 2, BlzSetItemExtendedTooltip = 2,
      BlzSetItemDescription = 2, BlzSetAbilityTooltip = 2, BlzSetAbilityExtendedTooltip = 2,
      BlzSetAbilityResearchTooltip = 2, BlzSetAbilityResearchExtendedTooltip = 2, BlzSetUnitWeaponStringField = 3 }
    for nome, pos in pairs(onde) do
      local f = rawget(G, nome)
      if type(f) == "function" then
        rawset(G, nome, function(...)
          local a = table.pack(...)
          a[pos] = traduz(a[pos])
          return f(table.unpack(a, 1, a.n))
        end)
      end
    end
  end
end








do
  local CLICAVEIS = { GLUETEXTBUTTON = true, GLUEBUTTON = true, BUTTON = true, TEXTBUTTON = true, CHECKBOX = true,
    GLUECHECKBOX = true, POPUPMENU = true, GLUEPOPUPMENU = true, SLIDER = true, MENU = true, EDITBOX = true,
    GLUEEDITBOX = true }
  local trig_q = nil



  local habilita0 = rawget(G, "BlzFrameSetEnable")
  local mundo_em = -1
  local n_erro_wcb = 0
  local function wcb(codigo)
    local f = rawget(LENV, "WindowEventCallBack")
    if type(f) ~= "function" then return end
    local ok, e = pcall(f, codigo)

    if not ok and n_erro_wcb < 30 and type(__logerr) == "function" then
      n_erro_wcb = n_erro_wcb + 1
      __logerr("WindowEventCallBack(" .. tostring(codigo) .. "): " .. tostring(e))
    end
  end
  local id_do
  local function quadro_clicado()
    if GetTriggerPlayer() ~= GetLocalPlayer() then return end
    local f = BlzGetTriggerFrame()

    if __JENV and f then rawset(__JENV, "DB_mouse_focus", id_do(f)) end

    if os.clock() - mundo_em >= 0.05 then
      __ydwe_clique_de = "frame"
      wcb(1)
      wcb(2)
    end
    if f and habilita0 then habilita0(f, false) habilita0(f, true) end
  end



  local trig_ent, trig_sai = nil, nil
  id_do = function(f)
    local fid = __JENV and rawget(__JENV, "DB_fid")
    if f == nil or type(fid) ~= "function" then return 0 end
    return fid(f) or 0
  end
  local function entra()
    if GetTriggerPlayer() ~= GetLocalPlayer() or not __JENV then return end
    rawset(__JENV, "DB_mouse_focus", id_do(BlzGetTriggerFrame()))
  end
  local function sai()
    if GetTriggerPlayer() ~= GetLocalPlayer() or not __JENV then return end
    if rawget(__JENV, "DB_mouse_focus") == id_do(BlzGetTriggerFrame()) then rawset(__JENV, "DB_mouse_focus", 0) end
  end
  local function registra(f)
    if f == nil or type(BlzTriggerRegisterFrameEvent) ~= "function" then return end
    if trig_q == nil then
      trig_q = CreateTrigger()
      TriggerAddAction(trig_q, quadro_clicado)
      trig_ent = CreateTrigger()
      TriggerAddAction(trig_ent, entra)
      trig_sai = CreateTrigger()
      TriggerAddAction(trig_sai, sai)
    end
    BlzTriggerRegisterFrameEvent(trig_q, f, FRAMEEVENT_CONTROL_CLICK)
    BlzTriggerRegisterFrameEvent(trig_ent, f, FRAMEEVENT_MOUSE_ENTER)
    BlzTriggerRegisterFrameEvent(trig_sai, f, FRAMEEVENT_MOUSE_LEAVE)
  end




  __ydwe_textura_apelido = __ydwe_textura_apelido or {}
  __ydwe_texturas_usadas = {}
  local n_usadas = 0
  local function caminho(p, modelo)
    if type(p) ~= "string" then return p end
    local q = string.gsub(p, "\\\\+", "\\")
    local a = __ydwe_textura_apelido[q] or __ydwe_textura_apelido[string.lower(q)]
    if a then q = a end
    if n_usadas < 20000 and not __ydwe_texturas_usadas[q] then
      n_usadas = n_usadas + 1
      __ydwe_texturas_usadas[q] = true
    end
    local aus = __ydwe_textura_ausente
    if aus and (aus[q] or aus[string.lower(q)]) then return modelo and "" or (__ydwe_transparente or "") end
    return q
  end
  for _, nome in ipairs({ "BlzFrameSetTexture", "BlzFrameSetModel" }) do
    local f0 = rawget(G, nome)
    if type(f0) == "function" then
      local modelo = nome == "BlzFrameSetModel"
      rawset(G, nome, function(f, p, ...) return f0(f, caminho(p, modelo), ...) end)
    end
  end
  local por_tipo, por_modelo = rawget(G, "BlzCreateFrameByType"), rawget(G, "BlzCreateFrame")


  __ydwe_modelos_usados = {}
  if type(por_tipo) == "function" then
    rawset(G, "BlzCreateFrameByType", function(tipo, nome, pai, modelo, ...)
      if type(modelo) == "string" and modelo ~= "" then __ydwe_modelos_usados[tostring(tipo) .. "|" .. modelo] = true end
      local f = por_tipo(tipo, nome, pai, modelo, ...)
      if f ~= nil and CLICAVEIS[tostring(tipo)] then registra(f) end
      return f
    end)
  end
  if type(por_modelo) == "function" then
    rawset(G, "BlzCreateFrame", function(...)
      local f = por_modelo(...)
      registra(f)
      return f
    end)
  end

  __ydwe_ponte_mouse = function()
    if type(BlzGetTriggerPlayerMouseButton) ~= "function" then return end
    local t = CreateTrigger()
    for i = 0, bj_MAX_PLAYERS - 1 do
      TriggerRegisterPlayerEvent(t, Player(i), EVENT_PLAYER_MOUSE_DOWN)
      TriggerRegisterPlayerEvent(t, Player(i), EVENT_PLAYER_MOUSE_UP)
    end
    TriggerAddAction(t, function()
      if GetTriggerPlayer() ~= GetLocalPlayer() then return end
      __ydwe_clique_de = "world"
      mundo_em = os.clock()
      local desce = GetTriggerEventId() == EVENT_PLAYER_MOUSE_DOWN
      local dir = BlzGetTriggerPlayerMouseButton() == MOUSE_BUTTON_TYPE_RIGHT
      wcb(dir and (desce and 3 or 4) or (desce and 1 or 2))
    end)




    local w0, h0 = -1, -1
    local bate = CreateTimer()
    TimerStart(bate, 0.02, true, function()
      if type(BlzGetLocalClientWidth) == "function" then
        local w, h = BlzGetLocalClientWidth(), BlzGetLocalClientHeight()
        if w ~= w0 or h ~= h0 then
          w0, h0 = w, h
          wcb(9)
        end
      end
      wcb(10)
    end)
  end
end


do
  local K, R = {}, { 7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22, 5, 9, 14, 20, 5, 9, 14, 20, 5, 9, 14, 20,
    5, 9, 14, 20, 4, 11, 16, 23, 4, 11, 16, 23, 4, 11, 16, 23, 4, 11, 16, 23, 6, 10, 15, 21, 6, 10, 15, 21, 6, 10, 15, 21,
    6, 10, 15, 21 }



  K = { 0xd76aa478, 0xe8c7b756, 0x242070db, 0xc1bdceee, 0xf57c0faf, 0x4787c62a, 0xa8304613, 0xfd469501, 0x698098d8,
    0x8b44f7af, 0xffff5bb1, 0x895cd7be, 0x6b901122, 0xfd987193, 0xa679438e, 0x49b40821, 0xf61e2562, 0xc040b340,
    0x265e5a51, 0xe9b6c7aa, 0xd62f105d, 0x02441453, 0xd8a1e681, 0xe7d3fbc8, 0x21e1cde6, 0xc33707d6, 0xf4d50d87,
    0x455a14ed, 0xa9e3e905, 0xfcefa3f8, 0x676f02d9, 0x8d2a4c8a, 0xfffa3942, 0x8771f681, 0x6d9d6122, 0xfde5380c,
    0xa4beea44, 0x4bdecfa9, 0xf6bb4b60, 0xbebfbc70, 0x289b7ec6, 0xeaa127fa, 0xd4ef3085, 0x04881d05, 0xd9d4d039,
    0xe6db99e5, 0x1fa27cf8, 0xc4ac5665, 0xf4292244, 0x432aff97, 0xab9423a7, 0xfc93a039, 0x655b59c3, 0x8f0ccc92,
    0xffeff47d, 0x85845dd1, 0x6fa87e4f, 0xfe2ce6e0, 0xa3014314, 0x4e0811a1, 0xf7537e82, 0xbd3af235, 0x2ad7d2bb,
    0xeb86d391 }
  local function rol(x, n) x = x & 0xFFFFFFFF return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF end
  function __ydwe_md5(msg)
    local len = #msg
    msg = msg .. string.char(128) .. string.rep(string.char(0), (55 - len) % 64) .. string.pack("<I8", (len * 8) & 0xFFFFFFFFFFFFFFFF)
    local a0, b0, c0, d0 = 0x67452301, 0xefcdab89, 0x98badcfe, 0x10325476
    for bloco = 1, #msg, 64 do
      local M = { string.unpack("<I4I4I4I4I4I4I4I4I4I4I4I4I4I4I4I4", msg, bloco) }
      local A, B, C, D = a0, b0, c0, d0
      for i = 0, 63 do
        local F, g
        if i < 16 then F = (B & C) | (~B & D) g = i
        elseif i < 32 then F = (D & B) | (~D & C) g = (5 * i + 1) % 16
        elseif i < 48 then F = B ~ C ~ D g = (3 * i + 5) % 16
        else F = C ~ (B | ~D) g = (7 * i) % 16 end
        F = (F + A + K[i + 1] + M[g + 1]) & 0xFFFFFFFF
        A, D, C = D, C, B
        B = (B + rol(F, R[i + 1])) & 0xFFFFFFFF
      end
      a0, b0, c0, d0 = (a0 + A) & 0xFFFFFFFF, (b0 + B) & 0xFFFFFFFF, (c0 + C) & 0xFFFFFFFF, (d0 + D) & 0xFFFFFFFF
    end
    local out = string.pack("<I4I4I4I4", a0, b0, c0, d0)
    return (string.gsub(out, ".", function(c) return string.format("%02x", string.byte(c)) end))
  end
end



LENV.post_message = function()
  __ydwe_ausente["inerte.post_message"] = (__ydwe_ausente["inerte.post_message"] or 0) + 1
end



do
  local cod = { integer = "I", real = "R", string = "S", boolean = "B", code = "C", nothing = "V" }
  LENV.register_japi = function(texto)
    if type(texto) ~= "string" then return end
    for nome, takes, ret in sgmatch(texto, "native%s+([%w_]+)%s+takes%s+(.-)%s+returns%s+([%w_]+)") do
      __ydwe_japi_registrada[nome] = true
      if __sig[nome] == nil then
        local ps = {}
        if takes ~= "nothing" then
          for tipo in sgmatch(takes, "([%w_]+)%s+[%w_]+") do ps[#ps + 1] = cod[tipo] or "H" end
        end
        __sig[nome] = (cod[ret] or "H") .. "|" .. table.concat(ps, ",")
      end
    end
  end
end




__ydwe_execs = {}
function __ydwe_exec(nome)
  nome = sgsub(nome, "^[ \t\r\n]+", "")
  nome = sgsub(nome, "[ \t\r\n]+$", "")
  __ydwe_execs[#__ydwe_execs + 1] = nome
  local ok, e = xpcall(require, errh, nome)
  if not ok then __logerr("exec-lua " .. nome .. ": " .. tostring(e)) end
end
local function gancho_exec(nome_nativa)
  local f = rawget(G, nome_nativa)
  rawset(G, nome_nativa, function(s, ...)
    if type(s) == "string" and ssub(s, 1, 9) == "exec-lua:" then
      __ydwe_exec(ssub(s, 10))
      return 0
    end
    if f then return f(s, ...) end
    return 0
  end)
end
gancho_exec("AbilityId")
gancho_exec("Cheat")



do
  local f = rawget(G, "ExecuteFunc")
  rawset(G, "ExecuteFunc", function(nome, ...)
    if nome == "main" and __ydwe_main_rodou then
      __ydwe_ausente["main de novo (ExecuteFunc)"] = (__ydwe_ausente["main de novo (ExecuteFunc)"] or 0) + 1
      return
    end
    if f then return f(nome, ...) end
  end)
end

do
  local f = rawget(G, "StartCampaignAI")
  rawset(G, "StartCampaignAI", function(p, s)
    if type(s) == "string" and ssub(s, 1, 8) == "callback" then return end
    if f then return f(p, s) end
  end)
end



function __exs(n)
  local f = __exs_fn[n]
  if f == nil then return "" end
  local ok, r = xpcall(f, errh)
  if not ok then __logerr("exs " .. n .. ": " .. tostring(r)) return "" end
  if r == nil then return nil end
  return __tostr(r)
end
do
  local visto = {}
  rawset(G, "EXExecuteScript", function(s)
    if type(s) ~= "string" then return "" end
    local f = load("return " .. s, "=exs", "t", LENV) or load(s, "=exs", "t", LENV)
    if not f then
      local k = ssub(s, 1, 60)
      if not visto[k] then visto[k] = true __logerr("exs: does not compile: " .. k) end
      return ""
    end
    local ok, v = xpcall(f, errh)
    if not ok then __logerr("exs: " .. tostring(v)) return "" end
    if v == nil then return nil end
    return __tostr(v)
  end)
end
end
