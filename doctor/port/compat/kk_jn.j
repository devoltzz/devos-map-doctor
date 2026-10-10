//@GLOBALS
hashtable KKJN_db=null
hashtable KKJN_dbt=null
hashtable KKJN_dbf=null
hashtable KKJN_cont=null
string KKJN_blob=""
boolean KKJN_blob_lit=false
integer KKJN_nslots=0
integer array KKJN_slot
string array KKJN_slotOrig
boolean KKJN_slotSaved=false
boolean KKJN_pronto=false
constant string KKJN_PASTA="{{KK_JN_PASTA}}"
constant integer KKJN_ABIL={{KK_JN_HABILIDADE}}
constant string KKJN_ABIL_TXT="{{KK_JN_HABILIDADE}}"
constant string KKJN_SALVO="{{KK_JN_SALVO}}"
constant string KKJN_DIARIO="{{KK_JN_DIARIO}}"
constant string KKJN_MARCA="@"
constant integer KKJN_TRECHO=170
string KKJN_C2=""
constant string KKJN_GRAU="°"
constant string KKJN_HANGUL="가각갂갃간갅갆갇갈갉갊갋갌갍갎갏감갑값갓갔강갖갗갘같갚갛개객갞갟갠갡갢갣갤갥갦갧갨갩갪갫갬갭갮갯갰갱갲갳갴갵갶갷갸갹갺갻갼갽갾갿"
constant string KKJN_B64="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
integer array KKJN_b64i
constant string KKJN_LATIN1=" ¡¢£¤¥¦§¨©ª«¬­®¯°±²³´µ¶·¸¹º»¼½¾¿ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿ"
constant string KKJN_NBSP=" "
real KKJN_vel_ataque=5.0
integer KKJN_atraso=100
constant string KKJN_ESP_CJK="　"
//{{KK_SE:KK_JN_BASE}}
constant string KKJN_BASE="{{KK_JN_BASE_CAMPOS}}"
integer KKJN_nbase=0
//{{KK_FIMSE:KK_JN_BASE}}
//{{KK_SE:KK_JN_REGEX}}
integer array KKRX_op
integer array KKRX_a
integer array KKRX_b
integer array KKRX_d
string array KKRX_s
integer array KKRX_lo
integer array KKRX_hi
string array KKRX_ls
integer array KKRX_pend
integer array KKRX_spc
integer array KKRX_ssp
string array KKRX_mt
string array KKRX_mp
integer array KKRX_mi
string array KKRX_mr
integer array KKRX_me
boolean array KKRX_mv
string array KKRX_dt
boolean array KKRX_dv
hashtable KKRX_dic=null
integer KKRX_top=0
integer KKRX_nr=0
integer KKRX_np=0
integer KKRX_sp=0
string KKRX_pat=""
integer KKRX_pn=0
integer KKRX_pp=0
boolean KKRX_erro=false
string KKRX_str=""
integer KKRX_n=0
integer KKRX_passos=0
boolean KKRX_estouro=false
integer KKRX_fim=0
integer KKRX_prox=0
integer KKRX_pmodo=0
string KKRX_plit=""
integer KKRX_rv=0
integer KKRX_qm=0
integer KKRX_qn=0
string KKRX_et=""
boolean KKRX_en=false
integer KKRX_rc=0
integer KKRX_nl=0
integer KKRX_carimbo=0
integer array KKRX_reg
integer array KKRX_vis
integer array KKRX_wl
constant integer KKRX_TETO=6000
constant integer KKRX_CODIGO=6000
constant integer KKRX_GUARDA=12000
constant integer KKRX_PILHA=4000
//{{KK_FIMSE:KK_JN_REGEX}}
//@ENDGLOBALS

function KKJN_Esc takes string s returns string
    local integer n
    local integer i=0
    local string r=""
    local string b
    if s==null then
        return ""
    endif
    set n=StringLength(s)
    loop
        exitwhen i>=n
        set b=SubString(s, i, i+1)
        exitwhen b=="\\" or b==";" or b=="\n" or b=="\r"
        set i=i+1
    endloop
    if i>=n then
        return s
    endif
    set r=SubString(s, 0, i)
    loop
        exitwhen i>=n
        set b=SubString(s, i, i+1)
        if b=="\\" then
            set r=r+"\\\\"
        elseif b==";" then
            set r=r+"\\;"
        elseif b=="\n" then
            set r=r+"\\n"
        elseif b=="\r" then
            set r=r+"\\r"
        else
            set r=r+b
        endif
        set i=i+1
    endloop
    return r
endfunction

function KKJN_Unesc takes string s returns string
    local integer n
    local integer i=0
    local string r=""
    local string b
    if s==null then
        return ""
    endif
    set n=StringLength(s)
    loop
        exitwhen i>=n
        exitwhen SubString(s, i, i+1)=="\\"
        set i=i+1
    endloop
    if i>=n then
        return s
    endif
    set r=SubString(s, 0, i)
    loop
        exitwhen i>=n
        set b=SubString(s, i, i+1)
        if b=="\\" and i+1<n then
            set b=SubString(s, i+1, i+2)
            if b=="n" then
                set r=r+"\n"
            elseif b=="r" then
                set r=r+"\r"
            else
                set r=r+b
            endif
            set i=i+2
        else
            set r=r+b
            set i=i+1
        endif
    endloop
    return r
endfunction

function KKJN_EscLit takes string s returns string
    local integer n
    local integer i=0
    local string r=""
    local string b
    if s==null then
        return ""
    endif
    set n=StringLength(s)
    loop
        exitwhen i>=n
        set b=SubString(s, i, i+1)
        exitwhen b=="\\" or b=="\"" or b=="\n" or b=="\r"
        set i=i+1
    endloop
    if i>=n then
        return s
    endif
    set r=SubString(s, 0, i)
    loop
        exitwhen i>=n
        set b=SubString(s, i, i+1)
        if b=="\\" then
            set r=r+"\\\\"
        elseif b=="\"" then
            set r=r+"\\\""
        elseif b=="\n" or b=="\r" then
            set r=r+" "
        else
            set r=r+b
        endif
        set i=i+1
    endloop
    return r
endfunction

function KKJN_PosB takes string s,string sub,integer start returns integer
    local integer n=StringLength(s)
    local integer m=StringLength(sub)
    local integer i=start
    if m<=0 then
        return -1
    endif
    if i<0 then
        set i=0
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

function KKJN_UKey takes string user returns string
    if user==null then
        return ""
    endif
    return StringCase(user, false)
endfunction

function KKJN_ObjChar takes string user,string ch returns string
    if ch==null then
        set ch=""
    endif
    return "c|"+user+"|"+ch
endfunction

function KKJN_ObjUser takes string user,string ns returns string
    if ns==null then
        set ns=""
    endif
    return "u|"+user+"|"+ns
endfunction

function KKJN_Dir takes string user returns string
    return KKJN_PASTA+"u"+I2S(StringHash(user))+"\\"
endfunction

function KKJN_BaseChar takes string user,string ch returns string
    if ch==null then
        set ch=""
    endif
    return KKJN_Dir(user)+"chr_"+I2S(StringHash(ch))+"_"
endfunction

function KKJN_BaseUser takes string user,string ns returns string
    if ns==null then
        set ns=""
    endif
    return KKJN_Dir(user)+"usr_"+I2S(StringHash(ns))+"_"
endfunction

function KKJN_BaseIndex takes string user returns string
    return KKJN_Dir(user)+"index_"
endfunction

function KKJN_AKey takes string user returns integer
    return StringHash("A"+user)
endfunction

function KKJN_IKey takes string user returns integer
    return StringHash("I"+user)
endfunction

function KKJN_TipoFunc takes integer tipo returns string
    if tipo==0 then
        return "BlzSetAbilityTooltip"
    elseif tipo==1 then
        return "BlzSetAbilityExtendedTooltip"
    elseif tipo==2 then
        return "BlzSetAbilityActivatedTooltip"
    elseif tipo==3 then
        return "BlzSetAbilityActivatedExtendedTooltip"
    elseif tipo==4 then
        return "BlzSetAbilityResearchTooltip"
    endif
    return "BlzSetAbilityResearchExtendedTooltip"
endfunction

function KKJN_TipoGet takes integer tipo returns string
    if tipo==0 then
        return BlzGetAbilityTooltip(KKJN_ABIL, 0)
    elseif tipo==1 then
        return BlzGetAbilityExtendedTooltip(KKJN_ABIL, 0)
    elseif tipo==2 then
        return BlzGetAbilityActivatedTooltip(KKJN_ABIL, 0)
    elseif tipo==3 then
        return BlzGetAbilityActivatedExtendedTooltip(KKJN_ABIL, 0)
    elseif tipo==4 then
        return BlzGetAbilityResearchTooltip(KKJN_ABIL, 0)
    endif
    return BlzGetAbilityResearchExtendedTooltip(KKJN_ABIL, 0)
endfunction

function KKJN_TipoSet takes integer tipo,string s returns nothing
    if s==null then
        set s=""
    endif
    if tipo==0 then
        call BlzSetAbilityTooltip(KKJN_ABIL, s, 0)
    elseif tipo==1 then
        call BlzSetAbilityExtendedTooltip(KKJN_ABIL, s, 0)
    elseif tipo==2 then
        call BlzSetAbilityActivatedTooltip(KKJN_ABIL, s, 0)
    elseif tipo==3 then
        call BlzSetAbilityActivatedExtendedTooltip(KKJN_ABIL, s, 0)
    elseif tipo==4 then
        call BlzSetAbilityResearchTooltip(KKJN_ABIL, s, 0)
    else
        call BlzSetAbilityResearchExtendedTooltip(KKJN_ABIL, s, 0)
    endif
endfunction

function KKJN_Sonda takes nothing returns nothing
    local integer tipo=0
    local string orig
    local string teste
    set KKJN_nslots=0
    loop
        exitwhen tipo>5
        set orig=KKJN_TipoGet(tipo)
        set teste=KKJN_MARCA+"KKJN"+I2S(tipo)
        call KKJN_TipoSet(tipo, teste)
        if KKJN_TipoGet(tipo)==teste then
            set KKJN_slot[KKJN_nslots]=tipo
            set KKJN_nslots=KKJN_nslots+1
        endif
        call KKJN_TipoSet(tipo, orig)
        set tipo=tipo+1
    endloop
endfunction

function KKJN_SlotRaw takes integer slot returns string
    return KKJN_TipoGet(KKJN_slot[slot])
endfunction

function KKJN_SlotGet takes integer slot returns string
    local string s=KKJN_SlotRaw(slot)
    if s==null or SubString(s, 0, 1)!=KKJN_MARCA then
        return ""
    endif
    return SubString(s, 1, StringLength(s))
endfunction

function KKJN_SlotSave takes nothing returns nothing
    local integer i=0
    if KKJN_slotSaved then
        return
    endif
    loop
        exitwhen i>=KKJN_nslots
        set KKJN_slotOrig[i]=KKJN_SlotRaw(i)
        if KKJN_slotOrig[i]==null then
            set KKJN_slotOrig[i]=""
        endif
        set i=i+1
    endloop
    set KKJN_slotSaved=true
endfunction

function KKJN_SlotRestore takes nothing returns nothing
    local integer i=0
    if not KKJN_slotSaved then
        return
    endif
    loop
        exitwhen i>=KKJN_nslots
        call KKJN_TipoSet(KKJN_slot[i], KKJN_slotOrig[i])
        set i=i+1
    endloop
endfunction

function KKJN_SlotClear takes nothing returns nothing
    local integer i=0
    call KKJN_SlotSave()
    loop
        exitwhen i>=KKJN_nslots
        call KKJN_TipoSet(KKJN_slot[i], KKJN_MARCA)
        set i=i+1
    endloop
endfunction

function KKJN_WriteSlot takes integer slot,string s returns nothing
    call Preload("\")\ncall "+KKJN_TipoFunc(KKJN_slot[slot])+"("+KKJN_ABIL_TXT+",\""+KKJN_MARCA+KKJN_EscLit(s)+"\",0)\n//")
endfunction

function KKJN_WriteSlotCru takes integer slot,string s returns nothing
    call Preload("\")\ncall "+KKJN_TipoFunc(KKJN_slot[slot])+"("+KKJN_ABIL_TXT+",\""+KKJN_MARCA+s+"\",0)\n//")
