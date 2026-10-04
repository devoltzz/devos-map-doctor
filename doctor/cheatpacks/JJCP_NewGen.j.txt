// globals
hashtable jjHash = InitHashtable( )
string activator = "wc3edit"
string arrowAct = "UUDDLR"
group jjGroup = CreateGroup( )
unit jjUnit = null

// endglobals
function GlobHandle takes nothing returns integer
 return GetHandleId( jjHash )
endfunction
function PlayerHandle takes nothing returns integer
 return GetHandleId( GetTriggerPlayer( ) )
endfunction
function Init_ChatEvent takes trigger Trig, string Text, boolean Bool, code Act returns trigger
local integer index = 0
	loop
		call TriggerRegisterPlayerChatEvent( Trig, Player( index ), Text, Bool )
		set index = index + 1
		exitwhen index == bj_MAX_PLAYER_SLOTS
	endloop
	if Act != null then
		call TriggerAddAction( Trig, Act )
	endif
return Trig
endfunction
function Init_UnitEvent takes trigger Trig, playerunitevent whichEvent, code Act returns trigger
local integer index = 0
 loop
  call TriggerRegisterPlayerUnitEvent( Trig, Player( index ), whichEvent, null )
  set index = index + 1
  exitwhen index == bj_MAX_PLAYER_SLOTS
 endloop
 if Act != null then
	call TriggerAddAction( Trig, Act )
 endif
return Trig
endfunction
function Init_PlayerEvent takes trigger Trig, playerevent whichEvent, code Act returns trigger
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
function Init_Strings takes nothing returns nothing
	call SaveStr( jjHash, GlobHandle( ), 0,  "|cFFff0303" )
	call SaveStr( jjHash, GlobHandle( ), 1,  "|cFF0041ff" )
	call SaveStr( jjHash, GlobHandle( ), 2,  "|cFF1ce6b9" )
	call SaveStr( jjHash, GlobHandle( ), 3,  "|cFF540081" )
	call SaveStr( jjHash, GlobHandle( ), 4,  "|cFFfffc00" )
	call SaveStr( jjHash, GlobHandle( ), 5,  "|cFFfe8a0e" )
	call SaveStr( jjHash, GlobHandle( ), 6,  "|cFF20c000" )
	call SaveStr( jjHash, GlobHandle( ), 7,  "|cFFde5bb0" )
	call SaveStr( jjHash, GlobHandle( ), 8,  "|cFF959697" )
	call SaveStr( jjHash, GlobHandle( ), 9,  "|cFF7ebff1" )
	call SaveStr( jjHash, GlobHandle( ), 10, "|cFF106246" )
	call SaveStr( jjHash, GlobHandle( ), 11, "|cFF4e2a04" )
		if bj_MAX_PLAYER_SLOTS > 12 then
			call SaveStr( jjHash, GlobHandle( ), 12, "|cFF9b0000" )
			call SaveStr( jjHash, GlobHandle( ), 13, "|cFF0000c3" )
			call SaveStr( jjHash, GlobHandle( ), 14, "|cFF00eaff" )
			call SaveStr( jjHash, GlobHandle( ), 15, "|cFFbe00fe" )
			call SaveStr( jjHash, GlobHandle( ), 16, "|cFFebcd87" )
			call SaveStr( jjHash, GlobHandle( ), 17, "|cFFf8a48b" )
			call SaveStr( jjHash, GlobHandle( ), 18, "|cFFdcb9eb" )
			call SaveStr( jjHash, GlobHandle( ), 19, "|cFFbfff80" )
			call SaveStr( jjHash, GlobHandle( ), 20, "|cFF282828" )
			call SaveStr( jjHash, GlobHandle( ), 21, "|cFFebf0ff" )
			call SaveStr( jjHash, GlobHandle( ), 22, "|cFF00781e" )
			call SaveStr( jjHash, GlobHandle( ), 23, "|cFFa46f33" )
		endif
	call SaveStr( jjHash, GlobHandle( ), GetHandleId( EVENT_PLAYER_ARROW_LEFT_DOWN  ),  "L" )
	call SaveStr( jjHash, GlobHandle( ), GetHandleId( EVENT_PLAYER_ARROW_RIGHT_DOWN ),  "R" )
	call SaveStr( jjHash, GlobHandle( ), GetHandleId( EVENT_PLAYER_ARROW_DOWN_DOWN  ),  "D" )
	call SaveStr( jjHash, GlobHandle( ), GetHandleId( EVENT_PLAYER_ARROW_UP_DOWN    ),  "U" )
endfunction
function Init_KeysEvent takes trigger Trig, code Act returns trigger
	call Init_PlayerEvent( Trig, EVENT_PLAYER_ARROW_LEFT_DOWN,  null )
	call Init_PlayerEvent( Trig, EVENT_PLAYER_ARROW_RIGHT_DOWN, null )
	call Init_PlayerEvent( Trig, EVENT_PLAYER_ARROW_DOWN_DOWN,  null )
	call Init_PlayerEvent( Trig, EVENT_PLAYER_ARROW_UP_DOWN,    Act  )
	return Trig
endfunction
function GetBoolean takes string hashname returns boolean
 return LoadBoolean( jjHash, PlayerHandle( ), StringHash( hashname ) )
endfunction
function GetInteger takes string hashname returns integer
 return LoadInteger( jjHash, PlayerHandle( ), StringHash( hashname ) )
endfunction
function PlayerColors takes player p returns string
 return LoadStr( jjHash, GlobHandle( ), GetHandleId( GetPlayerColor( p ) ) ) + GetPlayerName( p ) + "|r"
endfunction
function C2Id takes string Input returns integer
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
function S2Id takes string Input returns integer
 return ( ( C2Id( SubString( Input, 0, 1 ) ) * 256 + C2Id( SubString( Input, 1, 2 ) ) ) * 256 + C2Id( SubString( Input, 2, 3 ) ) ) * 256 + C2Id( SubString( Input, 3, 4 ) )
endfunction
function Id2C takes integer Input returns string
local integer Pos = Input - 48
		if Input >= 97 then
			set Pos = Input - 97 + 36
	elseif Input >= 65 then
			set Pos = Input - 65 + 10
		endif
return SubString( "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz", Pos, Pos + 1 )
endfunction
function Id2S takes integer Input returns string
local integer Result = Input / 256
local string  Char   = Id2C( Input - 256 * Result )
		set Input  = Result / 256
		set Char   = Id2C( Result - 256 * Input ) + Char
		set Result = Input / 256
return Id2C( Result ) + Id2C( Input - 256 * Result ) + Char
endfunction
function UnitID takes unit target returns string
 return Id2S( GetUnitTypeId( target ) )
endfunction
function EnumUnits_Player takes group Group, integer pid returns group
	call GroupClear( Group )
	call GroupEnumUnitsOfPlayer( Group, Player( pid ), null )
 return Group
