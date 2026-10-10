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
NO_WINDOW = 0x08000000 if os.name == 'nt' else 0
PACK_FILE = {JASS: 'pack.j', LUA: 'pack.lua'}
_PACKS = None


def _mod():
    for m in list(sys.modules.values()):
        if m is not None and getattr(m, '__name__', '').rsplit('.', 1)[-1] in ('desprotege', 'unprotect'):
            return m
    raise RuntimeError('the engine module (desprotege/unprotect) is not loaded')


def _api(mod, *names):
    for n in names:
        f = getattr(mod, n, None)
        if f is not None:
            return f
    raise RuntimeError('%s has none of: %s' % (getattr(mod, '__name__', mod), ', '.join(names)))


def _open_map(path):
    return _api(_mod(), '_abre', '_open')(path)


def _read_file(a, name):
    return _api(_mod(), '_le', '_read')(a, name)


def _error_text(e):
    return _api(_mod(), '_erro', '_error')(e)


def _calado():
    return _api(_mod(), 'calado', 'quiet')()


def _check_map(source, out_path, excluir):
    return _api(_mod(), 'confere_conteudo', 'check_content')(source, out_path, excluir)


def _adiciona(path, repl, apagar):
    import contextlib
    from doctor.mpq import mpqadd
    f = _api(mpqadd, 'adiciona', 'add_files')
    with contextlib.redirect_stdout(io.StringIO()):
        return f(path, repl, apagar)


def _parte(out_path):
    return _api(_mod(), '_parte', '_part')(out_path)


MARK_NAME = 'DV_CHEATPACK'
MARK_HEAD = 'cheatpack:'
KNOWN = (
    {
        'id': 'jjcp',
        'title': 'JJCP NewGen',
        'prefix': '-',
        'evidence': ('NewGenCommandHandler', 'Map cheated by'),
        'activator': (r'(?m)^string\s+activator\s*=\s*"([^"]*)"',),
    },
    {
        'id': 'nzcp',
        'title': 'NZCP',
        'prefix': '-',
        'evidence': ('CheatPackCommands_Handler', 'NUZAMACUXE', 'CheatPack_Action'),
        'activator': (r'StringHash\(\s*"Activator"\s*\)\s*,\s*"([^"]*)"',),
    },
    {
        'id': 'ozzycp',
        'title': 'OzzyCP',
        'prefix': '-',
        'evidence': ('OzzyCP', '\\79\\122\\122\\121\\67\\80', 'showbinds'),
        'activator': (r'n\.WC\s*=\s*"([^"]*)"', r'(?m)^local\s+G\s*=\s*"([^"]*)"'),
    },
    {
        'id': 'jjcp_classic',
        'title': 'JJCP classic',
        'prefix': '',
        'evidence': ('JJ2197', 'SpicePirate', '-cheats'),
        'activator': (r'"(-cheats\s*)"',),
    },
    {
        'id': 'hke_cp',
        'title': 'Hke CP (arrow and name activator)',
        'prefix': '',
        'evidence': ('whitegun', 'hke_Z0z'),
        'activator': (r'"(whitegun)"',),
    },
    {
        'id': 'sabrac_cp',
        'title': "SabRaC's CP",
        'prefix': '',
        'evidence': ('SabRaC', 'sbrkw'),
        'activator': (r'"(SabRaC)"',),
    },
    {
        'id': 'sgguy_menu',
        'title': "SGGuy's Cheat Menu",
        'prefix': '',
        'evidence': ('SgGuy', 'sgguy_pass'),
        'activator': (r'"(IoI\s*)"',),
    },
    {
        'id': 'cheatscript',
        'title': 'Cheat Script v0.1 beta (Korean)',
        'prefix': '',
        'evidence': ('Cheat Script v0.1 beta', '치트 권한', '치트 사용자'),
        'activator': (r'TriggerRegisterPlayerChatEvent\([^,]+,[^,]+,\s*"(@[^"]*)"',),
        'shortest': True,
    },
)


