# Wraps the interface events of the platform so they run only for the local player.
import re


REGISTROS = {
    'DzFrameSetScriptByCode': (3, 2),
    'DzTriggerRegisterMouseEventByCode': (3, 4),
    'DzTriggerRegisterMouseMoveEventByCode': (1, 2),
    'DzTriggerRegisterMouseWheelEventByCode': (1, 2),
    'DzTriggerRegisterKeyEventByCode': (3, 4),
}
PREFIX = 'KK_loc_'
DEFAULT_MARK = '// [KK framework] step 3n: the body only on the machine of whoever acted (the event runs on all)'
RX_EX = re.compile(r'\bDzFrameSetUpdateCallbackByCodeEx\s*\(\s*"(\w+)"\s*\)')
RX_BY_NAME = re.compile(r'\bDzFrameSetScript\s*\(')
RX_LITERAL_NAME = re.compile(r'^\s*"([A-Za-z_]\w*)"\s*$')
RX_INITCT = re.compile(r'(?m)^function InitCustomTriggers takes nothing returns nothing[ \t]*\r?\n')
RX_MAIN = re.compile(r'(?m)^function main takes nothing returns nothing[ \t]*(?:\r\n|\r|\n)')
RX_CODE = re.compile(r'^\s*\(*\s*function\s+(\w+)\s*\)*\s*$')
RX_DEF = re.compile(r'(?m)^[ \t]*function[ \t]+(\w+)[ \t]+takes[ \t]+([^\r\n]*?)[ \t]+returns[ \t]+\w+[ \t]*\r?$')
RX_END = re.compile(r'(?m)^[ \t]*endfunction\b')


def apply_replacements(body_text, replacements):
    replacements = sorted(replacements)
    if any(replacements[i][1] > replacements[i + 1][0] for i in range(len(replacements) - 1)):
        for begin, end_pos, new in reversed(replacements):
            body_text = body_text[:begin] + new + body_text[end_pos:]
        return body_text
    pieces, pos = [], 0
    for begin, end_pos, new in replacements:
        pieces.append(body_text[pos:begin])
        pieces.append(new)
        pos = end_pos
    pieces.append(body_text[pos:])
    return ''.join(pieces)


def on_close(body_text, i):
    level = 0
    n = len(body_text)
    while i < n:
        c = body_text[i]
        if c == '"':
            i += 1
            while i < n and body_text[i] != '"':
                i += 2 if body_text[i] == '\\' else 1
        elif c == "'":
            i += 1
            while i < n and body_text[i] != "'":
                i += 1
        elif c == '(':
            level += 1
        elif c == ')':
            level -= 1
            if level == 0:
                return i
        i += 1
    return -1


def arguments(s):
    args = []
    level = 0
    begin = 0
    i = 0
    n = len(s)
    while i < n:
        c = s[i]
        if c == '"':
            i += 1
            while i < n and s[i] != '"':
                i += 2 if s[i] == '\\' else 1
        elif c == "'":
            i += 1
            while i < n and s[i] != "'":
                i += 1
        elif c in '([':
            level += 1
        elif c in ')]':
            level -= 1
        elif c == ',' and level == 0:
            args.append((begin, i))
            begin = i + 1
        i += 1
    args.append((begin, n))
    return args


def literal_bool(s):
    s = s.strip()
    while s.startswith('(') and s.endswith(')'):
        s = s[1:-1].strip()
    return s if s in ('true', 'false') else None


def _highest_index(i_sync, i_code):
    return max(i for i in (i_sync, i_code) if isinstance(i, int))


