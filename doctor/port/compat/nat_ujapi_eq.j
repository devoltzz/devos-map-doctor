function AddAbilityBooleanLevelArrayField takes ability whichAbility, abilitybooleanlevelarrayfield whichField, integer level, boolean value returns boolean
    return BlzAddAbilityBooleanLevelArrayField(whichAbility, whichField, level, value)
endfunction

function AddAbilityIntegerLevelArrayField takes ability whichAbility, abilityintegerlevelarrayfield whichField, integer level, integer value returns boolean
    return BlzAddAbilityIntegerLevelArrayField(whichAbility, whichField, level, value)
endfunction

function AddAbilityRealLevelArrayField takes ability whichAbility, abilityreallevelarrayfield whichField, integer level, real value returns boolean
    return BlzAddAbilityRealLevelArrayField(whichAbility, whichField, level, value)
endfunction

function AddAbilityStringLevelArrayField takes ability whichAbility, abilitystringlevelarrayfield whichField, integer level, string value returns boolean
    return BlzAddAbilityStringLevelArrayField(whichAbility, whichField, level, value)
endfunction

function AddFrameText takes framehandle whichFrame, string text returns nothing
    call BlzFrameAddText(whichFrame, text)
endfunction

function ClearFrameAllPoints takes framehandle whichFrame returns nothing
    call BlzFrameClearAllPoints(whichFrame)
endfunction

function ClickFrame takes framehandle whichFrame returns nothing
    call BlzFrameClick(whichFrame)
endfunction

function ConvertAbilityType takes integer i returns integer
    return i
endfunction

function ConvertAttachmentType takes integer i returns integer
    return i
endfunction

function ConvertBoneType takes integer i returns integer
    return i
endfunction

function ConvertBonusAttribute takes integer i returns integer
    return i
endfunction

function ConvertCollisionType takes integer i returns integer
    return i
endfunction

function ConvertColour takes integer alpha, integer red, integer green, integer blue returns integer
    return BlzConvertColor(alpha, red, green, blue)
endfunction

function ConvertConnectionType takes integer i returns integer
    return i
endfunction

function ConvertControlStyleFlag takes integer i returns integer
    return i
endfunction

function ConvertCursorAnimType takes integer i returns integer
    return i
endfunction

function ConvertDamageFlag takes integer i returns integer
    return i
endfunction

function ConvertFrameState takes integer i returns integer
    return i
endfunction

function ConvertGridStyleFlag takes integer i returns integer
    return i
endfunction

function ConvertItemDisableFlag takes integer i returns integer
    return i
endfunction

function ConvertLayerStyleFlag takes integer i returns integer
    return i
endfunction

function ConvertLayoutStyleFlag takes integer i returns integer
    return i
endfunction

function ConvertMappedField takes integer i returns integer
    return i
endfunction

function ConvertPathingAIType takes integer i returns integer
    return i
endfunction

function ConvertProjectileType takes integer i returns integer
    return i
endfunction

function ConvertRenderStage takes integer i returns integer
    return i
endfunction

function ConvertSpriteFlag takes integer i returns integer
    return i
endfunction

function ConvertTimeType takes integer i returns integer
    return i
endfunction

function ConvertTradeState takes integer i returns integer
    return i
endfunction

function ConvertVariableType takes integer i returns integer
    return i
endfunction

function CreateFrame takes string templateName, framehandle whichParent, integer priority, integer createContext returns framehandle
    return BlzCreateFrame(templateName, whichParent, priority, createContext)
endfunction

function CreateFrameByType takes string frameType, string contextName, framehandle whichParent, string templateName, integer createContext returns framehandle
    return BlzCreateFrameByType(frameType, contextName, whichParent, templateName, createContext)
endfunction

function CreateSimpleFrame takes string templateName, framehandle whichParent, integer createContext returns framehandle
    return BlzCreateSimpleFrame(templateName, whichParent, createContext)
endfunction

function DecPlayerTechResearched takes player whichPlayer, integer techid, integer levels returns nothing
    call BlzDecPlayerTechResearched(whichPlayer, techid, levels)
endfunction

function DestroyFrame takes framehandle whichFrame returns nothing
    call BlzDestroyFrame(whichFrame)
endfunction

function DisplayChatMessage takes player whichPlayer, integer recipient, string message returns nothing
    call BlzDisplayChatMessage(whichPlayer, recipient, message)
