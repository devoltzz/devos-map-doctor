# Every 4-byte raw code a map brings (units, items, abilities...), the id kept as BYTES: the PG family renames the objects with ids that are not ASCII.
import os
import re

from doctor.mpq import mpqread
from doctor.data import objbin
from doctor.data import slk


ILEGIVEL = object()
VAZIO = b'\x00\x00\x00\x00'
OBJETOS = (('w3u', 'unit'), ('w3t', 'item'), ('w3a', 'ability'), ('w3b', 'destructable'), ('w3d', 'doodad'),
           ('w3h', 'buff'), ('w3q', 'upgrade'))
PREFIXOS = ('war3map.', 'war3mapSkin.')
TABELAS = ('Units\\UnitData.slk', 'Units\\UnitUI.slk', 'Units\\UnitBalance.slk', 'Units\\UnitAbilities.slk',
           'Units\\UnitWeapons.slk', 'Units\\ItemData.slk', 'Units\\AbilityData.slk', 'Units\\AbilityBuffData.slk',
           'Units\\UpgradeData.slk', 'Units\\DestructableData.slk', 'Doodads\\Doodads.slk',
           'Doodads\\DoodadsSkin.slk')
RACAS = ('Campaign', 'Human', 'Orc', 'Undead', 'NightElf', 'Neutral')
PERFIS = tuple('Units\\%s%s%s.txt' % (raca, tipo, parte) for raca in RACAS for tipo in ('Unit', 'Ability', 'Upgrade')
               for parte in ('Func', 'Strings')) + (
    'Units\\UnitSkin.txt', 'Units\\ItemSkin.txt', 'Units\\AbilitySkin.txt', 'Units\\UpgradeSkin.txt',
    'Units\\DestructableSkin.txt', 'Units\\ItemFunc.txt', 'Units\\ItemStrings.txt', 'Units\\ItemAbilityFunc.txt',
    'Units\\ItemAbilityStrings.txt', 'Units\\CommonAbilityFunc.txt', 'Units\\CommonAbilityStrings.txt',
    'Units\\DestructableFunc.txt', 'Units\\DestructableStrings.txt', 'Units\\BuffFunc.txt', 'Units\\BuffStrings.txt',
    'Units\\UpgradeFunc.txt', 'Units\\UpgradeStrings.txt')
NAO_OBJETO = ('miscdata.txt', 'miscgame.txt', 'commandfunc.txt', 'commandstrings.txt')
CANONICOS = tuple('%s%s' % (prefixo, ext) for prefixo in PREFIXOS for ext, _kind in OBJETOS) + TABELAS + PERFIS
CANONICOS_BAIXO = set(nome.lower() for nome in CANONICOS)
RX_TABELA = re.compile(r'^(units|doodads)\\.+\.(slk|txt)$', re.I)
CHAVES_KIND = (
    ('abilitybuff', 'buff'),
    ('ability', 'ability'),
    ('destructable', 'destructable'),
    ('upgrade', 'upgrade'),
    ('buff', 'buff'),
    ('item', 'item'),
    ('unit', 'unit'),
    ('doodad', 'doodad'),
)
QUEBRA = (('\n', '\\x0a'), ('\r', '\\x0d'), ('\x0b', '\\x0b'), ('\x0c', '\\x0c'), ('\x1c', '\\x1c'), ('\x1d', '\\x1d'),
          ('\x1e', '\\x1e'), ('\u2028', '\\u2028'), ('\u2029', '\\u2029'))


def _nada(*_args):
    pass


def _texto(b):
    return b.decode('utf-8', 'surrogateescape')


def _bytes(s):
    return s.encode('utf-8', 'surrogateescape')


def _visivel(s):
    return ''.join(chr(b) if 0x20 <= b <= 0x7E else '\\x%02x' % b for b in _bytes(s))


def _nao_visivel(s):
    return any(b < 0x20 or b > 0x7E for b in _bytes(s))


def _linha(ident):
    for c, escape in QUEBRA:
        if c in ident:
            ident = ident.replace(c, escape)
    return ident


def _kind_do_nome(nome):
    baixo = os.path.basename(nome.replace('/', '\\')).lower()
    if baixo in NAO_OBJETO:
        return None
    for chave, kind in CHAVES_KIND:
        if chave in baixo:
            return kind
    return None


