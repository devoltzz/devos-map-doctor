//@REQUER KK:kk_ui.j KK_UI_KIT
//@GLOBALS
constant integer KKC_MAXN=12
constant integer KKC_COD=30400
constant integer KKC_COD_APAGA=30420
constant integer KKC_COD_NOVO=30440
constant integer KKC_COD_FECHA=30441
constant integer KKC_COD_FIM=30442
constant integer KKC_G_CARREGA=1
constant integer KKC_G_NOVO=2
constant integer KKC_G_APAGA=3
constant integer KKC_G_N=3
constant string KKC_TEX_VAZIO="war3mapImported\\KKUI\\vazio.tga"
integer KKC_slots=8
string KKC_titulo="Characters"
string KKC_r_slot="Slot "
string KKC_r_vazio="Empty slot (click: new character here)"
string KKC_r_novo="New character"
string KKC_r_apaga="Delete"
string KKC_r_certeza="Sure?"
string KKC_r_dica="Click a character to load it, or start a new one."
string KKC_r_conf="Click |cffff8080Sure?|r to delete this character for good (it cannot be undone)."
string KKC_m_espera="|cffffcc00The character menu opens a moment after the game starts.|r"
real KKC_x=0.235
real KKC_y=0.530
real KKC_w=0.330
real KKC_lh=0.026
integer KKC_jogadores=12
boolean KKC_ok=false
boolean KKC_iniciado=false
boolean KKC_pronto=false
string array KKC_rot
boolean array KKC_usa
integer array KKC_conf
string array KKC_linha_baixo
trigger array KKC_tg
boolean array KKC_tem
integer KKC_ev_pid=0
integer KKC_ev_slot=-1
timer KKC_tm_espera=null
integer KKC_raiz=0
integer KKC_f_dica=0
integer KKC_c_novo=0
integer array KKC_c_lin
integer array KKC_c_apa
//@ENDGLOBALS

function KKC_gancho takes integer qual, code f returns nothing
    if qual<1 or qual>KKC_G_N then
        return
    endif
    if KKC_tg[qual]==null then
        set KKC_tg[qual]=CreateTrigger()
    endif
    call TriggerAddCondition(KKC_tg[qual], Condition(f))
    set KKC_tem[qual]=true
endfunction

function KKC_chama takes integer qual, integer pid, integer s returns nothing
    if qual>=1 and qual<=KKC_G_N and KKC_tem[qual] then
        set KKC_ev_pid=pid
        set KKC_ev_slot=s
        call TriggerEvaluate(KKC_tg[qual])
    endif
endfunction

function KKC_n takes nothing returns integer
    return IMinBJ(IMaxBJ(KKC_slots, 1), KKC_MAXN)
endfunction

function KKC_pid_ok takes integer pid returns boolean
    return pid>=0 and pid<KKC_jogadores
endfunction

function KKC_usado takes integer pid, integer s returns boolean
    return KKC_pid_ok(pid) and s>=0 and s<KKC_n() and KKC_usa[pid*KKC_MAXN+s]
endfunction

function KKC_poe takes integer pid, integer s, string rotulo returns nothing
    if KKC_pid_ok(pid) and s>=0 and s<KKC_n() then
        set KKC_usa[pid*KKC_MAXN+s]=true
        set KKC_rot[pid*KKC_MAXN+s]=rotulo
    endif
endfunction

function KKC_tira takes integer pid, integer s returns nothing
    if KKC_pid_ok(pid) and s>=0 and s<KKC_n() then
        set KKC_usa[pid*KKC_MAXN+s]=false
        set KKC_rot[pid*KKC_MAXN+s]=""
        if KKC_conf[pid]==s then
            set KKC_conf[pid]=-1
        endif
    endif
endfunction

function KKC_livre takes integer pid returns integer
    local integer s=0
    loop
        exitwhen s>=KKC_n()
        if not KKC_usado(pid, s) then
            return s
        endif
        set s=s+1
    endloop
    return -1
endfunction

function KKC_conta takes integer pid returns integer
    local integer s=0
    local integer q=0
    loop
        exitwhen s>=KKC_n()
        if KKC_usado(pid, s) then
            set q=q+1
        endif
        set s=s+1
    endloop
    return q
endfunction

function KKC_e_aberto takes integer pid returns boolean
    return KKC_pronto and KKC_pid_ok(pid) and KKU_na_pilha(pid, KKC_raiz)>=0
endfunction

