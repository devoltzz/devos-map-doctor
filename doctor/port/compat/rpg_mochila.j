//@GLOBALS
constant integer RPGM_MAXT=256
constant integer RPGM_MAXL=32
constant integer RPGM_G_MUDOU=1
constant integer RPGM_G_USA=2
constant integer RPGM_G_LOOT=3
integer RPGM_jogadores=12
real RPGM_raio=1500.0
boolean RPGM_avisa=true
real array RPGM_mult
hashtable RPGM_ht=null
trigger array RPGM_tg
boolean array RPGM_tem
trigger RPGM_t_morte=null
trigger RPGM_t_pega=null
group RPGM_g=null
integer array RPGM_n
integer array RPGM_lista
unit RPGM_ev_u=null
integer RPGM_ev_pid=0
integer RPGM_ev_id=0
integer RPGM_ev_n=0
integer RPGM_part=0
//@ENDGLOBALS

function RPGM_gancho takes integer qual, code f returns nothing
    if qual<1 or qual>8 then
        return
    endif
    call TriggerAddCondition(RPGM_tg[qual], Condition(f))
    set RPGM_tem[qual]=true
endfunction

function RPGM_chama takes integer qual, integer pid, integer id, integer n returns nothing
    if qual>=1 and qual<=8 and RPGM_tem[qual] then
        set RPGM_ev_pid=pid
        set RPGM_ev_id=id
        set RPGM_ev_n=n
        call TriggerEvaluate(RPGM_tg[qual])
    endif
endfunction

function RPGM_qtd takes integer pid, integer id returns integer
    return LoadInteger(RPGM_ht, pid, id)
endfunction

function RPGM_id_em takes integer pid, integer i returns integer
    return RPGM_lista[pid*RPGM_MAXT+i]
endfunction

function RPGM_soma takes integer pid, integer id, integer n returns integer
    local integer q
    local integer d
    if id==0 or pid<0 or n==0 then
        return RPGM_qtd(pid, id)
    endif
    set q=LoadInteger(RPGM_ht, pid, id)
    if not HaveSavedBoolean(RPGM_ht, pid, -id) and n>0 then
        if RPGM_n[pid]>=RPGM_MAXT then
            return q
        endif
        set RPGM_lista[pid*RPGM_MAXT+RPGM_n[pid]]=id
        set RPGM_n[pid]=RPGM_n[pid]+1
        call SaveBoolean(RPGM_ht, pid, -id, true)
    endif
    set d=n
    if q+n<0 then
        set d=-q
    endif
    set q=q+d
    call SaveInteger(RPGM_ht, pid, id, q)
    if d!=0 then
        call RPGM_chama(RPGM_G_MUDOU, pid, id, d)
    endif
    return q
endfunction

function RPGM_tira takes integer pid, integer id, integer n returns boolean
    if n<0 or RPGM_qtd(pid, id)<n then
        return false
    endif
    call RPGM_soma(pid, id, -n)
    return true
endfunction

function RPGM_limpa takes integer pid returns nothing
    local integer i=0
    loop
        exitwhen i>=RPGM_n[pid]
        call RemoveSavedBoolean(RPGM_ht, pid, -RPGM_lista[pid*RPGM_MAXT+i])
        set RPGM_lista[pid*RPGM_MAXT+i]=0
        set i=i+1
    endloop
    call FlushChildHashtable(RPGM_ht, pid)
    set RPGM_n[pid]=0
endfunction

function RPGM_usa takes integer pid, integer id returns boolean
    if not RPGM_tira(pid, id, 1) then
        return false
    endif
    call RPGM_chama(RPGM_G_USA, pid, id, 1)
    return true
endfunction

function RPGM_material takes integer id returns nothing
    call SaveBoolean(RPGM_ht, -1, id, true)
endfunction

function RPGM_e_material takes integer id returns boolean
    return LoadBoolean(RPGM_ht, -1, id)
endfunction

function RPGM_pega takes nothing returns boolean
    local item it=GetManipulatedItem()
    local integer id=GetItemTypeId(it)
    local integer pid=GetPlayerId(GetOwningPlayer(GetTriggerUnit()))
    local integer n
    if it!=null and RPGM_e_material(id) and pid<RPGM_jogadores then
        set n=GetItemCharges(it)
        if n<1 then
            set n=1
        endif
        call RemoveItem(it)
        call RPGM_soma(pid, id, n)
        if RPGM_avisa then
            call DisplayTimedTextToPlayer(Player(pid), 0, 0, 3.0, "|cff80ff80+"+I2S(n)+"|r "+GetObjectName(id))
        endif
    endif
    set it=null
    return false
endfunction

function RPGM_drop takes integer tipo, integer id, real chance, integer min, integer max returns nothing
    local integer k=LoadInteger(RPGM_ht, -2, tipo)
    if k>=RPGM_MAXL then
        return
    endif
    call SaveInteger(RPGM_ht, -3-k, tipo, id)
    call SaveReal(RPGM_ht, -3-k, -tipo, chance)
    call SaveInteger(RPGM_ht, -100-k, tipo, min)
    call SaveInteger(RPGM_ht, -100-k, -tipo, max)
    call SaveInteger(RPGM_ht, -2, tipo, k+1)
