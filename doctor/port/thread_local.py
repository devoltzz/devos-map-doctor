# Finds the threads and the handle-creating calls reached from code that runs on one machine only (they desync).
import re


RX_FUNCTION = re.compile(r'(?m)^[ \t]*function[ \t]+(\w+)[ \t]+takes\b')
RX_CALL = re.compile(r'\b(\w+)[ \t]*\(')
RX_EXEC = re.compile(r'\bExecuteFunc[ \t]*\([ \t]*"(\w+)"')
THREAD = re.compile(r'\b(TriggerEvaluate|TriggerExecute|TriggerExecuteWait|ConditionalTriggerExecute|ExecuteFunc|'
                    r'ForForce|ForGroup|ForGroupBJ|EnumItemsInRect|EnumItemsInRectBJ|EnumDestructablesInRect|'
                    r'EnumDestructablesInRectAll|EnumDestructablesInCircleBJ)[ \t]*\(')
CREATES = re.compile(
    r'\b(CreateTrigger|CreateTimer|CreateGroup|CreateForce|Location|Rect|RectFromLoc|CreateRegion|'
    r'InitHashtable|AddSpecialEffect|AddSpecialEffectLoc|AddSpecialEffectTarget|CreateTextTag|CreateUnit|'
    r'CreateUnitByName|CreateUnitAtLoc|CreateItem|CreateDestructable|BlzCreateFrame|BlzCreateSimpleFrame|'
    r'BlzCreateFrameByType|Condition|Filter|TriggerAddAction|TriggerAddCondition|CreateSound|'
    r'CreateLeaderboard|CreateMultiboard|DialogCreate|DialogAddButton|CreateImage|AddLightning|'
    r'AddLightningEx|CreateFogModifierRect|CreateFogModifierRadius|CreateQuest|CreateTimerDialog|'
    r'GetUnitLoc|GetSpellTargetLoc|GetRectCenter|CreateMinimapIcon|CreateMinimapIconOnUnit|'
    r'TriggerRegister\w+|BlzTriggerRegister\w+|CreateCameraSetup|CreateUnitPool|CreateItemPool|'
    r'AddWeatherEffect|BlzCreateUnitWithSkin|BlzCreateItemWithSkin|CreateTrackable|CreateUbersplat)'
    r'[ \t]*\('
)
RX_LOCAL_BODY = re.compile(r'\bcall[ \t]+(\w+)[ \t]*\(')
RX_COMMENT = re.compile(r'//[^\r\n]*')


def functions(body_text):
    pos = [(m.start(), m.group(1)) for m in RX_FUNCTION.finditer(body_text)]
    out = {}
    for k, (a, fname) in enumerate(pos):
        b = pos[k + 1][0] if k + 1 < len(pos) else len(body_text)
        out[fname] = RX_COMMENT.sub('', body_text[a:b])
    return out


def audit(body_text, creation=False):
    fs = functions(body_text)
    roots = []
    for fname, c in fs.items():
        if fname.startswith('KK_loc_'):
            m = RX_LOCAL_BODY.search(c)
            if m and m.group(1) in fs:
                roots.append((m.group(1), fname))
    file_path = {}
    work_queue = [(r, [loc]) for r, loc in roots]
    while work_queue:
        f, cpath = work_queue.pop(0)
        if f in file_path or f not in fs:
            continue
        file_path[f] = cpath
        c = fs[f]
        next_item = set(m.group(1) for m in RX_CALL.finditer(c))
        next_item |= set(RX_EXEC.findall(c))
        for g in next_item:
            if g in fs and g not in file_path:
                work_queue.append((g, cpath + [f]))
    matches = []
    for f in sorted(file_path):
        ths = sorted(set(m.group(1) for m in THREAD.finditer(fs[f])))
        if creation:
            ths += sorted(set('+' + m.group(1) for m in CREATES.finditer(fs[f])))
        if ths:
            matches.append((f, ths, ' <- '.join([f] + list(reversed(file_path[f])))))
    return matches


def report_data(matches, log=print):
    if not matches:
        log('thread in local code: none (the KK_loc_ bodies run no trigger and no thread)')
        return
    log('thread in LOCAL code (born on one machine only: it desyncs): %d function(s)' % len(matches))
    for f, ths, cpath in matches:
        log('   %-40s %s  [%s]' % (f, ', '.join(ths), cpath[:200]))
