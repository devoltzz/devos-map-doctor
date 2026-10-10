function DB_tabelas_init takes nothing returns nothing
    if DB_init then
        return
    endif
    set DB_init=true
    call DB_slots_init()
    call DB_hex_init()
    call DB_alfabeto_init()
    call DB_chars_init()
    call DB_c2_init()
    call DB_pot_init()
    call DB_norm_init()
    call DB_code_init()
endfunction

hashtable DB_ht=null
integer array DB_pk_h
string array DB_pk
integer DB_pk_n=0
boolean DB_init=false
boolean DB_sv_capturado=false
constant integer DB_PEDACO=170
constant string DB_RAIZ="{{KK_SAVE_RAIZ}}"
constant integer DB_META_PREFIXO=6
function DB_perfil_ht takes nothing returns hashtable
    if DB_ht==null then
        set DB_ht=InitHashtable()
    endif
    return DB_ht
endfunction

function DB_pos takes string s,string sub,integer ini returns integer
    local integer i=ini
    local integer n=StringLength(s)
    local integer m=StringLength(sub)
    if m==0 or m>n then
        return -1
    endif
    loop
        exitwhen i+m>n
        if SubString(s, i, i+m)==sub then
            return i
        endif
        set i=i+1
    endloop
    return -1
endfunction

function DB_troca takes string s,string de,string para returns string
    local integer p
    local integer n
    local string out=""
    if s==null or de==null or de=="" then
        return s
    endif
    set n=StringLength(de)
    loop
        set p=DB_pos(s, de, 0)
        exitwhen p<0
        set out=out+SubString(s, 0, p)+para
        set s=SubString(s, p+n, StringLength(s))
    endloop
    return out+s
endfunction

string array DB_HEX
function DB_hex_init takes nothing returns nothing
    set DB_HEX[0]="0"
    set DB_HEX[1]="1"
    set DB_HEX[2]="2"
    set DB_HEX[3]="3"
    set DB_HEX[4]="4"
    set DB_HEX[5]="5"
    set DB_HEX[6]="6"
    set DB_HEX[7]="7"
    set DB_HEX[8]="8"
    set DB_HEX[9]="9"
    set DB_HEX[10]="A"
    set DB_HEX[11]="B"
    set DB_HEX[12]="C"
    set DB_HEX[13]="D"
    set DB_HEX[14]="E"
    set DB_HEX[15]="F"
endfunction

function DB_byte takes string ch returns integer
    if ch=="#" then
        return 35
    elseif ch=="." then
        return 46
    elseif ch==" " then
        return 32
    elseif ch=="%" then
        return 37
    elseif ch=="[" then
        return 91
    elseif ch=="]" then
        return 93
    elseif ch=="(" then
        return 40
    elseif ch==")" then
        return 41
    elseif ch=="," then
        return 44
    elseif ch==":" then
        return 58
    elseif ch==";" then
        return 59
    elseif ch=="@" then
        return 64
    endif
    return -1
endfunction

function DB_chars_init takes nothing returns nothing
    local integer i
    if DB_chars_on then
        return
    endif
    set DB_chars_on=true
    set i=0
    loop
        exitwhen i>9
        set DB_OK[i]=DB_DIG[i]
        set i=i+1
    endloop
    set i=0
    loop
        exitwhen i>25
        set DB_OK[10+i]=DB_UP[i]
        set DB_OK[36+i]=DB_LO[i]
        set i=i+1
    endloop
    set DB_OK[62]="_"
    set DB_OK[63]="-"
endfunction

function DB_eh_seguro takes string ch returns boolean
    local integer i=0
    loop
        exitwhen i>63
        if DB_OK[i]==ch then
            return true
        endif
        set i=i+1
    endloop
    return false
endfunction

function DB_safe_name takes string s returns string
    local integer i=0
    local integer b
    local string ch
    local string out=""
    if s==null then
        return ""
    endif
    loop
        exitwhen i>=StringLength(s)
        set ch=SubString(s, i, i+1)
        if DB_eh_seguro(ch) then
            set out=out+ch
        else
            set b=DB_byte(ch)
            if b>=0 then
                set out=out+"%"+DB_HEX[b/16]+DB_HEX[b-b/16*16]
            else
                set out=out+ch
            endif
        endif
        set i=i+1
    endloop
    return out
endfunction

string array DB_OK
boolean DB_chars_on=false

string array DB_DIG
string array DB_UP
string array DB_LO
function DB_alfabeto_init takes nothing returns nothing
    set DB_DIG[0]="0"
    set DB_DIG[1]="1"
    set DB_DIG[2]="2"
    set DB_DIG[3]="3"
    set DB_DIG[4]="4"
    set DB_DIG[5]="5"
    set DB_DIG[6]="6"
    set DB_DIG[7]="7"
    set DB_DIG[8]="8"
    set DB_DIG[9]="9"
    set DB_UP[0]="A"
    set DB_UP[1]="B"
    set DB_UP[2]="C"
    set DB_UP[3]="D"
    set DB_UP[4]="E"
    set DB_UP[5]="F"
    set DB_UP[6]="G"
    set DB_UP[7]="H"
    set DB_UP[8]="I"
    set DB_UP[9]="J"
    set DB_UP[10]="K"
    set DB_UP[11]="L"
    set DB_UP[12]="M"
    set DB_UP[13]="N"
    set DB_UP[14]="O"
    set DB_UP[15]="P"
    set DB_UP[16]="Q"
    set DB_UP[17]="R"
    set DB_UP[18]="S"
    set DB_UP[19]="T"
    set DB_UP[20]="U"
    set DB_UP[21]="V"
    set DB_UP[22]="W"
    set DB_UP[23]="X"
    set DB_UP[24]="Y"
    set DB_UP[25]="Z"
    set DB_LO[0]="a"
    set DB_LO[1]="b"
    set DB_LO[2]="c"
    set DB_LO[3]="d"
    set DB_LO[4]="e"
    set DB_LO[5]="f"
    set DB_LO[6]="g"
    set DB_LO[7]="h"
    set DB_LO[8]="i"
    set DB_LO[9]="j"
    set DB_LO[10]="k"
    set DB_LO[11]="l"
    set DB_LO[12]="m"
    set DB_LO[13]="n"
    set DB_LO[14]="o"
    set DB_LO[15]="p"
    set DB_LO[16]="q"
    set DB_LO[17]="r"
    set DB_LO[18]="s"
    set DB_LO[19]="t"
    set DB_LO[20]="u"
    set DB_LO[21]="v"
    set DB_LO[22]="w"
    set DB_LO[23]="x"
    set DB_LO[24]="y"
    set DB_LO[25]="z"
endfunction

string array DB_nome_cru

function DB_nomes_crus takes nothing returns nothing
    local integer k=0
    loop
        exitwhen k>=bj_MAX_PLAYER_SLOTS
        if DB_nome_cru[k]==null or DB_nome_cru[k]=="" then
            set DB_nome_cru[k]=GetPlayerName(Player(k))
        endif
        set k=k+1
    endloop
endfunction

function DB_nome_conta takes player p returns string
    local integer i=GetPlayerId(p)
    local string n=GetPlayerName(p)
    if DB_pos(n, "|", 0)<0 then
        set DB_nome_cru[i]=n
        return n
    endif
    if DB_nome_cru[i]!=null and DB_nome_cru[i]!="" then
        return DB_nome_cru[i]
    endif
    return n