endfunction

function EnableTargetIndicator takes boolean enable returns nothing
    call BlzEnableTargetIndicator(enable)
endfunction

function ForceHasPlayer takes force whichForce, player whichPlayer returns boolean
    return BlzForceHasPlayer(whichForce, whichPlayer)
endfunction

function GetAbilityBooleanField takes ability whichAbility, abilitybooleanfield whichField returns boolean
    return BlzGetAbilityBooleanField(whichAbility, whichField)
endfunction

function GetAbilityBooleanLevelArrayField takes ability whichAbility, abilitybooleanlevelarrayfield whichField, integer level, integer index returns boolean
    return BlzGetAbilityBooleanLevelArrayField(whichAbility, whichField, level, index)
endfunction

function GetAbilityBooleanLevelField takes ability whichAbility, abilitybooleanlevelfield whichField, integer level returns boolean
    return BlzGetAbilityBooleanLevelField(whichAbility, whichField, level)
endfunction

function GetAbilityIntegerField takes ability whichAbility, abilityintegerfield whichField returns integer
    return BlzGetAbilityIntegerField(whichAbility, whichField)
endfunction

function GetAbilityIntegerLevelArrayField takes ability whichAbility, abilityintegerlevelarrayfield whichField, integer level, integer index returns integer
    return BlzGetAbilityIntegerLevelArrayField(whichAbility, whichField, level, index)
endfunction

function GetAbilityIntegerLevelField takes ability whichAbility, abilityintegerlevelfield whichField, integer level returns integer
    return BlzGetAbilityIntegerLevelField(whichAbility, whichField, level)
endfunction

function GetAbilityRealField takes ability whichAbility, abilityrealfield whichField returns real
    return BlzGetAbilityRealField(whichAbility, whichField)
endfunction

function GetAbilityRealLevelArrayField takes ability whichAbility, abilityreallevelarrayfield whichField, integer level, integer index returns real
    return BlzGetAbilityRealLevelArrayField(whichAbility, whichField, level, index)
endfunction

function GetAbilityRealLevelField takes ability whichAbility, abilityreallevelfield whichField, integer level returns real
    return BlzGetAbilityRealLevelField(whichAbility, whichField, level)
endfunction

function GetAbilityStringField takes ability whichAbility, abilitystringfield whichField returns string
    return BlzGetAbilityStringField(whichAbility, whichField)
endfunction

function GetAbilityStringLevelArrayField takes ability whichAbility, abilitystringlevelarrayfield whichField, integer level, integer index returns string
    return BlzGetAbilityStringLevelArrayField(whichAbility, whichField, level, index)
endfunction

function GetAbilityStringLevelField takes ability whichAbility, abilitystringlevelfield whichField, integer level returns string
    return BlzGetAbilityStringLevelField(whichAbility, whichField, level)
endfunction

function GetAbsorbingItem takes nothing returns item
    return BlzGetAbsorbingItem()
endfunction

function GetEventAttackType takes nothing returns attacktype
    return BlzGetEventAttackType()
endfunction

function GetEventDamageTarget takes nothing returns unit
    return BlzGetEventDamageTarget()
endfunction

function GetEventDamageType takes nothing returns damagetype
    return BlzGetEventDamageType()
endfunction

function GetEventIsAttack takes nothing returns boolean
    return BlzGetEventIsAttack()
endfunction

function GetEventWeaponType takes nothing returns weapontype
    return BlzGetEventWeaponType()
endfunction

function GetFrameAlpha takes framehandle whichFrame returns integer
    return BlzFrameGetAlpha(whichFrame)
endfunction

function GetFrameByName takes string frameName, integer createContext returns framehandle
    return BlzGetFrameByName(frameName, createContext)
endfunction

function GetFrameChild takes framehandle whichFrame, integer index returns framehandle
    return BlzFrameGetChild(whichFrame, index)
endfunction

function GetFrameChildrenCount takes framehandle whichFrame returns integer
    return BlzFrameGetChildrenCount(whichFrame)
endfunction

function GetFrameHeight takes framehandle whichFrame returns real
    return BlzFrameGetHeight(whichFrame)
endfunction

function GetFrameName takes framehandle whichFrame returns string
    return BlzFrameGetName(whichFrame)
endfunction

function GetFrameParent takes framehandle whichFrame returns framehandle
    return BlzFrameGetParent(whichFrame)
