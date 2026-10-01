# Extracts the texts of a map for translation.
import json
import os
import re
from collections import OrderedDict


HERE = os.path.dirname(os.path.abspath(__file__))
TR = os.environ.get('TR_DIR') or os.path.join(HERE, 'tr')
import kr_inventory as ki

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


def quebra(body_text, jass=False):
    crlf = body_text.count('\r\n')
    if body_text.count('\r') - crlf > crlf:
        return break_outside_das_quotes(body_text, 'mista'), '\n'
    if jass and literal_multilinha():
        method, sep = ('crlf', '\r\n') if crlf and crlf >= body_text.count('\n') - crlf else ('lf', '\n')
        return break_outside_das_quotes(body_text, method), sep
    sep = '\r\n' if crlf else '\n'
    return body_text.split(sep), sep


_CONFIG = {}


def literal_multilinha(tr_dir=None):
    p = os.path.join(tr_dir or TR, 'config.json')
    if p not in _CONFIG:
        _CONFIG[p] = json.load(open(p, encoding='utf-8')) if os.path.isfile(p) else {}
    return bool(_CONFIG[p].get('literal_multilinha'))


_SEP_MODE = {'mista': r'\r\n|\r|\n', 'crlf': r'\r\n', 'lf': r'\n'}
_COMENTARIO_MODE = {'mista': r'//[^\r\n]*', 'crlf': r'//(?:(?!\r\n).)*', 'lf': r'//[^\n]*'}
_RX_QUOTES_MODE = dict((m, re.compile(_COMENTARIO_MODE[m] + r'|"(?:[^"\\]|\\.)*"|' + _SEP_MODE[m], re.S))
                       for m in _SEP_MODE)


def break_outside_das_quotes(body_text, method='mista'):
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


def e_protegida(fname, protected):
    return bool(fname) and any(fname == f or (f.endswith('*') and fname.startswith(f[:-1])) for f in protected)


def lines_protected(line_list, protected):
    if not protected:
        return []
    inside, current = [], None
    for line_text in line_list:
        m = RX_FUNCTION.match(line_text)
        if m:
            current = m.group(1)
        inside.append(e_protegida(current, protected))
        if RX_END_FUNCTION.match(line_text):
            current = None
    return inside


def extract_txt_text(details, body_text, entries, stats, unknown, tem_text=None):
    present = tem_text or CJK.search
    obj = None
    for ln, line_text in enumerate(quebra(body_text)[0]):
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
        if kind == 'skip':
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
                line=ln,
            )
        )
        stats[details] += 1


def extract_misc_text(fn, body_text, entries, stats, tem_text=None):
    present = tem_text or CJK.search
    for ln, line_text in enumerate(quebra(body_text)[0]):
        mk = re.match(r'^([A-Za-z0-9_]+)=(.*)$', line_text)
        if mk and present(mk.group(2)):
            entries.append(
                OrderedDict(
                    id='misc:%s:%s' % (fn, mk.group(1)),
                    src=fn,
                    obj='',
                    key=mk.group(1),
                    kind='tip',
                    quoted=False,
                    comma=False,
                    text=mk.group(2),
                    line=ln,
                )
            )
            stats[fn] += 1


RX_WTS = re.compile(r'STRING (\d+)\s*(?://[^\n]*\n)?\s*\{\r?\n(.*?)\r?\n\}', re.S)


def extract_wts_text(t, entries, stats, tem_text=None):
    present = tem_text or CJK.search
    for mo in RX_WTS.finditer(t):
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


def extract_script_text(src, entries, stats, protected=(), tem_text=None):
    present = tem_text or CJK.search
    lines = quebra(src, jass=True)[0]
    seen = OrderedDict()
    inside = lines_protected(lines, protected)
    outside = set()
    for ln, line_text in enumerate(lines):
        for pos, lit in ki.literals(line_text):
            if not present(lit):
                continue
            if not (inside and inside[ln]):
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
            e['lines'].append(ln)
    record = re.compile(r'\|[' + chr(0xAC00) + '-' + chr(0xD7A3) + r']+[0-9.]+\|')
    for lit, e in seen.items():
        if 'comparison' in e['uses'] or 'hash/substring' in e['uses'] or 'chat' in e['uses']:
            e['kind'] = 'command'
        if record.search(lit) or any(
            re.search(r'SubString\([^)]*\)\s*[=!]=\s*"' + re.escape(lit) + '"', c) for c in e['contexts']
        ):
            e['kind'] = 'data'
        if protected and lit not in outside:
            e['kind'] = 'data'
            e['datum'] = 'funcao protegida'
        entries.append(e)
    stats['war3map.j (literais unicos)'] = len(seen)
    stats['war3map.j (comandos)'] = sum(1 for e in seen.values() if e['kind'] == 'command')
    if protected:
        stats['war3map.j (so\' em funcao protegida: dado)'] = sum(1 for e in seen.values() if e.get('datum'))