endfunction

function DB_conta takes nothing returns string
    return DB_safe_name(DB_nome_conta(GetLocalPlayer()))
endfunction

function DB_dir takes nothing returns string
    return DB_RAIZ+DB_conta()+"\\"
endfunction

function DB_caminho takes string nome,integer parte returns string
    return DB_dir()+nome+I2S(parte)+".pld"
endfunction

function DB_caminho_meta takes string prefixo returns string
    return DB_dir()+prefixo+"meta.pld"
endfunction

function DB_chave_pos takes string k returns integer
    local integer hk=StringHash(k)
    local integer lo=0
    local integer hi=DB_pk_n-1
    local integer meio
    loop
        exitwhen lo>hi
        set meio=(lo+hi)/2
        if DB_pk_h[meio]==hk then
            return meio
        elseif DB_pk_h[meio]<hk then
            set lo=meio+1
        else
            set hi=meio-1
        endif
    endloop
    return -lo-1
endfunction

function DB_chave_add takes string k returns nothing
    local integer hk=StringHash(k)
    local integer p=DB_chave_pos(k)
    local integer i
    if p>=0 or DB_pk_n>=DB_MAX then
        return
    endif
    set p=-p-1
    set i=DB_pk_n
    loop
        exitwhen i<=p
        set DB_pk[i]=DB_pk[i-1]
        set DB_pk_h[i]=DB_pk_h[i-1]
        set i=i-1
    endloop
    set DB_pk[p]=k
    set DB_pk_h[p]=hk
    set DB_pk_n=DB_pk_n+1
endfunction

t_natives.lua:4731, "profile.v1." .. tostring(k)).
constant string DB_NS="profile.v1."

function DB_ns takes string chave returns string
    if chave==null or chave=="" then
        return chave
    endif
    if SubString(chave, 0, 11)=="profile.v1." then
        return chave
    endif
    return DB_NS+chave
endfunction

function DB_put takes player p,string chave,string valor returns nothing
    if p==null or chave==null or chave=="" then
        return
    endif
    set chave=DB_ns(chave)
    if valor==null then
        set valor=""
    endif
    call SaveStr(DB_perfil_ht(), GetHandleId(p), StringHash(chave), valor)
    call DB_chave_add(chave)
endfunction

function DB_get takes player p,string chave returns string
    local integer h
    local string v
    if p==null or chave==null or chave=="" then
        return ""
    endif
    set chave=DB_ns(chave)
    set h=GetHandleId(p)
    if not HaveSavedString(DB_perfil_ht(), h, StringHash(chave)) then
        return ""
    endif
    set v=LoadStr(DB_perfil_ht(), h, StringHash(chave))
    if v==null then
        return ""
    endif
    return v
endfunction

function DB_esc takes string s returns string
    set s=DB_troca(s, "\\", "\\\\")
    set s=DB_troca(s, "|", "\\|")
    set s=DB_troca(s, "=", "\\=")
    return s
endfunction

function DB_unesc takes string s returns string
    set s=DB_troca(s, "\\|", "|")
    set s=DB_troca(s, "\\=", "=")
    set s=DB_troca(s, "\\\\", "\\")
    return s
endfunction

function DB_encode takes player p returns string
    local integer i=0
    local string out=""
    local string v
    loop
        exitwhen i>=DB_pk_n
        set v=DB_get(p, DB_pk[i])
        if v!="" then
            if out!="" then
                set out=out+"|"
            endif
            set out=out+DB_esc(DB_pk[i])+"="+DB_esc(v)
        endif
        set i=i+1
    endloop
    return out
endfunction

function DB_pad5 takes integer n returns string
    if n<10 then
        return "0000"+I2S(n)
    elseif n<100 then
        return "000"+I2S(n)
    elseif n<1000 then
        return "00"+I2S(n)
    elseif n<10000 then
        return "0"+I2S(n)
    endif
    return I2S(n)
endfunction

function DB_esc_jass takes string s returns string
    set s=DB_troca(s, "\\", "\\\\")
    set s=DB_troca(s, "\"", "\\\"")
    set s=DB_troca(s, "\n", "\\n")
    set s=DB_troca(s, "\r", "\\r")
    return s
endfunction

function DB_grava takes player p returns boolean
    local string blob
    local integer total
    local integer f
    local integer idx
    local integer base
    local string pedaco
    local string linha
    local integer nfiles
    local integer nslots
    if p==null then
        return false
    endif
    if not DB_init then
        set DB_init=true
        call DB_slots_init()
        call DB_hex_init()
        call DB_alfabeto_init()
        call DB_chars_init()
    endif
    set nslots=DB_SLOT_N
    if nslots<1 then
        return false
    endif
    set blob=DB_encode(p)
    set total=StringLength(blob)
    set nfiles=(total/(DB_PEDACO*nslots))+1
    if nfiles<1 then
        set nfiles=1
    endif
    set f=1
    loop
        exitwhen f>nfiles
        call PreloadGenClear()
        call PreloadGenStart()
        set base=(f-1)*nslots
        set idx=0
        loop
            exitwhen idx>=nslots
            if (base+idx)*DB_PEDACO>=total then
                exitwhen true
            endif
            set pedaco=SubString(blob, (base+idx)*DB_PEDACO, (base+idx)*DB_PEDACO+DB_PEDACO)
            if DB_slot_kind[idx]==0 then
                set linha="call BlzSetAbilityTooltip("+DB_slot_txt[idx]+",\"@00000\",0)"
            else
                set linha="call BlzSetAbilityExtendedTooltip("+DB_slot_txt[idx]+",\"@00000\",0)"
            endif
            if DB_slot_kind[idx]==0 then
                set linha="call BlzSetAbilityTooltip("+DB_slot_txt[idx]+",\"@"+DB_pad5(base+idx)+DB_esc_jass(pedaco)+"\",0)"
            else
                set linha="call BlzSetAbilityExtendedTooltip("+DB_slot_txt[idx]+",\"@"+DB_pad5(base+idx)+DB_esc_jass(pedaco)+"\",0)"
            endif
            call Preload("\")\n"+linha+"\n//")
            set idx=idx+1
        endloop
        call PreloadGenEnd(DB_caminho("profile_", f))
        set f=f+1
    endloop
    call PreloadGenClear()
    call PreloadGenStart()
    call Preload("\")\ncall BlzSetAbilityTooltip("+DB_slot_txt[0]+",\"@META "+I2S(nfiles)+" "+I2S(nslots)+" "+I2S(total)+"\",0)\n//")
    call PreloadGenEnd(DB_caminho_meta(""))
    return true
endfunction

function DB_le_meta takes nothing returns string
    local string v=BlzGetAbilityTooltip(DB_slot_code[0], 0)
    if v==null then
        return ""
    endif
    return v
endfunction

function DB_le_pedaco takes integer idx returns string
    local string v
    local integer p
    if DB_slot_kind[idx]==0 then
        set v=BlzGetAbilityTooltip(DB_slot_code[idx], 0)
    else
        set v=BlzGetAbilityExtendedTooltip(DB_slot_code[idx], 0)
    endif
    if v==null then
        return ""
    endif
    if SubString(v, 0, 1)!="@" then
        return ""
    endif
    set p=DB_META_PREFIXO
    if StringLength(v)<=p then
        return ""
    endif
    return SubString(v, p, StringLength(v))
endfunction

