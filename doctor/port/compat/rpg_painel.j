//@GLOBALS
integer array RPGP_passo
unit array RPGP_heroi
trigger RPGP_t_mapa_grade=null
trigger RPGP_t_mapa_aplica=null
//@ENDGLOBALS

function RPGP_consumivel takes integer id returns nothing
    call SaveBoolean(RPGM_ht, -10, id, true)
endfunction

function RPGP_e_consumivel takes integer id returns boolean
    return LoadBoolean(RPGM_ht, -10, id)
endfunction

function RPGP_mapa_grade takes code f returns nothing
    call TriggerAddCondition(RPGP_t_mapa_grade, Condition(f))
endfunction

function RPGP_mapa_aplica takes code f returns nothing
    call TriggerAddCondition(RPGP_t_mapa_aplica, Condition(f))
endfunction

function RPGP_pct takes real r returns string
    return I2S(R2I(r*1000.0+0.5)/10)+"."+I2S(ModuloInteger(R2I(r*1000.0+0.5), 10))+"%"
endfunction

function RPGP_ficha takes nothing returns boolean
    local integer pid=KKP_arg_pid
    local unit h=RPGP_heroi[pid]
    local string s
    local integer i=0
    local integer id
    set KKP_heroi[pid]=h
    set KKP_mult[pid]=RPGM_mult[pid]
    call FlushChildHashtable(KKP_ht, 930000+pid)
    loop
        exitwhen i>=RPGM_n[pid]
        set id=RPGM_id_em(pid, i)
        call SaveInteger(KKP_ht, 930000+pid, id, RPGM_qtd(pid, id))
        set i=i+1
    endloop
    set s="|cffffcc00Gold:|r "+RPGD_curto(I2R(GetPlayerState(Player(pid), PLAYER_STATE_RESOURCE_GOLD)))
    if h!=null then
        set s=s+"|n|cffffcc00Attribute points:|r "+I2S(RPGT_livres(pid, h))+" free"
        set s=s+"|n|cffffcc00Paragon:|r "+I2S(RPGT_par_n[pid])+" ("+I2S(RPGT_par_livres(pid))+" free)"
        set s=s+"|n|n|cffffcc00Skill damage:|r +"+RPGP_pct(RPGD_bonus(h, RPGD_S_SKILL))
        set s=s+"|n|cffffcc00Healing:|r +"+RPGP_pct(RPGD_bonus(h, RPGD_S_CURA))
        set s=s+"|n|cffffcc00Critical:|r "+RPGP_pct(RPGD_crit_base+RPGD_bonus(h, RPGD_S_CRIT))+" for x"+R2SW(RPGD_critx_base+RPGD_bonus(h, RPGD_S_CRITX), 1, 1)
        set s=s+"|n|cffffcc00Defense:|r "+RPGD_curto(RPGD_bonus(h, RPGD_S_DEF))+" ("+RPGP_pct(RPGD_reducao(h, GetHeroLevel(h)))+" vs. your level)"
        set s=s+"|n|cffffcc00Damage reduction:|r "+RPGP_pct(RPGD_bonus(h, RPGD_S_RED))
        set s=s+"|n|cffffcc00Dodge:|r "+RPGP_pct(RPGD_bonus(h, RPGD_S_ESQ))
        set s=s+"|n|cffffcc00Attack speed bonus:|r +"+RPGP_pct(RPGD_bonus(h, RPGD_S_VEL))
    endif
    set KKP_x_mapa[pid]=s
    set h=null
    return false
endfunction

function RPGP_limpa takes integer b returns nothing
    set KKP_g_n[b]=0
    set KKP_g_atual[b]=-1
    set KKP_g_topo[b]=""
    set KKP_g_det[b]=""
    set KKP_g_b1[b]=""
    set KKP_g_b2[b]=""
    set KKP_g_bm[b]=0
endfunction