def marca(pack, opcoes):
    key = pack.get('mark_option')
    if not key:
        return None
    ativador = str((opcoes or {}).get(key) or '')
    value = (MARK_HEAD + pack['id'] + ':' + ativador).replace('\\', '\\\\').replace('"', '\\"')
    return 'string %s = "%s" + "%s"' % (MARK_NAME, MARK_HEAD, value[len(MARK_HEAD):])


def detect(mapa, progresso=None):
    from doctor.viewers import map_files
    out = []
    try:
        s = map_files.script(mapa)
    except BaseException:
        return out
    text = s.get('text') or ''
    if not text:
        return out
    where = s.get('name') or '?'
    m = re.search(r'%s\s*=\s*"([^"]*)"(?:\s*\+\s*"([^"]*)")?' % MARK_NAME, text)
    if m:
        value = MARK_HEAD + (m.group(2) or '')
    else:
        m = re.search(r'(?m)^\s*--\s*%s\s+(\S+)' % MARK_NAME, text)
        if m:
            value = m.group(1)
    if m:
        parts = value.split(':', 2)
        prefixo = ''
        try:
            prefixo = (_packs().get(parts[1]) or {}).get('prefix') or ''
        except BaseException:
            prefixo = ''
        out.append({'id': 'devo', 'pack': parts[1] if len(parts) > 1 else '',
                    'title': 'Injected by the Doctor (%s)' % (parts[1] if len(parts) > 1 else '?'),
                    'activator': (prefixo + parts[2]) if len(parts) > 2 and parts[2] else '?',
                    'where': where, 'evidence': 'the Doctor\'s own marker (%s)' % value, 'confidence': 'high'})
    ja = set(x.get('pack') for x in out)
    for k in KNOWN:
        if k['id'] in ja:
            continue
        found = [e for e in k['evidence'] if e in text]
        if not found:
            continue
        ativador = '?'
        for rx in k['activator']:
            found_rx = re.findall(rx, text)
            if found_rx:
                if k.get('shortest'):
                    found_rx = sorted(found_rx, key=len)
                ativador = k['prefix'] + found_rx[0].strip()
                break
        out.append({'id': k['id'], 'title': k['title'], 'activator': ativador, 'where': where,
                    'evidence': ', '.join(found[:3]),
                    'confidence': 'high' if (len(found) > 1 or ativador != '?') else 'low'})
    return out


def _packs(recarrega=False):
    global _PACKS
    if _PACKS is None or recarrega:
        found = {}
        if not os.path.isdir(PACKS_DIR):
            raise RuntimeError('the cheat pack folder is missing: %s' % PACKS_DIR)
        for name in sorted(os.listdir(PACKS_DIR)):
            folder = os.path.join(PACKS_DIR, name)
            path = os.path.join(folder, 'pack.json')
            if not (os.path.isdir(folder) and os.path.isfile(path)):
                continue
            p = _read_json(path, name)
            if p['id'] in found:
                raise RuntimeError('two cheat pack folders answer to the id %r: %s' % (p['id'], folder))
            found[p['id']] = p
        if not found:
            raise RuntimeError('no cheat pack under %s (a pack is a folder with a `pack.json`)' % PACKS_DIR)
        _PACKS = found
    return _PACKS


