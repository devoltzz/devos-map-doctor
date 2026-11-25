//@GLOBALS
integer KKSC_nt=0
integer array KKSC_tecla
integer array KKSC_pot
timer KKSC_relogio=null
boolean KKSC_pronto=false
trigger KKSC_tr_mascara=null
trigger KKSC_tr_tipo=null
trigger KKSC_tr_tabela=null
integer KKSC_ml=0
integer KKSC_ms=0
integer KKSC_ml_env=0
integer KKSC_ms_env=0
boolean KKSC_mira_antes=false
group KKSC_gl=null
integer KKSC_tique=0
boolean array KKSC_on
boolean array KKSC_sempre
boolean array KKSC_reg
integer array KKSC_kd
integer array KKSC_kp
boolean array KKSC_ks
integer array KKSC_tt
integer array KKSC_tu
real array KKSC_tx
real array KKSC_ty
integer array KKSC_tc
integer array KKSC_tn
real array KKSC_mx
real array KKSC_my
boolean array KKSC_mh
unit array KKSC_cand
trigger KKSC_tk=null
trigger KKSC_tm=null
framehandle array KKSC_bt
integer KKSC_nh=0
integer array KKSC_habs
integer array KKSC_ord
hashtable KKSC_ht=null
integer KKSC_q_hab=0
integer KKSC_q_tecla=0
integer KKSC_q_tipo=0
integer KKSC_q_padrao=0
string array KKSC_campo
integer KKSC_ncampos=0
constant integer KKSC_JANELA=20
constant integer KKSC_REPETE=10
//@ENDGLOBALS

function KKSC_divide takes string s returns nothing
    local integer n=StringLength(s)
    local integer i=0
    local integer ini=0
    set KKSC_ncampos=0
    loop
        exitwhen i>n or KKSC_ncampos>=16
        if i==n or SubString(s, i, i+1)==";" then
            set KKSC_campo[KKSC_ncampos]=SubString(s, ini, i)
            set KKSC_ncampos=KKSC_ncampos+1
            set ini=i+1
        endif
        set i=i+1
    endloop
endfunction

function KKSC_indice takes integer tecla returns integer
    local integer i=0
    loop
        exitwhen i>=KKSC_nt
        if KKSC_tecla[i]==tecla then
            return i
        endif
        set i=i+1
    endloop
    return -1
endfunction

function KKSC_mira takes nothing returns boolean
    local integer i=0
    if KKSC_bt[11]==null or not BlzFrameIsVisible(KKSC_bt[11]) then
        return false
    endif
    loop
        exitwhen i>10
        if KKSC_bt[i]!=null and BlzFrameIsVisible(KKSC_bt[i]) then
            return false
        endif
        set i=i+1
    endloop
    return true
endfunction

function KKSC_hab takes integer hab, integer tecla, string ordem returns nothing
    local integer o=0
    local integer n
    if ordem!="" then
        set o=OrderId(ordem)
        if o==0 then
            return
        endif
    endif
    if KKSC_ht==null then
        set KKSC_ht=InitHashtable()
    endif
    set KKSC_nh=KKSC_nh+1
    set KKSC_habs[KKSC_nh]=hab
    set KKSC_ord[KKSC_nh]=o
    set n=LoadInteger(KKSC_ht, tecla, -1)+1
    call SaveInteger(KKSC_ht, tecla, -1, n)
    call SaveInteger(KKSC_ht, tecla, n, KKSC_nh)
endfunction

function KKSC_tipo takes integer hab, integer k, integer id returns integer
    set KKSC_q_hab=hab
    set KKSC_q_tecla=KKSC_tecla[k]
    set KKSC_q_tipo=0
    set KKSC_q_padrao=0
    if KKSC_tr_tipo==null then
        return 0
    endif
    call TriggerEvaluate(KKSC_tr_tipo)
    if KKSC_q_tipo>=0 then
        return KKSC_q_tipo
    endif
    if KKSC_sempre[id*16+k] then
        return 1
    endif
    return KKSC_q_padrao
endfunction

