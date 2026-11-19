





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






local jmt = getmetatable(japi) or {}
local jold = jmt.__index


local function dz(name)
  local f = common[name]
  if type(f) == 'function' then return f end
  local ok, g = pcall(function() return jold and jold(japi, name) end)
  if ok and type(g) == 'function' then return g end
  return nil
end
local FRAMES = {}
local DESTROY_CB = {}
__xm_frames = FRAMES
local function key(f) if f == nil or f == 0 then return nil end return f end
local function of(f)
  local k = key(f)
  if k == nil then return { points = {}, children = {}, w = 0.0, h = 0.0, text = '', tex = '', alpha = 255, scale = 1.0, visible = false } end
  local s = FRAMES[k]
  if not s then
    s = { points = {}, visible = true, alpha = 255, scale = 1.0, w = 0.0, h = 0.0, text = '', tex = '', children = {}, enable = true }
    FRAMES[k] = s
  end
  return s
end
local VIRTUAL_IDS = {}
local function call(name, ...)
  for i = 1, select('#', ...) do
    local v = select(i, ...)
    if v ~= nil and VIRTUAL_IDS[v] then return nil end
  end
  local f = dz(name)
  if f then
    local ok, r, r2 = pcall(f, ...)
    if ok then return r, r2 end
  end
  return nil
end



