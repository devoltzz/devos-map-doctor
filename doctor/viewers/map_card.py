# Reads and edits what a map says about itself: name, author, texts, players, teams, images.
import base64
import collections
import copy
import gc
import io
import os
import re
import shutil
import struct
import tempfile
import time

import numpy as np
from PIL import Image

from doctor.models import blpread
from doctor.models import blpwrite
from doctor.fix import unprotect
from doctor.script import jass_ast
from doctor.script import lua_ast
from doctor.models import mdxtex
from doctor.mpq import mpqadd
from doctor.mpq import mpqread
from doctor.mpq import hm3w_names
from doctor.translation import tr_gradient
from doctor.data import w3i


KNOWN_W3I = (18, 25, 28, 31, 33)
RX_WTS = re.compile(rb'^(?:\xef\xbb\xbf)?STRING[ \t]+(\d+)[^\n]*\n(?:[ \t]*(?://[^\n]*)?\r?\n)*[ \t]*\{[^\n]*\n'
                    rb'(.*?)\r?\n?^\}', re.S | re.M)
RX_TRIGSTR = re.compile(r'TRIGSTR_(\d+)\s*$')
RX_COLOR = re.compile(r'\|[cC][0-9a-fA-F]{8}|\|[rRnN]')

TEXTS = (('name', 'name'), ('author', 'author'), ('description', 'description'),
         ('players_suggested', 'players_recommended'), ('loading.title', 'loading_title'),
         ('loading.subtitle', 'loading_subtitle'), ('loading.text', 'loading_text'),
         ('prologue.title', 'prologue_title'), ('prologue.subtitle', 'prologue_subtitle'),
         ('prologue.text', 'prologue_text'))
RACES = {0: 'selectable', 1: 'human', 2: 'orc', 3: 'undead', 4: 'nightelf'}
CONTROLLERS = {0: 'none', 1: 'user', 2: 'computer', 3: 'neutral', 4: 'rescuable'}
FORCE_FLAGS = ((0x01, 'allied'), (0x02, 'allied_victory'), (0x04, 'shared_vision'), (0x10, 'shared_control'),
               (0x20, 'shared_advanced_control'))
MAP_FLAGS = ((0x0001, 'hide_minimap_in_preview'), (0x0002, 'custom_ally_priorities'), (0x0004, 'melee'),
             (0x0010, 'masked_area_partially_visible'), (0x0020, 'fixed_player_settings'), (0x0040, 'custom_forces'),
             (0x0080, 'custom_techtree'), (0x0100, 'custom_abilities'), (0x0200, 'custom_upgrades'),
             (0x0800, 'waves_on_cliff_shores'), (0x1000, 'waves_on_rolling_shores'))

MINIMAP = ('war3mapMap.blp', 'war3mapMap.tga')
PREVIEW = ('war3mapPreview.tga',)
IMAGE_EXTS = ('.blp', '.tga', '.dds')
QUADRANTS = ('TL', 'TR', 'BL', 'BR')
BLP_QUALITY = 50
MINIMAP_SIDES = (32, 1024)
PREVIEW_SIDES = (16, 1024)
JPEG_TOLERANCE = 8.0

RX_CHAT_EVENT = re.compile(r'TriggerRegisterPlayerChatEvent\s*\(')
_LIT = r'"[^"\\]*(?:\\.[^"\\]*)*"'
RX_LIT_DQ = re.compile(_LIT, re.S)
RX_LIT_SQ = re.compile(r"'[^'\\]*(?:\\.[^'\\]*)*'", re.S)
RX_CHAT_AFTER = re.compile(r'GetEventPlayerChatString\(\s*\)\s*(?:==|!=|~=)\s*(' + _LIT + ')')
RX_CHAT_SUBSTRING = re.compile(r'GetEventPlayerChatString\(\s*\)\s*,[^()]*\)\s*(?:==|!=|~=)\s*(' + _LIT + ')')
RX_CHAT_BEFORE = re.compile(r'(' + _LIT + r')\s*(?:==|!=|~=)\s*\Z')
RX_SUBSTRING_BEFORE = re.compile(r'SubString(?:BJ)?\(\s*\Z')
RX_PRELOAD = (('writes', re.compile(r'PreloadGenEnd\s*\(')), ('reads', re.compile(r'Preloader\s*\(')))
RX_PRELOAD_LINE = re.compile(r'Preload\s*\(')
RX_PLATFORM_SAVE = re.compile(r'(DzAPI_Map_(?:SaveServerValue|GetServerValue\w*|Store\w*|GetStored\w*|Global_Store\w*|'
                              r'Global_GetStore\w*|\w*Archive\w*|FlushStoredMission)|'
                              r'JNObject(?:Character|User|Map|Score)\w*|JNRPG\w*)\s*\(')
RX_GAME_CACHE = re.compile(r'InitGameCache(?:BJ)?\s*\(\s*(' + _LIT + ')')
RX_SAVE_GAME_CACHE = re.compile(r'SaveGameCache\s*\(')
RX_MIRROR_CALL = re.compile(r'(?:SetMapName|SetMapDescription|SetPlayerName)\s*\([^()]*(?:\([^()]*\)[^()]*)?\Z')
MIRRORS = (('name', 'SetMapName'), ('description', 'SetMapDescription'))
RX_PATHLIKE = re.compile(r'[\\/]|\.(?:mdx|mdl|blp|tga|dds|wav|mp3|flac|ogg|txt|slk|fdf|toc|j|ai|pld|w3x|w3m)$', re.I)

WRITING = (('han', '㐀-䶿一-鿿豈-﫿', 2), ('kana', '぀-ヿㇰ-ㇿ', 2),
           ('hangul', '가-힯ᄀ-ᇿ㄰-㆏', 2), ('cyrillic', 'Ѐ-ӿ', 1),
           ('greek', 'Ͱ-Ͽ', 1), ('arabic', '؀-ۿ', 1), ('thai', '฀-๿', 1),
           ('latin', 'A-Za-zÀ-ɏ', 1))
RX_WRITING = dict((k, re.compile('[' + cls + ']')) for k, cls, _w in WRITING)
LANGUAGE_OF = {'han': 'Chinese', 'kana': 'Japanese', 'hangul': 'Korean', 'cyrillic': 'Russian', 'greek': 'Greek',
               'arabic': 'Arabic', 'thai': 'Thai'}
STOPWORDS = (('English', 'the and you your to of is for with this are have will'),
             ('Portuguese', 'de que não você para com uma os ao seu sua'),
             ('Spanish', 'de que el los las para con una por tu su'),
             ('German', 'der die das und ist nicht mit sie ein eine'),
             ('French', 'le la les et est pas vous pour avec une des'))
RX_WORD = re.compile(r'[A-Za-zÀ-ɏ]+')
TEXT_PUNCTUATION = frozenset('.,!?\'":;()-+%/|#&' + '。，、！？：；「」『'
                             '』（）【】《》…—～·')


class CardError(Exception):
    def __init__(self, code, message):
        Exception.__init__(self, message)
        self.code = code
        self.message = message


def _nothing(_label):
    pass


def _text(b):
    if b is None:
        return None
    return b.decode('utf-8', 'replace').replace('\r\n', '\n')


def _b64(b):
    return base64.b64encode(bytes(b)).decode('ascii')


def _open(path):
    if not os.path.isfile(path):
        raise CardError('not_found', 'The file does not exist.')
    try:
        return unprotect._open(path)
    except KeyboardInterrupt:
        raise
    except BaseException as e:
        raise CardError('not_a_map', 'The file is not a map that can be read (%s); a protected or damaged map has to '
                                     'be unprotected first.' % (str(e) or type(e).__name__))


