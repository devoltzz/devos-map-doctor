# Finds the interface memory hacks of patches 1.24-1.28 (the MemHackAPI) and gives each one its Warcraft III 3.0 equivalent.
import json
import os
import re


HERE = os.path.dirname(os.path.abspath(__file__))
CATALOG = os.path.join(HERE, 'memhack_api.json')
RX_FUNC = re.compile(r'^[ \t]*(?:constant[ \t]+)?function[ \t]+(\w+)[ \t]+takes[ \t]+(.*?)[ \t]+returns[ \t]+(\w+)')
TABLE_NAME = 'KK_mh_ht'
FRAME_KEY = 7

LIBRARIES = (
    ('MemHackAPI (Unryze, 1.24e-1.28f)',
     ('UnlockMemory', 'UnlockMemEx', 'ReadRealMemory', 'WriteRealMemory', 'GetBytecodeAddress', 'InitBytecode',
      'GetJassTable', 'CreateJassNativeHook', 'ExecuteBytecode', 'AllocateExecutableMemory', 'ChangeOffsetProtection',
      'GetMemoryArrayAddress', 'TypecastMemoryArray'),
     ('MemHackTable', 'pGameDLL', 'PatchVersion')),
    ('Memory Hack (1.26a/1.27a: leandrotp, DracoL1ch; the core MemHackAPI grew from)',
     ('ReadMemory', 'WriteMemory', 'ReadRealMemory', 'GetArrayAddress', 'TypecastArray', 'NewGlobal', 'SetGlobal',
      'UnlockMemory', 'GetBytecodeAddress', 'TypecastByteCode'),
     ('l__bytecode', 'l__Array', 'pbytecode')),
)

F = 'KKMH_f(%s)'
FP = 'KKMH_fp(%s)'
FID = 'KKMH_fid(%s)'
D = ' * bj_DEGTORAD'


def _q(i):
    return F % '{%d}' % i


