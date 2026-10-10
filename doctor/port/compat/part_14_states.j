hashtable DB_est_ht=null
constant integer DB_EST_TIPO=0
constant integer DB_EST_BONUS=1
constant integer DB_EST_VEL=2
constant integer DB_EST_COOL=3
constant integer DB_EST_ALC=4
constant real DB_ASPD_MIN=-0.8
constant real DB_ASPD_MAX=4.0
trigger DB_aspd_trg=null
unit DB_aspd_u=null
real DB_aspd_piso_v=0.0

function DB_est_garante takes nothing returns nothing
    if DB_est_ht==null then
        set DB_est_ht=InitHashtable()
    endif
endfunction

function DB_est_h takes unit u returns integer
    local integer h=GetHandleId(u)
    local integer t=GetUnitTypeId(u)
    call DB_est_garante()
    if HaveSavedInteger(DB_est_ht,h,DB_EST_TIPO) then
        if LoadInteger(DB_est_ht,h,DB_EST_TIPO)==t then
            return h
        endif
        //{{KK_SE:KK_MORFO_ESTADO}}
        if HaveSavedInteger(DB_est_ht,h,DB_EST_MORFO) then
            call DB_morfo_volta(u,h)
            return h
        endif
        //{{KK_FIMSE:KK_MORFO_ESTADO}}
        call FlushChildHashtable(DB_est_ht,h)
    endif
    call SaveInteger(DB_est_ht,h,DB_EST_TIPO,t)
    return h
endfunction

function DB_est_esquece takes unit u returns nothing
    if u==null or DB_est_ht==null then
        return
    endif
    call FlushChildHashtable(DB_est_ht,GetHandleId(u))
endfunction

function DB_est_piso takes real x returns integer
    local integer i
    if x>=2147483000.0 then
        return 2147483000
    elseif x<=-2147483000.0 then
        return -2147483000
    endif
    set i=R2I(x)
    if I2R(i)>x then
        set i=i-1
    endif
    return i
endfunction

function DB_est_arred takes real x returns integer
    return DB_est_piso(x+0.5)
endfunction

function DB_est_trunca takes real x returns integer
    if x>=2147483000.0 then
        return 2147483000
    elseif x<=-2147483000.0 then
        return -2147483000
    endif
    return R2I(x)
endfunction

function DB_estado_max_vida takes unit u,real v returns nothing
    local real atual
    local real maxv
    local integer n
    //{{KK_SE:KK_EST_VIDA_GRANDE}}
    local real k
    //{{KK_FIMSE:KK_EST_VIDA_GRANDE}}
    if u==null then
        return
    endif
    //{{KK_SE:KK_MORFO_ESTADO}}
    call DB_morfo_confere(u)
    //{{KK_FIMSE:KK_MORFO_ESTADO}}
    set atual=GetUnitState(u,UNIT_STATE_LIFE)
    set maxv=GetUnitState(u,UNIT_STATE_MAX_LIFE)
    set n=DB_est_arred(v)
    if n<1 then
        set n=1
    endif
    //{{KK_SE:KK_EST_VIDA_GRANDE}}
    if maxv>1000000.0 and I2R(n)*10.0<maxv then
        set k=maxv
        loop
            set k=k/10.0
            exitwhen k<=I2R(n)
            call BlzSetUnitMaxHP(u,R2I(k))
            call SetUnitState(u,UNIT_STATE_LIFE,RMinBJ(GetUnitState(u,UNIT_STATE_LIFE),k))
        endloop
    endif
    //{{KK_FIMSE:KK_EST_VIDA_GRANDE}}
    call BlzSetUnitMaxHP(u,n)
    if maxv>0.0 and atual>0.0 then
        if atual<v then
            call SetUnitState(u,UNIT_STATE_LIFE,atual)
        else
            call SetUnitState(u,UNIT_STATE_LIFE,v)
        endif
    endif
    //{{KK_SE:KK_MORFO_ESTADO}}
    call DB_morfo_refoto(u)
    //{{KK_FIMSE:KK_MORFO_ESTADO}}
endfunction