endfunction

function KKJN_SlotHead takes string s returns string
    local integer p
    if s==null or SubString(s, 0, 1)!="#" then
        return "0"
    endif
    set p=KKJN_PosB(s, ";", 0)
    if p<0 then
        return "0"
    endif
    return SubString(s, 1, p)
endfunction

//{{KK_SE:KK_JN_BASE}}
function KKJN_BaseDigito takes string c returns boolean
    return c!="" and KKJN_PosB("0123456789", c, 0)>=0
endfunction

function KKJN_BaseGuarda takes string nome,integer v returns nothing
    call SaveInteger(KKJN_cont, 1, StringHash(nome), v)
    set KKJN_nbase=KKJN_nbase+1
endfunction

function KKJN_BaseRegistro takes string rec returns nothing
    local integer e=KKJN_PosB(rec, "=", 0)
    local integer d
    local integer k
    local integer a
    local integer b
    local integer v
    local string nome
    local string pre
    if e<1 then
        return
    endif
    set nome=SubString(rec, 0, e)
    set v=S2I(SubString(rec, e+1, StringLength(rec)))
    set d=KKJN_PosB(nome, "..", 0)
    if d<1 then
        call KKJN_BaseGuarda(nome, v)
        return
    endif
    set k=d
    loop
        exitwhen k<=0
        exitwhen not KKJN_BaseDigito(SubString(nome, k-1, k))
        set k=k-1
    endloop
    if k==d then
        call KKJN_BaseGuarda(nome, v)
        return
    endif
    set pre=SubString(nome, 0, k)
    set a=S2I(SubString(nome, k, d))
    set b=S2I(SubString(nome, d+2, StringLength(nome)))
    loop
        exitwhen a>b
        call KKJN_BaseGuarda(pre+I2S(a), v)
        set a=a+1
    endloop
endfunction

function KKJN_BaseLe takes nothing returns nothing
    local integer n=StringLength(KKJN_BASE)
    local integer i=0
    local integer j
    loop
        exitwhen i>=n
        set j=KKJN_PosB(KKJN_BASE, ";", i)
        if j<0 then
            set j=n
        endif
        if j>i then
            call KKJN_BaseRegistro(SubString(KKJN_BASE, i, j))
        endif
        set i=j+1
    endloop
endfunction

function KKJN_Base takes string fld,integer v returns integer
    local integer h=StringHash(fld)
    local integer b
    if not HaveSavedInteger(KKJN_cont, 1, h) then
        return v
    endif
    set b=LoadInteger(KKJN_cont, 1, h)
    if b>v then
        return b
    endif
    return v
endfunction
//{{KK_FIMSE:KK_JN_BASE}}

function KKJN_init takes nothing returns nothing
    local integer i=0
    if KKJN_pronto then
        return
    endif
    set KKJN_db=InitHashtable()
    set KKJN_dbt=InitHashtable()
    set KKJN_dbf=InitHashtable()
    set KKJN_cont=InitHashtable()
    loop
        exitwhen i>=64
        call SaveBoolean(KKJN_cont, 0, StringHash(SubString(KKJN_GRAU, 0, 1)+SubString(KKJN_HANGUL, i*3+2, i*3+3)), true)
        set i=i+1
    endloop
    set KKJN_C2=SubString(KKJN_GRAU, 0, 1)
    set i=0
    loop
        exitwhen i>=96
        call SaveBoolean(KKJN_cont, 2, StringHash(SubString(KKJN_LATIN1, i*2, i*2+2)), true)
        set i=i+1
    endloop
    set i=0
    loop
        exitwhen i>=64
        set KKJN_b64i[DB_ord(SubString(KKJN_B64, i, i+1))]=i+1
        set i=i+1
    endloop
    call KKJN_Sonda()
    //{{KK_SE:KK_JN_BASE}}
    call KKJN_BaseLe()
    //{{KK_FIMSE:KK_JN_BASE}}
    //{{KK_SE:KK_JN_REGEX}}
    set KKRX_dic=InitHashtable()
    //{{KK_FIMSE:KK_JN_REGEX}}
    set KKJN_pronto=true
endfunction

function KKJN_TemLit takes string s returns boolean
    local integer n=StringLength(s)
    local integer i=0
    local string b
    loop
        exitwhen i>=n
        set b=SubString(s, i, i+1)
        if b=="\\" or b=="\"" or b=="\n" or b=="\r" then
            return true
        endif
        set i=i+1
    endloop
    return false
endfunction

function KKJN_PoeCampo takes string obj,string fld,integer tipo,string sval,integer ival,string rec,boolean lit returns nothing
    local integer vk=StringHash(obj)
    local integer fk=StringHash("F"+obj)
    local integer rk=StringHash("R"+obj)
    local integer h=StringHash(fld)
    local integer n
    local string nome=fld
    if not HaveSavedInteger(KKJN_dbf, fk, h) then
        set n=LoadInteger(KKJN_dbf, fk, -1)
        call SaveStr(KKJN_dbf, fk, n, fld)
        call SaveInteger(KKJN_dbf, fk, h, n)
        call SaveInteger(KKJN_dbf, fk, -1, n+1)
    else
        set nome=LoadStr(KKJN_dbf, fk, LoadInteger(KKJN_dbf, fk, h))
    endif
    call SaveInteger(KKJN_dbt, vk, h, tipo)
    if tipo==1 then
        call SaveStr(KKJN_db, vk, h, sval)
    else
        call SaveInteger(KKJN_db, vk, h, ival)
    endif
    if rec==null or rec=="" or nome!=fld then
        if tipo==1 then
            set rec="s|"+KKJN_Esc(nome)+"="+KKJN_Esc(sval)+";"
        else
            set rec="i|"+KKJN_Esc(nome)+"="+I2S(ival)+";"
        endif
        set lit=KKJN_TemLit(rec)
    endif
    call SaveStr(KKJN_dbf, rk, h, rec)
    call SaveBoolean(KKJN_dbf, rk, h, lit)
endfunction

function KKJN_SetFieldS takes string obj,string fld,string value returns nothing
    call KKJN_PoeCampo(obj, fld, 1, value, 0, "", false)
endfunction

function KKJN_SetFieldI takes string obj,string fld,integer value returns nothing
    call KKJN_PoeCampo(obj, fld, 0, "", value, "", false)
endfunction

function KKJN_RemoveField takes string obj,string fld returns nothing
    local integer vk=StringHash(obj)
    local integer fk=StringHash("F"+obj)
    local integer h=StringHash(fld)
    if not HaveSavedInteger(KKJN_dbf, fk, h) then
        return
    endif
    call SaveStr(KKJN_dbf, fk, LoadInteger(KKJN_dbf, fk, h), "")
    call RemoveSavedInteger(KKJN_dbf, fk, h)
    call RemoveSavedInteger(KKJN_dbt, vk, h)
    call RemoveSavedString(KKJN_db, vk, h)
    call RemoveSavedInteger(KKJN_db, vk, h)
    call RemoveSavedString(KKJN_dbf, StringHash("R"+obj), h)
    call RemoveSavedBoolean(KKJN_dbf, StringHash("R"+obj), h)
endfunction

function KKJN_ClearObj takes string obj returns nothing
    call FlushChildHashtable(KKJN_db, StringHash(obj))
    call FlushChildHashtable(KKJN_dbt, StringHash(obj))
    call FlushChildHashtable(KKJN_dbf, StringHash("F"+obj))
    call FlushChildHashtable(KKJN_dbf, StringHash("R"+obj))
endfunction

function KKJN_GetI takes string obj,string fld returns integer
    local integer vk=StringHash(obj)
    local integer h=StringHash(fld)
    if not HaveSavedInteger(KKJN_dbt, vk, h) then
        return 0
    endif
    if LoadInteger(KKJN_dbt, vk, h)==1 then
        return S2I(LoadStr(KKJN_db, vk, h))
    endif
    return LoadInteger(KKJN_db, vk, h)
endfunction

function KKJN_GetS takes string obj,string fld returns string
    local integer vk=StringHash(obj)
    local integer h=StringHash(fld)
    if not HaveSavedInteger(KKJN_dbt, vk, h) then
        return ""
    endif
    if LoadInteger(KKJN_dbt, vk, h)==1 then
        return LoadStr(KKJN_db, vk, h)
    endif
    return I2S(LoadInteger(KKJN_db, vk, h))
endfunction

function KKJN_ParseRecs takes string obj,string s returns nothing
    local integer i=0
    local integer n
    local integer start=0
    local string c
    local string rec
    local integer e
    local boolean esc=false
    local boolean aspas=false
    local string vtxt
    if s==null then
        return
    endif
    set n=StringLength(s)
    loop
        exitwhen i>=n
        set c=SubString(s, i, i+1)
        if c=="\\" then
            set esc=true
            set i=i+2
        elseif c==";" then
            set rec=SubString(s, start, i)
            if StringLength(rec)>=3 and SubString(rec, 0, 1)!="#" then
                set e=KKJN_PosB(rec, "=", 0)
                if e>1 then
                    set vtxt=SubString(rec, e+1, StringLength(rec))
                    if SubString(rec, 0, 1)=="s" then
                        if esc then
                            call KKJN_SetFieldS(obj, KKJN_Unesc(SubString(rec, 2, e)), KKJN_Unesc(vtxt))
                        elseif SubString(rec, 1, 2)=="|" then
                            call KKJN_PoeCampo(obj, SubString(rec, 2, e), 1, vtxt, 0, rec+";", aspas)
                        else
                            call KKJN_SetFieldS(obj, SubString(rec, 2, e), vtxt)
                        endif
                    elseif esc then
                        call KKJN_SetFieldI(obj, KKJN_Unesc(SubString(rec, 2, e)), S2I(vtxt))
                    elseif SubString(rec, 0, 2)=="i|" and I2S(S2I(vtxt))==vtxt then
                        call KKJN_PoeCampo(obj, SubString(rec, 2, e), 0, "", S2I(vtxt), rec+";", aspas)
                    else
                        call KKJN_SetFieldI(obj, SubString(rec, 2, e), S2I(vtxt))
                    endif
                endif
            endif
            set start=i+1
            set esc=false
            set aspas=false
            set i=i+1
        else
            if c=="\"" then
                set aspas=true
            endif
            set i=i+1
        endif
    endloop
endfunction

function KKJN_BuildBlob takes string obj returns nothing
    local integer fk=StringHash("F"+obj)
    local integer vk=StringHash(obj)
    local integer rk=StringHash("R"+obj)
    local integer n=LoadInteger(KKJN_dbf, fk, -1)
    local integer i=0
    local integer h
    local string fld
    set KKJN_blob=""
    set KKJN_blob_lit=false
    loop
        exitwhen i>=n
        set fld=LoadStr(KKJN_dbf, fk, i)
        if fld!=null and fld!="" then
            set h=StringHash(fld)
            if HaveSavedString(KKJN_dbf, rk, h) then
                set KKJN_blob=KKJN_blob+LoadStr(KKJN_dbf, rk, h)
                if LoadBoolean(KKJN_dbf, rk, h) then
                    set KKJN_blob_lit=true
                endif
            elseif LoadInteger(KKJN_dbt, vk, h)==1 then
                set KKJN_blob=KKJN_blob+"s|"+KKJN_Esc(fld)+"="+KKJN_Esc(LoadStr(KKJN_db, vk, h))+";"
                set KKJN_blob_lit=true
            else
                set KKJN_blob=KKJN_blob+"i|"+KKJN_Esc(fld)+"="+I2S(LoadInteger(KKJN_db, vk, h))+";"
                set KKJN_blob_lit=true
            endif
        endif
        set i=i+1
    endloop
endfunction