def forwarders(body_text, record_count=None, fixed_ones=False):
    record_count = dict(REGISTROS if record_count is None else record_count)
    new_ones = {}
    internal_ones = set()
    while True:
        all_items = dict(record_count, **new_ones)
        rx = re.compile(r'\b(%s)\s*\(' % '|'.join(map(re.escape, all_items)))
        achou = False
        for d in RX_DEF.finditer(body_text):
            fname, params = d.group(1), d.group(2).strip()
            if fname in all_items or params == 'nothing':
                continue
            ps = [p.split() for p in params.split(',')]
            if not all(len(p) == 2 for p in ps):
                continue
            types = dict((p[1], (i, p[0])) for i, p in enumerate(ps))
            end_pos = RX_END.search(body_text, d.end())
            if not end_pos:
                continue
            for m in rx.finditer(body_text, d.end(), end_pos.start()):
                f = on_close(body_text, m.end() - 1)
                if f < 0:
                    continue
                core_part = body_text[m.end():f]
                args = arguments(core_part)
                i_sync, i_code = all_items[m.group(1)]
                if len(args) <= _highest_index(i_sync, i_code):
                    continue
                a_code = core_part[args[i_code][0]:args[i_code][1]].strip()
                if types.get(a_code, (0, ''))[1] != 'code':
                    continue
                if isinstance(i_sync, str):
                    a_sync, fixed_fields = None, i_sync
                else:
                    a_sync = core_part[args[i_sync][0]:args[i_sync][1]].strip()
                    fixed_fields = literal_bool(a_sync)
                if a_sync is not None and types.get(a_sync, (0, ''))[1] == 'boolean':
                    new_ones[fname] = (types[a_sync][0], types[a_code][0])
                elif fixed_ones and fixed_fields == 'false':
                    new_ones[fname] = ('false', types[a_code][0])
                else:
                    continue
                internal_ones.add(m.start())
                achou = True
                break
        if not achou:
            return new_ones, internal_ones


