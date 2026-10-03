# The port rules: the diagnosis of a platform map and the parts of the layer it needs.
import os
import re
import subprocess
import sys


HERE = os.path.dirname(os.path.abspath(__file__))
ARCHIVE_ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
MODELO = os.path.join(HERE, 'model')
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


def model(fname, valores):
    t = open(os.path.join(MODELO, fname + '.template'), encoding='utf-8').read()

    def swap(m):
        if m.group(1) not in valores:
            raise SystemExit('model %s: the value of {{%s}} is missing' % (fname, m.group(1)))
        return str(valores[m.group(1)])
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

