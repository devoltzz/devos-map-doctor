// ==============================================================================================
// ==============================================================================================

function IsReplayMode takes nothing returns boolean
    return false
endfunction

string array KKN_qcb_nome
integer KKN_qcb_n = 0

function KKN_qcb_tique takes nothing returns nothing
    local integer i=0
    loop
        exitwhen i>=KKN_qcb_n
        call ExecuteFunc(KKN_qcb_nome[i])
        set i=i+1
    endloop
endfunction

function DzFrameSetUpdateCallback takes string xfunc returns nothing
    local integer i=0
    if xfunc==null or xfunc=="" then
        return
    endif
    loop
        exitwhen i>=KKN_qcb_n
        if KKN_qcb_nome[i]==xfunc then
            return
        endif
        set i=i+1
    endloop
    if KKN_qcb_n==0 then
        call DzFrameSetUpdateCallbackByCode(function KKN_qcb_tique)
    endif
    set KKN_qcb_nome[KKN_qcb_n]=xfunc
    set KKN_qcb_n=KKN_qcb_n+1
endfunction

function DzUnlockOpCodeLimit takes boolean enable returns nothing
endfunction

function DzUnlockBlpSizeLimit takes boolean enable returns nothing
endfunction

function DzFixUnitEventMemoryLeak takes nothing returns nothing
endfunction

function DzToggleFPS takes boolean show returns nothing
endfunction

function DzEnableHashtableSetNull takes boolean is_enable returns nothing
endfunction