endfunction

function GetFrameText takes framehandle whichFrame returns string
    return BlzFrameGetText(whichFrame)
endfunction

function GetFrameTextSizeLimit takes framehandle whichFrame returns integer
    return BlzFrameGetTextSizeLimit(whichFrame)
endfunction

function GetFrameValue takes framehandle whichFrame returns real
    return BlzFrameGetValue(whichFrame)
endfunction

function GetFrameWidth takes framehandle whichFrame returns real
    return BlzFrameGetWidth(whichFrame)
endfunction

function GetItemAbilityByIndex takes item whichItem, integer index returns ability
    return BlzGetItemAbilityByIndex(whichItem, index)
endfunction

function GetItemBooleanField takes item whichItem, itembooleanfield whichField returns boolean
    return BlzGetItemBooleanField(whichItem, whichField)
endfunction

function GetItemIntegerField takes item whichItem, itemintegerfield whichField returns integer
    return BlzGetItemIntegerField(whichItem, whichField)
endfunction

function GetItemRealField takes item whichItem, itemrealfield whichField returns real
    return BlzGetItemRealField(whichItem, whichField)
endfunction

function GetItemStringField takes item whichItem, itemstringfield whichField returns string
    return BlzGetItemStringField(whichItem, whichField)
endfunction

function GetLocale takes nothing returns string
    return BlzGetLocale()
endfunction

function GetOriginFrame takes originframetype whichType, integer index returns framehandle
    return BlzGetOriginFrame(whichType, index)
endfunction

function GetSpecialEffectScale takes effect whichEffect returns real
    return BlzGetSpecialEffectScale(whichEffect)
endfunction

function GetStackingItemSource takes nothing returns item
    return BlzGetStackingItemSource()
endfunction

function GetStackingItemTarget takes nothing returns item
    return BlzGetStackingItemTarget()
endfunction

function GetStackingItemTargetPreviousCharges takes nothing returns integer
    return BlzGetStackingItemTargetPreviousCharges()
endfunction

function GetTriggerFrame takes nothing returns framehandle
    return BlzGetTriggerFrame()
endfunction

function GetTriggerFrameEvent takes nothing returns frameeventtype
    return BlzGetTriggerFrameEvent()
endfunction

function GetTriggerPlayerIsKeyDown takes nothing returns boolean
    return BlzGetTriggerPlayerIsKeyDown()
endfunction

function GetTriggerPlayerKey takes nothing returns oskeytype
    return BlzGetTriggerPlayerKey()
endfunction

function GetTriggerPlayerMetaKey takes nothing returns integer
    return BlzGetTriggerPlayerMetaKey()
endfunction

function GetTriggerPlayerMouseButton takes nothing returns mousebuttontype
    return BlzGetTriggerPlayerMouseButton()
endfunction

function GetTriggerSyncData takes nothing returns string
    return BlzGetTriggerSyncData()
endfunction

function GetTriggerSyncPrefix takes nothing returns string
    return BlzGetTriggerSyncPrefix()
endfunction

function GetUnitAbility takes unit whichUnit, integer abilityTypeId returns ability
    return BlzGetUnitAbility(whichUnit, abilityTypeId)
endfunction

function GetUnitAbilityByIndex takes unit whichUnit, integer index returns ability
    return BlzGetUnitAbilityByIndex(whichUnit, index)
endfunction

function GetUnitBooleanField takes unit whichUnit, unitbooleanfield whichField returns boolean
    return BlzGetUnitBooleanField(whichUnit, whichField)
endfunction

function GetUnitIntegerField takes unit whichUnit, unitintegerfield whichField returns integer
    return BlzGetUnitIntegerField(whichUnit, whichField)
endfunction

function GetUnitOrderCount takes unit whichUnit returns integer
    return BlzGetUnitOrderCount(whichUnit)
endfunction

function GetUnitRealField takes unit whichUnit, unitrealfield whichField returns real
    return BlzGetUnitRealField(whichUnit, whichField)
endfunction

function GetUnitStringField takes unit whichUnit, unitstringfield whichField returns string
    return BlzGetUnitStringField(whichUnit, whichField)
endfunction

function GetUnitWeaponBooleanField takes unit whichUnit, unitweaponbooleanfield whichField, integer index returns boolean
    return BlzGetUnitWeaponBooleanField(whichUnit, whichField, index)
