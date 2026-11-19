//@REQUER KK:kk_painel.j
//@GLOBALS
constant integer KKZ_CORPO=1
constant integer KKZ_ASA=2
constant integer KKZ_AURA=3
constant integer KKZ_RASTRO=4
constant integer KKZ_PROJETIL=5
constant integer KKZ_PEGADA=6
constant integer KKZ_NT=6
constant integer KKZ_MAX=400
constant integer KKZ_PEGADAS=8
constant real KKZ_PASSO=0.25
constant real KKZ_PASSO_D=70.
integer KKZ_jogadores=12
string KKZ_aba="skins"
string KKZ_ico_padrao="ReplaceableTextures\\CommandButtons\\BTNSpellBookBLS.blp"
string KKZ_topo="|cffffcc00Skins|r  |cff999999(looks only; free; saved with your character)|r"
integer array KKZ_sub_de
string array KKZ_nome_tipo
integer KKZ_n=0
integer KKZ_fora=0
integer array KKZ_k_tipo
integer array KKZ_k_unid
string array KKZ_k_modelo
string array KKZ_k_ponto
real array KKZ_k_escala
string array KKZ_k_nome
string array KKZ_k_ico
string array KKZ_k_chave
integer array KKZ_sel
integer array KKZ_posto
effect array KKZ_fx
boolean array KKZ_fx_vivo
unit array KKZ_heroi
integer array KKZ_tipo_u
string array KKZ_art0
effect array KKZ_pe
integer array KKZ_pe_i
real array KKZ_pe_x
real array KKZ_pe_y
trigger KKZ_t_heroi=null
integer KKZ_arg_pid=0
unit KKZ_arg_u=null
timer KKZ_tm=null
boolean KKZ_pronto=false
//@ENDGLOBALS

function KKZ_skin takes integer tipo, integer unid, string modelo, string ponto, real escala, string nome, string ico, string chave returns integer
    if KKZ_n>=KKZ_MAX-1 or tipo<1 or tipo>KKZ_NT then
        return 0
    endif
    set KKZ_n=KKZ_n+1
    set KKZ_k_tipo[KKZ_n]=tipo
    set KKZ_k_unid[KKZ_n]=unid
    set KKZ_k_modelo[KKZ_n]=modelo
    set KKZ_k_ponto[KKZ_n]=ponto
    set KKZ_k_escala[KKZ_n]=escala
    set KKZ_k_nome[KKZ_n]=nome
    set KKZ_k_ico[KKZ_n]=ico
    set KKZ_k_chave[KKZ_n]=chave
    return KKZ_n
endfunction

function KKZ_vivo takes unit h returns boolean
    return h!=null and GetUnitTypeId(h)!=0 and not IsUnitType(h, UNIT_TYPE_DEAD)
endfunction

function KKZ_por_chave takes string c returns integer
    local integer k=1
    loop
        exitwhen k>KKZ_n
        if KKZ_k_chave[k]==c then
            return k
        endif
        set k=k+1
    endloop
    return 0
endfunction

function KKZ_corpo takes unit h, integer alvo, real escala returns nothing
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

function KKZ_pegadas_limpa takes integer pid returns nothing
    local integer j=0
    loop
        exitwhen j>=KKZ_PEGADAS
        if KKZ_pe[pid*KKZ_PEGADAS+j]!=null then
            call DestroyEffect(KKZ_pe[pid*KKZ_PEGADAS+j])
            set KKZ_pe[pid*KKZ_PEGADAS+j]=null
        endif
        set j=j+1
    endloop
endfunction

function KKZ_desposta takes integer pid, integer tipo returns nothing
    local integer i=pid*8+tipo
    local unit h=KKZ_heroi[pid]
    if tipo==KKZ_CORPO then
        if KKZ_posto[i]!=0 and h!=null and GetUnitTypeId(h)!=0 then
            call KKZ_corpo(h, GetUnitTypeId(h), 1.0)
        endif
    elseif tipo==KKZ_PROJETIL then
        if KKZ_posto[i]!=0 and h!=null and GetUnitTypeId(h)!=0 and KKZ_art0[pid]!=null then
            call BlzSetUnitWeaponStringField(h, UNIT_WEAPON_SF_ATTACK_PROJECTILE_ART, 0, KKZ_art0[pid])
        endif
    elseif tipo==KKZ_PEGADA then
        call KKZ_pegadas_limpa(pid)
    elseif KKZ_fx[i]!=null then
        call DestroyEffect(KKZ_fx[i])
        set KKZ_fx[i]=null
    endif
    set KKZ_posto[i]=0
    set h=null
endfunction