function DB_estado_max_mana takes unit u,real v returns nothing
    local real atual
    local integer n
    if u==null then
        return
    endif
    //{{KK_SE:KK_MORFO_ESTADO}}
    call DB_morfo_confere(u)
    //{{KK_FIMSE:KK_MORFO_ESTADO}}
    set atual=GetUnitState(u,UNIT_STATE_MANA)
    set n=DB_est_arred(v)
    if n<0 then
        set n=0
    endif
    call BlzSetUnitMaxMana(u,n)
    if atual<v then
        call SetUnitState(u,UNIT_STATE_MANA,atual)
    else
        call SetUnitState(u,UNIT_STATE_MANA,v)
    endif
    //{{KK_SE:KK_MORFO_ESTADO}}
    call DB_morfo_refoto(u)
    //{{KK_FIMSE:KK_MORFO_ESTADO}}
endfunction

function DB_aspd_fator takes real v returns real
    if v<DB_ASPD_MIN then
        set v=DB_ASPD_MIN
    elseif v>DB_ASPD_MAX then
        set v=DB_ASPD_MAX
    endif
    return 1.0+v
endfunction

function DB_aspd_base takes unit u,integer h returns real
    local real c
    if HaveSavedReal(DB_est_ht,h,DB_EST_COOL) then
        return LoadReal(DB_est_ht,h,DB_EST_COOL)
    endif
    set c=BlzGetUnitAttackCooldown(u,0)
    call SaveReal(DB_est_ht,h,DB_EST_COOL,c)
    return c
endfunction

function DB_aspd_piso takes unit u returns real
    if DB_aspd_trg==null or u==null then
        return 0.0
    endif
    set DB_aspd_u=u
    set DB_aspd_piso_v=0.0
    call TriggerEvaluate(DB_aspd_trg)
    set DB_aspd_u=null
    return DB_aspd_piso_v
endfunction

function DB_aspd_aplica takes unit u,integer h returns nothing
    local real b=DB_aspd_base(u,h)
    local real c
    local real p
    local real d
    if b<=0.0 then
        return
    endif
    set c=b/DB_aspd_fator(LoadReal(DB_est_ht,h,DB_EST_VEL))
    set p=DB_aspd_piso(u)
    if c<p then
        set c=p
    endif
    set d=BlzGetUnitAttackCooldown(u,0)-c
    if d>0.0005 or d<-0.0005 then
        call BlzSetUnitAttackCooldown(u,c,0)
    endif
endfunction

function DB_aspd_reaplica takes unit u returns nothing
    if u==null or GetUnitTypeId(u)==0 then
        return
    endif
    call DB_aspd_aplica(u,DB_est_h(u))
endfunction

function DB_est_ataca takes unit u returns boolean
    return IsUnitType(u,UNIT_TYPE_MELEE_ATTACKER) or IsUnitType(u,UNIT_TYPE_RANGED_ATTACKER)
endfunction

function DB_est_alcance takes unit u,integer h returns real
    local real r
    if DB_est_ataca(u) then
        set r=BlzGetUnitWeaponRealField(u,UNIT_WEAPON_RF_ATTACK_RANGE,0)
        if r>0.0 then
            return r
        endif
    endif
    if HaveSavedReal(DB_est_ht,h,DB_EST_ALC) then
        return LoadReal(DB_est_ht,h,DB_EST_ALC)
    endif
    set r=S2R(DB_slk_get(DB_TAB_UNIT,GetUnitTypeId(u),DB_C_UNIT_RANGEN1))
    call SaveReal(DB_est_ht,h,DB_EST_ALC,r)
    return r
endfunction

function DB_est_alcance_set takes unit u,integer h,real v returns nothing
    local real r0
    local real r1
    if DB_est_ataca(u) then
        set r0=BlzGetUnitWeaponRealField(u,UNIT_WEAPON_RF_ATTACK_RANGE,0)
        if r0>0.0 then
            if v!=r0 then
                set r1=BlzGetUnitWeaponRealField(u,UNIT_WEAPON_RF_ATTACK_RANGE,1)
                call BlzSetUnitWeaponRealField(u,UNIT_WEAPON_RF_ATTACK_RANGE,1,v-r0+r1)
            endif
            call SaveReal(DB_est_ht,h,DB_EST_ALC,v)
            return
        endif
    endif
    set r0=DB_est_alcance(u,h)
    if v!=r0 then
        if not BlzSetUnitWeaponRealField(u,UNIT_WEAPON_RF_ATTACK_RANGE,1,v-r0) then
            call BlzSetUnitWeaponRealField(u,UNIT_WEAPON_RF_ATTACK_RANGE,0,v)
        endif
    endif
    call SaveReal(DB_est_ht,h,DB_EST_ALC,v)