def _read_json(path, folder):
    import json
    try:
        with io.open(path, encoding='utf-8') as f:
            d = json.load(f)
    except ValueError as e:
        raise RuntimeError('%s is not valid JSON: %s' % (path, e))
    if not isinstance(d, dict):
        raise RuntimeError('%s has to hold a JSON object' % path)
    missing_fields = [k for k in ('id', 'title', 'language', 'options', 'finds') if not d.get(k)]
    if missing_fields:
        raise RuntimeError('%s is missing the field(s): %s' % (path, ', '.join(missing_fields)))
    if not isinstance(d['options'], list):
        raise RuntimeError('%s: `options` has to be a list' % path)
    if not isinstance(d['finds'], dict):
        raise RuntimeError('%s: `finds` has to be an object (one regex per option)' % path)
    if d['id'] != folder:
        raise RuntimeError('%s says id %r, but its folder is named %r' % (path, d['id'], folder))
    if d['language'] not in PACK_FILE:
        raise RuntimeError('%s: the language has to be %s or %s, not %r' % (path, JASS, LUA, d['language']))
    arquivo = PACK_FILE[d['language']]
    if not os.path.isfile(os.path.join(PACKS_DIR, folder, arquivo)):
        raise RuntimeError('%s: the %s pack needs its %s' % (path, d['language'].upper(), arquivo))
    opcoes = []
    for o in d['options']:
        if not isinstance(o, dict) or [k for k in ('key', 'label', 'default', 'kind') if k not in o]:
            raise RuntimeError('%s: every option needs key, label, default and kind (%r)' % (path, o))
        if o['kind'] not in ('text', 'bool'):
            raise RuntimeError('%s: the kind of %r has to be text or bool, not %r' % (path, o['key'], o['kind']))
        if 'note' in o and not isinstance(o['note'], str):
            raise RuntimeError('%s: the note of %r has to be text' % (path, o['key']))
        opcoes.append((o['key'], o['label'], o['default'], o['kind']))
    notas = dict((o['key'], o['note']) for o in d['options'] if o.get('note'))
    keys = [o[0] for o in opcoes]
    if len(set(keys)) != len(keys):
        raise RuntimeError('%s: two options with the same key (%s)' % (path, ', '.join(keys)))
    without_find = [k for k in keys if not d['finds'].get(k)]
    if without_find:
        raise RuntimeError('%s: no `finds` regex for the option(s): %s' % (path, ', '.join(without_find)))
    leftover = sorted(k for k in d['finds'] if k not in keys)
    if leftover:
        raise RuntimeError('%s: `finds` names no option: %s' % (path, ', '.join(leftover)))
    for k in sorted(d['finds']):
        try:
            re.compile(d['finds'][k])
        except re.error as e:
            raise RuntimeError('%s: the regex of %r does not compile: %s' % (path, k, e))
    if d.get('inside'):
        try:
            re.compile(d['inside'])
        except re.error as e:
            raise RuntimeError('%s: the `inside` regex does not compile: %s' % (path, e))
    marca_opt = d.get('mark_option')
    if marca_opt and marca_opt not in keys:
        raise RuntimeError('%s: `mark_option` is %r, which is not one of the options' % (path, marca_opt))
    return {'id': d['id'], 'title': d['title'], 'language': d['language'], 'needs': d.get('needs') or '',
        'options': opcoes, 'notes': notas, 'finds': d['finds'], 'inside': d.get('inside'), 'mark_option': marca_opt,
        'prefix': d.get('prefix') or '', 'default': bool(d.get('default')), 'file': arquivo}


def _pack(pack_id):
    found = _packs()
    p = found.get(pack_id)
    if p is None:
        raise ValueError('unknown cheat pack %r (the archive has: %s)' % (pack_id, ', '.join(sorted(found))))
    return p


def _path(pack):
    p = os.path.join(PACKS_DIR, pack['id'], pack['file'])
    if not os.path.isfile(p):
        raise RuntimeError('the cheat pack file is missing: %s' % p)
    return p


def catalog():
    out = []
    found = _packs()
    for pid in sorted(found, key=lambda x: (not found[x].get('default'), x)):
        p = found[pid]
        out.append({'id': p['id'], 'title': p['title'], 'language': p['language'],
                    'file': '%s/%s' % (p['id'], p['file']), 'needs': p['needs'],
                    'default': bool(p.get('default')),
                    'options': [{'key': k, 'label': l, 'default': d, 'kind': t, 'note': p['notes'].get(k)}
                                for k, l, d, t in p['options']]})
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
    out['found'] = detect(mapa, progresso)
    return out


