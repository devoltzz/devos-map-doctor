//@GLOBALS
string KKP_titulo="Codex"
string KKP_toc="war3mapImported\\KKPainel.toc"
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
string KKP_arg_s=""
boolean KKP_arg_ok=false
unit array KKP_heroi
string array KKP_x_mapa
real array KKP_mult
unit array KKP_inv_u
integer array KKP_g_n
integer array KKP_g_atual
string array KKP_g_topo
string array KKP_g_det
string array KKP_g_b1
string array KKP_g_b2
integer array KKP_g_bm
string array KKP_g_nome
string array KKP_g_ico
string array KKP_g_info
string array KKP_g_edet
boolean array KKP_g_trava
boolean array KKP_g_ok
integer array KKP_g_eb
integer array KKP_g_val
hashtable KKP_ht=null
boolean KKP_pronto=false
boolean KKP_iniciado=false
integer KKP_carga_k=0
integer KKP_nq=0
trigger KKP_t_clique=null
trigger KKP_t_roda=null
trigger KKP_t_busca=null
trigger KKP_t_tecla=null
trigger KKP_t_sync=null
timer KKP_tm_espera=null
timer KKP_tm_1s=null
timer KKP_tm_local=null
boolean array KKP_aberto
integer array KKP_aba
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
framehandle KKP_raiz=null
framehandle KKP_caixa=null
framehandle KKP_fundo=null
framehandle array KKP_pag
framehandle KKP_f_ico=null
framehandle KKP_f_nome=null
framehandle KKP_f_stat=null
framehandle KKP_f_mapa=null
framehandle KKP_c_busca=null
framehandle KKP_c_btxt=null
framehandle KKP_c_pag=null
framehandle KKP_c_dico=null
framehandle KKP_c_dnome=null
framehandle KKP_c_dsub=null
framehandle KKP_c_rtit=null
framehandle array KKP_c_rico
framehandle array KKP_c_rbt
framehandle array KKP_c_rok
framehandle array KKP_c_rqt
framehandle KKP_c_utit=null
framehandle array KKP_c_uico
framehandle array KKP_c_ubt
framehandle KKP_c_desc=null
framehandle KKP_b_pag=null
framehandle KKP_b_dico=null
framehandle KKP_b_dnome=null
framehandle KKP_b_dinfo=null
framehandle KKP_b_dnota=null
framehandle KKP_b_dtit=null
framehandle array KKP_b_dico2
framehandle array KKP_b_dbt
framehandle array KKP_b_dtx
framehandle KKP_g_topo_tx=null
framehandle KKP_g_corpo1=null
framehandle KKP_g_corpo2=null
framehandle KKP_l_pag=null
framehandle array KKP_g_bt
framehandle array KKP_g_icof
framehandle array KKP_g_dim
framehandle array KKP_g_cur
framehandle KKP_g_marca=null
framehandle KKP_g_pag=null
framehandle KKP_g_dico=null
framehandle KKP_g_dnome=null
framehandle KKP_g_dtxt=null
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
constant real KKP_DX=-0.035
constant integer KKP_GL=9
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
    endif
    return KKP_t_g8
endfunction

function KKP_gancho takes integer qual,code f returns nothing
    if qual<1 or qual>8 then
        return
    endif
    call TriggerAddCondition(KKP_tg(qual), Condition(f))
    set KKP_g_tem[qual]=true
endfunction

function KKP_chama takes integer qual returns boolean
    if qual<1 or qual>8 or not KKP_g_tem[qual] then
        return false
    endif
    call TriggerEvaluate(KKP_tg(qual))
    return true
endfunction

function KKP_amostra takes integer pid returns nothing
    local unit h
    set KKP_arg_pid=pid
    call KKP_chama(KKP_G_FICHA)
    set h=KKP_heroi[pid]
    if h==null or GetUnitTypeId(h)==0 then
        set KKP_h_ok[pid]=false
        set h=null
        return
    endif
    set KKP_h_ok[pid]=true
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
    set KKP_arg_pid=pid
    set KKP_arg_s=s
    call KKP_chama(KKP_G_FAV_GRAVA)
endfunction

function KKP_poe takes framehandle f,real x,real y,real w,real h returns nothing
    call BlzFrameClearAllPoints(f)
    call BlzFrameSetAbsPoint(f, FRAMEPOINT_TOPLEFT, x+KKP_DX, y)
    call BlzFrameSetSize(f, w, h)
endfunction

function KKP_img takes framehandle pai,string tex,real x,real y,real w,real h returns framehandle
    local framehandle f=BlzCreateFrameByType("BACKDROP", "KKPImg", pai, "", 0)
    set KKP_nq=KKP_nq+1
    call KKP_poe(f, x, y, w, h)
    call BlzFrameSetTexture(f, tex, 0, true)
    return f
endfunction

function KKP_caixa_nova takes framehandle pai,boolean apertada,real x,real y,real w,real h returns framehandle
    local framehandle f
    if apertada then
        set f=BlzCreateFrame("QuestButtonPushedBackdropTemplate", pai, 0, 0)
    else
        set f=BlzCreateFrame("QuestButtonBaseTemplate", pai, 0, 0)
    endif
    set KKP_nq=KKP_nq+1
    call KKP_poe(f, x, y, w, h)
    return f
endfunction

function KKP_txt takes framehandle pai,string modelo,real x,real y,real w,real h returns framehandle
    local framehandle f=BlzCreateFrameByType("TEXT", "KKPTxt", pai, modelo, 0)
    set KKP_nq=KKP_nq+1
    call KKP_poe(f, x, y, w, h)
    call BlzFrameSetTextAlignment(f, TEXT_JUSTIFY_TOP, TEXT_JUSTIFY_LEFT)
    call BlzFrameSetText(f, "")
    return f
endfunction

function KKP_bt takes framehandle pai,real x,real y,real w,real h,integer cod,boolean roda returns framehandle
    local framehandle b=BlzCreateFrameByType("BUTTON", "KKPBt", pai, "ScoreScreenTabButtonTemplate", 0)
    set KKP_nq=KKP_nq+1
    call KKP_poe(b, x, y, w, h)
    call SaveInteger(KKP_ht, GetHandleId(b), 0, cod)
    call BlzTriggerRegisterFrameEvent(KKP_t_clique, b, FRAMEEVENT_CONTROL_CLICK)
    if roda then
        call BlzTriggerRegisterFrameEvent(KKP_t_roda, b, FRAMEEVENT_MOUSE_WHEEL)
    endif
    return b
endfunction