TRANSLATIONS = {
    'GetFrameByName': (['string', 'integer'], 'integer', ['return ' + FID % 'BlzGetFrameByName({0}, {1})']),
    'GetFrameTextByName': (['string', 'integer'], 'string', ['return BlzFrameGetText(BlzGetFrameByName({0}, {1}))']),
    'GetTooltipUberFrame': ([], 'integer', ['return ' + FID % 'BlzGetOriginFrame(ORIGIN_FRAME_UBERTOOLTIP, 0)']),
    'CreateFrame': (
        ['string', 'integer', 'integer'],
        'integer',
        ['return ' + FID % ('BlzCreateFrame({0}, %s, 0, {2})' % (FP % '{1}'))],
    ),
    'LoadTOCFile': (['string'], 'integer', ['if BlzLoadTOCFile({0}) then', '    return 1', 'endif', 'return 0']),
    'HideFrame': (['integer'], 'integer', ['call BlzFrameSetVisible(%s, false)' % _q(0), 'return {0}']),
    'ShowFrame': (['integer'], 'integer', ['call BlzFrameSetVisible(%s, true)' % _q(0), 'return {0}']),
    'SetFrameAlpha': (['integer', 'integer'], 'integer', ['call BlzFrameSetAlpha(%s, {1})' % _q(0), 'return {0}']),
    'GetFrameAlpha': (['integer'], 'integer', ['return BlzFrameGetAlpha(%s)' % _q(0)]),
    'SetFrameTooltip': (
        ['integer', 'integer'],
        'integer',
        ['call BlzFrameSetTooltip(%s, %s)' % (_q(0), _q(1)), 'return {0}'],
    ),
    'SetFrameFocus': (['integer', 'boolean'], 'integer', ['call BlzFrameSetFocus(%s, {1})' % _q(0), 'return {0}']),
    'SetFrameCageMouse': (['integer', 'boolean'], 'integer', ['call BlzFrameCageMouse(%s, {1})' % _q(0), 'return {0}']),
    'SetFrameAbsolutePoint': (
        ['integer', 'integer', 'real', 'real'],
        'integer',
        ['call BlzFrameSetAbsPoint(%s, ConvertFramePointType({1}), {2}, {3})' % _q(0), 'return {0}'],
    ),
    'SetFramePoint': (
        ['integer', 'integer', 'integer', 'integer', 'real', 'real'],
        'integer',
        [
            'call BlzFrameSetPoint(%s, ConvertFramePointType({1}), %s, ConvertFramePointType({3}), {4}, {5})'
            % (_q(0), FP % '{2}'),
            'return {0}',
        ],
    ),
    'SetUIFramePoint': (
        ['integer', 'integer', 'integer', 'integer', 'real', 'real'],
        'integer',
        [
            'call BlzFrameSetPoint(%s, ConvertFramePointType({1}), %s, ConvertFramePointType({3}), {4}, '
            '{5})' % (_q(0), FP % '{2}'),
            'return {0}',
        ],
    ),
    'ClearFrameAllPoints': (['integer'], 'integer', ['call BlzFrameClearAllPoints(%s)' % _q(0), 'return {0}']),
    'SetFrameAllPoints': (
        ['integer', 'integer'],
        'integer',
        ['call BlzFrameSetAllPoints(%s, %s)' % (_q(0), FP % '{1}'), 'return {0}'],
    ),
    'SetFrameWidth': (
        ['integer', 'real'],
        'integer',
        ['call BlzFrameSetSize(%s, {1}, BlzFrameGetHeight(%s))' % (_q(0), _q(0)), 'return {0}'],
    ),
    'SetFrameHeight': (
        ['integer', 'real'],
        'integer',
        ['call BlzFrameSetSize(%s, BlzFrameGetWidth(%s), {1})' % (_q(0), _q(0)), 'return {0}'],
    ),
    'SetFrameSize': (
        ['integer', 'real', 'real'],
        'integer',
        ['call BlzFrameSetSize(%s, {1}, {2})' % _q(0), 'return {0}'],
    ),
    'GetFrameWidth': (['integer'], 'real', ['return BlzFrameGetWidth(%s)' % _q(0)]),
    'GetFrameHeight': (['integer'], 'real', ['return BlzFrameGetHeight(%s)' % _q(0)]),
    'SetFrameScale': (['integer', 'real'], 'integer', ['call BlzFrameSetScale(%s, {1})' % _q(0), 'return {0}']),
    'SetLayoutFrameScale': (['integer', 'real'], 'integer', ['call BlzFrameSetScale(%s, {1})' % _q(0), 'return {0}']),
    'SetFrameVertexColour': (
        ['integer', 'integer'],
        'integer',
        ['call BlzFrameSetVertexColor(%s, {1})' % _q(0), 'return {0}'],
    ),
    'SetFrameVertexColourEx': (
        ['integer', 'integer', 'integer', 'integer', 'integer'],
        'integer',
        ['call BlzFrameSetVertexColor(%s, BlzConvertColor({1}, {2}, {4}, {3}))' % _q(0), 'return {0}'],
    ),
    'SetFrameTextColour': (
        ['integer', 'integer'],
        'integer',
        ['call BlzFrameSetTextColor(%s, {1})' % _q(0), 'return {0}'],
    ),
    'SetFrameTextColourEx': (
        ['integer', 'integer', 'integer', 'integer', 'integer'],
        'integer',
        ['call BlzFrameSetTextColor(%s, BlzConvertColor({1}, {2}, {4}, {3}))' % _q(0), 'return {0}'],
    ),
    'DestroyFrame': (['integer'], 'integer', ['call BlzDestroyFrame(%s)' % _q(0), 'return 0']),
    'IsFrameEnabled': (['integer'], 'boolean', ['return BlzFrameGetEnable(%s)' % _q(0)]),
    'EnableFrame': (['integer'], 'integer', ['call BlzFrameSetEnable(%s, true)' % _q(0), 'return {0}']),
    'DisableFrame': (['integer'], 'integer', ['call BlzFrameSetEnable(%s, false)' % _q(0), 'return {0}']),
    'ClickFrame': (['integer'], 'integer', ['call BlzFrameClick(%s)' % _q(0), 'return {0}']),
    'SetFrameModel': (
        ['integer', 'string', 'integer', 'boolean'],
        'integer',
        ['call BlzFrameSetModel(%s, {1}, {2})' % _q(0), 'return {0}'],
    ),
    'SetFrameTexture': (
        ['integer', 'string', 'boolean'],
        'integer',
        ['call BlzFrameSetTexture(%s, {1}, 0, {2})' % _q(0), 'return {0}'],
    ),
    'GetFrameParent': (['integer'], 'integer', ['return ' + FID % ('BlzFrameGetParent(%s)' % _q(0))]),
    'SetFrameParent': (
        ['integer', 'integer'],
        'integer',
        ['call BlzFrameSetParent(%s, %s)' % (_q(0), FP % '{1}'), 'return {0}'],
    ),
    'GetFrameName': (['integer'], 'string', ['return BlzFrameGetName(%s)' % _q(0)]),
    'GetFrameValue': (['integer'], 'real', ['return BlzFrameGetValue(%s)' % _q(0)]),
    'SetFrameValue': (['integer', 'real'], 'integer', ['call BlzFrameSetValue(%s, {1})' % _q(0), 'return {0}']),
    'SetFrameMinMaxValue': (
        ['integer', 'real', 'real'],
        'integer',
        ['call BlzFrameSetMinMaxValue(%s, {1}, {2})' % _q(0), 'return {0}'],
    ),
    'SetFrameStepValue': (['integer', 'real'], 'nothing', ['call BlzFrameSetStepSize(%s, {1})' % _q(0)]),
    'SetFrameFont': (
        ['integer', 'string', 'real', 'integer'],
        'integer',
        ['call BlzFrameSetFont(%s, {1}, {2}, {3})' % _q(0), 'return {0}'],
    ),
    'SetLayerFont': (
        ['integer', 'string', 'real', 'integer'],
        'integer',
        ['call BlzFrameSetFont(%s, {1}, {2}, {3})' % _q(0), 'return {0}'],
    ),
    'GetFrameTextMaxLength': (['integer'], 'integer', ['return BlzFrameGetTextSizeLimit(%s)' % _q(0)]),
    'SetFrameMaxTextLength': (['integer', 'integer'], 'nothing', ['call BlzFrameSetTextSizeLimit(%s, {1})' % _q(0)]),
    'GetFrameText': (['integer'], 'string', ['return BlzFrameGetText(%s)' % _q(0)]),
    'SetFrameText': (['integer', 'string'], 'integer', ['call BlzFrameSetText(%s, {1})' % _q(0), 'return {0}']),
    'HideUI': ([], 'nothing', ['call BlzHideOriginFrames(true)']),
    'ShowUI': ([], 'nothing', ['call BlzHideOriginFrames(false)']),
    'HideMiniMap': ([], 'nothing', ['call BlzFrameSetVisible(BlzGetOriginFrame(ORIGIN_FRAME_MINIMAP, 0), false)']),
    'ShowMiniMap': ([], 'nothing', ['call BlzFrameSetVisible(BlzGetOriginFrame(ORIGIN_FRAME_MINIMAP, 0), true)']),
    'HideBlackBorders': (
        [],
        'nothing',
        [
            'call BlzFrameSetAllPoints(BlzGetOriginFrame(ORIGIN_FRAME_WORLD_FRAME, 0), '
            'BlzGetOriginFrame(ORIGIN_FRAME_GAME_UI, 0))',
            'call BlzFrameSetVisible(BlzGetFrameByName("ConsoleUIBackdrop", 0), false)',
        ],
    ),
    'GetEffectX': (['effect'], 'real', ['return BlzGetLocalSpecialEffectX({0})']),
    'GetEffectY': (['effect'], 'real', ['return BlzGetLocalSpecialEffectY({0})']),
    'GetEffectZ': (['effect'], 'real', ['return BlzGetLocalSpecialEffectZ({0})']),
    'SetEffectX': (['effect', 'real'], 'nothing', ['call BlzSetSpecialEffectX({0}, {1})']),
    'SetEffectY': (['effect', 'real'], 'nothing', ['call BlzSetSpecialEffectY({0}, {1})']),
    'SetEffectZ': (['effect', 'real'], 'nothing', ['call BlzSetSpecialEffectZ({0}, {1})']),
    'SetEffectPosition': (
        ['effect', 'real', 'real', 'real'],
        'nothing',
        ['call BlzSetSpecialEffectPosition({0}, {1}, {2}, {3})'],
    ),
    'SetEffectTimeScale': (['effect', 'real'], 'nothing', ['call BlzSetSpecialEffectTimeScale({0}, {1})']),
    'GetEffectScale': (['effect'], 'real', ['return BlzGetSpecialEffectScale({0})']),
    'SetEffectScale': (['effect', 'real'], 'nothing', ['call BlzSetSpecialEffectScale({0}, {1})']),
    'SetEffectScaleEx': (
        ['effect', 'real', 'real', 'real'],
        'nothing',
        ['call BlzSetSpecialEffectMatrixScale({0}, {1}, {2}, {3})'],
    ),
    'SetEffectRoll': (['effect', 'real'], 'nothing', ['call BlzSetSpecialEffectRoll({0}, {1}%s)' % D]),
    'SetEffectPitch': (['effect', 'real'], 'nothing', ['call BlzSetSpecialEffectPitch({0}, {1}%s)' % D]),
    'SetEffectYaw': (['effect', 'real'], 'nothing', ['call BlzSetSpecialEffectYaw({0}, {1}%s)' % D]),
    'SetEffectFacing': (['effect', 'real'], 'nothing', ['call BlzSetSpecialEffectYaw({0}, {1}%s)' % D]),
    'SetEffectOrientation': (
        ['effect', 'real', 'real', 'real'],
        'nothing',
        ['call BlzSetSpecialEffectOrientation({0}, {1}%s, {2}%s, {3}%s)' % (D, D, D)],
    ),
    'SetEffectSpaceRotation': (
        ['effect', 'real', 'real', 'real'],
        'nothing',
        ['call BlzSetSpecialEffectOrientation({0}, {1}%s, {2}%s, {3}%s)' % (D, D, D)],
    ),
    'ResetEffectMatrix': (['effect'], 'nothing', ['call BlzResetSpecialEffectMatrix({0})']),
    'SetEffectAlpha': (['effect', 'integer'], 'nothing', ['call BlzSetSpecialEffectAlpha({0}, {1})']),
    'SetEffectColourEx': (
        ['effect', 'integer', 'integer', 'integer', 'integer'],
        'nothing',
        ['call BlzSetSpecialEffectColor({0}, {1}, {2}, {3})', 'call BlzSetSpecialEffectAlpha({0}, {4})'],
    ),
    'SetEffectVertexColour': (
        ['effect', 'integer', 'integer', 'integer', 'integer'],
        'nothing',
        ['call BlzSetSpecialEffectColor({0}, {1}, {2}, {3})', 'call BlzSetSpecialEffectAlpha({0}, {4})'],
    ),
    'SetEffectColour': (
        ['effect', 'integer'],
        'nothing',
        [
            'local integer a = BlzBitAnd({1}, 0x7F000000) / 0x1000000',
            'if {1} < 0 then',
            '    set a = a + 128',
            'endif',
            'call BlzSetSpecialEffectColor({0}, BlzBitAnd({1}, 0xFF0000) / 0x10000, BlzBitAnd({1}, 0xFF00) / 0x100, '
            'BlzBitAnd({1}, 0xFF))',
            'call BlzSetSpecialEffectAlpha({0}, a)',
        ],
    ),
    'GetUnitBaseDamage': (['unit'], 'integer', ['return BlzGetUnitBaseDamage({0}, 0)']),
    'SetUnitBaseDamage': (['unit', 'integer'], 'nothing', ['call BlzSetUnitBaseDamage({0}, {1}, 0)']),
    'SetUnitMaxMana': (['unit', 'real'], 'nothing', ['call BlzSetUnitMaxMana({0}, R2I({1}))']),
    'SetUnitMaxLife': (['unit', 'real'], 'nothing', ['call BlzSetUnitMaxHP({0}, R2I({1}))']),
    'SetUnitLifeRegen': (
        ['unit', 'real'],
        'nothing',
        ['call BlzSetUnitRealField({0}, UNIT_RF_HIT_POINTS_REGENERATION_RATE, {1})'],
    ),
    'SetUnitManaRegen': (
        ['unit', 'real'],
        'nothing',
        ['call BlzSetUnitRealField({0}, UNIT_RF_MANA_REGENERATION, {1})'],
    ),
    'GetUnitCollisionSize': (['unit'], 'real', ['return BlzGetUnitCollisionSize({0})']),
    'IsUnitInvulnerable': (['unit'], 'boolean', ['return BlzIsUnitInvulnerable({0})']),
    'GetUnitAbilityByIndex': (['unit', 'integer'], 'ability', ['return BlzGetUnitAbilityByIndex({0}, {1})']),
    'GetItemAbilityByIndex': (['item', 'integer'], 'ability', ['return BlzGetItemAbilityByIndex({0}, {1})']),
    'GetUnitAbilityManaCost': (
        ['unit', 'integer', 'integer'],
        'integer',
        ['return BlzGetUnitAbilityManaCost({0}, {1}, {2})'],
    ),
    'SetUnitAbilityManaCost': (
        ['unit', 'integer', 'integer', 'integer'],
        'nothing',
        ['call BlzSetUnitAbilityManaCost({0}, {1}, {2}, {3})'],
    ),
    'StartUnitAbilityCooldown': (
        ['unit', 'integer', 'real'],
        'nothing',
        ['call BlzStartUnitAbilityCooldown({0}, {1}, {2})'],
    ),
    'GetUnitAbilityCurrentCooldown': (
        ['unit', 'integer'],
        'real',
        ['return BlzGetUnitAbilityCooldownRemaining({0}, {1})'],
    ),
    'ResetUnitAbilityCooldown': (['unit', 'integer'], 'nothing', ['call BlzEndUnitAbilityCooldown({0}, {1})']),
    'SetUnitFacingEx': (
        ['unit', 'real', 'boolean'],
        'nothing',
        ['if {2} then', '    call BlzSetUnitFacingEx({0}, {1})', 'else', '    call SetUnitFacing({0}, {1})', 'endif'],
    ),
}


