//@GLOBALS
constant integer RPGE_ONDAS=1
constant integer RPGE_ENCOLHE=2
constant integer RPGE_DEFENDE=3
constant integer RPGE_TANK=4
constant integer RPGE_CURA=5
constant integer RPGE_DPS=6
constant integer RPGE_APOIO=7
constant integer RPGE_MAXK=24
integer RPGE_jogadores=12
integer RPGE_dono=12
integer RPGE_amigo=15
real RPGE_onda=20.0
real RPGE_nom_vida=10.0
real RPGE_encolhe=0.15
real RPGE_fora=0.15
real RPGE_totem_vida=40.0
real RPGE_sangra=0.03
real RPGE_dps_vida=400.0
real RPGE_grupo=800.0
real RPGE_comp_ch=0.25
integer RPGE_prova_nivel=150
integer RPGE_totem=0
integer RPGE_aliado=0
integer RPGE_ron=0
integer array RPGE_faixa_nv
integer array RPGE_lacaio
integer array RPGE_material
integer array RPGE_comp
real array RPGE_vida_faixa
unit array RPGE_heroi
integer RPGE_n=0
integer array RPGE_k_tipo
real array RPGE_k_x
real array RPGE_k_y
real array RPGE_k_raio
real array RPGE_k_dur
string array RPGE_k_nome
unit array RPGE_k_pedra
integer array RPGE_k_estado
integer array RPGE_k_faixa
real array RPGE_k_t
real array RPGE_k_onda
unit array RPGE_k_alvo
group array RPGE_k_g
integer array RPGE_k_quem
unit RPGE_mestre_u=null
hashtable RPGE_ht=null
trigger RPGE_t_chat=null
timer RPGE_tm=null
group RPGE_g=null
integer RPGE_c_k=0
integer RPGE_c_vivos=0
//@ENDGLOBALS

function RPGE_desafio takes integer tipo, real x, real y, real raio, real dur, string nome returns integer
    local integer k=RPGE_n
    if k>=RPGE_MAXK then
        return -1
    endif
    set RPGE_n=k+1
    set RPGE_k_tipo[k]=tipo
    set RPGE_k_x[k]=x
    set RPGE_k_y[k]=y
    set RPGE_k_raio[k]=raio
    set RPGE_k_dur[k]=dur
    set RPGE_k_nome[k]=nome
    set RPGE_k_estado[k]=0
    set RPGE_k_g[k]=CreateGroup()
    return k
endfunction

function RPGE_pedra takes integer k, integer tipo, real x, real y returns unit
    set RPGE_k_pedra[k]=CreateUnit(Player(RPGE_amigo), tipo, x, y, 270.0)
    call SetUnitInvulnerable(RPGE_k_pedra[k], true)
    return RPGE_k_pedra[k]
endfunction

function RPGE_mestre takes unit u returns nothing
    set RPGE_mestre_u=u
    call SetUnitInvulnerable(u, true)
endfunction

function RPGE_prova takes integer tipo_heroi, integer k, string titulo returns nothing
    call SaveInteger(RPGE_ht, tipo_heroi, 0, k+1)
    call SaveStr(RPGE_ht, tipo_heroi, 1, titulo)
endfunction

function RPGE_vivo takes unit u returns boolean
    return u!=null and GetUnitTypeId(u)!=0 and not IsUnitType(u, UNIT_TYPE_DEAD)
endfunction

function RPGE_diz takes integer pid, string s returns nothing
    call DisplayTimedTextToPlayer(Player(pid), 0, 0, 8.0, s)
endfunction

function RPGE_perto takes unit a, unit b, real r returns boolean
    local real dx=GetUnitX(a)-GetUnitX(b)
    local real dy=GetUnitY(a)-GetUnitY(b)
    return a!=null and b!=null and dx*dx+dy*dy<=r*r
endfunction

function RPGE_bit takes integer pid returns integer
    return R2I(Pow(2.0, I2R(pid))+0.5)