function DB_campo takes string s,integer n returns string
    local integer i=0
    local integer ini
    local integer fim
    set ini=DB_pos(s, " ", 0)
    if ini<0 then
        return "0"
    endif
    set ini=ini+1
    loop
        exitwhen i>=n
        set fim=DB_pos(s, " ", ini)
        if fim<0 then
            return "0"
        endif
        set ini=fim+1
        set i=i+1
    endloop
    set fim=DB_pos(s, " ", ini)
    if fim<0 then
        set fim=StringLength(s)
    endif
    return SubString(s, ini, fim)
endfunction

function DB_sv_captura takes nothing returns nothing
    local integer i=0
    loop
        exitwhen i>=DB_SLOT_N
        if DB_slot_kind[i]==0 then
            set DB_slot_tip_orig[i]=BlzGetAbilityTooltip(DB_slot_code[i], 0)
        else
            set DB_slot_ubt_orig[i]=BlzGetAbilityExtendedTooltip(DB_slot_code[i], 0)
        endif
        set i=i+1
    endloop
    set DB_sv_capturado=true
endfunction

function DB_restaura takes nothing returns nothing
    local integer i=0
    if not DB_sv_capturado then
        return
    endif
    loop
        exitwhen i>=DB_SLOT_N
        if DB_slot_kind[i]==0 then
            call BlzSetAbilityTooltip(DB_slot_code[i], DB_slot_tip_orig[i], 0)
        else
            call BlzSetAbilityExtendedTooltip(DB_slot_code[i], DB_slot_ubt_orig[i], 0)
        endif
        set i=i+1
    endloop
endfunction

function DB_decode takes player p,string blob returns nothing
    local integer i=0
    local integer n=StringLength(blob)
    local string campo=""
    local integer eq
    loop
        exitwhen i>n
        if i==n or SubString(blob, i, i+1)=="|" then
            set eq=DB_pos(campo, "=", 0)
            if eq>0 then
                call DB_put(p, DB_unesc(SubString(campo, 0, eq)), DB_unesc(SubString(campo, eq+1, StringLength(campo))))
            endif
            set campo=""
        else
            set campo=campo+SubString(blob, i, i+1)
        endif
        set i=i+1
    endloop
endfunction

function DB_srv_ns takes integer dataType returns string
    if dataType==38 or dataType==39 or dataType==103 then
        return "ex~"
    elseif dataType==36 or dataType==37 then
        return "gl~"
    endif
    return "pb~"
endfunction

//{{KK_SE:KK_SRV_BACKEND}}
timer DB_srv_relogio=null
timer DB_srv_aviso_tmr=null
hashtable DB_srv_aviso_ht=null
integer DB_srv_aviso_n=0

function DB_srv_agora takes nothing returns integer
    if DB_srv_relogio==null then
        set DB_srv_relogio=CreateTimer()
        call TimerStart(DB_srv_relogio, 1000000.0, false, null)
    endif
    return 1+R2I(TimerGetElapsed(DB_srv_relogio))
endfunction

function DB_srv_envia takes string prefixo,string dado returns nothing
    call BlzSendSyncData(prefixo, dado)
endfunction

function DB_srv_aviso_passa takes nothing returns nothing
    local integer i=0
    loop
        exitwhen i>=DB_srv_aviso_n
        if GetLocalPlayer()==Player(LoadInteger(DB_srv_aviso_ht, i, 0)) then
            call DB_srv_envia(LoadStr(DB_srv_aviso_ht, i, 1), LoadStr(DB_srv_aviso_ht, i, 2))
        endif
        set i=i+1
    endloop
    set DB_srv_aviso_n=0
endfunction

function DB_srv_avisa takes player p,string prefixo,string dado returns nothing
    if DB_srv_aviso_ht==null then
        set DB_srv_aviso_ht=InitHashtable()
        set DB_srv_aviso_tmr=CreateTimer()
    endif
    call SaveInteger(DB_srv_aviso_ht, DB_srv_aviso_n, 0, GetPlayerId(p))
    call SaveStr(DB_srv_aviso_ht, DB_srv_aviso_n, 1, prefixo)
    call SaveStr(DB_srv_aviso_ht, DB_srv_aviso_n, 2, dado)
    set DB_srv_aviso_n=DB_srv_aviso_n+1
    call TimerStart(DB_srv_aviso_tmr, 0.50, false, function DB_srv_aviso_passa)
endfunction

function DB_srv_backend takes integer dataType,player p,string k,string g returns boolean
    if dataType==1009 then
        return true
    endif
    if p==null or k==null or k=="" then
        return false
    endif
    call DB_perfil_garante()
    if dataType==84 then
        return DB_get(p, "bl~"+k)!=""
    elseif dataType==83 then
        if DB_get(p, "bl~"+k)!="" then
            return false
        endif
        if g==null then
            set g=""
        endif
        call DB_put(p, "bl~"+k, I2S(GetRandomInt(1, 2147483646)))
        call DB_put(p, "blt~"+k, I2S(DB_srv_agora()))
        call DB_put(p, "blg~"+k, g)
        call DB_srv_avisa(p, "DZBLU", k)
        return true
    elseif dataType==89 then
        if DB_get(p, "bl~"+k)!="" then
            call DB_put(p, "bl~"+k, "")
            call DB_put(p, "blt~"+k, "")
            call DB_put(p, "blg~"+k, "")
            call DB_srv_avisa(p, "DZBLD", k)
        endif
        return true
    endif
    return false
endfunction

function DB_srv_hex8 takes integer v returns string
    local string s=""
    local integer i=0
    loop
        exitwhen i>=8
        set s=SubString("0123456789abcdef", BlzBitAnd(v, 15), BlzBitAnd(v, 15)+1)+s
        set v=BlzBitAnd(BlzBitAnd(v, -16)/16, 0x0FFFFFFF)
        set i=i+1
    endloop
    return s
endfunction

function DB_srv_guid takes player p returns string
    local string n=DB_nome_conta(p)
    return DB_srv_hex8(StringHash("kkguid:"+n))+DB_srv_hex8(StringHash(n+":kkguid"))+DB_srv_hex8(StringHash("kkg2:"+n))+DB_srv_hex8(StringHash(n+":kkg2"))
endfunction
//{{KK_FIMSE:KK_SRV_BACKEND}}

function RequestExtraIntegerData takes integer dataType,player whichPlayer,string param1,string param2,boolean param3,integer param4,integer param5,integer param6 returns integer
    if dataType==4 or dataType==5 then
        call DB_perfil_garante()
    endif
    if dataType==5 then
        return S2I(DB_get(whichPlayer, param1))
    endif
    if dataType==4 then
        call DB_put(whichPlayer, param1, param2)
        //{{KK_INCLUI:apos_store}}
        return 0
    endif
    //{{KK_INCLUI:plataforma_inteiro}}
    if dataType==30 or dataType==41 then
        return 1
    elseif dataType==82 then
        return 999999
    endif
    //{{KK_SE:KK_SRV_BACKEND}}
    if (dataType==85 or dataType==87) and whichPlayer!=null and param1!=null and param1!="" then
        call DB_perfil_garante()
        if dataType==85 then
            return S2I(DB_get(whichPlayer, "bl~"+param1))
        endif
        return S2I(DB_get(whichPlayer, "blt~"+param1))
    elseif dataType==101 then
        return 999999
    endif
    //{{KK_FIMSE:KK_SRV_BACKEND}}
    return 0
