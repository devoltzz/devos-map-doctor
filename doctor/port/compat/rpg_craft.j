//@GLOBALS
constant integer RPGK_MAXR=1024
constant integer RPGK_MAXI=8
constant integer RPGK_T_MAT=1
constant integer RPGK_T_ITEM=2
constant integer RPGK_T_CAT=3
constant integer RPGK_G_FEITO=1
constant integer RPGK_G_REFINO=2
integer RPGK_jogadores=12
integer RPGK_ron=0
integer RPGK_ref_max=10
integer array RPGK_ref_ron
real array RPGK_ref_ouro
real array RPGK_ref_ch
real RPGK_ref_pity=0.10
integer array RPGK_preco
real RPGK_ferreiro_raio=600.0
boolean RPGK_avisa=true
unit array RPGK_heroi
hashtable RPGK_ht=null
trigger array RPGK_tg
boolean array RPGK_tem
trigger RPGK_t_sync=null
group RPGK_ferreiros=null
integer RPGK_n=0
integer array RPGK_r_res
integer array RPGK_r_ouro
integer array RPGK_r_n
integer array RPGK_i_tipo
integer array RPGK_i_id
integer array RPGK_i_n
string RPGK_falta=""
integer RPGK_ev_pid=0
item RPGK_ev_item=null
integer RPGK_ev_r=0
boolean RPGK_ev_ok=false
integer RPGK_ev_nivel=0
boolean RPGK_tmp_ok=false
unit RPGK_tmp_u=null
//@ENDGLOBALS

function RPGK_gancho takes integer qual, code f returns nothing
    if qual<1 or qual>8 then
        return
    endif
    call TriggerAddCondition(RPGK_tg[qual], Condition(f))
    set RPGK_tem[qual]=true
endfunction

function RPGK_chama takes integer qual returns nothing
    if qual>=1 and qual<=8 and RPGK_tem[qual] then
        call TriggerEvaluate(RPGK_tg[qual])
    endif
endfunction

function RPGK_receita takes integer resultado, integer ouro returns integer
    if RPGK_n>=RPGK_MAXR-1 then
        return 0
    endif
    set RPGK_n=RPGK_n+1
    set RPGK_r_res[RPGK_n]=resultado
    set RPGK_r_ouro[RPGK_n]=ouro
    set RPGK_r_n[RPGK_n]=0
    if not HaveSavedInteger(RPGK_ht, 1, resultado) then
        call SaveInteger(RPGK_ht, 1, resultado, RPGK_n)
    endif
    return RPGK_n
endfunction

function RPGK_ingr takes integer r, integer tipo, integer id, integer n returns nothing
    local integer k
    if r<1 or r>RPGK_n or RPGK_r_n[r]>=RPGK_MAXI then
        return
    endif
    set k=r*RPGK_MAXI+RPGK_r_n[r]
    set RPGK_i_tipo[k]=tipo
    set RPGK_i_id[k]=id
    set RPGK_i_n[k]=n
    set RPGK_r_n[r]=RPGK_r_n[r]+1
endfunction

function RPGK_mat takes integer r, integer id, integer n returns nothing
    call RPGK_ingr(r, RPGK_T_MAT, id, n)
endfunction

function RPGK_item takes integer r, integer id, integer n returns nothing
    call RPGK_ingr(r, RPGK_T_ITEM, id, n)
endfunction

function RPGK_cat takes integer r, integer cat, integer n returns nothing
    call RPGK_ingr(r, RPGK_T_CAT, cat, n)
endfunction

function RPGK_de takes integer resultado returns integer
    return LoadInteger(RPGK_ht, 1, resultado)
endfunction

function RPGK_categoria takes integer id, integer cat returns nothing
    call SaveInteger(RPGK_ht, 2, id, cat)
endfunction

function RPGK_cat_de takes integer id returns integer
    return LoadInteger(RPGK_ht, 2, id)
endfunction

function RPGK_grau takes integer id, integer g returns nothing
    call SaveInteger(RPGK_ht, 3, id, g)
endfunction

function RPGK_grau_de takes integer id returns integer
    local integer g=LoadInteger(RPGK_ht, 3, id)
    if g<1 then
        return 1
    endif
    return g
endfunction

function RPGK_conta_inv takes unit h, integer tipo, integer id returns integer
    local integer s=0
    local integer n=0
    local item it
    loop
        exitwhen s>=UnitInventorySize(h)
        set it=UnitItemInSlot(h, s)
        if it!=null then
            if (tipo==RPGK_T_ITEM and GetItemTypeId(it)==id) or (tipo==RPGK_T_CAT and RPGK_cat_de(GetItemTypeId(it))==id) then
                set n=n+1
            endif
        endif
        set s=s+1
    endloop
    set it=null
    return n
endfunction

function RPGK_nivel takes item it returns integer
    if it==null then
        return 0
    endif
    return LoadInteger(RPGK_ht, GetHandleId(it), 10)
endfunction

function RPGK_poe_nivel takes item it, integer n returns nothing
    call SaveInteger(RPGK_ht, GetHandleId(it), 10, n)
