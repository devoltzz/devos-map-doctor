# Lists the script literals and the text of a map, the base of the translation export.
import re


HANGUL = re.compile(
    '[' + chr(0xAC00) + '-' + chr(0xD7A3) + chr(0x1100) + '-' + chr(0x11FF) + chr(0x3130) + '-' + chr(0x318F) + ']'
)
CJK = re.compile('[' + chr(0x4E00) + '-' + chr(0x9FFF) + chr(0x3400) + '-' + chr(0x4DBF) + ']')
JAPANESE = re.compile('[' + chr(0x3040) + '-' + chr(0x30FF) + ']')


_RX_LITERAL = re.compile(r'"((?:[^"\\]|\\[\s\S]?)*)"?|//')


def literals(line, _matches=_RX_LITERAL.finditer):
    if '"' not in line:
        return []
    if '//' not in line:
        return [(m.start(), m.group(1)) for m in _matches(line)]
    out = []
    for m in _matches(line):
        s = m.group(1)
        if s is None:
            break
        out.append((m.start(), s))
    return out


def classify(line, pos, lit):
    before = line[max(0, pos - 40):pos]
    after = line[pos + len(lit) + 2:pos + len(lit) + 12]
    if re.search(r'[=!]=\s*$', before) or after.lstrip().startswith(('==', '!=')):
        return 'comparison'
    if re.search(r'TriggerRegisterPlayerChatEvent\s*\([^()"]*(?:\([^()"]*\)[^()"]*)*$', line[:pos]):
        return 'chat'
    if 'StringHash(' in before or 'SubString(' in before or 'StringLength(' in before:
        return 'hash/substring'
    if 'GetLocalizedString' in before:
        return 'localizada'
    for fn in (
        'DisplayTextToPlayer',
        'DisplayTimedTextToPlayer',
        'BlzFrameSetText',
        'DzFrameSetText',
        'CreateTextTag',
        'SetTextTagText',
        'BlzSetAbility',
        'BlzSetUnitName',
        'BlzSetItem',
        'DialogSetMessage',
        'DialogAddButton',
        'QuestSet',
        'SetPlayerName',
        'MultiboardSet',
        'CreateQuest',
        'ForceUIKey',
    ):
        if fn in before:
            return 'exibicao'
    return 'other'
