// ==============================================================================================
// ==============================================================================================

function KKN_frame_exec takes nothing returns nothing
    local string n=LoadStr(DB_ui_ht,GetHandleId(GetTriggeringTrigger()),1)
    if n!=null and n!="" then
        call ExecuteFunc(n)
    endif
endfunction

function DzFrameSetScript takes integer frame,integer eventId,string xfunc,boolean sync returns nothing
    local trigger t
    if xfunc==null or xfunc=="" then
        call DzFrameSetScriptByCode(frame,eventId,null,sync)
        return
    endif
    call DzFrameSetScriptByCode(frame,eventId,function KKN_frame_exec,sync)
    set t=LoadTriggerHandle(DB_ui_ht,frame,100+eventId)
    if t!=null then
        call SaveStr(DB_ui_ht,GetHandleId(t),1,xfunc)
    endif
    set t=null
endfunction

function EXGetAbilityString takes integer abilcode,integer level,integer data_type returns string
    local integer lv=level-1
    if lv<0 then
        set lv=0
    endif
    if data_type==203 then
        return GetObjectName(abilcode)
    elseif data_type==204 then
        return BlzGetAbilityIcon(abilcode)
    elseif data_type==215 then
        return BlzGetAbilityTooltip(abilcode,lv)
    elseif data_type==218 then
        return BlzGetAbilityExtendedTooltip(abilcode,lv)
    elseif data_type==214 then
        return BlzGetAbilityResearchTooltip(abilcode,lv)
    elseif data_type==217 then
        return BlzGetAbilityResearchExtendedTooltip(abilcode,lv)
    elseif data_type==216 then
        return BlzGetAbilityActivatedTooltip(abilcode,lv)
    elseif data_type==219 then
        return BlzGetAbilityActivatedExtendedTooltip(abilcode,lv)
    elseif data_type==220 then
        return BlzGetAbilityActivatedIcon(abilcode)
    endif
    return ""
endfunction