endfunction

function RPGE_entrou takes integer k, integer pid returns boolean
    return ModuloInteger(RPGE_k_quem[k]/RPGE_bit(pid), 2)==1
endfunction

function RPGE_faixa_de takes integer nivel returns integer
    local integer f=1
    loop
        exitwhen f>=10 or RPGE_faixa_nv[f+1]<=0 or nivel<RPGE_faixa_nv[f+1]
        set f=f+1
    endloop
    return f
endfunction

function RPGE_avancou takes unit h returns boolean
    return LoadBoolean(RPGE_ht, GetHandleId(h), 2)
endfunction

function RPGE_cria takes integer k, integer dono, integer id, real x, real y returns unit
    local unit u=CreateUnit(Player(dono), id, x, y, 270.0)
    call GroupAddUnit(RPGE_k_g[k], u)
    return u
endfunction

function RPGE_vida takes unit u, real mult returns nothing
    call BlzSetUnitMaxHP(u, IMaxBJ(1, R2I(RMinBJ(I2R(BlzGetUnitMaxHP(u))*mult, 2000000000.0))))
    call SetWidgetLife(u, I2R(BlzGetUnitMaxHP(u)))
endfunction

function RPGE_onda_de takes integer k, integer n returns nothing
    local integer j=0
    local real a
    local unit u
    local real r=RPGE_k_raio[k]*0.8
    loop
        exitwhen j>=n
        set a=GetRandomReal(0.0, 2.0*bj_PI)
        set u=RPGE_cria(k, RPGE_dono, RPGE_lacaio[RPGE_k_faixa[k]], RPGE_k_x[k]+r*Cos(a), RPGE_k_y[k]+r*Sin(a))
        if RPGE_vivo(RPGE_k_alvo[k]) and RPGE_k_tipo[k]==RPGE_DEFENDE then
            call IssueTargetOrder(u, "attack", RPGE_k_alvo[k])
        else
            call IssuePointOrder(u, "attack", RPGE_k_x[k], RPGE_k_y[k])
        endif
        set j=j+1
    endloop
    set u=null
endfunction

function RPGE_conta takes integer k returns integer
    local integer pid=0
    local integer n=0
    loop
        exitwhen pid>=RPGE_jogadores
        if RPGE_entrou(k, pid) and RPGE_vivo(RPGE_heroi[pid]) then
            set n=n+1
        endif
        set pid=pid+1
    endloop
    return n
endfunction

