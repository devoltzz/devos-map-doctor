//{{KK_SE:KK_UI_KIT}}
//@REQUER out_ui_dados.j
//@GLOBALS
constant integer KKU_MAX=4000
constant integer KKU_T_IMG=1
constant integer KKU_T_TXT=2
constant integer KKU_T_CAIXA=3
constant integer KKU_T_PAGINA=4
constant integer KKU_T_ALVO=5
constant integer KKU_T_FUNDO=6
constant integer KKU_T_SPRITE=7
constant integer KKU_T_EXTERNO=8
constant integer KKU_T_ALVO_TXT=9
constant integer KKU_T_CAMPO=10
constant integer KKU_T_AREA=11
constant integer KKU_T_ALVO_SIMP=12
constant real KKU_AREA_H_MIN=0.03
constant integer KKU_CAMPO_MAX=255
constant integer KKU_P_MOLDURA=1
constant integer KKU_P_FAIXA_TOPO=2
constant integer KKU_P_CANTO_TL=3
constant integer KKU_P_CANTO_TR=4
constant integer KKU_P_CANTO_BL=5
constant integer KKU_P_CANTO_BR=6
constant integer KKU_P_CAIXA=7
constant integer KKU_P_CAIXA_ATIVA=8
constant integer KKU_P_BOTAO=9
constant integer KKU_P_BOTAO_BORDA=10
constant integer KKU_P_ABA=11
constant integer KKU_P_ABA_ATIVA=12
constant integer KKU_P_FECHAR=13
constant integer KKU_P_SETA_ESQ=14
constant integer KKU_P_SETA_DIR=15
constant integer KKU_P_MARCA=16
constant integer KKU_P_ESCURO=17
constant integer KKU_P_VISTO=18
constant integer KKU_P_REALCE=19
constant integer KKU_P_ICONE_PADRAO=20
constant integer KKU_P_BORDA_9=21
constant integer KKU_F_NORMAL=1
constant integer KKU_F_PEQUENA=2
constant integer KKU_AO_CLIQUE=1
constant integer KKU_AO_RODA=2
constant integer KKU_AO_MENU=3
constant integer KKU_AO_FECHA=4
constant integer KKU_AO_CARGA=5
constant integer KKU_AO_TEXTO=6
constant integer KKU_AO_N=6
constant integer KKU_M_BOTAO=1
constant integer KKU_M_POSICAO=2
constant integer KKU_M_TEXTO=3
constant integer KKU_M_SIMPLES=4
integer KKU_alvo_padrao=1
integer array KKU_simp_q
integer KKU_nsimp=0
boolean KKU_simp_suja=false
real array KKU_cob_x
real array KKU_cob_y
real array KKU_cob_w
real array KKU_cob_h
integer array KKU_simp_jan
boolean array KKU_simp_dep
integer array KKU_dc_ini
integer array KKU_dc_prox
integer array KKU_dr_ini
integer array KKU_dr_prox
integer array KKU_sraiz
integer KKU_nsraiz=0
integer KKU_segue_prox=0
boolean array KKU_roda_ped
integer array KKU_pf_i
boolean array KKU_pf_c
integer KKU_npf=0
integer array KKU_pr_q
integer KKU_npr=0
integer array KKU_sm_i
integer array KKU_sm_c
integer KKU_nsm=0
integer KKU_sm_passe=0
integer array KKU_su_q
integer KKU_nsu=0
integer array KKU_jan_pos
integer KKU_jan_carimbo=0
boolean KKU_sp_ok=false
integer KKU_sp_p=0
integer KKU_sp_np=0
integer KKU_sp_nr=0
integer KKU_sp_base=0
integer KKU_sp_topo=-1
real array KKU_sp_x
real array KKU_sp_x2
real array KKU_sp_y
real array KKU_sp_y2
integer KKU_jan_quem=-1
constant integer KKU_EXT=8
integer array KKU_ext_id
real array KKU_ext_x
real array KKU_ext_y
real array KKU_ext_w
real array KKU_ext_h
integer array KKU_next
constant string KKU_SINC="kku"
string array KKU_tema_tex
string array KKU_tema_fdf
string array KKU_fonte
string KKU_cor_ativo=""
string KKU_cor_inativo=""
string KKU_cor_travado=""
string KKU_cor_erro=""
string KKU_cor_nota=""
real KKU_painel_x=0.0
real KKU_painel_y=0.0
real KKU_painel_w=0.0
real KKU_painel_h=0.0
integer KKU_painel_nivel=0
integer array KKU_pv_chave
string array KKU_pv_mdx
real array KKU_pv_k
real array KKU_pv_cx
real array KKU_pv_cy
framehandle array KKU_f
integer array KKU_tipo
integer array KKU_pai
integer array KKU_arg
real array KKU_x
real array KKU_y
real array KKU_w
real array KKU_h
integer KKU_n=0
boolean array KKU_q_vis
string array KKU_q_txt
string array KKU_q_tex
string array KKU_q_mod
real array KKU_q_esc
integer array KKU_q_alfa
boolean array KKU_q_ati
integer array KKU_q_niv
boolean array KKU_a_vis
string array KKU_a_txt
string array KKU_a_tex
string array KKU_a_mod
real array KKU_a_esc
integer array KKU_a_alfa
boolean array KKU_a_ati
integer array KKU_a_niv
real array KKU_a_x
real array KKU_a_y
real array KKU_a_w
real array KKU_a_h
boolean array KKU_a_ok
constant integer KKU_ANC_TL=0
constant integer KKU_ANC_BL=1
integer array KKU_anc
integer array KKU_a_anc
boolean array KKU_preso
integer array KKU_suja
boolean array KKU_esta_suja
integer KKU_nsuja=0
integer KKU_nat=0
integer KKU_cheio=0
integer array KKU_alvo_i
integer array KKU_alvo_cod
integer array KKU_alvo_q
integer array KKU_alvo_v
integer array KKU_alvo_seg
integer array KKU_alvo_de
boolean array KKU_alvo_on
integer KKU_nalvo=0
integer KKU_ult_alvo=0
integer array KKU_campos
integer KKU_ncampo=0
integer KKU_foco_modo=1
framehandle KKU_f_foco=null
integer KKU_foco_pend=0
boolean KKU_realce_liga=true
constant real KKU_DICA_W=0.20
constant real KKU_DICA_FOLGA=0.006
constant integer KKU_DICA_MAX=4096
integer KKU_i_realce=0
integer KKU_i_dica=0
integer KKU_i_dica_txt=0
boolean KKU_mouse_tent=false
constant integer KKU_COD_MENU=-1
integer KKU_i_borda=0
integer KKU_i_menu=0
integer KKU_dica_ver=0
timer KKU_tm_local=null
integer KKU_m_ult=0
integer KKU_m_ver=0
real KKU_m_x=0.0
real KKU_m_y=0.0
real KKU_m_w=0.0
real KKU_m_h=0.0
string array KKU_rot
string array KKU_lin_cor
integer array KKU_lin_ico
integer array KKU_lin_txt
integer array KKU_lin_info
integer array KKU_lin_marca
constant integer KKU_AL_TOPO_ESQ=0
constant integer KKU_AL_MEIO_ESQ=1
constant integer KKU_AL_MEIO_CENTRO=2
constant integer KKU_AL_MEIO_DIR=3
constant integer KKU_AL_TOPO_CENTRO=4
integer array KKU_alin
boolean array KKU_roda
boolean KKU_pronto=false
boolean KKU_toc_ok=false
hashtable KKU_ht=null
trigger array KKU_t_ao
trigger KKU_t_menu=null
trigger KKU_t_clique=null
trigger KKU_t_fundo=null
trigger KKU_t_roda=null
trigger KKU_t_sinc=null
trigger KKU_t_texto=null
trigger KKU_t_carga=null
timer KKU_tm_carga=null
constant integer KKU_RC_CRIA=100
constant integer KKU_RC_SIMP=3
constant integer KKU_RC_APLICA=16
constant integer KKU_RC_TETO=22
integer KKU_ap_teto=0
boolean KKU_rc_ativa=false
integer KKU_rc_fase=0
integer KKU_rc_i=0
integer KKU_rc_n=0
integer KKU_rc_ap=0
integer KKU_rc_voltas=0
framehandle KKU_rc_fb=null
framehandle KKU_rc_fh=null
framehandle KKU_f_console=null
constant integer KKU_PILHA=16
constant real KKU_ESC_JANELA=0.35
constant integer KKU_NIVEL_TETO=7
integer array KKU_pilha
integer array KKU_npilha
integer array KKU_esc_n_tecla
integer array KKU_esc_n_cine
integer array KKU_esc_via
real array KKU_esc_t
boolean array KKU_esc_par
real array KKU_esc_gap
timer KKU_tm_relogio=null
trigger KKU_t_esc_tecla=null
trigger KKU_t_esc_cine=null
boolean KKU_pv_ligada=false
boolean KKU_pv_bloqueada=false
boolean KKU_pv_avisa=false
boolean KKU_pv_apaga=true
integer KKU_pv_ultimo=0
real KKU_pv_resta=0.0
integer KKU_pv_passo=0
constant real KKU_ECO_JANELA=0.10
integer array KKU_eco_foco
integer array KKU_eco_pend_id
trigger array KKU_eco_pend_t
real array KKU_eco_pend_ini
integer KKU_eco_n=0
timer KKU_tm_sinc=null
timer KKU_tm_1s=null
group KKU_g_her=null
integer KKU_n_her=0
boolean array KKU_aviso
integer KKU_c_pid=0
integer KKU_c_cod=0
integer KKU_c_jan=0
real KKU_c_valor=0.0
integer KKU_c_id=0
string KKU_c_txt=""
integer KKU_c_alvo=0
//@ENDGLOBALS

function KKU_ao takes integer qual, code f returns nothing
    if qual < 1 or qual > KKU_AO_N or not KKU_pronto then
        return
    endif
    call TriggerAddCondition(KKU_t_ao[qual], Condition(f))
endfunction

function KKU_chama takes integer qual returns nothing
    if KKU_t_ao[qual] != null then
        call TriggerEvaluate(KKU_t_ao[qual])
    endif
endfunction

function KKU_args takes integer pid, integer cod, integer jan, real valor, integer id returns nothing
    set KKU_c_pid=pid
    set KKU_c_cod=cod
    set KKU_c_jan=jan
    set KKU_c_valor=valor
    set KKU_c_id=id
    set KKU_c_alvo=0
endfunction

function KKU_menu_tecla takes nothing returns nothing
    call KKU_args(GetPlayerId(GetTriggerPlayer()), 0, 0, 0.0, 0)
    call KKU_chama(KKU_AO_MENU)
endfunction

function KKU_vivo takes integer i returns boolean
    return not KKU_rc_ativa or i < KKU_rc_i or i > KKU_rc_n
endfunction

function KKU_quadro takes integer i returns framehandle
    if not KKU_vivo(i) then
        return null
    endif
    return KKU_f[i]
endfunction

function KKU_livre takes nothing returns boolean
    if KKU_n >= KKU_MAX - 1 then
        set KKU_cheio=KKU_cheio + 1
        return false
    endif
    return true
endfunction

function KKU_livres takes integer k returns boolean
    if not KKU_mouse_tent then
        set k=k + 3
    endif
    if KKU_n + k >= KKU_MAX then
        set KKU_cheio=KKU_cheio + 1
        return false
    endif
    return true
endfunction

function KKU_pai_ok takes integer pai returns boolean
    return pai >= 0 and pai < KKU_MAX and KKU_f[pai] != null and KKU_vivo(pai)
endfunction

function KKU_inicia takes integer i returns nothing
    set KKU_q_vis[i]=true
    set KKU_a_vis[i]=true
    set KKU_q_txt[i]=""
    set KKU_a_txt[i]=""
    set KKU_q_tex[i]=""
    set KKU_a_tex[i]=""
    set KKU_q_mod[i]=""
    set KKU_a_mod[i]=""
    set KKU_q_esc[i]=1.0
    set KKU_a_esc[i]=1.0
    set KKU_q_alfa[i]=255
    set KKU_a_alfa[i]=255
    set KKU_q_ati[i]=true
    set KKU_a_ati[i]=true
    set KKU_q_niv[i]=0
    set KKU_a_niv[i]=0
    set KKU_anc[i]=KKU_ANC_TL
    set KKU_a_anc[i]=KKU_ANC_TL
    set KKU_preso[i]=false
    set KKU_a_x[i]=KKU_x[i]
    set KKU_a_y[i]=KKU_y[i]
    set KKU_a_w[i]=KKU_w[i]
    set KKU_a_h[i]=KKU_h[i]
    set KKU_a_ok[i]=true
    set KKU_esta_suja[i]=false
