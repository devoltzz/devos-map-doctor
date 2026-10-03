# Rewrites the EXExecuteScript calls that only read an object field into a table lookup.
import os
import re


TARGET = 'EXExecuteScript('
TABS = {'unit': 'DB_TAB_UNIT', 'ability': 'DB_TAB_ABILITY', 'item': 'DB_TAB_ITEM'}
RX_PREFIX_MATCH = re.compile(
    r'^"\(?\s*require\s*\(?\s*(?:\'|\\")jass\.slk(?:\'|\\")\s*\)?\s*\)?\.(unit|ability|item)\[\s*"$'
)
RX_I2S = re.compile(r'^I2S\s*\((.*)\)$', re.S)
RX_SUFFIX = re.compile(r'^"\s*\]\.([A-Za-z][A-Za-z0-9]*)\s*"$')
RX_LITERAL = re.compile(r'^"\(?\s*require\s*\(?\s*(?:\'|\\")jass\.slk(?:\'|\\")\s*\)?\s*\)?\.(unit|ability|item)\.'
                        r'([A-Za-z0-9]{4})\.([A-Za-z][A-Za-z0-9]*)\s*"$')


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


def find_calls(ln):
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
        if ln.startswith(TARGET, i) and (i == 0 or not (ln[i - 1].isalnum() or ln[i - 1] == '_')):
            k = i + len(TARGET)
            max_depth = 1
            while k < n and max_depth > 0:
                ch = ln[k]
                if ch == '"':
                    k = skip_string(ln, k)
                    continue
                if ch == "'":
                    k = skip_rawcode(ln, k)
                    continue
                if ch == '(':
                    max_depth += 1
                elif ch == ')':
                    max_depth -= 1
                k += 1
            if max_depth != 0:
                return None
            out.append((i, k, ln[i + len(TARGET):k - 1]))
            i = k
            continue
        i += 1
    return out


def without_comment(ln):
    n = len(ln)
    i = 0
    while i < n:
        c = ln[i]
        if c == '"':
            i = skip_string(ln, i)
            continue
        if c == '/' and ln.startswith('//', i):
            return ln[:i]
        if c == "'":
            i = skip_rawcode(ln, i)
            continue
        i += 1
    return ln


def masked_lines(body_text):
    out = []
    inside = False
    for line in body_text.split('\n'):
        n = len(line)
        i = 0
        if inside:
            while i < n and line[i] != '"':
                i += 2 if line[i] == '\\' else 1
            if i >= n:
                out.append(' ' * n)
                continue
            i += 1
            inside = False
        begin = i
        while i < n:
            c = line[i]
            if c == '"':
                k = i + 1
                while k < n and line[k] != '"':
                    k += 2 if line[k] == '\\' else 1
                if k >= n:
                    inside = True
                    break
                i = k + 1
                continue
            if c == '/' and line.startswith('//', i):
                break
            if c == "'":
                i = skip_rawcode(line, i)
                continue
            i += 1
        out.append(' ' * begin + line[begin:] if begin else line)
    return out


def count_slk_code(body_text):
    tgt = "require'jass.slk'"
    n = 0
    for line in masked_lines(body_text):
        if tgt in line:
            n += without_comment(line).count(tgt)
    return n


def split_more(arg):
    pieces = []
    max_depth = 0
    begin = 0
    i = 0
    n = len(arg)
    while i < n:
        c = arg[i]
        if c == '"':
            i = skip_string(arg, i)
            continue
        if c == "'":
            i = skip_rawcode(arg, i)
            continue
        if c == '(':
            max_depth += 1
        elif c == ')':
            max_depth -= 1
        elif c == '+' and max_depth == 0:
            pieces.append(arg[begin:i])
            begin = i + 1
        i += 1
    pieces.append(arg[begin:])
    return [p.strip() for p in pieces]


