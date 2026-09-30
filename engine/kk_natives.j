// Signatures of the natives of the KK platform, read by the script decompiler.
native DzGetMouseTerrainX takes nothing returns real
native DzGetMouseTerrainY takes nothing returns real
native DzGetMouseTerrainZ takes nothing returns real
native DzIsMouseOverUI takes nothing returns boolean
native DzGetMouseX takes nothing returns integer
native DzGetMouseY takes nothing returns integer
native DzGetMouseXRelative takes nothing returns integer
native DzGetMouseYRelative takes nothing returns integer
native DzSetMousePos takes integer x, integer y returns nothing
native DzTriggerRegisterMouseEvent takes trigger trig, integer btn, integer status, boolean sync, string xfunc returns nothing
native DzTriggerRegisterMouseEventByCode takes trigger trig, integer btn, integer status, boolean sync, code xfuncHandle returns nothing
native DzTriggerRegisterKeyEvent takes trigger trig, integer key, integer status, boolean sync, string xfunc returns nothing
native DzTriggerRegisterKeyEventByCode takes trigger trig, integer key, integer status, boolean sync, code xfuncHandle returns nothing
native DzTriggerRegisterMouseWheelEvent takes trigger trig, boolean sync, string xfunc returns nothing
native DzTriggerRegisterMouseWheelEventByCode takes trigger trig, boolean sync, code xfuncHandle returns nothing
native DzTriggerRegisterMouseMoveEvent takes trigger trig, boolean sync, string xfunc returns nothing
native DzTriggerRegisterMouseMoveEventByCode takes trigger trig, boolean sync, code xfuncHandle returns nothing
native DzGetTriggerKey takes nothing returns integer
native DzGetWheelDelta takes nothing returns integer
native DzIsKeyDown takes integer iKey returns boolean
native DzGetTriggerKeyPlayer takes nothing returns player
native DzGetWindowWidth takes nothing returns integer
native DzGetWindowHeight takes nothing returns integer
native DzGetWindowX takes nothing returns integer
native DzGetWindowY takes nothing returns integer
native DzTriggerRegisterWindowResizeEvent takes trigger trig, boolean sync, string xfunc returns nothing
native DzTriggerRegisterWindowResizeEventByCode takes trigger trig, boolean sync, code xfuncHandle returns nothing
native DzIsWindowActive takes nothing returns boolean
native DzDestructablePosition takes destructable d, real x, real y returns nothing
native DzSetUnitPosition takes unit whichUnit, real x, real y returns nothing
native DzExecuteFunc takes string xfuncName returns nothing
native DzGetUnitUnderMouse takes nothing returns unit
native DzSetUnitTexture takes unit whichUnit, string path, integer texId returns nothing
native DzSetMemory takes integer address, real value returns nothing
native DzSetUnitID takes unit whichUnit, integer id returns nothing
native DzSetUnitModel takes unit whichUnit, string path returns nothing
native DzSetWar3MapMap takes string map returns nothing
native DzGetLocale takes nothing returns string
native DzGetUnitNeededXP takes unit whichUnit, integer level returns integer
native DzTriggerRegisterSyncData takes trigger trig, string prefix, boolean server returns nothing
native DzSyncData takes string prefix, string data returns nothing
native DzGetTriggerSyncPrefix takes nothing returns string
native DzGetTriggerSyncData takes nothing returns string
native DzGetTriggerSyncPlayer takes nothing returns player
native DzSyncBuffer takes string prefix, string data, integer dataLen returns nothing
native DzSyncDataImmediately takes string prefix, string data returns nothing
native DzFrameHideInterface takes nothing returns nothing
native DzFrameEditBlackBorders takes real upperHeight, real bottomHeight returns nothing
native DzFrameGetPortrait takes nothing returns integer
native DzFrameGetMinimap takes nothing returns integer
native DzFrameGetCommandBarButton takes integer row, integer column returns integer
native DzFrameGetHeroBarButton takes integer buttonId returns integer
native DzFrameGetHeroHPBar takes integer buttonId returns integer
native DzFrameGetHeroManaBar takes integer buttonId returns integer
native DzFrameGetItemBarButton takes integer buttonId returns integer
native DzFrameGetMinimapButton takes integer buttonId returns integer
native DzFrameGetUpperButtonBarButton takes integer buttonId returns integer
native DzFrameGetTooltip takes nothing returns integer
native DzFrameGetChatMessage takes nothing returns integer
native DzFrameGetUnitMessage takes nothing returns integer
native DzFrameGetTopMessage takes nothing returns integer
native DzGetColor takes integer r, integer g, integer b, integer a returns integer
native DzFrameSetUpdateCallback takes string xfunc returns nothing
native DzFrameSetUpdateCallbackByCode takes code xfuncHandle returns nothing
native DzFrameShow takes integer frame, boolean enable returns nothing
native DzCreateFrame takes string frame, integer parent, integer id returns integer
native DzCreateSimpleFrame takes string frame, integer parent, integer id returns integer
native DzDestroyFrame takes integer frame returns nothing
native DzLoadToc takes string fileName returns nothing
native DzFrameSetPoint takes integer frame, integer point, integer relativeFrame, integer relativePoint, real x, real y returns nothing
native DzFrameSetAbsolutePoint takes integer frame, integer point, real x, real y returns nothing
native DzFrameClearAllPoints takes integer frame returns nothing
native DzFrameSetEnable takes integer name, boolean enable returns nothing
native DzFrameSetScript takes integer frame, integer eventId, string xfunc, boolean sync returns nothing
native DzFrameSetScriptByCode takes integer frame, integer eventId, code xfuncHandle, boolean sync returns nothing
native DzGetTriggerUIEventPlayer takes nothing returns player
native DzGetTriggerUIEventFrame takes nothing returns integer
native DzFrameFindByName takes string name, integer id returns integer
native DzSimpleFrameFindByName takes string name, integer id returns integer
native DzSimpleFontStringFindByName takes string name, integer id returns integer
native DzSimpleTextureFindByName takes string name, integer id returns integer
native DzGetGameUI takes nothing returns integer
native DzClickFrame takes integer frame returns nothing
native DzSetCustomFovFix takes real value returns nothing
native DzEnableWideScreen takes boolean enable returns nothing
native DzFrameSetText takes integer frame, string text returns nothing
native DzFrameGetText takes integer frame returns string
native DzFrameSetTextSizeLimit takes integer frame, integer size returns nothing
native DzFrameGetTextSizeLimit takes integer frame returns integer
native DzFrameSetTextColor takes integer frame, integer color returns nothing
native DzGetMouseFocus takes nothing returns integer
native DzFrameSetAllPoints takes integer frame, integer relativeFrame returns boolean
native DzFrameSetFocus takes integer frame, boolean enable returns boolean
native DzFrameSetModel takes integer frame, string modelFile, integer modelType, integer flag returns nothing
native DzFrameGetEnable takes integer frame returns boolean
native DzFrameSetAlpha takes integer frame, integer alpha returns nothing
native DzFrameGetAlpha takes integer frame returns integer
native DzFrameSetAnimate takes integer frame, integer animId, boolean autocast returns nothing
native DzFrameSetAnimateOffset takes integer frame, real offset returns nothing
native DzFrameSetTexture takes integer frame, string texture, integer flag returns nothing
native DzFrameSetScale takes integer frame, real scale returns nothing
native DzFrameSetTooltip takes integer frame, integer tooltip returns nothing
native DzFrameCageMouse takes integer frame, boolean enable returns nothing
native DzFrameGetValue takes integer frame returns real
native DzFrameSetMinMaxValue takes integer frame, real minValue, real maxValue returns nothing
native DzFrameSetStepValue takes integer frame, real step returns nothing
native DzFrameSetValue takes integer frame, real value returns nothing
native DzFrameSetSize takes integer frame, real w, real h returns nothing
native DzCreateFrameByTagName takes string frameType, string name, integer parent, string template, integer id returns integer
native DzFrameSetVertexColor takes integer frame, integer color returns nothing
native DzOriginalUIAutoResetPoint takes boolean enable returns nothing
native DzFrameSetPriority takes integer frame, integer priority returns nothing
native DzFrameSetParent takes integer frame, integer parent returns nothing
native DzFrameGetHeight takes integer frame returns real
native DzFrameSetFont takes integer frame, string fileName, real height, integer flag returns nothing
native DzFrameGetParent takes integer frame returns integer
native DzFrameSetTextAlignment takes integer frame, integer align returns nothing
native DzFrameGetName takes integer frame returns string
native DzGetClientWidth takes nothing returns integer
native DzGetClientHeight takes nothing returns integer
native DzFrameIsVisible takes integer frame returns boolean
native DzFrameAddText takes integer frame, string text returns nothing
native DzUnitSilence takes unit whichUnit, boolean disable returns nothing
native DzUnitDisableAttack takes unit whichUnit, boolean disable returns nothing
native DzUnitDisableInventory takes unit whichUnit, boolean disable returns nothing
native DzUpdateMinimap takes nothing returns nothing
native DzUnitChangeAlpha takes unit whichUnit, integer alpha, boolean forceUpdate returns nothing
native DzUnitSetCanSelect takes unit whichUnit, boolean state returns nothing
native DzUnitSetTargetable takes unit whichUnit, boolean state returns nothing
native DzSaveMemoryCache takes string cache returns nothing
native DzGetMemoryCache takes nothing returns string
native DzSetSpeed takes real ratio returns nothing
native DzConvertWorldPosition takes real x, real y, real z, code callback returns boolean
native DzGetConvertWorldPositionX takes nothing returns real
native DzGetConvertWorldPositionY takes nothing returns real
native DzCreateCommandButton takes integer parent, string icon, string name, string desc returns integer
native DzAPI_Map_HasMallItem takes player whichPlayer, string key returns boolean
native DzAPI_Map_GetMapLevel takes player whichPlayer returns integer
native RequestExtraIntegerData takes integer dataType, player whichPlayer, string param1, string param2, boolean param3, integer param4, integer param5, integer param6 returns integer
native RequestExtraBooleanData takes integer dataType, player whichPlayer, string param1, string param2, boolean param3, integer param4, integer param5, integer param6 returns boolean
native RequestExtraStringData takes integer dataType, player whichPlayer, string param1, string param2, boolean param3, integer param4, integer param5, integer param6 returns string
native RequestExtraRealData takes integer dataType, player whichPlayer, string param1, string param2, boolean param3, integer param4, integer param5, integer param6 returns real
native UnitAlive takes unit id returns boolean
native DzGetSelectedLeaderUnit takes nothing returns unit
native DzIsChatBoxOpen takes nothing returns boolean
native DzSetUnitPreselectUIVisible takes unit whichUnit, boolean visible returns nothing
native DzSetEffectAnimation takes effect whichEffect, integer index, integer flag returns nothing
native DzSetEffectPos takes effect whichEffect, real x, real y, real z returns nothing
native DzSetEffectVertexColor takes effect whichEffect, integer color returns nothing
native DzSetEffectVertexAlpha takes effect whichEffect, integer alpha returns nothing
native DzSetEffectModel takes effect whichEffect, string model returns nothing
native DzSetEffectTeamColor takes effect whichHandle, integer playerId returns nothing
native DzFrameSetClip takes integer whichframe, boolean enable returns nothing
native DzChangeWindowSize takes integer width, integer height returns boolean
native DzPlayEffectAnimation takes effect whichEffect, string anim, string link returns nothing
native DzBindEffect takes widget parent, string attachPoint, effect whichEffect returns nothing
native DzUnbindEffect takes effect whichEffect returns nothing
native DzSetWidgetSpriteScale takes widget whichUnit, real scale returns nothing
native DzSetEffectScale takes effect whichHandle, real scale returns nothing
native DzGetEffectVertexColor takes effect whichEffect returns integer
native DzGetEffectVertexAlpha takes effect whichEffect returns integer
native DzGetItemAbility takes item whichEffect, integer index returns ability
native DzFrameGetChildrenCount takes integer whichframe returns integer
native DzFrameGetChild takes integer whichframe, integer index returns integer
native DzUnlockBlpSizeLimit takes boolean enable returns nothing
native DzGetActivePatron takes unit store, player p returns unit
native DzGetLocalSelectUnitCount takes nothing returns integer
native DzGetLocalSelectUnit takes integer index returns unit
native DzGetJassStringTableCount takes nothing returns integer
native DzModelRemoveFromCache takes string path returns nothing
native DzModelRemoveAllFromCache takes nothing returns nothing
native DzFrameGetInfoPanelSelectButton takes integer index returns integer
native DzFrameGetInfoPanelBuffButton takes integer index returns integer
native DzFrameGetPeonBar takes nothing returns integer
native DzFrameGetCommandBarButtonNumberText takes integer whichframe returns integer
native DzFrameGetCommandBarButtonNumberOverlay takes integer whichframe returns integer
native DzFrameGetCommandBarButtonCooldownIndicator takes integer whichframe returns integer
native DzFrameGetCommandBarButtonAutoCastIndicator takes integer whichframe returns integer
native DzToggleFPS takes boolean show returns nothing
native DzGetFPS takes nothing returns integer
native DzFrameWorldToMinimapPosX takes real x, real y returns real
native DzFrameWorldToMinimapPosY takes real x, real y returns real
native DzWidgetSetMinimapIcon takes unit whichunit, string path returns nothing
native DzWidgetSetMinimapIconEnable takes unit whichunit, boolean enable returns nothing
native DzFrameGetWorldFrameMessage takes nothing returns integer
native DzSimpleMessageFrameAddMessage takes integer whichframe, string text, integer color, real duration, boolean permanent returns nothing
native DzSimpleMessageFrameClear takes integer whichframe returns nothing
native DzConvertScreenPositionX takes real x, real y returns real
native DzConvertScreenPositionY takes real x, real y returns real
native DzRegisterOnBuildLocal takes code xfunc returns nothing
native DzGetOnBuildOrderId takes nothing returns integer
native DzGetOnBuildOrderType takes nothing returns integer
native DzGetOnBuildAgent takes nothing returns widget
native DzRegisterOnTargetLocal takes code xfunc returns nothing
native DzGetOnTargetAbilId takes nothing returns integer
native DzGetOnTargetOrderId takes nothing returns integer
native DzGetOnTargetOrderType takes nothing returns integer
native DzGetOnTargetAgent takes nothing returns widget
native DzGetOnTargetInstantTarget takes nothing returns widget
native DzOpenQQGroupUrl takes string url returns boolean
native DzFrameEnableClipRect takes boolean enable returns nothing
native DzSetUnitName takes unit whichUnit, string name returns nothing
native DzSetUnitPortrait takes unit whichUnit, string modelFile returns nothing
native DzSetUnitDescription takes unit whichUnit, string value returns nothing
native DzSetUnitMissileArc takes unit whichUnit, real arc returns nothing
native DzSetUnitMissileModel takes unit whichUnit, string modelFile returns nothing
native DzSetUnitProperName takes unit whichUnit, string name returns nothing
native DzSetUnitMissileHoming takes unit whichUnit, boolean enable returns nothing
native DzSetUnitMissileSpeed takes unit whichUnit, real speed returns nothing
native DzSetEffectVisible takes effect whichHandle, boolean enable returns nothing
native DzReviveUnit takes unit whichUnit, player whichPlayer, real hp, real mp, real x, real y returns nothing
native DzGetAttackAbility takes unit whichUnit returns ability
native DzAttackAbilityEndCooldown takes ability whichHandle returns nothing
native EXSetUnitArrayString takes integer uid, integer id, integer n, string name returns boolean
native EXSetUnitInteger takes integer uid, integer id, integer n returns boolean
native DzDoodadCreate takes integer id, integer var, real x, real y, real z, real rotate, real scale returns integer
native DzDoodadGetTypeId takes integer doodad returns integer
native DzDoodadSetModel takes integer doodad, string modelFile returns nothing
native DzDoodadSetTeamColor takes integer doodad, integer color returns nothing
native DzDoodadSetColor takes integer doodad, integer color returns nothing
native DzDoodadGetX takes integer doodad returns real
native DzDoodadGetY takes integer doodad returns real
native DzDoodadGetZ takes integer doodad returns real
native DzDoodadSetPosition takes integer doodad, real x, real y, real z returns nothing
native DzDoodadSetOrientMatrixRotate takes integer doodad, real angle, real axisX, real axisY, real axisZ returns nothing
native DzDoodadSetOrientMatrixScale takes integer doodad, real x, real y, real z returns nothing
native DzDoodadSetOrientMatrixResize takes integer doodad returns nothing
native DzDoodadSetVisible takes integer doodad, boolean enable returns nothing
native DzDoodadSetAnimation takes integer doodad, string animName, boolean animRandom returns nothing
native DzDoodadSetTimeScale takes integer doodad, real scale returns nothing
native DzDoodadGetTimeScale takes integer doodad returns real
native DzDoodadGetCurrentAnimationIndex takes integer doodad returns integer
native DzDoodadGetAnimationCount takes integer doodad returns integer
native DzDoodadGetAnimationName takes integer doodad, integer index returns string
native DzDoodadGetAnimationTime takes integer doodad, integer index returns integer
native DzUnitFindAbility takes unit whichUnit, integer abilcode returns ability
native DzAbilitySetStringData takes ability whichAbility, string key, string value returns nothing
native DzAbilitySetEnable takes ability whichAbility, boolean enable, boolean hideUI returns nothing
native DzUnitSetMoveType takes unit whichUnit, string moveType returns nothing
native DzFrameGetWidth takes integer frame returns real
native DzFrameSetAnimateByIndex takes integer frame, integer index, integer flag returns nothing
native DzSetUnitDataCacheInteger takes integer uid, integer id,integer index,integer v returns nothing
native DzUnitUIAddLevelArrayInteger takes integer uid, integer id,integer lv,integer v returns nothing
native EXGetUnitAbility takes unit u, integer abilcode returns ability
native EXGetUnitAbilityByIndex takes unit u, integer index returns ability
native EXGetAbilityId takes ability abil returns integer
native EXGetAbilityState takes ability abil, integer state_type returns real
native EXSetAbilityState takes ability abil, integer state_type, real value returns boolean
native EXGetAbilityDataReal takes ability abil, integer level, integer data_type returns real
native EXSetAbilityDataReal takes ability abil, integer level, integer data_type, real value returns boolean
native EXGetAbilityDataInteger takes ability abil, integer level, integer data_type returns integer
native EXSetAbilityDataInteger takes ability abil, integer level, integer data_type, integer value returns boolean
native EXGetAbilityDataString takes ability abil, integer level, integer data_type returns string
native EXSetAbilityDataString takes ability abil, integer level, integer data_type, string value returns boolean
native EXSetAbilityAEmeDataA takes ability abil, integer unitid returns boolean
native EXGetItemDataString takes integer itemcode, integer data_type returns string
native EXSetItemDataString takes integer itemcode, integer data_type, string value returns boolean
native EXGetEventDamageData takes integer edd_type returns integer
native EXSetEventDamage takes real amount returns boolean
native EXGetEffectX takes effect e returns real
native EXGetEffectY takes effect e returns real
native EXGetEffectZ takes effect e returns real
native EXSetEffectXY takes effect e, real x, real y returns nothing
native EXSetEffectZ takes effect e, real z returns nothing
native EXGetEffectSize takes effect e returns real
native EXSetEffectSize takes effect e, real size returns nothing
native EXEffectMatRotateX takes effect e, real angle returns nothing
native EXEffectMatRotateY takes effect e, real angle returns nothing
native EXEffectMatRotateZ takes effect e, real angle returns nothing
native EXEffectMatScale takes effect e, real x, real y, real z returns nothing
native EXEffectMatReset takes effect e returns nothing
native EXSetEffectSpeed takes effect e, real speed returns nothing
native EXSetUnitFacing takes unit u, real angle returns nothing
native EXPauseUnit takes unit u, boolean flag returns nothing
native EXSetUnitCollisionType takes boolean enable, unit u, integer t returns nothing
native EXSetUnitMoveType takes unit u, integer t returns nothing
native EXDisplayChat takes player p, integer chat_recipient, string message returns nothing
native EXExecuteScript takes string script returns string
native DzBitGet takes integer i, integer byteIndex returns integer
native DzBitSet takes integer i, integer byteIndex, integer byteValue returns integer
native DzBitGetByte takes integer i, integer byteIndex returns integer
native DzBitSetByte takes integer i, integer byteIndex, integer byteValue returns integer
native DzBitNot takes integer i returns integer
native DzBitAnd takes integer a, integer b returns integer
native DzBitOr takes integer a, integer b returns integer
native DzBitXor takes integer a, integer b returns integer
native DzBitShiftLeft takes integer i, integer bitsToShift returns integer
native DzBitShiftRight takes integer i, integer bitsToShift returns integer
native DzBitToInt takes integer b1, integer b2, integer b3, integer b4 returns integer