def _apply_options(pack, text, opcoes):
    usados = {}
    ini, fim = 0, len(text)
    if pack.get('inside'):
        m = re.search(pack['inside'], text)
        if not m:
            raise RuntimeError('the %s option table was not found in %s' % (pack['id'], pack['file']))
        ini, fim = m.start(), m.end()
    trecho = text[ini:fim]
    for p in pack['options']:
        key, _label, default, kind = p
        val = (opcoes or {}).get(key, default)
        if kind == 'bool':
            val = 'true' if str(val).lower() in ('1', 'true', 'sim', 'yes', 'on') else 'false'
        else:
            val = str(val if val is not None else default)
        rx = pack['finds'][key]

        def swap(m, val=val, key=key):
            if m.start(1) < 0:
                raise RuntimeError('the %s option %r has no value group in %s' % (pack['id'], key, pack['file']))
            g0 = m.group(0)
            return g0[:m.start(1) - m.start(0)] + val + g0[m.end(1) - m.start(0):]
        new_text, n = re.subn(rx, swap, trecho)
        if n != 1:
            raise RuntimeError('the %s option %r matched %d time(s) in %s' % (pack['id'], key, n, pack['file']))
        trecho = new_text
        usados[key] = val
    return text[:ini] + trecho + text[fim:], usados


def _jass_parts(text):
    lines = text.replace('\r\n', '\n').split('\n')
    ini = fim = None
    for i, l in enumerate(lines):
        s = l.strip()
        if ini is None and (s == '// globals' or s.startswith('globals')):
            ini = i
        elif ini is not None and (s == '// endglobals' or s == 'endglobals'):
            fim = i
            break
    globais = '\n'.join(lines[ini + 1:fim]) if ini is not None and fim is not None else ''
    body = lines[fim + 1:] if fim is not None else lines
    principal, funcoes = [], []
    for i, l in enumerate(body):
        if l.strip() == '// function main':
            principal = [x for x in body[i + 1:] if x.strip()]
            funcoes = body[:i]
            break
    if not principal:
        m = None
        for i, l in enumerate(body):
            if re.match(r'^\s*function\s+main\s+takes\s+nothing\s+returns\s+nothing\s*$', l):
                m = i
        if m is not None:
            j = next((k for k in range(m + 1, len(body)) if body[k].strip() == 'endfunction'), len(body))
            funcoes = body[:m] + body[j + 1:]
            principal = [x for x in body[m + 1:j] if x.strip()]
    return globais, '\n'.join(funcoes).strip('\n'), '\n'.join(principal).strip('\n')


def _declara(text):
    names = set(re.findall(r'(?m)^\s*function\s+([A-Za-z_]\w*)\s+takes', text))
    for m in re.finditer(r'(?ms)^\s*globals\b(.*?)^\s*endglobals\b', text):
        for l in m.group(1).split('\n'):
            mm = re.match(r'\s*(?:constant\s+)?[A-Za-z_]\w*\s+(?:array\s+)?([A-Za-z_]\w*)\s*(?:=.*)?$', l.strip())
            if mm:
                names.add(mm.group(1))
    return names


def _motor():
    try:
        from doctor.script import ofusca_jass
        ref = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ref', '3.0'))
        return set(
            _api(ofusca_jass, 'ids_do_motor', 'engine_ids')(
                [os.path.join(ref, 'common.j'), os.path.join(ref, 'blizzard.j')]
            )
        )
    except Exception:
        return set()


