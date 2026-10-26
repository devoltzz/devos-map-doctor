# Writes the map info, object data, doodads and terrain of an older game version and lists the media that version does not load.
import collections
import os
import struct



FLAGS_BY_FORMAT = ((31, (0x20000, 0x40000)),
                   (33, (0x80000, 0x100000, 0x200000, 0x400000)),
                   (39, (0x800000, 0x1000000, 0x2000000)))
FLAG_NAMES = {0x20000: 'accurate_probability', 0x40000: 'custom_ability_skin', 0x80000: 'disable_deny_icon',
              0x100000: 'force_default_camera_zoom', 0x200000: 'force_max_camera_zoom',
              0x400000: 'force_min_camera_zoom', 0x800000: 'hd_water_color', 0x1000000: 'alpha_tile_minimap_color',
              0x2000000: 'dynamic_minimap'}
FIELDS_BY_FORMAT = ((27, ('game_version',)), (28, ('script_language',)), (29, ('supported_modes',)),
                    (30, ('game_data_version',)), (32, ('v33_extra',)), (34, ('hd_water',)), (35, ('hd_water_envmap',)),
                    (36, ('fog_heights',)), (37, ('race_crest',)), (38, ('minimap_alpha_color',)), (39, ('fog_extra',)))
PLAYER_FIELDS = ((31, ('enemy_low', 'enemy_high')), (37, ('hud',)))
REMAINING = ('object data version 3 and the war3mapSkin.* files', 'the script (the *WithSkin calls, the dialogue '
             'functions)', 'the trigger file in the 1.31 format', 'terrain, doodads, units, regions, cameras, sounds')
MODEL_MAX_OLD = 800
FIRST_PATCH = {'dds': (1, 32, 0), 'flac': (1, 32, 0), 'model': (1, 32, 0), 'ogg': (1, 30, 0)}
MODEL_MAX_REFORGED = {'2.0.4': 1200}
MODEL_EXTS = ('.mdx',)


class Refused(Exception):
    pass


def _key(version):
    from doctor.data import wc3_versions
    return wc3_versions._key(version)


def _target(version):
    from doctor.data import wc3_versions
    v = wc3_versions.normalize(version)
    if v is None or v == wc3_versions.REFORGED:
        raise ValueError('the target has to be an older game (1.24 to 1.29, or Reforged %s): %r'
                         % (', '.join(wc3_versions.REFORGED_OLD), version))
    return v, wc3_versions.limits(v)


def _older_reforged(version):
    from doctor.data import wc3_versions
    return wc3_versions.reforged_game(version)


REFORGED_OLD_SAVE = {'2.0.4': (6117, [2, 0, 4, 23745])}


def editor_number(version):
    from doctor.fix import game_builds
    from doctor.data import wc3_versions
    v = wc3_versions.normalize(version)
    if v in REFORGED_OLD_SAVE:
        return REFORGED_OLD_SAVE[v][0]
    for b in game_builds.builds():
        if b['label'] == v and b['editor']:
            return b['editor']
    from doctor.fix import editor_version
    return editor_version.profile(version)['editor']


def plan_w3i(model, version='1.29.2'):
    v, lim = _target(version)
    target = lim['w3i']
    src = model['version']
    out = {'target': target, 'from': src, 'refusals': [], 'cleared_flags': [], 'dropped': [], 'warnings': []}
    if src <= target:
        return out
    if model.get('script_language') == 1 and not lim.get('lua'):
        out['refusals'].append('the map script is Lua: Warcraft III %s does not run Lua (it starts with 1.31)' % v)
    n = len(model.get('players') or [])
    if n > lim['players']:
        out['refusals'].append('the map has %d player slots; Warcraft III %s has %d' % (n, v, lim['players']))
    for fmt, bits in FLAGS_BY_FORMAT:
        if fmt > target and src >= fmt:
            out['cleared_flags'] += [FLAG_NAMES[b] for b in bits if model['flags'] & b]
    for fmt, names in FIELDS_BY_FORMAT:
        if src >= fmt > target:
            out['dropped'] += [k for k in names if k in model]
    for fmt, names in PLAYER_FIELDS:
        if src >= fmt > target:
            out['dropped'] += ['player.' + k for k in names if any(k in p for p in model.get('players') or [])]
    if model.get('game_data_version') == 2 and not _older_reforged(v):
        out['warnings'].append(
            'the map uses the Forsaken Kingdom game data (game_data_version 2), which Warcraft III %s does not have' % v
        )
    game = _older_reforged(v)
    if game:
        _plan_w3i_reforged(model, game, out)
    if src >= 31 and any(p.get('enemy_low') or p.get('enemy_high') for p in model.get('players') or []):
        out['warnings'].append('the enemy priorities of the players are dropped (the format has no place for them)')
    return out


