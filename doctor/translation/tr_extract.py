# Extracts the texts of a map for translation.
import json
import os
import re
from collections import Counter, OrderedDict


HERE = os.path.dirname(os.path.abspath(__file__))
TR = os.environ.get('TR_DIR') or os.path.join(HERE, 'tr')
from doctor.translation import kr_inventory as ki

CJK = re.compile(
    '['
    + chr(0xAC00)
    + '-'
    + chr(0xD7A3)
    + chr(0x1100)
    + '-'
    + chr(0x11FF)
    + chr(0x3130)
    + '-'
    + chr(0x318F)
    + chr(0x4E00)
    + '-'
    + chr(0x9FFF)
    + chr(0x3400)
    + '-'
    + chr(0x4DBF)
    + chr(0x3040)
    + '-'
    + chr(0x30FF)
    + chr(0x3000)
    + '-'
    + chr(0x303F)
    + chr(0xFF00)
    + '-'
    + chr(0xFFEF)
    + ']'
)

TEXT_KEYS = {
    'Name': 'name',
    'Propernames': 'name',
    'EditorSuffix': 'skip',
    'Hotkey': 'skip',
    'Researchhotkey': 'skip',
    'Unhotkey': 'skip',
    'Tip': 'tip',
    'Ubertip': 'tip',
    'Description': 'tip',
    'Awakentip': 'tip',
    'Revivetip': 'tip',
    'Bufftip': 'tip',
    'Buffubertip': 'tip',
    'Researchtip': 'tip',
    'Researchubertip': 'tip',
    'Untip': 'tip',
    'Unubertip': 'tip',
    'Casterarttip': 'tip',
    'Awakenhotkey': 'skip',
    'Casterupgradename': 'name',
    'Casterupgradetip': 'tip',
}
TEXT_KEYS_LC = {k.lower(): v for k, v in TEXT_KEYS.items()}
STRING_FILES = ['units/itemstrings.txt', 'units/campaignabilitystrings.txt', 'units/campaignunitstrings.txt',
                'units/commonabilitystrings.txt', 'units/campaignupgradestrings.txt', 'units/itemabilitystrings.txt']
STRING_FILES += [s.strip() for s in os.environ.get('TR_TXT_EXTRA', '').split(',') if s.strip()]


RX_PROTECTED_PATH = re.compile(r'^[^\r\n"|]*[\x1c-\x1f][^\r\n"|]*\.(?:mdx|mdl|blp|tga|dds|mp3|wav|ogg|flac)$', re.I)


def cjk_text(s):
    return bool(CJK.search(s)) and not RX_PROTECTED_PATH.match(s.replace('\\\\', '\\'))


def read_text(path):
    return open(path, 'rb').read().decode('utf-8', 'surrogateescape')


def line_break(body_text, jass=False, multiline=None):
    crlf = body_text.count('\r\n')
    if body_text.count('\r') - crlf > crlf:
        return split_outside_quotes(body_text, 'mista'), '\n'
    if jass and (multiline if multiline is not None else literal_multilinha()):
        if multiline:
            method, sep = ('crlf', '\r\n') if crlf else ('lf', '\n')
        else:
            method, sep = ('crlf', '\r\n') if crlf and crlf >= body_text.count('\n') - crlf else ('lf', '\n')
        return split_outside_quotes(body_text, method), sep
    sep = '\r\n' if crlf else '\n'
    return body_text.split(sep), sep


_CONFIG = {}


def config(tr_dir=None):
    p = os.path.join(tr_dir or TR, 'config.json')
    if p not in _CONFIG:
        _CONFIG[p] = json.load(open(p, encoding='utf-8')) if os.path.isfile(p) else {}
    return _CONFIG[p]


def literal_multilinha(tr_dir=None):
    return bool(config(tr_dir).get('literal_multilinha'))


def objects_out(tr_dir=None):
    return set(config(tr_dir).get('objects_out', ()))


_SEP_MODE = {'mista': r'\r\n|\r|\n', 'crlf': r'\r\n', 'lf': r'\n'}
_COMENTARIO_MODE = {'mista': r'//[^\r\n]*', 'crlf': r'//(?:(?!\r\n).)*', 'lf': r'//[^\n]*'}
_RX_QUOTES_MODE = dict((m, re.compile(_COMENTARIO_MODE[m] + r'|"(?:[^"\\]|\\.)*"|' + _SEP_MODE[m], re.S))
                       for m in _SEP_MODE)


def split_outside_quotes(body_text, method='mista'):
    line_list, begin = [], 0
    for m in _RX_QUOTES_MODE[method].finditer(body_text):
        g = m.group(0)
        if g and g[0] in '\r\n':
            line_list.append(body_text[begin:m.start()])
            begin = m.end()
    line_list.append(body_text[begin:])
    return line_list


RX_FUNCTION = re.compile(r'\s*(?:constant\s+)?function\s+(\w+)\s+takes\b')
RX_END_FUNCTION = re.compile(r'\s*endfunction\b')


def functions_protected(tr_dir):
    p = os.path.join(tr_dir, 'intocaveis.json')
    if not os.path.isfile(p):
        return ()
    return tuple(json.load(open(p, encoding='utf-8')).get('functions_protected', ()))


def is_protected(fname, protected):
    return bool(fname) and any(fname == f or (f.endswith('*') and fname.startswith(f[:-1])) for f in protected)


def lines_protected(line_list, protected):
    if not protected:
        return []
    inside, current = [], None
    for line_text in line_list:
        m = RX_FUNCTION.match(line_text)
        if m:
            current = m.group(1)
        inside.append(is_protected(current, protected))
        if RX_END_FUNCTION.match(line_text):
            current = None
    return inside


