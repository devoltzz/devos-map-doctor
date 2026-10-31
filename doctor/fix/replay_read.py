# Reads Warcraft III replays (.w3g): the timeline, the players that left, the sync and frame events, the checksum of every turn.
import os
import struct
import zlib



MAGIC = b'Warcraft III recorded game'
REFORGED_BUILD = 6089
BURST_MS = 3000
BURST_MIN = 3
FRAME_NEAR_MS = 6000
EVENT_MAX = 20000
BLOCK = 8192
STREAM_MAX = 128 << 20
CHAT_MODES = {0: 'all', 1: 'allies', 2: 'observers'}
LEAVE_REASONS = {0x01: 'connection closed by the remote game', 0x0C: 'connection closed by the local game',
                 0x0E: 'unknown (like 0x01)'}
LEAVE_RESULTS = {0x01: 'left', 0x07: 'left', 0x08: 'lost', 0x09: 'won', 0x0A: 'draw', 0x0B: 'left (observer)'}
FRAME_EVENTS = {
    1: 'control click',
    2: 'mouse enter',
    3: 'mouse leave',
    4: 'mouse up',
    5: 'mouse down',
    6: 'mouse wheel',
    7: 'checkbox checked',
    8: 'checkbox unchecked',
    9: 'editbox text changed',
    10: 'popup menu item changed',
    11: 'mouse double click',
    12: 'sprite animation update',
    13: 'slider value changed',
    14: 'dialog cancel',
    15: 'dialog accept',
    16: 'editbox enter',
}
class ReplayError(Exception):
    pass


class _Cut(Exception):
    pass


class _Buf(object):
    def __init__(self, data, pos=0):
        self.d = data
        self.p = pos

    def left(self):
        return len(self.d) - self.p

    def skip(self, n):
        if n < 0 or self.p + n > len(self.d):
            raise _Cut()
        self.p += n

    def take(self, n):
        if n < 0 or self.p + n > len(self.d):
            raise _Cut()
        v = self.d[self.p:self.p + n]
        self.p += n
        return v

    def u8(self):
        return self.take(1)[0]

    def u16(self):
        return struct.unpack('<H', self.take(2))[0]

    def u32(self):
        return struct.unpack('<I', self.take(4))[0]

    def f32(self):
        return struct.unpack('<f', self.take(4))[0]

    def cstr(self):
        i = self.d.find(b'\0', self.p)
        if i < 0:
            raise _Cut()
        v = self.d[self.p:i]
        self.p = i + 1
        return v.decode('utf-8', 'replace')


def _container(data):
    i = data.find(MAGIC)
    if i < 0:
        raise ReplayError('This is not a Warcraft III replay (the "Warcraft III recorded game" mark is missing).')
    b = _Buf(data, i)
    try:
        b.cstr()
        header_size = b.u32()
        compressed = b.u32()
        header_version = b.u32()
        decompressed = b.u32()
        count = b.u32()
        if header_version == 0:
            exp = b.u16()
            version = b.u16()
            build = b.u16()
            flags = b.u16()
            duration = b.u32()
            sub = {'ident': 'W3XP' if exp else 'WAR3', 'version': version, 'build': build, 'flags': flags,
                   'duration_ms': duration}
        else:
            ident = b.take(4)[::-1].decode('ascii', 'replace')
            version = b.u32()
            build = b.u16()
            flags = b.u16()
            duration = b.u32()
            sub = {'ident': ident, 'version': version, 'build': build, 'flags': flags, 'duration_ms': duration}
    except _Cut:
        raise ReplayError('The replay header is cut.')
    head = {'header_size': header_size, 'compressed': compressed, 'header_version': header_version,
            'decompressed': decompressed, 'blocks': count}
    head.update(sub)
    head['reforged'] = (sub['build'] or 0) >= REFORGED_BUILD
    pos = i + header_size
    out = []
    n = 0
    truncated = False
    cap = min(decompressed + BLOCK if decompressed else STREAM_MAX, STREAM_MAX)
    total = 0
    while pos < len(data):
        step = 12 if head['reforged'] else 8
        if pos + step > len(data):
            truncated = True
            break
        if head['reforged']:
            size, _usize, _ck = struct.unpack_from('<3I', data, pos)
        else:
            size, _usize = struct.unpack_from('<HH', data, pos)
        blk = data[pos + step:pos + step + size]
        if len(blk) < size:
            truncated = True
        try:
            d = zlib.decompressobj()
            pedaco = d.decompress(blk, min(BLOCK, cap - total) + 1)
        except zlib.error:
            truncated = True
            break
        if len(pedaco) > BLOCK or total + len(pedaco) > cap:
            truncated = True
            break
        total += len(pedaco)
        out.append(pedaco)
        n += 1
        pos += step + size
        if len(blk) < size:
            break
    head['blocks_read'] = n
    raw = b''.join(out)
    if decompressed and len(raw) > decompressed:
        raw = raw[:decompressed]
    elif decompressed and len(raw) < decompressed:
        truncated = True
    return head, raw, truncated


