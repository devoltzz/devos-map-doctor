//@REQUER KK:kk_ui.j KK_UI_KIT
//@GLOBALS
string KKP_titulo="Codex"

integer KKP_jogadores=12
string KKP_txt_receita=""
string KKP_txt_codex="Pick an item on the left."
string KKP_txt_chefes="Pick a boss on the left."
string KKP_txt_taxa="with your drop bonus"
string KKP_txt_sem_heroi="No hero yet."
integer KKP_aba_n=0
integer array KKP_aba_tipo
string array KKP_aba_nome
integer array KKP_aba_tecla
integer KKP_cat_n=0
string array KKP_cat_nome
integer array KKP_cat_ini
integer array KKP_cat_qt
integer KKP_it_n=0
integer array KKP_it
integer array KKP_it_cat
string array KKP_it_ico
integer array KKP_it_rc
integer array KKP_it_rcn
integer array KKP_it_us
integer array KKP_it_usn
integer array KKP_it_dp
integer array KKP_it_dpn
integer array KKP_us
integer array KKP_dp_bs
integer array KKP_dp_qt
integer array KKP_dp_tipo
integer array KKP_dp_taxa
integer KKP_rc_n=0
integer array KKP_rc_res
integer array KKP_rc_ini
integer array KKP_rc_ingn
integer array KKP_rc_ouro
integer array KKP_rc_madeira
integer array KKP_ing
integer array KKP_ing_qt
integer KKP_bs_n=0
integer array KKP_bs_unid
integer array KKP_bs_grupo
integer array KKP_bs_nivel
integer array KKP_bs_vida
string array KKP_bs_ico
string array KKP_bs_nome
string array KKP_bs_nota
real array KKP_bs_x
real array KKP_bs_y
boolean array KKP_bs_pos
integer array KKP_bs_dr
integer array KKP_bs_drn
integer array KKP_dr_it
integer array KKP_dr_qt
integer array KKP_dr_tipo
integer array KKP_dr_taxa
integer KKP_gr_n=0
string array KKP_gr_nome
integer array KKP_gr_ini
integer array KKP_gr_qt
string array KKP_aba_id
integer array KKP_ab_subn
string array KKP_ab_sub
integer array KKP_ab_lay
constant integer KKP_G_FICHA=1
constant integer KKP_G_GRADE=2
constant integer KKP_G_APLICA=3
constant integer KKP_G_FAV_LE=4
constant integer KKP_G_FAV_GRAVA=5
trigger KKP_t_g1=CreateTrigger()
trigger KKP_t_g2=CreateTrigger()
trigger KKP_t_g3=CreateTrigger()
trigger KKP_t_g4=CreateTrigger()
trigger KKP_t_g5=CreateTrigger()
trigger KKP_t_g6=CreateTrigger()
trigger KKP_t_g7=CreateTrigger()
trigger KKP_t_g8=CreateTrigger()
boolean array KKP_g_tem
integer KKP_arg_pid=0
integer KKP_arg_aba=0
integer KKP_arg_sub=0
integer KKP_arg_i=0
integer KKP_arg_btn=0
//{{KK_SE:KK_PAINEL_CRAFT}}
constant integer KKP_G_CRAFT=6
integer KKP_arg_item=0
//{{KK_FIMSE:KK_PAINEL_CRAFT}}
string KKP_arg_s=""
boolean KKP_arg_ok=false
unit array KKP_heroi
string array KKP_x_mapa
real array KKP_mult
unit array KKP_inv_u
integer array KKP_h_pv
integer array KKP_g_pv
integer array KKP_g_n
integer array KKP_g_atual
string array KKP_g_topo
string array KKP_g_det
string array KKP_g_b1
string array KKP_g_b2
integer array KKP_g_bm
string array KKP_g_nome
string array KKP_g_tit
string array KKP_g_ico
string array KKP_g_info
string array KKP_g_edet
boolean array KKP_g_trava
boolean array KKP_g_ok
integer array KKP_g_eb
integer array KKP_g_val
//{{KK_SE:KK_PAINEL_IMG}}
string array KKP_g_img
real array KKP_g_img_l
real array KKP_g_img_a
integer KKP_g_dimg=0
integer KKP_k_dimg=0
real array KKP_im_x
real array KKP_im_y
real array KKP_im_w
real array KKP_im_h
//{{KK_FIMSE:KK_PAINEL_IMG}}
//{{KK_SE:KK_PAINEL_EXTRA}}
constant integer KKP_G_PRONTO=7
constant integer KKP_G_DADOS=8
constant integer KKP_G_ITEM=9
trigger KKP_t_g9=CreateTrigger()
constant integer KKP_DADOS_MAX=64
integer KKP_arg_x=0
integer KKP_dados_k=0
string KKP_b3_rot=""
boolean array KKP_it_b3ok
boolean array KKP_b3_fora
boolean KKP_com_link=false
integer array KKP_f_link
string array KKP_f_link_tx
integer KKP_f_lico=0
integer KKP_f_ltxt=0
integer KKP_f_lbt=0
string array KKP_dm_s
integer array KKP_dm_k
integer KKP_x_qi=0
integer KKP_x_qc=0
integer KKP_t1_pid=0
//{{KK_FIMSE:KK_PAINEL_EXTRA}}
//{{KK_SE:KK_PAINEL_CHEFE_BT}}
//@REQUER KK:kk_painel.j KK_PAINEL_EXTRA
constant integer KKP_G_CHEFE=10
trigger KKP_t_g10=CreateTrigger()
string KKP_bb_rot=""
boolean array KKP_bs_bok
boolean array KKP_bb_fora
integer KKP_g_quer_i=-1
//{{KK_FIMSE:KK_PAINEL_CHEFE_BT}}
//{{KK_SE:KK_PAINEL_DROPS}}
//@REQUER KK:kk_painel.j KK_PAINEL_EXTRA
constant integer KKP_DR_TETO=96
integer KKP_b_dtop=0
integer KKP_b_dsel=0
integer KKP_b_dpag=0
//{{KK_FIMSE:KK_PAINEL_DROPS}}
//{{KK_SE:KK_PAINEL_PADRAO}}
group KKP_g_auto=null
unit KKP_au_u=null
//{{KK_FIMSE:KK_PAINEL_PADRAO}}
hashtable KKP_ht=null
boolean KKP_pronto=false
boolean KKP_iniciado=false
integer KKP_carga_k=0
integer KKP_nq=0

trigger KKP_t_sync=null
timer KKP_tm_espera=null
timer KKP_tm_1s=null
timer KKP_tm_local=null
boolean array KKP_aberto
integer array KKP_aba
integer array KKP_ped_aba
integer array KKP_ped_sub
integer array KKP_fav
integer array KKP_favn
boolean array KKP_fav_ok
string array KKP_it_busca
boolean array KKP_h_ok
string array KKP_h_nome
integer array KKP_h_tipo
integer array KKP_h_nivel
integer array KKP_h_for
integer array KKP_h_agi
integer array KKP_h_int
integer array KKP_h_forb
integer array KKP_h_agib
integer array KKP_h_intb
integer array KKP_h_vida
integer array KKP_h_vidamax
integer array KKP_h_mana
integer array KKP_h_manamax
integer array KKP_h_dano1
integer array KKP_h_dano2
integer array KKP_h_vel
real array KKP_h_arm
real array KKP_h_cd
integer KKP_raiz=0
integer KKP_caixa=0
integer KKP_fundo=0
integer KKP_f_titulo=0
integer KKP_f_aviso=0
integer array KKP_pag
integer KKP_f_ico=0
integer KKP_f_nome=0
integer KKP_f_stat=0
integer KKP_f_mapa=0
integer KKP_c_busca=0
integer KKP_c_btxt=0
integer KKP_c_pag=0
integer KKP_c_dico=0
integer KKP_c_dnome=0
integer KKP_c_dsub=0
integer KKP_c_rtit=0
integer array KKP_c_rico
integer array KKP_c_rbt
integer array KKP_c_rok
integer array KKP_c_rqt
integer KKP_c_utit=0
integer array KKP_c_uico
integer array KKP_c_ubt
integer KKP_c_desc=0
integer KKP_b_pag=0
integer KKP_b_dico=0
integer KKP_b_dnome=0
integer KKP_b_dinfo=0
integer KKP_b_dnota=0
integer KKP_b_dtit=0
integer array KKP_b_dico2
integer array KKP_b_dbt
integer array KKP_b_dtx
integer KKP_g_topo_tx=0
integer KKP_g_corpo1=0
integer KKP_g_corpo2=0
integer KKP_l_pag=0
integer array KKP_g_bt
integer array KKP_g_icof
integer array KKP_g_dim
integer array KKP_g_cur
integer KKP_g_marca=0
integer KKP_g_pag=0
integer KKP_g_dcx=0
integer KKP_g_dico=0
integer KKP_g_dnome=0
integer KKP_g_dtxt=0
integer KKP_g_corpo3=0
integer KKP_k_topo=0
integer KKP_k_pag=0
integer KKP_k_dico=0
integer KKP_k_dnome=0
integer KKP_k_dtxt=0
integer KKP_pv_ficha=0
integer KKP_pv_det=0
integer KKP_pv_cx_ficha=0
integer KKP_pv_cx_det=0
integer KKP_pv_rot_ficha=0
integer KKP_pv_rot_det=0
integer KKP_pv_rot_ult=0
integer KKP_pv_k=0
integer KKP_pv_cx_k=0
integer KKP_pv_rot_k=0
integer KKP_pv_al_ficha=0
integer KKP_pv_alb_ficha=0
integer KKP_pv_al_det=0
integer KKP_pv_alb_det=0
integer KKP_pv_al_ult=0
integer KKP_pv_alb_ult=0
integer KKP_pv_al_k=0
integer KKP_pv_alb_k=0
boolean KKP_aba_tex=false
boolean KKP_tem3=false
integer KKP_c_cat=1
integer KKP_c_top=0
integer KKP_c_sel=0
integer KKP_c_utop=0
string KKP_c_q=""
boolean KKP_c_eco=false
integer KKP_c_eco_t=0
string KKP_c_ign=""
integer array KKP_res
integer KKP_res_n=0
integer KKP_res_i=0
boolean KKP_c_pend=false
integer array KKP_c_lin
integer array KKP_c_rec
integer KKP_c_rec_n=0
integer KKP_b_grupo=1
integer KKP_b_top=0
integer KKP_b_sel=0
boolean KKP_b_pend=false
integer array KKP_b_lin
integer array KKP_b_drop
integer KKP_g_aba=0
integer KKP_g_sub=1
integer KKP_g_top=0
integer KKP_g_sel=-1
integer array KKP_g_lin
integer KKP_g_quer=0
integer KKP_av_t=0
string KKP_av_s=""
boolean KKP_av_novo=false
boolean KKP_des_pend=false
integer array KKP_st_cod
boolean array KKP_st_at
boolean KKP_st_pend=false
boolean KKP_c_foco=false
boolean KKP_pv_espera=false
boolean array KKP_l_at
boolean array KKP_l_tr
constant real KKP_DX=-0.035
constant real KKP_X0=0.045
constant real KKP_Y0=0.575
constant real KKP_W0=0.71
constant real KKP_H0=0.44
constant string KKP_TEX_VAZIO="war3mapImported\\KKUI\\vazio.tga"
constant string KKP_COR_FONTE="|cfffcd312"
constant string KKP_COR_BOTAO="|cffd0d0d0"
constant integer KKP_GL=9
constant integer KKP_KL=11
constant integer KKP_SETA_ALFA=90
constant real KKP_AVISO_S=8.0
constant integer KKP_AVISO_TIQUES=100
constant integer KKP_COD_PV=19001
constant integer KKP_COD_PV_B=19002
constant string KKP_PV_ROTULO="3D preview"
constant string KKP_PV_DICA="Shows the 3D model here.|nIf the game ever closes while a model is shown, it turns off for you."
constant string KKP_PV_DICA_BLOQ="3D preview was turned off after the game closed. Click to turn it on again."
constant real KKP_PV_FX=0.695
constant real KKP_PV_FY=0.375
constant real KKP_PV_FH=0.260
constant real KKP_PV_DX=0.699
constant real KKP_PV_DY=0.320
constant real KKP_PV_DH=0.130
constant real KKP_PV_KY=0.380
constant real KKP_PV_KH=0.180
constant real KKP_PV_TX0=0.632
constant real KKP_PV_TX1=0.766
constant integer KKP_GE=96
//@ENDGLOBALS

function KKP_limpa takes string s returns string
    local integer n=StringLength(s)
    local integer i=0
    local string r=""
    local string c
    local string d
    loop
        exitwhen i>=n
        set c=SubString(s, i, i+1)
        if c=="|" and i+1<n then
            set d=SubString(s, i+1, i+2)
            if d=="c" or d=="C" then
                set i=i+10
            elseif d=="r" or d=="R" then
                set i=i+2
            elseif d=="n" or d=="N" then
                set r=r+" "
                set i=i+2
            else
                set r=r+c
                set i=i+1
            endif
        else
            set r=r+c
            set i=i+1
        endif
    endloop
    return StringCase(r, false)
endfunction

function KKP_contem takes string s,string q returns boolean
    local integer n=StringLength(s)
    local integer k=StringLength(q)
    local integer i=0
    if k==0 then
        return true
    endif
    loop
        exitwhen i+k>n
        if SubString(s, i, i+k)==q then
            return true
        endif
        set i=i+1
    endloop
    return false
endfunction

function KKP_mil takes integer n returns string
    local string s=""
    local string sinal=""
    local integer r
    if n<0 then
        set sinal="-"
        set n=-n
    endif
    loop
        exitwhen n<1000
        set r=ModuloInteger(n, 1000)
        if r<10 then
            set s=",00"+I2S(r)+s
        elseif r<100 then
            set s=",0"+I2S(r)+s
        else
            set s=","+I2S(r)+s
        endif
        set n=n/1000
    endloop
    return sinal+I2S(n)+s
endfunction

function KKP_pct takes real p returns string
    if p>=100.0 then
        return "100%"
    elseif p>=10.0 then
        return R2SW(p, 1, 1)+"%"
    elseif p>=1.0 then
        return R2SW(p, 1, 1)+"%"
    endif
    return R2SW(p, 1, 2)+"%"
endfunction

function KKP_id2s takes integer i returns string
    local string t="!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~"
    local string s=""
    local integer k=0
    local integer c
    loop
        exitwhen k>=4
        set c=ModuloInteger(i, 256)
        set i=i/256
        if c>=33 and c<=126 then
            set s=SubString(t, c-33, c-32)+s
        else
            set s="?"+s
        endif
        set k=k+1
    endloop
    return s
endfunction

function KKP_s2id takes string s returns integer
    local string t="!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~"
    local integer r=0
    local integer k=0
    local integer j
    local string c
    if StringLength(s)!=4 then
        return 0
    endif
    loop
        exitwhen k>=4
        set c=SubString(s, k, k+1)
        set j=0
        loop
            exitwhen j>=94 or SubString(t, j, j+1)==c
            set j=j+1
        endloop
        if j>=94 then
            return 0
        endif
        set r=r*256+j+33
        set k=k+1
    endloop
    return r
endfunction

function KKP_idx takes integer x returns integer
    if x==0 then
        return 0
    endif
    return LoadInteger(KKP_ht, x, 1)
endfunction

function KKP_ico_item takes integer x returns string
    local integer k=KKP_idx(x)
    local string s=""
    if k>0 then
        set s=KKP_it_ico[k]
    endif
    if s==null or s=="" then
        set s=BlzGetAbilityIcon(x)
    endif
    if s==null or s=="" then
        return "ReplaceableTextures\\CommandButtons\\BTNSelectHeroOn.blp"
    endif
    return s
endfunction

function KKP_tem_ico takes string s returns boolean
    return s!=null and s!=""
endfunction

function KKP_ico_vale takes string s returns string
    if KKP_tem_ico(s) then
        return s
    endif
    return "ReplaceableTextures\\CommandButtons\\BTNSelectHeroOn.blp"
endfunction

function KKP_nome_item takes integer x returns string
    local string s=GetObjectName(x)
    if s==null or s=="" then
        return KKP_id2s(x)
    endif
    return s
endfunction

function KKP_ico_chefe takes integer j returns string
    local string s=KKP_bs_ico[j]
    if s==null or s=="" then
        set s=BlzGetAbilityIcon(KKP_bs_unid[j])
    endif
    if s==null or s=="" then
        return "ReplaceableTextures\\CommandButtons\\BTNSelectHeroOn.blp"
    endif
    return s
endfunction

function KKP_nome_chefe takes integer j returns string
    local string s=KKP_bs_nome[j]
    if s==null or s=="" then
        set s=GetObjectName(KKP_bs_unid[j])
    endif
    if s==null or s=="" then
        return KKP_id2s(KKP_bs_unid[j])
    endif
    return s
endfunction

function KKP_taxa_txt takes integer tipo,integer taxa,integer pid returns string
    local real m=KKP_mult[pid]
    if tipo==0 or (taxa>=1000 and tipo!=3) then
        return "|cff00ff00always|r"
    elseif tipo==3 or taxa<0 then
        return "|cff999999rolled by the boss|r"
    endif
    if m<=0.0 then
        set m=1.0
    endif
    if I2R(taxa)*m>=1000.0 then
        return "|cff00ff00always|r"
    endif
    return "|cff00ff00"+KKP_pct(I2R(taxa)*m/10.0)+"|r"
endfunction

function KKP_pagina takes integer top,integer por,integer n returns string
    local integer tot=(n+por-1)/por
    local integer pg=top/por+1
    if tot<1 then
        set tot=1
    endif
    if top+por>=n or pg>tot then
        set pg=tot
    endif
    return "Page "+I2S(pg)+"/"+I2S(tot)
endfunction

function KKP_tg takes integer qual returns trigger
    if qual==1 then
        return KKP_t_g1
    elseif qual==2 then
        return KKP_t_g2
    elseif qual==3 then
        return KKP_t_g3
    elseif qual==4 then
        return KKP_t_g4
    elseif qual==5 then
        return KKP_t_g5
    elseif qual==6 then
        return KKP_t_g6
    elseif qual==7 then
        return KKP_t_g7
//{{KK_SE:KK_PAINEL_EXTRA}}
    elseif qual==9 then
        return KKP_t_g9
//{{KK_FIMSE:KK_PAINEL_EXTRA}}
//{{KK_SE:KK_PAINEL_CHEFE_BT}}
    elseif qual==10 then
        return KKP_t_g10
//{{KK_FIMSE:KK_PAINEL_CHEFE_BT}}
    endif
    return KKP_t_g8
endfunction

function KKP_gancho takes integer qual,code f returns nothing
    if qual<1 or qual>8 then
//{{KK_SE:KK_PAINEL_EXTRA}}
        if qual!=KKP_G_ITEM then
//{{KK_FIMSE:KK_PAINEL_EXTRA}}
//{{KK_SE:KK_PAINEL_CHEFE_BT}}
        if qual!=KKP_G_CHEFE then
//{{KK_FIMSE:KK_PAINEL_CHEFE_BT}}
        return
//{{KK_SE:KK_PAINEL_CHEFE_BT}}
        endif
//{{KK_FIMSE:KK_PAINEL_CHEFE_BT}}
//{{KK_SE:KK_PAINEL_EXTRA}}
        endif
//{{KK_FIMSE:KK_PAINEL_EXTRA}}
    endif
    call TriggerAddCondition(KKP_tg(qual), Condition(f))
    set KKP_g_tem[qual]=true
