constant string UJ_ASCII = " !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~"
constant string UJ_HEX = "0123456789ABCDEF"

function UJ_pot takes integer n returns integer
    local integer r = 1
    if n < 0 or n > 31 then
        return 0
    endif
    loop
        exitwhen n == 0
        set r = r * 2
        set n = n - 1
    endloop
    return r
endfunction

function UJ_shr takes integer i, integer n returns integer
    if n <= 0 then
        return i
    endif
    if n >= 32 then
        return 0
    endif
    if n == 31 then
        if i < 0 then
            return 1
        endif
        return 0
    endif
    if i >= 0 then
        return i / UJ_pot(n)
    endif
    return BlzBitAnd(i, 2147483647) / UJ_pot(n) + UJ_pot(31 - n)
endfunction

function BitwiseNOT takes integer i returns integer
    return -1 - i
endfunction

function BitwiseAND takes integer a, integer b returns integer
    return BlzBitAnd(a, b)
endfunction

function BitwiseOR takes integer a, integer b returns integer
    return BlzBitOr(a, b)
endfunction

function BitwiseXOR takes integer a, integer b returns integer
    return BlzBitXor(a, b)
endfunction

function BitwiseShiftLeft takes integer i, integer bitsToShift returns integer
    if bitsToShift < 0 or bitsToShift > 31 then
        return 0
    endif
    return i * UJ_pot(bitsToShift)
endfunction

function BitwiseShiftLeftLogical takes integer i, integer bitsToShift returns integer
    if bitsToShift < 0 or bitsToShift > 31 then
        return 0
    endif
    return i * UJ_pot(bitsToShift)
endfunction

function BitwiseShiftRight takes integer i, integer bitsToShift returns integer
    if bitsToShift <= 0 then
        return i
    endif
    if bitsToShift >= 31 then
        if i < 0 then
            return -1
        endif
        return 0
    endif
    if i >= 0 then
        return i / UJ_pot(bitsToShift)
    endif
    return -((-(i + 1)) / UJ_pot(bitsToShift)) - 1
endfunction

function BitwiseShiftRightLogical takes integer i, integer bitsToShift returns integer
    return UJ_shr(i, bitsToShift)
endfunction

function BitwiseGetBit takes integer i, integer bitIndex returns integer
    return BlzBitAnd(UJ_shr(i, bitIndex), 1)
endfunction

function BitwiseSetBit takes integer i, integer bitIndex, integer bitValue returns integer
    if bitValue != 0 then
        return BlzBitOr(i, UJ_pot(bitIndex))
    endif
    return BlzBitAnd(i, -1 - UJ_pot(bitIndex))
endfunction

function BitwiseGetByte takes integer i, integer byteIndex returns integer
    return BlzBitAnd(UJ_shr(i, byteIndex * 8), 255)
endfunction

function BitwiseSetByte takes integer i, integer byteIndex, integer byteValue returns integer
    local integer p = UJ_pot(byteIndex * 8)
    return BlzBitOr(BlzBitAnd(i, -1 - 255 * p), BlzBitAnd(byteValue, 255) * p)
endfunction

function BitwiseToInteger takes integer byte1, integer byte2, integer byte3, integer byte4 returns integer
    return BlzBitAnd(byte1, 255) * 16777216 + BlzBitAnd(byte2, 255) * 65536 + BlzBitAnd(byte3, 255) * 256 + BlzBitAnd(byte4, 255)
endfunction

function B2I takes boolean b returns integer
    if b then
        return 1
    endif
    return 0
endfunction

function B2S takes boolean b returns string
    if b then
        return "true"
    endif
    return "false"
endfunction

function IntToChar takes integer i returns string
    if i < 32 or i > 126 then
        return ""
    endif
    return SubString(UJ_ASCII, i - 32, i - 31)
endfunction

function UJ_codigo takes string c returns integer
    local integer i = 0
    loop
        exitwhen i >= 95
        if SubString(UJ_ASCII, i, i + 1) == c then
            return i + 32
        endif
        set i = i + 1
    endloop
    return 0
