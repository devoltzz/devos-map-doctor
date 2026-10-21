# Makes the map code that reads the save wait until the saved profiles have arrived.
import re

from doctor.port import dead_type


MARK = '// [KK framework] save_wiring'
RX_READING = re.compile(r'\b(?:RequestExtra\w*Data\s*\(\s*5\s*,|DzAPI_Map_(?:GetServerValue|GetStored\w+|'
                        r'GetServerArchive\w*)\s*\()')
RX_ACTION = re.compile(r'\bTriggerAddAction\s*\(\s*(\w+(?:\[[^\]]*\])?)\s*,\s*function\s+(\w+)\s*\)')
RX_EXEC = re.compile(r'\b(?:ConditionalTriggerExecute|TriggerExecute)\s*\(\s*(\w+(?:\[[^\]]*\])?)\s*\)')
NEUTRAL = {'integer': '0', 'real': '0.0', 'boolean': 'false'}
RX_CALLS = re.compile(r'(?<![\w.])([A-Za-z_]\w*)\s*\(|\bfunction\s+([A-Za-z_]\w*)')
_RX_W = re.compile(r'\w')
_RX_TRIGGER = r'(\w+(?:\[[^\]]*\])?)'
RX_EVENT = re.compile(r'\b\w*TriggerRegister\w*\s*\(\s*' + _RX_TRIGGER + r'\s*,')
RX_TIME = re.compile(r'\bTriggerRegisterTimerEvent(?:Single\s*\(\s*' + _RX_TRIGGER + r'\s*,\s*([\d.]+)\s*\)|\s*\(\s*'
                     + _RX_TRIGGER + r'\s*,\s*([\d.]+)\s*,\s*false\s*\))')
RX_YD_LOCAL = re.compile(r'^\s*local\s+integer\s+(\w+)\s*=\s*LoadInteger\s*\(\s*(\w+)\s*,\s*GetHandleId\s*\(\s*'
                         r'GetTriggeringTrigger\s*\(\s*\)\s*\)\s*,\s*(\w+)\s*\)\s*$')


def clock_triggers(body_text):
    events_of, action_codes, time_limit = {}, {}, {}
    for m in RX_EVENT.finditer(body_text):
        events_of[m.group(1)] = events_of.get(m.group(1), 0) + 1
    for m in RX_ACTION.finditer(body_text):
        action_codes[m.group(1)] = action_codes.get(m.group(1), 0) + 1
    by_hand = set(m.group(1) for m in RX_EXEC.finditer(body_text))
    for m in RX_TIME.finditer(body_text):
        g, s = (m.group(1), m.group(2)) if m.group(1) else (m.group(3), m.group(4))
        try:
            time_limit[g] = float(s)
        except ValueError:
            pass
    return dict(
        (g, s) for g, s in time_limit.items() if events_of.get(g) == 1 and action_codes.get(g) == 1 and g not in by_hand
    )


def _uses(fname, body_text):
    c, n, i = 0, len(fname), body_text.find(fname)
    while i >= 0:
        if not (i and _RX_W.match(body_text[i - 1])) and not (i + n < len(body_text) and _RX_W.match(body_text[i + n])):
            c += 1
        i = body_text.find(fname, i + 1)
    return c


def readers(body_text, fs):
    body = dict((n, body_text[i:f]) for n, i, f in fs)
    name_list = set(body)
    called = dict((n, set(m.group(1) or m.group(2) for m in RX_CALLS.finditer(c.split('\n', 1)[-1])) & name_list)
                  for n, c in body.items())
    read_data = set(n for n, c in body.items() if RX_READING.search(dead_type._without_text(c)))
    changed = True
    while changed:
        changed = False
        for n, cs in called.items():
            if n not in read_data and cs & read_data:
                read_data.add(n)
                changed = True
    return read_data


def _insert(body_text, fs, fname, line_list, prologue=False):
    begin, end_pos = next((i, f) for n, i, f in fs if n == fname)
    body = body_text[begin:end_pos].split('\n')
    k, last = 1, 0
    while k < len(body) and (body[k].strip().startswith(('local ', '//')) or not body[k].strip()):
        if body[k].strip().startswith('local '):
            last = k
        k += 1
    k = last + 1 if last else 1
    while k < len(body) and not body[k].strip():
        k += 1
    nl = '\r' if body[0].endswith('\r') else ''
    after_diag = []
    if prologue:
        m = next((RX_YD_LOCAL.match(line) for line in body[1:k] if RX_YD_LOCAL.match(line)), None)
        if m:
            v, ht, counter_key = m.groups()
            rx_add = re.compile(r'^\s*set\s+%s\s*=\s*%s\s*\+\s*\d+\s*$' % (v, v))
            rx_save = re.compile(r'^\s*call\s+SaveInteger\s*\(\s*%s\s*,\s*GetHandleId\s*\(\s*GetTriggeringTrigger\s*'
                                 r'\(\s*\)\s*\)\s*,\s*(\w+)\s*,\s*%s\s*\)\s*$' % (re.escape(ht), v))
            j = k
            if j < len(body) and rx_add.match(body[j]):
                j += 1
                while j < len(body) and rx_save.match(body[j]):
                    if rx_save.match(body[j]).group(1) != counter_key:
                        after_diag.append(body[j].rstrip('\r'))
                    j += 1
                k = j
    body[k:k] = [line + nl for line in line_list + after_diag]
    return body_text[:begin] + '\n'.join(body) + body_text[end_pos:]