function RPGE_comeca takes integer k, integer quem, integer faixa returns nothing
    local integer pid=0
    local integer j
    local unit u
    local unit h
    local real a
    set RPGE_k_estado[k]=1
    set RPGE_k_quem[k]=quem
    set RPGE_k_faixa[k]=IMaxBJ(1, IMinBJ(10, faixa))
    set RPGE_k_t[k]=0.0
    set RPGE_k_onda[k]=0.0
    set RPGE_k_alvo[k]=null
    loop
        exitwhen pid>=RPGE_jogadores
        if RPGE_entrou(k, pid) then
            set h=RPGE_heroi[pid]
            call SetUnitPosition(h, RPGE_k_x[k], RPGE_k_y[k]-100.0)
            if GetLocalPlayer()==Player(pid) then
                call PanCameraToTimed(RPGE_k_x[k], RPGE_k_y[k], 0.0)
            endif
            call RPGE_diz(pid, "|cffffcc00"+RPGE_k_nome[k]+"|r begins.")
        endif
        set pid=pid+1
    endloop
    set h=null
    if RPGE_k_tipo[k]==RPGE_DEFENDE then
        set u=RPGE_cria(k, RPGE_amigo, RPGE_totem, RPGE_k_x[k], RPGE_k_y[k]+150.0)
        call BlzSetUnitMaxHP(u, IMaxBJ(1, R2I(RMinBJ(RPGE_totem_vida*RPGE_vida_faixa[RPGE_k_faixa[k]], 2000000000.0))))
        call SetWidgetLife(u, I2R(BlzGetUnitMaxHP(u)))
        set RPGE_k_alvo[k]=u
    elseif RPGE_k_tipo[k]==RPGE_TANK then
        set RPGE_k_alvo[k]=RPGE_cria(k, RPGE_amigo, RPGE_aliado, RPGE_k_x[k], RPGE_k_y[k]+150.0)
        set j=0
        loop
            exitwhen j>=3
            set a=2.0*bj_PI*I2R(j)/3.0
            set u=RPGE_cria(k, RPGE_dono, RPGE_lacaio[RPGE_k_faixa[k]], RPGE_k_x[k]+250.0*Cos(a), RPGE_k_y[k]+250.0*Sin(a))
            call RPGE_vida(u, 20.0)
            call IssueTargetOrder(u, "attack", RPGE_k_alvo[k])
            set j=j+1
        endloop
    elseif RPGE_k_tipo[k]==RPGE_CURA then
        set j=0
        loop
            exitwhen j>=4
            set a=2.0*bj_PI*I2R(j)/4.0
            call RPGE_cria(k, RPGE_amigo, RPGE_aliado, RPGE_k_x[k]+150.0*Cos(a), RPGE_k_y[k]+150.0*Sin(a))
            set j=j+1
        endloop
    elseif RPGE_k_tipo[k]==RPGE_DPS or RPGE_k_tipo[k]==RPGE_APOIO then
        set u=RPGE_cria(k, RPGE_dono, RPGE_lacaio[RPGE_k_faixa[k]], RPGE_k_x[k], RPGE_k_y[k]+200.0)
        set pid=0
        loop
            exitwhen pid>=RPGE_jogadores or RPGE_entrou(k, pid)
            set pid=pid+1
        endloop
        set h=RPGE_heroi[pid]
        if RPGE_k_tipo[k]==RPGE_DPS then
            call BlzSetUnitMaxHP(u, IMaxBJ(1, R2I(RMinBJ(RPGE_dps_vida*RPGW_principal(h), 2000000000.0))))
            call SetWidgetLife(u, I2R(BlzGetUnitMaxHP(u)))
        else
            call RPGE_vida(u, 15.0)
            call RPGE_cria(k, PLAYER_NEUTRAL_PASSIVE, RPGE_aliado, RPGE_k_x[k]-150.0, RPGE_k_y[k])
            call RPGE_cria(k, PLAYER_NEUTRAL_PASSIVE, RPGE_aliado, RPGE_k_x[k]+150.0, RPGE_k_y[k])
        endif
        set RPGE_k_alvo[k]=u
        set h=null
    endif
    set u=null
endfunction

function RPGE_limpa_cada takes nothing returns nothing
    call RemoveUnit(GetEnumUnit())
endfunction

function RPGE_premio takes integer k, integer pid returns nothing
    local integer f=RPGE_k_faixa[k]
    local unit h=RPGE_heroi[pid]
    local integer tipo
    if RPGE_k_tipo[k]>=RPGE_TANK then
        call SaveBoolean(RPGE_ht, GetHandleId(h), 2, true)
        call RPGW_avancado(h, true)
        call RPGW_sincroniza(h)
        set tipo=GetUnitTypeId(h)
        if LoadStr(RPGE_ht, tipo, 1)!=null then
            call BlzSetHeroProperName(h, LoadStr(RPGE_ht, tipo, 1))
        endif
        call RPGE_diz(pid, "|cffffcc00Trial complete!|r Your advanced form awakens: +1 rank to every skill.")
        set h=null
        return
    endif
    if RPGE_material[f]!=0 then
        call RPGM_soma(pid, RPGE_material[f], 3)
    endif
    if RPGE_comp[f]!=0 and GetRandomReal(0.0, 1.0)<RPGE_comp_ch then
        call RPGM_soma(pid, RPGE_comp[f], 1)
    endif
    if RPGE_k_tipo[k]==RPGE_DEFENDE and RPGE_ron!=0 then
        call RPGM_soma(pid, RPGE_ron, 1)
    endif
    call RPGE_diz(pid, "|cff80ff80"+RPGE_k_nome[k]+" cleared!|r Rewards went to your satchel.")
    set h=null