MEMUI_CORE = ('GetGameUI2', 'GetFrameLayout', 'IsFrameLayout', 'SetCLayoutFrameAbsolutePoint',
              'ClearCLayoutFrameAllPoints', 'GetPortraitButton')
MEMUI_NAME = 'MemUI (the memory UI library of the M16 maps, 1.28.5)'
_FH = 'DB_fh({0})'
MEMUI = {
    'GetFrameMouseX': ([], 'real', ['return BlzPixelToFrameX(BlzGetMouseScreenPosX())']),
    'GetFrameMouseY': ([], 'real', ['return BlzPixelToFrameY(BlzGetMouseScreenPosY())']),
    'GetGameWindowWidth': ([], 'real', ['return I2R(BlzGetLocalClientWidth())']),
    'GetGameWindowHeight': ([], 'real', ['return I2R(BlzGetLocalClientHeight())']),
    'GetPortraitButtonUnit': ([], 'unit', ['return DzGetSelectedLeaderUnit()']),
    'GetPortraitButtonUnitId': ([], 'integer', ['return GetUnitTypeId(DzGetSelectedLeaderUnit())']),
    'GetTooltip': ([], 'integer', ['return DzFrameGetTooltip()']),
    'GetUberTooltip': ([], 'integer', ['return DB_origin(ORIGIN_FRAME_UBERTOOLTIP, 0)']),
    'GetFrameLayout': (['integer'], 'integer', ['return {0}']),
    'IsFrameLayout': (['integer'], 'boolean', ['return {0} != 0']),
    'SetCLayoutFrameAbsolutePoint': (['integer', 'integer', 'real', 'real'], 'integer',
                                     ['call DzFrameSetAbsolutePoint({0}, {1}, {2}, {3})', 'return {0}']),
    'SetCLayoutFramePoint': (['integer', 'integer', 'integer', 'integer', 'real', 'real'], 'integer',
                             ['call DzFrameSetPoint({0}, {1}, {2}, {3}, {4}, {5})', 'return {0}']),
    'ClearCLayoutFrameAllPoints': (['integer'], 'integer', ['call DzFrameClearAllPoints({0})', 'return {0}']),
    'ClearSimpleFontsAllPoints': (['integer'], 'integer', ['call DzFrameClearAllPoints({0})', 'return {0}']),
    'SetCLayoutFrameWidth': (['integer', 'real'], 'integer', [
        'if %s != null then' % _FH, '    call BlzFrameSetSize(%s, {1}, BlzFrameGetHeight(%s))' % (_FH, _FH), 'endif',
        'return {0}']),
    'SetCLayoutFrameHeight': (['integer', 'real'], 'integer', [
        'if %s != null then' % _FH, '    call BlzFrameSetSize(%s, BlzFrameGetWidth(%s), {1})' % (_FH, _FH), 'endif',
        'return {0}']),
    'SetFramePriority': (['integer', 'integer'], 'nothing', ['call DzFrameSetPriority({0}, {1})']),
    'GetCFrameByName': (['string', 'integer'], 'integer', ['return DzFrameFindByName({0}, {1})']),
    'ClickCSimpleButton': (['integer', 'integer'], 'integer', ['call DzClickFrame({0})', 'return {0}']),
    'ClickCControl': (['integer', 'integer'], 'integer', ['call DzClickFrame({0})', 'return {0}']),
    'JNGetUnitLifeRegen': (['unit'], 'real', ['return BlzGetUnitRealField({0}, UNIT_RF_HIT_POINTS_REGENERATION_RATE)']),
    'JNGetUnitManaRegen2': (['unit'], 'real', ['return BlzGetUnitRealField({0}, UNIT_RF_MANA_REGENERATION)']),
    'JNSetUnitManaRegen2': (['unit', 'real'], 'nothing',
                            ['call BlzSetUnitRealField({0}, UNIT_RF_MANA_REGENERATION, {1})']),
    'JNGetUnitArmourType': (['unit'], 'integer', ['return BlzGetUnitIntegerField({0}, UNIT_IF_DEFENSE_TYPE)']),
    'JNIsUnitAbilityOnCooldownMem': (['unit', 'integer'], 'boolean',
                                     ['return BlzGetUnitAbilityCooldownRemaining({0}, {1}) > 0.0']),
}
MEMUI_ADDRESSES = {
    0xCB1AF8: 'BlzPixelToFrameX(BlzGetMouseScreenPosX())',
    0xCB1AFC: 'BlzPixelToFrameY(BlzGetMouseScreenPosY())',
    0xD0FAB4: 'I2R(BlzGetLocalClientWidth())',
    0xD0FAB0: 'I2R(BlzGetLocalClientHeight())',
}
MEMUI_VIA = frozenset(('SetFrameAbsolutePoint', 'SetFramePoint', 'ClearFrameAllPoints', 'SetFrameSize',
                       'SetCLayoutFrameSize', 'GetItemMouseX', 'GetItemMouseY'))
