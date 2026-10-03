# Writes a clean MPQ archive from a set of files.
import hashlib
import os
import struct
import zlib

import mpqlib as M
import mpqread


FREE = 0xFFFFFFFF
DELETED = 0xFFFFFFFE
F_EXISTS = 0x80000000
F_COMPRESS = 0x00000200


class RebuildError(Exception):
    pass


def _norm(n):
    return n.replace('/', '\\')


def pair(fname):
    n = _norm(fname)
    return M.hashstr(n, 1), M.hashstr(n, 2)


def pack_file(data_bytes, sector_bytes, level):
    if not data_bytes:
        return b'', 0
    pieces = []
    for i in range(0, len(data_bytes), sector_bytes):
        s = data_bytes[i:i + sector_bytes]
        z = b'\x02' + zlib.compress(s, level)
        pieces.append(z if len(z) < len(s) else s)
    n = len(pieces)
    offs = [4 * (n + 1)]
    for p in pieces:
        offs.append(offs[-1] + len(p))
    return struct.pack('<%dI' % (n + 1), *offs) + b''.join(pieces), F_EXISTS | F_COMPRESS


def rebuild(
    entry,
    output,
    name_list,
    replacements=None,
    new_ones=None,
    to_remove=(),
    sector_shift=3,
    level=6,
    listfile=True,
    log=print,
    hash_factor=1,
):
    replacements = {_norm(k): v for k, v in (replacements or {}).items()}
    new_ones = {_norm(k): v for k, v in (new_ones or {}).items()}
    to_remove = {_norm(n) for n in to_remove}
    a = mpqread.Archive(entry)
    hn = a.h.hash_n
    known = {}
    for n in list(name_list) + list(replacements) + list(new_ones) + list(to_remove) + ['(listfile)', '(attributes)',
                                                                              '(signature)']:
        n = _norm(n)
        known.setdefault(pair(n), n)
    ht = [tuple(a.ht[i * 4:i * 4 + 4]) for i in range(hn)]
    live = [i for i in range(hn) if ht[i][3] < len(a.blocks)]
    clusters = {}
    for i in live:
        clusters.setdefault((ht[i][0], ht[i][1]), []).append(i)
    keep = {}
    dropped = set()
    decoys = []
    for hash_key, slots in clusters.items():
        fname = known.get(hash_key)
        if fname is not None and fname in to_remove:
            dropped.update(slots)
            continue
        if len(slots) == 1:
            keep[slots[0]] = fname
            continue
        if fname is not None:
            r = a.find(fname)
            chosen = r[0]
        else:
            neutrals = [s for s in slots if (ht[s][2] & 0xFFFFFF) == 0]
            if len(neutrals) > 1:
                flags0_only = [s for s in neutrals if (ht[s][2] >> 24) == 0]
                neutrals = flags0_only if len(flags0_only) == 1 else neutrals
            if len(neutrals) != 1:
                raise RebuildError(
                    'hash pair %08x/%08x without a name, %d entries and %d neutral: cannot tell which one the game '
                    'opens' % (hash_key[0], hash_key[1], len(slots), len(neutrals))
                )
            chosen = neutrals[0]
        keep[chosen] = fname
        for s in slots:
            if s != chosen:
                dropped.add(s)
                decoys.append((fname or '%08x/%08x' % hash_key, s))
    pair_slot = dict(((ht[s][0], ht[s][1]), s) for s in keep)
    for origin in (new_ones, replacements):
        for n in sorted(origin):
            s = pair_slot.get(pair(n))
            if s is None or keep[s] == n:
                continue
            if keep[s] is None:
                keep[s] = n
            replacements[keep[s]] = origin.pop(n)
    missing_items = [n for n in to_remove if not any(known.get((ht[i][0], ht[i][1])) == n for i in live)]
    if missing_items:
        log('warning: names to remove that the map does not have: %s' % missing_items)
    content = {}
    for slot, fname in keep.items():
        if fname is not None and fname in replacements:
            content[slot] = replacements[fname]
            continue
        bi = ht[slot][3]
        fl = a.blocks[bi][3]
        hash_key = None
        if fl & mpqread.FLAG_ENCRYPT and fname is None:
            hash_key = a.unnamed_key(bi)
            if hash_key is None:
                raise RebuildError(
                    'slot %d: block %d is ENCRYPTED and has no known name (the key is the hash of the name)'
                    % (slot, bi)
                )
        d = a.read(fname if fname is not None else '__unnamed__', bi=bi, hash_key=hash_key)
        if d is None:
            raise RebuildError('slot %d (%s): block %d could not be read' % (slot, fname, bi))
        content[slot] = d
    already_present = sorted(n for n in new_ones if n in keep.values())
    if already_present:
        raise RebuildError('new file(s) that the map already has (use trocar): %s' % already_present)
    replacements_without_target = [n for n in replacements if n not in keep.values()]
    for n in replacements_without_target:
        new_ones[n] = replacements[n]
    k = hash_factor
    if k < 1 or k & (k - 1):
        raise RebuildError('fator_hash must be a power of 2: %r' % (k,))
    hm = hn * k

    def status(s):
        if s in keep:
            return ('alive', s)
        if ht[s][3] == FREE and s not in dropped:
            return 'free'
        return 'deleted'

    tab = [status(j % hn) for j in range(hm)]
    live_pairs = {(ht[s][0], ht[s][1]) for s in keep}
    new_slots = {}

    def place(fname):
        hA, hB = pair(fname)
        if (hA, hB) in live_pairs:
            raise RebuildError('new %s already exists in the map (use trocar)' % fname)
        i0 = M.hashstr(fname, 0) & (hm - 1)
        for p in range(hm):
            i = (i0 + p) & (hm - 1)
            if tab[i] in ('free', 'deleted'):
                tab[i] = ('new', fname)
                new_slots[fname] = i
                live_pairs.add((hA, hB))
                return
        raise RebuildError('hash table full for %s (larger fator_hash needed)' % fname)

    for fname in new_ones:
        place(fname)
    new_content = dict(new_ones)
    if listfile:
        lst = sorted(set(n for n in list(keep.values()) + list(new_ones) if n and n not in
                         ('(listfile)', '(attributes)', '(signature)')))
        lst_data = ('\r\n'.join(lst) + '\r\n').encode('utf-8', 'surrogateescape')
        slot_lst = next((s for s, n in keep.items() if n == '(listfile)'), None)
        if slot_lst is None:
            place('(listfile)')
            new_content['(listfile)'] = lst_data
        else:
            content[slot_lst] = lst_data
    sector_bytes = 512 << sector_shift
    off = a.h.offset
    map_header = a.d[:off]
    block_list = []
    data_bytes = bytearray()
    order = sorted([(s, ('v', s)) for s in keep] + [(j, ('n', n)) for n, j in new_slots.items()])
    new_bi = {}
    for _slot, hash_key in order:
        d = content[hash_key[1]] if hash_key[0] == 'v' else new_content[hash_key[1]]
        body, fl = pack_file(d, sector_bytes, level)
        pos = 32 + len(data_bytes)
        new_bi[hash_key] = len(block_list)
        block_list.append((pos, len(body), len(d), fl if body else F_EXISTS))
        data_bytes += body
    hash_vals = []
    for t in tab:
        if t == 'free':
            hash_vals += [FREE, FREE, 0xFFFFFFFF, FREE]
        elif t == 'deleted':
            hash_vals += [FREE, FREE, 0xFFFFFFFF, DELETED]
        elif t[0] == 'alive':
            hash_vals += [ht[t[1]][0], ht[t[1]][1], 0, new_bi[('v', t[1])]]
        else:
            hA, hB = pair(t[1])
            hash_vals += [hA, hB, 0, new_bi[('n', t[1])]]
    block_vals = []
    for b in block_list:
        block_vals += list(b)
    hash_pos = 32 + len(data_bytes)
    block_pos = hash_pos + 16 * hm
    total = block_pos + 16 * len(block_list)
    header = struct.pack(
        '<4sIIHHIIII', b'MPQ\x1a', 32, total, 0, sector_shift, hash_pos, block_pos, hm, len(block_list)
    )
    with open(output, 'wb') as fh:
        fh.write(map_header)
        fh.write(header)
        fh.write(data_bytes)
        fh.write(M.encrypt(hash_vals, M.HASH_TABLE_KEY))
        fh.write(M.encrypt(block_vals, M.BLOCK_TABLE_KEY))
    details = {
        'entry': entry,
        'output': output,
        'file_set': len(block_list),
        'deleted_slots': len(dropped),
        'decoys': decoys,
        'removed': sorted(to_remove - set(missing_items)),
        'replaced': sorted(n for n in replacements if n in keep.values()),
        'new_ones': sorted(new_ones),
        'bytes': os.path.getsize(output),
        'sector_bytes': sector_bytes,
        'hash_n': hm,
    }
    b = mpqread.Archive(output)
    error_list = []
    for _slot, hash_key in order:
        fname = keep[hash_key[1]] if hash_key[0] == 'v' else hash_key[1]
        expected_len = content[hash_key[1]] if hash_key[0] == 'v' else new_content[hash_key[1]]
        bi = new_bi[hash_key]
        d = b.read(fname if fname else '__unnamed__', bi=bi)
        if d is None or hashlib.sha256(d).digest() != hashlib.sha256(expected_len).digest():
            error_list.append('%s (%s): differs when read back' % (fname, hash_key))
        if fname:
            r = b.find(fname)
            if r is None or r[1] != bi:
                error_list.append('%s: the probe does not find block %d' % (fname, bi))
    for i in range(b.h.hash_n):
        hA, hB, bl, bi = b.ht[i * 4:i * 4 + 4]
        if bi < len(b.blocks) and bl != 0:
            error_list.append('slot %d: locale/platform %08x' % (i, bl))
    for n in to_remove:
        if b.find(n) is not None:
            error_list.append('%s: still in the map' % n)
    details['error_list'] = error_list
    log('rebuilt: %s -> %s: %d files (%d replaced, %d new), %d entries deleted (%d decoys, %d requested); '
        'hash table %d (%dx); %d B; check: %s' % (
            os.path.basename(entry), os.path.basename(output), len(block_list), len(details['replaced']), len(new_ones),
            len(dropped), len(decoys), len(details['removed']), hm, k, details['bytes'],
            'all read back identical' if not error_list else '%d ERRORS' % len(error_list)))
    for e in error_list[:10]:
        log('   ERROR: %s' % e)
    return details


