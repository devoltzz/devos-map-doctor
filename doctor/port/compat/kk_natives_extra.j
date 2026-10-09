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
    return BlzConvertColor(a,r,g,b)
endfunction

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