endfunction

function KKP_chama takes integer qual returns boolean
    if qual<1 or qual>8 or not KKP_g_tem[qual] then
//{{KK_SE:KK_PAINEL_EXTRA}}
        if qual!=KKP_G_ITEM or not KKP_g_tem[qual] then
//{{KK_FIMSE:KK_PAINEL_EXTRA}}
//{{KK_SE:KK_PAINEL_CHEFE_BT}}
        if qual!=KKP_G_CHEFE or not KKP_g_tem[qual] then
//{{KK_FIMSE:KK_PAINEL_CHEFE_BT}}
        return false
//{{KK_SE:KK_PAINEL_CHEFE_BT}}
        endif
//{{KK_FIMSE:KK_PAINEL_CHEFE_BT}}
//{{KK_SE:KK_PAINEL_EXTRA}}
        endif
//{{KK_FIMSE:KK_PAINEL_EXTRA}}
    endif
    call TriggerEvaluate(KKP_tg(qual))
    return true
endfunction
//{{KK_SE:KK_PAINEL_PADRAO}}

function KKP_heroi_auto takes integer pid returns unit
    local unit u
    local integer n=-1
    set KKP_au_u=null
    if pid<0 or pid>=KKP_jogadores or KKP_g_auto==null then
        return null
    endif
    call GroupEnumUnitsOfPlayer(KKP_g_auto, Player(pid), null)
    loop
        set u=FirstOfGroup(KKP_g_auto)
        exitwhen u==null
        call GroupRemoveUnit(KKP_g_auto, u)
        if IsUnitType(u, UNIT_TYPE_HERO) and not IsUnitType(u, UNIT_TYPE_DEAD) and not IsUnitIllusion(u) and GetHeroLevel(u)>n then
            set KKP_au_u=u
            set n=GetHeroLevel(u)
        endif
    endloop
    return KKP_au_u
endfunction
//{{KK_FIMSE:KK_PAINEL_PADRAO}}

function KKP_amostra takes integer pid returns nothing
    local unit h
    set KKP_arg_pid=pid
//{{KK_SE:KK_PAINEL_EXTRA}}
    set KKP_f_link[pid]=0
    set KKP_f_link_tx[pid]=""
//{{KK_FIMSE:KK_PAINEL_EXTRA}}
    set KKP_h_pv[pid]=0
    call KKP_chama(KKP_G_FICHA)
    set h=KKP_heroi[pid]
    if h==null or GetUnitTypeId(h)==0 then
        set KKP_h_ok[pid]=false
        set KKP_h_pv[pid]=0
        set h=null
        return
    endif
    set KKP_h_ok[pid]=true
    if KKP_h_pv[pid]==0 then
        set KKP_h_pv[pid]=GetUnitTypeId(h)
    endif
    set KKP_h_tipo[pid]=GetUnitTypeId(h)
    set KKP_h_nome[pid]=GetUnitName(h)
    set KKP_h_nivel[pid]=GetHeroLevel(h)
    set KKP_h_for[pid]=GetHeroStr(h, false)
    set KKP_h_agi[pid]=GetHeroAgi(h, false)
    set KKP_h_int[pid]=GetHeroInt(h, false)
    set KKP_h_forb[pid]=GetHeroStr(h, true)
    set KKP_h_agib[pid]=GetHeroAgi(h, true)
    set KKP_h_intb[pid]=GetHeroInt(h, true)
    set KKP_h_vida[pid]=R2I(GetWidgetLife(h))
    set KKP_h_vidamax[pid]=BlzGetUnitMaxHP(h)
    set KKP_h_mana[pid]=R2I(GetUnitState(h, UNIT_STATE_MANA))
    set KKP_h_manamax[pid]=BlzGetUnitMaxMana(h)
    set KKP_h_arm[pid]=BlzGetUnitArmor(h)
    set KKP_h_dano1[pid]=BlzGetUnitBaseDamage(h, 0)+BlzGetUnitDiceNumber(h, 0)
    set KKP_h_dano2[pid]=BlzGetUnitBaseDamage(h, 0)+BlzGetUnitDiceNumber(h, 0)*BlzGetUnitDiceSides(h, 0)
    set KKP_h_cd[pid]=BlzGetUnitAttackCooldown(h, 0)
    set KKP_h_vel[pid]=R2I(GetUnitMoveSpeed(h))
    set h=null
endfunction

function KKP_amostra_grade takes integer pid returns nothing
    local integer s=1
    local integer b
    local integer i
    local integer n
    loop
        exitwhen s>10
        set b=pid*16+s
        set n=KKP_g_n[b]
        if n>KKP_GE then
            set n=KKP_GE
        endif
        set i=0
        loop
            exitwhen i>=n
            set KKP_g_tit[b*KKP_GE+i]=""
//{{KK_SE:KK_PAINEL_IMG}}
            set KKP_g_img[b*KKP_GE+i]=""
            set KKP_g_img_l[b*KKP_GE+i]=0.0
            set KKP_g_img_a[b*KKP_GE+i]=0.0
//{{KK_FIMSE:KK_PAINEL_IMG}}
            if KKU_PV_N>0 then
                set KKP_g_pv[b*KKP_GE+i]=0
            endif
            set i=i+1
        endloop
        set s=s+1
    endloop
    set KKP_arg_pid=pid
    set KKP_arg_aba=KKP_aba[pid]
    call KKP_chama(KKP_G_GRADE)
endfunction

function KKP_fav_le takes integer pid returns nothing
    local string s
    local integer i=0
    local integer x
    set KKP_arg_pid=pid
    set KKP_arg_ok=true
    set KKP_arg_s=""
    call KKP_chama(KKP_G_FAV_LE)
    if not KKP_arg_ok then
        return
    endif
    set s=KKP_arg_s
    if s==null then
        set s=""
    endif
    call FlushChildHashtable(KKP_ht, 910000+pid)
    set KKP_favn[pid]=0
    loop
        exitwhen i+4>StringLength(s) or KKP_favn[pid]>=40
        set x=KKP_s2id(SubString(s, i, i+4))
        if KKP_idx(x)>0 and not LoadBoolean(KKP_ht, 910000+pid, x) then
            set KKP_favn[pid]=KKP_favn[pid]+1
            set KKP_fav[pid*64+KKP_favn[pid]]=x
            call SaveBoolean(KKP_ht, 910000+pid, x, true)
        endif
        set i=i+4
    endloop
    set KKP_fav_ok[pid]=true
endfunction

function KKP_fav_troca takes player p,integer x returns nothing
    local integer pid=GetPlayerId(p)
    local integer i=1
    local integer j
    local string s=""
    if pid<0 or pid>=KKP_jogadores or KKP_idx(x)<1 then
        return
    endif
    if not KKP_fav_ok[pid] then
        call KKP_fav_le(pid)
    endif
    if LoadBoolean(KKP_ht, 910000+pid, x) then
        call RemoveSavedBoolean(KKP_ht, 910000+pid, x)
        loop
            exitwhen i>KKP_favn[pid]
            if KKP_fav[pid*64+i]==x then
                set j=i
                loop
                    exitwhen j>=KKP_favn[pid]
                    set KKP_fav[pid*64+j]=KKP_fav[pid*64+j+1]
                    set j=j+1
                endloop
                set KKP_favn[pid]=KKP_favn[pid]-1
                exitwhen true
            endif
            set i=i+1
        endloop
    elseif KKP_favn[pid]<40 then
        set KKP_favn[pid]=KKP_favn[pid]+1
        set KKP_fav[pid*64+KKP_favn[pid]]=x
        call SaveBoolean(KKP_ht, 910000+pid, x, true)
    else
        call DisplayTextToPlayer(p, 0, 0, "|cffff5555Favorites are full (40). Remove one first.|r")
        return
    endif
    set i=1
    loop
        exitwhen i>KKP_favn[pid]
        set s=s+KKP_id2s(KKP_fav[pid*64+i])
        set i=i+1
    endloop
    if not KKP_fav_ok[pid] then
        return
    endif
    set KKP_arg_pid=pid
    set KKP_arg_s=s
    call KKP_chama(KKP_G_FAV_GRAVA)
endfunction

function KKP_registra takes integer cod,integer t returns nothing
    if t>0 then
        call SaveBoolean(KKP_ht, 940000, cod, true)
        call SaveBoolean(KKP_ht, 940001, t, true)
    endif
endfunction

function KKP_meu takes integer cod,integer t returns boolean
    if cod<1000 or cod>21999 or t<1 then
        return false
    endif
    return LoadBoolean(KKP_ht, 940000, cod) and LoadBoolean(KKP_ht, 940001, t)
endfunction

function KKP_gx takes real x returns real
    return KKU_painel_x+(x+KKP_DX-KKP_X0)*KKU_painel_w/KKP_W0
endfunction

function KKP_gy takes real y returns real
    return KKU_painel_y-(KKP_Y0-y)*KKU_painel_h/KKP_H0
endfunction

function KKP_gw takes real w returns real
    return w*KKU_painel_w/KKP_W0
endfunction

function KKP_gh takes real h returns real
    return h*KKU_painel_h/KKP_H0
endfunction

function KKP_gs takes real s returns real
    return s*RMinBJ(KKU_painel_w/KKP_W0, KKU_painel_h/KKP_H0)
endfunction

function KKP_img takes integer pai,integer papel,real x,real y,real w,real h returns integer
    return KKU_img(pai, papel, KKP_gx(x), KKP_gy(y), KKP_gw(w), KKP_gh(h))
endfunction

function KKP_quad takes integer pai,integer papel,real x,real y,real s returns integer
    return KKU_img(pai, papel, KKP_gx(x), KKP_gy(y), KKP_gs(s), KKP_gs(s))
endfunction

function KKP_sobre takes integer pai,integer papel,integer i_ico,real dx,real dy,real s returns integer
    return KKU_img(pai, papel, KKU_x[i_ico]+KKP_gs(dx), KKU_y[i_ico]+KKP_gs(dy), KKP_gs(s), KKP_gs(s))
endfunction

function KKP_caixa_nova takes integer pai,boolean apertada,real x,real y,real w,real h returns integer
    if apertada then
        return KKU_caixa(pai, KKU_P_CAIXA_ATIVA, KKP_gx(x), KKP_gy(y), KKP_gw(w), KKP_gh(h))
    endif
    return KKU_caixa(pai, KKU_P_CAIXA, KKP_gx(x), KKP_gy(y), KKP_gw(w), KKP_gh(h))
endfunction

function KKP_txt takes integer pai,integer fonte,real x,real y,real w,real h returns integer
    return KKU_txt(pai, fonte, KKP_gx(x), KKP_gy(y), KKP_gw(w), KKP_gh(h))
endfunction

function KKP_pag_nova takes integer pai returns integer
    local integer i=KKU_pagina(pai)
    if i>0 and i<KKU_MAX then
        call KKU_poe(i, KKU_x[i], KKU_y[i], 0.0, 0.0)
    endif
    return i
endfunction

function KKP_bt takes integer pai,integer i_desenho,integer cod,boolean roda returns integer
    local integer t=KKU_alvo(pai, i_desenho, cod, roda)
    call KKP_registra(cod, t)
    return t
endfunction

function KKP_btxt takes integer pai,string rot,real x,real y,real w,real h,integer cod returns integer
    local integer b=KKU_botao(pai, rot, KKP_gx(x), KKP_gy(y), KKP_gw(w), KKP_gh(h), cod)
    if b>0 and b<KKU_MAX then
        call SaveInteger(KKP_ht, cod, 0, b)
        call KKP_registra(cod, KKU_ult_alvo)
    endif
    return b
endfunction

function KKP_bpapel takes integer pai,integer papel,string rot,real x,real y,real w,real h,integer cod returns integer
    local real gx=KKP_gx(x)
    local real gy=KKP_gy(y)
    local real gw=KKP_gw(w)
    local real gh=KKP_gh(h)
    local real lado=RMinBJ(gw, gh)
    local integer b
    if rot=="" then
        set gx=gx+(gw-lado)/2.0
        set gy=gy-(gh-lado)/2.0
        set gw=lado
        set gh=lado
    endif
    set b=KKU_botao_papel(pai, papel, rot, gx, gy, gw, gh, cod)
    if b>0 and b<KKU_MAX then
        call SaveInteger(KKP_ht, cod, 0, b)
        call SaveInteger(KKP_ht, cod, 2, KKU_ult_alvo)
        call KKP_registra(cod, KKU_ult_alvo)
    endif
    return b
endfunction

function KKP_linha takes integer pai,real x,real y,real w,real h,integer cod,boolean ico,boolean info returns integer
    local integer l=KKU_linha_op(pai, KKP_gx(x), KKP_gy(y), KKP_gw(w), KKP_gh(h), cod, ico, info, true)
    if l>0 and l<KKU_MAX then
        call SaveInteger(KKP_ht, cod, 1, l)
        call KKP_registra(cod, KKU_ult_alvo)
    endif
    return l
endfunction

function KKP_vis takes integer i,boolean v returns nothing
    if i>0 and i<KKU_MAX then
        call KKU_vis(i, v)
    endif
endfunction

function KKP_lin takes integer cod,boolean v,string s,string ico,boolean ativa,boolean travada returns nothing
    local integer l=LoadInteger(KKP_ht, cod, 1)
    if l<1 or l>=KKU_MAX then
        return
    endif
    if v then
        set KKP_l_at[l]=ativa
        set KKP_l_tr[l]=travada
        call KKU_linha_texto(l, s)
        call KKU_linha_icone(l, ico)
    endif
    call KKU_linha_mostra(l, v, KKP_l_at[l], KKP_l_tr[l])
    if v and KKU_lin_ico[l]>0 and not KKP_tem_ico(ico) then
        call KKU_vis(KKU_lin_ico[l], false)
    endif
    if KKP_l_at[l] and KKP_l_tr[l] and KKU_lin_txt[l]>0 then
        call KKU_texto(KKU_lin_txt[l], KKU_cor_ativo+KKU_cor_travado+KKU_rot[KKU_lin_txt[l]]+"|r|r")
    endif
endfunction

function KKP_rot takes integer cod,string s,boolean ativo returns nothing
    local integer b=LoadInteger(KKP_ht, cod, 0)
    if b>0 then
        if ativo then
            call KKU_texto(b+2, KKU_cor_ativo+s+"|r")
        elseif KKU_cor_inativo==KKP_COR_FONTE then
            call KKU_texto(b+2, KKP_COR_BOTAO+s+"|r")
        else
            call KKU_texto(b+2, KKU_cor_inativo+s+"|r")
        endif
    endif
endfunction

function KKP_brot takes integer cod,string s returns nothing
    local integer b=LoadInteger(KKP_ht, cod, 0)
    if b>0 then
        call KKU_texto(b+2, s)
    endif
endfunction

function KKP_bvis takes integer cod,boolean v returns nothing
    call KKP_vis(LoadInteger(KKP_ht, cod, 0), v)
endfunction

function KKP_seta_k takes integer cod returns integer
    local integer g=cod/1000
    local integer k
//{{KK_SE:KK_PAINEL_DROPS}}
    if cod==13003 or cod==13004 then
        return cod-12992
    endif
//{{KK_FIMSE:KK_PAINEL_DROPS}}
    if g==5 then
        set k=0
    elseif g==11 then
        set k=2
    elseif g==15 then
        set k=4
    elseif g==21 then
        set k=6
    elseif g==18 then
        set k=8
    else
        return 0
    endif
    if ModuloInteger(cod, 10)==1 then
        return k+1
    endif
    return k+2
endfunction

function KKP_seta takes integer cod,boolean ativa returns nothing
    local integer k=KKP_seta_k(cod)
    if k<1 then
        return
    endif
    call KKU_alvo_mouse(LoadInteger(KKP_ht, cod, 2), ativa)
    if KKP_st_cod[k]!=cod or KKP_st_at[k]!=ativa then
        set KKP_st_cod[k]=cod
        set KKP_st_at[k]=ativa
        set KKP_st_pend=true
    endif
endfunction

//{{KK_SE:KK_PAINEL_DROPS}}
function KKP_seta_um takes integer k returns nothing
    local integer b
    local string rot
        if KKP_st_cod[k]!=0 then
            set b=LoadInteger(KKP_ht, KKP_st_cod[k], 0)
            if ModuloInteger(k, 2)==1 then
                set rot=KKU_ROT_SETA_ESQ
            else
                set rot=KKU_ROT_SETA_DIR
            endif
            if b>0 and b+2<KKU_MAX then
                if rot=="" then
                    if KKP_st_at[k] then
                        call KKU_alfa(b, 255)
                    else
                        call KKU_alfa(b, KKP_SETA_ALFA)
                    endif
                elseif KKP_st_at[k] then
                    call KKU_texto(b+2, rot)
                else
                    call KKU_texto(b+2, KKU_cor_travado+rot+"|r")
                endif
            endif
        endif
endfunction

//{{KK_FIMSE:KK_PAINEL_DROPS}}
function KKP_setas_aplica takes nothing returns nothing
    local integer k=1
    local integer b
    local string rot
    set KKP_st_pend=false
    loop
        exitwhen k>10
        if KKP_st_cod[k]!=0 then
            set b=LoadInteger(KKP_ht, KKP_st_cod[k], 0)
            if ModuloInteger(k, 2)==1 then
                set rot=KKU_ROT_SETA_ESQ
            else
                set rot=KKU_ROT_SETA_DIR
            endif
            if b>0 and b+2<KKU_MAX then
                if rot=="" then
                    if KKP_st_at[k] then
                        call KKU_alfa(b, 255)
                    else
                        call KKU_alfa(b, KKP_SETA_ALFA)
                    endif
                elseif KKP_st_at[k] then
                    call KKU_texto(b+2, rot)
                else
                    call KKU_texto(b+2, KKU_cor_travado+rot+"|r")
                endif
            endif
        endif
        set k=k+1
    endloop
//{{KK_SE:KK_PAINEL_DROPS}}
    call KKP_seta_um(11)
    call KKP_seta_um(12)
//{{KK_FIMSE:KK_PAINEL_DROPS}}
endfunction

//{{KK_SE:KK_PAINEL_BOLSA}}
function KKP_tem_bolsa takes integer pid,integer x returns integer
    local integer n=0
    local integer k=0
    local integer s
    local integer ns
    local unit u
    local item it
    loop
        exitwhen k>4
        if k==0 then
            set u=KKP_heroi[pid]
        else
            set u=KKP_inv_u[pid*4+k-1]
        endif
        if u!=null then
            set ns=6+UnitExtendedInventorySize(u)
            set s=0
            loop
                exitwhen s>=ns
                if s<6 then
                    set it=UnitItemInSlot(u, s)
                else
                    set it=UnitItemInBagSlot(u, s-6)
                endif
                if it!=null and GetItemTypeId(it)==x then
                    if GetItemCharges(it)>1 then
                        set n=n+GetItemCharges(it)
                    else
                        set n=n+1
                    endif
                endif
                set s=s+1
            endloop
        endif
        set k=k+1
    endloop
    set u=null
    set it=null
    return n
endfunction

//{{KK_FIMSE:KK_PAINEL_BOLSA}}
function KKP_tem takes integer pid,integer x returns integer
    local integer n=0
    local integer k=0
    local integer s
    local unit u
    local item it
//{{KK_SE:KK_PAINEL_BOLSA}}
    set n=KKP_tem_bolsa(pid, x)
    set k=5
