//@GLOBALS
constant integer RPGR_MAXR=64
constant integer RPGR_G_INICIO=1
constant integer RPGR_G_PRIMEIRA=2
constant integer RPGR_G_FIM=3
integer RPGR_jogadores=12
integer RPGR_teto=5
real RPGR_altar_raio=600.0
real RPGR_conf_tempo=10.0
real RPGR_saida=5.0
real RPGR_sx=0.0
real RPGR_sy=0.0
integer RPGR_dono=11
boolean RPGR_avisa=true
unit array RPGR_heroi
integer RPGR_n=0
integer array RPGR_r_sigilo
integer array RPGR_r_chefe
real array RPGR_r_x
real array RPGR_r_y
real array RPGR_r_raio
integer array RPGR_r_nivel
integer array RPGR_r_req
real array RPGR_r_vida
integer array RPGR_r_vit
boolean array RPGR_venc
hashtable RPGR_ht=null
trigger array RPGR_tg
boolean array RPGR_tem
trigger RPGR_t_sync=null
trigger RPGR_t_dial=null
trigger RPGR_t_morte=null
timer RPGR_tm=null
group RPGR_altares=null
dialog RPGR_dial=null
button RPGR_b_sim=null
button RPGR_b_nao=null
integer RPGR_estado=0
integer RPGR_k=0
integer RPGR_quem=-1
unit RPGR_boss=null
real RPGR_t=0.0
integer array RPGR_resp
boolean RPGR_venceu_agora=false
string RPGR_falta=""
integer RPGR_ev_k=0
unit RPGR_ev_boss=null
integer RPGR_ev_pid=0
boolean RPGR_ev_ok=false
boolean RPGR_tmp_ok=false
unit RPGR_tmp_u=null
//@ENDGLOBALS

function RPGR_gancho takes integer qual, code f returns nothing
    if qual<1 or qual>8 then
        return
    endif
    call TriggerAddCondition(RPGR_tg[qual], Condition(f))
    set RPGR_tem[qual]=true
endfunction

function RPGR_chama takes integer qual returns nothing
    if qual>=1 and qual<=8 and RPGR_tem[qual] then
        call TriggerEvaluate(RPGR_tg[qual])
    endif
endfunction

function RPGR_diz takes integer pid, string s returns nothing
    if RPGR_avisa and pid>=0 then
        call DisplayTimedTextToPlayer(Player(pid), 0, 0, 6.0, s)
    endif
endfunction

function RPGR_ritual takes integer sigilo, integer chefe, real x, real y, real raio, integer nivel, integer requisito, real vida returns integer
    if RPGR_n>=RPGR_MAXR-1 then
        return 0
    endif
    set RPGR_n=RPGR_n+1
    set RPGR_r_sigilo[RPGR_n]=sigilo
    set RPGR_r_chefe[RPGR_n]=chefe
    set RPGR_r_x[RPGR_n]=x
    set RPGR_r_y[RPGR_n]=y
    set RPGR_r_raio[RPGR_n]=raio
    set RPGR_r_nivel[RPGR_n]=nivel
    set RPGR_r_req[RPGR_n]=requisito
    set RPGR_r_vida[RPGR_n]=vida
    set RPGR_r_vit[RPGR_n]=0
    return RPGR_n
endfunction

function RPGR_venceu takes integer pid, integer k returns boolean
    return RPGR_venc[pid*RPGR_MAXR+k]
endfunction

function RPGR_marca takes integer pid, integer k, boolean b returns nothing
    set RPGR_venc[pid*RPGR_MAXR+k]=b
endfunction

function RPGR_altar takes unit u returns nothing
    call GroupAddUnit(RPGR_altares, u)
endfunction

function RPGR_perto_cada takes nothing returns nothing
    local real dx=GetUnitX(GetEnumUnit())-GetUnitX(RPGR_tmp_u)
    local real dy=GetUnitY(GetEnumUnit())-GetUnitY(RPGR_tmp_u)
    if dx*dx+dy*dy<=RPGR_altar_raio*RPGR_altar_raio then
        set RPGR_tmp_ok=true
    endif
