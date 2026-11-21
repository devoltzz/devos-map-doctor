//@REQUER KK:kk_ui.j KK_UI_KIT
//@GLOBALS
constant integer KKI_MAXN=120
constant integer KKI_COD=30000
constant integer KKI_COD_HEROI=30100
constant integer KKI_COD_FECHA=30200
constant integer KKI_COD_ANT=30201
constant integer KKI_COD_PROX=30202
constant integer KKI_G_HEROI=1
constant integer KKI_G_PODE=2
constant integer KKI_G_GUARDA=3
constant integer KKI_G_ANTES_DAR=4
constant integer KKI_G_DEPOIS_DAR=5
constant integer KKI_G_MUDOU=6
constant integer KKI_G_ATRIBUTO=7
constant integer KKI_G_N=7
constant integer KKI_COD_AT=30210
constant integer KKI_AT_MAX=4
constant integer KKI_AT_DIG=9
constant real KKI_FOCO_TEMPO=3.0
constant string KKI_TEX_VAZIO="war3mapImported\\KKUI\\vazio.tga"
integer KKI_colunas=6
integer KKI_linhas=3
integer KKI_paginas=1
integer KKI_tecla=73
string KKI_tecla_nome="I"
string KKI_titulo="Inventory"
string KKI_r_pagina=""
real KKI_pag_w=0.0
string KKI_prefixo="kki"
real KKI_x=0.263
real KKI_y=0.515
real KKI_s=0.034
real KKI_gap=0.006
string KKI_r_heroi="Hero bag"
string KKI_r_guardado="Stored"
string KKI_r_dica="Click an item in your bag to store it. Click a stored item to take it back."
string KKI_r_dica_heroi="Click: store in the inventory"
string KKI_r_dica_casa="Click: take back to your hero"
string KKI_m_cheio="|cffffcc00The inventory is full.|r"
string KKI_m_sem_heroi="|cffffcc00Pick a hero first.|r"
string KKI_m_morto="|cffffcc00Your hero is dead.|r"
string KKI_m_chao="|cffffcc00Your bag is full: the item was dropped at your feet.|r"
string KKI_m_espera="|cffffcc00The inventory opens a moment after the game starts.|r"
real array KKI_px
real array KKI_py
boolean KKI_at_liga=false
integer KKI_at_n=3
string array KKI_at_nome
playerstate KKI_at_estado=PLAYER_STATE_RESOURCE_LUMBER
string KKI_r_at_pontos="Stat points (lumber): "
string KKI_r_at_dica="Empty = all your points go to that stat; or type an amount"
string KKI_r_at_botao="Click: put the points in "
integer KKI_jogadores=12
boolean KKI_ok=false
item array KKI_it
integer array KKI_tag
integer array KKI_pag
integer array KKI_ver
boolean array KKI_aberto
unit array KKI_heroi
trigger array KKI_tg
boolean array KKI_tem
integer KKI_ult_slot=-1
integer KKI_ult_q=0
integer KKI_tag_novo=0
integer KKI_lugar_novo=-1
integer KKI_ev_pid=0
integer KKI_ev_slot=0
item KKI_ev_it=null
unit KKI_ev_u=null
boolean KKI_ev_ok=true
string KKI_ev_msg=""
integer KKI_at_quem=-1
integer KKI_at_qual=0
integer KKI_at_num=0
string KKI_at_txt=""
timer KKI_tm_rel=null
trigger KKI_t_tecla=null
trigger KKI_t_sync=null
timer KKI_tm_espera=null
timer KKI_tm_local=null
timer KKI_tm_1s=null
boolean KKI_iniciado=false
boolean KKI_pronto=false
integer KKI_raiz=0
integer KKI_f_titulo=0
integer KKI_f_pag=0
integer KKI_f_det=0
integer KKI_f_pontos=0
integer KKI_f_num=0
integer array KKI_c_at
integer KKI_c_ant=0
integer KKI_c_prox=0
integer array KKI_c_casa
integer array KKI_c_qtd
integer array KKI_h_casa
integer array KKI_h_qtd
integer KKI_l_ver=-1
integer KKI_l_pid=-1
integer KKI_l_pag=-1
integer KKI_l_cod=-1
integer KKI_l_pontos=-1
boolean KKI_l_foco=false
real KKI_l_foco_t=0.0
integer array KKI_l_t
integer array KKI_l_q
integer array KKI_lh_t
integer array KKI_lh_q
//@ENDGLOBALS

function KKI_gancho takes integer qual, code f returns nothing
    if qual<1 or qual>KKI_G_N then
        return
    endif
    if KKI_tg[qual]==null then
        set KKI_tg[qual]=CreateTrigger()
    endif
    call TriggerAddCondition(KKI_tg[qual], Condition(f))
    set KKI_tem[qual]=true
endfunction