def _decode_meta_string(hexs):
    raw = bytes.fromhex(hexs)
    out = bytearray()
    mask = 0
    for i, c in enumerate(raw):
        if i % 8 == 0:
            mask = c
        else:
            out.append(c if mask & (1 << (i % 8)) else (c - 1) & 0xFF)
    return bytes(out)


def _varint(b, p):
    v = 0
    s = 0
    while p < len(b):
        c = b[p]
        p += 1
        v |= (c & 0x7F) << s
        s += 7
        if not c & 0x80:
            return v, p
    raise _Cut()


def _proto(b):
    out = {}
    p = 0
    while p < len(b):
        key, p = _varint(b, p)
        f, w = key >> 3, key & 7
        if w == 0:
            v, p = _varint(b, p)
        elif w == 2:
            n, p = _varint(b, p)
            v = b[p:p + n]
            p += n
        elif w == 1:
            v, p = b[p:p + 8], p + 8
        elif w == 5:
            v, p = b[p:p + 4], p + 4
        else:
            break
        out.setdefault(f, []).append(v)
    return out


def _host_record(b):
    pid = b.u8()
    name = b.cstr()
    b.skip(b.u8())
    return {'id': pid, 'name': name}


def _metadata(raw):
    b = _Buf(raw)
    b.skip(5)
    players = [_host_record(b)]
    game_name = b.cstr()
    b.cstr()
    i = raw.find(b'\0', b.p)
    if i < 0:
        raise _Cut()
    enc = raw[b.p:i]
    b.p = i + 1
    meta = _map_meta(_decode_meta_string(enc.hex()))
    player_count = b.u32()
    game_type = b.take(4).hex()
    locale = b.take(4).hex()
    while b.left() and raw[b.p] == 0x16:
        b.p += 1
        players.append(_host_record(b))
        b.skip(4)
    reforged = []
    skins = {}
    post202 = False
    while b.left() and raw[b.p] in (0x38, 0x39):
        if b.u8() == 0x38:
            post202 = True
        sub = b.u8()
        n = b.u32()
        data = b.take(n)
        try:
            msg = _proto(data)
        except _Cut:
            msg = {}
        if sub == 3:
            def _txt(v):
                return v.decode('utf-8', 'replace') if isinstance(v, (bytes, bytearray)) else ''
            reforged.append({'id': (msg.get(1) or [0])[0],
                             'name': _txt((msg.get(2) or [b''])[0]),
                             'clan': _txt((msg.get(3) or [b''])[0])})
        elif sub == 4:
            skins[(msg.get(1) or [0])[0]] = len(msg.get(2) or [])
    if b.u8() != 0x19:
        raise _Cut()
    remaining = b.u16()
    count = b.u8()
    slots = []
    for _ in range(count):
        s = b.take(9)
        slots.append({'player': s[0], 'download': s[1], 'status': s[2], 'computer': s[3], 'team': s[4],
                      'color': s[5], 'race': s[6], 'ai': s[7], 'handicap': s[8]})
    seed = b.u32()
    mode = b.u8()
    spots = b.u8()
    names = dict((r['id'], r['name']) for r in reforged)
    for pl in players:
        if pl['id'] in names and names[pl['id']]:
            pl['name'] = names[pl['id']]
    meta.update(game_name=game_name, player_count=player_count, game_type=game_type, locale=locale, seed=seed,
                select_mode=mode, start_spots=spots, slots_ok=(remaining == 1 + count * 9 + 6), post202=post202,
                skins=skins)
    return {'players': players, 'slots': slots, 'map': meta}, b.p


