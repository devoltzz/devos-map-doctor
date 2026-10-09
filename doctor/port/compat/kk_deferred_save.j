constant real KK_GA_ESPERA=2.0
timer array KK_ga_tm

function KK_grava_tique takes nothing returns nothing
    local timer t=GetExpiredTimer()
    local integer i=0
    loop
        exitwhen i>=bj_MAX_PLAYER_SLOTS
        if KK_ga_tm[i]==t then
            if not DB_rede_pronto then
                call TimerStart(t, KK_GA_ESPERA, false, function KK_grava_tique)
            else
                call DB_perfil_salva(Player(i))
            endif
            set t=null
            return
        endif
        set i=i+1
    endloop
    set t=null
endfunction

function KK_grava_agenda takes player p returns nothing
    local integer i
    if p==null then
        return
    endif
    if GetPlayerController(p)!=MAP_CONTROL_USER or GetPlayerSlotState(p)!=PLAYER_SLOT_STATE_PLAYING then
        return
    endif
    set i=GetPlayerId(p)
    if KK_ga_tm[i]==null then
        set KK_ga_tm[i]=CreateTimer()
    endif
    call TimerStart(KK_ga_tm[i], KK_GA_ESPERA, false, function KK_grava_tique)
endfunction
