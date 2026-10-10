# The port rules: the diagnosis of a platform map and the parts of the layer it needs.
import os
import re
import subprocess
import sys


HERE = os.path.dirname(os.path.abspath(__file__))
ARCHIVE_ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
TEMPLATE = os.path.join(HERE, 'model')
REF = os.path.join(ARCHIVE_ROOT, 'common', 'ref', '3.0')

LAYER_FIELDS = ['unit.file', 'unit.rangeN1', 'item.Art', 'item.Name', 'item.Ubertip']
EMPTY_EXPECTED = {
    'data_bytes': None,
    'lbkkapi': None,
    'typecast': None,
    'shadowed': None,
    'class1': None,
    'translation': None,
    'effects': None,
    'statuses': None,
    'engine': None,
    'ui_local': None,
    'desync': None,
}
RX_NATIVE = re.compile(r'(?m)^[ \t]*(?:constant[ \t]+)?native[ \t]+(\w+)[ \t]+takes[^\r\n]*')
RX_FUNCTION = re.compile(r'(?m)^[ \t]*function[ \t]+(\w+)[ \t]+takes')
RX_TEMPLATE = re.compile(r'\{\{([A-Z0-9_]+)\}\}')
ALWAYS_NAMES = ['(listfile)', 'war3map.j', 'war3map.lua', 'scripts\\war3map.j', 'war3map.w3i', 'war3map.wts',
                'war3map.w3e', 'war3map.w3u', 'war3map.w3t', 'war3map.w3a', 'war3map.w3b', 'war3map.w3d',
                'war3map.w3h', 'war3map.w3q', 'war3map.doo', 'war3mapUnits.doo', 'war3map.imp', 'war3map.mmp',
                'war3map.shd', 'war3map.wpm', 'war3mapMisc.txt', 'war3mapSkin.txt', 'war3mapExtra.txt',
                'war3mapMap.blp', 'war3mapPreview.tga', 'kkmap.jc', 'UI\\template.fdf',
                'Scripts\\Blizzard.j', 'Scripts\\common.j']


def log(s=''):
    print(s)
    sys.stdout.flush()


def run_action(label, cmd, cwd, log_file):
    env = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
    r = subprocess.run([sys.executable] + cmd, cwd=cwd, capture_output=True, text=True, encoding='utf-8',
                       errors='replace', env=env)
    out = (r.stdout or '') + (r.stderr or '')
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    open(log_file, 'w', encoding='utf-8').write(out)
    last_unit = next((line for line in reversed(out.strip().splitlines()) if line.strip()), '')
    log('   [%s] code %d -- %s  (log: %s)' % (label, r.returncode, last_unit[:150], os.path.basename(log_file)))
    return r.returncode, out


def model(fname, value_list):
    t = open(os.path.join(TEMPLATE, fname + '.template'), encoding='utf-8').read()

    def swap(m):
        if m.group(1) not in value_list:
            raise SystemExit('model %s: the value of {{%s}} is missing' % (fname, m.group(1)))
        return str(value_list[m.group(1)])
    return RX_TEMPLATE.sub(swap, t)


def save(file_path, body_text):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(body_text)


def layer_parts(jn=False, blizzard=False, ujapi=False):
    return (
        [
            'KK:part_0_natives.j',
            'KK:part_1_types.j',
            'out/slk_campos_tabela.j',
            ('KK:part_natives.j', 'out_profile_slots.j'),
            'KK:part_3_save2.j',
            'KK:part_2_profile.j',
            'KK:part_13_hooks.j',
            'KK:part_14_states.j',
            'KK:part_15_time.j',
            'KK:part_16_hash.j',
            'out_sh_chars.j',
            'out_seqs.j',
            'out_anim_names.j',
            'KK:part_17_quick_save.j',
            'KK:part_18_network_profile.j',
            'KK:kk_natives_extra.j',
            'KK:kk_natives_extra2.j',
            'KK:kk_natives_extra3.j',
            'KK:kk_deferred_save.j',
            'KK:kk_profiles_wait.j',
            'KK:kk_engine.j',
        ]
        + (['KK:kk_jn.j', 'KKN:nat_jn.j'] if jn else [])
        + ['KKN:nat_blizzard.j', 'KKN:nat_shop.j', 'KKN:nat_dzapi.j', 'KKN:nat_relatives.j', 'KKN:nat_emulated.j']
        + (['KKN:nat_ujapi.j', 'KKN:nat_ujapi_eq.j'] if ujapi else [])
        + (['out_blizzard_mapa.j'] if blizzard else [])
    )


