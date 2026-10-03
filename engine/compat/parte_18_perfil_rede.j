// ==============================================================================================
// ==============================================================================================
constant string DB_REDE_PREFIXO="kkpf"
constant integer DB_REDE_PEDACO=200
constant integer DB_REDE_POR_TIQUE=3
constant real DB_REDE_LIMITE=60.0
constant real DB_REDE_AVISO_ESPERA=5.0
boolean DB_rede_on=false
boolean DB_rede_pronto=false
boolean DB_rede_avisou=false
trigger DB_rede_aviso=null
trigger DB_rede_trig=null
trigger DB_rede_saida=null
timer DB_rede_tm=null
real DB_rede_t=0.0
integer DB_rede_falta=0
boolean array DB_rede_espera
boolean array DB_rede_bloq
string array DB_rede_resto
integer array DB_rede_nped
integer array DB_rede_nrec
string array DB_rede_ped
integer DB_rede_np=0
integer DB_rede_nregs=0
integer DB_rede_env=0
boolean DB_rede_fim_env=false

function DB_rede_serializa takes nothing returns nothing
    local player p=GetLocalPlayer()
    local integer i=0
    local string v
    local string buf=""
    set DB_rede_np=0
    set DB_rede_nregs=0
    loop
        exitwhen i>=DB_pk_n
        set v=DB_get(p, DB_pk[i])
        if v!="" then
            set buf=buf+I2S(DB_pk_h[i])+":"+I2S(StringLength(v))+":"+v
            set DB_rede_nregs=DB_rede_nregs+1
            loop
                exitwhen StringLength(buf)<DB_REDE_PEDACO
                set DB_rede_ped[DB_rede_np]=SubString(buf, 0, DB_REDE_PEDACO)
                set DB_rede_np=DB_rede_np+1
                set buf=SubString(buf, DB_REDE_PEDACO, StringLength(buf))
            endloop
        endif
        set i=i+1
    endloop
    if buf!="" then
        set DB_rede_ped[DB_rede_np]=buf
        set DB_rede_np=DB_rede_np+1
    endif
    set p=null
endfunction

function DB_rede_aplica takes player p,string d returns nothing
    local integer id=GetPlayerId(p)
    local integer h=GetHandleId(p)
    local string s=DB_rede_resto[id]+d
    local integer n=StringLength(s)
    local integer i=0
    local integer j
    local integer k
    local integer tam
    loop
        set j=i
        loop
            exitwhen j>=n or SubString(s, j, j+1)==":"
            set j=j+1
        endloop
        exitwhen j>=n
        set k=j+1
        loop
            exitwhen k>=n or SubString(s, k, k+1)==":"
            set k=k+1
        endloop
        exitwhen k>=n
        set tam=S2I(SubString(s, j+1, k))
        exitwhen k+1+tam>n
        call SaveStr(DB_perfil_ht(), h, S2I(SubString(s, i, j)), SubString(s, k+1, k+1+tam))
        set DB_rede_nrec[id]=DB_rede_nrec[id]+1
        set i=k+1+tam
    endloop
    set DB_rede_resto[id]=SubString(s, i, n)
endfunction

function DB_rede_conclui takes nothing returns nothing
    if DB_rede_pronto then
        return
    endif
    set DB_rede_pronto=true
    if DB_rede_tm!=null then
        call PauseTimer(DB_rede_tm)
    endif
    if DB_rede_avisou then
        call DisplayTimedTextToForce(GetPlayersAll(), 8.0, "|cFFFFCC00System: |rAll saved characters are ready.")
    endif
    if DB_rede_aviso!=null then
        call TriggerExecute(DB_rede_aviso)
    endif
endfunction

function DB_rede_termina takes player p,boolean ok returns nothing
    local integer id=GetPlayerId(p)
    if not DB_rede_espera[id] then
        return
    endif
    set DB_rede_espera[id]=false
    set DB_rede_resto[id]=""
    if not ok then
        call FlushChildHashtable(DB_perfil_ht(), GetHandleId(p))
        set DB_rede_bloq[id]=true
    endif
    set DB_rede_falta=DB_rede_falta-1
    if DB_rede_falta<=0 then
        call DB_rede_conclui()
    endif
endfunction