endfunction

function DB_estado_bonus takes unit u,real v returns nothing
    local integer h
    if u==null then
        return
    endif
    set h=DB_est_h(u)
    call SaveReal(DB_est_ht,h,DB_EST_BONUS,v)
endfunction

function DB_est_media_dados takes unit u returns real
    return I2R(BlzGetUnitDiceNumber(u,0)*(BlzGetUnitDiceSides(u,0)+1))/2.0
endfunction
//{{KK_SE:KK_MORFO_ESTADO}}

constant integer DB_EST_MORFO=10
constant integer DB_EST_F_DANO=11
constant integer DB_EST_F_DADOS=12
constant integer DB_EST_F_LADOS=13
constant integer DB_EST_F_ARMA=14
constant integer DB_EST_F_VIDA=15
constant integer DB_EST_F_MANA=16
constant integer DB_EST_F_ATQ=17
constant integer DB_EST_F_PONTO=18
constant integer DB_EST_F_BACK=19
constant integer DB_EST_F_VPROJ=20
constant integer DB_EST_F_TIQUES=21
constant integer DB_EST_COOL_MAPA=22
constant integer DB_MORFO_MAX=64
unit array DB_morfo_u
integer DB_morfo_n=0
timer DB_morfo_tmr=null

function DB_arma_foto takes unit u,integer h returns nothing
    call SaveInteger(DB_est_ht,h,DB_EST_F_DANO,BlzGetUnitBaseDamage(u,0))
    call SaveInteger(DB_est_ht,h,DB_EST_F_DADOS,BlzGetUnitDiceNumber(u,0))
    call SaveInteger(DB_est_ht,h,DB_EST_F_LADOS,BlzGetUnitDiceSides(u,0))
    call SaveReal(DB_est_ht,h,DB_EST_F_ARMA,BlzGetUnitArmor(u))
    call SaveInteger(DB_est_ht,h,DB_EST_F_VIDA,BlzGetUnitMaxHP(u))
    call SaveInteger(DB_est_ht,h,DB_EST_F_MANA,BlzGetUnitMaxMana(u))
    if DB_est_ataca(u) then
        call SaveInteger(DB_est_ht,h,DB_EST_F_ATQ,BlzGetUnitWeaponIntegerField(u,UNIT_WEAPON_IF_ATTACK_ATTACK_TYPE,0))
        call SaveReal(DB_est_ht,h,DB_EST_F_PONTO,BlzGetUnitWeaponRealField(u,UNIT_WEAPON_RF_ATTACK_DAMAGE_POINT,0))
        call SaveReal(DB_est_ht,h,DB_EST_F_BACK,BlzGetUnitWeaponRealField(u,UNIT_WEAPON_RF_ATTACK_BACKSWING_POINT,0))
        call SaveReal(DB_est_ht,h,DB_EST_F_VPROJ,BlzGetUnitWeaponRealField(u,UNIT_WEAPON_RF_ATTACK_PROJECTILE_SPEED,0))
    endif
endfunction

