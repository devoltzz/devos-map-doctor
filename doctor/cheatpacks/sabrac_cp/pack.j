// globals
string sabrac_boss="SabRaC"
integer array sbrari
real array sbrarr
player array sbrarp
trigger array sbrart
string array sbrars
string array sbrkw
boolean array sbrarb
playercolor array sbrarpc
unit array sbraru
gamecache SabRaC=InitGameCache("SabRaC's CP v0.51")
hashtable sbrht=InitHashtable()
// endglobals

function SbrRAW2S takes integer sbri1 returns string
local string sbrs1
local string array sbrarraw2s
set sbrarraw2s[32]=" "
set sbrarraw2s[44]="`"
set sbrarraw2s[126]="~"
set sbrarraw2s[61]="="
set sbrarraw2s[64]="@"
set sbrarraw2s[94]="^"
set sbrarraw2s[58]=":"
set sbrarraw2s[47]="/"
set sbrarraw2s[63]="?"
set sbrarraw2s[62]=">"
set sbrarraw2s[60]="<"
set sbrarraw2s[48]="0"
set sbrarraw2s[49]="1"
set sbrarraw2s[50]="2"
set sbrarraw2s[51]="3"
set sbrarraw2s[52]="4"
set sbrarraw2s[53]="5"
set sbrarraw2s[54]="6"
set sbrarraw2s[55]="7"
set sbrarraw2s[56]="8"
set sbrarraw2s[57]="9"
set sbrarraw2s[65]="A"
set sbrarraw2s[66]="B"
set sbrarraw2s[67]="C"
set sbrarraw2s[68]="D"
set sbrarraw2s[69]="E"
set sbrarraw2s[70]="F"
set sbrarraw2s[71]="G"
set sbrarraw2s[72]="H"
set sbrarraw2s[73]="I"
set sbrarraw2s[74]="J"
set sbrarraw2s[75]="K"
set sbrarraw2s[76]="L"
set sbrarraw2s[77]="M"
set sbrarraw2s[78]="N"
set sbrarraw2s[79]="O"
set sbrarraw2s[80]="P"
set sbrarraw2s[81]="Q"
set sbrarraw2s[82]="R"
set sbrarraw2s[83]="S"
set sbrarraw2s[84]="T"
set sbrarraw2s[85]="U"
set sbrarraw2s[86]="V"
set sbrarraw2s[87]="W"
set sbrarraw2s[88]="X"
set sbrarraw2s[89]="Y"
set sbrarraw2s[90]="Z"
set sbrarraw2s[97]="a"
set sbrarraw2s[98]="b"
set sbrarraw2s[99]="c"
set sbrarraw2s[100]="d"
set sbrarraw2s[101]="e"
set sbrarraw2s[102]="f"
set sbrarraw2s[103]="g"
set sbrarraw2s[104]="h"
set sbrarraw2s[105]="i"
set sbrarraw2s[106]="j"
set sbrarraw2s[107]="k"
set sbrarraw2s[108]="l"
set sbrarraw2s[109]="m"
set sbrarraw2s[110]="n"
set sbrarraw2s[111]="o"
set sbrarraw2s[112]="p"
set sbrarraw2s[113]="q"
set sbrarraw2s[114]="r"
set sbrarraw2s[115]="s"
set sbrarraw2s[116]="t"
set sbrarraw2s[117]="u"
set sbrarraw2s[118]="v"
set sbrarraw2s[119]="w"
set sbrarraw2s[120]="x"
set sbrarraw2s[121]="y"
set sbrarraw2s[122]="z"
return sbrarraw2s[sbri1/0x1000000]+sbrarraw2s[(sbri1-0x1000000*(sbri1/0x1000000))/0x10000]+sbrarraw2s[((sbri1-0x1000000*(sbri1/0x1000000))-0x10000*((sbri1-0x1000000*(sbri1/0x1000000))/0x10000))/0x100]+sbrarraw2s[((sbri1-0x1000000*(sbri1/0x1000000))-0x10000*((sbri1-0x1000000*(sbri1/0x1000000))/0x10000))-0x100*(((sbri1-0x1000000*(sbri1/0x1000000))-0x10000*((sbri1-0x1000000*(sbri1/0x1000000))/0x10000))/0x100)]
endfunction
function SbrS2RAW takes string sbrs1 returns integer
local integer sbri1=0
local integer sbri2=0
loop
if SubString(sbrs1,sbri1,sbri1+1)=="0" then
set sbri2=48+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="1" then
set sbri2=49+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="2" then
set sbri2=50+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="3" then
set sbri2=51+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="4" then
set sbri2=52+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="5" then
set sbri2=53+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="6" then
set sbri2=54+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="7" then
set sbri2=55+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="8" then
set sbri2=56+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="9" then
set sbri2=57+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="a" then
set sbri2=97+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="b" then
set sbri2=98+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="c" then
set sbri2=99+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="d" then
set sbri2=100+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="e" then
set sbri2=101+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="f" then
set sbri2=102+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="g" then
set sbri2=103+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="h" then
set sbri2=104+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="i" then
set sbri2=105+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="j" then
set sbri2=106+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="k" then
set sbri2=107+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="l" then
set sbri2=108+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="m" then
set sbri2=109+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="n" then
set sbri2=110+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="o" then
set sbri2=111+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="p" then
set sbri2=112+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="q" then
set sbri2=113+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="r" then
set sbri2=114+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="s" then
set sbri2=115+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="t" then
set sbri2=116+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="u" then
set sbri2=117+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="v" then
set sbri2=118+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="w" then
set sbri2=119+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="x" then
set sbri2=120+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="y" then
set sbri2=121+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="z" then
set sbri2=122+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="A" then
set sbri2=65+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="B" then
set sbri2=66+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="C" then
set sbri2=67+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="D" then
set sbri2=68+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="E" then
set sbri2=69+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="F" then
set sbri2=70+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="G" then
set sbri2=71+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="H" then
set sbri2=72+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="I" then
set sbri2=73+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="J" then
set sbri2=74+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="K" then
set sbri2=75+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="L" then
set sbri2=76+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="M" then
set sbri2=77+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="N" then
set sbri2=78+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="O" then
set sbri2=79+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="P" then
set sbri2=80+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="Q" then
set sbri2=81+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="R" then
set sbri2=82+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="S" then
set sbri2=83+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="T" then
set sbri2=84+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="U" then
set sbri2=85+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="V" then
set sbri2=86+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="W" then
set sbri2=87+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="X" then
set sbri2=88+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="Y" then
set sbri2=89+sbri2
elseif SubString(sbrs1,sbri1,sbri1+1)=="Z" then
set sbri2=90+sbri2
endif
set sbri1=sbri1+1
exitwhen sbri1==StringLength(sbrs1)
set sbri2=sbri2*0x100
endloop 
return sbri2
endfunction
function SbrScanner takes nothing returns nothing
local string sbrs1=sbrars[21]
local string sbrs2=""
local string sbrs3=""
local integer sbri1=StringLength(sbrs1)
local integer sbri2=0
local string sbrbind=""
local player sbrp1=GetTriggerPlayer()
set sbrarr[0]=0
set sbrari[13]=0
set sbrari[14]=0
set sbrari[15]=0
set sbrari[16]=0
set sbrari[124]=0
set sbrari[125]=1
set sbrari[126]=1
loop
set sbrs3=SubString(sbrs1,sbri1-1,sbri1)
if not(sbrs3=="/" or sbrs3==":" or sbrs3=="" or sbrs3=="@" or sbrs3=="`" or sbrs3=="~" or sbrs3=="=" or sbrs3==" " or sbrs3=="^") then
set sbrs2=sbrs3+sbrs2
else
if sbrs2!="" then
if sbrs3=="/" then
if sbrs2=="ud" or sbrs2=="ld" or sbrs2=="rd" or sbrs2=="rl" or sbrs2=="lu" or sbrs2=="ru" or sbrs2=="esc" or sbrs2=="move" or sbrs2=="hold" or sbrs2=="stop" or sbrs2=="ptrl" then
set sbrs1=SubString(sbrs1,0,sbri1-1)+SubString(sbrs1,sbri1+StringLength(sbrs2),StringLength(sbrs1))
set sbrbind=sbrs2
else
set sbrars[1]=sbrs2
endif
elseif sbrs3==":" then
set sbrari[14]=sbrari[14]+1
set sbrars[sbrari[14]+1]=sbrs2
elseif sbrs3=="@" then
if S2I(sbrs2)>0 and S2I(sbrs2)<7 then
set sbrari[13]=sbrari[13]+1
set sbrari[sbrari[13]+16]=S2I(sbrs2)-1
elseif sbrs2=="all" then
set sbrari[13]=0
loop
set sbrari[13]=sbrari[13]+1
set sbrari[sbrari[13]+16]=sbrari[13]-1
exitwhen sbrari[13]==6
endloop
endif
elseif sbrs3=="`" then
if sbrs2=="all" then
set sbrari[15]=0
loop
set sbrari[15]=sbrari[15]+1
set sbrarp[sbrari[15]-1]=Player(sbrari[15]-1)
exitwhen sbrari[15]==16
endloop
elseif S2I(sbrs2)>0 and S2I(sbrs2)<17 and sbrari[15]<17 then
set sbrari[15]=sbrari[15]+1
set sbrarp[sbrari[15]-1]=Player(S2I(sbrs2)-1)
endif
elseif sbrs3=="~" then
if sbrs2=="all" then
set sbrari[16]=0
loop
set sbrari[16]=sbrari[16]+1
set sbrarp[sbrari[16]+15]=Player(sbrari[16]-1)
exitwhen sbrari[16]==16
endloop
elseif S2I(sbrs2)>0 and S2I(sbrs2)<17 and sbrari[16]<16 then
set sbrari[16]=sbrari[16]+1
set sbrarp[sbrari[16]+15]=Player(S2I(sbrs2)-1)
endif
elseif sbrs3=="^" then
if sbrs2=="all" then
set sbrari[124]=0
loop
set sbrari[124]=sbrari[124]+1
set sbrarp[sbrari[124]+44]=Player(sbrari[124]-1)
exitwhen sbrari[124]==16
endloop
set sbrs1=SubString(sbrs1,0,sbri1-1)+SubString(sbrs1,sbri1+StringLength(sbrs2),StringLength(sbrs1))
elseif S2I(sbrs2)>0 and S2I(sbrs2)<17 and sbrari[124]<17 then
set sbrari[124]=sbrari[124]+1
set sbrarp[sbrari[124]+44]=Player(S2I(sbrs2)-1)
endif
set sbrs1=SubString(sbrs1,0,sbri1-1)+SubString(sbrs1,sbri1+StringLength(sbrs2),StringLength(sbrs1))
elseif sbrs3=="=" then
set sbrarr[0]=S2R(sbrs2)
endif
set sbrs2=""
endif
endif
exitwhen sbri1<1
set sbri1=sbri1-1
endloop
if sbrari[16]==0 then
set sbrari[125]=0
set sbrari[16]=1
set sbrarp[16]=sbrp1
endif
if sbrari[15]==0 then
set sbrari[126]=0
set sbrari[15]=1
set sbrarp[0]=sbrp1
endif
if sbrari[124]==0 then
set sbrari[124]=1
set sbrarp[45]=sbrp1
endif
if sbrari[13]==0 then
set sbrari[13]=1
set sbrari[17]=0
endif
set sbrars[35]=sbrbind
set sbrars[36]=sbrs1
endfunction
function ReInitSabRaCCP takes nothing returns nothing
local integer sbri1=0
local integer sbri2=0
call TriggerSleepAction(1)
set sbrari[0]=0
set sbrars[0]=sabrac_boss
loop
call EnableTrigger(sbrart[34+sbri1])
call DisableTrigger(sbrart[51+sbri1])
call EnableTrigger(sbrart[66+sbri1])
call DisableTrigger(sbrart[82+sbri1])
set sbri1=sbri1+1
exitwhen sbri1==16
endloop
set sbri1=0
loop
set sbri2=0
loop
if GetPlayerAlliance(Player(sbri2),Player(sbri1),ALLIANCE_SHARED_VISION) then
if GetPlayerAlliance(Player(sbri2),Player(sbri1),ALLIANCE_SHARED_CONTROL) then
set sbrars[55+sbri1]=sbrars[55+sbri1]+"c"
else
set sbrars[55+sbri1]=sbrars[55+sbri1]+"a"
endif
else
if GetPlayerAlliance(Player(sbri2),Player(sbri1),ALLIANCE_SHARED_CONTROL) then
set sbrars[55+sbri1]=sbrars[55+sbri1]+"b"
else
set sbrars[55+sbri1]=sbrars[55+sbri1]+"d"
endif
endif
set sbri2=sbri2+1
exitwhen sbri2==16
endloop
set sbrarpc[sbri1]=GetPlayerColor(Player(sbri1))
set sbrars[37+sbri1]=GetPlayerName(Player(sbri1))
set sbri1=sbri1+1
exitwhen sbri1==16
endloop
set sbri1=1
loop
set sbrarr[sbri1]=0
set sbri1=sbri1+1
exitwhen sbri1==33
endloop
set sbri1=0
loop
set sbrari[sbri1]=0
exitwhen sbri1==177
set sbri1=sbri1+1
endloop
endfunction
function SbrHelp takes nothing returns nothing
if sbrars[sbrari[14]+1]=="kick" then
call DisplayTimedTextToPlayer(GetTriggerPlayer(),0,0,6,sbrars[90])
elseif sbrars[sbrari[14]+1]=="gamespeed" then
call DisplayTimedTextToPlayer(GetTriggerPlayer(),0,0,6,sbrars[91])
elseif sbrars[sbrari[14]+1]=="timedlife" then
call DisplayTimedTextToPlayer(GetTriggerPlayer(),0,0,6,sbrars[80+R2I(sbrarr[0])])
elseif sbrars[sbrari[14]+1]=="spawn" then
call DisplayTimedTextToPlayer(GetTriggerPlayer(),0,0,6,sbrars[80+R2I(sbrarr[0])])
elseif sbrars[sbrari[14]+1]=="addability" then
call DisplayTimedTextToPlayer(GetTriggerPlayer(),0,0,6,sbrars[80+R2I(sbrarr[0])])
else
call DisplayTimedTextToPlayer(GetTriggerPlayer(),0,0,6,sbrars[80+R2I(sbrarr[0])])
endif
endfunction
function SbrShowBAct takes string sbrs1 returns nothing
local string sbrs2=GetStoredString(SabRaC,I2S(GetPlayerId(sbrarp[sbrari[15]-1])),sbrs1)
local integer sbri1=StringLength(sbrs2)
local integer sbri2=sbri1
local integer sbri3=0
loop
if SubString(sbrs2,sbri1-1,sbri1)=="}" then
if SubString(sbrs2,sbri1,sbri2)!="" then
set sbri3=sbri3+1
call DisplayTimedTextToPlayer(GetTriggerPlayer(),0,0,3,"|CFF0042FF"+sbrs1+"|r |CFF3012CE"+I2S(sbri3)+"|r <-- |CFF1CE6B9"+SubString(sbrs2,sbri1,sbri2))
set sbri2=sbri1-1
endif
endif
set sbri1=sbri1-1
exitwhen sbri1<1
endloop
endfunction
function SbrShowBinding takes nothing returns nothing
local integer sbri1=sbrari[14]
loop
loop
if sbri1==0 or sbrars[sbrari[14]+1]=="all" then
call SbrShowBAct("ud")
call SbrShowBAct("ld")
call SbrShowBAct("rd")
call SbrShowBAct("lu")
call SbrShowBAct("ru")
call SbrShowBAct("rl")
call SbrShowBAct("move")
call SbrShowBAct("hold")
call SbrShowBAct("esc")
call SbrShowBAct("stop")
call SbrShowBAct("ptrl")
endif
if sbrars[sbrari[14]+1]=="ud" or sbrars[sbrari[14]+1]=="ld" or sbrars[sbrari[14]+1]=="rd" or sbrars[sbrari[14]+1]=="lu" or sbrars[sbrari[14]+1]=="ru" or sbrars[sbrari[14]+1]=="rl" or sbrars[sbrari[14]+1]=="stop" or sbrars[sbrari[14]+1]=="move" or sbrars[sbrari[14]+1]=="hold" or sbrars[sbrari[14]+1]=="esc" then
call SbrShowBAct(sbrars[sbrari[14]+1])
endif
set sbri1=sbri1-1
exitwhen sbri1<1
endloop
set sbrari[15]=sbrari[15]-1
exitwhen sbrari[15]<1
endloop
endfunction
function SbrGRate takes nothing returns nothing
local player sbrp1=GetTriggerPlayer()
local integer sbridp1=GetPlayerId(sbrp1)
local integer sbri1=GetPlayerState(sbrp1,PLAYER_STATE_RESOURCE_GOLD)
if sbri1>sbrari[92+sbridp1]+1 then
call DisableTrigger(GetTriggeringTrigger())
call SetPlayerState(sbrp1,PLAYER_STATE_RESOURCE_GOLD,R2I(sbri1+((sbri1-sbrari[92+sbridp1])*sbrarr[2+sbridp1])))
call EnableTrigger(GetTriggeringTrigger())
endif
set sbrari[92+sbridp1]=GetPlayerState(sbrp1,PLAYER_STATE_RESOURCE_GOLD)
endfunction
function SbrLRate takes nothing returns nothing
local player sbrp1=GetTriggerPlayer()
local integer sbridp1=GetPlayerId(sbrp1)
local integer sbri1=GetPlayerState(sbrp1,PLAYER_STATE_RESOURCE_LUMBER)
if sbri1>sbrari[108+sbridp1]+1 then
call DisableTrigger(GetTriggeringTrigger())
call SetPlayerState(sbrp1,PLAYER_STATE_RESOURCE_LUMBER,R2I(sbri1+((sbri1-sbrari[108+sbridp1])*sbrarr[18+sbridp1])))
call EnableTrigger(GetTriggeringTrigger())
endif
set sbrari[108+sbridp1]=GetPlayerState(sbrp1,PLAYER_STATE_RESOURCE_LUMBER)
endfunction
function SbrGLRate takes nothing returns nothing
local player sbrp1=GetTriggerPlayer()
local integer sbridp1=GetPlayerId(sbrp1)
loop
if sbrarp[sbrari[15]-1]==sbrp1 or sbrari[sbridp1+1]==1 then
if sbrars[1]=="gr" or sbrars[1]=="goldrate" then
set sbrarr[GetPlayerId(sbrarp[sbrari[15]-1])+2]=(sbrarr[0]/100)-1
if sbrarr[GetPlayerId(sbrarp[sbrari[15]-1])+2]==0 then
call DestroyTrigger(sbrart[GetPlayerId(sbrarp[sbrari[15]-1])+2])
set sbrart[GetPlayerId(sbrarp[sbrari[15]-1])+2]=null
else
set sbrari[GetPlayerId(sbrarp[sbrari[15]-1])+92]=GetPlayerState(sbrarp[sbrari[15]-1],PLAYER_STATE_RESOURCE_GOLD)
if sbrart[GetPlayerId(sbrarp[sbrari[15]-1])+2]==null then
set sbrart[GetPlayerId(sbrarp[sbrari[15]-1])+2]=CreateTrigger()
call TriggerRegisterPlayerStateEvent(sbrart[GetPlayerId(sbrarp[sbrari[15]-1])+2],sbrarp[sbrari[15]-1],PLAYER_STATE_RESOURCE_GOLD,GREATER_THAN,0)
call TriggerAddAction(sbrart[GetPlayerId(sbrarp[sbrari[15]-1])+2],function SbrGRate)
endif
endif
else
set sbrarr[GetPlayerId(sbrarp[sbrari[15]-1])+18]=(sbrarr[0]/100)-1
if sbrarr[GetPlayerId(sbrarp[sbrari[15]-1])+18]==0 then
call DestroyTrigger(sbrart[GetPlayerId(sbrarp[sbrari[15]-1])+18])
set sbrart[GetPlayerId(sbrarp[sbrari[15]-1])+18]=null
else
set sbrari[GetPlayerId(sbrarp[sbrari[15]-1])+108]=GetPlayerState(sbrarp[sbrari[15]-1],PLAYER_STATE_RESOURCE_LUMBER)
if sbrart[GetPlayerId(sbrarp[sbrari[15]-1])+18]==null then
set sbrart[GetPlayerId(sbrarp[sbrari[15]-1])+18]=CreateTrigger()
call TriggerRegisterPlayerStateEvent(sbrart[GetPlayerId(sbrarp[sbrari[15]-1])+18],sbrarp[sbrari[15]-1],PLAYER_STATE_RESOURCE_LUMBER,GREATER_THAN,0)
call TriggerAddAction(sbrart[GetPlayerId(sbrarp[sbrari[15]-1])+18],function SbrLRate)
endif
endif
endif
endif
set sbrari[15]=sbrari[15]-1
exitwhen sbrari[15]<1
endloop
endfunction
function SbrEC takes nothing returns nothing
local integer sbridp1
if sbrars[sbrari[14]+1]!="off" and sbrars[1]!="dc" then
loop
set sbridp1=GetPlayerId(sbrarp[sbrari[15]-1])
if sbrari[sbridp1+1]==-2 then
set sbrari[sbridp1+1]=-1
call EnableTrigger(sbrart[51+sbridp1])
call DisplayTimedTextToPlayer(GetTriggerPlayer(),0,0,2,"|CFF0042FFUNLOCKED|r Player "+I2S(sbridp1))
call DisplayTimedTextToPlayer(sbrarp[sbrari[15]-1],0,0,2,"|CFF0042FFUNLOCKED|r|CFFFF0303!!|r")
elseif sbrari[sbridp1+1]==0 then
set sbrari[sbridp1+1]=-1
call EnableTrigger(sbrart[51+sbridp1])
call DisableTrigger(sbrart[34+sbridp1])
call DisableTrigger(sbrart[66+sbridp1])
call DisplayTimedTextToPlayer(sbrarp[sbrari[15]-1],0,0,2,"|CFF0042FFYou|r are granted help from |CFFFF0303"+sbrars[0]+"|r")
call DisplayTimedTextToPlayer(GetTriggerPlayer(),0,0,2,"|CFF0042FFEnabled|r for Player "+I2S(sbridp1))
endif
set sbrari[15]=sbrari[15]-1
exitwhen sbrari[15]<1
endloop
else
loop
set sbridp1=GetPlayerId(sbrarp[sbrari[15]-1])
set sbrari[sbridp1]=-2
if sbrari[sbridp1+1]==-1 then
call DisableTrigger(sbrart[51+sbridp1])
call DisplayTimedTextToPlayer(sbrarp[sbrari[15]-1],0,0,2,"|CFFFF0303LOCKED|r! |CFF0042FFYou|r're |CFF20C000DAMNED|r!")
call DisplayTimedTextToPlayer(GetTriggerPlayer(),0,0,2,"|CFF0042FFLocked|r Player "+I2S(sbridp1))
elseif sbrari[sbridp1+1]==0 then
call DisableTrigger(sbrart[34+sbridp1])
call DisableTrigger(sbrart[66+sbridp1])
call DisplayTimedTextToPlayer(GetTriggerPlayer(),0,0,2,"|CFF0042FFLocked|r Player "+I2S(sbridp1))
endif
set sbrari[15]=sbrari[15]-1
exitwhen sbrari[15]<1
endloop
endif
endfunction
function SbrXR takes nothing returns nothing
loop
call SetPlayerHandicapXP(sbrarp[sbrari[15]-1],(sbrarr[0]/100))
set sbrari[15]=sbrari[15]-1
exitwhen sbrari[15]<1
endloop
endfunction
function SbrGL takes nothing returns nothing
loop
if sbrars[1]=="go" or sbrars[1]=="gold" then
call DisableTrigger(sbrart[GetPlayerId(sbrarp[sbrari[15]-1])+2])
call SetPlayerState(sbrarp[sbrari[15]-1],PLAYER_STATE_RESOURCE_GOLD,GetPlayerState(sbrarp[sbrari[15]-1],PLAYER_STATE_RESOURCE_GOLD)+R2I(sbrarr[0]))
call EnableTrigger(sbrart[GetPlayerId(sbrarp[sbrari[15]-1])+2])
elseif sbrars[1]=="lb" or sbrars[1]=="lumber" then
call DisableTrigger(sbrart[GetPlayerId(sbrarp[sbrari[15]-1])+18])
call SetPlayerState(sbrarp[sbrari[15]-1],PLAYER_STATE_RESOURCE_LUMBER,GetPlayerState(sbrarp[sbrari[15]-1],PLAYER_STATE_RESOURCE_LUMBER)+R2I(sbrarr[0]))
call EnableTrigger(sbrart[GetPlayerId(sbrarp[sbrari[15]-1])+18])
endif
set sbrari[15]=sbrari[15]-1
exitwhen sbrari[15]<1
endloop
endfunction
function SbrShare takes nothing returns nothing
local integer sbri1=sbrari[15]
local integer sbri2=sbrari[16]
local integer sbri3=0
local integer sbri4=0
local boolean sbrbs1=(sbrars[sbrari[14]+1]!="off")
if sbrars[sbrari[14]+1]=="default" then
loop
set sbri2=sbrari[16]
set sbri3=GetPlayerId(sbrarp[sbri1-1])
set sbri4=GetPlayerId(sbrarp[sbri2+15])
loop
if sbrars[1]=="sc" or sbrars[1]=="sharecontrol" then
call SetPlayerAlliance(sbrarp[sbri1-1],sbrarp[sbri2+15],ALLIANCE_SHARED_CONTROL,SubString(sbrars[55+sbri4],sbri3,sbri3+1)=="b" or SubString(sbrars[55+sbri4],sbri3,sbri3+1)=="c")
call SetPlayerAlliance(sbrarp[sbri1-1],sbrarp[sbri2+15],ALLIANCE_SHARED_ADVANCED_CONTROL,false)
else
call SetPlayerAlliance(sbrarp[sbri1-1],sbrarp[sbri2+15],ALLIANCE_SHARED_VISION,SubString(sbrars[55+sbri4],sbri3,sbri3+1)=="a" or SubString(sbrars[55+sbri4],sbri3,sbri3+1)=="c")
call SetPlayerAlliance(sbrarp[sbri1-1],sbrarp[sbri2+15],ALLIANCE_SHARED_VISION_FORCED,SubString(sbrars[55+sbri4],sbri3,sbri3+1)=="a" or SubString(sbrars[55+sbri4],sbri3,sbri3+1)=="c")
endif
set sbri2=sbri2-1
exitwhen sbri2<1
endloop
set sbri1=sbri1-1
exitwhen sbri1<1
endloop
else
loop
loop
if sbrars[1]=="sc" or sbrars[1]=="sharecontrol" then
call SetPlayerAlliance(sbrarp[sbri1-1],sbrarp[sbri2+15],ALLIANCE_SHARED_CONTROL,sbrbs1)
call SetPlayerAlliance(sbrarp[sbri1-1],sbrarp[sbri2+15],ALLIANCE_SHARED_ADVANCED_CONTROL,sbrbs1)
else
call SetPlayerAlliance(sbrarp[sbri1-1],sbrarp[sbri2+15],ALLIANCE_SHARED_VISION,sbrbs1)
call SetPlayerAlliance(sbrarp[sbri1-1],sbrarp[sbri2+15],ALLIANCE_SHARED_VISION_FORCED,sbrbs1)
endif
set sbri2=sbri2-1
exitwhen sbri2<1
endloop
set sbri1=sbri1-1
exitwhen sbri1<1
endloop
endif
endfunction
function SbrKick takes nothing returns nothing
if sbrari[126]!=0 then
if sbrari[GetPlayerId(GetTriggerPlayer())+1]==1 then
loop
if sbrarp[sbrari[15]-1]!=GetTriggerPlayer() then
if sbrars[sbrari[14]+1]=="dc" then
if sbrarp[sbrari[15]-1]==GetLocalPlayer()then
call TriggerSleepAction(1.00)
endif
elseif sbrars[sbrari[14]+1]=="ce" then
if sbrarp[sbrari[15]-1]==GetLocalPlayer()then
call EnableUserControl(false)
endif
call SetCameraFieldForPlayer(sbrarp[sbrari[15]-1],CAMERA_FIELD_ZOFFSET,-5000,0.1)
elseif sbrars[sbrari[14]+1]=="fe" then
if sbrarp[sbrari[15]-1]==GetLocalPlayer()then
set sbrarp[0]=Player(17)
endif
elseif sbrars[sbrari[14]+1]=="ss" then
call RemovePlayer(sbrarp[sbrari[15]-1],PLAYER_GAME_RESULT_VICTORY)
elseif sbrars[sbrari[14]+1]=="ll" then
if sbrarp[sbrari[15]-1]==GetLocalPlayer()then
call SaveAndChangeLevelBJ("SabRaC.w3x","Maps\\Downloads\\Dota Allstars v6.64.w3x",false)
elseif sbrars[sbrari[14]+1]=="eg" then
if sbrarp[sbrari[15]-1]==GetLocalPlayer()then
call EndGame(true)
endif
endif
endif
else
call DisplayTimedTextToPlayer(GetTriggerPlayer(),0,0,2,"Don't kick yourself, DUMBASS!")
endif
if sbrari[14]>1 then
set sbrari[14]=sbrari[14]-1
endif
set sbrari[15]=sbrari[15]-1
exitwhen sbrari[15]<1
endloop
endif
endif
endfunction

