# Applies translated texts to the script and the data files of a map.
import json
import os
import re
from collections import Counter


HERE = os.path.dirname(os.path.abspath(__file__))
TR = os.environ.get('TR_DIR') or os.path.join(HERE, 'tr')
BUILD = os.path.join(TR, 'build')
from doctor.translation import kr_inventory as ki
from doctor.translation import tr_extract as tx


def load_translations():
    tr = {}
    for fn in ('reuso.json', 'glossary.json', 'bulk.json', 'repair.json', 'manual.json'):
        p = os.path.join(TR, fn)
        if os.path.exists(p):
            tr.update(json.load(open(p, encoding='utf-8')))
    return tr


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
FRAME_NAMES = frozenset((
    'DzCreateFrameByTagName', 'DzCreateFrame', 'BlzCreateFrame', 'BlzCreateFrameByType',
    'BlzCreateSimpleFrame', 'BlzGetFrameByName', 'BlzFrameGetName', 'BlzFrameFindByName',
    'DzFrameFindByName', 'DzFrameFindByNameEx',
))
for _f in FRAME_NAMES:
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


def classifica_occurrence(ln, pos, lit, caution_as_screen=False):
    before = ln[max(0, pos - 400):pos]
    after_diag = ln[pos + len(lit) + 2:pos + len(lit) + 13]
    if re.search(r'[=!]=\s*$', before) or after_diag.lstrip().startswith(('==', '!=')):
        return 'caution:comparison'
    fn, idx = call_envolvente(before)
    if fn is None:
        return 'screen:no call (assignment/list)'
    if fn == 'StringHash':
        return 'hash_key:StringHash'
    if fn in FUNCTIONS_CAUTION:
        return 'caution:' + fn
    if fn in ARGUMENTS_KEY:
        keys = ARGUMENTS_KEY[fn]
        if keys is ALL_OS_ARGUMENTS or idx in keys:
            return 'hash_key:' + fn
        return 'screen:' + fn
    for p in PREFIXES_KEY:
        if fn.startswith(p):
            return 'hash_key:' + fn
    for p, idxs in PREFIXES_KEY_ARGS.items():
        if fn.startswith(p) and idx in idxs:
            return 'hash_key:' + fn
    return 'screen:' + fn


def apply_by_occurrence(body_text, by_text, caution_as_screen=False, all_entries=None):
    line_list, sep = tx.line_break(body_text, jass=True)
    cats, detail, n = apply_by_occurrence_lines(line_list, by_text, caution_as_screen, all_entries)
    return sep.join(line_list), cats, detail, n


def apply_by_occurrence_lines(line_list, by_text, caution_as_screen=False, all_entries=None, protected=None):
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
                    cats['datum:protected function'] += 1
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
            cat = 'all_entries:explicit decision' if lit in all_entries else \
                classifica_occurrence(line, pos, lit, caution_as_screen)
            cluster = cat.split(':', 1)[0]
            cats[cat] += 1
            d = detail.setdefault(lit, Counter())
            d[cluster] += 1
            if cluster in ('screen', 'all_entries') or (cluster == 'caution' and caution_as_screen):
                out.append(line[last:pos + 1])
                out.append(en)
                last = pos + 1 + len(lit)
                changed = True
                n += 1
        if changed:
            out.append(line[last:])
            line_list[line_no] = ''.join(out)
    return cats, detail, n


def load_extras():
    p = os.path.join(TR, 'texto_en_extra.json')
    if not os.path.exists(p):
        return {}
    d = json.load(open(p, encoding='utf-8'))
    return dict((k, v) for k, v in d.items() if not k.startswith('_'))


def load_all():
    p = os.path.join(TR, 'texto_en_todas.json')
    if not os.path.exists(p):
        return {}
    d = json.load(open(p, encoding='utf-8'))
    return dict((k, v) for k, v in d.items() if not k.startswith('_'))


def extras_by_id(entries, extras):
    output = {}
    for e in entries:
        if e.get('text') in extras:
            output[e['id']] = extras[e['text']]
    return output