//{{KK_FIMSE:KK_PAINEL_BOLSA}}
    loop
        exitwhen k>4
        if k==0 then
            set u=KKP_heroi[pid]
        else
            set u=KKP_inv_u[pid*4+k-1]
        endif
        if u!=null then
            set s=0
            loop
                exitwhen s>5
                set it=UnitItemInSlot(u, s)
                if it!=null and GetItemTypeId(it)==x then
                    if GetItemCharges(it)>1 then
                        set n=n+GetItemCharges(it)
                    else
                        set n=n+1
                    endif
                endif
                set s=s+1
            endloop
        endif
        set k=k+1
    endloop
//{{KK_SE:KK_PAINEL_CRAFT}}
    set n=n+LoadInteger(KKP_ht, 930000+pid, x)
//{{KK_FIMSE:KK_PAINEL_CRAFT}}
    set u=null
    set it=null
    return n
endfunction

function KKP_pv_tem takes integer chave returns boolean
    local integer j=1
    if chave==0 then
        return false
    endif
    loop
        exitwhen j>KKU_PV_N
        if KKU_pv_chave[j]==chave then
            return true
        endif
        set j=j+1
    endloop
    return false
endfunction

function KKP_pv_desenha takes integer lugar,integer cx,integer rot,integer al,integer alb,integer chave,real x,real y,real h returns boolean
    local boolean tem
    local boolean mostra=false
    if lugar<=0 then
        return false
    endif
    set tem=KKP_pv_tem(chave)
    call KKP_vis(cx, tem)
    call KKP_vis(rot, tem)
    call KKU_casa_estado(cx, false, false, KKU_pv_ligada and not KKU_pv_bloqueada)
    call KKU_alvo_vis(al, tem and not KKU_pv_bloqueada)
    call KKU_alvo_vis(alb, tem and KKU_pv_bloqueada)
    if tem and not KKP_pv_espera then
        set mostra=KKU_previa(lugar, chave, x, y, h)
    endif
    call KKP_vis(lugar, mostra)
    return mostra
endfunction

function KKP_des_ficha takes integer pid returns nothing
    local string s
    local integer chave=0
//{{KK_SE:KK_PAINEL_EXTRA}}
    local integer lk=KKP_f_link[pid]
    local boolean lv=false
//{{KK_FIMSE:KK_PAINEL_EXTRA}}
    if KKP_h_ok[pid] then
        set chave=KKP_h_pv[pid]
    endif
    call KKP_pv_desenha(KKP_pv_ficha, KKP_pv_cx_ficha, KKP_pv_rot_ficha, KKP_pv_al_ficha, KKP_pv_alb_ficha, chave, KKP_gx(KKP_PV_FX), KKP_gy(KKP_PV_FY), KKP_gs(KKP_PV_FH))
    call KKP_vis(KKP_f_ico, true)
    if not KKP_h_ok[pid] then
        call KKU_tex(KKP_f_ico, "ReplaceableTextures\\CommandButtons\\BTNSelectHeroOn.blp")
        call KKU_texto(KKP_f_nome, "|cffffcc00"+KKP_txt_sem_heroi+"|r")
        call KKU_texto(KKP_f_stat, "")
    else
        call KKU_tex(KKP_f_ico, KKP_ico_vale(BlzGetAbilityIcon(KKP_h_tipo[pid])))
        call KKU_texto(KKP_f_nome, "|cffffcc00"+KKP_h_nome[pid]+"|r|nLevel "+I2S(KKP_h_nivel[pid]))
        set s="|cffffcc00Strength:|r "+KKP_mil(KKP_h_forb[pid])+"|n|cff999999   base "+KKP_mil(KKP_h_for[pid])+"|r"
        set s=s+"|n|cffffcc00Agility:|r "+KKP_mil(KKP_h_agib[pid])+"|n|cff999999   base "+KKP_mil(KKP_h_agi[pid])+"|r"
        set s=s+"|n|cffffcc00Intelligence:|r "+KKP_mil(KKP_h_intb[pid])+"|n|cff999999   base "+KKP_mil(KKP_h_int[pid])+"|r"
        set s=s+"|n|n|cffffcc00HP:|r "+KKP_mil(KKP_h_vida[pid])+" / "+KKP_mil(KKP_h_vidamax[pid])
        set s=s+"|n|cffffcc00MP:|r "+KKP_mil(KKP_h_mana[pid])+" / "+KKP_mil(KKP_h_manamax[pid])
        set s=s+"|n|cffffcc00Armor:|r "+R2SW(KKP_h_arm[pid], 1, 1)
        set s=s+"|n|cffffcc00Damage:|r "+KKP_mil(KKP_h_dano1[pid])+" - "+KKP_mil(KKP_h_dano2[pid])
        set s=s+"|n|cffffcc00Attack cooldown:|r "+R2SW(KKP_h_cd[pid], 1, 2)+" s"
        set s=s+"|n|cffffcc00Move speed:|r "+I2S(KKP_h_vel[pid])
        call KKU_texto(KKP_f_stat, s)
    endif
    set s=KKP_x_mapa[pid]
    if s==null then
        set s=""
    endif
    call KKU_texto(KKP_f_mapa, s)
//{{KK_SE:KK_PAINEL_EXTRA}}
    if KKP_f_lico>0 then
        set lv=KKP_h_ok[pid] and lk!=0 and KKP_idx(lk)>0
        call KKP_vis(KKP_f_lico, lv)
        call KKP_vis(KKP_f_ltxt, lv)
        call KKU_alvo_vis(KKP_f_lbt, lv)
        if lv then
            set s=KKP_f_link_tx[pid]
            if s==null then
                set s=""
            endif
            call KKU_tex(KKP_f_lico, KKP_ico_item(lk))
            call KKU_texto(KKP_f_ltxt, s+KKP_nome_item(lk))
        endif
    endif
//{{KK_FIMSE:KK_PAINEL_EXTRA}}
endfunction

function KKP_c_tam takes integer pid returns integer
    if KKP_c_q!="" then
        return KKP_res_n
    elseif KKP_c_cat==0 then
        return KKP_favn[pid]
    endif
    return KKP_cat_qt[KKP_c_cat]
endfunction

function KKP_c_item takes integer pid,integer i returns integer
    if KKP_c_q!="" then
        return KKP_res[i]
    elseif KKP_c_cat==0 then
        return KKP_idx(KKP_fav[pid*64+i])
    endif
    return KKP_cat_ini[KKP_c_cat]+i-1
endfunction

function KKP_des_codex_lista takes nothing returns nothing
    local integer pid=GetPlayerId(GetLocalPlayer())
    local integer n=KKP_c_tam(pid)
    local integer s=1
    local integer k=0
    local integer x
    local string nome
    loop
        exitwhen k>KKP_cat_n
        if k==0 then
            call KKP_lin(3000, true, "Favorites", "", KKP_c_q=="" and KKP_c_cat==0, false)
        else
            call KKP_lin(3000+k, true, KKP_cat_nome[k], "", KKP_c_q=="" and KKP_c_cat==k, false)
        endif
        set k=k+1
    endloop
    if KKP_c_top>n-11 then
        set KKP_c_top=n-11
    endif
    if KKP_c_top<0 then
        set KKP_c_top=0
    endif
    loop
        exitwhen s>11
        if KKP_c_top+s<=n then
            set x=KKP_c_item(pid, KKP_c_top+s)
            set KKP_c_lin[s]=x
            set nome=KKP_nome_item(KKP_it[x])
            if LoadBoolean(KKP_ht, 910000+pid, KKP_it[x]) then
                set nome=nome+"|r |cffffcc00*|r"
            endif
            call KKP_lin(4000+s, true, nome, KKP_ico_item(KKP_it[x]), x==KKP_c_sel, false)
        else
            set KKP_c_lin[s]=0
            call KKP_lin(4000+s, false, "", "", false, false)
        endif
        set s=s+1
    endloop
    call KKU_texto(KKP_c_pag, KKP_pagina(KKP_c_top, 11, n))
    call KKP_seta(5001, KKP_c_top>0)
    call KKP_seta(5002, KKP_c_top+11<n)
    if KKP_c_q!="" then
        if KKP_res_i>0 then
            call KKU_texto(KKP_c_btxt, "|cff999999Searching...|r")
        elseif n==1 then
            call KKU_texto(KKP_c_btxt, "|cffffcc001|r result for \""+KKP_c_q+"\"")
        else
            call KKU_texto(KKP_c_btxt, "|cffffcc00"+I2S(n)+"|r results for \""+KKP_c_q+"\"")
        endif
    elseif KKP_c_cat==0 then
        call KKU_texto(KKP_c_btxt, "|cffffcc00Favorites|r: "+I2S(n)+" |cff999999(open an item, click Favorite)|r")
    else
        call KKU_texto(KKP_c_btxt, "|cffffcc00"+KKP_cat_nome[KKP_c_cat]+"|r: "+I2S(n)+" items")
    endif
endfunction

function KKP_des_codex_det takes nothing returns nothing
    local integer pid=GetPlayerId(GetLocalPlayer())
    local integer x=KKP_c_sel
    local integer id
    local integer r
    local integer n=0
    local integer m=1
    local integer k
    local integer ing
    local integer q
    local integer tem
    local integer prontos=0
    local integer un
    local boolean ok
    local boolean vis=(x>0 and x<=KKP_it_n)
    local string s
    local string rs=""
    loop
        exitwhen m>8
        call KKP_vis(KKP_c_rico[m], false)
        call KKU_alvo_vis(KKP_c_rbt[m], false)
        call KKP_vis(KKP_c_rqt[m], false)
        call KKP_vis(KKP_c_rok[m], false)
        set m=m+1
    endloop
    set m=1
    loop
        exitwhen m>6
        call KKP_vis(KKP_c_uico[m], false)
        call KKU_alvo_vis(KKP_c_ubt[m], false)
        set m=m+1
    endloop
    call KKP_vis(KKP_c_dico, vis)
    call KKP_vis(KKP_c_dnome, vis)
    call KKP_vis(KKP_c_dsub, vis)
    call KKP_vis(KKP_c_rtit, vis)
    call KKP_vis(KKP_c_utit, vis)
    call KKP_bvis(6003, vis)
    call KKP_bvis(6004, false)
    call KKP_bvis(6005, false)
//{{KK_SE:KK_PAINEL_CRAFT}}
    call KKP_bvis(6007, false)
//{{KK_FIMSE:KK_PAINEL_CRAFT}}
//{{KK_SE:KK_PAINEL_EXTRA}}
    call KKP_bvis(6008, false)
//{{KK_FIMSE:KK_PAINEL_EXTRA}}
    if not vis then
        call KKU_texto(KKP_c_desc, "|cffffcc00"+KKP_titulo+"|r|n|n"+KKP_txt_codex)
        return
    endif
    set id=KKP_it[x]
    call KKU_tex(KKP_c_dico, KKP_ico_item(id))
    call KKU_texto(KKP_c_dnome, KKP_nome_item(id))
    call KKU_texto(KKP_c_dsub, "|cff999999"+KKP_cat_nome[KKP_it_cat[x]]+"|r")
    if LoadBoolean(KKP_ht, 910000+pid, id) then
        call KKP_rot(6003, "Unfavorite", true)
    else
        call KKP_rot(6003, "Favorite", false)
    endif
//{{KK_SE:KK_PAINEL_CRAFT}}
    call KKP_bvis(6007, KKP_g_tem[KKP_G_CRAFT] and KKP_it_rc[x]>0)
//{{KK_FIMSE:KK_PAINEL_CRAFT}}
//{{KK_SE:KK_PAINEL_EXTRA}}
    call KKP_bvis(6008, KKP_b3_rot!="" and KKP_it_b3ok[x] and not KKP_b3_fora[pid])
//{{KK_FIMSE:KK_PAINEL_EXTRA}}
    set r=KKP_it_rc[x]
    if r>0 then
        set n=IMinBJ(KKP_rc_ingn[r], 8)
    endif
    set KKP_c_rec_n=n
    set m=1
    loop
        exitwhen m>n
        set k=KKP_rc_ini[r]+m-1
        set ing=KKP_ing[k]
        set q=KKP_ing_qt[k]
        set tem=KKP_tem(pid, ing)
        set ok=tem>=IMaxBJ(q, 1)
        set KKP_c_rec[m]=ing
        call KKU_tex(KKP_c_rico[m], KKP_ico_item(ing))
        call KKP_vis(KKP_c_rico[m], true)
        call KKU_alvo_vis(KKP_c_rbt[m], KKP_idx(ing)>0)
        call KKP_vis(KKP_c_rok[m], ok)
        if q>1 then
            if ok then
                call KKU_texto(KKP_c_rqt[m], "|cff00ff00"+I2S(tem)+"/"+I2S(q)+"|r")
            else
                call KKU_texto(KKP_c_rqt[m], "|cffff5555"+I2S(tem)+"/"+I2S(q)+"|r")
            endif
            call KKP_vis(KKP_c_rqt[m], true)
        endif
        if m>1 then
            set rs=rs+", "
        endif
        set rs=rs+KKP_nome_item(ing)+"|r"
        if q>1 then
            set rs=rs+" x"+I2S(q)
        endif
        if ok then
            set rs=rs+" |cff00ff00(carried)|r"
            set prontos=prontos+1
        endif
        set m=m+1
    endloop
    if n>0 then
        set s="|cffffcc00Recipe|r  "+I2S(prontos)+"/"+I2S(n)+" carried"
        if KKP_it_rcn[x]>1 then
            set s=s+" |cff999999(+"+I2S(KKP_it_rcn[x]-1)+" more)|r"
        endif
        call KKU_texto(KKP_c_rtit, s)
    else
        call KKU_texto(KKP_c_rtit, "|cffffcc00Recipe|r  |cff999999none: this item is not crafted|r")
    endif
    set un=KKP_it_usn[x]
    if KKP_c_utop>un-6 then
        set KKP_c_utop=un-6
    endif
    if KKP_c_utop<0 then
        set KKP_c_utop=0
    endif
    set m=1
    loop
        exitwhen m>6
        if KKP_c_utop+m<=un then
            call KKU_tex(KKP_c_uico[m], KKP_ico_item(KKP_it[KKP_us[KKP_it_us[x]+KKP_c_utop+m-1]]))
            call KKP_vis(KKP_c_uico[m], true)
            call KKU_alvo_vis(KKP_c_ubt[m], true)
        endif
        set m=m+1
    endloop
    call KKP_bvis(6004, KKP_c_utop>0)
    call KKP_bvis(6005, KKP_c_utop+6<un)
    if un>0 then
        call KKU_texto(KKP_c_utit, "|cffffcc00Used in|r  "+I2S(un)+" recipes |cff999999(click to open)|r")
    else
        call KKU_texto(KKP_c_utit, "|cffffcc00Used in|r  |cff999999no recipe uses this item|r")
    endif
    set s=""
    if n>0 then
        set s="|cffffcc00Recipe:|r "+rs
        if KKP_rc_ouro[r]>0 then
            set s=s+" + "+KKP_mil(KKP_rc_ouro[r])+" gold"
        endif
        if KKP_rc_madeira[r]>0 then
            set s=s+" + "+KKP_mil(KKP_rc_madeira[r])+" lumber"
        endif
        if KKP_txt_receita!="" then
            set s=s+"|n|cff999999("+KKP_txt_receita+")|r"
        endif
        set s=s+"|n|n"
    endif
    set s=s+BlzGetAbilityExtendedTooltip(id, 0)
//{{KK_SE:KK_PAINEL_EXTRA}}
    if id!=0 and KKP_dm_k[1]==id then
        if KKP_dm_s[1]!=null and KKP_dm_s[1]!="" then
            set s=s+"|n|n|r"+KKP_dm_s[1]
        endif
        call KKU_texto(KKP_c_desc, s)
        return
    endif
//{{KK_FIMSE:KK_PAINEL_EXTRA}}
    set m=1
    if KKP_it_dpn[x]>0 then
        set s=s+"|n|n|r|cffffcc00Dropped by|r |cff999999(chance per kill, "+KKP_txt_taxa+")|r"
        loop
            exitwhen m>KKP_it_dpn[x] or m>14
            set k=KKP_it_dp[x]+m-1
            set s=s+"|n"+KKP_nome_chefe(KKP_dp_bs[k])+"|r: "+KKP_taxa_txt(KKP_dp_tipo[k], KKP_dp_taxa[k], pid)
            if KKP_dp_qt[k]>1 then
                set s=s+" x"+I2S(KKP_dp_qt[k])
            endif
            set m=m+1
        endloop
        if KKP_it_dpn[x]>14 then
            set s=s+"|n|cff999999+"+I2S(KKP_it_dpn[x]-14)+" more|r"
        endif
    endif
    call KKU_texto(KKP_c_desc, s)
endfunction

function KKP_des_chefe_lista takes nothing returns nothing
    local integer g=KKP_b_grupo
    local integer n=KKP_gr_qt[g]
    local integer s=1
    local integer k=1
    local integer j
    loop
        exitwhen k>KKP_gr_n
        call KKP_rot(9000+k, KKP_gr_nome[k], k==g)
        set k=k+1
    endloop
    if KKP_b_top>n-11 then
        set KKP_b_top=n-11
    endif
    if KKP_b_top<0 then
        set KKP_b_top=0
    endif
    loop
        exitwhen s>11
        if KKP_b_top+s<=n then
            set j=KKP_gr_ini[g]+KKP_b_top+s-1
            set KKP_b_lin[s]=j
            call KKP_lin(10000+s, true, KKP_nome_chefe(j)+"|r |cff999999Lv "+I2S(KKP_bs_nivel[j])+"|r", KKP_ico_chefe(j), j==KKP_b_sel, false)
        else
            set KKP_b_lin[s]=0
            call KKP_lin(10000+s, false, "", "", false, false)
        endif
        set s=s+1
    endloop
    call KKU_texto(KKP_b_pag, KKP_pagina(KKP_b_top, 11, n))
    call KKP_seta(11001, KKP_b_top>0)
    call KKP_seta(11002, KKP_b_top+11<n)
endfunction

//{{KK_SE:KK_PAINEL_DROPS}}
function KKP_des_chefe_dpag takes integer j,integer pid returns nothing
    local integer n=IMinBJ(KKP_bs_drn[j], KKP_DR_TETO)
    local integer m=1
    local integer d
    local integer s
    local integer k
    local integer it
    local string t
    if KKP_b_dtop>((n-1)/10)*10 then
        set KKP_b_dtop=((n-1)/10)*10
    endif
    if KKP_b_dtop<0 then
        set KKP_b_dtop=0
    endif
    loop
        exitwhen m>10 or KKP_b_dtop+m>n
        set d=KKP_b_dtop+m
        set s=m
        if m>5 then
            set s=m+1
        endif
        set k=KKP_bs_dr[j]+d-1
        set it=KKP_dr_it[k]
        set KKP_b_drop[s]=it
        call KKU_tex(KKP_b_dico2[s], KKP_ico_item(it))
        call KKP_vis(KKP_b_dico2[s], true)
        call KKU_alvo_vis(KKP_b_dbt[s], KKP_idx(it)>0)
        set t=KKP_nome_item(it)+"|r|n"+KKP_taxa_txt(KKP_dr_tipo[k], KKP_dr_taxa[k], pid)
        if KKP_dr_qt[k]>1 then
            set t=t+" x"+I2S(KKP_dr_qt[k])
        endif
        call KKU_texto(KKP_b_dtx[s], t)
        if KKP_dm_k[2+d]!=0 and KKP_dm_k[2+d]==KKP_bs_unid[j] then
            call KKU_texto(KKP_b_dtx[s], KKP_dm_s[2+d])
        endif
        call KKP_vis(KKP_b_dtx[s], true)
        set m=m+1
    endloop
    call KKU_texto(KKP_b_dpag, "Drops "+I2S(KKP_b_dtop+1)+"-"+I2S(IMinBJ(KKP_b_dtop+10, n))+" of "+I2S(n))
    call KKP_vis(KKP_b_dpag, true)
    call KKP_bvis(13003, true)
    call KKP_bvis(13004, true)
    call KKP_seta(13003, KKP_b_dtop>0)
    call KKP_seta(13004, KKP_b_dtop+10<n)
