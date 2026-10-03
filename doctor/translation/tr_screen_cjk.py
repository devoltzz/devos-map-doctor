# Finds the Chinese text a player would still see after a translation.
import collections
import os
import re

from doctor.translation import kr_inventory as ki
from doctor.translation import tr_apply as ta
from doctor.translation import tr_extract as tx


CJK = re.compile('[぀-ヿ㐀-䶿一-鿿가-힣]')


def occurrences(line_list, tem_text=None, protected=None):
    present = tem_text or CJK.search
    inside = tx.lines_protected(line_list, tx.functions_protected(ta.TR) if protected is None else protected)
    out = []
    for ln, line in enumerate(line_list):
        for pos, lit in ki.literals(line):
            if not present(lit):
                continue
            if inside and inside[ln]:
                out.append((ln, lit, 'datum'))
            else:
                out.append((ln, lit, ta.classifica_occurrence(line, pos, lit, False)))
    return out


def script(file_path):
    body_text = open(file_path, encoding='utf-8', errors='surrogateescape').read()
    line_list, _sep = tx.quebra(body_text, jass=True)
    clusters = collections.Counter()
    ideog = collections.Counter()
    screen = collections.defaultdict(list)
    for ln, lit, cat in occurrences(line_list):
        g = cat.split(':', 1)[0]
        n = len(CJK.findall(lit))
        clusters[g] += 1
        ideog[g] += n
        if g == 'screen':
            screen[lit].append(ln + 1)
    return clusters, ideog, screen, line_list


def data_bytes(folder):
    por = collections.Counter()
    ex = collections.defaultdict(list)
    for root, _d, fs in os.walk(folder):
        for f in fs:
            if not f.lower().endswith('.txt'):
                continue
            p = os.path.join(root, f)
            for line in open(p, encoding='utf-8', errors='replace').read().splitlines():
                m = re.match(r'([A-Za-z0-9_]+)\s*=(.*)$', line)
                if m and CJK.search(m.group(2)):
                    hash_key = '%s:%s' % (f, m.group(1))
                    por[hash_key] += 1
                    if len(ex[hash_key]) < 3:
                        ex[hash_key].append(m.group(2)[:90])
    return por, ex
