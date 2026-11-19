






do
  local N = __xm_nat or {}
  __xm_nat = N
  local H = N.__unidade or {}
  N.__unidade = H

  local function C() return __xm_ctx end

  local function F(name)
    local c = C()
    if c == nil then return nil end
    local ok, f = pcall(function() return c.common[name] end)
    if ok and type(f) == 'function' then return f end
    return nil
  end
  local function nat(name, ...)
    local f = F(name)
    if f == nil then return nil end
    local ok, a, b = pcall(f, ...)
    if ok then return a, b end
    return nil
  end

  local function layer(name, ...)
    local c = C()
    if c == nil or c.call == nil then return nil end
    return c.call(name, ...)
  end
  local function cc(s) return (string.unpack('>I4', s)) end
  local FIELDS = {}
  local function field(conv, code)
    local k = conv .. code
    local f = FIELDS[k]
    if f == nil then
      f = nat(conv, cc(code)) or false
      FIELDS[k] = f
    end
    return f or nil
  end


  local function hid(h)
    if h == nil or h == 0 or h == false then return nil end
    if math.type(h) == 'integer' then return h end
    local v = nat('GetHandleId', h)
    if v == nil or v == 0 then return nil end
    return v
  end
  local function no(h) return h == nil or h == 0 or h == false end
  local function int(v)
    v = tonumber(v)
    if v == nil or v ~= v then return 0 end
    local i = math.tointeger(v)
    if i then return i end
    v = v >= 0 and math.floor(v) or math.ceil(v)
    if v > 2147483647 then return 2147483647 end
    if v < -2147483648 then return -2147483648 end
    return math.tointeger(v) or 0
  end
  local function real(v) return (tonumber(v) or 0.0) + 0.0 end
  local function str(v) if v == nil then return '' end return tostring(v) end

  local function S(t, h)
    local k = hid(h)
    if k == nil then return {} end
    local s = t[k]
    if s == nil then s = {} t[k] = s end
    return s
  end
  local function peek(t, h)
    local k = hid(h)
    return k and t[k] or nil
  end

  local function slk(kind, id, key)
    local ok, v = pcall(function()
      local s = require 'jass.slk'
      local row = s[kind][id]
      if row == nil then return nil end
      return row[key]
    end)
    if ok then return v end
    return nil
  end
  local function now()
    local c = C()
    if c and c.game_time then return c.game_time() end
    return 0.0
  end
  local function level(u, aid) return int(nat('GetUnitAbilityLevel', u, aid)) end

  H.no = no
  H.F, H.nat, H.layer, H.cc, H.field, H.hid, H.int, H.real, H.str, H.S, H.peek, H.slk, H.now, H.level =
    F, nat, layer, cc, field, hid, int, real, str, S, peek, slk, now, level



  local ready = false
  H.SEL, H.SPELL_TGT, H.ATK_TGT = {}, {}, {}
  local function ensure()
    if ready then return end
    if F('CreateTrigger') == nil then return end
    ready = true
    local function reg(ev, fn)
      local e = nat('ConvertPlayerUnitEvent', ev)
      local t = nat('CreateTrigger')
      if H.no(t) or e == nil then return end
      for i = 0, 27 do
        local p = nat('Player', i)
        if p then nat('TriggerRegisterPlayerUnitEvent', t, p, e, nil) end
      end
      nat('TriggerAddAction', t, fn)
    end

    reg(25, function()
      local p = nat('GetTriggerPlayer')
      local k = hid(p)
      if k then H.SEL[k] = nat('GetTriggerUnit') end
    end)
    reg(26, function()
      local p = nat('GetTriggerPlayer')
      local k = hid(p)
      if k and H.SEL[k] == nat('GetTriggerUnit') then H.SEL[k] = nil end
    end)

    reg(274, function()
      local u = nat('GetTriggerUnit')
      local t = nat('GetSpellTargetUnit') or nat('GetSpellTargetItem') or nat('GetSpellTargetDestructable')
      S(H.SPELL_TGT, u)[nat('GetSpellAbilityId') or 0] = t or false
    end)

    reg(18, function() S(H.ATK_TGT, nat('GetAttacker')).t = nat('GetTriggerUnit') end)
    reg(39, function()
      local o = nat('GetIssuedOrderId')
      if o == 851983 or o == 851971 then
        S(H.ATK_TGT, nat('GetTriggerUnit')).t = nat('GetOrderTargetUnit') or nat('GetOrderTarget')
      else
        S(H.ATK_TGT, nat('GetTriggerUnit')).t = nil
      end
    end)
    reg(38, function() S(H.ATK_TGT, nat('GetTriggerUnit')).t = nil end)
    reg(40, function() S(H.ATK_TGT, nat('GetTriggerUnit')).t = nil end)

    reg(20, function() if H.clear_buffs then H.clear_buffs(nat('GetTriggerUnit')) end end)
  end
  H.ensure = ensure
end




