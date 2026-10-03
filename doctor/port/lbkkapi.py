# Checks the KK API library the Chinese editor embeds in the script against the game natives.
import os
import re


HERE = os.path.dirname(os.path.abspath(__file__))
REF_30 = os.path.normpath(os.path.join(HERE, '..', 'ref', '3.0'))
START_MARK = '//globals from LBKKAPI:'
END_MARK = '//endglobals from LBKKAPI'
COMMENT = ('// LBKKAPI: %d globals removed by the build (redeclared by the common.j 3.0 of Reforged; 0 uses). '
           '%d kept. See RELATORIO_build.md')
RENAMED_COMMENT = ' %d renamed to LBKKAPI_<name> (used: %s).'
PREFIX = 'LBKKAPI_'
RX_COMMENT = re.compile(r'^// LBKKAPI: \d+ globais removidas pelo build ')
RX_DECL_LINE = re.compile(r'^\s*(?:constant\s+)?([A-Za-z_]\w*)\s+([A-Za-z_]\w*)\s*=')
_RX_W = re.compile(r'\w')
_RX_TOKEN = re.compile(
    r'''(?P<com>//[^\n]*)|(?P<str>"(?:[^"\\]|\\.)*")|(?P<raw>'(?:[^'\\]|\\.)*')|(?P<id>[A-Za-z_]\w*)''', re.S
)


def code_counts(body_text, name_list):
    tgt = set(name_list)
    contas = dict((n, 0) for n in name_list)
    for m in _RX_TOKEN.finditer(body_text):
        if m.lastgroup == 'id' and m.group() in tgt:
            contas[m.group()] += 1
    return contas


def renomeia_identificadores(body_text, replacements):
    contas = dict((v, 0) for v in replacements)

    def swap(m):
        if m.lastgroup == 'id' and m.group() in replacements:
            contas[m.group()] += 1
            return replacements[m.group()]
        return m.group()
    return _RX_TOKEN.sub(swap, body_text), contas


def read_reference(ref_dir=None):
    ref_dir = ref_dir or REF_30
    ref_text = ''
    for f in ('common.j', 'blizzard.j'):
        p = os.path.join(ref_dir, f)
        if os.path.exists(p):
            with open(p, 'rb') as fh:
                ref_text += '\n' + fh.read().decode('latin-1')
    if not ref_text.strip():
        raise ValueError(
            'LBKKAPI: could not find the Reforged reference in %s: without it it is not possible to decide which '
            'declarations collide' % ref_dir
        )
    return ref_text


def declared_in_reference(fname, ref_text):
    pat = (r'^\s*(?:constant\s+|debug\s+)?[A-Za-z_]\w*\s+(?:array\s+)?'
           + re.escape(fname) + r'\s*(?:=(?!=)|$)')
    return re.search(pat, ref_text, re.M) is not None


def measure_uses(fname, body_text):
    c, n, i = 0, len(fname), body_text.find(fname)
    while i >= 0:
        a = body_text[i - 1] if i else ''
        b = body_text[i + n] if i + n < len(body_text) else ''
        if not (a == '.' or (a and _RX_W.match(a))) and not (b and _RX_W.match(b)):
            c += 1
        i = body_text.find(fname, i + 1)
    return c, max(0, c - 1)


def applies(body_text, ref_dir=None, ref_text=None):
    line_list = body_text.split('\n')
    begin = end_pos = None
    for i, line in enumerate(line_list):
        s = line.strip()
        if s == START_MARK:
            begin = i
        elif s == END_MARK and begin is not None and end_pos is None:
            end_pos = i
    anc = [('start marker', sum(1 for line in line_list if line.strip() == START_MARK), '1'),
           ('end marker', sum(1 for line in line_list if line.strip() == END_MARK), '1')]
    info = {'status': None, 'detail': '', 'removed_ones': 0, 'mantidas': 0, 'declaracoes': [], 'ancoras': anc,
            'failures': []}
    if begin is None or end_pos is None:
        info.update(status='does not apply', detail='the block does not exist in this text')
        return body_text, info
    if ref_text is None:
        ref_text = read_reference(ref_dir)
    decl = []
    for i in range(begin + 1, end_pos):
        mm = RX_DECL_LINE.match(line_list[i])
        if mm:
            decl.append((i, mm.group(2)))
    ref = dict((n, declared_in_reference(n, ref_text)) for _i, n in decl)
    to_remove = [(i, n) for i, n in decl if ref[n]]
    keep_names = [(i, n) for i, n in decl if not ref[n]]
    if RX_COMMENT.match(line_list[begin + 1].strip()):
        if to_remove:
            info['failures'].append(
                'the LBKKAPI comment is already in the block, but there are still %d declaration(s) that '
                'collide (%s): mixed state' % (len(to_remove), ', '.join(n for _i, n in to_remove))
            )
            return body_text, info
        info.update(
            status='already applied',
            detail='the comment is in the block and nothing else collides (%d declarations kept)' % len(keep_names),
            mantidas=len(keep_names),
        )
        return body_text, info
    uses = dict((n, measure_uses(n, body_text)) for _i, n in decl)
    with_text = [n for _i, n in to_remove if uses[n][1] > 0]
    code = code_counts(body_text, with_text) if with_text else {}
    for n in with_text:
        uses[n] = (uses[n][0], max(0, code[n] - 1))
    rename_items = [(i, n) for i, n in to_remove if uses[n][1] > 0]
    to_remove = [(i, n) for i, n in to_remove if uses[n][1] == 0]
    replacements = dict((n, PREFIX + n) for _i, n in rename_items)
    for new in replacements.values():
        if measure_uses(new, body_text)[0] or declared_in_reference(new, ref_text):
            info['failures'].append('LBKKAPI: the new name %s already exists in the script or in the reference' % new)
    if info['failures']:
        return body_text, info
    for i, _n in reversed(to_remove):
        del line_list[i]
    comment_text = COMMENT % (len(to_remove), len(keep_names))
    if rename_items:
        comment_text = comment_text[:-len(' See RELATORIO_build.md')] + (
            RENAMED_COMMENT % (len(rename_items), ', '.join(n for _i, n in rename_items)) + ' See RELATORIO_build.md')
    line_list.insert(begin + 1, comment_text + '\r')
    output = '\n'.join(line_list)
    contas = {}
    if replacements:
        output, contas = renomeia_identificadores(output, replacements)
        for n, k in contas.items():
            if k != uses[n][1] + 1:
                info['failures'].append('LBKKAPI: %s renamed in %d code place(s), the count was %d'
                                        % (n, k, uses[n][1] + 1))
        if info['failures']:
            return body_text, info
    status = dict((n, 'REMOVIDA') for _i, n in to_remove)
    status.update((n, 'RENAMED') for _i, n in rename_items)
    info.update(
        status='aplicado',
        detail='%d of %d declarations removed (ONLY those that collide; all with 0 uses)%s; %d '
        'mantidas'
        % (
            len(to_remove),
            len(decl),
            '; %d renamed (%s)'
            % (len(rename_items), ', '.join('%s: %d use(s)' % (n, uses[n][1]) for _i, n in rename_items))
            if rename_items
            else '',
            len(keep_names),
        ),
        removed_ones=len(to_remove),
        renamed_list=len(rename_items),
        mantidas=len(keep_names),
        declaracoes=[(n, uses[n][0], uses[n][1], status.get(n, 'kept_key')) for _i, n in decl],
    )
    return output, info
