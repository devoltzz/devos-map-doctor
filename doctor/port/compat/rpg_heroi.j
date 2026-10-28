//@GLOBALS
constant integer RPGH_MAXT=12
constant integer RPGH_G_NASCE=1
constant integer RPGH_G_GRAVA=2
integer RPGH_jogadores=12
real RPGH_x=0.0
real RPGH_y=0.0
real RPGH_reviver_base=5.0
real RPGH_reviver_faixa=2.0
integer RPGH_faixa_niveis=30
real RPGH_xp_raio=1500.0
real RPGH_gx_base=25.0
real RPGH_gx_a=1.0
real RPGH_gx_b=5.0
real RPGH_gx_c=5.0
string RPGH_titulo="Choose your hero"
integer RPGH_n=0
integer array RPGH_tipo
string array RPGH_ico
string array RPGH_papel
string array RPGH_texto
trigger array RPGH_tg
boolean array RPGH_tem
unit array RPGH_u
integer array RPGH_k
boolean array RPGH_escolhendo
trigger RPGH_t_clique=null
trigger RPGH_t_morte=null
group RPGH_g=null
framehandle RPGH_q_painel=null
framehandle array RPGH_q_bt
framehandle RPGH_q_desc=null
unit RPGH_ev_u=null
integer RPGH_ev_pid=0
boolean RPGH_pronto=false
//@ENDGLOBALS

function RPGH_gancho takes integer qual, code f returns nothing
    if qual<1 or qual>8 then
        return
    endif
    call TriggerAddCondition(RPGH_tg[qual], Condition(f))
    set RPGH_tem[qual]=true
endfunction

function RPGH_chama takes integer qual, integer pid, unit u returns nothing
    if qual>=1 and qual<=8 and RPGH_tem[qual] then
        set RPGH_ev_pid=pid
        set RPGH_ev_u=u
        call TriggerEvaluate(RPGH_tg[qual])
    endif
endfunction

function RPGH_heroi_tipo takes integer tipo, string icone, string papel, string texto returns nothing
    if RPGH_n>=RPGH_MAXT then
        return
    endif
    set RPGH_n=RPGH_n+1
    set RPGH_tipo[RPGH_n]=tipo
    set RPGH_ico[RPGH_n]=icone
    set RPGH_papel[RPGH_n]=papel
    set RPGH_texto[RPGH_n]=texto
endfunction

function RPGH_id2s takes integer id returns string
    local string cs="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    local string r=""
    local integer i=0
    local integer c
    loop
        exitwhen i>=4
        set c=ModuloInteger(id, 256)
        set id=id/256
        if c>=48 and c<=57 then
            set r=SubString(cs, c-48, c-47)+r
        elseif c>=65 and c<=90 then
            set r=SubString(cs, c-55, c-54)+r
        elseif c>=97 and c<=122 then
            set r=SubString(cs, c-61, c-60)+r
        else
            set r="_"+r
        endif
        set i=i+1
    endloop
    return r
endfunction

function RPGH_mostra takes integer pid, boolean v returns nothing
    set RPGH_escolhendo[pid]=v
    if GetLocalPlayer()==Player(pid) and RPGH_q_painel!=null then
        call BlzFrameSetVisible(RPGH_q_painel, v)
    endif
endfunction

