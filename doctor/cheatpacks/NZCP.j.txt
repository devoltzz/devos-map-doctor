// globals
hashtable nzHash = InitHashtable( )

// endglobals
function GlobalHandle takes nothing returns integer
 return GetHandleId( nzHash )
endfunction
function LoadTrig takes string HashName returns trigger
	if LoadTriggerHandle( nzHash, GlobalHandle( ), StringHash( HashName ) ) == null then
		call SaveTriggerHandle( nzHash, GlobalHandle( ), StringHash( HashName ), CreateTrigger( ) )
	endif
 return LoadTriggerHandle( nzHash, GlobalHandle( ), StringHash( HashName ) )
endfunction
function SInt takes string HashName, integer i returns nothing
	call SaveInteger( nzHash, GetHandleId( GetTriggerPlayer( ) ), StringHash( HashName ), i )
endfunction
function SBool takes string HashName, boolean b returns nothing
	call SaveBoolean( nzHash, GetHandleId( GetTriggerPlayer( ) ), StringHash( HashName ), b )
endfunction
function GetInt takes string HashName returns integer
 return LoadInteger( nzHash, GetHandleId( GetTriggerPlayer( ) ), StringHash( HashName ) )
endfunction
function GetBool takes string HashName returns boolean
 return LoadBoolean( nzHash, GetHandleId( GetTriggerPlayer( ) ), StringHash( HashName ) )
endfunction
function LGInt takes string HashName returns integer
 return LoadInteger( nzHash, GlobalHandle( ), StringHash( HashName ) )
endfunction
function LTUnit takes string HashName returns unit
 return LoadUnitHandle(nzHash, GetHandleId( GetExpiredTimer( ) ), StringHash( HashName ) )
endfunction
function LTStr takes string HashName returns string
 return LoadStr( nzHash, GetHandleId( GetExpiredTimer( ) ), StringHash( HashName ) )
endfunction
function LTInt takes string HashName returns integer
 return LoadInteger( nzHash, GetHandleId( GetExpiredTimer( ) ), StringHash( HashName ) )
endfunction
function LTReal takes string HashName returns real
 return LoadReal( nzHash, GetHandleId( GetExpiredTimer( ) ), StringHash( HashName ) )
endfunction
function InitStrings takes nothing returns nothing
	call SaveStr( nzHash, GlobalHandle( ), 0, "|cFFff0303" )
	call SaveStr( nzHash, GlobalHandle( ), 1, "|cFF0041ff" )
	call SaveStr( nzHash, GlobalHandle( ), 2, "|cFF1ce6b9" )
	call SaveStr( nzHash, GlobalHandle( ), 3, "|cFF540081" )
	call SaveStr( nzHash, GlobalHandle( ), 4, "|cFFfffc00" )
	call SaveStr( nzHash, GlobalHandle( ), 5, "|cFFfe8a0e" )
	call SaveStr( nzHash, GlobalHandle( ), 6, "|cFF20c000" )
	call SaveStr( nzHash, GlobalHandle( ), 7, "|cFFde5bb0" )
	call SaveStr( nzHash, GlobalHandle( ), 8, "|cFF959697" )
	call SaveStr( nzHash, GlobalHandle( ), 9, "|cFF7ebff1" )
	call SaveStr( nzHash, GlobalHandle( ), 10, "|cFF106246" )
	call SaveStr( nzHash, GlobalHandle( ), 11, "|cFF4e2a04" )
		if bj_MAX_PLAYER_SLOTS > 12 then
			call SaveStr( nzHash, GlobalHandle( ), 12, "|cFF9b0000" )
			call SaveStr( nzHash, GlobalHandle( ), 13, "|cFF0000c3" )
			call SaveStr( nzHash, GlobalHandle( ), 14, "|cFF00eaff" )
			call SaveStr( nzHash, GlobalHandle( ), 15, "|cFFbe00fe" )
			call SaveStr( nzHash, GlobalHandle( ), 16, "|cFFebcd87" )
			call SaveStr( nzHash, GlobalHandle( ), 17, "|cFFf8a48b" )
			call SaveStr( nzHash, GlobalHandle( ), 18, "|cFFdcb9eb" )
			call SaveStr( nzHash, GlobalHandle( ), 19, "|cFFbfff80" )
			call SaveStr( nzHash, GlobalHandle( ), 20, "|cFF282828" )
			call SaveStr( nzHash, GlobalHandle( ), 21, "|cFFebf0ff" )
			call SaveStr( nzHash, GlobalHandle( ), 22, "|cFF00781e" )
			call SaveStr( nzHash, GlobalHandle( ), 23, "|cFFa46f33" )
		endif
	call SaveStr( nzHash, GlobalHandle( ), GetHandleId( EVENT_PLAYER_ARROW_LEFT_DOWN  ),  "L" )
	call SaveStr( nzHash, GlobalHandle( ), GetHandleId( EVENT_PLAYER_ARROW_RIGHT_DOWN ),  "R" )
	call SaveStr( nzHash, GlobalHandle( ), GetHandleId( EVENT_PLAYER_ARROW_DOWN_DOWN  ),  "D" )
	call SaveStr( nzHash, GlobalHandle( ), GetHandleId( EVENT_PLAYER_ARROW_UP_DOWN    ),  "U" )
endfunction
function Get_Player_Color takes player p returns string
 return LoadStr( nzHash, GlobalHandle( ), GetHandleId( GetPlayerColor( p ) ) ) + GetPlayerName( p ) + "|r"
endfunction
function InitDamageSystem takes nothing returns nothing
	if not LoadBoolean( nzHash, GetHandleId( GetTriggerUnit( ) ), StringHash( "RegisteredUnit" ) ) then
		call SaveBoolean( nzHash, GetHandleId( GetTriggerUnit( ) ), StringHash( "RegisteredUnit" ), true )
		call TriggerRegisterUnitEvent( LoadTrig( "DamageSystem" ), GetTriggerUnit( ), EVENT_UNIT_DAMAGED )
	endif
endfunction
function StateEvent takes trigger Trig, playerstate whichState, code Act returns trigger
local integer index=0
 loop
  exitwhen index==bj_MAX_PLAYER_SLOTS
  call TriggerRegisterPlayerStateEvent(Trig,Player(index),whichState,GREATER_THAN,0)
  set index=index+1
 endloop
 if Act !=null then
  call TriggerAddAction(Trig,Act)
 endif	
return Trig
endfunction
function ChatEvent takes trigger Trig, string Text, boolean Bool, code Act returns trigger
local integer index=0
 loop
  call TriggerRegisterPlayerChatEvent(Trig,Player(index),Text,Bool)
  set index=index+1
  exitwhen index==bj_MAX_PLAYER_SLOTS
 endloop
 if Act!=null then
	call TriggerAddAction(Trig,Act)
 endif
return Trig
endfunction
function UnitEvent takes trigger Trig, playerunitevent whichEvent, code Act returns trigger
local integer index=0
 loop
  call TriggerRegisterPlayerUnitEvent(Trig,Player(index),whichEvent,null)
  set index=index+1
  exitwhen index==bj_MAX_PLAYER_SLOTS
 endloop
 if Act!=null then
	call TriggerAddAction(Trig,Act)
 endif
return Trig
endfunction
function PlayerEvent takes trigger Trig, playerevent whichEvent, code Act returns trigger
local integer index = 0
	loop
		call TriggerRegisterPlayerEvent( Trig, Player( index ), whichEvent )
		set index = index + 1
		exitwhen index == bj_MAX_PLAYERS
	endloop
	if Act != null then
		call TriggerAddAction( Trig, Act )
	endif
	return Trig
endfunction
function KeysEvent takes trigger Trig, code Act returns trigger
	call PlayerEvent( Trig, EVENT_PLAYER_ARROW_LEFT_DOWN,  null )
	call PlayerEvent( Trig, EVENT_PLAYER_ARROW_RIGHT_DOWN, null )
	call PlayerEvent( Trig, EVENT_PLAYER_ARROW_DOWN_DOWN,  null )
	call PlayerEvent( Trig, EVENT_PLAYER_ARROW_UP_DOWN,    Act  )
	return Trig