function KKI_chama takes integer qual returns nothing
    if qual>=1 and qual<=KKI_G_N and KKI_tem[qual] then
        call TriggerEvaluate(KKI_tg[qual])
    endif
endfunction

function KKI_n takes nothing returns integer
    return IMinBJ(IMaxBJ(KKI_colunas*KKI_linhas*KKI_paginas, 1), KKI_MAXN)
endfunction

function KKI_por_pag takes nothing returns integer
    return IMinBJ(IMinBJ(IMaxBJ(KKI_colunas*KKI_linhas, 1), KKI_MAXN), KKI_COD_HEROI-KKI_COD)
endfunction

function KKI_npag takes nothing returns integer
    local integer pp=KKI_por_pag()
    return (KKI_n()+pp-1)/pp
endfunction

function KKI_pid_ok takes integer pid returns boolean
    return pid>=0 and pid<KKI_jogadores
endfunction

function KKI_item takes integer pid, integer s returns item
    if not KKI_pid_ok(pid) or s<0 or s>=KKI_n() then
        return null
    endif
    if GetItemTypeId(KKI_it[pid*KKI_MAXN+s])==0 then
        return null
    endif
    return KKI_it[pid*KKI_MAXN+s]
endfunction

function KKI_e_aberto takes integer pid returns boolean
    return KKI_pronto and KKI_pid_ok(pid) and KKU_na_pilha(pid, KKI_raiz)>=0
endfunction

function KKI_tag_de takes integer pid, integer s returns integer
    if not KKI_pid_ok(pid) or s<0 or s>=KKI_n() then
        return 0
    endif
    return KKI_tag[pid*KKI_MAXN+s]
endfunction

function KKI_tag_poe takes integer pid, integer s, integer v returns nothing
    if KKI_pid_ok(pid) and s>=0 and s<KKI_n() then
        set KKI_tag[pid*KKI_MAXN+s]=v
    endif
endfunction

function KKI_qtd takes integer pid returns integer
    local integer s=0
    local integer q=0
    if not KKI_pid_ok(pid) then
        return 0
    endif
    loop
        exitwhen s>=KKI_n()
        if GetItemTypeId(KKI_it[pid*KKI_MAXN+s])!=0 then
            set q=q+1
        endif
        set s=s+1
    endloop
    return q
endfunction

function KKI_livre takes integer pid returns integer
    local integer s=0
    loop
        exitwhen s>=KKI_n()
        if KKI_it[pid*KKI_MAXN+s]==null then
            return s
        endif
        if GetItemTypeId(KKI_it[pid*KKI_MAXN+s])==0 then
            set KKI_it[pid*KKI_MAXN+s]=null
            set KKI_tag[pid*KKI_MAXN+s]=0
            return s
        endif
        set s=s+1
    endloop
    return -1
endfunction

function KKI_mudou takes integer pid, integer s, item it returns nothing
    set KKI_ver[pid]=KKI_ver[pid]+1
    if KKI_tem[KKI_G_MUDOU] then
        set KKI_ev_pid=pid
        set KKI_ev_slot=s
        set KKI_ev_it=it
        call KKI_chama(KKI_G_MUDOU)
        set KKI_ev_it=null
    endif
endfunction

function KKI_poe takes integer pid, item it returns boolean
    local integer s
    local integer k=0
    local integer n=KKI_n()
    set KKI_ult_slot=-1
    if not KKI_pid_ok(pid) or it==null or GetItemTypeId(it)==0 then
        set KKI_tag_novo=0
        set KKI_lugar_novo=-1
        return false
    endif
    if KKI_lugar_novo<0 then
        loop
            exitwhen k>=n
            if KKI_it[pid*KKI_MAXN+k]==it then
                set KKI_tag_novo=0
                return false
            endif
            set k=k+1
        endloop
    endif
    set s=-1
    if KKI_lugar_novo>=0 and KKI_lugar_novo<KKI_n() then
        if KKI_it[pid*KKI_MAXN+KKI_lugar_novo]!=null and GetItemTypeId(KKI_it[pid*KKI_MAXN+KKI_lugar_novo])==0 then
            set KKI_it[pid*KKI_MAXN+KKI_lugar_novo]=null
            set KKI_tag[pid*KKI_MAXN+KKI_lugar_novo]=0
        endif
        if KKI_it[pid*KKI_MAXN+KKI_lugar_novo]==null then
            set s=KKI_lugar_novo
        endif
    endif
    set KKI_lugar_novo=-1
    if s<0 then
        set s=KKI_livre(pid)
    endif
    if s<0 then
        set KKI_tag_novo=0
        return false
    endif
    set KKI_it[pid*KKI_MAXN+s]=it
    set KKI_tag[pid*KKI_MAXN+s]=KKI_tag_novo
    set KKI_tag_novo=0
    set KKI_ult_slot=s
    if KKI_tem[KKI_G_GUARDA] then
        set KKI_ev_pid=pid
        set KKI_ev_slot=s
        set KKI_ev_it=it
        call KKI_chama(KKI_G_GUARDA)
        set KKI_ev_it=null
    else
        call SetItemPosition(it, KKI_px[pid], KKI_py[pid])
        call SetItemVisible(it, false)
    endif
    call KKI_mudou(pid, s, it)
    return true
