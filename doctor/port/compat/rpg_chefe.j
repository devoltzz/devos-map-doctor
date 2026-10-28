//@GLOBALS
constant integer RPGC_MAXC=16
constant integer RPGC_MAXF=8
constant integer RPGC_G_FASE=1
constant integer RPGC_G_ESCUDO=2
constant integer RPGC_G_ENRAGE=3
constant integer RPGC_G_MORTE=4
real RPGC_barra=1500000000.0
real RPGC_esc_base=0.25
real RPGC_esc_ref=8.0
real RPGC_enr_passo=0.5
real RPGC_enr_cada=10.0
real RPGC_tique=0.1
integer RPGC_bloq='YTpb'
real RPGC_bloq_passo=96.0
hashtable RPGC_ht=null
timer RPGC_tm=null
real RPGC_agora=0.0
trigger array RPGC_tg
boolean array RPGC_tem
unit array RPGC_c_u
real array RPGC_c_total
real array RPGC_c_resta
boolean array RPGC_c_vivo
integer array RPGC_c_nb
real array RPGC_c_fase
integer array RPGC_c_nf
integer array RPGC_c_fase_n
real array RPGC_c_esc
real array RPGC_c_esc_fim
real array RPGC_c_enr
real array RPGC_c_enr_mult
real array RPGC_c_enr_prox
boolean array RPGC_c_toca
real array RPGC_c_tx
real array RPGC_c_ty
real array RPGC_c_tr
real array RPGC_c_sx
real array RPGC_c_sy
group array RPGC_c_ocultos
group RPGC_tmpg=null
integer RPGC_foco_c=-1
framehandle RPGC_q_fundo=null
framehandle RPGC_q_cheio=null
framehandle RPGC_q_txt=null
real RPGC_q_larg=0.40
unit RPGC_ev_boss=null
integer RPGC_ev_fase=0
boolean RPGC_ev_ok=false
//@ENDGLOBALS

function RPGC_gancho takes integer qual, code f returns nothing
    if qual<1 or qual>8 then
        return
    endif
    call TriggerAddCondition(RPGC_tg[qual], Condition(f))
    set RPGC_tem[qual]=true
endfunction

function RPGC_chama takes integer qual, unit boss returns nothing
    if qual>=1 and qual<=8 and RPGC_tem[qual] then
        set RPGC_ev_boss=boss
        call TriggerEvaluate(RPGC_tg[qual])
    endif
endfunction

function RPGC_slot takes unit boss returns integer
    if boss==null then
        return -1
    endif
    return LoadInteger(RPGC_ht, GetHandleId(boss), 0)-1
endfunction

function RPGC_escala takes integer n returns real
    if n<1 then
        set n=1
    endif
    return RPGC_esc_base+(1.0-RPGC_esc_base)*I2R(n)/RPGC_esc_ref
endfunction

function RPGC_abaixo takes integer c returns integer
    return RPGC_c_nb[c]
endfunction

function RPGC_recalcula takes integer c returns nothing
    set RPGC_c_resta[c]=I2R(RPGC_c_nb[c])*RPGC_barra+GetWidgetLife(RPGC_c_u[c])
endfunction

function RPGC_registra takes unit boss, real vida, integer jogadores returns integer
    local integer c=RPGC_slot(boss)
    local real barra
    if c<0 then
        set c=0
        loop
            exitwhen c>=RPGC_MAXC
            exitwhen RPGC_c_u[c]==null
            set c=c+1
        endloop
        if c>=RPGC_MAXC then
            return -1
        endif
        call SaveInteger(RPGC_ht, GetHandleId(boss), 0, c+1)
    endif
    set RPGC_c_u[c]=boss
    set RPGC_c_total[c]=vida*RPGC_escala(jogadores)
    set RPGC_c_vivo[c]=true
    set RPGC_c_nf[c]=0
    set RPGC_c_fase_n[c]=0
    set RPGC_c_esc[c]=0.0
    set RPGC_c_enr[c]=-1.0
    set RPGC_c_enr_mult[c]=1.0
    set RPGC_c_toca[c]=false
    set barra=RPGC_barra
    set RPGC_c_nb[c]=0
    if RPGC_c_total[c]<=barra then
        set barra=RPGC_c_total[c]
    else
        set RPGC_c_nb[c]=R2I((RPGC_c_total[c]-1.0)/RPGC_barra)
    endif
    call BlzSetUnitMaxHP(boss, R2I(barra))
    call BlzSetUnitRealField(boss, UNIT_RF_HIT_POINTS_REGENERATION_RATE, 0.0)
    call SetWidgetLife(boss, RPGC_c_total[c]-I2R(RPGC_c_nb[c])*RPGC_barra)
    call RPGC_recalcula(c)
    set RPGC_foco_c=c
    return c
