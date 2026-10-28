//@GLOBALS
constant integer RPGZ_CORPO=1
constant integer RPGZ_AURA=2
constant integer RPGZ_ASA=3
constant integer RPGZ_PE=4
constant integer RPGZ_RASTRO=5
constant integer RPGZ_NT=5
constant integer RPGZ_MAX=400
integer RPGZ_jogadores=12
string RPGZ_aba="skins"
string RPGZ_ico_padrao="ReplaceableTextures\\CommandButtons\\BTNSpellBookBLS.blp"
integer RPGZ_n=0
integer array RPGZ_k_sub
integer array RPGZ_k_tipo
integer array RPGZ_k_unid
string array RPGZ_k_modelo
string array RPGZ_k_ponto
real array RPGZ_k_escala
string array RPGZ_k_nome
string array RPGZ_k_ico
string array RPGZ_k_chave
integer array RPGZ_sel
effect array RPGZ_fx
boolean array RPGZ_fx_vivo
unit array RPGZ_heroi
timer RPGZ_tm=null
boolean RPGZ_pronto=false
//@ENDGLOBALS

function RPGZ_skin takes integer sub, integer tipo, integer unid, string modelo, string ponto, real escala, string nome, string ico, string chave returns integer
    if RPGZ_n>=RPGZ_MAX-1 then
        return 0
    endif
    set RPGZ_n=RPGZ_n+1
    set RPGZ_k_sub[RPGZ_n]=sub
    set RPGZ_k_tipo[RPGZ_n]=tipo
    set RPGZ_k_unid[RPGZ_n]=unid
    set RPGZ_k_modelo[RPGZ_n]=modelo
    set RPGZ_k_ponto[RPGZ_n]=ponto
    set RPGZ_k_escala[RPGZ_n]=escala
    set RPGZ_k_nome[RPGZ_n]=nome
    set RPGZ_k_ico[RPGZ_n]=ico
    set RPGZ_k_chave[RPGZ_n]=chave
    return RPGZ_n
endfunction

function RPGZ_vivo takes unit h returns boolean
    return h!=null and GetUnitTypeId(h)!=0 and not IsUnitType(h, UNIT_TYPE_DEAD)
endfunction

function RPGZ_corpo takes unit h, integer alvo, real escala returns nothing
    local boolean dist=IsUnitType(h, UNIT_TYPE_RANGED_ATTACKER)
    local string art=null
    local real vel=0.0
    local real arco=0.0
    if dist then
        set art=BlzGetUnitWeaponStringField(h, UNIT_WEAPON_SF_ATTACK_PROJECTILE_ART, 0)
        set vel=BlzGetUnitWeaponRealField(h, UNIT_WEAPON_RF_ATTACK_PROJECTILE_SPEED, 0)
        set arco=BlzGetUnitWeaponRealField(h, UNIT_WEAPON_RF_ATTACK_PROJECTILE_ARC, 0)
    endif
    call BlzSetUnitSkin(h, alvo)
    call SetUnitScale(h, escala, escala, escala)
    if dist then
        if art!=null and art!="" then
            call BlzSetUnitWeaponStringField(h, UNIT_WEAPON_SF_ATTACK_PROJECTILE_ART, 0, art)
        endif
        if vel>0.0 then
            call BlzSetUnitWeaponRealField(h, UNIT_WEAPON_RF_ATTACK_PROJECTILE_SPEED, 0, vel)
        endif
        if arco>0.0 then
            call BlzSetUnitWeaponRealField(h, UNIT_WEAPON_RF_ATTACK_PROJECTILE_ARC, 0, arco)
        endif
    endif
endfunction

function RPGZ_tira takes integer pid, integer tipo returns nothing
    local integer i=pid*8+tipo
    local unit h=RPGZ_heroi[pid]
    if tipo==RPGZ_CORPO then
        if RPGZ_sel[i]!=0 and RPGZ_vivo(h) then
            call RPGZ_corpo(h, GetUnitTypeId(h), 1.0)
        endif
    elseif RPGZ_fx[i]!=null then
        call DestroyEffect(RPGZ_fx[i])
        set RPGZ_fx[i]=null
    endif
    set RPGZ_sel[i]=0
    set h=null
endfunction

function RPGZ_veste takes integer pid, integer k returns boolean
    local integer tipo
    local integer i
    local unit h=RPGZ_heroi[pid]
    if k<1 or k>RPGZ_n or h==null or GetUnitTypeId(h)==0 then
        set h=null
        return false
    endif
    set tipo=RPGZ_k_tipo[k]
    set i=pid*8+tipo
    if tipo!=RPGZ_CORPO then
        call RPGZ_tira(pid, tipo)
        set RPGZ_fx[i]=AddSpecialEffectTarget(RPGZ_k_modelo[k], h, RPGZ_k_ponto[k])
        set RPGZ_fx_vivo[i]=RPGZ_vivo(h)
    else
        call RPGZ_corpo(h, RPGZ_k_unid[k], RPGZ_k_escala[k])
    endif
    set RPGZ_sel[i]=k
    set h=null
    return true