function DB_arma_volta takes unit u,integer h,boolean mesmo returns nothing
    local integer i
    local real r
    set i=LoadInteger(DB_est_ht,h,DB_EST_F_DANO)
    if BlzGetUnitBaseDamage(u,0)!=i then
        call BlzSetUnitBaseDamage(u,i,0)
    endif
    set i=LoadInteger(DB_est_ht,h,DB_EST_F_DADOS)
    if i>0 and BlzGetUnitDiceNumber(u,0)!=i then
        call BlzSetUnitDiceNumber(u,i,0)
    endif
    set i=LoadInteger(DB_est_ht,h,DB_EST_F_LADOS)
    if i>0 and BlzGetUnitDiceSides(u,0)!=i then
        call BlzSetUnitDiceSides(u,i,0)
    endif
    set r=LoadReal(DB_est_ht,h,DB_EST_F_ARMA)
    if BlzGetUnitArmor(u)!=r then
        call BlzSetUnitArmor(u,r)
    endif
    set i=LoadInteger(DB_est_ht,h,DB_EST_F_VIDA)
    if i>0 and BlzGetUnitMaxHP(u)!=i then
        call BlzSetUnitMaxHP(u,i)
    endif
    set i=LoadInteger(DB_est_ht,h,DB_EST_F_MANA)
    if i>0 and BlzGetUnitMaxMana(u)!=i then
        call BlzSetUnitMaxMana(u,i)
    endif
    if DB_est_ataca(u) and HaveSavedReal(DB_est_ht,h,DB_EST_F_VPROJ) then
        set r=LoadReal(DB_est_ht,h,DB_EST_F_VPROJ)
        if r>0.0 and BlzGetUnitWeaponRealField(u,UNIT_WEAPON_RF_ATTACK_PROJECTILE_SPEED,0)<=0.0 then
            call BlzSetUnitWeaponRealField(u,UNIT_WEAPON_RF_ATTACK_PROJECTILE_SPEED,0,r)
        endif
        if mesmo then
            set i=LoadInteger(DB_est_ht,h,DB_EST_F_ATQ)
            if BlzGetUnitWeaponIntegerField(u,UNIT_WEAPON_IF_ATTACK_ATTACK_TYPE,0)!=i then
                call BlzSetUnitWeaponIntegerField(u,UNIT_WEAPON_IF_ATTACK_ATTACK_TYPE,0,i)
            endif
            set r=LoadReal(DB_est_ht,h,DB_EST_F_PONTO)
            if BlzGetUnitWeaponRealField(u,UNIT_WEAPON_RF_ATTACK_DAMAGE_POINT,0)!=r then
                call BlzSetUnitWeaponRealField(u,UNIT_WEAPON_RF_ATTACK_DAMAGE_POINT,0,r)
            endif
            set r=LoadReal(DB_est_ht,h,DB_EST_F_BACK)
            if BlzGetUnitWeaponRealField(u,UNIT_WEAPON_RF_ATTACK_BACKSWING_POINT,0)!=r then
                call BlzSetUnitWeaponRealField(u,UNIT_WEAPON_RF_ATTACK_BACKSWING_POINT,0,r)
            endif
        endif
    endif
endfunction

function DB_morfo_volta takes unit u,integer h returns nothing
    local integer velho=LoadInteger(DB_est_ht,h,DB_EST_MORFO)
    local integer novo=GetUnitTypeId(u)
    local real b
    local real c
    local real p
    call RemoveSavedInteger(DB_est_ht,h,DB_EST_MORFO)
    call SaveInteger(DB_est_ht,h,DB_EST_TIPO,novo)
    call DB_arma_volta(u,h,velho==novo)
    if HaveSavedReal(DB_est_ht,h,DB_EST_COOL) then
        set b=LoadReal(DB_est_ht,h,DB_EST_COOL)
        set c=b/DB_aspd_fator(LoadReal(DB_est_ht,h,DB_EST_VEL))
        set p=DB_aspd_piso(u)
        if c<p then
            set c=p
        endif
        set p=BlzGetUnitAttackCooldown(u,0)
        if velho!=novo and (p-c>0.0005 or c-p>0.0005) and not LoadBoolean(DB_est_ht,h,DB_EST_COOL_MAPA) then
            call SaveReal(DB_est_ht,h,DB_EST_COOL,p)
        endif
        call DB_aspd_aplica(u,h)
    endif
    if velho!=novo and HaveSavedReal(DB_est_ht,h,DB_EST_ALC) then
        set b=S2R(DB_slk_get(DB_TAB_UNIT,velho,DB_C_UNIT_RANGEN1))
        set c=S2R(DB_slk_get(DB_TAB_UNIT,novo,DB_C_UNIT_RANGEN1))
        if b>0.0 and c>0.0 then
            call DB_est_alcance_set(u,h,LoadReal(DB_est_ht,h,DB_EST_ALC)-b+c)
        endif
    endif
endfunction

function DB_morfo_confere takes unit u returns nothing
    local integer h
    if DB_morfo_n==0 or u==null or DB_est_ht==null then
        return
    endif
    set h=GetHandleId(u)
    if HaveSavedInteger(DB_est_ht,h,DB_EST_MORFO) and GetUnitTypeId(u)!=0 and GetUnitTypeId(u)!=LoadInteger(DB_est_ht,h,DB_EST_MORFO) then
        call DB_morfo_volta(u,h)
    endif
endfunction

function DB_morfo_refoto takes unit u returns nothing
    local integer h
    if DB_morfo_n==0 or u==null or DB_est_ht==null then
        return
    endif
    set h=GetHandleId(u)
    if HaveSavedInteger(DB_est_ht,h,DB_EST_MORFO) and GetUnitTypeId(u)==LoadInteger(DB_est_ht,h,DB_EST_MORFO) then
        call DB_arma_foto(u,h)
    endif
