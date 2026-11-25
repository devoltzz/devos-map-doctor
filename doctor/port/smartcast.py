# Rebuilds the SmartCastSystem quick cast of M16 maps with Reforged natives: synced keys and aim.
import contextlib
import io
import json
import os
import re


HERE = os.path.dirname(os.path.abspath(__file__))

MARK = (
    '// [framework KK, issue 104] the SmartCastSystem quick cast on Reforged (smartcast.py; the layer: kk_smartcast.j)'
)
PART = 'kk_smartcast.j'
ORDERS = os.path.join(HERE, 'smartcast_ordens.json')
TABLE_CAP = 3000
KEY_CAP = 16

RX_WANNA = re.compile(r'\b(SmartCastSystem_+)wannaSmartCast\b')
RX_FUNC = re.compile(r'(?m)^[ \t]*(?:constant[ \t]+)?function[ \t]+(\w+)[ \t]+takes\b')
RX_END = re.compile(r'(?m)^[ \t]*endfunction\b')
RX_MAIN = re.compile(r'(?m)^function main takes nothing returns nothing[ \t]*\r?$')
RX_REG = re.compile(r'\bcall[ \t]+DzTriggerRegisterKeyEventByCode[ \t]*\(')
RX_LOCAL = re.compile(r'^[ \t]*local[ \t]+\w+[ \t]+(?:array[ \t]+)?(\w+)')
RX_ID = re.compile(r'[A-Za-z_]\w*')
RX_JN_KEY = re.compile(r'\bJN_OSKEY_([A-Z0-9])\b')
RX_FILTER_LINE = re.compile(r'^(?:(?:if|elseif)\b.*\bthen|else|endif|return)$')
RX_CALLS = re.compile(r'\b(?!(?:if|elseif|and|or|not|then|return)\b)[A-Za-z_]\w*[ \t]*\(')
RX_STRING = re.compile(r'"(?:[^"\\]|\\.)*"')
TYPES = ('NONE', 'ALWAYS', 'SHIFT_DOWN', 'SHIFT_UP')
KEYWORDS = set('if then elseif else endif return not and or true false null'.split())


def _no_comment(line):
    i, n, s = 0, len(line), None
    while i < n:
        c = line[i]
        if c == '"':
            i += 1
            while i < n and line[i] != '"':
                i += 2 if line[i] == '\\' else 1
        elif c == '/' and line[i:i + 2] == '//':
            return line[:i].strip()
        i += 1
    return line.strip()


def _functions(body_text):
    out = []
    pos = 0
    while True:
        m = RX_FUNC.search(body_text, pos)
        if not m:
            return out
        f = RX_END.search(body_text, m.end())
        if not f:
            return out
        end_pos = body_text.find('\n', f.end())
        end_pos = len(body_text) if end_pos < 0 else end_pos
        out.append((m.group(1), m.start(), end_pos))
        pos = end_pos


def _args(body_text, k):
    from doctor.port import statuses
    line_end = body_text.find('\n', k)
    line_end = len(body_text) if line_end < 0 else line_end
    pairs, on_close = statuses.args(body_text[:line_end], k)
    if pairs is None:
        return None, None
    return [body_text[a:b].strip() for a, b in pairs], on_close


def _registrations(body_text, handler):
    out = []
    for m in RX_REG.finditer(body_text):
        a, on_close = _args(body_text, m.end() - 1)
        if not a or len(a) != 5:
            continue
        if re.sub(r'\s+', ' ', a[4]) != 'function ' + handler:
            continue
        out.append((m.start(), on_close + 1, a[1], a[2], a[3]))
    return out


def _local_writer(body_text, funcs, pre):
    from doctor.port import ui_local
    bodies = dict((n, body_text[a:b]) for n, a, b in funcs)
    rx_write = re.compile(r'\b(?:set[ \t]+%sdefaultTriggerType\b|(?:Save|Flush|Remove)\w*[ \t]*\([ \t]*%stable\b)'
                          % (re.escape(pre), re.escape(pre)))
    write = set(n for n, c in bodies.items() if rx_write.search(c))
    if not write:
        return None
    roots = set()
    for m in ui_local.RX_CALL.finditer(body_text):
        isync, icode = ui_local.REGISTROS[m.group(1)]
        a, _f = _args(body_text, m.end() - 1)
        if a and len(a) > max(isync, icode) and a[isync].strip('() ') == 'false':
            cm = re.match(r'^function[ \t]+(\w+)$', a[icode])
            if cm:
                roots.add(cm.group(1))
    rx_name = re.compile(r'\b([A-Za-z_]\w*)[ \t]*\(')
    seen, work_queue = set(), list(roots)
    while work_queue:
        n = work_queue.pop()
        if n in seen or n not in bodies:
            continue
        seen.add(n)
        if n in write:
            return n
        work_queue.extend(x for x in rx_name.findall(bodies[n]) if x in bodies and x not in seen)
    return None