def _descola(script, pack_text):
    globais, funcoes, _principal = _jass_parts(pack_text)
    from_pack = _declara('globals\n' + globais + '\nendglobals\n' + funcoes)
    ocupados = _declara(script) | _motor()
    colisao = [n for n in from_pack if n in ocupados]
    if not colisao:
        return pack_text, []
    renamed = []
    for n in sorted(set(colisao), key=len, reverse=True):
        new_text = n
        while new_text in ocupados or new_text in from_pack:
            new_text = 'Cp_' + new_text
        pack_text = re.sub(r'\b%s\b' % re.escape(n), new_text, pack_text)
        ocupados.add(new_text)
        renamed.append('%s -> %s' % (n, new_text))
    return pack_text, renamed


def _jass_merge(script, pack_text, mark_line=None):
    globais, funcoes, principal = _jass_parts(pack_text)
    if not funcoes:
        raise RuntimeError('the cheat pack has no functions to inject')
    lines = script.replace('\r\n', '\n').split('\n')
    fim = next((i for i, l in enumerate(lines) if l.strip() == 'endglobals'), None)
    if fim is None:
        raise RuntimeError('the map script has no globals block (the obfuscator needs one)')
    if globais.strip():
        lines = lines[:fim] + globais.split('\n') + lines[fim:]
    if mark_line:
        lines = lines[:fim] + [mark_line] + lines[fim:]
    ini_main = None
    for i, l in enumerate(lines):
        if re.match(r'^\s*function\s+main\s+takes\s+nothing\s+returns\s+nothing\s*$', l):
            ini_main = i
            break
    if ini_main is None:
        raise RuntimeError('the map script has no main function (the obfuscator needs one)')
    fim_main = next((k for k in range(ini_main + 1, len(lines)) if lines[k].strip() == 'endfunction'), None)
    if fim_main is None:
        raise RuntimeError('the map script has a main function without endfunction')
    if principal.strip():
        lines = lines[:fim_main] + principal.split('\n') + lines[fim_main:]
    lines = lines[:ini_main] + ['', funcoes, ''] + lines[ini_main:]
    return '\n'.join(lines)


def _api(mod, *names):
    for n in names:
        f = getattr(mod, n, None)
        if f is not None:
            return f
    raise RuntimeError('%s has none of: %s' % (getattr(mod, '__name__', mod), ', '.join(names)))


def _text_record(reg):
    for name in ('texto', 'body_text', 'text'):
        f = getattr(reg, name, None)
        if callable(f):
            return f()
    return ''


def _obfuscate_jass(source, out_path, progresso=None):
    from doctor.script import ofusca_jass
    ref = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ref', '3.0'))
    common = os.path.join(ref, 'common.j')
    blizz = os.path.join(ref, 'blizzard.j')
    if not (os.path.isfile(common) and os.path.isfile(blizz)):
        raise RuntimeError('the game scripts are missing: %s' % ref)
    args = ['ofusca_jass.py', '--j=' + source, '--' + 'sai' + 'da=' + out_path, '--output=' + out_path,
            '--common=' + common, '--blizzard=' + blizz, '--manter=' + MARK_NAME, '--keep_names=' + MARK_NAME]
    old = list(sys.argv)
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
        sys.argv = old
    return {'lines': (_text_record(reg).splitlines() if reg is not None else [])}


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
    name = 'pjass' if sys.platform.startswith('linux') else 'pjass.exe'
    for p in (os.path.join(aqui, name), os.path.normpath(os.path.join(aqui, '..', 'script', name)),
              os.path.normpath(os.path.join(aqui, '..', 'kk', name))):
        if os.path.isfile(p):
            return p
    return None


def _pjass_erros(script, mapa=None):
    import collections
    ok, det, _s = _pjass_check(script, mapa, _cru=True)
    return collections.Counter(det) if isinstance(det, list) else collections.Counter()


def _sem_linha(x):
    return re.sub(r'^.*?:\d+:\s*', '', x.strip())