endfunction

function KKU_guarda takes framehandle f, integer tipo, integer pai, integer arg, real x, real y, real w, real h returns integer
    set KKU_n=KKU_n + 1
    set KKU_f[KKU_n]=f
    set KKU_tipo[KKU_n]=tipo
    set KKU_pai[KKU_n]=pai
    set KKU_arg[KKU_n]=arg
    set KKU_x[KKU_n]=x
    set KKU_y[KKU_n]=y
    set KKU_w[KKU_n]=w
    set KKU_h[KKU_n]=h
    call KKU_inicia(KKU_n)
    return KKU_n
endfunction

function KKU_posiciona takes integer i returns nothing
    local framehandle f=KKU_f[i]
    call BlzFrameClearAllPoints(f)
    if KKU_tipo[i] == KKU_T_SPRITE then
        call BlzFrameSetAbsPoint(f, FRAMEPOINT_BOTTOMLEFT, KKU_x[i], KKU_y[i] - KKU_h[i])
    elseif KKU_anc[i] == KKU_ANC_BL then
        call BlzFrameSetAbsPoint(f, FRAMEPOINT_BOTTOMLEFT, KKU_x[i], KKU_y[i])
    else
        call BlzFrameSetAbsPoint(f, FRAMEPOINT_TOPLEFT, KKU_x[i], KKU_y[i])
    endif
    if KKU_tipo[i] == KKU_T_AREA and KKU_h[i] < KKU_AREA_H_MIN then
        call BlzFrameSetSize(f, KKU_w[i], KKU_AREA_H_MIN)
    else
        call BlzFrameSetSize(f, KKU_w[i], KKU_h[i])
    endif
    set KKU_a_anc[i]=KKU_anc[i]
    set KKU_a_x[i]=KKU_x[i]
    set KKU_a_y[i]=KKU_y[i]
    set KKU_a_w[i]=KKU_w[i]
    set KKU_a_h[i]=KKU_h[i]
    set KKU_nat=KKU_nat + 3
    set f=null
endfunction

function KKU_marca takes integer i returns nothing
    if i < 0 or i >= KKU_MAX then
        return
    endif
    if KKU_f[i] == null or KKU_esta_suja[i] then
        return
    endif
    if KKU_rc_ativa and i <= KKU_rc_n then
        return
    endif
    set KKU_esta_suja[i]=true
    set KKU_nsuja=KKU_nsuja + 1
    set KKU_suja[KKU_nsuja]=i
endfunction

function KKU_vis takes integer i, boolean v returns nothing
    set KKU_q_vis[i]=v
    call KKU_marca(i)
endfunction

function KKU_texto takes integer i, string s returns nothing
    if KKU_tipo[i] == KKU_T_CAMPO then
        return
    endif
    set KKU_q_txt[i]=s
    call KKU_marca(i)
endfunction

function KKU_tex takes integer i, string caminho returns nothing
    set KKU_q_tex[i]=caminho
    call KKU_marca(i)
endfunction

function KKU_poe takes integer i, real x, real y, real w, real h returns nothing
    if KKU_tipo[i] == KKU_T_AREA then
        if KKU_q_esc[i] > 0.0 and KKU_q_esc[i] < 1.0 then
            if h * KKU_q_esc[i] < KKU_AREA_H_MIN then
                set h=KKU_AREA_H_MIN / KKU_q_esc[i]
            endif
        elseif h < KKU_AREA_H_MIN then
            set h=KKU_AREA_H_MIN
        endif
    endif
    set KKU_x[i]=x
    set KKU_y[i]=y
    set KKU_w[i]=w
    set KKU_h[i]=h
    call KKU_marca(i)
endfunction

function KKU_alfa takes integer i, integer a returns nothing
    set KKU_q_alfa[i]=a
    call KKU_marca(i)
endfunction

function KKU_modelo takes integer i, string caminho returns nothing
    set KKU_q_mod[i]=caminho
    call KKU_marca(i)
endfunction

function KKU_escala takes integer i, real k returns nothing
    if KKU_tipo[i] == KKU_T_AREA and (k <= 0.0 or KKU_h[i] * k < KKU_AREA_H_MIN) then
        return
    endif
    set KKU_q_esc[i]=k
    call KKU_marca(i)
endfunction

function KKU_ativo takes integer i, boolean v returns nothing
    set KKU_q_ati[i]=v
    call KKU_marca(i)
endfunction

function KKU_ancora takes integer i, integer anc returns nothing
    set KKU_anc[i]=anc
    call KKU_marca(i)
endfunction

function KKU_nivel takes integer i, integer n returns nothing
    set KKU_q_niv[i]=n
    call KKU_marca(i)
endfunction

function KKU_simp_prep takes nothing returns nothing
    local integer a=0
    local integer k=0
    set KKU_sp_ok=true
    set KKU_sp_p=GetPlayerId(GetLocalPlayer())
    set KKU_sp_np=0
    set KKU_sp_nr=0
    set KKU_sp_topo=-1
    set KKU_jan_carimbo=KKU_jan_carimbo + 1
    set KKU_sp_base=KKU_jan_carimbo * 32
    if KKU_sp_p < 0 or KKU_sp_p >= KKU_JOGADORES then
        return
    endif
    set KKU_sp_np=KKU_npilha[KKU_sp_p]
    loop
        exitwhen a >= KKU_sp_np
        set k=KKU_pilha[KKU_sp_p * KKU_PILHA + a]
        set KKU_jan_pos[k]=KKU_sp_base + a
        if KKU_cob_w[k] > 0.0 then
            set KKU_sp_x[a]=KKU_cob_x[k]
            set KKU_sp_x2[a]=KKU_cob_x[k] + KKU_cob_w[k]
            set KKU_sp_y[a]=KKU_cob_y[k]
            set KKU_sp_y2[a]=KKU_cob_y[k] - KKU_cob_h[k]
        else
            set KKU_sp_x[a]=KKU_x[k]
            set KKU_sp_x2[a]=KKU_x[k] + KKU_w[k]
            set KKU_sp_y[a]=KKU_y[k]
            set KKU_sp_y2[a]=KKU_y[k] - KKU_h[k]
        endif
        set a=a + 1
    endloop
    set KKU_sp_nr=KKU_sp_np
    set a=0
    loop
        exitwhen a >= KKU_next[KKU_sp_p]
        set k=KKU_sp_p * KKU_EXT + a
        set KKU_sp_x[KKU_sp_nr]=KKU_ext_x[k]
        set KKU_sp_x2[KKU_sp_nr]=KKU_ext_x[k] + KKU_ext_w[k]
        set KKU_sp_y[KKU_sp_nr]=KKU_ext_y[k]
        set KKU_sp_y2[KKU_sp_nr]=KKU_ext_y[k] - KKU_ext_h[k]
        set KKU_sp_nr=KKU_sp_nr + 1
        set a=a + 1
    endloop
    if KKU_sp_nr == KKU_sp_np and KKU_sp_np > 0 then
        set KKU_sp_topo=KKU_sp_base + KKU_sp_np - 1
    endif
endfunction

function KKU_simp_tapado takes integer q returns boolean
    local integer i=KKU_alvo_i[KKU_alvo_de[q]]
    local integer a=KKU_jan_pos[KKU_simp_jan[q]] - KKU_sp_base
    local real x=KKU_x[i]
    local real y=KKU_y[i]
    local real x2=x + KKU_w[i]
    local real y2=y - KKU_h[i]
    if a < 0 or a >= KKU_sp_np then
        set a=-1
    endif
    loop
        set a=a + 1
        exitwhen a >= KKU_sp_nr
        if x < KKU_sp_x2[a] and KKU_sp_x[a] < x2 and y > KKU_sp_y2[a] and KKU_sp_y[a] > y2 then
            return true
        endif
    endloop
    return false
endfunction

function KKU_simp_um takes integer q returns nothing
    local boolean v=KKU_q_vis[q]
    local integer i=KKU_alvo_v[KKU_alvo_de[q]]
    if KKU_f[q] == null then
        return
    endif
    loop
        exitwhen not v or i <= 0
        set v=KKU_a_vis[i]
        set i=KKU_pai[i]
    endloop
    if v then
        if not KKU_sp_ok then
            call KKU_simp_prep()
        endif
        if KKU_sp_nr > 0 and KKU_jan_pos[KKU_simp_jan[q]] != KKU_sp_topo then
            set v=not KKU_simp_tapado(q)
        endif
    endif
    if v != KKU_a_vis[q] then
        call BlzFrameSetVisible(KKU_f[q], v)
        set KKU_a_vis[q]=v
        set KKU_nat=KKU_nat + 1
    endif
endfunction

function KKU_simp_some takes integer i, boolean tudo returns nothing
    local integer q=KKU_dr_ini[i]
    local integer c=KKU_dc_ini[i]
    loop
        exitwhen q <= 0
        if KKU_a_vis[q] and KKU_f[q] != null then
            call BlzFrameSetVisible(KKU_f[q], false)
            set KKU_a_vis[q]=false
            set KKU_nat=KKU_nat + 1
        endif
        set q=KKU_dr_prox[q]
    endloop
    loop
        exitwhen c <= 0
        if tudo or KKU_a_vis[c] then
            call KKU_simp_some(c, tudo)
        endif
        set c=KKU_dc_prox[c]
    endloop
endfunction

function KKU_simp_surge takes integer i returns nothing
    local integer q=KKU_dr_ini[i]
    local integer c=KKU_dc_ini[i]
    local integer a=0
    local integer d=0
    local boolean v=false
    local real x=0.0
    local real y=0.0
    local real x2=0.0
    local real y2=0.0
    loop
        exitwhen q <= 0
        set v=KKU_q_vis[q]
        if v and KKU_sp_nr > 0 then
            set a=KKU_jan_pos[KKU_simp_jan[q]]
            if a != KKU_sp_topo then
                set a=a - KKU_sp_base
                if a < 0 or a >= KKU_sp_np then
                    set a=-1
                endif
                set d=KKU_alvo_i[KKU_alvo_de[q]]
                set x=KKU_x[d]
                set y=KKU_y[d]
                set x2=x + KKU_w[d]
                set y2=y - KKU_h[d]
                loop
                    set a=a + 1
                    exitwhen a >= KKU_sp_nr
                    if x < KKU_sp_x2[a] and KKU_sp_x[a] < x2 and y > KKU_sp_y2[a] and KKU_sp_y[a] > y2 then
                        set v=false
                        exitwhen true
                    endif
                endloop
            endif
        endif
        if v != KKU_a_vis[q] and KKU_f[q] != null then
            call BlzFrameSetVisible(KKU_f[q], v)
            set KKU_a_vis[q]=v
            set KKU_nat=KKU_nat + 1
        endif
        set q=KKU_dr_prox[q]
    endloop
    loop
        exitwhen c <= 0
        if KKU_a_vis[c] then
            call KKU_simp_surge(c)
        endif
        set c=KKU_dc_prox[c]
    endloop
endfunction

function KKU_simp_muda takes integer i returns nothing
    local integer p=KKU_pai[i]
    loop
        exitwhen p <= 0
        if not KKU_a_vis[p] then
            return
        endif
        set p=KKU_pai[p]
    endloop
    call KKU_simp_some(i, false)
endfunction

function KKU_simp_surgem takes nothing returns nothing
    local integer k=1
    local integer i=0
    local integer p=0
    local boolean vale=false
    if not KKU_simp_suja then
        loop
            exitwhen k > KKU_nsm
            set i=KKU_sm_i[k]
            set vale=KKU_a_vis[i]
            set p=KKU_pai[i]
            loop
                exitwhen not vale or p <= 0
                if not KKU_a_vis[p] or KKU_sm_c[p] == KKU_sm_passe then
                    set vale=false
                endif
                set p=KKU_pai[p]
            endloop
            if vale then
                if not KKU_sp_ok then
                    call KKU_simp_prep()
                endif
                call KKU_simp_surge(i)
            endif
            set k=k + 1
        endloop
    endif
    set KKU_nsm=0
endfunction

function KKU_simp_pendentes takes nothing returns nothing
    local integer k=1
    loop
        exitwhen k > KKU_npf
        set KKU_pf_c[KKU_pf_i[k]]=false
        call KKU_simp_some(KKU_pf_i[k], true)
        set k=k + 1
    endloop
    set KKU_npf=0
endfunction

