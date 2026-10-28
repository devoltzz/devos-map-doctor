//@GLOBALS
constant integer RPGS_TRECHO=170
constant integer RPGS_MAXP=24
constant integer RPGS_PACOTE=200
constant integer RPGS_G_GRAVA=1
constant integer RPGS_G_CARREGA=2
string RPGS_pasta="RPGSave\\"
string RPGS_abil_txt="'Amls'"
integer RPGS_abil='Amls'
string RPGS_sal="rpg"
integer RPGS_jogadores=12
real RPGS_auto=0.0
boolean RPGS_avisa=true
hashtable RPGS_ht=null
trigger array RPGS_tg
boolean array RPGS_tem_g
trigger RPGS_t_sync=null
timer RPGS_tm=null
integer RPGS_nslots=0
integer array RPGS_slot
string array RPGS_orig
string RPGS_w=""
string array RPGS_buf
string array RPGS_nome
integer array RPGS_estado
integer RPGS_ev_pid=0
boolean RPGS_ev_ok=false
//@ENDGLOBALS

function RPGS_gancho takes integer qual, code f returns nothing
    if qual<1 or qual>8 then
        return
    endif
    call TriggerAddCondition(RPGS_tg[qual], Condition(f))
    set RPGS_tem_g[qual]=true
endfunction

function RPGS_chama takes integer qual, integer pid returns nothing
    if qual>=1 and qual<=8 and RPGS_tem_g[qual] then
        set RPGS_ev_pid=pid
        call TriggerEvaluate(RPGS_tg[qual])
    endif
endfunction

function RPGS_esc takes string s returns string
    local integer i=0
    local integer n=StringLength(s)
    local string r=""
    local string c
    loop
        exitwhen i>=n
        set c=SubString(s, i, i+1)
        if c=="~" then
            set r=r+"~t"
        elseif c=="\\" then
            set r=r+"~b"
        elseif c=="\"" then
            set r=r+"~q"
        elseif c==";" then
            set r=r+"~s"
        elseif c=="=" then
            set r=r+"~e"
        elseif c=="\n" or c=="\r" then
            set r=r+"~n"
        else
            set r=r+c
        endif
        set i=i+1
    endloop
    return r
endfunction

function RPGS_desesc takes string s returns string
    local integer i=0
    local integer n=StringLength(s)
    local string r=""
    local string c
    loop
        exitwhen i>=n
        set c=SubString(s, i, i+1)
        if c=="~" and i+1<n then
            set c=SubString(s, i+1, i+2)
            set i=i+1
            if c=="t" then
                set r=r+"~"
            elseif c=="b" then
                set r=r+"\\"
            elseif c=="q" then
                set r=r+"\""
            elseif c=="s" then
                set r=r+";"
            elseif c=="e" then
                set r=r+"="
            elseif c=="n" then
                set r=r+"\n"
            endif
        else
            set r=r+c
        endif
        set i=i+1
    endloop
    return r
endfunction

function RPGS_poe_s takes string k, string v returns nothing
    set RPGS_w=RPGS_w+RPGS_esc(k)+"="+RPGS_esc(v)+";"
endfunction

function RPGS_poe_i takes string k, integer v returns nothing
    set RPGS_w=RPGS_w+RPGS_esc(k)+"="+I2S(v)+";"
endfunction

function RPGS_le_s takes integer pid, string k returns string
    local string v=LoadStr(RPGS_ht, pid, StringHash(k))
    if v==null then
        return ""
    endif
    return v
endfunction

function RPGS_le_i takes integer pid, string k returns integer
    return S2I(RPGS_le_s(pid, k))
endfunction

function RPGS_tem takes integer pid, string k returns boolean
    return HaveSavedString(RPGS_ht, pid, StringHash(k))
endfunction

function RPGS_separa takes integer pid, string s returns nothing
    local integer i=0
    local integer n=StringLength(s)
    local integer ini=0
    local integer eq=-1
    local string c
    call FlushChildHashtable(RPGS_ht, pid)
    loop
        exitwhen i>=n
        set c=SubString(s, i, i+1)
        if c=="=" and eq<0 then
            set eq=i
        elseif c==";" then
            if eq>ini then
                call SaveStr(RPGS_ht, pid, StringHash(RPGS_desesc(SubString(s, ini, eq))), RPGS_desesc(SubString(s, eq+1, i)))
            endif
            set ini=i+1
            set eq=-1
        endif
        set i=i+1
    endloop
