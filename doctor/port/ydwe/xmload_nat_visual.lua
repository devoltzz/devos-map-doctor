




do
  local N = __xm_nat or {}
  __xm_nat = N
  local V = N.__vis or {}
  N.__vis = V
  local function C() return __xm_ctx end
  local function cm() return __xm_ctx.common end
  local function live(h) return h ~= nil and h ~= 0 end
  local function pc(f, ...) if type(f) ~= 'function' then return nil end local ok, r = pcall(f, ...) if ok then return r end return nil end
  local function int(v)
    v = tonumber(v) or 0
    if v ~= v then return 0 end
    return math.tointeger(math.floor(v)) or 0
  end
  local function clamp255(v) v = int(v) if v < 0 then return 0 end if v > 255 then return 255 end return v end

  local function kind(h)
    if not live(h) then return nil end
    local u = h
    if type(h) == 'number' and type(__i2hf) == 'function' then u = __i2hf(h) end
    if u == nil then return nil end
    local k = tostring(u):match('^(%a+):')
    if k == 'unit' or k == 'item' or k == 'effect' or k == 'destructable' then return k end
    local c = cm()
    if (pc(c.GetUnitTypeId, h) or 0) ~= 0 then return 'unit' end
    if (pc(c.GetItemTypeId, h) or 0) ~= 0 then return 'item' end
    return 'effect'
  end
  V.kind, V.live, V.pc, V.int = kind, live, pc, int

  V.W = V.W or {}
  local W = V.W
  local function st(h)
    local s = W[h]
    if s == nil then s = { a = 255, r = 255, g = 255, b = 255, scale = 1.0, speed = 1.0, anim = '', index = 0 } W[h] = s end
    return s
  end
  V.st = st


  V.ALIAS = V.ALIAS or {}
  local ALIAS = V.ALIAS
  local function targets(h)
    local a = ALIAS[h]
    if a ~= nil then return h, a end
    return h
  end
  V.targets = targets
  N.__effect_of = function(h) return ALIAS[h] or h end

  local function each(h, f) local a, b = targets(h) f(a) if b ~= nil then f(b) end end
  V.each = each

  local function apply_color(h, s)
    local c, k = cm(), kind(h)
    if k == 'effect' then
      each(h, function(e) pc(c.BlzSetSpecialEffectColor, e, s.r, s.g, s.b) pc(c.BlzSetSpecialEffectAlpha, e, s.hidden and 0 or s.a) end)
    elseif k == 'unit' then
      pc(c.SetUnitVertexColor, h, s.r, s.g, s.b, s.a)
    elseif k == 'item' then
      pc(c.BlzSetItemIntegerField, h, c.ITEM_IF_TINTING_COLOR_RED, s.r)
      pc(c.BlzSetItemIntegerField, h, c.ITEM_IF_TINTING_COLOR_GREEN, s.g)
      pc(c.BlzSetItemIntegerField, h, c.ITEM_IF_TINTING_COLOR_BLUE, s.b)
      pc(c.BlzSetItemIntegerField, h, c.ITEM_IF_TINTING_COLOR_ALPHA, s.a)
    end
  end
  V.apply_color = apply_color


  N.XMSetWidgetAlpha = function(h, a)
    if not live(h) then return end
    local s = st(h)
    s.a = clamp255(a)
    local c, k = cm(), kind(h)
    if k == 'effect' then
      if not s.hidden then each(h, function(e) pc(c.BlzSetSpecialEffectAlpha, e, s.a) end) end
    else
      apply_color(h, s)
    end
  end
  N.XMGetWidgetAlpha = function(h) if not live(h) then return 0 end return int(st(h).a) end


  N.XMSetWidgetVertexColor = function(h, r, g, b, a)
    if not live(h) then return end
    local s = st(h)
    s.r, s.g, s.b, s.a = clamp255(r), clamp255(g), clamp255(b), clamp255(a)
    apply_color(h, s)
  end
  N.XMGetWidgetVertexColor = function(h)
    if not live(h) then return 0 end
    local s = st(h)
    local v = ((s.a & 255) << 24) | ((s.r & 255) << 16) | ((s.g & 255) << 8) | (s.b & 255)
    if v >= 0x80000000 then v = v - 0x100000000 end
    return math.tointeger(v) or 0
  end

  N.XMSetWidgetModelScale = function(h, scale)
    if not live(h) then return end
    scale = (tonumber(scale) or 1.0) + 0.0
    local s = st(h)
    s.scale = scale
    local c, k = cm(), kind(h)
    if k == 'effect' then
      if not s.hidden then each(h, function(e) pc(c.BlzSetSpecialEffectScale, e, scale) end) end
    elseif k == 'unit' then
      pc(c.SetUnitScale, h, scale, scale, scale)
    elseif k == 'item' then
      pc(c.BlzSetItemRealField, h, c.ITEM_RF_SCALING_VALUE, scale)
    end
  end

  N.XMSetPariticleSize = function(h, size) if live(h) then st(h).particle = (tonumber(size) or 1.0) + 0.0 end end


  N.XMWidgetSetTargetable = function(h, b) if live(h) then st(h).targetable = b and true or false end end


  N.XMSetWidgetTexture = function(h, src, dest)
    if not live(h) then return end
    local s = st(h)
    s.tex = s.tex or {}
    s.tex[tostring(src or '')] = dest
  end
  N.XMSetWidgetTextureById = function(h, path, id)
    if not live(h) then return end
    local s = st(h)
    s.texid = s.texid or {}
    s.texid[int(id)] = path
  end


  N.XMGetWidgetPreselectUI = function(h) return 0 end
  N.XMSetWidgetPreselectUIVisible = function(h, b) if live(h) then st(h).preselect = b and true or false end end
  N.XMGetWidgetPreselectUIVisible = function(h)
    if not live(h) then return false end
    local v = st(h).preselect
    if v == nil then return true end
    return v
  end