endfunction

function Id2String takes integer i returns string
    return IntToChar(UJ_shr(i, 24)) + IntToChar(BlzBitAnd(UJ_shr(i, 16), 255)) + IntToChar(BlzBitAnd(UJ_shr(i, 8), 255)) + IntToChar(BlzBitAnd(i, 255))
endfunction

function String2Id takes string idString returns integer
    local integer r = 0
    local integer i = 0
    local integer n = StringLength(idString)
    loop
        exitwhen i >= n
        set r = r * 256 + UJ_codigo(SubString(idString, i, i + 1))
        set i = i + 1
    endloop
    return r
endfunction

function IntToHex takes integer i returns string
    local string s = ""
    local integer k = 0
    if i == 0 then
        return "0"
    endif
    loop
        exitwhen i == 0 or k >= 8
        set s = SubString(UJ_HEX, BlzBitAnd(i, 15), BlzBitAnd(i, 15) + 1) + s
        set i = UJ_shr(i, 4)
        set k = k + 1
    endloop
    return s
endfunction

function HexToInt takes string hex returns integer
    local string s = StringCase(hex, true)
    local integer r = 0
    local integer i = 0
    local integer n = StringLength(s)
    local integer d
    local string c
    if SubString(s, 0, 2) == "0X" then
        set i = 2
    elseif SubString(s, 0, 1) == "$" then
        set i = 1
    endif
    loop
        exitwhen i >= n
        set c = SubString(s, i, i + 1)
        set d = 0
        loop
            exitwhen d >= 16 or SubString(UJ_HEX, d, d + 1) == c
            set d = d + 1
        endloop
        exitwhen d >= 16
        set r = r * 16 + d
        set i = i + 1
    endloop
    return r
endfunction

function IntToRoman takes integer i returns string
    local string s = ""
    if i <= 0 or i >= 4000 then
        return ""
    endif
    loop
        exitwhen i < 1000
        set s = s + "M"
        set i = i - 1000
    endloop
    if i >= 900 then
        set s = s + "CM"
        set i = i - 900
    elseif i >= 500 then
        set s = s + "D"
        set i = i - 500
    elseif i >= 400 then
        set s = s + "CD"
        set i = i - 400
    endif
    loop
        exitwhen i < 100
        set s = s + "C"
        set i = i - 100
    endloop
    if i >= 90 then
        set s = s + "XC"
        set i = i - 90
    elseif i >= 50 then
        set s = s + "L"
        set i = i - 50
    elseif i >= 40 then
        set s = s + "XL"
        set i = i - 40
    endif
    loop
        exitwhen i < 10
        set s = s + "X"
        set i = i - 10
    endloop
    if i == 9 then
        return s + "IX"
    elseif i >= 5 then
        set s = s + "V"
        set i = i - 5
    elseif i == 4 then
        return s + "IV"
    endif
    loop
        exitwhen i < 1
        set s = s + "I"
        set i = i - 1
    endloop
    return s
endfunction

function MathRealAbs takes real r returns real
    if r < 0 then
        return -r
    endif
    return r
endfunction

function MathRealFloor takes real r returns real
    local real f = I2R(R2I(r))
    if f > r then
        return f - 1.0
    endif
    return f
endfunction

function MathRealCeil takes real r returns real
    local real f = I2R(R2I(r))
    if f < r then
        return f + 1.0
    endif
    return f
endfunction

function MathRealRound takes real r returns real
    if r < 0 then
        return -MathRealFloor(-r + 0.5)
    endif
    return MathRealFloor(r + 0.5)
endfunction