def _map_meta(b):
    r = _Buf(b)
    speed = r.u8()
    f2 = r.u8()
    f3 = r.u8()
    f4 = r.u8()
    r.skip(5)
    checksum = r.take(4).hex()
    path = r.cstr()
    creator = r.cstr()
    sha1 = ''
    try:
        r.skip(1)
        sha1 = r.take(20).hex()
    except _Cut:
        pass
    return {'speed': speed, 'hide_terrain': bool(f2 & 1), 'explored': bool(f2 & 2), 'always_visible': bool(f2 & 4),
            'observer_mode': (f2 >> 4) & 3, 'teams_together': bool(f2 & 0x40), 'fixed_teams': bool(f3 & 6),
            'shared_control': bool(f4 & 1), 'random_hero': bool(f4 & 2), 'random_races': bool(f4 & 4),
            'referees': bool(f4 & 0x40), 'checksum': checksum, 'path': path, 'creator': creator, 'sha1': sha1}


def _cache(b):
    return b.cstr(), b.cstr(), b.cstr()


def _unit_cache(b):
    b.skip(4)
    for _ in range(b.u32()):
        b.skip(12)
    b.skip(48)
    for _ in range(b.u32()):
        b.skip(8)
    b.skip(12)
    for _ in range(b.u32()):
        b.skip(4)
    b.skip(4 + 2)


def _action(b, aid):
    if aid in (0x1, 0x2, 0x4, 0x5, 0x1a, 0x20, 0x22, 0x23, 0x24, 0x25, 0x26, 0x29, 0x2a, 0x2b, 0x2c, 0x2f, 0x61, 0x66,
               0x67):
        return {'id': aid} if aid in (0x61, 0x66, 0x67) else None
    if aid in (0x3, 0x75):
        return {'id': aid, 'value': b.u8()}
    if aid == 0x6:
        b.cstr()
        b.cstr()
        b.u8()
        return None
    if aid == 0x7:
        b.skip(4)
        return None
    if aid == 0x10:
        b.skip(14)
        return None
    if aid == 0x11:
        b.skip(22)
        return None
    if aid == 0x12:
        b.skip(30)
        return None
    if aid == 0x13:
        b.skip(38)
        return None
    if aid == 0x14:
        b.skip(43)
        return None
    if aid == 0x15:
        b.skip(51)
        return None
    if aid in (0x16, 0x17):
        b.u8()
        b.skip(b.u16() * 8)
        return None
    if aid == 0x18:
        b.skip(2)
        return None
    if aid == 0x19:
        b.skip(12)
        return None
    if aid in (0x1b, 0x1c):
        b.skip(9)
        return None
    if aid == 0x1d:
        b.skip(8)
        return None
    if aid in (0x1e, 0x1f):
        b.skip(5)
        return None
    if aid == 0x21:
        b.skip(8)
        return None
    if aid in (0x27, 0x28, 0x2d):
        b.skip(5)
        return None
    if aid == 0x2e:
        b.skip(4)
        return None
    if aid == 0x50:
        b.skip(5)
        return None
    if aid == 0x51:
        b.skip(9)
        return None
    if aid == 0x60:
        b.skip(8)
        b.cstr()
        return None
    if aid == 0x62:
        b.skip(12)
        return None
    if aid == 0x63:
        b.skip(8)
        return None
    if aid in (0x64, 0x65):
        b.skip(8)
        return None
    if aid == 0x68:
        b.skip(12)
        return {'id': aid}
    if aid in (0x69, 0x6a):
        b.skip(16)
        return None
    if aid in (0x6b, 0x6c):
        c = _cache(b)
        b.skip(4)
        return {'id': aid, 'cache': c}
    if aid == 0x6d:
        c = _cache(b)
        b.skip(1)
        return {'id': aid, 'cache': c}
    if aid == 0x6e:
        c = _cache(b)
        _unit_cache(b)
        return {'id': aid, 'cache': c}
    if aid in (0x70, 0x71, 0x72, 0x73):
        _cache(b)
        return None
    if aid == 0x76:
        b.skip(10)
        return None
    if aid == 0x77:
        b.skip(8)
        b.skip(b.u32())
        return {'id': aid, 'api': True}
    if aid == 0x78:
        ident = b.cstr()
        val = b.cstr()
        b.skip(4)
        return {'id': aid, 'sync': ident, 'value': val}
    if aid == 0x79:
        b.skip(8)
        ev = b.u32()
        v = b.f32()
        text = b.cstr()
        return {'id': aid, 'frame': ev, 'value': v, 'text': text}
    if aid == 0x7a:
        b.skip(20)
        return None
    if aid == 0x7b:
        b.skip(16)
        return None
    if aid == 0xa0:
        b.skip(14)
        return None
    if aid == 0xa1:
        b.skip(9)
        return None
    raise KeyError(aid)


