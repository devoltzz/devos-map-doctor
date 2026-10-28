//@GLOBALS
constant integer RPGX_MAX=96
constant integer RPGX_CIRC=1
constant integer RPGX_ROSCA=2
constant integer RPGX_LINHA=3
constant integer RPGX_CONE=4
constant integer RPGX_RODA=5
constant integer RPGX_ESPALHA=6
constant integer RPGX_JUNTA=7
constant integer RPGX_ZONA=8
constant integer RPGX_PUXA=9
constant integer RPGX_TANK=10
constant integer RPGX_CANAL=11
constant integer RPGX_G_CANAL=1
constant integer RPGX_G_TOTENS=2
real RPGX_tique=0.1
string RPGX_fx_chao="Doodads\\Cinematic\\GlowingRunes\\GlowingRunes0.mdl"
real RPGX_fx_raio=100.0
real RPGX_fx_passo=128.0
string RPGX_fx_marca="Abilities\\Spells\\Other\\TalkToMe\\TalkToMe.mdl"
string RPGX_fx_tank="Abilities\\Spells\\Other\\TalkToMe\\TalkToMe.mdl"
real RPGX_roda_cd=0.5
real RPGX_acum_mult=0.5
real RPGX_acum_dur=20.0
real RPGX_zona_alcance=4000.0
boolean RPGX_fica=false
hashtable RPGX_ht=null
timer RPGX_tm=null
real RPGX_agora=0.0
trigger array RPGX_tg
boolean array RPGX_tem
group RPGX_g=null
group RPGX_com_totem=null
integer array RPGX_i_tipo
unit array RPGX_i_boss
unit array RPGX_i_u
real array RPGX_i_x
real array RPGX_i_y
real array RPGX_i_a
real array RPGX_i_b
real array RPGX_i_ang
real array RPGX_i_c
real array RPGX_i_frac
real array RPGX_i_fim
real array RPGX_i_dur
integer array RPGX_i_n
integer array RPGX_i_nfx
real array RPGX_i_acc
boolean array RPGX_i_fica
unit RPGX_ev_boss=null
boolean RPGX_ev_ok=false
//@ENDGLOBALS

function RPGX_gancho takes integer qual, code f returns nothing
    if qual<1 or qual>8 then
        return
    endif
    call TriggerAddCondition(RPGX_tg[qual], Condition(f))
    set RPGX_tem[qual]=true
endfunction

function RPGX_chama takes integer qual, unit boss, boolean ok returns nothing
    if qual>=1 and qual<=8 and RPGX_tem[qual] then
        set RPGX_ev_boss=boss
        set RPGX_ev_ok=ok
        call TriggerEvaluate(RPGX_tg[qual])
    endif
endfunction

function RPGX_novo takes integer tipo, unit boss, real atraso, real frac returns integer
    local integer i=0
    loop
        exitwhen i>=RPGX_MAX
        if RPGX_i_tipo[i]==0 then
            set RPGX_i_tipo[i]=tipo
            set RPGX_i_boss[i]=boss
            set RPGX_i_u[i]=null
            set RPGX_i_frac[i]=frac
            set RPGX_i_fim[i]=RPGX_agora+atraso
            set RPGX_i_dur[i]=0.0
            set RPGX_i_nfx[i]=0
            set RPGX_i_acc[i]=0.0
            set RPGX_i_fica[i]=RPGX_fica
            set RPGX_fica=false
            call FlushChildHashtable(RPGX_ht, 1000+i)
            return i
        endif
        set i=i+1
    endloop
    return -1
endfunction

function RPGX_fx takes integer i, real x, real y, real escala returns nothing
    local effect e=AddSpecialEffect(RPGX_fx_chao, x, y)
    call BlzSetSpecialEffectScale(e, escala)
    call SaveEffectHandle(RPGX_ht, 1000+i, RPGX_i_nfx[i], e)
    set RPGX_i_nfx[i]=RPGX_i_nfx[i]+1
    set e=null
