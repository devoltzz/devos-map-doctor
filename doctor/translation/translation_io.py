# Exports the texts a player sees to one file and imports a translation back, checked.
import collections
import gc
import hashlib
import json
import os
import re
import shutil

from doctor.fix import unprotect
from doctor.mpq import mpqadd
from doctor.data import object_names
from doctor.data import objbin
from doctor.data import slk_patch
from doctor.translation import tr_apply
from doctor.translation import tr_compared
from doctor.translation import tr_extract
from doctor.translation import tr_pair_check
from doctor.translation import tr_screen_cjk
from doctor.data import w3i


FORMAT = 'devos-map-doctor-translation'
VERSION = 1
SCRIPTS = ('war3map.j', 'scripts\\war3map.j')
TEXT_FIELDS = {
    'w3u': {'unam': 'Name', 'utip': 'Tooltip', 'utub': 'Extended tooltip', 'ides': 'Description',
            'upro': 'Proper names', 'uawt': 'Awaken tooltip', 'utpr': 'Revive tooltip',
            'ucun': 'Caster upgrade names', 'ucut': 'Caster upgrade tooltips'},
    'w3t': {'unam': 'Name', 'utip': 'Tooltip', 'utub': 'Extended tooltip', 'ides': 'Description'},
    'w3a': {'anam': 'Name', 'atp1': 'Tooltip', 'aub1': 'Extended tooltip', 'aret': 'Research tooltip',
            'arut': 'Research extended tooltip', 'aut1': 'Turn off tooltip', 'auu1': 'Turn off extended tooltip'},
    'w3h': {'ftip': 'Tooltip', 'fube': 'Extended tooltip'},
    'w3q': {'gnam': 'Name', 'gtp1': 'Tooltip', 'gub1': 'Extended tooltip'},
    'w3b': {'bnam': 'Name'},
}
OBJECT_KIND = {'w3u': 'unit', 'w3t': 'item', 'w3a': 'ability', 'w3h': 'buff', 'w3q': 'upgrade', 'w3b': 'destructable'}
NAME_FIELDS = ('unam', 'anam', 'gnam', 'bnam', 'upro', 'ucun')
W3I_FIELDS = (('name', 'map name'), ('author', 'map author'), ('description', 'map description'),
              ('players_recommended', 'suggested players'), ('loading_title', 'loading screen title'),
              ('loading_subtitle', 'loading screen subtitle'), ('loading_text', 'loading screen text'),
              ('prologue_title', 'prologue title'), ('prologue_subtitle', 'prologue subtitle'),
              ('prologue_text', 'prologue text'))
MISC_FILES = ('war3mapSkin.txt', 'war3mapMisc.txt')
DISPLAY_CALLS = ('Display', 'BlzFrameSetText', 'BlzFrameAddText', 'BlzFrameSetTooltip', 'DzFrameSetText',
                 'BlzSetAbilityTooltip', 'BlzSetAbilityExtendedTooltip', 'BlzSetAbilityActivated',
                 'BlzSetAbilityResearch', 'BlzSetUnitName', 'BlzSetHeroProperName', 'BlzSetItemName',
                 'BlzSetItemTooltip', 'BlzSetItemExtendedTooltip', 'BlzSetItemDescription', 'BlzDisplayChatMessage',
                 'SetTextTag', 'CreateTextTag', 'Dialog', 'Quest', 'CreateQuest', 'Multiboard', 'CreateMultiboard',
                 'Leaderboard', 'CreateLeaderboard', 'TimerDialogSetTitle', 'CreateTimerDialog', 'CustomVictory',
                 'CustomDefeat', 'SetPlayerName', 'TransmissionFromUnit', 'DoTransmission', 'SetCinematicScene',
                 'BJDebugMsg')
NOT_TEXT_CALLS = ('SetUnitAnimation', 'QueueUnitAnimation', 'AddUnitAnimationProperties', 'SetDestructableAnimation',
                  'QueueDestructableAnimation', 'SetDoodadAnimation', 'AddSpecialEffect', 'AddSpellEffect',
                  'BlzSetSpecialEffect', 'BlzPlaySpecialEffect', 'Issue', 'ExecuteFunc', 'Preload', 'CreateSound',
                  'CreateMIDISound', 'SetSoundParamsFromLabel', 'PlayMusic', 'PlayThematicMusic', 'SetMapMusic',
                  'TriggerRegisterPlayerChatEvent', 'GetLocalizedString', 'GetLocalizedHotkey', 'OrderId', 'S2I',
                  'S2R', 'BlzLoadTOCFile', 'DzLoadToc', 'BlzFrameSetTexture', 'DzFrameSetTexture', 'BlzFrameSetModel',
                  'DzFrameSetModel', 'BlzFrameSetFont', 'DzFrameSetFont', 'SetSkyModel', 'SetCineFilterTexture',
                  'AddLightning', 'DzSetUnitModel', 'DzSetUnitTexture', 'DzSync', 'BlzSendSyncData',
                  'BlzTriggerRegisterPlayerSyncEvent', 'BlzSetAbilityIcon', 'BlzSetItemIconPath')
CJK_LANGUAGES = ('zh', 'existing', 'ko', 'cn', 'jp', 'kr', 'chinese', 'japanese', 'korean')
RX_COLOR = object_names.RX_COLOR
RX_TRIGSTR = re.compile(r'\s*TRIGSTR_(\d+)\s*$')
RX_WESTRING = re.compile(r'\s*WESTRING_\w+\s*$')
RX_FILE = re.compile(r'\.(?:mdl|mdx|blp|tga|dds|png|jpg|wav|mp3|flac|ogg|txt|slk|fdf|toc|j|lua|ai|pld|w3[a-z])$',
                     re.I)