endfunction

function RPGK_tira_inv takes unit h, integer tipo, integer id, integer n returns integer
    local integer s=0
    local integer maior=0
    local item it
    loop
        exitwhen s>=UnitInventorySize(h) or n<=0
        set it=UnitItemInSlot(h, s)
        if it!=null then
            if (tipo==RPGK_T_ITEM and GetItemTypeId(it)==id) or (tipo==RPGK_T_CAT and RPGK_cat_de(GetItemTypeId(it))==id) then
                if RPGK_nivel(it)>maior then
                    set maior=RPGK_nivel(it)
                endif
                call FlushChildHashtable(RPGK_ht, GetHandleId(it))
                call RemoveItem(it)
                set n=n-1
            endif
        endif
        set s=s+1
    endloop
    set it=null
    return maior
endfunction

function RPGK_pode takes integer pid, unit h, integer r returns boolean
    local integer k=0
    local integer b
    local integer t
    local integer tem
    local boolean ok=true
    set RPGK_falta=""
    if r<1 or r>RPGK_n or h==null then
        set RPGK_falta="no recipe"
        return false
    endif
    loop
        exitwhen k>=RPGK_r_n[r]
        set b=r*RPGK_MAXI+k
        set t=RPGK_i_tipo[b]
        if t==RPGK_T_MAT then
            set tem=RPGM_qtd(pid, RPGK_i_id[b])
        else
            set tem=RPGK_conta_inv(h, t, RPGK_i_id[b])
        endif
        if tem<RPGK_i_n[b] then
            set ok=false
            if t==RPGK_T_CAT then
                set RPGK_falta=RPGK_falta+I2S(RPGK_i_n[b]-tem)+"x item of category "+I2S(RPGK_i_id[b])+"; "
            else
                set RPGK_falta=RPGK_falta+I2S(RPGK_i_n[b]-tem)+"x "+GetObjectName(RPGK_i_id[b])+"; "
            endif
        endif
        set k=k+1
    endloop
    if GetPlayerState(Player(pid), PLAYER_STATE_RESOURCE_GOLD)<RPGK_r_ouro[r] then
        set ok=false
        set RPGK_falta=RPGK_falta+I2S(RPGK_r_ouro[r]-GetPlayerState(Player(pid), PLAYER_STATE_RESOURCE_GOLD))+" gold; "
    endif
    return ok
endfunction

function RPGK_faz takes integer pid, unit h, integer r returns item
    local integer k=0
    local integer b
    local integer heranca=0
    local integer x
    local item novo
    if not RPGK_pode(pid, h, r) then
        if RPGK_avisa then
            call DisplayTimedTextToPlayer(Player(pid), 0, 0, 5.0, "|cffff8080Missing:|r "+RPGK_falta)
        endif
        return null
    endif
    loop
        exitwhen k>=RPGK_r_n[r]
        set b=r*RPGK_MAXI+k
        if RPGK_i_tipo[b]==RPGK_T_MAT then
            call RPGM_tira(pid, RPGK_i_id[b], RPGK_i_n[b])
        else
            set x=RPGK_tira_inv(h, RPGK_i_tipo[b], RPGK_i_id[b], RPGK_i_n[b])
            if RPGK_i_tipo[b]==RPGK_T_CAT and x>heranca then
                set heranca=x
            endif
        endif
        set k=k+1
    endloop
    call SetPlayerState(Player(pid), PLAYER_STATE_RESOURCE_GOLD, GetPlayerState(Player(pid), PLAYER_STATE_RESOURCE_GOLD)-RPGK_r_ouro[r])
    set novo=CreateItem(RPGK_r_res[r], GetUnitX(h), GetUnitY(h))
    call UnitAddItem(h, novo)
    call RPGK_poe_nivel(novo, heranca/2)
    set RPGK_ev_pid=pid
    set RPGK_ev_item=novo
    set RPGK_ev_r=r
    call RPGK_chama(RPGK_G_FEITO)
    if RPGK_avisa then
        call DisplayTimedTextToPlayer(Player(pid), 0, 0, 5.0, "|cff80ff80Crafted:|r "+GetItemName(novo))
    endif
    set bj_lastCreatedItem=novo
    set novo=null
    return bj_lastCreatedItem
endfunction

function RPGK_ferreiro takes unit u returns nothing
    call GroupAddUnit(RPGK_ferreiros, u)
endfunction

function RPGK_perto_cada takes nothing returns nothing
    local real dx=GetUnitX(GetEnumUnit())-GetUnitX(RPGK_tmp_u)
    local real dy=GetUnitY(GetEnumUnit())-GetUnitY(RPGK_tmp_u)
    if dx*dx+dy*dy<=RPGK_ferreiro_raio*RPGK_ferreiro_raio then
        set RPGK_tmp_ok=true
    endif
endfunction

function RPGK_no_ferreiro takes unit h returns boolean
    set RPGK_tmp_ok=false
    set RPGK_tmp_u=h
    call ForGroup(RPGK_ferreiros, function RPGK_perto_cada)
    return RPGK_tmp_ok