endfunction

function RPGX_fx_alvo takes integer i, unit u, string m returns nothing
    local effect e=AddSpecialEffectTarget(m, u, "overhead")
    call SaveEffectHandle(RPGX_ht, 1000+i, RPGX_i_nfx[i], e)
    set RPGX_i_nfx[i]=RPGX_i_nfx[i]+1
    set e=null
endfunction

function RPGX_fx_linha takes integer i, real x, real y, real ang, real comp returns nothing
    local real d=0.0
    local real r=ang*bj_DEGTORAD
    loop
        exitwhen d>comp
        call RPGX_fx(i, x+d*Cos(r), y+d*Sin(r), 0.6)
        set d=d+RPGX_fx_passo
    endloop
endfunction

function RPGX_fx_arco takes integer i, real x, real y, real raio, real a1, real a2 returns nothing
    local real passo
    local real a=a1
    if raio<1.0 then
        return
    endif
    set passo=RPGX_fx_passo/raio*bj_RADTODEG
    loop
        exitwhen a>a2
        call RPGX_fx(i, x+raio*Cos(a*bj_DEGTORAD), y+raio*Sin(a*bj_DEGTORAD), 0.6)
        set a=a+passo
    endloop
endfunction

function RPGX_fim takes integer i returns nothing
    local integer k=0
    local effect e
    loop
        exitwhen k>=RPGX_i_nfx[i]
        set e=LoadEffectHandle(RPGX_ht, 1000+i, k)
        if e!=null then
            call DestroyEffect(e)
        endif
        set k=k+1
    endloop
    call FlushChildHashtable(RPGX_ht, 1000+i)
    set RPGX_i_tipo[i]=0
    set RPGX_i_boss[i]=null
    set RPGX_i_u[i]=null
    set RPGX_i_nfx[i]=0
    set e=null
endfunction

function RPGX_alvo_ok takes unit boss, unit u returns boolean
    return u!=null and GetUnitTypeId(u)!=0 and not IsUnitType(u, UNIT_TYPE_DEAD) and not IsUnitType(u, UNIT_TYPE_STRUCTURE) and IsUnitEnemy(u, GetOwningPlayer(boss))
endfunction

function RPGX_bate takes unit boss, unit u, real frac returns nothing
    call RPGD_dano(boss, u, frac*I2R(BlzGetUnitMaxHP(u)), RPGD_T_PURO)
endfunction

function RPGX_ang_dif takes real a, real b returns real
    local real d=ModuloReal(a-b+180.0, 360.0)-180.0
    if d<0.0 then
        return -d
    endif
    return d
endfunction

function RPGX_na_linha takes unit u, real x, real y, real ang, real comp, real w returns boolean
    local real r=ang*bj_DEGTORAD
    local real dx=GetUnitX(u)-x
    local real dy=GetUnitY(u)-y
    local real t=dx*Cos(r)+dy*Sin(r)
    local real p=-dx*Sin(r)+dy*Cos(r)
    if p<0.0 then
        set p=-p
    endif
    return t>=0.0 and t<=comp and p<=w
endfunction

function RPGX_dist2 takes unit u, real x, real y returns real
    local real dx=GetUnitX(u)-x
    local real dy=GetUnitY(u)-y
    return dx*dx+dy*dy
endfunction

function RPGX_circulo takes unit boss, real x, real y, real raio, real atraso, real frac returns nothing
    local integer i=RPGX_novo(RPGX_CIRC, boss, atraso, frac)
    if i<0 then
        return
    endif
    set RPGX_i_x[i]=x
    set RPGX_i_y[i]=y
    set RPGX_i_a[i]=raio
    call RPGX_fx(i, x, y, raio/RPGX_fx_raio)
endfunction