endfunction

function DB_morfo_tira takes integer i returns nothing
    set DB_morfo_n=DB_morfo_n-1
    set DB_morfo_u[i]=DB_morfo_u[DB_morfo_n]
    set DB_morfo_u[DB_morfo_n]=null
endfunction

function DB_morfo_tique takes nothing returns nothing
    local integer i=DB_morfo_n-1
    local unit u
    local integer h
    loop
        exitwhen i<0
        set u=DB_morfo_u[i]
        set h=GetHandleId(u)
        if GetUnitTypeId(u)==0 or not HaveSavedInteger(DB_est_ht,h,DB_EST_MORFO) then
            call RemoveSavedInteger(DB_est_ht,h,DB_EST_MORFO)
            call DB_morfo_tira(i)
        elseif GetUnitTypeId(u)!=LoadInteger(DB_est_ht,h,DB_EST_MORFO) then
            call DB_morfo_volta(u,h)
            call DB_morfo_tira(i)
        elseif LoadInteger(DB_est_ht,h,DB_EST_F_TIQUES)<=1 then
            call RemoveSavedInteger(DB_est_ht,h,DB_EST_MORFO)
            call DB_morfo_tira(i)
        else
            call SaveInteger(DB_est_ht,h,DB_EST_F_TIQUES,LoadInteger(DB_est_ht,h,DB_EST_F_TIQUES)-1)
        endif
        set i=i-1
    endloop
    if DB_morfo_n==0 then
        call PauseTimer(DB_morfo_tmr)
    endif
    set u=null
endfunction

function DB_morfo_anuncia takes unit u returns nothing
    local integer h
    if u==null or GetUnitTypeId(u)==0 then
        return
    endif
    set h=DB_est_h(u)
    if not HaveSavedInteger(DB_est_ht,h,DB_EST_MORFO) then
        if DB_morfo_n>=DB_MORFO_MAX then
            return
        endif
        set DB_morfo_u[DB_morfo_n]=u
        set DB_morfo_n=DB_morfo_n+1
        if DB_morfo_tmr==null then
            set DB_morfo_tmr=CreateTimer()
        endif
        if DB_morfo_n==1 then
            call TimerStart(DB_morfo_tmr,0.05,true,function DB_morfo_tique)
        endif
    endif
    call SaveInteger(DB_est_ht,h,DB_EST_MORFO,GetUnitTypeId(u))
    call SaveInteger(DB_est_ht,h,DB_EST_F_TIQUES,40)
    call DB_arma_foto(u,h)
endfunction

function DB_morfo_skin_volta takes unit u returns nothing
    local integer h=GetHandleId(u)
    if DB_est_ht!=null and HaveSavedInteger(DB_est_ht,h,DB_EST_MORFO) then
        call DB_morfo_volta(u,h)
    endif
endfunction

function KK_morfo_antes takes unit u returns nothing
    call DB_morfo_anuncia(u)
endfunction
//{{KK_FIMSE:KK_MORFO_ESTADO}}

//{{KK_SE:KK_EST_14}}
function DB_est_primario takes unit u returns real
    local integer a
    if not IsUnitType(u,UNIT_TYPE_HERO) then
        return 0.0
    endif
    set a=BlzGetUnitIntegerField(u,UNIT_IF_PRIMARY_ATTRIBUTE)
    if a==1 then
        return I2R(GetHeroStr(u,true))
    elseif a==2 then
        return I2R(GetHeroInt(u,true))
    elseif a==3 then
        return I2R(GetHeroAgi(u,true))
    endif
    return 0.0
endfunction
//{{KK_FIMSE:KK_EST_14}}