def _pjass_check(script, mapa=None, original=None, _cru=False, mesclado=None):
    tmp = tempfile.mkdtemp(prefix='cheatpack_pjass_')
    try:
        alvo = os.path.join(tmp, 'script.j')
        with open(alvo, 'w', encoding='utf-8', errors='surrogateescape', newline='\n') as f:
            f.write(script.replace('\r\n', '\n'))
        exe = _pjass_exe()
        if not exe:
            from doctor.script import jass_ast
            ok, det = jass_ast.check_text(script)
            return ok, det or 'jass_ast', False
        ref = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ref', '3.0'))
        comuns = _map_scripts(mapa, tmp) or [os.path.join(ref, 'common.j'), os.path.join(ref, 'blizzard.j')]
        import subprocess
        r = subprocess.run([exe] + comuns + [alvo], cwd=tmp, capture_output=True, text=True, errors='replace',
                           creationflags=NO_WINDOW)
        out_path = (r.stdout or '') + (r.stderr or '')
        if _cru:
            return r.returncode == 0, [_sem_linha(x) for x in out_path.splitlines()
                                       if x.strip() and 'Parse successful' not in x and re.search(r':\d+:', x)], False
        if r.returncode == 0 and 'error' not in out_path.lower():
            return True, 'pjass: %s' % (out_path.strip().splitlines()[-1] if out_path.strip() else 'ok'), False
        ruins = [x for x in out_path.splitlines() if x.strip() and 'Parse successful' not in x]
        if original is not None:
            ja = _pjass_erros(original, mapa)
            depois = _pjass_erros(mesclado if mesclado is not None else script, mapa)
            novos = depois - ja
            n_aqui = len([x for x in ruins if re.search(r':\d+:', x)])
            if sum(ja.values()) and not novos and n_aqui == sum(depois.values()):
                return True, 'pjass: %d complaint(s) of the map\'s own script, none new' % sum(ja.values()), 'own'
        from_map = [x for x in ruins if 'mapa_' in x]
        nosso = [x for x in ruins if x not in from_map]
        sintaxe = [
            x
            for x in nosso
            if re.search(
                r'syntax error|expected|unexpected|invalid|unclosed|token|already defined|allready defined|redefinition|redefined|type mismatch|cannot convert',
                x,
                re.I,
            )
        ]
        if sintaxe:
            return False, 'pjass: %s' % ' | '.join(sintaxe)[:400], False
        rest = nosso or from_map
        return True, 'pjass: %s' % (' | '.join(rest)[:400] if rest else 'ok'), bool(rest)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _map_scripts(mapa, tmp):
    ref = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ref', '3.0'))
    from_game = [os.path.join(ref, 'common.j'), os.path.join(ref, 'blizzard.j')]
    if not mapa:
        return from_game
    try:
        a = _open_map(mapa)
    except BaseException:
        return from_game
    out_path = []
    for i, candidatos in enumerate((('common.j', 'scripts\\common.j', 'Scripts\\common.j'),
                                    ('Blizzard.j', 'blizzard.j', 'scripts\\Blizzard.j', 'Scripts\\Blizzard.j'))):
        found_one = None
        for name in candidatos:
            dados = _read_file(a, name)
            if dados:
                found_one = os.path.join(tmp, 'mapa_' + os.path.basename(name).lower())
                with open(found_one, 'wb') as f:
                    f.write(dados)
                break
        out_path.append(found_one or from_game[i])
    return out_path


def _lua_obfusca(text):
    from doctor.script import lua_ast
    before = lua_ast.canonical(text)
    kinds, texts, _lines, offs, comments, ctok = lua_ast._lex(text)[:6]
    by_token = {}
    for c, k in zip(comments, ctok):
        by_token.setdefault(k, []).append(c.text)
    parts = []
    pos = 0
    for i, (k, s, off) in enumerate(zip(kinds, texts, offs)):
        if k == 'EOF':
            break
        gap = text[pos:off]
        for t in by_token.get(i, ()):
            gap = gap.replace(t, '', 1)
        parts.append(gap + s)
        pos = off + len(s)
    out_path = ''.join(parts) + text[pos:]
    for c in comments:
        out_path = out_path.replace(c.text, '', 1)
    if lua_ast.canonical(lua_ast.parse(out_path)) != before:
        raise RuntimeError('the Lua obfuscation changed the code, not only the comments')
    return out_path


