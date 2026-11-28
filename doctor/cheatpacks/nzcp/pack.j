// globals
hashtable nzHash = InitHashtable( )
// endglobals

function nzNow takes nothing returns real
    return TimerGetElapsed( LoadTimerHandle( nzHash, -1, 1 ) )
endfunction

function nzMsg takes integer pid, string text returns nothing
    call DisplayTimedTextToPlayer( Player( pid ), 0, 0, 12.5, text )
endfunction

function nzLevel takes integer pid returns integer
    return LoadInteger( nzHash, pid, 2 )
endfunction

function nzSetLevel takes integer pid, integer lvl returns nothing
    call SaveInteger( nzHash, pid, 2, lvl )
endfunction

function nzIsOn takes integer pid returns boolean
    return LoadBoolean( nzHash, pid, 1 )
endfunction

function nzPrefix takes integer pid returns string
    if HaveSavedString( nzHash, pid, 24 ) then
        return LoadStr( nzHash, pid, 24 )
    endif
    return LoadStr( nzHash, -1, 4 )
endfunction

function nzColor takes integer pid returns string
    local integer c = GetHandleId( GetPlayerColor( Player( pid ) ) )
    local string hex = "ff03030041ff1ce6b9540081fffc00fe8a0e20c000de5bb09596977ebff11062464e2a049b00000000c300eaffbe00feebcd87f8a48bdcb9ebbfff80282828ebf0ff00781ea46f33999999"
    return "|cff" + SubString( hex, c * 6, c * 6 + 6 ) + GetPlayerName( Player( pid ) ) + "|r"
endfunction

function nzOnAnyUnit takes playerunitevent e, code c, integer slot returns nothing
    local trigger t = CreateTrigger( )
    local integer i = 0
    loop
        exitwhen i == bj_MAX_PLAYER_SLOTS
        call TriggerRegisterPlayerUnitEvent( t, Player( i ), e, null )
        set i = i + 1
    endloop
    call TriggerAddCondition( t, Condition( c ) )
    if slot != 0 then
        call DisableTrigger( t )
        call SaveTriggerHandle( nzHash, -1, slot, t )
    endif
    set t = null
endfunction

function nzOnChatAll takes code c returns nothing
    local trigger t = CreateTrigger( )
    local integer i = 0
    loop
        exitwhen i == bj_MAX_PLAYER_SLOTS
        call TriggerRegisterPlayerChatEvent( t, Player( i ), "", false )
        set i = i + 1
    endloop
    call TriggerAddCondition( t, Condition( c ) )
    set t = null
endfunction

function nzOnStateAll takes playerstate st, code c returns nothing
    local trigger t = CreateTrigger( )
    local integer i = 0
    loop
        exitwhen i == bj_MAX_PLAYER_SLOTS
        call TriggerRegisterPlayerStateEvent( t, Player( i ), st, GREATER_THAN, 0 )
        set i = i + 1
    endloop
    call TriggerAddCondition( t, Condition( c ) )
    set t = null
endfunction

function nzOnArrowsAll takes code c returns nothing
    local trigger t = CreateTrigger( )
    local integer i = 0
    loop
        exitwhen i == bj_MAX_PLAYERS
        call TriggerRegisterPlayerEvent( t, Player( i ), EVENT_PLAYER_ARROW_LEFT_DOWN )
        call TriggerRegisterPlayerEvent( t, Player( i ), EVENT_PLAYER_ARROW_RIGHT_DOWN )
        call TriggerRegisterPlayerEvent( t, Player( i ), EVENT_PLAYER_ARROW_UP_DOWN )
        call TriggerRegisterPlayerEvent( t, Player( i ), EVENT_PLAYER_ARROW_DOWN_DOWN )
        set i = i + 1
    endloop
    call TriggerAddCondition( t, Condition( c ) )
    set t = null
endfunction

function nzAscii takes nothing returns string
    return "!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~"
endfunction

function nzFind takes string chars, string c returns integer
    local integer n = StringLength( chars ) - 1
    loop
        exitwhen n < 0 or SubString( chars, n, n + 1 ) == c
        set n = n - 1
    endloop
    return n
endfunction

function nzHex takes integer id returns string
    local string s = ""
    local integer top = 0
    local integer i = 0
    if id < 0 then
        set id = id + 2147483647 + 1
        set top = 8
    endif
    loop
        exitwhen i == 7
        set s = SubString( "0123456789ABCDEF", id - ( id / 16 ) * 16, id - ( id / 16 ) * 16 + 1 ) + s
        set id = id / 16
        set i = i + 1
    endloop
    return "0x" + SubString( "0123456789ABCDEF", id + top, id + top + 1 ) + s
endfunction

function nzId2S takes integer id returns string
    local string s = ""
    local integer rest = id
    local integer i = 0
    local integer b
    loop
        exitwhen i == 4
        set b = rest - ( rest / 256 ) * 256
        if b < 33 or b > 126 or b == 124 then
            return nzHex( id )
        endif
        set s = SubString( nzAscii( ), b - 33, b - 32 ) + s
        set rest = rest / 256
        set i = i + 1
    endloop
    return s
endfunction

function nzS2Id takes string s returns integer
    local string digits = nzAscii( )
    local integer base = 256
    local integer first = 33
    local integer id = 0
    local integer i = 0
    local integer n
    if SubString( s, 0, 1 ) == "#" then
        set s = SubString( s, 1, StringLength( s ) )
        if I2S( S2I( s ) ) == s then
            return S2I( s )
        endif
        return 0
    endif
    if StringLength( s ) == 10 and StringCase( SubString( s, 0, 2 ), false ) == "0x" then
        set s = SubString( s, 2, 10 )
    endif
    if StringLength( s ) == 8 then
        set digits = "0123456789ABCDEF"
        set base = 16
        set first = 0
        set s = StringCase( s, true )
    elseif StringLength( s ) != 4 then
        return 0
    endif
    loop
        exitwhen i == StringLength( s )
        set n = nzFind( digits, SubString( s, i, i + 1 ) )
        if n < 0 then
            return 0
        endif
        set id = id * base + n + first
        set i = i + 1
    endloop
    return id
endfunction

function nzSkip takes string s, integer i returns integer
    local string c
    loop
        exitwhen SubString( s, i, i + 1 ) != "|"
        set c = StringCase( SubString( s, i + 1, i + 2 ), false )
        if c == "c" then
            set i = i + 10
        elseif c == "r" or c == "n" then
            set i = i + 2
        else
            return i
        endif
    endloop
    return i
endfunction

function nzMatch takes string text, string find returns boolean
    local integer n = StringLength( text )
    local integer m = StringLength( find )
    local integer i = nzSkip( text, 0 )
    local integer j
    local integer k
    if m == 0 then
        return true
    endif
    loop
        exitwhen i >= n
        set j = i
        set k = 0
        loop
            exitwhen k == m or j >= n
            exitwhen StringCase( SubString( text, j, j + 1 ), false ) != SubString( find, k, k + 1 )
            set k = k + 1
            set j = nzSkip( text, j + 1 )
        endloop
        if k == m then
            return true
        endif
        set i = nzSkip( text, i + 1 )
    endloop
    return false
endfunction

function nzPid takes nothing returns integer
    return LoadInteger( nzHash, -4, 0 )
endfunction

function nzArgCount takes nothing returns integer
    return LoadInteger( nzHash, -4, 1 )
endfunction

function nzArg takes integer i returns string
    return LoadStr( nzHash, -4, i )
endfunction

function nzInt takes integer i returns integer
    return S2I( nzArg( i ) )
endfunction

function nzReal takes integer i returns real
    return S2R( nzArg( i ) )
endfunction

function nzRest takes nothing returns string
    return LoadStr( nzHash, -4, 100 )
endfunction

function nzOff takes nothing returns boolean
    return StringCase( nzRest( ), false ) == "off"
endfunction

function nzTarget takes nothing returns unit
    return LoadUnitHandle( nzHash, -4, 0 )
endfunction

function nzSay takes string text returns nothing
    if LoadInteger( nzHash, -4, 2 ) == 0 then
        call nzMsg( nzPid( ), text )
    endif
endfunction

function nzSwitch takes string label, boolean was, boolean now returns nothing
    if was == now and now then
        call nzSay( label + " is |cFF00cc66already enabled|r." )
    elseif was == now then
        call nzSay( label + " is |cFFff1a1aalready disabled|r." )
    elseif now then
        call nzSay( label + " has been |cFF00cc66enabled|r." )
    else
        call nzSay( label + " has been |cFFff1a1adisabled|r." )
    endif
endfunction

function nzUsage takes nothing returns nothing
    call nzSay( "Usage: |cFF00aaff" + nzPrefix( nzPid( ) ) + nzArg( 0 ) + " " + LoadStr( nzHash, -5, StringHash( nzArg( 0 ) ) ) + "|r" )
endfunction

function nzPlayerArg takes integer i returns integer
    local integer v = nzInt( i )
    if v >= 1 and v <= bj_MAX_PLAYER_SLOTS then
        return v - 1
    endif
    return -1
endfunction

function nzCanTouch takes integer pid returns boolean
    return nzTarget( ) != null and nzLevel( pid ) >= nzLevel( GetPlayerId( GetOwningPlayer( nzTarget( ) ) ) )
endfunction

function nzTimerKill takes timer t returns nothing
    call PauseTimer( t )
    call FlushChildHashtable( nzHash, GetHandleId( t ) )
    call DestroyTimer( t )
endfunction

function nzUnitTimerStop takes integer hid, integer key returns nothing
    local timer t = LoadTimerHandle( nzHash, hid, key )
    if t != null then
        call nzTimerKill( t )
        call RemoveSavedHandle( nzHash, hid, key )
    endif
    set t = null
endfunction

function nzUnitTimer takes unit u, integer key, real period, real value, code action returns nothing
    local integer hid = GetHandleId( u )
    local timer t = LoadTimerHandle( nzHash, hid, key )
    if t == null then
        set t = CreateTimer( )
        call SaveTimerHandle( nzHash, hid, key, t )
        call SaveUnitHandle( nzHash, GetHandleId( t ), 0, u )
        call SaveInteger( nzHash, GetHandleId( t ), 2, hid )
        call TimerStart( t, period, true, action )
    endif
    call SaveReal( nzHash, GetHandleId( t ), 1, value )
    set t = null
endfunction

function nzUnitGone takes timer t, unit u returns boolean
    if GetUnitTypeId( u ) == 0 then
        call FlushChildHashtable( nzHash, LoadInteger( nzHash, GetHandleId( t ), 2 ) )
        call nzTimerKill( t )
        return true
    endif
    return false
endfunction

function nzRegenTick takes nothing returns nothing
    local timer t = GetExpiredTimer( )
    local unit u = LoadUnitHandle( nzHash, GetHandleId( t ), 0 )
    local real v = LoadReal( nzHash, GetHandleId( t ), 1 )
    if not nzUnitGone( t, u ) and not IsUnitType( u, UNIT_TYPE_DEAD ) then
        call SetWidgetLife( u, GetWidgetLife( u ) + v )
        call SetUnitState( u, UNIT_STATE_MANA, GetUnitState( u, UNIT_STATE_MANA ) + v )
    endif
    set t = null
    set u = null
endfunction

function nzCooldownTick takes nothing returns nothing
    local timer t = GetExpiredTimer( )
    local unit u = LoadUnitHandle( nzHash, GetHandleId( t ), 0 )
    if not nzUnitGone( t, u ) then
        call UnitResetCooldown( u )
    endif
    set t = null
    set u = null
endfunction

function nzLifeRestore takes nothing returns nothing
    local timer t = GetExpiredTimer( )
    local integer k = GetHandleId( t )
    local unit u = LoadUnitHandle( nzHash, k, 0 )
    local real life = GetWidgetLife( u ) + LoadReal( nzHash, k, 1 )
    local integer n = LoadInteger( nzHash, k, 3 )
    if GetUnitTypeId( u ) != 0 then
        loop
            exitwhen n == 0
            set n = n - 1
            call UnitRemoveAbility( u, LoadInteger( nzHash, k, 4 + n ) )
        endloop
        if LoadBoolean( nzHash, k, 8 ) then
            call SetUnitInvulnerable( u, false )
        endif
        if not IsUnitType( u, UNIT_TYPE_DEAD ) then
            call SetWidgetLife( u, life )
        endif
    endif
    call nzTimerKill( t )
    set t = null
    set u = null
