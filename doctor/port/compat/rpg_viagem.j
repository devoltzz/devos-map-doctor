//@GLOBALS
constant integer RPGV_MAX=31
integer RPGV_jogadores=12
integer RPGV_dono=15
real RPGV_raio=500.0
real RPGV_canal=5.0
real RPGV_folga=100.0
unit array RPGV_heroi
unit array RPGV_p_u
string array RPGV_p_nome
boolean array RPGV_p_livre
integer RPGV_n=0
integer array RPGV_mask
integer array RPGV_vai
real array RPGV_fim
real array RPGV_ox
real array RPGV_oy
real RPGV_agora=0.0
trigger RPGV_t_chat=null
timer RPGV_tm=null
//@ENDGLOBALS

function RPGV_bit takes integer k returns integer
    local integer b=1
    local integer i=0
    loop
        exitwhen i>=k
        set b=b*2
        set i=i+1
    endloop
    return b
endfunction

function RPGV_tem takes integer pid, integer k returns boolean
    return RPGV_p_livre[k] or ModuloInteger(RPGV_mask[pid]/RPGV_bit(k), 2)==1
endfunction

function RPGV_pedra takes integer tipo, real x, real y, string nome, boolean livre returns unit
    local unit u
    if RPGV_n>=RPGV_MAX then
        return null
    endif
    set u=CreateUnit(Player(RPGV_dono), tipo, x, y, 270.0)
    call SetUnitInvulnerable(u, true)
    set RPGV_p_u[RPGV_n]=u
    set RPGV_p_nome[RPGV_n]=nome
    set RPGV_p_livre[RPGV_n]=livre
    set RPGV_n=RPGV_n+1
    return u
endfunction

function RPGV_diz takes integer pid, string s returns nothing
    call DisplayTimedTextToPlayer(Player(pid), 0, 0, 6.0, s)
endfunction

function RPGV_vivo takes unit h returns boolean
    return h!=null and GetUnitTypeId(h)!=0 and not IsUnitType(h, UNIT_TYPE_DEAD)
endfunction

function RPGV_d2 takes unit a, unit b returns real
    local real dx=GetUnitX(a)-GetUnitX(b)
    local real dy=GetUnitY(a)-GetUnitY(b)
    return dx*dx+dy*dy
endfunction

function RPGV_perto takes unit h returns integer
    local integer k=0
    loop
        exitwhen k>=RPGV_n
        if RPGV_d2(h, RPGV_p_u[k])<=RPGV_raio*RPGV_raio then
            return k
        endif
        set k=k+1
    endloop
    return -1
endfunction

function RPGV_lista takes integer pid returns nothing
    local integer k=0
    local string s="|cffffcc00Waypoints|r (type -wp <number>):"
    loop
        exitwhen k>=RPGV_n
        if RPGV_tem(pid, k) then
            set s=s+"|n  "+I2S(k+1)+". "+RPGV_p_nome[k]
        endif
        set k=k+1
    endloop
    call DisplayTimedTextToPlayer(Player(pid), 0, 0, 12.0, s)
endfunction

function RPGV_chat takes nothing returns nothing
    local integer pid=GetPlayerId(GetTriggerPlayer())
    local string s=GetEventPlayerChatString()
    local unit h=RPGV_heroi[pid]
    local integer k
    if pid>=RPGV_jogadores or not RPGV_vivo(h) then
        set h=null
        return
    endif
    if RPGV_perto(h)<0 then
        call RPGV_diz(pid, "|cffff8080Stand next to a waypoint stone.|r")
        set h=null
        return
    endif
    if StringLength(s)<=4 then
        call RPGV_lista(pid)
    else
        set k=S2I(SubString(s, 4, StringLength(s)))-1
        if k<0 or k>=RPGV_n or not RPGV_tem(pid, k) then
            call RPGV_diz(pid, "|cffff8080Unknown waypoint.|r Type -wp for the list.")
        else
            set RPGV_vai[pid]=k+1
            set RPGV_fim[pid]=RPGV_agora+RPGV_canal
            set RPGV_ox[pid]=GetUnitX(h)
            set RPGV_oy[pid]=GetUnitY(h)
            call RPGV_diz(pid, "Travelling to "+RPGV_p_nome[k]+"... (damage or moving cancels)")
        endif
    endif
    set h=null