function RPGH_quadros takes nothing returns nothing
    local framehandle jogo=BlzGetOriginFrame(ORIGIN_FRAME_GAME_UI, 0)
    local framehandle f
    local framehandle t
    local integer k=1
    local integer col
    local integer lin
    local real x
    local real y
    set RPGH_q_painel=BlzCreateFrame("EscMenuBackdrop", jogo, 0, 0)
    call BlzFrameSetAbsPoint(RPGH_q_painel, FRAMEPOINT_CENTER, 0.40, 0.36)
    call BlzFrameSetSize(RPGH_q_painel, 0.66, 0.40)
    set t=BlzCreateFrameByType("TEXT", "RPGH_titulo", RPGH_q_painel, "", 0)
    call BlzFrameSetPoint(t, FRAMEPOINT_TOP, RPGH_q_painel, FRAMEPOINT_TOP, 0.0, -0.03)
    call BlzFrameSetSize(t, 0.5, 0.02)
    call BlzFrameSetTextAlignment(t, TEXT_JUSTIFY_CENTER, TEXT_JUSTIFY_MIDDLE)
    call BlzFrameSetText(t, "|cffffcc00"+RPGH_titulo+"|r")
    loop
        exitwhen k>RPGH_n
        set col=ModuloInteger(k-1, 5)
        set lin=(k-1)/5
        set x=0.105+col*0.115
        set y=0.465-lin*0.115
        set f=BlzCreateFrameByType("BACKDROP", "RPGH_ico", RPGH_q_painel, "", k)
        call BlzFrameSetAbsPoint(f, FRAMEPOINT_TOP, x+0.05, y)
        call BlzFrameSetSize(f, 0.045, 0.045)
        call BlzFrameSetTexture(f, RPGH_ico[k], 0, true)
        set RPGH_q_bt[k]=BlzCreateFrame("ScriptDialogButton", RPGH_q_painel, 0, k)
        call BlzFrameSetAbsPoint(RPGH_q_bt[k], FRAMEPOINT_TOP, x+0.05, y-0.047)
        call BlzFrameSetSize(RPGH_q_bt[k], 0.11, 0.03)
        call BlzFrameSetText(RPGH_q_bt[k], GetObjectName(RPGH_tipo[k]))
        call BlzTriggerRegisterFrameEvent(RPGH_t_clique, RPGH_q_bt[k], FRAMEEVENT_CONTROL_CLICK)
        set t=BlzCreateFrameByType("TEXT", "RPGH_papel", RPGH_q_painel, "", k)
        call BlzFrameSetAbsPoint(t, FRAMEPOINT_TOP, x+0.05, y-0.078)
        call BlzFrameSetSize(t, 0.11, 0.012)
        call BlzFrameSetTextAlignment(t, TEXT_JUSTIFY_CENTER, TEXT_JUSTIFY_MIDDLE)
        call BlzFrameSetText(t, "|cff999999"+RPGH_papel[k]+"|r")
        set k=k+1
    endloop
    set RPGH_q_desc=BlzCreateFrameByType("TEXT", "RPGH_desc", RPGH_q_painel, "", 0)
    call BlzFrameSetPoint(RPGH_q_desc, FRAMEPOINT_BOTTOM, RPGH_q_painel, FRAMEPOINT_BOTTOM, 0.0, 0.025)
    call BlzFrameSetSize(RPGH_q_desc, 0.6, 0.03)
    call BlzFrameSetTextAlignment(RPGH_q_desc, TEXT_JUSTIFY_CENTER, TEXT_JUSTIFY_MIDDLE)
    call BlzFrameSetText(RPGH_q_desc, "Each hero has its own save. Pick one to load it (or start it new).")
    call BlzFrameSetVisible(RPGH_q_painel, false)
    set jogo=null
    set f=null
    set t=null
endfunction

function RPGH_escolhe takes integer pid, integer k returns nothing
    if pid<0 or pid>=RPGH_jogadores or k<1 or k>RPGH_n or not RPGH_escolhendo[pid] or RPGH_u[pid]!=null then
        return
    endif
    set RPGH_k[pid]=k
    call RPGH_mostra(pid, false)
    call RPGS_carrega(pid, RPGH_id2s(RPGH_tipo[k]))
endfunction

function RPGH_clique takes nothing returns nothing
    local framehandle f=BlzGetTriggerFrame()
    local integer pid=GetPlayerId(GetTriggerPlayer())
    local integer k=1
    if GetLocalPlayer()==GetTriggerPlayer() then
        call BlzFrameSetEnable(f, false)
        call BlzFrameSetEnable(f, true)
    endif
    loop
        exitwhen k>RPGH_n
        if RPGH_q_bt[k]==f then
            call RPGH_escolhe(pid, k)
        endif
        set k=k+1
    endloop
    set f=null
endfunction