endfunction

function KKI_tira takes integer pid, integer s returns item
    local item it=KKI_item(pid, s)
    if it==null then
        return null
    endif
    set KKI_it[pid*KKI_MAXN+s]=null
    set KKI_tag[pid*KKI_MAXN+s]=0
    call SetItemVisible(it, true)
    call KKI_mudou(pid, s, it)
    return it
endfunction

function KKI_limpa takes integer pid, boolean remove returns nothing
    local integer s=0
    local item it
    if not KKI_pid_ok(pid) then
        return
    endif
    loop
        exitwhen s>=KKI_n()
        set it=KKI_it[pid*KKI_MAXN+s]
        if it!=null then
            set KKI_it[pid*KKI_MAXN+s]=null
            set KKI_tag[pid*KKI_MAXN+s]=0
            if remove then
                call RemoveItem(it)
            else
                call SetItemVisible(it, true)
            endif
        endif
        set s=s+1
    endloop
    set it=null
    call KKI_mudou(pid, -1, null)
endfunction

function KKI_heroi_de takes integer pid returns unit
    if KKI_tem[KKI_G_HEROI] then
        set KKI_ev_pid=pid
        call KKI_chama(KKI_G_HEROI)
    endif
    if KKI_heroi[pid]!=null and GetUnitTypeId(KKI_heroi[pid])==0 then
        set KKI_heroi[pid]=null
    endif
    return KKI_heroi[pid]
endfunction

function KKI_vivo takes unit u returns boolean
    return u!=null and GetUnitTypeId(u)!=0 and not IsUnitType(u, UNIT_TYPE_DEAD) and GetWidgetLife(u)>0.405
endfunction

function KKI_vaga takes unit u returns boolean
    local integer s=0
    loop
        exitwhen s>=UnitInventorySize(u)
        if UnitItemInSlot(u, s)==null then
            return true
        endif
        set s=s+1
    endloop
    return false
endfunction

function KKI_avisa takes integer pid, string s returns nothing
    if s!=null and s!="" then
        call DisplayTimedTextToPlayer(Player(pid), 0, 0, 6.0, s)
    endif
endfunction

function KKI_deposita takes integer pid, integer hs returns boolean
    local unit h
    local item it
    if not KKI_pid_ok(pid) then
        return false
    endif
    set h=KKI_heroi_de(pid)
    if h==null then
        call KKI_avisa(pid, KKI_m_sem_heroi)
        return false
    endif
    if not KKI_vivo(h) then
        set h=null
        call KKI_avisa(pid, KKI_m_morto)
        return false
    endif
    set it=UnitItemInSlot(h, hs)
    if it==null then
        set h=null
        return false
    endif
    if KKI_livre(pid)<0 then
        set h=null
        set it=null
        call KKI_avisa(pid, KKI_m_cheio)
        return false
    endif
    set KKI_ev_ok=true
    set KKI_ev_msg=""
    if KKI_tem[KKI_G_PODE] then
        set KKI_ev_pid=pid
        set KKI_ev_it=it
        set KKI_ev_u=h
        call KKI_chama(KKI_G_PODE)
        set KKI_ev_it=null
        set KKI_ev_u=null
    endif
    if not KKI_ev_ok then
        call KKI_avisa(pid, KKI_ev_msg)
        set h=null
        set it=null
        return false
    endif
    call KKI_poe(pid, it)
    set h=null
    set it=null
    return true
endfunction

function KKI_retira takes integer pid, integer s returns boolean
    local unit h
    local item it
    if not KKI_pid_ok(pid) or KKI_item(pid, s)==null then
        return false
    endif
    set h=KKI_heroi_de(pid)
    if h==null then
        call KKI_avisa(pid, KKI_m_sem_heroi)
        return false
    endif
    if not KKI_vivo(h) then
        set h=null
        call KKI_avisa(pid, KKI_m_morto)
        return false
    endif
    set it=KKI_tira(pid, s)
    set KKI_ev_pid=pid
    set KKI_ev_it=it
    set KKI_ev_u=h
    call KKI_chama(KKI_G_ANTES_DAR)
    if KKI_vaga(h) then
        call UnitAddItem(h, it)
    else
        call SetItemPosition(it, GetUnitX(h), GetUnitY(h))
        call KKI_avisa(pid, KKI_m_chao)
    endif
    set KKI_ev_pid=pid
    set KKI_ev_it=it
    set KKI_ev_u=h
    call KKI_chama(KKI_G_DEPOIS_DAR)
    set KKI_ev_it=null
    set KKI_ev_u=null
    set h=null
    set it=null
    return true
endfunction