def _plan_w3i_reforged(model, game, out):
    out.setdefault('set', {})
    ts = (model.get('tileset') or b'').decode('latin-1')
    if ts and ts not in game['tilesets']:
        out['refusals'].append(
            'the map uses the tileset %r, which Warcraft III %s does not have' % (ts, game['version'])
        )
    modes = model.get('supported_modes')
    if isinstance(modes, int) and modes & ~3:
        out['set']['supported_modes'] = (modes & 3) or 3
    weather = model.get('weather') or b'\0\0\0\0'
    if weather.strip(b'\0') and weather.decode('latin-1') not in game['weather']:
        out['set']['weather'] = b'\0\0\0\0'
        out['warnings'].append('the map weather %s is not in Warcraft III %s: the map has none there'
                               % (weather.decode('latin-1'), game['version']))
    light = (model.get('light_env') or b'\0').decode('latin-1')
    if light.strip('\0') and light not in game['tilesets']:
        out['set']['light_env'] = b'\0'
        out['warnings'].append('the map lighting of tileset %r is not in Warcraft III %s: the default one is used'
                               % (light, game['version']))
    bg = model.get('loading_bg')
    if isinstance(bg, int) and bg >= 0 and str(bg) not in game['loading_screens']:
        out['set']['loading_bg'] = -1
        out['warnings'].append('the loading screen %d is not in Warcraft III %s: the default one is shown'
                               % (bg, game['version']))


def downgrade_w3i(data, version='1.29.2'):
    from doctor.data import w3i
    model = w3i.parse(data)
    if w3i.write(model) != data:
        raise ValueError('the map info does not read back exactly: it is left as it is')
    plan = plan_w3i(model, version)
    if plan['refusals']:
        raise Refused('; '.join(plan['refusals']))
    if model['version'] <= plan['target']:
        return data, plan
    for fmt, bits in FLAGS_BY_FORMAT:
        for b in bits:
            model['flags'] &= ~b
    model['editor_version'] = editor_number(version)
    v = _target(version)[0]
    if v in REFORGED_OLD_SAVE:
        model['game_version'] = list(REFORGED_OLD_SAVE[v][1])
        model.update(plan.get('set') or {})
    new = w3i.write(model, version=plan['target'])
    back = w3i.parse(new)
    if w3i.write(back) != new or back['version'] != plan['target']:
        raise ValueError('the downgraded map info does not read back')
    for k in ('name', 'author', 'description', 'width', 'height', 'tileset', 'forces', 'upgrades', 'techs'):
        if back.get(k) != model.get(k):
            raise ValueError('the field %s changed in the downgrade' % k)
    return new, plan


def remaining(path, version):
    from doctor.fix import unprotect
    from doctor.fix import editor_version
    a = unprotect._open(path)

    def read(n):
        try:
            return unprotect._read(a, n)
        except BaseException as e:
            if isinstance(e, KeyboardInterrupt):
                raise
            return None
    c = editor_version.check_map(version, read)
    return c['blocks'] + c['warnings']