RX_FORMAT = re.compile(r'%(?:\d+\$)?[sd]')
RX_COMPILER_DEBUG = re.compile(r'(?:when (?:calling|writing array) \S+ in \S+, line \d+|via function reference \S+, '
                               r'line \d+|\S+, line \d+|Called \S+ on invalid object\.|'
                               r'Nullpointer exception when calling \S+|Out of memory: Could not create \S+|'
                               r'Could not initialize package \S+\.|Double free: object of type \S+)$')
RX_KEY = re.compile(r'^([A-Za-z0-9_]+)=(.*)$')
RX_SECTION = re.compile(r'^\[(.+)\]\s*$')
HELP = (
    'Fill "translation" for each entry you translate; leave it empty to keep the original text.',
    'Keep every color code (|cAARRGGBB ... |r) and line break code (|n) in the same order, every number, %s and %d.',
    'Script entries are JASS strings: keep \\" and \\\\ as they are and write no real line break.',
    'Profile entries with commas are lists of levels: keep the same number of commas.',
    'Chat commands stay as they are, also when a tooltip quotes them.',
    'An entry with a "note" about the script comparing it: give every entry with that text the same translation.',
    'For a Chinese, Japanese or Korean translation, set "language" (zh, ja or ko).')
REASONS = (('empty', 'empty translation'), ('CJK restante', 'Chinese, Japanese or Korean text left'),
           ('mencao a IA', 'mentions AI or translation'), ('raw line break', 'a real line break (use |n)'),
           ('codigos de cor diferentes', 'color codes changed'),
           ('double quotes in a txt value', 'double quotes in a data value'),
           ('different quote escaping', 'escaped quotes changed'),
           ('aspas sem escape', 'a double quote without a backslash in a script text'),
           ('barra invertida solta', 'a lone backslash in a script text'),
           ('muito longo', 'much longer than the original'), ('numeros diferentes', 'numbers changed'),
           ('level_list', 'level commas changed'), ('not a string', 'not a string'))


def _nothing(*_a, **_k):
    pass


def _read(a, name):
    return unprotect._read(a, name)


def _decode(b):
    return b.decode('utf-8', 'surrogateescape')


def _encode(s):
    return s.encode('utf-8', 'surrogateescape')


def _bad_utf8(s):
    return any(0xDC80 <= ord(c) <= 0xDCFF for c in s)


def is_text(s):
    v = s.strip()
    if len(v) >= 2 and v[0] == '"' and v[-1] == '"':
        v = v[1:-1]
    return any(c.isalpha() for c in RX_COLOR.sub('', v)) and not RX_TRIGSTR.match(v) and not RX_WESTRING.match(v)


def path_like(s, script=False):
    v = s.strip()
    if not v or ' ' in v:
        return False
    return ('\\\\' in v if script else '\\' in v) or bool(RX_FILE.search(v))


def _cjk(s):
    return bool(tr_extract.CJK.search(s))


def _short(s, n=160):
    s = ' '.join(s.split())
    return s if len(s) <= n else s[:n - 3] + '...'


def separators(text, lines):
    seps, pos = [], 0
    for line in lines[:-1]:
        pos += len(line)
        sep = '\r\n' if text.startswith('\r\n', pos) else text[pos:pos + 1]
        if sep not in ('\r\n', '\r', '\n'):
            raise ValueError('lines do not split the text at line breaks')
        seps.append(sep)
        pos += len(sep)
    if ''.join(line + s for line, s in zip(lines, seps + [''])) != text:
        raise ValueError('lines do not rebuild the text')
    return seps


def join_lines(lines, seps):
    return ''.join(line + s for line, s in zip(lines, list(seps) + ['']))


def _dedupe(entries):
    seen = collections.Counter()
    for e in entries:
        seen[e['id']] += 1
        if seen[e['id']] > 1:
            e['id'] = '%s#%d' % (e['id'], seen[e['id']])


class MapText(object):
    def __init__(self):
        self.entries = []
        self.files = {}
        self.skipped = collections.Counter()
        self.script = 'none'
        self.script_file = None
        self.map_name = ''
        self.refs = collections.defaultdict(list)
        self.compared_trigstr = set()
        self.name_trigstr = set()

    def add(self, **kw):
        self.entries.append(kw)
        return kw


def _ref(mt, value, who, name=False):
    m = RX_TRIGSTR.match(value)
    if m:
        mt.refs[int(m.group(1))].append(who)
        if name:
            mt.name_trigstr.add(int(m.group(1)))
    return bool(m)


def _collect_w3i(mt, read):
    b = read('war3map.w3i')
    if not b:
        return
    try:
        m = w3i.parse(b)
        same = w3i.write(m) == b
    except Exception:
        mt.skipped['w3i: unreadable'] += 1
        return
    mt.files['war3map.w3i'] = b
    rows = [(field, label, ('field', field), m.get(field)) for field, label in W3I_FIELDS]
    rows += [('player:%d' % i, 'player %d name' % (p['number'] + 1), ('player', i), p.get('name'))
             for i, p in enumerate(m.get('players') or [])]
    rows += [('force:%d' % i, 'force %d name' % (i + 1), ('force', i), f.get('name'))
             for i, f in enumerate(m.get('forces') or [])]
    mt.map_name = _decode(m.get('name') or b'')
    for key, label, where, value in rows:
        if value is None:
            continue
        s = _decode(value)
        if _ref(mt, s, 'w3i ' + label) or not is_text(s):
            continue
        if not same:
            mt.skipped['w3i: not rewritable byte for byte'] += 1
            continue
        mt.add(id='w3i:' + key, source='w3i', file='war3map.w3i', context=label, text=s, _kind='meta', _where=where)