endfunction

function RPGZ_por_chave takes string c returns integer
    local integer k=1
    loop
        exitwhen k>RPGZ_n
        if RPGZ_k_chave[k]==c then
            return k
        endif
        set k=k+1
    endloop
    return 0
endfunction

function RPGZ_grade takes nothing returns boolean
    local integer pid=KKP_arg_pid
    local integer s
    local integer b
    local integer k
    local string info
    if KKP_aba_id[KKP_arg_aba]!=RPGZ_aba then
        return false
    endif
    set s=1
    loop
        exitwhen s>15
        set b=pid*16+s
        call RPGP_limpa(b)
        set KKP_g_topo[b]="|cffffcc00Skins|r  |cff999999(looks only; free; saved with your hero)|r"
        set KKP_g_b1[b]="Wear"
        set KKP_g_b2[b]="Remove"
        set KKP_g_bm[b]=1
        set s=s+1
    endloop
    set k=1
    loop
        exitwhen k>RPGZ_n
        set b=pid*16+RPGZ_k_sub[k]
        set info=""
        if RPGZ_sel[pid*8+RPGZ_k_tipo[k]]==k then
            set info="|cff80ff80worn|r"
        endif
        if RPGZ_k_ico[k]!="" then
            call RPGP_poe(b, RPGZ_k_nome[k], RPGZ_k_ico[k], info, "", 1, k)
        else
            call RPGP_poe(b, RPGZ_k_nome[k], RPGZ_ico_padrao, info, "", 1, k)
        endif
        set k=k+1
    endloop
    return false
endfunction

function RPGZ_aplica takes nothing returns boolean
    local integer pid=KKP_arg_pid
    local integer b=pid*16+KKP_arg_sub
    local integer k=0
    if KKP_aba_id[KKP_arg_aba]!=RPGZ_aba then
        return false
    endif
    if KKP_arg_i>=0 and KKP_arg_i<KKP_g_n[b] then
        set k=KKP_g_val[b*KKP_GE+KKP_arg_i]
    endif
    if k<1 or k>RPGZ_n then
        set KKP_arg_ok=false
        return false
    endif
    if KKP_arg_btn==1 then
        set KKP_arg_ok=RPGZ_veste(pid, k)
    elseif KKP_arg_btn==2 then
        call RPGZ_tira(pid, RPGZ_k_tipo[k])
        set KKP_arg_ok=true
    endif
    return false
endfunction

function RPGZ_grava takes nothing returns boolean
    local integer pid=RPGS_ev_pid
    local integer t=1
    loop
        exitwhen t>RPGZ_NT
        if RPGZ_sel[pid*8+t]!=0 then
            call RPGS_poe_s("z"+I2S(t), RPGZ_k_chave[RPGZ_sel[pid*8+t]])
        endif
        set t=t+1
    endloop
    return false
endfunction

function RPGZ_nasce takes nothing returns boolean
    local integer pid=RPGH_ev_pid
    local integer t=1
    local integer k
    loop
        exitwhen t>RPGZ_NT
        if RPGZ_fx[pid*8+t]!=null then
            call DestroyEffect(RPGZ_fx[pid*8+t])
            set RPGZ_fx[pid*8+t]=null
        endif
        set RPGZ_sel[pid*8+t]=0
        set t=t+1
    endloop
    set RPGZ_heroi[pid]=RPGH_ev_u
    if RPGS_ev_ok then
        set t=1
        loop
            exitwhen t>RPGZ_NT
            if RPGS_tem(pid, "z"+I2S(t)) then
                set k=RPGZ_por_chave(RPGS_le_s(pid, "z"+I2S(t)))
                if k>0 then
                    call RPGZ_veste(pid, k)
                endif
            endif
            set t=t+1
        endloop
    endif
    return false
endfunction

function RPGZ_tiq takes nothing returns nothing
    local integer pid=0
    local integer t
    local integer i
    local boolean v
    loop
        exitwhen pid>=RPGZ_jogadores
        set v=RPGZ_vivo(RPGZ_heroi[pid])
        set t=RPGZ_AURA
        loop
            exitwhen t>RPGZ_NT
            set i=pid*8+t
            if RPGZ_sel[i]!=0 then
                if v and not RPGZ_fx_vivo[i] then
                    call RPGZ_veste(pid, RPGZ_sel[i])
                elseif not v then
                    set RPGZ_fx_vivo[i]=false
                endif
            endif
            set t=t+1
        endloop
        set pid=pid+1
    endloop
endfunction

function RPGZ_init takes nothing returns nothing
    if RPGZ_pronto then
        return
    endif
    set RPGZ_pronto=true
    call RPGP_mapa_grade(function RPGZ_grade)
    call RPGP_mapa_aplica(function RPGZ_aplica)
    call RPGS_gancho(RPGS_G_GRAVA, function RPGZ_grava)
    call RPGH_gancho(RPGH_G_NASCE, function RPGZ_nasce)
    set RPGZ_tm=CreateTimer()
    call TimerStart(RPGZ_tm, 1.0, true, function RPGZ_tiq)
endfunction