function RPGX_rosca takes unit boss, real x, real y, real r_dentro, real r_fora, real atraso, real frac returns nothing
    local integer i=RPGX_novo(RPGX_ROSCA, boss, atraso, frac)
    if i<0 then
        return
    endif
    set RPGX_i_x[i]=x
    set RPGX_i_y[i]=y
    set RPGX_i_a[i]=r_dentro
    set RPGX_i_b[i]=r_fora
    call RPGX_fx_arco(i, x, y, r_dentro, 0.0, 359.0)
    call RPGX_fx_arco(i, x, y, r_fora, 0.0, 359.0)
endfunction

function RPGX_linha takes unit boss, real x, real y, real ang, real comp, real larg, real atraso, real frac returns nothing
    local integer i=RPGX_novo(RPGX_LINHA, boss, atraso, frac)
    if i<0 then
        return
    endif
    set RPGX_i_x[i]=x
    set RPGX_i_y[i]=y
    set RPGX_i_ang[i]=ang
    set RPGX_i_a[i]=comp
    set RPGX_i_b[i]=larg*0.5
    call RPGX_fx_linha(i, x, y, ang, comp)
endfunction

function RPGX_cone takes unit boss, real x, real y, real ang, real raio, real arco, real atraso, real frac returns nothing
    local integer i=RPGX_novo(RPGX_CONE, boss, atraso, frac)
    if i<0 then
        return
    endif
    set RPGX_i_x[i]=x
    set RPGX_i_y[i]=y
    set RPGX_i_ang[i]=ang
    set RPGX_i_a[i]=raio
    set RPGX_i_b[i]=arco*0.5
    call RPGX_fx_linha(i, x, y, ang-arco*0.5, raio)
    call RPGX_fx_linha(i, x, y, ang+arco*0.5, raio)
    call RPGX_fx_arco(i, x, y, raio, ang-arco*0.5, ang+arco*0.5)
endfunction

function RPGX_roda takes unit boss, integer raios, real comp, real larg, real vel, real atraso, real dur, real frac returns nothing
    local integer i=RPGX_novo(RPGX_RODA, boss, atraso, frac)
    local integer k=0
    if i<0 then
        return
    endif
    set RPGX_i_n[i]=raios
    set RPGX_i_a[i]=comp
    set RPGX_i_b[i]=larg*0.5
    set RPGX_i_c[i]=vel
    set RPGX_i_ang[i]=GetUnitFacing(boss)
    set RPGX_i_dur[i]=dur
    loop
        exitwhen k>=raios
        call RPGX_fx_linha(i, GetUnitX(boss), GetUnitY(boss), RPGX_i_ang[i]+360.0*I2R(k)/I2R(raios), comp)
        set k=k+1
    endloop
endfunction

function RPGX_espalha takes unit boss, unit u, real raio, real atraso, real frac returns nothing
    local integer i=RPGX_novo(RPGX_ESPALHA, boss, atraso, frac)
    if i<0 then
        return
    endif
    set RPGX_i_u[i]=u
    set RPGX_i_a[i]=raio
    call RPGX_fx_alvo(i, u, RPGX_fx_marca)
endfunction

function RPGX_junta takes unit boss, unit u, real raio, integer minimo, real atraso, real frac returns nothing
    local integer i=RPGX_novo(RPGX_JUNTA, boss, atraso, frac)
    if i<0 then
        return
    endif
    set RPGX_i_u[i]=u
    set RPGX_i_a[i]=raio
    set RPGX_i_n[i]=minimo
    call RPGX_fx_alvo(i, u, RPGX_fx_marca)
endfunction

function RPGX_zona takes unit boss, real x, real y, real raio, real atraso, real frac returns nothing
    local integer i=RPGX_novo(RPGX_ZONA, boss, atraso, frac)
    if i<0 then
        return
    endif
    set RPGX_i_x[i]=x
    set RPGX_i_y[i]=y
    set RPGX_i_a[i]=raio
    call RPGX_fx(i, x, y, raio/RPGX_fx_raio)
endfunction