SHIFTS = {'none': 0x100, 'w3gjs': 0x77, 'down': 0x76}


def _block_actions(data, shift):
    b = _Buf(data)
    out = []
    thr = SHIFTS[shift]
    while b.left():
        aid = b.u8()
        if aid > thr:
            aid += 1
        try:
            a = _action(b, aid)
        except (_Cut, KeyError):
            return out, False
        if a:
            out.append(a)
    return out, True


def _choose_shift(blocks, hint):
    sample = blocks[:4000]
    best = None
    for sh in [hint] + [x for x in ('down', 'w3gjs', 'none') if x != hint]:
        bad = sum(1 for d in sample if not _block_actions(d, sh)[1])
        if best is None or bad < best[1]:
            best = (sh, bad, len(sample))
        if bad == 0:
            break
    return best


def _game_data(raw, start):
    b = _Buf(raw, start)
    blocks = []
    cut = False
    clock = 0
    while b.left():
        at = b.p
        try:
            bid = b.u8()
            if bid == 0x17:
                reason = b.u32()
                pid = b.u8()
                result = b.u32()
                b.skip(4)
                blocks.append({'k': 'leave', 't': clock, 'player': pid, 'reason': reason, 'result': result})
            elif bid in (0x1a, 0x1b, 0x1c):
                b.skip(4)
                blocks.append({'k': 'start', 't': clock, 'n': bid})
            elif bid in (0x1e, 0x1f):
                size = b.u16()
                end = b.p + size
                inc = b.u16()
                clock += inc
                cmds = []
                while b.p < end:
                    pid = b.u8()
                    n = b.u16()
                    cmds.append((pid, b.take(n)))
                if b.p != end:
                    b.p = end
                blocks.append({'k': 'turn', 't': clock, 'inc': inc, 'cmds': cmds})
            elif bid == 0x20:
                pid = b.u8()
                n = b.u16()
                end = b.p + n
                flags = b.u8()
                mode = b.u32() if flags == 0x20 else 0
                msg = b.cstr()
                b.p = max(b.p, min(end, len(raw)))
                blocks.append({'k': 'chat', 't': clock, 'player': pid, 'mode': mode, 'text': msg})
            elif bid == 0x22:
                n = b.u8()
                v = b.take(n)
                blocks.append({'k': 'check', 't': clock, 'value': v.hex()})
            elif bid == 0x23:
                b.skip(10)
            elif bid == 0x2f:
                b.skip(8)
            elif bid == 0:
                break
            else:
                blocks.append({'k': 'unknown', 't': clock, 'id': bid, 'at': at})
                break
        except _Cut:
            cut = True
            break
    return blocks, cut