endfunction

function RequestExtraBooleanData takes integer dataType,player whichPlayer,string param1,string param2,boolean param3,integer param4,integer param5,integer param6 returns boolean
    if dataType==4 then
        call DB_perfil_garante()
    endif
    if dataType==4 then
        if whichPlayer==null or param1==null or param1=="" then
            return false
        endif
        call DB_put(whichPlayer, param1, param2)
        //{{KK_INCLUI:apos_store}}
        return true
    endif
    //{{KK_INCLUI:plataforma_booleano}}
    if dataType==39 or dataType==103 or dataType==37 or dataType==31 then
        if whichPlayer==null or param1==null or param1=="" then
            return false
        endif
        call DB_perfil_garante()
        call DB_put(whichPlayer, DB_srv_ns(dataType)+param1, param2)
        return true
    elseif dataType==10 or dataType==42 or dataType==102 or dataType==104 then
        return true
    endif
    //{{KK_SE:KK_SRV_BACKEND}}
    if dataType==83 or dataType==84 or dataType==89 or dataType==1009 then
        return DB_srv_backend(dataType, whichPlayer, param1, param2)
    endif
    //{{KK_FIMSE:KK_SRV_BACKEND}}
    return false
endfunction

function RequestExtraStringData takes integer dataType,player whichPlayer,string param1,string param2,boolean param3,integer param4,integer param5,integer param6 returns string
    if dataType==5 then
        call DB_perfil_garante()
    endif
    if dataType==5 then
        return DB_get(whichPlayer, param1)
    endif
    if dataType==81 and whichPlayer!=null then
        return DB_nome_conta(whichPlayer)
    endif
    //{{KK_INCLUI:plataforma_texto}}
    if dataType==38 or dataType==36 or dataType==32 then
        call DB_perfil_garante()
        return DB_get(whichPlayer, DB_srv_ns(dataType)+param1)
    elseif dataType==37 and whichPlayer!=null and param1!=null and param1!="" then
        call DB_perfil_garante()
        call DB_put(whichPlayer, DB_srv_ns(dataType)+param1, param2)
    endif
    //{{KK_SE:KK_SRV_BACKEND}}
    if (dataType==86 or dataType==88) and whichPlayer!=null and param1!=null and param1!="" then
        call DB_perfil_garante()
        if dataType==86 then
            return DB_get(whichPlayer, "bl~"+param1)
        endif
        return DB_get(whichPlayer, "blg~"+param1)
    elseif dataType==93 and whichPlayer!=null then
        return DB_srv_guid(whichPlayer)
    endif
    //{{KK_FIMSE:KK_SRV_BACKEND}}
    return ""
endfunction

function RequestExtraRealData takes integer dataType,player whichPlayer,string param1,string param2,boolean param3,integer param4,integer param5,integer param6 returns real
    if dataType==5 then
        return S2R(DB_get(whichPlayer, param1))
    endif
    if dataType==4 then
        call DB_put(whichPlayer, param1, param2)
        //{{KK_INCLUI:apos_store}}
    endif
    return 0.0
endfunction

//{{KK_INCLUI:loja}}

hashtable DB_frame_ht=null

function DB_fid takes framehandle f returns integer
    local integer id
    if f==null then
        return 0
    endif
    if DB_frame_ht==null then
        set DB_frame_ht=InitHashtable()
    endif
    set id=GetHandleId(f)
    if not HaveSavedHandle(DB_frame_ht,id,0) then
        call SaveFrameHandle(DB_frame_ht,id,0,f)
        set DB_frame_n=DB_frame_n+1
    endif
    return id
endfunction

function DB_fh takes integer id returns framehandle
    if id==0 or DB_frame_ht==null then
        return null
    endif
    return LoadFrameHandle(DB_frame_ht,id,0)
endfunction

function DB_init_pontos takes nothing returns nothing
    set DB_ponto[0]=FRAMEPOINT_TOPLEFT
    set DB_ponto[1]=FRAMEPOINT_TOP
    set DB_ponto[2]=FRAMEPOINT_TOPRIGHT
    set DB_ponto[3]=FRAMEPOINT_LEFT
    set DB_ponto[4]=FRAMEPOINT_CENTER
    set DB_ponto[5]=FRAMEPOINT_RIGHT
    set DB_ponto[6]=FRAMEPOINT_BOTTOMLEFT
    set DB_ponto[7]=FRAMEPOINT_BOTTOM
    set DB_ponto[8]=FRAMEPOINT_BOTTOMRIGHT
endfunction

function DB_p takes integer i returns framepointtype
    if i<0 or i>8 then
        return FRAMEPOINT_CENTER
    endif
    if DB_ponto[4]==null then
        call DB_init_pontos()
    endif
    return DB_ponto[i]
endfunction

integer array DB_zr0
integer array DB_zr1
//{{KK_SE:KK_Z_4}}
integer array DB_zr2
integer array DB_zr3
//{{KK_FIMSE:KK_Z_4}}
integer array DB_zi
boolean DB_z_pronto=false
real DB_z_ox=0.0
real DB_z_oy=0.0
integer DB_z_w=0
integer DB_z_h=0
integer DB_z_n=0
integer DB_z_va=0
integer DB_z_vb=0

function DB_z_run takes integer k returns integer
    if k<32768 then
        return DB_zr0[k]
    endif
    //{{KK_SE:KK_Z_4}}
    if k>=65536 then
        if k<98304 then
            return DB_zr2[k-65536]
        endif
        return DB_zr3[k-98304]
    endif
    //{{KK_FIMSE:KK_Z_4}}
    return DB_zr1[k-32768]
endfunction

function DB_z_par takes integer i,integer j returns nothing
    local integer lo=DB_zi[j]
    local integer hi=DB_zi[j+1]-1
    local integer fim=hi
    local integer mid
    local integer v
    loop
        exitwhen lo>=hi
        set mid=(lo+hi+1)/2
        if DB_z_run(mid)/16384<=i then
            set lo=mid
        else
            set hi=mid-1
        endif
    endloop
    set v=DB_z_run(lo)
    set DB_z_va=v-(v/16384)*16384
    set DB_z_vb=DB_z_va
    if lo<fim then
        set v=DB_z_run(lo+1)
        if v/16384<=i+1 then
            set DB_z_vb=v-(v/16384)*16384
        endif
    endif
endfunction

function KK_z takes real x,real y returns real
    local real fx
    local real fy
    local integer i
    local integer j
    local real a
    local real b
    if DB_z_w<2 or DB_z_h<2 then
        return 0.0
    endif
    set fx=(x-DB_z_ox)/128.0
    set fy=(y-DB_z_oy)/128.0
    if fx<0.0 then
        set fx=0.0
    elseif fx>I2R(DB_z_w-1) then
        set fx=I2R(DB_z_w-1)
    endif
    if fy<0.0 then
        set fy=0.0
    elseif fy>I2R(DB_z_h-1) then
        set fy=I2R(DB_z_h-1)
    endif
    set i=R2I(fx)
    if i>DB_z_w-2 then
        set i=DB_z_w-2
    endif
    set j=R2I(fy)
    if j>DB_z_h-2 then
        set j=DB_z_h-2
    endif
    set fx=fx-I2R(i)
    set fy=fy-I2R(j)
    call DB_z_par(i,j)
    set a=I2R(DB_z_va)+(I2R(DB_z_vb)-I2R(DB_z_va))*fx
    call DB_z_par(i,j+1)
    set b=I2R(DB_z_va)+(I2R(DB_z_vb)-I2R(DB_z_va))*fx
    return (a+(b-a)*fy-4096.0)*0.25