function KKP_btxt takes framehandle pai,string rot,real x,real y,real w,real h,integer cod returns framehandle
    local framehandle b=BlzCreateFrameByType("GLUETEXTBUTTON", "KKPBtTxt", pai, "ScriptDialogButton", 0)
    set KKP_nq=KKP_nq+1
    call KKP_poe(b, x, y, w, h)
    call BlzFrameSetText(b, rot)
    call SaveInteger(KKP_ht, GetHandleId(b), 0, cod)
    call SaveFrameHandle(KKP_ht, cod, 0, b)
    call BlzTriggerRegisterFrameEvent(KKP_t_clique, b, FRAMEEVENT_CONTROL_CLICK)
    return b
endfunction

function KKP_linha takes framehandle pai,real x,real y,real w,real h,integer cod,boolean ico,boolean info returns nothing
    local real tx=x+0.006
    local real tw
    local framehandle f
    call SaveFrameHandle(KKP_ht, cod, 1, KKP_caixa_nova(pai, false, x, y, w, h))
    set f=KKP_caixa_nova(pai, true, x, y, w, h)
    call BlzFrameSetVisible(f, false)
    call SaveFrameHandle(KKP_ht, cod, 2, f)
    if ico then
        set f=KKP_img(pai, "UI\\Widgets\\Console\\Human\\CommandButton\\human-activebutton.blp", x+0.001, y-0.001, h-0.002, h-0.002)
        call BlzFrameSetVisible(f, false)
        call SaveFrameHandle(KKP_ht, cod, 7, f)
        call SaveFrameHandle(KKP_ht, cod, 3, KKP_img(pai, "ReplaceableTextures\\CommandButtons\\BTNSelectHeroOn.blp", x+0.003, y-0.003, h-0.006, h-0.006))
        set tx=x+h+0.002
    endif
    set tw=x+w-tx-0.004
    if info then
        set tw=tw-0.078
    endif
    set f=KKP_txt(pai, "EscMenuLabelTextSmallTemplate", tx, y, tw, h)
    if ico then
        call BlzFrameSetTextAlignment(f, TEXT_JUSTIFY_MIDDLE, TEXT_JUSTIFY_LEFT)
    else
        call BlzFrameSetTextAlignment(f, TEXT_JUSTIFY_MIDDLE, TEXT_JUSTIFY_CENTER)
    endif
    call SaveFrameHandle(KKP_ht, cod, 4, f)
    if info then
        set f=KKP_txt(pai, "EscMenuLabelTextSmallTemplate", x+w-0.082, y, 0.078, h)
        call BlzFrameSetTextAlignment(f, TEXT_JUSTIFY_MIDDLE, TEXT_JUSTIFY_RIGHT)
        call SaveFrameHandle(KKP_ht, cod, 6, f)
    endif
    call SaveFrameHandle(KKP_ht, cod, 5, KKP_bt(pai, x, y, w, h, cod, true))
    set f=null
endfunction

function KKP_vis takes framehandle f,boolean v returns nothing
    if f!=null then
        call BlzFrameSetVisible(f, v)
    endif
endfunction

function KKP_lvis takes integer cod,boolean v returns nothing
    local integer k=1
    loop
        exitwhen k>7
        if (k!=2 and k!=7) or not v then
            call KKP_vis(LoadFrameHandle(KKP_ht, cod, k), v)
        endif
        set k=k+1
    endloop
endfunction

function KKP_lativa takes integer cod,string s,boolean ativo returns nothing
    call KKP_vis(LoadFrameHandle(KKP_ht, cod, 2), ativo)
    call KKP_vis(LoadFrameHandle(KKP_ht, cod, 7), ativo)
    call KKP_vis(LoadFrameHandle(KKP_ht, cod, 1), not ativo)
    if LoadFrameHandle(KKP_ht, cod, 4)!=null then
        if ativo then
            call BlzFrameSetText(LoadFrameHandle(KKP_ht, cod, 4), "|cffffcc00"+s+"|r")
        else
            call BlzFrameSetText(LoadFrameHandle(KKP_ht, cod, 4), s)
        endif
    endif
endfunction

function KKP_rot takes integer cod,string s,boolean ativo returns nothing
    local framehandle b=LoadFrameHandle(KKP_ht, cod, 0)
    if b!=null then
        if ativo then
            call BlzFrameSetText(b, "|cffffcc00"+s+"|r")
        else
            call BlzFrameSetText(b, "|cffd0d0d0"+s+"|r")
        endif
    endif
    set b=null
endfunction

function KKP_bvis takes integer cod,boolean v returns nothing
    call KKP_vis(LoadFrameHandle(KKP_ht, cod, 0), v)
endfunction

function KKP_tem takes integer pid,integer x returns integer
    local integer n=0
    local integer k=0
    local integer s
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
    set u=null
    set it=null
    return n
endfunction

