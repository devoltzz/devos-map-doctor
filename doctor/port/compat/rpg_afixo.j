//@GLOBALS
constant integer RPGF_N=12
real RPGF_tique=1.0
real RPGF_alcance=1200.0
real RPGF_cad_chao=4.0
real RPGF_cad_gelo=6.0
real RPGF_cad_arc=10.0
real RPGF_cad_tele=8.0
real RPGF_cad_inv=12.0
real RPGF_frac_chao=0.25
real RPGF_frac_gelo=0.20
real RPGF_frac_arc=0.30
real RPGF_frac_peste=0.30
real RPGF_vamp=0.30
real RPGF_esc=0.20
real RPGF_espinho=0.10
real RPGF_jug_vel=0.70
real RPGF_frenesi=0.05
real RPGF_frenesi_teto=1.0
integer RPGF_lacaio=0
integer RPGF_inv_n=2
hashtable RPGF_ht=null
timer RPGF_tm=null
trigger RPGF_t_morte=null
group RPGF_elites=null
group RPGF_g=null
real RPGF_agora=0.0
string array RPGF_nome
unit RPGF_esc_u=null
unit RPGF_tmp_u=null
real RPGF_tmp_d=0.0
integer RPGF_tmp_n=0
integer RPGF_tmp_k=0
//@ENDGLOBALS

function RPGF_bit takes integer k returns integer
    local integer b=1
    local integer i=1
    loop
        exitwhen i>=k
        set b=b*2
        set i=i+1
    endloop
    return b
endfunction

function RPGF_mascara takes unit u returns integer
    if u==null then
        return 0
    endif
    return LoadInteger(RPGF_ht, GetHandleId(u), 0)
endfunction

function RPGF_tem takes unit u, integer k returns boolean
    local integer m=RPGF_mascara(u)
    local integer b=RPGF_bit(k)
    return ModuloInteger(m/b, 2)==1
endfunction

function RPGF_imune takes unit u returns boolean
    return RPGF_tem(u, 9)
endfunction

function RPGF_poe takes unit u, integer mascara returns nothing
    local integer h=GetHandleId(u)
    local integer k=1
    local string tags=""
    call SaveInteger(RPGF_ht, h, 0, mascara)
    loop
        exitwhen k>RPGF_N
        if ModuloInteger(mascara/RPGF_bit(k), 2)==1 then
            set tags=tags+"["+RPGF_nome[k]+"] "
            call SaveReal(RPGF_ht, h, k, -1000000.0)
        endif
        set k=k+1
    endloop
    if not HaveSavedString(RPGF_ht, h, 50) then
        call SaveStr(RPGF_ht, h, 50, GetUnitName(u))
    endif
    call BlzSetUnitName(u, tags+LoadStr(RPGF_ht, h, 50))
    if RPGF_tem(u, 9) then
        call SetUnitMoveSpeed(u, GetUnitDefaultMoveSpeed(u)*RPGF_jug_vel)
    endif
    call SaveInteger(RPGF_ht, h, 51, 0)
    call SaveReal(RPGF_ht, h, 52, 0.0)
    call SaveBoolean(RPGF_ht, h, 53, false)
    call GroupAddUnit(RPGF_elites, u)
endfunction

function RPGF_aplica takes unit u, integer n returns integer
    local integer m=0
    local integer k
    local integer tent=0
    local integer max=RPGF_N
    if RPGF_lacaio==0 then
        set max=RPGF_N-1
    endif
    if n>max then
        set n=max
    endif
    loop
        exitwhen n<=0 or tent>200
        set k=GetRandomInt(1, RPGF_N)
        if ModuloInteger(m/RPGF_bit(k), 2)==0 and (k!=7 or RPGF_lacaio!=0) then
            set m=m+RPGF_bit(k)
            set n=n-1
        endif
        set tent=tent+1
    endloop
    call RPGF_poe(u, m)
    return m
endfunction

function RPGF_inimigo_ok takes unit e, unit u returns boolean
    return u!=null and GetUnitTypeId(u)!=0 and not IsUnitType(u, UNIT_TYPE_DEAD) and not IsUnitType(u, UNIT_TYPE_STRUCTURE) and IsUnitEnemy(u, GetOwningPlayer(e))
endfunction

function RPGF_conta_cada takes nothing returns nothing
    if RPGF_inimigo_ok(RPGF_esc_u, GetEnumUnit()) then
        set RPGF_tmp_n=RPGF_tmp_n+1
    endif
endfunction

function RPGF_pega_cada takes nothing returns nothing
    if RPGF_inimigo_ok(RPGF_esc_u, GetEnumUnit()) then
        set RPGF_tmp_k=RPGF_tmp_k-1
        if RPGF_tmp_k==0 then
            set RPGF_tmp_u=GetEnumUnit()
        endif
    endif
endfunction