function KKI_digitos takes string s, integer maximo returns string
    local integer i=0
    local integer n=StringLength(s)
    local string c
    local string r=""
    loop
        exitwhen i>=n or StringLength(r)>=maximo
        set c=SubString(s, i, i+1)
        if c=="0" or c=="1" or c=="2" or c=="3" or c=="4" or c=="5" or c=="6" or c=="7" or c=="8" or c=="9" then
            set r=r+c
        endif
        set i=i+1
    endloop
    return r
endfunction

function KKI_campo_digitando takes nothing returns boolean
    local integer pid=GetPlayerId(GetLocalPlayer())
    local real agora
    if not KKI_l_foco or not KKI_pronto or not KKI_pid_ok(pid) then
        return false
    endif
    set agora=TimerGetElapsed(KKI_tm_rel)
    if KKU_na_pilha(pid, KKI_raiz)<0 or agora-KKI_l_foco_t>=KKI_FOCO_TEMPO or agora<KKI_l_foco_t then
        set KKI_l_foco=false
        return false
    endif
    return true
endfunction

function KKI_solta_campo takes nothing returns nothing
    set KKI_l_foco=false
    if KKI_f_num>0 and KKI_f_num<KKU_MAX then
        call KKU_campo_foco(KKI_f_num, false)
    endif
endfunction

function KKI_digitando takes nothing returns boolean
    //{{KK_INCLUI:inv_digitando}}
    return false
endfunction

function KKI_icone takes integer c, integer q, item it returns nothing
    if it==null or GetItemTypeId(it)==0 then
        call KKU_vis(c+1, false)
        call KKU_texto(q, "")
    else
        call KKU_casa_icone(c, BlzGetItemIconPath(it))
        call KKU_vis(c+1, true)
        if GetItemCharges(it)>0 then
            call KKU_texto(q, I2S(GetItemCharges(it)))
        else
            call KKU_texto(q, "")
        endif
    endif
endfunction

function KKI_desenha takes integer pid, boolean tudo returns nothing
    local integer pp=KKI_por_pag()
    local integer off
    local integer i=0
    local integer t
    local integer q
    local unit h=KKI_heroi[pid]
    local item it
    local boolean mudou=false
    if not KKI_pronto or not KKI_pid_ok(pid) then
        set h=null
        return
    endif
    if pid!=KKI_l_pid then
        set KKI_l_pid=pid
        set tudo=true
    endif
    if KKI_l_pag!=KKI_pag[pid] then
        set KKI_l_pag=KKI_pag[pid]
        set tudo=true
        if KKI_f_pag>0 and KKI_f_pag<KKU_MAX then
            call KKU_texto(KKI_f_pag, KKI_r_pagina+I2S(KKI_pag[pid]+1)+" / "+I2S(KKI_npag()))
        endif
    endif
    loop
        exitwhen i>=6
        set it=null
        if h!=null and i<UnitInventorySize(h) then
            set it=UnitItemInSlot(h, i)
        endif
        set t=GetItemTypeId(it)
        set q=GetItemCharges(it)
        if tudo or t!=KKI_lh_t[i] or q!=KKI_lh_q[i] then
            set KKI_lh_t[i]=t
            set KKI_lh_q[i]=q
            call KKI_icone(KKI_h_casa[i], KKI_h_qtd[i], it)
            set mudou=true
        endif
        set i=i+1
    endloop
    if tudo or KKI_l_ver!=KKI_ver[pid] then
        set KKI_l_ver=KKI_ver[pid]
        set off=KKI_pag[pid]*pp
        set i=0
        loop
            exitwhen i>=pp
            set it=null
            if off+i<KKI_n() then
                set it=KKI_it[pid*KKI_MAXN+off+i]
            endif
            set t=GetItemTypeId(it)
            set q=GetItemCharges(it)
            if tudo or t!=KKI_l_t[i] or q!=KKI_l_q[i] then
                set KKI_l_t[i]=t
                set KKI_l_q[i]=q
                call KKI_icone(KKI_c_casa[i], KKI_c_qtd[i], it)
                set mudou=true
            endif
            set i=i+1
        endloop
    endif
    if KKI_at_liga and KKI_f_pontos>0 and KKI_f_pontos<KKU_MAX then
        set q=GetPlayerState(Player(pid), KKI_at_estado)
        if tudo or q!=KKI_l_pontos then
            set KKI_l_pontos=q
            call KKU_texto(KKI_f_pontos, KKI_r_at_pontos+"|cffffcc00"+I2S(q)+"|r")
            set mudou=true
        endif
    endif
    set h=null
    set it=null
    if mudou then
        set KKI_l_cod=-1
        call KKU_aplica()
    endif
endfunction