do
  local N = __xm_nat
  local H = N.__unidade
  local nat, field, S, peek, int, real, str, slk = H.nat, H.field, H.S, H.peek, H.int, H.real, H.str, H.slk
  local ATTR = {}
  H.ATTR = ATTR
  local function urf(code) return field('ConvertUnitRealField', code) end
  local function wrf(code) return field('ConvertUnitWeaponRealField', code) end
  local function wif(code) return field('ConvertUnitWeaponIntegerField', code) end
  local function wsf(code) return field('ConvertUnitWeaponStringField', code) end

  local function unitreal(code)
    return {
      function(u) local f = urf(code) return f and nat('BlzGetUnitRealField', u, f) end,
      function(u, v) local f = urf(code) if f then nat('BlzSetUnitRealField', u, f, v) end end }
  end
  local function weapreal(code, i)
    return {
      function(u) local f = wrf(code) return f and nat('BlzGetUnitWeaponRealField', u, f, i) end,
      function(u, v) local f = wrf(code) if f then nat('BlzSetUnitWeaponRealField', u, f, i, v) end end }
  end
  local REAL = {
    [101] = weapreal('ua1z', 0),
    [107] = weapreal('ua1z', 1),
    [149] = weapreal('uma1', 0),
    [150] = weapreal('uma1', 1),

    [102] = { function(u) return nat('BlzGetUnitCollisionSize', u) end, nil },

    [105] = { nil, function(u, v) if v > 0 then nat('UnitApplyTimedLife', u, H.cc('BTLF'), v) end end },
    [115] = unitreal('usir'),
    [116] = unitreal('ucpt'),
    [117] = unitreal('ucbs'),
    [118] = unitreal('urun'),
    [119] = unitreal('uwal'),
    [129] = unitreal('ussc'),
    [139] = unitreal('umxp'),
    [140] = unitreal('umxr'),
    [143] = unitreal('uhpr'),
    [144] = unitreal('umpr'),

    [151] = { function(u) local f = urf('usca') return f and nat('BlzGetUnitRealField', u, f) end,
      function(u, v) nat('SetUnitScale', u, v, v, v) local f = urf('usca') if f then nat('BlzSetUnitRealField', u, f, v) end end },
  }
  local INTEGER = {

    [157] = { function(u) local f = wif('utc1') return f and nat('BlzGetUnitWeaponIntegerField', u, f, 0) end,
      function(u, v) local f = wif('utc1') if f then nat('BlzSetUnitWeaponIntegerField', u, f, 0, v) end end },
    [158] = { function(u) local f = wif('utc1') return f and nat('BlzGetUnitWeaponIntegerField', u, f, 1) end,
      function(u, v) local f = wif('utc1') if f then nat('BlzSetUnitWeaponIntegerField', u, f, 1, v) end end },
    [153] = { function(u) local f = wif('ucs1') return f and nat('BlzGetUnitWeaponIntegerField', u, f, 0) end,
      function(u, v) local f = wif('ucs1') if f then nat('BlzSetUnitWeaponIntegerField', u, f, 0, v) end end },
    [154] = { function(u) local f = wif('ucs1') return f and nat('BlzGetUnitWeaponIntegerField', u, f, 1) end,
      function(u, v) local f = wif('ucs1') if f then nat('BlzSetUnitWeaponIntegerField', u, f, 1, v) end end },
  }
  local function type_slk(u, key) return slk('unit', nat('GetUnitTypeId', u) or 0, key) end
  local STRING = {
    [1] = { function(u) return type_slk(u, 'art') end, nil },
    [4] = { function(u) return nat('GetUnitName', u) end, function(u, v) nat('BlzSetUnitName', u, v) end },
    [6] = { function(u) return nat('GetHeroProperName', u) end, function(u, v) nat('BlzSetHeroProperName', u, v) end },
    [108] = { function(u) local f = wsf('ua1m') return f and nat('BlzGetUnitWeaponStringField', u, f, 0) end,
      function(u, v) local f = wsf('ua1m') if f then nat('BlzSetUnitWeaponStringField', u, f, 0, v) end end },
    [109] = { function(u) local f = wsf('ua1m') return f and nat('BlzGetUnitWeaponStringField', u, f, 1) end,
      function(u, v) local f = wsf('ua1m') if f then nat('BlzSetUnitWeaponStringField', u, f, 1, v) end end },

    [254] = { function(u) return type_slk(u, 'file') end, function(u, v) H.layer('DzSetUnitModel', u, v) end },
  }
  local function setter(tab, conv)
    return function(u, t, v)
      if H.no(u) then return end
      H.ensure()
      v = conv(v)
      local s = S(ATTR, u)
      s[t] = v
      local e = tab[t]
      if e and e[2] then e[2](u, v) end
    end
  end
  local function getter(tab, conv, empty)
    return function(u, t)
      if H.no(u) then return empty end
      local s = peek(ATTR, u)
      if s and s[t] ~= nil then return conv(s[t]) end
      local e = tab[t]
      if e and e[1] then
        local v = e[1](u)
        if v ~= nil then return conv(v) end
      end
      return empty
    end
  end
  N.XMSetUnitAttrReal = setter(REAL, real)
  N.XMGetUnitAttrReal = getter(REAL, real, 0.0)
  N.XMSetUnitAttrInteger = setter(INTEGER, int)
  N.XMGetUnitAttrInteger = getter(INTEGER, int, 0)
  N.XMSetUnitAttr = setter(STRING, str)
  N.XMGetUnitAttr = getter(STRING, str, '')

  N.XMSetUnitModel = function(u, model)
    if H.no(u) then return end
    S(ATTR, u)[254] = str(model)
    H.layer('DzSetUnitModel', u, str(model))
  end
end


