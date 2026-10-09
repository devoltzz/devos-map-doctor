//@GLOBALS
constant string KK_CREDITOS_TITULO="{{KK_CREDITOS_TITULO}}"
constant string KK_CREDITOS_TEXTO="{{KK_CREDITOS_TEXTO}}"
constant string KK_CREDITOS_ICONE="{{KK_CREDITOS_ICONE}}"
boolean KK_creditos_feito=false
//@ENDGLOBALS

function KK_creditos_f9 takes nothing returns nothing
    local quest q
    if KK_creditos_feito then
        return
    endif
    set KK_creditos_feito=true
    set q=CreateQuest()
    call QuestSetTitle(q, KK_CREDITOS_TITULO)
    call QuestSetDescription(q, KK_CREDITOS_TEXTO)
    call QuestSetIconPath(q, KK_CREDITOS_ICONE)
    call QuestSetRequired(q, true)
    call QuestSetDiscovered(q, true)
    call QuestSetCompleted(q, false)
    set q=null
endfunction
