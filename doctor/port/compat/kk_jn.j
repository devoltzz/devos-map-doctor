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
//{{KK_SE:KK_JN_BASE}}
constant string KKJN_BASE="{{KK_JN_BASE_CAMPOS}}"
integer KKJN_nbase=0
//{{KK_FIMSE:KK_JN_BASE}}
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
        exitwhen i>=64
        set KKJN_b64i[DB_ord(SubString(KKJN_B64, i, i+1))]=i+1
        set i=i+1
    endloop
    call KKJN_Sonda()
    //{{KK_SE:KK_JN_BASE}}
    call KKJN_BaseLe()
    //{{KK_FIMSE:KK_JN_BASE}}
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
    return 1
endfunction

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
    local integer b1
    if str==null or length<=0 then
        return ""
    endif
    if start<0 then
        set start=0
    endif
    set b0=KKJN_CharToByte(str, start)
    set b1=KKJN_CharToByte(str, start+length)
    if b1<=b0 then
        return ""
    endif
    return SubString(str, b0, b1)
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
        exitwhen b!=" " and b!="\t" and b!="\r" and b!="\n"
        set i=i+1
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
        exitwhen b!=" " and b!="\t" and b!="\r" and b!="\n"
        set i=i-1
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
    elseif index>n then
        set index=n
    endif
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
    return ""
endfunction

function JNStringCalcLines takes string str,integer length returns integer
    if str==null or length<=0 then
        return 1
    endif
    return 1+(KKJN_CharLen(str)/length)
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
    return I2R(i)
endfunction

function JNR2I takes real r returns integer
    return R2I(r)
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
    return 0.0
endfunction

function JNSetMaxAttackSpeed takes real speed returns nothing
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
    return 0
endfunction

function JNSetSyncDelay takes integer delay returns nothing
endfunction

function JNProcessStart takes string fileName,string arguments returns boolean
    return false
endfunction

function JNServerPluginVersion takes nothing returns integer
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