function RPGF_longe_cada takes nothing returns nothing
    local unit u=GetEnumUnit()
    local real dx
    local real dy
    if RPGF_inimigo_ok(RPGF_esc_u, u) then
        set dx=GetUnitX(u)-GetUnitX(RPGF_esc_u)
        set dy=GetUnitY(u)-GetUnitY(RPGF_esc_u)
        if dx*dx+dy*dy>RPGF_tmp_d then
            set RPGF_tmp_d=dx*dx+dy*dy
            set RPGF_tmp_u=u
        endif
    endif
    set u=null
endfunction

function RPGF_inimigo takes unit e, boolean longe returns unit
    set RPGF_esc_u=e
    set RPGF_tmp_u=null
    call GroupEnumUnitsInRange(RPGF_g, GetUnitX(e), GetUnitY(e), RPGF_alcance, null)
    if longe then
        set RPGF_tmp_d=-1.0
        call ForGroup(RPGF_g, function RPGF_longe_cada)
    else
        set RPGF_tmp_n=0
        call ForGroup(RPGF_g, function RPGF_conta_cada)
        if RPGF_tmp_n>0 then
            set RPGF_tmp_k=GetRandomInt(1, RPGF_tmp_n)
            call ForGroup(RPGF_g, function RPGF_pega_cada)
        endif
    endif
    call GroupClear(RPGF_g)
    return RPGF_tmp_u
endfunction

function RPGF_vez takes unit e, integer k, real cad returns boolean
    local integer h=GetHandleId(e)
    if RPGF_agora<LoadReal(RPGF_ht, h, k)+cad then
        return false
    endif
    call SaveReal(RPGF_ht, h, k, RPGF_agora)
    return true
endfunction

function RPGF_age_cada takes nothing returns nothing
    local unit e=GetEnumUnit()
    local unit a
    local integer h=GetHandleId(e)
    local real ang
    local group g
    if IsUnitType(e, UNIT_TYPE_DEAD) or GetUnitTypeId(e)==0 then
        set e=null
        return
    endif
    set a=RPGF_inimigo(e, false)
    if a==null then
        if RPGF_tem(e, 12) and LoadReal(RPGF_ht, h, 54)>0.0 then
            call RPGD_soma(e, RPGD_S_VEL, -LoadReal(RPGF_ht, h, 54))
            call SaveReal(RPGF_ht, h, 54, 0.0)
            call RPGD_vel(e)
        endif
        set e=null
        return
    endif
    if RPGF_tem(e, 1) and RPGF_vez(e, 1, RPGF_cad_chao) then
        call RPGX_circulo(e, GetUnitX(a), GetUnitY(a), 200.0, 1.5, RPGF_frac_chao)
    endif
    if RPGF_tem(e, 2) and RPGF_vez(e, 2, RPGF_cad_gelo) then
        call RPGX_circulo(e, GetUnitX(a), GetUnitY(a), 250.0, 2.0, RPGF_frac_gelo)
        set a=RPGF_inimigo(e, false)
        if a!=null then
            call RPGX_circulo(e, GetUnitX(a), GetUnitY(a), 250.0, 2.0, RPGF_frac_gelo)
        endif
    endif
    if RPGF_tem(e, 3) and RPGF_vez(e, 3, RPGF_cad_arc) then
        call RPGX_roda(e, 1, 700.0, 100.0, 60.0, 1.5, 5.0, RPGF_frac_arc)
    endif
    if RPGF_tem(e, 6) and RPGF_vez(e, 6, RPGF_cad_tele) then
        set a=RPGF_inimigo(e, true)
        if a!=null then
            set ang=Atan2(GetUnitY(e)-GetUnitY(a), GetUnitX(e)-GetUnitX(a))
            call SetUnitPosition(e, GetUnitX(a)+120.0*Cos(ang), GetUnitY(a)+120.0*Sin(ang))
            call IssueTargetOrder(e, "attack", a)
        endif
    endif
    if RPGF_tem(e, 7) and RPGF_lacaio!=0 and RPGF_vez(e, 7, RPGF_cad_inv) then
        set g=RPGX_ondas(e, RPGF_lacaio, RPGF_inv_n, GetUnitX(e), GetUnitY(e), 150.0)
        call DestroyGroup(g)
    endif
    if RPGF_tem(e, 12) and LoadReal(RPGF_ht, h, 54)<RPGF_frenesi_teto then
        call RPGD_soma(e, RPGD_S_VEL, RPGF_frenesi)
        call SaveReal(RPGF_ht, h, 54, LoadReal(RPGF_ht, h, 54)+RPGF_frenesi)
        call RPGD_vel(e)
    endif
    set e=null
    set a=null
    set g=null
endfunction

function RPGF_tiq takes nothing returns nothing
    set RPGF_agora=RPGF_agora+RPGF_tique
    call ForGroup(RPGF_elites, function RPGF_age_cada)
endfunction

function RPGF_espelho takes unit e returns nothing
    local unit c=CreateUnit(GetOwningPlayer(e), GetUnitTypeId(e), GetUnitX(e)+150.0, GetUnitY(e), GetUnitFacing(e))
    local integer m=RPGF_mascara(e)-RPGF_bit(11)
    call SaveStr(RPGF_ht, GetHandleId(c), 50, LoadStr(RPGF_ht, GetHandleId(e), 50))
    call RPGF_poe(c, m)
    call BlzSetUnitMaxHP(c, BlzGetUnitMaxHP(e)/2)
    call SetWidgetLife(c, I2R(BlzGetUnitMaxHP(c)))
    set c=null