endfunction

function GetUnitWeaponIntegerField takes unit whichUnit, unitweaponintegerfield whichField, integer index returns integer
    return BlzGetUnitWeaponIntegerField(whichUnit, whichField, index)
endfunction

function GetUnitWeaponRealField takes unit whichUnit, unitweaponrealfield whichField, integer index returns real
    return BlzGetUnitWeaponRealField(whichUnit, whichField, index)
endfunction

function GetUnitWeaponStringField takes unit whichUnit, unitweaponstringfield whichField, integer index returns string
    return BlzGetUnitWeaponStringField(whichUnit, whichField, index)
endfunction

function GetUnitZ takes unit whichUnit returns real
    return BlzGetUnitZ(whichUnit)
endfunction

function HideOriginFrames takes boolean flag returns nothing
    call BlzHideOriginFrames(flag)
endfunction

function IsFrameVisible takes framehandle whichFrame returns boolean
    return BlzFrameIsVisible(whichFrame)
endfunction

function IsKeyPressed takes oskeytype whichKey returns boolean
    return BlzIsKeyPressed(whichKey)
endfunction

function IsSelectionCircleEnabled takes nothing returns boolean
    return BlzIsSelectionCircleEnabled()
endfunction

function IsSelectionEnabled takes nothing returns boolean
    return BlzIsSelectionEnabled()
endfunction

function IsTargetIndicatorEnabled takes nothing returns boolean
    return BlzIsTargetIndicatorEnabled()
endfunction

function IsUnitInvulnerable takes unit whichUnit returns boolean
    return BlzIsUnitInvulnerable(whichUnit)
endfunction

function IsUnitSelectable takes unit whichUnit returns boolean
    return BlzIsUnitSelectable(whichUnit)
endfunction

function LoadTOCFile takes string TOCFile returns boolean
    return BlzLoadTOCFile(TOCFile)
endfunction

function PauseUnitEx takes unit whichUnit, boolean pause returns nothing
    call BlzPauseUnitEx(whichUnit, pause)
endfunction

function QueueBuildOrderById takes unit whichPeon, integer unitTypeId, real x, real y returns boolean
    return BlzQueueBuildOrderById(whichPeon, unitTypeId, x, y)
endfunction

function QueueImmediateOrderById takes unit whichUnit, integer orderId returns boolean
    return BlzQueueImmediateOrderById(whichUnit, orderId)
endfunction

function QueueInstantPointOrderById takes unit whichUnit, integer orderId, real x, real y, widget instantTargetWidget returns boolean
    return BlzQueueInstantPointOrderById(whichUnit, orderId, x, y, instantTargetWidget)
endfunction

function QueueInstantTargetOrderById takes unit whichUnit, integer orderId, widget targetWidget, widget instantTargetWidget returns boolean
    return BlzQueueInstantTargetOrderById(whichUnit, orderId, targetWidget, instantTargetWidget)
endfunction

function QueueNeutralImmediateOrderById takes player whichPlayer, unit neutralStructure, integer unitTypeId returns boolean
    return BlzQueueNeutralImmediateOrderById(whichPlayer, neutralStructure, unitTypeId)
endfunction

function QueueNeutralPointOrderById takes player whichPlayer, unit neutralStructure, integer unitTypeId, real x, real y returns boolean
    return BlzQueueNeutralPointOrderById(whichPlayer, neutralStructure, unitTypeId, x, y)
endfunction

function QueueNeutralTargetOrderById takes player whichPlayer, unit neutralStructure, integer unitTypeId, widget target returns boolean
    return BlzQueueNeutralTargetOrderById(whichPlayer, neutralStructure, unitTypeId, target)
endfunction

function QueuePointOrderById takes unit whichUnit, integer orderId, real x, real y returns boolean
    return BlzQueuePointOrderById(whichUnit, orderId, x, y)
endfunction

function QueueSpecialEffectAnimation takes effect whichEffect, string animationName returns nothing
    call BlzQueueSpecialEffectAnimation(whichEffect, animationName)
endfunction

function QueueTargetOrderById takes unit whichUnit, integer orderId, widget targetWidget returns boolean
    return BlzQueueTargetOrderById(whichUnit, orderId, targetWidget)
endfunction