def extract_txt_text(details, body_text, entries, stats, unknown, tem_text=None, outside=None):
    present = tem_text or cjk_text
    outside = objects_out() if outside is None else outside
    obj = None
    for txt_ln, line_text in enumerate(line_break(body_text)[0]):
        mo = re.match(r'^\[(.+)\]\s*$', line_text)
        if mo:
            obj = mo.group(1)
            continue
        mk = re.match(r'^([A-Za-z0-9_]+)=(.*)$', line_text)
        if not mk:
            continue
        key, val = mk.group(1), mk.group(2)
        if not present(val):
            continue
        kind = TEXT_KEYS_LC.get(key.lower())
        if kind is None:
            unknown[key] += 1
            continue
        if kind == 'skip' or (kind == 'name' and obj in outside):
            continue
        quoted = len(val) >= 2 and val.startswith('"') and val.endswith('"')
        core = val[1:-1] if quoted else val
        entries.append(
            OrderedDict(
                id='obj:%s:%s:%s' % (details.split('/')[-1], obj, key),
                src=details,
                obj=obj,
                key=key,
                kind=kind,
                quoted=quoted,
                comma=(',' in core),
                text=core,
                line=txt_ln,
            )
        )
        stats[details] += 1


def misc_parts(body_text):
    line_list, sep = line_break(body_text)
    if not any('\n' in one_line or '\r' in one_line for one_line in line_list):
        return line_list, sep
    return re.split(r'(\r\n|\n|\r)', body_text), ''


def misc_lines(body_text):
    pieces, sep = misc_parts(body_text)
    if sep:
        return list(enumerate(pieces))
    return [(i, p) for i, p in enumerate(pieces) if i % 2 == 0]


def extract_misc_text(fn, body_text, entries, stats, tem_text=None):
    present = tem_text or cjk_text
    line_list, sections, secao = [], Counter(), ''
    for txt_ln, line_text in misc_lines(body_text):
        ms = re.match(r'^\[(.*)\]\s*$', line_text)
        if ms:
            secao = ms.group(1)
            continue
        mk = re.match(r'^([A-Za-z0-9_]+)=(.*)$', line_text)
        if mk:
            line_list.append((txt_ln, secao, mk))
            sections[mk.group(1)] += 1
    for txt_ln, secao, mk in line_list:
        if present(mk.group(2)):
            hash_key = mk.group(1) if sections[mk.group(1)] == 1 else '%s:%s' % (secao, mk.group(1))
            entries.append(
                OrderedDict(
                    id='misc:%s:%s' % (fn, hash_key),
                    src=fn,
                    obj='',
                    key=mk.group(1),
                    kind='tip',
                    quoted=False,
                    comma=False,
                    text=mk.group(2),
                    line=txt_ln,
                )
            )
            stats[fn] += 1


from doctor.data import object_names
wts_entries = object_names.wts_entries


def extract_wts_text(t, entries, stats, tem_text=None, outside=None):
    present = tem_text or cjk_text
    for mo in wts_entries(t):
        if outside and outside(mo.group(1)):
            continue
        if present(mo.group(2)):
            entries.append(
                OrderedDict(
                    id='wts:%s' % mo.group(1),
                    src='war3map.wts',
                    obj='',
                    key='STRING %s' % mo.group(1),
                    kind='tip',
                    quoted=False,
                    comma=False,
                    text=mo.group(2),
                )
            )
            stats['war3map.wts'] += 1


def extract_script_text(src, entries, stats, protected=(), tem_text=None, multiline=None):
    present = tem_text or cjk_text
    lines = line_break(src, jass=True, multiline=multiline)[0]
    seen = OrderedDict()
    inside = lines_protected(lines, protected)
    outside = set()
    for txt_ln, line_text in enumerate(lines):
        for pos, lit in ki.literals(line_text):
            if not present(lit):
                continue
            if not (inside and inside[txt_ln]):
                outside.add(lit)
            use = ki.classify(line_text, pos, lit)
            ctx = line_text.strip()
            if len(ctx) > 220:
                a = max(0, pos - 90)
                ctx = (
                    ('...' if a else '')
                    + line_text[a : pos + len(lit) + 90].strip()
                    + ('...' if pos + len(lit) + 90 < len(line_text) else '')
                )
            if lit not in seen:
                seen[lit] = OrderedDict(
                    id='j:%d' % len(seen),
                    src='war3map.j',
                    obj='',
                    key='',
                    kind='script',
                    text=lit,
                    count=0,
                    uses=[],
                    contexts=[],
                    lines=[],
                )
            e = seen[lit]
            e['count'] += 1
            if use not in e['uses']:
                e['uses'].append(use)
            if len(e['contexts']) < 2:
                e['contexts'].append(ctx)
            e['lines'].append(txt_ln)
    record = re.compile(r'\|[' + chr(0xAC00) + '-' + chr(0xD7A3) + r']+[0-9.]+\|')
    for lit, e in seen.items():
        if 'comparison' in e['uses'] or 'hash/substring' in e['uses'] or 'chat' in e['uses']:
            e['kind'] = 'command'
        q = '"' + lit + '"'
        if record.search(lit) or any('SubString(' in c and q in c and
                                     re.search(r'SubString\([^)]*\)\s*[=!]=\s*"' + re.escape(lit) + '"', c)
                                     for c in e['contexts']):
            e['kind'] = 'data'
        if protected and lit not in outside:
            e['kind'] = 'data'
            e['datum'] = 'funcao protegida'
        entries.append(e)
    stats['war3map.j (literais unicos)'] = len(seen)
    stats['war3map.j (comandos)'] = sum(1 for e in seen.values() if e['kind'] == 'command')
    if protected:
        stats['war3map.j (so\' em funcao protegida: dado)'] = sum(1 for e in seen.values() if e.get('datum'))
