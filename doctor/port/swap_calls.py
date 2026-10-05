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


def sitios(ln, replacements):
    out = []
    n = len(ln)
    i = 0
    while i < n:
        c = ln[i]
        if c == '"':
            i = skip_string(ln, i)
            continue
        if c == '/' and ln.startswith('//', i):
            break
        if c == "'":
            i = skip_rawcode(ln, i)
            continue
        if (c.isalpha() or c == '_') and (i == 0 or not (ln[i - 1].isalnum() or ln[i - 1] in '_.')):
            j = i + 1
            while j < n and (ln[j].isalnum() or ln[j] == '_'):
                j += 1
            fname = ln[i:j]
            if fname in replacements:
                k = j
                while k < n and ln[k] in ' \t':
                    k += 1
                if k < n and ln[k] == '(':
                    out.append((i, j, fname))
            i = j
            continue
        i += 1
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