function KKU_simp_sozinhos takes nothing returns nothing
    local integer k=1
    loop
        exitwhen k > KKU_npr
        call KKU_simp_um(KKU_pr_q[k])
        set k=k + 1
    endloop
    set KKU_npr=0
    set k=1
    loop
        exitwhen k > KKU_nsu
        call KKU_simp_um(KKU_su_q[k])
        set k=k + 1
    endloop
    set KKU_nsu=0
endfunction

function KKU_simples_aplica takes nothing returns nothing
    local integer k=1
    set KKU_simp_suja=false
    call KKU_simp_prep()
    loop
        exitwhen k > KKU_nsraiz
        if KKU_a_vis[KKU_sraiz[k]] then
            call KKU_simp_surge(KKU_sraiz[k])
        endif
        set k=k + 1
    endloop
endfunction

function KKU_aplica takes nothing returns nothing
    local integer k=1
    local integer i
    local integer n=0
    local boolean novo
    local boolean mostra
    local framehandle f
    local integer teto=KKU_ap_teto
    local integer feitos=0
    set KKU_ap_teto=0
    if KKU_rc_ativa then
        return
    endif
    set KKU_sp_ok=false
    set KKU_nsm=0
    set KKU_nsu=0
    set KKU_sm_passe=KKU_sm_passe + 1
    if KKU_npf > 0 then
        call KKU_simp_pendentes()
    endif
    loop
        if teto > 0 then
            exitwhen feitos >= teto or KKU_nsuja <= 0
            set i=KKU_suja[KKU_nsuja]
            set KKU_nsuja=KKU_nsuja - 1
            set feitos=feitos + 1
        else
            exitwhen k > KKU_nsuja
            set i=KKU_suja[k]
            set k=k + 1
        endif
        set KKU_esta_suja[i]=false
        set f=KKU_f[i]
        if f != null then
            set novo=not KKU_a_ok[i]
            if novo then
                if not KKU_a_vis[i] and KKU_simp_dep[i] then
                    set KKU_nsm=KKU_nsm + 1
                    set KKU_sm_i[KKU_nsm]=i
                    set KKU_sm_c[i]=KKU_sm_passe
                endif
                set KKU_a_vis[i]=true
                set KKU_a_txt[i]=""
                set KKU_a_tex[i]=""
                set KKU_a_mod[i]=""
                set KKU_a_esc[i]=1.0
                set KKU_a_alfa[i]=255
                set KKU_a_ati[i]=true
                set KKU_a_niv[i]=0
                set novo=KKU_tipo[i] != KKU_T_EXTERNO or KKU_w[i] > 0.0 or KKU_h[i] > 0.0
            endif
            set mostra=KKU_q_vis[i] and not KKU_a_vis[i] and KKU_tipo[i] != KKU_T_ALVO_SIMP
            if not KKU_preso[i] and (novo or KKU_x[i] != KKU_a_x[i] or KKU_y[i] != KKU_a_y[i] or KKU_w[i] != KKU_a_w[i] or KKU_h[i] != KKU_a_h[i] or KKU_anc[i] != KKU_a_anc[i]) then
                if KKU_alvo_seg[i] > 0 then
                    call KKU_poe(KKU_alvo_seg[i], KKU_x[i], KKU_y[i], KKU_w[i], KKU_h[i])
                endif
                call KKU_posiciona(i)
            endif
            if KKU_tipo[i] != KKU_T_PAGINA and KKU_q_txt[i] != KKU_a_txt[i] then
                call BlzFrameSetText(f, KKU_q_txt[i])
                set KKU_a_txt[i]=KKU_q_txt[i]
                set n=n + 1
            endif
            if KKU_q_tex[i] != KKU_a_tex[i] then
                call BlzFrameSetTexture(f, KKU_q_tex[i], 0, true)
                set KKU_a_tex[i]=KKU_q_tex[i]
                set n=n + 1
            endif
            if KKU_q_mod[i] != KKU_a_mod[i] then
                call BlzFrameSetModel(f, KKU_q_mod[i], 0)
                call BlzFrameSetSpriteAnimate(f, 2, 0)
                set KKU_a_mod[i]=KKU_q_mod[i]
                set n=n + 2
            endif
            if KKU_q_esc[i] != KKU_a_esc[i] then
                call BlzFrameSetScale(f, KKU_q_esc[i])
                set KKU_a_esc[i]=KKU_q_esc[i]
                set n=n + 1
            endif
            if KKU_tipo[i] == KKU_T_ALVO_SIMP then
                set KKU_nsu=KKU_nsu + 1
                set KKU_su_q[KKU_nsu]=i
            elseif KKU_q_vis[i] != KKU_a_vis[i] then
                call BlzFrameSetVisible(f, KKU_q_vis[i])
                set KKU_a_vis[i]=KKU_q_vis[i]
                set n=n + 1
                if KKU_simp_dep[i] then
                    if KKU_q_vis[i] then
                        set KKU_nsm=KKU_nsm + 1
                        set KKU_sm_i[KKU_nsm]=i
                        set KKU_sm_c[i]=KKU_sm_passe
                    else
                        call KKU_simp_muda(i)
                    endif
                endif
            endif
            if KKU_q_niv[i] != KKU_a_niv[i] then
                call BlzFrameSetLevel(f, KKU_q_niv[i])
                set KKU_a_niv[i]=KKU_q_niv[i]
                set mostra=true
                set n=n + 1
            endif
            if KKU_q_alfa[i] != KKU_a_alfa[i] or mostra then
                call BlzFrameSetAlpha(f, KKU_q_alfa[i])
                set KKU_a_alfa[i]=KKU_q_alfa[i]
                set n=n + 1
            endif
            if KKU_q_ati[i] != KKU_a_ati[i] then
                call BlzFrameSetEnable(f, KKU_q_ati[i])
                set KKU_a_ati[i]=KKU_q_ati[i]
                set n=n + 1
            endif
            set KKU_a_ok[i]=true
        endif
    endloop
    set KKU_nat=KKU_nat + n
    if teto <= 0 then
        set KKU_nsuja=0
    endif
    if KKU_nsm > 0 then
        call KKU_simp_surgem()
    endif
    if KKU_npr + KKU_nsu > 0 then
        call KKU_simp_sozinhos()
    endif
    if KKU_simp_suja and KKU_rc_fase == 0 then
        if KKU_nsimp > 0 then
            call KKU_simples_aplica()
        else
            set KKU_simp_suja=false
        endif
    endif
    set f=null
endfunction

function KKU_img takes integer pai, integer papel, real x, real y, real w, real h returns integer
    local integer i
    if not KKU_pai_ok(pai) or not KKU_livre() then
        return KKU_MAX
    endif
    set i=KKU_guarda(BlzCreateFrameByType("BACKDROP", "KKUImg", KKU_f[pai], "", 0), KKU_T_IMG, pai, papel, x, y, w, h)
    call KKU_posiciona(i)
    call BlzFrameSetTexture(KKU_f[i], KKU_tema_tex[papel], 0, true)
    set KKU_q_tex[i]=KKU_tema_tex[papel]
    set KKU_a_tex[i]=KKU_tema_tex[papel]
    set KKU_nat=KKU_nat + 1
    return i
endfunction

function KKU_txt takes integer pai, integer fonte, real x, real y, real w, real h returns integer
    local integer i
    if not KKU_pai_ok(pai) or not KKU_livre() then
        return KKU_MAX
    endif
    set i=KKU_guarda(BlzCreateFrameByType("TEXT", "KKUTxt", KKU_f[pai], KKU_fonte[fonte], 0), KKU_T_TXT, pai, fonte, x, y, w, h)
    call KKU_posiciona(i)
    call BlzFrameSetTextAlignment(KKU_f[i], TEXT_JUSTIFY_TOP, TEXT_JUSTIFY_LEFT)
    call BlzFrameSetText(KKU_f[i], "")
    call BlzFrameSetEnable(KKU_f[i], false)
    set KKU_q_ati[i]=false
    set KKU_a_ati[i]=false
    set KKU_alin[i]=0
    set KKU_nat=KKU_nat + 3
    return i
endfunction

function KKU_caixa takes integer pai, integer papel, real x, real y, real w, real h returns integer
    local integer i
    local framehandle f
    if not KKU_pai_ok(pai) or not KKU_livre() then
        return KKU_MAX
    endif
    if KKU_tema_fdf[papel] != null and KKU_tema_fdf[papel] != "" then
        set f=BlzCreateFrame(KKU_tema_fdf[papel], KKU_f[pai], 0, 0)
        set i=KKU_guarda(f, KKU_T_CAIXA, pai, papel, x, y, w, h)
    else
        set f=BlzCreateFrameByType("BACKDROP", "KKUCaixa", KKU_f[pai], "", 0)
        set i=KKU_guarda(f, KKU_T_CAIXA, pai, papel, x, y, w, h)
        call BlzFrameSetTexture(f, KKU_tema_tex[papel], 0, true)
        set KKU_q_tex[i]=KKU_tema_tex[papel]
        set KKU_a_tex[i]=KKU_tema_tex[papel]
        set KKU_nat=KKU_nat + 1
    endif
    call KKU_posiciona(i)
    set f=null
    return i
endfunction

function KKU_pagina takes integer pai returns integer
    local integer i
    if not KKU_pai_ok(pai) or not KKU_livre() then
        return KKU_MAX
    endif
    set i=KKU_guarda(BlzCreateFrameByType("FRAME", "KKUPagina", KKU_f[pai], "", 0), KKU_T_PAGINA, pai, 0, KKU_x[pai], KKU_y[pai], KKU_w[pai], KKU_h[pai])
    call KKU_posiciona(i)
    return i
endfunction

function KKU_sprite takes integer pai returns integer
    local integer i
    if not KKU_pai_ok(pai) or not KKU_livre() then
        return KKU_MAX
    endif
    set i=KKU_guarda(BlzCreateFrameByType("SPRITE", "KKUSprite", KKU_f[pai], "", 0), KKU_T_SPRITE, pai, 0, KKU_x[pai], KKU_y[pai] - KKU_h[pai] + 0.001, 0.001, 0.001)
    call KKU_posiciona(i)
    return i
endfunction

function KKU_adota takes framehandle f returns integer
    if f == null or not KKU_livre() then
        return KKU_MAX
    endif
    return KKU_guarda(f, KKU_T_EXTERNO, 0, 0, 0.0, 0.0, 0.0, 0.0)
endfunction

function KKU_campo takes integer pai, real x, real y, real w, real h, integer limite returns integer
    local integer i
    local framehandle f
    if not KKU_pai_ok(pai) or not KKU_livre() then
        return KKU_MAX
    endif
    if limite > KKU_CAMPO_MAX then
        set limite=KKU_CAMPO_MAX
    endif
    set f=BlzCreateFrameByType("EDITBOX", "KKUCampo", KKU_f[pai], KKU_MODELO_CAMPO, 0)
    set i=KKU_guarda(f, KKU_T_CAMPO, pai, limite, x, y, w, h)
    call KKU_posiciona(i)
    call BlzFrameSetTextSizeLimit(f, limite)
    set KKU_nat=KKU_nat + 1
    set KKU_ncampo=KKU_ncampo + 1
    set KKU_campos[KKU_ncampo]=i
    call SaveInteger(KKU_ht, GetHandleId(f), 2, i)
    call BlzTriggerRegisterFrameEvent(KKU_t_texto, f, FRAMEEVENT_EDITBOX_TEXT_CHANGED)
    call BlzTriggerRegisterFrameEvent(KKU_t_texto, f, FRAMEEVENT_EDITBOX_ENTER)
    set f=null
    return i
endfunction

function KKU_campo_poe takes integer i, string s returns nothing
    if i < 1 or i >= KKU_MAX then
        return
    endif
    if KKU_tipo[i] != KKU_T_CAMPO or KKU_f[i] == null or not KKU_vivo(i) then
        return
    endif
    call BlzFrameSetText(KKU_f[i], s)
    set KKU_nat=KKU_nat + 1
endfunction

function KKU_campo_foco takes integer i, boolean v returns nothing
    if i < 1 or i >= KKU_MAX then
        return
    endif
    if KKU_tipo[i] != KKU_T_CAMPO or KKU_f[i] == null or not KKU_vivo(i) then
        return
    endif
    call BlzFrameSetFocus(KKU_f[i], v)
    set KKU_nat=KKU_nat + 1
endfunction

function KKU_area takes integer pai, real x, real y, real w, real h returns integer
    local integer i
    local framehandle f
    if h < KKU_AREA_H_MIN then
        set KKU_cheio=KKU_cheio + 1
        return KKU_MAX
    endif
    if not KKU_pai_ok(pai) or not KKU_livre() then
        return KKU_MAX
    endif
    set f=BlzCreateFrame(KKU_MODELO_AREA, KKU_f[pai], 0, 0)
    if f == null then
        return KKU_txt(pai, KKU_F_PEQUENA, x, y, w, h)
    endif
    set i=KKU_guarda(f, KKU_T_AREA, pai, 0, x, y, w, h)
    call KKU_posiciona(i)
    set f=null
    return i