def parse(data, source=None):
    head, raw, truncated = _container(data)
    out = {'path': source, 'error': None, 'header': head, 'game': {}, 'players': [], 'slots': [], 'timeline': [],
           'chat': [], 'leaves': [], 'syncs': {}, 'frames': [], 'checksums': [], 'findings': [], 'format': {},
           'turns': 0, 'duration_ms': head.get('duration_ms'), 'truncated': truncated, 'stats': {},
           'source_kind': 'crash' if os.path.basename(source or '').lower() == 'tempreplay.w3g' else 'replay'}
    try:
        md, start = _metadata(raw)
    except _Cut:
        out['error'] = 'The replay has no complete game description (it was cut before the game started).'
        out['findings'] = [('warn', out['error'])]
        return out
    out['game'] = md['map']
    out['slots'] = md['slots']
    out['players'] = md['players']
    names = dict((p['id'], p['name']) for p in md['players'])
    blocks, cut = _game_data(raw, start)
    out['truncated'] = truncated or cut
    cmd_blocks = [d for k in blocks if k['k'] == 'turn' for _p, d in k['cmds']]
    hint = 'w3gjs' if md['map']['post202'] else ('down' if head['reforged'] and head['version'] >= 10200 else 'none')
    shift, bad, used = _choose_shift(cmd_blocks, hint)
    out['format'] = {'action_shift': shift, 'unreadable_command_blocks': bad, 'command_blocks': len(cmd_blocks),
                     'post202_records': md['map']['post202']}
    t_events = []
    idc = {}
    syncs = out['syncs']
    last_turn_t = 0
    unknown = None
    count_turns = 0
    for k in blocks:
        t = k['t']
        kind = k['k']
        if kind == 'turn':
            count_turns += 1
            last_turn_t = t
            for pid, d in k['cmds']:
                acts, _ok = _block_actions(d, shift)
                for a in acts:
                    idc[a['id']] = idc.get(a['id'], 0) + 1
                    if 'sync' in a:
                        s = syncs.setdefault(a['sync'], {'count': 0, 'first': t, 'last': t, 'players': set()})
                        s['count'] += 1
                        s['last'] = t
                        s['players'].add(pid)
                        if len(t_events) < EVENT_MAX:
                            t_events.append({'t': t, 'kind': 'sync', 'player': pid, 'name': names.get(pid, '?'),
                                             'id': a['sync'], 'value': a['value'][:60]})
                    elif 'frame' in a:
                        e = {'t': t, 'kind': 'frame', 'player': pid, 'name': names.get(pid, '?'),
                             'event': a['frame'], 'value': a['value'], 'text': a['text'][:60]}
                        out['frames'].append(e)
                        if len(t_events) < EVENT_MAX:
                            t_events.append(e)
        elif kind == 'chat':
            e = {'t': t, 'kind': 'chat', 'player': k['player'], 'name': names.get(k['player'], '?'),
                 'mode': CHAT_MODES.get(k['mode'], 'player %d' % (k['mode'] - 3) if k['mode'] >= 3 else str(k['mode'])),
                 'text': k['text']}
            out['chat'].append(e)
            t_events.append(e)
        elif kind == 'leave':
            e = {'t': t, 'kind': 'leave', 'player': k['player'], 'name': names.get(k['player'], '?'),
                 'reason': k['reason'], 'result': k['result'],
                 'why': LEAVE_REASONS.get(k['reason'], '0x%X' % k['reason']),
                 'what': LEAVE_RESULTS.get(k['result'], '0x%X' % k['result'])}
            out['leaves'].append(e)
            t_events.append(e)
        elif kind == 'check':
            out['checksums'].append((t, k['value']))
        elif kind == 'unknown':
            unknown = k
    out['timeline'] = t_events
    out['turns'] = count_turns
    out['stats'] = {'actions': dict(sorted(idc.items())), 'last_turn_ms': last_turn_t}
    if unknown:
        out['stats']['unknown_block'] = unknown
    for s in syncs.values():
        s['players'] = sorted(s['players'])
    out['findings'] = _findings(out)
    return out


MAX_REPLAY = 64 << 20


def read(path):
    if os.path.isdir(path):
        for n in ('TempReplay.w3g', 'LastReplay.w3g'):
            if os.path.isfile(os.path.join(path, n)):
                path = os.path.join(path, n)
                break
    try:
        if os.path.getsize(path) > MAX_REPLAY:
            return {
                'path': path,
                'error': 'This file is too big to be a replay (%d MB).' % (os.path.getsize(path) >> 20),
                'findings': [],
            }
        with open(path, 'rb') as f:
            data = f.read()
    except OSError as e:
        return {'path': path, 'error': 'The replay could not be read: %s' % e, 'findings': []}
    try:
        r = parse(data, path)
    except ReplayError as e:
        return {'path': path, 'error': str(e), 'findings': []}
    return r


def frame_event(n):
    return 'event %d (%s)' % (n, FRAME_EVENTS[n]) if n in FRAME_EVENTS else 'event %d' % n


def bursts(leaves, window=BURST_MS, minimum=BURST_MIN):
    out = []
    i = 0
    ls = sorted(leaves, key=lambda e: e['t'])
    while i < len(ls):
        j = i
        while j + 1 < len(ls) and ls[j + 1]['t'] - ls[i]['t'] <= window:
            j += 1
        if j - i + 1 >= minimum:
            out.append((ls[i]['t'], ls[i:j + 1]))
            i = j + 1
        else:
            i += 1
    return out


