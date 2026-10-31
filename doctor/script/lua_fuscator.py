# Takes the WC3Fuscator loader layers off a Lua script without running the map.
import re

from doctor.script.lua_obfuscate import ALPHABET_B64, b64_decode, lehmer_key, add_key


MARKER = '-- Protected with WC3Fuscator V2.1. Do not edit.'
LOADER_MAX = 4000
MAX_LAYERS = 16
_ID = r'[A-Za-z_]\w*'
RX_LEHMER = re.compile(r'local\s+(%s)\s*=\s*(\d+)\s+for\s+%s\s*=\s*1\s*,\s*(\d+)\s+do\s+\1\s*=\s*\(\s*\1\s*\*\s*75\s*'
                       r'\+\s*74\s*\)\s*%%\s*65537' % (_ID, _ID))
RX_B64 = re.compile(r'local\s+(%s)\s*=\s*"([A-Za-z0-9+/]*={0,2})"' % _ID)
RX_KEY_USE = re.compile(r'(%s)\s*\[\s*\(\s*\(\s*%s\s*-\s*1\s*\)\s*%%\s*(%s|\d+)\s*\)\s*\+\s*1\s*\]' % (_ID, _ID, _ID))
RX_XOR = re.compile(r'local\s+function\s+(%s)\s*\(\s*(%s)\s*,\s*(%s)\s*\)\s*local\s+(%s)\s*,\s*(%s)\s*=\s*0\s*,\s*1\s+'
                    r'for\s+%s\s*=\s*1\s*,\s*8\s+do\s+local\s+(%s)\s*,\s*(%s)\s*=\s*\2\s*%%\s*2\s*,\s*\3\s*%%\s*2\s+'
                    r'if\s+\6\s*~=\s*\7\s+then\s+\4\s*=\s*\4\s*\+\s*\5' % ((_ID,) * 8))
RX_OUT_XOR = re.compile(r'string\.char\(\s*(%s)\s*\(' % _ID)
RX_OUT_SUB = re.compile(r'string\.char\(\s*\(\s*%s\s*\[\s*%s\s*\]\s*-\s*%s\s*\[' % (_ID, _ID, _ID))
RX_OUT_ADD = re.compile(r'string\.char\(\s*\(\s*%s\s*\[\s*%s\s*\]\s*\+\s*%s\s*\[' % (_ID, _ID, _ID))
RX_RUN = re.compile(
    r'local\s+(%s)\s*=\s*assert\s*\(\s*\(\s*loadstring\s+or\s+load\s*\)\s*\(\s*table\.concat\s*\(\s*%s\s*\)'
    r'[^)]*\)\s*\)\s*(?:\1\s*\(\s*\)|return\s+\1\s*\(\s*\.\.\.\s*\))\s*;?' % (_ID, _ID)
)
RX_TABLE = r'local\s+%s\s*=\s*\{\s*(\d+(?:\s*,\s*\d+)*)\s*,?\s*\}'
RX_COMMENTS = re.compile(r'\A(?:\s|--(?!\[=*\[)[^\n]*\n?)*')
RX_LONG_COMMENT = re.compile(r'--\[(=*)\[.*?\]\1\]|--[^\r\n]*', re.S)
RX_RENAMED = re.compile(r'(?<![\w.:])__L(\d+)\b')


def _text(datum):
    return datum.decode('latin-1') if isinstance(datum, (bytes, bytearray)) else datum


def detect(body_text):
    t = _text(body_text)
    if 'loadstring' not in t or ALPHABET_B64 not in t or len(t) > 400_000_000:
        return None
    body_start = RX_COMMENTS.match(t).end()
    m_run = RX_RUN.search(t)
    if not m_run:
        return None
    cands = [m for m in RX_B64.finditer(t, body_start, m_run.start()) if m.group(2) != ALPHABET_B64]
    if not cands:
        return None
    pay = max(cands, key=lambda m: len(m.group(2)))
    if ('#' + pay.group(1)) not in t.replace(' ', ''):
        return None
    use_of = RX_KEY_USE.search(t, pay.end(), m_run.start())
    if not use_of:
        return None
    k_name = use_of.group(1)
    xor = RX_XOR.search(t, body_start, m_run.start())
    out_x = RX_OUT_XOR.search(t, pay.end(), m_run.start())
    if xor and out_x and out_x.group(1) == xor.group(1):
        family, op = 'wc3fuscator', 'xor'
    elif RX_OUT_SUB.search(t, pay.end(), m_run.start()):
        family, op = 'layered_loader', 'sub'
    elif RX_OUT_ADD.search(t, pay.end(), m_run.start()):
        family, op = 'layered_loader', 'add'
    else:
        return None
    m_l = RX_LEHMER.search(t, body_start, m_run.start())
    if m_l:
        jpeg_seed, n = int(m_l.group(2)), int(m_l.group(3))
        if not (0 < n <= 4096):
            return None
        hash_key, origin = lehmer_key(jpeg_seed, n), 'lehmer'
    else:
        m_t = re.search(RX_TABLE % re.escape(k_name), t[body_start:m_run.start()])
        if not m_t:
            return None
        hash_key = [int(x) for x in re.split(r'\s*,\s*', m_t.group(1))]
        if not hash_key or any(not 0 <= x <= 255 for x in hash_key):
            return None
        jpeg_seed, n, origin = None, len(hash_key), 'literal (not checked on a real map)'
    starts = [pay.start()] + [m.start() for m in (m_l, xor, re.compile(r'local\s+%s\s*=\s*\{' % re.escape(k_name))
                                                    .search(t, body_start, m_run.start())) if m]
    return {'family': family, 'op': op, 'key': origin, 'seed': jpeg_seed, 'key_len': n, 'key_bytes': hash_key,
            'payload': pay.group(2), 'marker': MARKER in t[:body_start + len(MARKER) + 2],
            'start': body_start, 'loader_start': min(starts), 'end': m_run.end()}