function KKP_des_ficha takes integer pid returns nothing
    local string s
    if not KKP_h_ok[pid] then
        call BlzFrameSetTexture(KKP_f_ico, "ReplaceableTextures\\CommandButtons\\BTNSelectHeroOn.blp", 0, true)
        call BlzFrameSetText(KKP_f_nome, "|cffffcc00"+KKP_txt_sem_heroi+"|r")
        call BlzFrameSetText(KKP_f_stat, "")
    else
        call BlzFrameSetTexture(KKP_f_ico, BlzGetAbilityIcon(KKP_h_tipo[pid]), 0, true)
        call BlzFrameSetText(KKP_f_nome, "|cffffcc00"+KKP_h_nome[pid]+"|r|nLevel "+I2S(KKP_h_nivel[pid]))
        set s="|cffffcc00Strength:|r "+KKP_mil(KKP_h_forb[pid])+"|n|cff999999   base "+KKP_mil(KKP_h_for[pid])+"|r"
        set s=s+"|n|cffffcc00Agility:|r "+KKP_mil(KKP_h_agib[pid])+"|n|cff999999   base "+KKP_mil(KKP_h_agi[pid])+"|r"
        set s=s+"|n|cffffcc00Intelligence:|r "+KKP_mil(KKP_h_intb[pid])+"|n|cff999999   base "+KKP_mil(KKP_h_int[pid])+"|r"
        set s=s+"|n|n|cffffcc00HP:|r "+KKP_mil(KKP_h_vida[pid])+" / "+KKP_mil(KKP_h_vidamax[pid])
        set s=s+"|n|cffffcc00MP:|r "+KKP_mil(KKP_h_mana[pid])+" / "+KKP_mil(KKP_h_manamax[pid])
        set s=s+"|n|cffffcc00Armor:|r "+R2SW(KKP_h_arm[pid], 1, 1)
        set s=s+"|n|cffffcc00Damage:|r "+KKP_mil(KKP_h_dano1[pid])+" - "+KKP_mil(KKP_h_dano2[pid])
        set s=s+"|n|cffffcc00Attack cooldown:|r "+R2SW(KKP_h_cd[pid], 1, 2)+" s"
        set s=s+"|n|cffffcc00Move speed:|r "+I2S(KKP_h_vel[pid])
        call BlzFrameSetText(KKP_f_stat, s)
    endif
    set s=KKP_x_mapa[pid]
    if s==null then
        set s=""
    endif
    call BlzFrameSetText(KKP_f_mapa, s)
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
    local boolean achou=false
    loop
        exitwhen k>KKP_cat_n
        if k==0 then
            call KKP_lativa(3000, "Favorites", KKP_c_q=="" and KKP_c_cat==0)
        else
            call KKP_lativa(3000+k, KKP_cat_nome[k], KKP_c_q=="" and KKP_c_cat==k)
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
            call KKP_lvis(4000+s, true)
            call BlzFrameSetTexture(LoadFrameHandle(KKP_ht, 4000+s, 3), KKP_ico_item(KKP_it[x]), 0, true)
            call KKP_lativa(4000+s, nome, x==KKP_c_sel)
        else
            set KKP_c_lin[s]=0
            call KKP_lvis(4000+s, false)
        endif
        set s=s+1
    endloop
    call BlzFrameSetText(KKP_c_pag, KKP_pagina(KKP_c_top, 11, n))
    if KKP_c_q!="" then
        if KKP_res_i>0 then
            call BlzFrameSetText(KKP_c_btxt, "|cff999999Searching...|r")
        elseif n==1 then
            call BlzFrameSetText(KKP_c_btxt, "|cffffcc001|r result for \""+KKP_c_q+"\"")
        else
            call BlzFrameSetText(KKP_c_btxt, "|cffffcc00"+I2S(n)+"|r results for \""+KKP_c_q+"\"")
        endif
    elseif KKP_c_cat==0 then
        call BlzFrameSetText(KKP_c_btxt, "|cffffcc00Favorites|r: "+I2S(n)+" |cff999999(open an item, click Favorite)|r")
    else
        call BlzFrameSetText(KKP_c_btxt, "|cffffcc00"+KKP_cat_nome[KKP_c_cat]+"|r: "+I2S(n)+" items")
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
        call KKP_vis(KKP_c_rbt[m], false)
        call KKP_vis(KKP_c_rqt[m], false)
        call KKP_vis(KKP_c_rok[m], false)
        set m=m+1
    endloop
    set m=1
    loop
        exitwhen m>6
        call KKP_vis(KKP_c_uico[m], false)
        call KKP_vis(KKP_c_ubt[m], false)
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
    if not vis then
        call BlzFrameSetText(KKP_c_desc, "|cffffcc00"+KKP_titulo+"|r|n|n"+KKP_txt_codex)
        return
    endif
    set id=KKP_it[x]
    call BlzFrameSetTexture(KKP_c_dico, KKP_ico_item(id), 0, true)
    call BlzFrameSetText(KKP_c_dnome, KKP_nome_item(id))
    call BlzFrameSetText(KKP_c_dsub, "|cff999999"+KKP_cat_nome[KKP_it_cat[x]]+"|r")
    if LoadBoolean(KKP_ht, 910000+pid, id) then
        call KKP_rot(6003, "Unfavorite", true)
    else
        call KKP_rot(6003, "Favorite", false)
    endif
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
        call BlzFrameSetTexture(KKP_c_rico[m], KKP_ico_item(ing), 0, true)
        call KKP_vis(KKP_c_rico[m], true)
        call KKP_vis(KKP_c_rbt[m], KKP_idx(ing)>0)
        call KKP_vis(KKP_c_rok[m], ok)
        if q>1 then
            if ok then
                call BlzFrameSetText(KKP_c_rqt[m], "|cff00ff00"+I2S(tem)+"/"+I2S(q)+"|r")
            else
                call BlzFrameSetText(KKP_c_rqt[m], "|cffff5555"+I2S(tem)+"/"+I2S(q)+"|r")
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
        call BlzFrameSetText(KKP_c_rtit, s)
    else
        call BlzFrameSetText(KKP_c_rtit, "|cffffcc00Recipe|r  |cff999999none: this item is not crafted|r")
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
            call BlzFrameSetTexture(KKP_c_uico[m], KKP_ico_item(KKP_it[KKP_us[KKP_it_us[x]+KKP_c_utop+m-1]]), 0, true)
            call KKP_vis(KKP_c_uico[m], true)
            call KKP_vis(KKP_c_ubt[m], true)
        endif
        set m=m+1
    endloop
    call KKP_bvis(6004, KKP_c_utop>0)
    call KKP_bvis(6005, KKP_c_utop+6<un)
    if un>0 then
        call BlzFrameSetText(KKP_c_utit, "|cffffcc00Used in|r  "+I2S(un)+" recipes |cff999999(click to open)|r")
    else
        call BlzFrameSetText(KKP_c_utit, "|cffffcc00Used in|r  |cff999999no recipe uses this item|r")
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
    call BlzFrameSetText(KKP_c_desc, s)
endfunction

function KKP_des_chefe_lista takes nothing returns nothing
    local integer g=KKP_b_grupo
    local integer n=KKP_gr_qt[g]
    local integer s=1
    local integer k=1
    local integer j
    local boolean achou=false
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
            call KKP_lvis(10000+s, true)
            call BlzFrameSetTexture(LoadFrameHandle(KKP_ht, 10000+s, 3), KKP_ico_chefe(j), 0, true)
            call KKP_lativa(10000+s, KKP_nome_chefe(j)+"|r |cff999999Lv "+I2S(KKP_bs_nivel[j])+"|r", j==KKP_b_sel)
        else
            set KKP_b_lin[s]=0
            call KKP_lvis(10000+s, false)
        endif
        set s=s+1
    endloop
    call BlzFrameSetText(KKP_b_pag, KKP_pagina(KKP_b_top, 11, n))
