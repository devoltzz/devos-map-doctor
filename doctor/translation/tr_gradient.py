# Writes a text with a color gradient, one color code per character.
import collections
import glob
import json
import os
import re
import sys


RX_COLOR = re.compile(r'\|[cC][0-9a-fA-F]{8}|\|[rR]')
RX_COD = re.compile(r'\|[cC][0-9a-fA-F]{8}|\|[rRnN]')
RX_SHORT_SEGMENT = re.compile(r'\|[cC][0-9a-fA-F]{8}([^|]{0,4})\|[rR]')
RX_NOT_CUT = re.compile(r'\d+(?:\.\d+)?%?|\\.')


def e_gradient(original, minimum=6):
    segs = RX_SHORT_SEGMENT.findall(original)
    return len(segs) >= minimum and sum(len(s) for s in segs) <= 2 * len(segs)


RX_ORIGINAL_COLOR = re.compile(r'\|[cC][0-9a-fA-F]{8}')


def copy_codes(original, translation):
    right_codes = RX_ORIGINAL_COLOR.findall(original)
    marks = [m.start() for m in re.finditer(r'\|[cC]', translation)]
    if not right_codes or len(right_codes) != len(marks):
        return None
    out, pos = [], 0
    for begin, right_code in zip(marks, right_codes):
        hex_digits = right_code[2:]
        k = 0
        while (
            k < 8 and begin + 2 + k < len(translation) and translation[begin + 2 + k].lower() == hex_digits[k].lower()
        ):
            k += 1
        if k < 6:
            return None
        out.append(translation[pos:begin])
        out.append(right_code)
        pos = begin + 2 + k
    out.append(translation[pos:])
    return ''.join(out)


def _tokens(original):
    out, pos = [], 0
    for m in RX_COD.finditer(original):
        if m.start() > pos:
            out.append((False, original[pos:m.start()]))
        out.append((True, m.group(0)))
        pos = m.end()
    if pos < len(original):
        out.append((False, original[pos:]))
    return out


def _cortes_proibidos(plain_name):
    proib = set()
    for m in RX_NOT_CUT.finditer(plain_name):
        proib.update(range(m.start() + 1, m.end()))
    return proib


def recolore(original, translation):
    toks = _tokens(original)
    texts = [i for i, (code_part, _t) in enumerate(toks) if not code_part]
    plain_name = RX_COD.sub('', translation)
    if not texts:
        return ''.join(t for _c, t in toks)
    weights = [max(len(toks[i][1]), 1) for i in texts]
    total = float(sum(weights))
    proib = _cortes_proibidos(plain_name)
    cuts, acum, prev_item = [], 0, 0
    for p in weights[:-1]:
        acum += p
        c = int(round(len(plain_name) * acum / total))
        c = max(c, prev_item)
        while c in proib and c < len(plain_name):
            c += 1
        cuts.append(c)
        prev_item = c
    chunks, begin = [], 0
    for c in cuts + [len(plain_name)]:
        chunks.append(plain_name[begin:c])
        begin = c
    out = []
    k = 0
    for code_part, t in toks:
        if code_part:
            out.append(t)
        else:
            out.append(chunks[k])
            k += 1
    return ''.join(out)


def without_color(body_text):
    return RX_COLOR.sub('', body_text)


def for_agent(work, dest, from_=0, cap=800):
    os.makedirs(dest, exist_ok=True)
    old_streams, gl, n = [], {}, 0
    for p in sorted(glob.glob(os.path.join(work, 'b_*.json'))):
        doc = json.load(open(p, encoding='utf-8'), object_pairs_hook=collections.OrderedDict)
        for it in doc['item_entries']:
            if e_gradient(it['t']):
                it['t'] = without_color(it['t'])
                it['gradient'] = True
        if int(os.path.basename(p)[2:-5]) >= from_:
            json.dump(
                doc, open(os.path.join(dest, os.path.basename(p)), 'w', encoding='utf-8'), ensure_ascii=False, indent=1
            )
            n += 1
        else:
            old_streams += [it for it in doc['item_entries'] if it.get('gradient')]
            gl.update(doc['glossary'])
    slices = [old_streams[i:i + cap] for i in range(0, len(old_streams), cap)]
    for i, f in enumerate(slices):
        doc = collections.OrderedDict(glossary=gl, item_entries=f)
        json.dump(doc, open(os.path.join(dest, 'g_%03d.json' % i), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return n, len(slices)


if __name__ == '__main__' and sys.argv[1:2] == ['para-agente']:
    _of_it = int(next((a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--de=')), 0))
    print('blocks, g files:', for_agent(sys.argv[2], sys.argv[3], _of_it))
elif __name__ == '__main__':
    zh = '|cffff0000这|r|cfffd060a一|r|cfffb0c14切|r|cfff9121e.|r'
    en = '|cffff0000Th|r|cfffd060ais is|r|cfffb0c14 al|r|cfff9121el.|r'
    new = recolore(zh, 'All of |cffff0000this|r 10000.')
    assert RX_COD.findall(new) == RX_COD.findall(zh), new
    assert '10000' in RX_COD.sub('', new) and RX_COD.sub('', new) == 'All of this 10000.', new
    assert e_gradient('|cffff0000a|r' * 6) and not e_gradient('|cffff0000abcdefgh|r' * 6)
    header = '|CffFF9900[S]: dif --|r|cffffff00A|r|cffedff12B|r|cffdbff24C|r |cffc9ff36D|r'
    new = recolore(header, '[System Fairy]: Current difficulty -- Holy Fairy')
    assert RX_COD.findall(new) == RX_COD.findall(header), new
    print('ok:', new)
