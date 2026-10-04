# The release obfuscator of a map script: no comment, every name renamed, strings and raw codes encrypted (used here on the script a cheat pack was injected into).
import collections
import hashlib
import json
import os
import random
import re
import subprocess
import sys
import time

from doctor.script import sstrhash


TOKEN = re.compile(r'''(?P<com>//[^\n]*)|(?P<str>"(?:[^"\\]|\\.)*")|(?P<raw>'(?:[^'\\]|\\.)*')'''
                   r'''|(?P<num>0[xX][0-9A-Fa-f]+|\$[0-9A-Fa-f]+|\d+\.\d*|\.\d+|\d+)|(?P<id>[A-Za-z_]\w*)'''
                   r'''|(?P<nl>\r?\n)|(?P<ws>[ \t\r\f\v]+)|(?P<op>.)''', re.S)
PECA = re.compile(r'\\.|.', re.S)
PECA_PALAVRA = re.compile(r'\\.|[A-Za-z0-9]+|.', re.S)
PALAVRAS = set('''function takes returns return nothing endfunction local set call if then else elseif
endif loop endloop exitwhen globals endglobals constant native type extends array and or not true false
null debug integer real boolean string handle code'''.split())
MODULO = 9973
LARG = 4
SEG = 250
ALFABETO = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
TETO_VETOR = 30000


def arg(nome, padrao=None):
    for a in sys.argv[1:]:
        if a.startswith('--%s=' % nome):
            return a.split('=', 1)[1]
    return padrao


def flag(nome):
    return ('--%s' % nome) in sys.argv[1:]


def tokeniza(texto):
    kinds, texts = [], []
    ka, ta = kinds.append, texts.append
    for m in TOKEN.finditer(texto):
        ka(m.lastgroup)
        ta(m.group())
    return kinds, texts


def ids_do_motor(caminhos):
    out = set()
    for c in caminhos:
        t = open(c, 'rb').read().decode('utf-8', 'surrogateescape')
        for m in TOKEN.finditer(t):
            if m.lastgroup == 'id':
                out.add(m.group())
    return out


class Funcao(object):
    def __init__(self, nome, li0):
        self.nome = nome
        self.li0 = li0
        self.li1 = None
        self.locais = []
        self.novos = {}


class Gerador(object):
    def __init__(self, rng, proibidos):
        self.rng = rng
        self.usados = set(proibidos)

    def novo(self, lmin, lmax, locais=None):
        rng = self.rng
        while True:
            n = rng.randint(lmin, lmax)
            s = rng.choice('Il') + ''.join(rng.choice('Il1') for _ in range(n - 1))
            if s in self.usados or (locais is not None and s in locais):
                continue
            if locais is None:
                self.usados.add(s)
            else:
                locais.add(s)
            return s


def linhas_de(kinds, texts):
    linhas = []
    atual = []
    espaco = {}
    viu = False
    for i, k in enumerate(kinds):
        if k == 'nl':
            linhas.append(atual)
            atual = []
            viu = False
            continue
        if k == 'ws' or k == 'com':
            viu = True
            continue
        if viu:
            espaco[i] = True
        viu = False
        atual.append(i)
    linhas.append(atual)
    return linhas, espaco