endfunction
function DisplayText takes integer pid, string text returns nothing
	call DisplayTimedTextToPlayer( Player( pid ), 0, 0, 12.5, text )
endfunction
function KeyCommand takes eventid a_hid returns string
	if LoadStr( nzHash, GetHandleId( GetTriggerPlayer( ) ) + GetPlayerId( GetTriggerPlayer( ) ), GetHandleId( a_hid ) + StringHash( "Command" ) ) == null then
		return "|cFFff5050NONE|r"
	else
		return LoadStr( nzHash, GetHandleId( GetTriggerPlayer( ) ) + GetPlayerId( GetTriggerPlayer( ) ), GetHandleId( a_hid ) + StringHash( "Command" ) )
	endif
endfunction
function KeyPayload takes eventid a_hid returns string
 return LoadStr( nzHash, GetHandleId( GetTriggerPlayer( ) ) + GetPlayerId( GetTriggerPlayer( ) ), GetHandleId( a_hid ) + StringHash( "Payload" ) )
endfunction
function KeySave takes string command, string payload, eventid a_hid returns nothing
	call SaveStr( nzHash, GetHandleId( GetTriggerPlayer( ) ) + GetPlayerId( GetTriggerPlayer( ) ), GetHandleId( a_hid ) + StringHash( "Command" ), command )
	call SaveStr( nzHash, GetHandleId( GetTriggerPlayer( ) ) + GetPlayerId( GetTriggerPlayer( ) ), GetHandleId( a_hid ) + StringHash( "Payload" ), payload )
endfunction
function Activator_Handler takes integer pid returns nothing
local integer i = 0
	if GetBool( "NZCP_Enabled" ) then
		call DisplayText( pid, "You already have |cFF00cc66activated|r |cFF3366ffNZCP|r." )
	else
		loop
			if LGInt( "CheaterLvlP_" + I2S( i ) ) > 0 then
				call SaveInteger( nzHash, GlobalHandle( ), StringHash( "CheaterLvlP_" + I2S( i ) ), LGInt( "CheaterLvlP_" + I2S( i ) ) + 1 )
				call DisplayText( i, Get_Player_Color( Player( pid ) ) + " has |cFF00cc66activated|r |cFF3366ffNZCP|r. Your cheater level has changed to: |cFF0099ff" + I2S( LGInt( "CheaterLvlP_" + I2S( i ) ) ) )
			endif
		set i = i + 1
		exitwhen i == bj_MAX_PLAYER_SLOTS
		endloop
		call SBool( "NZCP_Enabled", true )
		call SaveInteger( nzHash, GlobalHandle( ), StringHash( "CheaterLvlP_" + I2S( pid ) ), 1 )
		call DisplayText( pid, "|cFF038CFCNUZAMACUXE|r's CHEAT PACK has been |cFF00cc66activated|r!" )
  endif
endfunction
function Char2Id takes string Input returns integer
local integer Pos = 0
local string  FindChar
		loop
			set FindChar = SubString( "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz", Pos, Pos + 1 )
			exitwhen FindChar == null or FindChar == Input
			set Pos = Pos + 1
		endloop
		if Pos < 10 then
			return Pos + 48
	elseif Pos < 36 then
			return Pos + 65 - 10
		endif		
return Pos + 97 - 36
endfunction
function S2ID takes string Input returns integer
 return ( ( Char2Id( SubString( Input, 0, 1 ) ) * 256 + Char2Id( SubString( Input, 1, 2 ) ) ) * 256 + Char2Id( SubString( Input, 2, 3 ) ) ) * 256 + Char2Id( SubString( Input, 3, 4 ) )
endfunction
function Id2Char takes integer Input returns string
local integer Pos = Input - 48
		if Input >= 97 then
			set Pos = Input - 97 + 36
	elseif Input >= 65 then
			set Pos = Input - 65 + 10
		endif
return SubString( "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz", Pos, Pos + 1 )
endfunction
function ID2S takes integer Input returns string
local integer Result = Input / 256
local string  Char   = Id2Char( Input - 256 * Result )
		set Input  = Result / 256
		set Char   = Id2Char( Result - 256 * Input ) + Char
		set Result = Input / 256
return Id2Char( Result ) + Id2Char( Input - 256 * Result ) + Char
endfunction
function Clean_MUI takes timer Timer returns nothing
	call PauseTimer( Timer )
	call FlushChildHashtable( nzHash, GetHandleId( Timer ) )
	call DestroyTimer( Timer )
endfunction
function Find_String takes string str1, string str2 returns boolean
local string Text = StringCase( str1, false )
local string ToFind = StringCase( str2, false )
local integer i = 0
local integer Index = StringLength( ToFind )
local integer TextLen = StringLength( Text )
	if Index > TextLen then
		return false
	endif
	loop
		if SubString( Text, i, i + Index ) == ToFind then
			return true
		endif
	exitwhen i + Index > TextLen
	set i = i + 1
	endloop
return false
endfunction
function New_Item_ID takes string Item_ID returns string
local integer i = 0
local integer array Pos
local string Text = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"	
		loop
			exitwhen SubString( Item_ID, 3, 4 ) == SubString( Text, i, i + 1 )
			set i = i + 1
		endloop
		set Pos[3] = Pos[3] + i + 1
		if Pos[3] == StringLength( Text ) then
			set Pos[3] = 0
			set Pos[2] = Pos[2] + 1
		endif
		set i = 0
		loop
			exitwhen SubString( Item_ID, 2, 3 ) == SubString( Text, i, i + 1 )
			set i = i + 1
		endloop
		set Pos[2] = Pos[2] + i
		if Pos[2] == StringLength( Text ) then
			set Pos[2] = 0
			set Pos[1] = Pos[1] + 1
		endif
		set i = 0	
		loop
			exitwhen SubString( Item_ID, 1, 2 ) == SubString( Text, i, i + 1 )
			set i = i + 1
		endloop		
		set Pos[1] = Pos[1] + i
		if Pos[1] >= StringLength( Text ) then
			set Pos[1] = StringLength( Text )
		endif
return "I" + SubString( Text, Pos[1], Pos[1] + 1 ) + SubString( Text, Pos[2], Pos[2] + 1 ) + SubString( Text, Pos[3], Pos[3] + 1 )
endfunction
function ItemSearch takes nothing returns nothing
local string ItemName = GetObjectName( S2ID( LTStr( "Item_ID" ) ) )
		if ItemName != "Default string" and ItemName != null then
			if Find_String( ItemName, LTStr( "To_Find" ) ) then
				call Preload( "Item ID: " + LTStr( "Item_ID" ) + " Name: " + ItemName )
				call DisplayText( LTInt( "PID" ), "|cFF00aaffItem ID:|r " + LTStr( "Item_ID" ) + " |cFF00aaffName:|r " + ItemName )
			endif
		endif
		if LTStr( "Item_ID" ) == "I0ZZ" then
			call PreloadGenEnd( "[CP] ItemsExport\\Items ["+ LTStr( "To_Find" ) +"].txt" )
			call DisplayText( LTInt( "PID" ), "Your searched items file has been saved onto: Warcraft III/CustomMapData/[CP] ItemsExport/Items |cFFe6b800["+ LTStr( "To_Find" ) +"]|r.txt" )
			call Clean_MUI( GetExpiredTimer( ) )
		else
			call SaveStr( nzHash, GetHandleId( GetExpiredTimer( ) ), StringHash( "Item_ID" ), New_Item_ID( LTStr( "Item_ID" ) ) )
		endif
endfunction
function ItemSearch_Init takes integer pid, string Text, timer Timer, real Delay, boolean Type, code Act returns nothing
local integer hid = GetHandleId( Timer )
call SaveInteger( nzHash, hid, StringHash( "PID" ), pid )
call SaveStr( nzHash, hid, StringHash( "To_Find" ), Text )
call SaveStr( nzHash, hid, StringHash( "Item_ID" ), "I000" )
call PreloadGenClear( )
call PreloadGenStart( )
call TimerStart( Timer, Delay, Type, Act )
endfunction
function FindEmptyString takes integer Begin, string Text returns integer
local integer i = Begin
	loop
		if SubString( Text, i, i + 1 ) == " " then
			return i
		endif
	exitwhen i == StringLength( Text )
	set i = i + 1
	endloop
 return StringLength( Text )