def _lua_check(text):
    from doctor.script import lua_ast
    try:
        lua_ast.parse(text)
    except Exception as e:
        return False, 'lua_ast: %s' % e
    return True, 'lua_ast: ok'


def inject(mapa, out_path, pack_id, opcoes=None, progresso=None):
    p = progresso or (lambda *_a: None)
    pack = _pack(pack_id)
    out = {'lines': [], 'file': None, 'pack': pack['id'], 'options': {}, 'syntax': None, 'script': None}
    if os.path.normcase(os.path.abspath(mapa)) == os.path.normcase(os.path.abspath(out_path)):
        out['lines'] = [('bad', 'The output must be a new file: the map itself is never written.')]
        return out
    from doctor.viewers import map_files
    s = map_files.script(mapa)
    if s.get('language') != pack['language']:
        out['lines'] = [('bad', 'The map script is %s: the %s pack is for %s maps.'
                         % (s.get('language') or 'unreadable', pack['title'], pack['language'].upper()))]
        return out
    from doctor.mpq import mpqadd
    if _api(mpqadd, 'formato', 'format')(mapa) != 0:
        out['lines'] = [('bad', 'The cheat pack was not injected: %s' % (
            'The archive header is not a normal MPQ v1 header (a protected map): unprotect it first.'))]
        return out
    name = s.get('name')
    try:
        dados = (_read_file(_open_map(mapa), name) if name else None) or b''
    except BaseException as e:
        if isinstance(e, KeyboardInterrupt):
            raise
        dados = b''
    text = dados.decode('utf-8', 'surrogateescape').replace('\r\n', '\n').replace('\r', '\n')
    if not text:
        out['lines'] = [('bad', 'The map script is empty or unreadable.')]
        return out
    p('Reading the cheat pack')
    bruto = open(_path(pack), 'r', encoding='utf-8', newline='').read()
    try:
        return _injeta(p, pack, text, name, bruto, opcoes, mapa, out_path, out)
    except BaseException as e:
        if isinstance(e, KeyboardInterrupt):
            raise
        try:
            parte = _parte(out_path)
            if os.path.isfile(parte):
                os.remove(parte)
        except (OSError, RuntimeError):
            pass
        out['file'] = None
        out['lines'] = [('bad', 'The cheat pack was not injected: %s' % _error_text(e))]
        return out