function MathRealLn takes real r returns real
    local integer k = 0
    local real z
    local real z2
    local real termo
    local real soma
    local integer n = 1
    if r <= 0 then
        return 0.0
    endif
    loop
        exitwhen r < 2.0
        set r = r / 2.0
        set k = k + 1
    endloop
    loop
        exitwhen r >= 0.5
        set r = r * 2.0
        set k = k - 1
    endloop
    set z = (r - 1.0) / (r + 1.0)
    set z2 = z * z
    set termo = z
    set soma = 0.0
    loop
        exitwhen n > 41
        set soma = soma + termo / I2R(n)
        set termo = termo * z2
        set n = n + 2
    endloop
    return 2.0 * soma + I2R(k) * 0.6931471805599453
endfunction

function MathRealLog takes real r, integer base returns real
    local real b = MathRealLn(I2R(base))
    if b == 0 then
        return 0.0
    endif
    return MathRealLn(r) / b
endfunction

function MathIntegerLn takes integer i returns real
    return MathRealLn(I2R(i))
endfunction

function MathIntegerLog takes integer i, integer base returns real
    return MathRealLog(I2R(i), base)
endfunction

function MathRealModulo takes real dividend, real divisor returns real
    if divisor == 0 then
        return 0.0
    endif
    return dividend - I2R(R2I(dividend / divisor)) * divisor
endfunction

function MathRealMin takes real a, real b returns real
    if a < b then
        return a
    endif
    return b
endfunction

function MathRealMax takes real a, real b returns real
    if a > b then
        return a
    endif
    return b
endfunction

function MathRealSign takes real r returns integer
    if r > 0 then
        return 1
    elseif r < 0 then
        return -1
    endif
    return 0
endfunction

function MathRealClamp takes real value, real min, real max returns real
    if value < min then
        return min
    elseif value > max then
        return max
    endif
    return value
endfunction

function MathRealLerp takes real a, real b, real t returns real
    return a + (b - a) * t
endfunction

function MathIntegerAbs takes integer i returns integer
    if i < 0 then
        return -i
    endif
    return i
endfunction

function MathIntegerModulo takes integer dividend, integer divisor returns integer
    if divisor == 0 then
        return 0
    endif
    return dividend - (dividend / divisor) * divisor
endfunction

function MathIntegerMin takes integer a, integer b returns integer
    if a < b then
        return a
    endif
    return b
endfunction

function MathIntegerMax takes integer a, integer b returns integer
    if a > b then
        return a
    endif
    return b
endfunction

function MathIntegerSign takes integer i returns integer
    if i > 0 then
        return 1
    elseif i < 0 then
        return -1
    endif
    return 0
endfunction

function MathIntegerClamp takes integer value, integer min, integer max returns integer
    if value < min then
        return min
    elseif value > max then
        return max
    endif
    return value
endfunction

function MathSinDeg takes real r returns real
    return Sin(r * bj_DEGTORAD)
endfunction

function MathCosDeg takes real r returns real
    return Cos(r * bj_DEGTORAD)
endfunction

function MathTanDeg takes real r returns real
    return Tan(r * bj_DEGTORAD)
endfunction

function MathPointProjectionX takes real x, real angle, real distance returns real
    return x + distance * Cos(angle * bj_DEGTORAD)
endfunction

function MathPointProjectionY takes real y, real angle, real distance returns real
    return y + distance * Sin(angle * bj_DEGTORAD)
endfunction

function MathAngleBetweenPoints takes real fromX, real fromY, real toX, real toY returns real
    return bj_RADTODEG * Atan2(toY - fromY, toX - fromX)
endfunction

function MathDistanceBetweenPoints takes real fromX, real fromY, real toX, real toY returns real
    return SquareRoot((toX - fromX) * (toX - fromX) + (toY - fromY) * (toY - fromY))
endfunction

function MathAngleBetweenLocations takes location fromLoc, location toLoc returns real
    return bj_RADTODEG * Atan2(GetLocationY(toLoc) - GetLocationY(fromLoc), GetLocationX(toLoc) - GetLocationX(fromLoc))
endfunction

function MathDistanceBetweenLocations takes location fromLoc, location toLoc returns real
    local real dx = GetLocationX(toLoc) - GetLocationX(fromLoc)
    local real dy = GetLocationY(toLoc) - GetLocationY(fromLoc)
    return SquareRoot(dx * dx + dy * dy)