endfunction

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
    loop
        exitwhen s>12
        set KKP_b_drop[s]=0
        call KKP_vis(KKP_b_dico2[s], false)
        call KKP_vis(KKP_b_dbt[s], false)
        call KKP_vis(KKP_b_dtx[s], false)
        set s=s+1
    endloop
    if not vis then
        call BlzFrameSetText(KKP_b_dnota, KKP_txt_chefes)
        return
    endif
    call BlzFrameSetTexture(KKP_b_dico, KKP_ico_chefe(j), 0, true)
    call BlzFrameSetText(KKP_b_dnome, KKP_nome_chefe(j))
    set t="|cff999999"+KKP_gr_nome[KKP_bs_grupo[j]]+"|r"
    if KKP_bs_nivel[j]>0 then
        set t=t+"  |cffffcc00Level|r "+I2S(KKP_bs_nivel[j])
    endif
    if KKP_bs_vida[j]>0 then
        set t=t+"  |cffffcc00HP|r "+KKP_mil(KKP_bs_vida[j])
    endif
    call BlzFrameSetText(KKP_b_dinfo, t)
    if KKP_bs_nota[j]!=null and KKP_bs_nota[j]!="" then
        call BlzFrameSetText(KKP_b_dnota, KKP_bs_nota[j])
    else
        call BlzFrameSetText(KKP_b_dnota, "")
    endif
    call BlzFrameSetText(KKP_b_dtit, "|cffffcc00Drops|r  "+I2S(KKP_bs_drn[j])+" |cff999999(chance per kill, "+KKP_txt_taxa+")|r")
    set s=1
    loop
        exitwhen s>12 or s>KKP_bs_drn[j]
        set k=KKP_bs_dr[j]+s-1
        set it=KKP_dr_it[k]
        set KKP_b_drop[s]=it
        call BlzFrameSetTexture(KKP_b_dico2[s], KKP_ico_item(it), 0, true)
        call KKP_vis(KKP_b_dico2[s], true)
        call KKP_vis(KKP_b_dbt[s], KKP_idx(it)>0)
        set t=KKP_nome_item(it)+"|r|n"+KKP_taxa_txt(KKP_dr_tipo[k], KKP_dr_taxa[k], pid)
        if KKP_dr_qt[k]>1 then
            set t=t+" x"+I2S(KKP_dr_qt[k])
        endif
        call BlzFrameSetText(KKP_b_dtx[s], t)
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
    local boolean achou=false
    local boolean ok
    local string t
    loop
        exitwhen k>10
        if k<=KKP_ab_subn[a] then
            call KKP_bvis(16000+k, true)
            call KKP_rot(16000+k, KKP_ab_sub[a*16+k], k==sub)
        else
            call KKP_bvis(16000+k, false)
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
    elseif KKP_g_top>n-1 then
        set KKP_g_top=((n-1)/40)*40
    endif
    if KKP_g_top<0 then
        set KKP_g_top=0
    endif
    call KKP_vis(KKP_g_corpo1, lay!=2)
    call KKP_vis(KKP_g_corpo2, lay==2)
    if KKP_g_topo[b]!=null then
        call BlzFrameSetText(KKP_g_topo_tx, KKP_g_topo[b])
    else
        call BlzFrameSetText(KKP_g_topo_tx, "")
    endif
    if lay==2 then
        loop
            exitwhen s>KKP_GL
            set i=KKP_g_top+s-1
            if i<n then
                set e=b*KKP_GE+i
                set KKP_g_lin[s]=i
                call KKP_lvis(20000+s, true)
                call BlzFrameSetTexture(LoadFrameHandle(KKP_ht, 20000+s, 3), KKP_g_ico[e], 0, true)
                if KKP_g_trava[e] then
                    call KKP_lativa(20000+s, "|cff808080"+KKP_g_nome[e]+"|r", i==KKP_g_sel)
                else
                    call KKP_lativa(20000+s, KKP_g_nome[e], i==KKP_g_sel)
                endif
                if KKP_g_info[e]!=null then
                    call BlzFrameSetText(LoadFrameHandle(KKP_ht, 20000+s, 6), KKP_g_info[e])
                else
                    call BlzFrameSetText(LoadFrameHandle(KKP_ht, 20000+s, 6), "")
                endif
            else
                set KKP_g_lin[s]=-1
                call KKP_lvis(20000+s, false)
            endif
            set s=s+1
        endloop
        call BlzFrameSetText(KKP_l_pag, KKP_pagina(KKP_g_top, KKP_GL, n))
    else
        loop
            exitwhen s>40
            set i=KKP_g_top+s-1
            if i<n then
                set e=b*KKP_GE+i
                set KKP_g_lin[s]=i
                call BlzFrameSetTexture(KKP_g_icof[s], KKP_g_ico[e], 0, true)
                call KKP_vis(KKP_g_icof[s], true)
                call KKP_vis(KKP_g_bt[s], true)
                call KKP_vis(KKP_g_dim[s], KKP_g_trava[e])
                call KKP_vis(KKP_g_cur[s], KKP_g_ok[e])
                if i==KKP_g_sel then
                    call BlzFrameClearAllPoints(KKP_g_marca)
                    call BlzFrameSetPoint(KKP_g_marca, FRAMEPOINT_TOPLEFT, KKP_g_icof[s], FRAMEPOINT_TOPLEFT, -0.003, 0.003)
                    call BlzFrameSetPoint(KKP_g_marca, FRAMEPOINT_BOTTOMRIGHT, KKP_g_icof[s], FRAMEPOINT_BOTTOMRIGHT, 0.003, -0.003)
                    set achou=true
                endif
            else
                set KKP_g_lin[s]=-1
                call KKP_vis(KKP_g_icof[s], false)
                call KKP_vis(KKP_g_bt[s], false)
                call KKP_vis(KKP_g_dim[s], false)
                call KKP_vis(KKP_g_cur[s], false)
            endif
            set s=s+1
        endloop
        call KKP_vis(KKP_g_marca, achou)
        call BlzFrameSetText(KKP_g_pag, KKP_pagina(KKP_g_top, 40, n))
    endif
    set i=KKP_g_sel
    if i<0 or i>=n then
        set i=KKP_g_atual[b]
    endif
    set ok=i>=0 and i<n
    if ok then
        set e=b*KKP_GE+i
        call BlzFrameSetTexture(KKP_g_dico, KKP_g_ico[e], 0, true)
        call KKP_vis(KKP_g_dico, true)
        call BlzFrameSetText(KKP_g_dnome, "|cffffcc00"+KKP_g_nome[e]+"|r")
        set t=""
        if KKP_g_trava[e] then
            set t="|cffff5555Locked.|r|n"
        endif
        if KKP_g_edet[e]!=null and KKP_g_edet[e]!="" then
            set t=t+KKP_g_edet[e]
        endif
    else
        set e=0
        call KKP_vis(KKP_g_dico, false)
        call BlzFrameSetText(KKP_g_dnome, "")
        if n>0 then
            set t="|cff999999Pick an entry on the left.|r"
        else
            set t="|cff999999Nothing here yet.|r"
        endif
    endif
    if KKP_g_det[b]!=null and KKP_g_det[b]!="" then
        set t=t+"|n|n"+KKP_g_det[b]
    endif
    call BlzFrameSetText(KKP_g_dtxt, t)
    set k=1
    loop
        exitwhen k>2
        if k==1 then
            set t=KKP_g_b1[b]
        else
            set t=KKP_g_b2[b]
        endif
        if t==null or t=="" then
            call KKP_bvis(17000+k, false)
        elseif KKP_bit(KKP_g_bm[b], k) and not (ok and KKP_bit(KKP_g_eb[e], k)) then
            call KKP_bvis(17000+k, false)
        else
            call BlzFrameSetText(LoadFrameHandle(KKP_ht, 17000+k, 0), t)
            call KKP_bvis(17000+k, true)
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
        set i=i+1
    endloop
