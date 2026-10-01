# Applies translated texts to the script and the data files of a map.
import os
import re
from collections import Counter


HERE = os.path.dirname(os.path.abspath(__file__))
TR = os.environ.get('TR_DIR') or os.path.join(HERE, 'tr')
import kr_inventory as ki
import tr_extract as tx


ALL_OS_ARGUMENTS = object()

_KINDS_HASHTABLE = (
    'Str', 'Integer', 'Real', 'Boolean', 'UnitHandle', 'ItemHandle', 'AbilityHandle',
    'TimerHandle', 'TriggerHandle', 'TriggerConditionHandle', 'TriggerActionHandle',
    'TriggerEventHandle', 'ForceHandle', 'GroupHandle', 'LocationHandle', 'RectHandle',
    'BooleanExprHandle', 'SoundHandle', 'EffectHandle', 'UnitPoolHandle', 'ItemPoolHandle',
    'QuestHandle', 'QuestItemHandle', 'DefeatConditionHandle', 'TimerDialogHandle',
    'LeaderboardHandle', 'LeaderboardItemHandle', 'TrackableHandle', 'DialogHandle',
    'ButtonHandle', 'TextTagHandle', 'LightningHandle', 'ImageHandle', 'UbersplatHandle',
    'RegionHandle', 'FogStateHandle', 'FogModifierHandle', 'AgentHandle', 'HashtableHandle',
)
ARGUMENTS_KEY = {}
for _t in _KINDS_HASHTABLE:
    for _p in ('Save', 'Load', 'HaveSaved', 'RemoveSaved'):
        ARGUMENTS_KEY[_p + _t] = frozenset((1, 2))
ARGUMENTS_KEY['FlushChildHashtable'] = frozenset((1,))
ARGUMENTS_KEY['FlushParentHashtable'] = frozenset()
for _f in ('StoreString', 'StoreInteger', 'StoreReal', 'StoreBoolean',
           'GetStoredString', 'GetStoredInteger', 'GetStoredReal', 'GetStoredBoolean',
           'HaveStoredString', 'HaveStoredInteger', 'HaveStoredReal', 'HaveStoredBoolean',
           'FlushStoredString', 'FlushStoredInteger', 'FlushStoredReal', 'FlushStoredBoolean',
           'FlushStoredMission',
           'YDWESaveStringByString', 'YDWESaveStringByInteger',
           'YDWEGetStringByString', 'YDWEGetStringByInteger',
           'YDWEHaveSavedIntegerByString', 'YDWEHaveSavedIntegerByInteger',
           'YDWEFlushStoredIntegerByString', 'YDWEFlushStoredIntegerByInteger'):
    ARGUMENTS_KEY[_f] = frozenset((0, 1))
ARGUMENTS_KEY['YDWEFlushMissionByString'] = frozenset((0,))
ARGUMENTS_KEY['YDWEFlushMissionByInteger'] = frozenset((0,))
PREFIXES_KEY = ('DzAPI_Map_', 'JNObject', 'JNDaily', 'JNRPG', 'JNSetLog', 'JNMapServerLog', 'JNPublicMapServerLog')
PREFIXES_KEY_ARGS = {
    'DzSync': frozenset((0,)),
    'DzTriggerRegisterSyncData': frozenset((1,)),
}
NAMES_DE_FRAME = frozenset((
    'DzCreateFrameByTagName', 'DzCreateFrame', 'BlzCreateFrame', 'BlzCreateFrameByType',
    'BlzCreateSimpleFrame', 'BlzGetFrameByName', 'BlzFrameGetName', 'BlzFrameFindByName',
    'DzFrameFindByName', 'DzFrameFindByNameEx',
))
for _f in NAMES_DE_FRAME:
    ARGUMENTS_KEY[_f] = ALL_OS_ARGUMENTS
FUNCTIONS_CAUTION = ('SubString', 'SubStringBJ', 'StringLength', 'StringLengthBJ')


def call_envolvente(before):
    max_depth = virgulas = 0
    i = len(before) - 1
    while i >= 0:
        c = before[i]
        if c == ')':
            max_depth += 1
        elif c == '(':
            if max_depth == 0:
                j = i - 1
                while j >= 0 and (before[j].isalnum() or before[j] in '_$'):
                    j -= 1
                fname = before[j + 1:i]
                if fname:
                    return fname, virgulas
            else:
                max_depth -= 1
        elif c == ',' and max_depth == 0:
            virgulas += 1
        i -= 1
    return None, None


def classifica_occurrence(ln, pos, lit, caution_como_screen=False):
    before = ln[max(0, pos - 400):pos]
    after_diag = ln[pos + len(lit) + 2:pos + len(lit) + 13]
    if re.search(r'[=!]=\s*$', before) or after_diag.lstrip().startswith(('==', '!=')):
        return 'prudencia:comparacao'
    fn, idx = call_envolvente(before)
    if fn is None:
        return 'screen:no call (assignment/list)'
    if fn == 'StringHash':
        return 'chave:StringHash'
    if fn in FUNCTIONS_CAUTION:
        return 'prudencia:' + fn
    if fn in ARGUMENTS_KEY:
        keys = ARGUMENTS_KEY[fn]
        if keys is ALL_OS_ARGUMENTS or idx in keys:
            return 'chave:' + fn
        return 'tela:' + fn
    for p in PREFIXES_KEY:
        if fn.startswith(p):
            return 'chave:' + fn
    for p, idxs in PREFIXES_KEY_ARGS.items():
        if fn.startswith(p) and idx in idxs:
            return 'chave:' + fn
    return 'tela:' + fn


def apply_por_occurrence_lines(line_list, by_text, caution_como_screen=False, all_entries=None, protected=None):
    all_entries = all_entries or {}
    cats = Counter()
    detail = {}
    n = 0
    inside = tx.lines_protected(line_list, tx.functions_protected(TR) if protected is None else protected)
    for line_no, line in enumerate(line_list):
        lits = ki.literals(line)
        if not lits:
            continue
        if inside and inside[line_no]:
            for pos, lit in lits:
                if lit in by_text:
                    cats['dado:funcao protegida'] += 1
                    detail.setdefault(lit, Counter())['datum'] += 1
            continue
        out, last, changed = [], 0, False
        for pos, lit in lits:
            en = by_text.get(lit)
            if en is None:
                key2 = lit.encode('utf-8', 'surrogateescape').decode('utf-8', 'replace')
                en = by_text.get(key2)
            if en is None:
                continue
            cat = 'todas:decisao explicita' if lit in all_entries else \
                classifica_occurrence(line, pos, lit, caution_como_screen)
            cluster = cat.split(':', 1)[0]
            cats[cat] += 1
            d = detail.setdefault(lit, Counter())
            d[cluster] += 1
            if cluster in ('screen', 'all_entries') or (cluster == 'caution' and caution_como_screen):
                out.append(line[last:pos + 1])
                out.append(en)
                last = pos + 1 + len(lit)
                changed = True
                n += 1
        if changed:
            out.append(line[last:])
            line_list[line_no] = ''.join(out)
    return cats, detail, n


def fix_value(en, entry):
    en = en.replace('"', "'")
    if entry.get('quoted'):
        return '"' + en + '"'
    if ',' in en and not entry.get('comma'):
        return '"' + en + '"'
    return en