function KKC_desenha takes integer pid returns nothing
    local integer s=0
    local integer l
    local string d
    if not KKC_pronto or not KKC_pid_ok(pid) or GetLocalPlayer()!=Player(pid) then
        return
    endif
    loop
        exitwhen s>=KKC_n()
        set l=KKC_c_lin[s]
        if KKC_usa[pid*KKC_MAXN+s] then
            call KKU_linha_texto(l, KKC_rot[pid*KKC_MAXN+s])
            call KKU_linha_mostra(l, true, KKC_conf[pid]==s, false)
            call KKU_vis(KKC_c_apa[s], true)
            if KKC_conf[pid]==s then
                call KKU_texto(KKC_c_apa[s]+2, "|cffff8080"+KKC_r_certeza+"|r")
            else
                call KKU_texto(KKC_c_apa[s]+2, KKC_r_apaga)
            endif
        else
            call KKU_linha_texto(l, KKC_r_vazio)
            call KKU_linha_mostra(l, true, false, true)
            call KKU_vis(KKC_c_apa[s], false)
        endif
        call KKU_linha_info(l, KKC_r_slot+I2S(s+1))
        set s=s+1
    endloop
    set d=KKC_linha_baixo[pid]
    if KKC_conf[pid]>=0 then
        set d=KKC_r_conf
    elseif d==null or d=="" then
        set d=KKC_r_dica
    endif
    call KKU_texto(KKC_f_dica, d)
    call KKU_aplica()
endfunction

function KKC_dica takes integer pid, string s returns nothing
    if KKC_pid_ok(pid) then
        set KKC_linha_baixo[pid]=s
        if KKC_e_aberto(pid) then
            call KKC_desenha(pid)
        endif
    endif
endfunction

function KKC_abre takes integer pid returns nothing
    if not KKC_pid_ok(pid) then
        return
    endif
    if not KKC_pronto or KKU_rc_fase!=0 then
        if GetLocalPlayer()==Player(pid) then
            call DisplayTimedTextToPlayer(Player(pid), 0, 0, 6.0, KKC_m_espera)
        endif
        return
    endif
    set KKC_conf[pid]=-1
    call KKU_janela_abre(pid, KKC_raiz)
    call KKC_desenha(pid)
endfunction

function KKC_fecha takes integer pid returns nothing
    if not KKC_pid_ok(pid) then
        return
    endif
    set KKC_conf[pid]=-1
    if KKC_pronto then
        call KKU_janela_fecha(pid, KKC_raiz)
    endif
endfunction

function KKC_ao_clique takes nothing returns boolean
    local integer pid=KKU_c_pid
    local integer c=KKU_c_cod
    local integer s
    if c<KKC_COD or c>=KKC_COD_FIM or not KKC_pronto or KKU_rc_fase!=0 or not KKC_pid_ok(pid) then
        return false
    endif
    if not KKC_e_aberto(pid) then
        return false
    endif
    if c==KKC_COD_FECHA then
        call KKC_fecha(pid)
        return false
    endif
    if c==KKC_COD_NOVO then
        set KKC_conf[pid]=-1
        call KKC_chama(KKC_G_NOVO, pid, KKC_livre(pid))
    elseif c>=KKC_COD_APAGA and c<KKC_COD_APAGA+KKC_n() then
        set s=c-KKC_COD_APAGA
        if KKC_usado(pid, s) then
            if KKC_conf[pid]==s then
                set KKC_conf[pid]=-1
                call KKC_chama(KKC_G_APAGA, pid, s)
            else
                set KKC_conf[pid]=s
            endif
        endif
    elseif c>=KKC_COD and c<KKC_COD+KKC_n() then
        set s=c-KKC_COD
        set KKC_conf[pid]=-1
        if KKC_usado(pid, s) then
            call KKC_chama(KKC_G_CARREGA, pid, s)
        else
            call KKC_chama(KKC_G_NOVO, pid, s)
        endif
    endif
    if KKC_e_aberto(pid) then
        call KKC_desenha(pid)
    endif
    return false
endfunction

function KKC_ao_fecha takes nothing returns boolean
    if KKU_c_jan==KKC_raiz and KKC_raiz>0 and KKC_pid_ok(KKU_c_pid) then
        set KKC_conf[KKU_c_pid]=-1
    endif
    return false
endfunction

function KKC_ao_carga takes nothing returns boolean
    local integer pid
    if not KKC_pronto then
        return false
    endif
    set pid=GetPlayerId(GetLocalPlayer())
    if KKC_e_aberto(pid) then
        call KKC_desenha(pid)
    endif
    return false
endfunction