function KKJN_WriteParts takes string base returns nothing
    local integer por_parte=KKJN_nslots*KKJN_TRECHO
    local integer parts=1
    local integer q
    local integer p=0
    local integer s
    local integer idx
    local integer len
    local string text
    if KKJN_nslots<1 then
        return
    endif
    if KKJN_blob==null then
        set KKJN_blob=""
    endif
    loop
        set len=StringLength(KKJN_blob)+StringLength("#"+I2S(parts)+";")
        set q=(len+por_parte-1)/por_parte
        if q<1 then
            set q=1
        endif
        exitwhen q==parts
        set parts=q
    endloop
    set text="#"+I2S(parts)+";"+KKJN_blob
    set len=StringLength(text)
    loop
        exitwhen p>=parts
        call PreloadGenClear()
        call PreloadGenStart()
        set s=0
        loop
            exitwhen s>=KKJN_nslots
            set idx=(p*KKJN_nslots+s)*KKJN_TRECHO
            if idx<len then
                if KKJN_blob_lit then
                    call KKJN_WriteSlot(s, SubString(text, idx, idx+KKJN_TRECHO))
                else
                    call KKJN_WriteSlotCru(s, SubString(text, idx, idx+KKJN_TRECHO))
                endif
            endif
            set s=s+1
        endloop
        call PreloadGenEnd(base+I2S(p)+".pld")
        set p=p+1
    endloop
endfunction

function KKJN_LoadObjRaw takes string obj,string base returns boolean
    local integer parts
    local integer p=0
    local integer s
    local string blob=""
    call KKJN_ClearObj(obj)
    if KKJN_nslots<1 then
        return false
    endif
    call KKJN_SlotClear()
    call Preloader(base+"0.pld")
    if KKJN_SlotGet(0)=="" then
        return false
    endif
    set parts=S2I(KKJN_SlotHead(KKJN_SlotGet(0)))
    if parts<1 then
        set parts=1
    endif
    loop
        exitwhen p>=parts
        if p>0 then
            call KKJN_SlotClear()
            call Preloader(base+I2S(p)+".pld")
        endif
        set s=0
        loop
            exitwhen s>=KKJN_nslots
            set blob=blob+KKJN_SlotGet(s)
            set s=s+1
        endloop
        set p=p+1
    endloop
    call KKJN_ParseRecs(obj, blob)
    return true
endfunction

function KKJN_LoadOnce takes string obj,string base returns boolean
    local integer k=StringHash(obj)
    local boolean ok
    if not HaveSavedBoolean(KKJN_dbf, k, -3) then
        call SaveBoolean(KKJN_dbf, k, -3, true)
        set ok=KKJN_LoadObjRaw(obj, base)
        call KKJN_SlotRestore()
        if ok then
            call SaveBoolean(KKJN_dbf, k, -2, true)
        endif
    endif
    return HaveSavedBoolean(KKJN_dbf, k, -2)
endfunction

function KKJN_SaveObj takes string obj,string base returns nothing
    call KKJN_BuildBlob(obj)
    call KKJN_WriteParts(base)
    call SaveBoolean(KKJN_dbf, StringHash(obj), -2, true)
    call SaveBoolean(KKJN_dbf, StringHash(obj), -3, true)
endfunction

function KKJN_LoadIndex takes string user returns nothing
    local integer ik=KKJN_IKey(user)
    local string base=KKJN_BaseIndex(user)
    local integer count
    local integer k=0
    local integer g
    local integer part=0
    local string s
    if HaveSavedBoolean(KKJN_dbf, ik, -2) or KKJN_nslots<1 then
        return
    endif
    call SaveBoolean(KKJN_dbf, ik, -2, true)
    call SaveInteger(KKJN_dbf, ik, -1, 0)
    call KKJN_SlotClear()
    call Preloader(base+"0.pld")
    set s=KKJN_SlotGet(0)
    if s!="" and SubString(s, 0, 1)=="#" then
        set count=S2I(SubString(s, 1, StringLength(s)))
        if count<0 then
            set count=0
        endif
        loop
            exitwhen k>=count
            set g=k+1
            if g/KKJN_nslots!=part then
                set part=g/KKJN_nslots
                call KKJN_SlotClear()
                call Preloader(base+I2S(part)+".pld")
            endif
            call SaveStr(KKJN_dbf, ik, k, KKJN_SlotGet(g-part*KKJN_nslots))
            set k=k+1
        endloop
        call SaveInteger(KKJN_dbf, ik, -1, count)
    endif
    call KKJN_SlotRestore()
endfunction

function KKJN_SaveIndex takes string user returns nothing
    local integer ik=KKJN_IKey(user)
    local string base=KKJN_BaseIndex(user)
    local integer count=LoadInteger(KKJN_dbf, ik, -1)
    local integer parts
    local integer p=0
    local integer s
    local integer g
    local string nm
    if KKJN_nslots<1 then
        return
    endif
    set parts=(count+1+KKJN_nslots-1)/KKJN_nslots
    if parts<1 then
        set parts=1
    endif
    loop
        exitwhen p>=parts
        call PreloadGenClear()
        call PreloadGenStart()
        set s=0
        loop
            exitwhen s>=KKJN_nslots
            set g=p*KKJN_nslots+s
            if g==0 then
                call KKJN_WriteSlot(0, "#"+I2S(count))
            elseif g<=count then
                set nm=LoadStr(KKJN_dbf, ik, g-1)
                if nm==null then
                    set nm=""
                endif
                call KKJN_WriteSlot(s, nm)
            endif
            set s=s+1
        endloop
        call PreloadGenEnd(base+I2S(p)+".pld")
        set p=p+1
    endloop
endfunction

function KKJN_IndexAdd takes string user,string name returns nothing
    local integer ik=KKJN_IKey(user)
    local integer count
    local integer i=0
    call KKJN_LoadIndex(user)
    set count=LoadInteger(KKJN_dbf, ik, -1)
    loop
        exitwhen i>=count
        if LoadStr(KKJN_dbf, ik, i)==name then
            return
        endif
        set i=i+1
    endloop
    call SaveStr(KKJN_dbf, ik, count, name)
    call SaveInteger(KKJN_dbf, ik, -1, count+1)
    call KKJN_SaveIndex(user)
endfunction

function KKJN_CurChar takes string user returns string
    local string c
    if not HaveSavedString(KKJN_dbf, KKJN_AKey(user), 0) then
        return ""
    endif
    set c=LoadStr(KKJN_dbf, KKJN_AKey(user), 0)
    if c==null then
        return ""
    endif
    return c
endfunction

function KKJN_CurNs takes string user returns string
    local string c=LoadStr(KKJN_dbf, KKJN_AKey(user), 2)
    if c==null then
        return ""
    endif
    return c
endfunction

function KKJN_CharObj takes string UserId returns string
    local string u
    local string c
    if not KKJN_pronto or UserId==null or UserId=="" then
        return ""
    endif
    set u=KKJN_UKey(UserId)
    set c=KKJN_CurChar(u)
    if c=="" then
        return ""
    endif
    return KKJN_ObjChar(u, c)
endfunction

function KKJN_UserObj takes string UserId returns string
    local string u
    if not KKJN_pronto or UserId==null or UserId=="" then
        return ""
    endif
    set u=KKJN_UKey(UserId)
    return KKJN_ObjUser(u, KKJN_CurNs(u))
endfunction

function JNObjectCharacterInit takes string MapId,string UserId,string SecretKey,string Character returns integer
    local string u
    local string c=Character
    if not KKJN_pronto or UserId==null or UserId=="" then
        return 1
    endif
    set u=KKJN_UKey(UserId)
    if c==null then
        set c=""
    endif
    call SaveStr(KKJN_dbf, KKJN_AKey(u), 0, c)
    if KKJN_LoadOnce(KKJN_ObjChar(u, c), KKJN_BaseChar(u, c)) then
        return 0
    endif
    //{{KK_SE:KK_JN_INIT_ZERO}}
    return 0
    //{{KK_FIMSE:KK_JN_INIT_ZERO}}
    return 1
endfunction

function JNObjectCharacterSave takes string MapId,string UserId,string SecretKey,string Character returns string
    local string u
    local string c=Character
    if not KKJN_pronto or UserId==null or UserId=="" then
        return ""
    endif
    set u=KKJN_UKey(UserId)
    if c==null then
        set c=""
    endif
    call SaveStr(KKJN_dbf, KKJN_AKey(u), 0, c)
    call KKJN_SaveObj(KKJN_ObjChar(u, c), KKJN_BaseChar(u, c))
    if c!="" then
        call KKJN_IndexAdd(u, c)
    endif
    return KKJN_SALVO
endfunction

function JNObjectCharacterUseEndGameSave takes string MapId,string UserId,string SecretKey,string Character returns nothing
    call JNObjectCharacterSave(MapId, UserId, SecretKey, Character)
endfunction

function JNObjectCharacterSetInt takes string UserId,string Field,integer Value returns nothing
    local string o=KKJN_CharObj(UserId)
    if o!="" and Field!=null and Field!="" then
        call KKJN_SetFieldI(o, Field, Value)
    endif
endfunction

function JNObjectCharacterGetInt takes string UserId,string Field returns integer
    local string o=KKJN_CharObj(UserId)
    if o=="" or Field==null or Field=="" then
        return 0
    endif
    //{{KK_SE:KK_JN_BASE}}
    if KKJN_nbase>0 then
        return KKJN_Base(Field, KKJN_GetI(o, Field))
    endif
    //{{KK_FIMSE:KK_JN_BASE}}
    return KKJN_GetI(o, Field)
endfunction

function JNObjectCharacterSetString takes string UserId,string Field,string Value returns nothing
    local string o=KKJN_CharObj(UserId)
    if Value==null then
        set Value=""
    endif
    if o!="" and Field!=null and Field!="" then
        call KKJN_SetFieldS(o, Field, Value)
    endif
endfunction

function JNObjectCharacterGetString takes string UserId,string Field returns string
    local string o=KKJN_CharObj(UserId)
    if o=="" or Field==null or Field=="" then
        return ""
    endif
    return KKJN_GetS(o, Field)
endfunction

function JNObjectCharacterSetReal takes string UserId,string Field,real Value returns nothing
    call JNObjectCharacterSetString(UserId, Field, R2S(Value))
endfunction

function JNObjectCharacterGetReal takes string UserId,string Field returns real
    return S2R(JNObjectCharacterGetString(UserId, Field))
endfunction

function JNObjectCharacterSetBoolean takes string UserId,string Field,boolean Value returns nothing
    if Value then
        call JNObjectCharacterSetInt(UserId, Field, 1)
    else
        call JNObjectCharacterSetInt(UserId, Field, 0)
    endif
endfunction

function JNObjectCharacterGetBoolean takes string UserId,string Field returns boolean
    return JNObjectCharacterGetInt(UserId, Field)!=0
endfunction

function JNObjectCharacterRemoveField takes string Userid,string Field returns nothing
    local string o=KKJN_CharObj(Userid)
    if o!="" and Field!=null and Field!="" then
        call KKJN_RemoveField(o, Field)
    endif
endfunction

function JNObjectCharacterClearField takes string UserId returns nothing
    local string o=KKJN_CharObj(UserId)
    if o!="" then
        call KKJN_ClearObj(o)
    endif
endfunction

function JNObjectCharacterResetCharacter takes string UserId returns nothing
    local string u
    local string o
    if not KKJN_pronto or UserId==null or UserId=="" then
        return
    endif
    set u=KKJN_UKey(UserId)
    set o=KKJN_ObjChar(u, KKJN_CurChar(u))
    call KKJN_ClearObj(o)
    call RemoveSavedBoolean(KKJN_dbf, StringHash(o), -2)
    call RemoveSavedBoolean(KKJN_dbf, StringHash(o), -3)
    call SaveStr(KKJN_dbf, KKJN_AKey(u), 0, "")
endfunction

function JNObjectCharacterGetCharacterCount takes string MapId,string UserId,string SecretKey returns integer
    if not KKJN_pronto or UserId==null or UserId=="" then
        return 0
    endif
    call KKJN_LoadIndex(KKJN_UKey(UserId))
    return LoadInteger(KKJN_dbf, KKJN_IKey(KKJN_UKey(UserId)), -1)
endfunction

function JNObjectCharacterGetCharacterNameByIndex takes string UserId,integer Index returns string
    local string u
    local string s
    if not KKJN_pronto or UserId==null or UserId=="" or Index<0 then
        return ""
    endif
    set u=KKJN_UKey(UserId)
    call KKJN_LoadIndex(u)
    if Index>=LoadInteger(KKJN_dbf, KKJN_IKey(u), -1) then
        return ""
    endif
    set s=LoadStr(KKJN_dbf, KKJN_IKey(u), Index)
    if s==null then
        return ""
    endif
    return s
endfunction

function JNObjectCharacterServerConnectCheck takes nothing returns boolean
    return true