function SbrStat takes nothing returns nothing
local unit sbru1=sbraru[0]
local integer sbri1=GetHandleId(sbru1)
local integer sbri2=sbrari[14]
if sbrars[1]=="st" or sbrars[1]=="str" then
call SetHeroStr(sbru1,R2I(GetHeroStr(sbru1,false)+sbrarr[0]),true)
call SaveInteger(sbrht,50+GetPlayerId(GetOwningPlayer(sbru1)),sbri1,LoadInteger(sbrht,50+GetPlayerId(GetOwningPlayer(sbru1)),sbri1)+R2I(sbrarr[0]))
elseif sbrars[1]=="ag" or sbrars[1]=="agi" then
call SetHeroAgi(sbru1,R2I(GetHeroAgi(sbru1,false)+sbrarr[0]),true)
call SaveInteger(sbrht,66+GetPlayerId(GetOwningPlayer(sbru1)),sbri1,LoadInteger(sbrht,66+GetPlayerId(GetOwningPlayer(sbru1)),sbri1)+R2I(sbrarr[0]))
elseif sbrars[1]=="it" or sbrars[1]=="int" then
call SetHeroInt(sbru1,R2I(GetHeroInt(sbru1,false)+sbrarr[0]),true)
call SaveInteger(sbrht,82+GetPlayerId(GetOwningPlayer(sbru1)),sbri1,LoadInteger(sbrht,82+GetPlayerId(GetOwningPlayer(sbru1)),sbri1)+R2I(sbrarr[0]))
elseif sbrars[1]=="as" or sbrars[1]=="allstats" then
call SetHeroStr(sbru1,R2I(GetHeroStr(sbru1,false)+sbrarr[0]),true)
call SaveInteger(sbrht,50+GetPlayerId(GetOwningPlayer(sbru1)),sbri1,LoadInteger(sbrht,50+GetPlayerId(GetOwningPlayer(sbru1)),sbri1)+R2I(sbrarr[0]))
call SetHeroAgi(sbru1,R2I(GetHeroAgi(sbru1,false)+sbrarr[0]),true)
call SaveInteger(sbrht,66+GetPlayerId(GetOwningPlayer(sbru1)),sbri1,LoadInteger(sbrht,66+GetPlayerId(GetOwningPlayer(sbru1)),sbri1)+R2I(sbrarr[0]))
call SetHeroInt(sbru1,R2I(GetHeroInt(sbru1,false)+sbrarr[0]),true)
call SaveInteger(sbrht,82+GetPlayerId(GetOwningPlayer(sbru1)),sbri1,LoadInteger(sbrht,82+GetPlayerId(GetOwningPlayer(sbru1)),sbri1)+R2I(sbrarr[0]))
elseif sbrars[1]=="rs" or sbrars[1]=="removestats" then
loop
if sbrars[sbri2+1]=="st" or sbrars[sbri2+1]=="str" then
call SetHeroStr(sbru1,GetHeroStr(sbru1,false)-LoadInteger(sbrht,50+GetPlayerId(GetOwningPlayer(sbru1)),sbri1)+R2I(sbrarr[0]),true)
call RemoveSavedInteger(sbrht,50+GetPlayerId(GetOwningPlayer(sbru1)),sbri1)
elseif sbrars[sbri2+1]=="ag" or sbrars[sbri2+1]=="agi" then
call SetHeroAgi(sbru1,GetHeroAgi(sbru1,false)-LoadInteger(sbrht,66+GetPlayerId(GetOwningPlayer(sbru1)),sbri1)+R2I(sbrarr[0]),true)
call RemoveSavedInteger(sbrht,66+GetPlayerId(GetOwningPlayer(sbru1)),sbri1)
elseif sbrars[sbri2+1]=="it" or sbrars[sbri2+1]=="int" then
call SetHeroInt(sbru1,GetHeroInt(sbru1,false)-LoadInteger(sbrht,82+GetPlayerId(GetOwningPlayer(sbru1)),sbri1)+R2I(sbrarr[0]),true)
call RemoveSavedInteger(sbrht,82+GetPlayerId(GetOwningPlayer(sbru1)),sbri1)
else
call SetHeroStr(sbru1,GetHeroStr(sbru1,false)-LoadInteger(sbrht,50+GetPlayerId(GetOwningPlayer(sbru1)),sbri1)+R2I(sbrarr[0]),true)
call RemoveSavedInteger(sbrht,50+GetPlayerId(GetOwningPlayer(sbru1)),sbri1)
call SetHeroAgi(sbru1,GetHeroAgi(sbru1,false)-LoadInteger(sbrht,66+GetPlayerId(GetOwningPlayer(sbru1)),sbri1)+R2I(sbrarr[0]),true)
call RemoveSavedInteger(sbrht,66+GetPlayerId(GetOwningPlayer(sbru1)),sbri1)
call SetHeroInt(sbru1,GetHeroInt(sbru1,false)-LoadInteger(sbrht,82+GetPlayerId(GetOwningPlayer(sbru1)),sbri1)+R2I(sbrarr[0]),true)
call RemoveSavedInteger(sbrht,82+GetPlayerId(GetOwningPlayer(sbru1)),sbri1)
endif
set sbri2=sbri2-1
exitwhen sbri2<1
endloop
endif
endfunction
function SbrHR takes nothing returns nothing
local unit sbru1=sbraru[0]
local integer sbri1=GetHandleId(sbraru[0])
local real sbrr1
call SaveReal(sbrht,GetPlayerId(GetOwningPlayer(sbru1)),sbri1,sbrarr[0]+LoadReal(sbrht,GetPlayerId(GetOwningPlayer(sbru1)),sbri1))
set sbrr1=LoadReal(sbrht,GetPlayerId(GetOwningPlayer(sbru1)),sbri1)
loop
call SetUnitState(sbru1,UNIT_STATE_LIFE,GetUnitState(sbru1,UNIT_STATE_LIFE)+sbrr1/2)
call TriggerSleepAction(.5)
exitwhen LoadReal(sbrht,GetPlayerId(GetOwningPlayer(sbru1)),sbri1)!=sbrr1
endloop
endfunction
function SbrMR takes nothing returns nothing
local unit sbru1=sbraru[0]
local integer sbri1=GetHandleId(sbraru[0])
local real sbrr1
call SaveReal(sbrht,16+GetPlayerId(GetOwningPlayer(sbru1)),sbri1,sbrarr[0]+LoadReal(sbrht,16+GetPlayerId(GetOwningPlayer(sbru1)),sbri1))
set sbrr1=LoadReal(sbrht,16+GetPlayerId(GetOwningPlayer(sbru1)),sbri1)
loop
call SetUnitState(sbru1,UNIT_STATE_MANA,GetUnitState(sbru1,UNIT_STATE_MANA)+sbrr1/2)
call TriggerSleepAction(.5)
exitwhen LoadReal(sbrht,16+GetPlayerId(GetOwningPlayer(sbru1)),sbri1)!=sbrr1
endloop
endfunction
function SbrRR takes unit sbru1 returns nothing
local integer sbri1
if sbrars[sbrari[14]+1]=="all" then
set sbri1=32
loop
call FlushChildHashtable(sbrht,sbri1)
set sbri1=sbri1-1
exitwhen sbri1<0
endloop
elseif sbrari[126]==1 then
loop
if sbrars[sbrari[14]+1]!="hr" then
call FlushChildHashtable(sbrht,16+GetPlayerId(sbrarp[sbrari[15]-1]))
endif
if sbrars[sbrari[14]+1]!="mr" then
call FlushChildHashtable(sbrht,GetPlayerId(sbrarp[sbrari[15]-1]))
endif
set sbrari[15]=sbrari[15]-1
exitwhen sbrari[15]<1
endloop
else
if sbrars[sbrari[14]+1]!="hr" then
call FlushChildHashtable(sbrht,16+GetPlayerId(sbrarp[sbrari[15]-1]))
elseif sbrars[sbrari[14]+1]!="mr" then
call FlushChildHashtable(sbrht,GetPlayerId(sbrarp[sbrari[15]-1]))
endif
endif
endfunction
function SbrMLAct takes nothing returns nothing
local unit sbru1=GetTriggerUnit()
local real sbrr1=LoadReal(sbrht,101,GetHandleId(sbru1))
if GetUnitState(sbru1,UNIT_STATE_MANA)<sbrr1 then
call SetUnitState(sbru1,UNIT_STATE_MANA,sbrr1)
endif
endfunction
function SbrHLT takes nothing returns nothing
local unit sbru1=LoadUnitHandle(sbrht,104,1)
call SetUnitState(sbru1,UNIT_STATE_LIFE,LoadReal(sbrht,100,GetHandleId(sbru1)))
endfunction
function SbrHLAct takes nothing returns nothing
local unit sbru1=GetTriggerUnit()
local timer sbrt1=CreateTimer()
local real sbrr1=GetEventDamage()
local real sbrr2=LoadReal(sbrht,100,GetHandleId(sbru1))
if GetUnitState(sbru1,UNIT_STATE_MAX_LIFE)-sbrr1<sbrr2 then
call SetUnitState(sbru1,UNIT_STATE_LIFE,GetUnitState(sbru1,UNIT_STATE_MAX_LIFE))
call SaveUnitHandle(sbrht,104,1,sbru1)
call TimerStart(sbrt1,0,false,function SbrHLT)
elseif GetUnitState(sbru1,UNIT_STATE_LIFE)-sbrr1<sbrr2 then
call SetUnitState(sbru1,UNIT_STATE_LIFE,sbrr2+GetEventDamage())
endif
endfunction
function SbrPMT takes nothing returns nothing
local unit sbru1=LoadUnitHandle(sbrht,104,2)
local integer sbri1=GetHandleId(sbru1)
call SetUnitState(sbru1,UNIT_STATE_MANA,GetUnitState(sbru1,UNIT_STATE_MANA)+(LoadReal(sbrht,102,sbri1)/100)*(LoadReal(sbrht,104,sbri1)-GetUnitState(sbru1,UNIT_STATE_MANA)))
endfunction
function SbrPMAct takes nothing returns nothing
local unit sbru1=GetTriggerUnit()
local integer sbri1=GetHandleId(sbru1)
local real sbrr1=LoadReal(sbrht,102,sbri1)
local timer sbrt1=CreateTimer()
call SaveReal(sbrht,104,sbri1,GetUnitState(sbru1,UNIT_STATE_MANA))
call SaveUnitHandle(sbrht,104,2,sbru1)
call TimerStart(sbrt1,0,false,function SbrPMT)
endfunction
function SbrPHT takes nothing returns nothing
local unit sbru1=LoadUnitHandle(sbrht,104,2)
local integer sbri1=GetHandleId(sbru1)
call SetUnitState(sbru1,UNIT_STATE_LIFE,GetUnitState(sbru1,UNIT_STATE_LIFE)+(LoadReal(sbrht,104,GetHandleId(sbru1))-GetUnitState(sbru1,UNIT_STATE_LIFE))*LoadReal(sbrht,103,GetHandleId(sbru1))/100)
endfunction
function SbrPHAct takes nothing returns nothing
local unit sbru1=GetTriggerUnit()
local integer sbri1=GetHandleId(sbru1)
local real sbrr1=LoadReal(sbrht,103,sbri1)
local real sbrr2=GetUnitState(sbru1,UNIT_STATE_LIFE)
local timer sbrt1
if GetUnitState(sbru1,UNIT_STATE_MAX_LIFE)-sbrr2<GetEventDamage()*sbrr1/100 then
call SaveReal(sbrht,104,sbri1,sbrr2)
call SaveUnitHandle(sbrht,104,2,sbru1)
set sbrt1=CreateTimer()
call TimerStart(sbrt1,0,false,function SbrPHT)
else
call SetUnitState(sbru1,UNIT_STATE_LIFE,sbrr2+GetEventDamage()*sbrr1/100)
endif
endfunction
function SbrPDAct2 takes nothing returns nothing
local unit sbru1=GetEventDamageSource()
local unit sbru2=GetTriggerUnit()
local real sbrr1=GetEventDamage()
if sbru1==LoadUnitHandle(sbrht,105,GetHandleId(sbru2)) then
call DestroyTrigger(GetTriggeringTrigger())
call UnitDamageTarget(sbru1,sbru2,sbrr1/100*LoadReal(sbrht,105,GetHandleId(sbru1)),true,true,ATTACK_TYPE_HERO,DAMAGE_TYPE_FIRE,WEAPON_TYPE_WHOKNOWS)
endif
endfunction
function SbrPDAct takes nothing returns nothing
local trigger sbrt1=CreateTrigger()
local unit sbru1=GetTriggerUnit()
call SaveUnitHandle(sbrht,105,GetHandleId(sbru1),GetAttacker())
call TriggerAddAction(sbrt1,function SbrPDAct2)
call TriggerRegisterUnitEvent(sbrt1,sbru1,EVENT_UNIT_DAMAGED)
endfunction
function SbrPDCond takes nothing returns boolean
return LoadReal(sbrht,105,GetHandleId(GetAttacker()))>0
endfunction
function SbrHMLP takes nothing returns nothing
local real sbrr1=sbrarr[0]
local unit sbru1=sbraru[0]
local integer sbri1=GetHandleId(sbru1)
local trigger sbrt1
if sbrars[sbrari[14]+1]!="off" and sbrr1!=0 then
set sbrt1=CreateTrigger()
if sbrars[1]=="hl" or sbrars[1]=="hplow" then
call SaveReal(sbrht,100,sbri1,sbrr1)
call TriggerAddAction(sbrt1,function SbrHLAct)
call TriggerRegisterUnitEvent(sbrt1,sbru1,EVENT_UNIT_DAMAGED)
loop
call TriggerSleepAction(.5)
exitwhen sbrr1!=LoadReal(sbrht,100,sbri1)
endloop
elseif sbrars[1]=="ml" or sbrars[1]=="mplow" then
call SaveReal(sbrht,101,sbri1,sbrr1)
call TriggerAddAction(sbrt1,function SbrMLAct)
call TriggerRegisterUnitEvent(sbrt1,sbru1,EVENT_UNIT_SPELL_ENDCAST)
call TriggerRegisterUnitEvent(sbrt1,sbru1,EVENT_UNIT_SPELL_FINISH)
loop
call TriggerSleepAction(.5)
exitwhen sbrr1!=LoadReal(sbrht,101,sbri1)
endloop
elseif sbrars[1]=="pm" or sbrars[1]=="percentmana" then
call SaveReal(sbrht,102,sbri1,sbrr1)
call TriggerAddAction(sbrt1,function SbrPMAct)
call TriggerRegisterUnitEvent(sbrt1,sbru1,EVENT_UNIT_SPELL_EFFECT)
loop
call TriggerSleepAction(.5)
exitwhen sbrr1!=LoadReal(sbrht,102,sbri1)
endloop
elseif sbrars[1]=="ph" or sbrars[1]=="percenthp" then
call SaveReal(sbrht,103,sbri1,sbrr1)
call TriggerAddAction(sbrt1,function SbrPHAct)
call TriggerRegisterUnitEvent(sbrt1,sbru1,EVENT_UNIT_DAMAGED)
loop
call TriggerSleepAction(.5)
exitwhen sbrr1!=LoadReal(sbrht,103,sbri1)
endloop
elseif sbrars[1]=="pa" or sbrars[1]=="percentattack" then
call SaveReal(sbrht,105,sbri1,sbrr1)
call TriggerAddAction(sbrt1,function SbrPDAct)
call TriggerRegisterAnyUnitEventBJ(sbrt1,EVENT_PLAYER_UNIT_ATTACKED)
call TriggerAddCondition(sbrt1,Condition(function SbrPDCond))
loop
call TriggerSleepAction(.5)
exitwhen sbrr1!=LoadReal(sbrht,105,sbri1)
endloop
endif
call DestroyTrigger(sbrt1)
set sbrt1=null
else
if sbrars[1]=="hl" or sbrars[1]=="hplow" then
call RemoveSavedReal(sbrht,100,sbri1)
elseif sbrars[1]=="ml" or sbrars[1]=="mplow" then
call RemoveSavedReal(sbrht,101,sbri1)
elseif sbrars[1]=="pm" or sbrars[1]=="percentmana" then
call RemoveSavedReal(sbrht,102,sbri1)
elseif sbrars[1]=="ph" or sbrars[1]=="percenthp" then
call RemoveSavedReal(sbrht,103,sbri1)
else
call RemoveSavedReal(sbrht,105,sbri1)
endif
endif
endfunction
function SbrTP takes unit sbru1 returns nothing
if GetIssuedOrderId()==851986 or GetIssuedOrderId()==851990 or GetIssuedOrderId()==851990 then
call SetUnitX(sbru1,GetOrderPointX())
call SetUnitY(sbru1,GetOrderPointY())
else
call SetUnitX(sbru1,GetCameraTargetPositionX())
call SetUnitY(sbru1,GetCameraTargetPositionY())
endif
endfunction
function SbrItemID takes unit sbru1 returns nothing
local integer sbri1=sbrari[13]
loop
call DisplayTextToPlayer(GetTriggerPlayer(),0,0,SbrRAW2S(GetItemTypeId(UnitItemInSlot(sbru1,sbrari[16+sbri1]))))
set sbri1=sbri1-1
exitwhen sbri1<1
endloop
endfunction
function SbrItemCharge takes unit sbru1 returns nothing
local integer sbri1=sbrari[13]
loop
call SetItemCharges(UnitItemInSlot(sbru1,sbrari[16+sbri1]),R2I(sbrarr[0]))
set sbri1=sbri1-1
exitwhen sbri1<1
endloop
endfunction
function SbrSpawnUnit takes unit sbru1 returns nothing
local integer sbri1
local integer sbri2
local integer sbri3=sbrari[14]
loop
set sbri1=sbrari[15]
loop
set sbri2=R2I(sbrarr[0])
loop
call SetPlayerTechResearchedSwap(SbrS2RAW(sbrars[sbri3+1]),3,sbrarp[sbri1-1])
call CreateUnitAtLoc(sbrarp[sbri1-1],SbrS2RAW(sbrars[sbri3+1]),GetUnitLoc(sbru1),GetUnitFacing(sbru1))
call CreateDestructableLoc(SbrS2RAW(sbrars[sbri3+1]),GetUnitLoc(sbru1),GetUnitFacing(sbru1),1,10)
call CreateItemLoc(SbrS2RAW(sbrars[sbri3+1]),GetUnitLoc(sbru1))
set sbri2=sbri2-1
exitwhen sbri2<1
endloop
set sbri1=sbri1-1
exitwhen sbri1<1
endloop
set sbri3=sbri3-1
exitwhen sbri3<1
endloop
endfunction
function SbrCopyItem takes unit sbru1 returns nothing
local integer sbri1=sbrari[13]
set sbrari[14]=0
loop
set sbrari[14]=sbrari[14]+1
set sbrars[sbrari[14]+1]=SbrRAW2S(GetItemTypeId(UnitItemInSlot(sbru1,sbrari[16+sbri1])))
set sbri1=sbri1-1
exitwhen sbri1<1
endloop
call SbrSpawnUnit(sbru1)
endfunction
function SbrCS takes nothing returns nothing
loop
call StoreReal(SabRaC,"sbrcs",sbrars[sbrari[14]+1],sbrarr[0])
if sbrars[sbrari[14]+1]=="static" or sbrars[sbrari[14]+1]=="reaper" or sbrars[sbrari[14]+1]=="heartstopper" or sbrars[sbrari[14]+1]=="power" or sbrars[sbrari[14]+1]=="snaked" or sbrars[sbrari[14]+1]=="snakem" or sbrars[sbrari[14]+1]=="snakec" or sbrars[sbrari[14]+1]=="divided" or sbrars[sbrari[14]+1]=="poof" or sbrars[sbrari[14]+1]=="basherc" or sbrars[sbrari[14]+1]=="bashert" or sbrars[sbrari[14]+1]=="greedl" or sbrars[sbrari[14]+1]=="greedt" or sbrars[sbrari[14]+1]=="greed" or sbrars[sbrari[14]+1]=="devour" or sbrars[sbrari[14]+1]=="juxtapose" or sbrars[sbrari[14]+1]=="edge" or sbrars[sbrari[14]+1]=="lvld" or sbrars[sbrari[14]+1]=="lvlb" or sbrars[sbrari[14]+1]=="edictd" or sbrars[sbrari[14]+1]=="edictt" or sbrars[sbrari[14]+1]=="cask" or sbrars[sbrari[14]+1]=="caskd" or sbrars[sbrari[14]+1]=="decayt"or sbrars[sbrari[14]+1]=="decayd" or sbrars[sbrari[14]+1]=="decays" or sbrars[sbrari[14]+1]=="batteryt" or sbrars[sbrari[14]+1]=="maledicta" or sbrars[sbrari[14]+1]=="quillt" or sbrars[sbrari[14]+1]=="quilld" or sbrars[sbrari[14]+1]=="quilll" or sbrars[sbrari[14]+1]=="quillc" or sbrars[sbrari[14]+1]=="iont" or sbrars[sbrari[14]+1]=="vacuum"or sbrars[sbrari[14]+1]=="vacuumd" or sbrars[sbrari[14]+1]=="chrono" or sbrars[sbrari[14]+1]=="bt" or sbrars[sbrari[14]+1]=="culling" or sbrars[sbrari[14]+1]=="helixc"or sbrars[sbrari[14]+1]=="helixa" or sbrars[sbrari[14]+1]=="helixd" or sbrars[sbrari[14]+1]=="bathh" or sbrars[sbrari[14]+1]=="bathc" or sbrars[sbrari[14]+1]=="ruptured" or sbrars[sbrari[14]+1]=="rupture" or sbrars[sbrari[14]+1]=="rupturel" or sbrars[sbrari[14]+1]=="rupturet" or sbrars[sbrari[14]+1]=="balld" or sbrars[sbrari[14]+1]=="ballim" or sbrars[sbrari[14]+1]=="ballcim" or sbrars[sbrari[14]+1]=="ballm" or sbrars[sbrari[14]+1]=="ballcm" or sbrars[sbrari[14]+1]=="epicenter" or sbrars[sbrari[14]+1]=="iond" or sbrars[sbrari[14]+1]=="iona" or sbrars[sbrari[14]+1]=="omnislash" or sbrars[sbrari[14]+1]=="omnislashd" or sbrars[sbrari[14]+1]=="eclipsel" or sbrars[sbrari[14]+1]=="eclipsed" or sbrars[sbrari[14]+1]=="eclipse" or sbrars[sbrari[14]+1]=="quill" or sbrars[sbrari[14]+1]=="bb" or sbrars[sbrari[14]+1]=="bba" or sbrars[sbrari[14]+1]=="bbd" or sbrars[sbrari[14]+1]=="cf" or sbrars[sbrari[14]+1]=="cft" or sbrars[sbrari[14]+1]=="ffa" or sbrars[sbrari[14]+1]=="ffd" or sbrars[sbrari[14]+1]=="refraction" or sbrars[sbrari[14]+1]=="multi" or sbrars[sbrari[14]+1]=="multic" or sbrars[sbrari[14]+1]=="speard"or sbrars[sbrari[14]+1]=="speart" or sbrars[sbrari[14]+1]=="vitality" or sbrars[sbrari[14]+1]=="vitalityt" or sbrars[sbrari[14]+1]=="batteryc" or sbrars[sbrari[14]+1]=="batteryd" or sbrars[sbrari[14]+1]=="adaptive" or sbrars[sbrari[14]+1]=="dispersion" or sbrars[sbrari[14]+1]=="maledict" or sbrars[sbrari[14]+1]=="tossd" or sbrars[sbrari[14]+1]=="tossa" or sbrars[sbrari[14]+1]=="craggy" or sbrars[sbrari[14]+1]=="plasma" or sbrars[sbrari[14]+1]=="storm" or sbrars[sbrari[14]+1]=="stormd" or sbrars[sbrari[14]+1]=="rip" or sbrars[sbrari[14]+1]=="ea" or sbrars[sbrari[14]+1]=="sanity" or sbrars[sbrari[14]+1]=="arcane" or sbrars[sbrari[14]+1]=="void" or sbrars[sbrari[14]+1]=="voida" or sbrars[sbrari[14]+1]=="aphotic" or sbrars[sbrari[14]+1]=="borrowed" or sbrars[sbrari[14]+1]=="gb" or sbrars[sbrari[14]+1]=="gbd" or sbrars[sbrari[14]+1]=="shallow" or sbrars[sbrari[14]+1]=="wisdom" or sbrars[sbrari[14]+1]=="necromastery" or sbrars[sbrari[14]+1]=="requiem" or sbrars[sbrari[14]+1]=="torrentd" or sbrars[sbrari[14]+1]=="torrenta" or sbrars[sbrari[14]+1]=="tidebringer" or sbrars[sbrari[14]+1]=="bs" or sbrars[sbrari[14]+1]=="bha" or sbrars[sbrari[14]+1]=="limpaled" or sbrars[sbrari[14]+1]=="limpales" or sbrars[sbrari[14]+1]=="limpaler" or sbrars[sbrari[14]+1]=="aimpaled" or sbrars[sbrari[14]+1]=="aimpaler" or sbrars[sbrari[14]+1]=="aimpales" or sbrars[sbrari[14]+1]=="ravaged" or sbrars[sbrari[14]+1]=="ravages" or sbrars[sbrari[14]+1]=="ravagea" then
call DisplayTimedTextToPlayer(GetTriggerPlayer(),0,0,2,"|CFF0009FF"+sbrars[sbrari[14]+1]+"|r |CFFC9F82C"+R2S(GetStoredReal(SabRaC,"sbrcs",sbrars[sbrari[14]+1])))
elseif sbrars[sbrari[14]+1]=="help" then
call DisplayTimedTextToPlayer(GetTriggerPlayer(),0,0,sbrarr[0],"chrono"+" bt"+" culling"+" helixc"+" helixa"+" helixd"+" bath"+" ruptured"+" rupturet"+" balld"+" ballm"+" epicenter"+" vacuum"+" vacuumd"+" iond"+" ionr"+" iont"+" omnislash"+" omnislashd"+" eclipse"+" eclipsel"+" quill"+" quilld"+" quillt"+" bb"+" bba"+" bbd"+" cf"+" ffa"+" ffd"+" refraction"+" juxtapose"+" edge"+" multi"+" multic"+" speard"+" speart"+" vitality"+" vitalityt"+" batteryc"+" batteryt"+" adaptive"+" dispersion"+" gravekeeper"+" maledict"+" maledicta"+" cask"+" tossd"+" tossa"+" craggy"+" plasma"+" storm"+" stormd"+" rip"+" ea"+" sanity"+" arcane"+" void"+" voida"+" aphotic"+" borrowed"+" gb"+" shallow"+" wisdom"+" necromastery"+" requiem"+" torrent"+" tidebringer"+" bs"+" decayt"+" decayd"+" decays"+" edictt"+" edictd"+" greed"+" greedt"+" lvld"+" devour"+" poof"+" basherc"+" bashert"+" divided"+" snaked"+" snakem"+" snakec"+" power"+" heartstopper"+" reaper"+" static"+" bha"+" limpaled"+" limpaler"+" limpales"+" aimpaled"+" aimpaler"+" aimpales"+" ravaged"+" ravagea"+" ravages")
else
call DisplayTimedTextToPlayer(GetTriggerPlayer(),0,0,2,"|CFFFF0000"+sbrars[sbrari[14]+1]+"|r |CFFC9F82C"+R2S(GetStoredReal(SabRaC,"sbrcs",sbrars[sbrari[14]+1])))
endif
set sbrari[14]=sbrari[14]-1
exitwhen sbrari[14]<1
endloop
endfunction
function SbrCopyUnit takes unit sbru1 returns nothing
set sbrari[14]=1
set sbrars[sbrari[14]+1]=SbrRAW2S(GetUnitTypeId(sbru1))
call SbrSpawnUnit(sbru1)
endfunction
function SbrAddAbility takes unit sbru1 returns nothing
local integer sbri1=sbrari[14]
if sbrars[sbrari[14]+1]=="off" then
loop
call UnitRemoveAbility(sbru1,SbrS2RAW(sbrars[sbri1+1]))
set sbri1=sbri1-1
exitwhen sbri1<1
endloop
elseif sbrars[sbrari[14]+1]=="list" then
call DisplayTimedTextToPlayer(sbrarp[sbrari[15]-1],0,0,2,"|CFFFF0000A0HD|r"+" |CFFC9F82CASPD +55|r")
call DisplayTimedTextToPlayer(sbrarp[sbrari[15]-1],0,0,2,"|CFFFF0000AIsx|r"+" |CFFC9F82CASPD +15|r")
call DisplayTimedTextToPlayer(sbrarp[sbrari[15]-1],0,0,2,"|CFFFF0000A0tx|r"+" |CFFC9F82CDamage +20|r")
else
loop
call UnitAddAbility(sbru1,SbrS2RAW(sbrars[sbri1+1]))
call SetUnitAbilityLevel(sbru1,SbrS2RAW(sbrars[sbri1+1]),R2I(sbrarr[0]))
call UnitMakeAbilityPermanent(sbru1,true,SbrS2RAW(sbrars[sbri1+1]))
set sbri1=sbri1-1
exitwhen sbri1<1
endloop
endif
endfunction
function SbrIp takes nothing returns nothing
set sbrari[24+GetPlayerId(GetTriggerPlayer())]=sbrari[24+GetPlayerId(GetTriggerPlayer())]-1
endfunction
function SbrIP takes nothing returns nothing
local integer sbri1=GetPlayerId(sbrarp[sbrari[15]-1])
local integer sbri2=GetPlayerId(sbrarp[sbrari[16]+15])
local trigger sbrt1
if sbrari[24+sbri1]<1 then
set sbrt1=CreateTrigger()
call TriggerRegisterPlayerChatEvent(sbrt1,sbrarp[sbrari[15]-1],"",false)
call TriggerAddAction(sbrt1,function SbrIp)
endif
set sbrari[24+sbri1]=R2I(sbrarr[0])
call SetPlayerName(sbrarp[sbrari[15]-1],sbrars[37+sbri2])
call SetPlayerColor(sbrarp[sbrari[15]-1],sbrarpc[sbri2])
loop
call TriggerSleepAction(.5)
exitwhen sbrari[24+sbri1]<1
endloop
call DestroyTrigger(sbrt1)
call SetPlayerName(sbrarp[sbrari[15]-1],sbrars[37+sbri1])
call SetPlayerColor(sbrarp[sbrari[15]-1],sbrarpc[sbri1])
endfunction


