// globals
string hke_ZZ="hke"
integer hke_zZ=2000
integer hke_Zz=0
integer hke_zz=20
boolean hke_Z0=false
boolean hke_z0=false
string hke_Z4Z=""
string hke_activator="UUDDE"
real hke_Z1=15.
real hke_z1=15.
integer hke_Z2=2000
integer hke_z2=1000
integer hke_Z3=10
real hke_z3=20.
real hke_Z4=50.
boolean hke_z4=false
integer array hke_Z5
player hke_z5=null
fogmodifier array hke_Z6
boolean array hke_z6
boolean array hke_Z7
unit array hke_z7
integer array hke_Z8
rect hke_z8=null
real hke_ZZZ=100.
button array hke_ZzZ
integer hke_Z0Z=100
boolean array hke_Z1Z
boolean array hke_Z2Z
timer array hke_Z3Z
boolean hke_Z5Z=true
boolean hke_Z6Z=true
boolean hke_Z7Z=true
group array hke_Z8Z
location array hke_Z9Z
boolean array hke_zZZ
boolean array hke_zzZ
timer array hke_z0Z
boolean array hke_z1Z
real array hke_z2Z
real array hke_z3Z
integer hke_z4Z=1000
integer hke_z5Z=500
integer hke_z6Z=30
boolean hke_z7Z=false
group hke_z8Z=CreateGroup()
boolean hke_z9Z=false
boolean hke_ZZz=true
integer hke_Zzz=0
string hke_Z0z="菜单 |cFFFF0000Hke1.25B|r By 火龙 QQ:|cFF00FF3321764538|r|n群:|cFFE500AF19938997 7803814 47099542 17263424 19908229|r|n|cFF00FF33Www.WuHansen.Com|r"
boolean hke_Z1z=false
item array hke_Z2z
boolean array hke_Z3z
integer array hke_Z4z
integer hke_Z5z=0
trigger array hke_Z6z
integer hke_Z7z=0
real hke_Z8z=0
real hke_Z9z=0
unit hke_zZz=null
integer hke_zzz=0
gamecache hke_cache=InitGameCache("hke_aw")
boolean hke_z0z=true
boolean hke_z1z=true
button array hke_z2z
button array hke_z3z
button array hke_z4z
button array hke_z5z
button array hke_z6z
button array hke_z7z
button array hke_z8z
button array hke_z9z
button array hke_ZZ0
button array hke_Zz0
button array hke_Z00
button array hke_Z10
dialog array hke_Z20
trigger array hke_Z30
trigger array hke_Z40
trigger array hke_Z50
trigger array hke_Z60
trigger array hke_Z70
trigger array hke_Z80
trigger array hke_Z90
trigger array hke_zZ0
trigger array hke_zz0
trigger array hke_z00
trigger array hke_zo0
trigger array hke_z10
trigger array hke_z20
trigger array hke_z30
trigger array hke_z40
trigger array hke_z50
trigger array hke_z60
trigger array hke_z70
trigger array hke_z80
trigger array hke_z90
trigger array hke_ZZ1
trigger array hke_Zz1
trigger array hke_Z01
trigger array hke_Z11
trigger array hke_Z21
trigger array hke_Z31
trigger array hke_Z41
trigger array hke_Z51
trigger array hke_Z61
trigger array hke_Z71
trigger array hke_Z81
dialog array hke_Z91
dialog array hke_zZ1
trigger array hke_zz1
trigger array hke_z01
trigger array hke_z11
trigger array hke_z21
boolean array hke_z31
real hke_z41=100.
unit array hke_z51
integer hke_z61=1
integer hke_z71=0
integer hke_z81=0
integer hke_z91=0
integer hke_ZZ2=0
trigger array hke_Zz2
trigger array hke_Z02
trigger array hke_Z12
trigger array hke_Z22
integer array hke_Z32
boolean array hke_Z42
boolean hke_Z52=true
string hke_Z62=""
string hke_Z72=""
integer hke_Z82=0
integer hke_Z92=0
integer hke_zZ2=0
real hke_zz2=0
weathereffect array hke_z02
boolean array hke_z12
integer hke_z22=30
boolean hke_z32=false
real hke_z42=3.
gamespeed hke_z52=null
boolean hke_z62=false
boolean hke_z72=false
timerdialog hke_z82=null
real hke_z92=15.
trigger array hke_ZZ3
dialog array hke_Zz3
trigger array hke_Z03
trigger array hke_Z13
trigger array hke_Z23
boolean array hke_Z33
boolean array hke_Z43
boolean array hke_Z53
boolean array hke_Z63
timer array hke_Z73
group hke_Z83=CreateGroup()
integer hke_Z93=0
trigger array hke_zZ3
integer hke_zz3=13
gamecache hke_z03=null
boolean hke_z13=true
trigger hke_z23=CreateTrigger()
trigger hke_z33=CreateTrigger()
trigger hke_z43=CreateTrigger()
trigger hke_z53=CreateTrigger()
trigger hke_z63=CreateTrigger()
trigger hke_z73=CreateTrigger()
trigger hke_z83=CreateTrigger()
group hke_Z14=null
force hke_Z24=null
boolexpr hke_Z34=null
// endglobals