def fix_w3i(path_in, path_out, version='1.29.2', progress=None):
    from doctor.fix import unprotect
    from doctor.fix import map_rewrite
    p = progress or (lambda *_a, **_k: None)
    rep = {'state': 'failed', 'lines': [], 'plan': None, 'remaining': []}

    def stop(state, why):
        rep['state'] = state
        rep['lines'] = [('bad' if state == 'failed' else 'warn', why)]
        return rep

    if os.path.abspath(path_in) == os.path.abspath(path_out):
        return stop('failed', 'The output must be a new file.')
    try:
        v, _lim = _target(version)
    except ValueError as e:
        return stop('refused', str(e))
    p('Reading the map')
    try:
        a = unprotect._open(path_in)
        data = unprotect._read(a, 'war3map.w3i')
    except BaseException as e:
        if isinstance(e, KeyboardInterrupt):
            raise
        return stop('failed', 'The map cannot be read (%s).' % unprotect._error(e))
    if not data:
        return stop('refused', 'The map has no war3map.w3i.')
    lua = unprotect._read(a, 'war3map.lua') is not None and unprotect._read(a, 'war3map.j') is None \
        and unprotect._read(a, 'Scripts\\war3map.j') is None
    try:
        from doctor.data import w3i
        model = w3i.parse(data)
    except Exception as e:
        return stop('refused', 'The map info does not read (%s).' % str(e)[:80])
    plan = plan_w3i(model, v)
    rep['plan'] = plan
    if lua and not any('Lua' in r for r in plan['refusals']):
        plan['refusals'].append('the map script is Lua (war3map.lua): Warcraft III %s does not run Lua' % v)
    if plan['refusals']:
        return stop('refused', 'Not taken to Warcraft III %s: %s.' % (v, '; '.join(plan['refusals'])))
    if model['version'] <= plan['target']:
        return stop('nothing_to_do', 'The map info is already in format %d, which Warcraft III %s reads.'
                    % (model['version'], v))
    p('Writing the map info')
    try:
        new, plan = downgrade_w3i(data, v)
        w = map_rewrite.write(path_in, path_out, [('war3map.w3i', new)], p)
    except Refused as e:
        return stop('refused', 'Not taken to Warcraft III %s: %s.' % (v, e))
    except Exception as e:
        return stop('failed', 'The map could not be written (%s).' % unprotect._error(e))
    rep.update(state='done', file=path_out, same_files=w['same_files'], plan=plan)
    rep['lines'] = [('title', 'Map info taken to Warcraft III %s' % v),
                    ('good', 'war3map.w3i: format %d -> %d.' % (plan['from'], plan['target']))]
    if plan['cleared_flags']:
        rep['lines'].append(('info', 'Flags cleared: %s.' % ', '.join(plan['cleared_flags'])))
    if plan['dropped']:
        rep['lines'].append(
            ('info', 'Fields the old format has no place for: %s.' % ', '.join(sorted(set(plan['dropped']))))
        )
    rep['lines'] += [('warn', w_) for w_ in plan['warnings']]
    try:
        rep['remaining'] = remaining(path_out, v)
    except Exception:
        rep['remaining'] = []
    rep['lines'] += [('warn', '%s: %s' % (c, t)) for c, t in rep['remaining']]
    rep['lines'].append(('warn', 'Only the map info was converted. Not converted: %s.' % '; '.join(REMAINING)))
    return rep


OBJECT_KINDS = ('w3u', 'w3t', 'w3a', 'w3b', 'w3d', 'w3h', 'w3q')
LEVEL_KINDS = ('w3a', 'w3d', 'w3q')


def _mod_key(d, start, levels):
    return d[start:start + 4] + (d[start + 8:start + 16] if levels else b'')


def _chosen_sets(sets):
    zero = [s for s in sets if not s[0]]
    chosen = zero or sets[:1]
    return chosen, sorted(set(s[0] for s in sets if s not in chosen and s[0]))


def merge_object_file(classic, skin, levels):
    from doctor.data import skin_split
    rows = collections.OrderedDict()
    info = {'objects': 0, 'merged': 0, 'added': 0, 'flags_left': []}
    for data, from_skin in ((classic, False), (skin, True)):
        if not data:
            continue
        version, objects, end = skin_split._parse(data, levels)
        if end != len(data) and data[end:].strip(b'\0'):
            raise ValueError('the object file does not close (%d of %d bytes)' % (end, len(data)))
        for table, ids, sets in objects:
            chosen, left = _chosen_sets(sets) if version >= 3 else (sets, [])
            info['flags_left'] += left
            key = (table, ids)
            if key not in rows:
                rows[key] = collections.OrderedDict()
                if from_skin:
                    info['added'] += 1
            elif from_skin:
                info['merged'] += 1
            for _flag, mods in chosen:
                for _f, s, e in mods:
                    rows[key][_mod_key(data, s, levels)] = data[s:e]
    out = [struct.pack('<I', 2)]
    for table in (0, 1):
        group = [(ids, mods) for (t, ids), mods in rows.items() if t == table]
        out.append(struct.pack('<I', len(group)))
        for ids, mods in group:
            out.append(ids + struct.pack('<I', len(mods)))
            out.extend(mods.values())
    info['objects'] = len(rows)
    info['flags_left'] = sorted(set(info['flags_left']))
    return b''.join(out), info


def _object_content(data, levels):
    from doctor.data import skin_split
    return skin_split._content(data, levels)


def downgrade_objects(files):
    out, report = {}, {}
    low = dict((n.lower(), n) for n in files)
    for kind in OBJECT_KINDS:
        cn, sn = low.get('war3map.' + kind), low.get('war3mapskin.' + kind)
        classic, skin = files.get(cn) if cn else None, files.get(sn) if sn else None
        if not classic and not skin:
            continue
        if not skin and struct.unpack_from('<I', classic, 0)[0] <= 2:
            continue
        levels = kind in LEVEL_KINDS
        new, info = merge_object_file(classic, skin, levels)
        got = _object_content(new, levels)
        want = {}
        for data in (classic, skin):
            if not data:
                continue
            m2, _i = merge_object_file(data, None, levels)
            for ids, c in _object_content(m2, levels).items():
                cur = want.setdefault(ids, {})
                for (field, level, value), _n in c.items():
                    cur[(field, level)] = value
        for ids, fields in want.items():
            have = dict(((f, lv), v) for (f, lv, v), _n in got.get(ids, {}).items())
            if have != fields:
                raise ValueError('the merged %s does not carry the fields of %r' % (kind, ids))
        out['war3map.' + kind if not cn else cn] = new
        if sn:
            out[sn] = None
        report[kind] = info
    return out, report


