function EXDisplayChat takes player p,integer chat_recipient,string message returns nothing
    if p==null then
        return
    endif
    if message==null then
        set message=""
    endif
    call BlzDisplayChatMessage(p,chat_recipient,message)
endfunction

function DzGetColor takes integer r,integer g,integer b,integer a returns integer
    //{{KK_SE:KK_DZ_REAL}}
    return BlzConvertColor(r,g,b,a)
    //{{KK_FIMSE:KK_DZ_REAL}}
    return BlzConvertColor(a,r,g,b)
endfunction

//{{KK_SE:KK_XP}}
constant string DB_xp_tabela="{{KK_XP_TABELA}}"
constant real DB_XP_A={{KK_XP_A}}
constant real DB_XP_B={{KK_XP_B}}
constant real DB_XP_C={{KK_XP_C}}

function DzGetUnitNeededXP takes unit whichUnit,integer level returns integer
    local integer n=StringLength(DB_xp_tabela)
    local integer i=0
    local integer j
    local integer niv=1
    local real tot=0.0
    local real q
    if level<1 then
        return 0
    endif
    loop
        exitwhen i>=n or niv>level
        set j=i
        loop
            exitwhen j>=n or SubString(DB_xp_tabela, j, j+1)==","
            set j=j+1
        endloop
        set niv=niv+1
        set tot=S2R(SubString(DB_xp_tabela, i, j))
        set i=j+1
    endloop
    if niv>level then
        return R2I(tot)
    endif
    if DB_XP_A==1.0 then
        set q=I2R(level+1-niv)
        return R2I(tot+DB_XP_B*(I2R((level+1)*(level+2))-I2R((niv)*(niv+1)))/2.0+DB_XP_C*q)
    endif
    loop
        exitwhen niv>level
        set niv=niv+1
        set tot=DB_XP_A*tot+DB_XP_B*I2R(niv)+DB_XP_C
    endloop
    return R2I(tot)
endfunction

//{{KK_FIMSE:KK_XP}}
function DzSetUnitPortrait takes unit whichUnit,string modelFile returns nothing
endfunction

function DzUnitDisableAttack takes unit whichUnit,boolean disable returns nothing
    if whichUnit==null then
        return
    endif
    call BlzUnitDisableAbility(whichUnit,'Aatk',disable,false)
    if disable then
        call BlzUnitInterruptAttack(whichUnit)
    endif
endfunction

function DzReviveUnit takes unit whichUnit,player whichPlayer,real hp,real mp,real x,real y returns nothing
    local unit nu
    if whichUnit==null then
        return
    endif
    if whichPlayer==null then
        set whichPlayer=GetOwningPlayer(whichUnit)
    endif
    if IsUnitType(whichUnit,UNIT_TYPE_HERO) then
        call ReviveHero(whichUnit,x,y,false)
        if hp>0.0 then
            call SetUnitState(whichUnit,UNIT_STATE_LIFE,hp)
        endif
        call SetUnitState(whichUnit,UNIT_STATE_MANA,mp)
        if whichPlayer!=GetOwningPlayer(whichUnit) then
            call SetUnitOwner(whichUnit,whichPlayer,true)
        endif
        return
    endif
    set nu=CreateUnit(whichPlayer,GetUnitTypeId(whichUnit),x,y,GetUnitFacing(whichUnit))
    if hp>0.0 then
        call SetUnitState(nu,UNIT_STATE_LIFE,hp)
    endif
    call SetUnitState(nu,UNIT_STATE_MANA,mp)
    set nu=null
endfunction

function DzFrameSetAlpha takes integer frame,integer alpha returns nothing
    local framehandle f=DB_fh(frame)
    if f==null then
        return
    endif
    if alpha<0 then
        set alpha=0
    elseif alpha>255 then
        set alpha=255
    endif
    call BlzFrameSetAlpha(f,alpha)
    set f=null
endfunction

function DzFrameSetAnimate takes integer frame,integer animId,boolean autocast returns nothing
    local framehandle f=DB_fh(frame)
    if f==null then
        return
    endif
    if autocast then
        call BlzFrameSetSpriteAnimate(f,animId,1)
    else
        call BlzFrameSetSpriteAnimate(f,animId,0)
    endif
    set f=null
endfunction

function DzFrameSetAnimateOffset takes integer frame,real offset returns nothing
endfunction

function DzFrameGetMinimap takes nothing returns integer
    return DB_origin(ORIGIN_FRAME_MINIMAP, 0)
endfunction

function DzFrameGetMinimapButton takes integer buttonId returns integer
    return DB_origin(ORIGIN_FRAME_MINIMAP_BUTTON, buttonId)
endfunction