function DB_rede_recebe takes nothing returns nothing
    local player p=GetTriggerPlayer()
    local string d=BlzGetTriggerSyncData()
    local integer id=GetPlayerId(p)
    local string tipo=SubString(d, 0, 1)
    local string r
    local string nome
    local integer c
    if DB_rede_pronto or not DB_rede_espera[id] then
        set p=null
        return
    endif
    if tipo=="D" then
        set DB_rede_nped[id]=DB_rede_nped[id]+1
        call DB_rede_aplica(p, SubString(d, 1, StringLength(d)))
    elseif tipo=="E" then
        set r=SubString(d, 1, StringLength(d))
        set c=DB_pos(r, ":", 0)
        if c>0 and S2I(SubString(r, 0, c))==DB_rede_nped[id] and S2I(SubString(r, c+1, StringLength(r)))==DB_rede_nrec[id] and DB_rede_resto[id]=="" then
            call DB_rede_termina(p, true)
        else
            set nome=GetPlayerName(p)
            call DisplayTimedTextToForce(GetPlayersAll(), 20.0, "|cffff5555The saved character of "+nome+" arrived incomplete. They play a new character in this game; their save file was not touched.|r")
            call DB_rede_termina(p, false)
        endif
    endif
    set p=null
endfunction

function DB_rede_sai takes nothing returns nothing
    if not DB_rede_pronto then
        call DB_rede_termina(GetTriggerPlayer(), false)
    endif
endfunction

function DB_rede_tique takes nothing returns nothing
    local integer k=0
    local string nome
    if DB_rede_pronto then
        call PauseTimer(DB_rede_tm)
        return
    endif
    set DB_rede_t=DB_rede_t+0.10
    if not DB_rede_fim_env and DB_rede_espera[GetPlayerId(GetLocalPlayer())] then
        loop
            exitwhen k>=DB_REDE_POR_TIQUE or DB_rede_fim_env
            if DB_rede_env<DB_rede_np then
                if BlzSendSyncData(DB_REDE_PREFIXO, "D"+DB_rede_ped[DB_rede_env]) then
                    set DB_rede_env=DB_rede_env+1
                endif
            elseif BlzSendSyncData(DB_REDE_PREFIXO, "E"+I2S(DB_rede_np)+":"+I2S(DB_rede_nregs)) then
                set DB_rede_fim_env=true
            endif
            set k=k+1
        endloop
    endif
    if DB_rede_t>=DB_REDE_AVISO_ESPERA and not DB_rede_avisou then
        set DB_rede_avisou=true
        call DisplayTimedTextToForce(GetPlayersAll(), 10.0, "|cFFFFCC00System: |rSharing the saved characters between the players, please wait...")
    endif
    if DB_rede_t>=DB_REDE_LIMITE then
        set k=0
        loop
            exitwhen k>=bj_MAX_PLAYERS
            if DB_rede_espera[k] then
                set nome=GetPlayerName(Player(k))
                call DisplayTimedTextToForce(GetPlayersAll(), 20.0, "|cffff5555The saved character of "+nome+" did not reach the other players in time. They play a new character in this game; their save file was not touched.|r")
                call DB_rede_termina(Player(k), false)
            endif
            set k=k+1
        endloop
    endif
endfunction

function DB_rede_init takes nothing returns nothing
    local integer i=0
    local player p
    if DB_rede_on then
        return
    endif
    set DB_rede_on=true
    call DB_perfil_ht()
    call DB_perfil_garante()
    set DB_rede_trig=CreateTrigger()
    set DB_rede_saida=CreateTrigger()
    loop
        exitwhen i>=bj_MAX_PLAYERS
        set p=Player(i)
        if GetPlayerController(p)==MAP_CONTROL_USER and GetPlayerSlotState(p)==PLAYER_SLOT_STATE_PLAYING then
            set DB_rede_espera[i]=true
            set DB_rede_resto[i]=""
            set DB_rede_falta=DB_rede_falta+1
            call BlzTriggerRegisterPlayerSyncEvent(DB_rede_trig, p, DB_REDE_PREFIXO, false)
            call TriggerRegisterPlayerEventLeave(DB_rede_saida, p)
        endif
        set i=i+1
    endloop
    call TriggerAddAction(DB_rede_trig, function DB_rede_recebe)
    call TriggerAddAction(DB_rede_saida, function DB_rede_sai)
    call DB_rede_serializa()
    call FlushChildHashtable(DB_perfil_ht(), GetHandleId(GetLocalPlayer()))
    set DB_rede_tm=CreateTimer()
    call TimerStart(DB_rede_tm, 0.10, true, function DB_rede_tique)
    if DB_rede_falta<=0 then
        call DB_rede_conclui()
    endif
    set p=null
endfunction