function KKI_detalhe takes integer pid, integer cod returns nothing
    local item it=null
    local string s
    local integer i
    if cod==KKI_l_cod then
        return
    endif
    set KKI_l_cod=cod
    if cod>=KKI_COD_HEROI and cod<KKI_COD_HEROI+6 then
        if KKI_heroi[pid]!=null then
            set it=UnitItemInSlot(KKI_heroi[pid], cod-KKI_COD_HEROI)
        endif
    elseif cod>=KKI_COD and cod<KKI_COD+KKI_por_pag() then
        set i=KKI_pag[pid]*KKI_por_pag()+cod-KKI_COD
        if i<KKI_n() then
            set it=KKI_it[pid*KKI_MAXN+i]
        endif
    endif
    if it==null or GetItemTypeId(it)==0 then
        set s=KKI_r_dica
    else
        set s="|cffffcc00"+GetItemName(it)+"|r"
        if GetItemCharges(it)>0 then
            set s=s+"  ["+I2S(GetItemCharges(it))+"]"
        endif
        if cod>=KKI_COD_HEROI then
            set s=s+"|n|cff999999"+KKI_r_dica_heroi+"|r"
        else
            set s=s+"|n|cff999999"+KKI_r_dica_casa+"|r"
        endif
    endif
    set it=null
    call KKU_texto(KKI_f_det, s)
    call KKU_aplica()
endfunction

function KKI_tique_local takes nothing returns nothing
    local integer pid=GetPlayerId(GetLocalPlayer())
    local integer t
    local integer cod=0
    if not KKI_pronto or KKU_rc_fase!=0 or not KKI_pid_ok(pid) then
        return
    endif
    if KKU_na_pilha(pid, KKI_raiz)<0 then
        return
    endif
    call KKI_desenha(pid, false)
    set t=KKU_sob_mouse()
    if t>0 then
        set cod=KKU_alvo_cod[t]
    endif
    call KKI_detalhe(pid, cod)
endfunction

function KKI_abre takes integer pid returns nothing
    if not KKI_pid_ok(pid) then
        return
    endif
    if not KKI_pronto or KKU_rc_fase!=0 then
        call KKI_avisa(pid, KKI_m_espera)
        return
    endif
    call KKI_heroi_de(pid)
    if KKI_pag[pid]<0 or KKI_pag[pid]>=KKI_npag() then
        set KKI_pag[pid]=0
    endif
    set KKI_aberto[pid]=true
    call KKU_janela_abre(pid, KKI_raiz)
    if GetLocalPlayer()==Player(pid) then
        set KKI_l_cod=-1
        call KKI_desenha(pid, true)
        call KKI_detalhe(pid, 0)
    endif
endfunction

function KKI_fecha takes integer pid returns nothing
    if not KKI_pid_ok(pid) then
        return
    endif
    set KKI_aberto[pid]=false
    if KKI_pronto then
        call KKU_janela_fecha(pid, KKI_raiz)
        if GetLocalPlayer()==Player(pid) then
            call KKI_solta_campo()
        endif
    endif
endfunction

function KKI_alterna takes integer pid returns nothing
    if KKI_e_aberto(pid) then
        call KKI_fecha(pid)
    else
        call KKI_abre(pid)
    endif
endfunction

function KKI_ev_tecla takes nothing returns nothing
    local player p=GetTriggerPlayer()
    if GetLocalPlayer()==p then
        if not KKI_digitando() and not KKI_campo_digitando() then
            call BlzSendSyncData(KKI_prefixo, "t")
        endif
    endif
    set p=null
endfunction

function KKI_atributo takes integer pid, integer q, string d returns nothing
    if not KKI_at_liga or not KKI_pid_ok(pid) or q<0 or q>=KKI_at_n then
        return
    endif
    set KKI_at_quem=pid
    set KKI_ev_pid=pid
    set KKI_at_qual=q
    set KKI_at_txt=d
    set KKI_at_num=0
    if d!="" then
        set KKI_at_num=S2I(d)
    endif
    call KKI_chama(KKI_G_ATRIBUTO)
    set KKI_at_quem=-1
    set KKI_ver[pid]=KKI_ver[pid]+1
endfunction

function KKI_ev_sync takes nothing returns nothing
    local integer pid=GetPlayerId(GetTriggerPlayer())
    local string s=BlzGetTriggerSyncData()
    local string d
    if s=="t" then
        call KKI_alterna(pid)
        return
    endif
    if StringLength(s)<3 or SubString(s, 0, 1)!="a" or SubString(s, 2, 3)!=":" then
        return
    endif
    if KKI_digitos(SubString(s, 1, 2), 1)=="" then
        return
    endif
    set d=SubString(s, 3, StringLength(s))
    if StringLength(d)>KKI_AT_DIG or KKI_digitos(d, KKI_AT_DIG)!=d then
        return
    endif
    call KKI_atributo(pid, S2I(SubString(s, 1, 2)), d)
endfunction