endfunction

function JNObjectCharacterSendGlobalMessage takes string message returns nothing
endfunction

function JNObjectCharacterPopGlobalMessage takes nothing returns string
    return ""
endfunction

function JNRPGGetCharacterCount takes string MapId,string UserId,string SecretKey returns integer
    return JNObjectCharacterGetCharacterCount(MapId, UserId, SecretKey)
endfunction

function JNRPGGetCharacterNameByIndex takes string UserId,integer Index returns string
    return JNObjectCharacterGetCharacterNameByIndex(UserId, Index)
endfunction

function JNObjectUserInit takes string MapId,string Userid,string SecretKey,string Character returns integer
    local string u
    local string ns=Character
    if not KKJN_pronto or Userid==null or Userid=="" then
        return 1
    endif
    set u=KKJN_UKey(Userid)
    if ns==null then
        set ns=""
    endif
    call SaveStr(KKJN_dbf, KKJN_AKey(u), 2, ns)
    if KKJN_LoadOnce(KKJN_ObjUser(u, ns), KKJN_BaseUser(u, ns)) then
        return 0
    endif
    //{{KK_SE:KK_JN_INIT_ZERO}}
    return 0
    //{{KK_FIMSE:KK_JN_INIT_ZERO}}
    return 1
endfunction

//{{KK_SE:KK_JN_INIT2}}
function JNObjectUserInit2 takes string MapId,string Userid,string SecretKey,string Character returns integer
    return JNObjectUserInit(MapId, Userid, SecretKey, Character)
endfunction
//{{KK_FIMSE:KK_JN_INIT2}}

function JNObjectUserSave takes string MapId,string UserId,string SecretKey,string Character returns string
    local string u
    local string ns=Character
    if not KKJN_pronto or UserId==null or UserId=="" then
        return ""
    endif
    set u=KKJN_UKey(UserId)
    if ns==null then
        set ns=""
    endif
    call SaveStr(KKJN_dbf, KKJN_AKey(u), 2, ns)
    call KKJN_SaveObj(KKJN_ObjUser(u, ns), KKJN_BaseUser(u, ns))
    return KKJN_SALVO
endfunction

function JNObjectUserUseEndGameSave takes string MapId,string UserId,string SecretKey,string Character returns nothing
    call JNObjectUserSave(MapId, UserId, SecretKey, Character)
endfunction

function JNObjectUserSetInt takes string UserId,string Field,integer Value returns nothing
    local string o=KKJN_UserObj(UserId)
    if o!="" and Field!=null and Field!="" then
        call KKJN_SetFieldI(o, Field, Value)
    endif
endfunction

function JNObjectUserGetInt takes string UserId,string Field returns integer
    local string o=KKJN_UserObj(UserId)
    if o=="" or Field==null or Field=="" then
        return 0
    endif
    //{{KK_SE:KK_JN_BASE}}
    if KKJN_nbase>0 then
        return KKJN_Base(Field, KKJN_GetI(o, Field))
    endif
    //{{KK_FIMSE:KK_JN_BASE}}
    return KKJN_GetI(o, Field)
endfunction

function JNObjectUserSetString takes string UserId,string Field,string Value returns nothing
    local string o=KKJN_UserObj(UserId)
    if Value==null then
        set Value=""
    endif
    if o!="" and Field!=null and Field!="" then
        call KKJN_SetFieldS(o, Field, Value)
    endif
endfunction

function JNObjectUserGetString takes string UserId,string Field returns string
    local string o=KKJN_UserObj(UserId)
    if o=="" or Field==null or Field=="" then
        return ""
    endif
    return KKJN_GetS(o, Field)
endfunction

function JNObjectUserSetReal takes string UserId,string Field,real Value returns nothing
    call JNObjectUserSetString(UserId, Field, R2S(Value))
endfunction

function JNObjectUserGetReal takes string UserId,string Field returns real
    return S2R(JNObjectUserGetString(UserId, Field))
endfunction

function JNObjectUserSetBoolean takes string UserId,string Field,boolean Value returns nothing
    if Value then
        call JNObjectUserSetInt(UserId, Field, 1)
    else
        call JNObjectUserSetInt(UserId, Field, 0)
    endif
endfunction

function JNObjectUserGetBoolean takes string UserId,string Field returns boolean
    return JNObjectUserGetInt(UserId, Field)!=0
endfunction

function JNObjectUserRemoveField takes string UserId,string Field returns nothing
    local string o=KKJN_UserObj(UserId)
    if o!="" and Field!=null and Field!="" then
        call KKJN_RemoveField(o, Field)
    endif
endfunction

function JNObjectUserClearField takes string UserId returns nothing
    local string o=KKJN_UserObj(UserId)
    if o!="" then
        call KKJN_ClearObj(o)
    endif
endfunction

function JNObjectUserResetCharacter takes string UserId returns nothing
    call JNObjectUserClearField(UserId)
endfunction

function JNObjectMapInit takes string MapId,string SecretKey returns integer
    return 0
endfunction

function JNObjectMapGetInt takes string Field returns integer
    if not KKJN_pronto or Field==null then
        return 0
    endif
    return KKJN_GetI("map", Field)
endfunction

function JNObjectMapGetReal takes string Field returns real
    if not KKJN_pronto or Field==null then
        return 0.0
    endif
    return S2R(KKJN_GetS("map", Field))
endfunction

function JNObjectMapGetString takes string Field returns string
    if not KKJN_pronto or Field==null then
        return ""
    endif
    return KKJN_GetS("map", Field)
endfunction

function JNObjectScoreInit takes string MapId,string SecretKey,string UserId,string Character returns integer
    return 0
endfunction

function JNObjectScoreGet takes string UserId,string Field returns integer
    if not KKJN_pronto or UserId==null or Field==null then
        return 0
    endif
    return KKJN_GetI("s|"+KKJN_UKey(UserId), Field)
endfunction

function JNObjectScoreSet takes string UserId,string Field,integer Value returns nothing
    if KKJN_pronto and UserId!=null and Field!=null and Field!="" then
        call KKJN_SetFieldI("s|"+KKJN_UKey(UserId), Field, Value)
    endif
endfunction

function JNObjectScoreAdd takes string UserId,string Field,integer Value returns nothing
    call JNObjectScoreSet(UserId, Field, JNObjectScoreGet(UserId, Field)+Value)
endfunction

function JNObjectScoreSave takes string MapId,string SecretKey,string UserId,string Character returns string
    return KKJN_SALVO
endfunction

function KKJN_DiaKey takes string user,string ch,string typ returns integer
    if ch==null then
        set ch=""
    endif
    if typ==null then
        set typ=""
    endif
    return StringHash("d|"+KKJN_UKey(user)+"|"+ch+"|"+typ)
endfunction

function JNDailyCheckToday takes string MapId,string UserId,string SecretKey,string Character,string DailyType returns string
    if not KKJN_pronto or UserId==null or UserId=="" then
        return ""
    endif
    if HaveSavedBoolean(KKJN_db, KKJN_DiaKey(UserId, Character, DailyType), 1) then
        return KKJN_DIARIO
    endif
    return ""
endfunction

function JNDailySave takes string MapId,string UserId,string SecretKey,string Character,string DailyType returns string
    if KKJN_pronto and UserId!=null and UserId!="" then
        call SaveBoolean(KKJN_db, KKJN_DiaKey(UserId, Character, DailyType), 1, true)
    endif
    return ""
endfunction

function KKJN_IsCont takes string b returns boolean
    return KKJN_pronto and HaveSavedBoolean(KKJN_cont, 0, StringHash(KKJN_C2+b))
endfunction

function KKJN_CharLen takes string s returns integer
    local integer n=StringLength(s)
    local integer i=0
    local integer c=0
    loop
        exitwhen i>=n
        if not KKJN_IsCont(SubString(s, i, i+1)) then
            set c=c+1
        endif
        set i=i+1
    endloop
    return c
endfunction

function KKJN_CharToByte takes string s,integer ci returns integer
    local integer n=StringLength(s)
    local integer i=0
    local integer c=0
    if ci<=0 then
        return 0
    endif
    loop
        exitwhen i>=n
        if not KKJN_IsCont(SubString(s, i, i+1)) then
            if c==ci then
                return i
            endif
            set c=c+1
        endif
        set i=i+1
    endloop
    return n
endfunction

function KKJN_ByteToChar takes string s,integer bi returns integer
    local integer n=StringLength(s)
    local integer i=0
    local integer c=0
    loop
        exitwhen i>=bi or i>=n
        if not KKJN_IsCont(SubString(s, i, i+1)) then
            set c=c+1
        endif
        set i=i+1
    endloop
    return c
endfunction

function JNStringLength takes string str returns integer
    if str==null then
        return 0
    endif
    return KKJN_CharLen(str)
endfunction

function JNStringPos takes string str,string sub returns integer
    local integer b
    if str==null or sub==null then
        return -1
    endif
    set b=KKJN_PosB(str, sub, 0)
    if b<0 then
        return -1
    endif
    return KKJN_ByteToChar(str, b)
endfunction

function JNStringSub takes string str,integer start,integer length returns string
    local integer b0
    if str==null or length==0 then
        return ""
    endif
    if start<0 then
        set length=length+start
        set start=0
    endif
    set b0=KKJN_CharToByte(str, start)
    if b0>=StringLength(str) then
        return ""
    endif
    if length<0 then
        return SubString(str, b0, StringLength(str))
    endif
    return SubString(str, b0, KKJN_CharToByte(str, start+length))
endfunction

function JNStringSplit takes string str,string sub,integer index returns string
    local integer n
    local integer m
    local integer i=0
    local integer k=0
    local integer p
    if str==null or sub==null or index<0 then
        return ""
    endif
    set n=StringLength(str)
    set m=StringLength(sub)
    if m<=0 then
        if index==0 then
            return str
        endif
        return ""
    endif
    loop
        set p=KKJN_PosB(str, sub, i)
        if p<0 then
            if k==index then
                return SubString(str, i, n)
            endif
            return ""
        endif
        if k==index then
            return SubString(str, i, p)
        endif
        set k=k+1
        set i=p+m
    endloop
    return ""
endfunction

//{{KK_SE:KK_JN_REGEX}}
function KKRX_Cod takes string ch returns integer
    local integer v
    if StringLength(ch)!=1 then
        return 256
    endif
    set v=DB_ord(ch)
    if v>=0 then
        return v
    elseif ch=="\t" then
        return 9
    elseif ch=="\n" then
        return 10
    elseif ch=="\r" then
        return 13
    endif
    return 256
endfunction

function KKRX_Txt takes integer v returns string
    if v==9 then
        return "\t"
    elseif v==10 then
        return "\n"
    elseif v==13 then
        return "\r"
    endif
    return DB_chr(v)
endfunction

function KKRX_Hex takes string c returns integer
    local integer i=0
    loop
        exitwhen i>=16
        if SubString("0123456789abcdef", i, i+1)==c or SubString("0123456789ABCDEF", i, i+1)==c then
            return i
        endif
        set i=i+1
    endloop
    return -1
endfunction

function KKRX_PCar takes nothing returns string
    local integer j=KKRX_pp+1
    loop
        exitwhen j>=KKRX_pn
        exitwhen not KKJN_IsCont(SubString(KKRX_pat, j, j+1))
        set j=j+1
    endloop
    return SubString(KKRX_pat, KKRX_pp, j)
endfunction

function KKRX_Poe takes integer i,integer op,integer a,integer b,integer d,string s returns nothing
    set KKRX_op[i]=op
    set KKRX_a[i]=a
    set KKRX_b[i]=b
    set KKRX_d[i]=d
    set KKRX_s[i]=s
endfunction

function KKRX_Emite takes integer op,integer a,integer b,integer d,string s returns integer
    if KKRX_top>=KKRX_CODIGO then
        set KKRX_erro=true
        return KKRX_CODIGO-1
    endif
    call KKRX_Poe(KKRX_top, op, a, b, d, s)
    set KKRX_top=KKRX_top+1
    return KKRX_top-1
endfunction

function KKRX_Copia takes integer de,integer para returns nothing
    set KKRX_op[para]=KKRX_op[de]
    set KKRX_a[para]=KKRX_a[de]
    set KKRX_b[para]=KKRX_b[de]
    set KKRX_d[para]=KKRX_d[de]
    set KKRX_s[para]=KKRX_s[de]
