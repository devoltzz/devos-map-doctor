# Writes a text with a color gradient, one color code per character.
import re


RX_COD = re.compile(r'\|[cC][0-9a-fA-F]{8}|\|[rRnN]')
RX_SHORT_SEGMENT = re.compile(r'\|[cC][0-9a-fA-F]{8}([^|]{0,4})\|[rR]')
RX_NOT_CUT = re.compile(r'\d+(?:\.\d+)?%?|\\.')


def e_gradient(original, minimum=6):
    segs = RX_SHORT_SEGMENT.findall(original)
    return len(segs) >= minimum and sum(len(s) for s in segs) <= 2 * len(segs)


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