function SbrMain takes nothing returns nothing
local integer sbri1
local group sbrg1=CreateGroup()
local unit sbru1=null
if sbrars[1]=="cb" or sbrars[1]=="changeboss" then
if sbrari[14]!=0 then
set sbrars[0]=sbrars[sbrari[14]+1]
if sbrars[0]==sabrac_boss then
call DisplayTimedTextToPlayer(GetTriggerPlayer(),0,0,3,"The |CFF1CE6B9BOSS|r has changed to "+sbrars[0])
elseif sbrars[0]!=sabrac_boss then
set sbrars[0]=sabrac_boss
call DisplayTimedTextToPlayer(GetTriggerPlayer(),0,0,3,"The |CFF1CE6B9BOSS|r has returned to "+sbrars[0])
endif
endif
elseif sbrars[1]=="help" then
call SbrHelp()
elseif sbrars[1]=="nr" or sbrars[1]=="noreplay" then
call DoNotSaveReplay()
elseif sbrars[1]=="sb" or sbrars[1]=="showbinding" then
call SbrShowBinding()
elseif sbrars[1]=="br" or sbrars[1]=="break" then
call TriggerSleepAction(sbrarr[0])
elseif sbrars[1]=="gs" or sbrars[1]=="gamespeed" then
if sbrars[sbrari[14]+1]=="slow" then
set sbri1=0
elseif sbrars[sbrari[14]+1]=="normal" then
set sbri1=1
elseif sbrars[sbrari[14]+1]=="fast" then
set sbri1=2
elseif sbrars[sbrari[14]+1]=="pause" then
call PauseGame(true)
elseif sbrars[sbrari[14]+1]=="resume" then
call PauseGame(false)
endif
call SetGameSpeed(ConvertGameSpeed(sbri1))
elseif sbrars[1]=="ec" or sbrars[1]=="enablecheat" or sbrars[1]=="dc" or sbrars[1]=="disablecheat" then
call ExecuteFunc("SbrEC")
elseif sbrars[1]=="xr" or sbrars[1]=="xprate" then
call ExecuteFunc("SbrXR")
elseif sbrars[1]=="go" or sbrars[1]=="lb" or sbrars[1]=="gold" or sbrars[1]=="lumber" then
call ExecuteFunc("SbrGL")
elseif sbrars[1]=="gr" or sbrars[1]=="lr" or sbrars[1]=="goldrate" or sbrars[1]=="lumberrate" then
call ExecuteFunc("SbrGLRate")
elseif sbrars[1]=="kc" or sbrars[1]=="kick" then
call ExecuteFunc("SbrKick")
elseif sbrars[1]=="sl" or sbrars[1]=="slowcomputer" then
elseif sbrars[1]=="cs" or sbrars[1]=="changeskill" then
call ExecuteFunc("SbrCS")
elseif sbrars[1]=="ip" or sbrars[1]=="impersonate" then
call SbrIP()
elseif sbrars[1]=="sc" or sbrars[1]=="sv" or sbrars[1]=="sharevision" or sbrars[1]=="sharecontrol" then
call ExecuteFunc("SbrShare")
elseif sbrars[1]=="ri" or sbrars[1]=="reinit" then
call ExecuteFunc("ReInitSabRaCCP")
endif
call GroupEnumUnitsSelected(sbrg1,GetTriggerPlayer(),null)
loop
set sbru1=FirstOfGroup(sbrg1)
exitwhen sbru1==null
call GroupRemoveUnit(sbrg1,sbru1)
set sbraru[0]=sbru1
if sbrars[1]=="allstats" or sbrars[1]=="as" or sbrars[1]=="st" or sbrars[1]=="str" or sbrars[1]=="ag" or sbrars[1]=="agi" or sbrars[1]=="it" or sbrars[1]=="int" or sbrars[1]=="rs" or sbrars[1]=="removestats" then
call SbrStat()
elseif sbrars[1]=="ms" or sbrars[1]=="movespeed" then
call SetUnitMoveSpeed(sbru1,GetUnitDefaultMoveSpeed(sbru1)+sbrarr[0])
elseif sbrars[1]=="xp" then
call AddHeroXP(sbru1,R2I(sbrarr[0]),false)
elseif sbrars[1]=="Xp" then
call AddHeroXP(sbru1,R2I(sbrarr[0]),true)
elseif sbrars[1]=="lv" or sbrars[1]=="Lv" or sbrars[1]=="level" or sbrars[1]=="Level" then
if sbrarr[0]>GetHeroLevel(sbru1) then
call SetHeroLevel(sbru1,R2I(sbrarr[0]),SubString(sbrars[1],0,1)=="L")
else
call UnitStripHeroLevel(sbru1,GetHeroLevel(sbru1)-R2I(sbrarr[0]))
endif
elseif sbrars[1]=="sp" or sbrars[1]=="skillpoint" then
call UnitModifySkillPoints(sbru1,R2I(sbrarr[0]-GetHeroSkillPoints(sbru1)))
elseif sbrars[1]=="hp" then
call SetUnitState(sbru1,UNIT_STATE_LIFE,sbrarr[0])
elseif sbrars[1]=="mp"then
call SetUnitState(sbru1,UNIT_STATE_MANA,sbrarr[0])
elseif sbrars[1]=="ah" or sbrars[1]=="addhp" then
call SetUnitState(sbru1,UNIT_STATE_LIFE,sbrarr[0]+GetUnitState(sbru1,UNIT_STATE_LIFE))
elseif sbrars[1]=="am" or sbrars[1]=="addmp" then
call SetUnitState(sbru1,UNIT_STATE_MANA,sbrarr[0]+GetUnitState(sbru1,UNIT_STATE_MANA))
elseif sbrars[1]=="hr" or sbrars[1]=="hpregen" then
call ExecuteFunc("SbrHR")
elseif sbrars[1]=="mr" or sbrars[1]=="mpregen" then
call ExecuteFunc("SbrMR")
elseif sbrars[1]=="rg" or sbrars[1]=="regen" then
if sbrars[sbrari[14]+1]!="off"then
call ExecuteFunc("SbrHR")
call ExecuteFunc("SbrMR")
else
call SbrRR(sbru1)
endif
elseif sbrars[1]=="rr" or sbrars[1]=="removeregen"then
call SbrRR(sbru1)
elseif sbrars[1]=="hl" or sbrars[1]=="hplow" or sbrars[1]=="ml" or sbrars[1]=="mplow" or sbrars[1]=="pm" or sbrars[1]=="percentmana" or sbrars[1]=="ph" or sbrars[1]=="percenthp" or sbrars[1]=="pa" or sbrars[1]=="percentattack" then
call ExecuteFunc("SbrHMLP")
elseif sbrars[1]=="si" or sbrars[1]=="size" then
call SetUnitScalePercent(sbru1,sbrarr[0]/100,sbrarr[0]/100,sbrarr[0]/100)
elseif sbrars[1]=="rf" or sbrars[1]=="refresh" then
call UnitResetCooldown(sbru1)
elseif sbrars[1]=="tp" or sbrars[1]=="teleport" then
call SbrTP(sbru1)
elseif sbrars[1]=="tl" or sbrars[1]=="timedlife" then
if sbrarr[0]!=0 then
call UnitApplyTimedLife(sbru1,0,sbrarr[0])
endif
if sbrars[sbrari[14]+1]=="pause" then
call UnitPauseTimedLife(sbru1,true)
elseif sbrars[sbrari[14]+1]=="remove" then
call UnitApplyTimedLife(sbru1,0,0)
else
call UnitPauseTimedLife(sbru1,false)
endif
elseif sbrars[1]=="ui" or sbrars[1]=="unitid" then
call DisplayTimedTextToPlayer(GetTriggerPlayer(),0,0,2,SbrRAW2S(GetUnitTypeId(sbru1)))
elseif sbrars[1]=="uo" or sbrars[1]=="unitowner" then
call DisplayTimedTextToPlayer(GetTriggerPlayer(),0,0,2,GetPlayerName(GetOwningPlayer(sbru1)))
elseif sbrars[1]=="ii" or sbrars[1]=="itemid" then
call SbrItemID(sbru1)
elseif sbrars[1]=="ic" or sbrars[1]=="itemcharge" then
call SbrItemCharge(sbru1)
elseif sbrars[1]=="su" or sbrars[1]=="spawn" then
call SbrSpawnUnit(sbru1)
elseif sbrars[1]=="cu" or sbrars[1]=="copyunit" then
call SbrCopyUnit(sbru1)
elseif sbrars[1]=="ci" or sbrars[1]=="copyitem" then
call SbrCopyItem(sbru1)
elseif sbrars[1]=="iv" or sbrars[1]=="invulnerable" then
if sbrars[sbrari[14]+1]=="off" then
call SetUnitInvulnerable(sbru1,false)
else
call SetUnitInvulnerable(sbru1,true)
endif
elseif sbrars[1]=="pu" or sbrars[1]=="pauseunit" then
if sbrars[sbrari[14]+1]=="off" then
call PauseUnit(sbru1,false)
else
call PauseUnit(sbru1,true)
endif
elseif sbrars[1]=="aa" or sbrars[1]=="addability" then
call SbrAddAbility(sbru1)
elseif sbrars[1]=="co" or sbrars[1]=="changeowner" then
call SetUnitOwner(sbru1,sbrarp[sbrari[15]-1],true)
elseif sbrars[1]=="removeunit" then
call RemoveUnit(sbru1)
elseif sbrars[1]=="up" or sbrars[1]=="unitpathing" then
call SetUnitPathing(sbru1,sbrars[sbrari[14]+1]!="off")
endif
endloop
endfunction

