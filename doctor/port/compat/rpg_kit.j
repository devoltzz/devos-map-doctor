//@GLOBALS
constant integer RPGW_NUKE=1
constant integer RPGW_AREA=2
constant integer RPGW_PONTO=3
constant integer RPGW_LINHA=4
constant integer RPGW_CADEIA=5
constant integer RPGW_DOT=6
constant integer RPGW_ZONA=7
constant integer RPGW_ESCUDO=8
constant integer RPGW_BUFF=9
constant integer RPGW_DEBUFF=10
constant integer RPGW_TAUNT=11
constant integer RPGW_INVOCA=12
constant integer RPGW_SALTO=13
constant integer RPGW_MANA=14
constant integer RPGW_DRENO=15
constant integer RPGW_POSTURA=16
constant integer RPGW_P_RAIO=1
constant integer RPGW_P_DUR=2
constant integer RPGW_P_N=3
constant integer RPGW_P_DECAI=4
constant integer RPGW_P_STUN=5
constant integer RPGW_P_LENTO=6
constant integer RPGW_P_AMEACA=7
constant integer RPGW_P_ALCANCE=8
constant integer RPGW_P_LARGURA=9
constant integer RPGW_P_INTERVALO=10
constant integer RPGW_P_HPCUSTO=11
constant integer RPGW_P_ALVO=12
constant integer RPGW_P_EMPURRA=13
constant integer RPGW_P_ACIMA80=14
constant integer RPGW_P_REVIVE=15
constant integer RPGW_P_VIDA=17
constant integer RPGW_P_DANO=18
constant integer RPGW_P_CORTA=19
constant integer RPGW_P_CURA=20
constant integer RPGW_P_MANA=21
constant integer RPGW_S_MOV=100
constant integer RPGW_ROUBO=1
constant integer RPGW_BLOQUEIO=2
constant integer RPGW_GRACA=3
constant integer RPGW_MURCHA=4
constant integer RPGW_COSTAS=5
constant integer RPGW_ALMAS=6
constant integer RPGW_HEADSHOT=7
constant integer RPGW_FLUXO=8
constant integer RPGW_FURIA=9
constant integer RPGW_AURA_A=10
constant integer RPGW_AURA_I=11
constant integer RPGW_MAXB=600
integer RPGW_jogadores=12
integer array RPGW_lim_b
integer array RPGW_lim_u
real RPGW_tique=0.25
hashtable RPGW_ht=null
trigger RPGW_t_cast=null
trigger RPGW_t_nivel=null
trigger RPGW_t_morte=null
timer RPGW_tm=null
group RPGW_g=null
real RPGW_agora=0.0
unit array RPGW_b_u
integer array RPGW_b_s
real array RPGW_b_v
real array RPGW_b_fim
integer RPGW_bn=0
unit array RPGW_z_u
integer array RPGW_z_a
integer array RPGW_z_r
real array RPGW_z_x
real array RPGW_z_y
real array RPGW_z_fim
real array RPGW_z_prox
boolean array RPGW_z_reviveu
effect array RPGW_z_fx
integer RPGW_zn=0
unit array RPGW_d_src
unit array RPGW_d_tgt
real array RPGW_d_v
integer array RPGW_d_n
integer RPGW_dn=0
unit RPGW_c_u=null
integer RPGW_c_a=0
integer RPGW_c_r=0
real RPGW_c_mult=1.0
real RPGW_c_x=0.0
real RPGW_c_y=0.0
unit RPGW_c_alvo=null
integer RPGW_c_conta=0
//@ENDGLOBALS

function RPGW_skill takes integer abil, integer forma returns nothing
    call SaveInteger(RPGW_ht, abil, 0, forma)
endfunction

function RPGW_p takes integer abil, integer k, real v returns nothing
    call SaveReal(RPGW_ht, abil, k, v)
endfunction

function RPGW_v takes integer abil, integer k returns real
    return LoadReal(RPGW_ht, abil, k)
endfunction

function RPGW_unidade takes integer abil, integer id returns nothing
    call SaveInteger(RPGW_ht, abil, 300, id)
endfunction

function RPGW_efeito takes integer abil, integer k, string m returns nothing
    call SaveStr(RPGW_ht, abil, 200+k, m)
endfunction

function RPGW_fx_de takes integer abil, integer k returns string
    local string s=LoadStr(RPGW_ht, abil, 200+k)
    if s==null then
        return ""
    endif
    return s
endfunction

function RPGW_buff_def takes integer abil, integer i, integer stat, real v returns nothing
    call SaveInteger(RPGW_ht, abil, 40+i*2, stat)
    call SaveReal(RPGW_ht, abil, 41+i*2, v)
endfunction

function RPGW_kit takes integer tipo, integer abil, boolean ult returns nothing
    local integer n=LoadInteger(RPGW_ht, tipo, -1)+1
    call SaveInteger(RPGW_ht, tipo, -1, n)
    call SaveInteger(RPGW_ht, tipo, -1-n, abil)
    call SaveBoolean(RPGW_ht, tipo, -100-n, ult)
endfunction

function RPGW_passiva takes integer tipo, integer p, real a, real b returns nothing
    call SaveBoolean(RPGW_ht, tipo, -300-p, true)
    call SaveReal(RPGW_ht, tipo, -400-p, a)
    call SaveReal(RPGW_ht, tipo, -500-p, b)
endfunction

function RPGW_tem takes unit u, integer p returns boolean
    return u!=null and LoadBoolean(RPGW_ht, GetUnitTypeId(u), -300-p)
endfunction

function RPGW_pa takes unit u, integer p returns real
    return LoadReal(RPGW_ht, GetUnitTypeId(u), -400-p)
endfunction