endfunction

function KKP_desenha takes boolean detalhe returns nothing
    local integer pid=GetPlayerId(GetLocalPlayer())
    local integer t
    if not KKP_pronto or pid<0 or pid>=KKP_jogadores then
        return
    endif
    if not KKP_aberto[pid] then
        call BlzFrameSetVisible(KKP_raiz, false)
        return
    endif
    call BlzFrameSetVisible(KKP_raiz, true)
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
        call KKP_des_mapa()
    endif
endfunction

function KKP_limpa_busca takes nothing returns nothing
    local string t=BlzFrameGetText(KKP_c_busca)
    set KKP_c_q=""
    set KKP_res_i=0
    call BlzFrameSetFocus(KKP_c_busca, false)
    if t!=null and t!="" then
        set KKP_c_ign=StringCase(t, false)
        set KKP_c_eco=true
        set KKP_c_eco_t=40
        call BlzFrameSetText(KKP_c_busca, "")
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
        set KKP_aberto[pid]=false
    else
        set KKP_aberto[pid]=true
        set KKP_aba[pid]=aba
        call KKP_amostra_aba(pid)
    endif
    if GetLocalPlayer()==p then
        call KKP_desenha(true)
    endif
endfunction

function KKP_vai takes player p,integer aba returns nothing
    local integer pid=GetPlayerId(p)
    if aba<1 or aba>KKP_aba_n then
        return
    endif
    set KKP_aberto[pid]=true
    set KKP_aba[pid]=aba
    call KKP_amostra_aba(pid)
endfunction

function KKP_mostra takes player p,integer aba returns nothing
    local integer pid=GetPlayerId(p)
    if pid<0 or pid>=KKP_jogadores or aba<1 or aba>KKP_aba_n then
        return
    endif
    if not KKP_pronto then
        call DisplayTextToPlayer(p, 0, 0, "|cffffcc00The "+KKP_titulo+" opens a moment after the game starts.|r")
        return
    endif
    call KKP_vai(p, aba)
    if GetLocalPlayer()==p then
        call KKP_desenha(true)
    endif
endfunction

function KKP_mostra_id takes player p,string id returns nothing
    call KKP_mostra(p, KKP_aba_de_id(id))
endfunction

function KKP_tecla takes nothing returns nothing
    local player p=GetTriggerPlayer()
    local oskeytype k=BlzGetTriggerPlayerKey()
    local integer pid=GetPlayerId(p)
    local integer i=1
    if pid<0 or pid>=KKP_jogadores then
        set p=null
        set k=null
        return
    endif
    if k==OSKEY_ESCAPE then
        if KKP_pronto and KKP_aberto[pid] then
            set KKP_aberto[pid]=false
            if GetLocalPlayer()==p then
                call KKP_desenha(false)
            endif
        endif
    else
        loop
            exitwhen i>KKP_aba_n
            if KKP_aba_tecla[i]>0 and k==ConvertOsKeyType(KKP_aba_tecla[i]) then
                call KKP_abre(p, i)
                exitwhen true
            endif
            set i=i+1
        endloop
    endif
    set p=null
    set k=null
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
    endif
endfunction

function KKP_clique takes nothing returns nothing
    local framehandle f=BlzGetTriggerFrame()
    local player p=GetTriggerPlayer()
    local integer pid=GetPlayerId(p)
    local integer c=LoadInteger(KKP_ht, GetHandleId(f), 0)
    local integer g=c/1000
    local integer i=c-g*1000
    local integer x
    if pid<0 or pid>=KKP_jogadores or c<=0 or not KKP_pronto then
        set f=null
        set p=null
        return
    endif
    if GetLocalPlayer()==p then
        call BlzFrameSetEnable(f, false)
        call BlzFrameSetEnable(f, true)
        call BlzFrameSetFocus(KKP_c_busca, false)
    endif
    if g==1 then
        call KKP_vai(p, i)
        if GetLocalPlayer()==p then
            call KKP_desenha(true)
        endif
    elseif g==2 then
        set KKP_aberto[pid]=false
        if GetLocalPlayer()==p then
            call KKP_desenha(false)
        endif
    elseif g==12 then
        set x=KKP_aba_do_tipo(2)
        if x>0 then
            call KKP_vai(p, x)
            if GetLocalPlayer()==p then
                call KKP_abre_item(KKP_idx(KKP_b_drop[i]))
                call KKP_desenha(true)
            endif
        endif
    elseif g!=19 and GetLocalPlayer()==p then
        call KKP_clique_local(g, i)
    endif
    set f=null
    set p=null
endfunction

function KKP_roda takes nothing returns nothing
    local framehandle f=BlzGetTriggerFrame()
    local player p=GetTriggerPlayer()
    local integer pid=GetPlayerId(p)
    local integer c=LoadInteger(KKP_ht, GetHandleId(f), 0)
    local integer g=c/1000
    local integer d=-1
    local integer t
    if BlzGetTriggerFrameValue()<0.0 then
        set d=1
    endif
    if pid>=0 and pid<KKP_jogadores and KKP_pronto and GetLocalPlayer()==p and KKP_aberto[pid] then
        set t=KKP_aba_tipo[KKP_aba[pid]]
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
            if KKP_ab_lay[KKP_aba[pid]*16+KKP_g_sub]==2 then
                set KKP_g_top=KKP_g_top+d
            else
                set KKP_g_top=KKP_g_top+d*40
            endif
            call KKP_des_mapa()
        endif
    endif
    set f=null
    set p=null
endfunction

function KKP_busca_evento takes nothing returns nothing
    local player p=GetTriggerPlayer()
    local integer pid=GetPlayerId(p)
    local string q=BlzGetTriggerFrameText()
    if pid<0 or pid>=KKP_jogadores or not KKP_pronto then
        set p=null
        return
    endif
    if GetLocalPlayer()==p then
        if BlzGetTriggerFrameEvent()==FRAMEEVENT_EDITBOX_ENTER then
            call BlzFrameSetFocus(KKP_c_busca, false)
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
            set KKP_c_q=q
            set KKP_c_top=0
            set KKP_res_n=0
            if q!="" then
                set KKP_res_i=1
            else
                set KKP_res_i=0
            endif
            if KKP_aberto[pid] and KKP_aba_tipo[KKP_aba[pid]]==2 then
                call KKP_des_codex_lista()
            endif
        endif
    endif
    set p=null
