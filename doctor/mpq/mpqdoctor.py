# Repairs MPQ headers and tables tampered with by map protectors.
import collections
import re
import struct

from doctor.mpq import mpqlib as M
from doctor.mpq import mpqread as R


SIG = b'MPQ\x1a'
HASH_FREE = 0xFFFFFFFF
HASH_DELETED = 0xFFFFFFFE


def u32(buf, off):
    return struct.unpack_from('<I', buf, off)[0]


def u16(buf, off):
    return struct.unpack_from('<H', buf, off)[0]


def scan_header(d, fname=None):
    h, skipped = M.find_header(d, fname)
    picked = h.offset if h else None
    existing = set(o for o, _m in skipped)
    decoys = list(skipped)
    for o in range(0, len(d) - 32, 0x200):
        sig = d[o:o + 4]
        if o in existing or o == picked:
            continue
        if sig[:3] == b'MPQ' and sig != SIG and (picked is None or o < picked):
            decoys.append((o, 'signature %s (tampered magic)' % sig.hex()))
        elif sig == SIG and picked is not None and o > picked and u32(d, o + 4) >= 0x20:
            decoys.append((o, 'candidate also accepted (StormLib stops at the first one)'))
    decoys.sort()
    return picked, decoys


def malformed(d, hdr):
    h = M._v1_fields(M.Header(), d, hdr, len(d))
    issues = M.is_malformed(h)
    return issues, (
        h.header_size,
        h.archive_size,
        h.version,
        h.block_shift,
        h.hash_pos,
        h.block_pos,
        h.hash_n,
        h.block_n,
    )


def is_sprotect(a):
    marked = used_entries = 0
    for i in range(a.hash_n_read):
        bi = a.ht[i * 4 + 3]
        if bi in (HASH_FREE, HASH_DELETED):
            continue
        used_entries += 1
        if bi >> 24 == 0x40 and (bi & 0x00FFFFFF) < len(a.blocks):
            marked += 1
    return used_entries > 0 and marked * 2 > used_entries, marked, used_entries


def virtual_tables(a):
    return a.hash_n_read < a.h.hash_n or len(a.bt) // 4 < a.h.block_n or a.h.hash_pos < 0x20


def outside_tables(a, byte_size):
    base = a.h.offset
    ivs = [(0, base + 32)]
    for pos, n in ((a.h.hash_pos, a.h.hash_n), (a.h.block_pos, a.h.block_n)):
        begin = (base + pos) & 0xFFFFFFFF
        ivs.append((begin, min(byte_size, begin + 16 * n)))
    for off, cs, _fs, fl in a.blocks:
        if fl & 0x80000000 and cs:
            begin = (base + off) & 0xFFFFFFFF
            ivs.append((begin, min(byte_size, begin + cs)))
    ivs.sort()
    outside, segments, end_pos = 0, [], 0
    for begin, f in ivs + [(byte_size, byte_size)]:
        if begin > end_pos:
            outside += begin - end_pos
            if begin - end_pos >= 1 << 20:
                segments.append((end_pos, begin))
        end_pos = max(end_pos, f)
    return outside, segments


def data_regions(a, byte_size):
    out = []
    for off, cs, _fs, fl in a.blocks:
        if fl & 0x80000000 and cs:
            begin = (a.h.offset + off) & 0xFFFFFFFF
            if begin + cs <= byte_size:
                out.append((begin, begin + cs))
    return out


def overlaps(begin, end_pos, regions):
    return any(i < end_pos and begin < f for i, f in regions)


