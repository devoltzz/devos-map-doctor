# Injects a cheat pack into the map script, obfuscated, and puts the script back with mpqadd.
import io
import os
import re
import shutil
import sys
import tempfile



PACKS_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'cheatpacks'))
JASS = 'jass'
LUA = 'lua'
NO_WINDOW = 0x08000000
PACKS = (
    {'id': 'jjcp', 'file': 'JJCP_NewGen.j.txt', 'language': JASS, 'title': 'JJCP NewGen',
     'needs': 'classic and Reforged (no Blz native)',
     'options': (('activator', 'Activation string', 'wc3edit', 'text'),
                 ('arrow', 'Arrow activation', 'UUDDLR', 'text'),
                 ('name', 'Player name that activates it', 'nuzamacuxe', 'text')),
     'finds': {'activator': r'(?m)^string\s+activator\s*=\s*"([^"]*)"',
               'arrow': r'(?m)^string\s+arrowAct\s*=\s*"([^"]*)"',
               'name': r'Init_NameEvent\(\s*"([^"]*)"\s*\)'}},
    {'id': 'nzcp', 'file': 'NZCP.j.txt', 'language': JASS, 'title': 'NZCP',
     'needs': 'classic and Reforged (no Blz native)',
     'options': (('activator', 'Activation string', 'easymode', 'text'),
                 ('arrow', 'Arrow activation', 'UUDDLR', 'text'),
                 ('name', 'Player name that activates it', 'nuzamacuxe', 'text')),
     'finds': {'activator': r'StringHash\(\s*"Activator"\s*\)\s*,\s*"([^"]*)"',
               'arrow': r'StringHash\(\s*"ArrowActivator"\s*\)\s*,\s*"([^"]*)"',
               'name': r'NameEvent\(\s*"([^"]*)"\s*\)'}},
    {'id': 'dvcp', 'file': 'dvcp.j', 'language': JASS, 'title': "Devo's CP",
     'needs': 'Reforged only (18 Blz natives and the damage events)',
     'options': (('act', 'Activation string', 'devo', 'text'),
                 ('pfx', 'Command prefix', '-', 'text'),
                 ('arr', 'Arrow activation', 'UUDDLRLR', 'text'),
                 ('nm', 'Player name that activates it (empty: nobody)', '', 'text')),
     'finds': {'act': r'(?m)^\s*call DCP_CfgSet\(\s*"act"\s*,\s*"([^"]*)"\s*\)\s*$',
               'pfx': r'(?m)^\s*call DCP_CfgSet\(\s*"pfx"\s*,\s*"([^"]*)"\s*\)\s*$',
               'arr': r'(?m)^\s*call DCP_CfgSet\(\s*"arr"\s*,\s*"([^"]*)"\s*\)\s*$',
               'nm': r'(?m)^\s*call DCP_CfgSet\(\s*"nm"\s*,\s*"([^"]*)"\s*\)\s*$'},
     'inside': r'(?ms)^function DCP_CfgInit\b.*?^endfunction'},
    {'id': 'ozzycp', 'file': 'OzzyCP.lua.txt', 'language': LUA, 'title': 'OzzyCP',
     'needs': 'Reforged only (Blz key/sync natives)',
     'options': (('greet', 'Message when it is enabled', 'OzzyCP has been enabled', 'text'),
                 ('activator', 'Activation string', 'ozzy', 'text'),
                 ('arrow', 'Arrow activation', 'uuddlrlr', 'text'),
                 ('symbol', 'Command prefix', '-', 'text'),
                 ('key', 'Key activation (empty: off)', 'ozzy is godlike', 'text'),
                 ('objectid', 'Search objects by numeric id', 'false', 'bool'),
                 ('advanced', 'Advanced key input', 'false', 'bool')),
     'finds': {'greet': r'(?m)^local\s+l\s*=\s*"([^"]*)"', 'activator': r'(?m)^local\s+G\s*=\s*"([^"]*)"',
               'arrow': r'(?m)^local\s+T\s*=\s*"([^"]*)"', 'symbol': r"(?m)^local\s+Z\s*=\s*'([^']*)'",
               'key': r'(?m)^local\s+k\s*=\s*"([^"]*)"', 'objectid': r'(?m)^local\s+e\s*=\s*(true|false)',
               'advanced': r'(?m)^local\s+D\s*=\s*(true|false)'}},
)