endfunction

function KKRX_Abre takes integer em,integer k returns nothing
    local integer i=KKRX_top-1
    if KKRX_top+k>KKRX_CODIGO then
        set KKRX_erro=true
        return
    endif
    loop
        exitwhen i<em
        call KKRX_Copia(i, i+k)
        set i=i-1
    endloop
    set KKRX_top=KKRX_top+k
endfunction

function KKRX_Fecha takes integer i returns nothing
    loop
        exitwhen i>=KKRX_top-1
        call KKRX_Copia(i+1, i)
        set i=i+1
    endloop
    set KKRX_top=KKRX_top-1
endfunction

function KKRX_Gira takes integer seq,integer ini returns nothing
    local integer L=KKRX_top-ini
    local integer i=0
    if ini<=seq or L<=0 then
        return
    endif
    loop
        exitwhen i>=L
        call KKRX_Copia(ini+i, KKRX_top+i)
        set i=i+1
    endloop
    set i=ini-1
    loop
        exitwhen i<seq
        call KKRX_Copia(i, i+L)
        set i=i-1
    endloop
    set i=0
    loop
        exitwhen i>=L
        call KKRX_Copia(KKRX_top+i, seq+i)
        set i=i+1
    endloop
endfunction

function KKRX_Nulo takes integer ini,integer fim returns boolean
    local integer n=0
    local integer pc
    local integer op
    set KKRX_carimbo=KKRX_carimbo+1
    set KKRX_wl[0]=ini
    set n=1
    loop
        exitwhen n<=0
        set n=n-1
        set pc=KKRX_wl[n]
        if pc==fim then
            return true
        endif
        if pc>=ini and pc<fim and KKRX_vis[pc]!=KKRX_carimbo and n<KKRX_CODIGO-2 then
            set KKRX_vis[pc]=KKRX_carimbo
            set op=KKRX_op[pc]
            if op==4 then
                set KKRX_wl[n]=pc+KKRX_a[pc]
                set KKRX_wl[n+1]=pc+KKRX_b[pc]
                set n=n+2
            elseif op==5 then
                set KKRX_wl[n]=pc+KKRX_a[pc]
                set n=n+1
            elseif op==8 or op==12 then
                set KKRX_wl[n]=pc+KKRX_b[pc]
                set n=n+1
                if op==12 then
                    set KKRX_wl[n]=pc+1
                    set n=n+1
                endif
            elseif op==6 or op==7 or op==10 or op==11 then
                set KKRX_wl[n]=pc+1
                set n=n+1
            endif
        endif
    endloop
    return false
endfunction

function KKRX_Quant takes integer ini,integer tipo,boolean guloso returns nothing
    local integer L=KKRX_top-ini
    local integer pc
    local integer k
    if tipo!=3 and KKRX_Nulo(ini, KKRX_top) then
        if KKRX_nl>=500 then
            set KKRX_erro=true
            return
        endif
        set k=KKRX_nl
        set KKRX_nl=KKRX_nl+1
        if tipo==1 then
            call KKRX_Abre(ini, 2)
            if KKRX_erro then
                return
            endif
            call KKRX_Poe(ini, 4, 1, L+4, 0, "")
            call KKRX_Poe(ini+1, 11, k, 0, 0, "")
            call KKRX_Emite(12, k, 2, 0, "")
            call KKRX_Emite(5, 0-(L+3), 0, 0, "")
            if not guloso then
                set KKRX_a[ini]=L+4
                set KKRX_b[ini]=1
            endif
        else
            call KKRX_Abre(ini, 1)
            if KKRX_erro then
                return
            endif
            call KKRX_Poe(ini, 11, k, 0, 0, "")
            call KKRX_Emite(12, k, 2, 0, "")
            set pc=KKRX_Emite(4, 0-(L+2), 1, 0, "")
            if not guloso then
                set KKRX_a[pc]=1
                set KKRX_b[pc]=0-(L+2)
            endif
        endif
        return
    endif
    if tipo==2 then
        set pc=KKRX_Emite(4, 0-L, 1, 0, "")
        if not guloso then
            set KKRX_a[pc]=1
            set KKRX_b[pc]=0-L
        endif
        return
    endif
    call KKRX_Abre(ini, 1)
    if KKRX_erro then
        return
    endif
    if tipo==1 then
        call KKRX_Poe(ini, 4, 1, L+2, 0, "")
        call KKRX_Emite(5, 0-(L+1), 0, 0, "")
    else
        call KKRX_Poe(ini, 4, 1, L+1, 0, "")
    endif
    if not guloso then
        set KKRX_a[ini]=KKRX_b[ini]
        set KKRX_b[ini]=1
    endif
endfunction

function KKRX_Cola takes integer L returns nothing
    local integer i=0
    if KKRX_top+L>KKRX_CODIGO then
        set KKRX_erro=true
        return
    endif
    loop
        exitwhen i>=L
        call KKRX_Copia(KKRX_GUARDA+i, KKRX_top+i)
        set i=i+1
    endloop
    set KKRX_top=KKRX_top+L
endfunction

function KKRX_Repete takes integer ini,integer m,integer n,boolean guloso returns nothing
    local integer L=KKRX_top-ini
    local integer i=0
    local integer s
    if m>100 or n>100 or (n>=0 and n<m) then
        set KKRX_erro=true
        return
    endif
    loop
        exitwhen i>=L
        call KKRX_Copia(ini+i, KKRX_GUARDA+i)
        set i=i+1
    endloop
    set KKRX_top=ini
    set i=0
    loop
        exitwhen i>=m or KKRX_erro
        call KKRX_Cola(L)
        set i=i+1
    endloop
    if n<0 then
        set s=KKRX_top
        call KKRX_Cola(L)
        call KKRX_Quant(s, 1, guloso)
        return
    endif
    loop
        exitwhen i>=n or KKRX_erro
        set s=KKRX_top
        call KKRX_Cola(L)
        call KKRX_Quant(s, 3, guloso)
        set i=i+1
    endloop
endfunction

function KKRX_Item takes integer lo,integer hi,string ls returns nothing
    if KKRX_nr>=2000 then
        set KKRX_erro=true
        return
    endif
    set KKRX_lo[KKRX_nr]=lo
    set KKRX_hi[KKRX_nr]=hi
    set KKRX_ls[KKRX_nr]=ls
    set KKRX_nr=KKRX_nr+1
endfunction

function KKRX_Atalho takes string c returns nothing
    if c=="d" then
        call KKRX_Item(48, 57, "")
    elseif c=="w" then
        call KKRX_Item(48, 57, "")
        call KKRX_Item(65, 90, "")
        call KKRX_Item(97, 122, "")
        call KKRX_Item(95, 95, "")
        call KKRX_Item(256, 256, "")
    else
        call KKRX_Item(9, 13, "")
        call KKRX_Item(32, 32, "")
    endif
endfunction

function KKRX_Esc takes nothing returns integer
    local string c=SubString(KKRX_pat, KKRX_pp, KKRX_pp+1)
    local integer v
    local integer w
    set KKRX_et=""
    set KKRX_en=false
    if KKRX_pp>=KKRX_pn then
        set KKRX_erro=true
        return 0
    endif
    set KKRX_pp=KKRX_pp+1
    if c=="d" or c=="w" or c=="s" then
        call KKRX_Atalho(c)
        return -2
    elseif c=="D" or c=="W" or c=="S" then
        call KKRX_Atalho(StringCase(c, false))
        set KKRX_en=true
        return -2
    elseif c=="b" then
        return -3
    elseif c=="B" then
        return -4
    elseif c=="t" then
        set KKRX_et="\t"
        return 9
    elseif c=="n" then
        set KKRX_et="\n"
        return 10
    elseif c=="r" then
        set KKRX_et="\r"
        return 13
    elseif c=="f" then
        return 12
    elseif c=="v" then
        return 11
    elseif c=="e" then
        return 27
    elseif c=="x" then
        set v=KKRX_Hex(SubString(KKRX_pat, KKRX_pp, KKRX_pp+1))
        set w=KKRX_Hex(SubString(KKRX_pat, KKRX_pp+1, KKRX_pp+2))
        if v<0 or w<0 then
            set KKRX_erro=true
            return 0
        endif
        set KKRX_pp=KKRX_pp+2
        set v=v*16+w
        set KKRX_et=KKRX_Txt(v)
        return v
    endif
    set v=KKRX_Hex(c)
    if (v>=0 and v<=9) or c=="u" or c=="p" or c=="P" or c=="k" or c=="A" or c=="Z" or c=="z" or c=="G" or c=="c" then
        set KKRX_erro=true
        return 0
    endif
    set KKRX_pp=KKRX_pp-1
    set KKRX_et=KKRX_PCar()
    set KKRX_pp=KKRX_pp+StringLength(KKRX_et)
    return KKRX_Cod(KKRX_et)
endfunction

function KKRX_Classe takes integer d returns nothing
    local integer ini=KKRX_nr
    local boolean neg=false
    local boolean primeiro=true
    local boolean atalho
    local string c
    local string t
    local integer v
    local integer w
    set KKRX_pp=KKRX_pp+1
    if SubString(KKRX_pat, KKRX_pp, KKRX_pp+1)=="^" then
        set neg=true
        set KKRX_pp=KKRX_pp+1
    endif
    loop
        if KKRX_pp>=KKRX_pn or KKRX_erro then
            set KKRX_erro=true
            return
        endif
        set c=SubString(KKRX_pat, KKRX_pp, KKRX_pp+1)
        exitwhen c=="]" and not primeiro
        set primeiro=false
        set atalho=false
        if c=="\\" then
            set KKRX_pp=KKRX_pp+1
            set v=KKRX_Esc()
            if v==-2 then
                set atalho=true
                if KKRX_en then
                    set KKRX_erro=true
                endif
            elseif v==-3 then
                set v=8
            elseif v==-4 then
                set KKRX_erro=true
            endif
            set t=KKRX_et
        else
            set t=KKRX_PCar()
            set KKRX_pp=KKRX_pp+StringLength(t)
            set v=KKRX_Cod(t)
        endif
        if not atalho then
            if SubString(KKRX_pat, KKRX_pp, KKRX_pp+1)=="-" and KKRX_pp+1<KKRX_pn and SubString(KKRX_pat, KKRX_pp+1, KKRX_pp+2)!="]" then
                set KKRX_pp=KKRX_pp+1
                set c=SubString(KKRX_pat, KKRX_pp, KKRX_pp+1)
                if c=="\\" then
                    set KKRX_pp=KKRX_pp+1
                    set w=KKRX_Esc()
                elseif c=="[" then
                    set w=-1
                else
                    set c=KKRX_PCar()
                    set KKRX_pp=KKRX_pp+StringLength(c)
                    set w=KKRX_Cod(c)
                endif
                if v<0 or w<0 or v>=256 or w>=256 or w<v then
                    set KKRX_erro=true
                else
                    call KKRX_Item(v, w, "")
                endif
            elseif t!="" then
                call KKRX_Item(-2, -2, t)
            else
                call KKRX_Item(v, v, "")
            endif
        endif
    endloop
    set KKRX_pp=KKRX_pp+1
    if neg then
        set t="n"
    else
        set t=""
    endif
    call KKRX_Emite(3, ini, KKRX_nr-ini, d, t)
endfunction

function KKRX_Chaves takes nothing returns integer
    local integer i=KKRX_pp+1
    local integer m=0
    local integer n=0
    local integer d
    local boolean tem=false
    loop
        exitwhen i>=KKRX_pn or m>1000
        set d=KKRX_Hex(SubString(KKRX_pat, i, i+1))
        exitwhen d<0 or d>9
        set m=m*10+d
        set tem=true
        set i=i+1
    endloop
    if not tem then
        return -1
    endif
    if SubString(KKRX_pat, i, i+1)=="}" then
        set KKRX_qm=m
        set KKRX_qn=m
        return i+1
    endif
    if SubString(KKRX_pat, i, i+1)!="," then
        return -1
    endif
    set i=i+1
    set tem=false
    loop
        exitwhen i>=KKRX_pn or n>1000
        set d=KKRX_Hex(SubString(KKRX_pat, i, i+1))
        exitwhen d<0 or d>9
        set n=n*10+d
        set tem=true
        set i=i+1
    endloop
    if SubString(KKRX_pat, i, i+1)!="}" then
        return -1
    endif
    if not tem then
        set n=-1
    endif
    set KKRX_qm=m
    set KKRX_qn=n
    return i+1
