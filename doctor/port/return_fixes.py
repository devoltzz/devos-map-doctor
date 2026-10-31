# Fixes return statements the old compiler accepted and the 3.0 compiler refuses.
import os
import re


RX_CODE_FUNCTION = re.compile(r'^\s*(?:constant\s+)?function\s+\w+\s+takes\s+.*?\s+returns\s+code\s*(?://.*)?$')
RX_NULL_RETURN = re.compile(r'^(\s*return\s+)null(\s*(?://.*)?)$')
RX_FIRST_FUNCTION = re.compile(r'(?m)^[ \t]*(?:constant[ \t]+)?function[ \t]')
VAZIA = 'KKM_codigo_vazio'


def null_code(body_text):
    line_list = body_text.split('\n')
    code, n = False, 0
    for i, txt_ln in enumerate(line_list):
        s = txt_ln.strip()
        if s.startswith('function ') or s.startswith('constant function '):
            code = bool(RX_CODE_FUNCTION.match(txt_ln.rstrip('\r')))
        elif s.startswith('endfunction'):
            code = False
        elif code:
            m = RX_NULL_RETURN.match(txt_ln.rstrip('\r'))
            if m:
                line_list[i] = '%sfunction %s%s%s' % (
                    m.group(1),
                    VAZIA,
                    m.group(2),
                    '\r' if txt_ln.endswith('\r') else '',
                )
                n += 1
    if not n:
        return body_text, 0
    new = '\n'.join(line_list)
    if not re.search(r'(?m)^[ \t]*function[ \t]+%s[ \t]' % VAZIA, new):
        m = RX_FIRST_FUNCTION.search(new)
        nl = '\r\n' if '\r\n' in new else '\n'
        new = new[:m.start()] + 'function %s takes nothing returns nothing%sendfunction%s%s' % (VAZIA, nl, nl, nl) + \
            new[m.start():]
    return new, n


RX_FUNCTION_TYPE = re.compile(r'^\s*(?:constant\s+)?function\s+\w+\s+takes\s+.*?\s+returns\s+(\w+)\s*(?://.*)?$')
RX_EMPTY_RETURN = re.compile(r'^(\s*return)(\s*(?://.*)?)$')
NEUTRAL = {'integer': '0', 'real': '0.0', 'boolean': 'false'}


def empty_return(body_text):
    line_list = body_text.split('\n')
    kind, n = None, 0
    for i, txt_ln in enumerate(line_list):
        s = txt_ln.strip()
        if s.startswith('function ') or s.startswith('constant function '):
            m = RX_FUNCTION_TYPE.match(txt_ln.rstrip('\r'))
            kind = m.group(1) if m and m.group(1) != 'nothing' else None
        elif s.startswith('endfunction'):
            kind = None
        elif kind:
            m = RX_EMPTY_RETURN.match(txt_ln.rstrip('\r'))
            if m:
                line_list[i] = '%s %s%s%s' % (m.group(1), NEUTRAL.get(kind, 'null'), m.group(2),
                                              '\r' if txt_ln.endswith('\r') else '')
                n += 1
    return ('\n'.join(line_list), n) if n else (body_text, 0)


RX_GLOBAL_ARRAY = re.compile(r'(?m)^[ \t]*\w+[ \t]+array[ \t]+(\w+)')
RX_LOCAL = re.compile(r'^[ \t]*local[ \t]+\w+[ \t]+(\w+)')
RX_NOT_CODE = re.compile(r'"(?:[^"\\]|\\.)*"|\'[^\'\n]*\'|//[^\n]*')


def _code_only(rx, ln, repl):
    out, pos = [], 0
    for m in RX_NOT_CODE.finditer(ln):
        out.append(rx.sub(repl, ln[pos:m.start()]))
        out.append(m.group(0))
        pos = m.end()
    out.append(rx.sub(repl, ln[pos:]))
    return ''.join(out)


def _free_local_name(fname, suffix, script_words, in_use):
    new, k = fname + suffix, 1
    while new in script_words or new in in_use:
        k += 1
        new = '%s%s_%d' % (fname, suffix, k)
    in_use.add(new)
    return new