function RPGP_poe takes integer b, string nome, string ico, string info, string det, integer eb, integer val returns nothing
    local integer e=b*KKP_GE+KKP_g_n[b]
    if KKP_g_n[b]>=KKP_GE then
        return
    endif
    set KKP_g_nome[e]=nome
    set KKP_g_ico[e]=ico
    set KKP_g_info[e]=info
    set KKP_g_edet[e]=det
    set KKP_g_trava[e]=false
    set KKP_g_ok[e]=false
    set KKP_g_eb[e]=eb
    set KKP_g_val[e]=val
    set KKP_g_n[b]=KKP_g_n[b]+1
endfunction

function RPGP_passo_de takes integer pid returns integer
    if RPGP_passo[pid]<1 then
        set RPGP_passo[pid]=1
    endif
    return RPGP_passo[pid]
endfunction

function RPGP_pontos takes integer pid returns nothing
    local unit h=RPGP_heroi[pid]
    local integer b=pid*16+1
    local integer p=RPGP_passo_de(pid)
    call RPGP_limpa(b)
    set KKP_g_topo[b]="|cffffcc00"+I2S(RPGT_livres(pid, h))+"|r free points  |cff999999(each level gives "+I2S(RPGT_por_nivel)+")|r"
    set KKP_g_b1[b]="+"+I2S(p)
    set KKP_g_b2[b]="Step: "+I2S(p)
    set KKP_g_bm[b]=1
    if h!=null then
        call RPGP_poe(b, "Strength", "ReplaceableTextures\\CommandButtons\\BTNGauntletsOfOgrePower.blp", I2S(GetHeroStr(h, false))+" (+"+I2S(RPGT_gasto[pid*4+1])+")", "Health, health regeneration and physical damage.", 1, 1)
        call RPGP_poe(b, "Agility", "ReplaceableTextures\\CommandButtons\\BTNSlippersOfAgility.blp", I2S(GetHeroAgi(h, false))+" (+"+I2S(RPGT_gasto[pid*4+2])+")", "Attack speed, critical strike and dodge.", 1, 2)
        call RPGP_poe(b, "Intelligence", "ReplaceableTextures\\CommandButtons\\BTNMantleOfIntelligence.blp", I2S(GetHeroInt(h, false))+" (+"+I2S(RPGT_gasto[pid*4+3])+")", "Mana, mana regeneration and spell power.", 1, 3)
    endif
    set b=pid*16+2
    call RPGP_limpa(b)
    set KKP_g_topo[b]="|cffffcc00"+I2S(RPGT_par_livres(pid))+"|r free paragon points  |cff999999(paragon level "+I2S(RPGT_par_n[pid])+")|r"
    set KKP_g_b1[b]="+"+I2S(p)
    set KKP_g_b2[b]="Step: "+I2S(p)
    set KKP_g_bm[b]=1
    call RPGP_poe(b, "Primary attribute", "ReplaceableTextures\\CommandButtons\\BTNAdvancedStrengthOfTheMoon.blp", "+"+RPGP_pct(RPGT_par_pct(pid, 1)), "+"+RPGP_pct(RPGT_par_prim)+" per point.", 1, 1)
    call RPGP_poe(b, "Skill damage and healing", "ReplaceableTextures\\CommandButtons\\BTNSpellBookBLS.blp", "+"+RPGP_pct(RPGT_par_pct(pid, 2)), "+"+RPGP_pct(RPGT_par_skill)+" per point.", 1, 2)
    call RPGP_poe(b, "Health", "ReplaceableTextures\\CommandButtons\\BTNPeriapt.blp", "+"+RPGP_pct(RPGT_par_pct(pid, 3)), "+"+RPGP_pct(RPGT_par_vida)+" per point.", 1, 3)
    call RPGP_poe(b, "Damage reduction", "ReplaceableTextures\\CommandButtons\\BTNDefend.blp", "+"+RPGP_pct(RPGT_par_pct(pid, 4)), "+"+RPGP_pct(RPGT_par_red)+" per point, up to "+RPGP_pct(RPGT_par_red_teto)+".", 1, 4)
    set b=pid*16+3
    call RPGP_limpa(b)
    set KKP_g_topo[b]="Reset all attribute points for "+I2S(RPGT_reset_ouro)+" gold."
    set KKP_g_b1[b]="Reset"
    set KKP_g_bm[b]=0
    set h=null
