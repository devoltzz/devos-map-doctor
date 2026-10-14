# Writes an edited war3map.j back into a map, checked by pjass and by reading it back.
import os
import shutil



SCRIPT_FILES = (('war3map.j', 'jass'), ('scripts\\war3map.j', 'jass'), ('war3map.lua', 'lua'))


def _nothing(*_a, **_k):
    pass


def _kb(n):
    return '{:,} bytes'.format(n)


def rewrite(path_in, path_out, transform, progress=None, describe=None, compact=True):
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
        new, r = transform(data.decode('latin-1'), language)
        rep['files'][name] = r
        if r.get('state') == 'done':
            repl.append((name, new.encode('latin-1')))
    if not rep['files']:
        return stop('nothing_to_do', 'The map has no script.')
    if not repl:
        why = '; '.join('%s: %s' % (n, r['reason']) for n, r in rep['files'].items() if r.get('reason'))
        return stop('nothing_to_do', why or 'Nothing to change in the script.')
    with unprotect.quiet():
        protected = a.is_malformed or mpqdoctor.virtual_tables(a) or mpqdoctor.is_sprotect(a)[0]
    del a
    if protected or mpqadd.format(path_in) != 0:
        return stop('refused', 'The archive is protected or not MPQ v1: remove the protection first.')
    p('Writing the changed script')
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
        if r.get('state') == 'done' and describe:
            lines.append(describe(n, r))
        elif r.get('reason'):
            lines.append('%s: %s' % (n, r['reason']))
    lines.append('The map: %s -> %s.' % (_kb(rep['size_before']), _kb(rep['size_after'])))
    rep['lines'] = lines
    rep['state'] = 'done'
    return rep