def _clock(ms):
    s = int((ms or 0) // 1000)
    return '%d:%02d' % (s // 60, s % 60)


def _findings(r):
    f = []
    h = r['header']
    g = r['game']
    f.append(('muted', 'Game version %s, build %s%s; %s of game time in the turns (the header says %s).' % (
        h.get('version'), h.get('build'), ' (Reforged format)' if h.get('reforged') else '',
        _clock(r['stats'].get('last_turn_ms')), _clock(h.get('duration_ms')))))
    if g.get('path'):
        f.append(('muted', 'The map: %s (checksum %s).' % (g['path'], g.get('checksum'))))
    if r['truncated']:
        f.append(('muted', 'The replay is cut: it ends at %s of game time (the game wrote it while it was closing, or '
                           'it was copied before it ended).' % _clock(r['stats'].get('last_turn_ms'))))
    fmt = r['format']
    if fmt.get('unreadable_command_blocks'):
        f.append(('warn', '%d of %d command blocks could not be read to their end: the reader does not know some '
                          'action of this game version.' % (fmt['unreadable_command_blocks'], fmt['command_blocks'])))
    if r['stats'].get('unknown_block'):
        u = r['stats']['unknown_block']
        f.append(
            (
                'warn',
                'The game data has a block the replay reader does not know (id 0x%02X at byte %d): the timeline '
                'stops there.' % (u['id'], u['at']),
            )
        )
    bs = bursts(r['leaves'])
    for t, ev in bs[:3]:
        f.append(('warn', 'Suspected desync or disconnect: %d players left within %.1f s at %s (%s). A burst of leaves '
                          'with a "remote game closed" reason is what a desync looks like in a replay, but a group '
                          'quitting a lost game looks the same: this is a suspicion, not a finding.' % (
                              len(ev), (ev[-1]['t'] - ev[0]['t']) / 1000.0, _clock(t),
                              ', '.join(e['name'] for e in ev[:6]))))
    if r['leaves'] and not bs:
        e = r['leaves'][-1]
        f.append(('muted', '%d leave(s); the last: %s at %s (%s, %s).' % (len(r['leaves']), e['name'], _clock(e['t']),
                                                                     e['why'], e['what'])))
    if r['frames']:
        e = r['frames'][-1]
        gap = r['stats'].get('last_turn_ms', 0) - e['t']
        recent = sum(1 for x in r['frames'] if r['stats'].get('last_turn_ms', 0) - x['t'] <= FRAME_NEAR_MS)
        crash = r.get('source_kind') == 'crash'
        f.append(
            (
                'warn' if crash and gap <= FRAME_NEAR_MS else 'muted',
                '%d frame event(s) (BlzTriggerRegisterFrameEvent) were sent; the last one by %s at %s '
                '(%s, %s)%s.'
                % (
                    len(r['frames']),
                    e['name'],
                    _clock(e['t']),
                    frame_event(e['event']),
                    'text "%s"' % e['text'] if e['text'] else 'no text',
                    (
                        '; the replay ends %.1f s later (%d frame events in the last %d s). This is the '
                        'game\'s own crash copy of the replay: a frame event just before the end is a '
                        'SUSPICION about the frame callbacks (the UI code that a click, a mouse enter or a mouse leave '
                        'runs), not a measured cause' % (gap / 1000.0, recent, FRAME_NEAR_MS // 1000)
                    )
                    if crash and gap <= FRAME_NEAR_MS
                    else '',
                ),
            )
        )
    if r.get('source_kind') == 'crash' and r['stats'].get('last_turn_ms', 0) < 1000 and r['turns']:
        f.append(('muted', 'The game closed %.2f s of game time after it started: the crash happened while the map was '
                           'loading or starting, before any play (a diagnostic copy made in "init" mode writes its '
                           'markers at once and shows how far the script got).' % (
                               r['stats'].get('last_turn_ms', 0) / 1000.0)))
    if r['syncs']:
        top = sorted(r['syncs'].items(), key=lambda kv: -kv[1]['count'])[:4]
        f.append(('muted', '%d BlzSendSyncData packet kind(s): %s.' % (
            len(r['syncs']), ', '.join('"%s" x%d' % (k, v['count']) for k, v in top))))
    if r['chat']:
        f.append(('muted', '%d chat message(s).' % len(r['chat'])))
    f.append(('muted', '%d turns, %d state checksums (block 0x22).' % (r['turns'], len(r['checksums']))))
    return f


def compare(a, b):
    ra = a if isinstance(a, dict) else read(a)
    rb = b if isinstance(b, dict) else read(b)
    for r in (ra, rb):
        if r.get('error'):
            return {'same_game': False, 'turns': (0, 0), 'first_difference': None, 'text': r['error']}
    ga, gb = ra['game'], rb['game']
    same = (ga.get('seed') == gb.get('seed') and ga.get('checksum') == gb.get('checksum') and
            ga.get('game_name') == gb.get('game_name'))
    ca, cb = ra['checksums'], rb['checksums']
    first = None
    for i in range(min(len(ca), len(cb))):
        if ca[i][1] != cb[i][1]:
            first = {'turn': i, 't': ca[i][0], 'a': ca[i][1], 'b': cb[i][1]}
            break
    if not same:
        txt = (
            'These are not two recordings of the same game (the random seed, the game name or the map checksum differ).'
        )
    elif first:
        txt = ('The state checksums first differ at turn %d (%s of game time): %s against %s. From there the two '
               'machines ran different games.' % (first['turn'], _clock(first['t']), first['a'], first['b']))
    else:
        txt = 'The %d state checksums of the shorter replay are all equal.' % min(len(ca), len(cb))
    return {'same_game': same, 'turns': (len(ca), len(cb)), 'first_difference': first, 'text': txt}


def folders(limit=20):
    from doctor.fix import diagnose
    base = os.path.join(diagnose.documents(), 'Warcraft III')
    out = []
    err = os.path.join(base, 'Errors')
    if os.path.isdir(err):
        for d in os.listdir(err):
            p = os.path.join(err, d, 'TempReplay.w3g')
            if os.path.isfile(p):
                out.append({'path': p, 'name': d, 'kind': 'crash'})
    bnet = os.path.join(base, 'BattleNet')
    if os.path.isdir(bnet):
        for acc in os.listdir(bnet):
            rp = os.path.join(bnet, acc, 'Replays')
            if not os.path.isdir(rp):
                continue
            for root, _dirs, files in os.walk(rp):
                for f in files:
                    if f.lower().endswith('.w3g'):
                        out.append({'path': os.path.join(root, f), 'name': f,
                                    'kind': 'last' if f.lower() == 'lastreplay.w3g' else 'saved'})
    vivos = []
    for x in out:
        try:
            st = os.stat(x['path'])
        except OSError:
            continue
        x['modified'] = st.st_mtime
        x['bytes'] = st.st_size
        vivos.append(x)
    out = vivos
    out.sort(key=lambda x: -x['modified'])
    return out[:limit]


def text(r, everything=False):
    from doctor.fix import crash_report
    if r.get('error'):
        return crash_report.sem_usuario(r['error'])
    out = ['Replay: %s' % crash_report.sem_usuario(r.get('path') or '')]
    out += ['- ' + crash_report.sem_usuario(t) for _s, t in r['findings']]
    if r['players']:
        out.append('Players: ' + ', '.join('%s (%d)' % (p['name'], p['id']) for p in r['players']))
    if r['leaves']:
        out.append('Leaves (time, player, reason, result):')
        out += ['  %s %s: %s, %s' % (_clock(e['t']), e['name'], e['why'], e['what']) for e in r['leaves'][:30]]
    if r['chat']:
        out.append('Chat:')
        out += ['  %s %s [%s]: %s' % (_clock(e['t']), e['name'], e['mode'], e['text']) for e in r['chat'][:40]]
    if r['frames']:
        out.append('Frame events (the last 10):')
        out += [
            '  %s %s: %s value %.2f %s' % (_clock(e['t']), e['name'], frame_event(e['event']), e['value'], e['text'])
            for e in r['frames'][-10:]
        ]
    if everything:
        out.append('Timeline:')
        out += ['  %s %s %s' % (_clock(e['t']), e['kind'], {k: v for k, v in e.items() if k not in ('t', 'kind')})
                for e in r['timeline'][:400]]
    return '\n'.join(out)