def _collect_wts(mt, read):
    b = read('war3map.wts')
    if not b:
        return {}
    mt.files['war3map.wts'] = b
    t = _decode(b)
    texts = {}
    for mo in tr_extract.RX_WTS.finditer(t):
        texts.setdefault(int(mo.group(1)), mo.group(2))
    found = []
    tr_extract.extract_wts_text(t, found, collections.Counter(), tem_text=is_text)
    seen = set()
    for e in found:
        n = int(e['key'].split()[1])
        if n in seen:
            mt.skipped['wts: repeated string number'] += 1
            continue
        seen.add(n)
        if path_like(e['text']):
            mt.skipped['wts: a file path'] += 1
            continue
        mt.add(id='wts:%d' % n, source='wts', file='war3map.wts', context='', text=e['text'], _kind='tip', _where=n)
    return texts


def _collect_objects(mt, read):
    try:
        names = object_names.names(read, game=False)
    except Exception:
        names = {}
    for prefix in ('war3map.', 'war3mapSkin.'):
        for ext in sorted(TEXT_FIELDS):
            name = prefix + ext
            b = read(name)
            if not b:
                continue
            levels = name.lower() in objbin.WITH_LEVELS
            try:
                _version, tables, _end = objbin.read_data(b, levels)
            except Exception:
                mt.skipped['object data: %s unreadable' % name] += 1
                continue
            mt.files[name] = b
            for ti, table in enumerate(tables):
                for oi, (old, new, mods) in enumerate(table):
                    ident = new if ti == 1 else old
                    for mi, (mid, vt, lvl, _dptr, val) in enumerate(mods):
                        if vt != 3:
                            continue
                        s = _decode(val)
                        label = TEXT_FIELDS[ext].get(mid)
                        what = '%s %s %s' % (OBJECT_KIND[ext], ident, label or mid)
                        if _ref(mt, s, what, mid in NAME_FIELDS) or not label or not is_text(s):
                            continue
                        title = names.get(ident)
                        mt.add(id='obj:%s:%s:%s%s' % (name, ident, mid, ':%d' % lvl if lvl else ''), source='object',
                               file=name, context='%s %s%s, %s%s' % (
                                   OBJECT_KIND[ext], ident, ' (%s)' % title if title and mid not in NAME_FIELDS else '',
                                   label, ' level %d' % lvl if lvl else ''),
                               text=s, _kind='name' if mid in NAME_FIELDS else 'tip', _where=(ti, oi, mi),
                               _levels=levels)


def _sections(lines):
    out, current = [], ''
    for line in lines:
        m = RX_SECTION.match(line)
        if m:
            current = m.group(1)
        out.append(current)
    return out


def _collect_profiles(mt, read, names):
    files = slk_patch.table_files(names, read)
    for name in sorted(files, key=lambda n: n.lower()):
        if not name.lower().endswith('.txt'):
            continue
        text = _decode(files[name])
        found = []
        tr_extract.extract_txt_text(name, text, found, collections.Counter(), collections.Counter(),
                                    tem_text=is_text)
        lines = tr_extract.line_break(text)[0]
        sections = _sections(lines)
        for ln, line in enumerate(lines):
            m = RX_KEY.match(line)
            if m:
                _ref(mt, m.group(2).strip('"'), '%s [%s] %s' % (name, sections[ln], m.group(1)),
                     m.group(1).lower() in ('name', 'propernames'))
        if found:
            mt.files[name] = files[name]
        for e in found:
            mt.add(id='txt:%s:%s:%s' % (name, e['obj'], e['key']), source='profile', file=name,
                   context='%s [%s] %s' % (name, e['obj'], e['key']), text=e['text'], _kind=e['kind'],
                   _where=e['line'], _key=e['key'], _tx={'quoted': e['quoted'], 'comma': e['comma']})
    for name in MISC_FILES:
        b = read(name)
        if not b:
            continue
        text = _decode(b)
        found = []
        tr_extract.extract_misc_text(name, text, found, collections.Counter(), tem_text=is_text)
        lines = tr_extract.line_break(text)[0]
        sections = _sections(lines)
        for ln, line in enumerate(lines):
            m = RX_KEY.match(line)
            if m:
                _ref(mt, m.group(2), '%s [%s] %s' % (name, sections[ln], m.group(1)))
        kept = [e for e in found if sections[e['line']].lower() == 'framedef' or
                (_cjk(e['text']) and not path_like(e['text']))]
        if kept:
            mt.files[name] = b
        for e in kept:
            mt.add(id='txt:%s:%s:%s' % (name, sections[e['line']], e['key']), source='profile', file=name,
                   context='%s [%s] %s' % (name, sections[e['line']], e['key']), text=e['text'], _kind='tip',
                   _where=e['line'], _key=e['key'], _misc=True)


def _script_candidate(lit):
    return is_text(lit) and not path_like(lit, script=True)


def _functions_by_line(lines):
    out, current = [], None
    for line in lines:
        m = tr_extract.RX_FUNCTION.match(line)
        if m:
            current = m.group(1)
        out.append(current)
        if tr_extract.RX_END_FUNCTION.match(line):
            current = None
    return out


def script_language(a, read):
    name = next((n for n in SCRIPTS if read(n) is not None), None)
    j = read(name) if name else None
    lua = read('war3map.lua')
    lang = unprotect.language_from_w3i(read('war3map.w3i'))
    if lua is not None and (lang == 1 or j is None):
        return 'lua', 'war3map.lua', lua
    if j is None:
        return 'none', None, None
    if unprotect.script_j2b(a, j):
        return 'j2b', name, j
    if len(j) < 450 and a.find('kkmap.jc'):
        return 'kkwe', name, j
    return 'jass', name, j