JN_PARAMETERS = {
    '_sync_note': (
        'KK_SYNC_FATIA: DzSyncData above 200 bytes goes in pieces and the receiver reassembles before firing '
        'the map triggers (common/kk/compat/part_natives.j, SYNC section): the engine cuts BlzSendSyncData '
        'in ~255 bytes, and the M16 platform delivered the whole text.'
    ),
    'KK_SYNC_FATIA': 'true',
}


def natives_of(body_text):
    return set(m.group(1) for m in RX_NATIVE.finditer(body_text))


RX_LITERAL = r'\s*[!=]=\s*"((?:[^"\\\n]|\\.)*)"'


def _close_parens(t, i):
    max_depth = 1
    while i < len(t):
        c = t[i]
        if c == '"':
            i += 1
            while i < len(t) and t[i] not in '"\n':
                i += 2 if t[i] == '\\' else 1
        elif c == '(':
            max_depth += 1
        elif c == ')':
            max_depth -= 1
            if max_depth == 0:
                return i + 1
        elif c == '\n':
            return -1
        i += 1
    return -1


def return_literal(body_text, natives):
    t = body_text.replace('\r\n', '\n').replace('\r', '\n')
    for nat in natives:
        for m in re.finditer(r'\b%s\s*\(' % re.escape(nat), t):
            begin = t.rfind('\n', 0, m.start()) + 1
            if re.match(r'[ \t]*(?:constant[ \t]+)?native\b', t[begin:m.start()]):
                continue
            end_pos = _close_parens(t, m.end())
            if end_pos < 0:
                continue
            matches = []
            c = re.match(RX_LITERAL, t[end_pos:end_pos + 400])
            if c:
                matches.append(c.group(1))
            a = re.search(r'\bset[ \t]+(\w+(?:\[[^\]\n]*\])?)[ \t]*=[ \t]*$', t[begin:m.start()])
            if not matches and a:
                matches = [x.group(1) for x in re.finditer(r'(?<![\w\]])' + re.escape(a.group(1)) + RX_LITERAL, t)]
                matches.sort(key=lambda s: bool(re.match(r'^-?\d*$', s)))
            if not matches:
                matches = _literal_over_network(t, m.start(), a.group(1) if a else None)
            matches = [x for x in matches if _jass_text(x) not in JN_FAILURE_REPLIES]
            if matches:
                return _jass_text(matches[0])
    return None


JN_FAILURE_REPLIES = ('서버와 연결이 끊겨있습니다', 'M16Tool서버에 접속할 수 없거나 저장이 실패하였습니다',
                      '저장이 실패하였습니다.')


def _jass_text(lit):
    try:
        return lit.encode('latin-1').decode('utf-8')
    except UnicodeError:
        return lit