def _injeta(p, pack, text, name, bruto, opcoes, mapa, out_path, out):
    pack_body, usados = _apply_options(pack, bruto, opcoes)
    out['options'] = usados
    out['script'] = name
    p('Injecting it into the script')
    mark_line = marca(pack, usados)
    if pack['language'] == JASS and re.search(r'(?m)^\s*(?:constant\s+)?\w+\s+%s\b' % MARK_NAME, text):
        out['file'] = None
        out['lines'] = [('bad', 'The cheat pack was not injected: this map already carries the Doctor\'s mark (%s), '
                                 'and a second pack would declare it twice.' % MARK_NAME)]
        return out
    if pack['language'] == JASS:
        pack_body, renamed = _descola(text, pack_body)
        if renamed:
            out['renamed_names'] = renamed
        new_text = _jass_merge(text, pack_body, mark_line)
    else:
        new_text = ('-- %s %s%s\n' % (MARK_NAME, MARK_HEAD, pack['id'] + ':' + (usados.get('activator') or ''))) \
            + _lua_obfusca(pack_body) + '\n' + text.replace('\r\n', '\n')
    mesclado = new_text
    p('Obfuscating the script')
    tmp = tempfile.mkdtemp(prefix='cheatpack_')
    try:
        if pack['language'] == JASS:
            cru = os.path.join(tmp, 'merged.j')
            with open(cru, 'w', encoding='utf-8', errors='surrogateescape', newline='\n') as f:
                f.write(new_text)
            pronto = os.path.join(tmp, 'release.j')
            r = _obfuscate_jass(cru, pronto, p)
            new_text = open(pronto, 'r', encoding='utf-8', errors='surrogateescape', newline='').read()
            out['renames'] = _obfuscation_summary(r['lines'])[:4]
        p('Checking the syntax')
        semantico = False
        if pack['language'] == JASS:
            ok, det, semantico = _pjass_check(new_text, mapa, original=text, mesclado=mesclado)
        else:
            ok, det = _lua_check(new_text)
        out['syntax'] = {'ok': bool(ok), 'detail': det, 'semantic': bool(semantico)}
        if not ok:
            out['lines'] = [('bad', 'The injected script does not pass the syntax check: %s' % det)]
            return out
        p('Writing the map')
        empty = _open_map(mapa)
        before = _read_file(empty, name) or b''
        del empty
        parte = _parte(out_path)
        shutil.copyfile(mapa, parte)
        from doctor.mpq import mpqadd
        with _calado():
            _adiciona(parte, [(name, new_text.encode('utf-8', 'surrogateescape'))], [])
        p('Checking the result')
        b = _open_map(parte)
        lido = _read_file(b, name)
        if lido != new_text.encode('utf-8', 'surrogateescape'):
            raise RuntimeError('the script did not come back from the map as it was written')
        conf = _check_map(mapa, parte, [name])
        dif = conf.get('diferentes') or conf.get('different') or conf.get('differs') or []
        missing = conf.get('faltam') or conf.get('missing') or []
        if dif or missing:
            raise RuntimeError('the check: %d file(s) different, %d missing' % (len(dif), len(missing)))
        del b
        os.replace(parte, out_path)
        out['file'] = out_path
        out['size_before'] = len(before)
        out['size_after'] = len(lido)
        out['lines'] = _report(pack, usados, name, before, lido, out.get('renames'), det,
                               out.get('renamed_names'), semantico)
        return out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _obfuscation_summary(lines):
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


def _report(pack, usados, name, before, after, renames, det, renamed=None, semantico=False):
    out = [('title', '%s injected into %s' % (pack['title'], os.path.basename(name))),
           ('good', 'The script went back into the map with mpqadd: the file was not rebuilt (%s -> %s).'
            % (_kb(len(before)), _kb(len(after)))),
           ('good', 'The syntax check passed (%s).' % det)]
    if semantico == 'own':
        out.append(
            (
                'warn',
                'The map\'s own script already fails the check against the game scripts (for example the '
                'return bug of patch 1.23 and older): the pack added no new problem, and the map runs only '
                'on the game versions it ran on before.',
            )
        )
    elif semantico:
        out.append(('warn', 'The map uses natives the game scripts do not declare (the platform client provides them '
                             'at run time): the check reports those and nothing else, and the pack adds no native. '
                             'Only a syntax error blocks the injection.'))
    if renamed:
        out.append(('info', '  name(s) the map already used, prefixed: %s' % ', '.join(renamed)))
    if renames:
        out += [('info', '  ' + x.strip()) for x in renames]
    out.append(('subtitle', 'Options'))
    for k, _l, _d, _t in pack['options']:
        out.append(('info', '  %s: %s' % (k, usados.get(k))))
    out.append(('info', '  Works on: %s' % pack['needs']))
    if pack['language'] == LUA:
        out.append(('info', '  The OzzyCP body is already an obfuscated build; the comments (and the header that '
                            'explains the options) were removed.'))
    if pack['language'] == JASS:
        out.append(('warn', 'Test the map in game before sharing it: the pack runs from the map main, and the '
                             'obfuscator decrypts the strings in the first instruction of main.'))
    return out


def _kb(n):
    return ('%.1f kB' % (n / 1024.0)) if n < 1024 * 1024 else ('%.1f MB' % (n / 1048576.0))