endfunction

function RPGR_no_altar takes unit h returns boolean
    set RPGR_tmp_ok=false
    set RPGR_tmp_u=h
    call ForGroup(RPGR_altares, function RPGR_perto_cada)
    return RPGR_tmp_ok
endfunction

function RPGR_vivo takes unit h returns boolean
    return h!=null and GetUnitTypeId(h)!=0 and not IsUnitType(h, UNIT_TYPE_DEAD)
endfunction

function RPGR_slot_sigilo takes unit h, integer id returns integer
    local integer s=0
    loop
        exitwhen s>=UnitInventorySize(h)
        if GetItemTypeId(UnitItemInSlot(h, s))==id then
            return s
        endif
        set s=s+1
    endloop
    return -1
endfunction

function RPGR_tem_sigilo takes integer pid, integer id returns boolean
    return RPGM_qtd(pid, id)>0 or RPGR_slot_sigilo(RPGR_heroi[pid], id)>=0
endfunction

function RPGR_gasta_sigilo takes integer pid, integer id returns nothing
    local integer s
    if RPGM_tira(pid, id, 1) then
        return
    endif
    set s=RPGR_slot_sigilo(RPGR_heroi[pid], id)
    if s>=0 then
        call RemoveItem(UnitItemInSlot(RPGR_heroi[pid], s))
    endif
endfunction

function RPGR_pode takes integer pid, integer k returns boolean
    local unit h
    set RPGR_falta=""
    if pid<0 or pid>=RPGR_jogadores or k<1 or k>RPGR_n then
        set RPGR_falta="no such ritual"
        return false
    endif
    set h=RPGR_heroi[pid]
    if not RPGR_vivo(h) then
        set RPGR_falta="no hero"
    elseif RPGR_estado!=0 then
        set RPGR_falta="another ritual is in progress"
    elseif not RPGR_no_altar(h) then
        set RPGR_falta="go to the Altar of Summons"
    elseif RPGR_r_vit[k]>=RPGR_teto then
        set RPGR_falta="this boss was already defeated "+I2S(RPGR_teto)+" times this game"
    elseif GetHeroLevel(h)<RPGR_r_nivel[k] then
        set RPGR_falta="requires level "+I2S(RPGR_r_nivel[k])
    elseif RPGR_r_req[k]>0 and not RPGR_venceu(pid, RPGR_r_req[k]) then
        set RPGR_falta="defeat "+GetObjectName(RPGR_r_chefe[RPGR_r_req[k]])+" first"
    elseif not RPGR_tem_sigilo(pid, RPGR_r_sigilo[k]) then
        set RPGR_falta="requires "+GetObjectName(RPGR_r_sigilo[k])
    endif
    set h=null
    return RPGR_falta==""
endfunction

function RPGR_invoca takes integer pid, integer k returns boolean
    local integer i=0
    local integer chamados=0
    if not RPGR_pode(pid, k) then
        call RPGR_diz(pid, "|cffff8080Cannot summon:|r "+RPGR_falta)
        return false
    endif
    set RPGR_estado=1
    set RPGR_k=k
    set RPGR_quem=pid
    set RPGR_t=0.0
    call DialogClear(RPGR_dial)
    call DialogSetMessage(RPGR_dial, GetPlayerName(Player(pid))+" summons "+GetObjectName(RPGR_r_chefe[k])+". Join?")
    set RPGR_b_sim=DialogAddButton(RPGR_dial, "Join", 0)
    set RPGR_b_nao=DialogAddButton(RPGR_dial, "Decline", 0)
    loop
        exitwhen i>=RPGR_jogadores
        set RPGR_resp[i]=0
        if i==pid then
            set RPGR_resp[i]=1
        elseif RPGR_vivo(RPGR_heroi[i]) and GetHeroLevel(RPGR_heroi[i])>=RPGR_r_nivel[k] then
            set RPGR_resp[i]=-2
            set chamados=chamados+1
            call DialogDisplay(Player(i), RPGR_dial, true)
        endif
        set i=i+1
    endloop
    if chamados==0 then
        set RPGR_t=RPGR_conf_tempo
    endif
    return true
