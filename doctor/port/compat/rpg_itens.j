//@GLOBALS
constant integer RPGI_S_PRIM=1
constant integer RPGI_S_SEC=2
constant integer RPGI_S_ATQ=3
constant integer RPGI_S_SKILL=4
constant integer RPGI_S_DEF=5
constant integer RPGI_S_VIDA=6
constant integer RPGI_S_CURA=7
constant integer RPGI_S_MANA=8
constant integer RPGI_S_CRIT=9
constant integer RPGI_S_CRITX=10
constant integer RPGI_S_MOV=11
constant integer RPGI_S_ESQ=12
constant integer RPGI_S_VEL=13
constant integer RPGI_NS=13
integer RPGI_jogadores=12
real RPGI_ref_pct=0.10
string array RPGI_tipo_nome
hashtable RPGI_ht=null
trigger RPGI_t_inv=null
timer RPGI_tm=null
boolean array RPGI_sujo
real array RPGI_ap
//@ENDGLOBALS

function RPGI_item takes integer id, integer tipo, integer grau returns nothing
    call SaveInteger(RPGI_ht, id, 0, tipo)
    call SaveInteger(RPGI_ht, id, 100, grau)
endfunction

function RPGI_req takes integer id, integer nivel returns nothing
    call SaveInteger(RPGI_ht, id, 101, nivel)
endfunction

function RPGI_stat takes integer id, integer s, real v returns nothing
    call SaveReal(RPGI_ht, id, s, v)
endfunction

function RPGI_tipo takes integer id returns integer
    return LoadInteger(RPGI_ht, id, 0)
endfunction

function RPGI_heroi takes integer tipo, integer prim, integer sec returns nothing
    call SaveInteger(RPGI_ht, tipo, 200, prim)
    call SaveInteger(RPGI_ht, tipo, 201, sec)
endfunction

function RPGI_get_attr takes unit h, integer a returns integer
    if a==1 then
        return GetHeroStr(h, false)
    elseif a==2 then
        return GetHeroAgi(h, false)
    endif
    return GetHeroInt(h, false)
endfunction

function RPGI_set_attr takes unit h, integer a, integer v returns nothing
    if a==1 then
        call SetHeroStr(h, v, true)
    elseif a==2 then
        call SetHeroAgi(h, v, true)
    else
        call SetHeroInt(h, v, true)
    endif
endfunction

function RPGI_base takes unit h, integer a returns integer
    local integer pid=GetPlayerId(GetOwningPlayer(h))
    return RPGI_get_attr(h, a)-R2I(RPGI_ap[pid*32+a])
endfunction

function RPGI_aplica_delta takes unit h, integer pid, integer k, real novo returns nothing
    local real d=novo-RPGI_ap[pid*32+k]
    if d==0.0 then
        return
    endif
    set RPGI_ap[pid*32+k]=novo
    if k<=3 then
        call RPGI_set_attr(h, k, RPGI_get_attr(h, k)+R2I(d))
    elseif k==4+RPGI_S_ATQ then
        call RPGD_soma(h, RPGD_S_ATQ, d)
    elseif k==4+RPGI_S_SKILL then
        call RPGD_soma(h, RPGD_S_SKILL, d)
    elseif k==4+RPGI_S_DEF then
        call RPGD_soma(h, RPGD_S_DEF, d)
    elseif k==4+RPGI_S_VIDA then
        call BlzSetUnitMaxHP(h, BlzGetUnitMaxHP(h)+R2I(d))
        if d>0.0 then
            call SetWidgetLife(h, GetWidgetLife(h)+d)
        endif
    elseif k==4+RPGI_S_CURA then
        call RPGD_soma(h, RPGD_S_CURA, d)
    elseif k==4+RPGI_S_MANA then
        call BlzSetUnitMaxMana(h, BlzGetUnitMaxMana(h)+R2I(d))
    elseif k==4+RPGI_S_CRIT then
        call RPGD_soma(h, RPGD_S_CRIT, d)
    elseif k==4+RPGI_S_CRITX then
        call RPGD_soma(h, RPGD_S_CRITX, d)
    elseif k==4+RPGI_S_MOV then
        call SetUnitMoveSpeed(h, GetUnitMoveSpeed(h)+d)
    elseif k==4+RPGI_S_ESQ then
        call RPGD_soma(h, RPGD_S_ESQ, d)
    elseif k==4+RPGI_S_VEL then
        call RPGD_soma(h, RPGD_S_VEL, d)
        call RPGD_vel(h)
    endif
endfunction