endfunction

function RPGE_termina takes integer k, boolean venceu returns nothing
    local integer pid=0
    local unit h
    local real sx=RPGE_k_x[k]
    local real sy=RPGE_k_y[k]
    if RPGE_k_pedra[k]!=null then
        set sx=GetUnitX(RPGE_k_pedra[k])
        set sy=GetUnitY(RPGE_k_pedra[k])-200.0
    elseif RPGE_mestre_u!=null then
        set sx=GetUnitX(RPGE_mestre_u)
        set sy=GetUnitY(RPGE_mestre_u)-200.0
    endif
    call ForGroup(RPGE_k_g[k], function RPGE_limpa_cada)
    call GroupClear(RPGE_k_g[k])
    loop
        exitwhen pid>=RPGE_jogadores
        if RPGE_entrou(k, pid) then
            set h=RPGE_heroi[pid]
            if venceu then
                call RPGE_premio(k, pid)
            else
                call RPGE_diz(pid, "|cffff8080"+RPGE_k_nome[k]+" failed.|r You can try again.")
            endif
            if h!=null and GetUnitTypeId(h)!=0 then
                if IsUnitType(h, UNIT_TYPE_DEAD) then
                    call ReviveHero(h, sx, sy, true)
                else
                    call SetUnitPosition(h, sx, sy)
                endif
            endif
        endif
        set pid=pid+1
    endloop
    set RPGE_k_estado[k]=0
    set RPGE_k_quem[k]=0
    set RPGE_k_alvo[k]=null
    set h=null
endfunction

function RPGE_aliados_cada takes nothing returns nothing
    local unit u=GetEnumUnit()
    if GetUnitTypeId(u)==RPGE_aliado then
        if RPGE_vivo(u) then
            set RPGE_c_vivos=RPGE_c_vivos+1
            if RPGE_k_tipo[RPGE_c_k]==RPGE_CURA then
                call SetWidgetLife(u, GetWidgetLife(u)-RPGE_sangra*I2R(BlzGetUnitMaxHP(u)))
            endif
        endif
    endif
    set u=null
endfunction