function KKZ_posta takes integer pid, integer k returns boolean
    local integer tipo=KKZ_k_tipo[k]
    local integer i=pid*8+tipo
    local unit h=KKZ_heroi[pid]
    if k<1 or k>KKZ_n or h==null or GetUnitTypeId(h)==0 then
        set h=null
        return false
    endif
    if tipo==KKZ_PROJETIL and not IsUnitType(h, UNIT_TYPE_RANGED_ATTACKER) then
        set h=null
        return false
    endif
    call KKZ_desposta(pid, tipo)
    if tipo==KKZ_CORPO then
        if KKZ_k_unid[k]==0 then
            set h=null
            return false
        endif
        call KKZ_corpo(h, KKZ_k_unid[k], KKZ_k_escala[k])
    elseif tipo==KKZ_PROJETIL then
        call BlzSetUnitWeaponStringField(h, UNIT_WEAPON_SF_ATTACK_PROJECTILE_ART, 0, KKZ_k_modelo[k])
    elseif tipo==KKZ_PEGADA then
        set KKZ_pe_x[pid]=GetUnitX(h)
        set KKZ_pe_y[pid]=GetUnitY(h)
    else
        set KKZ_fx[i]=AddSpecialEffectTarget(KKZ_k_modelo[k], h, KKZ_k_ponto[k])
        if KKZ_k_escala[k]>0.0 and KKZ_k_escala[k]!=1.0 then
            call BlzSetSpecialEffectScale(KKZ_fx[i], KKZ_k_escala[k])
        endif
        set KKZ_fx_vivo[i]=KKZ_vivo(h)
    endif
    set KKZ_posto[i]=k
    set h=null
    return true
endfunction

function KKZ_escolhe takes integer pid, integer tipo, integer k returns boolean
    local integer i=pid*8+tipo
    if k==0 then
        call KKZ_desposta(pid, tipo)
        set KKZ_sel[i]=0
        return true
    endif
    if not KKZ_posta(pid, k) then
        return false
    endif
    set KKZ_sel[i]=k
    return true
endfunction

function KKZ_reveste takes integer pid returns nothing
    local integer t=1
    loop
        exitwhen t>KKZ_NT
        set KKZ_posto[pid*8+t]=0
        if KKZ_fx[pid*8+t]!=null then
            call DestroyEffect(KKZ_fx[pid*8+t])
            set KKZ_fx[pid*8+t]=null
        endif
        set t=t+1
    endloop
    call KKZ_pegadas_limpa(pid)
    set t=1
    loop
        exitwhen t>KKZ_NT
        if KKZ_sel[pid*8+t]!=0 and not KKZ_posta(pid, KKZ_sel[pid*8+t]) then
            set KKZ_sel[pid*8+t]=0
        endif
        set t=t+1
    endloop
endfunction

function KKZ_txt takes integer pid returns string
    local string s=""
    local integer t=1
    local integer k
    loop
        exitwhen t>KKZ_NT
        set k=KKZ_sel[pid*8+t]
        if k>0 and k<=KKZ_n then
            if s!="" then
                set s=s+","
            endif
            set s=s+I2S(t)+":"+KKZ_k_chave[k]
        endif
        set t=t+1
    endloop
    return s
endfunction

function KKZ_zera takes integer pid returns nothing
    local integer t=1
    loop
        exitwhen t>KKZ_NT
        call KKZ_desposta(pid, t)
        set KKZ_sel[pid*8+t]=0
        set t=t+1
    endloop
endfunction

function KKZ_le takes integer pid, string s returns nothing
    local integer n=StringLength(s)
    local integer a=0
    local integer i=0
    local integer d
    local integer t
    local integer k
    local string par
    call KKZ_zera(pid)
    loop
        exitwhen a>=n
        set i=a
        loop
            exitwhen i>=n or SubString(s, i, i+1)==","
            set i=i+1
        endloop
        set par=SubString(s, a, i)
        set d=0
        loop
            exitwhen d>=StringLength(par) or SubString(par, d, d+1)==":"
            set d=d+1
        endloop
        if d>0 and d<StringLength(par) then
            set t=S2I(SubString(par, 0, d))
            set k=KKZ_por_chave(SubString(par, d+1, StringLength(par)))
            if t>=1 and t<=KKZ_NT and k>0 and KKZ_k_tipo[k]==t then
                set KKZ_sel[pid*8+t]=k
            endif
        endif
        set a=i+1
    endloop
    if KKZ_heroi[pid]!=null then
        call KKZ_reveste(pid)
    endif
endfunction

