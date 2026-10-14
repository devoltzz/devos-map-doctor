# Compares the lobby (war3map.w3i) with the script's config(): players, controllers, teams.
import re



CONTROLS = {1: 'MAP_CONTROL_USER', 2: 'MAP_CONTROL_COMPUTER', 3: 'MAP_CONTROL_NEUTRAL', 4: 'MAP_CONTROL_RESCUABLE'}
NUM = r'(\$[0-9A-Fa-f]+|0[xX][0-9A-Fa-f]+|\d+)'
RX_PLAYERS = re.compile(r'\bSetPlayers\s*\(\s*' + NUM)
RX_CONTROL = re.compile(r'\bSetPlayerController\s*\(\s*Player\s*\(\s*' + NUM + r'\s*\)\s*,\s*(MAP_CONTROL_\w+)')
RX_TEAM = re.compile(r'\bSetPlayerTeam\s*\(\s*Player\s*\(\s*' + NUM + r'\s*\)\s*,\s*' + NUM)


def _num(t):
    if t[0] == '$':
        return int(t[1:], 16)
    if t[:2] in ('0x', '0X'):
        return int(t[2:], 16)
    return int(t)


def _body(text, name, lua):
    if lua:
        m = re.search(r'\bfunction\s+' + name + r'\s*\(\s*\)(.*?)\n[ \t]*end\b', text, re.S)
    else:
        m = re.search(r'\bfunction\s+' + name + r'\s+takes\s+nothing\s+returns\s+nothing(.*?)\bendfunction', text, re.S)
    return m.group(1) if m else ''


def _expanded(text, body, lua, depth=3):
    out = [body]
    if depth:
        for name in sorted(set(re.findall(r'(?:\bcall\s+|^\s*)([A-Za-z_]\w*)\s*\(\s*\)', body, re.M))):
            if name in ('config', 'main'):
                continue
            sub = _body(text, name, lua)
            if sub:
                out.append(_expanded(text, sub, lua, depth - 1))
    return '\n'.join(out)


def check_players(w3i_bytes, text, lua=False):
    from doctor.data import w3i
    m = w3i.parse_or_tolerant(w3i_bytes)
    out = {'players': {'w3i': len(m['players']), 'script': None}, 'controller': [], 'team': [], 'compared': False}
    config = _body(text, 'config', lua)
    if not config:
        return out
    config = _expanded(text, config, lua)
    sp = RX_PLAYERS.search(config)
    if sp is None:
        return out
    out['compared'] = True
    out['players']['script'] = _num(sp.group(1))
    control = dict((_num(a), b) for a, b in RX_CONTROL.findall(config))
    team = dict((_num(a), _num(b)) for a, b in RX_TEAM.findall(config))
    w3i_control = dict((p['number'], CONTROLS.get(p['type'])) for p in m['players'])
    w3i_team = {}
    for fi, f in enumerate(m['forces']):
        for bit in range(28):
            if f['mask'] >> bit & 1:
                w3i_team.setdefault(bit, fi)
    for i in sorted(set(control) | set(w3i_control)) if control else ():
        if control.get(i) != w3i_control.get(i):
            out['controller'].append((i, control.get(i), w3i_control.get(i)))
    for i in sorted(team):
        if i in control and team[i] != w3i_team.get(i):
            out['team'].append((i, team[i], w3i_team.get(i)))
    return out


def _slot(i):
    return 'Player %d' % (i + 1)


def scan(path, progress=None):
    from doctor.fix import unprotect
    from doctor.fix import single_player
    p = progress or (lambda *_a, **_k: None)
    out = {'findings': [], 'players': None, 'compared': False, 'file': None}
    p('Reading the map')
    try:
        a, sc, _strings = single_player.read_map(path)
    except BaseException as e:
        if isinstance(e, KeyboardInterrupt):
            raise
        out['error'] = 'The map does not open (%s).' % unprotect._error(e)
        return out
    out['file'] = sc['file']
    if sc['language'] is None or sc['bytes'] is None or sc['compiled']:
        out['reason'] = 'The script cannot be read.'
        return out
    d = unprotect._read(a, 'war3map.w3i')
    if not d:
        out['reason'] = 'The map has no war3map.w3i.'
        return out
    try:
        r = check_players(d, sc['bytes'].decode('utf-8', 'surrogateescape'), sc['language'] == 'lua')
    except Exception as e:
        out['reason'] = 'war3map.w3i does not read (%s).' % e
        return out
    out['players'] = r['players']
    out['compared'] = r['compared']
    if not r['compared']:
        out['reason'] = 'The script has no config() with SetPlayers, so there is nothing to compare.'
        return out
    pl = r['players']
    if pl['script'] != pl['w3i']:
        out['findings'].append(
            {
                'code': 'players_count',
                'severity': 'warning',
                'script': pl['script'],
                'w3i': pl['w3i'],
                'text': 'The lobby (war3map.w3i) has %d players and the script\'s config() sets %d.'
                % (pl['w3i'], pl['script']),
            }
        )
    if r['controller']:
        rows = ['%s: script %s, lobby %s' % (_slot(i), (s or 'none').replace('MAP_CONTROL_', '').lower(),
                                            (w or 'none').replace('MAP_CONTROL_', '').lower())
                for i, s, w in r['controller']]
        out['findings'].append({'code': 'player_controller', 'severity': 'warning', 'slots': r['controller'],
                                'text': 'The script and the lobby disagree on who controls %d slot(s): %s.'
                                % (len(rows), '; '.join(rows[:6]))})
    if r['team']:
        rows = ['%s: script team %d, lobby team %s' % (_slot(i), s, 'none' if w is None else w)
                for i, s, w in r['team']]
        out['findings'].append({'code': 'player_team', 'severity': 'warning', 'slots': r['team'],
                                'text': 'The script and the lobby disagree on the team of %d slot(s): %s.'
                                % (len(rows), '; '.join(rows[:6]))})
    return out