function RPGW_pb takes unit u, integer p returns real
    return LoadReal(RPGW_ht, GetUnitTypeId(u), -500-p)
endfunction

function RPGW_aura takes integer tipo, integer p, integer stat, real v, real raio returns nothing
    call RPGW_passiva(tipo, p, v, raio)
    call SaveInteger(RPGW_ht, tipo, -600-p, stat)
endfunction

function RPGW_vivo takes unit u returns boolean
    return u!=null and GetUnitTypeId(u)!=0 and not IsUnitType(u, UNIT_TYPE_DEAD)
endfunction

function RPGW_inimigo takes unit src, unit u returns boolean
    return RPGW_vivo(u) and IsUnitEnemy(u, GetOwningPlayer(src)) and not IsUnitType(u, UNIT_TYPE_STRUCTURE)
endfunction

function RPGW_aliado takes unit src, unit u returns boolean
    return RPGW_vivo(u) and IsUnitAlly(u, GetOwningPlayer(src)) and not IsUnitType(u, UNIT_TYPE_STRUCTURE)
endfunction

function RPGW_fx takes string m, real x, real y returns nothing
    if m!="" then
        call DestroyEffect(AddSpecialEffect(m, x, y))
    endif
endfunction

function RPGW_fx_u takes string m, unit u returns nothing
    if m!="" then
        call DestroyEffect(AddSpecialEffectTarget(m, u, "origin"))
    endif
endfunction

function RPGW_principal takes unit h returns real
    local integer a=LoadInteger(RPGI_ht, GetUnitTypeId(h), 200)
    if a==2 then
        return I2R(GetHeroAgi(h, true))
    elseif a==3 then
        return I2R(GetHeroInt(h, true))
    endif
    return I2R(GetHeroStr(h, true))
endfunction

function RPGW_aplica_stat takes unit u, integer s, real v returns nothing
    if s==RPGW_S_MOV then
        call SetUnitMoveSpeed(u, GetUnitMoveSpeed(u)+v)
    elseif s==200 then
        if v>0.0 then
            call BlzPauseUnitEx(u, true)
        else
            call BlzPauseUnitEx(u, false)
        endif
    else
        call RPGD_soma(u, s, v)
        if s==RPGD_S_VEL then
            call RPGD_vel(u)
        endif
    endif
endfunction

function RPGW_buff takes unit u, integer s, real v, real dur returns nothing
    if not RPGW_vivo(u) or RPGW_bn>=RPGW_MAXB or dur<=0.0 then
        return
    endif
    if (s==200 or (s==RPGW_S_MOV and v<0.0)) and RPGF_imune(u) then
        return
    endif
    call RPGW_aplica_stat(u, s, v)
    set RPGW_b_u[RPGW_bn]=u
    set RPGW_b_s[RPGW_bn]=s
    set RPGW_b_v[RPGW_bn]=v
    set RPGW_b_fim[RPGW_bn]=RPGW_agora+dur
    set RPGW_bn=RPGW_bn+1
endfunction

function RPGW_atordoa takes unit u, real dur returns nothing
    if dur>0.0 then
        call RPGW_buff(u, 200, 1.0, dur)
    endif
endfunction

function RPGW_lento takes unit u, real frac, real dur returns nothing
    if frac>0.0 and dur>0.0 then
        call RPGW_buff(u, RPGW_S_MOV, -GetUnitMoveSpeed(u)*frac, dur)
    endif
endfunction

function RPGW_buff_skill takes unit u, integer abil, real dur returns nothing
    local integer i=0
    local integer s
    loop
        exitwhen i>3
        set s=LoadInteger(RPGW_ht, abil, 40+i*2)
        if s!=0 then
            call RPGW_buff(u, s, LoadReal(RPGW_ht, abil, 41+i*2), dur)
        endif
        set i=i+1
    endloop
endfunction

function RPGW_dano takes unit src, unit tgt, real mult returns nothing
    local real m=RPGW_c_mult*mult
    if RPGW_v(RPGW_c_a, RPGW_P_ACIMA80)>0.0 and GetWidgetLife(tgt)>=0.8*I2R(BlzGetUnitMaxHP(tgt)) then
        set m=m*(1.0+RPGW_v(RPGW_c_a, RPGW_P_ACIMA80))
    endif
    if HaveSavedReal(RPGD_ht, RPGW_c_a, 1) then
        call RPGD_skill(src, tgt, RPGW_c_a, RPGW_c_r, m)
    endif
    if RPGW_v(RPGW_c_a, RPGW_P_AMEACA)>1.0 then
        call RPGA_soma(tgt, src, RPGD_bruto(src, RPGW_c_a, RPGW_c_r)*(RPGW_v(RPGW_c_a, RPGW_P_AMEACA)-1.0))
    endif
    call RPGW_atordoa(tgt, RPGW_v(RPGW_c_a, RPGW_P_STUN))
    call RPGW_lento(tgt, RPGW_v(RPGW_c_a, RPGW_P_LENTO), IMaxBJ(2, R2I(RPGW_v(RPGW_c_a, RPGW_P_DUR))))
    call RPGW_fx_u(RPGW_fx_de(RPGW_c_a, 1), tgt)
endfunction

function RPGW_cura takes unit src, unit tgt, real mult returns nothing
    if HaveSavedReal(RPGD_ht, -RPGW_c_a, 1) then
        call RPGD_cura(src, tgt, -RPGW_c_a, RPGW_c_r, RPGW_c_mult*mult)
    endif
endfunction

function RPGW_area_cada takes nothing returns nothing
    local unit u=GetEnumUnit()
    if RPGW_inimigo(RPGW_c_u, u) then
        call RPGW_dano(RPGW_c_u, u, 1.0)
    elseif RPGW_aliado(RPGW_c_u, u) then
        call RPGW_cura(RPGW_c_u, u, 1.0)
    endif
    set u=null
