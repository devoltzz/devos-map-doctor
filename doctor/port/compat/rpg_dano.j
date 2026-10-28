//@GLOBALS
constant integer RPGD_S_SKILL=1
constant integer RPGD_S_CRIT=2
constant integer RPGD_S_CRITX=3
constant integer RPGD_S_DEF=4
constant integer RPGD_S_RED=5
constant integer RPGD_S_VEL=6
constant integer RPGD_S_CURA=7
constant integer RPGD_S_ESQ=8
constant integer RPGD_S_ATQ=9
constant integer RPGD_S_DANO=10
constant integer RPGD_T_ATAQUE=0
constant integer RPGD_T_SKILL=1
constant integer RPGD_T_OUTRO=2
constant integer RPGD_T_CURA=3
constant integer RPGD_T_PURO=4
real RPGD_crit_base=0.05
real RPGD_critx_base=2.0
real RPGD_def_k=50.0
real RPGD_def_exp=1.5
real RPGD_def_teto=0.75
real RPGD_esq_teto=0.40
real RPGD_vel_teto=3.0
real RPGD_txt_grande=0.0
integer RPGD_jogadores=12
real array RPGD_vel_k
real RPGD_vel_k_padrao=1000.0
hashtable RPGD_ht=null
trigger RPGD_t_dano=null
trigger RPGD_t_final=null
trigger RPGD_t_cmd=null
boolean RPGD_tem_gancho=false
boolean array RPGD_txt_on
boolean RPGD_dentro=false
integer RPGD_prof=0
real RPGD_pend_valor=0.0
integer RPGD_pend_tipo=0
integer RPGD_pend_abil=0
boolean RPGD_pend_crit=false
unit RPGD_ev_src=null
unit RPGD_ev_tgt=null
real RPGD_ev_valor=0.0
integer RPGD_ev_tipo=0
integer RPGD_ev_abil=0
boolean RPGD_ev_crit=false
real RPGD_ev_texto=-1.0
//@ENDGLOBALS

function RPGD_bonus takes unit u, integer s returns real
    if u==null then
        return 0.0
    endif
    return LoadReal(RPGD_ht, GetHandleId(u), s)
endfunction

function RPGD_soma takes unit u, integer s, real v returns nothing
    local integer h
    if u==null then
        return
    endif
    set h=GetHandleId(u)
    call SaveReal(RPGD_ht, h, s, LoadReal(RPGD_ht, h, s)+v)
endfunction

function RPGD_zera takes unit u returns nothing
    if u!=null then
        call FlushChildHashtable(RPGD_ht, GetHandleId(u))
    endif
endfunction

function RPGD_curto takes real v returns string
    local string suf=""
    local real d=1.0
    local integer i
    local integer dec
    if v<0 then
        return "-"+RPGD_curto(-v)
    endif
    if v>=1000000000000.0 then
        set suf="T"
        set d=1000000000000.0
    elseif v>=1000000000.0 then
        set suf="B"
        set d=1000000000.0
    elseif v>=1000000.0 then
        set suf="M"
        set d=1000000.0
    elseif v>=1000.0 then
        set suf="K"
        set d=1000.0
    endif
    if suf=="" then
        return I2S(R2I(v+0.5))
    endif
    set v=v/d
    set i=R2I(v)
    set dec=R2I((v-i)*10.0+0.5)
    if dec>=10 then
        set i=i+1
        set dec=0
    endif
    if dec==0 then
        return I2S(i)+suf
    endif
    return I2S(i)+"."+I2S(dec)+suf
endfunction

function RPGD_pot takes real b, real e returns real
    if b<=0.0 then
        return 0.0
    endif
    return Pow(b, e)
endfunction

function RPGD_def takes integer abil, real base, real cresce, real cstr, real cagi, real cint, real catk, integer tipo returns nothing
    call SaveReal(RPGD_ht, abil, 1, base)
    call SaveReal(RPGD_ht, abil, 2, cresce)
    call SaveReal(RPGD_ht, abil, 3, cstr)
    call SaveReal(RPGD_ht, abil, 4, cagi)
    call SaveReal(RPGD_ht, abil, 5, cint)
    call SaveReal(RPGD_ht, abil, 6, catk)
    call SaveInteger(RPGD_ht, abil, 7, tipo)
    call SaveBoolean(RPGD_ht, abil, 8, true)
endfunction