def applies(body_text):
    info = {'readers': 0, 'first_pos': [], 'in_order': [], 'waiting': [], 'kept_list': [], 'failures': []}
    if MARK in body_text:
        return body_text, info
    fs = dead_type.functions(body_text)
    read_data = readers(body_text, fs)
    info['readers'] = len(read_data)
    if not read_data:
        return body_text, info
    action_codes = {}
    for m in RX_ACTION.finditer(body_text):
        action_codes.setdefault(m.group(2), set()).add(m.group(1))
    body = dict((n, body_text[i:f]) for n, i, f in fs)
    at_start = set()
    for n in ('main', 'RunInitializationTriggers', 'InitCustomTriggers'):
        if n in body:
            at_start |= set(m.group(1) for m in RX_EXEC.finditer(body[n]))
    clock_of = clock_triggers(body_text)
    when_of = dict((action_code, min(clock_of[g] for g in gs)) for action_code, gs in action_codes.items()
                   if action_code in body and gs and all(g in clock_of for g in gs))
    action_only = dict(
        (action_code, _uses(action_code, body_text) == 2)
        for action_code in action_codes
        if action_code in read_data or action_code in when_of
    )
    reading = [
        when_of[a] for a in when_of if a in read_data and action_only.get(a) and not (action_codes[a] & at_start)
    ]
    in_order = set(a for a in when_of if reading and when_of[a] >= min(reading) and action_only.get(a)
                   and not (action_codes[a] & at_start))
    insertions = []
    for action_code in sorted(action_codes):
        if (action_code not in read_data and action_code not in in_order) or action_code not in body:
            continue
        m_ret = re.search(r'\breturns\s+(\w+)', body[action_code].split('\n', 1)[0])
        kind = m_ret.group(1) if m_ret else 'nothing'
        out_path = '        return' + ('' if kind == 'nothing' else ' ' + NEUTRAL.get(kind, 'null'))
        prologue = False
        if action_codes[action_code] & at_start:
            line_list = [
                '    if not DB_rede_pronto then ' + MARK + ': the action reads the save; waits for the profiles',
                '        call KK_perfis_depois(GetTriggeringTrigger())',
                out_path,
                '    endif',
            ]
            info['first_pos'].append(action_code)
        elif action_code in in_order:
            line_list = [
                '    if KK_relogio_espera(GetTriggeringTrigger(), %s) then ' % ('%.4f' % when_of[action_code])
                + MARK
                + ': the clock of the start waits for the profiles, in its order and with its gaps',
                out_path,
                '    endif',
            ]
            info['in_order'].append(action_code)
        elif action_only.get(action_code):
            line_list = ['    loop ' + MARK + ': the action reads the save; waits for the profiles in its own thread',
                         '        exitwhen DB_rede_pronto', '        call TriggerSleepAction(0.10)', '    endloop']
            info['waiting'].append(action_code)
            prologue = True
        else:
            line_list = [
                '    if not DB_rede_pronto then '
                + MARK
                + ': the action reads the save; skip until the profiles arrive',
                out_path,
                '    endif',
            ]
            info['kept_list'].append(action_code)
        insertions.append((action_code, line_list, prologue))
    start_of = dict((n, i) for n, i, f in fs)
    for action_code, line_list, prologue in sorted(insertions, key=lambda x: start_of[x[0]], reverse=True):
        body_text = _insert(body_text, fs, action_code, line_list, prologue)
    if insertions:
        fs = dead_type.functions(body_text)
    if 'main' not in body:
        info['failures'].append('the script has no main')
        return body_text, info
    begin, end_pos = next((i, f) for n, i, f in fs if n == 'main')
    main_body = body_text[begin:end_pos]
    k = main_body.rfind('endfunction')
    nl = '\r\n' if '\r\n' in main_body else '\n'
    new_main = (main_body[:k] + '    call TimerStart(CreateTimer(), 0.0, false, function KK_perfis_prepara) ' + MARK +
                ': the profiles start to arrive with the match running' + nl + main_body[k:])
    body_text = body_text[:begin] + new_main + body_text[end_pos:]
    return body_text, info


def report_data(info):
    if info['readers']:
        print('save wiring: %d function(s) read the storage; %d initialization action(s) deferred, %d of the '
              'start clock queued, in order, %d wait in their own thread, %d held until the profiles arrive'
              % (info['readers'], len(info['first_pos']), len(info.get('in_order', ())), len(info['waiting']),
                 len(info['kept_list'])))
    else:
        print('save wiring: the map does not read the platform storage')