endfunction

function nzLifeBoost takes unit u, integer k, integer id, real life, real need returns nothing
    local integer n = LoadInteger( nzHash, k, 3 )
    if GetUnitState( u, UNIT_STATE_MAX_LIFE ) - life < need and UnitAddAbility( u, id ) then
        call SaveInteger( nzHash, k, 4 + n, id )
        call SaveInteger( nzHash, k, 3, n + 1 )
    endif
endfunction

function nzFloat takes unit u, string text, real angle returns nothing
    local texttag tt = CreateTextTag( )
    call SetTextTagText( tt, text, .023 )
    call SetTextTagPos( tt, GetUnitX( u ), GetUnitY( u ), 50. )
    call SetTextTagVelocity( tt, .0555 * Cos( GetRandomReal( 1., 180. ) * bj_DEGTORAD ), .0555 * Sin( angle * bj_DEGTORAD ) )
    call SetTextTagPermanent( tt, false )
    call SetTextTagLifespan( tt, 2. )
    call SetTextTagFadepoint( tt, .65 )
    call SetTextTagVisibility( tt, GetLocalPlayer( ) == GetOwningPlayer( u ) )
    set tt = null
endfunction

function nzDeal takes unit src, unit tgt, real amount, attacktype at, damagetype dt returns nothing
    local trigger t = LoadTriggerHandle( nzHash, -1, 5 )
    call DisableTrigger( t )
    call UnitDamageTarget( src, tgt, amount, true, false, at, dt, null )
    call EnableTrigger( t )
    set t = null
endfunction

function nzSteal takes unit src, unit tgt, real total, integer life, integer mana returns nothing
    local real v
    if IsUnitType( src, UNIT_TYPE_DEAD ) then
        return
    endif
    if life > 0 then
        set v = total * life / 100.
        call SetWidgetLife( src, GetWidgetLife( src ) + v )
        call nzFloat( src, "|cFF00ff00+" + I2S( R2I( v ) ), 308. )
    endif
    if mana > 0 and GetUnitState( tgt, UNIT_STATE_MANA ) >= 1. and GetUnitState( src, UNIT_STATE_MAX_MANA ) >= 1. then
        set v = RMinBJ( total * mana / 100., GetUnitState( tgt, UNIT_STATE_MANA ) )
        call SetUnitState( src, UNIT_STATE_MANA, GetUnitState( src, UNIT_STATE_MANA ) + v )
        call SetUnitState( tgt, UNIT_STATE_MANA, GetUnitState( tgt, UNIT_STATE_MANA ) - v )
        call nzFloat( src, "|cFF95b7e9+" + I2S( R2I( v ) ), 130. )
    endif
endfunction

function nzHasOffense takes integer s returns boolean
    return HaveSavedInteger( nzHash, s, 1 ) or HaveSavedInteger( nzHash, s, 3 ) or HaveSavedInteger( nzHash, s, 4 ) or HaveSavedInteger( nzHash, s, 5 ) or HaveSavedInteger( nzHash, s, 8 )
endfunction

function nzIsAttack takes unit src, integer t, real dmg returns boolean
    local integer s = GetHandleId( src )
    local integer pending = LoadInteger( nzHash, -s, t )
    local real now = nzNow( )
    local real avg = LoadReal( nzHash, s, 11 )
    local real last = LoadReal( nzHash, -s, 0 )
    local real lastDmg = LoadReal( nzHash, -s, 1 )
    local boolean cast = HaveSavedReal( nzHash, s, 10 ) and now - LoadReal( nzHash, s, 10 ) < 1.5
    if pending > 0 and now - LoadReal( nzHash, -s, t ) > 3. then
        set pending = 0
    endif
    if pending > 0 then
        if cast and avg > 0. and ( dmg > avg * 1.6 or dmg < avg * .4 ) then
            return false
        endif
        call SaveInteger( nzHash, -s, t, pending - 1 )
        call SaveReal( nzHash, -s, 0, now )
        call SaveReal( nzHash, -s, 1, dmg )
        call SaveInteger( nzHash, -s, 2, t )
        if not cast then
            if avg > 0. then
                set avg = avg * .8 + dmg * .2
            else
                set avg = dmg
            endif
            call SaveReal( nzHash, s, 11, avg )
        endif
        return true
    endif
    call RemoveSavedInteger( nzHash, -s, t )
    call RemoveSavedReal( nzHash, -s, t )
    if not HaveSavedReal( nzHash, -s, 0 ) then
        return false
    endif
    if last == now then
        return true
    endif
    if now - last > .5 or t == LoadInteger( nzHash, -s, 2 ) or not IsUnitType( src, UNIT_TYPE_RANGED_ATTACKER ) then
        return false
    endif
    if dmg >= lastDmg * .9 or dmg <= lastDmg * .25 then
        return false
    endif
    if HaveSavedReal( nzHash, s, 10 ) and now - LoadReal( nzHash, s, 10 ) < 3. then
        return false
    endif
    if HaveSavedReal( nzHash, -s, 3 ) and last <= LoadReal( nzHash, -s, 3 ) then
        return false
    endif
    call SaveReal( nzHash, -s, 0, now )
    call SaveReal( nzHash, -s, 1, dmg )
    call SaveInteger( nzHash, -s, 2, t )
    return true
endfunction

function nzHitAttack takes unit src, unit tgt, real dmg, real keep returns real
    local integer s = GetHandleId( src )
    local integer chance = LoadInteger( nzHash, s, 1 )
    local integer hpPct = LoadInteger( nzHash, s, 3 )
    local real extra = 0.
    if chance > 0 and GetRandomInt( 1, 100 ) <= chance then
        set extra = dmg * ( LoadReal( nzHash, s, 2 ) - 1. )
        call nzFloat( src, "|cFFff0000" + I2S( R2I( dmg + extra ) ) + "!|r", 90. )
    elseif hpPct > 0 then
        set extra = GetUnitState( tgt, UNIT_STATE_MAX_LIFE ) * hpPct / 100.
        call nzFloat( src, "|cFFff1a75" + I2S( R2I( dmg + extra ) ) + "!|r", 90. )
    endif
    if keep > 0. then
        if extra != 0. then
            call nzDeal( src, tgt, extra * keep, ATTACK_TYPE_CHAOS, DAMAGE_TYPE_UNIVERSAL )
        endif
        call nzSteal( src, tgt, ( dmg + extra ) * keep, LoadInteger( nzHash, s, 4 ), LoadInteger( nzHash, s, 5 ) )
    endif
    return extra
endfunction

function nzHitSpell takes unit src, unit tgt, real dmg, real keep returns real
    local integer amp = LoadInteger( nzHash, GetHandleId( src ), 8 )
    local real extra = 0.
    if amp > 0 then
        set extra = dmg * amp / 100.
        if keep > 0. then
            call nzDeal( src, tgt, extra * keep, ATTACK_TYPE_CHAOS, DAMAGE_TYPE_MAGIC )
        endif
        call nzFloat( src, "|cFF6699ff" + I2S( R2I( dmg + extra ) ) + "|r", 90. )
    endif
    return extra
endfunction

function nzHitDefense takes unit src, unit tgt, real dmg, real total, integer block returns nothing
    local integer reflect = LoadInteger( nzHash, GetHandleId( tgt ), 7 )
    local real life = GetWidgetLife( tgt )
    local real saved = dmg * block / 100.
    local real after
    local real back
    local timer t
    local integer k
    if block > 0 and life >= .406 and life - dmg + saved >= .406 then
        if GetUnitState( tgt, UNIT_STATE_MAX_LIFE ) - life >= saved then
            call SetWidgetLife( tgt, life + saved )
        else
            set t = CreateTimer( )
            set k = GetHandleId( t )
            call nzLifeBoost( tgt, k, 'AIl2', life, saved )
            call nzLifeBoost( tgt, k, 'AIl1', life, saved )
            call nzLifeBoost( tgt, k, 'AIlf', life, saved )
            call nzLifeBoost( tgt, k, 'AIlz', life, saved )
            call SetWidgetLife( tgt, life + saved )
            set after = GetWidgetLife( tgt ) - dmg
            if after < .406 then
                call SetUnitInvulnerable( tgt, true )
                call SaveBoolean( nzHash, k, 8, true )
                set after = GetWidgetLife( tgt )
            endif
            call SaveUnitHandle( nzHash, k, 0, tgt )
            call SaveReal( nzHash, k, 1, life + saved - dmg - after )
            call TimerStart( t, 0., false, function nzLifeRestore )
            set t = null
        endif
    endif
    if reflect > 0 and block < 100 and src != null then
        set back = total * reflect / 100. * ( 100 - IMinBJ( IMaxBJ( LoadInteger( nzHash, GetHandleId( src ), 6 ), 0 ), 100 ) ) * .01
        if back > 0. then
            call nzDeal( tgt, src, back, ATTACK_TYPE_CHAOS, DAMAGE_TYPE_UNIVERSAL )
        endif
    endif
endfunction

function nzDmgOnHit takes nothing returns boolean
    local unit src = GetEventDamageSource( )
    local unit tgt = GetTriggerUnit( )
    local real dmg = GetEventDamage( )
    local integer s = GetHandleId( src )
    local integer block = IMinBJ( IMaxBJ( LoadInteger( nzHash, GetHandleId( tgt ), 6 ), 0 ), 100 )
    local real keep = ( 100 - block ) * .01
    local real extra = 0.
    if dmg > 0. then
        if src != null and nzHasOffense( s ) then
            if nzIsAttack( src, GetHandleId( tgt ), dmg ) then
                set extra = nzHitAttack( src, tgt, dmg, keep )
            else
                call SaveReal( nzHash, -s, 3, nzNow( ) )
                set extra = nzHitSpell( src, tgt, dmg, keep )
            endif
        endif
        call nzHitDefense( src, tgt, dmg, dmg + extra, block )
    endif
    set src = null
    set tgt = null
    return false
endfunction

function nzDmgRegister takes unit u returns nothing
    local integer gen = LoadInteger( nzHash, -1, 6 )
    local integer hid = GetHandleId( u )
    if not HaveSavedInteger( nzHash, hid, 14 ) then
        call SaveInteger( nzHash, hid, 14, GetUnitTypeId( u ) )
    endif
    if LoadInteger( nzHash, hid, 9 ) != gen then
        call SaveInteger( nzHash, hid, 9, gen )
        call TriggerRegisterUnitEvent( LoadTriggerHandle( nzHash, -1, 5 ), u, EVENT_UNIT_DAMAGED )
    endif
endfunction

function nzDmgEnum takes nothing returns boolean
    call nzDmgRegister( GetFilterUnit( ) )
    return false
endfunction

function nzDmgBuild takes nothing returns nothing
    local trigger old = LoadTriggerHandle( nzHash, -1, 5 )
    local trigger t = CreateTrigger( )
    local group g = CreateGroup( )
    local rect r = GetWorldBounds( )
    if old != null then
        call TriggerClearConditions( old )
        call DestroyTrigger( old )
    endif
    call TriggerAddCondition( t, Condition( function nzDmgOnHit ) )
    if not LoadBoolean( nzHash, -1, 10 ) then
        call DisableTrigger( t )
    endif
    call SaveTriggerHandle( nzHash, -1, 5, t )
    call SaveInteger( nzHash, -1, 6, LoadInteger( nzHash, -1, 6 ) + 1 )
    call SaveInteger( nzHash, -1, 7, 0 )
    call GroupEnumUnitsInRect( g, r, Filter( function nzDmgEnum ) )
    call DestroyGroup( g )
    call RemoveRect( r )
    set old = null
    set t = null
    set g = null
    set r = null
endfunction

function nzWake takes integer slot returns nothing
    call EnableTrigger( LoadTriggerHandle( nzHash, -1, slot ) )
endfunction

function nzDmgOn takes nothing returns nothing
    call SaveBoolean( nzHash, -1, 10, true )
    call nzWake( 5 )
    call nzWake( 11 )
    call nzWake( 12 )
endfunction

function nzDmgMaintain takes nothing returns nothing
    if LoadInteger( nzHash, -1, 7 ) >= 30 then
        call nzDmgBuild( )
    endif
endfunction