endfunction

function RPGV_cancela takes integer pid, string motivo returns nothing
    if RPGV_vai[pid]>0 then
        set RPGV_vai[pid]=0
        call RPGV_diz(pid, "|cffff8080Travel cancelled|r ("+motivo+").")
    endif
endfunction

function RPGV_gancho_dano takes nothing returns boolean
    local integer pid
    if RPGD_ev_tgt!=null and RPGD_ev_valor>0.0 and RPGD_ev_tipo!=RPGD_T_CURA then
        set pid=GetPlayerId(GetOwningPlayer(RPGD_ev_tgt))
        if pid<RPGV_jogadores and RPGV_heroi[pid]==RPGD_ev_tgt then
            call RPGV_cancela(pid, "damage")
        endif
    endif
    return false
endfunction

function RPGV_tiq takes nothing returns nothing
    local integer pid=0
    local integer k
    local unit h
    local real dx
    local real dy
    set RPGV_agora=RPGV_agora+0.25
    loop
        exitwhen pid>=RPGV_jogadores
        set h=RPGV_heroi[pid]
        if RPGV_vivo(h) then
            if ModuloInteger(R2I(RPGV_agora*4.0+0.5), 4)==0 then
                set k=RPGV_perto(h)
                if k>=0 and not RPGV_tem(pid, k) then
                    set RPGV_mask[pid]=RPGV_mask[pid]+RPGV_bit(k)
                    call RPGV_diz(pid, "|cff80c0ffWaypoint unlocked:|r "+RPGV_p_nome[k])
                endif
            endif
            if RPGV_vai[pid]>0 then
                set dx=GetUnitX(h)-RPGV_ox[pid]
                set dy=GetUnitY(h)-RPGV_oy[pid]
                if dx*dx+dy*dy>RPGV_folga*RPGV_folga then
                    call RPGV_cancela(pid, "moved")
                elseif RPGV_agora>=RPGV_fim[pid] then
                    set k=RPGV_vai[pid]-1
                    set RPGV_vai[pid]=0
                    call SetUnitPosition(h, GetUnitX(RPGV_p_u[k]), GetUnitY(RPGV_p_u[k])-150.0)
                    if GetLocalPlayer()==Player(pid) then
                        call PanCameraToTimed(GetUnitX(h), GetUnitY(h), 0.0)
                    endif
                endif
            endif
        else
            set RPGV_vai[pid]=0
        endif
        set pid=pid+1
    endloop
    set h=null
endfunction

function RPGV_grava takes nothing returns boolean
    call RPGS_poe_i("wp", RPGV_mask[RPGS_ev_pid])
    return false
endfunction

function RPGV_nasce takes nothing returns boolean
    local integer pid=RPGH_ev_pid
    set RPGV_heroi[pid]=RPGH_ev_u
    set RPGV_vai[pid]=0
    set RPGV_mask[pid]=0
    if RPGS_ev_ok and RPGS_tem(pid, "wp") then
        set RPGV_mask[pid]=RPGS_le_i(pid, "wp")
    endif
    return false
endfunction

function RPGV_init takes nothing returns nothing
    local integer i=0
    if RPGV_t_chat!=null then
        return
    endif
    set RPGV_t_chat=CreateTrigger()
    loop
        exitwhen i>=RPGV_jogadores
        call TriggerRegisterPlayerChatEvent(RPGV_t_chat, Player(i), "-wp", false)
        set i=i+1
    endloop
    call TriggerAddAction(RPGV_t_chat, function RPGV_chat)
    call RPGD_gancho(function RPGV_gancho_dano)
    call RPGS_gancho(RPGS_G_GRAVA, function RPGV_grava)
    call RPGH_gancho(RPGH_G_NASCE, function RPGV_nasce)
    set RPGV_tm=CreateTimer()
    call TimerStart(RPGV_tm, 0.25, true, function RPGV_tiq)
endfunction
