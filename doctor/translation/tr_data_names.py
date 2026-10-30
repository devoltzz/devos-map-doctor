# Finds the object names the script reads as data (GetObjectName as a number or a key, a compared name), which a translation must keep.
import re
import struct


LIT = r'"(?:[^"\\]|\\.)*"'
FN_NAME = r'(?:GetUnitName|GetItemName|GetHeroProperName|GetObjectName)\('
RX_OBJNAME = re.compile(r"GetObjectName\(\s*(-?\d+|'[^']{4}')\s*\)")
RX_COMPARE = [
    re.compile(FN_NAME + r'[^\n]{0,120}?\)\s*\)?\s*(?:==|!=)\s*\(?\s*(' + LIT + ')'),
    re.compile('(' + LIT + r')\s*\)?\s*(?:==|!=)\s*\(?\s*' + FN_NAME),
    re.compile(r'StringHash\(\s*' + FN_NAME + r'[^\n]{0,160}?(?:==|!=)\s*\(?\s*StringHash\(\s*(' + LIT + r')\s*\)'),
]
RX_PREFIX_MATCH = re.compile('(' + LIT + r')\s*\+\s*' + FN_NAME)


DISPLAY_CALLS = (
    'DisplayTextToPlayer',
    'DisplayTimedTextToPlayer',
    'DisplayTextToForce',
    'DisplayTimedTextToForce',
    'DisplayTimedTextFromPlayer',
    'BJDebugMsg',
    'QuestSetTitle',
    'QuestSetDescription',
    'QuestItemSetDescription',
    'CreateQuestBJ',
    'MultiboardSetItemValue',
    'MultiboardSetItemValueBJ',
    'MultiboardSetTitleText',
    'LeaderboardAddItem',
    'LeaderboardAddItemBJ',
    'LeaderboardSetLabel',
    'DialogAddButton',
    'DialogSetMessage',
    'DialogAddButtonBJ',
    'DialogSetMessageBJ',
    'SetTextTagText',
    'SetTextTagTextBJ',
    'CreateTextTagUnitBJ',
    'CreateTextTagLocBJ',
    'BlzFrameSetText',
    'DzFrameSetText',
    'BlzFrameAddText',
    'SetPlayerName',
    'TransmissionFromUnitWithNameBJ',
    'CustomVictoryBJ',
    'CustomDefeatBJ',
)
def _context(script, begin, end_pos):
    max_depth, i = 0, begin - 1
    while i >= 0:
        c = script[i]
        if c == ')':
            max_depth += 1
        elif c == '(':
            if max_depth == 0:
                m = re.search(r'(\w+)\s*$', script[max(0, i - 80):i])
                fname = m.group(1) if m else ''
                if fname in DISPLAY_CALLS:
                    return 'screen'
                if fname:
                    return 'datum'
            else:
                max_depth -= 1
        elif c in '\n=!<>,' and max_depth == 0:
            if c == ',':
                depth2, j = 0, i - 1
                while j >= 0:
                    if script[j] == ')':
                        depth2 += 1
                    elif script[j] == '(':
                        if depth2 == 0:
                            m = re.search(r'(\w+)\s*$', script[max(0, j - 80):j])
                            return 'screen' if m and m.group(1) in DISPLAY_CALLS else 'datum'
                        depth2 -= 1
                    elif script[j] == '\n':
                        break
                    j -= 1
            return 'datum'
        i -= 1
    return 'datum'


def rawcode(s):
    if s.startswith("'"):
        return s[1:-1]
    return struct.pack('>i', int(s)).decode('latin-1')


def body_text(lit):
    return lit[1:-1].replace('\\"', '"').replace('\\\\', '\\')


def measure(script, name_list):
    read_count = sorted(set(rawcode(m.group(1)) for m in RX_OBJNAME.finditer(script)
                            if _context(script, m.start(), m.end()) == 'datum'))
    comparados, prefixes = {}, {}
    for rx in RX_COMPARE:
        for m in rx.finditer(script):
            comparados.setdefault(body_text(m.group(1)), [])
    for m in RX_PREFIX_MATCH.finditer(script):
        prefixes.setdefault(body_text(m.group(1)), [])
    for obj, t in name_list:
        if t in comparados:
            comparados[t].append(obj)
        for p in prefixes:
            if p and t.startswith(p):
                prefixes[p].append(obj)
    return read_count, comparados, prefixes