endfunction

function RPGW_varre takes real x, real y, real raio, code f returns nothing
    call GroupEnumUnitsInRange(RPGW_g, x, y, raio, null)
    call ForGroup(RPGW_g, f)
    call GroupClear(RPGW_g)
endfunction

function RPGW_linha_cada takes nothing returns nothing
    local unit u=GetEnumUnit()
    local real dx=GetUnitX(u)-GetUnitX(RPGW_c_u)
    local real dy=GetUnitY(u)-GetUnitY(RPGW_c_u)
    local real a=Atan2(RPGW_c_y-GetUnitY(RPGW_c_u), RPGW_c_x-GetUnitX(RPGW_c_u))
    local real t=dx*Cos(a)+dy*Sin(a)
    local real p=RAbsBJ(-dx*Sin(a)+dy*Cos(a))
    if RPGW_inimigo(RPGW_c_u, u) and t>=0.0 and t<=RPGW_v(RPGW_c_a, RPGW_P_ALCANCE) and p<=RPGW_v(RPGW_c_a, RPGW_P_LARGURA)*0.5 then
        call RPGW_dano(RPGW_c_u, u, 1.0)
    endif
    set u=null
endfunction

function RPGW_cadeia_cada takes nothing returns nothing
    local unit u=GetEnumUnit()
    local real dx=GetUnitX(u)-RPGW_c_x
    local real dy=GetUnitY(u)-RPGW_c_y
    local boolean ok
    if HaveSavedBoolean(RPGW_ht, -9, GetHandleId(u)) then
        set u=null
        return
    endif
    if HaveSavedReal(RPGD_ht, -RPGW_c_a, 1) and not HaveSavedReal(RPGD_ht, RPGW_c_a, 1) then
        set ok=RPGW_aliado(RPGW_c_u, u) and GetWidgetLife(u)<I2R(BlzGetUnitMaxHP(u))
    else
        set ok=RPGW_inimigo(RPGW_c_u, u)
    endif
    if ok and (RPGW_c_alvo==null or dx*dx+dy*dy<LoadReal(RPGW_ht, -9, 0)) then
        set RPGW_c_alvo=u
        call SaveReal(RPGW_ht, -9, 0, dx*dx+dy*dy)
    endif
    set u=null
endfunction

function RPGW_zona takes unit src, integer abil, integer rank, real x, real y returns nothing
    local integer i=RPGW_zn
    if i>=200 then
        return
    endif
    set RPGW_zn=i+1
    set RPGW_z_u[i]=src
    set RPGW_z_a[i]=abil
    set RPGW_z_r[i]=rank
    set RPGW_z_x[i]=x
    set RPGW_z_y[i]=y
    set RPGW_z_fim[i]=RPGW_agora+RPGW_v(abil, RPGW_P_DUR)
    set RPGW_z_prox[i]=RPGW_agora
    set RPGW_z_reviveu[i]=false
    set RPGW_z_fx[i]=null
    if RPGW_fx_de(abil, 2)!="" then
        set RPGW_z_fx[i]=AddSpecialEffect(RPGW_fx_de(abil, 2), x, y)
    endif
endfunction

function RPGW_zona_cada takes nothing returns nothing
    local unit u=GetEnumUnit()
    local integer i=LoadInteger(RPGW_ht, -8, 0)
    local real meio=0.5/RMaxBJ(RPGW_v(RPGW_c_a, RPGW_P_DUR), 0.5)
    if RPGW_inimigo(RPGW_c_u, u) then
        call RPGW_dano(RPGW_c_u, u, meio)
    elseif RPGW_aliado(RPGW_c_u, u) then
        call RPGW_cura(RPGW_c_u, u, meio)
        call RPGW_buff_skill(u, RPGW_c_a, 0.6)
    elseif RPGW_v(RPGW_c_a, RPGW_P_REVIVE)>0.0 and not RPGW_z_reviveu[i] and IsUnitType(u, UNIT_TYPE_HERO) and IsUnitType(u, UNIT_TYPE_DEAD) and IsUnitAlly(u, GetOwningPlayer(RPGW_c_u)) then
        set RPGW_z_reviveu[i]=true
        call ReviveHero(u, GetUnitX(u), GetUnitY(u), true)
        call SetWidgetLife(u, I2R(BlzGetUnitMaxHP(u))*0.3)
    endif
    set u=null
endfunction

function RPGW_dot takes unit src, unit tgt, real total, integer abil returns nothing
    local integer i=0
    local integer n=0
    local integer max=R2I(RMaxBJ(RPGW_v(abil, RPGW_P_N), 1.0))
    local real dur=RMaxBJ(RPGW_v(abil, RPGW_P_DUR), 1.0)
    loop
        exitwhen i>=RPGW_dn
        if RPGW_d_src[i]==src and RPGW_d_tgt[i]==tgt and RPGW_d_n[i]>0 then
            set n=n+1
        endif
        set i=i+1
    endloop
    if n>=max or RPGW_dn>=300 then
        return
    endif
    set RPGW_d_src[RPGW_dn]=src
    set RPGW_d_tgt[RPGW_dn]=tgt
    set RPGW_d_n[RPGW_dn]=R2I(dur/0.5)
    set RPGW_d_v[RPGW_dn]=total/I2R(RPGW_d_n[RPGW_dn])
    set RPGW_dn=RPGW_dn+1
endfunction