def _get(a, name):
    return unprotect._read(a, name)


def wts_strings(wts):
    out = {}
    for m in RX_WTS.finditer(wts or b''):
        out.setdefault(int(m.group(1)), _text(m.group(2)))
    return out


def _eol(raw, default):
    return b'\r\n' if b'\r\n' in raw else (b'\n' if b'\n' in raw else default)


def wts_set(wts, number, text):
    wts = wts or b''
    eol = _eol(wts, b'\r\n')
    lines = text.replace('\r\n', '\n').split('\n')
    if any(x.lstrip().startswith('}') for x in lines):
        raise CardError('bad_text', 'A line of the text cannot start with "}".')
    body = eol.join(x.encode('utf-8') for x in lines)
    found = [m for m in RX_WTS.finditer(wts) if int(m.group(1)) == number]
    if not found:
        sep = b'' if not wts or wts.endswith(b'\n') else eol
        return wts + sep + b'STRING %d' % number + eol + b'{' + eol + body + eol + b'}' + eol + eol
    out = bytearray(wts)
    for m in reversed(found):
        new = body + eol if body and wts[m.end(2):m.end(2) + 1] == b'}' else body
        out[m.start(2):m.end(2)] = new
    return bytes(out)


def _resolve(raw, strings):
    t = _text(raw)
    m = RX_TRIGSTR.match(t or '')
    if not m:
        return t, None
    n = int(m.group(1))
    ref = {'ref': t.strip(), 'number': n, 'found': n in strings}
    return (strings[n] if n in strings else t), ref


def _w3i_model(b):
    if len(b) < 16:
        raise CardError('w3i_unreadable', 'The map info file (war3map.w3i) is too short.')
    v = struct.unpack_from('<i', b, 0)[0]
    if v in KNOWN_W3I:
        try:
            m = w3i.parse(b)
            if w3i.write(m) == b:
                return m, 'exact', []
        except Exception:
            pass
        try:
            m, dev = w3i.parse_tolerant(b)
            return m, 'tolerant', dev
        except Exception:
            raise CardError('w3i_unreadable', 'The map info file (war3map.w3i, version %d) cannot be read.' % v)
    r = w3i.R(b)
    try:
        m = {'version': r.i32(), 'saves': r.i32(), 'editor_version': r.i32()}
        if v >= 28:
            m['game_version'] = [r.i32(), r.i32(), r.i32(), r.i32()]
        for k in ('name', 'author', 'description', 'players_recommended'):
            m[k] = r.s()
    except Exception:
        raise CardError('w3i_unreadable', 'The map info file (war3map.w3i, version %d) cannot be read.' % v)
    return m, 'partial', ['unknown_version']


def _flag_names(value, table):
    return [n for bit, n in table if value & bit]


def _w3i_part(card, m, how, dev, strings):
    trig = {}

    def put(field, raw):
        if raw is None:
            return None
        t, ref = _resolve(raw, strings)
        if ref:
            trig[field] = ref
        return t

    v = m['version']
    for field, key in TEXTS:
        val = put(field, m.get(key))
        if '.' in field:
            sec, sub = field.split('.')
            card.setdefault(sec, {})[sub] = val
        else:
            card[field] = val
    players = m.get('players') or []
    forces = m.get('forces') or []
    numbers = [p['number'] for p in players]
    team = {}
    for i, f in enumerate(forces):
        for num in numbers:
            if 0 <= num < 32 and f['mask'] & (1 << num):
                team.setdefault(num, i)
    card['players'] = [{'index': p['number'], 'name': put('players.%d.name' % p['number'], p['name']),
                        'race': RACES.get(p['race'], p['race']), 'controller': CONTROLLERS.get(p['type'], p['type']),
                        'team': team.get(p['number']), 'fixed_start': bool(p['fixed_start']),
                        'start': [round(p['x'], 2), round(p['y'], 2)]} for p in players]
    card['forces'] = [{'index': i, 'name': put('forces.%d.name' % i, f['name']), 'flags': f['flags'],
                       'flag_names': _flag_names(f['flags'], FORCE_FLAGS),
                       'players': [n for n in numbers if 0 <= n < 32 and f['mask'] & (1 << n)]}
                      for i, f in enumerate(forces)]
    prologue_model = _text(m.get('prologue_model') or b'').strip() if v >= 25 and how != 'partial' else ''
    card.setdefault('prologue', {})['screen'] = {'model': prologue_model or None}
    info = {'version': v, 'editor_version': m.get('editor_version'), 'game_version': m.get('game_version'),
            'script_language': {0: 'jass', 1: 'lua'}.get(m.get('script_language'), m.get('script_language')),
            'read': how, 'deviations': dev, 'editable': how == 'exact', 'why_not': None}
    if how != 'partial':
        info['flags'] = m['flags']
        info['flag_names'] = _flag_names(m['flags'], MAP_FLAGS)
        info['game_data_set'] = m.get('game_data_set')
        info['tail_bytes'] = len(m.get('_tail') or b'')
    if how == 'tolerant':
        info['why_not'] = 'The map info file does not read back exactly (%s): only texts kept in the strings ' \
                          'file can be changed.' % (', '.join(dev) or 'damaged end')
    elif how == 'partial':
        info['why_not'] = 'The map info file is version %d, newer than this reader: only texts kept in the ' \
                          'strings file can be changed.' % v
    card['w3i'] = info
    card['trigstr'] = trig


def _blp_image(data):
    fd, tmp = tempfile.mkstemp(suffix='.blp')
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
        im, info = blpread.le_melhor(tmp)
        return im.convert('RGBA'), info
    finally:
        os.remove(tmp)


def _blp_bytes(im, alpha_bits, mipmaps, extra):
    fd, tmp = tempfile.mkstemp(suffix='.blp')
    os.close(fd)
    try:
        blpwrite.save_blp(im, tmp, quality=BLP_QUALITY, alpha_bits=alpha_bits, mipmaps=mipmaps, extra=extra)
        with open(tmp, 'rb') as f:
            return f.read()
    finally:
        os.remove(tmp)