endfunction

function KKU_visivel takes integer i returns boolean
    local integer k=0
    loop
        exitwhen i <= 0 or k > 64
        if not KKU_q_vis[i] then
            return false
        endif
        set i=KKU_pai[i]
        set k=k + 1
    endloop
    return true
endfunction

function KKU_alvo_em takes boolean so_pos returns integer
    local real mx=0.0
    local real my=0.0
    local integer t=KKU_nalvo
    local integer i=0
    if BlzGetLocalClientWidth() <= 0 or BlzGetLocalClientHeight() <= 0 then
        return 0
    endif
    set mx=BlzPixelToFrameX(BlzGetMouseScreenPosX())
    set my=BlzPixelToFrameY(BlzGetMouseScreenPosY())
    loop
        exitwhen t < 1
        if (not so_pos or KKU_alvo_q[t] == 0) and KKU_alvo_on[t] then
            set i=KKU_alvo_i[t]
            if not KKU_preso[i] and KKU_x[i] <= mx and mx <= KKU_x[i] + KKU_w[i] and KKU_y[i] - KKU_h[i] <= my and my <= KKU_y[i] then
                if KKU_visivel(KKU_alvo_v[t]) then
                    return t
                endif
            endif
        endif
        set t=t - 1
    endloop
    return 0
endfunction

function KKU_sob_mouse takes nothing returns integer
    return KKU_alvo_em(false)
endfunction

function KKU_alvo_posicao takes integer cod returns integer
    local integer t=1
    if cod == 0 then
        return 0
    endif
    loop
        exitwhen t > KKU_nalvo
        if KKU_alvo_q[t] == 0 and KKU_alvo_cod[t] == cod then
            return t
        endif
        set t=t + 1
    endloop
    return 0
endfunction

function KKU_cod_posicao takes integer cod returns boolean
    return KKU_alvo_posicao(cod) > 0
endfunction

function KKU_foco_par takes framehandle f returns nothing
    call BlzFrameSetEnable(f, false)
    call BlzFrameSetEnable(f, true)
    set KKU_nat=KKU_nat + 2
endfunction

function KKU_foco_pia takes nothing returns nothing
    call BlzFrameSetEnable(KKU_f_foco, true)
    call BlzFrameSetFocus(KKU_f_foco, true)
    call BlzFrameSetFocus(KKU_f_foco, false)
    call BlzFrameSetEnable(KKU_f_foco, false)
    set KKU_nat=KKU_nat + 4
endfunction

function KKU_solta_foco takes framehandle f, integer q returns nothing
    if KKU_foco_modo == 1 then
        call KKU_foco_par(f)
    elseif KKU_foco_modo == 2 then
        if KKU_f_foco != null then
            call KKU_foco_pia()
        else
            call KKU_foco_par(f)
        endif
    elseif KKU_foco_modo == 3 then
        set KKU_foco_pend=q
    elseif KKU_foco_modo == 4 then
        call BlzFrameSetFocus(f, false)
        set KKU_nat=KKU_nat + 1
    endif
endfunction

function KKU_ev_clique takes nothing returns nothing
    local framehandle f=BlzGetTriggerFrame()
    local player p=GetTriggerPlayer()
    local integer t=LoadInteger(KKU_ht, GetHandleId(f), 1)
    if GetLocalPlayer() == p and t > 0 then
        if KKU_tipo[KKU_alvo_q[t]] == KKU_T_ALVO and KKU_alvo_on[t] then
            call KKU_solta_foco(f, KKU_alvo_q[t])
        endif
    endif
    if t > 0 then
        if KKU_alvo_cod[t] == KKU_COD_MENU then
            call KKU_args(GetPlayerId(p), 0, 0, 0.0, 0)
            call KKU_chama(KKU_AO_MENU)
        else
            call KKU_args(GetPlayerId(p), KKU_alvo_cod[t], 0, 0.0, 0)
            set KKU_c_alvo=t
            call KKU_chama(KKU_AO_CLIQUE)
        endif
    endif
    set f=null
    set p=null
endfunction

function KKU_ev_fundo takes nothing returns nothing
    local integer t=0
    local integer k=1
    if GetLocalPlayer() == GetTriggerPlayer() then
        loop
            exitwhen k > KKU_ncampo
            call KKU_campo_foco(KKU_campos[k], false)
            set k=k + 1
        endloop
        if KKU_f_foco != null then
            call BlzFrameSetFocus(KKU_f_foco, false)
            set KKU_nat=KKU_nat + 1
        endif
        set t=KKU_alvo_em(true)
        if t > 0 then
            call BlzSendSyncData(KKU_SINC, I2S(KKU_alvo_cod[t]))
        endif
    endif
endfunction

function KKU_ev_sinc takes nothing returns nothing
    local integer cod=S2I(BlzGetTriggerSyncData())
    local integer t=KKU_alvo_posicao(cod)
    if t > 0 then
        call KKU_args(GetPlayerId(GetTriggerPlayer()), cod, 0, 0.0, 0)
        set KKU_c_alvo=t
        call KKU_chama(KKU_AO_CLIQUE)
    endif
endfunction

function KKU_ev_texto takes nothing returns nothing
    local integer i=LoadInteger(KKU_ht, GetHandleId(BlzGetTriggerFrame()), 2)
    local real v=0.0
    if i < 1 or i >= KKU_MAX then
        return
    endif
    if KKU_tipo[i] != KKU_T_CAMPO then
        return
    endif
    if BlzGetTriggerFrameEvent() == FRAMEEVENT_EDITBOX_ENTER then
        set v=1.0
    endif
    set KKU_c_txt=BlzGetTriggerFrameText()
    call KKU_args(GetPlayerId(GetTriggerPlayer()), 0, 0, v, i)
    call KKU_chama(KKU_AO_TEXTO)
endfunction

function KKU_ev_roda takes nothing returns nothing
    local integer h=GetHandleId(BlzGetTriggerFrame())
    local integer t=LoadInteger(KKU_ht, h, 1)
    local integer cod=0
    local integer id=0
    if t > 0 then
        set cod=KKU_alvo_cod[t]
    else
        set id=LoadInteger(KKU_ht, h, 3)
    endif
    call KKU_args(GetPlayerId(GetTriggerPlayer()), cod, 0, BlzGetTriggerFrameValue(), id)
    set KKU_c_alvo=t
    call KKU_chama(KKU_AO_RODA)
endfunction

function KKU_esconde takes integer i returns nothing
    if KKU_pai_ok(i) then
        if KKU_simp_dep[i] and not KKU_pf_c[i] then
            set KKU_pf_c[i]=true
            set KKU_npf=KKU_npf + 1
            set KKU_pf_i[KKU_npf]=i
        endif
        call BlzFrameSetVisible(KKU_f[i], false)
        set KKU_q_vis[i]=false
        set KKU_a_vis[i]=false
        set KKU_nat=KKU_nat + 1
    endif
endfunction

function KKU_alinha_f takes framehandle f, integer modo returns nothing
    if modo == KKU_AL_MEIO_ESQ then
        call BlzFrameSetTextAlignment(f, TEXT_JUSTIFY_MIDDLE, TEXT_JUSTIFY_LEFT)
    elseif modo == KKU_AL_MEIO_CENTRO then
        call BlzFrameSetTextAlignment(f, TEXT_JUSTIFY_MIDDLE, TEXT_JUSTIFY_CENTER)
    elseif modo == KKU_AL_MEIO_DIR then
        call BlzFrameSetTextAlignment(f, TEXT_JUSTIFY_MIDDLE, TEXT_JUSTIFY_RIGHT)
    elseif modo == KKU_AL_TOPO_CENTRO then
        call BlzFrameSetTextAlignment(f, TEXT_JUSTIFY_TOP, TEXT_JUSTIFY_CENTER)
    else
        call BlzFrameSetTextAlignment(f, TEXT_JUSTIFY_TOP, TEXT_JUSTIFY_LEFT)
    endif
    set KKU_nat=KKU_nat + 1
endfunction

function KKU_alinha takes integer i, integer modo returns nothing
    if not KKU_pai_ok(i) or modo < KKU_AL_TOPO_ESQ or modo > KKU_AL_TOPO_CENTRO then
        return
    endif
    if KKU_tipo[i] != KKU_T_TXT then
        return
    endif
    call KKU_alinha_f(KKU_f[i], modo)
    set KKU_alin[i]=modo
endfunction

function KKU_rotulo takes integer i, string s, boolean centro returns nothing
    if not KKU_pai_ok(i) then
        return
    endif
    if centro then
        call BlzFrameSetTextAlignment(KKU_f[i], TEXT_JUSTIFY_MIDDLE, TEXT_JUSTIFY_CENTER)
        set KKU_alin[i]=2
    else
        call BlzFrameSetTextAlignment(KKU_f[i], TEXT_JUSTIFY_MIDDLE, TEXT_JUSTIFY_LEFT)
        set KKU_alin[i]=1
    endif
    call BlzFrameSetText(KKU_f[i], s)
    set KKU_q_txt[i]=s
    set KKU_a_txt[i]=s
    set KKU_nat=KKU_nat + 2
endfunction

function KKU_dica_prende takes nothing returns nothing
    local framehandle c=KKU_f[KKU_i_dica]
    local framehandle t=KKU_f[KKU_i_dica_txt]
    if KKU_i_dica > 0 and KKU_i_dica_txt > 0 and c != null and t != null then
        call BlzFrameClearAllPoints(c)
        call BlzFrameSetSize(c, KKU_DICA_W + 2.0 * KKU_DICA_FOLGA, 2.0 * KKU_DICA_FOLGA)
        call BlzFrameSetPoint(c, FRAMEPOINT_BOTTOMLEFT, t, FRAMEPOINT_BOTTOMLEFT, -KKU_DICA_FOLGA, -KKU_DICA_FOLGA)
        call BlzFrameSetPoint(c, FRAMEPOINT_TOPRIGHT, t, FRAMEPOINT_TOPRIGHT, KKU_DICA_FOLGA, KKU_DICA_FOLGA)
        set KKU_nat=KKU_nat + 4
    endif
    set c=null
    set t=null
endfunction

function KKU_foco_cria takes nothing returns nothing
    set KKU_f_foco=BlzCreateFrameByType("EDITBOX", "KKUFoco", KKU_f[0], KKU_MODELO_CAMPO, 0)
    if KKU_f_foco != null then
        call BlzFrameSetAbsPoint(KKU_f_foco, FRAMEPOINT_BOTTOMLEFT, 0.0, 0.0)
        call BlzFrameSetSize(KKU_f_foco, 0.001, 0.001)
        call BlzFrameSetAlpha(KKU_f_foco, 0)
        call BlzFrameSetEnable(KKU_f_foco, false)
        set KKU_nat=KKU_nat + 4
    endif
endfunction

function KKU_mouse_cria takes nothing returns nothing
    local integer papel=KKU_P_CAIXA
    if KKU_mouse_tent then
        return
    endif
    set KKU_mouse_tent=true
    call KKU_foco_cria()
    if not KKU_livres(3) then
        return
    endif
    set KKU_i_realce=KKU_img(0, KKU_P_REALCE, 0.0, 0.1, 0.01, 0.01)
    call KKU_esconde(KKU_i_realce)
    if KKU_tema_fdf[KKU_P_BORDA_9] != null and KKU_tema_fdf[KKU_P_BORDA_9] != "" then
        set papel=KKU_P_BORDA_9
    endif
    set KKU_i_dica=KKU_caixa(0, papel, 0.0, 0.1, KKU_DICA_W + 2.0 * KKU_DICA_FOLGA, 2.0 * KKU_DICA_FOLGA)
    call KKU_esconde(KKU_i_dica)
    set KKU_i_dica_txt=KKU_txt(KKU_i_dica, KKU_F_PEQUENA, KKU_DICA_FOLGA, 0.1 - KKU_DICA_FOLGA, KKU_DICA_W, 0.0)
    set KKU_preso[KKU_i_dica]=true
    call KKU_dica_prende()
    call BlzFrameSetEnable(KKU_f[KKU_i_dica], false)
    set KKU_q_ati[KKU_i_dica]=false
    set KKU_a_ati[KKU_i_dica]=false
    set KKU_nat=KKU_nat + 1
    call KKU_nivel(KKU_i_realce, 8)
    call KKU_nivel(KKU_i_dica, 9)
    call KKU_nivel(KKU_i_dica_txt, 9)