def _mod():
    for m in list(sys.modules.values()):
        if m is not None and getattr(m, '__name__', '').rsplit('.', 1)[-1] in ('desprotege', 'unprotect'):
            return m
    raise RuntimeError('the engine module (desprotege/unprotect) is not loaded')


def _api(mod, *nomes):
    for n in nomes:
        f = getattr(mod, n, None)
        if f is not None:
            return f
    raise RuntimeError('%s has none of: %s' % (getattr(mod, '__name__', mod), ', '.join(nomes)))


def _abre(path):
    return _api(_mod(), '_abre', '_open')(path)


def _le(a, nome):
    return _api(_mod(), '_le', '_read')(a, nome)


def _erro(e):
    return _api(_mod(), '_erro', '_error')(e)


def _calado():
    return _api(_mod(), 'calado', 'quiet')()


def _confere(entrada, saida, excluir):
    return _api(_mod(), 'confere_conteudo', 'check_content')(entrada, saida, excluir)


def _adiciona(path, repl, apagar):
    import contextlib
    from doctor.mpq import mpqadd
    f = _api(mpqadd, 'adiciona', 'add_files')
    with contextlib.redirect_stdout(io.StringIO()):
        return f(path, repl, apagar)


def _pack(pack_id):
    for p in PACKS:
        if p['id'] == pack_id:
            return p
    raise ValueError('unknown cheat pack %r' % pack_id)


def _path(pack):
    p = os.path.join(PACKS_DIR, pack['file'])
    if not os.path.isfile(p):
        raise RuntimeError('the cheat pack file is missing: %s' % p)
    return p


def catalog():
    out = []
    for p in PACKS:
        out.append({'id': p['id'], 'title': p['title'], 'language': p['language'], 'file': p['file'],
                    'needs': p['needs'],
                    'options': [{'key': k, 'label': l, 'default': d, 'kind': t} for k, l, d, t in p['options']]})
    return out


def list_packs(mapa, progresso=None):
    from doctor.viewers import map_files
    s = map_files.script(mapa)
    lang = s.get('language')
    out = {'language': lang, 'script': s.get('name'), 'compiled': s.get('compiled'), 'size': s.get('size') or 0,
           'note': s.get('note') or '', 'error': s.get('error'), 'packs': []}
    if lang in (JASS, LUA):
        out['packs'] = [p for p in catalog() if p['language'] == lang]
    else:
        out['why'] = ('The map script is %s: a cheat pack needs a JASS or a Lua script the Doctor can read and write.'
                      % (('compiled by the KK platform' if lang in ('kkwe', 'j2b') else 'not readable')))
    return out


def _apply_options(pack, texto, opcoes):
    usados = {}
    ini, fim = 0, len(texto)
    if pack.get('inside'):
        m = re.search(pack['inside'], texto)
        if not m:
            raise RuntimeError('the %s option table was not found in %s' % (pack['id'], pack['file']))
        ini, fim = m.start(), m.end()
    trecho = texto[ini:fim]
    for p in pack['options']:
        key, _label, default, kind = p
        val = (opcoes or {}).get(key, default)
        if kind == 'bool':
            val = 'true' if str(val).lower() in ('1', 'true', 'sim', 'yes', 'on') else 'false'
        else:
            val = str(val if val is not None else default)
        rx = pack['finds'][key]
        novo, n = re.subn(rx, lambda m: m.group(0).replace(m.group(1), val, 1), trecho)
        if n != 1:
            raise RuntimeError('the %s option %r matched %d time(s) in %s' % (pack['id'], key, n, pack['file']))
        trecho = novo
        usados[key] = val
    return texto[:ini] + trecho + texto[fim:], usados