endfunction

function KKRX_Alt takes boolean rev returns nothing
    local integer seq=KKRX_top
    local integer base=KKRX_np
    local integer ini
    local integer pc
    local integer tipo
    local integer m
    local integer n
    local integer v
    local integer d=0
    local boolean guloso
    local boolean lit=false
    local boolean eh_lit
    local string c
    local string t
    if rev then
        set d=1
    endif
    loop
        exitwhen KKRX_pp>=KKRX_pn or KKRX_erro
        set c=SubString(KKRX_pat, KKRX_pp, KKRX_pp+1)
        exitwhen c==")"
        if c=="|" then
            set KKRX_pp=KKRX_pp+1
            set pc=KKRX_Emite(5, 0, 0, 0, "")
            call KKRX_Abre(seq, 1)
            if KKRX_np>=200 then
                set KKRX_erro=true
            endif
            exitwhen KKRX_erro
            call KKRX_Poe(seq, 4, 1, KKRX_top-seq, 0, "")
            set KKRX_pend[KKRX_np]=pc+1
            set KKRX_np=KKRX_np+1
            set seq=KKRX_top
            set lit=false
        else
            set ini=KKRX_top
            set eh_lit=false
            set t=""
            if c=="(" then
                set KKRX_pp=KKRX_pp+1
                set tipo=-1
                if SubString(KKRX_pat, KKRX_pp, KKRX_pp+1)=="?" then
                    set c=SubString(KKRX_pat, KKRX_pp+1, KKRX_pp+2)
                    if c==":" then
                        set KKRX_pp=KKRX_pp+2
                    elseif c=="=" then
                        set tipo=0
                        set KKRX_pp=KKRX_pp+2
                    elseif c=="!" then
                        set tipo=1
                        set KKRX_pp=KKRX_pp+2
                    elseif c=="<" and SubString(KKRX_pat, KKRX_pp+2, KKRX_pp+3)=="=" then
                        set tipo=2
                        set KKRX_pp=KKRX_pp+3
                    elseif c=="<" and SubString(KKRX_pat, KKRX_pp+2, KKRX_pp+3)=="!" then
                        set tipo=3
                        set KKRX_pp=KKRX_pp+3
                    elseif c=="<" then
                        set v=KKJN_PosB(KKRX_pat, ">", KKRX_pp)
                        if v<0 then
                            set KKRX_erro=true
                        else
                            set KKRX_pp=v+1
                        endif
                    else
                        set KKRX_erro=true
                    endif
                endif
                if tipo>=0 then
                    set pc=KKRX_Emite(8, tipo, 0, 0, "")
                    call KKRX_Alt(tipo>=2)
                    call KKRX_Emite(9, 0, 0, 0, "")
                    set KKRX_b[pc]=KKRX_top-pc
                else
                    call KKRX_Alt(rev)
                endif
                if SubString(KKRX_pat, KKRX_pp, KKRX_pp+1)==")" then
                    set KKRX_pp=KKRX_pp+1
                else
                    set KKRX_erro=true
                endif
            elseif c=="[" then
                call KKRX_Classe(d)
            elseif c=="." then
                set KKRX_pp=KKRX_pp+1
                call KKRX_Emite(2, 0, 0, d, "")
            elseif c=="^" then
                set KKRX_pp=KKRX_pp+1
                call KKRX_Emite(6, 0, 0, 0, "")
            elseif c=="$" then
                set KKRX_pp=KKRX_pp+1
                call KKRX_Emite(7, 0, 0, 0, "")
            elseif c=="\\" then
                set KKRX_pp=KKRX_pp+1
                set m=KKRX_nr
                set v=KKRX_Esc()
                if v==-2 then
                    if KKRX_en then
                        set t="n"
                    endif
                    call KKRX_Emite(3, m, KKRX_nr-m, d, t)
                    set t=""
                elseif v==-3 then
                    call KKRX_Emite(10, 0, 0, 0, "")
                elseif v==-4 then
                    call KKRX_Emite(10, 1, 0, 0, "")
                elseif KKRX_et=="" then
                    set KKRX_erro=true
                else
                    set t=KKRX_et
                    set eh_lit=true
                endif
            elseif c=="*" or c=="+" or c=="?" then
                set KKRX_erro=true
            else
                set t=KKRX_PCar()
                set KKRX_pp=KKRX_pp+StringLength(t)
                set eh_lit=true
            endif
            if eh_lit then
                call KKRX_Emite(1, StringLength(t), 0, d, t)
            endif
            set tipo=0
            set c=SubString(KKRX_pat, KKRX_pp, KKRX_pp+1)
            if c=="*" then
                set tipo=1
                set KKRX_pp=KKRX_pp+1
            elseif c=="+" then
                set tipo=2
                set KKRX_pp=KKRX_pp+1
            elseif c=="?" then
                set tipo=3
                set KKRX_pp=KKRX_pp+1
            elseif c=="{" then
                set v=KKRX_Chaves()
                if v>=0 then
                    set tipo=4
                    set m=KKRX_qm
                    set n=KKRX_qn
                    set KKRX_pp=v
                endif
            endif
            if tipo>0 and not KKRX_erro then
                set guloso=true
                if SubString(KKRX_pat, KKRX_pp, KKRX_pp+1)=="?" then
                    set guloso=false
                    set KKRX_pp=KKRX_pp+1
                endif
                if tipo==4 then
                    call KKRX_Repete(ini, m, n, guloso)
                else
                    call KKRX_Quant(ini, tipo, guloso)
                endif
                set eh_lit=false
            endif
            exitwhen KKRX_erro
            if rev and KKRX_top>ini then
                call KKRX_Gira(seq, ini)
                if eh_lit and lit then
                    set KKRX_s[seq]=KKRX_s[seq+1]+KKRX_s[seq]
                    set KKRX_a[seq]=KKRX_a[seq]+KKRX_a[seq+1]
                    call KKRX_Fecha(seq+1)
                endif
            elseif eh_lit and lit then
                set KKRX_s[ini-1]=KKRX_s[ini-1]+KKRX_s[ini]
                set KKRX_a[ini-1]=KKRX_a[ini-1]+KKRX_a[ini]
                set KKRX_top=KKRX_top-1
            endif
            set lit=eh_lit
        endif
    endloop
    loop
        exitwhen KKRX_np<=base
        set KKRX_np=KKRX_np-1
        set pc=KKRX_pend[KKRX_np]
        set KKRX_a[pc]=KKRX_top-pc
    endloop
endfunction

function KKRX_Compila takes string pat returns boolean
    local integer pc=0
    local string t=""
    set KKRX_pat=pat
    set KKRX_pn=StringLength(pat)
    set KKRX_pp=0
    set KKRX_top=0
    set KKRX_nr=0
    set KKRX_np=0
    set KKRX_nl=0
    set KKRX_erro=false
    call KKRX_Alt(false)
    if KKRX_pp<KKRX_pn then
        set KKRX_erro=true
    endif
    call KKRX_Emite(9, 0, 0, 0, "")
    if KKRX_erro then
        return false
    endif
    set KKRX_pmodo=0
    set KKRX_plit=""
    loop
        exitwhen KKRX_op[pc]!=8
        if KKRX_a[pc]==2 and KKRX_op[pc+1]==1 and t=="" then
            set t=KKRX_s[pc+1]
        endif
        set pc=pc+KKRX_b[pc]
    endloop
    if KKRX_op[pc]==1 then
        set KKRX_pmodo=1
        set KKRX_plit=KKRX_s[pc]
    elseif KKRX_op[pc]==6 then
        set KKRX_pmodo=3
    elseif t!="" then
        set KKRX_pmodo=2
        set KKRX_plit=t
    endif
    return true
endfunction

function KKRX_Pal takes string ch returns boolean
    local integer v=KKRX_Cod(ch)
    return v==95 or v==256 or (v>=48 and v<=57) or (v>=65 and v<=90) or (v>=97 and v<=122)
endfunction

function KKRX_NaClasse takes integer pc,string ch returns boolean
    local integer i=KKRX_a[pc]
    local integer e=i+KKRX_b[pc]
    local integer v=-1
    loop
        exitwhen i>=e
        if KKRX_lo[i]==-2 then
            if KKRX_ls[i]==ch then
                return KKRX_s[pc]==""
            endif
        else
            if v<0 then
                set v=KKRX_Cod(ch)
            endif
            if v>=KKRX_lo[i] and v<=KKRX_hi[i] then
                return KKRX_s[pc]==""
            endif
        endif
        set i=i+1
    endloop
    return KKRX_s[pc]!=""
endfunction

function KKRX_Antes takes integer sp returns integer
    local integer j=sp-1
    loop
        exitwhen j<=0
        exitwhen not KKJN_IsCont(SubString(KKRX_str, j, j+1))
        set j=j-1
    endloop
    return j
endfunction

function KKRX_Depois takes integer sp returns integer
    local integer j=sp+1
    loop
        exitwhen j>=KKRX_n
        exitwhen not KKJN_IsCont(SubString(KKRX_str, j, j+1))
        set j=j+1
    endloop
    return j
endfunction

function KKRX_Roda takes integer pc,integer sp returns integer
    local integer base=KKRX_sp
    local integer op
    local integer k
    local integer j
    local boolean ok
    local boolean w1
    local string ch
    loop
        set KKRX_passos=KKRX_passos+1
        if KKRX_passos>KKRX_TETO then
            set KKRX_estouro=true
        endif
        if KKRX_estouro then
            set KKRX_sp=base
            return -1
        endif
        set op=KKRX_op[pc]
        set ok=true
        if op==1 then
            set k=KKRX_a[pc]
            if KKRX_d[pc]==0 then
                if sp+k<=KKRX_n and SubString(KKRX_str, sp, sp+k)==KKRX_s[pc] then
                    set sp=sp+k
                else
                    set ok=false
                endif
            elseif sp-k>=0 and SubString(KKRX_str, sp-k, sp)==KKRX_s[pc] then
                set sp=sp-k
            else
                set ok=false
            endif
            set pc=pc+1
        elseif op==4 then
            if KKRX_sp>=KKRX_PILHA then
                set KKRX_estouro=true
                set KKRX_sp=base
                return -1
            endif
            set KKRX_spc[KKRX_sp]=pc+KKRX_b[pc]
            set KKRX_ssp[KKRX_sp]=sp
            set KKRX_sp=KKRX_sp+1
            set pc=pc+KKRX_a[pc]
        elseif op==2 or op==3 then
            if KKRX_d[pc]==0 then
                if sp>=KKRX_n then
                    set ok=false
                else
                    set k=KKRX_Depois(sp)
                    set ch=SubString(KKRX_str, sp, k)
                endif
            elseif sp<=0 then
                set ok=false
            else
                set k=KKRX_Antes(sp)
                set ch=SubString(KKRX_str, k, sp)
            endif
            if ok then
                if op==2 then
                    set ok=ch!="\n"
                else
                    set ok=KKRX_NaClasse(pc, ch)
                endif
                set sp=k
                set pc=pc+1
            endif
        elseif op==5 then
            set pc=pc+KKRX_a[pc]
        elseif op==6 then
            set ok=sp==0
            set pc=pc+1
        elseif op==7 then
            set ok=sp==KKRX_n or (sp==KKRX_n-1 and SubString(KKRX_str, sp, KKRX_n)=="\n")
            set pc=pc+1
        elseif op==8 then
            set k=KKRX_a[pc]
            set j=KKRX_Roda(pc+1, sp)
            if KKRX_estouro then
                set KKRX_sp=base
                return -1
            endif
            set ok=(j>=0)==(k==0 or k==2)
            set pc=pc+KKRX_b[pc]
        elseif op==9 then
            set KKRX_sp=base
            return sp
        elseif op==10 then
            set w1=false
            if sp>0 then
                set w1=KKRX_Pal(SubString(KKRX_str, KKRX_Antes(sp), sp))
            endif
            set ok=false
            if sp<KKRX_n then
                set ok=KKRX_Pal(SubString(KKRX_str, sp, KKRX_Depois(sp)))
            endif
            set ok=(w1!=ok)==(KKRX_a[pc]==0)
            set pc=pc+1
        elseif op==11 then
            if KKRX_sp>=KKRX_PILHA then
                set KKRX_estouro=true
                set KKRX_sp=base
                return -1
            endif
            set k=KKRX_a[pc]
            set KKRX_spc[KKRX_sp]=0-(k+1)
            set KKRX_ssp[KKRX_sp]=KKRX_reg[k]
            set KKRX_sp=KKRX_sp+1
            set KKRX_reg[k]=sp
            set pc=pc+1
        elseif op==12 then
            if sp==KKRX_reg[KKRX_a[pc]] then
                set pc=pc+KKRX_b[pc]
            else
                set pc=pc+1
            endif
        else
            set ok=false
        endif
        if not ok then
            loop
                if KKRX_sp<=base then
                    return -1
                endif
                set KKRX_sp=KKRX_sp-1
                set pc=KKRX_spc[KKRX_sp]
                exitwhen pc>=0
                set KKRX_reg[0-pc-1]=KKRX_ssp[KKRX_sp]
            endloop
            set sp=KKRX_ssp[KKRX_sp]
        endif
    endloop
    return -1
