// ==============================================================================================
// ==============================================================================================
constant integer KK_PE_MAX=32
trigger array KK_pe_fila
integer KK_pe_n=0
boolean KK_pe_ligado=false

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
    set DB_rede_aviso=CreateTrigger()
    call TriggerAddAction(DB_rede_aviso, function KK_perfis_pronto)
    set t=CreateTrigger()
    call TriggerAddAction(t, function DB_rede_init)
    call TriggerExecute(t)
    call DestroyTrigger(t)
    set t=null
endfunction
