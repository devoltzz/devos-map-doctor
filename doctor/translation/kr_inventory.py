# Lists the script literals and the text of a map, the base of the translation export.
import re


HANGUL = re.compile(
    '[' + chr(0xAC00) + '-' + chr(0xD7A3) + chr(0x1100) + '-' + chr(0x11FF) + chr(0x3130) + '-' + chr(0x318F) + ']'
)
CJK = re.compile('[' + chr(0x4E00) + '-' + chr(0x9FFF) + chr(0x3400) + '-' + chr(0x4DBF) + ']')
JAPANESE = re.compile('[' + chr(0x3040) + '-' + chr(0x30FF) + ']')


def literals(line):
    out = []
    i = 0
    n = len(line)
    while i < n:
        c = line[i]
        if c == '/' and i + 1 < n and line[i + 1] == '/':
            break
        if c == '"':
            j = i + 1
            buf = []
            while j < n:
                d = line[j]
                if d == chr(92) and j + 1 < n:
                    buf.append(d + line[j + 1])
                    j += 2
                    continue
                if d == '"':
                    break
                buf.append(d)
                j += 1
            out.append((i, ''.join(buf)))
            i = j + 1
            continue
        i += 1
    return out


def classify(line, pos, lit):
    before = line[max(0, pos - 40):pos]
    after = line[pos + len(lit) + 2:pos + len(lit) + 12]
    if '==' in before[-4:] or after.startswith('==') or '!=' in before[-4:] or after.startswith('!='):
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