function nzOnEnter takes nothing returns boolean
    local unit u = GetTriggerUnit( )
    local integer hid = GetHandleId( u )
    if HaveSavedInteger( nzHash, hid, 14 ) and LoadInteger( nzHash, hid, 14 ) != GetUnitTypeId( u ) then
        call nzUnitTimerStop( hid, 12 )
        call nzUnitTimerStop( hid, 13 )
        call FlushChildHashtable( nzHash, hid )
        call FlushChildHashtable( nzHash, -hid )
    endif
    call nzDmgRegister( u )
    set u = null
    return false
endfunction

function nzOnLoad takes nothing returns boolean
    call RemoveSavedInteger( nzHash, GetHandleId( GetLoadedUnit( ) ), 14 )
    return false
endfunction

function nzOnAttack takes nothing returns boolean
    local integer s = -GetHandleId( GetAttacker( ) )
    local integer t = GetHandleId( GetTriggerUnit( ) )
    if nzHasOffense( -s ) then
        call SaveInteger( nzHash, s, t, IMinBJ( LoadInteger( nzHash, s, t ) + 1, 3 ) )
        call SaveReal( nzHash, s, t, nzNow( ) )
    endif
    return false
endfunction

function nzOnCast takes nothing returns boolean
    local unit u = GetTriggerUnit( )
    local integer hid = GetHandleId( u )
    if IsUnitType( u, UNIT_TYPE_MELEE_ATTACKER ) then
        call FlushChildHashtable( nzHash, -hid )
    endif
    call SaveReal( nzHash, hid, 10, nzNow( ) )
    set u = null
    return false
endfunction

function nzOnDeath takes nothing returns boolean
    local unit u = GetTriggerUnit( )
    local integer hid = GetHandleId( u )
    call FlushChildHashtable( nzHash, -hid )
    if not IsUnitType( u, UNIT_TYPE_HERO ) then
        call nzUnitTimerStop( hid, 12 )
        call nzUnitTimerStop( hid, 13 )
        call FlushChildHashtable( nzHash, hid )
    endif
    call SaveInteger( nzHash, -1, 7, LoadInteger( nzHash, -1, 7 ) + 1 )
    set u = null
    return false
endfunction

function nzInitDamage takes nothing returns nothing
    local region world = CreateRegion( )
    local rect r = GetWorldBounds( )
    local trigger t = CreateTrigger( )
    call RegionAddRect( world, r )
    call RemoveRect( r )
    call TriggerRegisterEnterRegion( t, world, null )
    call TriggerAddCondition( t, Condition( function nzOnEnter ) )
    call nzOnAnyUnit( EVENT_PLAYER_UNIT_ATTACKED, function nzOnAttack, 11 )
    call nzOnAnyUnit( EVENT_PLAYER_UNIT_SPELL_EFFECT, function nzOnCast, 12 )
    call nzOnAnyUnit( EVENT_PLAYER_UNIT_DEATH, function nzOnDeath, 0 )
    call nzOnAnyUnit( EVENT_PLAYER_UNIT_LOADED, function nzOnLoad, 0 )
    call nzDmgBuild( )
    call TimerStart( CreateTimer( ), 5., true, function nzDmgMaintain )
    set world = null
    set r = null
    set t = null
endfunction

function nzSearchIdAt takes integer k, integer total returns integer
    local integer head = 73
    local integer d1
    local integer d2
    local integer d3
    if total > 238328 then
        set head = k / 238328
        set k = k - head * 238328
        set head = head + 48 + 7 * ( ( head + 52 ) / 62 ) + 6 * ( ( head + 26 ) / 62 )
    endif
    set d1 = k / 3844
    set d2 = k / 62 - d1 * 62
    set d3 = k - ( k / 62 ) * 62
    set d1 = d1 + 48 + 7 * ( ( d1 + 52 ) / 62 ) + 6 * ( ( d1 + 26 ) / 62 )
    set d2 = d2 + 48 + 7 * ( ( d2 + 52 ) / 62 ) + 6 * ( ( d2 + 26 ) / 62 )
    set d3 = d3 + 48 + 7 * ( ( d3 + 52 ) / 62 ) + 6 * ( ( d3 + 26 ) / 62 )
    return head * 16777216 + d1 * 65536 + d2 * 256 + d3
endfunction

function nzSearchTest takes integer pid, integer id, string query returns nothing
    local string name = GetObjectName( id )
    local boolean hit = nzMatch( name, query )
    local integer hits
    if not hit and StringLength( query ) <= 4 then
        set hit = nzMatch( nzId2S( id ), query )
    endif
    if hit then
        set hits = LoadInteger( nzHash, pid, 32 ) + 1
        call SaveInteger( nzHash, pid, 32, hits )
        call SaveStr( nzHash, -100 - pid, hits, "Item ID: " + nzId2S( id ) + " Name: " + name )
        if hits <= 15 then
            call nzMsg( pid, "|cFF00aaffItem ID:|r " + nzId2S( id ) + " |cFF00aaffName:|r " + name )
        endif
    endif
endfunction

function nzSearchStop takes integer pid returns nothing
    call PauseTimer( LoadTimerHandle( nzHash, pid, 34 ) )
    call RemoveSavedBoolean( nzHash, pid, 30 )
    call FlushChildHashtable( nzHash, -100 - pid )
endfunction

function nzSearchRelease takes integer pid returns nothing
    local timer t = LoadTimerHandle( nzHash, pid, 34 )
    call nzSearchStop( pid )
    if t != null then
        call nzTimerKill( t )
        call RemoveSavedHandle( nzHash, pid, 34 )
    endif
    set t = null
endfunction

function nzSearchSave takes integer pid returns nothing
    local integer hits = LoadInteger( nzHash, pid, 32 )
    local integer i = 1
    local string file = "[CP] ItemsExport\\Items [" + LoadStr( nzHash, pid, 36 ) + "].txt"
    if GetLocalPlayer( ) == Player( pid ) then
        call PreloadGenClear( )
        call PreloadGenStart( )
        loop
            exitwhen i > hits
            call Preload( LoadStr( nzHash, -100 - pid, i ) )
            set i = i + 1
        endloop
        call PreloadGenEnd( file )
    endif
endfunction

function nzSearchFinish takes integer pid returns nothing
    local string term = LoadStr( nzHash, pid, 36 )
    call nzSearchSave( pid )
    call nzSearchStop( pid )
    call nzMsg( pid, "|cFF00cc66" + I2S( LoadInteger( nzHash, pid, 32 ) ) + "|r item(s) found in |cFFffcc00" + R2SW( nzNow( ) - LoadReal( nzHash, pid, 35 ), 1, 1 ) + "s|r. Full list: Warcraft III/CustomMapData/[CP] ItemsExport/Items |cFFe6b800[" + term + "]|r.txt" )
endfunction

function nzSearchSlice takes nothing returns boolean
    local integer pid = LoadInteger( nzHash, -1, 19 )
    local integer k = LoadInteger( nzHash, pid, 31 )
    local integer total = LoadInteger( nzHash, pid, 37 )
    local integer budget = LoadInteger( nzHash, -1, 8 )
    local string query = LoadStr( nzHash, pid, 33 )
    local integer found = LoadInteger( nzHash, pid, 39 )
    local integer cost = 0
    local integer id
    local item it
    loop
        exitwhen k >= total or cost >= budget or found >= 3
        set id = nzSearchIdAt( k, total )
        set it = CreateItem( id, 0., 0. )
        set cost = cost + 1
        if it != null then
            call RemoveItem( it )
            set cost = cost + 100
            set found = found + 1
            call nzSearchTest( pid, id, query )
        endif
        set k = k + 1
    endloop
    set it = null
    call SaveInteger( nzHash, pid, 31, k )
    call SaveInteger( nzHash, pid, 39, found )
    return false
endfunction

function nzSearchTick takes nothing returns nothing
    local integer pid = LoadInteger( nzHash, GetHandleId( GetExpiredTimer( ) ), 2 )
    local integer total = LoadInteger( nzHash, pid, 37 )
    local integer slices = 1
    local integer k
    if total > 238328 then
        set slices = 10
    endif
    call SaveInteger( nzHash, -1, 19, pid )
    call SaveInteger( nzHash, pid, 39, 0 )
    loop
        call TriggerEvaluate( LoadTriggerHandle( nzHash, -1, 18 ) )
        set slices = slices - 1
        set k = LoadInteger( nzHash, pid, 31 )
        exitwhen slices == 0 or k >= total or LoadInteger( nzHash, pid, 39 ) >= 3
    endloop
    if k >= total then
        call nzSearchFinish( pid )
        return
    endif
    if k >= LoadInteger( nzHash, pid, 38 ) then
        call SaveInteger( nzHash, pid, 38, LoadInteger( nzHash, pid, 38 ) + total / 10 )
        call nzMsg( pid, "Searching... |cFFffcc00" + I2S( R2I( k * 100. / total ) ) + "%|r" )
    endif
    call TimerStart( GetExpiredTimer( ), .03, false, function nzSearchTick )
endfunction

function nzFileName takes string s returns string
    local string out = ""
    local string c
    local integer i = 0
    loop
        exitwhen i >= StringLength( s )
        set c = SubString( s, i, i + 1 )
        if nzFind( "\\/:*?\"<>|", c ) >= 0 then
            set c = "_"
        endif
        set out = out + c
        set i = i + 1
    endloop
    return out
endfunction

function nzSearchStart takes integer pid, string term, integer total returns nothing
    local timer t = LoadTimerHandle( nzHash, pid, 34 )
    if LoadBoolean( nzHash, pid, 30 ) then
        call nzMsg( pid, "A search is already running. Type |cFF00aaff" + nzPrefix( pid ) + "sitem off|r to cancel." )
    elseif StringLength( term ) < 2 then
        call nzMsg( pid, "Type at least |cFFffcc002|r characters." )
    else
        if t == null then
            set t = CreateTimer( )
            call SaveTimerHandle( nzHash, pid, 34, t )
            call SaveInteger( nzHash, GetHandleId( t ), 2, pid )
        endif
        if not HaveSavedHandle( nzHash, -1, 18 ) then
            call SaveTriggerHandle( nzHash, -1, 18, CreateTrigger( ) )
            call TriggerAddCondition( LoadTriggerHandle( nzHash, -1, 18 ), Condition( function nzSearchSlice ) )
        endif
        call FlushChildHashtable( nzHash, -100 - pid )
        call SaveBoolean( nzHash, pid, 30, true )
        call SaveInteger( nzHash, pid, 31, 0 )
        call SaveInteger( nzHash, pid, 32, 0 )
        call SaveInteger( nzHash, pid, 37, total )
        call SaveInteger( nzHash, pid, 38, total / 10 )
        call SaveStr( nzHash, pid, 33, StringCase( term, false ) )
        call SaveStr( nzHash, pid, 36, nzFileName( term ) )
        call SaveReal( nzHash, pid, 35, nzNow( ) )
        call nzMsg( pid, "Searching items for |cFFe6b800[" + term + "]|r... The game may |cFFff1a1astutter|r a little while searching." )
        if total > 238328 then
            call nzMsg( pid, "|cFFff9900Deep search|r: all IDs, takes |cFFffcc00~2-3 minutes|r with some lag. Type |cFF00aaff" + nzPrefix( pid ) + "sitem off|r to cancel." )
        endif
        call TimerStart( t, .03, false, function nzSearchTick )
    endif
    set t = null
endfunction

function nzActivate takes integer pid returns nothing
    local integer i = 0
    if nzIsOn( pid ) then
        call nzMsg( pid, "You already have |cFF00cc66activated|r |cFF3366ffNZCP|r." )
        return
    endif
    loop
        exitwhen i == bj_MAX_PLAYER_SLOTS
        if nzLevel( i ) > 0 then
            call nzSetLevel( i, nzLevel( i ) + 1 )
            call nzMsg( i, nzColor( pid ) + " has |cFF00cc66activated|r |cFF3366ffNZCP|r. Your cheater level has changed to: |cFF0099ff" + I2S( nzLevel( i ) ) + "|r." )
        endif
        set i = i + 1
    endloop
    call SaveBoolean( nzHash, pid, 1, true )
    call nzSetLevel( pid, 1 )
    call nzMsg( pid, "|cFF038CFCNUZAMACUXE|r's CHEAT PACK has been |cFF00cc66activated|r! Type |cFF00aaff" + nzPrefix( pid ) + "cmds|r to list the commands." )