endfunction

function RPGP_mochila takes integer pid returns nothing
    local integer b=pid*16+1
    local integer i=0
    local integer id
    local integer eb
    call RPGP_limpa(b)
    set KKP_g_topo[b]="|cffffcc00Backpack|r  |cff999999(materials, components and potions; no slot limit)|r"
    set KKP_g_b1[b]="Use"
    set KKP_g_bm[b]=1
    loop
        exitwhen i>=RPGM_n[pid]
        set id=RPGM_id_em(pid, i)
        if RPGM_qtd(pid, id)>0 then
            set eb=0
            if RPGP_e_consumivel(id) then
                set eb=1
            endif
            call RPGP_poe(b, GetObjectName(id), KKP_ico_item(id), "x"+I2S(RPGM_qtd(pid, id)), BlzGetAbilityExtendedTooltip(id, 0), eb, id)
        endif
        set i=i+1
    endloop
endfunction

function RPGP_grade takes nothing returns boolean
    local string id=KKP_aba_id[KKP_arg_aba]
    if id=="pontos" then
        call RPGP_pontos(KKP_arg_pid)
    elseif id=="mochila" then
        call RPGP_mochila(KKP_arg_pid)
    else
        call TriggerEvaluate(RPGP_t_mapa_grade)
    endif
    return false
endfunction

function RPGP_aplica takes nothing returns boolean
    local integer pid=KKP_arg_pid
    local string id=KKP_aba_id[KKP_arg_aba]
    local integer b=pid*16+KKP_arg_sub
    local boolean tem=KKP_arg_i>=0 and KKP_arg_i<KKP_g_n[b]
    local integer v=0
    local unit h=RPGP_heroi[pid]
    if tem then
        set v=KKP_g_val[b*KKP_GE+KKP_arg_i]
    endif
    set KKP_arg_ok=false
    if id=="pontos" then
        if KKP_arg_btn==2 and KKP_arg_sub<=2 then
            if RPGP_passo_de(pid)==1 then
                set RPGP_passo[pid]=10
            elseif RPGP_passo[pid]==10 then
                set RPGP_passo[pid]=100
            else
                set RPGP_passo[pid]=1
            endif
            set KKP_arg_ok=true
        elseif KKP_arg_btn==1 and KKP_arg_sub==1 and tem then
            set KKP_arg_ok=RPGT_aloca(pid, h, v, RPGP_passo_de(pid))>0
        elseif KKP_arg_btn==1 and KKP_arg_sub==2 and tem then
            set KKP_arg_ok=RPGT_par_aloca(pid, h, v, RPGP_passo_de(pid))>0
        elseif KKP_arg_btn==1 and KKP_arg_sub==3 then
            set KKP_arg_ok=RPGT_reseta(pid, h)
        endif
    elseif id=="mochila" then
        if KKP_arg_btn==1 and tem and RPGP_e_consumivel(v) then
            set KKP_arg_ok=RPGM_usa(pid, v)
        endif
    else
        call TriggerEvaluate(RPGP_t_mapa_aplica)
    endif
    set h=null
    return false
endfunction

function RPGP_craft takes nothing returns boolean
    local integer pid=KKP_arg_pid
    local integer r=RPGK_de(KKP_arg_item)
    set KKP_arg_ok=false
    if r>0 and RPGP_heroi[pid]!=null then
        set KKP_arg_ok=RPGK_faz(pid, RPGP_heroi[pid], r)!=null
    endif
    return false
endfunction

function RPGP_init takes nothing returns nothing
    if RPGP_t_mapa_grade!=null then
        return
    endif
    set RPGP_t_mapa_grade=CreateTrigger()
    set RPGP_t_mapa_aplica=CreateTrigger()
    call KKP_init()
    call KKP_gancho(KKP_G_FICHA, function RPGP_ficha)
    call KKP_gancho(KKP_G_GRADE, function RPGP_grade)
    call KKP_gancho(KKP_G_APLICA, function RPGP_aplica)
    call KKP_gancho(KKP_G_CRAFT, function RPGP_craft)
endfunction