endfunction

function RPGS_tipo_get takes integer t returns string
    if t==0 then
        return BlzGetAbilityTooltip(RPGS_abil, 0)
    elseif t==1 then
        return BlzGetAbilityExtendedTooltip(RPGS_abil, 0)
    elseif t==2 then
        return BlzGetAbilityActivatedTooltip(RPGS_abil, 0)
    elseif t==3 then
        return BlzGetAbilityActivatedExtendedTooltip(RPGS_abil, 0)
    elseif t==4 then
        return BlzGetAbilityResearchTooltip(RPGS_abil, 0)
    endif
    return BlzGetAbilityResearchExtendedTooltip(RPGS_abil, 0)
endfunction

function RPGS_tipo_set takes integer t, string s returns nothing
    if s==null then
        set s=""
    endif
    if t==0 then
        call BlzSetAbilityTooltip(RPGS_abil, s, 0)
    elseif t==1 then
        call BlzSetAbilityExtendedTooltip(RPGS_abil, s, 0)
    elseif t==2 then
        call BlzSetAbilityActivatedTooltip(RPGS_abil, s, 0)
    elseif t==3 then
        call BlzSetAbilityActivatedExtendedTooltip(RPGS_abil, s, 0)
    elseif t==4 then
        call BlzSetAbilityResearchTooltip(RPGS_abil, s, 0)
    else
        call BlzSetAbilityResearchExtendedTooltip(RPGS_abil, s, 0)
    endif
endfunction

function RPGS_tipo_func takes integer t returns string
    if t==0 then
        return "BlzSetAbilityTooltip"
    elseif t==1 then
        return "BlzSetAbilityExtendedTooltip"
    elseif t==2 then
        return "BlzSetAbilityActivatedTooltip"
    elseif t==3 then
        return "BlzSetAbilityActivatedExtendedTooltip"
    elseif t==4 then
        return "BlzSetAbilityResearchTooltip"
    endif
    return "BlzSetAbilityResearchExtendedTooltip"
endfunction

function RPGS_sonda takes nothing returns nothing
    local integer t=0
    local string orig
    set RPGS_nslots=0
    loop
        exitwhen t>5
        set orig=RPGS_tipo_get(t)
        call RPGS_tipo_set(t, "@RPGS"+I2S(t))
        if RPGS_tipo_get(t)=="@RPGS"+I2S(t) then
            set RPGS_slot[RPGS_nslots]=t
            set RPGS_nslots=RPGS_nslots+1
        endif
        call RPGS_tipo_set(t, orig)
        set t=t+1
    endloop
endfunction

function RPGS_escreve takes string base, string s returns integer
    local integer parte=0
    local integer cap=RPGS_nslots*RPGS_TRECHO
    local integer partes
    local integer k
    local integer i
    local string pedaco
    set partes=(StringLength(s)+6+cap-1)/cap
    if partes<1 then
        set partes=1
    endif
    set s="#"+I2S(partes)+";"+s
    loop
        exitwhen parte>=partes
        call PreloadGenClear()
        call PreloadGenStart()
        set k=0
        loop
            exitwhen k>=RPGS_nslots
            set i=parte*cap+k*RPGS_TRECHO
            if i<StringLength(s) then
                set pedaco=SubString(s, i, IMinBJ(i+RPGS_TRECHO, StringLength(s)))
                call Preload("\")\ncall "+RPGS_tipo_func(RPGS_slot[k])+"("+RPGS_abil_txt+",\"@"+pedaco+"\",0)\n//")
            endif
            set k=k+1
        endloop
        call PreloadGenEnd(base+I2S(parte)+".pld")
        set parte=parte+1
    endloop
    return partes
endfunction

function RPGS_grava takes integer pid, string nome returns nothing
    local string s
    if pid<0 or pid>=RPGS_jogadores or RPGS_nslots<1 then
        return
    endif
    set RPGS_w=""
    call RPGS_chama(RPGS_G_GRAVA, pid)
    set s=RPGS_w+"!"+I2S(StringHash(RPGS_w+RPGS_sal))
    set RPGS_w=""
    set RPGS_nome[pid]=nome
    call SaveStr(RPGS_ht, 100+pid, StringHash(nome), s)
    if GetLocalPlayer()==Player(pid) then
        call RPGS_escreve(RPGS_pasta+nome+"_", s)
        if RPGS_avisa then
            call DisplayTimedTextToPlayer(Player(pid), 0, 0, 3.0, "|cff80ff80Saved.|r")
        endif
    endif