endfunction

function nzNameActivate takes string name returns nothing
    local integer i = 0
    loop
        exitwhen i == bj_MAX_PLAYER_SLOTS
        if GetPlayerName( Player( i ) ) == name then
            call SaveBoolean( nzHash, i, 1, true )
            call nzSetLevel( i, 1 )
            call nzMsg( i, "|cFFff9900Welcome|r, " + nzColor( i ) + "! |cFF3366ffNZCP|r has been |cFF00cc66auto activated|r." )
        endif
        set i = i + 1
    endloop
endfunction

function nzMapHackOff takes integer pid returns nothing
    local fogmodifier fm = LoadFogModifierHandle( nzHash, pid, 21 )
    if fm != null then
        call FogModifierStop( fm )
        call DestroyFogModifier( fm )
        call RemoveSavedHandle( nzHash, pid, 21 )
    endif
    set fm = null
endfunction

function nzCmdLvl takes nothing returns boolean
    local unit u = nzTarget( )
    local integer v = nzInt( 1 )
    if not IsUnitType( u, UNIT_TYPE_HERO ) then
        call nzSay( "|cFFff9900Level|r only works on |cFFff1a1aheroes|r." )
    else
        if v > GetHeroLevel( u ) then
            call SetHeroLevel( u, v, false )
        else
            call UnitStripHeroLevel( u, GetHeroLevel( u ) - v )
        endif
        call nzSay( "|cFFff9900Level|r: |cFFffcc00" + I2S( GetHeroLevel( u ) ) + "|r" )
    endif
    set u = null
    return false
endfunction

function nzCmdStat takes nothing returns boolean
    local unit u = nzTarget( )
    local string c = nzArg( 0 )
    local integer v = nzInt( 1 )
    local string label
    local integer now
    if c == "hp" then
        call SetWidgetLife( u, v )
        set label = "Life"
        set now = R2I( GetWidgetLife( u ) )
    elseif c == "mp" then
        call SetUnitState( u, UNIT_STATE_MANA, v )
        set label = "Mana"
        set now = R2I( GetUnitState( u, UNIT_STATE_MANA ) )
    elseif c == "ms" then
        call SetUnitMoveSpeed( u, v )
        set label = "Movement speed"
        set now = R2I( GetUnitMoveSpeed( u ) )
    elseif not IsUnitType( u, UNIT_TYPE_HERO ) then
        set label = ""
    elseif c == "str" then
        call SetHeroStr( u, v, true )
        set label = "Strength"
        set now = GetHeroStr( u, false )
    elseif c == "agi" then
        call SetHeroAgi( u, v, true )
        set label = "Agility"
        set now = GetHeroAgi( u, false )
    elseif c == "int" then
        call SetHeroInt( u, v, true )
        set label = "Intelligence"
        set now = GetHeroInt( u, false )
    elseif c == "sp" then
        call UnitModifySkillPoints( u, v )
        set label = "Skill points"
        set now = GetHeroSkillPoints( u )
    else
        call SetHeroXP( u, v, false )
        set label = "Experience"
        set now = GetHeroXP( u )
    endif
    if label == "" then
        call nzSay( "|cFFff9900" + c + "|r only works on |cFFff1a1aheroes|r." )
    else
        call nzSay( "|cFFff9900" + label + "|r: |cFFffcc00" + I2S( now ) + "|r" )
    endif
    set u = null
    return false
endfunction

function nzCmdOwner takes nothing returns boolean
    local integer p = nzPlayerArg( 1 )
    if p >= 0 then
        call SetUnitOwner( nzTarget( ), Player( p ), true )
        call nzSay( "|cFFff9900Owner|r changed to " + nzColor( p ) + "." )
    else
        call nzUsage( )
    endif
    return false
endfunction

function nzCmdCharge takes nothing returns boolean
    local item it = UnitItemInSlot( nzTarget( ), nzInt( 1 ) - 1 )
    if it != null then
        call SetItemCharges( it, nzInt( 2 ) )
        call nzSay( "|cFFff9900Charges|r in slot |cFF00aaff" + nzArg( 1 ) + "|r: |cFFffcc00" + I2S( GetItemCharges( it ) ) + "|r" )
    else
        call nzSay( "There's |cFFff9900no item|r in slot |cFF00aaff" + nzArg( 1 ) + "|r. Make sure to type the |cFF009933correct|r slot." )
    endif
    set it = null
    return false
endfunction

function nzCmdInvul takes nothing returns boolean
    call nzSwitch( "|cFFff9900Invulnerability|r", GetUnitAbilityLevel( nzTarget( ), 'Avul' ) > 0, nzArg( 0 ) == "invul" )
    call SetUnitInvulnerable( nzTarget( ), nzArg( 0 ) == "invul" )
    return false
endfunction

function nzCmdKill takes nothing returns boolean
    local unit u = nzTarget( )
    local integer hid = GetHandleId( u )
    if nzArg( 0 ) == "kill" then
        call nzSay( "|cFFff9900" + GetUnitName( u ) + "|r has been |cFFff1a1akilled|r." )
        call KillUnit( u )
    else
        call nzSay( "|cFFff9900" + GetUnitName( u ) + "|r has been |cFFff1a1aremoved|r." )
        call nzUnitTimerStop( hid, 12 )
        call nzUnitTimerStop( hid, 13 )
        call FlushChildHashtable( nzHash, hid )
        call FlushChildHashtable( nzHash, -hid )
        call RemoveUnit( u )
    endif
    set u = null
    return false
endfunction

function nzAbilScanRow takes nothing returns boolean
    local unit u = LoadUnitHandle( nzHash, -6, 0 )
    local integer row = LoadInteger( nzHash, -6, -1 )
    local integer n = LoadInteger( nzHash, -6, 0 )
    local integer d2 = 48
    local integer d3
    loop
        exitwhen d2 > 122
        set d3 = 48
        loop
            exitwhen d3 > 122
            if GetUnitAbilityLevel( u, row + d2 * 256 + d3 ) > 0 then
                set n = n + 1
                call SaveInteger( nzHash, -6, n, row + d2 * 256 + d3 )
            endif
            if d3 == 57 then
                set d3 = 65
            elseif d3 == 90 then
                set d3 = 97
            else
                set d3 = d3 + 1
            endif
        endloop
        if d2 == 57 then
            set d2 = 65
        elseif d2 == 90 then
            set d2 = 97
        else
            set d2 = d2 + 1
        endif
    endloop
    call SaveInteger( nzHash, -6, 0, n )
    set u = null
    return false
endfunction

function nzAbilScan takes unit u returns nothing
    local trigger t = LoadTriggerHandle( nzHash, -1, 17 )
    local integer d1 = 48
    if t == null then
        set t = CreateTrigger( )
        call TriggerAddCondition( t, Condition( function nzAbilScanRow ) )
        call SaveTriggerHandle( nzHash, -1, 17, t )
    endif
    call FlushChildHashtable( nzHash, -6 )
    call SaveUnitHandle( nzHash, -6, 0, u )
    loop
        exitwhen d1 > 122
        call SaveInteger( nzHash, -6, -1, 'A' * 16777216 + d1 * 65536 )
        call TriggerEvaluate( t )
        if d1 == 57 then
            set d1 = 65
        elseif d1 == 90 then
            set d1 = 97
        else
            set d1 = d1 + 1
        endif
    endloop
    set t = null
endfunction

function nzCopyAbilities takes unit u, unit c returns nothing
    local integer i = LoadInteger( nzHash, -6, 0 )
    local integer id
    local integer lvl
    local integer cur
    loop
        exitwhen i < 1
        set id = LoadInteger( nzHash, -6, i )
        set lvl = GetUnitAbilityLevel( u, id )
        loop
            set cur = GetUnitAbilityLevel( c, id )
            exitwhen cur >= lvl or not IsUnitType( c, UNIT_TYPE_HERO )
            call UnitModifySkillPoints( c, 1 )
            call SelectHeroSkill( c, id )
            if GetUnitAbilityLevel( c, id ) == cur then
                call UnitModifySkillPoints( c, -1 )
                exitwhen true
            endif
        endloop
        if cur == 0 then
            call UnitAddAbility( c, id )
        endif
        if cur < lvl then
            call SetUnitAbilityLevel( c, id, lvl )
        endif
        set i = i - 1
    endloop
    if IsUnitType( c, UNIT_TYPE_HERO ) then
        call UnitModifySkillPoints( c, GetHeroSkillPoints( u ) - GetHeroSkillPoints( c ) )
    endif
endfunction

function nzCopyUnit takes unit u, boolean full returns nothing
    local unit c = CreateUnit( GetOwningPlayer( u ), GetUnitTypeId( u ), GetUnitX( u ), GetUnitY( u ), GetUnitFacing( u ) )
    local integer hid = GetHandleId( u )
    local integer k = 1
    local item it
    if IsUnitType( u, UNIT_TYPE_HERO ) then
        call SetHeroXP( c, GetHeroXP( u ), false )
        call SetHeroStr( c, GetHeroStr( u, false ), true )
        call SetHeroAgi( c, GetHeroAgi( u, false ), true )
        call SetHeroInt( c, GetHeroInt( u, false ), true )
    endif
    loop
        exitwhen k > 6
        set it = UnitItemInSlot( u, k - 1 )
        if it != null and UnitAddItemToSlotById( c, GetItemTypeId( it ), k - 1 ) then
            call SetItemCharges( UnitItemInSlot( c, k - 1 ), GetItemCharges( it ) )
        endif
        set k = k + 1
    endloop
    if full then
        call nzCopyAbilities( u, c )
    elseif GetUnitAbilityLevel( u, 'Avul' ) > 0 then
        call SetUnitInvulnerable( c, true )
    endif
    set k = 1
    loop
        exitwhen k > 8
        if HaveSavedInteger( nzHash, hid, k ) then
            call SaveInteger( nzHash, GetHandleId( c ), k, LoadInteger( nzHash, hid, k ) )
        endif
        set k = k + 1
    endloop
    if HaveSavedReal( nzHash, hid, 2 ) then
        call SaveReal( nzHash, GetHandleId( c ), 2, LoadReal( nzHash, hid, 2 ) )
    endif
    if HaveSavedHandle( nzHash, hid, 12 ) then
        call nzUnitTimer( c, 12, .25, LoadReal( nzHash, GetHandleId( LoadTimerHandle( nzHash, hid, 12 ) ), 1 ), function nzRegenTick )
    endif
    if HaveSavedHandle( nzHash, hid, 13 ) then
        call nzUnitTimer( c, 13, .2, 0., function nzCooldownTick )
    endif
    call SetUnitMoveSpeed( c, GetUnitMoveSpeed( u ) )
    call SetUnitState( c, UNIT_STATE_LIFE, GetUnitState( u, UNIT_STATE_LIFE ) )
    call SetUnitState( c, UNIT_STATE_MANA, GetUnitState( u, UNIT_STATE_MANA ) )
    set c = null
    set it = null
endfunction

function nzCmdCopy takes nothing returns boolean
    local unit u = nzTarget( )
    local integer n = nzInt( 1 )
    local boolean full = StringCase( nzArg( 2 ), false ) == "full"
    local integer i = 0
    if n <= 0 then
        call nzUsage( )
    elseif full then
        call nzSay( "|cFFff9900Full copy|r: scanning abilities, the game |cFFff1a1afreezes for a moment|r." )
        call nzAbilScan( u )
    endif
    loop
        exitwhen i >= n
        call nzCopyUnit( u, full )
        set i = i + 1
    endloop
    if n > 0 then
        call nzSay( "|cFFff9900" + GetUnitName( u ) + "|r copied |cFFffcc00" + I2S( n ) + "|r time(s)." )
    endif
    set u = null
    return false
endfunction