endfunction

function RPGR_pede takes integer k returns nothing
    call BlzSendSyncData("rpgr", "I"+I2S(k))
endfunction

function RPGR_sync takes nothing returns nothing
    local integer pid=GetPlayerId(GetTriggerPlayer())
    local string v=BlzGetTriggerSyncData()
    if v!=null and StringLength(v)>=2 and SubString(v, 0, 1)=="I" then
        call RPGR_invoca(pid, S2I(SubString(v, 1, StringLength(v))))
    endif
endfunction

function RPGR_clique takes nothing returns nothing
    local integer pid=GetPlayerId(GetTriggerPlayer())
    if RPGR_estado!=1 or pid<0 or pid>=RPGR_jogadores or RPGR_resp[pid]!=-2 then
        return
    endif
    if GetClickedButton()==RPGR_b_sim then
        set RPGR_resp[pid]=1
    else
        set RPGR_resp[pid]=-1
    endif
    call DialogDisplay(Player(pid), RPGR_dial, false)
endfunction

function RPGR_comeca takes nothing returns nothing
    local integer k=RPGR_k
    local integer i=0
    local integer n=0
    local real a
    loop
        exitwhen i>=RPGR_jogadores
        if RPGR_resp[i]==-2 then
            set RPGR_resp[i]=-1
            call DialogDisplay(Player(i), RPGR_dial, false)
        endif
        if RPGR_resp[i]==1 and RPGR_vivo(RPGR_heroi[i]) then
            set n=n+1
        else
            set RPGR_resp[i]=-1
        endif
        set i=i+1
    endloop
    call RPGR_gasta_sigilo(RPGR_quem, RPGR_r_sigilo[k])
    set RPGR_boss=CreateUnit(Player(RPGR_dono), RPGR_r_chefe[k], RPGR_r_x[k], RPGR_r_y[k], 270.0)
    call RPGC_registra(RPGR_boss, RPGR_r_vida[k], n)
    call RPGA_registra(RPGR_boss)
    call RPGC_toca(RPGR_boss, RPGR_r_x[k], RPGR_r_y[k], RPGR_r_raio[k], RPGR_sx, RPGR_sy)
    set i=0
    loop
        exitwhen i>=RPGR_jogadores
        if RPGR_resp[i]==1 then
            set a=I2R(i)*bj_PI*2.0/I2R(RPGR_jogadores)
            call SetUnitPosition(RPGR_heroi[i], RPGR_r_x[k]+RPGR_r_raio[k]*0.6*Cos(a), RPGR_r_y[k]+RPGR_r_raio[k]*0.6*Sin(a))
            call RPGR_diz(i, "|cffffcc00The ritual begins!|r")
        endif
        set i=i+1
    endloop
    set RPGR_estado=2
    set RPGR_ev_k=k
    set RPGR_ev_boss=RPGR_boss
    call RPGR_chama(RPGR_G_INICIO)
endfunction