endfunction

function KK_zl takes location l returns real
    if l==null then
        return 0.0
    endif
    return KK_z(GetLocationX(l),GetLocationY(l))
endfunction

function DB_z_efeito takes effect e,real x,real y returns real
    if DB_z_pronto then
        return KK_z(x,y)
    endif
    return BlzGetLocalSpecialEffectZ(e)
endfunction

hashtable DB_ef_ht=null
integer DB_ef_anel=0
constant integer DB_EF_MAX=16384
widget array DB_ef_segue
effect DB_efx_ultimo=null
boolean array DB_ef_vivo
constant integer DB_EF_PULA=64
boolean array DB_ef_pend
boolean array DB_ef_msc
boolean array DB_ef_assado
unit array DB_ef_uni
constant boolean DB_CAR_LIGADO={{KK_CAR_LIGADO}}
unit array DB_ef_car
effect array DB_ef_vis
boolean array DB_ef_sinc
boolean array DB_ef_solto
integer array DB_ef_cor
integer array DB_ef_alfa
real array DB_ef_vel
integer array DB_ef_anim
real array DB_ef_mx
real array DB_ef_my
real array DB_ef_mz
boolean array DB_ef_oculto
unit array DB_car_fila
integer array DB_car_prazo
integer DB_car_n=0
integer DB_car_tique=0
timer DB_car_tmr=null
constant integer DB_CAR_MAX=4096
constant integer DB_CAR_ESPERA=10
boolean KK_teste_ligado=false
effect array DB_efp_e
integer array DB_efp_i
integer DB_efp_n=0
timer DB_efp_tmr=null
constant integer DB_EFP_MAX=4096

function DB_ef_slot_novo takes integer id returns integer
    local integer i
    local integer k
    if DB_ef_ht==null then
        set DB_ef_ht=InitHashtable()
    endif
    if DB_ef_n<DB_EF_MAX then
        set i=DB_ef_n
        set DB_ef_n=i+1
    else
        set k=0
        loop
            set i=DB_ef_anel
            set DB_ef_anel=DB_ef_anel+1
            if DB_ef_anel>=DB_EF_MAX then
                set DB_ef_anel=0
            endif
            set k=k+1
            exitwhen (not DB_ef_vivo[i]) or k>=DB_EF_PULA
        endloop
        if LoadInteger(DB_ef_ht,DB_ef_id[i],0)==i+1 then
            call RemoveSavedInteger(DB_ef_ht,DB_ef_id[i],0)
        endif
    endif
    call SaveInteger(DB_ef_ht,id,0,i+1)
    set DB_ef_vivo[i]=true
    set DB_ef_id[i]=id
    set DB_ef_x[i]=0.0
    set DB_ef_y[i]=0.0
    set DB_ef_z[i]=0.0
    set DB_ef_rx[i]=0.0
    set DB_ef_ry[i]=0.0
    set DB_ef_rz[i]=0.0
    set DB_ef_size[i]=1.0
    set DB_ef_segue[i]=null
    set DB_ef_pend[i]=false
    set DB_ef_msc[i]=false
    if DB_ef_uni[i]!=null then
        call RemoveUnit(DB_ef_uni[i])
        set DB_ef_uni[i]=null
    endif
    if DB_ef_vis[i]!=null then
        call DestroyEffect(DB_ef_vis[i])
        set DB_ef_vis[i]=null
        call RemoveUnit(DB_ef_car[i])
    endif
    set DB_ef_car[i]=null
    set DB_ef_sinc[i]=false
    set DB_ef_solto[i]=false
    set DB_ef_cor[i]=-1
    set DB_ef_alfa[i]=255
    set DB_ef_vel[i]=1.0
    set DB_ef_anim[i]=-1
    set DB_ef_mx[i]=1.0
    set DB_ef_my[i]=1.0
    set DB_ef_mz[i]=1.0
    set DB_ef_oculto[i]=false
    //{{KK_SE:KK_FX_LOCAL}}
    set DB_ef_fxc[i]=0
    set DB_ef_fxd[i]=null
    //{{KK_FIMSE:KK_FX_LOCAL}}
    return i
endfunction

function DB_ef takes effect e returns integer
    local integer i
    local integer id
    if e==null then
        return -1
    endif
    set id=GetHandleId(e)
    if DB_ef_ht!=null then
        set i=LoadInteger(DB_ef_ht,id,0)-1
        if i>=0 then
            return i
        endif
    endif
    set i=DB_ef_slot_novo(id)
    set DB_ef_x[i]=BlzGetLocalSpecialEffectX(e)
    set DB_ef_y[i]=BlzGetLocalSpecialEffectY(e)
    set DB_ef_z[i]=BlzGetLocalSpecialEffectZ(e)
    set DB_ef_size[i]=BlzGetSpecialEffectScale(e)
    return i
endfunction

function DB_ef_idx takes effect e returns integer
    if e==null or DB_ef_ht==null then
        return -1
    endif
    return LoadInteger(DB_ef_ht,GetHandleId(e),0)-1
endfunction

function DB_efx_cria takes string modelo,real x,real y returns effect
    local integer i
    //{{KK_SE:KK_FX_LOCAL}}
    local string kk_fx_orig=modelo
    set modelo=KK_fx_m(modelo)
    //{{KK_FIMSE:KK_FX_LOCAL}}
    set DB_efx_ultimo=AddSpecialEffect(modelo,x,y)
    //{{KK_SE:KK_FX_LOCAL}}
    set modelo=kk_fx_orig
    //{{KK_FIMSE:KK_FX_LOCAL}}
    if DB_efx_ultimo!=null then
        set i=DB_ef_slot_novo(GetHandleId(DB_efx_ultimo))
        call SaveStr(DB_ef_ht,GetHandleId(DB_efx_ultimo),1,modelo)
        //{{KK_SE:KK_FX_LOCAL}}
        call KK_fx_anota(i)
        //{{KK_FIMSE:KK_FX_LOCAL}}
        set DB_ef_x[i]=x
        set DB_ef_y[i]=y
        set DB_ef_z[i]=DB_z_efeito(DB_efx_ultimo,x,y)
        set DB_ef_sinc[i]=true
    endif
    return DB_efx_ultimo
endfunction

function DB_efx_cria_loc takes string modelo,location onde returns effect
    local integer i
    //{{KK_SE:KK_FX_LOCAL}}
    local string kk_fx_orig=modelo
    set modelo=KK_fx_m(modelo)
    //{{KK_FIMSE:KK_FX_LOCAL}}
    set DB_efx_ultimo=AddSpecialEffectLoc(modelo,onde)
    //{{KK_SE:KK_FX_LOCAL}}
    set modelo=kk_fx_orig
    //{{KK_FIMSE:KK_FX_LOCAL}}
    if DB_efx_ultimo!=null then
        set i=DB_ef_slot_novo(GetHandleId(DB_efx_ultimo))
        call SaveStr(DB_ef_ht,GetHandleId(DB_efx_ultimo),1,modelo)
        //{{KK_SE:KK_FX_LOCAL}}
        call KK_fx_anota(i)
        //{{KK_FIMSE:KK_FX_LOCAL}}
        set DB_ef_x[i]=GetLocationX(onde)
        set DB_ef_y[i]=GetLocationY(onde)
        set DB_ef_z[i]=DB_z_efeito(DB_efx_ultimo,DB_ef_x[i],DB_ef_y[i])
        set DB_ef_sinc[i]=true
    endif
    return DB_efx_ultimo