endfunction

function UJ_caixa takes string s, boolean caseSensitive returns string
    if caseSensitive then
        return s
    endif
    return StringCase(s, true)
endfunction

function StringFind takes string s, string whichString, boolean caseSensitive returns integer
    local string a = UJ_caixa(s, caseSensitive)
    local string b = UJ_caixa(whichString, caseSensitive)
    local integer n = StringLength(a)
    local integer m = StringLength(b)
    local integer i = 0
    if m == 0 then
        return 0
    endif
    loop
        exitwhen i + m > n
        if SubString(a, i, i + m) == b then
            return i
        endif
        set i = i + 1
    endloop
    return -1
endfunction

function StringContains takes string s, string whichString, boolean caseSensitive returns boolean
    return StringFind(s, whichString, caseSensitive) >= 0
endfunction

function UJ_no_conjunto takes string c, string conjunto returns boolean
    local integer i = 0
    local integer n = StringLength(conjunto)
    loop
        exitwhen i >= n
        if SubString(conjunto, i, i + 1) == c then
            return true
        endif
        set i = i + 1
    endloop
    return false
endfunction

function UJ_acha_conjunto takes string s, string conjunto, boolean caseSensitive, boolean dentro, boolean doFim returns integer
    local string a = UJ_caixa(s, caseSensitive)
    local string b = UJ_caixa(conjunto, caseSensitive)
    local integer n = StringLength(a)
    local integer i = 0
    local integer passo = 1
    if doFim then
        set i = n - 1
        set passo = -1
    endif
    loop
        exitwhen i < 0 or i >= n
        if UJ_no_conjunto(SubString(a, i, i + 1), b) == dentro then
            return i
        endif
        set i = i + passo
    endloop
    return -1
endfunction

function StringFindFirstOf takes string s, string whichString, boolean caseSensitive returns integer
    return UJ_acha_conjunto(s, whichString, caseSensitive, true, false)
endfunction

function StringFindFirstNotOf takes string s, string whichString, boolean caseSensitive returns integer
    return UJ_acha_conjunto(s, whichString, caseSensitive, false, false)
endfunction

function StringFindLastOf takes string s, string whichString, boolean caseSensitive returns integer
    return UJ_acha_conjunto(s, whichString, caseSensitive, true, true)
endfunction

function StringFindLastNotOf takes string s, string whichString, boolean caseSensitive returns integer
    return UJ_acha_conjunto(s, whichString, caseSensitive, false, true)
endfunction

function StringCount takes string s, string whichString, boolean caseSensitive returns integer
    local string a = UJ_caixa(s, caseSensitive)
    local string b = UJ_caixa(whichString, caseSensitive)
    local integer n = StringLength(a)
    local integer m = StringLength(b)
    local integer i = 0
    local integer c = 0
    if m == 0 then
        return 0
    endif
    loop
        exitwhen i + m > n
        if SubString(a, i, i + m) == b then
            set c = c + 1
            set i = i + m
        else
            set i = i + 1
        endif
    endloop
    return c
endfunction

function UJ_branco takes string c returns boolean
    return c == " " or c == "\t" or c == "\n" or c == "\r"
endfunction

function StringTrimLeft takes string s, boolean caseSensitive returns string
    local integer i = 0
    local integer n = StringLength(s)
    loop
        exitwhen i >= n or not UJ_branco(SubString(s, i, i + 1))
        set i = i + 1
    endloop
    return SubString(s, i, n)
endfunction

function StringTrimRight takes string s, boolean caseSensitive returns string
    local integer n = StringLength(s)
    loop
        exitwhen n <= 0 or not UJ_branco(SubString(s, n - 1, n))
        set n = n - 1
    endloop
    return SubString(s, 0, n)
endfunction

function StringTrim takes string s, boolean caseSensitive returns string
    return StringTrimRight(StringTrimLeft(s, caseSensitive), caseSensitive)
