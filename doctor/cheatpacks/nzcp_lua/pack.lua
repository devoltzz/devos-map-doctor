do
    local PREFIX = "-"
    local activator = "easymode"
    local ARROWS = "UUDDLR"
    local AUTO_NAME = "nuzamacuxe"
    local BUDGET = 300

    local PLAYER, FIRST, EACH, GUARD = 0, 1, 2, 3
    local COLORS = "ff03030041ff1ce6b9540081fffc00fe8a0e20c000de5bb09596977ebff11062464e2a049b00000000c300eaffbe00feebcd87f8a48bdcb9ebbfff80282828ebf0ff00781ea46f33999999"
    local DIGITS = { string.byte("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz", 1, -1) }
    local PREFIXES = "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{}~"
    local ARROW_NAMES = { "Left", "Right", "Up", "Down" }
    local CHEATS = { "crit", "mult", "hpdmg", "lifesteal", "manasteal", "block", "reflect", "amp" }

    local players, units, cmds, names, cmd = {}, {}, {}, {}, {}
    local group, dmgTrig, orderTrigs, tpTrig, zoomTimer
    local dealing = false

    local function msg(pid, text, duration)
        DisplayTimedTextToPlayer(Player(pid), 0., 0., duration or 12.5, text)
    end

    local function lower(s)
        return StringCase(s, false)
    end

    local function fresh()
        return { level = 0, bind = {}, rate = {}, last = {} }
    end

    local function prefix(pid)
        return players[pid].prefix or PREFIX
    end

    local function color(pid)
        local c = GetHandleId(GetPlayerColor(Player(pid))) * 6
        return "|cff" .. COLORS:sub(c + 1, c + 6) .. GetPlayerName(Player(pid)) .. "|r"
    end

    local function data(u)
        local d = units[u]
        if not d then
            d = {}
            units[u] = d
        end
        return d
    end

    local function signed(v)
        if v >= 0x80000000 then
            return v - 0x100000000
        end
        return v
    end

    local function id2s(id)
        local s = string.pack(">I4", id & 0xFFFFFFFF)
        if s:find("[^!-{}~]") then
            return string.format("0x%08X", id & 0xFFFFFFFF)
        end
        return s
    end

    local function s2id(s)
        s = s or ""
        local dec = s:match("^#(%-?%d+)$")
        if dec then
            local v = math.tointeger(tonumber(dec))
            if v and tostring(v) == dec and v >= -0x80000000 and v < 0x80000000 then
                return v
            end
            return 0
        end
        local hex = s:match("^0[xX](%x%x%x%x%x%x%x%x)$") or s:match("^(%x%x%x%x%x%x%x%x)$")
        if hex then
            return signed(tonumber(hex, 16))
        end
        if #s == 4 and not s:find("[^!-~]") then
            return string.unpack(">i4", s)
        end
        return 0
    end

    local AVUL, HERO = s2id("Avul"), s2id("HERO")

    local function plain(s)
        return (s:gsub("|[cC]........", ""):gsub("|[rRnN]", ""))
    end

    local function has(text, find)
        return lower(plain(text)):find(find, 1, true) ~= nil
    end

    local function spawn(pid, fn)
        local co, t = coroutine.create(fn), CreateTimer()
        local function step()
            local ok, wait = coroutine.resume(co)
            if not ok then
                msg(pid, "|cFFff1a1aNZCP error|r: " .. tostring(wait))
            end
            if coroutine.status(co) == "dead" then
                DestroyTimer(t)
            else
                TimerStart(t, wait or 0., false, step)
            end
        end
        step()
    end

    local Ctx = {}
    Ctx.__index = Ctx

    function Ctx:say(text)
        if self.first then
            msg(self.pid, text)
        end
    end

    function Ctx:usage()
        self:say("Usage: |cFF00aaff" .. prefix(self.pid) .. self.name .. " " .. cmds[self.name].usage .. "|r")
    end

    function Ctx:switch(label, was, on)
        if was == on then
            self:say(label .. (on and " is |cFF00cc66already enabled|r." or " is |cFFff1a1aalready disabled|r."))
        else
            self:say(label .. (on and " has been |cFF00cc66enabled|r." or " has been |cFFff1a1adisabled|r."))
        end
    end

    function Ctx:int(i)
        return S2I(self[i] or "")
    end

    function Ctx:real(i)
        return S2R(self[i] or "")
    end

    function Ctx:low(i)
        return lower(self[i] or "")
    end

    function Ctx:off()
        return lower(self.rest) == "off"
    end

    function Ctx:player(i)
        local v = self:int(i)
        if v >= 1 and v <= bj_MAX_PLAYER_SLOTS then
            return v - 1
        end
    end

    local function stop(d, key)
        local t = d and d[key]
        if t then
            PauseTimer(t)
            DestroyTimer(t)
            d[key] = nil
        end
    end

    local function forget(u)
        local d = units[u]
        if d then
            stop(d, "regen")
            stop(d, "nocd")
            units[u] = nil
        end
    end

    local function unitTimer(u, key, period, tick)
        local d = data(u)
        if d[key] then
            return
        end
        d[key] = CreateTimer()
        TimerStart(d[key], period, true, function()
            if GetUnitTypeId(u) == 0 then
                forget(u)
            else
                tick(u, d)
            end
        end)
    end

    local function regenOn(u, v)
        data(u).regenValue = v
        unitTimer(u, "regen", .25, function(_, d)
            if not IsUnitType(u, UNIT_TYPE_DEAD) then
                SetWidgetLife(u, GetWidgetLife(u) + d.regenValue)
                SetUnitState(u, UNIT_STATE_MANA, GetUnitState(u, UNIT_STATE_MANA) + d.regenValue)
            end
        end)
    end

    local function nocdOn(u)
        unitTimer(u, "nocd", .2, function() UnitResetCooldown(u) end)
    end

    local function float(u, text, angle)
        local tt = CreateTextTag()
        SetTextTagText(tt, text, .023)
        SetTextTagPos(tt, GetUnitX(u), GetUnitY(u), 50.)
        SetTextTagVelocity(tt, .0555 * math.cos(math.rad(GetRandomReal(1., 180.))), .0555 * math.sin(math.rad(angle)))
        SetTextTagPermanent(tt, false)
        SetTextTagLifespan(tt, 2.)
        SetTextTagFadepoint(tt, .65)
        SetTextTagVisibility(tt, GetLocalPlayer() == GetOwningPlayer(u))
    end

    local function deal(src, tgt, amount)
        dealing = true
        UnitDamageTarget(src, tgt, amount, true, false, ATTACK_TYPE_CHAOS, DAMAGE_TYPE_UNIVERSAL, WEAPON_TYPE_WHOKNOWS)
        dealing = false
    end

    local function steal(src, tgt, total, life, mana)
        if IsUnitType(src, UNIT_TYPE_DEAD) then
            return
        end
        if (life or 0) > 0 then
            local v = total * life / 100.
            SetWidgetLife(src, GetWidgetLife(src) + v)
            float(src, "|cFF00ff00+" .. R2I(v), 308.)
        end
        if (mana or 0) > 0 and GetUnitState(tgt, UNIT_STATE_MANA) >= 1. and GetUnitState(src, UNIT_STATE_MAX_MANA) >= 1. then
            local v = math.min(total * mana / 100., GetUnitState(tgt, UNIT_STATE_MANA))
            SetUnitState(src, UNIT_STATE_MANA, GetUnitState(src, UNIT_STATE_MANA) + v)
            SetUnitState(tgt, UNIT_STATE_MANA, GetUnitState(tgt, UNIT_STATE_MANA) - v)
            float(src, "|cFF95b7e9+" .. R2I(v), 130.)
        end
    end

    local isAttack = BlzGetEventIsAttack or function()
        return BlzGetEventDamageType() == DAMAGE_TYPE_NORMAL and BlzGetEventAttackType() ~= ATTACK_TYPE_NORMAL
    end

    local function onDamage()
        local dmg = GetEventDamage()
        if dealing or dmg <= 0. then
            return
        end
        local src, tgt = GetEventDamageSource(), GetTriggerUnit()
        local a, d = src and units[src], units[tgt]
        local attack = a and isAttack()
        local total = dmg
        if attack then
            if (a.crit or 0) > 0 and GetRandomInt(1, 100) <= a.crit then
                total = dmg * a.mult
                float(src, "|cFFff0000" .. R2I(total) .. "!|r", 90.)
            elseif (a.hpdmg or 0) > 0 then
                total = dmg + GetUnitState(tgt, UNIT_STATE_MAX_LIFE) * a.hpdmg / 100.
                float(src, "|cFFff1a75" .. R2I(total) .. "!|r", 90.)
            end
        elseif a and (a.amp or 0) > 0 then
            total = dmg * (1. + a.amp / 100.)
            float(src, "|cFF6699ff" .. R2I(total) .. "|r", 90.)
        end
        local block = math.max(math.min(d and d.block or 0, 100), 0)
        local hit = total * (100 - block) / 100.
        if hit ~= dmg then
            BlzSetEventDamage(hit)
        end
        if attack and hit > 0. then
            steal(src, tgt, hit, a.lifesteal, a.manasteal)
        end
        if d and (d.reflect or 0) > 0 and src and block < 100 then
            local back = total * d.reflect / 100. * (100 - math.max(math.min(a and a.block or 0, 100), 0)) / 100.
            if back > 0. then
                deal(tgt, src, back)
            end
        end
    end

    local function dmgOn()
        EnableTrigger(dmgTrig)
    end

    local function idAt(k, total)
        local head = 73
        if total > 238328 then
            head = DIGITS[k // 238328 + 1]
            k = k % 238328
        end
        return head * 16777216 + DIGITS[k // 3844 + 1] * 65536 + DIGITS[k // 62 % 62 + 1] * 256 + DIGITS[k % 62 + 1]
    end

    local function searchTest(pid, s, id)
        local name, code = GetObjectName(id), id2s(id)
        if has(name, s.query) or (#s.query <= 4 and has(code, s.query)) then
            s.hits[#s.hits + 1] = "Item ID: " .. code .. " Name: " .. name
            if #s.hits <= 15 then
                msg(pid, "|cFF00aaffItem ID:|r " .. code .. " |cFF00aaffName:|r " .. name)
            end
        end
    end

    local function searchFinish(pid, s)
        local file = "[CP] ItemsExport\\Items [" .. s.file .. "].txt"
        if GetLocalPlayer() == Player(pid) then
            PreloadGenClear()
            PreloadGenStart()
            for _, line in ipairs(s.hits) do
                Preload(line)
            end
            PreloadGenEnd(file)
        end
        msg(pid, "|cFF00cc66" .. #s.hits .. "|r item(s) found in |cFFffcc00" .. string.format("%.1f", s.ticks * .03) .. "s|r. Full list: Warcraft III/CustomMapData/[CP] ItemsExport/Items |cFFe6b800[" .. s.file .. "]|r.txt")
    end

    local function search(pid, term, total)
        local p = players[pid]
        if p.search then
            return msg(pid, "A search is already running. Type |cFF00aaff" .. prefix(pid) .. "sitem off|r to cancel.")
        elseif #term < 2 then
            return msg(pid, "Type at least |cFFffcc002|r characters.")
        end
        local s = { term = term, file = term:gsub('[\\/:*?"<>|]', "_"), query = lower(term), hits = {}, ticks = 0 }
        local budget = total > 238328 and BUDGET * 10 or BUDGET
        p.search = s
        msg(pid, "Searching items for |cFFe6b800[" .. term .. "]|r... The game may |cFFff1a1astutter|r a little while searching.")
        if total > 238328 then
            msg(pid, "|cFFff9900Deep search|r: all IDs, takes |cFFffcc00~2-3 minutes|r with some lag. Type |cFF00aaff" .. prefix(pid) .. "sitem off|r to cancel.")
        end
        spawn(pid, function()
            local cost, found, mark = 0, 0, total // 10
            local function pause()
                s.ticks = s.ticks + 1
                coroutine.yield(.03)
            end
            pause()
            for k = 0, total - 1 do
                if p.search ~= s then
                    return
                end
                local id = idAt(k, total)
                local it = CreateItem(id, 0., 0.)
                cost = cost + 1
                if it then
                    RemoveItem(it)
                    cost, found = cost + 100, found + 1
                    searchTest(pid, s, id)
                end
                if (cost >= budget or found >= 3) and k + 1 < total then
                    if k + 1 >= mark then
                        mark = mark + total // 10
                        msg(pid, "Searching... |cFFffcc00" .. (k + 1) * 100 // total .. "%|r")
                    end
                    pause()
                    cost, found = 0, 0
                end
            end
            if p.search == s then
                p.search = nil
                searchFinish(pid, s)
            end
        end)
    end

    local function activate(pid)
        local p = players[pid]
        if p.on then
            return msg(pid, "You already have |cFF00cc66activated|r |cFF3366ffNZCP|r.")
        end
        for i = 0, bj_MAX_PLAYER_SLOTS - 1 do
            local o = players[i]
            if o.level > 0 then
                o.level = o.level + 1
                msg(i, color(pid) .. " has |cFF00cc66activated|r |cFF3366ffNZCP|r. Your cheater level has changed to: |cFF0099ff" .. o.level .. "|r.")
            end
        end
        p.on, p.level = true, 1
        msg(pid, "|cFF038CFCNUZAMACUXE|r's CHEAT PACK has been |cFF00cc66activated|r! Type |cFF00aaff" .. prefix(pid) .. "cmds|r to list the commands.")
    end

    local function nameActivate(name)
        for i = 0, bj_MAX_PLAYER_SLOTS - 1 do
            if GetPlayerName(Player(i)) == name then
                players[i].on, players[i].level = true, 1
                msg(i, "|cFFff9900Welcome|r, " .. color(i) .. "! |cFF3366ffNZCP|r has been |cFF00cc66auto activated|r.")
            end
        end
    end

    local function mapHackOff(pid)
        local fog = players[pid].fog
        if fog then
            FogModifierStop(fog)
            DestroyFogModifier(fog)
            players[pid].fog = nil
        end
    end

    local function zoomOff(pid)
        if players[pid].zoom then
            players[pid].zoom = nil
            if GetLocalPlayer() == Player(pid) then
                SetCameraField(CAMERA_FIELD_TARGET_DISTANCE, 1650., .5)
                SetCameraField(CAMERA_FIELD_FARZ, 5000., .5)
            end
        end
    end

    local function zoomTick()
        local d = players[GetPlayerId(GetLocalPlayer())].zoom
        if d then
            SetCameraField(CAMERA_FIELD_TARGET_DISTANCE, d, .5)
            SetCameraField(CAMERA_FIELD_FARZ, d + 3000., .5)
        end
    end

    local function addState(pid, res, v)
        local total = GetPlayerState(Player(pid), res.state) + v
        players[pid].last[res.key] = total
        SetPlayerState(Player(pid), res.state, total)
    end

    local STATS = {
        hp = { "Life", function(u, v) SetWidgetLife(u, v) end, function(u) return R2I(GetWidgetLife(u)) end },
        mp = { "Mana", function(u, v) SetUnitState(u, UNIT_STATE_MANA, v) end, function(u) return R2I(GetUnitState(u, UNIT_STATE_MANA)) end },
        ms = { "Movement speed", SetUnitMoveSpeed, function(u) return R2I(GetUnitMoveSpeed(u)) end },
        str = { "Strength", function(u, v) SetHeroStr(u, v, true) end, function(u) return GetHeroStr(u, false) end, true },
        agi = { "Agility", function(u, v) SetHeroAgi(u, v, true) end, function(u) return GetHeroAgi(u, false) end, true },
        int = { "Intelligence", function(u, v) SetHeroInt(u, v, true) end, function(u) return GetHeroInt(u, false) end, true },
        sp = { "Skill points", UnitModifySkillPoints, GetHeroSkillPoints, true },
        xp = { "Experience", function(u, v) SetHeroXP(u, v, false) end, GetHeroXP, true },
    }

    local GOLD = { key = "gold", state = PLAYER_STATE_RESOURCE_GOLD, title = "|cFFffff00Gold|r", label = "|cFFffff00Gold Rate|r", gave = "|cFFffff00gold|r", given = "|cFFffff00gold|r" }
    local LUMBER = { key = "lumber", state = PLAYER_STATE_RESOURCE_LUMBER, title = "|cFF00cc66Lumber|r", label = "|cFF009933Lumber Rate|r", gave = "|cFF00cc66lumber|r", given = "|cFF009933lumber|r" }

    local TP_KEYS = {
        m = { 851986, "Move" },
        p = { 851990, "Patrol" },
        a = { 851983, "Attack" },
    }

    function cmd.lvl(c)
        local u, v = c.unit, c:int(1)
        if not IsUnitType(u, UNIT_TYPE_HERO) then
            return c:say("|cFFff9900Level|r only works on |cFFff1a1aheroes|r.")
        end
        if v > GetHeroLevel(u) then
            SetHeroLevel(u, v, false)
        else
            UnitStripHeroLevel(u, GetHeroLevel(u) - v)
        end
        c:say("|cFFff9900Level|r: |cFFffcc00" .. GetHeroLevel(u) .. "|r")
    end

    function cmd.stat(c)
        local label, set, get, heroOnly = table.unpack(c.data)
        if heroOnly and not IsUnitType(c.unit, UNIT_TYPE_HERO) then
            return c:say("|cFFff9900" .. c.name .. "|r only works on |cFFff1a1aheroes|r.")
        end
        set(c.unit, c:int(1))
        c:say("|cFFff9900" .. label .. "|r: |cFFffcc00" .. get(c.unit) .. "|r")
    end

    function cmd.owner(c)
        local p = c:player(1)
        if not p then
            return c:usage()
        end
        SetUnitOwner(c.unit, Player(p), true)
        c:say("|cFFff9900Owner|r changed to " .. color(p) .. ".")
    end

    function cmd.charge(c)
        local it = UnitItemInSlot(c.unit, c:int(1) - 1)
        if not it then
            return c:say("There's |cFFff9900no item|r in slot |cFF00aaff" .. c[1] .. "|r. Make sure to type the |cFF009933correct|r slot.")
        end
        SetItemCharges(it, c:int(2))
        c:say("|cFFff9900Charges|r in slot |cFF00aaff" .. c[1] .. "|r: |cFFffcc00" .. GetItemCharges(it) .. "|r")
    end

    function cmd.invul(c)
        local on = c.name == "invul"
        c:switch("|cFFff9900Invulnerability|r", GetUnitAbilityLevel(c.unit, AVUL) > 0, on)
        SetUnitInvulnerable(c.unit, on)
    end

    function cmd.kill(c)
        local u = c.unit
        if c.name == "kill" then
            c:say("|cFFff9900" .. GetUnitName(u) .. "|r has been |cFFff1a1akilled|r.")
            KillUnit(u)
        else
            c:say("|cFFff9900" .. GetUnitName(u) .. "|r has been |cFFff1a1aremoved|r.")
            forget(u)
            RemoveUnit(u)
        end
    end

    local function abilityList(u)
        local list = {}
        if BlzGetAbilityId then
            local i, a = 0, BlzGetUnitAbilityByIndex(u, 0)
            while a do
                list[#list + 1] = BlzGetAbilityId(a)
                i = i + 1
                a = BlzGetUnitAbilityByIndex(u, i)
            end
            table.sort(list)
            return list
        end
        for r, d1 in ipairs(DIGITS) do
            local row = 65 * 16777216 + d1 * 65536
            for _, d2 in ipairs(DIGITS) do
                for _, d3 in ipairs(DIGITS) do
                    if GetUnitAbilityLevel(u, row + d2 * 256 + d3) > 0 then
                        list[#list + 1] = row + d2 * 256 + d3
                    end
                end
            end
            if r % 4 == 0 then
                coroutine.yield()
            end
        end
        return list
    end

    local function copyAbilities(u, c, list)
        local hero = IsUnitType(c, UNIT_TYPE_HERO)
        for i = #list, 1, -1 do
            local id = list[i]
            local lvl, cur = GetUnitAbilityLevel(u, id), GetUnitAbilityLevel(c, id)
            while hero and cur < lvl do
                UnitModifySkillPoints(c, 1)
                SelectHeroSkill(c, id)
                if GetUnitAbilityLevel(c, id) == cur then
                    UnitModifySkillPoints(c, -1)
                    break
                end
                cur = GetUnitAbilityLevel(c, id)
            end
            if cur == 0 then
                UnitAddAbility(c, id)
            end
            if cur < lvl then
                SetUnitAbilityLevel(c, id, lvl)
            end
        end
        if hero then
            UnitModifySkillPoints(c, GetHeroSkillPoints(u) - GetHeroSkillPoints(c))
        end
    end

    local function copyUnit(u, abilities)
        local c = CreateUnit(GetOwningPlayer(u), GetUnitTypeId(u), GetUnitX(u), GetUnitY(u), GetUnitFacing(u))
        local d = units[u]
        if IsUnitType(u, UNIT_TYPE_HERO) then
            SetHeroXP(c, GetHeroXP(u), false)
            SetHeroStr(c, GetHeroStr(u, false), true)
            SetHeroAgi(c, GetHeroAgi(u, false), true)
            SetHeroInt(c, GetHeroInt(u, false), true)
            BlzSetHeroProperName(c, GetHeroProperName(u))
        else
            BlzSetUnitName(c, GetUnitName(u))
        end
        for slot = 0, 5 do
            local it = UnitItemInSlot(u, slot)
            if it and UnitAddItemToSlotById(c, GetItemTypeId(it), slot) then
                SetItemCharges(UnitItemInSlot(c, slot), GetItemCharges(it))
            end
        end
        if abilities then
            copyAbilities(u, c, abilities)
        elseif GetUnitAbilityLevel(u, AVUL) > 0 then
            SetUnitInvulnerable(c, true)
        end
        if d then
            local e = data(c)
            for _, key in ipairs(CHEATS) do
                e[key] = d[key]
            end
            if d.regen then
                regenOn(c, d.regenValue)
            end
            if d.nocd then
                nocdOn(c)
            end
        end
        BlzSetUnitBaseDamage(c, BlzGetUnitBaseDamage(u, 0), 0)
        BlzSetUnitDiceNumber(c, BlzGetUnitDiceNumber(u, 0), 0)
        BlzSetUnitDiceSides(c, BlzGetUnitDiceSides(u, 0), 0)
        BlzSetUnitAttackCooldown(c, BlzGetUnitAttackCooldown(u, 0), 0)
        if BlzGetUnitMaxHP(c) ~= BlzGetUnitMaxHP(u) then
            BlzSetUnitMaxHP(c, BlzGetUnitMaxHP(u))
        end
        if BlzGetUnitMaxMana(c) ~= BlzGetUnitMaxMana(u) then
            BlzSetUnitMaxMana(c, BlzGetUnitMaxMana(u))
        end
        SetUnitMoveSpeed(c, GetUnitMoveSpeed(u))
        SetUnitState(c, UNIT_STATE_LIFE, GetUnitState(u, UNIT_STATE_LIFE))
        SetUnitState(c, UNIT_STATE_MANA, GetUnitState(u, UNIT_STATE_MANA))
    end

    function cmd.copy(c)
        local u, n = c.unit, c:int(1)
        if n <= 0 then
            return c:usage()
        end
        local function copies(abilities)
            if GetUnitTypeId(u) ~= 0 then
                for _ = 1, n do
                    copyUnit(u, abilities)
                end
                c:say("|cFFff9900" .. GetUnitName(u) .. "|r copied |cFFffcc00" .. n .. "|r time(s).")
            end
        end
        if c:low(2) ~= "full" then
            return copies(nil)
        end
        if not BlzGetAbilityId then
            c:say("|cFFff9900Full copy|r: scanning abilities, it takes |cFFffcc00about a second|r.")
        end
        spawn(c.pid, function()
            copies(abilityList(u))
        end)
    end

    function cmd.learn(c)
        local u, id = c.unit, s2id(c[1])
        if id == 0 then
            return c:usage()
        end
        local name = "|cFFff9900Ability|r: [|cFF00cc66" .. GetObjectName(id) .. "|r] has been "
        if c.name == "unlearn" then
            UnitRemoveAbility(u, id)
            c:say(name .. "|cFFff1a1aremoved|r.")
        elseif GetUnitAbilityLevel(u, id) == 0 then
            UnitAddAbility(u, id)
            c:say(name .. "|cFF00cc66added|r.")
        else
            IncUnitAbilityLevel(u, id)
            c:say(name .. "|cFF00cc66leveled up!|r")
        end
    end

    function cmd.rg(c)
        local u, v = c.unit, c:real(1)
        if v == 0. then
            local d = units[u]
            c:switch("|cFFff9900Regeneration buff|r", d ~= nil and d.regen ~= nil, false)
            stop(d, "regen")
        else
            regenOn(u, v)
            c:say("|cFFff9900[EXTRA]|r |cFF00f600HP|r & |cFF95b7e9MP|r Regen: |cFFff9900" .. string.format("%.1f", v) .. "|r/.25s")
        end
    end

    function cmd.nc(c)
        local d = units[c.unit]
        c:switch("|cFFff9900No cooldown|r", d ~= nil and d.nocd ~= nil, not c:off())
        if c:off() then
            stop(d, "nocd")
        else
            nocdOn(c.unit)
        end
    end

    function cmd.pause(c)
        c:switch("|cFFff9900Pause|r", IsUnitPaused(c.unit), not c:off())
        PauseUnit(c.unit, not c:off())
    end

    local function unitPct(c, key, label)
        local v = c:int(1)
        if v < 0 then
            return c:usage()
        end
        local d = data(c.unit)
        dmgOn()
        if v == 0 then
            c:switch("|cFFff9900" .. label .. "|r", d[key] ~= nil, false)
            d[key] = nil
        else
            d[key] = v
            c:say(label .. ": |cFFffcc00" .. v .. "%|r")
        end
    end

    function cmd.dmgc(c)
        local d = data(c.unit)
        dmgOn()
        if d.hpdmg then
            c:say("In order to use Critical Strike Chance and Damage Multiplier, you must |cFFff1a1adisable|r the |cFFff9900Maximum HP Damage|r.")
        elseif c:int(1) == 0 then
            c:switch("|cFFff9900Critical Strike|r", d.crit ~= nil, false)
            d.crit, d.mult = nil, nil
        elseif c:int(1) > 0 and c:real(2) > 1. then
            d.crit, d.mult = c:int(1), c:real(2)
            c:say("Critical Strike Chance: |cFFffcc00" .. c[1] .. "%|r  Damage Multiplier: |cFFffcc00" .. c[2] .. "x|r")
        else
            c:usage()
        end
    end

    function cmd.dmghp(c)
        if data(c.unit).crit then
            return c:say("In order to use Maximum HP Damage, you must |cFFff1a1adisable|r the |cFFff9900Critical Strike Chance|r.")
        end
        unitPct(c, "hpdmg", "Maximum HP Damage")
    end

    function cmd.pct(c)
        unitPct(c, table.unpack(c.data))
    end

    function cmd.status(c)
        local d = units[c.unit] or {}
        msg(c.pid, "|cFFff9933Current Selected Unit Status|r"
            .. "\nCritical: |cFFffcc00" .. (d.crit or 0) .. "%|r x |cFFffcc00" .. string.format("%.1f", d.mult or 0) .. "|r"
            .. "\nMaximum HP Damage: |cFFffcc00" .. (d.hpdmg or 0) .. "%|r"
            .. "\nSpell damage: |cFF6699ff+" .. (d.amp or 0) .. "%|r"
            .. "\nLife steal: |cFF00ff00" .. (d.lifesteal or 0) .. "%|r   Mana steal: |cFF95b7e9" .. (d.manasteal or 0) .. "%|r"
            .. "\nBlock: |cFFffcc00" .. (d.block or 0) .. "%|r   Reflect: |cFFffcc00" .. (d.reflect or 0) .. "%|r")
    end

    function cmd.unitid(c)
        local id = GetUnitTypeId(c.unit)
        msg(c.pid, "|cFF00aaffUnit ID:|r " .. id2s(id) .. "  |cFF00aaffName:|r " .. GetObjectName(id))
    end

    function cmd.itemid(c)
        local slot = c:int(1)
        if slot < 1 or slot > 6 then
            return c:usage()
        end
        local id = GetItemTypeId(UnitItemInSlot(c.unit, slot - 1))
        if id == 0 then
            msg(c.pid, "There's |cFFff9900no item|r in slot |cFF00aaff" .. slot .. "|r.")
        else
            msg(c.pid, "|cFF00aaffItem ID:|r " .. id2s(id) .. "  |cFF00aaffName:|r " .. GetObjectName(id))
        end
    end

    function cmd.islot(c)
        local u, slot, id = c.unit, c:int(1), s2id(c[2])
        if slot < 1 or slot > 6 or id == 0 then
            c:usage()
        elseif slot > UnitInventorySize(u) then
            c:say("This unit has only |cFF00aaff" .. UnitInventorySize(u) .. "|r inventory slots.")
        elseif UnitItemInSlot(u, slot - 1) then
            c:say("Slot |cFF00aaff" .. slot .. "|r is |cFFff1a1aoccupied|r.")
        elseif UnitAddItemToSlotById(u, id, slot - 1) then
            c:say("[|cFF00cc66" .. GetObjectName(id) .. "|r] has been |cFF00cc66added|r to slot |cFF00aaff" .. slot .. "|r.")
        else
            c:say("There's |cFFff1a1ano item|r with ID [|cFF00aaff" .. c[2] .. "|r].")
        end
    end

    function cmd.create(c)
        local u, id = c.unit, s2id(c[1])
        if id == 0 then
            c:usage()
        elseif not CreateItem(id, GetUnitX(u), GetUnitY(u)) and not CreateUnit(Player(c.pid), id, GetUnitX(u), GetUnitY(u), 270.) then
            msg(c.pid, "There's |cFFff1a1ano item or unit|r with ID [|cFF00aaff" .. c[1] .. "|r].")
        else
            msg(c.pid, "|cFFff9900Object|r with ID: [|cFF00cc66" .. id2s(id) .. "|r] has been |cFF00cc66spawned|r.")
        end
    end

    function cmd.ritem(c)
        local n = math.min(c:int(1), 99)
        if n <= 0 then
            return c:usage()
        end
        for _ = 1, n do
            CreateItem(ChooseRandomItemEx(ITEM_TYPE_ANY, -1), GetUnitX(c.unit), GetUnitY(c.unit))
        end
        msg(c.pid, "|cFFffcc00" .. n .. "|r random item(s) |cFF00cc66created|r.")
    end

    function cmd.food(c)
        local a = c:low(1)
        if a == "use" or a == "nouse" then
            if not c.unit then
                return msg(c.pid, "|cFFff1a1aSelect a unit|r first.")
            end
            SetUnitUseFood(c.unit, a == "use")
            msg(c.pid, "|cFFff9900" .. GetUnitName(c.unit) .. "|r food usage: |cFFffcc00" .. a .. "|r")
        elseif c:int(1) ~= 0 then
            SetPlayerState(Player(c.pid), PLAYER_STATE_FOOD_CAP_CEILING, c:int(1))
            SetPlayerState(Player(c.pid), PLAYER_STATE_RESOURCE_FOOD_CAP, c:int(1))
            msg(c.pid, "|cFFb33c00Food|r cap: |cFFffcc00" .. GetPlayerState(Player(c.pid), PLAYER_STATE_RESOURCE_FOOD_CAP) .. "|r")
        else
            c:usage()
        end
    end

    function cmd.resource(c)
        local res = c.data
        addState(c.pid, res, c:int(1))
        msg(c.pid, res.title .. ": |cFFffcc00" .. GetPlayerState(Player(c.pid), res.state) .. "|r")
    end

    function cmd.give(c)
        local p, v = c:player(1), c:int(2)
        if not p then
            c:usage()
        elseif c.name == "givef" then
            SetPlayerState(Player(p), PLAYER_STATE_FOOD_CAP_CEILING, v)
            SetPlayerState(Player(p), PLAYER_STATE_RESOURCE_FOOD_CAP, v)
            msg(c.pid, "|cFFb33c00Food|r cap of " .. color(p) .. " set to " .. v .. ".")
        else
            addState(p, c.data, v)
            msg(c.pid, "You gave " .. v .. " " .. c.data.gave .. " to " .. color(p) .. ".")
        end
    end

    function cmd.rate(c)
        local p, res, v = players[c.pid], c.data, c:int(1)
        if p.rate[res.key] then
            if v == 0 then
                p.rate[res.key] = nil
                msg(c.pid, res.label .. " has been |cFFff1a1adisabled|r.")
            else
                p.rate[res.key] = v
                msg(c.pid, res.label .. " has been |cFFe68a00changed|r to |cFFffff00" .. v .. "%|r.")
            end
        elseif v > 0 then
            p.rate[res.key] = v
            p.last[res.key] = GetPlayerState(Player(c.pid), res.state)
            msg(c.pid, res.label .. " has been |cFFe68a00set|r to |cFFffff00" .. v .. "%|r.")
        else
            c:usage()
        end
    end

    function cmd.expr(c)
        local p = Player(c.pid)
        local v = math.max(R2I(100. * GetPlayerHandicapXP(p) + .5) + c:int(1), 0)
        SetPlayerHandicapXP(p, v * .01)
        msg(c.pid, "|cFFe600e6Experience Rate|r is now |cFFe600e6" .. v .. "%|r.")
    end

    function cmd.tech(c)
        local p, id = Player(c.pid), s2id(c[1])
        if id == 0 then
            return c:usage()
        end
        local before = GetPlayerTechCount(p, id, true)
        SetPlayerTechResearched(p, id, c.n >= 2 and c:int(2) or before + 1)
        local lvl = GetPlayerTechCount(p, id, true)
        if lvl == before then
            msg(c.pid, "|cFFff9900Upgrade|r [|cFF00cc66" .. GetObjectName(id) .. "|r] |cFFff1a1adidn't change|r (level |cFFffcc00" .. lvl .. "|r): max level reached or not an upgrade ID.")
        else
            msg(c.pid, "|cFFff9900Upgrade|r [|cFF00cc66" .. GetObjectName(id) .. "|r] set to level |cFFffcc00" .. lvl .. "|r.")
        end
    end

    function cmd.kick(c)
        local p = c:player(1)
        if p == c.pid then
            msg(c.pid, "You |cFFff1a1acan't|r kick yourself.")
        elseif not p then
            c:usage()
        elseif players[c.pid].level > players[p].level then
            CustomDefeatBJ(Player(p), "You have been |cFFff1a1akicked|r!")
        else
            msg(c.pid, "You |cFFff1a1acan't|r kick a cheater with the same or a higher level.")
        end
    end

    function cmd.share(c)
        local a, b, on = c:player(1), c:player(2), c.name == "share"
        if not a or not b then
            return c:usage()
        end
        if players[c.pid].level > players[a].level then
            SetPlayerAlliance(Player(a), Player(b), ALLIANCE_SHARED_VISION, on)
            SetPlayerAlliance(Player(a), Player(b), ALLIANCE_SHARED_CONTROL, on)
            SetPlayerAlliance(Player(a), Player(b), ALLIANCE_SHARED_ADVANCED_CONTROL, on)
            msg(c.pid, "You have " .. c.name .. "d " .. color(a) .. " with " .. color(b) .. ".")
        end
    end

    function cmd.ploc(c)
        if GetLocalPlayer() == Player(c.pid) then
            PingMinimapEx(c:real(1), c:real(2), 15., 51, 153, 255, true)
        end
    end

    function cmd.revive(c)
        local p = Player(c.pid)
        local heroes, food = GetPlayerTechMaxAllowed(p, HERO), GetPlayerState(p, PLAYER_STATE_RESOURCE_FOOD_USED)
        local revived, failed = 0, 0
        SetPlayerTechMaxAllowed(p, HERO, -1)
        SetPlayerState(p, PLAYER_STATE_RESOURCE_FOOD_USED, 0)
        GroupEnumUnitsOfPlayer(group, p, nil)
        for i = 0, BlzGroupGetSize(group) - 1 do
            local u = BlzGroupUnitAt(group, i)
            if IsUnitType(u, UNIT_TYPE_HERO) and IsUnitType(u, UNIT_TYPE_DEAD) then
                local kind = GetUnitTypeId(u)
                local limit = GetPlayerTechMaxAllowed(p, kind)
                SetPlayerTechMaxAllowed(p, kind, -1)
                if ReviveHero(u, GetUnitX(u), GetUnitY(u), true) then
                    revived = revived + 1
                else
                    failed = failed + 1
                end
                SetPlayerTechMaxAllowed(p, kind, limit)
            end
        end
        GroupClear(group)
        SetPlayerTechMaxAllowed(p, HERO, heroes)
        SetPlayerState(p, PLAYER_STATE_RESOURCE_FOOD_USED, food + GetPlayerState(p, PLAYER_STATE_RESOURCE_FOOD_USED))
        if revived + failed == 0 then
            msg(c.pid, "|cFFff9900Revive|r: no dead heroes.")
        elseif failed == 0 then
            msg(c.pid, "|cFFff9900Revive|r: |cFF00cc66" .. revived .. "|r hero(es) revived.")
        else
            msg(c.pid, "|cFFff9900Revive|r: |cFF00cc66" .. revived .. "|r revived, |cFFff1a1a" .. failed .. "|r failed.")
        end
    end

    function cmd.pname(c)
        SetPlayerName(Player(c.pid), c.rest)
        msg(c.pid, "|cFFff9900Name|r has been changed to: " .. color(c.pid) .. ".")
    end

    function cmd.pzoom(c)
        local p, d = players[c.pid], c:real(1)
        if c:off() then
            c:switch("|cFFff9900Zoom|r", p.zoom ~= nil, false)
            return zoomOff(c.pid)
        elseif d <= 0. then
            return c:usage()
        end
        p.zoom = d
        if not zoomTimer then
            zoomTimer = CreateTimer()
            TimerStart(zoomTimer, .5, true, zoomTick)
        end
        zoomTick()
        msg(c.pid, "|cFFff9900Zoom|r: |cFFffcc00" .. R2I(d) .. "|r. Type |cFF00aaff" .. prefix(c.pid) .. "pzoom off|r to restore.")
    end

    function cmd.act(c)
        activator = c[1]
        msg(c.pid, "|cFFff9900Activator|r has been changed to: |cFF00cc66" .. activator .. "|r.")
    end

    function cmd.bind(c)
        local p, slot, line = players[c.pid], c.data, c.rest
        local key = "|cFFff9900" .. ARROW_NAMES[slot] .. " Arrow Key|r"
        if line:sub(1, 1) == prefix(c.pid) then
            line = line:sub(2)
        end
        if c:off() then
            p.bind[slot] = nil
            msg(c.pid, key .. " bind has been |cFFff1a1aremoved|r.")
        else
            p.bind[slot] = line
            msg(c.pid, "[ |cFF00cc66" .. line .. "|r ] has been |cFF00cc66bound|r to " .. key .. ".")
        end
    end

    function cmd.showbinds(c)
        local text = "|cFF00cc66Current Bound Commands|r:"
        for slot, name in ipairs(ARROW_NAMES) do
            local line = players[c.pid].bind[slot]
            text = text .. "\n|cFFff9900" .. name .. ":|r [ " .. (line and "|cFF00cc66" .. line or "|cFFff5050NONE") .. "|r ]"
        end
        msg(c.pid, text)
    end

    function cmd.clearbinds(c)
        players[c.pid].bind = {}
        msg(c.pid, "|cFFff9900Key bindings|r have been |cFFff1a1aremoved|r.")
    end

    function cmd.toggle(c)
        local p, key, label = players[c.pid], table.unpack(c.data)
        local was, on = p[key] == true, not c:off()
        c:switch(label, was, on)
        p[key] = on or nil
        if on and not was and key == "fast" then
            EnableTrigger(orderTrigs[1])
            EnableTrigger(orderTrigs[2])
            msg(c.pid, "|cFFff1a1aDon't|r forget to press |cFF00cc66ESC|r to instantly build and train units.")
        end
    end

    function cmd.mh(c)
        local p = players[c.pid]
        local was = p.fog ~= nil
        c:switch("|cFFff9900Map hack|r", was, not c:off())
        if c:off() then
            mapHackOff(c.pid)
        elseif not was then
            p.fog = CreateFogModifierRect(Player(c.pid), FOG_OF_WAR_VISIBLE, bj_mapInitialPlayableArea, false, false)
            FogModifierStart(p.fog)
        end
    end

    function cmd.tp(c)
        local p, a = players[c.pid], c:low(1)
        local tp = prefix(c.pid) .. "tp"
        if c:off() then
            c:switch("|cFFff9900Teleport|r", p.tp == true, false)
            p.tp = nil
            return
        elseif c.n >= 1 and not TP_KEYS[a] then
            return c:usage()
        end
        if not p.tp then
            p.tp, p.tpOrder = true, TP_KEYS.p[1]
            EnableTrigger(tpTrig)
            msg(c.pid, "|cFFff9900Teleport|r has been |cFF00cc66enabled|r! Press |cFF00aaffP|r (patrol) on the desired place.\nChange the key with: " .. tp .. " |cFF00aaffM|r (move), " .. tp .. " |cFF00aaffP|r (patrol), " .. tp .. " |cFF00aaffA|r (attack).")
        elseif c.n == 0 then
            c:switch("|cFFff9900Teleport|r", true, true)
        end
        if TP_KEYS[a] then
            p.tpOrder = TP_KEYS[a][1]
            msg(c.pid, "|cFFff9900Teleport's|r bind key changed to |cFF00aaff" .. TP_KEYS[a][2] .. "|r.")
        end
    end

    function cmd.sitem(c)
        if not c:off() then
            return search(c.pid, c.rest, c.name == "sitem!" and 14776336 or 238328)
        elseif not players[c.pid].search then
            return msg(c.pid, "There's |cFFff9900no item search|r running.")
        end
        players[c.pid].search = nil
        msg(c.pid, "Item search |cFFff1a1acancelled|r.")
    end

    function cmd.prefix(c)
        local p = c[1]
        if #p ~= 1 or not PREFIXES:find(p, 1, true) then
            return msg(c.pid, "The |cFFff9900prefix|r must be |cFFffcc00one|r of these symbols: |cFF00aaff" .. PREFIXES:gsub(".", " %0"):sub(2) .. "|r")
        end
        players[c.pid].prefix = p
        msg(c.pid, "|cFFff9900Command prefix|r changed to |cFF00aaff" .. p .. "|r. Example: |cFF00aaff" .. p .. "cmds|r")
    end

    function cmd.cmds(c)
        local p, find = prefix(c.pid), c.n > 0 and lower(c.rest) or nil
        local text = "|cFF3366ffNZCP|r commands (|cFF00aaff" .. p .. "cmds <text>|r shows the syntax):"
        local last, hits = nil, 0
        for _, name in ipairs(names) do
            local k = cmds[name]
            if not find then
                local side = k.flags == PLAYER and "\n|cFFff9900Player:|r" or "\n|cFFff9900Selected units:|r"
                if side ~= last then
                    text, last = text .. side, side
                end
                text = text .. " " .. p .. name
            elseif name:find(find, 1, true) then
                hits = hits + 1
                text = text .. "\n|cFF00aaff" .. p .. name .. "|r " .. k.usage
            end
        end
        if find and hits == 0 then
            text = "No command matches |cFFe6b800[" .. find .. "]|r."
        end
        msg(c.pid, text, 30.)
    end

    function cmd.clear(c)
        if GetLocalPlayer() == Player(c.pid) then
            ClearTextMessages()
        end
    end

    function cmd.noreplay(c)
        DoNotSaveReplay()
        msg(c.pid, "|cFFff9900Replay|r has been |cFFff1a1adisabled|r.")
    end

    function cmd.disable(c)
        local level = players[c.pid].level
        for i = 0, bj_MAX_PLAYER_SLOTS - 1 do
            local o = players[i]
            if o.level > level then
                o.level = o.level - 1
                msg(i, color(c.pid) .. " has |cFFff1a1adeactivated|r |cFF3366ffNZCP|r. Your cheater level has changed to: |cFF0099ff" .. o.level .. "|r.")
            end
        end
        mapHackOff(c.pid)
        zoomOff(c.pid)
        players[c.pid].search = nil
        players[c.pid] = fresh()
        msg(c.pid, "|cFF3366ffNZCP|r has been |cFFff1a1adeactivated|r.")
    end

    local COMMANDS = {
        { "lvl", GUARD, "<level>", cmd.lvl },
        { "str", GUARD, "<value>", cmd.stat, STATS.str },
        { "agi", GUARD, "<value>", cmd.stat, STATS.agi },
        { "int", GUARD, "<value>", cmd.stat, STATS.int },
        { "sp", GUARD, "<points>", cmd.stat, STATS.sp },
        { "hp", GUARD, "<value>", cmd.stat, STATS.hp },
        { "mp", GUARD, "<value>", cmd.stat, STATS.mp },
        { "ms", GUARD, "<speed>", cmd.stat, STATS.ms },
        { "xp", GUARD, "<value>", cmd.stat, STATS.xp },
        { "owner", GUARD, "<player number>", cmd.owner },
        { "charge", GUARD, "<slot 1-6> <charges>", cmd.charge },
        { "dmgc", GUARD, "<chance%> [multiplier]", cmd.dmgc },
        { "dmghp", GUARD, "<%>", cmd.dmghp },
        { "dmgls", GUARD, "<%>", cmd.pct, { "lifesteal", "Life steal" } },
        { "dmgms", GUARD, "<%>", cmd.pct, { "manasteal", "Mana steal" } },
        { "dmgb", GUARD, "<%>", cmd.pct, { "block", "Block damage" } },
        { "dmgr", GUARD, "<%>", cmd.pct, { "reflect", "Reflect damage" } },
        { "dmgs", GUARD, "<%>", cmd.pct, { "amp", "Spell damage" } },
        { "vul", GUARD, "", cmd.invul },
        { "invul", GUARD, "", cmd.invul },
        { "kill", GUARD, "", cmd.kill },
        { "removeu", GUARD, "", cmd.kill },
        { "copy", EACH, "<amount> [full]", cmd.copy },
        { "learn", EACH, "<ability ID>", cmd.learn },
        { "unlearn", EACH, "<ability ID>", cmd.learn },
        { "rg", EACH, "<value|off>", cmd.rg },
        { "nc", EACH, "[off]", cmd.nc },
        { "pause", EACH, "[off]", cmd.pause },
        { "islot", EACH, "<slot 1-6> <item ID>", cmd.islot },
        { "status", FIRST, "", cmd.status },
        { "unitid", FIRST, "", cmd.unitid },
        { "itemid", FIRST, "<slot 1-6>", cmd.itemid },
        { "create", FIRST, "<object ID>", cmd.create },
        { "ritem", FIRST, "<amount 1-99>", cmd.ritem },
        { "food", PLAYER, "<value|use|nouse>", cmd.food },
        { "gold", PLAYER, "<amount>", cmd.resource, GOLD },
        { "lumber", PLAYER, "<amount>", cmd.resource, LUMBER },
        { "giveg", PLAYER, "<player> <amount>", cmd.give, GOLD },
        { "givel", PLAYER, "<player> <amount>", cmd.give, LUMBER },
        { "givef", PLAYER, "<player> <amount>", cmd.give },
        { "grate", PLAYER, "<%>", cmd.rate, GOLD },
        { "lrate", PLAYER, "<%>", cmd.rate, LUMBER },
        { "expr", PLAYER, "<%>", cmd.expr },
        { "tech", PLAYER, "<upgrade ID> [level]", cmd.tech },
        { "kick", PLAYER, "<player>", cmd.kick },
        { "share", PLAYER, "<player> <player>", cmd.share },
        { "unshare", PLAYER, "<player> <player>", cmd.share },
        { "ploc", PLAYER, "<x> <y>", cmd.ploc },
        { "revive", PLAYER, "", cmd.revive },
        { "pname", PLAYER, "<name>", cmd.pname },
        { "pzoom", PLAYER, "<distance|off>", cmd.pzoom },
        { "act", PLAYER, "<word>", cmd.act },
        { "bindleft", PLAYER, "<command line|off>", cmd.bind, 1 },
        { "bindright", PLAYER, "<command line|off>", cmd.bind, 2 },
        { "bindup", PLAYER, "<command line|off>", cmd.bind, 3 },
        { "binddown", PLAYER, "<command line|off>", cmd.bind, 4 },
        { "showbinds", PLAYER, "", cmd.showbinds },
        { "clearbinds", PLAYER, "", cmd.clearbinds },
        { "fast", PLAYER, "[off]", cmd.toggle, { "fast", "|cFFff9900Fast|r building, upgrading and training" } },
        { "enemychat", PLAYER, "[off]", cmd.toggle, { "spy", "|cFFff1a1aEnemy|r's chat" } },
        { "nowaste", PLAYER, "[off]", cmd.toggle, { "nowaste", "|cFFff9900Infinite Charge|r" } },
        { "mh", PLAYER, "[off]", cmd.mh },
        { "tp", PLAYER, "[m|p|a|off]", cmd.tp },
        { "sitem", PLAYER, "<text|off>", cmd.sitem },
        { "sitem!", PLAYER, "<text|off>", cmd.sitem },
        { "cmds", PLAYER, "[text]", cmd.cmds },
        { "prefix", PLAYER, "<symbol>", cmd.prefix },
        { "clear", PLAYER, "", cmd.clear },
        { "noreplay", PLAYER, "", cmd.noreplay },
        { "disable", PLAYER, "", cmd.disable },
    }

    local function call(fn, c)
        local ok, err = pcall(fn, c)
        if not ok then
            msg(c.pid, "|cFFff1a1aNZCP error|r in |cFF00aaff" .. prefix(c.pid) .. c.name .. "|r: " .. tostring(err))
        end
    end

    local function run(pid, line)
        local name, rest = line:gsub(" +$", ""):match("^ *([^ ]+) ?(.*)$")
        name = name and lower(name)
        local k = cmds[name or ""]
        if not k then
            return
        end
        local c = setmetatable({ pid = pid, name = name, rest = rest, data = k.data, n = 0, first = true }, Ctx)
        for word in rest:gmatch("[^ ]+") do
            c.n = c.n + 1
            c[c.n] = word
        end
        if c.n < k.need then
            return c:usage()
        end
        GroupEnumUnitsSelected(group, Player(pid), nil)
        local selected = {}
        for i = 0, BlzGroupGetSize(group) - 1 do
            selected[i + 1] = BlzGroupUnitAt(group, i)
        end
        GroupClear(group)
        c.unit = selected[1]
        if k.flags ~= PLAYER and not c.unit then
            return msg(pid, "|cFFff1a1aSelect a unit|r first.")
        elseif k.flags ~= EACH and k.flags ~= GUARD then
            return call(k.fn, c)
        end
        local per, done = { __index = c }, 0
        for _, u in ipairs(selected) do
            if k.flags ~= GUARD or players[pid].level >= players[GetPlayerId(GetOwningPlayer(u))].level then
                call(k.fn, setmetatable({ unit = u, first = done == 0 }, per))
                done = done + 1
            end
        end
        if done > 1 then
            msg(pid, "Applied to |cFF00cc66" .. done .. "|r units.")
        end
    end

    local function onChat()
        local from = GetPlayerId(GetTriggerPlayer())
        local text = GetEventPlayerChatString()
        for i = 0, bj_MAX_PLAYER_SLOTS - 1 do
            local p = players[i]
            if p.spy and p.level > players[from].level and IsPlayerEnemy(Player(from), Player(i)) then
                msg(i, "[Enemies] " .. color(from) .. ": " .. text)
            end
        end
        local line = text:sub(2)
        if text:sub(1, 1) ~= prefix(from) or line == "" then
            return
        end
        if line == activator then
            activate(from)
        elseif players[from].on then
            run(from, line)
        end
    end

    local function onArrow(slot)
        local pid = GetPlayerId(GetTriggerPlayer())
        local p = players[pid]
        if p.on then
            if p.bind[slot] then
                run(pid, p.bind[slot])
            end
            return
        end
        local key, step = ("LRUD"):sub(slot, slot), p.step or 0
        if ARROWS:sub(step + 1, step + 1) == key then
            step = step + 1
        else
            local seq = ARROWS:sub(1, step) .. key
            step = step + 1
            repeat
                step = step - 1
            until step <= 0 or seq:sub(-step) == ARROWS:sub(1, step)
        end
        if step > 0 and step == #ARROWS then
            step = 0
            activate(pid)
        end
        p.step = step
    end

    local function onResource(res)
        local p = GetTriggerPlayer()
        local d = players[GetPlayerId(p)]
        local total, last, rate = GetPlayerState(p, res.state), d.last[res.key] or 0, d.rate[res.key]
        if rate and total > last then
            local bonus = R2I((total - last) * rate / 100.)
            total = total + bonus
            DisableTrigger(GetTriggeringTrigger())
            SetPlayerState(p, res.state, total)
            EnableTrigger(GetTriggeringTrigger())
            DisplayTimedTextToPlayer(p, 0., 0., 2., "|cFF00cc66+" .. (total - last) .. "|r " .. res.given .. " |cFF999999(rate +" .. bonus .. ")|r")
        end
        d.last[res.key] = total
    end

    local function onFast()
        local p = GetTriggerPlayer()
        if not players[GetPlayerId(p)].fast then
            return
        end
        local u, trained, tech = GetTriggerUnit(), GetTrainedUnitType(), GetResearched()
        if trained ~= 0 then
            CreateUnit(p, trained, GetUnitX(u), GetUnitY(u), 270.)
        end
        UnitSetConstructionProgress(u, 100)
        UnitSetUpgradeProgress(u, 100)
        if tech ~= 0 then
            SetPlayerTechResearched(p, tech, GetPlayerTechCount(p, tech, true) + 1)
        end
    end

    local function onTeleport()
        local p = players[GetPlayerId(GetTriggerPlayer())]
        if p.tp and GetIssuedOrderId() == p.tpOrder then
            SetUnitPosition(GetTriggerUnit(), GetOrderPointX(), GetOrderPointY())
        end
    end

    local function onNoWaste()
        if players[GetPlayerId(GetTriggerPlayer())].nowaste then
            SetItemCharges(GetManipulatedItem(), GetItemCharges(GetManipulatedItem()) + 1)
        end
    end

    local function onDeath()
        local u = GetTriggerUnit()
        if units[u] and not IsUnitType(u, UNIT_TYPE_HERO) then
            forget(u)
        end
    end

    local function trigger(fn, register, count)
        local t = CreateTrigger()
        for i = 0, (count or bj_MAX_PLAYER_SLOTS) - 1 do
            register(t, Player(i))
        end
        TriggerAddCondition(t, Condition(fn))
        return t
    end

    local function onUnit(event, fn, dormant)
        local t = trigger(fn, function(t, p) TriggerRegisterPlayerUnitEvent(t, p, event, nil) end)
        if dormant then
            DisableTrigger(t)
        end
        return t
    end

    local function onState(res)
        trigger(function() onResource(res) end, function(t, p) TriggerRegisterPlayerStateEvent(t, p, res.state, GREATER_THAN, 0.) end)
    end

    local function init()
        group = CreateGroup()
        for i = 0, bj_MAX_PLAYER_SLOTS - 1 do
            players[i] = fresh()
        end
        for _, entry in ipairs(COMMANDS) do
            local name, flags, usage, fn, info = table.unpack(entry)
            cmds[name] = { flags = flags, usage = usage, fn = fn, data = info, need = select(2, usage:gsub("<", "")) }
            names[#names + 1] = name
        end
        dmgTrig = onUnit(EVENT_PLAYER_UNIT_DAMAGED, onDamage, true)
        orderTrigs = { onUnit(EVENT_PLAYER_UNIT_ISSUED_ORDER, onFast, true), onUnit(EVENT_PLAYER_UNIT_ISSUED_UNIT_ORDER, onFast, true) }
        tpTrig = onUnit(EVENT_PLAYER_UNIT_ISSUED_POINT_ORDER, onTeleport, true)
        onUnit(EVENT_PLAYER_UNIT_DEATH, onDeath)
        onUnit(EVENT_PLAYER_UNIT_USE_ITEM, onNoWaste)
        onUnit(EVENT_PLAYER_UNIT_CONSTRUCT_CANCEL, onFast)
        onUnit(EVENT_PLAYER_UNIT_UPGRADE_CANCEL, onFast)
        onUnit(EVENT_PLAYER_UNIT_TRAIN_CANCEL, onFast)
        onUnit(EVENT_PLAYER_UNIT_RESEARCH_START, onFast)
        onState(GOLD)
        onState(LUMBER)
        trigger(onChat, function(t, p) TriggerRegisterPlayerChatEvent(t, p, "", false) end)
        for slot, event in ipairs({ EVENT_PLAYER_ARROW_LEFT_DOWN, EVENT_PLAYER_ARROW_RIGHT_DOWN, EVENT_PLAYER_ARROW_UP_DOWN, EVENT_PLAYER_ARROW_DOWN_DOWN }) do
            trigger(function() onArrow(slot) end, function(t, p) TriggerRegisterPlayerEvent(t, p, event) end, bj_MAX_PLAYERS)
        end
        nameActivate(AUTO_NAME)
    end

    local main0 = main
    function main()
        main0()
        init()
    end
end