function RPGW_invoca takes unit h, integer abil, real x, real y returns nothing
    local integer n=R2I(RMaxBJ(RPGW_v(abil, RPGW_P_N), 1.0))
    local integer k=0
    local unit u
    local real a
    local real almas=0.0
    if RPGW_tem(h, RPGW_ALMAS) then
        set almas=LoadReal(RPGW_ht, GetHandleId(h), -20)*RPGW_pa(h, RPGW_ALMAS)
    endif
    loop
        exitwhen k>=n
        set a=2.0*bj_PI*I2R(k)/I2R(n)
        set u=CreateUnit(GetOwningPlayer(h), LoadInteger(RPGW_ht, abil, 300), x+120.0*Cos(a), y+120.0*Sin(a), GetUnitFacing(h))
        call BlzSetUnitMaxHP(u, IMaxBJ(1, R2I(I2R(BlzGetUnitMaxHP(h))*RPGW_v(abil, RPGW_P_VIDA))))
        call SetWidgetLife(u, I2R(BlzGetUnitMaxHP(u)))
        call BlzSetUnitBaseDamage(u, IMaxBJ(1, R2I(RPGW_principal(h)*RPGW_v(abil, RPGW_P_DANO)*(1.0+almas))), 0)
        call UnitApplyTimedLife(u, 'BTLF', RMaxBJ(RPGW_v(abil, RPGW_P_DUR), 1.0))
        call RPGW_fx(RPGW_fx_de(abil, 1), GetUnitX(u), GetUnitY(u))
        set k=k+1
    endloop
    set u=null
endfunction

function RPGW_custo_vida takes unit h, integer abil returns nothing
    local real c=RPGW_v(abil, RPGW_P_HPCUSTO)
    if c>0.0 then
        call SetWidgetLife(h, RMaxBJ(1.0, GetWidgetLife(h)-c*I2R(BlzGetUnitMaxHP(h))))
    endif
endfunction

function RPGW_buff_grupo_cada takes nothing returns nothing
    if RPGW_aliado(RPGW_c_u, GetEnumUnit()) then
        call RPGW_buff_skill(GetEnumUnit(), RPGW_c_a, RPGW_v(RPGW_c_a, RPGW_P_DUR))
        call RPGW_fx_u(RPGW_fx_de(RPGW_c_a, 1), GetEnumUnit())
    endif
endfunction

function RPGW_debuff_cada takes nothing returns nothing
    local unit u=GetEnumUnit()
    local real dur=RPGW_v(RPGW_c_a, RPGW_P_DUR)
    if RPGW_inimigo(RPGW_c_u, u) then
        call RPGW_buff_skill(u, RPGW_c_a, dur)
        call RPGW_dano(RPGW_c_u, u, 1.0)
        if RPGW_tem(RPGW_c_u, RPGW_MURCHA) then
            call RPGW_dot(RPGW_c_u, u, RPGW_pa(RPGW_c_u, RPGW_MURCHA)*I2R(GetHeroInt(RPGW_c_u, true))*dur, RPGW_c_a)
        endif
    endif
    set u=null
endfunction

function RPGW_taunt_cada takes nothing returns nothing
    if RPGW_inimigo(RPGW_c_u, GetEnumUnit()) then
        call RPGA_registra(GetEnumUnit())
        call RPGA_taunt(GetEnumUnit(), RPGW_c_u, RPGW_v(RPGW_c_a, RPGW_P_DUR))
    endif
endfunction

function RPGW_mana_cada takes nothing returns nothing
    local unit u=GetEnumUnit()
    if RPGW_aliado(RPGW_c_u, u) then
        call SetUnitState(u, UNIT_STATE_MANA, GetUnitState(u, UNIT_STATE_MANA)+GetUnitState(u, UNIT_STATE_MAX_MANA)*RPGW_v(RPGW_c_a, RPGW_P_N))
    endif
    set u=null
endfunction

