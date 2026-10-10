# Renames calls in a script, outside strings and comments.
import re


RX_NATIVE = re.compile(r'^\s*(?:constant\s+)?native\s')


def skip_string(s, i):
    n = len(s)
    k = i + 1
    while k < n:
        c = s[k]
        if c == '\\':
            k += 2
            continue
        if c == '"':
            return k + 1
        k += 1
    return n


def skip_rawcode(s, i):
    j = s.find("'", i + 1)
    if 0 < j - i <= 5:
        return j + 1
    return i + 1


_RX_SITE = re.compile(r'''"(?:[^"\\]|\\[\s\S])*"?|(//)|'[^']{0,4}'|(?<![\w.])(\w+)(?=[ \t]*\()''')
_FILTER_CAP = 32


def sitios(ln, replacements, _matches=_RX_SITE.finditer):
    if len(replacements) <= _FILTER_CAP:
        for k in replacements:
            if k in ln:
                break
        else:
            return []
    out = []
    for m in _matches(ln):
        fname = m.group(2)
        if fname is None:
            if m.group(1) is not None:
                break
            continue
        if fname in replacements and (fname[0] == '_' or fname[0].isalpha()):
            out.append((m.start(), m.end(), fname))
    return out


def pluralize(body_text, replacements):
    r = dict((k, 0) for k in replacements)
    for line in body_text.split('\n'):
        if RX_NATIVE.match(line):
            continue
        if not any(k in line for k in replacements):
            continue
        for _, _, fname in sitios(line, replacements):
            r[fname] += 1
    return r


def applies(body_text, replacements, expected_count=None, to_report=False, label='call swap'):
    line_list = body_text.split('\n')
    by = dict((k, 0) for k in replacements)
    failures = []
    for idx, line in enumerate(line_list):
        if RX_NATIVE.match(line):
            continue
        if not any(k in line for k in replacements):
            continue
        ss = sitios(line, replacements)
        if not ss:
            continue
        for begin, end_pos, fname in sorted(ss, reverse=True):
            line = line[:begin] + replacements[fname] + line[end_pos:]
            by[fname] += 1
        line_list[idx] = line
    swapped = sum(by.values())
    if swapped and expected_count is not None:
        for k, exp_len in expected_count.items():
            if by[k] != exp_len:
                failures.append('%s: %d calls replaced, the count measured in the raw is %d' % (k, by[k], exp_len))
    info = {'by_native': by, 'swapped': swapped, 'failures': failures}
    if failures:
        return body_text, info
    new = '\n'.join(line_list)
    if new.count('\n') != body_text.count('\n'):
        failures.append('the line count changed')
        return body_text, info
    rest = pluralize(new, replacements)
    if any(rest.values()):
        failures.append('calls to the replaced natives remain: %s' % rest)
        return body_text, info
    if to_report:
        report_data(info, label)
    return new, info


def report_data(info, label='call swap'):
    print('%s: %d calls rewritten (%s)'
          % (label, info['swapped'], ', '.join('%s=%d' % (k, v) for k, v in info['by_native'].items())))

