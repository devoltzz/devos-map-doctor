//{{KK_SE:KK_LOJA_ISCAS}}
function DB_loja_isca takes string key returns boolean
    local string lista="{{KK_LOJA_ISCAS_LISTA}}"
    local string alvo="|"+key+"|"
    local integer n=StringLength(alvo)
    local integer m=StringLength(lista)
    local integer i=0
    loop
        exitwhen i+n>m
        if SubString(lista, i, i+n)==alvo then
            return true
        endif
        set i=i+1
    endloop
    return false
endfunction
//{{KK_FIMSE:KK_LOJA_ISCAS}}

function DzAPI_Map_HasMallItem takes player whichPlayer,string key returns boolean
    //{{KK_SE:KK_LOJA_ISCAS}}
    if key!=null and DB_loja_isca(key) then
        return false
    endif
    //{{KK_FIMSE:KK_LOJA_ISCAS}}
    return true
endfunction

function DzAPI_Map_GetMapLevel takes player whichPlayer returns integer
    return 30
endfunction

function DzAPI_Map_GetPlatformVIP takes player whichPlayer returns integer
    return 1
endfunction

function DzAPI_Map_IsRedVIP takes player whichPlayer returns boolean
    return true
endfunction

function DzAPI_Map_IsBlueVIP takes player whichPlayer returns boolean
    return true
endfunction