def _tga_colors(raw, bits, alpha_bits):
    n = raw.shape[0]
    out = np.empty((n, 4), np.uint8)
    if bits in (24, 32):
        out[:, 0], out[:, 1], out[:, 2] = raw[:, 2], raw[:, 1], raw[:, 0]
        out[:, 3] = raw[:, 3] if bits == 32 else 255
        if bits == 32 and not alpha_bits and not out[:, 3].any():
            out[:, 3] = 255
    elif bits in (15, 16):
        v = raw[:, 0].astype(np.uint16) | (raw[:, 1].astype(np.uint16) << 8)
        for k, shift in ((0, 10), (1, 5), (2, 0)):
            out[:, k] = (((v >> shift) & 31) * 255 // 31).astype(np.uint8)
        out[:, 3] = 255 if bits == 15 or not alpha_bits else ((v >> 15) & 1) * 255
    elif bits == 8:
        out[:, 0] = out[:, 1] = out[:, 2] = raw[:, 0]
        out[:, 3] = 255
    else:
        raise ValueError('TGA with %d bits per pixel' % bits)
    return out


def _tga_rle(d, p, need, size):
    out = bytearray()
    end = len(d)
    while len(out) < need and p < end:
        c = d[p]
        p += 1
        k = (c & 0x7F) + 1
        if c & 0x80:
            out += d[p:p + size] * k
            p += size
        else:
            out += d[p:p + k * size]
            p += k * size
    return bytes(out[:need])


def tga_decode(d):
    if len(d) < 18:
        raise ValueError('TGA too short')
    idlen, cmtype, itype, cmfirst, cmlen, cmbits, _x, _y, w, h, bpp, desc = struct.unpack_from('<BBBHHBHHHHBB', d, 0)
    if itype not in (1, 2, 3, 9, 10, 11) or not w or not h or bpp not in (8, 15, 16, 24, 32):
        raise ValueError('TGA type %d, %d bits: not an image this reader knows' % (itype, bpp))
    p = 18 + idlen
    cmap = None
    if cmtype:
        esize = (cmbits + 7) // 8
        cmap = np.frombuffer(d, np.uint8, cmlen * esize, p).reshape(cmlen, esize)
        p += cmlen * esize
    size = (bpp + 7) // 8
    need = w * h * size
    data = _tga_rle(d, p, need, size) if itype >= 9 else d[p:p + need]
    if len(data) < need:
        raise ValueError('TGA cut short')
    raw = np.frombuffer(data, np.uint8).reshape(w * h, size)
    abits = desc & 0x0F
    if itype in (1, 9):
        if cmap is None:
            raise ValueError('TGA color mapped without a color map')
        idx = raw[:, 0].astype(np.int64) if size == 1 else (raw[:, 0] | (raw[:, 1].astype(np.int64) << 8))
        rgba = _tga_colors(cmap, cmbits, abits)[np.clip(idx - cmfirst, 0, cmlen - 1)]
        fmt = 'TGA/colormapped'
    elif itype in (3, 11):
        rgba = _tga_colors(raw[:, :1], 8, 0)
        if size == 2:
            rgba[:, 3] = raw[:, 1]
        fmt = 'TGA/gray'
    else:
        rgba = _tga_colors(raw, bpp, abits)
        fmt = 'TGA/%d' % bpp
    rgba = rgba.reshape(h, w, 4)
    if not desc & 0x20:
        rgba = rgba[::-1]
    if desc & 0x10:
        rgba = rgba[:, ::-1]
    return w, h, np.ascontiguousarray(rgba).tobytes(), fmt + ('/RLE' if itype >= 9 else '')


def tga_bytes(w, h, rgba):
    px = np.frombuffer(rgba, np.uint8).reshape(h, w, 4)[::-1, :, [2, 1, 0, 3]]
    return struct.pack('<BBBHHBHHHHBB', 0, 0, 2, 0, 0, 0, 0, 0, w, h, 32, 8) + np.ascontiguousarray(px).tobytes()


def decode(data, name=''):
    if data[:4] in (b'BLP1', b'BLP2'):
        im, info = _blp_image(data)
        return im.width, im.height, im.tobytes(), info['format']
    if data[:4] != b'DDS ' and data[:4] != b'\x89PNG' and (name.lower().endswith('.tga') or not name):
        try:
            return tga_decode(data)
        except ValueError:
            if name.lower().endswith('.tga'):
                raise
    im = Image.open(io.BytesIO(data))
    im.load()
    return im.width, im.height, im.convert('RGBA').tobytes(), im.format or 'image'


def _header_size(data, name):
    try:
        if data[:4] == b'BLP1':
            return struct.unpack_from('<II', data, 12) + ('BLP1',)
        if data[:4] == b'BLP2':
            return struct.unpack_from('<II', data, 8) + ('BLP2',)
        if data[:4] == b'DDS ':
            h, w = struct.unpack_from('<II', data, 12)
            return w, h, 'DDS'
        if name.lower().endswith('.tga'):
            w, h = struct.unpack_from('<HH', data, 12)
            return w, h, 'TGA'
    except struct.error:
        pass
    return None, None, None


def _first(a, names):
    for n in names:
        d = _get(a, n)
        if d:
            return n, d
    return None, None


def _texture(a, cited):
    name = cited.replace('/', '\\').strip()
    base, ext = os.path.splitext(name)
    for c in [name] + [base + e for e in IMAGE_EXTS if e != ext.lower()]:
        d = _get(a, c)
        if d:
            return c, d
    return None, None


def _quadrant(name):
    stem = os.path.splitext(name.replace('/', '\\').split('\\')[-1])[0].upper()
    return next((q for q in QUADRANTS if stem.endswith(q)), None)


def _loading_screen(a, m):
    v = m.get('version', 0)
    s = {'preset': None, 'custom': False, 'model': None, 'model_in_map': False, 'textures': [], 'layout': None,
         'size': None, 'replaceable': False, 'why_not': None}
    datas = {}
    if 'loading_bg' not in m:
        s['why_not'] = 'The loading screen of this map format is not known.'
        return s, datas
    s['preset'] = m['loading_bg'] if v >= 25 else m.get('loading_number')
    model = (_text(m.get('loading_model') or b'') or '').strip() if v >= 25 else ''
    if not model:
        s['why_not'] = ('The map uses a loading screen of the game, not an imported one.' if (s['preset'] or 0) >= 0
                        else 'The map has no imported loading screen.')
        return s, datas
    s['custom'] = True
    s['model'] = model = model.replace('/', '\\')
    if model.lower().endswith(IMAGE_EXTS):
        cited = [model]
        s['model_in_map'] = _texture(a, model)[0] is not None
    else:
        md = _get(a, model)
        if md is None:
            s['why_not'] = 'The loading screen model is not inside the map.'
            return s, datas
        s['model_in_map'] = True
        if md[:4] == b'MDLX':
            cited = mdxtex.mdx_textures(md)
        else:
            cited = [x.decode('utf-8', 'replace') for x in re.findall(rb'Image\s+"([^"]+)"', md)]
    for c in cited:
        f, d = _texture(a, c)
        w, h, kind = _header_size(d, f) if d else (None, None, None)
        s['textures'].append({'cited': c, 'file': f, 'format': kind, 'width': w, 'height': h,
                              'quadrant': _quadrant(c)})
        if f:
            datas[f] = d
    tx = s['textures']
    if len(tx) == 1:
        s['layout'] = 'single'
        s['size'] = [tx[0]['width'], tx[0]['height']] if tx[0]['file'] else None
    elif len(tx) == 4 and sorted(t['quadrant'] or '' for t in tx) == sorted(QUADRANTS):
        s['layout'] = 'quadrants'
        q = dict((t['quadrant'], t) for t in tx)
        if all(t['file'] for t in tx) and q['TL']['width'] == q['BL']['width'] and \
                q['TR']['width'] == q['BR']['width'] and q['TL']['height'] == q['TR']['height'] and \
                q['BL']['height'] == q['BR']['height']:
            s['size'] = [q['TL']['width'] + q['TR']['width'], q['TL']['height'] + q['BL']['height']]
    elif tx:
        s['layout'] = 'other'
    missing = [t['cited'] for t in tx if not t['file']]
    if not tx:
        s['why_not'] = 'The loading screen model has no texture.'
    elif missing:
        s['why_not'] = 'A texture of the loading screen is not inside the map: %s.' % ', '.join(missing)
    elif s['layout'] == 'other':
        s['why_not'] = 'The loading screen model uses %d textures in a layout this version does not know.' % len(tx)
    elif not s['size']:
        s['why_not'] = 'The four loading screen textures do not fit together.'
    elif any(t['format'] not in ('BLP1', 'BLP2', 'TGA') for t in tx):
        s['why_not'] = 'The loading screen texture is a %s file, which this version cannot write.' % \
                       next(t['format'] or 'unknown' for t in tx if t['format'] not in ('BLP1', 'BLP2', 'TGA'))
    else:
        s['replaceable'] = True
    return s, datas


RX_LUA_TOKENS = re.compile(r'--\[(=*)\[.*?\]\1\]|--[^\n]*|\[(=*)\[.*?\]\2\]|"((?:[^"\\\n]|\\.)*)"|'
                           r"'((?:[^'\\\n]|\\.)*)'", re.S)


def _script(a, m):
    j_name = j = None
    for n in ('war3map.j', 'scripts\\war3map.j'):
        d = _get(a, n)
        if d is not None:
            j_name, j = n, d
            break
    lua = _get(a, 'war3map.lua')
    if lua is not None and (m.get('script_language') == 1 or j_name is None):
        return 'lua', 'war3map.lua', lua.decode('utf-8', 'surrogateescape')
    if j_name is None:
        return None, None, ''
    kind = 'jass'
    if unprotect.script_j2b(a, j):
        kind = 'j2b'
    elif len(j) < 450 and a.find('kkmap.jc'):
        kind = 'kkwe'
    return kind, j_name, j.decode('utf-8', 'surrogateescape')


def _literals(text, lua):
    out = []
    if not lua:
        for m in jass_ast._LITERAL_SPLIT_RE.finditer(text):
            if m.group(1) is not None:
                out.append((m.start(), jass_ast._unescape(m.group(1))))
        return out
    for m in RX_LUA_TOKENS.finditer(text):
        if m.group(2) is not None:
            out.append((m.start(), lua_ast._long_value(m.group(0))))
        elif m.group(3) is not None or m.group(4) is not None:
            body = m.group(3) if m.group(3) is not None else m.group(4)
            value = lua_ast._unescape(body)[0]
            out.append((m.start(), body if value is None else value))
    return out


def _args(text, i, limit=4000):
    depth, start, out, k, n = 0, i + 1, [], i, len(text)
    while k < n and k - i < limit:
        c = text[k]
        if c == '"' or c == "'":
            m = (RX_LIT_DQ if c == '"' else RX_LIT_SQ).match(text, k)
            k = m.end() if m else k + 1
            continue
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                out.append(text[start:k].strip())
                return out
        elif c == ',' and depth == 1:
            out.append(text[start:k].strip())
            start = k + 1
        k += 1
    return None


def _value(arg, text, lua, cache):
    m = RX_LIT_DQ.fullmatch(arg) or (lua and RX_LIT_SQ.fullmatch(arg))
    if m:
        body = arg[1:-1]
        return lua_ast._unescape(body)[0] if lua else jass_ast._unescape(body)
    if lua and re.fullmatch(r'\[(=*)\[.*\]\1\]', arg, re.S):
        return lua_ast._long_value(arg)
    if not re.fullmatch(r'[A-Za-z_]\w*', arg):
        return None
    if arg not in cache:
        rx = re.compile((re.escape(arg) if lua else r'string\s+' + re.escape(arg)) + r'\s*=\s*(' + _LIT + ')')
        d = next(_calls(rx, text), None)
        cache[arg] = jass_ast._unescape(d.group(1)[1:-1]) if d else None
    return cache[arg]


def _calls(rx, text):
    for m in rx.finditer(text):
        s = m.start()
        if s and (text[s - 1].isalnum() or text[s - 1] in '_.:'):
            continue
        yield m


def _trig(value, strings):
    m = RX_TRIGSTR.match(value or '')
    return strings.get(int(m.group(1)), value) if m else value


def _unquote(literal, lua):
    body = literal[1:-1]
    return lua_ast._unescape(body)[0] if lua else jass_ast._unescape(body)


def _chat_compared(text, lua):
    out = set()
    key = 'GetEventPlayerChatString'
    i = text.find(key)
    while i >= 0:
        before = text[max(0, i - 400):i]
        m = RX_CHAT_AFTER.match(text, i)
        if m:
            out.add(_unquote(m.group(1), lua))
        m = RX_CHAT_BEFORE.search(before)
        if m:
            out.add(_unquote(m.group(1), lua))
        if RX_SUBSTRING_BEFORE.search(before):
            m = RX_CHAT_SUBSTRING.match(text, i)
            if m:
                out.add(_unquote(m.group(1), lua))
        i = text.find(key, i + len(key))
    return out


def computed_strings(text, expressions, budget=300000, seconds=8.0):
    out = {}
    if not expressions:
        return out
    try:
        from doctor.script import jass_eval
        it = jass_eval.run(text, budget=budget, seconds=seconds)
    except Exception:
        return out
    deadline = time.time() + seconds
    for x in expressions:
        if time.time() > deadline:
            break
        try:
            out[x] = it.text(x)
        except Exception:
            pass
    return out


def chat_commands(text, lua, strings=None):
    strings = strings or {}
    found, cache = [], {}
    for m in _calls(RX_CHAT_EVENT, text):
        args = _args(text, m.end() - 1)
        if not args or len(args) < 3:
            continue
        value = _value(args[2], text, lua, cache)
        exact = {'true': True, 'false': False}.get(args[3] if len(args) > 3 else '')
        found.append((value, exact, args[2]))
    decoded = {} if lua else computed_strings(text, sorted(set(
        x for v, _e, x in found if v is None and ('(' in x or (re.fullmatch(r'[A-Za-z_]\w*', x) and re.search(
            r'(?m)^[ \t]*(?:constant\s+)?string\s+' + re.escape(x) + r'\b', text))))))
    seen, built = {}, set()
    for value, exact, expr in found:
        if value is None and decoded.get(expr) is not None:
            key = (_trig(decoded[expr], strings), exact, None)
            built.add(key)
        else:
            key = (_trig(value, strings), exact, None if value is not None else expr[:120])
        seen[key] = seen.get(key, 0) + 1
    order = sorted(seen.items(), key=lambda kv: (kv[0][0] is None, kv[0][0] if kv[0][0] is not None else kv[0][2],
                                                 str(kv[0][1])))
    registered = [dict({'text': t, 'exact': e, 'count': c}, **({'decoded': True} if (t, e, x) in built else {}))
                  if t is not None else {'text': None, 'expr': x, 'exact': e, 'count': c} for (t, e, x), c in order]
    compared = set(_trig(x, strings) for x in _chat_compared(text, lua))
    return registered, sorted(x for x in compared if x is not None)


def save_info(text, lua, registered):
    files = {}
    cache = {}
    for kind, rx in RX_PRELOAD:
        out = []
        for m in _calls(rx, text):
            args = _args(text, m.end() - 1)
            if not args or not args[0]:
                continue
            value = _value(args[0], text, lua, cache)
            item = value if value is not None else args[0][:160]
            if item not in out:
                out.append(item)
        files[kind] = out
    platform = {}
    for m in _calls(RX_PLATFORM_SAVE, text):
        platform[m.group(1)] = platform.get(m.group(1), 0) + 1
    caches = []
    if next(_calls(RX_SAVE_GAME_CACHE, text), None):
        for m in _calls(RX_GAME_CACHE, text):
            name = _unquote(m.group(1), lua)
            if name not in caches:
                caches.append(name)
    kinds = []
    if files['writes'] or files['reads']:
        kinds.append('local_file')
    if any(n.startswith('DzAPI') for n in platform):
        kinds.append('platform_kk')
    if any(n.startswith('JN') for n in platform):
        kinds.append('platform_jn')
    if caches:
        kinds.append('game_cache')
    commands = sorted(set(r['text'] for r in registered if r['text'] and re.search(r'save|load', r['text'], re.I)))
    return {'kinds': kinds, 'files': files, 'preload_lines': sum(1 for _m in _calls(RX_PRELOAD_LINE, text)),
            'platform': dict(sorted(platform.items())), 'game_caches': caches, 'commands': commands}


def language(pieces, trusted=('wts', 'w3i'), enough=200):
    joined = dict((src, RX_COLOR.sub(' ', '\n'.join(t for t in texts if t))) for src, texts in pieces.items())
    weight = dict((k, wgt) for k, _c, wgt in WRITING)

    def count(text):
        return dict((k, len(RX_WRITING[k].findall(text))) for k, _c, _w in WRITING)

    basis = [s for s in trusted if s in joined]
    allt = '\n'.join(joined[s] for s in basis)
    chars = count(allt)
    if sum(n * weight[k] for k, n in chars.items()) < enough:
        basis = sorted(joined)
        allt = '\n'.join(joined.values())
        chars = count(allt)
    total = count('\n'.join(joined.values()))
    out = {'language': None, 'script': None, 'basis': basis, 'chars': dict((k, n) for k, n in total.items() if n),
           'sources': dict((src, len(t)) for src, t in joined.items())}
    best = max(chars, key=lambda k: (chars[k] * weight[k], k))
    if not chars[best]:
        return out
    out['script'] = best
    if best == 'han' and chars['kana'] * 5 >= chars['han']:
        out['language'] = 'Japanese'
    elif best == 'latin':
        words = collections.Counter(RX_WORD.findall(allt.lower()))
        hits = [(sum(words[w] for w in sw.split()), lang) for lang, sw in STOPWORDS]
        n, lang = max(hits)
        out['language'] = lang if n >= 5 and n * 100 >= sum(words.values()) else 'Latin script'
    else:
        out['language'] = LANGUAGE_OF.get(best)
    return out


def _visible_literal(s):
    if not s or s.startswith('TRIGSTR_') or RX_PATHLIKE.search(s):
        return False
    if s.isascii() and not any(c.isspace() for c in s):
        return False
    t = RX_COLOR.sub('', s)
    odd = sum(1 for c in t if not (c.isalnum() or c.isspace() or c in TEXT_PUNCTUATION))
    return bool(t.strip()) and odd * 10 <= len(t)


def _lobby(path):
    with open(path, 'rb') as f:
        cab = f.read(hm3w_names.TAM)
    if cab[:4] != b'HM3W' or b'\0' not in cab[hm3w_names.OFF_NAME:]:
        return None, None
    end = cab.index(b'\0', hm3w_names.OFF_NAME)
    players = struct.unpack_from('<I', cab, end + 5)[0] if end + 9 <= len(cab) else None
    return hm3w_names.name_hm3w(path), players


def _model_of(a):
    b = _get(a, 'war3map.w3i')
    if b is None:
        if _get(a, 'war3campaign.w3f') is not None:
            raise CardError('campaign', 'This is a campaign, not a map: open one of its maps.')
        raise CardError('no_w3i', 'The map has no map info file (war3map.w3i) that can be read; a protected map has '
                                  'to be unprotected first.')
    m, how, dev = _w3i_model(b)
    wts = _get(a, 'war3map.wts')
    return b, m, how, dev, wts, wts_strings(wts)


def read(path, progress=None):
    try:
        return _read(path, progress or _nothing)
    except CardError as e:
        return {'ok': False, 'path': path, 'error': e.code, 'message': e.message}
    except MemoryError:
        return {'ok': False, 'path': path, 'error': 'read_failed', 'message': 'The map is too large to read here.'}
    except Exception as e:
        return {'ok': False, 'path': path, 'error': 'read_failed',
                'message': 'The map could not be read (%s).' % unprotect._error(e)}


def _read(path, p):
    p('Opening the map')
    a = _open(path)
    p('Reading the map info')
    _b, m, how, dev, wts, strings = _model_of(a)
    card = {'ok': True, 'path': path}
    _w3i_part(card, m, how, dev, strings)
    card['lobby_name'], card['lobby_players'] = _lobby(path)
    p('Looking at the images')
    screen, _datas = _loading_screen(a, m)
    card['loading']['screen'] = screen
    loading = None
    if screen['textures'] and all(t['file'] for t in screen['textures']):
        files = [t['file'] for t in screen['textures']]
        if screen['layout'] == 'quadrants':
            q = dict((t['quadrant'], t['file']) for t in screen['textures'])
            files = [q[k] for k in QUADRANTS]
        loading = files[0] if len(files) == 1 else files
    card['images'] = {'minimap': _first(a, MINIMAP)[0], 'preview': _first(a, PREVIEW)[0], 'loading': loading}
    p('Reading the script')
    kind, name, text = _script(a, m)
    lua = kind == 'lua'
    registered, compared = chat_commands(text, lua, strings) if text else ([], [])
    literals = [v for _s, v in _literals(text, lua)] if text else []
    w3i_texts = [card.get(f) for f, _k in TEXTS if '.' not in f] + \
        [card[sec].get(sub) for sec, sub in (f.split('.') for f, _k in TEXTS if '.' in f)] + \
        [x['name'] for x in card['players']] + [x['name'] for x in card['forces']]
    card['info'] = {
        'script': {'kind': kind, 'file': name, 'bytes': len(text.encode('utf-8', 'surrogateescape')) if text else 0},
        'chat_commands': registered, 'chat_compared': compared,
        'save': save_info(text, lua, registered),
        'language': language({'wts': list(strings.values()), 'w3i': w3i_texts,
                              'script': [v for v in literals if _visible_literal(v)]})}
    p('Done')
    return card


def _compose(parts, size):
    w, h = size
    out = np.zeros((h, w, 4), np.uint8)
    tl = parts['TL']
    for q, (x, y) in (('TL', (0, 0)), ('TR', (tl[0], 0)), ('BL', (0, tl[1])), ('BR', (tl[0], tl[1]))):
        pw, ph, px = parts[q]
        out[y:y + ph, x:x + pw] = np.frombuffer(px, np.uint8).reshape(ph, pw, 4)
    return out.tobytes()


def _loading_pixels(screen, datas):
    tx = screen['textures']
    if screen['layout'] == 'single':
        f = tx[0]['file']
        w, h, px, fmt = decode(datas[f], f)
        return w, h, px, [f], fmt
    if screen['layout'] == 'quadrants' and screen['size']:
        parts, fmts, files = {}, set(), []
        for q in QUADRANTS:
            t = next(t for t in tx if t['quadrant'] == q)
            w, h, px, fmt = decode(datas[t['file']], t['file'])
            if (w, h) != (t['width'], t['height']):
                raise ValueError('the %s quadrant decodes at another size' % q)
            parts[q] = (w, h, px)
            fmts.add(fmt)
            files.append(t['file'])
        return screen['size'][0], screen['size'][1], _compose(parts, screen['size']), files, '+'.join(sorted(fmts))
    raise ValueError('no loading image')


def image(path, which, progress=None):
    p = progress or _nothing
    try:
        p('Opening the map')
        a = _open(path)
        p('Decoding the image')
        if which in ('minimap', 'preview'):
            name, d = _first(a, MINIMAP if which == 'minimap' else PREVIEW)
            if d is None:
                return None
            w, h, px, fmt = decode(d, name)
            files = [name]
        elif which == 'loading':
            _b, m, _how, _dev, _wts, _s = _model_of(a)
            screen, datas = _loading_screen(a, m)
            w, h, px, files, fmt = _loading_pixels(screen, datas)
        else:
            return None
        return {'width': w, 'height': h, 'rgba': _b64(px), 'files': files, 'format': fmt}
    except Exception:
        return None


def _hex_color(c):
    s = str(c).strip()
    s = s[2:] if s[:2] in ('|c', '|C') else s.lstrip('#')
    if re.fullmatch(r'[0-9a-fA-F]{8}', s):
        s = s[2:]
    if not re.fullmatch(r'[0-9a-fA-F]{6}', s):
        raise ValueError('not a hex color: %r' % c)
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def gradient(text, colors):
    if isinstance(colors, str):
        colors = [c for c in re.split(r'[\s,;]+', colors) if c]
    stops = [_hex_color(c) for c in colors]
    if not stops:
        raise ValueError('no color')
    tokens = []
    pos = 0
    for m in tr_gradient.RX_COD.finditer(text):
        tokens.extend(text[pos:m.start()])
        if m.group(0).lower() == '|n':
            tokens.append('|n')
        pos = m.end()
    tokens.extend(text[pos:])
    visible = [t for t in tokens if t != '|n' and not t.isspace()]
    n = len(visible)

    def color(i):
        if len(stops) == 1 or n == 1:
            return stops[0]
        x = i * (len(stops) - 1) / float(n - 1)
        j = min(int(x), len(stops) - 2)
        f = x - j
        return tuple(int(round(stops[j][k] * (1 - f) + stops[j + 1][k] * f)) for k in range(3))

    out, run, spaces, i = [], None, '', 0
    for t in tokens:
        if t == '|n' or t in '\r\n':
            if run is not None:
                out.append('|r')
                run = None
            out.append(spaces + t)
            spaces = ''
        elif t.isspace():
            spaces += t
        else:
            c = color(i)
            i += 1
            if c == run:
                out.append(spaces + t)
            else:
                if run is not None:
                    out.append('|r')
                out.append(spaces + '|cff%02x%02x%02x' % c + t)
                run = c
            spaces = ''
    if run is not None:
        out.append('|r')
    out.append(spaces)
    return ''.join(out)


CHANGE_KEYS = ('name', 'author', 'description', 'players_suggested', 'loading', 'prologue', 'lobby_name', 'players',
               'forces', 'images', 'minimap', 'preview')


def _by_index(value, what):
    if isinstance(value, dict):
        items = value.items()
    elif isinstance(value, list):
        try:
            items = [(x['index'], x['name']) for x in value]
        except (TypeError, KeyError):
            raise CardError('bad_change', 'Each of the %s changes needs an index and a name.' % what)
    else:
        raise CardError('bad_change', 'The %s change must be a list or a mapping.' % what)
    try:
        return dict((int(k), v) for k, v in items)
    except (TypeError, ValueError):
        raise CardError('bad_change', 'A %s index is not a number.' % what)


def _text_changes(changes, m):
    out = []
    for field, key in TEXTS:
        if '.' in field:
            sec, sub = field.split('.')
            val = (changes.get(sec) or {}).get(sub) if isinstance(changes.get(sec), dict) else None
        else:
            val = changes.get(field)
        if val is not None:
            out.append((field, val, ('w3i', key)))
    for what, lst, kind in (('players', m.get('players') or [], 'player'), ('forces', m.get('forces') or [], 'force')):
        if changes.get(what) is None:
            continue
        for idx, val in sorted(_by_index(changes[what], what).items()):
            if kind == 'player':
                pos = next((i for i, x in enumerate(lst) if x['number'] == idx), None)
            else:
                pos = idx if 0 <= idx < len(lst) else None
            if pos is None:
                raise CardError('bad_change', 'The map has no %s with index %d.' % (kind, idx))
            out.append(('%ss.%d.name' % (kind, idx), val, (kind, pos)))
    for field, val, _w in out:
        if not isinstance(val, str):
            raise CardError('bad_change', 'The new %s is not a text.' % field)
        if '\0' in val:
            raise CardError('bad_text', 'The new %s has a NUL character.' % field)
    return out


def _raw_of(m, where):
    kind, x = where
    if kind == 'w3i':
        return m.get(x)
    return m['players' if kind == 'player' else 'forces'][x]['name']


def _set_raw(m, where, raw):
    kind, x = where
    if kind == 'w3i':
        m[x] = raw
    else:
        m['players' if kind == 'player' else 'forces'][x]['name'] = raw


def _check_w3i(old, new_model, new_bytes, changed):
    try:
        back = w3i.parse(new_bytes)
    except Exception as e:
        raise CardError('check_failed', 'The new map info file does not read back (%s).' % unprotect._error(e))
    if w3i.write(back) != new_bytes:
        raise CardError('check_failed', 'The new map info file does not read back exactly.')
    for k in set(old) | set(back):
        if k in ('players', 'forces'):
            kind = 'player' if k == 'players' else 'force'
            if len(old[k]) != len(back[k]):
                raise CardError('check_failed', 'The number of %s changed in the map info file.' % k)
            for i, (a_, b_) in enumerate(zip(old[k], back[k])):
                want = dict(a_, name=new_model[k][i]['name']) if (kind, i) in changed else a_
                if want != b_:
                    raise CardError('check_failed', 'A field of %s %d changed in the map info file.' % (kind, i))
        elif ('w3i', k) in changed:
            if back.get(k) != new_model.get(k):
                raise CardError('check_failed', 'The map info field %s did not take the new text.' % k)
        elif old.get(k) != back.get(k):
            raise CardError('check_failed', 'The map info field %s changed.' % k)


def _new_image(spec, what):
    try:
        w, h = int(spec['width']), int(spec['height'])
        px = base64.b64decode(spec['rgba'], validate=True)
    except Exception:
        raise CardError('bad_image', 'The new %s is not an image (width, height and rgba in base64).' % what)
    if w <= 0 or h <= 0 or len(px) != w * h * 4:
        raise CardError('bad_image', 'The new %s has %d bytes of pixels; %dx%d needs %d.' % (what, len(px), w, h,
                                                                                            w * h * 4))
    return w, h, px


def _blp_params(old):
    if old and old[:4] == b'BLP1' and len(old) >= 28:
        _c, alpha, _w, _h, extra, mips = struct.unpack_from('<IIIIII', old, 4)
        return (8 if alpha else 0), bool(mips), extra
    return 0, False, 5


def _encode(name, w, h, px, old):
    if name.lower().endswith('.tga'):
        return tga_bytes(w, h, px), 0
    alpha, mips, extra = _blp_params(old)
    return _blp_bytes(Image.frombytes('RGBA', (w, h), px), alpha, mips, extra), alpha


def _check_image(name, data, w, h, px, alpha):
    try:
        w2, h2, px2, _fmt = decode(data, name)
    except Exception as e:
        raise CardError('check_failed', 'The new %s does not decode (%s).' % (name, unprotect._error(e)))
    if (w2, h2) != (w, h):
        raise CardError('check_failed', 'The new %s decodes at %dx%d, not %dx%d.' % (name, w2, h2, w, h))
    if name.lower().endswith('.tga'):
        if px2 != px:
            raise CardError('check_failed', 'The new %s does not decode to the same pixels.' % name)
        return
    a = np.frombuffer(px, np.uint8).reshape(-1, 4).astype(np.int16)
    b = np.frombuffer(px2, np.uint8).reshape(-1, 4).astype(np.int16)
    k = 4 if alpha else 3
    err = np.abs(a[:, :k] - b[:, :k]).mean(axis=0).max()
    if err > JPEG_TOLERANCE:
        raise CardError('check_failed', 'The new %s decodes too far from the image (%.1f per channel).' % (name, err))


def _image_files(a, m, images):
    out = []
    for which, spec in sorted(images.items()):
        if spec is None:
            continue
        if which not in ('minimap', 'preview', 'loading'):
            raise CardError('bad_change', 'Unknown image: %s.' % which)
        w, h, px = _new_image(spec, which)
        if which == 'minimap':
            lo, hi = MINIMAP_SIDES
            if w != h or w & (w - 1) or not lo <= w <= hi:
                raise CardError('bad_image', 'The minimap must be square with a side that is a power of two from %d '
                                             'to %d (the editor writes 256x256); this one is %dx%d.' % (lo, hi, w, h))
            name, old = _first(a, MINIMAP)
            name = name or MINIMAP[0]
            data, alpha = _encode(name, w, h, px, old)
            out.append((name, data, w, h, px, alpha))
        elif which == 'preview':
            lo, hi = PREVIEW_SIDES
            if w != h or not lo <= w <= hi:
                raise CardError('bad_image', 'The preview must be square, from %d to %d pixels a side; this one is '
                                             '%dx%d.' % (lo, hi, w, h))
            out.append((PREVIEW[0], tga_bytes(w, h, px), w, h, px, 0))
        else:
            screen, datas = _loading_screen(a, m)
            if not screen['replaceable']:
                raise CardError('not_supported', 'The loading image cannot be changed in this map: %s'
                                % (screen['why_not'] or 'unknown reason'))
            sw, sh = screen['size']
            if (w, h) != (sw, sh):
                raise CardError('bad_image', 'The loading image must be %dx%d, the size of the one it replaces; this '
                                             'one is %dx%d.' % (sw, sh, w, h))
            if screen['layout'] == 'single':
                f = screen['textures'][0]['file']
                data, alpha = _encode(f, w, h, px, datas[f])
                out.append((f, data, w, h, px, alpha))
                continue
            full = np.frombuffer(px, np.uint8).reshape(h, w, 4)
            q = dict((t['quadrant'], t) for t in screen['textures'])
            x0, y0 = q['TL']['width'], q['TL']['height']
            for key, (ys, xs) in (('TL', (slice(0, y0), slice(0, x0))), ('TR', (slice(0, y0), slice(x0, w))),
                                  ('BL', (slice(y0, h), slice(0, x0))), ('BR', (slice(y0, h), slice(x0, w)))):
                t = q[key]
                part = np.ascontiguousarray(full[ys, xs]).tobytes()
                data, alpha = _encode(t['file'], t['width'], t['height'], part, datas[t['file']])
                out.append((t['file'], data, t['width'], t['height'], part, alpha))
    return out


def _other_files_same(a, b, changed):
    if a.hash_n_read != b.hash_n_read or a.h.offset != b.h.offset:
        raise CardError('check_failed', 'The file table of the new map is not the one of the original.')
    allowed = set()
    for n in changed:
        allowed.update(e[0] for e in a.hash_entries(n))
        allowed.update(e[0] for e in b.hash_entries(n))
    blocks, same = set(), 0
    for i in range(a.hash_n_read):
        if i in allowed:
            continue
        ea, eb = tuple(a.ht[4 * i:4 * i + 4]), tuple(b.ht[4 * i:4 * i + 4])
        if ea != eb:
            raise CardError('check_failed', 'Entry %d of the file table changed.' % i)
        same += 1
        if ea[3] < 0xFFFFFFFE and (ea[3] & mpqread.BLOCK_MASK) < len(a.blocks):
            blocks.add(ea[3] & mpqread.BLOCK_MASK)
    spans = []
    for bi in sorted(blocks):
        if bi >= len(b.blocks) or tuple(a.blocks[bi]) != tuple(b.blocks[bi]):
            raise CardError('check_failed', 'The entry of block %d changed in the new map.' % bi)
        start = (a.h.offset + a.blocks[bi][0]) & 0xFFFFFFFF
        end = min(start + a.blocks[bi][1], len(a.d))
        if start < end:
            spans.append((start, end, bi))
    spans.sort()
    merged = []
    for s, e, bi in spans:
        if merged and s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
            merged[-1][2].append(bi)
        else:
            merged.append([s, e, [bi]])
    for s, e, _bis in merged:
        for k in range(s, e, 1 << 24):
            x, y = a.d[k:min(e, k + (1 << 24))], b.d[k:min(e, k + (1 << 24))]
            if x != y:
                p = k + int(np.argmax(np.frombuffer(x, np.uint8) != np.frombuffer(y, np.uint8)))
                bad = next(bi for s2, e2, bi in spans if s2 <= p < e2)
                raise CardError('check_failed', 'A file this card does not change would come out different (block %d): '
                                                'unprotect the map first.' % bad)
    return {'hash_entries': same, 'blocks': len(blocks)}


def _writable(a):
    h = a.h
    if len(a.d) < h.offset + 32 or struct.unpack_from('<H', a.d, h.offset + 12)[0] != 0:
        raise CardError('protected', 'The archive header of this map is not the standard one (a protector changed '
                                     'it): unprotect the map first.')
    for bi in set(a.ht[4 * i + 3] & mpqread.BLOCK_MASK for i in range(a.hash_n_read)
                  if a.ht[4 * i + 3] < 0xFFFFFFFE):
        if bi < len(a.blocks) and a.blocks[bi][1]:
            s = (h.offset + a.blocks[bi][0]) & 0xFFFFFFFF
            if s < h.offset + 32 and h.offset < s + a.blocks[bi][1]:
                raise CardError('protected', 'A file of this map is stored over its archive header (a protector\'s '
                                             'trick): unprotect the map first.')


def _remove(path):
    for _ in range(3):
        try:
            if os.path.exists(path):
                os.remove(path)
            return
        except OSError:
            gc.collect()


def _shared(number, m, where, text):
    def uses(raw):
        r = RX_TRIGSTR.match(_text(raw or b''))
        return bool(r) and int(r.group(1)) == number

    out = [field for field, key in TEXTS if ('w3i', key) != where and uses(m.get(key))]
    for kind, lst in (('player', m.get('players') or []), ('force', m.get('forces') or [])):
        for i, x in enumerate(lst):
            if (kind, i) != where and uses(x['name']):
                out.append('%ss.%d.name' % (kind, x['number'] if kind == 'player' else i))
    n = 0
    for r in re.finditer(r'TRIGSTR_0*%d(?!\d)' % number, text or ''):
        before = text[max(0, r.start() - 120):r.start()]
        line = before.rsplit('\n', 1)[-1]
        if '//' in line or RX_MIRROR_CALL.search(before):
            continue
        n += 1
    if n:
        out.append('the script (%d)' % n)
    return out


def _script_sets(text, lua, call, old):
    rx = re.compile(re.escape(call) + r'\s*\(')
    cache = {}
    for m in _calls(rx, text or ''):
        args = _args(text, m.end() - 1)
        if args and (_value(args[0], text, lua, cache) or '').replace('\r\n', '\n') == old:
            return True
    return False


def write(path_in, path_out, changes, progress=None):
    try:
        return _write(path_in, path_out, changes or {}, progress or _nothing)
    except CardError as e:
        return {'ok': False, 'error': e.code, 'message': e.message}
    except MemoryError:
        return {'ok': False, 'error': 'write_failed', 'message': 'The map is too large to write here.'}
    except Exception as e:
        return {'ok': False, 'error': 'write_failed', 'message': 'The map could not be written (%s).'
                % unprotect._error(e)}


def _write_checked(a, part, repl, imgs, lobby, w3i_edit, texts, p):
    m, m2, w3i_changed = w3i_edit
    if repl:
        no_room = []
        with unprotect.quiet():
            mpqadd.add_files(part, repl, log=_nothing, no_slot=no_room)
        if no_room:
            raise CardError('table_full', 'The file table of the map has no room for %s: unprotect the map first.'
                            % ', '.join(no_room))
    if lobby is not None:
        try:
            hm3w_names.renomeia(part, lobby)
        except ValueError:
            raise CardError('bad_text', 'The lobby name is too long for the map header.')
    p('Checking the new map')
    b = _open(part)
    for n, d in repl:
        if _get(b, n) != d:
            raise CardError('check_failed', 'The new %s does not read back the same.' % n)
    for name, _data, w, h, px, alpha in imgs:
        _check_image(name, _get(b, name), w, h, px, alpha)
    if w3i_changed:
        _check_w3i(m, m2, _get(b, 'war3map.w3i'), w3i_changed)
    same = _other_files_same(a, b, [n for n, _d in repl])
    if lobby is not None and _lobby(part)[0] != lobby:
        raise CardError('check_failed', 'The new lobby name does not read back.')
    _bb, mb, howb, devb, _wb, sb = _model_of(b)
    card = {}
    _w3i_part(card, mb, howb, devb, sb)
    for field, val, _where in texts:
        sec, _dot, sub = field.partition('.')
        if sec in ('players', 'forces'):
            idx = int(sub.split('.')[0])
            got = next((x['name'] for x in card[sec] if x['index'] == idx), None)
        else:
            got = card[sec][sub] if sub else card[sec]
        if got != val.replace('\r\n', '\n'):
            raise CardError('check_failed', 'The new %s does not read back.' % field)
    return same


def _write(path_in, path_out, changes, p):
    if not isinstance(changes, dict):
        raise CardError('bad_change', 'The changes must be a mapping.')
    unknown = sorted(set(changes) - set(CHANGE_KEYS))
    for sec, keys in (('loading', ('title', 'subtitle', 'text', 'image')), ('prologue', ('title', 'subtitle', 'text'))):
        if changes.get(sec) is not None:
            if not isinstance(changes[sec], dict):
                raise CardError('bad_change', 'The %s change must be a mapping.' % sec)
            unknown += ['%s.%s' % (sec, k) for k in sorted(set(changes[sec]) - set(keys))]
    if unknown:
        raise CardError('bad_change', 'Unknown change: %s.' % ', '.join(unknown))
    if os.path.normcase(os.path.abspath(path_in)) == os.path.normcase(os.path.abspath(path_out)):
        raise CardError('same_path', 'The output must be a new file, not the map itself.')
    p('Opening the map')
    a = _open(path_in)
    _b, m, how, _dev, wts, strings = _model_of(a)
    texts = _text_changes(changes, m)
    images = dict(changes.get('images') or {})
    for k in ('minimap', 'preview'):
        if changes.get(k) is not None:
            images[k] = changes[k]
    if (changes.get('loading') or {}).get('image') is not None:
        images['loading'] = changes['loading']['image']

    p('Preparing the texts')
    kind, _sname, script = _script(a, m)
    m2 = copy.deepcopy(m)
    w3i_changed, wts_changed, fields, notes = set(), {}, [], []
    for field, val, where in texts:
        raw = _raw_of(m, where)
        cur, ref = _resolve(raw, strings)
        new = val.replace('\r\n', '\n')
        if new == (cur or ''):
            continue
        if ref:
            n = ref['number']
            if n in wts_changed and wts_changed[n] != new:
                raise CardError('bad_change', 'Two fields share string %d of the map and got different texts.' % n)
            wts_changed[n] = new
            fields.append({'field': field, 'to': 'war3map.wts', 'string': n})
            others = [x for x in _shared(n, m, where, script) if x not in [f['field'] for f in fields]]
            if others:
                notes.append('String %d (%s) is also used by %s: it changes there too.' % (n, field, ', '.join(others)))
        else:
            eol = '\r\n' if b'\r\n' in (raw or b'') else '\n'
            _set_raw(m2, where, new.replace('\n', eol).encode('utf-8'))
            w3i_changed.add(where)
            fields.append({'field': field, 'to': 'war3map.w3i'})
            for f_, call in MIRRORS:
                if field == f_ and _script_sets(script, kind == 'lua', call, cur or ''):
                    notes.append('The script still sets the old %s (%s in config); the script is not changed.'
                                 % (field, call))
    repl = []
    if w3i_changed:
        if how != 'exact':
            raise CardError('w3i_not_exact', 'The map info file (war3map.w3i, version %d) does not read back exactly, '
                                             'so it is not rewritten: %s cannot change.'
                            % (m['version'], ', '.join(f['field'] for f in fields if f['to'] == 'war3map.w3i')))
        new_w3i = w3i.write(m2)
        _check_w3i(m, m2, new_w3i, w3i_changed)
        repl.append(('war3map.w3i', new_w3i))
    if wts_changed:
        new_wts = wts
        for n, t in sorted(wts_changed.items()):
            new_wts = wts_set(new_wts, n, t)
        back = wts_strings(new_wts)
        if any(back.get(n) != t for n, t in wts_changed.items()) or \
                any(back.get(n) != t for n, t in strings.items() if n not in wts_changed):
            raise CardError('check_failed', 'The new strings file does not read back with the new texts only.')
        repl.append(('war3map.wts', new_wts))

    p('Preparing the images')
    imgs = _image_files(a, m, images)
    repl += [(x[0], x[1]) for x in imgs]
    lobby = changes.get('lobby_name')
    current_lobby = _lobby(path_in)[0]
    if lobby is not None and lobby != current_lobby:
        if current_lobby is None:
            raise CardError('no_hm3w', 'The map has no lobby header (HM3W) to hold a lobby name.')
        if not isinstance(lobby, str) or '\0' in lobby:
            raise CardError('bad_text', 'The lobby name must be a text without NUL characters.')
    else:
        lobby = None
    if not repl and lobby is None:
        return {'ok': True, 'written': False, 'output': None, 'fields': [], 'files': [], 'new_files': [],
                'lobby_name': None, 'checks': {}, 'notes': ['Nothing changed: no map was written.']}
    new_files = [n for n, _d in repl if not a.find(n)]
    lf = _get(a, '(listfile)')
    if new_files and lf is not None:
        listed = lf.decode('utf-8', 'surrogateescape')
        lines = [x for x in listed.replace('\r\n', '\n').split('\n') if x.strip()]
        have = set(x.strip().lower() for x in lines)
        lines += [n for n in new_files if n.lower() not in have]
        eol = '\r\n' if '\r\n' in listed or not listed else '\n'
        repl.append(('(listfile)', (eol.join(lines) + eol).encode('utf-8', 'surrogateescape')))
    if a.find('(attributes)') and repl:
        notes.append('The (attributes) file of the map was kept as it was.')

    if repl:
        _writable(a)
    p('Writing the map')
    part = unprotect._part(path_out)
    failure = None
    try:
        shutil.copyfile(path_in, part)
        same = _write_checked(a, part, repl, imgs, lobby, (m, m2, w3i_changed), texts, p)
        os.replace(part, path_out)
    except KeyboardInterrupt:
        _remove(part)
        raise
    except CardError as e:
        failure = (e.code, e.message)
    except BaseException as e:
        failure = ('write_failed', 'The map could not be written (%s); unprotect it first.' % unprotect._error(e))
    if failure:
        _remove(part)
        raise CardError(*failure)
    return {
        'ok': True,
        'written': True,
        'output': path_out,
        'fields': fields,
        'files': [n for n, _d in repl],
        'new_files': new_files,
        'lobby_name': lobby,
        'checks': {
            'files_reread': len(repl),
            'images_decoded': len(imgs),
            'other_hash_entries': same['hash_entries'],
            'other_blocks': same['blocks'],
            'w3i_round_trip': bool(w3i_changed),
        },
        'notes': notes,
    }