def _jass_parts(texto):
    linhas = texto.replace('\r\n', '\n').split('\n')
    ini = fim = None
    for i, l in enumerate(linhas):
        s = l.strip()
        if ini is None and (s == '// globals' or s.startswith('globals')):
            ini = i
        elif ini is not None and (s == '// endglobals' or s == 'endglobals'):
            fim = i
            break
    globais = '\n'.join(linhas[ini + 1:fim]) if ini is not None and fim is not None else ''
    corpo = linhas[fim + 1:] if fim is not None else linhas
    principal, funcoes = [], []
    for i, l in enumerate(corpo):
        if l.strip() == '// function main':
            principal = [x for x in corpo[i + 1:] if x.strip()]
            funcoes = corpo[:i]
            break
    if not principal:
        m = None
        for i, l in enumerate(corpo):
            if re.match(r'^\s*function\s+main\s+takes\s+nothing\s+returns\s+nothing\s*$', l):
                m = i
        if m is not None:
            j = next((k for k in range(m + 1, len(corpo)) if corpo[k].strip() == 'endfunction'), len(corpo))
            funcoes = corpo[:m] + corpo[j + 1:]
            principal = [x for x in corpo[m + 1:j] if x.strip()]
    return globais, '\n'.join(funcoes).strip('\n'), '\n'.join(principal).strip('\n')


def _declara(texto):
    nomes = set(re.findall(r'(?m)^\s*function\s+([A-Za-z_]\w*)\s+takes', texto))
    for m in re.finditer(r'(?ms)^\s*globals\b(.*?)^\s*endglobals\b', texto):
        for l in m.group(1).split('\n'):
            mm = re.match(r'\s*(?:constant\s+)?[A-Za-z_]\w*\s+(?:array\s+)?([A-Za-z_]\w*)\s*(?:=.*)?$', l.strip())
            if mm:
                nomes.add(mm.group(1))
    return nomes


def _motor():
    try:
        from doctor.script import ofusca_jass
        ref = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ref', '3.0'))
        return set(ofusca_jass.ids_do_motor([os.path.join(ref, 'common.j'), os.path.join(ref, 'blizzard.j')]))
    except Exception:
        return set()


def _descola(script, pack_texto):
    globais, funcoes, _principal = _jass_parts(pack_texto)
    do_pack = _declara('globals\n' + globais + '\nendglobals\n' + funcoes)
    ocupados = _declara(script) | _motor()
    colisao = [n for n in do_pack if n in ocupados]
    if not colisao:
        return pack_texto, []
    trocados = []
    for n in sorted(set(colisao), key=len, reverse=True):
        novo = n
        while novo in ocupados or novo in do_pack:
            novo = 'Cp_' + novo
        pack_texto = re.sub(r'\b%s\b' % re.escape(n), novo, pack_texto)
        ocupados.add(novo)
        trocados.append('%s -> %s' % (n, novo))
    return pack_texto, trocados


def _jass_merge(script, pack_texto):
    globais, funcoes, principal = _jass_parts(pack_texto)
    if not funcoes:
        raise RuntimeError('the cheat pack has no functions to inject')
    linhas = script.replace('\r\n', '\n').split('\n')
    fim = next((i for i, l in enumerate(linhas) if l.strip() == 'endglobals'), None)
    if fim is None:
        raise RuntimeError('the map script has no globals block (the obfuscator needs one)')
    if globais.strip():
        linhas = linhas[:fim] + globais.split('\n') + linhas[fim:]
    ini_main = None
    for i, l in enumerate(linhas):
        if re.match(r'^\s*function\s+main\s+takes\s+nothing\s+returns\s+nothing\s*$', l):
            ini_main = i
            break
    if ini_main is None:
        raise RuntimeError('the map script has no main function (the obfuscator needs one)')
    fim_main = next((k for k in range(ini_main + 1, len(linhas)) if linhas[k].strip() == 'endfunction'), None)
    if fim_main is None:
        raise RuntimeError('the map script has a main function without endfunction')
    if principal.strip():
        linhas = linhas[:fim_main] + principal.split('\n') + linhas[fim_main:]
    linhas = linhas[:ini_main] + ['', funcoes, ''] + linhas[ini_main:]
    return '\n'.join(linhas)