function RPGH_nasce takes nothing returns boolean
    local integer pid=RPGS_ev_pid
    local integer k=RPGH_k[pid]
    local unit h
    local integer lv
    if k<1 or RPGH_u[pid]!=null then
        return false
    endif
    set h=CreateUnit(Player(pid), RPGH_tipo[k], RPGH_x, RPGH_y, 270.0)
    set RPGH_u[pid]=h
    set RPGP_heroi[pid]=h
    set RPGK_heroi[pid]=h
    set RPGR_heroi[pid]=h
    if RPGS_ev_ok then
        set lv=RPGS_le_i(pid, "lv")
        if lv>1 then
            call SetHeroLevel(h, lv, false)
        endif
        call SetHeroXP(h, RPGS_le_i(pid, "xp"), false)
        call SetHeroStr(h, RPGS_le_i(pid, "str"), true)
        call SetHeroAgi(h, RPGS_le_i(pid, "agi"), true)
        call SetHeroInt(h, RPGS_le_i(pid, "int"), true)
        call SetPlayerState(Player(pid), PLAYER_STATE_RESOURCE_GOLD, RPGS_le_i(pid, "ouro"))
        call RPGS_le_mochila(pid)
        call RPGS_le_inventario(pid, h)
        call RPGS_le_rituais(pid)
        call RPGT_le_save(pid)
        call RPGT_aplica(pid, h)
        call DisplayTimedTextToPlayer(Player(pid), 0, 0, 6.0, "|cff80ff80Save loaded:|r level "+I2S(GetHeroLevel(h)))
    else
        call RPGM_limpa(pid)
        call DisplayTimedTextToPlayer(Player(pid), 0, 0, 6.0, "|cffffcc00New hero.|r Your progress saves itself (and with -save).")
    endif
    call RPGD_vel(h)
    call RPGI_marca(pid)
    if GetLocalPlayer()==Player(pid) then
        call ClearSelection()
        call SelectUnit(h, true)
        call PanCameraToTimed(RPGH_x, RPGH_y, 0.0)
    endif
    call RPGH_chama(RPGH_G_NASCE, pid, h)
    set h=null
    return false
endfunction

function RPGH_grava_campos takes nothing returns boolean
    local integer pid=RPGS_ev_pid
    local unit h=RPGH_u[pid]
    if h==null then
        return false
    endif
    call RPGS_poe_i("lv", GetHeroLevel(h))
    call RPGS_poe_i("xp", GetHeroXP(h))
    call RPGS_poe_i("str", RPGI_base(h, 1))
    call RPGS_poe_i("agi", RPGI_base(h, 2))
    call RPGS_poe_i("int", RPGI_base(h, 3))
    call RPGS_poe_i("ouro", GetPlayerState(Player(pid), PLAYER_STATE_RESOURCE_GOLD))
    call RPGS_poe_mochila(pid)
    call RPGS_poe_inventario(h)
    call RPGS_poe_rituais(pid)
    call RPGT_poe_save(pid)
    call RPGH_chama(RPGH_G_GRAVA, pid, h)
    set h=null
    return false
endfunction

function RPGH_grava takes integer pid returns nothing
    if RPGH_u[pid]!=null and RPGH_k[pid]>0 then
        call RPGS_grava(pid, RPGH_id2s(RPGH_tipo[RPGH_k[pid]]))
    endif
endfunction

function RPGH_no_ritual takes integer pid returns boolean
    return RPGR_estado!=0 and RPGR_resp[pid]==1
endfunction

function RPGH_repick takes integer pid returns boolean
    if RPGH_u[pid]==null or RPGH_no_ritual(pid) then
        return false
    endif
    call RPGH_grava(pid)
    set RPGS_estado[pid]=0
    call RPGI_zera(pid, null)
    call RemoveUnit(RPGH_u[pid])
    set RPGH_u[pid]=null
    set RPGP_heroi[pid]=null
    set RPGK_heroi[pid]=null
    set RPGR_heroi[pid]=null
    set RPGH_k[pid]=0
    call RPGM_limpa(pid)
    call RPGH_mostra(pid, true)
    return true
endfunction

function RPGH_xp_morte takes integer lv returns real
    local real x=RPGH_gx_base
    local integer i=2
    loop
        exitwhen i>lv
        set x=x*RPGH_gx_a+I2R(i)*RPGH_gx_b+RPGH_gx_c
        set i=i+1
    endloop
    return x
endfunction

function RPGH_reviver takes nothing returns nothing
    local timer t=GetExpiredTimer()
    local integer pid=LoadInteger(RPGS_ht, -77, GetHandleId(t))
    local unit h=RPGH_u[pid]
    if h!=null and IsUnitType(h, UNIT_TYPE_DEAD) and not RPGH_no_ritual(pid) then
        call ReviveHero(h, RPGH_x, RPGH_y, true)
        if GetLocalPlayer()==Player(pid) then
            call PanCameraToTimed(RPGH_x, RPGH_y, 0.0)
        endif
    endif
    call RemoveSavedInteger(RPGS_ht, -77, GetHandleId(t))
    call DestroyTimer(t)
    set t=null
    set h=null