function nzCmdLearn takes nothing returns boolean
    local unit u = nzTarget( )
    local integer id = nzS2Id( nzArg( 1 ) )
    if id != 0 then
        if nzArg( 0 ) == "unlearn" then
            call UnitRemoveAbility( u, id )
            call nzSay( "|cFFff9900Ability|r: [|cFF00cc66" + GetObjectName( id ) + "|r] has been |cFFff1a1aremoved|r." )
        elseif GetUnitAbilityLevel( u, id ) == 0 then
            call UnitAddAbility( u, id )
            call nzSay( "|cFFff9900Ability|r: [|cFF00cc66" + GetObjectName( id ) + "|r] has been |cFF00cc66added|r." )
        else
            call IncUnitAbilityLevel( u, id )
            call nzSay( "|cFFff9900Ability|r: [|cFF00cc66" + GetObjectName( id ) + "|r] has been |cFF00cc66leveled up!|r" )
        endif
    else
        call nzUsage( )
    endif
    set u = null
    return false
endfunction

function nzCmdRegen takes nothing returns boolean
    local unit u = nzTarget( )
    local real v = nzReal( 1 )
    if v == 0. then
        call nzSwitch( "|cFFff9900Regeneration buff|r", HaveSavedHandle( nzHash, GetHandleId( u ), 12 ), false )
        call nzUnitTimerStop( GetHandleId( u ), 12 )
    else
        call nzUnitTimer( u, 12, .25, v, function nzRegenTick )
        call nzSay( "|cFFff9900[EXTRA]|r |cFF00f600HP|r & |cFF95b7e9MP|r Regen: |cFFff9900" + R2SW( v, 1, 1 ) + "|r/.25s" )
    endif
    set u = null
    return false
endfunction

function nzCmdNoCd takes nothing returns boolean
    local unit u = nzTarget( )
    call nzSwitch( "|cFFff9900No cooldown|r", HaveSavedHandle( nzHash, GetHandleId( u ), 13 ), not nzOff( ) )
    if nzOff( ) then
        call nzUnitTimerStop( GetHandleId( u ), 13 )
    else
        call nzUnitTimer( u, 13, .2, 0., function nzCooldownTick )
    endif
    set u = null
    return false
endfunction

function nzCmdPause takes nothing returns boolean
    call nzSwitch( "|cFFff9900Pause|r", IsUnitPaused( nzTarget( ) ), not nzOff( ) )
    call PauseUnit( nzTarget( ), not nzOff( ) )
    return false
endfunction

function nzUnitPct takes integer key, string label returns nothing
    local integer hid = GetHandleId( nzTarget( ) )
    local integer v = nzInt( 1 )
    if v < 0 then
        call nzUsage( )
        return
    elseif key == 6 then
        set v = IMinBJ( v, 100 )
    endif
    call nzDmgOn( )
    if v == 0 then
        call nzSwitch( "|cFFff9900" + label + "|r", HaveSavedInteger( nzHash, hid, key ), false )
        call RemoveSavedInteger( nzHash, hid, key )
    else
        call SaveInteger( nzHash, hid, key, v )
        call nzSay( label + ": |cFFffcc00" + I2S( v ) + "%|r" )
    endif
endfunction

function nzCmdCrit takes nothing returns boolean
    local integer hid = GetHandleId( nzTarget( ) )
    call nzDmgOn( )
    if HaveSavedInteger( nzHash, hid, 3 ) then
        call nzSay( "In order to use Critical Strike Chance and Damage Multiplier, you must |cFFff1a1adisable|r the |cFFff9900Maximum HP Damage|r." )
    elseif nzInt( 1 ) == 0 then
        call nzSwitch( "|cFFff9900Critical Strike|r", HaveSavedInteger( nzHash, hid, 1 ), false )
        call RemoveSavedInteger( nzHash, hid, 1 )
        call RemoveSavedReal( nzHash, hid, 2 )
    elseif nzInt( 1 ) > 0 and nzReal( 2 ) > 1. then
        call SaveInteger( nzHash, hid, 1, nzInt( 1 ) )
        call SaveReal( nzHash, hid, 2, nzReal( 2 ) )
        call nzSay( "Critical Strike Chance: |cFFffcc00" + nzArg( 1 ) + "%|r  Damage Multiplier: |cFFffcc00" + nzArg( 2 ) + "x|r" )
    else
        call nzUsage( )
    endif
    return false
endfunction

function nzCmdHpDmg takes nothing returns boolean
    if HaveSavedInteger( nzHash, GetHandleId( nzTarget( ) ), 1 ) then
        call nzSay( "In order to use Maximum HP Damage, you must |cFFff1a1adisable|r the |cFFff9900Critical Strike Chance|r." )
    else
        call nzUnitPct( 3, "Maximum HP Damage" )
    endif
    return false
endfunction

function nzCmdPct takes nothing returns boolean
    local string c = nzArg( 0 )
    if c == "dmgls" then
        call nzUnitPct( 4, "Life steal" )
    elseif c == "dmgms" then
        call nzUnitPct( 5, "Mana steal" )
    elseif c == "dmgb" then
        call nzUnitPct( 6, "Block damage" )
    elseif c == "dmgr" then
        call nzUnitPct( 7, "Reflect damage" )
    else
        call nzUnitPct( 8, "Spell damage" )
    endif
    return false
endfunction

function nzCmdStatus takes nothing returns boolean
    local integer hid = GetHandleId( nzTarget( ) )
    local string text = "|cFFff9933Current Selected Unit Status|r"
    set text = text + "\nCritical: |cFFffcc00" + I2S( LoadInteger( nzHash, hid, 1 ) ) + "%|r x |cFFffcc00" + R2SW( LoadReal( nzHash, hid, 2 ), 1, 1 ) + "|r"
    set text = text + "\nMaximum HP Damage: |cFFffcc00" + I2S( LoadInteger( nzHash, hid, 3 ) ) + "%|r"
    set text = text + "\nSpell damage: |cFF6699ff+" + I2S( LoadInteger( nzHash, hid, 8 ) ) + "%|r"
    set text = text + "\nLife steal: |cFF00ff00" + I2S( LoadInteger( nzHash, hid, 4 ) ) + "%|r   Mana steal: |cFF95b7e9" + I2S( LoadInteger( nzHash, hid, 5 ) ) + "%|r"
    set text = text + "\nBlock: |cFFffcc00" + I2S( LoadInteger( nzHash, hid, 6 ) ) + "%|r   Reflect: |cFFffcc00" + I2S( LoadInteger( nzHash, hid, 7 ) ) + "%|r"
    call nzMsg( nzPid( ), text )
    return false
endfunction

function nzCmdUnitId takes nothing returns boolean
    local integer id = GetUnitTypeId( nzTarget( ) )
    call nzMsg( nzPid( ), "|cFF00aaffUnit ID:|r " + nzId2S( id ) + "  |cFF00aaffName:|r " + GetObjectName( id ) )
    return false
endfunction

function nzCmdItemId takes nothing returns boolean
    local integer pid = nzPid( )
    local integer slot = nzInt( 1 )
    local integer id = GetItemTypeId( UnitItemInSlot( nzTarget( ), slot - 1 ) )
    if slot < 1 or slot > 6 then
        call nzUsage( )
    elseif id == 0 then
        call nzMsg( pid, "There's |cFFff9900no item|r in slot |cFF00aaff" + I2S( slot ) + "|r." )
    else
        call nzMsg( pid, "|cFF00aaffItem ID:|r " + nzId2S( id ) + "  |cFF00aaffName:|r " + GetObjectName( id ) )
    endif
    return false
endfunction

function nzCmdItemSlot takes nothing returns boolean
    local unit u = nzTarget( )
    local integer slot = nzInt( 1 )
    local integer id = nzS2Id( nzArg( 2 ) )
    if slot < 1 or slot > 6 or id == 0 then
        call nzUsage( )
    elseif slot > UnitInventorySize( u ) then
        call nzSay( "This unit has only |cFF00aaff" + I2S( UnitInventorySize( u ) ) + "|r inventory slots." )
    elseif UnitItemInSlot( u, slot - 1 ) != null then
        call nzSay( "Slot |cFF00aaff" + I2S( slot ) + "|r is |cFFff1a1aoccupied|r." )
    elseif UnitAddItemToSlotById( u, id, slot - 1 ) then
        call nzSay( "[|cFF00cc66" + GetObjectName( id ) + "|r] has been |cFF00cc66added|r to slot |cFF00aaff" + I2S( slot ) + "|r." )
    else
        call nzSay( "There's |cFFff1a1ano item|r with ID [|cFF00aaff" + nzArg( 2 ) + "|r]." )
    endif
    set u = null
    return false
endfunction

function nzCmdCreate takes nothing returns boolean
    local integer pid = nzPid( )
    local unit u = nzTarget( )
    local integer id = nzS2Id( nzArg( 1 ) )
    if id == 0 then
        call nzUsage( )
    elseif CreateItem( id, GetUnitX( u ), GetUnitY( u ) ) == null and CreateUnit( Player( pid ), id, GetUnitX( u ), GetUnitY( u ), 270. ) == null then
        call nzMsg( pid, "There's |cFFff1a1ano item or unit|r with ID [|cFF00aaff" + nzArg( 1 ) + "|r]." )
    else
        call nzMsg( pid, "|cFFff9900Object|r with ID: [|cFF00cc66" + nzId2S( id ) + "|r] has been |cFF00cc66spawned|r." )
    endif
    set u = null
    return false
endfunction

function nzCmdRandomItem takes nothing returns boolean
    local unit u = nzTarget( )
    local integer n = IMinBJ( nzInt( 1 ), 99 )
    local integer i = 0
    if n <= 0 then
        call nzUsage( )
    endif
    loop
        exitwhen i >= n
        call CreateItem( ChooseRandomItemEx( ITEM_TYPE_ANY, -1 ), GetUnitX( u ), GetUnitY( u ) )
        set i = i + 1
    endloop
    if n > 0 then
        call nzMsg( nzPid( ), "|cFFffcc00" + I2S( n ) + "|r random item(s) |cFF00cc66created|r." )
    endif
    set u = null
    return false
endfunction

function nzAddState takes integer p, playerstate st, integer v returns nothing
    local integer now = GetPlayerState( Player( p ), st ) + v
    if st == PLAYER_STATE_RESOURCE_GOLD then
        call SaveInteger( nzHash, p, 13, now )
    else
        call SaveInteger( nzHash, p, 16, now )
    endif
    call SetPlayerState( Player( p ), st, now )
endfunction

function nzCmdResource takes nothing returns boolean
    local integer pid = nzPid( )
    if nzArg( 0 ) == "gold" then
        call nzAddState( pid, PLAYER_STATE_RESOURCE_GOLD, nzInt( 1 ) )
        call nzMsg( pid, "|cFFffff00Gold|r: |cFFffcc00" + I2S( GetPlayerState( Player( pid ), PLAYER_STATE_RESOURCE_GOLD ) ) + "|r" )
    else
        call nzAddState( pid, PLAYER_STATE_RESOURCE_LUMBER, nzInt( 1 ) )
        call nzMsg( pid, "|cFF00cc66Lumber|r: |cFFffcc00" + I2S( GetPlayerState( Player( pid ), PLAYER_STATE_RESOURCE_LUMBER ) ) + "|r" )
    endif
    return false
endfunction

function nzCmdGive takes nothing returns boolean
    local integer pid = nzPid( )
    local integer p = nzPlayerArg( 1 )
    local integer v = nzInt( 2 )
    local string cmd = nzArg( 0 )
    if p < 0 then
        call nzUsage( )
    elseif cmd == "giveg" then
        call nzAddState( p, PLAYER_STATE_RESOURCE_GOLD, v )
        call nzMsg( pid, "You gave " + I2S( v ) + " |cFFffff00gold|r to " + nzColor( p ) + "." )
    elseif cmd == "givel" then
        call nzAddState( p, PLAYER_STATE_RESOURCE_LUMBER, v )
        call nzMsg( pid, "You gave " + I2S( v ) + " |cFF00cc66lumber|r to " + nzColor( p ) + "." )
    else
        call SetPlayerState( Player( p ), PLAYER_STATE_FOOD_CAP_CEILING, v )
        call SetPlayerState( Player( p ), PLAYER_STATE_RESOURCE_FOOD_CAP, v )
        call nzMsg( pid, "|cFFb33c00Food|r cap of " + nzColor( p ) + " set to " + I2S( v ) + "." )
    endif
    return false
endfunction