function RPGE_um takes integer k returns nothing
    local integer tipo=RPGE_k_tipo[k]
    local integer pid=0
    local integer vivos=RPGE_conta(k)
    local unit h
    local unit u
    local real r
    local real dx
    local real dy
    set RPGE_k_t[k]=RPGE_k_t[k]+1.0
    if vivos==0 then
        call RPGE_termina(k, false)
        return
    endif
    if tipo<=RPGE_DEFENDE and RPGE_k_estado[k]==1 and RPGE_k_t[k]>=RPGE_k_onda[k] then
        set RPGE_k_onda[k]=RPGE_k_t[k]+RPGE_onda
        call RPGE_onda_de(k, 3+2*vivos)
    endif
    if tipo==RPGE_ONDAS then
        if RPGE_k_estado[k]==1 and RPGE_k_t[k]>=RPGE_k_dur[k] then
            set RPGE_k_estado[k]=2
            set u=RPGE_cria(k, RPGE_dono, RPGE_lacaio[RPGE_k_faixa[k]], RPGE_k_x[k], RPGE_k_y[k]+200.0)
            call RPGE_vida(u, RPGE_nom_vida)
            call RPGF_aplica(u, 2)
            set RPGE_k_alvo[k]=u
        elseif RPGE_k_estado[k]==2 and not RPGE_vivo(RPGE_k_alvo[k]) then
            call RPGE_termina(k, true)
        endif
    elseif tipo==RPGE_ENCOLHE then
        set r=RPGE_k_raio[k]*RMaxBJ(0.2, 1.0-RPGE_encolhe*I2R(R2I(RPGE_k_t[k]/60.0)))
        loop
            exitwhen pid>=RPGE_jogadores
            set h=RPGE_heroi[pid]
            if RPGE_entrou(k, pid) and RPGE_vivo(h) then
                set dx=GetUnitX(h)-RPGE_k_x[k]
                set dy=GetUnitY(h)-RPGE_k_y[k]
                if dx*dx+dy*dy>r*r then
                    call SetWidgetLife(h, GetWidgetLife(h)-RPGE_fora*I2R(BlzGetUnitMaxHP(h)))
                endif
                if ModuloInteger(R2I(RPGE_k_t[k]+0.5), 60)==0 and RPGE_material[RPGE_k_faixa[k]]!=0 then
                    call RPGM_soma(pid, RPGE_material[RPGE_k_faixa[k]], 1)
                endif
            endif
            set pid=pid+1
        endloop
        if RPGE_k_t[k]>=RPGE_k_dur[k] then
            call RPGE_termina(k, true)
        endif
    elseif tipo==RPGE_DEFENDE then
        if not RPGE_vivo(RPGE_k_alvo[k]) then
            call RPGE_termina(k, false)
        elseif RPGE_k_t[k]>=RPGE_k_dur[k] then
            call RPGE_termina(k, true)
        endif
    elseif tipo==RPGE_TANK then
        if not RPGE_vivo(RPGE_k_alvo[k]) then
            call RPGE_termina(k, false)
        elseif RPGE_k_t[k]>=RPGE_k_dur[k] then
            call RPGE_termina(k, true)
        endif
    elseif tipo==RPGE_CURA or tipo==RPGE_APOIO then
        set RPGE_c_k=k
        set RPGE_c_vivos=0
        call ForGroup(RPGE_k_g[k], function RPGE_aliados_cada)
        if tipo==RPGE_CURA and RPGE_c_vivos<4 then
            call RPGE_termina(k, false)
        elseif tipo==RPGE_APOIO and RPGE_c_vivos==0 then
            call RPGE_termina(k, false)
        elseif tipo==RPGE_APOIO and not RPGE_vivo(RPGE_k_alvo[k]) then
            call RPGE_termina(k, true)
        elseif RPGE_k_t[k]>=RPGE_k_dur[k] then
            call RPGE_termina(k, tipo==RPGE_CURA)
        endif
    elseif tipo==RPGE_DPS then
        if not RPGE_vivo(RPGE_k_alvo[k]) then
            call RPGE_termina(k, true)
        elseif RPGE_k_t[k]>=RPGE_k_dur[k] then
            call RPGE_termina(k, false)
        endif
    endif
    set h=null
    set u=null
endfunction

function RPGE_tiq takes nothing returns nothing
    local integer k=0
    loop
        exitwhen k>=RPGE_n
        if RPGE_k_estado[k]>0 then
            call RPGE_um(k)
        endif
        set k=k+1
    endloop
endfunction

function RPGE_start takes integer pid returns nothing
    local unit h=RPGE_heroi[pid]
    local integer k=0
    local integer i
    local integer quem=0
    local integer soma=0
    local integer n=0
    loop
        exitwhen k>=RPGE_n
        if RPGE_k_pedra[k]!=null and RPGE_perto(h, RPGE_k_pedra[k], 400.0) then
            if RPGE_k_estado[k]>0 then
                call RPGE_diz(pid, "|cffff8080"+RPGE_k_nome[k]+" is already in progress.|r")
            else
                set i=0
                loop
                    exitwhen i>=RPGE_jogadores
                    if RPGE_vivo(RPGE_heroi[i]) and RPGE_perto(RPGE_heroi[i], RPGE_k_pedra[k], RPGE_grupo) then
                        set quem=quem+RPGE_bit(i)
                        set soma=soma+GetHeroLevel(RPGE_heroi[i])
                        set n=n+1
                    endif
                    set i=i+1
                endloop
                call RPGE_comeca(k, quem, RPGE_faixa_de(soma/IMaxBJ(1, n)))
            endif
            set h=null
            return
        endif
        set k=k+1
    endloop
    call RPGE_diz(pid, "|cffff8080Stand next to a dungeon stone.|r")
    set h=null
