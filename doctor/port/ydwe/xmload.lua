





local japi = require 'jass.japi'
local common = require 'jass.common'

local function null(name)
  local t, mt = {}, {}
  mt.__index = function(_, k) return null(name .. '.' .. tostring(k)) end
  mt.__newindex = function() end
  mt.__call = function() return null(name) end
  local zero = function() return 0 end
  mt.__add, mt.__sub, mt.__mul, mt.__div, mt.__mod, mt.__pow, mt.__unm, mt.__idiv = zero, zero, zero, zero, zero, zero, zero, zero
  mt.__concat = function(a, b) return (type(a) == 'table' and '' or a) .. (type(b) == 'table' and '' or b) end
  mt.__lt = function() return false end
  mt.__le = mt.__lt
  mt.__len = zero
  mt.__tostring = function() return 'null:' .. name end
  mt.__pairs = function() return function() end, t, nil end
  return setmetatable(t, mt)
end

cc, ccui, ccs, sp, cocos2dx, tolua, gl = null('cc'), null('ccui'), null('ccs'), null('sp'), null('cocos2dx'), null('tolua'), null('gl')
for _, k in ipairs({ 'mat4_getInversed', 'mat4_transformVector', 'mat4_multiply', 'mat4_decompose', 'mat4_translate',
  'mat4_createRotationZ', 'mat4_setIdentity', 'mat4_createTranslation', 'mat4_createRotation', 'vec2_isLineIntersect',
  'cc_mathutils_random' }) do _G[k] = null(k) end


