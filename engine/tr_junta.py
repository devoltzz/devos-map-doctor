# Checks each translated text against its original.
import collections
import os
import re


HERE = os.path.dirname(os.path.abspath(__file__))
TR_DIR = os.environ.get('TR_DIR') or os.path.join(HERE, 'tr')
OUT = os.path.join(TR_DIR, 'out')
os.environ.setdefault('TR_DIR', TR_DIR)
import tr_validate as tv
import tr_gradient as tg

RX_COLOR = re.compile(r'\|[cC][0-9a-fA-F]{8}|\|[rRnN]')
RX_NUM = re.compile(r'\d+(?:\.\d+)?')
RX_MULT = re.compile(r'(\d+(?:\.\d+)?)[ \t]*([百千万亿]|[wW](?![A-Za-z]))')
MULT = {'百': 100, '千': 1000, '万': 10000, '亿': 100000000, 'w': 10000, 'W': 10000,
        '백': 100, '천': 1000, '만': 10000, '억': 100000000}
RX_MULT_KO = re.compile(r'(\d+(?:\.\d+)?)([천백]?[만억]|[천백])')
def _expande_mult(m):
    v = float(m.group(1)) * MULT[m.group(2)]
    return ' %d ' % round(v) if abs(v - round(v)) < 1e-6 else ' %s ' % v


RX_CADA1_ZH = re.compile(r'每\s*1(?![\d.])')
RX_CADA1_EN = re.compile(r'\b(every|each|per)\s+1(?![\d.])', re.I)


def numeros(t):
    t = RX_CADA1_EN.sub(r'\1', RX_CADA1_ZH.sub('每', t))
    return sorted(RX_NUM.findall(RX_MULT.sub(_expande_mult, RX_COLOR.sub(' ', t))))


def _value_ko(m):
    v = float(m.group(1))
    for c in m.group(2):
        v *= MULT[c]
    return ' %d ' % round(v) if abs(v - round(v)) < 1e-6 else ' %s ' % v


def leituras_ko(t, out_limit=8):
    ms = list(RX_MULT_KO.finditer(t))
    clusters = sorted(set(m.group(0) for m in ms))
    if not ms or len(clusters) > out_limit:
        return []
    out = []
    for bitmask in range(1, 2 ** len(clusters)):
        step_on = set(g for i, g in enumerate(clusters) if bitmask >> i & 1)
        pieces, end_pos = [], 0
        for m in ms:
            if m.group(0) in step_on:
                pieces.append(t[end_pos:m.start()])
                pieces.append(_value_ko(m))
                end_pos = m.end()
        pieces.append(t[end_pos:])
        out.append(numeros(''.join(pieces)))
    return out


RX_COMPOSTO_KO = re.compile(r'(\d+)\s*억((?:\s*\d+\s*[천백십만])+)')
RX_DECIMAL_VIRGULA = re.compile(r'(?<![\d,])(\d+),(\d{1,2})(?![\d,])')
RX_PART_KO = re.compile(r'(\d+)\s*([천백십만])')
VALUE_PART_KO = {'fala': {'천': 10 ** 7, '백': 10 ** 6, '십': 10 ** 5, '만': 10 ** 4},
                 'literal': {'천': 1000, '백': 100, '십': 10, '만': 10000}}


def leituras_compostas_ko(t, out_limit=4):
    ms = list(RX_COMPOSTO_KO.finditer(t))
    if not ms or len(ms) > out_limit:
        return []
    out = []
    for method in ('fala', 'literal'):
        pieces, end_pos = [], 0
        for m in ms:
            v = int(m.group(1)) * 10 ** 8
            for p in RX_PART_KO.finditer(m.group(2)):
                v += int(p.group(1)) * VALUE_PART_KO[method][p.group(2)]
            pieces += [t[end_pos:m.start()], ' %d ' % v]
            end_pos = m.end()
        pieces.append(t[end_pos:])
        s = ''.join(pieces)
        out.append(numeros(s))
        out.extend(leituras_ko(s))
    return out


RX_FAIXA_MULT_KO = re.compile(r'(\d+(?:\.\d+)?)(\s*~\s*)(\d+(?:\.\d+)?)([천백]?[만억]|[천백])')


RX_MAN_RESTO_KO = re.compile(r'(\d+)만\s*(\d{1,4})(?![\d.만천백억])')
RX_MAN_CHEON_KO = re.compile(r'(\d+)만\s*(\d)천(?![\d.만])')


