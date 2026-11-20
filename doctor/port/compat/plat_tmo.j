//{{TMO_GLOBAIS}}
hashtable TMOE_ht=InitHashtable()
timer TMOE_relogio=CreateTimer()
integer TMOE_base=0
real TMOE_gravado=-1000.0
boolean TMOE_relogio_lido=false
integer TMOE_n=0
integer TMOE_ncargas=0
boolean TMOE_sondado=false
integer array TMOE_carga
string array TMOE_carga_orig
//{{TMO_FUNCOES}}
function TMOE_Init takes nothing returns nothing
    call TimerStart(TMOE_relogio, 1000000.0, false, null)
endfunction

function TMOE_Barra takes string s,integer de returns integer
    local integer n=StringLength(s)
    loop
        exitwhen de>=n
        if SubString(s, de, de+1)=="|" then
            return de
        endif
        set de=de+1
    endloop
    return -1
endfunction

function TMOE_Escapa takes string s returns string
    local integer i=0
    local integer n=StringLength(s)
    local string c
    local string r=""
    loop
        exitwhen i>=n
        set c=SubString(s, i, i+1)
        if c=="\"" then
            set r=r+"\\\""
        elseif c=="\\" then
            set r=r+"\\\\"
        elseif c=="\n" or c=="\r" then
            set r=r+" "
        else
            set r=r+c
        endif
        set i=i+1
    endloop
    return r
endfunction

function TMOE_Sonda takes nothing returns nothing
    local integer array c
    local integer i=0
    local integer n=24
    local string o
    if TMOE_sondado then
        return
    endif
    set TMOE_sondado=true
    set c[0]='AEsh'
    set c[1]='AEsf'
    set c[2]='AEah'
    set c[3]='AEtq'
    set c[4]='AEer'
    set c[5]='AEfn'
    set c[6]='AEbl'
    set c[7]='AEfk'
    set c[8]='AEst'
    set c[9]='ANbf'
    set c[10]='ANdb'
    set c[11]='ANdh'
    set c[12]='ANef'
    set c[13]='ANdr'
    set c[14]='ANfl'
    set c[15]='ANms'
    set c[16]='ANst'
    set c[17]='ANsg'
    set c[18]='ANsq'
    set c[19]='ANsw'
    set c[20]='ANbr'
    set c[21]='ANrf'
    set c[22]='ANca'
    set c[23]='ANht'
    loop
        exitwhen i>=n
        set o=BlzGetAbilityTooltip(c[i], 0)
        call BlzSetAbilityTooltip(c[i], "@tmo", 0)
        if BlzGetAbilityTooltip(c[i], 0)=="@tmo" then
            set TMOE_carga[TMOE_ncargas]=c[i]
            set TMOE_carga_orig[TMOE_ncargas]=o
            set TMOE_ncargas=TMOE_ncargas+1
        endif
        call BlzSetAbilityTooltip(c[i], o, 0)
        set i=i+1
    endloop
endfunction

function TMOE_Limpa takes nothing returns nothing
    local integer i=0
    loop
        exitwhen i>=TMOE_ncargas
        call BlzSetAbilityTooltip(TMOE_carga[i], "", 0)
        set i=i+1
    endloop
endfunction

function TMOE_Restaura takes nothing returns nothing
    local integer i=0
    loop
        exitwhen i>=TMOE_ncargas
        call BlzSetAbilityTooltip(TMOE_carga[i], TMOE_carga_orig[i], 0)
        set i=i+1
    endloop
endfunction

function TMOE_Grava takes string nome,string corpo returns nothing
    local integer n=StringLength(corpo)
    local integer pos=0
    local integer arq=0
    local integer k=1
    local string pedaco
    call TMOE_Sonda()
    if TMOE_ncargas<2 then
        return
    endif
    call PreloadGenClear()
    call PreloadGenStart()
    call Preload("\")\ncall BlzSetAbilityTooltip("+I2S(TMOE_carga[0])+",\"@TMO"+I2S(n)+";\",0)\n//")
    loop
        exitwhen pos>=n
        if k>=TMOE_ncargas then
            call PreloadGenEnd({{TMO_PASTA}}+nome+"_"+I2S(arq)+".pld")
            set arq=arq+1
            set k=0
            call PreloadGenClear()
            call PreloadGenStart()
        endif
        set pedaco=SubString(corpo, pos, IMinBJ(pos+90, n))
        call Preload("\")\ncall BlzSetAbilityTooltip("+I2S(TMOE_carga[k])+",\""+TMOE_Escapa(pedaco)+"\",0)\n//")
        set pos=pos+90
        set k=k+1
    endloop
    call PreloadGenEnd({{TMO_PASTA}}+nome+"_"+I2S(arq)+".pld")
