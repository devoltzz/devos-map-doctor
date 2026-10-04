# Adds code to a map script, checks it with pjass and writes the new map, checked file by file.
import os
import re
import shutil

from doctor.fix import unprotect



def _nothing(*_a, **_k):
    pass


def insert(text, tree, globals_lines=(), functions='', main_top=(), main_end=()):
    parts = re.split(r'(\r\n?|\n)', text)
    lines = [parts[i] + (parts[i + 1] if i + 1 < len(parts) else '') for i in range(0, len(parts), 2)]
    nl = '\r\n' if text.count('\r\n') * 2 > text.count('\n') else '\n'
    main = tree.function_index.get('main')
    if main is None or main.is_native:
        raise ValueError('the script has no function main')
    edits = []
    if main_end:
        edits.append((main.end_line - 1, list(main_end)))
    if main_top:
        after = max([main.line] + [l.line for l in main.locals])
        edits.append((after, list(main_top)))
    if functions:
        edits.append((main.line - 1, functions.rstrip('\n').split('\n') + ['']))
    if globals_lines:
        block = next((it for it in tree.items if type(it).__name__ == 'Globals'), None)
        if block is not None:
            edits.append((block.end_line - 1, list(globals_lines)))
        else:
            first = next((it for it in tree.items if type(it).__name__ == 'Function' and not it.is_native),
                         main)
            edits.append((first.line - 1, ['globals'] + list(globals_lines) + ['endglobals']))
    for at, new in sorted(edits, key=lambda e: -e[0]):
        lines[at:at] = [l + nl for l in new]
    return ''.join(lines)


def gate(old_bytes, new_bytes):
    from doctor.fix import single_player
    return single_player._pjass(old_bytes, new_bytes)


def write(path_in, path_out, files, progress=None, check=None):
    from doctor.mpq import mpqadd
    p = progress or _nothing
    if os.path.abspath(path_out) == os.path.abspath(path_in):
        raise RuntimeError('the output must be a new file')
    names = [n for n, _b in files]
    part = unprotect._part(path_out)
    try:
        p('Writing the map')
        shutil.copyfile(path_in, part)
        no_room = []
        with unprotect.quiet():
            mpqadd.add_files(part, list(files), all_entries=True, log=_nothing, no_slot=no_room)
        if no_room:
            raise RuntimeError('no room in the hash table for %s' % ', '.join(no_room))
        p('Checking the written map')
        b = unprotect._open(part)
        for n, data in files:
            if unprotect._read(b, n) != data:
                raise RuntimeError('%s is not read back as written' % n)
        del b
        with unprotect.quiet():
            same = unprotect.check_content(path_in, part, exclude=names)
        if same['different'] or same['missing_items']:
            raise RuntimeError('other files changed: %s' % ', '.join((same['different'] + same['missing_items'])[:5]))
        if check is not None:
            check(part)
        os.replace(part, path_out)
    except BaseException:
        try:
            os.remove(part)
        except OSError:
            pass
        raise
    return {'same_files': same['identical']}