MEMUI_GENERAL = frozenset(MEMUI) | MEMUI_VIA | frozenset((
    'GetGameUI2', 'GetPortraitButton', 'GetPortraitButtonHPText', 'GetPortraitButtonManaText', 'FindFrameUnderCursor',
    'FindCLayerUnderCursor2', 'GetInfoBar', 'GetInfoPanelUnitDetail', 'GetBuffBarFrame', 'GetBuffIndicatorLive',
    'GetBuffIndicatorIdLive', 'GetBuffBarText', 'GetBuffIndicator', 'GetBuffIndicatorId', 'GetUISimpleConsole',
    'GetUIPeonBar', 'JN_ConvertHandleId', 'JN_ConvertHandle', 'JN_GetCObjectFromHashGroup', 'JN_GetUnitAttackAbility',
    'JNGetUnitBonusDamage', 'JN_GetCObjectFromHash', 'JN_GetCAgentFromHash', 'JN_GetCAgentFromHashGroup',
    'JN_GetUnitAbilityPtr', 'JNGetUnitAbilityDisabled', 'JNGetUnitAbilityDisabledEx', 'GetUIMessage', 'GetUITopMessage',
    'GetIdlePeonButton', 'GetSimpleConsoleTextureByIndex', 'GetUIInfoBar', 'GetInventoryCoverTexture',
    'SetCSimpleButtonStateTexture', 'SetSpriteModeal', 'SetSpriteFrameScale', 'GetUITimeOfDayIndicator',
    'GetTimeOfDayIndicatorSpriteUber', 'SetTimeOfDayIndicatorModel', 'SetCSimpleTextureTexture', 'SetConsoleRaceUI',
    'SetIdlePeonButtonTexture'))
