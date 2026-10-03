# Makes the map code that reads the save wait until the saved profiles have arrived.
import re

import dead_type


MARK = '// [KK framework] save_wiring'
RX_READING = re.compile(r'\b(?:RequestExtra\w*Data\s*\(\s*5\s*,|DzAPI_Map_(?:GetServerValue|GetStored\w+|'
                        r'GetServerArchive\w*)\s*\()')
RX_ACTION = re.compile(r'\bTriggerAddAction\s*\(\s*(\w+(?:\[[^\]]*\])?)\s*,\s*function\s+(\w+)\s*\)')
RX_EXEC = re.compile(r'\b(?:ConditionalTriggerExecute|TriggerExecute)\s*\(\s*(\w+(?:\[[^\]]*\])?)\s*\)')
NEUTRAL = {'integer': '0', 'real': '0.0', 'boolean': 'false'}
RX_CALLS = re.compile(r'(?<![\w.])([A-Za-z_]\w*)\s*\(|\bfunction\s+([A-Za-z_]\w*)')


def readers(body_text, fs):
    body = dict((n, body_text[i:f]) for n, i, f in fs)
    name_list = set(body)
    chama = dict((n, set(m.group(1) or m.group(2) for m in RX_CALLS.finditer(c.split('\n', 1)[-1])) & name_list)
                 for n, c in body.items())
    read_data = set(n for n, c in body.items() if RX_READING.search(dead_type._without_text(c)))
    changed = True
    while changed:
        changed = False
        for n, cs in chama.items():
            if n not in read_data and cs & read_data:
                read_data.add(n)
                changed = True
    return read_data


def _insert(body_text, fs, fname, line_list):
    begin, end_pos = next((i, f) for n, i, f in fs if n == fname)
    body = body_text[begin:end_pos].split('\n')
    k = 1
    while k < len(body) and (body[k].strip().startswith('local ') or not body[k].strip()):
        k += 1
    nl = '\r' if body[0].endswith('\r') else ''
    body[k:k] = [line + nl for line in line_list]
    return body_text[:begin] + '\n'.join(body) + body_text[end_pos:]


def applies(body_text):
    info = {'readers': 0, 'first_pos': [], 'esperam': [], 'kept_list': [], 'failures': []}
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
    action_only = dict(
        (action_code, len(re.findall(r'\b%s\b' % re.escape(action_code), body_text)) == 2)
        for action_code in action_codes
    )
    for action_code in sorted(action_codes):
        if action_code not in read_data or action_code not in body:
            continue
        m_ret = re.search(r'\breturns\s+(\w+)', body[action_code].split('\n', 1)[0])
        kind = m_ret.group(1) if m_ret else 'nothing'
        out_path = '        return' + ('' if kind == 'nothing' else ' ' + NEUTRAL.get(kind, 'null'))
        if action_codes[action_code] & at_start:
            line_list = [
                '    if not DB_rede_pronto then ' + MARK + ': the action reads the save; waits for the profiles',
                '        call KK_perfis_depois(GetTriggeringTrigger())',
                out_path,
                '    endif',
            ]
            info['first_pos'].append(action_code)
        elif action_only.get(action_code):
            line_list = ['    loop ' + MARK + ': the action reads the save; waits for the profiles in its own thread',
                         '        exitwhen DB_rede_pronto', '        call TriggerSleepAction(0.10)', '    endloop']
            info['esperam'].append(action_code)
        else:
            line_list = [
                '    if not DB_rede_pronto then '
                + MARK
                + ': the action reads the save; skip until the profiles arrive',
                out_path,
                '    endif',
            ]
            info['kept_list'].append(action_code)
        body_text = _insert(body_text, fs, action_code, line_list)
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
        print('save wiring: %d function(s) read the storage; %d initialization action(s) deferred, %d wait '
              'in its own thread, %d held until the profiles arrive' % (info['readers'], len(info['first_pos']),
                                                                        len(info['esperam']), len(info['kept_list'])))
    else:
        print('save wiring: the map does not read the platform storage')
