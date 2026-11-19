# The Forsaken race of Reforged 3.0: the war3mapSkin.txt that gives it the Human interface files.
import json
import os
import re


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
TABLE_NAME = os.path.normpath(os.path.join(HERE, '..', 'ref', '3.0', 'skin_forsaken.json'))
SKINS_CACHE = os.path.join(ROOT, 'common', 'cache', 'game_data', 'files', 'war3.w3mod', 'ui', 'war3skins.txt')
NOME = 'war3mapSkin.txt'
ONLY_OF = re.compile(r'forsaken|\\fk-|^ForsakenFK$', re.I)
COMMENT = '// Forsaken race (Reforged 3.0): its interface files are not loaded for this map, the Human ones are used'

_tab = None


def _sections(body_text):
    sec, cur = {}, None
    for ln in body_text.splitlines():
        m = re.match(r'\s*\[([^\]]+)\]', ln)
        if m:
            cur = m.group(1)
            sec.setdefault(cur, {})
            continue
        if cur is None or '=' not in ln or ln.lstrip().startswith('//'):
            continue
        k, v = ln.split('=', 1)
        sec[cur][k.strip()] = v.strip()
    return sec


def gera(war3skins=None):
    file_path = war3skins or SKINS_CACHE
    body_text = open(file_path, encoding='utf-8', errors='replace').read()
    sec = _sections(body_text)
    fk, hu, from_ = sec.get('Forsaken'), sec.get('Human', {}), sec.get('Default', {})
    if not fk:
        raise ValueError('%s: no [Forsaken] section' % file_path)
    forsaken, missing_items = {}, []
    for k, v in fk.items():
        h = hu.get(k, from_.get(k))
        if h is None:
            missing_items.append(k)
        else:
            forsaken[k] = h
    if missing_items:
        raise ValueError('Forsaken keys with no Human or Default value: %s' % missing_items)
    so_de = [k for k, v in fk.items() if ONLY_OF.search(v)]
    return {'fonte': 'war3.w3mod:ui\\war3skins.txt', 'forsaken': forsaken, 'so_de': so_de}


def table():
    global _tab
    if _tab is None:
        _tab = json.load(open(TABLE_NAME, encoding='utf-8'))
    return _tab


def applies(data_bytes):
    t = table()
    body_text = data_bytes.decode('utf-8', 'surrogateescape') if data_bytes else ''
    nl = '\r\n' if ('\r\n' in body_text or not body_text) else '\n'
    sec = _sections(body_text)
    wanted = {'Forsaken': dict(t['forsaken']),
              'CustomSkin': {k: t['forsaken'][k] for k in t['so_de']}}
    missing = {s: [(k, v) for k, v in kv.items() if k not in sec.get(s, {})] for s, kv in wanted.items()}
    if not any(missing.values()):
        return None
    line_list = body_text.split(nl) if body_text else []
    if line_list and line_list[-1] == '':
        line_list.pop()
    for s in ('CustomSkin', 'Forsaken'):
        if not missing[s]:
            continue
        added = [COMMENT] + ['%s=%s' % kv for kv in missing[s]]
        begin = next((i for i, line in enumerate(line_list) if re.match(r'\s*\[%s\]\s*$' % s, line)), None)
        if begin is None:
            if line_list and line_list[-1].strip():
                line_list.append('')
            line_list += ['[%s]' % s] + added
        else:
            end_pos = next(
                (i for i in range(begin + 1, len(line_list)) if re.match(r'\s*\[', line_list[i])), len(line_list)
            )
            while end_pos > begin + 1 and not line_list[end_pos - 1].strip():
                end_pos -= 1
            line_list[end_pos:end_pos] = added
    return (nl.join(line_list) + nl).encode('utf-8', 'surrogateescape')


def from_original(original):
    from doctor.mpq import mpqread
    a = mpqread.Archive(original)
    if not a.hash_entries(NOME):
        return None
    try:
        d = a.read(NOME)
    except Exception as e:
        raise ValueError('%s: %s exists and cannot be read (%s)' % (original, NOME, e))
    if d is None:
        raise ValueError('%s: %s exists and cannot be read' % (original, NOME))
    return d


def _content(v):
    if isinstance(v, (bytes, bytearray)):
        return bytes(v)
    with open(v, 'rb') as f:
        return f.read()


def item(original, item_entries):
    pairs = list(item_entries.items()) if isinstance(item_entries, dict) else list(item_entries)
    current = None
    for n, v in pairs:
        if n.lower() == NOME.lower():
            current = _content(v)
    if current is None:
        current = from_original(original)
    new = applies(current)
    return None if new is None else (NOME, new)


def with_item(original, item_entries, log=None):
    it = item(original, item_entries)
    if it is None:
        return list(item_entries)
    output = [(n, v) for n, v in item_entries if n.lower() != NOME.lower()] + [it]
    if log:
        log('forsaken_skin: %s with the Human interface for the Forsaken race' % NOME)
    return output