def write_mpq(output, file_set, map_header=b'', sector_shift=3, level=6, listfile=True):
    file_set = dict((_norm(n), d) for n, d in file_set.items())
    if listfile:
        lst = sorted((n for n in file_set if n not in ('(listfile)', '(attributes)', '(signature)')),
                     key=lambda n: (n.lower(), n))
        file_set['(listfile)'] = ('\r\n'.join(lst) + '\r\n').encode('utf-8', 'surrogateescape')
    file_set.pop('(attributes)', None)
    sector_bytes = 512 << sector_shift
    hm = 16
    while hm < 2 * len(file_set):
        hm <<= 1
    tab = [None] * hm
    for fname in sorted(file_set, key=lambda n: (n.lower(), n)):
        i0 = M.hashstr(fname, 0) & (hm - 1)
        for p in range(hm):
            i = (i0 + p) & (hm - 1)
            if tab[i] is None:
                tab[i] = fname
                break
    block_list = []
    data_bytes = bytearray()
    bi = {}
    for fname in sorted(file_set, key=lambda n: (n.lower(), n)):
        d = file_set[fname]
        body, fl = pack_file(d, sector_bytes, level)
        bi[fname] = len(block_list)
        block_list.append((32 + len(data_bytes), len(body), len(d), fl if body else F_EXISTS))
        data_bytes += body
    hash_vals = []
    for fname in tab:
        if fname is None:
            hash_vals += [FREE, FREE, 0xFFFFFFFF, FREE]
        else:
            hA, hB = pair(fname)
            hash_vals += [hA, hB, 0, bi[fname]]
    block_vals = [v for b in block_list for v in b]
    map_header = bytes(map_header)
    if map_header and len(map_header) % 0x200:
        map_header += b'\0' * (0x200 - len(map_header) % 0x200)
    hash_pos = 32 + len(data_bytes)
    block_pos = hash_pos + 16 * hm
    total = block_pos + 16 * len(block_list)
    header = struct.pack(
        '<4sIIHHIIII', b'MPQ\x1a', 32, total, 0, sector_shift, hash_pos, block_pos, hm, len(block_list)
    )
    with open(output, 'wb') as fh:
        fh.write(map_header)
        fh.write(header)
        fh.write(data_bytes)
        fh.write(M.encrypt(hash_vals, M.HASH_TABLE_KEY))
        fh.write(M.encrypt(block_vals, M.BLOCK_TABLE_KEY))
    b = mpqread.Archive(output)
    error_list = [n for n, d in file_set.items() if b.read(n) != d]
    return {'file_set': len(file_set), 'bytes': os.path.getsize(output), 'error_list': error_list, 'hash_n': hm}


def report_leftovers(cat, included):
    return (
        'from the dictionary (%d names outside the closure): %d decoys the game does not read, %d over the data of a map file, %d '
        'empty, %d with content of another type (the `.w3x` that is a model), %d without a block; %d art leftovers %s'
        % (
            sum(
                cat[k]
                for k in ('invalid_decoy', 'alias_decoy', 'empty_decoy', 'wrong_type_decoy', 'no_block', 'leftovers')
            ),
            cat['invalid_decoy'],
            cat['alias_decoy'],
            cat['empty_decoy'],
            cat['wrong_type_decoy'],
            cat['no_block'],
            cat['leftovers'],
            '(included: --leftovers)' if included else '(left out; --leftovers adds them)',
        )
    )