endfunction

function RPGC_foco takes unit boss returns nothing
    set RPGC_foco_c=RPGC_slot(boss)
endfunction

function RPGC_fase takes unit boss, real frac returns nothing
    local integer c=RPGC_slot(boss)
    if c<0 or RPGC_c_nf[c]>=RPGC_MAXF then
        return
    endif
    set RPGC_c_fase[c*RPGC_MAXF+RPGC_c_nf[c]]=frac
    set RPGC_c_nf[c]=RPGC_c_nf[c]+1
endfunction

function RPGC_escudo takes unit boss, real valor, real dur returns nothing
    local integer c=RPGC_slot(boss)
    if c>=0 then
        set RPGC_c_esc[c]=valor
        set RPGC_c_esc_fim[c]=RPGC_agora+dur
    endif
endfunction

function RPGC_enrage takes unit boss, real seg returns nothing
    local integer c=RPGC_slot(boss)
    if c>=0 then
        set RPGC_c_enr[c]=RPGC_agora+seg
        set RPGC_c_enr_prox[c]=RPGC_agora+seg
        set RPGC_c_enr_mult[c]=1.0
    endif
endfunction

function RPGC_frac takes unit boss returns real
    local integer c=RPGC_slot(boss)
    if c<0 or RPGC_c_total[c]<=0.0 then
        return 0.0
    endif
    return RPGC_c_resta[c]/RPGC_c_total[c]
endfunction

function RPGC_resta takes unit boss returns real
    local integer c=RPGC_slot(boss)
    if c<0 then
        return 0.0
    endif
    return RPGC_c_resta[c]
endfunction

function RPGC_oculta_filtro takes nothing returns boolean
    local unit u=GetFilterUnit()
    local boolean ok=u!=RPGC_ev_boss and GetOwningPlayer(u)==GetOwningPlayer(RPGC_ev_boss) and not IsUnitType(u, UNIT_TYPE_DEAD) and not IsUnitType(u, UNIT_TYPE_HERO)
    set u=null
    return ok
endfunction

function RPGC_oculta_cada takes nothing returns nothing
    call PauseUnit(GetEnumUnit(), true)
    call ShowUnit(GetEnumUnit(), false)
endfunction

function RPGC_mostra_cada takes nothing returns nothing
    call ShowUnit(GetEnumUnit(), true)
    call PauseUnit(GetEnumUnit(), false)
endfunction

function RPGC_anel takes integer c, boolean cria returns nothing
    local real r=RPGC_c_tr[c]
    local integer n=R2I(2.0*bj_PI*r/RPGC_bloq_passo)+1
    local integer i=0
    local real a
    local destructable d
    local integer h=GetHandleId(RPGC_c_u[c])
    loop
        exitwhen i>=n
        if cria then
            set a=2.0*bj_PI*I2R(i)/I2R(n)
            set d=CreateDestructable(RPGC_bloq, RPGC_c_tx[c]+r*Cos(a), RPGC_c_ty[c]+r*Sin(a), 0.0, 1.0, 0)
            call SaveDestructableHandle(RPGC_ht, h, 100+i, d)
        else
            set d=LoadDestructableHandle(RPGC_ht, h, 100+i)
            if d!=null then
                call RemoveDestructable(d)
            endif
            call RemoveSavedHandle(RPGC_ht, h, 100+i)
        endif
        set i=i+1
    endloop
    call SaveInteger(RPGC_ht, h, 99, n)
    set d=null