endfunction

function RPGE_trial takes integer pid returns nothing
    local unit h=RPGE_heroi[pid]
    local integer k=LoadInteger(RPGE_ht, GetUnitTypeId(h), 0)-1
    if not RPGE_perto(h, RPGE_mestre_u, 600.0) then
        call RPGE_diz(pid, "|cffff8080Speak to Tarvin, the Death God, in the Hall of Trials.|r")
    elseif k<0 then
        call RPGE_diz(pid, "|cffff8080Your class has no trial.|r")
    elseif RPGE_avancou(h) then
        call RPGE_diz(pid, "You have already awakened your advanced form.")
    elseif GetHeroLevel(h)<RPGE_prova_nivel then
        call RPGE_diz(pid, "|cffff8080The trial requires level "+I2S(RPGE_prova_nivel)+".|r")
    elseif RPGE_k_estado[k]>0 then
        call RPGE_diz(pid, "|cffff8080Another hero of your class is in the trial. Wait for them.|r")
    else
        call RPGE_comeca(k, RPGE_bit(pid), RPGE_faixa_de(GetHeroLevel(h)))
    endif
    set h=null
endfunction

function RPGE_chat takes nothing returns nothing
    local integer pid=GetPlayerId(GetTriggerPlayer())
    local string s=GetEventPlayerChatString()
    if pid>=RPGE_jogadores or not RPGE_vivo(RPGE_heroi[pid]) then
        return
    endif
    if s=="-start" then
        call RPGE_start(pid)
    elseif s=="-trial" then
        call RPGE_trial(pid)
    endif
endfunction

function RPGE_grava takes nothing returns boolean
    local unit h=RPGE_heroi[RPGS_ev_pid]
    if h!=null and RPGE_avancou(h) then
        call RPGS_poe_i("av", 1)
    endif
    set h=null
    return false
endfunction

function RPGE_nasce takes nothing returns boolean
    local integer pid=RPGH_ev_pid
    local unit h=RPGH_ev_u
    set RPGE_heroi[pid]=h
    if RPGS_ev_ok and RPGS_le_i(pid, "av")==1 then
        call SaveBoolean(RPGE_ht, GetHandleId(h), 2, true)
        call RPGW_avancado(h, true)
        call RPGW_sincroniza(h)
        if LoadStr(RPGE_ht, GetUnitTypeId(h), 1)!=null then
            call BlzSetHeroProperName(h, LoadStr(RPGE_ht, GetUnitTypeId(h), 1))
        endif
    endif
    set h=null
    return false
endfunction

function RPGE_init takes nothing returns nothing
    local integer i=0
    if RPGE_ht!=null then
        return
    endif
    set RPGE_ht=InitHashtable()
    set RPGE_g=CreateGroup()
    set RPGE_t_chat=CreateTrigger()
    loop
        exitwhen i>=RPGE_jogadores
        call TriggerRegisterPlayerChatEvent(RPGE_t_chat, Player(i), "-start", true)
        call TriggerRegisterPlayerChatEvent(RPGE_t_chat, Player(i), "-trial", true)
        set i=i+1
    endloop
    call TriggerAddAction(RPGE_t_chat, function RPGE_chat)
    call RPGS_gancho(RPGS_G_GRAVA, function RPGE_grava)
    call RPGH_gancho(RPGH_G_NASCE, function RPGE_nasce)
    set RPGE_tm=CreateTimer()
    call TimerStart(RPGE_tm, 1.0, true, function RPGE_tiq)
endfunction