function RPGD_ataque takes unit u returns real
    local real b=I2R(BlzGetUnitBaseDamage(u, 0))
    local real d=I2R(BlzGetUnitDiceNumber(u, 0))
    local real s=I2R(BlzGetUnitDiceSides(u, 0))
    return b+d*(s+1.0)*0.5+RPGD_bonus(u, RPGD_S_ATQ)
endfunction

function RPGD_bruto takes unit src, integer abil, integer rank returns real
    local real v
    if not LoadBoolean(RPGD_ht, abil, 8) then
        return 0.0
    endif
    if rank<1 then
        set rank=1
    endif
    set v=LoadReal(RPGD_ht, abil, 1)*RPGD_pot(LoadReal(RPGD_ht, abil, 2), I2R(rank-1))
    if IsUnitType(src, UNIT_TYPE_HERO) then
        set v=v+LoadReal(RPGD_ht, abil, 3)*I2R(GetHeroStr(src, true))
        set v=v+LoadReal(RPGD_ht, abil, 4)*I2R(GetHeroAgi(src, true))
        set v=v+LoadReal(RPGD_ht, abil, 5)*I2R(GetHeroInt(src, true))
    endif
    set v=v+LoadReal(RPGD_ht, abil, 6)*RPGD_ataque(src)
    return v
endfunction

function RPGD_rola_crit takes unit src returns boolean
    return GetRandomReal(0.0, 1.0)<RPGD_crit_base+RPGD_bonus(src, RPGD_S_CRIT)
endfunction

function RPGD_mult_crit takes unit src returns real
    return RPGD_critx_base+RPGD_bonus(src, RPGD_S_CRITX)
endfunction

function RPGD_reducao takes unit tgt, integer lv returns real
    local real d=RPGD_bonus(tgt, RPGD_S_DEF)
    local real r
    if d<=0.0 then
        return 0.0
    endif
    if lv<1 then
        set lv=1
    endif
    set r=d/(d+RPGD_def_k*RPGD_pot(I2R(lv), RPGD_def_exp))
    if r>RPGD_def_teto then
        return RPGD_def_teto
    endif
    return r
endfunction

function RPGD_nivel takes unit u returns integer
    if IsUnitType(u, UNIT_TYPE_HERO) then
        return GetHeroLevel(u)
    endif
    return GetUnitLevel(u)
endfunction

function RPGD_texto takes unit src, unit tgt, real v, integer tipo, boolean crit returns nothing
    local texttag tt
    local integer pid=-1
    local string s
    local boolean ve
    if v<1.0 or tgt==null then
        return
    endif
    if src!=null then
        set pid=GetPlayerId(GetOwningPlayer(src))
    endif
    set s=RPGD_curto(v)
    if crit then
        set s=s+"!"
    endif
    set tt=CreateTextTag()
    call SetTextTagText(tt, s, 0.020+0.006*I2R(IntegerTertiaryOp(crit, 1, 0)))
    call SetTextTagPosUnit(tt, tgt, 40.0)
    if tipo==RPGD_T_CURA then
        call SetTextTagColor(tt, 80, 255, 80, 255)
    elseif crit then
        call SetTextTagColor(tt, 255, 200, 40, 255)
    elseif tipo==RPGD_T_ATAQUE then
        call SetTextTagColor(tt, 255, 255, 255, 255)
    else
        call SetTextTagColor(tt, 120, 190, 255, 255)
    endif
    call SetTextTagVelocity(tt, 0.0, 0.035)
    call SetTextTagPermanent(tt, false)
    call SetTextTagLifespan(tt, 1.2)
    call SetTextTagFadepoint(tt, 0.7)
    set ve=pid>=0 and GetLocalPlayer()==Player(pid) and RPGD_txt_on[pid]
    if crit and RPGD_txt_grande>0.0 and v>=RPGD_txt_grande and RPGD_txt_on[GetPlayerId(GetLocalPlayer())] then
        set ve=true
    endif
    call SetTextTagVisibility(tt, ve)
    set tt=null
endfunction

function RPGD_gancho takes code f returns nothing
    call TriggerAddCondition(RPGD_t_final, Condition(f))
    set RPGD_tem_gancho=true
endfunction