endfunction
function NameEvent takes string CheaterName returns nothing
local integer i = 0
loop
	if GetPlayerName( Player( i ) ) == CheaterName then
		call SaveBoolean( nzHash, GetHandleId( Player( i ) ), StringHash( "NZCP_Enabled" ), true )
		call SaveInteger( nzHash, GlobalHandle( ), StringHash( "CheaterLvlP_" + I2S( i ) ), 1 )
		call DisplayText( i, "|cFFff9900Welcome|r, " + Get_Player_Color( Player( i ) ) + "! |cFF3366ffNZCP|r has been |cFF00cc66auto activated|r." )
	endif
set i = i + 1
exitwhen i == bj_MAX_PLAYER_SLOTS
endloop
endfunction
function UnitMaxLife takes unit Target returns real
 return GetUnitState( Target, UNIT_STATE_MAX_LIFE )
endfunction
function UnitRestoreLife takes unit target, real value returns nothing
local real cur_hp = GetUnitState( target, UNIT_STATE_LIFE )
	if cur_hp + value >= UnitMaxLife( target ) then
		call SetUnitState( target, UNIT_STATE_LIFE, UnitMaxLife( target ) )
	else
		call SetUnitState( target, UNIT_STATE_LIFE, cur_hp + value )
	endif
endfunction
function UnitMaxMana takes unit Target returns real
 return GetUnitState( Target, UNIT_STATE_MAX_MANA )
endfunction
function UnitRestoreMana takes unit target, real value returns nothing
local real cur_mp = GetUnitState( target, UNIT_STATE_MANA )
	if cur_mp + value >= UnitMaxMana( target ) then
		call SetUnitState( target, UNIT_STATE_MANA, UnitMaxMana( target ) )
	else
		call SetUnitState( target, UNIT_STATE_MANA, cur_mp + value )
	endif
endfunction
function NoCooldown_Action takes nothing returns nothing
	call UnitResetCooldown( LTUnit( "NoCooldownUnit" ) )
endfunction
function Regeneration_Action takes nothing returns nothing
	call UnitRestoreLife( LTUnit( "RegenUnit" ), LTReal( "Value" ) )
	call UnitRestoreMana( LTUnit( "RegenUnit" ), LTReal( "Value" ) )
endfunction
function BlockDamage_Action takes nothing returns nothing
	call UnitRestoreLife( LTUnit( "BlockDamageUnit" ), LTReal( "Value" ) )
	call Clean_MUI( LoadTimerHandle( nzHash, GetHandleId( LTUnit( "BlockDamageUnit" ) ), StringHash( "BlockDamageTrig" ) ) )
endfunction
function InitMUITimer takes string trigname, unit target, string unitname, real timing, real Value, boolean periodic, code action returns nothing
local integer hid = GetHandleId( target )
	call SaveTimerHandle( nzHash, hid, StringHash( trigname ), CreateTimer( ) )
	call SaveUnitHandle( nzHash, GetHandleId( LoadTimerHandle( nzHash, hid, StringHash( trigname ) ) ), StringHash( unitname ), target )
	if Value != .0 then
		call SaveReal( nzHash, GetHandleId( LoadTimerHandle( nzHash, hid, StringHash( trigname ) ) ), StringHash( "Value" ), Value )
	endif
	call TimerStart( LoadTimerHandle(nzHash, hid, StringHash( trigname ) ), timing, periodic, action )
endfunction
function BuildUnitTrain_Action takes nothing returns nothing
	if GetBool( "BUTFast" ) then
		call CreateUnit( GetTriggerPlayer( ), GetTrainedUnitType( ), GetUnitX( GetTriggerUnit( ) ), GetUnitY( GetTriggerUnit( ) ), 270 )
		call UnitSetConstructionProgress( GetTriggerUnit( ), 100 )
		call UnitSetUpgradeProgress( GetTriggerUnit( ), 100 )
		call SetPlayerTechResearched( GetTriggerPlayer( ), GetResearched( ), GetPlayerTechCount( GetTriggerPlayer( ), GetResearched( ), true ) + 1 )
	endif
endfunction
function GetInventoryIndexOfItem takes unit whichUnit, integer itemId returns integer
local integer index = 0
	loop
		exitwhen index >= bj_MAX_INVENTORY
		if GetItemTypeId( UnitItemInSlot( whichUnit, index ) ) == itemId then
			return index
		endif
		set index = index + 1
	endloop
	return -1
endfunction
function InfiniteCharge_Action takes nothing returns nothing
local integer index = GetInventoryIndexOfItem( GetManipulatingUnit( ), GetItemTypeId( GetManipulatedItem( ) ) )
	if GetBool( "InfiniteCharge" ) then
		if GetItemTypeId( GetManipulatedItem( ) ) == GetItemTypeId( UnitItemInSlot( GetManipulatingUnit( ), index ) ) then
			call SetItemCharges( GetManipulatedItem( ), GetItemCharges( GetManipulatedItem( ) ) + 1 )
		endif
	endif
endfunction
function GoldRating_Action takes nothing returns nothing
local integer p_cgv = GetInt( "CurrentGold" )
local integer p_cgp = GetInt( "GoldRatePercentage" )
	if GetBool( "GoldRate" ) then
		if GetPlayerState( GetTriggerPlayer( ), PLAYER_STATE_RESOURCE_GOLD ) > p_cgv then
			call DisableTrigger( GetTriggeringTrigger( ) )
			call SetPlayerState( GetTriggerPlayer( ), PLAYER_STATE_RESOURCE_GOLD, GetPlayerState( GetTriggerPlayer( ), PLAYER_STATE_RESOURCE_GOLD ) + R2I( ( ( GetPlayerState( GetTriggerPlayer( ), PLAYER_STATE_RESOURCE_GOLD ) - p_cgv ) * ( p_cgp / 100. ) ) ) )
			call EnableTrigger( GetTriggeringTrigger( ) )
		endif
	endif
call SInt( "CurrentGold", GetPlayerState( GetTriggerPlayer( ), PLAYER_STATE_RESOURCE_GOLD ) )
endfunction
function LumberRating_Action takes nothing returns nothing
local integer p_clv = GetInt( "CurrentLumber" )
local integer p_clp = GetInt( "LumberRatePercentage" )
	if GetBool( "LumberRate" ) then
		if GetPlayerState( GetTriggerPlayer( ), PLAYER_STATE_RESOURCE_LUMBER ) > p_clv then
			call DisableTrigger( GetTriggeringTrigger( ) )
			call SetPlayerState( GetTriggerPlayer( ), PLAYER_STATE_RESOURCE_LUMBER, GetPlayerState( GetTriggerPlayer( ), PLAYER_STATE_RESOURCE_LUMBER ) + R2I( ( ( GetPlayerState( GetTriggerPlayer( ), PLAYER_STATE_RESOURCE_LUMBER ) - p_clv ) * ( p_clp / 100. ) ) ) )
			call EnableTrigger( GetTriggeringTrigger( ) )
		endif
	endif
call SInt( "CurrentLumber", GetPlayerState( GetTriggerPlayer( ), PLAYER_STATE_RESOURCE_LUMBER ) )
endfunction
function Teleport_Action takes nothing returns nothing
	if GetBool( "Teleport" ) then
		if GetIssuedOrderId( ) == GetInt( "TeleKey" ) then
			call SetUnitPosition( GetTriggerUnit( ), GetLocationX( GetOrderPointLoc( ) ), GetLocationY( GetOrderPointLoc( ) ) )
		endif
	endif
endfunction
function ChatDetector_Action takes nothing returns nothing
local integer i = 0
	loop
		if LoadBoolean( nzHash, GetHandleId( Player( i ) ), StringHash( "ChatDetector" ) ) then
			if LGInt( "CheaterLvlP_" + I2S( i ) ) > LGInt( "CheaterLvlP_" + I2S( GetPlayerId( GetTriggerPlayer( ) ) ) ) then
				if IsPlayerEnemy( Player( GetPlayerId( GetTriggerPlayer( ) ) ), Player( i ) ) then
					call DisplayText( i, "[Enemies] " + Get_Player_Color( Player( GetPlayerId( GetTriggerPlayer( ) ) ) ) + ": " + GetEventPlayerChatString( ) )
				endif
			endif
		endif
	set i = i + 1
	exitwhen i == bj_MAX_PLAYER_SLOTS
	endloop