function RemoveAbilityBooleanLevelArrayField takes ability whichAbility, abilitybooleanlevelarrayfield whichField, integer level, boolean value returns boolean
    return BlzRemoveAbilityBooleanLevelArrayField(whichAbility, whichField, level, value)
endfunction

function RemoveAbilityIntegerLevelArrayField takes ability whichAbility, abilityintegerlevelarrayfield whichField, integer level, integer value returns boolean
    return BlzRemoveAbilityIntegerLevelArrayField(whichAbility, whichField, level, value)
endfunction

function RemoveAbilityRealLevelArrayField takes ability whichAbility, abilityreallevelarrayfield whichField, integer level, real value returns boolean
    return BlzRemoveAbilityRealLevelArrayField(whichAbility, whichField, level, value)
endfunction

function RemoveAbilityStringLevelArrayField takes ability whichAbility, abilitystringlevelarrayfield whichField, integer level, string value returns boolean
    return BlzRemoveAbilityStringLevelArrayField(whichAbility, whichField, level, value)
endfunction

function ResetSpecialEffectMatrix takes effect whichEffect returns nothing
    call BlzResetSpecialEffectMatrix(whichEffect)
endfunction

function SendSyncData takes string prefix, string data returns boolean
    return BlzSendSyncData(prefix, data)
endfunction

function SetAbilityBooleanField takes ability whichAbility, abilitybooleanfield whichField, boolean value returns boolean
    return BlzSetAbilityBooleanField(whichAbility, whichField, value)
endfunction

function SetAbilityBooleanLevelArrayField takes ability whichAbility, abilitybooleanlevelarrayfield whichField, integer level, integer index, boolean value returns boolean
    return BlzSetAbilityBooleanLevelArrayField(whichAbility, whichField, level, index, value)
endfunction

function SetAbilityBooleanLevelField takes ability whichAbility, abilitybooleanlevelfield whichField, integer level, boolean value returns boolean
    return BlzSetAbilityBooleanLevelField(whichAbility, whichField, level, value)
endfunction

function SetAbilityIntegerField takes ability whichAbility, abilityintegerfield whichField, integer value returns boolean
    return BlzSetAbilityIntegerField(whichAbility, whichField, value)
endfunction

function SetAbilityIntegerLevelArrayField takes ability whichAbility, abilityintegerlevelarrayfield whichField, integer level, integer index, integer value returns boolean
    return BlzSetAbilityIntegerLevelArrayField(whichAbility, whichField, level, index, value)
endfunction

function SetAbilityIntegerLevelField takes ability whichAbility, abilityintegerlevelfield whichField, integer level, integer value returns boolean
    return BlzSetAbilityIntegerLevelField(whichAbility, whichField, level, value)
endfunction

function SetAbilityRealField takes ability whichAbility, abilityrealfield whichField, real value returns boolean
    return BlzSetAbilityRealField(whichAbility, whichField, value)
endfunction

function SetAbilityRealLevelArrayField takes ability whichAbility, abilityreallevelarrayfield whichField, integer level, integer index, real value returns boolean
    return BlzSetAbilityRealLevelArrayField(whichAbility, whichField, level, index, value)
endfunction

function SetAbilityRealLevelField takes ability whichAbility, abilityreallevelfield whichField, integer level, real value returns boolean
    return BlzSetAbilityRealLevelField(whichAbility, whichField, level, value)
endfunction

function SetAbilityStringField takes ability whichAbility, abilitystringfield whichField, string value returns boolean
    return BlzSetAbilityStringField(whichAbility, whichField, value)
endfunction

function SetAbilityStringLevelArrayField takes ability whichAbility, abilitystringlevelarrayfield whichField, integer level, integer index, string value returns boolean
    return BlzSetAbilityStringLevelArrayField(whichAbility, whichField, level, index, value)
endfunction

function SetAbilityStringLevelField takes ability whichAbility, abilitystringlevelfield whichField, integer level, string value returns boolean
    return BlzSetAbilityStringLevelField(whichAbility, whichField, level, value)
endfunction

function SetDestructableVertexColour takes destructable whichDestructable, integer red, integer green, integer blue, integer alpha returns nothing
    call SetDestructableVertexColor(whichDestructable, red, green, blue, alpha)
endfunction

function SetEventAttackType takes attacktype attackType returns boolean
    return BlzSetEventAttackType(attackType)
endfunction

function SetEventDamage takes real damage returns nothing
    call BlzSetEventDamage(damage)