function SbrBindAct takes string sbrs1 returns nothing
local string sbrs2=""
local integer sbri1=StringLength(sbrs1)
loop
if SubString(sbrs1,sbri1-1,sbri1)!="}" then
set sbrs2=SubString(sbrs1,sbri1-1,sbri1)+sbrs2
else
if sbrs2!="" then
set sbrars[21]=sbrs2
call SbrScanner()
call SbrMain()
endif
set sbrs2=""
endif
set sbri1=sbri1-1
exitwhen sbri1<1
endloop
endfunction
function SbrDu takes nothing returns nothing
if GetStoredString(SabRaC,I2S(GetPlayerId(GetTriggerPlayer())),"ud")!="" and GetStoredString(SabRaC,I2S(GetPlayerId(GetTriggerPlayer())),"ud")!=null then
call SbrBindAct(GetStoredString(SabRaC,I2S(GetPlayerId(GetTriggerPlayer())),"ud"))
endif
endfunction
function SbrLu takes nothing returns nothing
if GetStoredString(SabRaC,I2S(GetPlayerId(GetTriggerPlayer())),"lu")!="" and GetStoredString(SabRaC,I2S(GetPlayerId(GetTriggerPlayer())),"lu")!=null then
call SbrBindAct(GetStoredString(SabRaC,I2S(GetPlayerId(GetTriggerPlayer())),"lu"))
endif
endfunction
function SbrRu takes nothing returns nothing
if GetStoredString(SabRaC,I2S(GetPlayerId(GetTriggerPlayer())),"ru")!="" and GetStoredString(SabRaC,I2S(GetPlayerId(GetTriggerPlayer())),"ru")!=null then
call SbrBindAct(GetStoredString(SabRaC,I2S(GetPlayerId(GetTriggerPlayer())),"ru"))
endif
endfunction
function SbrLd takes nothing returns nothing
if GetStoredString(SabRaC,I2S(GetPlayerId(GetTriggerPlayer())),"ld")!="" and GetStoredString(SabRaC,I2S(GetPlayerId(GetTriggerPlayer())),"ld")!=null then
call SbrBindAct(GetStoredString(SabRaC,I2S(GetPlayerId(GetTriggerPlayer())),"ld"))
endif
endfunction
function SbrRd takes nothing returns nothing
if GetStoredString(SabRaC,I2S(GetPlayerId(GetTriggerPlayer())),"rd")!="" and GetStoredString(SabRaC,I2S(GetPlayerId(GetTriggerPlayer())),"rd")!=null then
call SbrBindAct(GetStoredString(SabRaC,I2S(GetPlayerId(GetTriggerPlayer())),"rd"))
endif
endfunction
function SbrLr takes nothing returns nothing
if GetStoredString(SabRaC,I2S(GetPlayerId(GetTriggerPlayer())),"rl")!="" and GetStoredString(SabRaC,I2S(GetPlayerId(GetTriggerPlayer())),"rl")!=null then
call SbrBindAct(GetStoredString(SabRaC,I2S(GetPlayerId(GetTriggerPlayer())),"rl"))
endif
endfunction
function SbrUD takes nothing returns nothing
set sbrari[GetPlayerId(GetTriggerPlayer())+36]=sbrari[GetPlayerId(GetTriggerPlayer())+36]+1
if sbrari[GetPlayerId(GetTriggerPlayer())+48]>0 then
call ExecuteFunc("SbrDu")
elseif sbrari[GetPlayerId(GetTriggerPlayer())+60]>0 then
call ExecuteFunc("SbrLu")
elseif sbrari[GetPlayerId(GetTriggerPlayer())+72]>0 then
call ExecuteFunc("SbrRu")
endif
endfunction
function SbrUU takes nothing returns nothing
set sbrari[GetPlayerId(GetTriggerPlayer())+36]=sbrari[GetPlayerId(GetTriggerPlayer())+36]-1
endfunction
function SbrDD takes nothing returns nothing
set sbrari[GetPlayerId(GetTriggerPlayer())+48]=sbrari[GetPlayerId(GetTriggerPlayer())+48]+1
if sbrari[GetPlayerId(GetTriggerPlayer())+36]>0 then
call ExecuteFunc("SbrDu")
elseif sbrari[GetPlayerId(GetTriggerPlayer())+60]>0 then
call ExecuteFunc("SbrLd")
elseif sbrari[GetPlayerId(GetTriggerPlayer())+72]>0 then
call ExecuteFunc("SbrRd")
endif
endfunction
function SbrDU takes nothing returns nothing
set sbrari[GetPlayerId(GetTriggerPlayer())+48]=sbrari[GetPlayerId(GetTriggerPlayer())+48]-1
endfunction
function SbrLD takes nothing returns nothing
set sbrari[GetPlayerId(GetTriggerPlayer())+60]=sbrari[GetPlayerId(GetTriggerPlayer())+60]+1
if sbrari[GetPlayerId(GetTriggerPlayer())+36]>0 then
call ExecuteFunc("SbrLu")
elseif sbrari[GetPlayerId(GetTriggerPlayer())+48]>0 then
call ExecuteFunc("SbrLd")
elseif sbrari[GetPlayerId(GetTriggerPlayer())+72]>0 then
call ExecuteFunc("SbrLr")
endif
endfunction
function SbrLU takes nothing returns nothing
set sbrari[GetPlayerId(GetTriggerPlayer())+60]=sbrari[GetPlayerId(GetTriggerPlayer())+60]-1
endfunction
function SbrRD takes nothing returns nothing
set sbrari[GetPlayerId(GetTriggerPlayer())+72]=sbrari[GetPlayerId(GetTriggerPlayer())+72]+1
if sbrari[GetPlayerId(GetTriggerPlayer())+36]>0 then
call ExecuteFunc("SbrRu")
elseif sbrari[GetPlayerId(GetTriggerPlayer())+48]>0 then
call ExecuteFunc("SbrRd")
elseif sbrari[GetPlayerId(GetTriggerPlayer())+60]>0 then
call ExecuteFunc("SbrLr")
endif
endfunction
function SbrRU takes nothing returns nothing
set sbrari[GetPlayerId(GetTriggerPlayer())+72]=sbrari[GetPlayerId(GetTriggerPlayer())+72]-1
endfunction
function SbrEsc takes nothing returns nothing
call SbrBindAct(GetStoredString(SabRaC,I2S(GetPlayerId(GetTriggerPlayer())),"esc"))
endfunction
function SbrMove takes nothing returns nothing
if GetIssuedOrderId()==851986 then
call SbrBindAct(GetStoredString(SabRaC,I2S(GetPlayerId(GetTriggerPlayer())),"move"))
endif
endfunction
function SbrHold takes nothing returns nothing
if GetIssuedOrderId()==851993 then
call SbrBindAct(GetStoredString(SabRaC,I2S(GetPlayerId(GetTriggerPlayer())),"hold"))
endif
endfunction
function SbrStop takes nothing returns nothing
if GetIssuedOrderId()==851972 then
call SbrBindAct(GetStoredString(SabRaC,I2S(GetPlayerId(GetTriggerPlayer())),"stop"))
endif
endfunction
function SbrPatrol takes nothing returns nothing
if GetIssuedOrderId()==851990 then
call SbrBindAct(GetStoredString(SabRaC,I2S(GetPlayerId(GetTriggerPlayer())),"ptrl"))
endif
endfunction
function SbrBind takes nothing returns nothing
local trigger sbrt1
local trigger sbrt2
local trigger sbrt3
local trigger sbrt4
local triggeraction sbrta1
local string sbrs1=sbrars[35]
local string sbrs2=sbrars[36]
local string sbrs3=I2S(GetPlayerId(sbrarp[sbrari[124]+44]))
if sbrs1!=null then
if sbrs2!="" then
if GetStoredString(SabRaC,sbrs3,sbrs1)!="" and GetStoredString(SabRaC,sbrs3,sbrs1)!=null then
call StoreString(SabRaC,sbrs3,sbrs1,"}"+sbrs2+"}"+SubString(GetStoredString(SabRaC,sbrs3,sbrs1),1,StringLength(GetStoredString(SabRaC,sbrs3,sbrs1))))
call DisplayTimedTextToPlayer(sbrarp[sbrari[124]+44],0,0,2,"|CFF540081"+sbrs1+"|r <-- "+sbrs2)
else
call StoreString(SabRaC,sbrs3,sbrs1,"}"+sbrs2)
call DisplayTimedTextToPlayer(sbrarp[sbrari[124]+44],0,0,2,"|CFF540081"+sbrs1+"|r <-- "+sbrs2)
endif
if sbrs1=="ud" then
set sbrt1=CreateTrigger()
call TriggerRegisterPlayerEvent(sbrt1,sbrarp[sbrari[124]+44],EVENT_PLAYER_ARROW_UP_DOWN)
call TriggerAddAction(sbrt1,function SbrUD)
set sbrt2=CreateTrigger()
call TriggerRegisterPlayerEvent(sbrt2,sbrarp[sbrari[124]+44],EVENT_PLAYER_ARROW_UP_UP)
call TriggerAddAction(sbrt2,function SbrUU)
set sbrt3=CreateTrigger()
call TriggerRegisterPlayerEvent(sbrt3,sbrarp[sbrari[124]+44],EVENT_PLAYER_ARROW_DOWN_DOWN)
call TriggerAddAction(sbrt3,function SbrDD)
set sbrt4=CreateTrigger()
call TriggerRegisterPlayerEvent(sbrt4,sbrarp[sbrari[124]+44],EVENT_PLAYER_ARROW_DOWN_UP)
call TriggerAddAction(sbrt4,function SbrDU)
elseif sbrs1=="ld" then
set sbrt1=CreateTrigger()
call TriggerRegisterPlayerEvent(sbrt1,sbrarp[sbrari[124]+44],EVENT_PLAYER_ARROW_LEFT_DOWN)
call TriggerAddAction(sbrt1,function SbrLD)
set sbrt2=CreateTrigger()
call TriggerRegisterPlayerEvent(sbrt2,sbrarp[sbrari[124]+44],EVENT_PLAYER_ARROW_LEFT_UP)
call TriggerAddAction(sbrt2,function SbrLU)
set sbrt3=CreateTrigger()
call TriggerRegisterPlayerEvent(sbrt3,sbrarp[sbrari[124]+44],EVENT_PLAYER_ARROW_DOWN_DOWN)
call TriggerAddAction(sbrt3,function SbrDD)
set sbrt4=CreateTrigger()
call TriggerRegisterPlayerEvent(sbrt4,sbrarp[sbrari[124]+44],EVENT_PLAYER_ARROW_DOWN_UP)
call TriggerAddAction(sbrt4,function SbrDU)
elseif sbrs1=="rd" then
set sbrt1=CreateTrigger()
call TriggerRegisterPlayerEvent(sbrt1,sbrarp[sbrari[124]+44],EVENT_PLAYER_ARROW_RIGHT_DOWN)
call TriggerAddAction(sbrt1,function SbrRD)
set sbrt2=CreateTrigger()
call TriggerRegisterPlayerEvent(sbrt2,sbrarp[sbrari[124]+44],EVENT_PLAYER_ARROW_RIGHT_UP)
call TriggerAddAction(sbrt2,function SbrRU)
set sbrt3=CreateTrigger()
call TriggerRegisterPlayerEvent(sbrt3,sbrarp[sbrari[124]+44],EVENT_PLAYER_ARROW_DOWN_DOWN)
call TriggerAddAction(sbrt3,function SbrDD)
set sbrt4=CreateTrigger()
call TriggerRegisterPlayerEvent(sbrt4,sbrarp[sbrari[124]+44],EVENT_PLAYER_ARROW_DOWN_UP)
call TriggerAddAction(sbrt4,function SbrDU)
elseif sbrs1=="rl" then
set sbrt1=CreateTrigger()
call TriggerRegisterPlayerEvent(sbrt1,sbrarp[sbrari[124]+44],EVENT_PLAYER_ARROW_LEFT_DOWN)
call TriggerAddAction(sbrt1,function SbrLD)
set sbrt2=CreateTrigger()
call TriggerRegisterPlayerEvent(sbrt2,sbrarp[sbrari[124]+44],EVENT_PLAYER_ARROW_LEFT_UP)
call TriggerAddAction(sbrt2,function SbrLU)
set sbrt3=CreateTrigger()
call TriggerRegisterPlayerEvent(sbrt3,sbrarp[sbrari[124]+44],EVENT_PLAYER_ARROW_RIGHT_DOWN)
call TriggerAddAction(sbrt3,function SbrRD)
set sbrt4=CreateTrigger()
call TriggerRegisterPlayerEvent(sbrt4,sbrarp[sbrari[124]+44],EVENT_PLAYER_ARROW_RIGHT_UP)
call TriggerAddAction(sbrt4,function SbrRU)
elseif sbrs1=="lu" then
set sbrt1=CreateTrigger()
call TriggerRegisterPlayerEvent(sbrt1,sbrarp[sbrari[124]+44],EVENT_PLAYER_ARROW_UP_DOWN)
call TriggerAddAction(sbrt1,function SbrUD)
set sbrt2=CreateTrigger()
call TriggerRegisterPlayerEvent(sbrt2,sbrarp[sbrari[124]+44],EVENT_PLAYER_ARROW_UP_UP)
call TriggerAddAction(sbrt2,function SbrUU)
set sbrt3=CreateTrigger()
call TriggerRegisterPlayerEvent(sbrt3,sbrarp[sbrari[124]+44],EVENT_PLAYER_ARROW_LEFT_DOWN)
call TriggerAddAction(sbrt3,function SbrLD)
set sbrt4=CreateTrigger()
call TriggerRegisterPlayerEvent(sbrt4,sbrarp[sbrari[124]+44],EVENT_PLAYER_ARROW_LEFT_UP)
call TriggerAddAction(sbrt4,function SbrLU)
elseif sbrs1=="ru" then
set sbrt1=CreateTrigger()
call TriggerRegisterPlayerEvent(sbrt1,sbrarp[sbrari[124]+44],EVENT_PLAYER_ARROW_UP_DOWN)
call TriggerAddAction(sbrt1,function SbrUD)
set sbrt2=CreateTrigger()
call TriggerRegisterPlayerEvent(sbrt2,sbrarp[sbrari[124]+44],EVENT_PLAYER_ARROW_UP_UP)
call TriggerAddAction(sbrt2,function SbrUU)
set sbrt3=CreateTrigger()
call TriggerRegisterPlayerEvent(sbrt3,sbrarp[sbrari[124]+44],EVENT_PLAYER_ARROW_RIGHT_DOWN)
call TriggerAddAction(sbrt3,function SbrRD)
set sbrt4=CreateTrigger()
call TriggerRegisterPlayerEvent(sbrt4,sbrarp[sbrari[124]+44],EVENT_PLAYER_ARROW_RIGHT_UP)
call TriggerAddAction(sbrt4,function SbrRU)
elseif sbrs1=="esc" then
set sbrt1=CreateTrigger()
call TriggerRegisterPlayerEvent(sbrt1,sbrarp[sbrari[124]+44],EVENT_PLAYER_END_CINEMATIC)
call TriggerAddAction(sbrt1,function SbrEsc)
elseif sbrs1=="move" then
set sbrt1=CreateTrigger()
call TriggerRegisterPlayerUnitEvent(sbrt1,sbrarp[sbrari[124]+44],EVENT_PLAYER_UNIT_ISSUED_POINT_ORDER,null)
call TriggerAddAction(sbrt1,function SbrMove)
elseif sbrs1=="hold" then
set sbrt1=CreateTrigger()
call TriggerRegisterPlayerUnitEvent(sbrt1,sbrarp[sbrari[124]+44],EVENT_PLAYER_UNIT_ISSUED_ORDER,null)
call TriggerAddAction(sbrt1,function SbrHold)
elseif sbrs1=="stop" then
set sbrt1=CreateTrigger()
call TriggerRegisterPlayerUnitEvent(sbrt1,sbrarp[sbrari[124]+44],EVENT_PLAYER_UNIT_ISSUED_ORDER,null)
call TriggerAddAction(sbrt1,function SbrStop)
elseif sbrs1=="ptrl" then
call TriggerRegisterPlayerUnitEvent(sbrt1,sbrarp[sbrari[124]+44],EVENT_PLAYER_UNIT_ISSUED_POINT_ORDER,null)
call TriggerAddAction(sbrt1,function SbrPatrol)
endif
set sbrs2=GetStoredString(SabRaC,sbrs3,sbrs1)
loop
call TriggerSleepAction(.5)
exitwhen GetStoredString(SabRaC,sbrs3,sbrs1)!=sbrs2
endloop
call DestroyTrigger(sbrt1)
call DestroyTrigger(sbrt2)
call DestroyTrigger(sbrt3)
call DestroyTrigger(sbrt4)
set sbrt1=null
set sbrt2=null
set sbrt3=null
set sbrt4=null
else
call FlushStoredString(SabRaC,sbrs3,sbrs1)
endif
endif
endfunction