def applies(
    body_text,
    expected_count=None,
    to_report=False,
    mark=DEFAULT_MARK,
    boot_info=True,
    quadro=True,
    fixed_ones=False,
    tolerant_mode=False,
):
    failures = []
    info = {
        'failures': failures,
        'local_vars': 0,
        'functions': 0,
        'synchronous_ones': 0,
        'quadro': 0,
        'boot_info': 0,
        'wrapped': [],
        'by_name': 0,
        'by_name_outside': [],
        'outside': [],
    }
    if 'call DB_ui_boot()' in body_text:
        return body_text, info
    body_text = by_name(body_text, info)
    if not boot_info and re.search(r'(?m)^[ \t]*function[ \t]+%s\w+[ \t]+takes' % re.escape(PREFIX), body_text):
        return body_text, info
    regs, internal_ones = forwarders(body_text, fixed_ones=fixed_ones)
    record_count = dict(REGISTROS, **regs)
    rx_call = re.compile(r'\b(%s)\s*\(' % '|'.join(map(re.escape, record_count)))
    info['forwarders'] = sorted(regs)
    replacements = []
    name_list = []
    for m in rx_call.finditer(body_text):
        start_line = body_text.rfind('\n', 0, m.start()) + 1
        ln = body_text[start_line:m.start()]
        if re.match(r'\s*(native|function)\b', ln) or '//' in ln or m.start() in internal_ones:
            continue
        opens = m.end() - 1
        end_pos = on_close(body_text, opens)
        if end_pos < 0:
            failures.append('unclosed parenthesis in %s (offset %d)' % (m.group(1), m.start()))
            continue
        core_part = body_text[opens + 1:end_pos]
        args = arguments(core_part)
        i_sync, i_code = record_count[m.group(1)]
        if len(args) <= _highest_index(i_sync, i_code):
            failures.append('%s with %d argument(s) (offset %d)' % (m.group(1), len(args), m.start()))
            continue
        sync = i_sync if isinstance(i_sync, str) else literal_bool(core_part[args[i_sync][0]:args[i_sync][1]])
        a0, a1 = args[i_code]
        code = RX_CODE.match(core_part[a0:a1])
        if code is None and core_part[a0:a1].strip() == 'null':
            continue
        if (sync is None or code is None) and tolerant_mode:
            info['outside'].append('%s(%s)' % (m.group(1), core_part[:100]))
            continue
        if sync is None or code is None:
            failures.append('%s without a literal `sync` or without `function X` (offset %d): %s'
                            % (m.group(1), m.start(), core_part[:120]))
            continue
        if sync == 'true':
            info['synchronous_ones'] += 1
            continue
        fname = code.group(1)
        if fname.startswith(PREFIX):
            continue
        replacements.append((opens + 1 + a0, opens + 1 + a1, ' function %s%s' % (PREFIX, fname)))
        if fname not in name_list:
            name_list.append(fname)
        info['local_vars'] += 1
    keys = {}
    for m in (RX_EX.finditer(body_text) if quadro else ()):
        start_line = body_text.rfind('\n', 0, m.start()) + 1
        if re.match(r'\s*function\b', body_text[start_line:m.start()]):
            continue
        fname = m.group(1)
        keys.setdefault(fname, len(keys) + 1)
        replacements.append((m.start(), m.end(), 'DB_quadro_registra(function %s, %d)' % (fname, keys[fname])))
        info['quadro'] += 1
    body_text = apply_replacements(body_text, replacements)
    for fname in name_list:
        rx = re.compile(r'(?m)^[ \t]*function %s takes nothing returns nothing[ \t]*\r?\n' % re.escape(fname))
        matches = list(rx.finditer(body_text))
        booleano = False
        if not matches:
            rx = re.compile(r'(?m)^[ \t]*function %s takes nothing returns boolean[ \t]*\r?\n' % re.escape(fname))
            matches = list(rx.finditer(body_text))
            booleano = bool(matches)
        if len(matches) != 1:
            failures.append('function %s: %d definition(s), expected 1' % (fname, len(matches)))
            continue
        end_pos = re.compile(r'(?m)^[ \t]*endfunction[ \t]*(\r?\n)').search(body_text, matches[0].end())
        if not end_pos:
            failures.append('function %s without endfunction' % fname)
            continue
        nl = end_pos.group(1)
        if booleano:
            body = nl.join([
                mark,
                'function %s%s takes nothing returns boolean' % (PREFIX, fname),
                '\tif GetTriggerPlayer()==GetLocalPlayer() then',
                '\t\treturn %s()' % fname,
                '\tendif',
                '\treturn false',
                'endfunction',
            ]) + nl
        else:
            body = nl.join([
                mark,
                'function %s%s takes nothing returns nothing' % (PREFIX, fname),
                '\tif GetTriggerPlayer()==GetLocalPlayer() then',
                '\t\tcall %s()' % fname,
                '\tendif',
                'endfunction',
            ]) + nl
        body_text = body_text[:end_pos.end()] + body + body_text[end_pos.end():]
        info['functions'] += 1
        info['wrapped'].append(fname)
    matches = list(RX_INITCT.finditer(body_text)) if boot_info else []
    if not boot_info:
        pass
    elif len(matches) > 1:
        failures.append('InitCustomTriggers: %d, expected 1' % len(matches))
    elif matches:
        nl = '\r\n' if matches[0].group().endswith('\r\n') else '\n'
        body_text = body_text[:matches[0].end()] + '\tcall DB_ui_boot()' + nl + body_text[matches[0].end():]
        info['boot_info'] = 1
    else:
        m = RX_MAIN.search(body_text)
        if not m:
            failures.append('without InitCustomTriggers and without main')
        else:
            nl = '\r\n' if m.group().endswith('\r\n') else ('\r' if m.group().endswith('\r') else '\n')
            main_end = re.compile(r'(?m)^endfunction\b').search(body_text, m.end())
            body = body_text[m.end():main_end.start() if main_end else len(body_text)]
            ib = list(re.finditer(r'(?m)^[ \t]*call InitBlizzard\(\)[ \t]*(?:\r\n|\r|\n)', body))
            if len(ib) == 1:
                pos = m.end() + ib[0].end()
            else:
                pos = m.end()
                for lm in re.finditer(r'[^\r\n]*(?:\r\n|\r|\n)', body):
                    if not re.match(r'[ \t]*local\b', lm.group()):
                        break
                    pos = m.end() + lm.end()
            body_text = body_text[:pos] + '\tcall DB_ui_boot()' + nl + body_text[pos:]
            info['boot_info'] = 1
    _registers, internal_end = forwarders(body_text, fixed_ones=True) if fixed_ones else ({}, set())
    for m in rx_call.finditer(body_text):
        start_line = body_text.rfind('\n', 0, m.start()) + 1
        ln = body_text[start_line:m.start()]
        if re.match(r'\s*(native|function)\b', ln) or '//' in ln or m.start() in internal_end:
            continue
        end_pos = on_close(body_text, m.end() - 1)
        core_part = body_text[m.end():end_pos]
        args = arguments(core_part)
        i_sync, i_code = record_count[m.group(1)]
        sync = i_sync if isinstance(i_sync, str) else (
            literal_bool(core_part[args[i_sync][0]:args[i_sync][1]]) if len(args) > i_sync else None)
        if len(args) > _highest_index(i_sync, i_code) and sync == 'false':
            code = RX_CODE.match(core_part[args[i_code][0]:args[i_code][1]])
            if not code and (tolerant_mode or core_part[args[i_code][0]:args[i_code][1]].strip() == 'null'):
                continue
            if not code or not code.group(1).startswith(PREFIX):
                failures.append('local registration WITHOUT wrapper: %s' % core_part[:120])
    for k, v in (expected_count or {}).items():
        if v is not None and info[k] != v:
            failures.append('%s: %d, measured: %d' % (k, info[k], v))
    if to_report and not failures:
        report_data(info)
    return body_text, info