function RPGI_recalcula takes integer pid, unit h returns nothing
    local real array soma
    local integer s=0
    local integer k
    local item it
    local integer id
    local real mult
    local integer prim
    local integer sec
    local real base_prim
    if h==null or GetUnitTypeId(h)==0 then
        return
    endif
    set prim=LoadInteger(RPGI_ht, GetUnitTypeId(h), 200)
    set sec=LoadInteger(RPGI_ht, GetUnitTypeId(h), 201)
    if prim<1 then
        set prim=1
    endif
    if sec<1 then
        set sec=2
    endif
    loop
        exitwhen s>=UnitInventorySize(h)
        set it=UnitItemInSlot(h, s)
        if it!=null then
            set id=GetItemTypeId(it)
            if RPGI_tipo(id)>0 then
                set mult=1.0+RPGI_ref_pct*I2R(RPGK_nivel(it))
                set k=1
                loop
                    exitwhen k>RPGI_NS
                    set soma[k]=soma[k]+LoadReal(RPGI_ht, id, k)*mult
                    set k=k+1
                endloop
            endif
        endif
        set s=s+1
    endloop
    set base_prim=I2R(RPGI_base(h, prim))+soma[RPGI_S_PRIM]
    set soma[RPGI_S_PRIM]=soma[RPGI_S_PRIM]+base_prim*RPGT_par_pct(pid, 1)
    set soma[RPGI_S_VIDA]=soma[RPGI_S_VIDA]+(I2R(BlzGetUnitMaxHP(h))-RPGI_ap[pid*32+4+RPGI_S_VIDA])*RPGT_par_pct(pid, 3)
    set k=1
    loop
        exitwhen k>3
        if k==prim then
            call RPGI_aplica_delta(h, pid, k, soma[RPGI_S_PRIM])
        elseif k==sec then
            call RPGI_aplica_delta(h, pid, k, soma[RPGI_S_SEC])
        else
            call RPGI_aplica_delta(h, pid, k, 0.0)
        endif
        set k=k+1
    endloop
    set k=RPGI_S_ATQ
    loop
        exitwhen k>RPGI_NS
        call RPGI_aplica_delta(h, pid, 4+k, soma[k])
        set k=k+1
    endloop
    set it=null
endfunction

function RPGI_zera takes integer pid, unit h returns nothing
    local integer k=1
    loop
        exitwhen k>4+RPGI_NS
        if h!=null then
            call RPGI_aplica_delta(h, pid, k, 0.0)
        endif
        set RPGI_ap[pid*32+k]=0.0
        set k=k+1
    endloop
endfunction

function RPGI_marca takes integer pid returns nothing
    if pid>=0 and pid<RPGI_jogadores then
        set RPGI_sujo[pid]=true
    endif
endfunction

function RPGI_inv takes nothing returns nothing
    local unit h=GetTriggerUnit()
    local item it=GetManipulatedItem()
    local integer pid=GetPlayerId(GetOwningPlayer(h))
    local integer tipo=RPGI_tipo(GetItemTypeId(it))
    local integer s=0
    local item o
    if pid>=RPGI_jogadores or not IsUnitType(h, UNIT_TYPE_HERO) then
        set h=null
        set it=null
        return
    endif
    if GetTriggerEventId()==EVENT_PLAYER_UNIT_PICKUP_ITEM and tipo>0 and GetHeroLevel(h)<LoadInteger(RPGI_ht, GetItemTypeId(it), 101) then
        call UnitRemoveItem(h, it)
        call DisplayTimedTextToPlayer(Player(pid), 0, 0, 4.0, "|cffff8080Requires level "+I2S(LoadInteger(RPGI_ht, GetItemTypeId(it), 101))+".|r")
        set tipo=0
    endif
    if GetTriggerEventId()==EVENT_PLAYER_UNIT_PICKUP_ITEM and tipo>0 then
        loop
            exitwhen s>=UnitInventorySize(h)
            set o=UnitItemInSlot(h, s)
            if o!=null and o!=it and RPGI_tipo(GetItemTypeId(o))==tipo then
                call UnitRemoveItem(h, it)
                call DisplayTimedTextToPlayer(Player(pid), 0, 0, 4.0, "|cffff8080You already wear a "+RPGI_tipo_nome[tipo]+".|r")
                set s=UnitInventorySize(h)
            endif
            set s=s+1
        endloop
    endif
    set RPGI_sujo[pid]=true
    set h=null
    set it=null
    set o=null
endfunction

function RPGI_gancho_refino takes nothing returns boolean
    call RPGI_marca(RPGK_ev_pid)
    return false
endfunction

function RPGI_gancho_feito takes nothing returns boolean
    call RPGI_marca(RPGK_ev_pid)
    return false
endfunction

function RPGI_tiq takes nothing returns nothing
    local integer pid=0
    loop
        exitwhen pid>=RPGI_jogadores
        if RPGI_sujo[pid] then
            set RPGI_sujo[pid]=false
            call RPGI_recalcula(pid, RPGK_heroi[pid])
        endif
        set pid=pid+1
    endloop
endfunction

function RPGI_init takes nothing returns nothing
    local integer i=0
    if RPGI_ht!=null then
        return
    endif
    set RPGI_ht=InitHashtable()
    set RPGI_tipo_nome[1]="weapon"
    set RPGI_tipo_nome[2]="helm"
    set RPGI_tipo_nome[3]="armor"
    set RPGI_tipo_nome[4]="pair of boots"
    set RPGI_tipo_nome[5]="ring"
    set RPGI_tipo_nome[6]="accessory"
    set RPGI_t_inv=CreateTrigger()
    loop
        exitwhen i>=RPGI_jogadores
        call TriggerRegisterPlayerUnitEvent(RPGI_t_inv, Player(i), EVENT_PLAYER_UNIT_PICKUP_ITEM, null)
        call TriggerRegisterPlayerUnitEvent(RPGI_t_inv, Player(i), EVENT_PLAYER_UNIT_DROP_ITEM, null)
        call TriggerRegisterPlayerUnitEvent(RPGI_t_inv, Player(i), EVENT_PLAYER_UNIT_PAWN_ITEM, null)
        set i=i+1
    endloop
    call TriggerAddAction(RPGI_t_inv, function RPGI_inv)
    call RPGK_gancho(RPGK_G_REFINO, function RPGI_gancho_refino)
    call RPGK_gancho(RPGK_G_FEITO, function RPGI_gancho_feito)
    set RPGI_tm=CreateTimer()
    call TimerStart(RPGI_tm, 0.1, true, function RPGI_tiq)
endfunction