function RPGX_puxa takes unit boss, real x, real y, real raio, real dist, real atraso returns nothing
    local integer i=RPGX_novo(RPGX_PUXA, boss, atraso, 0.0)
    if i<0 then
        return
    endif
    set RPGX_i_x[i]=x
    set RPGX_i_y[i]=y
    set RPGX_i_a[i]=raio
    set RPGX_i_b[i]=dist
    call RPGX_fx_arco(i, x, y, raio, 0.0, 359.0)
endfunction

function RPGX_acumulos takes unit u returns integer
    local integer h=GetHandleId(u)
    if LoadReal(RPGX_ht, h, 2)<RPGX_agora then
        return 0
    endif
    return LoadInteger(RPGX_ht, h, 1)
endfunction

function RPGX_golpe_tank takes unit boss, real frac, real atraso returns nothing
    local integer i
    local unit u=RPGA_alvo(boss)
    if u==null then
        set u=null
        return
    endif
    set i=RPGX_novo(RPGX_TANK, boss, atraso, frac)
    if i<0 then
        set u=null
        return
    endif
    set RPGX_i_u[i]=u
    call RPGX_fx_alvo(i, u, RPGX_fx_tank)
    set u=null
endfunction

function RPGX_canal takes unit boss, real dur, real quebra, real frac returns nothing
    local integer i=RPGX_novo(RPGX_CANAL, boss, dur, frac)
    if i<0 then
        return
    endif
    set RPGX_i_a[i]=quebra
    set RPGX_i_acc[i]=0.0
endfunction

function RPGX_canal_de takes unit boss returns integer
    local integer i=0
    loop
        exitwhen i>=RPGX_MAX
        if RPGX_i_tipo[i]==RPGX_CANAL and RPGX_i_boss[i]==boss then
            return i
        endif
        set i=i+1
    endloop
    return -1
endfunction

function RPGX_ondas takes unit boss, integer id, integer n, real x, real y, real raio returns group
    local group g=CreateGroup()
    local integer k=0
    local real a
    local unit u
    loop
        exitwhen k>=n
        set a=2.0*bj_PI*I2R(k)/I2R(n)
        set u=CreateUnit(GetOwningPlayer(boss), id, x+raio*Cos(a), y+raio*Sin(a), a*bj_RADTODEG)
        call GroupAddUnit(g, u)
        call IssuePointOrder(u, "attack", GetUnitX(boss), GetUnitY(boss))
        set k=k+1
    endloop
    set u=null
    return g
endfunction

function RPGX_totem takes unit boss, integer id, real x, real y returns unit
    local unit u=CreateUnit(GetOwningPlayer(boss), id, x, y, 270.0)
    local integer h=GetHandleId(boss)
    local group g=LoadGroupHandle(RPGX_ht, h, 3)
    if g==null then
        set g=CreateGroup()
        call SaveGroupHandle(RPGX_ht, h, 3, g)
    endif
    call GroupAddUnit(g, u)
    call SaveBoolean(RPGX_ht, h, 4, true)
    call GroupAddUnit(RPGX_com_totem, boss)
    set bj_lastCreatedUnit=u
    set u=null
    set g=null
    return bj_lastCreatedUnit
endfunction