def detect(body_text):
    m = RX_WANNA.search(body_text)
    if not m:
        return None
    pre = m.group(1)
    info = {'prefix': pre, 'handler': None, 'keyvar': None, 'filtro': [], 'always': [], 'record_count': 0,
            'key_codes': [], 'failures': []}
    for g in ('table', 'TABLE_TRIGGER_TYPE_KEY', 'defaultTriggerType'):
        if not re.search(r'(?m)^[ \t]*(?:constant[ \t]+)?\w+[ \t]+%s%s\b' % (re.escape(pre), g), body_text):
            info['failures'].append('the global %s%s is not declared' % (pre, g))
    for t in TYPES:
        if not re.search(r'(?m)^[ \t]*constant[ \t]+integer[ \t]+SmartCastSystem_TRIGGER_TYPE_%s\b' % t, body_text):
            info['failures'].append('the constant SmartCastSystem_TRIGGER_TYPE_%s is not declared' % t)
    rx_arm = re.compile(r'(?m)^[ \t]*set[ \t]+%swannaSmartCast[ \t]*=[ \t]*true\b' % re.escape(pre))
    funcs = _functions(body_text)
    cands = [(n, a, b) for n, a, b in funcs if rx_arm.search(body_text, a, b) and 'DzGetTriggerKey' in body_text[a:b]]
    if len(cands) != 1:
        info['failures'].append('%d function(s) that arm the quick cast with the event key (expected 1)' % len(cands))
        return info
    fname, a, b = cands[0]
    info['handler'] = fname
    body = body_text[a:b].split('\n')
    local_vars = set()
    for line in body:
        lm = RX_LOCAL.match(line)
        if lm:
            local_vars.add(lm.group(1))
    kv = None
    ik = None
    for i, line in enumerate(body):
        km = re.match(r'^[ \t]*set[ \t]+(\w+)[ \t]*=[ \t]*\(*[ \t]*DzGetTriggerKey[ \t]*\([ \t]*\)[ \t]*\)*[ \t]*$',
                      _no_comment(line))
        if km:
            kv, ik = km.group(1), i
            break
    if kv is None:
        info['failures'].append('%s: no `set <key>=DzGetTriggerKey()`' % fname)
        return info
    info['keyvar'] = kv
    others = local_vars - {kv}
    filtro = []
    for line in body[ik + 1:]:
        s = _no_comment(line)
        if not s:
            continue
        if s.startswith(('set ', 'call ', 'local ')) or s == 'endfunction':
            break
        if not RX_FILTER_LINE.match(s) or RX_CALLS.search(RX_STRING.sub('""', s)):
            info['failures'].append('%s: a filter line the step does not understand: %s' % (fname, s[:80]))
            return info
        in_use = set(RX_ID.findall(re.sub(r'"(?:[^"\\]|\\.)*"', '""', s)))
        if in_use & others:
            info['failures'].append('%s: the filter reads the local %s' % (fname, ', '.join(sorted(in_use & others))))
            return info
        filtro.append(s)
    if sum(1 for s in filtro if s.startswith('if ')) != sum(1 for s in filtro if s == 'endif'):
        info['failures'].append('%s: the filter does not close its ifs' % fname)
        return info
    info['filtro'] = filtro
    ss = [_no_comment(line) for line in body]
    ss = [s for s in ss if s]
    for i, s in enumerate(ss[:-1]):
        within = re.match(r'^elseif[ \t]+(.+?)[ \t]+then$', s)
        if not within or not re.match(
            r'^set[ \t]+\w+[ \t]*=[ \t]*\(?[ \t]*SmartCastSystem_TRIGGER_TYPE_ALWAYS[ \t]*\)?$', ss[i + 1]
        ):
            continue
        e = within.group(1)
        in_use = set(RX_ID.findall(e))
        if RX_CALLS.search(RX_STRING.sub('""', e)) or (in_use & others) or kv not in in_use:
            continue
        info['always'].append(e)
    writer = _local_writer(body_text, funcs, pre)
    if writer:
        info['failures'].append('the library type is written from LOCAL code (%s, reached from a registration with '
                                '`false`): the map side reads it in synchronized code' % writer)
    regs = _registrations(body_text, fname)
    info['record_count'] = len(regs)
    letters = set()
    for begin, end_pos, key_char, status, sync in regs:
        if status.strip('() ') != '1':
            info['failures'].append('registration with status %s (only the press, 1, is understood)' % status)
        lm = RX_JN_KEY.fullmatch(key_char.strip('() '))
        nm = re.fullmatch(r'(?:\$|0[xX])([0-9A-Fa-f]+)|(\d+)', key_char.strip('() '))
        if lm:
            letters.add(lm.group(1))
        elif nm and 0x30 <= int(nm.group(1) or nm.group(2), 16 if nm.group(1) else 10) <= 0x5A:
            letters.add(chr(int(nm.group(1) or nm.group(2), 16 if nm.group(1) else 10)))
        else:
            for n2, a2, b2 in funcs:
                if a2 <= begin < b2:
                    letters.update(RX_JN_KEY.findall(body_text[a2:b2]))
    info['key_codes'] = sorted(letters)
    if regs and not letters:
        info['failures'].append('the keys the library registers cannot be read in the script (no `JN_OSKEY_<K>`)')
    if len(letters) > KEY_CAP:
        info['failures'].append('%d keys (the layer keeps up to %d)' % (len(letters), KEY_CAP))
    return info