endfunction

function RPGC_toca takes unit boss, real x, real y, real raio, real xs, real ys returns nothing
    local integer c=RPGC_slot(boss)
    if c<0 or RPGC_c_toca[c] then
        return
    endif
    set RPGC_c_toca[c]=true
    set RPGC_c_tx[c]=x
    set RPGC_c_ty[c]=y
    set RPGC_c_tr[c]=raio
    set RPGC_c_sx[c]=xs
    set RPGC_c_sy[c]=ys
    if RPGC_c_ocultos[c]==null then
        set RPGC_c_ocultos[c]=CreateGroup()
    endif
    call GroupClear(RPGC_c_ocultos[c])
    set RPGC_ev_boss=boss
    call GroupEnumUnitsInRange(RPGC_c_ocultos[c], x, y, raio+600.0, Condition(function RPGC_oculta_filtro))
    call ForGroup(RPGC_c_ocultos[c], function RPGC_oculta_cada)
    call RPGC_anel(c, true)
endfunction

function RPGC_abre takes unit boss returns nothing
    local integer c=RPGC_slot(boss)
    if c<0 or not RPGC_c_toca[c] then
        return
    endif
    set RPGC_c_toca[c]=false
    call ForGroup(RPGC_c_ocultos[c], function RPGC_mostra_cada)
    call GroupClear(RPGC_c_ocultos[c])
    call RPGC_anel(c, false)
endfunction

function RPGC_fora_cada takes nothing returns nothing
    local unit u=GetEnumUnit()
    local integer c=LoadInteger(RPGC_ht, 0, 1)
    local real dx=GetUnitX(u)-RPGC_c_tx[c]
    local real dy=GetUnitY(u)-RPGC_c_ty[c]
    if IsUnitType(u, UNIT_TYPE_HERO) and not IsUnitType(u, UNIT_TYPE_DEAD) and dx*dx+dy*dy>RPGC_c_tr[c]*RPGC_c_tr[c] then
        call SetUnitPosition(u, RPGC_c_sx[c], RPGC_c_sy[c])
    endif
    set u=null
endfunction

function RPGC_cruza_fases takes integer c, real antes returns nothing
    local integer i=0
    local real f
    loop
        exitwhen i>=RPGC_c_nf[c]
        set f=RPGC_c_fase[c*RPGC_MAXF+i]*RPGC_c_total[c]
        if antes>f and RPGC_c_resta[c]<=f then
            set RPGC_c_fase_n[c]=RPGC_c_fase_n[c]+1
            set RPGC_ev_fase=RPGC_c_fase_n[c]
            call RPGC_chama(RPGC_G_FASE, RPGC_c_u[c])
        endif
        set i=i+1
    endloop
endfunction