def _collect_script(mt, a, read):
    mt.script, name, b = script_language(a, read)
    if mt.script != 'jass':
        if mt.script != 'none':
            mt.skipped['script: %s, literals not exported' % mt.script] += 1
        return None, []
    mt.script_file = name
    mt.files[name] = b
    src = _decode(b)
    found = []
    tr_extract.extract_script_text(src, found, collections.Counter(), (), tem_text=_script_candidate)
    lines = tr_extract.line_break(src, jass=True)[0]
    functions = _functions_by_line(lines)
    screen = dict((e['text'], e) for e in found if e['kind'] == 'script')
    cats = collections.defaultdict(collections.Counter)
    for ln, lit, cat in tr_screen_cjk.occurrences(lines, lambda x: x in screen or RX_TRIGSTR.match(x), protected=()):
        m = RX_TRIGSTR.match(lit)
        if m:
            n = int(m.group(1))
            mt.refs[n].append('script function %s' % functions[ln] if functions[ln] else 'script globals')
            if cat.split(':', 1)[0] in ('caution', 'hash_key'):
                mt.compared_trigstr.add(n)
            continue
        cats[lit][cat] += 1
    for e in found:
        if e['kind'] != 'script':
            mt.skipped['script: compared or key text' if e['kind'] == 'command' else 'script: data read by position'] \
                += 1
            continue
        lit = e['text']
        c = cats[lit]
        groups = collections.Counter()
        for cat, n in c.items():
            groups[cat.split(':', 1)[0]] += n
        calls = [cat.split(':', 1)[1] for cat in c if cat.startswith('tela:')]
        if 'localizada' in e['uses']:
            reason = 'a game string key'
        elif groups['caution'] or groups['datum']:
            reason = 'compared by the script'
        elif not groups['screen']:
            reason = 'used as a key only'
        elif all(f.startswith(NOT_TEXT_CALLS) for f in calls):
            reason = 'not screen text'
        elif not _cjk(lit) and RX_COMPILER_DEBUG.match(lit):
            reason = 'a compiler debug message'
        elif not _cjk(lit) and not ('exibicao' in e['uses'] or any(f.startswith(DISPLAY_CALLS) for f in calls) or
                                    ' ' in RX_COLOR.sub('', lit).strip() or RX_COLOR.search(lit)):
            reason = 'not screen text'
        else:
            reason = None
        if reason:
            mt.skipped['script: ' + reason] += 1
            continue
        ln = e['lines'][0]
        where = 'function %s' % functions[ln] if functions[ln] else 'globals'
        entry = mt.add(id='script:' + hashlib.sha1(_encode(lit)).hexdigest()[:12], source='script', file=name,
                       context='%s: %s' % (where, _short(e['contexts'][0])), text=lit, _kind='script', _where=None,
                       _screen=groups['screen'])
        if groups['hash_key']:
            entry['note'] = 'Also used as a key by the script: those %d copies stay as they are.' % groups['hash_key']
    return src, found


def _comparison_rules(mt, src, script_entries, wts_texts):
    data = [e for e in mt.entries if e['source'] != 'script']
    linked, keyed = {}, set()
    if src is not None:
        fake = [{'id': e['id'], 'src': e['file'], 'kind': e['_kind'], 'text': e['text'], 'key': ''} for e in data]
        by = tr_compared.measure(src, list(script_entries) + fake, dict((e['id'], e['text']) for e in data))
        for lit, d in by.items():
            if d['rec'] == 'all_entries' and d['clusters'].get('hash_key'):
                keyed.add(lit)
            elif d['rec'] == 'all_entries':
                linked[lit] = 'script'
        window = sorted(lit for lit, d in by.items() if d['rec'] == 'window')
    else:
        window = []
    for n in mt.compared_trigstr:
        if n in wts_texts:
            linked.setdefault(wts_texts[n], 'wts')
    keep = []
    for e in mt.entries:
        is_name = e['_kind'] == 'name' or (e['source'] == 'wts' and e['_where'] in mt.name_trigstr)
        if is_name and window and any(w in e['text'] for w in window):
            mt.skipped['%s: a name the script reads by byte position' % e['source']] += 1
            continue
        if e['source'] != 'script' and e['text'] in keyed:
            mt.skipped['%s: compared and used as a key by the script' % e['source']] += 1
            continue
        if e['source'] != 'script' and e['text'] in linked:
            e['_group'] = linked[e['text']]
            e['note'] = 'The script compares this text: give every entry with it the same translation.'
        keep.append(e)
    mt.entries = keep


def _wts_contexts(mt):
    for e in mt.entries:
        if e['source'] != 'wts':
            continue
        who = list(dict.fromkeys(mt.refs.get(e['_where'], ())))
        if not who:
            e['context'] = 'not used by the object data, the map info or the script'
        else:
            e['context'] = 'used by ' + '; '.join(who[:3]) + (' and %d more' % (len(who) - 3) if len(who) > 3 else '')


def collect(a, progress=None):
    p = progress or _nothing
    mt = MapText()

    def read(name):
        return _read(a, name)
    p('map info')
    _collect_w3i(mt, read)
    p('strings')
    wts_texts = _collect_wts(mt, read)
    p('object data')
    _collect_objects(mt, read)
    p('profiles')
    _collect_profiles(mt, read, unprotect.listfile_names(a))
    p('script')
    src, script_entries = _collect_script(mt, a, read)
    _comparison_rules(mt, src, script_entries, wts_texts)
    _wts_contexts(mt)
    m = RX_TRIGSTR.match(mt.map_name)
    if m:
        mt.map_name = wts_texts.get(int(m.group(1)), mt.map_name)
    mt.map_name = object_names.clean(_encode(mt.map_name).decode('utf-8', 'replace'))
    good = []
    for e in mt.entries:
        if _bad_utf8(e['text']) or _bad_utf8(e['id']):
            mt.skipped['%s: not valid UTF-8' % e['source']] += 1
        else:
            good.append(e)
    mt.entries = good
    _dedupe(mt.entries)
    return mt


def _open(path):
    with unprotect.quiet():
        return unprotect.mpqread.Archive(path)