function KKSC_lanca takes integer id, integer k returns boolean
    local player p=Player(id)
    local integer tecla=KKSC_tecla[k]
    local integer n=0
    local integer i=0
    local integer j
    local integer e
    local integer h
    local integer o
    local integer t
    local integer hid
    local boolean shift=KKSC_ks[id*16+k]
    local boolean ok=false
    local unit alvo=null
    local unit u=null
    local group g
    if KKSC_ht!=null then
        set n=LoadInteger(KKSC_ht, tecla, -1)
    endif
    if n<=0 or KKSC_tn[id]<=0 or (KKSC_tu[id]==0 and not KKSC_mh[id]) then
        set p=null
        return false
    endif
    set g=CreateGroup()
    if KKSC_tu[id]!=0 then
        call GroupEnumUnitsInRange(g, KKSC_tx[id], KKSC_ty[id], 600.0, null)
        loop
            set u=FirstOfGroup(g)
            exitwhen u==null
            call GroupRemoveUnit(g, u)
            if GetHandleId(u)==KKSC_tu[id] and IsUnitVisible(u, p) then
                set alvo=u
            endif
        endloop
    endif
    call GroupEnumUnitsOfPlayer(g, p, null)
    loop
        set u=FirstOfGroup(g)
        exitwhen u==null
        call GroupRemoveUnit(g, u)
        set hid=GetHandleId(u)
        set j=0
        loop
            exitwhen j>=KKSC_tn[id]
            if KKSC_tc[id*12+j]==hid then
                set KKSC_cand[j]=u
            endif
            set j=j+1
        endloop
    endloop
    call DestroyGroup(g)
    set g=null
    loop
        exitwhen i>=KKSC_tn[id]
        set u=KKSC_cand[i]
        set KKSC_cand[i]=null
        if u!=null and not ok and GetOwningPlayer(u)==p and GetWidgetLife(u)>0.405 then
            set j=1
            loop
                exitwhen j>n or ok
                set e=LoadInteger(KKSC_ht, tecla, j)
                set h=KKSC_habs[e]
                if GetUnitAbilityLevel(u, h)>0 then
                    set t=KKSC_tipo(h, k, id)
                    if t==1 or (t==2 and shift) or (t==3 and not shift) then
                        set o=KKSC_ord[e]
                        if o==0 then
                            set o=OrderId(BlzGetAbilityStringLevelField(BlzGetUnitAbility(u, h), ABILITY_SLF_BASE_ORDER_ID_NCL6, GetUnitAbilityLevel(u, h)-1))
                        endif
                        if o!=0 then
                            if alvo!=null then
                                set ok=IssueTargetOrderById(u, o, alvo)
                            endif
                            if not ok and KKSC_mh[id] then
                                set ok=IssuePointOrderById(u, o, KKSC_mx[id], KKSC_my[id])
                            endif
                        endif
                    endif
                endif
                set j=j+1
            endloop
        endif
        set i=i+1
    endloop
    set alvo=null
    set u=null
    set p=null
    return ok
endfunction

function KKSC_resolve takes integer id returns nothing
    local integer k=0
    local integer melhor=-1
    local integer tm=0
    local integer t
    local integer tt=KKSC_tt[id]
    if tt<=0 or KKSC_tique-tt>KKSC_JANELA then
        return
    endif
    loop
        exitwhen k>=KKSC_nt
        set t=KKSC_kp[id*16+k]
        if t>0 and t-tt<=KKSC_JANELA and tt-t<=KKSC_JANELA then
            if melhor<0 then
                set melhor=k
                set tm=t
            elseif t<=tt and (tm>tt or t>tm) then
                set melhor=k
                set tm=t
            elseif t>tt and tm>tt and t<tm then
                set melhor=k
                set tm=t
            endif
        endif
        set k=k+1
    endloop
    if melhor<0 then
        return
    endif
    set KKSC_tt[id]=0
    set KKSC_kp[id*16+melhor]=0
    if KKSC_lanca(id, melhor) then
        if GetLocalPlayer()==Player(id) then
            if KKSC_mira() then
                call ForceUICancel()
            endif
        endif
    endif
endfunction