OBJECT_KIND_OF = {'w3u': 'unit', 'w3t': 'item', 'w3a': 'ability', 'w3h': 'buff', 'w3b': 'destructable',
                  'w3d': 'doodad', 'w3q': 'upgrade'}
FIELD_KIND_OF = dict(OBJECT_KIND_OF, w3t='unit')


def downgrade_objects_reforged(files, game):
    from doctor.data import skin_split
    out, report = {}, {}
    for name, data in sorted(files.items()):
        ext = name.lower().rsplit('.', 1)[-1]
        if not data or ext not in OBJECT_KIND_OF:
            continue
        levels = ext in LEVEL_KINDS
        version, objects, end = skin_split._parse(data, levels)
        if end != len(data) and data[end:].strip(b'\0'):
            raise ValueError('%s does not close (%d of %d bytes)' % (name, end, len(data)))
        newer = game['newer']['fields'].get(FIELD_KIND_OF[ext], frozenset())
        bases = game['objects'].get(OBJECT_KIND_OF[ext], frozenset())
        gone = collections.Counter(f for _t, _ids, sets in objects for _fl, mods in sets for f, _s, _e in mods
                                   if f in newer)
        unknown = [(ids[4:8].decode('latin-1') if table else '', ids[:4].decode('latin-1'))
                   for table, ids, _sets in objects if ids[:4].decode('latin-1') not in bases]
        report[name] = {'fields': dict(gone), 'unknown_bases': unknown, 'objects': len(objects)}
        if not gone:
            continue
        new = skin_split._write(version, objects, data, lambda f: f not in newer)
        v2, back, end2 = skin_split._parse(new, levels)
        if end2 != len(new) or v2 != version or len(back) != len(objects) or any(
                (t, i) != (t2, i2) or len(s) != len(s2) or any(
                    len(m2) != len([f for f, _a, _b in m if f not in newer]) for (_x, m), (_y, m2) in zip(s, s2))
                for (t, i, s), (t2, i2, s2) in zip(objects, back)):
            raise ValueError('%s without the fields of the newer game does not read back' % name)
        out[name] = new
    return out, report


def reforged_content(read, game, script=None):
    import re
    out = {'doodads': [], 'units': [], 'terrain': [], 'files': [], 'weather': []}
    own = set()
    for ext in OBJECT_KIND_OF:
        d = read('war3map.' + ext)
        if not d:
            continue
        try:
            from doctor.data import skin_split
            _v, objects, _e = skin_split._parse(d, ext in LEVEL_KINDS)
            own.update(ids[4:8].decode('latin-1') for table, ids, _s in objects if table)
        except Exception:
            pass
    known = set(game['objects'].get('doodad', ())) | set(game['objects'].get('destructable', ())) | own
    d = read('war3map.doo')
    if d:
        try:
            from doctor.fix import doodads
            dd = doodads.read_data(d)
            if dd['on_close']:
                out['doodads'] = sorted(set(r['id'].decode('latin-1') for r in dd['regs']) - known)
        except Exception:
            pass
    known = set(game['objects'].get('unit', ())) | set(game['objects'].get('item', ())) | own
    d = read('war3mapUnits.doo')
    if d:
        try:
            from doctor.fix import inflated_counts
            uu = inflated_counts.read_units_doo(d)
            ids = set(r['ident'].decode('latin-1') for r in uu.get('regs') or [])
            out['units'] = sorted(i for i in ids - known if i != 'sloc' and not i.startswith(('YY', 'iDNR')))
        except Exception:
            pass
    d = read('war3map.w3e')
    if d and d[:4] == b'W3E!':
        try:
            nt = struct.unpack_from('<I', d, 13)[0]
            tiles = [d[17 + 4 * k:21 + 4 * k].decode('latin-1') for k in range(nt)]
            q = 17 + 4 * nt
            nc = struct.unpack_from('<I', d, q)[0]
            cliffs = [d[q + 4 + 4 * k:q + 8 + 4 * k].decode('latin-1') for k in range(nc)]
            out['terrain'] = sorted(set(t for t in tiles if t not in game['terrain']) |
                                    set(c for c in cliffs if c not in game['cliffs']))
        except (struct.error, UnicodeDecodeError):
            pass
    from doctor.data import wc3_versions
    rx = re.compile(rb'[A-Za-z0-9_ \-\\/.]{3,200}?\.(?:mdx|mdl|blp|dds|tga|png|wav|flac|ogg|mp3)\b', re.I)
    inside = set()
    lst = read('(listfile)') or b''
    for n in re.split(rb'[\r\n]+', lst):
        k, s = wc3_versions.stem_kind(n.decode('utf-8', 'replace'))
        if k:
            inside.add((k, s))
    cited = set()
    texts = [script.encode('utf-8', 'surrogateescape') if isinstance(script, str) else (script or b'')]
    texts += [read(n) or b'' for n in ['war3map.w3i'] + ['war3map.' + e for e in OBJECT_KIND_OF] +
              ['war3mapSkin.' + e for e in OBJECT_KIND_OF]]
    for t in texts:
        for m in rx.finditer(t):
            p = m.group(0).decode('latin-1').strip().replace('\\\\', '\\')
            k, s = wc3_versions.stem_kind(p)
            if k and (k, s) not in inside and s in game['newer']['stems'].get(k, ()):
                cited.add(p)
    out['files'] = sorted(cited, key=str.lower)
    if script:
        txt = script if isinstance(script, str) else script.decode('latin-1')
        ids = set(
            re.findall(
                r"AddWeatherEffect\s*\([^,()]*(?:\([^()]*\))?[^,()]*,\s*(?:'(\w{4})'|FourCC\(\s*\"(\w{4})\"\s*\))", txt
            )
        )
        out['weather'] = sorted(set(a or b for a, b in ids) - set(game['weather']))
    return out