def balanced(expr):
    max_depth = 0
    i = 0
    n = len(expr)
    while i < n:
        c = expr[i]
        if c == '"':
            i = skip_string(expr, i)
            continue
        if c == "'":
            i = skip_rawcode(expr, i)
            continue
        if c == '(':
            max_depth += 1
        elif c == ')':
            max_depth -= 1
            if max_depth < 0:
                return False
        i += 1
    return max_depth == 0


def paren_balance(ln):
    code = without_comment(ln)
    s = 0
    i = 0
    n = len(code)
    while i < n:
        c = code[i]
        if c == '"':
            i = skip_string(code, i)
            continue
        if c == "'":
            i = skip_rawcode(code, i)
            continue
        if c == '(':
            s += 1
        elif c == ')':
            s -= 1
        i += 1
    return s


def site_parts(arg):
    pieces = split_more(arg)
    m = RX_LITERAL.match(pieces[0]) if len(pieces) == 1 else None
    if m:
        return m.group(1), m.group(3), "'%s'" % m.group(2)
    if len(pieces) != 3:
        return None, '%d top-level part(s) (expected 3)' % len(pieces), None
    m0 = RX_PREFIX_MATCH.match(pieces[0])
    m1 = RX_I2S.match(pieces[1])
    m2 = RX_SUFFIX.match(pieces[2])
    if not m0:
        return None, 'prefix does not match: %s' % pieces[0], None
    if not m1:
        return None, 'the middle is not I2S(...): %s' % pieces[1], None
    if not m2:
        return None, 'suffix does not match: %s' % pieces[2], None
    expr = m1.group(1).strip()
    if not expr or not balanced(expr):
        return None, 'unbalanced I2S expression: %s' % pieces[1], None
    return m0.group(1), m2.group(1), expr


def reescreve(arg):
    tab, field_id, expr = site_parts(arg)
    if tab is None:
        return None, field_id, None
    field_id = field_id.upper()
    return 'DB_slk_get(%s,%s,DB_C_%s_%s)' % (TABS[tab], expr, tab.upper(), field_id), tab, field_id


def script_pairs(body_text):
    pairs = {}
    failures = []
    for i, line in enumerate(masked_lines(body_text)):
        if TARGET not in line:
            continue
        sitios = find_calls(line)
        if sitios is None:
            failures.append('line %d: EXExecuteScript parenthesis does not close' % (i + 1))
            continue
        for _start, _stop, arg in sitios:
            if 'jass.slk' not in arg:
                continue
            tab, field_id, _expr = site_parts(arg)
            if tab is None:
                failures.append('line %d: %s' % (i + 1, field_id))
                continue
            pairs[(tab, field_id)] = pairs.get((tab, field_id), 0) + 1
    return pairs, failures


def read_codes(table):
    if not table or not os.path.isfile(table):
        return None
    t = open(table, 'rb').read().decode('latin-1')
    return set(re.findall(r'(?m)^\s*constant\s+integer\s+(DB_(?:C|TAB)_\w+)\s*=', t))


def class_of(arg):
    if 'jass.slk' in arg:
        return 'class 1 (SLK)'
    if 'lua_load(' in arg:
        return 'lua_load'
    if 'lua_save(' in arg:
        return 'lua_save'
    if 'LoadStr(' in arg:
        return 'chunk stored in the hashtable'
    if 'ac.' in arg or "require 'ac" in arg or 'require"ac' in arg:
        return 'framework ac'
    return 'variable/other'