def _literal_over_network(t, pos, var):
    rx_sync = r'\bDzSyncData(?:Immediately)?[ \t]*\([ \t]*("(?:[^"\\\n]|\\.)*"|\w+)[ \t]*,'
    prefixes = []
    if var:
        end_pos = t.find('endfunction', pos)
        body = t[pos:end_pos if end_pos >= 0 else len(t)]
        for s in re.finditer(rx_sync + r'([^\n]*)', body):
            if re.search(r'(?<![\w\]])%s\b' % re.escape(var), s.group(2)):
                prefixes.append(s.group(1))
    else:
        begin = t.rfind('\n', 0, pos) + 1
        s = re.search(rx_sync, t[begin:pos])
        if s:
            prefixes.append(s.group(1))
    matches = []
    for p in prefixes:
        for r in re.finditer(r'\bDzTriggerRegisterSyncData[ \t]*\([ \t]*(\w+)[ \t]*,[ \t]*%s[ \t]*,' % re.escape(p), t):
            action_match = re.compile(r'\bTriggerAddAction[ \t]*\([ \t]*%s[ \t]*,[ \t]*function[ \t]+(\w+)[ \t]*\)'
                                      % re.escape(r.group(1))).search(t, r.end())
            if not action_match:
                continue
            f = re.compile(
                r'(?ms)^[ \t]*function[ \t]+%s\b.*?^[ \t]*endfunction' % re.escape(action_match.group(1))
            ).search(t)
            if not f:
                continue
            for c in re.finditer(RX_LITERAL, f.group(0)):
                lit = c.group(1)
                if len(_jass_text(lit)) > 1 and not re.match(r'^-?\d*$', lit):
                    matches.append(lit)
            if matches:
                return matches
    return matches


RX_GAME_END = re.compile(r'\b(?:EndGame|CustomDefeatBJ|CustomDefeatDialogBJ|RemovePlayer|RemovePlayerSimple)\s*\(')


def jnuse_gate(body_text):
    t = body_text.replace('\r\n', '\n').replace('\r', '\n')
    if 'JNUse' not in t:
        return 'false'
    name_list = set(m.group(1) for m in re.finditer(r'\bset[ \t]+(\w+)[ \t]*=[ \t]*JNUse[ \t]*\([ \t]*\)', t))
    rx = re.compile(r'\bJNUse[ \t]*\([ \t]*\)' + ''.join(r'|\b%s\b' % re.escape(n) for n in name_list))
    for body in re.findall(r'(?ms)^[ \t]*function\s+\w+.*?^[ \t]*endfunction', t):
        if not RX_GAME_END.search(body):
            continue
        for ln in body.split('\n'):
            if re.match(r'[ \t]*(?:if|elseif)\b', ln) and rx.search(ln):
                return 'true'
    return 'false'


def jninit_gate(body_text):
    t = body_text
    if re.search(r'\b(?:User)?StorageDownload___', t):
        return 'true'
    if re.search(r'==\s*\(?\s*-\s*1\b', t) and re.search(r'==\s*\(?\s*-\s*2\b', t) and \
            re.search(r'==\s*\(?\s*-\s*3\b', t) and 'JNObject' in t and 'Init' in t:
        return 'true'
    return 'false'


def jnregex_gate(body_text):
    if re.search(r'\bJNStringRegex\s*\(', body_text):
        return 'true'
    for m in re.finditer(r'\bJNStringCount[ \t]*\(', body_text):
        end_pos = _close_parens(body_text, m.end())
        if end_pos < 0:
            continue
        args, max_depth, i, cut = body_text[m.end():end_pos - 1], 0, 0, None
        while i < len(args) and cut is None:
            c = args[i]
            if c == '"':
                i += 1
                while i < len(args) and args[i] != '"':
                    i += 2 if args[i] == '\\' else 1
            elif c == '(':
                max_depth += 1
            elif c == ')':
                max_depth -= 1
            elif c == ',' and max_depth == 0:
                cut = i
            i += 1
        lits = re.findall(r'"((?:[^"\\\n]|\\.)*)"', args[cut + 1:]) if cut is not None else []
        if any(re.search(r'[\[\](){}.*+?^$|]|\\\\', s) for s in lits):
            return 'true'
    return 'false'


RX_PLUGIN = re.compile(r'\bJNServerPluginVersion[ \t]*\([ \t]*\)[ \t]*(<=|<|>=|>|==)[ \t]*\(?[ \t]*(\d+)')