endfunction

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
        if GetLocalPlayer()==p then
            set KKP_c_pend=true
            if KKP_aberto[pid] and KKP_aba_tipo[KKP_aba[pid]]==2 then
                call KKP_des_codex_lista()
            endif
        endif
    elseif c=="O" then
        call KKP_abre(p, S2I(SubString(v, 1, StringLength(v))))
    elseif c=="G" then
        set v=SubString(v, 1, StringLength(v))
        set KKP_arg_pid=pid
        set KKP_arg_aba=S2I(KKP_campo(v, 0))
        set KKP_arg_sub=S2I(KKP_campo(v, 1))
        set KKP_arg_i=S2I(KKP_campo(v, 2))
        set KKP_arg_btn=S2I(KKP_campo(v, 3))
        set KKP_arg_ok=false
        if KKP_arg_aba>=1 and KKP_arg_aba<=KKP_aba_n and KKP_aba_tipo[KKP_arg_aba]==4 and KKP_arg_sub>=1 and KKP_arg_sub<=KKP_ab_subn[KKP_arg_aba] and KKP_arg_i>=-1 and KKP_arg_i<KKP_GE and KKP_arg_btn>=1 and KKP_arg_btn<=2 then
            call KKP_chama(KKP_G_APLICA)
            if KKP_aberto[pid] and KKP_aba[pid]==KKP_arg_aba then
                call KKP_amostra_grade(pid)
                if GetLocalPlayer()==p then
                    call KKP_des_mapa()
                endif
            endif
        endif
    endif
    set p=null
endfunction

function KKP_tique1 takes nothing returns nothing
    local integer pid=0
    local integer t
    if not KKP_pronto then
        return
    endif
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
    if pid>=0 and pid<KKP_jogadores and KKP_aberto[pid] then
        set t=KKP_aba_tipo[KKP_aba[pid]]
        if t==1 then
            call KKP_des_ficha(pid)
        elseif t==4 and KKP_g_aba==KKP_aba[pid] then
            call KKP_des_mapa()
        endif
    endif
endfunction

function KKP_tique_local takes nothing returns nothing
    local integer pid
    local integer i
    local integer fim
    if not KKP_pronto then
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
        endif
        return
    endif
    if not KKP_aberto[pid] then
        return
    endif
    if KKP_c_pend and KKP_aba_tipo[KKP_aba[pid]]==2 then
        set KKP_c_pend=false
        call KKP_des_codex_det()
    elseif KKP_b_pend and KKP_aba_tipo[KKP_aba[pid]]==3 then
        set KKP_b_pend=false
        call KKP_des_chefe_det()
    endif
endfunction

function KKP_cria_base takes nothing returns nothing
    local framehandle ui=BlzGetOriginFrame(ORIGIN_FRAME_GAME_UI, 0)
    local integer i=1
    local integer n=0
    local real x=0.100
    local real w
    set KKP_raiz=BlzCreateFrameByType("FRAME", "KKPRaiz", ui, "", 0)
    set KKP_nq=KKP_nq+1
    call BlzFrameSetLevel(KKP_raiz, 6)
    set KKP_caixa=BlzCreateFrame("EscMenuBackdrop", KKP_raiz, 0, 0)
    set KKP_nq=KKP_nq+1
    call KKP_poe(KKP_caixa, 0.08, 0.575, 0.71, 0.44)
    set KKP_fundo=BlzCreateFrameByType("TEXT", "KKPFundo", KKP_raiz, "", 0)
    set KKP_nq=KKP_nq+1
    call KKP_poe(KKP_fundo, 0.08, 0.575, 0.71, 0.44)
    call BlzFrameSetText(KKP_fundo, "")
    call SaveInteger(KKP_ht, GetHandleId(KKP_fundo), 0, 19000)
    call BlzTriggerRegisterFrameEvent(KKP_t_clique, KKP_fundo, FRAMEEVENT_CONTROL_CLICK)
    call BlzTriggerRegisterFrameEvent(KKP_t_roda, KKP_fundo, FRAMEEVENT_MOUSE_WHEEL)
    loop
        exitwhen i>KKP_aba_n
        set n=n+IMaxBJ(StringLength(KKP_aba_nome[i]), 4)
        set i=i+1
    endloop
    set i=1
    loop
        exitwhen i>KKP_aba_n
        set w=(0.635-0.004*I2R(KKP_aba_n))*I2R(IMaxBJ(StringLength(KKP_aba_nome[i]), 4))/I2R(IMaxBJ(n, 1))
        call KKP_btxt(KKP_raiz, KKP_aba_nome[i], x, 0.556, w, 0.028, 1000+i)
        set x=x+w+0.004
        set i=i+1
    endloop
    call KKP_btxt(KKP_raiz, "X", 0.742, 0.556, 0.030, 0.028, 2001)
    set i=1
    loop
        exitwhen i>4
        set KKP_pag[i]=BlzCreateFrameByType("FRAME", "KKPPag", KKP_raiz, "", 0)
        set KKP_nq=KKP_nq+1
        call BlzFrameSetVisible(KKP_pag[i], false)
        set i=i+1
    endloop
    call BlzFrameSetVisible(KKP_raiz, false)
    set ui=null
endfunction

function KKP_cria_ficha takes nothing returns nothing
    local framehandle pg=KKP_pag[1]
    call KKP_caixa_nova(pg, false, 0.100, 0.522, 0.220, 0.357)
    call KKP_caixa_nova(pg, false, 0.325, 0.522, 0.445, 0.357)
    set KKP_f_ico=KKP_img(pg, "ReplaceableTextures\\CommandButtons\\BTNSelectHeroOn.blp", 0.110, 0.512, 0.042, 0.042)
    set KKP_f_nome=KKP_txt(pg, "EscMenuLabelTextTemplate", 0.158, 0.512, 0.156, 0.042)
    set KKP_f_stat=KKP_txt(pg, "EscMenuLabelTextSmallTemplate", 0.110, 0.462, 0.204, 0.292)
    set KKP_f_mapa=BlzCreateFrame("EscMenuTextAreaTemplate", pg, 0, 0)
    if KKP_f_mapa==null then
        set KKP_f_mapa=KKP_txt(pg, "EscMenuLabelTextSmallTemplate", 0.335, 0.512, 0.425, 0.337)
    else
        set KKP_nq=KKP_nq+1
        call KKP_poe(KKP_f_mapa, 0.330, 0.516, 0.435, 0.345)
    endif
    set pg=null
endfunction