endfunction

function SetEventDamageType takes damagetype whichDamageType returns boolean
    return BlzSetEventDamageType(whichDamageType)
endfunction

function SetEventWeaponType takes weapontype weaponType returns boolean
    return BlzSetEventWeaponType(weaponType)
endfunction

function SetFrameAlpha takes framehandle whichFrame, integer alpha returns nothing
    call BlzFrameSetAlpha(whichFrame, alpha)
endfunction

function SetFrameFont takes framehandle whichFrame, string fontName, real size, integer flags returns nothing
    call BlzFrameSetFont(whichFrame, fontName, size, flags)
endfunction

function SetFrameModel takes framehandle whichFrame, string model, integer cameraIndex returns nothing
    call BlzFrameSetModel(whichFrame, model, cameraIndex)
endfunction

function SetFrameParent takes framehandle whichFrame, framehandle whichParent returns nothing
    call BlzFrameSetParent(whichFrame, whichParent)
endfunction

function SetFrameScale takes framehandle whichFrame, real scale returns nothing
    call BlzFrameSetScale(whichFrame, scale)
endfunction

function SetFrameSize takes framehandle whichFrame, real width, real height returns nothing
    call BlzFrameSetSize(whichFrame, width, height)
endfunction

function SetFrameStepSize takes framehandle whichFrame, real stepSize returns nothing
    call BlzFrameSetStepSize(whichFrame, stepSize)
endfunction

function SetFrameText takes framehandle whichFrame, string text returns nothing
    call BlzFrameSetText(whichFrame, text)
endfunction

function SetFrameTextAlignment takes framehandle whichFrame, textaligntype verticalAlign, textaligntype horizontalAlign returns nothing
    call BlzFrameSetTextAlignment(whichFrame, verticalAlign, horizontalAlign)
endfunction

function SetFrameTextColour takes framehandle whichFrame, integer colour returns nothing
    call BlzFrameSetTextColor(whichFrame, colour)
endfunction

function SetFrameTextSizeLimit takes framehandle whichFrame, integer textSize returns nothing
    call BlzFrameSetTextSizeLimit(whichFrame, textSize)
endfunction

function SetFrameTexture takes framehandle whichFrame, string textureFile, integer textureId, boolean blend returns nothing
    call BlzFrameSetTexture(whichFrame, textureFile, textureId, blend)
endfunction

function SetFrameTooltip takes framehandle whichFrame, framehandle tooltipFrame returns nothing
    call BlzFrameSetTooltip(whichFrame, tooltipFrame)
endfunction

function SetFrameValue takes framehandle whichFrame, real value returns nothing
    call BlzFrameSetValue(whichFrame, value)
endfunction

function SetItemBooleanField takes item whichItem, itembooleanfield whichField, boolean value returns boolean
    return BlzSetItemBooleanField(whichItem, whichField, value)
endfunction

function SetItemIntegerField takes item whichItem, itemintegerfield whichField, integer value returns boolean
    return BlzSetItemIntegerField(whichItem, whichField, value)
endfunction

function SetItemRealField takes item whichItem, itemrealfield whichField, real value returns boolean
    return BlzSetItemRealField(whichItem, whichField, value)
endfunction

function SetItemStringField takes item whichItem, itemstringfield whichField, string value returns boolean
    return BlzSetItemStringField(whichItem, whichField, value)
endfunction

function SetSpecialEffectAlpha takes effect whichEffect, integer alpha returns nothing
    call BlzSetSpecialEffectAlpha(whichEffect, alpha)
endfunction

function SetSpecialEffectAnimation takes effect whichEffect, string animationName returns nothing
    call BlzSetSpecialEffectAnimation(whichEffect, animationName)
endfunction

function SetSpecialEffectHeight takes effect whichEffect, real height returns nothing
    call BlzSetSpecialEffectHeight(whichEffect, height)
endfunction

function SetSpecialEffectMatrixScale takes effect whichEffect, real x, real y, real z returns nothing
    call BlzSetSpecialEffectMatrixScale(whichEffect, x, y, z)
endfunction

function SetSpecialEffectOrientation takes effect whichEffect, real yaw, real pitch, real roll returns nothing
    call BlzSetSpecialEffectOrientation(whichEffect, yaw, pitch, roll)
endfunction

function SetSpecialEffectPitch takes effect whichEffect, real pitch returns nothing
    call BlzSetSpecialEffectPitch(whichEffect, pitch)