endfunction

function RPGS_le_disco takes string base returns string
    local integer partes=1
    local integer p=0
    local integer k
    local string tudo=""
    local string v
    local integer x
    set k=0
    loop
        exitwhen k>=RPGS_nslots
        set RPGS_orig[k]=RPGS_tipo_get(RPGS_slot[k])
        set k=k+1
    endloop
    loop
        exitwhen p>=partes
        set k=0
        loop
            exitwhen k>=RPGS_nslots
            call RPGS_tipo_set(RPGS_slot[k], "@")
            set k=k+1
        endloop
        call Preloader(base+I2S(p)+".pld")
        set k=0
        loop
            exitwhen k>=RPGS_nslots
            set v=RPGS_tipo_get(RPGS_slot[k])
            if v!=null and StringLength(v)>1 and SubString(v, 0, 1)=="@" then
                set tudo=tudo+SubString(v, 1, StringLength(v))
            endif
            set k=k+1
        endloop
        if p==0 then
            if SubString(tudo, 0, 1)!="#" then
                set tudo=""
                set partes=0
            else
                set x=1
                loop
                    exitwhen x>=StringLength(tudo) or SubString(tudo, x, x+1)==";"
                    set x=x+1
                endloop
                set partes=S2I(SubString(tudo, 1, x))
                if partes<1 or partes>RPGS_MAXP then
                    set partes=1
                endif
                set tudo=SubString(tudo, x+1, StringLength(tudo))
            endif
        endif
        set p=p+1
    endloop
    set k=0
    loop
        exitwhen k>=RPGS_nslots
        call RPGS_tipo_set(RPGS_slot[k], RPGS_orig[k])
        set k=k+1
    endloop
    return tudo
endfunction

function RPGS_confere takes string s returns string
    local integer i=StringLength(s)-1
    loop
        exitwhen i<0 or SubString(s, i, i+1)=="!"
        set i=i-1
    endloop
    if i<0 then
        return ""
    endif
    if I2S(StringHash(SubString(s, 0, i)+RPGS_sal))!=SubString(s, i+1, StringLength(s)) then
        return ""
    endif
    return SubString(s, 0, i)
endfunction

function RPGS_carrega takes integer pid, string nome returns nothing
    local string s
    local integer i
    if pid<0 or pid>=RPGS_jogadores then
        return
    endif
    set RPGS_estado[pid]=1
    set RPGS_nome[pid]=nome
    set RPGS_buf[pid]=""
    if GetLocalPlayer()==Player(pid) then
        if HaveSavedString(RPGS_ht, 100+pid, StringHash(nome)) then
            set s=RPGS_confere(LoadStr(RPGS_ht, 100+pid, StringHash(nome)))
        else
            set s=RPGS_le_disco(RPGS_pasta+nome+"_")
            call SaveStr(RPGS_ht, 100+pid, StringHash(nome), s)
            set s=RPGS_confere(s)
        endif
        call BlzSendSyncData("rpgs", "B")
        set i=0
        loop
            exitwhen i>=StringLength(s)
            call BlzSendSyncData("rpgs", "D"+SubString(s, i, IMinBJ(i+RPGS_PACOTE, StringLength(s))))
            set i=i+RPGS_PACOTE
        endloop
        if s=="" then
            call BlzSendSyncData("rpgs", "E0")
        else
            call BlzSendSyncData("rpgs", "E1")
        endif
    endif
endfunction

function RPGS_sync takes nothing returns nothing
    local integer pid=GetPlayerId(GetTriggerPlayer())
    local string v=BlzGetTriggerSyncData()
    local string c
    if pid<0 or pid>=RPGS_jogadores or v==null or StringLength(v)<1 then
        return
    endif
    set c=SubString(v, 0, 1)
    if c=="B" then
        set RPGS_buf[pid]=""
    elseif c=="D" then
        set RPGS_buf[pid]=RPGS_buf[pid]+SubString(v, 1, StringLength(v))
    elseif c=="E" then
        set RPGS_ev_ok=SubString(v, 1, 2)=="1"
        if RPGS_ev_ok then
            call RPGS_separa(pid, RPGS_buf[pid])
            set RPGS_estado[pid]=2
        else
            call FlushChildHashtable(RPGS_ht, pid)
            set RPGS_estado[pid]=3
        endif
        set RPGS_buf[pid]=""
        call RPGS_chama(RPGS_G_CARREGA, pid)
    endif