local FRAMES, last = {}, 1000
local function fresh(parent, name)
  last = last + 1
  FRAMES[last] = { parent = parent, name = name, points = {}, visible = true, alpha = 255, scale = 1.0, w = 0.0, h = 0.0,
    text = '', tex = '', children = {} }
  if FRAMES[parent] then local c = FRAMES[parent].children c[#c + 1] = last end
  return last
end
local GAME_UI = fresh(0, 'GameUI')
local function of(f)
  if f == nil then return { points = {}, children = {}, w = 0.0, h = 0.0, text = '', tex = '', alpha = 255, scale = 1.0, visible = false } end
  if not FRAMES[f] then FRAMES[f] = { points = {}, visible = true, alpha = 255, scale = 1.0, w = 0.0, h = 0.0, text = '', tex = '', children = {} } end
  return FRAMES[f]
end
local FRAME_API = {
  XMGetGameUI = function() return GAME_UI end,
  XMDestroyFrame = function(f) if f ~= nil then FRAMES[f] = nil end end,
  XMFrameShow = function(f, v) of(f).visible = v end,
  XMFrameIsVisible = function(f) return of(f).visible end,
  XMFrameSetSize = function(f, w, h) local s = of(f) s.w, s.h = w, h end,
  XMFrameGetSize = function(f) local s = of(f) return s.w, s.h end,
  XMFrameGetWidth = function(f) return of(f).w end,
  XMFrameGetHeight = function(f) return of(f).h end,
  XMFrameSetText = function(f, x) of(f).text = x end,
  XMFrameGetText = function(f) return of(f).text end,
  XMFrameSetTexture = function(f, x) of(f).tex = x end,
  XMFrameGetTexture = function(f) return of(f).tex end,
  XMFrameGetTexture2 = function(f) return of(f).tex end,
  XMFrameSetAlpha = function(f, x) of(f).alpha = x end,
  XMFrameGetAlpha = function(f) return of(f).alpha end,
  XMFrameSetScale = function(f, x) of(f).scale = x end,
  XMFrameGetScale = function(f) return of(f).scale end,
  XMFrameSetParent = function(f, p) of(f).parent = p end,
  XMFrameGetParent = function(f) return of(f).parent end,
  XMFrameGetName = function(f) return of(f).name or '' end,
  XMFrameSetPoint = function(f, a, r, b, x, y) local s = of(f) s.points[#s.points + 1] = { a, r, b, x, y } end,
  XMFrameSetAbsolutePoint = function(f, a, x, y) local s = of(f) s.points[#s.points + 1] = { a, 0, 0, x, y } end,
  XMFrameClearAllPoints = function(f) of(f).points = {} end,
  XMFrameGetPoints = function(f) return of(f).points end,
  XMFrameGetChildren = function(f) return of(f).children end,
  XMFrameGetChildrens = function(f) return of(f).children end,
  XMFrameGetChildrenCount = function(f) return #of(f).children end,
  XMGetFrameClassName = function(f) return of(f).name or 'FRAME' end,
  XMIsSimpleFrame = function() return false end,
  XMFrameGetEnable = function() return true end,
  XMFrameIsIgnoreTrackEvents = function() return false end,
  XMGetMouseFocus = function() return 0 end,
  XMFrameGetTriggerUI = function() return 0 end,
}
local function creator(name)
  return function(...)
    local a, parent, label = { ... }, 0, name
    for i = 1, #a do
      local v = a[i]
      if math.type(v) == 'integer' and FRAMES[v] then parent = v end
      if type(v) == 'string' and label == name then label = v end
    end
    return fresh(parent, label)
  end
end


local jmt = getmetatable(japi) or {}
local jold = jmt.__index
local cache = {
  XMGetLuaParams = function(...) return ... end,
  XMGetLuaConvRet = function(...) return ... end,
  XMGetPlatformName = function() return 'local' end,
  XMGetTime = function() return 0 end,
}
local function resolve(name)
  local c = cache[name]
  if c ~= nil then return c end
  local f = FRAME_API[name]
  if not f and name:find('Create') and name:find('Frame') then f = creator(name) end
  if not f and (name:find('^XMFrameSet') or name:find('^XMFrameAdjust') or name:find('^XMFrameBind')) then
    f = function(frame, ...) of(frame)[name] = { ... } end
  end
  if not f then
    local s = name:sub(3)
    f = common[s]
    if type(f) ~= 'function' then f = common['Blz' .. s] end
    if type(f) ~= 'function' then
      local ok, g = pcall(function() return jold and jold(japi, 'Dz' .. s) end)
      f = ok and type(g) == 'function' and g or nil
    end
  end
  if type(f) ~= 'function' then
    local v
    if name:find('Points$') or name:find('Children') or name:find('List$') then v = function() return {} end
    elseif name:find('Text$') or name:find('Name$') or name:find('Font') or name:find('Texture') or name:find('Model$') then v = function() return '' end
    elseif name:find('Get') then v = function() return 0 end
    else v = function() end end
    f = v
  end
  cache[name] = f
  return f
end
jmt.__index = function(t, k)
  if k == 'XMSourcePath' then return nil end
  if type(k) == 'string' and k:sub(1, 2) == 'XM' then return resolve(k) end
  local v = jold and jold(t, k)
  if v == nil and type(k) == 'string' and k:sub(1, 2) == 'Dz' then return function() return 0 end end
  return v
end
setmetatable(japi, jmt)
local cmt = getmetatable(common) or {}
local cold = cmt.__index
cmt.__index = function(t, k)
  local v = cold and (type(cold) == 'function' and cold(t, k) or type(cold) == 'table' and cold[k]) or nil
  if v == nil and type(k) == 'string' and k:sub(1, 2) == 'Dz' then return function() return 0 end end
  return v
end
setmetatable(common, cmt)
XMGetLuaParams, XMGetLuaConvRet = cache.XMGetLuaParams, cache.XMGetLuaConvRet


package.preload['w3api'] = function()
  local base = { canonicalize = function(s) return s end, addBackslash = function(s) return s end,
    pathAppend = function(a, b) return (a or '') .. (b or '') end, isDebug = function() return false end,
    openDebugger = function() end, md5 = function(s) return string.format('%032x', #tostring(s)) end,
    GetTime = function() return 0 end, AsynTimerStart = function(t, d, r, f) return common.TimerStart(t, d, r, f) end }
  return setmetatable(base, { __index = function(_, k)
    local f = common[k]
    if type(f) == 'function' then return f end
    return function() end
  end })
end
package.preload['debugger'] = function() return null('debugger') end
package.preload['BigNum'] = function() return null('BigNum') end

local function json_decode(s)
  local i = 1
  local value
  local function ws() i = s:find('[^ \t\r\n]', i) or #s + 1 end
  local function str()
    local o, esc = {}, { n = '\n', t = '\t', r = '\r', b = '\b', f = '\f' }
    i = i + 1
    while true do
      local c = s:sub(i, i)
      if c == '' then error('json: open string') end
      if c == '"' then i = i + 1 break end
      if c == '\\' then
        local e = s:sub(i + 1, i + 1)
        if e == 'u' then
          o[#o + 1] = utf8.char(tonumber(s:sub(i + 2, i + 5), 16))
          i = i + 6
        else
          o[#o + 1] = esc[e] or e
          i = i + 2
        end
      else
        o[#o + 1] = c
        i = i + 1
      end
    end
    return table.concat(o)
  end
  value = function()
    ws()
    local c = s:sub(i, i)
    if c == '{' then
      local r = {}
      i = i + 1
      ws()
      if s:sub(i, i) == '}' then i = i + 1 return r end
      while true do
        ws()
        local k = str()
        ws()
        i = i + 1
        r[k] = value()
        ws()
        local d = s:sub(i, i)
        i = i + 1
        if d == '}' then return r end
      end
    elseif c == '[' then
      local r = {}
      i = i + 1
      ws()
      if s:sub(i, i) == ']' then i = i + 1 return r end
      while true do
        r[#r + 1] = value()
        ws()
        local d = s:sub(i, i)
        i = i + 1
        if d == ']' then return r end
      end
    elseif c == '"' then return str()
    elseif s:sub(i, i + 3) == 'true' then i = i + 4 return true
    elseif s:sub(i, i + 4) == 'false' then i = i + 5 return false
    elseif s:sub(i, i + 3) == 'null' then i = i + 4 return nil
    end
    local n = s:match('^-?%d+%.?%d*[eE]?[+-]?%d*', i)
    if not n then error('json: bad value at ' .. i) end
    i = i + #n
    return tonumber(n)
  end
  return value()
end
local function json_encode(v)
  local kind = type(v)
  if kind == 'table' then
    local o = {}
    if #v > 0 or next(v) == nil then
      for i = 1, #v do o[i] = json_encode(v[i]) end
      return '[' .. table.concat(o, ',') .. ']'
    end
    for k, x in pairs(v) do o[#o + 1] = string.format('%q', tostring(k)) .. ':' .. json_encode(x) end
    return '{' .. table.concat(o, ',') .. '}'
  elseif kind == 'string' then return string.format('%q', v)
  elseif kind == 'number' or kind == 'boolean' then return tostring(v)
  end
  return 'null'
end
package.preload['cjson'] = function() return { decode = json_decode, encode = json_encode } end


local XHR = {}
XHR.__index = XHR
function XHR.new() return setmetatable({ readyState = 0, status = 0, response = '' }, XHR) end
function XHR:open(method, url) self.url = url self.method = method end
function XHR:setRequestHeader() end
function XHR:registerScriptHandler(f) self.fn = f end
function XHR:unregisterScriptHandler() self.fn = nil end
function XHR:send()
  local t = common.CreateTimer()
  common.TimerStart(t, 0.05, false, function()
    common.DestroyTimer(t)
    self.status, self.readyState, self.response = 200, 4, '{"code":200,"msg":"ok","data":{}}'
    if self.fn then self.fn(self) end
  end)
end
rawset(cc, 'XMLHttpRequest', XHR)


local os0 = os or {}
os = setmetatable({ time = os0.time or function() return 0 end, clock = os0.clock or function() return 0.0 end,
  date = os0.date or function() return '' end, difftime = os0.difftime or function(a, b) return a - b end },
  { __index = function() return function() end end })
SafePairs = pairs
s2id = function(s) return (string.unpack('>I4', s .. string.rep(' ', 4 - #s))) end
id2s = function(i) return string.pack('>I4', i) end
warn = function() end
setfenv = function(f) return f end
getfenv = function() return _G end
for _, k in ipairs({ 'find', 'sub', 'match', 'gmatch', 'gsub', 'byte', 'len', 'upper', 'lower', 'rep', 'reverse' }) do
  local f = string[k]
  string[k] = function(s, ...)
    if type(s) ~= 'string' and type(s) ~= 'number' then s = '' end
    return f(s, ...)
  end
end
local tostring0, tonumber0 = tostring, tonumber
tostring = function(...) if select('#', ...) == 0 then return 'nil' end return tostring0(...) end
tonumber = function(...) if select('#', ...) == 0 then return nil end return tonumber0(...) end
if debug and debug.setmetatable then

  local m = {}
  m.__index = function() return nil end
  m.__call = function() return nil end
  local zero = function() return 0 end
  m.__add, m.__sub, m.__mul, m.__div, m.__mod, m.__pow, m.__unm, m.__idiv, m.__len = zero, zero, zero, zero, zero, zero, zero, zero, zero
  m.__concat = function(a, b) return (a == nil and '' or tostring(a)) .. (b == nil and '' or tostring(b)) end
  m.__lt = function() return false end
  m.__le = m.__lt
  debug.setmetatable(nil, m)
end


local require0 = require
local function safe_require(n)
  if n:find('^cocos') or n:find('^csb') then
    package.loaded[n] = package.loaded[n] or null('mod:' .. n)
    return package.loaded[n]
  end
  n = n:gsub('^scripts%.', '')
  local ok, r = pcall(require0, n)
  if ok then
    if n == 'engine.xmapi' and type(r) == 'table' then
      for k in pairs(r) do
        if type(k) == 'string' and k:sub(1, 2) == 'XM' and type(r[k]) == 'function' and
            (k:find('Frame') or k == 'XMGetGameUI' or k == 'XMGetMouseFocus') then
          r[k] = resolve(k)
          _G[k] = r[k]
        end
      end
    end
    return r
  end
  package.loaded[n] = null('mod:' .. n)
  return package.loaded[n]
end
require = safe_require
_G.require = safe_require





local jass_code = require 'jass.code'
local jass_slk = require 'jass.slk'
local unpack_ = table.unpack
local pending, pending_n = {}, 0
local args, args_n = {}, 0
local results, results_n, results_at = {}, 0, 1

local function push(...)
  for i = 1, select('#', ...) do
    pending_n = pending_n + 1
    pending[pending_n] = (select(i, ...))
  end
end

local function run(name)
  local f = _G[name]
  local a, n = pending, pending_n
  pending, pending_n = {}, 0
  results, results_n, results_at = {}, 0, 1
  if type(f) ~= 'function' then return nil end
  local old_a, old_n = args, args_n
  args, args_n = a, n
  local ok, r = pcall(f, unpack_(a, 1, n))
  args, args_n = old_a, old_n
  if not ok then error(r, 0) end
  if results_n == 0 and r ~= nil then results, results_n, results_at = { r }, 1, 1 end
  return r
end

local function take()
  local v = results[results_at]
  results_at = results_at + 1
  return v
end


local OBJECTS, OBJECT_IDS, next_object = {}, setmetatable({}, { __mode = 'k' }), 0x40000000
local function object_id(o)
  local id = OBJECT_IDS[o]
  if not id then
    next_object = next_object + 1
    id = next_object
    OBJECT_IDS[o], OBJECTS[id] = id, o
  end
  return id
end
local function as_integer(v)
  local t = type(v)
  if t == 'number' then return math.tointeger(v) or math.tointeger(v >= 0 and math.floor(v) or math.ceil(v)) or 0 end
  if t == 'boolean' then return v and 1 or 0 end
  if t == 'string' then return math.tointeger(tonumber(v) or 0) or 0 end
  if t == 'table' or t == 'userdata' then return object_id(v) end
  return 0
end


local BIG, next_big = {}, 0x20000000
local function new_big(v)
  next_big = next_big + 1
  BIG[next_big] = tonumber(v) or 0.0
  return next_big
end
local function big(id) return BIG[id] or 0.0 end

local RETURNS = {
  integer = function() return as_integer(take()) end,
  real = function() return (tonumber(take()) or 0.0) + 0.0 end,
  boolean = function() local v = take() return v == true or (type(v) == 'number' and v ~= 0) end,
  string = function() local v = take() return v == nil and '' or tostring(v) end,
}
RETURNS.fstring = RETURNS.string

local bridge_side = rawset
for _, name in ipairs({ 'boolean', 'cocoshandle', 'frame', 'handle', 'integer', 'path', 'real', 'string' }) do
  local n = 'LuaParam_' .. name
  local function f(v) push(v) end
  _G[n] = f
  bridge_side(common, n, f)
  bridge_side(japi, n, f)
end
local function lua_big(v) push(new_big(v)) end
_G.LuaParam_xmbignum = lua_big
bridge_side(common, 'LuaParam_xmbignum', lua_big)
bridge_side(japi, 'LuaParam_xmbignum', lua_big)
cache.XMGetLuaParams = function() return unpack_(args, 1, args_n) end
cache.XMGetLuaConvRet = function() results, results_n, results_at, pending, pending_n = pending, pending_n, 1, {}, 0 end
XMGetLuaParams, XMGetLuaConvRet = cache.XMGetLuaParams, cache.XMGetLuaConvRet

local unit_of = function(g, list)
  local n = 0
  while true do
    local u = common.FirstOfGroup(g)
    if u == nil or u == 0 then break end
    common.GroupRemoveUnit(g, u)
    n = n + 1
    list[n] = u
  end
  return n
end
local LISTS, next_list = {}, 0
local SLK_KIND = { [0] = 'ability', [1] = 'buff', [2] = 'unit', [3] = 'item', [4] = 'upgrade', [5] = 'doodad', [6] = 'destructable' }
local function property(kind, id, prop)
  local view = jass_slk[SLK_KIND[kind] or '']
  if view == nil then return nil end
  local row = view[id]
  if row == nil and math.type(id) == 'integer' then row = view[string.pack('>I4', id & 0xFFFFFFFF)] end
  if row == nil then return nil end
  return row[prop]
end
local function bits(v) v = v & 0xFFFFFFFF if v >= 0x80000000 then v = v - 0x100000000 end return v end
local BIT = {
  [0] = function(a, b) return a & b end, [1] = function(a, b) return a | b end, [2] = function(a, b) return a ~ b end,
  [3] = function(a, b) return ~a end, [4] = function(a, b) return (a & 0xFFFFFFFF) << b end,
  [5] = function(a, b) return (a & 0xFFFFFFFF) >> b end, [6] = function(a, b) return a & ~b end,
}

local BIG_OP = {
  [0] = function(a, b) return a + b end, [1] = function(a, b) return a - b end,
  [2] = function(a, b) return a * b end, [3] = function(a, b) return b ~= 0 and a / b or 0.0 end,
}

local BIG_CMP = {
  [0] = function(a, b) return a > b end, [1] = function(a, b) return a < b end, [2] = function(a, b) return a == b end,
}
local function enum_group(enum, ...)
  local g = common.CreateGroup()
  enum(g, ...)
  return g
end
local function polar(x, y, angle, distance, loc)
  local r = math.rad(angle)
  local px, py = x + distance * math.cos(r), y + distance * math.sin(r)
  if loc ~= nil and loc ~= 0 then common.MoveLocation(loc, px, py) end
  return px + 0.0
end
local DIRECT = {
  ExecuteLuaFunc = function(name) local r = run(name) if results_n > 0 then r = take() end return r == nil and '' or tostring(r) end,
  ExecuteLuaFuncNoRet = function(name) run(name) end,
  XMBitOperator = function(a, t, b) local f = BIT[t] return f and bits(f(a, b)) or 0 end,
  XMBigNumCreate = function(v) return new_big(v) end,
  XMBigNumCreateOne = function(v) return new_big(v) end,
  XMBigNumOperationReal2 = function(id, op, r) local f = BIG_OP[op] return new_big(f and f(big(id), r) or big(id)) end,
  XMBigNumCompare = function(a, op, b) local f = BIG_CMP[op] return f and f(big(a), big(b)) or false end,
  XMBigNumToReal = function(id) return big(id) + 0.0 end,
  XMBigNumToString = function(id, decimal) return string.format('%.' .. math.max(0, decimal) .. 'f', big(id)) end,
  SaveXMBignumHandle = function(t, p, c, v) common.SaveInteger(t, p, c, v) return true end,
  LoadXMBignumHandle = function(t, p, c) return common.LoadInteger(t, p, c) end,
  SaveXMTimerHandle = function(t, p, c, v) common.SaveInteger(t, p, c, v) return true end,
  HaveSavedXMTimer = function(t, p, c) return common.HaveSavedInteger(t, p, c) end,
  RemoveSavedXMTimer = function(t, p, c) common.RemoveSavedInteger(t, p, c) end,
  XMListCreate = function() next_list = next_list + 1 LISTS[next_list] = {} return next_list end,
  XMListDestroy = function(l) LISTS[l] = nil end,
  XMListGetUnit = function(l, i) local t = LISTS[l] return t and t[i] or nil end,
  XMEnumUnitInRange2 = function(x, y, r, l)
    local g = enum_group(common.GroupEnumUnitsInRange, x, y, r, nil)
    LISTS[l] = {}
    local n = unit_of(g, LISTS[l])
    common.DestroyGroup(g)
    return n
  end,
  XMEnumUnitInRange = function(x, y, r, filter, action)
    local g = enum_group(common.GroupEnumUnitsInRange, x, y, r, filter)
    common.ForGroup(g, action)
    common.DestroyGroup(g)
  end,
  XMEnumUnitInRect = function(rect, filter, action)
    local g = enum_group(common.GroupEnumUnitsInRect, rect, filter)
    common.ForGroup(g, action)
    common.DestroyGroup(g)
  end,
  XMGetObjectPropertyString = function(k, id, p) local v = property(k, id, p) return v == nil and '' or tostring(v) end,
  XMGetObjectPropertyInteger = function(k, id, p) return as_integer(tonumber(property(k, id, p))) end,
  XMGetObjectPropertyReal = function(k, id, p) return (tonumber(property(k, id, p)) or 0.0) + 0.0 end,
  XMGetColor = function(r, g, b, a) return bits(((a & 255) << 24) | ((r & 255) << 16) | ((g & 255) << 8) | (b & 255)) end,
  XMIsNetGame = function() return true end,
  XMAngleBetween = function(x1, y1, x2, y2) return math.deg(math.atan(y2 - y1, x2 - x1)) end,
  XMDistanceBetween = function(x1, y1, x2, y2) return math.sqrt((x2 - x1) ^ 2 + (y2 - y1) ^ 2) end,
  XMPolarProjectionEx = polar,
  XMLerpEx = function(x1, y1, x2, y2, alpha, loc)
    local px, py = x1 + (x2 - x1) * alpha, y1 + (y2 - y1) * alpha
    if loc ~= nil and loc ~= 0 then common.MoveLocation(loc, px, py) end
    return px + 0.0
  end,
  XMH2Unit = function(h) return h end,
  XMH2Item = function(h) return h end,
  XMH2Destructable = function(h) return h end,
  XMExecuteTrigger = function(t) common.TriggerExecute(t) end,
  XMGetUnitHeight = function(u) return common.GetUnitFlyHeight(u) end,
  XMGetGroupUnitCount = function(g) return common.BlzGroupGetSize(g) end,
  XMDisplayTextToPlayer = function(p, time, _mode, msg) common.DisplayTimedTextToPlayer(p, 0.0, 0.0, time, msg) end,
}


local function found(name)
  if cache[name] then return cache[name] end
  if FRAME_API[name] then return FRAME_API[name] end
  local s = name:sub(3)
  local f = common[s]
  if type(f) ~= 'function' then f = common['Blz' .. s] end
  if type(f) ~= 'function' and (name:find('^XMFrame')) then f = resolve(name) end
  return type(f) == 'function' and f or nil
end
for _, name in ipairs(XM_NATIVES) do
  local kind = name:match('^XMLuaReturn_(.+)$')
  local f = DIRECT[name]
  if f == nil and kind then
    local r = RETURNS[kind]
    f = r or function() local v = take() return type(v) == 'number' and v or nil end
  elseif f == nil and name == 'XMLuaParam_xmbignum' then
    f = function(id) push(big(id)) end
  elseif f == nil and name:find('^XMLuaParam_') then
    f = push
  elseif f == nil and name:sub(1, 2) == 'XM' then
    f = found(name)
  end
  if f then jass_code[name] = f end
end
require 'jass.runtime'.handle_level = 2
return true