def shadow_local(body_text):
    m_globals = re.search(r'(?m)^[ \t]*globals\b', body_text)
    m_e = re.search(r'(?m)^[ \t]*endglobals\b', body_text)
    if not m_globals or not m_e:
        return body_text, 0
    arrays = set(RX_GLOBAL_ARRAY.findall(body_text[m_globals.end():m_e.start()]))
    if not arrays:
        return body_text, 0
    line_list = body_text.split('\n')
    script_words = None
    n = 0
    i = 0
    while i < len(line_list):
        s = line_list[i].strip()
        if s.startswith('function ') or s.startswith('constant function '):
            j = i + 1
            while j < len(line_list) and not line_list[j].strip().startswith('endfunction'):
                j += 1
            shadows = set()
            for k in range(i + 1, j):
                m = RX_LOCAL.match(line_list[k])
                if m and m.group(1) in arrays:
                    shadows.add(m.group(1))
            if shadows:
                script_words = set(re.findall(r'\w+', body_text)) if script_words is None else script_words
                in_use = set()
                new = dict((x, _free_local_name(x, '_kkl', script_words, in_use)) for x in sorted(shadows))
                rx = re.compile(r'\b(%s)\b' % '|'.join(map(re.escape, sorted(shadows))))
                for k in range(i + 1, j):
                    line_list[k] = _code_only(rx, line_list[k], lambda m: new[m.group(1)])
                n += len(shadows)
            i = j
        i += 1
    return ('\n'.join(line_list), n) if n else (body_text, 0)


RX_FUNC_PARAMS = re.compile(r'^\s*(?:constant\s+)?function\s+\w+\s+takes\s+(.*?)\s+returns\s+\w+')


def local_param_clash(body_text):
    line_list = body_text.split('\n')
    script_words = None
    n = 0
    i = 0
    while i < len(line_list):
        m = RX_FUNC_PARAMS.match(line_list[i])
        if not m:
            i += 1
            continue
        params = set(p.split()[-1] for p in m.group(1).split(',') if p.strip() and p.strip() != 'nothing')
        j = i + 1
        while j < len(line_list) and not line_list[j].strip().startswith('endfunction'):
            j += 1
        dup = set()
        for k in range(i + 1, j):
            mm = RX_LOCAL.match(line_list[k])
            if mm and mm.group(1) in params:
                dup.add(mm.group(1))
        if dup:
            script_words = set(re.findall(r'\w+', body_text)) if script_words is None else script_words
            in_use = set()
            new = dict((x, _free_local_name(x, '_kkl', script_words, in_use)) for x in sorted(dup))
            rx = re.compile(r'\b(%s)\b' % '|'.join(map(re.escape, sorted(dup))))
            seen = set()
            for k in range(i + 1, j):
                line = line_list[k]
                mm = RX_LOCAL.match(line)
                if not mm:
                    line_list[k] = _code_only(rx, line, lambda m: new[m.group(1)])
                    continue
                rest = _code_only(rx, line[mm.end(1):], lambda m: new[m.group(1)] if m.group(1) in seen else m.group(1))
                if mm.group(1) in dup:
                    seen.add(mm.group(1))
                    line_list[k] = line[:mm.start(1)] + new[mm.group(1)] + rest
                else:
                    line_list[k] = line[:mm.end(1)] + rest
            n += len(dup)
        i = j + 1
    return ('\n'.join(line_list), n) if n else (body_text, 0)


RX_LOCAL_NAME = re.compile(r'^[ \t]*local[ \t]+\w+[ \t]+(?:array[ \t]+)?(\w+)')


def repeated_local(body_text):
    line_list = body_text.split('\n')
    script_words = None
    n = 0
    i = 0
    while i < len(line_list):
        if not RX_FUNC_PARAMS.match(line_list[i]):
            i += 1
            continue
        j = i + 1
        while j < len(line_list) and not line_list[j].strip().startswith('endfunction'):
            j += 1
        seen = {}
        for k in range(i + 1, j):
            mm = RX_LOCAL_NAME.match(line_list[k])
            if mm:
                seen[mm.group(1)] = seen.get(mm.group(1), 0) + 1
        repeated = set(fname for fname, q in seen.items() if q > 1)
        if repeated:
            script_words = set(re.findall(r'\w+', body_text)) if script_words is None else script_words
            in_use = set()
            rx = re.compile(r'\b(%s)\b' % '|'.join(map(re.escape, sorted(repeated))))
            current = {}
            count = {}
            for k in range(i + 1, j):
                line = line_list[k]
                mm = RX_LOCAL_NAME.match(line)
                if mm and mm.group(1) in repeated:
                    fname = mm.group(1)
                    count[fname] = count.get(fname, 0) + 1
                    rest = _code_only(rx, line[mm.end(1):], lambda m: m.group(1) + current.get(m.group(1), ''))
                    if count[fname] > 1:
                        current[fname] = _free_local_name(fname, '_kkl%d' % count[fname], script_words, in_use)[
                            len(fname) :
                        ]
                        n += 1
                    line_list[k] = line[:mm.start(1)] + fname + current.get(fname, '') + rest
                elif current:
                    line_list[k] = _code_only(rx, line, lambda m: m.group(1) + current.get(m.group(1), ''))
        i = j + 1
    return ('\n'.join(line_list), n) if n else (body_text, 0)


