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


def layer_parts(jn=False, blizzard=False):
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
            if matches:
                try:
                    return matches[0].encode('latin-1').decode('utf-8')
                except UnicodeError:
                    return matches[0]
    return None


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