function RPGC_gancho_dano takes nothing returns boolean
    local integer c
    local real v
    local real antes
    local real cur
    if RPGD_ev_tipo==RPGD_T_CURA then
        return false
    endif
    set c=RPGC_slot(RPGD_ev_src)
    if c>=0 and RPGC_c_enr_mult[c]>1.0 then
        set RPGD_ev_valor=RPGD_ev_valor*RPGC_c_enr_mult[c]
    endif
    set c=RPGC_slot(RPGD_ev_tgt)
    if c<0 or not RPGC_c_vivo[c] then
        return false
    endif
    set v=RPGD_ev_valor
    if RPGC_c_esc[c]>0.0 then
        if v<RPGC_c_esc[c] then
            set RPGC_c_esc[c]=RPGC_c_esc[c]-v
            set RPGD_ev_texto=v
            set RPGD_ev_valor=0.0
            return false
        endif
        set v=v-RPGC_c_esc[c]
        set RPGC_c_esc[c]=0.0
        set RPGC_ev_ok=true
        call RPGC_chama(RPGC_G_ESCUDO, RPGC_c_u[c])
    endif
    set RPGD_ev_texto=RPGD_ev_valor
    set antes=RPGC_c_resta[c]
    set cur=GetWidgetLife(RPGC_c_u[c])
    loop
        exitwhen v<cur or RPGC_c_nb[c]<=0
        set v=v-cur
        set RPGC_c_nb[c]=RPGC_c_nb[c]-1
        set cur=RPGC_barra
    endloop
    set cur=cur-v
    if cur<=0.405 then
        set RPGC_c_vivo[c]=false
        set RPGC_c_resta[c]=0.0
        call RPGC_cruza_fases(c, antes)
        call RPGC_chama(RPGC_G_MORTE, RPGC_c_u[c])
        call RPGC_abre(RPGC_c_u[c])
        set RPGD_ev_valor=GetWidgetLife(RPGC_c_u[c])+1.0
        return false
    endif
    set RPGD_ev_valor=0.0
    call SetWidgetLife(RPGC_c_u[c], cur)
    call RPGC_recalcula(c)
    call RPGC_cruza_fases(c, antes)
    return false
endfunction

function RPGC_seg takes real s returns string
    local integer t=R2I(s)
    local integer m=t/60
    local integer r=t-m*60
    if r<10 then
        return I2S(m)+":0"+I2S(r)
    endif
    return I2S(m)+":"+I2S(r)
endfunction

function RPGC_desenha takes nothing returns nothing
    local integer c=RPGC_foco_c
    local string s
    local real f
    local real fb
    local integer nb
    if RPGC_q_fundo==null then
        return
    endif
    if c<0 or RPGC_c_u[c]==null or not RPGC_c_vivo[c] then
        call BlzFrameSetVisible(RPGC_q_fundo, false)
        return
    endif
    set nb=RPGC_abaixo(c)+1
    set fb=GetWidgetLife(RPGC_c_u[c])/I2R(BlzGetUnitMaxHP(RPGC_c_u[c]))
    if fb>1.0 then
        set fb=1.0
    endif
    set f=RPGC_c_resta[c]/RPGC_c_total[c]
    set s=GetUnitName(RPGC_c_u[c])+"   |cffffcc00x"+I2S(nb)+"|r   "+I2S(R2I(f*100.0+0.5))+"%"
    if RPGC_c_fase_n[c]>0 then
        set s=s+"   Phase "+I2S(RPGC_c_fase_n[c]+1)
    endif
    if RPGC_c_esc[c]>0.0 then
        set s=s+"   |cff80c0ffShield "+RPGD_curto(RPGC_c_esc[c])+"|r"
    endif
    if RPGC_c_enr[c]>=0.0 then
        if RPGC_agora>=RPGC_c_enr[c] then
            set s=s+"   |cffff4040ENRAGED|r"
        else
            set s=s+"   Enrage "+RPGC_seg(RPGC_c_enr[c]-RPGC_agora)
        endif
    endif
    call BlzFrameSetText(RPGC_q_txt, s)
    call BlzFrameSetSize(RPGC_q_cheio, RPGC_q_larg*fb+0.0001, 0.012)
    call BlzFrameSetVisible(RPGC_q_fundo, true)
endfunction