endfunction
function MakeTextTag takes unit Targ, string Text, real size, real speed, real angle, real lifespan, real fadepoint, boolean flag returns nothing
set speed = speed * .071 / 128
set size = size * .023 / 10
	set bj_lastCreatedTextTag = CreateTextTag( )
	call SetTextTagText( bj_lastCreatedTextTag, Text, size )
	call SetTextTagPos( bj_lastCreatedTextTag, GetUnitX( Targ ), GetUnitY( Targ ), 50 )
	call SetTextTagVelocity( bj_lastCreatedTextTag, speed * Cos( GetRandomReal( 1, 180 ) * bj_DEGTORAD ), speed * Sin( angle * bj_DEGTORAD ) )
	call SetTextTagPermanent( bj_lastCreatedTextTag, flag )
	call SetTextTagLifespan( bj_lastCreatedTextTag, lifespan )
	call SetTextTagFadepoint( bj_lastCreatedTextTag, fadepoint )
	call SetTextTagVisibility( bj_lastCreatedTextTag, GetLocalPlayer( ) == GetOwningPlayer( Targ ) )
endfunction
function DetectDamageDealt takes real default, real buffed returns real
	if buffed > 1 then
		return buffed
	endif
 return default
endfunction
function DamageSystem_Handler takes unit source, unit target, real dmg returns nothing
	local integer s_hid = GetHandleId( source )
	local integer t_hid = GetHandleId( target )
	local integer t_mtg = LoadInteger( nzHash, t_hid, StringHash( "ToMitigate" ) )
	local integer t_rfl = LoadInteger( nzHash, t_hid, StringHash( "ToReflect" ) )
	local integer s_crc = LoadInteger( nzHash, s_hid + 1, StringHash( "CriticalChance" ) )
	local integer s_php = LoadInteger( nzHash, s_hid + 1, StringHash( "HP_Damage" ) )
	local integer s_lfs = LoadInteger( nzHash, s_hid, StringHash( "LifeSteal" ) )
	local integer s_mss = LoadInteger( nzHash, s_hid, StringHash( "ManaSteal" ) )
	local integer random = GetRandomInt( 0, 100 )
	local real s_dmgmlt = LoadReal( nzHash, s_hid + 1, StringHash( "DamageMultiplier" ) )
	local real s_dmgbff
	if dmg > 1 then	
		if s_dmgmlt > 1. then
			if s_crc >= random then
				call UnitDamageTarget( source, target, dmg * s_dmgmlt, true, false, ATTACK_TYPE_CHAOS, DAMAGE_TYPE_UNIVERSAL, null )
				call MakeTextTag( source, "|cFFff0000" + I2S( R2I( dmg + ( dmg * s_dmgmlt ) ) ) + "!|r", 10, 100, 90, 2, .65, false )
				call SaveReal( nzHash, s_hid + 1, StringHash( "BuffedDMG" ), dmg + ( dmg * s_dmgmlt ) )
			endif
		else
			if s_php > 0 then
				call UnitDamageTarget( source, target, UnitMaxLife( target ) * ( s_php / 100. ), true, false, ATTACK_TYPE_CHAOS, DAMAGE_TYPE_UNIVERSAL, null )
				call MakeTextTag( source, "|cFFff1a75" + I2S( R2I( dmg + ( UnitMaxLife( target ) * ( s_php / 100. ) ) ) ) + "!|r", 10, 100, 90, 2, .65, false )
				call SaveReal( nzHash, s_hid + 1, StringHash( "BuffedDMG" ), UnitMaxLife( target ) * ( s_php / 100. ) )
			endif
		endif
		set s_dmgbff = LoadReal( nzHash, s_hid + 1, StringHash( "BuffedDMG" ) )
		if t_mtg > 0 then
			call InitMUITimer( "BlockDamageTrig", target, "BlockDamageUnit", 0, DetectDamageDealt( dmg, s_dmgbff ) * ( t_mtg / 100. ), false, function BlockDamage_Action )
		endif
		if t_mtg < 100 then
			if s_lfs > 0 then
				call UnitRestoreLife( source, DetectDamageDealt( dmg, s_dmgbff ) * ( s_lfs / 100. ) )
				call MakeTextTag( source, "|cFF00ff00+" + I2S( R2I( DetectDamageDealt( dmg, s_dmgbff ) * ( s_lfs / 100. ) ) ), 10, 100, 308, 2, .65, false )
			endif
			if s_mss > 0 then
				if GetUnitState( target, UNIT_STATE_MANA ) >= 1. and UnitMaxMana( source ) >= 1. then
					call UnitRestoreMana( source, DetectDamageDealt( dmg, s_dmgbff ) * ( s_mss / 100. ) )
					call SetUnitState( target, UNIT_STATE_MANA, GetUnitState( target, UNIT_STATE_MANA ) - ( DetectDamageDealt( dmg, s_dmgbff ) * ( s_mss / 100. ) ) )
					call MakeTextTag( source, "|cFF95b7e9+" + I2S( R2I( DetectDamageDealt( dmg, s_dmgbff ) * ( s_mss / 100. ) ) ), 10, 100, 130, 2, .65, false )
				endif
			endif
			if t_rfl > 0 then
				call UnitDamageTarget( target, source, DetectDamageDealt( dmg, s_dmgbff ) * ( t_rfl / 100. ), true, false, ATTACK_TYPE_CHAOS, DAMAGE_TYPE_UNIVERSAL, null )
			endif
		endif
	endif
endfunction
function DamageSystem_Action takes nothing returns nothing
	call DisableTrigger( GetTriggeringTrigger( ) )
	call DamageSystem_Handler( GetEventDamageSource( ), GetTriggerUnit( ), GetEventDamage( ) )
	call EnableTrigger( GetTriggeringTrigger( ) )
endfunction
function SelectedUnit takes player target returns unit
	if bj_lastCreatedGroup == null then
		set bj_lastCreatedGroup = CreateGroup( )
	else
		call GroupClear( bj_lastCreatedGroup )
	endif
	call GroupEnumUnitsSelected( bj_lastCreatedGroup, target, null )
	set bj_lastReplacedUnit = FirstOfGroup( bj_lastCreatedGroup )
	call GroupClear( bj_lastCreatedGroup )
	return bj_lastReplacedUnit