def texts_ko(t):
    out = [t]
    if RX_DECIMAL_VIRGULA.search(t):
        out.append(RX_DECIMAL_VIRGULA.sub(r'\1.\2', t))
    if RX_FAIXA_MULT_KO.search(t):
        out += [RX_FAIXA_MULT_KO.sub(r'\1\4\2\3\4', x) for x in list(out)]
    if RX_MAN_RESTO_KO.search(t) or RX_MAN_CHEON_KO.search(t):
        def whole(x):
            x = RX_MAN_CHEON_KO.sub(lambda m: ' %d ' % (int(m.group(1)) * 10000 + int(m.group(2)) * 1000), x)
            return RX_MAN_RESTO_KO.sub(lambda m: ' %d ' % (int(m.group(1)) * 10000 + int(m.group(2))), x)
        out += [whole(x) for x in list(out)]
    return out


RX_QUOTE_SOLTA = re.compile(r'(?<!\\)"')
RX_SEP_LEVEL = re.compile(r',(?=\|[cC][0-9a-fA-F]{8})')
RX_OPEN_COLOR = re.compile(r'\|[cC][0-9a-fA-F]{8}')
RX_LEVEL_BETWEEN_QUOTES = re.compile(r'(?:^|,)"')


def list_com_quotes(t):
    return bool(RX_LEVEL_BETWEEN_QUOTES.search(t))


def virgulas_de_level(s, quoted):
    if not quoted:
        return [i for i, c in enumerate(s) if c == ',']
    pos, inside = [], False
    for i, c in enumerate(s):
        if c == '"' and (i == 0 or s[i - 1] != '\\'):
            inside = not inside
        elif c == ',' and not inside:
            pos.append(i)
    return pos


def levels_de(t, quoted):
    cuts = virgulas_de_level(t, quoted)
    return [t[a + 1:b] for a, b in zip([-1] + cuts, cuts + [len(t)])]


def fix_levels(item, en):
    n = item.get('level_list')
    quoted = list_com_quotes(item['t'])
    if n and quoted:
        n = len(virgulas_de_level(item['t'], True)) + 1
    if not n or len(virgulas_de_level(en, quoted)) == n - 1:
        return en
    zh = levels_de(item['t'], quoted)
    if len(zh) != n:
        return en
    if quoted:
        if all(p.startswith('"') for p in zh[1:]):
            virg = virgulas_de_level(en, True)
            cuts = [i for i in virg if en[i + 1:i + 2] == '"']
            if len(cuts) == n - 1:
                swap = set(virg) - set(cuts)
                return ''.join(';' if i in swap else ch for i, ch in enumerate(en))
            pieces = en.split('","')
            if len(pieces) == n and en.count('"') == 2 * (n - 1):
                return ','.join('"%s"' % p if z.startswith('"') else p.replace(',', ';') for p, z in zip(pieces, zh))
            if '"' not in en:
                cuts = [i for i, c in enumerate(en) if c == ',' and en[:i].rstrip().endswith('.')]
                if len(cuts) == n - 1:
                    pieces = [en[a + 1:b] for a, b in zip([-1] + cuts, cuts + [len(en)])]
                    if all(_mesmos_numbers(z, p) for z, p in zip(zh, pieces)):
                        return ','.join('"%s"' % p if z.startswith('"') else p.replace(',', ';')
                                        for p, z in zip(pieces, zh))
        return fix_levels_por_numbers(item, en)
    if not all(RX_OPEN_COLOR.match(p) for p in zh[1:]):
        return fix_levels_por_point(zh, en, fix_levels_por_numbers(item, en))
    pieces = RX_SEP_LEVEL.split(en)
    if len(pieces) != n:
        return fix_levels_por_point(zh, en, fix_levels_por_numbers(item, en))
    return ','.join(p.replace(',', ';') for p in pieces)


def fix_levels_por_point(zh, en, done):
    if done != en or not all(z.rstrip().endswith('.') for z in zh[:-1]):
        return done
    virg = [i for i, c in enumerate(en) if c == ',']
    cuts = [i for i in virg if en[:i].rstrip().endswith('.')]
    if len(cuts) != len(zh) - 1:
        return done
    swap = set(virg) - set(cuts)
    return ''.join(';' if i in swap else ch for i, ch in enumerate(en))


def _mesmos_numbers(a, b):
    ca, field_bytes = collections.Counter(numeros(a)), collections.Counter(numeros(b))
    return set((ca - field_bytes) + (field_bytes - ca)) <= {'1'}


