//@GLOBALS
constant integer RPGT_G_MUDOU=1
integer RPGT_por_nivel=5
integer RPGT_nivel_max=300
real RPGT_xp_par=1000000.0
integer RPGT_reset_ouro=0
real RPGT_par_prim=0.005
real RPGT_par_skill=0.005
real RPGT_par_vida=0.003
real RPGT_par_red=0.002
real RPGT_par_red_teto=0.25
integer RPGT_jogadores=12
trigger array RPGT_tg
boolean array RPGT_tem
integer array RPGT_extra
integer array RPGT_gasto
integer array RPGT_par_n
real array RPGT_par_xp
integer array RPGT_par_g
real array RPGT_ap_skill
real array RPGT_ap_red
integer RPGT_ev_pid=0
boolean RPGT_pronto=false
//@ENDGLOBALS

function RPGT_gancho takes integer qual, code f returns nothing
    if qual<1 or qual>8 then
        return
    endif
    call TriggerAddCondition(RPGT_tg[qual], Condition(f))
    set RPGT_tem[qual]=true
endfunction

function RPGT_chama takes integer qual, integer pid returns nothing
    if qual>=1 and qual<=8 and RPGT_tem[qual] then
        set RPGT_ev_pid=pid
        call TriggerEvaluate(RPGT_tg[qual])
    endif
endfunction

function RPGT_gastos takes integer pid returns integer
    return RPGT_gasto[pid*4+1]+RPGT_gasto[pid*4+2]+RPGT_gasto[pid*4+3]
endfunction

function RPGT_livres takes integer pid, unit h returns integer
    if h==null then
        return 0
    endif
    return GetHeroLevel(h)*RPGT_por_nivel+RPGT_extra[pid]-RPGT_gastos(pid)
endfunction

function RPGT_soma_attr takes unit h, integer a, integer n returns nothing
    if a==1 then
        call SetHeroStr(h, GetHeroStr(h, false)+n, true)
    elseif a==2 then
        call SetHeroAgi(h, GetHeroAgi(h, false)+n, true)
    else
        call SetHeroInt(h, GetHeroInt(h, false)+n, true)
    endif
endfunction

function RPGT_aloca takes integer pid, unit h, integer a, integer n returns integer
    local integer livre=RPGT_livres(pid, h)
    if h==null or a<1 or a>3 or n<1 or livre<1 then
        return 0
    endif
    if n>livre then
        set n=livre
    endif
    call RPGT_soma_attr(h, a, n)
    set RPGT_gasto[pid*4+a]=RPGT_gasto[pid*4+a]+n
    call RPGT_chama(RPGT_G_MUDOU, pid)
    return n
endfunction

function RPGT_reseta takes integer pid, unit h returns boolean
    local integer a=1
    if h==null or RPGT_gastos(pid)==0 then
        return false
    endif
    if GetPlayerState(Player(pid), PLAYER_STATE_RESOURCE_GOLD)<RPGT_reset_ouro then
        return false
    endif
    call SetPlayerState(Player(pid), PLAYER_STATE_RESOURCE_GOLD, GetPlayerState(Player(pid), PLAYER_STATE_RESOURCE_GOLD)-RPGT_reset_ouro)
    loop
        exitwhen a>3
        call RPGT_soma_attr(h, a, -RPGT_gasto[pid*4+a])
        set RPGT_gasto[pid*4+a]=0
        set a=a+1
    endloop
    call RPGT_chama(RPGT_G_MUDOU, pid)
    return true
endfunction

function RPGT_xp takes integer pid, real xp returns nothing
    if xp<=0.0 or RPGT_xp_par<=0.0 then
        return
    endif
    set RPGT_par_xp[pid]=RPGT_par_xp[pid]+xp
    loop
        exitwhen RPGT_par_xp[pid]<RPGT_xp_par
        set RPGT_par_xp[pid]=RPGT_par_xp[pid]-RPGT_xp_par
        set RPGT_par_n[pid]=RPGT_par_n[pid]+1
    endloop
endfunction

function RPGT_par_livres takes integer pid returns integer
    return RPGT_par_n[pid]-RPGT_par_g[pid*5+1]-RPGT_par_g[pid*5+2]-RPGT_par_g[pid*5+3]-RPGT_par_g[pid*5+4]
endfunction