def jnplugin_gate(body_text):
    v = None
    for ln in body_text.replace('\r\n', '\n').split('\n'):
        code = ln.split('//', 1)[0]
        for m in RX_PLUGIN.finditer(code):
            n = int(m.group(2)) + (1 if m.group(1) in ('<=', '>') else 0)
            v = n if v is None else max(v, n)
    return v


RX_STATE_14 = re.compile(r'ConvertUnitState\s*\(\s*(?:0[xX]0*14|\$0*14|20)\s*\)|\bUNIT_STATE_DAMAGE_MIN\b|'
                         r'\bDB_estado_le\s*\([^()]*(?:\([^()]*\)[^()]*)*,\s*0[xX]14\s*\)')


def ui_alpha(body_text):
    return 'true' if 'DzFrameSetText' in body_text and re.search(r'\|[cC]00[0-9A-Fa-f]{6}', body_text) else 'false'


RX_FDF_BUTTON = re.compile(
    r'(?<![\w"])Frame\s+"(?:BUTTON|GLUEBUTTON|GLUETEXTBUTTON|SIMPLEBUTTON)"\s+"([^"|\\]+)"', re.I
)


def fdf_buttons(extract, body_text):
    if 'DzCreateFrame' not in body_text or not extract or not os.path.isdir(extract):
        return None
    name_list = set()
    for d, _ds, fs in os.walk(extract):
        for f in fs:
            if f.lower().endswith('.fdf'):
                t = open(os.path.join(d, f), 'rb').read().decode('latin-1')
                name_list.update(m.group(1) for m in RX_FDF_BUTTON.finditer(t))
    in_use = sorted(n for n in name_list if re.search(r'\bDzCreateFrame\s*\(\s*"%s"' % re.escape(n), body_text))
    if not in_use:
        return None
    return '|%s|' % '|'.join(in_use)


def buttons_in_chunks(listing, chunks=8, byte_size=1000):
    name_list = [n for n in listing.split('|') if n]
    out, current, i = {}, '|', 1
    for n in name_list:
        if len(current) + len(n) + 1 > byte_size:
            out['KK_UI_BOTOES_%d' % i] = current
            i += 1
            current = '|'
            if i > chunks:
                break
        current += n + '|'
    if i <= chunks:
        out['KK_UI_BOTOES_%d' % i] = current
    for k in range(1, chunks + 1):
        out.setdefault('KK_UI_BOTOES_%d' % k, '')
    return out


def empty_sync(body_text):
    return 'true' if re.search(r'\bDzSyncData(?:Immediately)?\s*\([^,()]+,\s*""\s*\)', body_text) else 'false'


def _call(body_text, native, args=r'[^\n]*'):
    for m in re.finditer(r'\b%s[ \t]*\(%s' % (re.escape(native), args), body_text):
        begin = body_text.rfind('\n', 0, m.start()) + 1
        if not re.match(r'[ \t]*(?:constant[ \t]+)?native\b', body_text[begin:m.start()]):
            return True
    return False


def ui_mouse_pos(body_text):
    if 'DzSetMousePos' not in body_text:
        return 'false'
    for body in re.findall(r'(?ms)^[ \t]*function\s+\w+.*?^[ \t]*endfunction', body_text):
        if re.search(r'\bDzSetMousePos[ \t]*\(', body) and re.search(r'\bDzGetMouse[XY]Relative[ \t]*\(', body):
            return 'true'
    return 'false'


def ui_borders(body_text):
    return 'true' if _call(body_text, 'DzFrameEditBlackBorders', r'[^,\n]*,[ \t]*\(?[ \t]*0*\.?0*[ \t]*\)?[ \t]*\)') \
        else 'false'


def ui_portrait(body_text):
    return (
        'true'
        if re.search(r'\bDzFrameClearAllPoints[ \t]*\([ \t]*\(?[ \t]*DzFrameGetPortrait[ \t]*\([ \t]*\)', body_text)
        else 'false'
    )