function RPGX_resolve_cada takes nothing returns nothing
    local unit u=GetEnumUnit()
    local integer i=LoadInteger(RPGX_ht, 0, 1)
    local unit boss=RPGX_i_boss[i]
    local integer t=RPGX_i_tipo[i]
    local real d2
    local real ang
    local boolean leva=false
    if not RPGX_alvo_ok(boss, u) then
        set u=null
        set boss=null
        return
    endif
    if t==RPGX_CIRC then
        set leva=RPGX_dist2(u, RPGX_i_x[i], RPGX_i_y[i])<=RPGX_i_a[i]*RPGX_i_a[i]
    elseif t==RPGX_ROSCA then
        set d2=RPGX_dist2(u, RPGX_i_x[i], RPGX_i_y[i])
        set leva=d2>RPGX_i_a[i]*RPGX_i_a[i] and d2<=RPGX_i_b[i]*RPGX_i_b[i]
    elseif t==RPGX_LINHA then
        set leva=RPGX_na_linha(u, RPGX_i_x[i], RPGX_i_y[i], RPGX_i_ang[i], RPGX_i_a[i], RPGX_i_b[i])
    elseif t==RPGX_CONE then
        set ang=Atan2(GetUnitY(u)-RPGX_i_y[i], GetUnitX(u)-RPGX_i_x[i])*bj_RADTODEG
        set leva=RPGX_dist2(u, RPGX_i_x[i], RPGX_i_y[i])<=RPGX_i_a[i]*RPGX_i_a[i] and RPGX_ang_dif(ang, RPGX_i_ang[i])<=RPGX_i_b[i]
    elseif t==RPGX_ZONA then
        set leva=RPGX_dist2(u, RPGX_i_x[i], RPGX_i_y[i])>RPGX_i_a[i]*RPGX_i_a[i]
    elseif t==RPGX_ESPALHA then
        set leva=RPGX_dist2(u, RPGX_i_x[i], RPGX_i_y[i])<=RPGX_i_a[i]*RPGX_i_a[i]
    elseif t==RPGX_JUNTA then
        set leva=RPGX_dist2(u, RPGX_i_x[i], RPGX_i_y[i])<=RPGX_i_a[i]*RPGX_i_a[i]
    elseif t==RPGX_CANAL then
        set leva=true
    elseif t==RPGX_PUXA then
        set d2=RPGX_dist2(u, RPGX_i_x[i], RPGX_i_y[i])
        if d2<=RPGX_i_a[i]*RPGX_i_a[i] and d2>1.0 then
            set ang=Atan2(RPGX_i_y[i]-GetUnitY(u), RPGX_i_x[i]-GetUnitX(u))
            set d2=SquareRoot(d2)
            if RPGX_i_b[i]>0.0 and RPGX_i_b[i]>d2 then
                call SetUnitPosition(u, RPGX_i_x[i], RPGX_i_y[i])
            else
                call SetUnitPosition(u, GetUnitX(u)+RPGX_i_b[i]*Cos(ang), GetUnitY(u)+RPGX_i_b[i]*Sin(ang))
            endif
        endif
    endif
    if leva and t!=RPGX_PUXA then
        if t==RPGX_JUNTA then
            call RPGX_bate(boss, u, RPGX_i_frac[i]*I2R(RPGX_i_n[i])/RPGX_i_c[i])
        else
            call RPGX_bate(boss, u, RPGX_i_frac[i])
        endif
    endif
    set u=null
    set boss=null
endfunction

function RPGX_conta_cada takes nothing returns nothing
    local integer i=LoadInteger(RPGX_ht, 0, 1)
    if RPGX_alvo_ok(RPGX_i_boss[i], GetEnumUnit()) and RPGX_dist2(GetEnumUnit(), RPGX_i_x[i], RPGX_i_y[i])<=RPGX_i_a[i]*RPGX_i_a[i] then
        set RPGX_i_c[i]=RPGX_i_c[i]+1.0
    endif
endfunction

function RPGX_varre takes integer i, code f returns nothing
    local unit boss=RPGX_i_boss[i]
    call SaveInteger(RPGX_ht, 0, 1, i)
    if RPGX_i_fica[i] then
        call GroupEnumUnitsInRange(RPGX_g, RPGX_i_x[i], RPGX_i_y[i], RPGX_zona_alcance, null)
        call ForGroup(RPGX_g, f)
        call GroupClear(RPGX_g)
        set boss=null
        return
    endif
    call GroupEnumUnitsInRange(RPGX_g, GetUnitX(boss), GetUnitY(boss), RPGX_zona_alcance, null)
    call ForGroup(RPGX_g, f)
    call GroupClear(RPGX_g)
    set boss=null