function KKSC_tecla_evento takes nothing returns nothing
    local integer id=GetPlayerId(GetTriggerPlayer())
    local integer k=KKSC_indice(GetHandleId(BlzGetTriggerPlayerKey()))
    local integer n
    local boolean novo
    if k<0 then
        return
    endif
    set n=id*16+k
    set novo=KKSC_tique-KKSC_kd[n]>KKSC_REPETE
    set KKSC_kd[n]=KKSC_tique
    if novo and KKSC_on[n] then
        set KKSC_kp[n]=KKSC_tique
        set KKSC_ks[n]=BlzBitAnd(BlzGetTriggerPlayerMetaKey(), 1)!=0
        call KKSC_resolve(id)
    endif
endfunction

function KKSC_mouse takes nothing returns nothing
    local integer id=GetPlayerId(GetTriggerPlayer())
    local real x=BlzGetTriggerPlayerMouseX()
    local real y=BlzGetTriggerPlayerMouseY()
    if x==0.0 and y==0.0 then
        return
    endif
    set KKSC_mx[id]=x
    set KKSC_my[id]=y
    set KKSC_mh[id]=true
endfunction

function KKSC_recebe_mascara takes nothing returns nothing
    local player p=GetTriggerPlayer()
    local integer id=GetPlayerId(p)
    local integer ml
    local integer ms
    local integer i=0
    local integer b
    local oskeytype ok
    call KKSC_divide(BlzGetTriggerSyncData())
    if KKSC_ncampos!=2 or KKSC_nt<=0 or id<0 or id>=bj_MAX_PLAYER_SLOTS then
        set p=null
        return
    endif
    set ml=S2I(KKSC_campo[0])
    set ms=S2I(KKSC_campo[1])
    if ml<0 or ms<0 or ml>=KKSC_pot[KKSC_nt-1]*2 or ms>=KKSC_pot[KKSC_nt-1]*2 then
        set p=null
        return
    endif
    if ml!=0 and not KKSC_reg[id] then
        set KKSC_reg[id]=true
        loop
            exitwhen i>=KKSC_nt
            set ok=ConvertOsKeyType(KKSC_tecla[i])
            call BlzTriggerRegisterPlayerKeyEvent(KKSC_tk, p, ok, 0, true)
            call BlzTriggerRegisterPlayerKeyEvent(KKSC_tk, p, ok, 1, true)
            set i=i+1
        endloop
        call TriggerRegisterPlayerEvent(KKSC_tm, p, EVENT_PLAYER_MOUSE_MOVE)
    endif
    set i=0
    loop
        exitwhen i>=KKSC_nt
        set b=ml/KKSC_pot[i]
        set KKSC_on[id*16+i]=b-(b/2)*2==1
        set b=ms/KKSC_pot[i]
        set KKSC_sempre[id*16+i]=b-(b/2)*2==1
        set i=i+1
    endloop
    set ok=null
    set p=null
endfunction

function KKSC_recebe_mira takes nothing returns nothing
    local integer id=GetPlayerId(GetTriggerPlayer())
    local integer i=3
    if id<0 or id>=bj_MAX_PLAYER_SLOTS then
        return
    endif
    call KKSC_divide(BlzGetTriggerSyncData())
    if KKSC_ncampos<3 then
        return
    endif
    set KKSC_tu[id]=S2I(KKSC_campo[0])
    set KKSC_tx[id]=S2R(KKSC_campo[1])
    set KKSC_ty[id]=S2R(KKSC_campo[2])
    set KKSC_tn[id]=0
    loop
        exitwhen i>=KKSC_ncampos or KKSC_tn[id]>=12
        set KKSC_tc[id*12+KKSC_tn[id]]=S2I(KKSC_campo[i])
        set KKSC_tn[id]=KKSC_tn[id]+1
        set i=i+1
    endloop
    set KKSC_tt[id]=KKSC_tique
    call KKSC_resolve(id)
endfunction