function RPGW_lanca takes unit h, integer abil, unit alvo, real x, real y returns nothing
    local integer forma=LoadInteger(RPGW_ht, abil, 0)
    local integer k
    local integer n
    local real raio=RPGW_v(abil, RPGW_P_RAIO)
    local real m=1.0
    local unit u
    local real v
    local integer cont
    if forma==0 then
        return
    endif
    set RPGW_c_u=h
    set RPGW_c_a=abil
    set RPGW_c_r=IMaxBJ(1, LoadInteger(RPGW_ht, GetHandleId(h), abil))
    set RPGW_c_x=x
    set RPGW_c_y=y
    if RPGW_tem(h, RPGW_FLUXO) then
        set cont=LoadInteger(RPGW_ht, GetHandleId(h), -21)+1
        if cont>=R2I(RPGW_pa(h, RPGW_FLUXO)) then
            set cont=0
            set m=RPGW_pb(h, RPGW_FLUXO)
            call SetUnitState(h, UNIT_STATE_MANA, GetUnitState(h, UNIT_STATE_MANA)+I2R(BlzGetUnitAbilityManaCost(h, abil, 0)))
        endif
        call SaveInteger(RPGW_ht, GetHandleId(h), -21, cont)
    endif
    set RPGW_c_mult=m
    call RPGW_custo_vida(h, abil)
    if forma==RPGW_NUKE or forma==RPGW_DRENO then
        if alvo==null then
            return
        endif
        set n=R2I(RMaxBJ(RPGW_v(abil, RPGW_P_N), 1.0))
        set k=0
        loop
            exitwhen k>=n
            set v=GetWidgetLife(alvo)
            call RPGW_dano(h, alvo, 1.0)
            if forma==RPGW_DRENO then
                call SetWidgetLife(h, GetWidgetLife(h)+RMaxBJ(0.0, v-GetWidgetLife(alvo))*RPGW_v(abil, RPGW_P_CURA))
            endif
            set k=k+1
        endloop
        if RPGW_v(abil, RPGW_P_EMPURRA)!=0.0 then
            set v=Atan2(GetUnitY(alvo)-GetUnitY(h), GetUnitX(alvo)-GetUnitX(h))
            call SetUnitPosition(alvo, GetUnitX(alvo)+RPGW_v(abil, RPGW_P_EMPURRA)*Cos(v), GetUnitY(alvo)+RPGW_v(abil, RPGW_P_EMPURRA)*Sin(v))
        endif
        if RPGW_v(abil, RPGW_P_ALCANCE)>0.0 then
            set v=Atan2(GetUnitY(h)-GetUnitY(alvo), GetUnitX(h)-GetUnitX(alvo))
            call SetUnitPosition(h, GetUnitX(alvo)+90.0*Cos(v), GetUnitY(alvo)+90.0*Sin(v))
        endif
    elseif forma==RPGW_AREA then
        call RPGW_fx(RPGW_fx_de(abil, 2), GetUnitX(h), GetUnitY(h))
        call RPGW_varre(GetUnitX(h), GetUnitY(h), raio, function RPGW_area_cada)
    elseif forma==RPGW_PONTO then
        set n=R2I(RMaxBJ(RPGW_v(abil, RPGW_P_N), 1.0))
        set k=0
        loop
            exitwhen k>=n
            call RPGW_fx(RPGW_fx_de(abil, 2), x, y)
            call RPGW_varre(x, y, raio, function RPGW_area_cada)
            set k=k+1
        endloop
        if RPGW_v(abil, RPGW_P_DUR)>0.0 then
            call RPGW_zona(h, abil, RPGW_c_r, x, y)
        endif
    elseif forma==RPGW_LINHA then
        if alvo!=null then
            set RPGW_c_x=GetUnitX(alvo)
            set RPGW_c_y=GetUnitY(alvo)
        endif
        set k=0
        loop
            exitwhen I2R(k)*128.0>RPGW_v(abil, RPGW_P_ALCANCE)
            set v=Atan2(RPGW_c_y-GetUnitY(h), RPGW_c_x-GetUnitX(h))
            call RPGW_fx(RPGW_fx_de(abil, 2), GetUnitX(h)+I2R(k)*128.0*Cos(v), GetUnitY(h)+I2R(k)*128.0*Sin(v))
            set k=k+2
        endloop
        call RPGW_varre(GetUnitX(h), GetUnitY(h), RPGW_v(abil, RPGW_P_ALCANCE)+200.0, function RPGW_linha_cada)
    elseif forma==RPGW_CADEIA then
        call FlushChildHashtable(RPGW_ht, -9)
        set u=alvo
        if u==null then
            set u=h
        endif
        set n=R2I(RMaxBJ(RPGW_v(abil, RPGW_P_N), 1.0))
        set k=0
        loop
            exitwhen k>=n or u==null
            call SaveBoolean(RPGW_ht, -9, GetHandleId(u), true)
            if RPGW_inimigo(h, u) then
                call RPGW_dano(h, u, Pow(1.0-RPGW_v(abil, RPGW_P_DECAI), I2R(k)))
            elseif RPGW_aliado(h, u) then
                call RPGW_cura(h, u, Pow(1.0-RPGW_v(abil, RPGW_P_DECAI), I2R(k)))
            endif
            set RPGW_c_x=GetUnitX(u)
            set RPGW_c_y=GetUnitY(u)
            set RPGW_c_alvo=null
            call SaveReal(RPGW_ht, -9, 0, 1000000000.0)
            call RPGW_varre(RPGW_c_x, RPGW_c_y, RMaxBJ(raio, 500.0), function RPGW_cadeia_cada)
            set u=RPGW_c_alvo
            set k=k+1
        endloop
    elseif forma==RPGW_DOT then
        if alvo!=null then
            call RPGW_dot(h, alvo, RPGD_bruto(h, abil, RPGW_c_r)*(1.0+RPGD_bonus(h, RPGD_S_SKILL))*m, abil)
            call RPGW_fx_u(RPGW_fx_de(abil, 1), alvo)
        endif
    elseif forma==RPGW_ZONA then
        if alvo!=null or (x==0.0 and y==0.0) then
            set x=GetUnitX(h)
            set y=GetUnitY(h)
        endif
        call RPGW_zona(h, abil, RPGW_c_r, x, y)
    elseif forma==RPGW_ESCUDO then
        set u=alvo
        if u==null or not RPGW_aliado(h, u) then
            set u=h
        endif
        set v=RPGD_bruto(h, -abil, RPGW_c_r)*(1.0+RPGD_bonus(h, RPGD_S_CURA))*m
        call SaveReal(RPGW_ht, GetHandleId(u), -30, LoadReal(RPGW_ht, GetHandleId(u), -30)+v)
        call SaveReal(RPGW_ht, GetHandleId(u), -31, RPGW_agora+RPGW_v(abil, RPGW_P_DUR))
        call RPGW_fx_u(RPGW_fx_de(abil, 1), u)
    elseif forma==RPGW_BUFF then
        set k=R2I(RPGW_v(abil, RPGW_P_ALVO))
        if k==1 then
            call RPGW_varre(GetUnitX(h), GetUnitY(h), RMaxBJ(raio, 600.0), function RPGW_buff_grupo_cada)
        elseif k==2 and alvo!=null and RPGW_aliado(h, alvo) then
            call RPGW_buff_skill(alvo, abil, RPGW_v(abil, RPGW_P_DUR))
            call RPGW_fx_u(RPGW_fx_de(abil, 1), alvo)
        else
            call RPGW_buff_skill(h, abil, RPGW_v(abil, RPGW_P_DUR))
            call RPGW_fx_u(RPGW_fx_de(abil, 1), h)
        endif
    elseif forma==RPGW_DEBUFF then
        if R2I(RPGW_v(abil, RPGW_P_ALVO))==4 and alvo!=null then
            call RPGW_varre(GetUnitX(alvo), GetUnitY(alvo), 50.0, function RPGW_debuff_cada)
        elseif alvo!=null and R2I(RPGW_v(abil, RPGW_P_ALVO))==5 then
            call RPGW_varre(GetUnitX(alvo), GetUnitY(alvo), raio, function RPGW_debuff_cada)
        else
            if x==0.0 and y==0.0 then
                set x=GetUnitX(h)
                set y=GetUnitY(h)
            endif
            call RPGW_varre(x, y, raio, function RPGW_debuff_cada)
        endif
        call RPGW_fx(RPGW_fx_de(abil, 2), GetUnitX(h), GetUnitY(h))
    elseif forma==RPGW_TAUNT then
        call RPGW_varre(GetUnitX(h), GetUnitY(h), raio, function RPGW_taunt_cada)
        call RPGW_buff_skill(h, abil, RPGW_v(abil, RPGW_P_DUR))
        call RPGW_fx(RPGW_fx_de(abil, 2), GetUnitX(h), GetUnitY(h))
    elseif forma==RPGW_INVOCA then
        call RPGW_invoca(h, abil, GetUnitX(h), GetUnitY(h))
    elseif forma==RPGW_SALTO then
        if alvo!=null then
            set v=GetUnitFacing(alvo)*bj_DEGTORAD+bj_PI
            call SetUnitPosition(h, GetUnitX(alvo)+80.0*Cos(v), GetUnitY(alvo)+80.0*Sin(v))
            call SetUnitFacing(h, GetUnitFacing(alvo))
            call RPGW_buff(h, RPGD_S_CRIT, 1.0, 2.0)
            call IssueTargetOrder(h, "attack", alvo)
            call RPGW_fx_u(RPGW_fx_de(abil, 1), h)
        endif
        call RPGA_corta(h, RPGW_v(abil, RPGW_P_CORTA))
    elseif forma==RPGW_MANA then
        call RPGW_varre(GetUnitX(h), GetUnitY(h), RMaxBJ(raio, 800.0), function RPGW_mana_cada)
        call RPGA_corta(h, RPGW_v(abil, RPGW_P_CORTA))
        call RPGW_fx(RPGW_fx_de(abil, 2), GetUnitX(h), GetUnitY(h))
    elseif forma==RPGW_POSTURA then
        if RPGA_postura(h) then
            if RPGA_em_postura(h) then
                call DisplayTimedTextToPlayer(GetOwningPlayer(h), 0, 0, 2.0, "|cff80c0ffTank stance ON|r")
            else
                call DisplayTimedTextToPlayer(GetOwningPlayer(h), 0, 0, 2.0, "|cff999999Tank stance OFF|r")
            endif
        endif
    endif
    if forma!=RPGW_SALTO and forma!=RPGW_MANA and RPGW_v(abil, RPGW_P_CORTA)>0.0 then
        call RPGA_corta(h, RPGW_v(abil, RPGW_P_CORTA))
    endif
    set u=null