do
  local N = __xm_nat
  local H = N.__unidade
  local nat, field, S, peek, int, real, str, slk, hid, cc = H.nat, H.field, H.S, H.peek, H.int, H.real, H.str, H.slk, H.hid, H.cc
  local FLAGS = {}
  H.FLAGS = FLAGS
  local function is_hero(u) return not H.no(u) and nat('IsHeroUnitId', nat('GetUnitTypeId', u) or 0) == true end


  local GROWTH = { [1] = 'ustp', [2] = 'uinp', [3] = 'uagp' }
  N.XMGetHeroAttributePlus = function(u, t)
    if not is_hero(u) then return 0.0 end
    local code = GROWTH[t]
    if code == nil then return 0.0 end
    local f = field('ConvertUnitRealField', code)
    return real(f and nat('BlzGetUnitRealField', u, f))
  end

  local PRIMARY = { STR = 1, INT = 2, AGI = 3 }
  N.XMGetHeroPrimaryAttribute = function(u)
    if not is_hero(u) then return -1 end
    local f = field('ConvertUnitIntegerField', 'upra')
    local v = int(f and nat('BlzGetUnitIntegerField', u, f))
    if v >= 1 and v <= 3 then return v end
    local s = slk('unit', nat('GetUnitTypeId', u) or 0, 'primary')
    return PRIMARY[str(s):upper()] or 1
  end

  N.XMSetHeroPrimaryAttributeEx = function(u, i, _b)
    if not is_hero(u) then return end
    local f = field('ConvertUnitIntegerField', 'upra')
    if f then nat('BlzSetUnitIntegerField', u, f, i) end
  end


  local function toggle(u, key, aid, off, hide)
    local s = S(FLAGS, u)
    if (s[key] or false) == off then return end
    s[key] = off
    nat('BlzUnitDisableAbility', u, aid, off, hide or false)
  end
  N.XMSetUnitMoveEnable = function(u, b) if u then toggle(u, 'move', cc('Amov'), not b) end end

  N.XMUnitDisableInventory = function(u, b) if u then toggle(u, 'inv', cc('AInv'), b == true) end end

  N.XMUnitDisableAttack = function(u, b)
    if H.no(u) then return end
    local s = S(FLAGS, u)
    b = b == true
    if (s.atk or false) == b then return end
    s.atk = b
    if H.layer('DzUnitDisableAttack', u, b) == nil and H.F('DzUnitDisableAttack') == nil then
      nat('BlzUnitDisableAbility', u, cc('Aatk'), b, false)
    end
  end

  N.XMSetUnitAttackType = function(u, i)
    if H.no(u) then return end
    local f = field('ConvertUnitWeaponBooleanField', 'uaen')
    if f == nil then return end
    nat('BlzSetUnitWeaponBooleanField', u, f, 0, (i & 1) ~= 0)
    nat('BlzSetUnitWeaponBooleanField', u, f, 1, (i & 2) ~= 0)
  end


  local REF_MOVE = { [0] = 0, [1] = 0x2000002, [2] = 0x2000002, [4] = 0x4000004, [8] = 0x40000040, [16] = 0x40000040, [32] = 0x40000040 }
  N.XMSetUnitMoveType = function(u, i)
    if H.no(u) then return end
    S(FLAGS, u).movetype = i
    if i & 4 ~= 0 then
      if nat('UnitAddAbility', u, cc('Amrf')) then nat('UnitRemoveAbility', u, cc('Amrf')) end
      nat('SetUnitPathing', u, false)
    elseif i == 0 then
      nat('SetUnitPathing', u, false)
    else
      nat('SetUnitPathing', u, true)
    end
  end
  N.XMGetUnitMoveType = function(u)
    if H.no(u) then return 0 end
    local s = peek(FLAGS, u)
    if s and s.movetype then return int(s.movetype) end
    local f = field('ConvertUnitIntegerField', 'umvt')
    local v = f and nat('BlzGetUnitIntegerField', u, f)
    if v ~= nil and REF_MOVE[v] then return REF_MOVE[v] end
    if nat('IsUnitType', u, nat('ConvertUnitType', 2)) then return 0x4000004 end
    return 0x2000002
  end


  N.XMUnitSetCanSelect = function(u, b)
    if H.no(u) then return end
    local s = S(FLAGS, u)
    b = b == true
    if (s.nosel or false) == (not b) then return end
    s.nosel = not b
    if not b then
      nat('UnitAddAbility', u, cc('Aloc'))
    else
      nat('UnitRemoveAbility', u, cc('Aloc'))
      nat('ShowUnit', u, false)
      nat('ShowUnit', u, true)
    end
  end

  N.XMSetUnitVisibleAbility = function(u, p, b)
    if H.no(u) or H.no(p) then return end
    S(FLAGS, u)['vis' .. tostring(hid(p))] = b
  end


  N.XMGetPlayerSelectUnit = function(p)
    H.ensure()
    local k = hid(p)
    return k and H.SEL[k] or nil
  end

  N.XMGetPlayerSelectMainUnit = function()
    local u = H.layer('DzGetSelectedLeaderUnit')
    if not H.no(u) and u ~= 0 then return u end
    local k = hid(nat('GetLocalPlayer'))
    return k and H.SEL[k] or nil
  end

  N.XMGetUnitAttackTarget = function(u)
    H.ensure()
    local s = peek(H.ATK_TGT, u)
    return s and s.t or nil
  end



  local ICON = {}
  local function redraw(u)
    local s = S(ICON, u)
    if s.icon then nat('DestroyMinimapIcon', s.icon) s.icon = nil end
    if s.path == nil or s.path == '' then return end
    local path = s.path
    local low = path:lower()
    if not (low:find('%.mdl$') or low:find('%.mdx$')) then path = 'UI\\Minimap\\MiniMap-Hero.mdl' end
    local c = s.c1 or 0xFFFFFFFF
    local fog = nat('ConvertFogState', 2)
    s.icon = nat('CreateMinimapIconOnUnit', u, (c >> 16) & 255, (c >> 8) & 255, c & 255, path, fog)
  end
  N.XMSetUnitMinimapIcon = function(u, path, height)
    if H.no(u) then return end
    local s = S(ICON, u)
    s.path, s.height = str(path), height
    redraw(u)
  end
  N.XMSetUnitMinimapIconColor = function(u, c1, c2)
    if H.no(u) then return end
    local s = S(ICON, u)
    s.c1, s.c2 = c1 & 0xFFFFFFFF, c2 & 0xFFFFFFFF
    if s.path then redraw(u) end
  end
  N.XMSetUnitMinimapIconBlink = function(u, b)
    if H.no(u) then return end
    S(ICON, u).blink = b
  end


  N.XMSubPlayerTechResearched = function(p, tech, lvl)
    if H.no(p) or lvl <= 0 then return false end
    if H.F('BlzDecPlayerTechResearched') then
      nat('BlzDecPlayerTechResearched', p, tech, lvl)
    else
      local cur = int(nat('GetPlayerTechCount', p, tech, true))
      nat('SetPlayerTechResearched', p, tech, math.max(0, cur - lvl))
    end
    return true
  end




  H.ILLUSION = {}
  N.XMCreateIllusion = function(p, u, x, y, dur, attackRate, defenseRate)
    if H.no(p) or H.no(u) then return nil end
    local il = nat('CreateUnit', p, nat('GetUnitTypeId', u), x, y, nat('GetUnitFacing', u) or 0.0)
    if H.no(il) then return nil end
    if is_hero(u) then
      nat('SetHeroLevel', il, nat('GetHeroLevel', u) or 1, false)
      nat('SetHeroStr', il, nat('GetHeroStr', u, false) or 0, true)
      nat('SetHeroAgi', il, nat('GetHeroAgi', u, false) or 0, true)
      nat('SetHeroInt', il, nat('GetHeroInt', u, false) or 0, true)
    end
    local skin = nat('BlzGetUnitSkin', u)
    if skin and skin ~= nat('GetUnitTypeId', u) then nat('BlzSetUnitSkin', il, skin) end
    local mhp = nat('BlzGetUnitMaxHP', u)
    if mhp then nat('BlzSetUnitMaxHP', il, mhp) nat('SetUnitState', il, nat('ConvertUnitState', 0), (nat('GetWidgetLife', u) or mhp) + 0.0) end
    local dmg = nat('BlzGetUnitBaseDamage', u, 0)
    if dmg then nat('BlzSetUnitBaseDamage', il, int(dmg * (attackRate or 1.0)), 0) end
    local arm = nat('BlzGetUnitArmor', u)
    if arm then nat('BlzSetUnitArmor', il, arm) end
    nat('SetUnitVertexColor', il, 150, 150, 255, 200)
    if dur and dur > 0 then nat('UnitApplyTimedLife', il, cc('BTLF'), dur) end
    S(H.ILLUSION, il).atk, S(H.ILLUSION, il).def = real(attackRate), real(defenseRate)
    S(H.ILLUSION, il).of = u
    return il
  end
