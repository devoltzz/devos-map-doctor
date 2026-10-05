# Renames map globals that clash with names Warcraft III 3.0 defines.
import re

from doctor.port import lbkkapi


RX_GLOBALS = re.compile(r'(?m)^[ \t]*globals[ \t]*\r?$')
RX_ENDGLOBALS = re.compile(r'(?m)^[ \t]*endglobals[ \t]*\r?$')
RX_DECL_LINE = re.compile(
    r'^([ \t]*)(constant[ \t]+)?([A-Za-z_]\w*)[ \t]+(array[ \t]+)?([A-Za-z_]\w*)[ \t]*(=[^\r\n]*)?(\r?)$'
)
REF_CONSTANTS = [set()]
KEYWORDS = {'function', 'endfunction', 'native', 'type', 'globals', 'endglobals', 'local', 'set', 'call', 'return'}


def reference_declarations(ref_text):
    out = {}
    for m_start in RX_GLOBALS.finditer(ref_text):
        m_end = RX_ENDGLOBALS.search(ref_text, m_start.end())
        if not m_end:
            break
        for ln in ref_text[m_start.end():m_end.start()].split('\n'):
            m = RX_DECL_LINE.match(ln.split('//')[0].rstrip())
            if m and m.group(3) not in KEYWORDS:
                out.setdefault(m.group(5), (m.group(3), (m.group(6) or '').lstrip('=').strip()))
    return out


def _rename_global(body_text, name_list):
    name_list = sorted(set(name_list))
    if not name_list:
        return body_text
    rx = re.compile(r'\b(%s)\b' % '|'.join(map(re.escape, name_list)))
    return rx.sub(lambda m: 'kkm_' + m.group(1), body_text)


def applies(body_text, expected_count=None, ref_dir=None):
    info = {'failures': [], 'removed_ones': []}
    m_start = RX_GLOBALS.search(body_text)
    m_end = RX_ENDGLOBALS.search(body_text, m_start.end()) if m_start else None
    if not m_start or not m_end:
        if expected_count:
            info['failures'].append('no globals block, but %d was expected' % expected_count)
        return body_text, info
    ref_text = lbkkapi.read_reference(ref_dir)
    ref = reference_declarations(ref_text)
    REF_CONSTANTS[0] = set(re.findall(r'(?m)^[ \t]*constant[ \t]+\w+[ \t]+(\w+)', ref_text))
    block_entry = body_text[m_start.end():m_end.start()]
    line_list = block_entry.split('\n')
    for k, ln in enumerate(line_list):
        m = RX_DECL_LINE.match(ln)
        if not m or m.group(3) in KEYWORDS or m.group(5) not in ref:
            continue
        kind, fname = m.group(3), m.group(5)
        ref_type, ref_value = ref[fname]
        assigns = re.search(r'(?m)^[ \t]*set[ \t]+%s\b' % re.escape(fname), body_text) and fname in REF_CONSTANTS[0]
        if kind != ref_type or assigns:
            info.setdefault('renamed_list', []).append((fname, kind, ref_type))
            continue
        field_value = (m.group(6) or '').lstrip('=').strip()
        info['removed_ones'].append((fname, kind, field_value, ref_value))
        line_list[k] = ('%s// [KK framework] step 0e: already in common.j 3.0 (%s), removed: %s%s'
                        % (m.group(1), ref_value or 'no value', ln.strip(), m.group(7)))
    body_text = body_text[:m_start.end()] + '\n'.join(line_list) + body_text[m_end.start():]
    body_text = _rename_global(body_text, set(n for n, _t, _r in info.get('renamed_list', [])))
    from_game = set(re.findall(r'(?m)^[ \t]*(?:constant[ \t]+)?native[ \t]+(\w+)', ref_text)) | \
        set(re.findall(r'(?m)^[ \t]*function[ \t]+(\w+)', ref_text))
    functions = sorted(set(re.findall(r'(?m)^[ \t]*function[ \t]+(\w+)[ \t]+takes\b', body_text)) & from_game)
    body_text = _rename_global(body_text, functions)
    if functions:
        info['functions'] = functions
    body_text, res = reserved_names(body_text)
    if res:
        info['functions'] = info.get('functions', []) + ['%s (reserved in pjass)' % r for r in res]
    if expected_count is not None and len(info['removed_ones']) != expected_count:
        info['failures'].append('redeclared globals: %d, measured is %d' % (expected_count, len(info['removed_ones'])))
    return body_text, info


PJASS_RESERVED = ('alias',)


def _code_only(ln, rx, new):
    out, i, n, begin = [], 0, len(ln), 0
    while i < n:
        c = ln[i]
        if c == '"' or c == "'":
            out.append(rx.sub(new, ln[begin:i]))
            k = i + 1
            while k < n and ln[k] != c:
                k += 2 if ln[k] == '\\' else 1
            out.append(ln[i:k + 1])
            i = begin = k + 1
            continue
        if ln.startswith('//', i):
            break
        i += 1
    out.append(rx.sub(new, ln[begin:i]) + ln[i:])
    return ''.join(out)


def reserved_names(body_text):
    hits = [r for r in PJASS_RESERVED if re.search(r'\b%s\b' % r, body_text)]
    if not hits:
        return body_text, []
    rx = re.compile(r'\b(%s)\b' % '|'.join(hits))
    line_list = body_text.split('\n')
    used_entries = set()
    for k, line in enumerate(line_list):
        if rx.search(line):
            new = _code_only(line, rx, r'kkm_\1')
            if new != line:
                used_entries.update(m.group(1) for m in rx.finditer(line))
                line_list[k] = new
    return ('\n'.join(line_list), sorted(used_entries)) if used_entries else (body_text, [])


def report_data(info):
    if info.get('functions'):
        print('0e shadowed: %d map function(s) with the name of a 3.0 one, renamed to kkm_<name>: %s'
              % (len(info['functions']), ', '.join(info['functions'])))
    if info.get('renamed_list'):
        print('0e shadowed: %d map global(s) with the name of a 3.0 one and ANOTHER type, renamed to kkm_<name>: %s'
              % (len(info['renamed_list']), ', '.join('%s (%s x %s)' % x for x in info['renamed_list'])))
    if not info['removed_ones']:
        print('0e shadowed: no map global that common.j 3.0 already declares')
        return
    print('0e shadowed: %d map global(s) that common.j 3.0 already declares, removed (the uses become the '
          'of Reforged): %s' % (len(info['removed_ones']), '; '.join('%s %s: map %s -> 3.0 %s' % (t, n, v, r)
                                                                     for n, t, v, r in info['removed_ones'])))