def _api(mod, *nomes):
    for n in nomes:
        f = getattr(mod, n, None)
        if f is not None:
            return f
    raise RuntimeError('%s has none of: %s' % (getattr(mod, '__name__', mod), ', '.join(nomes)))


def _registro_texto(reg):
    for nome in ('texto', 'body_text', 'text'):
        f = getattr(reg, nome, None)
        if callable(f):
            return f()
    return ''


def _ofusca_jass(entrada, saida, progresso=None):
    from doctor.script import ofusca_jass
    ref = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ref', '3.0'))
    common = os.path.join(ref, 'common.j')
    blizz = os.path.join(ref, 'blizzard.j')
    if not (os.path.isfile(common) and os.path.isfile(blizz)):
        raise RuntimeError('the game scripts are missing: %s' % ref)
    args = ['ofusca_jass.py', '--j=' + entrada, '--' + 'sai' + 'da=' + saida, '--output=' + saida,
            '--common=' + common, '--blizzard=' + blizz]
    velho = list(sys.argv)
    sys.argv = args
    reg = None
    try:
        with _calado() as reg:
            try:
                ofusca_jass.main()
            except SystemExit as e:
                if e.code:
                    raise RuntimeError('the obfuscator stopped (exit %s); its own report is in the job log' % e.code)
    finally:
        sys.argv = velho
    return {'lines': (_registro_texto(reg).splitlines() if reg is not None else [])}


def _pjass_exe():
    aqui = os.path.dirname(os.path.abspath(__file__))
    p = os.environ.get('PJASS')
    if p and os.path.isfile(p):
        return p
    try:
        kk = os.path.normpath(os.path.join(aqui, '..', 'kk'))
        from doctor.script import pjass as _P
        exe = _P.exe()
        if exe and os.path.isfile(exe):
            return exe
    except Exception:
        pass
    for p in (os.path.join(aqui, 'pjass.exe'), os.path.normpath(os.path.join(aqui, '..', 'script', 'pjass.exe')),
              os.path.normpath(os.path.join(aqui, '..', 'kk', 'pjass.exe'))):
        if os.path.isfile(p):
            return p
    return None


def _pjass_confere(script, mapa=None):
    tmp = tempfile.mkdtemp(prefix='cheatpack_pjass_')
    try:
        alvo = os.path.join(tmp, 'script.j')
        with open(alvo, 'w', encoding='utf-8', newline='\n') as f:
            f.write(script.replace('\r\n', '\n'))
        exe = _pjass_exe()
        if not exe:
            from doctor.script import jass_ast
            ok, det = jass_ast.check_text(script)
            return ok, det or 'jass_ast', False
        ref = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ref', '3.0'))
        comuns = _scripts_do_mapa(mapa, tmp) or [os.path.join(ref, 'common.j'), os.path.join(ref, 'blizzard.j')]
        import subprocess
        r = subprocess.run([exe] + comuns + [alvo], cwd=tmp, capture_output=True, text=True, errors='replace',
                           creationflags=NO_WINDOW)
        saida = (r.stdout or '') + (r.stderr or '')
        if r.returncode == 0 and 'error' not in saida.lower():
            return True, 'pjass: %s' % (saida.strip().splitlines()[-1] if saida.strip() else 'ok'), False
        ruins = [x for x in saida.splitlines() if x.strip() and 'Parse successful' not in x]
        sintaxe = [x for x in ruins if re.search(r'syntax error|expected|unexpected|invalid|unclosed|token',
                                                 x, re.I)]
        detalhe = ' | '.join(ruins)[:400]
        if sintaxe or not ruins:
            return False, 'pjass: %s' % detalhe, False
        return True, 'pjass: %s' % detalhe, True
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _scripts_do_mapa(mapa, tmp):
    if not mapa:
        return None
    try:
        a = _abre(mapa)
    except BaseException:
        return None
    achados = []
    for nome in ('common.j', 'Common.j', 'scripts\\common.j', 'Blizzard.j', 'blizzard.j',
                 'scripts\\Blizzard.j', 'scripts\\blizzard.j'):
        dados = _le(a, nome)
        if dados:
            destino = os.path.join(tmp, 'mapa_' + os.path.basename(nome).lower())
            with open(destino, 'wb') as f:
                f.write(dados)
            achados.append((os.path.basename(nome).lower(), destino))
    if len(achados) < 2:
        return None
    achados.sort(key=lambda x: 0 if x[0].startswith('common') else 1)
    return [p for _n, p in achados[:2]]


