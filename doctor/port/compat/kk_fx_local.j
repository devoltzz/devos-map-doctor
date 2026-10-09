//@GLOBALS
constant boolean KK_FX_LIGADO={{KK_FX_LOCAL}}
constant string KK_FX_CHAVE="{{KK_FX_CHAVE}}"
integer array KK_fx_nivel
boolean array KK_fx_escolheu
integer KK_fx_cat=0
player KK_fx_dono=null
integer array KK_fx_pcat
player array KK_fx_pdono
integer KK_fx_pn=0
real KK_fx_pt=-1.0
player array KK_fx_ctx
integer KK_fx_cn=0
real KK_fx_ct=-1.0
timer KK_fx_relogio=null
hashtable KK_fx_ht=null
integer array DB_ef_fxc
player array DB_ef_fxd
effect KK_fx_r_e=null
unit KK_fx_r_u=null
integer KK_fx_r_i=0
lightning KK_fx_r_l=null
boolean KK_fx_r_b=false
//@ENDGLOBALS

function KK_fx_agora takes nothing returns real
    if KK_fx_relogio==null then
        return 0.0
    endif
    return TimerGetElapsed(KK_fx_relogio)
endfunction

function KK_fx_some takes integer cat,player dono returns boolean
    local integer n
    if cat!=1 then
        return false
    endif
    if dono!=null and GetPlayerController(dono)!=MAP_CONTROL_USER then
        return false
    endif
    set n=KK_fx_nivel[GetPlayerId(GetLocalPlayer())]
    if n==2 then
        return true
    endif
    return n==1 and dono!=GetLocalPlayer()
endfunction

function KK_fx_some_ctx takes nothing returns boolean
    if KK_fx_cat!=1 or KK_fx_pt!=KK_fx_agora() then
        return false
    endif
    return KK_fx_some(1, KK_fx_dono)
endfunction

function KK_fx_m takes string m returns string
    if KK_fx_some_ctx() then
        return ""
    endif
    return m
endfunction

function KK_fx_m_vaga takes string m,integer i returns string
    if i>=0 and KK_fx_some(DB_ef_fxc[i], DB_ef_fxd[i]) then
        return ""
    endif
    return m
endfunction

function KK_fx_anota takes integer i returns nothing
    if i<0 then
        return
    endif
    if KK_fx_cat==1 and KK_fx_pt==KK_fx_agora() then
        set DB_ef_fxc[i]=1
        set DB_ef_fxd[i]=KK_fx_dono
    else
        set DB_ef_fxc[i]=0
        set DB_ef_fxd[i]=null
    endif
endfunction

function KK_fx_unidade takes unit u returns nothing
    if u!=null and KK_fx_some_ctx() then
        call SetUnitVertexColor(u, 255, 255, 255, 0)
    endif
endfunction

function KK_fx_raio takes lightning l returns nothing
    if l!=null and KK_fx_some_ctx() then
        call SetLightningColor(l, 1.0, 1.0, 1.0, 0.0)
    endif
endfunction

function KK_fx_liga takes player d returns nothing
    local real t=KK_fx_agora()
    if t!=KK_fx_pt then
        set KK_fx_pn=0
        set KK_fx_cat=0
        set KK_fx_dono=null
        set KK_fx_pt=t
    endif
    set KK_fx_pcat[KK_fx_pn]=KK_fx_cat
    set KK_fx_pdono[KK_fx_pn]=KK_fx_dono
    set KK_fx_pn=KK_fx_pn+1
    set KK_fx_cat=1
    set KK_fx_dono=d
endfunction

function KK_fx_desliga takes nothing returns nothing
    if KK_fx_pn>0 then
        set KK_fx_pn=KK_fx_pn-1
        set KK_fx_cat=KK_fx_pcat[KK_fx_pn]
        set KK_fx_dono=KK_fx_pdono[KK_fx_pn]
        set KK_fx_pdono[KK_fx_pn]=null
    else
        set KK_fx_cat=0
        set KK_fx_dono=null
    endif
endfunction

function KK_fx_empilha takes player p returns nothing
    local real t=KK_fx_agora()
    if t!=KK_fx_ct then
        set KK_fx_cn=0
        set KK_fx_ct=t
    endif
    set KK_fx_ctx[KK_fx_cn]=p
    set KK_fx_cn=KK_fx_cn+1
endfunction

function KK_fx_desempilha takes nothing returns nothing
    if KK_fx_cn>0 then
        set KK_fx_cn=KK_fx_cn-1
        set KK_fx_ctx[KK_fx_cn]=null
    endif
endfunction