DOO_CLASSIC = (8, 11)


def downgrade_doo(data, keep_skin=False):
    from doctor.fix import doodads
    d = doodads.read_data(data)
    if not d['on_close']:
        raise ValueError('war3map.doo does not close in any known layout')
    ver, sub, skin = d['version_num'], d['subversion'], d['skin']
    info = {'from': (ver, sub, skin), 'records': len(d['regs'])}
    keep = bool(keep_skin and skin)
    if ver <= 8 and (keep or not skin):
        return data, info
    if ver < 8:
        raise ValueError('war3map.doo version %d with a skin field: not a layout this knows' % ver)
    out = [data[:4], struct.pack('<iiI', DOO_CLASSIC[0], DOO_CLASSIC[1], len(d['regs']))]
    for r in d['regs']:
        b = data[r['begin']:r['begin'] + r['sz']]
        p = 36
        head = b[:40] if keep else b[:36]
        p += 4 if skin else 0
        p += 4 if ver >= 12 else 0
        flags_life = b[p:p + 2]
        p += 2
        start = p
        sets = struct.unpack_from('<I', b, p + 4)[0]
        p += 8
        for _k in range(sets):
            p += 4 + 8 * struct.unpack_from('<I', b, p)[0]
        items = b[start:p]
        p += 4 if ver >= 13 else 0
        editor_id = b[p:p + 4]
        out.append(head + flags_life + items + editor_id)
    out.append(d['tail'])
    new = b''.join(out)
    back = doodads.read_data(new, skin=keep)
    if not back['on_close'] or len(back['regs']) != len(d['regs']) or \
            [x['id'] for x in back['regs']] != [x['id'] for x in d['regs']] or \
            [x['editor_id'] for x in back['regs']] != [x['editor_id'] for x in d['regs']]:
        raise ValueError('the classic war3map.doo does not read back with the same doodads')
    return new, info


def downgrade_w3e(data):
    if data[:4] != b'W3E!':
        raise ValueError('war3map.w3e without W3E!')
    v = struct.unpack_from('<i', data, 4)[0]
    if v <= 11:
        return data, {'from': v, 'points': 0}
    if v != 12:
        raise ValueError('war3map.w3e version %d is not one this knows' % v)
    p = 13
    nt = struct.unpack_from('<I', data, p)[0]
    p += 4 + 4 * nt
    nc = struct.unpack_from('<I', data, p)[0]
    p += 4 + 4 * nc
    w, h = struct.unpack_from('<II', data, p)
    p += 16
    n = w * h
    if len(data) - p != 8 * n:
        raise ValueError('war3map.w3e version 12: %d bytes after the header for %dx%d points of 8 bytes'
                         % (len(data) - p, w, h))
    pts = struct.unpack_from('<' + 'hHHBB' * n, data, p)
    out = bytearray(data[:4] + struct.pack('<i', 11) + data[8:p])
    pack = struct.Struct('<hHBBB').pack
    for i in range(0, 5 * n, 5):
        tf = pts[i + 2]
        tex, flags = tf & 0x3F, tf >> 6
        if tex > 15 or flags > 15:
            raise ValueError('war3map.w3e: a point with ground texture %d and flags %d (version 11 holds 0 to 15)'
                             % (tex, flags))
        out += pack(pts[i], pts[i + 1], (flags << 4) | tex, pts[i + 3], pts[i + 4])
    return bytes(out), {'from': 12, 'points': n}