function DB_estado_le takes unit u,integer st returns real
    local integer h
    if u==null then
        return 0.0
    endif
    //{{KK_SE:KK_MORFO_ESTADO}}
    call DB_morfo_confere(u)
    //{{KK_FIMSE:KK_MORFO_ESTADO}}
    if st==0x12 then
        return I2R(BlzGetUnitBaseDamage(u,0))
    elseif st==0x20 then
        return BlzGetUnitArmor(u)
    elseif st==0x23 then
        if DB_est_ataca(u) then
            return I2R(BlzGetUnitWeaponIntegerField(u,UNIT_WEAPON_IF_ATTACK_ATTACK_TYPE,0))
        endif
        return 0.0
    elseif st==0x50 then
        return I2R(BlzGetUnitIntegerField(u,UNIT_IF_DEFENSE_TYPE))
    elseif st==0x10 then
        return I2R(BlzGetUnitDiceNumber(u,0))
    elseif st==0x11 then
        return I2R(BlzGetUnitDiceSides(u,0))
    endif
    set h=DB_est_h(u)
    //{{KK_SE:KK_EST_14}}
    if st==0x14 then
        return I2R(BlzGetUnitBaseDamage(u,0)+BlzGetUnitDiceNumber(u,0))+DB_est_primario(u)+LoadReal(DB_est_ht,h,DB_EST_BONUS)
    endif
    //{{KK_FIMSE:KK_EST_14}}
    if st==0x15 then
        //{{KK_SE:KK_EST_14}}
        return I2R(BlzGetUnitBaseDamage(u,0)+BlzGetUnitDiceNumber(u,0)*BlzGetUnitDiceSides(u,0))+DB_est_primario(u)+LoadReal(DB_est_ht,h,DB_EST_BONUS)
        //{{KK_FIMSE:KK_EST_14}}
        return I2R(BlzGetUnitBaseDamage(u,0)+BlzGetUnitDiceNumber(u,0)*BlzGetUnitDiceSides(u,0))+LoadReal(DB_est_ht,h,DB_EST_BONUS)
    elseif st==0x51 then
        return LoadReal(DB_est_ht,h,DB_EST_VEL)
    elseif st==0x25 then
        return DB_aspd_base(u,h)
    elseif st==0x13 then
        //{{KK_INCLUI:estado_verde_le}}
        return LoadReal(DB_est_ht,h,DB_EST_BONUS)
    elseif st==0x16 then
        return DB_est_alcance(u,h)
    elseif st==0x52 then
        return BlzGetUnitRealField(u,UNIT_RF_ACQUISITION_RANGE)
    elseif st==0x53 then
        return BlzGetUnitRealField(u,UNIT_RF_HIT_POINTS_REGENERATION_RATE)
    elseif st==0x54 then
        return BlzGetUnitRealField(u,UNIT_RF_MANA_REGENERATION)
    elseif st==0x60 then
        return I2R(BlzGetUnitIntegerField(u,UNIT_IF_TARGETED_AS))
    elseif not DB_est_ataca(u) then
        return 0.0
    elseif st==0x21 then
        return BlzGetUnitWeaponRealField(u,UNIT_WEAPON_RF_ATTACK_DAMAGE_LOSS_FACTOR,0)
    elseif st==0x22 then
        return I2R(BlzGetUnitWeaponIntegerField(u,UNIT_WEAPON_IF_ATTACK_WEAPON_SOUND,0))
    elseif st==0x24 then
        return I2R(BlzGetUnitWeaponIntegerField(u,UNIT_WEAPON_IF_ATTACK_MAXIMUM_NUMBER_OF_TARGETS,0))
    elseif st==0x26 then
        return BlzGetUnitWeaponRealField(u,UNIT_WEAPON_RF_ATTACK_DAMAGE_POINT,0)
    elseif st==0x28 then
        return BlzGetUnitWeaponRealField(u,UNIT_WEAPON_RF_ATTACK_BACKSWING_POINT,0)
    elseif st==0x29 then
        return I2R(BlzGetUnitWeaponIntegerField(u,UNIT_WEAPON_IF_ATTACK_TARGETS_ALLOWED,0))
    elseif st==0x40 then
        return BlzGetUnitWeaponRealField(u,UNIT_WEAPON_RF_ATTACK_RANGE,1)
    elseif st==0x56 then
        return BlzGetUnitWeaponRealField(u,UNIT_WEAPON_RF_ATTACK_DAMAGE_SPILL_DISTANCE,0)
    elseif st==0x57 then
        return BlzGetUnitWeaponRealField(u,UNIT_WEAPON_RF_ATTACK_DAMAGE_SPILL_RADIUS,0)
    endif
    return 0.0
endfunction