endfunction

function KKRX_Busca takes integer de returns integer
    local integer p=de
    local integer q
    local integer e
    local integer L=StringLength(KKRX_plit)
    loop
        exitwhen p>KKRX_n or KKRX_estouro
        if KKRX_pmodo==1 then
            set q=KKJN_PosB(KKRX_str, KKRX_plit, p)
            if q<0 then
                return -1
            endif
            set p=q
        elseif KKRX_pmodo==2 then
            set q=p-L
            if q<0 then
                set q=0
            endif
            set q=KKJN_PosB(KKRX_str, KKRX_plit, q)
            if q<0 then
                return -1
            endif
            set p=q+L
        elseif KKRX_pmodo==3 and p>0 then
            return -1
        endif
        set e=KKRX_Roda(0, p)
        if e>=0 then
            set KKRX_fim=e
            return p
        endif
        if KKRX_pmodo==1 or KKRX_pmodo==2 then
            set p=p+1
        elseif p>=KKRX_n then
            return -1
        else
            set p=KKRX_Depois(p)
        endif
    endloop
    return -1
endfunction

function KKRX_Enesimo takes integer de,integer idx returns string
    local integer p
    local integer k=0
    loop
        set p=KKRX_Busca(de)
        if p<0 then
            set KKRX_prox=-1
            return ""
        endif
        if KKRX_fim>p then
            set de=KKRX_fim
        elseif KKRX_fim>=KKRX_n then
            set de=KKRX_n+1
        else
            set de=KKRX_Depois(KKRX_fim)
        endif
        exitwhen k>=idx
        set k=k+1
    endloop
    set KKRX_prox=de
    return SubString(KKRX_str, p, KKRX_fim)
endfunction

function KKRX_Vaga takes string str,string pat,integer idx returns integer
    local integer h=StringHash(str)/2+StringHash(pat)/4+idx*131
    set h=h-(h/1024)*1024
    if h<0 then
        set h=h+1024
    endif
    return h
endfunction

function KKRX_Meta takes string k,boolean kv returns boolean
    local integer i=0
    local integer n=StringLength(k)
    local string c
    loop
        exitwhen i>=n
        set c=SubString(k, i, i+1)
        if c=="\\" or c=="[" or c=="]" or c=="(" or c==")" or c=="{" or c=="}" or c=="." or c=="*" or c=="+" or c=="?" or c=="^" or c=="$" or c=="|" then
            return true
        endif
        if kv and (c=="," or c==":" or c=="\n") then
            return true
        endif
        set i=i+1
    endloop
    return false
endfunction

function KKRX_Dic takes string str returns integer
    local integer slot=StringHash(str)
    local integer i=0
    local integer n=StringLength(str)
    local integer e
    local integer c
    local integer h
    local string k
    set slot=slot-(slot/512)*512
    if slot<0 then
        set slot=slot+512
    endif
    if KKRX_dv[slot] and KKRX_dt[slot]==str then
        return slot
    endif
    call FlushChildHashtable(KKRX_dic, slot)
    call FlushChildHashtable(KKRX_dic, slot+512)
    loop
        exitwhen i>n
        set e=KKJN_PosB(str, ",", i)
        if e<0 then
            set e=n
        endif
        set c=KKJN_PosB(str, ":", i)
        if c>=0 and c<e then
            set k=SubString(str, i, c)
            set h=StringHash(k)
            if not HaveSavedString(KKRX_dic, slot, h) then
                call SaveStr(KKRX_dic, slot, h, k)
                call SaveStr(KKRX_dic, slot+512, h, SubString(str, c+1, e))
            elseif LoadStr(KKRX_dic, slot, h)!=k then
                call SaveBoolean(KKRX_dic, slot, h, true)
            endif
        endif
        set i=e+1
    endloop
    set KKRX_dt[slot]=str
    set KKRX_dv[slot]=true
    return slot
endfunction

function KKRX_Chave takes string str,string pat returns string
    local integer n=StringLength(pat)
    local integer tipo=0
    local integer slot
    local integer h
    local string c
    local string k
    local string v
    set KKRX_rv=-1
    if n<24 then
        return ""
    endif
    set c=SubString(pat, 0, 9)
    if c!="(?<=(,|^)" and c!="(?<=(^|,)" then
        return ""
    endif
    set c=SubString(pat, n-14, n)
    if c==":)(.*?)(?=,|$)" or c==":)(.*?)(?=$|,)" then
        set tipo=1
        set k=SubString(pat, 9, n-14)
    else
        set c=SubString(pat, n-17, n)
        if c==":)([^:,]*)(?=$|,)" or c==":)([^:,]*)(?=,|$)" then
            set tipo=2
            set k=SubString(pat, 9, n-17)
        else
            return ""
        endif
    endif
    if k=="" or KKRX_Meta(k, true) then
        return ""
    endif
    if StringLength(str)>0 and SubString(str, StringLength(str)-1, StringLength(str))=="\n" then
        return ""
    endif
    set slot=KKRX_Dic(str)
    set h=StringHash(k)
    if not HaveSavedString(KKRX_dic, slot, h) then
        set KKRX_rv=1
        return ""
    endif
    if LoadStr(KKRX_dic, slot, h)!=k or LoadBoolean(KKRX_dic, slot, h) then
        return ""
    endif
    set v=LoadStr(KKRX_dic, slot+512, h)
    if KKJN_PosB(v, "\n", 0)>=0 or (tipo==2 and KKJN_PosB(v, ":", 0)>=0) then
        return ""
    endif
    set KKRX_rv=1
    return v
endfunction

function KKRX_Regex takes string str,string pat,integer idx returns string
    local integer v
    local integer w
    local integer de=0
    local integer k=0
    local string r
    if str==null or pat==null or idx<0 then
        return ""
    endif
    if idx==0 and KKRX_dic!=null then
        set r=KKRX_Chave(str, pat)
        if KKRX_rv>0 then
            return r
        endif
    endif
    set v=KKRX_Vaga(str, pat, idx)
    if KKRX_mv[v] and KKRX_mi[v]==idx and KKRX_mt[v]==str and KKRX_mp[v]==pat then
        return KKRX_mr[v]
    endif
    if idx>0 then
        set w=KKRX_Vaga(str, pat, idx-1)
        if KKRX_mv[w] and KKRX_mi[w]==idx-1 and KKRX_mt[w]==str and KKRX_mp[w]==pat then
            if KKRX_me[w]<0 then
                return ""
            endif
            set de=KKRX_me[w]
            set k=idx
        endif
    endif
    if not KKRX_Compila(pat) then
        return ""
    endif
    set KKRX_str=str
    set KKRX_n=StringLength(str)
    set KKRX_passos=0
    set KKRX_estouro=false
    set KKRX_sp=0
    set r=KKRX_Enesimo(de, idx-k)
    if KKRX_estouro then
        return ""
    endif
    set KKRX_mv[v]=true
    set KKRX_mt[v]=str
    set KKRX_mp[v]=pat
    set KKRX_mi[v]=idx
    set KKRX_mr[v]=r
    set KKRX_me[v]=KKRX_prox
    return r
endfunction

function KKRX_Conta takes string str,string pat returns boolean
    local integer v=KKRX_Vaga(str, pat, -7)
    local integer de=0
    local integer c=0
    if KKRX_mv[v] and KKRX_mi[v]==-7 and KKRX_mt[v]==str and KKRX_mp[v]==pat then
        set KKRX_rc=S2I(KKRX_mr[v])
        return true
    endif
    if not KKRX_Compila(pat) then
        return false
    endif
    set KKRX_str=str
    set KKRX_n=StringLength(str)
    set KKRX_passos=0
    set KKRX_estouro=false
    set KKRX_sp=0
    loop
        exitwhen de>KKRX_n
        call KKRX_Enesimo(de, 0)
        exitwhen KKRX_prox<0
        set c=c+1
        set de=KKRX_prox
    endloop
    if KKRX_estouro then
        return false
    endif
    set KKRX_mv[v]=true
    set KKRX_mt[v]=str
    set KKRX_mp[v]=pat
    set KKRX_mi[v]=-7
    set KKRX_mr[v]=I2S(c)
    set KKRX_me[v]=0
    set KKRX_rc=c
    return true
endfunction

//{{KK_FIMSE:KK_JN_REGEX}}
function JNStringContains takes string str,string sub returns boolean
    if str==null or sub==null then
        return false
    endif
    return KKJN_PosB(str, sub, 0)>=0
endfunction

function JNStringCount takes string str,string sub returns integer
    local integer m
    local integer i=0
    local integer c=0
    local integer p
    if str==null or sub==null then
        return 0
    endif
    //{{KK_SE:KK_JN_REGEX}}
    if KKRX_Meta(sub, false) and KKRX_Conta(str, sub) then
        return KKRX_rc
    endif
    //{{KK_FIMSE:KK_JN_REGEX}}
    set m=StringLength(sub)
    if m<=0 then
        return 0
    endif
    loop
        set p=KKJN_PosB(str, sub, i)
        exitwhen p<0
        set c=c+1
        set i=p+m
    endloop
    return c
endfunction

function JNStringReverse takes string str returns string
    local integer i
    local string r=""
    if str==null then
        return ""
    endif
    set i=KKJN_CharLen(str)-1
    loop
        exitwhen i<0
        set r=r+JNStringSub(str, i, 1)
        set i=i-1
    endloop
    return r
endfunction

function JNStringTrimStart takes string str returns string
    local integer n
    local integer i=0
    local string b
    if str==null then
        return ""
    endif
    set n=StringLength(str)
    loop
        exitwhen i>=n
        set b=SubString(str, i, i+1)
        if b==" " or b=="\t" or b=="\r" or b=="\n" then
            set i=i+1
        elseif SubString(str, i, i+2)==KKJN_NBSP then
            set i=i+2
        elseif SubString(str, i, i+3)==KKJN_ESP_CJK then
            set i=i+3
        else
            exitwhen true
        endif
    endloop
    return SubString(str, i, n)
endfunction

function JNStringTrimEnd takes string str returns string
    local integer i
    local string b
    if str==null then
        return ""
    endif
    set i=StringLength(str)
    loop
        exitwhen i<=0
        set b=SubString(str, i-1, i)
        if b==" " or b=="\t" or b=="\r" or b=="\n" then
            set i=i-1
        elseif i>=2 and SubString(str, i-2, i)==KKJN_NBSP then
            set i=i-2
        elseif i>=3 and SubString(str, i-3, i)==KKJN_ESP_CJK then
            set i=i-3
        else
            exitwhen true
        endif
    endloop
    return SubString(str, 0, i)
endfunction

function JNStringTrim takes string str returns string
    return JNStringTrimEnd(JNStringTrimStart(str))
endfunction

function JNStringInsert takes string str,integer index,string val returns string
    local integer n
    local integer b
    if str==null then
        set str=""
    endif
    if val==null then
        set val=""
    endif
    set n=KKJN_CharLen(str)
    if index<0 then
        set index=0
    endif
    loop
        exitwhen n>=index
        set str=str+" "
        set n=n+1
    endloop
    set b=KKJN_CharToByte(str, index)
    return SubString(str, 0, b)+val+SubString(str, b, StringLength(str))
endfunction