RX_MEMUI_GLOBAL = re.compile(r'^[ \t]*set[ \t]+(\w+)[ \t]*=[ \t]*\w+[ \t]*\+[ \t]*(?:\$|0[xX])([0-9A-Fa-f]+)[ \t]*$')


def detect_memui(body_text, defs=None):
    defs = _defined(body_text) if defs is None else defs
    if not re.search(r'\bnative[ \t]+JNMemoryGetInteger\b', body_text):
        return []
    sig = {'GetGameUI2': (['integer', 'integer'], 'integer'), 'GetFrameLayout': (['integer'], 'integer'),
           'IsFrameLayout': (['integer'], 'boolean'),
           'SetCLayoutFrameAbsolutePoint': (['integer', 'integer', 'real', 'real'], 'integer'),
           'ClearCLayoutFrameAllPoints': (['integer'], 'integer'), 'GetPortraitButton': ([], 'integer')}
    hits = [n for n in MEMUI_CORE if defs.get(n) == sig[n]]
    return hits if len(hits) >= 3 else []


def _memui_addresses(line_list):
    out = {}
    for line in line_list:
        m = RX_MEMUI_GLOBAL.match(line)
        if m and int(m.group(2), 16) in MEMUI_ADDRESSES:
            out[m.group(1)] = MEMUI_ADDRESSES[int(m.group(2), 16)]
    return out


