# Writes the ported map: the original archive plus the changed files, checked file by file.
import os
import shutil

import mpqadd
import mpqread
import mpq_rebuild
import hm3w_names


TETO = 512 * 1024 * 1024
CRLF = '\r\n'


def content(v):
    if isinstance(v, (bytes, bytearray)):
        return bytes(v)
    with open(v, 'rb') as f:
        return f.read()


def classify_items(item_entries, original):
    a = mpqread.Archive(original)
    output = []
    for n, p in item_entries:
        try:
            d = a.read(n)
        except Exception:
            d = None
        if d is None:
            output.append((n, p, 'new', None))
        else:
            output.append((n, p, 'igual' if d == content(p) else 'diferente', len(d)))
    return output


def attach(original, output, file_set, to_delete=(), reset=False, all_entries=False, fake_count=False, log=print):
    if os.path.abspath(original) != os.path.abspath(output):
        shutil.copyfile(original, output)
    repl = [(n, content(v)) for n, v in file_set]
    return mpqadd.add_files(
        output, repl, list(to_delete), reset=reset, all_entries=all_entries, fake_count=fake_count, log=log
    )


def rebuild(
    original,
    output,
    name_list,
    replacements=None,
    new_ones=None,
    to_remove=(),
    sector_shift=3,
    level=6,
    hash_factor=1,
    log=print,
):
    return mpq_rebuild.rebuild(
        original,
        output,
        name_list,
        replacements=replacements,
        new_ones=new_ones,
        to_remove=to_remove,
        sector_shift=sector_shift,
        level=level,
        hash_factor=hash_factor,
        log=log,
    )


def listfile(name_list):
    return (CRLF.join(sorted(set(name_list))) + CRLF).encode('utf-8', 'surrogateescape')


def verify(map_path, expected_len, textura=False, present_keys=(), missing_ones=(), log=None):
    a = mpqread.Archive(map_path)
    if textura:
        import blp_huffman
    failures = []
    for n, v in expected_len:
        try:
            d = a.read(n)
        except Exception as e:
            d = None
            failures.append('%s: cannot be read (%s)' % (n, e))
        w = content(v)
        ok = d is not None and (d == w or (textura and blp_huffman.same_texture(d, w)))
        if log:
            log(n, ok, len(d) if d is not None else None)
        if d is None:
            failures.append('%s: absent from the map' % n)
        elif not ok:
            failures.append('%s: DIFFERENT (%d B in the map, %d expected)' % (n, len(d), len(w)))
    for n in present_keys:
        if a.read(n) is None:
            failures.append('%s: missing from the map (must be there)' % n)
    for n in missing_ones:
        if a.read(n) is not None:
            failures.append('%s: PRESENT in the map (must not be)' % n)
    return failures


def hm3w(map_path, fname):
    changed, before = hm3w_names.renomeia(map_path, fname)
    return changed, before, hm3w_names.name_hm3w(map_path)


def cap(map_path):
    sz = os.path.getsize(map_path)
    return sz, TETO - sz