def _error(e):
    return '%s: %s' % (type(e).__name__, e) if str(e) else type(e).__name__


def public(e):
    out = collections.OrderedDict((k, e[k]) for k in ('id', 'source', 'file', 'context', 'text'))
    out['context'] = _encode(out['context']).decode('utf-8', 'replace')
    out['file'] = _encode(out['file']).decode('utf-8', 'replace')
    if e.get('note'):
        out['note'] = e['note']
    out['translation'] = ''
    return out


def export(path, out_file, progress=None):
    p = progress or _nothing
    rep = {'state': None, 'error': None, 'file': None, 'map_name': None, 'script': None, 'entries': 0,
           'by_source': {}, 'skipped': {}, 'linked': 0}
    try:
        p('reading map')
        a = _open(path)
        mt = collect(a, p)
    except (Exception, SystemExit) as e:
        rep.update(state='failed', error='cannot read the map (%s)' % _error(e))
        return rep
    rep.update(map_name=mt.map_name, script=mt.script, skipped=dict(sorted(mt.skipped.items())),
               entries=len(mt.entries), linked=sum(1 for e in mt.entries if e.get('_group')),
               by_source=dict(collections.Counter(e['source'] for e in mt.entries)))
    if not mt.entries:
        rep['state'] = 'no_text'
        return rep
    order = {'w3i': 0, 'wts': 1, 'object': 2, 'profile': 3, 'script': 4}
    entries = [public(e) for e in sorted(mt.entries, key=lambda e: order[e['source']])]
    doc = collections.OrderedDict([('format', FORMAT), ('version', VERSION), ('map', os.path.basename(path)),
                                   ('map_name', mt.map_name), ('language', ''), ('help', list(HELP)),
                                   ('entries', entries)])
    p('writing')
    part = out_file + '.part'
    try:
        with open(part, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(doc, f, ensure_ascii=False, indent=1)
        with open(part, encoding='utf-8') as f:
            back = json.load(f)
        if back != json.loads(json.dumps(doc)):
            raise ValueError('the file did not read back the same')
        os.replace(part, out_file)
    except Exception as e:
        if os.path.exists(part):
            os.remove(part)
        rep.update(state='failed', error='cannot write the file (%s)' % _error(e))
        return rep
    rep.update(state='done', file=out_file)
    return rep


RX_CODES = re.compile(r'(\|c[0-9A-Fa-f]{8}|\|[rRnN]|%(?:\d+\$)?[sd]|\\n|\n)')


def _html_text(s):
    import html
    out = []
    for i, part in enumerate(RX_CODES.split(s)):
        if not part:
            continue
        if i % 2:
            out.append('<span translate="no" class="c">%s</span>' % html.escape(part).replace('\n', '&#10;'))
        else:
            out.append(html.escape(part).replace('\n', '<br>'))
    return ''.join(out)


def export_html(path, out_file, progress=None):
    import html
    tmp = out_file + '.json.part'
    rep = export(path, tmp, progress)
    if rep['state'] != 'done':
        return rep
    try:
        with open(tmp, encoding='utf-8') as f:
            doc = json.load(f)
    finally:
        os.remove(tmp)
    rows = []
    for e in doc['entries']:
        text = e['text'].replace('\r\n', '\n')
        rows.append('<tr data-id="%s"%s><td translate="no" class="id">%s</td>'
                    '<td translate="no" class="src">%s</td><td class="t">%s</td></tr>'
                    % (html.escape(e['id'], True), ' data-crlf="1"' if '\r\n' in e['text'] else '',
                       html.escape(e['id']), html.escape(text), _html_text(text)))
    body = (
        '<!doctype html>\n<html lang="%s"><head><meta charset="utf-8"><meta name="format" content="%s;%d">'
        '<title>%s</title><style>td{border:1px solid #ccc;padding:4px;vertical-align:top}.id,.src{color:#777;'
        'font-size:80%%}.c{color:#a50}</style></head><body><p translate="no">Devo\'s Map Doctor translation file for '
        '%s. Translate only the last column; leave the gray cells and the brown codes as they are, then load the '
        'translated file back in the Translation tab.</p><table>\n%s\n</table></body></html>\n'
        % (
            doc.get('language') or 'und',
            FORMAT,
            VERSION,
            html.escape(doc['map']),
            html.escape(doc['map']),
            '\n'.join(rows),
        )
    )
    part = out_file + '.part'
    try:
        with open(part, 'w', encoding='utf-8', newline='\n') as f:
            f.write(body)
        back = _load_html(part)
        if [x['id'] for x in back['entries']] != [e['id'] for e in doc['entries']] or \
                any(x['translation'] != e['text'] for x, e in zip(back['entries'], doc['entries'])):
            raise ValueError('the HTML file did not read back the same')
        os.replace(part, out_file)
    except Exception as e:
        if os.path.exists(part):
            os.remove(part)
        rep.update(state='failed', file=None, error='cannot write the file (%s)' % _error(e))
        return rep
    rep['file'] = out_file
    return rep


def _load_html(translation_file):
    import html
    import html.parser

    class Reader(html.parser.HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.rows, self.cell, self.buf, self.lang = [], None, [], ''

        def handle_starttag(self, tag, attrs):
            a = dict(attrs)
            if tag == 'html' and a.get('lang'):
                self.lang = a['lang']
            elif tag == 'tr' and 'data-id' in a:
                self.rows.append({'id': a['data-id'], 'src': '', 't': '', 'crlf': 'data-crlf' in a})
            elif tag == 'td' and self.rows:
                cls = a.get('class') or ''
                self.cell = 'src' if 'src' in cls else 't' if 't' in cls.split() else None
                self.buf = []
            elif tag == 'br' and self.cell == 't':
                self.buf.append('\n')

        def handle_endtag(self, tag):
            if tag == 'td' and self.cell and self.rows:
                self.rows[-1][self.cell] = ''.join(self.buf)
                self.cell = None

        def handle_data(self, data):
            if self.cell:
                self.buf.append(data)

    r = Reader()
    with open(translation_file, encoding='utf-8-sig') as f:
        r.feed(f.read())
    if not r.rows:
        raise ValueError('not a Devo\'s Map Doctor translation file')
    lang = r.lang if r.lang and r.lang != 'und' else ''
    def back(s, crlf):
        s = s.replace('\r\n', '\n')
        return s.replace('\n', '\r\n') if crlf else s
    return {'format': FORMAT, 'language': lang,
            'entries': [{'id': x['id'], 'text': back(x['src'], x['crlf']), 'translation': back(x['t'], x['crlf'])}
                        for x in r.rows]}


def _english(err):
    for pt, en in REASONS:
        if err.startswith(pt):
            rest = err[len(pt):]
            if pt == 'level_list':
                m = re.match(r':\s*(\d+) (virgulas|aspas), esperado (\d+)', rest)
                if m:
                    return 'level %s: %s, expected %s' % ('commas' if m.group(2) == 'virgulas' else 'quotes',
                                                         m.group(1), m.group(3))
            if pt == 'muito longo':
                rest = rest.replace(' chars vs ', ' characters vs ')
            return en + (rest if rest.startswith(' (') else '')
    return err


def _is_cjk_language(language):
    return (language or '').strip().lower().startswith(CJK_LANGUAGES)


def check_entry(e, translation, language=''):
    if not isinstance(translation, str):
        return ['not a string']
    tx = e.get('_tx') or {}
    entry_ = {'text': e['text'], 'kind': e['_kind'], 'src': e['file'], 'quoted': tx.get('quoted', False),
               'comma': tx.get('comma', False)}
    item = {'t': e['text']}
    if tx.get('comma') and not tx.get('quoted'):
        item['level_list'] = e['text'].count(',') + 1
    errs = tr_pair_check.errors_of(item, entry_, translation)
    if tx.get('quoted') and '","' in e['text']:
        expected = len(tr_pair_check.level_commas('"%s"' % e['text'], True))
        found = len(tr_pair_check.level_commas('"%s"' % translation, True))
        if found != expected:
            errs.append('niveis: %d virgulas, esperado %d' % (found, expected))
        elif translation.count('"') % 2 != e['text'].count('"') % 2:
            errs.append('niveis: %d aspas, esperado %d' % (translation.count('"'), e['text'].count('"')))
    if not _cjk(e['text']) or _is_cjk_language(language):
        errs = [x for x in errs if not x.startswith('CJK restante')]
    out = [_english(x) for x in errs]
    if '\x00' in translation:
        out.append('a NUL character')
    if sorted(RX_FORMAT.findall(e['text'])) != sorted(RX_FORMAT.findall(translation)):
        out.append('format codes (%s, %d) changed')
    if e['source'] == 'wts' and re.search(r'^\}', translation, re.M):
        out.append('a line starting with } (it ends a wts string)')
    if e['source'] == 'profile' and ('\r' in translation or '\n' in translation):
        out.append('a real line break in a profile value')
    if _bad_utf8(translation):
        out.append('not valid UTF-8')
    return list(dict.fromkeys(out))


def _written(e, translation):
    if e['source'] == 'profile' and not e.get('_misc'):
        return tr_apply.fix_value(translation, dict(e['_tx'], text=e['text']))
    if e['source'] == 'profile':
        return translation.replace('"', "'")
    return translation


def replace_wts(t, new):
    out, last, done = [], 0, set()
    for m in tr_extract.RX_WTS.finditer(t):
        n = int(m.group(1))
        if n in new and n not in done:
            out += [t[last:m.start(2)], new[n]]
            last = m.end(2)
            done.add(n)
    if done != set(new):
        raise RuntimeError('wts strings not found: %s' % sorted(set(new) - done)[:5])
    return ''.join(out) + t[last:]


def _build(mt, wanted, linked):
    by_file = collections.defaultdict(list)
    for e, t in wanted:
        by_file[e['file']].append((e, t))
    if linked and mt.script_file:
        by_file.setdefault(mt.script_file, [])
    out, script = {}, {'replaced': 0, 'categories': {}, 'per_literal': {}}
    for name, items in sorted(by_file.items()):
        orig = mt.files[name]
        if name == 'war3map.wts':
            new = _encode(replace_wts(_decode(orig), dict((e['_where'], tr) for e, tr in items)))
        elif name == 'war3map.w3i':
            m = w3i.parse(orig)
            for e, tr in items:
                kind, key = e['_where']
                value = _encode(tr)
                if kind == 'field':
                    m[key] = value
                elif kind == 'player':
                    m['players'][key]['name'] = value
                else:
                    m['forces'][key]['name'] = value
            new = w3i.write(m)
        elif name == mt.script_file:
            src = _decode(orig)
            lines = tr_extract.line_break(src, jass=True)[0]
            seps = separators(src, lines)
            by_text = dict((e['text'], tr) for e, tr in items)
            by_text.update(linked)
            cats, detail, n = tr_apply.apply_by_occurrence_lines(lines, by_text, False, linked, protected=())
            script.update(replaced=n, categories=dict(cats), per_literal=dict(
                (lit, d['screen'] + d['all_entries']) for lit, d in detail.items()))
            new = _encode(join_lines(lines, seps))
        elif items[0][0]['source'] == 'object':
            change = dict((e['_where'], _encode(_written(e, tr))) for e, tr in items)
            new, n = objbin.rewrite(orig, items[0][0]['_levels'], lambda ti, oi, mi, _f, _v: change.get((ti, oi, mi)))
            if n != len(change):
                raise RuntimeError('%s: %d of %d values written' % (name, n, len(change)))
        else:
            text = _decode(orig)
            lines = tr_extract.line_break(text)[0]
            seps = separators(text, lines)
            for e, tr in items:
                m = RX_KEY.match(lines[e['_where']])
                if not m or m.group(1) != e['_key']:
                    raise RuntimeError('%s: line %d is not %s' % (name, e['_where'] + 1, e['_key']))
                lines[e['_where']] = '%s=%s' % (e['_key'], _written(e, tr))
            new = _encode(join_lines(lines, seps))
        if new != orig:
            out[name] = new
    return out, script


def _script_counts(text, watch):
    lines = tr_extract.line_break(text, jass=True)[0]
    return collections.Counter(lit for _ln, lit, _c in tr_screen_cjk.occurrences(lines, lambda x: x in watch,
                                                                                  protected=()))


def _readback(a, mt, wanted, linked, script):
    missing = []
    cache, parsed = {}, {}

    def data(name):
        if name not in cache:
            cache[name] = _read(a, name)
        return cache[name]

    def view(e):
        if e['file'] not in parsed:
            b = data(e['file'])
            if e['source'] == 'wts':
                v = {}
                for mo in tr_extract.RX_WTS.finditer(_decode(b)):
                    v.setdefault(int(mo.group(1)), mo.group(2))
            elif e['source'] == 'w3i':
                v = w3i.parse(b)
            elif e['source'] == 'object':
                v = objbin.read_data(b, e['_levels'])[1]
            else:
                v = tr_extract.line_break(_decode(b))[0]
            parsed[e['file']] = v
        return parsed[e['file']]
    for e, tr in wanted:
        if e['source'] == 'script':
            continue
        v = view(e)
        if e['source'] == 'wts':
            got = v.get(e['_where'])
        elif e['source'] == 'w3i':
            kind, key = e['_where']
            raw = v[key] if kind == 'field' else (v['players'] if kind == 'player' else v['forces'])[key]['name']
            got = _decode(raw)
        elif e['source'] == 'object':
            ti, oi, mi = e['_where']
            got = _decode(v[ti][oi][2][mi][4])
        else:
            m = RX_KEY.match(v[e['_where']])
            got = m.group(2) if m else None
        if got != _written(e, tr):
            missing.append((e['id'], got))
    texts = dict((e['text'], tr) for e, tr in wanted if e['source'] == 'script')
    texts.update(linked)
    if texts:
        watch = set(texts) | set(texts.values())
        before = _script_counts(_decode(mt.files[mt.script_file]), watch)
        after = _script_counts(_decode(data(mt.script_file)), watch)
        replaced = script['per_literal']
        made = collections.Counter()
        for lit, tr in texts.items():
            made[tr] += replaced.get(lit, 0)
        for x in sorted(watch):
            if after[x] != before[x] - replaced.get(x, 0) + made[x]:
                missing.append(('script literal %r' % x[:40], '%d copies, expected %d' % (
                    after[x], before[x] - replaced.get(x, 0) + made[x])))
        for e, tr in wanted:
            if e['source'] == 'script' and replaced.get(e['text'], 0) != e['_screen']:
                missing.append((e['id'], '%d of %d screen copies' % (replaced.get(e['text'], 0), e['_screen'])))
        for lit in linked:
            if replaced.get(lit, 0) != before[lit]:
                missing.append(('script copy of %r' % lit[:40], '%d of %d copies' % (replaced.get(lit, 0),
                                                                                    before[lit])))
    return missing


def _load(translation_file):
    if translation_file.lower().endswith(('.html', '.htm')):
        return _load_html(translation_file)
    with open(translation_file, encoding='utf-8-sig') as f:
        doc = json.load(f)
    if not isinstance(doc, dict) or doc.get('format') != FORMAT or not isinstance(doc.get('entries'), list):
        raise ValueError('not a Devo\'s Map Doctor translation file')
    return doc


def _plan(mt, doc):
    language = str(doc.get('language') or '')
    current = dict((e['id'], e) for e in mt.entries)
    wanted, rejected, unknown, seen = [], [], [], set()
    empty = 0
    for t in doc['entries']:
        ident = t.get('id') if isinstance(t, dict) and isinstance(t.get('id'), str) else None
        tr = t.get('translation') if isinstance(t, dict) else None
        if tr is None or tr == '':
            empty += 1
            continue
        e = current.get(ident)
        reason = None
        if ident in seen:
            reason = 'repeated id in the file'
        elif e is None:
            unknown.append(ident)
        elif t.get('text') != e['text']:
            reason = 'the text in the map is not the one in the file'
        else:
            errs = check_entry(e, tr, language)
            if errs:
                reason = '; '.join(errs)
            else:
                wanted.append((e, tr))
        if reason:
            rejected.append({'id': ident, 'text': tr if isinstance(tr, str) else repr(tr), 'reason': reason})
        seen.add(ident)
    linked, groups = {}, collections.defaultdict(list)
    for e in mt.entries:
        if e.get('_group'):
            groups[e['text']].append(e)
    given = dict((e['id'], tr) for e, tr in wanted)
    drop = set()
    for text, members in sorted(groups.items()):
        trs = [given[m['id']] for m in members if m['id'] in given]
        if not trs:
            continue
        reason = None
        if len(trs) != len(members) or len(set(trs)) != 1:
            reason = 'the script compares this text: every entry with it needs the same translation'
        elif members[0]['_group'] == 'script' and ('"' in trs[0] or '\\' in trs[0]):
            reason = 'the script compares this text: no double quote or backslash in its translation'
        if reason:
            for m in members:
                if m['id'] in given:
                    drop.add(m['id'])
                    rejected.append({'id': m['id'], 'text': given[m['id']], 'reason': reason})
        elif members[0]['_group'] == 'script':
            linked[text] = trs[0]
    wanted = [(e, tr) for e, tr in wanted if e['id'] not in drop]
    return wanted, linked, rejected, empty, unknown


def check(path, translation_file, progress=None):
    p = progress or _nothing
    rep = {'ok': 0, 'rejected': [], 'empty': 0, 'unknown': [], 'error': None}
    try:
        doc = _load(translation_file)
    except Exception as e:
        rep['error'] = 'cannot read the translation file (%s)' % _error(e)
        return rep
    try:
        p('reading map')
        mt = collect(_open(path), p)
    except (Exception, SystemExit) as e:
        rep['error'] = 'cannot read the map (%s)' % _error(e)
        return rep
    p('checking translations')
    wanted, _linked, rejected, empty, unknown = _plan(mt, doc)
    rep.update(ok=len(wanted), rejected=rejected, empty=empty, unknown=unknown)
    return rep


def _other_blocks(path_in, b, names):
    a = _open(path_in)
    skip = set()
    for n in names:
        r = a.find_locale(n) if a.find(n) else None
        if r:
            skip.add(r[1])
    todo = [(i, blk) for i, blk in enumerate(a.blocks) if i not in skip and blk[3] & 0x80000000]
    bad = None
    if a.h.offset == b.h.offset:
        spans = sorted(((a.h.offset + blk[0]) & 0xFFFFFFFF, ((a.h.offset + blk[0]) & 0xFFFFFFFF) + blk[1])
                       for _i, blk in todo)
        merged = []
        for s, e in spans:
            if merged and s <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], e)
            else:
                merged.append([s, e])
        bad = [(s, e) for s, e in merged if a.d[s:e] != b.d[s:e]]
    same = differ = 0
    for i, blk in todo:
        pa, pb = (a.h.offset + blk[0]) & 0xFFFFFFFF, (b.h.offset + blk[0]) & 0xFFFFFFFF
        if bad is not None and not any(s < pa + blk[1] and pa < e for s, e in bad):
            equal = True
        else:
            equal = a.d[pa:pa + blk[1]] == b.d[pb:pb + blk[1]]
        if i < len(b.blocks) and b.blocks[i] == blk and equal:
            same += 1
        else:
            differ += 1
    return same, differ