function KKI_ao_texto takes nothing returns boolean
    local string s=KKU_c_txt
    local string d
    if KKI_f_num<=0 or KKU_c_id!=KKI_f_num or not KKI_pid_ok(KKU_c_pid) then
        return false
    endif
    if GetLocalPlayer()==Player(KKU_c_pid) then
        if s==null then
            set s=""
        endif
        set d=KKI_digitos(s, KKI_AT_DIG)
        if KKU_c_valor>0.5 then
            call KKI_solta_campo()
        else
            set KKI_l_foco=true
            set KKI_l_foco_t=TimerGetElapsed(KKI_tm_rel)
        endif
        if d!=s then
            call KKU_campo_poe(KKI_f_num, d)
        endif
    endif
    return false
endfunction

function KKI_ao_clique takes nothing returns boolean
    local integer pid=KKU_c_pid
    local integer c=KKU_c_cod
    local integer pp=KKI_por_pag()
    local string d
    if c<KKI_COD or c>=KKI_COD_AT+KKI_AT_MAX or not KKI_pronto or KKU_rc_fase!=0 or not KKI_pid_ok(pid) then
        return false
    endif
    set KKI_aberto[pid]=KKI_e_aberto(pid)
    if not KKI_aberto[pid] then
        return false
    endif
    if c==KKI_COD_FECHA then
        call KKI_fecha(pid)
        return false
    elseif c==KKI_COD_ANT then
        if KKI_pag[pid]>0 then
            set KKI_pag[pid]=KKI_pag[pid]-1
        endif
    elseif c==KKI_COD_PROX then
        if KKI_pag[pid]<KKI_npag()-1 then
            set KKI_pag[pid]=KKI_pag[pid]+1
        endif
    elseif c>=KKI_COD_AT then
        if KKI_at_liga and c<KKI_COD_AT+KKI_at_n and GetLocalPlayer()==Player(pid) then
            set d=""
            if KKI_f_num>0 and KKI_f_num<KKU_MAX and KKU_f[KKI_f_num]!=null then
                set d=KKI_digitos(BlzFrameGetText(KKU_f[KKI_f_num]), KKI_AT_DIG)
            endif
            call BlzSendSyncData(KKI_prefixo, "a"+I2S(c-KKI_COD_AT)+":"+d)
        endif
    elseif c>=KKI_COD_HEROI and c<KKI_COD_HEROI+6 then
        call KKI_deposita(pid, c-KKI_COD_HEROI)
    elseif c<KKI_COD+pp then
        call KKI_retira(pid, KKI_pag[pid]*pp+c-KKI_COD)
    else
        call KKI_heroi_de(pid)
    endif
    if GetLocalPlayer()==Player(pid) then
        set KKI_l_cod=-1
        call KKI_solta_campo()
        call KKI_desenha(pid, false)
    endif
    return false
endfunction

function KKI_ao_fecha takes nothing returns boolean
    if KKU_c_jan==KKI_raiz and KKI_raiz>0 and KKI_pid_ok(KKU_c_pid) then
        set KKI_aberto[KKU_c_pid]=false
        if GetLocalPlayer()==Player(KKU_c_pid) then
            call KKI_solta_campo()
        endif
    endif
    return false
endfunction

function KKI_ao_carga takes nothing returns boolean
    local integer pid
    if not KKI_pronto then
        return false
    endif
    set pid=GetPlayerId(GetLocalPlayer())
    set KKI_l_pid=-1
    set KKI_l_cod=-1
    set KKI_l_foco=false
    if KKI_pid_ok(pid) and KKU_na_pilha(pid, KKI_raiz)>=0 then
        call KKI_desenha(pid, true)
    endif
    return false
endfunction

function KKI_tique1 takes nothing returns nothing
    local integer pid=0
    local unit h
    loop
        exitwhen pid>=KKI_jogadores
        set KKI_aberto[pid]=KKI_e_aberto(pid)
        if KKI_aberto[pid] then
            set h=KKI_heroi[pid]
            if KKI_heroi_de(pid)!=h then
                set KKI_ver[pid]=KKI_ver[pid]+1
            endif
        endif
        set pid=pid+1
    endloop
    set h=null
endfunction

function KKI_rotulo_novo takes integer pai, integer fonte, real x, real y, real w, real h, string s returns integer
    local integer t=KKU_txt(pai, fonte, x, y, w, h)
    call KKU_rotulo(t, s, false)
    return t
endfunction

function KKI_casa_nova takes integer pai, real x, real y, integer cod returns integer
    local integer c=KKU_casa(pai, x, y, KKI_s, cod)
    local integer q
    set q=KKU_txt(c, KKU_F_PEQUENA, x+KKI_s*0.30, y-KKI_s*0.60, KKI_s*0.64, KKI_s*0.34)
    call KKU_alinha(q, KKU_AL_MEIO_DIR)
    call KKU_vis(c+1, false)
    set KKI_ult_q=q
    return c
endfunction

