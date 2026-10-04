// globals
group array fgact
player array fpact
boolean array fbact
trigger array ftact
hashtable array fhact
string array fsact
dialog array fdact
button array fuact
// endglobals

function Fukki_Trigger_Destroy1 takes integer fi2i,integer fi3i,integer fi4i,integer fi5i,integer fi6i,boolean fb2b,boolean fb3b returns nothing
if fb3b then
set fpact[fi2i+fi3i]=Player(fi2i)
set fbact[fi2i+fi3i]=fbact[1]
else
set fpact[fi2i+fi3i]=null
set fbact[fi2i+fi3i]=fbact[2]
if fb2b then
call TriggerRemoveAction(ftact[fi2i+fi3i],LoadTriggerActionHandle(fhact[2],fi4i,fi2i))
call SaveTriggerActionHandle(fhact[2],fi4i,fi2i,null)
call DestroyTrigger(ftact[fi2i+fi3i])
endif
endif
endfunction
function Fukki_Trigger_Check takes integer fi2i,integer fi3i,integer fi4i,integer fi5i,integer fi6i,boolean fb2b returns nothing
local player fp2p=Player(fi2i)
if fi5i!=0and fi3i==fi5i and null!=fpact[fi2i+fi3i]and fi6i==0then
call Fukki_Trigger_Destroy1(fi2i,fi3i,fi4i,fi5i,fi6i,fb2b,fbact[2])
elseif fi5i!=0and fi3i==fi5i then
call Fukki_Trigger_Destroy1(fi2i,fi3i,fi4i,fi5i,fi6i,fb2b,fbact[1])
elseif fbact[fi2i+fi3i]then
call Fukki_Trigger_Destroy1(fi2i,fi3i,fi4i,fi5i,fi6i,fb2b,fbact[2])
else
call Fukki_Trigger_Destroy1(fi2i,fi3i,fi4i,fi5i,fi6i,fb2b,fbact[1])
endif
endfunction
function Fukki_Trigger_Destroy2 takes integer fi2i,integer fi3i,integer fi4i,boolean fb2b returns nothing
local integer fi5i=LoadInteger(fhact[1],fi3i,fi4i+1)
if fb2b then
call SaveInteger(fhact[1],fi3i,fi4i+1,fi5i+1)
else
call SaveInteger(fhact[1],fi3i,fi4i+1,fi5i-1)
set fi5i=LoadInteger(fhact[1],fi3i,fi4i+1)
if fi5i<=0then
call TriggerRemoveAction(ftact[fi2i],LoadTriggerActionHandle(fhact[2],fi3i,fi4i))
call SaveTriggerActionHandle(fhact[2],fi3i,fi4i,null)
call DestroyTrigger(ftact[fi2i])
call SaveInteger(fhact[1],fi3i,fi4i,0)
call SaveInteger(fhact[1],fi3i+1,fi4i,0)
endif
endif
endfunction
function Fukki_Button1 takes integer fi2i returns integer
return fi2i*20
endfunction
function Fukki_Player_Color takes integer fi2i returns string
if fi2i<12then
set fi2i=fi2i*6
return SubString("FF00000000FF00FFFFA020F0FFFF00FFA50000FF00FF14936969699AC0CD0064008B4513",fi2i,fi2i+6)
endif
return"FFFFFF"
endfunction
function Fukki_Button2 takes integer fi2i,integer fi3i,integer fi4i,string fs2s returns nothing
set fuact[Fukki_Button1(fi2i)+fi3i]=DialogAddButton(fdact[fi2i+fi4i],fs2s,0)
endfunction
function Fukki_Action1 takes integer fi2i,integer fi3i,integer fi4i,code fc2c returns nothing
call SaveTriggerActionHandle(fhact[2],fi2i,fi3i,TriggerAddAction(ftact[fi3i+fi4i],fc2c))
endfunction
function Fukki_Action2 takes integer fi2i,integer fi3i,integer fi4i,code fc2c returns nothing
call SaveTriggerActionHandle(fhact[2],fi2i,fi3i,TriggerAddAction(ftact[fi4i],fc2c))
endfunction
function Fukki_Text takes player fp2p,string fs2s returns nothing
call DisplayTimedTextToPlayer(fp2p,0,0,LoadReal(fhact[0],0,0),fs2s)
endfunction
function Fukki_Dialog takes integer fi2i,integer fi3i,integer fi4i,string fs2s,code fc2c returns nothing
if fbact[1]!=fbact[fi2i+fi3i]then
set fdact[fi2i+fi3i]=DialogCreate()
set ftact[fi2i+fi3i]=CreateTrigger()
call TriggerRegisterDialogEvent(ftact[fi2i+fi3i],fdact[fi2i+fi3i])
call Fukki_Action1(fi4i,fi2i,fi3i,fc2c)
call Fukki_Trigger_Check(fi2i,fi3i,fi4i,0,0,fbact[1])
endif
call DialogClear(fdact[fi2i+fi3i])
call DialogSetMessage(fdact[fi2i+fi3i],fs2s)
endfunction
function Fukki_Custom_Table takes integer fi2i,integer fi3i,integer fi4i,string fs2s,code fc2c returns nothing
call DisplayTimedTextToPlayer(Player(fi2i),0,0,15,fs2s)
if fbact[1]!=fbact[fi2i+fi3i]then
set ftact[fi2i+fi3i]=CreateTrigger()
call TriggerRegisterPlayerChatEvent(ftact[fi2i+fi3i],Player(fi2i),"",false)
call Fukki_Action1(fi4i,fi2i,fi3i,fc2c)
call Fukki_Trigger_Check(fi2i,fi3i,fi4i,0,0,fbact[1])
endif
endfunction
function Fukki_Share_Player takes integer fi2i returns integer
if LoadBoolean(fhact[1],255,fi2i)then
call DisplayTimedTextToPlayer(Player(fi2i),0,0,10,"|cffffcc00Share Option:|r |cff"+Fukki_Player_Color(LoadInteger(fhact[1],255,fi2i))+GetPlayerName(Player(LoadInteger(fhact[1],255,fi2i)))+"|r")
set fi2i=LoadInteger(fhact[1],255,fi2i)
endif
return fi2i
endfunction
function Fukki_Gold_Rate7 takes nothing returns nothing
local playerstate fstat=ConvertPlayerState(1)
local trigger ft2t=GetTriggeringTrigger()
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=GetPlayerState(fp2p,fstat)
local integer fi4i=LoadInteger(fhact[1],1,fi2i)
local integer fi5i=LoadInteger(fhact[0],1,fi2i)
call DisableTrigger(ftact[50+fi2i])
call DisableTrigger(ftact[950+fi2i])
if fi3i>fi5i and fbact[50+fi2i]then
set fi3i=R2I(fi3i+((fi3i-fi5i)*(I2R(fi4i)/100)))
call SetPlayerState(fp2p,fstat,fi3i)
endif
if fi5i>fi3i and fbact[950+fi2i]then
set fi3i=(fi5i-fi3i)+fi3i
call SetPlayerState(fp2p,fstat,fi3i)
endif
call SaveInteger(fhact[0],1,fi2i,fi3i)
call EnableTrigger(ftact[950+fi2i])
call EnableTrigger(ftact[50+fi2i])
endfunction
function Fukki_Gold_Rate4 takes integer fi2i,integer fi3i,integer fi4i,integer fi5i returns nothing
local player fp2p=Player(fi2i)
if fbact[1]!=fbact[fi2i+fi3i]then
set ftact[fi2i+fi3i]=CreateTrigger()
call TriggerRegisterPlayerStateEvent(ftact[fi2i+fi3i],fp2p,ConvertPlayerState(1),ConvertLimitOp(4),0)
call Fukki_Action1(fi5i,fi2i,fi3i,function Fukki_Gold_Rate7)
endif
call Fukki_Trigger_Check(fi2i,fi3i,fi5i,fi3i,fi4i,fbact[1])
endfunction
function Fukki_Gold_Rate6 takes nothing returns nothing
local integer fi3i=S2I(GetEventPlayerChatString())
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi4i=Fukki_Share_Player(fi2i)
if fi3i<0then
set fi3i=0
endif
call SaveInteger(fhact[1],1,fi4i,fi3i)
call Fukki_Gold_Rate4(fi4i,50,fi3i,3)
call Fukki_Text(fp2p,"|cffffcc00Gold Rate:|r +"+I2S(fi3i)+"%")
call Fukki_Trigger_Check(fi2i,70,4,0,0,fbact[1])
call ExecuteFunc("Fukki_Gold_Rate1")
endfunction
function Fukki_Gold_Rate3 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=LoadInteger(fhact[1],0,1)
local integer fi6i=Fukki_Share_Player(fi2i)
local integer fi4i=LoadInteger(fhact[1],1,fi6i)
local integer fi5i=Fukki_Button1(fi2i)
local button fb2b=GetClickedButton()
if fb2b==fuact[fi5i+0]then
call SaveInteger(fhact[1],1,fi6i,0)
call Fukki_Gold_Rate4(fi6i,50,0,3)
call ExecuteFunc("Fukki_Main_Menu1")
elseif fb2b==fuact[fi5i+1]then
call ExecuteFunc("Fukki_Main_Menu1")
elseif fb2b==fuact[fi5i+2]then
set fi4i=fi4i+fi3i
call SaveInteger(fhact[1],1,fi6i,fi4i)
call Fukki_Gold_Rate4(fi6i,50,fi4i,3)
call ExecuteFunc("Fukki_Gold_Rate1")
elseif fb2b==fuact[fi5i+3]then
set fi4i=fi4i-fi3i
if fi4i<0then
set fi4i=0
endif
call SaveInteger(fhact[1],1,fi6i,fi4i)
call Fukki_Gold_Rate4(fi6i,50,fi4i,3)
call ExecuteFunc("Fukki_Gold_Rate1")
elseif fb2b==fuact[fi5i+4]then
call Fukki_Custom_Table(fi2i,70,4,"|cffffcc00ENTER GOLD RATE|r",function Fukki_Gold_Rate6)
elseif fb2b==fuact[fi5i+5]then
call ExecuteFunc("Fukki_Main_Menu1")
endif
endfunction
function Fukki_Gold_Rate1 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=LoadInteger(fhact[1],0,1)
local integer fi4i=Fukki_Share_Player(fi2i)
call Fukki_Dialog(fi2i,30,2,"|cffffcc00FukKi CP [Gold Rate]|r",function Fukki_Gold_Rate3)
if fbact[fi4i+50]then
call Fukki_Button2(fi2i,0,30,"|cffffcc00Disable|r")
endif
call Fukki_Button2(fi2i,1,30,"|cffffcc00"+I2S(LoadInteger(fhact[1],1,fi4i))+"%|r")
call Fukki_Button2(fi2i,2,30,"|cffffffff+"+I2S(fi3i)+"%|r")
call Fukki_Button2(fi2i,3,30,"|cffffffff-"+I2S(fi3i)+"%|r")
call Fukki_Button2(fi2i,4,30,"|cffffcc00Custom|r")
call Fukki_Button2(fi2i,5,30,"|cffffcc00Back|r")
call DialogDisplay(fp2p,fdact[fi2i+30],fbact[1])
endfunction
function Fukki_Lumber_Rate7 takes nothing returns nothing
local playerstate fstat=ConvertPlayerState(2)
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=GetPlayerState(fp2p,fstat)
local integer fi4i=LoadInteger(fhact[1],2,fi2i)
local integer fi5i=LoadInteger(fhact[0],2,fi2i)
call DisableTrigger(ftact[fi2i+110])
call DisableTrigger(ftact[fi2i+970])
if fi3i>fi5i and fbact[50+fi2i]then
set fi3i=R2I(fi3i+((fi3i-fi5i)*(I2R(fi4i)/100)))
call SetPlayerState(fp2p,fstat,fi3i)
endif
if fi5i>fi3i and fbact[970+fi2i]then
set fi3i=(fi5i-fi3i)+fi3i
call SetPlayerState(fp2p,fstat,fi3i)
endif
call SaveInteger(fhact[0],2,fi2i,fi3i)
call EnableTrigger(ftact[fi2i+970])
call EnableTrigger(ftact[fi2i+110])
endfunction
function Fukki_Lumber_Rate4 takes integer fi2i,integer fi3i,integer fi4i,integer fi5i returns nothing
local player fp2p=Player(fi2i)
if fbact[1]!=fbact[fi2i+fi3i]then
set ftact[fi2i+fi3i]=CreateTrigger()
call TriggerRegisterPlayerStateEvent(ftact[fi2i+fi3i],fp2p,ConvertPlayerState(2),ConvertLimitOp(4),0)
call Fukki_Action1(fi5i,fi2i,fi3i,function Fukki_Lumber_Rate7)
endif
call Fukki_Trigger_Check(fi2i,fi3i,fi5i,fi3i,fi4i,fbact[1])
endfunction
function Fukki_Lumber_Rate6 takes nothing returns nothing
local integer fi3i=S2I(GetEventPlayerChatString())
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi4i=Fukki_Share_Player(fi2i)
if fi3i<0then
set fi3i=0
endif
call SaveInteger(fhact[1],2,fi4i,fi3i)
call Fukki_Lumber_Rate4(fi4i,110,fi3i,6)
call Fukki_Text(fp2p,"|cffffcc00Lumber Rate:|r +"+I2S(fi3i)+"%")
call Fukki_Trigger_Check(fi2i,130,4,0,0,fbact[1])
call ExecuteFunc("Fukki_Lumber_Rate1")
endfunction
function Fukki_Lumber_Rate3 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=LoadInteger(fhact[1],0,2)
local integer fi6i=Fukki_Share_Player(fi2i)
local integer fi4i=LoadInteger(fhact[1],2,fi6i)
local integer fi5i=Fukki_Button1(fi2i)
local button fb2b=GetClickedButton()
if fb2b==fuact[fi5i+0]then
call SaveInteger(fhact[1],2,fi6i,0)
call Fukki_Lumber_Rate4(fi6i,110,0,6)
call ExecuteFunc("Fukki_Main_Menu1")
elseif fb2b==fuact[fi5i+1]then
call ExecuteFunc("Fukki_Main_Menu1")
elseif fb2b==fuact[fi5i+2]then
set fi4i=fi4i+fi3i
call SaveInteger(fhact[1],2,fi6i,fi4i)
call Fukki_Lumber_Rate4(fi6i,110,fi4i,6)
call ExecuteFunc("Fukki_Lumber_Rate1")
elseif fb2b==fuact[fi5i+3]then
set fi4i=fi4i-fi3i
if fi4i<0then
set fi4i=0
endif
call SaveInteger(fhact[1],2,fi6i,fi4i)
call Fukki_Lumber_Rate4(fi6i,110,fi4i,6)
call ExecuteFunc("Fukki_Lumber_Rate1")
elseif fb2b==fuact[fi5i+4]then
call Fukki_Custom_Table(fi2i,130,7,"|cffffcc00ENTER LUMBER RATE|r",function Fukki_Lumber_Rate6)
elseif fb2b==fuact[fi5i+5]then
call ExecuteFunc("Fukki_Main_Menu1")
endif
endfunction
function Fukki_Lumber_Rate1 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=LoadInteger(fhact[1],0,2)
local integer fi4i=Fukki_Share_Player(fi2i)
call Fukki_Dialog(fi2i,90,5,"|cffffcc00FukKi CP [Lumber Rate]|r",function Fukki_Lumber_Rate3)
if fbact[fi4i+110]then
call Fukki_Button2(fi2i,0,90,"|cffffcc00Disable|r")
endif
call Fukki_Button2(fi2i,1,90,"|cffffcc00"+I2S(LoadInteger(fhact[1],2,fi4i))+"%|r")
call Fukki_Button2(fi2i,2,90,"|cffffffff+"+I2S(fi3i)+"%|r")
call Fukki_Button2(fi2i,3,90,"|cffffffff-"+I2S(fi3i)+"%|r")
call Fukki_Button2(fi2i,4,90,"|cffffcc00Custom|r")
call Fukki_Button2(fi2i,5,90,"|cffffcc00Back|r")
call DialogDisplay(fp2p,fdact[fi2i+90],fbact[1])
endfunction
function Fukki_EXP_Rate8 takes nothing returns nothing
local unit fu2u=GetEnumUnit()
local integer fi3i=GetHeroXP(fu2u)
local integer fi4i=GetHandleId(fu2u)
local integer fi2i=GetPlayerId(GetOwningPlayer(fu2u))
local integer fi7i=LoadInteger(fhact[1],3,fi2i)
local integer fi5i=LoadInteger(fhact[0],3,fi4i)
local unit fi6i=LoadUnitHandle(fhact[0],3,fi4i)
if fi3i>fi5i and fi5i>0and fbact[fi2i+190]and fu2u==fi6i then
set fi3i=R2I(fi3i+((fi3i-fi5i)*(I2R(fi7i)/100)))
call SetHeroXP(fu2u,fi3i,fbact[2])
elseif fbact[2]==fbact[fi2i+190]then
call RemoveSavedInteger(fhact[0],3,fi4i)
call SaveUnitHandle(fhact[0],3,fi4i,null)
call GroupRemoveUnit(fgact[6],fu2u)
endif
if fu2u==fi6i then
call SaveInteger(fhact[0],3,fi4i,fi3i)
endif
endfunction
function Fukki_EXP_Rate7 takes nothing returns nothing
call ForGroup(fgact[6],function Fukki_EXP_Rate8)
endfunction
function Fukki_EXP_Rate11 takes nothing returns nothing
local unit fu2u=GetTriggerUnit()
local integer fi2i=GetHandleId(fu2u)
call DestroyTrigger(GetTriggeringTrigger())
if IsUnitInGroup(fu2u,fgact[6])then
call GroupRemoveUnit(fgact[6],fu2u)
call RemoveSavedInteger(fhact[0],3,fi2i)
call SaveUnitHandle(fhact[0],3,fi2i,null)
endif
endfunction
function Fukki_EXP_Rate10 takes unit fu2u,integer fi2i,trigger ft2t returns nothing
if not IsUnitInGroup(fu2u,fgact[6])and IsUnitType(fu2u,ConvertUnitType(0))then
set ft2t=CreateTrigger()
call GroupAddUnit(fgact[6],fu2u)
call SaveUnitHandle(fhact[0],3,GetHandleId(fu2u),fu2u)
call TriggerRegisterUnitEvent(ft2t,fu2u,ConvertUnitEvent(53))
endif
call TriggerAddAction(ft2t,function Fukki_EXP_Rate11)
endfunction
function Fukki_EXP_Rate9 takes nothing returns nothing
local unit fu2u=GetTriggerUnit()
local unit fu3u=GetAttacker()
local unit fu4u=GetSpellTargetUnit()
local integer fi2i=GetPlayerId(GetOwningPlayer(fu2u))
local integer fi3i=GetPlayerId(GetOwningPlayer(fu3u))
local integer fi4i=GetPlayerId(GetOwningPlayer(fu4u))
if fbact[190+fi2i]then
call Fukki_EXP_Rate10(fu2u,fi2i,null)
elseif fbact[190+fi3i]then
call Fukki_EXP_Rate10(fu3u,fi3i,null)
elseif fbact[190+fi4i]then
call Fukki_EXP_Rate10(fu4u,fi4i,null)
endif
endfunction
function Fukki_EXP_Rate4 takes integer fi2i,integer fi3i,integer fi4i returns nothing
if LoadInteger(fhact[1],9,16)!=1then
call SaveInteger(fhact[1],9,16,1)
set fgact[6]=CreateGroup()
set ftact[190]=CreateTrigger()
call TriggerRegisterTimerEvent(ftact[190],.5,fbact[1])
call Fukki_Action2(9,16,190,function Fukki_EXP_Rate7)
endif
if LoadInteger(fhact[1],9,18)!=1then
call SaveInteger(fhact[1],9,18,1)
set ftact[191]=CreateTrigger()
call TriggerRegisterAnyUnitEventBJ(ftact[191],ConvertPlayerUnitEvent(18))
call TriggerRegisterAnyUnitEventBJ(ftact[191],ConvertPlayerUnitEvent(38))
call TriggerRegisterAnyUnitEventBJ(ftact[191],ConvertPlayerUnitEvent(39))
call TriggerRegisterAnyUnitEventBJ(ftact[191],ConvertPlayerUnitEvent(40))
call TriggerRegisterAnyUnitEventBJ(ftact[191],ConvertPlayerUnitEvent(272))
call TriggerRegisterAnyUnitEventBJ(ftact[191],ConvertPlayerUnitEvent(273))
call TriggerRegisterAnyUnitEventBJ(ftact[191],ConvertPlayerUnitEvent(274))
call Fukki_Action2(9,18,191,function Fukki_EXP_Rate9)
endif
call Fukki_Trigger_Check(fi2i,fi3i,9,fi3i,fi4i,fbact[1])
call Fukki_Trigger_Destroy2(fi3i,9,16,fbact[fi2i+fi3i])
call Fukki_Trigger_Destroy2(191,9,18,fbact[fi2i+fi3i])
if LoadInteger(fhact[1],9,17)==0then
call FlushChildHashtable(fhact[0],3)
call DestroyGroup(fgact[6])
endif
endfunction
function Fukki_EXP_Rate6 takes nothing returns nothing
local integer fi3i=S2I(GetEventPlayerChatString())
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi4i=Fukki_Share_Player(fi2i)
if fi3i<0then
set fi3i=0
endif
call SaveInteger(fhact[1],3,fi4i,fi3i)
call Fukki_EXP_Rate4(fi4i,190,fi3i)
call Fukki_Text(fp2p,"|cffffcc00EXP Rate:|r +"+I2S(fi3i)+"%")
call Fukki_Trigger_Check(fi2i,170,10,0,0,fbact[1])
call ExecuteFunc("Fukki_EXP_Rate1")
endfunction
function Fukki_EXP_Rate3 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=LoadInteger(fhact[1],0,3)
local integer fi6i=Fukki_Share_Player(fi2i)
local integer fi4i=LoadInteger(fhact[1],3,fi6i)
local integer fi5i=Fukki_Button1(fi2i)
local button fb2b=GetClickedButton()
if fb2b==fuact[fi5i+0]then
call SaveInteger(fhact[1],3,fi6i,0)
call Fukki_EXP_Rate4(fi6i,190,0)
call ExecuteFunc("Fukki_Main_Menu1")
elseif fb2b==fuact[fi5i+1]then
call ExecuteFunc("Fukki_Main_Menu1")
elseif fb2b==fuact[fi5i+2]then
set fi4i=fi4i+fi3i
call SaveInteger(fhact[1],3,fi6i,fi4i)
call Fukki_EXP_Rate4(fi6i,190,fi4i)
call ExecuteFunc("Fukki_EXP_Rate1")
elseif fb2b==fuact[fi5i+3]then
set fi4i=fi4i-fi3i
if fi4i<0then
set fi4i=0
endif
call SaveInteger(fhact[1],3,fi6i,fi4i)
call Fukki_EXP_Rate4(fi6i,190,fi4i)
call ExecuteFunc("Fukki_EXP_Rate1")
elseif fb2b==fuact[fi5i+4]then
call Fukki_Custom_Table(fi2i,170,10,"|cffffcc00ENTER EXP RATE|r",function Fukki_EXP_Rate6)
elseif fb2b==fuact[fi5i+5]then
call ExecuteFunc("Fukki_Main_Menu1")
endif
endfunction
function Fukki_EXP_Rate1 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=LoadInteger(fhact[1],0,3)
local integer fi4i=Fukki_Share_Player(fi2i)
call Fukki_Dialog(fi2i,150,8,"|cffffcc00FukKi CP [EXP Rate]|r",function Fukki_EXP_Rate3)
if fbact[fi4i+190]then
call Fukki_Button2(fi2i,0,150,"|cffffcc00Disable|r")
endif
call Fukki_Button2(fi2i,1,150,"|cffffcc00"+I2S(LoadInteger(fhact[1],3,fi4i))+"%|r")
call Fukki_Button2(fi2i,2,150,"|cffffffff+"+I2S(fi3i)+"%|r")
call Fukki_Button2(fi2i,3,150,"|cffffffff-"+I2S(fi3i)+"%|r")
call Fukki_Button2(fi2i,4,150,"|cffffcc00Custom|r")
call Fukki_Button2(fi2i,5,150,"|cffffcc00Back|r")
call DialogDisplay(fp2p,fdact[fi2i+150],fbact[1])
endfunction
function Fukki_Damage_Action20 takes unit fu2u,real fr2r returns nothing
local texttag ft2t=CreateTextTagUnitBJ(I2S(R2I(fr2r))+"!",fu2u,0,10,255,0,0,0)
call SetTextTagPermanent(ft2t,fbact[2])
call SetTextTagLifespan(ft2t,3.5)
call SetTextTagFadepoint(ft2t,3)
call SetTextTagVelocity(ft2t,0,.05)
endfunction
function Fukki_Damage_Action19 takes unit fu2u,unit fu3u,real fr2r returns nothing
call UnitDamageTarget(fu2u,fu3u,fr2r,fbact[2],fbact[2],ConvertAttackType(5),ConvertDamageType(0),ConvertWeaponType(0))
endfunction
function Fukki_Damage_Action7 takes unit fu2u,unit fu3u,real fr2r returns nothing
local integer fi2i=GetUnitTypeId(fu3u)
local real fr3r=GetWidgetLife(fu3u)
local real fr4r=LoadReal(fhact[0],255,fi2i)
local real fr5r=0
if fr3r>0then
if fr4r<=0then
call Fukki_Damage_Action19(fu2u,fu3u,fr2r)
else
call Fukki_Damage_Action19(fu2u,fu3u,fr2r+((fr2r*fr4r)/100))
endif
set fr5r=GetWidgetLife(fu3u)
set fr3r=((fr3r-fr5r)/fr2r)*100
if fr5r>0then
if fr3r<100then
set fr3r=100-fr3r
if fr3r>fr4r then
set fr5r=fr4r+(fr3r-fr4r)
else
set fr5r=fr4r+(fr4r-fr3r)
endif
call SaveReal(fhact[0],255,fi2i,fr5r)
elseif fr3r>100then
call SaveReal(fhact[0],255,fi2i,fr4r-(fr3r-100))
endif
endif 
endif
endfunction
function Fukki_Damage_Action14 takes nothing returns nothing
local timer ft2t=GetExpiredTimer()
local integer fi2i=GetHandleId(ft2t)
call SetWidgetLife(LoadUnitHandle(fhact[1],40,fi2i),LoadReal(fhact[1],40,fi2i))
call FlushChildHashtable(fhact[1],40)
call DestroyTimer(ft2t)
endfunction
function Fukki_Damage_Action15 takes nothing returns nothing
local timer ft2t=GetExpiredTimer()
local integer fi2i=GetHandleId(ft2t)
call Fukki_Damage_Action7(LoadUnitHandle(fhact[1],42,fi2i),LoadUnitHandle(fhact[1],41,fi2i),LoadReal(fhact[1],43,fi2i))
call FlushChildHashtable(fhact[1],41)
call FlushChildHashtable(fhact[1],42)
call FlushChildHashtable(fhact[1],43)
call DestroyTimer(ft2t)
endfunction
function Fukki_Damage_Action18 takes nothing returns nothing
local timer ft2t=GetExpiredTimer()
local integer fi2i=GetHandleId(ft2t)
call Fukki_Damage_Action7(LoadUnitHandle(fhact[1],44,fi2i),LoadUnitHandle(fhact[1],45,fi2i),LoadReal(fhact[1],46,fi2i))
call FlushChildHashtable(fhact[1],44)
call FlushChildHashtable(fhact[1],45)
call FlushChildHashtable(fhact[1],46)
call DestroyTimer(ft2t)
endfunction
function Fukki_Damage_Action6 takes nothing returns nothing
local unit fu3u=GetTriggerUnit()
local real fi5i=GetEventDamage()
local player fp2p=GetOwningPlayer(fu3u)
local integer fi2i=GetPlayerId(fp2p)
local real fi3i=GetWidgetLife(fu3u)
local eventid fe2e=GetTriggerEventId()
local timer ft2t=null
local integer fi4i=0
if fe2e==ConvertUnitEvent(52)and fp2p==fpact[fi2i+310]then
set ft2t=CreateTimer()
set fi4i=GetHandleId(ft2t)
set fi3i=fi3i+(fi5i*(LoadReal(fhact[1],6,fi2i)/'d'))
call SaveUnitHandle(fhact[1],40,fi4i,fu3u)
call SaveReal(fhact[1],40,fi4i,fi3i-fi5i)
call SetWidgetLife(fu3u,fi3i)
call TimerStart(ft2t,0,fbact[2],function Fukki_Damage_Action14)
elseif IsUnitInGroup(fu3u,fgact[1])then
call DestroyTrigger(GetTriggeringTrigger())
call GroupRemoveUnit(fgact[1],fu3u)
endif
endfunction
function Fukki_Damage_Action5 takes nothing returns nothing
local unit fu2u=GetEventDamageSource()
local unit fu3u=GetTriggerUnit()
local real fi5i=GetEventDamage()
local player fp2p=GetOwningPlayer(fu3u)
local integer fi2i=GetPlayerId(fp2p)
local eventid fe2e=GetTriggerEventId()
local boolean fb2b=fe2e==ConvertUnitEvent(52)
local timer ft2t=null
local integer fi3i=0
if fb2b and fp2p==fpact[fi2i+250]then
set ft2t=CreateTimer()
set fi3i=GetHandleId(ft2t)
set fi5i=fi5i*(LoadReal(fhact[1],5,fi2i)/'d')
call SaveUnitHandle(fhact[1],41,fi3i,fu2u)
call SaveUnitHandle(fhact[1],42,fi3i,fu3u)
call SaveReal(fhact[1],43,fi3i,fi5i)
call SaveReal(fhact[1],50,GetHandleId(fu3u),fi5i)
call TimerStart(ft2t,0,fbact[2],function Fukki_Damage_Action15)
elseif IsUnitInGroup(fu3u,fgact[0])then
call DestroyTrigger(GetTriggeringTrigger())
call GroupRemoveUnit(fgact[0],fu3u)
endif
endfunction
function Fukki_Damage_Action4 takes unit fu2u,integer fi2i,trigger ft2t returns nothing
if IsUnitOwnedByPlayer(fu2u,fpact[fi2i+250])then
if not IsUnitInGroup(fu2u,fgact[0])then
set ft2t=CreateTrigger()
call GroupAddUnit(fgact[0],fu2u)
call TriggerRegisterUnitEvent(ft2t,fu2u,ConvertUnitEvent(52))
call TriggerRegisterUnitEvent(ft2t,fu2u,ConvertUnitEvent(53))
call TriggerAddAction(ft2t,function Fukki_Damage_Action5)
endif
endif
if IsUnitOwnedByPlayer(fu2u,fpact[fi2i+310])then
if not IsUnitInGroup(fu2u,fgact[1])then
set ft2t=CreateTrigger()
call GroupAddUnit(fgact[1],fu2u)
call TriggerRegisterUnitEvent(ft2t,fu2u,ConvertUnitEvent(52))
call TriggerRegisterUnitEvent(ft2t,fu2u,ConvertUnitEvent(53))
call TriggerAddAction(ft2t,function Fukki_Damage_Action6)
endif
endif
if IsUnitOwnedByPlayer(fu2u,fpact[fi2i+1450])then
call UnitRemoveBuffs(fu2u,fbact[2],fbact[1])
endif
endfunction
function Fukki_Damage_Action3 takes integer fi2i returns boolean
return fbact[250+fi2i]or fbact[310+fi2i]or fbact[1450+fi2i]
endfunction
function Fukki_Damage_Action8 takes nothing returns nothing
local unit fu2u=GetEventDamageSource()
local unit fu3u=GetTriggerUnit()
local real fi5i=GetEventDamage()
local player fp2p=GetOwningPlayer(fu2u)
local integer fi2i=GetPlayerId(fp2p)
local integer fi7i=GetHandleId(fu2u)
local eventid fe2e=GetTriggerEventId()
local boolean fb2b=fe2e==ConvertUnitEvent(52)
local boolean fb3b=not IsUnitInGroup(fu2u,fgact[4])
local real fi6i=LoadReal(fhact[1],50,fi7i)
local timer ft3t=null
local integer fi3i=0
if fb2b and fb3b and fi6i!=fi5i and fbact[fi2i+370]then
if fbact[fi2i+1210]and fbact[fi2i+1270]then
if GetRandomInt(0,100)<=LoadInteger(fhact[1],93,fi2i)then
set fi6i=fi5i*(LoadReal(fhact[1],7,fi2i)/'d')
if fi6i==0then
set fi6i=fi5i*(I2R(LoadInteger(fhact[1],90,fi2i))/'d')
else
set fi6i=fi6i*(I2R(LoadInteger(fhact[1],90,fi2i))/'d')
endif
set ft3t=CreateTimer()
set fi3i=GetHandleId(ft3t)
call Fukki_Damage_Action20(fu2u,fi6i+fi5i)
call SaveUnitHandle(fhact[1],44,fi3i,fu2u)
call SaveUnitHandle(fhact[1],45,fi3i,fu3u)
call SaveReal(fhact[1],46,fi3i,fi6i)
call TimerStart(ft3t,0,fbact[2],function Fukki_Damage_Action18)
endif
else
set ft3t=CreateTimer()
set fi3i=GetHandleId(ft3t)
set fi6i=fi5i*(LoadReal(fhact[1],7,fi2i)/'d')
call SaveUnitHandle(fhact[1],44,fi3i,fu2u)
call SaveUnitHandle(fhact[1],45,fi3i,fu3u)
call SaveReal(fhact[1],46,fi3i,fi6i)
call TimerStart(ft3t,0,fbact[2],function Fukki_Damage_Action18)
endif
elseif fi6i==fi5i then
call RemoveSavedReal(fhact[1],50,fi7i)
elseif IsUnitInGroup(fu3u,fgact[2])then
call DestroyTrigger(GetTriggeringTrigger())
call GroupRemoveUnit(fgact[2],fu3u)
endif
endfunction
function Fukki_Damage_Action13 takes nothing returns nothing
local unit fu2u=GetEventDamageSource()
local unit fu3u=GetTriggerUnit()
local real fi5i=GetEventDamage()
local player fp2p=GetOwningPlayer(fu2u)
local integer fi2i=GetPlayerId(fp2p)
local integer fi7i=GetHandleId(fu2u)
local eventid fe2e=GetTriggerEventId()
local real fi6i=LoadReal(fhact[1],50,fi7i)
local boolean fb2b=fe2e==ConvertUnitEvent(52)
local boolean fb3b=not IsUnitInGroup(fu2u,fgact[4])
if fb2b and fb3b and fi6i!=fi5i and fp2p==fpact[fi2i+710]then
set fi5i=fi5i*(I2R(LoadInteger(fhact[1],10,fi2i))/'d')
call SetUnitState(fu2u,ConvertUnitState(2),GetUnitState(fu2u,ConvertUnitState(2))+fi5i)
call SetUnitState(fu3u,ConvertUnitState(2),GetUnitState(fu3u,ConvertUnitState(2))-fi5i)
elseif fi6i==fi5i then
call RemoveSavedReal(fhact[1],50,fi7i)
elseif IsUnitInGroup(fu3u,fgact[8])then
call DestroyTrigger(GetTriggeringTrigger())
call GroupRemoveUnit(fgact[8],fu3u)
endif
endfunction
function Fukki_Damage_Action12 takes nothing returns nothing
local unit fu2u=GetEventDamageSource()
local unit fu3u=GetTriggerUnit()
local real fi5i=GetEventDamage()
local player fp2p=GetOwningPlayer(fu2u)
local integer fi2i=GetPlayerId(fp2p)
local integer fi7i=GetHandleId(fu2u)
local eventid fe2e=GetTriggerEventId()
local real fi6i=LoadReal(fhact[1],50,fi7i)
local boolean fb2b=fe2e==ConvertUnitEvent(52)
local boolean fb3b=not IsUnitInGroup(fu2u,fgact[4])
if fb2b and fb3b and fi6i!=fi5i and fp2p==fpact[fi2i+650]then
call SetWidgetLife(fu2u,GetWidgetLife(fu2u)+(fi5i*(I2R(LoadInteger(fhact[1],9,fi2i))/'d')))
elseif fi6i==fi5i then
call RemoveSavedReal(fhact[1],50,fi7i)
elseif IsUnitInGroup(fu3u,fgact[7])then
call DestroyTrigger(GetTriggeringTrigger())
call GroupRemoveUnit(fgact[7],fu3u)
endif
endfunction
function Fukki_Damage_Action11 takes nothing returns nothing
local trigger ft2t=GetTriggeringTrigger()
local unit fu3u=GetTriggerUnit()
local real fi5i=GetEventDamage()
local unit fu4u=GetEventDamageSource()
local player fp4p=GetOwningPlayer(fu4u)
local player fp3p=GetOwningPlayer(fu3u)
local integer fi7i=GetHandleId(fu4u)
local integer fi4i=GetPlayerId(fp4p)
local eventid fe2e=GetTriggerEventId()
local real fi6i=LoadReal(fhact[1],50,fi7i)
local boolean fb3b=fe2e==ConvertUnitEvent(52)
local boolean fb2b=IsUnitInGroup(fu4u,fgact[4])
local boolean fb4b=fb3b and fb2b and fp3p!=fp4p
if fb4b and fi5i!=fi6i and fbact[fi4i+430]then
call DisableTrigger(ft2t)
if fbact[fi4i+1330]and fbact[fi4i+1390]then
if GetRandomInt(0,100)<=LoadInteger(fhact[1],100,fi4i)then
set fi6i=fi5i*(LoadReal(fhact[1],8,fi4i)/100)
if fi6i==0then
set fi6i=fi5i*(I2R(LoadInteger(fhact[1],97,fi4i))/100)
else
set fi6i=fi6i*(I2R(LoadInteger(fhact[1],97,fi4i))/100)
endif
call Fukki_Damage_Action7(fu4u,fu3u,fi6i)
call Fukki_Damage_Action20(fu4u,fi6i+fi5i)
endif
else
set fi6i=fi5i*(LoadReal(fhact[1],8,fi4i)/100)
call Fukki_Damage_Action7(fu4u,fu3u,fi6i)
endif
call EnableTrigger(ft2t)
elseif fi6i==fi5i then
call RemoveSavedReal(fhact[1],50,fi7i)
elseif IsUnitInGroup(fu3u,fgact[5])then
call DestroyTrigger(ft2t)
call GroupRemoveUnit(fgact[5],fu3u)
endif
endfunction
function Fukki_Damage_Action10 takes nothing returns nothing
local unit fu2u=GetEnumUnit()
local trigger ft2t=null
if not IsUnitInGroup(fu2u,fgact[5])then
call GroupAddUnit(fgact[5],fu2u)
set ft2t=CreateTrigger()
call TriggerRegisterUnitEvent(ft2t,fu2u,ConvertUnitEvent(52))
call TriggerRegisterUnitEvent(ft2t,fu2u,ConvertUnitEvent(53))
call TriggerAddAction(ft2t,function Fukki_Damage_Action11)
endif
endfunction
function Fukki_Damage_Action9 takes nothing returns boolean
return(not(IsUnitInGroup(GetFilterUnit(),fgact[5])))
endfunction
function Fukki_Damage_Action2 takes nothing returns nothing
local unit fu2u=GetTriggerUnit()
local unit fu3u=GetAttacker()
local unit fu4u=GetSpellTargetUnit()
local integer fi2i=GetPlayerId(GetOwningPlayer(fu2u))
local integer fi3i=GetPlayerId(GetOwningPlayer(fu3u))
local integer fi4i=GetPlayerId(GetOwningPlayer(fu4u))
local eventid fe2e=GetTriggerEventId()
local trigger ft2t=null
local group fg2g=null
if fe2e==ConvertPlayerUnitEvent(18)then
if IsUnitInGroup(fu3u,fgact[4])then
call GroupRemoveUnit(fgact[4],fu3u)
endif
if IsUnitOwnedByPlayer(fu3u,fpact[fi3i+370])then
if not IsUnitInGroup(fu2u,fgact[2])then
set ft2t=CreateTrigger()
call GroupAddUnit(fgact[2],fu2u)
call TriggerRegisterUnitEvent(ft2t,fu2u,ConvertUnitEvent(52))
call TriggerRegisterUnitEvent(ft2t,fu2u,ConvertUnitEvent(53))
call TriggerAddAction(ft2t,function Fukki_Damage_Action8)
endif
endif
if IsUnitOwnedByPlayer(fu3u,fpact[fi3i+650])then
if not IsUnitInGroup(fu2u,fgact[7])then
set ft2t=CreateTrigger()
call GroupAddUnit(fgact[7],fu2u)
call TriggerRegisterUnitEvent(ft2t,fu2u,ConvertUnitEvent(52))
call TriggerRegisterUnitEvent(ft2t,fu2u,ConvertUnitEvent(53))
call TriggerAddAction(ft2t,function Fukki_Damage_Action12)
endif
endif
if IsUnitOwnedByPlayer(fu3u,fpact[fi3i+710])then
if not IsUnitInGroup(fu2u,fgact[8])then
set ft2t=CreateTrigger()
call GroupAddUnit(fgact[8],fu2u)
call TriggerRegisterUnitEvent(ft2t,fu2u,ConvertUnitEvent(52))
call TriggerRegisterUnitEvent(ft2t,fu2u,ConvertUnitEvent(53))
call TriggerAddAction(ft2t,function Fukki_Damage_Action13)
endif
endif
if IsUnitOwnedByPlayer(fu3u,fpact[fi3i+1430])then
call UnitRemoveBuffs(fu2u,fbact[1],fbact[2])
endif
else
if IsUnitOwnedByPlayer(fu2u,fpact[fi2i+430])then
if not IsUnitInGroup(fu2u,fgact[4])then
call GroupAddUnit(fgact[4],fu2u)
endif
set fg2g=CreateGroup()
call GroupEnumUnitsInRect(fg2g,bj_mapInitialPlayableArea,Filter(function Fukki_Damage_Action9))
call ForGroup(fg2g,function Fukki_Damage_Action10)
call DestroyGroup(fg2g)
endif
endif
if Fukki_Damage_Action3(fi2i)then
call Fukki_Damage_Action4(fu2u,fi2i,null)
elseif Fukki_Damage_Action3(fi3i)then
call Fukki_Damage_Action4(fu3u,fi3i,null)
elseif Fukki_Damage_Action3(fi4i)then
call Fukki_Damage_Action4(fu4u,fi4i,null)
endif
endfunction
function Fukki_Damage_Action1 takes integer fi2i,integer fi3i,integer fi4i returns nothing
local player fp2p=Player(fi2i)
if LoadInteger(fhact[1],13,16)!=1then
call SaveInteger(fhact[1],13,16,1)
set ftact[250]=CreateTrigger()
call TriggerRegisterAnyUnitEventBJ(ftact[250],ConvertPlayerUnitEvent(18))
call TriggerRegisterAnyUnitEventBJ(ftact[250],ConvertPlayerUnitEvent(38))
call TriggerRegisterAnyUnitEventBJ(ftact[250],ConvertPlayerUnitEvent(39))
call TriggerRegisterAnyUnitEventBJ(ftact[250],ConvertPlayerUnitEvent(40))
call TriggerRegisterAnyUnitEventBJ(ftact[250],ConvertPlayerUnitEvent(272))
call TriggerRegisterAnyUnitEventBJ(ftact[250],ConvertPlayerUnitEvent(273))
call TriggerRegisterAnyUnitEventBJ(ftact[250],ConvertPlayerUnitEvent(274))
call Fukki_Action2(13,18,250,function Fukki_Damage_Action2)
endif
call Fukki_Trigger_Check(fi2i,fi3i,0,fi3i,fi4i,fbact[2])
call Fukki_Trigger_Destroy2(250,13,16,fbact[fi2i+fi3i])
if LoadInteger(fhact[1],13,17)==0then
call FlushChildHashtable(fhact[1],50)
endif
endfunction
function Fukki_Return_Damage_Rate6 takes nothing returns nothing
local integer fi3i=S2I(GetEventPlayerChatString())
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi4i=Fukki_Share_Player(fi2i)
if fi3i<0then
set fi3i=0
endif
call SaveReal(fhact[1],5,fi4i,fi3i)
call Fukki_Damage_Action1(fi4i,250,fi3i)
call Fukki_Text(fp2p,"|cffffcc00Return Damage Rate:|r +"+I2S(fi3i)+"%")
call Fukki_Trigger_Check(fi2i,230,12,0,0,fbact[1])
call ExecuteFunc("Fukki_Return_Damage_Rate1")
endfunction
function Fukki_Return_Damage_Rate3 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=LoadInteger(fhact[1],0,5)
local integer fi6i=Fukki_Share_Player(fi2i)
local integer fi4i=R2I(LoadReal(fhact[1],5,fi6i))
local integer fi5i=Fukki_Button1(fi2i)
local button fb2b=GetClickedButton()
if fb2b==fuact[fi5i+0]then
call SaveReal(fhact[1],5,fi6i,0)
call Fukki_Damage_Action1(fi6i,250,0)
call ExecuteFunc("Fukki_Main_Menu1")
elseif fb2b==fuact[fi5i+1]then
call ExecuteFunc("Fukki_Main_Menu1")
elseif fb2b==fuact[fi5i+2]then
set fi4i=fi4i+fi3i
call SaveReal(fhact[1],5,fi6i,fi4i)
call Fukki_Damage_Action1(fi6i,250,fi4i)
call ExecuteFunc("Fukki_Return_Damage_Rate1")
elseif fb2b==fuact[fi5i+3]then
set fi4i=fi4i-fi3i
if fi4i<0then
set fi4i=0
endif
call SaveReal(fhact[1],5,fi6i,fi4i)
call Fukki_Damage_Action1(fi6i,250,fi4i)
call ExecuteFunc("Fukki_Return_Damage_Rate1")
elseif fb2b==fuact[fi5i+4]then
call Fukki_Custom_Table(fi2i,230,12,"|cffffcc00ENTER RETURN DAMAGE RATE|r",function Fukki_Return_Damage_Rate6)
elseif fb2b==fuact[fi5i+5]then
call ExecuteFunc("Fukki_Main_Menu1")
endif
endfunction
function Fukki_Return_Damage_Rate1 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=LoadInteger(fhact[1],0,5)
local integer fi4i=Fukki_Share_Player(fi2i)
call Fukki_Dialog(fi2i,210,11,"|cffffcc00FukKi CP [Return Damage]|r",function Fukki_Return_Damage_Rate3)
if fbact[fi4i+250]then
call Fukki_Button2(fi2i,0,210,"|cffffcc00Disable|r")
endif
call Fukki_Button2(fi2i,1,210,"|cffffcc00"+I2S(R2I(LoadReal(fhact[1],5,fi4i)))+"%|r")
call Fukki_Button2(fi2i,2,210,"|cffffffff+"+I2S(fi3i)+"%|r")
call Fukki_Button2(fi2i,3,210,"|cffffffff-"+I2S(fi3i)+"%|r")
call Fukki_Button2(fi2i,4,210,"|cffffcc00Custom|r")
call Fukki_Button2(fi2i,5,210,"|cffffcc00Back|r")
call DialogDisplay(fp2p,fdact[fi2i+210],fbact[1])
endfunction
function Fukki_Blocking_Damage_Rate6 takes nothing returns nothing
local integer fi3i=S2I(GetEventPlayerChatString())
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi4i=Fukki_Share_Player(fi2i)
if fi3i<0then
set fi3i=0
endif
call SaveReal(fhact[1],6,fi4i,fi3i)
call Fukki_Damage_Action1(fi4i,310,fi3i)
call Fukki_Text(fp2p,"|cffffcc00Blocking Damage Rate:|r +"+I2S(fi3i)+"%")
call Fukki_Trigger_Check(fi2i,290,15,0,0,fbact[1])
call ExecuteFunc("Fukki_Blocking_Damage_Rate1")
endfunction
function Fukki_Blocking_Damage_Rate3 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=LoadInteger(fhact[1],0,6)
local integer fi6i=Fukki_Share_Player(fi2i)
local integer fi4i=R2I(LoadReal(fhact[1],6,fi2i))
local integer fi5i=Fukki_Button1(fi2i)
local button fb2b=GetClickedButton()
if fb2b==fuact[fi5i+0]then
call SaveReal(fhact[1],6,fi6i,0)
call Fukki_Damage_Action1(fi6i,310,0)
call ExecuteFunc("Fukki_Main_Menu1")
elseif fb2b==fuact[fi5i+1]then
call ExecuteFunc("Fukki_Main_Menu1")
elseif fb2b==fuact[fi5i+2]then
set fi4i=fi4i+fi3i
call SaveReal(fhact[1],6,fi6i,fi4i)
call Fukki_Damage_Action1(fi6i,310,fi4i)
call ExecuteFunc("Fukki_Blocking_Damage_Rate1")
elseif fb2b==fuact[fi5i+3]then
set fi4i=fi4i-fi3i
if fi4i<0then
set fi4i=0
endif
call SaveReal(fhact[1],6,fi6i,fi4i)
call Fukki_Damage_Action1(fi6i,310,fi4i)
call ExecuteFunc("Fukki_Blocking_Damage_Rate1")
elseif fb2b==fuact[fi5i+4]then
call Fukki_Custom_Table(fi2i,290,15,"|cffffcc00ENTER BLOKING DAMAGE RATE|r",function Fukki_Blocking_Damage_Rate6)
elseif fb2b==fuact[fi5i+5]then
call ExecuteFunc("Fukki_Main_Menu1")
endif
endfunction
function Fukki_Blocking_Damage_Rate1 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=LoadInteger(fhact[1],0,6)
local integer fi4i=Fukki_Share_Player(fi2i)
call Fukki_Dialog(fi2i,270,14,"|cffffcc00FukKi CP [Blocking Damage]|r",function Fukki_Blocking_Damage_Rate3)
if fbact[fi4i+310]then
call Fukki_Button2(fi2i,0,270,"|cffffcc00Disable|r")
endif
call Fukki_Button2(fi2i,1,270,"|cffffcc00"+I2S(R2I(LoadReal(fhact[1],6,fi4i)))+"%|r")
call Fukki_Button2(fi2i,2,270,"|cffffffff+"+I2S(fi3i)+"%|r")
call Fukki_Button2(fi2i,3,270,"|cffffffff-"+I2S(fi3i)+"%|r")
call Fukki_Button2(fi2i,4,270,"|cffffcc00Custom|r")
call Fukki_Button2(fi2i,5,270,"|cffffcc00Back|r")
call DialogDisplay(fp2p,fdact[fi2i+270],fbact[1])
endfunction
function Fukki_Attack_Damage6 takes nothing returns nothing
local integer fi3i=S2I(GetEventPlayerChatString())
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi4i=Fukki_Share_Player(fi2i)
if fi3i<0then
set fi3i=0
endif
call SaveReal(fhact[1],7,fi4i,fi3i)
call Fukki_Damage_Action1(fi4i,370,fi3i)
call Fukki_Text(fp2p,"|cffffcc00Attack Damage:|r +"+I2S(fi3i)+"%")
call Fukki_Trigger_Check(fi2i,350,17,0,0,fbact[1])
call ExecuteFunc("Fukki_Attack_Damage1")
endfunction
function Fukki_Attack_Damage3 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=LoadInteger(fhact[1],0,7)
local integer fi6i=Fukki_Share_Player(fi2i)
local integer fi4i=R2I(LoadReal(fhact[1],7,fi6i))
local integer fi5i=Fukki_Button1(fi2i)
local button fb2b=GetClickedButton()
if fb2b==fuact[fi5i+0]then
if fbact[fi6i+370]then
call SaveReal(fhact[1],7,fi6i,0)
call Fukki_Damage_Action1(fi6i,370,0)
endif
if fbact[fi6i+1210]then
call SaveInteger(fhact[1],90,fi6i,0)
call Fukki_Damage_Action1(fi6i,1210,0)
endif
if fbact[fi6i+1270]then
call SaveInteger(fhact[1],93,fi6i,0)
call Fukki_Damage_Action1(fi6i,1270,0)
endif
call ExecuteFunc("Fukki_Main_Menu1")
elseif fb2b==fuact[fi5i+1]then
call ExecuteFunc("Fukki_Main_Menu1")
elseif fb2b==fuact[fi5i+2]then
set fi4i=fi4i+fi3i
call SaveReal(fhact[1],7,fi6i,fi4i)
call Fukki_Damage_Action1(fi6i,370,fi4i)
call ExecuteFunc("Fukki_Attack_Damage1")
elseif fb2b==fuact[fi5i+3]then
set fi4i=fi4i-fi3i
if fi4i<0then
set fi4i=0
endif
call SaveReal(fhact[1],7,fi6i,fi4i)
call Fukki_Damage_Action1(fi6i,370,fi4i)
call ExecuteFunc("Fukki_Attack_Damage1")
elseif fb2b==fuact[fi5i+4]then
call Fukki_Custom_Table(fi2i,350,17,"|cffffcc00ENTER ATTACK DAMAGE|r",function Fukki_Attack_Damage6)
elseif fb2b==fuact[fi5i+5]then
call ExecuteFunc("Fukki_Attack_Critical1")
elseif fb2b==fuact[fi5i+6]then
call ExecuteFunc("Fukki_Attack_Critical4")
elseif fb2b==fuact[fi5i+7]then
call ExecuteFunc("Fukki_Main_Menu1")
endif
endfunction
function Fukki_Attack_Damage1 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=LoadInteger(fhact[1],0,7)
local integer fi4i=Fukki_Share_Player(fi2i)
local integer fi6i=LoadInteger(fhact[1],90,fi4i)
local integer fi7i=LoadInteger(fhact[1],93,fi4i)
local real fi5i=LoadReal(fhact[1],7,fi4i)
call Fukki_Dialog(fi2i,330,16,"|cffffcc00FukKi CP [Attack Damage]|r",function Fukki_Attack_Damage3)
if fbact[fi4i+1190]and fbact[fi4i+1270]and fbact[fi4i+370]!=fbact[1]then
call Fukki_Button2(fi2i,0,330,"|cffffcc00Disable|r")
call Fukki_Damage_Action1(fi4i,370,1)
elseif fbact[fi4i+370]then
call Fukki_Button2(fi2i,0,330,"|cffffcc00Disable|r")
endif
call Fukki_Button2(fi2i,5,330,"|cffffcc00Critical Damage: |r|cffffffff+"+I2S(fi6i)+"%|r")
call Fukki_Button2(fi2i,6,330,"|cffffcc00Critical Chance: |r|cffffffff+"+I2S(fi7i)+"%|r")
call Fukki_Button2(fi2i,1,330,"|cffffcc00"+I2S(R2I(fi5i))+"%|r")
call Fukki_Button2(fi2i,2,330,"|cffffffff+"+I2S(fi3i)+"%|r")
call Fukki_Button2(fi2i,3,330,"|cffffffff-"+I2S(fi3i)+"%|r")
call Fukki_Button2(fi2i,4,330,"|cffffcc00Custom|r")
call Fukki_Button2(fi2i,7,330,"|cffffcc00Back|r")
call DialogDisplay(fp2p,fdact[fi2i+330],fbact[1])
endfunction
function Fukki_Skill_Damage6 takes nothing returns nothing
local integer fi3i=S2I(GetEventPlayerChatString())
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi4i=Fukki_Share_Player(fi2i)
if fi3i<0then
set fi3i=0
endif
call SaveReal(fhact[1],8,fi4i,fi3i)
call Fukki_Damage_Action1(fi4i,430,fi3i)
call Fukki_Text(fp2p,"|cffffcc00Skill Damage:|r +"+I2S(fi3i)+"%")
call Fukki_Trigger_Check(fi2i,410,19,0,0,fbact[1])
call ExecuteFunc("Fukki_Skill_Damage1")
endfunction
function Fukki_Skill_Damage3 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=LoadInteger(fhact[1],0,8)
local integer fi6i=Fukki_Share_Player(fi2i)
local integer fi4i=R2I(LoadReal(fhact[1],8,fi6i))
local integer fi5i=Fukki_Button1(fi2i)
local button fb2b=GetClickedButton()
if fb2b==fuact[fi5i+0]then
if fbact[fi4i+430]then
call SaveReal(fhact[1],8,fi6i,0)
call Fukki_Damage_Action1(fi6i,430,0)
endif
if fbact[fi4i+1330]then
call SaveInteger(fhact[1],97,fi6i,0)
call Fukki_Damage_Action1(fi6i,1330,0)
endif
if fbact[fi4i+1390]then
call SaveInteger(fhact[1],100,fi6i,0)
call Fukki_Damage_Action1(fi6i,1390,0)
endif
call ExecuteFunc("Fukki_Main_Menu1")
elseif fb2b==fuact[fi5i+1]then
call ExecuteFunc("Fukki_Main_Menu1")
elseif fb2b==fuact[fi5i+2]then
set fi4i=fi4i+fi3i
call SaveReal(fhact[1],8,fi6i,fi4i)
call Fukki_Damage_Action1(fi6i,430,fi4i)
call ExecuteFunc("Fukki_Skill_Damage1")
elseif fb2b==fuact[fi5i+3]then
set fi4i=fi4i-fi3i
if fi4i<0then
set fi4i=0
endif
call SaveReal(fhact[1],8,fi6i,fi4i)
call Fukki_Damage_Action1(fi6i,430,fi4i)
call ExecuteFunc("Fukki_Skill_Damage1")
elseif fb2b==fuact[fi5i+4]then
call Fukki_Custom_Table(fi2i,410,19,"|cffffcc00ENTER SKILL DAMAGE|r",function Fukki_Skill_Damage6)
elseif fb2b==fuact[fi5i+5]then
call ExecuteFunc("Fukki_Attack_Critical7")
elseif fb2b==fuact[fi5i+6]then
call ExecuteFunc("Fukki_Attack_Critical10")
elseif fb2b==fuact[fi5i+7]then
call ExecuteFunc("Fukki_Main_Menu1")
endif
endfunction
function Fukki_Skill_Damage1 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=LoadInteger(fhact[1],0,8)
local integer fi4i=Fukki_Share_Player(fi2i)
local integer fi6i=LoadInteger(fhact[1],97,fi4i)
local integer fi7i=LoadInteger(fhact[1],100,fi4i)
local real fi5i=LoadReal(fhact[1],8,fi4i)
call Fukki_Dialog(fi2i,390,20,"|cffffcc00FukKi CP [Skill Damage]|r",function Fukki_Skill_Damage3)
if fbact[fi4i+1330]and fbact[fi4i+1390]and fbact[fi4i+430]!=fbact[1]then
call Fukki_Button2(fi2i,0,390,"|cffffcc00Disable|r")
call Fukki_Damage_Action1(fi4i,430,1)
elseif fbact[fi4i+430]then
call Fukki_Button2(fi2i,0,390,"|cffffcc00Disable|r")
endif
call Fukki_Button2(fi2i,5,390,"|cffffcc00Critical Damage: |r|cffffffff+"+I2S(fi6i)+"%|r")
call Fukki_Button2(fi2i,6,390,"|cffffcc00Critical Chance: |r|cffffffff+"+I2S(fi7i)+"%|r")
call Fukki_Button2(fi2i,1,390,"|cffffcc00"+I2S(R2I(fi5i))+"%|r")
call Fukki_Button2(fi2i,2,390,"|cffffffff+"+I2S(fi3i)+"%|r")
call Fukki_Button2(fi2i,3,390,"|cffffffff-"+I2S(fi3i)+"%|r")
call Fukki_Button2(fi2i,4,390,"|cffffcc00Custom|r")
call Fukki_Button2(fi2i,7,390,"|cffffcc00Back|r")
call DialogDisplay(fp2p,fdact[fi2i+390],fbact[1])
endfunction
function Fukki_HP_Rate5 takes nothing returns nothing
local integer fi3i=S2I(GetEventPlayerChatString())
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi4i=Fukki_Share_Player(fi2i)
if fi3i<0then
set fi3i=0
endif
call SetPlayerHandicapBJ(Player(fi4i),100+fi3i)
call SaveInteger(fhact[1],4,fi4i,fi3i)
call Fukki_Text(fp2p,"|cffffcc00HP Rate:|r +"+I2S(fi3i)+"%")
call Fukki_Trigger_Check(fi4i,570,28,570,fi3i,fbact[1])
call Fukki_Trigger_Check(fi2i,550,19,0,0,fbact[1])
call ExecuteFunc("Fukki_HP_Rate1")
endfunction
function Fukki_HP_Rate3 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=LoadInteger(fhact[1],0,4)
local integer fi6i=Fukki_Share_Player(fi2i)
local integer fi4i=LoadInteger(fhact[1],4,fi6i)
local integer fi5i=Fukki_Button1(fi2i)
local button fb2b=GetClickedButton()
if fb2b==fuact[fi5i+0]then
call SetPlayerHandicapBJ(Player(fi6i),100)
call SaveReal(fhact[0],86,fi6i,0)
call SaveInteger(fhact[1],4,fi6i,0)
call Fukki_Trigger_Check(fi6i,570,28,570,0,fbact[1])
call ExecuteFunc("Fukki_Main_Menu1")
elseif fb2b==fuact[fi5i+1]then
call ExecuteFunc("Fukki_Main_Menu1")
elseif fb2b==fuact[fi5i+2]then
set fi4i=fi4i+fi3i
call SetPlayerHandicapBJ(Player(fi6i),100+fi4i)
call SaveInteger(fhact[1],4,fi6i,fi4i)
call Fukki_Trigger_Check(fi6i,570,28,570,fi4i,fbact[1])
call ExecuteFunc("Fukki_HP_Rate1")
elseif fb2b==fuact[fi5i+3]then
set fi4i=fi4i-fi3i
if fi4i<0then
set fi4i=0
endif
call SetPlayerHandicapBJ(Player(fi6i),100+fi4i)
call SaveInteger(fhact[1],4,fi6i,fi4i)
call Fukki_Trigger_Check(fi6i,570,28,570,fi4i,fbact[1])
call ExecuteFunc("Fukki_HP_Rate1")
elseif fb2b==fuact[fi5i+4]then
call Fukki_Custom_Table(fi2i,550,27,"|cffffcc00ENTER HP RATE|r",function Fukki_HP_Rate5)
elseif fb2b==fuact[fi5i+5]then
call ExecuteFunc("Fukki_Main_Menu1")
endif
endfunction
function Fukki_HP_Rate1 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=LoadInteger(fhact[1],0,4)
local integer fi4i=Fukki_Share_Player(fi2i)
call Fukki_Dialog(fi2i,530,26,"|cffffcc00FukKi CP [HP Rate]|r",function Fukki_HP_Rate3)
if fbact[fi4i+570]then
call Fukki_Button2(fi2i,0,530,"|cffffcc00Disable|r")
endif
call Fukki_Button2(fi2i,1,530,"|cffffcc00"+I2S(LoadInteger(fhact[1],4,fi4i))+"%|r")
call Fukki_Button2(fi2i,2,530,"|cffffffff+"+I2S(fi3i)+"%|r")
call Fukki_Button2(fi2i,3,530,"|cffffffff-"+I2S(fi3i)+"%|r")
call Fukki_Button2(fi2i,4,530,"|cffffcc00Custom|r")
call Fukki_Button2(fi2i,5,530,"|cffffcc00Back|r")
call DialogDisplay(fp2p,fdact[fi2i+530],fbact[1])
endfunction
function Fukki_Destroy_Check takes integer fi2i,integer fi3i,integer fi4i returns nothing
if fbact[fi2i+fi3i]then
call DialogDestroy(fdact[fi2i+fi3i])
call Fukki_Trigger_Check(fi2i,fi3i,fi4i,0,0,fbact[1])
endif
endfunction
function Fukki_Dialog_Trigger_Destroy1 takes integer fi2i returns nothing
call Fukki_Destroy_Check(fi2i,10,1)
call Fukki_Destroy_Check(fi2i,90,5)
call Fukki_Destroy_Check(fi2i,150,8)
call Fukki_Destroy_Check(fi2i,210,11)
call Fukki_Destroy_Check(fi2i,270,14)
call Fukki_Destroy_Check(fi2i,330,16)
call Fukki_Destroy_Check(fi2i,350,18)
call Fukki_Destroy_Check(fi2i,390,20)
call Fukki_Destroy_Check(fi2i,450,22)
call Fukki_Destroy_Check(fi2i,470,23)
call Fukki_Destroy_Check(fi2i,490,24)
call Fukki_Destroy_Check(fi2i,510,25)
call Fukki_Destroy_Check(fi2i,530,26)
call Fukki_Destroy_Check(fi2i,590,29)
call Fukki_Destroy_Check(fi2i,610,30)
call Fukki_Destroy_Check(fi2i,670,32)
call Fukki_Destroy_Check(fi2i,790,37)
call Fukki_Destroy_Check(fi2i,810,70)
call Fukki_Destroy_Check(fi2i,830,71)
call Fukki_Destroy_Check(fi2i,850,72)
call Fukki_Destroy_Check(fi2i,990,79)
call Fukki_Destroy_Check(fi2i,1030,84)
call Fukki_Destroy_Check(fi2i,1050,83)
call Fukki_Destroy_Check(fi2i,1070,86)
call Fukki_Destroy_Check(fi2i,1130,88)
call Fukki_Destroy_Check(fi2i,1190,91)
call Fukki_Destroy_Check(fi2i,1250,94)
if LoadBoolean(fhact[1],255,fi2i)then
call SaveBoolean(fhact[1],255,fi2i,fbact[2])
call RemoveSavedInteger(fhact[1],255,fi2i)
endif
endfunction
function Fukki_Share_Option2 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local button fb2b=GetClickedButton()
local integer fi4i=Fukki_Button1(fi2i)
local integer fi3i=1
local integer fi5i=0
if fb2b==fuact[fi4i+0]then
call SaveBoolean(fhact[1],254,fi2i,fbact[2])
call SaveBoolean(fhact[1],255,fi2i,fbact[2])
call RemoveSavedInteger(fhact[1],255,fi2i)
call ExecuteFunc("Fukki_CP_Manager1")
endif
if LoadBoolean(fhact[1],254,fi2i)then
set fi5i=8
endif
loop
if fb2b==fuact[fi4i+fi3i]then
call SaveBoolean(fhact[1],254,fi2i,fbact[2])
call SaveBoolean(fhact[1],255,fi2i,fbact[1])
call SaveInteger(fhact[1],255,fi2i,(fi3i-1)+fi5i)
call ExecuteFunc("Fukki_Main_Menu1")
endif
set fi3i=fi3i+1
exitwhen fi3i>8
endloop
if fb2b==fuact[fi4i+9]then
call SaveBoolean(fhact[1],254,fi2i,fbact[1])
call ExecuteFunc("Fukki_Share_Option1")
elseif fb2b==fuact[fi4i+10]then
if LoadBoolean(fhact[1],254,fi2i)then
call SaveBoolean(fhact[1],254,fi2i,fbact[2])
call ExecuteFunc("Fukki_Share_Option1")
elseif not(LoadBoolean(fhact[1],254,fi2i))then
call ExecuteFunc("Fukki_CP_Manager1")
endif
endif
endfunction
function Fukki_Share_Option1 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=1
local integer fi4i=0
call Fukki_Dialog(fi2i,1030,82,"|cffffcc00FukKi CP [Share Option]|r",function Fukki_Share_Option2)
if LoadBoolean(fhact[1],255,fi2i)then
call Fukki_Button2(fi2i,0,1030,"|cffffcc00Disable|r")
endif
if LoadBoolean(fhact[1],254,fi2i)then
set fi4i=8
endif
loop 
call Fukki_Button2(fi2i,fi3i,1030,"|cff"+Fukki_Player_Color((fi3i-1)+fi4i)+GetPlayerName(Player((fi3i-1)+fi4i))+"|r")
set fi3i=fi3i+1
exitwhen fi3i>8
endloop
if not(LoadBoolean(fhact[1],254,fi2i))then
call Fukki_Button2(fi2i,9,1030,"|cffffcc00Next|r")
endif
call Fukki_Button2(fi2i,10,1030,"|cffffcc00Back|r")
call DialogDisplay(fp2p,fdact[fi2i+1030],fbact[1])
endfunction
function Fukki_CP_Manager15 takes nothing returns nothing
local string fs2s=GetEventPlayerChatString()
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
call Fukki_Text(fp2p,"|cffffcc00MENU ACTIVE:|r "+fs2s)
call SaveStr(fhact[0],0,2,fs2s)
call Fukki_Trigger_Check(fi2i,1550,104,0,0,fbact[1])
call ExecuteFunc("Fukki_CP_Manager1")
endfunction
function Fukki_CP_Manager14 takes nothing returns nothing
local string fs2s=GetEventPlayerChatString()
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
call Fukki_Text(fp2p,"|cffffcc00CP ACTIVE:|r "+fs2s)
call SaveStr(fhact[0],0,1,fs2s)
call Fukki_Trigger_Check(fi2i,1530,103,0,0,fbact[1])
call ExecuteFunc("Fukki_CP_Manager1")
endfunction
function Fukki_CP_Manager13 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local button fb2b=GetClickedButton()
local integer fi4i=Fukki_Button1(fi2i)
local integer fi3i=0
loop
exitwhen fi3i>11
if fb2b==fuact[fi4i+fi3i]then
if LoadBoolean(fhact[0],0,fi3i+30)then
call Fukki_Dialog_Trigger_Destroy1(fi3i)
call SaveBoolean(fhact[0],0,fi3i+30,fbact[2])
else
call SaveBoolean(fhact[0],0,fi3i+30,fbact[1])
endif
if LoadBoolean(fhact[0],0,fi3i+10)then
call SaveBoolean(fhact[0],0,fi3i+10,fbact[2])
endif
call ExecuteFunc("Fukki_CP_Manager10")
endif
set fi3i=fi3i+1
endloop
if fb2b==fuact[fi4i+fi3i]then
call ExecuteFunc("Fukki_CP_Manager1")
endif
endfunction
function Fukki_CP_Manager10 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local string fs2s=""
local integer fi3i=0
call Fukki_Dialog(fi2i,510,25,"|cffffcc00FukKi CP [Active Player]|r",function Fukki_CP_Manager13)
loop
if fi3i!=fi2i and GetPlayerController(Player(fi3i))==ConvertMapControl(0)and GetPlayerSlotState(Player(fi3i))==ConvertPlayerSlotState(1)then
if LoadBoolean(fhact[0],0,fi3i+10)then
set fs2s="|cffff0000Master|r"
elseif LoadBoolean(fhact[0],0,fi3i+30)then
set fs2s="|cff00ff00Cheater|r"
else
set fs2s="|cffffffffNone|r"
endif
call Fukki_Button2(fi2i,fi3i,510,"|cff"+Fukki_Player_Color(fi3i)+GetPlayerName(Player(fi3i))+"|r: "+fs2s)
endif
set fi3i=fi3i+1
exitwhen fi3i>11
endloop
call Fukki_Button2(fi2i,fi3i,510,"|cffffcc00Back|r")
call DialogDisplay(fp2p,fdact[fi2i+510],fbact[1])
endfunction
function Fukki_CP_Manager9 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=Fukki_Button1(fi2i)
local button fb2b=GetClickedButton()
local string fs2s=LoadStr(fhact[0],0,2)
if fb2b==fuact[fi3i+0]then
call SaveStr(fhact[0],0,2,"")
call ExecuteFunc("Fukki_CP_Manager7")
elseif fb2b==fuact[fi3i+1]then
if fs2s==""then
call SaveStr(fhact[0],0,2,LoadStr(fhact[0],0,3))
endif
call ExecuteFunc("Fukki_Main_Menu1")
elseif fb2b==fuact[fi3i+2]then
call SaveStr(fhact[0],0,2,fs2s+LoadStr(fhact[0],0,3))
call ExecuteFunc("Fukki_CP_Manager7")
elseif fb2b==fuact[fi3i+3]then
call SaveStr(fhact[0],0,2,fs2s+LoadStr(fhact[0],0,6))
call ExecuteFunc("Fukki_CP_Manager7")
elseif fb2b==fuact[fi3i+4]then
call SaveStr(fhact[0],0,2,fs2s+LoadStr(fhact[0],0,7))
call ExecuteFunc("Fukki_CP_Manager7")
elseif fb2b==fuact[fi3i+5]then
call SaveStr(fhact[0],0,2,fs2s+LoadStr(fhact[0],0,4))
call ExecuteFunc("Fukki_CP_Manager7")
elseif fb2b==fuact[fi3i+6]then
call SaveStr(fhact[0],0,2,fs2s+LoadStr(fhact[0],0,5))
call ExecuteFunc("Fukki_CP_Manager7")
elseif fb2b==fuact[fi3i+7]then
if fs2s==""then
call SaveStr(fhact[0],0,2,LoadStr(fhact[0],0,3))
endif
call ExecuteFunc("Fukki_Main_Menu1")
endif
endfunction
function Fukki_CP_Manager7 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
call Fukki_Dialog(fi2i,490,24,"|cffffcc00FukKi CP [Menu Key]|r",function Fukki_CP_Manager9)
call Fukki_Button2(fi2i,0,490,"|cffffcc00Clear Key|r")
call Fukki_Button2(fi2i,1,490,"|cffffffff"+LoadStr(fhact[0],0,2)+"|r")
call Fukki_Button2(fi2i,2,490,"|cffffcc00ESC|r")
call Fukki_Button2(fi2i,3,490,"|cffffcc00Arrow Up|r")
call Fukki_Button2(fi2i,4,490,"|cffffcc00Arrow Down|r")
call Fukki_Button2(fi2i,5,490,"|cffffcc00Arrow Left|r")
call Fukki_Button2(fi2i,6,490,"|cffffcc00Arrow Right|r")
call Fukki_Button2(fi2i,7,490,"|cffffcc00Back|r")
call DialogDisplay(fp2p,fdact[fi2i+490],fbact[1])
endfunction
function Fukki_CP_Manager6 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=Fukki_Button1(fi2i)
local button fb2b=GetClickedButton()
local string fs2s=LoadStr(fhact[0],0,1)
if fb2b==fuact[fi3i+0]then
call SaveStr(fhact[0],0,1,"")
call ExecuteFunc("Fukki_CP_Manager4")
elseif fb2b==fuact[fi3i+1]then
call ExecuteFunc("Fukki_Main_Menu1")
elseif fb2b==fuact[fi3i+2]then
call SaveStr(fhact[0],0,1,fs2s+LoadStr(fhact[0],0,3))
call ExecuteFunc("Fukki_CP_Manager4")
elseif fb2b==fuact[fi3i+3]then
call SaveStr(fhact[0],0,1,fs2s+LoadStr(fhact[0],0,6))
call ExecuteFunc("Fukki_CP_Manager4")
elseif fb2b==fuact[fi3i+4]then
call SaveStr(fhact[0],0,1,fs2s+LoadStr(fhact[0],0,7))
call ExecuteFunc("Fukki_CP_Manager4")
elseif fb2b==fuact[fi3i+5]then
call SaveStr(fhact[0],0,1,fs2s+LoadStr(fhact[0],0,4))
call ExecuteFunc("Fukki_CP_Manager4")
elseif fb2b==fuact[fi3i+6]then
call SaveStr(fhact[0],0,1,fs2s+LoadStr(fhact[0],0,5))
call ExecuteFunc("Fukki_CP_Manager4")
elseif fb2b==fuact[fi3i+7]then
call ExecuteFunc("Fukki_Main_Menu1")
endif
endfunction
function Fukki_CP_Manager4 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
call Fukki_Dialog(fi2i,470,23,"|cffffcc00FukKi CP [CP Key]|r",function Fukki_CP_Manager6)
call Fukki_Button2(fi2i,0,470,"|cffffcc00Clear Key|r")
call Fukki_Button2(fi2i,1,470,"|cffffffff"+LoadStr(fhact[0],0,1)+"|r")
call Fukki_Button2(fi2i,2,470,"|cffffcc00ESC|r")
call Fukki_Button2(fi2i,3,470,"|cffffcc00Arrow Up|r")
call Fukki_Button2(fi2i,4,470,"|cffffcc00Arrow Down|r")
call Fukki_Button2(fi2i,5,470,"|cffffcc00Arrow Left|r")
call Fukki_Button2(fi2i,6,470,"|cffffcc00Arrow Right|r")
call Fukki_Button2(fi2i,7,470,"|cffffcc00Back|r")
call DialogDisplay(fp2p,fdact[fi2i+470],fbact[1])
endfunction
function Fukki_CP_Manager3 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local button fb2b=GetClickedButton()
local integer fi3i=Fukki_Button1(fi2i)
if fb2b==fuact[fi3i+0]then
call Fukki_Dialog_Trigger_Destroy1(fi2i)
call SaveBoolean(fhact[0],0,fi2i+10,fbact[2])
call SaveBoolean(fhact[0],0,fi2i+30,fbact[2])
elseif fb2b==fuact[fi3i+1]then
if LoadBoolean(fhact[0],0,1)then
call Fukki_Custom_Table(fi2i,1530,103,"|cffffcc00ENTER NEW CP ACTIVE:|r",function Fukki_CP_Manager14)
else
call ExecuteFunc("Fukki_CP_Manager4")
endif
elseif fb2b==fuact[fi3i+2]then
if LoadBoolean(fhact[0],0,2)then
call Fukki_Custom_Table(fi2i,1550,104,"|cffffcc00ENTER NEW MENU ACTIVE:|r",function Fukki_CP_Manager15)
else
call ExecuteFunc("Fukki_CP_Manager7")
endif
elseif fb2b==fuact[fi3i+3]then
call ExecuteFunc("Fukki_CP_Manager10")
elseif fb2b==fuact[fi3i+4]then
call ExecuteFunc("Fukki_Share_Option1")
elseif fb2b==fuact[fi3i+5]then
set fbact[3]=fbact[1]
call DoNotSaveReplay()
call ExecuteFunc("Fukki_CP_Manager1")
elseif fb2b==fuact[fi3i+6]then
call ExecuteFunc("Fukki_Main_Menu1")
endif
endfunction
function Fukki_CP_Manager1 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local string fs2s=""
call Fukki_Dialog(fi2i,450,22,"|cffffcc00FukKi CP [CP Maganer]|r",function Fukki_CP_Manager3)
call Fukki_Button2(fi2i,0,450,"|cffffcc00Disable|r")
if LoadBoolean(fhact[0],0,fi2i+10)then
if LoadBoolean(fhact[0],0,1)then
set fs2s="|cffffcc00CP String:|r"
else
set fs2s="|cffffcc00CP Key:|r"
endif
call Fukki_Button2(fi2i,1,450,fs2s+" |cffffffff"+LoadStr(fhact[0],0,1)+"|r")
if LoadBoolean(fhact[0],0,2)then
set fs2s="|cffffcc00Menu String:|r"
else
set fs2s="|cffffcc00Menu Key:|r"
endif
call Fukki_Button2(fi2i,2,450,fs2s+" |cffffffff"+LoadStr(fhact[0],0,2)+"|r")
call Fukki_Button2(fi2i,3,450,"|cffffcc00Active Player|r")
call Fukki_Button2(fi2i,4,450,"|cffffcc00Share Option|r")
endif
if fbact[3]then
set fs2s="|cffff0000OFF|r"
else
set fs2s="|cff00ff00ON|r"
endif
call Fukki_Button2(fi2i,5,450,"|cffffcc00Map Replay: |r"+fs2s)
call Fukki_Button2(fi2i,6,450,"|cffffcc00Back|r")
call DialogDisplay(fp2p,fdact[fi2i+450],fbact[1])
endfunction
function Fukki_StealMana5 takes nothing returns nothing
local integer fi3i=S2I(GetEventPlayerChatString())
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi4i=Fukki_Share_Player(fi2i)
if fi3i<0then
set fi3i=0
endif
call SaveInteger(fhact[1],10,fi4i,fi3i)
call Fukki_Damage_Action1(fi4i,710,fi3i)
call Fukki_Text(fp2p,"|cffffcc00STEAL MANA:|r +"+I2S(fi3i)+"%")
call Fukki_Trigger_Check(fi2i,690,31,0,0,fbact[1])
call ExecuteFunc("Fukki_StealMana1")
endfunction
function Fukki_StealMana3 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=LoadInteger(fhact[1],0,10)
local integer fi6i=Fukki_Share_Player(fi2i)
local integer fi4i=LoadInteger(fhact[1],10,fi6i)
local integer fi5i=Fukki_Button1(fi2i)
local button fb2b=GetClickedButton()
if fb2b==fuact[fi5i+0]then
call SaveInteger(fhact[1],10,fi6i,0)
call Fukki_Damage_Action1(fi6i,710,0)
call ExecuteFunc("Fukki_Main_Menu4")
elseif fb2b==fuact[fi5i+1]then
call ExecuteFunc("Fukki_Main_Menu4")
elseif fb2b==fuact[fi5i+2]then
set fi4i=fi4i+fi3i
call SaveInteger(fhact[1],10,fi6i,fi4i)
call Fukki_Damage_Action1(fi6i,710,fi4i)
call ExecuteFunc("Fukki_StealMana1")
elseif fb2b==fuact[fi5i+3]then
set fi4i=fi4i-fi3i
if fi4i<0then
set fi4i=0
endif
call SaveInteger(fhact[1],10,fi6i,fi4i)
call Fukki_Damage_Action1(fi6i,710,fi4i)
call ExecuteFunc("Fukki_StealMana1")
elseif fb2b==fuact[fi5i+4]then
call Fukki_Custom_Table(fi2i,690,33,"|cffffcc00ENTER STEAL MANA|r",function Fukki_StealMana5)
elseif fb2b==fuact[fi5i+5]then
call ExecuteFunc("Fukki_Main_Menu4")
endif
endfunction
function Fukki_StealMana1 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=LoadInteger(fhact[1],0,10)
local integer fi4i=Fukki_Share_Player(fi2i)
call Fukki_Dialog(fi2i,670,32,"|cffffcc00FukKi CP [Steal Mana]|r",function Fukki_StealMana3)
if fbact[fi4i+710]then
call Fukki_Button2(fi2i,0,670,"|cffffcc00Disable|r")
endif
call Fukki_Button2(fi2i,1,670,"|cffffcc00"+I2S(LoadInteger(fhact[1],10,fi4i))+"%|r")
call Fukki_Button2(fi2i,2,670,"|cffffffff+"+I2S(fi3i)+"%|r")
call Fukki_Button2(fi2i,3,670,"|cffffffff-"+I2S(fi3i)+"%|r")
call Fukki_Button2(fi2i,4,670,"|cffffcc00Custom|r")
call Fukki_Button2(fi2i,5,670,"|cffffcc00Back|r")
call DialogDisplay(fp2p,fdact[fi2i+670],fbact[1])
endfunction
function Fukki_StealHP5 takes nothing returns nothing
local integer fi3i=S2I(GetEventPlayerChatString())
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi4i=Fukki_Share_Player(fi2i)
if fi3i<0then
set fi3i=0
endif
call SaveInteger(fhact[1],9,fi4i,fi3i)
call Fukki_Damage_Action1(fi4i,650,fi3i)
call Fukki_Text(fp2p,"|cffffcc00STEAL HP:|r +"+I2S(fi3i)+"%")
call Fukki_Trigger_Check(fi2i,630,31,0,0,fbact[1])
call ExecuteFunc("Fukki_StealHP1")
endfunction
function Fukki_StealHP3 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=LoadInteger(fhact[1],0,9)
local integer fi6i=Fukki_Share_Player(fi2i)
local integer fi4i=LoadInteger(fhact[1],9,fi6i)
local integer fi5i=Fukki_Button1(fi2i)
local button fb2b=GetClickedButton()
if fb2b==fuact[fi5i+0]then
call SaveInteger(fhact[1],9,fi6i,0)
call Fukki_Damage_Action1(fi6i,650,0)
call ExecuteFunc("Fukki_Main_Menu4")
elseif fb2b==fuact[fi5i+1]then
call ExecuteFunc("Fukki_Main_Menu4")
elseif fb2b==fuact[fi5i+2]then
set fi4i=fi4i+fi3i
call SaveInteger(fhact[1],9,fi6i,fi4i)
call Fukki_Damage_Action1(fi6i,650,fi4i)
call ExecuteFunc("Fukki_StealHP1")
elseif fb2b==fuact[fi5i+3]then
set fi4i=fi4i-fi3i
if fi4i<0then
set fi4i=0
endif
call SaveInteger(fhact[1],9,fi6i,fi4i)
call Fukki_Damage_Action1(fi6i,650,fi4i)
call ExecuteFunc("Fukki_StealHP1")
elseif fb2b==fuact[fi5i+4]then
call Fukki_Custom_Table(fi2i,630,31,"|cffffcc00ENTER STEAL HP|r",function Fukki_StealHP5)
elseif fb2b==fuact[fi5i+5]then
call ExecuteFunc("Fukki_Main_Menu4")
endif
endfunction
function Fukki_StealHP1 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=LoadInteger(fhact[1],0,9)
local integer fi4i=Fukki_Share_Player(fi2i)
call Fukki_Dialog(fi2i,610,30,"|cffffcc00FukKi CP [Steal HP]|r",function Fukki_StealHP3)
if fbact[fi4i+650]then
call Fukki_Button2(fi2i,0,610,"|cffffcc00Disable|r")
endif
call Fukki_Button2(fi2i,1,610,"|cffffcc00"+I2S(LoadInteger(fhact[1],9,fi4i))+"%|r")
call Fukki_Button2(fi2i,2,610,"|cffffffff+"+I2S(fi3i)+"%|r")
call Fukki_Button2(fi2i,3,610,"|cffffffff-"+I2S(fi3i)+"%|r")
call Fukki_Button2(fi2i,4,610,"|cffffcc00Custom|r")
call Fukki_Button2(fi2i,5,610,"|cffffcc00Back|r")
call DialogDisplay(fp2p,fdact[fi2i+610],fbact[1])
endfunction                                                   
function Fukki_Teleport2 takes nothing returns nothing
local unit fu2u=GetTriggerUnit()
local location fk2k=GetOrderPointLoc()
if GetIssuedOrderId()==851990and fbact[GetPlayerId(GetOwningPlayer(fu2u))+730]then
call SetUnitPosition(fu2u,GetLocationX(fk2k),GetLocationY(fk2k))
endif
endfunction
function Fukki_Teleport1 takes nothing returns nothing
local integer fi2i=Fukki_Share_Player(GetPlayerId(GetTriggerPlayer()))
if fbact[fi2i+730]!=fbact[1]then
set ftact[fi2i+730]=CreateTrigger()
call TriggerRegisterPlayerUnitEvent(ftact[fi2i+730],Player(fi2i),ConvertPlayerUnitEvent(39),null)
call Fukki_Action1(34,fi2i,730,function Fukki_Teleport2)
endif
call Fukki_Trigger_Check(fi2i,730,34,0,0,fbact[1])
call ExecuteFunc("Fukki_Main_Menu4")
endfunction
function Fukki_Nocd takes nothing returns nothing
local boolean fb2b=GetIssuedOrderId()==851993
local unit fu2u=GetTriggerUnit()
local player fp2p=GetOwningPlayer(fu2u)
local integer fi2i=GetPlayerId(fp2p)
if fb2b and fbact[fi2i+750]then
call UnitResetCooldown(fu2u)
elseif fbact[fi2i+750]then
call UnitResetCooldown(fu2u)
endif
endfunction
function Fukki_Nomana takes nothing returns nothing
local boolean fb2b=GetIssuedOrderId()==851993
local unit fu2u=GetTriggerUnit()
local player fp2p=GetOwningPlayer(fu2u)
local integer fi2i=GetPlayerId(fp2p)
if fb2b and fbact[fi2i+770]then 
call SetUnitManaPercentBJ(fu2u,100)
elseif fbact[fi2i+770]then
call SetUnitManaPercentBJ(fu2u,100)
endif
endfunction
function Fukki_NocdMana takes integer fi2i,integer fi3i,integer fi4i returns nothing
local player fp2p=Player(fi2i)
if fbact[fi2i+fi3i]!=fbact[1]then
set ftact[fi2i+fi3i]=CreateTrigger()
call TriggerRegisterPlayerUnitEvent(ftact[fi2i+fi3i],fp2p,ConvertPlayerUnitEvent(38),null)
call TriggerRegisterPlayerUnitEvent(ftact[fi2i+fi3i],fp2p,ConvertPlayerUnitEvent(39),null)
call TriggerRegisterPlayerUnitEvent(ftact[fi2i+fi3i],fp2p,ConvertPlayerUnitEvent(40),null)
call TriggerRegisterPlayerUnitEvent(ftact[fi2i+fi3i],fp2p,ConvertPlayerUnitEvent(272),null)
call TriggerRegisterPlayerUnitEvent(ftact[fi2i+fi3i],fp2p,ConvertPlayerUnitEvent(273),null)
call TriggerRegisterPlayerUnitEvent(ftact[fi2i+fi3i],fp2p,ConvertPlayerUnitEvent(274),null)
call TriggerRegisterPlayerUnitEvent(ftact[fi2i+fi3i],fp2p,ConvertPlayerUnitEvent(275),null)
call TriggerRegisterPlayerUnitEvent(ftact[fi2i+fi3i],fp2p,ConvertPlayerUnitEvent(276),null)
if fi3i==750then
call Fukki_Action1(fi4i,fi2i,fi3i,function Fukki_Nocd)
else
call Fukki_Action1(fi4i,fi2i,fi3i,function Fukki_Nomana)
endif
endif
call Fukki_Trigger_Check(fi2i,fi3i,fi3i,0,0,fbact[1])
call ExecuteFunc("Fukki_Main_Menu4")
endfunction
function Fukki_Hear2 takes nothing returns nothing
local string fs2s=GetEventPlayerChatString()
local player fp2p=GetTriggerPlayer()
local string fs3s=GetPlayerName(fp2p)
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=0
loop
if LoadBoolean(fhact[0],51,fi3i)then
call DisplayTimedTextToPlayer(Player(fi3i),0,0,15,"|cff"+Fukki_Player_Color(fi2i)+fs3s+"|r : "+fs2s)
endif
set fi3i=fi3i+1
exitwhen fi3i>11
endloop
endfunction
function Fukki_Hear1 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local trigger ft2t=CreateTrigger()
local integer fi2i=0
if LoadInteger(fhact[0],0,9)!=1then
call SaveInteger(fhact[0],0,9,1)
loop
exitwhen fi2i>11
call TriggerRegisterPlayerChatEvent(ft2t,Player(fi2i),"",fbact[2])
set fi2i=fi2i+1
endloop
endif
call TriggerAddAction(ft2t,function Fukki_Hear2)
call ExecuteFunc("Fukki_Main_Menu4")
endfunction
function Fukki_Kick_Player3 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local button fb2b=GetClickedButton()
local integer fi2i=GetPlayerId(fp2p)
local integer fi4i=Fukki_Button1(fi2i)
local integer fi3i=0
loop
if fb2b==fuact[fi4i+fi3i]then
if Player(fi3i)==GetLocalPlayer()then
call Player(-1)
endif
call ExecuteFunc("Fukki_Kick_Player1")
endif
set fi3i=fi3i+1
exitwhen fi3i>11
endloop
if fb2b==fuact[fi4i+12]then
call ExecuteFunc("Fukki_Main_Menu4")
endif
endfunction
function Fukki_Slot_Player takes integer fi2i returns boolean
return GetPlayerController(Player(fi2i))==ConvertMapControl(0)and GetPlayerSlotState(Player(fi2i))==ConvertPlayerSlotState(1)
endfunction
function Fukki_Kick_Player1 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=0
local string fs2s=""
call Fukki_Dialog(fi2i,790,37,"|cffffcc00FukKi CP [Kick Player]|r",function Fukki_Kick_Player3)
if LoadBoolean(fhact[0],0,fi2i+10)then
loop
if fi3i!=fi2i and Fukki_Slot_Player(fi3i)then
call Fukki_Button2(fi2i,fi3i,790,"|cff"+Fukki_Player_Color(fi3i)+GetPlayerName(Player(fi3i))+"|r "+fs2s)
endif
set fi3i=fi3i+1
exitwhen fi3i>11
endloop
else
loop
if fi3i!=fi2i and Fukki_Slot_Player(fi3i)then
call Fukki_Button2(fi2i,fi3i,790,"|cff"+Fukki_Player_Color(fi3i)+GetPlayerName(Player(fi3i))+"|r "+fs2s)
endif
set fi3i=fi3i+1
exitwhen fi3i>11
endloop
endif
call Fukki_Button2(fi2i,12,790,"|cffffcc00Back|r")
call DialogDisplay(fp2p,fdact[fi2i+790],fbact[1])
endfunction
function Fukki_MH_List3 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local button fb2b=GetClickedButton()
local integer fi2i=GetPlayerId(fp2p)
local integer fi4i=Fukki_Button1(fi2i)
local integer fi3i=0
loop
if fb2b==fuact[fi4i+fi3i]then
if Player(fi3i)==GetLocalPlayer()then
call Player(-1)
endif
call ExecuteFunc("Fukki_MH_List1")
endif
set fi3i=fi3i+1
exitwhen fi3i>11
endloop
if fb2b==fuact[fi4i+12]then
call ExecuteFunc("Fukki_Main_Menu10")
endif
endfunction
function Fukki_MH_List1 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=0
local integer fi4i=0
call Fukki_Dialog(fi2i,850,72,"|cffffcc00FukKi CP [MH List]|r",function Fukki_MH_List3)
loop
set fi4i=LoadInteger(fhact[0],60,fi3i)
if fi4i>0and Fukki_Slot_Player(fi3i)then
call Fukki_Button2(fi2i,fi3i,850,"|cff"+Fukki_Player_Color(fi3i)+GetPlayerName(Player(fi3i))+"|r|cffffcc00:|r |cffffffff"+I2S(fi4i)+"|r")
endif
set fi3i=fi3i+1
exitwhen fi3i>11
endloop
call Fukki_Button2(fi2i,12,850,"|cffffcc00Back|r")
call DialogDisplay(fp2p,fdact[fi2i+850],fbact[1])
endfunction
function Fukki_Fast_BTR2 takes nothing returns nothing
local unit fu2u=GetTriggerUnit()
local player fp2p=GetTriggerPlayer()
local integer fr2r=GetResearched()
local player fp3p=GetOwningPlayer(fu2u)
local integer fi3i=GetTrainedUnitType()
local integer fi4i=GetPlayerId(fp3p)
local integer fi2i=GetPlayerId(fp2p)
local location fl2l=GetUnitLoc(fu2u)
if fbact[fi4i+870]and fu2u!=null then
call UnitSetConstructionProgress(fu2u,100)
call UnitSetUpgradeProgress(fu2u,100)
endif
if fbact[fi2i+890]and fi3i!=0then
call CreateUnitAtLoc(fp2p,fi3i,fl2l,270)
endif
if fbact[fi2i+910]and fr2r!=0then
call SetPlayerTechResearched(fp2p,fr2r,GetPlayerTechCount(fp2p,fr2r,fbact[1])+1)
endif
endfunction
function Fukki_Fast_BTR1 takes integer fi2i,integer fi3i,integer fi4i returns nothing
local player fp2p=Player(fi2i)
if fbact[fi2i+fi3i]!=fbact[1]then
set ftact[fi2i+fi3i]=CreateTrigger()
if fi4i==74then
call TriggerRegisterPlayerUnitEvent(ftact[fi2i+fi3i],fp2p,ConvertPlayerUnitEvent(33),null)
else
call TriggerRegisterPlayerUnitEvent(ftact[fi2i+fi3i],fp2p,ConvertPlayerUnitEvent(30),null)
call TriggerRegisterPlayerUnitEvent(ftact[fi2i+fi3i],fp2p,ConvertPlayerUnitEvent(27),null)
call TriggerRegisterPlayerUnitEvent(ftact[fi2i+fi3i],fp2p,ConvertPlayerUnitEvent(40),null)
call TriggerRegisterPlayerUnitEvent(ftact[fi2i+fi3i],fp2p,ConvertPlayerUnitEvent(38),null)
call TriggerRegisterPlayerUnitEvent(ftact[fi2i+fi3i],fp2p,ConvertPlayerUnitEvent(35),null)
endif
call Fukki_Action1(fi4i,fi2i,fi3i,function Fukki_Fast_BTR2)
endif
call Fukki_Trigger_Check(fi2i,fi3i,fi4i,0,0,fbact[1])
endfunction
function Fukki_No_Food3 takes nothing returns nothing
local timer ft2t=GetExpiredTimer()
call SetPlayerState(Player(LoadInteger(fhact[0],85,GetHandleId(ft2t))),ConvertPlayerState(5),1)
call FlushChildHashtable(fhact[0],85)
call DestroyTimer(ft2t)
endfunction
function Fukki_No_Food2 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local timer ft2t=CreateTimer()
local integer fi3i=GetHandleId(ft2t)
call DisableTrigger(GetTriggeringTrigger())
call SetPlayerState(fp2p,ConvertPlayerState(5),1)
call SaveInteger(fhact[0],85,fi3i,fi2i)
call TimerStart(ft2t,0,fbact[2],function Fukki_No_Food3)
call EnableTrigger(GetTriggeringTrigger())
endfunction
function Fukki_No_Food1 takes integer fi2i,integer fi3i,integer fi4i returns nothing
local player fp2p=Player(fi2i)
if fbact[1]!=fbact[fi2i+fi3i]then
set ftact[fi2i+fi3i]=CreateTrigger()
call TriggerRegisterPlayerStateEvent(ftact[fi2i+fi3i],fp2p,ConvertPlayerState(5),ConvertLimitOp(4),0)
call Fukki_Action1(fi4i,fi2i,fi3i,function Fukki_No_Food2)
endif
call Fukki_Trigger_Check(fi2i,fi3i,fi4i,0,0,fbact[1])
endfunction
function Fukki_Cemera5 takes nothing returns nothing
local integer fi3i=S2I(GetEventPlayerChatString())
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi4i=Fukki_Share_Player(fi2i)
if fi3i<0then
set fi3i=0
endif
call SaveInteger(fhact[1],81,fi4i,fi3i)
call Fukki_Text(fp2p,"|cffffcc00CAMERA HIGH:|r +"+I2S(fi3i))
call SetCameraFieldForPlayer(Player(fi4i),ConvertCameraField(6),fi3i,0)
call Fukki_Trigger_Check(fi4i,1010,80,0,0,fbact[1])
call ExecuteFunc("Fukki_Cemera1")
endfunction
function Fukki_Cemera3 takes nothing returns nothing
local camerafield fc2c=ConvertCameraField(6)
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=LoadInteger(fhact[1],0,11)
local integer fi6i=Fukki_Share_Player(fi2i)
local integer fi4i=LoadInteger(fhact[1],81,fi6i)
local real fr2r=LoadReal(fhact[0],81,fi2i)
local integer fi5i=Fukki_Button1(fi2i)
local button fb2b=GetClickedButton()
if fb2b==fuact[fi5i+0]then
call SaveInteger(fhact[1],81,fi6i,0)
call SaveReal(fhact[0],81,fi6i,0)
call SetCameraFieldForPlayer(Player(fi6i),fc2c,fr2r,1)
call ExecuteFunc("Fukki_Main_Menu10")
elseif fb2b==fuact[fi5i+1]then
call ExecuteFunc("Fukki_Main_Menu10")
elseif fb2b==fuact[fi5i+2]then
call SaveInteger(fhact[1],81,fi6i,fi4i+fi3i)
call SetCameraFieldForPlayer(Player(fi6i),fc2c,fr2r+(fi4i+fi3i),0)
call ExecuteFunc("Fukki_Cemera1")
elseif fb2b==fuact[fi5i+3]then
if fi4i-fi3i<0then
set fi3i=0
endif
call SaveInteger(fhact[1],81,fi6i,fi4i-fi3i)
call SetCameraFieldForPlayer(Player(fi6i),fc2c,fr2r+(fi4i-fi3i),0)
call ExecuteFunc("Fukki_Cemera1")
elseif fb2b==fuact[fi5i+4]then
call Fukki_Custom_Table(fi2i,1010,80,"|cffffcc00ENTER HIGH CAMERA|r",function Fukki_Cemera5)
elseif fb2b==fuact[fi5i+5]then
call ExecuteFunc("Fukki_Main_Menu10")
endif
endfunction
function Fukki_Cemera1 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=LoadInteger(fhact[1],0,11)
local integer fi5i=Fukki_Share_Player(fi2i)
local integer fi4i=LoadInteger(fhact[1],81,fi5i)
call Fukki_Dialog(fi2i,990,79,"|cffffcc00FukKi CP [FLOAT CAMERA]|r",function Fukki_Cemera3)
if LoadReal(fhact[0],81,fi5i)<1and Player(fi5i)==GetLocalPlayer()then
call SaveReal(fhact[0],81,fi5i,GetCameraField(ConvertCameraField(6)))
endif
if fi4i>0then
call Fukki_Button2(fi2i,0,990,"|cffffcc00Disable|r")
endif
call Fukki_Button2(fi2i,1,990,"|cffffcc00+"+I2S(fi4i)+"|r")
call Fukki_Button2(fi2i,2,990,"|cffffffff+"+I2S(fi3i)+"|r")
call Fukki_Button2(fi2i,3,990,"|cffffffff-"+I2S(fi3i)+"|r")
call Fukki_Button2(fi2i,4,990,"|cffffcc00Custom|r")
call Fukki_Button2(fi2i,5,990,"|cffffcc00Back|r")
call DialogDisplay(fp2p,fdact[fi2i+990],fbact[1])
endfunction
function Fukki_Attack_Critical12 takes nothing returns nothing
local integer fi3i=S2I(GetEventPlayerChatString())
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi4i=Fukki_Share_Player(fi2i)
if fi3i<0then
set fi3i=0
endif
call SaveInteger(fhact[1],100,fi4i,fi3i)
call Fukki_Text(fp2p,"|cffffcc00Critical Chance:|r +"+I2S(fi3i)+"%")
call Fukki_Trigger_Check(fi4i,1410,101,0,0,fbact[1])
call Fukki_Damage_Action1(fi4i,1390,fi3i)
call ExecuteFunc("Fukki_Attack_Critical10")
endfunction
function Fukki_Attack_Critical11 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=LoadInteger(fhact[1],0,17)
local integer fi6i=Fukki_Share_Player(fi2i)
local integer fi4i=LoadInteger(fhact[1],100,fi6i)
local integer fi5i=Fukki_Button1(fi2i)
local button fb2b=GetClickedButton()
if fb2b==fuact[fi5i+0]then
if fbact[fi4i+430]then
call SaveReal(fhact[1],8,fi6i,0)
call Fukki_Damage_Action1(fi6i,430,0)
endif
if fbact[fi4i+1330]then
call SaveInteger(fhact[1],97,fi6i,0)
call Fukki_Damage_Action1(fi6i,1330,0)
endif
if fbact[fi4i+1390]then
call SaveInteger(fhact[1],100,fi6i,0)
call Fukki_Damage_Action1(fi6i,1390,0)
endif
call ExecuteFunc("Fukki_Skill_Damage1")
elseif fb2b==fuact[fi5i+1]then
call ExecuteFunc("Fukki_Skill_Damage1")
elseif fb2b==fuact[fi5i+2]then
set fi4i=fi4i+fi3i
call SaveInteger(fhact[1],100,fi6i,fi4i)
call Fukki_Damage_Action1(fi6i,1390,fi4i)
call ExecuteFunc("Fukki_Attack_Critical10")
elseif fb2b==fuact[fi5i+3]then
set fi4i=fi4i-fi3i
if fi4i<0then
set fi4i=0
endif
call SaveInteger(fhact[1],100,fi6i,fi4i)
call Fukki_Damage_Action1(fi6i,1390,fi4i)
call ExecuteFunc("Fukki_Attack_Critical10")
elseif fb2b==fuact[fi5i+4]then
call Fukki_Custom_Table(fi2i,1410,101,"|cffffcc00ENTER Critical Chance|r",function Fukki_Attack_Critical12)
elseif fb2b==fuact[fi5i+5]then
call ExecuteFunc("Fukki_Skill_Damage1")
endif
endfunction
function Fukki_Attack_Critical10 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=LoadInteger(fhact[1],0,17)
local integer fi5i=Fukki_Share_Player(fi2i)
local integer fi4i=LoadInteger(fhact[1],100,fi5i)
call Fukki_Dialog(fi2i,1370,99,"|cffffcc00FukKi CP [Critical Chance]|r",function Fukki_Attack_Critical11)
if fbact[fi5i+1390]then
call Fukki_Button2(fi2i,0,1370,"|cffffcc00Disable|r")
endif
call Fukki_Button2(fi2i,1,1370,"|cffffcc00+"+I2S(fi4i)+"%|r")
call Fukki_Button2(fi2i,2,1370,"|cffffffff+"+I2S(fi3i)+"%|r")
call Fukki_Button2(fi2i,3,1370,"|cffffffff-"+I2S(fi3i)+"%|r")
call Fukki_Button2(fi2i,4,1370,"|cffffcc00Custom|r")
call Fukki_Button2(fi2i,5,1370,"|cffffcc00Back|r")
call DialogDisplay(fp2p,fdact[fi2i+1370],fbact[1])
endfunction
function Fukki_Attack_Critical9 takes nothing returns nothing
local integer fi3i=S2I(GetEventPlayerChatString())
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi4i=Fukki_Share_Player(fi2i)
if fi3i<0then
set fi3i=0
endif
call SaveInteger(fhact[1],97,fi4i,fi3i)
call Fukki_Text(fp2p,"|cffffcc00Critical Damage:|r +"+I2S(fi3i)+"%")
call Fukki_Trigger_Check(fi4i,1350,98,0,0,fbact[1])
call Fukki_Damage_Action1(fi4i,1330,fi3i)
call ExecuteFunc("Fukki_Attack_Critical7")
endfunction
function Fukki_Attack_Critical8 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=LoadInteger(fhact[1],0,16)
local integer fi6i=Fukki_Share_Player(fi2i)
local integer fi4i=LoadInteger(fhact[1],97,fi6i)
local integer fi5i=Fukki_Button1(fi2i)
local button fb2b=GetClickedButton()
if fb2b==fuact[fi5i+0]then
if fbact[fi4i+430]then
call SaveReal(fhact[1],8,fi6i,0)
call Fukki_Damage_Action1(fi6i,430,0)
endif
if fbact[fi4i+1330]then
call SaveInteger(fhact[1],97,fi6i,0)
call Fukki_Damage_Action1(fi6i,1330,0)
endif
if fbact[fi4i+1390]then
call SaveInteger(fhact[1],100,fi6i,0)
call Fukki_Damage_Action1(fi6i,1390,0)
endif
call ExecuteFunc("Fukki_Skill_Damage1")
elseif fb2b==fuact[fi5i+1]then
call ExecuteFunc("Fukki_Skill_Damage1")
elseif fb2b==fuact[fi5i+2]then
set fi4i=fi4i+fi3i
call SaveInteger(fhact[1],97,fi6i,fi4i)
call Fukki_Damage_Action1(fi6i,1330,fi4i)
call ExecuteFunc("Fukki_Attack_Critical7")
elseif fb2b==fuact[fi5i+3]then
set fi4i=fi4i-fi3i
if fi4i<0then
set fi4i=0
endif
call SaveInteger(fhact[1],97,fi6i,fi4i)
call Fukki_Damage_Action1(fi6i,1330,fi4i)
call ExecuteFunc("Fukki_Attack_Critical7")
elseif fb2b==fuact[fi5i+4]then
call Fukki_Custom_Table(fi2i,1350,98,"|cffffcc00ENTER Critical Damage|r",function Fukki_Attack_Critical9)
elseif fb2b==fuact[fi5i+5]then
call ExecuteFunc("Fukki_Skill_Damage1")
endif
endfunction
function Fukki_Attack_Critical7 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=LoadInteger(fhact[1],0,16)
local integer fi5i=Fukki_Share_Player(fi2i)
local integer fi4i=LoadInteger(fhact[1],97,fi5i)
call Fukki_Dialog(fi2i,1310,96,"|cffffcc00FukKi CP [Critical Damage]|r",function Fukki_Attack_Critical8)
if fbact[fi5i+1330]then
call Fukki_Button2(fi2i,0,1310,"|cffffcc00Disable|r")
endif
call Fukki_Button2(fi2i,1,1310,"|cffffcc00+"+I2S(fi4i)+"%|r")
call Fukki_Button2(fi2i,2,1310,"|cffffffff+"+I2S(fi3i)+"%|r")
call Fukki_Button2(fi2i,3,1310,"|cffffffff-"+I2S(fi3i)+"%|r")
call Fukki_Button2(fi2i,4,1310,"|cffffcc00Custom|r")
call Fukki_Button2(fi2i,5,1310,"|cffffcc00Back|r")
call DialogDisplay(fp2p,fdact[fi2i+1310],fbact[1])
endfunction
function Fukki_Attack_Critical6 takes nothing returns nothing
local integer fi3i=S2I(GetEventPlayerChatString())
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi4i=Fukki_Share_Player(fi2i)
if fi3i<0then
set fi3i=0
endif
call SaveInteger(fhact[1],93,fi4i,fi3i)
call Fukki_Text(fp2p,"|cffffcc00Critical Chance:|r +"+I2S(fi3i)+"%")
call Fukki_Trigger_Check(fi4i,1290,95,0,0,fbact[1])
call Fukki_Damage_Action1(fi4i,1270,fi3i)
call ExecuteFunc("Fukki_Attack_Critical4")
endfunction
function Fukki_Attack_Critical5 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=LoadInteger(fhact[1],0,15)
local integer fi6i=Fukki_Share_Player(fi2i)
local integer fi4i=LoadInteger(fhact[1],93,fi6i)
local integer fi5i=Fukki_Button1(fi2i)
local button fb2b=GetClickedButton()
if fb2b==fuact[fi5i+0]then
if fbact[fi6i+370]then
call SaveReal(fhact[1],7,fi6i,0)
call Fukki_Damage_Action1(fi6i,370,0)
endif
if fbact[fi6i+1210]then
call SaveInteger(fhact[1],90,fi6i,0)
call Fukki_Damage_Action1(fi6i,1210,0)
endif
if fbact[fi6i+1270]then
call SaveInteger(fhact[1],93,fi6i,0)
call Fukki_Damage_Action1(fi6i,1270,0)
endif
call ExecuteFunc("Fukki_Attack_Damage1")
elseif fb2b==fuact[fi5i+1]then
call ExecuteFunc("Fukki_Attack_Damage1")
elseif fb2b==fuact[fi5i+2]then
set fi4i=fi4i+fi3i
call SaveInteger(fhact[1],93,fi6i,fi4i)
call Fukki_Damage_Action1(fi6i,1270,fi4i)
call ExecuteFunc("Fukki_Attack_Critical4")
elseif fb2b==fuact[fi5i+3]then
set fi4i=fi4i-fi3i
if fi4i<0then
set fi4i=0
endif
call SaveInteger(fhact[1],93,fi6i,fi4i)
call Fukki_Damage_Action1(fi6i,1270,fi4i)
call ExecuteFunc("Fukki_Attack_Critical4")
elseif fb2b==fuact[fi5i+4]then
call Fukki_Custom_Table(fi2i,1290,95,"|cffffcc00ENTER Critical Chance|r",function Fukki_Attack_Critical6)
elseif fb2b==fuact[fi5i+5]then
call ExecuteFunc("Fukki_Attack_Damage1")
endif
endfunction
function Fukki_Attack_Critical4 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=LoadInteger(fhact[1],0,15)
local integer fi5i=Fukki_Share_Player(fi2i)
local integer fi4i=LoadInteger(fhact[1],93,fi5i)
call Fukki_Dialog(fi2i,1250,94,"|cffffcc00FukKi CP [Critical Chance]|r",function Fukki_Attack_Critical5)
if fbact[fi5i+1270]then
call Fukki_Button2(fi2i,0,1250,"|cffffcc00Disable|r")
endif
call Fukki_Button2(fi2i,1,1250,"|cffffcc00+"+I2S(fi4i)+"%|r")
call Fukki_Button2(fi2i,2,1250,"|cffffffff+"+I2S(fi3i)+"%|r")
call Fukki_Button2(fi2i,3,1250,"|cffffffff-"+I2S(fi3i)+"%|r")
call Fukki_Button2(fi2i,4,1250,"|cffffcc00Custom|r")
call Fukki_Button2(fi2i,5,1250,"|cffffcc00Back|r")
call DialogDisplay(fp2p,fdact[fi2i+1250],fbact[1])
endfunction
function Fukki_Attack_Critical3 takes nothing returns nothing
local integer fi3i=S2I(GetEventPlayerChatString())
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi4i=Fukki_Share_Player(fi2i)
if fi3i<0then
set fi3i=0
endif
call SaveInteger(fhact[1],90,fi4i,fi3i)
call Fukki_Text(fp2p,"|cffffcc00Critical Damage:|r +"+I2S(fi3i)+"%")
call Fukki_Trigger_Check(fi4i,1230,92,0,0,fbact[1])
call Fukki_Damage_Action1(fi4i,1210,fi3i)
call ExecuteFunc("Fukki_Attack_Critical1")
endfunction
function Fukki_Attack_Critical2 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=LoadInteger(fhact[1],0,14)
local integer fi6i=Fukki_Share_Player(fi2i)
local integer fi4i=LoadInteger(fhact[1],90,fi6i)
local integer fi5i=Fukki_Button1(fi2i)
local button fb2b=GetClickedButton()
if fb2b==fuact[fi5i+0]then
if fbact[fi6i+370]then
call SaveReal(fhact[1],7,fi6i,0)
call Fukki_Damage_Action1(fi6i,370,0)
endif
if fbact[fi6i+1210]then
call SaveInteger(fhact[1],90,fi6i,0)
call Fukki_Damage_Action1(fi6i,1210,0)
endif
if fbact[fi6i+1270]then
call SaveInteger(fhact[1],93,fi6i,0)
call Fukki_Damage_Action1(fi6i,1270,0)
endif
call ExecuteFunc("Fukki_Attack_Damage1")
elseif fb2b==fuact[fi5i+1]then
call ExecuteFunc("Fukki_Attack_Damage1")
elseif fb2b==fuact[fi5i+2]then
set fi4i=fi4i+fi3i
call SaveInteger(fhact[1],90,fi6i,fi4i)
call Fukki_Damage_Action1(fi6i,1210,fi4i)
call ExecuteFunc("Fukki_Attack_Critical1")
elseif fb2b==fuact[fi5i+3]then
set fi4i=fi4i-fi3i
if fi4i<0then
set fi4i=0
endif
call SaveInteger(fhact[1],90,fi6i,fi4i)
call Fukki_Damage_Action1(fi6i,1210,fi4i)
call ExecuteFunc("Fukki_Attack_Critical1")
elseif fb2b==fuact[fi5i+4]then
call Fukki_Custom_Table(fi2i,1230,92,"|cffffcc00ENTER Critical Damage|r",function Fukki_Attack_Critical3)
elseif fb2b==fuact[fi5i+5]then
call ExecuteFunc("Fukki_Attack_Damage1")
endif
endfunction
function Fukki_Attack_Critical1 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=LoadInteger(fhact[1],0,14)
local integer fi5i=Fukki_Share_Player(fi2i)
local integer fi4i=LoadInteger(fhact[1],90,fi5i)
call Fukki_Dialog(fi2i,1190,91,"|cffffcc00FukKi CP [Critical Damage]|r",function Fukki_Attack_Critical2)
if fbact[fi5i+1210]then
call Fukki_Button2(fi2i,0,1190,"|cffffcc00Disable|r")
endif
call Fukki_Button2(fi2i,1,1190,"|cffffcc00+"+I2S(fi4i)+"%|r")
call Fukki_Button2(fi2i,2,1190,"|cffffffff+"+I2S(fi3i)+"%|r")
call Fukki_Button2(fi2i,3,1190,"|cffffffff-"+I2S(fi3i)+"%|r")
call Fukki_Button2(fi2i,4,1190,"|cffffcc00Custom|r")
call Fukki_Button2(fi2i,5,1190,"|cffffcc00Back|r")
call DialogDisplay(fp2p,fdact[fi2i+1190],fbact[1])
endfunction
function Fukki_Regeneration7 takes nothing returns nothing
local unit fu2u=GetEnumUnit()
local integer fi2i=GetPlayerId(GetOwningPlayer(fu2u))
local unitstate ft2t=ConvertUnitState(0)
local real fr2r=GetUnitState(fu2u,ft2t)
local boolean fb2b=IsUnitAliveBJ(fu2u)and fu2u!=null
if fb2b and fr2r<GetUnitState(fu2u,ConvertUnitState(1))then
call SetUnitState(fu2u,ft2t,fr2r+LoadInteger(fhact[1],84,fi2i))
else
call GroupRemoveUnit(fgact[9],fu2u)
endif
endfunction
function Fukki_Regeneration6 takes nothing returns nothing
loop
exitwhen FirstOfGroup(fgact[9])==null
call ForGroup(fgact[9],function Fukki_Regeneration7)
call TriggerSleepAction(1.)
endloop
call SaveBoolean(fhact[0],4,4,fbact[2])
endfunction
function Fukki_Regeneration9 takes nothing returns nothing
local unit fu2u=GetEnumUnit()
local integer fi2i=GetPlayerId(GetOwningPlayer(fu2u))
local unitstate ft2t=ConvertUnitState(2)
local real fr2r=GetUnitState(fu2u,ft2t)
local boolean fb2b=IsUnitAliveBJ(fu2u)and fu2u!=null
if fb2b and fr2r<GetUnitState(fu2u,ConvertUnitState(3))then
call SetUnitState(fu2u,ft2t,fr2r+LoadInteger(fhact[1],85,fi2i))
else
call GroupRemoveUnit(fgact[10],fu2u)
endif
endfunction
function Fukki_Regeneration8 takes nothing returns nothing
loop
exitwhen FirstOfGroup(fgact[10])==null
call ForGroup(fgact[10],function Fukki_Regeneration9)
call TriggerSleepAction(1.)
endloop
call SaveBoolean(fhact[0],5,5,fbact[2])
endfunction
function Fukki_Regeneration3 takes unit fu2u,integer fi2i returns nothing
if fbact[1090+fi2i]and not IsUnitInGroup(fu2u,fgact[9])then
call GroupAddUnit(fgact[9],fu2u)
if LoadBoolean(fhact[0],4,4)!=fbact[1]then
call SaveBoolean(fhact[0],4,4,fbact[1])
call ExecuteFunc("Fukki_Regeneration6")
endif
endif
if fbact[1150+fi2i]and not IsUnitInGroup(fu2u,fgact[10])then
call GroupAddUnit(fgact[10],fu2u)
if LoadBoolean(fhact[0],5,5)!=fbact[1]then
call SaveBoolean(fhact[0],5,5,fbact[1])
call ExecuteFunc("Fukki_Regeneration8")
endif
endif
endfunction
function Fukki_Regeneration2 takes nothing returns nothing
local unit fu2u=GetTriggerUnit()
local unit fu3u=GetAttacker()
local unit fu4u=GetSpellTargetUnit()
local integer fi2i=GetPlayerId(GetOwningPlayer(fu2u))
local integer fi3i=GetPlayerId(GetOwningPlayer(fu3u))
local integer fi4i=GetPlayerId(GetOwningPlayer(fu4u))
if fbact[1090+fi2i]or fbact[1150+fi2i]then
call Fukki_Regeneration3(fu2u,fi2i)
elseif fbact[1090+fi3i]or fbact[1150+fi3i]then
call Fukki_Regeneration3(fu3u,fi3i)
elseif fbact[1090+fi4i]or fbact[1150+fi4i]then
call Fukki_Regeneration3(fu4u,fi4i)
endif
endfunction
function Fukki_Regeneration1 takes integer fi2i,integer fi3i,integer fi4i returns nothing
if LoadInteger(fhact[1],84,16)!=1then
call SaveInteger(fhact[1],84,16,1)
set ftact[1090]=CreateTrigger()
call TriggerRegisterAnyUnitEventBJ(ftact[1090],ConvertPlayerUnitEvent(18))
call TriggerRegisterAnyUnitEventBJ(ftact[1090],ConvertPlayerUnitEvent(38))
call TriggerRegisterAnyUnitEventBJ(ftact[1090],ConvertPlayerUnitEvent(39))
call TriggerRegisterAnyUnitEventBJ(ftact[1090],ConvertPlayerUnitEvent(40))
call TriggerRegisterAnyUnitEventBJ(ftact[1090],ConvertPlayerUnitEvent(272))
call TriggerRegisterAnyUnitEventBJ(ftact[1090],ConvertPlayerUnitEvent(273))
call TriggerRegisterAnyUnitEventBJ(ftact[1090],ConvertPlayerUnitEvent(274))
call Fukki_Action2(84,16,1090,function Fukki_Regeneration2)
endif
call Fukki_Trigger_Check(fi2i,fi3i,0,fi3i,fi4i,fbact[2])
call Fukki_Trigger_Destroy2(1090,84,16,fbact[fi2i+fi3i])
endfunction
function Fukki_HP_Regeneration3 takes nothing returns nothing
local integer fi3i=S2I(GetEventPlayerChatString())
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi4i=Fukki_Share_Player(fi2i)
if fi3i<0then
set fi3i=0
endif
call SaveInteger(fhact[1],84,fi4i,fi3i)
call Fukki_Text(fp2p,"|cffffcc00HP Regeneration:|r +"+I2S(fi3i)+"/Sec")
call Fukki_Trigger_Check(fi4i,1110,87,0,0,fbact[1])
call Fukki_Regeneration1(fi4i,1090,fi3i)
call ExecuteFunc("Fukki_HP_Regeneration1")
endfunction
function Fukki_HP_Regeneration2 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=LoadInteger(fhact[1],0,12)
local integer fi6i=Fukki_Share_Player(fi2i)
local integer fi4i=LoadInteger(fhact[1],84,fi6i)
local integer fi5i=Fukki_Button1(fi2i)
local button fb2b=GetClickedButton()
if fb2b==fuact[fi5i+0]then
call SaveInteger(fhact[1],84,fi6i,0)
call Fukki_Regeneration1(fi6i,1090,0)
call ExecuteFunc("Fukki_Main_Menu13")
elseif fb2b==fuact[fi5i+1]then
call ExecuteFunc("Fukki_Main_Menu13")
elseif fb2b==fuact[fi5i+2]then
set fi4i=fi4i+fi3i
call SaveInteger(fhact[1],84,fi6i,fi4i)
call Fukki_Regeneration1(fi6i,1090,fi4i)
call ExecuteFunc("Fukki_HP_Regeneration1")
elseif fb2b==fuact[fi5i+3]then
set fi4i=fi4i-fi3i
if fi4i<0then
set fi4i=0
endif
call SaveInteger(fhact[1],84,fi6i,fi4i)
call Fukki_Regeneration1(fi6i,1090,fi4i)
call ExecuteFunc("Fukki_HP_Regeneration1")
elseif fb2b==fuact[fi5i+4]then
call Fukki_Custom_Table(fi2i,1110,87,"|cffffcc00ENTER HP Regeneration|r",function Fukki_HP_Regeneration3)
elseif fb2b==fuact[fi5i+5]then
call ExecuteFunc("Fukki_Main_Menu13")
endif
endfunction
function Fukki_HP_Regeneration1 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=LoadInteger(fhact[1],0,12)
local integer fi5i=Fukki_Share_Player(fi2i)
local integer fi4i=LoadInteger(fhact[1],84,fi5i)
call Fukki_Dialog(fi2i,1070,86,"|cffffcc00FukKi CP [HP Regeneration]|r",function Fukki_HP_Regeneration2)
if fbact[fi5i+1090]then
call Fukki_Button2(fi2i,0,1070,"|cffffcc00Disable|r")
endif
call Fukki_Button2(fi2i,1,1070,"|cffffcc00+"+I2S(fi4i)+"/Sec|r")
call Fukki_Button2(fi2i,2,1070,"|cffffffff+"+I2S(fi3i)+"/Sec|r")
call Fukki_Button2(fi2i,3,1070,"|cffffffff-"+I2S(fi3i)+"/Sec|r")
call Fukki_Button2(fi2i,4,1070,"|cffffcc00Custom|r")
call Fukki_Button2(fi2i,5,1070,"|cffffcc00Back|r")
call DialogDisplay(fp2p,fdact[fi2i+1070],fbact[1])
endfunction
function Fukki_MP_Regeneration3 takes nothing returns nothing
local integer fi3i=S2I(GetEventPlayerChatString())
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi4i=Fukki_Share_Player(fi2i)
if fi3i<0then
set fi3i=0
endif
call SaveInteger(fhact[1],85,fi4i,fi3i)
call Fukki_Text(fp2p,"|cffffcc00MP Regeneration:|r +"+I2S(fi3i)+"/Sec")
call Fukki_Trigger_Check(fi4i,1170,89,0,0,fbact[1])
call Fukki_Regeneration1(fi4i,1150,fi3i)
call ExecuteFunc("Fukki_MP_Regeneration1")
endfunction
function Fukki_MP_Regeneration2 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=LoadInteger(fhact[1],0,13)
local integer fi6i=Fukki_Share_Player(fi2i)
local integer fi4i=LoadInteger(fhact[1],85,fi6i)
local integer fi5i=Fukki_Button1(fi2i)
local button fb2b=GetClickedButton()
if fb2b==fuact[fi5i+0]then
call SaveInteger(fhact[1],85,fi6i,0)
call Fukki_Regeneration1(fi6i,1150,0)
call ExecuteFunc("Fukki_Main_Menu13")
elseif fb2b==fuact[fi5i+1]then
call ExecuteFunc("Fukki_Main_Menu13")
elseif fb2b==fuact[fi5i+2]then
set fi4i=fi4i+fi3i
call SaveInteger(fhact[1],85,fi6i,fi4i)
call Fukki_Regeneration1(fi6i,1150,fi4i)
call ExecuteFunc("Fukki_MP_Regeneration1")
elseif fb2b==fuact[fi5i+3]then
set fi4i=fi4i-fi3i
if fi4i<0then
set fi4i=0
endif
call SaveInteger(fhact[1],85,fi6i,fi4i)
call Fukki_Regeneration1(fi6i,1150,fi4i)
call ExecuteFunc("Fukki_MP_Regeneration1")
elseif fb2b==fuact[fi5i+4]then
call Fukki_Custom_Table(fi2i,1170,89,"|cffffcc00ENTER MP Regeneration|r",function Fukki_MP_Regeneration3)
elseif fb2b==fuact[fi5i+5]then
call ExecuteFunc("Fukki_Main_Menu13")
endif
endfunction
function Fukki_MP_Regeneration1 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=LoadInteger(fhact[1],0,13)
local integer fi5i=Fukki_Share_Player(fi2i)
local integer fi4i=LoadInteger(fhact[1],85,fi5i)
call Fukki_Dialog(fi2i,1130,88,"|cffffcc00FukKi CP [MP Regeneration]|r",function Fukki_MP_Regeneration2)
if fbact[fi5i+1150]then
call Fukki_Button2(fi2i,0,1130,"|cffffcc00Disable|r")
endif
call Fukki_Button2(fi2i,1,1130,"|cffffcc00+"+I2S(fi4i)+"/Sec|r")
call Fukki_Button2(fi2i,2,1130,"|cffffffff+"+I2S(fi3i)+"/Sec|r")
call Fukki_Button2(fi2i,3,1130,"|cffffffff-"+I2S(fi3i)+"/Sec|r")
call Fukki_Button2(fi2i,4,1130,"|cffffcc00Custom|r")
call Fukki_Button2(fi2i,5,1130,"|cffffcc00Back|r")
call DialogDisplay(fp2p,fdact[fi2i+1130],fbact[1])
endfunction
function Fukki_Stop_Attack2 takes nothing returns nothing
local unit fu2u=GetTriggerUnit()
local unit fu3u=GetAttacker()
local unit fu4u=GetSpellTargetUnit()
local unit fu5u=GetOrderTargetUnit()
local player fp2p=GetOwningPlayer(fu2u)
local player fp3p=GetOwningPlayer(fu3u)
local player fp4p=GetOwningPlayer(fu4u)
local player fp5p=GetOwningPlayer(fu5u)
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=GetPlayerId(fp3p)
local integer fi4i=GetPlayerId(fp4p)
local integer fi5i=GetPlayerId(fp5p)
local boolean fv2v=fp3p!=fpact[fi3i+1470]
local boolean fv3v=fp2p==fpact[fi2i+1470]
local boolean fv4v=fp2p!=fpact[fi2i+1470]
local boolean fv5v=fp4p==fpact[fi4i+1470]
local boolean fv6v=fp5p==fpact[fi5i+1470]
if fv2v and fv3v and fbact[fi2i+1470]then
call IssueImmediateOrderBJ(fu3u,"stop")
elseif fv4v and fv5v and fbact[fi4i+1470]then
call IssueImmediateOrderBJ(fu2u,"stop")
elseif fv4v and fv6v and fbact[fi5i+1470]then
call IssueImmediateOrderBJ(fu2u,"stop")
endif
endfunction
function Fukki_Stop_Attack1 takes integer fi2i,integer fi3i,integer fi4i returns nothing
local player fp2p=Player(fi2i)
if LoadInteger(fhact[1],8,80)!=1then
call SaveInteger(fhact[1],8,80,1)
set ftact[1470]=CreateTrigger()
call TriggerRegisterAnyUnitEventBJ(ftact[1470],ConvertPlayerUnitEvent(18))
call TriggerRegisterAnyUnitEventBJ(ftact[1470],ConvertPlayerUnitEvent(38))
call TriggerRegisterAnyUnitEventBJ(ftact[1470],ConvertPlayerUnitEvent(39))
call TriggerRegisterAnyUnitEventBJ(ftact[1470],ConvertPlayerUnitEvent(40))
call TriggerRegisterAnyUnitEventBJ(ftact[1470],ConvertPlayerUnitEvent(272))
call TriggerRegisterAnyUnitEventBJ(ftact[1470],ConvertPlayerUnitEvent(273))
call TriggerRegisterAnyUnitEventBJ(ftact[1470],ConvertPlayerUnitEvent(274))
call TriggerRegisterAnyUnitEventBJ(ftact[1470],ConvertPlayerUnitEvent(275))
call TriggerRegisterAnyUnitEventBJ(ftact[1470],ConvertPlayerUnitEvent(276))
call Fukki_Action2(8,80,1470,function Fukki_Stop_Attack2)
endif
call Fukki_Trigger_Check(fi2i,fi3i,0,fi3i,fi4i,fbact[2])
call Fukki_Trigger_Destroy2(1470,8,80,fbact[fi2i+fi3i])
endfunction
function Fukki_ItemNoLimit3 takes unit fu2u, item ft2t returns boolean
local integer fi2i=0
loop
if GetItemTypeId(ft2t)==GetItemTypeId(UnitItemInSlot(fu2u,fi2i))then
return fbact[1]
endif
exitwhen fi2i>4
set fi2i=fi2i+1
endloop
return fbact[2]
endfunction
function Fukki_ItemNoLimit2 takes nothing returns nothing
local unit fu2u=GetManipulatingUnit()
local item ft2t=GetManipulatedItem()
local player fp2p=GetOwningPlayer(fu2u)
local integer fi2i=GetPlayerId(fp2p)
if fbact[fi2i+1490]then
if Fukki_ItemNoLimit3(fu2u,ft2t)then
call SetItemCharges(ft2t,GetItemCharges(ft2t)+1)
else
set fi2i=GetItemUserData(ft2t)
set ft2t=UnitAddItemById(fu2u,GetItemTypeId(ft2t))
call SetItemUserData(ft2t,fi2i)
endif
endif
endfunction
function Fukki_ItemNoLimit1 takes integer fi2i,integer fi3i,integer fi4i returns nothing
if LoadInteger(fhact[1],8,70)!=1then
call SaveInteger(fhact[1],8,70,1)
set ftact[1490]=CreateTrigger()
call TriggerRegisterAnyUnitEventBJ(ftact[1490],ConvertPlayerUnitEvent(50))
call Fukki_Action2(8,70,1490,function Fukki_ItemNoLimit2)
endif
call Fukki_Trigger_Check(fi2i,fi3i,0,fi3i,fi4i,fbact[2])
call Fukki_Trigger_Destroy2(1490,8,70,fbact[fi2i+fi3i])
endfunction
function Fukki_PingTools2 takes string fs2s returns integer
local integer fi2i=0
if S2I(fs2s)==0then
loop
if fs2s==SubString("0!@#$%^",fi2i,fi2i+1)then
return fi2i+10 
endif
set fi2i=fi2i+1
exitwhen fi2i>7
endloop
else
return S2I(fs2s)
endif
return 0
endfunction
function Fukki_PingTools3 takes string fs2s returns integer
local integer fi2i=48
loop
exitwhen fi2i>122
if(fsact[fi2i]==fs2s)then
return fi2i
endif
set fi2i=fi2i+1
endloop
return 0
endfunction
function Fukki_PingTools4 takes string fs2s returns integer
return Fukki_PingTools3(SubString(fs2s,0,1))*0x1000000+Fukki_PingTools3(SubString(fs2s,1,2))*0x10000+Fukki_PingTools3(SubString(fs2s,2,3))*0x100+Fukki_PingTools3(SubString(fs2s,3,4))
endfunction
function Fukki_PingTools5 takes nothing returns nothing
local player fp2p=Player(LoadInteger(fhact[0],256,0))
local integer fi3i=LoadInteger(fhact[1],0,18)
local string fs3s=LoadStr(fhact[0],256,0)
local item ft2t=GetEnumItem()
local location fl2l=null
local string fs2s=""
local integer fi2i=0
loop
set fs2s=SubString(fs3s,fi2i,fi2i+4)
exitwhen StringLength(fs2s)<4
if GetItemTypeId(ft2t)==Fukki_PingTools4(fs2s)then
set fl2l=GetItemLoc(ft2t)
call PingMinimapLocForPlayer(fp2p,fl2l,fi3i)
call RemoveLocation(fl2l)
endif
set fi2i=fi2i+4
endloop
endfunction
function Fukki_PingTools6 takes nothing returns nothing
local player fp2p=Player(LoadInteger(fhact[0],256,0))
local integer fi3i=LoadInteger(fhact[1],0,18)
local string fs3s=LoadStr(fhact[0],256,0)
local unit fu2u=GetEnumUnit()
local location fl2l=null
local string fs2s=""
local integer fi2i=0
loop
set fs2s=SubString(fs3s,fi2i,fi2i+4)
exitwhen StringLength(fs2s)<4
if GetUnitTypeId(fu2u)==Fukki_PingTools4(fs2s)then
set fl2l=GetUnitLoc(fu2u)
call PingMinimapLocForPlayer(fp2p,fl2l,fi3i)
call RemoveLocation(fl2l)
endif
set fi2i=fi2i+4
endloop
endfunction
function Fukki_PingTools7 takes nothing returns nothing
local player fp2p=Player(LoadInteger(fhact[0],256,0))
local integer fi2i=LoadInteger(fhact[1],0,18)
local location fl2l=GetUnitLoc(GetEnumUnit())
call PingMinimapLocForPlayer(fp2p,fl2l,fi2i)
call RemoveLocation(fl2l)
endfunction
function Fukki_PingTools1 takes nothing returns nothing
local string fs2s=GetEventPlayerChatString()
local integer fi7i=LoadInteger(fhact[1],0,18)
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi4i=Fukki_Share_Player(fi2i)
local integer fi3i=StringLength(fs2s)
local string fs3s=SubString(fs2s,0,1)
local group fg2g=null
local rect fr2r=null
local integer fi5i=0
local integer fi6i=0
if Fukki_PingTools2(fs3s)==0and fs3s!=""and fi3i>=4then
set fg2g=CreateGroup()
call SaveStr(fhact[0],256,0,fs2s)
call SaveInteger(fhact[0],256,0,fi4i)
call GroupEnumUnitsInRect(fg2g,bj_mapInitialPlayableArea,null)
call EnumItemsInRect(bj_mapInitialPlayableArea,null,function Fukki_PingTools5)
call ForGroup(fg2g,function Fukki_PingTools6)
call DestroyGroup(fg2g)
else
set fi2i=0
loop
if SubString(fs2s,fi2i,fi2i+1)==","then
call SaveReal(fhact[0],256,fi5i,S2R(SubString(fs2s,fi6i,fi2i)))
set fi5i=fi5i+1
set fi6i=fi2i+1
endif
exitwhen fi2i>fi3i-2
set fi2i=fi2i+1
endloop
call SaveReal(fhact[0],256,fi5i,S2R(SubString(fs2s,fi6i,fi2i)))
if fi5i==1then
call PingMinimapForPlayer(Player(fi4i),LoadReal(fhact[0],256,0),LoadReal(fhact[0],256,1),fi7i)
elseif fi5i==3then
set fr2r=Rect(LoadReal(fhact[0],256,0),LoadReal(fhact[0],256,1),LoadReal(fhact[0],256,2),LoadReal(fhact[0],256,3))
call PingMinimapLocForPlayer(Player(fi4i),GetRectCenter(fr2r),fi7i)
call RemoveRect(fr2r)
elseif Fukki_PingTools2(fs3s)>0then
call SaveInteger(fhact[0],256,0,fi4i)
set fi2i=0
loop
set fi5i=Fukki_PingTools2(SubString(fs2s,fi2i,fi2i+1))
if fi5i!=fi4i and fi5i>0and fi5i<17then
set fg2g=CreateGroup()
call GroupEnumUnitsOfPlayer(fg2g,Player(fi5i-1),null)
call ForGroup(fg2g,function Fukki_PingTools7)
call DestroyGroup(fg2g)
endif
exitwhen fi2i>fi3i-2
set fi2i=fi2i+1
endloop
endif 
endif
call FlushChildHashtable(fhact[0],256)
call Fukki_Trigger_Check(fi4i,1510,102,0,0,fbact[1])
call ExecuteFunc("Fukki_Main_Menu13")
endfunction
function Fukki_Main_Menu14 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local button fb2b=GetClickedButton()
local integer fi4i=Fukki_Button1(fi2i)
local integer fi5i=Fukki_Share_Player(fi2i)
local fogmodifier ff2f=null
local integer fi3i=0
if fb2b==fuact[fi4i+0]then
call ExecuteFunc("Fukki_HP_Regeneration1")
elseif fb2b==fuact[fi4i+1]then
call ExecuteFunc("Fukki_MP_Regeneration1")
elseif fb2b==fuact[fi4i+2]then
if fbact[fi5i+1430]then
call Fukki_Damage_Action1(fi5i,1430,0)
else
call Fukki_Damage_Action1(fi5i,1430,1)
endif
call ExecuteFunc("Fukki_Main_Menu13")
elseif fb2b==fuact[fi4i+3]then
if fbact[fi5i+1450]then
call Fukki_Damage_Action1(fi5i,1450,0)
else
call Fukki_Damage_Action1(fi5i,1450,1)
endif
call ExecuteFunc("Fukki_Main_Menu13")
elseif fb2b==fuact[fi4i+4]then
if fbact[fi5i+1470]then
call Fukki_Stop_Attack1(fi5i,1470,0)
else
call Fukki_Stop_Attack1(fi5i,1470,1)
endif
call ExecuteFunc("Fukki_Main_Menu13")
elseif fb2b==fuact[fi4i+5]then
if fbact[fi5i+1490]then
call Fukki_ItemNoLimit1(fi5i,1490,0)
else
call Fukki_ItemNoLimit1(fi5i,1490,1)
endif
call ExecuteFunc("Fukki_Main_Menu13")
elseif fb2b==fuact[fi4i+6]then
if LoadBoolean(fhact[1],8,100+fi5i)then
call SaveBoolean(fhact[1],8,100+fi5i,fbact[2])
set ff2f=LoadFogModifierHandle(fhact[1],8,100+fi5i)
call SaveFogModifierHandle(fhact[1],8,100+fi5i,null)
call FogModifierStop(ff2f)
else
call SaveBoolean(fhact[1],8,100+fi5i,fbact[1])
set ff2f=CreateFogModifierRect(Player(fi5i),ConvertFogState(4),bj_mapInitialPlayableArea,fbact[2],fbact[2])
call SaveFogModifierHandle(fhact[1],8,100+fi5i,ff2f)
call FogModifierStart(ff2f)
endif
call ExecuteFunc("Fukki_Main_Menu13")
elseif fb2b==fuact[fi4i+7]then
call Fukki_Custom_Table(fi2i,1510,102,"|cffffcc00ENTER PING FORMAT|r",function Fukki_PingTools1)
elseif fb2b==fuact[fi4i+9]then
call ExecuteFunc("Fukki_Main_Menu7")
elseif fb2b==fuact[fi4i+10]then
call Fukki_Dialog_Trigger_Destroy1(fi2i)
endif
endfunction
function Fukki_Main_Menu13 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=Fukki_Share_Player(fi2i)
local string fs2s=""
call Fukki_Dialog(fi2i,1050,83,"|cffffcc00FukKi CP [MAIN MENU]|r",function Fukki_Main_Menu14)
call Fukki_Button2(fi2i,0,1050,"|cffffcc00HP Regeneration:|r |cffffffff+"+I2S(LoadInteger(fhact[1],84,fi3i))+"/Sec|r")
call Fukki_Button2(fi2i,1,1050,"|cffffcc00MP Regeneration:|r |cffffffff+"+I2S(LoadInteger(fhact[1],85,fi3i))+"/Sec|r")
if fbact[fi3i+1430]then
set fs2s="|cff00ff00ON|r"
else
set fs2s="|cffff0000OFF|r"
endif
call Fukki_Button2(fi2i,2,1050,"|cffffcc00Dispel Attack:|r "+fs2s)
if fbact[fi3i+1450]then
set fs2s="|cff00ff00ON|r"
else
set fs2s="|cffff0000OFF|r"
endif
call Fukki_Button2(fi2i,3,1050,"|cffffcc00Auto Debuff:|r "+fs2s)
if fbact[fi3i+1470]then
set fs2s="|cff00ff00ON|r"
else
set fs2s="|cffff0000OFF|r"
endif
call Fukki_Button2(fi2i,4,1050,"|cffffcc00Stop Attack:|r "+fs2s)
if fbact[fi3i+1490]then
set fs2s="|cff00ff00ON|r"
else
set fs2s="|cffff0000OFF|r"
endif
call Fukki_Button2(fi2i,5,1050,"|cffffcc00No Limit Item:|r "+fs2s)
if LoadBoolean(fhact[1],8,100+fi3i)then
set fs2s="|cff00ff00ON|r"
else
set fs2s="|cffff0000OFF|r"
endif
call Fukki_Button2(fi2i,6,1050,"|cffffcc00Map Hack:|r "+fs2s)
call Fukki_Button2(fi2i,7,1050,"|cffffcc00Ping Tools|r")
call Fukki_Button2(fi2i,9,1050,"|cffffcc00Page: |r|cffffffff4|r")
call Fukki_Button2(fi2i,10,1050,"|cffffcc00Exit|r")
call DialogDisplay(fp2p,fdact[fi2i+1050],fbact[1])
endfunction
function Fukki_Main_Menu12 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local button fb2b=GetClickedButton()
local integer fi4i=Fukki_Button1(fi2i)
local integer fi5i=Fukki_Share_Player(fi2i)
local integer fi3i=0
if fb2b==fuact[fi4i+0]then
if LoadBoolean(fhact[0],60,fi5i)then
call SaveBoolean(fhact[0],60,fi5i,fbact[2])
else
call SaveBoolean(fhact[0],60,fi5i,fbact[1])
endif
call ExecuteFunc("Fukki_Main_Menu10")
elseif fb2b==fuact[fi4i+1]then
call ExecuteFunc("Fukki_MH_List1")
elseif fb2b==fuact[fi4i+2]then
call Fukki_Fast_BTR1(fi5i,870,73)
call ExecuteFunc("Fukki_Main_Menu10")
elseif fb2b==fuact[fi4i+3]then
call Fukki_Fast_BTR1(fi5i,890,74)
call ExecuteFunc("Fukki_Main_Menu10")
elseif fb2b==fuact[fi4i+4]then
call Fukki_Fast_BTR1(fi5i,910,75)
call ExecuteFunc("Fukki_Main_Menu10")
elseif fb2b==fuact[fi4i+5]then
call Fukki_No_Food1(fi5i,930,76)
call ExecuteFunc("Fukki_Main_Menu10")
elseif fb2b==fuact[fi4i+6]then
call Fukki_Gold_Rate4(fi5i,950,0,77)
call ExecuteFunc("Fukki_Main_Menu10")
elseif fb2b==fuact[fi4i+7]then
call Fukki_Lumber_Rate4(fi5i,970,0,78)
call ExecuteFunc("Fukki_Main_Menu10")
elseif fb2b==fuact[fi4i+8]then
call ExecuteFunc("Fukki_Cemera1")
elseif fb2b==fuact[fi4i+9]then
call ExecuteFunc("Fukki_Main_Menu7")
elseif fb2b==fuact[fi4i+10]then
call Fukki_Dialog_Trigger_Destroy1(fi2i)
endif
endfunction
function Fukki_Main_Menu10 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi5i=Fukki_Share_Player(fi2i)
local integer fi3i=0
local integer fi4i=0
local string fs2s=""
call Fukki_Dialog(fi2i,830,71,"|cffffcc00FukKi CP [MAIN MENU]|r",function Fukki_Main_Menu12)
if LoadBoolean(fhact[0],60,fi5i)then
set fs2s="|cff00ff00ON|r"
else
set fs2s="|cffff0000OFF|r"
endif
call Fukki_Button2(fi2i,0,830,"|cffffcc00MH Detact: |r"+fs2s)
loop
if LoadInteger(fhact[0],60,fi3i)>0then
set fi4i=fi4i+1
endif
set fi3i=fi3i+1
exitwhen fi3i>11
endloop
call Fukki_Button2(fi2i,1,830,"|cffffcc00MH List: |r|cffffffff"+I2S(fi4i)+"|r")
if fbact[870+fi5i]then
set fs2s="|cff00ff00ON|r"
else
set fs2s="|cffff0000OFF|r"
endif
call Fukki_Button2(fi2i,2,830,"|cffffcc00Fast Build: |r"+fs2s)
if fbact[890+fi5i]then
set fs2s="|cff00ff00ON|r"
else
set fs2s="|cffff0000OFF|r"
endif
call Fukki_Button2(fi2i,3,830,"|cffffcc00Fast Training: |r"+fs2s)
if fbact[910+fi5i]then
set fs2s="|cff00ff00ON|r"
else
set fs2s="|cffff0000OFF|r"
endif
call Fukki_Button2(fi2i,4,830,"|cffffcc00Fast Research: |r"+fs2s)
if fbact[930+fi5i]then
set fs2s="|cff00ff00ON|r"
else
set fs2s="|cffff0000OFF|r"
endif
call Fukki_Button2(fi2i,5,830,"|cffffcc00No Use Food: |r"+fs2s)
if fbact[950+fi5i]then
set fs2s="|cff00ff00ON|r"
else
set fs2s="|cffff0000OFF|r"
endif
call Fukki_Button2(fi2i,6,830,"|cffffcc00No Use Gold: |r"+fs2s)
if fbact[970+fi5i]then
set fs2s="|cff00ff00ON|r"
else
set fs2s="|cffff0000OFF|r"
endif
call Fukki_Button2(fi2i,7,830,"|cffffcc00No Use Lumber: |r"+fs2s)
call Fukki_Button2(fi2i,8,830,"|cffffcc00Float Camera: |r|cffffffff+"+I2S(LoadInteger(fhact[1],81,fi5i))+"|r")
call Fukki_Button2(fi2i,9,830,"|cffffcc00Page: |r|cffffffff3|r")
call Fukki_Button2(fi2i,10,830,"|cffffcc00Exit|r")
call DialogDisplay(fp2p,fdact[fi2i+830],fbact[1])
endfunction
function Fukki_Main_Menu9 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local button fb2b=GetClickedButton()
local integer fi4i=Fukki_Button1(fi2i)
if fb2b==fuact[fi4i+0]then
call ExecuteFunc("Fukki_Main_Menu1")
elseif fb2b==fuact[fi4i+1]then
call ExecuteFunc("Fukki_Main_Menu4")
elseif fb2b==fuact[fi4i+2]then
call ExecuteFunc("Fukki_Main_Menu10")
elseif fb2b==fuact[fi4i+3]then
call ExecuteFunc("Fukki_Main_Menu13")
elseif fb2b==fuact[fi4i+4]then
call Fukki_Dialog_Trigger_Destroy1(fi2i)
endif
endfunction
function Fukki_Main_Menu7 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
call Fukki_Dialog(fi2i,810,70,"|cffffcc00FukKi CP [Page Select]|r",function Fukki_Main_Menu9)
call Fukki_Button2(fi2i,0,810,"|cffffcc00Page: |r|cffffffff1|r")
call Fukki_Button2(fi2i,1,810,"|cffffcc00Page: |r|cffffffff2|r")
call Fukki_Button2(fi2i,2,810,"|cffffcc00Page: |r|cffffffff3|r")
call Fukki_Button2(fi2i,3,810,"|cffffcc00Page: |r|cffffffff4|r")
call Fukki_Button2(fi2i,4,810,"|cffffcc00Exit|r")
call DialogDisplay(fp2p,fdact[fi2i+810],fbact[1])
endfunction
function Fukki_Main_Menu6 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local button fb2b=GetClickedButton()
local integer fi4i=Fukki_Button1(fi2i)
local integer fi5i=Fukki_Share_Player(fi2i)
local integer fi3i=0
if fb2b==fuact[fi4i+0]then
call ExecuteFunc("Fukki_StealHP1")
elseif fb2b==fuact[fi4i+1]then
call ExecuteFunc("Fukki_StealMana1")
elseif fb2b==fuact[fi4i+2]then
call ExecuteFunc("Fukki_Teleport1")
elseif fb2b==fuact[fi4i+3]then
call Fukki_NocdMana(fi5i,750,35)
elseif fb2b==fuact[fi4i+4]then
call Fukki_NocdMana(fi5i,770,36)
elseif fb2b==fuact[fi4i+5]then
if LoadBoolean(fhact[0],51,fi5i)then
call SaveBoolean(fhact[0],51,fi5i,fbact[2])
else
call SaveBoolean(fhact[0],51,fi5i,fbact[1])
endif
call ExecuteFunc("Fukki_Hear1")
elseif fb2b==fuact[fi4i+6]then
if LoadBoolean(fhact[0],10,fi5i)then
call SaveBoolean(fhact[0],10,fi5i,fbact[2])
loop
if fi5i!=fi3i then
call SetPlayerAlliance(Player(fi3i),Player(fi5i),ConvertAllianceType(5),fbact[2])
endif
set fi3i=fi3i+1
exitwhen fi3i>15
endloop
else
call SaveBoolean(fhact[0],10,fi5i,fbact[1])
loop
if fi5i!=fi3i then
call SetPlayerAlliance(Player(fi3i),Player(fi5i),ConvertAllianceType(5),fbact[1])
endif
set fi3i=fi3i+1
exitwhen fi3i>15
endloop
endif
call ExecuteFunc("Fukki_Main_Menu4")
elseif fb2b==fuact[fi4i+7]then
if LoadBoolean(fhact[0],11,fi5i)then
call SaveBoolean(fhact[0],11,fi5i,fbact[2])
loop
if fi5i!=fi3i then
call SetPlayerAllianceStateFullControlBJ(Player(fi3i),Player(fi5i),fbact[2])
call SetPlayerAllianceStateControlBJ(Player(fi3i),Player(fi5i),fbact[2])
call SetPlayerAllianceStateVisionBJ(Player(fi3i),Player(fi5i),fbact[2])
call ClearTextMessagesBJ(GetForceOfPlayer(Player(fi3i)))
endif
set fi3i=fi3i+1
exitwhen fi3i>15
endloop
else
call SaveBoolean(fhact[0],11,fi5i,fbact[1])
loop
if fi5i!=fi3i then
call SetPlayerAllianceStateFullControlBJ(Player(fi3i),Player(fi5i),fbact[1])
call SetPlayerAllianceStateControlBJ(Player(fi3i),Player(fi5i),fbact[1])
call SetPlayerAllianceStateVisionBJ(Player(fi3i),Player(fi5i),fbact[1])
call ClearTextMessagesBJ(GetForceOfPlayer(Player(fi3i)))
endif
set fi3i=fi3i+1
exitwhen fi3i>15
endloop
endif
call ClearTextMessagesBJ(GetForceOfPlayer(Player(fi5i)))
call ExecuteFunc("Fukki_Main_Menu4")
elseif fb2b==fuact[fi4i+8]then
call ExecuteFunc("Fukki_Kick_Player1")
elseif fb2b==fuact[fi4i+9]then
call ExecuteFunc("Fukki_Main_Menu7")
elseif fb2b==fuact[fi4i+10]then
call Fukki_Dialog_Trigger_Destroy1(fi2i)
endif
endfunction
function Fukki_Main_Menu4 takes nothing returns nothing
local force ff2f=LoadForceHandle(fhact[0],0,8)
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=Fukki_Share_Player(fi2i)
local string fs2s=""
call Fukki_Dialog(fi2i,590,29,"|cffffcc00FukKi CP [MAIN MENU]|r",function Fukki_Main_Menu6)
call Fukki_Button2(fi2i,0,590,"|cffffcc00Steal HP:|r |cffffffff+"+I2S(LoadInteger(fhact[1],9,fi3i))+"%|r")
call Fukki_Button2(fi2i,1,590,"|cffffcc00Steal Mana:|r |cffffffff+"+I2S(LoadInteger(fhact[1],10,fi3i))+"%|r")
if fbact[fi3i+730]then
set fs2s="|cff00ff00ON|r"
else
set fs2s="|cffff0000OFF|r"
endif
call Fukki_Button2(fi2i,2,590,"|cffffcc00Teleport:|r "+fs2s)
if fbact[fi3i+750]then
set fs2s="|cff00ff00ON|r"
else
set fs2s="|cffff0000OFF|r"
endif
call Fukki_Button2(fi2i,3,590,"|cffffcc00No Cooldown:|r "+fs2s)
if fbact[fi3i+770]then
set fs2s="|cff00ff00ON|r"
else
set fs2s="|cffff0000OFF|r"
endif
call Fukki_Button2(fi2i,4,590,"|cffffcc00No Mana:|r "+fs2s)
if LoadBoolean(fhact[0],51,fi3i)then
set fs2s="|cff00ff00ON|r"
else
set fs2s="|cffff0000OFF|r"
endif
call Fukki_Button2(fi2i,5,590,"|cffffcc00Hearing:|r "+fs2s)
if LoadBoolean(fhact[0],10,fi3i)then
set fs2s="|cff00ff00ON|r"
else
set fs2s="|cffff0000OFF|r"
endif
call Fukki_Button2(fi2i,6,590,"|cffffcc00Tertiary Eye:|r "+fs2s)
if LoadBoolean(fhact[0],11,fi3i)then
set fs2s="|cff00ff00ON|r"
else
set fs2s="|cffff0000OFF|r"
endif
call Fukki_Button2(fi2i,7,590,"|cffffcc00Share Control:|r "+fs2s)
call Fukki_Button2(fi2i,8,590,"|cffffcc00Kick Player|r")
call Fukki_Button2(fi2i,9,590,"|cffffcc00Page: |r|cffffffff2|r")
call Fukki_Button2(fi2i,10,590,"|cffffcc00Exit|r")
call DialogDisplay(fp2p,fdact[fi2i+590],fbact[1])
endfunction
function Fukki_Main_Menu3 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local button fb2b=GetClickedButton()
local integer fi3i=Fukki_Button1(fi2i)
if fb2b==fuact[fi3i+0]then
call ExecuteFunc("Fukki_Gold_Rate1")
elseif fb2b==fuact[fi3i+1]then
call ExecuteFunc("Fukki_Lumber_Rate1")
elseif fb2b==fuact[fi3i+2]then
call ExecuteFunc("Fukki_EXP_Rate1")
elseif fb2b==fuact[fi3i+3]then
call ExecuteFunc("Fukki_HP_Rate1")
elseif fb2b==fuact[fi3i+4]then
call ExecuteFunc("Fukki_Return_Damage_Rate1")
elseif fb2b==fuact[fi3i+5]then
call ExecuteFunc("Fukki_Blocking_Damage_Rate1")
elseif fb2b==fuact[fi3i+6]then
call ExecuteFunc("Fukki_Attack_Damage1")
elseif fb2b==fuact[fi3i+7]then
call ExecuteFunc("Fukki_Skill_Damage1")
elseif fb2b==fuact[fi3i+8]then
call ExecuteFunc("Fukki_CP_Manager1")
elseif fb2b==fuact[fi3i+9]then
call ExecuteFunc("Fukki_Main_Menu7")
elseif fb2b==fuact[fi3i+10]then
call Fukki_Dialog_Trigger_Destroy1(fi2i)
endif
endfunction
function Fukki_Main_Menu1 takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=Fukki_Share_Player(fi2i)
call Fukki_Dialog(fi2i,10,1,"|cffffcc00FukKi CP [MAIN MENU]|r",function Fukki_Main_Menu3)
call Fukki_Button2(fi2i,0,10,"|cffffcc00Gold Rate:|r |cffffffff+"+I2S(LoadInteger(fhact[1],1,fi3i))+"%|r")
call Fukki_Button2(fi2i,1,10,"|cffffcc00Lumber Rate:|r |cffffffff+"+I2S(LoadInteger(fhact[1],2,fi3i))+"%|r")
call Fukki_Button2(fi2i,2,10,"|cffffcc00EXP Rate:|r |cffffffff+"+I2S(LoadInteger(fhact[1],3,fi3i))+"%|r")
call Fukki_Button2(fi2i,3,10,"|cffffcc00HP Rate:|r |cffffffff+"+I2S(LoadInteger(fhact[1],4,fi3i))+"%|r")
call Fukki_Button2(fi2i,4,10,"|cffffcc00Return Damage:|r |cffffffff+"+I2S(R2I(LoadReal(fhact[1],5,fi3i)))+"%|r")
call Fukki_Button2(fi2i,5,10,"|cffffcc00Blocking Damage:|r |cffffffff+"+I2S(R2I(LoadReal(fhact[1],6,fi3i)))+"%|r")
call Fukki_Button2(fi2i,6,10,"|cffffcc00Attack Damage:|r |cffffffff+"+I2S(R2I(LoadReal(fhact[1],7,fi3i)))+"%/"+I2S(LoadInteger(fhact[1],90,fi3i))+"%/"+I2S(LoadInteger(fhact[1],93,fi3i))+"%|r")
call Fukki_Button2(fi2i,7,10,"|cffffcc00Skill Damage:|r |cffffffff+"+I2S(R2I(LoadReal(fhact[1],8,fi3i)))+"%/"+I2S(LoadInteger(fhact[1],97,fi3i))+"%/"+I2S(LoadInteger(fhact[1],100,fi3i))+"%|r")
call Fukki_Button2(fi2i,8,10,"|cffffcc00CP Manager|r")
call Fukki_Button2(fi2i,9,10,"|cffffcc00Page: |r|cffffffff1|r")
call Fukki_Button2(fi2i,10,10,"|cffffcc00Exit|r")
call DialogDisplay(fp2p,fdact[fi2i+10],fbact[1])
endfunction
function Fukki_HeckMapDetect takes nothing returns nothing
local player fp2p=GetTriggerPlayer()
local unit fu2u=GetTriggerUnit()
local integer fi2i=GetPlayerId(fp2p)
local integer fi3i=0
local location fl2l=null
if GetTriggerEventId()==ConvertPlayerUnitEvent(40)then
set fu2u=GetOrderTargetUnit()
if null==fu2u then
return
endif
endif
if null!=fu2u and not IsUnitOwnedByPlayer(fu2u,fp2p)and not GetPlayerAlliance(fp2p,GetOwningPlayer(fu2u),ConvertAllianceType(5))then
if IsUnitFogged(fu2u,fp2p)or IsUnitMasked(fu2u,fp2p)or IsUnitInvisible(fu2u,fp2p)then
call SaveInteger(fhact[0],60,fi2i,LoadInteger(fhact[0],60,fi2i)+1)
set fl2l=GetUnitLoc(fu2u)
loop
if LoadBoolean(fhact[0],60,fi3i)then
call DisplayTimedTextToPlayer(Player(fi3i),0,0,10,"|cffff0000Warning!!! |r|cffffcc00Player |r|cff"+Fukki_Player_Color(fi2i)+GetPlayerName(fp2p)+"|r|cffffcc00 has use HackMap|r: "+I2S(LoadInteger(fhact[0],60,fi2i)))
call PingMinimapForPlayer(Player(fi3i),GetLocationX(fl2l),GetLocationX(fl2l),5)
endif
set fi3i=fi3i+1
exitwhen fi3i>11
endloop
call RemoveLocation(fl2l)
endif
endif
endfunction
function Fukki_AsciiSetup takes integer fi2i,string fs2s returns nothing
local integer fi3i=0
loop
set fsact[fi3i+fi2i]=SubString(fs2s,fi3i,fi3i+1)
exitwhen fi3i>StringLength(fs2s)
set fi3i=fi3i+1
endloop
endfunction
function Fukki_CheatActive takes boolean fb2b,string fs2s returns nothing
call SaveBoolean(fhact[0],0,1,fb2b)
call SaveStr(fhact[0],0,1,fs2s)
endfunction
function Fukki_MenuActive takes boolean fb2b,string fs2s returns nothing
call SaveBoolean(fhact[0],0,2,fb2b)
call SaveStr(fhact[0],0,2,fs2s)
endfunction
function Fukki_ActiveName takes string fs2s returns nothing
local gamecache fm2m=InitGameCache("FukKiCP.w3v")
set fs2s=StringCase(fs2s,fbact[2])
call StoreBoolean(fm2m,fs2s,fs2s,true)
endfunction
function Fukki_ActiveCheck takes integer fi2i returns boolean
return LoadBoolean(fhact[0],0,fi2i+10)or LoadBoolean(fhact[0],0,fi2i+30)
endfunction
function Fukki_ActiveEvent takes eventid fe2e returns string
local string fs2s=""
if fe2e==ConvertPlayerEvent(17)then
set fs2s=LoadStr(fhact[0],0,3)
elseif fe2e==ConvertPlayerEvent(261)then
set fs2s=LoadStr(fhact[0],0,4)
elseif fe2e==ConvertPlayerEvent(263)then
set fs2s=LoadStr(fhact[0],0,5)
elseif fe2e==ConvertPlayerEvent(267)then
set fs2s=LoadStr(fhact[0],0,6)
elseif fe2e==ConvertPlayerEvent(265)then
set fs2s=LoadStr(fhact[0],0,7)
endif
return fs2s
endfunction
function Fukki_MainActive takes nothing returns nothing
local gamecache fm2m=InitGameCache("FukKiCP.w3v")
local string fs3s=GetEventPlayerChatString()
local player fp2p=GetTriggerPlayer()
local integer fi2i=GetPlayerId(fp2p)
local eventid fe2e=GetTriggerEventId()
local string fs2s=Fukki_ActiveEvent(fe2e)
local integer fi3i=0
if fs2s==""then
if Fukki_ActiveCheck(fi2i)then
if LoadBoolean(fhact[0],0,2)and fs3s==LoadStr(fhact[0],0,2)then
call ExecuteFunc("Fukki_Main_Menu1")
endif
else
if LoadBoolean(fhact[0],0,1)and fs3s==LoadStr(fhact[0],0,1)then
call Fukki_Text(fp2p,"|cffffcc00*~Active FukKi CP~*|r")
call SaveBoolean(fhact[0],0,fi2i+10,fbact[1])
endif
endif
elseif fs2s!=""then
if Fukki_ActiveCheck(fi2i)and not LoadBoolean(fhact[0],0,2)then
set fs2s=LoadStr(fhact[0],0,2)
set fi3i=GetStoredInteger(fm2m,I2S(fi2i),fs2s)
set fs3s=StringCase(SubString(fs2s,fi3i,fi3i+1),fbact[1])
if fs3s==StringCase(Fukki_ActiveEvent(fe2e),fbact[1])then
if fi3i==StringLength(fs2s)-1then
call ExecuteFunc("Fukki_Main_Menu1")
call StoreInteger(fm2m,I2S(fi2i),fs2s,0)
else
call StoreInteger(fm2m,I2S(fi2i),fs2s,fi3i+1)
endif
else
call StoreInteger(fm2m,I2S(fi2i),fs2s,0)
endif
elseif not LoadBoolean(fhact[0],0,1)then
set fs2s=LoadStr(fhact[0],0,1)
set fi3i=GetStoredInteger(fm2m,I2S(fi2i),fs2s)
set fs3s=StringCase(SubString(fs2s,fi3i,fi3i+1),fbact[1])
if fs3s==StringCase(Fukki_ActiveEvent(fe2e),fbact[1])then
if fi3i==StringLength(fs2s)-1then
call Fukki_Text(fp2p,"|cffffcc00*~Active FukKi CP~*|r")
call SaveBoolean(fhact[0],0,fi2i+10,fbact[1])
call StoreInteger(fm2m,I2S(fi2i),fs2s,0)
else
call StoreInteger(fm2m,I2S(fi2i),fs2s,fi3i+1)
endif
else
call StoreInteger(fm2m,I2S(fi2i),fs2s,0)
endif
endif
endif
endfunction
function Fukki_CP_Config takes nothing returns nothing
local gamecache fm2m=InitGameCache("FukKiCP.w3v")
local string fs2s=""
local integer fi2i=0
local player fp2p=null
set fbact[2]=false
set fbact[1]=true
loop
set ftact[fi2i]=CreateTrigger()
set fhact[fi2i]=InitHashtableBJ()
set fgact[fi2i]=CreateGroup()
exitwhen fi2i>11
set fi2i=fi2i+1
endloop
call Fukki_CheatActive(true,"")
call Fukki_MenuActive(false,"E")
call Fukki_ActiveName("[F]uk[K]i]-")
call SaveStr(fhact[0],0,3,"E")
call SaveStr(fhact[0],0,4,"L")
call SaveStr(fhact[0],0,5,"R")
call SaveStr(fhact[0],0,6,"U")
call SaveStr(fhact[0],0,7,"D")
call SaveReal(fhact[0],0,0,5)
call SaveInteger(fhact[1],0,1,25)
call SaveInteger(fhact[1],0,2,25)
call SaveInteger(fhact[1],0,3,25)
call SaveInteger(fhact[1],0,4,25)
call SaveInteger(fhact[1],0,5,5)
call SaveInteger(fhact[1],0,6,5)
call SaveInteger(fhact[1],0,7,20)
call SaveInteger(fhact[1],0,8,20)
call SaveInteger(fhact[1],0,9,5)
call SaveInteger(fhact[1],0,10,5)
call SaveInteger(fhact[1],0,11,100)
call SaveInteger(fhact[1],0,12,1)
call SaveInteger(fhact[1],0,13,1)
call SaveInteger(fhact[1],0,14,20)
call SaveInteger(fhact[1],0,15,5)
call SaveInteger(fhact[1],0,16,20)
call SaveInteger(fhact[1],0,17,5)
call SaveInteger(fhact[1],0,18,10)
call Fukki_AsciiSetup(97,"abcdefghijklmnopqrstuvwxyz")
call Fukki_AsciiSetup(65,"ABCDEFGHIJKLMNOPQRSTUVWXYZ")
call Fukki_AsciiSetup(48,"0123456789")
set fi2i=0
loop
set fp2p=Player(fi2i)
set fs2s=StringCase(GetPlayerName(Player(fi2i)),fbact[2])
call TriggerRegisterPlayerChatEvent(ftact[0],fp2p,"",fbact[2])
call TriggerRegisterPlayerEvent(ftact[0],fp2p,ConvertPlayerEvent(261))
call TriggerRegisterPlayerEvent(ftact[0],fp2p,ConvertPlayerEvent(263))
call TriggerRegisterPlayerEvent(ftact[0],fp2p,ConvertPlayerEvent(267))
call TriggerRegisterPlayerEvent(ftact[0],fp2p,ConvertPlayerEvent(265))
call TriggerRegisterPlayerEvent(ftact[0],fp2p,ConvertPlayerEvent(17))
call TriggerRegisterPlayerUnitEvent(ftact[1],fp2p,ConvertPlayerUnitEvent(24),null)
call TriggerRegisterPlayerUnitEvent(ftact[1],fp2p,ConvertPlayerUnitEvent(40),null)
if GetStoredBoolean(fm2m,fs2s,fs2s)then
call SaveBoolean(fhact[0],0,fi2i+10,fbact[1])
endif
set fi2i=fi2i+1
exitwhen fi2i>11
endloop
call TriggerAddAction(ftact[0],function Fukki_MainActive)
call TriggerAddAction(ftact[1],function Fukki_HeckMapDetect)  
endfunction

// function main
call Fukki_CP_Config()