endfunction

//{{KK_FIMSE:KK_PAINEL_DROPS}}
function KKP_des_chefe_det takes nothing returns nothing
    local integer pid=GetPlayerId(GetLocalPlayer())
    local integer j=KKP_b_sel
    local boolean vis=(j>0 and j<=KKP_bs_n)
    local integer s=1
    local integer k
    local integer it
    local string t
    call KKP_vis(KKP_b_dico, vis)
    call KKP_vis(KKP_b_dnome, vis)
    call KKP_vis(KKP_b_dinfo, vis)
    call KKP_vis(KKP_b_dtit, vis)
    call KKP_bvis(13001, vis and KKP_bs_pos[j])
//{{KK_SE:KK_PAINEL_CHEFE_BT}}
    call KKP_bvis(13002, vis and KKP_bb_rot!="" and KKP_bs_bok[j] and not KKP_bb_fora[pid])
//{{KK_FIMSE:KK_PAINEL_CHEFE_BT}}
    loop
        exitwhen s>12
        set KKP_b_drop[s]=0
        call KKP_vis(KKP_b_dico2[s], false)
        call KKU_alvo_vis(KKP_b_dbt[s], false)
        call KKP_vis(KKP_b_dtx[s], false)
        set s=s+1
    endloop
//{{KK_SE:KK_PAINEL_DROPS}}
    call KKP_bvis(13003, false)
    call KKP_bvis(13004, false)
    call KKP_vis(KKP_b_dpag, false)
    if KKP_b_dsel!=j then
        set KKP_b_dsel=j
        set KKP_b_dtop=0
    endif
//{{KK_FIMSE:KK_PAINEL_DROPS}}
    if not vis then
        call KKU_texto(KKP_b_dnota, KKP_txt_chefes)
        return
    endif
    call KKU_tex(KKP_b_dico, KKP_ico_chefe(j))
    call KKU_texto(KKP_b_dnome, KKP_nome_chefe(j))
    set t="|cff999999"+KKP_gr_nome[KKP_bs_grupo[j]]+"|r"
    if KKP_bs_nivel[j]>0 then
        set t=t+"  |cffffcc00Level|r "+I2S(KKP_bs_nivel[j])
    endif
    if KKP_bs_vida[j]>0 then
        set t=t+"  |cffffcc00HP|r "+KKP_mil(KKP_bs_vida[j])
    endif
    call KKU_texto(KKP_b_dinfo, t)
    if KKP_bs_nota[j]!=null and KKP_bs_nota[j]!="" then
        call KKU_texto(KKP_b_dnota, KKP_bs_nota[j])
    else
        call KKU_texto(KKP_b_dnota, "")
    endif
    call KKU_texto(KKP_b_dtit, "|cffffcc00Drops|r  "+I2S(KKP_bs_drn[j])+" |cff999999(chance per kill, "+KKP_txt_taxa+")|r")
//{{KK_SE:KK_PAINEL_EXTRA}}
    if KKP_dm_k[2]!=0 and KKP_dm_k[2]==KKP_bs_unid[j] then
        call KKU_texto(KKP_b_dtit, KKP_dm_s[2])
    endif
//{{KK_FIMSE:KK_PAINEL_EXTRA}}
//{{KK_SE:KK_PAINEL_DROPS}}
    if KKP_bs_drn[j]>12 then
        call KKP_des_chefe_dpag(j, pid)
        return
    endif
//{{KK_FIMSE:KK_PAINEL_DROPS}}
    set s=1
    loop
        exitwhen s>12 or s>KKP_bs_drn[j]
        set k=KKP_bs_dr[j]+s-1
        set it=KKP_dr_it[k]
        set KKP_b_drop[s]=it
        call KKU_tex(KKP_b_dico2[s], KKP_ico_item(it))
        call KKP_vis(KKP_b_dico2[s], true)
        call KKU_alvo_vis(KKP_b_dbt[s], KKP_idx(it)>0)
        set t=KKP_nome_item(it)+"|r|n"+KKP_taxa_txt(KKP_dr_tipo[k], KKP_dr_taxa[k], pid)
        if KKP_dr_qt[k]>1 then
            set t=t+" x"+I2S(KKP_dr_qt[k])
        endif
        call KKU_texto(KKP_b_dtx[s], t)
//{{KK_SE:KK_PAINEL_EXTRA}}
        if KKP_dm_k[2+s]!=0 and KKP_dm_k[2+s]==KKP_bs_unid[j] then
            call KKU_texto(KKP_b_dtx[s], KKP_dm_s[2+s])
        endif
//{{KK_FIMSE:KK_PAINEL_EXTRA}}
        call KKP_vis(KKP_b_dtx[s], true)
        set s=s+1
    endloop
endfunction

function KKP_bit takes integer x,integer k returns boolean
    if k==2 then
        return ModuloInteger(x/2, 2)==1
    endif
    return ModuloInteger(x, 2)==1
endfunction

//{{KK_SE:KK_PAINEL_IMG}}
function KKP_des_img takes boolean k3,boolean ok,integer e,integer dtxt returns nothing
    local integer q=1
    local integer img=KKP_g_dimg
    local real w=0.0
    local real h=0.0
    local string s=""
    if k3 then
        set q=2
        set img=KKP_k_dimg
        call KKP_vis(KKP_g_dimg, false)
    else
        call KKP_vis(KKP_k_dimg, false)
    endif
    if img<=0 or img>=KKU_MAX or dtxt<=0 or dtxt>=KKU_MAX then
        return
    endif
    if ok then
        set s=KKP_g_img[e]
    endif
    if s!=null and s!="" then
        set w=KKP_im_w[q]
        if KKP_g_img_l[e]>0.0 then
            set w=RMinBJ(KKP_gw(KKP_g_img_l[e]), KKP_im_w[q])
        endif
        if KKP_g_img_a[e]<=0.0 then
            set h=w*9.0/16.0
        elseif KKP_g_img_l[e]>0.0 then
            set h=KKP_gh(KKP_g_img_a[e])*w/KKP_gw(KKP_g_img_l[e])
        else
            set h=KKP_gh(KKP_g_img_a[e])
        endif
        set h=RMinBJ(h, KKP_im_h[q]-KKP_gh(0.040))
    endif
    if h>0.0 then
        call KKU_tex(img, s)
        call KKU_poe(img, KKP_im_x[q], KKP_im_y[q], w, h)
        call KKP_vis(img, true)
        call KKU_poe(dtxt, KKP_im_x[q], KKP_im_y[q]-h-KKP_gh(0.006), KKP_im_w[q], KKP_im_h[q]-h-KKP_gh(0.006))
    else
        call KKP_vis(img, false)
        call KKU_poe(dtxt, KKP_im_x[q], KKP_im_y[q], KKP_im_w[q], KKP_im_h[q])
    endif
endfunction

//{{KK_FIMSE:KK_PAINEL_IMG}}
function KKP_des_mapa takes nothing returns nothing
    local integer pid=GetPlayerId(GetLocalPlayer())
    local integer a=KKP_aba[pid]
    local integer sub=KKP_g_sub
    local integer b=pid*16+sub
    local integer n=KKP_g_n[b]
    local integer lay=KKP_ab_lay[a*16+sub]
    local integer s=1
    local integer i
    local integer e
    local integer k=1
    local integer c
    local boolean achou=false
    local boolean ok
    local string t
    local integer chave=0
    local boolean k3=lay==3
    local integer dico=KKP_g_dico
    local integer dnome=KKP_g_dnome
    local integer dtxt=KKP_g_dtxt
    local integer bt=17000
    loop
        exitwhen k>10
        if k<=KKP_ab_subn[a] and not k3 then
            call KKP_bvis(16000+k, true)
            call KKP_rot(16000+k, KKP_ab_sub[a*16+k], k==sub)
        else
            call KKP_bvis(16000+k, false)
        endif
        if KKP_tem3 then
            call KKP_lin(18000+k, k3 and k<=KKP_ab_subn[a], KKP_ab_sub[a*16+k], "", k==sub, false)
        endif
        set k=k+1
    endloop
    if n>KKP_GE then
        set n=KKP_GE
    endif
    if lay==2 then
        if KKP_g_top>n-KKP_GL then
            set KKP_g_top=n-KKP_GL
        endif
    elseif k3 then
        if KKP_g_top>n-KKP_KL then
            set KKP_g_top=n-KKP_KL
        endif
    elseif KKP_g_top>n-1 then
        set KKP_g_top=((n-1)/40)*40
    endif
    if KKP_g_top<0 then
        set KKP_g_top=0
    endif
    call KKP_vis(KKP_g_corpo1, lay!=2 and not k3)
    call KKP_vis(KKP_g_corpo2, lay==2)
    if KKP_tem3 then
        call KKP_vis(KKP_g_corpo3, k3)
        call KKP_vis(KKP_g_topo_tx, not k3)
        call KKP_vis(KKP_g_dcx, not k3)
        call KKP_vis(KKP_g_dnome, not k3)
        call KKP_vis(KKP_g_dtxt, not k3)
    endif
    if k3 then
        set dico=KKP_k_dico
        set dnome=KKP_k_dnome
        set dtxt=KKP_k_dtxt
        set bt=18160
        call KKP_vis(KKP_g_dico, false)
        call KKP_bvis(17001, false)
        call KKP_bvis(17002, false)
        if KKP_g_topo[b]!=null then
            call KKU_texto(KKP_k_topo, KKP_g_topo[b])
        else
            call KKU_texto(KKP_k_topo, "")
        endif
    elseif KKP_g_topo[b]!=null then
        call KKU_texto(KKP_g_topo_tx, KKP_g_topo[b])
    else
        call KKU_texto(KKP_g_topo_tx, "")
    endif
    if lay==2 then
        loop
            exitwhen s>KKP_GL
            set i=KKP_g_top+s-1
            if i<n then
                set e=b*KKP_GE+i
                set KKP_g_lin[s]=i
                call KKP_lin(20000+s, true, KKP_g_nome[e], KKP_g_ico[e], i==KKP_g_sel, KKP_g_trava[e])
                if KKP_g_info[e]!=null then
                    call KKU_linha_info(LoadInteger(KKP_ht, 20000+s, 1), KKP_g_info[e])
                else
                    call KKU_linha_info(LoadInteger(KKP_ht, 20000+s, 1), "")
                endif
            else
                set KKP_g_lin[s]=-1
                call KKP_lin(20000+s, false, "", "", false, false)
            endif
            set s=s+1
        endloop
        call KKU_texto(KKP_l_pag, KKP_pagina(KKP_g_top, KKP_GL, n))
        call KKP_seta(21001, KKP_g_top>0)
        call KKP_seta(21002, KKP_g_top+KKP_GL<n)
    elseif k3 then
        loop
            exitwhen s>KKP_KL
            set i=KKP_g_top+s-1
            if i<n then
                set e=b*KKP_GE+i
                set KKP_g_lin[s]=i
                call KKP_lin(18100+s, true, KKP_g_nome[e], KKP_g_ico[e], i==KKP_g_sel, KKP_g_trava[e])
                if KKP_g_info[e]!=null then
                    call KKU_linha_info(LoadInteger(KKP_ht, 18100+s, 1), KKP_g_info[e])
                else
                    call KKU_linha_info(LoadInteger(KKP_ht, 18100+s, 1), "")
                endif
            else
                set KKP_g_lin[s]=-1
                call KKP_lin(18100+s, false, "", "", false, false)
            endif
            set s=s+1
        endloop
        call KKU_texto(KKP_k_pag, KKP_pagina(KKP_g_top, KKP_KL, n))
        call KKP_seta(18151, KKP_g_top>0)
        call KKP_seta(18152, KKP_g_top+KKP_KL<n)
    else
        loop
            exitwhen s>40
            set i=KKP_g_top+s-1
            set c=KKP_g_icof[s]
            if i<n then
                set e=b*KKP_GE+i
                set KKP_g_lin[s]=i
                call KKU_tex(c, KKP_g_ico[e])
                call KKP_vis(c, true)
                if KKP_tem_ico(KKP_g_ico[e]) then
                    call KKU_alfa(c, 255)
                else
                    call KKU_alfa(c, 0)
                endif
                call KKU_alvo_vis(KKP_g_bt[s], true)
                call KKP_vis(KKP_g_dim[s], KKP_g_trava[e])
                call KKP_vis(KKP_g_cur[s], KKP_g_ok[e])
                if i==KKP_g_sel then
                    call KKU_poe(KKP_g_marca, KKU_x[c]-KKP_gs(0.003), KKU_y[c]+KKP_gs(0.003), KKU_w[c]+KKP_gs(0.006), KKU_h[c]+KKP_gs(0.006))
                    set achou=true
                endif
            else
                set KKP_g_lin[s]=-1
                call KKP_vis(c, false)
                call KKU_alvo_vis(KKP_g_bt[s], false)
                call KKP_vis(KKP_g_dim[s], false)
                call KKP_vis(KKP_g_cur[s], false)
            endif
            set s=s+1
        endloop
        call KKP_vis(KKP_g_marca, achou)
        call KKU_texto(KKP_g_pag, KKP_pagina(KKP_g_top, 40, n))
        call KKP_seta(15001, KKP_g_top>0)
        call KKP_seta(15002, KKP_g_top+40<n)
    endif
    set i=KKP_g_sel
    if i<0 or i>=n then
        set i=KKP_g_atual[b]
    endif
    set ok=i>=0 and i<n
    if ok then
        set e=b*KKP_GE+i
        set chave=KKP_g_pv[e]
    endif
    if k3 then
        call KKP_pv_desenha(KKP_pv_det, KKP_pv_cx_det, KKP_pv_rot_det, KKP_pv_al_det, KKP_pv_alb_det, 0, 0.0, 0.0, 0.0)
        call KKP_pv_desenha(KKP_pv_k, KKP_pv_cx_k, KKP_pv_rot_k, KKP_pv_al_k, KKP_pv_alb_k, chave, KKP_gx(KKP_PV_DX), KKP_gy(KKP_PV_KY), KKP_gs(KKP_PV_KH))
    else
        call KKP_pv_desenha(KKP_pv_det, KKP_pv_cx_det, KKP_pv_rot_det, KKP_pv_al_det, KKP_pv_alb_det, chave, KKP_gx(KKP_PV_DX), KKP_gy(KKP_PV_DY), KKP_gs(KKP_PV_DH))
    endif
    if ok then
        call KKU_tex(dico, KKP_g_ico[e])
        call KKP_vis(dico, KKP_tem_ico(KKP_g_ico[e]))
        set t=KKP_g_tit[e]
        if t==null or t=="" then
            set t=KKP_g_nome[e]
        endif
        call KKU_texto(dnome, "|cffffcc00"+t+"|r")
        set t=""
        if KKP_g_trava[e] then
            set t="|cffff5555Locked.|r|n"
        endif
        if KKP_g_edet[e]!=null and KKP_g_edet[e]!="" then
            set t=t+KKP_g_edet[e]
        endif
    else
        set e=0
        call KKP_vis(dico, false)
        call KKU_texto(dnome, "")
        if n>0 then
            set t="|cff999999Pick an entry on the left.|r"
        else
            set t="|cff999999Nothing here yet.|r"
        endif
    endif
    if KKP_g_det[b]!=null and KKP_g_det[b]!="" then
        set t=t+"|n|n"+KKP_g_det[b]
    endif
    call KKU_texto(dtxt, t)
//{{KK_SE:KK_PAINEL_IMG}}
    call KKP_des_img(k3, ok, e, dtxt)
//{{KK_FIMSE:KK_PAINEL_IMG}}
    set k=1
    loop
        exitwhen k>2
        if k==1 then
            set t=KKP_g_b1[b]
        else
            set t=KKP_g_b2[b]
        endif
        if t==null or t=="" then
            call KKP_bvis(bt+k, false)
        elseif KKP_bit(KKP_g_bm[b], k) and not (ok and KKP_bit(KKP_g_eb[e], k)) then
            call KKP_bvis(bt+k, false)
        else
            call KKP_brot(bt+k, t)
            call KKP_bvis(bt+k, true)
        endif
        set k=k+1
    endloop
endfunction

function KKP_des_abas takes integer pid returns nothing
    local integer i=1
    local integer a=KKP_aba[pid]
    local integer t=KKP_aba_tipo[a]
    loop
        exitwhen i>4
        call KKP_vis(KKP_pag[i], i==t)
        set i=i+1
    endloop
    set i=1
    loop
        exitwhen i>KKP_aba_n
        call KKP_rot(1000+i, KKP_aba_nome[i], i==a)
        if KKP_aba_tex then
            if i==a then
                call KKU_tex(LoadInteger(KKP_ht, 1000+i, 0), KKU_tema_tex[KKU_P_ABA_ATIVA])
            else
                call KKU_tex(LoadInteger(KKP_ht, 1000+i, 0), KKU_tema_tex[KKU_P_ABA])
            endif
        endif
        set i=i+1
    endloop
endfunction

//{{KK_SE:KK_PAINEL_CHEFE_BT}}
function KKP_entrada_aplica takes integer pid returns nothing
    local integer i=KKP_g_quer_i
    local integer lay=KKP_ab_lay[KKP_aba[pid]*16+KKP_g_sub]
    if i<0 then
        return
    endif
    if i>=IMinBJ(KKP_g_n[pid*16+KKP_g_sub], KKP_GE) then
        set KKP_g_sel=-1
        return
    endif
    set KKP_g_sel=i
    if lay==2 then
        set KKP_g_top=i-KKP_GL/2
    elseif lay==3 then
        set KKP_g_top=i-KKP_KL/2
    else
        set KKP_g_top=(i/40)*40
    endif
endfunction

//{{KK_FIMSE:KK_PAINEL_CHEFE_BT}}
function KKP_desenha takes boolean detalhe returns nothing
    local integer pid=GetPlayerId(GetLocalPlayer())
    local integer t
    if not KKP_pronto or KKU_rc_fase!=0 or pid<0 or pid>=KKP_jogadores then
        return
    endif
    if not KKP_aberto[pid] then
        return
    endif
    call KKP_des_abas(pid)
    set t=KKP_aba_tipo[KKP_aba[pid]]
    if t==1 then
        call KKP_des_ficha(pid)
    elseif t==2 then
        call KKP_des_codex_lista()
        if detalhe then
            set KKP_c_pend=true
        endif
    elseif t==3 then
        call KKP_des_chefe_lista()
        if detalhe then
            set KKP_b_pend=true
        endif
    elseif t==4 then
        if KKP_g_aba!=KKP_aba[pid] then
            set KKP_g_aba=KKP_aba[pid]
            set KKP_g_sub=1
            set KKP_g_top=0
            set KKP_g_sel=-1
        endif
        if KKP_g_quer>0 and KKP_g_quer<=KKP_ab_subn[KKP_aba[pid]] and KKP_g_quer!=KKP_g_sub then
            set KKP_g_sub=KKP_g_quer
            set KKP_g_top=0
            set KKP_g_sel=-1
        endif