function KKZ_grade takes nothing returns boolean
    local integer pid=KKP_arg_pid
    local integer s
    local integer t
    local integer b
    local integer k
    local integer e
    local string info
    local string det
    if KKP_aba_id[KKP_arg_aba]!=KKZ_aba then
        return false
    endif
    set s=1
    loop
        exitwhen s>15
        set b=pid*16+s
        set KKP_g_n[b]=0
        set KKP_g_atual[b]=-1
        set KKP_g_topo[b]=KKZ_topo
        set KKP_g_det[b]="Pick a skin on the left: Wear puts it on your hero, Remove takes off the one of that kind."
        set KKP_g_b1[b]="Wear"
        set KKP_g_b2[b]="Remove"
        set KKP_g_bm[b]=3
        set s=s+1
    endloop
    set KKZ_fora=0
    set k=1
    loop
        exitwhen k>KKZ_n
        set t=KKZ_k_tipo[k]
        set s=KKZ_sub_de[t]
        if s>=1 and s<=15 then
            set b=pid*16+s
            if KKP_g_n[b]>=KKP_GE then
                set KKZ_fora=KKZ_fora+1
            else
                set e=b*KKP_GE+KKP_g_n[b]
                set info=""
                set det="|cffffcc00"+KKZ_nome_tipo[t]+"|r"
                if KKZ_sel[pid*8+t]==k then
                    set info="|cff80ff80Worn|r"
                    set det=det+"  |cff80ff80(worn)|r"
                endif
                if t==KKZ_PROJETIL then
                    set det=det+"|n|cff999999Changes the missile of a ranged hero's attack.|r"
                elseif t==KKZ_PEGADA then
                    set det=det+"|n|cff999999Leaves footprints on the ground as your hero walks.|r"
                elseif t==KKZ_CORPO then
                    set det=det+"|n|cff999999Changes your hero's model (any class; looks only).|r"
                endif
                set KKP_g_nome[e]=KKZ_k_nome[k]
                set KKP_g_tit[e]=KKZ_k_nome[k]
                if KKZ_k_ico[k]!="" and KKZ_k_ico[k]!=null then
                    set KKP_g_ico[e]=KKZ_k_ico[k]
                else
                    set KKP_g_ico[e]=KKZ_ico_padrao
                endif
                set KKP_g_info[e]=info
                set KKP_g_edet[e]=det
                set KKP_g_ok[e]=KKZ_sel[pid*8+t]==k
                set KKP_g_trava[e]=false
                if KKZ_sel[pid*8+t]==k then
                    set KKP_g_eb[e]=2
                else
                    set KKP_g_eb[e]=1
                endif
                set KKP_g_val[e]=k
                set KKP_g_pv[e]=0
                set KKP_g_n[b]=KKP_g_n[b]+1
            endif
        endif
        set k=k+1
    endloop
    return false
endfunction

function KKZ_aplica takes nothing returns boolean
    local integer pid=KKP_arg_pid
    local integer b=pid*16+KKP_arg_sub
    local integer k=0
    local integer t
    if KKP_aba_id[KKP_arg_aba]!=KKZ_aba then
        return false
    endif
    if KKP_arg_i>=0 and KKP_arg_i<KKP_g_n[b] then
        set k=KKP_g_val[b*KKP_GE+KKP_arg_i]
    endif
    if k<1 or k>KKZ_n then
        set KKP_arg_ok=false
        return false
    endif
    set t=KKZ_k_tipo[k]
    if KKP_arg_btn==1 then
        set KKP_arg_ok=KKZ_escolhe(pid, t, k)
        if not KKP_arg_ok then
            if KKZ_heroi[pid]==null then
                call DisplayTimedTextToPlayer(Player(pid), 0, 0, 6.0, "|cffff8080Pick your hero first.|r")
            elseif t==KKZ_PROJETIL then
                call DisplayTimedTextToPlayer(Player(pid), 0, 0, 6.0, "|cffff8080Missile skins are for ranged heroes only.|r")
            endif
        endif
    elseif KKP_arg_btn==2 then
        set KKP_arg_ok=KKZ_escolhe(pid, t, 0)
    endif
    return false
endfunction

function KKZ_carimba takes integer pid, unit h returns nothing
    local integer k=KKZ_posto[pid*8+KKZ_PEGADA]
    local integer j
    local real x=GetUnitX(h)
    local real y=GetUnitY(h)
    local real dx=x-KKZ_pe_x[pid]
    local real dy=y-KKZ_pe_y[pid]
    if k<1 or dx*dx+dy*dy<KKZ_PASSO_D*KKZ_PASSO_D then
        return
    endif
    set KKZ_pe_x[pid]=x
    set KKZ_pe_y[pid]=y
    set j=pid*KKZ_PEGADAS+KKZ_pe_i[pid]
    if KKZ_pe[j]!=null then
        call DestroyEffect(KKZ_pe[j])
    endif
    set KKZ_pe[j]=AddSpecialEffect(KKZ_k_modelo[k], x, y)
    call BlzSetSpecialEffectYaw(KKZ_pe[j], GetUnitFacing(h)*bj_DEGTORAD)
    if KKZ_k_escala[k]>0.0 and KKZ_k_escala[k]!=1.0 then
        call BlzSetSpecialEffectScale(KKZ_pe[j], KKZ_k_escala[k])
    endif
    set KKZ_pe_i[pid]=KKZ_pe_i[pid]+1
    if KKZ_pe_i[pid]>=KKZ_PEGADAS then
        set KKZ_pe_i[pid]=0
    endif