RX_CARD = re.compile(r'\bJNMemoryGetInteger[ \t]*\([ \t]*\(?[ \t]*\w+[ \t]*\+[ \t]*400[ \t]*\)?[ \t]*\)')


def card_gate(body_text):
    if 'DzFrameGetCommandBarButton' not in body_text or '+400' not in body_text.replace(' ', ''):
        return 'false'
    for body in re.findall(r'(?ms)^[ \t]*function\s+\w+.*?^[ \t]*endfunction', body_text):
        if 'DzFrameGetCommandBarButton' in body and RX_CARD.search(body):
            return 'true'
    return 'false'


def covered_attack(extract):
    import contextlib
    import io
    from doctor.port import slk_tables
    if not extract or not slk_tables.has_slk(extract):
        return None
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            units, abils, _items = slk_tables.build_tables(extract)
    except Exception:
        return None
    button_slot = '3,0'
    U = os.path.join(extract, 'units')
    for f in os.listdir(U) if os.path.isdir(U) else ():
        if f.lower() == 'commandfunc.txt':
            sec = None
            for ln in open(os.path.join(U, f), 'rb').read().decode('utf-8', 'replace').splitlines():
                s = ln.strip()
                m = re.match(r'^\[(.+)\]$', s)
                if m:
                    sec = m.group(1).strip().lower()
                elif sec == 'cmdattack' and s.split('=', 1)[0].strip().lower() == 'buttonpos' and '=' in s:
                    button_slot = s.split('=', 1)[1].strip()

    def _norm(p):
        p = re.sub(r'\s+', '', p or '').strip('"')
        return p if re.match(r'^-?\d+,-?\d+$', p) else None
    button_slot = _norm(button_slot)
    if button_slot is None:
        return None
    out = []
    for uid, fields in units.items():
        if not uid or len(uid) != 4 or not re.match(r'^[\x21-\x7e]{4}$', uid):
            continue
        if (fields.get('weapson') or '0').strip() in ('', '0', '_', '-'):
            continue
        listing = ','.join(fields.get(k) or '' for k in ('abillist', 'heroabillist'))
        for aid in (a.strip().strip('"') for a in listing.split(',')):
            if aid and aid in abils and _norm(abils[aid].get('buttonpos')) == button_slot:
                out.append(uid)
                break
    return ','.join(sorted(out)) if out else None


BIG_LIFE = 10000000


def big_life(extract):
    import struct
    p = os.path.join(extract or '', 'war3map.w3u')
    if not os.path.isfile(p):
        return 'false'
    try:
        from doctor.data import objbin
        _ver, tables, _p = objbin.read_data(open(p, 'rb').read(), False)
    except Exception:
        return 'false'
    for t in tables:
        for _old, _new, mods in t:
            for mid, vt, _l, _d, val in mods:
                if mid == 'uhpm' and vt == 0 and len(val) == 4 and struct.unpack('<i', val)[0] >= BIG_LIFE:
                    return 'true'
    return 'false'


RX_MEM_CAP = r'(?:0x|\$)0*D38804\b'
RX_NUMBER = r'[0-9]+\.?[0-9]*|\.[0-9]+'