def _open(d):
    data_bytes = b64_decode(d['payload'])
    hash_key = d['key_bytes']
    if d['op'] == 'xor':
        n = len(hash_key)
        return bytes(b ^ hash_key[i % n] for i, b in enumerate(data_bytes))
    return add_key(data_bytes, hash_key, -1 if d['op'] == 'sub' else 1)


def _parse_error(b):
    from doctor.script import lua_ast
    try:
        lua_ast.parse(b.decode('latin-1'))
        return None
    except Exception as e:
        return '%s: %s' % (type(e).__name__, str(e)[:200])


def peel(body_text, check_parse=True):
    was_bytes = isinstance(body_text, (bytes, bytearray))
    current = bytes(body_text) if was_bytes else body_text.encode('utf-8', 'surrogateescape')
    details = {
        'ok': False,
        'layers': [],
        'family': None,
        'renamed_locals': 0,
        'marker': False,
        'notes': [],
        'error': None,
    }
    for _ in range(MAX_LAYERS):
        t = current.decode('latin-1')
        d = detect(t)
        if d is None:
            break
        after_diag = len(t[d['end']:].strip())
        before = len(RX_LONG_COMMENT.sub('', t[d['start']:d['loader_start']]).strip().lstrip('\xef\xbb\xbf﻿')
                     .strip())
        if after_diag or before or (d['end'] - d['start']) - len(d['payload']) > LOADER_MAX:
            details['error'] = 'layer %d: other code around the loader (%d bytes); not peeled' % (
                len(details['layers']) + 1, after_diag or before or (d['end'] - d['start']) - len(d['payload']))
            break
        plaintext = _open(d)
        if check_parse:
            err = _parse_error(plaintext)
            if err:
                details['error'] = 'layer %d: the decoded text does not parse as Lua (%s); not peeled' % (
                    len(details['layers']) + 1, err)
                break
        details['layers'].append({'family': d['family'], 'cipher': d['op'], 'key': d['key'], 'seed': d['seed'],
                                  'key_len': d['key_len'], 'in_bytes': len(current), 'out_bytes': len(plaintext),
                                  'marker': d['marker']})
        details['family'] = details['family'] or d['family']
        details['marker'] = details['marker'] or d['marker']
        current = plaintext
    else:
        details['error'] = 'more than %d layers; stopped' % MAX_LAYERS
    details['ok'] = bool(details['layers']) and details['error'] is None
    final = current.decode('latin-1')
    details['renamed_locals'] = len(set(RX_RENAMED.findall(final))) if details['family'] == 'wc3fuscator' else 0
    details['notes'] = _notes(details)
    return (current if was_bytes else current.decode('utf-8', 'surrogateescape')), details


def _notes(details):
    if not details['layers']:
        return [details['error']] if details['error'] else []
    n = len(details['layers'])
    if details['family'] == 'wc3fuscator':
        out = ['The Lua script was obfuscated by WC3Fuscator 2.1: layers peeled: %d (the key is in the loader).' % n,
               'Strings, numbers, globals and comments are back as they were.']
        if details['renamed_locals']:
            out.append('%d local names stay as __L0..__L%d: WC3Fuscator does not keep the original names, so they '
                       'cannot come back.' % (details['renamed_locals'], details['renamed_locals'] - 1))
    else:
        out = ['The Lua script was wrapped in loader layers of the WC3Fuscator kind (additive cipher, the one '
               'DevoProtect uses): layers peeled: %d.' % n,
               'The code inside is still minified, with renamed names and encrypted strings.']
    if details['error']:
        out.append('Stopped: %s.' % details['error'])
    return out