endfunction

function StringReverse takes string s, boolean caseSensitive returns string
    local string r = ""
    local integer i = StringLength(s)
    loop
        exitwhen i <= 0
        set r = r + SubString(s, i - 1, i)
        set i = i - 1
    endloop
    return r
endfunction

function StringReplace takes string s, string whichString, string replaceWith, boolean caseSensitive returns string
    local string a = UJ_caixa(s, caseSensitive)
    local string b = UJ_caixa(whichString, caseSensitive)
    local integer n = StringLength(a)
    local integer m = StringLength(b)
    local integer i = 0
    local integer ini = 0
    local string r = ""
    if m == 0 then
        return s
    endif
    loop
        exitwhen i + m > n
        if SubString(a, i, i + m) == b then
            set r = r + SubString(s, ini, i) + replaceWith
            set i = i + m
            set ini = i
        else
            set i = i + 1
        endif
    endloop
    return r + SubString(s, ini, n)
endfunction

function StringInsert takes string s, string whichString, integer whichPosition, boolean caseSensitive returns string
    local integer n = StringLength(s)
    if whichPosition < 0 then
        set whichPosition = 0
    elseif whichPosition > n then
        set whichPosition = n
    endif
    return SubString(s, 0, whichPosition) + whichString + SubString(s, whichPosition, n)
endfunction

function StringEncrypt takes string s, string keyString returns string
    return s
endfunction

function StringDecrypt takes string s, string keyString returns string
    return s
endfunction

function GroupGetCount takes group whichGroup returns integer
    return BlzGroupGetSize(whichGroup)
endfunction

function GroupContainsUnit takes group whichGroup, unit whichUnit returns boolean
    return IsUnitInGroup(whichUnit, whichGroup)
endfunction

function GroupGetUnitByIndex takes group whichGroup, integer index returns unit
    return BlzGroupUnitAt(whichGroup, index)
endfunction

function GroupAddGroupEx takes group destGroup, group sourceGroup returns integer
    return BlzGroupAddGroupFast(sourceGroup, destGroup)
endfunction

function GroupRemoveGroupEx takes group destGroup, group sourceGroup returns integer
    return BlzGroupRemoveGroupFast(sourceGroup, destGroup)
endfunction

function GetPlayerMask takes player whichPlayer returns integer
    return UJ_pot(GetPlayerId(whichPlayer))
endfunction

function ForceGetPlayerMask takes force whichForce returns integer
    local integer i = 0
    local integer m = 0
    loop
        exitwhen i >= bj_MAX_PLAYER_SLOTS
        if IsPlayerInForce(Player(i), whichForce) then
            set m = m + UJ_pot(i)
        endif
        set i = i + 1
    endloop
    return m
endfunction

function ForceCountPlayers takes force whichForce returns integer
    local integer i = 0
    local integer c = 0
    loop
        exitwhen i >= bj_MAX_PLAYER_SLOTS
        if IsPlayerInForce(Player(i), whichForce) then
            set c = c + 1
        endif
        set i = i + 1
    endloop
    return c
endfunction

function IsUnitAlive takes unit whichUnit returns boolean
    return GetUnitTypeId(whichUnit) != 0 and not IsUnitType(whichUnit, UNIT_TYPE_DEAD)
endfunction

function IsUnitDead takes unit whichUnit returns boolean
    return GetUnitTypeId(whichUnit) == 0 or IsUnitType(whichUnit, UNIT_TYPE_DEAD)
endfunction

function IsUnitHero takes unit whichUnit returns boolean
    return IsUnitType(whichUnit, UNIT_TYPE_HERO)
endfunction

function IsUnitPeon takes unit whichUnit returns boolean
    return IsUnitType(whichUnit, UNIT_TYPE_PEON)
endfunction

function IsUnitFlying takes unit whichUnit returns boolean
    return IsUnitType(whichUnit, UNIT_TYPE_FLYING)
endfunction