endfunction

function RPGF_gancho_dano takes nothing returns boolean
    local unit src=RPGD_ev_src
    local unit tgt=RPGD_ev_tgt
    local integer h
    local real v=RPGD_ev_valor
    local real maxv
    local real depois
    local integer lim
    if RPGD_ev_tipo==RPGD_T_CURA then
        set src=null
        set tgt=null
        return false
    endif
    if src!=null and RPGF_tem(src, 4) and v>0.0 then
        call SetWidgetLife(src, GetWidgetLife(src)+v*RPGF_vamp)
    endif
    if tgt!=null and RPGF_mascara(tgt)!=0 then
        set h=GetHandleId(tgt)
        if LoadReal(RPGF_ht, h, 52)>0.0 then
            if v<=LoadReal(RPGF_ht, h, 52) then
                call SaveReal(RPGF_ht, h, 52, LoadReal(RPGF_ht, h, 52)-v)
                set RPGD_ev_texto=v
                set RPGD_ev_valor=0.0
                set v=0.0
            else
                set v=v-LoadReal(RPGF_ht, h, 52)
                call SaveReal(RPGF_ht, h, 52, 0.0)
                set RPGD_ev_texto=RPGD_ev_valor
                set RPGD_ev_valor=v
            endif
        endif
        if RPGF_tem(tgt, 8) and src!=null and RPGD_ev_tipo!=RPGD_T_PURO and RPGD_ev_valor>0.0 then
            call RPGD_dano(tgt, src, RPGD_ev_valor*RPGF_espinho, RPGD_T_PURO)
        endif
        set maxv=I2R(BlzGetUnitMaxHP(tgt))
        set depois=GetWidgetLife(tgt)-RPGD_ev_valor
        if RPGF_tem(tgt, 5) and maxv>0.0 then
            set lim=LoadInteger(RPGF_ht, h, 51)
            if (lim<1 and depois<=maxv*0.7) or (lim<2 and depois<=maxv*0.4) or (lim<3 and depois<=maxv*0.1) then
                if depois<=maxv*0.1 then
                    call SaveInteger(RPGF_ht, h, 51, 3)
                elseif depois<=maxv*0.4 then
                    call SaveInteger(RPGF_ht, h, 51, 2)
                else
                    call SaveInteger(RPGF_ht, h, 51, 1)
                endif
                call SaveReal(RPGF_ht, h, 52, maxv*RPGF_esc)
            endif
        endif
        if RPGF_tem(tgt, 11) and not LoadBoolean(RPGF_ht, h, 53) and depois>0.405 and depois<=maxv*0.5 then
            call SaveBoolean(RPGF_ht, h, 53, true)
            call RPGF_espelho(tgt)
        endif
    endif
    set src=null
    set tgt=null
    return false
endfunction

function RPGF_morte takes nothing returns boolean
    local unit u=GetTriggerUnit()
    if RPGF_mascara(u)!=0 then
        if RPGF_tem(u, 10) then
            set RPGX_fica=true
            call RPGX_circulo(u, GetUnitX(u), GetUnitY(u), 300.0, 1.5, RPGF_frac_peste)
        endif
        call GroupRemoveUnit(RPGF_elites, u)
        call RemoveSavedInteger(RPGF_ht, GetHandleId(u), 0)
    endif
    set u=null
    return false
endfunction

function RPGF_init takes nothing returns nothing
    local integer i=0
    if RPGF_ht!=null then
        return
    endif
    set RPGF_ht=InitHashtable()
    set RPGF_elites=CreateGroup()
    set RPGF_g=CreateGroup()
    set RPGF_nome[1]="Molten"
    set RPGF_nome[2]="Frozen"
    set RPGF_nome[3]="Arcane"
    set RPGF_nome[4]="Vampiric"
    set RPGF_nome[5]="Shielded"
    set RPGF_nome[6]="Teleporter"
    set RPGF_nome[7]="Summoner"
    set RPGF_nome[8]="Thorns"
    set RPGF_nome[9]="Juggernaut"
    set RPGF_nome[10]="Plague"
    set RPGF_nome[11]="Mirror"
    set RPGF_nome[12]="Frenzied"
    call RPGD_gancho(function RPGF_gancho_dano)
    set RPGF_t_morte=CreateTrigger()
    loop
        exitwhen i>=bj_MAX_PLAYER_SLOTS
        call TriggerRegisterPlayerUnitEvent(RPGF_t_morte, Player(i), EVENT_PLAYER_UNIT_DEATH, null)
        set i=i+1
    endloop
    call TriggerAddCondition(RPGF_t_morte, Condition(function RPGF_morte))
    set RPGF_tm=CreateTimer()
    call TimerStart(RPGF_tm, RPGF_tique, true, function RPGF_tiq)
endfunction