//{{KK_SE:KK_PAINEL_CHEFE_BT}}
        call KKP_entrada_aplica(pid)
//{{KK_FIMSE:KK_PAINEL_CHEFE_BT}}
        call KKP_des_mapa()
    endif
//{{KK_SE:KK_PAINEL_CHEFE_BT}}
    set KKP_g_quer_i=-1
//{{KK_FIMSE:KK_PAINEL_CHEFE_BT}}
    set KKP_g_quer=0
    call KKU_aplica()
endfunction

function KKP_solta_busca takes nothing returns nothing
    if KKP_c_foco then
        set KKP_c_foco=false
        call KKU_campo_foco(KKP_c_busca, false)
    endif
endfunction

function KKP_limpa_busca takes nothing returns nothing
    local string t=BlzFrameGetText(KKU_quadro(KKP_c_busca))
    set KKP_c_q=""
    set KKP_res_i=0
    call KKP_solta_busca()
    if t!=null and t!="" then
        set KKP_c_ign=StringCase(t, false)
        set KKP_c_eco=true
        set KKP_c_eco_t=40
        call KKU_campo_poe(KKP_c_busca, "")
    endif
endfunction

function KKP_abre_item takes integer k returns nothing
    if k<1 or k>KKP_it_n then
        return
    endif
    set KKP_c_sel=k
    set KKP_c_utop=0
    call KKP_limpa_busca()
    set KKP_c_cat=KKP_it_cat[k]
    set KKP_c_top=k-KKP_cat_ini[KKP_c_cat]-5
    set KKP_c_pend=true
endfunction

function KKP_aba_do_tipo takes integer t returns integer
    local integer i=1
    loop
        exitwhen i>KKP_aba_n
        if KKP_aba_tipo[i]==t then
            return i
        endif
        set i=i+1
    endloop
    return 0
endfunction

function KKP_aba_de_id takes string id returns integer
    local integer i=1
    loop
        exitwhen i>KKP_aba_n
        if KKP_aba_id[i]==id then
            return i
        endif
        set i=i+1
    endloop
    return 0
endfunction

function KKP_campo takes string s,integer n returns string
    local integer i=0
    local integer ini=0
    local integer k=0
    local integer len=StringLength(s)
    loop
        exitwhen i>len
        if i==len or SubString(s, i, i+1)=="|" then
            if k==n then
                return SubString(s, ini, i)
            endif
            set k=k+1
            set ini=i+1
        endif
        set i=i+1
    endloop
    return ""
endfunction

function KKP_pede takes integer aba returns nothing
    if aba>0 then
        call BlzSendSyncData("kkp", "O"+I2S(aba))
    endif
endfunction

function KKP_pede_id takes string id returns nothing
    call KKP_pede(KKP_aba_de_id(id))
endfunction

function KKP_amostra_aba takes integer pid returns nothing
    local integer t=KKP_aba_tipo[KKP_aba[pid]]
    call KKP_amostra(pid)
    if t==4 then
        call KKP_amostra_grade(pid)
    endif
endfunction

function KKP_pode takes integer pid returns boolean
    if not KKP_pronto or KKU_rc_fase!=0 or not KKU_pid_ok(pid) then
        return false
    endif
    return KKU_na_pilha(pid, KKP_raiz)>=0 or KKU_npilha[pid]<KKU_PILHA
endfunction

function KKP_vai takes player p,integer aba returns nothing
    local integer pid=GetPlayerId(p)
    if aba<1 or aba>KKP_aba_n then
        return
    endif
    set KKP_aberto[pid]=true
    set KKP_aba[pid]=aba
    call KKP_amostra_aba(pid)
    if GetLocalPlayer()==p then
        set KKP_pv_espera=false
    endif
    call KKU_janela_abre(pid, KKP_raiz)
endfunction

function KKP_fecha takes integer pid returns nothing
    set KKP_aberto[pid]=false
    call KKU_janela_fecha(pid, KKP_raiz)
endfunction

function KKP_abre takes player p,integer aba returns nothing
    local integer pid=GetPlayerId(p)
    if pid<0 or pid>=KKP_jogadores or aba<1 or aba>KKP_aba_n then
        return
    endif
    if not KKP_pronto then
        call DisplayTextToPlayer(p, 0, 0, "|cffffcc00The "+KKP_titulo+" opens a moment after the game starts.|r")
        return
    endif
    if KKP_aberto[pid] and KKP_aba[pid]==aba then
        call KKP_fecha(pid)
    elseif KKP_pode(pid) then
        call KKP_vai(p, aba)
        if GetLocalPlayer()==p then
            call KKP_desenha(true)
        endif
    endif
endfunction

function KKP_mostra_em takes player p,integer aba,integer sub returns nothing
    local integer pid=GetPlayerId(p)
    if pid<0 or pid>=KKP_jogadores or aba<1 or aba>KKP_aba_n then
        return
    endif
    if not KKP_pronto then
        call DisplayTextToPlayer(p, 0, 0, "|cffffcc00The "+KKP_titulo+" opens a moment after the game starts.|r")
        return
    endif
    if not KKP_pode(pid) then
        return
    endif
    set KKP_ped_aba[pid]=aba
    set KKP_ped_sub[pid]=sub
    call KKP_vai(p, aba)
    if GetLocalPlayer()==p then
        set KKP_g_quer=sub
        set KKP_des_pend=true
    endif
endfunction

function KKP_mostra takes player p,integer aba returns nothing
    call KKP_mostra_em(p, aba, 0)
endfunction

function KKP_abre_em takes integer pid,string id,integer sub returns nothing
    if pid>=0 and pid<KKP_jogadores then
        call KKP_mostra_em(Player(pid), KKP_aba_de_id(id), sub)
    endif
endfunction

function KKP_abre_em_alterna takes integer pid,string id,integer sub returns nothing
    local integer aba=KKP_aba_de_id(id)
    if pid<0 or pid>=KKP_jogadores or aba<1 then
        return
    endif
    if KKP_aberto[pid] and KKP_aba[pid]==aba and KKP_ped_aba[pid]==aba and KKP_ped_sub[pid]==sub then
        call KKP_fecha(pid)
    else
        call KKP_mostra_em(Player(pid), aba, sub)
    endif
endfunction

function KKP_pede_em takes string id,integer sub returns nothing
    local integer aba=KKP_aba_de_id(id)
    if aba>0 and sub>0 then
        call BlzSendSyncData("kkp", "O"+I2S(aba)+"|"+I2S(sub))
    endif
endfunction

function KKP_avisa takes integer pid,string s returns nothing
    if pid<0 or pid>=KKP_jogadores or s==null or s=="" then
        return
    endif
    call DisplayTimedTextToPlayer(Player(pid), 0.0, 0.0, KKP_AVISO_S, s)
    if GetLocalPlayer()==Player(pid) then
        set KKP_av_s=s
        set KKP_av_novo=true
    endif
endfunction

function KKP_mostra_id takes player p,string id returns nothing
    call KKP_mostra(p, KKP_aba_de_id(id))
endfunction
//{{KK_SE:KK_PAINEL_EXTRA}}

function KKP_mostra_item takes player p,integer x returns nothing
    local integer pid=GetPlayerId(p)
    local integer k=KKP_idx(x)
    local integer aba=KKP_aba_do_tipo(2)
    if pid<0 or pid>=KKP_jogadores or k<1 or aba<1 then
        return
    endif
    if not KKP_pronto then
        call DisplayTextToPlayer(p, 0, 0, "|cffffcc00The "+KKP_titulo+" opens a moment after the game starts.|r")
        return
    endif
    if not KKP_pode(pid) then
        return
    endif
    set KKP_ped_aba[pid]=0
    call KKP_vai(p, aba)
    if GetLocalPlayer()==p then
        set KKP_x_qi=k
        set KKP_x_qc=0
        set KKP_des_pend=true
    endif
endfunction

function KKP_mostra_chefe takes player p,integer u returns nothing
    local integer pid=GetPlayerId(p)
    local integer aba=KKP_aba_do_tipo(3)
    local integer j=1
    if pid<0 or pid>=KKP_jogadores or u==0 or aba<1 then
        return
    endif
    loop
        exitwhen j>KKP_bs_n or KKP_bs_unid[j]==u
        set j=j+1
    endloop
    if j>KKP_bs_n then
        return
    endif
    if not KKP_pronto then
        call DisplayTextToPlayer(p, 0, 0, "|cffffcc00The "+KKP_titulo+" opens a moment after the game starts.|r")
        return
    endif
    if not KKP_pode(pid) then
        return
    endif
    set KKP_ped_aba[pid]=0
    call KKP_vai(p, aba)
    if GetLocalPlayer()==p then
        set KKP_x_qc=j
        set KKP_x_qi=0
        set KKP_des_pend=true
    endif
endfunction
//{{KK_FIMSE:KK_PAINEL_EXTRA}}
//{{KK_SE:KK_PAINEL_CHEFE_BT}}

function KKP_mostra_entrada takes player p,integer aba,integer sub,integer i returns nothing
    local integer pid=GetPlayerId(p)
    if pid<0 or pid>=KKP_jogadores or aba<1 or aba>KKP_aba_n then
        return
    endif
    call KKP_mostra_em(p, aba, sub)
    if KKP_aba_tipo[aba]!=4 or sub<1 or sub>KKP_ab_subn[aba] or not KKP_aberto[pid] or KKP_aba[pid]!=aba then
        return
    endif
    if GetLocalPlayer()==p then
        set KKP_g_quer_i=i
    endif
endfunction

function KKP_abre_entrada takes integer pid,string id,integer sub,integer i returns nothing
    if pid>=0 and pid<KKP_jogadores then
        call KKP_mostra_entrada(Player(pid), KKP_aba_de_id(id), sub, i)
    endif
endfunction
//{{KK_FIMSE:KK_PAINEL_CHEFE_BT}}

function KKP_ao_menu takes nothing returns boolean
    local integer pid=KKU_c_pid
    if pid>=0 and pid<KKP_jogadores then
        call KKP_abre(Player(pid), KKP_aba[pid])
    endif
    return false
endfunction

function KKP_ao_fecha takes nothing returns boolean
    local integer pid=KKU_c_pid
    if KKU_c_jan==KKP_raiz and pid>=0 and pid<KKP_jogadores then
        set KKP_aberto[pid]=false
    endif
    return false
endfunction

function KKP_clique_local takes integer g,integer i returns nothing
    local integer pid=GetPlayerId(GetLocalPlayer())
    local integer x
    local integer j
    if g==3 then
        set KKP_c_cat=i
        set KKP_c_top=0
        call KKP_limpa_busca()
        call KKP_des_codex_lista()
    elseif g==4 then
        set x=KKP_c_lin[i]
        if x!=0 then
            set KKP_c_sel=x
            set KKP_c_utop=0
            set KKP_c_pend=true
            call KKP_des_codex_lista()
        endif
    elseif g==5 then
        if i==1 then
            set KKP_c_top=KKP_c_top-11
        else
            set KKP_c_top=KKP_c_top+11
        endif
        call KKP_des_codex_lista()
    elseif g==6 then
        if i==3 and KKP_c_sel>0 then
            call BlzSendSyncData("kkp", "F"+KKP_id2s(KKP_it[KKP_c_sel]))
//{{KK_SE:KK_PAINEL_EXTRA}}
        elseif i==8 and KKP_c_sel>0 then
            call BlzSendSyncData("kkp", "W"+KKP_id2s(KKP_it[KKP_c_sel]))
//{{KK_FIMSE:KK_PAINEL_EXTRA}}
//{{KK_SE:KK_PAINEL_CRAFT}}
        elseif i==7 and KKP_c_sel>0 then
            call BlzSendSyncData("kkp", "C"+KKP_id2s(KKP_it[KKP_c_sel]))
//{{KK_FIMSE:KK_PAINEL_CRAFT}}
        elseif i==4 then
            set KKP_c_utop=KKP_c_utop-6
            set KKP_c_pend=true
        elseif i==5 then
            set KKP_c_utop=KKP_c_utop+6
            set KKP_c_pend=true
        elseif i==6 then
            call KKP_limpa_busca()
            call KKP_des_codex_lista()
        endif
    elseif g==7 then
        if i<=KKP_c_rec_n and KKP_idx(KKP_c_rec[i])>0 then
            call KKP_abre_item(KKP_idx(KKP_c_rec[i]))
            call KKP_des_codex_lista()
        endif
    elseif g==8 then
        if KKP_c_sel>0 and KKP_c_utop+i<=KKP_it_usn[KKP_c_sel] then
            call KKP_abre_item(KKP_us[KKP_it_us[KKP_c_sel]+KKP_c_utop+i-1])
            call KKP_des_codex_lista()
        endif
    elseif g==9 then
        set KKP_b_grupo=i
        set KKP_b_top=0
        call KKP_des_chefe_lista()
    elseif g==10 then
        set j=KKP_b_lin[i]
        if j!=0 then
            set KKP_b_sel=j
            set KKP_b_pend=true
            call KKP_des_chefe_lista()
        endif
    elseif g==11 then
        if i==1 then
            set KKP_b_top=KKP_b_top-11
        else
            set KKP_b_top=KKP_b_top+11
        endif
        call KKP_des_chefe_lista()
    elseif g==13 then
        if i==1 and KKP_b_sel>0 and KKP_bs_pos[KKP_b_sel] then
            call PingMinimap(KKP_bs_x[KKP_b_sel], KKP_bs_y[KKP_b_sel], 4.00)
        endif
//{{KK_SE:KK_PAINEL_CHEFE_BT}}
        if i==2 and KKP_b_sel>0 and KKP_b_sel<=KKP_bs_n then
            call BlzSendSyncData("kkp", "B"+KKP_id2s(KKP_bs_unid[KKP_b_sel]))
        endif
//{{KK_FIMSE:KK_PAINEL_CHEFE_BT}}
//{{KK_SE:KK_PAINEL_DROPS}}
        if i==3 then
            set KKP_b_dtop=KKP_b_dtop-10
            set KKP_b_pend=true
        elseif i==4 then
            set KKP_b_dtop=KKP_b_dtop+10
            set KKP_b_pend=true
        endif
//{{KK_FIMSE:KK_PAINEL_DROPS}}
    elseif g==14 or g==20 then
        if KKP_g_lin[i]>=0 then
            set KKP_g_sel=KKP_g_lin[i]
            call KKP_des_mapa()
        endif
    elseif g==15 or g==21 then
        if g==15 then
            set j=40
        else
            set j=KKP_GL
        endif
        if i==1 then
            set KKP_g_top=KKP_g_top-j
        else
            set KKP_g_top=KKP_g_top+j
        endif
        call KKP_des_mapa()
    elseif g==16 then
        set KKP_g_sub=i
        set KKP_g_top=0
        set KKP_g_sel=-1
        call KKP_des_mapa()
    elseif g==17 then
        call BlzSendSyncData("kkp", "G"+I2S(KKP_aba[pid])+"|"+I2S(KKP_g_sub)+"|"+I2S(KKP_g_sel)+"|"+I2S(i))
    elseif g==18 then
        if i>=1 and i<=10 then
            set KKP_g_sub=i
            set KKP_g_top=0
            set KKP_g_sel=-1
            call KKP_des_mapa()
        elseif i>100 and i<=100+KKP_KL then
            if KKP_g_lin[i-100]>=0 then
                set KKP_g_sel=KKP_g_lin[i-100]
                call KKP_des_mapa()
            endif
        elseif i==151 then
            set KKP_g_top=KKP_g_top-KKP_KL
            call KKP_des_mapa()
        elseif i==152 then
            set KKP_g_top=KKP_g_top+KKP_KL
            call KKP_des_mapa()
        elseif i==161 or i==162 then
            call BlzSendSyncData("kkp", "G"+I2S(KKP_aba[pid])+"|"+I2S(KKP_g_sub)+"|"+I2S(KKP_g_sel)+"|"+I2S(i-160))
        endif
    endif
endfunction

function KKP_ao_clique takes nothing returns boolean
    local integer pid=KKU_c_pid
    local integer c=KKU_c_cod
    local integer alvo=KKU_c_alvo
    local integer g=c/1000
    local integer i=c-g*1000
    local integer x
    local player p
    if pid<0 or pid>=KKP_jogadores or c<=0 or not KKP_pronto or KKU_rc_fase!=0 then
        return false
    endif
    if not KKP_meu(c, alvo) then
        return false
    endif
    if not KKP_aberto[pid] then
        return false
    endif
    set p=Player(pid)
    if g==1 or g==12 or g==16 or (g==18 and i>=1 and i<=10) then
        set KKP_ped_aba[pid]=0
    endif
    if GetLocalPlayer()==p then
        call KKP_solta_busca()
    endif
    if g==1 then
        if KKP_pode(pid) then
            call KKP_vai(p, i)
            if GetLocalPlayer()==p then
                call KKP_desenha(true)
            endif
        endif
    elseif g==2 then
        call KKP_fecha(pid)
    elseif g==12 then
        set x=KKP_aba_do_tipo(2)
        if x>0 and KKP_pode(pid) then
            call KKP_vai(p, x)
            if GetLocalPlayer()==p then
                call KKP_abre_item(KKP_idx(KKP_b_drop[i]))
                call KKP_desenha(true)
            endif
        endif
    elseif g==19 then
        if GetLocalPlayer()==p then
            if KKU_pv_bloqueada then
                call KKU_previa_desbloqueia()
                call KKU_previa_liga(true)
            elseif KKP_pv_espera then
                call KKU_previa_liga(true)
            else
                call KKU_previa_liga(not KKU_pv_ligada)
            endif
            set KKP_pv_espera=false
            call KKP_desenha(false)
        endif
//{{KK_SE:KK_PAINEL_EXTRA}}
    elseif c==6009 then
        call KKP_mostra_item(p, KKP_f_link[pid])
//{{KK_FIMSE:KK_PAINEL_EXTRA}}
    elseif GetLocalPlayer()==p then
        call KKP_clique_local(g, i)
        call KKU_aplica()
    endif
    set p=null
    return false
endfunction

function KKP_ao_roda takes nothing returns boolean
    local integer pid=KKU_c_pid
    local integer c=KKU_c_cod
    local real v=KKU_c_valor
    local integer id=KKU_c_id
    local integer alvo=KKU_c_alvo
    local integer g=c/1000
    local integer d=-1
    local integer t
    if v<0.0 then
        set d=1
    endif
    if c==0 then
        if id!=KKP_fundo then
            return false
        endif
    elseif not KKP_meu(c, alvo) then
        return false
    endif
    if pid>=0 and pid<KKP_jogadores and KKP_pronto and KKU_rc_fase==0 then
        if GetLocalPlayer()==Player(pid) and KKP_aberto[pid] then
            set t=KKP_aba_tipo[KKP_aba[pid]]
            if c==0 then
                set alvo=KKU_sob_mouse()
                if alvo>0 then
                    if KKP_meu(KKU_alvo_cod[alvo], alvo) then
                        set g=KKU_alvo_cod[alvo]/1000
                    endif
                endif
            endif
            if g==8 then
                set KKP_c_utop=KKP_c_utop+d
                set KKP_c_pend=true
            elseif t==2 then
                set KKP_c_top=KKP_c_top+d
                call KKP_des_codex_lista()
            elseif t==3 then
                set KKP_b_top=KKP_b_top+d
                call KKP_des_chefe_lista()
            elseif t==4 then
                if KKP_ab_lay[KKP_aba[pid]*16+KKP_g_sub]>=2 then
                    set KKP_g_top=KKP_g_top+d
                else
                    set KKP_g_top=KKP_g_top+d*40
                endif
                call KKP_des_mapa()
            endif
            call KKU_aplica()
        endif
    endif
    return false