endfunction

function KKU_dica takes integer cod, string texto returns nothing
    if KKU_ht == null then
        return
    endif
    if StringLength(texto) > KKU_DICA_MAX then
        set texto=SubString(texto, 0, KKU_DICA_MAX)
    endif
    call SaveStr(KKU_ht, cod, 0, texto)
    set KKU_dica_ver=KKU_dica_ver + 1
endfunction

function KKU_dica_acima takes integer cod, real x0, real x1 returns nothing
    if KKU_ht == null then
        return
    endif
    if x1 - x0 <= 2.0 * KKU_DICA_FOLGA then
        set x0=0.0
        set x1=0.0
    endif
    call SaveReal(KKU_ht, cod, 1, x0)
    call SaveReal(KKU_ht, cod, 2, x1)
    set KKU_dica_ver=KKU_dica_ver + 1
endfunction

function KKU_alvo_segue takes integer t, integer v returns nothing
    local integer q=KKU_alvo_q[t]
    local integer i=v
    set KKU_alvo_v[t]=v
    if q <= 0 then
        return
    endif
    if KKU_tipo[q] != KKU_T_ALVO_SIMP then
        return
    endif
    set KKU_dr_prox[q]=KKU_dr_ini[v]
    set KKU_dr_ini[v]=q
    loop
        exitwhen i <= 0
        if not KKU_simp_dep[i] then
            set KKU_simp_dep[i]=true
            if KKU_pai[i] > 0 then
                set KKU_dc_prox[i]=KKU_dc_ini[KKU_pai[i]]
                set KKU_dc_ini[KKU_pai[i]]=i
            else
                set KKU_nsraiz=KKU_nsraiz + 1
                set KKU_sraiz[KKU_nsraiz]=i
            endif
        endif
        set KKU_simp_jan[q]=i
        set i=KKU_pai[i]
    endloop
    set KKU_npr=KKU_npr + 1
    set KKU_pr_q[KKU_npr]=q
endfunction

function KKU_alvo_modo takes integer pai, integer i_desenho, integer cod, boolean roda, integer modo returns integer
    local integer t
    local integer q=0
    local framehandle f=null
    local integer segue=KKU_segue_prox
    set KKU_segue_prox=0
    set KKU_ult_alvo=0
    if not KKU_pai_ok(pai) or not KKU_pai_ok(i_desenho) or KKU_nalvo >= KKU_MAX - 1 then
        return 0
    endif
    if modo != KKU_M_POSICAO then
        if not KKU_livres(1) then
            return 0
        endif
    elseif not KKU_livres(0) then
        return 0
    endif
    call KKU_mouse_cria()
    if modo != KKU_M_POSICAO then
        if modo == KKU_M_SIMPLES and KKU_toc_ok then
            set f=BlzCreateSimpleFrame("KKUAlvoSimples", KKU_f_console, 0)
        endif
        if f != null then
            set q=KKU_guarda(f, KKU_T_ALVO_SIMP, pai, cod, KKU_x[i_desenho], KKU_y[i_desenho], KKU_w[i_desenho], KKU_h[i_desenho])
            set KKU_roda_ped[q]=roda
            set roda=false
            set KKU_nsimp=KKU_nsimp + 1
            set KKU_simp_q[KKU_nsimp]=q
        elseif modo == KKU_M_TEXTO then
            set f=BlzCreateFrameByType("TEXT", "KKUAlvoT", KKU_f[pai], "", 0)
            set q=KKU_guarda(f, KKU_T_ALVO_TXT, pai, cod, KKU_x[i_desenho], KKU_y[i_desenho], KKU_w[i_desenho], KKU_h[i_desenho])
        else
            set f=BlzCreateFrameByType("BUTTON", "KKUAlvo", KKU_f[pai], "", 0)
            set q=KKU_guarda(f, KKU_T_ALVO, pai, cod, KKU_x[i_desenho], KKU_y[i_desenho], KKU_w[i_desenho], KKU_h[i_desenho])
        endif
        call KKU_posiciona(q)
        call BlzTriggerRegisterFrameEvent(KKU_t_clique, f, FRAMEEVENT_CONTROL_CLICK)
        set KKU_roda[q]=roda
        if roda then
            call BlzTriggerRegisterFrameEvent(KKU_t_roda, f, FRAMEEVENT_MOUSE_WHEEL)
        endif
    endif
    set KKU_nalvo=KKU_nalvo + 1
    set t=KKU_nalvo
    set KKU_alvo_i[t]=i_desenho
    set KKU_alvo_cod[t]=cod
    set KKU_alvo_q[t]=q
    set KKU_alvo_on[t]=true
    if q > 0 then
        call SaveInteger(KKU_ht, GetHandleId(f), 1, t)
        set KKU_alvo_de[q]=t
        set KKU_alvo_seg[i_desenho]=q
    endif
    if segue > 0 then
        call KKU_alvo_segue(t, segue)
    else
        call KKU_alvo_segue(t, i_desenho)
    endif
    set KKU_ult_alvo=t
    set f=null
    return t
endfunction

function KKU_alvo takes integer pai, integer i_desenho, integer cod, boolean roda returns integer
    return KKU_alvo_modo(pai, i_desenho, cod, roda, KKU_alvo_padrao)
endfunction

function KKU_janela_cobre takes integer j, real x, real y, real w, real h returns nothing
    if j < 1 or j >= KKU_MAX then
        return
    endif
    set KKU_cob_x[j]=x
    set KKU_cob_y[j]=y
    set KKU_cob_w[j]=w
    set KKU_cob_h[j]=h
    set KKU_simp_suja=true
endfunction

function KKU_cobre_externo takes integer pid, integer id, real x, real y, real w, real h returns nothing
    local integer k=0
    local integer b
    if pid < 0 or pid >= KKU_JOGADORES or id == 0 then
        return
    endif
    set b=pid * KKU_EXT
    loop
        exitwhen k >= KKU_next[pid] or KKU_ext_id[b + k] == id
        set k=k + 1
    endloop
    if k >= KKU_next[pid] then
        if KKU_next[pid] >= KKU_EXT then
            set KKU_cheio=KKU_cheio + 1
            return
        endif
        set KKU_next[pid]=KKU_next[pid] + 1
    endif
    set KKU_ext_id[b + k]=id
    set KKU_ext_x[b + k]=x
    set KKU_ext_y[b + k]=y
    set KKU_ext_w[b + k]=w
    set KKU_ext_h[b + k]=h
    set KKU_simp_suja=true
endfunction

function KKU_descobre_externo takes integer pid, integer id returns nothing
    local integer k=0
    local integer b
    if pid < 0 or pid >= KKU_JOGADORES or id == 0 then
        return
    endif
    set b=pid * KKU_EXT
    loop
        exitwhen k >= KKU_next[pid] or KKU_ext_id[b + k] == id
        set k=k + 1
    endloop
    if k >= KKU_next[pid] then
        return
    endif
    set KKU_next[pid]=KKU_next[pid] - 1
    set KKU_ext_id[b + k]=KKU_ext_id[b + KKU_next[pid]]
    set KKU_ext_x[b + k]=KKU_ext_x[b + KKU_next[pid]]
    set KKU_ext_y[b + k]=KKU_ext_y[b + KKU_next[pid]]
    set KKU_ext_w[b + k]=KKU_ext_w[b + KKU_next[pid]]
    set KKU_ext_h[b + k]=KKU_ext_h[b + KKU_next[pid]]
    set KKU_ext_id[b + KKU_next[pid]]=0
    set KKU_simp_suja=true
endfunction

function KKU_alvo_vis takes integer t, boolean v returns nothing
    if t < 1 or t > KKU_nalvo then
        return
    endif
    set KKU_alvo_on[t]=v
    if KKU_alvo_q[t] > 0 then
        call KKU_vis(KKU_alvo_q[t], v)
    endif
endfunction

function KKU_alvo_mouse takes integer t, boolean v returns nothing
    if t < 1 or t > KKU_nalvo then
        return
    endif
    set KKU_alvo_on[t]=v
endfunction

function KKU_fundo takes integer pai, real x, real y, real w, real h, boolean roda returns integer
    local integer i
    if not KKU_pai_ok(pai) or not KKU_livre() then
        return KKU_MAX
    endif
    set i=KKU_guarda(BlzCreateFrameByType("TEXT", "KKUFundo", KKU_f[pai], "", 0), KKU_T_FUNDO, pai, 0, x, y, w, h)
    call KKU_posiciona(i)
    call SaveInteger(KKU_ht, GetHandleId(KKU_f[i]), 1, 0)
    call SaveInteger(KKU_ht, GetHandleId(KKU_f[i]), 3, i)
    call BlzTriggerRegisterFrameEvent(KKU_t_fundo, KKU_f[i], FRAMEEVENT_CONTROL_CLICK)
    set KKU_roda[i]=roda
    if roda then
        call BlzTriggerRegisterFrameEvent(KKU_t_roda, KKU_f[i], FRAMEEVENT_MOUSE_WHEEL)
    endif
    return i
endfunction

function KKU_botao_modo takes integer pai, integer papel, string rotulo, real x, real y, real w, real h, integer cod, integer modo returns integer
    local integer b
    if not KKU_pai_ok(pai) or not KKU_livres(4) then
        return KKU_MAX
    endif
    set b=KKU_caixa(pai, papel, x, y, w, h)
    call KKU_caixa(b, KKU_P_BOTAO_BORDA, x, y, w, h)
    call KKU_rotulo(KKU_txt(b, KKU_F_NORMAL, x, y, w, h), rotulo, true)
    call KKU_alvo_modo(b, b, cod, false, modo)
    return b
endfunction

function KKU_botao_papel takes integer pai, integer papel, string rotulo, real x, real y, real w, real h, integer cod returns integer
    return KKU_botao_modo(pai, papel, rotulo, x, y, w, h, cod, KKU_alvo_padrao)
endfunction

function KKU_botao takes integer pai, string rotulo, real x, real y, real w, real h, integer cod returns integer
    return KKU_botao_papel(pai, KKU_P_BOTAO, rotulo, x, y, w, h, cod)
endfunction

function KKU_menu_prende takes framehandle h returns nothing
    local integer b=KKU_i_menu
    local integer k
    local integer q
    local framehandle c
    if b <= 0 or h == null then
        return
    endif
    set c=KKU_f[b]
    if c == null then
        return
    endif
    call BlzFrameClearAllPoints(c)
    call BlzFrameSetPoint(c, FRAMEPOINT_TOPLEFT, h, FRAMEPOINT_BOTTOMLEFT, 0.0, -0.004)
    call BlzFrameSetSize(c, KKU_w[b], KKU_h[b])
    set KKU_nat=KKU_nat + 3
    set k=1
    loop
        exitwhen k > 3
        set q=b + k
        if k == 3 then
            set q=KKU_alvo_seg[b]
        endif
        if q > 0 and KKU_f[q] != null and KKU_pai[q] == b then
            set KKU_preso[q]=true
            call BlzFrameClearAllPoints(KKU_f[q])
            call BlzFrameSetAllPoints(KKU_f[q], c)
            set KKU_nat=KKU_nat + 2
        endif
        set k=k + 1
    endloop
    set c=null
endfunction

function KKU_menu_botao takes nothing returns integer
    local framehandle f
    local integer b
    if not KKU_BOTAO_MENU then
        return 0
    endif
    if KKU_i_menu > 0 then
        return KKU_i_menu
    endif
    if KKU_i_borda <= 0 then
        set f=BlzGetFrameByName("ConsoleUIBackdrop", 0)
        if f == null or not KKU_livres(5) then
            set f=null
            return 0
        endif
        set KKU_i_borda=KKU_adota(f)
        set f=null
    endif
    set b=KKU_botao_modo(KKU_i_borda, KKU_P_BOTAO, "Menu (" + KKU_TECLA_NOME + ")", 0.0, 0.0, 0.070, 0.022, KKU_COD_MENU, KKU_M_BOTAO)
    if b == KKU_MAX then
        return 0
    endif
    set KKU_i_menu=b
    set KKU_preso[b]=true
    call KKU_menu_prende(BlzGetOriginFrame(ORIGIN_FRAME_HERO_BUTTON, IMaxBJ(IMinBJ(KKU_HEROIS_NA_BARRA, 7), 1) - 1))
    return b
endfunction