function nzCmdFood takes nothing returns boolean
    local integer pid = nzPid( )
    local string a = StringCase( nzArg( 1 ), false )
    if ( a == "use" or a == "nouse" ) and nzTarget( ) == null then
        call nzMsg( pid, "|cFFff1a1aSelect a unit|r first." )
    elseif a == "use" or a == "nouse" then
        call SetUnitUseFood( nzTarget( ), a == "use" )
        call nzMsg( pid, "|cFFff9900" + GetUnitName( nzTarget( ) ) + "|r food usage: |cFFffcc00" + a + "|r" )
    elseif nzInt( 1 ) != 0 then
        call SetPlayerState( Player( pid ), PLAYER_STATE_FOOD_CAP_CEILING, nzInt( 1 ) )
        call SetPlayerState( Player( pid ), PLAYER_STATE_RESOURCE_FOOD_CAP, nzInt( 1 ) )
        call nzMsg( pid, "|cFFb33c00Food|r cap: |cFFffcc00" + I2S( GetPlayerState( Player( pid ), PLAYER_STATE_RESOURCE_FOOD_CAP ) ) + "|r" )
    else
        call nzUsage( )
    endif
    return false
endfunction

function nzCmdRate takes nothing returns boolean
    local integer pid = nzPid( )
    local integer v = nzInt( 1 )
    local integer on = 11
    local playerstate st = PLAYER_STATE_RESOURCE_GOLD
    local string label = "|cFFffff00Gold Rate|r"
    if nzArg( 0 ) == "lrate" then
        set on = 14
        set st = PLAYER_STATE_RESOURCE_LUMBER
        set label = "|cFF009933Lumber Rate|r"
    endif
    if LoadBoolean( nzHash, pid, on ) then
        if v == 0 then
            call RemoveSavedBoolean( nzHash, pid, on )
            call nzMsg( pid, label + " has been |cFFff1a1adisabled|r." )
        else
            call SaveInteger( nzHash, pid, on + 1, v )
            call nzMsg( pid, label + " has been |cFFe68a00changed|r to |cFFffff00" + I2S( v ) + "%|r." )
        endif
    elseif v > 0 then
        call SaveBoolean( nzHash, pid, on, true )
        call SaveInteger( nzHash, pid, on + 1, v )
        call SaveInteger( nzHash, pid, on + 2, GetPlayerState( Player( pid ), st ) )
        call nzMsg( pid, label + " has been |cFFe68a00set|r to |cFFffff00" + I2S( v ) + "%|r." )
    else
        call nzUsage( )
    endif
    set st = null
    return false
endfunction

function nzCmdExpRate takes nothing returns boolean
    local integer pid = nzPid( )
    local player p = Player( pid )
    local integer v = IMaxBJ( R2I( 100 * GetPlayerHandicapXP( p ) + .5 ) + nzInt( 1 ), 0 )
    call SetPlayerHandicapXP( p, v * .01 )
    call nzMsg( pid, "|cFFe600e6Experience Rate|r is now |cFFe600e6" + I2S( v ) + "%|r." )
    set p = null
    return false
endfunction

function nzCmdTech takes nothing returns boolean
    local integer pid = nzPid( )
    local player p = Player( pid )
    local integer id = nzS2Id( nzArg( 1 ) )
    local integer before = GetPlayerTechCount( p, id, true )
    local integer lvl = before + 1
    if id == 0 then
        call nzUsage( )
    else
        if nzArgCount( ) > 2 then
            set lvl = nzInt( 2 )
        endif
        call SetPlayerTechResearched( p, id, lvl )
        set lvl = GetPlayerTechCount( p, id, true )
        if lvl == before then
            call nzMsg( pid, "|cFFff9900Upgrade|r [|cFF00cc66" + GetObjectName( id ) + "|r] |cFFff1a1adidn't change|r (level |cFFffcc00" + I2S( lvl ) + "|r): max level reached or not an upgrade ID." )
        else
            call nzMsg( pid, "|cFFff9900Upgrade|r [|cFF00cc66" + GetObjectName( id ) + "|r] set to level |cFFffcc00" + I2S( lvl ) + "|r." )
        endif
    endif
    set p = null
    return false
endfunction

function nzCmdKick takes nothing returns boolean
    local integer pid = nzPid( )
    local integer p = nzPlayerArg( 1 )
    if p == pid then
        call nzMsg( pid, "You |cFFff1a1acan't|r kick yourself." )
    elseif p < 0 then
        call nzUsage( )
    elseif nzLevel( pid ) > nzLevel( p ) then
        call CustomDefeatBJ( Player( p ), "You have been |cFFff1a1akicked|r!" )
    else
        call nzMsg( pid, "You |cFFff1a1acan't|r kick a cheater with the same or a higher level." )
    endif
    return false
endfunction

function nzCmdShare takes nothing returns boolean
    local integer pid = nzPid( )
    local integer a = nzPlayerArg( 1 )
    local integer b = nzPlayerArg( 2 )
    local boolean on = nzArg( 0 ) == "share"
    if a < 0 or b < 0 then
        call nzUsage( )
    elseif nzLevel( pid ) > nzLevel( a ) then
        call SetPlayerAlliance( Player( a ), Player( b ), ALLIANCE_SHARED_VISION, on )
        call SetPlayerAlliance( Player( a ), Player( b ), ALLIANCE_SHARED_CONTROL, on )
        call SetPlayerAlliance( Player( a ), Player( b ), ALLIANCE_SHARED_ADVANCED_CONTROL, on )
        call nzMsg( pid, "You have " + nzArg( 0 ) + "d " + nzColor( a ) + " with " + nzColor( b ) + "." )
    endif
    return false
endfunction

function nzCmdPing takes nothing returns boolean
    if GetLocalPlayer( ) == Player( nzPid( ) ) then
        call PingMinimapEx( nzReal( 1 ), nzReal( 2 ), 15, 51, 153, 255, true )
    endif
    return false
endfunction

function nzCmdRevive takes nothing returns boolean
    local integer pid = nzPid( )
    local player p = Player( pid )
    local integer heroes = GetPlayerTechMaxAllowed( p, 'HERO' )
    local integer food = GetPlayerState( p, PLAYER_STATE_RESOURCE_FOOD_USED )
    local group g = CreateGroup( )
    local integer n = 0
    local integer failed = 0
    local integer kind
    local integer limit
    local unit u
    call SetPlayerTechMaxAllowed( p, 'HERO', -1 )
    call SetPlayerState( p, PLAYER_STATE_RESOURCE_FOOD_USED, 0 )
    call GroupEnumUnitsOfPlayer( g, p, null )
    loop
        set u = FirstOfGroup( g )
        exitwhen u == null
        call GroupRemoveUnit( g, u )
        if IsUnitType( u, UNIT_TYPE_HERO ) and IsUnitType( u, UNIT_TYPE_DEAD ) then
            set kind = GetUnitTypeId( u )
            set limit = GetPlayerTechMaxAllowed( p, kind )
            call SetPlayerTechMaxAllowed( p, kind, -1 )
            if ReviveHero( u, GetUnitX( u ), GetUnitY( u ), true ) then
                set n = n + 1
            else
                set failed = failed + 1
            endif
            call SetPlayerTechMaxAllowed( p, kind, limit )
        endif
    endloop
    call SetPlayerTechMaxAllowed( p, 'HERO', heroes )
    call SetPlayerState( p, PLAYER_STATE_RESOURCE_FOOD_USED, food + GetPlayerState( p, PLAYER_STATE_RESOURCE_FOOD_USED ) )
    if n + failed == 0 then
        call nzMsg( pid, "|cFFff9900Revive|r: no dead heroes." )
    elseif failed == 0 then
        call nzMsg( pid, "|cFFff9900Revive|r: |cFF00cc66" + I2S( n ) + "|r hero(es) revived." )
    else
        call nzMsg( pid, "|cFFff9900Revive|r: |cFF00cc66" + I2S( n ) + "|r revived, |cFFff1a1a" + I2S( failed ) + "|r failed." )
    endif
    call DestroyGroup( g )
    set g = null
    set p = null
	set u = null
    return false
endfunction

function nzCmdName takes nothing returns boolean
    local integer pid = nzPid( )
    call SetPlayerName( Player( pid ), nzRest( ) )
    call nzMsg( pid, "|cFFff9900Name|r has been changed to: " + nzColor( pid ) + "." )
    return false
endfunction

function nzZoomTick takes nothing returns nothing
    local real d = LoadReal( nzHash, GetPlayerId( GetLocalPlayer( ) ), 23 )
    if d > 0. then
        call SetCameraField( CAMERA_FIELD_TARGET_DISTANCE, d, .5 )
        call SetCameraField( CAMERA_FIELD_FARZ, d + 3000., .5 )
    endif
endfunction

function nzZoomOff takes integer pid returns nothing
    if HaveSavedReal( nzHash, pid, 23 ) then
        call RemoveSavedReal( nzHash, pid, 23 )
        if GetLocalPlayer( ) == Player( pid ) then
            call SetCameraField( CAMERA_FIELD_TARGET_DISTANCE, 1650., .5 )
            call SetCameraField( CAMERA_FIELD_FARZ, 5000., .5 )
        endif
    endif
endfunction

function nzCmdZoom takes nothing returns boolean
    local integer pid = nzPid( )
    local real d = nzReal( 1 )
    if nzOff( ) then
        call nzSwitch( "|cFFff9900Zoom|r", HaveSavedReal( nzHash, pid, 23 ), false )
        call nzZoomOff( pid )
    elseif d <= 0. then
        call nzUsage( )
    else
        call SaveReal( nzHash, pid, 23, d )
        if not HaveSavedHandle( nzHash, -1, 16 ) then
            call SaveTimerHandle( nzHash, -1, 16, CreateTimer( ) )
            call TimerStart( LoadTimerHandle( nzHash, -1, 16 ), .5, true, function nzZoomTick )
        endif
        call nzZoomTick( )
        call nzMsg( pid, "|cFFff9900Zoom|r: |cFFffcc00" + I2S( R2I( d ) ) + "|r. Type |cFF00aaff" + nzPrefix( pid ) + "pzoom off|r to restore." )
    endif
    return false
endfunction

function nzCmdActivator takes nothing returns boolean
    call SaveStr( nzHash, -1, 2, nzArg( 1 ) )
    call nzMsg( nzPid( ), "|cFFff9900Activator|r has been changed to: |cFF00cc66" + nzArg( 1 ) + "|r." )
    return false
endfunction

function nzArrowName takes integer slot returns string
    if slot == 4 then
        return "Left"
    elseif slot == 5 then
        return "Right"
    elseif slot == 6 then
        return "Up"
    endif
    return "Down"
endfunction

function nzCmdBind takes nothing returns boolean
    local integer pid = nzPid( )
    local string cmd = nzArg( 0 )
    local string line = nzRest( )
    local integer slot = 7
    if SubString( line, 0, 1 ) == nzPrefix( pid ) then
        set line = SubString( line, 1, StringLength( line ) )
    endif
    if cmd == "bindleft" then
        set slot = 4
    elseif cmd == "bindright" then
        set slot = 5
    elseif cmd == "bindup" then
        set slot = 6
    endif
    if nzOff( ) then
        call RemoveSavedString( nzHash, pid, slot )
        call nzMsg( pid, "|cFFff9900" + nzArrowName( slot ) + " Arrow Key|r bind has been |cFFff1a1aremoved|r." )
    else
        call SaveStr( nzHash, pid, slot, line )
        call nzMsg( pid, "[ |cFF00cc66" + line + "|r ] has been |cFF00cc66bound|r to |cFFff9900" + nzArrowName( slot ) + " Arrow Key|r." )
    endif
    return false
endfunction

function nzCmdShowBinds takes nothing returns boolean
    local integer pid = nzPid( )
    local integer slot = 4
    local string text = "|cFF00cc66Current Bound Commands|r:"
    loop
        exitwhen slot > 7
        if HaveSavedString( nzHash, pid, slot ) then
            set text = text + "\n|cFFff9900" + nzArrowName( slot ) + ":|r [ |cFF00cc66" + LoadStr( nzHash, pid, slot ) + "|r ]"
        else
            set text = text + "\n|cFFff9900" + nzArrowName( slot ) + ":|r [ |cFFff5050NONE|r ]"
        endif
        set slot = slot + 1
    endloop
    call nzMsg( pid, text )
    return false
endfunction

function nzCmdClearBinds takes nothing returns boolean
    local integer pid = nzPid( )
    local integer slot = 4
    loop
        exitwhen slot > 7
        call RemoveSavedString( nzHash, pid, slot )
        set slot = slot + 1
    endloop
    call nzMsg( pid, "|cFFff9900Key bindings|r have been |cFFff1a1aremoved|r." )
    return false