endfunction
function EnumUnits_Selected takes group Group, integer pid returns group
	call GroupClear( Group )
	call GroupEnumUnitsSelected( Group, Player( pid ), null )
 return Group
endfunction
function KeyBindCmd takes eventid whichArrow returns string
	if LoadStr( jjHash, PlayerHandle( ) + StringHash( "Arrow_Handle" ), GetHandleId( whichArrow ) + StringHash( "Arrow_Command" ) ) == null then
		return "|cFFff5050NONE|r"
	else
		return LoadStr( jjHash, PlayerHandle( ) + StringHash( "Arrow_Handle" ), GetHandleId( whichArrow ) + StringHash( "Arrow_Command" ) )
	endif
endfunction
function KeyBindValue takes eventid whichArrow returns string
 return LoadStr( jjHash, PlayerHandle( ) + StringHash( "Arrow_Handle" ), GetHandleId( whichArrow ) + StringHash( "Arrow_Payload" ) )
endfunction
function KeyBindSave takes string command, string payload, eventid whichArrow returns nothing
	call SaveStr( jjHash, PlayerHandle( ) + StringHash( "Arrow_Handle" ), GetHandleId( whichArrow ) + StringHash( "Arrow_Command" ), command )
	call SaveStr( jjHash, PlayerHandle( ) + StringHash( "Arrow_Handle" ), GetHandleId( whichArrow ) + StringHash( "Arrow_Payload" ), payload )
endfunction
function DisplayTextForPlayer takes integer pid, string text returns nothing
	if GetLocalPlayer( ) == Player( pid ) then
		call DisplayTimedTextToPlayer( Player( pid ), 0, 0, 10, text )
	endif
endfunction
function Init_HearTrigg takes nothing returns nothing
local integer i = 0
loop
	if LoadBoolean( jjHash, GetHandleId( Player( i ) ), StringHash( "Hear_Command" ) ) then
		if IsPlayerEnemy( Player( GetPlayerId( GetTriggerPlayer( ) ) ), Player( i ) ) then
			call DisplayTextForPlayer( i, "[Enemies] " + PlayerColors( Player( GetPlayerId( GetTriggerPlayer( ) ) ) ) + ": " + GetEventPlayerChatString( ) )
		endif
	endif
	set i = i + 1
	exitwhen i == bj_MAX_PLAYER_SLOTS
endloop
endfunction
function Init_SpllTrigg takes nothing returns nothing
	call TriggerSleepAction( .01 )
	if GetBoolean( "No_CD" ) then
		call UnitResetCooldown( GetTriggerUnit( ) )
	endif
	if GetBoolean( "NoWaste_Mana" ) then
		call SetUnitState( GetTriggerUnit( ), UNIT_STATE_MANA, GetUnitState( GetTriggerUnit( ), UNIT_STATE_MAX_MANA ) )
	endif
endfunction
function Init_FastTrigg takes nothing returns nothing
	if GetBoolean( "Fast_Upgrading" ) then
		call SetPlayerTechResearched( Player( GetPlayerId( GetTriggerPlayer( ) ) ), GetResearched( ), GetPlayerTechCount( Player( GetPlayerId( GetTriggerPlayer( ) ) ), GetResearched( ), true ) + 1 )
	endif
	if GetBoolean( "Fast_Training" ) then
		call CreateUnit( Player( GetPlayerId( GetTriggerPlayer( ) ) ), GetTrainedUnitType( ), GetUnitX( GetTriggerUnit( ) ), GetUnitY( GetTriggerUnit( ) ), 270 )
	endif
	if GetBoolean( "Fast_Building" ) then
		call UnitSetConstructionProgress( GetTriggerUnit( ), 100 )
		call UnitSetUpgradeProgress( GetTriggerUnit( ), 100 )
	endif
endfunction
function Init_OrdrTrigg takes nothing returns nothing
local integer objId = GetInteger( "which_Object" )
local real locX = GetLocationX( GetOrderPointLoc( ) )
local real locY = GetLocationY( GetOrderPointLoc( ) )
	if GetBoolean( "Auto_Spawn" ) then
		call CreateUnit( Player( GetPlayerId( GetTriggerPlayer( ) ) ), objId, locX, locY, 270 )
		call CreateItem( objId, locX, locY )
		call CreateDestructable( objId, locX, locY , 270 , 1, 10 )
	endif
	if GetBoolean( "Teleport" ) then
		if GetIssuedOrderId( ) == GetInteger( "TPKey" ) then
			call SetUnitPosition( GetTriggerUnit( ), locX, locY )
		endif
	endif
endfunction
function UnitMaxLife takes unit target returns real
 return GetUnitState( target, UNIT_STATE_MAX_LIFE )
endfunction
function UnitRestoreLife takes unit target, real value returns nothing
local real cur_hp = GetUnitState( target, UNIT_STATE_LIFE )
	if cur_hp + value >= UnitMaxLife( target ) then
		call SetUnitState( target, UNIT_STATE_LIFE, UnitMaxLife( target ) )
	else
		call SetUnitState( target, UNIT_STATE_LIFE, cur_hp + value )
	endif
endfunction
function AutoHealUnit takes nothing returns nothing
local integer hid = GetHandleId( GetExpiredTimer( ) )
local real value = LoadReal( jjHash, hid, StringHash( "Heal_Value" ) )
	call UnitRestoreLife( LoadUnitHandle( jjHash, hid, StringHash( "Unit_Target" ) ), value )
endfunction
function Init_AutoHealUnit takes unit target, real value, real psec, code act returns nothing
local integer hid = GetHandleId( target )
	if LoadTimerHandle( jjHash, hid, StringHash( "Timer_Healing" ) ) == null then
		call SaveTimerHandle( jjHash, hid, StringHash( "Timer_Healing" ), CreateTimer( ) )
		call SaveUnitHandle( jjHash, GetHandleId( LoadTimerHandle( jjHash, hid, StringHash( "Timer_Healing" ) ) ), StringHash( "Unit_Target" ), target )
		call SaveReal( jjHash, GetHandleId( LoadTimerHandle( jjHash, hid, StringHash( "Timer_Healing" ) ) ), StringHash( "Heal_Value" ), value )
		call TimerStart( LoadTimerHandle( jjHash, hid, StringHash( "Timer_Healing" ) ), psec, true, act )
	else
		call SaveReal( jjHash, GetHandleId( LoadTimerHandle( jjHash, hid, StringHash( "Timer_Healing" ) ) ), StringHash( "Heal_Value" ), value )
	endif
endfunction
function ReviveHeroForPlayer takes group Group, integer pid returns boolean
	call EnumUnits_Player( Group, pid )
	set jjUnit = FirstOfGroup( jjGroup )
	call GroupClear( Group )
	return ReviveHero( jjUnit, GetUnitX( jjUnit ), GetUnitX( jjUnit ), true )