endfunction

function DB_efx_cria_alvo takes string modelo,widget alvo,string anexo returns effect
    local integer i
    //{{KK_SE:KK_FX_LOCAL}}
    local string kk_fx_orig=modelo
    set modelo=KK_fx_m(modelo)
    //{{KK_FIMSE:KK_FX_LOCAL}}
    set DB_efx_ultimo=AddSpecialEffectTarget(modelo,alvo,anexo)
    //{{KK_SE:KK_FX_LOCAL}}
    set modelo=kk_fx_orig
    //{{KK_FIMSE:KK_FX_LOCAL}}
    if DB_efx_ultimo!=null then
        set i=DB_ef_slot_novo(GetHandleId(DB_efx_ultimo))
        call SaveStr(DB_ef_ht,GetHandleId(DB_efx_ultimo),1,modelo)
        //{{KK_SE:KK_FX_LOCAL}}
        call KK_fx_anota(i)
        //{{KK_FIMSE:KK_FX_LOCAL}}
        set DB_ef_x[i]=GetWidgetX(alvo)
        set DB_ef_y[i]=GetWidgetY(alvo)
        set DB_ef_z[i]=DB_z_efeito(DB_efx_ultimo,DB_ef_x[i],DB_ef_y[i])
        set DB_ef_segue[i]=alvo
    endif
    return DB_efx_ultimo
endfunction

function DB_efx_cria_loc_bj takes location where,string modelName returns effect
    set bj_lastCreatedEffect=DB_efx_cria_loc(modelName,where)
    return bj_lastCreatedEffect
endfunction

function DB_efx_cria_alvo_bj takes string attachPointName,widget targetWidget,string modelName returns effect
    set bj_lastCreatedEffect=DB_efx_cria_alvo(modelName,targetWidget,attachPointName)
    return bj_lastCreatedEffect
endfunction

function KK_leque_poe takes unit u,real x,real y returns nothing
    if x<GetRectMinX(bj_mapInitialPlayableArea) then
        set x=GetRectMinX(bj_mapInitialPlayableArea)
    elseif x>GetRectMaxX(bj_mapInitialPlayableArea) then
        set x=GetRectMaxX(bj_mapInitialPlayableArea)
    endif
    if y<GetRectMinY(bj_mapInitialPlayableArea) then
        set y=GetRectMinY(bj_mapInitialPlayableArea)
    elseif y>GetRectMaxY(bj_mapInitialPlayableArea) then
        set y=GetRectMaxY(bj_mapInitialPlayableArea)
    endif
    call SetUnitX(u,x)
    call SetUnitY(u,y)
endfunction

function KK_leque_cria takes string modelo,real x,real y returns effect
    local integer t=0
    local integer i
    if modelo=="Spell0465.mdl" then
        set t='eLqA'
    elseif modelo=="Spell0466.mdl" then
        set t='eLqB'
    elseif modelo=="KK_Leque80.mdl" then
        set t='eLqM'
    elseif modelo=="KK_Leque50.mdl" then
        set t='eLqN'
    endif
    if t==0 then
        return DB_efx_cria(modelo,x,y)
    endif
    call DB_efx_cria("",x,y)
    if DB_efx_ultimo!=null then
        set i=DB_ef_idx(DB_efx_ultimo)
        if i>=0 then
            call SaveStr(DB_ef_ht,GetHandleId(DB_efx_ultimo),1,modelo)
            set DB_ef_uni[i]=CreateUnit(Player(PLAYER_NEUTRAL_PASSIVE),t,x,y,0.0)
            call KK_leque_poe(DB_ef_uni[i],x,y)
        endif
    endif
    return DB_efx_ultimo
endfunction

function DB_car_varre takes nothing returns nothing
    local integer k=0
    local integer j=0
    set DB_car_tique=DB_car_tique+1
    loop
        exitwhen k>=DB_car_n
        if DB_car_prazo[k]<=DB_car_tique then
            call RemoveUnit(DB_car_fila[k])
        else
            set DB_car_fila[j]=DB_car_fila[k]
            set DB_car_prazo[j]=DB_car_prazo[k]
            set j=j+1
        endif
        set k=k+1
    endloop
    set k=j
    loop
        exitwhen k>=DB_car_n
        set DB_car_fila[k]=null
        set k=k+1
    endloop
    set DB_car_n=j
    if DB_car_n==0 then
        call PauseTimer(DB_car_tmr)
    endif
endfunction

function DB_car_agenda takes unit u returns nothing
    if u==null then
        return
    endif
    if DB_car_n>=DB_CAR_MAX then
        call RemoveUnit(u)
        return
    endif
    set DB_car_fila[DB_car_n]=u
    set DB_car_prazo[DB_car_n]=DB_car_tique+DB_CAR_ESPERA
    set DB_car_n=DB_car_n+1
    if DB_car_tmr==null then
        set DB_car_tmr=CreateTimer()
    endif
    if DB_car_n==1 then
        call TimerStart(DB_car_tmr,0.50,true,function DB_car_varre)
    endif
endfunction

function DB_car_altura takes integer i returns nothing
    local real h
    if DB_ef_car[i]==null then
        return
    endif
    set h=DB_ef_z[i]-KK_z(DB_ef_x[i],DB_ef_y[i])
    if h<0.0 then
        set h=0.0
    endif
    call SetUnitFlyHeight(DB_ef_car[i],h,0.0)
endfunction

function DB_ef_vis_estado takes integer i returns nothing
    local effect v=DB_ef_vis[i]
    if v==null then
        return
    endif
    call BlzSetSpecialEffectScale(v,DB_ef_size[i])
    if DB_ef_msc[i] and not DB_ef_assado[i] then
        call BlzSetSpecialEffectMatrixScale(v,DB_ef_mx[i],DB_ef_my[i],DB_ef_mz[i])
    endif
    if DB_ef_cor[i]>=0 then
        call BlzSetSpecialEffectColor(v,DB_ef_cor[i]/65536,ModuloInteger(DB_ef_cor[i]/256,256),ModuloInteger(DB_ef_cor[i],256))
    endif
    if DB_ef_alfa[i]!=255 then
        call BlzSetSpecialEffectAlpha(v,DB_ef_alfa[i])
    endif
    if DB_ef_vel[i]!=1.0 then
        call BlzSetSpecialEffectTimeScale(v,DB_ef_vel[i])
    endif
    if DB_ef_anim[i]>=0 then
        call BlzPlaySpecialEffect(v,ConvertAnimType(DB_seq_tipo(LoadStr(DB_ef_ht,DB_ef_id[i],1),DB_ef_anim[i])-1))
    endif
    if DB_ef_oculto[i] then
        call BlzSetSpecialEffectAlpha(v,0)
        call BlzSetSpecialEffectScale(v,0.0)
    endif
    set v=null
endfunction