def apply_memui(line_list, ref, ref_text=''):
    info = {'translated': [], 'readings': 0}
    body_text = '\n'.join(line_list)
    if not detect_memui(body_text):
        return info
    tgt = []
    i = 0
    while i < len(line_list):
        m = RX_FUNC.match(line_list[i])
        if m and m.group(1) in MEMUI:
            j = i + 1
            while j < len(line_list) and not re.match(r'^[ \t]*endfunction\b', line_list[j]):
                j += 1
            ps = m.group(2).strip()
            params = [] if ps == 'nothing' else [p.split() for p in ps.split(',')]
            types = [p[-2] for p in params if len(p) >= 2]
            expected_len, ret, body = MEMUI[m.group(1)]
            if types == expected_len and ret == m.group(3):
                new = [line.format(*[p[-1] for p in params]) for line in body]
                natives = set(re.findall(r'\b(Blz\w+)\(', '\n'.join(new)))
                consts = set(re.findall(r'\b([A-Z][A-Z0-9]*_[A-Z0-9_]+)\b', '\n'.join(new)))
                if all(n in ref.natives for n in natives) and all(
                        re.search(r'\b%s\b' % c, ref_text) for c in consts if ref_text):
                    tgt.append((i, j, m.group(1), new))
            i = j
        i += 1
    for i, j, fname, new in reversed(tgt):
        indent_trim = re.match(r'^([ \t]*)', line_list[i]).group(1) + '    '
        line_list[i + 1:j] = [indent_trim + line for line in new]
        info['translated'].append(fname)
    info['translated'].reverse()
    end = _memui_addresses(line_list)
    if end:
        name_list = '|'.join(map(re.escape, sorted(end, key=len, reverse=True)))
        rx = re.compile(
            r'\bJNMemoryGetReal[ \t]*\([ \t]*(?:\([ \t]*(%s)[ \t]*\)|(%s))[ \t]*\)' % (name_list, name_list)
        )
        for k, line in enumerate(line_list):
            if 'JNMemoryGetReal' in line and rx.search(line):
                new, n = rx.subn(lambda mm: end[mm.group(1) or mm.group(2)], line)
                line_list[k] = new
                info['readings'] += n
    return info