function RPGC_quadros takes nothing returns nothing
    local framehandle jogo=BlzGetOriginFrame(ORIGIN_FRAME_GAME_UI, 0)
    set RPGC_q_fundo=BlzCreateFrameByType("BACKDROP", "RPGC_fundo", jogo, "", 0)
    call BlzFrameSetAbsPoint(RPGC_q_fundo, FRAMEPOINT_TOP, 0.40, 0.575)
    call BlzFrameSetSize(RPGC_q_fundo, RPGC_q_larg+0.006, 0.034)
    call BlzFrameSetTexture(RPGC_q_fundo, "UI\\Widgets\\EscMenu\\Human\\editbox-background.blp", 0, true)
    set RPGC_q_cheio=BlzCreateFrameByType("BACKDROP", "RPGC_cheio", RPGC_q_fundo, "", 0)
    call BlzFrameSetPoint(RPGC_q_cheio, FRAMEPOINT_BOTTOMLEFT, RPGC_q_fundo, FRAMEPOINT_BOTTOMLEFT, 0.003, 0.003)
    call BlzFrameSetSize(RPGC_q_cheio, RPGC_q_larg, 0.012)
    call BlzFrameSetTexture(RPGC_q_cheio, "ReplaceableTextures\\TeamColor\\TeamColor00.blp", 0, true)
    set RPGC_q_txt=BlzCreateFrameByType("TEXT", "RPGC_txt", RPGC_q_fundo, "", 0)
    call BlzFrameSetPoint(RPGC_q_txt, FRAMEPOINT_TOP, RPGC_q_fundo, FRAMEPOINT_TOP, 0.0, -0.003)
    call BlzFrameSetSize(RPGC_q_txt, RPGC_q_larg, 0.014)
    call BlzFrameSetTextAlignment(RPGC_q_txt, TEXT_JUSTIFY_CENTER, TEXT_JUSTIFY_MIDDLE)
    call BlzFrameSetVisible(RPGC_q_fundo, false)
    set jogo=null
endfunction

function RPGC_tiq takes nothing returns nothing
    local integer c=0
    set RPGC_agora=RPGC_agora+RPGC_tique
    loop
        exitwhen c>=RPGC_MAXC
        if RPGC_c_u[c]!=null and RPGC_c_vivo[c] then
            if RPGC_c_esc[c]>0.0 and RPGC_agora>=RPGC_c_esc_fim[c] then
                set RPGC_c_esc[c]=0.0
                set RPGC_ev_ok=false
                call RPGC_chama(RPGC_G_ESCUDO, RPGC_c_u[c])
            endif
            if RPGC_c_enr[c]>=0.0 and RPGC_agora>=RPGC_c_enr_prox[c] then
                if RPGC_c_enr_mult[c]<=1.0 then
                    call RPGC_chama(RPGC_G_ENRAGE, RPGC_c_u[c])
                endif
                set RPGC_c_enr_mult[c]=RPGC_c_enr_mult[c]+RPGC_enr_passo
                set RPGC_c_enr_prox[c]=RPGC_c_enr_prox[c]+RPGC_enr_cada
            endif
            if RPGC_c_toca[c] then
                call SaveInteger(RPGC_ht, 0, 1, c)
                call GroupEnumUnitsInRange(RPGC_tmpg, RPGC_c_tx[c], RPGC_c_ty[c], RPGC_c_tr[c]+800.0, null)
                call ForGroup(RPGC_tmpg, function RPGC_fora_cada)
                call GroupClear(RPGC_tmpg)
            endif
        endif
        set c=c+1
    endloop
    call RPGC_desenha()
endfunction

function RPGC_solta takes unit boss returns nothing
    local integer c=RPGC_slot(boss)
    if c<0 then
        return
    endif
    call RPGC_abre(boss)
    set RPGC_c_u[c]=null
    set RPGC_c_vivo[c]=false
    set RPGC_c_resta[c]=0.0
    call RemoveSavedInteger(RPGC_ht, GetHandleId(boss), 0)
    if RPGC_foco_c==c then
        set RPGC_foco_c=-1
    endif
endfunction

function RPGC_init takes nothing returns nothing
    local integer i=1
    if RPGC_ht!=null then
        return
    endif
    set RPGC_ht=InitHashtable()
    set RPGC_tmpg=CreateGroup()
    loop
        exitwhen i>8
        set RPGC_tg[i]=CreateTrigger()
        set i=i+1
    endloop
    call RPGD_gancho(function RPGC_gancho_dano)
    call RPGC_quadros()
    set RPGC_tm=CreateTimer()
    call TimerStart(RPGC_tm, RPGC_tique, true, function RPGC_tiq)
endfunction