def speed_cap(body_text):
    if not re.search(RX_MEM_CAP, body_text):
        return None
    globals_block = dict((n, float(v)) for n, v in re.findall(
        r'(?m)^[ \t]*(?:constant[ \t]+)?real[ \t]+(\w+)[ \t]*=[ \t]*(%s)[ \t\r]*$' % RX_NUMBER, body_text))

    def field_value(arg):
        arg = arg.strip().strip('()').strip()
        if re.fullmatch(RX_NUMBER, arg):
            return float(arg)
        return globals_block.get(arg)
    vals = []
    for m in re.finditer(
        r'\bJNMemorySetReal[ \t]*\([^,\n]*%s[ \t]*\)?[ \t]*,[ \t]*([^)\n]+)\)' % RX_MEM_CAP, body_text
    ):
        vals.append(field_value(m.group(1)))
    for m in re.finditer(r'(?s)\bfunction[ \t]+(\w+)[ \t]+takes[ \t]+real[ \t]+(\w+)[ \t]+returns[ \t]+nothing(.*?)'
                         r'\bendfunction', body_text):
        fname, pair, body = m.groups()
        if re.search(r'\bJNMemorySetReal[ \t]*\([^,\n]*%s[ \t]*\)?[ \t]*,[ \t]*%s[ \t]*\)' % (RX_MEM_CAP, pair), body):
            vals.extend(field_value(a) for a in re.findall(r'\b%s[ \t]*\(([^()\n]*)\)' % fname, body_text))
    vals = [v for v in vals if v]
    return max(vals) if vals else None


def queried_keys(body_text):
    out = set()
    for m in re.finditer(r'\bDzIsKeyDown[ \t]*\([ \t]*(0[xX][0-9A-Fa-f]+|\$[0-9A-Fa-f]+|\d+)[ \t]*\)', body_text):
        x = m.group(1)
        n = int(x, 16) if x[:2].lower() == '0x' else int(x[1:], 16) if x[0] == '$' else int(x)
        if 0 < n < 256:
            out.add(n)
    return ','.join(str(n) for n in sorted(out))


def hero_xp(extract, body_text):
    if not re.search(r'\bDzGetUnitNeededXP[ \t]*\(', re.sub(r'(?m)^[ \t]*native\b.*$', '', body_text)):
        return {'KK_XP': 'false'}
    vals = {'NeedHeroXP': '200', 'NeedHeroXPFormulaA': '1', 'NeedHeroXPFormulaB': '100', 'NeedHeroXPFormulaC': '0'}
    p = None
    for d in os.listdir(extract) if extract and os.path.isdir(extract) else []:
        if d.lower() == 'war3mapmisc.txt':
            p = os.path.join(extract, d)
    sec = None
    for ln in (open(p, 'rb').read().decode('utf-8', 'replace').splitlines() if p else []):
        s = ln.strip()
        m = re.match(r'^\[(.+)\]$', s)
        if m:
            sec = m.group(1).strip().lower()
        elif sec == 'misc' and '=' in s and s.split('=', 1)[0].strip() in vals:
            vals[s.split('=', 1)[0].strip()] = s.split('=', 1)[1].strip()

    def real(x, default_value):
        try:
            return repr(float(x))
        except ValueError:
            return default_value
    table = ','.join(str(int(float(v))) for v in re.findall(r'-?\d+(?:\.\d+)?', vals['NeedHeroXP'])) or '200'
    return {'KK_XP': 'true', 'KK_XP_TABELA': table, 'KK_XP_A': real(vals['NeedHeroXPFormulaA'], '1.0'),
            'KK_XP_B': real(vals['NeedHeroXPFormulaB'], '100.0'), 'KK_XP_C': real(vals['NeedHeroXPFormulaC'], '0.0')}


def reads_state_14(body_text):
    return 'true' if RX_STATE_14.search(body_text) else 'false'


def inclusion_points():
    pts = set()
    folder = os.path.join(HERE, 'compat')
    for f in os.listdir(folder):
        if f.endswith('.j'):
            pts.update(re.findall(r'\{\{KK_INCLUI:([a-z0-9_]+)\}\}', open(os.path.join(folder, f), encoding='utf-8',
                                                                        errors='replace').read()))
    return sorted(pts)


def layer_functions():
    name_list = set()
    folder = os.path.join(HERE, 'compat')
    for f in os.listdir(folder):
        if f.endswith('.j'):
            name_list.update(
                RX_FUNCTION.findall(open(os.path.join(folder, f), encoding='utf-8', errors='replace').read())
            )
    return name_list