def analyze_tables(a):
    free_slots = deleted = valid_entries = 0
    by_block = collections.Counter()
    pairs = set()
    for i in range(a.hash_n_read):
        bi = a.ht[i * 4 + 3]
        if bi == HASH_FREE:
            free_slots += 1
        elif bi == HASH_DELETED:
            deleted += 1
        elif bi < len(a.blocks):
            valid_entries += 1
            pair = (a.ht[i * 4], a.ht[i * 4 + 1], bi)
            if pair not in pairs:
                pairs.add(pair)
                by_block[bi] += 1
    live = [(off, off + cs, bi, fs) for bi, (off, cs, fs, fl) in enumerate(a.blocks) if fl & 0x80000000 and cs]
    live.sort()
    overlap_count = 0
    end_pos = -1
    for begin, f, _bi, _fs in live:
        if begin < end_pos:
            overlap_count += 1
        end_pos = max(end_pos, f)
    return {'free_slots': free_slots, 'deleted': deleted, 'valid_entries': valid_entries,
            'alias': sum(1 for c in by_block.values() if c > 1), 'alias_max': max(by_block.values() or [0]),
            'overlapping': overlap_count, 'fs_sum': sum(x[3] for x in live), 'live': len(live)}


PROBES = ['war3map.j', 'war3map.lua', 'war3map.w3e', 'war3map.w3i', 'war3map.wts',
          'war3map.doo', 'war3map.wpm', 'war3map.shd', 'war3mapMap.blp', 'war3map.w3u']


SPECIAL_FILES = ('(listfile)', '(attributes)', '(signature)')


def locale_decoys(a, name_list):
    out = []
    for n in sorted(set(name_list), key=str.upper):
        es = a.hash_entries(n)
        if not any(e[1] != 0 for e in es):
            continue
        r = a.find(n)
        r2 = a.find_locale(n)
        if r is None or not r2 or r2[1] == r[1]:
            continue
        neutrals = [e for e in es if e[1] == 0 and e[2] == 0]
        neutral = neutrals[-1][0] if neutrals else None
        keep = neutral if neutral is not None else r2[0]
        out.append((n, neutral, r2[1], [e[0] for e in es if e[1] != 0 and e[3] == r2[1] and e[0] != keep]))
    return out


GAME_ONLY_READS = "only the game's rule reads it"


def classify_blocks(a, name_list=(), copies=False):
    block_name = {}
    for n in list(name_list) + PROBES + ['(listfile)', '(attributes)']:
        for _slot, _loc, _plat, bi, _fl in a.hash_entries(n):
            block_name.setdefault(bi, n)
    from doctor.mpq import mpqnames
    in_use = set(a.ht[i * 4 + 3] for i in range(a.hash_n_read)) - {HASH_FREE, HASH_DELETED}
    status = {}
    for bi in sorted(b for b in in_use if b < len(a.blocks)):
        v, m = a.validate(bi, block_name.get(bi))
        if v == 'invalid' and bi in block_name and mpqnames.read_by_name(a, bi, block_name[bi]):
            v, m = 'ok', '%s (%s)' % (GAME_ONLY_READS, m)
        if v == 'ok' and m in R.VALID_FOR_GAME:
            if not mpqnames.is_valid_name(a, bi, block_name[bi]):
                v, m = 'invalid', 'not compressed, with a wrong stored size and content of another type'
        status[bi] = ({'ok': 'real', 'invalid': 'junk'}.get(v, 'uncertain'), m)
    import bisect
    real_blocks = sorted((a.blocks[b][0], a.blocks[b][0] + a.blocks[b][1], b) for b, (e, _m) in status.items()
                         if e == 'real' and a.blocks[b][1])
    starts = [r[0] for r in real_blocks]
    max_end = []
    m = -1
    for r in real_blocks:
        m = max(m, r[1])
        max_end.append(m)
    for bi, (e, _m) in list(status.items()):
        if e == 'junk':
            continue
        off, cs, fs, fl = a.blocks[bi]
        if not cs or e == 'real' and bi in block_name:
            continue
        k = bisect.bisect_right(starts, off + cs - 1) - 1
        while k >= 0 and max_end[k] > off:
            ro, rf, rb = real_blocks[k]
            if rb != bi and rf > off and ro < off + cs and a.blocks[rb][:3] != (off, cs, fs):
                if e == 'uncertain' or rb in block_name and bi not in block_name:
                    status[bi] = ('junk', 'overlaps block %d (%s)' % (rb, block_name.get(rb, 'real, unnamed')))
                    break
            k -= 1
    if copies:
        by_data = collections.defaultdict(list)
        for bi, (e, _m) in status.items():
            if e == 'real':
                by_data[a.blocks[bi]].append(bi)
        for cluster in by_data.values():
            with_name = [b for b in cluster if b in block_name]
            if with_name:
                for b in cluster:
                    if b not in block_name:
                        status[b] = ('junk', 'identical copy of %s' % block_name[with_name[0]])
    return status, block_name