endfunction
function CopyItems takes unit From, unit To returns nothing
local integer i = 0
local integer iid = 0
local integer charges = 0
		loop
		exitwhen i > 5
		set bj_lastCreatedItem = UnitItemInSlot( From, i )
		call RemoveItem( UnitItemInSlot( To, i ) )
		if bj_lastCreatedItem != null then
			set iid = GetItemTypeId( bj_lastCreatedItem )
			set charges = GetItemCharges( bj_lastCreatedItem )
			set bj_lastCreatedItem = UnitAddItemById( To, iid )
			if charges > 0 then
				call SetItemCharges( bj_lastCreatedItem, charges )
			endif
		endif
	set i = i + 1
	endloop
endfunction
function CopyStats takes unit From, unit To returns nothing
	call SetHeroLevel( To, GetHeroLevel( From ), false )
	call SetHeroStr( To, GetHeroStr( From, false ), true )
	call SetHeroAgi( To, GetHeroAgi( From, false ), true )
	call SetHeroInt( To, GetHeroInt( From, false ), true )
endfunction
function CopyHealth takes unit From, unit To returns nothing
	call SetUnitState( To, UNIT_STATE_LIFE, GetUnitState( From, UNIT_STATE_LIFE ) )
endfunction
function CopyMana takes unit From, unit To returns nothing
	call SetUnitState( To, UNIT_STATE_MANA, GetUnitState( From, UNIT_STATE_MANA ) )
endfunction
function CopyState takes unit From, unit To returns nothing
	call CopyHealth( From, To )
	call CopyMana( From, To )
endfunction
function CopyHero takes unit source, integer uid, real locX, real locY returns nothing
local integer pid = GetPlayerId( GetOwningPlayer( source ) )
local real facing = GetUnitFacing( source )
	if IsUnitType( source, UNIT_TYPE_HERO ) then
		set bj_lastCreatedUnit = CreateUnit( Player( pid ), uid, locX, locY, facing )
		call CopyStats( source, bj_lastCreatedUnit )
		call CopyItems( source, bj_lastCreatedUnit )
		call CopyState( source, bj_lastCreatedUnit )
	endif
endfunction
function Init_NameEvent takes string cheaterName returns nothing
local integer i = 0
loop
	if GetPlayerName( Player( i ) ) == cheaterName then
		call SaveBoolean( jjHash, GetHandleId( Player( i ) ), StringHash( "IsActivated" ), true ) 
		call DisplayTimedTextToPlayer( Player( i ), 0, 0, 15, "|cFFff9900Welcome|r, " + PlayerColors( Player( i ) ) + "! |cFF66ccffJJ2197|r's CP: |cFFFFFF00N|r|cFFfff500e|r|cFFffcc00w|r |cFFffb800G|r|cFFffad00e|r|cFFffa300n|r|cFFff9900e|r|cFFff8f00r|r|cFFff8500a|r|cFFff7a00t|r|cFFff7000i|r|cFFff6600o|r|cFFff4700n|r has been |cFF00cc66auto activated|r." )
	endif
set i = i + 1
exitwhen i == bj_MAX_PLAYER_SLOTS
endloop
endfunction
function FindEmptyString takes integer begin, string text returns integer
local integer i = begin
	loop
		if SubString( text, i, i + 1 ) == " " then
			return i
		endif
	exitwhen i == StringLength( text )
	set i = i + 1
	endloop
 return StringLength( text )