endfunction

function KKZ_tiq takes nothing returns nothing
    local integer pid=0
    local integer t
    local integer i
    local boolean v
    local unit h
    loop
        exitwhen pid>=KKZ_jogadores
        set KKZ_arg_pid=pid
        set KKZ_arg_u=null
        call TriggerEvaluate(KKZ_t_heroi)
        set h=KKZ_arg_u
        set KKZ_arg_u=null
        if h!=KKZ_heroi[pid] then
            if h==null then
                set t=KKZ_ASA
                loop
                    exitwhen t>KKZ_RASTRO
                    if KKZ_fx[pid*8+t]!=null then
                        call DestroyEffect(KKZ_fx[pid*8+t])
                        set KKZ_fx[pid*8+t]=null
                    endif
                    set KKZ_posto[pid*8+t]=0
                    set t=t+1
                endloop
                call KKZ_pegadas_limpa(pid)
            endif
            set KKZ_heroi[pid]=h
            set KKZ_tipo_u[pid]=0
            if h!=null then
                set KKZ_tipo_u[pid]=GetUnitTypeId(h)
                set KKZ_art0[pid]=BlzGetUnitWeaponStringField(h, UNIT_WEAPON_SF_ATTACK_PROJECTILE_ART, 0)
                call KKZ_reveste(pid)
            endif
        elseif h!=null and GetUnitTypeId(h)!=KKZ_tipo_u[pid] then
            set KKZ_tipo_u[pid]=GetUnitTypeId(h)
            set KKZ_posto[pid*8+KKZ_CORPO]=0
            if KKZ_posto[pid*8+KKZ_PROJETIL]==0 then
                set KKZ_art0[pid]=BlzGetUnitWeaponStringField(h, UNIT_WEAPON_SF_ATTACK_PROJECTILE_ART, 0)
            endif
            set KKZ_posto[pid*8+KKZ_PROJETIL]=0
            if KKZ_sel[pid*8+KKZ_CORPO]!=0 then
                call KKZ_posta(pid, KKZ_sel[pid*8+KKZ_CORPO])
            endif
            if KKZ_sel[pid*8+KKZ_PROJETIL]!=0 and not KKZ_posta(pid, KKZ_sel[pid*8+KKZ_PROJETIL]) then
                set KKZ_sel[pid*8+KKZ_PROJETIL]=0
            endif
        endif
        if h!=null then
            set v=KKZ_vivo(h)
            set t=KKZ_ASA
            loop
                exitwhen t>KKZ_RASTRO
                set i=pid*8+t
                if KKZ_sel[i]!=0 then
                    if v and not KKZ_fx_vivo[i] then
                        call KKZ_posta(pid, KKZ_sel[i])
                    elseif not v then
                        set KKZ_fx_vivo[i]=false
                    endif
                endif
                set t=t+1
            endloop
            if v then
                call KKZ_carimba(pid, h)
            endif
        endif
        set pid=pid+1
    endloop
    set h=null
endfunction

function KKZ_init takes code heroi returns nothing
    if KKZ_pronto then
        return
    endif
    set KKZ_pronto=true
    set KKZ_nome_tipo[KKZ_CORPO]="Hero skin"
    set KKZ_nome_tipo[KKZ_ASA]="Wings"
    set KKZ_nome_tipo[KKZ_AURA]="Aura"
    set KKZ_nome_tipo[KKZ_RASTRO]="Effect"
    set KKZ_nome_tipo[KKZ_PROJETIL]="Missile"
    set KKZ_nome_tipo[KKZ_PEGADA]="Footprints"
    set KKZ_t_heroi=CreateTrigger()
    call TriggerAddCondition(KKZ_t_heroi, Condition(heroi))
    call KKP_gancho(KKP_G_GRADE, function KKZ_grade)
    call KKP_gancho(KKP_G_APLICA, function KKZ_aplica)
    set KKZ_tm=CreateTimer()
    call TimerStart(KKZ_tm, KKZ_PASSO, true, function KKZ_tiq)
endfunction
