//@GLOBALS
constant integer RPGB_CIRC=1
constant integer RPGB_SERIE=2
constant integer RPGB_ROSCA=3
constant integer RPGB_LINHA=4
constant integer RPGB_CONE=5
constant integer RPGB_RODA=6
constant integer RPGB_ESPALHA=7
constant integer RPGB_JUNTA=8
constant integer RPGB_ZONA=9
constant integer RPGB_PUXA=10
constant integer RPGB_TANK=11
constant integer RPGB_CANAL=12
constant integer RPGB_ONDAS=13
constant integer RPGB_TOTEM=14
constant integer RPGB_ESCUDO=15
constant integer RPGB_MAXI=48
constant integer RPGB_MAXG=24
real RPGB_tique=0.5
real RPGB_gcd=3.0
real RPGB_alcance=1800.0
real RPGB_aggro=900.0
real RPGB_roda_comp=1400.0
real RPGB_roda_larg=120.0
real RPGB_zona_dist=600.0
hashtable RPGB_ht=null
timer RPGB_tm=null
group RPGB_g=null
real RPGB_agora=0.0
unit array RPGB_i_u
integer array RPGB_i_fase
integer array RPGB_i_vez
real array RPGB_i_livre
integer RPGB_n=0
unit RPGB_c_boss=null
unit RPGB_c_alvo=null
trigger RPGB_t_entra=null
region RPGB_rg=null
//@ENDGLOBALS

function RPGB_fase takes integer tipo, real frac returns nothing
    local integer n=LoadInteger(RPGB_ht, tipo, -2)
    call SaveReal(RPGB_ht, tipo, -100-n, frac)
    call SaveInteger(RPGB_ht, tipo, -2, n+1)
endfunction

function RPGB_enrage takes integer tipo, real seg returns nothing
    call SaveReal(RPGB_ht, tipo, -3, seg)
endfunction

function RPGB_campo takes integer tipo returns nothing
    call SaveBoolean(RPGB_ht, tipo, -4, true)
endfunction

function RPGB_afixos takes integer tipo, integer n returns nothing
    call SaveInteger(RPGB_ht, tipo, -5, n)
endfunction

function RPGB_golpe takes integer tipo, integer fmin, integer fmax, integer peca, real cad, integer id, real a, real b, real c, real atraso, real frac returns nothing
    local integer n=LoadInteger(RPGB_ht, tipo, -1)
    local integer k
    if n>=RPGB_MAXG then
        return
    endif
    set k=n*16
    call SaveInteger(RPGB_ht, tipo, k+1, fmin)
    call SaveInteger(RPGB_ht, tipo, k+2, fmax)
    call SaveInteger(RPGB_ht, tipo, k+3, peca)
    call SaveReal(RPGB_ht, tipo, k+4, cad)
    call SaveInteger(RPGB_ht, tipo, k+5, id)
    call SaveReal(RPGB_ht, tipo, k+6, a)
    call SaveReal(RPGB_ht, tipo, k+7, b)
    call SaveReal(RPGB_ht, tipo, k+8, c)
    call SaveReal(RPGB_ht, tipo, k+9, atraso)
    call SaveReal(RPGB_ht, tipo, k+10, frac)
    call SaveInteger(RPGB_ht, tipo, -1, n+1)
endfunction

function RPGB_vivo takes unit u returns boolean
    return u!=null and GetUnitTypeId(u)!=0 and not IsUnitType(u, UNIT_TYPE_DEAD)
endfunction

function RPGB_perto_cada takes nothing returns nothing
    local unit u=GetEnumUnit()
    if RPGB_c_alvo==null and RPGB_vivo(u) and IsUnitType(u, UNIT_TYPE_HERO) and IsUnitEnemy(u, GetOwningPlayer(RPGB_c_boss)) then
        set RPGB_c_alvo=u
    endif
    set u=null
endfunction

function RPGB_perto takes unit boss, real raio returns unit
    set RPGB_c_boss=boss
    set RPGB_c_alvo=null
    call GroupEnumUnitsInRange(RPGB_g, GetUnitX(boss), GetUnitY(boss), raio, null)
    call ForGroup(RPGB_g, function RPGB_perto_cada)
    call GroupClear(RPGB_g)
    return RPGB_c_alvo
endfunction

