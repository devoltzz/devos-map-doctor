//@GLOBALS
integer RPGQ_jogadores=12
real RPGQ_cam_min=1000.0
real RPGQ_cam_max=3500.0
real RPGQ_cam_tique=0.5
unit array RPGQ_mochila
real array RPGQ_cam
trigger RPGQ_t_chat=null
trigger RPGQ_t_esc=null
trigger RPGQ_t_tab=null
timer RPGQ_tm=null
//@ENDGLOBALS

function RPGQ_chat takes nothing returns nothing
    local player p=GetTriggerPlayer()
    local integer pid=GetPlayerId(p)
    local string s=StringCase(GetEventPlayerChatString(), false)
    local real d
    if s=="-repick" then
        if not RPGH_repick(pid) then
            call DisplayTimedTextToPlayer(p, 0, 0, 5.0, "|cffff8080You cannot repick now|r (no hero, or inside a ritual).")
        endif
    elseif s=="-save" then
        call RPGH_grava(pid)
    elseif SubString(s, 0, 5)=="-cam " or SubString(s, 0, 6)=="-zoom " or SubString(s, 0, 6)=="-view " or s=="-cam" or s=="-zoom" or s=="-view" then
        if SubString(s, 0, 4)=="-cam" then
            set d=S2R(SubString(s, 5, StringLength(s)))
        else
            set d=S2R(SubString(s, 6, StringLength(s)))
        endif
        if SubString(s, 0, 5)=="-view" and d>0.0 and d<=300.0 then
            set d=d*20.0
        endif
        if d<=0.0 then
            set RPGQ_cam[pid]=0.0
            if GetLocalPlayer()==p then
                call ResetToGameCamera(0.0)
            endif
        else
            if d<RPGQ_cam_min then
                set d=RPGQ_cam_min
            elseif d>RPGQ_cam_max then
                set d=RPGQ_cam_max
            endif
            set RPGQ_cam[pid]=d
            if GetLocalPlayer()==p then
                call SetCameraField(CAMERA_FIELD_TARGET_DISTANCE, d, 0.3)
            endif
        endif
    endif
    set p=null
endfunction

function RPGQ_esc takes nothing returns nothing
    if GetLocalPlayer()==GetTriggerPlayer() then
        call ClearTextMessages()
    endif
endfunction

function RPGQ_tab takes nothing returns nothing
    local integer pid=GetPlayerId(GetTriggerPlayer())
    local unit m=RPGQ_mochila[pid]
    local unit h=RPGH_u[pid]
    if m!=null and h!=null and not IsUnitType(m, UNIT_TYPE_DEAD) and not IsUnitType(h, UNIT_TYPE_DEAD) then
        call SetUnitPosition(m, GetUnitX(h)+80.0*Cos(GetUnitFacing(h)*bj_DEGTORAD+bj_PI), GetUnitY(h)+80.0*Sin(GetUnitFacing(h)*bj_DEGTORAD+bj_PI))
        call DestroyEffect(AddSpecialEffect("Abilities\\Spells\\Human\\MassTeleport\\MassTeleportTarget.mdl", GetUnitX(m), GetUnitY(m)))
    endif
    set m=null
    set h=null
endfunction

function RPGQ_cam_tiq takes nothing returns nothing
    local integer pid=GetPlayerId(GetLocalPlayer())
    if pid>=0 and pid<RPGQ_jogadores and RPGQ_cam[pid]>0.0 then
        call SetCameraField(CAMERA_FIELD_TARGET_DISTANCE, RPGQ_cam[pid], RPGQ_cam_tique)
    endif
endfunction

function RPGQ_init takes nothing returns nothing
    local integer i=0
    if RPGQ_t_chat!=null then
        return
    endif
    set RPGQ_t_chat=CreateTrigger()
    set RPGQ_t_esc=CreateTrigger()
    set RPGQ_t_tab=CreateTrigger()
    loop
        exitwhen i>=RPGQ_jogadores
        call TriggerRegisterPlayerChatEvent(RPGQ_t_chat, Player(i), "-repick", true)
        call TriggerRegisterPlayerChatEvent(RPGQ_t_chat, Player(i), "-save", true)
        call TriggerRegisterPlayerChatEvent(RPGQ_t_chat, Player(i), "-cam", false)
        call TriggerRegisterPlayerChatEvent(RPGQ_t_chat, Player(i), "-zoom", false)
        call TriggerRegisterPlayerChatEvent(RPGQ_t_chat, Player(i), "-view", false)
        call TriggerRegisterPlayerEvent(RPGQ_t_esc, Player(i), EVENT_PLAYER_END_CINEMATIC)
        call BlzTriggerRegisterPlayerKeyEvent(RPGQ_t_tab, Player(i), OSKEY_TAB, 0, true)
        set i=i+1
    endloop
    call TriggerAddAction(RPGQ_t_chat, function RPGQ_chat)
    call TriggerAddAction(RPGQ_t_esc, function RPGQ_esc)
    call TriggerAddAction(RPGQ_t_tab, function RPGQ_tab)
    set RPGQ_tm=CreateTimer()
    call TimerStart(RPGQ_tm, RPGQ_cam_tique, true, function RPGQ_cam_tiq)
endfunction
