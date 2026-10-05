# Rewrites the return bug functions of old maps with a correctly typed body.
import re


RX_PRAGMA = re.compile(r'(?m)^([ \t]*)//# \+nosemanticerror[ \t]*\r?$')
RX_FUNC = re.compile(r'(?m)^([ \t]*)function[ \t]+(\w+)[ \t]+takes[ \t]+([^\r\n]*?)[ \t]+returns[ \t]+(\w+)[ \t]*\r?$')
RX_END = re.compile(r'(?m)^[ \t]*endfunction\b[^\r\n]*\r?$')
NULL_CAST = 'KK_tc_nula'
MARK = '// [framework KK] passo 0d'
NEUTRAL = {'integer': 'return 0', 'real': 'return 0.', 'boolean': 'return false', 'string': 'return ""'}


def body(retorno, params):
    ps = [p.split() for p in params.split(',')] if params.strip() != 'nothing' else []
    if len(ps) == 1 and len(ps[0]) == 2:
        kind, fname = ps[0]
        if retorno == 'integer' and kind == 'boolean':
            return ['if %s then' % fname, '    return 1', 'endif', 'return 0']
        if retorno == 'boolean' and kind == 'integer':
            return ['return %s!=0' % fname]
        if retorno == 'integer' and kind == 'string':
            return ['return StringHash(%s)' % fname]
    if retorno == 'nothing':
        return []
    if retorno == 'code':
        return ['return function %s' % NULL_CAST]
    return [NEUTRAL.get(retorno, 'return null')]


def applies(body_text, expected_count=None):
    info = {'failures': [], 'rewrites': 0, 'functions': []}
    failures = info['failures']
    nl = '\r\n' if '\r\n' in body_text else '\n'
    replacements = []
    for m in RX_PRAGMA.finditer(body_text):
        f = RX_FUNC.search(body_text, m.end())
        if not f or body_text[m.end():f.start()].strip():
            failures.append('pragma without a function right after (offset %d)' % m.start())
            continue
        end_pos = RX_END.search(body_text, f.end())
        if not end_pos:
            failures.append('function %s without endfunction' % f.group(2))
            continue
        indent_trim, fname, params, retorno = f.group(1), f.group(2), f.group(3), f.group(4)
        inside = indent_trim + '    '
        new = [indent_trim + MARK + ': the body became TYPE-CORRECT (the game does not know the //# '
               '+nosemanticerror and would refuse the script)', f.group(0).rstrip('\r')]
        new += [inside + line for line in body(retorno, params)]
        replacements.append((m.start(), end_pos.start(), nl.join(new) + nl))
        calls = len(re.findall(r'\b%s\s*\(' % re.escape(fname), body_text)) + \
            len(re.findall(r'\bfunction\s+%s\b' % re.escape(fname), body_text)) - 1
        info['functions'].append((fname, retorno, calls))
    for begin, end_pos, new in sorted(replacements, reverse=True):
        body_text = body_text[:begin] + new + body_text[end_pos:]
    info['rewrites'] = len(replacements)
    if any(r == 'code' for _n, r, _c in info['functions']) and \
            not re.search(r'(?m)^[ \t]*function %s takes' % NULL_CAST, body_text):
        i = body_text.index('return function %s' % NULL_CAST)
        begin = body_text.rfind(MARK, 0, i)
        begin = body_text.rfind('\n', 0, begin) + 1
        body_text = (
            body_text[:begin]
            + 'function %s takes nothing returns nothing%sendfunction%s' % (NULL_CAST, nl, nl)
            + body_text[begin:]
        )
    if expected_count is not None and info['rewrites'] != expected_count:
        failures.append('functions with //# +nosemanticerror: %d, measured is %d' % (info['rewrites'], expected_count))
    return body_text, info


def report_data(info):
    if not info['rewrites']:
        print('0d typecast: no //# +nosemanticerror')
        return
    print('0d typecast: %d "return bug" function(s) rewritten with a type-correct body: %s' % (
        info['rewrites'], ', '.join('%s->%s (%d chamada(s))' % (n, r, c) for n, r, c in info['functions'])))
    used_entries = [n for n, _r, c in info['functions'] if c > 0]
    if used_entries:
        print('   WARNING: calls made by the map (the neutral value may not work): %s' % ', '.join(used_entries))