def fix_value(en, entry):
    if '"' not in (entry.get('text') or ''):
        en = en.replace('"', "'")
    if entry.get('quoted'):
        return '"' + en + '"'
    if ',' in en and not entry.get('comma'):
        return '"' + en + '"'
    return en


def apply_txt(root, entries, tr, stats):
    by_file = {}
    for e in entries:
        if e['src'].endswith('.txt') and e['id'] in tr:
            by_file.setdefault(e['src'], {})[e['line']] = (e, tr[e['id']])
    for details, lines_map in by_file.items():
        src = tx.read_text(os.path.join(root, details))
        lines, sep = tx.line_break(src)
        n = 0
        for line_no, (e, en) in lines_map.items():
            mk = re.match(r'^([A-Za-z0-9_]+)=(.*)$', lines[line_no])
            assert mk and mk.group(1) == e['key'], (details, line_no, e['key'])
            lines[line_no] = '%s=%s' % (e['key'], fix_value(en, e))
            n += 1
        out = os.path.join(BUILD, details.replace('/', os.sep))
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, 'wb').write(sep.join(lines).encode('utf-8', 'surrogateescape'))
        stats[details] = n


def apply_misc(root, entries, tr, stats):
    for fn in ('war3mapMisc.txt', 'war3mapSkin.txt'):
        p = os.path.join(root, fn)
        if not os.path.exists(p):
            continue
        lines, sep = tx.line_break(tx.read_text(p))
        n = 0
        for e in entries:
            if e['src'] == fn and e['id'] in tr:
                lines[e['line']] = '%s=%s' % (e['key'], tr[e['id']].replace('"', "'"))
                n += 1
        open(os.path.join(BUILD, fn), 'wb').write(sep.join(lines).encode('utf-8', 'surrogateescape'))
        stats[fn] = n
    p = os.path.join(root, 'war3map.wts')
    if os.path.exists(p):
        t = tx.read_text(p)
        n = 0
        for e in entries:
            if e['src'] == 'war3map.wts' and e['id'] in tr:
                num = e['key'].split()[1]
                t, k = re.subn(
                    r'(STRING %s\s*(?://[^\n]*\n)?\s*\{\r?\n)(.*?)(\r?\n\})' % num,
                    lambda m: m.group(1) + tr[e['id']] + m.group(3),
                    t,
                    count=1,
                    flags=re.S,
                )
                n += k
        open(os.path.join(BUILD, 'war3map.wts'), 'wb').write(t.encode('utf-8', 'surrogateescape'))
        stats['war3map.wts'] = n
    p = os.path.join(root, 'war3map.w3i')
    if os.path.exists(p):
        w = open(p, 'rb').read()
        q = 12
        parts = [w[:12]]
        for lab in ('name', 'author', 'description', 'players'):
            e = w.index(b'\0', q)
            s = w[q:e]
            key = 'w3i:' + lab
            if key in tr:
                s = tr[key].encode('utf-8')
            parts.append(s + b'\0')
            q = e + 1
        fixed = 32 + 16 + 8 + 4 + 1 + 4
        parts.append(w[q:q + fixed])
        q += fixed
        for lab in ('loading_model', 'loading_text', 'loading_title', 'loading_sub'):
            e = w.index(b'\0', q)
            s = w[q:e]
            key = 'w3i:' + lab
            if key in tr:
                s = tr[key].encode('utf-8')
            parts.append(s + b'\0')
            q = e + 1
        parts.append(w[q:])
        open(os.path.join(BUILD, 'war3map.w3i'), 'wb').write(b''.join(parts))
        stats['war3map.w3i'] = sum(1 for k in tr if k.startswith('w3i:'))


def translation_map(entries, tr, extras=None):
    by_text = {}
    for e in entries:
        if e['src'] == 'war3map.j' and e['kind'] in ('script', 'command') and e['id'] in tr:
            by_text[e['text']] = tr[e['id']]
    for k, v in (extras or {}).items():
        by_text.setdefault(k, v)
    return by_text