RX_RETURN_EXPR = re.compile(r'^(\s*return\s+)(\S.*?)(\s*)$')
RX_PJASS_INT_REAL = re.compile(r'^.*?:(\d+):\s*Cannot convert returned value from integer to real')


def _pjass_lines(body_text, rx):
    try:
        from doctor.script import pjass
    except ImportError:
        return []
    if not os.path.isfile(pjass.exe()):
        return []
    import shutil
    import tempfile
    tmp = tempfile.mkdtemp('', 'kk_return_fixes_pjass_')
    try:
        origin = os.path.join(tmp, 'war3map.j')
        with open(origin, 'wb') as f:
            f.write(body_text.encode('utf-8', 'surrogateescape'))
        ref = pjass.default_ref()
        r = pjass.run_action(
            [
                (os.path.join(ref, 'common.j'), 'common.j'),
                (os.path.join(ref, 'blizzard.j'), 'Blizzard.j'),
                (origin, 'war3map.j'),
            ],
            tmp=os.path.join(tmp, 'pjass'),
        )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if r.get('missing'):
        return []
    return sorted(set(int(m.group(1)) for m in (rx.match(line) for line in r['line_list']) if m))


RX_REAL_LITERAL = re.compile(r'^[\s(]*-?[\s(]*(?:\d+\.\d*|\.\d+)[\s)]*$')


def integer_in_real(body_text):
    if not re.search(r'(?m)\breturns[ \t]+real\b', body_text):
        return body_text, 0
    targets = _pjass_lines(body_text, RX_PJASS_INT_REAL)
    if not targets:
        return body_text, 0
    line_list = body_text.split('\n')
    n = 0
    done_names = set()
    for k in targets:
        for i in (k - 1, k - 2):
            if not 0 <= i < len(line_list) or i in done_names:
                continue
            txt_ln = line_list[i]
            cr = '\r' if txt_ln.endswith('\r') else ''
            m = RX_RETURN_EXPR.match(txt_ln.rstrip('\r'))
            if m:
                if RX_REAL_LITERAL.match(m.group(2)) or m.group(2).strip().startswith('I2R('):
                    continue
                if '//' not in m.group(2):
                    line_list[i] = '%sI2R(%s)%s%s' % (m.group(1), m.group(2), m.group(3), cr)
                    done_names.add(i)
                    n += 1
                break
    return ('\n'.join(line_list), n) if n else (body_text, 0)


def applies(body_text):
    from doctor.fix import editor_prep
    body_text, real_blocks = editor_prep.real_literal_return(body_text)
    body_text, empty_files = empty_return(body_text)
    body_text, codes = null_code(body_text)
    body_text, shadows = shadow_local(body_text)
    body_text, param = local_param_clash(body_text)
    body_text, repeated = repeated_local(body_text)
    body_text, i2r = integer_in_real(body_text)
    return body_text, {
        'real_blocks': real_blocks + i2r,
        'codes': codes,
        'shadows': shadows + param + repeated,
        'empty_files': empty_files,
        'repeated': repeated,
    }


def report_data(info):
    if info['real_blocks'] or info['codes'] or info.get('shadows') or info.get('empty_files'):
        print(
            '0g returns: %d `return <integer>` in real function -> real; %d `return` without value -> the neutral of the type; '
            '%d `return null` in code function -> %s; %d local(s) with the name of a global array, of a parameter or '
            'declared again -> <name>_kkl (%d repeated)'
            % (
                info['real_blocks'],
                info.get('empty_files', 0),
                info['codes'],
                VAZIA,
                info.get('shadows', 0),
                info.get('repeated', 0),
            )
        )