endfunction

function RPGK_refina takes integer pid, unit h, item it returns integer
    local integer n
    local integer g
    local integer ron
    local integer ouro
    local integer falhas
    local real ch
    local integer hi
    set RPGK_falta=""
    if it==null or h==null then
        set RPGK_falta="no item"
        return -1
    endif
    if not RPGK_no_ferreiro(h) then
        set RPGK_falta="only at the blacksmith"
        return -1
    endif
    set hi=GetHandleId(it)
    set n=RPGK_nivel(it)+1
    if n>RPGK_ref_max then
        set RPGK_falta="already at the maximum"
        return -1
    endif
    set g=RPGK_grau_de(GetItemTypeId(it))
    set ron=RPGK_ref_ron[n]*g
    set ouro=R2I(RPGK_ref_ouro[n]*I2R(RPGK_preco[g]))
    if RPGM_qtd(pid, RPGK_ron)<ron then
        set RPGK_falta=I2S(ron-RPGM_qtd(pid, RPGK_ron))+"x "+GetObjectName(RPGK_ron)
        return -1
    endif
    if GetPlayerState(Player(pid), PLAYER_STATE_RESOURCE_GOLD)<ouro then
        set RPGK_falta=I2S(ouro-GetPlayerState(Player(pid), PLAYER_STATE_RESOURCE_GOLD))+" gold"
        return -1
    endif
    call RPGM_tira(pid, RPGK_ron, ron)
    call SetPlayerState(Player(pid), PLAYER_STATE_RESOURCE_GOLD, GetPlayerState(Player(pid), PLAYER_STATE_RESOURCE_GOLD)-ouro)
    set falhas=LoadInteger(RPGK_ht, hi, 11)
    set ch=RPGK_ref_ch[n]+RPGK_ref_pity*I2R(falhas)
    set RPGK_ev_pid=pid
    set RPGK_ev_item=it
    if GetRandomReal(0.0, 1.0)<ch then
        call RPGK_poe_nivel(it, n)
        call SaveInteger(RPGK_ht, hi, 11, 0)
        set RPGK_ev_ok=true
        set RPGK_ev_nivel=n
        call RPGK_chama(RPGK_G_REFINO)
        if RPGK_avisa then
            call DisplayTimedTextToPlayer(Player(pid), 0, 0, 5.0, "|cff80ff80Refine success:|r +"+I2S(n))
        endif
        return 1
    endif
    call SaveInteger(RPGK_ht, hi, 11, falhas+1)
    set RPGK_ev_ok=false
    set RPGK_ev_nivel=n-1
    call RPGK_chama(RPGK_G_REFINO)
    if RPGK_avisa then
        call DisplayTimedTextToPlayer(Player(pid), 0, 0, 5.0, "|cffff8080Refine failed|r (next try +"+I2S(R2I(RPGK_ref_pity*100.0+0.5))+"%)")
    endif
    return 0
endfunction

function RPGK_pede_craft takes integer r returns nothing
    call BlzSendSyncData("rpgk", "C"+I2S(r))
endfunction

function RPGK_pede_refino takes integer slot returns nothing
    call BlzSendSyncData("rpgk", "R"+I2S(slot))
endfunction

function RPGK_sync takes nothing returns nothing
    local integer pid=GetPlayerId(GetTriggerPlayer())
    local string v=BlzGetTriggerSyncData()
    local string c
    local integer x
    local item it
    if pid<0 or pid>=RPGK_jogadores or v==null or StringLength(v)<2 or RPGK_heroi[pid]==null then
        return
    endif
    set c=SubString(v, 0, 1)
    set x=S2I(SubString(v, 1, StringLength(v)))
    if c=="C" then
        call RPGK_faz(pid, RPGK_heroi[pid], x)
    elseif c=="R" and x>=0 and x<UnitInventorySize(RPGK_heroi[pid]) then
        set it=UnitItemInSlot(RPGK_heroi[pid], x)
        if RPGK_refina(pid, RPGK_heroi[pid], it)<0 and RPGK_avisa then
            call DisplayTimedTextToPlayer(Player(pid), 0, 0, 5.0, "|cffff8080Cannot refine:|r "+RPGK_falta)
        endif
    endif
    set it=null
endfunction

function RPGK_init takes nothing returns nothing
    local integer i=1
    if RPGK_ht!=null then
        return
    endif
    set RPGK_ht=InitHashtable()
    set RPGK_ferreiros=CreateGroup()
    loop
        exitwhen i>8
        set RPGK_tg[i]=CreateTrigger()
        set i=i+1
    endloop
    set RPGK_t_sync=CreateTrigger()
    set i=0
    loop
        exitwhen i>=RPGK_jogadores
        call BlzTriggerRegisterPlayerSyncEvent(RPGK_t_sync, Player(i), "rpgk", false)
        set i=i+1
    endloop
    call TriggerAddAction(RPGK_t_sync, function RPGK_sync)
endfunction