def estrutura(linhas, texts):
    globais = []
    natives = set()
    funcoes = {}
    ordem = []
    li_globals = li_endglobals = None
    estado = 'topo'
    atual = None
    for li, lin in enumerate(linhas):
        if not lin:
            continue
        t0 = texts[lin[0]]
        if estado == 'globals':
            if t0 == 'endglobals':
                estado = 'topo'
                li_endglobals = li
                continue
            j = 0
            const = False
            if texts[lin[j]] == 'constant':
                const = True
                j += 1
            tipo = texts[lin[j]]
            j += 1
            arr = False
            if j < len(lin) and texts[lin[j]] == 'array':
                arr = True
                j += 1
            nome_i = lin[j]
            ini = None
            if j + 1 < len(lin) and texts[lin[j + 1]] == '=':
                ini = lin[j + 2:]
            globais.append({'nome': texts[nome_i], 'const': const, 'tipo': tipo, 'arr': arr, 'ini': ini,
                            'li': li, 'j_nome': j})
            continue
        if t0 == 'globals':
            estado = 'globals'
            li_globals = li
            continue
        t1 = texts[lin[1]] if len(lin) > 1 else ''
        if t0 == 'native' or (t0 == 'constant' and t1 == 'native'):
            natives.add(texts[lin[1 if t0 == 'native' else 2]])
            continue
        if t0 == 'function' or (t0 == 'constant' and t1 == 'function'):
            j = 1 if t0 == 'function' else 2
            nome = texts[lin[j]]
            atual = Funcao(nome, li)
            funcoes[nome] = atual
            ordem.append(nome)
            k = j + 1
            if texts[lin[k]] == 'takes' and texts[lin[k + 1]] != 'nothing':
                k += 1
                while k < len(lin) and texts[lin[k]] != 'returns':
                    if texts[lin[k]] == ',':
                        k += 1
                        continue
                    atual.locais.append(texts[lin[k + 1]])
                    k += 2
            estado = 'funcao'
            continue
        if estado == 'funcao':
            if t0 == 'endfunction':
                atual.li1 = li
                estado = 'topo'
                atual = None
                continue
            if t0 == 'local':
                j = 2
                if texts[lin[j]] == 'array':
                    j += 1
                atual.locais.append(texts[lin[j]])
    return globais, natives, funcoes, ordem, li_globals, li_endglobals


def fecha(lin, texts, a):
    prof = 0
    for b in range(a, len(lin)):
        t = texts[lin[b]]
        if t == '(':
            prof += 1
        elif t == ')':
            prof -= 1
            if prof == 0:
                return b
    return None


def conteudo(tok):
    return tok[1:-1]


def operandos(lin, texts, a, b):
    while a < b and texts[lin[a]] == '(' and fecha(lin, texts, a) == b:
        a += 1
        b -= 1
    out = []
    prof = 0
    ini = a
    for c in range(a, b + 1):
        t = texts[lin[c]]
        if t == '(':
            prof += 1
        elif t == ')':
            prof -= 1
        elif t == '+' and prof == 0:
            out.append((ini, c - 1))
            ini = c + 1
    out.append((ini, b))
    return out


def literal_so(lin, texts, kinds, a, b):
    while a < b and texts[lin[a]] == '(' and texts[lin[b]] == ')':
        a += 1
        b -= 1
    if a == b and kinds[lin[a]] == 'str':
        return conteudo(texts[lin[a]])
    return None


def pecas(s, rx=PECA):
    return rx.findall(s)


def base36(v, alf, n=4):
    d = []
    for _ in range(n):
        d.append(alf[v % 36])
        v //= 36
    return ''.join(reversed(d))