endfunction

function KKP_ao_texto takes nothing returns boolean
    local integer pid=KKU_c_pid
    local integer id=KKU_c_id
    local string q=KKU_c_txt
    local boolean enter=KKU_c_valor>0.5
    if id!=KKP_c_busca or pid<0 or pid>=KKP_jogadores or not KKP_pronto or KKU_rc_fase!=0 then
        return false
    endif
    if GetLocalPlayer()==Player(pid) then
        if enter then
            call KKP_solta_busca()
        endif
        if q==null then
            set q=""
        endif
        set q=StringCase(q, false)
        if KKP_c_eco then
            if q=="" then
                set KKP_c_eco=false
            endif
            set q=KKP_c_q
        elseif q!="" and q==KKP_c_ign then
            set q=KKP_c_q
        elseif q!=KKP_c_q then
            set KKP_c_ign=""
        endif
        if q!=KKP_c_q then
            if not enter then
                set KKP_c_foco=true
            endif
            set KKP_c_q=q
            set KKP_c_top=0
            set KKP_res_n=0
            if q!="" then
                set KKP_res_i=1
            else
                set KKP_res_i=0
            endif
            if KKP_aberto[pid] and KKP_aba_tipo[KKP_aba[pid]]==2 then
                if KKP_res_i>0 then
                    call KKU_texto(KKP_c_btxt, "|cff999999Searching...|r")
                else
                    call KKP_des_codex_lista()
                endif
                call KKU_aplica()
            endif
        endif
    endif
    return false
endfunction

//{{KK_SE:KK_PAINEL_CHEFE_BT}}
function KKP_chefe_bb takes integer u returns integer
    local integer j=1
    loop
        exitwhen j>KKP_bs_n
        if KKP_bs_unid[j]==u and KKP_bs_bok[j] then
            return j
        endif
        set j=j+1
    endloop
    return 0
endfunction

//{{KK_FIMSE:KK_PAINEL_CHEFE_BT}}
function KKP_sync takes nothing returns nothing
    local player p=GetTriggerPlayer()
    local string v=BlzGetTriggerSyncData()
    local integer pid=GetPlayerId(p)
    local string c
    if pid<0 or pid>=KKP_jogadores or not KKP_pronto or v==null or StringLength(v)<2 then
        set p=null
        return
    endif
    set c=SubString(v, 0, 1)
    if c=="F" and StringLength(v)==5 then
        call KKP_fav_troca(p, KKP_s2id(SubString(v, 1, 5)))
        if GetLocalPlayer()==p and KKU_rc_fase==0 then
            set KKP_c_pend=true
            if KKP_aberto[pid] and KKP_aba_tipo[KKP_aba[pid]]==2 then
                call KKP_des_codex_lista()
                call KKU_aplica()
            endif
        endif
//{{KK_SE:KK_PAINEL_CRAFT}}
    elseif c=="C" and StringLength(v)==5 then
        set KKP_arg_pid=pid
        set KKP_arg_item=KKP_s2id(SubString(v, 1, 5))
        call KKP_chama(KKP_G_CRAFT)
        if GetLocalPlayer()==p then
            set KKP_c_pend=true
        endif
//{{KK_FIMSE:KK_PAINEL_CRAFT}}
//{{KK_SE:KK_PAINEL_EXTRA}}
    elseif c=="W" and StringLength(v)==5 then
        set KKP_arg_x=KKP_s2id(SubString(v, 1, 5))
        if KKP_b3_rot!="" and KKP_idx(KKP_arg_x)>0 and not KKP_b3_fora[pid] then
            if KKP_it_b3ok[KKP_idx(KKP_arg_x)] then
                set KKP_arg_pid=pid
                call KKP_chama(KKP_G_ITEM)
                if GetLocalPlayer()==p and KKU_rc_fase==0 then
                    set KKP_c_pend=true
                endif
            endif
        endif
//{{KK_FIMSE:KK_PAINEL_EXTRA}}
//{{KK_SE:KK_PAINEL_CHEFE_BT}}
    elseif c=="B" and StringLength(v)==5 then
        if KKP_bb_rot!="" and not KKP_bb_fora[pid] and KKP_aberto[pid] and KKP_aba_tipo[KKP_aba[pid]]==3 and KKP_chefe_bb(KKP_s2id(SubString(v, 1, 5)))>0 then
            set KKP_arg_x=KKP_s2id(SubString(v, 1, 5))
            set KKP_arg_i=KKP_chefe_bb(KKP_arg_x)
            set KKP_arg_pid=pid
            call KKP_chama(KKP_G_CHEFE)
        endif
//{{KK_FIMSE:KK_PAINEL_CHEFE_BT}}
    elseif c=="O" then
        set v=SubString(v, 1, StringLength(v))
        if S2I(KKP_campo(v, 1))>0 then
            call KKP_mostra_em(p, S2I(KKP_campo(v, 0)), S2I(KKP_campo(v, 1)))
        else
            call KKP_abre(p, S2I(KKP_campo(v, 0)))
        endif
    elseif c=="G" then
        set v=SubString(v, 1, StringLength(v))
        set KKP_arg_pid=pid
        set KKP_arg_aba=S2I(KKP_campo(v, 0))
        set KKP_arg_sub=S2I(KKP_campo(v, 1))
        set KKP_arg_i=S2I(KKP_campo(v, 2))
        set KKP_arg_btn=S2I(KKP_campo(v, 3))
        set KKP_arg_ok=false
        if KKP_aberto[pid] and KKP_aba[pid]==KKP_arg_aba and KKP_arg_aba>=1 and KKP_arg_aba<=KKP_aba_n and KKP_aba_tipo[KKP_arg_aba]==4 and KKP_arg_sub>=1 and KKP_arg_sub<=KKP_ab_subn[KKP_arg_aba] and KKP_arg_i>=-1 and KKP_arg_i<KKP_GE and KKP_arg_btn>=1 and KKP_arg_btn<=2 then
            call KKP_chama(KKP_G_APLICA)
            if KKP_aberto[pid] and KKP_aba[pid]==KKP_arg_aba then
                call KKP_amostra_grade(pid)
                if GetLocalPlayer()==p and KKU_rc_fase==0 then
                    call KKP_des_mapa()
                    call KKU_aplica()
                endif
            endif
        endif
    endif
    set p=null
endfunction

//{{KK_SE:KK_PAINEL_EXTRA}}
function KKP_local_item takes nothing returns integer
    local integer pid=GetPlayerId(GetLocalPlayer())
    if not KKP_pronto or pid<0 or pid>=KKP_jogadores then
        return 0
    endif
    if not KKP_aberto[pid] or KKP_aba_tipo[KKP_aba[pid]]!=2 or KKP_c_sel<1 or KKP_c_sel>KKP_it_n then
        return 0
    endif
    return KKP_it[KKP_c_sel]
endfunction

function KKP_local_chefe takes nothing returns integer
    local integer pid=GetPlayerId(GetLocalPlayer())
    if not KKP_pronto or pid<0 or pid>=KKP_jogadores then
        return 0
    endif
    if not KKP_aberto[pid] or KKP_aba_tipo[KKP_aba[pid]]!=3 or KKP_b_sel<1 or KKP_b_sel>KKP_bs_n then
        return 0
    endif
    return KKP_bs_unid[KKP_b_sel]
endfunction

function KKP_local_drop takes integer s returns integer
    local integer j=KKP_b_sel
//{{KK_FIMSE:KK_PAINEL_EXTRA}}
//{{KK_SE:KK_PAINEL_DROPS}}
    if s>12 and s<=KKP_DR_TETO and KKP_local_chefe()!=0 and s<=KKP_bs_drn[j] then
        return KKP_dr_it[KKP_bs_dr[j]+s-1]
    endif
//{{KK_FIMSE:KK_PAINEL_DROPS}}
//{{KK_SE:KK_PAINEL_EXTRA}}
    if KKP_local_chefe()==0 or s<1 or s>12 or s>KKP_bs_drn[j] then
        return 0
    endif
    return KKP_dr_it[KKP_bs_dr[j]+s-1]
endfunction

function KKP_det_mapa takes integer qual,string s returns nothing
    local integer k
//{{KK_FIMSE:KK_PAINEL_EXTRA}}
//{{KK_SE:KK_PAINEL_DROPS}}
    if qual>14 and qual<=2+KKP_DR_TETO then
        set k=KKP_local_chefe()
        if s==null then
            set s=""
        endif
        if KKP_dm_k[qual]==k and KKP_dm_s[qual]==s then
            return
        endif
        set KKP_dm_k[qual]=k
        set KKP_dm_s[qual]=s
        if k!=0 then
            set KKP_b_pend=true
        endif
        return
    endif
//{{KK_FIMSE:KK_PAINEL_DROPS}}
//{{KK_SE:KK_PAINEL_EXTRA}}
    if qual<1 or qual>14 then
        return
    endif
    if qual==1 then
        set k=KKP_local_item()
    else
        set k=KKP_local_chefe()
    endif
    if s==null then
        set s=""
    endif
    if KKP_dm_k[qual]==k and KKP_dm_s[qual]==s then
        return
    endif
    set KKP_dm_k[qual]=k
    set KKP_dm_s[qual]=s
    if k!=0 then
        if qual==1 then
            set KKP_c_pend=true
        else
            set KKP_b_pend=true
        endif
    endif
endfunction

function KKP_tique1_um takes nothing returns nothing
    local integer pid=KKP_t1_pid
    if not KKP_fav_ok[pid] and GetPlayerSlotState(Player(pid))==PLAYER_SLOT_STATE_PLAYING then
        call KKP_fav_le(pid)
    endif
    if KKP_aberto[pid] then
        call KKP_amostra(pid)
        if KKP_aba_tipo[KKP_aba[pid]]==4 then
            call KKP_amostra_grade(pid)
        endif
    endif
endfunction

function KKP_tique1_fios takes nothing returns nothing
    local integer pid=0
    local integer t
    loop
        exitwhen pid>=KKP_jogadores
        if KKP_aberto[pid] or (not KKP_fav_ok[pid] and GetPlayerSlotState(Player(pid))==PLAYER_SLOT_STATE_PLAYING) then
            set KKP_t1_pid=pid
            call ExecuteFunc("KKP_tique1_um")
        endif
        set pid=pid+1
    endloop
    set pid=GetPlayerId(GetLocalPlayer())
    if pid>=0 and pid<KKP_jogadores and KKP_aberto[pid] and KKU_rc_fase==0 then
        set t=KKP_aba_tipo[KKP_aba[pid]]
        if t==1 then
            call KKP_des_ficha(pid)
            call KKU_aplica()
        elseif t==4 and KKP_g_aba==KKP_aba[pid] then
            call KKP_des_mapa()
            call KKU_aplica()
        endif
    endif
endfunction

//{{KK_FIMSE:KK_PAINEL_EXTRA}}
function KKP_tique1 takes nothing returns nothing
    local integer pid=0
    local integer t
    if not KKP_pronto then
        return
    endif
//{{KK_SE:KK_PAINEL_EXTRA}}
    call KKP_tique1_fios()
    return
//{{KK_FIMSE:KK_PAINEL_EXTRA}}
    loop
        exitwhen pid>=KKP_jogadores
        if not KKP_fav_ok[pid] and GetPlayerSlotState(Player(pid))==PLAYER_SLOT_STATE_PLAYING then
            call KKP_fav_le(pid)
        endif
        if KKP_aberto[pid] then
            call KKP_amostra(pid)
            if KKP_aba_tipo[KKP_aba[pid]]==4 then
                call KKP_amostra_grade(pid)
            endif
        endif
        set pid=pid+1
    endloop
    set pid=GetPlayerId(GetLocalPlayer())
    if pid>=0 and pid<KKP_jogadores and KKP_aberto[pid] and KKU_rc_fase==0 then
        set t=KKP_aba_tipo[KKP_aba[pid]]
        if t==1 then
            call KKP_des_ficha(pid)
            call KKU_aplica()
        elseif t==4 and KKP_g_aba==KKP_aba[pid] then
            call KKP_des_mapa()
            call KKU_aplica()
        endif
    endif
endfunction

function KKP_tique_local takes nothing returns nothing
    local integer pid
    local integer i
    local integer fim
    if not KKP_pronto or KKU_rc_fase!=0 then
        return
    endif
    set pid=GetPlayerId(GetLocalPlayer())
    if pid<0 or pid>=KKP_jogadores then
        return
    endif
    if KKP_c_eco then
        set KKP_c_eco_t=KKP_c_eco_t-1
        if KKP_c_eco_t<=0 then
            set KKP_c_eco=false
        endif
    endif
//{{KK_SE:KK_PAINEL_EXTRA}}
    if KKP_x_qi>0 then
        call KKP_abre_item(KKP_x_qi)
        set KKP_x_qi=0
    elseif KKP_x_qc>0 then
        set KKP_b_grupo=KKP_bs_grupo[KKP_x_qc]
        set KKP_b_top=KKP_x_qc-KKP_gr_ini[KKP_b_grupo]-5
        set KKP_b_sel=KKP_x_qc
        set KKP_b_pend=true
        set KKP_x_qc=0
    endif
//{{KK_FIMSE:KK_PAINEL_EXTRA}}
    if KKP_des_pend then
        set KKP_des_pend=false
        call KKP_desenha(true)
    endif
    if KKP_av_novo then
        set KKP_av_novo=false
        if KKP_aberto[pid] then
            set KKP_av_t=KKP_AVISO_TIQUES
            call KKU_texto(KKP_f_aviso, KKP_av_s)
            call KKP_vis(KKP_f_aviso, true)
            call KKU_aplica()
        endif
    elseif KKP_av_t>0 then
        set KKP_av_t=KKP_av_t-1
        if KKP_av_t==0 then
            call KKP_vis(KKP_f_aviso, false)
            call KKU_aplica()
        endif
    endif
    if KKP_st_pend then
        call KKP_setas_aplica()
        call KKU_aplica()
    endif
    if KKP_res_i>0 then
        set i=KKP_res_i
        set fim=IMinBJ(KKP_it_n, i+149)
        loop
            exitwhen i>fim
            if KKP_contem(KKP_it_busca[i], KKP_c_q) then
                set KKP_res_n=KKP_res_n+1
                set KKP_res[KKP_res_n]=i
            endif
            set i=i+1
        endloop
        if i>KKP_it_n then
            set KKP_res_i=0
        else
            set KKP_res_i=i
        endif
        if KKP_res_i==0 and KKP_aberto[pid] and KKP_aba_tipo[KKP_aba[pid]]==2 then
            call KKP_des_codex_lista()
            call KKU_aplica()
        endif
        return
    endif
    if not KKP_aberto[pid] then
        return
    endif
    if KKP_c_pend and KKP_aba_tipo[KKP_aba[pid]]==2 then
        set KKP_c_pend=false
        call KKP_des_codex_det()
        call KKU_aplica()
    elseif KKP_b_pend and KKP_aba_tipo[KKP_aba[pid]]==3 then
        set KKP_b_pend=false
        call KKP_des_chefe_det()
        call KKU_aplica()
    endif
endfunction

function KKP_ao_carga takes nothing returns boolean
    local integer pid=0
    local integer k=1
    local integer t
    if not KKP_pronto then
        return false
    endif
    set KKP_c_cat=1
    set KKP_c_top=0
    set KKP_c_sel=0
    set KKP_c_utop=0
    set KKP_c_q=""
    set KKP_res_n=0
    set KKP_res_i=0
    set KKP_c_pend=false
    set KKP_b_grupo=1
    set KKP_b_top=0
    set KKP_b_sel=0
    set KKP_b_pend=false
    set KKP_g_aba=0
    set KKP_g_sub=1
    set KKP_g_top=0
    set KKP_g_sel=-1
    set KKP_c_eco=false
    set KKP_c_eco_t=0
    set KKP_c_ign=""
    set KKP_c_rec_n=0
    set KKP_g_quer=0
    set KKP_av_t=0
    set KKP_av_novo=false
    set KKP_des_pend=false
    set KKP_c_foco=false
//{{KK_SE:KK_PAINEL_EXTRA}}
    set KKP_x_qi=0
    set KKP_x_qc=0
//{{KK_FIMSE:KK_PAINEL_EXTRA}}
//{{KK_SE:KK_PAINEL_CHEFE_BT}}
    set KKP_g_quer_i=-1
//{{KK_FIMSE:KK_PAINEL_CHEFE_BT}}
//{{KK_SE:KK_PAINEL_DROPS}}
    set KKP_st_cod[11]=0
    set KKP_st_cod[12]=0
    set KKP_b_dtop=0
    set KKP_b_dsel=0
//{{KK_FIMSE:KK_PAINEL_DROPS}}
    set KKP_st_pend=false
    loop
        exitwhen k>10
        set KKP_st_cod[k]=0
        set k=k+1
    endloop
    set k=1
    set KKP_pv_espera=true
    loop
        exitwhen pid>=KKP_jogadores
        set KKP_aberto[pid]=KKU_na_pilha(pid, KKP_raiz)>=0
        set KKP_ped_aba[pid]=0
        if KKP_aberto[pid] then
            call KKP_amostra_aba(pid)
        endif
        set pid=pid+1
    endloop
    set pid=GetPlayerId(GetLocalPlayer())
    if pid>=0 and pid<KKP_jogadores then
        set t=KKP_aba_tipo[KKP_aba[pid]]
        loop
            exitwhen k>4
            call KKP_vis(KKP_pag[k], k==t)
            set k=k+1
        endloop
        call KKP_vis(KKP_f_aviso, false)
        call KKP_desenha(true)
        call KKU_aplica()
    endif
    return false
endfunction