function KK_fx_de_relogio takes timer t returns player
    local integer k
    if t==null or KK_fx_ht==null then
        return null
    endif
    set k=LoadInteger(KK_fx_ht, GetHandleId(t), 0)
    if k>0 then
        return Player(k-1)
    endif
    return null
endfunction

function KK_fx_de takes nothing returns player
    local player p=null
    if KK_fx_cn>0 and KK_fx_ct==KK_fx_agora() then
        set p=KK_fx_ctx[KK_fx_cn-1]
    endif
    if p==null and DB_gtu()!=null then
        set p=GetOwningPlayer(DB_gtu())
    endif
    return p
endfunction

function KK_fx_relogio_entra takes nothing returns nothing
    call KK_fx_empilha(KK_fx_de_relogio(GetExpiredTimer()))
endfunction

function KK_fx_relogio_sai takes nothing returns nothing
    call KK_fx_desempilha()
endfunction

function KK_fx_TimerStart takes timer t,real r,boolean per,code c returns nothing
    local player d
    if t!=null and KK_fx_ht!=null then
        set d=KK_fx_de()
        if d!=null then
            call SaveInteger(KK_fx_ht, GetHandleId(t), 0, GetPlayerId(d)+1)
        else
            call RemoveSavedInteger(KK_fx_ht, GetHandleId(t), 0)
        endif
        set d=null
    endif
    call TimerStart(t, r, per, c)
endfunction

function KK_fx_relogio_solta takes timer t returns nothing
    if t!=null and KK_fx_ht!=null then
        call RemoveSavedInteger(KK_fx_ht, GetHandleId(t), 0)
    endif
endfunction

function KK_fx_TriggerEvaluate takes trigger g returns boolean
    call KK_fx_empilha(KK_fx_de())
    set KK_fx_r_b=TriggerEvaluate(g)
    call KK_fx_desempilha()
    return KK_fx_r_b
endfunction

function KK_fxj_DB_efx_cria takes string m,real x,real y returns effect
    call KK_fx_liga(KK_fx_de())
    set KK_fx_r_e=DB_efx_cria(m, x, y)
    call KK_fx_desliga()
    return KK_fx_r_e
endfunction

function KK_fxj_DB_efx_cria_loc takes string m,location l returns effect
    call KK_fx_liga(KK_fx_de())
    set KK_fx_r_e=DB_efx_cria_loc(m, l)
    call KK_fx_desliga()
    return KK_fx_r_e
endfunction

function KK_fxj_DB_efx_cria_alvo takes string m,widget w,string a returns effect
    call KK_fx_liga(KK_fx_de())
    set KK_fx_r_e=DB_efx_cria_alvo(m, w, a)
    call KK_fx_desliga()
    return KK_fx_r_e
endfunction

function KK_fxj_DB_efx_cria_loc_bj takes location l,string m returns effect
    call KK_fx_liga(KK_fx_de())
    set KK_fx_r_e=DB_efx_cria_loc_bj(l, m)
    call KK_fx_desliga()
    return KK_fx_r_e
endfunction

function KK_fxj_DB_efx_cria_alvo_bj takes string a,widget w,string m returns effect
    call KK_fx_liga(KK_fx_de())
    set KK_fx_r_e=DB_efx_cria_alvo_bj(a, w, m)
    call KK_fx_desliga()
    return KK_fx_r_e
endfunction

function KK_fxj_DzSetUnitModel takes unit u,string m returns nothing
    call KK_fx_liga(KK_fx_de())
    call DzSetUnitModel(u, m)
    call KK_fx_desliga()
endfunction

function KK_fxj_AddLightningEx takes string c,boolean v,real x1,real y1,real z1,real x2,real y2,real z2 returns lightning
    call KK_fx_liga(KK_fx_de())
    set KK_fx_r_l=AddLightningEx(c, v, x1, y1, z1, x2, y2, z2)
    call KK_fx_raio(KK_fx_r_l)
    call KK_fx_desliga()
    return KK_fx_r_l
endfunction

function KK_fxj_AddLightning takes string c,boolean v,real x1,real y1,real x2,real y2 returns lightning
    call KK_fx_liga(KK_fx_de())
    set KK_fx_r_l=AddLightning(c, v, x1, y1, x2, y2)
    call KK_fx_raio(KK_fx_r_l)
    call KK_fx_desliga()
    return KK_fx_r_l
endfunction

function KK_fx_diz takes player p,string t returns nothing
    if p==GetLocalPlayer() then
        call DisplayTimedTextToPlayer(p, 0, 0, 20.0, t)
    endif
endfunction