def fix_levels_por_numbers(item, en):
    n = item.get('level_list')
    quoted = list_com_quotes(item['t'])
    zh = levels_de(item['t'], quoted)
    if n and quoted:
        n = len(zh)
    virg = virgulas_de_level(en, quoted)
    if not n or len(zh) != n or len(virg) < n - 1 or len(virg) > 400:
        return en
    tgt = zh
    sols = []

    def busca(k, begin, cuts):
        if len(sols) > 8:
            return
        if k == n - 1:
            if _mesmos_numbers(tgt[k], en[begin:]):
                sols.append(list(cuts))
            return
        for c in virg:
            if c < begin:
                continue
            seg = en[begin:c]
            if _mesmos_numbers(tgt[k], seg):
                cuts.append(c)
                busca(k + 1, c + 1, cuts)
                cuts.pop()
            elif collections.Counter(numeros(seg)) - collections.Counter(numeros(tgt[k])) - collections.Counter(
                    {'1': 99}):
                break

    busca(0, 0, [])
    if len(sols) > 1:
        def ok_color(c, z):
            mz = RX_OPEN_COLOR.match(z)
            if not mz:
                return True
            me = RX_OPEN_COLOR.match(en[c + 1:])
            return bool(me) and me.group(0).lower() == mz.group(0).lower()
        sols = [s for s in sols if all(ok_color(c, z) for c, z in zip(s, zh[1:]))]
    if len(sols) != 1:
        return en
    cuts = set(sols[0])
    swap = set(virg) - cuts
    return ''.join(';' if i in swap else ch for i, ch in enumerate(en))


def fix_simbolos(orig, en):
    missing_seta = orig.count('→') - en.count('→')
    if missing_seta > 0 and en.count('->') >= missing_seta and '->' not in orig:
        en = en.replace('->', '→', missing_seta)
    order = [c for c in orig if c in '※§']
    existing = [c for c in en if c in '※§']
    extra = en.count('#') - orig.count('#')
    if order and not existing and extra == len(order) and '#' not in orig:
        it = iter(order)
        en = ''.join(next(it) if c == '#' else c for c in en)
    return en


def fixable(item, entry, en):
    done = []
    if not isinstance(en, str):
        return en, done
    if any(e.startswith('color codes') for e in tv.check(entry, en)) and tg.e_gradient(item['t']):
        en = tg.recolore(item['t'], en)
        done.append('gradient')
    if '"' not in entry['text'] and RX_QUOTE_SOLTA.search(en):
        en = RX_QUOTE_SOLTA.sub("'", en)
        done.append('quoted')
    if '\n' not in entry['text'] and '\r' not in entry['text'] and ('\n' in en or '\r' in en):
        en = re.sub(r'\s*[\r\n]+\s*', ' ', en)
        done.append('quebra crua')
    new = fix_simbolos(entry['text'], en)
    if new != en:
        en = new
        done.append('simbolos')
    new = fix_levels(item, en)
    if new != en:
        en = new
        done.append('level_list')
    from tr_commands import e_command
    if e_command(entry):
        from tr_commands import canonico
        new = canonico(en, entry['text'])
        if new != en:
            en = new
            done.append('statement')
    return en, done


def errors_de(item, entry, en):
    errs = tv.check(entry, en)
    if entry['kind'] == 'command' and not entry['text'].startswith('-'):
        errs = [e for e in errs if not e.startswith(('the command is not there', 'espaco final'))]
    if isinstance(en, str) and len(en) <= 3.5 * len(entry['text']) + 40:
        errs = [e for e in errs if not e.startswith('muito longo')]
    if isinstance(en, str):
        if tg.e_gradient(item['t']):
            zh_n, en_n = numeros(RX_COLOR.sub('', item['t'])), numeros(RX_COLOR.sub('', en))
        else:
            zh_n, en_n = numeros(item['t']), numeros(en)
        a, b = collections.Counter(zh_n), collections.Counter(en_n)
        if set((a - b) + (b - a)) <= {'1'}:
            zh_n = en_n
        elif RX_MULT_KO.search(item['t']) or RX_DECIMAL_VIRGULA.search(item['t']):
            text_ko = RX_COLOR.sub('', item['t']) if tg.e_gradient(item['t']) else item['t']
            for tk in texts_ko(text_ko):
                achou = False
                for listing in [numeros(tk)] + leituras_ko(tk) + leituras_compostas_ko(tk):
                    ko = collections.Counter(listing)
                    if set((ko - b) + (b - ko)) <= {'1'}:
                        achou = True
                        break
                if achou:
                    zh_n = en_n
                    break
        if zh_n != en_n:
            errs.append('numeros diferentes (%s -> %s)' % (' '.join(numeros(item['t']))[:40],
                                                           ' '.join(numeros(en))[:40]))
        if item.get('level_list'):
            quoted = list_com_quotes(item['t'])
            expected_len = len(virgulas_de_level(item['t'], True)) if quoted else item['level_list'] - 1
            finding = len(virgulas_de_level(en, quoted))
            if finding != expected_len:
                errs.append('niveis: %d virgulas, esperado %d' % (finding, expected_len))
            elif quoted and en.count('"') % 2 != item['t'].count('"') % 2:
                errs.append('niveis: %d aspas, esperado %d' % (en.count('"'), item['t'].count('"')))
    return errs