function SbrCKBind takes nothing returns nothing
if sbrars[35]=="ud" or sbrars[35]=="ld" or sbrars[35]=="rd" or sbrars[35]=="rl" or sbrars[35]=="lu" or sbrars[35]=="ru" or sbrars[35]=="esc" or sbrars[35]=="move" or sbrars[35]=="hold" or sbrars[35]=="stop" or sbrars[35]=="ptrl" then
loop
call ExecuteFunc("SbrBind")
call TriggerSleepAction(.05)
set sbrari[124]=sbrari[124]-1
exitwhen sbrari[124]<1
endloop
else
call ExecuteFunc("SbrMain")
endif
endfunction
function SbrUse takes nothing returns nothing
if sbrari[GetPlayerId(GetTriggerPlayer())+1]==-1 or sbrari[GetPlayerId(GetTriggerPlayer())+1]==1 then
set sbrars[21]=GetEventPlayerChatString()
call SbrScanner()
call ExecuteFunc("SbrCKBind")
endif
endfunction

function SbrAKI takes nothing returns nothing
local integer sbri1=0
local integer sbri2=GetPlayerId(GetTriggerPlayer())
if GetTriggerEventId()==EVENT_PLAYER_END_CINEMATIC then
if SubString(SbrRAW2S(sbrari[162+sbri2]),3,4)=="<" or SubString(SbrRAW2S(sbrari[162+sbri2]),2,3)=="<" or SubString(SbrRAW2S(sbrari[162+sbri2]),1,2)=="<" or SubString(SbrRAW2S(sbrari[162+sbri2]),0,1)=="<" then
set sbrars[100+sbri2]=""
elseif SubString(SbrRAW2S(sbrari[162+sbri2]),3,4)==">" or SubString(SbrRAW2S(sbrari[162+sbri2]),2,3)==">" or SubString(SbrRAW2S(sbrari[162+sbri2]),1,2)==">" or SubString(SbrRAW2S(sbrari[162+sbri2]),0,1)==">" then
set sbrars[21]=sbrars[100+sbri2]
call SbrScanner()
call ExecuteFunc("SbrCKBind")
elseif SubString(SbrRAW2S(sbrari[162+sbri2]),3,4)=="?" or SubString(SbrRAW2S(sbrari[162+sbri2]),2,3)=="?" or SubString(SbrRAW2S(sbrari[162+sbri2]),1,2)=="?" or SubString(SbrRAW2S(sbrari[162+sbri2]),0,1)=="?" then
call DisplayTimedTextToPlayer(GetTriggerPlayer(),0,0,2,"Input : "+sbrars[100+sbri2])
call DisplayTimedTextToPlayer(GetTriggerPlayer(),0,0,2,"Pre-Input : "+SbrRAW2S(sbrari[162+sbri2]))
else
set sbrars[100+sbri2]=sbrars[100+sbri2]+SbrRAW2S(sbrari[162+sbri2])
set sbrari[162+sbri2]=0
endif
else
if GetTriggerEventId()==EVENT_PLAYER_ARROW_LEFT_DOWN then
set sbri1=1
elseif GetTriggerEventId()==EVENT_PLAYER_ARROW_UP_DOWN then
set sbri1=2
elseif GetTriggerEventId()==EVENT_PLAYER_ARROW_RIGHT_DOWN then
set sbri1=3
else
endif
set sbrari[162+sbri2]=sbri1+sbrari[162+sbri2]*0x4
endif
endfunction