def _lua_obfusca(texto):
    from doctor.script import lua_ast
    antes = lua_ast.canonical(texto)
    kinds, texts, _lines, offs, comments, ctok = lua_ast._lex(texto)[:6]
    por_tok = {}
    for c, k in zip(comments, ctok):
        por_tok.setdefault(k, []).append(c.text)
    partes = []
    pos = 0
    for i, (k, s, off) in enumerate(zip(kinds, texts, offs)):
        if k == 'EOF':
            break
        gap = texto[pos:off]
        for t in por_tok.get(i, ()):
            gap = gap.replace(t, '', 1)
        partes.append(gap + s)
        pos = off + len(s)
    saida = ''.join(partes) + texto[pos:]
    for c in comments:
        saida = saida.replace(c.text, '', 1)
    if lua_ast.canonical(lua_ast.parse(saida)) != antes:
        raise RuntimeError('the Lua obfuscation changed the code, not only the comments')
    return saida


def _lua_confere(texto):
    from doctor.script import lua_ast
    try:
        lua_ast.parse(texto)
    except Exception as e:
        return False, 'lua_ast: %s' % e
    return True, 'lua_ast: ok'


def inject(mapa, saida, pack_id, opcoes=None, progresso=None):
    p = progresso or (lambda *_a: None)
    pack = _pack(pack_id)
    out = {'lines': [], 'file': None, 'pack': pack['id'], 'options': {}, 'syntax': None, 'script': None}
    from doctor.viewers import map_files
    s = map_files.script(mapa)
    if s.get('language') != pack['language']:
        out['lines'] = [('ruim', 'The map script is %s: the %s pack is for %s maps.'
                         % (s.get('language') or 'unreadable', pack['title'], pack['language'].upper()))]
        return out
    nome = s.get('name')
    texto = s.get('text') or ''
    if not texto:
        out['lines'] = [('ruim', 'The map script is empty or unreadable.')]
        return out
    p('Reading the cheat pack')
    bruto = open(_path(pack), 'r', encoding='utf-8', newline='').read()
    try:
        return _injeta(p, pack, texto, nome, bruto, opcoes, mapa, saida, out)
    except BaseException as e:
        if isinstance(e, KeyboardInterrupt):
            raise
        if os.path.isfile(saida):
            os.remove(saida)
        out['file'] = None
        out['lines'] = [('ruim', 'The cheat pack was not injected: %s' % _erro(e))]
        return out