endfunction

function RPGW_cast takes nothing returns nothing
    local unit h=GetTriggerUnit()
    local integer abil=GetSpellAbilityId()
    local location l
    local real x=0.0
    local real y=0.0
    if LoadInteger(RPGW_ht, abil, 0)!=0 then
        set l=GetSpellTargetLoc()
        if l!=null then
            set x=GetLocationX(l)
            set y=GetLocationY(l)
            call RemoveLocation(l)
        endif
        call RPGW_lanca(h, abil, GetSpellTargetUnit(), x, y)
    endif
    set h=null
    set l=null
endfunction

function RPGW_gancho_dano takes nothing returns boolean
    local unit src=RPGD_ev_src
    local unit tgt=RPGD_ev_tgt
    local real v=RPGD_ev_valor
    local real f
    local real e
    if src==null or tgt==null then
        return false
    endif
    if RPGD_ev_tipo==RPGD_T_CURA then
        if RPGW_tem(src, RPGW_GRACA) then
            set e=v-(I2R(BlzGetUnitMaxHP(tgt))-GetWidgetLife(tgt))
            if e>0.0 then
                set f=RMinBJ(LoadReal(RPGW_ht, GetHandleId(tgt), -30)+e, RPGW_pa(src, RPGW_GRACA)*I2R(BlzGetUnitMaxHP(tgt)))
                call SaveReal(RPGW_ht, GetHandleId(tgt), -30, f)
                call SaveReal(RPGW_ht, GetHandleId(tgt), -31, RPGW_agora+10.0)
            endif
        endif
        set src=null
        set tgt=null
        return false
    endif
    if RPGW_tem(src, RPGW_COSTAS) and RAbsBJ(ModuloReal(GetUnitFacing(src)-GetUnitFacing(tgt)+180.0, 360.0)-180.0)<90.0 then
        set v=v*(1.0+RPGW_pa(src, RPGW_COSTAS))
    endif
    if RPGW_tem(src, RPGW_HEADSHOT) and RPGD_ev_tipo==RPGD_T_ATAQUE and GetRandomReal(0.0, 1.0)<RPGW_pa(src, RPGW_HEADSHOT) then
        set v=v*RPGW_pb(src, RPGW_HEADSHOT)
    endif
    if RPGW_tem(src, RPGW_FURIA) and not RPGD_ev_crit then
        set f=1.0-GetWidgetLife(src)/I2R(BlzGetUnitMaxHP(src))
        if GetRandomReal(0.0, 1.0)<f*RPGW_pa(src, RPGW_FURIA) then
            set v=v*RPGD_mult_crit(src)
        endif
    endif
    if RPGW_tem(tgt, RPGW_BLOQUEIO) and GetRandomReal(0.0, 1.0)<RPGW_pa(tgt, RPGW_BLOQUEIO) then
        set v=v*(1.0-RPGW_pb(tgt, RPGW_BLOQUEIO))
    endif
    set e=LoadReal(RPGW_ht, GetHandleId(tgt), -30)
    if e>0.0 then
        if RPGW_agora>LoadReal(RPGW_ht, GetHandleId(tgt), -31) then
            call SaveReal(RPGW_ht, GetHandleId(tgt), -30, 0.0)
        elseif v<=e then
            call SaveReal(RPGW_ht, GetHandleId(tgt), -30, e-v)
            set RPGD_ev_texto=v
            set v=0.0
        else
            call SaveReal(RPGW_ht, GetHandleId(tgt), -30, 0.0)
            set v=v-e
        endif
    endif
    set RPGD_ev_valor=v
    if RPGW_tem(src, RPGW_ROUBO) and v>0.0 then
        set f=1.0-GetWidgetLife(src)/I2R(BlzGetUnitMaxHP(src))
        call SetWidgetLife(src, GetWidgetLife(src)+v*(RPGW_pa(src, RPGW_ROUBO)+f*(RPGW_pb(src, RPGW_ROUBO)-RPGW_pa(src, RPGW_ROUBO))))
    endif
    set src=null
    set tgt=null
    return false