def _le(a, nome):
    try:
        if a.find(nome) is None:
            return None
    except Exception:
        return None
    try:
        return a.read(nome)
    except Exception:
        return ILEGIVEL


def nomes_do_mapa(a):
    por = {}
    dados = _le(a, '(listfile)')
    if isinstance(dados, bytes) and dados:
        for linha in _texto(dados).replace('\r\n', '\n').replace('\r', '\n').split('\n'):
            nome = linha.strip().replace('/', '\\')
            if nome:
                por.setdefault(nome.lower(), nome)
    for canonico in CANONICOS:
        if canonico.lower() in por:
            continue
        try:
            if a.find(canonico) is not None:
                por[canonico.lower()] = canonico
        except Exception:
            continue
    return por


def _ids_de_quatro(nomes):
    vistos, ids, fora = set(), [], 0
    for nome in nomes:
        b = _bytes(nome)
        if len(b) != 4 or b == VAZIO:
            fora += 1
        elif b not in vistos:
            vistos.add(b)
            ids.append(b)
    return ids, fora


def _ids_objeto(dados, nome):
    com_nivel = os.path.basename(nome).lower() in objbin.WITH_LEVELS
    _ver, tabelas, _fim = objbin.read_data(dados, com_nivel)
    vistos, ids, zeros = set(), [], 0
    for tabela in tabelas:
        for old, new, _mods in tabela:
            for s in (new, old):
                b = s.encode('latin-1')
                if len(b) != 4 or b == VAZIO:
                    zeros += 1
                elif b not in vistos:
                    vistos.add(b)
                    ids.append(b)
    return ids, zeros


def _ids_tabela(dados, nome):
    if nome.lower().endswith('.slk'):
        _header, linhas = slk.parse_slk_bytes(dados)
        return _ids_de_quatro(list(linhas))
    return _ids_de_quatro(list(slk.parse_ini_bytes(dados)))