function RPGD_evento takes nothing returns boolean
    local unit src=GetEventDamageSource()
    local unit tgt=BlzGetEventDamageTarget()
    local real v=GetEventDamage()
    local integer tipo
    local boolean crit=false
    local real esq
    if RPGD_dentro then
        set v=RPGD_pend_valor
        set tipo=RPGD_pend_tipo
        set crit=RPGD_pend_crit
        set RPGD_ev_abil=RPGD_pend_abil
    elseif BlzGetEventIsAttack() then
        set tipo=RPGD_T_ATAQUE
        set RPGD_ev_abil=0
        set esq=RPGD_bonus(tgt, RPGD_S_ESQ)
        if esq>RPGD_esq_teto then
            set esq=RPGD_esq_teto
        endif
        if esq>0.0 and GetRandomReal(0.0, 1.0)<esq then
            call BlzSetEventDamage(0.0)
            set src=null
            set tgt=null
            return false
        endif
        set v=v+RPGD_bonus(src, RPGD_S_ATQ)
        if RPGD_rola_crit(src) then
            set crit=true
            set v=v*RPGD_mult_crit(src)
        endif
    else
        set tipo=RPGD_T_OUTRO
        set RPGD_ev_abil=0
    endif
    if src!=null and RPGD_bonus(src, RPGD_S_DANO)!=0.0 then
        set v=v*(1.0+RPGD_bonus(src, RPGD_S_DANO))
    endif
    if tipo!=RPGD_T_PURO then
        set v=v*(1.0-RPGD_reducao(tgt, RPGD_nivel(src)))
        set v=v*(1.0-RPGD_bonus(tgt, RPGD_S_RED))
    endif
    if v<0.0 then
        set v=0.0
    endif
    set RPGD_ev_src=src
    set RPGD_ev_tgt=tgt
    set RPGD_ev_valor=v
    set RPGD_ev_tipo=tipo
    set RPGD_ev_crit=crit
    set RPGD_ev_texto=-1.0
    if RPGD_tem_gancho then
        call TriggerEvaluate(RPGD_t_final)
    endif
    set v=RPGD_ev_valor
    call BlzSetEventDamage(v)
    if RPGD_ev_texto>=0.0 then
        set v=RPGD_ev_texto
    endif
    call RPGD_texto(src, tgt, v, tipo, crit)
    set src=null
    set tgt=null
    return false
endfunction

function RPGD_guarda takes integer n returns nothing
    call SaveUnitHandle(RPGD_ht, -1, n*10+1, RPGD_ev_src)
    call SaveUnitHandle(RPGD_ht, -1, n*10+2, RPGD_ev_tgt)
    call SaveReal(RPGD_ht, -1, n*10+3, RPGD_ev_valor)
    call SaveInteger(RPGD_ht, -1, n*10+4, RPGD_ev_tipo)
    call SaveInteger(RPGD_ht, -1, n*10+5, RPGD_ev_abil)
    call SaveBoolean(RPGD_ht, -1, n*10+6, RPGD_ev_crit)
    call SaveReal(RPGD_ht, -1, n*10+7, RPGD_ev_texto)
endfunction

function RPGD_devolve takes integer n returns nothing
    set RPGD_ev_src=LoadUnitHandle(RPGD_ht, -1, n*10+1)
    set RPGD_ev_tgt=LoadUnitHandle(RPGD_ht, -1, n*10+2)
    set RPGD_ev_valor=LoadReal(RPGD_ht, -1, n*10+3)
    set RPGD_ev_tipo=LoadInteger(RPGD_ht, -1, n*10+4)
    set RPGD_ev_abil=LoadInteger(RPGD_ht, -1, n*10+5)
    set RPGD_ev_crit=LoadBoolean(RPGD_ht, -1, n*10+6)
    set RPGD_ev_texto=LoadReal(RPGD_ht, -1, n*10+7)
endfunction

function RPGD_skill takes unit src, unit tgt, integer abil, integer rank, real mult returns real
    local real v=RPGD_bruto(src, abil, rank)*(1.0+RPGD_bonus(src, RPGD_S_SKILL))*mult
    local boolean crit=RPGD_rola_crit(src)
    local boolean antes=RPGD_dentro
    if crit then
        set v=v*RPGD_mult_crit(src)
    endif
    set RPGD_prof=RPGD_prof+1
    call RPGD_guarda(RPGD_prof)
    set RPGD_dentro=true
    set RPGD_pend_valor=v
    set RPGD_pend_tipo=RPGD_T_SKILL
    set RPGD_pend_abil=abil
    set RPGD_pend_crit=crit
    call UnitDamageTarget(src, tgt, 1.0, false, false, ATTACK_TYPE_MAGIC, DAMAGE_TYPE_UNIVERSAL, WEAPON_TYPE_WHOKNOWS)
    set RPGD_dentro=antes
    call RPGD_devolve(RPGD_prof)
    set RPGD_prof=RPGD_prof-1
    return v