local EV = { HIDE = 8, SHOW = 9, POS = 10, WIDTH = 11, HEIGHT = 12, SCALE = 13, ADD = 14, REMOVE = 15, VALUE = 16 }
local DZ_MOUSE = { [1] = 1, [2] = 2, [3] = 3, [4] = 5, [5] = 4, [6] = 6, [7] = 12 }
local trigger_ui, trigger_child = {}, {}
local function fire(f, ev, child)
  local s = FRAMES[f]
  local hs = s and s.scripts and s.scripts[ev]
  if not hs then return end
  trigger_ui[#trigger_ui + 1], trigger_child[#trigger_child + 1] = f, child or 0
  for i = 1, #hs do
    local ok, e = pcall(hs[i])
    if not ok and __logerr then __logerr('xmload frame event ' .. ev .. ': ' .. tostring(e)) end
  end
  trigger_ui[#trigger_ui], trigger_child[#trigger_child] = nil, nil
end




local function added(p, f)
  if p == f then return end
  fire(p, EV.ADD, f)
end
local function flush_adds() end
__xm_flush_adds = flush_adds

local function point_at(f, a)
  a = a or 0
  for _, q in ipairs(of(f).points) do if q.anchor == a then return q end end
  return nil
end
local function put_point(s, p)
  for i, q in ipairs(s.points) do
    if q.anchor == p.anchor then s.points[i] = p return end
  end
  s.points[#s.points + 1] = p
end






local MOUSE_CB = {}
__xm_mouse = MOUSE_CB
local click_focus = nil
local click_key, click_down = nil, false
local click_hook = nil
local CLICK_NAMES = { _IN_EVENT = true, _BUTTON = true }
local function made(f, class, name, parent)
  if f == nil or f == 0 then return f end
  local s = of(f)
  s.class, s.name, s.parent = class or s.class or 'FRAME', name or s.name or '', parent
  local p = key(parent)
  if p ~= nil then local c = of(p).children c[#c + 1] = f added(p, f) end
  if click_hook and s.class == 'BUTTON' and CLICK_NAMES[s.name] then click_hook(f) end
  return f
end




local FRAME_TYPES = {}
for t in ('BACKDROP BUTTON CHATDISPLAY CHECKBOX CONTROL DIALOG EDITBOX FRAME GLUEBUTTON GLUECHECKBOX GLUEEDITBOX ' ..
    'GLUEPOPUPMENU GLUETEXTBUTTON HIGHLIGHT LISTBOX MENU MODEL POPUPMENU SCROLLBAR SIMPLEBUTTON SIMPLECHECKBOX ' ..
    'SIMPLEFRAME SIMPLESTATUSBAR SLASHCHATBOX SLIDER SPRITE TEXT TEXTAREA TEXTBUTTON TIMERTEXT'):gmatch('%S+') do
  FRAME_TYPES[t] = true
end
local function create_by_tag(tag, name, parent, template, id, class)
  local asked = parent
  if parent == nil or parent == 0 then parent = call('DzGetGameUI') end
  local kind = type(tag) == 'string' and tag:upper() or ''
  if not FRAME_TYPES[kind] then
    if __logerr then __logerr('xmload: frame type ' .. tostring(tag) .. ' unknown to Reforged, created as FRAME') end
    kind = 'FRAME'
  end
  local f = call('DzCreateFrameByTagName', kind, name or '', parent, template or '', id or 0)

  if asked == nil or asked == 0 then
    if f ~= nil and f ~= 0 then local s = of(f) s.class, s.name, s.parent = class or kind, name or '', 0 end
    return f
  end
  return made(f, class or kind, name, parent)
end


local function set_size(f, s)
  local w, h = s.w or 0.0, s.h or 0.0
  if s.class == 'TEXT' then
    if w < 0.0005 then w = 0.0 end
    if h < 0.0005 then h = 0.0 end
  end
  call('DzFrameSetSize', f, w, h)
end
local GAME_UI
local function game_ui()
  if GAME_UI == nil or GAME_UI == 0 then GAME_UI = call('DzGetGameUI') or 0 if GAME_UI ~= 0 then of(GAME_UI).class = 'FRAME' end end
  return GAME_UI
end





local INFO_BAR
local VIRTUAL = VIRTUAL_IDS
local function info_bar()
  if INFO_BAR == nil then
    INFO_BAR = 0x7FFF0001
    VIRTUAL[INFO_BAR] = true
    local s = of(INFO_BAR)
    s.class = 'FRAME'
    for n, class in ipairs({ '.?AVCSimpleFrame@@', '.?AVCSimpleFontString@@', '.?AVCSimpleTexture@@' }) do
      local id = INFO_BAR + n
      VIRTUAL[id] = true
      local c = of(id)
      c.class, c.parent = class, INFO_BAR
      s.children[#s.children + 1] = id
    end
  end
  return INFO_BAR
end



local HP_UI
local function hp_ui()
  if HP_UI == nil or HP_UI == 0 then
    local ui = game_ui()
    HP_UI = create_by_tag('FRAME', 'XMHPUIInterface', ui, '', 0, 'FRAME') or 0
    if HP_UI ~= 0 then
      call('DzFrameSetAllPoints', HP_UI, ui)
      of(HP_UI).w, of(HP_UI).h = 0.8, 0.6
    end
  end
  return HP_UI
end





local CONSOLE, CONSOLE_TILES = nil, {}
local console_hidden = false
local function console_show(v)
  if not v and not console_hidden then
    console_hidden = true
    call('DzFrameHideInterface')
  elseif v and console_hidden then
    console_hidden = false
    local f = common.BlzHideOriginFrames
    if f then pcall(f, false) end
  end
end
local function console_frame()
  if CONSOLE == nil then
    CONSOLE = 0x7FFF0010
    VIRTUAL_IDS[CONSOLE] = true
    local s = of(CONSOLE)
    s.class, s.name = '.?AVCSimpleFrame@@', 'ConsoleUI'

    local TILES = { { 256, 32, 0 }, { 87, 32 }, { 53, 32 }, { 256, 32, 2 }, { 32, 32 }, { 256, 176, 6 }, { 256, 150 },
      { 256, 176, 8 }, { 32, 176 } }
    for k, d in ipairs(TILES) do
      local t = CONSOLE + k
      VIRTUAL_IDS[t] = true
      CONSOLE_TILES[t] = true
      local c = of(t)
      c.class, c.parent, c.w, c.h = '.?AVCSimpleTexture@@', CONSOLE, d[1] / 1000, d[2] / 1000
      if d[3] then c.points[1] = { anchor = d[3], frame = CONSOLE, type = d[3], x = 0.0, y = 0.0 } end
      s.children[#s.children + 1] = t
    end
  end
  return CONSOLE
end
local FRAME_API = {
  XMGetGameUI = game_ui,

  XMGetGameFrame = game_ui,
  XMGetMinimap = function() return call('DzFrameGetMinimap') or 0 end,
  XMSimpleFrameFindByName = function(name, id)
    if name == 'ConsoleUI' then return console_frame() end
    return call('DzSimpleFrameFindByName', name, id or 0) or 0
  end,
  XMGetHPUIInterface = hp_ui,
  XMFrameGetInfoBar = info_bar,
  XMFrameGetLowest = function()
    local f = call('DzFrameGetLowest')
    if f == nil or f == 0 then f = game_ui() end
    return f
  end,
  XMCreateFrameByTagName = function(tag, name, parent, template, id) return create_by_tag(tag, name, parent, template, id) end,

  XMFrameCreatePortrait = function(name, parent) return create_by_tag('SPRITE', name, parent, '', 0, 'PORTRAIT') end,



  XMFrameSetDestroyByCode = function(k, fn) if k ~= nil then DESTROY_CB[k] = fn end end,
  XMFrameClearDestroyByCode = function(k) if k ~= nil then DESTROY_CB[k] = nil end end,
  XMDestroyFrame = function(f)
    if key(f) == nil then return end
    local s = of(f)
    if s.destroyed then return end


    trigger_ui[#trigger_ui + 1], trigger_child[#trigger_child + 1] = f, 0
    for _, cb in pairs(DESTROY_CB) do
      local ok, e = pcall(cb)
      if not ok and __logerr then __logerr('xmload destroy listener: ' .. tostring(e)) end
    end
    trigger_ui[#trigger_ui], trigger_child[#trigger_child] = nil, nil
    if key(s.parent) ~= nil then fire(s.parent, EV.REMOVE, f) end
    s.scripts = nil
    s.visible, s.destroyed = false, true
    call('DzFrameShow', f, false)
    call('DzFrameClearAllPoints', f)
    local p = key(s.parent)
    if p ~= nil and FRAMES[p] then
      local c = FRAMES[p].children
      for i = #c, 1, -1 do if c[i] == f then table.remove(c, i) end end
    end
  end,
  XMFrameShow = function(f, v)
    local s = of(f)
    if (s.visible and true or false) == (v and true or false) then return end
    s.visible = v
    if CONSOLE_TILES[f] then console_show(v) end
    call('DzFrameShow', f, v)
    fire(f, v and EV.SHOW or EV.HIDE)
  end,
  XMFrameIsVisible = function(f) return of(f).visible end,
  XMFrameSetSize = function(f, w, h) local s = of(f) s.w, s.h = w, h set_size(f, s) fire(f, EV.WIDTH) fire(f, EV.HEIGHT) end,
  XMFrameGetWidth2 = function(f) return of(f).w end,
  XMFrameGetHeight2 = function(f) return of(f).h end,
  XMFrameSetWidth = function(f, w) local s = of(f) s.w = w set_size(f, s) fire(f, EV.WIDTH) end,
  XMFrameSetHeight = function(f, h) local s = of(f) s.h = h set_size(f, s) fire(f, EV.HEIGHT) end,
  XMFrameGetWidth = function(f) return of(f).w end,
  XMFrameGetHeight = function(f) return of(f).h end,
  XMFrameSetText = function(f, x) of(f).text = x call('DzFrameSetText', f, x) end,
  XMFrameGetText = function(f) return of(f).text end,

  XMFrameSetStyle = function(f, st) of(f).style = st end,
  XMFrameGetStyle = function(f) return of(f).style or 0 end,
  XMFrameSetTexture = function(f, x, flag) of(f).tex = x call('DzFrameSetTexture', f, x, flag or 0) end,
  XMBackdropSetTexture = function(f, x, flag) of(f).tex = x call('DzFrameSetTexture', f, x, flag or 0) end,
  XMFrameGetTexture = function(f) return of(f).tex end,
  XMFrameGetTexture2 = function(f) return of(f).tex end,
  XMFrameSetAlpha = function(f, x) of(f).alpha = x call('DzFrameSetAlpha', f, x) end,
  XMFrameGetAlpha = function(f) return of(f).alpha end,
  XMFrameSetScale = function(f, x) of(f).scale = x call('DzFrameSetScale', f, x) fire(f, EV.SCALE) end,
  XMFrameGetScale = function(f) return of(f).scale end,
  XMFrameSetParent = function(f, p)
    local s = of(f)
    if key(p) ~= nil and FRAMES[p] then
      local simple = function(c) return type(c) == 'string' and c:find('^SIMPLE') ~= nil end
      if simple(s.class) ~= simple(FRAMES[p].class) then return end
    end
    call('DzFrameSetParent', f, p)
    local old = key(s.parent)
    if old ~= nil then
      local c = of(old).children
      for i = #c, 1, -1 do if c[i] == f then table.remove(c, i) end end
    end
    s.parent = p
    if old ~= nil and old ~= p then fire(old, EV.REMOVE, f) end
    if key(p) ~= nil then local c = of(p).children c[#c + 1] = f added(p, f) end
  end,
  XMFrameGetParent = function(f) return of(f).parent or 0 end,
  XMFrameGetName = function(f) return of(f).name or '' end,

  XMFrameSetPoint = function(f, a, r, b, x, y)
    local s = of(f)
    put_point(s, { anchor = a, frame = r, type = b, x = x, y = y })
    call('DzFrameSetPoint', f, a, r, b, x, y)
    fire(f, EV.POS)
  end,
  XMFrameSetAbsolutePoint = function(f, a, x, y)
    local s = of(f)
    put_point(s, { anchor = a, frame = 0, type = a, x = x, y = y })
    call('DzFrameSetAbsolutePoint', f, a, x, y)
    fire(f, EV.POS)
  end,
  XMFrameSetAllPoints = function(f, r) call('DzFrameSetAllPoints', f, r) end,
  XMFrameClearAllPoints = function(f) of(f).points = {} call('DzFrameClearAllPoints', f) end,
  XMFrameGetPointType = function(f, i) local p = point_at(f, i) return p and p.anchor or 0 end,
  XMFrameGetRelativeFrame = function(f, i) local p = point_at(f, i) return p and p.frame or 0 end,
  XMFrameGetRelativePoint = function(f, i) local p = point_at(f, i) return p and p.type or 0 end,



  XMFrameGetX = function(f, i) local p = point_at(f, i) return p and p.x or 0.0 end,
  XMFrameGetY = function(f, i) local p = point_at(f, i) return p and p.y or 0.0 end,
  XMFrameGetChildren = function(f, i) return of(f).children[i or 1] or 0 end,
  XMFrameGetChildrenCount = function(f) return #of(f).children end,
  XMFrameFindChildByName = function(f, name)
    for _, c in ipairs(of(f).children) do if of(c).name == name then return c end end
    return 0
  end,
  XMGetFrameClassName = function(f) return of(f).class or 'FRAME' end,
  XMFrameGetClassName = function(f) return of(f).class or 'FRAME' end,
  XMIsSimpleFrame = function(f) local c = of(f).class or '' return c:find('^SIMPLE') ~= nil end,
  XMFrameSetEnable = function(f, v) of(f).enable = v call('DzFrameSetEnable', f, v) end,
  XMFrameGetEnable = function(f) return of(f).enable ~= false end,
  XMFrameSetPriority = function(f, v) of(f).priority = v call('DzFrameSetPriority', f, v) end,
  XMFrameGetPriority = function(f) return of(f).priority or 0 end,
  XMFrameSetFontEx = function(f, font, size, flags)
    local s = of(f)
    s.font = { path = font, size = size, style = flags or 0 }
    call('DzFrameSetFont', f, font, size, flags or 0)
  end,
  XMFrameSetFont = function(f, font, size, flags)
    local s = of(f)
    s.font = { path = font, size = size, style = flags or 0 }
    call('DzFrameSetFont', f, font, size, flags or 0)
  end,

  XMFrameGetFont = function(f) local s = of(f).font return s and s.path or 'Fonts\\FRIZQT__.TTF' end,
  XMFrameGetFontSize = function(f) local s = of(f).font return s and s.size or 0.012 end,
  XMFrameGetFontStyle = function(f) local s = of(f).font return s and s.style or 0 end,
  XMFrameSetModel = function(f, m, kind, flag) call('DzFrameSetModel', f, m, kind or 0, flag or 0) end,
  XMFrameSetScriptByCode = function(f, ev, fn, sync)
    if key(f) == nil or fn == nil then return end
    local s = of(f)
    s.scripts = s.scripts or {}
    local hs = s.scripts[ev]
    if hs == nil then hs = {} s.scripts[ev] = hs end
    hs[#hs + 1] = fn
    local dz_ev = DZ_MOUSE[ev]
    if dz_ev and #hs == 1 then
      call('DzFrameSetScriptByCode', f, dz_ev, function() fire(f, ev) end, sync or false)
    end
  end,
  XMFrameIsIgnoreTrackEvents = function(f) return of(f).ignore == true end,
  XMFrameSetIgnoreTrackEvents = function(f, v) of(f).ignore = v end,
  XMGetMouseFocus = function()
    if click_focus ~= nil then return click_focus end
    return call('DzGetMouseFocus') or 0
  end,
  XMGetTriggerKey = function()
    if click_key ~= nil then return click_key end
    return call('DzGetTriggerKey') or 0
  end,
  XMIsKeyDown = function(k)
    if click_key ~= nil and k == click_key then return click_down end
    return call('DzIsKeyDown', k) or false
  end,
  XMTriggerRegisterMouseEventByCode = function(trig, btn, status, sync, fn)
    if fn ~= nil then
      local k = tostring(btn) .. ':' .. tostring(status)
      local l = MOUSE_CB[k]
      if l == nil then l = {} MOUSE_CB[k] = l end
      l[#l + 1] = fn
    end
    return call('DzTriggerRegisterMouseEventByCode', trig, btn, status, sync, fn)
  end,
  XMFrameGetTriggerUI = function()
    local f = trigger_ui[#trigger_ui]
    if f ~= nil then return f end
    return call('DzGetTriggerUIEventFrame') or 0
  end,
  XMFrameGetTriggerChild = function() return trigger_child[#trigger_child] or 0 end,
}
local function run_mouse(k)
  local l = MOUSE_CB[k]
  if not l then return end
  for i = 1, #l do
    local ok, e = pcall(l[i])
    if not ok and __logerr then __logerr('xmload mouse handler: ' .. tostring(e)) end
  end
end
click_hook = function(f)

  FRAME_API.XMFrameSetScriptByCode(f, 5, function()
    local p = common.GetTriggerPlayer()
    if p ~= nil and common.GetPlayerId(p) ~= common.GetPlayerId(common.GetLocalPlayer()) then return end

    click_focus, click_key = f, 1
    click_down = true
    run_mouse('1:1')
    click_down = false
    run_mouse('1:0')
    click_focus, click_key = nil, nil
  end, false)
end
local function creator(name)
  return function(...)
    local a = { ... }

    local tag, label, parent = nil, nil, nil
    for i = 1, #a do
      local v = a[i]
      if type(v) == 'string' then
        if tag == nil and FRAME_TYPES[v:upper()] then tag = v elseif label == nil then label = v end
      elseif parent == nil and v ~= nil and v ~= 0 and (math.type(v) ~= 'integer' or FRAMES[v]) then parent = v end
    end
    local kind = tag or ((name:find('Portrait') or name:find('Model')) and 'SPRITE' or 'FRAME')
    return create_by_tag(kind, label or '', parent, '', 0)
  end
end

local DZ_CREATORS = {
  DzCreateFrameByTagName = function(f) return function(tag, name, parent, template, id)
    local kind = type(tag) == 'string' and FRAME_TYPES[tag:upper()] and tag or 'FRAME'
    return made(f(kind, name, parent, template, id), kind, name, parent) end end,
  CreateFrameByTagName = function(f) return function(tag, name, parent, template, id)
    local kind = type(tag) == 'string' and FRAME_TYPES[tag:upper()] and tag or 'FRAME'
    return made(f(kind, name, parent, template, id), kind, name, parent) end end,
  DzCreateFrame = function(f) return function(template, parent, id) return made(f(template, parent, id), template, template, parent) end end,
  DzCreateSimpleFrame = function(f) return function(template, parent, id)
    return made(f(template, parent, id), 'SIMPLE' .. tostring(template), template, parent) end end,
  DzDestroyFrame = function() return function(fr) FRAME_API.XMDestroyFrame(fr) end end,
  DzFrameGetFont = function() return function(fr) local s = of(fr).font if s then return s.path, s.size, s.style end return 'Fonts\\FRIZQT__.TTF', 0.012, 0 end end,
  DzFrameSetFont = function(f) return function(fr, font, size, flags)
    of(fr).font = { path = font, size = size, style = flags or 0 }
    return f(fr, font, size, flags) end end,
}





local clock_timer
local function game_time()
  if clock_timer == nil and common.CreateTimer then
    clock_timer = common.CreateTimer()
    common.TimerStart(clock_timer, 1000000.0, false, nil)
  end
  return clock_timer and (common.TimerGetElapsed(clock_timer) + 0.0) or 0.0
end
local cache = {
  XMGetLuaParams = function(...) return ... end,
  XMGetLuaConvRet = function(...) return ... end,
  XMGetPlatformName = function() return 'local' end,
  XMGetTime = game_time,
}
local function resolve(name)
  local c = cache[name]
  if c ~= nil then return c end
  local f = FRAME_API[name]
  if not f and __xm_nat then f = __xm_nat[name] end
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
local wrapped = {}
jmt.__index = function(t, k)
  if k == 'XMSourcePath' then return nil end
  if type(k) == 'string' and k:sub(1, 2) == 'XM' then return resolve(k) end
  if DZ_CREATORS[k] then
    if wrapped[k] == nil then
      local f = jold and jold(t, k)
      wrapped[k] = DZ_CREATORS[k](type(f) == 'function' and f or function() return 0 end)
    end
    return wrapped[k]
  end
  local v = jold and jold(t, k)
  if v == nil and type(k) == 'string' and k:sub(1, 2) == 'Dz' then return function() return 0 end end
  return v
end
setmetatable(japi, jmt)
local cmt = getmetatable(common) or {}
local cold = cmt.__index






local TRIG_BY_NAME, NAME_BY_TRIG, trig_n = {}, {}, 0
local COMMON_EXTRA = {
  EncryptInt = function(v) return v end,
  DecryptInt = function(v) return v end,
  HPHighRefresh = function() end,
  XMGetTriggerName = function(trig)
    if trig == nil then return '' end
    local n = NAME_BY_TRIG[trig]
    if n == nil then
      trig_n = trig_n + 1
      n = '__xm_trig_' .. trig_n
      NAME_BY_TRIG[trig], TRIG_BY_NAME[n] = n, trig
    end
    return n
  end,
}

cache.XMGetTriggerName = COMMON_EXTRA.XMGetTriggerName
local exec_wrapped = nil
cmt.__index = function(t, k)

  if COMMON_EXTRA[k] then return COMMON_EXTRA[k] end
  local v = cold and (type(cold) == 'function' and cold(t, k) or type(cold) == 'table' and cold[k]) or nil
  if k == 'ExecuteFunc' and type(v) == 'function' then
    if exec_wrapped == nil then
      local orig = v
      exec_wrapped = function(name)
        local trig = TRIG_BY_NAME[name]
        if trig ~= nil then return common.TriggerExecute(trig) end
        return orig(name)
      end
    end
    return exec_wrapped
  end
  if v == nil and type(k) == 'string' and k:sub(1, 2) == 'Dz' then return function() return 0 end end
  return v
end
setmetatable(common, cmt)
XMGetLuaParams, XMGetLuaConvRet = cache.XMGetLuaParams, cache.XMGetLuaConvRet


package.preload['w3api'] = function()
  local base = { canonicalize = function(s) return s end, addBackslash = function(s) return s end,
    pathAppend = function(a, b) return (a or '') .. (b or '') end, isDebug = function() return false end,
    openDebugger = function() end, md5 = function(s) return string.format('%032x', #tostring(s)) end,
    GetTime = game_time, AsynTimerStart = function(t, d, r, f) return common.TimerStart(t, d, r, f) end }



  local function point_copy(p) return { anchor = p.anchor, frame = p.frame, type = p.type, x = p.x, y = p.y } end
  local W = {
    CreateFrameByTagName = function(...) return FRAME_API.XMCreateFrameByTagName(...) end,
    DestroyFrame = function(f) return FRAME_API.XMDestroyFrame(f) end,
    GetGameUI = function() return game_ui() end,
    GetMouseFocus = function() return FRAME_API.XMGetMouseFocus() end,
    FrameGetClassName = function(f) return FRAME_API.XMGetFrameClassName(f) end,
    FrameIsSimple = function(f) return FRAME_API.XMIsSimpleFrame(f) end,
    FrameGetSize = function(f) local s = of(f) return { width = s.w, height = s.h } end,
    FrameGetSize2 = function(f) local s = of(f) return { width = s.w, height = s.h } end,
    FrameGetPoints = function(f)
      local o = {}
      for i, p in ipairs(of(f).points) do o[i] = point_copy(p) end
      return o
    end,
    FrameGetPoint = function(f, i) local p = of(f).points[(i or 0) + 1] return p and point_copy(p) or nil end,
    FrameGetXY = function(f) local p = of(f).points[1] return p and p.x or 0.0, p and p.y or 0.0 end,
    FrameGetXY2 = function(f) local p = of(f).points[1] return p and p.x or 0.0, p and p.y or 0.0 end,
    FrameGetFont = function(f)
      local s = of(f).font
      local size = s and s.size or 0.012
      return { path = s and s.path or 'Fonts\\FRIZQT__.TTF', size = size, style = s and s.style or 0, realSize = size }
    end,
    FrameGetChildrenCount = function(f) return #of(f).children end,
    FrameGetChildren = function(f, i) return of(f).children[i or 1] or 0 end,
    FrameGetChildrens = function(f)
      local o = {}
      for i, c in ipairs(of(f).children) do o[i] = c end
      return o
    end,
    FrameGetGColor = function() return { r = 255, g = 255, b = 255, a = 255 } end,
    GetImageSize = function() return 0, 0 end,
  }


  local function units_of(fill, filter)
    local g = common.CreateGroup()
    fill(g)
    local list, n = {}, 0
    while true do
      local u = common.FirstOfGroup(g)
      if u == nil or u == 0 then break end
      common.GroupRemoveUnit(g, u)
      if filter == nil or filter(u) ~= false then n = n + 1 list[n] = u end
    end
    common.DestroyGroup(g)
    return list
  end
  local function in_rect(rect, filter) return units_of(function(g) common.GroupEnumUnitsInRect(g, rect, nil) end, filter) end
  local function in_range(x, y, r, filter) return units_of(function(g) common.GroupEnumUnitsInRange(g, x, y, r, nil) end, filter) end
  W.GroupEnumUnitsInRect = in_rect
  W.EnumUnitsInRect1 = in_rect
  W.EnumUnitsInRect2 = function(minx, miny, maxx, maxy, filter)
    if type(minx) ~= 'number' then return in_rect(minx, miny) end
    local r = common.Rect(minx, miny, maxx, maxy)
    local l = in_rect(r, filter)
    common.RemoveRect(r)
    return l
  end
  W.GroupEnumUnitsInRange = in_range
  W.EnumUnitsInSector = function(x, y, r, facing, angle, filter)
    local half = (tonumber(angle) or 360.0) / 2.0
    return in_range(x, y, r, function(u)
      local a = math.deg(math.atan(common.GetUnitY(u) - y, common.GetUnitX(u) - x))
      local d = ((a - (tonumber(facing) or 0.0)) + 180.0) % 360.0 - 180.0
      if math.abs(d) > half then return false end
      if filter then return filter(u) end
    end)
  end
  W.GetUnitXY = function(u) return common.GetUnitX(u), common.GetUnitY(u) end
  W.GetUnitZ = function(u) return common.BlzGetUnitZ and common.BlzGetUnitZ(u) or 0.0 end
  W.GetUnitXYZ = function(u) return common.GetUnitX(u), common.GetUnitY(u), (common.BlzGetUnitZ and common.BlzGetUnitZ(u) or 0.0) end
  W.GetEffectXY = function(e) return common.BlzGetLocalSpecialEffectX(e), common.BlzGetLocalSpecialEffectY(e) end
  W.GetEffectZ = function(e) return common.BlzGetLocalSpecialEffectZ(e) end
  W.GetEffectXYZ = function(e) return common.BlzGetLocalSpecialEffectX(e), common.BlzGetLocalSpecialEffectY(e), common.BlzGetLocalSpecialEffectZ(e) end


  W.GetWindowSize = function() return { width = common.BlzGetLocalClientWidth(), height = common.BlzGetLocalClientHeight() } end
  W.GetClientSize = W.GetWindowSize
  W.GetMouseXYRelative = function()
    local w, h = common.BlzGetLocalClientWidth(), common.BlzGetLocalClientHeight()
    return { x = (w or 0) / 2, y = (h or 0) / 2 }
  end
  W.GetMouseXY = W.GetMouseXYRelative



  local pi = math.pi
  local function bounce_out(t)
    if t < 1 / 2.75 then return 7.5625 * t * t
    elseif t < 2 / 2.75 then t = t - 1.5 / 2.75 return 7.5625 * t * t + 0.75
    elseif t < 2.5 / 2.75 then t = t - 2.25 / 2.75 return 7.5625 * t * t + 0.9375 end
    t = t - 2.625 / 2.75
    return 7.5625 * t * t + 0.984375
  end
  local function inout(fin, t) if t < 0.5 then return fin(t * 2) / 2 end return 1 - fin((1 - t) * 2) / 2 end
  local function out(fin, t) return 1 - fin(1 - t) end
  local IN = {
    [1] = function(t) return 1 - math.cos(t * pi / 2) end,
    [4] = function(t) return t * t end,
    [7] = function(t) return t * t * t end,
    [10] = function(t) return t ^ 4 end,
    [13] = function(t) return t ^ 5 end,
    [16] = function(t) return t == 0 and 0 or 2 ^ (10 * (t - 1)) - 0.001 end,
    [19] = function(t) return 1 - math.sqrt(math.max(0, 1 - t * t)) end,
    [22] = function(t, p) local per = (p and p ~= 0) and p or 0.3 if t == 0 or t == 1 then return t end
      t = t - 1 return -(2 ^ (10 * t)) * math.sin((t - per / 4) * pi * 2 / per) end,
    [25] = function(t) local s = 1.70158 return t * t * ((s + 1) * t - s) end,
    [28] = function(t) return 1 - bounce_out(1 - t) end,
  }
  W.tweenTo = function(t, kind, param)
    t = tonumber(t) or 0
    if t <= 0 then return 0 end
    if t >= 1 then return 1 end
    kind = math.tointeger(tonumber(kind) or 0) or 0
    if kind <= 0 or kind > 30 then return t end
    local base = kind - (kind - 1) % 3
    local fin = IN[base]
    if not fin then return t end
    local f = function(x) return fin(x, param) end
    local mode = (kind - 1) % 3
    if mode == 0 then return f(t) elseif mode == 1 then return out(f, t) end
    return inout(f, t)
  end



  W.RegisterMouseEventByCode = function(btn, status, fn)
    if fn ~= nil then
      local k = tostring(btn) .. ':' .. tostring(status)
      local l = MOUSE_CB[k]
      if l == nil then l = {} MOUSE_CB[k] = l end
      l[#l + 1] = fn
    end
    return call('DzTriggerRegisterMouseEventByCode', nil, btn, status, false, fn)
  end
  W.GetTriggerKey = function() return FRAME_API.XMGetTriggerKey() end
  W.RegisterKeyEventByCode = function(key, status, fn) return call('DzTriggerRegisterKeyEventByCode', nil, key, status, false, fn) end
  W.RegisterMouseMoveEventByCode = function(fn) return call('DzTriggerRegisterMouseMoveEventByCode', nil, false, fn) end
  W.RegisterWindowResizeEventByCode = function(fn) return call('DzTriggerRegisterWindowResizeEventByCode', nil, false, fn) end
  W.GetUnitAbilitys = function() return {} end
  W.GetWidgetAnimateDatas = function() return {} end
  W.EnumEffectInRects = function() return {} end
  W.EnumEffectInRanges = function() return {} end
  W.EnumDoodadInRects = function() return {} end
  W.EnumDoodadInRanges = function() return {} end

  W.FramePoints = { LEFT_TOP = 0, TOP = 1, RIGHT_TOP = 2, LEFT = 3, CENTER = 4, RIGHT = 5, LEFT_BOTTOM = 6, BOTTOM = 7,
    RIGHT_BOTTOM = 8 }
  return setmetatable(base, { __index = function(_, k)
    local w = W[k]
    if w ~= nil then return w end
    if type(k) == 'string' and k:sub(1, 5) == 'Frame' then
      local x = FRAME_API['XM' .. k]
      if x ~= nil then return x end
    end

    if type(k) == 'string' and __xm_nat then
      local n = __xm_nat['XM' .. k] or __xm_nat[k]
      if type(n) == 'function' then return n end
    end
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

  local bc = rawget(_G, '__bc_note')
  if bc then bc('lua ' .. tostring(name)) end
  flush_adds()
  local f = _G[name]
  local a, n = pending, pending_n
  pending, pending_n = {}, 0
  results, results_n, results_at = {}, 0, 1
  if type(f) ~= 'function' then return nil end
  local old_a, old_n = args, args_n
  args, args_n = a, n

  local ok, r = xpcall(f, function(e) return debug and debug.traceback and debug.traceback(tostring(e), 2) or e end,
    unpack_(a, 1, n))
  args, args_n = old_a, old_n
  if not ok then error(r, 0) end
  if results_n == 0 and r ~= nil then results, results_n, results_at = { r }, 1, 1 end
  flush_adds()


  local tr = rawget(_G, 'XM_TRACE')
  if type(tr) == 'table' and tr[name] and not (tr.__zero and results[1] ~= 0 and results[1] ~= nil) then
    tr[name] = (tr[name] == true and 0 or tr[name]) + 1
    if tr[name] <= (tr.__limit or 12) then
      local o = {}
      for i = 1, n do o[#o + 1] = tostring(a[i]) end
      local q = {}
      for i = 1, results_n do q[#q + 1] = tostring(results[i]) end
      XM_TRACE_OUT = XM_TRACE_OUT or {}
      XM_TRACE_OUT[#XM_TRACE_OUT + 1] = name .. '(' .. table.concat(o, ', ') .. ') -> ' .. table.concat(q, ', ')
    end
  end
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
  [0] = function(a, b) return a == b end, [1] = function(a, b) return a < b end, [2] = function(a, b) return a <= b end,
  [3] = function(a, b) return a > b end, [4] = function(a, b) return a >= b end,
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

  XMTimerStartNew = function(t, d, f) common.TimerStart(t, d, false, f) end,
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


__xm_ctx = { common = common, japi = japi, FRAMES = FRAMES, of = of, call = call, FRAME_API = FRAME_API, LISTS = LISTS,
  new_big = new_big, big = big, BIG = BIG, BIG_OP = BIG_OP, BIG_CMP = BIG_CMP, enum_group = enum_group, game_time = game_time, run = run, push = push,
  take = take, jass_code = jass_code }
local NAT = __xm_nat or {}
local no_body = {}
for _, name in ipairs(XM_NATIVES) do
  local kind = name:match('^XMLuaReturn_(.+)$')
  local f = DIRECT[name]
  if f == nil then f = NAT[name] end
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
  if f then jass_code[name] = f else no_body[#no_body + 1] = name end
end
__xm_no_body = no_body
require 'jass.runtime'.handle_level = 2
return true