function RPGB_alvo takes unit boss returns unit
    local unit u=RPGA_outro(boss)
    if not RPGB_vivo(u) then
        set u=RPGA_alvo(boss)
    endif
    if not RPGB_vivo(u) then
        set u=RPGB_perto(boss, RPGB_alcance)
    endif
    return u
endfunction

function RPGB_ang takes unit boss, unit u returns real
    if u==null then
        return GetUnitFacing(boss)
    endif
    return Atan2(GetUnitY(u)-GetUnitY(boss), GetUnitX(u)-GetUnitX(boss))*bj_RADTODEG
endfunction

function RPGB_falta takes unit boss returns real
    if RPGC_slot(boss)>=0 then
        return RPGC_resta(boss)
    endif
    return GetWidgetLife(boss)
endfunction

function RPGB_faz takes unit boss, integer tipo, integer i returns nothing
    local integer k=i*16
    local integer peca=LoadInteger(RPGB_ht, tipo, k+3)
    local integer id=LoadInteger(RPGB_ht, tipo, k+5)
    local real a=LoadReal(RPGB_ht, tipo, k+6)
    local real b=LoadReal(RPGB_ht, tipo, k+7)
    local real c=LoadReal(RPGB_ht, tipo, k+8)
    local real atraso=LoadReal(RPGB_ht, tipo, k+9)
    local real frac=LoadReal(RPGB_ht, tipo, k+10)
    local real bx=GetUnitX(boss)
    local real by=GetUnitY(boss)
    local unit u
    local integer j
    local integer n
    local real ang
    local real d
    if peca==RPGB_CIRC then
        set n=IMaxBJ(1, R2I(b))
        set j=0
        loop
            exitwhen j>=n
            set u=RPGB_alvo(boss)
            if u!=null then
                call RPGX_circulo(boss, GetUnitX(u), GetUnitY(u), a, atraso, frac)
            endif
            set j=j+1
        endloop
    elseif peca==RPGB_SERIE then
        set u=RPGB_alvo(boss)
        set ang=RPGB_ang(boss, u)*bj_DEGTORAD
        set n=IMaxBJ(1, R2I(b))
        set j=0
        loop
            exitwhen j>=n
            set d=a*1.5*I2R(j+1)
            call RPGX_circulo(boss, bx+d*Cos(ang), by+d*Sin(ang), a, atraso+0.4*I2R(j), frac)
            set j=j+1
        endloop
    elseif peca==RPGB_ROSCA then
        call RPGX_rosca(boss, bx, by, a, b, atraso, frac)
    elseif peca==RPGB_LINHA then
        set u=RPGB_alvo(boss)
        set ang=RPGB_ang(boss, u)
        set n=IMaxBJ(1, R2I(c))
        set j=0
        loop
            exitwhen j>=n
            call RPGX_linha(boss, bx, by, ang+25.0*(I2R(j)-I2R(n-1)*0.5), a, b, atraso, frac)
            set j=j+1
        endloop
    elseif peca==RPGB_CONE then
        set u=RPGB_alvo(boss)
        call RPGX_cone(boss, bx, by, RPGB_ang(boss, u), a, b, atraso, frac)
    elseif peca==RPGB_RODA then
        call RPGX_roda(boss, IMaxBJ(1, R2I(a)), RPGB_roda_comp, RPGB_roda_larg, b, atraso, c, frac)
    elseif peca==RPGB_ESPALHA then
        set n=IMaxBJ(1, R2I(b))
        set j=0
        loop
            exitwhen j>=n
            set u=RPGB_alvo(boss)
            if u!=null then
                call RPGX_espalha(boss, u, a, atraso, frac)
            endif
            set j=j+1
        endloop
    elseif peca==RPGB_JUNTA then
        set u=RPGB_alvo(boss)
        if u!=null then
            call RPGX_junta(boss, u, a, IMaxBJ(1, R2I(b)), atraso, frac)
        endif
    elseif peca==RPGB_ZONA then
        set ang=GetRandomReal(0.0, 2.0*bj_PI)
        call RPGX_zona(boss, bx+RPGB_zona_dist*Cos(ang), by+RPGB_zona_dist*Sin(ang), a, atraso, frac)
    elseif peca==RPGB_PUXA then
        call RPGX_puxa(boss, bx, by, a, b, atraso)
    elseif peca==RPGB_TANK then
        call RPGX_golpe_tank(boss, frac, atraso)
    elseif peca==RPGB_CANAL then
        call RPGX_canal(boss, a, b*RPGB_falta(boss), frac)
    elseif peca==RPGB_ONDAS then
        call DestroyGroup(RPGX_ondas(boss, id, IMaxBJ(1, R2I(a)), bx, by, 400.0))
    elseif peca==RPGB_TOTEM then
        set n=IMaxBJ(1, R2I(a))
        set j=0
        loop
            exitwhen j>=n
            set ang=2.0*bj_PI*I2R(j)/I2R(n)
            call RPGX_totem(boss, id, bx+b*Cos(ang), by+b*Sin(ang))
            set j=j+1
        endloop
    elseif peca==RPGB_ESCUDO then
        if RPGC_slot(boss)>=0 then
            call RPGC_escudo(boss, a*RPGB_falta(boss), b)
        endif
    endif
    set u=null