endfunction

function RPGS_poe_mochila takes integer pid returns nothing
    local integer i=0
    local integer id
    local string s=""
    loop
        exitwhen i>=RPGM_n[pid]
        set id=RPGM_id_em(pid, i)
        if RPGM_qtd(pid, id)>0 then
            set s=s+I2S(id)+":"+I2S(RPGM_qtd(pid, id))+","
        endif
        set i=i+1
    endloop
    call RPGS_poe_s("m", s)
endfunction

function RPGS_pares takes string s, integer qual, integer pid, unit h returns nothing
    local integer i=0
    local integer ini=0
    local integer dois=-1
    local integer a
    local integer b
    local item it
    loop
        exitwhen i>=StringLength(s)
        if SubString(s, i, i+1)==":" then
            set dois=i
        elseif SubString(s, i, i+1)=="," then
            if dois>ini then
                set a=S2I(SubString(s, ini, dois))
                set b=S2I(SubString(s, dois+1, i))
                if qual==1 then
                    call RPGM_soma(pid, a, b)
                elseif qual==2 and a!=0 then
                    set it=CreateItem(a, GetUnitX(h), GetUnitY(h))
                    call UnitAddItem(h, it)
                    call RPGK_poe_nivel(it, b)
                endif
            endif
            set ini=i+1
            set dois=-1
        endif
        set i=i+1
    endloop
    set it=null
endfunction

function RPGS_le_mochila takes integer pid returns nothing
    call RPGM_limpa(pid)
    call RPGS_pares(RPGS_le_s(pid, "m"), 1, pid, null)
endfunction

function RPGS_poe_inventario takes unit h returns nothing
    local integer s=0
    local item it
    local string r=""
    loop
        exitwhen s>=UnitInventorySize(h)
        set it=UnitItemInSlot(h, s)
        if it!=null and GetItemTypeId(it)!=0 then
            set r=r+I2S(GetItemTypeId(it))+":"+I2S(RPGK_nivel(it))+","
        endif
        set s=s+1
    endloop
    call RPGS_poe_s("i", r)
    set it=null
endfunction

function RPGS_le_inventario takes integer pid, unit h returns nothing
    call RPGS_pares(RPGS_le_s(pid, "i"), 2, pid, h)
endfunction

function RPGS_poe_rituais takes integer pid returns nothing
    local integer k=1
    local string s=""
    loop
        exitwhen k>RPGR_n
        if RPGR_venceu(pid, k) then
            set s=s+I2S(k)+","
        endif
        set k=k+1
    endloop
    call RPGS_poe_s("r", s)
endfunction

function RPGS_le_rituais takes integer pid returns nothing
    local string s=RPGS_le_s(pid, "r")
    local integer i=0
    local integer ini=0
    loop
        exitwhen i>=StringLength(s)
        if SubString(s, i, i+1)=="," then
            call RPGR_marca(pid, S2I(SubString(s, ini, i)), true)
            set ini=i+1
        endif
        set i=i+1
    endloop
endfunction

function RPGS_auto_tiq takes nothing returns nothing
    local integer pid=0
    loop
        exitwhen pid>=RPGS_jogadores
        if RPGS_estado[pid]==2 or RPGS_estado[pid]==3 then
            call RPGS_grava(pid, RPGS_nome[pid])
        endif
        set pid=pid+1
    endloop
endfunction

function RPGS_init takes nothing returns nothing
    local integer i=1
    if RPGS_ht!=null then
        return
    endif
    set RPGS_ht=InitHashtable()
    loop
        exitwhen i>8
        set RPGS_tg[i]=CreateTrigger()
        set i=i+1
    endloop
    call RPGS_sonda()
    set RPGS_t_sync=CreateTrigger()
    set i=0
    loop
        exitwhen i>=RPGS_jogadores
        call BlzTriggerRegisterPlayerSyncEvent(RPGS_t_sync, Player(i), "rpgs", false)
        set RPGS_estado[i]=0
        set i=i+1
    endloop
    call TriggerAddAction(RPGS_t_sync, function RPGS_sync)
    if RPGS_auto>0.0 then
        set RPGS_tm=CreateTimer()
        call TimerStart(RPGS_tm, RPGS_auto, true, function RPGS_auto_tiq)
    endif
endfunction