endfunction

function TMOE_Le takes string nome returns string
    local string cab
    local string r=""
    local string d
    local integer n
    local integer arq=0
    local integer k=1
    call TMOE_Sonda()
    if TMOE_ncargas<2 then
        return "\n"
    endif
    call TMOE_Limpa()
    call Preloader({{TMO_PASTA}}+nome+"_0.pld")
    set cab=BlzGetAbilityTooltip(TMOE_carga[0], 0)
    if SubString(cab, 0, 4)!="@TMO" or SubString(cab, StringLength(cab)-1, StringLength(cab))!=";" then
        call TMOE_Restaura()
        return "\n"
    endif
    set n=S2I(SubString(cab, 4, StringLength(cab)-1))
    loop
        exitwhen StringLength(r)>=n
        if k>=TMOE_ncargas then
            set arq=arq+1
            set k=0
            call TMOE_Limpa()
            call Preloader({{TMO_PASTA}}+nome+"_"+I2S(arq)+".pld")
        endif
        set d=BlzGetAbilityTooltip(TMOE_carga[k], 0)
        if d=="" then
            call TMOE_Restaura()
            return "\n"
        endif
        set r=r+d
        set k=k+1
    endloop
    call TMOE_Restaura()
    if StringLength(r)!=n then
        return "\n"
    endif
    return r
endfunction

function TMOE_Agora takes nothing returns integer
    local string s
    local integer t=0
    local integer dia
    if not TMOE_relogio_lido then
        set TMOE_relogio_lido=true
        set s=TMOE_Le("tmo_relogio")
        if s!="\n" then
            set t=S2I(s)
        endif
        if t<1767225600 then
            set t=1767225600
        endif
        set dia=(t+32400)/86400+1
        set TMOE_base=dia*86400-32400+3600-R2I(TimerGetElapsed(TMOE_relogio))
    endif
    set t=TMOE_base+R2I(TimerGetElapsed(TMOE_relogio))
    if TimerGetElapsed(TMOE_relogio)-TMOE_gravado>=60.0 then
        set TMOE_gravado=TimerGetElapsed(TMOE_relogio)
        call TMOE_Grava("tmo_relogio", I2S(t))
    endif
    return t
endfunction

function TMOE_Pedido takes string estado,string http,string erro,string versao,string corpo returns string
    set TMOE_n=TMOE_n+1
    call SaveStr(TMOE_ht, TMOE_n, 1, estado)
    call SaveStr(TMOE_ht, TMOE_n, 2, http)
    call SaveStr(TMOE_ht, TMOE_n, 3, erro)
    call SaveStr(TMOE_ht, TMOE_n, 4, versao)
    call SaveStr(TMOE_ht, TMOE_n, 5, corpo)
    return I2S(TMOE_n)
endfunction

function TMOE_Slot takes integer slot returns nothing
    local string s
    if LoadBoolean(TMOE_ht, -1-slot, 3) then
        return
    endif
    call SaveBoolean(TMOE_ht, -1-slot, 3, true)
    set s=TMOE_Le("tmo_s"+I2S(slot))
    if s!="\n" and s!="" then
        call SaveStr(TMOE_ht, -1-slot, 2, s)
        call SaveInteger(TMOE_ht, -1-slot, 1, 1)
    endif
endfunction

