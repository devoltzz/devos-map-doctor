# Removes the indentation of the map script, never inside a text that spans lines; the tokens are proved the same.
import os
import re
import shutil



SCRIPT_FILES = (('war3map.j', 'jass'), ('scripts\\war3map.j', 'jass'), ('war3map.lua', 'lua'))
_LEADING = re.compile(r'(\r\n?|\n)[ \t]+')
_BOM = '\xef\xbb\xbf'


def _nothing(*_a, **_k):
    pass


def _jass_spans(text):
    from doctor.script import jass_ast
    spans = []
    end = 0
    for m in jass_ast._TOKEN_RE.finditer(text):
        if m.start() != end:
            return None
        end = m.end()
        tok = m.group(1)
        if tok[:1] in ('"', "'") and len(tok) > 1 and ('\n' in tok or '\r' in tok):
            spans.append((m.start(1), m.end(1)))
    if text[end:].strip(' \t﻿'):
        return None
    return spans


def _lua_spans(text):
    from doctor.script import lua_ast
    levels = lua_ast._LONG_LEVELS.findall(text)
    pieces = lua_ast._pieces(max(map(len, levels)) if levels else 0)
    spans = []
    pos = 0
    for s in pieces.findall(text):
        c = s[0]
        if c in ('"', "'", '[', '-') and ('\n' in s or '\r' in s):
            spans.append((pos, pos + len(s)))
        pos += len(s)
    if pos != len(text):
        return None
    return spans


def _tokens(text, language):
    if language == 'jass':
        from doctor.script import jass_ast
        return jass_ast.tokenize(text)
    from doctor.script import lua_ast
    kinds, texts, lines, _offs, comments, _ctok, _sv = lua_ast._lex(text)
    if 'ERROR' in kinds:
        return None
    return list(zip(kinds, texts, lines)), [(c.text, c.line) for c in comments]


def _strip_text(text, spans):
    out, n, pos = [], 0, 0
    for i, (a, b) in enumerate(list(spans) + [(len(text), len(text))]):
        seg = text[pos:a]
        if pos == 0:
            head = _BOM if seg.startswith(_BOM) else ''
            rest = seg[len(head):]
            lead = len(rest) - len(rest.lstrip(' \t'))
            if lead:
                n += 1
                seg = head + rest[lead:]
        seg, k = _LEADING.subn(r'\1', seg)
        n += k
        out.append(seg)
        out.append(text[a:b])
        pos = b
    return ''.join(out), n


def strip(data, language):
    rep = {'state': 'nothing_to_do', 'reason': None, 'lines': 0, 'kept': 0, 'before': len(data or b''),
           'after': len(data or b'')}
    if not data:
        return data, rep
    text = data.decode('latin-1')
    spans = _jass_spans(text) if language == 'jass' else _lua_spans(text)
    if spans is None:
        rep.update(state='refused', reason='the script does not tokenize to the end: kept as it was')
        return data, rep
    new, n = _strip_text(text, spans)
    rep['kept'] = len(spans)
    if new == text:
        return data, rep
    before = _tokens(text, language)
    if before is None:
        rep.update(state='refused', reason='the script does not tokenize to the end: kept as it was')
        return data, rep
    if before != _tokens(new, language):
        rep.update(state='refused', reason='the tokens would change: kept as it was')
        return data, rep
    if text.count('\n') != new.count('\n') or text.count('\r') != new.count('\r'):
        rep.update(state='refused', reason='the line ends would change: kept as it was')
        return data, rep
    out = new.encode('latin-1')
    rep.update(state='done', lines=n, after=len(out))
    return out, rep


def _kb(n):
    return '{:,} bytes'.format(n)


def fix(path_in, path_out, progress=None, compact=True):
    from doctor.fix import unprotect
    from doctor.mpq import mpqadd
    from doctor.mpq import mpqdoctor
    p = progress or _nothing
    rep = {'state': None, 'reason': None, 'error': None, 'files': {}, 'size_before': None, 'size_after': None,
           'lines': [], 'output': None}

    def stop(state, why):
        rep['state'], rep['reason'] = state, why
        if state != 'done':
            rep['error'] = why
        rep['lines'] = rep['lines'] or [why]
        return rep

    if os.path.abspath(path_in) == os.path.abspath(path_out):
        return stop('refused', 'The output must be a new file.')
    p('Reading the map script')
    try:
        a = unprotect._open(path_in)
    except BaseException as e:
        if isinstance(e, KeyboardInterrupt):
            raise
        return stop('failed', 'The map cannot be read (%s).' % unprotect._error(e))
    rep['size_before'] = os.path.getsize(path_in)
    repl = []
    for name, language in SCRIPT_FILES:
        data = unprotect._read(a, name) if a.find(name) else None
        if not data:
            continue
        new, r = strip(data, language)
        rep['files'][name] = r
        if r['state'] == 'done':
            repl.append((name, new))
    if not rep['files']:
        return stop('nothing_to_do', 'The map has no script.')
    if not repl:
        why = '; '.join('%s: %s' % (n, r['reason']) for n, r in rep['files'].items() if r['reason'])
        return stop('nothing_to_do', 'The script has no indentation to remove.' + (' (%s)' % why if why else ''))
    with unprotect.quiet():
        protected = a.is_malformed or mpqdoctor.virtual_tables(a) or mpqdoctor.is_sprotect(a)[0]
    del a
    if protected or mpqadd.format(path_in) != 0:
        return stop('refused', 'The archive is protected or not MPQ v1: remove the protection first.')
    p('Writing the script without its indentation')
    names = [n for n, _d in repl]
    part = unprotect._part(path_out)
    tight = part + '.compact.w3x'
    try:
        shutil.copyfile(path_in, part)
        no_room = []
        with unprotect.quiet():
            mpqadd.add_files(part, repl, log=_nothing, no_slot=no_room)
        if no_room:
            raise RuntimeError('no room in the hash table for %s' % ', '.join(no_room))
        p('Checking the written map')
        b = unprotect._open(part)
        for n, data in repl:
            if unprotect._read(b, n) != data:
                raise RuntimeError('%s is not read back as written' % n)
        del b
        with unprotect.quiet():
            same = unprotect.check_content(path_in, part, exclude=names)
        if same['different'] or same['missing_items']:
            raise RuntimeError('other files changed: %s' % ', '.join((same['different'] + same['missing_items'])[:5]))
        if compact:
            from doctor.fix import shrink
            p('Dropping the space of the old script')
            s = shrink.shrink(part, tight, {'recompress': False, 'blp': False, 'dedup': False})
            if s.get('state') == 'done':
                os.replace(tight, part)
        os.replace(part, path_out)
    except Exception as e:
        for f in (part, tight):
            try:
                os.remove(f)
            except OSError:
                pass
        return stop('failed', 'The map could not be written (%s).' % unprotect._error(e))
    rep['size_after'] = os.path.getsize(path_out)
    rep['output'] = os.path.abspath(path_out)
    lines = []
    for n, r in rep['files'].items():
        if r['state'] == 'done':
            lines.append('%s: %s -> %s, %d lines without their indentation%s.' % (
                n, _kb(r['before']), _kb(r['after']), r['lines'],
                ', %d text(s) that span lines kept as they are' % r['kept'] if r['kept'] else ''))
        elif r['reason']:
            lines.append('%s: %s.' % (n, r['reason']))
    lines.append('The map: %s -> %s.' % (_kb(rep['size_before']), _kb(rep['size_after'])))
    rep['lines'] = lines
    rep['state'] = 'done'
    return rep