function RPGR_termina takes boolean venceu returns nothing
    local integer k=RPGR_k
    local integer i=0
    set RPGR_venceu_agora=venceu
    if venceu then
        set RPGR_r_vit[k]=RPGR_r_vit[k]+1
        loop
            exitwhen i>=RPGR_jogadores
            if RPGR_resp[i]==1 then
                if not RPGR_venceu(i, k) then
                    call RPGR_marca(i, k, true)
                    set RPGR_ev_k=k
                    set RPGR_ev_pid=i
                    call RPGR_chama(RPGR_G_PRIMEIRA)
                endif
                call RPGR_diz(i, "|cff80ff80Victory!|r ("+I2S(RPGR_r_vit[k])+"/"+I2S(RPGR_teto)+" this game)")
            endif
            set i=i+1
        endloop
    else
        call RPGM_soma(RPGR_quem, RPGR_r_sigilo[k], 1)
        call RPGC_solta(RPGR_boss)
        call RPGA_solta(RPGR_boss)
        call RemoveUnit(RPGR_boss)
        loop
            exitwhen i>=RPGR_jogadores
            if RPGR_resp[i]==1 then
                call RPGR_diz(i, "|cffff8080The party has fallen.|r The sigil returns to the summoner.")
            endif
            set i=i+1
        endloop
    endif
    set RPGR_boss=null
    set RPGR_estado=3
    set RPGR_t=0.0
endfunction

function RPGR_sai takes nothing returns nothing
    local integer i=0
    local unit h
    loop
        exitwhen i>=RPGR_jogadores
        if RPGR_resp[i]==1 then
            set h=RPGR_heroi[i]
            if h!=null and GetUnitTypeId(h)!=0 then
                if IsUnitType(h, UNIT_TYPE_DEAD) then
                    call ReviveHero(h, RPGR_sx, RPGR_sy, true)
                else
                    call SetUnitPosition(h, RPGR_sx, RPGR_sy)
                endif
            endif
        endif
        set RPGR_resp[i]=0
        set i=i+1
    endloop
    set RPGR_estado=0
    set RPGR_ev_k=RPGR_k
    set RPGR_ev_ok=RPGR_venceu_agora
    call RPGR_chama(RPGR_G_FIM)
    set h=null
endfunction

function RPGR_tiq takes nothing returns nothing
    local integer i=0
    local boolean todos=true
    local boolean algum=false
    set RPGR_t=RPGR_t+0.25
    if RPGR_estado==1 then
        loop
            exitwhen i>=RPGR_jogadores
            if RPGR_resp[i]==-2 then
                set todos=false
            endif
            set i=i+1
        endloop
        if todos or RPGR_t>=RPGR_conf_tempo then
            call RPGR_comeca()
        endif
    elseif RPGR_estado==2 then
        if RPGR_boss==null or IsUnitType(RPGR_boss, UNIT_TYPE_DEAD) then
            call RPGR_termina(true)
            return
        endif
        loop
            exitwhen i>=RPGR_jogadores
            if RPGR_resp[i]==1 and RPGR_vivo(RPGR_heroi[i]) then
                set algum=true
            endif
            set i=i+1
        endloop
        if not algum then
            call RPGR_termina(false)
        endif
    elseif RPGR_estado==3 then
        if RPGR_t>=RPGR_saida then
            call RPGR_sai()
        endif
    endif
endfunction

function RPGR_init takes nothing returns nothing
    local integer i=1
    if RPGR_ht!=null then
        return
    endif
    set RPGR_ht=InitHashtable()
    set RPGR_altares=CreateGroup()
    loop
        exitwhen i>8
        set RPGR_tg[i]=CreateTrigger()
        set i=i+1
    endloop
    set RPGR_dial=DialogCreate()
    set RPGR_t_dial=CreateTrigger()
    call TriggerRegisterDialogEvent(RPGR_t_dial, RPGR_dial)
    call TriggerAddAction(RPGR_t_dial, function RPGR_clique)
    set RPGR_t_sync=CreateTrigger()
    set i=0
    loop
        exitwhen i>=RPGR_jogadores
        call BlzTriggerRegisterPlayerSyncEvent(RPGR_t_sync, Player(i), "rpgr", false)
        set i=i+1
    endloop
    call TriggerAddAction(RPGR_t_sync, function RPGR_sync)
    set RPGR_tm=CreateTimer()
    call TimerStart(RPGR_tm, 0.25, true, function RPGR_tiq)
endfunction