function TMOE_Saves takes string op,string a returns string
    local integer i=TMOE_Barra(a, 0)
    local integer slot
    local integer v
    local integer b
    local string id
    if i<0 then
        set slot=S2I(a)
    else
        set slot=S2I(SubString(a, 0, i))
    endif
    call TMOE_Slot(slot)
    set v=LoadInteger(TMOE_ht, -1-slot, 1)
    if op=="get" then
        if HaveSavedString(TMOE_ht, -1-slot, 2) then
            return TMOE_Pedido("ok", "200", "", I2S(v), LoadStr(TMOE_ht, -1-slot, 2))
        endif
        return TMOE_Pedido("error", "404", "save_not_found", I2S(v), "")
    elseif op=="put" then
        set b=TMOE_Barra(a, i+1)
        if i<0 or b<0 then
            return "w3a:error:invalid_request"
        endif
        set id=SubString(a, b+1, StringLength(a))
        if not HaveSavedString(TMOE_ht, 0, S2I(id)) then
            return "w3a:error:invalid_buffer"
        endif
        set v=v+1
        call SaveInteger(TMOE_ht, -1-slot, 1, v)
        call SaveStr(TMOE_ht, -1-slot, 2, LoadStr(TMOE_ht, 0, S2I(id)))
        call RemoveSavedString(TMOE_ht, 0, S2I(id))
        call TMOE_Grava("tmo_s"+I2S(slot), LoadStr(TMOE_ht, -1-slot, 2))
        return TMOE_Pedido("ok", "200", "", I2S(v), "")
    endif
    call RemoveSavedString(TMOE_ht, -1-slot, 2)
    set v=v+1
    call SaveInteger(TMOE_ht, -1-slot, 1, v)
    call TMOE_Grava("tmo_s"+I2S(slot), "")
    return TMOE_Pedido("ok", "200", "", I2S(v), "")
endfunction

function TMOE_Request takes string op,string a returns string
    local integer i=TMOE_Barra(a, 0)
    local integer id
    local integer o=0
    local string corpo
    if i<0 then
        set id=S2I(a)
    else
        set id=S2I(SubString(a, 0, i))
        set o=S2I(SubString(a, i+1, StringLength(a)))
    endif
    if not HaveSavedString(TMOE_ht, id, 1) then
        if op=="status" then
            return "error"
        endif
        return ""
    endif
    set corpo=LoadStr(TMOE_ht, id, 5)
    if op=="status" then
        return LoadStr(TMOE_ht, id, 1)
    elseif op=="http" then
        return LoadStr(TMOE_ht, id, 2)
    elseif op=="error" then
        return LoadStr(TMOE_ht, id, 3)
    elseif op=="version" then
        return LoadStr(TMOE_ht, id, 4)
    elseif op=="size" then
        return I2S(StringLength(corpo))
    elseif op=="read" then
        return SubString(corpo, o, IMinBJ(o+1000, StringLength(corpo)))
    elseif op=="next" then
        return I2S(IMinBJ(o+1000, StringLength(corpo)))
    elseif op=="release" then
        call FlushChildHashtable(TMOE_ht, id)
        return "1"
    endif
    return ""
endfunction

function TMOE_LS takes string k returns string
    local integer i=TMOE_Barra(k, 0)
    local string op=k
    local string a=""
    local integer b
    if SubString(k, 0, 4)!="w3a:" then
        return GetLocalizedString(k)
    endif
    if i>=0 then
        set op=SubString(k, 0, i)
        set a=SubString(k, i+1, StringLength(k))
    endif
    if op=="w3a:loaded" or op=="w3a:auth.ready" or op=="w3a:session" or op=="w3a:time.refresh" then
        return "1"
    elseif op=="w3a:time.now" then
        return I2S(TMOE_Agora())
    elseif op=="w3a:buffer.create" then
        set TMOE_n=TMOE_n+1
        call SaveStr(TMOE_ht, 0, TMOE_n, "")
        return I2S(TMOE_n)
    elseif op=="w3a:buffer.append" then
        set b=TMOE_Barra(a, 0)
        if b<0 or not HaveSavedString(TMOE_ht, 0, S2I(SubString(a, 0, b))) then
            return "w3a:error:invalid_buffer"
        endif
        call SaveStr(TMOE_ht, 0, S2I(SubString(a, 0, b)), LoadStr(TMOE_ht, 0, S2I(SubString(a, 0, b)))+SubString(a, b+1, StringLength(a)))
        return "1"
    elseif op=="w3a:buffer.release" then
        call RemoveSavedString(TMOE_ht, 0, S2I(a))
        return "1"
    elseif SubString(op, 0, 10)=="w3a:saves." then
        return TMOE_Saves(SubString(op, 10, StringLength(op)), a)
    elseif SubString(op, 0, 12)=="w3a:request." then
        return TMOE_Request(SubString(op, 12, StringLength(op)), a)
    endif
    return "w3a:error:unsupported"
endfunction