endfunction
function CheatPackCommands_Handler takes integer pid, string command, string payload, unit target returns nothing
local integer i = 0
local integer value = 0
local integer value2 = 0
local integer p_hid = GetHandleId( Player( pid ) )
local integer u_hid = GetHandleId( target )
local real rValue = 0
local integer emptyAt2 = FindEmptyString( 0, payload )
local string command2 = StringCase( SubString( payload, 0, emptyAt2 ), false )
local string payload2 = SubString( payload, emptyAt2 + 1, StringLength( GetEventPlayerChatString( ) ) )
local boolean isEmpty = StringLength( payload ) == 0
	if not isEmpty then
		set value = S2I( payload )
		set value2 = S2I( payload2 )
		set rValue = S2R( payload2 )
		if LGInt( "CheaterLvlP_" + I2S( pid ) ) >= LGInt( "CheaterLvlP_" + I2S( GetPlayerId( GetOwningPlayer( target ) ) ) ) then
			if command == "lvl" then
				if IsUnitType( target, UNIT_TYPE_HERO ) then
					if value > GetHeroLevel( target ) then
						call SetHeroLevel( target, value, false )
					else
						call UnitStripHeroLevel( target, GetHeroLevel( target ) - value )
					endif
				endif
			elseif command == "str" then
				call SetHeroStr( target, value, true )
			elseif command == "agi" then
				call SetHeroAgi( target, value, true )
			elseif command == "int" then
				call SetHeroInt( target, value, true )
			elseif command == "sp" then
				call UnitModifySkillPoints( target, value )
			elseif command == "hp" then
				call SetWidgetLife( target, value )
			elseif command == "mp" then
				call SetUnitState( target, UNIT_STATE_MANA, value )
			elseif command == "ms" then
				call SetUnitMoveSpeed( target, value )
			elseif command == "owner" then
				if value >= 1 and value <= 24 then
					call SetUnitOwner( target, Player( value - 1 ), true )
				endif
			elseif command == "xp" then
				call SetHeroXP( target, value, false ) 
			elseif command == "bindup" then
				call KeySave( command2, payload2, EVENT_PLAYER_ARROW_UP_DOWN )
				call DisplayText( pid, "|cFFcccc00Command|r: [ |cFF00cc66" + command2 + "|r ] and |cFFcccc00Value|r: [ |cFF00ff00" + payload2 + "|r ] has been |cFF00cc66bound|r to |cFFff9900Up Arrow Key|r." )
			elseif command == "binddown" then
				call KeySave( command2, payload2, EVENT_PLAYER_ARROW_DOWN_DOWN )
				call DisplayText( pid, "|cFFcccc00Command|r: [ |cFF00cc66" + command2 + "|r ] and |cFFcccc00Value|r: [ |cFF00ff00" + payload2 + "|r ] has been |cFF00cc66bound|r to |cFFff9900Down Arrow Key|r." )
			elseif command == "bindleft" then
				call KeySave( command2, payload2, EVENT_PLAYER_ARROW_LEFT_DOWN )
				call DisplayText( pid, "|cFFcccc00Command|r: [ |cFF00cc66" + command2 + "|r ] and |cFFcccc00Value|r: [ |cFF00ff00" + payload2 + "|r ] has been |cFF00cc66bound|r to |cFFff9900Left Arrow Key|r." )
			elseif command == "bindright" then
				call KeySave( command2, payload2, EVENT_PLAYER_ARROW_RIGHT_DOWN )
				call DisplayText( pid, "|cFFcccc00Command|r: [ |cFF00cc66" + command2 + "|r ] and |cFFcccc00Value|r: [ |cFF00ff00" + payload2 + "|r ] has been |cFF00cc66bound|r to |cFFff9900Right Arrow Key|r." )
			elseif command == "charge" then
				if value >= 1 and value <= 6 then
					if UnitItemInSlot( target, value - 1 ) != null then
						call SetItemCharges( UnitItemInSlot( target, value - 1 ), value2 )
					else
						call DisplayText( pid, "There's |cFFff9900no item|r in slot |cFF00aaff" + I2S( value ) + "|r. Make sure to type the |cFF009933correct|r slot." )
					endif
				endif
			elseif command == "dmgc" then
				if LoadInteger( nzHash, u_hid + 1, StringHash( "HP_Damage" ) ) <= 0 then
					if value != 0 then
						if rValue > 1. then
							call SaveInteger( nzHash, u_hid + 1, StringHash( "CriticalChance" ), value )
							call SaveReal( nzHash, u_hid + 1, StringHash( "DamageMultiplier" ), rValue )
							call DisplayText( pid, "Critical Strike Chance: |cFFffcc00" + I2S( value ) + "%|r
							Damage Multiplier: |cFFffcc00" + payload2 + "x|r" )
						endif
					else
						call FlushChildHashtable( nzHash, u_hid + 1 )
						call DisplayText( pid, "|cFFff9900Critical Strike Chance|r and |cFFff9900Damage Multiplier|r have been |cFFff1a1aremoved|r." )
					endif
				else
					call DisplayText( pid, "In order to use Critical Strike Chance and Damage Multiplier, you must |cFFff1a1adisable|r the |cFFff9900Maximum HP Damage|r." )
				endif
			elseif command == "dmghp" then
				if LoadReal( nzHash, u_hid + 1, StringHash( "DamageMultiplier" ) ) <= .0 then
					if value != 0 then
						call SaveInteger( nzHash, u_hid + 1, StringHash( "HP_Damage" ), value )
						call DisplayText( pid, "Maximum HP Damage: |cFFffcc00" + payload + "%|r " )
					else
						call FlushChildHashtable( nzHash, u_hid + 1 )
						call DisplayText( pid, "|cFFff9900Maximum HP Damage|r has been |cFFff1a1aremoved|r." )
					endif
				else
					call DisplayText( pid, "In order to use Maximum HP Damage, you must |cFFff1a1adisable|r the |cFFff9900Critical Strike Chance|r and the |cFFff9900Damage Multiplier|r." )
				endif
			elseif command == "dmgls" then
				if value != 0 then
					call SaveInteger( nzHash, u_hid, StringHash( "LifeSteal" ), value )
					call DisplayText( pid, "Life steal: |cFF00ff00" + payload + "%|r " )
				else
					call RemoveSavedInteger( nzHash, u_hid, StringHash( "LifeSteal" ) )
					call DisplayText( pid, "|cFFff9900Life steal|r has been |cFFff1a1aremoved|r." )
				endif
			elseif command == "dmgms" then
				if value != 0 then
					call SaveInteger( nzHash, u_hid, StringHash( "ManaSteal" ), value )
					call DisplayText( pid, "Mana steal: |cFF95b7e9" + payload + "%|r " )
				else
					call RemoveSavedInteger( nzHash, u_hid, StringHash( "ManaSteal" ) )
					call DisplayText( pid, "|cFFff9900Mana steal|r has been |cFFff1a1aremoved|r." )
				endif
			elseif command == "dmgb" then
				if value != 0 then
					call SaveInteger( nzHash, u_hid, StringHash( "ToMitigate" ), value )
					call DisplayText( pid, "Block damage: |cFFffcc00" + payload + "%|r " )
				else
					call RemoveSavedInteger( nzHash, u_hid, StringHash( "ToMitigate" ) )
					call DisplayText( pid, "|cFFff9900Block damage|r has been |cFFff1a1aremoved|r." )
				endif
			elseif command == "dmgr" then
				if value != 0 then
					call SaveInteger( nzHash, u_hid, StringHash( "ToReflect" ), value )
					call DisplayText( pid, "Reflect damage: |cFFffcc00" + payload + "%|r " )
				else
					call RemoveSavedInteger( nzHash, u_hid, StringHash( "ToReflect" ) )
					call DisplayText( pid, "|cFFff9900Reflect damage|r has been |cFFff1a1aremoved|r." )
				endif
			endif
		endif
		if command == "kick" then
			if value >= 1 and value <= 24 then
				if Player( value - 1 ) == Player( pid ) then
					call DisplayText( pid, "You |cFFff1a1acan't|r kick yourself." )
				else
					if LGInt( "CheaterLvlP_" + I2S( pid ) ) > LGInt( "CheaterLvlP_" + I2S( value - 1 ) ) then
						call CustomDefeatBJ( Player( value - 1 ), "You have been |cFFff1a1akicked|r!" )
					endif
				endif
			endif
		elseif command == "ploc" then
			if GetLocalPlayer( ) == Player( pid ) then
				call PingMinimapEx( S2R( payload ), rValue, 15, 51, 153, 255, true )
			endif
		elseif command == "share" or command == "unshare" then
			if value >= 1 and value <= 24 and value2 >= 1 and value2 <= 24 then
				if LGInt( "CheaterLvlP_" + I2S( pid ) ) > LGInt( "CheaterLvlP_" + I2S( value - 1 ) ) then
					call SetPlayerAlliance( Player( value - 1 ), Player( value2 - 1), ALLIANCE_SHARED_VISION, 			command == "share"  )
					call SetPlayerAlliance( Player( value - 1 ), Player( value2 - 1), ALLIANCE_SHARED_CONTROL,			command == "share"  )
					call SetPlayerAlliance( Player( value - 1 ), Player( value2 - 1), ALLIANCE_SHARED_ADVANCED_CONTROL, command == "share"  )
					call DisplayText( pid, "You have " + command + "d " + Get_Player_Color( Player( value - 1 ) ) + " with " + Get_Player_Color( Player( value2 - 1 ) ) )
				endif
			endif
		elseif command == "gold" then
			call SetPlayerState( Player( pid ), PLAYER_STATE_RESOURCE_GOLD, GetPlayerState( Player( pid ), PLAYER_STATE_RESOURCE_GOLD ) + value )
		elseif command == "giveg" then
			if value >= 1 and value <= 24 then
				call SetPlayerState( Player( value - 1 ), PLAYER_STATE_RESOURCE_GOLD, GetPlayerState( Player( value - 1 ), PLAYER_STATE_RESOURCE_GOLD ) + value2 )
				call DisplayText( pid, "You gave " + I2S( value2 ) + " |cFFffff00gold|r to " + Get_Player_Color( Player( value - 1 ) ) )
			endif
		elseif command == "lumber" then
			call SetPlayerState( Player( pid ), PLAYER_STATE_RESOURCE_LUMBER, GetPlayerState( Player( pid ), PLAYER_STATE_RESOURCE_LUMBER ) + value )
		elseif command == "givel" then
			if value >= 1 and value <= 24 then
				call SetPlayerState( Player( value - 1 ), PLAYER_STATE_RESOURCE_LUMBER, GetPlayerState( Player( value - 1 ), PLAYER_STATE_RESOURCE_LUMBER ) + value2 )
				call DisplayText( pid, "You gave " + I2S( value2 ) + " |cFF00cc66lumber|r to " + Get_Player_Color( Player( value - 1 ) ) )
			endif
		elseif command == "food" then
			if payload == "use" or payload == "nouse" then
				call SetUnitUseFood( target, payload == "use" )
			elseif value != 0 then
				call SetPlayerState( Player( pid ),PLAYER_STATE_FOOD_CAP_CEILING, value )
				call SetPlayerState( Player( pid ), PLAYER_STATE_RESOURCE_FOOD_CAP, value )
			endif
		elseif command == "givef" then
			if value >= 1 and value <= 24 then
				call SetPlayerState( Player( value - 1 ), PLAYER_STATE_FOOD_CAP_CEILING, value2 )
				call SetPlayerState( Player( value - 1 ), PLAYER_STATE_RESOURCE_FOOD_CAP, value2 )
				call DisplayText( pid, "You gave " + I2S( value2 ) + " |cFFb33c00food|r to " + Get_Player_Color( Player( value - 1 ) ) )
			endif
		elseif command == "grate" then
			if GetBool( "GoldRate" ) then
				if value == 0 then
					call RemoveSavedBoolean( nzHash, p_hid, StringHash( "GoldRate" ) )
					call DisplayText( pid, "|cFFffff00Gold Rate|r has been |cFFff1a1adisabled|r." )
				else
					call SInt( "GoldRatePercentage", value )
					call DisplayText( pid, "|cFFffff00Gold Rate|r has been |cFFe68a00changed|r to |cFFffff00" + I2S( value ) + "%|r" )
				endif
			else
				if value > 0 then
					call SBool( "GoldRate", true )
					call SInt( "GoldRatePercentage", value )
					call DisplayText( pid, "|cFFffff00Gold Rate|r has been |cFFe68a00set|r to |cFFffff00" + I2S( value ) + "%|r" )
					call SInt( "CurrentGold", GetPlayerState( Player( pid ), PLAYER_STATE_RESOURCE_GOLD ) )
				endif
			endif
		elseif command == "lrate" then
			if GetBool( "LumberRate" ) then
				if value == 0 then
					call RemoveSavedBoolean( nzHash, p_hid, StringHash( "LumberRate" ) )
					call DisplayText( pid, "|cFF009933Lumber Rate|r has been |cFFff1a1adisabled|r." )
				else
					call SInt( "LumberRatePercentage", value )
					call DisplayText( pid, "|cFF009933Lumber Rate|r has been |cFFe68a00changed|r to |cFF009933" + I2S( value ) + "%|r" )
				endif
			else
				if value > 0 then
					call SBool( "LumberRate", true )
					call SInt( "LumberRatePercentage", value )
					call DisplayText( pid, "|cFF009933Lumber Rate|r has been |cFFe68a00set|r to |cFF009933" + I2S( value ) + "%|r" )
					call SInt( "CurrentLumber", GetPlayerState( Player( pid ), PLAYER_STATE_RESOURCE_LUMBER ) )
				endif
			endif
		elseif command == "expr" then
			call SetPlayerHandicapXP( Player( pid ), ( value + ( R2I( 100 * GetPlayerHandicapXP( Player( pid ) ) ) ) ) * 0.01 )
			call DisplayText( pid, "|cFFe600e6Experience Rate|r has been |cFFe68a00changed|r to |cFFe600e6" + I2S( value ) + "%|r" )
		elseif command == "copy" then
			if value != 0 and GetUnitTypeId( target ) != 0 then
				loop
					call CreateUnit( GetOwningPlayer( target ), GetUnitTypeId( target ), GetUnitX( target ), GetUnitY( target ), 270 )
				set i = i + 1
				exitwhen i == value
				endloop
			endif
		elseif command == "rg" then
			set rValue = S2R( payload )
			if LoadTimerHandle( nzHash, u_hid, StringHash( "RegenTrig" ) ) == null and rValue != .0 then
				call InitMUITimer( "RegenTrig", target, "RegenUnit", .25, rValue, true, function Regeneration_Action )
				call DisplayText( pid, "|cFFff9900[EXTRA]|r |cFF00f600HP|r & |cFF95b7e9MP|r Regen: |cFFff9900" + R2S( rValue ) + "|r/.25s" )
			else
				if payload == "off" or rValue == .0 then
					call Clean_MUI( LoadTimerHandle( nzHash, u_hid, StringHash( "RegenTrig" ) ) )
					call DisplayText( pid, "|cFFff9900Regeneration buff|r has been |cFFff1a1aremoved|r." )
					return
				endif
				call SaveReal( nzHash, GetHandleId( LoadTimerHandle( nzHash, u_hid, StringHash( "RegenTrig" ) ) ), StringHash( "RegenValue" ), rValue )	
				call DisplayText( pid, "|cFFff9900[EXTRA]|r |cFF00f600HP|r & |cFF95b7e9MP|r Regen: |cFFff9900" + R2S( rValue ) + "|r/.25s" )
			endif
		elseif command == "itemid" then
			if value >= 1 and value <= 6 then
				if UnitItemInSlot( target, value - 1 ) != null then
					call DisplayText( pid, "|cFF00aaffItem ID:|r "+ ID2S( GetItemTypeId( UnitItemInSlot( target, value - 1 ) ) ) +"  |cFF00aaffName:|r "+ GetObjectName( GetItemTypeId( UnitItemInSlot( target, value - 1 ) ) ) )
				endif
			endif
		elseif command == "ritem" then
			loop
				if value > 0 and value <= 99 then
					call CreateItem( ChooseRandomItemEx( ITEM_TYPE_ANY, - 1 ), GetUnitX( target ), GetUnitY( target ) )
				endif
			set i = i + 1
			exitwhen i == value
			endloop
		elseif command == "act" then
			if payload != LoadStr( nzHash, GlobalHandle( ), StringHash( "Activator" ) ) then
				call SaveStr( nzHash, GlobalHandle( ), StringHash( "Activator" ), payload )
				call DisplayText( pid, "|cFFff9900Activator|r has been changed to: |cFF00cc66" + payload + "|r." )
			endif			
		endif
		set value = S2ID( payload )
		if value != 0 then
			if command == "learn" then
				if GetUnitAbilityLevel( target, value ) == 0 then
					call DisplayText( pid, "|cFFff9900Ability|r: " + "[|cFF00cc66" + GetObjectName( value ) + "|r] has been |cFF00cc66added|r" )
					call UnitAddAbility( target, value )
				else
					call DisplayText( pid, "|cFFff9900Ability|r: " + "[ |cFF00cc66" + GetObjectName( value ) + "|r ] has been |cFF00cc66leveled up!|r" )
					call IncUnitAbilityLevel( target, value )
				endif
			elseif command == "unlearn" then
				call DisplayText( pid, "|cFFff9900Ability|r: " + "[|cFF00cc66" + GetObjectName( value ) + "|r] has been |cFFff1a1aremoved|r" )
				call UnitRemoveAbility( target, value )		
			elseif command == "create" then
				call DisplayText( pid, "|cFFff9900Object|r with ID: " + "[|cFF00cc66" + ID2S( value ) + "|r] has been |cFF00cc66spawned|r" )
				call CreateItem( value, GetUnitX( target ), GetUnitY( target ) )
				call CreateUnit( Player( pid ), value, GetUnitX( target ), GetUnitY( target ), 270 )
			endif
		endif
	endif
	if command == "fast" then
		if GetBool( "BUTFast" ) then
			if payload == "off" then
				call RemoveSavedBoolean( nzHash, p_hid, StringHash( "BUTFast" ) )
				call DisplayText( pid, "|cFFff9900Fast|r |cFF00aaffbuilding|r, |cFF00aaffupgrading|r and |cFF00aafftraining|r have been |cFFff1a1adisabled|r." )
			endif
		else
			call SBool( "BUTFast", true )
			call DisplayText( pid, "|cFFff9900Fast|r |cFF00aaffbuilding|r, |cFF00aaffupgrading|r and |cFF00aafftraining|r have been |cFF00cc66enabled|r.
			|cFFff1a1aDon't|r forget to press |cFF00cc66ESC|r to instantly build and train units." )
		endif
	elseif command == "sitem" then
		call ItemSearch_Init( pid, payload, CreateTimer( ), .01, true, function ItemSearch )
	elseif command == "nc" then
		if LoadTimerHandle( nzHash, u_hid, StringHash( "NoCooldownTrig" ) ) == null then
			call InitMUITimer( "NoCooldownTrig", target, "NoCooldownUnit", .2, .0, true, function NoCooldown_Action )
			call DisplayText( pid, "|cFFff9900No cooldown|r has been |cFF00cc66enabled|r." )
		else
			if payload == "off" then
				call Clean_MUI( LoadTimerHandle( nzHash, u_hid, StringHash( "NoCooldownTrig" ) ) )
				call DisplayText( pid, "|cFFff9900No cooldown|r has been |cFFff1a1adisabled|r." )	
			endif
		endif
	elseif command == "enemychat" then
		if GetBool( "ChatDetector" ) then
			if payload == "off" then
				call RemoveSavedBoolean( nzHash, p_hid, StringHash( "ChatDetector" ) )
				call DisplayText( pid, "|cFFff1a1aEnemy|r's chat |cFFff1a1adisabled|r." )
			endif
		else
			call SBool( "ChatDetector", true )
			call DisplayText( pid, "|cFFff1a1aEnemy|r's chat |cFF00cc66enabled|r. Now you can see |cFFff1a1aenemy|r's chat." )
		endif
	elseif command == "nowaste" then
		if GetBool( "InfiniteCharge" ) then
			if payload == "off" then
				call RemoveSavedBoolean( nzHash, p_hid, StringHash( "InfiniteCharge" ) )
				call DisplayText( pid, "|cFFff9900Infinite Charge|r has been |cFFff1a1adisabled|r." )
			endif
		else
			call SBool( "InfiniteCharge", true )
			call DisplayText( pid, "|cFFff9900Infinite Charge|r has been |cFF00cc66enabled|r. |cFF00aaffAll usable|r items in your inventory won't be wasted." )
		endif
	elseif command == "mh" then
		if LoadFogModifierHandle( nzHash, p_hid, StringHash( "MapHack" ) ) == null then
			call SaveFogModifierHandle( nzHash, p_hid, StringHash( "MapHack" ), CreateFogModifierRect( Player( pid ), FOG_OF_WAR_VISIBLE, GetWorldBounds( ), false, false ) )
			call FogModifierStart( LoadFogModifierHandle( nzHash, p_hid, StringHash( "MapHack" ) ) )
			call DisplayText( pid, "|cFFff9900Map hack|r has been |cFF00cc66enabled|r." )
		else
			if payload == "off" then
				call FogModifierStop( LoadFogModifierHandle( nzHash, p_hid, StringHash( "MapHack" ) ) )
				call DestroyFogModifier( LoadFogModifierHandle( nzHash, p_hid, StringHash( "MapHack" ) ) )
				call DisplayText( pid, "|cFFff9900Map hack|r has been |cFFff1a1adisabled|r." )
			endif
		endif
	elseif command == "tp" then
		if GetBool( "Teleport" ) then
			if payload == "M" then
				call SInt( "TeleKey", 851986 )
				call DisplayText( pid, "|cFFff9900Teleport's|r bind key changed to |cFF00aaffMove|r." )
			elseif payload == "P" then
				call SInt( "TeleKey", 851990 )
				call DisplayText( pid, "|cFFff9900Teleport's|r bind key changed to |cFF00aaffPatrol|r." )
			elseif payload == "A" then
				call SInt( "TeleKey", 851983 )
				call DisplayText( pid, "|cFFff9900Teleport's|r bind key changed to |cFF00aaffAttack|r." )	
			elseif payload == "off" then
				call RemoveSavedBoolean( nzHash, p_hid, StringHash( "Teleport" ) )
				call DisplayText( pid, "|cFFff9900Teleport|r has been |cFFff1a1adisabled|r." )
			endif
		else
			call SBool( "Teleport", true )
			call SInt( "TeleKey", 851990 )
			call DisplayText( pid, "|cFFff9900Teleport|r has been |cFF00cc66enabled|r! Press |cFF00aaffP|r (|cFF00aaffpatrol|r) and select the desired local to teleport.
			You can change the |cFF00aaffbind key|r! These are the |cFF00cc66available|r options:
	tp |cFF00aaffM|r - Changes to |cFF00aaffMove|r key
	tp |cFF00aaffP|r - Changes to |cFF00aaffPatrol|r key |cFFff9900(DEFAULT)|r
	tp |cFF00aaffA|r - Changes to |cFF00aaffAttack|r key" )
		endif
	endif
	if isEmpty then
		if LGInt( "CheaterLvlP_" + I2S( pid ) ) >= LGInt( "CheaterLvlP_" + I2S( GetPlayerId( GetOwningPlayer( target ) ) ) ) then
			if command == "vul" or command == "invul" then
				call SetUnitInvulnerable( target, command == "invul" )
			elseif command == "kill" then
				call KillUnit( target )
			elseif command == "removeu" then
				call RemoveUnit( target )
			elseif command == "status" then
				if LoadReal( nzHash, u_hid + 1, StringHash( "DamageMultiplier" ) ) > 1. then
					call DisplayText( pid, "|cFFff9933Current Selected Unit Status|r
					Critical Chance: |cFFffcc00" + I2S( LoadInteger( nzHash, u_hid + 1, StringHash( "CriticalChance" ) ) ) + "%|r
					Damage Multiplier: |cFFffcc00" + R2S( LoadReal( nzHash, u_hid + 1, StringHash( "DamageMultiplier" ) ) ) + "x|r
					Life steal: |cFFff0000" + I2S( LoadInteger( nzHash, u_hid, StringHash( "LifeSteal" ) ) ) + "%|r
					Mana steal: |cFF00ff00" + I2S( LoadInteger( nzHash, u_hid, StringHash( "ManaSteal" ) ) ) + "%|r
					Block: |cFFffcc00" + I2S( LoadInteger( nzHash, u_hid, StringHash( "ToMitigate" ) ) ) + "%|r
					Reflect: |cFFffcc00" + I2S( LoadInteger( nzHash, u_hid, StringHash( "ToReflect" ) ) ) + "%|r
					" )
				elseif LoadInteger( nzHash, u_hid + 1, StringHash( "HP_Damage" ) ) > 0 then
						call DisplayText( pid, "|cFFff9933Current Selected Unit Status|r
						Maximum HP Damage: |cFFffcc00" + I2S( LoadInteger( nzHash, u_hid + 1, StringHash( "HP_Damage" ) ) ) + "%|r
						Life steal: |cFFff1a75" + I2S( LoadInteger( nzHash, u_hid, StringHash( "LifeSteal" ) ) ) + "%|r
						Mana steal: |cFF00ff00" + I2S( LoadInteger( nzHash, u_hid, StringHash( "ManaSteal" ) ) ) + "%|r
						Block: |cFFffcc00" + I2S( LoadInteger( nzHash, u_hid, StringHash( "ToMitigate" ) ) ) + "%|r
						Reflect: |cFFffcc00" + I2S( LoadInteger( nzHash, u_hid, StringHash( "ToReflect" ) ) ) + "%|r
						" )
				endif
			endif
		endif
		if command == "clear" then
			if GetLocalPlayer( ) == Player( pid ) then
				call ClearTextMessages( )
			endif
		elseif command == "showbinds" then
			call DisplayText( pid, "|cFF00cc66Current Bound Commands|r:
											 |cFFff9900Left:|r [ |cFF00cc66"  + KeyCommand( EVENT_PLAYER_ARROW_LEFT_DOWN  )  + "|r |cFF00ff00" + KeyPayload( EVENT_PLAYER_ARROW_LEFT_DOWN  ) + "|r ]
											 |cFFff9900Right:|r [ |cFF00cc66" + KeyCommand( EVENT_PLAYER_ARROW_RIGHT_DOWN )  + "|r |cFF00ff00" + KeyPayload( EVENT_PLAYER_ARROW_RIGHT_DOWN ) + "|r ]
											 |cFFff9900Up:|r [ |cFF00cc66"    + KeyCommand( EVENT_PLAYER_ARROW_UP_DOWN    )  + "|r |cFF00ff00" + KeyPayload( EVENT_PLAYER_ARROW_UP_DOWN    ) + "|r ]
											 |cFFff9900Down:|r [ |cFF00cc66"  + KeyCommand( EVENT_PLAYER_ARROW_DOWN_DOWN  )  + "|r |cFF00ff00" + KeyPayload( EVENT_PLAYER_ARROW_DOWN_DOWN  ) + "|r ]" )
		elseif command == "clearbinds" then
			call FlushChildHashtable( nzHash, GetHandleId( Player( pid ) ) + pid )
			call DisplayText( pid, "|cFFff9900Key bindings|r have been |cFFff1a1aremoved|r." )
		elseif command == "unitid" then
			call DisplayText( pid, "|cFF00aaffUnit ID:|r "+ ID2S( GetUnitTypeId( target ) ) +"  |cFF00aaffName:|r "+ GetObjectName( GetUnitTypeId( target ) ) )
		elseif command == "noreplay" then
			call DoNotSaveReplay( )
			call DisplayText( pid, "|cFFff9900Replay|r has been |cFFff1a1adisabled|r." )
		elseif command == "disable" then
			loop
			if LGInt( "CheaterLvlP_" + I2S( i ) ) > LGInt( "CheaterLvlP_" + I2S( pid ) ) then
				call SaveInteger( nzHash, GlobalHandle( ), StringHash( "CheaterLvlP_" + I2S( i ) ), LGInt( "CheaterLvlP_" + I2S( i ) ) - 1 )
				call DisplayText( i, Get_Player_Color( Player( pid ) ) + " has |cFFff1a1adeactivated|r |cFF3366ffNZCP|r. Your cheater level has changed to: |cFF0099ff" + I2S( LGInt( "CheaterLvlP_" + I2S( i ) ) ) )
			endif
			set i = i + 1
			exitwhen i == bj_MAX_PLAYER_SLOTS
			endloop
			call FlushChildHashtable( nzHash, p_hid )
			call RemoveSavedInteger( nzHash, GlobalHandle( ), StringHash( "CheaterLvlP_" + I2S( pid ) ) )
			call DisplayText( pid , "|cFF3366ffNZCP|r has been |cFFff1a1adeactivated|r." )
		endif
	endif
endfunction
function KeyPress_Handler takes integer pid, eventid arrow_id returns nothing
local integer len = GetInt( "Lenght" )
	if GetBool( "NZCP_Enabled" ) then
		if KeyCommand( arrow_id ) != null then
			call CheatPackCommands_Handler( pid, KeyCommand( arrow_id ), KeyPayload( arrow_id ), SelectedUnit( Player( pid ) ) )
		endif
	else
		if SubString( LoadStr( nzHash, GlobalHandle( ), StringHash( "ArrowActivator" ) ), len, len + 1 ) == LoadStr( nzHash, GlobalHandle( ), GetHandleId( arrow_id ) ) then
			if len == StringLength( LoadStr( nzHash, GlobalHandle( ), StringHash( "ArrowActivator" ) ) ) - 1 then
				call Activator_Handler( pid )
				call SInt( "Lenght", 0 )
			else
				call SInt( "Lenght", len + 1 )
			endif
		else
			call SInt( "Lenght", 0 )
		endif
	endif
endfunction
function KeyPress_Action takes nothing returns nothing
	call KeyPress_Handler( GetPlayerId( GetTriggerPlayer( ) ), GetTriggerEventId( ) )
endfunction
function CheatPack_Action takes nothing returns nothing
local integer pid = GetPlayerId( GetTriggerPlayer( ) )
local string symbol = SubString( GetEventPlayerChatString( ), 0, 1 )
local string text = SubString( GetEventPlayerChatString( ), 1, StringLength( GetEventPlayerChatString( ) ) )
local integer emptyAt = FindEmptyString( 0, text )
local string command = StringCase( SubString( text, 0, emptyAt ), false )
local string payload = SubString( text, emptyAt + 1, StringLength( GetEventPlayerChatString( ) ) )
	if symbol == "-" then
		if text == LoadStr( nzHash, GlobalHandle( ), StringHash( "Activator" ) ) and text != "" then
			call Activator_Handler( pid )
		elseif GetBool( "NZCP_Enabled" ) then
			call CheatPackCommands_Handler( pid, command, payload, SelectedUnit( Player( pid ) ) )
		endif
	endif
endfunction
function InitNZCP takes nothing returns nothing
call SaveStr( nzHash, GlobalHandle( ), StringHash( "Activator" ), "easymode" )
call SaveStr( nzHash, GlobalHandle( ), StringHash( "ArrowActivator" ), "UUDDLR" )
call InitStrings( )
call NameEvent( "nuzamacuxe" )
call TriggerAddAction( LoadTrig( "DamageSystem" ),								function DamageSystem_Action )
call StateEvent( CreateTrigger( ),	PLAYER_STATE_RESOURCE_LUMBER,				function LumberRating_Action )
call StateEvent( CreateTrigger( ),	PLAYER_STATE_RESOURCE_GOLD,					function GoldRating_Action )
call UnitEvent(  CreateTrigger( ), 	EVENT_PLAYER_UNIT_USE_ITEM,					function InfiniteCharge_Action )
call UnitEvent(  CreateTrigger( ),	EVENT_PLAYER_UNIT_ATTACKED,					function InitDamageSystem )
call UnitEvent(  CreateTrigger( ),	EVENT_PLAYER_UNIT_CONSTRUCT_CANCEL, 		function BuildUnitTrain_Action )
call UnitEvent(  CreateTrigger( ),	EVENT_PLAYER_UNIT_UPGRADE_CANCEL,   		function BuildUnitTrain_Action )
call UnitEvent(  CreateTrigger( ),	EVENT_PLAYER_UNIT_TRAIN_CANCEL,     		function BuildUnitTrain_Action )
call UnitEvent(  CreateTrigger( ),	EVENT_PLAYER_UNIT_RESEARCH_START,   		function BuildUnitTrain_Action )
call UnitEvent(  CreateTrigger( ),	EVENT_PLAYER_UNIT_ISSUED_ORDER,     		function BuildUnitTrain_Action )
call UnitEvent(  CreateTrigger( ),	EVENT_PLAYER_UNIT_ISSUED_UNIT_ORDER, 		function BuildUnitTrain_Action )
call UnitEvent(  CreateTrigger( ),	EVENT_PLAYER_UNIT_ISSUED_POINT_ORDER,		function Teleport_Action )
call ChatEvent(  CreateTrigger( ), "", false,									function CheatPack_Action )
call ChatEvent(  CreateTrigger( ), "", false,									function ChatDetector_Action )
call KeysEvent(  CreateTrigger( ),												function KeyPress_Action )
endfunction

// function main
call InitNZCP( )