function IsUnitStunned takes unit whichUnit returns boolean
    return IsUnitType(whichUnit, UNIT_TYPE_STUNNED)
endfunction

function IsUnitSnared takes unit whichUnit returns boolean
    return IsUnitType(whichUnit, UNIT_TYPE_SNARED)
endfunction

function GetUnitScale takes unit whichUnit returns real
    return BlzGetUnitRealField(whichUnit, UNIT_RF_SCALING_VALUE)
endfunction

function DisableUnitAbility takes unit whichUnit, integer abilityTypeId, boolean hide, boolean disable returns nothing
    call BlzUnitDisableAbility(whichUnit, abilityTypeId, disable, hide)
endfunction

function GetUnitMaxMana takes unit whichUnit returns real
    return I2R(BlzGetUnitMaxMana(whichUnit))
endfunction

function SetUnitMaxMana takes unit whichUnit, real maxMana returns nothing
    call BlzSetUnitMaxMana(whichUnit, R2I(maxMana))
endfunction

function SetUnitFacingEx takes unit whichUnit, real facingAngle, boolean isInstant returns nothing
    if isInstant then
        call BlzSetUnitFacingEx(whichUnit, facingAngle)
    else
        call SetUnitFacing(whichUnit, facingAngle)
    endif
endfunction

function ItemAddAbility takes item whichItem, ability whichAbility returns boolean
    return BlzItemAddAbility(whichItem, BlzGetAbilityId(whichAbility))
endfunction

function ItemRemoveAbility takes item whichItem, ability whichAbility returns boolean
    return BlzItemRemoveAbility(whichItem, BlzGetAbilityId(whichAbility))
endfunction

function GetLightningColourA takes lightning whichBolt returns integer
    return R2I(GetLightningColorA(whichBolt) * 255.0 + 0.5)
endfunction

function GetLightningColourR takes lightning whichBolt returns integer
    return R2I(GetLightningColorR(whichBolt) * 255.0 + 0.5)
endfunction

function GetLightningColourG takes lightning whichBolt returns integer
    return R2I(GetLightningColorG(whichBolt) * 255.0 + 0.5)
endfunction

function GetLightningColourB takes lightning whichBolt returns integer
    return R2I(GetLightningColorB(whichBolt) * 255.0 + 0.5)
endfunction

function SetLightningColour takes lightning whichBolt, integer red, integer green, integer blue, integer alpha returns boolean
    return SetLightningColor(whichBolt, red / 255.0, green / 255.0, blue / 255.0, alpha / 255.0)
endfunction

function SetSpecialEffectColour takes effect whichEffect, integer colour returns nothing
    call BlzSetSpecialEffectColor(whichEffect, BlzBitAnd(UJ_shr(colour, 16), 255), BlzBitAnd(UJ_shr(colour, 8), 255), BlzBitAnd(colour, 255))
    call BlzSetSpecialEffectAlpha(whichEffect, UJ_shr(colour, 24))
endfunction

function SetSpecialEffectPosition takes effect whichEffect, real x, real y returns nothing
    call BlzSetSpecialEffectX(whichEffect, x)
    call BlzSetSpecialEffectY(whichEffect, y)
endfunction

function SetFrameVertexColour takes framehandle whichFrame, integer alpha, integer red, integer green, integer blue returns nothing
    call BlzFrameSetVertexColor(whichFrame, BlzConvertColor(alpha, red, green, blue))
endfunction

function SetFrameAllPoints takes framehandle whichFrame, framehandle relative returns boolean
    call BlzFrameSetAllPoints(whichFrame, relative)
    return true
endfunction

function SetFrameFocus takes framehandle whichFrame, boolean isFocus returns boolean
    call BlzFrameSetFocus(whichFrame, isFocus)
    return true
endfunction

function GetJassArrayLimit takes nothing returns integer
    return JASS_MAX_ARRAY_SIZE
endfunction

function GetTextTagLimit takes nothing returns integer
    return 100
endfunction