function DB_ef_modelo_assado takes string m,integer i returns string
    local string s=StringCase(m,true)
    if s=="SPELL0409.MDL" or s=="SPELL0409.MDX" then
        if DB_ef_mx[i]==0.5 and DB_ef_my[i]==5.0 and DB_ef_mz[i]==1.0 then
            return "KK_Spell0409_x05y5.mdx"
        endif
    elseif s=="SPELL0410.MDL" or s=="SPELL0410.MDX" then
        if DB_ef_mx[i]==1.5 and DB_ef_my[i]==2.5 and DB_ef_mz[i]==1.0 then
            return "KK_Spell0410_x15y25.mdx"
        endif
    endif
    return ""
endfunction

function DB_ef_porta takes integer i,effect e returns nothing
    local unit u
    local string m=LoadStr(DB_ef_ht,GetHandleId(e),1)
    local string mb
    //{{KK_INCLUI:portadora_local}}
    if m==null then
        set m=""
    endif
    set DB_ef_assado[i]=false
    if DB_ef_msc[i] then
        set mb=DB_ef_modelo_assado(m,i)
        if mb!="" then
            set m=mb
            set DB_ef_assado[i]=true
        endif
    endif
    //{{KK_INCLUI:portadora_antes}}
    set u=CreateUnit(Player(PLAYER_NEUTRAL_PASSIVE),'eLqP',DB_ef_x[i],DB_ef_y[i],DB_ef_rz[i]*180.0/3.14159265358979)
    //{{KK_INCLUI:portadora_depois}}
    set DB_ef_car[i]=u
    call KK_leque_poe(u,DB_ef_x[i],DB_ef_y[i])
    call DB_car_altura(i)
    //{{KK_SE:KK_FX_LOCAL}}
    set m=KK_fx_m_vaga(m,i)
    //{{KK_FIMSE:KK_FX_LOCAL}}
    set DB_ef_vis[i]=AddSpecialEffectTarget(m,u,"origin")
    call DB_ef_vis_estado(i)
    call BlzSetSpecialEffectAlpha(e,0)
    call BlzSetSpecialEffectScale(e,0.0)
    call BlzSetSpecialEffectMatrixScale(e,0.0,0.0,0.0)
    if not DB_ef_vivo[i] then
        call DestroyEffect(DB_ef_vis[i])
        set DB_ef_vis[i]=null
        call DB_car_agenda(u)
    endif
    set u=null
endfunction

function DB_ef_solta takes integer i,effect e returns nothing
    if DB_ef_vis[i]!=null then
        call BlzSetSpecialEffectAlpha(DB_ef_vis[i],0)
        call BlzSetSpecialEffectScale(DB_ef_vis[i],0.0)
        call DestroyEffect(DB_ef_vis[i])
        set DB_ef_vis[i]=null
        call RemoveUnit(DB_ef_car[i])
    endif
    set DB_ef_car[i]=null
    set DB_ef_solto[i]=true
    if e==null then
        return
    endif
    call BlzSetSpecialEffectPosition(e,DB_ef_x[i],DB_ef_y[i],DB_ef_z[i])
    if DB_ef_msc[i] then
        call BlzSetSpecialEffectMatrixScale(e,DB_ef_mx[i],DB_ef_my[i],DB_ef_mz[i])
    else
        call BlzResetSpecialEffectMatrix(e)
    endif
    if DB_ef_oculto[i] then
        call BlzSetSpecialEffectAlpha(e,0)
        call BlzSetSpecialEffectScale(e,0.0)
    else
        call BlzSetSpecialEffectAlpha(e,DB_ef_alfa[i])
        call BlzSetSpecialEffectScale(e,DB_ef_size[i])
    endif
endfunction

function DB_efx_destroi takes effect e returns nothing
    local integer i
    if e!=null and DB_ef_ht!=null then
        set i=LoadInteger(DB_ef_ht,GetHandleId(e),0)-1
        if i>=0 and DB_ef_segue[i]!=null then
            set DB_ef_x[i]=GetWidgetX(DB_ef_segue[i])
            set DB_ef_y[i]=GetWidgetY(DB_ef_segue[i])
            set DB_ef_segue[i]=null
        endif
        if i>=0 then
            set DB_ef_vivo[i]=false
            if DB_ef_uni[i]!=null then
                call RemoveUnit(DB_ef_uni[i])
                set DB_ef_uni[i]=null
            endif
            if DB_ef_vis[i]!=null then
                call DestroyEffect(DB_ef_vis[i])
                set DB_ef_vis[i]=null
                call DB_car_agenda(DB_ef_car[i])
            endif
        endif
    endif
    call DestroyEffect(e)
endfunction

function DB_efeito_vivo takes effect e returns boolean
    local integer i
    if e==null then
        return false
    endif
    set i=DB_ef_idx(e)
    if i<0 then
        return true
    endif
    return true
endfunction

function DB_cond_local takes nothing returns boolean
    return GetLocalPlayer()==GetTriggerPlayer()
endfunction

function DB_init_eventos takes nothing returns nothing
    set DB_evt[1]=FRAMEEVENT_CONTROL_CLICK
    set DB_evt[2]=FRAMEEVENT_MOUSE_ENTER
    set DB_evt[3]=FRAMEEVENT_MOUSE_LEAVE
    set DB_evt[4]=FRAMEEVENT_MOUSE_UP
    set DB_evt[5]=FRAMEEVENT_MOUSE_DOWN
    set DB_evt[6]=FRAMEEVENT_MOUSE_WHEEL
    set DB_evt[7]=FRAMEEVENT_CHECKBOX_CHECKED
    set DB_evt[8]=FRAMEEVENT_CHECKBOX_UNCHECKED
    set DB_evt[9]=FRAMEEVENT_EDITBOX_TEXT_CHANGED
    set DB_evt[10]=FRAMEEVENT_POPUPMENU_ITEM_CHANGED
    set DB_evt[11]=FRAMEEVENT_POPUPMENU_ITEM_CHANGED
    set DB_evt[12]=FRAMEEVENT_MOUSE_DOUBLECLICK
    set DB_evt[13]=FRAMEEVENT_SPRITE_ANIM_UPDATE
    set DB_evt[14]=FRAMEEVENT_SLIDER_VALUE_CHANGED
    set DB_evt[15]=FRAMEEVENT_DIALOG_CANCEL
    set DB_evt[16]=FRAMEEVENT_DIALOG_ACCEPT
    set DB_evt[17]=FRAMEEVENT_EDITBOX_ENTER
endfunction

function DB_ev takes integer i returns frameeventtype
    if i<1 or i>17 then
        return null
    endif
    if DB_evt[1]==null then
        call DB_init_eventos()
    endif
    return DB_evt[i]
endfunction

function DB_efeito_anota takes effect e,real x,real y,real z returns nothing
    local integer i=DB_ef(e)
    if i<0 then
        return
    endif
    set DB_ef_x[i]=x
    set DB_ef_y[i]=y
    set DB_ef_z[i]=z
    set DB_ef_segue[i]=null
endfunction

function DB_efeito_anota_x takes effect e,real x returns nothing
    local integer i=DB_ef(e)
    if i<0 then
        return
    endif
    set DB_ef_x[i]=x
endfunction

function DB_efeito_anota_y takes effect e,real y returns nothing
    local integer i=DB_ef(e)
    if i<0 then
        return
    endif
    set DB_ef_y[i]=y
endfunction

function DB_efeito_anota_z takes effect e,real z returns nothing
    local integer i=DB_ef(e)
    if i<0 then
        return
    endif
    set DB_ef_z[i]=z