def main():
    t0 = time.time()
    entrada = arg('j')
    saida = arg('saida')
    common = arg('common')
    blizz = arg('blizzard')
    if not (entrada and saida and common and blizz):
        print(__doc__)
        return 2
    bruto = open(entrada, 'rb').read()
    if bruto.startswith(b'\xef\xbb\xbf'):
        bruto = bruto[3:]
    texto = bruto.decode('utf-8', 'surrogateescape')
    semente = int(arg('semente', '0') or 0) or int(hashlib.sha256(bruto).hexdigest()[:12], 16)
    rng = random.Random(semente)
    faz_nomes = not flag('sem-nomes')
    faz_strings = not flag('sem-strings')
    faz_ids = not flag('sem-ids')
    bloco = int(arg('bloco', '4000'))
    rx_peca = PECA_PALAVRA if arg('pecas', 'caractere') == 'palavra' else PECA
    manter = set(x for x in (arg('manter', '') or '').split(',') if x)

    kinds, texts = tokeniza(texto)
    linhas, espaco = linhas_de(kinds, texts)
    globais, natives, funcoes, ordem, li_g, li_eg = estrutura(linhas, texts)
    if li_g is None or li_eg is None or 'main' not in funcoes:
        raise SystemExit('ERRO: esperava um bloco globals e a funcao main')
    motor = ids_do_motor([common, blizz])
    print('entrada: %s (%d B, %d linhas, %d tokens); funcoes %d, globais %d, natives %d; semente %d'
          % (entrada, len(bruto), len(linhas), len(kinds), len(funcoes), len(globais), len(natives), semente))

    dona = [None] * len(linhas)
    for f in funcoes.values():
        for li in range(f.li0, (f.li1 or f.li0) + 1):
            dona[li] = f

    chama = {}
    for f in funcoes.values():
        alvo = set()
        for li in range(f.li0 + 1, f.li1 or f.li0):
            lin = linhas[li]
            for p, ti in enumerate(lin):
                if kinds[ti] == 'id' and texts[ti] in funcoes:
                    prev = texts[lin[p - 1]] if p > 0 else ''
                    prox = texts[lin[p + 1]] if p + 1 < len(lin) else ''
                    if prox == '(' or prev == 'function':
                        alvo.add(texts[ti])
        chama[f.nome] = alvo
    do_config = set()
    pilha = ['config'] if 'config' in funcoes else []
    while pilha:
        n = pilha.pop()
        if n in do_config:
            continue
        do_config.add(n)
        pilha.extend(chama.get(n, ()))

    congelado = set()
    lidos_cedo = set()
    for g in globais:
        if g['ini']:
            for ti in g['ini']:
                congelado.add(ti)
                if kinds[ti] == 'id':
                    lidos_cedo.add(texts[ti])
    for n in do_config:
        f = funcoes[n]
        for li in range(f.li0, (f.li1 or f.li0) + 1):
            for ti in linhas[li]:
                congelado.add(ti)
                if kinds[ti] == 'id':
                    lidos_cedo.add(texts[ti])
    fm = funcoes['main']
    li_primeira = None
    for li in range(fm.li0 + 1, fm.li1):
        lin = linhas[li]
        if not lin:
            continue
        if texts[lin[0]] == 'local':
            if len(lin) > 3:
                eq = [p for p, ti in enumerate(lin) if texts[ti] == '=']
                if eq:
                    for ti in lin[eq[0] + 1:]:
                        congelado.add(ti)
            continue
        li_primeira = li
        break
    if li_primeira is None:
        li_primeira = fm.li1

    convertidas = {}
    for g in globais:
        ini = g['ini']
        if g['arr'] or not ini or g['nome'] in lidos_cedo:
            continue
        a, b = 0, len(ini) - 1
        while a < b and texts[ini[a]] == '(' and texts[ini[b]] == ')':
            a += 1
            b -= 1
        if a != b:
            continue
        ti = ini[a]
        if (kinds[ti] == 'str' and g['tipo'] == 'string' and faz_strings and texts[ti] != '""') or \
           (kinds[ti] == 'raw' and g['tipo'] == 'integer' and faz_ids):
            convertidas[g['nome']] = ti
            congelado.discard(ti)

    proibidos = set(motor) | PALAVRAS | set(natives) | manter | set(funcoes) | set(g['nome'] for g in globais)
    ger = Gerador(rng, proibidos)
    manter_f = set(['main', 'config']) | manter | motor | natives
    fmap, gmap = {}, {}
    if faz_nomes:
        nomes_f = [n for n in ordem if n not in manter_f]
        for n in nomes_f:
            fmap[n] = ger.novo(10, 16)
        for g in globais:
            if g['nome'] not in manter and g['nome'] not in motor:
                gmap[g['nome']] = ger.novo(10, 16)
        for f in funcoes.values():
            usados = set()
            for n in f.locais:
                if n not in f.novos:
                    f.novos[n] = ger.novo(3, 9, usados)

    subst = {}
    apagar = set()
    antes = {}
    depois = {}
    padroes = set()
    n_ef_lit = n_ef_din = 0
    for f in funcoes.values():
        for li in range(f.li0 + 1, f.li1 or f.li0):
            lin = linhas[li]
            for p, ti in enumerate(lin):
                if kinds[ti] != 'id' or texts[ti] != 'ExecuteFunc':
                    continue
                if p + 1 >= len(lin) or texts[lin[p + 1]] != '(':
                    continue
                q = fecha(lin, texts, p + 1)
                a, b = p + 2, q - 1
                ops = operandos(lin, texts, a, b)
                vals = [literal_so(lin, texts, kinds, x, y) for x, y in ops]
                if all(v is not None for v in vals):
                    nome = ''.join(vals)
                    if nome in fmap:
                        subst[lin[a]] = '"%s"' % fmap[nome]
                        kinds[lin[a]] = 'str'
                        for c in range(a + 1, b + 1):
                            apagar.add(lin[c])
                        n_ef_lit += 1
                    continue
                prefixo = vals[0] if len(vals) > 1 and vals[0] is not None else ''
                sufixo = vals[-1] if len(vals) > 1 and vals[-1] is not None else ''
                padroes.add((prefixo, sufixo))
                antes[lin[a]] = antes.get(lin[a], '') + '\x00NOMEFN('
                depois[lin[b]] = ')' + depois.get(lin[b], '')
                n_ef_din += 1
    tabela_nomes = []
    if padroes and fmap:
        vistos = {}
        for orig, novo in fmap.items():
            if any(orig.startswith(pa) and orig.endswith(su) for pa, su in padroes):
                for dobra in (True, False):
                    h = (dobra, sstrhash.stringhash_reforged(orig, dobra))
                    if h in vistos:
                        raise SystemExit('ERRO: StringHash do Reforged repetido entre %s e %s (use --manter)'
                                         % (vistos[h], orig))
                    vistos[h] = orig
                tabela_nomes.append((orig, novo))
    print('ExecuteFunc: %d literal(is) renomeado(s), %d montado(s) em tempo de execucao (padroes %s); '
          'tabela de nomes: %d' % (n_ef_lit, n_ef_din, sorted(padroes), len(tabela_nomes)))

    idx_str, idx_raw = {}, {}
    ocorr_str = ocorr_raw = 0
    li_decl_global = set(g['li'] for g in globais)
    for li, lin in enumerate(linhas):
        if li in li_decl_global:
            continue
        for ti in lin:
            if ti in congelado or ti in apagar:
                continue
            k = kinds[ti]
            if k == 'str' and faz_strings:
                s = subst.get(ti, texts[ti])
                if s == '""':
                    continue
                c = conteudo(s)
                if c not in idx_str:
                    idx_str[c] = None
                ocorr_str += 1
            elif k == 'raw' and faz_ids:
                c = conteudo(texts[ti])
                if c not in idx_raw:
                    idx_raw[c] = None
                ocorr_raw += 1
    for n, ti in convertidas.items():
        c = conteudo(texts[ti])
        if kinds[ti] == 'str':
            idx_str.setdefault(c, None)
        else:
            idx_raw.setdefault(c, None)
    for orig, _ in tabela_nomes:
        idx_str.setdefault(orig, None)
    lista_s = list(idx_str)
    rng.shuffle(lista_s)
    for k, c in enumerate(lista_s):
        idx_str[c] = k
    lista_r = list(idx_raw)
    rng.shuffle(lista_r)
    for k, c in enumerate(lista_r):
        idx_raw[c] = k
    if len(lista_r) > TETO_VETOR:
        raise SystemExit('ERRO: %d rawcodes distintos passam do teto de um vetor' % len(lista_r))

    novo = lambda: ger.novo(10, 16)
    n_vet_s = max(1, (len(lista_s) + TETO_VETOR - 1) // TETO_VETOR)
    V_S = [novo() for _ in range(n_vet_s)]
    V_I, V_T, F_D, F_R, F_INI, F_NOME = novo(), novo(), novo(), novo(), novo(), novo()
    H_ALF, H_NOME = novo(), novo()

    def ref_s(c):
        k = idx_str[c]
        return '%s[%d]' % (V_S[k // TETO_VETOR], k % TETO_VETOR)

    def ref_r(c):
        return '%s[%d]' % (V_I, idx_raw[c])

    unid = dict((c, pecas(c, rx_peca)) for c in lista_s)
    todas = {}
    for us in unid.values():
        for x in us:
            todas[x] = None
    pares = collections.Counter()
    if rx_peca is PECA:
        for us in unid.values():
            for par in zip(us, us[1:]):
                pares[par] += 1
    vaga = MODULO - 2 - len(todas)
    escolhidos = set(k for k, n in pares.most_common(max(0, vaga)) if n >= 3)
    pecas_de = {}
    for c, us in unid.items():
        ps = []
        i = 0
        while i < len(us):
            if i + 1 < len(us) and (us[i], us[i + 1]) in escolhidos:
                ps.append(us[i] + us[i + 1])
                i += 2
            else:
                ps.append(us[i])
                i += 1
        pecas_de[c] = ps
        for x in ps:
            todas[x] = None
    todas[''] = None
    tabela = list(todas)
    rng.shuffle(tabela)
    if len(tabela) >= MODULO:
        raise SystemExit('ERRO: %d pecas distintas passam do modulo %d' % (len(tabela), MODULO))
    if len(tabela) > 32000:
        raise SystemExit('ERRO: %d pecas distintas passam do teto de um vetor' % len(tabela))
    pos = dict((x, i) for i, x in enumerate(tabela))
    passo = rng.randint(1000, MODULO - 1000)
    n_pecas = 0

    def cifra(c):
        nonlocal n_pecas
        ps = pecas_de[c]
        n_pecas += len(ps)
        partes = []
        for a in range(0, len(ps), SEG):
            seg = ps[a:a + SEG]
            if len(seg) % 2:
                seg = seg + ['']
            x = rng.randrange(MODULO)
            x0 = x
            dig = []
            for peca in seg:
                dig.append('%0*d' % (LARG, (pos[peca] + x) % MODULO))
                x = (x + passo) % MODULO
            partes.append('%s(%d,"%s")' % (F_D, x0, ''.join(dig)))
        return '+'.join(partes)

    alf = list(ALFABETO)
    rng.shuffle(alf)
    hs = [sstrhash.sstrhash2(ch) for ch in alf]
    if len(set(hs)) != 36:
        raise SystemExit('ERRO: StringHash repetido no alfabeto')
    a1, b1 = rng.randint(1000, 49999), rng.randint(0, 65535)
    a2, b2 = rng.randint(1000, 49999), rng.randint(0, 65535)

    def rawval(c):
        if not c:
            return 0
        v = 0
        for ch in c.encode('latin-1'):
            v = v * 256 + ch
        return v & 0xFFFFFFFF

    def cifra_raw(c):
        k = idx_raw[c]
        v = rawval(c)
        hi, lo = (v >> 16) & 0xFFFF, v & 0xFFFF
        ka = (k * a1 + b1) % 65536
        kb = (k * a2 + b2) % 65536
        e = base36((hi + ka) % 65536, alf) + base36((lo + kb) % 65536, alf)
        corte = rng.randint(2, 6)
        return '%s(%d,"%s"+"%s")' % (F_R, k, e[:corte], e[corte:])

    fora_global = set()
    for g in globais:
        if g['nome'] in convertidas:
            fora_global.add(g['li'])

    def wordish(ch):
        return ch.isascii() and (ch.isalnum() or ch in '_$.')

    def opch(ch):
        return not wordish(ch) and ch not in '"\'()[],'

    def resolve(ti, lin, p, f):
        nome = texts[ti]
        if not faz_nomes or nome in PALAVRAS:
            return nome
        prev = texts[lin[p - 1]] if p > 0 else ''
        prox = texts[lin[p + 1]] if p + 1 < len(lin) else ''
        if prox == '(' or prev == 'function':
            return fmap.get(nome, nome)
        if f is not None and nome in f.novos:
            return f.novos[nome]
        if nome in gmap:
            return gmap[nome]
        return fmap.get(nome, nome)

    def emite(lin, f, pula_ini=None):
        out = []
        ult = ''
        ult_op = False
        for p, ti in enumerate(lin):
            if pula_ini is not None and p >= pula_ini:
                break
            if ti in apagar:
                continue
            k = kinds[ti]
            if k == 'id':
                t = resolve(ti, lin, p, f)
            elif k == 'str':
                s = subst.get(ti, texts[ti])
                if faz_strings and ti not in congelado and s != '""' and conteudo(s) in idx_str:
                    t = ref_s(conteudo(s))
                else:
                    t = s
            elif k == 'raw':
                if faz_ids and ti not in congelado and conteudo(texts[ti]) in idx_raw:
                    t = ref_r(conteudo(texts[ti]))
                else:
                    t = texts[ti]
            else:
                t = texts[ti]
            t = antes.get(ti, '') + t + depois.get(ti, '')
            t = t.replace('\x00NOMEFN', F_NOME)
            if out:
                c0 = t[0]
                if (wordish(ult) and (wordish(c0) or c0 in '"\'')) or (ult in '"\'' and wordish(c0)) or \
                   (ult_op and opch(c0) and espaco.get(ti)):
                    out.append(' ')
            out.append(t)
            ult = t[-1]
            ult_op = opch(ult)
        return ''.join(out)

    li_1a_funcao = min(f.li0 for f in funcoes.values())
    saida_l = []
    for li, lin in enumerate(linhas):
        if li == li_eg:
            for v in V_S:
                saida_l.append('string array %s' % v)
            saida_l.append('integer array %s' % V_I)
            saida_l.append('string array %s' % V_T)
            saida_l.append('hashtable %s=InitHashtable()' % H_ALF)
            if tabela_nomes:
                saida_l.append('hashtable %s=InitHashtable()' % H_NOME)
            saida_l.append('endglobals')
            continue
        if li == li_1a_funcao:
            saida_l.extend(pecas_novas(locals()))
        if not lin:
            continue
        f = dona[li]
        if li == li_primeira:
            saida_l.append('call %s()' % F_INI)
        if li in fora_global:
            g = next(x for x in globais if x['li'] == li)
            ini_pos = lin.index(g['ini'][0]) - 1
            txt = emite(lin, None, pula_ini=ini_pos)
            if txt.startswith('constant '):
                txt = txt[len('constant '):]
            saida_l.append(txt)
            continue
        saida_l.append(emite(lin, f))

    saida_txt = '\n'.join(saida_l) + '\n'
    open(saida, 'wb').write(saida_txt.encode('utf-8', 'surrogateescape'))
    print('strings: %d ocorrencia(s) de %d literal(is), %d pecas (%d distintas); rawcodes: %d ocorrencia(s) de %d'
          % (ocorr_str, len(lista_s), n_pecas, len(tabela), ocorr_raw, len(lista_r)))
    print('nomes: %d funcoes, %d globais, %d locais/parametros; globais convertidas: %d; congelados: %d tokens'
          % (len(fmap), len(gmap), sum(len(f.novos) for f in funcoes.values()), len(convertidas), len(congelado)))
    print('saida: %s (%d B, %d linhas) em %.1fs' % (saida, len(saida_txt.encode('utf-8', 'surrogateescape')),
                                                     len(saida_l), time.time() - t0))
    mapa = arg('mapa')
    if mapa:
        json.dump({'semente': semente, 'funcoes': fmap, 'globais': gmap,
                   'locais': dict((f.nome, f.novos) for f in funcoes.values() if f.novos),
                   'pecas': {'vetores_string': V_S, 'vetor_rawcode': V_I, 'tabela': V_T, 'decifra': F_D,
                             'decifra_rawcode': F_R, 'inicializa': F_INI, 'nome_dinamico': F_NOME}},
                  open(mapa, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
        print('mapa de simbolos: %s' % mapa)
    verif = arg('verificacao')
    if verif:
        escreve_verificacao(verif, lista_s, lista_r, rawval, ref_s, ref_r, tabela_nomes, fmap, padroes, F_NOME)
    pj = arg('pjass')
    if pj:
        return roda_pjass(pj, common, blizz, saida)
    return 0


def valor_jass(c):
    esc = {'\\': '\\', '"': '"', 'n': '\n', 'r': '\r', 't': '\t', 'b': '\b', 'f': '\f'}
    return re.sub(r'\\(.)', lambda m: esc.get(m.group(1), m.group(1)), c, flags=re.S)


def lua_lit(s):
    out = []
    for b in s.encode('utf-8', 'surrogateescape'):
        ch = chr(b)
        if 32 <= b < 127 and ch not in '"\\':
            out.append(ch)
        else:
            out.append('\\%03d' % b)
    return '"%s"' % ''.join(out)


def escreve_verificacao(caminho, lista_s, lista_r, rawval, ref_s, ref_r, tabela_nomes, fmap, padroes, F_NOME):
    linhas = ['__esp = { s = {}, r = {}, nomes = {}, fn = %s }' % lua_lit(F_NOME)]
    for c in lista_s:
        linhas.append('__esp.s[#__esp.s + 1] = { %s, %s }' % (lua_lit(ref_s(c)), lua_lit(valor_jass(c))))
    for c in lista_r:
        linhas.append(
            '__esp.r[#__esp.r + 1] = { %s, %d }'
            % (lua_lit(ref_r(c)), rawval(c) - (1 << 32) if rawval(c) >= (1 << 31) else rawval(c))
        )
    for orig, novo in fmap.items():
        if any(orig.startswith(pa) and orig.endswith(su) for pa, su in padroes):
            linhas.append('__esp.nomes[#__esp.nomes + 1] = { %s, %s }' % (lua_lit(orig), lua_lit(novo)))
    open(caminho, 'w', encoding='utf-8').write('\n'.join(linhas) + '\n')
    print('verificacao: %s (%d strings, %d rawcodes, %d nomes dinamicos)'
          % (caminho, len(lista_s), len(lista_r), len(tabela_nomes)))


def pecas_novas(L):
    F_D, F_R, F_INI, F_NOME = L['F_D'], L['F_R'], L['F_INI'], L['F_NOME']
    V_T, V_I, H_ALF, H_NOME = L['V_T'], L['V_I'], L['H_ALF'], L['H_NOME']
    ger, rng, bloco = L['ger'], L['rng'], L['bloco']
    passo, tabela, alf = L['passo'], L['tabela'], L['alf']
    a1, b1, a2, b2 = L['a1'], L['b1'], L['a2'], L['b2']
    lista_s, lista_r, cifra, cifra_raw = L['lista_s'], L['lista_r'], L['cifra'], L['cifra_raw']
    ref_s, ref_r = L['ref_s'], L['ref_r']
    tabela_nomes, convertidas, gmap, texts, kinds = (
        L['tabela_nomes'],
        L['convertidas'],
        L['gmap'],
        L['texts'],
        L['kinds'],
    )
    n = ger.novo
    out = []
    u = set()
    e, x, p, v, r, c, m, q, t, h = [n(3, 9, u) for _ in range(10)]
    uma = ['if %s<0 then' % v,
           'set %s=%s+%d' % (v, v, MODULO),
           'endif',
           'set %s=%s+%s[%s]' % (c, c, V_T, v),
           'set %s=%s+%d' % (x, x, passo),
           'if %s>=%d then' % (x, MODULO),
           'set %s=%s-%d' % (x, x, MODULO),
           'endif']
    out += ['function %s takes integer %s,string %s returns string' % (F_D, x, e),
            'local integer %s=StringLength(%s)' % (q, e),
            'local integer %s=0' % p,
            'local integer %s' % v,
            'local integer %s' % t,
            'local integer %s' % h,
            'local string %s=""' % r,
            'local string %s=""' % c,
            'local integer %s=0' % m,
            'loop',
            'exitwhen %s>=%s' % (p, q),
            'set %s=S2I(SubString(%s,%s,%s+%d))' % (t, e, p, p, 2 * LARG),
            'set %s=%s/%d' % (h, t, 10 ** LARG),
            'set %s=%s-%s' % (v, h, x)] + uma + [
            'set %s=%s-%s*%d-%s' % (v, t, h, 10 ** LARG, x)] + uma + [
            'set %s=%s+%d' % (p, p, 2 * LARG),
            'set %s=%s+1' % (m, m),
            'if %s==8 then' % m,
            'set %s=%s+%s' % (r, r, c),
            'set %s=""' % c,
            'set %s=0' % m,
            'endif',
            'endloop',
            'return %s+%s' % (r, c),
            'endfunction']
    u = set()
    k, e2, i, hi, lo, a, b = [n(3, 9, u) for _ in range(7)]
    out += ['function %s takes integer %s,string %s returns integer' % (F_R, k, e2),
            'local integer %s=0' % i,
            'local integer %s=0' % hi,
            'local integer %s=0' % lo,
            'local integer %s=%s*%d+%d' % (a, k, a1, b1),
            'local integer %s=%s*%d+%d' % (b, k, a2, b2),
            'set %s=%s-(%s/65536)*65536' % (a, a, a),
            'set %s=%s-(%s/65536)*65536' % (b, b, b),
            'loop',
            'exitwhen %s>=4' % i,
            'set %s=%s*36+LoadInteger(%s,0,StringHash(SubString(%s,%s,%s+1)))' % (hi, hi, H_ALF, e2, i, i),
            'set %s=%s*36+LoadInteger(%s,0,StringHash(SubString(%s,%s+4,%s+5)))' % (lo, lo, H_ALF, e2, i, i),
            'set %s=%s+1' % (i, i),
            'endloop',
            'set %s=%s-%s' % (hi, hi, a),
            'if %s<0 then' % hi,
            'set %s=%s+65536' % (hi, hi),
            'endif',
            'set %s=%s-%s' % (lo, lo, b),
            'if %s<0 then' % lo,
            'set %s=%s+65536' % (lo, lo),
            'endif',
            'if %s>=32768 then' % hi,
            'return (%s-65536)*65536+%s' % (hi, lo),
            'endif',
            'return %s*65536+%s' % (hi, lo),
            'endfunction']
    if tabela_nomes:
        u = set()
        s, h = n(3, 9, u), n(3, 9, u)
        out += ['function %s takes string %s returns string' % (F_NOME, s),
                'local integer %s=StringHash(%s)' % (h, s),
                'if HaveSavedString(%s,%s,1) then' % (H_NOME, h),
                'if LoadStr(%s,%s,1)==%s then' % (H_NOME, h, s),
                'return LoadStr(%s,%s,0)' % (H_NOME, h),
                'endif',
                'endif',
                'return %s' % s,
                'endfunction']
    blocos = []

    def novo_bloco(linhas_):
        nome = n(10, 16)
        blocos.append(nome)
        out.append('function %s takes nothing returns nothing' % nome)
        out.extend(linhas_)
        out.append('endfunction')

    lt = []
    for idx, peca in enumerate(tabela):
        lt.append('set %s[%d]="%s"' % (V_T, idx, peca))
        if len(lt) >= 4000:
            novo_bloco(lt)
            lt = []
    if lt:
        novo_bloco(lt)
    la = ['call SaveInteger(%s,0,StringHash("%s"),%d)' % (H_ALF, ch, alf.index(ch)) for ch in alf]
    lr = list(la)
    for c in lista_r:
        lr.append('set %s=%s' % (ref_r(c), cifra_raw(c)))
        if len(lr) >= 800:
            novo_bloco(lr)
            lr = []
    if lr:
        novo_bloco(lr)
    ls = []
    custo = 0
    for c in lista_s:
        ls.append('set %s=%s' % (ref_s(c), cifra(c)))
        custo += len(L['pecas_de'][c]) + 4
        if custo >= bloco:
            novo_bloco(ls)
            ls = []
            custo = 0
    if ls:
        novo_bloco(ls)
    ln = []
    for orig, nv in tabela_nomes:
        ln.append('call SaveStr(%s,StringHash(%s),0,"%s")' % (H_NOME, ref_s(orig), nv))
        ln.append('call SaveStr(%s,StringHash(%s),1,%s)' % (H_NOME, ref_s(orig), ref_s(orig)))
        if len(ln) >= 3000:
            novo_bloco(ln)
            ln = []
    if ln:
        novo_bloco(ln)
    lg = []
    for nome, ti in convertidas.items():
        alvo = gmap.get(nome, nome)
        c = texts[ti][1:-1]
        lg.append('set %s=%s' % (alvo, ref_s(c) if kinds[ti] == 'str' else ref_r(c)))
    if lg:
        novo_bloco(lg)
    out.append('function %s takes nothing returns nothing' % F_INI)
    for b_ in blocos:
        out.append('call ExecuteFunc("%s")' % b_)
    out.append('endfunction')
    return out


def roda_pjass(pj, common, blizz, saida):
    tmp = saida + '.pjass_lf.j'
    t = open(saida, 'rb').read().replace(b'\r\n', b'\n').replace(b'\r', b'\n')
    open(tmp, 'wb').write(t)
    r = subprocess.run([pj, common, blizz, tmp], capture_output=True, text=True, encoding='utf-8', errors='replace')
    os.remove(tmp)
    txt = (r.stdout or '') + (r.stderr or '')
    linhas = [l for l in txt.splitlines() if l.strip()]
    for l in linhas[-15:]:
        print('  pjass: ' + l)
    ruim = r.returncode != 0 or any(('error' in l.lower() or 'warning' in l.lower()) and 'Parse successful' not in l
                                    for l in linhas)
    print('pjass: %s' % ('FALHA' if ruim else 'PASSA'))
    return 1 if ruim else 0


if __name__ == '__main__':
    sys.exit(main())