def helpers(chosen):
    lazy_init = ['    if %s == null then' % TABLE_NAME, '        set %s = InitHashtable()' % TABLE_NAME, '    endif']
    out = []
    if 'KKMH_f' in chosen:
        out += ['function KKMH_f takes integer i returns framehandle'] + lazy_init + [
            '    return LoadFrameHandle(%s, %d, i)' % (TABLE_NAME, FRAME_KEY), 'endfunction']
    if 'KKMH_fp' in chosen:
        out += ['function KKMH_fp takes integer i returns framehandle', '    if i == 0 then',
                '        return BlzGetOriginFrame(ORIGIN_FRAME_GAME_UI, 0)', '    endif'] + lazy_init + [
            '    return LoadFrameHandle(%s, %d, i)' % (TABLE_NAME, FRAME_KEY), 'endfunction']
    if 'KKMH_fid' in chosen:
        out += (
            [
                'function KKMH_fid takes framehandle f returns integer',
                '    if f == null then',
                '        return 0',
                '    endif',
            ]
            + lazy_init
            + [
                '    call SaveFrameHandle(%s, %d, GetHandleId(f), f)' % (TABLE_NAME, FRAME_KEY),
                '    return GetHandleId(f)',
                'endfunction',
            ]
        )
    return out


_CAT = {}


def catalog():
    if 'c' not in _CAT:
        _CAT['c'] = json.load(open(CATALOG, encoding='utf-8')) if os.path.isfile(CATALOG) else {}
    return _CAT['c']


def _defined(body_text):
    out = {}
    for m in re.finditer(
        r'(?m)^[ \t]*(?:constant[ \t]+)?function[ \t]+(\w+)[ \t]+takes[ \t]+(.*?)[ \t]+returns[ \t]+(\w+)', body_text
    ):
        ps = m.group(2).strip()
        out[m.group(1)] = ([] if ps == 'nothing' else [p.split()[-2] for p in ps.split(',') if len(p.split()) >= 2],
                           m.group(3))
    return out


def detect_libraries(body_text, defs=None):
    defs = _defined(body_text) if defs is None else defs
    libs = {}
    for fname, core, globals_block in LIBRARIES:
        hits = [n for n in core if n in defs]
        if not hits:
            continue
        marks = [
            g for g in globals_block if re.search(r'(?m)^[ \t]*\w+[ \t]+(?:array[ \t]+)?%s\b' % re.escape(g), body_text)
        ]
        if len(hits) >= 3 or marks:
            libs[fname] = hits + marks
            if marks:
                break
    return libs