endfunction

boolean DB_perfil_carregou=false

function DB_perfil_garante takes nothing returns nothing
    local string pasta
    local integer r
    if DB_perfil_carregou then
        return
    endif
    set DB_perfil_carregou=true
    call DB_sv_prepara()
    set pasta=DB_conta()
    set r=DB_sv_le("", pasta)
    if r==2 then
        call DB_sv_aplica()
        set DB_s2_n_principal=DB_s2_n_lida
        set DB_s2_gen_principal=DB_s2_gen_lida
        if DB_s2_n_lida>DB_s2_cont then
            set DB_s2_cont=DB_s2_n_lida
        endif
    elseif r==1 then
        call DB_decode(GetLocalPlayer(), DB_sv_env)
    endif
    call DB_perfil_resgate(pasta)
    //{{KK_INCLUI:perfil_depois}}
endfunction

function DB_perfil_aplica takes string blob,string pasta,boolean principal returns nothing
    local string claro
    if blob==null or blob=="" then
        return
    endif
    if SubString(blob, 0, 11)==DB_C2_CH_BLOB+"=" then
        set claro=DB_save2_abre(blob, pasta)
        if claro!=null then
            if principal then
                set DB_s2_n_principal=DB_s2_n_lida
                set DB_s2_gen_principal=DB_s2_gen_lida
            endif
            call DB_decode(GetLocalPlayer(), claro)
            return
        endif
        return
    endif
    call DB_decode(GetLocalPlayer(), blob)
endfunction

integer DB_s2_n_principal=0
integer DB_s2_gen_principal=-1
string DB_s2_resgate="nao tentado"

function DB_perfil_resgate takes string pasta returns nothing
    local boolean tenta=DB_resgate_tenta()
    local integer r=DB_sv_le("wipe_", pasta)
    set DB_s2_resgate="backup nao abre"
    if not tenta or r!=2 then
        set DB_s2_n_lida=DB_s2_n_principal
        set DB_s2_gen_lida=DB_s2_gen_principal
        if not tenta then
            set DB_s2_resgate="principal valido"
        else
            set DB_s2_resgate="backup sem contador"
        endif
        return
    endif
    if DB_resgate_aplica(DB_s2_n_lida) then
        call DB_sv_aplica()
        call DB_perfil_marca_resgate(DB_s2_resgate)
    endif
endfunction

function DB_resgate_tenta takes nothing returns boolean
    if DB_s2_gen_principal==DB_C2_GEN and DB_s2_n_principal>0 then
        set DB_s2_resgate="principal valido"
        return false
    endif
    return true
endfunction

function DB_resgate_aplica takes integer n_backup returns boolean
    if n_backup<=0 then
        set DB_s2_resgate="backup sem contador"
        set DB_s2_n_lida=DB_s2_n_principal
        set DB_s2_gen_lida=DB_s2_gen_principal
        return false
    endif
    if n_backup<=DB_s2_n_principal then
        set DB_s2_resgate="backup mais velho ("+I2S(n_backup)+" <= "+I2S(DB_s2_n_principal)+")"
        set DB_s2_n_lida=DB_s2_n_principal
        set DB_s2_gen_lida=DB_s2_gen_principal
        return false
    endif
    set DB_s2_resgate="wipe_ n="+I2S(n_backup)+" (principal n="+I2S(DB_s2_n_principal)+        " gen="+I2S(DB_s2_gen_principal)+")"
    set DB_s2_cont=n_backup
    set DB_s2_gen_lida=DB_C2_GEN
    return true
endfunction

function DB_perfil_marca_resgate takes string detalhe returns nothing
    call DB_perfil_diag("RESCUE "+I2S(GetPlayerId(GetLocalPlayer()))+" "+detalhe)
endfunction

function DB_perfil_diag takes string linha returns nothing
    call PreloadGenClear()
    call PreloadGenStart()
    call Preload("\")\n// "+DB_esc_jass(linha)+"\n//")
    call PreloadGenEnd("DreamS5\\perfil_diag.pld")
endfunction

function DB_le_blob takes string prefixo returns string
    local string meta
    local integer nfiles
    local integer f
    local integer i
    local integer base
    local string v
    local string blob=""
    local integer nslots
    local string antes
    local string mudou
    call DB_tabelas_init()
    set nslots=DB_SLOT_N
    if nslots<1 then
        return null
    endif
    set antes=DB_foto_antes()
    call DB_sv_captura()
    call Preloader(DB_caminho_meta(prefixo))
    set mudou=DB_foto_confere(antes)
    if mudou!="" then
        call DB_save2_cheatpld(prefixo+"meta.pld", mudou)
    endif
    set meta=DB_le_meta()
    if SubString(meta, 0, 6)!="@META " then
        return null
    endif
    set nfiles=S2I(DB_campo(meta, 0))
    if nfiles<1 or nfiles>64 then
        return null
    endif
    set f=1
    loop
        exitwhen f>nfiles
        set antes=DB_foto_antes()
        call Preloader(DB_caminho(prefixo+"profile_", f))
        set mudou=DB_foto_confere(antes)
        if mudou!="" then
            call DB_save2_cheatpld(prefixo+"profile_"+I2S(f)+".pld", mudou)
        endif
        set base=(f-1)*nslots
        set i=0
        loop
            exitwhen i>=nslots
            set blob=blob+DB_le_pedaco(i)
            set i=i+1
        endloop
        set f=f+1
    endloop
    call DB_restaura()
    return blob
endfunction

function DB_grava_blob takes string blob returns boolean
    local integer total
    local integer nslots
    local integer f
    local integer idx
    local integer base
    local string pedaco
    local string linha
    local integer nfiles
    call DB_tabelas_init()
    set nslots=DB_SLOT_N
    if nslots<1 then
        return false
    endif
    set total=StringLength(blob)
    set nfiles=(total/(DB_PEDACO*nslots))+1
    if nfiles<1 then
        set nfiles=1
    endif
    set f=1
    loop
        exitwhen f>nfiles
        call PreloadGenClear()
        call PreloadGenStart()
        set base=(f-1)*nslots
        set idx=0
        loop
            exitwhen idx>=nslots
            if (base+idx)*DB_PEDACO>=total then
                exitwhen true
            endif
            set pedaco=SubString(blob, (base+idx)*DB_PEDACO, (base+idx)*DB_PEDACO+DB_PEDACO)
            if DB_slot_kind[idx]==0 then
                set linha="call BlzSetAbilityTooltip("+DB_slot_txt[idx]+",\"@"+DB_pad5(base+idx)+DB_troca(pedaco, "\\", "\\\\")+"\",0)"
            else
                set linha="call BlzSetAbilityExtendedTooltip("+DB_slot_txt[idx]+",\"@"+DB_pad5(base+idx)+DB_troca(pedaco, "\\", "\\\\")+"\",0)"
            endif
            call Preload("\")\n"+linha+"\n//")
            set idx=idx+1
        endloop
        call PreloadGenEnd(DB_caminho("profile_", f))
        set f=f+1
    endloop
    call PreloadGenClear()
    call PreloadGenStart()
    call Preload("\")\ncall BlzSetAbilityTooltip("+DB_slot_txt[0]+",\"@META "+I2S(nfiles)+" "+I2S(nslots)+" "+I2S(total)+"\",0)\n//")
    call PreloadGenEnd(DB_caminho_meta(""))
    return true
endfunction