endfunction

function RPGX_resolve takes integer i returns nothing
    local integer t=RPGX_i_tipo[i]
    local unit u
    local integer h
    if t==RPGX_ESPALHA or t==RPGX_JUNTA then
        set RPGX_i_x[i]=GetUnitX(RPGX_i_u[i])
        set RPGX_i_y[i]=GetUnitY(RPGX_i_u[i])
        if t==RPGX_JUNTA then
            set RPGX_i_c[i]=0.0
            call RPGX_varre(i, function RPGX_conta_cada)
            if RPGX_i_c[i]<1.0 then
                set RPGX_i_c[i]=1.0
            endif
        endif
    endif
    if t==RPGX_TANK then
        set u=RPGX_i_u[i]
        if RPGX_alvo_ok(RPGX_i_boss[i], u) then
            call RPGX_bate(RPGX_i_boss[i], u, RPGX_i_frac[i]*(1.0+I2R(RPGX_acumulos(u))*RPGX_acum_mult))
            set h=GetHandleId(u)
            call SaveInteger(RPGX_ht, h, 1, RPGX_acumulos(u)+1)
            call SaveReal(RPGX_ht, h, 2, RPGX_agora+RPGX_acum_dur)
        endif
        set u=null
    elseif t==RPGX_CANAL then
        if RPGX_i_acc[i]>=RPGX_i_a[i] then
            call RPGX_chama(RPGX_G_CANAL, RPGX_i_boss[i], true)
        else
            call RPGX_varre(i, function RPGX_resolve_cada)
            call RPGX_chama(RPGX_G_CANAL, RPGX_i_boss[i], false)
        endif
    else
        call RPGX_varre(i, function RPGX_resolve_cada)
    endif
endfunction

function RPGX_roda_cada takes nothing returns nothing
    local unit u=GetEnumUnit()
    local integer i=LoadInteger(RPGX_ht, 0, 1)
    local unit boss=RPGX_i_boss[i]
    local integer k=0
    local integer chave
    if RPGX_alvo_ok(boss, u) then
        set chave=GetHandleId(u)
        if LoadReal(RPGX_ht, 1000+i, -chave)<=RPGX_agora then
            loop
                exitwhen k>=RPGX_i_n[i]
                if RPGX_na_linha(u, GetUnitX(boss), GetUnitY(boss), RPGX_i_ang[i]+360.0*I2R(k)/I2R(RPGX_i_n[i]), RPGX_i_a[i], RPGX_i_b[i]) then
                    call RPGX_bate(boss, u, RPGX_i_frac[i])
                    call SaveReal(RPGX_ht, 1000+i, -chave, RPGX_agora+RPGX_roda_cd)
                    set k=RPGX_i_n[i]
                endif
                set k=k+1
            endloop
        endif
    endif
    set u=null
    set boss=null
endfunction

function RPGX_roda_anda takes integer i returns nothing
    local unit boss=RPGX_i_boss[i]
    local integer k=0
    local integer f=0
    local integer por
    local real d
    local real a
    local effect e
    call RPGX_varre(i, function RPGX_roda_cada)
    set RPGX_i_ang[i]=RPGX_i_ang[i]+RPGX_i_c[i]*RPGX_tique
    if RPGX_i_n[i]>0 then
        set por=RPGX_i_nfx[i]/RPGX_i_n[i]
        loop
            exitwhen k>=RPGX_i_n[i]
            set a=(RPGX_i_ang[i]+360.0*I2R(k)/I2R(RPGX_i_n[i]))*bj_DEGTORAD
            set d=0.0
            set f=0
            loop
                exitwhen f>=por
                set e=LoadEffectHandle(RPGX_ht, 1000+i, k*por+f)
                if e!=null then
                    call BlzSetSpecialEffectPosition(e, GetUnitX(boss)+d*Cos(a), GetUnitY(boss)+d*Sin(a), 0.0)
                endif
                set d=d+RPGX_fx_passo
                set f=f+1
            endloop
            set k=k+1
        endloop
    endif
    set boss=null
    set e=null
