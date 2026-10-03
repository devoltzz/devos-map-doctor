# Restores object ids scrambled by the PG2 protector.
import collections
import os
import re
import shutil
import struct
import sys

from doctor.mpq import mpqread
from doctor.data import objects


TYPES = (('w3u', False, 'unit'), ('w3t', False, 'item'), ('w3a', True, 'ability'), ('w3b', False, 'destructible'),
         ('w3d', True, 'doodad'), ('w3h', False, 'buff'), ('w3q', True, 'upgrade'))
PREFIX = {'w3t': 'I', 'w3a': 'A', 'w3b': 'B', 'w3d': 'D', 'w3h': 'B', 'w3q': 'R'}
NAME_FIELDS = (b'unam', b'anam', b'bnam', b'dnam', b'fnam', b'gnam')
B36 = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
M32 = 0xFFFFFFFF
RX_ALNUM = re.compile(rb'[0-9A-Za-z]{4}\Z')
RX_SCRIPT = re.compile(rb'(?P<str>"(?:[^"\\]|\\.)*")|(?P<comment>//[^\r\n]*)'
                       rb"|(?P<sum_expr>\(\s*'(?P<a>(?:[^'\\]|\\.){4})'\s*\+\s*'(?P<b>(?:[^'\\]|\\.){4})'\s*\))"
                       rb"|(?P<raw>'(?P<r>(?:[^'\\]|\\.){4})')"
                       rb'|(?P<num>(?<![\w.$])(?:0[xX][0-9A-Fa-f]+|\$[0-9A-Fa-f]+|\d+)(?![\w.]))', re.S)


def is_scrambled(idb):
    return not RX_ALNUM.match(idb)


def unescape(b):
    return re.sub(rb'\\(.)', lambda m: m.group(1), b)


def rawcode_value(b):
    v = 0
    for c in b:
        v = (v * 256 + (c - 256 if c >= 128 else c)) & M32
    return v


def id_value(idb):
    return struct.unpack('>I', idb)[0]


def object_name(mods):
    for m in mods:
        if m[0].encode('latin-1') in NAME_FIELDS and m[1] == 3:
            return m[4].decode('utf-8', 'replace')
    return ''


def load_data(a):
    files_ = {}
    for ext, level, _t in TYPES:
        try:
            d = a.read('war3map.' + ext)
        except Exception:
            d = None
        if not d:
            continue
        ver, objs, pos = objects.read_objects_bytes(d, level, 'war3map.' + ext, with_end=True)
        if objects.write_objects_bytes(ver, objs, level) != d[:pos]:
            raise ValueError('war3map.%s: the round trip without changes does not match -- not rewriting' % ext)
        files_[ext] = (ver, objs, level, d, pos)
    return files_


def script_rawcodes(j):
    in_use = set()
    for m in RX_SCRIPT.finditer(j):
        if m.group('raw'):
            in_use.add(unescape(m.group('r')))
    return in_use