def detect_memhack(body_text):
    defs = _defined(body_text)
    cat = catalog()
    in_api = sorted(n for n, (ps, r) in defs.items() if n in cat and cat[n][0] == ps and cat[n][1] == r)
    libs = detect_libraries(body_text, defs)
    out = {'libraries': libs, 'api': len(in_api), 'calls': {}, 'translated': [], 'no_equivalent': []}
    memui = detect_memui(body_text, defs)
    if memui:
        libs[MEMUI_NAME] = memui
        out['memui'] = True
        in_api = sorted(set(in_api) | set(n for n in MEMUI if n in defs) |
                        set(n for n in defs if n in MEMUI_GENERAL))
        out['api'] = len(in_api)
    if not libs and len(in_api) < 5:
        return out
    api = set(in_api)
    inside = None
    rx = re.compile(r'\b(%s)\b' % '|'.join(map(re.escape, sorted(api, key=len, reverse=True)))) if api else None
    for ln in body_text.split('\n'):
        m = RX_FUNC.match(ln)
        if m:
            inside = m.group(1)
            continue
        if inside is None or inside in api or rx is None or inside.startswith(('Init_', 'InitTrig_')) or \
                '___' in inside:
            continue
        nameless = re.sub(r'"(?:[^"\\]|\\.)*"|//.*', '', ln)
        for c in rx.findall(nameless):
            out['calls'][c] = out['calls'].get(c, 0) + 1
    for n in sorted(out['calls']):
        ok = n in TRANSLATIONS or (memui and (n in MEMUI or n in MEMUI_VIA))
        (out['translated'] if ok else out['no_equivalent']).append(n)
    return out


def warning(detail):
    if not detail or not detail.get('libraries'):
        return None
    libs = '; '.join(sorted(detail['libraries']))
    pieces = ['the map uses a memory hack of patch 1.24-1.28 (%s): %d function(s) of the %s' % (
        libs, detail['api'], 'library' if detail.get('memui') else 'MemHackAPI')]
    if detail['translated']:
        pieces.append('%d the map calls now use the Reforged natives (%s)' % (
            len(detail['translated']), ', '.join(detail['translated'][:12])))
    if detail['no_equivalent']:
        pieces.append('%d the map calls have no Reforged equivalent and do nothing (%s)' % (
            len(detail['no_equivalent']), ', '.join(detail['no_equivalent'][:12])))
    if not detail['calls']:
        pieces.append('the memory exploit itself does not exist in Reforged: what it changed in the game does not '
                      'happen')
    return '; '.join(pieces) + '; check those features in game'


def applies(line_list, ref, ref_text=''):
    info = {'translated': [], 'helpers': set()}
    cat = catalog()
    if not cat:
        return info
    body_text = '\n'.join(line_list)
    if not detect_libraries(body_text):
        return info
    tgt = []
    i = 0
    while i < len(line_list):
        m = RX_FUNC.match(line_list[i])
        if m and m.group(1) in TRANSLATIONS and m.group(1) in cat:
            j = i + 1
            while j < len(line_list) and not re.match(r'^[ \t]*endfunction\b', line_list[j]):
                j += 1
            ps = m.group(2).strip()
            params = [] if ps == 'nothing' else [p.split() for p in ps.split(',')]
            types = [p[-2] for p in params if len(p) >= 2]
            expected_len, ret, body = TRANSLATIONS[m.group(1)]
            if types == expected_len == cat[m.group(1)][0] and ret == m.group(3) == cat[m.group(1)][1]:
                new = [line.format(*[p[-1] for p in params]) for line in body]
                natives = set(re.findall(r'\b(Blz\w+|Convert\w+)\(', '\n'.join(new)))
                consts = set(re.findall(r'\b([A-Z][A-Z0-9]*_[A-Z0-9_]+)\b', '\n'.join(new))) - {'KK_mh_ht'}
                if all(n in ref.natives for n in natives) and all(
                        re.search(r'\b%s\b' % c, ref_text) for c in consts if ref_text):
                    tgt.append((i, j, m.group(1), new))
            i = j
        i += 1
    for i, j, fname, new in reversed(tgt):
        indent_trim = re.match(r'^([ \t]*)', line_list[i]).group(1) + '    '
        line_list[i + 1:j] = [indent_trim + line for line in new]
        info['translated'].append(fname)
        for a in ('KKMH_fid', 'KKMH_fp', 'KKMH_f'):
            if any(a + '(' in line for line in new):
                info['helpers'].add(a)
    info['translated'].reverse()
    return info


def table():
    out = []
    for n, (ps, r, lib, file_) in sorted(catalog().items(), key=lambda kv: (kv[1][3], kv[0])):
        eq = '; '.join(TRANSLATIONS[n][2]) if n in TRANSLATIONS else ''
        out.append((n, '%s (%s)' % (lib, file_), '%s -> %s' % (', '.join(ps) or 'nothing', r), eq))
    return out
