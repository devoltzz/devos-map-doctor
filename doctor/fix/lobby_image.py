# Puts a picture of your own in the lobby of a Reforged map, the minimap kept in game.
import os
import re


PREVIEW = 'war3mapPreview.blp'
MINIMAP = 'war3mapMap.blp'
INGAME = 'war3mapMap_ingame.blp'
NATIVE = 'BlzChangeMinimapTerrainTex'
SIDES = (32, 1024)
QUALITY = 50
CALL_JASS = 'call %s("%s")' % (NATIVE, INGAME)
CALL_LUA = '%s("%s")' % (NATIVE, INGAME)
MARK = 'Devo lobby image'
RX_CALL = re.compile(r'%s\s*\(\s*"(?:war3mapMap_ingame\.blp)"' % NATIVE, re.I)


def _nothing(*_a, **_k):
    pass


def _old_game(path):
    try:
        from doctor.data import wc3_versions
        d = wc3_versions.detect(path)
    except Exception:
        return None
    if d and d.get('range') in ('pre-1.24', '1.24-1.28'):
        return ('this map was made for Warcraft III %s, which has no %s (it starts with patch 1.29)'
                % (d['range'], NATIVE))
    return None


def _blp_size(data):
    from doctor.models import blpread
    info = blpread.header_bytes(data)
    return info['map_width'], info['map_height']


def _blp_from_image(path):
    with open(path, 'rb') as f:
        raw = f.read()
    if raw[:4] in (b'BLP1', b'BLP2', b'BLX1'):
        w, h = _blp_size(raw)
        if raw[:4] == b'BLX1':
            raise ValueError('%s is a BLX1 (KK platform) texture: make it a BLP1 first' % os.path.basename(path))
        return raw, (w, h)
    try:
        from PIL import Image
        im = Image.open(path)
        im.load()
    except Exception as e:
        raise ValueError('%s is not an image the Doctor reads (%s)' % (os.path.basename(path), str(e)[:60]))
    w, h = im.size
    _check_size(w, h, os.path.basename(path))
    import tempfile
    from doctor.models import blpwrite
    fd, tmp = tempfile.mkstemp(suffix='.blp', prefix='lobby_')
    os.close(fd)
    try:
        blpwrite.save_blp(im, tmp, QUALITY, alpha_bits=0, mipmaps=True)
        with open(tmp, 'rb') as f:
            return f.read(), (w, h)
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass


def _check_size(w, h, what):
    lo, hi = SIDES
    if w != h or w & (w - 1) or not lo <= w <= hi:
        raise ValueError(
            '%s is %dx%d: the lobby picture must be square with a side that is a power of two from %d to %d '
            '(the size of the editor\'s minimap)' % (what, w, h, lo, hi)
        )


def _script(path):
    from doctor.fix import single_player
    a, sc, _strings = single_player.read_map(path)
    return a, sc


def scan(path):
    from doctor.fix import unprotect
    out = {'state': 'refused', 'source': None, 'minimap': None, 'language': None, 'why': None}
    try:
        a, sc = _script(path)
    except BaseException as e:
        if isinstance(e, KeyboardInterrupt):
            raise
        out['why'] = 'The map cannot be read (%s).' % unprotect._error(e)
        return out
    out['language'] = sc['language']
    if sc['language'] not in ('jass', 'lua') or sc['compiled'] or sc['bytes'] is None:
        out['why'] = (
            'The script is compiled by the KK platform: port the map first.'
            if sc['compiled']
            else 'The script is %s: only JASS and Lua scripts can take the call.' % (sc['language'] or 'unreadable')
        )
        return out
    old = _old_game(path)
    if old:
        out['why'] = old[0].upper() + old[1:] + '.'
        return out
    mini = unprotect._read(a, MINIMAP)
    prev = unprotect._read(a, PREVIEW)
    ingame = unprotect._read(a, INGAME)
    text = sc['bytes'].decode('utf-8', 'surrogateescape')
    if sc['language'] == 'lua' and '__ydwe' in text:
        out['why'] = (
            'The map is a KK map ported by the Doctor\'s Lua route: it starts its own main inside the port\'s '
            'runtime, so a call added after it may run too early. Edit the original map before the port.'
        )
        return out
    called = bool(RX_CALL.search(text))
    out['minimap'] = _blp_size(mini) if mini else None
    out['source'] = {'name': PREVIEW, 'size': _blp_size(prev)} if prev else None
    if ingame is not None and called:
        out['state'] = 'applied'
        out['why'] = 'The lobby image is already set (%s keeps the minimap, the script calls %s).' % (INGAME, NATIVE)
        return out
    if mini is None:
        out['why'] = 'The map has no %s: there is no minimap to keep for the game.' % MINIMAP
        return out
    if prev is None:
        out['state'] = 'nothing_to_do'
        out['why'] = 'The map has no %s (import the picture under that name in the editor, or give an image).' % PREVIEW
        return out
    out['state'] = 'ready'
    return out