function KKP_cria_base takes nothing returns nothing
    local integer i=1
    local integer n=0
    local real x=0.100
    local real w
    set KKP_raiz=KKP_pag_nova(0)
    call KKU_nivel(KKP_raiz, KKU_painel_nivel)
    call KKU_janela_cobre(KKP_raiz, KKU_painel_x, KKU_painel_y, KKU_painel_w, KKU_painel_h)
    set KKP_caixa=KKU_caixa(KKP_raiz, KKU_P_MOLDURA, KKU_painel_x, KKU_painel_y, KKU_painel_w, KKU_painel_h)
    set KKP_fundo=KKU_fundo(KKP_raiz, KKU_painel_x, KKU_painel_y, KKU_painel_w, KKU_painel_h, true)
    if KKU_tema_tex[KKU_P_FAIXA_TOPO]!=KKP_TEX_VAZIO then
        call KKU_img(KKP_raiz, KKU_P_FAIXA_TOPO, KKU_painel_x, KKU_painel_y, KKU_painel_w, 0.036)
    endif
    if KKU_tema_tex[KKU_P_CANTO_TL]!=KKP_TEX_VAZIO then
        call KKU_img(KKP_raiz, KKU_P_CANTO_TL, KKU_painel_x, KKU_painel_y, 0.02, 0.02)
    endif
    if KKU_tema_tex[KKU_P_CANTO_TR]!=KKP_TEX_VAZIO then
        call KKU_img(KKP_raiz, KKU_P_CANTO_TR, KKU_painel_x+KKU_painel_w-0.02, KKU_painel_y, 0.02, 0.02)
    endif
    if KKU_tema_tex[KKU_P_CANTO_BL]!=KKP_TEX_VAZIO then
        call KKU_img(KKP_raiz, KKU_P_CANTO_BL, KKU_painel_x, KKU_painel_y-KKU_painel_h+0.02, 0.02, 0.02)
    endif
    if KKU_tema_tex[KKU_P_CANTO_BR]!=KKP_TEX_VAZIO then
        call KKU_img(KKP_raiz, KKU_P_CANTO_BR, KKU_painel_x+KKU_painel_w-0.02, KKU_painel_y-KKU_painel_h+0.02, 0.02, 0.02)
    endif
    set KKP_aba_tex=(KKU_tema_fdf[KKU_P_ABA]==null or KKU_tema_fdf[KKU_P_ABA]=="") and (KKU_tema_fdf[KKU_P_ABA_ATIVA]==null or KKU_tema_fdf[KKU_P_ABA_ATIVA]=="")
    loop
        exitwhen i>KKP_aba_n
        set n=n+IMaxBJ(StringLength(KKP_aba_nome[i]), 4)
        set i=i+1
    endloop
    set i=1
    loop
        exitwhen i>KKP_aba_n
        set w=(0.635-0.004*I2R(KKP_aba_n))*I2R(IMaxBJ(StringLength(KKP_aba_nome[i]), 4))/I2R(IMaxBJ(n, 1))
        call KKP_bpapel(KKP_raiz, KKU_P_ABA, KKP_aba_nome[i], x, 0.556, w, 0.028, 1000+i)
        set x=x+w+0.004
        set i=i+1
    endloop
    call KKP_bpapel(KKP_raiz, KKU_P_FECHAR, KKU_ROT_FECHAR, 0.742, 0.556, 0.030, 0.028, 2001)
    set KKP_f_titulo=KKP_txt(KKP_raiz, KKU_F_PEQUENA, 0.100, 0.573, 0.300, 0.014)
    call KKU_texto(KKP_f_titulo, KKP_titulo+"  ["+KKU_TECLA_NOME+"]")
    set KKP_f_aviso=KKP_txt(KKP_raiz, KKU_F_PEQUENA, 0.405, 0.573, 0.330, 0.014)
    call KKU_alinha(KKP_f_aviso, KKU_AL_MEIO_DIR)
    call KKU_esconde(KKP_f_aviso)
    call KKU_menu_botao()
    set i=1
    loop
        exitwhen i>4
        set KKP_pag[i]=KKP_pag_nova(KKP_raiz)
        call KKU_esconde(KKP_pag[i])
        set i=i+1
    endloop
    call KKU_esconde(KKP_raiz)
endfunction

function KKP_pv_caixa takes integer pg,real x,real y returns integer
    local real s=KKP_gs(0.016)
    local integer c=KKU_casa(pg, KKP_gx(x), KKP_gy(y), s, KKP_COD_PV)
    local integer r
    set KKP_pv_rot_ult=0
    set KKP_pv_al_ult=0
    set KKP_pv_alb_ult=0
    if c<=0 or c>=KKU_MAX then
        return 0
    endif
    set KKP_pv_al_ult=KKU_ult_alvo
    call KKP_registra(KKP_COD_PV, KKP_pv_al_ult)
    set KKP_pv_alb_ult=KKU_alvo(c, c, KKP_COD_PV_B, false)
    call KKP_registra(KKP_COD_PV_B, KKP_pv_alb_ult)
    call KKU_alvo_vis(KKP_pv_alb_ult, false)
    call KKU_esconde(c+1)
    call KKU_poe(c+4, KKU_x[c]+s*0.125, KKU_y[c]-s*0.125, s*0.75, s*0.75)
    set r=KKP_txt(pg, KKU_F_PEQUENA, x+0.020, y, 0.100, 0.016)
    call KKU_alinha(r, KKU_AL_MEIO_ESQ)
    call KKU_texto(r, KKP_PV_ROTULO)
    set KKP_pv_rot_ult=r
    call KKU_dica_acima(KKP_COD_PV, KKP_gx(KKP_PV_TX0), KKP_gx(KKP_PV_TX1))
    call KKU_dica_acima(KKP_COD_PV_B, KKP_gx(KKP_PV_TX0), KKP_gx(KKP_PV_TX1))
    call KKU_dica(KKP_COD_PV, KKP_PV_DICA)
    call KKU_dica(KKP_COD_PV_B, KKP_PV_DICA_BLOQ)
    return c
endfunction

function KKP_cria_ficha takes nothing returns nothing
    local integer pg=KKP_pag[1]
    call KKP_caixa_nova(pg, false, 0.100, 0.522, 0.220, 0.357)
    call KKP_caixa_nova(pg, false, 0.325, 0.522, 0.445, 0.357)
    set KKP_f_ico=KKP_quad(pg, KKU_P_ICONE_PADRAO, 0.110, 0.512, 0.042)
    set KKP_f_nome=KKP_txt(pg, KKU_F_NORMAL, 0.158, 0.512, 0.156, 0.042)
    set KKP_f_stat=KKP_txt(pg, KKU_F_PEQUENA, 0.110, 0.462, 0.204, 0.292)
//{{KK_SE:KK_PAINEL_EXTRA}}
    if KKP_com_link then
        set KKP_f_lico=KKP_quad(pg, KKU_P_ICONE_PADRAO, 0.110, 0.205, 0.030)
        set KKP_f_ltxt=KKP_txt(pg, KKU_F_PEQUENA, 0.146, 0.205, 0.168, 0.030)
        call KKU_alinha(KKP_f_ltxt, KKU_AL_MEIO_ESQ)
        set KKP_f_lbt=KKP_bt(pg, KKP_f_lico, 6009, false)
        call KKU_esconde(KKP_f_lico)
        call KKU_esconde(KKP_f_ltxt)
        call KKU_alvo_vis(KKP_f_lbt, false)
    endif
//{{KK_FIMSE:KK_PAINEL_EXTRA}}
    if KKU_PV_N<=0 then
        set KKP_f_mapa=KKU_area(pg, KKP_gx(0.330), KKP_gy(0.516), KKP_gw(0.435), KKP_gh(0.345))
        return
    endif
    set KKP_f_mapa=KKU_area(pg, KKP_gx(0.330), KKP_gy(0.516), KKP_gw(0.290), KKP_gh(0.345))
    set KKP_pv_ficha=KKU_sprite(pg)
    call KKU_esconde(KKP_pv_ficha)
    set KKP_pv_cx_ficha=KKP_pv_caixa(pg, 0.632, 0.200)
    set KKP_pv_rot_ficha=KKP_pv_rot_ult
    set KKP_pv_al_ficha=KKP_pv_al_ult
    set KKP_pv_alb_ficha=KKP_pv_alb_ult
endfunction

function KKP_cria_codex takes nothing returns nothing
    local integer pg=KKP_pag[2]
    local integer k=0
    local integer s=1
    local real x
    loop
        exitwhen k>KKP_cat_n
        call KKP_linha(pg, 0.100, 0.522-k*0.0262, 0.085, 0.025, 3000+k, false, false)
        set k=k+1
    endloop
    set KKP_c_busca=KKU_campo(pg, KKP_gx(0.190), KKP_gy(0.525), KKP_gw(0.172), KKP_gh(0.030), 30)
    call KKP_bpapel(pg, KKU_P_FECHAR, KKU_ROT_FECHAR, 0.365, 0.524, 0.028, 0.028, 6006)
    set KKP_c_btxt=KKP_txt(pg, KKU_F_PEQUENA, 0.190, 0.492, 0.205, 0.014)
    loop
        exitwhen s>11
        call KKP_linha(pg, 0.190, 0.476-(s-1)*0.0255, 0.205, 0.025, 4000+s, true, false)
        set s=s+1
    endloop
    call KKP_bpapel(pg, KKU_P_SETA_ESQ, KKU_ROT_SETA_ESQ, 0.190, 0.193, 0.030, 0.024, 5001)
    set KKP_c_pag=KKP_txt(pg, KKU_F_PEQUENA, 0.222, 0.193, 0.141, 0.024)
    call KKU_alinha(KKP_c_pag, KKU_AL_MEIO_CENTRO)
    call KKP_bpapel(pg, KKU_P_SETA_DIR, KKU_ROT_SETA_DIR, 0.365, 0.193, 0.030, 0.024, 5002)
    call KKP_caixa_nova(pg, false, 0.400, 0.522, 0.370, 0.357)
    set KKP_c_dico=KKP_quad(pg, KKU_P_ICONE_PADRAO, 0.408, 0.514, 0.036)
    set KKP_c_dnome=KKP_txt(pg, KKU_F_NORMAL, 0.450, 0.514, 0.314, 0.020)
    set KKP_c_dsub=KKP_txt(pg, KKU_F_PEQUENA, 0.450, 0.493, 0.150, 0.014)
    call KKP_btxt(pg, "Favorite", 0.674, 0.496, 0.090, 0.024, 6003)
//{{KK_SE:KK_PAINEL_CRAFT}}
    call KKP_btxt(pg, "Craft", 0.580, 0.496, 0.090, 0.024, 6007)
    call KKU_poe(KKP_c_dsub, KKU_x[KKP_c_dsub], KKU_y[KKP_c_dsub], KKP_gw(0.125), KKP_gh(0.014))
//{{KK_FIMSE:KK_PAINEL_CRAFT}}
//{{KK_SE:KK_PAINEL_EXTRA}}
    if KKP_b3_rot!="" then
        call KKP_btxt(pg, KKP_b3_rot, 0.674, 0.520, 0.090, 0.022, 6008)
        call KKU_poe(KKP_c_dnome, KKU_x[KKP_c_dnome], KKU_y[KKP_c_dnome], KKP_gw(0.220), KKP_gh(0.020))
    endif
//{{KK_FIMSE:KK_PAINEL_EXTRA}}
    set KKP_c_rtit=KKP_txt(pg, KKU_F_PEQUENA, 0.408, 0.468, 0.356, 0.014)
    set s=1
    loop
        exitwhen s>8
        set x=0.408+(s-1)*0.0355
        set KKP_c_rico[s]=KKP_quad(pg, KKU_P_ICONE_PADRAO, x, 0.452, 0.030)
        set KKP_c_rok[s]=KKP_sobre(pg, KKU_P_VISTO, KKP_c_rico[s], 0.017, 0.003, 0.014)
        set KKP_c_rqt[s]=KKP_txt(pg, KKU_F_PEQUENA, x-0.003, 0.420, 0.036, 0.011)
        call KKU_alinha(KKP_c_rqt[s], KKU_AL_TOPO_CENTRO)
        set KKP_c_rbt[s]=KKP_bt(pg, KKP_c_rico[s], 7000+s, false)
        set s=s+1
    endloop
    set KKP_c_utit=KKP_txt(pg, KKU_F_PEQUENA, 0.408, 0.404, 0.356, 0.014)
    call KKP_bpapel(pg, KKU_P_SETA_ESQ, KKU_ROT_SETA_ESQ, 0.406, 0.389, 0.020, 0.030, 6004)
    set s=1
    loop
        exitwhen s>6
        set x=0.430+(s-1)*0.0355
        set KKP_c_uico[s]=KKP_quad(pg, KKU_P_ICONE_PADRAO, x, 0.389, 0.030)
        set KKP_c_ubt[s]=KKP_bt(pg, KKP_c_uico[s], 8000+s, true)
        set s=s+1
    endloop
    call KKP_bpapel(pg, KKU_P_SETA_DIR, KKU_ROT_SETA_DIR, 0.645, 0.389, 0.020, 0.030, 6005)
    set KKP_c_desc=KKU_area(pg, KKP_gx(0.404), KKP_gy(0.354), KKP_gw(0.362), KKP_gh(0.186))
endfunction

//{{KK_SE:KK_PAINEL_GRUPOS8}}
function KKP_cria_chefes8 takes nothing returns nothing
    local integer pg=KKP_pag[3]
    local integer s=1
    local integer c
    local integer r
    local real x
    local real y
    if KKP_gr_n>8 then
        set KKP_gr_n=8
    endif
    loop
        exitwhen s>KKP_gr_n
        call KKP_btxt(pg, KKP_gr_nome[s], 0.100+ModuloInteger(s-1, 4)*0.074, 0.526-((s-1)/4)*0.022, 0.071, 0.020, 9000+s)
        set s=s+1
    endloop
    set s=1
    loop
        exitwhen s>11
        call KKP_linha(pg, 0.100, 0.482-(s-1)*0.0262, 0.292, 0.025, 10000+s, true, false)
        set s=s+1
    endloop
    call KKP_bpapel(pg, KKU_P_SETA_ESQ, KKU_ROT_SETA_ESQ, 0.100, 0.193, 0.030, 0.024, 11001)
    set KKP_b_pag=KKP_txt(pg, KKU_F_PEQUENA, 0.132, 0.193, 0.228, 0.024)
    call KKU_alinha(KKP_b_pag, KKU_AL_MEIO_CENTRO)
    call KKP_bpapel(pg, KKU_P_SETA_DIR, KKU_ROT_SETA_DIR, 0.362, 0.193, 0.030, 0.024, 11002)
    call KKP_caixa_nova(pg, false, 0.400, 0.522, 0.370, 0.357)
    set KKP_b_dico=KKP_quad(pg, KKU_P_ICONE_PADRAO, 0.408, 0.514, 0.040)
    set KKP_b_dnome=KKP_txt(pg, KKU_F_NORMAL, 0.454, 0.514, 0.310, 0.020)
    set KKP_b_dinfo=KKP_txt(pg, KKU_F_PEQUENA, 0.454, 0.493, 0.310, 0.020)
    set KKP_b_dnota=KKP_txt(pg, KKU_F_PEQUENA, 0.408, 0.470, 0.356, 0.046)
    call KKP_btxt(pg, "Show on map", 0.648, 0.420, 0.116, 0.024, 13001)
    set KKP_b_dtit=KKP_txt(pg, KKU_F_PEQUENA, 0.408, 0.414, 0.238, 0.026)
    set s=1
    loop
        exitwhen s>12
        set c=(s-1)/6
        set r=(s-1)-c*6
        set x=0.408+c*0.181
        set y=0.386-r*0.0362
        set KKP_b_dico2[s]=KKP_quad(pg, KKU_P_ICONE_PADRAO, x, y, 0.030)
        set KKP_b_dtx[s]=KKP_txt(pg, KKU_F_PEQUENA, x+0.034, y+0.001, 0.145, 0.032)
        set KKP_b_dbt[s]=KKP_bt(pg, KKP_b_dico2[s], 12000+s, false)
        set s=s+1
    endloop
endfunction

//{{KK_FIMSE:KK_PAINEL_GRUPOS8}}
function KKP_cria_chefes takes nothing returns nothing
    local integer pg=KKP_pag[3]
    local integer s=1
    local integer c
    local integer r
    local real x
    local real y
//{{KK_SE:KK_PAINEL_GRUPOS8}}
    if KKP_gr_n>4 then
        call KKP_cria_chefes8()
        return
    endif
//{{KK_FIMSE:KK_PAINEL_GRUPOS8}}
    loop
        exitwhen s>KKP_gr_n
        call KKP_btxt(pg, KKP_gr_nome[s], 0.100+(s-1)*0.074, 0.524, 0.071, 0.026, 9000+s)
        set s=s+1
    endloop
    set s=1
    loop
        exitwhen s>11
        call KKP_linha(pg, 0.100, 0.492-(s-1)*0.0262, 0.292, 0.025, 10000+s, true, false)
        set s=s+1
    endloop
    call KKP_bpapel(pg, KKU_P_SETA_ESQ, KKU_ROT_SETA_ESQ, 0.100, 0.193, 0.030, 0.024, 11001)
    set KKP_b_pag=KKP_txt(pg, KKU_F_PEQUENA, 0.132, 0.193, 0.228, 0.024)
    call KKU_alinha(KKP_b_pag, KKU_AL_MEIO_CENTRO)
    call KKP_bpapel(pg, KKU_P_SETA_DIR, KKU_ROT_SETA_DIR, 0.362, 0.193, 0.030, 0.024, 11002)
    call KKP_caixa_nova(pg, false, 0.400, 0.522, 0.370, 0.357)
    set KKP_b_dico=KKP_quad(pg, KKU_P_ICONE_PADRAO, 0.408, 0.514, 0.040)
    set KKP_b_dnome=KKP_txt(pg, KKU_F_NORMAL, 0.454, 0.514, 0.310, 0.020)
    set KKP_b_dinfo=KKP_txt(pg, KKU_F_PEQUENA, 0.454, 0.493, 0.310, 0.020)
    set KKP_b_dnota=KKP_txt(pg, KKU_F_PEQUENA, 0.408, 0.470, 0.356, 0.046)
    call KKP_btxt(pg, "Show on map", 0.648, 0.420, 0.116, 0.024, 13001)
    set KKP_b_dtit=KKP_txt(pg, KKU_F_PEQUENA, 0.408, 0.414, 0.238, 0.026)
    set s=1
    loop
        exitwhen s>12
        set c=(s-1)/6
        set r=(s-1)-c*6
        set x=0.408+c*0.181
        set y=0.386-r*0.0362
        set KKP_b_dico2[s]=KKP_quad(pg, KKU_P_ICONE_PADRAO, x, y, 0.030)
        set KKP_b_dtx[s]=KKP_txt(pg, KKU_F_PEQUENA, x+0.034, y+0.001, 0.145, 0.032)
        set KKP_b_dbt[s]=KKP_bt(pg, KKP_b_dico2[s], 12000+s, false)
        set s=s+1
    endloop
endfunction