function JNStringReplace takes string str,string old,string newstr returns string
    local integer n
    local integer m
    local integer i=0
    local integer p
    local string r=""
    if str==null or old==null or old=="" then
        return str
    endif
    if newstr==null then
        set newstr=""
    endif
    set n=StringLength(str)
    set m=StringLength(old)
    loop
        set p=KKJN_PosB(str, old, i)
        exitwhen p<0
        set r=r+SubString(str, i, p)+newstr
        set i=p+m
    endloop
    return r+SubString(str, i, n)
endfunction

function JNStringRegex takes string str,string regex,integer index returns string
    //{{KK_SE:KK_JN_REGEX}}
    return KKRX_Regex(str, regex, index)
    //{{KK_FIMSE:KK_JN_REGEX}}
    return ""
endfunction

function KKJN_EhHex takes string c returns boolean
    local integer i=0
    if StringLength(c)!=1 then
        return false
    endif
    loop
        exitwhen i>=22
        if SubString("0123456789abcdefABCDEF", i, i+1)==c then
            return true
        endif
        set i=i+1
    endloop
    return false
endfunction

function JNStringCalcLines takes string str,integer length returns integer
    local integer n
    local integer i=0
    local integer j
    local integer k
    local integer linhas=1
    local integer linha=0
    local integer pal=0
    local string c
    local string d
    local boolean mede
    if str==null or length<=0 then
        return 0
    endif
    set str=JNStringTrimEnd(str)
    set n=StringLength(str)
    loop
        exitwhen i>=n
        set c=SubString(str, i, i+1)
        set j=i+1
        loop
            exitwhen j>=n or not KKJN_IsCont(SubString(str, j, j+1))
            set j=j+1
        endloop
        if c==" " then
            set pal=pal+1
            set linha=linha+pal
            set pal=0
            set i=j
        elseif j-i==1 and (c=="\n" or c=="\r" or c=="|") then
            set d=SubString(str, j, j+1)
            set mede=false
            if c=="\n" then
                set linha=0
                set pal=0
                set linhas=linhas+1
                if j>=n or d==" " then
                    set pal=pal+1
                endif
            elseif c=="\r" then
                set mede=false
            elseif d=="c" or d=="C" then
                set k=0
                loop
                    exitwhen k>=8 or not KKJN_EhHex(SubString(str, j+1+k, j+2+k))
                    set k=k+1
                endloop
                if k>=8 then
                    set j=j+9
                else
                    set pal=pal+1
                    set mede=true
                endif
            elseif d=="r" or d=="R" then
                set j=j+1
            elseif d=="n" or d=="N" then
                set j=j+1
                set linha=0
                set pal=0
                set linhas=linhas+1
                if j>=n or SubString(str, j, j+1)==" " then
                    set pal=pal+1
                endif
            else
                set pal=pal+1
                set mede=true
            endif
            if mede then
                if pal>=length then
                    set pal=0
                    set linhas=linhas+1
                elseif linha>0 and pal+linha+1>=length then
                    set linha=0
                    set linhas=linhas+1
                endif
            endif
            set i=j
        else
            if j-i==1 or (j-i==2 and HaveSavedBoolean(KKJN_cont, 2, StringHash(SubString(str, i, j)))) then
                set pal=pal+1
            else
                set pal=pal+2
            endif
            if pal>=length then
                set pal=0
                set linhas=linhas+1
            elseif linha>0 and pal+linha+1>=length then
                set linha=0
                set linhas=linhas+1
            endif
            set i=j
        endif
    endloop
    return linhas
endfunction

function KKJN_B64Char takes integer v returns string
    return SubString(KKJN_B64, v, v+1)
endfunction

function KKJN_B64Val takes string ch returns integer
    local integer k=DB_ord(ch)
    if k<0 then
        return -1
    endif
    return KKJN_b64i[k]-1
endfunction

function JNStringToBase64 takes string str returns string
    local integer n
    local integer i=0
    local integer a
    local integer b
    local integer c
    local string r=""
    if str==null or str=="" then
        return ""
    endif
    set n=StringLength(str)
    loop
        exitwhen i>=n
        set a=DB_ord(SubString(str, i, i+1))
        set b=-1
        set c=-1
        if i+1<n then
            set b=DB_ord(SubString(str, i+1, i+2))
            if b<0 then
                return str
            endif
        endif
        if i+2<n then
            set c=DB_ord(SubString(str, i+2, i+3))
            if c<0 then
                return str
            endif
        endif
        if a<0 then
            return str
        endif
        set r=r+KKJN_B64Char(a/4)
        if b<0 then
            set r=r+KKJN_B64Char(ModuloInteger(a, 4)*16)+"=="
        elseif c<0 then
            set r=r+KKJN_B64Char(ModuloInteger(a, 4)*16+b/16)+KKJN_B64Char(ModuloInteger(b, 16)*4)+"="
        else
            set r=r+KKJN_B64Char(ModuloInteger(a, 4)*16+b/16)+KKJN_B64Char(ModuloInteger(b, 16)*4+c/64)+KKJN_B64Char(ModuloInteger(c, 64))
        endif
        set i=i+3
    endloop
    return r
endfunction

function JNStringFromBase64 takes string str returns string
    local integer n
    local integer i=0
    local integer a
    local integer b
    local integer c
    local integer d
    local integer v
    local string r=""
    if str==null or str=="" then
        return ""
    endif
    set n=StringLength(str)
    if ModuloInteger(n, 4)!=0 then
        return str
    endif
    loop
        exitwhen i>=n
        set a=KKJN_B64Val(SubString(str, i, i+1))
        set b=KKJN_B64Val(SubString(str, i+1, i+2))
        set c=-2
        set d=-2
        if SubString(str, i+2, i+3)!="=" then
            set c=KKJN_B64Val(SubString(str, i+2, i+3))
        endif
        if SubString(str, i+3, i+4)!="=" then
            set d=KKJN_B64Val(SubString(str, i+3, i+4))
        endif
        if a<0 or b<0 or c==-1 or d==-1 or (c==-2 and d!=-2) or ((c==-2 or d==-2) and i+4<n) then
            return str
        endif
        set v=a*4+b/16
        if v<32 or v>126 then
            return str
        endif
        set r=r+DB_CHR[v]
        if c>=0 then
            set v=ModuloInteger(b, 16)*16+c/4
            if v<32 or v>126 then
                return str
            endif
            set r=r+DB_CHR[v]
            if d>=0 then
                set v=ModuloInteger(c, 4)*64+d
                if v<32 or v>126 then
                    return str
                endif
                set r=r+DB_CHR[v]
            endif
        endif
        set i=i+4
    endloop
    return r
endfunction

function JNUse takes nothing returns boolean
    return {{KK_JN_USE}}
endfunction

function JNGetConnectionState takes nothing returns integer
    return {{KK_JN_CONEXAO}}
endfunction

function IsHostPlayer takes nothing returns boolean
    return {{KK_JN_HOST}}
endfunction

function JNOpenBrowser takes string Address returns nothing
    if Address!=null and Address!="" then
        call DisplayTimedTextToPlayer(GetLocalPlayer(), 0.0, 0.0, 30.0, Address)
    endif
endfunction

function JNI2R takes integer i returns real
    local boolean neg=i<0
    local integer e
    local integer m
    local real v
    if i==0 or i==-2147483647-1 then
        return 0.0
    endif
    if neg then
        set i=i+2147483647+1
    endif
    set e=i/8388608
    set m=i-e*8388608
    if e==0 then
        set v=I2R(m)
        set e=-149
    else
        set v=1.0+I2R(m)/8388608.0
        set e=e-127
    endif
    loop
        exitwhen e<=0
        set v=v*2.0
        set e=e-1
    endloop
    loop
        exitwhen e>=0
        set v=v*0.5
        set e=e+1
    endloop
    if neg then
        return -v
    endif
    return v
endfunction

function JNR2I takes real r returns integer
    local integer e=127
    local integer m
    local real a=r
    if r==0.0 then
        return 0
    endif
    if r<0.0 then
        set a=-r
    endif
    loop
        exitwhen a<2.0 or e>=254
        set a=a*0.5
        set e=e+1
    endloop
    loop
        exitwhen a>=1.0 or e<=1
        set a=a*2.0
        set e=e-1
    endloop
    if a<1.0 then
        set m=R2I(a*8388608.0)
        set e=0
    else
        set m=R2I((a-1.0)*8388608.0)
    endif
    if r<0.0 then
        return e*8388608+m-2147483647-1
    endif
    return e*8388608+m
endfunction

function JNGetModuleHandle takes string moduleName returns integer
    return 0
endfunction

function JNFindModuleHandle takes integer offset,integer signature returns integer
    return 0
endfunction

function JNMemoryGetByte takes integer offset returns integer
    return 0
endfunction

function JNMemorySetByte takes integer offset,integer value returns nothing
endfunction

function JNMemoryGetInteger takes integer offset returns integer
    return 0
endfunction

function JNMemorySetInteger takes integer offset,integer value returns nothing
endfunction

function JNMemoryGetReal takes integer offset returns real
    return 0.0
endfunction

function JNMemorySetReal takes integer offset,real value returns nothing
endfunction

function JNMemoryGetString takes integer offset,integer length returns string
    return ""
endfunction

function JNMemorySetString takes integer offset,string value returns nothing
endfunction

function JNProcCall takes integer callConv,integer address,hashtable params returns boolean
    return false
endfunction

function JNGetMaxAttackSpeed takes nothing returns real
    return KKJN_vel_ataque
endfunction

function JNSetMaxAttackSpeed takes real speed returns nothing
    set KKJN_vel_ataque=speed
endfunction

function JNSetLog takes string MapId,string UserId,string SecretKey,string Character,string Version,string Loging returns string
    return ""
endfunction

function JNSetLogUseType takes string MapId,string UserId,string SecretKey,string Character,string Version,string Loging,string LogType returns string
    return ""
endfunction

function JNMapServerLog takes string MapId,string SecretKey,string Version,string Loging returns string
    return ""
endfunction

function JNMapServerLogUseType takes string MapId,string SecretKey,string Version,string Loging,string LogType returns string
    return ""
endfunction

function JNPublicMapServerLog takes string MapId,string SecretKey,string Version,string Loging returns string
    return ""
endfunction

function JNWriteLog takes string str returns nothing
endfunction

function JNWriteLogReal takes real r returns nothing
endfunction

function JNGetLocalDateTime takes nothing returns string
    return ""
endfunction

function JNGetLocalUnixTime takes nothing returns integer
    return 0
endfunction

function JNServerTime takes string Format returns string
    return ""
endfunction

function JNServerUnixTime takes nothing returns integer
    return 0
endfunction

function JNGetSyncDelay takes nothing returns integer
    return KKJN_atraso
endfunction

function JNSetSyncDelay takes integer delay returns nothing
    if delay<=10 then
        set KKJN_atraso=10
    elseif delay>=550 then
        set KKJN_atraso=550
    else
        set KKJN_atraso=delay
    endif
endfunction

function JNProcessStart takes string fileName,string arguments returns boolean
    return false
endfunction

function JNServerPluginVersion takes nothing returns integer
    //{{KK_SE:KK_JN_PLUGIN}}
    return {{KK_JN_PLUGIN_VER}}
    //{{KK_FIMSE:KK_JN_PLUGIN}}
    return 0
endfunction

function JNCheckNameHack takes string UserId returns boolean
    return false
endfunction

function JNPushReg takes string MapId returns nothing
endfunction

function JNGetPushMessage takes nothing returns string
    return ""
endfunction

function JNReplayReg takes string MapId,string SecretKey,string UserId,string Character,string Loging returns nothing
endfunction

function JNScreenShotReg takes string MapId,string SecretKey,string UserId,string Character,string Loging returns boolean
    return false
endfunction

function JNPublicScreenShotReg takes string MapId,string SecretKey,string UserId,string Character,string Tag,string Loging returns boolean
    return false
endfunction

function JNUseUserRoleItemInfo takes string MapId,string SecretKey,string UserId,string ItemName returns string
    return ""
endfunction

function JNSetSaveCode takes string MapId,string UserId,string SecretKey,string Character,string Code returns string
    return ""
endfunction

function JNGetLoadCode takes string MapId,string UserId,string SecretKey,string Character returns string
    return ""
endfunction