endfunction

function RPGH_conta_max takes nothing returns nothing
    local unit u=GetEnumUnit()
    local integer pid=GetPlayerId(GetOwningPlayer(u))
    if pid<RPGH_jogadores and u==RPGH_u[pid] and not IsUnitType(u, UNIT_TYPE_DEAD) and GetHeroLevel(u)>=RPGT_nivel_max then
        call SaveInteger(RPGS_ht, -78, 0, LoadInteger(RPGS_ht, -78, 0)+1)
    endif
    set u=null
endfunction

function RPGH_da_max takes nothing returns nothing
    local unit u=GetEnumUnit()
    local integer pid=GetPlayerId(GetOwningPlayer(u))
    if pid<RPGH_jogadores and u==RPGH_u[pid] and not IsUnitType(u, UNIT_TYPE_DEAD) and GetHeroLevel(u)>=RPGT_nivel_max then
        call RPGT_xp(pid, LoadReal(RPGS_ht, -78, 1))
    endif
    set u=null
endfunction

function RPGH_morte takes nothing returns boolean
    local unit u=GetTriggerUnit()
    local integer pid=GetPlayerId(GetOwningPlayer(u))
    local timer t
    local integer n
    if pid<RPGH_jogadores and u==RPGH_u[pid] then
        if not RPGH_no_ritual(pid) then
            set t=CreateTimer()
            call SaveInteger(RPGS_ht, -77, GetHandleId(t), pid)
            call TimerStart(t, RPGH_reviver_base+RPGH_reviver_faixa*I2R(GetHeroLevel(u)/RPGH_faixa_niveis), false, function RPGH_reviver)
            call DisplayTimedTextToPlayer(Player(pid), 0, 0, 5.0, "|cffff8080You died.|r Reviving at the Haven...")
        endif
    elseif IsUnitEnemy(u, Player(0)) and not IsUnitType(u, UNIT_TYPE_HERO) then
        call SaveInteger(RPGS_ht, -78, 0, 0)
        call GroupEnumUnitsInRange(RPGH_g, GetUnitX(u), GetUnitY(u), RPGH_xp_raio, null)
        call ForGroup(RPGH_g, function RPGH_conta_max)
        set n=LoadInteger(RPGS_ht, -78, 0)
        if n>0 then
            call SaveReal(RPGS_ht, -78, 1, RPGH_xp_morte(GetUnitLevel(u))/I2R(n))
            call ForGroup(RPGH_g, function RPGH_da_max)
        endif
        call GroupClear(RPGH_g)
    endif
    set u=null
    set t=null
    return false
endfunction

function RPGH_comeca takes nothing returns nothing
    local integer i=0
    if RPGH_q_painel==null then
        call RPGH_quadros()
    endif
    loop
        exitwhen i>=RPGH_jogadores
        if GetPlayerSlotState(Player(i))==PLAYER_SLOT_STATE_PLAYING and GetPlayerController(Player(i))==MAP_CONTROL_USER then
            call RPGH_mostra(i, true)
        endif
        set i=i+1
    endloop
endfunction

function RPGH_init takes nothing returns nothing
    local integer i=1
    if RPGH_pronto then
        return
    endif
    set RPGH_pronto=true
    loop
        exitwhen i>8
        set RPGH_tg[i]=CreateTrigger()
        set i=i+1
    endloop
    set RPGH_g=CreateGroup()
    set RPGH_t_clique=CreateTrigger()
    call TriggerAddAction(RPGH_t_clique, function RPGH_clique)
    call RPGS_gancho(RPGS_G_CARREGA, function RPGH_nasce)
    call RPGS_gancho(RPGS_G_GRAVA, function RPGH_grava_campos)
    set RPGH_t_morte=CreateTrigger()
    set i=0
    loop
        exitwhen i>=bj_MAX_PLAYER_SLOTS
        call TriggerRegisterPlayerUnitEvent(RPGH_t_morte, Player(i), EVENT_PLAYER_UNIT_DEATH, null)
        if i<RPGH_jogadores then
            set RPGH_escolhendo[i]=false
        endif
        set i=i+1
    endloop
    call TriggerAddCondition(RPGH_t_morte, Condition(function RPGH_morte))
endfunction