function KKC_cria takes nothing returns nothing
    local real x=KKC_x
    local real y=KKC_y
    local real w=KKC_w
    local real lw=w-0.040-0.058
    local real h
    local real cy
    local integer i=0
    local integer t
    set h=0.040+I2R(KKC_n())*(KKC_lh+0.004)+0.010+0.030+0.044+0.012
    set KKC_raiz=KKU_pagina(0)
    if KKC_raiz<=0 or KKC_raiz>=KKU_MAX then
        return
    endif
    call KKU_poe(KKC_raiz, x, y, 0.0, 0.0)
    call KKU_janela_cobre(KKC_raiz, x, y, w, h)
    call KKU_caixa(KKC_raiz, KKU_P_MOLDURA, x, y, w, h)
    call KKU_fundo(KKC_raiz, x, y, w, h, false)
    if KKU_tema_tex[KKU_P_FAIXA_TOPO]!=KKC_TEX_VAZIO then
        call KKU_img(KKC_raiz, KKU_P_FAIXA_TOPO, x, y, w, 0.032)
    endif
    if KKU_tema_tex[KKU_P_CANTO_TL]!=KKC_TEX_VAZIO then
        call KKU_img(KKC_raiz, KKU_P_CANTO_TL, x, y, 0.02, 0.02)
    endif
    if KKU_tema_tex[KKU_P_CANTO_TR]!=KKC_TEX_VAZIO then
        call KKU_img(KKC_raiz, KKU_P_CANTO_TR, x+w-0.02, y, 0.02, 0.02)
    endif
    if KKU_tema_tex[KKU_P_CANTO_BL]!=KKC_TEX_VAZIO then
        call KKU_img(KKC_raiz, KKU_P_CANTO_BL, x, y-h+0.02, 0.02, 0.02)
    endif
    if KKU_tema_tex[KKU_P_CANTO_BR]!=KKC_TEX_VAZIO then
        call KKU_img(KKC_raiz, KKU_P_CANTO_BR, x+w-0.02, y-h+0.02, 0.02, 0.02)
    endif
    set t=KKU_txt(KKC_raiz, KKU_F_NORMAL, x+0.020, y-0.008, w-0.070, 0.020)
    call KKU_rotulo(t, KKC_titulo, false)
    call KKU_botao_papel(KKC_raiz, KKU_P_FECHAR, KKU_ROT_FECHAR, x+w-0.040, y-0.006, 0.026, 0.024, KKC_COD_FECHA)
    set cy=y-0.040
    loop
        exitwhen i>=KKC_n()
        set KKC_c_lin[i]=KKU_linha_op(KKC_raiz, x+0.020, cy, lw, KKC_lh, KKC_COD+i, false, true, false)
        set KKC_c_apa[i]=KKU_botao(KKC_raiz, KKC_r_apaga, x+0.020+lw+0.006, cy, 0.052, KKC_lh, KKC_COD_APAGA+i)
        set cy=cy-KKC_lh-0.004
        set i=i+1
    endloop
    set cy=cy-0.010
    set KKC_c_novo=KKU_botao(KKC_raiz, KKC_r_novo, x+0.020, cy, 0.130, 0.028, KKC_COD_NOVO)
    set cy=cy-0.036
    set KKC_f_dica=KKU_txt(KKC_raiz, KKU_F_PEQUENA, x+0.020, cy, w-0.040, 0.040)
    call KKU_texto(KKC_f_dica, KKC_r_dica)
    call KKU_esconde(KKC_raiz)
    set KKC_pronto=KKC_f_dica>0 and KKC_f_dica<KKU_MAX and KKC_c_novo>0 and KKC_c_novo<KKU_MAX and KKC_c_apa[KKC_n()-1]>0 and KKC_c_apa[KKC_n()-1]<KKU_MAX
    call KKU_aplica()
endfunction

function KKC_espera takes nothing returns nothing
    if KKC_iniciado or KKU_rc_fase!=0 then
        if KKC_iniciado then
            call PauseTimer(GetExpiredTimer())
        endif
        return
    endif
    set KKC_iniciado=true
    call PauseTimer(GetExpiredTimer())
    call ExecuteFunc("KKC_cria")
endfunction

function KKC_init takes nothing returns nothing
    local integer i=0
    if KKC_ok then
        return
    endif
    set KKC_ok=true
    call KKU_init()
    set KKC_jogadores=IMinBJ(KKU_JOGADORES, 16)
    if KKC_slots<1 then
        set KKC_slots=1
    endif
    call KKU_ao(KKU_AO_CLIQUE, function KKC_ao_clique)
    call KKU_ao(KKU_AO_FECHA, function KKC_ao_fecha)
    call KKU_ao(KKU_AO_CARGA, function KKC_ao_carga)
    loop
        exitwhen i>=KKC_jogadores
        set KKC_conf[i]=-1
        set KKC_linha_baixo[i]=""
        set i=i+1
    endloop
    set KKC_tm_espera=CreateTimer()
    call TimerStart(KKC_tm_espera, 0.50, true, function KKC_espera)
endfunction