end


do
  local N = __xm_nat
  local H = N.__unidade
  local nat, int, hid = H.nat, H.int, H.hid
  local function each_in_range(x, y, r, fn)
    local g = nat('CreateGroup')
    if H.no(g) then return end
    nat('GroupEnumUnitsInRange', g, x, y, r, nil)
    local n = int(nat('BlzGroupGetSize', g))
    for i = 0, n - 1 do
      local u = nat('BlzGroupUnitAt', g, i)
      if u then fn(u) end
    end
    nat('DestroyGroup', g)
  end

  N.XMEnumUnitsInRect2 = function(g, x, y, angle, distance, width)
    if H.no(g) then return end
    nat('GroupClear', g)
    local a = math.rad(angle)
    local dx, dy = math.cos(a), math.sin(a)
    local half = width / 2.0
    local cx, cy = x + dx * distance / 2.0, y + dy * distance / 2.0
    local r = math.sqrt((distance / 2.0) ^ 2 + half ^ 2) + 1.0
    each_in_range(cx, cy, r, function(u)
      local px, py = (nat('GetUnitX', u) or 0.0) - x, (nat('GetUnitY', u) or 0.0) - y
      local along, across = px * dx + py * dy, -px * dy + py * dx
      if along >= 0 and along <= distance and math.abs(across) <= half then nat('GroupAddUnit', g, u) end
    end)
  end

  N.XMEnumUnitsInSector = function(g, x, y, radius, angle, width)
    if H.no(g) then return end
    nat('GroupClear', g)
    local half = width / 2.0
    each_in_range(x, y, radius, function(u)
      local px, py = (nat('GetUnitX', u) or 0.0) - x, (nat('GetUnitY', u) or 0.0) - y
      if px == 0 and py == 0 then nat('GroupAddUnit', g, u) return end
      local d = (math.deg(math.atan(py, px)) - angle) % 360.0
      if d > 180.0 then d = 360.0 - d end
      if d <= half then nat('GroupAddUnit', g, u) end
    end)
  end

  N.XMEnumUnitInRect2 = function(r, l)
    local c = __xm_ctx
    if H.no(r) or c == nil then return 0 end
    local g = nat('CreateGroup')
    if H.no(g) then return 0 end
    nat('GroupEnumUnitsInRect', g, r, nil)
    local t = {}
    local n = int(nat('BlzGroupGetSize', g))
    for i = 0, n - 1 do t[i + 1] = nat('BlzGroupUnitAt', g, i) end
    nat('DestroyGroup', g)
    c.LISTS[l] = t
    return n
  end



  local next_gl = 0x30000000
  N.__group_lists = N.__group_lists or {}
  N.XMGetGroupUnitList = function(g)
    local c = __xm_ctx
    if H.no(g) or c == nil then return 0 end
    local t = {}
    local n = int(nat('BlzGroupGetSize', g))
    for i = 0, n - 1 do t[i + 1] = nat('BlzGroupUnitAt', g, i) end
    next_gl = next_gl + 1
    c.LISTS[next_gl] = t
    N.__group_lists[next_gl] = g
    return next_gl
  end
  N.XMGetUnitFromGroupListByIndex = function(id, i)
    local c = __xm_ctx
    local t = c and c.LISTS[id]
    if t == nil or i < 0 then return nil end
    return t[i + 1]
  end
end