endfunction

function RPGW_avancado takes unit h, boolean b returns nothing
    call SaveBoolean(RPGW_ht, GetHandleId(h), -40, b)
endfunction

function RPGW_sincroniza takes unit h returns nothing
    local integer tipo=GetUnitTypeId(h)
    local integer n=LoadInteger(RPGW_ht, tipo, -1)
    local integer i=1
    local integer abil
    local integer r
    local integer k
    local integer lv=GetHeroLevel(h)
    local integer max
    local boolean av=LoadBoolean(RPGW_ht, GetHandleId(h), -40)
    loop
        exitwhen i>n
        set abil=LoadInteger(RPGW_ht, tipo, -1-i)
        set r=0
        if LoadBoolean(RPGW_ht, tipo, -100-i) then
            set max=5
            set k=1
            loop
                exitwhen k>max
                if lv>=RPGW_lim_u[k] then
                    set r=k
                endif
                set k=k+1
            endloop
        else
            set max=10
            set k=1
            loop
                exitwhen k>max
                if lv>=RPGW_lim_b[k] then
                    set r=k
                endif
                set k=k+1
            endloop
        endif
        if av and r>0 then
            set r=r+1
        endif
        if r>0 then
            if GetUnitAbilityLevel(h, abil)==0 then
                call UnitAddAbility(h, abil)
                call UnitMakeAbilityPermanent(h, true, abil)
            endif
            call SaveInteger(RPGW_ht, GetHandleId(h), abil, r)
        endif
        set i=i+1
    endloop
endfunction

function RPGW_custos takes unit h returns nothing
    local integer tipo=GetUnitTypeId(h)
    local integer n=LoadInteger(RPGW_ht, tipo, -1)
    local integer i=1
    local integer abil
    loop
        exitwhen i>n
        set abil=LoadInteger(RPGW_ht, tipo, -1-i)
        if RPGW_v(abil, RPGW_P_MANA)>0.0 and GetUnitAbilityLevel(h, abil)>0 then
            call BlzSetUnitAbilityManaCost(h, abil, 0, R2I(GetUnitState(h, UNIT_STATE_MAX_MANA)*RPGW_v(abil, RPGW_P_MANA)))
        endif
        set i=i+1
    endloop
endfunction

function RPGW_rank takes unit h, integer abil returns integer
    return LoadInteger(RPGW_ht, GetHandleId(h), abil)
endfunction

function RPGW_nivel takes nothing returns nothing
    call RPGW_sincroniza(GetTriggerUnit())
endfunction

function RPGW_aura_cada takes nothing returns nothing
    local unit u=GetEnumUnit()
    local integer p=LoadInteger(RPGW_ht, -7, 0)
    local integer s=LoadInteger(RPGW_ht, GetUnitTypeId(RPGW_c_u), -600-p)
    if (p==RPGW_AURA_A and RPGW_aliado(RPGW_c_u, u)) or (p==RPGW_AURA_I and RPGW_inimigo(RPGW_c_u, u)) then
        call RPGW_buff(u, s, RPGW_pa(RPGW_c_u, p), 1.0)
    endif
    set u=null
endfunction

function RPGW_almas_cada takes nothing returns nothing
    local unit u=GetEnumUnit()
    if RPGW_tem(u, RPGW_ALMAS) and RPGW_vivo(u) then
        call SaveReal(RPGW_ht, GetHandleId(u), -20, RMinBJ(LoadReal(RPGW_ht, GetHandleId(u), -20)+1.0, RPGW_pb(u, RPGW_ALMAS)))
    endif
    set u=null
endfunction

function RPGW_morte takes nothing returns boolean
    local unit u=GetTriggerUnit()
    if IsUnitEnemy(u, Player(0)) then
        call RPGW_varre(GetUnitX(u), GetUnitY(u), 900.0, function RPGW_almas_cada)
    endif
    set u=null
    return false
endfunction