endfunction

function RPGB_entra takes integer i, integer f returns nothing
    local unit boss=RPGB_i_u[i]
    local integer tipo=GetUnitTypeId(boss)
    local integer n=LoadInteger(RPGB_ht, tipo, -1)
    local integer j=0
    set RPGB_i_fase[i]=f
    loop
        exitwhen j>=n
        if LoadReal(RPGB_ht, tipo, j*16+4)<0.0 and LoadInteger(RPGB_ht, tipo, j*16+1)==f then
            call RPGB_faz(boss, tipo, j)
        endif
        set j=j+1
    endloop
    set boss=null
endfunction

function RPGB_slot takes unit boss returns integer
    local integer i=0
    loop
        exitwhen i>=RPGB_n
        if RPGB_i_u[i]==boss then
            return i
        endif
        set i=i+1
    endloop
    return -1
endfunction

function RPGB_comeca takes unit boss returns nothing
    local integer tipo=GetUnitTypeId(boss)
    local integer i
    local integer j=0
    local integer nf=LoadInteger(RPGB_ht, tipo, -2)
    if boss==null or RPGB_slot(boss)>=0 or RPGB_n>=RPGB_MAXI then
        return
    endif
    set i=RPGB_n
    set RPGB_n=i+1
    set RPGB_i_u[i]=boss
    set RPGB_i_vez[i]=0
    set RPGB_i_livre[i]=RPGB_agora+RPGB_gcd
    loop
        exitwhen j>=LoadInteger(RPGB_ht, tipo, -1)
        call SaveReal(RPGB_ht, GetHandleId(boss), j, RPGB_agora+RAbsBJ(LoadReal(RPGB_ht, tipo, j*16+4))*0.5)
        set j=j+1
    endloop
    if RPGA_slot(boss)<0 then
        call RPGA_registra(boss)
    endif
    if RPGC_slot(boss)>=0 then
        set j=0
        loop
            exitwhen j>=nf
            call RPGC_fase(boss, LoadReal(RPGB_ht, tipo, -100-j))
            set j=j+1
        endloop
        if LoadReal(RPGB_ht, tipo, -3)>0.0 then
            call RPGC_enrage(boss, LoadReal(RPGB_ht, tipo, -3))
        endif
    endif
    call RPGB_entra(i, 1)
endfunction

function RPGB_tira takes integer i returns nothing
    call FlushChildHashtable(RPGB_ht, GetHandleId(RPGB_i_u[i]))
    set RPGB_n=RPGB_n-1
    set RPGB_i_u[i]=RPGB_i_u[RPGB_n]
    set RPGB_i_fase[i]=RPGB_i_fase[RPGB_n]
    set RPGB_i_vez[i]=RPGB_i_vez[RPGB_n]
    set RPGB_i_livre[i]=RPGB_i_livre[RPGB_n]
    set RPGB_i_u[RPGB_n]=null
endfunction

function RPGB_para takes unit boss returns nothing
    local integer i=RPGB_slot(boss)
    if i>=0 then
        call RPGB_tira(i)
    endif
endfunction

function RPGB_gancho_fase takes nothing returns boolean
    local integer i=RPGB_slot(RPGC_ev_boss)
    if i>=0 then
        call RPGB_entra(i, RPGC_ev_fase+1)
    endif
    return false
endfunction