def _injeta(p, pack, texto, nome, bruto, opcoes, mapa, saida, out):
    texto_pack, usados = _apply_options(pack, bruto, opcoes)
    out['options'] = usados
    out['script'] = nome
    p('Injecting it into the script')
    if pack['language'] == JASS:
        texto_pack, trocados = _descola(texto, texto_pack)
        if trocados:
            out['renamed_names'] = trocados
        novo = _jass_merge(texto, texto_pack)
    else:
        novo = _lua_obfusca(texto_pack) + '\n' + texto.replace('\r\n', '\n')
    p('Obfuscating the script')
    tmp = tempfile.mkdtemp(prefix='cheatpack_')
    try:
        if pack['language'] == JASS:
            cru = os.path.join(tmp, 'merged.j')
            with open(cru, 'w', encoding='utf-8', newline='\n') as f:
                f.write(novo)
            pronto = os.path.join(tmp, 'release.j')
            r = _ofusca_jass(cru, pronto, p)
            novo = open(pronto, 'r', encoding='utf-8', newline='').read()
            out['renames'] = _resumo_ofusca(r['lines'])[:4]
        p('Checking the syntax')
        semantico = False
        if pack['language'] == JASS:
            ok, det, semantico = _pjass_confere(novo, mapa)
        else:
            ok, det = _lua_confere(novo)
        out['syntax'] = {'ok': bool(ok), 'detail': det, 'semantic': bool(semantico)}
        if not ok:
            out['lines'] = [('ruim', 'The injected script does not pass the syntax check: %s' % det)]
            return out
        p('Writing the map')
        vazio = _abre(mapa)
        antes = _le(vazio, nome) or b''
        del vazio
        shutil.copyfile(mapa, saida)
        from doctor.mpq import mpqadd
        with _calado():
            _adiciona(saida, [(nome, novo.encode('utf-8', 'surrogateescape'))], [])
        p('Checking the result')
        b = _abre(saida)
        lido = _le(b, nome)
        if lido != novo.encode('utf-8', 'surrogateescape'):
            raise RuntimeError('the script did not come back from the map as it was written')
        conf = _confere(mapa, saida, [nome])
        dif = conf.get('diferentes') or conf.get('different') or conf.get('differs') or []
        falta = conf.get('faltam') or conf.get('missing') or []
        if dif or falta:
            raise RuntimeError('the check: %d file(s) different, %d missing' % (len(dif), len(falta)))
        out['file'] = saida
        out['size_before'] = len(antes)
        out['size_after'] = len(lido)
        out['lines'] = _report(pack, usados, nome, antes, lido, out.get('renames'), det,
                               out.get('renamed_names'), semantico)
        return out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _resumo_ofusca(lines):
    out = []
    for l in lines or ():
        m = re.search(r'ExecuteFunc:\s*(\d+)\s*literal', l)
        if m:
            out.append('ExecuteFunc: %s literal name(s) renamed' % m.group(1))
            continue
        m = re.search(r'strings:\s*(\d+)\s*ocorrencia\(s\)\s*de\s*(\d+)', l)
        if m:
            out.append('strings: %s use(s) of %s literal(s) encrypted' % (m.group(1), m.group(2)))
            continue
        m = re.search(r'rawcodes:\s*(\d+)\s*ocorrencia\(s\)\s*de\s*(\d+)', l)
        if m:
            out.append('raw codes: %s use(s) of %s encrypted' % (m.group(1), m.group(2)))
    return out


def _report(pack, usados, nome, antes, depois, renames, det, trocados=None, semantico=False):
    out = [('titulo', '%s injected into %s' % (pack['title'], os.path.basename(nome))),
           ('ok', 'The script went back into the map with mpqadd: the file was not rebuilt (%s -> %s).'
            % (_kb(len(antes)), _kb(len(depois)))),
           ('ok', 'The syntax check passed (%s).' % det)]
    if semantico:
        out.append(('aviso', 'The map uses natives the game scripts do not declare (the platform client provides them '
                             'at run time): the check reports those and nothing else, and the pack adds no native. '
                             'Only a syntax error blocks the injection.'))
    if trocados:
        out.append(('info', '  name(s) the map already used, prefixed: %s' % ', '.join(trocados)))
    if renames:
        out += [('info', '  ' + x.strip()) for x in renames]
    out.append(('titulo2', 'Options'))
    for k, _l, _d, _t in pack['options']:
        out.append(('info', '  %s: %s' % (k, usados.get(k))))
    out.append(('info', '  Works on: %s' % pack['needs']))
    if pack['language'] == LUA:
        out.append(('info', '  The OzzyCP body is already an obfuscated build; the comments (and the header that '
                            'explains the options) were removed.'))
    if pack['language'] == JASS:
        out.append(('aviso', 'Test the map in game before sharing it: the pack runs from the map main, and the '
                             'obfuscator decrypts the strings in the first instruction of main.'))
    return out


def _kb(n):
    return ('%.1f kB' % (n / 1024.0)) if n < 1024 * 1024 else ('%.1f MB' % (n / 1048576.0))