def _fourcc_ok(s):
    return isinstance(s, str) and len(s) == 4 and all(0x21 <= ord(c) <= 0x7e and c not in '\'\\' for c in s)


def table(extract, key_codes):
    if not extract or not os.path.isdir(extract):
        return []
    from doctor.port import slk_tables
    ordens = json.load(open(ORDERS, encoding='utf-8'))['ordens']
    with contextlib.redirect_stdout(io.StringIO()):
        _mode_of, _u, abils, _i = slk_tables.build_auto_tables(extract)
    letters = set(key_codes)
    out = []
    for aid, d in abils.items():
        if not _fourcc_ok(aid):
            continue
        hk = (d.get('hotkey') or '').strip().strip('"').split(',')[0].strip().upper()
        if len(hk) != 1 or hk not in letters:
            continue
        code = (d.get('code') or aid).strip().strip('"')
        if code == 'ANcl':
            order = ''
        else:
            order = ordens.get(code) or (d.get('order') or '').strip().strip('"')
            if not order or not re.match(r'^\w+$', order):
                continue
        out.append((aid, ord(hk), order))
    if 'A' in letters and not any(a == 'Aatk' for a, _k, _o in out):
        out.append(('Aatk', ord('A'), 'attack'))
    return sorted(out)[:TABLE_CAP]


def _glue(info, tab, nl):
    kv = info['keyvar']
    pre = info['prefix']
    L = [MARK,
         '// the key FILTER of the library (copied from `%s`): LOCAL, reads the switches of the player of this machine'
         % info['handler'],
         'function KKSC_mapa_filtro takes integer %s returns boolean' % kv]
    for s in info['filtro']:
        L.append('    ' + ('return false' if s == 'return' else s))
    L += [
        '    return true',
        'endfunction',
        '',
        '// the key that is ON forces the ALWAYS type (the ARS variant); `false` without it',
        'function KKSC_mapa_sempre takes integer %s returns boolean' % kv,
        '    return %s' % (' or '.join('(%s)' % e for e in info['always']) if info['always'] else 'false'),
        'endfunction',
        '',
        '// LOCAL (the layer evaluates it on every machine every 0.03 s): the mask of the keys of the local player that are on',
        'function KKSC_mapa_mascara takes nothing returns boolean',
        '    local integer i=0',
        '    set KKSC_ml=0',
        '    set KKSC_ms=0',
        '    loop',
        '        exitwhen i>=KKSC_nt',
        '        if KKSC_mapa_filtro(KKSC_tecla[i]) then',
        '            set KKSC_ml=KKSC_ml+KKSC_pot[i]',
        '            if KKSC_mapa_sempre(KKSC_tecla[i]) then',
        '                set KKSC_ms=KKSC_ms+KKSC_pot[i]',
        '            endif',
        '        endif',
        '        set i=i+1',
        '    endloop',
        '    return false',
        'endfunction',
        '',
        'function KKSC_mapa_tipo_n takes integer t returns integer',
        '    if t==SmartCastSystem_TRIGGER_TYPE_ALWAYS then',
        '        return 1',
        '    elseif t==SmartCastSystem_TRIGGER_TYPE_SHIFT_DOWN then',
        '        return 2',
        '    elseif t==SmartCastSystem_TRIGGER_TYPE_SHIFT_UP then',
        '        return 3',
        '    endif',
        '    return 0',
        'endfunction',
        '',
        '// SYNCHRONIZED: the type of the ability `KKSC_q_hab` from the library table (-1 = no entry: the default in',
        '// `KKSC_q_padrao`, the layer decides with the key that forces ALWAYS)',
        'function KKSC_mapa_tipo takes nothing returns boolean',
        '    if HaveSavedInteger(%stable, KKSC_q_hab, %sTABLE_TRIGGER_TYPE_KEY) then' % (pre, pre),
        '        set KKSC_q_tipo=KKSC_mapa_tipo_n(LoadInteger(%stable, KKSC_q_hab, %sTABLE_TRIGGER_TYPE_KEY))'
        % (pre, pre),
        '    else',
        '        set KKSC_q_tipo=-1',
        '        set KKSC_q_padrao=KKSC_mapa_tipo_n(%sdefaultTriggerType)' % pre,
        '    endif',
        '    return false',
        'endfunction',
        '',
        '// SYNCHRONIZED (at the layer start): the abilities of each key, from the map data (%d)' % len(tab),
        'function KKSC_mapa_tabela takes nothing returns boolean',
    ]
    for aid, k, order in tab:
        L.append("    call KKSC_hab('%s', %d, \"%s\")" % (aid, k, order))
    L += ['    return false', 'endfunction', '']
    return nl.join(L) + nl