function KKP_cria_codex takes nothing returns nothing
    local framehandle pg=KKP_pag[2]
    local integer k=0
    local integer s=1
    local real x
    local real y
    loop
        exitwhen k>KKP_cat_n
        call KKP_linha(pg, 0.100, 0.522-k*0.0262, 0.085, 0.025, 3000+k, false, false)
        set k=k+1
    endloop
    set KKP_c_busca=BlzCreateFrameByType("EDITBOX", "KKPBusca", pg, "EscMenuEditBoxTemplate", 0)
    set KKP_nq=KKP_nq+1
    call KKP_poe(KKP_c_busca, 0.190, 0.525, 0.172, 0.030)
    call BlzFrameSetTextSizeLimit(KKP_c_busca, 30)
    call BlzFrameSetText(KKP_c_busca, "")
    call BlzTriggerRegisterFrameEvent(KKP_t_busca, KKP_c_busca, FRAMEEVENT_EDITBOX_TEXT_CHANGED)
    call BlzTriggerRegisterFrameEvent(KKP_t_busca, KKP_c_busca, FRAMEEVENT_EDITBOX_ENTER)
    call KKP_btxt(pg, "X", 0.365, 0.524, 0.028, 0.028, 6006)
    set KKP_c_btxt=KKP_txt(pg, "EscMenuLabelTextSmallTemplate", 0.190, 0.492, 0.205, 0.014)
    loop
        exitwhen s>11
        call KKP_linha(pg, 0.190, 0.476-(s-1)*0.0255, 0.205, 0.025, 4000+s, true, false)
        set s=s+1
    endloop
    call KKP_btxt(pg, "<", 0.190, 0.193, 0.030, 0.024, 5001)
    set KKP_c_pag=KKP_txt(pg, "EscMenuLabelTextSmallTemplate", 0.222, 0.193, 0.141, 0.024)
    call BlzFrameSetTextAlignment(KKP_c_pag, TEXT_JUSTIFY_MIDDLE, TEXT_JUSTIFY_CENTER)
    call KKP_btxt(pg, ">", 0.365, 0.193, 0.030, 0.024, 5002)
    call KKP_caixa_nova(pg, false, 0.400, 0.522, 0.370, 0.357)
    set KKP_c_dico=KKP_img(pg, "ReplaceableTextures\\CommandButtons\\BTNSelectHeroOn.blp", 0.408, 0.514, 0.036, 0.036)
    set KKP_c_dnome=KKP_txt(pg, "EscMenuLabelTextTemplate", 0.450, 0.514, 0.314, 0.020)
    set KKP_c_dsub=KKP_txt(pg, "EscMenuLabelTextSmallTemplate", 0.450, 0.493, 0.150, 0.014)
    call KKP_btxt(pg, "Favorite", 0.674, 0.496, 0.090, 0.024, 6003)
    set KKP_c_rtit=KKP_txt(pg, "EscMenuLabelTextSmallTemplate", 0.408, 0.468, 0.356, 0.014)
    set s=1
    loop
        exitwhen s>8
        set x=0.408+(s-1)*0.0355
        set KKP_c_rico[s]=KKP_img(pg, "ReplaceableTextures\\CommandButtons\\BTNSelectHeroOn.blp", x, 0.452, 0.030, 0.030)
        set KKP_c_rok[s]=KKP_img(pg, "UI\\Widgets\\EscMenu\\Human\\checkbox-check.blp", x+0.017, 0.455, 0.014, 0.014)
        set KKP_c_rqt[s]=KKP_txt(pg, "EscMenuLabelTextSmallTemplate", x-0.003, 0.420, 0.036, 0.011)
        call BlzFrameSetTextAlignment(KKP_c_rqt[s], TEXT_JUSTIFY_TOP, TEXT_JUSTIFY_CENTER)
        set KKP_c_rbt[s]=KKP_bt(pg, x, 0.452, 0.030, 0.030, 7000+s, false)
        set s=s+1
    endloop
    set KKP_c_utit=KKP_txt(pg, "EscMenuLabelTextSmallTemplate", 0.408, 0.404, 0.356, 0.014)
    call KKP_btxt(pg, "<", 0.406, 0.389, 0.020, 0.030, 6004)
    set s=1
    loop
        exitwhen s>6
        set x=0.430+(s-1)*0.0355
        set KKP_c_uico[s]=KKP_img(pg, "ReplaceableTextures\\CommandButtons\\BTNSelectHeroOn.blp", x, 0.389, 0.030, 0.030)
        set KKP_c_ubt[s]=KKP_bt(pg, x, 0.389, 0.030, 0.030, 8000+s, true)
        set s=s+1
    endloop
    call KKP_btxt(pg, ">", 0.645, 0.389, 0.020, 0.030, 6005)
    set KKP_c_desc=BlzCreateFrame("EscMenuTextAreaTemplate", pg, 0, 0)
    if KKP_c_desc==null then
        set KKP_c_desc=KKP_txt(pg, "EscMenuLabelTextSmallTemplate", 0.408, 0.352, 0.356, 0.180)
    else
        set KKP_nq=KKP_nq+1
        call KKP_poe(KKP_c_desc, 0.404, 0.354, 0.362, 0.186)
    endif
    set pg=null
endfunction

function KKP_cria_chefes takes nothing returns nothing
    local framehandle pg=KKP_pag[3]
    local integer s=1
    local integer c
    local integer r
    local real x
    local real y
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
    call KKP_btxt(pg, "<", 0.100, 0.193, 0.030, 0.024, 11001)
    set KKP_b_pag=KKP_txt(pg, "EscMenuLabelTextSmallTemplate", 0.132, 0.193, 0.228, 0.024)
    call BlzFrameSetTextAlignment(KKP_b_pag, TEXT_JUSTIFY_MIDDLE, TEXT_JUSTIFY_CENTER)
    call KKP_btxt(pg, ">", 0.362, 0.193, 0.030, 0.024, 11002)
    call KKP_caixa_nova(pg, false, 0.400, 0.522, 0.370, 0.357)
    set KKP_b_dico=KKP_img(pg, "ReplaceableTextures\\CommandButtons\\BTNSelectHeroOn.blp", 0.408, 0.514, 0.040, 0.040)
    set KKP_b_dnome=KKP_txt(pg, "EscMenuLabelTextTemplate", 0.454, 0.514, 0.310, 0.020)
    set KKP_b_dinfo=KKP_txt(pg, "EscMenuLabelTextSmallTemplate", 0.454, 0.493, 0.310, 0.020)
    set KKP_b_dnota=KKP_txt(pg, "EscMenuLabelTextSmallTemplate", 0.408, 0.470, 0.356, 0.046)
    call KKP_btxt(pg, "Show on map", 0.648, 0.420, 0.116, 0.024, 13001)
    set KKP_b_dtit=KKP_txt(pg, "EscMenuLabelTextSmallTemplate", 0.408, 0.414, 0.238, 0.026)
    set s=1
    loop
        exitwhen s>12
        set c=(s-1)/6
        set r=(s-1)-c*6
        set x=0.408+c*0.181
        set y=0.386-r*0.0362
        set KKP_b_dico2[s]=KKP_img(pg, "ReplaceableTextures\\CommandButtons\\BTNSelectHeroOn.blp", x, y, 0.030, 0.030)
        set KKP_b_dtx[s]=KKP_txt(pg, "EscMenuLabelTextSmallTemplate", x+0.034, y+0.001, 0.145, 0.032)
        set KKP_b_dbt[s]=KKP_bt(pg, x, y, 0.030, 0.030, 12000+s, false)
        set s=s+1
    endloop
    set pg=null
