function IsReplayMode takes nothing returns boolean
    return false
endfunction

string array KKN_qcb_nome
integer KKN_qcb_n = 0

function KKN_qcb_tique takes nothing returns nothing
    local integer i=0
    loop
        exitwhen i>=KKN_qcb_n
        call ExecuteFunc(KKN_qcb_nome[i])
        set i=i+1
    endloop
endfunction

function DzFrameSetUpdateCallback takes string xfunc returns nothing
    local integer i=0
    if xfunc==null or xfunc=="" then
        return
    endif
    loop
        exitwhen i>=KKN_qcb_n
        if KKN_qcb_nome[i]==xfunc then
            return
        endif
        set i=i+1
    endloop
    if KKN_qcb_n==0 then
        call DzFrameSetUpdateCallbackByCode(function KKN_qcb_tique)
    endif
    set KKN_qcb_nome[KKN_qcb_n]=xfunc
    set KKN_qcb_n=KKN_qcb_n+1
endfunction

function DzUnlockOpCodeLimit takes boolean enable returns nothing
endfunction

function DzUnlockBlpSizeLimit takes boolean enable returns nothing
endfunction

function DzFixUnitEventMemoryLeak takes nothing returns nothing
endfunction

function DzToggleFPS takes boolean show returns nothing
endfunction

function DzEnableHashtableSetNull takes boolean is_enable returns nothing
endfunction

function GetMouseVectorX takes nothing returns real
    return BlzPixelToFrameX(BlzGetMouseScreenPosX())/0.8*1024.0
endfunction

function GetMouseVectorY takes nothing returns real
    return BlzPixelToFrameY(BlzGetMouseScreenPosY())/0.6*768.0
endfunction

function DzGroupGetCount takes group g returns integer
    return BlzGroupGetSize(g)
endfunction

function DzGroupGetUnitAt takes group g,integer index returns unit
    return BlzGroupUnitAt(g,index)
endfunction

location KKN_tz_ponto=Location(0.0,0.0)

function DzGetTerrainZ takes real x,real y returns real
    if DB_z_w>=2 and DB_z_h>=2 then
        return KK_z(x,y)
    endif
    call MoveLocation(KKN_tz_ponto,x,y)
    return GetLocationZ(KKN_tz_ponto)
endfunction

function DzSetUnitAbilityEnable takes unit u,integer abil_id returns boolean
    if u==null or GetUnitAbilityLevel(u,abil_id)<=0 then
        return false
    endif
    call BlzUnitDisableAbility(u,abil_id,false,false)
    return true
endfunction

function DzSetUnitAbilityDisable takes unit u,integer abil_id returns boolean
    if u==null or GetUnitAbilityLevel(u,abil_id)<=0 then
        return false
    endif
    call BlzUnitDisableAbility(u,abil_id,true,false)
    return true
endfunction

function DzSetUnitSelectScale takes unit Unit,real scale returns nothing
    call BlzSetUnitRealField(Unit,UNIT_RF_SELECTION_SCALE,scale)
endfunction

function DzPositionCanPlaceAround takes real x,real y,real collision_size,integer collision_type returns boolean
    return not IsTerrainPathable(x,y,PATHING_TYPE_WALKABILITY)
endfunction

function DzUnitCanPlaceAround takes widget obj,real x,real y returns boolean
    return not IsTerrainPathable(x,y,PATHING_TYPE_WALKABILITY)
endfunction

hashtable KKN_vinc_ht=InitHashtable()

function KKN_vinc_modelo takes effect e returns string
    local string m=LoadStr(DB_ef_ht,GetHandleId(e),2)
    if m==null or m=="" then
        set m=LoadStr(DB_ef_ht,GetHandleId(e),1)
    endif
    return m
endfunction

function DzUnbindEffect takes effect whichEffect returns nothing
    local effect c
    if whichEffect==null then
        return
    endif
    set c=LoadEffectHandle(KKN_vinc_ht,GetHandleId(whichEffect),0)
    if c!=null then
        call DestroyEffect(c)
        call RemoveSavedHandle(KKN_vinc_ht,GetHandleId(whichEffect),0)
    endif
    set c=null
endfunction

function DzBindEffect takes widget parent,string attachPoint,effect whichEffect returns nothing
    local string m
    if whichEffect==null or parent==null or DB_ef_ht==null then
        return
    endif
    call DzUnbindEffect(whichEffect)
    set m=KKN_vinc_modelo(whichEffect)
    if m==null or m=="" then
        return
    endif
    call BlzSetSpecialEffectAlpha(whichEffect,0)
    call SaveEffectHandle(KKN_vinc_ht,GetHandleId(whichEffect),0,AddSpecialEffectTarget(m,parent,attachPoint))
endfunction

function DzSetEffectAttachedModelScale takes effect whichEffect,real scaleX,real scaleY,real scaleZ returns boolean
    local effect c
    if whichEffect==null then
        return false
    endif
    set c=LoadEffectHandle(KKN_vinc_ht,GetHandleId(whichEffect),0)
    if c==null then
        return false
    endif
    call BlzSetSpecialEffectMatrixScale(c,scaleX,scaleY,scaleZ)
    set c=null
    return true
endfunction
