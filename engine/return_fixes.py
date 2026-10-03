# Fixes return statements the old compiler accepted and the 3.0 compiler refuses.
import re


RX_CODE_FUNCTION = re.compile(r'^\s*(?:constant\s+)?function\s+\w+\s+takes\s+.*?\s+returns\s+code\s*(?://.*)?$')
RX_NULL_RETURN = re.compile(r'^(\s*return\s+)null(\s*(?://.*)?)$')
RX_FIRST_FUNCTION = re.compile(r'(?m)^[ \t]*(?:constant[ \t]+)?function[ \t]')
VAZIA = 'KKM_codigo_vazio'


def null_code(body_text):
    line_list = body_text.split('\n')
    code, n = False, 0
    for i, ln in enumerate(line_list):
        s = ln.strip()
        if s.startswith('function ') or s.startswith('constant function '):
            code = bool(RX_CODE_FUNCTION.match(ln.rstrip('\r')))
        elif s.startswith('endfunction'):
            code = False
        elif code:
            m = RX_NULL_RETURN.match(ln.rstrip('\r'))
            if m:
                line_list[i] = '%sfunction %s%s%s' % (m.group(1), VAZIA, m.group(2), '\r' if ln.endswith('\r') else '')
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
    for i, ln in enumerate(line_list):
        s = ln.strip()
        if s.startswith('function ') or s.startswith('constant function '):
            m = RX_FUNCTION_TYPE.match(ln.rstrip('\r'))
            kind = m.group(1) if m and m.group(1) != 'nothing' else None
        elif s.startswith('endfunction'):
            kind = None
        elif kind:
            m = RX_EMPTY_RETURN.match(ln.rstrip('\r'))
            if m:
                line_list[i] = '%s %s%s%s' % (m.group(1), NEUTRAL.get(kind, 'null'), m.group(2),
                                              '\r' if ln.endswith('\r') else '')
                n += 1
    return ('\n'.join(line_list), n) if n else (body_text, 0)


RX_GLOBAL_ARRAY = re.compile(r'(?m)^[ \t]*\w+[ \t]+array[ \t]+(\w+)')
RX_LOCAL = re.compile(r'^[ \t]*local[ \t]+\w+[ \t]+(\w+)')


def shadow_local(body_text):
    m_globals = re.search(r'(?m)^[ \t]*globals\b', body_text)
    m_e = re.search(r'(?m)^[ \t]*endglobals\b', body_text)
    if not m_globals or not m_e:
        return body_text, 0
    arrays = set(RX_GLOBAL_ARRAY.findall(body_text[m_globals.end():m_e.start()]))
    if not arrays:
        return body_text, 0
    line_list = body_text.split('\n')
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
                rx = re.compile(r'\b(%s)\b' % '|'.join(map(re.escape, sorted(shadows))))
                for k in range(i + 1, j):
                    line_list[k] = rx.sub(r'\1_kkl', line_list[k])
                n += len(shadows)
            i = j
        i += 1
    return ('\n'.join(line_list), n) if n else (body_text, 0)


def applies(body_text):
    import editor_prep
    body_text, real_blocks = editor_prep.real_literal_return(body_text)
    body_text, empty_files = empty_return(body_text)
    body_text, codes = null_code(body_text)
    body_text, shadows = shadow_local(body_text)
    return body_text, {'real_blocks': real_blocks, 'codes': codes, 'shadows': shadows, 'empty_files': empty_files}


def report_data(info):
    if info['real_blocks'] or info['codes'] or info.get('shadows') or info.get('empty_files'):
        print(
            '0g returns: %d `return <integer>` in real function -> real; %d `return` without value -> the neutral of the type; '
            '%d `return null` in code function -> %s; %d local(s) with the name of a global array -> <name>_kkl'
            % (info['real_blocks'], info.get('empty_files', 0), info['codes'], VAZIA, info.get('shadows', 0))
        )