function KKI_cria takes nothing returns nothing
    local integer cols=IMinBJ(KKI_colunas, KKI_MAXN)
    local integer pp=KKI_por_pag()
    local real passo=KKI_s+KKI_gap
    local real w=I2R(IMaxBJ(cols, 6))*passo-KKI_gap+0.040
    local real x=KKI_x
    local real y=KKI_y
    local real h
    local real cx
    local real cy
    local integer i=0
    local integer linhas=(pp+cols-1)/cols
    set h=0.040+0.016+KKI_s+0.014+0.016+I2R(linhas)*passo-KKI_gap+0.012+0.040+0.016
    if KKI_paginas>1 then
        set h=h+0.026
    endif
    if KKI_at_liga then
        set h=h+0.068
    endif
    set KKI_raiz=KKU_pagina(0)
    if KKI_raiz<=0 or KKI_raiz>=KKU_MAX then
        return
    endif
    call KKU_poe(KKI_raiz, x, y, 0.0, 0.0)
    call KKU_janela_cobre(KKI_raiz, x, y, w, h)
    call KKU_caixa(KKI_raiz, KKU_P_MOLDURA, x, y, w, h)
    call KKU_fundo(KKI_raiz, x, y, w, h, false)
    if KKU_tema_tex[KKU_P_FAIXA_TOPO]!=KKI_TEX_VAZIO then
        call KKU_img(KKI_raiz, KKU_P_FAIXA_TOPO, x, y, w, 0.032)
    endif
    if KKU_tema_tex[KKU_P_CANTO_TL]!=KKI_TEX_VAZIO then
        call KKU_img(KKI_raiz, KKU_P_CANTO_TL, x, y, 0.02, 0.02)
    endif
    if KKU_tema_tex[KKU_P_CANTO_TR]!=KKI_TEX_VAZIO then
        call KKU_img(KKI_raiz, KKU_P_CANTO_TR, x+w-0.02, y, 0.02, 0.02)
    endif
    if KKU_tema_tex[KKU_P_CANTO_BL]!=KKI_TEX_VAZIO then
        call KKU_img(KKI_raiz, KKU_P_CANTO_BL, x, y-h+0.02, 0.02, 0.02)
    endif
    if KKU_tema_tex[KKU_P_CANTO_BR]!=KKI_TEX_VAZIO then
        call KKU_img(KKI_raiz, KKU_P_CANTO_BR, x+w-0.02, y-h+0.02, 0.02, 0.02)
    endif
    set KKI_f_titulo=KKI_rotulo_novo(KKI_raiz, KKU_F_NORMAL, x+0.020, y-0.008, w-0.070, 0.020, KKI_titulo+"  ["+KKI_tecla_nome+"]")
    call KKU_botao_papel(KKI_raiz, KKU_P_FECHAR, KKU_ROT_FECHAR, x+w-0.040, y-0.006, 0.026, 0.024, KKI_COD_FECHA)
    set cy=y-0.040
    call KKI_rotulo_novo(KKI_raiz, KKU_F_PEQUENA, x+0.020, cy, w-0.040, 0.014, KKI_r_heroi)
    set cy=cy-0.016
    loop
        exitwhen i>=6
        set cx=x+0.020+I2R(i)*passo
        set KKI_h_casa[i]=KKI_casa_nova(KKI_raiz, cx, cy, KKI_COD_HEROI+i)
        set KKI_h_qtd[i]=KKI_ult_q
        call KKU_dica(KKI_COD_HEROI+i, KKI_r_dica_heroi)
        set i=i+1
    endloop
    set cy=cy-KKI_s-0.014
    call KKI_rotulo_novo(KKI_raiz, KKU_F_PEQUENA, x+0.020, cy, w-0.040, 0.014, KKI_r_guardado+" ("+I2S(KKI_n())+")")
    set cy=cy-0.016
    set i=0
    loop
        exitwhen i>=pp
        set cx=x+0.020+I2R(ModuloInteger(i, cols))*passo
        set KKI_c_casa[i]=KKI_casa_nova(KKI_raiz, cx, cy-I2R(i/cols)*passo, KKI_COD+i)
        set KKI_c_qtd[i]=KKI_ult_q
        call KKU_dica(KKI_COD+i, KKI_r_dica_casa)
        set i=i+1
    endloop
    set cy=cy-I2R(linhas)*passo+KKI_gap-0.010
    if KKI_paginas>1 then
        set KKI_c_ant=KKU_botao_papel(KKI_raiz, KKU_P_SETA_ESQ, "", x+0.020, cy, 0.024, 0.022, KKI_COD_ANT)
        set KKI_f_pag=KKU_txt(KKI_raiz, KKU_F_PEQUENA, x+0.050, cy, 0.060+KKI_pag_w, 0.022)
        call KKU_alinha(KKI_f_pag, KKU_AL_MEIO_CENTRO)
        set KKI_c_prox=KKU_botao_papel(KKI_raiz, KKU_P_SETA_DIR, "", x+0.116+KKI_pag_w, cy, 0.024, 0.022, KKI_COD_PROX)
        set cy=cy-0.026
    endif
    if KKI_at_liga then
        set KKI_f_pontos=KKI_rotulo_novo(KKI_raiz, KKU_F_PEQUENA, x+0.020, cy, w-0.040, 0.014, KKI_r_at_pontos)
        set cy=cy-0.018
        set KKI_f_num=KKU_campo(KKI_raiz, x+0.020, cy, 0.070, 0.024, KKI_AT_DIG)
        set i=0
        loop
            exitwhen i>=KKI_at_n
            set KKI_c_at[i]=KKU_botao(KKI_raiz, KKI_at_nome[i], x+0.096+I2R(i)*0.054, cy, 0.050, 0.024, KKI_COD_AT+i)
            call KKU_dica(KKI_COD_AT+i, KKI_r_at_botao+KKI_at_nome[i])
            set i=i+1
        endloop
        set cy=cy-0.028
        call KKI_rotulo_novo(KKI_raiz, KKU_F_PEQUENA, x+0.020, cy, w-0.040, 0.014, KKI_r_at_dica)
        set cy=cy-0.022
    endif
    set KKI_f_det=KKU_txt(KKI_raiz, KKU_F_PEQUENA, x+0.020, cy, w-0.040, 0.050)
    call KKU_texto(KKI_f_det, KKI_r_dica)
    call KKU_esconde(KKI_raiz)
    set KKI_pronto=KKI_f_det>0 and KKI_f_det<KKU_MAX and KKI_c_casa[pp-1]>0 and KKI_c_casa[pp-1]<KKU_MAX and KKI_h_casa[5]>0 and KKI_h_casa[5]<KKU_MAX
    if KKI_at_liga then
        set KKI_pronto=KKI_pronto and KKI_f_num>0 and KKI_f_num<KKU_MAX and KKI_f_pontos>0 and KKI_f_pontos<KKU_MAX
    endif
    call KKU_aplica()
