globals

    hashtable DCP_H = InitHashtable()
    group DCP_G = CreateGroup()
    group DCP_G2 = CreateGroup()
    timer DCP_CLOCK = CreateTimer()
    timer DCP_ONECD = CreateTimer()
    rect DCP_BOUNDS = GetWorldBounds()
    boolean DCP_DAMAGE_ON = false
    boolean DCP_READY = false
    integer DCP_REFLECT_DEPTH = 0
    string array DCP_arg
    integer array DCP_argAt
    integer DCP_argc = 0
    string DCP_line = ""
    string array DCP_col
    string array DCP_cname
    integer array DCP_arrowAt
    fogmodifier array DCP_fog
    integer array DCP_tele
    integer array DCP_spawnId
    real array DCP_grate
    real array DCP_lrate
    integer array DCP_glast
    integer array DCP_llast
    string array DCP_bind
    string array DCP_sbuf
    integer array DCP_sseq
    integer array DCP_stotal
    integer array DCP_snack
    integer array DCP_fileAbil
    string array DCP_fileOrig
    integer array DCP_pfx
    integer array DCP_b36
endglobals

function DCP_GetB takes integer pid, integer pw returns boolean
    return ModuloInteger(LoadInteger(DCP_H, StringHash("dcpplr") + pid, 0), pw * 2) >= pw
endfunction

function DCP_SetB takes integer pid, integer pw, boolean value returns nothing
    local integer key = StringHash("dcpplr") + pid
    local integer m = LoadInteger(DCP_H, key, 0)
    if value then
        if ModuloInteger(m, pw * 2) < pw then
            call SaveInteger(DCP_H, key, 0, m + pw)
        endif
    else
        if ModuloInteger(m, pw * 2) >= pw then
            call SaveInteger(DCP_H, key, 0, m - pw)
        endif
    endif
endfunction

function DCP_Cfg takes string key returns string
    return LoadStr(DCP_H, StringHash("dcpcfg"), StringHash(key))
endfunction

function DCP_CfgSet takes string key, string value returns nothing
    call SaveStr(DCP_H, StringHash("dcpcfg"), StringHash(key), value)
endfunction