function RPGT_par_pct takes integer pid, integer t returns real
    local real r
    if t==1 then
        return RPGT_par_prim*I2R(RPGT_par_g[pid*5+1])
    elseif t==2 then
        return RPGT_par_skill*I2R(RPGT_par_g[pid*5+2])
    elseif t==3 then
        return RPGT_par_vida*I2R(RPGT_par_g[pid*5+3])
    endif
    set r=RPGT_par_red*I2R(RPGT_par_g[pid*5+4])
    if r>RPGT_par_red_teto then
        return RPGT_par_red_teto
    endif
    return r
endfunction

function RPGT_aplica takes integer pid, unit h returns nothing
    local real s
    local real r
    if h==null then
        return
    endif
    set s=RPGT_par_pct(pid, 2)
    set r=RPGT_par_pct(pid, 4)
    call RPGD_soma(h, RPGD_S_SKILL, s-RPGT_ap_skill[pid])
    call RPGD_soma(h, RPGD_S_CURA, s-RPGT_ap_skill[pid])
    call RPGD_soma(h, RPGD_S_RED, r-RPGT_ap_red[pid])
    set RPGT_ap_skill[pid]=s
    set RPGT_ap_red[pid]=r
endfunction

function RPGT_par_aloca takes integer pid, unit h, integer t, integer n returns integer
    local integer livre=RPGT_par_livres(pid)
    if t<1 or t>4 or n<1 or livre<1 then
        return 0
    endif
    if n>livre then
        set n=livre
    endif
    set RPGT_par_g[pid*5+t]=RPGT_par_g[pid*5+t]+n
    call RPGT_aplica(pid, h)
    call RPGT_chama(RPGT_G_MUDOU, pid)
    return n
endfunction

function RPGT_poe_save takes integer pid returns nothing
    call RPGS_poe_s("tg", I2S(RPGT_gasto[pid*4+1])+","+I2S(RPGT_gasto[pid*4+2])+","+I2S(RPGT_gasto[pid*4+3])+","+I2S(RPGT_extra[pid])+",")
    call RPGS_poe_s("tp", I2S(RPGT_par_n[pid])+","+R2S(RPGT_par_xp[pid])+","+I2S(RPGT_par_g[pid*5+1])+","+I2S(RPGT_par_g[pid*5+2])+","+I2S(RPGT_par_g[pid*5+3])+","+I2S(RPGT_par_g[pid*5+4])+",")
endfunction

function RPGT_campo takes string s, integer k returns string
    local integer i=0
    local integer ini=0
    local integer n=0
    loop
        exitwhen i>=StringLength(s)
        if SubString(s, i, i+1)=="," then
            if n==k then
                return SubString(s, ini, i)
            endif
            set n=n+1
            set ini=i+1
        endif
        set i=i+1
    endloop
    return ""
endfunction

function RPGT_le_save takes integer pid returns nothing
    local string g=RPGS_le_s(pid, "tg")
    local string p=RPGS_le_s(pid, "tp")
    set RPGT_gasto[pid*4+1]=S2I(RPGT_campo(g, 0))
    set RPGT_gasto[pid*4+2]=S2I(RPGT_campo(g, 1))
    set RPGT_gasto[pid*4+3]=S2I(RPGT_campo(g, 2))
    set RPGT_extra[pid]=S2I(RPGT_campo(g, 3))
    set RPGT_par_n[pid]=S2I(RPGT_campo(p, 0))
    set RPGT_par_xp[pid]=S2R(RPGT_campo(p, 1))
    set RPGT_par_g[pid*5+1]=S2I(RPGT_campo(p, 2))
    set RPGT_par_g[pid*5+2]=S2I(RPGT_campo(p, 3))
    set RPGT_par_g[pid*5+3]=S2I(RPGT_campo(p, 4))
    set RPGT_par_g[pid*5+4]=S2I(RPGT_campo(p, 5))
    set RPGT_ap_skill[pid]=0.0
    set RPGT_ap_red[pid]=0.0
endfunction

function RPGT_init takes nothing returns nothing
    local integer i=1
    if RPGT_pronto then
        return
    endif
    set RPGT_pronto=true
    loop
        exitwhen i>8
        set RPGT_tg[i]=CreateTrigger()
        set i=i+1
    endloop
endfunction
