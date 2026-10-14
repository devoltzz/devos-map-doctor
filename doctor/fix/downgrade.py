# Writes the map info of an older game version and lists the media that version does not load.
import os



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
        raise ValueError('the target has to be a classic game (1.24 to 1.29): %r' % (version,))
    return v, wc3_versions.limits(v)


def editor_number(version):
    from doctor.fix import game_builds
    from doctor.data import wc3_versions
    v = wc3_versions.normalize(version)
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
    if model.get('script_language') == 1:
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
    if model.get('game_data_version') == 2:
        out['warnings'].append(
            'the map uses the Forsaken Kingdom game data (game_data_version 2), which Warcraft III %s does not have' % v
        )
    if src >= 31 and any(p.get('enemy_low') or p.get('enemy_high') for p in model.get('players') or []):
        out['warnings'].append('the enemy priorities of the players are dropped (the format has no place for them)')
    return out


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
    for n in names:
        ext = os.path.splitext(n)[1].lower()
        for kind, field in (('.dds', 'dds'), ('.flac', 'flac'), ('.ogg', 'ogg')):
            if ext == kind and k < FIRST_PATCH[field] and n.upper() not in seen:
                seen.add(n.upper())
                out[field].append(n)
    if k < FIRST_PATCH['model']:
        for name, _bi, data in model_check._models(a, names, p):
            if not name.lower().endswith(MODEL_EXTS) or not data:
                continue
            mv = model_check.model_version(data)
            if mv is not None and mv > MODEL_MAX_OLD:
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