function KK_fx_nome takes integer n returns string
    if n==1 then
        return "|cFFFFCC00MINE|r (other players' skill and item effects are hidden on your screen)"
    elseif n==2 then
        return "|cFFFF5555OFF|r (the skill and item effects of all players, yours too, are hidden on your screen)"
    endif
    return "|cFF66FF66ALL|r (every effect is shown)"
endfunction

function KK_fx_pref_grava takes player p returns nothing
    local integer i
    if p==null or not DB_rede_pronto then
        return
    endif
    set i=GetPlayerId(p)
    if KK_fx_nivel[i]!=0 or DB_get(p, KK_FX_CHAVE)!="" then
        call DB_put(p, KK_FX_CHAVE, I2S(KK_fx_nivel[i]))
    endif
endfunction

function KK_fx_cmd takes nothing returns nothing
    local player p=GetTriggerPlayer()
    local integer i=GetPlayerId(p)
    local string s=StringCase(GetEventPlayerChatString(), false)
    local integer n=StringLength(s)
    local integer a=3
    local integer b
    local string arg
    if SubString(s, 0, 3)!="-fx" or (n>3 and SubString(s, 3, 4)!=" ") then
        set p=null
        return
    endif
    loop
        exitwhen a>=n or SubString(s, a, a+1)!=" "
        set a=a+1
    endloop
    set b=n
    loop
        exitwhen b<=a or SubString(s, b-1, b)!=" "
        set b=b-1
    endloop
    set arg=SubString(s, a, b)
    if arg=="all" then
        set KK_fx_nivel[i]=0
    elseif arg=="mine" then
        set KK_fx_nivel[i]=1
    elseif arg=="off" or arg=="none" then
        set KK_fx_nivel[i]=2
    else
        call KK_fx_diz(p, "|cFFFFCC00Effects:|r "+KK_fx_nome(KK_fx_nivel[i])+"|nType |cFFFFCC00-fx all|r (show every effect), |cFFFFCC00-fx mine|r (hide other players' skill and item effects) or |cFFFFCC00-fx off|r (hide the skill and item effects of all players, yours too). Boss attacks and warnings always show.")
        set p=null
        return
    endif
    set KK_fx_escolheu[i]=true
    call KK_fx_pref_grava(p)
    call KK_fx_diz(p, "|cFFFFCC00Effects:|r "+KK_fx_nome(KK_fx_nivel[i])+". New effects follow it; boss attacks and warnings always show.")
    set p=null
endfunction

function KK_fx_pref_recebe takes nothing returns nothing
    local player p=GetTriggerPlayer()
    local integer i=GetPlayerId(p)
    local string v=BlzGetTriggerSyncData()
    if not KK_fx_escolheu[i] then
        if v=="1" then
            set KK_fx_nivel[i]=1
        elseif v=="2" then
            set KK_fx_nivel[i]=2
        endif
        if KK_fx_nivel[i]!=0 then
            call KK_fx_diz(p, "|cFFFFCC00Effects:|r your saved setting is back: "+KK_fx_nome(KK_fx_nivel[i])+". Type |cFFFFCC00-fx|r to change it.")
        endif
    endif
    set p=null
endfunction

function KK_fx_pref_anuncia takes nothing returns nothing
    local string v
    if not DB_rede_pronto then
        call TimerStart(GetExpiredTimer(), 1.00, false, function KK_fx_pref_anuncia)
        return
    endif
    set v=DB_get(GetLocalPlayer(), KK_FX_CHAVE)
    if v=="1" or v=="2" then
        call BlzSendSyncData("kkfx", v)
    endif
    call DestroyTimer(GetExpiredTimer())
endfunction

function KK_fx_init takes nothing returns nothing
    local trigger t
    local integer i
    if KK_fx_ht!=null then
        return
    endif
    set KK_fx_ht=InitHashtable()
    set KK_fx_relogio=CreateTimer()
    call TimerStart(KK_fx_relogio, 1000000.0, false, null)
    set t=CreateTrigger()
    set i=0
    loop
        exitwhen i>=bj_MAX_PLAYERS
        call TriggerRegisterPlayerChatEvent(t, Player(i), "-fx", false)
        set i=i+1
    endloop
    call TriggerAddAction(t, function KK_fx_cmd)
    set t=CreateTrigger()
    set i=0
    loop
        exitwhen i>=bj_MAX_PLAYERS
        call BlzTriggerRegisterPlayerSyncEvent(t, Player(i), "kkfx", false)
        set i=i+1
    endloop
    call TriggerAddAction(t, function KK_fx_pref_recebe)
    call TimerStart(CreateTimer(), 8.00, false, function KK_fx_pref_anuncia)
    set t=null
endfunction
