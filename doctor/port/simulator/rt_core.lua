



__RT_VERSION = "dream-s5-lua-1"
__TRACE = __TRACE or false

local G = _G
local type, tostring, tonumber, select, pairs, ipairs, rawget, rawset, setmetatable, getmetatable, pcall, xpcall, error =
      type, tostring, tonumber, select, pairs, ipairs, rawget, rawset, setmetatable, getmetatable, pcall, xpcall, error
local table, string, math = table, string, math
local unpack = table.unpack




local loglines = {}
local logcount = 0
local logdirty = false
local LOG_MAX = 1500











local dhead, dtail = {}, {}
local D_HEAD_MAX, D_TAIL_MAX = 420, 520
local ddirty, dcortou = false, false

function __dlog(msg)
  msg = tostring(msg)
  if #msg > 230 then msg = msg:sub(1, 230) end
  local t = 0.0
  local ok, v = pcall(__clock)
  if ok and type(v) == "number" then t = v end
  msg = string.format("%7.1f %s", t, msg)
  if #dhead < D_HEAD_MAX then
    dhead[#dhead + 1] = msg
  else
    dtail[#dtail + 1] = msg
    if #dtail > D_TAIL_MAX * 2 then
      local keep = {}
      for i = #dtail - D_TAIL_MAX + 1, #dtail do keep[#keep + 1] = dtail[i] end
      dtail = keep
      dcortou = true
    end
  end
  ddirty = true
end




local D_FIXO_MAX = 12
local dfixo = 0
function __dlog_fixo(msg)
  __dlog(msg)
  if dfixo >= D_FIXO_MAX then return end
  dfixo = dfixo + 1
  msg = tostring(msg)
  if #msg > 230 then msg = msg:sub(1, 230) end
  local t = 0.0
  local ok, v = pcall(__clock)
  if ok and type(v) == "number" then t = v end
  dhead[#dhead + 1] = string.format("%7.1f %s", t, msg)
  ddirty = true
end





__DS_PARTIDA = nil
function __ds_nome_arquivo(pid)
  if pid == nil then
    pid = 0
    local p = GetLocalPlayer and GetLocalPlayer()
    if p then pid = GetPlayerId(p) end
  end
  if __DS_PARTIDA ~= nil then return "desync_" .. pid .. "_" .. __DS_PARTIDA .. ".pld" end
  return "desync_" .. pid .. ".pld"
end

function __dflush(forcar)
  if not ddirty and not forcar then return end
  ddirty = false
  pcall(function()
    PreloadGenClear()
    PreloadGenStart()
    for i = 1, #dhead do Preload(dhead[i]) end
    if dcortou then Preload("        ... (trecho do meio descartado)") end
    for i = 1, #dtail do Preload(dtail[i]) end
    local pid = 0
    local p = GetLocalPlayer and GetLocalPlayer()
    if p then pid = GetPlayerId(p) end
    PreloadGenEnd("DreamS5\\" .. __ds_nome_arquivo(pid))
  end)
end

function __logflush()
  if not __TRACE or not logdirty then return end
  logdirty = false
  local ok = pcall(function()
    PreloadGenClear()
    PreloadGenStart()
    local n = #loglines
    local from = (n > LOG_MAX) and (n - LOG_MAX + 1) or 1
    for i = from, n do Preload(loglines[i]) end
    local pid = 0
    local p = GetLocalPlayer and GetLocalPlayer()
    if p then pid = GetPlayerId(p) end
    PreloadGenEnd("DreamS5\\log_" .. pid .. ".pld")
  end)
end

function __log(msg)
  logcount = logcount + 1
  msg = tostring(msg)
  if #msg > 240 then msg = msg:sub(1, 240) end
  loglines[#loglines + 1] = logcount .. " " .. msg
  if #loglines > LOG_MAX * 2 then
    local keep = {}
    for i = #loglines - LOG_MAX + 1, #loglines do keep[#keep + 1] = loglines[i] end
    loglines = keep
  end
  logdirty = true
  if __TRACE and __TRACE_SCREEN and print then pcall(print, msg) end
end

local errcount = 0










;(function()
local ERR_DISTINTAS_MAX = 40
local err_vistas, err_distintas = {}, 0
local function err_assinatura(msg)

  msg = tostring(msg)
  local p = msg:find("\n", 1, true)
  if p then msg = msg:sub(1, p - 1) end
  return (msg:gsub(":%d+:", ":?:"))
end

local function err_funcao(fn)
  if fn == nil then return nil end
  local nomear = rawget(G, "__nome_da_funcao")
  if type(nomear) ~= "function" then return nil end
  local ok, nome = pcall(nomear, fn)
  if ok and nome and nome ~= "?" then return nome end
  return nil
end

function __erro_detector(msg, fn)
  if __dlog == nil then return end
  local chave = err_assinatura(msg)
  local visto = err_vistas[chave]
  if visto == nil then
    if err_distintas >= ERR_DISTINTAS_MAX then return end
    err_distintas = err_distintas + 1
    err_vistas[chave] = 1
    local nome = err_funcao(fn)
    pcall(__dlog, "ERRO-LUA " .. (nome and ("em " .. nome .. ": ") or "") .. tostring(msg))
  else
    visto = visto + 1
    err_vistas[chave] = visto
    if visto == 1000 then pcall(__dlog, "ERRO-LUA x1000: " .. chave) end
  end
end

function __erros_resumo()
  local total = 0
  for _, n in pairs(err_vistas) do total = total + n end
  return err_distintas, total
end
end)()

function __logerr(msg, fn)
  errcount = errcount + 1
  if errcount <= 200 then
    __log("ERR " .. tostring(msg))
    if __TRACE and errcount <= 12 and print then pcall(print, "|cffff5555LUA ERR " .. tostring(msg) .. "|r") end
  end

  __erro_detector(msg, fn)





  local rt = rawget(_G, "__rt_runtime")
  local eh = rt and rawget(rt, "error_handle")
  if type(eh) == "function" then pcall(eh, msg) end

end

local function errh(e)
  if debug and debug.traceback then return tostring(debug.traceback(e, 2)) end
  return tostring(e)
end


function __wrap(f)
  if f == nil then return nil end
  if type(f) ~= "function" then return f end
  return function(...)
    local ok, r = xpcall(f, errh, ...)

    if not ok then __logerr(r, f) return nil end
    return r
  end
end




function __cat(...)
  local n = select("#", ...)
  if n == 2 then
    local a, b = ...
    return (a == nil and "" or a) .. (b == nil and "" or b)
  end
  local t = {...}
  for i = 1, n do
    local v = t[i]
    if v == nil then t[i] = "" elseif type(v) ~= "string" then t[i] = tostring(v) end
  end
  return table.concat(t, "", 1, n)
end

function __idiv(a, b)
  if b == 0 or b == nil or a == nil then return 0 end



  if math.type(a) == "integer" and math.type(b) == "integer" then
    local q = a // b
    if q < 0 and q * b ~= a then q = q + 1 end
    return q
  end
  local q = a / b
  if q >= 0 then q = math.floor(q) else q = math.ceil(q) end
  return math.tointeger(q) or q
end

function __div(a, b)
  if b == 0 or b == nil or a == nil then return 0.0 end
  return a / b
end

local function wrap32(r)
  if math.type(r) == "integer" then
    if r > 2147483647 or r < -2147483648 then
      r = ((r + 2147483648) & 0xFFFFFFFF) - 2147483648
    end
  end
  return r
end
__wrap32 = wrap32
function __imul(a, b) return wrap32(a * b) end
function __iadd(a, b) return wrap32(a + b) end
function __isub(a, b) return wrap32(a - b) end


do
  local made = 0
  for name, sg in pairs(__sig or {}) do
    local f = rawget(G, name)
    if type(f) == "function" then
      local ret, ps = sg:match("^(%w)|(.*)$")
      local params = {}
      for p in ps:gmatch("[^,]+") do params[#params + 1] = p end
      local spos = {}
      for i = 1, #params do if params[i] == "S" then spos[#spos + 1] = i end end
      if #spos > 0 and #params <= 12 then
        local args = {}
        for i = 1, #params do args[i] = "a" .. i end
        local checks = {}
        for _, i in ipairs(spos) do checks[#checks + 1] = string.format("if a%d == nil then a%d = '' end ", i, i) end
        local src = string.format("local f = ... return function(%s) %sreturn f(%s) end", table.concat(args, ","), table.concat(checks), table.concat(args, ","))
        local gen = load(src, "=strwrap", "t")
        if gen then
          rawset(G, name, gen(f))
          made = made + 1
        end
      end
    end
  end
  __strwrap_count = made
end

local mt_i = { __index = function() return 0 end }
local mt_r = { __index = function() return 0.0 end }
local mt_b = { __index = function() return false end }
function __arr_i() return setmetatable({}, mt_i) end
function __arr_r() return setmetatable({}, mt_r) end
function __arr_b() return setmetatable({}, mt_b) end

function __tostr(v)
  if v == nil then return "" end
  local t = type(v)
  if t == "string" then return v end
  if t == "boolean" then return v and "true" or "false" end
  if t == "number" then
    if math.type(v) == "integer" then return tostring(v) end
    if v == math.floor(v) and math.abs(v) < 1e15 then return string.format("%d", v) end
    return tostring(v)
  end
  return tostring(v)
end











__RAIZ_FIXA = __RAIZ_FIXA or {}
function __fixa_raiz(v)
  if v ~= nil then __RAIZ_FIXA[#__RAIZ_FIXA + 1] = v end
  return v
end
for _, nome in ipairs({ "bj_lastStartedTimer", "bj_lastCreatedGroup", "bj_queuedExecTimeoutTimer",
    "bj_volumeGroupsTimer", "bj_delayedSuspendDecayTimer", "bj_suspendDecayBoneGroup",
    "bj_suspendDecayFleshGroup" }) do
  __fixa_raiz(rawget(_G, nome))
end




local i2h = {}
local i2h_weak = setmetatable({}, { __mode = "v" })
local refcnt = {}
__i2h_registry = i2h

local native_GetHandleId = GetHandleId
__rawnat = __rawnat or {}
__rawnat["GetHandleId"] = native_GetHandleId

function GetHandleId(h)
  if h == nil then return 0 end
  local id = native_GetHandleId(h)
  if id ~= nil and id ~= 0 and i2h[id] == nil then i2h_weak[id] = h end
  return id
end
local GetHandleId = GetHandleId

function __h2i(h)
  if h == nil then return 0 end
  local id = native_GetHandleId(h)
  if id == nil or id == 0 then return 0 end




  if i2h[id] == nil then i2h[id] = h end

  if __fixa_handle then __fixa_handle(h) end

  return id
end

function __i2hf(v)
  if type(v) == "number" then
    if v == 0 then return nil end
    return i2h[v] or i2h_weak[v]
  end
  return v
end

function __register_handle_globals()
  local env = __JENV
  if env == nil then return end
  local n = 0
  for name in pairs(__handle_globals or {}) do
    local v = rawget(env, name)
    local tv = type(v)
    if v ~= nil and tv ~= "number" and tv ~= "string" and tv ~= "boolean" and tv ~= "function" then __h2i(v) n = n + 1 end
  end
  return n
end


local ids1, ids2 = {}, {}
function id2string(a)
  if a == 0 or a == nil then return "" end
  if a < 0 then a = a + 0x100000000 end
  local r = ids1[a]
  if r == nil then r = string.pack(">I4", a) ids1[a] = r ids2[r] = a end
  return r
end
function string2id(a)
  if (not a) or (#a == 0) then return 0 end
  local r = ids2[a]
  if r == nil then
    if #a == 4 then r = string.unpack(">I4", a) elseif #a < 4 then r = string.unpack(">I" .. #a, a) else r = string.unpack(">I4", a:sub(1, 4)) end
    ids2[a] = r ids1[r] = a
  end
  return r
end

function __handle_release(h)
  if h == nil then return end
  local id = GetHandleId(h)
  if id and id ~= 0 and (refcnt[id] or 0) <= 0 then i2h[id] = nil end
end

local function handle_ref(v)
  local id = (type(v) == "number") and v or (v and GetHandleId(v)) or 0
  if id == 0 then return end
  refcnt[id] = (refcnt[id] or 0) + 1
  if i2h[id] == nil and type(v) ~= "number" then i2h[id] = v end
end

local function handle_unref(v)
  local id = (type(v) == "number") and v or (v and GetHandleId(v)) or 0
  if id == 0 then return end
  local c = (refcnt[id] or 0) - 1
  if c <= 0 then refcnt[id] = nil; i2h[id] = nil else refcnt[id] = c end
end





__sig = __sig or {}
local sigcache = {}
local function parse_sig(name)
  local c = sigcache[name]
  if c then return c end
  local s = __sig[name]
  if not s then return nil end
  local ret, ps = s:match("^(%w)|(.*)$")
  local params = {}
  for p in ps:gmatch("[^,]+") do params[#params + 1] = p end
  c = { ret = ret, params = params, n = #params }
  sigcache[name] = c
  return c
end
__parse_sig = parse_sig


local orig = {}
__orig = orig
local function get_orig(name)
  local f = orig[name]
  if f == nil then
    f = rawget(G, name)
    if f ~= nil then orig[name] = f end
  end
  return f
end
__get_orig = get_orig


local function make_int_wrapper(name)
  local f = get_orig(name)
  if type(f) ~= "function" then return nil end
  local sg = parse_sig(name)
  if not sg then

    return function(...)
      local r = f(...)
      if type(r) == "userdata" then return __h2i(r) end
      return r
    end
  end
  local params, n, retH = sg.params, sg.n, (sg.ret == "H")
  local anyH = false
  for i = 1, n do if params[i] == "H" then anyH = true end end
  if not anyH then
    if retH then
      return function(...) return __h2i(f(...)) end
    end
    return f
  end
  return function(...)
    local a = {...}
    for i = 1, n do
      if params[i] == "H" then a[i] = __i2hf(a[i]) end
    end
    local r = f(unpack(a, 1, n))
    if retH then return __h2i(r) end
    return r
  end
end
__make_int_wrapper = make_int_wrapper




local jass = setmetatable({}, { __index = function(t, name)
  local v = rawget(G, name)
  if v == nil then return nil end
  if type(v) ~= "function" then return v end
  local w = make_int_wrapper(name)
  rawset(t, name, w)
  return w
end })
__jass = jass

local japi = setmetatable({}, { __index = function(t, name)
  local v = rawget(G, name)
  if v == nil then
    if __JENV then v = rawget(__JENV, name) end
    if v == nil then return nil end
  end
  if type(v) ~= "function" then return v end
  local w = make_int_wrapper(name)
  rawset(t, name, w)
  return w
end })
__japi = japi


local hookfns = {}
local function install_hook(name, f)
  local base = get_orig(name)
  if base == nil then base = rawget(G, name) end
  local sg = parse_sig(name)
  local params, n, retH = {}, 0, false
  if sg then params, n, retH = sg.params, sg.n, (sg.ret == "H") end
  local function def(...)
    if base == nil then return nil end
    local a = {...}
    for i = 1, n do if params[i] == "H" then a[i] = __i2hf(a[i]) end end
    local r = base(unpack(a, 1, n))
    if retH then return __h2i(r) end
    return r
  end
  local wrapper = function(...)
    local a = {...}
    local m = select("#", ...)
    if n > m then m = n end
    for i = 1, n do if params[i] == "H" then a[i] = __h2i(a[i]) end end
    a[m + 1] = def
    local r = f(unpack(a, 1, m + 1))
    if retH then return __i2hf(r) end
    return r
  end
  rawset(G, name, wrapper)
  if __JENV then rawset(__JENV, name, wrapper) end
end
local hook = setmetatable({}, {
  __index = function(t, k) return hookfns[k] end,
  __newindex = function(t, k, f)
    hookfns[k] = f
    if f ~= nil then install_hook(k, f) end
  end,
})
__hook = hook


__handle_globals = __handle_globals or {}
local glo = setmetatable({}, {
  __index = function(t, k)
    local env = __JENV
    if env == nil then return nil end
    return env[k]
  end,
  __newindex = function(t, k, v)
    local env = __JENV
    if env == nil then return end
    if __handle_globals[k] and type(v) == "number" then v = __i2hf(v) end
    rawset(env, k, v)
  end,
})


local function id2s(id)
  if type(id) ~= "number" then return id end
  id = id & 0xFFFFFFFF
  return string.pack(">I4", id)
end
__id2s = id2s
local function make_slk_view(raw)
  local cache = {}
  local recmt = { __index = function(t, k)
    local rec = rawget(t, "__rec")
    if type(k) == "string" then return rec[string.lower(k)] end
    return rec[k]
  end }
  return setmetatable({}, { __index = function(t, id)
    local sid = id2s(id)
    local c = cache[sid]
    if c ~= nil then return c or nil end
    local rec = raw[sid]
    if rec == nil then cache[sid] = false return nil end
    c = setmetatable({ __rec = rec }, recmt)
    cache[sid] = c
    return c
  end })
end
__slk_raw = __slk_raw or { unit = {}, ability = {}, item = {} }
local slk = { unit = make_slk_view(__slk_raw.unit), ability = make_slk_view(__slk_raw.ability), item = make_slk_view(__slk_raw.item) }
__slk = slk
function __slk_get(kind, id, field)
  local tab = __slk_raw[kind]
  if not tab then return nil end
  local rec = tab[id2s(id)]
  if not rec then return nil end
  return rec[string.lower(field)]
end
function __slk_set(kind, id, field, value)
  local tab = __slk_raw[kind]
  if not tab then return false end
  local sid = id2s(id)
  local rec = tab[sid]
  if not rec then rec = {} tab[sid] = rec end
  rec[string.lower(field)] = value
  return true
end


__sel = {}
function __sel_first(p)
  local pid = GetPlayerId(p)
  local t = __sel[pid]
  if t then
    for i = 1, #t do
      local u = t[i]
      if u ~= nil and GetUnitTypeId(u) ~= 0 then return u end
    end
  end
  return nil
end

local message = {
  selection = function()
    local u = __sel_first(GetLocalPlayer())
    if u == nil then return 0 end


    return GetHandleId(u)
  end,
  order_point = function(order, x, y, flag) if __local_order then __local_order("point", order, x, y, nil, flag) end end,
  order_target = function(order, x, y, target, flag) if __local_order then __local_order("target", order, x, y, target, flag) end end,
  order_immediate = function(order, flag) if __local_order then __local_order("immediate", order, 0, 0, nil, flag) end end,
}

local dbg = {
  handle_ref = handle_ref,
  handle_unref = handle_unref,
  gchash = function() end,
  currentpos = function() return "" end,
  handledef = function() end,
}
__dbg = dbg

local runtime = { handle_level = 0, error_handle = nil, sleep = false, console = false, version = 2 }
__rt_runtime = runtime
local console = { write = function(...) if print then pcall(print, ...) end end }
local storm = { load = function() return nil end, has = function() return false end, save = function() return false end }
local bignum = {}




if type(package) ~= "table" then package = {} end
package.loaded = package.loaded or {}
package.preload = package.preload or {}
package.path = package.path or ""
package.loaded["jass.common"] = jass
package.loaded["jass.japi"] = japi
package.loaded["jass.hook"] = hook
package.loaded["jass.globals"] = glo
package.loaded["jass.slk"] = slk
package.loaded["jass.debug"] = dbg
package.loaded["jass.runtime"] = runtime
package.loaded["jass.console"] = console
package.loaded["jass.storm"] = storm
package.loaded["jass.message"] = message
package.loaded["jass.bignum"] = bignum

package.preload["ac.message"] = function() return {} end

function require(name)
  local m = package.loaded[name]
  if m ~= nil then return m end
  local loader = package.preload[name]
  if loader == nil then error("module '" .. tostring(name) .. "' not found", 2) end
  local r = loader(name)
  if r == nil then r = package.loaded[name] end
  if r == nil then r = true end
  package.loaded[name] = r
  return r
end

if type(debug) ~= "table" then
  debug = { traceback = function(m) return tostring(m) end, getinfo = function() return nil end }
end


__clock_timer = nil
function __clock()
  if __clock_timer == nil then return 0.0 end
  return TimerGetElapsed(__clock_timer)
end




if type(os) ~= "table" then
  os = { clock = function() return __clock() end, time = function() return 0 end, date = function() return {} end }
else
  os.clock = function() return __clock() end
  if os.time == nil then os.time = function() return 0 end end
  if os.date == nil then os.date = function() return {} end end
end




__exs_fn = __exs_fn or {}
function __exs(n)
  local f = __exs_fn[n]
  if f == nil then return "" end
  local ok, r = pcall(f)
  if not ok then __logerr("exs " .. n .. ": " .. tostring(r)) return "" end
  return __tostr(r)
end

local function exs_dyn(s)

  local kind, id, field = s:match("^%(require'jass%.slk'%)%.(%w+)%[%s*(%-?%d+)%s*%]%.([%w_]+)$")
  if kind then
    local v = __slk_get(kind, tonumber(id), field)
    return __tostr(v)
  end

  local uid, bname, aid = s:match("^ac%.unit%.j_unit%((%-?%d+)%):add_buff'([^']+)'{atkunit=ac%.unit%.j_unit%((%-?%d+)%)}$")
  if uid then
    local ok, e = pcall(function()
      local ac = G.ac
      local u = ac.unit.j_unit(tonumber(uid))
      if u then u:add_buff(bname){ atkunit = ac.unit.j_unit(tonumber(aid)) } end
    end)
    if not ok then __logerr("exs add_buff: " .. tostring(e)) end
    return ""
  end
  local uid2, bname2 = s:match("^ac%.unit%.j_unit%((%-?%d+)%):remove_buff'([^']+)'%s*$")
  if uid2 then
    local ok, e = pcall(function()
      local u = G.ac.unit.j_unit(tonumber(uid2))
      if u then u:remove_buff(bname2) end
    end)
    if not ok then __logerr("exs remove_buff: " .. tostring(e)) end
    return ""
  end
  local uid3 = s:match("^ac%.unit%.j_unit%((%-?%d+)%):clearbuffs%(true%)$")
  if uid3 then
    local ok, e = pcall(function()
      local u = G.ac.unit.j_unit(tonumber(uid3))
      if u then u:clearbuffs(true) end
    end)
    if not ok then __logerr("exs clearbuffs: " .. tostring(e)) end
    return ""
  end
  local a1, a2 = s:match("^tostring%(P104MorpheusApplyDoom%((%-?%d+),(%-?%d+)%)%)$")
  if a1 then
    local f = G.P104MorpheusApplyDoom
    if type(f) ~= "function" then return "" end
    local ok, r = pcall(f, tonumber(a1), tonumber(a2))
    if not ok then __logerr("exs doom: " .. tostring(r)) return "" end
    return __tostr(r)
  end
  return nil
end

local exs_seen = {}
function EXExecuteScript(s)
  if type(s) ~= "string" then return "" end
  local r = exs_dyn(s)
  if r ~= nil then return r end
  if type(load) == "function" then
    local f = load("return " .. s, "=exs", "t") or load(s, "=exs", "t")
    if f then
      local ok, v = pcall(f)
      if ok then return __tostr(v) end
      __logerr("exs run: " .. tostring(v))
      __exs_erros = (__exs_erros or 0) + 1
      return ""
    end
  end
  local key = s:sub(1, 60)
  if not exs_seen[key] then
    exs_seen[key] = true
    __logerr("exs nao suportado: " .. key)
  end
  __exs_erros = (__exs_erros or 0) + 1
  return ""
end



__exs_erros = __exs_erros or 0




__luachunk_fn = __luachunk_fn or {}
function __luachunk(n)
  local f = __luachunk_fn[n]
  if f == nil then __logerr("luachunk " .. n .. " ausente") return end
  local ok, e = xpcall(f, errh)
  if not ok then
    p9_lua_error = tostring(e)
    __logerr("luachunk " .. n .. ": " .. tostring(e))
  end
end












__cb_motor_n = __cb_motor_n or 0
__cb_por_nativa = __cb_por_nativa or {}
__cb_sitio = __cb_sitio or setmetatable({}, { __mode = "k" })
__cb_nomes = __cb_nomes or setmetatable({}, { __mode = "k" })
__CB_POR_SITIO = { ForGroup = true, ForForce = true, EnumItemsInRect = true, EnumDestructablesInRect = true,
                   Filter = true, TimerStart = true }
function __wrap_motor(f, nome)
  if f == nil then return nil end
  if type(f) ~= "function" then return f end
  local por_sitio = __CB_POR_SITIO[nome]
  return function(...)
    __cb_motor_n = __cb_motor_n + 1
    __cb_por_nativa[nome] = (__cb_por_nativa[nome] or 0) + 1
    if por_sitio then __cb_sitio[f] = (__cb_sitio[f] or 0) + 1 end
    local ok, r = xpcall(f, errh, ...)
    if not ok then __logerr(r) return nil end
    return r
  end
end
__rawnat = __rawnat or {}
do
  local function wrap_native(name, argpos)
    local f = rawget(G, name)
    if type(f) ~= "function" then return end
    if __rawnat[name] then return end
    __rawnat[name] = f
    rawset(G, name, function(...)
      local a = {...}
      local n = select("#", ...)
      if argpos <= n then a[argpos] = __wrap_motor(a[argpos], name) end
      return f(unpack(a, 1, n))
    end)
  end
  wrap_native("TriggerAddAction", 2)
  wrap_native("Condition", 1)
  wrap_native("Filter", 1)
  wrap_native("TimerStart", 4)
  wrap_native("ForGroup", 2)
  wrap_native("ForForce", 2)
  wrap_native("EnumItemsInRect", 3)
  wrap_native("EnumDestructablesInRect", 3)
end


do
  local native_exec = __rawnat["ExecuteFunc"] or rawget(G, "ExecuteFunc")
  __rawnat["ExecuteFunc"] = native_exec
  __exec_target = nil
  function __jtramp()
    local f = __exec_target
    __exec_target = nil
    if f then

      __cb_motor_n = __cb_motor_n + 1
      __cb_por_nativa.ExecuteFunc = (__cb_por_nativa.ExecuteFunc or 0) + 1
      f()
    end
  end


  __exec_por_nome = {}
  rawset(G, "ExecuteFunc", function(name)
    if type(name) == "string" then __exec_por_nome[name] = (__exec_por_nome[name] or 0) + 1 end
    local env = __JENV or G
    local f = env[name]
    if type(f) ~= "function" then
      f = rawget(G, name)
      if type(f) ~= "function" then __logerr("ExecuteFunc: funcao ausente " .. tostring(name)) return end
    end
    __exec_target = __wrap(f)
    if native_exec then
      native_exec("__jtramp")
      if __exec_target ~= nil then

        __exec_native_ok = false
        __jtramp()
      else
        __exec_native_ok = true
      end
    else
      __jtramp()
    end
  end)
end


do
  local names = { "DestroyEffect", "DestroyTrigger", "DestroyTimer", "RemoveLocation", "DestroyGroup", "DestroyTextTag",
                  "DestroyLightning", "RemoveItem", "DestroyForce", "RemoveRect", "RemoveRegion", "DestroyImage",
                  "DestroyBoolExpr", "DestroyCondition", "DestroyFilter", "RemoveUnit", "DestroyUbersplat", "DestroyFogModifier" }
  for _, name in ipairs(names) do
    local f = rawget(G, name)
    if type(f) == "function" and not __rawnat[name] then
      __rawnat[name] = f
      rawset(G, name, function(h, ...)
        local r = f(h, ...)
        __handle_release(h)
        return r
      end)
    end
  end
end





























__handle_keep = {}
do
  local criadoras = {
    "CreateTimer", "CreateTrigger", "CreateGroup", "CreateForce", "Location", "Rect", "RectFromLoc",
    "CreateRegion", "Condition", "Filter", "And", "Or", "Not", "CreateTextTag", "InitHashtable",
    "InitGameCache", "CreateQuest", "CreateQuestItem", "CreateDefeatCondition", "CreateTimerDialog",
    "CreateLeaderboard", "CreateMultiboard", "CreateFogModifier", "CreateFogModifierRect",
    "CreateFogModifierRadius", "CreateFogModifierRadiusLoc", "AddSpecialEffect", "AddSpecialEffectLoc",
    "AddSpecialEffectTarget", "AddLightning", "AddLightningEx", "CreateImage", "CreateUbersplat",
    "CreateSound", "CreateSoundFilenameWithLabel", "CreateMIDISound", "DialogCreate", "CreateUnitPool",
    "CreateItemPool", "CreateTrackable",
  }
  for _, name in ipairs(criadoras) do
    local f = rawget(G, name)
    if type(f) == "function" then
      __handle_keep[name] = true
      if __rawnat[name] == nil then __rawnat[name] = f end
      rawset(G, name, function(...)
        local h = f(...)
        if h ~= nil then __h2i(h) end
        return h
      end)
    end
  end
end














do
  local criadoras_f5 = {

    "GetUnitLoc", "GetItemLoc",
    "GetUnitRallyPoint", "GetSpellTargetLoc", "GetOrderPointLoc", "GetStartLocationLoc",
    "GetCameraTargetPositionLoc", "GetCameraEyePositionLoc", "CameraSetupGetDestPositionLoc",
    "GetWorldBounds",

    "AddWeatherEffect", "CreateCameraSetup", "CreateSoundFromLabel", "CreateMinimapIcon",
    "CreateMinimapIconOnUnit", "CreateMinimapIconAtLoc", "CreateCommandButtonEffect",
    "CreateUpgradeCommandButtonEffect", "CreateLearnCommandButtonEffect",

    "MultiboardGetItem",

    "DialogAddButton", "DialogAddQuitButton",
  }
  for _, nome in ipairs(criadoras_f5) do
    local f = rawget(G, nome)
    if type(f) == "function" and not __handle_keep[nome] then
      __handle_keep[nome] = true
      if __rawnat[nome] == nil then __rawnat[nome] = f end
      rawset(G, nome, function(...)
        local h = f(...)
        if h ~= nil then __h2i(h) end
        return h
      end)
    end
  end


  local destruidoras_f5 = {
    "RemoveWeatherEffect", "DestroyCameraSetup", "MultiboardReleaseItem", "DestroySound",
    "DestroyQuest", "DestroyQuestItem", "DestroyDefeatCondition", "DestroyTimerDialog",
    "DestroyLeaderboard", "DestroyMultiboard", "DestroyMinimapIcon", "DestroyCommandButtonEffect",
    "DestroyUnitPool", "DestroyItemPool",
  }
  for _, nome in ipairs(destruidoras_f5) do
    local f = rawget(G, nome)
    if type(f) == "function" and __rawnat[nome] == nil then
      __rawnat[nome] = f
      rawset(G, nome, function(h, ...)
        local r = f(h, ...)
        __handle_release(h)
        return r
      end)
    end
  end
end
do


  local botoes_do_dialogo = {}
  local add = rawget(G, "DialogAddButton")
  local addq = rawget(G, "DialogAddQuitButton")
  local function anota(d, b)
    local k = (d ~= nil) and GetHandleId(d) or 0
    if b == nil or k == 0 then return b end
    local lista = botoes_do_dialogo[k]
    if lista == nil then lista = {} botoes_do_dialogo[k] = lista end
    lista[#lista + 1] = b
    return b
  end
  if type(add) == "function" then
    rawset(G, "DialogAddButton", function(d, ...) return anota(d, add(d, ...)) end)
  end
  if type(addq) == "function" then
    rawset(G, "DialogAddQuitButton", function(d, ...) return anota(d, addq(d, ...)) end)
  end
  local function solta_botoes(d)
    local k = (d ~= nil) and GetHandleId(d) or 0
    local lista = (k ~= 0) and botoes_do_dialogo[k] or nil
    if lista == nil then return end
    for i = 1, #lista do __handle_release(lista[i]) end
    botoes_do_dialogo[k] = nil
  end
  local limpa = rawget(G, "DialogClear")
  if type(limpa) == "function" and __rawnat["DialogClear"] == nil then
    __rawnat["DialogClear"] = limpa
    rawset(G, "DialogClear", function(d, ...)
      local r = limpa(d, ...)
      solta_botoes(d)
      return r
    end)
  end
  local mata = rawget(G, "DialogDestroy")
  if type(mata) == "function" and __rawnat["DialogDestroy"] == nil then
    __rawnat["DialogDestroy"] = mata
    rawset(G, "DialogDestroy", function(d, ...)
      local r = mata(d, ...)
      solta_botoes(d)
      __handle_release(d)
      return r
    end)
  end
end























if __PIN_HANDLES_ON == nil then __PIN_HANDLES_ON = false end
__PIN_HANDLES = __PIN_HANDLES or {}
__pin_n = 0
__pin_envolvidas = 0
do
  local pin = __PIN_HANDLES
  local ligado = __PIN_HANDLES_ON
  function __fixa_handle(h)
    if ligado then
      local th = type(h)
      if (th == "userdata" or th == "table") and pin[h] == nil then
        pin[h] = true
        __pin_n = __pin_n + 1
      end
    end
    return h
  end
  if ligado then
    local nomes = {}
    for nome, sg in pairs(__sig or {}) do
      if type(sg) == "string" and string.sub(sg, 1, 2) == "H|" and type(rawget(G, nome)) == "function" then
        nomes[#nomes + 1] = nome
      end
    end
    table.sort(nomes)
    for i = 1, #nomes do
      local f = rawget(G, nomes[i])
      rawset(G, nomes[i], function(...) return __fixa_handle(f(...)) end)
    end
    __pin_envolvidas = #nomes
  end
end