function KKU_linha takes integer pai, real x, real y, real w, real h, integer cod returns integer
    local integer l
    local integer k
    if not KKU_pai_ok(pai) or not KKU_livres(5) then
        return KKU_MAX
    endif
    set l=KKU_caixa(pai, KKU_P_CAIXA, x, y, w, h)
    call KKU_esconde(KKU_caixa(pai, KKU_P_CAIXA_ATIVA, x, y, w, h))
    set KKU_lin_ico[l]=KKU_img(pai, KKU_P_ICONE_PADRAO, x + 0.002, y - 0.002, h - 0.004, h - 0.004)
    set k=KKU_txt(pai, KKU_F_NORMAL, x + h + 0.002, y, w - h - 0.002, h)
    call KKU_rotulo(k, "", false)
    set KKU_rot[k]=""
    set KKU_lin_txt[l]=k
    set KKU_lin_info[l]=0
    set KKU_lin_marca[l]=0
    set KKU_lin_cor[l]=KKU_cor_inativo
    set KKU_segue_prox=k
    call KKU_alvo(k, l, cod, false)
    return l
endfunction

function KKU_linha_op takes integer pai, real x, real y, real w, real h, integer cod, boolean ico, boolean info, boolean roda returns integer
    local integer l
    local integer k
    local integer n=4
    local real tx=x + 0.006
    local real tw
    if ico then
        set n=n + 2
    endif
    if info then
        set n=n + 1
    endif
    if not KKU_pai_ok(pai) or not KKU_livres(n) then
        return KKU_MAX
    endif
    set l=KKU_caixa(pai, KKU_P_CAIXA, x, y, w, h)
    call KKU_esconde(KKU_caixa(pai, KKU_P_CAIXA_ATIVA, x, y, w, h))
    set KKU_lin_ico[l]=0
    set KKU_lin_info[l]=0
    set KKU_lin_marca[l]=0
    if ico then
        set KKU_lin_marca[l]=KKU_img(pai, KKU_P_MARCA, x + 0.001, y - 0.001, h - 0.002, h - 0.002)
        call KKU_esconde(KKU_lin_marca[l])
        set KKU_lin_ico[l]=KKU_img(pai, KKU_P_ICONE_PADRAO, x + 0.003, y - 0.003, h - 0.006, h - 0.006)
        set tx=x + h + 0.002
    endif
    set tw=x + w - tx - 0.004
    if info then
        set tw=tw - 0.078
    endif
    set k=KKU_txt(pai, KKU_F_PEQUENA, tx, y, tw, h)
    call KKU_rotulo(k, "", not ico)
    set KKU_rot[k]=""
    set KKU_lin_txt[l]=k
    set KKU_lin_cor[l]=KKU_cor_inativo
    if info then
        set KKU_lin_info[l]=KKU_txt(pai, KKU_F_PEQUENA, x + w - 0.082, y, 0.078, h)
        call KKU_alinha(KKU_lin_info[l], KKU_AL_MEIO_DIR)
    endif
    set KKU_segue_prox=k
    call KKU_alvo(k, l, cod, roda)
    return l
endfunction

function KKU_linha_texto takes integer l, string s returns nothing
    local integer k
    if l < 1 or l >= KKU_MAX then
        return
    endif
    set k=KKU_lin_txt[l]
    if k <= 0 then
        return
    endif
    set KKU_rot[k]=s
    call KKU_texto(k, KKU_lin_cor[l] + s + "|r")
endfunction

function KKU_linha_mostra takes integer l, boolean v, boolean ativa, boolean travada returns nothing
    local string cor=KKU_cor_inativo
    local integer k
    if l < 1 or l >= KKU_MAX - 1 then
        return
    endif
    set k=KKU_lin_txt[l]
    if k <= 0 then
        return
    endif
    if travada then
        set cor=KKU_cor_travado
    elseif ativa then
        set cor=KKU_cor_ativo
    endif
    call KKU_vis(l, v and not ativa)
    call KKU_vis(l + 1, v and ativa)
    if KKU_lin_marca[l] > 0 then
        call KKU_vis(KKU_lin_marca[l], v and ativa)
    endif
    if KKU_lin_ico[l] > 0 then
        call KKU_vis(KKU_lin_ico[l], v)
    endif
    call KKU_vis(k, v)
    if KKU_lin_info[l] > 0 then
        call KKU_vis(KKU_lin_info[l], v)
    endif
    set KKU_lin_cor[l]=cor
    call KKU_texto(k, cor + KKU_rot[k] + "|r")
endfunction

function KKU_linha_estado takes integer i, boolean ativa, boolean travada returns nothing
    call KKU_linha_mostra(i, true, ativa, travada)
endfunction

function KKU_linha_info takes integer l, string s returns nothing
    if l < 1 or l >= KKU_MAX then
        return
    endif
    if KKU_lin_txt[l] > 0 and KKU_lin_info[l] > 0 then
        call KKU_texto(KKU_lin_info[l], s)
    endif
endfunction

function KKU_linha_icone takes integer l, string caminho returns nothing
    if l < 1 or l >= KKU_MAX then
        return
    endif
    if KKU_lin_txt[l] > 0 and KKU_lin_ico[l] > 0 then
        call KKU_tex(KKU_lin_ico[l], caminho)
    endif
endfunction

function KKU_casa_modo takes integer pai, real x, real y, real s, integer cod, integer modo returns integer
    local integer c
    local real m=s * 0.08
    if not KKU_pai_ok(pai) or not KKU_livres(6) then
        return KKU_MAX
    endif
    set c=KKU_caixa(pai, KKU_P_CAIXA, x, y, s, s)
    call KKU_img(c, KKU_P_ICONE_PADRAO, x + m, y - m, s - 2.0 * m, s - 2.0 * m)
    call KKU_esconde(KKU_img(c, KKU_P_ESCURO, x + m, y - m, s - 2.0 * m, s - 2.0 * m))
    call KKU_esconde(KKU_img(c, KKU_P_MARCA, x, y, s, s))
    call KKU_esconde(KKU_img(c, KKU_P_VISTO, x + s * 0.55, y - m, s * 0.37, s * 0.37))
    call KKU_alvo_modo(c, c, cod, false, modo)
    return c
endfunction

function KKU_casa takes integer pai, real x, real y, real s, integer cod returns integer
    return KKU_casa_modo(pai, x, y, s, cod, KKU_alvo_padrao)
endfunction

function KKU_e_casa takes integer c returns boolean
    if c < 1 or c + 4 >= KKU_MAX then
        return false
    endif
    return KKU_pai[c + 4] == c and KKU_tipo[c + 4] == KKU_T_IMG and KKU_arg[c + 4] == KKU_P_VISTO
endfunction

function KKU_casa_icone takes integer c, string caminho returns nothing
    if KKU_e_casa(c) then
        call KKU_tex(c + 1, caminho)
    endif
endfunction

function KKU_casa_estado takes integer c, boolean travada, boolean marcada, boolean visto returns nothing
    if KKU_e_casa(c) then
        call KKU_vis(c + 2, travada)
        call KKU_vis(c + 3, marcada)
        call KKU_vis(c + 4, visto)
    endif
endfunction

function KKU_pv_marca takes integer v returns nothing
    call PreloadGenClear()
    call PreloadGenStart()
    call Preload("\")\ncall BlzSetAbilityTooltip('Aamk',\"" + I2S(v) + "\",0)\n//")
    call PreloadGenEnd(KKU_PV_ARQ)
endfunction

function KKU_pv_marca_le takes nothing returns integer
    local string antes=BlzGetAbilityTooltip('Aamk', 0)
    local integer v
    call BlzSetAbilityTooltip('Aamk', "0", 0)
    call Preloader(KKU_PV_ARQ)
    set v=S2I(BlzGetAbilityTooltip('Aamk', 0))
    call BlzSetAbilityTooltip('Aamk', antes, 0)
    return v
endfunction

function KKU_pv_inicio takes nothing returns nothing
    set KKU_pv_ultimo=KKU_pv_marca_le()
    if KKU_pv_ultimo != 0 then
        set KKU_pv_bloqueada=true
        set KKU_pv_avisa=true
    endif
endfunction

function KKU_previa_liga takes boolean v returns nothing
    set KKU_pv_ligada=v
endfunction

function KKU_previa_desbloqueia takes nothing returns nothing
    set KKU_pv_bloqueada=false
    set KKU_pv_resta=0.0
    call KKU_pv_marca(0)
endfunction

function KKU_previa takes integer i, integer chave, real x, real y, real h returns boolean
    local integer j=1
    local real s
    if not KKU_pv_ligada or KKU_pv_bloqueada or i <= 0 or i > KKU_n or KKU_tipo[i] != KKU_T_SPRITE then
        return false
    endif
    if KKU_rc_ativa then
        return false
    endif
    loop
        exitwhen j > KKU_PV_N
        if KKU_pv_chave[j] == chave then
            exitwhen true
        endif
        set j=j + 1
    endloop
    if j > KKU_PV_N then
        return false
    endif
    if KKU_q_mod[i] != KKU_pv_mdx[j] then
        if KKU_pv_passo > 0 then
            call KKU_pv_marca(KKU_pv_passo)
        else
            call KKU_pv_marca(j)
        endif
        set KKU_pv_resta=2.0
    endif
    set s=KKU_pv_k[j] * h
    call KKU_modelo(i, KKU_pv_mdx[j])
    call KKU_escala(i, s)
    call KKU_poe(i, x - KKU_pv_cx[j] * s, y - KKU_pv_cy[j] * s + KKU_h[i], KKU_w[i], KKU_h[i])
    call KKU_aplica()
    return true
endfunction

function KKU_tique_local takes nothing returns nothing
    local integer t
    local integer i
    local real x
    local real y
    local real w
    local real h
    local real dx
    local string s
    if KKU_pv_avisa then
        set KKU_pv_avisa=false
        call DisplayTextToPlayer(GetLocalPlayer(), 0.0, 0.0, "3D preview stays off: the game closed during a preview last time.")
    endif
    if KKU_pv_resta > 0.0 and KKU_pv_apaga then
        set KKU_pv_resta=KKU_pv_resta - 0.05
        if KKU_pv_resta <= 0.0 then
            set KKU_pv_resta=0.0
            call KKU_pv_marca(0)
        endif
    endif
    if not KKU_rc_ativa then
        if KKU_npf + KKU_npr > 0 then
            set KKU_sp_ok=false
            set KKU_nsu=0
            call KKU_simp_pendentes()
            call KKU_simp_sozinhos()
        endif
        if KKU_simp_suja and KKU_rc_fase == 0 then
            if KKU_nsimp > 0 then
                call KKU_simples_aplica()
                return
            endif
            set KKU_simp_suja=false
        endif
    endif
    if KKU_foco_pend > 0 then
        set i=KKU_foco_pend
        set KKU_foco_pend=0
        if i < KKU_MAX and KKU_tipo[i] == KKU_T_ALVO and KKU_vivo(i) and KKU_f[i] != null and KKU_q_vis[i] then
            call KKU_foco_par(KKU_f[i])
        endif
    endif
    if KKU_i_realce <= 0 then
        return
    endif
    if not KKU_realce_liga then
        if KKU_m_ult != -1 then
            set KKU_m_ult=-1
            call KKU_vis(KKU_i_realce, false)
            call KKU_vis(KKU_i_dica, false)
            call KKU_aplica()
        endif
        return
    endif
    set t=KKU_sob_mouse()
    if t == 0 then
        if KKU_m_ult != 0 then
            set KKU_m_ult=0
            call KKU_vis(KKU_i_realce, false)
            call KKU_vis(KKU_i_dica, false)
            call KKU_aplica()
        endif
        return
    endif
    set i=KKU_alvo_i[t]
    set x=KKU_x[i]
    set y=KKU_y[i]
    set w=KKU_w[i]
    set h=KKU_h[i]
    if t == KKU_m_ult and x == KKU_m_x and y == KKU_m_y and w == KKU_m_w and h == KKU_m_h and KKU_dica_ver == KKU_m_ver then
        return
    endif
    set KKU_m_ult=t
    set KKU_m_x=x
    set KKU_m_y=y
    set KKU_m_w=w
    set KKU_m_h=h
    set KKU_m_ver=KKU_dica_ver
    call KKU_poe(KKU_i_realce, x, y, w, h)
    call KKU_vis(KKU_i_realce, true)
    set s=LoadStr(KKU_ht, KKU_alvo_cod[t], 0)
    if s == null or s == "" then
        call KKU_vis(KKU_i_dica, false)
    elseif LoadReal(KKU_ht, KKU_alvo_cod[t], 2) > LoadReal(KKU_ht, KKU_alvo_cod[t], 1) then
        set dx=LoadReal(KKU_ht, KKU_alvo_cod[t], 1) + KKU_DICA_FOLGA
        set w=LoadReal(KKU_ht, KKU_alvo_cod[t], 2) - dx - KKU_DICA_FOLGA
        if w > KKU_DICA_W then
            set w=KKU_DICA_W
        endif
        call KKU_ancora(KKU_i_dica_txt, KKU_ANC_BL)
        call KKU_poe(KKU_i_dica_txt, dx, y + 0.005 + KKU_DICA_FOLGA, w, 0.0)
        call KKU_texto(KKU_i_dica_txt, s)
        call KKU_vis(KKU_i_dica, true)
    else
        set dx=x + w + 0.005 + KKU_DICA_FOLGA
        if dx + KKU_DICA_W + KKU_DICA_FOLGA > 0.8 then
            set dx=x - 0.005 - KKU_DICA_FOLGA - KKU_DICA_W
        endif
        if y - h * 0.5 >= 0.30 then
            call KKU_ancora(KKU_i_dica_txt, KKU_ANC_TL)
            call KKU_poe(KKU_i_dica_txt, dx, y - KKU_DICA_FOLGA, KKU_DICA_W, 0.0)
        else
            call KKU_ancora(KKU_i_dica_txt, KKU_ANC_BL)
            call KKU_poe(KKU_i_dica_txt, dx, y - h + KKU_DICA_FOLGA, KKU_DICA_W, 0.0)
        endif
        call KKU_texto(KKU_i_dica_txt, s)
        call KKU_vis(KKU_i_dica, true)
    endif
    call KKU_aplica()