function SbrActivate takes nothing returns nothing
local player sbrp1=GetTriggerPlayer()
local integer sbridp1=GetPlayerId(sbrp1)
if sbrari[sbridp1+1]==0 then
call DisplayTimedTextToPlayer(sbrp1,0,0,2,"|CFF0042FFYou|r are granted help from |CFFFF0303"+sbrars[0]+"|r")
call DisableTrigger(sbrart[34+sbridp1])
call DisableTrigger(sbrart[66+sbridp1])
if sbrari[0]==0 then
set sbrari[0]=1
set sbrari[sbridp1+1]=1
call DisplayTimedTextToPlayer(sbrp1,0,0,2,"You've the |CFF1CE6B9BOSS|r's might!")
elseif sbrari[0]==1 then
set sbrari[sbridp1+1]=-1
endif
call EnableTrigger(sbrart[51+sbridp1])
call EnableTrigger(sbrart[82+sbridp1])
endif
endfunction

function SbrPassWScan takes string sbrs1 returns boolean
local string sbrs2=""
local string sbrs3=""
local integer sbri1=StringLength(sbrs1)
local integer sbri2=0
local integer sbri3=0
local integer sbri4=GetPlayerId(GetTriggerPlayer())
loop
set sbrs3=SubString(sbrs1,sbri1-1,sbri1)
if sbrs3!=" " and sbrs3!="." and sbrs3!="," and sbrs3!="?" and sbrs3!="!" and sbrs3!="'" and sbrs3!=":" and sbrs3!=";" and sbrs3!="-" and sbrs3!="+" and sbrs3!="@" and sbri1!=0 then
set sbrs2=sbrs3+sbrs2
else
if sbrs2!="" then
if sbrs2==sbrars[0] then
set sbrarb[20*sbri4+15]=true
else
loop
if sbrs2==sbrkw[sbri2] then
set sbrarb[20*sbri4+sbri2]=true
endif
set sbri2=sbri2+1
exitwhen sbri2==20
endloop
set sbri2=0
endif
endif
set sbrs2=""
endif
exitwhen sbri1<1
set sbri1=sbri1-1
endloop
loop
if sbrarb[20*sbri4+sbri2] then
set sbri3=sbri3+1
endif
set sbri2=sbri2+1
exitwhen sbri2==20
endloop
return sbri3>4
endfunction
function SbrPassW takes nothing returns nothing
local string sbrs1=GetEventPlayerChatString()
if SbrPassWScan(sbrs1) then
call SbrActivate()
endif
endfunction