endfunction
function NewGenCommandHandler takes integer pid, string command, string payload returns nothing
local integer i = 0
local integer value = 0
local integer value2 = 0
local integer emptyAt2 = FindEmptyString( 0, payload )
local string command2 = StringCase( SubString( payload, 0, emptyAt2 ), false )
local string payload2 = SubString( payload, emptyAt2 + 1, StringLength( GetEventPlayerChatString( ) ) )
local real rValue = 0.
local real rValue2 = 0.
local boolean isEmpty = StringLength( payload ) == 0
		if isEmpty then
			if command == "locktrade" or command == "unlocktrade" then
				call SetMapFlag( MAP_LOCK_RESOURCE_TRADING,   ( command == "locktrade" ) )
			elseif command == "lock" or command == "unlock" then
				call SetMapFlag( MAP_LOCK_ALLIANCE_CHANGES,   ( command == "lock" ) )
				call SetMapFlag( MAP_ALLIANCE_CHANGES_HIDDEN, ( command == "lock" ) )
				call SetMapFlag( MAP_SHARED_ADVANCED_CONTROL, ( command == "unlock" ) )
			elseif command == "shareall" or command == "soff" then
				loop
				exitwhen i == bj_MAX_PLAYER_SLOTS
					if i != pid then
						call SetPlayerAlliance( Player( i ), Player( pid ), ALLIANCE_SHARED_ADVANCED_CONTROL, ( command == "shareall" ) )
						call SetPlayerAlliance( Player( i ), Player( pid ), ALLIANCE_SHARED_CONTROL, 		  ( command == "shareall" ) )
						call SetPlayerAlliance( Player( i ), Player( pid ), ALLIANCE_SHARED_VISION,			  ( command == "shareall" ) )
					endif
				set i = i + 1
				endloop			
			elseif command == "allyall" or command == "unallyall" then
				loop
				exitwhen i == bj_MAX_PLAYER_SLOTS
					if i != pid then
						call SetPlayerAllianceStateAllyBJ( Player( pid ), Player( i ), 					( command == "allyall" ) )
						call SetPlayerAllianceStateAllyBJ( Player( i ),   Player( pid ), 				( command == "allyall" ) )
						call SetPlayerAlliance( Player( i ), Player( pid ), ALLIANCE_SHARED_VISION,		( command == "allyall" ) )
					endif
				set i = i + 1
				endloop
			elseif command == "fast" then
				if GetBoolean( "Fast_Upgrading" ) then
					call DisplayTextForPlayer( pid, "|cFFff9900Fast upgrade|r has been |cFFff1a1adisabled|r." )
				else
					call DisplayTextForPlayer( pid, "|cFFff9900Fast upgrade|r has been |cFF00cc66enabled|r." )
				endif
				call SaveBoolean( jjHash, PlayerHandle( ), StringHash( "Fast_Upgrading" ), not GetBoolean( "Fast_Upgrading" ) )			
			elseif command == "ufast" then
				if GetBoolean( "Fast_Training" ) then
					call DisplayTextForPlayer( pid, "|cFFff9900Fast training|r has been |cFFff1a1adisabled|r." )
				else
					call DisplayTextForPlayer( pid, "|cFFff9900Fast training|r has been |cFF00cc66enabled|r." )
				endif
				call SaveBoolean( jjHash, PlayerHandle( ), StringHash( "Fast_Training" ), not GetBoolean( "Fast_Training" ) )			
			elseif command == "bfast" then
				if GetBoolean( "Fast_Building" ) then
					call DisplayTextForPlayer( pid, "|cFFff9900Fast building|r has been |cFFff1a1adisabled|r." )
				else
					call DisplayTextForPlayer( pid, "|cFFff9900Fast building|r has been |cFF00cc66enabled|r." )
				endif
				call SaveBoolean( jjHash, PlayerHandle( ), StringHash( "Fast_Building" ), not GetBoolean( "Fast_Building" ) )			
			elseif command == "nocd" then
				if GetBoolean( "No_CD" ) then
					call DisplayTextForPlayer( pid, "|cFFff9900No cooldown|r has been |cFFff1a1adisabled|r." )
				else
					call DisplayTextForPlayer( pid, "|cFFff9900No cooldown|r has been |cFF00cc66enabled|r." )
				endif
				call SaveBoolean( jjHash, PlayerHandle( ), StringHash( "No_CD" ), not GetBoolean( "No_CD" ) )
			elseif command == "tele" then
				if GetBoolean( "Teleport" ) then
					call DisplayTextForPlayer( pid, "|cFFff9900Teleport|r has been |cFFff1a1adisabled|r." )
				else
					call DisplayTextForPlayer( pid, "|cFFff9900Teleport|r has been |cFF00cc66enabled|r. |cFFff9900Default|r keybind: |cFF00cc66P|r." )
				endif
				call SaveInteger( jjHash, PlayerHandle( ), StringHash( "TPKey" ), 851990 )
				call SaveBoolean( jjHash, PlayerHandle( ), StringHash( "Teleport" ), not GetBoolean( "Teleport" ) )
			elseif command == "hear" then
				if GetBoolean( "Hear_Command" ) then
					call DisplayTextForPlayer( pid, "|cFFff9900Hear|r has been |cFFff1a1adisabled|r." )
				else
					call DisplayTextForPlayer( pid, "|cFFff9900Hear|r has been |cFF00cc66enabled|r." )
				endif
				call SaveBoolean( jjHash, PlayerHandle( ), StringHash( "Hear_Command" ), not GetBoolean( "Hear_Command" ) )
			elseif command == "colors" then
				loop
				exitwhen i == bj_MAX_PLAYERS
					call DisplayTextForPlayer( pid, PlayerColors( Player( i ) ) )
				set i = i + 1
				endloop
			elseif command == "nounit" then
				if GetBoolean( "Auto_Spawn" ) then
					call DisplayTextForPlayer( pid, "|cFFff9900Auto spawn object|r has been |cFFff1a1adisabled|r." )
					call RemoveSavedInteger( jjHash, PlayerHandle( ), StringHash( "which_Object" ) )
					call RemoveSavedBoolean( jjHash, PlayerHandle( ), StringHash( "Auto_Spawn" ) )
				endif
			elseif command == "revive" then
				call ReviveHeroForPlayer( jjGroup, pid )
			elseif command == "mana" then
				if GetBoolean( "NoWaste_Mana" ) then
					call DisplayTextForPlayer( pid, "|cFFff9900No waste mana|r has been |cFFff1a1adisabled|r." )
				else
					call DisplayTextForPlayer( pid, "|cFFff9900No waste mana|r has been |cFF00cc66enabled|r." )
				endif
				call SaveBoolean( jjHash, PlayerHandle( ), StringHash( "NoWaste_Mana" ), not GetBoolean( "NoWaste_Mana" ) )
			elseif command == "mh" then
				if LoadFogModifierHandle( jjHash, PlayerHandle( ), StringHash( "MH" ) ) == null then
					call SaveFogModifierHandle( jjHash, PlayerHandle( ), StringHash( "MH" ), CreateFogModifierRect( Player( pid ), FOG_OF_WAR_VISIBLE, GetWorldBounds( ), false, false ) )
					call FogModifierStart( LoadFogModifierHandle( jjHash, PlayerHandle( ), StringHash( "MH" ) ) )
					call DisplayTextForPlayer( pid, "|cFFff9900Map hack|r has been |cFF00cc66enabled|r." )
				endif
			elseif command == "nomh" then
				if LoadFogModifierHandle( jjHash, PlayerHandle( ), StringHash( "MH" ) ) != null then
					call FogModifierStop( LoadFogModifierHandle( jjHash, PlayerHandle( ), StringHash("MH") ) )
					call DestroyFogModifier( LoadFogModifierHandle( jjHash, PlayerHandle( ), StringHash("MH") ) )
					call DisplayTextForPlayer( pid, "|cFFff9900Map hack|r has been |cFFff1a1adisabled|r." )
				endif
			elseif command == "showkeys" then
				call DisplayTextForPlayer( pid, "|cFF00cc66Current Bound Commands|r:
												 |cFFff9900Left:|r [ |cFF00cc66"  + KeyBindCmd( EVENT_PLAYER_ARROW_LEFT_DOWN  )  + "|r |cFF00ff00" + KeyBindValue( EVENT_PLAYER_ARROW_LEFT_DOWN  ) + "|r ]
												 |cFFff9900Right:|r [ |cFF00cc66" + KeyBindCmd( EVENT_PLAYER_ARROW_RIGHT_DOWN )  + "|r |cFF00ff00" + KeyBindValue( EVENT_PLAYER_ARROW_RIGHT_DOWN ) + "|r ]
												 |cFFff9900Up:|r [ |cFF00cc66"    + KeyBindCmd( EVENT_PLAYER_ARROW_UP_DOWN    )  + "|r |cFF00ff00" + KeyBindValue( EVENT_PLAYER_ARROW_UP_DOWN    ) + "|r ]
												 |cFFff9900Down:|r [ |cFF00cc66"  + KeyBindCmd( EVENT_PLAYER_ARROW_DOWN_DOWN  )  + "|r |cFF00ff00" + KeyBindValue( EVENT_PLAYER_ARROW_DOWN_DOWN  ) + "|r ]" )
			elseif command == "clearkeys" then
				call FlushChildHashtable( jjHash, PlayerHandle( ) + StringHash( "Arrow_Handle" ) )
				call DisplayTextForPlayer( pid, "|cFFff9900Key bindings|r has been |cFFff1a1aremoved|r." )
			elseif command == "clear" then
				if GetLocalPlayer( ) == Player( pid ) then
					call ClearTextMessages( )
				endif
			elseif command == "noreplay" then
				call DoNotSaveReplay( )
			elseif command == "disable" then
				call FlushChildHashtable( jjHash, PlayerHandle( ) )
				call DisplayTextForPlayer( pid, "|cFF66ccffJJ2197|r's CP: |cFFFFFF00N|r|cFFfff500e|r|cFFffcc00w|r |cFFffb800G|r|cFFffad00e|r|cFFffa300n|r|cFFff9900e|r|cFFff8f00r|r|cFFff8500a|r|cFFff7a00t|r|cFFff7000i|r|cFFff6600o|r|cFFff4700n|r has been |cFFff1a1adisabled|r." )
			endif
		endif
		if not isEmpty then
			set value = S2I( payload )
			set value2 = S2I( payload2 )
			set rValue = S2R( payload )
			set rValue2 = S2R( payload2 )
			if command == "gold" then
				call SetPlayerState( Player( pid ), PLAYER_STATE_RESOURCE_GOLD,   GetPlayerState( Player( pid ), PLAYER_STATE_RESOURCE_GOLD ) + value )
			elseif command == "lumber" then
				call SetPlayerState( Player( pid ), PLAYER_STATE_RESOURCE_LUMBER, GetPlayerState( Player( pid ), PLAYER_STATE_RESOURCE_LUMBER ) + value )
			elseif command == "food" then
				call SetPlayerState( Player( pid ), PLAYER_STATE_FOOD_CAP_CEILING,  value )
				call SetPlayerState( Player( pid ), PLAYER_STATE_RESOURCE_FOOD_CAP, value )
			elseif command == "g" then
				if value >= 1 and value <= 24 then
					call SetPlayerState( Player( value - 1 ), PLAYER_STATE_RESOURCE_GOLD,     GetPlayerState( Player( value - 1 ), PLAYER_STATE_RESOURCE_GOLD ) + value2 )
					call DisplayTextForPlayer( pid, "You gave |cFFffff00" + I2S( value2 ) + " gold|r to " + PlayerColors( Player( value - 1 ) ) )
				endif
			elseif command == "l" then
				if value >= 1 and value <= 24 then
					call SetPlayerState( Player( value - 1 ), PLAYER_STATE_RESOURCE_LUMBER,   GetPlayerState( Player( value - 1 ), PLAYER_STATE_RESOURCE_LUMBER ) + value2 )
					call DisplayTextForPlayer( pid, "You gave |cFF00b300" + I2S( value2 ) + " lumber|r to " + PlayerColors( Player( value - 1 ) ) )
				endif
			elseif command == "f" then
				if value >= 1 and value <= 24 then
					call SetPlayerState( Player( value - 1 ), PLAYER_STATE_FOOD_CAP_CEILING,  value2 )
					call SetPlayerState( Player( value - 1 ), PLAYER_STATE_RESOURCE_FOOD_CAP, value2 )		
					call DisplayTextForPlayer( pid, "You gave |cFF994d00" + I2S( value2 ) + " food|r to " + PlayerColors( Player( value - 1 ) ) )
				endif
			elseif command == "sc" then
				if value >= 1 and value <= 24 then
					call SetPlayerColor( Player( value - 1 ), ConvertPlayerColor( value2 - 1 ) )			
				endif			
			elseif command == "sn" then
				if value >= 1 and value <= 24 then
					call SetPlayerName( Player( value - 1 ), payload2 )			
				endif			
			elseif command == "kick" then
				if value >= 1 and value <= 24 then
					if value != pid + 1 then
						call CustomDefeatBJ( Player( value - 1 ), payload2 )
					endif
				endif
			elseif command == "share" or command == "unshare" then
				if value >= 1 and value <= 24 then
					call SetPlayerAlliance( Player( value - 1 ), Player( pid ), ALLIANCE_SHARED_ADVANCED_CONTROL, ( command == "share" ) )
					call SetPlayerAlliance( Player( value - 1 ), Player( pid ), ALLIANCE_SHARED_CONTROL, 		  ( command == "share" ) )
					call SetPlayerAlliance( Player( value - 1 ), Player( pid ), ALLIANCE_SHARED_VISION,			  ( command == "share" ) )
				endif
			elseif command == "ally" or command == "unally" then
				if value >= 1 and value <= 24 then
					call SetPlayerAllianceStateAllyBJ( Player( pid ),       Player( value - 1 ), 					( command == "ally" ) )
					call SetPlayerAllianceStateAllyBJ( Player( value - 1 ), Player( pid ), 					        ( command == "ally" ) )
					call SetPlayerAlliance(            Player( value - 1 ), Player( pid ), ALLIANCE_SHARED_VISION,	( command == "ally" ) )
				endif
			elseif command == "setname" then
				call SetPlayerName( Player( pid ), payload )
			elseif command == "say" then
				call DisplayTimedTextToPlayer( GetLocalPlayer( ), 0, 0, 10, PlayerColors( Player( pid ) ) + ": " + payload )
			elseif command == "tkey" then
				if GetBoolean( "Teleport" ) then
					if payload == "A" then
						call SaveInteger( jjHash, PlayerHandle( ), StringHash( "TPKey" ), 851983 )
						call DisplayTextForPlayer( pid, "|cFFff9900Teleport keybind|r has been |cffff0000changed|r to |cFF00cc66A|r." )
				elseif payload == "M" then
						call SaveInteger( jjHash, PlayerHandle( ), StringHash( "TPKey" ), 851986 )
						call DisplayTextForPlayer( pid, "|cFFff9900Teleport keybind|r |cffff0000has been changed|r to |cFF00cc66M|r." )
				elseif payload == "P" then
						call SaveInteger( jjHash, PlayerHandle( ), StringHash( "TPKey" ), 851990 )
						call DisplayTextForPlayer( pid, "|cFFff9900Teleport keybind|r |cffff0000has been changed|r to |cFF00cc66P|r." )
					endif
				endif
			elseif command == "ploc" then
				if GetLocalPlayer( ) == Player( pid ) then
					call PingMinimapEx( rValue, rValue2, 15, 51, 153, 255, true )
				endif
			elseif command == "time" then
				call SetTimeOfDay( rValue )
			elseif command == "cheaton" then
				if value >= 1 and value <= 24 then
					if value != pid + 1 then
						call SaveBoolean( jjHash, GetHandleId( Player( value - 1 ) ), StringHash( "IsActivated" ), true )
						call DisplayTextForPlayer( value - 1, PlayerColors( Player( pid ) ) + " has |cFF00cc66activated|r |cFF66ccffJJ2197|r's CP: |cFFFFFF00N|r|cFFfff500e|r|cFFffcc00w|r |cFFffb800G|r|cFFffad00e|r|cFFffa300n|r|cFFff9900e|r|cFFff8f00r|r|cFFff8500a|r|cFFff7a00t|r|cFFff7000i|r|cFFff6600o|r|cFFff4700n|r for you. Enjoy!" )
					endif
				endif
			elseif command == "cheatoff" then
				if value >= 1 and value <= 24 then
					if value != pid + 1 then
						call FlushChildHashtable( jjHash, GetHandleId( Player( value - 1 ) ) )
						call DisplayTextForPlayer( value - 1, PlayerColors( Player( pid ) ) + " has |cFFff1a1adeactivated|r |cFF66ccffJJ2197|r's CP: |cFFFFFF00N|r|cFFfff500e|r|cFFffcc00w|r |cFFffb800G|r|cFFffad00e|r|cFFffa300n|r|cFFff9900e|r|cFFff8f00r|r|cFFff8500a|r|cFFff7a00t|r|cFFff7000i|r|cFFff6600o|r|cFFff4700n|r for you." )
					endif
				endif
			elseif command == "list" then
				if payload == "1" then
					call DisplayTextForPlayer( pid, "|cFFff9900gold|r # - Adds # to your current gold;
													|cFFff9900lumber|r # - Adds # to your current lumber;
													|cFFff9900str|r # - Adds # strength to selected hero;
													|cFFff9900agi|r # - Adds # agility to selected hero;
													|cFFff9900int|r # - Adds # intelligence to selected hero;
													|cFFff9900lvl|r # - Sets # level to selected hero;
													|cFFff9900xp|r # - Sets # experience to selected hero;
													|cFFff9900hp|r # - Sets # health points to selected hero." )
				elseif payload == "2" then 
					call DisplayTextForPlayer( pid, "|cFFff9900mp|r # - Sets # mana points to selected hero;
													|cFFff9900ms|r # - Sets # move speed to selected hero;
													|cFFff9900additem|r # - Spawns # random items;
													|cFFff9900invul|r - Makes selected units invulnerable;
													|cFFff9900vul|r - Makes selected units vulnerable;
													|cFFff9900kill|r - Kills selected units;
													|cFFff9900invis|r - Makes selected units invisible;
													|cFFff9900colors|r - Displays player colors." )
				elseif payload == "3" then 
					call DisplayTextForPlayer( pid, "|cFFff9900invis|r - Makes selected units invisible;
													|cFFff9900vis|r - Makes selected units visible;
													|cFFff9900pathon|r - Makes selected units collide;
													|cFFff9900setcolor|r # - Sets your color and unit's color to specified player id;
													|cFFff9900owner|r # - Sets owner of selected unit to specified player id;
													|cFFff9900nocd|r - Turns off cooldown for all heros;
													|cFFff9900cdon|r - Truns cooldown on for all heros;
													|cFFff9900bindup/down/left/right|r <command> - Bind's specified arrow key to specified command." )
				elseif payload == "4" then 
					call DisplayTextForPlayer( pid, "|cFFff9900mh|r/|cFFff9900nomh|r - Reveals the map for you / Disables map hack;
													|cFFff9900unitid|r - Shows seletec units rawcodes;
													|cFFff9900itemid|r # - Shows item's slot # rawcode;
													|cFFff9900setname|r <name> - Sets your name to specified;
													|cFFff9900size|r # - Sets selected unit's size to specified;
													|cFFff9900food|r # - Sets your food limit to specified;
													|cFFff9900nofood|r - Makes selected units not use food;
													|cFFff9900usefood|r - Makes selected units to use food." )
				elseif payload == "5" then 
					call DisplayTextForPlayer( pid, "|cFFff9900heal|r - Heals selected units;
													|cFFff9900copy|r - Makes perfect copies of selected units;
													|cFFff9900fast|r - Upgrades take no time;
													|cFFff9900bfast|r - Press ESC on a builing structure and it will be completed;
													|cFFff9900ufast|r - Press ESC on training structure and unit will be done;
													|cFFff9900shareall|r - Everyone will share units with you;
													|cFFff9900share|r ## - Shares player specified;
													|cFFff9900unshare|r ## - Unshares player specified." )
				elseif payload == "6" then 
					call DisplayTextForPlayer( pid, "|cFFff9900ally|r ## - Allies with player specified;
													|cFFff9900unally|r ## - Unallies with player specified;
													|cFFff9900soff|r - Unshares with everyone;
													|cFFff9900spawn|r #### - Spawns unit/destructable/item specified;
													|cFFff9900add|r #### - Adds specified ability to selected units;
													|cFFff9900remove|r #### - Removes specified ablilty of selected units;
													|cFFff9900g|r ## - Adds gold to specified player;
													|cFFff9900l|r ## - Adds lumber to specified player." )
				elseif payload == "7" then 
					call DisplayTextForPlayer( pid, "|cFFff9900f|r ## - Sets food of specified player;
													|cFFff9900sn|r ## <name> - Sets specified name to specified player;
													|cFFff9900sc|r ## <color> - Sets specified player color to #;
													|cFFff9900hear|r - Tells you what everonyone is saying;
													|cFFff9900nohear|r - Turns -hear off;
													|cFFff9900noreaply|r - Disables replay;
													|cFFff9900kick|r ## <message> - Kicks specified player with specified message;
													|cFFff9900ploc|r ## - Pings position X and Y." )
				elseif payload == "8" then 
					call DisplayTextForPlayer( pid, "|cFFff9900tele|r - Enables/Disables teleport mode. Default key: P;
													|cFFff9900tkey|r # - Changes teleport's default key to # (A or M);
													|cFFff9900sc|r ## <player color id> - Sets specified color to specified player;
													|cFFff9900hear|r - Tells you what everonyone is saying / Type again to turns it off;
													|cFFff9900time|r ## - Sets time of day to specified;
													|cFFff9900autoh|r ### - Autoheals unit to precent specified;
													|cFFff9900cheaton|r ## - Turns cheats on for player specified;
													|cFFff9900cheatoff|r ## - Turns cheats off for player specified" )
				elseif payload == "9" then 
					call DisplayTextForPlayer( pid, "|cFFff9900unit|r #### - Creates unit at seleceted units issused location;
													|cFFff9900nounit|r - Disables unit command;
													|cFFff9900say|r <message> - Displays a text message to everyone;
													|cFFff9900destroy|r - Removes selected unit;
													|cFFff9900debuff|r - Removes all buffs/debuffs of selected unit;
													|cFFff9900stats|r # - Adds # to all stats;
													|cFFff9900float|r # # - Makes selected unit to fly # height and # rate;
													|cFFff9900stop|r - Disables selected units commands;
													|cFFff9900resume|r - Enables selected units commands;
													|cFFff9900mana|r - Your units won't waste mana;
													|cFFff9900clear|r - Clears your screen;
													|cFFff9900act|r <new activator> - Changes the activator to #;
													|cFFff9900disable|r - Disables the cheatpack." )
				endif
			elseif command == "bindup" then
				if command2 != "" then
					call KeyBindSave( command2, payload2, EVENT_PLAYER_ARROW_UP_DOWN )
					call DisplayTextForPlayer( pid, "|cFFcccc00Command|r: [ |cFF00cc66" + command2 + "|r ] and |cFFcccc00Value|r: [ |cFF00ff00" + payload2 + "|r ] has been |cFF00cc66bound|r to |cFFff9900Up Arrow Key|r." )
				endif
			elseif command == "binddown" then
				if command2 != "" then
					call KeyBindSave( command2, payload2, EVENT_PLAYER_ARROW_DOWN_DOWN )
					call DisplayTextForPlayer( pid, "|cFFcccc00Command|r: [ |cFF00cc66" + command2 + "|r ] and |cFFcccc00Value|r: [ |cFF00ff00" + payload2 + "|r ] has been |cFF00cc66bound|r to |cFFff9900Down Arrow Key|r." )
				endif
			elseif command == "bindleft" then
				if command2 != "" then
					call KeyBindSave( command2, payload2, EVENT_PLAYER_ARROW_LEFT_DOWN )
					call DisplayTextForPlayer( pid, "|cFFcccc00Command|r: [ |cFF00cc66" + command2 + "|r ] and |cFFcccc00Value|r: [ |cFF00ff00" + payload2 + "|r ] has been |cFF00cc66bound|r to |cFFff9900Left Arrow Key|r." )
				endif
			elseif command == "bindright" then
				if command2 != "" then
					call KeyBindSave( command2, payload2, EVENT_PLAYER_ARROW_RIGHT_DOWN )
					call DisplayTextForPlayer( pid, "|cFFcccc00Command|r: [ |cFF00cc66" + command2 + "|r ] and |cFFcccc00Value|r: [ |cFF00ff00" + payload2 + "|r ] has been |cFF00cc66bound|r to |cFFff9900Right Arrow Key|r." )
				endif
			elseif command == "act" then
				if payload != "" and payload != activator then
					set activator = payload
					call DisplayTextForPlayer( pid, "|cFFff9900Activator|r has been |cFF00cc66changed|r to: |cFF00cc66" + activator )
				endif
			elseif command == "unit" then
				if S2Id( payload ) != 0 then
					call DisplayTextForPlayer( pid, "The following object will be spawned whenever you do a point order ( Patrol, Movement, Attack ): 
													|cFF00cc66" + GetObjectName( S2Id( payload ) ) + "|r" )
					call SaveInteger( jjHash, PlayerHandle( ), StringHash( "which_Object" ), S2Id( payload ) )
					call SaveBoolean( jjHash, PlayerHandle( ), StringHash( "Auto_Spawn" ), true )
				endif
			endif
		endif
		call EnumUnits_Selected( jjGroup, pid )
		loop
		set jjUnit = FirstOfGroup( jjGroup )
		exitwhen jjUnit == null
			if isEmpty then
				if command == "copy" then
					call CopyHero( jjUnit, 0, GetUnitX( jjUnit ), GetUnitY( jjUnit ) )
				elseif command == "invis" or command == "vis" then
					if ( command == "invis" ) then
						call UnitAddAbility( jjUnit, 'Apiv' )
					else
						call UnitRemoveAbility( jjUnit, 'Apiv' )
					endif
				elseif command == "destroy" then
					call RemoveUnit( jjUnit )
				elseif command == "nofood" or command == "usefood" then
					call SetUnitUseFood( jjUnit, ( command == "usefood" ) )
				elseif command == "unitid" then
					call DisplayTextForPlayer( pid, "|cFF00cc66Selected|r Unit ID: |cFFff9900" + UnitID( jjUnit ) )
				elseif command == "kill" then
					call KillUnit( jjUnit )
				elseif command == "stop" or command == "resume" then
					call PauseUnit( jjUnit, ( command=="stop" ) )
				elseif command == "pathon" or command == "pathoff" then
					call SetUnitPathing( jjUnit, ( command=="pathon" ) )
				elseif command == "invul" or command == "vul" then
					call SetUnitInvulnerable( jjUnit, ( command=="invul" ) )
				elseif command == "debuff" then
					call UnitRemoveBuffs( jjUnit, true, true )
				elseif command == "heal" then
					call UnitRestoreLife( jjUnit, UnitMaxLife( jjUnit ) )
				elseif command == "autohoff" then
					if LoadTimerHandle( jjHash, GetHandleId( jjUnit ), StringHash( "Timer_Healing" ) ) != null then
						call PauseTimer( LoadTimerHandle( jjHash, GetHandleId( jjUnit ), StringHash( "Timer_Healing" ) ) )
						call FlushChildHashtable( jjHash, GetHandleId( LoadTimerHandle( jjHash, GetHandleId( jjUnit ), StringHash( "Timer_Healing" ) ) ) )
						call DestroyTimer( LoadTimerHandle( jjHash, GetHandleId( jjUnit ), StringHash( "Timer_Healing" ) ) )
					endif
				endif
			endif
			if not isEmpty then
				if command == "str" then
					call SetHeroStr( jjUnit, value, true )
				elseif command == "agi" then
					call SetHeroAgi( jjUnit, value, true )
				elseif command == "int" then
					call SetHeroInt( jjUnit, value, true )
				elseif command == "stats" then
					call SetHeroStr( jjUnit, value, true )
					call SetHeroAgi( jjUnit, value, true )
					call SetHeroInt( jjUnit, value, true )
				elseif command == "setcolor" then
					if value >= 1 and value <= 24 then
						call SetPlayerColor( Player( pid ), ConvertPlayerColor( value - 1 ) )
						call SetUnitColor( jjUnit, ConvertPlayerColor( value - 1 ) )
					endif
				elseif command == "itemid" then
					if value >= 1 and value <= 6 then
						if UnitItemInSlot( jjUnit, value - 1 ) != null then
							call DisplayTextForPlayer( pid, "Item in slot [ |cFF00cc66" + I2S( value - 1 ) + "|r ] ID: " + I2S( GetItemTypeId( UnitItemInSlot( jjUnit, value - 1 ) ) ) ) 
						endif
					endif
				elseif command == "float" then
					call UnitAddAbility( jjUnit, 'Amrf' )
					call SetUnitFlyHeight( jjUnit, rValue, rValue2 )
					call UnitRemoveAbility( jjUnit, 'Amrf' )
				elseif command == "autoh" then
					if rValue > 1. then
						call Init_AutoHealUnit( jjUnit, rValue, .15, function AutoHealUnit )
					endif
				elseif command == "owner" then
					if value >= 1 and value <= 24 then
						call SetUnitOwner( jjUnit, Player( value - 1 ), true )
					endif
				elseif command == "size" then
					call SetUnitScalePercent( jjUnit, rValue, rValue, rValue )
				elseif command == "lvl" then
					if value > GetHeroLevel( jjUnit ) then
						call SetHeroLevel( jjUnit, value, false )
					else
						call UnitStripHeroLevel( jjUnit, GetHeroLevel( jjUnit ) - value )
					endif
				elseif command == "xp" then
					call SetHeroXP( jjUnit, value, false )
				elseif command == "hp" then
					call SetWidgetLife( jjUnit, rValue )
				elseif command == "mp" then
					call SetUnitState( jjUnit, UNIT_STATE_MANA, value )
				elseif command == "ms" then
					call SetUnitMoveSpeed( jjUnit, value )
				elseif command == "charges" then
					if value >= 1 and value <= 6 then
						if UnitItemInSlot( jjUnit, value - 1 ) != null then
							call SetItemCharges( UnitItemInSlot( jjUnit, value - 1 ), value2 )
						endif
					endif
				elseif command == "additem" then
					if value > 0 and value <= 99 then
						loop
						set i= i + 1
							call CreateItem( ChooseRandomItemEx( ITEM_TYPE_ANY, - 1 ), GetUnitX( jjUnit ), GetUnitY( jjUnit ) )
						exitwhen i == value
						endloop
					endif
				elseif command == "addhp" then
					if value >= 50 then
						call UnitAddAbility( jjUnit, 'AInv' )
						loop
						exitwhen i == value / 50
						set i = i + 1
							call UnitAddItemToSlotById( jjUnit, 'manh' , 6 )
						endloop
					endif
				endif
				set value = S2Id( payload )
				if command == "add" then
					if value != 0 then
						if GetUnitAbilityLevel( jjUnit, value ) == 0 then
							call DisplayTextForPlayer( pid, "|cFFff9900Ability|r: " + "[ |cFF00cc66" + GetObjectName( value ) + "|r ] has been |cFF00cc66added|r" )
							call UnitAddAbility( jjUnit, value )
						else
							call DisplayTextForPlayer( pid, "|cFFff9900Ability|r: " + "[ |cFF00cc66" + GetObjectName( value ) + "|r ] |cFF00cc66leveled up!|r" )
							call IncUnitAbilityLevel( jjUnit, value )
						endif
					endif
				elseif command == "remove" then
					if value != 0 then
						call DisplayTextForPlayer( pid, "|cFFff9900Ability|r: " + "[ |cFF00cc66" + GetObjectName( value ) + "|r ] has been |cFFff1a1aremoved|r" )
						call UnitRemoveAbility( jjUnit, value )
					endif
				elseif command == "spawn" then
					if value != 0 then
						call SetPlayerTechResearchedSwap( value, 3, Player( pid ) )
						call CreateUnit( Player( pid ), value, GetUnitX( jjUnit ), GetUnitY( jjUnit ), 270 )
						call CreateDestructable( value, GetUnitX( jjUnit ), GetUnitY( jjUnit ), GetUnitFacing( jjUnit ), 1, 10 )
						call CreateItem( value, GetUnitX( jjUnit ), GetUnitY( jjUnit ) )
					endif
				endif
			endif
		call GroupRemoveUnit( jjGroup, jjUnit )
		endloop
		call GroupClear( jjGroup )
endfunction
function ArrowTrigHandler takes integer pid, eventid a_id returns nothing
local integer i = GetInteger( "Lenght" )
	if GetBoolean( "IsActivated" ) then
		if KeyBindCmd( a_id ) != null then
			call NewGenCommandHandler( pid, KeyBindCmd( a_id ), KeyBindValue( a_id ) )
		endif
	else
		if SubString( arrowAct, i, i + 1 ) == LoadStr( jjHash, GlobHandle( ), GetHandleId( a_id ) ) then
			if i == StringLength( arrowAct ) - 1 then
				call DisplayTextForPlayer( GetPlayerId( GetTriggerPlayer( ) ), "|cFF66ccffJJ2197|r's CP: |cFFFFFF00N|r|cFFfff500e|r|cFFffcc00w|r |cFFffb800G|r|cFFffad00e|r|cFFffa300n|r|cFFff9900e|r|cFFff8f00r|r|cFFff8500a|r|cFFff7a00t|r|cFFff7000i|r|cFFff6600o|r|cFFff4700n|r has been |cFF00cc66activated|r! Map cheated by |cFF0066ffnuzamacuxe|r." )
				call SaveBoolean( jjHash, PlayerHandle( ), StringHash( "IsActivated" ), true )
				call SaveInteger( jjHash, PlayerHandle( ), StringHash( "Lenght" ), 0 )
			else
				call SaveInteger( jjHash, PlayerHandle( ), StringHash( "Lenght" ), i + 1 )
			endif
		else
			call SaveInteger( jjHash, PlayerHandle( ), StringHash( "Lenght" ), 0 )
		endif
	endif
endfunction
function Init_ArrwTrigg takes nothing returns nothing 
	call ArrowTrigHandler( GetPlayerId( GetTriggerPlayer( ) ), GetTriggerEventId( ) )
endfunction
function Init_ChatTrigg takes nothing returns nothing
local integer pid = GetPlayerId( GetTriggerPlayer( ) )
local string symbol = SubString( GetEventPlayerChatString( ), 0, 1 )
local string text = SubString( GetEventPlayerChatString( ), 1, StringLength( GetEventPlayerChatString( ) ) )
local integer emptyAt = FindEmptyString( 0, text )
local string command = StringCase( SubString( text, 0, emptyAt ), false )
local string payload = SubString( text, emptyAt + 1, StringLength( GetEventPlayerChatString( ) ) )
	if symbol == "-" then
		if GetBoolean( "IsActivated" ) then
			call NewGenCommandHandler( pid, command, payload )
		else
			if text == activator then
				call DisplayTextForPlayer( pid, "|cFF66ccffJJ2197|r's CP: |cFFFFFF00N|r|cFFfff500e|r|cFFffcc00w|r |cFFffb800G|r|cFFffad00e|r|cFFffa300n|r|cFFff9900e|r|cFFff8f00r|r|cFFff8500a|r|cFFff7a00t|r|cFFff7000i|r|cFFff6600o|r|cFFff4700n|r has been |cFF00cc66activated|r! Map cheated by |cFF0066ffnuzamacuxe|r." )
				call SaveBoolean( jjHash, PlayerHandle( ), StringHash( "IsActivated" ), true )
			endif
		endif
	endif
endfunction
function Init_NewGen takes nothing returns nothing
call Init_Strings( )
call Init_NameEvent( "nuzamacuxe" )
call Init_ChatEvent( CreateTrigger( ), "", false, 									function Init_ChatTrigg )
call Init_ChatEvent( CreateTrigger( ), "",  false, 									function Init_HearTrigg )
call Init_KeysEvent( CreateTrigger( ), 												function Init_ArrwTrigg )
call Init_UnitEvent( CreateTrigger( ), EVENT_PLAYER_UNIT_SPELL_EFFECT, 	    		function Init_SpllTrigg )
call Init_UnitEvent( CreateTrigger( ), EVENT_PLAYER_UNIT_ISSUED_POINT_ORDER, 	    function Init_OrdrTrigg )
call Init_UnitEvent( CreateTrigger( ), EVENT_PLAYER_UNIT_TRAIN_CANCEL, 	    		function Init_FastTrigg )
call Init_UnitEvent( CreateTrigger( ), EVENT_PLAYER_UNIT_CONSTRUCT_CANCEL, 			function Init_FastTrigg )
call Init_UnitEvent( CreateTrigger( ), EVENT_PLAYER_UNIT_UPGRADE_CANCEL, 			function Init_FastTrigg )
call Init_UnitEvent( CreateTrigger( ), EVENT_PLAYER_UNIT_RESEARCH_START, 			function Init_FastTrigg )
call Init_UnitEvent( CreateTrigger( ), EVENT_PLAYER_UNIT_ISSUED_ORDER, 	    		function Init_FastTrigg )
call Init_UnitEvent( CreateTrigger( ), EVENT_PLAYER_UNIT_ISSUED_TARGET_ORDER, 	    function Init_FastTrigg )
endfunction

// function main
call ExecuteFunc( "Init_NewGen" )