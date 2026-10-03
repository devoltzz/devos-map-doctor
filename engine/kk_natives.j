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
native DzFrameSetScriptBlock takes integer frame, integer eventId, code funcHandle, boolean sync returns nothing
native DzFrameSetScriptAsync takes integer frame, integer eventId, string funcName returns nothing
native DzFrameSetScriptByCodeAsync takes integer frame, integer eventId, code func returns nothing
native DzFrameSetScriptBlockAsync takes integer frame, integer eventId, code func returns nothing
native DzSimpleFrameShow takes integer frame, boolean enable returns nothing
native DzUnlockOpCodeLimit takes boolean enable returns nothing
native DzSetClipboard takes string content returns boolean
native DzDoodadRemove takes integer doodad returns nothing
native DzRemovePlayerTechResearched takes player whichPlayer, integer techid, integer removelevels returns nothing
native DzItemSetModel takes item whichItem, string file returns nothing
native DzItemSetVertexColor takes item whichItem, integer color returns nothing
native DzItemSetAlpha takes item whichItem, integer color returns nothing
native DzItemSetPortrait takes item whichItem, string modelPath returns nothing
native DzFrameHookHpBar takes code func returns nothing
native DzFrameGetTriggerHpBarUnit takes nothing returns unit
native DzFrameGetTriggerHpBar takes nothing returns integer
native DzFrameGetUnitHpBar takes unit whichUnit returns integer
native DzGetCursorFrame takes nothing returns integer
native DzFrameGetPointValid takes integer frame, integer anchor returns boolean
native DzFrameGetPointRelative takes integer frame, integer anchor returns integer
native DzFrameGetPointRelativePoint takes integer frame, integer anchor returns integer
native DzFrameGetPointX takes integer frame, integer anchor returns real
native DzFrameGetPointY takes integer frame, integer anchor returns real
native DzWriteLog takes string msg returns nothing
native DzTextTagGetFont takes nothing returns string
native DzTextTagSetFont takes string fileName returns nothing
native DzTextTagSetStartAlpha takes texttag t, integer alpha returns nothing
native DzTextTagGetShadowColor takes texttag t returns integer
native DzTextTagSetShadowColor takes texttag t, integer color returns nothing
native DzGroupGetCount takes group g returns integer
native DzGroupGetUnitAt takes group g, integer index returns unit
native DzUnitCreateIllusion takes player p, integer unitId, real x, real y, real face returns unit
native DzUnitCreateIllusionFromUnit takes unit u returns unit
native DzStringContains takes string s, string whichString, boolean caseSensitive returns boolean
native DzStringFind takes string s, string whichString, integer off, boolean caseSensitive returns integer
native DzStringFindFirstOf takes string s, string whichString, integer off, boolean caseSensitive returns integer
native DzStringFindFirstNotOf takes string s, string whichString, integer off, boolean caseSensitive returns integer
native DzStringFindLastOf takes string s, string whichString, integer off, boolean caseSensitive returns integer
native DzStringFindLastNotOf takes string s, string whichString, integer off, boolean caseSensitive returns integer
native DzStringTrimLeft takes string s returns string
native DzStringTrimRight takes string s returns string
native DzStringTrim takes string s returns string
native DzStringReverse takes string s returns string
native DzStringReplace takes string s, string whichString, string replaceWith, boolean caseSensitive returns string
native DzStringInsert takes string s, integer whichPosition, string whichString returns string
native DzQueueGroupImmediateOrderById takes group whichGroup, integer order returns boolean
native DzQueueGroupPointOrderById takes group whichGroup, integer order, real x, real y returns boolean
native DzQueueGroupTargetOrderById takes group whichGroup, integer order, widget targetWidget returns boolean
native DzQueueIssueImmediateOrderById takes unit whichUnit, integer order returns boolean
native DzQueueIssuePointOrderById takes unit whichUnit, integer order, real x, real y returns boolean
native DzQueueIssueTargetOrderById takes unit whichUnit, integer order, widget targetWidget returns boolean
native DzQueueIssueInstantPointOrderById takes unit whichUnit, integer order, real x, real y, widget instantTargetWidget returns boolean
native DzQueueIssueInstantTargetOrderById takes unit whichUnit, integer order, widget targetWidget, widget instantTargetWidget returns boolean
native DzQueueIssueBuildOrderById takes unit whichPeon, integer unitId, real x, real y returns boolean
native DzQueueIssueNeutralImmediateOrderById takes player forWhichPlayer,unit neutralStructure, integer unitId returns boolean
native DzQueueIssueNeutralPointOrderById takes player forWhichPlayer,unit neutralStructure, integer unitId, real x, real y returns boolean
native DzQueueIssueNeutralTargetOrderById takes player forWhichPlayer,unit neutralStructure, integer unitId, widget target returns boolean
native DzUnitOrdersCount takes unit u returns integer
native DzUnitOrdersClear takes unit u, boolean onlyQueued returns nothing
native DzUnitOrdersExec takes unit u returns nothing
native DzUnitOrdersForceStop takes unit u, boolean clearQueue returns nothing
native DzUnitOrdersReverse takes unit u returns nothing
native DzXlsxOpen takes string filePath returns integer
native DzXlsxClose takes integer docHandle returns boolean
native DzXlsxWorksheetGetRowCount takes integer docHandle, string sheetName returns integer
native DzXlsxWorksheetGetColumnCount takes integer docHandle, string sheetName returns integer
native DzXlsxWorksheetGetCellType takes integer docHandle, string sheetName, integer row, integer column returns integer
native DzXlsxWorksheetGetCellString takes integer docHandle, string sheetName, integer row, integer column returns string
native DzXlsxWorksheetGetCellInteger takes integer docHandle, string sheetName, integer row, integer column returns integer
native DzXlsxWorksheetGetCellBoolean takes integer docHandle, string sheetName, integer row, integer column returns boolean
native DzXlsxWorksheetGetCellFloat takes integer docHandle, string sheetName, integer row, integer column returns real
native DzFrameSetTexCoord takes integer frame, real left, real top, real right, real bottom returns nothing
native DzSetUnitAbilityRange takes unit Unit, integer abil_code, real value returns boolean
native DzGetUnitAbilityRange takes unit Unit, integer abil_code returns real
native DzSetUnitAbilityArea takes unit Unit, integer abil_code, real value returns boolean
native DzGetUnitAbilityArea takes unit Unit, integer abil_code returns real
native DzSetUnitAbilityCool takes unit Unit, integer abil_code, real cool, real max_cool returns boolean
native DzGetUnitAbilityCool takes unit Unit, integer abil_code returns real
native DzGetUnitAbilityMaxCool takes unit Unit, integer abil_code returns real
native DzSetUnitAbilityDataA takes unit Unit, integer abil_code, real value returns boolean
native DzGetUnitAbilityDataA takes unit Unit, integer abil_code returns real
native DzSetUnitAbilityDataB takes unit Unit, integer abil_code, real value returns boolean
native DzGetUnitAbilityDataB takes unit Unit, integer abil_code returns real
native DzSetUnitAbilityDataC takes unit Unit, integer abil_code, real value returns boolean
native DzGetUnitAbilityDataC takes unit Unit, integer abil_code returns real
native DzSetUnitAbilityDataD takes unit Unit, integer abil_code, real value returns boolean
native DzGetUnitAbilityDataD takes unit Unit, integer abil_code returns real
native DzSetUnitAbilityDataE takes unit Unit, integer abil_code, real value returns boolean
native DzGetUnitAbilityDataE takes unit Unit, integer abil_code returns real
native DzSetUnitAbilityButtonPos takes unit Unit, integer abil_code, integer x, integer y returns boolean
native DzSetUnitAbilityHotkey takes unit Unit, integer abil_code, string key returns boolean
native DzConvertTargs2Str takes integer targs returns string
native DzConvertStr2Targs takes string targs returns integer
native DzSetUnitAbilityTargs takes unit Unit, integer abil_code, integer value returns boolean
native DzGetUnitAbilityTargs takes unit Unit, integer abil_code returns integer
native DzSetUnitAbilityCost takes unit Unit, integer abil_code, integer value returns boolean
native DzGetUnitAbilityCost takes unit Unit, integer abil_code returns integer
native DzSetUnitAbilityReqLevel takes unit Unit, integer abil_code, integer value returns boolean
native DzGetUnitAbilityReqLevel takes unit Unit, integer abil_code returns integer
native DzSetUnitAbilityUnitId takes unit Unit, integer abil_code, integer value returns boolean
native DzGetUnitAbilityUnitId takes unit Unit, integer abil_code returns integer
native DzSetUnitAbilityBuildOrderId takes unit Unit, integer abil_code, integer value returns boolean
native DzGetUnitAbilityBuildOrderId takes unit Unit, integer abil_code returns integer
native DzSetUnitAbilityBuildModel takes unit Unit, integer abil_code, string model_path, real model_scale returns boolean
native DzUnitHasAbility takes unit Unit, integer abil_code returns boolean
native KKCreateCommandButton takes nothing returns integer
native KKDestroyCommandButton takes integer btn returns nothing
native KKCommandButtonClick takes integer btn, integer mouse_type returns nothing
native KKCommandTargetClick takes integer mouse_type, widget target returns boolean
native KKCommandTerrainClick takes integer mouse_type, real x, real y, real z returns boolean
native KKSetCommandUnitAbility takes integer btn, unit Unit, integer abil_code returns nothing
native DzItemGetVertexColor takes item Item returns integer
native DzItemSetSize takes item Item, real size returns nothing
native DzItemGetSize takes item Item returns real
native DzItemMatRotateX takes item Item, real x returns nothing
native DzItemMatRotateY takes item Item, real y returns nothing
native DzItemMatRotateZ takes item Item, real z returns nothing
native DzItemMatScale takes item Item, real x, real y, real z returns nothing
native DzItemMatReset takes item Item returns nothing
native DzGetLastSelectedItem takes nothing returns item
native DzSetPariticle2Size takes agent Widget, real scale returns nothing
native DzSetUnitCollisionSize takes unit Unit, real size returns nothing
native DzGetUnitCollisionSize takes unit Unit returns real
native DzSetWidgetTexture takes agent Handle, string TexturePath, integer ReplaceId returns nothing
native DzSetUnitSelectScale takes unit Unit, real scale returns nothing
native DzSetUnitHitIgnore takes unit Unit, boolean ignore returns nothing
native DzEffectBindEffect takes agent Handle, string AttachName, effect eff returns nothing
native DzFrameSetIgnoreTrackEvents takes integer frame, boolean ignore returns nothing
native DzFrameAddModel takes integer parent_frame returns integer
native DzFrameSetModel2 takes integer model_frame, string model_file, integer team_color_id returns nothing
native DzFrameAddModelEffect takes integer model_frame, string attach_point, string model_file returns integer
native DzFrameRemoveModelEffect takes integer model_frame, integer effect_frame returns nothing
native DzFrameSetModelAnimationByIndex takes integer model_frame, integer anim_index returns nothing
native DzFrameSetModelAnimation takes integer model_frame, string animation returns nothing
native DzFrameSetModelCameraSource takes integer model_frame, real x, real y, real z returns nothing
native DzFrameSetModelCameraTarget takes integer model_frame, real x, real y, real z returns nothing
native DzFrameSetModelSize takes integer model_frame, real size returns nothing
native DzFrameGetModelSize takes integer model_frame returns real
native DzFrameSetModelPosition takes integer model_frame, real x, real y, real z returns nothing
native DzFrameSetModelX takes integer model_frame, real x returns nothing
native DzFrameGetModelX takes integer model_frame returns real
native DzFrameSetModelY takes integer model_frame, real y returns nothing
native DzFrameGetModelY takes integer model_frame returns real
native DzFrameSetModelZ takes integer model_frame, real z returns nothing
native DzFrameGetModelZ takes integer model_frame returns real
native DzFrameSetModelSpeed takes integer model_frame, real speed returns nothing
native DzFrameGetModelSpeed takes integer model_frame returns real
native DzFrameSetModelScale takes integer model_frame, real x, real y, real z returns nothing
native DzFrameSetModelMatReset takes integer model_frame returns nothing
native DzFrameSetModelRotateX takes integer model_frame, real x returns nothing
native DzFrameSetModelRotateY takes integer model_frame, real y returns nothing
native DzFrameSetModelRotateZ takes integer model_frame, real z returns nothing
native DzFrameSetModelColor takes integer model_frame, integer color returns nothing
native DzFrameGetModelColor takes integer model_frame returns integer
native DzFrameSetModelTexture takes integer model_frame, string texture_file, integer replace_texutre_id returns nothing
native DzFrameSetModelParticle2Size takes integer model_frame, real scale returns nothing
native DzGetGlueUI takes nothing returns integer
native DzFrameGetMouse takes nothing returns integer
native DzFrameGetContext takes integer frame returns integer
native DzFrameSetNameContext takes integer frame, string name, integer context returns nothing
native DzFrameSetTextFontSpacing takes integer text_frame, real spacing returns nothing
native KKCommandGetCooldownModel takes integer cmd_btn returns integer
native KKCommandSetCooldownModelSize takes integer cmd_btn, real size returns nothing
native KKCommandSetCooldownModelSize2 takes integer cmd_btn, real width, real height returns nothing
native DzGetPlayerLastSelectedItem takes player p returns item
native DzGetCacheModelCount takes nothing returns integer
native DzSetMaxFps takes integer max_fps returns nothing
native DzEnableDrawSkillPanel takes unit u, boolean is_enable returns nothing
native DzEnableDrawSkillPanelByPlayer takes player p, boolean is_enable returns nothing
native DzSetEffectFogVisible takes effect eff, boolean is_visible returns nothing
native DzSetEffectMaskVisible takes effect eff, boolean is_visible returns nothing
native DzFrameBindWidget takes integer frame, widget u, real world_x, real world_y, real world_z, real screen_x, real screen_y, boolean fog_visible, boolean unit_visible, boolean dead_visible returns nothing
native DzFrameBindWorldPos takes integer frame, real world_x, real world_y, real world_z, real screen_x, real screen_y, boolean fog_visible returns nothing
native DzFrameUnBind takes integer frame returns nothing
native DzDisableUnitPreselectUi takes nothing returns nothing
native DzDisableItemPreselectUi takes nothing returns nothing
native DzFrameGetLowerLevelFrame takes nothing returns integer
native DzFrameSetCheckBoxState takes integer check_box_frame, boolean checked returns nothing
native DzFrameGetCheckBoxState takes integer check_box_frame returns boolean
native DzFrameIsFocus takes integer frame returns boolean
native DzFrameSetEditBoxActive takes integer frame, boolean is_active returns nothing
native DzFrameSetEditBoxDisableIme takes integer frame, boolean is_disable returns nothing
native DzIsWindowMode takes nothing returns boolean
native DzWindowSetPoint takes integer x, integer y returns nothing
native DzWindowSetSize takes integer width, integer height returns nothing
native DzGetSystemMetricsWidth takes nothing returns integer
native DzGetSystemMetricsHeight takes nothing returns integer
native DzGetDoodadsCount takes nothing returns integer
native DzSetDoodadsMatScale takes integer doodads_index, real x, real y, real z returns nothing
native DzSetDoodadsMatRotateX takes integer doodads_index, real x returns nothing
native DzSetDoodadsMatRotateY takes integer doodads_index, real y returns nothing
native DzSetDoodadsMatRotateZ takes integer doodads_index, real z returns nothing
native DzSetDoodadsMatReset takes integer doodads_index returns nothing
native DzSetUnitAbilityArt takes unit u, integer abil_id, string art_path returns boolean
native DzGetUnitAbilityArt takes unit u, integer abil_id returns string
native DzSetUnitAbilityTip takes unit u, integer abil_id, string tip returns boolean
native DzGetUnitAbilityTip takes unit u, integer abil_id returns string
native DzSetUnitAbilityUberTip takes unit u, integer abil_id, string ubertip returns boolean
native DzGetUnitAbilityUberTip takes unit u, integer abil_id returns string
native DzSetUnitAbilityUpdate takes unit u, integer abil_id returns boolean
native DzSetUnitAbilityOrderId takes unit u, integer abil_id, integer order_id returns boolean
native DzGetUnitAbilityOrderId takes unit u, integer abil_id returns integer
native DzSetUnitAbilitySpellBookList takes unit u, integer abil_id, string abil_list, boolean save_cooldown returns boolean
native DzGetUnitAbilitySpellBookList takes unit u, integer abil_id returns string
native DzSetUnitAbilityMissileArt takes unit u, integer abil_id, string missile_art returns boolean
native DzGetUnitAbilityMissileArt takes unit u, integer abil_id returns string
native DzSetUnitAbilityMissileSpeed takes unit u, integer abil_id, real missile_speed returns boolean
native DzGetUnitAbilityMissileSpeed takes unit u, integer abil_id returns real
native DzSetUnitAbilityMissileArc takes unit u, integer abil_id, real missile_arc returns boolean
native DzGetUnitAbilityMissileArc takes unit u, integer abil_id returns real
native DzSetUnitAbilityMissileHoming takes unit u, integer abil_id, boolean missile_homing returns boolean
native DzGetUnitAbilityMissileHoming takes unit u, integer abil_id returns boolean
native DzSetUnitAbilityMissileCount takes unit u, integer abil_id, integer missile_count returns boolean
native DzGetUnitAbilityMissileCount takes unit u, integer abil_id returns integer
native DzSetUnitAbilityMissileDamage takes unit u, integer abil_id, real damage, real max_damage, attacktype atktp, damagetype dmgtp returns boolean
native DzGetUnitAbilityMissileDamage takes unit u, integer abil_id returns real
native DzGetUnitAbilityMissileMaxDamage takes unit u, integer abil_id returns real
native DzSendKeyboard takes player p, integer key_code, integer is_down returns nothing
native DzForceUiKeyboard takes player p, integer key_code, integer is_down returns nothing
native DzDisableWindowKeyboard takes player p, integer key_code returns nothing
native DzDisableGameUIKeyboard takes player p, integer key_code returns nothing
native DzUnitCanPlaceAround takes widget obj, real x, real y returns boolean
native DzPositionCanPlaceAround takes real x, real y, real collision_size, integer collision_type returns boolean
native DzGetTerrainZ takes real x, real y returns real
native DzGetUnitZ takes unit u returns real
native DzGetUnitOverheadOffset takes widget u returns real
native DzFrameSetModelEnableWideScreen takes integer frame, boolean is_enable returns nothing
native DzSetUnitAbilityEnable takes unit u, integer abil_id returns boolean
native DzSetUnitAbilityDisable takes unit u, integer abil_id returns boolean
native DzGetUnitAbilityIsDisabled takes unit u, integer abil_id returns boolean
native DzGetUnitAbilityDisabledCount takes unit u, integer abil_id returns integer
native DzSetUnitAbilityTechReach takes unit u, integer abil_id, boolean reach returns boolean
native DzGetUnitAbilityTechReach takes unit u, integer abil_id returns boolean
native DzSetUnitAbilityTechReachTip takes unit u, integer abil_id, string tip returns boolean
native DzAsyncGetCurrentBuildingAbilityId takes nothing returns integer
native DzAsyncGetCurrentBuildingUnitId takes nothing returns integer
native DzFrameUnlockMouseRectLimit takes boolean is_unlock returns nothing
native KKSimpleFrameIsVisible takes integer simple_frame returns boolean
native DzFrameGetChatEditBar takes nothing returns integer
native DzGetLocalChatRecipient takes nothing returns integer
native DzPlayerSendChat takes player p, string msg, integer recipient returns nothing
native DzEnableHashtableSetNull takes boolean is_enable returns nothing
native DzSetItemCollisionSize takes item it, real size returns nothing
native DzGetItemCollisionSize takes item it returns real
native DzSetUnitDisableLocalOrder takes unit u, boolean is_disable returns nothing
native DzGetUnitDisableLocalOrder takes unit u returns boolean
native DzSetUnitDisableControlOrder takes unit u, boolean is_disable returns nothing
native DzGetUnitDisableControlOrder takes unit u returns boolean
native DzSetUnitAttack1TargetType takes unit u, integer target_type returns nothing
native DzGetUnitAttack1TargetType takes unit u returns integer
native DzSetUnitAttack2TargetType takes unit u, integer target_type returns nothing
native DzGetUnitAttack2TargetType takes unit u returns integer
native DzSetUnitAsAttackTargetType takes unit u, integer target_type returns nothing
native DzGetUnitAsAttackTargetType takes unit u returns integer
native DzFrameBindAddHideRect takes integer frame, real left, real bottom, real right, real top, real width, real height returns nothing
native DzFrameGetRealWidth takes integer frame returns real
native DzFrameGetRealHeight takes integer frame returns real
native DzSetUnitAbilitySpellBookAddAbility takes unit u, integer abil_id, integer add_abil_id returns boolean
native DzSetUnitAbilitySpellBookRemoveAbility takes unit u, integer abil_id, integer remove_abil_id returns boolean
native KKCommandButtonGetAbilityId takes integer command_button returns integer
native KKCommandButtonGetOrderId takes integer command_button returns integer
native DzFixUnitEventMemoryLeak takes nothing returns nothing
native DzGetUnitPojectileLaunchX takes unit u returns real
native DzGetUnitPojectileLaunchY takes unit u returns real
native DzGetUnitPojectileLaunchZ takes unit u returns real
native DzLaunchMissile takes unit source, widget target, string model, integer team_color, integer color, real x, real y, real z, real scale, real speed, attacktype attack_type, damagetype damage_type, weapontype weapon_type, real damage, real arc, boolean homing, boolean can_miss, boolean never_miss, boolean attack, integer flags returns boolean
native DzLaunchMissileBounce takes unit source, widget target, string model, integer team_color, integer color, real x, real y, real z, real scale, real speed, attacktype attack_type, damagetype damage_type, weapontype weapon_type, real damage, real arc, boolean homing, boolean can_miss, boolean never_miss, boolean attack, integer flags, integer target_flags, integer target_count, real bounce_range, real damage_loss returns boolean
native DzLaunchMissileLine takes unit source, widget target, string model, integer team_color, integer color, real x, real y, real z, real scale, real speed, attacktype attack_type, damagetype damage_type, weapontype weapon_type, real damage, real arc, boolean homing, boolean can_miss, boolean never_miss, boolean attack, integer flags, integer target_flags, real damage_loss, real distance, real range returns boolean
native DzLaunchMissileSplash takes unit source, widget target, string model, integer team_color, integer color, real x, real y, real z, real scale, real speed, attacktype attack_type, damagetype damage_type, weapontype weapon_type, real damage, real arc, boolean homing, boolean can_miss, boolean never_miss, boolean attack, integer flags, integer target_flags, real half_factor, real quar_factor, real full_area, real half_area, real quar_area returns boolean
native DzLaunchArtillery takes unit source, widget target, real target_x, real target_y, string model, integer team_color, integer color, real x, real y, real z, real scale, real speed, attacktype attack_type, damagetype damage_type, weapontype weapon_type, real damage, real arc, boolean attack, integer flags, real min_distance, integer target_flags, real half_factor, real quar_factor, real full_area, real half_area, real quar_area returns boolean
native DzLaunchArtilleryLine takes unit source, widget target, real target_x, real target_y, string model, integer team_color, integer color, real x, real y, real z, real scale, real speed, attacktype attack_type, damagetype damage_type, weapontype weapon_type, real damage, real arc, boolean attack, integer flags, real min_distance, integer target_flags, real half_factor, real quar_factor, real full_area, real half_area, real quar_area, real damage_loss, real distance, real range returns boolean
native DzLaunchMissileCarrionSwarmEx takes unit source, string model, integer team_color, integer color, real x, real y, real z, real facing, real distance, real scale, real speed, attacktype attack_type, damagetype damage_type, weapontype weapon_type, real damage, integer flags, integer target_flags, real start_radius, real end_radius, real max_damage, integer buffID returns boolean
native DzKillUnit takes unit whichUnit, unit killer returns boolean
native DzSetUnitXY takes unit whichUnit, real x, real y returns boolean
native DzSetUnitAbilityEngineeringUpgrade takes unit whichUnit, integer old_id, integer new_id, boolean update_hero_ability returns boolean
native DzSetUnitAbilityEngineeringUpgradeCancel takes unit whichUnit, integer old_id returns boolean
native DzGetUnitAbilityEngineeringUpgradeNewId takes unit whichUnit, integer old_id returns integer
native DzGetUnitAbilityEngineeringUpgradeOldId takes unit whichUnit, integer new_id returns integer
native DzSetUnitAbilityCastTime takes unit u, integer abil_id, real value returns boolean
native DzGetUnitAbilityCastTime takes unit u, integer abil_id returns real
native DzSetUnitAbilityDuration takes unit u, integer abil_id, real value returns boolean
native DzGetUnitAbilityDuration takes unit u, integer abil_id returns real
native DzSetUnitAbilityHeroDuration takes unit u, integer abil_id, real value returns boolean
native DzGetUnitAbilityHeroDuration takes unit u, integer abil_id returns real
native DzSetUnitAbilityCastPoint takes unit u, integer abil_id, real value returns boolean
native DzGetUnitAbilityCastPoint takes unit u, integer abil_id returns real
native DzSetUnitAbilityBackSwing takes unit u, integer abil_id, real value returns boolean
native DzGetUnitAbilityBackSwing takes unit u, integer abil_id returns real
native DzSetUnitLifeRegen takes unit whichUnit, real regen returns boolean
native DzGetUnitLifeRegen takes unit whichUnit returns real
native DzSetUnitManaRegen takes unit whichUnit, real regen returns boolean
native DzGetUnitManaRegen takes unit whichUnit returns real
native DzSetUnitMinSpeed takes unit whichUnit, real speed, boolean ignore_polymorph returns boolean
native DzGetUnitMinSpeed takes unit whichUnit returns real
native DzSetUnitMaxSpeed takes unit whichUnit, real speed, boolean ignore_polymorph returns boolean
native DzGetUnitMaxSpeed takes unit whichUnit returns real
native DzSetUnitCastPoint takes unit whichUnit, real cast_point returns boolean
native DzGetUnitCastPoint takes unit whichUnit returns real
native DzSetUnitBackSwing takes unit whichUnit, real back_swing returns boolean
native DzGetUnitBackSwing takes unit whichUnit returns real
native DzSetUnitAttackTargetCount takes unit whichUnit, integer index, integer target_count returns boolean
native DzGetUnitAttackTargetCount takes unit whichUnit, integer index returns integer
native DzSetHeroPrimaryAttributeType takes unit whichUnit, integer attribute, boolean keep_primary_bonus returns boolean
native DzGetHeroPrimaryAttributeType takes unit whichUnit returns integer
native DzSetHeroPrimaryAttribute takes unit whichUnit, integer attribute returns boolean
native DzGetHeroPrimaryAttribute takes unit whichUnit, boolean include_bonus returns integer
native DzSetHeroPrimaryAttributePlus takes unit whichUnit, integer attreibute, real value, boolean keep_current_bonus returns boolean
native DzGetHeroPrimaryAttributePlus takes unit whichUnit, integer attribute returns real
native DzDisableAttackSpeedLimit takes nothing returns nothing
native DzSetMinMaxAttackSpeedFactor takes real min_factor, real max_factor returns nothing
native DzSetMoveSpeedBonusesStack takes boolean is_enable returns nothing
native DzSetGlobalUnitMinMaxMoveSpeed takes real building_min, real building_max, real unit_min, real unit_max, real GC_building_min, real GC_building_max, real GC_unit_min, real GC_unit_max, real harvest_min, real windwalk_max returns nothing
native DzSaveHandleId takes hashtable whichHashtable, integer parentKey, integer childKey, integer handleId returns boolean
native DzSaveHandleIdEx takes hashtable whichHashtable, integer parentKey, integer childKey, integer handleId, integer handleType returns boolean
native DzLoadHandleId takes hashtable whichHashtable, integer parentKey, integer childKey returns integer
native DzSetHashtableLimit takes integer maxCount returns nothing
native DzDisableRemoveExtraDeadHero takes nothing returns nothing
native DzSetPlayerPathFindingLimit takes player whichPlayer, integer limit1, integer limit2, integer limit3, integer limit4 returns boolean
native DzSetGameConstantFoodCeiling takes integer value returns nothing
native DzDisableLoadingPressAKey takes nothing returns nothing
native DzMultiboardGetFrame takes multiboard whichMultiboard returns integer
native DzTimerDialogGetFrame takes timerdialog whichTimerDialog returns integer
native DzFrameAddTextShadow takes integer whichFrame, real offsetX, real offsetY, integer color returns boolean
native DzFrameDuplicateTextShadow takes integer whichFrame, integer count returns boolean
native DzSetCommandButtonShowCooldown takes boolean showAbility, boolean showItem returns nothing
native DzSetCommandButtonShowHotkey takes boolean showAbility, boolean showItem returns nothing
native DzSetCommandButtonHotkeyBackground takes string filepath returns nothing
native DzGetEnumEffect takes nothing returns effect
native DzUpdateEffectSmartPosition takes effect whichEffect returns boolean
native DzRemoveEffect takes effect whichEffect returns boolean
native DzRemoveEffectTimed takes effect whichEffect, real time returns boolean
native DzSetEffectAlwaysRender takes effect whichEffect, boolean flag returns boolean
native DzDieEffectTimed takes effect whichEffect, real time returns boolean
native DzSetEffectGroupBlacklist takes effect whichEffect, boolean flag returns boolean
native DzSetEffectAttachedModelScale takes effect whichEffect, real scaleX, real scaleY, real scaleZ returns boolean
native DzFrameSetAttachedModelScale takes integer frame, real scaleX, real scaleY, real scaleZ returns boolean
native DzEffectReplayBirth takes effect whichEffect returns nothing
native DzGetBuffBar takes nothing returns integer
native DzGetBuffBarButton takes integer row, integer col returns integer
native DzBuffBarResize takes integer row, integer col returns nothing
native DzSetBuffBarShowDuplicatedBuff takes boolean flag returns nothing
native DzUnitAddBuff takes unit target, unit source, integer typeId, integer buffId, integer level, integer priority, real duration, real data1, real data2, real data3, real data4, real data5, real data6, real data7, real data8, real data9, real data10, real data11 returns boolean
native DzUnitAddBuffBdet takes unit target, integer buffId, integer level, integer priority, real duration, player detectPlayer, integer detectType returns boolean
native DzUnitAddBuffBUan takes unit target, integer buffId, integer level, integer priority, real duration, integer invulnerable returns boolean
native DzUnitAddBuffBFig takes unit target, integer buffId, integer level, integer priority, real duration returns boolean
native DzUnitAddBuffBEfn takes unit target, integer buffId, integer level, integer priority, real duration returns boolean
native DzUnitAddBuffBhwd takes unit target, integer buffId, integer level, integer priority, real duration returns boolean
native DzUnitAddBuffBplg takes unit target, integer buffId, integer level, integer priority, real duration returns boolean
native DzUnitAddBuffBrai takes unit target, integer buffId, integer level, integer priority, real duration returns boolean
native DzUnitAddBuffBHwe takes unit target, integer buffId, integer level, integer priority, real duration returns boolean
native DzUnitAddBuffBTLF takes unit target, integer buffId, integer level, integer priority, real duration returns boolean
native DzUnitAddBuffBdef takes unit target, integer buffId, integer level, integer priority, real duration, real armor returns boolean
native DzUnitAddBuffBdig takes unit target, unit source, integer buffId, integer level, integer priority, real duration, real dps returns boolean
native DzUnitAddBuffBHds takes unit target, integer buffId, integer level, integer priority, real duration returns boolean
native DzUnitAddBuffBNdo takes unit target, unit source, integer buffId, integer level, integer priority, real duration, real dps, player owner, integer unitId, integer count, real lifeTime, integer summonBuffId returns boolean
native DzUnitAddBuffBNdi takes unit target, integer buffId, integer level, integer priority, real duration returns boolean
native DzUnitAddBuffBNdh takes unit target, unit source, integer buffId, integer level, integer priority, real duration, real moveSpeed, real attackSpeed, integer disableType, real missChance returns boolean
native DzUnitAddBuffBOeq takes unit target, unit source, integer buffId, integer level, integer priority, real duration, real moveSpeed, real attackSpeed returns boolean
native DzUnitAddBuffBeat takes unit target, integer buffId, integer level, integer priority, real duration, real health, real mana returns boolean
native DzUnitAddBuffBgra takes unit target, integer buffId, integer level, integer priority, real duration, integer attackCount, integer disableWeapon, integer enableWeapon, integer treeId returns boolean
native DzUnitAddBuffBena takes unit target, unit source, integer buffId, integer level, integer priority, real duration, player owner, real fallTime, real height, real meleeRange returns boolean
native DzUnitAddBuffBeng takes unit target, unit source, integer buffId, integer level, integer priority, real duration, player owner, real fallTime, real height, real meleeRange returns boolean
native DzUnitAddBuffBwea takes unit target, unit source, integer buffId, integer level, integer priority, real duration, player owner, real fallTime, real height, real meleeRange returns boolean
native DzUnitAddBuffBweb takes unit target, unit source, integer buffId, integer level, integer priority, real duration, player owner, real fallTime, real height, real meleeRange returns boolean
native DzUnitAddBuffBEer takes unit target, unit source, integer buffId, integer level, integer priority, real duration, real dps returns boolean
native DzUnitAddBuffBcrsV2 takes unit target, unit source, integer buffId, integer level, integer priority, real duration, real missChance returns boolean
native DzUnitAddBuffBeye takes unit target, integer buffId, integer level, integer priority, real duration returns boolean
native DzUnitAddBuffBfae takes unit target, integer buffId, integer level, integer priority, real duration, player owner, real armorReduce returns boolean
native DzUnitAddBuffBshs takes unit target, integer buffId, integer level, integer priority, real duration, player owner returns boolean
native DzUnitAddBuffBNlm takes unit target, integer buffId, integer level, integer priority, real duration, integer splitCount, real splitDelay, integer attackNeeded, real healthBonus, real lifeTimeBonus, integer maxCount, integer remainingCount, real distance returns boolean
native DzUnitAddBuffBNso takes unit target, unit source, integer buffId, integer level, integer priority, real duration, real damage, real interval, real moveSpeedReduce, real attackSpeedReduce, real attackReduce returns boolean
native DzUnitAddBuffBPSE takes unit target, unit source, integer buffId, integer level, integer priority, real duration returns boolean
native DzUnitAddBuffBHfa takes unit target, integer buffId, integer level, integer priority, real duration, real damage returns boolean
native DzUnitAddBuffBUfa takes unit target, integer buffId, integer level, integer priority, real duration, real debuffDuration, real armor returns boolean
native DzUnitAddBuffBfro takes unit target, unit source, integer buffId, integer level, integer priority, real duration, real moveSpeed, real attackSpeed returns boolean
native DzUnitAddBuffBOhx takes unit target, unit source, integer buffId, integer level, integer priority, real duration, integer unitId returns boolean
native DzUnitAddBuffBNht takes unit target, integer buffId, integer level, integer priority, real duration, real damageIncrease, real armor, real healthRegen, real manaRegen returns boolean
native DzUnitAddBuffBprg takes unit target, unit source, integer buffId, integer level, integer priority, real duration, real moveSpeedUpdateCount, real attackSpeedUpdateCount, real pauseDuration, real heroPauseDuration returns boolean
native DzUnitAddBuffBhea takes unit target, unit source, integer buffId, integer level, integer priority, real duration returns boolean
native DzUnitAddBuffBrej takes unit target, integer buffId, integer level, integer priority, real duration, real health, real mana returns boolean
native DzUnitAddBuffBIrm takes unit target, integer buffId, integer level, integer priority, real duration, real mana, integer dispel returns boolean
native DzUnitAddBuffBIrl takes unit target, integer buffId, integer level, integer priority, real duration, real health, integer dispel returns boolean
native DzUnitAddBuffBIrg takes unit target, integer buffId, integer level, integer priority, real duration, real health, real mana, integer dispel returns boolean
native DzUnitAddBuffBfre takes unit target, unit source, integer buffId, integer level, integer priority, real duration, integer mirrorImage returns boolean
native DzUnitAddBuffBIcb takes unit target, integer buffId, integer level, integer priority, real duration, real armorReduce returns boolean
native DzUnitAddBuffBIrb takes unit target, integer buffId, integer level, integer priority, real duration returns boolean
native DzUnitAddBuffBIpv takes unit target, integer buffId, integer level, integer priority, real duration, real lifeSteal, real damageBonus returns boolean
native DzUnitAddBuffBUcb takes unit target, unit source, integer buffId, integer level, integer priority, real duration returns boolean
native DzUnitAddBuffBEia takes unit target, integer buffId, integer level, integer priority, real duration, real damage returns boolean
native DzUnitAddBuffBEim takes unit target, integer buffId, integer level, integer priority, real duration, real manaCost, real interval, real area, real damage, integer targetFlags, player owner returns boolean
native DzUnitAddBuffBNpi takes unit target, integer buffId, integer level, integer priority, real duration, real manaCost, real interval, real area, real damage, integer targetFlags, player owner returns boolean
native DzUnitAddBuffBpig takes unit target, integer buffId, integer level, integer priority, real duration, real manaCost, real interval, real area, real damage, integer targetFlags, player owner returns boolean
native DzUnitAddBuffBIcf takes unit target, integer buffId, integer level, integer priority, real duration, real manaCost, real interval, real area, real damage, integer targetFlags, player owner returns boolean
native DzStartManageInventory takes integer maxSize returns boolean
native DzSetInventoryHotkey takes integer slot, string hotkey returns boolean
native DzGetInventoryMaxSize takes nothing returns integer
native DzGetInventoryDropSlotOrderID takes integer slot returns integer
native DzGetInventoryUseSlotOrderID takes integer slot returns integer
native DzGetInventoryBarButton takes integer slot returns integer
native DzTriggerRegisterPlayerUnitSwapItemSlotEvent takes trigger whichTrigger, player whichPlayer returns event
native DzGetSwapItemSlotEventFromSlotID takes nothing returns integer
native DzGetSwapItemSlotEventToSlotID takes nothing returns integer
native DzUnitAddBuffBUim takes unit target, unit source, integer buffId, integer level, integer priority, real duration, real data1, real data2 returns boolean
native DzUnitAddBuffBNin takes unit target, unit source, integer buffId, integer level, integer priority, real duration, real data1, real data2 returns boolean
native DzUnitAddBuffBinf takes unit target, integer buffId, integer level, integer priority, real duration, real data1, real data2, real data3, real data4 returns boolean
native DzUnitAddBuffBinv takes unit target, integer buffId, integer level, integer priority, real duration, real data1 returns boolean
native DzUnitAddBuffBvul takes unit target, integer buffId, integer level, integer priority, real duration returns boolean
native DzUnitAddBuffBlsh takes unit target, integer buffId, integer level, integer priority, real duration, real data1, real data2, real data3 returns boolean
native DzUnitAddBuffBlshV2 takes unit target, integer buffId, integer level, integer priority, real duration, real data1, real data2, real data3, integer data4, player owner returns boolean
native DzUnitAddBuffBams takes unit target, integer buffId, integer level, integer priority, real duration returns boolean
native DzUnitAddBuffBam2 takes unit target, integer buffId, integer level, integer priority, real duration, real data1 returns boolean
native DzUnitAddBuffBmfl takes unit target, integer buffId, integer level, integer priority, real duration, real data1, real data2, real data3, real data4, real data5, real data6, real data7, integer data8, integer data9, integer data10 returns boolean
native DzUnitAddBuffBNms takes unit target, integer buffId, integer level, integer priority, real duration, real data1, real data2 returns boolean
native DzUnitAddBuffBOmi takes unit target, unit source, integer buffId, integer level, integer priority, real duration, real data1, real data2 returns boolean
native DzUnitAddBuffBIil takes unit target, unit source, integer buffId, integer level, integer priority, real duration, real data1, real data2 returns boolean
native DzUnitAddBuffBNpa takes unit target, integer buffId, integer level, integer priority, real duration, real data1, real data2, real data3, integer data4, integer data5, integer data6, real data7, player owner, integer data8 returns boolean
native DzUnitAddBuffBNpm takes unit target, integer buffId, integer level, integer priority, real duration returns boolean
native DzUnitAddBuffBpsh takes unit target, unit source, integer buffId, integer level, integer priority, real duration returns boolean
native DzUnitAddBuffBply takes unit target, unit source, integer buffId, integer level, integer priority, real duration, integer data1 returns boolean
native DzUnitAddBuffBNsa takes unit target, integer buffId, integer level, integer priority, real duration, real data1, real data2, real data3 returns boolean
native DzUnitAddBuffBHtc takes unit target, unit source, integer buffId, integer level, integer priority, real duration, real data1, real data2 returns boolean
native DzUnitAddBuffBCtc takes unit target, unit source, integer buffId, integer level, integer priority, real duration, real data1, real data2 returns boolean
native DzUnitAddBuffBNfy takes unit target, integer buffId, integer level, integer priority, real duration, real data1, integer data2, real data3, integer data4, real data5, real data6 returns boolean
native DzUnitAddBuffBNcg takes unit target, unit source, integer buffId, integer level, integer priority, real duration, real data1, real data2, real data3 returns boolean
native DzUnitAddBuffBNto takes unit target, integer buffId, integer level, integer priority, real duration returns boolean
native DzUnitAddBuffBuhf takes unit target, unit source, integer buffId, integer level, integer priority, real duration, real data1, real data2 returns boolean
native DzUnitAddBuffBuns takes unit target, unit source, integer buffId, integer level, integer priority, real duration, real data1, real data2 returns boolean
native DzUnitAddBuffBOvc takes unit target, integer buffId, integer level, integer priority, real duration returns boolean
native DzUnitAddBuffBOvd takes unit target, integer buffId, integer level, integer priority, real duration returns boolean
native DzUnitAddBuffBOwd takes unit target, integer buffId, integer level, integer priority, real duration returns boolean
native DzUnitAddBuffBImo takes unit target, integer buffId, integer level, integer priority, real duration, real data1, real data2, real data3 returns boolean
native DzUnitAddBuffBNwm takes unit target, integer buffId, integer level, integer priority, real duration returns boolean
native DzUnitAddBuffBmec takes unit target, integer buffId, integer level, integer priority, real duration returns boolean
native DzUnitAddBuffBNsg takes unit target, integer buffId, integer level, integer priority, real duration returns boolean
native DzUnitAddBuffBNsq takes unit target, integer buffId, integer level, integer priority, real duration returns boolean
native DzUnitAddBuffBNsw takes unit target, integer buffId, integer level, integer priority, real duration returns boolean
native DzUnitAddBuffBOwk takes unit target, integer buffId, integer level, integer priority, real duration, real data1, real data2, real data3, integer data4 returns boolean
native DzUnitAddBuffBfrz takes unit target, unit source, integer buffId, integer level, integer priority, real duration returns boolean
native DzUnitAddBuffBliq takes unit target, unit source, integer buffId, integer level, integer priority, real duration, real data1, real data2, real data3, integer data4 returns boolean
native DzUnitAddBuffBNab takes unit target, unit source, integer buffId, integer level, integer priority, real duration, real data1, real data2, real data3, real data4, real data5 returns boolean
native DzUnitAddBuffBNsl takes unit target, unit source, integer buffId, integer level, integer priority, real duration returns boolean
native DzUnitAddBuffBHbn takes unit target, unit source, integer buffId, integer level, integer priority, real duration, real data1, real data2 returns boolean
native DzUnitAddBuffBbsk takes unit target, unit source, integer buffId, integer level, integer priority, real duration, real data1, real data2, real data3 returns boolean
native DzUnitAddBuffBNdm takes unit target, integer buffId, integer level, integer priority, real duration returns boolean
native DzUnitAddBuffBNba takes unit target, unit source, integer buffId, integer level, integer priority, real duration, player owner, integer data1, integer data2, real data3, integer data4 returns boolean
native DzUnitAddBuffBNrd takes unit target, unit source, integer buffId, integer level, integer priority, real duration, real data1 returns boolean
native DzUnitAddBuffBblo takes unit target, unit source, integer buffId, integer level, integer priority, real duration, real data1, real data2, real data3 returns boolean
native DzUnitAddBuffBfzy takes unit target, unit source, integer buffId, integer level, integer priority, real duration, real data1, real data2, real data3 returns boolean
native DzUnitAddBuffBNbf takes unit target, unit source, integer buffId, integer level, integer priority, real duration, real data1 returns boolean
native DzUnitAddBuffBCbf takes unit target, unit source, integer buffId, integer level, integer priority, real duration, real data1 returns boolean
native DzUnitAddBuffBpos takes unit target, unit source, integer buffId, integer level, integer priority, real duration, integer data1, integer data2 returns boolean
native DzUnitAddBuffBpoc takes unit target, integer buffId, integer level, integer priority, real duration returns boolean
native DzUnitAddBuffBcmg takes unit target, integer buffId, integer level, integer priority, real duration returns boolean
native DzUnitAddBuffBclf takes unit target, unit source, integer buffId, integer level, integer priority, real duration, real data1, real data2, integer data3, real data4 returns boolean
native DzSetUnitAbilityDataF takes unit Unit, integer abil_code, real value returns boolean
native DzGetUnitAbilityDataF takes unit Unit, integer abil_code returns real
native DzSetUnitAbilityDataG takes unit Unit, integer abil_code, real value returns boolean
native DzGetUnitAbilityDataG takes unit Unit, integer abil_code returns real
native DzSetUnitAbilityDataH takes unit Unit, integer abil_code, real value returns boolean
native DzGetUnitAbilityDataH takes unit Unit, integer abil_code returns real
native DzSetUnitAbilityDataI takes unit Unit, integer abil_code, real value returns boolean
native DzGetUnitAbilityDataI takes unit Unit, integer abil_code returns real
native GetUnitGoldCost takes integer unitid returns integer
native GetUnitWoodCost takes integer unitid returns integer
native GetUnitBuildTime takes integer unitid returns integer
native GetUnitCountDone takes integer unitid returns integer
native JNSetMaxAttackSpeed takes real speed returns nothing
native IsHostPlayer takes nothing returns boolean
native JNGetModuleHandle takes string moduleName returns integer
native JNMemoryGetInteger takes integer offset returns integer
native JNMemorySetReal takes integer offset,real value returns nothing
native JNUse takes nothing returns boolean
native JNOpenBrowser takes string Address returns nothing
native JNMapServerLog takes string MapId,string SecretKey,string Version,string Loging returns string
native JNRPGGetCharacterCount takes string MapId,string UserId,string SecretKey returns integer
native JNRPGGetCharacterNameByIndex takes string UserId,integer Index returns string
native JNObjectCharacterInit takes string MapId,string UserId,string SecretKey,string Character returns integer
native JNObjectCharacterSave takes string MapId,string UserId,string SecretKey,string Character returns string
native JNObjectCharacterSetInt takes string UserId,string Field,integer Value returns nothing
native JNObjectCharacterGetInt takes string UserId,string Field returns integer
native JNObjectCharacterResetCharacter takes string UserId returns nothing
native JNObjectCharacterGetCharacterCount takes string MapId,string UserId,string SecretKey returns integer
native JNObjectCharacterGetCharacterNameByIndex takes string UserId,integer Index returns string
native JNObjectUserInit takes string MapId,string Userid,string SecretKey,string Character returns integer
native JNObjectUserSave takes string MapId,string UserId,string SecretKey,string Character returns string
native JNObjectUserSetInt takes string UserId,string Field,integer Value returns nothing
native JNObjectUserGetInt takes string UserId,string Field returns integer
native JNStringPos takes string str,string sub returns integer
native JNStringSplit takes string str,string sub,integer index returns string
native JNStringSub takes string str,integer start,integer length returns string
native JNStringLength takes string str returns integer
native EXGetUnitString takes integer unitcode, integer data_type returns string
native EXSetUnitString takes integer unitcode, integer data_type, string value returns boolean
native EXGetUnitReal takes integer unitcode, integer data_type returns real
native EXSetUnitReal takes integer unitcode, integer data_type, real value returns boolean
native EXGetUnitInteger takes integer unitcode, integer data_type returns integer
native EXGetUnitArrayString takes integer unitcode, integer data_type, integer index returns string
native BitOr takes integer x, integer y returns integer
native BitAnd takes integer x, integer y returns integer
native BitXor takes integer x, integer y returns integer
native BitShiftL takes integer x, integer y returns integer
native BitShiftR takes integer x, integer y returns integer
native JNI2R takes integer i returns real
native JNR2I takes real r returns integer
native JNWriteLog takes string str returns nothing
native JNWriteLogReal takes real r returns nothing
native JNGetLocalDateTime takes nothing returns string
native JNGetLocalUnixTime takes nothing returns integer
native JNGetMaxAttackSpeed takes nothing returns real
native IsReplayMode takes nothing returns boolean
native JNGetSyncDelay takes nothing returns integer
native JNSetSyncDelay takes integer delay returns nothing
native JNGetConnectionState takes nothing returns integer
native JNProcessStart takes string fileName, string arguments returns boolean
native JNFindModuleHandle takes integer offset, integer signature returns integer
native JNMemoryGetByte takes integer offset returns integer
native JNMemorySetByte takes integer offset, integer value returns nothing
native JNMemorySetInteger takes integer offset, integer value returns nothing
native JNMemoryGetReal takes integer offset returns real
native JNMemoryGetString takes integer offset, integer length returns string
native JNMemorySetString takes integer offset, string value returns nothing
native JNProcCall takes integer callConv, integer address, hashtable params returns boolean
native JNServerPluginVersion takes nothing returns integer
native JNCheckNameHack takes string UserId returns boolean
native JNServerTime takes string Format returns string
native JNServerUnixTime takes nothing returns integer
native JNPushReg takes string MapId returns nothing
native JNGetPushMessage takes nothing returns string
native JNSetLog takes string MapId, string UserId, string SecretKey, string Character, string Version, string Loging returns string
native JNSetLogUseType takes string MapId, string UserId, string SecretKey, string Character, string Version, string Loging, string LogType returns string
native JNPublicMapServerLog takes string MapId, string SecretKey, string Version, string Loging returns string
native JNMapServerLogUseType takes string MapId, string SecretKey, string Version, string Loging, string LogType returns string
native JNReplayReg takes string MapId, string SecretKey, string UserId, string Character, string Loging returns nothing
native JNScreenShotReg takes string MapId, string SecretKey, string UserId, string Character, string Loging returns boolean
native JNPublicScreenShotReg takes string MapId, string SecretKey, string UserId, string Character, string Tag, string Loging returns boolean
native JNUseUserRoleItemInfo takes string MapId, string SecretKey, string UserId, string ItemName returns string
native JNSetSaveCode takes string MapId, string UserId, string SecretKey, string Character, string Code returns string
native JNGetLoadCode takes string MapId, string UserId, string SecretKey, string Character returns string
native JNObjectCharacterServerConnectCheck takes nothing returns boolean
native JNObjectCharacterSetReal takes string UserId, string Field, real Value returns nothing
native JNObjectCharacterGetReal takes string UserId, string Field returns real
native JNObjectCharacterSetString takes string UserId, string Field, string Value returns nothing
native JNObjectCharacterGetString takes string UserId, string Field returns string
native JNObjectCharacterSetBoolean takes string UserId, string Field, boolean Value returns nothing
native JNObjectCharacterGetBoolean takes string UserId, string Field returns boolean
native JNObjectCharacterRemoveField takes string Userid, string Field returns nothing
native JNObjectCharacterClearField takes string UserId returns nothing
native JNObjectScoreInit takes string MapId, string SecretKey, string UserId, string Character returns integer
native JNObjectScoreGet takes string UserId, string Field returns integer
native JNObjectScoreAdd takes string UserId, string Field, integer Value returns nothing
native JNObjectScoreSet takes string UserId, string Field, integer Value returns nothing
native JNObjectScoreSave takes string MapId, string SecretKey, string UserId, string Character returns string
native JNObjectCharacterUseEndGameSave takes string MapId, string UserId, string SecretKey, string Character returns nothing
native JNObjectCharacterPopGlobalMessage takes nothing returns string
native JNObjectCharacterSendGlobalMessage takes string message returns nothing
native JNObjectUserSetReal takes string UserId, string Field, real Value returns nothing
native JNObjectUserGetReal takes string UserId, string Field returns real
native JNObjectUserSetString takes string UserId, string Field, string Value returns nothing
native JNObjectUserGetString takes string UserId, string Field returns string
native JNObjectUserSetBoolean takes string UserId, string Field, boolean Value returns nothing
native JNObjectUserGetBoolean takes string UserId, string Field returns boolean
native JNObjectUserRemoveField takes string UserId, string Field returns nothing
native JNObjectUserClearField takes string UserId returns nothing
native JNObjectUserResetCharacter takes string UserId returns nothing
native JNObjectUserUseEndGameSave takes string MapId, string UserId, string SecretKey, string Character returns nothing
native JNObjectMapInit takes string MapId, string SecretKey returns integer
native JNObjectMapGetInt takes string Field returns integer
native JNObjectMapGetReal takes string Field returns real
native JNObjectMapGetString takes string Field returns string
native JNObjectMapGetBoolean takes string Field returns boolean
native JNDailySave takes string MapId, string UserId, string SecretKey, string Character, string DailyType returns string
native JNDailyCheckToday takes string MapId, string UserId, string SecretKey, string Character, string DailyType returns string
native JNDailyCheckTodayList takes string MapId, string UserId, string SecretKey, string Character, string DailyType returns string
native JNDailyCountWeek takes string MapId, string UserId, string SecretKey, string Character, string DailyType, string WeekDay returns string
native JNDailyCountWeekList takes string MapId, string UserId, string SecretKey, string Character, string DailyType, string WeekDay returns string
native JNDailyCountMonth takes string MapId, string UserId, string SecretKey, string Character, string DailyType returns string
native JNDailyCountMonthList takes string MapId, string UserId, string SecretKey, string Character, string DailyType returns string
native JNPVPCharacter takes string UserId, string Character returns nothing
native JNPVPKill takes string UserId returns nothing
native JNPVPDeath takes string UserId returns nothing
native JNPVPAssist takes string UserId returns nothing
native JNPVPLog takes string UserId, string Log returns nothing
native JNPVPWin takes string UserId, boolean Win returns nothing
native JNSetPVPLog2 takes string MapId, string UserId, string SecretKey, string Character, boolean Win, integer Kill, integer Death, integer Assist, integer Point, string Loging returns string
native JNSetAreasteal takes string MapId, string UserId, string SecretKey, string Character, integer Area, integer Score returns string
native JNRemoveAreasteal takes string MapId, string UserId, string SecretKey, string Character, integer Area returns string
native JNGetMyAreastealScore takes string MapId, string UserId, string SecretKey, string Character, integer Area returns integer
native JNInitBestAreastealtop10 takes string MapId, string UserId, string SecretKey, string Character, integer Area returns integer
native JNGetBestAreasteal takes integer Area, integer Index, string Format returns string
native JNInitBestMultiAreasteal takes string MapId, string UserId, string SecretKey, string Character, string Areas returns integer
native JNGetMultipleBestAreasteal takes integer Area, string Format returns string
native JNUserJoinGroupInfo takes string MapId, string UserId, string SecretKey returns string
native JNGroupManageLog takes string MapId, string UserId, string SecretKey, string Log returns string
native JNGroupNumberGet takes string MapId, string UserId, string SecretKey, string Field returns real
native JNGroupNumberAdd takes string MapId, string UserId, string SecretKey, string Field, real Number returns string
native JNGroupStringGet takes string MapId, string UserId, string SecretKey, string Field returns string
native JNGroupStringSet takes string MapId, string UserId, string SecretKey, string Field, string Set returns string
native JNInitMail takes string MapId, string UserId, string SecretKey, string Character returns integer
native JNGetMailItem takes integer Index returns string
native JNGetMailMsg takes integer Index returns string
native JNGetMailid takes integer Index returns string
native JNGetMailremove takes string MapId, string UserId, string SecretKey, string Character, string Id returns boolean
native JNStringReverse takes string str returns string
native JNStringTrim takes string str returns string
native JNStringTrimStart takes string str returns string
native JNStringTrimEnd takes string str returns string
native JNStringRegex takes string str, string regex, integer index returns string
native JNStringCount takes string str, string sub returns integer
native JNStringContains takes string str, string sub returns boolean
native JNStringReplace takes string str, string old, string newstr returns string
native JNStringInsert takes string str, integer index, string val returns string
native JNStringEncrypt takes string plainText, string key returns string
native JNStringDecrypt takes string cipherText, string key returns string
native JNStringFromBase64 takes string str returns string
native JNStringToBase64 takes string str returns string
native JNGetScoreRankListScore takes integer index returns integer
native JNGetScoreRankListUserId takes integer index returns string
native JNGetScoreRankListInit takes string MapId, string SecretKey, string Field returns integer
native JNGetScoreRankListInit50 takes string MapId, string SecretKey, string Field returns integer
native JNGetScoreRank takes string MapId, string SecretKey, string UserId, string Character, string Field returns integer
type dzeffectgroup extends agent
native DzEffectGroupCreate takes nothing returns dzeffectgroup
native DzEffectGroupGetSize takes dzeffectgroup whichEffectGroup returns integer
native DzEffectGroupAt takes dzeffectgroup whichEffectGroup, integer index returns effect
native DzEffectGroupClear takes dzeffectgroup whichEffectGroup returns integer
native DzEffectGroupAdd takes dzeffectgroup whichEffectGroup, effect whichEffect, boolean allowDuplicate returns integer
native DzEffectGroupRemove takes dzeffectgroup whichEffectGroup, effect whichEffect, boolean firstOnly returns boolean
native DzEffectGroupEnumRange takes dzeffectgroup whichEffectGroup, real x, real y, real range, boolean clear, boolean allowDuplicate returns integer
native DzEffectGroupEnumRect takes dzeffectgroup whichEffectGroup, rect whichRect, boolean clear, boolean allowDuplicate returns integer
native DzEffectGroupContains takes dzeffectgroup whichEffectGroup, effect whichEffect returns boolean
native DzEffectGroupDestroy takes dzeffectgroup whichEffectGroup returns boolean
native DzForEffectGroup takes dzeffectgroup whichEffectGroup, code callback returns integer
native DzHandle2EffectGroup takes integer handleID returns dzeffectgroup
native SaveDzEffectGroupHandle takes hashtable table, integer parentKey, integer childKey, dzeffectgroup g returns boolean
native LoadDzEffectGroupHandle takes hashtable table, integer parentKey, integer childKey returns dzeffectgroup