do
  local N = __xm_nat
  local H = N.__unidade
  local nat, S, peek, int, real, hid, level = H.nat, H.S, H.peek, H.int, H.real, H.hid, H.level
  local BUFF = {}
  H.BUFF = BUFF
  local function fire(mode, u, bid, caster)
    local f = N._on_buff
    if type(f) == 'function' then pcall(f, mode, u, bid, caster) end
  end
  local function rec(u, bid)
    local s = peek(BUFF, u)
    return s and s[bid] or nil
  end
  H.buff = rec
  local function remove(u, bid, quiet)
    local s = peek(BUFF, u)
    local r = s and s[bid]
    if r == nil then return end
    s[bid] = nil
    if r.timer then nat('PauseTimer', r.timer) nat('DestroyTimer', r.timer) r.timer = nil end
    if r.added then nat('UnitRemoveAbility', u, bid) end
    if not quiet then fire(2, u, bid, r.caster) end
  end
  H.remove_buff = remove
  H.clear_buffs = function(u)
    local s = peek(BUFF, u)
    if s == nil then return end
    local ids = {}
    for bid in pairs(s) do ids[#ids + 1] = bid end
    table.sort(ids)
    for _, bid in ipairs(ids) do remove(u, bid) end
  end
  local function arm(u, bid, r, t)
    if r.timer then nat('PauseTimer', r.timer) end
    if H.no(t) or t <= 0 then return end
    if r.timer == nil then r.timer = nat('CreateTimer') end
    if r.timer == nil then return end
    r.ends = H.now() + t
    nat('TimerStart', r.timer, t, false, function() remove(u, bid) end)
  end
  H.arm_buff = arm
  N.XMSetUnitBuffEx = function(u, t, bid, lvl, dur, _id)
    if H.no(u) or H.no(t) or lvl == nil or lvl <= 0 then return false end
    H.ensure()
    local s = S(BUFF, u)
    local r = s[bid]
    local mode = 1
    if r == nil or (r.added and level(u, bid) == 0) then
      r = { flags = r and r.flags or {} }
      s[bid] = r
      mode = 0
      if level(u, bid) == 0 then r.added = nat('UnitAddAbility', u, bid) == true end
    end
    r.level, r.caster, r.dur = lvl, t, real(dur)
    if r.added then nat('SetUnitAbilityLevel', u, bid, lvl) end
    arm(u, bid, r, r.dur)
    if r.dur <= 0 and r.timer then nat('PauseTimer', r.timer) r.ends = nil end
    fire(mode, u, bid, t)
    return true
  end
  N.XMUnitBuffSetFlag = function(u, bid, t, v)
    if H.no(u) then return end
    local r = rec(u, bid)
    if r == nil then
      if level(u, bid) == 0 then return end
      r = { flags = {}, level = level(u, bid) }
      S(BUFF, u)[bid] = r
    end
    r.flags[t] = v == true
  end

  N.XMGetUnitBuffCastUnit = function(u, bid)
    local r = rec(u, bid)
    return r and r.caster or nil
  end

  N.XMEnableBuffExtend = function() H.ensure() end


  N.XMGetUnitAbilityLevel = function(u, aid)
    if H.no(u) then return 0 end
    local r = rec(u, aid)
    if r and r.level then
      if r.added and level(u, aid) == 0 then remove(u, aid, true) return 0 end
      return int(r.level)
    end
    return level(u, aid)
  end
end





do
  local N = __xm_nat
  local H = N.__unidade
  local nat, S, peek, int, real, hid, level, now = H.nat, H.S, H.peek, H.int, H.real, H.hid, H.level, H.now
  local REG, ASTATE = {}, {}
  N.XMGetUnitAbility = function(u, aid)
    if H.no(u) then return nil end
    local a = nat('BlzGetUnitAbility', u, aid)
    local k = hid(a)
    if k then REG[k] = { u = u, aid = aid } end
    return a
  end
  local function owner(a)
    local k = hid(a)
    return k and REG[k] or nil, k
  end
  local function lvl0(u, aid) return math.max(0, level(u, aid) - 1) end
  N.XMGetAbilityDuration = function(a)
    local o, k = owner(a)
    if k == nil then return 0.0 end
    if o then
      local r = H.buff(o.u, o.aid)
      if r then return real(r.dur) end
    end
    local s = ASTATE[k]
    if s and s.dur then return real(s.dur) end
    if o then return real(nat('BlzGetUnitAbilityCooldown', o.u, o.aid, lvl0(o.u, o.aid))) end
    return 0.0
  end
  N.XMSetAbilityDuration = function(a, t)
    local o, k = owner(a)
    if k == nil then return end
    if o then
      local r = H.buff(o.u, o.aid)
      if r then r.dur = real(t) return end
    end
    ASTATE[k] = ASTATE[k] or {}
    ASTATE[k].dur = real(t)
  end
  N.XMGetAbilityCountdown = function(a)
    local o, k = owner(a)
    if k == nil then return 0.0 end
    if o then
      local r = H.buff(o.u, o.aid)
      if r then
        if r.timer and r.ends then return math.max(0.0, real(nat('TimerGetRemaining', r.timer))) end
        return 0.0
      end
      return real(nat('BlzGetUnitAbilityCooldownRemaining', o.u, o.aid))
    end
    local s = ASTATE[k]
    if s and s.ends then return math.max(0.0, s.ends - now()) end
    return 0.0
  end
  N.XMSetAbilityCountdown = function(a, t)
    t = math.max(0.0, real(t))
    local o, k = owner(a)
    if k == nil then return end
    if o then
      local r = H.buff(o.u, o.aid)
      if r then
        if t <= 0 then H.remove_buff(o.u, o.aid) else H.arm_buff(o.u, o.aid, r, t) end
        return
      end
      if t <= 0 then nat('BlzEndUnitAbilityCooldown', o.u, o.aid) else nat('BlzStartUnitAbilityCooldown', o.u, o.aid, t) end
      return
    end
    ASTATE[k] = ASTATE[k] or {}
    ASTATE[k].ends = now() + t
  end



  local CD = {}
  N.XMSetUnitCDIDCooldown = function(u, cdid, duration, countdown)
    if H.no(u) then return end
    local s = S(CD, u)
    s[cdid] = { dur = real(duration), ends = now() + math.max(0.0, real(countdown)) }
    if level(u, cdid) > 0 then
      if countdown > 0 then nat('BlzStartUnitAbilityCooldown', u, cdid, countdown + 0.0) else nat('BlzEndUnitAbilityCooldown', u, cdid) end
    end
  end
  N.XMGetUnitCDIDDuration = function(u, cdid)
    local s = peek(CD, u)
    local r = s and s[cdid]
    if r and now() < r.ends then return real(r.dur) end
    if not H.no(u) and level(u, cdid) > 0 and real(nat('BlzGetUnitAbilityCooldownRemaining', u, cdid)) > 0 then
      return real(nat('BlzGetUnitAbilityCooldown', u, cdid, lvl0(u, cdid)))
    end
    return 0.0
  end
  N.XMGetUnitCDIDCountdown = function(u, cdid)
    local s = peek(CD, u)
    local r = s and s[cdid]
    if r then
      local left = r.ends - now()
      if left > 0 then return left + 0.0 end
    end
    if not H.no(u) and level(u, cdid) > 0 then return real(nat('BlzGetUnitAbilityCooldownRemaining', u, cdid)) end
    return 0.0
  end



  local SLK_REAL = { [42] = 'cast', [44] = 'cool', [47] = 'dur', [48] = 'herodur', [50] = 'rng', [51] = 'area',
    [52] = 'dataa', [53] = 'datab', [54] = 'datac', [55] = 'datad', [56] = 'datae', [57] = 'dataf', [58] = 'datag',
    [59] = 'datah', [60] = 'datai' }
  N.XMGetAbilityReal = function(aid, lvl, t)
    lvl = math.max(1, lvl or 1)
    if t == 44 then
      local v = nat('BlzGetAbilityCooldown', aid, lvl - 1)
      if v ~= nil then return real(v) end
    end
    local key = SLK_REAL[t]
    if key == nil then return 0.0 end
    return real(H.slk('ability', aid, key .. lvl) or H.slk('ability', aid, key .. '1'))
  end
end





do
  local N = __xm_nat
  local H = N.__unidade
  local nat, field, S, peek, int, real, str, level, cc = H.nat, H.field, H.S, H.peek, H.int, H.real, H.str, H.level, H.cc
  local AD = {}
  H.AD = AD
  local function abil(u, aid) return nat('BlzGetUnitAbility', u, aid) end
  local function lv(u, aid) return math.max(0, level(u, aid) - 1) end
  local function kept(u, aid) return S(AD, u)[aid] or (function() local t = {} S(AD, u)[aid] = t return t end)() end
  local function seen(u, aid)
    local s = peek(AD, u)
    return s and s[aid] or nil
  end

  local function ifld(code)
    return { function(u, aid, a) local f = field('ConvertAbilityIntegerField', code) return f and nat('BlzGetAbilityIntegerField', a, f) end,
      function(u, aid, a, v) local f = field('ConvertAbilityIntegerField', code) if f then nat('BlzSetAbilityIntegerField', a, f, v) end end }
  end
  local function ilf(code)
    return { function(u, aid, a) local f = field('ConvertAbilityIntegerLevelField', code) return f and nat('BlzGetAbilityIntegerLevelField', a, f, lv(u, aid)) end,
      function(u, aid, a, v) local f = field('ConvertAbilityIntegerLevelField', code) if f then nat('BlzSetAbilityIntegerLevelField', a, f, lv(u, aid), v) end end }
  end
  local function rlf(code)
    return { function(u, aid, a) local f = field('ConvertAbilityRealLevelField', code) return f and nat('BlzGetAbilityRealLevelField', a, f, lv(u, aid)) end,
      function(u, aid, a, v) local f = field('ConvertAbilityRealLevelField', code) if f then nat('BlzSetAbilityRealLevelField', a, f, lv(u, aid), v) end end }
  end
  local function sf(code)
    return { function(u, aid, a) local f = field('ConvertAbilityStringField', code) return f and nat('BlzGetAbilityStringField', a, f) end,
      function(u, aid, a, v) local f = field('ConvertAbilityStringField', code) if f then nat('BlzSetAbilityStringField', a, f, v) end end }
  end

  local function slf(code, typeset)
    return { function(u, aid, a) local f = field('ConvertAbilityStringLevelField', code) return f and nat('BlzGetAbilityStringLevelField', a, f, lv(u, aid)) end,
      function(u, aid, a, v)
        local f = field('ConvertAbilityStringLevelField', code)
        if f then nat('BlzSetAbilityStringLevelField', a, f, lv(u, aid), v) end
        if typeset == 'icon' then nat('BlzSetAbilityIcon', aid, v)
        elseif typeset == 'aicon' then nat('BlzSetAbilityActivatedIcon', aid, v)
        elseif typeset then nat(typeset, aid, v, lv(u, aid)) end
      end }
  end
  local AINT = {
    [8] = ifld('aubx'), [9] = ifld('auby'), [10] = ifld('abpx'), [11] = ifld('abpy'),
    [36] = { function(u, aid) return level(u, aid) end, function(u, aid, a, v) nat('SetUnitAbilityLevel', u, aid, v) end },
    [45] = ilf('atar'),
    [49] = { function(u, aid) return nat('BlzGetUnitAbilityManaCost', u, aid, lv(u, aid)) end,
      function(u, aid, a, v) nat('BlzSetUnitAbilityManaCost', u, aid, lv(u, aid), v) end },
  }
  local AREAL = {
    [21] = { function(u, aid, a) local f = field('ConvertAbilityIntegerField', 'amsp') return f and nat('BlzGetAbilityIntegerField', a, f) end,
      function(u, aid, a, v) local f = field('ConvertAbilityIntegerField', 'amsp') if f then nat('BlzSetAbilityIntegerField', a, f, H.int(v)) end end },
    [22] = { function(u, aid, a) local f = field('ConvertAbilityRealField', 'amac') return f and nat('BlzGetAbilityRealField', a, f) end,
      function(u, aid, a, v) local f = field('ConvertAbilityRealField', 'amac') if f then nat('BlzSetAbilityRealField', a, f, v) end end },
    [42] = rlf('acas'),

    [43] = { function(u, aid) return nat('BlzGetUnitAbilityCooldownRemaining', u, aid) end,
      function(u, aid, a, v) if v > 0 then nat('BlzStartUnitAbilityCooldown', u, aid, v) else nat('BlzEndUnitAbilityCooldown', u, aid) end end },
    [44] = { function(u, aid) return nat('BlzGetUnitAbilityCooldown', u, aid, lv(u, aid)) end,
      function(u, aid, a, v) nat('BlzSetUnitAbilityCooldown', u, aid, lv(u, aid), v) end },
    [47] = rlf('adur'), [48] = rlf('ahdu'), [50] = rlf('aran'), [51] = rlf('aare'),
  }
  local ASTR = {
    [1] = sf('anam'), [2] = slf('aut1', 'BlzSetAbilityActivatedTooltip'), [3] = slf('auu1', 'BlzSetAbilityActivatedExtendedTooltip'),
    [4] = slf('atp1', 'BlzSetAbilityTooltip'), [5] = slf('aub1', 'BlzSetAbilityExtendedTooltip'),
    [14] = { sf('auar')[1], function(u, aid, a, v) sf('auar')[2](u, aid, a, v) nat('BlzSetAbilityActivatedIcon', aid, v) end },
    [15] = slf('aart', 'icon'), [17] = slf('asat'), [19] = slf('amat'), [24] = slf('aeat'), [25] = slf('atat'),
    [28] = slf('aaea'), [30] = slf('acat'),
  }

  local SLK_DATA = { [52] = 'dataa', [53] = 'datab', [54] = 'datac', [55] = 'datad', [56] = 'datae', [57] = 'dataf',
    [58] = 'datag', [59] = 'datah', [60] = 'datai' }
  local function getter(tab, conv, empty)
    return function(u, aid, t)
      if H.no(u) then return empty end
      local k = seen(u, aid)
      if k and k[t] ~= nil and t ~= 36 and t ~= 43 then return conv(k[t]) end
      local e = tab[t]
      if e and e[1] then
        local a = abil(u, aid)
        if not H.no(a) or t == 36 then
          local v = e[1](u, aid, a)
          if v ~= nil then return conv(v) end
        end
      end
      if SLK_DATA[t] and level(u, aid) > 0 then
        local v = H.slk('ability', aid, SLK_DATA[t] .. level(u, aid))
        if v ~= nil then return conv(v) end
      end
      return empty
    end
  end
  local function setter(tab, conv)
    return function(u, aid, t, v)
      if H.no(u) then return end
      H.ensure()
      v = conv(v)
      local e = tab[t]
      if e and e[2] then
        local a = abil(u, aid)
        if not H.no(a) or t == 36 then e[2](u, aid, a, v) end
      end
      if t ~= 36 and t ~= 43 then kept(u, aid)[t] = v end
    end
  end
  N.XMUnitAbilityGetInt = getter(AINT, int, 0)
  N.XMUnitAbilitySetInt = setter(AINT, int)
  N.XMUnitAbilityGetReal = getter(AREAL, real, 0.0)
  N.XMUnitAbilitySetReal = setter(AREAL, real)
  N.XMUnitAbilityGetStr = getter(ASTR, str, '')
  N.XMUnitAbilitySetStr = setter(ASTR, str)
end

do
  local N = __xm_nat
  local H = N.__unidade
  local nat, S, peek, int, real, str, level, cc, slk = H.nat, H.S, H.peek, H.int, H.real, H.str, H.level, H.cc, H.slk
  local function code(aid) return str(slk('ability', aid, 'code')) end
  local function order(aid) return str(slk('ability', aid, 'order')) end
  local AURAS = { AHab = true, AHad = true, AOae = true, AUau = true, AEah = true, AEar = true, AOr2 = true, AUav = true,
    ACba = true, ACac = true, ACav = true, ACat = true, AOac = true, AEtr = true, ACnr = true, ACvs = true }

  N.XMUnitAbilityGetType = function(u, aid)
    if H.no(u) or level(u, aid) == 0 then return 0 end
    local c = code(aid)
    if AURAS[c] then return 3 end
    if order(aid) ~= '' or str(slk('ability', aid, 'orderon')) ~= '' then return 1 end
    if c:sub(1, 2) == 'AI' then return 4 end
    return 2
  end

  N.XMUnitAbilityGetCastType = function(u, aid)
    if H.no(u) or level(u, aid) == 0 then return 0 end
    if code(aid) == 'ANcl' then
      local b = int(slk('ability', aid, 'datab' .. level(u, aid)))
      if b == 1 then return 4 elseif b == 2 then return 2 elseif b == 3 then return 6 end
      return 1
    end
    local t = str(slk('ability', aid, 'targs1')):lower()
    if t == '' or t == '_' or t == 'none' or t == 'self' then return 1 end
    return 4
  end

  N.XMUnitAbilityCheckCanUse = function(u, aid)
    if H.no(u) or level(u, aid) == 0 then return false end
    if real(nat('BlzGetUnitAbilityCooldownRemaining', u, aid)) > 0 then return false end
    local cost = int(nat('BlzGetUnitAbilityManaCost', u, aid, level(u, aid) - 1))
    return real(nat('GetUnitState', u, nat('ConvertUnitState', 2))) >= cost
  end

  N.XMUnitAbilityGetTarget = function(u, aid)
    H.ensure()
    local s = peek(H.SPELL_TGT, u)
    local t = s and s[aid]
    return t or nil
  end

  local function req(aid)
    local ids, lv = {}, {}
    for w in str(slk('ability', aid, 'requires')):gmatch('[^,]+') do
      local s = w:match('^%s*(.-)%s*$')
      if #s == 4 then ids[#ids + 1] = cc(s) end
    end
    for s in str(slk('ability', aid, 'requiresamount')):gmatch('[^,]+') do lv[#lv + 1] = int(s) end
    return ids, lv
  end
  N.XMUnitAbilityRequireListGetCount = function(u, aid) local ids = req(aid) return #ids end
  N.XMUnitAbilityRequireListGetId = function(u, aid, i) local ids = req(aid) return ids[i + 1] or 0 end
  N.XMUnitAbilityRequireListGetLevel = function(u, aid, i)
    local ids, lv = req(aid)
    if ids[i + 1] == nil then return 0 end
    local v = lv[i + 1]
    return (v and v > 0) and v or 1
  end

  N.XMUnitAbilityShow = function(u, aid, show) if u then nat('BlzUnitHideAbility', u, aid, not show) end end

  local SIL = {}
  N.XMSilenceUnitAbility = function(u, aid, hide)
    if H.no(u) then return end
    local s = S(SIL, u)
    if s[aid] then return end
    s[aid] = true
    nat('BlzUnitDisableAbility', u, aid, true, hide == true)
  end
  N.XMUnsilenceUnitAbility = function(u, aid, show)
    if H.no(u) then return end
    local s = S(SIL, u)
    if not s[aid] then return end
    s[aid] = nil
    nat('BlzUnitDisableAbility', u, aid, false, not show)
  end

  local KEEP = { Aatk = true, Amov = true, AInv = true, Ahar = true, Aloc = true, Avul = true, Abun = true, Amrf = true }
  N.XMSilenceUnit = function(u, b)
    if H.no(u) then return end
    local s = S(SIL, u)
    b = b == true
    if (s.all or false) == b then return end
    s.all = b
    for i = 0, 255 do
      local a = nat('BlzGetUnitAbilityByIndex', u, i)
      if H.no(a) then break end
      local id = int(nat('BlzGetAbilityId', a))
      local name = string.pack('>I4', id & 0xFFFFFFFF)
      if not KEEP[name] and name:sub(1, 1) ~= 'B' and not s[id] then nat('BlzUnitDisableAbility', u, id, b, false) end
    end
  end

  N.XMUnitRemoveAbilityEx = function(u, it, aid)
    if not H.no(it) then nat('BlzItemRemoveAbility', it, aid) return end
    if H.no(u) then return end
    if H.buff(u, aid) then H.remove_buff(u, aid) end
    nat('UnitRemoveAbility', u, aid)
  end

  local function ord(aid)
    local o = order(aid)
    if o == '' then return 0 end
    return int(nat('OrderId', o))
  end
  N.XMUnitSimulateAbility = function(u, aid)
    if H.no(u) or level(u, aid) == 0 then return false end
    local o = ord(aid)
    return o ~= 0 and nat('IssueImmediateOrderById', u, o) == true
  end
  N.XMUnitSimulateAbilityByTarget = function(u, aid, t)
    if H.no(u) or H.no(t) or level(u, aid) == 0 then return false end
    local o = ord(aid)
    return o ~= 0 and nat('IssueTargetOrderById', u, o, t) == true
  end
  N.XMUnitSimulateAbilityByXY = function(u, aid, x, y)
    if H.no(u) or level(u, aid) == 0 then return false end
    local o = ord(aid)
    return o ~= 0 and nat('IssuePointOrderById', u, o, x, y) == true
  end


  N.XMUnitSimulateAttackEx = function(u, mode, t, _nodist, _nomiss)
    if H.no(u) or H.no(t) then return false end
    local w = (mode == 1) and 1 or 0
    local base = int(nat('BlzGetUnitBaseDamage', u, w))
    local dice = int(nat('BlzGetUnitDiceNumber', u, w))
    local sides = int(nat('BlzGetUnitDiceSides', u, w))
    local roll = 0
    if dice > 0 and sides > 0 then roll = int(nat('GetRandomInt', dice, dice * sides)) end
    local wf = H.field('ConvertUnitWeaponIntegerField', 'ua1t')
    local at = wf and nat('BlzGetUnitWeaponIntegerField', u, wf, w) or 1
    local atk = nat('ConvertAttackType', at) or nat('ConvertAttackType', 0)
    local dmg = nat('ConvertDamageType', 4)
    local wpn = nat('ConvertWeaponType', 0)
    return nat('UnitDamageTarget', u, t, (base + roll) + 0.0, true, false, atk, dmg, wpn) == true
  end
end




do
  local N = __xm_nat
  local H = N.__unidade
  local nat, field, S, peek, int, real, str, slk, cc = H.nat, H.field, H.S, H.peek, H.int, H.real, H.str, H.slk, H.cc
  local IA = {}
  H.ITEM = IA
  local ISTR = {
    [1] = { 'BlzGetItemIconPath', 'BlzSetItemIconPath' }, [2] = { 'BlzGetItemTooltip', 'BlzSetItemTooltip' },
    [3] = { 'BlzGetItemExtendedTooltip', 'BlzSetItemExtendedTooltip' }, [4] = { 'GetItemName', 'BlzSetItemName' },
    [5] = { 'BlzGetItemDescription', 'BlzSetItemDescription' },
  }
  N.XMSetItemAttr = function(it, t, v)
    if H.no(it) then return end
    v = str(v)
    S(IA, it)['s' .. t] = v
    local e = ISTR[t]
    if e then nat(e[2], it, v)
    elseif t == 254 then
      local f = field('ConvertItemStringField', 'ifil')
      if f then nat('BlzSetItemStringField', it, f, v) end
    end
  end
  N.XMGetItemAttr = function(it, t)
    if H.no(it) then return '' end
    local s = peek(IA, it)
    if s and s['s' .. t] ~= nil then return s['s' .. t] end
    local e = ISTR[t]
    if e then return str(nat(e[1], it)) end
    if t == 254 then return str(slk('item', nat('GetItemTypeId', it) or 0, 'file')) end
    return ''
  end
  local function icid(it)
    local f = field('ConvertItemIntegerField', 'icid')
    local v = f and nat('BlzGetItemIntegerField', it, f)
    if v ~= nil and v ~= 0 then return int(v) end
    local s = str(slk('item', nat('GetItemTypeId', it) or 0, 'cooldownid'))
    if #s == 4 then return cc(s) end
    return 0
  end
  N.XMSetItemAttrInteger = function(it, t, v)
    if H.no(it) then return end
    S(IA, it)[t] = v
    if t == 156 then
      local f = field('ConvertItemIntegerField', 'icid')
      if f then nat('BlzSetItemIntegerField', it, f, v) end
    end
  end
  N.XMGetItemAttrInteger = function(it, t)
    if H.no(it) then return 0 end
    local s = peek(IA, it)
    if s and s[t] ~= nil then return int(s[t]) end
    if t == 156 then return icid(it) end
    return 0
  end

  local SLK_INT = { [72] = 'pickrandom', [76] = 'powerup', [80] = 'sellable', [84] = 'pawnable', [88] = 'usable',
    [92] = 'perishable', [96] = 'droppable', [100] = 'dropondeath', [112] = 'cooldownid', [116] = 'ignorecd' }
  local SLK_STR = { [44] = 'name', [48] = 'description', [588] = 'art', [608] = 'tip', [620] = 'ubertip' }
  N.XMGetItemSlkInt = function(id, t)
    local k = SLK_INT[t]
    if k == nil then return 0 end
    local v = slk('item', id, k)
    if t == 112 then
      v = str(v)
      return #v == 4 and cc(v) or 0
    end
    return int(v)
  end
  N.XMGetItemSlkStr = function(id, t)
    local k = SLK_STR[t]
    if k == nil then return '' end
    return str(slk('item', id, k))
  end

  N.XMGetItemSpellAbility = function(it)
    if H.no(it) then return 0 end
    local a = nat('BlzGetItemAbilityByIndex', it, 0)
    return a and int(nat('BlzGetAbilityId', a)) or 0
  end


  local STYLE = { [64] = 'iper', [128] = 'idrp', [512] = 'iusa', [1024] = 'idro', [2048] = 'ipow', [8192] = 'ipaw' }
  N.XMGetItemStyle = function(it)
    if H.no(it) then return 0 end
    local v = 0
    for bit, code in pairs(STYLE) do
      local f = field('ConvertItemBooleanField', code)
      if f and nat('BlzGetItemBooleanField', it, f) == true then v = v | bit end
    end
    local s = peek(IA, it)
    if s and s.inf then v = v | 4096 end
    return v
  end
  N.XMSetItemStyle = function(it, v)
    if H.no(it) then return end
    for bit, code in pairs(STYLE) do
      local f = field('ConvertItemBooleanField', code)
      if f then nat('BlzSetItemBooleanField', it, f, (v & bit) ~= 0) end
    end
    S(IA, it).inf = (v & 4096) ~= 0
  end

  N.XMGetItemUnderMouse = function() return nil end

  N.XMModifyItemIDList = function(it, t, mode, id)
    if H.no(it) or t ~= 142 then return end
    if mode then nat('BlzItemAddAbility', it, id) else nat('BlzItemRemoveAbility', it, id) end
  end

  local STOCK = {}
  N.XMSetItemFromStockReal = function(u, id, t, v)
    if H.no(u) then return end
    local s = S(STOCK, u)
    local r = s[id] or {}
    s[id] = r
    r[t] = v
    if t == 0 or t == 1 then
      local cur = int(r[0] or 1)
      local max = int(r[1] or slk('item', id, 'stockmax') or cur)
      if cur <= 0 then nat('RemoveItemFromStock', u, id) else nat('AddItemToStock', u, id, cur, math.max(cur, max)) end
    end
  end
end
