# The names workflow: the file names of an issue, minus what the shared list has, into names/learned.txt.
import os
import re
import sys
import urllib.request

RX_BLOCK = re.compile(r'```[^\n]*\n(.*?)```', re.S)
RX_ATTACH = re.compile(r'https://github\.com/[^\s()<>\]]+\.txt')
SPECIAL = ('(listfile)', '(attributes)', '(signature)')
NAME_MAX = 300
NAMES_MAX = 50000
ATTACH_MAX = 5


def crypt_table():
    seed, t = 0x00100001, [0] * 0x500
    for i in range(0x100):
        k = i
        for _j in range(5):
            seed = (seed * 125 + 3) % 0x2AAAAB
            t1 = (seed & 0xFFFF) << 16
            seed = (seed * 125 + 3) % 0x2AAAAB
            t[k] = t1 | (seed & 0xFFFF)
            k += 0x100
    return t


CRYPT = crypt_table()


def hash_string(name, ht):
    s1, s2 = 0x7FED7FED, 0xEEEEEEEE
    for c in name.replace('/', '\\').encode('utf-8', 'replace').upper():
        s1 = CRYPT[(ht << 8) + c] ^ ((s1 + s2) & 0xFFFFFFFF)
        s2 = (c + s1 + s2 + (s2 << 5) + 3) & 0xFFFFFFFF
    return s1


def clean(line):
    n = line.strip().strip('`').strip().replace('/', '\\').lstrip('\\')
    if not n or n.lower() in SPECIAL or len(n.encode('utf-8', 'replace')) > NAME_MAX:
        return None
    if any(ord(c) < 0x20 or ord(c) == 0x7f for c in n) or n.count(' ') > 6:
        return None
    return n


def names_of(text):
    blocks = RX_BLOCK.findall(text)
    lines = '\n'.join(blocks).splitlines() if blocks else text.splitlines()
    for url in RX_ATTACH.findall(text)[:ATTACH_MAX]:
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                lines += r.read(4 << 20).decode('utf-8', 'replace').splitlines()
        except Exception as e:
            print('(the attachment %s could not be read: %s)' % (url, e), file=sys.stderr)
    out, seen, bad = [], set(), 0
    for line in lines:
        n = clean(line)
        if n is None:
            bad += line.strip() != ''
            continue
        if n.upper() in seen:
            continue
        seen.add(n.upper())
        out.append(n)
    return out, bad


def in_index(path, names):
    if not path or not os.path.isfile(path):
        return set()
    try:
        import numpy as np
        z = np.load(path)
        key = z['hash_key'] if 'hash_key' in z.files else z['chave']
    except Exception as e:
        print('(names.npz not read: %s)' % e, file=sys.stderr)
        return set()
    has = set()
    for n in names:
        k = (hash_string(n, 1) << 32) | hash_string(n, 2)
        p = int(np.searchsorted(key, np.uint64(k)))
        if p < len(key) and int(key[p]) == k:
            has.add(n)
    return has


def main(argv):
    body, learned = argv[1], argv[2]
    index = argv[3] if len(argv) > 3 else None
    with open(body, encoding='utf-8', errors='replace') as f:
        names, bad = names_of(f.read())
    if len(names) > NAMES_MAX:
        print(
            'This issue has %d file names, more than the %d one map can have: nothing was added. Please send the list '
            'of one map per issue.' % (len(names), NAMES_MAX)
        )
        return 0
    old = []
    if os.path.isfile(learned):
        with open(learned, encoding='utf-8', errors='replace') as f:
            old = [l_.rstrip('\r\n') for l_ in f if l_.strip()]
    old_keys = set(n.upper() for n in old)
    dup_index = in_index(index, names)
    new = [n for n in names if n.upper() not in old_keys and n not in dup_index]
    dups = len(names) - len(new)
    if new:
        with open(learned, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(sorted(old + new, key=str.upper)) + '\n')
    print(
        'I read %d file name(s): %d new (added to names/learned.txt, they go into the shared list of the next '
        'release), %d already in the list, %d line(s) that are not file names. Thank you!'
        % (len(names), len(new), dups, bad)
    )
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