endfunction

function RPGM_gancho_dano takes nothing returns boolean
    local integer pid
    local integer h
    local integer m
    local integer b
    if RPGD_ev_tipo==RPGD_T_CURA or RPGD_ev_src==null or RPGD_ev_tgt==null then
        return false
    endif
    set pid=GetPlayerId(GetOwningPlayer(RPGD_ev_src))
    if pid>=RPGM_jogadores or LoadInteger(RPGM_ht, -2, GetUnitTypeId(RPGD_ev_tgt))==0 then
        return false
    endif
    set h=GetHandleId(RPGD_ev_tgt)
    set m=LoadInteger(RPGM_ht, -200, h)
    set b=R2I(Pow(2.0, I2R(pid))+0.5)
    if ModuloInteger(m/b, 2)==0 then
        call SaveInteger(RPGM_ht, -200, h, m+b)
    endif
    return false
endfunction

function RPGM_perto_cada takes nothing returns nothing
    local unit u=GetEnumUnit()
    local integer pid=GetPlayerId(GetOwningPlayer(u))
    local integer b
    if IsUnitType(u, UNIT_TYPE_HERO) and pid<RPGM_jogadores then
        set b=R2I(Pow(2.0, I2R(pid))+0.5)
        if ModuloInteger(RPGM_part/b, 2)==0 then
            set RPGM_part=RPGM_part+b
        endif
    endif
    set u=null
endfunction

function RPGM_sorteia_tipo takes integer pid, integer tipo, unit morto returns nothing
    local integer n=LoadInteger(RPGM_ht, -2, tipo)
    local integer k=0
    local integer id
    local integer q
    local real m=RPGM_mult[pid]
    local string aviso=""
    if m<=0.0 then
        set m=1.0
    endif
    loop
        exitwhen k>=n
        set id=LoadInteger(RPGM_ht, -3-k, tipo)
        if GetRandomReal(0.0, 1.0)<LoadReal(RPGM_ht, -3-k, -tipo)*m then
            set q=GetRandomInt(LoadInteger(RPGM_ht, -100-k, tipo), LoadInteger(RPGM_ht, -100-k, -tipo))
            if q>0 then
                call RPGM_soma(pid, id, q)
                set RPGM_ev_u=morto
                call RPGM_chama(RPGM_G_LOOT, pid, id, q)
                if aviso!="" then
                    set aviso=aviso+", "
                endif
                set aviso=aviso+"|cff80ff80+"+I2S(q)+"|r "+GetObjectName(id)
            endif
        endif
        set k=k+1
    endloop
    if RPGM_avisa and aviso!="" then
        call DisplayTimedTextToPlayer(Player(pid), 0, 0, 5.0, aviso)
    endif
endfunction

function RPGM_sorteia takes integer pid, unit morto returns nothing
    call RPGM_sorteia_tipo(pid, GetUnitTypeId(morto), morto)
endfunction

function RPGM_morte takes nothing returns boolean
    local unit u=GetTriggerUnit()
    local integer h=GetHandleId(u)
    local integer pid=0
    local integer b=1
    if LoadInteger(RPGM_ht, -2, GetUnitTypeId(u))==0 then
        set u=null
        return false
    endif
    set RPGM_part=LoadInteger(RPGM_ht, -200, h)
    call RemoveSavedInteger(RPGM_ht, -200, h)
    call GroupEnumUnitsInRange(RPGM_g, GetUnitX(u), GetUnitY(u), RPGM_raio, null)
    call ForGroup(RPGM_g, function RPGM_perto_cada)
    call GroupClear(RPGM_g)
    loop
        exitwhen pid>=RPGM_jogadores
        if ModuloInteger(RPGM_part/b, 2)==1 then
            call RPGM_sorteia(pid, u)
        endif
        set b=b*2
        set pid=pid+1
    endloop
    set u=null
    return false
endfunction

function RPGM_init takes nothing returns nothing
    local integer i=1
    if RPGM_ht!=null then
        return
    endif
    set RPGM_ht=InitHashtable()
    set RPGM_g=CreateGroup()
    loop
        exitwhen i>8
        set RPGM_tg[i]=CreateTrigger()
        set i=i+1
    endloop
    call RPGD_gancho(function RPGM_gancho_dano)
    set RPGM_t_morte=CreateTrigger()
    set RPGM_t_pega=CreateTrigger()
    set i=0
    loop
        exitwhen i>=bj_MAX_PLAYER_SLOTS
        call TriggerRegisterPlayerUnitEvent(RPGM_t_morte, Player(i), EVENT_PLAYER_UNIT_DEATH, null)
        if i<RPGM_jogadores then
            call TriggerRegisterPlayerUnitEvent(RPGM_t_pega, Player(i), EVENT_PLAYER_UNIT_PICKUP_ITEM, null)
            if RPGM_mult[i]<=0.0 then
                set RPGM_mult[i]=1.0
            endif
        endif
        set i=i+1
    endloop
    call TriggerAddCondition(RPGM_t_morte, Condition(function RPGM_morte))
    call TriggerAddCondition(RPGM_t_pega, Condition(function RPGM_pega))
endfunction