def _known_function(td, f):
    from doctor.triggers import wtg
    try:
        td.arity(wtg.KINDS[f.kind], f.name)
    except Exception:
        return False
    for p in f.params:
        while p is not None:
            if p.kind == wtg.PRESET and p.value and p.value not in td.presets:
                return False
            p = p.index
    return True


class KnownTriggers(object):
    def __init__(self, td, known):
        self.td, self.known = td, known
        self.presets = dict((k, v) for k, v in td.presets.items() if k in known['preset'])
        self.types = dict((k, v) for k, v in td.types.items() if k in known['type'])

    def arity(self, kind, name):
        from doctor.triggers import triggerdata
        k = triggerdata._kind_name(kind)
        if name not in self.known.get(k, ()):
            raise triggerdata.UnknownFunction(k, name)
        return self.td.arity(kind, name)

    def __getattr__(self, name):
        if name in ('td', 'known'):
            raise AttributeError(name)
        return getattr(self.td, name)


def downgrade_triggers(wtg_data, wct_data, version):
    from doctor.triggers import editor_render
    from doctor.fix import editor_version
    from doctor.triggers import gui_render
    from doctor.triggers import wtg
    from doctor.triggers import triggerdata
    td_new, _how = wtg.load_td()
    td_new = triggerdata.ScriptFallback(td_new)
    game = _older_reforged(version)
    td_old = KnownTriggers(td_new, game['triggers']) if game else editor_version.trigger_data(version)
    try:
        mt = wtg.read_wtg(wtg_data, td_new)
        ct = wtg.read_wct(wct_data) if wct_data else None
    except Exception as e:
        raise ValueError('the triggers do not read (%s)' % str(e)[:120])
    if (
        game
        and all(
            t.is_text or t.is_comment or all(_known_function(td_old, f) for f in wtg.iter_functions(t.functions))
            for t in mt.triggers
        )
        and all(v.type in td_old.types for v in mt.variables)
    ):
        return None
    texts = wtg.trigger_texts(mt, ct) if ct is not None else [None] * len(mt.triggers)
    if mt.sub_version is not None:
        new, texts = editor_render._classico(mt, texts)
    else:
        new = wtg.to_classic(mt)
    info = {'from_131': mt.sub_version is not None, 'to_text': [], 'var_types': {}}
    for i, t in enumerate(new.triggers):
        if t.is_text or t.is_comment or all(_known_function(td_old, f) for f in wtg.iter_functions(t.functions)):
            continue
        texts[i] = gui_render.render_trigger(t, td_new, new)
        t.is_text, t.functions = 1, []
        info['to_text'].append(t.name)
    for v in new.variables:
        if v.type not in td_old.types:
            info['var_types'][v.name] = v.type
            v.type = 'handle'
    if not info['from_131'] and not info['to_text'] and not info['var_types']:
        return None
    wtg_b = wtg.write_wtg(new, td_old)
    wct_b = wtg.write_wct(wtg.CustomText(False, ct.comment if ct else '', ct.header if ct else None, texts,
                                         ct.version if ct else 1))
    back = wtg.read_wtg(wtg_b, td_old)
    if len(back.triggers) != len(new.triggers) or len(wtg.read_wct(wct_b).texts) != len(back.triggers):
        raise ValueError('the classic triggers do not read back with the TriggerData of %s' % version)
    return wtg_b, wct_b, info


NEUTRAL_24_TO_12 = {24: 12, 25: 13, 26: 14, 27: 15}