endfunction

function nzCmdToggle takes nothing returns boolean
    local integer pid = nzPid( )
    local string c = nzArg( 0 )
    local integer key = 20
    local string label = "|cFFff9900Infinite Charge|r"
    local boolean was
    if c == "fast" then
        set key = 10
        set label = "|cFFff9900Fast|r building, upgrading and training"
    elseif c == "enemychat" then
        set key = 19
        set label = "|cFFff1a1aEnemy|r's chat"
    endif
    set was = LoadBoolean( nzHash, pid, key )
    call nzSwitch( label, was, not nzOff( ) )
    if nzOff( ) then
        call RemoveSavedBoolean( nzHash, pid, key )
    elseif not was then
        call SaveBoolean( nzHash, pid, key, true )
        if key == 10 then
            call nzWake( 13 )
            call nzWake( 14 )
            call nzMsg( pid, "|cFFff1a1aDon't|r forget to press |cFF00cc66ESC|r to instantly build and train units." )
        endif
    endif
    return false
endfunction

function nzCmdMapHack takes nothing returns boolean
    local integer pid = nzPid( )
    local boolean was = HaveSavedHandle( nzHash, pid, 21 )
    local fogmodifier fm
    call nzSwitch( "|cFFff9900Map hack|r", was, not nzOff( ) )
    if nzOff( ) then
        call nzMapHackOff( pid )
    elseif not was then
        set fm = CreateFogModifierRect( Player( pid ), FOG_OF_WAR_VISIBLE, bj_mapInitialPlayableArea, false, false )
        call FogModifierStart( fm )
        call SaveFogModifierHandle( nzHash, pid, 21, fm )
        set fm = null
    endif
    return false
endfunction

function nzCmdTeleport takes nothing returns boolean
    local integer pid = nzPid( )
    local boolean was = LoadBoolean( nzHash, pid, 17 )
    local string a = StringCase( nzArg( 1 ), false )
    local string tp = nzPrefix( pid ) + "tp"
    if nzOff( ) then
        call nzSwitch( "|cFFff9900Teleport|r", was, false )
        call RemoveSavedBoolean( nzHash, pid, 17 )
    elseif a != "m" and a != "p" and a != "a" and nzArgCount( ) > 1 then
        call nzUsage( )
    else
        if not was then
            call SaveBoolean( nzHash, pid, 17, true )
            call nzWake( 15 )
            call SaveInteger( nzHash, pid, 18, 851990 )
            call nzMsg( pid, "|cFFff9900Teleport|r has been |cFF00cc66enabled|r! Press |cFF00aaffP|r (patrol) on the desired place.\nChange the key with: " + tp + " |cFF00aaffM|r (move), " + tp + " |cFF00aaffP|r (patrol), " + tp + " |cFF00aaffA|r (attack)." )
        elseif nzArgCount( ) < 2 then
            call nzSwitch( "|cFFff9900Teleport|r", true, true )
        endif
        if a == "m" then
            call SaveInteger( nzHash, pid, 18, 851986 )
            call nzMsg( pid, "|cFFff9900Teleport's|r bind key changed to |cFF00aaffMove|r." )
        elseif a == "p" then
            call SaveInteger( nzHash, pid, 18, 851990 )
            call nzMsg( pid, "|cFFff9900Teleport's|r bind key changed to |cFF00aaffPatrol|r." )
        elseif a == "a" then
            call SaveInteger( nzHash, pid, 18, 851983 )
            call nzMsg( pid, "|cFFff9900Teleport's|r bind key changed to |cFF00aaffAttack|r." )
        endif
    endif
    return false
endfunction

function nzCmdSearch takes nothing returns boolean
    local integer pid = nzPid( )
    local integer total = 238328
    if nzArg( 0 ) == "sitem!" then
        set total = 14776336
    endif
    if nzOff( ) and not LoadBoolean( nzHash, pid, 30 ) then
        call nzMsg( pid, "There's |cFFff9900no item search|r running." )
    elseif nzOff( ) then
        call nzSearchStop( pid )
        call nzMsg( pid, "Item search |cFFff1a1acancelled|r." )
    else
        call nzSearchStart( pid, nzRest( ), total )
    endif
    return false
endfunction

function nzCmdPrefix takes nothing returns boolean
    local integer pid = nzPid( )
    local string p = nzArg( 1 )
    if StringLength( p ) != 1 or nzFind( "0123456789abcdefghijklmnopqrstuvwxyz|", StringCase( p, false ) ) >= 0 then
        call nzMsg( pid, "The |cFFff9900prefix|r must be |cFFffcc00one|r of these symbols: |cFF00aaff! \" # $ % & ' ( ) * + , - . / : ; < = > ? @ [ \\ ] ^ _ ` { } ~|r" )
    else
        call SaveStr( nzHash, pid, 24, p )
        call nzMsg( pid, "|cFFff9900Command prefix|r changed to |cFF00aaff" + p + "|r. Example: |cFF00aaff" + p + "cmds|r" )
    endif
    return false
endfunction

function nzCmdList takes nothing returns boolean
    local integer pid = nzPid( )
    local boolean all = nzArgCount( ) < 2
    local string find = StringCase( nzRest( ), false )
    local string p = nzPrefix( pid )
    local string text = "|cFF3366ffNZCP|r commands (|cFF00aaff" + p + "cmds <text>|r shows the syntax):"
    local integer last = -1
    local integer i = 1
    local integer hits = 0
    local integer side
    local string name
    loop
        exitwhen i > LoadInteger( nzHash, -7, 0 )
        set name = LoadStr( nzHash, -7, i )
        if all then
            set side = IMinBJ( LoadInteger( nzHash, -3, StringHash( name ) ), 1 )
            if side != last and side == 0 then
                set text = text + "\n|cFFff9900Player:|r"
            elseif side != last then
                set text = text + "\n|cFFff9900Selected units:|r"
            endif
            set last = side
            set text = text + " " + p + name
        elseif nzMatch( name, find ) then
            set hits = hits + 1
            set text = text + "\n|cFF00aaff" + p + name + "|r " + LoadStr( nzHash, -5, StringHash( name ) )
        endif
        set i = i + 1
    endloop
    if not all and hits == 0 then
        set text = "No command matches |cFFe6b800[" + find + "]|r."
    endif
    call DisplayTimedTextToPlayer( Player( pid ), 0, 0, 30., text )
    return false
endfunction

function nzCmdClear takes nothing returns boolean
    if GetLocalPlayer( ) == Player( nzPid( ) ) then
        call ClearTextMessages( )
    endif
    return false
endfunction

function nzCmdNoReplay takes nothing returns boolean
    call DoNotSaveReplay( )
    call nzMsg( nzPid( ), "|cFFff9900Replay|r has been |cFFff1a1adisabled|r." )
    return false
endfunction

function nzCmdDisable takes nothing returns boolean
    local integer pid = nzPid( )
    local integer i = 0
    loop
        exitwhen i == bj_MAX_PLAYER_SLOTS
        if nzLevel( i ) > nzLevel( pid ) then
            call nzSetLevel( i, nzLevel( i ) - 1 )
            call nzMsg( i, nzColor( pid ) + " has |cFFff1a1adeactivated|r |cFF3366ffNZCP|r. Your cheater level has changed to: |cFF0099ff" + I2S( nzLevel( i ) ) + "|r." )
        endif
        set i = i + 1
    endloop
    call nzMapHackOff( pid )
    call nzZoomOff( pid )
    call nzSearchRelease( pid )
    call FlushChildHashtable( nzHash, pid )
    call nzMsg( pid, "|cFF3366ffNZCP|r has been |cFFff1a1adeactivated|r." )
    return false
endfunction

function nzParse takes integer pid, string line returns integer
    local integer len = StringLength( line )
    local integer i = 0
    local integer start = 0
    local integer count = 0
    loop
        exitwhen len == 0 or SubString( line, len - 1, len ) != " "
        set len = len - 1
    endloop
    call FlushChildHashtable( nzHash, -4 )
    call SaveInteger( nzHash, -4, 0, pid )
    loop
        exitwhen i > len
        if i == len or SubString( line, i, i + 1 ) == " " then
            if i > start then
                if count == 0 then
                    call SaveStr( nzHash, -4, 0, StringCase( SubString( line, start, i ), false ) )
                    call SaveStr( nzHash, -4, 100, SubString( line, IMinBJ( i + 1, len ), len ) )
                else
                    call SaveStr( nzHash, -4, count, SubString( line, start, i ) )
                endif
                set count = count + 1
            endif
            set start = i + 1
        endif
        set i = i + 1
    endloop
    call SaveInteger( nzHash, -4, 1, count )
    return count
endfunction

function nzRun takes integer pid, string line returns nothing
    local integer key
    local integer flags
    local integer done = 0
    local trigger cmd
    local group g
    local unit u
    if nzParse( pid, line ) == 0 then
        return
    endif
    set key = StringHash( nzArg( 0 ) )
    set cmd = LoadTriggerHandle( nzHash, -2, key )
    if cmd == null then
        return
    endif
    if nzArgCount( ) - 1 < LoadInteger( nzHash, -5, key ) then
        call nzUsage( )
        set cmd = null
        return
    endif
    set flags = LoadInteger( nzHash, -3, key )
    set g = CreateGroup( )
    call GroupEnumUnitsSelected( g, Player( pid ), null )
    call SaveUnitHandle( nzHash, -4, 0, FirstOfGroup( g ) )
    if flags != 0 and FirstOfGroup( g ) == null then
        call nzMsg( pid, "|cFFff1a1aSelect a unit|r first." )
    elseif flags <= 1 then
        call TriggerEvaluate( cmd )
    else
        loop
            set u = FirstOfGroup( g )
            exitwhen u == null
            call GroupRemoveUnit( g, u )
            call SaveUnitHandle( nzHash, -4, 0, u )
            if flags != 4 or nzCanTouch( pid ) then
                call SaveInteger( nzHash, -4, 2, done )
                call TriggerEvaluate( cmd )
                set done = done + 1
            endif
        endloop
        if done > 1 then
            call nzMsg( pid, "Applied to |cFF00cc66" + I2S( done ) + "|r units." )
        endif
    endif
    call DestroyGroup( g )
    set g = null
    set u = null
    set cmd = null
endfunction

function nzOnChat takes nothing returns boolean
    local integer pid = GetPlayerId( GetTriggerPlayer( ) )
    local string msg = GetEventPlayerChatString( )
    local string line = SubString( msg, 1, StringLength( msg ) )
    if SubString( msg, 0, 1 ) != nzPrefix( pid ) or line == "" then
        return false
    endif
    if line == LoadStr( nzHash, -1, 2 ) then
        call nzActivate( pid )
    elseif nzIsOn( pid ) then
        call nzRun( pid, line )
    endif
    return false
endfunction

function nzOnSpy takes nothing returns boolean
    local integer from = GetPlayerId( GetTriggerPlayer( ) )
    local integer i = 0
    loop
        exitwhen i == bj_MAX_PLAYER_SLOTS
        if LoadBoolean( nzHash, i, 19 ) and nzLevel( i ) > nzLevel( from ) and IsPlayerEnemy( Player( from ), Player( i ) ) then
            call nzMsg( i, "[Enemies] " + nzColor( from ) + ": " + GetEventPlayerChatString( ) )
        endif
        set i = i + 1
    endloop
    return false
endfunction

function nzArrowSlot takes eventid e returns integer
    if e == EVENT_PLAYER_ARROW_LEFT_DOWN then
        return 4
    elseif e == EVENT_PLAYER_ARROW_RIGHT_DOWN then
        return 5
    elseif e == EVENT_PLAYER_ARROW_UP_DOWN then
        return 6
    endif
    return 7
endfunction