def _remove(path):
    gc.collect()
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


def import_(path_in, translation_file, path_out, progress=None):
    p = progress or _nothing
    rep = {'state': None, 'error': None, 'output': None, 'applied': 0, 'applied_by_source': {}, 'empty': 0,
           'rejected': [], 'unknown': [], 'rejected_by_reason': {}, 'files_changed': [], 'script_copies': 0,
           'verified': None}
    try:
        doc = _load(translation_file)
    except Exception as e:
        rep.update(state='failed', error='cannot read the translation file (%s)' % _error(e))
        return rep
    try:
        p('reading map')
        a = _open(path_in)
        mt = collect(a, p)
    except (Exception, SystemExit) as e:
        rep.update(state='failed', error='cannot read the map (%s)' % _error(e))
        return rep
    p('checking translations')
    wanted, linked, rejected, empty, unknown = _plan(mt, doc)
    rep.update(rejected=rejected, empty=empty, unknown=unknown,
               rejected_by_reason=dict(collections.Counter(r['reason'] for r in rejected)))
    if not wanted:
        rep['state'] = 'nothing_to_apply'
        return rep
    if a.h.version != 0 or a.hash_n_read < a.hash_n:
        rep.update(state='failed', error='the map is protected: unprotect it with Devo\'s Map Doctor first')
        return rep
    del a
    p('building files')
    try:
        changed, script = _build(mt, wanted, linked)
    except Exception as e:
        rep.update(state='failed', error='cannot rewrite the files (%s)' % _error(e))
        return rep
    rep['script_copies'] = sum(script['per_literal'].get(t, 0) for t in linked)
    if not changed:
        rep['state'] = 'nothing_to_apply'
        return rep
    p('writing')
    part = unprotect._part(path_out)
    error = None
    try:
        shutil.copyfile(path_in, part)
        no_slot = []
        with unprotect.quiet():
            mpqadd.add_files(part, sorted(changed.items()), log=_nothing, no_slot=no_slot)
        if no_slot:
            raise RuntimeError('no room in the hash table for %s' % ', '.join(no_slot))
        p('checking')
        b = _open(part)
        bad = [n for n, d in changed.items() if _read(b, n) != d]
        if bad:
            raise RuntimeError('%s not read back as written' % ', '.join(sorted(bad)))
        with unprotect.quiet():
            same = unprotect.check_content(path_in, part, exclude=list(changed))
            blocks_same, blocks_differ = _other_blocks(path_in, b, changed)
        missing = _readback(b, mt, wanted, linked, script)
        del b
        rep['verified'] = {
            'identical': same['identical'],
            'differ': same['different'],
            'missing': same['missing_items'],
            'blocks_identical': blocks_same,
            'blocks_differ': blocks_differ,
            'translations_found': len(wanted) - len(missing),
        }
        if same['different'] or same['missing_items'] or blocks_differ:
            raise RuntimeError('files the translation does not touch changed: %s' % ', '.join(
                (same['different'] + same['missing_items'])[:5] or ['%d unnamed block(s)' % blocks_differ]))
        if missing:
            raise RuntimeError('%d translation(s) not found in the written map, first: %s (%s)'
                               % (len(missing), missing[0][0], missing[0][1]))
        os.replace(part, path_out)
    except (Exception, SystemExit) as e:
        error = _error(e)
    if error:
        _remove(part)
        rep.update(state='failed', error=error)
        return rep
    rep.update(state='done', output=path_out, applied=len(wanted), files_changed=sorted(changed),
               applied_by_source=dict(collections.Counter(e['source'] for e, _t in wanted)))
    return rep
