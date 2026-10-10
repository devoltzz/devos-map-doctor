# Rewrites the unit state calls of the platform API that Warcraft III 3.0 does not have.
import re

from doctor.port import swap_calls as T


KNOWN_NAMES = {'SetUnitState': 1, 'GetUnitState': 1, 'GetUnitStateSwap': 1}
RX_CONVERT = re.compile(r'^ConvertUnitState\(\s*(0[xX][0-9A-Fa-f]+|\$[0-9A-Fa-f]+|\d+)\s*\)$')
LABEL_TEXT = 'japi states -> part_14'


def args(ln, k):
    max_depth = 0
    i = k
    begin = k + 1
    out = []
    n = len(ln)
    while i < n:
        c = ln[i]
        if c == '"':
            i = T.skip_string(ln, i)
            continue
        if c == "'":
            i = T.skip_rawcode(ln, i)
            continue
        if c == '(':
            max_depth += 1
        elif c == ')':
            max_depth -= 1
            if max_depth == 0:
                out.append((begin, i))
                return out, i
        elif c == ',' and max_depth == 1:
            out.append((begin, i))
            begin = i + 1
        i += 1
    return None, None


RX_CONSTANT = re.compile(
    r'(?m)^[ \t]*constant[ \t]+unitstate[ \t]+(\w+)[ \t]*=[ \t]*(ConvertUnitState\([^()\n]*\))[ \t]*$'
)


def w3p_constants(body_text):
    if 'unitstate' not in body_text:
        return {}
    return dict((m.group(1), m.group(2)) for m in RX_CONSTANT.finditer(body_text) if RX_CONVERT.match(m.group(2)))


def classify_items(fname, st, consts=None):
    st = st.strip()
    if consts and st in consts:
        st = consts[st]
    m = RX_CONVERT.match(st)
    if m:
        x = m.group(1)
        if x[:2].lower() == '0x':
            n = int(x, 16)
        elif x[0] == '$':
            n = int(x[1:], 16)
        elif len(x) > 1 and x[0] == '0':
            try:
                n = int(x, 8)
            except ValueError:
                return None, None
        else:
            n = int(x)
        return ('%s 0x%X' % ('set' if fname == 'SetUnitState' else 'get', n)), '0x%X' % n
    if fname == 'SetUnitState' and st == 'UNIT_STATE_MAX_LIFE':
        return 'set MAX_LIFE', None
    if fname == 'SetUnitState' and st == 'UNIT_STATE_MAX_MANA':
        return 'set MAX_MANA', None
    return None, None


def rewrite_line(line, by, failures, no, consts=None):
    ss = T.sitios(line, KNOWN_NAMES)
    for begin, end_pos, fname in sorted(ss, reverse=True):
        k = line.index('(', end_pos)
        a, on_close = args(line, k)
        if a is None:
            failures.append('line %d: %s does not close on the line' % (no, fname))
            continue
        if len(a) != (3 if fname == 'SetUnitState' else 2):
            failures.append('line %d: %s with %d arguments' % (no, fname, len(a)))
            continue
        if fname == 'GetUnitStateSwap':
            cat, new_st = classify_items(fname, line[a[0][0]:a[0][1]], consts)
            if cat is None:
                continue
            by[cat] = by.get(cat, 0) + 1
            line = (
                line[:begin]
                + 'DB_estado_le('
                + line[a[1][0] : a[1][1]].strip()
                + ', '
                + new_st
                + ')'
                + line[on_close + 1 :]
            )
            continue
        cat, new_st = classify_items(fname, line[a[1][0]:a[1][1]], consts)
        if cat is None:
            continue
        by[cat] = by.get(cat, 0) + 1
        if cat == 'set MAX_LIFE' or cat == 'set MAX_MANA':
            tgt = 'DB_estado_max_vida' if cat == 'set MAX_LIFE' else 'DB_estado_max_mana'
            line = line[:begin] + tgt + line[end_pos:a[0][1]] + line[a[1][1]:]
        else:
            tgt = 'DB_estado_set' if fname == 'SetUnitState' else 'DB_estado_le'
            start_state, end_st = a[1]
            lead = len(line[start_state:end_st]) - len(line[start_state:end_st].lstrip())
            line = line[:begin] + tgt + line[end_pos:start_state + lead] + new_st + line[end_st:]
    return line


def pluralize(body_text):
    by = {}
    failures = []
    consts = w3p_constants(body_text)
    for no, line in enumerate(body_text.split('\n'), 1):
        if T.RX_NATIVE.match(line) or 'UnitState' not in line:
            continue
        rewrite_line(line, by, failures, no, consts)
    return by


def applies(body_text, expected_count=None, to_report=False):
    line_list = body_text.split('\n')
    by = {}
    failures = []
    consts = w3p_constants(body_text)
    for idx, line in enumerate(line_list):
        if T.RX_NATIVE.match(line) or 'UnitState' not in line:
            continue
        new_l = rewrite_line(line, by, failures, idx + 1, consts)
        line_list[idx] = new_l
    swapped = sum(by.values())
    if swapped and expected_count is not None:
        for k, exp_len in expected_count.items():
            if by.get(k, 0) != exp_len:
                failures.append('%s: %d calls, the count measured in the raw script is %d' % (k, by.get(k, 0), exp_len))
        for k in by:
            if k not in expected_count:
                failures.append('%s: %d calls of a category that the raw one did not have' % (k, by[k]))
    info = {'by_category': by, 'swapped': swapped, 'failures': failures}
    if failures:
        return body_text, info
    new = '\n'.join(line_list)
    if new.count('\n') != body_text.count('\n'):
        failures.append('the line count changed')
        return body_text, info
    rest = pluralize(new)
    if any(rest.values()):
        failures.append('calls left over: %s' % rest)
        return body_text, info
    if to_report:
        report_data(info)
    return new, info


def report_data(info):
    print('%s: %d calls rewritten (%s)'
          % (LABEL_TEXT, info['swapped'], ', '.join('%s=%d' % kv for kv in sorted(info['by_category'].items()))))