def choose_ids(files_, used_in_script, avoid=()):
    in_use = set(used_in_script)
    for ext, (_v, objs, _n, _d, _p) in files_.items():
        for _t, orig, new, _m in objs:
            in_use.add(orig.encode('latin-1'))
            in_use.add(new.encode('latin-1'))
    whole_types = set()
    for ext, (_v, objs, _n, _d, _p) in files_.items():
        new_ids = [o[2].encode('latin-1') for o in objs if o[0] == 1]
        if new_ids and sum(1 for i in new_ids if is_scrambled(i)) * 2 > len(new_ids):
            whole_types.add(ext)
    tally = collections.Counter()
    new_ones = {}
    for ext, (_v, objs, _n, _d, _p) in files_.items():
        for tab, orig, new, mods in objs:
            nb = new.encode('latin-1')
            if tab != 1 or nb in new_ones or nb in avoid or not (ext in whole_types or is_scrambled(nb)):
                continue
            pref = orig[0] if ext == 'w3u' else PREFIX[ext]
            if ext == 'w3u' and (0x41 <= nb[0] <= 0x5A) != pref.isupper():
                raise ValueError(
                    'unit %r (base %r): the 1st letter of the scrambled id and that of the base disagree on whether it is a hero'
                    % (nb, orig)
                )
            while True:
                n = tally[pref]
                tally[pref] += 1
                if n >= 36 ** 3:
                    raise ValueError('ids %s000..%sZZZ exhausted' % (pref, pref))
                cand = (pref + B36[n // 1296] + B36[n // 36 % 36] + B36[n % 36]).encode('latin-1')
                if cand not in in_use:
                    break
            in_use.add(cand)
            new_ones[nb] = (cand, ext, orig, object_name(mods))
    return new_ones


def rewrite_objects(files_, new_ones):
    output = {}
    tally = collections.Counter()
    ids = {k: v[0] for k, v in new_ones.items()}
    for ext, (ver, objs, level, d, pos) in files_.items():
        new_objs = []
        changed = False
        for tab, orig, new, mods in objs:
            ob, nb = orig.encode('latin-1'), new.encode('latin-1')
            if nb in ids:
                nb = ids[nb]
                tally['object id'] += 1
                changed = True
            if ob in ids:
                ob = ids[ob]
                tally['base id'] += 1
                changed = True
            mods2 = []
            for m in mods:
                field_id, kind, level_, pointer, val, end_pos = m
                if kind == 3:
                    pieces = val.split(b',')
                    swapped = [ids.get(p, p) for p in pieces]
                    n = sum(1 for p, q in zip(pieces, swapped) if p != q)
                    if n:
                        val = b','.join(swapped)
                        tally['text value (%s)' % field_id] += n
                        changed = True
                elif kind == 0:
                    b = struct.pack('>i', val)
                    if b in ids:
                        val = struct.unpack('>i', ids[b])[0]
                        tally['integer value (%s)' % field_id] += 1
                        changed = True
                if end_pos in ids:
                    end_pos = ids[end_pos]
                    tally['end of record'] += 1
                    changed = True
                mods2.append((field_id, kind, level_, pointer, val, end_pos))
            new_objs.append((tab, ob.decode('latin-1'), nb.decode('latin-1'), mods2))
        if changed:
            output[ext] = objects.write_objects_bytes(ver, new_objs, level) + d[pos:]
    return output, tally


def rewrite_script(j, new_ones):
    ids = {id_value(k): v[0] for k, v in new_ones.items()}
    tally = collections.Counter()

    def swap(m):
        if m.group('str') or m.group('comment'):
            return m.group(0)
        if m.group('sum_expr'):
            v = (rawcode_value(unescape(m.group('a'))) + rawcode_value(unescape(m.group('b')))) & M32
            if v in ids:
                tally['sum of two rawcodes'] += 1
                return b"'" + ids[v] + b"'"
            return m.group(0)
        if m.group('raw'):
            v = rawcode_value(unescape(m.group('r')))
            if v in ids:
                tally['direct rawcode'] += 1
                return b"'" + ids[v] + b"'"
            return m.group(0)
        t = m.group('num')
        v = int(t[2:], 16) if t[:2] in (b'0x', b'0X') else (int(t[1:], 16) if t[:1] == b'$' else int(t))
        if v & M32 in ids and v <= M32:
            tally['numeric'] += 1
            return b"'" + ids[v & M32] + b"'"
        return t

    return RX_SCRIPT.sub(swap, j), tally


def leftovers_in_script(j, new_ones):
    ids = set(id_value(k) for k in new_ones)
    n = 0
    for m in RX_SCRIPT.finditer(j):
        if m.group('sum_expr'):
            v = (rawcode_value(unescape(m.group('a'))) + rawcode_value(unescape(m.group('b')))) & M32
            n += v in ids
        elif m.group('raw'):
            n += rawcode_value(unescape(m.group('r'))) in ids
    return n


def main(argv):
    args = [x for x in argv[1:] if not x.startswith('--')]
    op = dict(x[2:].split('=', 1) if '=' in x else (x[2:], '1') for x in argv[1:] if x.startswith('--'))
    if len(args) < 1 or (len(args) < 2 and 'count-only' not in op):
        print(__doc__)
        return 2
    entry = args[0]
    a = mpqread.Archive(entry)
    j_name = 'war3map.j' if a.find('war3map.j') else 'scripts\\war3map.j'
    j = a.read(j_name)
    if j is None:
        raise SystemExit('the map has neither war3map.j nor scripts\\war3map.j')
    files_ = load_data(a)
    lst = a.read('(listfile)') or b''
    to_skip = {'war3map.' + e for e, _n, _t in TYPES} | {j_name.lower(), '(listfile)', '(attributes)', '(signature)'}
    others = {}
    for n in lst.decode('utf-8', 'surrogateescape').replace('\r\n', '\n').split('\n'):
        if (
            not n.strip()
            or n.lower() in to_skip
            or not re.search(r'\.(w3i|doo|txt|slk|w3s|w3r|w3c|wtg|wct|imp|fdf)$', n, re.I)
        ):
            continue
        try:
            d = a.read(n)
        except Exception:
            continue
        if d:
            others[n] = d
    candidates = set()
    for _e, (_v, objs, _n, _d, _p) in files_.items():
        candidates |= set(o[2].encode('latin-1') for o in objs if o[0] == 1)
    avoid = {}
    for n, d in others.items():
        for k in candidates:
            if k in d:
                avoid.setdefault(k, []).append(n)
    new_ones = choose_ids(files_, script_rawcodes(j), avoid)
    by_kind = collections.Counter(v[1] for v in new_ones.values())
    print(
        'ids regenerated: %d %s (heroes: %d)'
        % (len(new_ones), dict(by_kind), sum(1 for v in new_ones.values() if v[1] == 'w3u' and v[0][:1].isupper()))
    )
    kept = sorted((k, v) for k, v in avoid.items() if is_scrambled(k))
    print('kept (referenced in a file that is not rewritten): %s' % ([(k, v) for k, v in kept] or 'none'))
    obj, c_obj = rewrite_objects(files_, new_ones)
    j2, c_j = rewrite_script(j, new_ones)
    print('object files: %s' % dict(c_obj))
    print('script (%s): %s; leftovers of a regenerated id: %d' % (j_name, dict(c_j), leftovers_in_script(j2, new_ones)))
    remaining_sums = sum(1 for m in RX_SCRIPT.finditer(j2) if m.group('sum_expr'))
    print('sums of two rawcodes left in the script (ids that stayed): %d' % remaining_sums)
    if 'count-only' in op:
        return 0
    if leftovers_in_script(j2, new_ones):
        raise SystemExit('a reference was left in the script: not writing')
    output = args[1]
    if os.path.normcase(os.path.abspath(output)) == os.path.normcase(os.path.abspath(entry)):
        raise SystemExit('the output must be a different file (the original does not change)')
    shutil.copyfile(entry, output)
    from doctor.mpq import mpqadd
    replacements = [('war3map.' + e, b) for e, b in obj.items()] + [(j_name, j2)]
    mpqadd.add_files(output, replacements, log=lambda *x: None)
    b = mpqread.Archive(output)
    bad_ones = [n for n, data_bytes in replacements if b.read(n) != data_bytes]
    files2 = load_data(b)
    rest = sum(1 for _e, (_v, objs, _n, _d, _p) in files2.items() for o in objs
               if o[0] == 1 and o[2].encode('latin-1') in new_ones)
    print('new map: %s -- %d file(s) replaced, read back %s; objects still with an old regenerated id: %d'
          % (output, len(replacements), 'identical' if not bad_ones else 'DIFFERENT %s' % bad_ones, rest))
    tsv = op.get('tsv')
    if tsv:
        with open(tsv, 'w', encoding='utf-8') as f:
            f.write('old_id_hex\tnew_id\ttype\tbase\tname\n')
            for k, (nv, ext, base, fname) in sorted(new_ones.items(), key=lambda x: (x[1][1], x[1][0])):
                f.write(
                    '%s\t%s\t%s\t%s\t%s\n'
                    % (
                        k.hex(),
                        nv.decode('latin-1'),
                        dict((e, t) for e, _n, t in TYPES)[ext],
                        base,
                        fname.replace('\t', ' ').replace('\n', ' '),
                    )
                )
        print('table: %s' % tsv)
    return 1 if bad_ones or rest else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