endfunction

function RPGX_gancho_dano takes nothing returns boolean
    local integer i
    if RPGD_ev_tipo==RPGD_T_CURA or RPGD_ev_tgt==null then
        return false
    endif
    set i=RPGX_canal_de(RPGD_ev_tgt)
    if i>=0 then
        if RPGD_ev_texto>=0.0 then
            set RPGX_i_acc[i]=RPGX_i_acc[i]+RPGD_ev_texto
        else
            set RPGX_i_acc[i]=RPGX_i_acc[i]+RPGD_ev_valor
        endif
        if RPGX_i_acc[i]>=RPGX_i_a[i] then
            call RPGX_chama(RPGX_G_CANAL, RPGX_i_boss[i], true)
            call RPGX_fim(i)
        endif
    endif
    return false
endfunction

function RPGX_totens_cada takes nothing returns nothing
    if not IsUnitType(GetEnumUnit(), UNIT_TYPE_DEAD) and GetUnitTypeId(GetEnumUnit())!=0 then
        call SaveBoolean(RPGX_ht, 0, 2, true)
    endif
endfunction

function RPGX_totens_vivos takes unit boss returns boolean
    local integer h=GetHandleId(boss)
    local group g=LoadGroupHandle(RPGX_ht, h, 3)
    if g==null then
        return false
    endif
    call SaveBoolean(RPGX_ht, 0, 2, false)
    call ForGroup(g, function RPGX_totens_cada)
    if not LoadBoolean(RPGX_ht, 0, 2) and LoadBoolean(RPGX_ht, h, 4) then
        call SaveBoolean(RPGX_ht, h, 4, false)
        call GroupClear(g)
        call RPGX_chama(RPGX_G_TOTENS, boss, true)
    endif
    set g=null
    return LoadBoolean(RPGX_ht, 0, 2)
endfunction

function RPGX_totens_tiq takes nothing returns nothing
    if not RPGX_totens_vivos(GetEnumUnit()) then
        call GroupRemoveUnit(RPGX_com_totem, GetEnumUnit())
    endif
endfunction

function RPGX_tiq takes nothing returns nothing
    local integer i=0
    set RPGX_agora=RPGX_agora+RPGX_tique
    loop
        exitwhen i>=RPGX_MAX
        if RPGX_i_tipo[i]!=0 then
            if RPGX_i_boss[i]==null or (IsUnitType(RPGX_i_boss[i], UNIT_TYPE_DEAD) and not RPGX_i_fica[i]) then
                call RPGX_fim(i)
            elseif RPGX_agora>=RPGX_i_fim[i] then
                if RPGX_i_tipo[i]==RPGX_RODA then
                    if RPGX_agora>=RPGX_i_fim[i]+RPGX_i_dur[i] then
                        call RPGX_fim(i)
                    else
                        call RPGX_roda_anda(i)
                    endif
                else
                    call RPGX_resolve(i)
                    call RPGX_fim(i)
                endif
            endif
        endif
        set i=i+1
    endloop
    call ForGroup(RPGX_com_totem, function RPGX_totens_tiq)
endfunction

function RPGX_init takes nothing returns nothing
    local integer i=1
    if RPGX_ht!=null then
        return
    endif
    set RPGX_ht=InitHashtable()
    set RPGX_g=CreateGroup()
    set RPGX_com_totem=CreateGroup()
    loop
        exitwhen i>8
        set RPGX_tg[i]=CreateTrigger()
        set i=i+1
    endloop
    call RPGD_gancho(function RPGX_gancho_dano)
    set RPGX_tm=CreateTimer()
    call TimerStart(RPGX_tm, RPGX_tique, true, function RPGX_tiq)
endfunction