def _jass_edit(text):
    from doctor.script import jass_ast
    from doctor.fix import map_rewrite
    tree = jass_ast.parse(text)
    return map_rewrite.insert(text, tree, main_end=(CALL_JASS + '  // ' + MARK,))


def _lua_edit(text):
    nl = '\r\n' if text.count('\r\n') * 2 > text.count('\n') else '\n'
    tail = ('-- %s: the real minimap back in game' % MARK, 'do', '  local map_main = main', '  function main()',
            '    if map_main then map_main() end', '    ' + CALL_LUA, '  end', 'end')
    new = text + ('' if text.endswith(('\n', '\r')) else nl) + nl.join(tail) + nl
    from doctor.script import lua_ast
    try:
        lua_ast.parse(new)
    except lua_ast.LuaSyntaxError:
        raise ValueError('the Lua script ends with a return, so a call cannot be added after it')
    return new


def fix(path_in, path_out, progress=None, image=None):
    from doctor.fix import unprotect
    from doctor.fix import map_rewrite
    p = progress or _nothing
    rep = {'state': 'failed', 'lines': [], 'source': None, 'size': None}

    def stop(state, why):
        rep['state'] = state
        rep['lines'] = [('bad' if state == 'failed' else 'warn', why)]
        return rep

    if os.path.abspath(path_in) == os.path.abspath(path_out):
        return stop('failed', 'The output must be a new file.')
    p('Reading the map')
    s = scan(path_in)
    if s['state'] == 'refused':
        return stop('refused', s['why'])
    if s['state'] == 'applied' and not image:
        return stop('nothing_to_do', s['why'])
    try:
        a, sc = _script(path_in)
    except BaseException as e:
        if isinstance(e, KeyboardInterrupt):
            raise
        return stop('failed', 'The map cannot be read (%s).' % unprotect._error(e))
    mini = unprotect._read(a, MINIMAP)
    files = []
    if image:
        try:
            blp, size = _blp_from_image(image)
        except (ValueError, OSError) as e:
            return stop('refused', str(e))
        rep['source'] = os.path.basename(image)
    else:
        if s['state'] != 'ready':
            return stop('nothing_to_do', s['why'])
        blp = unprotect._read(a, PREVIEW)
        try:
            size = _blp_size(blp)
            _check_size(size[0], size[1], PREVIEW)
        except ValueError as e:
            return stop('refused', str(e))
        except Exception as e:
            return stop('refused', '%s is not a BLP the Doctor reads (%s).' % (PREVIEW, str(e)[:60]))
        rep['source'] = PREVIEW
    rep['size'] = size
    text = sc['bytes'].decode('utf-8', 'surrogateescape')
    if s['state'] == 'applied':
        new_bytes = None
    else:
        p('Editing the script')
        try:
            new_text = _lua_edit(text) if sc['language'] == 'lua' else _jass_edit(text)
        except Exception as e:
            return stop('refused', 'The script cannot take the call (%s).' % e)
        new_bytes = new_text.encode('utf-8', 'surrogateescape')
        if sc['language'] == 'jass':
            p('Running pjass')
            gate = map_rewrite.gate(sc['bytes'], new_bytes)
            rep['pjass'] = gate
            if gate['state'] == 'failed':
                return stop('refused', 'pjass does not accept the edited script (%s).' % gate.get('new'))
        files += [(sc['file'], new_bytes)] + [(c, new_bytes) for c in sc['copies']]
        files.append((INGAME, mini))
    files.append((MINIMAP, blp))
    try:
        w = map_rewrite.write(path_in, path_out, files, p)
    except Exception as e:
        return stop('failed', 'The map could not be written (%s).' % unprotect._error(e))
    rep.update(state='done', file=path_out, same_files=w['same_files'], written=[n for n, _b in files])
    rep['lines'] = [('title', 'Lobby image set'),
                    ('good', 'The lobby picture (%s, %dx%d) is now %s.' % (rep['source'], size[0], size[1], MINIMAP))]
    if new_bytes is not None:
        rep['lines'] += [('good', 'The minimap moved to %s and the script calls %s when the map starts, so the game '
                                  'still draws the real minimap.' % (INGAME, NATIVE))]
    rep['lines'] += [('info', 'Do this last: the World Editor writes %s again on every save and does not keep these '
                              'files (they are not in the import list).' % MINIMAP),
                     ('info', 'Not tested in the game: the Doctor never runs it.')]
    return rep