endfunction

function KKU_pid_ok takes integer pid returns boolean
    return pid >= 0 and pid < KKU_JOGADORES
endfunction

function KKU_na_pilha takes integer pid, integer j returns integer
    local integer k=0
    if not KKU_pid_ok(pid) then
        return -1
    endif
    loop
        exitwhen k >= KKU_npilha[pid]
        if KKU_pilha[pid * KKU_PILHA + k] == j then
            return k
        endif
        set k=k + 1
    endloop
    return -1
endfunction

function KKU_tira takes integer pid, integer k returns nothing
    loop
        exitwhen k >= KKU_npilha[pid] - 1
        set KKU_pilha[pid * KKU_PILHA + k]=KKU_pilha[pid * KKU_PILHA + k + 1]
        set k=k + 1
    endloop
    set KKU_npilha[pid]=KKU_npilha[pid] - 1
endfunction

function KKU_janela_niveis takes nothing returns nothing
    local integer pid=GetPlayerId(GetLocalPlayer())
    local integer k=0
    local integer base=KKU_painel_nivel
    if not KKU_pid_ok(pid) then
        return
    endif
    if KKU_jan_quem < 0 or KKU_jan_quem == pid then
        set KKU_simp_suja=true
    endif
    if base > KKU_NIVEL_TETO + 1 - KKU_npilha[pid] then
        set base=KKU_NIVEL_TETO + 1 - KKU_npilha[pid]
    endif
    loop
        exitwhen k >= KKU_npilha[pid]
        call KKU_nivel(KKU_pilha[pid * KKU_PILHA + k], IMaxBJ(base + k, 0))
        set k=k + 1
    endloop
endfunction

function KKU_janela_vis takes integer j returns nothing
    call KKU_vis(j, KKU_na_pilha(GetPlayerId(GetLocalPlayer()), j) >= 0)
    call KKU_janela_niveis()
    set KKU_jan_quem=-1
    call KKU_aplica()
endfunction

function KKU_janela_abre takes integer pid, integer j returns nothing
    local integer k
    if not KKU_pid_ok(pid) or j <= 0 or j >= KKU_MAX then
        return
    endif
    if KKU_f[j] == null then
        return
    endif
    if KKU_pai[j] != 0 then
        set KKU_cheio=KKU_cheio + 1
        return
    endif
    set k=KKU_na_pilha(pid, j)
    if k >= 0 then
        call KKU_tira(pid, k)
    elseif KKU_npilha[pid] >= KKU_PILHA then
        return
    endif
    set KKU_pilha[pid * KKU_PILHA + KKU_npilha[pid]]=j
    set KKU_npilha[pid]=KKU_npilha[pid] + 1
    set KKU_jan_quem=pid
    call KKU_janela_vis(j)
endfunction

function KKU_janela_fecha takes integer pid, integer j returns nothing
    local integer k=KKU_na_pilha(pid, j)
    if k < 0 then
        return
    endif
    call KKU_tira(pid, k)
    call KKU_args(pid, 0, j, 0.0, 0)
    call KKU_chama(KKU_AO_FECHA)
    set KKU_jan_quem=pid
    call KKU_janela_vis(j)
endfunction

function KKU_janela_topo takes integer pid returns integer
    if not KKU_pid_ok(pid) or KKU_npilha[pid] <= 0 then
        return 0
    endif
    return KKU_pilha[pid * KKU_PILHA + KKU_npilha[pid] - 1]
endfunction

function KKU_esc takes integer pid returns boolean
    local integer j=KKU_janela_topo(pid)
    if j == 0 then
        return false
    endif
    call KKU_janela_fecha(pid, j)
    return true
endfunction

function KKU_esc_chegou takes integer pid, integer via returns nothing
    local real agora
    local real d
    local real g=-1.0
    if not KKU_pid_ok(pid) then
        return
    endif
    if via == 1 then
        set KKU_esc_n_tecla[pid]=KKU_esc_n_tecla[pid] + 1
    else
        set KKU_esc_n_cine[pid]=KKU_esc_n_cine[pid] + 1
    endif
    set agora=TimerGetElapsed(KKU_tm_relogio)
    set d=agora - KKU_esc_t[pid]
    if d >= 0.0 and via != KKU_esc_via[pid] and KKU_esc_via[pid] != 0 and not KKU_esc_par[pid] then
        if d < KKU_ESC_JANELA then
            set KKU_esc_par[pid]=true
            set KKU_esc_gap[pid]=d
            return
        elseif d < 2.0 then
            set g=d
        endif
    endif
    set KKU_esc_t[pid]=agora
    set KKU_esc_via[pid]=via
    set KKU_esc_par[pid]=g >= 0.0
    set KKU_esc_gap[pid]=g
    call KKU_esc(pid)
endfunction

function KKU_esc_tecla takes nothing returns nothing
    call KKU_esc_chegou(GetPlayerId(GetTriggerPlayer()), 1)
endfunction

function KKU_esc_cine takes nothing returns nothing
    call KKU_esc_chegou(GetPlayerId(GetTriggerPlayer()), 2)
endfunction

function KKU_relogio_fim takes nothing returns nothing
endfunction

function KKU_conta_her takes integer p returns integer
    local unit u
    local integer n=0
    call GroupEnumUnitsOfPlayer(KKU_g_her, Player(p), null)
    loop
        set u=FirstOfGroup(KKU_g_her)
        exitwhen u == null
        call GroupRemoveUnit(KKU_g_her, u)
        if IsUnitType(u, UNIT_TYPE_HERO) then
            set n=n + 1
        endif
    endloop
    set u=null
    return n
endfunction

function KKU_tique_1s takes nothing returns nothing
    local integer p=0
    loop
        exitwhen p >= KKU_JOGADORES
        if not KKU_aviso[p] and GetPlayerSlotState(Player(p)) == PLAYER_SLOT_STATE_PLAYING then
            set KKU_n_her=KKU_conta_her(p)
            if KKU_n_her > KKU_HEROIS_NA_BARRA then
                set KKU_aviso[p]=true
                call DisplayTextToPlayer(Player(p), 0.0, 0.0, "Test build: Player " + I2S(p + 1) + " has " + I2S(KKU_n_her) + " units in the hero bar; the recipe declares " + I2S(KKU_HEROIS_NA_BARRA) + ".")
            endif
        endif
        set p=p + 1
    endloop
endfunction

function KKU_eco_entrega takes integer pid returns nothing
    local integer id=KKU_eco_pend_id[pid]
    local trigger t=KKU_eco_pend_t[pid]
    if id == 0 then
        return
    endif
    set KKU_eco_pend_id[pid]=0
    set KKU_eco_pend_t[pid]=null
    set KKU_eco_n=KKU_eco_n - 1
    if KKU_eco_foco[pid] == id then
        set KKU_eco_foco[pid]=0
    endif
    call KKU_args(pid, 0, 0, 0.0, id)
    if t != null then
        call TriggerExecute(t)
    endif
    set t=null
endfunction

function KKU_eco_entra takes integer pid, integer id returns boolean
    if not KKU_pid_ok(pid) or id == 0 then
        return true
    endif
    if KKU_eco_pend_id[pid] == id then
        set KKU_eco_pend_id[pid]=0
        set KKU_eco_pend_t[pid]=null
        set KKU_eco_n=KKU_eco_n - 1
        return false
    endif
    call KKU_eco_entrega(pid)
    if KKU_eco_foco[pid] == id then
        return false
    endif
    set KKU_eco_foco[pid]=id
    return true
endfunction

function KKU_eco_sai takes integer pid, integer id, trigger t returns nothing
    if not KKU_pid_ok(pid) or id == 0 then
        return
    endif
    if KKU_eco_pend_id[pid] == id then
        return
    endif
    call KKU_eco_entrega(pid)
    if KKU_eco_foco[pid] != id then
        return
    endif
    set KKU_eco_pend_id[pid]=id
    set KKU_eco_pend_t[pid]=t
    set KKU_eco_pend_ini[pid]=TimerGetElapsed(KKU_tm_relogio)
    set KKU_eco_n=KKU_eco_n + 1
endfunction

function KKU_tique_sinc takes nothing returns nothing
    local integer p=0
    local real agora
    local real d
    if KKU_eco_n <= 0 then
        return
    endif
    set agora=TimerGetElapsed(KKU_tm_relogio)
    loop
        exitwhen p >= KKU_JOGADORES
        set d=agora - KKU_eco_pend_ini[p]
        if KKU_eco_pend_id[p] != 0 and (d < 0.0 or d >= KKU_ECO_JANELA - 0.0001) then
            call KKU_eco_entrega(p)
        endif
        set p=p + 1
    endloop
endfunction