def applies(body_text, to_report=False, codes=None, expected_count=None, table=None, tolerant_mode=False):
    if codes is None:
        codes = read_codes(table)
    line_list = body_text.split('\n')
    failures = []
    plain_name = []
    n_examples = 0
    n_slk = 0
    by_field = {}
    by_class = {}
    in_use = set()

    for i, line in enumerate(masked_lines(body_text)):
        if TARGET not in line:
            continue
        sitios = find_calls(line)
        if sitios is None:
            failures.append('line %d: EXExecuteScript parenthesis does not close: %s' % (i + 1, line.strip()[:160]))
            continue
        n_examples += len(sitios)
        replacements = []
        for begin, end_pos, arg in sitios:
            if 'jass.slk' not in arg:
                k = class_of(arg)
                by_class[k] = by_class.get(k, 0) + 1
                continue
            n_slk += 1
            new, tab, field_id = reescreve(arg)
            if new is None and tolerant_mode:
                by_class['class 1 in game'] = by_class.get('class 1 in game', 0) + 1
                n_slk -= 1
                continue
            if new is None:
                failures.append('line %d: %s :: %s' % (i + 1, tab, line.strip()[:200]))
                continue
            in_use.add(TABS[tab])
            in_use.add('DB_C_%s_%s' % (tab.upper(), field_id))
            hash_key = '%s.%s' % (tab, field_id)
            by_field[hash_key] = by_field.get(hash_key, 0) + 1
            replacements.append((begin, end_pos, new))
        if replacements:
            plain_name.append((i, replacements))
    swapped = sum(len(tr) for _, tr in plain_name)
    if codes is None:
        failures.append('table %s not found: the DB_C_*/DB_TAB_* codes cannot be checked' % table)
    else:
        missing_items = sorted(in_use - codes)
        if missing_items:
            failures.append('code(s) without `constant integer` in %s: %s'
                            % (os.path.basename(table) if table else 'slk_campos_tabela.j', ', '.join(missing_items)))
    if expected_count is not None and swapped not in (0, expected_count):
        failures.append('%d sites rewritten: expected %d (1st run) or 0 (text already relinked)'
                        % (swapped, expected_count))
    info = {'sitios': n_examples, 'with_slk': n_slk, 'swapped': swapped, 'remaining_count': n_examples - n_slk,
            'by_field': by_field, 'by_class': by_class, 'expected_count': expected_count,
            'slk_get_before': body_text.count('DB_slk_get('), 'slk_get_after': None, 'failures': failures,
            'rewritten_lines': len(plain_name)}
    if failures:
        return body_text, info

    for i, replacements in plain_name:
        line = line_list[i]
        before = paren_balance(line)
        for begin, end_pos, new in sorted(replacements, reverse=True):
            line = line[:begin] + new + line[end_pos:]
        after_diag = paren_balance(line)
        if after_diag != before:
            failures.append('line %d: the parenthesis balance changed (%d -> %d): %s'
                            % (i + 1, before, after_diag, line.strip()[:200]))
        line_list[i] = line
    new_text = '\n'.join(line_list)
    info['slk_get_after'] = new_text.count('DB_slk_get(')

    if new_text.count('\n') != body_text.count('\n'):
        failures.append('the line count changed (%d -> %d)' % (body_text.count('\n') + 1, new_text.count('\n') + 1))
    n_required = count_slk_code(new_text) - by_class.get('class 1 in game', 0)
    if n_required > 0 or (n_required < 0 and not tolerant_mode):
        failures.append("%d `require'jass.slk'` left in CODE (outside comments)" % n_required)
    if info['slk_get_after'] - info['slk_get_before'] != swapped:
        failures.append('`DB_slk_get(` grew %d, expected %d'
                        % (info['slk_get_after'] - info['slk_get_before'], swapped))
    if failures:
        return body_text, info
    if to_report:
        report_data(info)
    return new_text, info


def report_data(info):
    print('EXExecuteScript sites : %d' % info['sitios'])
    print('  with jass.slk (class 1) : %d -> rewritten in DB_slk_get: %d' % (info['with_slk'], info['swapped']))
    print('  without jass.slk (kept) : %d  [%s]'
          % (info['remaining_count'], ', '.join('%s=%d' % kv for kv in sorted(info['by_class'].items(),
                                                                          key=lambda kv: -kv[1]))))
    if info['by_field']:
        print('  per field               : %s'
              % ', '.join('%s=%d' % kv for kv in sorted(info['by_field'].items(), key=lambda kv: -kv[1])))
    print('  DB_slk_get( before/after: %s / %s' % (info['slk_get_before'], info['slk_get_after']))
    if info.get('expected_count') is None:
        print('  (without --esperadas: the count lock is OFF)')