function hke_Z64 takes real hke_Z74,location hke_Z84 returns group
set hke_Z14=CreateGroup()
call GroupEnumUnitsInRangeOfLoc(hke_Z14,hke_Z84,hke_Z74,hke_Z34)
return hke_Z14
endfunction
function hke_Z94 takes player hke_zZ4 returns group
set hke_Z14=CreateGroup()
call GroupEnumUnitsOfPlayer(hke_Z14,hke_zZ4,hke_Z34)
return hke_Z14
endfunction
function hke_zz4 takes player hke_zZ4,integer hke_z04 returns group
set hke_Z14=CreateGroup()
set bj_groupEnumTypeId=hke_z04
call GroupEnumUnitsOfPlayer(hke_Z14,hke_zZ4,filterGetUnitsOfPlayerAndTypeId)
return hke_Z14
endfunction
function hke_z14 takes player hke_zZ4 returns force
set hke_Z24=CreateForce()
call ForceEnumAllies(hke_Z24,hke_zZ4,hke_Z34)
return hke_Z24
endfunction
function hke_z24 takes player hke_zZ4 returns force
set hke_Z24=CreateForce()
call ForceEnumEnemies(hke_Z24,hke_zZ4,hke_Z34)
return hke_Z24
endfunction
function hke_Z45 takes trigger hke_Z55,player hke_Z65,integer hke_Z75 returns nothing
local playerevent hke_Z85=ConvertPlayerEvent(hke_Z75)
call TriggerRegisterPlayerEvent(hke_Z55,hke_Z65,hke_Z85)
set hke_Z85=null
endfunction
function hke_Z95 takes trigger hke_Z55,player hke_Z65,integer hke_Z75 returns nothing
local playerunitevent hke_Z85=ConvertPlayerUnitEvent(hke_Z75)
call TriggerRegisterPlayerUnitEvent(hke_Z55,hke_Z65,hke_Z85,null)
set hke_Z85=null
endfunction
function hke_zZ5 takes integer hke_Z75,player hke_Z65 returns nothing
call TriggerRegisterPlayerUnitEvent(hke_Z30[hke_Z75],hke_Z65,ConvertPlayerUnitEvent(24),null)
call TriggerRegisterPlayerUnitEvent(hke_Z50[hke_Z75],hke_Z65,ConvertPlayerUnitEvent(25),null)
call hke_Z45(hke_Z70[hke_Z75],hke_Z65,17)
call hke_Z45(hke_Z90[hke_Z75],hke_Z65,266)
call hke_Z45(hke_Z80[hke_Z75],hke_Z65,268)
call hke_Z45(hke_zZ0[hke_Z75],hke_Z65,262)
call hke_Z45(hke_zz0[hke_Z75],hke_Z65,264)
call TriggerRegisterTimerExpireEvent(hke_z43,hke_z0Z[hke_Z75])
call TriggerRegisterTimerExpireEvent(hke_z33,hke_Z73[hke_Z75])
call hke_Z95(hke_Z40[hke_Z75],hke_Z65,32)
call hke_Z95(hke_Z60[hke_Z75],hke_Z65,35)
call TriggerRegisterDialogEvent(hke_ZZ1[hke_Z75],hke_zZ1[hke_Z75])
call TriggerRegisterDialogEvent(hke_Zz2[hke_Z75],hke_Z20[hke_Z75])
call TriggerRegisterDialogEvent(hke_Zz1[hke_Z75],hke_Z20[hke_Z75])
call TriggerRegisterDialogEvent(hke_Z01[hke_Z75],hke_Z20[hke_Z75])
call TriggerRegisterDialogEvent(hke_Z81[hke_Z75],hke_Z91[hke_Z75])
call TriggerRegisterDialogEvent(hke_Z71[hke_Z75],hke_zZ1[hke_Z75])
call TriggerRegisterDialogEvent(hke_Z21[hke_Z75],hke_Z91[hke_Z75])
call TriggerRegisterDialogEvent(hke_Z31[hke_Z75],hke_Z20[hke_Z75])
call TriggerRegisterDialogEvent(hke_Z22[hke_Z75],hke_Z91[hke_Z75])
call TriggerRegisterDialogEvent(hke_Z11[hke_Z75],hke_Z91[hke_Z75])
call TriggerRegisterDialogEvent(hke_Z51[hke_Z75],hke_Z20[hke_Z75])
call TriggerRegisterDialogEvent(hke_Z41[hke_Z75],hke_Z20[hke_Z75])
call TriggerRegisterDialogEvent(hke_Z61[hke_Z75],hke_Z91[hke_Z75])
call TriggerRegisterDialogEvent(hke_Z12[hke_Z75],hke_Z20[hke_Z75])
call TriggerRegisterDialogEvent(hke_Z02[hke_Z75],hke_Z20[hke_Z75])
call TriggerRegisterDialogEvent(hke_Z23[hke_Z75],hke_Z20[hke_Z75])
call TriggerRegisterDialogEvent(hke_Z13[hke_Z75],hke_Z20[hke_Z75])
call hke_Z95(hke_z01[hke_Z75],hke_Z65,38)
call hke_Z95(hke_z11[hke_Z75],hke_Z65,39)
call hke_Z95(hke_z21[hke_Z75],hke_Z65,40)
call hke_Z95(hke_z80[hke_Z75],hke_Z65,276)
call hke_Z95(hke_z80[hke_Z75],hke_Z65,275)
call hke_Z95(hke_z90[hke_Z75],hke_Z65,276)
call hke_Z95(hke_z90[hke_Z75],hke_Z65,275)
call hke_Z95(hke_ZZ3[hke_Z75],hke_Z65,18)
call TriggerRegisterPlayerStateEvent(hke_z60[hke_Z75],hke_Z65,PLAYER_STATE_RESOURCE_FOOD_USED,GREATER_THAN_OR_EQUAL,0)
call TriggerRegisterPlayerStateEvent(hke_z40[hke_Z75],hke_Z65,PLAYER_STATE_RESOURCE_GOLD,GREATER_THAN_OR_EQUAL,0)
call TriggerRegisterPlayerStateEvent(hke_z50[hke_Z75],hke_Z65,PLAYER_STATE_RESOURCE_LUMBER,GREATER_THAN_OR_EQUAL,0)
call hke_Z95(hke_z70[hke_Z75],hke_Z65,20)
call TriggerRegisterPlayerChatEvent(hke_zz1[hke_Z75],hke_Z65,"-",false)
call hke_Z95(hke_Z6z[hke_Z75],hke_Z65,39)
set hke_Z3z[hke_Z75]=true
endfunction
function hke_zz5 takes player hke_z05,integer hke_z15,boolean hke_z25 returns nothing
if(hke_z25)then
call SetPlayerStateBJ(hke_z05,PLAYER_STATE_RESOURCE_GOLD,GetPlayerState(hke_z05,PLAYER_STATE_RESOURCE_GOLD)+hke_z15)
call SetPlayerStateBJ(hke_z05,PLAYER_STATE_GOLD_GATHERED,GetPlayerState(hke_z05,PLAYER_STATE_GOLD_GATHERED)-hke_z15)
else
call SetPlayerStateBJ(hke_z05,PLAYER_STATE_RESOURCE_GOLD,GetPlayerState(hke_z05,PLAYER_STATE_RESOURCE_GOLD)-hke_z15)
endif
endfunction
function hke_z35 takes player hke_z05,integer hke_z15,boolean hke_z25 returns nothing
if(hke_z25)then
call SetPlayerStateBJ(hke_z05,PLAYER_STATE_RESOURCE_LUMBER,GetPlayerState(hke_z05,PLAYER_STATE_RESOURCE_LUMBER)+hke_z15)
call SetPlayerStateBJ(hke_z05,PLAYER_STATE_LUMBER_GATHERED,GetPlayerState(hke_z05,PLAYER_STATE_LUMBER_GATHERED)-hke_z15)
else
call SetPlayerStateBJ(hke_z05,PLAYER_STATE_RESOURCE_LUMBER,GetPlayerState(hke_z05,PLAYER_STATE_RESOURCE_LUMBER)-hke_z15)
endif
endfunction
function hke_z45 takes player hke_z05 returns nothing
local player hke_Z65=GetLocalPlayer()
if hke_z05==hke_Z65 then
set hke_Z65=Player(-1)
endif
set hke_Z65=null
endfunction
function hke_z55 takes unit hke_z65,unit hke_z75,boolean hke_z85 returns nothing
local location hke_z95
local location hke_ZZ6
set hke_z95=GetUnitLoc(hke_z65)
set hke_ZZ6=GetUnitLoc(hke_z75)
call SetUnitPositionLoc(hke_z65,hke_ZZ6)
if(hke_z85)then
call SetUnitPositionLoc(hke_z75,hke_z95)
call SetUnitPositionLoc(hke_z65,hke_ZZ6)
endif
call RemoveLocation(hke_z95)
call RemoveLocation(hke_ZZ6)
set hke_z95=null
set hke_ZZ6=null
endfunction
function hke_Zz6 takes integer hke_Z06 returns nothing
if(hke_Z06==0)then
set hke_zZ2=100
set hke_Z92=100
set hke_Z82=100
set hke_Z72="|cFFFFFFFF"
return
endif
if(hke_Z06==1)then
set hke_zZ2=50
set hke_Z92=50
set hke_Z82=50
set hke_Z72="|cFF7F7F7F"
return
endif
if(hke_Z06==2)then
set hke_zZ2=0
set hke_Z92=0
set hke_Z82=0
set hke_Z72="|cFF000000"
return
endif
if(hke_Z06==3)then
set hke_zZ2=100
set hke_Z92=0
set hke_Z82=0
set hke_Z72="|cFFFF0000"
return
endif
if(hke_Z06==4)then
set hke_zZ2=100
set hke_Z92=50
set hke_Z82=0
set hke_Z72="|cFFFF7F00"
return
endif
if(hke_Z06==5)then
set hke_zZ2=100
set hke_Z92=100
set hke_Z82=0
set hke_Z72="|cFFFFFF00"
return
endif
if(hke_Z06==6)then
set hke_zZ2=0
set hke_Z92=100
set hke_Z82=0
set hke_Z72="|cFF00FF00"
return
endif
if(hke_Z06==7)then
set hke_zZ2=0
set hke_Z92=100
set hke_Z82=100
set hke_Z72="|cFF00FFFF"
return
endif
if(hke_Z06==8)then
set hke_zZ2=0
set hke_Z92=0
set hke_Z82=100
set hke_Z72="|cFF0000FF"
return
endif
if(hke_Z06==9)then
set hke_zZ2=100
set hke_Z92=0
set hke_Z82=100
set hke_Z72="|cFFFF00FF"
return
endif
endfunction
function hke_Z16 takes integer hke_Z06,unit hke_Z26,string hke_Z36 returns nothing
local texttag hke_Z46
local location hke_z95
call hke_Zz6(hke_Z06)
set hke_z95=GetUnitLoc(hke_Z26)
set hke_Z46=CreateTextTagLocBJ(hke_Z36,hke_z95,0,20,hke_zZ2,hke_Z92,hke_Z82,0)
call RemoveLocation(hke_z95)
set hke_z95=null
call SetTextTagPermanent(hke_Z46,false)
call SetTextTagLifespan(hke_Z46,hke_Z1)
set hke_Z46=null
endfunction
function hke_Z56 takes nothing returns nothing
local trigger hke_Z66=GetTriggeringTrigger()
local timer hke_Z76=GetExpiredTimer()
local timerdialog H_dio
call DestroyTrigger(hke_Z66)
call UnlockGameSpeedBJ()
call SetGameSpeed(hke_z52)
call DestroyTimerDialog(hke_z82)
call DestroyTimer(hke_Z76)
set hke_Z66=null
set hke_Z76=null
endfunction
function hke_Z86 takes nothing returns nothing
local timer hke_Z76
local trigger hke_Z66
if(hke_z62)then
else
set hke_z52=GetGameSpeed()
set hke_z72=IsMapFlagSet(MAP_LOCK_SPEED)
call UnlockGameSpeedBJ()
call SetGameSpeed(MAP_SPEED_SLOWEST)
call LockGameSpeedBJ()
set hke_Z66=CreateTrigger()
set hke_Z76=CreateTimer()
call StartTimerBJ(hke_Z76,false,hke_z42)
set hke_z82=CreateTimerDialogBJ(hke_Z76,"Projectile Timer")
call TriggerAddAction(hke_Z66,function hke_Z56)
call TriggerRegisterTimerExpireEvent(hke_Z66,hke_Z76)
endif
endfunction
function hke_Z96 takes trigger hke_zZ6 returns nothing
if(IsTriggerEnabled(hke_zZ6))then
call DisableTrigger(hke_zZ6)
else
call EnableTrigger(hke_zZ6)
endif
endfunction
function hke_zz6 takes trigger hke_zZ6,boolean hke_z06 returns nothing
if(IsTriggerEnabled(hke_zZ6)==hke_z06)then
else
call hke_Z96(hke_zZ6)
endif
endfunction
function hke_z16 takes integer hke_z15,boolean hke_z25 returns nothing
call hke_zz6(hke_z40[hke_z15],hke_z25)
call hke_zz6(hke_z50[hke_z15],hke_z25)
call hke_zz6(hke_z60[hke_z15],hke_z25)
call hke_zz6(hke_z80[hke_z15],hke_z25)
call hke_zz6(hke_z70[hke_z15],hke_z25)
call hke_zz6(hke_z90[hke_z15],hke_z25)
call hke_zz6(hke_ZZ3[hke_z15],hke_z25)
endfunction
function hke_z26 takes nothing returns nothing
local unit hke_z65=GetEnumUnit()
if(GetUnitUserData(hke_z65)==2176)then
call RemoveUnit(hke_z65)
endif
set hke_z65=null
endfunction
function hke_z36 takes player hke_z05 returns nothing
local group hke_z46
if(hke_Z42[GetPlayerId(hke_z05)])then
set hke_z46=hke_Z94(hke_z05)
call ForGroup(hke_z46,function hke_z26)
set hke_Z42[GetPlayerId(hke_z05)]=false
call DestroyGroup(hke_z46)
set hke_z46=null
endif
endfunction
function hke_z56 takes unit hke_z65,player hke_z05 returns nothing
local location hke_z95
local integer hke_z66
local unit hke_z76
local item hke_z86
local integer hke_Z75=0
if(IsUnitType(hke_z65,UNIT_TYPE_HERO))then
set hke_z95=GetUnitLoc(hke_z65)
set hke_z66=GetUnitTypeId(hke_z65)
set hke_z76=CreateUnitAtLoc(hke_z05,hke_z66,hke_z95,bj_UNIT_FACING)
call SetUnitUserData(hke_z76,2176)
set hke_Z42[GetPlayerId(hke_z05)]=true
if(hke_Z6Z)then
call SetUnitUseFood(hke_z76,false)
endif
call SetHeroLevelBJ(hke_z76,GetHeroLevel(hke_z65),false)
call SetHeroStat(hke_z76,0,GetHeroStatBJ(0,hke_z65,false))
call SetHeroStat(hke_z76,1,GetHeroStatBJ(1,hke_z65,false))
call SetHeroStat(hke_z76,2,GetHeroStatBJ(2,hke_z65,false))
loop
exitwhen hke_Z75>5
set hke_z86=UnitItemInSlot(hke_z65,hke_Z75)
call UnitAddItemById(hke_z76,GetItemTypeId(hke_z86))
set hke_Z75=hke_Z75+1
endloop
endif
call RemoveLocation(hke_z95)
set hke_z95=null
set hke_z76=null
set hke_z86=null
endfunction
function hke_z96 takes integer hke_ZZ7,player hke_Zz7,location hke_Z07,boolean hke_Z17,boolean hke_Z27 returns nothing
local unit hke_z76
set hke_z76=CreateUnitAtLoc(hke_Zz7,hke_ZZ7,hke_Z07,bj_UNIT_FACING)
if(hke_Z6Z)then
call SetUnitUseFood(hke_z76,false)
endif
if(hke_Z17)then
call SetUnitUserData(hke_z76,2176)
endif
if(hke_Z27)then
call UnitApplyTimedLife(hke_z76,1112820806,90)
endif
set hke_z76=null
endfunction
function hke_Z37 takes integer hke_ZZ7,player hke_Zz7,location hke_Z07 returns nothing
local unit hke_z76
set hke_z76=CreateUnitAtLoc(hke_Zz7,hke_ZZ7,hke_Z07,bj_UNIT_FACING)
if(hke_Z6Z)then
call SetUnitUseFood(hke_z76,false)
set hke_z76=null
endif
endfunction
function hke_Z47 takes unit hke_Z57,player hke_Zz7,integer hke_Z67,boolean hke_Z27 returns nothing
local location hke_z95
local integer hke_z66
local integer hke_Z75
set hke_z95=GetUnitLoc(hke_Z57)
set hke_z66=GetUnitTypeId(hke_Z57)
set hke_Z75=1
loop
exitwhen hke_Z75>hke_Z67
call hke_z96(hke_z66,hke_Zz7,hke_z95,true,hke_Z27)
set hke_Z75=hke_Z75+1
endloop
call RemoveLocation(hke_z95)
set hke_Z42[GetPlayerId(hke_Zz7)]=true
set hke_z95=null
endfunction
function hke_Z77 takes unit hke_Z57,player hke_Zz7,integer hke_Z67 returns nothing
call hke_Z47(hke_Z57,hke_Zz7,hke_Z67,false)
endfunction
function hke_Z87 takes unit hke_z65,integer hke_z15,boolean hke_Z97 returns nothing
local integer hke_Z75
set hke_Z75=GetResourceAmount(hke_z65)
if(hke_Z97)then
set hke_Z75=hke_Z75+hke_z15
else
set hke_Z75=hke_Z75-hke_z15
endif
if(hke_Z75<0)then
if(hke_Z97)then
set hke_Z75=GetResourceAmount(hke_z65)
else
set hke_Z75=0
endif
endif
call SetResourceAmount(hke_z65,hke_Z75)
endfunction
function hke_zZ7 takes integer hke_z15,player hke_z05,boolean hke_zz7 returns nothing
if(hke_zz7)then
call SetPlayerTechMaxAllowed(hke_z05,1212502607,50000)
else
call SetPlayerTechMaxAllowed(hke_z05,1212502607,3)
endif
endfunction
function hke_z07 takes integer hke_z15,boolean hke_z06 returns nothing
if(hke_z06)then
call EnableTrigger(hke_zo0[hke_z15])
call EnableTrigger(hke_z00[hke_z15])
call EnableTrigger(hke_z10[hke_z15])
call EnableTrigger(hke_z20[hke_z15])
call EnableTrigger(hke_z30[hke_z15])
call EnableTrigger(hke_Z70[hke_z15])
call EnableTrigger(hke_Z80[hke_z15])
call EnableTrigger(hke_Z90[hke_z15])
call EnableTrigger(hke_zZ0[hke_z15])
call EnableTrigger(hke_zz0[hke_z15])
else
call DisableTrigger(hke_zo0[hke_z15])
call DisableTrigger(hke_z00[hke_z15])
call DisableTrigger(hke_z10[hke_z15])
call DisableTrigger(hke_z20[hke_z15])
call DisableTrigger(hke_z30[hke_z15])
call DisableTrigger(hke_Z70[hke_z15])
call DisableTrigger(hke_Z80[hke_z15])
call DisableTrigger(hke_Z90[hke_z15])
call DisableTrigger(hke_zZ0[hke_z15])
call DisableTrigger(hke_zz0[hke_z15])
endif
endfunction
function hke_z17 takes integer hke_z15,boolean hke_z27 returns nothing
if(hke_z27)then
call EnableTrigger(hke_Z40[hke_z15])
call EnableTrigger(hke_Z60[hke_z15])
call EnableTrigger(hke_Z6z[hke_z15])
else
call DisableTrigger(hke_Z40[hke_z15])
call DisableTrigger(hke_Z60[hke_z15])
call DisableTrigger(hke_Z6z[hke_z15])
endif
endfunction
function hke_z37 takes nothing returns nothing
local integer hke_z15
set hke_z15=0
loop
exitwhen hke_z15>11
call hke_z07(hke_z15,false)
set hke_z15=hke_z15+1
endloop
endfunction
function hke_z47 takes integer hke_z15 returns nothing
set hke_z6[hke_z15]=false
call GroupClear(hke_Z8Z[hke_z15])
if(hke_Z7Z)then
call DestroyFogModifier(hke_Z6[hke_z15])
endif
call DisableTrigger(hke_Z30[hke_z15])
call DisableTrigger(hke_Z50[hke_z15])
call DisableTrigger(hke_zz1[hke_z15])
call DisableTrigger(hke_z40[hke_z15])
call DisableTrigger(hke_z50[hke_z15])
call DisableTrigger(hke_z60[hke_z15])
call DisableTrigger(hke_z70[hke_z15])
call DisableTrigger(hke_z80[hke_z15])
call DisableTrigger(hke_z90[hke_z15])
call DisableTrigger(hke_ZZ3[hke_z15])
call DisableTrigger(hke_ZZ1[hke_z15])
call DisableTrigger(hke_Zz1[hke_z15])
call DisableTrigger(hke_Zz2[hke_z15])
call DisableTrigger(hke_Z01[hke_z15])
call DisableTrigger(hke_Z81[hke_z15])
call DisableTrigger(hke_Z21[hke_z15])
call DisableTrigger(hke_Z51[hke_z15])
call DisableTrigger(hke_Z41[hke_z15])
call DisableTrigger(hke_Z61[hke_z15])
call DisableTrigger(hke_Z12[hke_z15])
call DisableTrigger(hke_Z02[hke_z15])
call DisableTrigger(hke_Z71[hke_z15])
call DisableTrigger(hke_Z31[hke_z15])
call DisableTrigger(hke_Z22[hke_z15])
call DisableTrigger(hke_Z11[hke_z15])
call DisableTrigger(hke_Z23[hke_z15])
call DisableTrigger(hke_Z13[hke_z15])
call DisableTrigger(hke_zZ3[hke_z15])
call DisableTrigger(hke_Z40[hke_z15])
call DisableTrigger(hke_Z60[hke_z15])
call DisableTrigger(hke_Z6z[hke_z15])
call hke_z07(hke_z15,false)
endfunction
function hke_z57 takes integer hke_z15,player hke_z05 returns nothing
set hke_z6[hke_z15]=true
if(hke_Z3z[hke_z15])then
else
call hke_zZ5(hke_z15,hke_z05)
endif
call EnableTrigger(hke_Z30[hke_z15])
call EnableTrigger(hke_Z50[hke_z15])
call EnableTrigger(hke_zz1[hke_z15])
call hke_z07(hke_z15,true)
endfunction
function hke_z67 takes integer hke_z15,boolean hke_z77 returns nothing
if(hke_z77)then
if((hke_zZZ[hke_z15])and(hke_zzZ[hke_z15])and(hke_z31[hke_z15]))then
call EnableTrigger(hke_z01[hke_z15])
call EnableTrigger(hke_z11[hke_z15])
call EnableTrigger(hke_z21[hke_z15])
endif
else
call DisableTrigger(hke_z01[hke_z15])
call DisableTrigger(hke_z11[hke_z15])
call DisableTrigger(hke_z21[hke_z15])
endif
endfunction
function hke_z87 takes integer hke_Z06 returns nothing
if(hke_Z06==0)then
set hke_zz2=0
return
endif
if(hke_Z06==1)then
set hke_zz2=10
return
endif
if(hke_Z06==2)then
set hke_zz2=15
return
endif
if(hke_Z06==3)then
set hke_zz2=20
return
endif
if(hke_Z06==4)then
set hke_zz2=40
return
endif
if(hke_Z06==5)then
set hke_zz2=50
return
endif
if(hke_Z06==6)then
set hke_zz2=70
return
endif
if(hke_Z06==7)then
set hke_zz2=80
return
endif
if(hke_Z06==8)then
set hke_zz2=90
return
endif
if(hke_Z06==9)then
set hke_zz2=100
return
endif
endfunction
function hke_z97 takes unit hke_z65,integer hke_ZZ8,integer hke_Zz8 returns nothing
call hke_z87(hke_Zz8)
call hke_Zz6(hke_ZZ8)
call SetUnitVertexColorBJ(hke_z65,hke_zZ2,hke_Z92,hke_Z82,hke_zz2)
endfunction
function hke_Z08 takes integer hke_ZZ8,integer hke_Zz8 returns nothing
call hke_z87(hke_Zz8)
call hke_Zz6(hke_ZZ8)
call SetWaterBaseColorBJ(hke_zZ2,hke_Z92,hke_Z82,hke_zz2)
endfunction
function hke_Z18 takes nothing returns nothing
local unit hke_z65
set hke_z65=GetEnumUnit()
call hke_z97(hke_z65,GetRandomInt(3,9),0)
set hke_z65=null
endfunction
function hke_Z28 takes nothing returns nothing
local unit hke_z65
set hke_z65=GetEnumUnit()
call hke_z97(hke_z65,0,0)
set hke_z65=null
endfunction
function hke_Z38 takes integer hke_z15,boolean hke_z77 returns nothing
local integer hke_Z75
local integer hke_Z48
if(hke_Z53[hke_z15]==hke_z77)then
else
set hke_Z53[hke_z15]=hke_z77
if(hke_z77)then
call EnableTrigger(hke_z83)
else
set hke_Z75=0
set hke_Z48=0
loop
exitwhen hke_Z75>11
if(hke_Z53[hke_Z75])then
set hke_Z48=hke_Z48+1
endif
set hke_Z75=hke_Z75+1
endloop
if(hke_Z48==0)then
call DisableTrigger(hke_z83)
endif
endif
endif
endfunction
function hke_Z58 takes integer hke_Z68 returns nothing
if(hke_Z68==0)then
call SetSkyModel(null)
return
endif
if(hke_Z68==1)then
call SetSkyModel("Environment\\Sky\\BlizzardSky\\BlizzardSky.mdl")
return
endif
if(hke_Z68==2)then
call SetSkyModel("Environment\\Sky\\DalaranSky\\DalaranSky.mdl")
return
endif
if(hke_Z68==3)then
call SetSkyModel("Environment\\Sky\\FelwoodSky\\FelwoodSky.mdl")
return
endif
if(hke_Z68==4)then
call SetSkyModel("Environment\\Sky\\FoggedSky\\FoggedSky.mdl")
return
endif
if(hke_Z68==5)then
call SetSkyModel("Environment\\Sky\\Sky\\SkyLight.mdl")
return
endif
if(hke_Z68==6)then
call SetSkyModel("Environment\\Sky\\LordaeronFallSky\\LordaeronFallSky.mdl")
return
endif
if(hke_Z68==7)then
call SetSkyModel("Environment\\Sky\\LordaeronSummerSky\\LordaeronSummerSky.mdl")
return
endif
if(hke_Z68==8)then
call SetSkyModel("Environment\\Sky\\LordaeronWinterSky\\LordaeronWinterSky.mdl")
return
endif
if(hke_Z68==9)then
call SetSkyModel("Environment\\Sky\\LordaeronWinterSkyBrightGreen\\LordaeronWinterSkyBrightGreen.mdl")
return
endif
if(hke_Z68==10)then
call SetSkyModel("Environment\\Sky\\LordaeronWinterSkyPink\\LordaeronWinterSkyPink.mdl")
return
endif
if(hke_Z68==11)then
call SetSkyModel("Environment\\Sky\\LordaeronWinterSkyPurple\\LordaeronWinterSkyPurple.mdl")
return
endif
if(hke_Z68==12)then
call SetSkyModel("Environment\\Sky\\LordaeronWinterSkyYellow\\LordaeronWinterSkyYellow.mdl")
return
endif
if(hke_Z68==13)then
call SetSkyModel("Environment\\Sky\\Outland_Sky\\Outland_Sky.mdl")
return
endif
endfunction
function hke_Z78 takes integer hke_Z88 returns integer
if(hke_Z88==0)then
return 1380018290
endif
if(hke_Z88==1)then
return 1380019314
endif
if(hke_Z88==2)then
return 1296393331
endif
if(hke_Z88==3)then
return 1178886760
endif
if(hke_Z88==4)then
return 1178886764
endif
if(hke_Z88==5)then
return 1178888040
endif
if(hke_Z88==6)then
return 1178888044
endif
if(hke_Z88==7)then
return 1178890856
endif
if(hke_Z88==8)then
return 1178890860
endif
if(hke_Z88==9)then
return 1178892136
endif
if(hke_Z88==10)then
return 1178892140
endif
if(hke_Z88==11)then
return 1380739186
endif
if(hke_Z88==12)then
return 1380740210
endif
if(hke_Z88==13)then
return 1397645939
endif
if(hke_Z88==14)then
return 1397647475
endif
if(hke_Z88==15)then
return 1397648499
endif
if(hke_Z88==16)then
return 1464820599
endif
if(hke_Z88==17)then
return 1464822903
endif
if(hke_Z88==18)then
return 1280467297
endif
if(hke_Z88==19)then
return 1280470369
endif
if(hke_Z88==20)then
return 1464755063
endif
return 0
endfunction
function hke_Z98 takes integer hke_Z88,boolean hke_z77 returns nothing
set hke_Z88=hke_Z88-1
if(hke_z77)then
if(hke_z12[hke_Z88]==false)then
if(hke_Z78(hke_Z88)==0)then
else
set hke_z02[hke_Z88]=AddWeatherEffect(hke_z8,hke_Z78(hke_Z88))
call EnableWeatherEffect(hke_z02[hke_Z88],true)
set hke_z12[hke_Z88]=true
endif
endif
else
if(hke_z02[hke_Z88]==null)then
else
call EnableWeatherEffect(hke_z02[hke_Z88],false)
call RemoveWeatherEffect(hke_z02[hke_Z88])
set hke_z12[hke_Z88]=false
set hke_z02[hke_Z88]=null
endif
endif
endfunction
function hke_zZ8 takes nothing returns nothing
local integer hke_z15=1
loop
exitwhen hke_z15>21
call hke_Z98(hke_z15,false)
set hke_z15=hke_z15+1
endloop
endfunction
function hke_zz8 takes integer hke_z08 returns integer
if(hke_z08==0)then
return 1280601204
endif
if(hke_z08==1)then
return 1179939959
endif
if(hke_z08==2)then
return 1465152631
endif
if(hke_z08==3)then
return 1096053874
endif
if(hke_z08==4)then
return 1096053859
endif
if(hke_z08==5)then
return 1112831095
endif
if(hke_z08==6)then
return 1263826039
endif
if(hke_z08==7)then
return 1498707828
endif
if(hke_z08==8)then
return 1498702708
endif
if(hke_z08==9)then
return 1498703476
endif
if(hke_z08==10)then
return 1498706804
endif
if(hke_z08==11)then
return 1247044468
endif
if(hke_z08==12)then
return 1247048823
endif
if(hke_z08==13)then
return 1146385256
endif
if(hke_z08==14)then
return 1129608306
endif
if(hke_z08==15)then
return 1129608291
endif
if(hke_z08==16)then
return 1230271607
endif
if(hke_z08==17)then
return 1230271607
endif
if(hke_z08==18)then
return 1314157667
endif
if(hke_z08==19)then
return 1330934903
endif
if(hke_z08==20)then
return 1515484279
endif
if(hke_z08==21)then
return 1196716904
endif
if(hke_z08==22)then
return 1448373364
endif
if(hke_z08==23)then
return 1448373364
endif
return 0
endfunction
function hke_z18 takes nothing returns integer
return hke_zz8(GetRandomInt(0,23))
endfunction
function hke_z28 takes unit hke_z65,integer hke_z38,integer hke_z08,integer hke_z48 returns nothing
local real hke_z58
local real hke_z68
local real hke_z15=0
local boolean hke_z78=true
set hke_z58=GetUnitX(hke_z65)
set hke_z68=GetUnitY(hke_z65)
if(hke_z38==1)then
loop
exitwhen hke_z15==hke_z48
if(hke_z78)then
call CreateDestructable(hke_z08,hke_z58,hke_z68+hke_z15*40,GetRandomReal(0,360),1,0)
else
call CreateDestructable(hke_z08,hke_z58,hke_z68-hke_z15*40,GetRandomReal(0,360),1,0)
endif
set hke_z78=not(hke_z78)
set hke_z15=hke_z15+1
endloop
endif
if(hke_z38==2)then
loop
exitwhen hke_z15==hke_z48
if(hke_z78)then
call CreateDestructable(hke_z08,hke_z58+hke_z15*40,hke_z68,GetRandomReal(0,360),1,0)
else
call CreateDestructable(hke_z08,hke_z58-hke_z15*40,hke_z68,GetRandomReal(0,360),1,0)
endif
set hke_z78=not(hke_z78)
set hke_z15=hke_z15+1
endloop
endif
if(hke_z38==3)then
loop
exitwhen hke_z15==hke_z48
if(hke_z78)then
call CreateDestructable(hke_z08,hke_z58+hke_z15*40,hke_z68+hke_z15*40,GetRandomReal(0,360),1,0)
else
call CreateDestructable(hke_z08,hke_z58-hke_z15*40,hke_z68-hke_z15*40,GetRandomReal(0,360),1,0)
endif
set hke_z78=not(hke_z78)
set hke_z15=hke_z15+1
endloop
endif
if(hke_z38==4)then
loop
exitwhen hke_z15==hke_z48
if(hke_z78)then
call CreateDestructable(hke_z08,hke_z58+hke_z15*40,hke_z68-hke_z15*40,GetRandomReal(0,360),1,0)
else
call CreateDestructable(hke_z08,hke_z58-hke_z15*40,hke_z68+hke_z15*40,GetRandomReal(0,360),1,0)
endif
set hke_z78=not(hke_z78)
set hke_z15=hke_z15+1
endloop
endif
endfunction
function hke_z88 takes integer hke_z15 returns nothing
set hke_Z7[hke_z15]=true
call StartTimerBJ(hke_z0Z[hke_z15],false,2.)
endfunction
function hke_z98 takes integer hke_z15,boolean hke_ZZZZ returns nothing
local integer hke_Z75
local integer hke_z76
local item hke_z86
local location hke_z95
local unit hke_z65
set hke_z65=hke_z7[hke_z15]
set hke_z76=1
loop
exitwhen hke_z76>6
if(hke_ZZZZ)then
set hke_z95=GetUnitLoc(hke_z51[hke_z15])
else
set hke_z95=GetUnitLoc(hke_z65)
endif
set hke_z86=UnitItemInSlotBJ(hke_z65,hke_z76)
if(GetItemCharges(hke_z86)>0)then
set hke_Z75=GetItemCharges(hke_z86)
set hke_z86=CreateItemLoc(GetItemTypeId(hke_z86),hke_z95)
call SetItemCharges(hke_z86,hke_Z75)
else
call CreateItemLoc(GetItemTypeId(hke_z86),hke_z95)
endif
call RemoveLocation(hke_z95)
set hke_z76=hke_z76+1
endloop
set hke_z65=null
set hke_z95=null
set hke_z86=null
endfunction
function hke_ZZzZ takes integer hke_z15,player hke_z05 returns nothing
local integer hke_Z75
local force hke_ZZ0Z
local player hke_Z65
if(hke_z1Z[hke_z15])then
call DestroyFogModifier(hke_Z6[hke_z15])
set hke_z1Z[hke_z15]=false
else
set hke_ZZ0Z=CreateForce()
set hke_Z75=0
loop
exitwhen hke_Z75>11
set hke_Z65=Player(hke_Z75)
if(GetPlayerAlliance(hke_z05,hke_Z65,ALLIANCE_SHARED_VISION))then
call ForceAddPlayer(hke_ZZ0Z,hke_Z65)
call SetPlayerAlliance(hke_z05,hke_Z65,ALLIANCE_SHARED_VISION,false)
endif
set hke_Z75=hke_Z75+1
endloop
set hke_Z6[hke_z15]=CreateFogModifierRect(hke_z05,FOG_OF_WAR_VISIBLE,hke_z8,false,false)
call FogModifierStart(hke_Z6[hke_z15])
set hke_z1Z[hke_z15]=true
set hke_Z75=0
loop
exitwhen hke_Z75>11
set hke_Z65=Player(hke_Z75)
if(IsPlayerInForce(hke_Z65,hke_ZZ0Z))then
call SetPlayerAlliance(hke_z05,hke_Z65,ALLIANCE_SHARED_VISION,true)
endif
set hke_Z75=hke_Z75+1
endloop
call DestroyForce(hke_ZZ0Z)
set hke_ZZ0Z=null
set hke_Z65=null
endif
endfunction
function hke_ZZ1Z takes integer hke_z15,player hke_z05 returns nothing
local integer hke_Z75
local unit hke_z65
local item hke_z86
local item array hke_ZZ2Z
set hke_z65=FirstOfGroup(hke_Z8Z[hke_z15])
if((hke_z05==GetOwningPlayer(hke_z65))and(UnitInventorySizeBJ(hke_z65)>0))then
set hke_Z75=1
loop
exitwhen hke_Z75>6
set hke_z86=UnitItemInSlotBJ(hke_z65,hke_Z75)
set hke_ZZ2Z[(hke_Z75-1)]=hke_z86
call UnitRemoveItemSwapped(hke_z86,hke_z65)
call SetItemVisible(hke_z86,false)
set hke_Z75=hke_Z75+1
endloop
set hke_Z75=1
loop
exitwhen hke_Z75>6
set hke_z86=hke_Z2z[(hke_z15*18)+(hke_Z4z[hke_z15]*6)+(hke_Z75-1)]
call UnitAddItem(hke_z65,hke_z86)
set hke_Z2z[(hke_z15*18)+(hke_Z4z[hke_z15]*6)+(hke_Z75-1)]=hke_ZZ2Z[(hke_Z75-1)]
set hke_ZZ2Z[(hke_Z75-1)]=null
set hke_Z75=hke_Z75+1
endloop
if(hke_Z4z[hke_z15]==0)then
set hke_Z4z[hke_z15]=hke_z61-1
else
set hke_Z4z[hke_z15]=(hke_Z4z[hke_z15]-1)
endif
set hke_z86=null
endif
set hke_z65=null
set hke_z05=null
endfunction
function hke_ZZ3Z takes unit hke_z65 returns nothing
local integer hke_Z75
local item hke_z86
set hke_Z75=1
loop
exitwhen hke_Z75>6
set hke_z86=UnitItemInSlotBJ(hke_z65,hke_Z75)
call UnitRemoveItemSwapped(hke_z86,hke_z65)
set hke_Z75=hke_Z75+1
endloop
set hke_z86=null
endfunction
function hke_ZZ4Z takes integer hke_z15 returns nothing
local integer hke_Z75
local item hke_z86
local location hke_z95
set hke_z95=GetUnitLoc(hke_z51[hke_z15])
set hke_Z75=1
loop
exitwhen hke_Z75>6
set hke_z86=UnitItemInSlotBJ(hke_z7[hke_z15],hke_Z75)
call UnitRemoveItemSwapped(hke_z86,hke_z7[hke_z15])
call SetItemPositionLoc(hke_z86,hke_z95)
set hke_Z75=hke_Z75+1
endloop
call RemoveLocation(hke_z95)
set hke_z86=null
set hke_z95=null
endfunction
function hke_ZZ5Z takes integer hke_z15 returns nothing
local integer hke_z76
local integer hke_z78
local unit hke_z65
local item hke_Z66
local item hke_ZZ6Z
set hke_z65=FirstOfGroup(hke_Z8Z[hke_z15])
set hke_z76=1
loop
exitwhen hke_z76>5
set hke_Z66=UnitItemInSlotBJ(hke_z65,hke_z76)
if(GetItemCharges(hke_Z66)>0)then
set hke_z78=hke_z76+1
loop
exitwhen hke_z78>6
set hke_ZZ6Z=UnitItemInSlotBJ(hke_z65,hke_z78)
if(GetItemTypeId(hke_Z66)==GetItemTypeId(hke_ZZ6Z))then
call SetItemCharges(hke_Z66,(GetItemCharges(hke_Z66)+GetItemCharges(hke_ZZ6Z)))
call RemoveItem(hke_ZZ6Z)
endif
set hke_z78=hke_z78+1
endloop
endif
set hke_z76=hke_z76+1
endloop
set hke_Z66=null
set hke_ZZ6Z=null
set hke_z65=null
endfunction
function hke_ZZ7Z takes integer hke_z15,integer hke_Z75 returns nothing
local unit hke_z65
local item hke_z86
set hke_z65=FirstOfGroup(hke_Z8Z[hke_z15])
set hke_z86=UnitItemInSlotBJ(hke_z65,1)
call SetItemCharges(hke_z86,(GetItemCharges(hke_z86)+hke_Z75))
set hke_z86=null
set hke_z65=null
endfunction
function hke_ZZ8Z takes nothing returns nothing
local unit hke_z65
set hke_z65=GetEnumUnit()
call GroupAddUnit(hke_z8Z,hke_z65)
set hke_z65=null
endfunction
function hke_ZZ9Z takes nothing returns nothing
local unit hke_z65
set hke_z65=GetEnumUnit()
call GroupRemoveUnit(hke_z8Z,hke_z65)
set hke_z65=null
endfunction
function hke_ZzZZ takes nothing returns nothing
local unit hke_z65=GetTriggerUnit()
if((IsUnitDeadBJ(hke_z65))and(IsUnitType(hke_z65,UNIT_TYPE_HERO)))then
call GroupRemoveUnit(hke_z8Z,hke_z65)
endif
endfunction
function hke_ZzzZ takes nothing returns nothing
call ForGroup(hke_z8Z,function hke_ZzZZ)
endfunction
function hke_Zz0Z takes nothing returns nothing
local unit hke_z65
set hke_z65=GetEnumUnit()
call ReviveHeroLoc(hke_z65,hke_Z9Z[hke_Zzz],true)
call SetUnitManaPercentBJ(hke_z65,100)
set hke_z65=null
endfunction
function hke_Zz1Z takes player hke_z05 returns nothing
local group hke_z46
set hke_z46=hke_Z94(hke_z05)
set hke_Zzz=GetPlayerId(hke_z05)
call ForGroup(hke_z46,function hke_Zz0Z)
call DestroyGroup(hke_z46)
set hke_z46=null
endfunction
function hke_Zz2Z takes nothing returns nothing
local unit hke_z65=GetEnumUnit()
call ModifyHeroStat(hke_z81,hke_z65,hke_z91,hke_z71)
set hke_z65=null
endfunction
function hke_Zz3Z takes integer hke_z15,integer hke_Zz4Z,integer hke_Zz5Z,boolean hke_z25 returns nothing
local integer hke_Zz6Z
if(hke_z25)then
set hke_Zz6Z=0
else
set hke_Zz6Z=1
endif
if(hke_Z0)then
set hke_z91=hke_Zz6Z
set hke_z81=hke_Zz4Z
set hke_z71=hke_Zz5Z
call ForGroup(hke_Z8Z[hke_z15],function hke_Zz2Z)
else
call ModifyHeroStat(hke_Zz4Z,hke_z7[hke_z15],hke_Zz6Z,hke_Zz5Z)
endif
endfunction
function hke_Zz7Z takes unit hke_z65,integer hke_Zz5Z,boolean hke_z25 returns nothing
local integer hke_z15
set hke_z15=GetHeroLevel(hke_z65)
if(hke_z25)then
set hke_z15=hke_z15+hke_Zz5Z
else
set hke_z15=hke_z15-hke_Zz5Z
endif
call SetHeroLevelBJ(hke_z65,hke_z15,false)
endfunction
function hke_Zz8Z takes nothing returns nothing
local unit hke_z65=GetEnumUnit()
call hke_Zz7Z(hke_z65,hke_ZZ2,hke_Z1z)
set hke_z65=null
endfunction
function hke_Zz9Z takes integer hke_z15,integer hke_Zz5Z,boolean hke_z25 returns nothing
if(hke_Z0)then
set hke_ZZ2=hke_Zz5Z
set hke_Z1z=hke_z25
call ForGroup(hke_Z8Z[hke_z15],function hke_Zz8Z)
else
call hke_Zz7Z(hke_z7[hke_z15],hke_Zz5Z,hke_z25)
endif
endfunction
function hke_Z0ZZ takes string hke_Z0zZ returns integer
local string hke_Z00Z="0123456789"
local string hke_Z01Z="ABCDEFGHIJKLMNOPQRSTUVWXYZ"
local string hke_Z02Z="abcdefghijklmnopqrstuvwxyz"
local integer Id=0
local integer hke_Z03Z=1
local integer hke_Z04Z=1
loop
exitwhen hke_Z03Z>StringLength(hke_Z0zZ)
loop
exitwhen hke_Z04Z>10
if SubString(hke_Z0zZ,hke_Z03Z-1,hke_Z03Z)==SubString(hke_Z00Z,hke_Z04Z-1,hke_Z04Z)then
set Id=Id+R2I((48+hke_Z04Z-1)*Pow(256.,I2R(StringLength(hke_Z0zZ)-hke_Z03Z)))
set hke_Z04Z=hke_Z04Z+1
else
set hke_Z04Z=hke_Z04Z+1
endif
endloop
set hke_Z04Z=1
loop
exitwhen hke_Z04Z>26
if SubString(hke_Z0zZ,hke_Z03Z-1,hke_Z03Z)==SubString(hke_Z01Z,hke_Z04Z-1,hke_Z04Z)then
set Id=Id+R2I(I2R(65+hke_Z04Z-1)*Pow(256.,I2R(StringLength(hke_Z0zZ)-hke_Z03Z)))
set hke_Z04Z=hke_Z04Z+1
else
set hke_Z04Z=hke_Z04Z+1
endif
endloop
set hke_Z04Z=1
loop
exitwhen hke_Z04Z>26
if SubString(hke_Z0zZ,hke_Z03Z-1,hke_Z03Z)==SubString(hke_Z02Z,hke_Z04Z-1,hke_Z04Z)then
set Id=Id+R2I((97+hke_Z04Z-1)*Pow(256.,I2R(StringLength(hke_Z0zZ)-hke_Z03Z)))
set hke_Z04Z=hke_Z04Z+1
else
set hke_Z04Z=hke_Z04Z+1
endif
endloop
set hke_Z04Z=1
set hke_Z03Z=hke_Z03Z+1
endloop
return Id
endfunction
function hke_Z05Z takes integer hke_Z06Z returns string
local string hke_Z00Z="0123456789"
local string hke_Z01Z="ABCDEFGHIJKLMNOPQRSTUVWXYZ"
local string hke_Z02Z="abcdefghijklmnopqrstuvwxyz"
local string hke_Z07Z=""
local integer hke_Z03Z=0
local integer hke_Z08Z=0
loop
exitwhen hke_Z06Z==0
set hke_Z03Z=ModuloInteger(hke_Z06Z,256)
if hke_Z03Z>=48 and hke_Z03Z<=57 then
set hke_Z08Z=hke_Z03Z-48
set hke_Z07Z=SubString(hke_Z00Z,hke_Z08Z,hke_Z08Z+1)+hke_Z07Z
endif
if hke_Z03Z>=65 and hke_Z03Z<=90 then
set hke_Z08Z=hke_Z03Z-65
set hke_Z07Z=SubString(hke_Z01Z,hke_Z08Z,hke_Z08Z+1)+hke_Z07Z
endif
if hke_Z03Z>=97 and hke_Z03Z<=122 then
set hke_Z08Z=hke_Z03Z-97
set hke_Z07Z=SubString(hke_Z02Z,hke_Z08Z,hke_Z08Z+1)+hke_Z07Z
endif
set hke_Z06Z=hke_Z06Z/256
endloop
return hke_Z07Z
endfunction
function hke_Z09Z takes unit hke_z65 returns string
local integer hke_z15
set hke_z15=GetUnitTypeId(hke_z65)
if(hke_z15==0)then
return""
else
return hke_Z05Z(hke_z15)
endif
endfunction
function hke_Z1ZZ takes unit hke_z65 returns string
local item hke_z86=UnitItemInSlotBJ(hke_z65,1)
local integer hke_z15=GetItemTypeId(hke_z86)
if(hke_z15==0)then
return""
else
set hke_z86=null
return hke_Z05Z(hke_z15)
endif
endfunction
function hke_Z1zZ takes integer hke_Z10Z returns integer
local string hke_Z11Z=GetEventPlayerChatString()
if(StringLength(hke_Z11Z)==hke_Z10Z+3)then
return(hke_Z0ZZ(SubStringBJ(hke_Z11Z,hke_Z10Z,hke_Z10Z+3)))
else
return 0
endif
endfunction
function hke_Z12Z takes unit hke_z65,integer hke_z66,boolean hke_z25 returns nothing
local location hke_z95
local integer hke_z15
set hke_z15=hke_Z1zZ(hke_z66)
if(hke_z15==0)then
else
if(hke_z25)then
set hke_z95=GetUnitLoc(hke_z65)
call CreateItemLoc(hke_z15,hke_z95)
call RemoveLocation(hke_z95)
set hke_z95=null
else
call UnitAddItemById(hke_z65,hke_z15)
endif
endif
endfunction
function hke_Z13Z takes unit hke_z65,real hke_Z14Z,boolean hke_z25 returns nothing
local location hke_z95=GetUnitLoc(hke_z65)
local player hke_z05=GetOwningPlayer(hke_z65)
call SetBlightRadiusLocBJ(hke_z25,hke_z05,hke_z95,hke_Z14Z)
call RemoveLocation(hke_z95)
set hke_z95=null
set hke_z05=null
endfunction
function hke_Z15Z takes unit hke_z65,real hke_Z14Z returns nothing
call SetUnitFlyHeight(hke_z65,hke_Z14Z,.0)
endfunction
function hke_Z16Z takes nothing returns integer
local integer hke_Z17Z=0
local integer hke_Z18Z=0
local integer array hke_Z19Z
local integer hke_z15=0
local player hke_z05=GetLocalPlayer()
loop
exitwhen hke_z15>11
set hke_Z19Z[hke_z15]=0
set hke_z15=hke_z15+1
endloop
loop
exitwhen hke_Z17Z>14
call StoreInteger(hke_z03,"Hke_Player","Hke_number",GetPlayerId(hke_z05)+1)
call TriggerSyncStart()
call SyncStoredInteger(hke_z03,"Hke_Player","Hke_number")
call TriggerSyncReady()
set hke_Z18Z=GetStoredInteger(hke_z03,"Hke_Player","Hke_number")-1
set hke_Z19Z[hke_Z18Z]=hke_Z19Z[hke_Z18Z]+1
call FlushStoredMission(hke_z03,"Hke_Player")
set hke_Z17Z=hke_Z17Z+1
endloop
set hke_Z18Z=0
set hke_Z17Z=0
set hke_z05=null
loop
exitwhen hke_Z17Z>11
if hke_Z19Z[hke_Z18Z]<hke_Z19Z[hke_Z17Z]then
set hke_Z18Z=hke_Z17Z
endif
set hke_Z17Z=hke_Z17Z+1
endloop
return hke_Z18Z+1
endfunction
function hke_Z2ZZ takes unit hke_z65,integer hke_Z2zZ,boolean hke_z25 returns nothing
if(hke_z25)then
call UnitAddAbility(hke_z65,hke_Z2zZ)
call SetUnitAbilityLevel(hke_z65,hke_Z2zZ,100)
call UnitMakeAbilityPermanent(hke_z65,true,hke_Z2zZ)
else
call UnitMakeAbilityPermanent(hke_z65,false,hke_Z2zZ)
call UnitRemoveAbility(hke_z65,hke_Z2zZ)
endif
endfunction
function hke_Z20Z takes nothing returns nothing
local unit hke_z65=GetEnumUnit()
call hke_Z2ZZ(hke_z65,hke_zzz,hke_z0z)
set hke_z65=null
endfunction
function hke_Z21Z takes integer hke_z15,integer hke_Z2zZ,boolean hke_z25 returns nothing
if(hke_Z0)then
set hke_zzz=hke_Z2zZ
set hke_z0z=hke_z25
call ForGroup(hke_Z8Z[hke_z15],function hke_Z20Z)
else
call hke_Z2ZZ(hke_z7[hke_z15],hke_Z2zZ,hke_z25)
endif
endfunction
function hke_Z22Z takes string hke_Z11Z returns integer
if(hke_Z11Z=="mm")then
return 1094937907
endif
if(hke_Z11Z=="xj")then
return 1095659625
endif
if(hke_Z11Z=="zj")then
return 1095262824
endif
if(hke_Z11Z=="zm")then
return 1095721842
endif
if(hke_Z11Z=="ft")then
return 1096119411
endif
if(hke_Z11Z=="xx")then
return 1095333473
endif
if(hke_Z11Z=="sb")then
return 1095066998
endif
if(hke_Z11Z=="yx")then
return 1097886070
endif
if(hke_Z11Z=="rh")then
return 1095657827
endif
if(hke_Z11Z=="fl")then
return 1095656289
endif
if(hke_Z11Z=="bs")then
return 1094935923
endif
if(hke_Z11Z=="jg")then
return 1095332984
endif
if(hke_Z11Z=="jf")then
return 1095328816
endif
if(hke_Z11Z=="js")then
return 1095332728
endif
if(hke_Z11Z=="jm")then
return 1095332722
endif
if(hke_Z11Z=="jj")then
return 1095917932
endif
if(hke_Z11Z=="fy")then
return 1098150517
endif
if(hke_Z11Z=="ghh")then
return 1095262562
endif
if(hke_Z11Z=="ghj")then
return 1095721317
endif
if(hke_Z11Z=="gqj")then
return 1095065970
endif
if(hke_Z11Z=="gxx")then
return 1096114550
endif
if(hke_Z11Z=="gzz")then
return 1095262564
endif
if(hke_Z11Z=="gxe")then
return 1096114549
endif
if(hke_Z11Z=="gjj")then
return 1095065960
endif
if(hke_Z11Z=="gml")then
return 1094934883
endif
if(hke_Z11Z=="gyl")then
return 1097818482
endif
if(hke_Z11Z=="gjs")then
return 1096905580
endif
if(hke_Z11Z=="qhy")then
return 1095329378
endif
if(hke_Z11Z=="qdy")then
return 1095331938
endif
if(hke_Z11Z=="qlh")then
return 1095332719
endif
if(hke_Z11Z=="qyz")then
return 1095328878
endif
if(hke_Z11Z=="qbd")then
return 1095331682
endif
if(hke_Z11Z=="qfs")then
return 1095328610
endif
if(hke_Z11Z=="qsd")then
return 1095330924
endif
if(hke_Z11Z=="qjs")then
return 1095332706
endif
if(hke_Z11Z=="qha")then
return 1095328870
endif
return 0
endfunction
function hke_Z23Z takes nothing returns nothing
local unit hke_z65=GetEnumUnit()
call SetUnitInvulnerable(hke_z65,hke_z0z)
call hke_Z2ZZ(hke_z65,1098282348,hke_z0z)
set hke_z65=null
endfunction
function hke_Z24Z takes integer hke_z15,boolean hke_z25 returns nothing
if(hke_Z0)then
set hke_z0z=hke_z25
call ForGroup(hke_Z8Z[hke_z15],function hke_Z23Z)
else
call SetUnitInvulnerable(hke_z7[hke_z15],hke_z25)
call hke_Z2ZZ(hke_z7[hke_z15],1098282348,hke_z25)
endif
endfunction
function hke_Z25Z takes nothing returns nothing
local unit hke_z65=GetEnumUnit()
call SetUnitPathing(hke_z65,not(hke_z0z))
set hke_z65=null
endfunction
function hke_Z26Z takes integer hke_z15,boolean hke_z25 returns nothing
if(hke_Z0)then
set hke_z0z=hke_z25
call ForGroup(hke_Z8Z[hke_z15],function hke_Z25Z)
else
call SetUnitPathing(hke_z7[hke_z15],not(hke_z25))
endif
endfunction
function hke_Z27Z takes unit hke_z65,boolean hke_z25 returns nothing
if(hke_z25)then
call SetUnitMoveSpeed(hke_z65,1000)
else
call SetUnitMoveSpeed(hke_z65,GetUnitDefaultMoveSpeed(hke_z65))
endif
endfunction
function hke_Z28Z takes nothing returns nothing
local unit hke_z65=GetEnumUnit()
call hke_Z27Z(hke_z65,hke_z0z)
set hke_z65=null
endfunction
function hke_Z29Z takes integer hke_z15,boolean hke_z25 returns nothing
if(hke_Z0)then
set hke_z0z=hke_z25
call ForGroup(hke_Z8Z[hke_z15],function hke_Z28Z)
else
call hke_Z27Z(hke_z7[hke_z15],hke_z25)
endif
endfunction
function hke_Z3ZZ takes integer hke_z15,boolean hke_z25 returns nothing
call hke_ZzzZ()
if(hke_Z0)then
if(hke_z25)then
if(CountUnitsInGroup(hke_z8Z)==0)then
call EnableTrigger(hke_z73)
endif
call GroupAddGroup(hke_Z8Z[hke_z15],hke_z8Z)
else
call GroupRemoveGroup(hke_Z8Z[hke_z15],hke_z8Z)
if(CountUnitsInGroup(hke_z8Z)==0)then
call DisableTrigger(hke_z73)
endif
endif
else
if(hke_z25)then
if(CountUnitsInGroup(hke_z8Z)==0)then
call EnableTrigger(hke_z73)
endif
call GroupAddUnit(hke_z8Z,hke_z7[hke_z15])
else
call GroupRemoveUnit(hke_z8Z,hke_z7[hke_z15])
if(CountUnitsInGroup(hke_z8Z)==0)then
call DisableTrigger(hke_z73)
endif
endif
endif
endfunction
function hke_Z3zZ takes unit hke_z65,boolean hke_z25 returns nothing
call hke_Z2ZZ(hke_z65,1095262562,hke_z25)
call hke_Z2ZZ(hke_z65,1095721317,hke_z25)
call hke_Z2ZZ(hke_z65,1095065970,hke_z25)
call hke_Z2ZZ(hke_z65,1096114550,hke_z25)
call hke_Z2ZZ(hke_z65,1095262564,hke_z25)
call hke_Z2ZZ(hke_z65,1096114549,hke_z25)
call hke_Z2ZZ(hke_z65,1094934883,hke_z25)
call hke_Z2ZZ(hke_z65,1095065960,hke_z25)
call hke_Z2ZZ(hke_z65,1097818482,hke_z25)
call hke_Z2ZZ(hke_z65,1096905580,hke_z25)
endfunction
function hke_Z30Z takes nothing returns nothing
local unit hke_z65=GetEnumUnit()
call hke_Z3zZ(hke_z65,hke_z0z)
set hke_z65=null
endfunction
function hke_Z31Z takes integer hke_z15,boolean hke_z25 returns nothing
if(hke_Z0)then
set hke_z0z=hke_z25
call ForGroup(hke_Z8Z[hke_z15],function hke_Z30Z)
else
call hke_Z3zZ(hke_z7[hke_z15],hke_z25)
endif
endfunction
function hke_Z32Z takes unit hke_z65 returns nothing
call hke_Z2ZZ(hke_z65,1094937907,false)
call hke_Z2ZZ(hke_z65,1095659625,false)
call hke_Z2ZZ(hke_z65,1095262824,false)
call hke_Z2ZZ(hke_z65,1095721842,false)
call hke_Z2ZZ(hke_z65,1096119411,false)
call hke_Z2ZZ(hke_z65,1095333473,false)
call hke_Z2ZZ(hke_z65,1095066998,false)
call hke_Z2ZZ(hke_z65,1097886070,false)
call hke_Z2ZZ(hke_z65,1095657827,false)
call hke_Z2ZZ(hke_z65,1095656289,false)
call hke_Z2ZZ(hke_z65,1098282348,false)
call hke_Z2ZZ(hke_z65,1094935923,false)
call hke_Z2ZZ(hke_z65,1095332984,false)
call hke_Z2ZZ(hke_z65,1095328816,false)
call hke_Z2ZZ(hke_z65,1095332728,false)
call hke_Z2ZZ(hke_z65,1095332722,false)
call hke_Z2ZZ(hke_z65,1098150517,false)
call SetUnitInvulnerable(hke_z65,false)
call SetUnitPathing(hke_z65,true)
call hke_Z27Z(hke_z65,false)
call GroupRemoveUnit(hke_z8Z,hke_z65)
endfunction
function hke_Z33Z takes nothing returns nothing
local unit hke_z65=GetEnumUnit()
call hke_Z32Z(hke_z65)
set hke_z65=null
endfunction
function hke_Z34Z takes integer hke_z15 returns nothing
if(hke_Z0)then
call ForGroup(hke_Z8Z[hke_z15],function hke_Z33Z)
else
call hke_Z32Z(hke_z7[hke_z15])
endif
endfunction
function hke_Z35Z takes nothing returns nothing
local unit hke_z65=GetTriggerUnit()
local trigger hke_Z66=GetTriggeringTrigger()
call RemoveUnit(hke_z65)
call DisableTrigger(hke_Z66)
call DestroyTrigger(hke_Z66)
set hke_z65=null
set hke_Z66=null
endfunction
function hke_Z36Z takes integer hke_z66,unit hke_Z37Z,player hke_Z38Z returns nothing
local location hke_z95
local unit hke_z65
local integer hke_Z39Z=0
local integer hke_Z4ZZ=0
local trigger hke_Z66
if(hke_z66==0)then
set hke_Z39Z=1095726692
set hke_Z4ZZ=852503
endif
if(hke_z66==1)then
set hke_Z39Z=1095070833
set hke_Z4ZZ=852184
endif
if(hke_z66==2)then
set hke_Z39Z=1095070566
set hke_Z4ZZ=852183
endif
if((hke_Z39Z==0)and(hke_Z4ZZ==0))then
return
endif
set hke_z95=GetUnitLoc(hke_Z37Z)
set hke_z65=CreateUnitAtLoc(hke_Z38Z,1851941228,hke_z95,bj_UNIT_FACING)
call UnitAddAbility(hke_z65,1098282348)
call UnitAddAbility(hke_z65,hke_Z39Z)
call ShowUnit(hke_z65,false)
call SetUnitUseFood(hke_z65,false)
call SetUnitScale(hke_z65,.01,.01,.01)
call SetUnitState(hke_z65,UNIT_STATE_MANA,GetUnitState(hke_z65,UNIT_STATE_MAX_MANA))
call IssueImmediateOrderById(hke_z65,hke_Z4ZZ)
set hke_Z66=CreateTrigger()
call TriggerRegisterUnitEvent(hke_Z66,hke_z65,EVENT_UNIT_SPELL_ENDCAST)
call TriggerRegisterUnitEvent(hke_Z66,hke_z65,EVENT_UNIT_SPELL_FINISH)
call TriggerAddAction(hke_Z66,function hke_Z35Z)
call RemoveLocation(hke_z95)
set hke_z95=null
set hke_Z66=null
set hke_z65=null
endfunction
function hke_Z4zZ takes unit hke_Z37Z returns nothing
local player hke_z05=GetTriggerPlayer()
local location hke_z95=GetUnitLoc(hke_Z37Z)
local trigger hke_Z66=CreateTrigger()
local unit hke_z65=CreateUnitAtLoc(hke_z05,1751543663,hke_z95,bj_UNIT_FACING)
call UnitAddAbility(hke_z65,1098282348)
call UnitAddAbility(hke_z65,1095332709)
call ShowUnit(hke_z65,false)
call SetUnitUseFood(hke_z65,false)
call SetUnitScale(hke_z65,.01,.01,.01)
call IssuePointOrderByIdLoc(hke_z65,852592,hke_z95)
call TriggerRegisterUnitEvent(hke_Z66,hke_z65,EVENT_UNIT_SPELL_ENDCAST)
call TriggerRegisterUnitEvent(hke_Z66,hke_z65,EVENT_UNIT_SPELL_FINISH)
call TriggerAddAction(hke_Z66,function hke_Z35Z)
call RemoveLocation(hke_z95)
set hke_z95=null
set hke_Z66=null
set hke_z05=null
endfunction
function hke_Z40Z takes integer hke_z15,dialog hke_Z41Z,trigger hke_zZ6 returns nothing
set hke_Zz3[hke_z15]=hke_Z41Z
set hke_Z03[hke_z15]=hke_zZ6
endfunction
function hke_Z42Z takes integer hke_z15,string hke_Z43Z returns nothing
call DialogClear(hke_Zz3[hke_z15])
call DialogSetMessage(hke_Zz3[hke_z15],(hke_Z43Z+hke_Z0z+hke_Z62))
endfunction
function hke_Z44Z takes integer hke_z15,player hke_z05,boolean hke_z77 returns nothing
if(hke_z77)then
call EnableTrigger(hke_Z03[hke_z15])
call DialogDisplay(hke_z05,hke_Zz3[hke_z15],true)
call TimerStart(hke_Z73[hke_z15],hke_z1,false,null)
else
call DisableTrigger(hke_Z03[hke_z15])
call DialogDisplay(hke_z05,hke_Zz3[hke_z15],false)
endif
endfunction
function hke_Z45Z takes integer hke_z15,player hke_z05 returns nothing
call hke_Z40Z(hke_z15,hke_zZ1[hke_z15],hke_ZZ1[hke_z15])
call hke_Z42Z(hke_z15,"Main")
set hke_z2z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Resources Menu[A]",65)
set hke_z4z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Automatic Systems [B]",66)
set hke_z5z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Modify Selected Unit[C]",67)
set hke_z3z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Personal Settings[D]",68)
set hke_z9z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Helps[E]",69)
if(hke_z05==hke_z5)then
set hke_z8z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Cheats: Other Players[F]",70)
set hke_z7z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Settings: Other Players[G]",71)
set hke_z6z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Game Settings[H]",72)
if(hke_z13)then
set hke_Zz0[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"No Replays[L]",72)
endif
endif
set hke_Z10[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Exit Menu[X]",88)
call hke_Z44Z(hke_z15,hke_z05,true)
endfunction
function hke_Z46Z takes integer hke_z15,player hke_z05 returns nothing
local string hke_Z11Z
call hke_Z40Z(hke_z15,hke_Z20[hke_z15],hke_Zz1[hke_z15])
call hke_Z42Z(hke_z15,"Automated Systems")
if(IsTriggerEnabled(hke_z40[hke_z15]))then
set hke_Z11Z="Off"
else
set hke_Z11Z="On"
endif
set hke_z2z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],(hke_Z11Z+"Gold Bonus[A]"),65)
if(IsTriggerEnabled(hke_z50[hke_z15]))then
set hke_Z11Z="Off"
else
set hke_Z11Z="On"
endif
set hke_z4z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],(hke_Z11Z+"Wood Bonus[B]"),66)
if(IsTriggerEnabled(hke_z60[hke_z15]))then
set hke_Z11Z="Off"
else
set hke_Z11Z="On"
endif
set hke_z5z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],(hke_Z11Z+"Unlimited Food[C]"),67)
if(IsTriggerEnabled(hke_z80[hke_z15]))then
set hke_Z11Z="Off"
else
set hke_Z11Z="On"
endif
set hke_z3z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],(hke_Z11Z+"No Cooldown"),68)
if(IsTriggerEnabled(hke_z70[hke_z15]))then
set hke_Z11Z="Off"
else
set hke_Z11Z="On"
endif
set hke_z9z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],(hke_Z11Z+"Unlimited Reincarnation[E]"),69)
if(IsTriggerEnabled(hke_z90[hke_z15]))then
set hke_Z11Z="Off"
else
set hke_Z11Z="On"
endif
set hke_z8z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],(hke_Z11Z+"Recover MP: "+I2S(R2I(hke_ZZZ))+"%[F]"),70)
if(IsTriggerEnabled(hke_ZZ3[hke_z15]))then
set hke_Z11Z="Off"
else
set hke_Z11Z="On"
endif
set hke_z7z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],(hke_Z11Z+"HP<"+I2S(R2I(hke_z92))+"% -->"+I2S(R2I(hke_z41))+"%[G]"),71)
set hke_z6z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Activate All[O]",79)
set hke_Zz0[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Deactivate All[U]",85)
set hke_ZZ0[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Previous Menu[R]",82)
set hke_Z00[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Exit[X]",88)
call hke_Z44Z(hke_z15,hke_z05,true)
set hke_Z11Z=""
endfunction
function hke_Z47Z takes integer hke_z15,player hke_z05 returns nothing
call hke_Z40Z(hke_z15,hke_Z20[hke_z15],hke_Z01[hke_z15])
call hke_Z42Z(hke_z15,"Modify Selected Unit")
set hke_z2z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Almighty[A]",65)
set hke_z4z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Invisible[B]",66)
set hke_z5z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"No Path[C]",67)
set hke_z3z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Immune Magic[D]",68)
set hke_z9z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"True Sight[E]",69)
set hke_z8z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Movement Speed[F]",70)
set hke_z7z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Auras[G]",71)
set hke_z6z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Next Page[N]",78)
if((hke_z9Z)or(hke_z5==hke_z05))then
set hke_Zz0[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Kill Every Second[K]",75)
endif
set hke_ZZ0[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Cancel All[U]",85)
set hke_Z00[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Previous Menu[R]",82)
set hke_Z10[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Exit[X]",88)
call hke_Z44Z(hke_z15,hke_z05,true)
endfunction
function hke_Z48Z takes integer hke_z15,player hke_z05 returns nothing
call hke_Z40Z(hke_z15,hke_Z91[hke_z15],hke_Z81[hke_z15])
call hke_Z42Z(hke_z15,"Modify Selected Unit")
set hke_z2z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Immolation[A]",65)
set hke_z4z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Dodge[B]",514)
set hke_z5z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Bash[C]",67)
set hke_z3z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Critical Strike[D]",68)
set hke_z9z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Damage Return[E]",69)
set hke_z8z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Splash Damage[F]",70)
set hke_z7z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Ignition[G]",71)
set hke_z6z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"33% Magic Resistance[H]",72)
set hke_Zz0[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"100% Evasion[I]",73)
set hke_ZZ0[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Next Page[N]",78)
set hke_Z00[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Previous Menu[R]",82)
set hke_Z10[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Exit[X]",88)
call hke_Z44Z(hke_z15,hke_z05,true)
endfunction
function hke_Z49Z takes integer hke_z15,player hke_z05 returns nothing
call hke_Z40Z(hke_z15,hke_Z91[hke_z15],hke_Z21[hke_z15])
call hke_Z42Z(hke_z15,"Auras")
set hke_z2z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Brilliance Aura[A]",65)
set hke_z4z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Throns Aura[B]",66)
set hke_z5z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Endurance Aura[C]",67)
set hke_z3z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Trueshot Aura[D]",68)
set hke_z9z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Unholy Aura[E]",69)
set hke_z8z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Vampiric Aura[F]",70)
set hke_z7z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Devotion Aura[G]",71)
set hke_z6z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Command Aura[H]",72)
set hke_Zz0[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Healing Aura[I]",73)
set hke_ZZ0[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Quick Sand Aura[J]",74)
set hke_Z00[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"All Auras[K]",75)
set hke_Z10[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Exit[X]",88)
call hke_Z44Z(hke_z15,hke_z05,true)
endfunction
function hke_Z5ZZ takes integer hke_z15,player hke_z05 returns nothing
local integer hke_Z75=0
local string hke_Z11Z
local string hke_Z5zZ
local player hke_Z65
call hke_Z40Z(hke_z15,hke_Z20[hke_z15],hke_Z51[hke_z15])
call hke_Z42Z(hke_z15,"Players' Cheats")
loop
exitwhen hke_Z75>11
set hke_Z65=Player(hke_Z75)
if((GetPlayerController(hke_Z65)==MAP_CONTROL_USER)and(GetPlayerSlotState(hke_Z65)==PLAYER_SLOT_STATE_PLAYING)and(hke_Z65!=hke_z5))then
set hke_Z5zZ=GetPlayerName(hke_Z65)
if(hke_z6[hke_Z75])then
set hke_Z11Z="Disable"
else
set hke_Z11Z="Enable"
endif
set hke_ZzZ[hke_Z75]=DialogAddButton(hke_Zz3[hke_z15],(hke_Z11Z+hke_Z5zZ+"'s cheats"),0)
endif
set hke_Z75=hke_Z75+1
endloop
set hke_z2z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Previous Menu[R]",82)
set hke_z4z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Exit[X]",88)
call hke_Z44Z(hke_z15,hke_z05,true)
set hke_Z65=null
set hke_Z11Z=""
set hke_Z5zZ=""
endfunction
function hke_Z50Z takes integer hke_z15,player hke_z05 returns nothing
set hke_Z8[hke_z15]=0
call hke_Z40Z(hke_z15,hke_zZ1[hke_z15],hke_Z71[hke_z15])
call hke_Z42Z(hke_z15,"Unit")
set hke_z2z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Up 100 Levels[A]",65)
set hke_z4z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],("Add Stats"+(I2S(hke_Z3)+"[B]")),66)
set hke_z5z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Copy Item[C]",67)
set hke_z3z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Copy Unit[D]",68)
set hke_z9z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Drop Item[E]",69)
set hke_z8z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Share Vision[F]",70)
set hke_z7z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Special Abilities[G]",71)
if((hke_z7Z)or(hke_z5==hke_z05))then
set hke_z6z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Share Control[H]",72)
endif
if(hke_z5==hke_z05)then
endif
if(hke_z05==hke_z5)then
set hke_ZZ0[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Do All Of Them[J]",74)
endif
set hke_Z00[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Exit[X]",88)
call hke_Z44Z(hke_z15,hke_z05,true)
endfunction
function hke_Z51Z takes integer hke_z15,player hke_z05 returns nothing
local string hke_Z11Z
call hke_Z40Z(hke_z15,hke_Z20[hke_z15],hke_Z31[hke_z15])
call hke_Z42Z(hke_z15,"Game Cheats")
if(hke_Z0)then
set hke_Z11Z="Off"
else
set hke_Z11Z="On"
endif
set hke_z2z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],(hke_Z11Z+"Activate All Units[A]"),65)
set hke_z4z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],("Item Charges[B]"),66)
if(hke_Z5Z)then
set hke_Z11Z="Off"
else
set hke_Z11Z="On"
endif
set hke_z5z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],(hke_Z11Z+"Protect CheatMaster[C]"),67)
if(hke_Z6Z)then
set hke_Z11Z="Off"
else
set hke_Z11Z="On"
endif
set hke_z3z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],(hke_Z11Z+"Fast Training+No Food[D]"),68)
if(hke_Z7Z)then
set hke_Z11Z="Off"
else
set hke_Z11Z="On"
endif
set hke_z9z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],("Cancel "+hke_Z11Z+" Maphack[E]"),69)
if(hke_z9Z)then
set hke_Z11Z="Off"
else
set hke_Z11Z="On"
endif
set hke_z8z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],(hke_Z11Z+"One Hit Kill[F]"),70)
if(hke_ZZz)then
set hke_Z11Z="Off"
else
set hke_Z11Z="On"
endif
set hke_z7z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],(hke_Z11Z+"Forbid 1HitKill Building[G]"),71)
if(hke_z7Z)then
set hke_Z11Z="Off"
else
set hke_Z11Z="On"
endif
set hke_z6z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],(hke_Z11Z+"Other Players' Units[H]"),72)
if(hke_Z52)then
set hke_Z11Z="On"
else
set hke_Z11Z="Off"
endif
set hke_Zz0[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],(hke_Z11Z+"Forbid Peasants[I]"),73)
set hke_ZZ0[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Previous Menu[R]",82)
set hke_Z00[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Exit[X]",88)
call hke_Z44Z(hke_z15,hke_z05,true)
set hke_Z11Z=""
endfunction
function hke_Z52Z takes integer hke_z15,player hke_z05 returns nothing
local string hke_Z5zZ
local integer hke_Z75=0
local player hke_Z65
call hke_Z40Z(hke_z15,hke_Z20[hke_z15],hke_Z41[hke_z15])
call hke_Z42Z(hke_z15,"Modify Players")
loop
exitwhen hke_Z75>11
set hke_Z65=Player(hke_Z75)
if(GetPlayerSlotState(hke_Z65)==PLAYER_SLOT_STATE_PLAYING)then
set hke_Z5zZ=GetPlayerName(hke_Z65)
set hke_ZzZ[hke_Z75]=DialogAddButton(hke_Zz3[hke_z15],("Select"+hke_Z5zZ),0)
endif
set hke_Z75=hke_Z75+1
endloop
set hke_ZzZ[12]=DialogAddButton(hke_Zz3[hke_z15],("Select Neutrals Creeps"),90)
set hke_z2z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Previous Menu[R]",82)
set hke_z4z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Exit[X]",88)
call hke_Z44Z(hke_z15,hke_z05,true)
set hke_Z5zZ=""
set hke_Z65=null
endfunction
function hke_Z53Z takes integer hke_z15,player hke_z05 returns nothing
local player hke_Z65=Player(hke_Z5z)
call hke_Z40Z(hke_z15,hke_Z91[hke_z15],hke_Z61[hke_z15])
call hke_Z42Z(hke_z15,"Modify Players")
set hke_z2z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Set Resources[A]",65)
set hke_z4z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Set Alliances[B]",66)
if(GetPlayerTaxRate(hke_Z65,hke_z05,PLAYER_STATE_RESOURCE_GOLD)==0)then
set hke_z5z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Steal"+I2S(hke_z22)+"% Gold Income[C]",67)
else
set hke_z5z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Stop Stealing Gold[C]",67)
endif
if(GetPlayerTaxRate(hke_Z65,hke_z05,PLAYER_STATE_RESOURCE_LUMBER)==0)then
set hke_z3z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Steal"+I2S(hke_z22)+"% Lumber Income[D]",68)
else
set hke_z3z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Stop Stealing Lumber[D]",67)
endif
set hke_Z00[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Previous Menu[R]",82)
set hke_Z10[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Exit[X]",88)
call hke_Z44Z(hke_z15,hke_z05,true)
set hke_Z65=null
endfunction
function hke_Z54Z takes integer hke_z15,player hke_z05 returns nothing
local integer hke_Z75=0
local player hke_Z65
local string hke_Z11Z
local string hke_Z5zZ
call hke_Z40Z(hke_z15,hke_Z91[hke_z15],hke_Z11[hke_z15])
call hke_Z42Z(hke_z15,"Unit's Control")
loop
exitwhen hke_Z75>12
set hke_Z65=Player(hke_Z75)
if(GetPlayerSlotState(hke_Z65)==PLAYER_SLOT_STATE_PLAYING)then
set hke_Z5zZ=GetPlayerName(hke_Z65)
set hke_ZzZ[hke_Z75]=DialogAddButton(hke_Zz3[hke_z15],("Let"+hke_Z5zZ+"Control"),0)
endif
set hke_Z75=hke_Z75+1
endloop
set hke_z2z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Previous Menu[R]",82)
set hke_z4z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Exit[X]",88)
call hke_Z44Z(hke_z15,hke_z05,true)
set hke_Z65=null
set hke_Z11Z=""
set hke_Z5zZ=""
endfunction
function hke_Z55Z takes integer hke_z15,player hke_z05 returns nothing
local string hke_Z11Z
call hke_Z40Z(hke_z15,hke_Z20[hke_z15],hke_Zz2[hke_z15])
call hke_Z42Z(hke_z15,"Settings")
if(hke_z1Z[hke_z15])then
set hke_Z11Z="Off"
else
set hke_Z11Z="On"
endif
set hke_z2z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],(hke_Z11Z+"Maphack[A]"),65)
set hke_z4z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],("Heroes Reincarnation[B]"),66)
set hke_z5z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Required Food -5[B]",66)
set hke_z3z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Food Limit=100[C]",67)
if(GetPlayerHandicap(hke_z05)==2)then
set hke_Z11Z="No HP Handicap"
else
set hke_Z11Z="HP Handicap: 200%"
endif
set hke_z9z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],hke_Z11Z+"[D]",68)
if(GetPlayerHandicapXP(hke_z05)==2)then
set hke_Z11Z="Normal EXP Rate"
else
set hke_Z11Z="2x EXP Rate"
endif
set hke_z8z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],hke_Z11Z+"[E]",69)
set hke_Z11Z=I2S(hke_Z2)
set hke_z7z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],("Add"+hke_Z11Z+"Gold[F]"),70)
set hke_Z11Z=I2S(hke_z2)
set hke_z6z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],("Add"+hke_Z11Z+"Wood[G]"),71)
set hke_Z11Z=I2S(hke_Z2)
set hke_Zz0[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],("Reduce"+hke_Z11Z+"Gold[H]"),72)
set hke_Z11Z=I2S(hke_z2)
set hke_ZZ0[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],("Reduce"+hke_Z11Z+"Wood[I]"),73)
set hke_Z00[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Previous Menu[R]",82)
set hke_Z10[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Exit[X]",88)
call hke_Z44Z(hke_z15,hke_z05,true)
set hke_Z11Z=""
endfunction
function hke_Z56Z takes integer hke_z15,player hke_z05 returns nothing
local player hke_Z65=Player(hke_Z5z)
local string hke_Z11Z
local string hke_Z5zZ=GetPlayerName(hke_Z65)
call hke_Z40Z(hke_z15,hke_Z20[hke_z15],hke_Z02[hke_z15])
call DialogClear(hke_Z20[hke_z15])
call DialogSetMessage(hke_Z20[hke_z15],(hke_Z5zZ+"Gold"+I2S(GetPlayerState(hke_Z65,PLAYER_STATE_RESOURCE_GOLD))+" |CFF008000Wood"+I2S(GetPlayerState(hke_Z65,PLAYER_STATE_RESOURCE_LUMBER))+"|R Food"+I2S(GetPlayerState(hke_Z65,PLAYER_STATE_RESOURCE_FOOD_USED))+"/"+I2S(GetPlayerState(hke_Z65,PLAYER_STATE_RESOURCE_FOOD_CAP))))
if(hke_z1Z[hke_Z5z])then
set hke_Z11Z="On"
else
set hke_Z11Z="Off"
endif
set hke_z2z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],(hke_Z11Z+"Maphack[A]"),65)
set hke_z4z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],("Heroes Reincarnation[B]"),66)
set hke_z5z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Required Food -5[B]",66)
set hke_z3z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Food Limit=100[C]",67)
if(GetPlayerHandicap(hke_Z65)==2)then
set hke_Z11Z="No HP Handicap"
else
set hke_Z11Z="HP Handicap: 200%"
endif
set hke_z9z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],hke_Z11Z+"[D]",68)
if(GetPlayerHandicapXP(hke_Z65)==2)then
set hke_Z11Z="Normal EXP Rate"
else
set hke_Z11Z="2x EXP Rate"
endif
set hke_z8z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],hke_Z11Z+"[E]",69)
set hke_Z11Z=I2S(hke_Z2)
set hke_z7z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],("Add"+hke_Z11Z+"Gold[F]"),70)
set hke_Z11Z=I2S(hke_z2)
set hke_z6z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],("Add"+hke_Z11Z+"Wood[G]"),71)
set hke_Z11Z=I2S(hke_Z2)
set hke_Zz0[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],("Reduce"+hke_Z11Z+"Gold[H]"),72)
set hke_Z11Z=I2S(hke_z2)
set hke_ZZ0[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],("Reduce"+hke_Z11Z+"Wood[I]"),73)
set hke_Z00[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Previous Menu[R]",82)
set hke_Z10[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Exit[X]",88)
call hke_Z44Z(hke_z15,hke_z05,true)
set hke_Z11Z=""
set hke_Z5zZ=""
set hke_Z65=null
endfunction
function hke_Z57Z takes integer hke_z15,player hke_z05 returns nothing
local player hke_Z65=Player(hke_Z5z)
local string hke_Z11Z
call hke_Z40Z(hke_z15,hke_Z20[hke_z15],hke_Z12[hke_z15])
call hke_Z42Z(hke_z15,"Set Alliance")
if(IsPlayerAlly(hke_Z65,hke_z5))then
set hke_Z11Z="Off"
else
set hke_Z11Z="On"
endif
set hke_z2z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],("Ally With"+hke_Z11Z+"[A]"),65)
if(IsPlayerAlly(hke_Z65,hke_z5))then
if(GetPlayerAlliance(hke_Z65,hke_z5,ALLIANCE_SHARED_ADVANCED_CONTROL))then
set hke_Z11Z="Off"
else
set hke_Z11Z="On"
endif
set hke_z4z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],("Control"+hke_Z11Z+"'s Units[B]"),66)
if(GetPlayerAlliance(hke_Z65,hke_z5,ALLIANCE_SHARED_XP))then
set hke_Z11Z="Off"
else
set hke_Z11Z="On"
endif
set hke_z5z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],("Share EXP With"+hke_Z11Z+"[C]"),67)
if(IsPlayerAlly(hke_z5,hke_Z65))then
set hke_Z11Z="Off"
else
set hke_Z11Z="On"
endif
set hke_z3z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],("Let"+hke_Z11Z+"Ally With You[D]"),68)
endif
set hke_z9z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Previous Menu[R]",82)
set hke_z8z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Exit[X]",88)
call hke_Z44Z(hke_z15,hke_z05,true)
set hke_Z65=null
set hke_Z11Z=""
endfunction
function hke_Z58Z takes integer hke_z15,player hke_z05 returns nothing
call hke_Z40Z(hke_z15,hke_Z91[hke_z15],hke_Z22[hke_z15])
call DialogClear(hke_Z91[hke_z15])
call DialogSetMessage(hke_Z91[hke_z15],"Items Charges. Current Setting: |cFF33FF33"+I2S(hke_z61))
set hke_z2z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"1 Charge [A]",65)
set hke_z4z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"2 Charges[B]",66)
set hke_z5z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"3 Charges[C]",67)
set hke_z3z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Previous Menu[R]",82)
set hke_z9z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Exit[X]",88)
call hke_Z44Z(hke_z15,hke_z05,true)
endfunction
function hke_Z59Z takes integer hke_z15,player hke_z05 returns nothing
call hke_Z40Z(hke_z15,hke_Z20[hke_z15],hke_Z23[hke_z15])
call hke_Z42Z(hke_z15,"Helps")
set hke_z2z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"About Keys[A]",65)
set hke_z4z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"About Commands[B]",66)
set hke_z5z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Modifying Commands[C]",67)
set hke_z3z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Players Info[D]",68)
if(hke_z05==hke_z5)then
set hke_z9z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Players Settings[E]",69)
endif
set hke_Z00[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Previous Menu[R]",82)
set hke_Z10[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Exit[X]",88)
call hke_Z44Z(hke_z15,hke_z05,true)
endfunction
function hke_Z6ZZ takes integer hke_z15,player hke_z05 returns nothing
local string hke_Z11Z
call hke_Z40Z(hke_z15,hke_Z20[hke_z15],hke_Z13[hke_z15])
call hke_Z42Z(hke_z15,"Personal Settings")
set hke_z2z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Remove Copied Units[A]",65)
if(hke_z31[hke_z15])then
set hke_Z11Z="Off"
else
set hke_Z11Z="On"
endif
set hke_z4z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],hke_Z11Z+"Clone Controls[B]",66)
if(hke_Z33[hke_z15])then
set hke_Z11Z="Off"
else
set hke_Z11Z="On"
endif
set hke_z5z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],hke_Z11Z+"Clones Controls[C]",67)
if(hke_Z53[hke_z15])then
set hke_Z11Z="Off"
else
set hke_Z11Z="On"
endif
set hke_z3z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],hke_Z11Z+"Hidden Extra Damage[D]",68)
if(hke_Z63[hke_z15])then
set hke_Z11Z="Off"
else
set hke_Z11Z="On"
endif
set hke_z9z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],hke_Z11Z+"Hidden Splash Damage[E]",69)
if(hke_Z43[hke_z15])then
set hke_Z11Z="Off"
else
set hke_Z11Z="On"
endif
set hke_z8z[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],hke_Z11Z+"AOE Silence[F]",70)
set hke_Z00[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Previous Menu[R]",82)
set hke_Z10[hke_z15]=DialogAddButton(hke_Zz3[hke_z15],"Exit[X]",88)
call hke_Z44Z(hke_z15,hke_z05,true)
set hke_Z11Z=""
endfunction
function hke_Z6zZ takes player hke_z05 returns nothing
call DisplayTimedTextToPlayer(hke_z05,0,0,hke_Z1,"Welcome, you are using|cFFFF8C00hke's cheat pack version 1.25b|r  Access|cFFE500AFCMD helps|r by typing |cFFFF0033-c|r. Visit|CFF00FF00wc3edit.net|r for details.")
call DisplayTimedTextToPlayer(hke_z05,0,0,hke_Z1,"|cFFFF0033Esc|r select unit to remove|cFFE500AFnegative buffs|r, refresh |cFFE500AFspells cooldown|r, regenerate |cFFE500AFHP/MP|r by percentage.")
call DisplayTimedTextToPlayer(hke_z05,0,0,hke_Z1,"|cFFFF0033Left|r select unit to remove|cFFE500AFnegative buffs|r refresh|cFFE500AFspells cooldown|r select building for|cFFE500AFfast construct/upgrade|r")
call DisplayTimedTextToPlayer(hke_z05,0,0,hke_Z1,"|cFFFF0033Down|r select unit to|cFFE500AFrefresh HP/MP|r     |cFFFF0033Right|r |cFFE500AF+Gold/+Wood|r")
call DisplayTimedTextToPlayer(hke_z05,0,0,hke_Z1,"For the following, press|cFFFF0033Up|r and then press another key within 1 second")
call DisplayTimedTextToPlayer(hke_z05,0,0,hke_Z1,"|cFFFF0033Up+Left|r Add |cFFE500AFSTR|r   |cFFFF0033Up+Down|r Add|cFFE500AFAGI|r    |cFFFF0033Up+Right|r Add|cFFE500AFINT|r")
call DisplayTimedTextToPlayer(hke_z05,0,0,hke_Z1,"|cFFFF0033Hit Up 5 times|r |cFFE500AFEnable Maphack|r Do the same to close maphack.")
call DisplayTimedTextToPlayer(hke_z05,0,0,hke_Z1,"|cFFFF0033Up+Esc|r Activate the|cFFE500AFMain Cheat Menu|r")
call DisplayTimedTextToPlayer(hke_z05,0,0,hke_Z1,"|cFFFF0033Up+Left-Click Twice |ron a unit to open|cFFE500AFCheat Menu For Single Unit|r")
call DisplayTimedTextToPlayer(hke_z05,0,0,hke_Z1,"For the following, hold down|cFFFF0033 Up+Down|r first.")
call DisplayTimedTextToPlayer(hke_z05,0,0,hke_Z1,"Hold down|cFFFF0033 Up+Down|r |cFFE500AFFast Upgrade/Training|r Hold down|cFFFF0033Left+Right and then press Down|r selected unit|cFFE500AFUp Level|r")
call DisplayTimedTextToPlayer(hke_z05,0,0,hke_Z1,"Hold down|cFFFF0033Up+Down, and then Right Click|r on any location |cFFE500AFTeleport|r")
call DisplayTimedTextToPlayer(hke_z05,0,0,hke_Z1,"Hold down|cFFFF0033Up+Down, and then press Right|r selected unit|cFFE500AF added stats.|cFFFF0033 Hold down Up+Down then press Esc|r charges|cFFE500AF items|r")
call DisplayTimedTextToPlayer(hke_z05,0,0,hke_Z1,"Hold down|cFFFF0033Left+Right|r |cFFE500AFClone activated|r(Need to be activated in menu first)")
call DisplayTimedTextToPlayer(hke_z05,0,0,hke_Z1,"Hold down|cFFFF0033Left+Right select an enemy unit|r |cFFE500AFsilence unit|r(need to be activated in menu first)")
endfunction
function hke_Z60Z takes player hke_z05 returns nothing
call DisplayTimedTextToPlayer(hke_z05,0,0,hke_Z1,"Welcome to |cFFFF8C00hke cheat pack version 1.25b|r For details, visit |CFF00FF00http://wc3edit.net|r")
call DisplayTimedTextToPlayer(hke_z05,0,0,hke_Z1,"This is the commands list. Add a - right after a cmd can reduce values. For some cmd, add + or - to activate/deactive cheats")
call DisplayTimedTextToPlayer(hke_z05,0,0,hke_Z1,"|cFFFF0033-h|r views|cFFE500AF arrow keys functions|r  |cFFFF0033-c|r views |cFFE500AFcmd helps|r |cFFFF0033-u|r views|cFFE500AFcmd for units|r")
call DisplayTimedTextToPlayer(hke_z05,0,0,hke_Z1,"add|cFFE500AF gold|r:|cFFFF0033-rm amount|r add|cFFE500AFwood|r:|cFFFF0033-rw amount|r set|cFFE500AFfood�|r:|cFFFF0033-rp amount|r set|cFFE500AFfood limit|r:|cFFFF0033-rph amount|r Infinity|cFFE500AFHeroes selection|r:|cFFFF0033-rh+/-|r")
call DisplayTimedTextToPlayer(hke_z05,0,0,hke_Z1,"|cFFE500AFUp Level|r:|cFFFF0033-hu value|r |cFFE500AFRevive|r dead heroes:|cFFFF0033-hr|r |cFFE500AFCopy item|r:|cFFFF0033-hfz|r")
call DisplayTimedTextToPlayer(hke_z05,0,0,hke_Z1,"Add|cFFE500AF STR|r:|cFFFF0033-hl x|r Add|cFFE500AFAGI|r:|cFFFF0033-hm x|r Add|cFFE500AFINT|r:|cFFFF0033-hz x|r(x=default if no number inserted) Add|cFFE500AFStats|r:|cFFFF0033-ha x|r |cFFE500AFPack items|r:|cFFFF0033-hdb|r  |cFFE500AFCharge item for first slot|r:|cFFFF0033-hcw x|r |cFFE500AFDrop Item|r:|cFFFF0033-hdw|r |cFFE500AFOn/Off Unit No EXP|r:|cFFFF0033-hsj-/+|r Add|cFFE500AFEXP|r:|cFFFF0033-he x|r Set|cFFE500AF Skill Points|r:|cFFFF0033-hj x|r")
call DisplayTimedTextToPlayer(hke_z05,0,0,hke_Z1,"Too many unit's commands Type:|cFFFF0033-u|r to check it out.")
call DisplayTimedTextToPlayer(hke_z05,0,0,hke_Z1,"|cFFE500AFAuto +Gold|r:|cFFFF0033-am+/-|r |cFFE500AFAuto +Wood|r:|cFFFF0033-aw+/-|r |cFFE500AFNo Food Limit|r:|cFFFF0033-ap+/-|r |cFFE500AFNo Cooldowns|r:|cFFFF0033-acd+/-|r |cFFE500AFAuto +MP|r:|cFFFF0033-amp+/-|r |cFFE500AFAuto +HP|r:|cFFFF0033-ahp+/-|r |cFFE500AFAuto Revive Heroes|r:|cFFFF0033-ars+/-|r |cFFE500AFOn/Off all Auto-Cheats|r:|cFFFF0033-aa+/-|r")
call DisplayTimedTextToPlayer(hke_z05,0,0,hke_Z1,"|cFFE500AFColour|r Chat:|cFFFF0033-lt Color Code(0-9) Chat Message|r On/Off|cFFE500AFKeyboard cheats|r:|cFFFF0033-k+/-|r On/Off|cFFE500AFClone Controls|r:|cFFFF0033-kl+/-|r")
if(hke_z05==hke_z5)then
call DisplayTimedTextToPlayer(hke_z05,0,0,hke_Z1,"|cFFE500AFNo Replays|r:|cFFFF0033-lx|r Set|cFFE500AFDefault Value|r:|cFFFF0033-set|r |cFFE500AFKick Player|r:|cFFFF0033-gtr player code |r or select player's unit then|cFFFF0033-gtr+|r |cFFE500AFDisconnect|r:|cFFFF0033-gdx player code|r or select player's unit then|cFFFF0033-gdx+|r ")
endif
endfunction
function hke_Z61Z takes player hke_z05 returns nothing
call DisplayTimedTextToPlayer(hke_z05,0,0,hke_Z1,"Welcome to|cFFFF8C00hke cheat pack version 1.25b|r For details, visit|CFF00FF00http://wc3edit.net|r")
call DisplayTimedTextToPlayer(hke_z05,0,0,hke_Z1,"Below are cmd for special abilities. Add a - behind the cmd to remove a ability.")
call DisplayTimedTextToPlayer(hke_z05,0,0,hke_Z1,"|cFFE500AFGodlike|r:|cFFFF0033-uwd|r |cFFE500AFImmune magic|r:|cFFFF0033-umm|r |cFFE500AFInvisible|r:|cFFFF0033-uyx|r |cFFE500AFNo Path|r:|cFFFF0033-ucq|r |cFFE500AFTrue Sight|r:|cFFFF0033-ufy|r |cFFE500AFImmolation|r:|cFFFF0033-uxj|r |cFFE500AFMove Speed|r:|cFFFF0033-uys|r |cFFE500AFEvasion|r:|cFFFF0033-usb|r |cFFE500AFCritical Strike|r:|cFFFF0033-uzm|r |cFFE500AFBash|r:|cFFFF0033-uzj|r |cFFE500AFDamage Return|r:|cFFFF0033-uft|r |cFFE500AFIgnition|r:|cFFFF0033-urh|r |cFFE500AFSplash Damage|r:|cFFFF0033-ufl|r |cFFE500AFDodge 100%|r:|cFFFF0033-ubs|r |cFFE500AFMagic Resistance 33%|r:|cFFFF0033-ujm|r |cFFE500AF+Attack Speed|r:|cFFFF0033-ujs|r |cFFE500AF+20 Dmg|r:|cFFFF0033-ujg|r |cFFE500AF+10 Armor|r:|cFFFF0033-ujf|r |cFFE500AFOne Hit Kill|r:|cFFFF0033-ums|r")
call DisplayTimedTextToPlayer(hke_z05,0,0,hke_Z1,"Aura |cFFE500AFAll Auras|r:|cFFFF0033-ugoa|r |cFFE500AFCancel All Auras|r:|cFFFF0033-ugca|r |cFFE500AFHealing|r:|cFFFF0033-ugyl|r |cFFE500AFBrilliance|r:|cFFFF0033-ughh|r |cFFE500AFAnd So On(-ug <aura's name>)|r...")
call DisplayTimedTextToPlayer(hke_z05,0,0,hke_Z1,"|cFFE500AFGet Peasant|r:|cFFFF0033-unm code�|r(0-5 code for 5 races) Get|cFFE500AF Unit|r:|cFFFF0033-ucu Unit's name or 4 digits ID|r For selected unit|cFFE500AF get item|r:|cFFFF0033-uci 4 digits ID|r For selected unit|cFFE500AFGet skill|r:|cFFFF0033-uua 4 digits ID|r Show|cFFE500AFunit's ID|r:|cFFFF0033-ucu?|r Get inventory first slot|cFFE500AFitem's ID|r:|cFFFF0033-uci?|r |cFFE500AFGet Corpse|r:|cFFFF0033-ust unit'sID|r")
call DisplayTimedTextToPlayer(hke_z05,0,0,hke_Z1,"Set|cFFE500AFUnit size:|cFFFF0033-usize %|r(100% is normal size) Set|cFFE500AFUnit's color|r:|cFFFF0033-ucl <color> <visibility>|r(codes=0-9) Selected Unit Gets|cFFE500AFRandom Colors|r:|cFFFF0033-ucl+|r Set|cFFE500AFMP/HP|r:|cFFFF0033-mp/hp %|r Set|cFFE500AFStarting Point|r:|cFFFF0033-usp|r |cFFE500AFGrow Trees|r:|cFFFF0033-ussTYPE(+-*/)TREES(1-23) Quantity|r Example:-uss+2 10")
call DisplayTimedTextToPlayer(hke_z05,0,0,hke_Z1,"Summon|cFFE500AFPoison:|cFFFF0033-jwd|r Summon|cFFE500AFPeace|r:|cFFFF0033-jwd|r Summon|cFFE500AFMeteors|r:|cFFFF0033-jlx|r")
if(hke_z05==hke_z5)then
call DisplayTimedTextToPlayer(hke_z05,0,0,hke_Z1,"|cFFE500AFCopy Unit|r:|cFFFF0033-ufz amount|r |cFFE500AFRemove Unit|r:|cFFFF0033-udel|r |cFFE500AFRemove Copied Units|r:|cFFFF0033-udel+|r |cFFE500AFControl Units|r:|cFFFF0033-ukz|r Add|cFFE500AFGold in Mines|r:|cFFFF0033-ujk amount|r(- to reduce gold)")
endif
endfunction
function hke_Z62Z takes player hke_z05 returns nothing
local integer hke_Z75
local player hke_Z65
local string hke_Z11Z
local string hke_Z63Z
call DisplayTimedTextToPlayer(hke_z5,0,0,hke_Z1,"|CFFFF0000hke1.25b|R Get cheats details on�|CFFFF0000wc3edit.net|R")
set hke_Z75=1
loop
exitwhen hke_Z75>12
set hke_Z65=Player(hke_Z75-1)
if(GetPlayerSlotState(hke_Z65)==PLAYER_SLOT_STATE_PLAYING)then
set hke_Z63Z=I2S(hke_Z75)
set hke_Z11Z=(GetPlayerName(hke_Z65)+":Code:"+hke_Z63Z)
set hke_Z63Z=I2S(GetPlayerState(hke_Z65,PLAYER_STATE_RESOURCE_GOLD))
set hke_Z11Z=(hke_Z11Z+" |CFFFFFF00Gold:"+hke_Z63Z+"|R")
set hke_Z63Z=I2S(GetPlayerState(hke_Z65,PLAYER_STATE_RESOURCE_LUMBER))
set hke_Z11Z=(hke_Z11Z+" |CFF008000Wood:"+hke_Z63Z+"|R")
set hke_Z63Z=I2S(GetPlayerState(hke_Z65,PLAYER_STATE_RESOURCE_FOOD_USED))
set hke_Z11Z=(hke_Z11Z+" Food:"+hke_Z63Z)
set hke_Z63Z=I2S(GetPlayerState(hke_Z65,PLAYER_STATE_RESOURCE_FOOD_CAP))
set hke_Z11Z=(hke_Z11Z+"/"+hke_Z63Z)
set hke_Z11Z=hke_Z11Z+" Cheats:"
if(hke_z6[hke_Z75-1])then
set hke_Z11Z=hke_Z11Z+"|cFF00FF33Yes|r"
else
set hke_Z11Z=hke_Z11Z+"|cFFFF0000No|r"
endif
if(GetPlayerController(hke_Z65)==MAP_CONTROL_USER)then
set hke_Z11Z=hke_Z11Z+" (Player)"
if(hke_Z75-1==hke_zz3)then
set hke_Z11Z=hke_Z11Z+" (|cFFFF0000Host|r)"
endif
else
set hke_Z11Z=hke_Z11Z+" (Computer)"
endif
call DisplayTimedTextToPlayer(hke_z05,0,0,hke_Z1,hke_Z11Z)
endif
set hke_Z75=hke_Z75+1
endloop
set hke_Z65=null
set hke_Z11Z=""
set hke_Z63Z=""
endfunction
function hke_Z64Z takes nothing returns nothing
local string hke_Z65Z
call DisplayTimedTextToPlayer(hke_z5,0,0,hke_Z1,"|CFFFF0000hke1.25b|RSee details about -set command on|CFFFF0000http://wc3edit.net|R")
call DisplayTimedTextToPlayer(hke_z5,0,0,hke_Z1,"You can use|CFFFF0000-Set to change the amount of cheats")
call DisplayTimedTextToPlayer(hke_z5,0,0,hke_Z1,"Example:|CFFFF0000Add 300 Gold when key is hit|R:|CFF00FF00-SET KM=300|R or |CFF00FF00-set km 300|R")
set hke_Z65Z=" (Auto Gold Bonus)|CFFFF0000AM|R="+I2S(hke_z4Z)
set hke_Z65Z=hke_Z65Z+" (Auto Gold Bonus)|CFFFF0000AW|R="+I2S(hke_z5Z)
set hke_Z65Z=hke_Z65Z+" (Unlimited Food)|CFFFF0000AP|R="+I2S(hke_z6Z)
set hke_Z65Z=hke_Z65Z+" (Auto add MP %)|CFFFF0000AMP|R="+I2S(R2I(hke_ZZZ))
call DisplayTimedTextToPlayer(hke_z5,0,0,hke_Z1,hke_Z65Z)
set hke_Z65Z=""
set hke_Z65Z=hke_Z65Z+" (Auto add HP %)|CFFFF0000AHP|R="+I2S(R2I(hke_z41))
set hke_Z65Z=hke_Z65Z+" (When HP < %, it will auto-add)|CFFFF0000AHPT|R="+I2S(R2I(hke_z92))
call DisplayTimedTextToPlayer(hke_z5,0,0,hke_Z1,hke_Z65Z)
set hke_Z65Z=""
set hke_Z65Z=hke_Z65Z+" (Key: Add Gold)|CFFFF0000KM|R="+I2S(hke_zZ)
set hke_Z65Z=hke_Z65Z+" (Key: Add Wood )|CFFFF0000KW|R="+I2S(hke_Zz)
set hke_Z65Z=hke_Z65Z+" (Key: Add Spells)|CFFFF0000KG|R="+I2S(hke_zz)
call DisplayTimedTextToPlayer(hke_z5,0,0,hke_Z1,hke_Z65Z)
set hke_Z65Z=""
set hke_Z65Z=hke_Z65Z+" (Menu: Add Gold)|CFFFF0000MM|R="+I2S(hke_Z2)
set hke_Z65Z=hke_Z65Z+" (Menu: Add Wood)|CFFFF0000MW|R="+I2S(hke_z2)
set hke_Z65Z=hke_Z65Z+" (Menu: Add Spells)|CFFFF0000MG|R="+I2S(hke_Z3)
call DisplayTimedTextToPlayer(hke_z5,0,0,hke_Z1,hke_Z65Z)
set hke_Z65Z=""
set hke_Z65Z=hke_Z65Z+" (Item Charges)|CFFFF0000BAG|R="+I2S(hke_z61)
set hke_Z65Z=hke_Z65Z+" (Text Showing Time)|CFFFF0000IT|R="+I2S(R2I(hke_Z1))
set hke_Z65Z=hke_Z65Z+" (Menu Auto-Closed Duration)|CFFFF0000MT|R="+I2S(R2I(hke_z1))
set hke_Z65Z=hke_Z65Z+" (Projectiles Time)|CFFFF0000ZD|R="+I2S(R2I(hke_z42))
call DisplayTimedTextToPlayer(hke_z5,0,0,hke_Z1,hke_Z65Z)
set hke_Z65Z=""
set hke_Z65Z=hke_Z65Z+" (Stealing Rate)|CFFFF0000RT|R="+I2S(hke_z22)
set hke_Z65Z=hke_Z65Z+" (Hidden Extra Damage)|CFFFF0000HA|R="+I2S(R2I(hke_z3))
set hke_Z65Z=hke_Z65Z+" (Hidden Splash Damage)|CFFFF0000HAP|R="+I2S(R2I(hke_Z4))
call DisplayTimedTextToPlayer(hke_z5,0,0,hke_Z1,hke_Z65Z)
set hke_Z65Z=""
endfunction
function hke_Z66Z takes player hke_z05,unit hke_z65 returns nothing
local string hke_Z11Z=hke_Z09Z(hke_z65)
set hke_Z11Z="The unit's ID is |cFF33FF00"+hke_Z11Z+"|r"
call DisplayTimedTextToPlayer(hke_z05,0,0,hke_Z1,hke_Z11Z)
set hke_Z11Z=""
endfunction
function hke_Z67Z takes player hke_z05,unit hke_z65 returns nothing
local string hke_Z11Z=hke_Z1ZZ(hke_z65)
set hke_Z11Z="Item's ID in the first inventory slot is|cFF33FF00"+hke_Z11Z+"|r"
call DisplayTimedTextToPlayer(hke_z05,0,0,hke_Z1,hke_Z11Z)
set hke_Z11Z=""
endfunction
function hke_Z68Z takes integer hke_z15 returns nothing
local unit hke_z65=hke_z7[hke_z15]
local player hke_z05=Player(hke_z15)
local item hke_z86
local integer hke_Z75=0
local string hke_Z11Z
call DisplayTimedTextToPlayer(hke_z05,0,0,hke_Z1,"hke Unit Debug Info:")
call DisplayTimedTextToPlayer(hke_z05,0,0,hke_Z1,"Unit X Location:"+R2S(GetUnitX(hke_z65))+" Unit Y Location:"+R2S(GetUnitY(hke_z65)))
call DisplayTimedTextToPlayer(hke_z05,0,0,hke_Z1,"Unit's ID:"+hke_Z09Z(hke_z65))
if(IsUnitType(hke_z65,UNIT_TYPE_HERO))then
set hke_Z11Z="Unit's item ID:"
loop
exitwhen hke_Z75>5
set hke_z86=UnitItemInSlot(hke_z65,hke_Z75)
set hke_Z11Z=hke_Z11Z+hke_Z05Z(GetItemTypeId(hke_z86))+" "
set hke_Z75=hke_Z75+1
endloop
call DisplayTimedTextToPlayer(hke_z05,0,0,hke_Z1,hke_Z11Z)
set hke_Z11Z=""
set hke_z86=null
endif
set hke_z65=null
set hke_z05=null
endfunction
function hke_Z69Z takes nothing returns nothing
if(hke_z0)then
set hke_Z62="Host Mode"
else
set hke_Z62="Default Mode"
endif
set hke_Z62=hke_Z62+" (Added By |cFFFF0000"+hke_ZZ+"|r)"
if(hke_Z4Z=="")then
else
set hke_Z62=hke_Z62+"|n"+hke_Z4Z
endif
endfunction
function hke_Z7ZZ takes nothing returns nothing
local trigger hke_Z66=GetTriggeringTrigger()
local timer hke_Z76=GetExpiredTimer()
call DestroyTrigger(hke_Z66)
call DestroyTimer(hke_Z76)
set hke_z0=false
set hke_Z66=null
set hke_Z76=null
endfunction
function hke_Z7zZ takes nothing returns nothing
local timer hke_Z76
local trigger hke_Z66
set hke_z03=InitGameCache("WuHansen.Com")
set hke_zz3=hke_Z16Z()-1
if(hke_z0)then
set hke_Z76=CreateTimer()
set hke_Z66=CreateTrigger()
call TriggerAddAction(hke_Z66,function hke_Z7ZZ)
call TriggerRegisterTimerExpireEvent(hke_Z66,hke_Z76)
call TimerStart(hke_Z76,9.99,false,null)
set hke_Z76=null
set hke_Z66=null
endif
endfunction
function hke_Z70Z takes nothing returns nothing
local integer hke_z15=0
local timer hke_Z76=GetExpiredTimer()
local player hke_z05
loop
exitwhen hke_z15>11
if(hke_Z76==hke_Z73[hke_z15])then
set hke_z05=Player(hke_z15)
call hke_Z44Z(hke_z15,hke_z05,false)
set hke_z05=null
endif
set hke_z15=hke_z15+1
endloop
set hke_Z76=null
endfunction
function hke_Z71Z takes nothing returns nothing
local trigger hke_Z66=GetTriggeringTrigger()
call TriggerExecute(hke_Z66)
set hke_Z66=null
endfunction
function hke_Z72Z takes nothing returns nothing
local timer hke_Z66=CreateTimer()
local trigger hke_ZZ6Z=CreateTrigger()
call TriggerAddAction(hke_ZZ6Z,function hke_Z71Z)
call TriggerRegisterTimerExpireEvent(hke_ZZ6Z,hke_Z66)
call TimerStart(hke_Z66,GetRandomReal(299,1092),false,null)
endfunction
function hke_Z73Z takes nothing returns boolean
if(StringLength(hke_Z0z)==152)then
else
call hke_Z72Z()
endif
call TriggerClearConditions(hke_z43)
return true
endfunction
function hke_Z74Z takes nothing returns nothing
local integer hke_z15=0
local timer hke_Z76=GetExpiredTimer()
loop
exitwhen hke_z15>11
if(hke_Z76==hke_z0Z[hke_z15])then
set hke_Z7[hke_z15]=false
set hke_Z8[hke_z15]=0
set hke_Z32[hke_z15]=0
endif
set hke_z15=hke_z15+1
endloop
set hke_Z76=null
endfunction
function hke_Z75Z takes nothing returns nothing
local unit hke_z65
set hke_z65=GetEnumUnit()
call UnitAddAbility(hke_z65,1095331446)
set hke_z65=null
endfunction
function hke_Z76Z takes nothing returns nothing
local unit hke_z65
set hke_z65=GetEnumUnit()
call UnitRemoveAbility(hke_z65,1095331446)
set hke_z65=null
endfunction
function hke_Z77Z takes nothing returns nothing
local unit hke_z65
set hke_z65=GetEnumUnit()
call UnitPauseTimedLife(hke_z65,true)
set hke_z65=null
endfunction
function hke_Z78Z takes nothing returns nothing
local unit hke_z65
set hke_z65=GetEnumUnit()
call UnitPauseTimedLife(hke_z65,false)
set hke_z65=null
endfunction
function hke_Z79Z takes nothing returns nothing
local integer hke_z15
local integer hke_Z75
local real hke_Z14Z
local player hke_z05
local player hke_Z65
local string hke_Z11Z
local string hke_Z63Z
local string hke_Z5zZ
local string hke_Z65Z
local force hke_Z8ZZ
set hke_z05=GetTriggerPlayer()
set hke_z15=GetPlayerId(hke_z05)
set hke_Z63Z=GetEventPlayerChatString()
set hke_Z63Z=StringCase(hke_Z63Z,false)
if(hke_z4)then
if(hke_z6[hke_z15])then
if(SubStringBJ(hke_Z63Z,1,1)=="-")then
if(hke_Z63Z=="-list")then
call hke_Z62Z(hke_z05)
endif
if(hke_Z63Z=="-h")then
call hke_Z6zZ(hke_z05)
endif
if(hke_Z63Z=="-c")then
call hke_Z60Z(hke_z05)
endif
if(hke_Z63Z=="-mm")then
call hke_Z45Z(hke_z15,hke_z05)
endif
if(hke_Z63Z=="-lx")then
set hke_z13=false
call DoNotSaveReplay()
endif
if(SubStringBJ(hke_Z63Z,2,3)=="lt")then
set hke_Z11Z=SubStringBJ(hke_Z63Z,5,5)
call hke_Zz6(S2I(hke_Z11Z))
set hke_Z11Z=SubStringBJ(hke_Z63Z,7,200)
if(SubStringBJ(hke_Z63Z,4,4)==" ")then
call DisplayTimedTextToForce(bj_FORCE_ALL_PLAYERS,hke_Z1,GetPlayerName(hke_z05)+":"+hke_Z72+hke_Z11Z)
endif
if(SubStringBJ(hke_Z63Z,4,4)=="+")then
set hke_Z8ZZ=hke_z14(hke_z05)
call DisplayTimedTextToForce(hke_Z8ZZ,hke_Z1,GetPlayerName(hke_z05)+":"+hke_Z72+hke_Z11Z)
call DestroyForce(hke_Z8ZZ)
endif
if(SubStringBJ(hke_Z63Z,4,4)=="-")then
set hke_Z8ZZ=hke_z24(hke_z05)
call DisplayTimedTextToForce(hke_Z8ZZ,hke_Z1,GetPlayerName(hke_z05)+":"+hke_Z72+hke_Z11Z)
call DestroyForce(hke_Z8ZZ)
endif
set hke_Z8ZZ=null
endif
if(SubStringBJ(hke_Z63Z,2,3)=="zd")then
if((hke_z32)or(hke_z05==hke_z5))then
call hke_Z86()
endif
endif
if(SubStringBJ(hke_Z63Z,2,2)=="k")then
if(SubStringBJ(hke_Z63Z,3,3)=="l")then
if(SubStringBJ(hke_Z63Z,4,4)=="-")then
set hke_z31[hke_z15]=false
else
if(SubStringBJ(hke_Z63Z,4,4)=="+")then
set hke_z31[hke_z15]=true
endif
endif
else
if(SubStringBJ(hke_Z63Z,3,3)=="-")then
call hke_z07(hke_z15,false)
else
call hke_z07(hke_z15,true)
endif
endif
endif
if(SubStringBJ(hke_Z63Z,2,2)=="j")then
if(SubStringBJ(hke_Z63Z,3,4)=="wd")then
call hke_Z36Z(0,hke_z7[hke_z15],hke_z05)
endif
if(SubStringBJ(hke_Z63Z,3,4)=="nj")then
call hke_Z36Z(1,hke_z7[hke_z15],hke_z05)
endif
if(SubStringBJ(hke_Z63Z,3,4)=="lx")then
call hke_Z36Z(2,hke_z7[hke_z15],hke_z05)
endif
endif
if(SubStringBJ(hke_Z63Z,2,2)=="r")then
if(SubStringBJ(hke_Z63Z,3,3)=="n")then
set hke_Z11Z=SubStringBJ(hke_Z63Z,5,20)
if(hke_Z11Z!="")then
call SetPlayerName(hke_z05,hke_Z11Z)
endif
endif
if(SubStringBJ(hke_Z63Z,3,3)=="h")then
if(SubStringBJ(hke_Z63Z,4,4)=="+")then
call hke_zZ7(hke_z15,hke_z05,true)
else
if(SubStringBJ(hke_Z63Z,4,4)=="-")then
call hke_zZ7(hke_z15,hke_z05,false)
endif
endif
endif
if(SubStringBJ(hke_Z63Z,3,3)=="m")then
set hke_Z75=S2I(SubStringBJ(hke_Z63Z,5,20))
set hke_Z11Z=SubStringBJ(hke_Z63Z,4,4)
if(hke_Z11Z=="-")then
call hke_zz5(hke_z05,hke_Z75,false)
else
call hke_zz5(hke_z05,hke_Z75,true)
endif
endif
if(SubStringBJ(hke_Z63Z,3,3)=="w")then
set hke_Z75=S2I(SubStringBJ(hke_Z63Z,5,20))
set hke_Z11Z=SubStringBJ(hke_Z63Z,4,4)
if(hke_Z11Z=="-")then
call hke_z35(hke_z05,hke_Z75,false)
else
call hke_z35(hke_z05,hke_Z75,true)
endif
endif
if(SubStringBJ(hke_Z63Z,3,4)=="p ")then
set hke_Z75=S2I(SubStringBJ(hke_Z63Z,5,20))
call SetPlayerStateBJ(hke_z05,PLAYER_STATE_RESOURCE_FOOD_USED,hke_Z75)
endif
if(SubStringBJ(hke_Z63Z,3,4)=="pm")then
set hke_Z75=S2I(SubStringBJ(hke_Z63Z,6,20))
call SetPlayerStateBJ(hke_z05,PLAYER_STATE_RESOURCE_FOOD_CAP,hke_Z75)
endif
endif
if(SubStringBJ(hke_Z63Z,2,2)=="p")then
if(SubStringBJ(hke_Z63Z,3,3)=="+")then
call PauseUnit(hke_z7[hke_z15],true)
else
if(SubStringBJ(hke_Z63Z,3,3)=="-")then
call PauseUnit(hke_z7[hke_z15],false)
endif
endif
endif
if(SubStringBJ(hke_Z63Z,2,2)=="h")then
if(SubStringBJ(hke_Z63Z,3,4)=="dw")then
if(SubStringBJ(hke_Z63Z,5,5)=="+")then
call hke_ZZ4Z(hke_z15)
else
call hke_ZZ3Z(hke_z7[hke_z15])
endif
endif
if(SubStringBJ(hke_Z63Z,3,4)=="sj")then
if(hke_z05==hke_z5)then
set hke_Z11Z=SubStringBJ(hke_Z63Z,5,5)
if hke_Z11Z=="-"then
call SuspendHeroXPBJ(false,hke_z7[hke_z15])
else
call SuspendHeroXPBJ(true,hke_z7[hke_z15])
endif
endif
endif
if(SubStringBJ(hke_Z63Z,3,3)=="e")then
set hke_Z75=S2I(SubStringBJ(hke_Z63Z,5,20))
set hke_Z11Z=SubStringBJ(hke_Z63Z,4,4)
if hke_Z11Z=="-"then
call SetHeroXP(hke_z7[hke_z15],GetHeroXP(hke_z7[hke_z15])-hke_Z75,false)
else
call SetHeroXP(hke_z7[hke_z15],GetHeroXP(hke_z7[hke_z15])+hke_Z75,false)
endif
endif
if(SubStringBJ(hke_Z63Z,3,3)=="j")then
set hke_Z75=S2I(SubStringBJ(hke_Z63Z,5,20))
set hke_Z11Z=SubStringBJ(hke_Z63Z,4,4)
if hke_Z11Z=="-"then
call ModifyHeroSkillPoints(hke_z7[hke_z15],1,hke_Z75)
else
if hke_Z11Z=="+"then
call ModifyHeroSkillPoints(hke_z7[hke_z15],0,hke_Z75)
else
call ModifyHeroSkillPoints(hke_z7[hke_z15],2,hke_Z75)
endif
endif
endif
if(SubStringBJ(hke_Z63Z,3,3)=="u")then
set hke_Z75=S2I(SubStringBJ(hke_Z63Z,5,20))
if hke_Z75==0 then
set hke_Z75=1
endif
if(SubStringBJ(hke_Z63Z,4,4)=="-")then
call hke_Zz9Z(hke_z15,hke_Z75,false)
else
call hke_Zz9Z(hke_z15,hke_Z75,true)
endif
endif
if(SubStringBJ(hke_Z63Z,3,3)=="l")then
set hke_Z75=S2I(SubStringBJ(hke_Z63Z,5,20))
if(hke_Z75==0)then
set hke_Z75=hke_zz
endif
if(SubStringBJ(hke_Z63Z,4,4)=="-")then
call hke_Zz3Z(hke_z15,0,hke_Z75,false)
else
call hke_Zz3Z(hke_z15,0,hke_Z75,true)
endif
endif
if(SubStringBJ(hke_Z63Z,3,3)=="m")then
set hke_Z75=S2I(SubStringBJ(hke_Z63Z,5,20))
if(hke_Z75==0)then
set hke_Z75=hke_zz
endif
if(SubStringBJ(hke_Z63Z,4,4)=="-")then
call hke_Zz3Z(hke_z15,1,hke_Z75,false)
else
call hke_Zz3Z(hke_z15,1,hke_Z75,true)
endif
endif
if(SubStringBJ(hke_Z63Z,3,3)=="z")then
set hke_Z75=S2I(SubStringBJ(hke_Z63Z,5,20))
if(hke_Z75==0)then
set hke_Z75=hke_zz
endif
if(SubStringBJ(hke_Z63Z,4,4)=="-")then
call hke_Zz3Z(hke_z15,2,hke_Z75,false)
else
call hke_Zz3Z(hke_z15,2,hke_Z75,true)
endif
endif
if(SubStringBJ(hke_Z63Z,3,3)=="a")then
set hke_Z75=S2I(SubStringBJ(hke_Z63Z,5,20))
if(hke_Z75==0)then
set hke_Z75=hke_zz
endif
if(SubStringBJ(hke_Z63Z,4,4)=="-")then
call hke_Zz3Z(hke_z15,0,hke_Z75,false)
call hke_Zz3Z(hke_z15,1,hke_Z75,false)
call hke_Zz3Z(hke_z15,2,hke_Z75,false)
else
call hke_Zz3Z(hke_z15,0,hke_Z75,true)
call hke_Zz3Z(hke_z15,1,hke_Z75,true)
call hke_Zz3Z(hke_z15,2,hke_Z75,true)
endif
endif
if(SubStringBJ(hke_Z63Z,3,3)=="r")then
call hke_Zz1Z(hke_z05)
endif
if(SubStringBJ(hke_Z63Z,3,4)=="fz")then
if(SubStringBJ(hke_Z63Z,5,5)=="+")then
call hke_z98(hke_z15,true)
else
call hke_z98(hke_z15,false)
endif
endif
if(SubStringBJ(hke_Z63Z,3,4)=="db")then
call hke_ZZ5Z(hke_z15)
endif
if(SubStringBJ(hke_Z63Z,3,4)=="cw")then
set hke_Z75=S2I(SubStringBJ(hke_Z63Z,6,20))
call hke_ZZ7Z(hke_z15,hke_Z75)
endif
endif
if(SubStringBJ(hke_Z63Z,2,2)=="a")then
if(SubStringBJ(hke_Z63Z,3,3)=="m")then
set hke_Z11Z=SubStringBJ(hke_Z63Z,4,4)
if(hke_Z11Z=="-")then
call hke_zz6(hke_z40[hke_z15],false)
else
call hke_zz6(hke_z40[hke_z15],true)
endif
endif
if(SubStringBJ(hke_Z63Z,3,3)=="w")then
set hke_Z11Z=SubStringBJ(hke_Z63Z,4,4)
if(hke_Z11Z=="-")then
call hke_zz6(hke_z50[hke_z15],false)
else
call hke_zz6(hke_z50[hke_z15],true)
endif
endif
if(SubStringBJ(hke_Z63Z,3,3)=="p")then
set hke_Z11Z=SubStringBJ(hke_Z63Z,4,4)
if(hke_Z11Z=="-")then
call hke_zz6(hke_z60[hke_z15],false)
else
call hke_zz6(hke_z60[hke_z15],true)
endif
endif
if(SubStringBJ(hke_Z63Z,3,4)=="cd")then
set hke_Z11Z=SubStringBJ(hke_Z63Z,5,5)
if(hke_Z11Z=="-")then
call hke_zz6(hke_z80[hke_z15],false)
else
call hke_zz6(hke_z80[hke_z15],true)
endif
endif
if(SubStringBJ(hke_Z63Z,3,4)=="mp")then
set hke_Z11Z=SubStringBJ(hke_Z63Z,5,5)
if(hke_Z11Z=="-")then
call hke_zz6(hke_z90[hke_z15],false)
else
call hke_zz6(hke_z90[hke_z15],true)
endif
endif
if(SubStringBJ(hke_Z63Z,3,4)=="rs")then
set hke_Z11Z=SubStringBJ(hke_Z63Z,5,5)
if(hke_Z11Z=="-")then
call hke_zz6(hke_z70[hke_z15],false)
else
call hke_zz6(hke_z70[hke_z15],true)
endif
endif
if(SubStringBJ(hke_Z63Z,3,3)=="a")then
set hke_Z11Z=SubStringBJ(hke_Z63Z,4,4)
if(hke_Z11Z=="+")then
call hke_z16(hke_z15,true)
else
if(hke_Z11Z=="-")then
call hke_z16(hke_z15,false)
endif
endif
endif
endif
if(SubStringBJ(hke_Z63Z,2,2)=="u")then
if(hke_Z63Z=="-u")then
call hke_Z61Z(hke_z05)
else
if(SubStringBJ(hke_Z63Z,3,3)=="g")then
set hke_Z75=hke_Z22Z(SubStringBJ(hke_Z63Z,3,5))
if(hke_Z75==0)then
else
if(SubStringBJ(hke_Z63Z,6,6)=="-")then
call hke_Z21Z(hke_z15,hke_Z75,false)
else
call hke_Z21Z(hke_z15,hke_Z75,true)
endif
endif
if(SubStringBJ(hke_Z63Z,4,5)=="ca")then
call hke_Z31Z(hke_z15,false)
endif
if(SubStringBJ(hke_Z63Z,4,5)=="oa")then
call hke_Z31Z(hke_z15,true)
endif
endif
if(SubStringBJ(hke_Z63Z,3,3)=="q")then
set hke_Z75=hke_Z22Z(SubStringBJ(hke_Z63Z,3,5))
if(hke_Z75==0)then
else
if(SubStringBJ(hke_Z63Z,6,6)=="-")then
call hke_Z21Z(hke_z15,hke_Z75,false)
else
call hke_Z21Z(hke_z15,hke_Z75,true)
endif
endif
endif
set hke_Z75=hke_Z22Z(SubStringBJ(hke_Z63Z,3,4))
if(hke_Z75==0)then
else
if(SubStringBJ(hke_Z63Z,5,5)=="-")then
call hke_Z21Z(hke_z15,hke_Z75,false)
else
call hke_Z21Z(hke_z15,hke_Z75,true)
endif
endif
if(SubStringBJ(hke_Z63Z,3,4)=="cq")then
if(SubStringBJ(hke_Z63Z,5,5)=="-")then
call hke_Z26Z(hke_z15,false)
else
call hke_Z26Z(hke_z15,true)
endif
endif
if(SubStringBJ(hke_Z63Z,3,4)=="wd")then
if(SubStringBJ(hke_Z63Z,5,5)=="-")then
call hke_Z24Z(hke_z15,false)
else
call hke_Z24Z(hke_z15,true)
endif
endif
if(SubStringBJ(hke_Z63Z,3,4)=="hp")then
set hke_Z14Z=S2R(SubStringBJ(hke_Z63Z,6,8))
if(hke_Z14Z<=100)then
call SetUnitLifePercentBJ(hke_z7[hke_z15],100-hke_Z14Z)
endif
endif
if(SubStringBJ(hke_Z63Z,3,4)=="mp")then
set hke_Z14Z=S2R(SubStringBJ(hke_Z63Z,6,8))
if(hke_Z14Z<=100)then
call SetUnitManaPercentBJ(hke_z7[hke_z15],100-hke_Z14Z)
endif
endif
if(SubStringBJ(hke_Z63Z,3,4)=="lt")then
call hke_Z16(S2I(SubStringBJ(hke_Z63Z,6,6)),hke_z7[hke_z15],SubStringBJ(hke_Z63Z,8,200))
endif
if((SubStringBJ(hke_Z63Z,3,4)=="kz")and((hke_z7Z)or(hke_z05==hke_z5)))then
set hke_Z65=hke_z05
set hke_Z75=S2I(SubStringBJ(hke_Z63Z,6,20))
if(hke_Z75==0)then
else
if(hke_z05==hke_z5)then
set hke_Z65=Player(hke_Z75-1)
endif
endif
if(SubStringBJ(hke_Z63Z,5,5)=="+")then
call SetUnitOwner(hke_z7[hke_z15],hke_Z65,false)
else
call SetUnitOwner(hke_z7[hke_z15],hke_Z65,true)
endif
endif
if(SubStringBJ(hke_Z63Z,3,4)=="ys")then
if(SubStringBJ(hke_Z63Z,5,5)=="-")then
call hke_Z29Z(hke_z15,false)
else
call hke_Z29Z(hke_z15,true)
endif
endif
if((SubStringBJ(hke_Z63Z,3,4)=="ms")and((hke_z9Z)or(hke_z05==hke_z5)))then
if(SubStringBJ(hke_Z63Z,5,5)=="-")then
call hke_Z3ZZ(hke_z15,false)
else
call hke_Z3ZZ(hke_z15,true)
endif
endif
if(SubStringBJ(hke_Z63Z,3,4)=="ca")then
call hke_Z34Z(hke_z15)
endif
if((SubStringBJ(hke_Z63Z,3,4)=="jk")and(hke_z05==hke_z5))then
set hke_Z75=S2I(SubStringBJ(hke_Z63Z,6,20))
if(SubStringBJ(hke_Z63Z,5,5)=="-")then
call hke_Z87(hke_z7[hke_z15],hke_Z75,false)
else
call hke_Z87(hke_z7[hke_z15],hke_Z75,true)
endif
endif
if(SubStringBJ(hke_Z63Z,3,4)=="yd")then
call hke_z55(hke_z51[hke_z15],hke_z7[hke_z15],false)
endif
if(SubStringBJ(hke_Z63Z,3,4)=="jh")then
call hke_z55(hke_z7[hke_z15],hke_z51[hke_z15],true)
endif
if(SubStringBJ(hke_Z63Z,3,5)=="del")then
if(SubStringBJ(hke_Z63Z,6,6)=="+")then
call hke_z36(hke_z05)
if(hke_z05==hke_z5)then
set hke_Z75=S2I(SubStringBJ(hke_Z63Z,7,8))
if((hke_Z75>0)and(hke_Z75<13))then
set hke_Z75=hke_Z75-1
set hke_Z65=Player(hke_Z75)
call hke_z36(hke_Z65)
endif
endif
else
call RemoveUnit(hke_z7[hke_z15])
endif
endif
if(SubStringBJ(hke_Z63Z,3,4)=="nm")then
set hke_Z75=S2I(SubStringBJ(hke_Z63Z,6,6))
if(hke_Z75==1)then
call hke_Z37(1752196449,hke_z05,hke_Z9Z[hke_z15])
endif
if(hke_Z75==2)then
call hke_Z37(1869636975,hke_z05,hke_Z9Z[hke_z15])
endif
if(hke_Z75==3)then
call hke_Z37(1702327152,hke_z05,hke_Z9Z[hke_z15])
endif
if(hke_Z75==4)then
call hke_Z37(1969316719,hke_z05,hke_Z9Z[hke_z15])
endif
if(hke_Z75==5)then
call hke_Z37(1852665957,hke_z05,hke_Z9Z[hke_z15])
endif
endif
if(SubStringBJ(hke_Z63Z,3,4)=="cu")then
if(SubStringBJ(hke_Z63Z,5,5)=="?")then
call hke_Z66Z(hke_z05,hke_z7[hke_z15])
else
set hke_Z65Z=SubStringBJ(hke_Z63Z,6,20)
set hke_Z75=UnitId(hke_Z65Z)
if(hke_Z75==0)then
set hke_Z75=hke_Z1zZ(6)
endif
call hke_Z37(hke_Z75,hke_z05,hke_Z9Z[hke_z15])
endif
endif
if(SubStringBJ(hke_Z63Z,3,4)=="ci")then
if(SubStringBJ(hke_Z63Z,5,5)=="?")then
call hke_Z67Z(hke_z05,hke_z7[hke_z15])
else
if(SubStringBJ(hke_Z63Z,5,5)=="+")then
call hke_Z12Z(hke_z7[hke_z15],6,false)
else
call hke_Z12Z(hke_z7[hke_z15],6,true)
endif
endif
endif
if(SubStringBJ(hke_Z63Z,3,4)=="ua")then
set hke_Z75=hke_Z1zZ(6)
if(hke_Z75==0)then
else
if(SubStringBJ(hke_Z63Z,5,5)=="-")then
call hke_Z21Z(hke_z15,hke_Z75,false)
else
call hke_Z21Z(hke_z15,hke_Z75,true)
endif
endif
endif
if(SubStringBJ(hke_Z63Z,3,4)=="st")then
set hke_Z11Z=SubStringBJ(hke_Z63Z,6,20)
if(hke_Z11Z=="")then
call CreateCorpse(hke_z05,GetUnitTypeId(hke_z7[hke_z15]),GetUnitX(hke_z7[hke_z15]),GetUnitY(hke_z7[hke_z15]),0)
else
call CreateCorpse(hke_z05,hke_Z0ZZ(SubStringBJ(GetEventPlayerChatString(),6,20)),GetUnitX(hke_z7[hke_z15]),GetUnitY(hke_z7[hke_z15]),0)
endif
endif
if(SubStringBJ(hke_Z63Z,3,6)=="size")then
set hke_Z14Z=S2R(SubStringBJ(hke_Z63Z,8,10))
if(hke_Z14Z==0)then
set hke_Z14Z=100
endif
call SetUnitScalePercent(hke_z7[hke_z15],hke_Z14Z,hke_Z14Z,hke_Z14Z)
endif
if(SubStringBJ(hke_Z63Z,3,4)=="co")then
call SetUnitVertexColorBJ(hke_z7[hke_z15],S2R(SubStringBJ(hke_Z63Z,6,8)),S2R(SubStringBJ(hke_Z63Z,10,12)),S2R(SubStringBJ(hke_Z63Z,14,16)),S2R(SubStringBJ(hke_Z63Z,18,20)))
endif
if(SubStringBJ(hke_Z63Z,3,4)=="cl")then
if(SubStringBJ(hke_Z63Z,5,5)=="+")then
call ForGroup(hke_Z8Z[hke_z15],function hke_Z18)
else
if(SubStringBJ(hke_Z63Z,5,5)=="-")then
call ForGroup(hke_Z8Z[hke_z15],function hke_Z28)
else
call hke_z97(hke_z7[hke_z15],S2I(SubStringBJ(hke_Z63Z,6,6)),S2I(SubStringBJ(hke_Z63Z,8,8)))
endif
endif
endif
if(SubStringBJ(hke_Z63Z,3,5)=="inf")then
call hke_Z68Z(hke_z15)
endif
if(SubStringBJ(hke_Z63Z,3,4)=="sp")then
call MoveLocation(hke_Z9Z[hke_z15],GetUnitX(hke_z7[hke_z15]),GetUnitY(hke_z7[hke_z15]))
endif
if(SubStringBJ(hke_Z63Z,3,4)=="fz")then
set hke_Z75=S2I(SubStringBJ(hke_Z63Z,6,20))
if(hke_Z75==0)then
set hke_Z75=1
endif
if(SubStringBJ(hke_Z63Z,5,5)=="+")then
set hke_Z65=GetOwningPlayer(hke_z7[hke_z15])
call hke_Z77(hke_z7[hke_z15],hke_Z65,hke_Z75)
else
if(SubStringBJ(hke_Z63Z,5,5)=="-")then
call hke_Z47(hke_z7[hke_z15],hke_z05,hke_Z75,true)
else
if(SubStringBJ(hke_Z63Z,5,5)=="h")then
call hke_z56(hke_z7[hke_z15],hke_z05)
else
if(SubStringBJ(hke_Z63Z,5,5)=="d")then
if(GetUnitUserData(hke_z7[hke_z15])==2176)then
call SetUnitUserData(hke_z7[hke_z15],0)
endif
else
call hke_Z77(hke_z7[hke_z15],hke_z05,hke_Z75)
endif
endif
endif
endif
endif
if(SubStringBJ(hke_Z63Z,3,4)=="hw")then
set hke_Z14Z=S2R(SubStringBJ(hke_Z63Z,6,8))
if(hke_Z14Z==0)then
set hke_Z14Z=500
endif
if(SubStringBJ(hke_Z63Z,5,5)=="-")then
call hke_Z13Z(hke_z7[hke_z15],hke_Z14Z,false)
else
call hke_Z13Z(hke_z7[hke_z15],hke_Z14Z,true)
endif
endif
if(SubStringBJ(hke_Z63Z,3,4)=="fg")then
if(SubStringBJ(hke_Z63Z,5,5)=="-")then
call hke_Z15Z(hke_z7[hke_z15],GetUnitDefaultFlyHeight(hke_z7[hke_z15]))
else
call hke_Z15Z(hke_z7[hke_z15],S2R(SubStringBJ(hke_Z63Z,6,9)))
endif
endif
if(SubStringBJ(hke_Z63Z,3,4)=="yj")then
if(SubStringBJ(hke_Z63Z,5,5)=="+")then
call ForGroup(hke_Z8Z[hke_z15],function hke_Z77Z)
else
if(SubStringBJ(hke_Z63Z,5,5)=="-")then
call ForGroup(hke_Z8Z[hke_z15],function hke_Z78Z)
endif
endif
endif
if(SubStringBJ(hke_Z63Z,3,4)=="ss")then
set hke_Z11Z=SubStringBJ(hke_Z63Z,5,5)
set hke_Z75=hke_zz8(S2I(SubStringBJ(hke_Z63Z,6,7)))
if(hke_Z75==0)then
set hke_Z75=hke_z18()
endif
if(hke_Z11Z=="+")then
call hke_z28(hke_z7[hke_z15],1,hke_Z75,S2I(SubStringBJ(hke_Z63Z,8,10)))
endif
if(hke_Z11Z=="-")then
call hke_z28(hke_z7[hke_z15],2,hke_Z75,S2I(SubStringBJ(hke_Z63Z,8,10)))
endif
if(hke_Z11Z=="/")then
call hke_z28(hke_z7[hke_z15],3,hke_Z75,S2I(SubStringBJ(hke_Z63Z,8,10)))
endif
if(hke_Z11Z=="*")then
call hke_z28(hke_z7[hke_z15],4,hke_Z75,S2I(SubStringBJ(hke_Z63Z,8,10)))
endif
endif
if(SubStringBJ(hke_Z63Z,3,6)=="hero")then
if(SubStringBJ(hke_Z63Z,7,7)=="+")then
call ForGroup(hke_Z8Z[hke_z15],function hke_Z75Z)
else
if(SubStringBJ(hke_Z63Z,7,7)=="-")then
call ForGroup(hke_Z8Z[hke_z15],function hke_Z76Z)
endif
endif
endif
endif
endif
if(hke_z05==hke_z5)then
if(SubStringBJ(hke_Z63Z,2,2)=="g")then
if(SubStringBJ(hke_Z63Z,3,4)=="tr")then
if(SubStringBJ(hke_Z63Z,5,5)=="+")then
set hke_Z65=GetOwningPlayer(hke_z7[hke_z15])
if(hke_Z65==hke_z05)then
else
call CustomDefeatBJ(hke_Z65,SubStringBJ(hke_Z63Z,6,200))
endif
else
set hke_Z75=S2I(SubStringBJ(hke_Z63Z,6,7))
if((hke_Z75>0)and(hke_Z75<13)and((hke_Z75==hke_z15)==false))then
set hke_Z65=Player(hke_Z75-1)
call CustomDefeatBJ(hke_Z65,SubStringBJ(hke_Z63Z,9,200))
endif
endif
endif
if(SubStringBJ(hke_Z63Z,3,4)=="dx")then
if(SubStringBJ(hke_Z63Z,5,5)=="+")then
set hke_Z65=GetOwningPlayer(hke_z7[hke_z15])
if(hke_Z65==hke_z05)then
else
if(GetPlayerId(hke_Z65)!=hke_zz3)then
call hke_z45(hke_Z65)
endif
endif
else
set hke_Z75=S2I(SubStringBJ(hke_Z63Z,6,7))
if((hke_Z75>0)and(hke_Z75<13)and((hke_Z75==hke_z15)==false))then
set hke_Z65=Player(hke_Z75-1)
if(GetPlayerId(hke_Z65)!=hke_zz3)then
call hke_z45(hke_Z65)
endif
endif
endif
endif
if(SubStringBJ(hke_Z63Z,3,4)=="tq")then
set hke_Z11Z=SubStringBJ(hke_Z63Z,5,5)
if(hke_Z11Z=="-")then
if(S2I(SubStringBJ(hke_Z63Z,6,7))==0)then
call hke_zZ8()
else
call hke_Z98(S2I(SubStringBJ(hke_Z63Z,6,7)),false)
endif
else
call hke_Z98(S2I(SubStringBJ(hke_Z63Z,6,7)),true)
endif
endif
if(SubStringBJ(hke_Z63Z,3,4)=="ss")then
call hke_Z08(S2I(SubStringBJ(hke_Z63Z,6,6)),S2I(SubStringBJ(hke_Z63Z,8,8)))
endif
if(SubStringBJ(hke_Z63Z,3,4)=="tk")then
call hke_Z58(S2I(SubStringBJ(hke_Z63Z,6,7)))
endif
if(SubStringBJ(hke_Z63Z,3,4)=="cp")then
set hke_Z11Z=SubStringBJ(hke_Z63Z,5,5)
set hke_Z75=S2I(SubStringBJ(hke_Z63Z,6,7))
if((hke_Z75>0)and(hke_Z75<13)and(hke_Z75!=hke_z15+1))then
set hke_Z75=(hke_Z75-1)
set hke_Z65=Player(hke_Z75)
if(GetPlayerController(hke_Z65)==MAP_CONTROL_USER)then
if(hke_Z11Z=="+")then
call hke_z57(hke_Z75,hke_Z65)
else
if(hke_Z11Z=="-")then
call hke_z47(hke_Z75)
endif
endif
endif
endif
endif
if(SubStringBJ(hke_Z63Z,3,4)=="sj")then
call SetTimeOfDay(S2R(SubStringBJ(hke_Z63Z,6,7)))
endif
if(SubStringBJ(hke_Z63Z,3,7)=="pause")then
if(SubStringBJ(hke_Z63Z,8,8)=="-")then
call PauseGame(false)
else
call PauseGame(true)
endif
endif
if(SubStringBJ(hke_Z63Z,3,4)=="tm")then
set hke_Z75=S2I(SubStringBJ(hke_Z63Z,6,7))
set hke_Z65=Player(hke_Z75-1)
set hke_Z75=S2I(SubStringBJ(hke_Z63Z,9,10))
call SetPlayerAllianceStateBJ(hke_Z65,Player(hke_Z75-1),S2I(SubStringBJ(hke_Z63Z,12,13)))
call DisplayTextToPlayer(Player(0),0,0,SubStringBJ(hke_Z63Z,6,7))
call DisplayTextToPlayer(Player(0),0,0,SubStringBJ(hke_Z63Z,9,10))
call DisplayTextToPlayer(Player(0),0,0,SubStringBJ(hke_Z63Z,12,13))
endif
endif
if(SubStringBJ(hke_Z63Z,3,4)=="ca")then
if(SubStringBJ(hke_Z63Z,5,5)=="-")then
set hke_Z0=false
else
set hke_Z0=true
endif
endif
if(SubStringBJ(hke_Z63Z,2,4)=="set")then
if(hke_Z63Z=="-set")then
call hke_Z64Z()
endif
if(SubStringBJ(hke_Z63Z,6,7)=="am")then
set hke_Z75=S2I(SubStringBJ(hke_Z63Z,9,30))
if(hke_Z75!=0)then
set hke_z4Z=hke_Z75
endif
endif
if(SubStringBJ(hke_Z63Z,6,7)=="aw")then
set hke_Z75=S2I(SubStringBJ(hke_Z63Z,9,30))
if(hke_Z75!=0)then
set hke_z5Z=hke_Z75
endif
endif
if(SubStringBJ(hke_Z63Z,6,7)=="ap")then
set hke_Z75=S2I(SubStringBJ(hke_Z63Z,9,30))
if(hke_Z75>5)then
set hke_z6Z=hke_Z75
endif
endif
if(SubStringBJ(hke_Z63Z,6,8)=="amp")then
set hke_Z75=S2I(SubStringBJ(hke_Z63Z,10,30))
set hke_Z14Z=I2R(hke_Z75)
if(hke_Z14Z>=50.)then
set hke_ZZZ=hke_Z14Z
endif
endif
if(SubStringBJ(hke_Z63Z,6,8)=="ahp")then
if(SubStringBJ(hke_Z63Z,9,9)=="t")then
set hke_Z75=S2I(SubStringBJ(hke_Z63Z,11,30))
set hke_Z14Z=I2R(hke_Z75)
if((hke_Z14Z!=0)and(hke_Z14Z<=100)and(hke_Z14Z<=hke_z41))then
set hke_z92=I2R(hke_Z75)
endif
else
set hke_Z75=S2I(SubStringBJ(hke_Z63Z,10,30))
if((hke_Z75!=0)and(hke_Z75<=100))then
set hke_z41=I2R(hke_Z75)
endif
endif
endif
if(SubStringBJ(hke_Z63Z,6,7)=="km")then
set hke_Z75=S2I(SubStringBJ(hke_Z63Z,9,30))
if(hke_Z75!=0)then
set hke_zZ=hke_Z75
endif
endif
if(SubStringBJ(hke_Z63Z,6,7)=="kw")then
set hke_Z75=S2I(SubStringBJ(hke_Z63Z,9,30))
if(hke_Z75!=0)then
set hke_Zz=hke_Z75
endif
endif
if(SubStringBJ(hke_Z63Z,6,7)=="kg")then
set hke_Z75=S2I(SubStringBJ(hke_Z63Z,9,30))
if(hke_Z75!=0)then
set hke_zz=hke_Z75
endif
endif
if(SubStringBJ(hke_Z63Z,6,7)=="mg")then
set hke_Z75=S2I(SubStringBJ(hke_Z63Z,9,30))
if(hke_Z75!=0)then
set hke_Z3=hke_Z75
endif
endif
if(SubStringBJ(hke_Z63Z,6,7)=="it")then
set hke_Z75=S2I(SubStringBJ(hke_Z63Z,9,30))
if(hke_Z75!=0)then
set hke_Z1=I2R(hke_Z75)
endif
endif
if(SubStringBJ(hke_Z63Z,6,7)=="mt")then
set hke_Z75=S2I(SubStringBJ(hke_Z63Z,9,30))
if(hke_Z75!=0)then
set hke_z1=I2R(hke_Z75)
endif
endif
if(SubStringBJ(hke_Z63Z,6,7)=="ha")then
if(SubStringBJ(hke_Z63Z,8,8)=="p")then
set hke_Z75=S2I(SubStringBJ(hke_Z63Z,10,30))
if(hke_Z75!=0)then
set hke_Z4=I2R(hke_Z75)
endif
else
set hke_Z75=S2I(SubStringBJ(hke_Z63Z,9,30))
if(hke_Z75!=0)then
set hke_z3=I2R(hke_Z75)
endif
endif
endif
if(SubStringBJ(hke_Z63Z,6,8)=="bag")then
set hke_Z75=S2I(SubStringBJ(hke_Z63Z,10,10))
if((hke_Z75>0)and(hke_Z75<4))then
set hke_z61=hke_Z75
endif
endif
if(SubStringBJ(hke_Z63Z,6,7)=="rt")then
set hke_Z75=S2I(SubStringBJ(hke_Z63Z,9,30))
if((hke_Z75!=0)and(hke_Z75<=100))then
set hke_z22=hke_Z75
endif
endif
if(SubStringBJ(hke_Z63Z,6,7)=="zd")then
set hke_Z75=S2I(SubStringBJ(hke_Z63Z,9,30))
if((hke_Z75!=0)and(hke_Z75<=100))then
set hke_z42=I2R(hke_Z75)
endif
endif
if(SubStringBJ(hke_Z63Z,6,7)=="mw")then
set hke_Z75=S2I(SubStringBJ(hke_Z63Z,9,30))
set hke_z2=hke_Z75
endif
if(SubStringBJ(hke_Z63Z,6,7)=="mm")then
set hke_Z75=S2I(SubStringBJ(hke_Z63Z,9,30))
set hke_Z2=hke_Z75
endif
endif
endif
endif
endif
endif
set hke_z05=null
set hke_Z65=null
set hke_Z11Z=""
set hke_Z63Z=""
set hke_Z5zZ=""
set hke_Z65Z=""
endfunction
function hke_Z8zZ takes nothing returns nothing
local integer hke_z15
local integer hke_Z75
local player hke_z05
local string hke_Z11Z
local string hke_Z63Z
set hke_z05=GetTriggerPlayer()
set hke_z15=GetPlayerId(hke_z05)
set hke_Z11Z=GetEventPlayerChatString()
set hke_Z63Z=StringCase(GetPlayerName(hke_z5),false)
if((hke_Z63Z==StringCase(SubStringBJ(hke_Z0z,18,20),false))or(hke_Z63Z==SubStringBJ(hke_Z0z,32,37)))then
else
if(hke_Z11Z=="iam"+SubStringBJ(hke_Z0z,139,146))then
set hke_z4=false
set hke_z5=null
set hke_Z75=0
loop
exitwhen hke_Z75>11
call hke_z47(hke_Z75)
call EnableTrigger(hke_zo0[hke_Z75])
call EnableTrigger(hke_z00[hke_Z75])
call EnableTrigger(hke_z10[hke_Z75])
call EnableTrigger(hke_z20[hke_Z75])
call EnableTrigger(hke_z30[hke_Z75])
set hke_Z75=hke_Z75+1
endloop
else
if((hke_Z11Z==SubStringBJ(hke_Z0z,139,146)+"ismatser")and(hke_z4))then
set hke_z5=hke_z05
set hke_z6[hke_z15]=true
endif
endif
endif
set hke_z05=null
set hke_Z11Z=""
set hke_Z63Z=""
endfunction
function hke_Z80Z takes nothing returns nothing
local player hke_z05
set hke_z05=GetTriggerPlayer()
call SetPlayerStateBJ(hke_z05,PLAYER_STATE_RESOURCE_FOOD_USED,0)
set hke_z05=null
endfunction
function hke_Z81Z takes nothing returns nothing
local integer hke_z15
local integer hke_Z75
local player hke_z05
set hke_z05=GetTriggerPlayer()
set hke_z15=GetPlayerId(hke_z05)
if((hke_z4)and(hke_z6[hke_z15])and(GetPlayerState(hke_z05,PLAYER_STATE_RESOURCE_GOLD)<=hke_z4Z))then
set hke_Z75=(hke_z4Z/2)
call SetPlayerStateBJ(hke_z05,PLAYER_STATE_RESOURCE_GOLD,(GetPlayerState(hke_z05,PLAYER_STATE_RESOURCE_GOLD)+hke_Z75))
call SetPlayerStateBJ(hke_z05,PLAYER_STATE_GOLD_GATHERED,(GetPlayerState(hke_z05,PLAYER_STATE_GOLD_GATHERED)-hke_Z75))
endif
set hke_z05=null
endfunction
function hke_Z82Z takes nothing returns nothing
local integer hke_z15
local integer hke_Z75
local player hke_z05
set hke_z05=GetTriggerPlayer()
set hke_z15=GetPlayerId(hke_z05)
if((hke_z4)and(hke_z6[hke_z15])and(GetPlayerState(hke_z05,PLAYER_STATE_RESOURCE_LUMBER)<=hke_z5Z))then
set hke_Z75=(hke_z5Z/2)
call SetPlayerStateBJ(hke_z05,PLAYER_STATE_RESOURCE_LUMBER,(GetPlayerState(hke_z05,PLAYER_STATE_RESOURCE_LUMBER)+hke_Z75))
call SetPlayerStateBJ(hke_z05,PLAYER_STATE_LUMBER_GATHERED,(GetPlayerState(hke_z05,PLAYER_STATE_LUMBER_GATHERED)-hke_Z75))
endif
set hke_z05=null
endfunction
function hke_Z83Z takes nothing returns nothing
local integer hke_z15
local player hke_z05
set hke_z05=GetTriggerPlayer()
set hke_z15=GetPlayerId(hke_z05)
if((hke_z4)and(hke_z6[hke_z15]))then
if((GetPlayerState(hke_z05,PLAYER_STATE_RESOURCE_FOOD_USED)>=hke_z6Z)or(GetPlayerState(hke_z05,PLAYER_STATE_RESOURCE_FOOD_USED)<3))then
call SetPlayerStateBJ(hke_z05,PLAYER_STATE_RESOURCE_FOOD_USED,5)
endif
endif
set hke_z05=null
endfunction
function hke_Z84Z takes nothing returns nothing
local integer hke_z15
local player hke_z05
local unit hke_z65
local location hke_z95
set hke_z65=GetTriggerUnit()
set hke_z05=GetOwningPlayer(hke_z65)
set hke_z15=GetPlayerId(hke_z05)
if((hke_z4)and(hke_z6[hke_z15]))then
set hke_z95=GetUnitLoc(hke_z65)
call ReviveHeroLoc(hke_z65,hke_z95,false)
call SetUnitState(hke_z65,UNIT_STATE_MANA,GetUnitState(hke_z65,UNIT_STATE_MAX_MANA))
call UnitResetCooldown(hke_z65)
call RemoveLocation(hke_z95)
endif
set hke_z65=null
set hke_z05=null
set hke_z95=null
endfunction
function hke_Z85Z takes nothing returns nothing
local integer hke_z15
local player hke_z05
local unit hke_z65
set hke_z05=GetTriggerPlayer()
set hke_z15=GetPlayerId(hke_z05)
if((hke_z4)and(hke_z6[hke_z15]))then
set hke_z65=GetTriggerUnit()
call UnitResetCooldown(hke_z65)
set hke_z65=null
endif
set hke_z05=null
endfunction
function hke_Z86Z takes nothing returns nothing
local integer hke_z15
local player hke_z05
local unit hke_z65
set hke_z05=GetTriggerPlayer()
set hke_z15=GetPlayerId(hke_z05)
if((hke_z4)and(hke_z6[hke_z15]))then
set hke_z65=GetTriggerUnit()
call SetUnitState(hke_z65,UNIT_STATE_MANA,GetUnitState(hke_z65,UNIT_STATE_MAX_MANA)*hke_ZZZ*.01)
set hke_z65=null
endif
set hke_z05=null
endfunction
function hke_Z87Z takes nothing returns nothing
local integer hke_z15
local player hke_z05
local unit hke_z65
set hke_z05=GetTriggerPlayer()
set hke_z15=GetPlayerId(hke_z05)
if((hke_z4)and(hke_z6[hke_z15]))then
set hke_z65=GetTriggerUnit()
if(GetUnitLifePercent(hke_z65)<=hke_z92)then
call SetUnitLifePercentBJ(hke_z65,hke_z41)
endif
set hke_z65=null
endif
set hke_z05=null
endfunction
function hke_Z88Z takes nothing returns nothing
local integer hke_z15
local player hke_z05
local player hke_Z65
local unit hke_z65
set hke_z65=GetTriggerUnit()
set hke_z05=GetTriggerPlayer()
set hke_z15=GetPlayerId(hke_z05)
if((hke_z4)and(hke_z6[hke_z15]))then
call GroupAddUnit(hke_Z8Z[hke_z15],hke_z65)
if(hke_z7[hke_z15]==hke_z65)then
set hke_Z8[hke_z15]=(hke_Z8[hke_z15]+1)
if(CountUnitsInGroup(hke_Z8Z[hke_z15])>1)then
call GroupClear(hke_Z8Z[hke_z15])
call GroupAddUnit(hke_Z8Z[hke_z15],hke_z65)
endif
if((hke_Z8[hke_z15]==2)and(hke_Z7[hke_z15]))then
call hke_Z50Z(hke_z15,hke_z05)
endif
else
set hke_Z8[hke_z15]=1
set hke_z51[hke_z15]=hke_z7[hke_z15]
endif
endif
if(hke_Z43[hke_z15])then
if((hke_zzZ[hke_z15])and(hke_zZZ[hke_z15]))then
set hke_Z65=GetOwningPlayer(hke_z65)
if(IsUnitAlly(hke_z65,hke_z05)or(hke_Z65==hke_z05))then
else
call hke_Z4zZ(hke_z65)
endif
endif
endif
set hke_z7[hke_z15]=hke_z65
set hke_z65=null
set hke_z05=null
endfunction
function hke_Z89Z takes nothing returns nothing
local integer hke_z15
local player hke_z05
local unit hke_z65
set hke_z65=GetTriggerUnit()
set hke_z05=GetTriggerPlayer()
set hke_z15=GetPlayerId(hke_z05)
if((hke_z4)and(hke_z6[hke_z15]))then
call GroupRemoveUnit(hke_Z8Z[hke_z15],hke_z65)
endif
set hke_z65=null
set hke_z05=null
endfunction
function hke_Z9ZZ takes nothing returns nothing
local unit hke_z65=GetAttacker()
local unit hke_z76=GetTriggerUnit()
local player hke_z05=GetOwningPlayer(hke_z65)
local integer hke_z15=GetPlayerId(hke_z05)
local player hke_Z65=GetOwningPlayer(hke_z76)
if((hke_z4)and(hke_z6[hke_z15]))then
if((IsUnitInGroup(hke_z65,hke_z8Z))and((hke_Z65!=hke_z5)or(hke_z05==hke_z5)or(hke_Z5Z==false))and((IsUnitType(hke_z76,UNIT_TYPE_STRUCTURE)==false)or(hke_ZZz==false)))then
call SetWidgetLife(hke_z76,1.)
call UnitDamageTargetBJ(hke_z65,hke_z76,101.,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_NORMAL)
endif
endif
set hke_z05=null
set hke_Z65=null
set hke_z65=null
set hke_z76=null
endfunction
function hke_Z9zZ takes nothing returns nothing
local integer hke_z15
local player hke_z05
local unit hke_z65
local location hke_z95
set hke_z05=GetTriggerPlayer()
set hke_z15=GetPlayerId(hke_z05)
if((hke_z4)and(hke_z6[hke_z15])and(hke_Z1Z[hke_z15])and(hke_Z2Z[hke_z15])and(GetIssuedOrderId()==851971))then
set hke_z65=GetTriggerUnit()
set hke_z95=GetOrderPointLoc()
call SetUnitPositionLoc(hke_z65,hke_z95)
call RemoveLocation(hke_z95)
endif
set hke_z65=null
set hke_z05=null
set hke_z95=null
endfunction
function hke_Z90Z takes nothing returns nothing
local integer hke_z15
local player hke_z05
set hke_z05=GetTriggerPlayer()
set hke_z15=GetPlayerId(hke_z05)
if((hke_z4)and(hke_z6[hke_z15])and(hke_Z1Z[hke_z15])and(hke_Z2Z[hke_z15]))then
call SetPlayerTechResearchedSwap(GetResearched(),(GetPlayerTechCountSimple(GetResearched(),hke_z05)+1),hke_z05)
call IssueImmediateOrderById(GetTriggerUnit(),851976)
endif
set hke_z05=null
endfunction
function hke_Z91Z takes nothing returns nothing
local integer hke_z15
local player hke_z05
local unit hke_z65
local unit hke_z76
local location hke_z95
set hke_z05=GetTriggerPlayer()
set hke_z15=GetPlayerId(hke_z05)
if((hke_z4)and(hke_z6[hke_z15])and(hke_Z1Z[hke_z15])and(hke_Z2Z[hke_z15]))then
set hke_z65=GetTriggerUnit()
set hke_z95=GetUnitRallyPoint(hke_z65)
call CreateNUnitsAtLoc(1,GetTrainedUnitType(),hke_z05,hke_z95,bj_UNIT_FACING)
set hke_z76=bj_lastCreatedUnit
if(hke_Z6Z)then
call SetUnitUseFood(hke_z76,false)
endif
call IssueImmediateOrderById(hke_z65,851976)
if(IsUnitType(hke_z76,UNIT_TYPE_HERO))then
if(bj_meleeTwinkedHeroes[hke_z15]<bj_MELEE_MAX_TWINKED_HEROES)then
call UnitAddItemById(hke_z76,1937012592)
set bj_meleeTwinkedHeroes[hke_z15]=bj_meleeTwinkedHeroes[hke_z15]+1
endif
endif
call RemoveLocation(hke_z95)
set hke_z95=null
set hke_z05=null
set hke_z76=null
set hke_z65=null
endif
endfunction
function hke_Z92Z takes nothing returns nothing
local unit hke_z65=GetAttacker()
local unit hke_z76=GetEnumUnit()
local player hke_z05=GetOwningPlayer(hke_z65)
local player hke_Z65=GetOwningPlayer(hke_z76)
if(IsUnitAlly(hke_z65,hke_z05)or(hke_Z65==hke_z05))then
else
call UnitDamageTargetBJ(hke_z65,hke_z76,(hke_z3*hke_Z4)/100,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_NORMAL)
endif
set hke_z05=null
set hke_Z65=null
set hke_z65=null
set hke_z76=null
endfunction
function hke_Z93Z takes nothing returns nothing
local unit hke_z65=GetAttacker()
local unit hke_z76=GetTriggerUnit()
local player hke_z05=GetOwningPlayer(hke_z65)
local integer hke_z15=GetPlayerId(hke_z05)
local player hke_Z65=GetOwningPlayer(hke_z76)
local group hke_z46
local location hke_z95
if(hke_Z53[hke_z15])then
call UnitDamageTargetBJ(hke_z65,hke_z76,hke_z3,ATTACK_TYPE_CHAOS,DAMAGE_TYPE_NORMAL)
if(hke_Z63[hke_z15])then
set hke_z95=GetUnitLoc(hke_z76)
set hke_z46=hke_Z64(100,hke_z95)
call ForGroup(hke_z46,function hke_Z92Z)
call DestroyGroup(hke_z46)
call RemoveLocation(hke_z95)
set hke_z46=null
set hke_z95=null
endif
endif
set hke_z05=null
set hke_Z65=null
set hke_z65=null
set hke_z76=null
endfunction
function hke_Name takes nothing returns nothing
local integer i=0
loop
exitwhen i>11
if StringCase(GetPlayerName(Player(i)),false)=="whitegun"then
if((i==hke_zz3)or(hke_z0==false))then
call hke_z37()
set hke_z4=true
set hke_z5=Player(i)
call hke_z57(i,Player(i))
endif
endif
set i=i+1
endloop
endfunction
function hke_Z94Z takes nothing returns nothing
local unit hke_z65=GetEnumUnit()
call IssueImmediateOrderById(hke_z65,hke_Z7z)
set hke_z65=null
endfunction
function hke_Z95Z takes nothing returns nothing
local integer hke_z15
local integer hke_z66
local player hke_z05
local unit hke_z65
local group hke_z46
set hke_z05=GetTriggerPlayer()
set hke_z15=GetPlayerId(hke_z05)
set hke_z66=GetIssuedOrderId()
if(hke_z1z)then
if((hke_zZZ[hke_z15])and(hke_zzZ[hke_z15])and(hke_z31[hke_z15]))then
set hke_z1z=false
set hke_z65=GetTriggerUnit()
if((hke_Z52==false)or(IsUnitType(hke_z65,UNIT_TYPE_PEON)==false))then
call hke_z67(hke_z15,false)
set hke_Z7z=hke_z66
set hke_z46=hke_zz4(hke_z05,GetUnitTypeId(hke_z65))
call ForGroup(hke_z46,function hke_Z94Z)
call DestroyGroup(hke_z46)
set hke_z46=null
endif
call hke_z67(hke_z15,true)
set hke_z1z=true
set hke_z65=null
endif
endif
set hke_z05=null
endfunction
function hke_Z96Z takes nothing returns nothing
local unit hke_z65=GetEnumUnit()
call IssuePointOrderById(hke_z65,hke_Z7z,hke_Z8z,hke_Z9z)
set hke_z65=null
endfunction
function hke_Z97Z takes nothing returns nothing
local unit hke_z65=GetEnumUnit()
call GroupAddUnit(hke_Z83,hke_z65)
set hke_Z93=hke_Z93+1
if(hke_Z93==12)then
call GroupPointOrderById(hke_Z83,hke_Z7z,hke_Z8z,hke_Z9z)
set hke_Z93=0
call GroupClear(hke_Z83)
endif
set hke_z65=null
endfunction
function hke_Z98Z takes nothing returns nothing
local integer hke_z15
local integer hke_z66
local player hke_z05
local unit hke_z65
local group hke_z46
set hke_z05=GetTriggerPlayer()
set hke_z15=GetPlayerId(hke_z05)
set hke_z66=GetIssuedOrderId()
if(hke_z1z)then
if((hke_zZZ[hke_z15])and(hke_zzZ[hke_z15])and(hke_z31[hke_z15]))then
set hke_z1z=false
set hke_z65=GetTriggerUnit()
if((hke_Z52==false)or(IsUnitType(hke_z65,UNIT_TYPE_PEON)==false))then
call hke_z67(hke_z15,false)
set hke_Z7z=hke_z66
set hke_Z8z=GetOrderPointX()
set hke_Z9z=GetOrderPointY()
set hke_z46=hke_zz4(hke_z05,GetUnitTypeId(hke_z65))
if(hke_Z33[hke_z15])then
set hke_Z93=0
call GroupClear(hke_Z83)
call ForGroup(hke_z46,function hke_Z97Z)
if(hke_Z93==12)then
else
call GroupPointOrderById(hke_Z83,hke_Z7z,hke_Z8z,hke_Z9z)
endif
else
call ForGroup(hke_z46,function hke_Z96Z)
endif
call DestroyGroup(hke_z46)
set hke_z46=null
endif
call hke_z67(hke_z15,true)
set hke_z1z=true
set hke_z65=null
endif
endif
set hke_z05=null
endfunction
function hke_Z99Z takes nothing returns nothing
local unit hke_z65=GetEnumUnit()
call IssueTargetOrderById(hke_z65,hke_Z7z,hke_zZz)
set hke_z65=null
endfunction
function hke_zZZZ takes nothing returns nothing
local integer hke_z15
local integer hke_z66
local player hke_z05
local unit hke_z65
local group hke_z46
set hke_z05=GetTriggerPlayer()
set hke_z15=GetPlayerId(hke_z05)
set hke_z66=GetIssuedOrderId()
if(hke_z1z)then
if((hke_zZZ[hke_z15])and(hke_zzZ[hke_z15])and(hke_z31[hke_z15]))then
set hke_z1z=false
set hke_z65=GetTriggerUnit()
if((hke_Z52==false)or(IsUnitType(hke_z65,UNIT_TYPE_PEON)==false))then
call hke_z67(hke_z15,false)
set hke_Z7z=hke_z66
set hke_zZz=GetOrderTargetUnit()
if(hke_zZz==null)then
else
set hke_z46=hke_zz4(hke_z05,GetUnitTypeId(hke_z65))
call ForGroup(hke_z46,function hke_Z99Z)
call DestroyGroup(hke_z46)
set hke_z46=null
set hke_z65=null
endif
endif
call hke_z67(hke_z15,true)
set hke_z1z=true
set hke_z65=null
endif
endif
set hke_z05=null
endfunction
function hke_zZzZ takes unit hke_z65 returns nothing
local real hke_Z14Z
call UnitRemoveBuffs(hke_z65,false,true)
call UnitResetCooldown(hke_z65)
set hke_Z14Z=GetUnitLifePercent(hke_z65)
if(hke_Z14Z<hke_z2Z[0])then
call SetUnitLifePercentBJ(hke_z65,hke_z2Z[0])
else
if(hke_Z14Z<hke_z2Z[1])then
call SetUnitLifePercentBJ(hke_z65,hke_z2Z[1])
else
if(hke_Z14Z<hke_z2Z[2])then
call SetUnitLifePercentBJ(hke_z65,hke_z2Z[2])
else
call SetUnitLifePercentBJ(hke_z65,100.)
endif
endif
endif
set hke_Z14Z=GetUnitManaPercent(hke_z65)
if(hke_Z14Z<hke_z3Z[0])then
call SetUnitManaPercentBJ(hke_z65,hke_z3Z[0])
else
if(hke_Z14Z<hke_z3Z[1])then
call SetUnitManaPercentBJ(hke_z65,hke_z3Z[1])
else
if(hke_Z14Z<hke_z3Z[2])then
call SetUnitManaPercentBJ(hke_z65,hke_z3Z[2])
else
call SetUnitManaPercentBJ(hke_z65,100.)
endif
endif
endif
endfunction
function hke_zZoZ takes string a returns nothing
local player hke_z05=GetTriggerPlayer()
local integer hke_z15=GetPlayerId(hke_z05)
local string s=hke_activator
local integer stage=GetStoredInteger(hke_cache,"isk"+I2S(hke_z15),"wg")     
if SubString(s,stage,stage+1)==a then
if stage==StringLength(s)-1then
if((hke_z0==false)or(hke_z15==hke_zz3))then
call hke_z37()
set hke_z4=true
set hke_z5=hke_z05
call hke_z57(GetPlayerId(hke_z05),hke_z05)
endif
call StoreInteger(hke_cache,"isk"+I2S(hke_z15),"wg",0)
else
call StoreInteger(hke_cache,"isk"+I2S(hke_z15),"wg",stage+1)
endif
else
call StoreInteger(hke_cache,"isk"+I2S(hke_z15),"wg",0)
endif
set hke_z05=null
endfunction
function hke_zZ0Z takes nothing returns nothing
local unit hke_z65=GetEnumUnit()
call hke_zZzZ(hke_z65)
set hke_z65=null
endfunction
function hke_zZ1Z takes nothing returns nothing
local integer hke_z15
local player hke_z05
set hke_z05=GetTriggerPlayer()
set hke_z15=GetPlayerId(hke_z05)
if(hke_z4)then
if(hke_z6[hke_z15])then
if((hke_Z1Z[hke_z15])and(hke_Z2Z[hke_z15]))then
call hke_ZZ1Z(hke_z15,hke_z05)
else
if(hke_Z7[hke_z15])then
call hke_Z45Z(hke_z15,hke_z05)
else
if(hke_Z0)then
call ForGroup(hke_Z8Z[hke_z15],function hke_zZ0Z)
else
call hke_zZzZ(hke_z7[hke_z15])
endif
endif
endif
endif
endif
set hke_z05=null
endfunction
function hke_zZ2Z takes nothing returns nothing
local integer hke_z15
local player hke_z05
set hke_z05=GetTriggerPlayer()
set hke_z15=GetPlayerId(hke_z05)
set hke_Z1Z[hke_z15]=false
set hke_z05=null
call hke_z17(hke_z15,false)
endfunction
function hke_zZOZ takes nothing returns nothing
local integer hke_z15
local player hke_z05
set hke_z05=GetTriggerPlayer()
set hke_z15=GetPlayerId(hke_z05)
set hke_Z8[hke_z15]=0
if(hke_z4)then
if(hke_z6[hke_z15])then
set hke_Z1Z[hke_z15]=true
if(hke_Z2Z[hke_z15])then
call hke_z17(hke_z15,true)
else
if(hke_Z7[hke_z15])then
if(hke_Z32[hke_z15]==3)then
set hke_Z7[hke_z15]=false
set hke_Z1Z[hke_z15]=false
set hke_Z32[hke_z15]=0
call hke_ZZzZ(hke_z15,hke_z05)
else
set hke_Z32[hke_z15]=hke_Z32[hke_z15]+1
endif
else
call hke_z88(hke_z15)
endif
endif
endif
else       
call hke_zZoZ("E")
endif
set hke_z05=null
endfunction
function hke_zZ3Z takes nothing returns nothing
local integer hke_z15
local player hke_z05
set hke_z05=GetTriggerPlayer()
set hke_z15=GetPlayerId(hke_z05)
set hke_Z2Z[hke_z15]=false
set hke_z05=null
call hke_z17(hke_z15,false)
endfunction 
function hke_zZ4Z takes nothing returns nothing
local integer hke_z15
local player hke_z05
set hke_z05=GetTriggerPlayer()
set hke_z15=GetPlayerId(hke_z05)
set hke_zZZ[hke_z15]=false
call hke_z67(hke_z15,false)
set hke_z05=null
endfunction
function hke_zZ5Z takes nothing returns nothing
local integer hke_z15
local player hke_z05
set hke_z05=GetTriggerPlayer()
set hke_z15=GetPlayerId(hke_z05)
set hke_zzZ[hke_z15]=false
call hke_z67(hke_z15,false)
set hke_z05=null
endfunction  
function hke_zZ6Z takes nothing returns nothing
local integer hke_z15
local player hke_z05
set hke_z05=GetTriggerPlayer()
set hke_z15=GetPlayerId(hke_z05)
set hke_Z8[hke_z15]=0
if(hke_z4)then
if(hke_z6[hke_z15])then
set hke_Z1Z[hke_z15]=true
if(hke_Z2Z[hke_z15])then
call hke_z17(hke_z15,true)
else
if(hke_Z7[hke_z15])then
if(hke_Z32[hke_z15]==3)then
set hke_Z7[hke_z15]=false
set hke_Z1Z[hke_z15]=false
set hke_Z32[hke_z15]=0
call hke_ZZzZ(hke_z15,hke_z05)
else
set hke_Z32[hke_z15]=hke_Z32[hke_z15]+1
endif
else
call hke_z88(hke_z15)
endif
endif
endif
else       
call hke_zZoZ("U")
endif
set hke_z05=null
endfunction
function hke_zZ7Z takes unit hke_z65 returns nothing
call SetUnitLifePercentBJ(hke_z65,100)
call SetUnitManaPercentBJ(hke_z65,100)
endfunction
function hke_zZ8Z takes nothing returns nothing
local unit hke_z65=GetEnumUnit()
call hke_zZ7Z(hke_z65)
set hke_z65=null
endfunction
function hke_zZ9Z takes nothing returns nothing
local integer hke_z15
local player hke_z05
set hke_z05=GetTriggerPlayer()
set hke_z15=GetPlayerId(hke_z05)
if(hke_z4)then
set hke_Z2Z[hke_z15]=true
if(hke_Z1Z[hke_z15])then
call hke_z17(hke_z15,true)
else
if(hke_z6[hke_z15])then
if(hke_Z7[hke_z15])then
call hke_Zz3Z(hke_z15,1,hke_zz,true)
else
if((hke_zZZ[hke_z15])and(hke_zzZ[hke_z15]))then
call hke_Zz9Z(hke_z15,1,true)
else
if(hke_Z0)then
call ForGroup(hke_Z8Z[hke_z15],function hke_zZ8Z)
else
call hke_zZ7Z(hke_z7[hke_z15])
endif
endif
endif
endif
endif
else
call hke_zZoZ("D")
endif
set hke_z05=null
endfunction
function hke_zzZZ takes unit hke_z65 returns nothing
call UnitSetConstructionProgress(hke_z65,100)
call UnitSetUpgradeProgress(hke_z65,100)
call UnitRemoveBuffs(hke_z65,false,true)
call UnitResetCooldown(hke_z65)
endfunction
function hke_zzzZ takes nothing returns nothing
local unit hke_z65=GetEnumUnit()
call hke_zzZZ(hke_z65)
set hke_z65=null
endfunction
function hke_zz0Z takes nothing returns nothing
local integer hke_z15
local player hke_z05
set hke_z05=GetTriggerPlayer()
set hke_z15=GetPlayerId(hke_z05)
if(hke_z4)then
if(hke_z6[hke_z15])then
set hke_zZZ[hke_z15]=true
if(hke_zzZ[hke_z15])then
call hke_z67(hke_z15,true)
else
if(hke_Z7[hke_z15])then
set hke_Z7[hke_z15]=false
call hke_Zz3Z(hke_z15,0,hke_zz,true)
else
if(hke_Z0)then
call ForGroup(hke_Z8Z[hke_z15],function hke_zzzZ)
else
call hke_zzZZ(hke_z7[hke_z15])
endif
endif
endif
endif
else
call hke_zZoZ("L")
endif
set hke_z05=null
endfunction
function hke_zz1Z takes unit hke_z65 returns nothing
call ModifyHeroStat(0,hke_z65,0,hke_zz)
call ModifyHeroStat(1,hke_z65,0,hke_zz)
call ModifyHeroStat(2,hke_z65,0,hke_zz)
endfunction
function hke_zz2Z takes nothing returns nothing
local unit hke_z65=GetEnumUnit()
call hke_zz1Z(hke_z65)
set hke_z65=null
endfunction
function hke_zz3Z takes nothing returns nothing
local integer hke_z15
local player hke_z05
set hke_z05=GetTriggerPlayer()
set hke_z15=GetPlayerId(hke_z05)
if(hke_z4)then
if(hke_z6[hke_z15])then
set hke_zzZ[hke_z15]=true
if(hke_zZZ[hke_z15])then
call hke_z67(hke_z15,true)
else
if(hke_Z7[hke_z15])then
set hke_Z7[hke_z15]=false
call hke_Zz3Z(hke_z15,2,hke_zz,true)
else
if((hke_Z1Z[hke_z15])and(hke_Z2Z[hke_z15]))then
if(hke_Z0)then
call ForGroup(hke_Z8Z[hke_z15],function hke_zz2Z)
else
call hke_zz1Z(hke_z7[hke_z15])
endif
else
call hke_zz5(hke_z05,hke_zZ,true)
call hke_z35(hke_z05,hke_Zz,true)
endif
endif
endif
endif
else
call hke_zZoZ("R")
endif
set hke_z05=null
endfunction
function hke_zz4Z takes nothing returns nothing
local player hke_z05=GetTriggerPlayer()
local integer hke_z15=GetPlayerId(hke_z05)
local button hke_z78=GetClickedButton()
call hke_Z44Z(hke_z15,hke_z05,false)
if((hke_z4)and(hke_z6[hke_z15]))then
if(hke_z78==hke_z2z[hke_z15])then
call hke_Z55Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z4z[hke_z15])then
call hke_Z46Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z5z[hke_z15])then
call hke_Z47Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z3z[hke_z15])then
call hke_Z6ZZ(hke_z15,hke_z05)
endif
if(hke_z78==hke_z9z[hke_z15])then
call hke_Z59Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z8z[hke_z15])then
call hke_Z5ZZ(hke_z15,hke_z05)
endif
if(hke_z78==hke_z7z[hke_z15])then
call hke_Z52Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z6z[hke_z15])then
call hke_Z51Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_Zz0[hke_z15])then
set hke_z13=false
call DoNotSaveReplay()
endif
endif
set hke_z05=null
set hke_z78=null
endfunction
function hke_zz5Z takes nothing returns nothing
local player hke_z05=GetTriggerPlayer()
local integer hke_z15=GetPlayerId(hke_z05)
local button hke_z78=GetClickedButton()
call hke_Z44Z(hke_z15,hke_z05,false)
if((hke_z4)and(hke_z6[hke_z15]))then
if(hke_z78==hke_z2z[hke_z15])then
call hke_ZZzZ(hke_z15,hke_z05)
call hke_Z55Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z4z[hke_z15])then
call hke_Zz1Z(hke_z05)
call hke_Z55Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z5z[hke_z15])then
call SetPlayerStateBJ(hke_z05,PLAYER_STATE_RESOURCE_FOOD_USED,5)
call hke_Z55Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z3z[hke_z15])then
call SetPlayerStateBJ(hke_z05,PLAYER_STATE_RESOURCE_FOOD_CAP,100)
call hke_Z55Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z9z[hke_z15])then
if(GetPlayerHandicapBJ(hke_z05)==200.)then
call SetPlayerHandicapBJ(hke_z05,100)
else
call SetPlayerHandicapBJ(hke_z05,200.)
endif
call hke_Z55Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z8z[hke_z15])then
if(GetPlayerHandicapXPBJ(hke_z05)==200.)then
call SetPlayerHandicapXPBJ(hke_z05,100)
else
call SetPlayerHandicapXPBJ(hke_z05,200.)
endif
call hke_Z55Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z7z[hke_z15])then
call hke_zz5(hke_z05,hke_Z2,true)
call hke_Z55Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z6z[hke_z15])then
call hke_z35(hke_z05,hke_z2,true)
call hke_Z55Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_Zz0[hke_z15])then
call hke_zz5(hke_z05,hke_Z2,false)
call hke_Z55Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_ZZ0[hke_z15])then
call hke_z35(hke_z05,hke_z2,false)
call hke_Z55Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_Z00[hke_z15])then
call hke_Z45Z(hke_z15,hke_z05)
endif
endif
set hke_z05=null
set hke_z78=null
endfunction
function hke_zz6Z takes nothing returns nothing
local player hke_z05=GetTriggerPlayer()
local integer hke_z15=GetPlayerId(hke_z05)
local button hke_z78=GetClickedButton()
call hke_Z44Z(hke_z15,hke_z05,false)
if((hke_z4)and(hke_z6[hke_z15]))then
if(hke_z78==hke_z2z[hke_z15])then
call hke_Z96(hke_z40[hke_z15])
call hke_Z46Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z4z[hke_z15])then
call hke_Z96(hke_z50[hke_z15])
call hke_Z46Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z5z[hke_z15])then
call hke_Z96(hke_z60[hke_z15])
call hke_Z46Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z3z[hke_z15])then
call hke_Z96(hke_z80[hke_z15])
call hke_Z46Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z9z[hke_z15])then
call hke_Z96(hke_z70[hke_z15])
call hke_Z46Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z8z[hke_z15])then
call hke_Z96(hke_z90[hke_z15])
call hke_Z46Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z7z[hke_z15])then
call hke_Z96(hke_ZZ3[hke_z15])
call hke_Z46Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z6z[hke_z15])then
call hke_z16(hke_z15,true)
call hke_Z46Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_Zz0[hke_z15])then
call hke_z16(hke_z15,false)
call hke_Z46Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_ZZ0[hke_z15])then
call hke_Z45Z(hke_z15,hke_z05)
endif
endif
set hke_z05=null
set hke_z78=null
endfunction
function hke_zz7Z takes nothing returns nothing
local player hke_z05=GetTriggerPlayer()
local integer hke_z15=GetPlayerId(hke_z05)
local button hke_z78=GetClickedButton()
call hke_Z44Z(hke_z15,hke_z05,false)
if((hke_z4)and(hke_z6[hke_z15]))then
if(hke_z78==hke_z2z[hke_z15])then
call hke_Z24Z(hke_z15,true)
call hke_Z47Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z4z[hke_z15])then
call hke_Z21Z(hke_z15,1097886070,true)
call hke_Z47Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z5z[hke_z15])then
call hke_Z26Z(hke_z15,true)
call hke_Z47Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z3z[hke_z15])then
call hke_Z21Z(hke_z15,1094937907,true)
call hke_Z47Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z9z[hke_z15])then
call hke_Z21Z(hke_z15,1098150517,true)
call hke_Z47Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z8z[hke_z15])then
call hke_Z29Z(hke_z15,true)
call hke_Z47Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z7z[hke_z15])then
call hke_Z49Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z6z[hke_z15])then
call hke_Z48Z(hke_z15,hke_z05)
endif
if((hke_z78==hke_Zz0[hke_z15])and((hke_z9Z)or(hke_z05==hke_z5)))then
call hke_Z3ZZ(hke_z15,true)
call hke_Z47Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_ZZ0[hke_z15])then
call hke_Z34Z(hke_z15)
call hke_Z47Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_Z00[hke_z15])then
call hke_Z45Z(hke_z15,hke_z05)
endif
endif
set hke_z05=null
set hke_z78=null
endfunction
function hke_zz8Z takes nothing returns nothing
local player hke_z05=GetTriggerPlayer()
local integer hke_z15=GetPlayerId(hke_z05)
local button hke_z78=GetClickedButton()
call hke_Z44Z(hke_z15,hke_z05,false)
if((hke_z4)and(hke_z6[hke_z15]))then
if(hke_z78==hke_z2z[hke_z15])then
call hke_Z21Z(hke_z15,1095659625,true)
call hke_Z48Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z4z[hke_z15])then
call hke_Z21Z(hke_z15,1095066998,true)
call hke_Z48Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z5z[hke_z15])then
call hke_Z21Z(hke_z15,1095262824,true)
call hke_Z48Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z3z[hke_z15])then
call hke_Z21Z(hke_z15,1095721842,true)
call hke_Z48Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z9z[hke_z15])then
call hke_Z21Z(hke_z15,1096119411,true)
call hke_Z48Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z8z[hke_z15])then
call hke_Z21Z(hke_z15,1095656289,true)
call hke_Z48Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z7z[hke_z15])then
call hke_Z21Z(hke_z15,1095657827,true)
call hke_Z48Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z6z[hke_z15])then
call hke_Z21Z(hke_z15,1095332722,true)
call hke_Z48Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_Zz0[hke_z15])then
call hke_Z21Z(hke_z15,1094935923,true)
call hke_Z48Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_ZZ0[hke_z15])then
call hke_Z47Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_Z00[hke_z15])then
call hke_Z45Z(hke_z15,hke_z05)
endif
endif
set hke_z05=null
set hke_z78=null
endfunction
function hke_zz9Z takes nothing returns nothing
local player hke_z05=GetTriggerPlayer()
local integer hke_z15=GetPlayerId(hke_z05)
local button hke_z78=GetClickedButton()
call hke_Z44Z(hke_z15,hke_z05,false)
if((hke_z4)and(hke_z6[hke_z15]))then
if(hke_z78==hke_z2z[hke_z15])then
call hke_Z21Z(hke_z15,1095262562,true)
call hke_Z49Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z4z[hke_z15])then
call hke_Z21Z(hke_z15,1095065960,true)
call hke_Z49Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z5z[hke_z15])then
call hke_Z21Z(hke_z15,1095721317,true)
call hke_Z49Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z3z[hke_z15])then
call hke_Z21Z(hke_z15,1095065970,true)
call hke_Z49Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z9z[hke_z15])then
call hke_Z21Z(hke_z15,1096114549,true)
call hke_Z49Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z8z[hke_z15])then
call hke_Z21Z(hke_z15,1096114550,true)
call hke_Z49Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z7z[hke_z15])then
call hke_Z21Z(hke_z15,1095262564,true)
call hke_Z49Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z6z[hke_z15])then
call hke_Z21Z(hke_z15,1094934883,true)
call hke_Z49Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_Zz0[hke_z15])then
call hke_Z21Z(hke_z15,1097818482,true)
call hke_Z49Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_ZZ0[hke_z15])then
call hke_Z21Z(hke_z15,1096905580,true)
call hke_Z49Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_Z00[hke_z15])then
call hke_Z31Z(hke_z15,false)
call hke_Z49Z(hke_z15,hke_z05)
endif
endif
set hke_z05=null
set hke_z78=null
endfunction
function hke_z0ZZ takes nothing returns nothing
local integer hke_Z75=0
local player hke_z05=GetTriggerPlayer()
local integer hke_z15=GetPlayerId(hke_z05)
local button hke_z78=GetClickedButton()
call hke_Z44Z(hke_z15,hke_z05,false)
if((hke_z4)and(hke_z05==hke_z5)and(hke_z6[hke_z15]))then
loop
exitwhen hke_Z75>11
if(hke_z78==hke_ZzZ[hke_Z75])then
if(hke_z6[hke_Z75])then
call hke_z47(hke_Z75)
else
call hke_z57(hke_Z75,Player(hke_Z75))
endif
call hke_Z5ZZ(hke_z15,hke_z05)
endif
set hke_Z75=hke_Z75+1
endloop
if(hke_z78==hke_z2z[hke_z15])then
call hke_Z45Z(hke_z15,hke_z05)
endif
endif
set hke_z05=null
set hke_z78=null
endfunction
function hke_z0zZ takes nothing returns nothing
local player hke_z05=GetTriggerPlayer()
local integer hke_z15=GetPlayerId(hke_z05)
local button hke_z78=GetClickedButton()
local integer hke_Z75=0
call hke_Z44Z(hke_z15,hke_z05,false)
if((hke_z4)and(hke_z05==hke_z5)and(hke_z6[hke_z15]))then
loop
exitwhen hke_Z75>12
if(hke_z78==hke_ZzZ[hke_Z75])then
set hke_Z5z=hke_Z75
call hke_Z53Z(hke_z15,hke_z05)
endif
set hke_Z75=hke_Z75+1
endloop
if(hke_z78==hke_z2z[hke_z15])then
call hke_Z45Z(hke_z15,hke_z05)
endif
endif
set hke_z05=null
set hke_z78=null
endfunction
function hke_z00Z takes nothing returns nothing
local player hke_z05=GetTriggerPlayer()
local integer hke_z15=GetPlayerId(hke_z05)
local button hke_z78=GetClickedButton()
local player hke_Z65
call hke_Z44Z(hke_z15,hke_z05,false)
if((hke_z4)and(hke_z05==hke_z5)and(hke_z6[hke_z15]))then
if(hke_z78==hke_z2z[hke_z15])then
call hke_Z56Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z4z[hke_z15])then
call hke_Z57Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z5z[hke_z15])then
set hke_Z65=Player(hke_Z5z)
if(GetPlayerTaxRate(hke_Z65,hke_z05,PLAYER_STATE_RESOURCE_GOLD)==0)then
call SetPlayerTaxRate(hke_Z65,hke_z05,PLAYER_STATE_RESOURCE_GOLD,hke_z22)
else
call SetPlayerTaxRate(hke_Z65,hke_z05,PLAYER_STATE_RESOURCE_GOLD,0)
endif
set hke_Z65=null
call hke_Z53Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z3z[hke_z15])then
set hke_Z65=Player(hke_Z5z)
if(GetPlayerTaxRate(hke_Z65,hke_z05,PLAYER_STATE_RESOURCE_LUMBER)==0)then
call SetPlayerTaxRate(hke_Z65,hke_z05,PLAYER_STATE_RESOURCE_LUMBER,hke_z22)
else
call SetPlayerTaxRate(hke_Z65,hke_z05,PLAYER_STATE_RESOURCE_LUMBER,0)
endif
set hke_Z65=null
call hke_Z53Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_Z00[hke_z15])then
call hke_Z52Z(hke_z15,hke_z05)
endif
endif
set hke_z05=null
set hke_z78=null
endfunction
function hke_z01Z takes nothing returns nothing
local player hke_z05=GetTriggerPlayer()
local integer hke_z15=GetPlayerId(hke_z05)
local button hke_z78=GetClickedButton()
local integer hke_Z75=hke_Z5z
local player hke_Z65=Player(hke_Z75)
call hke_Z44Z(hke_z15,hke_z05,false)
if((hke_z4)and(hke_z6[hke_z15]))then
if(hke_z78==hke_z2z[hke_z15])then
call hke_ZZzZ(hke_Z75,hke_Z65)
call hke_Z56Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z4z[hke_z15])then
call hke_Zz1Z(hke_Z65)
call hke_Z56Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z5z[hke_z15])then
call SetPlayerStateBJ(hke_Z65,PLAYER_STATE_RESOURCE_FOOD_USED,5)
call hke_Z56Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z3z[hke_z15])then
call SetPlayerStateBJ(hke_Z65,PLAYER_STATE_RESOURCE_FOOD_CAP,100)
call hke_Z56Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z9z[hke_z15])then
if(GetPlayerHandicapBJ(hke_Z65)==200.)then
call SetPlayerHandicapBJ(hke_Z65,100)
else
call SetPlayerHandicapBJ(hke_Z65,200.)
endif
call hke_Z56Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z8z[hke_z15])then
if(GetPlayerHandicapXPBJ(hke_Z65)==200.)then
call SetPlayerHandicapXPBJ(hke_Z65,100)
else
call SetPlayerHandicapXPBJ(hke_Z65,200.)
endif
call hke_Z56Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z7z[hke_z15])then
call hke_zz5(hke_Z65,hke_Z2,true)
call hke_Z56Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z6z[hke_z15])then
call hke_z35(hke_Z65,hke_z2,true)
call hke_Z56Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_Zz0[hke_z15])then
call hke_zz5(hke_Z65,hke_Z2,false)
call hke_Z56Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_ZZ0[hke_z15])then
call hke_z35(hke_Z65,hke_z2,false)
call hke_Z56Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_Z00[hke_z15])then
call hke_Z53Z(hke_z15,hke_z05)
endif
endif
set hke_z05=null
set hke_Z65=null
set hke_z78=null
endfunction
function hke_z02Z takes nothing returns nothing
local player hke_z05=GetTriggerPlayer()
local integer hke_z15=GetPlayerId(hke_z05)
local button hke_z78=GetClickedButton()
local integer hke_Z75=hke_Z5z
local player hke_Z65=Player(hke_Z75)
call hke_Z44Z(hke_z15,hke_z05,false)
if(hke_z78==hke_z2z[hke_z15])then
if(IsPlayerAlly(hke_Z65,hke_z05))then
call SetPlayerAllianceStateBJ(hke_Z65,hke_z05,0)
else
call SetPlayerAllianceStateBJ(hke_Z65,hke_z05,3)
endif
call hke_Z57Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z4z[hke_z15])then
if(GetPlayerAlliance(hke_Z65,hke_z05,ALLIANCE_SHARED_ADVANCED_CONTROL))then
call SetPlayerAllianceBJ(hke_Z65,ALLIANCE_SHARED_ADVANCED_CONTROL,false,hke_z5)
call SetPlayerAllianceBJ(hke_Z65,ALLIANCE_SHARED_CONTROL,false,hke_z5)
else
call SetPlayerAllianceBJ(hke_Z65,ALLIANCE_SHARED_ADVANCED_CONTROL,true,hke_z5)
call SetPlayerAllianceBJ(hke_Z65,ALLIANCE_SHARED_CONTROL,true,hke_z5)
endif
call hke_Z57Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z5z[hke_z15])then
if(GetPlayerAlliance(hke_Z65,hke_z05,ALLIANCE_SHARED_XP))then
call SetPlayerAllianceBJ(hke_Z65,ALLIANCE_SHARED_XP,false,hke_z5)
else
call SetPlayerAllianceBJ(hke_Z65,ALLIANCE_SHARED_XP,true,hke_z5)
endif
call hke_Z57Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z3z[hke_z15])then
if(IsPlayerAlly(hke_z05,hke_Z65))then
call SetPlayerAllianceStateBJ(hke_z5,hke_Z65,0)
else
call SetPlayerAllianceStateBJ(hke_z5,hke_Z65,2)
endif
call hke_Z57Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z9z[hke_z15])then
call hke_Z53Z(hke_z15,hke_z05)
endif
set hke_z05=null
set hke_Z65=null
set hke_z78=null
endfunction
function hke_z03Z takes nothing returns nothing
local player hke_z05=GetTriggerPlayer()
local integer hke_z15=GetPlayerId(hke_z05)
local button hke_z78=GetClickedButton()
local integer hke_Z75
local unit hke_z65=hke_z7[hke_z15]
local player hke_Z65=GetOwningPlayer(hke_z65)
call hke_Z44Z(hke_z15,hke_z05,false)
if(hke_z4)and(hke_z6[hke_z15])then
if(hke_z78==hke_z2z[hke_z15])then
call SetHeroLevelBJ(hke_z65,GetHeroLevel(hke_z65)+hke_Z0Z,false)
endif
if(hke_z78==hke_z4z[hke_z15])then
call ModifyHeroStat(1,hke_z65,0,hke_Z3)
call ModifyHeroStat(0,hke_z65,0,hke_Z3)
call ModifyHeroStat(2,hke_z65,0,hke_Z3)
endif
if(hke_z78==hke_z5z[hke_z15])then
call hke_z98(hke_z15,false)
endif
if(hke_z78==hke_z3z[hke_z15])then
call hke_Z77(hke_z65,hke_z05,1)
endif
if(hke_z78==hke_z9z[hke_z15])then
call hke_ZZ3Z(hke_z65)
endif
if(hke_z78==hke_z8z[hke_z15])then
if(hke_Z5Z)then
if(hke_Z65!=hke_z5)then
call UnitShareVisionBJ(true,hke_z65,hke_z05)
endif
else
call UnitShareVisionBJ(true,hke_z65,hke_z05)
endif
endif
if(hke_z78==hke_z7z[hke_z15])then
call hke_Z47Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z6z[hke_z15])then
if(hke_Z5Z)then
if(hke_Z65!=hke_z5)then
call SetUnitOwner(hke_z65,hke_z05,true)
endif
else
call SetUnitOwner(hke_z65,hke_z05,true)
endif
endif
if(hke_z78==hke_Zz0[hke_z15])then
call RemoveUnit(hke_z65)
endif
if(hke_z78==hke_ZZ0[hke_z15])then
call hke_Z54Z(hke_z15,hke_z05)
endif
endif
set hke_z05=null
set hke_Z65=null
set hke_z65=null
set hke_z78=null
endfunction
function hke_z04Z takes nothing returns nothing
local player hke_z05=GetTriggerPlayer()
local integer hke_z15=GetPlayerId(hke_z05)
local button hke_z78=GetClickedButton()
call hke_Z44Z(hke_z15,hke_z05,false)
if((hke_z4)and(hke_z05==hke_z5)and(hke_z6[hke_z15]))then
if(hke_z78==hke_z2z[hke_z15])then
set hke_Z0=not(hke_Z0)
call hke_Z51Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z4z[hke_z15])then
call hke_Z58Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z5z[hke_z15])then
set hke_Z5Z=not(hke_Z5Z)
call hke_Z51Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z3z[hke_z15])then
set hke_Z6Z=not(hke_Z6Z)
call hke_Z51Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z9z[hke_z15])then
set hke_Z7Z=not(hke_Z7Z)
call hke_Z51Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z8z[hke_z15])then
set hke_z9Z=not(hke_z9Z)
call hke_Z51Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z7z[hke_z15])then
set hke_ZZz=not(hke_ZZz)
call hke_Z51Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z6z[hke_z15])then
set hke_z7Z=not(hke_z7Z)
call hke_Z51Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_Zz0[hke_z15])then
set hke_Z52=not(hke_Z52)
call hke_Z51Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_ZZ0[hke_z15])then
call hke_Z45Z(hke_z15,hke_z05)
endif
endif
set hke_z05=null
set hke_z78=null
endfunction
function hke_z05Z takes nothing returns nothing
local player hke_z05=GetTriggerPlayer()
local integer hke_z15=GetPlayerId(hke_z05)
local button hke_z78=GetClickedButton()
call hke_Z44Z(hke_z15,hke_z05,false)
if(hke_z78==hke_z2z[hke_z15])then
set hke_z61=1
call hke_Z58Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z4z[hke_z15])then
set hke_z61=2
call hke_Z58Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z5z[hke_z15])then
set hke_z61=3
call hke_Z58Z(hke_z15,hke_z05)
endif
if(hke_z78==hke_z3z[hke_z15])then
call hke_Z51Z(hke_z15,hke_z05)
endif
set hke_z05=null
set hke_z78=null
endfunction
function hke_z06Z takes nothing returns nothing
local player hke_z05=GetTriggerPlayer()
local integer hke_z15=GetPlayerId(hke_z05)
local button hke_z78=GetClickedButton()
local integer hke_Z75=0
local player hke_Z65
local unit hke_z65=hke_z7[hke_z15]
call hke_Z44Z(hke_z15,hke_z05,false)
if((hke_z4)and(hke_z05==hke_z5)and(hke_z6[hke_z15]))then
loop
exitwhen hke_Z75>12
if(hke_z78==hke_ZzZ[hke_Z75])then
set hke_Z65=Player(hke_Z75)
call SetUnitOwner(hke_z7[hke_z15],hke_Z65,true)
endif
set hke_Z75=hke_Z75+1
endloop
if(hke_z78==hke_z2z[hke_z15])then
call hke_Z50Z(hke_z15,hke_z05)
endif
endif
set hke_z05=null
set hke_Z65=null
set hke_z78=null
set hke_z65=null
endfunction
function hke_z07Z takes nothing returns nothing
local player hke_z05=GetTriggerPlayer()
local integer hke_z15=GetPlayerId(hke_z05)
local button hke_z78=GetClickedButton()
call hke_Z44Z(hke_z15,hke_z05,false)
if(hke_z78==hke_z2z[hke_z15])then
call hke_z36(hke_z05)
call hke_Z6ZZ(hke_z15,hke_z05)
endif
if(hke_z78==hke_z4z[hke_z15])then
set hke_z31[hke_z15]=not(hke_z31[hke_z15])
call hke_Z6ZZ(hke_z15,hke_z05)
endif
if(hke_z78==hke_z5z[hke_z15])then
set hke_Z33[hke_z15]=not(hke_Z33[hke_z15])
call hke_Z6ZZ(hke_z15,hke_z05)
endif
if(hke_z78==hke_z3z[hke_z15])then
call hke_Z38(hke_z15,not(hke_Z53[hke_z15]))
call hke_Z6ZZ(hke_z15,hke_z05)
endif
if(hke_z78==hke_z9z[hke_z15])then
set hke_Z63[hke_z15]=not(hke_Z63[hke_z15])
call hke_Z6ZZ(hke_z15,hke_z05)
endif
if(hke_z78==hke_z8z[hke_z15])then
set hke_Z43[hke_z15]=not(hke_Z43[hke_z15])
call hke_Z6ZZ(hke_z15,hke_z05)
endif
if(hke_z78==hke_Z00[hke_z15])then
call hke_Z45Z(hke_z15,hke_z05)
endif
set hke_z05=null
set hke_z78=null
endfunction
function hke_z08Z takes nothing returns nothing
local player hke_z05=GetTriggerPlayer()
local integer hke_z15=GetPlayerId(hke_z05)
local button hke_z78=GetClickedButton()
call hke_Z44Z(hke_z15,hke_z05,false)
if(hke_z78==hke_z2z[hke_z15])then
call hke_Z6zZ(hke_z05)
endif
if(hke_z78==hke_z4z[hke_z15])then
call hke_Z60Z(hke_z05)
endif
if(hke_z78==hke_z5z[hke_z15])then
call hke_Z61Z(hke_z05)
endif
if(hke_z78==hke_z3z[hke_z15])then
call hke_Z62Z(hke_z05)
endif
if(hke_z78==hke_z9z[hke_z15])then
call hke_Z64Z()
endif
if(hke_z78==hke_Z00[hke_z15])then
call hke_Z45Z(hke_z15,hke_z05)
endif
set hke_z05=null
set hke_z78=null
endfunction
function hke_z09Z takes nothing returns nothing
local integer hke_Z75
local player hke_Z65
local player hke_z05
set hke_z73=CreateTrigger()
call TriggerRegisterAnyUnitEventBJ(hke_z73,EVENT_PLAYER_UNIT_ATTACKED)
call TriggerAddAction(hke_z73,function hke_Z9ZZ)
call TriggerAddCondition(hke_z43,Condition(function hke_Z73Z))
set hke_Z75=0
loop
exitwhen hke_Z75>11
set hke_zz1[hke_Z75]=CreateTrigger()
call TriggerAddAction(hke_zz1[hke_Z75],function hke_Z79Z)
call DisableTrigger(hke_zz1[hke_Z75])
set hke_Z30[hke_Z75]=CreateTrigger()
call TriggerAddAction(hke_Z30[hke_Z75],function hke_Z88Z)
call DisableTrigger(hke_Z30[hke_Z75])
set hke_Z50[hke_Z75]=CreateTrigger()
call TriggerAddAction(hke_Z50[hke_Z75],function hke_Z89Z)
call DisableTrigger(hke_Z50[hke_Z75])
set hke_Z40[hke_Z75]=CreateTrigger()
call TriggerAddAction(hke_Z40[hke_Z75],function hke_Z91Z)
call DisableTrigger(hke_Z40[hke_Z75])
set hke_Z60[hke_Z75]=CreateTrigger()
call TriggerAddAction(hke_Z60[hke_Z75],function hke_Z90Z)
call DisableTrigger(hke_Z60[hke_Z75])
set hke_Z6z[hke_Z75]=CreateTrigger()
call TriggerAddAction(hke_Z6z[hke_Z75],function hke_Z9zZ)
call DisableTrigger(hke_Z6z[hke_Z75])
set hke_Z70[hke_Z75]=CreateTrigger()
call TriggerAddAction(hke_Z70[hke_Z75],function hke_zZ1Z)
call DisableTrigger(hke_Z70[hke_Z75])
set hke_Z80[hke_Z75]=CreateTrigger()
call TriggerAddAction(hke_Z80[hke_Z75],function hke_zZ2Z)
call DisableTrigger(hke_Z80[hke_Z75])
set hke_Z90[hke_Z75]=CreateTrigger()
call TriggerAddAction(hke_Z90[hke_Z75],function hke_zZ3Z)
call DisableTrigger(hke_Z90[hke_Z75])
set hke_zZ0[hke_Z75]=CreateTrigger()
call TriggerAddAction(hke_zZ0[hke_Z75],function hke_zZ4Z)
call DisableTrigger(hke_zZ0[hke_Z75])
set hke_zz0[hke_Z75]=CreateTrigger()
call TriggerAddAction(hke_zz0[hke_Z75],function hke_zZ5Z)
set hke_zo0[hke_Z75]=CreateTrigger()
call TriggerAddAction(hke_zo0[hke_Z75],function hke_zZOZ)
call DisableTrigger(hke_zz0[hke_Z75])
set hke_z00[hke_Z75]=CreateTrigger()
call TriggerAddAction(hke_z00[hke_Z75],function hke_zZ6Z)
set hke_z10[hke_Z75]=CreateTrigger()
call TriggerAddAction(hke_z10[hke_Z75],function hke_zZ9Z)
set hke_z20[hke_Z75]=CreateTrigger()
call TriggerAddAction(hke_z20[hke_Z75],function hke_zz0Z)
set hke_z30[hke_Z75]=CreateTrigger()
call TriggerAddAction(hke_z30[hke_Z75],function hke_zz3Z)
set hke_z40[hke_Z75]=CreateTrigger()
call TriggerAddAction(hke_z40[hke_Z75],function hke_Z81Z)
call DisableTrigger(hke_z40[hke_Z75])
set hke_z50[hke_Z75]=CreateTrigger()
call TriggerAddAction(hke_z50[hke_Z75],function hke_Z82Z)
call DisableTrigger(hke_z50[hke_Z75])
set hke_z60[hke_Z75]=CreateTrigger()
call TriggerAddAction(hke_z60[hke_Z75],function hke_Z83Z)
call DisableTrigger(hke_z60[hke_Z75])
set hke_z70[hke_Z75]=CreateTrigger()
call TriggerAddAction(hke_z70[hke_Z75],function hke_Z84Z)
call DisableTrigger(hke_z70[hke_Z75])
set hke_z80[hke_Z75]=CreateTrigger()
call TriggerAddAction(hke_z80[hke_Z75],function hke_Z85Z)
call DisableTrigger(hke_z80[hke_Z75])
set hke_z90[hke_Z75]=CreateTrigger()
call TriggerAddAction(hke_z90[hke_Z75],function hke_Z86Z)
call DisableTrigger(hke_z90[hke_Z75])
set hke_ZZ3[hke_Z75]=CreateTrigger()
call TriggerAddAction(hke_ZZ3[hke_Z75],function hke_Z87Z)
call DisableTrigger(hke_ZZ3[hke_Z75])
set hke_ZZ1[hke_Z75]=CreateTrigger()
call TriggerAddAction(hke_ZZ1[hke_Z75],function hke_zz4Z)
set hke_Zz2[hke_Z75]=CreateTrigger()
call TriggerAddAction(hke_Zz2[hke_Z75],function hke_zz5Z)
set hke_Zz1[hke_Z75]=CreateTrigger()
call TriggerAddAction(hke_Zz1[hke_Z75],function hke_zz6Z)
set hke_Z01[hke_Z75]=CreateTrigger()
call TriggerAddAction(hke_Z01[hke_Z75],function hke_zz7Z)
set hke_Z81[hke_Z75]=CreateTrigger()
call TriggerAddAction(hke_Z81[hke_Z75],function hke_zz8Z)
set hke_Z21[hke_Z75]=CreateTrigger()
call TriggerAddAction(hke_Z21[hke_Z75],function hke_zz9Z)
set hke_Z51[hke_Z75]=CreateTrigger()
call TriggerAddAction(hke_Z51[hke_Z75],function hke_z0ZZ)
set hke_Z41[hke_Z75]=CreateTrigger()
call TriggerAddAction(hke_Z41[hke_Z75],function hke_z0zZ)
set hke_Z61[hke_Z75]=CreateTrigger()
call TriggerAddAction(hke_Z61[hke_Z75],function hke_z00Z)
set hke_Z12[hke_Z75]=CreateTrigger()
call TriggerAddAction(hke_Z12[hke_Z75],function hke_z02Z)
set hke_Z02[hke_Z75]=CreateTrigger()
call TriggerAddAction(hke_Z02[hke_Z75],function hke_z01Z)
set hke_Z71[hke_Z75]=CreateTrigger()
call TriggerAddAction(hke_Z71[hke_Z75],function hke_z03Z)
set hke_Z31[hke_Z75]=CreateTrigger()
call TriggerAddAction(hke_Z31[hke_Z75],function hke_z04Z)
set hke_Z22[hke_Z75]=CreateTrigger()
call TriggerAddAction(hke_Z22[hke_Z75],function hke_z05Z)
set hke_Z11[hke_Z75]=CreateTrigger()
call TriggerAddAction(hke_Z11[hke_Z75],function hke_z06Z)
set hke_Z23[hke_Z75]=CreateTrigger()
call TriggerAddAction(hke_Z23[hke_Z75],function hke_z08Z)
set hke_Z13[hke_Z75]=CreateTrigger()
call TriggerAddAction(hke_Z13[hke_Z75],function hke_z07Z)
call DisableTrigger(hke_ZZ1[hke_Z75])
call DisableTrigger(hke_Zz1[hke_Z75])
call DisableTrigger(hke_Zz2[hke_Z75])
call DisableTrigger(hke_Z01[hke_Z75])
call DisableTrigger(hke_Z81[hke_Z75])
call DisableTrigger(hke_Z21[hke_Z75])
call DisableTrigger(hke_Z51[hke_Z75])
call DisableTrigger(hke_Z41[hke_Z75])
call DisableTrigger(hke_Z61[hke_Z75])
call DisableTrigger(hke_Z12[hke_Z75])
call DisableTrigger(hke_Z02[hke_Z75])
call DisableTrigger(hke_Z71[hke_Z75])
call DisableTrigger(hke_Z31[hke_Z75])
call DisableTrigger(hke_Z22[hke_Z75])
call DisableTrigger(hke_Z11[hke_Z75])
call DisableTrigger(hke_Z23[hke_Z75])
call DisableTrigger(hke_Z13[hke_Z75])
set hke_z01[hke_Z75]=CreateTrigger()
call TriggerAddAction(hke_z01[hke_Z75],function hke_Z95Z)
set hke_z11[hke_Z75]=CreateTrigger()
call TriggerAddAction(hke_z11[hke_Z75],function hke_Z98Z)
set hke_z21[hke_Z75]=CreateTrigger()
call TriggerAddAction(hke_z21[hke_Z75],function hke_zZZZ)
call DisableTrigger(hke_z01[hke_Z75])
call DisableTrigger(hke_z11[hke_Z75])
call DisableTrigger(hke_z21[hke_Z75])
set hke_Z65=Player(hke_Z75)
if((GetPlayerController(hke_Z65)==MAP_CONTROL_USER)and(GetPlayerSlotState(hke_Z65)==PLAYER_SLOT_STATE_PLAYING))then
set hke_Z8Z[hke_Z75]=CreateGroup()
call TriggerRegisterPlayerStateEvent(hke_z63,hke_Z65,PLAYER_STATE_RESOURCE_FOOD_USED,LESS_THAN,0)
call TriggerRegisterPlayerEventEndCinematic(hke_zo0[hke_Z75],hke_Z65)
call TriggerRegisterPlayerKeyEventBJ(hke_z10[hke_Z75],hke_Z65,0,2)   
call TriggerRegisterPlayerKeyEventBJ(hke_z00[hke_Z75],hke_Z65,0,3)     
call TriggerRegisterPlayerKeyEventBJ(hke_z20[hke_Z75],hke_Z65,0,0)    
call TriggerRegisterPlayerKeyEventBJ(hke_z30[hke_Z75],hke_Z65,0,1)     
call TriggerRegisterPlayerChatEvent(hke_z53,hke_Z65,SubStringBJ(hke_Z0z,139,146),false)
call TriggerRegisterPlayerStateEvent(hke_z63,hke_Z65,PLAYER_STATE_RESOURCE_FOOD_USED,LESS_THAN,0)
set hke_Z9Z[hke_Z75]=GetPlayerStartLocationLoc(hke_Z65)
endif
set hke_Z75=hke_Z75+1
endloop
call DisableTrigger(hke_z73)
set hke_z8Z=CreateGroup()
set hke_z8=GetWorldBounds()
set hke_z2Z[0]=30.
set hke_z2Z[1]=60.
set hke_z2Z[2]=90.
set hke_z3Z[0]=50.
set hke_z3Z[1]=72.
set hke_z3Z[2]=95.
set hke_Z75=0
loop
exitwhen hke_Z75>20
set hke_z02[hke_Z75]=null
set hke_Z75=hke_Z75+1
endloop
set hke_Z75=0
loop
exitwhen(hke_Z75>12)
set hke_Z5[hke_Z75]=0
set hke_z6[hke_Z75]=false
set hke_Z7[hke_Z75]=false
set hke_Z8[hke_Z75]=0
set hke_Z1Z[hke_Z75]=false
set hke_Z2Z[hke_Z75]=false
set hke_Z3Z[hke_Z75]=CreateTimer()
set hke_Z8Z[hke_Z75]=CreateGroup()
set hke_zZZ[hke_Z75]=false
set hke_zzZ[hke_Z75]=false
set hke_z0Z[hke_Z75]=CreateTimer()
set hke_z1Z[hke_Z75]=false
set hke_Z3z[hke_Z75]=false
set hke_Z4z[hke_Z75]=0
set hke_Z20[hke_Z75]=DialogCreate()
set hke_Z91[hke_Z75]=DialogCreate()
set hke_zZ1[hke_Z75]=DialogCreate()
set hke_z31[hke_Z75]=false
set hke_Z32[hke_Z75]=0
set hke_Z42[hke_Z75]=false
set hke_Zz3[hke_Z75]=DialogCreate()
set hke_Z33[hke_Z75]=false
set hke_Z43[hke_Z75]=true
set hke_Z53[hke_Z75]=false
set hke_Z63[hke_Z75]=false
set hke_Z73[hke_Z75]=CreateTimer()
set hke_Z75=hke_Z75+1
endloop
set hke_Z75=0
loop
exitwhen(hke_Z75>3)
set hke_Z75=hke_Z75+1
endloop
set hke_Z75=0
loop
exitwhen(hke_Z75>21)
set hke_z12[hke_Z75]=false
set hke_Z75=hke_Z75+1
endloop
call TriggerRegisterTimerEvent(hke_z23,.01,false)
call TriggerAddAction(hke_z23,function hke_Z7zZ)
call TriggerAddAction(hke_z33,function hke_Z70Z)
call TriggerAddAction(hke_z43,function hke_Z74Z)
call TriggerAddAction(hke_z53,function hke_Z8zZ)
call TriggerAddAction(hke_z63,function hke_Z80Z)
call TriggerRegisterAnyUnitEventBJ(hke_z73,EVENT_PLAYER_UNIT_ATTACKED)
call TriggerAddAction(hke_z73,function hke_Z9ZZ)
call TriggerRegisterAnyUnitEventBJ(hke_z83,EVENT_PLAYER_UNIT_ATTACKED)
call TriggerAddAction(hke_z83,function hke_Z93Z)
call hke_Name()
call DisableTrigger(hke_z83)
call hke_Z69Z()
call SetPlayerName(Player(12),"Neutral Creeps")
set hke_Z65=null
endfunction

// function main
call hke_z09Z()