def by_name(body_text, info):
    replacements = []
    trampolines = []
    for m in RX_BY_NAME.finditer(body_text):
        start_line = body_text.rfind('\n', 0, m.start()) + 1
        ln = body_text[start_line:m.start()]
        if re.match(r'\s*(native|function)\b', ln) or '//' in ln:
            continue
        opens = m.end() - 1
        end_pos = on_close(body_text, opens)
        if end_pos < 0:
            info['failures'].append('unclosed parentheses in DzFrameSetScript (offset %d)' % m.start())
            continue
        core_part = body_text[opens + 1:end_pos]
        args = arguments(core_part)
        fname = RX_LITERAL_NAME.match(core_part[args[2][0]:args[2][1]]) if len(args) == 4 else None
        defs = list(re.finditer(r'(?m)^[ \t]*function[ \t]+%s[ \t]+takes[ \t]+nothing\b' % re.escape(fname.group(1)),
                                body_text)) if fname else []
        if len(defs) != 1:
            info['by_name_outside'].append(core_part[:120])
            continue
        tgt = fname.group(1)
        if defs[0].start() > m.start():
            if tgt not in trampolines:
                trampolines.append(tgt)
            tgt = 'KK_nome_' + tgt
        a0, a1 = args[2]
        replacements.append((m.start(), opens + 1 + a0, opens + 1 + a1, tgt))
    for begin, a0, a1, tgt in reversed(replacements):
        body_text = (
            body_text[:begin]
            + 'DzFrameSetScriptByCode('
            + body_text[body_text.index('(', begin) + 1 : a0]
            + ' function '
            + tgt
            + body_text[a1:]
        )
    if trampolines:
        prim = re.search(r'(?m)^[ \t]*function[ \t]+\w+[ \t]+takes\b', body_text)
        nl = '\r\n' if '\r\n' in body_text[:4096] else '\n'
        body = ''.join(nl.join([
            '// [KK framework] step 3n: the frame script by NAME, registered before the function exists',
            'function KK_nome_%s takes nothing returns nothing' % n,
            '\tcall ExecuteFunc("%s")' % n,
            'endfunction']) + nl for n in trampolines)
        body_text = body_text[:prim.start()] + body + body_text[prim.start():]
    info['by_name'] = len(replacements)
    info['trampolines'] = trampolines
    return body_text


def report_data(info):
    print('interface bridge: %d local record(s) wrapped (%d KK_loc_ functions), %d synchronous '
          'untouched, %d per-frame callback(s) by reference, %s'
          % (info['local_vars'], info['functions'], info['synchronous_ones'], info['quadro'],
             'start in InitCustomTriggers' if info['boot_info'] else 'without the interface start (M16 layer)'))
    if info.get('by_name') or info.get('by_name_outside'):
        print(
            '   frame script by NAME: %d converted to the by-code version; %d left (name not literal or '
            'function that does not exist): %s'
            % (info['by_name'], len(info['by_name_outside']), info['by_name_outside'][:3])
        )