function nzOnArrow takes nothing returns boolean
    local integer pid = GetPlayerId( GetTriggerPlayer( ) )
    local integer slot = nzArrowSlot( GetTriggerEventId( ) )
    local string key = SubString( "LRUD", slot - 4, slot - 3 )
    local string combo = LoadStr( nzHash, -1, 3 )
    local integer step = LoadInteger( nzHash, pid, 3 )
    local string seq
    if nzIsOn( pid ) then
        if HaveSavedString( nzHash, pid, slot ) then
            call nzRun( pid, LoadStr( nzHash, pid, slot ) )
        endif
        return false
    endif
    if SubString( combo, step, step + 1 ) == key then
        set step = step + 1
    else
        set seq = SubString( combo, 0, step ) + key
        set step = step + 1
        loop
            set step = step - 1
            exitwhen step == 0 or SubString( seq, StringLength( seq ) - step, StringLength( seq ) ) == SubString( combo, 0, step )
        endloop
    endif
    if step > 0 and step == StringLength( combo ) then
        set step = 0
        call nzActivate( pid )
    endif
    call SaveInteger( nzHash, pid, 3, step )
    return false
endfunction

function nzOnResource takes nothing returns boolean
    local player p = GetTriggerPlayer( )
    local integer pid = GetPlayerId( p )
    local playerstate st = GetEventPlayerState( )
    local integer on = 11
    local integer now = GetPlayerState( p, st )
    local string label = " |cFFffff00gold|r"
    local integer last
    local integer bonus
    if st == PLAYER_STATE_RESOURCE_LUMBER then
        set on = 14
        set label = " |cFF009933lumber|r"
    endif
    set last = LoadInteger( nzHash, pid, on + 2 )
    if LoadBoolean( nzHash, pid, on ) and now > last then
        set bonus = R2I( ( now - last ) * LoadInteger( nzHash, pid, on + 1 ) / 100. )
        set now = now + bonus
        call DisableTrigger( GetTriggeringTrigger( ) )
        call SetPlayerState( p, st, now )
        call EnableTrigger( GetTriggeringTrigger( ) )
        call DisplayTimedTextToPlayer( p, 0, 0, 2., "|cFF00cc66+" + I2S( now - last ) + "|r" + label + " |cFF999999(rate +" + I2S( bonus ) + ")|r" )
    endif
    call SaveInteger( nzHash, pid, on + 2, now )
    set p = null
    set st = null
    return false
endfunction

function nzOnFast takes nothing returns boolean
    local player p = GetTriggerPlayer( )
    local unit u = GetTriggerUnit( )
    local integer trained = GetTrainedUnitType( )
    local integer tech = GetResearched( )
    if LoadBoolean( nzHash, GetPlayerId( p ), 10 ) then
        if trained != 0 then
            call CreateUnit( p, trained, GetUnitX( u ), GetUnitY( u ), 270. )
        endif
        call UnitSetConstructionProgress( u, 100 )
        call UnitSetUpgradeProgress( u, 100 )
        if tech != 0 then
            call SetPlayerTechResearched( p, tech, GetPlayerTechCount( p, tech, true ) + 1 )
        endif
    endif
    set p = null
    set u = null
    return false
endfunction

function nzOnTeleport takes nothing returns boolean
    local integer pid = GetPlayerId( GetTriggerPlayer( ) )
    if LoadBoolean( nzHash, pid, 17 ) and GetIssuedOrderId( ) == LoadInteger( nzHash, pid, 18 ) then
        call SetUnitPosition( GetTriggerUnit( ), GetOrderPointX( ), GetOrderPointY( ) )
    endif
    return false
endfunction

function nzOnNoWaste takes nothing returns boolean
    if LoadBoolean( nzHash, GetPlayerId( GetTriggerPlayer( ) ), 20 ) then
        call SetItemCharges( GetManipulatedItem( ), GetItemCharges( GetManipulatedItem( ) ) + 1 )
    endif
    return false
endfunction

function nzCmd takes string name, integer flags, string usage, code action returns nothing
    local trigger t = CreateTrigger( )
    local integer key = StringHash( name )
    local integer n = LoadInteger( nzHash, -7, 0 ) + 1
    local integer need = 0
    local integer i = 0
    loop
        exitwhen i >= StringLength( usage )
        if SubString( usage, i, i + 1 ) == "<" then
            set need = need + 1
        endif
        set i = i + 1
    endloop
    call TriggerAddCondition( t, Condition( action ) )
    call SaveTriggerHandle( nzHash, -2, key, t )
    call SaveInteger( nzHash, -3, key, flags )
    call SaveInteger( nzHash, -5, key, need )
    call SaveStr( nzHash, -5, key, usage )
    call SaveInteger( nzHash, -7, 0, n )
    call SaveStr( nzHash, -7, n, name )
    set t = null
endfunction

function nzInitCommands takes nothing returns nothing
    call nzCmd( "lvl",        4, "<level>",                function nzCmdLvl )
    call nzCmd( "str",        4, "<value>",                function nzCmdStat )
    call nzCmd( "agi",        4, "<value>",                function nzCmdStat )
    call nzCmd( "int",        4, "<value>",                function nzCmdStat )
    call nzCmd( "sp",         4, "<points>",               function nzCmdStat )
    call nzCmd( "hp",         4, "<value>",                function nzCmdStat )
    call nzCmd( "mp",         4, "<value>",                function nzCmdStat )
    call nzCmd( "ms",         4, "<speed>",                function nzCmdStat )
    call nzCmd( "xp",         4, "<value>",                function nzCmdStat )
    call nzCmd( "owner",      4, "<player number>",        function nzCmdOwner )
    call nzCmd( "charge",     4, "<slot 1-6> <charges>",   function nzCmdCharge )
    call nzCmd( "dmgc",       4, "<chance%> [multiplier]", function nzCmdCrit )
    call nzCmd( "dmghp",      4, "<%>",                    function nzCmdHpDmg )
    call nzCmd( "dmgls",      4, "<%>",                    function nzCmdPct )
    call nzCmd( "dmgms",      4, "<%>",                    function nzCmdPct )
    call nzCmd( "dmgb",       4, "<%>",                    function nzCmdPct )
    call nzCmd( "dmgr",       4, "<%>",                    function nzCmdPct )
    call nzCmd( "dmgs",       4, "<%>",                    function nzCmdPct )
    call nzCmd( "vul",        4, "",                       function nzCmdInvul )
    call nzCmd( "invul",      4, "",                       function nzCmdInvul )
    call nzCmd( "kill",       4, "",                       function nzCmdKill )
    call nzCmd( "removeu",    4, "",                       function nzCmdKill )
    call nzCmd( "copy",       2, "<amount> [full]",        function nzCmdCopy )
    call nzCmd( "learn",      2, "<ability ID>",           function nzCmdLearn )
    call nzCmd( "unlearn",    2, "<ability ID>",           function nzCmdLearn )
    call nzCmd( "rg",         2, "<value|off>",            function nzCmdRegen )
    call nzCmd( "nc",         2, "[off]",                  function nzCmdNoCd )
    call nzCmd( "pause",      2, "[off]",                  function nzCmdPause )
    call nzCmd( "islot",      2, "<slot 1-6> <item ID>",   function nzCmdItemSlot )
    call nzCmd( "status",     1, "",                       function nzCmdStatus )
    call nzCmd( "unitid",     1, "",                       function nzCmdUnitId )
    call nzCmd( "itemid",     1, "<slot 1-6>",             function nzCmdItemId )
    call nzCmd( "create",     1, "<object ID>",            function nzCmdCreate )
    call nzCmd( "ritem",      1, "<amount 1-99>",          function nzCmdRandomItem )
    call nzCmd( "food",       0, "<value|use|nouse>",      function nzCmdFood )
    call nzCmd( "gold",       0, "<amount>",               function nzCmdResource )
    call nzCmd( "lumber",     0, "<amount>",               function nzCmdResource )
    call nzCmd( "giveg",      0, "<player> <amount>",      function nzCmdGive )
    call nzCmd( "givel",      0, "<player> <amount>",      function nzCmdGive )
    call nzCmd( "givef",      0, "<player> <amount>",      function nzCmdGive )
    call nzCmd( "grate",      0, "<%>",                    function nzCmdRate )
    call nzCmd( "lrate",      0, "<%>",                    function nzCmdRate )
    call nzCmd( "expr",       0, "<%>",                    function nzCmdExpRate )
    call nzCmd( "tech",       0, "<upgrade ID> [level]",   function nzCmdTech )
    call nzCmd( "kick",       0, "<player>",               function nzCmdKick )
    call nzCmd( "share",      0, "<player> <player>",      function nzCmdShare )
    call nzCmd( "unshare",    0, "<player> <player>",      function nzCmdShare )
    call nzCmd( "ploc",       0, "<x> <y>",                function nzCmdPing )
    call nzCmd( "revive",     0, "",                       function nzCmdRevive )
    call nzCmd( "pname",      0, "<name>",                 function nzCmdName )
    call nzCmd( "pzoom",      0, "<distance|off>",         function nzCmdZoom )
    call nzCmd( "act",        0, "<word>",                 function nzCmdActivator )
    call nzCmd( "bindleft",   0, "<command line|off>",     function nzCmdBind )
    call nzCmd( "bindright",  0, "<command line|off>",     function nzCmdBind )
    call nzCmd( "bindup",     0, "<command line|off>",     function nzCmdBind )
    call nzCmd( "binddown",   0, "<command line|off>",     function nzCmdBind )
    call nzCmd( "showbinds",  0, "",                       function nzCmdShowBinds )
    call nzCmd( "clearbinds", 0, "",                       function nzCmdClearBinds )
    call nzCmd( "fast",       0, "[off]",                  function nzCmdToggle )
    call nzCmd( "enemychat",  0, "[off]",                  function nzCmdToggle )
    call nzCmd( "nowaste",    0, "[off]",                  function nzCmdToggle )
    call nzCmd( "mh",         0, "[off]",                  function nzCmdMapHack )
    call nzCmd( "tp",         0, "[m|p|a|off]",            function nzCmdTeleport )
    call nzCmd( "sitem",      0, "<text|off>",             function nzCmdSearch )
    call nzCmd( "sitem!",     0, "<text|off>",             function nzCmdSearch )
    call nzCmd( "cmds",       0, "[text]",                 function nzCmdList )
    call nzCmd( "prefix",     0, "<symbol>",               function nzCmdPrefix )
    call nzCmd( "clear",      0, "",                       function nzCmdClear )
    call nzCmd( "noreplay",   0, "",                       function nzCmdNoReplay )
    call nzCmd( "disable",    0, "",                       function nzCmdDisable )
endfunction

function nzInit takes nothing returns nothing
    local timer clock = CreateTimer( )
    call TimerStart( clock, 999999., false, null )
    call SaveTimerHandle( nzHash, -1, 1, clock )
    call SaveStr( nzHash, -1, 4, "-" )
    call SaveStr( nzHash, -1, 2, "easymode" )
    call SaveStr( nzHash, -1, 3, "UUDDLR" )
    call SaveInteger( nzHash, -1, 8, 300 )
    call nzInitCommands( )
    call nzInitDamage( )
    call nzOnChatAll( function nzOnChat )
    call nzOnChatAll( function nzOnSpy )
    call nzOnArrowsAll( function nzOnArrow )
    call nzOnStateAll( PLAYER_STATE_RESOURCE_GOLD, function nzOnResource )
    call nzOnStateAll( PLAYER_STATE_RESOURCE_LUMBER, function nzOnResource )
    call nzOnAnyUnit( EVENT_PLAYER_UNIT_USE_ITEM, function nzOnNoWaste, 0 )
    call nzOnAnyUnit( EVENT_PLAYER_UNIT_CONSTRUCT_CANCEL, function nzOnFast, 0 )
    call nzOnAnyUnit( EVENT_PLAYER_UNIT_UPGRADE_CANCEL, function nzOnFast, 0 )
    call nzOnAnyUnit( EVENT_PLAYER_UNIT_TRAIN_CANCEL, function nzOnFast, 0 )
    call nzOnAnyUnit( EVENT_PLAYER_UNIT_RESEARCH_START, function nzOnFast, 0 )
    call nzOnAnyUnit( EVENT_PLAYER_UNIT_ISSUED_ORDER, function nzOnFast, 13 )
    call nzOnAnyUnit( EVENT_PLAYER_UNIT_ISSUED_UNIT_ORDER, function nzOnFast, 14 )
    call nzOnAnyUnit( EVENT_PLAYER_UNIT_ISSUED_POINT_ORDER, function nzOnTeleport, 15 )
    call nzNameActivate( "nuzamacuxe" )
    set clock = null
endfunction

// function main
call nzInit( )