function RPGB_afixa takes unit u returns nothing
    local integer n=LoadInteger(RPGB_ht, GetUnitTypeId(u), -5)
    if n>0 and RPGB_vivo(u) and RPGF_mascara(u)==0 then
        call RPGF_aplica(u, n)
    endif
endfunction

function RPGB_entrou takes nothing returns boolean
    call RPGB_afixa(GetTriggerUnit())
    return false
endfunction

function RPGB_afixa_cada takes nothing returns nothing
    call RPGB_afixa(GetEnumUnit())
endfunction

function RPGB_um takes integer i returns nothing
    local unit boss=RPGB_i_u[i]
    local integer tipo=GetUnitTypeId(boss)
    local integer n=LoadInteger(RPGB_ht, tipo, -1)
    local integer h=GetHandleId(boss)
    local integer t=0
    local integer j
    local integer k
    local integer f=RPGB_i_fase[i]
    local integer fmax
    local real cad
    if RPGB_agora<RPGB_i_livre[i] or n==0 or RPGB_perto(boss, RPGB_alcance)==null then
        set boss=null
        return
    endif
    loop
        exitwhen t>=n
        set j=ModuloInteger(RPGB_i_vez[i]+t, n)
        set k=j*16
        set cad=LoadReal(RPGB_ht, tipo, k+4)
        set fmax=LoadInteger(RPGB_ht, tipo, k+2)
        if cad>0.0 and f>=LoadInteger(RPGB_ht, tipo, k+1) and (fmax==0 or f<=fmax) and RPGB_agora>=LoadReal(RPGB_ht, h, j) then
            call RPGB_faz(boss, tipo, j)
            call SaveReal(RPGB_ht, h, j, RPGB_agora+cad)
            set RPGB_i_livre[i]=RPGB_agora+RPGB_gcd
            set RPGB_i_vez[i]=j+1
            set boss=null
            return
        endif
        set t=t+1
    endloop
    set boss=null
endfunction

function RPGB_campo_cada takes nothing returns nothing
    local unit u=GetEnumUnit()
    if RPGB_vivo(u) and LoadBoolean(RPGB_ht, GetUnitTypeId(u), -4) and RPGB_slot(u)<0 and RPGB_perto(u, RPGB_aggro)!=null then
        call RPGB_comeca(u)
    endif
    set u=null
endfunction

function RPGB_tiq takes nothing returns nothing
    local integer i=0
    local group g
    set RPGB_agora=RPGB_agora+RPGB_tique
    if RPGB_agora<=RPGB_tique*1.5 then
        set g=CreateGroup()
        call GroupEnumUnitsInRect(g, GetWorldBounds(), null)
        call ForGroup(g, function RPGB_afixa_cada)
        call DestroyGroup(g)
        set g=null
    endif
    loop
        exitwhen i>=RPGB_n
        if not RPGB_vivo(RPGB_i_u[i]) then
            call RPGB_tira(i)
        else
            call RPGB_um(i)
            set i=i+1
        endif
    endloop
    if ModuloInteger(R2I(RPGB_agora/RPGB_tique+0.5), 4)==0 then
        set g=CreateGroup()
        call GroupEnumUnitsOfPlayer(g, Player(PLAYER_NEUTRAL_AGGRESSIVE), null)
        call ForGroup(g, function RPGB_campo_cada)
        call GroupClear(g)
        call GroupEnumUnitsOfPlayer(g, Player(11), null)
        call ForGroup(g, function RPGB_campo_cada)
        call DestroyGroup(g)
        set g=null
    endif
endfunction

function RPGB_init takes nothing returns nothing
    if RPGB_ht!=null then
        return
    endif
    set RPGB_ht=InitHashtable()
    set RPGB_g=CreateGroup()
    call RPGC_gancho(RPGC_G_FASE, function RPGB_gancho_fase)
    set RPGB_rg=CreateRegion()
    set RPGB_t_entra=CreateTrigger()
    call TriggerRegisterEnterRegion(RPGB_t_entra, RPGB_rg, null)
    call RegionAddRect(RPGB_rg, GetWorldBounds())
    call TriggerAddCondition(RPGB_t_entra, Condition(function RPGB_entrou))
    set RPGB_tm=CreateTimer()
    call TimerStart(RPGB_tm, RPGB_tique, true, function RPGB_tiq)
endfunction