function RPGW_tiq takes nothing returns nothing
    local integer i=0
    local integer j
    local integer pid
    local unit h
    set RPGW_agora=RPGW_agora+RPGW_tique
    loop
        exitwhen i>=RPGW_bn
        if RPGW_agora>=RPGW_b_fim[i] or RPGW_b_u[i]==null or GetUnitTypeId(RPGW_b_u[i])==0 then
            if RPGW_b_u[i]!=null and GetUnitTypeId(RPGW_b_u[i])!=0 then
                call RPGW_aplica_stat(RPGW_b_u[i], RPGW_b_s[i], -RPGW_b_v[i])
            endif
            set RPGW_bn=RPGW_bn-1
            set RPGW_b_u[i]=RPGW_b_u[RPGW_bn]
            set RPGW_b_s[i]=RPGW_b_s[RPGW_bn]
            set RPGW_b_v[i]=RPGW_b_v[RPGW_bn]
            set RPGW_b_fim[i]=RPGW_b_fim[RPGW_bn]
            set RPGW_b_u[RPGW_bn]=null
        else
            set i=i+1
        endif
    endloop
    set i=0
    loop
        exitwhen i>=RPGW_zn
        if RPGW_agora>=RPGW_z_fim[i] or not RPGW_vivo(RPGW_z_u[i]) then
            if RPGW_z_fx[i]!=null then
                call DestroyEffect(RPGW_z_fx[i])
            endif
            set RPGW_zn=RPGW_zn-1
            set RPGW_z_u[i]=RPGW_z_u[RPGW_zn]
            set RPGW_z_a[i]=RPGW_z_a[RPGW_zn]
            set RPGW_z_r[i]=RPGW_z_r[RPGW_zn]
            set RPGW_z_x[i]=RPGW_z_x[RPGW_zn]
            set RPGW_z_y[i]=RPGW_z_y[RPGW_zn]
            set RPGW_z_fim[i]=RPGW_z_fim[RPGW_zn]
            set RPGW_z_prox[i]=RPGW_z_prox[RPGW_zn]
            set RPGW_z_reviveu[i]=RPGW_z_reviveu[RPGW_zn]
            set RPGW_z_fx[i]=RPGW_z_fx[RPGW_zn]
            set RPGW_z_u[RPGW_zn]=null
            set RPGW_z_fx[RPGW_zn]=null
        else
            if RPGW_agora>=RPGW_z_prox[i] then
                set RPGW_z_prox[i]=RPGW_agora+0.5
                set RPGW_c_u=RPGW_z_u[i]
                set RPGW_c_a=RPGW_z_a[i]
                set RPGW_c_r=RPGW_z_r[i]
                set RPGW_c_mult=1.0
                call SaveInteger(RPGW_ht, -8, 0, i)
                call RPGW_varre(RPGW_z_x[i], RPGW_z_y[i], RPGW_v(RPGW_z_a[i], RPGW_P_RAIO), function RPGW_zona_cada)
            endif
            set i=i+1
        endif
    endloop
    if ModuloInteger(R2I(RPGW_agora/RPGW_tique+0.5), 2)==0 then
        set i=0
        loop
            exitwhen i>=RPGW_dn
            if RPGW_d_n[i]<=0 or not RPGW_vivo(RPGW_d_tgt[i]) then
                set RPGW_dn=RPGW_dn-1
                set RPGW_d_src[i]=RPGW_d_src[RPGW_dn]
                set RPGW_d_tgt[i]=RPGW_d_tgt[RPGW_dn]
                set RPGW_d_v[i]=RPGW_d_v[RPGW_dn]
                set RPGW_d_n[i]=RPGW_d_n[RPGW_dn]
                set RPGW_d_src[RPGW_dn]=null
                set RPGW_d_tgt[RPGW_dn]=null
            else
                call RPGD_dano(RPGW_d_src[i], RPGW_d_tgt[i], RPGW_d_v[i], RPGD_T_SKILL)
                set RPGW_d_n[i]=RPGW_d_n[i]-1
                set i=i+1
            endif
        endloop
    endif
    if ModuloInteger(R2I(RPGW_agora/RPGW_tique+0.5), 4)==0 then
        set pid=0
        loop
            exitwhen pid>=RPGW_jogadores
            set h=RPGK_heroi[pid]
            if RPGW_vivo(h) then
                call RPGW_custos(h)
                set RPGW_c_u=h
                set j=RPGW_AURA_A
                loop
                    exitwhen j>RPGW_AURA_I
                    if RPGW_tem(h, j) then
                        call SaveInteger(RPGW_ht, -7, 0, j)
                        call RPGW_varre(GetUnitX(h), GetUnitY(h), RPGW_pb(h, j), function RPGW_aura_cada)
                    endif
                    set j=j+1
                endloop
            endif
            set pid=pid+1
        endloop
    endif
    set h=null
endfunction

function RPGW_init takes nothing returns nothing
    local integer i=0
    if RPGW_ht!=null then
        return
    endif
    set RPGW_ht=InitHashtable()
    set RPGW_g=CreateGroup()
    set RPGW_t_cast=CreateTrigger()
    set RPGW_t_nivel=CreateTrigger()
    set RPGW_t_morte=CreateTrigger()
    loop
        exitwhen i>=bj_MAX_PLAYER_SLOTS
        call TriggerRegisterPlayerUnitEvent(RPGW_t_morte, Player(i), EVENT_PLAYER_UNIT_DEATH, null)
        if i<RPGW_jogadores then
            call TriggerRegisterPlayerUnitEvent(RPGW_t_cast, Player(i), EVENT_PLAYER_UNIT_SPELL_EFFECT, null)
            call TriggerRegisterPlayerUnitEvent(RPGW_t_nivel, Player(i), EVENT_PLAYER_HERO_LEVEL, null)
        endif
        set i=i+1
    endloop
    call TriggerAddAction(RPGW_t_cast, function RPGW_cast)
    call TriggerAddAction(RPGW_t_nivel, function RPGW_nivel)
    call TriggerAddCondition(RPGW_t_morte, Condition(function RPGW_morte))
    call RPGD_gancho(function RPGW_gancho_dano)
    set RPGW_tm=CreateTimer()
    call TimerStart(RPGW_tm, RPGW_tique, true, function RPGW_tiq)
endfunction