function KKSC_envia_mira takes nothing returns nothing
    local unit u=BlzGetMouseFocusUnit()
    local string s
    local integer n=0
    if u==null then
        set s="0;0;0"
    else
        set s=I2S(GetHandleId(u))+";"+I2S(R2I(GetUnitX(u)))+";"+I2S(R2I(GetUnitY(u)))
    endif
    call GroupEnumUnitsSelected(KKSC_gl, GetLocalPlayer(), null)
    loop
        set u=FirstOfGroup(KKSC_gl)
        exitwhen u==null
        call GroupRemoveUnit(KKSC_gl, u)
        if n<12 then
            set s=s+";"+I2S(GetHandleId(u))
            set n=n+1
        endif
    endloop
    call GroupClear(KKSC_gl)
    if n>0 then
        call BlzSendSyncData("KKSCt", s)
    endif
    set u=null
endfunction

function KKSC_tique_f takes nothing returns nothing
    local boolean mira
    set KKSC_tique=KKSC_tique+1
    call TriggerEvaluate(KKSC_tr_mascara)
    if KKSC_ml!=KKSC_ml_env or KKSC_ms!=KKSC_ms_env then
        set KKSC_ml_env=KKSC_ml
        set KKSC_ms_env=KKSC_ms
        call BlzSendSyncData("KKSCm", I2S(KKSC_ml)+";"+I2S(KKSC_ms))
    endif
    if KKSC_ml==0 then
        set KKSC_mira_antes=false
        return
    endif
    set mira=KKSC_mira()
    if mira and not KKSC_mira_antes then
        call KKSC_envia_mira()
    endif
    set KKSC_mira_antes=mira
endfunction

function KKSC_partida takes nothing returns nothing
    local integer i=0
    local trigger a
    local trigger b
    if KKSC_pronto then
        return
    endif
    if KKSC_tr_mascara==null then
        call TimerStart(KKSC_relogio, 0.5, false, function KKSC_partida)
        return
    endif
    set KKSC_pronto=true
    loop
        exitwhen i>11
        set KKSC_bt[i]=BlzGetOriginFrame(ORIGIN_FRAME_COMMAND_BUTTON, i)
        set i=i+1
    endloop
    set KKSC_gl=CreateGroup()
    set KKSC_tk=CreateTrigger()
    call TriggerAddAction(KKSC_tk, function KKSC_tecla_evento)
    set KKSC_tm=CreateTrigger()
    call TriggerAddAction(KKSC_tm, function KKSC_mouse)
    set a=CreateTrigger()
    call TriggerAddAction(a, function KKSC_recebe_mascara)
    set b=CreateTrigger()
    call TriggerAddAction(b, function KKSC_recebe_mira)
    set i=0
    loop
        exitwhen i>=bj_MAX_PLAYERS
        call BlzTriggerRegisterPlayerSyncEvent(a, Player(i), "KKSCm", false)
        call BlzTriggerRegisterPlayerSyncEvent(b, Player(i), "KKSCt", false)
        set i=i+1
    endloop
    call TriggerEvaluate(KKSC_tr_tabela)
    call TimerStart(KKSC_relogio, 0.03, true, function KKSC_tique_f)
    set a=null
    set b=null
endfunction

function KKSC_registra takes integer tecla returns nothing
    if tecla<=0 or KKSC_indice(tecla)>=0 or KKSC_nt>=16 then
        return
    endif
    set KKSC_tecla[KKSC_nt]=tecla
    if KKSC_nt==0 then
        set KKSC_pot[0]=1
    else
        set KKSC_pot[KKSC_nt]=KKSC_pot[KKSC_nt-1]*2
    endif
    set KKSC_nt=KKSC_nt+1
    if KKSC_relogio==null then
        set KKSC_relogio=CreateTimer()
        call TimerStart(KKSC_relogio, 0.5, false, function KKSC_partida)
    endif
endfunction

function KKSC_liga takes boolexpr mascara, boolexpr tipo, boolexpr tabela returns nothing
    if KKSC_tr_mascara!=null then
        return
    endif
    set KKSC_tr_mascara=CreateTrigger()
    call TriggerAddCondition(KKSC_tr_mascara, mascara)
    set KKSC_tr_tipo=CreateTrigger()
    call TriggerAddCondition(KKSC_tr_tipo, tipo)
    set KKSC_tr_tabela=CreateTrigger()
    call TriggerAddCondition(KKSC_tr_tabela, tabela)
endfunction