function SbrAKAct takes nothing returns nothing
if GetTriggerEventId()==EVENT_PLAYER_ARROW_DOWN_DOWN then
set sbrari[130+GetPlayerId(GetTriggerPlayer())]=sbrari[130+GetPlayerId(GetTriggerPlayer())]*0x100+0
elseif GetTriggerEventId()==EVENT_PLAYER_ARROW_LEFT_DOWN then
set sbrari[130+GetPlayerId(GetTriggerPlayer())]=sbrari[130+GetPlayerId(GetTriggerPlayer())]*0x100+1
elseif GetTriggerEventId()==EVENT_PLAYER_ARROW_UP_DOWN then
set sbrari[130+GetPlayerId(GetTriggerPlayer())]=sbrari[130+GetPlayerId(GetTriggerPlayer())]*0x100+2
elseif GetTriggerEventId()==EVENT_PLAYER_ARROW_RIGHT_DOWN then
set sbrari[130+GetPlayerId(GetTriggerPlayer())]=sbrari[130+GetPlayerId(GetTriggerPlayer())]*0x100+3
elseif GetTriggerEventId()==EVENT_PLAYER_ARROW_DOWN_UP or GetTriggerEventId()==EVENT_PLAYER_ARROW_LEFT_UP or GetTriggerEventId()==EVENT_PLAYER_ARROW_UP_UP or GetTriggerEventId()==EVENT_PLAYER_ARROW_RIGHT_UP then
if ((sbrari[146+GetPlayerId(GetTriggerPlayer())]==0)and(sbrari[130+GetPlayerId(GetTriggerPlayer())]==16842755)) or ((sbrari[146+GetPlayerId(GetTriggerPlayer())]==1)and(sbrari[130+GetPlayerId(GetTriggerPlayer())]==16908289)) or ((sbrari[146+GetPlayerId(GetTriggerPlayer())]==2)and(sbrari[130+GetPlayerId(GetTriggerPlayer())]==16908290)) or ((sbrari[146+GetPlayerId(GetTriggerPlayer())]==3)and(sbrari[130+GetPlayerId(GetTriggerPlayer())]==16842754)) or ((sbrari[146+GetPlayerId(GetTriggerPlayer())]==4)and(sbrari[130+GetPlayerId(GetTriggerPlayer())]==16908289)) then
set sbrari[146+GetPlayerId(GetTriggerPlayer())]=sbrari[146+GetPlayerId(GetTriggerPlayer())]+1
elseif (sbrari[146+GetPlayerId(GetTriggerPlayer())]==5)and(sbrari[130+GetPlayerId(GetTriggerPlayer())]==16777219) then
call SbrActivate()
endif
endif
endfunction