def applies(body_text, extract=None):
    info = {'failures': [], 'done': False, 'existing': False, 'record_count': 0, 'table': 0, 'key_codes': []}
    if MARK in body_text:
        info['existing'] = True
        return body_text, info
    d = detect(body_text)
    if d is None:
        info['failures'].append('the script does not have the SmartCastSystem library')
        return body_text, info
    info.update((k, d[k]) for k in ('prefix', 'handler', 'key_codes', 'filtro', 'always'))
    info['record_count'] = d['record_count']
    if d['failures']:
        info['failures'] += d['failures']
        return body_text, info
    if not d['record_count']:
        info['failures'].append('the library registers no key (the map brought it turned off)')
        return body_text, info
    nl = '\r\n' if '\r\n' in body_text[:20000] else '\n'
    m = list(RX_MAIN.finditer(body_text))
    if len(m) != 1:
        info['failures'].append('%d function main, expected 1' % len(m))
        return body_text, info
    tab = table(extract, d['key_codes'])
    info['table'] = len(tab)
    regs = _registrations(body_text, d['handler'])
    pieces, pos = [], 0
    for begin, end_pos, key_char, _st, _sy in regs:
        pieces.append(body_text[pos:begin])
        pieces.append('call DoNothing()')
        pos = end_pos
    pieces.append(body_text[pos:])
    t = ''.join(pieces)
    m = list(RX_MAIN.finditer(t))
    begin = m[0].start()
    end_pos = t.find(nl + 'endfunction', m[0].end())
    if end_pos < 0:
        info['failures'].append('main without endfunction')
        return body_text, info
    step_on = ''.join(nl + '    call KKSC_registra(%d)' % ord(c) for c in d['key_codes'])
    step_on += (nl + '    call KKSC_liga(Condition(function KKSC_mapa_mascara), Condition(function KKSC_mapa_tipo), '
                'Condition(function KKSC_mapa_tabela))')
    t = t[:begin] + _glue(d, tab, nl) + t[begin:end_pos] + step_on + t[end_pos:]
    if _registrations(t, d['handler']):
        info['failures'].append('a key registration for %s is left' % d['handler'])
        return body_text, info
    info['done'] = True
    return t, info


def report_data(info):
    if info.get('existing'):
        print('7d smartcast: already applied')
    elif info.get('done'):
        print(
            '7d smartcast: %d key registration(s) -> DoNothing, keys %s at the end of main, filter of %d line(s) from %s, %s; '
            '%d ability(ies) in the table'
            % (
                info['record_count'],
                ''.join(info['key_codes']),
                len(info['filtro']),
                info['handler'],
                'key on = ALWAYS' if info['always'] else 'type from the library table',
                info['table'],
            )
        )
    else:
        print('7d smartcast: NOT applied: %s' % '; '.join(info['failures']))