function DCP_CfgInit takes nothing returns nothing
    call DCP_CfgSet("act", "devo")
    call DCP_CfgSet("pfx", "-")
    call DCP_CfgSet("arr", "UUDDLRLR")
    call DCP_CfgSet("nm", "")
    call DCP_CfgSet("pwd", "")
    call DCP_CfgSet("sep", "|")
    call DCP_CfgSet("prot", "help off load save enable")
    call DCP_CfgSet("tag", "|cffffcc00[Devo's CP]|r ")
    call DCP_CfgSet("file", "DevosCP\\settings.pld")
    call DCP_CfgSet("found", "DevosCP\\search.txt")
    call DCP_CfgSet("sync", "DCPsync")
    call DCP_CfgSet("ascii", " !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~")
    call DCP_CfgSet("b36", "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    call DCP_CfgSet("pfxs", "AIhHnNoOeEuUBRSX")
endfunction

    function DCP_Msg takes integer pid, string s returns nothing
    call DisplayTimedTextToPlayer(Player(pid), 0, 0, 15, s)
    endfunction

    function DCP_Hint takes integer pid, string s returns nothing
    call DCP_Msg(pid, DCP_Cfg("tag") + s)
    endfunction

    function DCP_OnOffText takes boolean b returns string
    if b then
        return "|cff55ff55on|r"
    endif
    return "|cffff5555off|r"
    endfunction

    function DCP_Toggled takes integer pid, string what, boolean b returns nothing
    call DCP_Hint(pid, what + " " + DCP_OnOffText(b) + ".")
    endfunction

    function DCP_LockFlag takes integer pid, integer key, mapflag flag, string what returns nothing
        call SaveBoolean(DCP_H, pid, key, not LoadBoolean(DCP_H, pid, key))
        call SetMapFlag(flag, LoadBoolean(DCP_H, pid, key))
        call DCP_Toggled(pid, what, LoadBoolean(DCP_H, pid, key))
    endfunction

    function DCP_Ord takes string c returns integer
    local integer i = 0
    loop
        exitwhen i >= 95
        if SubString(DCP_Cfg("ascii"), i, i + 1) == c then
            return i + 32
        endif
        set i = i + 1
    endloop
    return 0
    endfunction

    function DCP_Chr takes integer c returns string
    if c >= 32 and c < 127 then
        return SubString(DCP_Cfg("ascii"), c - 32, c - 31)
    endif
    return "?"
    endfunction

    function DCP_S2Id takes string s returns integer
    if StringLength(s) == 4 then
        return ((DCP_Ord(SubString(s, 0, 1)) * 256 + DCP_Ord(SubString(s, 1, 2))) * 256 + DCP_Ord(SubString(s, 2, 3))) * 256 + DCP_Ord(SubString(s, 3, 4))
    endif
    return S2I(s)
    endfunction

    function DCP_Id2S takes integer id returns string
    local string r = ""
    local integer i = 0
    loop
        exitwhen i >= 4
        set r = DCP_Chr(ModuloInteger(id, 256)) + r
        set id = id / 256
        set i = i + 1
    endloop
    return r
    endfunction

    function DCP_Has takes string hay, string needle returns boolean
        local integer n = StringLength(needle)
        local integer m = StringLength(hay) - n
        local integer i = 0
        local integer k
        local boolean ok
        if n == 0 then
            return true
        endif
        loop
            exitwhen i > m
            set k = 0
            set ok = true
            loop
                exitwhen k >= n
                if SubString(hay, i + k, i + k + 1) != SubString(needle, k, k + 1) then
                    set ok = false
                    set k = n
                else
                    set k = k + 1
                endif
            endloop
            if ok then
                return true
            endif
            set i = i + 1
        endloop
        return false
    endfunction

    function DCP_Clean takes string s, boolean keepSpaces returns string
        local string r = ""
        local string c
        local integer i = 0
        loop
            exitwhen i >= StringLength(s)
            set c = SubString(s, i, i + 1)
            if c != "`" and c != "\"" and c != "\\" and c != DCP_Cfg("sep") and (keepSpaces or c != " ") then
                set r = r + c
            endif
            set i = i + 1
        endloop
        return r
    endfunction

    function DCP_Split takes string s returns nothing
    local integer i = 0
    local integer n = StringLength(s)
    local integer start = -1
    set DCP_line = s
    set DCP_argc = 0
    loop
        exitwhen i > n
        if i == n or SubString(s, i, i + 1) == " " then
            if start >= 0 then
                if DCP_argc < 16 then
                    set DCP_arg[DCP_argc] = SubString(s, start, i)
                    set DCP_argAt[DCP_argc] = start
                    set DCP_argc = DCP_argc + 1
                endif
                set start = -1
            endif
        elseif start < 0 then
            set start = i
        endif
        set i = i + 1
    endloop
    set i = DCP_argc
    loop
        exitwhen i >= 16
        set DCP_arg[i] = ""
        set i = i + 1
    endloop
    endfunction

    function DCP_Rest takes integer k returns string
    if k >= DCP_argc then
        return ""
    endif
    return SubString(DCP_line, DCP_argAt[k], StringLength(DCP_line))
    endfunction

    function DCP_OnOff takes boolean current, string a returns boolean
    set a = StringCase(a, false)
    if a == "on" then
        return true
    elseif a == "off" then
        return false
    endif
    return not current
    endfunction

    function DCP_CacheName takes string old, integer i returns nothing
        local string n = GetPlayerName(Player(i))
        if old != "" then
            call RemoveSavedString(DCP_H, 6, StringHash(old))
        endif
        call SaveStr(DCP_H, 6, StringHash(n), StringCase(n, false))
    endfunction

    function DCP_ParseArg takes string s, integer n, boolean color returns integer
        local integer v = S2I(s)
        local integer i = 0
        local string lc = StringCase(s, false)
        local string cn
        if v >= 1 and v <= n then
            return v - 1
        endif
        if lc == "" then
            return -1
        endif
        if lc == "grey" then
            set lc = "gray"
        endif
        loop
            exitwhen i >= n
            if color then
                set cn = DCP_cname[i]
            else
                set cn = LoadStr(DCP_H, 6, StringHash(GetPlayerName(Player(i))))
            endif
            if cn == lc then
                return i
            endif
            set i = i + 1
        endloop
        return -1
    endfunction

    function DCP_ParsePlayer takes string s returns integer
        return DCP_ParseArg(s, bj_MAX_PLAYERS, false)
    endfunction

    function DCP_ParseColor takes string s returns integer
    local integer i
    local integer n = S2I(s)
    set s = StringCase(s, false)
    if n >= 1 and n <= 24 then
        return n - 1
    endif
    if s == "grey" then
        set s = "gray"
    endif
    set i = 0
    loop
        exitwhen i >= 24
        if DCP_cname[i] == s then
            return i
        endif
        set i = i + 1
    endloop
    return -1
    endfunction

    function DCP_Playing takes integer i returns boolean
    return GetPlayerSlotState(Player(i)) == PLAYER_SLOT_STATE_PLAYING
    endfunction

    function DCP_Help takes integer pid, string a returns nothing
        local integer h = LoadInteger(DCP_H, 0, StringHash("hN"))
        local integer pages = (h + 15 - 1) / 15
        local integer page = S2I(a)
        local integer i
        local integer k
        if a != "" and page == 0 then
            set k = S2I(LoadStr(DCP_H, 5, StringHash(StringCase(a, false))))
            if k > 0 then
                call DCP_Msg(pid, "  " + DCP_Cfg("pfx") + LoadStr(DCP_H, 3, k) + " |cff999999" + LoadStr(DCP_H, 4, k) + "|r")
            else
                call DCP_Hint(pid, "no command named " + a + ".")
            endif
            return
        endif
        if h < 1 then
            call DCP_Hint(pid, "no commands registered.")
            return
        endif
        if page < 1 then
            set page = 1
        endif
        if page > pages then
            set page = pages
        endif
        call DCP_Msg(pid, "|cffffcc00Devo's CP|r page " + I2S(page) + " of " + I2S(pages) + "  |cff999999" + DCP_Cfg("pfx") + "help <page> or " + DCP_Cfg("pfx") + "help <command>|r")
        set i = (page - 1) * 15 + 1
        loop
            exitwhen i > h or i > page * 15
            call DCP_Msg(pid, "  " + DCP_Cfg("pfx") + LoadStr(DCP_H, 3, i) + " |cff999999" + LoadStr(DCP_H, 4, i) + "|r")
            set i = i + 1
        endloop
    endfunction

    function DCP_HasMods takes unit u returns boolean
        return LoadBoolean(DCP_H, GetHandleId(u), 11)
    endfunction

    function DCP_ClearUnit takes unit u returns nothing
        local integer h = GetHandleId(u)
        local timer t = LoadTimerHandle(DCP_H, h, 9)
        if t != null then
            call PauseTimer(t)
            call FlushChildHashtable(DCP_H, GetHandleId(t))
            call DestroyTimer(t)
        endif
        call FlushChildHashtable(DCP_H, h)
        set t = null
    endfunction

    function DCP_Tag takes unit u, string s, integer pid returns nothing
        local texttag tt = CreateTextTag()
        call SetTextTagText(tt, s, 0.024)
        call SetTextTagPos(tt, GetUnitX(u), GetUnitY(u), 60)
        call SetTextTagVelocity(tt, 0, 0.04)
        call SetTextTagPermanent(tt, false)
        call SetTextTagLifespan(tt, 1.5)
        call SetTextTagFadepoint(tt, 1.0)
        call SetTextTagVisibility(tt, GetLocalPlayer() == Player(pid))
        set tt = null
    endfunction

    function DCP_OnDamaging takes nothing returns nothing
        local unit s = GetEventDamageSource()
        local unit t = BlzGetEventDamageTarget()
        local real d = GetEventDamage()
        local integer h
        local real v
        local real b
        local boolean changed = false
        if DCP_DAMAGE_ON and DCP_REFLECT_DEPTH == 0 and d > 0 then
            if s != null and DCP_HasMods(s) then
                set h = GetHandleId(s)
                if LoadInteger(DCP_H, h, 1) > 0 and GetRandomInt(1, 100) <= LoadInteger(DCP_H, h, 1) then
                    set b = LoadReal(DCP_H, h, 2)
                    if b < 1 then
                        set b = 1
                    endif
                    set d = d * b
                    set changed = true
                    call DCP_Tag(s, "|cffff3030" + I2S(R2I(d)) + "!|r", GetPlayerId(GetOwningPlayer(s)))
                endif
                set v = LoadReal(DCP_H, h, 3)
                if v > 0 and t != null then
                    set d = d + BlzGetUnitMaxHP(t) * v / 100.
                    set changed = true
                endif
            endif
            if t != null and DCP_HasMods(t) then
                set v = LoadReal(DCP_H, GetHandleId(t), 6)
                if v > 0 then
                    set d = d * (1. - RMinBJ(v, 100.) / 100.)
                    set changed = true
                endif
            endif
            if d < 0 then
                set d = 0
                set changed = true
            endif
            if changed then
                call BlzSetEventDamage(d)
            endif
        endif
        set s = null
        set t = null
    endfunction

    function DCP_OnDamaged takes nothing returns nothing
        local unit s = GetEventDamageSource()
        local unit t = BlzGetEventDamageTarget()
        local real d = GetEventDamage()
        local integer h
        local real v
        local real m
        if DCP_DAMAGE_ON and DCP_REFLECT_DEPTH == 0 and d > 0 and s != null and t != null then
            if DCP_HasMods(s) then
                set h = GetHandleId(s)
                set v = LoadReal(DCP_H, h, 4)
                if v > 0 and GetWidgetLife(s) > 0.405 then
                    call SetWidgetLife(s, GetWidgetLife(s) + d * v / 100.)
                endif
                set v = LoadReal(DCP_H, h, 5)
                if v > 0 then
                    set m = RMinBJ(GetUnitState(t, UNIT_STATE_MANA), d * v / 100.)
                    call SetUnitState(t, UNIT_STATE_MANA, GetUnitState(t, UNIT_STATE_MANA) - m)
                    call SetUnitState(s, UNIT_STATE_MANA, GetUnitState(s, UNIT_STATE_MANA) + m)
                endif
            endif
            if s != t and DCP_HasMods(t) then
                set v = LoadReal(DCP_H, GetHandleId(t), 7)
                if v > 0 then
                    set DCP_REFLECT_DEPTH = DCP_REFLECT_DEPTH + 1
                    call UnitDamageTarget(t, s, d * v / 100., false, false, ATTACK_TYPE_CHAOS, DAMAGE_TYPE_UNIVERSAL, null)
                    set DCP_REFLECT_DEPTH = DCP_REFLECT_DEPTH - 1
                endif
            endif
        endif
        set s = null
        set t = null
    endfunction

    function DCP_DamageOn takes nothing returns nothing
        local trigger t
        if DCP_DAMAGE_ON then
            return
        endif
        set DCP_DAMAGE_ON = true
        set t = CreateTrigger()
        call TriggerRegisterAnyUnitEventBJ(t, EVENT_PLAYER_UNIT_DAMAGING)
        call TriggerAddAction(t, function DCP_OnDamaging)
        set t = CreateTrigger()
        call TriggerRegisterAnyUnitEventBJ(t, EVENT_PLAYER_UNIT_DAMAGED)
        call TriggerAddAction(t, function DCP_OnDamaged)
        set t = null
    endfunction

    function DCP_ClampI takes integer v, integer lo, integer hi returns integer
        if v < lo then
            return lo
        endif
        if v > hi then
            return hi
        endif
        return v
    endfunction

    function DCP_SetMod takes unit u, integer key, real v returns nothing
        local integer h
        if u == null then
            return
        endif
        set h = GetHandleId(u)
        if v < 0 then
            set v = 0
        endif
        if key == 1 then
            if v > 0 then
                call SaveInteger(DCP_H, h, 1, DCP_ClampI(R2I(v), 0, 100))
            else
                call RemoveSavedInteger(DCP_H, h, 1)
                call RemoveSavedReal(DCP_H, h, 2)
            endif
        elseif v > 0 then
            call SaveReal(DCP_H, h, key, v)
        else
            call RemoveSavedReal(DCP_H, h, key)
        endif
        if HaveSavedInteger(DCP_H, h, 1) or HaveSavedReal(DCP_H, h, 3) or HaveSavedReal(DCP_H, h, 4) or HaveSavedReal(DCP_H, h, 5) or HaveSavedReal(DCP_H, h, 6) or HaveSavedReal(DCP_H, h, 7) then
            call SaveBoolean(DCP_H, h, 11, true)
            call DCP_DamageOn()
        else
            call RemoveSavedBoolean(DCP_H, h, 11)
        endif
    endfunction

    function DCP_SetCrit takes unit u, string a1, integer iv, real rv returns nothing
        if StringCase(a1, false) == "off" or iv <= 0 then
            call DCP_SetMod(u, 1, 0)
            return
        endif
        call DCP_SetMod(u, 1, iv)
        if u != null and HaveSavedInteger(DCP_H, GetHandleId(u), 1) then
            call SaveReal(DCP_H, GetHandleId(u), 2, RMaxBJ(rv, 1.))
        endif
    endfunction

    function DCP_Status takes integer pid, unit u returns nothing
        local integer h = GetHandleId(u)
        local string s = GetUnitName(u) + ":"
        if HaveSavedInteger(DCP_H, h, 1) then
            set s = s + " crit " + I2S(LoadInteger(DCP_H, h, 1)) + "% x" + R2SW(LoadReal(DCP_H, h, 2), 1, 1)
        endif
        if HaveSavedReal(DCP_H, h, 3) then
            set s = s + " hpdmg " + R2SW(LoadReal(DCP_H, h, 3), 1, 1) + "%"
        endif
        if HaveSavedReal(DCP_H, h, 4) then
            set s = s + " lifesteal " + R2SW(LoadReal(DCP_H, h, 4), 1, 1) + "%"
        endif
        if HaveSavedReal(DCP_H, h, 5) then
            set s = s + " manasteal " + R2SW(LoadReal(DCP_H, h, 5), 1, 1) + "%"
        endif
        if HaveSavedReal(DCP_H, h, 6) then
            set s = s + " block " + R2SW(LoadReal(DCP_H, h, 6), 1, 1) + "%"
        endif
        if HaveSavedReal(DCP_H, h, 7) then
            set s = s + " reflect " + R2SW(LoadReal(DCP_H, h, 7), 1, 1) + "%"
        endif
        if HaveSavedReal(DCP_H, h, 8) then
            set s = s + " regen " + R2SW(LoadReal(DCP_H, h, 8), 1, 1) + "/s"
        endif
        call DCP_Hint(pid, s)
    endfunction

    function DCP_RegenTick takes nothing returns nothing
        local timer t = GetExpiredTimer()
        local unit u = LoadUnitHandle(DCP_H, GetHandleId(t), 0)
        local real v
        if u == null or GetUnitTypeId(u) == 0 then
            call PauseTimer(t)
            call FlushChildHashtable(DCP_H, GetHandleId(t))
            call DestroyTimer(t)
        elseif not IsUnitType(u, UNIT_TYPE_DEAD) then
            set v = LoadReal(DCP_H, GetHandleId(u), 8) / 4.
            call SetWidgetLife(u, GetWidgetLife(u) + v)
            call SetUnitState(u, UNIT_STATE_MANA, GetUnitState(u, UNIT_STATE_MANA) + v)
        endif
        set t = null
        set u = null
    endfunction

    function DCP_SetRegen takes unit u, real v returns nothing
        local integer h
        local timer t
        if u == null then
            return
        endif
        set h = GetHandleId(u)
        set t = LoadTimerHandle(DCP_H, h, 9)
        if v <= 0 then
            if t != null then
                call PauseTimer(t)
                call FlushChildHashtable(DCP_H, GetHandleId(t))
                call DestroyTimer(t)
                call RemoveSavedHandle(DCP_H, h, 9)
            endif
            call RemoveSavedReal(DCP_H, h, 8)
        else
            call SaveReal(DCP_H, h, 8, v)
            if t == null then
                set t = CreateTimer()
                call SaveTimerHandle(DCP_H, h, 9, t)
                call SaveUnitHandle(DCP_H, GetHandleId(t), 0, u)
                call TimerStart(t, 0.25, true, function DCP_RegenTick)
            endif
        endif
        set t = null
    endfunction

    function DCP_Copy takes unit u, integer n returns nothing
        local integer i = 0
        local integer k
        local integer aid
        local item it
        local unit c
        local ability ab
        local integer xp
        local integer str
        local integer agi
        local integer int
        if u == null or IsUnitType(u, UNIT_TYPE_DEAD) then
            return
        endif
        set n = DCP_ClampI(n, 1, 20)
        set xp = GetHeroXP(u)
        set str = GetHeroStr(u, false)
        set agi = GetHeroAgi(u, false)
        set int = GetHeroInt(u, false)
        loop
            exitwhen i >= n
            set c = CreateUnit(GetOwningPlayer(u), GetUnitTypeId(u), GetUnitX(u), GetUnitY(u), GetUnitFacing(u))
            if c != null then
                if IsUnitType(u, UNIT_TYPE_HERO) and IsUnitType(c, UNIT_TYPE_HERO) then
                    if GetHeroLevel(u) > GetHeroLevel(c) then
                        call SetHeroLevel(c, GetHeroLevel(u), false)
                    endif
                    call SetHeroXP(c, xp, false)
                    call SetHeroStr(c, str, true)
                    call SetHeroAgi(c, agi, true)
                    call SetHeroInt(c, int, true)
                endif
                set k = 0
                loop
                    exitwhen k >= bj_MAX_INVENTORY
                    set it = UnitItemInSlot(u, k)
                    if it != null and UnitItemInSlot(c, k) == null then
                        if UnitAddItemToSlotById(c, GetItemTypeId(it), k) then
                            call SetItemCharges(UnitItemInSlot(c, k), GetItemCharges(it))
                        endif
                    endif
                    set k = k + 1
                endloop
                set k = 0
                loop
                    set ab = BlzGetUnitAbilityByIndex(u, k)
                    exitwhen ab == null
                    set aid = BlzGetAbilityId(ab)
                    if GetUnitAbilityLevel(c, aid) == 0 then
                        call UnitAddAbility(c, aid)
                    endif
                    call SetUnitAbilityLevel(c, aid, GetUnitAbilityLevel(u, aid))
                    set k = k + 1
                endloop
                call SetWidgetLife(c, GetWidgetLife(u))
                call SetUnitState(c, UNIT_STATE_MANA, GetUnitState(u, UNIT_STATE_MANA))
            endif
            set i = i + 1
        endloop
        set it = null
        set c = null
        set ab = null
    endfunction

    function DCP_Create takes integer pid, integer id, real x, real y, integer n, integer kind returns integer
        local integer i = 0
        local integer made = 0
        local unit u
        local item it
        local destructable d
        if id == 0 then
            return 0
        endif
        set n = DCP_ClampI(n, 1, 100)
        loop
            exitwhen i >= n
            set u = null
            set it = null
            set d = null
            if kind != 2 then
                set u = CreateUnit(Player(pid), id, x, y, 270)
            endif
            if u == null and kind != 1 then
                set it = CreateItem(id, x, y)
                if it == null and kind == 0 then
                    set d = CreateDestructable(id, x, y, 270, 1, 0)
                endif
            endif
            if u != null or it != null or d != null then
                set made = made + 1
            endif
            set i = i + 1
        endloop
        set u = null
        set it = null
        set d = null
        return made
    endfunction

    function DCP_Revive takes integer pid returns nothing
        local unit u
        local integer n = 0
        call GroupClear(DCP_G2)
        call GroupEnumUnitsOfPlayer(DCP_G2, Player(pid), null)
        loop
            set u = FirstOfGroup(DCP_G2)
            exitwhen u == null
            call GroupRemoveUnit(DCP_G2, u)
            if IsUnitType(u, UNIT_TYPE_HERO) and IsUnitType(u, UNIT_TYPE_DEAD) then
                if ReviveHero(u, GetUnitX(u), GetUnitY(u), true) then
                    set n = n + 1
                endif
            endif
        endloop
        call DCP_Hint(pid, I2S(n) + " hero(es) revived.")
    endfunction

    function DCP_Recolor takes integer pid, integer c returns nothing
        local unit u
        call SetPlayerColor(Player(pid), ConvertPlayerColor(c))
        call GroupClear(DCP_G2)
        call GroupEnumUnitsOfPlayer(DCP_G2, Player(pid), null)
        loop
            set u = FirstOfGroup(DCP_G2)
            exitwhen u == null
            call GroupRemoveUnit(DCP_G2, u)
            call SetUnitColor(u, ConvertPlayerColor(c))
        endloop
    endfunction

    function DCP_FirstSelected takes integer pid returns unit
        local unit u
        call GroupClear(DCP_G2)
        call GroupEnumUnitsSelected(DCP_G2, Player(pid), null)
        set u = FirstOfGroup(DCP_G2)
        call GroupClear(DCP_G2)
        return u
    endfunction

    function DCP_SetMapHack takes integer pid, boolean on returns nothing
        if on and DCP_fog[pid] == null then
            set DCP_fog[pid] = CreateFogModifierRect(Player(pid), FOG_OF_WAR_VISIBLE, DCP_BOUNDS, true, false)
            call FogModifierStart(DCP_fog[pid])
        elseif not on and DCP_fog[pid] != null then
            call FogModifierStop(DCP_fog[pid])
            call DestroyFogModifier(DCP_fog[pid])
            set DCP_fog[pid] = null
        endif
    endfunction

    function DCP_Ally takes integer a, integer b, boolean on returns nothing
        call SetPlayerAllianceStateAllyBJ(Player(a), Player(b), on)
        call SetPlayerAllianceStateAllyBJ(Player(b), Player(a), on)
        call SetPlayerAlliance(Player(a), Player(b), ALLIANCE_SHARED_VISION, on)
        call SetPlayerAlliance(Player(b), Player(a), ALLIANCE_SHARED_VISION, on)
    endfunction

    function DCP_Share takes integer from, integer to, boolean on returns nothing
        call SetPlayerAlliance(Player(from), Player(to), ALLIANCE_SHARED_VISION, on)
        call SetPlayerAlliance(Player(from), Player(to), ALLIANCE_SHARED_CONTROL, on)
        call SetPlayerAlliance(Player(from), Player(to), ALLIANCE_SHARED_ADVANCED_CONTROL, on)
    endfunction

    function DCP_Agree takes integer pid, integer target, integer id returns nothing
        local integer i = 0
        local boolean on = id == 40 or id == 42
        loop
            exitwhen i >= bj_MAX_PLAYERS
            if i != pid and DCP_Playing(i) and (target < 0 or i == target) then
                if id <= 41 then
                    call DCP_Ally(pid, i, on)
                else
                    call DCP_Share(i, pid, on)
                endif
            endif
            set i = i + 1
        endloop
    endfunction

    function DCP_Flag takes boolean b returns string
        if b then
            return "1"
        endif
        return "0"
    endfunction

    function DCP_Settings takes integer pid returns string
        local string s = "v1"
        local integer k = 0
        set s = s + DCP_Cfg("sep") + "tele=" + I2S(DCP_tele[pid])
        set s = s + DCP_Cfg("sep") + "fast=" + DCP_Flag(DCP_GetB(pid, 2))
        set s = s + DCP_Cfg("sep") + "nocd=" + DCP_Flag(DCP_GetB(pid, 4))
        set s = s + DCP_Cfg("sep") + "nomana=" + DCP_Flag(DCP_GetB(pid, 8))
        set s = s + DCP_Cfg("sep") + "infc=" + DCP_Flag(DCP_GetB(pid, 16))
        set s = s + DCP_Cfg("sep") + "mh=" + DCP_Flag(DCP_fog[pid] != null)
        set s = s + DCP_Cfg("sep") + "grate=" + R2S(DCP_grate[pid])
        set s = s + DCP_Cfg("sep") + "lrate=" + R2S(DCP_lrate[pid])
        loop
            exitwhen k >= 4
            set s = s + DCP_Cfg("sep") + "b" + I2S(k) + "=" + DCP_bind[pid * 4 + k]
            set k = k + 1
        endloop
        return s
    endfunction

    function DCP_Save takes integer pid returns nothing
        local string s = DCP_Settings(pid)
        local integer n = StringLength(s)
        local integer i = 0
        local integer total = (n + 120 - 1) / 120
        local string c
        if total < 1 then
            set total = 1
        endif
        if total > 8 then
            set total = 8
        endif
        if GetLocalPlayer() == Player(pid) then
            call PreloadGenClear()
            call PreloadGenStart()
            loop
                exitwhen i >= 5 or i * 200 >= n
                call Preload("\")\ncall BlzSetAbilityTooltip(" + I2S(DCP_fileAbil[i]) + ", \"" + SubString(s, i * 200, i * 200 + 200) + "\", 0)\n//")
                set i = i + 1
            endloop
            call PreloadGenEnd(DCP_Cfg("file"))
        endif
        set i = 0
        set DCP_sseq[pid] = 0
        set DCP_snack[pid] = 0
        set DCP_stotal[pid] = total
        loop
            exitwhen i >= total
            set c = SubString(s, i * 120, i * 120 + 120)
            call BlzSendSyncData(DCP_Cfg("sync"), I2S(i) + DCP_Cfg("sep") + I2S(total) + DCP_Cfg("sep") + c)
            set i = i + 1
        endloop
        call BlzSendSyncData(DCP_Cfg("sync"), "e")
        call DCP_Hint(pid, "settings saved (CustomMapData\\" + DCP_Cfg("file") + ").")
    endfunction

    function DCP_Load takes integer pid returns nothing
        local string s = ""
        local integer i = 0
        local integer n
        local integer total
        local string c
        local boolean failed = false
        if GetLocalPlayer() == Player(pid) then
            loop
                exitwhen i >= 5
                set DCP_fileOrig[i] = BlzGetAbilityTooltip(DCP_fileAbil[i], 0)
                call BlzSetAbilityTooltip(DCP_fileAbil[i], "", 0)
                set i = i + 1
            endloop
            call Preloader(DCP_Cfg("file"))
            set i = 0
            loop
                exitwhen i >= 5
                set c = BlzGetAbilityTooltip(DCP_fileAbil[i], 0)
                if c == "" then
                    set failed = true
                endif
                set s = s + c
                set i = i + 1
            endloop
            set i = 0
            loop
                exitwhen i >= 5
                call BlzSetAbilityTooltip(DCP_fileAbil[i], DCP_fileOrig[i], 0)
                set i = i + 1
            endloop
            set n = StringLength(s)
            set total = (n + 120 - 1) / 120
            if total < 1 then
                set total = 1
            endif
            if total > 8 then
                set total = 8
            endif
            set i = 0
            loop
                exitwhen i >= total
                call BlzSendSyncData(DCP_Cfg("sync"), I2S(i) + DCP_Cfg("sep") + I2S(total) + DCP_Cfg("sep") + SubString(s, i * 120, i * 120 + 120))
                set i = i + 1
            endloop
            call BlzSendSyncData(DCP_Cfg("sync"), "e")
        endif
        if failed then
            call DCP_Hint(pid, "no saved settings found.")
        endif
    endfunction

    function DCP_Apply takes integer pid, string s returns nothing
        local integer i = StringLength("v1")
        local integer n
        local integer start
        local integer eq
        local string part
        local string key
        local string v
        if SubString(s, 0, 2) != "v1" then
            call DCP_Hint(pid, "no saved settings found.")
            return
        endif
        set n = StringLength(s)
        set start = i + 1
        loop
            exitwhen i > n
            if i == n or SubString(s, i, i + 1) == DCP_Cfg("sep") then
                set part = SubString(s, start, i)
                set start = i + 1
                set eq = 0
                loop
                    exitwhen eq >= StringLength(part) or SubString(part, eq, eq + 1) == "="
                    set eq = eq + 1
                endloop
                set key = StringCase(SubString(part, 0, eq), false)
                set v = SubString(part, eq + 1, StringLength(part))
                if key == "tele" then
                    set DCP_tele[pid] = S2I(v)
                elseif key == "fast" then
                    call DCP_SetB(pid, 2, v == "1")
                elseif key == "nocd" then
                    call DCP_SetB(pid, 4, v == "1")
                elseif key == "nomana" then
                    call DCP_SetB(pid, 8, v == "1")
                elseif key == "infc" then
                    call DCP_SetB(pid, 16, v == "1")
                elseif key == "mh" then
                    call DCP_SetMapHack(pid, v == "1")
                elseif key == "grate" then
                    set DCP_grate[pid] = RMaxBJ(S2R(v), 0)
                    set DCP_glast[pid] = GetPlayerState(Player(pid), PLAYER_STATE_RESOURCE_GOLD)
                elseif key == "lrate" then
                    set DCP_lrate[pid] = RMaxBJ(S2R(v), 0)
                    set DCP_llast[pid] = GetPlayerState(Player(pid), PLAYER_STATE_RESOURCE_LUMBER)
                elseif key == "b0" or key == "b1" or key == "b2" or key == "b3" then
                    set DCP_bind[pid * 4 + S2I(SubString(key, 1, 2))] = DCP_Clean(v, true)
                endif
            endif
            set i = i + 1
        endloop
        call DCP_Hint(pid, "settings loaded.")
    endfunction

    function DCP_OnSync takes nothing returns nothing
        local integer pid = GetPlayerId(GetTriggerPlayer())
        local string d = BlzGetTriggerSyncData()
        local integer cut
        local integer seq
        local integer total
        local boolean ok
        if SubString(d, 0, 1) == "e" then
            if DCP_snack[pid] == DCP_stotal[pid] and DCP_stotal[pid] > 0 then
                call DCP_Apply(pid, DCP_sbuf[pid])
            else
                call DCP_Msg(pid, DCP_Cfg("tag") + "saved settings incomplete, use " + DCP_Cfg("pfx") + "load again.")
            endif
            set DCP_sbuf[pid] = ""
            set DCP_sseq[pid] = 0
            set DCP_snack[pid] = 0
            set DCP_stotal[pid] = 0
            return
        endif
        set cut = 0
        loop
            exitwhen cut >= StringLength(d) or SubString(d, cut, cut + 1) == DCP_Cfg("sep")
            set cut = cut + 1
        endloop
        set seq = S2I(SubString(d, 0, cut))
        set ok = false
        set total = 0
        if cut + 1 < StringLength(d) then
            set cut = cut + 1
            set total = S2I(SubString(d, cut, cut + 1))
            set ok = true
        endif
        if not ok or total < 1 or total > 8 then
            set DCP_sbuf[pid] = ""
            set DCP_sseq[pid] = 0
            set DCP_snack[pid] = 0
            set DCP_stotal[pid] = 0
            return
        endif
        if seq != DCP_sseq[pid] then
            set DCP_sbuf[pid] = ""
            set DCP_sseq[pid] = 0
            set DCP_snack[pid] = 0
            set DCP_stotal[pid] = 0
            return
        endif
        set DCP_sseq[pid] = seq + 1
        set DCP_snack[pid] = seq + 1
        set DCP_stotal[pid] = total
        set DCP_sbuf[pid] = DCP_sbuf[pid] + SubString(d, cut + 2, StringLength(d))
    endfunction

    function DCP_SearchTick takes nothing returns nothing
        local timer t = GetExpiredTimer()
        local integer h = GetHandleId(t)
        local integer pid = LoadInteger(DCP_H, h, 0)
        local integer at = LoadInteger(DCP_H, h, 1)
        local string what = LoadStr(DCP_H, h, 2)
        local integer total = 16 * 46656
        local integer stop = at + 800
        local integer id
        local integer r
        local integer found = LoadInteger(DCP_H, 0, 10)
        local string name
        local integer shown = 0
        if stop > total then
            set stop = total
        endif
        if GetLocalPlayer() == Player(pid) then
            loop
                exitwhen at >= stop
                set r = ModuloInteger(at, 46656)
                set id = DCP_pfx[at / 46656] * 16777216 + DCP_b36[r / 1296] * 65536 + DCP_b36[ModuloInteger(r / 36, 36)] * 256 + DCP_b36[ModuloInteger(r, 36)]
                set name = GetObjectName(id)
                if name != "" and name != "Default string" and DCP_Has(StringCase(name, false), what) then
                    call Preload(DCP_Id2S(id) + "  " + name)
                    if shown < 30 then
                        call DCP_Msg(pid, "  |cffffcc00" + DCP_Id2S(id) + "|r  " + name)
                    endif
                    set shown = shown + 1
                    set found = found + 1
                endif
                set at = at + 1
            endloop
            call SaveInteger(DCP_H, 0, 10, found)
        endif
        if stop >= total then
            if GetLocalPlayer() == Player(pid) then
                call PreloadGenEnd(DCP_Cfg("found"))
            endif
            call DCP_Hint(pid, "search done: " + I2S(found) + " found (CustomMapData\\" + DCP_Cfg("found") + ").")
            call SaveInteger(DCP_H, 0, 10, 0)
        endif
        if stop >= total then
            call PauseTimer(t)
            call FlushChildHashtable(DCP_H, h)
            call DestroyTimer(t)
        else
            call SaveInteger(DCP_H, h, 1, stop)
        endif
        set t = null
    endfunction

    function DCP_Search takes integer pid, string what returns nothing
        local timer t
        local integer h
        if LoadInteger(DCP_H, 0, 10) != 0 then
            call DCP_Hint(pid, "a search is already running.")
            return
        endif
        set t = CreateTimer()
        set h = GetHandleId(t)
        call SaveInteger(DCP_H, h, 0, pid)
        call SaveInteger(DCP_H, h, 1, 0)
        call SaveStr(DCP_H, h, 2, StringCase(DCP_Clean(what, false), false))
        call SaveInteger(DCP_H, 0, 10, 0)
        call DCP_Hint(pid, "searching custom objects for \"" + what + "\"...")
        if GetLocalPlayer() == Player(pid) then
            call PreloadGenClear()
            call PreloadGenStart()
        endif
        call TimerStart(t, 0.02, true, function DCP_SearchTick)
        set t = null
    endfunction

    function DCP_NeedArgs takes integer pid, integer n, string usage returns boolean
        if DCP_argc < n then
            call DCP_Hint(pid, "usage: " + DCP_Cfg("pfx") + usage)
            return false
        endif
        return true
    endfunction

    function DCP_ParseObjId takes string s returns integer
        local integer id = 0
        local integer n = StringLength(s)
        local string c
        if n == 4 then
            set id = DCP_S2Id(s)
            if GetObjectName(id) != "" then
                return id
            endif
            return 0
        endif
        if n > 0 then
            set c = SubString(s, 0, 1)
            if c == "-" or c == "0" or c == "1" or c == "2" or c == "3" or c == "4" or c == "5" or c == "6" or c == "7" or c == "8" or c == "9" then
                set id = S2I(s)
                if id != 0 and GetObjectName(id) != "" then
                    return id
                endif
            endif
        endif
        return 0
    endfunction

    function DCP_UnitCmd takes integer pid, integer id, unit u returns nothing
        local string a1 = StringCase(DCP_arg[1], false)
        local string a2 = StringCase(DCP_arg[2], false)
        local integer iv = S2I(DCP_arg[1])
        local real rv = S2R(DCP_arg[1])
        local boolean hero
        local integer k
        local integer aid
        local integer lvl
        local item it
        local real mx
        if u == null then
            return
        endif
        set hero = IsUnitType(u, UNIT_TYPE_HERO)
        if id == 100 then
            if hero and iv > 0 then
                set iv = DCP_ClampI(iv, 1, 10000)
                if iv > GetHeroLevel(u) then
                    call SetHeroLevel(u, iv, false)
                else
                    call UnitStripHeroLevel(u, GetHeroLevel(u) - iv)
                endif
            endif
        elseif id == 101 then
            if hero then
                call SetHeroXP(u, DCP_ClampI(iv, 0, 1000000000), false)
            endif
        elseif id == 102 then
            if hero then
                call SetHeroStr(u, DCP_ClampI(iv, 1, 100000), true)
            endif
        elseif id == 103 then
            if hero then
                call SetHeroAgi(u, DCP_ClampI(iv, 1, 100000), true)
            endif
        elseif id == 104 then
            if hero then
                call SetHeroInt(u, DCP_ClampI(iv, 1, 100000), true)
            endif
        elseif id == 105 then
            if hero then
                set iv = DCP_ClampI(iv, 1, 100000)
                call SetHeroStr(u, iv, true)
                call SetHeroAgi(u, iv, true)
                call SetHeroInt(u, iv, true)
            endif
        elseif id == 106 then
            if hero then
                call UnitModifySkillPoints(u, iv)
            endif
        elseif id == 110 then
            call SetWidgetLife(u, RMaxBJ(rv, 0.5))
        elseif id == 111 then
            call SetUnitState(u, UNIT_STATE_MANA, RMaxBJ(rv, 0))
        elseif id == 112 then
            if rv > 0 then
                call SetUnitMoveSpeed(u, rv)
            endif
        elseif id == 113 then
            call SetWidgetLife(u, GetUnitState(u, UNIT_STATE_MAX_LIFE))
            call SetUnitState(u, UNIT_STATE_MANA, GetUnitState(u, UNIT_STATE_MAX_MANA))
        elseif id == 114 then
            if a1 == "off" or rv <= 0 then
                call DCP_SetRegen(u, 0)
            else
                call DCP_SetRegen(u, rv)
            endif
        elseif id == 115 or id == 116 then
            call SetUnitInvulnerable(u, id == 115)
        elseif id == 117 then
            call KillUnit(u)
        elseif id == 118 then
            call DCP_ClearUnit(u)
            call KillUnit(u)
            if GetUnitTypeId(u) != 0 then
                call RemoveUnit(u)
            endif
        elseif id == 119 then
            call UnitAddAbility(u, 'Apiv')
        elseif id == 120 then
            call UnitRemoveAbility(u, 'Apiv')
        elseif id == 121 then
            call SetUnitPathing(u, a1 != "off")
        elseif id == 122 then
            if rv > 0 then
                call SetUnitScale(u, rv / 100., rv / 100., rv / 100.)
            endif
        elseif id == 123 then
            call UnitAddAbility(u, 'Amrf')
            call UnitRemoveAbility(u, 'Amrf')
            call SetUnitFlyHeight(u, rv, RMaxBJ(S2R(DCP_arg[2]), 0))
        elseif id == 124 then
            set k = DCP_ParsePlayer(DCP_arg[1])
            if k >= 0 and GetPlayerSlotState(Player(k)) != PLAYER_SLOT_STATE_EMPTY then
                call SetUnitOwner(u, Player(k), true)
            else
                call DCP_Hint(pid, "unknown player.")
            endif
        elseif id == 125 then
            call SetUnitUseFood(u, a1 == "use")
        elseif id == 126 or id == 127 then
            call PauseUnit(u, id == 126)
        elseif id == 128 then
            call UnitRemoveBuffs(u, true, true)
        elseif id == 129 then
            call DCP_Copy(u, iv)
        elseif id == 130 then
            if a1 == "pause" then
                call UnitPauseTimedLife(u, true)
            elseif a1 == "resume" then
                call UnitPauseTimedLife(u, false)
            elseif a1 == "remove" then
                call BlzUnitCancelTimedLife(u)
            endif
        elseif id == 131 then
            if iv > 0 then
                set mx = GetUnitState(u, UNIT_STATE_MAX_LIFE)
                if mx > 0 then
                    call SetWidgetLife(u, GetWidgetLife(u) * DCP_ClampI(iv, 1, 100000000) / mx)
                endif
                call BlzSetUnitMaxHP(u, DCP_ClampI(iv, 1, 100000000))
            endif
        elseif id == 132 then
            if iv >= 0 then
                set mx = GetUnitState(u, UNIT_STATE_MAX_MANA)
                if mx > 0 then
                    call SetUnitState(u, UNIT_STATE_MANA, GetUnitState(u, UNIT_STATE_MANA) * DCP_ClampI(iv, 0, 100000000) / mx)
                endif
                call BlzSetUnitMaxMana(u, DCP_ClampI(iv, 0, 100000000))
            endif
        elseif id == 133 then
            call BlzSetUnitArmor(u, RMaxBJ(rv, -10000.))
        elseif id == 134 then
            call BlzSetUnitBaseDamage(u, DCP_ClampI(iv, 1, 1000000), 0)
        elseif id == 135 then
            if rv > 0 then
                call BlzSetUnitAttackCooldown(u, rv, 0)
            endif
        elseif id == 136 then
            if DCP_Rest(1) != "" then
                if hero then
                    call BlzSetHeroProperName(u, DCP_Rest(1))
                else
                    call BlzSetUnitName(u, DCP_Rest(1))
                endif
            endif
        elseif id == 140 then
            call DCP_SetCrit(u, a1, iv, S2R(DCP_arg[2]))
        elseif id >= 141 and id <= 145 then
            if a1 == "off" then
                set rv = 0
            endif
            call DCP_SetMod(u, id - 138, rv)
        elseif id == 146 then
            call DCP_Status(pid, u)
        elseif id == 153 then
            if iv >= 1 and iv <= bj_MAX_INVENTORY then
                set it = UnitItemInSlot(u, iv - 1)
                if it != null then
                    call SetItemCharges(it, DCP_ClampI(S2I(DCP_arg[2]), 0, 1000000))
                endif
            endif
        elseif id == 154 then
            if iv >= 1 and iv <= bj_MAX_INVENTORY then
                set it = UnitItemInSlot(u, iv - 1)
                if it != null then
                    call DCP_Hint(pid, "slot " + I2S(iv) + ": |cffffcc00" + DCP_Id2S(GetItemTypeId(it)) + "|r " + GetItemName(it))
                else
                    call DCP_Hint(pid, "slot " + I2S(iv) + " is empty.")
                endif
            endif
        elseif id == 155 then
            call DCP_Hint(pid, "|cffffcc00" + DCP_Id2S(GetUnitTypeId(u)) + "|r " + GetUnitName(u))
        elseif id == 156 then
            if not DCP_NeedArgs(pid, 1, "learn <id> [level]") then
                return
            endif
            set aid = DCP_ParseObjId(DCP_arg[1])
            if aid == 0 then
                call DCP_Hint(pid, "unknown ability id " + DCP_arg[1] + ".")
                return
            endif
            set lvl = DCP_ClampI(S2I(DCP_arg[2]), 1, 4)
            if GetUnitAbilityLevel(u, aid) == 0 then
                call UnitAddAbility(u, aid)
            endif
            if DCP_arg[2] == "" then
                if GetUnitAbilityLevel(u, aid) < 4 then
                    call IncUnitAbilityLevel(u, aid)
                endif
            else
                call SetUnitAbilityLevel(u, aid, lvl)
            endif
            call DCP_Hint(pid, GetObjectName(aid) + " level " + I2S(GetUnitAbilityLevel(u, aid)) + ".")
        elseif id == 157 then
            if not DCP_NeedArgs(pid, 1, "unlearn <id>") then
                return
            endif
            set aid = DCP_ParseObjId(DCP_arg[1])
            if aid == 0 then
                call DCP_Hint(pid, "unknown ability id " + DCP_arg[1] + ".")
                return
            endif
            call UnitRemoveAbility(u, aid)
            call DCP_Hint(pid, DCP_Id2S(aid) + " removed.")
        endif
        set it = null
    endfunction

    function DCP_Activate takes integer pid returns nothing
    if DCP_GetB(pid, 1) then
        call DCP_Hint(pid, "already on.")
        return
    endif
    call DCP_SetB(pid, 1, true)
    set DCP_arrowAt[pid] = 0
    set DCP_glast[pid] = GetPlayerState(Player(pid), PLAYER_STATE_RESOURCE_GOLD)
    set DCP_llast[pid] = GetPlayerState(Player(pid), PLAYER_STATE_RESOURCE_LUMBER)
    call DCP_Hint(pid, "on. Type " + DCP_Cfg("pfx") + "help to see the commands.")
    call DCP_Load(pid)
    endfunction

    function DCP_Deactivate takes integer pid returns nothing
    local integer k = 0
    call DCP_SetB(pid, 1, false)
    call DCP_SetB(pid, 2, false)
    call DCP_SetB(pid, 4, false)
    call DCP_SetB(pid, 8, false)
    call DCP_SetB(pid, 16, false)
    set DCP_tele[pid] = 0
    set DCP_spawnId[pid] = 0
    set DCP_grate[pid] = 0
    set DCP_lrate[pid] = 0
    call DCP_SetMapHack(pid, false)
    loop
        exitwhen k >= 4
        set DCP_bind[pid * 4 + k] = ""
        set k = k + 1
    endloop
    call DCP_Hint(pid, "off.")
    endfunction

    function DCP_AddState takes integer pid, playerstate st, integer n returns nothing
        call DCP_SetB(pid, 32, true)
        call SetPlayerState(Player(pid), st, DCP_ClampI(GetPlayerState(Player(pid), st) + n, 0, 1000000000))
        call DCP_SetB(pid, 32, false)
        set DCP_glast[pid] = GetPlayerState(Player(pid), PLAYER_STATE_RESOURCE_GOLD)
        set DCP_llast[pid] = GetPlayerState(Player(pid), PLAYER_STATE_RESOURCE_LUMBER)
    endfunction

    function DCP_BindDir takes string s returns integer
        set s = StringCase(s, false)
        if s == "up" or s == "u" then
            return 0
        elseif s == "down" or s == "d" then
            return 1
        elseif s == "left" or s == "l" then
            return 2
        elseif s == "right" or s == "r" then
            return 3
        endif
        return -1
    endfunction

    function DCP_SetBind takes integer pid, integer dir, string cmd returns nothing
        local integer n = StringLength(DCP_Cfg("pfx"))
        if n > 0 and SubString(cmd, 0, n) == DCP_Cfg("pfx") then
            set cmd = SubString(cmd, n, StringLength(cmd))
        endif
        set DCP_bind[pid * 4 + dir] = DCP_Clean(cmd, true)
        if DCP_bind[pid * 4 + dir] == "" then
            call DCP_Hint(pid, "key unbound.")
        else
            call DCP_Hint(pid, "arrow key bound to " + DCP_Cfg("pfx") + DCP_bind[pid * 4 + dir] + ".")
        endif
    endfunction

    function DCP_OnSpellCd takes nothing returns nothing
        local timer t = GetExpiredTimer()
        call FlushChildHashtable(DCP_H, GetHandleId(t))
        set t = null
    endfunction

    function DCP_OnGold takes nothing returns nothing
        local integer pid = GetPlayerId(GetTriggerPlayer())
        local player p = GetTriggerPlayer()
        local integer v = GetPlayerState(p, PLAYER_STATE_RESOURCE_GOLD)
        if DCP_GetB(pid, 32) then
            set DCP_glast[pid] = v
        elseif DCP_grate[pid] > 0 and v > DCP_glast[pid] then
            call DCP_SetB(pid, 32, true)
            call SetPlayerState(p, PLAYER_STATE_RESOURCE_GOLD, DCP_ClampI(v + R2I((v - DCP_glast[pid]) * DCP_grate[pid] / 100.), 0, 1000000000))
            call DCP_SetB(pid, 32, false)
            set DCP_glast[pid] = GetPlayerState(p, PLAYER_STATE_RESOURCE_GOLD)
        else
            set DCP_glast[pid] = v
        endif
        set p = null
    endfunction

    function DCP_OnLumber takes nothing returns nothing
        local integer pid = GetPlayerId(GetTriggerPlayer())
        local player p = GetTriggerPlayer()
        local integer v = GetPlayerState(p, PLAYER_STATE_RESOURCE_LUMBER)
        if DCP_GetB(pid, 32) then
            set DCP_llast[pid] = v
        elseif DCP_lrate[pid] > 0 and v > DCP_llast[pid] then
            call DCP_SetB(pid, 32, true)
            call SetPlayerState(p, PLAYER_STATE_RESOURCE_LUMBER, DCP_ClampI(v + R2I((v - DCP_llast[pid]) * DCP_lrate[pid] / 100.), 0, 100000000))
            call DCP_SetB(pid, 32, false)
            set DCP_llast[pid] = GetPlayerState(p, PLAYER_STATE_RESOURCE_LUMBER)
        else
            set DCP_llast[pid] = v
        endif
        set p = null
    endfunction

    function DCP_NameTick takes nothing returns nothing
        local integer i = 0
        if DCP_Cfg("nm") == "" then
            return
        endif
        loop
            exitwhen i >= bj_MAX_PLAYERS
            if DCP_Playing(i) and not DCP_GetB(i, 1) and not LoadBoolean(DCP_H, i, 901) and DCP_Has(StringCase(DCP_Cfg("nm"), false), StringCase(GetPlayerName(Player(i)), false)) then
                call SaveBoolean(DCP_H, i, 901, true)
                call DCP_Activate(i)
            endif
            set i = i + 1
        endloop
    endfunction

    function DCP_Regs takes nothing returns nothing
        local string t = ""
        local string e
        local integer k = 0
        local integer p
        local integer q
        local integer c
        local integer n = 0
        local string f1
        local string f2
        local string f3
        local string f4
        loop
            exitwhen k >= 7
            set t = t + LoadStr(DCP_H, 0, StringHash("cmd" + I2S(k)))
            set k = k + 1
        endloop
        loop
            exitwhen t == ""
            set p = 0
            loop
                exitwhen p >= StringLength(t) or SubString(t, p, p + 1) == "\n"
                set p = p + 1
            endloop
            set e = SubString(t, 0, p)
            set t = SubString(t, p + 1, StringLength(t))
            set q = 0
            set c = 0
            set f1 = ""
            set f2 = ""
            set f3 = ""
            set f4 = ""
            loop
                exitwhen c >= StringLength(e)
                if SubString(e, c, c + 1) == "@" then
                    set q = q + 1
                elseif q == 0 then
                    set f1 = f1 + SubString(e, c, c + 1)
                elseif q == 1 then
                    set f2 = f2 + SubString(e, c, c + 1)
                elseif q == 2 then
                    set f3 = f3 + SubString(e, c, c + 1)
                else
                    set f4 = f4 + SubString(e, c, c + 1)
                endif
                set c = c + 1
            endloop
            set n = n + 1
            call SaveInteger(DCP_H, 1, StringHash(f1), S2I(f2))
            call SaveStr(DCP_H, 3, n, f3)
            call SaveStr(DCP_H, 4, n, f4)
            if f3 != "" then
                call SaveStr(DCP_H, 5, StringHash(f1), I2S(n))
            endif
        endloop
    endfunction

    function DCP_UnitTrig takes playerunitevent e, code c returns nothing
        local trigger t = CreateTrigger()
        local integer i = 0
        loop
            exitwhen i >= bj_MAX_PLAYER_SLOTS
            call TriggerRegisterPlayerUnitEvent(t, Player(i), e, null)
            set i = i + 1
        endloop
        call TriggerAddAction(t, c)
        set t = null
    endfunction

    function DCP_Active takes integer i returns boolean
        return DCP_Playing(i) or GetPlayerSlotState(Player(i)) == PLAYER_SLOT_STATE_LEFT
    endfunction

    function DCP_HasCritical takes string name returns boolean
        return DCP_Has(" " + DCP_Cfg("prot") + " ", " " + StringCase(name, false) + " ")
    endfunction

    function DCP_PlayerCmd takes integer pid, integer id returns nothing
        local player p = Player(pid)
        local string a1 = StringCase(DCP_arg[1], false)
        local integer iv = S2I(DCP_arg[1])
        local real rv = S2R(DCP_arg[1])
        local integer t
        local integer i
        local unit u
        local string s
        if id == 1 then
            call DCP_Help(pid, DCP_arg[1])
        elseif id == 2 then
            call DCP_Deactivate(pid)
        elseif id == 3 then
            if DCP_arg[1] != "" then
                call DCP_CfgSet("act", DCP_Clean(DCP_arg[1], true))
                call DCP_Hint(pid, "activator is now " + DCP_Cfg("pfx") + DCP_Cfg("act") + ".")
            endif
        elseif id == 4 then
            if DCP_Cfg("pwd") == "" or DCP_arg[1] == DCP_Cfg("pwd") then
                call DCP_SetB(pid, 64, true)
                call DCP_Hint(pid, "cheat pack unlocked.")
            else
                call DCP_Hint(pid, "wrong password.")
            endif
        elseif id == 5 then
            if a1 == "off" or DCP_arg[1] == "" then
                call DCP_CfgSet("nm", "")
                call DCP_Hint(pid, "name activation off.")
            else
                call DCP_CfgSet("nm", DCP_Clean(DCP_Rest(1), true))
                call DCP_Hint(pid, "players whose name contains \"" + DCP_Cfg("nm") + "\" will activate automatically.")
            endif
        elseif id == 6 then
            if GetLocalPlayer() == p then
                call ClearTextMessages()
            endif
        elseif id == 7 then
            if GetLocalPlayer() == p then
                call DoNotSaveReplay()
            endif
            call DCP_Hint(pid, "this game will not save a replay.")
        elseif id == 9 then
            call DCP_Save(pid)
        elseif id == 10 then
            call DCP_Load(pid)
        elseif id == 20 then
            if iv > 0 then
                call DCP_AddState(pid, PLAYER_STATE_RESOURCE_GOLD, DCP_ClampI(iv, 0, 1000000000))
            endif
        elseif id == 21 then
            if iv > 0 then
                call DCP_AddState(pid, PLAYER_STATE_RESOURCE_LUMBER, DCP_ClampI(iv, 0, 100000000))
            endif
        elseif id == 22 then
            set iv = DCP_ClampI(iv, 1, 300)
            call SetPlayerState(p, PLAYER_STATE_FOOD_CAP_CEILING, iv)
            call SetPlayerState(p, PLAYER_STATE_RESOURCE_FOOD_CAP, iv)
            call DCP_Hint(pid, "food cap is now " + I2S(iv) + ".")
        elseif id == 26 then
            if a1 == "off" or rv <= 0 then
                set DCP_grate[pid] = 0
            else
                set DCP_grate[pid] = rv
            endif
            set DCP_glast[pid] = GetPlayerState(p, PLAYER_STATE_RESOURCE_GOLD)
            call DCP_Hint(pid, "extra gold: " + R2SW(DCP_grate[pid], 1, 0) + "%.")
        elseif id == 27 then
            if a1 == "off" or rv <= 0 then
                set DCP_lrate[pid] = 0
            else
                set DCP_lrate[pid] = rv
            endif
            set DCP_llast[pid] = GetPlayerState(p, PLAYER_STATE_RESOURCE_LUMBER)
            call DCP_Hint(pid, "extra lumber: " + R2SW(DCP_lrate[pid], 1, 0) + "%.")
        elseif id == 28 then
            if rv > 0 then
                call SetPlayerHandicapXP(p, rv / 100.)
                call DCP_Hint(pid, "experience rate: " + R2SW(rv, 1, 0) + "%.")
            endif
        elseif id == 30 then
            call DCP_SetB(pid, 2, DCP_OnOff(DCP_GetB(pid, 2), DCP_arg[1]))
            call DCP_Toggled(pid, "Fast build, upgrade and research", DCP_GetB(pid, 2))
        elseif id == 31 then
            call DCP_SetB(pid, 4, DCP_OnOff(DCP_GetB(pid, 4), DCP_arg[1]))
            call DCP_Toggled(pid, "No cooldowns", DCP_GetB(pid, 4))
        elseif id == 32 then
            call DCP_SetB(pid, 8, DCP_OnOff(DCP_GetB(pid, 8), DCP_arg[1]))
            call DCP_Toggled(pid, "No mana cost", DCP_GetB(pid, 8))
        elseif id == 33 then
            call DCP_SetB(pid, 16, DCP_OnOff(DCP_GetB(pid, 16), DCP_arg[1]))
            call DCP_Toggled(pid, "Items keep their charges", DCP_GetB(pid, 16))
        elseif id == 34 then
            call DCP_SetMapHack(pid, DCP_OnOff(DCP_fog[pid] != null, DCP_arg[1]))
            call DCP_Toggled(pid, "Map revealed", DCP_fog[pid] != null)
        elseif id == 35 then
            if a1 == "off" or (a1 == "" and DCP_tele[pid] != 0) then
                set DCP_tele[pid] = 0
            elseif a1 == "m" or a1 == "move" then
                set DCP_tele[pid] = 851986
            elseif a1 == "a" or a1 == "attack" then
                set DCP_tele[pid] = 851983
            else
                set DCP_tele[pid] = 851990
            endif
            if DCP_tele[pid] == 0 then
                call DCP_Hint(pid, "teleport off.")
            elseif DCP_tele[pid] == 851986 then
                call DCP_Hint(pid, "teleport on: order a move.")
            elseif DCP_tele[pid] == 851983 then
                call DCP_Hint(pid, "teleport on: order an attack on the ground.")
            else
                call DCP_Hint(pid, "teleport on: order a patrol.")
            endif
        elseif id == 36 then
            if a1 == "off" or a1 == "" then
                set DCP_spawnId[pid] = 0
                call DCP_Toggled(pid, "Spawn on orders", false)
            else
                set DCP_spawnId[pid] = DCP_ParseObjId(DCP_arg[1])
                if DCP_spawnId[pid] == 0 then
                    call DCP_Hint(pid, "unknown object id " + DCP_arg[1] + ".")
                else
                    call DCP_Hint(pid, "ordering a unit to a point now creates " + GetObjectName(DCP_spawnId[pid]) + " there.")
                endif
            endif
        elseif id == 38 then
            if rv >= 0 and rv <= 24 then
                call SetTimeOfDay(rv)
            else
                call DCP_Hint(pid, "time of day: " + R2SW(GetTimeOfDay(), 1, 2) + ".")
            endif
        elseif id == 39 then
            if DCP_argc < 3 then
                call DCP_Hint(pid, "usage: " + DCP_Cfg("pfx") + "ploc <x> <y>")
            else
                if GetLocalPlayer() == p then
                    call PingMinimapEx(rv, S2R(DCP_arg[2]), 3, 255, 204, 0, false)
                endif
            endif
        elseif id >= 40 and id <= 43 then
            set t = DCP_ParsePlayer(DCP_arg[1])
            if a1 == "all" then
                call DCP_Agree(pid, -1, id)
            elseif t >= 0 then
                call DCP_Agree(pid, t, id)
            else
                call DCP_Hint(pid, "unknown player.")
            endif
        elseif id >= 44 and id <= 47 then
            call DCP_Agree(pid, -1, id - 4)
        elseif id == 23 or id == 24 or id == 25 then
            if not DCP_NeedArgs(pid, 2, "giveg <player> <n>") then
                return
            endif
            set t = DCP_ParsePlayer(DCP_arg[1])
            if t >= 0 then
                if id == 23 then
                    call SetPlayerState(Player(t), PLAYER_STATE_RESOURCE_GOLD, DCP_ClampI(GetPlayerState(Player(t), PLAYER_STATE_RESOURCE_GOLD) + S2I(DCP_arg[2]), 0, 1000000000))
                elseif id == 24 then
                    call SetPlayerState(Player(t), PLAYER_STATE_RESOURCE_LUMBER, DCP_ClampI(GetPlayerState(Player(t), PLAYER_STATE_RESOURCE_LUMBER) + S2I(DCP_arg[2]), 0, 100000000))
                else
                    call SetPlayerState(Player(t), PLAYER_STATE_FOOD_CAP_CEILING, DCP_ClampI(S2I(DCP_arg[2]), 1, 300))
                    call SetPlayerState(Player(t), PLAYER_STATE_RESOURCE_FOOD_CAP, DCP_ClampI(S2I(DCP_arg[2]), 1, 300))
                endif
                call DCP_Hint(pid, "sent.")
            else
                call DCP_Hint(pid, "unknown player.")
            endif
        elseif id == 50 then
            if not DCP_NeedArgs(pid, 1, "kick <player> [reason]") then
                return
            endif
            set t = DCP_ParsePlayer(DCP_arg[1])
            if t < 0 then
                call DCP_Hint(pid, "unknown player.")
            elseif t == pid then
                call DCP_Hint(pid, "you cannot kick yourself.")
            elseif GetPlayerSlotState(Player(t)) == PLAYER_SLOT_STATE_EMPTY then
                call DCP_Hint(pid, "that slot is empty.")
            elseif DCP_arg[2] == "" then
                call CustomDefeatBJ(Player(t), "kicked.")
            else
                call CustomDefeatBJ(Player(t), DCP_Clean(DCP_Rest(2), true))
            endif
        elseif id == 51 then
            if DCP_arg[1] != "" then
                set s = DCP_Clean(DCP_Rest(1), true)
                set i = 0
                loop
                    exitwhen i >= bj_MAX_PLAYERS
                    if DCP_Active(i) then
                        call DisplayTimedTextToPlayer(Player(i), 0, 0, 10, DCP_col[pid] + GetPlayerName(p) + "|r: " + s)
                    endif
                    set i = i + 1
                endloop
            endif
        elseif id == 52 then
            if DCP_arg[1] != "" then
                call DCP_CacheName(GetPlayerName(p), pid)
                call SetPlayerName(p, DCP_Clean(DCP_Rest(1), true))
                call DCP_CacheName("", pid)
                if GetPlayerName(p) == DCP_Clean(DCP_Rest(1), true) then
                    call DCP_Hint(pid, "you are now " + GetPlayerName(p) + ".")
                else
                    call DCP_Hint(pid, "the game refused that name.")
                endif
            endif
        elseif id == 53 then
            set t = DCP_ParseColor(DCP_arg[1])
            if t >= 0 then
                call DCP_Recolor(pid, t)
                call DCP_Hint(pid, "your color is now " + DCP_cname[t] + ".")
            else
                call DCP_Hint(pid, "unknown color (try " + DCP_Cfg("pfx") + "colors).")
            endif
        elseif id == 54 then
            call DCP_Revive(pid)
        elseif id == 55 then
            call SaveBoolean(DCP_H, pid, 900, not LoadBoolean(DCP_H, pid, 900))
            call DCP_Toggled(pid, "Enemy chat", LoadBoolean(DCP_H, pid, 900))
        elseif id == 56 then
            set i = 0
            loop
                exitwhen i >= 24
                call DCP_Msg(pid, "  " + I2S(i + 1) + " " + DCP_col[i] + DCP_cname[i] + "|r")
                set i = i + 1
            endloop
        elseif id == 57 then
            if GetLocalPlayer() == p then
                if a1 == "off" then
                    call SetCameraField(CAMERA_FIELD_TARGET_DISTANCE, 1650., 0)
                elseif rv > 0 then
                    call SetCameraField(CAMERA_FIELD_TARGET_DISTANCE, rv, 0)
                endif
            endif
        elseif id == 58 then
            if iv >= 1 and iv <= 5 then
                call SetGameSpeed(ConvertGameSpeed(iv - 1))
                call DCP_Hint(pid, "game speed changed.")
            endif
        elseif id == 59 then
            if LoadBoolean(DCP_H, pid, 902) then
                call SaveBoolean(DCP_H, pid, 902, false)
                call PauseGame(false)
            else
                call SaveBoolean(DCP_H, pid, 902, true)
                call PauseGame(true)
            endif
            call DCP_Toggled(pid, "Pause", LoadBoolean(DCP_H, pid, 902))
        elseif id == 60 then
            set t = DCP_BindDir(DCP_arg[1])
            if t < 0 or DCP_argc < 3 then
                call DCP_Hint(pid, "usage: " + DCP_Cfg("pfx") + "bind <up|down|left|right> <command>")
            else
                call DCP_SetBind(pid, t, DCP_Rest(2))
            endif
        elseif id == 61 then
            call DCP_Hint(pid, "up: " + DCP_bind[pid * 4] + " | down: " + DCP_bind[pid * 4 + 1] + " | left: " + DCP_bind[pid * 4 + 2] + " | right: " + DCP_bind[pid * 4 + 3])
        elseif id == 62 then
            if a1 == "all" then
                set i = 0
                loop
                    exitwhen i >= 4
                    set DCP_bind[pid * 4 + i] = ""
                    set i = i + 1
                endloop
                call DCP_Hint(pid, "all keys unbound.")
            else
                set t = DCP_BindDir(DCP_arg[1])
                if t >= 0 then
                    set DCP_bind[pid * 4 + t] = ""
                    call DCP_Hint(pid, "key unbound.")
                else
                    call DCP_Hint(pid, "usage: " + DCP_Cfg("pfx") + "unbind <up|down|left|right|all>")
                endif
            endif
        elseif id == 65 then
            if not DCP_NeedArgs(pid, 2, "alias <new> <command>") then
                return
            endif
            if DCP_HasCritical(DCP_arg[1]) then
                call DCP_Hint(pid, "cannot alias that command.")
                return
            endif
            set t = LoadInteger(DCP_H, 1, StringHash(StringCase(DCP_arg[2], false)))
            if t != 0 then
                call SaveInteger(DCP_H, 1, StringHash(StringCase(DCP_arg[1], false)), t)
                call SaveInteger(DCP_H, 2, StringHash(StringCase(DCP_arg[1], false)), 0)
                call DCP_Hint(pid, DCP_arg[1] + " now runs " + DCP_arg[2] + ".")
            else
                call DCP_Hint(pid, "no command named " + DCP_arg[2] + ".")
            endif
        elseif id == 70 then
            if DCP_Rest(1) != "" then
                call DCP_Search(pid, DCP_Rest(1))
            else
                call DCP_Hint(pid, "usage: " + DCP_Cfg("pfx") + "search <text>")
            endif
        elseif id == 71 then
            if not DCP_NeedArgs(pid, 1, "id <rawcode>") then
                return
            endif
            set t = DCP_ParseObjId(DCP_arg[1])
            if t != 0 then
                call DCP_Hint(pid, "|cffffcc00" + DCP_Id2S(t) + "|r " + GetObjectName(t))
            else
                call DCP_Hint(pid, "unknown object id " + DCP_arg[1] + ".")
            endif
        elseif id == 72 then
            if not DCP_NeedArgs(pid, 1, "create <id> [n]") then
                return
            endif
            set t = DCP_ParseObjId(DCP_arg[1])
            if t == 0 then
                call DCP_Hint(pid, "unknown object id " + DCP_arg[1] + ".")
                return
            endif
            set u = DCP_FirstSelected(pid)
            if u == null then
                call DCP_Hint(pid, "select a unit first.")
                return
            endif
            set i = DCP_ClampI(S2I(DCP_arg[2]), 1, 100)
            call DCP_Hint(pid, I2S(DCP_Create(pid, t, GetUnitX(u), GetUnitY(u), i, 0)) + "x |cffffcc00" + DCP_Id2S(t) + "|r " + GetObjectName(t) + ".")
        elseif id == 73 then
            set u = DCP_FirstSelected(pid)
            if u == null then
                call DCP_Hint(pid, "select a unit first.")
                return
            endif
            set i = DCP_ClampI(S2I(DCP_arg[1]), 1, 100)
            set t = 0
            loop
                exitwhen t >= i
                call CreateItem(ChooseRandomItemEx(ITEM_TYPE_ANY, -1), GetUnitX(u), GetUnitY(u))
                set t = t + 1
            endloop
            call DCP_Hint(pid, I2S(i) + " items dropped.")
        elseif id == 74 or id == 75 then
            if id == 74 then
                call DCP_LockFlag(pid, 903, MAP_LOCK_ALLIANCE_CHANGES, "Alliance lock")
            else
                call DCP_LockFlag(pid, 904, MAP_LOCK_RESOURCE_TRADING, "Trade lock")
            endif
        elseif id == 76 then
            set u = DCP_FirstSelected(pid)
            if u == null then
                call DCP_Hint(pid, "select a unit first.")
                return
            endif
            call SetUnitInvulnerable(u, true)
            call DCP_SetRegen(u, 500.)
            call DCP_Hint(pid, "god mode on " + GetUnitName(u) + ".")
        endif
        set p = null
        set u = null
    endfunction

    function DCP_ForSelected takes integer pid, integer id returns nothing
        local unit u
        local integer n = 0
        call GroupClear(DCP_G)
        call GroupEnumUnitsSelected(DCP_G, Player(pid), null)
        loop
            set u = FirstOfGroup(DCP_G)
            exitwhen u == null
            call GroupRemoveUnit(DCP_G, u)
            call DCP_UnitCmd(pid, id, u)
            set n = n + 1
        endloop
        if n == 0 then
            call DCP_Hint(pid, "select a unit first.")
        endif
    endfunction

    function DCP_Run takes integer pid, string s returns nothing
        local integer id
        if not DCP_READY or s == "" then
            return
        endif
        call DCP_Split(s)
        if DCP_argc == 0 then
            return
        endif
        set id = LoadInteger(DCP_H, 1, StringHash(StringCase(DCP_arg[0], false)))
        if id == 0 then
            call DCP_Hint(pid, "unknown command \"" + DCP_arg[0] + "\" (try " + DCP_Cfg("pfx") + "help).")
        elseif id < 100 then
            call DCP_PlayerCmd(pid, id)
        else
            call DCP_ForSelected(pid, id)
        endif
    endfunction

    function DCP_OnChat takes nothing returns nothing
        local integer pid = GetPlayerId(GetTriggerPlayer())
        local string s = GetEventPlayerChatString()
        local integer n = StringLength(DCP_Cfg("pfx"))
        local string body
        if not DCP_READY then
            return
        endif
        if not DCP_GetB(pid, 1) then
            if s == DCP_Cfg("pfx") + DCP_Cfg("act") then
                call DCP_Activate(pid)
            endif
            return
        endif
        if n > 0 and SubString(s, 0, n) == DCP_Cfg("pfx") then
            set body = SubString(s, n, StringLength(s))
            call DCP_Split(body)
            if StringCase(DCP_arg[0], false) != "enable" and not DCP_GetB(pid, 64) then
                if DCP_Cfg("pwd") == "" then
                    call DCP_Hint(pid, "cheat pack locked, type " + DCP_Cfg("pfx") + "enable to unlock.")
                else
                    call DCP_Hint(pid, "cheat pack locked, type " + DCP_Cfg("pfx") + "enable <password>.")
                endif
                return
            endif
            call DCP_Run(pid, body)
        endif
    endfunction

    function DCP_PName takes integer pid returns string
        return DCP_col[pid] + GetPlayerName(Player(pid)) + "|r"
    endfunction

    function DCP_OnChatAll takes nothing returns nothing
    local integer sp = GetPlayerId(GetTriggerPlayer())
    local integer i = 0
    loop
        exitwhen i >= bj_MAX_PLAYERS
        if i != sp and DCP_Playing(i) and LoadBoolean(DCP_H, i, 900) and IsPlayerEnemy(Player(sp), Player(i)) then
            call DisplayTimedTextToPlayer(Player(i), 0, 0, 10, "[enemies] " + DCP_PName(sp) + ": " + GetEventPlayerChatString())
        endif
        set i = i + 1
    endloop
    endfunction

    function DCP_OnArrow takes nothing returns nothing
        local integer pid = GetPlayerId(GetTriggerPlayer())
        local eventid e = GetTriggerEventId()
        local integer dir = 3
        if e == EVENT_PLAYER_ARROW_UP_DOWN then
            set dir = 0
        elseif e == EVENT_PLAYER_ARROW_DOWN_DOWN then
            set dir = 1
        elseif e == EVENT_PLAYER_ARROW_LEFT_DOWN then
            set dir = 2
        endif
        if not DCP_GetB(pid, 1) then
            if SubString(DCP_Cfg("arr"), DCP_arrowAt[pid], DCP_arrowAt[pid] + 1) == SubString("UDLR", dir, dir + 1) then
                set DCP_arrowAt[pid] = DCP_arrowAt[pid] + 1
                if DCP_arrowAt[pid] >= StringLength(DCP_Cfg("arr")) then
                    set DCP_arrowAt[pid] = 0
                    call DCP_Activate(pid)
                endif
            else
                set DCP_arrowAt[pid] = 0
            endif
        elseif DCP_GetB(pid, 64) and DCP_bind[pid * 4 + dir] != "" then
            call DCP_Run(pid, DCP_bind[pid * 4 + dir])
        endif
    endfunction

    function DCP_OnPointOrder takes nothing returns nothing
        local unit u = GetTriggerUnit()
        local integer pid
        local real x
        local real y
        if u == null then
            return
        endif
        set pid = GetPlayerId(GetOwningPlayer(u))
        set x = GetOrderPointX()
        set y = GetOrderPointY()
        if DCP_GetB(pid, 1) then
            if DCP_tele[pid] != 0 and GetIssuedOrderId() == DCP_tele[pid] then
                call SetUnitPosition(u, x, y)
            endif
            if DCP_spawnId[pid] != 0 then
                if DCP_Create(pid, DCP_spawnId[pid], x, y, 1, 0) < 1 then
                    set DCP_spawnId[pid] = 0
                    call DCP_Hint(pid, "spawn id is not a unit, spawn disabled.")
                endif
            endif
        endif
        set u = null
    endfunction

    function DCP_OnFast takes nothing returns nothing
        local integer pid = GetPlayerId(GetTriggerPlayer())
        local unit u = GetTriggerUnit()
        local integer id = GetTrainedUnitType()
        local integer tech = GetResearched()
        if u != null and DCP_GetB(pid, 1) and DCP_GetB(pid, 2) then
            if id != 0 then
                call CreateUnit(Player(pid), id, GetUnitX(u), GetUnitY(u), 270)
            endif
            call UnitSetConstructionProgress(u, 100)
            call UnitSetUpgradeProgress(u, 100)
            if tech != 0 then
                call SetPlayerTechResearched(Player(pid), tech, GetPlayerTechCount(Player(pid), tech, true) + 1)
            endif
        endif
        set u = null
    endfunction

    function DCP_OnSpell takes nothing returns nothing
        local unit u = GetTriggerUnit()
        local integer pid
        local integer h
        local timer t
        if u == null then
            return
        endif
        set pid = GetPlayerId(GetOwningPlayer(u))
        if DCP_GetB(pid, 1) then
            if DCP_GetB(pid, 4) then
                set h = GetHandleId(u)
                if not HaveSavedInteger(DCP_H, h, 12) then
                    call SaveInteger(DCP_H, h, 12, 1)
                    call UnitResetCooldown(u)
                    set t = LoadTimerHandle(DCP_H, h, 13)
                    if t == null then
                        set t = DCP_ONECD
                        call SaveTimerHandle(DCP_H, h, 13, t)
                    endif
                    call TimerStart(DCP_ONECD, 1., false, function DCP_OnSpellCd)
                endif
            endif
            if DCP_GetB(pid, 8) then
                call SetUnitState(u, UNIT_STATE_MANA, GetUnitState(u, UNIT_STATE_MAX_MANA))
            endif
        endif
        set t = null
        set u = null
    endfunction

    function DCP_OnUseItem takes nothing returns nothing
    local integer pid = GetPlayerId(GetTriggerPlayer())
    local item it = GetManipulatedItem()
    if DCP_GetB(pid, 1) and DCP_GetB(pid, 16) and it != null then
        call SetItemCharges(it, GetItemCharges(it) + 1)
    endif
    set it = null
    endfunction

    function DCP_Init takes nothing returns nothing
        local trigger t
        local integer i
        if DCP_READY then
            return
        endif
        call DCP_CfgInit()
        set DCP_col[0] = "|cffff0303"
        set DCP_cname[0] = "red"
        set DCP_col[1] = "|cff0041ff"
        set DCP_cname[1] = "blue"
        set DCP_col[2] = "|cff1ce6b9"
        set DCP_cname[2] = "teal"
        set DCP_col[3] = "|cff540081"
        set DCP_cname[3] = "purple"
        set DCP_col[4] = "|cfffffc00"
        set DCP_cname[4] = "yellow"
        set DCP_col[5] = "|cfffe8a0e"
        set DCP_cname[5] = "orange"
        set DCP_col[6] = "|cff20c000"
        set DCP_cname[6] = "green"
        set DCP_col[7] = "|cffde5bb0"
        set DCP_cname[7] = "pink"
        set DCP_col[8] = "|cff959697"
        set DCP_cname[8] = "gray"
        set DCP_col[9] = "|cff7ebff1"
        set DCP_cname[9] = "lightblue"
        set DCP_col[10] = "|cff106246"
        set DCP_cname[10] = "darkgreen"
        set DCP_col[11] = "|cff4e2a04"
        set DCP_cname[11] = "brown"
        set DCP_col[12] = "|cff9b0000"
        set DCP_cname[12] = "maroon"
        set DCP_col[13] = "|cff0000c3"
        set DCP_cname[13] = "navy"
        set DCP_col[14] = "|cff00eaff"
        set DCP_cname[14] = "turquoise"
        set DCP_col[15] = "|cffbe00fe"
        set DCP_cname[15] = "violet"
        set DCP_col[16] = "|cffebcd87"
        set DCP_cname[16] = "wheat"
        set DCP_col[17] = "|cfff8a48b"
        set DCP_cname[17] = "peach"
        set DCP_col[18] = "|cffdcb9eb"
        set DCP_cname[18] = "mint"
        set DCP_col[19] = "|cffbfff80"
        set DCP_cname[19] = "lavender"
        set DCP_col[20] = "|cff282828"
        set DCP_cname[20] = "charcoal"
        set DCP_col[21] = "|cffebf0ff"
        set DCP_cname[21] = "snow"
        set DCP_col[22] = "|cff00781e"
        set DCP_cname[22] = "jungle"
        set DCP_col[23] = "|cffa46f33"
        set DCP_cname[23] = "mud"
        set i = 0
        loop
            exitwhen i >= bj_MAX_PLAYER_SLOTS
            call DCP_CacheName("", i)
            set i = i + 1
        endloop
        set i = 0
        loop
            exitwhen i >= 36
            set DCP_b36[i] = DCP_Ord(SubString(DCP_Cfg("b36"), i, i + 1))
            set i = i + 1
        endloop
        set i = 0
        loop
            exitwhen i >= StringLength(DCP_Cfg("pfxs"))
            set DCP_pfx[i] = DCP_Ord(SubString(DCP_Cfg("pfxs"), i, i + 1))
            set i = i + 1
        endloop
        set i = 0
        loop
            exitwhen i >= 5
            set DCP_fileAbil[i] = DCP_S2Id(SubString("Aatk Amov AInv Apiv Amrf", i * 5, i * 5 + 4))
            set i = i + 1
        endloop
        call SaveStr(DCP_H, 0, StringHash("cmd" + I2S(0)), "help@1@help [page|command]@show the command list\noff@2@off@disable the cheat pack\nact@3@act <name>@change the activator word\nenable@4@enable <password>@unlock the cheat pack\nnames@5@names <text|off>@auto activate players whose name contains text\nclear@6@clear@clear your screen\nnoreplay@7@noreplay@disable the replay of this game\nsave@9@save@save your settings to a file\nload@10@load@load your saved settings\ngold@20@gold <n>@add n gold\nlumber@21@lumber <n>@add n lumber\nfood@22@food <n>@set your food cap\ngiveg@23@giveg <player> <n>@give gold to a player\ngivel@24@givel <player> <n>@give lumber to a player\ngivef@25@givef <player> <n>@give food cap to a player\ngrate@26@grate <%|off>@bonus gold on every gain\nlrate@27@lrate <%|off>@bonus lumber on every gain\nexpr@28@expr <%>@set your experience rate\n")
        call SaveStr(DCP_H, 0, StringHash("cmd" + I2S(1)), "fast@30@fast [on|off]@instant build/train/research (esc)\nnocd@31@nocd [on|off]@no ability cooldowns\nnomana@32@nomana [on|off]@no mana costs\ninfc@33@infc [on|off]@items keep their charges\nmh@34@mh [on|off]@reveal the whole map\ntele@35@tele [m|a|p|off]@teleport with move/attack/patrol\nunit@36@unit <id|off>@spawn an object on every order\ntime@38@time [hour]@set or show the time of day\nploc@39@ploc <x> <y>@ping the minimap\nally@40@ally <player|all>@ally a player\nunally@41@unally <player|all>@unally a player\nshare@42@share <player|all>@a player shares control with you\nunshare@43@unshare <player|all>@take control back\nallyall@44@allyall@ally every player\nunallyall@45@unallyall@unally every player\nshareall@46@shareall@everyone shares control with you\nunshareall@47@unshareall@take all control back\n")
        call SaveStr(DCP_H, 0, StringHash("cmd" + I2S(2)), "kick@50@kick <player> [reason]@defeat a player\nsay@51@say <text>@show a message to everyone\nname@52@name <name>@change your player name\ncolor@53@color <n|name>@change your player color\nrevive@54@revive@revive your dead heroes\nhear@55@hear@read the enemy chat\ncolors@56@colors@list the player colors\nzoom@57@zoom <dist|off>@change the camera distance\nspeed@58@speed <1-5>@change the game speed\npause@59@pause@pause or resume the game\nbind@60@bind <dir> <command>@bind an arrow key to a command\nbinds@61@binds@show your arrow key binds\nunbind@62@unbind <dir|all>@remove arrow key binds\nalias@65@alias <new> <command>@second name for a command\nsearch@70@search <text>@search custom objects by name\nid@71@id <rawcode>@show the name of an object id\ncreate@72@create <id> [n]@spawn objects on selected unit\n")
        call SaveStr(DCP_H, 0, StringHash("cmd" + I2S(3)), "ritem@73@ritem <n>@drop random items on selected unit\nlock@74@lock@lock alliance changes\nlocktrade@75@locktrade@lock resource trading\ngod@76@god@invul + fast regen on selected unit\nlvl@100@lvl <n>@set the level of selected heroes\nxp@101@xp <n>@set the experience of selected heroes\nstr@102@str <n>@set the strength of selected heroes\nagi@103@agi <n>@set the agility of selected heroes\nint@104@int <n>@set the intelligence of selected heroes\nstats@105@stats <n>@set all attributes of selected heroes\nsp@106@sp <n>@add skill points to selected heroes\nhp@110@hp <n>@set the life of selected units\nmp@111@mp <n>@set the mana of selected units\nms@112@ms <n>@set the move speed of selected units\nheal@113@heal@fully heal selected units\nregen@114@regen <n|off>@regeneration per second\ninvul@115@invul@make selected units invulnerable\n")
        call SaveStr(DCP_H, 0, StringHash("cmd" + I2S(4)), "vul@116@vul@make selected units vulnerable\nkill@117@kill@kill selected units\nremove@118@remove@delete selected units\ninvis@119@invis@make selected units invisible\nvis@120@vis@make selected units visible\npath@121@path [on|off]@collision of selected units\nsize@122@size <%>@scale selected units\nfloat@123@float <h> [rate]@fly height of selected units\nowner@124@owner <player>@change the owner of selected units\nusefood@125@usefood <use|nouse>@food usage of selected units\nstop@126@stop@pause selected units\nresume@127@resume@unpause selected units\ndebuff@128@debuff@remove buffs from selected units\ncopy@129@copy <n>@copy selected units n times\nlife@130@life <pause|resume|remove>@timed life of selected units\nmaxhp@131@maxhp <n>@max life of selected units\nmaxmana@132@maxmana <n>@max mana of selected units\n")
        call SaveStr(DCP_H, 0, StringHash("cmd" + I2S(5)), "armor@133@armor <n>@armor of selected units\ndmg@134@dmg <n>@base damage of selected units\natkspd@135@atkspd <seconds>@attack cooldown of selected units\nrename@136@rename <name>@rename selected units\ncrit@140@crit <%> <mult|off>@critical strikes for selected units\nhpdmg@141@hpdmg <%|off>@damage as % of target max life\nlifesteal@142@lifesteal <%|off>@life steal for selected units\nmanasteal@143@manasteal <%|off>@mana steal for selected units\nblock@144@block <%|off>@block damage on selected units\nreflect@145@reflect <%|off>@reflect damage on selected units\nstatus@146@status@show combat mods of selected units\ncharge@153@charge <slot> <n>@set item charges on selected units\nitemid@154@itemid <slot>@show the item id in a slot\nunitid@155@unitid@show the id of selected units\nlearn@156@learn <id> [level]@add or level an ability\n")
        call SaveStr(DCP_H, 0, StringHash("cmd" + I2S(6)), "unlearn@157@unlearn <id>@remove an ability\n")
        call DCP_Regs()
        set t = CreateTrigger()
        set i = 0
        loop
            exitwhen i >= bj_MAX_PLAYER_SLOTS
            call TriggerRegisterPlayerChatEvent(t, Player(i), "", false)
            set i = i + 1
        endloop
        call TriggerAddAction(t, function DCP_OnChat)
        set t = CreateTrigger()
        call TriggerRegisterAnyUnitEventBJ(t, EVENT_PLAYER_UNIT_DAMAGING)
        call TriggerAddAction(t, function DCP_OnDamaging)
        set t = CreateTrigger()
        call TriggerRegisterAnyUnitEventBJ(t, EVENT_PLAYER_UNIT_DAMAGED)
        call TriggerAddAction(t, function DCP_OnDamaged)
        set DCP_DAMAGE_ON = true
        set t = CreateTrigger()
        set i = 0
        loop
            exitwhen i >= bj_MAX_PLAYER_SLOTS
            call TriggerRegisterPlayerChatEvent(t, Player(i), "", false)
            set i = i + 1
        endloop
        call TriggerAddAction(t, function DCP_OnChatAll)
        set t = CreateTrigger()
        set i = 0
        loop
            exitwhen i >= bj_MAX_PLAYER_SLOTS
            call TriggerRegisterPlayerEvent(t, Player(i), EVENT_PLAYER_ARROW_UP_DOWN)
            call TriggerRegisterPlayerEvent(t, Player(i), EVENT_PLAYER_ARROW_DOWN_DOWN)
            call TriggerRegisterPlayerEvent(t, Player(i), EVENT_PLAYER_ARROW_LEFT_DOWN)
            call TriggerRegisterPlayerEvent(t, Player(i), EVENT_PLAYER_ARROW_RIGHT_DOWN)
            set i = i + 1
        endloop
        call TriggerAddAction(t, function DCP_OnArrow)
        set t = CreateTrigger()
        set i = 0
        loop
            exitwhen i >= bj_MAX_PLAYER_SLOTS
            call TriggerRegisterPlayerStateEvent(t, Player(i), PLAYER_STATE_RESOURCE_GOLD, GREATER_THAN, 0)
            set i = i + 1
        endloop
        call TriggerAddAction(t, function DCP_OnGold)
        set t = CreateTrigger()
        set i = 0
        loop
            exitwhen i >= bj_MAX_PLAYER_SLOTS
            call TriggerRegisterPlayerStateEvent(t, Player(i), PLAYER_STATE_RESOURCE_LUMBER, GREATER_THAN, 0)
            set i = i + 1
        endloop
        call TriggerAddAction(t, function DCP_OnLumber)
        call DCP_UnitTrig(EVENT_PLAYER_UNIT_USE_ITEM, function DCP_OnUseItem)
        call DCP_UnitTrig(EVENT_PLAYER_UNIT_SPELL_CAST, function DCP_OnSpell)
        call DCP_UnitTrig(EVENT_PLAYER_UNIT_SPELL_EFFECT, function DCP_OnSpell)
        call DCP_UnitTrig(EVENT_PLAYER_UNIT_ISSUED_POINT_ORDER, function DCP_OnPointOrder)
        call DCP_UnitTrig(EVENT_PLAYER_UNIT_RESEARCH_START, function DCP_OnFast)
        call DCP_UnitTrig(EVENT_PLAYER_UNIT_TRAIN_FINISH, function DCP_OnFast)
        call DCP_UnitTrig(EVENT_PLAYER_UNIT_CONSTRUCT_FINISH, function DCP_OnFast)
        call DCP_UnitTrig(EVENT_PLAYER_UNIT_UPGRADE_FINISH, function DCP_OnFast)
        call DCP_UnitTrig(EVENT_PLAYER_UNIT_RESEARCH_FINISH, function DCP_OnFast)
        set t = CreateTrigger()
        set i = 0
        loop
            exitwhen i >= bj_MAX_PLAYER_SLOTS
            call BlzTriggerRegisterPlayerSyncEvent(t, Player(i), DCP_Cfg("sync"), false)
            set i = i + 1
        endloop
        call TriggerAddAction(t, function DCP_OnSync)
        call TimerStart(DCP_CLOCK, 3., true, function DCP_NameTick)
        set DCP_READY = true
        set t = null
    endfunction

function main takes nothing returns nothing
    call DCP_Init()
endfunction
