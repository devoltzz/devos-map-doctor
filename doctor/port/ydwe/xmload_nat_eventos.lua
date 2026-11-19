








do
  local N = __xm_nat or {}
  __xm_nat = N
  local S = N.__evt or {}
  N.__evt = S
  local function C() return __xm_ctx end
  S.C = C
  local function live(h) return h ~= nil and h ~= 0 end
  S.live = live
  local function int(v) return math.tointeger(v) or math.tointeger(math.floor(tonumber(v) or 0)) or 0 end
  S.int = int
  local function num(v) return (tonumber(v) or 0) + 0.0 end
  S.num = num




  S.tu = S.tu or {}
  S.ab = S.ab or {}
  S.orig = S.orig or {}
  local function event_key()
    local f = S.orig.GetTriggerEventId or C().common.GetTriggerEventId
    if type(f) ~= 'function' then return false end
    local ok, e = pcall(f)
    if not ok or e == nil then return false end
    return e
  end
  S.event_key = event_key


  S.jorig = S.jorig or {}
  local function native_j(name)
    local v = S.jorig[name]
    if v ~= nil then return v or nil end
    local env = rawget(_G, '__JENV')
    local raw = env and rawget(env, name)
    if type(raw) ~= 'function' then raw = rawget(_G, name) end
    local pl = rawget(_G, '__ydwe_para_lua')
    if type(raw) == 'function' and type(pl) == 'function' then v = pl(name, raw)
    else v = C().common[name] end
    S.jorig[name] = type(v) == 'function' and v or false
    return S.jorig[name] or nil
  end
  S.native_j = native_j

  local function hook(name, mk)
    if S.orig[name] ~= nil then return S.orig[name] ~= false end
    local c = C()
    local ok, o = pcall(function() return c.common[name] end)
    if not ok or type(o) ~= 'function' then S.orig[name] = false return false end
    local oj = native_j(name) or o
    S.orig[name] = o
    pcall(function() c.jass_code[name] = mk(oj) end)
    pcall(rawset, c.common, name, mk(o))
    return true
  end
  S.hook = hook
  local function hook_trigger_unit()
    hook('GetTriggerEventId', function(o) return o end)
    hook('GetTriggerUnit', function(o)
      return function()
        local top = S.tu[#S.tu] or S.set_unit
        if top == nil then return o() end
        local r = o()

        if live(r) and top.ev ~= event_key() then return r end
        return top.u
      end
    end)
  end
  S.hook_trigger_unit = hook_trigger_unit



  local function fire(list, u, ab, pre, post)
    if list == nil or #list == 0 then return end
    local c = C()
    hook_trigger_unit()
    local snap = {}
    for i = 1, #list do snap[i] = list[i] end
    S.tu[#S.tu + 1] = { u = u, ev = event_key() }
    S.ab[#S.ab + 1] = ab or 0
    if pre then pre() end
    for i = 1, #snap do
      local t = snap[i]
      pcall(function()
        if c.common.IsTriggerEnabled(t) and c.common.TriggerEvaluate(t) then c.common.TriggerExecute(t) end
      end)
    end
    if post then post() end
    S.ab[#S.ab] = nil
    S.tu[#S.tu] = nil
  end
  S.fire = fire
  local function add_trig(list, trig)
    if not live(trig) then return end
    for i = 1, #list do if list[i] == trig then return end end
    list[#list + 1] = trig
  end
  S.add_trig = add_trig
  local function each_player(f)
    local c = C()
    local n = 28
    pcall(function() n = c.common.GetBJMaxPlayerSlots() or 28 end)
    for i = 0, n - 1 do
      local p = c.common.Player(i)
      if live(p) then f(p) end
    end
  end
  S.each_player = each_player
  local function ev(name, id)
    local v = C().common[name]
    if v == nil then return id end
    return v
  end
  S.ev = ev

  S.listen = S.listen or {}
  local function listen(name, id, fn)
    local l = S.listen[name]
    if l == nil then
      local c = C()
      l = {}
      S.listen[name] = l
      local trig = c.common.CreateTrigger()
      local e = ev(name, id)
      each_player(function(p) c.common.TriggerRegisterPlayerUnitEvent(trig, p, e, nil) end)
      c.common.TriggerAddAction(trig, function()
        for i = 1, #l do pcall(l[i]) end
      end)
    end
    l[#l + 1] = fn
  end
  S.listen_event = listen



  N.XMSetTriggerUnit = function(u)
    if live(u) then
      hook_trigger_unit()
      S.set_unit = { u = u, ev = event_key() }
    else
      S.set_unit = nil
    end
  end
  local function cur_ab() return int(S.ab[#S.ab] or 0) end
  N.XMTriggerAbility = cur_ab
  N.XMTriggerBuff = cur_ab

  S.buff_trg = S.buff_trg or { [0] = {}, [1] = {}, [2] = {} }

  N._on_buff = function(mode, u, buff, caster)
    local l = S.buff_trg[math.tointeger(mode) or -1]
    if l and #l > 0 and live(u) then fire(l, u, buff) end
  end
  N.__xm_fire_buff = N._on_buff
end


do
  local N = __xm_nat
  local S = N.__evt
  local C, live, int, fire, add_trig, listen, ev = S.C, S.live, S.int, S.fire, S.add_trig, S.listen_event, S.ev



  S.unit_trg = S.unit_trg or { [0] = {}, [1] = {} }
  local seen = S.seen or {}
  S.seen = seen
  local function world_enter()
    if S.enter_trig then return end
    local c = C()
    local reg = c.common.CreateRegion()
    c.common.RegionAddRect(reg, c.common.GetWorldBounds())
    local trig = c.common.CreateTrigger()
    S.enter_trig = trig
    c.common.TriggerRegisterEnterRegion(trig, reg, nil)
    c.common.TriggerAddAction(trig, function()
      local u = c.common.GetTriggerUnit()
      if not live(u) then return end
      local ty = c.common.GetUnitTypeId(u)
      if seen[u] == ty then return end
      seen[u] = ty
      fire(S.unit_trg[0], u)
    end)
  end
  N.XMTriggerRegisterUnitEventTrg = function(trig, e)
    local l = S.unit_trg[e]
    if l == nil then return end
    add_trig(l, trig)
    if e == 0 then world_enter() end
  end





  S.illusion_rates = function()
    if S.illusion_on then return end
    S.illusion_on = true
    local c = C()
    listen('EVENT_PLAYER_UNIT_DAMAGING', 308, function()
      local H = N.__unidade
      local IL = H and H.ILLUSION
      if IL == nil or next(IL) == nil then return end
      local a, d = IL[c.common.GetEventDamageSource()], IL[c.common.GetTriggerUnit()]
      if a == nil and d == nil then return end
      local get, set = S.native_j('GetEventDamage'), S.native_j('BlzSetEventDamage')
      if not get or not set then return end
      local v = S.num(get())
      if a and tonumber(a.atk) then v = v * a.atk end
      if d and tonumber(d.def) then v = v * d.def end
      set(v)
    end)
  end
  N.XMTriggerRegisterUnitDamagedPreTrg = function(trig)
    if not live(trig) then return end
    local c = C()
    S.illusion_rates()
    local e = ev('EVENT_PLAYER_UNIT_DAMAGING', 308)
    S.each_player(function(p) c.common.TriggerRegisterPlayerUnitEvent(trig, p, e, nil) end)
    S.track_spells()
  end


  N.XMDamageEventSkip = function()
    local c = C()
    pcall(c.common.BlzSetEventDamage, 0.0)
  end

  N.XMEnableDamageEx = function() S.track_spells() S.illusion_rates() end



  S.spell = S.spell or {}
  S.dmg_depth = S.dmg_depth or 0
  S.track_spells = function()
    if S.spells_on then return end
    S.spells_on = true
    local c = C()
    listen('EVENT_PLAYER_UNIT_SPELL_EFFECT', 274, function()
      local u = c.common.GetTriggerUnit()
      if live(u) then S.spell[u] = { id = c.common.GetSpellAbilityId(), t = c.game_time() } end
    end)
    S.hook('UnitDamageTarget', function(o)
      return function(...)
        S.dmg_depth = S.dmg_depth + 1
        local ok, r = pcall(o, ...)
        S.dmg_depth = S.dmg_depth - 1
        if not ok then return false end
        return r
      end
    end)
  end
  N.XMGetDamageAbility = function()
    local c = C()
    if S.dmg_depth > 0 then return 0 end
    local ok, atk = pcall(c.common.BlzGetEventIsAttack)
    if ok and atk then return 0 end
    local src = c.common.GetEventDamageSource()
    local s = live(src) and S.spell[src] or nil
    if s == nil or c.game_time() - s.t > 8.0 then return 0 end
    return int(s.id)
  end


  N.XMTriggerRegisterUnitAttackTrg = function(trig)
    if not live(trig) then return end
    local c = C()
    local e = ev('EVENT_PLAYER_UNIT_ATTACKED', 18)
    S.each_player(function(p) c.common.TriggerRegisterPlayerUnitEvent(trig, p, e, nil) end)
  end


  S.war3_trg = S.war3_trg or { [0] = {}, [1] = {}, [2] = {}, [3] = {} }
  N.XMTriggerRegisterUnitWar3EventTrg = function(trig, e)
    local l = S.war3_trg[e]
    if l then add_trig(l, trig) end
  end

  S.revive_trg = S.revive_trg or {}
  N.XMTriggerRegisterUnitReviveTrg = function(trig)
    add_trig(S.revive_trg, trig)
    if S.revive_on then return end
    S.revive_on = true
    local c = C()
    local last = {}
    local function revived(u)
      if not live(u) then return end
      local t = c.game_time()
      if last[u] and t - last[u] < 0.05 then return end
      last[u] = t
      fire(S.revive_trg, u)
    end
    listen('EVENT_PLAYER_HERO_REVIVE_FINISH', 45, function() revived(c.common.GetTriggerUnit()) end)
    for _, name in ipairs({ 'ReviveHero', 'ReviveHeroLoc' }) do
      S.hook(name, function(o)
        return function(u, ...)
          local r = o(u, ...)
          if r then revived(u) end
          return r
        end
      end)
    end
  end



  S.addab_trg = S.addab_trg or {}
  S.remab_trg = S.remab_trg or {}
  N.XMTriggerRegisterUnitAddAbilityTrg = function(trig)
    add_trig(S.addab_trg, trig)
    if S.addab_on then return end
    S.addab_on = true
    local c = C()
    S.hook('UnitAddAbility', function(o)
      return function(u, id)
        local r = o(u, id)
        if r then fire(S.addab_trg, u, id) end
        return r
      end
    end)
    listen('EVENT_PLAYER_HERO_SKILL', 41, function()
      if c.common.GetLearnedSkillLevel() == 1 then
        fire(S.addab_trg, c.common.GetLearningUnit(), c.common.GetLearnedSkill())
      end
    end)
  end
  N.XMTriggerRegisterUnitRemoveAbilityTrg = function(trig)
    add_trig(S.remab_trg, trig)
    if S.remab_on then return end
    S.remab_on = true
    S.hook('UnitRemoveAbility', function(o)
      return function(u, id)

        local c = C()
        local had = live(u) and c.common.GetUnitAbilityLevel(u, id) > 0
        if had then fire(S.remab_trg, u, id) end
        return o(u, id)
      end
    end)
  end

  S.cd_trg = S.cd_trg or {}
  N.XMTriggerRegisterAbilityCooldownTrg = function(trig)
    add_trig(S.cd_trg, trig)
    if S.cd_on then return end
    S.cd_on = true
    local c = C()
    listen('EVENT_PLAYER_UNIT_SPELL_EFFECT', 274, function()
      fire(S.cd_trg, c.common.GetTriggerUnit(), c.common.GetSpellAbilityId())
    end)
  end


  N.XMTriggerRegisterUnitBuffEventTrg = function(trig, mode)
    local l = S.buff_trg[mode]
    if l then add_trig(l, trig) end
  end



  S.item_trg = S.item_trg or { [0] = {}, [1] = {} }
  local function fire_item(e, it)
    if not live(it) then return end
    S.hook('GetEnumItem', function(o)
      return function()
        local r = o()
        if live(r) or S.enum_item == nil then return r end
        return S.enum_item
      end
    end)
    local old = S.enum_item
    fire(S.item_trg[e], nil, 0, function() S.enum_item = it end, function() S.enum_item = old end)
  end
  N.XMTriggerRegisterItemEventTrg = function(trig, e)
    local l = S.item_trg[e]
    if l == nil then return end
    add_trig(l, trig)
    if e == 0 then
      S.hook('CreateItem', function(o)
        return function(...)
          local it = o(...)
          fire_item(0, it)
          return it
        end
      end)
    else
      S.hook('RemoveItem', function(o)
        return function(it)
          fire_item(1, it)
          return o(it)
        end
      end)
    end
  end



  S.mouse_trg = S.mouse_trg or {}
  N.XMTriggerRegisterMouseUnderEventTrg = function(trig, mode)
    S.mouse_trg['u' .. tostring(mode)] = S.mouse_trg['u' .. tostring(mode)] or {}
    add_trig(S.mouse_trg['u' .. tostring(mode)], trig)
  end
  N.XMTriggerRegisterMouseLeaveEventTrg = function(trig, mode)
    S.mouse_trg['l' .. tostring(mode)] = S.mouse_trg['l' .. tostring(mode)] or {}
    add_trig(S.mouse_trg['l' .. tostring(mode)], trig)
  end



  N.XMTriggerHatredEvent = function(u, target, flag)
    local c = C()
    if not live(u) or not live(target) or u == target then return end
    if c.common.GetWidgetLife(target) <= 0.405 or c.common.GetWidgetLife(u) <= 0.405 then return end
    local p = c.common.GetOwningPlayer(u)
    local user = ev('MAP_CONTROL_USER', 0)
    if c.common.GetPlayerController(p) == user then return end
    pcall(c.common.IssueTargetOrderById, u, 851983, target)
  end


  local WSND = { [1] = 'MetalLightChop', [2] = 'MetalMediumChop', [3] = 'MetalHeavyChop', [4] = 'MetalLightSlice',
    [5] = 'MetalMediumSlice', [6] = 'MetalHeavySlice', [7] = 'MetalMediumBash', [8] = 'MetalHeavyBash',
    [9] = 'MetalMediumStab', [10] = 'MetalHeavyStab', [11] = 'WoodLightSlice', [12] = 'WoodMediumSlice',
    [13] = 'WoodHeavySlice', [14] = 'WoodLightBash', [15] = 'WoodMediumBash', [16] = 'WoodHeavyBash',
    [17] = 'WoodLightStab', [18] = 'WoodMediumStab', [19] = 'ClawLightSlice', [20] = 'ClawMediumSlice',
    [21] = 'ClawHeavySlice', [22] = 'AxeMediumChop', [23] = 'RockHeavyBash' }
  N.XMPlayUnitDamageSound = function(u, wt)
    local c = C()
    local n = WSND[int(wt)]
    if n == nil or not live(u) then return end
    pcall(function()
      local s = c.common.CreateSound('Sound\\Units\\Combat\\' .. n .. 'Flesh1.wav', false, true, true, 10, 10, 'CombatSoundsEAX')
      if not live(s) then return end
      c.common.SetSoundPosition(s, c.common.GetUnitX(u), c.common.GetUnitY(u), 0.0)
      c.common.StartSound(s)
      c.common.KillSoundWhenDone(s)
    end)
  end

  N.XMSetAIPathingLevel = function(n) S.ai_pathing = int(n) end


  N.XMSetUnitPathType = function(u, v)
    local c = C()
    if not live(u) then return false end
    v = int(v)
    if v == 1 then c.common.SetUnitPathing(u, true)
    else c.common.SetUnitPathing(u, false) end
    if v == 2 or v == 8 then
      local add = S.orig.UnitAddAbility or c.common.UnitAddAbility
      local rem = S.orig.UnitRemoveAbility or c.common.UnitRemoveAbility
      local amrf = 0x416d7266
      if add(u, amrf) then rem(u, amrf) end
    end
    return true
  end
end


do
  local N = __xm_nat
  local S = N.__evt
  local C, live = S.C, S.live



  S.detail = S.detail or { widget = {}, group = {}, portrait = {} }
  S.console = S.console or 0
  local state = { widget = -1, group = -1, portrait = -1, main = nil, count = -1 }
  local function run(list, v)
    local old = S.console
    S.console = v
    for i = 1, #list do pcall(list[i]) end
    S.console = old
  end
  local function poll()
    local c = C()
    local g = S.sel_group
    c.common.GroupClear(g)
    c.common.GroupEnumUnitsSelected(g, c.common.GetLocalPlayer(), nil)
    local n = c.common.BlzGroupGetSize(g)
    local main = n > 0 and c.common.BlzGroupUnitAt(g, 0) or nil
    local w = (n == 1) and 1 or 0
    local gr = (n > 1) and 1 or 0
    local po = (n >= 1) and 1 or 0
    local changed = main ~= state.main or n ~= state.count
    if w ~= state.widget or (w == 1 and changed) then state.widget = w run(S.detail.widget, w) end
    if gr ~= state.group or (gr == 1 and changed) then state.group = gr run(S.detail.group, gr) end
    if po ~= state.portrait or (po == 1 and main ~= state.main) then state.portrait = po run(S.detail.portrait, po) end
    state.main, state.count = main, n
  end
  local function reg(kind, code)
    if type(code) ~= 'function' then return end
    local l = S.detail[kind]
    l[#l + 1] = code
    if S.sel_timer then return end
    local c = C()
    S.sel_group = c.common.CreateGroup()
    S.sel_timer = c.common.CreateTimer()
    c.common.TimerStart(S.sel_timer, 0.1, true, function() pcall(poll) end)
  end
  N.XMWidgetDetailRegisterEvent = function(code) reg('widget', code) end
  N.XMGroupDetailRegisterEvent = function(code) reg('group', code) end
  N.XMPortraitDetailRegisterEvent = function(code) reg('portrait', code) end

  N.XMConsoleEvent = function() return math.tointeger(S.console) or 0 end
end


do
  local N = __xm_nat
  local S = N.__evt
  local int = S.int




  local MAP, L = {}, {}
  S.mod_map, S.mod_lists = MAP, L
  local next_id = 0x36000000
  local function key(t, id, k1) return t .. ':' .. int(id) .. ':' .. int(k1) end
  local function release(lid)
    local l = L[lid]
    if l == nil then return 0 end
    l.ref = l.ref - 1
    if l.ref <= 0 then L[lid] = nil return 0 end
    return l.ref
  end
  local function find(l, f)
    for i = 1, #l.ent do if l.ent[i].f == f then return i end end
    return nil
  end
  local function valid(t) t = int(t) return t >= 1 and t <= 42 end
  N.XMStaticModuleBindEvent = function(t, id, k1, f)
    if not valid(t) then return end
    local k = key(int(t), id, k1)
    local lid = MAP[k]
    if lid == nil or L[lid] == nil then
      next_id = next_id + 1
      lid = next_id
      L[lid] = { ent = {}, ref = 1, lock = 0, dirty = false, t = int(t), id = int(id), k = k }
      MAP[k] = lid
    end
    local l = L[lid]
    f = int(f)
    local i = find(l, f)
    if i then l.ent[i].n = l.ent[i].n + 1 else l.ent[#l.ent + 1] = { f = f, n = 1 } end
  end
  N.XMStaticModuleUnbindEvent = function(t, id, k1, f)
    if not valid(t) then return end
    local k = key(int(t), id, k1)
    local lid = MAP[k]
    local l = lid and L[lid]
    if l == nil then return end
    local i = find(l, int(f))
    if i then
      local e = l.ent[i]
      e.n = e.n - 1
      if l.lock > 0 then l.dirty = true
      elseif e.n <= 0 then table.remove(l.ent, i) end
    end
    if #l.ent == 0 then MAP[k] = nil release(lid) end
  end
  N.XMStaticModuleBindEventCount = function(e, fn)
    local l = L[e]
    if l == nil then return 0 end
    local i = find(l, int(fn))
    return i and (math.tointeger(l.ent[i].n) or 0) or 0
  end
  N.XMStaticModuleClearAllEvent = function(t, id)
    if not valid(t) then return end
    t, id = int(t), int(id)
    for k, lid in pairs(MAP) do
      local l = L[lid]
      if l == nil then MAP[k] = nil
      elseif l.t == t and l.id == id then MAP[k] = nil release(lid) end
    end
  end
  N.XMStaticModuleLockEvent = function(t, id, k1)
    if not valid(t) then return 0 end
    local lid = MAP[key(int(t), id, k1)]
    local l = lid and L[lid]
    if l == nil then return 0 end
    l.ref = l.ref + 1
    l.lock = l.lock + 1
    return lid
  end
  N.XMStaticModuleUnlockEvent = function(e)
    local l = L[e]
    if l == nil then return end
    l.lock = l.lock - 1
    if l.lock <= 0 and l.dirty then
      local keep = {}
      for i = 1, #l.ent do if l.ent[i].n > 0 then keep[#keep + 1] = l.ent[i] end end
      l.ent, l.dirty, l.lock = keep, false, 0
    end
    if release(e) > 0 and #l.ent == 0 and MAP[l.k] == e then MAP[l.k] = nil release(e) end
  end
  N.XMStaticModuleGetEventListCount = function(e)
    local l = L[e]
    return l and (math.tointeger(#l.ent) or 0) or 0
  end
  N.XMStaticModuleGetEventByEventList = function(e, i)
    local l = L[e]
    i = int(i)
    if l == nil or i < 0 or i >= #l.ent then return 0 end
    return math.tointeger(l.ent[i + 1].f) or 0
  end
end


do
  local N = __xm_nat
  local S = N.__evt
  local C, live, int, num = S.C, S.live, S.int, S.num




  local P = {}
  S.paths = P
  local next_id = 0x34000000
  local function easing(k, s)
    if k == 2 then return s * s
    elseif k == 3 then return s * (2 - s)
    elseif k == 4 then return s < 0.5 and 2 * s * s or -1 + (4 - 2 * s) * s
    elseif k == 5 then return s * s * s
    elseif k == 6 then local q = s - 1 return q * q * q + 1
    elseif k == 7 then return s < 0.5 and 4 * s * s * s or (s - 1) * (2 * s - 2) * (2 * s - 2) + 1
    elseif k == 8 then return s * s * s * s
    elseif k == 9 then local q = s - 1 return 1 - q * q * q * q
    elseif k == 10 then local q = s - 1 return s < 0.5 and 8 * s * s * s * s or 1 - 8 * q * q * q * q
    elseif k == 11 then return s * s * s * s * s
    elseif k == 12 then local q = s - 1 return 1 + q * q * q * q * q
    elseif k == 13 then local q = s - 1 return s < 0.5 and 16 * s * s * s * s * s or 1 + 16 * q * q * q * q * q
    elseif k == 14 then return 1 - math.cos(s * math.pi / 2)
    elseif k == 15 then return math.sin(s * math.pi / 2)
    elseif k == 16 then return -(math.cos(math.pi * s) - 1) / 2
    end
    return s
  end
  local function eff_of(e)
    local f = N.__effect_of
    if type(f) == 'function' then local ok, r = pcall(f, e) if ok and r ~= nil then return r end end
    return e
  end
  S.eff_of = eff_of
  local function place(p)
    if not live(p.eff) then return end
    local c = C()
    local e = eff_of(p.eff)
    pcall(c.common.BlzSetSpecialEffectPosition, e, p.cur[1], p.cur[2], p.cur[3])
  end
  local function update(p, now)
    local s = p.dur > 0 and (now - p.t0) / p.dur or 1.0
    if s < 0 then s = 0 elseif s > 1 then s = 1 end
    s = easing(p.tween, s)
    local a, b, q = p.p0, p.p2, p.c
    local u = 1 - s
    local ox, oy = p.cur[1], p.cur[2]
    for i = 1, 3 do p.cur[i] = u * u * a[i] + 2 * u * s * q[i] + s * s * b[i] end
    if live(p.eff) and (p.cur[1] ~= ox or p.cur[2] ~= oy) then
      pcall(C().common.BlzSetSpecialEffectYaw, eff_of(p.eff), math.atan(p.cur[2] - oy, p.cur[1] - ox))
    end
    place(p)
  end
  N.XMPathCreateBezier2 = function(sx, sy, sz, ex, ey, ez, time)
    next_id = next_id + 1
    sx, sy, sz, ex, ey, ez = num(sx), num(sy), num(sz), num(ex), num(ey), num(ez)
    P[next_id] = { p0 = { sx, sy, sz }, p2 = { ex, ey, ez }, c = { (sx + ex) / 2, (sy + ey) / 2, (sz + ez) / 2 },
      cur = { sx, sy, sz }, t0 = C().game_time(), dur = num(time), tween = 0, eff = nil }
    return next_id
  end
  N.XMPathDestroy = function(p) P[p] = nil end
  N.XMPathBindEffect = function(p, e)
    local o = P[p]
    if o == nil then return end
    o.eff = live(e) and e or nil
    place(o)
  end
  N.XMPathGetEffect = function(p) local o = P[p] return o and o.eff or nil end
  local function point(o, t)
    t = int(t)
    if t == 1 then return o.p0 elseif t == 2 then return o.p2 elseif t == 3 then return o.c end
    return o.cur
  end
  N.XMPathGetX = function(p, t) local o = P[p] return o and num(point(o, t)[1]) or 0.0 end
  N.XMPathGetY = function(p, t) local o = P[p] return o and num(point(o, t)[2]) or 0.0 end
  N.XMPathGetZ = function(p, t) local o = P[p] return o and num(point(o, t)[3]) or 0.0 end
  N.XMPathSetXYZ = function(p, t, x, y, z)
    local o = P[p]
    if o == nil then return end
    local q = point(o, t)
    q[1], q[2], q[3] = num(x), num(y), num(z)
    if int(t) == 0 then place(o) end
  end

  N.XMPathSetTime = function(p, t, v)
    local o = P[p]
    if o == nil then return end
    t = int(t)
    if t == 1 then o.t0 = num(v) elseif t == 2 then o.dur = num(v) else update(o, num(v)) end
  end
  N.XMPathSetTween = function(p, t) local o = P[p] if o then o.tween = int(t) end end
  N.SaveXMPathHandle = function(ht, a, b, v) C().common.SaveInteger(ht, a, b, int(v)) return true end
  N.LoadXMPathHandle = function(ht, a, b) return C().common.LoadInteger(ht, a, b) end
end


do
  local N = __xm_nat
  local S = N.__evt
  local C, live, int, num, fire, add_trig = S.C, S.live, S.int, S.num, S.fire, S.add_trig





  local M, LIST = {}, {}
  S.missiles = M
  S.miss_trg = S.miss_trg or {}
  local next_id = 0x30000000
  local DT = 0.03125
  local cur_missile = {}
  local function terrain_z(x, y)
    local c = C()
    if S.zloc == nil then S.zloc = c.common.Location(0.0, 0.0) end
    c.common.MoveLocation(S.zloc, x, y)
    return num(c.common.GetLocationZ(S.zloc))
  end
  S.terrain_z = terrain_z
  local function alive(u)
    if not live(u) then return false end
    local c = C()
    return c.common.GetWidgetLife(u) > 0.405 and not c.common.IsUnitType(u, S.ev('UNIT_TYPE_DEAD', 1))
  end
  local function unit_z(u, add)
    local c = C()
    local x, y = c.common.GetUnitX(u), c.common.GetUnitY(u)
    return terrain_z(x, y) + num(c.common.GetUnitFlyHeight(u)) + add
  end

  local function accept(m, u)
    local c = C()
    local f = m.flags
    if not live(u) or (u == m.units[1] and (f & 0x1000) == 0) then return false end
    local dead = c.common.GetWidgetLife(u) <= 0.405
    if (f & 0x3000000) == 0x2000000 then if not dead then return false end
    elseif dead then return false end
    local src = m.units[1]
    local p = live(src) and c.common.GetOwningPlayer(src) or m.owner
    if f == 0 then return p == nil or c.common.IsUnitEnemy(u, p) end
    if (f & 0xe) ~= 0 then
      local st = c.common.IsUnitType(u, S.ev('UNIT_TYPE_STRUCTURE', 2))
      local fl = c.common.IsUnitType(u, S.ev('UNIT_TYPE_FLYING', 3))
      local ok = (st and (f & 0x8) ~= 0) or (not st and fl and (f & 0x4) ~= 0) or (not st and not fl and (f & 0x2) ~= 0)
      if not ok then return false end
    end
    if (f & 0x1f000) ~= 0 and p ~= nil then
      local o = c.common.GetOwningPlayer(u)
      local ok = ((f & 0x1000) ~= 0 and u == src) or ((f & 0x2000) ~= 0 and o == p)
        or ((f & 0x4000) ~= 0 and o ~= p and c.common.IsUnitAlly(u, p))
        or ((f & 0x10000) ~= 0 and c.common.IsUnitEnemy(u, p))
        or ((f & 0x8000) ~= 0 and c.common.GetPlayerId(o) >= 24)
      if not ok then return false end
    end
    if (f & 0x300000) == 0x100000 then
      local ok, inv = pcall(c.common.BlzIsUnitInvulnerable, u)
      if ok and inv then return false end
    end
    if (f & 0xc00000) == 0x400000 and not c.common.IsUnitType(u, S.ev('UNIT_TYPE_HERO', 0)) then return false end
    if (f & 0xc00000) == 0x800000 and c.common.IsUnitType(u, S.ev('UNIT_TYPE_HERO', 0)) then return false end
    return true
  end
  local function in_range(m, x, y, r, fn)
    local c = C()
    local g = c.enum_group(c.common.GroupEnumUnitsInRange, x, y, r, nil)
    local us = {}
    while true do
      local u = c.common.FirstOfGroup(g)
      if not live(u) then break end
      c.common.GroupRemoveUnit(g, u)
      us[#us + 1] = u
    end
    c.common.DestroyGroup(g)
    for i = 1, #us do if accept(m, us[i]) then fn(us[i]) end end
  end
  local function event(m, t, u)
    local l = S.miss_trg[t]
    if l == nil or #l == 0 then return end
    cur_missile[#cur_missile + 1] = m.id
    fire(l, u)
    cur_missile[#cur_missile] = nil
  end
  local function hit(m, u)
    if not live(u) then return end
    m.hit[u] = true
    m.last = u
    if m.dmg > 0 and live(m.units[1]) then

      local f = S.native_j('UnitDamageTarget')
      if f then pcall(f, m.units[1], u, m.dmg, false, true, m.at, m.dt, S.ev('WEAPON_TYPE_WHOKNOWS', 0)) end
    end
    event(m, 1, u)
  end
  local function finish(m)
    if m.dead then return end
    m.dead = true
    event(m, 2, m.last or m.units[2])
    local c = C()
    if live(m.eff) then
      local e = S.eff_of(m.eff)
      if not m.visible then pcall(c.common.BlzSetSpecialEffectAlpha, e, 0) end
      pcall(c.common.DestroyEffect, e)
    end
    M[m.id] = nil
  end
  local function show(m)
    if not live(m.eff) then return end
    local c = C()
    local e = S.eff_of(m.eff)
    pcall(c.common.BlzSetSpecialEffectPosition, e, m.x, m.y, m.z)
    pcall(c.common.BlzSetSpecialEffectYaw, e, m.yaw or 0.0)
  end
  local function aim(m)
    local u = m.units[2]
    if (m.homing or not m.aimed) and alive(u) then
      local c = C()
      m.tx, m.ty, m.tz = c.common.GetUnitX(u), c.common.GetUnitY(u), unit_z(u, 50.0)
      m.aimed = true
    end
  end

  local function step(m)
    local dx, dy = m.tx - m.x, m.ty - m.y
    local d = math.sqrt(dx * dx + dy * dy)
    local s = m.speed * DT
    local arrived = d <= s
    if arrived then m.x, m.y = m.tx, m.ty
    else m.x, m.y = m.x + dx / d * s, m.y + dy / d * s end
    if d > 0 then m.yaw = math.atan(dy, dx) end
    m.done = m.done + math.min(s, d)
    local total = m.done + (arrived and 0 or (d - s))
    local p = total > 0 and m.done / total or 1.0
    m.p = p
    m.z = m.z0 + (m.tz - m.z0) * p + 4 * m.arc * total * p * (1 - p)
    return arrived
  end
  local function segment(m)
    m.z0, m.done = m.z, 0.0
  end
  local function tick(m)
    if m.dead then return end
    if m.kind == 1 or m.kind == 2 then
      aim(m)
      if step(m) then
        local u = m.units[2]
        if alive(u) then hit(m, u) end
        if m.kind == 2 and not m.dead then
          m.count = m.count - 1
          local best, bd = nil, nil
          if m.count > 0 then
            in_range(m, m.x, m.y, m.area, function(v)
              if not m.hit[v] then
                local c = C()
                local ddx, ddy = c.common.GetUnitX(v) - m.x, c.common.GetUnitY(v) - m.y
                local dd = ddx * ddx + ddy * ddy
                if bd == nil or dd < bd then best, bd = v, dd end
              end
            end)
          end
          if best then
            m.units[2] = best
            m.aimed = false
            segment(m)
            aim(m)
            show(m)
            return
          end
        end
        finish(m)
        return
      end
    elseif m.kind == 3 then
      local arrived = step(m)
      local r = m.range + (m.frange - m.range) * (m.p or 0)
      if r > 0 then in_range(m, m.x, m.y, r, function(v) if not m.hit[v] then hit(m, v) end end) end
      if arrived then finish(m) return end
    else
      if step(m) then
        if m.range > 0 then in_range(m, m.x, m.y, m.range, function(v) hit(m, v) end) end
        finish(m)
        return
      end
    end
    show(m)
  end
  local function run_all()
    local n = 0
    for i = 1, #LIST do
      local m = M[ LIST[i] ]
      if m and not m.dead then
        local ok = pcall(tick, m)
        if not ok then pcall(finish, m) end
      end
      if M[ LIST[i] ] then n = n + 1 LIST[n] = LIST[i] end
    end
    for i = #LIST, n + 1, -1 do LIST[i] = nil end
  end
  local function new(kind, u, model, scale, at, dt, dmg, speed, arc)
    local c = C()
    if S.miss_timer == nil then
      S.miss_timer = c.common.CreateTimer()
      c.common.TimerStart(S.miss_timer, DT, true, function() pcall(run_all) end)
    end
    next_id = next_id + 1
    local x, y, z = 0.0, 0.0, 0.0
    if live(u) then x, y, z = num(c.common.GetUnitX(u)), num(c.common.GetUnitY(u)), unit_z(u, 60.0) end
    local m = { id = next_id, kind = kind, units = { [1] = u }, ints = {}, reals = {}, strs = {}, hit = {},
      x = x, y = y, z = z, z0 = z, tx = x, ty = y, tz = z, done = 0.0, p = 0.0, at = at, dt = dt, dmg = num(dmg),
      speed = math.max(num(speed), 1.0), arc = num(arc), flags = 0, visible = true, model = model or '',
      owner = live(u) and c.common.GetOwningPlayer(u) or nil }
    if m.model ~= '' then
      local ok, e = pcall(c.common.AddSpecialEffect, m.model, x, y)
      if ok and live(e) then
        m.eff = e
        pcall(c.common.BlzSetSpecialEffectScale, e, num(scale) > 0 and num(scale) or 1.0)
        pcall(c.common.BlzSetSpecialEffectZ, e, z)
      end
    end
    M[m.id] = m
    LIST[#LIST + 1] = m.id
    return m
  end
  N.XMMissileCreateTarget = function(u, target, model, scale, at, dt, homing, damage, speed, arc)
    local m = new(1, u, model, scale, at, dt, damage, speed, arc)
    m.units[2], m.homing = target, homing == true
    aim(m)
    return m.id
  end
  N.XMMissileCreateBounce = function(u, target, model, scale, at, dt, count, area, damage, speed, arc)
    local m = new(2, u, model, scale, at, dt, damage, speed, arc)
    m.units[2], m.homing, m.count, m.area = target, true, math.max(int(count), 1), num(area)
    aim(m)
    return m.id
  end
  N.XMMissileCreateLine = function(u, x, y, z, model, scale, at, dt, damage, range, frange, speed)
    local m = new(3, u, model, scale, at, dt, damage, speed, 0.0)
    m.tx, m.ty, m.tz, m.z, m.z0 = num(x), num(y), num(z), num(z), num(z)
    m.range, m.frange = num(range), num(frange)
    return m.id
  end
  N.XMMissileCreateArtillery = function(u, x, y, z, model, scale, at, dt, damage, range, speed, arc)
    local m = new(4, u, model, scale, at, dt, damage, speed, arc)
    m.tx, m.ty, m.tz, m.range = num(x), num(y), num(z), num(range)
    return m.id
  end
  N.XMGetTriggerMissile = function() return math.tointeger(cur_missile[#cur_missile] or 0) or 0 end
  N.XMTriggerRegisterMissileEventTrg = function(trig, t)
    t = int(t)
    S.miss_trg[t] = S.miss_trg[t] or {}
    add_trig(S.miss_trg[t], trig)
  end
  N.XMMissileSetPos = function(id, x, y, z)
    local m = M[id]
    if m == nil then return end
    m.x, m.y, m.z = num(x), num(y), num(z)
    m.z0, m.done = m.z, 0.0
    show(m)
  end
  N.XMMissileVisible = function(id, b)
    local m = M[id]
    if m == nil then return end
    m.visible = b == true
    if live(m.eff) then pcall(C().common.BlzSetSpecialEffectAlpha, S.eff_of(m.eff), m.visible and 255 or 0) end
  end
  N.XMMissileSetSplashTargs = function(id, v) local m = M[id] if m then m.flags = int(v) & 0xffffffff end end
  N.XMMissileSetUnit = function(id, t, u)
    local m = M[id]
    if m == nil then return end
    t = int(t)
    m.units[t] = live(u) and u or nil
    if t == 2 then m.aimed = false end
  end
  N.XMMissileGetUnit = function(id, t) local m = M[id] return m and m.units[int(t)] or nil end
  N.XMMissileSetInt = function(id, t, v) local m = M[id] if m then m.ints[int(t)] = int(v) end end
  N.XMMissileGetInt = function(id, t) local m = M[id] return m and (m.ints[int(t)] or 0) or 0 end
  local ANIM = { birth = 0, death = 1, decay = 2, dissipate = 3, stand = 4, walk = 5, attack = 6, morph = 7, sleep = 8,
    spell = 9, portrait = 10 }
  N.XMMissileSetReal = function(id, t, v)
    local m = M[id]
    if m == nil then return end
    t, v = int(t), num(v)
    m.reals[t] = v
    if t == 17 and live(m.eff) then pcall(C().common.BlzSetSpecialEffectTimeScale, S.eff_of(m.eff), v) end
  end
  N.XMMissileGetReal = function(id, t) local m = M[id] return m and num(m.reals[int(t)] or 0.0) or 0.0 end
  N.XMMissileSetStr = function(id, t, s)
    local m = M[id]
    if m == nil then return end
    t = int(t)
    m.strs[t] = s or ''
    local a = ANIM[string.lower(tostring(s or ''))]
    if t == 22 and a and live(m.eff) then pcall(C().common.BlzPlaySpecialEffect, S.eff_of(m.eff), a) end
  end
  N.XMMissileGetStr = function(id, t) local m = M[id] return m and (m.strs[int(t)] or '') or '' end
  N.SaveXMMissileHandle = function(ht, a, b, v) C().common.SaveInteger(ht, a, b, int(v)) return true end
  N.LoadXMMissileHandle = function(ht, a, b) return C().common.LoadInteger(ht, a, b) end
end