def _unit_811(b, d, owners, keep_skin=False):
    p = d['p']
    skin = [d['skin_id']] if keep_skin and d.get('skin_id') else []
    out = (
        [b[p : p + 36]]
        + skin
        + [
            bytes((d['flags'],)),
            struct.pack('<hi', owners.get(d['owner'], d['owner']), d['uprooted']),
            struct.pack('<iii', d['hp'], d['mana'], d['itp']),
            struct.pack('<i', len(d['set_items'])),
        ]
    )
    for c in d['set_items']:
        out.append(struct.pack('<i', len(c)) + b''.join(iid + struct.pack('<i', ch) for iid, ch in c))
    out.append(struct.pack('<ifi', d['gold'], d['acq'], d['level']))
    out.append(struct.pack('<3i', *(d['hero_attributes'] or (0, 0, 0))))
    out.append(struct.pack('<i', len(d['inventory'])) + b''.join(struct.pack('<i', s) + iid
                                                                 for s, iid in d['inventory']))
    out.append(struct.pack('<i', len(d['abilities'])) + b''.join(hid + struct.pack('<2i', au, lv)
                                                                 for hid, au, lv in d['abilities']))
    out.append(struct.pack('<i', d['rnd']))
    if d['rnd'] == 0:
        out.append(d['block_entry'][0].to_bytes(3, 'little') + bytes((d['block_entry'][1],)))
    elif d['rnd'] == 1:
        out.append(struct.pack('<2i', *d['block_entry']))
    elif d['rnd'] == 2:
        out.append(
            struct.pack('<i', len(d['block_entry']))
            + b''.join(uid + struct.pack('<i', ch) for uid, ch in d['block_entry'])
        )
    out.append(struct.pack('<3i', d['color'], d['waygate'], d['creation']))
    return b''.join(out)


def downgrade_units(data, neutral_24_to_12=False, keep_skin=False):
    from doctor.fix import inflated_counts
    d = inflated_counts.read_units_doo(data)
    if not d.get('on_close'):
        raise ValueError('war3mapUnits.doo does not close in a known layout')
    owners = NEUTRAL_24_TO_12 if neutral_24_to_12 else {}
    moved = any(r['owner'] in owners for r in d['regs'])
    kept = ('7/9', '8/11', '8/11+skin', '8/9+skin') if keep_skin else ('7/9', '8/11')
    if d['layout'] in kept and not moved:
        return None
    if d['layout'] == '7/9':
        new = bytearray(data)
        for r in d['regs']:
            if r['owner'] in owners:
                struct.pack_into('<h', new, r['p'] + 37, owners[r['owner']])
        new = bytes(new)
    else:
        new = data[:4] + struct.pack('<iiI', 8, 11, len(d['regs'])) + b''.join(_unit_811(data, r, owners, keep_skin)
                                                                                 for r in d['regs'])
    back = inflated_counts.read_units_doo(new)
    if keep_skin and d.get('skin') and not back.get('skin'):
        raise ValueError('the war3mapUnits.doo of %s does not read back with its skin field' % 'the older Reforged')
    if not back.get('on_close') or len(back['regs']) != len(d['regs']) or \
            [r['ident'] for r in back['regs']] != [r['ident'] for r in d['regs']] or \
            [r['xyz'] for r in back['regs']] != [r['xyz'] for r in d['regs']] or \
            [r['creation'] for r in back['regs']] != [r['creation'] for r in d['regs']]:
        raise ValueError('the classic war3mapUnits.doo does not read back with the same units')
    return new, {'from': d['layout'], 'records': len(d['regs'])}


def downgrade_editor_files(files, neutral_24_to_12=False, reforged=False):
    from doctor.fix import inflated_counts
    from doctor.triggers import editor_render
    out, done, left = {}, {}, {}
    low = dict((n.lower(), n) for n in files)
    n = low.get('war3map.w3s')
    if n and files[n] and not reforged:
        try:
            v, sounds = editor_render.read_w3s(files[n])
            if v > 1:
                out[n] = editor_render.write_w3s(1, sounds)
                done[n] = 'version %d -> 1 (%d sounds)' % (v, len(sounds))
        except Exception as e:
            left[n] = str(e)[:100]
    n = low.get('war3map.w3c')
    if n and files[n]:
        try:
            d = inflated_counts.read_w3c(files[n])
            if d is None or d['remaining'] != 0 or len(d['regs']) != d['declared']:
                raise ValueError('war3map.w3c does not close')
            novos, dof = d.get('layout') or (False, False)
            if reforged and (d['version_num'] != 0 or dof):
                out[n] = inflated_counts.write_w3c(d['regs'], 0, novos, False)
                done[n] = 'version %d -> 0 (%d cameras; the depth of field and the camera type of 3.0 left out)' % (
                    d['version_num'], len(d['regs']))
            elif not reforged and (d['version_num'] != 0 or (novos, dof) != (False, False)):
                out[n] = inflated_counts.write_w3c(d['regs'], 0, False, False)
                done[n] = '%s (%d cameras)' % ('version %d -> 0' % d['version_num'] if d['version_num'] else
                                               'without the 1.31 local angles', len(d['regs']))
        except Exception as e:
            left[n] = str(e)[:100]
    n = low.get('war3map.w3r')
    if n and files[n]:
        try:
            d = inflated_counts.read_w3r(files[n])
            if d['remaining'] != 0 or len(d['regs']) != d['declared']:
                raise ValueError('war3map.w3r does not close')
            if d['version_num'] > 5:
                out[n] = inflated_counts.write_w3r(d['regs'], 5)
                done[n] = 'version %d -> 5 (%d regions)' % (d['version_num'], len(d['regs']))
        except Exception as e:
            left[n] = str(e)[:100]
    n = low.get('war3mapunits.doo')
    if n and files[n]:
        try:
            r = downgrade_units(files[n], neutral_24_to_12, keep_skin=reforged)
            if r:
                out[n] = r[0]
                done[n] = 'layout %s -> 8/11%s (%d units)' % (r[1]['from'], ' with the skin field' if reforged else '',
                                                              r[1]['records'])
        except Exception as e:
            left[n] = str(e)[:100]
    return out, done, left


