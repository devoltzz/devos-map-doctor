constant integer KK_PE_MAX=32
trigger array KK_pe_fila
integer KK_pe_n=0
boolean KK_pe_ligado=false
//{{KK_SE:KK_RELOGIO}}
constant integer KK_RL_MAX=256
trigger array KK_rl_fila
real array KK_rl_quando
integer KK_rl_n=0
real KK_rl_primeiro=-1.0
real KK_rl_atraso=0.0
boolean KK_rl_libera=false
timer KK_rl_relogio=null
hashtable KK_rl_ht=InitHashtable()

function KK_relogio_agora takes nothing returns real
    if KK_rl_relogio==null then
        return 0.0
    endif
    return TimerGetElapsed(KK_rl_relogio)
endfunction

function KK_relogio_roda takes trigger t returns nothing
    set KK_rl_libera=true
    call ConditionalTriggerExecute(t)
    set KK_rl_libera=false
endfunction

function KK_relogio_dispara takes nothing returns nothing
    local timer tm=GetExpiredTimer()
    local trigger t=LoadTriggerHandle(KK_rl_ht, GetHandleId(tm), 0)
    call FlushChildHashtable(KK_rl_ht, GetHandleId(tm))
    call DestroyTimer(tm)
    if t!=null then
        call KK_relogio_roda(t)
    endif
    set tm=null
    set t=null
endfunction

function KK_relogio_agenda takes trigger t,real espera returns nothing
    local timer tm
    if espera<=0.0 then
        call KK_relogio_roda(t)
        return
    endif
    set tm=CreateTimer()
    call SaveTriggerHandle(KK_rl_ht, GetHandleId(tm), 0, t)
    call TimerStart(tm, espera, false, function KK_relogio_dispara)
    set tm=null
endfunction

function KK_relogio_espera takes trigger t,real quando returns boolean
    if KK_rl_libera then
        set KK_rl_libera=false
        return false
    endif
    if t==null then
        return false
    endif
    if not DB_rede_pronto then
        if KK_rl_n<KK_RL_MAX then
            set KK_rl_fila[KK_rl_n]=t
            set KK_rl_quando[KK_rl_n]=quando
            set KK_rl_n=KK_rl_n+1
            if KK_rl_primeiro<0.0 or quando<KK_rl_primeiro then
                set KK_rl_primeiro=quando
            endif
            return true
        endif
        return false
    endif
    if KK_rl_atraso<=0.0 then
        return false
    endif
    call KK_relogio_agenda(t, KK_rl_atraso)
    return true
endfunction

function KK_relogio_pronto takes nothing returns nothing
    local integer i=0
    if KK_rl_n==0 then
        return
    endif
    set KK_rl_atraso=KK_relogio_agora()-KK_rl_primeiro
    if KK_rl_atraso<0.0 then
        set KK_rl_atraso=0.0
    endif
    loop
        exitwhen i>=KK_rl_n
        call KK_relogio_agenda(KK_rl_fila[i], KK_rl_quando[i]-KK_rl_primeiro)
        set KK_rl_fila[i]=null
        set i=i+1
    endloop
    set KK_rl_n=0
endfunction
//{{KK_FIMSE:KK_RELOGIO}}

function KK_perfis_pronto takes nothing returns nothing
    local integer i=0
    local trigger t
    loop
        exitwhen i>=KK_pe_n
        set t=KK_pe_fila[i]
        set KK_pe_fila[i]=null
        if t!=null then
            call ConditionalTriggerExecute(t)
        endif
        set i=i+1
    endloop
    set KK_pe_n=0
    set t=null
    //{{KK_SE:KK_RELOGIO}}
    call KK_relogio_pronto()
    //{{KK_FIMSE:KK_RELOGIO}}
endfunction

function KK_perfis_depois takes trigger t returns nothing
    if t==null then
        return
    endif
    if DB_rede_pronto then
        call ConditionalTriggerExecute(t)
        return
    endif
    if KK_pe_n<KK_PE_MAX then
        set KK_pe_fila[KK_pe_n]=t
        set KK_pe_n=KK_pe_n+1
    endif
endfunction

function KK_perfis_prepara takes nothing returns nothing
    local trigger t
    if KK_pe_ligado then
        return
    endif
    set KK_pe_ligado=true
    //{{KK_SE:KK_RELOGIO}}
    set KK_rl_relogio=CreateTimer()
    call TimerStart(KK_rl_relogio, 1000000.0, false, null)
    //{{KK_FIMSE:KK_RELOGIO}}
    set DB_rede_aviso=CreateTrigger()
    call TriggerAddAction(DB_rede_aviso, function KK_perfis_pronto)
    set t=CreateTrigger()
    call TriggerAddAction(t, function DB_rede_init)
    call TriggerExecute(t)
    call DestroyTrigger(t)
    set t=null
endfunction