endfunction

function KKP_cria_mapa takes nothing returns nothing
    local framehandle pg=KKP_pag[4]
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
    set KKP_g_topo_tx=KKP_txt(pg, "EscMenuLabelTextSmallTemplate", 0.100, 0.466, 0.670, 0.030)
    set KKP_g_corpo1=BlzCreateFrameByType("FRAME", "KKPCorpo", pg, "", 0)
    set KKP_nq=KKP_nq+1
    set KKP_g_marca=KKP_img(KKP_g_corpo1, "UI\\Widgets\\Console\\Human\\CommandButton\\human-activebutton.blp", 0.097, 0.435, 0.040, 0.040)
    call BlzFrameSetVisible(KKP_g_marca, false)
    set s=1
    loop
        exitwhen s>40
        set c=ModuloInteger(s-1, 8)
        set r=(s-1)/8
        set x=0.100+c*0.0375
        set y=0.432-r*0.0375
        set KKP_g_icof[s]=KKP_img(KKP_g_corpo1, "ReplaceableTextures\\CommandButtons\\BTNSelectHeroOn.blp", x, y, 0.034, 0.034)
        set KKP_g_dim[s]=KKP_img(KKP_g_corpo1, "Textures\\Black32.blp", x, y, 0.034, 0.034)
        call BlzFrameSetAlpha(KKP_g_dim[s], 170)
        set KKP_g_cur[s]=KKP_img(KKP_g_corpo1, "UI\\Widgets\\EscMenu\\Human\\checkbox-check.blp", x+0.019, y-0.019, 0.015, 0.015)
        set KKP_g_bt[s]=KKP_bt(KKP_g_corpo1, x, y, 0.034, 0.034, 14000+s, true)
        set s=s+1
    endloop
    call KKP_btxt(KKP_g_corpo1, "<", 0.100, 0.236, 0.030, 0.024, 15001)
    set KKP_g_pag=KKP_txt(KKP_g_corpo1, "EscMenuLabelTextSmallTemplate", 0.132, 0.236, 0.200, 0.024)
    call BlzFrameSetTextAlignment(KKP_g_pag, TEXT_JUSTIFY_MIDDLE, TEXT_JUSTIFY_CENTER)
    call KKP_btxt(KKP_g_corpo1, ">", 0.334, 0.236, 0.030, 0.024, 15002)
    set KKP_g_corpo2=BlzCreateFrameByType("FRAME", "KKPCorpo", pg, "", 0)
    set KKP_nq=KKP_nq+1
    set s=1
    loop
        exitwhen s>KKP_GL
        call KKP_linha(KKP_g_corpo2, 0.100, 0.432-(s-1)*0.0255, 0.298, 0.025, 20000+s, true, true)
        set s=s+1
    endloop
    call KKP_btxt(KKP_g_corpo2, "<", 0.100, 0.193, 0.030, 0.024, 21001)
    set KKP_l_pag=KKP_txt(KKP_g_corpo2, "EscMenuLabelTextSmallTemplate", 0.132, 0.193, 0.234, 0.024)
    call BlzFrameSetTextAlignment(KKP_l_pag, TEXT_JUSTIFY_MIDDLE, TEXT_JUSTIFY_CENTER)
    call KKP_btxt(KKP_g_corpo2, ">", 0.368, 0.193, 0.030, 0.024, 21002)
    call KKP_caixa_nova(pg, false, 0.405, 0.438, 0.365, 0.273)
    set KKP_g_dico=KKP_img(pg, "ReplaceableTextures\\CommandButtons\\BTNSelectHeroOn.blp", 0.413, 0.430, 0.040, 0.040)
    set KKP_g_dnome=KKP_txt(pg, "EscMenuLabelTextTemplate", 0.459, 0.430, 0.305, 0.040)
    set KKP_g_dtxt=KKP_txt(pg, "EscMenuLabelTextSmallTemplate", 0.413, 0.382, 0.351, 0.150)
    call KKP_btxt(pg, "", 0.413, 0.200, 0.170, 0.026, 17001)
    call KKP_btxt(pg, "", 0.590, 0.200, 0.170, 0.026, 17002)
    set pg=null
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

function KKP_espera takes nothing returns nothing
    if KKP_iniciado then
        call PauseTimer(GetExpiredTimer())
        return
    endif
    set KKP_iniciado=true
    call PauseTimer(GetExpiredTimer())
    call ExecuteFunc("KKP_cria_base")
    call ExecuteFunc("KKP_cria_ficha")
    call ExecuteFunc("KKP_cria_codex")
    call ExecuteFunc("KKP_cria_chefes")
    call ExecuteFunc("KKP_cria_mapa")
    set KKP_pronto=KKP_raiz!=null and KKP_c_desc!=null and KKP_g_dtxt!=null and KKP_f_mapa!=null
endfunction

function KKP_init takes nothing returns nothing
    local integer i=1
    local integer a
    set KKP_ht=InitHashtable()
    call KKP_dados_todos()
    call ExecuteFunc("KKP_carga_indice")
    set KKP_carga_k=1
    loop
        exitwhen KKP_carga_k>KKP_it_n
        call ExecuteFunc("KKP_carga_busca")
        set KKP_carga_k=KKP_carga_k+120
    endloop
    if KKP_toc!=null and KKP_toc!="" then
        call BlzLoadTOCFile(KKP_toc)
    endif
    set KKP_t_clique=CreateTrigger()
    call TriggerAddAction(KKP_t_clique, function KKP_clique)
    set KKP_t_roda=CreateTrigger()
    call TriggerAddAction(KKP_t_roda, function KKP_roda)
    set KKP_t_busca=CreateTrigger()
    call TriggerAddAction(KKP_t_busca, function KKP_busca_evento)
    set KKP_t_tecla=CreateTrigger()
    call TriggerAddAction(KKP_t_tecla, function KKP_tecla)
    set KKP_t_sync=CreateTrigger()
    call TriggerAddAction(KKP_t_sync, function KKP_sync)
    set i=0
    loop
        exitwhen i>=KKP_jogadores
        set a=1
        loop
            exitwhen a>KKP_aba_n
            if KKP_aba_tecla[a]>0 then
                call BlzTriggerRegisterPlayerKeyEvent(KKP_t_tecla, Player(i), ConvertOsKeyType(KKP_aba_tecla[a]), 0, false)
            endif
            set a=a+1
        endloop
        call BlzTriggerRegisterPlayerKeyEvent(KKP_t_tecla, Player(i), OSKEY_ESCAPE, 0, false)
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