endfunction

function KKI_espera takes nothing returns nothing
    if KKI_iniciado or KKU_rc_fase!=0 then
        if KKI_iniciado then
            call PauseTimer(GetExpiredTimer())
        endif
        return
    endif
    set KKI_iniciado=true
    call PauseTimer(GetExpiredTimer())
    call ExecuteFunc("KKI_cria")
endfunction

function KKI_init takes nothing returns nothing
    local integer i=0
    local integer m=0
    if KKI_ok then
        return
    endif
    set KKI_ok=true
    call KKU_init()
    set KKI_jogadores=IMinBJ(KKU_JOGADORES, 16)
    if KKI_colunas<1 then
        set KKI_colunas=1
    endif
    if KKI_linhas<1 then
        set KKI_linhas=1
    endif
    if KKI_paginas<1 then
        set KKI_paginas=1
    endif
    call KKU_ao(KKU_AO_CLIQUE, function KKI_ao_clique)
    call KKU_ao(KKU_AO_FECHA, function KKI_ao_fecha)
    call KKU_ao(KKU_AO_CARGA, function KKI_ao_carga)
    call KKU_ao(KKU_AO_TEXTO, function KKI_ao_texto)
    if KKI_at_nome[0]==null or KKI_at_nome[0]=="" then
        set KKI_at_nome[0]="STR"
        set KKI_at_nome[1]="AGI"
        set KKI_at_nome[2]="INT"
    endif
    set KKI_at_n=IMinBJ(IMaxBJ(KKI_at_n, 1), KKI_AT_MAX)
    set KKI_tm_rel=CreateTimer()
    call TimerStart(KKI_tm_rel, 100000.0, true, null)
    set KKI_t_tecla=CreateTrigger()
    call TriggerAddAction(KKI_t_tecla, function KKI_ev_tecla)
    set KKI_t_sync=CreateTrigger()
    call TriggerAddAction(KKI_t_sync, function KKI_ev_sync)
    loop
        exitwhen i>=KKI_jogadores
        set m=0
        loop
            exitwhen m > KKU_META_ULT
            call BlzTriggerRegisterPlayerKeyEvent(KKI_t_tecla, Player(i), ConvertOsKeyType(KKI_tecla), m, false)
            set m=m + 1
        endloop
        call BlzTriggerRegisterPlayerSyncEvent(KKI_t_sync, Player(i), KKI_prefixo, false)
        set KKI_aberto[i]=false
        set KKI_pag[i]=0
        set KKI_ver[i]=0
        set i=i+1
    endloop
    set KKI_tm_espera=CreateTimer()
    call TimerStart(KKI_tm_espera, 0.50, true, function KKI_espera)
    set KKI_tm_local=CreateTimer()
    call TimerStart(KKI_tm_local, 0.10, true, function KKI_tique_local)
    set KKI_tm_1s=CreateTimer()
    call TimerStart(KKI_tm_1s, 1.00, true, function KKI_tique1)
endfunction