endfunction

function SetSpecialEffectPositionLoc takes effect whichEffect, location loc returns nothing
    call BlzSetSpecialEffectPositionLoc(whichEffect, loc)
endfunction

function SetSpecialEffectRoll takes effect whichEffect, real roll returns nothing
    call BlzSetSpecialEffectRoll(whichEffect, roll)
endfunction

function SetSpecialEffectScale takes effect whichEffect, real scale returns nothing
    call BlzSetSpecialEffectScale(whichEffect, scale)
endfunction

function SetSpecialEffectTimeScale takes effect whichEffect, real timescale returns nothing
    call BlzSetSpecialEffectTimeScale(whichEffect, timescale)
endfunction

function SetSpecialEffectX takes effect whichEffect, real x returns nothing
    call BlzSetSpecialEffectX(whichEffect, x)
endfunction

function SetSpecialEffectY takes effect whichEffect, real y returns nothing
    call BlzSetSpecialEffectY(whichEffect, y)
endfunction

function SetSpecialEffectYaw takes effect whichEffect, real yaw returns nothing
    call BlzSetSpecialEffectYaw(whichEffect, yaw)
endfunction

function SetSpecialEffectZ takes effect whichEffect, real z returns nothing
    call BlzSetSpecialEffectZ(whichEffect, z)
endfunction

function SetUnitBooleanField takes unit whichUnit, unitbooleanfield whichField, boolean value returns boolean
    return BlzSetUnitBooleanField(whichUnit, whichField, value)
endfunction

function SetUnitIntegerField takes unit whichUnit, unitintegerfield whichField, integer value returns boolean
    return BlzSetUnitIntegerField(whichUnit, whichField, value)
endfunction

function SetUnitRealField takes unit whichUnit, unitrealfield whichField, real value returns boolean
    return BlzSetUnitRealField(whichUnit, whichField, value)
endfunction

function SetUnitStringField takes unit whichUnit, unitstringfield whichField, string value returns boolean
    return BlzSetUnitStringField(whichUnit, whichField, value)
endfunction

function SetUnitWeaponBooleanField takes unit whichUnit, unitweaponbooleanfield whichField, integer index, boolean value returns boolean
    return BlzSetUnitWeaponBooleanField(whichUnit, whichField, index, value)
endfunction

function SetUnitWeaponIntegerField takes unit whichUnit, unitweaponintegerfield whichField, integer index, integer value returns boolean
    return BlzSetUnitWeaponIntegerField(whichUnit, whichField, index, value)
endfunction

function SetUnitWeaponRealField takes unit whichUnit, unitweaponrealfield whichField, integer index, real value returns boolean
    return BlzSetUnitWeaponRealField(whichUnit, whichField, index, value)
endfunction

function SetUnitWeaponStringField takes unit whichUnit, unitweaponstringfield whichField, integer index, string value returns boolean
    return BlzSetUnitWeaponStringField(whichUnit, whichField, index, value)
endfunction

function TriggerRegisterFrameEvent takes trigger whichTrigger, framehandle whichFrame, frameeventtype eventId returns event
    return BlzTriggerRegisterFrameEvent(whichTrigger, whichFrame, eventId)
endfunction

function TriggerRegisterPlayerKeyEvent takes trigger whichTrigger, player whichPlayer, oskeytype whichKey, integer whichMetaKey, boolean isKeyDown returns event
    return BlzTriggerRegisterPlayerKeyEvent(whichTrigger, whichPlayer, whichKey, whichMetaKey, isKeyDown)
endfunction

function TriggerRegisterPlayerSyncEvent takes trigger whichTrigger, player whichPlayer, string prefix, boolean fromServer returns event
    return BlzTriggerRegisterPlayerSyncEvent(whichTrigger, whichPlayer, prefix, fromServer)
endfunction

function UnitCancelTimedLife takes unit whichUnit returns nothing
    call BlzUnitCancelTimedLife(whichUnit)
endfunction

function UnitClearOrders takes unit whichUnit, boolean onlyQueued returns nothing
    call BlzUnitClearOrders(whichUnit, onlyQueued)
endfunction

function UnitForceStopOrder takes unit whichUnit, boolean clearQueue returns nothing
    call BlzUnitForceStopOrder(whichUnit, clearQueue)
endfunction