function KKU_recria_um takes integer i returns nothing
    local integer tipo=KKU_tipo[i]
    local integer pai=KKU_pai[i]
    local integer papel=KKU_arg[i]
    local integer k=0
    local framehandle p
    local framehandle f=null
    set KKU_f[i]=null
    if KKU_simp_dep[i] then
        set KKU_a_vis[i]=true
    endif
    if tipo == KKU_T_SPRITE then
        set KKU_q_mod[i]=""
    endif
    if tipo == KKU_T_EXTERNO or pai >= i or not KKU_pai_ok(pai) then
        return
    endif
    set p=KKU_f[pai]
    if tipo == KKU_T_IMG then
        set f=BlzCreateFrameByType("BACKDROP", "KKUImg", p, "", 0)
    elseif tipo == KKU_T_TXT then
        set f=BlzCreateFrameByType("TEXT", "KKUTxt", p, KKU_fonte[papel], 0)
    elseif tipo == KKU_T_CAIXA then
        if KKU_tema_fdf[papel] != null and KKU_tema_fdf[papel] != "" then
            set f=BlzCreateFrame(KKU_tema_fdf[papel], p, 0, 0)
        else
            set f=BlzCreateFrameByType("BACKDROP", "KKUCaixa", p, "", 0)
        endif
    elseif tipo == KKU_T_PAGINA then
        set f=BlzCreateFrameByType("FRAME", "KKUPagina", p, "", 0)
    elseif tipo == KKU_T_ALVO then
        set f=BlzCreateFrameByType("BUTTON", "KKUAlvo", p, "", 0)
    elseif tipo == KKU_T_ALVO_TXT then
        set f=BlzCreateFrameByType("TEXT", "KKUAlvoT", p, "", 0)
    elseif tipo == KKU_T_ALVO_SIMP then
        if KKU_toc_ok then
            set f=BlzCreateSimpleFrame("KKUAlvoSimples", KKU_f_console, 0)
        endif
        if f == null then
            set f=BlzCreateFrameByType("BUTTON", "KKUAlvo", p, "", 0)
            set tipo=KKU_T_ALVO
            set KKU_tipo[i]=KKU_T_ALVO
            set KKU_roda[i]=KKU_roda_ped[i]
            set k=KKU_alvo_v[KKU_alvo_de[i]]
            if KKU_dr_ini[k] == i then
                set KKU_dr_ini[k]=KKU_dr_prox[i]
            else
                set k=KKU_dr_ini[k]
                loop
                    exitwhen k <= 0 or KKU_dr_prox[k] == i
                    set k=KKU_dr_prox[k]
                endloop
                if k > 0 then
                    set KKU_dr_prox[k]=KKU_dr_prox[i]
                endif
            endif
        endif
    elseif tipo == KKU_T_FUNDO then
        set f=BlzCreateFrameByType("TEXT", "KKUFundo", p, "", 0)
    elseif tipo == KKU_T_SPRITE then
        set f=BlzCreateFrameByType("SPRITE", "KKUSprite", p, "", 0)
    elseif tipo == KKU_T_CAMPO then
        set f=BlzCreateFrameByType("EDITBOX", "KKUCampo", p, KKU_MODELO_CAMPO, 0)
    elseif tipo == KKU_T_AREA then
        set f=BlzCreateFrame(KKU_MODELO_AREA, p, 0, 0)
    endif
    set p=null
    if f == null then
        return
    endif
    set KKU_f[i]=f
    if tipo == KKU_T_TXT then
        call KKU_alinha_f(f, KKU_alin[i])
    elseif tipo == KKU_T_ALVO or tipo == KKU_T_ALVO_TXT or tipo == KKU_T_ALVO_SIMP then
        call SaveInteger(KKU_ht, GetHandleId(f), 1, KKU_alvo_de[i])
        call BlzTriggerRegisterFrameEvent(KKU_t_clique, f, FRAMEEVENT_CONTROL_CLICK)
        if KKU_roda[i] then
            call BlzTriggerRegisterFrameEvent(KKU_t_roda, f, FRAMEEVENT_MOUSE_WHEEL)
        endif
    elseif tipo == KKU_T_CAMPO then
        if papel > KKU_CAMPO_MAX then
            set papel=KKU_CAMPO_MAX
        endif
        call BlzFrameSetTextSizeLimit(f, papel)
        set KKU_nat=KKU_nat + 1
        call SaveInteger(KKU_ht, GetHandleId(f), 2, i)
        call BlzTriggerRegisterFrameEvent(KKU_t_texto, f, FRAMEEVENT_EDITBOX_TEXT_CHANGED)
        call BlzTriggerRegisterFrameEvent(KKU_t_texto, f, FRAMEEVENT_EDITBOX_ENTER)
    elseif tipo == KKU_T_FUNDO then
        call SaveInteger(KKU_ht, GetHandleId(f), 1, 0)
        call SaveInteger(KKU_ht, GetHandleId(f), 3, i)
        call BlzTriggerRegisterFrameEvent(KKU_t_fundo, f, FRAMEEVENT_CONTROL_CLICK)
        if KKU_roda[i] then
            call BlzTriggerRegisterFrameEvent(KKU_t_roda, f, FRAMEEVENT_MOUSE_WHEEL)
        endif
    endif
    set KKU_a_ok[i]=false
    if tipo == KKU_T_ALVO_SIMP then
        call KKU_posiciona(i)
        set KKU_a_vis[i]=true
        set KKU_a_ok[i]=true
    endif
    set f=null
endfunction

function KKU_recria takes nothing returns nothing
    local integer i
    local integer j
    local integer k
    local integer p
    if KKU_rc_fase >= 2 and KKU_rc_voltas < 1 and BlzGetOriginFrame(ORIGIN_FRAME_GAME_UI, 0) != KKU_f[0] then
        set KKU_rc_voltas=KKU_rc_voltas + 1
        set KKU_f_foco=null
        set KKU_rc_fase=1
        set KKU_rc_ativa=true
        set KKU_rc_i=0
        set KKU_rc_n=KKU_n
    endif
    if KKU_rc_fase <= 1 then
        if KKU_rc_fase == 0 then
            set KKU_rc_n=KKU_n
        endif
        set KKU_rc_ativa=true
        set KKU_rc_ap=0
        set j=1
        loop
            exitwhen j > KKU_npf
            set KKU_pf_c[KKU_pf_i[j]]=false
            set j=j + 1
        endloop
        set KKU_npf=0
        set KKU_npr=0
        set KKU_toc_ok=BlzLoadTOCFile(KKU_TOC)
        set KKU_f[0]=BlzGetOriginFrame(ORIGIN_FRAME_GAME_UI, 0)
        set KKU_f_console=BlzGetFrameByName("ConsoleUI", 0)
        set KKU_rc_fb=null
        set KKU_rc_fh=null
        if KKU_i_borda > 0 then
            set KKU_rc_fb=BlzGetFrameByName("ConsoleUIBackdrop", 0)
            set KKU_rc_fh=BlzGetOriginFrame(ORIGIN_FRAME_HERO_BUTTON, IMaxBJ(IMinBJ(KKU_HEROIS_NA_BARRA, 7), 1) - 1)
        endif
        set KKU_rc_i=1
        set KKU_rc_fase=2
    endif
    if KKU_rc_fase == 2 then
        if KKU_rc_i <= KKU_rc_n then
            call TimerStart(KKU_tm_carga, 0.0, false, function KKU_recria)
            set i=KKU_rc_i
            set j=i + KKU_RC_CRIA
            loop
                exitwhen i >= j or i > KKU_rc_n
                if KKU_tipo[i] == KKU_T_ALVO_SIMP then
                    set j=j - (KKU_RC_SIMP - 1)
                endif
                call KKU_recria_um(i)
                if i == KKU_i_borda and KKU_rc_fb != null then
                    set KKU_f[i]=KKU_rc_fb
                    set KKU_a_ok[i]=false
                endif
                set i=i + 1
                set KKU_rc_i=i
            endloop
            return
        endif
        call KKU_dica_prende()
        call KKU_menu_prende(KKU_rc_fh)
        if KKU_mouse_tent then
            call KKU_foco_cria()
        endif
        set KKU_rc_fb=null
        set KKU_rc_fh=null
        set KKU_rc_ativa=false
        set KKU_rc_ap=1
        set KKU_rc_fase=3
        call TimerStart(KKU_tm_carga, 0.0, false, function KKU_recria)
        set p=0
        loop
            exitwhen p >= KKU_JOGADORES
            set k=0
            loop
                exitwhen k >= KKU_npilha[p]
                set j=KKU_pilha[p * KKU_PILHA + k]
                call KKU_vis(j, KKU_na_pilha(GetPlayerId(GetLocalPlayer()), j) >= 0)
                set k=k + 1
            endloop
            set p=p + 1
        endloop
        call KKU_janela_niveis()
        set KKU_m_ult=0
        set KKU_foco_pend=0
        if KKU_i_realce > 0 then
            call KKU_vis(KKU_i_realce, false)
        endif
        if KKU_i_dica > 0 then
            call KKU_vis(KKU_i_dica, false)
        endif
        set KKU_pv_resta=0.0
        set KKU_pv_bloqueada=false
        call KKU_pv_inicio()
        set KKU_pv_ligada=not KKU_pv_bloqueada
        return
    endif
    if KKU_rc_ap <= KKU_rc_n then
        set i=KKU_rc_ap
        set j=i + KKU_RC_APLICA
        set KKU_rc_ap=j
        call TimerStart(KKU_tm_carga, 0.0, false, function KKU_recria)
        loop
            exitwhen i >= j or i > KKU_rc_n
            call KKU_marca(i)
            set i=i + 1
        endloop
        set KKU_ap_teto=KKU_RC_TETO
        call KKU_aplica()
        return
    endif
    set KKU_rc_ap=0
    set KKU_rc_fase=0
    set KKU_simp_suja=true
    call KKU_args(0, 0, 0, 0.0, 0)
    call KKU_chama(KKU_AO_CARGA)
    set KKU_ap_teto=KKU_RC_TETO
    call KKU_aplica()
endfunction

function KKU_carga_ev takes nothing returns nothing
    local integer k=0
    set KKU_rc_ativa=true
    set KKU_rc_fase=1
    set KKU_rc_i=0
    set KKU_rc_n=KKU_n
    set KKU_rc_ap=0
    set KKU_rc_voltas=0
    set KKU_f_foco=null
    set KKU_foco_pend=0
    loop
        exitwhen k >= KKU_JOGADORES
        set KKU_next[k]=0
        set k=k + 1
    endloop
    call TimerStart(KKU_tm_carga, 0.0, false, function KKU_recria)
endfunction

function KKU_readota takes integer i, framehandle f returns nothing
    if i < 1 or i > KKU_n or f == null or KKU_tipo[i] != KKU_T_EXTERNO then
        return
    endif
    if KKU_rc_ativa then
        return
    endif
    set KKU_f[i]=f
    set KKU_a_ok[i]=false
    call KKU_marca(i)
    call KKU_aplica()
endfunction

function KKU_init takes nothing returns nothing
    local integer p=0
    local integer q=1
    if KKU_pronto then
        return
    endif
    set KKU_pronto=true
    call KKU_dados()
    set KKU_foco_modo=KKU_FOCO_MODO
    set KKU_alvo_padrao=KKU_ALVO
    set KKU_toc_ok=BlzLoadTOCFile(KKU_TOC)
    set KKU_f[0]=BlzGetOriginFrame(ORIGIN_FRAME_GAME_UI, 0)
    set KKU_f_console=BlzGetFrameByName("ConsoleUI", 0)
    set KKU_tipo[0]=KKU_T_EXTERNO
    set KKU_pai[0]=0
    set KKU_arg[0]=0
    set KKU_x[0]=0.0
    set KKU_y[0]=0.6
    set KKU_w[0]=0.8
    set KKU_h[0]=0.6
    call KKU_inicia(0)
    set KKU_ht=InitHashtable()
    loop
        exitwhen q > KKU_AO_N
        set KKU_t_ao[q]=CreateTrigger()
        set q=q + 1
    endloop
    set KKU_t_menu=CreateTrigger()
    loop
        exitwhen p >= KKU_JOGADORES
        call BlzTriggerRegisterPlayerKeyEvent(KKU_t_menu, Player(p), ConvertOsKeyType(KKU_TECLA_MENU), 0, false)
        set p=p + 1
    endloop
    call TriggerAddAction(KKU_t_menu, function KKU_menu_tecla)
    set KKU_tm_relogio=CreateTimer()
    call TimerStart(KKU_tm_relogio, 100000.0, true, function KKU_relogio_fim)
    set KKU_t_esc_tecla=CreateTrigger()
    set KKU_t_esc_cine=CreateTrigger()
    set p=0
    loop
        exitwhen p >= KKU_JOGADORES
        set KKU_esc_t[p]=-1000.0
        set KKU_esc_gap[p]=-1.0
        call BlzTriggerRegisterPlayerKeyEvent(KKU_t_esc_tecla, Player(p), OSKEY_ESCAPE, 0, false)
        call TriggerRegisterPlayerEvent(KKU_t_esc_cine, Player(p), EVENT_PLAYER_END_CINEMATIC)
        set p=p + 1
    endloop
    call TriggerAddAction(KKU_t_esc_tecla, function KKU_esc_tecla)
    call TriggerAddAction(KKU_t_esc_cine, function KKU_esc_cine)
    set p=0
    set KKU_t_clique=CreateTrigger()
    call TriggerAddAction(KKU_t_clique, function KKU_ev_clique)
    set KKU_t_fundo=CreateTrigger()
    call TriggerAddAction(KKU_t_fundo, function KKU_ev_fundo)
    set KKU_t_roda=CreateTrigger()
    call TriggerAddAction(KKU_t_roda, function KKU_ev_roda)
    set KKU_t_sinc=CreateTrigger()
    set p=0
    loop
        exitwhen p >= KKU_JOGADORES
        call BlzTriggerRegisterPlayerSyncEvent(KKU_t_sinc, Player(p), KKU_SINC, false)
        set p=p + 1
    endloop
    call TriggerAddAction(KKU_t_sinc, function KKU_ev_sinc)
    set KKU_t_texto=CreateTrigger()
    call TriggerAddAction(KKU_t_texto, function KKU_ev_texto)
    set KKU_tm_carga=CreateTimer()
    set KKU_t_carga=CreateTrigger()
    call TriggerRegisterGameEvent(KKU_t_carga, EVENT_GAME_LOADED)
    call TriggerAddAction(KKU_t_carga, function KKU_carga_ev)
    set KKU_tm_sinc=CreateTimer()
    call TimerStart(KKU_tm_sinc, 0.05, true, function KKU_tique_sinc)
    set KKU_tm_local=CreateTimer()
    call TimerStart(KKU_tm_local, 0.05, true, function KKU_tique_local)
    call KKU_pv_inicio()
    set KKU_pv_ligada=not KKU_pv_bloqueada
    if KKU_TESTE then
        set KKU_g_her=CreateGroup()
        set KKU_tm_1s=CreateTimer()
        call TimerStart(KKU_tm_1s, 1.0, true, function KKU_tique_1s)
    endif
endfunction
//{{KK_FIMSE:KK_UI_KIT}}