function KKP_cria_mapa takes nothing returns nothing
    local integer pg=KKP_pag[4]
    local integer s=1
    local integer c
    local integer r
    local real x
    local real y
    loop
        exitwhen s>10
        set c=ModuloInteger(s-1, 5)
        set r=(s-1)/5
        call KKP_btxt(pg, "", 0.100+c*0.134, 0.524-r*0.027, 0.131, 0.026, 16000+s)
        set s=s+1
    endloop
    set KKP_g_topo_tx=KKP_txt(pg, KKU_F_PEQUENA, 0.100, 0.466, 0.670, 0.030)
    set KKP_g_corpo1=KKP_pag_nova(pg)
    set KKP_g_marca=KKU_img(KKP_g_corpo1, KKU_P_MARCA, KKP_gx(0.100)-KKP_gs(0.003), KKP_gy(0.432)+KKP_gs(0.003), KKP_gs(0.034)+KKP_gs(0.006), KKP_gs(0.034)+KKP_gs(0.006))
    call KKU_esconde(KKP_g_marca)
    set s=1
    loop
        exitwhen s>40
        set c=ModuloInteger(s-1, 8)
        set r=(s-1)/8
        set x=0.100+c*0.0375
        set y=0.432-r*0.0375
        set KKP_g_icof[s]=KKP_quad(KKP_g_corpo1, KKU_P_ICONE_PADRAO, x, y, 0.034)
        set KKP_g_dim[s]=KKP_sobre(KKP_g_corpo1, KKU_P_ESCURO, KKP_g_icof[s], 0.0, 0.0, 0.034)
        call KKU_alfa(KKP_g_dim[s], 170)
        set KKP_g_cur[s]=KKP_sobre(KKP_g_corpo1, KKU_P_VISTO, KKP_g_icof[s], 0.019, -0.019, 0.015)
        set KKP_g_bt[s]=KKP_bt(KKP_g_corpo1, KKP_g_icof[s], 14000+s, true)
        set s=s+1
    endloop
    call KKP_bpapel(KKP_g_corpo1, KKU_P_SETA_ESQ, KKU_ROT_SETA_ESQ, 0.100, 0.236, 0.030, 0.024, 15001)
    set KKP_g_pag=KKP_txt(KKP_g_corpo1, KKU_F_PEQUENA, 0.132, 0.236, 0.200, 0.024)
    call KKU_alinha(KKP_g_pag, KKU_AL_MEIO_CENTRO)
    call KKP_bpapel(KKP_g_corpo1, KKU_P_SETA_DIR, KKU_ROT_SETA_DIR, 0.334, 0.236, 0.030, 0.024, 15002)
    set KKP_g_corpo2=KKP_pag_nova(pg)
    set s=1
    loop
        exitwhen s>KKP_GL
        call KKP_linha(KKP_g_corpo2, 0.100, 0.432-(s-1)*0.0255, 0.298, 0.025, 20000+s, true, true)
        set s=s+1
    endloop
    call KKP_bpapel(KKP_g_corpo2, KKU_P_SETA_ESQ, KKU_ROT_SETA_ESQ, 0.100, 0.193, 0.030, 0.024, 21001)
    set KKP_l_pag=KKP_txt(KKP_g_corpo2, KKU_F_PEQUENA, 0.132, 0.193, 0.234, 0.024)
    call KKU_alinha(KKP_l_pag, KKU_AL_MEIO_CENTRO)
    call KKP_bpapel(KKP_g_corpo2, KKU_P_SETA_DIR, KKU_ROT_SETA_DIR, 0.368, 0.193, 0.030, 0.024, 21002)
    set KKP_g_dcx=KKP_caixa_nova(pg, false, 0.405, 0.438, 0.365, 0.273)
    set KKP_g_dico=KKP_quad(pg, KKU_P_ICONE_PADRAO, 0.413, 0.430, 0.040)
    set KKP_g_dnome=KKP_txt(pg, KKU_F_NORMAL, 0.459, 0.430, 0.305, 0.040)
    if KKU_PV_N<=0 then
        set KKP_g_dtxt=KKP_txt(pg, KKU_F_PEQUENA, 0.413, 0.382, 0.351, 0.150)
    else
        set KKP_g_dtxt=KKP_txt(pg, KKU_F_PEQUENA, 0.413, 0.382, 0.215, 0.150)
        set KKP_pv_det=KKU_sprite(pg)
        call KKU_esconde(KKP_pv_det)
        set KKP_pv_cx_det=KKP_pv_caixa(pg, 0.640, 0.248)
        set KKP_pv_rot_det=KKP_pv_rot_ult
        set KKP_pv_al_det=KKP_pv_al_ult
        set KKP_pv_alb_det=KKP_pv_alb_ult
    endif
    call KKP_btxt(pg, "", 0.413, 0.200, 0.170, 0.026, 17001)
    call KKP_btxt(pg, "", 0.590, 0.200, 0.170, 0.026, 17002)
endfunction

function KKP_cria_mapa3 takes nothing returns nothing
    local integer pg=KKP_pag[4]
    local integer a=1
    local integer s
    loop
        exitwhen a>KKP_aba_n
        set s=1
        loop
            exitwhen s>KKP_ab_subn[a] or s>10
            if KKP_aba_tipo[a]==4 and KKP_ab_lay[a*16+s]==3 then
                set KKP_tem3=true
            endif
            set s=s+1
        endloop
        set a=a+1
    endloop
    if not KKP_tem3 or pg<=0 or pg>=KKU_MAX then
        return
    endif
    set KKP_g_corpo3=KKP_pag_nova(pg)
    set pg=KKP_g_corpo3
    set s=1
    loop
        exitwhen s>10
        call KKP_linha(pg, 0.100, 0.522-(s-1)*0.0262, 0.085, 0.025, 18000+s, false, false)
        set s=s+1
    endloop
    set KKP_k_topo=KKP_txt(pg, KKU_F_PEQUENA, 0.190, 0.522, 0.235, 0.040)
    set s=1
    loop
        exitwhen s>KKP_KL
        call KKP_linha(pg, 0.190, 0.476-(s-1)*0.0255, 0.235, 0.025, 18100+s, true, true)
        set s=s+1
    endloop
    call KKP_bpapel(pg, KKU_P_SETA_ESQ, KKU_ROT_SETA_ESQ, 0.190, 0.193, 0.030, 0.024, 18151)
    set KKP_k_pag=KKP_txt(pg, KKU_F_PEQUENA, 0.222, 0.193, 0.171, 0.024)
    call KKU_alinha(KKP_k_pag, KKU_AL_MEIO_CENTRO)
    call KKP_bpapel(pg, KKU_P_SETA_DIR, KKU_ROT_SETA_DIR, 0.395, 0.193, 0.030, 0.024, 18152)
    call KKP_caixa_nova(pg, false, 0.430, 0.522, 0.340, 0.357)
    set KKP_k_dico=KKP_quad(pg, KKU_P_ICONE_PADRAO, 0.438, 0.514, 0.036)
    set KKP_k_dnome=KKP_txt(pg, KKU_F_NORMAL, 0.480, 0.514, 0.284, 0.036)
    if KKU_PV_N<=0 then
        set KKP_k_dtxt=KKP_txt(pg, KKU_F_PEQUENA, 0.438, 0.470, 0.324, 0.236)
    else
        set KKP_k_dtxt=KKP_txt(pg, KKU_F_PEQUENA, 0.438, 0.470, 0.190, 0.236)
        set KKP_pv_k=KKU_sprite(pg)
        call KKU_esconde(KKP_pv_k)
        set KKP_pv_cx_k=KKP_pv_caixa(pg, 0.640, 0.262)
        set KKP_pv_rot_k=KKP_pv_rot_ult
        set KKP_pv_al_k=KKP_pv_al_ult
        set KKP_pv_alb_k=KKP_pv_alb_ult
    endif
    call KKP_btxt(pg, "", 0.438, 0.200, 0.160, 0.026, 18161)
    call KKP_btxt(pg, "", 0.604, 0.200, 0.160, 0.026, 18162)
endfunction

function KKP_carga_indice takes nothing returns nothing
    local integer i=1
    local integer g
    loop
        exitwhen i>KKP_it_n
        call SaveInteger(KKP_ht, KKP_it[i], 1, i)
        set i=i+1
    endloop
    set i=1
    loop
        exitwhen i>KKP_bs_n
        set g=KKP_bs_grupo[i]
        if KKP_gr_qt[g]==0 then
            set KKP_gr_ini[g]=i
        endif
        set KKP_gr_qt[g]=KKP_gr_qt[g]+1
        set i=i+1
    endloop
endfunction

function KKP_carga_busca takes nothing returns nothing
    local integer i=KKP_carga_k
    local integer fim=IMinBJ(KKP_it_n, i+119)
    loop
        exitwhen i>fim
        set KKP_it_busca[i]=KKP_limpa(GetObjectName(KKP_it[i]))
        set i=i+1
    endloop
endfunction

//{{KK_SE:KK_PAINEL_EXTRA}}
function KKP_dados_parte takes nothing returns nothing
    set KKP_arg_i=KKP_dados_k
    set KKP_arg_ok=false
    call KKP_chama(KKP_G_DADOS)
endfunction

function KKP_dados_mapa takes nothing returns nothing
    local integer i=1
    loop
        exitwhen i>KKP_it_n
        call RemoveSavedInteger(KKP_ht, KKP_it[i], 1)
        set i=i+1
    endloop
    set KKP_dados_k=1
    loop
        exitwhen KKP_dados_k>KKP_DADOS_MAX
        call ExecuteFunc("KKP_dados_parte")
        exitwhen not KKP_arg_ok
        set KKP_dados_k=KKP_dados_k+1
    endloop
    set i=1
    loop
        exitwhen i>16
        set KKP_gr_qt[i]=0
        set KKP_gr_ini[i]=0
        set i=i+1
    endloop
    call ExecuteFunc("KKP_carga_indice")
    set KKP_carga_k=1
    loop
        exitwhen KKP_carga_k>KKP_it_n
        call ExecuteFunc("KKP_carga_busca")
        set KKP_carga_k=KKP_carga_k+120
    endloop
endfunction

//{{KK_FIMSE:KK_PAINEL_EXTRA}}
//{{KK_SE:KK_PAINEL_IMG}}
function KKP_cria_img takes nothing returns nothing
    local integer pg=KKP_pag[4]
    if pg<=0 or pg>=KKU_MAX or KKP_g_dtxt<=0 or KKP_g_dtxt>=KKU_MAX then
        return
    endif
    set KKP_im_x[1]=KKU_x[KKP_g_dtxt]
    set KKP_im_y[1]=KKU_y[KKP_g_dtxt]
    set KKP_im_w[1]=KKU_w[KKP_g_dtxt]
    set KKP_im_h[1]=KKU_h[KKP_g_dtxt]
    set KKP_g_dimg=KKU_img(pg, KKU_P_ICONE_PADRAO, KKP_im_x[1], KKP_im_y[1], KKP_im_w[1], KKP_gh(0.010))
    call KKU_esconde(KKP_g_dimg)
    if KKP_tem3 and KKP_g_corpo3>0 and KKP_g_corpo3<KKU_MAX and KKP_k_dtxt>0 and KKP_k_dtxt<KKU_MAX then
        set KKP_im_x[2]=KKU_x[KKP_k_dtxt]
        set KKP_im_y[2]=KKU_y[KKP_k_dtxt]
        set KKP_im_w[2]=KKU_w[KKP_k_dtxt]
        set KKP_im_h[2]=KKU_h[KKP_k_dtxt]
        set KKP_k_dimg=KKU_img(KKP_g_corpo3, KKU_P_ICONE_PADRAO, KKP_im_x[2], KKP_im_y[2], KKP_im_w[2], KKP_gh(0.010))
        call KKU_esconde(KKP_k_dimg)
    endif
endfunction

//{{KK_FIMSE:KK_PAINEL_IMG}}
//{{KK_SE:KK_PAINEL_CHEFE_BT}}
function KKP_cria_chefes_bb takes nothing returns nothing
    local integer pg=KKP_pag[3]
    if KKP_bb_rot=="" or pg<=0 or pg>=KKU_MAX then
        return
    endif
    call KKP_btxt(pg, KKP_bb_rot, 0.674, 0.520, 0.090, 0.022, 13002)
    call KKU_poe(KKP_b_dnome, KKU_x[KKP_b_dnome], KKU_y[KKP_b_dnome], KKP_gw(0.215), KKP_gh(0.020))
endfunction

//{{KK_FIMSE:KK_PAINEL_CHEFE_BT}}
//{{KK_SE:KK_PAINEL_DROPS}}
function KKP_cria_chefes_dpag takes nothing returns nothing
    local integer pg=KKP_pag[3]
    if pg<=0 or pg>=KKU_MAX then
        return
    endif
    call KKP_bpapel(pg, KKU_P_SETA_ESQ, KKU_ROT_SETA_ESQ, 0.408, 0.205, 0.026, 0.024, 13003)
    set KKP_b_dpag=KKP_txt(pg, KKU_F_PEQUENA, 0.436, 0.205, 0.300, 0.024)
    call KKU_alinha(KKP_b_dpag, KKU_AL_MEIO_CENTRO)
    call KKP_bpapel(pg, KKU_P_SETA_DIR, KKU_ROT_SETA_DIR, 0.740, 0.205, 0.026, 0.024, 13004)
    call KKU_esconde(LoadInteger(KKP_ht, 13003, 0))
    call KKU_esconde(LoadInteger(KKP_ht, 13004, 0))
    call KKU_esconde(KKP_b_dpag)
endfunction

//{{KK_FIMSE:KK_PAINEL_DROPS}}
function KKP_espera takes nothing returns nothing
    if KKP_iniciado then
        call PauseTimer(GetExpiredTimer())
        return
    endif
//{{KK_SE:KK_PAINEL_EXTRA}}
    if KKP_g_tem[KKP_G_PRONTO] then
        set KKP_arg_ok=true
        call KKP_chama(KKP_G_PRONTO)
        if not KKP_arg_ok then
            return
        endif
    endif
//{{KK_FIMSE:KK_PAINEL_EXTRA}}
    set KKP_iniciado=true
    call PauseTimer(GetExpiredTimer())
//{{KK_SE:KK_PAINEL_EXTRA}}
    if KKP_g_tem[KKP_G_DADOS] then
        call KKP_dados_mapa()
    endif
//{{KK_FIMSE:KK_PAINEL_EXTRA}}
    call ExecuteFunc("KKP_cria_base")
    call ExecuteFunc("KKP_cria_ficha")
    call ExecuteFunc("KKP_cria_codex")
    call ExecuteFunc("KKP_cria_chefes")
    call ExecuteFunc("KKP_cria_mapa")
    call ExecuteFunc("KKP_cria_mapa3")
//{{KK_SE:KK_PAINEL_IMG}}
    call ExecuteFunc("KKP_cria_img")
//{{KK_FIMSE:KK_PAINEL_IMG}}
//{{KK_SE:KK_PAINEL_CHEFE_BT}}
    call ExecuteFunc("KKP_cria_chefes_bb")
//{{KK_FIMSE:KK_PAINEL_CHEFE_BT}}
//{{KK_SE:KK_PAINEL_DROPS}}
    call ExecuteFunc("KKP_cria_chefes_dpag")
//{{KK_FIMSE:KK_PAINEL_DROPS}}
    set KKP_nq=KKU_n
    set KKP_pronto=KKP_raiz>0 and KKP_raiz<KKU_MAX and KKP_pag[4]>0 and KKP_pag[4]<KKU_MAX
    set KKP_pronto=KKP_pronto and KKP_f_mapa>0 and KKP_f_mapa<KKU_MAX and KKP_c_desc>0 and KKP_c_desc<KKU_MAX
    set KKP_pronto=KKP_pronto and KKP_b_dtx[12]>0 and KKP_b_dtx[12]<KKU_MAX and KKP_g_dtxt>0 and KKP_g_dtxt<KKU_MAX
    set KKP_pronto=KKP_pronto and LoadInteger(KKP_ht, 17002, 0)>0 and KKP_f_titulo>0 and KKP_f_titulo<KKU_MAX
    set KKP_pronto=KKP_pronto and KKP_f_aviso>0 and KKP_f_aviso<KKU_MAX and KKP_g_dcx>0 and KKP_g_dcx<KKU_MAX
//{{KK_SE:KK_PAINEL_EXTRA}}
    if KKP_b3_rot!="" then
        set KKP_pronto=KKP_pronto and LoadInteger(KKP_ht, 6008, 0)>0
    endif
    if KKP_com_link then
        set KKP_pronto=KKP_pronto and KKP_f_lico>0 and KKP_f_lico<KKU_MAX and KKP_f_ltxt>0 and KKP_f_lbt>0
    endif
//{{KK_FIMSE:KK_PAINEL_EXTRA}}
//{{KK_SE:KK_PAINEL_IMG}}
    set KKP_pronto=KKP_pronto and KKP_g_dimg>0 and KKP_g_dimg<KKU_MAX
    if KKP_tem3 then
        set KKP_pronto=KKP_pronto and KKP_k_dimg>0 and KKP_k_dimg<KKU_MAX
    endif
//{{KK_FIMSE:KK_PAINEL_IMG}}
//{{KK_SE:KK_PAINEL_CHEFE_BT}}
    if KKP_bb_rot!="" then
        set KKP_pronto=KKP_pronto and LoadInteger(KKP_ht, 13002, 0)>0
    endif
//{{KK_FIMSE:KK_PAINEL_CHEFE_BT}}
//{{KK_SE:KK_PAINEL_DROPS}}
    set KKP_pronto=KKP_pronto and KKP_b_dpag>0 and KKP_b_dpag<KKU_MAX and LoadInteger(KKP_ht, 13004, 0)>0
//{{KK_FIMSE:KK_PAINEL_DROPS}}
    if KKP_tem3 then
        set KKP_pronto=KKP_pronto and KKP_g_corpo3>0 and KKP_g_corpo3<KKU_MAX and KKP_k_topo>0 and KKP_k_pag>0 and KKP_k_dico>0
        set KKP_pronto=KKP_pronto and KKP_k_dnome>0 and KKP_k_dtxt>0 and KKP_k_dtxt<KKU_MAX and LoadInteger(KKP_ht, 18162, 0)>0
        if KKU_PV_N>0 then
            set KKP_pronto=KKP_pronto and KKP_pv_k>0 and KKP_pv_k<KKU_MAX and KKP_pv_cx_k>0 and KKP_pv_rot_k>0 and KKP_pv_al_k>0 and KKP_pv_alb_k>0
        endif
    endif
    if KKU_PV_N>0 then
        set KKP_pronto=KKP_pronto and KKP_pv_ficha>0 and KKP_pv_ficha<KKU_MAX and KKP_pv_det>0 and KKP_pv_det<KKU_MAX
        set KKP_pronto=KKP_pronto and KKP_pv_cx_ficha>0 and KKP_pv_rot_ficha>0 and KKP_pv_cx_det>0 and KKP_pv_rot_det>0
        set KKP_pronto=KKP_pronto and KKP_pv_al_ficha>0 and KKP_pv_alb_ficha>0 and KKP_pv_al_det>0 and KKP_pv_alb_det>0
    endif
    call KKU_aplica()
endfunction

function KKP_init takes nothing returns nothing
    local integer i=1
    call KKU_init()
    set KKP_ht=InitHashtable()
//{{KK_SE:KK_PAINEL_PADRAO}}
    set KKP_g_auto=CreateGroup()
//{{KK_FIMSE:KK_PAINEL_PADRAO}}
    call KKP_dados_todos()
    call ExecuteFunc("KKP_carga_indice")
    set KKP_carga_k=1
    loop
        exitwhen KKP_carga_k>KKP_it_n
        call ExecuteFunc("KKP_carga_busca")
        set KKP_carga_k=KKP_carga_k+120
    endloop
    call KKU_ao(KKU_AO_CLIQUE, function KKP_ao_clique)
    call KKU_ao(KKU_AO_RODA, function KKP_ao_roda)
    call KKU_ao(KKU_AO_TEXTO, function KKP_ao_texto)
    call KKU_ao(KKU_AO_MENU, function KKP_ao_menu)
    call KKU_ao(KKU_AO_FECHA, function KKP_ao_fecha)
    call KKU_ao(KKU_AO_CARGA, function KKP_ao_carga)
    set KKP_t_sync=CreateTrigger()
    call TriggerAddAction(KKP_t_sync, function KKP_sync)
    set i=0
    loop
        exitwhen i>=KKP_jogadores
        call BlzTriggerRegisterPlayerSyncEvent(KKP_t_sync, Player(i), "kkp", false)
        set KKP_aberto[i]=false
        set KKP_aba[i]=1
        set KKP_favn[i]=0
        set KKP_mult[i]=1.0
        set i=i+1
    endloop
    set KKP_tm_espera=CreateTimer()
    call TimerStart(KKP_tm_espera, 0.50, true, function KKP_espera)
    set KKP_tm_1s=CreateTimer()
    call TimerStart(KKP_tm_1s, 1.00, true, function KKP_tique1)
    set KKP_tm_local=CreateTimer()
    call TimerStart(KKP_tm_local, 0.05, true, function KKP_tique_local)
endfunction