function DB_estado_set takes unit u,integer st,real v returns nothing
    local integer h
    if u==null then
        return
    endif
    //{{KK_SE:KK_MORFO_ESTADO}}
    call DB_morfo_confere(u)
    //{{KK_FIMSE:KK_MORFO_ESTADO}}
    if st==0x12 then
        call BlzSetUnitBaseDamage(u,DB_est_trunca(v),0)
    elseif st==0x14 or st==0x15 then
        return
    elseif st==0x20 then
        call BlzSetUnitArmor(u,v)
    elseif st==0x51 then
        set h=DB_est_h(u)
        call SaveReal(DB_est_ht,h,DB_EST_VEL,v)
        call DB_aspd_aplica(u,h)
    elseif st==0x25 then
        set h=DB_est_h(u)
        call SaveReal(DB_est_ht,h,DB_EST_COOL,v)
        //{{KK_SE:KK_MORFO_ESTADO}}
        call SaveBoolean(DB_est_ht,h,DB_EST_COOL_MAPA,true)
        //{{KK_FIMSE:KK_MORFO_ESTADO}}
        if v>0.0 then
            call DB_aspd_aplica(u,h)
        elseif DB_aspd_piso(u)>0.0 then
            call BlzSetUnitAttackCooldown(u,DB_aspd_piso(u),0)
        else
            call BlzSetUnitAttackCooldown(u,v,0)
        endif
    elseif st==0x13 then
        set h=DB_est_h(u)
        //{{KK_INCLUI:estado_verde_grava}}
        call SaveReal(DB_est_ht,h,DB_EST_BONUS,v)
    elseif st==0x16 then
        call DB_est_alcance_set(u,DB_est_h(u),v)
    elseif st==0x23 then
        call BlzSetUnitWeaponIntegerField(u,UNIT_WEAPON_IF_ATTACK_ATTACK_TYPE,0,DB_est_piso(v))
    elseif st==0x50 then
        call BlzSetUnitIntegerField(u,UNIT_IF_DEFENSE_TYPE,DB_est_piso(v))
    elseif st==0x10 then
        call BlzSetUnitDiceNumber(u,DB_est_piso(v),0)
    elseif st==0x11 then
        call BlzSetUnitDiceSides(u,DB_est_piso(v),0)
    elseif st==0x52 then
        call BlzSetUnitRealField(u,UNIT_RF_ACQUISITION_RANGE,v)
    elseif st==0x53 then
        call BlzSetUnitRealField(u,UNIT_RF_HIT_POINTS_REGENERATION_RATE,v)
    elseif st==0x54 then
        call BlzSetUnitRealField(u,UNIT_RF_MANA_REGENERATION,v)
    elseif st==0x60 then
        call BlzSetUnitIntegerField(u,UNIT_IF_TARGETED_AS,DB_est_trunca(v))
    elseif not DB_est_ataca(u) then
        return
    elseif st==0x21 then
        call BlzSetUnitWeaponRealField(u,UNIT_WEAPON_RF_ATTACK_DAMAGE_LOSS_FACTOR,0,v)
    elseif st==0x22 then
        call BlzSetUnitWeaponIntegerField(u,UNIT_WEAPON_IF_ATTACK_WEAPON_SOUND,0,DB_est_trunca(v))
    elseif st==0x24 then
        call BlzSetUnitWeaponIntegerField(u,UNIT_WEAPON_IF_ATTACK_MAXIMUM_NUMBER_OF_TARGETS,0,DB_est_trunca(v))
    elseif st==0x26 then
        call BlzSetUnitWeaponRealField(u,UNIT_WEAPON_RF_ATTACK_DAMAGE_POINT,0,v)
    elseif st==0x28 then
        call BlzSetUnitWeaponRealField(u,UNIT_WEAPON_RF_ATTACK_BACKSWING_POINT,0,v)
    elseif st==0x29 then
        call BlzSetUnitWeaponIntegerField(u,UNIT_WEAPON_IF_ATTACK_TARGETS_ALLOWED,0,DB_est_trunca(v))
    elseif st==0x56 then
        call BlzSetUnitWeaponRealField(u,UNIT_WEAPON_RF_ATTACK_DAMAGE_SPILL_DISTANCE,0,v)
    elseif st==0x57 then
        call BlzSetUnitWeaponRealField(u,UNIT_WEAPON_RF_ATTACK_DAMAGE_SPILL_RADIUS,0,v)
    endif
    //{{KK_SE:KK_MORFO_ESTADO}}
    call DB_morfo_refoto(u)
    //{{KK_FIMSE:KK_MORFO_ESTADO}}
endfunction