endfunction

function RPGD_dano takes unit src, unit tgt, real v, integer tipo returns nothing
    local boolean antes=RPGD_dentro
    if tgt==null or v<=0.0 then
        return
    endif
    set RPGD_prof=RPGD_prof+1
    call RPGD_guarda(RPGD_prof)
    set RPGD_dentro=true
    set RPGD_pend_valor=v
    set RPGD_pend_tipo=tipo
    set RPGD_pend_abil=0
    set RPGD_pend_crit=false
    call UnitDamageTarget(src, tgt, 1.0, false, false, ATTACK_TYPE_MAGIC, DAMAGE_TYPE_UNIVERSAL, WEAPON_TYPE_WHOKNOWS)
    set RPGD_dentro=antes
    call RPGD_devolve(RPGD_prof)
    set RPGD_prof=RPGD_prof-1
endfunction

function RPGD_cura takes unit src, unit tgt, integer abil, integer rank, real mult returns real
    local real v=RPGD_bruto(src, abil, rank)*(1.0+RPGD_bonus(src, RPGD_S_CURA))*mult
    local boolean crit=RPGD_rola_crit(src)
    if tgt==null or GetWidgetLife(tgt)<0.405 then
        return 0.0
    endif
    if crit then
        set v=v*RPGD_mult_crit(src)
    endif
    set RPGD_ev_src=src
    set RPGD_ev_tgt=tgt
    set RPGD_ev_valor=v
    set RPGD_ev_tipo=RPGD_T_CURA
    set RPGD_ev_abil=abil
    set RPGD_ev_crit=crit
    if RPGD_tem_gancho then
        call TriggerEvaluate(RPGD_t_final)
    endif
    set v=RPGD_ev_valor
    call SetWidgetLife(tgt, GetWidgetLife(tgt)+v)
    call RPGD_texto(src, tgt, v, RPGD_T_CURA, crit)
    return v
endfunction

function RPGD_vel takes unit u returns nothing
    local integer h=GetHandleId(u)
    local real base
    local real agi=0.0
    local real k
    local integer lv
    local real pct
    if u==null then
        return
    endif
    if not HaveSavedReal(RPGD_ht, h, 100) then
        call SaveReal(RPGD_ht, h, 100, BlzGetUnitAttackCooldown(u, 0))
    endif
    set base=LoadReal(RPGD_ht, h, 100)
    set lv=RPGD_nivel(u)
    set k=RPGD_vel_k[lv]
    if k<=0.0 then
        set k=RPGD_vel_k_padrao
    endif
    if IsUnitType(u, UNIT_TYPE_HERO) then
        set agi=I2R(GetHeroAgi(u, true))
    endif
    set pct=RPGD_vel_teto*agi/(agi+k)+RPGD_bonus(u, RPGD_S_VEL)
    if pct<0.0 then
        set pct=0.0
    endif
    call BlzSetUnitAttackCooldown(u, base/(1.0+pct), 0)
endfunction

function RPGD_cmd takes nothing returns nothing
    local integer pid=GetPlayerId(GetTriggerPlayer())
    set RPGD_txt_on[pid]=not RPGD_txt_on[pid]
    if RPGD_txt_on[pid] then
        call DisplayTimedTextToPlayer(GetTriggerPlayer(), 0, 0, 4.0, "Damage text: |cff80ff80ON|r")
    else
        call DisplayTimedTextToPlayer(GetTriggerPlayer(), 0, 0, 4.0, "Damage text: |cffff8080OFF|r")
    endif
endfunction

function RPGD_init takes nothing returns nothing
    local integer i=0
    if RPGD_ht!=null then
        return
    endif
    set RPGD_ht=InitHashtable()
    set RPGD_t_final=CreateTrigger()
    set RPGD_t_dano=CreateTrigger()
    set RPGD_t_cmd=CreateTrigger()
    call TriggerAddCondition(RPGD_t_dano, Condition(function RPGD_evento))
    call TriggerAddAction(RPGD_t_cmd, function RPGD_cmd)
    loop
        exitwhen i>=bj_MAX_PLAYER_SLOTS
        call TriggerRegisterPlayerUnitEvent(RPGD_t_dano, Player(i), EVENT_PLAYER_UNIT_DAMAGED, null)
        if i<RPGD_jogadores then
            set RPGD_txt_on[i]=true
            call TriggerRegisterPlayerChatEvent(RPGD_t_cmd, Player(i), "-dmg", true)
        endif
        set i=i+1
    endloop
endfunction