end

do
  local N = __xm_nat or {}
  __xm_nat = N
  local V = N.__vis
  local kind, live, pc, int, st, each = V.kind, V.live, V.pc, V.int, V.st, V.each
  local function cm() return __xm_ctx.common end
  local function now() local c = __xm_ctx return c.game_time and c.game_time() or 0.0 end


  local ANIM = { stand = 'ANIM_TYPE_STAND', birth = 'ANIM_TYPE_BIRTH', death = 'ANIM_TYPE_DEATH', decay = 'ANIM_TYPE_DECAY',
    dissipate = 'ANIM_TYPE_DISSIPATE', walk = 'ANIM_TYPE_WALK', attack = 'ANIM_TYPE_ATTACK', morph = 'ANIM_TYPE_MORPH',
    sleep = 'ANIM_TYPE_SLEEP', spell = 'ANIM_TYPE_SPELL', portrait = 'ANIM_TYPE_PORTRAIT' }
  local SUB = {}
  for w in ('alternate_ex berserk chainlightning channel complete critical defend drain eattree entangle fast fifth fill fire ' ..
      'first five flail flesh four fourth gold hit large left light looping lumber medium moderate off one puke ready right ' ..
      'rooted second severe slam small spiked spin swim talk third three throw turn two upgrade victory work wounded'):gmatch('%S+') do
    SUB[w] = 'SUBANIM_TYPE_' .. w:upper()
  end
  SUB.alternate = 'SUBANIM_TYPE_ALTERNATE_EX'
  local function play_effect(e, name)
    local c = cm()
    local main, subs = nil, {}
    for w in tostring(name or ''):lower():gmatch('%a+') do
      if main == nil and ANIM[w] then main = ANIM[w]
      elseif SUB[w] then subs[#subs + 1] = SUB[w] end
    end
    pc(c.BlzSpecialEffectClearSubAnimations, e)
    for _, s in ipairs(subs) do local v = c[s] if v ~= nil then pc(c.BlzSpecialEffectAddSubAnimation, e, v) end end
    local a = c[main or 'ANIM_TYPE_STAND']
    if a ~= nil then pc(c.BlzPlaySpecialEffect, e, a) end
  end

  N.XMSetWidgetAnimate = function(h, name)
    if not live(h) then return end
    local s = st(h)
    s.anim, s.index, s.t0 = tostring(name or ''), -1, now()
    local k = kind(h)
    if k == 'unit' then pc(cm().SetUnitAnimation, h, s.anim)
    elseif k == 'effect' then each(h, function(e) play_effect(e, s.anim) end) end
  end

  N.XMSetWidgetAnimateByIndex = function(h, index, autocast)
    if not live(h) then return end
    local s = st(h)
    s.index, s.anim, s.t0 = int(index), '', now()
    if kind(h) == 'unit' then pc(cm().SetUnitAnimationByIndex, h, s.index) end
  end
  N.XMGetWidgetAnimate = function(h) if not live(h) then return '' end return st(h).anim or '' end
  N.XMGetWidgetAnimateIndex = function(h) if not live(h) then return 0 end return int(st(h).index) end


  N.XMGetWidgetAnimateId = function(h, name)
    if not live(h) then return -1 end
    local s = st(h)
    if s.anim ~= '' and tostring(name or ''):lower() == s.anim:lower() then return int(s.index) end
    return -1
  end
  N.XMGetWidgetAnimateTime = function(h, name) return 1.0 end
  N.XMGetWidgetAnimateProgress = function(h)
    if not live(h) then return 0.0 end
    local s = st(h)
    if s.t0 == nil then return 0.0 end
    local p = (now() - s.t0) * (s.speed or 1.0)
    return (p - math.floor(p)) + 0.0
  end
  N.XMGetWidgetAnimateSpeed = function(h) if not live(h) then return 0.0 end return (st(h).speed or 1.0) + 0.0 end


  N.XMSetWidgetAnimnameStartCallback = function(h, f) if live(h) then st(h).on_start = f end end
  N.XMSetWidgetAnimnameEndCallback = function(h, f) if live(h) then st(h).on_end = f end end



  N.XMGetWidgetModelHeight = function(h)
    if not live(h) then return 0.0 end
    local c, k = cm(), kind(h)
    if k == 'unit' then
      local id = pc(c.GetUnitTypeId, h) or 0
      local z = 0.0
      if type(XMGetObjectPropertyReal) == 'function' then z = tonumber(pc(XMGetObjectPropertyReal, 2, id, 'impactZ')) or 0.0 end
      if z <= 0 then z = 60.0 end
      local sc = tonumber(pc(c.BlzGetUnitRealField, h, c.UNIT_RF_SCALING_VALUE)) or 1.0
      return z * 2.0 * sc + 0.0
    elseif k == 'effect' then
      local sc = tonumber(pc(c.BlzGetSpecialEffectScale, (V.targets(h)))) or (st(h).scale or 1.0)
      return 100.0 * sc + 0.0
    end
    return 0.0
  end

  N.XMGetWidgetModelPos = function(h, loc)
    local c = cm()
    if live(loc) then pc(c.MoveLocation, loc, 0.0, 0.0) end
    if not live(h) then return 0.0 end
    local k = kind(h)
    local x, y, z = 0.0, 0.0, 0.0
    if k == 'effect' then
      local e = (V.targets(h))
      x = tonumber(pc(c.BlzGetLocalSpecialEffectX, e)) or 0.0
      y = tonumber(pc(c.BlzGetLocalSpecialEffectY, e)) or 0.0
      z = tonumber(pc(c.BlzGetLocalSpecialEffectZ, e)) or 0.0
    elseif k == 'unit' then
      x, y = tonumber(pc(c.GetUnitX, h)) or 0.0, tonumber(pc(c.GetUnitY, h)) or 0.0
      z = tonumber(pc(c.BlzGetUnitZ, h)) or 0.0
      z = z + (tonumber(pc(c.GetUnitFlyHeight, h)) or 0.0)
    elseif k == 'item' then
      x, y = tonumber(pc(c.GetItemX, h)) or 0.0, tonumber(pc(c.GetItemY, h)) or 0.0
      if live(loc) then pc(c.MoveLocation, loc, x, y) z = tonumber(pc(c.GetLocationZ, loc)) or 0.0 end
    end
    if live(loc) then pc(c.MoveLocation, loc, x, y) end
    return z + 0.0
  end
end

do
  local N = __xm_nat or {}
  __xm_nat = N
  local V = N.__vis
  local kind, live, pc, int, st, each, ALIAS = V.kind, V.live, V.pc, V.int, V.st, V.each, V.ALIAS
  local function cm() return __xm_ctx.common end




  N.XMAddLocalEffect = function(path, x, y) return nil end


  N.XMShowEffect = function(e, b)
    if not live(e) then return end
    local c, s = cm(), st(e)
    if b then
      if not s.hidden then return end
      s.hidden = false
      each(e, function(x) pc(c.BlzSetSpecialEffectAlpha, x, s.a) pc(c.BlzSetSpecialEffectScale, x, s.shown_scale or s.scale or 1.0) end)
    else
      if not s.hidden then s.shown_scale = tonumber(pc(c.BlzGetSpecialEffectScale, e)) or s.scale or 1.0 end
      s.hidden = true
      each(e, function(x) pc(c.BlzSetSpecialEffectAlpha, x, 0) pc(c.BlzSetSpecialEffectScale, x, 0.0) end)
    end
  end

  N.XMEffectSetConstrainRender = function(e, b) if live(e) then st(e).constrain = b and true or false end end


  N.XMBindEffect = function(e, point, e1)
    if not live(e) or not live(e1) then return end
    local c = cm()
    local src = N.__effect_of(e)
    local x = tonumber(pc(c.BlzGetLocalSpecialEffectX, src)) or 0.0
    local y = tonumber(pc(c.BlzGetLocalSpecialEffectY, src)) or 0.0
    local z = tonumber(pc(c.BlzGetLocalSpecialEffectZ, src)) or 0.0
    each(e1, function(x1) pc(c.BlzSetSpecialEffectPosition, x1, x, y, z) end)
    st(e1).bound = { to = e, point = tostring(point or '') }
  end

  N.XMSetEffectMatOrient = function(e, x, y, z)
    if not live(e) then return end
    x, y, z = tonumber(x) or 0.0, tonumber(y) or 0.0, tonumber(z) or 0.0
    if x == 0 and y == 0 and z == 0 then return end
    local yaw = math.atan(y, x)
    local pitch = -math.atan(z, math.sqrt(x * x + y * y))
    local c = cm()
    each(e, function(t) pc(c.BlzSetSpecialEffectOrientation, t, yaw, pitch, 0.0) end)
  end





  do
    local base = rawget(_G, 'DestroyEffect')
    if type(base) == 'function' and not V.destroy_wrapped then
      V.destroy_wrapped = true
      _G.DestroyEffect = function(e, ...)
        if e ~= nil then
          local gid = (type(__rawnat) == 'table' and __rawnat.GetHandleId) or GetHandleId
          local id = type(e) == 'number' and e or (gid and gid(e)) or 0
          if id ~= 0 then
            V.W[id] = nil
            local a = ALIAS[id]
            if a ~= nil then ALIAS[id] = nil V.W[a] = nil if __xm_ctx then pc(__xm_ctx.common.DestroyEffect, a) end end
          end
        end
        return base(e, ...)
      end
    end
  end
  N.XMSetEffectModelEx = function(e, path, attach, bone, nine, color)
    if not live(e) then return end
    path = tostring(path or '')
    local c, s = cm(), st(e)
    s.model = path
    local old = ALIAS[e]
    if old ~= nil then ALIAS[e] = nil V.W[old] = nil pc(c.DestroyEffect, old) end
    if path == '' then return end
    local x = tonumber(pc(c.BlzGetLocalSpecialEffectX, e)) or 0.0
    local y = tonumber(pc(c.BlzGetLocalSpecialEffectY, e)) or 0.0
    local z = tonumber(pc(c.BlzGetLocalSpecialEffectZ, e)) or 0.0
    local n = pc(c.AddSpecialEffect, path, x, y)
    if not live(n) then return end
    ALIAS[e] = n
    pc(c.BlzSetSpecialEffectZ, n, z)
    pc(c.BlzSetSpecialEffectScale, n, tonumber(pc(c.BlzGetSpecialEffectScale, e)) or 1.0)
    pc(c.BlzSetSpecialEffectColor, n, s.r, s.g, s.b)
    pc(c.BlzSetSpecialEffectAlpha, n, s.hidden and 0 or s.a)
    if color ~= nil then

      local idx = type(color) == 'number' and int(color) or int(pc(c.GetHandleId, color))
      local p = (idx >= 0 and idx < 28) and pc(c.Player, idx) or nil
      if live(p) then pc(c.BlzSetSpecialEffectColorByPlayer, n, p) end
    end
    if s.hidden then pc(c.BlzSetSpecialEffectScale, n, 0.0) end
  end


  N.XMGetCommandButton = function(x, y)
    x, y = int(x), int(y)
    if x < 0 or x > 3 or y < 0 or y > 2 then return 0 end
    local f = __xm_ctx.call('DzFrameGetCommandBarButton', y, x)
    return int(f)
  end


  N.XMGetCommandButtonType = function(x, y)
    x, y = int(x), int(y)
    if x < 0 or x > 3 or y < 0 or y > 2 then return -1 end
    return 0
  end

  N.XMGetCommandButtonId = function(x, y) return 0 end


  N.XMGetCommandButtonImage = function(f) return 0 end
  N.XMGetCommandButtonImageDisable = function(f) return 0 end
  N.XMGetCommandButtonString = function(f, i) return '' end


  N.XMTextGetStyle = function(f) if not live(f) then return 0 end return int(__xm_ctx.of(f).text_style) end
  N.XMTextSetStyle = function(f, v) if live(f) then __xm_ctx.of(f).text_style = int(v) end end


  N.SaveXMGroupHandle = function(t, p, k, v) cm().SaveInteger(t, p, k, int(v)) return true end
  N.LoadXMGroupHandle = function(t, p, k) return int(cm().LoadInteger(t, p, k)) end

  N.XMRemoveGroupList = function(l)
    if not live(l) then return end
    local c = __xm_ctx
    if c.LISTS then c.LISTS[l] = nil end
    if type(N.__group_lists) == 'table' then N.__group_lists[l] = nil end
  end
end

do
  local N = __xm_nat or {}
  __xm_nat = N
  local V = N.__vis
  local live, pc, int = V.live, V.pc, V.int
  local function cm() return __xm_ctx.common end
  local function now() local c = __xm_ctx return c.game_time and c.game_time() or 0.0 end



  local seed = 0x2545F491
  local function lrand()
    seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
    return seed / 0x80000000
  end
  N.XMRandomReal = function(lo, hi)
    lo, hi = (tonumber(lo) or 0.0) + 0.0, (tonumber(hi) or 0.0) + 0.0
    return lo + (hi - lo) * lrand()
  end


  local function sync_rand(a, b)
    a, b = (tonumber(a) or 0.0) + 0.0, (tonumber(b) or 0.0) + 0.0
    if b < a then a, b = b, a end
    return cm().GetRandomReal(a, b) + 0.0
  end
  N.XMAroundRandom = function(x, y, z, rmin, rmax, amin, amax, hmin, hmax, loc)
    local r, a, hz = sync_rand(rmin, rmax), math.rad(sync_rand(amin, amax)), sync_rand(hmin, hmax)
    local px, py = x + r * math.cos(a), y + r * math.sin(a)
    if live(loc) then cm().MoveLocation(loc, px, py) end
    return z + hz + 0.0
  end
  N.XMSphereRandom = function(x, y, z, rmin, rmax, axmin, axmax, aymin, aymax, loc)
    local r, ax, ay = sync_rand(rmin, rmax), math.rad(sync_rand(axmin, axmax)), math.rad(sync_rand(aymin, aymax))
    local px = x + r * math.cos(ay) * math.cos(ax)
    local py = y + r * math.cos(ay) * math.sin(ax)
    if live(loc) then cm().MoveLocation(loc, px, py) end
    return z + r * math.sin(ay) + 0.0
  end


  N.XMWorldToScreen = function(loc, x, y, z)
    local c = cm()
    local ex, ey, ez = c.GetCameraEyePositionX(), c.GetCameraEyePositionY(), c.GetCameraEyePositionZ()
    local tx, ty, tz = c.GetCameraTargetPositionX(), c.GetCameraTargetPositionY(), c.GetCameraTargetPositionZ()
    local fx, fy, fz = tx - ex, ty - ey, tz - ez
    local fl = math.sqrt(fx * fx + fy * fy + fz * fz)
    if fl == 0 then return 0.0 end
    fx, fy, fz = fx / fl, fy / fl, fz / fl
    local rx, ry = fy, -fx
    local rl = math.sqrt(rx * rx + ry * ry)
    if rl == 0 then return 0.0 end
    rx, ry = rx / rl, ry / rl
    local ux, uy, uz = ry * fz, -rx * fz, rx * fy - ry * fx
    local vx, vy, vz = x - ex, y - ey, z - ez
    local d = vx * fx + vy * fy + vz * fz
    if d <= 0.01 then return 0.0 end
    local fov = tonumber(c.GetCameraField(c.CAMERA_FIELD_FIELD_OF_VIEW)) or math.rad(70.0)
    if fov > 3.2 then fov = math.rad(fov) end
    if fov <= 0.01 then fov = math.rad(70.0) end
    local k = 0.4 / math.tan(fov / 2.0)
    local sx = 0.4 + (vx * rx + vy * ry) / d * k
    local sy = 0.3 + (vx * ux + vy * uy + vz * uz) / d * k
    if live(loc) then c.MoveLocation(loc, sx, sy) end
    return d + 0.0
  end


  N.XMWorldToMinimap = function(x, y, loc)
    if not live(loc) then return end
    local c = cm()
    local x0, y0 = c.GetCameraBoundMinX(), c.GetCameraBoundMinY()
    local x1, y1 = c.GetCameraBoundMaxX(), c.GetCameraBoundMaxY()
    local w, h = x1 - x0, y1 - y0
    if w <= 0 or h <= 0 then return end
    c.MoveLocation(loc, 0.004 + (x - x0) / w * 0.142, 0.004 + (y - y0) / h * 0.142)
  end


  V.CFG = V.CFG or {}
  local CFG = V.CFG
  local function keep(name) return function(...) CFG[name] = { ... } end end
  N.XMUnlockBlpSize = keep('UnlockBlpSize')
  N.XMUnlockFontSize = keep('UnlockFontSize')
  N.XMUnlockFps = keep('UnlockFps')
  N.XMUnlockJassLimit = keep('UnlockJassLimit')
  N.XMGetBorderUnlock = keep('BorderUnlock')
  N.XMEnableMoveSpeedAcc = keep('MoveSpeedAcc')
  N.XMRenderMeshLimit = keep('RenderMeshLimit')
  N.XMSetUIClearDepth = keep('UIClearDepth')
  N.XMRealShadowAlpha = keep('RealShadowAlpha')
  N.XMRealShadowEnable = keep('RealShadowEnable')
  N.XMRealShadowFilter = keep('RealShadowFilter')
  N.XMRealShadowSetDir = keep('RealShadowSetDir')
  N.XMRealShadowSkipFrame = keep('RealShadowSkipFrame')
  N.XMRealShadowZOffset = keep('RealShadowZOffset')
  N.XMSetAIQueueNumber = keep('AIQueueNumber')
  N.XMShowHPInterface = keep('ShowHPInterface')
  N.XMAdjustPreselectUILevel = keep('AdjustPreselectUILevel')
  N.XMSetTexttagFontEx = keep('TexttagFont')
  N.XMSetTexttagVAlign = keep('TexttagVAlign')
  N.XMSetTexttagMaxCount = function(n) CFG.TexttagMaxCount = { n } if V.driver then V.driver() end end

  N.XMOpenUrl = function(s) end
  N.XMPostWindowMessage = function(m, w, l) end
end

do
  local N = __xm_nat or {}
  __xm_nat = N
  local V = N.__vis
  local live, pc, int = V.live, V.pc, V.int
  local function now() local c = __xm_ctx return c and c.game_time and c.game_time() or 0.0 end





  local TT = {}
  V.TT = TT
  local raw = {}
  local gid = function(h)
    if h == nil then return 0 end
    if type(h) == 'number' then return h end
    local f = (type(__rawnat) == 'table' and __rawnat.GetHandleId) or GetHandleId
    return f and f(h) or 0
  end

  local function wrap(name, mk)
    local base = rawget(_G, name)
    if type(base) ~= 'function' then return end
    raw[name] = base
    _G[name] = mk(base)
  end
  wrap('SetTextTagText', function(base) return function(t, s, h, ...)
    if t ~= nil then
      local id = gid(t)
      if id ~= 0 then
        local r = TT[id]
        if r == nil then r = { scale = 1.0, anims = {} } TT[id] = r end
        if not r.busy then r.text, r.height, r.ud = s, h, t end
      end
    end
    return base(t, s, h, ...)
  end end)
  wrap('DestroyTextTag', function(base) return function(t, ...)
    if t ~= nil then TT[gid(t)] = nil end
    return base(t, ...)
  end end)
  wrap('CreateTextTag', function(base) return function(...)
    local t = base(...)
    if t ~= nil then TT[gid(t)] = nil end
    return t
  end end)
  local function set_text(r, scale)
    local f = raw.SetTextTagText
    if f == nil or r.ud == nil or r.text == nil or r.height == nil then return end
    r.busy = true
    pcall(f, r.ud, r.text, r.height * scale)
    r.busy = false
  end
  local function set_vel(r, vx, vy)
    local f = rawget(_G, 'SetTextTagVelocity')
    if f ~= nil and r.ud ~= nil then pcall(f, r.ud, vx, vy) end
  end
  local function ease(kind, p)
    if p <= 0 then return 0.0 end
    if p >= 1 then return 1.0 end
    if kind == 1 then return p * p end
    if kind == 2 then return 1.0 - (1.0 - p) * (1.0 - p) end
    return p
  end
  local function step()
    local t = now()
    for id, r in pairs(TT) do
      local a = r.anims
      if a and #a > 0 then
        local vx, vy, keep, moves = 0.0, 0.0, {}, false
        for _, m in ipairs(a) do
          local t0, t1 = m.t0 + m.s, m.t0 + m.e
          if t >= t0 then
            if m.kind == 'scale' then
              if m.from == nil then m.from = r.scale end
              local p = (m.e > m.s) and ease(m.tween, (t - t0) / (m.e - m.s)) or 1.0
              r.scale = m.from + (m.to - m.from) * p
              set_text(r, r.scale)
            elseif t < t1 then
              moves = true
              local d = m.e - m.s
              vx, vy = vx + m.x / d, vy + m.y / d
            end
          end
          if t < t1 then keep[#keep + 1] = m end
          if m.kind == 'move' then moves = true end
        end
        if moves then set_vel(r, vx, vy) end
        r.anims = keep
      end
    end
  end
  local timer = nil
  local function driver()
    if timer ~= nil then return end
    local c = __xm_ctx
    if c == nil or c.common == nil or c.common.CreateTimer == nil then return end
    timer = c.common.CreateTimer()
    c.common.TimerStart(timer, 0.03, true, function() local ok, e = pcall(step) if not ok and __logerr then __logerr('xm texttag: ' .. tostring(e)) end end)
  end
  V.driver = driver
  N.__visual_init = driver
  N.XMAdjustTexttagLevel = function() V.CFG.AdjustTexttagLevel = true driver() end
  local function add(t, m)
    local id = gid(t)
    if id == 0 then return end
    local r = TT[id]
    if r == nil then r = { scale = 1.0, anims = {} } TT[id] = r end
    m.t0 = now()
    if timer == nil then

      if m.kind == 'scale' then r.scale = m.to set_text(r, r.scale) end
      return
    end
    r.anims[#r.anims + 1] = m
  end
  N.XMTexttagScaleAniname = function(t, s, e, scale, tween)
    if not live(t) then return end
    s, e = (tonumber(s) or 0.0) + 0.0, (tonumber(e) or 0.0) + 0.0
    if s > e then return end
    add(t, { kind = 'scale', s = s, e = e, to = (tonumber(scale) or 1.0) + 0.0, tween = int(tween) })
  end
  N.XMTexttagMoveAniname = function(t, s, e, x, y, tween)
    if not live(t) then return end
    s, e = (tonumber(s) or 0.0) + 0.0, (tonumber(e) or 0.0) + 0.0
    if s > e or e - s <= 0 then return end
    add(t, { kind = 'move', s = s, e = e, x = (tonumber(x) or 0.0) + 0.0, y = (tonumber(y) or 0.0) + 0.0, tween = int(tween) })
  end
end
