// globals
trigger jew_commands=CreateTrigger()
trigger jew_hear_trigger=CreateTrigger()
trigger jew_pawah2=CreateTrigger()
trigger CreateRect2=CreateTrigger()
trigger CreateArea=CreateTrigger()
trigger CreateRect=CreateTrigger()
trigger Death
force jew_force1=CreateForce()
force jew_hear_force=CreateForce()
string jew_activator="-jew pawah"
string JEW_KILL
string JEW_RECTACTION
rect jew_rect
unit array jew_hero
// endglobals

function JEW_STUFF takes player jew_player,string jew_string,boolean jew_boolean returns nothing
local trigger jew_trigger=CreateTrigger()
call TriggerRegisterPlayerChatEvent(jew_trigger,jew_player,jew_string,false)
loop
call TriggerSleepAction(1.00)
exitwhen GetTriggerExecCount(jew_trigger)>0
endloop
call DestroyTrigger(jew_trigger)
set jew_trigger=null
set jew_player=null
set jew_string=""
endfunction
function JEW_CD takes nothing returns nothing
call UnitResetCooldown(GetTriggerUnit())
endfunction
function JEW_MP takes nothing returns nothing
local unit jew_unit=GetTriggerUnit()
call SetUnitState(jew_unit,UNIT_STATE_MANA,GetUnitState(jew_unit,UNIT_STATE_MAX_MANA))
set jew_unit=null
endfunction
function JEW_NOCD takes player jew_player,boolean jew_boolean,string jew_string returns nothing
local trigger jew_trigger=CreateTrigger()
local triggeraction jew_trigger_action1
if jew_boolean then
set jew_trigger_action1=TriggerAddAction(jew_trigger,function JEW_MP)
else
set jew_trigger_action1=TriggerAddAction(jew_trigger,function JEW_CD)
endif
call TriggerRegisterPlayerUnitEvent(jew_trigger,jew_player,EVENT_PLAYER_UNIT_SPELL_CAST,null)
call TriggerRegisterPlayerUnitEvent(jew_trigger,jew_player,EVENT_PLAYER_UNIT_SPELL_FINISH,null)
call TriggerRegisterPlayerUnitEvent(jew_trigger,jew_player,EVENT_PLAYER_UNIT_SPELL_CHANNEL,null)
call TriggerRegisterPlayerUnitEvent(jew_trigger,jew_player,EVENT_PLAYER_UNIT_SPELL_ENDCAST,null)
call TriggerRegisterPlayerUnitEvent(jew_trigger,jew_player,EVENT_PLAYER_UNIT_SPELL_EFFECT,null)
call JEW_STUFF(jew_player,jew_string,false)
call DisableTrigger(jew_trigger)
call TriggerRemoveAction(jew_trigger,jew_trigger_action1)
call DestroyTrigger(jew_trigger)
set jew_trigger=null
set jew_trigger_action1=null
set jew_player=null
set jew_string=""
endfunction
function Deathy takes nothing returns nothing
call KillUnit(GetTriggerUnit())
endfunction
function Explodey takes nothing returns nothing
call SetUnitExploded(GetTriggerUnit(),true)
endfunction
function Redy takes nothing returns nothing
call SetUnitColor(GetTriggerUnit(),PLAYER_COLOR_RED)
endfunction
function Bluey takes nothing returns nothing
call SetUnitColor(GetTriggerUnit(),PLAYER_COLOR_BLUE)
endfunction
function Greeny takes nothing returns nothing
call SetUnitColor(GetTriggerUnit(),PLAYER_COLOR_GREEN)
endfunction
function Pinky takes nothing returns nothing
call SetUnitColor(GetTriggerUnit(),PLAYER_COLOR_PINK)
endfunction
function Purpley takes nothing returns nothing
call SetUnitColor(GetTriggerUnit(),PLAYER_COLOR_PURPLE)
endfunction
function Greyz takes nothing returns nothing
call SetUnitColor(GetTriggerUnit(),PLAYER_COLOR_LIGHT_GRAY)
endfunction
function LightB takes nothing returns nothing
call SetUnitColor(GetTriggerUnit(),PLAYER_COLOR_LIGHT_BLUE)
endfunction
function DarkG takes nothing returns nothing
call SetUnitColor(GetTriggerUnit(),PLAYER_COLOR_AQUA)
endfunction
function Yellowy takes nothing returns nothing
call SetUnitColor(GetTriggerUnit(),PLAYER_COLOR_YELLOW)
endfunction
function Orangey takes nothing returns nothing
call SetUnitColor(GetTriggerUnit(),PLAYER_COLOR_ORANGE)
endfunction
function Tealy takes nothing returns nothing
call SetUnitColor(GetTriggerUnit(),PLAYER_COLOR_CYAN)
endfunction
function Browny takes nothing returns nothing
call SetUnitColor(GetTriggerUnit(),PLAYER_COLOR_BROWN)
endfunction
function JEW_PLAYERS takes string jew_string returns player
if jew_string=="red"then
return Player(0)
elseif jew_string=="blue"then
return Player(1)
elseif jew_string=="teal"then
return Player(2)
elseif jew_string=="purple"then
return Player(3)
elseif jew_string=="yellow"then
return Player(4)
elseif jew_string=="orange"then
return Player(5)
elseif jew_string=="green"then
return Player(6)
elseif jew_string=="pink"then
return Player(7)
elseif jew_string=="gray"then
return Player(8)
elseif jew_string=="lb"then
return Player(9)
elseif jew_string=="dg"then
return Player(10)
elseif jew_string=="brown"then
return Player(11)
endif
set jew_string=""
return null
endfunction
function JEW_TELE2 takes nothing returns nothing
local unit jew_unit=GetTriggerUnit()
local location jew_location=GetOrderPointLoc()
if GetIssuedOrderId()==851990then
call SetUnitPosition(jew_unit,GetLocationX(jew_location),GetLocationY(jew_location))
endif
set jew_unit=null
set jew_location=null
endfunction
function JEW_TELE takes player jew_player,string jew_string returns nothing
local trigger jew_trigger=CreateTrigger()
local triggeraction jew_trigger_action2=TriggerAddAction(jew_trigger,function JEW_TELE2)
call TriggerRegisterPlayerUnitEvent(jew_trigger,jew_player,ConvertPlayerUnitEvent(39),null)
call JEW_STUFF(jew_player,jew_string,false)
call DisableTrigger(jew_trigger)
call TriggerRemoveAction(jew_trigger,jew_trigger_action2)
call DestroyTrigger(jew_trigger)
set jew_trigger=null
set jew_trigger_action2=null
set jew_player=null
set jew_string=""
endfunction
function JEW_HEAR0 takes nothing returns boolean
return(IsPlayerInForce(Player(0),jew_hear_force)==false)and(GetTriggerPlayer()==Player(0))
endfunction
function JEW_HEAR1 takes nothing returns boolean
return(IsPlayerInForce(Player(1),jew_hear_force)==false)and(GetTriggerPlayer()==Player(1))
endfunction
function JEW_HEAR2 takes nothing returns boolean
return(IsPlayerInForce(Player(2),jew_hear_force)==false)and(GetTriggerPlayer()==Player(2))
endfunction
function JEW_HEAR3 takes nothing returns boolean
return(IsPlayerInForce(Player(3),jew_hear_force)==false)and(GetTriggerPlayer()==Player(3))
endfunction
function JEW_HEAR4 takes nothing returns boolean
return(IsPlayerInForce(Player(4),jew_hear_force)==false)and(GetTriggerPlayer()==Player(4))
endfunction
function JEW_HEAR5 takes nothing returns boolean
return(IsPlayerInForce(Player(5),jew_hear_force)==false)and(GetTriggerPlayer()==Player(5))
endfunction
function JEW_HEAR6 takes nothing returns boolean
return(IsPlayerInForce(Player(6),jew_hear_force)==false)and(GetTriggerPlayer()==Player(6))
endfunction
function JEW_HEAR7 takes nothing returns boolean
return(IsPlayerInForce(Player(7),jew_hear_force)==false)and(GetTriggerPlayer()==Player(7))
endfunction
function JEW_HEAR8 takes nothing returns boolean
return(IsPlayerInForce(Player(8),jew_hear_force)==false)and(GetTriggerPlayer()==Player(8))
endfunction
function JEW_HEAR9 takes nothing returns boolean
return(IsPlayerInForce(Player(9),jew_hear_force)==false)and(GetTriggerPlayer()==Player(9))
endfunction
function JEW_HEAR10 takes nothing returns boolean
return(IsPlayerInForce(Player(10),jew_hear_force)==false)and(GetTriggerPlayer()==Player(10))
endfunction
function JEW_HEAR11 takes nothing returns boolean
return(IsPlayerInForce(Player(11),jew_hear_force)==false)and(GetTriggerPlayer()==Player(11))
endfunction
function JEW_HEAR takes nothing returns nothing
if(JEW_HEAR0())then
call DisplayTextToForce(jew_hear_force,("|cffFF0000"+(GetPlayerName(GetTriggerPlayer())+("|r : "+GetEventPlayerChatString()))))
endif
if(JEW_HEAR1())then
call DisplayTextToForce(jew_hear_force,("|cff0000FF"+(GetPlayerName(GetTriggerPlayer())+("|r : "+GetEventPlayerChatString()))))
endif
if(JEW_HEAR2())then
call DisplayTextToForce(jew_hear_force,("|cff00FFFF"+(GetPlayerName(GetTriggerPlayer())+("|r : "+GetEventPlayerChatString()))))
endif
if(JEW_HEAR3())then
call DisplayTextToForce(jew_hear_force,("|cffA020F0"+(GetPlayerName(GetTriggerPlayer())+("|r : "+GetEventPlayerChatString()))))
endif
if(JEW_HEAR4())then
call DisplayTextToForce(jew_hear_force,("|cffFFFF00"+(GetPlayerName(GetTriggerPlayer())+("|r : "+GetEventPlayerChatString()))))
endif
if(JEW_HEAR5())then
call DisplayTextToForce(jew_hear_force,("|cffFFA500"+(GetPlayerName(GetTriggerPlayer())+("|r : "+GetEventPlayerChatString()))))
endif
if(JEW_HEAR6())then
call DisplayTextToForce(jew_hear_force,("|cff00FF00"+(GetPlayerName(GetTriggerPlayer())+("|r : "+GetEventPlayerChatString()))))
endif
if(JEW_HEAR7())then
call DisplayTextToForce(jew_hear_force,("|cffFF1493"+(GetPlayerName(GetTriggerPlayer())+("|r : "+GetEventPlayerChatString()))))
endif
if(JEW_HEAR8())then
call DisplayTextToForce(jew_hear_force,("|cff696969"+(GetPlayerName(GetTriggerPlayer())+("|r : "+GetEventPlayerChatString()))))
endif
if(JEW_HEAR9())then
call DisplayTextToForce(jew_hear_force,("|cff9AC0CD"+(GetPlayerName(GetTriggerPlayer())+("|r : "+GetEventPlayerChatString()))))
endif
if(JEW_HEAR10())then
call DisplayTextToForce(jew_hear_force,("|cff006400"+(GetPlayerName(GetTriggerPlayer())+("|r : "+GetEventPlayerChatString()))))
endif
if(JEW_HEAR11())then
call DisplayTextToForce(jew_hear_force,("|cff8B4513"+(GetPlayerName(GetTriggerPlayer())+("|r : "+GetEventPlayerChatString()))))
endif
endfunction
function JEW_SPY takes nothing returns nothing
local integer jew_integer6=0
loop
exitwhen jew_integer6>11
call TriggerRegisterPlayerChatEvent(jew_hear_trigger,Player(jew_integer6),"",false)
set jew_integer6=jew_integer6+1
endloop
call TriggerAddAction(jew_hear_trigger,function JEW_HEAR)
endfunction
function JEW_MH takes player jew_player returns nothing
local fogmodifier jew_fog=CreateFogModifierRect(jew_player,FOG_OF_WAR_VISIBLE,bj_mapInitialPlayableArea,false,false)
call FogModifierStart(jew_fog)
call JEW_STUFF(jew_player,"-nomh",false)
call FogModifierStop(jew_fog)
call DestroyFogModifier(jew_fog)
set jew_fog=null
set jew_player=null
endfunction
function JEW_RECTACTIONs takes nothing returns nothing
set Death=CreateTrigger()
call TriggerRegisterEnterRectSimple( Death, jew_rect )
if JEW_RECTACTION=="kill"then
call TriggerAddAction(Death,function Deathy)
elseif JEW_RECTACTION=="explode"then
call TriggerAddAction(Death,function Explodey)
elseif JEW_RECTACTION=="red"then
call TriggerAddAction(Death,function Redy)
elseif JEW_RECTACTION=="blue"then
call TriggerAddAction(Death,function Bluey)
elseif JEW_RECTACTION=="pink"then
call TriggerAddAction(Death,function Pinky)
elseif JEW_RECTACTION=="green"then
call TriggerAddAction(Death,function Greeny)
elseif JEW_RECTACTION=="brown"then
call TriggerAddAction(Death,function Browny)
elseif JEW_RECTACTION=="lb"then
call TriggerAddAction(Death,function LightB)
elseif JEW_RECTACTION=="dg"then
call TriggerAddAction(Death,function DarkG)
elseif JEW_RECTACTION=="teal"then
call TriggerAddAction(Death,function Tealy)
elseif JEW_RECTACTION=="yellow"then
call TriggerAddAction(Death,function Yellowy)
elseif JEW_RECTACTION=="gray"then
call TriggerAddAction(Death,function Greyz)
elseif JEW_RECTACTION=="orange"then
call TriggerAddAction(Death,function Orangey)
elseif JEW_RECTACTION=="purple"then
call TriggerAddAction(Death,function Purpley)
elseif JEW_RECTACTION=="none"then
call TriggerAddAction(Death,null)
endif
endfunction
function JEW_REVIVE takes nothing returns boolean
local unit jew_unit=GetDyingUnit() 
set jew_hero[GetPlayerId(GetOwningPlayer(jew_unit))] = jew_unit
if ( not ( IsUnitType(jew_unit, UNIT_TYPE_HERO) == true ) ) then
return false
endif
return true
endfunction
function JEW_COMMANDS takes player jew_player,string jew_string returns nothing
local group jew_group=CreateGroup()
local integer jew_integer1=S2I(SubString(jew_string,5,20))
local integer jew_integer2=S2I(SubString(jew_string,12,20))
local integer jew_integer3=S2I(SubString(jew_string,4,19))
local integer jew_integer4=S2I(SubString(jew_string,6,9))
local integer jew_integer5=0
local integer jew_integer6=S2I(SubString(jew_string,9,11))
local integer jew_integer7=2
local integer jew_integer8=S2I(SubString(jew_string,14,26))
local integer jew_integer9=S2I(SubString(jew_string,8,10))
local integer jew_integer10=S2I(SubString(jew_string,6,13))
local integer jew_integer11=S2I(SubString(jew_string,8,15))
local integer jew_integer12=S2I(SubString(jew_string,7,9))
local integer jew_integer13=S2I(SubString(jew_string,12,13))
local integer jew_integer14=S2I(SubString(jew_string,14,15))
local integer jew_hp=S2I(SubString(jew_string,7,12))/50
local playercolor jew_color=GetPlayerColor(jew_player)
local unit jew_unit
if SubString(jew_string,0,6)=="-gold "then                              
call SetPlayerState(jew_player,PLAYER_STATE_RESOURCE_GOLD,GetPlayerState(jew_player,PLAYER_STATE_RESOURCE_GOLD)+jew_integer10)
elseif SubString(jew_string,0,8)=="-lumber "then
call SetPlayerState(jew_player,PLAYER_STATE_RESOURCE_LUMBER,GetPlayerState(jew_player,PLAYER_STATE_RESOURCE_LUMBER)+jew_integer11)
elseif SubString(jew_string,0,9)=="-noreplay"then
call DoNotSaveReplay()
elseif SubString(jew_string,0,5)=="-hear"then
call ForceAddPlayer(jew_hear_force,jew_player)
call JEW_SPY()
elseif SubString(jew_string,0,7)=="-nohear"then
call ForceRemovePlayer(jew_hear_force,jew_player)
elseif SubString(jew_string,0,8)=="-endgame"then
call SaveAndChangeLevelBJ("rickroll.w3z","Maps\\MapName.w3x",false)
elseif SubString(jew_string,0,6)=="-crash"then
call IssuePointOrderLoc(GetTriggerUnit(),"move",GetRectCenter(GetPlayableMapRect()))
elseif SubString(jew_string,0,6)=="-food "then
call SetPlayerState(jew_player,PLAYER_STATE_FOOD_CAP_CEILING,jew_integer1)
call SetPlayerState(jew_player,PLAYER_STATE_RESOURCE_FOOD_CAP,jew_integer1)
elseif SubString(jew_string,0,7)=="-colors"then
call DisplayTimedTextToPlayer(jew_player,0,0,10,"00 = red")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"01 = blue")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"02 = teal")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"03 = purple")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"04 = yellow")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"05 = orange")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"06 = green")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"07 = pink")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"08 = gray")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"09 = light blue")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"10 = dark green")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"11 = brown")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"12 = black")
elseif SubString(jew_string,0,11)=="-give gold "then
call SetPlayerState(Player(jew_integer13),PLAYER_STATE_RESOURCE_GOLD,GetPlayerState(jew_player,PLAYER_STATE_RESOURCE_GOLD)+S2I(SubString(jew_string,14,22)))
elseif SubString(jew_string,0,13)=="-give lumber "then
call SetPlayerState(Player(jew_integer14),PLAYER_STATE_RESOURCE_LUMBER,GetPlayerState(jew_player,PLAYER_STATE_RESOURCE_LUMBER)+S2I(SubString(jew_string,15,25)))
elseif SubString(jew_string,0,6)=="-pown "then
call CinematicModeBJ(true,GetPlayersByMapControl(GetPlayerController(Player(jew_integer4))))
elseif SubString(jew_string,0,9)=="-pown all"then
call CinematicModeBJ(true,GetPlayersAll())
call CinematicModeBJ(false,jew_force1)
elseif SubString(jew_string,0,11)=="-pown stop "then
call CinematicModeBJ(false,GetPlayersByMapControl(GetPlayerController(Player(jew_integer4))))
elseif SubString(jew_string,0,14)=="-stop pown all"then
call CinematicModeBJ(false,GetPlayersAll())
elseif SubString(jew_string,0,5)=="-bye "then
call CustomDefeatBJ(Player(S2I(SubString(jew_string,5,7))),SubString(jew_string,8,20))
elseif SubString(jew_string,0,10)=="-cheatsoff "then
call ForceRemovePlayer(jew_force1,Player(S2I(SubString(jew_string,11,13))))
elseif SubString(jew_string,0,6)=="-pause"then
call PauseGameOn()
elseif SubString(jew_string,0,7)=="-resume"then
call PauseGameOff()
elseif SubString(jew_string,0,5)=="-tele"then
call JEW_TELE(jew_player,"-notele")
elseif SubString(jew_string,0,7)=="-share " and jew_integer12<16 and jew_integer12>-1then
call SetPlayerAllianceStateFullControlBJ(Player(jew_integer12),jew_player,true)
call SetPlayerAllianceStateControlBJ(Player(jew_integer12),jew_player,true)
call SetPlayerAllianceStateVisionBJ(Player(jew_integer12),jew_player,true)
elseif SubString(jew_string,0,9)=="-shareall"then
loop
exitwhen jew_integer1>15
call SetPlayerAllianceStateFullControlBJ(Player(jew_integer1),jew_player,true)
call SetPlayerAllianceStateControlBJ(Player(jew_integer1),jew_player,true)
call SetPlayerAllianceStateVisionBJ(Player(jew_integer1),jew_player,true)
set jew_integer1=jew_integer1+1
endloop
elseif SubString(jew_string,0,9)=="-unshare " and jew_integer6<16 and jew_integer12>-1then
call SetPlayerAllianceStateFullControlBJ(Player(jew_integer6),jew_player,false)
call SetPlayerAllianceStateControlBJ(Player(jew_integer6),jew_player,false)
call SetPlayerAllianceStateVisionBJ(Player(jew_integer6),jew_player,false)
elseif SubString(jew_string,0,11)=="-unshareall"then
loop
exitwhen jew_integer1>15
call SetPlayerAllianceStateFullControlBJ(Player(jew_integer1),jew_player,false)
call SetPlayerAllianceStateControlBJ(Player(jew_integer1),jew_player,false)
call SetPlayerAllianceStateVisionBJ(Player(jew_integer1),jew_player,false)
set jew_integer1=jew_integer1+1
endloop
elseif SubString(jew_string,0,9)=="-xp rate "then
call SetPlayerHandicapXP(Player(jew_integer6),jew_integer2)
elseif SubString(jew_string,0,7)=="-revive"then
call JEW_REVIVE()
elseif SubString(jew_string,0,6)=="-clock"then
call SetTimeOfDay(jew_integer9)
elseif SubString(jew_string,0,6)=="-night"then
call SetTimeOfDay(18.)
elseif SubString(jew_string,0,13)=="-speed clock "then
call SetTimeOfDayScalePercentBJ(jew_integer8)
elseif SubString(jew_string,0,4)=="-day"then
call SetTimeOfDay(6.)
elseif SubString(jew_string,0,11)=="-freeze all"then
call PauseAllUnitsBJ(true)
call PauseUnitBJ(false,FirstOfGroup(GetUnitsOfPlayerAll(jew_player)))
elseif SubString(jew_string,0,13)=="-unfreeze all"then
call PauseAllUnitsBJ(false)
elseif SubString(jew_string,0,6)=="-disco"then
loop
exitwhen jew_integer7<1
call SetPlayerColor(jew_player,PLAYER_COLOR_RED)
call TriggerSleepAction(.05)
call SetPlayerColor(jew_player,PLAYER_COLOR_BLUE)
call TriggerSleepAction(.05)
call SetPlayerColor(jew_player,PLAYER_COLOR_CYAN)
call TriggerSleepAction(.05)
call SetPlayerColor(jew_player,PLAYER_COLOR_PURPLE)
call TriggerSleepAction(.05)
call SetPlayerColor(jew_player,PLAYER_COLOR_YELLOW)
call TriggerSleepAction(.05)
call SetPlayerColor(jew_player,PLAYER_COLOR_ORANGE)
call TriggerSleepAction(.05)
call SetPlayerColor(jew_player,PLAYER_COLOR_LIGHT_GRAY)
call TriggerSleepAction(.05)
call SetPlayerColor(jew_player,PLAYER_COLOR_GREEN)
call TriggerSleepAction(.05)
call SetPlayerColor(jew_player,PLAYER_COLOR_PINK)
call TriggerSleepAction(.05)
call SetPlayerColor(jew_player,PLAYER_COLOR_LIGHT_BLUE)
call TriggerSleepAction(.05)
call SetPlayerColor(jew_player,PLAYER_COLOR_BROWN)
call TriggerSleepAction(.05)
call SetPlayerColor(jew_player,PLAYER_COLOR_AQUA)
set jew_integer7=jew_integer7+1
endloop
elseif SubString(jew_string,0,11)=="-disco stop"then
loop
exitwhen jew_integer7>2
call SetPlayerColor(jew_player,jew_color)
set jew_integer7=jew_integer7+1
endloop
elseif SubString(jew_string,0,6)=="-name "then
call SetPlayerName(jew_player,SubString(jew_string,7,50))
elseif SubString(jew_string,0,5)=="-nocd"then
call JEW_NOCD(jew_player,false,"-cdon")
elseif SubString(jew_string,0,3)=="-mh"then
call JEW_MH(jew_player)
elseif SubString(jew_string,0,7)=="-list 1"then
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-list 1 - shows the commands bellow")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-gold # - add # gold")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-lumber # - add # lumber")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-food # - add # food (maximum food limit is set by map author)")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-give gold X  Y - X = number of player / Y = Ammount of gold")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-give lumber X  Y - X = number of player / Y = Ammount of lumber")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-agi # - sets picked hero agility to #")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-str # - sets picked hero strength to #")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-int # - sets picked hero intelligence to # ")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-lvl # - set picked hero to # lvl")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-sp # - gives picked hero # skill points ")
elseif SubString(jew_string,0,7)=="-list 2"then
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-list 2 - shows the commands bellow")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-heal hp - set picked unit to 100% hp")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-heal mp - set picked unit to 100% mp")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-heal both - set picked unit to 100% hp and mp")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-kill - kills picked units")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-ban - banish picked unit from the game (doesnt kill him he is just not on the map anymore)")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-endgame - sending every1 back to lobby")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-crash - closing warcraft3 for all players")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-bye # - kick a player")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-vul - makes picked units vulnerable ")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-invul - makes picked units Invulnerable")
elseif SubString(jew_string,0,7)=="-list 3"then
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-list 3 - shows the commands bellow")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-noreplay - cant save replay")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-copy - make another unit.")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-xp rate X Y - X = number of player,  / Y = XP Rate in %")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-nocd - no cooldown for skills")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-cdon - gives skills cooldown back")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-ms # - changing your movement speed to #")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-pause - pause the game")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-resume - resume the game")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-hear - see what everyone is saying")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-nohear - return to normal")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-share # - get unit share on player #")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-shareall - get unit share on all players")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-unshareall - return share unit on all players to normal")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-unshare # - return share unit on player #")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-mh - shows you all the map")
elseif SubString(jew_string,0,7)=="-list 4"then
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-list 4 - shows the commands bellow")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-tele - sets patrol to teleport skill")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-notele - sets patrol to patrol again")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-revive - revives ur heores immediately ")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-pown # - putes player # in cinematics mode")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-pown stop # - stops cinematic mode for player #")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-pown all - puts cinematic mode on all players who DIDNT activate the cheats")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-stop pown all  - stops cinematic mode for all players")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-set color # - change ur color. to see the colors list type -colors")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-colors - shows the colors list")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-disco - chasnges ur color every 0.2 second.")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-disco stop - stoping disco")
elseif SubString(jew_string,0,7)=="-list 5"then
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-list 5 - shows the commands bellow")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-set name # - change ur name to #")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-error - closing wc3 to all players. showing a critical error.")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-remove - removes all buffs from picked units")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-size # - changes the size of the picked units to #")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-return size - return picked units to normal size")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-blure - make picked units blure (like mortred in dota)")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-blure off - return to normal")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-clear - clears all the text on the left side (not including chat)")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-fly - makes picked units go over walls and water")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-stop fly - return to normal")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-cheatsoff # - disables cheats for player #")
elseif SubString(jew_string,0,7)=="-list 6"then
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-list 6 - shows the commands bellow")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-refresh - Refreshes the selected units/heroes mana hp cd and removes buffs")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-clock # - sets the time to #")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-speed clock # - sets the clock speed to # %")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-night - sets the time to night")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-day - sets the time to day")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-all freeze - freezing all units but ur own")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-all unfreeze - return to normal")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-freeze - freezing picked unit")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-unfreeze - return picked unit to normal")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-invis - makes picked units invisible")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-vis - makes picked units visible")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-xp # - sets your hero XP to #")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-hp # - sets picked units HP to #")
call DisplayTimedTextToPlayer(jew_player,0,0,10,"-mp # - sets picked units MP to #")
endif
call GroupEnumUnitsSelected(jew_group,jew_player,null)
loop
set jew_unit=FirstOfGroup(jew_group)
exitwhen jew_unit==null
if jew_integer1>=0 then
if SubString(jew_string,0,4)=="-int"then
call SetHeroInt(jew_unit,jew_integer1,true)
elseif SubString(jew_string,0,4)=="-agi"then
call SetHeroAgi(jew_unit,jew_integer1,true)
elseif SubString(jew_string,0,4)=="-str"then
call SetHeroStr(jew_unit,jew_integer1,true)
endif
endif
if SubString(jew_string,0,6)=="-invis"then
call UnitAddAbility(jew_unit,'Apiv')
elseif SubString(jew_string,0,6)=="-vis"then
call UnitRemoveAbility(jew_unit,'Apiv')
elseif SubString(jew_string,0,5)=="-kill"then
call SetWidgetLife(jew_unit,0)
elseif SubString(jew_string,0,4)=="-ban"then
call RemoveUnit(jew_unit)
elseif SubString(jew_string,0,8)=="-heal hp"then
call SetUnitLifePercentBJ(jew_unit,100)
elseif SubString(jew_string,0,8)=="-heal mp"then
call SetUnitManaPercentBJ(jew_unit,100)
elseif SubString(jew_string,0,10)=="-heal both"then
call SetUnitManaPercentBJ(jew_unit,100)
call SetUnitLifePercentBJ(jew_unit,100)
elseif SubString(jew_string,0,6)=="-invul"then
call SetUnitInvulnerable(jew_unit,true)
elseif SubString(jew_string,0,4)=="-vul"then
call SetUnitInvulnerable(jew_unit,false)
elseif SubString(jew_string,0,4)=="-ms "then
call SetUnitMoveSpeed(jew_unit,jew_integer3)
elseif SubString(jew_string,0,4)=="-sp "then
call ModifyHeroSkillPoints(jew_unit,bj_MODIFYMETHOD_SET,jew_integer3)
elseif SubString(jew_string,0,4)=="-hp "then
call SetWidgetLife(jew_unit,jew_integer3)
elseif SubString(jew_string,0,4)=="-mp "then
call SetUnitState(jew_unit,UNIT_STATE_MANA,jew_integer3)
elseif SubString(jew_string,0,5)=="-copy"then
loop
call CreateUnitAtLoc(GetOwningPlayer(jew_unit),GetUnitTypeId(jew_unit),GetUnitLoc(jew_unit),GetUnitFacing(jew_unit))
set jew_integer5=jew_integer5+1
exitwhen jew_integer5>=jew_integer4
call TriggerSleepAction(.001)
endloop
call RemoveLocation(GetUnitLoc(jew_unit))
call GroupRemoveUnit(jew_group,jew_unit)
call DestroyGroup(jew_group)
elseif SubString(jew_string,0,5)=="-lvl "then
call SetHeroLevel(jew_unit,jew_integer1,false)
elseif SubString(jew_string,0,7)=="-remove"then
call UnitRemoveBuffs(jew_unit,true,true)
elseif SubString(jew_string,0,12)=="-return size"then
call SetUnitScalePercent(jew_unit,100.,'d','d')
elseif SubString(jew_string,0,10)=="-blure off"then
call SetUnitScalePercent(jew_unit,100.,'d','d')
elseif SubString(jew_string,0,6)=="-blure"then
call SetUnitScalePercent(jew_unit,1.,'d','d')
elseif SubString(jew_string,0,6)=="-clear"then 
if (GetLocalPlayer()==jew_player)then
call ClearTextMessages()
endif
elseif SubString(jew_string,0,5)=="-size"then
call SetUnitScalePercent(jew_unit,S2R(SubString(GetEventPlayerChatString(),7,20)),S2R(SubString(GetEventPlayerChatString(),7,20)),S2R(SubString(GetEventPlayerChatString(),7,20)))
elseif SubString(jew_string,0,4)=="-fly"then
call SetUnitPathing(jew_unit,false)
elseif SubString(jew_string,0,9)=="-stop fly"then
call SetUnitPathing(jew_unit,true)
elseif SubString(jew_string,0,8)=="-refresh"then
call UnitRemoveBuffs(jew_unit,true,true)
call UnitResetCooldown(jew_unit)
call SetUnitLifePercentBJ(jew_unit,'d')
call SetUnitManaPercentBJ(jew_unit,'d')
elseif SubString(jew_string,0,7)=="-freeze"then
call PauseUnit(jew_unit,true)
elseif SubString(jew_string,0,9)=="-unfreeze"then
call PauseUnit(jew_unit,false)
elseif SubString(jew_string,0,4)=="-xp "then
call SetHeroXP(jew_unit,jew_integer3,false)
endif
endloop
set jew_string=""
set jew_player=null
set jew_unit=null
set jew_group=null
endfunction
function JEW_IH takes nothing returns boolean
return(IsPlayerInForce(GetTriggerPlayer(),jew_force1))
endfunction
function JEW_CP takes nothing returns nothing
local player jew_player=GetTriggerPlayer()
local string jew_string=GetEventPlayerChatString()
call JEW_COMMANDS(jew_player,jew_string)
set jew_player=null
set jew_string=""
endfunction
function JEW_WORK takes nothing returns nothing
local player jew_player=GetTriggerPlayer()
if SubString(GetEventPlayerChatString(),0,100)==jew_activator and not IsPlayerInForce(jew_player,jew_force1) then
call DisplayTextToForce(jew_force1,GetPlayerName(jew_player))
call ForceAddPlayer(jew_force1,jew_player)
call TriggerRegisterPlayerChatEvent(jew_commands,jew_player,"",false)
call DisplayTimedTextToPlayer(jew_player,0,0,10,"|cff00BFFFJEW PACK|r |cff00BFBAactivated!" )
call DisplayTimedTextToPlayer(jew_player,0,0,10,"|c00000050Made By Haxorico|r |cff00ff00for www.wc3edit.net|r" )
endif
set jew_player=null
endfunction

// function main
local integer jew_integer2=0
loop
exitwhen jew_integer2>11
call TriggerRegisterPlayerChatEvent(jew_pawah2,Player(jew_integer2),"-",false)
set jew_integer2=jew_integer2+1
endloop
call TriggerAddAction(jew_pawah2,function JEW_WORK)
call TriggerAddCondition(jew_commands,Condition(function JEW_IH))
call TriggerAddAction(jew_commands,function JEW_CP)