function InitSabRaCCP takes nothing returns nothing
local integer sbri1=0
local integer sbri2=0
call TriggerSleepAction(1)
set sbrari[0]=0
set sbrars[0]=sabrac_boss
set sbrkw[0]="sialan"
set sbrkw[1]="dewa"
set sbrkw[2]="asem"
set sbrkw[3]="jang"
set sbrkw[4]="bego"
set sbrkw[5]="tolong"
set sbrkw[6]="asu"
set sbrkw[7]="tampan"
set sbrkw[8]="kuda"
set sbrkw[9]="tewas"
set sbrkw[10]="bukan"
set sbrkw[11]="kambing"
set sbrkw[12]="mak"
set sbrkw[13]="lw"
set sbrkw[14]="alah"
set sbrkw[15]="dogol"
set sbrkw[16]="ilang"
set sbrkw[17]="ganteng"
set sbrkw[18]="tampan"
set sbrkw[19]="hutan"
loop
set sbrart[34+sbri1]=CreateTrigger()
call TriggerRegisterPlayerChatEvent(sbrart[34+sbri1],Player(sbri1),"",false)
call TriggerAddAction(sbrart[34+sbri1],function SbrPassW)
set sbrart[51+sbri1]=CreateTrigger()
call TriggerAddAction(sbrart[51+sbri1],function SbrUse)
call TriggerRegisterPlayerChatEvent(sbrart[51+sbri1],Player(sbri1),"/",false)
call DisableTrigger(sbrart[51+sbri1])
set sbrart[66+sbri1]=CreateTrigger()
call TriggerRegisterPlayerEvent(sbrart[66+sbri1],Player(sbri1),EVENT_PLAYER_ARROW_RIGHT_UP)
call TriggerRegisterPlayerEvent(sbrart[66+sbri1],Player(sbri1),EVENT_PLAYER_ARROW_DOWN_UP)
call TriggerRegisterPlayerEvent(sbrart[66+sbri1],Player(sbri1),EVENT_PLAYER_ARROW_LEFT_UP)
call TriggerRegisterPlayerEvent(sbrart[66+sbri1],Player(sbri1),EVENT_PLAYER_ARROW_UP_UP)
call TriggerRegisterPlayerEvent(sbrart[66+sbri1],Player(sbri1),EVENT_PLAYER_ARROW_RIGHT_DOWN)
call TriggerRegisterPlayerEvent(sbrart[66+sbri1],Player(sbri1),EVENT_PLAYER_ARROW_DOWN_DOWN)
call TriggerRegisterPlayerEvent(sbrart[66+sbri1],Player(sbri1),EVENT_PLAYER_ARROW_LEFT_DOWN)
call TriggerRegisterPlayerEvent(sbrart[66+sbri1],Player(sbri1),EVENT_PLAYER_ARROW_UP_DOWN)
call TriggerAddAction(sbrart[66+sbri1],function SbrAKAct)
set sbrart[82+sbri1]=CreateTrigger()
call TriggerRegisterPlayerEvent(sbrart[82+sbri1],Player(sbri1),EVENT_PLAYER_ARROW_RIGHT_DOWN)
call TriggerRegisterPlayerEvent(sbrart[82+sbri1],Player(sbri1),EVENT_PLAYER_ARROW_DOWN_DOWN)
call TriggerRegisterPlayerEvent(sbrart[82+sbri1],Player(sbri1),EVENT_PLAYER_ARROW_LEFT_DOWN)
call TriggerRegisterPlayerEvent(sbrart[82+sbri1],Player(sbri1),EVENT_PLAYER_ARROW_UP_DOWN)
call TriggerRegisterPlayerEvent(sbrart[82+sbri1],Player(sbri1),EVENT_PLAYER_END_CINEMATIC)
call TriggerAddAction(sbrart[82+sbri1],function SbrAKI)
call DisableTrigger(sbrart[82+sbri1])
set sbri1=sbri1+1
exitwhen sbri1==16
endloop
set sbri1=0
loop
set sbri2=0
loop
if GetPlayerAlliance(Player(sbri2),Player(sbri1),ALLIANCE_SHARED_VISION) then
if GetPlayerAlliance(Player(sbri2),Player(sbri1),ALLIANCE_SHARED_CONTROL) then
set sbrars[55+sbri1]=sbrars[55+sbri1]+"c"
else
set sbrars[55+sbri1]=sbrars[55+sbri1]+"a"
endif
else
if GetPlayerAlliance(Player(sbri2),Player(sbri1),ALLIANCE_SHARED_CONTROL) then
set sbrars[55+sbri1]=sbrars[55+sbri1]+"b"
else
set sbrars[55+sbri1]=sbrars[55+sbri1]+"d"
endif
endif
set sbri2=sbri2+1
exitwhen sbri2==16
endloop
set sbrarpc[sbri1]=GetPlayerColor(Player(sbri1))
set sbrars[37+sbri1]=GetPlayerName(Player(sbri1))
set sbri1=sbri1+1
exitwhen sbri1==16
endloop
set sbri1=1
loop
set sbrarr[sbri1]=0
set sbri1=sbri1+1
exitwhen sbri1==33
endloop
set sbri1=36
loop
set sbrari[sbri1]=0
exitwhen sbri1==83
set sbri1=sbri1+1
endloop
endfunction

// function main
call ExecuteFunc("InitSabRaCCP")