def _wts(body_text):
    out = {}
    for m in re.finditer(r'STRING[ \t]+(\d+)[^\n]*\n(?://[^\n]*\n)*\{\r?\n(.*?)\r?\n\}', body_text, re.S):
        out[int(m.group(1))] = m.group(2)
    return out


def build_hm3w(a):
    from doctor.data import w3i
    m = w3i.parse(a.read('war3map.w3i'))
    fname = m['name'].decode('utf-8', 'replace')
    tr = re.match(r'^TRIGSTR_(\d+)$', fname.strip())
    if tr:
        wts = a.read('war3map.wts')
        if wts:
            fname = _wts(wts.decode('utf-8', 'replace')).get(int(tr.group(1)), fname)
    b = b'HM3W' + b'\0' * 4 + fname.encode('utf-8')[:400] + b'\0' + struct.pack('<ii', m['flags'], len(m['players']))
    return b + b'\0' * (0x200 - len(b)), fname, m['flags'], len(m['players'])


def _new_tables(d, a, name_list=(), leftovers=False):
    from doctor.mpq import mpqnames
    from doctor.mpq import mpq_rebuild as RC
    hdr = a.h.offset
    closure = mpqnames.full_closure(a)
    chosen = dict((n, bi) for n, bi in closure.items() if n not in ('(listfile)', '(attributes)', '(signature)'))
    print('  VIRTUAL tables: %d file(s) the map references (the closure, each one validated)' % len(chosen))
    if name_list:
        extra, cat = mpqnames.dictionary_leftovers(a, closure, name_list)
        print('  ' + RC.report_leftovers(cat, leftovers))
        if leftovers:
            chosen.update(extra)
    block_name = {}
    for n in sorted(chosen, key=lambda n: (n.lower(), n)):
        block_name.setdefault(chosen[n], n)
    new = {}
    bt = []
    for bi in sorted(block_name, key=lambda b: (a.blocks[b][0], b)):
        off, _cs, fs, fl = a.blocks[bi]
        begin, end_pos = a.interval(bi, block_name[bi])
        if end_pos > begin and begin < hdr + 0x20 and end_pos > hdr:
            raise ValueError('block %d (%s) has data inside the header: it cannot be rewritten'
                             % (bi, block_name[bi]))
        new[bi] = len(bt) // 4
        bt += [off, end_pos - begin, fs, fl]
    listing = ('\r\n'.join(sorted((n.replace('/', '\\') for n in chosen), key=lambda n: (n.lower(), n))) + '\r\n'
               ).encode('utf-8', 'surrogateescape')
    body, fl_listing = RC.pack_file(listing, a.sector_size, 9)
    hash_entries = [(n, new[bi]) for n, bi in chosen.items()] + [('(listfile)', len(bt) // 4)]
    bt += [len(d) - hdr, len(body), len(listing), fl_listing]
    d += body
    hm = 16
    while hm < 2 * len(hash_entries):
        hm <<= 1
    ht = [HASH_FREE] * (4 * hm)
    for n, b in sorted(hash_entries, key=lambda e: e[0].lower()):
        h1, h2 = RC.pair(n)
        i0 = M.hashstr(RC._norm(n), 0) & (hm - 1)
        for k in range(hm):
            i = (i0 + k) & (hm - 1)
            if ht[i * 4 + 3] == HASH_FREE:
                ht[i * 4:i * 4 + 4] = [h1, h2, 0, b]
                break
    hp = len(d) - hdr
    d += M.encrypt(ht, M.HASH_TABLE_KEY)
    bp = len(d) - hdr
    d += M.encrypt(bt, M.BLOCK_TABLE_KEY)
    ss = u16(d, hdr + 0x0E)
    struct.pack_into('<IIHHIIII', d, hdr + 4, 0x20, len(d) - hdr, 0, ss, hp, bp, hm, len(bt) // 4)
    print(
        '  NEW tables at the end of the file: hash table of %d entries at 0x%X, block table of %d blocks at 0x%X, a'
        ' (listfile) with the %d names; the header points to them (dwHeaderSize 0x20, wFormatVersion 0, wSectorSize %d'
        ' kept: the data depends on it)' % (hm, hdr + hp, len(bt) // 4, hdr + bp, len(chosen), ss)
    )
    return chosen


def fix(path, out, name_list=(), clean_alias=False, prefix_hm3w=False, hide_junk=False, hide_copies=False,
        leftovers=False, report=None):
    details = report if report is not None else {}
    d = bytearray(open(path, 'rb').read())
    orig_size = len(d)
    hdr, decoys = scan_header(bytes(d), path)
    if hdr is None:
        print('no header to fix')
        return None
    hs, asz, ver, ss, hp, bp, hn, bn = struct.unpack_from('<IIHHIIII', d, hdr + 4)
    print('fix:')
    orig = R.Archive(path)

    details['fake_zeroed'] = 0
    for o, why in decoys:
        if o < hdr and why.startswith('FAKE header') and d[o:o + 4] == SIG:
            d[o:o + 4] = b'\0\0\0\0'
            details['fake_zeroed'] += 1
            print('  FAKE header @0x%X: signature zeroed' % o)

    chosen = None
    if virtual_tables(orig):
        chosen = _new_tables(d, orig, name_list, leftovers)
        details['new_tables'] = len(chosen)
        hs, asz, ver, ss, hp, bp, hn, bn = struct.unpack_from('<IIHHIIII', d, hdr + 4)

    if chosen is None and bn > 1 and (bp & 0x80000000 or bp <= 0x20):
        babs = (hdr + bp) & 0xFFFFFFFF
        if babs + bn * 16 > len(d):
            print('  block table outside the file; cannot fix it')
            return None
        newpos = len(d)
        d += d[babs:babs + bn * 16]
        bp = newpos - hdr
        struct.pack_into('<I', d, hdr + 0x14, bp)
        details['block_table_moved'] = True
        print('  block table: 0x%X -> 0x%X (relative 0x%X)' % (babs, newpos, bp))

    if chosen is None and bn > 1 and (hp & 0x80000000 or hp <= 0x20):
        habs = (hdr + hp) & 0xFFFFFFFF
        if habs + hn * 16 > len(d):
            print('  hash table outside the file; cannot fix it')
            return None
        newpos = len(d)
        d += d[habs:habs + hn * 16]
        hp = newpos - hdr
        struct.pack_into('<I', d, hdr + 0x10, hp)
        details['hash_table_moved'] = True
        print('  hash table: 0x%X -> 0x%X (relative 0x%X)' % (habs, newpos, hp))

    if chosen is None:
        data_bytes = data_regions(orig, orig_size)
        for which in ('hash', 'block'):
            habs, babs = (hdr + hp) & 0xFFFFFFFF, (hdr + bp) & 0xFFFFFFFF
            if which == 'hash':
                begin, end_pos, other_table = habs, habs + hn * 16, (babs, babs + bn * 16)
            else:
                begin, end_pos, other_table = babs, babs + bn * 16, (habs, habs + hn * 16)
            if end_pos > len(d) or not overlaps(begin, end_pos, data_bytes + [other_table, (hdr, hdr + 0x20)]):
                continue
            newpos = len(d)
            d += d[begin:end_pos]
            if which == 'hash':
                hp = newpos - hdr
                struct.pack_into('<I', d, hdr + 0x10, hp)
            else:
                bp = newpos - hdr
                struct.pack_into('<I', d, hdr + 0x14, bp)
            details[which + '_table_overlapping'] = True
            print('  %s table OVERLAPS something else: copied from 0x%X to 0x%X (the copy is what gets changed)'
                  % (which, begin, newpos))

    repointed = {}
    if chosen is None:
        replacements = locale_decoys(orig, set(name_list) | set(PROBES))
        if replacements:
            habs = (hdr + hp) & 0xFFFFFFFF
            ht = list(M.decrypt(bytes(d[habs:habs + hn * 16]), M.HASH_TABLE_KEY))
            for n, neutral, block_entry, to_delete in replacements:
                if neutral is not None:
                    ht[neutral * 4 + 3] = block_entry
                    repointed[neutral] = block_entry
                else:
                    keep = next(e[0] for e in orig.hash_entries(n) if e[3] == block_entry)
                    ht[keep * 4 + 2] &= 0xFFFF0000
                for s in to_delete:
                    ht[s * 4 + 3] = HASH_DELETED
                print('  locale decoy: %s -> block %d (the neutral entry pointed to a decoy; %d locale entry(ies) '
                      'deleted)' % (n, block_entry, len(to_delete)))
            d[habs:habs + hn * 16] = M.encrypt(ht, M.HASH_TABLE_KEY)
        details['locale_decoys'] = len(replacements)

    if clean_alias and chosen is None:
        hkey = M.HASH_TABLE_KEY
        habs = (hdr + hp) & 0xFFFFFFFF
        ht = list(M.decrypt(bytes(d[habs:habs + hn * 16]), hkey))
        known = collections.defaultdict(set)
        regular = collections.defaultdict(set)
        for n in set(name_list) | set(PROBES) | {'(listfile)', '(attributes)'}:
            for slot, _loc, _plat, bi, _fl in orig.hash_entries(n):
                known[bi].add(slot)
                if n.lower() not in SPECIAL_FILES:
                    regular[bi].add(slot)
        for slot, block_entry in repointed.items():
            known[block_entry].add(slot)
            regular[block_entry].add(slot)
        for n in SPECIAL_FILES:
            for slot, _loc, _plat, bi, _fl in orig.hash_entries(n):
                if regular.get(bi):
                    known[bi].discard(slot)
        deleted_count = 0
        for i in range(hn):
            bi = ht[i * 4 + 3]
            if bi in known and i not in known[bi]:
                ht[i * 4 + 3] = HASH_DELETED
                deleted_count += 1
        d[habs:habs + hn * 16] = M.encrypt(ht, hkey)
        details['deleted_aliases'], details['alias_blocks'] = deleted_count, len(known)
        print('  alias: %d entry(ies) deleted in %d block(s) with a known name' % (deleted_count, len(known)))

    if (hide_junk or hide_copies) and chosen is None:
        status, _nb = classify_blocks(orig, name_list, copies=hide_copies)
        c = collections.Counter(e for e, _m in status.values())
        junk = set(b for b, (e, _m) in status.items() if e == 'junk')
        habs = (hdr + hp) & 0xFFFFFFFF
        babs = (hdr + bp) & 0xFFFFFFFF
        ht = list(M.decrypt(bytes(d[habs:habs + hn * 16]), M.HASH_TABLE_KEY))
        bt = list(M.decrypt(bytes(d[babs:babs + bn * 16]), M.BLOCK_TABLE_KEY))
        hash_entries = 0
        for i in range(hn):
            if ht[i * 4 + 3] in junk:
                ht[i * 4 + 3] = HASH_DELETED
                hash_entries += 1
        for b in junk:
            bt[b * 4:b * 4 + 4] = [0, 0, 0, 0]
        d[habs:habs + hn * 16] = M.encrypt(ht, M.HASH_TABLE_KEY)
        d[babs:babs + bn * 16] = M.encrypt(bt, M.BLOCK_TABLE_KEY)
        details.update(
            junk_blocks=len(junk), junk_entries=hash_entries, real_blocks=c['real'], uncertain_items=c['uncertain']
        )
        print('  junk: %d block(s) hidden (%d entry(ies) deleted); %d real and %d uncertain remain'
              % (len(junk), hash_entries, c['real'], c['uncertain']))

    details['fields'] = []
    if hs != 0x20:
        struct.pack_into('<I', d, hdr + 0x04, 0x20)
        details['fields'].append(('dwHeaderSize', hs, 0x20))
        print('  dwHeaderSize 0x%08X -> 0x00000020' % hs)
    if ver != 0:
        struct.pack_into('<H', d, hdr + 0x0C, 0)
        details['fields'].append(('wFormatVersion', ver, 0))
        print('  wFormatVersion %d -> 0' % ver)
    if asz != len(d) - hdr:
        struct.pack_into('<I', d, hdr + 0x08, len(d) - hdr)
        details['fields'].append(('dwArchiveSize', asz, len(d) - hdr))
        print('  dwArchiveSize 0x%08X -> 0x%08X' % (asz, len(d) - hdr))
    if ss & 0xFF00:
        struct.pack_into('<H', d, hdr + 0x0E, ss & 0xFF)
        details['fields'].append(('wSectorSize', ss, ss & 0xFF))
        print('  wSectorSize 0x%04X -> 0x%04X (only the low byte counts: the sector stays %d B)'
              % (ss, ss & 0xFF, M.header_sector(ss)))

    if d[:4] != b'HM3W':
        try:
            header, fname, flags, n_players = build_hm3w(orig)
        except Exception as e:
            header = None
            details['hm3w'] = 'failed'
            print('  HM3W: could not build it (%s)' % e)
        if header is not None:
            if hdr >= 0x200:
                d[0:0x200] = header
                details['hm3w'] = 'written'
                print('  HM3W written at 0x000: name %r, flags 0x%X, %d player(s)' % (fname, flags, n_players))
            elif prefix_hm3w:
                d = bytearray(header) + d
                hdr += 0x200
                details['hm3w'] = 'prefixed'
                print('  HM3W PREFIXED (the MPQ moves to 0x200; the positions are relative to it): name %r' % fname)
            else:
                details['hm3w'] = 'no_space'
                print('  HM3W: the MPQ starts at 0x%X, no room (use --add-hm3w to put the 0x200 bytes in front)'
                      % hdr)

    open(out, 'wb').write(bytes(d))
    print('  written: %s (%d bytes)' % (out, len(d)))

    issues, _ = malformed(bytes(d), hdr)
    details['malformed_after'] = issues
    details['output'] = out
    h2, _p = M.find_header(bytes(d), out)
    print('  revalidated: MALFORMED = %s; the header the game opens: 0x%X' % (' | '.join(issues) if issues else 'NO',
                                                                        h2.offset if h2 else -1))
    if chosen is not None:
        old = open(path, 'rb').read()
        diff = [i for i in range(0, orig_size, 1 << 20) if old[i:i + (1 << 20)] != bytes(d[i:i + (1 << 20)])]
        outside = 0
        for i in diff:
            for j in range(i, min(i + (1 << 20), orig_size)):
                if old[j] != d[j] and not (hdr + 4 <= j < hdr + 0x20) and not any(o <= j < o + 4 for o, _w in decoys):
                    outside += 1
        print(
            '  original bytes: %s; the file grew by %d B (the (listfile) and the new tables)'
            % (
                'identical outside the header (the data, the old tables and the junk stay as they were)'
                if not outside
                else '%d B CHANGED outside the header' % outside,
                len(d) - orig_size,
            )
        )
    try:
        b = R.Archive(out)
        listing = orig.read('(listfile)')
        all_items = list(PROBES) + list(name_list)
        if listing:
            all_items += [
                line.strip() for line in listing.decode('utf-8', 'surrogateescape').splitlines() if line.strip()
            ]
        if chosen is not None:
            all_items = sorted(chosen, key=lambda n: (n.lower(), n))
        bad, identical, unreadable_items = [], 0, 0
        for n in dict.fromkeys(all_items):
            try:
                x = orig.read(n)
            except Exception:
                unreadable_items += 1
                continue
            if x is None:
                continue
            try:
                y = b.read(n)
            except Exception:
                y = None
            if x != y:
                bad.append(n)
            else:
                identical += 1
        details['content'] = {'identical': identical, 'different': bad, 'unreadable_items': unreadable_items}
        print(
            '  content: %s'
            % (
                'DIFFERENT in %s' % bad[:10]
                if bad
                else 'identical in %d file(s) with a known name%s'
                % (
                    identical,
                    (' (%d already unreadable in the original)' % unreadable_items) if unreadable_items else '',
                )
            )
        )
    except Exception as e:
        print('  could not recheck the content: %s' % e)
    return out