def extract(mapa, progresso=None):
    p = progresso or _nada
    r = {'kinds': [], 'total': 0, 'text': '', 'duplicates': [], 'note': '', 'error': None}
    p('read_map')
    try:
        a = mpqread.Archive(mapa)
    except (Exception, SystemExit) as e:
        r['error'] = 'cannot read the map: %s' % (str(e).strip() or type(e).__name__)
        return r
    por = nomes_do_mapa(a)
    fontes = []
    p('objects')
    for prefixo in PREFIXOS:
        for ext, kind in OBJETOS:
            nome = por.get((prefixo + ext).lower())
            if nome:
                fontes.append((nome, kind, True))
    p('tables')
    for canonico in TABELAS + PERFIS:
        nome = por.get(canonico.lower())
        if nome:
            fontes.append((nome, _kind_do_nome(nome), False))
    ignoradas = []
    for baixo in sorted(por):
        nome = por[baixo]
        if baixo in CANONICOS_BAIXO or not RX_TABELA.match(nome):
            continue
        kind = _kind_do_nome(nome)
        if kind:
            fontes.append((nome, kind, False))
        else:
            ignoradas.append(nome)
    kinds, ilegiveis = [], []
    ordem, kind_do_id, fontes_do_id = [], {}, {}
    zeros = fora4 = 0
    for nome, kind, classe_objeto in fontes:
        dados = _le(a, nome)
        if dados is ILEGIVEL:
            ilegiveis.append(nome)
            continue
        if not dados:
            continue
        try:
            ids, descartados = _ids_objeto(dados, nome) if classe_objeto else _ids_tabela(dados, nome)
        except Exception as e:
            ilegiveis.append('%s (%s)' % (nome, str(e)[:60]))
            continue
        if classe_objeto:
            zeros += descartados
        else:
            fora4 += descartados
        if not ids:
            continue
        texto_ids = [_texto(b) for b in ids]
        kinds.append({'kind': kind, 'source': nome, 'ids': texto_ids, 'count': len(texto_ids),
                      'ansii': sum(1 for b in ids if _nao_visivel(_texto(b)))})
        for ident in texto_ids:
            if ident in kind_do_id:
                fontes_do_id[ident].append(nome)
            else:
                kind_do_id[ident] = kind
                ordem.append(ident)
                fontes_do_id[ident] = [nome]
    r['kinds'] = kinds
    r['duplicates'] = [{'id': ident, 'kind': kind_do_id[ident], 'sources': fontes_do_id[ident]}
                       for ident in ordem if len(fontes_do_id[ident]) > 1]
    r['text'] = ''.join('%s\t%s\n' % (kind_do_id[ident], _linha(ident)) for ident in ordem)
    r['total'] = len(ordem)
    quebra = sum(1 for ident in ordem if any(c in ident for c, _e in QUEBRA))
    partes = [
        'Read only from the map itself: the object files (war3map.w3u/w3t/w3a/w3b/w3d/w3h/w3q and the war3mapSkin '
        'twins) and the Units\\*/Doodads\\* .slk/.txt tables the map carries. The tables of the installed game are not '
        'read, so an id that exists only in the game is not listed.',
        'Rawcodes the script builds at run time (a JASS/Lua \'xxxx\' literal, the sum of two rawcodes, a number) are '
        'not read: this is the bytes of the map files, not the script.',
        'A table row counts as an id only when its name is exactly 4 bytes; the zero-filled id slot is not an id.',
        '\'ansii\' counts the ids of a source with a byte outside printable ASCII (0x20..0x7E): the PG family ships '
        'ids of control bytes and every one of them is kept byte for byte (the text is utf-8/surrogateescape, so '
        'ident.encode(\'utf-8\', \'surrogateescape\') is the id of the file).',
        'An id in more than one source is listed once, in the first source that has it, and every source of it is in '
        'duplicates.',
        'The kind of a Units\\*.txt profile comes from the file name: Units\\CommonAbilityStrings.txt mixes ability '
        'and buff ids under the ability kind, and Units\\AbilityBuffData.slk is the table that declares the buffs.',
    ]
    if zeros:
        partes.append('%d id slot(s) were zero-filled.' % zeros)
    if fora4:
        partes.append('%d row(s) of a table were not a 4-byte name and stayed out.' % fora4)
    if ignoradas:
        partes.append('Not an object table, stayed out: %s.' % ', '.join(_visivel(n) for n in ignoradas))
    if ilegiveis:
        partes.append('Could not be read: %s.' % ', '.join(_visivel(n) for n in ilegiveis))
    if quebra:
        partes.append(
            '%d id(s) carry a byte Python reads as a line break and are written as \\xNN in text, so one line '
            'holds one id; ids and the json keep the byte as it is.' % quebra
        )
    r['note'] = ' '.join(partes)
    return r


def filtra(r, kinds):
    novo = dict(r)
    novo['kinds'] = [k for k in r['kinds'] if k['kind'] in kinds]
    ordem, visto = [], set()
    for k in novo['kinds']:
        for ident in k['ids']:
            if ident not in visto:
                visto.add(ident)
                ordem.append((k['kind'], ident))
    novo['text'] = ''.join('%s\t%s\n' % (kind, _linha(ident)) for kind, ident in ordem)
    novo['total'] = len(ordem)
    novo['duplicates'] = [d for d in r['duplicates'] if d['id'] in visto]
    novo['note'] = 'Filtered to the kinds: %s. %s' % (', '.join(sorted(kinds)), r['note'])
    return novo


def ids_unicos(r):
    ordem, visto = [], set()
    for k in r['kinds']:
        for ident in k['ids']:
            if ident not in visto:
                visto.add(ident)
                ordem.append(ident)
    return ordem


def relatorio(r, caminho):
    print('%s: %d source(s), %d unique id(s)' % (os.path.basename(caminho), len(r['kinds']), r['total']))
    largura = max([len(_visivel(k['source'])) for k in r['kinds']] + [6])
    for k in r['kinds']:
        print('  %-13s %-*s %6d id(s) %6d not plain ASCII'
              % (k['kind'], largura, _visivel(k['source']), k['count'], k['ansii']))
    fora = [ident for ident in ids_unicos(r) if _nao_visivel(ident)]
    print('ids with a byte outside printable ASCII: %d' % len(fora))
    if fora:
        print('examples (escaped): %s' % ', '.join(_visivel(ident) for ident in fora[:8]))
    print('ids in more than one source: %d' % len(r['duplicates']))
    print('note: %s' % r['note'])