def media_scan(path, version, progress=None):
    from doctor.models import model_check
    v, _lim = _target(version)
    k = _key(v)
    p = progress or (lambda *_a, **_k: None)
    out = {'models': [], 'dds': [], 'flac': [], 'ogg': [], 'names': 0, 'error': None}
    p('Reading the map')
    a, err = model_check._open(path)
    if a is None:
        out['error'] = err
        return out
    p('Finding the file names')
    names = model_check._names(a)
    out['names'] = len(names)
    seen = set()
    top = MODEL_MAX_REFORGED.get(v)
    for n in names:
        ext = os.path.splitext(n)[1].lower()
        for kind, field in (('.dds', 'dds'), ('.flac', 'flac'), ('.ogg', 'ogg')):
            if ext == kind and (k < FIRST_PATCH[field] or (top and field == 'ogg')) and n.upper() not in seen:
                seen.add(n.upper())
                out[field].append(n)
    if k < FIRST_PATCH['model'] or top:
        for name, _bi, data in model_check._models(a, names, p):
            if not name.lower().endswith(MODEL_EXTS) or not data:
                continue
            mv = model_check.model_version(data)
            if mv is not None and mv > (top or MODEL_MAX_OLD):
                out['models'].append((name, mv))
    return out


def _item(code, severity, text, fix, **data):
    out = {'code': code, 'severity': severity, 'text': text, 'fix': fix}
    if data:
        out['data'] = data
    return out


def media_items(path, version, progress=None):
    v, _lim = _target(version)
    s = media_scan(path, v, progress)
    label = 'Warcraft III %s' % v
    items = []
    top = MODEL_MAX_REFORGED.get(v)
    if top:
        if s['models']:
            vers = sorted({mv for _n, mv in s['models']})
            items.append(_item('media_model_version', 'warning',
                               '%d models are version %s; the models of %s itself are version %d, and that it loads a '
                               'newer version is not proven.' % (len(s['models']), ', '.join(str(x) for x in vers),
                                                                 label, top), 'none',
                               models=[n for n, _v in s['models']][:30], versions=vers))
        if s['ogg']:
            items.append(
                _item(
                    'media_ogg',
                    'warning',
                    '%d OGG sounds: %s has no OGG sound of its own (3.0 brought them), '
                    'and that it plays them is not proven.' % (len(s['ogg']), label),
                    'none',
                    files=s['ogg'][:30],
                )
            )
        return items
    if s['models']:
        vers = sorted({mv for _n, mv in s['models']})
        items.append(
            _item(
                'media_model_version',
                'warning',
                '%d models are version %s; %s loads model version %d (the HD models of 1.32 and later are 900 '
                'and above, reported not to load in older games).'
                % (len(s['models']), ', '.join(str(x) for x in vers), label, MODEL_MAX_OLD),
                'none',
                models=[n for n, _v in s['models']][:30],
                versions=vers,
            )
        )
    if s['dds']:
        items.append(
            _item(
                'media_dds',
                'warning',
                '%d DDS textures: %s is reported not to load DDS images (they start with 1.32).'
                % (len(s['dds']), label),
                'none',
                files=s['dds'][:30],
            )
        )
    if s['flac']:
        items.append(
            _item(
                'media_flac',
                'warning',
                '%d FLAC sounds: %s is reported not to play FLAC (it starts with 1.32).' % (len(s['flac']), label),
                'none',
                files=s['flac'][:30],
            )
        )
    if s['ogg']:
        items.append(
            _item(
                'media_ogg',
                'warning',
                '%d OGG sounds: %s is reported not to play OGG (it starts with 1.30; '
                'use MP3 or WAV).' % (len(s['ogg']), label),
                'none',
                files=s['ogg'][:30],
            )
        )
    return items
