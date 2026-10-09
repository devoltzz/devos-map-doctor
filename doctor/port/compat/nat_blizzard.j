function DzGetLocale takes nothing returns string
    return BlzGetLocale()
endfunction

function DzGetClientWidth takes nothing returns integer
    return BlzGetLocalClientWidth()
endfunction

function DzGetClientHeight takes nothing returns integer
    return BlzGetLocalClientHeight()
endfunction

function DzSetWar3MapMap takes string map returns nothing
    if map==null or map=="" then
        return
    endif
    call BlzChangeMinimapTerrainTex(map)
endfunction

function EXGetUnitAbilityByIndex takes unit u,integer index returns ability
    return BlzGetUnitAbilityByIndex(u,index)
endfunction

function EXGetAbilityId takes ability abil returns integer
    return BlzGetAbilityId(abil)
endfunction

function SetUnitName takes unit whichUnit,string name returns nothing
    call DzSetUnitName(whichUnit,name)
endfunction

function SetUnitModel takes unit whichUnit,string path returns nothing
    call DzSetUnitModel(whichUnit,path)
endfunction

function DzGetUnitCollisionSize takes unit whichUnit returns real
    if whichUnit==null then
        return 0.0
    endif
    return BlzGetUnitCollisionSize(whichUnit)
endfunction

function DzSetUnitMissileModel takes unit whichUnit,string modelFile returns nothing
    if whichUnit==null or modelFile==null then
        return
    endif
    call BlzSetUnitWeaponStringField(whichUnit,UNIT_WEAPON_SF_ATTACK_PROJECTILE_ART,0,modelFile)
    call BlzSetUnitWeaponStringField(whichUnit,UNIT_WEAPON_SF_ATTACK_PROJECTILE_ART,1,modelFile)
endfunction

function SetUnitMissileModel takes unit whichUnit,string modelFile returns nothing
    call DzSetUnitMissileModel(whichUnit,modelFile)
endfunction

function DzSetEffectScale takes effect e,real scale returns nothing
    if e==null then
        return
    endif
    call BlzSetSpecialEffectScale(e,scale)
endfunction

function DzRemoveEffect takes effect whichEffect returns boolean
    call BlzRemoveEffect(whichEffect)
    return true
endfunction

function DzRemoveEffectTimed takes effect whichEffect,real time returns boolean
    call RemoveEffectAfterTimeBJ(whichEffect,time)
    return true
endfunction

hashtable KKN_fx_alfa = InitHashtable()

function EXSetEffectColor takes effect e,integer argb returns nothing
    local integer b=ModuloInteger(argb,256)
    local integer rest=(argb-b)/256
    local integer g=ModuloInteger(rest,256)
    local integer r
    local integer a
    if e==null then
        return
    endif
    set rest=(rest-g)/256
    set r=ModuloInteger(rest,256)
    set a=ModuloInteger((rest-r)/256,256)
    call BlzSetSpecialEffectColor(e,r,g,b)
    call BlzSetSpecialEffectAlpha(e,a)
    call SaveInteger(KKN_fx_alfa,GetHandleId(e),0,a)
endfunction

function EXSetEffectVisible takes effect e,boolean visible returns nothing
    if e==null then
        return
    endif
    if visible then
        if HaveSavedInteger(KKN_fx_alfa,GetHandleId(e),0) then
            call BlzSetSpecialEffectAlpha(e,LoadInteger(KKN_fx_alfa,GetHandleId(e),0))
        else
            call BlzSetSpecialEffectAlpha(e,255)
        endif
    else
        call BlzSetSpecialEffectAlpha(e,0)
    endif
endfunction

function EXPlayEffectAnimation takes effect e,string animationName,string linkName returns nothing
    if e==null or animationName==null or animationName=="" then
        return
    endif
    call BlzSetSpecialEffectAnimation(e,animationName)
endfunction

function DzFrameIsVisible takes integer frame returns boolean
    local framehandle f=DB_fh(frame)
    if f==null then
        return false
    endif
    return BlzFrameIsVisible(f)
endfunction
