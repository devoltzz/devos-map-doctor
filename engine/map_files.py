# The viewers: the files of a map with a preview, the script, and the trigger tree.
import base64
import io
import os
import re
import struct
import time

import unprotect
import mpqnames
import mpqread


READ_MAX = 256 << 20
PREVIEW_MAX = 8 << 20
SCRIPT_MAX = 64 << 20
HEX_BYTES = 4096
MAX_SIDE = 1024
SNIFF_MAX = 5000
SPECIAL = ('(listfile)', '(attributes)', '(signature)')
RX_NOT_ASCII = re.compile(r'[^\x00-\x7f]')
RX_HIGH_BYTE = re.compile(rb'[\x80-\xff]')
RX_SCRIPT_TEXT = re.compile(rb'"(?:[^"\\\r\n]|\\.)*"|//[^\r\n]*|--[^\r\n]*')
CAMPAIGN_SEEDS = tuple('war3campaign.' + e for e in ('w3f', 'w3u', 'w3t', 'w3a', 'w3b', 'w3d', 'w3h', 'w3q', 'wts',
                                                      'imp')) + ('war3campaignSkin.txt', 'war3campaignMisc.txt')

IMAGE_EXT = tuple(mpqnames.IMAGE_EXT) + ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
MODEL_EXT = tuple(mpqnames.MODEL_EXT)
SOUND_MIME = {'.wav': 'audio/wav', '.mp3': 'audio/mpeg', '.ogg': 'audio/ogg', '.flac': 'audio/flac'}
SCRIPT_EXT = {'.j': 'jass', '.ai': 'jass', '.lua': 'lua'}
TEXT_EXT = tuple(sorted(set(mpqnames.EXT_TEXT) - set(SCRIPT_EXT))) + ('.wts',)
MAP_DATA_EXT = ('.w3e', '.w3i', '.wtg', '.wct', '.w3u', '.w3t', '.w3a', '.w3b', '.w3d', '.w3h', '.w3q', '.w3c', '.w3r',
                '.w3s', '.doo', '.wpm', '.shd', '.mmp', '.imp', '.w3f', '.w3v', '.w3x', '.w3m', '.w3n')
IMAGE_MIME = ((b'\x89PNG', 'image/png'), (b'\xff\xd8\xff', 'image/jpeg'), (b'GIF87a', 'image/gif'),
              (b'GIF89a', 'image/gif'), (b'BM', 'image/bmp'))
SOUND_MAGIC = ((b'RIFF', '.wav'), (b'ID3', '.mp3'), (b'\xff\xfb', '.mp3'), (b'\xff\xf3', '.mp3'),
               (b'\xff\xf2', '.mp3'), (b'OggS', '.ogg'), (b'fLaC', '.flac'))

_ARCHIVE = []
_NAMES = {}
_INDEX = []


def _quiet(*_a, **_k):
    pass


def _error(e):
    if isinstance(e, SystemExit):
        return str(e) or 'the map cannot be read'
    return '%s: %s' % (type(e).__name__, e) if str(e) else type(e).__name__


def _b64(data):
    return base64.b64encode(data).decode('ascii')


def _key(path):
    p = os.path.abspath(path)
    return p, os.path.getsize(p), os.path.getmtime(p)


def forget():
    del _ARCHIVE[:]
    _NAMES.clear()
    mpqread.clear_cache()


def _open(path):
    key = _key(path)
    if _ARCHIVE and _ARCHIVE[0][0] == key:
        return _ARCHIVE[0][1], _ARCHIVE[0][2]
    forget()
    import ntfs_undo
    notes = []
    archive, failure = None, None
    try:
        archive = unprotect._open(path)
        data = archive.d
    except (Exception, SystemExit) as e:
        failure = e
        with open(path, 'rb') as f:
            data = f.read()
    if ntfs_undo.detect(data) is not None:
        restored, _report = unprotect.restore_copy(path, data)
        if restored:
            archive = unprotect._open(restored)
            notes.append('The file is a copy made from a folder compressed by NTFS; it is read as the Doctor restores '
                         'it.')
    del data
    if archive is None:
        raise failure
    _ARCHIVE.append((key, archive, notes))
    return archive, notes


def _map_names(path, a):
    key = _key(path)
    names = _NAMES.get(key)
    if names is None:
        with unprotect.quiet():
            names = unprotect.map_names(a)
            if a.find('war3campaign.w3f'):
                have = set(n.upper() for n in names)
                extra = mpqnames.referenced_closure(a, seeds=list(CAMPAIGN_SEEDS))
                names = sorted(names + [n for n in extra if n.upper() not in have and n.lower() not in SPECIAL],
                               key=lambda n: (n.lower(), n))
        _NAMES[key] = names
    return names


def _game_block(a, name):
    r = a.find(name)
    if not r:
        return None
    if len(set(e[3] for e in a.hash_entries(name))) > 1 and a.validate_light(r[1], name)[0] != 'ok':
        r = a.find_locale(name) or r
    return r[1]


def kind_of(name):
    ext = os.path.splitext(name)[1].lower()
    if name.lower() == '(listfile)':
        return 'text'
    if ext in IMAGE_EXT:
        return 'image'
    if ext in MODEL_EXT:
        return 'model'
    if ext in SOUND_MIME:
        return 'sound'
    if ext in SCRIPT_EXT:
        return 'script'
    if ext in TEXT_EXT:
        return 'text'
    if ext in MAP_DATA_EXT:
        return 'map data'
    return 'other'


def _sniff(data):
    if not data:
        return 'other', '.bin'
    import carver
    try:
        standard, ext, _what = carver.identify(data[:1 << 20])
    except Exception:
        standard, ext = None, '.bin'
    for magic, e in SOUND_MAGIC:
        if data.startswith(magic):
            ext = e
    for magic, mime in IMAGE_MIME[:4]:
        if data.startswith(magic):
            ext = {'image/png': '.png', 'image/jpeg': '.jpg', 'image/gif': '.gif'}[mime]
    if standard:
        return kind_of(standard), ext
    return kind_of('x' + ext), ext


def _stored(a, bi, name):
    ini, end = a.interval(bi, name)
    return max(0, end - ini)


def _index():
    if not _INDEX:
        idx = None
        try:
            idx = mpqnames.load_big()
        except Exception:
            idx = None
        if idx is None:
            try:
                idx = mpqnames.load_data()
            except Exception:
                idx = None
        _INDEX.append(idx)
    return _INDEX[0]


def _dictionary_names(a, unnamed, known):
    idx = _index()
    wanted = set(unnamed)
    if idx is None or not wanted:
        return {}
    ht = a.ht
    pairs = []
    for i in range(a.hash_n_read):
        bi = ht[4 * i + 3]
        if bi < 0xFFFFFFFE and (bi & mpqread.BLOCK_MASK) in wanted:
            pairs.append((ht[4 * i], ht[4 * i + 1]))
    if not pairs:
        return {}
    found = set()
    if hasattr(idx, 'lookup_batch'):
        for i in idx.lookup_batch([p[0] for p in pairs], [p[1] for p in pairs]):
            if i >= 0:
                found.add(idx.fname(int(i)))
    else:
        for p in pairs:
            n = idx.lookup(p[0], p[1])
            if n:
                found.add(n)
    if not found:
        return {}
    with unprotect.quiet():
        accepted, _counts = mpqnames.dictionary_leftovers(a, known, sorted(found))
    return dict((n, bi) for n, bi in accepted.items() if bi in wanted)


def list_files(path, progress=None, dictionary=True, classify=False):
    say = progress or _quiet
    out = {'files': [], 'unnamed': [], 'total': 0, 'map': None, 'notes': [], 'error': None}
    try:
        say('Reading the map')
        a, notes = _open(path)
        out['notes'] = list(notes)
        out['map'] = {'name': unprotect.map_name(a.d), 'size': len(a.d), 'blocks': len(a.blocks),
                      'hash_entries': a.hash_n_read}
        say('Finding the file names')
        names = _map_names(path, a)
        known = {}
        for n in list(names) + [s for s in SPECIAL if a.find(s)]:
            bi = _game_block(a, n)
            if bi is None:
                continue
            known.setdefault(n, bi)
            out['files'].append({'name': n, 'size': a.blocks[bi][2], 'stored': _stored(a, bi, n), 'kind': kind_of(n),
                                 'known_name': True, 'block': bi})
        unnamed = mpqnames.unnamed_blocks(a, set(known.values()))
        if dictionary and unnamed:
            say('Looking up the unnamed files in the name list')
            extra = _dictionary_names(a, unnamed, dict((n, bi) for n, bi in known.items() if n not in SPECIAL))
            for n, bi in sorted(extra.items(), key=lambda x: (x[0].lower(), x[0])):
                out['files'].append({'name': n, 'size': a.blocks[bi][2], 'stored': _stored(a, bi, n),
                                     'kind': kind_of(n), 'known_name': False, 'block': bi})
            got = set(extra.values())
            unnamed = [bi for bi in unnamed if bi not in got]
        say('Looking at the unnamed files')
        verdicts = {}
        if classify and unnamed:
            import mpqdoctor
            if not mpqdoctor.virtual_tables(a):
                with unprotect.quiet():
                    states, _sizes = mpqdoctor.classify_blocks(a, list(known))
                words = {'real': 'real', 'junk': 'junk'}
                verdicts = dict((bi, words.get(s, 'unknown')) for bi, (s, _m) in states.items())
        for k, bi in enumerate(unnamed):
            item = {'block': bi, 'size': a.blocks[bi][2], 'stored': _stored(a, bi, None), 'kind': 'other',
                    'ext': '.bin', 'state': verdicts.get(bi, 'unknown')}
            if k < SNIFF_MAX:
                if bi not in verdicts:
                    try:
                        verdict = a.validate(bi, None)[0]
                    except Exception:
                        verdict = 'invalid'
                    item['state'] = {'ok': 'real', 'invalid': 'junk'}.get(verdict, 'unknown')
                item['kind'], item['ext'] = _sniff(mpqnames.read_unnamed(a, bi, whole=False))
            out['unnamed'].append(item)
        out['files'].sort(key=lambda f: (f['name'].lower(), f['name']))
        out['total'] = len(out['files']) + len(out['unnamed'])
        if not names:
            out['notes'].append('No name reaches the files of this map (its tables are scrambled or its names are '
                                'gone): Unprotect rebuilds what can be rebuilt.' if out['unnamed'] else
                                'No entry of the hash table reaches a file of this map (its tables are scrambled): '
                                'Unprotect rebuilds the map from its content.')
    except (Exception, SystemExit) as e:
        out['error'] = _error(e)
    return out


def _read(a, name):
    if name.startswith('#') and name[1:].isdigit():
        bi = int(name[1:])
        if bi >= len(a.blocks) or not a.exists(bi):
            raise LookupError('there is no block %d' % bi)
        if a.blocks[bi][2] > READ_MAX:
            raise ValueError('too large to read (%d bytes)' % a.blocks[bi][2])
        data = mpqnames.read_unnamed(a, bi)
        if data is None:
            raise ValueError('block %d cannot be read without its name' % bi)
        return data, bi
    name = name.replace('/', '\\')
    bi = _game_block(a, name)
    if bi is None:
        raise LookupError('the map has no file named %s' % name)
    if a.blocks[bi][2] > READ_MAX:
        raise ValueError('too large to read (%d bytes)' % a.blocks[bi][2])
    with unprotect.quiet():
        data = a.read(name, bi=bi)
    if data is None:
        raise ValueError('%s cannot be read' % name)
    return data, bi


def _decodes(data, encoding):
    for cut in range(4):
        try:
            return data[:len(data) - cut].decode(encoding)
        except UnicodeDecodeError as e:
            if e.start < len(data) - 4:
                return None
        except LookupError:
            return None
    return None


def guess_encoding(data, script=False):
    sample = data[:1 << 20]
    if script and not sample.startswith((b'\xef\xbb\xbf', b'\xff\xfe', b'\xfe\xff')):
        text = b'\n'.join(RX_SCRIPT_TEXT.findall(data[:16 << 20]))[:1 << 20]
        if RX_HIGH_BYTE.search(text):
            sample = text
    if sample.startswith(b'\xef\xbb\xbf'):
        return 'utf-8-sig'
    if sample.startswith((b'\xff\xfe', b'\xfe\xff')):
        return 'utf-16'
    if _decodes(sample, 'utf-8') is not None:
        return 'utf-8'
    loose = sample.decode('utf-8', 'replace')
    bad = loose.count('\ufffd')
    if bad * 50 <= len(RX_NOT_ASCII.findall(loose)) - bad:
        return 'utf-8'
    pairs = low_trail = high_lead = rows = 0
    i, n = 0, len(sample)
    while i < n - 1:
        c = sample[i]
        if c >= 0x81 and c != 0xFF:
            t = sample[i + 1]
            pairs += 1
            low_trail += t < 0xA1
            if c >= 0xB0:
                rows += 1
                high_lead += c >= 0xC9
            i += 2
        else:
            i += 1
    ok = dict((e, _decodes(sample, e) is not None) for e in ('gbk', 'big5', 'euc-kr', 'cp949', 'cp1252'))
    if pairs and rows and high_lead <= 0.03 * rows and (ok['euc-kr'] or ok['cp949']):
        return 'euc-kr' if ok['euc-kr'] else 'cp949'
    if pairs and ok['big5'] and low_trail > 0.15 * pairs:
        return 'big5'
    if ok['gbk'] and (low_trail <= 0.5 * pairs or not ok['cp1252']):
        return 'gbk'
    for e in ('big5', 'cp949', 'cp1252'):
        if ok[e]:
            return e
    return min(('utf-8', 'gbk', 'cp949', 'big5', 'cp1252'), key=lambda e: sample.decode(e, 'replace').count('\ufffd'))


def line_endings(text):
    crlf = text.count('\r\n')
    cr, lf = text.count('\r') - crlf, text.count('\n') - crlf
    kinds = [k for k, n in (('crlf', crlf), ('lf', lf), ('cr', cr)) if n]
    return kinds[0] if len(kinds) == 1 else ('mixed' if kinds else 'none')


def decode_text(data, max_bytes=PREVIEW_MAX, script=False):
    encoding = guess_encoding(data, script)
    head = data[:max_bytes]
    text = _decodes(head, encoding)
    if text is None:
        text = head.decode(encoding, 'replace')
    ends = line_endings(text)
    return {'text': text.replace('\r\n', '\n').replace('\r', '\n'), 'encoding': encoding,
            'invalid': text.count('\ufffd'), 'line_endings': ends, 'truncated': len(data) > max_bytes,
            'size': len(data)}


def _hexdump(data, offset=0):
    lines = []
    for p in range(0, len(data), 16):
        row = data[p:p + 16]
        hexes = ' '.join('%02x' % c for c in row)
        text = ''.join(chr(c) if 32 <= c < 127 else '.' for c in row)
        lines.append('%08x  %-47s  |%s|' % (offset + p, hexes, text))
    return '\n'.join(lines)


def _hex(data, note=None, n=HEX_BYTES):
    out = {'kind': 'other', 'hex': _hexdump(data[:n]), 'hex_bytes': min(n, len(data)), 'size': len(data),
           'truncated': len(data) > n}
    if note:
        out['note'] = note
    return out


def _pixels(im, max_side, image_format):
    from PIL import Image
    im = im.convert('RGBA')
    source = im.size
    if max(im.size) > max_side:
        im = im.copy()
        im.thumbnail((max_side, max_side), Image.LANCZOS)
    out = {'width': im.size[0], 'height': im.size[1], 'source_width': source[0], 'source_height': source[1],
           'scaled': im.size != source}
    if image_format == 'png':
        buf = io.BytesIO()
        im.save(buf, 'PNG')
        out['data'], out['mime'] = _b64(buf.getvalue()), 'image/png'
    else:
        out['rgba'] = _b64(im.tobytes())
    return out


def _image(data, ext, max_bytes, max_side, image_format):
    from PIL import Image
    if data[:4] in (b'BLP1', b'BLP2'):
        import blpread
        info = blpread.header_bytes(data)
        mip = 0
        while (
            max(info['map_width'] >> mip, info['map_height'] >> mip) > max_side and mip < 15 and info['sizes'][mip + 1]
        ):
            mip += 1
        try:
            im, _info = blpread.le_bytes(data, mip, info)
        except Exception:
            im, _info = blpread.le_bytes(data, 0, info)
            mip = 0
        out = _pixels(im, max_side, image_format)
        out.update(source_width=info['map_width'], source_height=info['map_height'], format=info['format'], mip=mip,
                   mips=sum(1 for s in info['sizes'] if s), alpha_bits=info['alpha_bits'])
        out['scaled'] = (out['width'], out['height']) != (info['map_width'], info['map_height'])
        return out
    for magic, mime in IMAGE_MIME:
        if data.startswith(magic):
            im = Image.open(io.BytesIO(data))
            if len(data) <= max_bytes:
                return {'data': _b64(data), 'mime': mime, 'width': im.size[0], 'height': im.size[1],
                        'source_width': im.size[0], 'source_height': im.size[1], 'scaled': False,
                        'format': mime.split('/')[1].upper()}
            im.load()
            out = _pixels(im, max_side, image_format)
            out['format'] = mime.split('/')[1].upper()
            return out
    formats = {'.tga': ['TGA'], '.dds': ['DDS']}.get(ext) or (['DDS'] if data[:4] == b'DDS ' else ['TGA'])
    im = Image.open(io.BytesIO(data), formats=formats)
    im.load()
    out = _pixels(im, max_side, image_format)
    out['format'] = formats[0] + ('/' + im.mode if im.mode else '')
    return out


NODE_NAMES = {'BONE': 'bones', 'HELP': 'helpers', 'ATCH': 'attachments', 'CLID': 'collision shapes',
              'EVTS': 'event objects', 'LITE': 'lights', 'PREM': 'particle emitters', 'PRE2': 'particle emitters 2',
              'RIBB': 'ribbon emitters'}


def model_info(data, has_file=None):
    if data[:4] == b'MDLX':
        return _mdx_info(data, has_file)
    return _mdl_info(data, has_file)


def _texture(path, rid, has_file):
    return {'path': path, 'replaceable_id': rid, 'in_map': bool(path) and bool(has_file and has_file(path))}


def _mdx_info(data, has_file):
    import mdx_anim
    import mdx_tex
    import mdxcheck
    import mdxnodes
    _chunks, problem = mdxcheck.walk(data)
    info = {'format': 'MDX', 'version': None, 'name': '', 'textures': [], 'sequences': [], 'geosets': 0,
            'vertices': 0, 'materials': 0, 'nodes': {}, 'chunks': [], 'problem': problem}
    end = len(data)
    for tag, off, n in mdx_tex.le_chunks(data, 4, end):
        info['chunks'].append(tag)
        n = min(n, end - off)
        try:
            if tag == 'VERS':
                info['version'] = struct.unpack_from('<I', data, off)[0]
            elif tag == 'MODL':
                info['name'] = mdx_tex.cstr(data[off:off + 80])
            elif tag == 'TEXS':
                info['textures'] = [_texture(t['path'], t['repl'], has_file) for t in mdx_tex.le_texs(data, off, n)]
            elif tag == 'SEQS':
                info['sequences'] = [{'name': s['fname'], 'start': s['begin'], 'end': s['end_pos'],
                                      'looping': not s['laco']} for s in mdx_anim.le_seqs(data, off, n)]
            elif tag == 'GEOS':
                geos = mdx_tex.le_geos_materiais(data, off, n)
                info['geosets'] = len(geos)
                info['vertices'] = sum(nv for _m, nv in geos)
            elif tag == 'MTLS':
                info['materials'] = len(mdx_tex.le_mtls(data, off, n, info['version'] or 800))
            elif tag.encode('latin-1') in mdxnodes.NODE_CHUNKS:
                body = data[off:off + n]
                count = sum(1 for _e in mdxnodes.iter_entries(tag.encode('latin-1'), body))
                info['nodes'][NODE_NAMES.get(tag, tag)] = count
        except (struct.error, IndexError, ValueError) as e:
            info['problem'] = info['problem'] or '%s: %s' % (tag, e)
    return info


RX_MDL_TEXTURE = re.compile(r'Bitmap\s*\{([^{}]*)\}', re.S)
RX_MDL_SEQUENCE = re.compile(r'Anim\s+"([^"]*)"\s*\{(.*?)\n\s*\}', re.S)
MDL_NODES = (('Bone', 'bones'), ('Helper', 'helpers'), ('Attachment', 'attachments'), ('CollisionShape',
             'collision shapes'), ('EventObject', 'event objects'), ('Light', 'lights'), ('ParticleEmitter',
             'particle emitters'), ('ParticleEmitter2', 'particle emitters 2'), ('RibbonEmitter', 'ribbon emitters'))


def _mdl_info(data, has_file):
    text = decode_text(data, len(data))['text']
    info = {'format': 'MDL', 'version': None, 'name': '', 'textures': [], 'sequences': [], 'geosets': 0,
            'vertices': 0, 'materials': 0, 'nodes': {}, 'chunks': [], 'problem': None}
    m = re.search(r'FormatVersion\s+(\d+)', text)
    info['version'] = int(m.group(1)) if m else None
    m = re.search(r'(?m)^Model\s+"([^"]*)"', text)
    info['name'] = m.group(1) if m else ''
    if not m:
        info['problem'] = 'no Model block: this is not an MDL model'
    for body in RX_MDL_TEXTURE.findall(text):
        image = re.search(r'Image\s+"([^"]*)"', body)
        rid = re.search(r'ReplaceableId\s+(\d+)', body)
        info['textures'].append(_texture(image.group(1) if image else '', int(rid.group(1)) if rid else 0, has_file))
    for name, body in RX_MDL_SEQUENCE.findall(text):
        interval = re.search(r'Interval\s*\{\s*(-?\d+)\s*,\s*(-?\d+)', body)
        info['sequences'].append({'name': name, 'start': int(interval.group(1)) if interval else 0,
                                  'end': int(interval.group(2)) if interval else 0,
                                  'looping': 'NonLooping' not in body})
    info['geosets'] = len(re.findall(r'(?m)^Geoset\s*\{', text))
    info['vertices'] = sum(int(x) for x in re.findall(r'(?m)^\s*Vertices\s+(\d+)\s*\{', text))
    m = re.search(r'(?m)^Materials\s+(\d+)', text)
    info['materials'] = int(m.group(1)) if m else 0
    for block, label in MDL_NODES:
        count = len(re.findall(r'(?m)^%s\s+"' % block, text))
        if count:
            info['nodes'][label] = count
    info['chunks'] = sorted(set(re.findall(r'(?m)^([A-Z][A-Za-z0-9]+)\b', text)))
    return info


def _content_kind(name, data):
    if name.startswith('#'):
        return _sniff(data)
    ext = os.path.splitext(name)[1].lower()
    kind = kind_of(name)
    if kind == 'image' and ext in ('.blp', '.png', '.jpg', '.jpeg', '.gif', '.bmp') and \
            not data.startswith((b'BLP1', b'BLP2') + tuple(m for m, _t in IMAGE_MIME)):
        return 'other', ext
    if kind == 'image' and ext == '.dds' and not data.startswith(b'DDS '):
        return 'other', ext
    if kind == 'model' and ext == '.mdx' and not data.startswith(b'MDLX'):
        return 'other', ext
    if kind == 'sound' and not data.startswith(tuple(m for m, _e in SOUND_MAGIC)):
        return 'other', ext
    return kind, ext


def preview(path, name, max_bytes=PREVIEW_MAX, max_side=MAX_SIDE, image_format='rgba'):
    out = {'kind': None, 'name': name, 'size': None, 'block': None, 'error': None}
    try:
        a, _notes = _open(path)
        data, out['block'] = _read(a, name)
    except (Exception, SystemExit) as e:
        out['error'] = _error(e)
        return out
    out['size'] = len(data)
    kind, ext = _content_kind(name, data)
    out['kind'] = kind
    try:
        if kind == 'image':
            out.update(_image(data, ext, max_bytes, max_side, image_format))
        elif kind in ('text', 'script'):
            out.update(decode_text(data, max_bytes, script=kind == 'script'))
            if kind == 'script':
                out['language'] = SCRIPT_EXT.get(ext, 'jass')
        elif kind == 'sound':
            mime = next((SOUND_MIME[e] for m, e in SOUND_MAGIC if data.startswith(m)), SOUND_MIME.get(ext))
            out.update(data=_b64(data[:max_bytes]), mime=mime, truncated=len(data) > max_bytes)
        elif kind == 'model':
            out['info'] = model_info(data, lambda p: _game_block(a, p.replace('/', '\\')) is not None)
        else:
            out.update(_hex(data))
            out['kind'] = kind
    except Exception as e:
        out.update(_hex(data, 'cannot be shown as %s: %s' % (kind, _error(e))))
        out['wanted_kind'] = kind
    return out


RX_BAD_CHARS = re.compile(r'[<>:"|?*\x00-\x1f]')
RESERVED = frozenset(['CON', 'PRN', 'AUX', 'NUL'] + ['COM%d' % i for i in range(1, 10)] +
                     ['LPT%d' % i for i in range(1, 10)])


def safe_path(name, ext='.bin'):
    if name.startswith('#') and name[1:].isdigit():
        return os.path.join('unnamed', 'block_%06d%s' % (int(name[1:]), ext))
    parts = []
    for part in re.split(r'[\\/]+', name):
        part = RX_BAD_CHARS.sub('_', part).rstrip(' .')
        if not part or part in ('.', '..'):
            continue
        if part.split('.')[0].upper() in RESERVED:
            part = '_' + part
        parts.append(part)
    return os.path.join(*parts) if parts else '_'


def extract(path, names, out_dir, progress=None, overwrite=False):
    say = progress or _quiet
    out = {'out_dir': os.path.abspath(out_dir), 'written': [], 'same': [], 'exists': [], 'failed': [], 'folders': [],
           'error': None}
    try:
        a, _notes = _open(path)
        root = os.path.abspath(out_dir)
        os.makedirs(root, exist_ok=True)
    except (Exception, SystemExit) as e:
        out['error'] = _error(e)
        return out
    folders = {}
    names = list(names)
    for k, name in enumerate(names):
        say('Extracting %d of %d' % (k + 1, len(names)))
        try:
            data, _bi = _read(a, name)
            ext = _sniff(data)[1] if name.startswith('#') else ''
            rel = safe_path(name, ext)
            target = os.path.abspath(os.path.join(root, rel))
            if os.path.commonpath([root, target]) != root:
                raise ValueError('the name leaves the folder')
            item = {'name': name, 'path': os.path.relpath(target, root), 'size': len(data)}
            if os.path.exists(target) and not overwrite:
                with open(target, 'rb') as f:
                    (out['same'] if f.read() == data else out['exists']).append(item)
                continue
            os.makedirs(os.path.dirname(target), exist_ok=True)
            part = target + '.part'
            with open(part, 'wb') as f:
                f.write(data)
            os.replace(part, target)
            with open(target, 'rb') as f:
                if f.read() != data:
                    raise IOError('the file on disk does not read back the same')
            out['written'].append(item)
            folder = os.path.dirname(item['path'])
            while folder and folder.lower() not in folders:
                folders[folder.lower()] = folder
                folder = os.path.dirname(folder)
        except (Exception, SystemExit) as e:
            out['failed'].append({'name': name, 'reason': _error(e)})
    out['folders'] = sorted(folders.values(), key=lambda f: (f.lower(), f))
    return out


def _script_file(a):
    j_name = 'war3map.j' if a.find('war3map.j') else ('scripts\\war3map.j' if a.find('scripts\\war3map.j') else None)
    j = unprotect._read(a, 'war3map.j')
    if j is None:
        j = unprotect._read(a, 'scripts\\war3map.j')
    lua = a.find('war3map.lua')
    with unprotect.quiet():
        language = unprotect.language_from_w3i(unprotect._read(a, 'war3map.w3i'))
    if lua and (language == 1 or not j):
        return 'lua', 'war3map.lua', unprotect._read(a, 'war3map.lua'), '', None
    if j and unprotect.script_j2b(a, j):
        size = a.blocks[a.find(unprotect.J2B_FILE)[1]][2]
        return 'j2b', j_name, j, ('The real script is the compiled war3map.bin (%d bytes, encrypted bytecode); %s is '
                                  'the shell that loads it. Open in World Editor turns it back into JASS.'
                                  % (size, j_name)), {'name': unprotect.J2B_FILE, 'size': size}
    if j is not None and len(j) < 450 and a.find('kkmap.jc'):
        import kkwe
        try:
            loader = kkwe.is_loader(kkwe.Bytecode(kkwe.read_container(unprotect._read(a, 'kkmap.jc'))))[0]
        except Exception:
            loader = False
        size = a.blocks[a.find('kkmap.jc')[1]][2]
        if loader:
            return 'none', j_name, j, ('The map is encrypted by the KK platform: kkmap.jc only loads the real map, '
                                       'which is outside the MPQ. There is no script to show.'), \
                {'name': 'kkmap.jc', 'size': size}
        return 'kkwe', j_name, j, ('The real script is the KKWE bytecode in kkmap.jc (%d bytes); %s is a stub. Open '
                                   'in World Editor turns it back into JASS.' % (size, j_name)), \
            {'name': 'kkmap.jc', 'size': size}
    if j:
        return 'jass', j_name, j, '', None
    if a.find('war3campaign.w3f'):
        return 'none', None, None, 'This is a campaign: each map inside it has its own script.', None
    return 'none', None, None, 'The map has no script (war3map.j, scripts\\war3map.j or war3map.lua).', None


def script(path, max_bytes=SCRIPT_MAX):
    out = {'language': 'none', 'name': None, 'text': '', 'size': 0, 'encoding': None, 'truncated': False, 'note': '',
           'compiled': None, 'error': None}
    try:
        a, notes = _open(path)
        out['language'], out['name'], data, out['note'], out['compiled'] = _script_file(a)
        if data is not None:
            t = decode_text(data, max_bytes, script=True)
            out.update(text=t['text'], size=len(data), encoding=t['encoding'], line_endings=t['line_endings'],
                       truncated=t['truncated'], invalid=t['invalid'])
        if notes:
            out['note'] = ' '.join(notes + [out['note']]).strip()
    except (Exception, SystemExit) as e:
        out['error'] = _error(e)
    return out


WORLD_EDIT_STRINGS = 'war3.w3mod:_locales\\enus.w3mod:ui\\worldeditstrings.txt'
BRANCH_HEADINGS = {'IfThenElseMultiple': ('WESTRING_TRIGSUBFUNC_IFCONDITIONS', 'WESTRING_TRIGSUBFUNC_IFTHENACTIONS',
                                          'WESTRING_TRIGSUBFUNC_IFELSEACTIONS'),
                   'AndMultiple': ('WESTRING_TRIGSUBFUNC_ANDORCONDITIONS',),
                   'OrMultiple': ('WESTRING_TRIGSUBFUNC_ANDORCONDITIONS',)}
LOOP_HEADING = 'WESTRING_TRIGSUBFUNC_FORLOOPACTIONS'
FALLBACK_STRINGS = {'WESTRING_TRIGSUBFUNC_IFCONDITIONS': 'If - Conditions',
                    'WESTRING_TRIGSUBFUNC_IFTHENACTIONS': 'Then - Actions',
                    'WESTRING_TRIGSUBFUNC_IFELSEACTIONS': 'Else - Actions',
                    'WESTRING_TRIGSUBFUNC_ANDORCONDITIONS': 'Conditions', LOOP_HEADING: 'Loop - Actions'}
OBJECT_GLOBAL = re.compile(r'^gg_(unit|item|dest)_(.{4})_(\d+)$')
RX_TRIGSTR = re.compile(r'^TRIGSTR_0*(\d+)$')
_STRINGS = []


def editor_strings(td=None):
    if _STRINGS:
        return _STRINGS[0]
    import slk
    import triggerdata
    strings, raw = {}, None
    try:
        import casc_wc3
        casc = casc_wc3.CascWC3()
        try:
            strings = slk.parse_ini_bytes(casc.read_data(WORLD_EDIT_STRINGS)).get('WorldEditStrings', {})
            raw = casc.read_wc3(triggerdata.GAME_PATH)
        finally:
            casc.on_close()
    except Exception:
        pass
    if raw is None and os.path.isfile(triggerdata.DOCS_COPY):
        with open(triggerdata.DOCS_COPY, 'rb') as f:
            raw = f.read()
    hidden = {}
    if raw:
        for key, value in slk.parse_ini_bytes(raw).get('TriggerCategories', {}).items():
            fields = triggerdata._fields(value)
            hidden[key] = len(fields) > 2 and fields[2] == '1'
    _STRINGS.append((strings, hidden))
    return _STRINGS[0]


class _Display(object):
    def __init__(self, td, object_names, trigger_names, map_strings=None):
        self.td = td
        self.strings, self.hidden = editor_strings(td)
        self.objects = object_names or {}
        self.trigger_names = trigger_names
        self.map_strings = map_strings or {}

    def text(self, key):
        if not key:
            return ''
        if key.startswith('WESTRING_'):
            return self.strings.get(key) or FALLBACK_STRINGS.get(key) or key[9:].split('_')[-1].title()
        return key

    def function(self, kind, name):
        tables = [self.td.get(kind, name)] + [self.td.get(k, name) for k in (3, 2, 1, 0) if k != kind]
        return next((f for f in tables if f is not None), None)

    def line(self, f, top=True):
        tf = self.function(f.kind, f.name)
        if tf is None:
            return '%s(%s)' % (f.name, ', '.join(self.param(p, None) for p in f.params))
        import triggerdata
        layout = triggerdata._fields(tf.meta['Parameters']) if tf.meta.get('Parameters') else []
        if len(layout) > 1 and layout[0] == tf.display_name and not layout[0].startswith('~') and \
                any(x.startswith('~') for x in layout[1:]):
            layout = layout[1:]
        if not layout:
            layout = [tf.display_name or f.name]
        params, types = list(f.params), list(tf.arg_types)
        pieces, k = [], 0
        for piece in layout:
            if not piece.startswith('~'):
                pieces.append(piece)
                continue
            if k < len(params):
                pieces.append(self.param(params[k], types[k] if k < len(types) else None))
            else:
                pieces.append(piece[1:])
            k += 1
        if k < len(params):
            pieces.append(' ' + ', '.join(self.param(p, types[i + k] if i + k < len(types) else None)
                                          for i, p in enumerate(params[k:])))
        text = ''.join(pieces)
        category = tf.category
        if (top or tf.kind == 'action') and category and not self.hidden.get(category) and \
                category in self.td.categories:
            text = '%s - %s' % (self.text(self.td.categories[category][0]), text)
        return text

    def param(self, p, type_):
        import wtg
        if p is None:
            return ''
        if p.kind == wtg.PRESET:
            preset = self.td.presets.get(p.value)
            return self.text(preset.display) if preset is not None else p.value
        if p.kind == wtg.VARIABLE:
            text = self.variable(p.value)
            if p.index is not None:
                text += '[%s]' % self.param(p.index, 'integer')
            return text
        if p.kind == wtg.FUNCTION:
            return '(%s)' % self.line(p.function, top=False) if p.function is not None else p.value
        if p.kind == wtg.LITERAL:
            if type_ and type_ != 'string' and self.td.base_type(type_) == 'integer' and len(p.value) == 4 and \
                    type_ in self.td.types and type_ != 'integer':
                return self.objects.get(p.value, p.value)
            if type_ == 'boolean' and p.value in ('true', 'false'):
                return self.text('WESTRING_' + p.value.upper())
            m = RX_TRIGSTR.match(p.value)
            if m and int(m.group(1)) in self.map_strings:
                return self.map_strings[int(m.group(1))]
            return p.value
        return '(%s)' % (type_ or 'nothing')

    def variable(self, name):
        m = OBJECT_GLOBAL.match(name)
        if m:
            return '%s %s <gen>' % (self.objects.get(m.group(2), m.group(2)), m.group(3))
        if name.startswith('gg_trg_'):
            return '%s <gen>' % self.trigger_names.get(name[7:], name[7:].replace('_', ' '))
        for prefix in ('gg_rct_', 'gg_cam_', 'gg_snd_'):
            if name.startswith(prefix):
                return '%s <gen>' % name[len(prefix):].replace('_', ' ')
        return name

    def lines(self, functions, depth=0, out=None):
        import triggerdata
        out = [] if out is None else out
        for f in functions:
            out.append({'text': self.line(f), 'depth': depth, 'enabled': bool(f.enabled), 'function': f.name})
            branches = triggerdata.MULTIPLE.get(f.name)
            if branches is None and not f.children:
                continue
            branches = branches or ('action',)
            headings = BRANCH_HEADINGS.get(f.name) or (LOOP_HEADING,) * len(branches)
            for b in range(len(branches)):
                out.append({'text': self.text(headings[b]), 'depth': depth + 1, 'enabled': bool(f.enabled),
                            'function': None, 'heading': True})
                self.lines([c for c in f.children if (c.branch or 0) == b], depth + 2, out)
        return out


def _view(mt, texts, td, object_names, map_strings=None):
    import gui_render
    names = dict((gui_render.trigger_identifier(t.name), t.name) for t in mt.triggers)
    show = _Display(td, object_names, names, map_strings)
    categories, by_id = [], {}
    for c in mt.categories:
        item = {'name': c.name, 'comment': bool(c.is_comment), 'triggers': []}
        categories.append(item)
        by_id.setdefault(c.id, item)
    counts = {'triggers': 0, 'gui': 0, 'text': 0, 'comments': 0, 'disabled': 0, 'lines': 0}
    for i, t in enumerate(mt.triggers):
        text = texts[i] if i < len(texts) else None
        item = {'name': t.name, 'enabled': bool(t.enabled), 'description': t.description,
                'initially_off': bool(t.initially_off), 'run_on_init': bool(t.run_on_init)}
        if t.is_comment:
            item.update(kind='text', comment=True, text=t.description)
            counts['comments'] += 1
        elif t.is_text:
            item.update(kind='text', comment=False, text=(text or '').replace('\r\n', '\n'))
            counts['text'] += 1
        else:
            item.update(kind='gui', comment=False,
                        events=show.lines([f for f in t.functions if f.kind == 0]),
                        conditions=show.lines([f for f in t.functions if f.kind == 1]),
                        actions=show.lines([f for f in t.functions if f.kind == 2]))
            counts['gui'] += 1
            counts['lines'] += len(item['events']) + len(item['conditions']) + len(item['actions'])
        counts['triggers'] += 1
        counts['disabled'] += not t.enabled
        target = by_id.get(t.category_id)
        if target is None:
            target = {'name': 'Triggers', 'comment': False, 'triggers': []}
            categories.append(target)
            by_id[t.category_id] = target
        target['triggers'].append(item)
    variables = []
    for v in mt.variables:
        t = td.types.get(v.type)
        variables.append({'name': v.name, 'type': v.type, 'type_display': show.text(t.display) if t else v.type,
                          'array': bool(v.is_array), 'size': v.array_size if v.is_array else 1,
                          'initial': v.initial_value if v.initialized else ''})
    counts['variables'] = len(variables)
    counts['categories'] = len(categories)
    return categories, variables, counts


def _object_names(a):
    import object_names
    try:
        with unprotect.quiet():
            return object_names.names(lambda n: unprotect._read(a, n))
    except Exception:
        return {}


def _restore(a, language, raw, td, fit, object_names_):
    import editor_prep
    import trigger_restore
    text = raw.decode('latin-1').replace('\r\n', '\n').replace('\r', '\n')
    bom = text.startswith('\xef\xbb\xbf')
    if bom:
        text = text[3:]
    files = None
    if fit:
        files = dict((n, unprotect._read(a, n)) for n in editor_prep.EDITOR_FILE_NAMES if a.find(n))
        files = dict((n, d) for n, d in files.items() if d is not None)
    with unprotect.quiet():
        if language == 'lua':
            res = trigger_restore.restore(raw[3:] if bom else raw, 'lua', td=td, editor_files=files)
        else:
            doo = unprotect._read(a, 'war3map.doo')
            text, standard, players = editor_prep.to_standard_script(
                text, unprotect._read(a, 'war3map.w3i'), _quiet, doo
            )
            res = trigger_restore.restore(text.encode('latin-1'), 'jass', td=td, editor_files=files, players=players,
                                          standard=standard, object_names=lambda: object_names_)
    return res, text


def _custom_script_alone(text, language):
    import editor_prep
    try:
        if language == 'lua':
            return editor_prep.custom_script_lua(text)
        return editor_prep.custom_script(text)[0].replace('\r\n', '\n')
    except Exception:
        return text


def _cut(text, max_chars):
    text = text or ''
    return {'text': text[:max_chars], 'size': len(text), 'truncated': len(text) > max_chars}


def triggers(path, progress=None, fit=True, max_chars=SCRIPT_MAX):
    say = progress or _quiet
    started = time.time()
    out = {'source': 'none', 'reason': '', 'notes': [], 'language': None, 'categories': [], 'variables': [],
           'custom_script': None, 'counts': {}, 'restore': None, 'seconds': {}, 'error': None}
    try:
        say('Reading the map')
        a, notes = _open(path)
        out['notes'] = list(notes)
        say('Reading the trigger editor data')
        import triggerdata
        import wtg
        try:
            td = triggerdata.load()
        except Exception as e:
            out['reason'] = ("The trigger editor's data (TriggerData.txt) cannot be read: Warcraft III is not "
                             "installed or its files cannot be read (%s)." % _error(e))
            return out
        if 'cannot be read' in (td.source or ''):
            out['notes'].append("Warcraft III's files cannot be read: the archive's copy of TriggerData.txt is used.")
        language, _name, raw, script_note, _compiled = _script_file(a)
        out['language'] = language
        mt = texts = header = None
        wtg_b, wct_b = unprotect._read(a, 'war3map.wtg'), unprotect._read(a, 'war3map.wct')
        if wtg_b and wct_b:
            say('Reading the map triggers')
            try:
                mt, ct = wtg.read_wtg(wtg_b, td), wtg.read_wct(wct_b)
                if mt.sub_version is not None:
                    ct = wtg.to_classic_wct(ct, mt)
                    mt = wtg.to_classic(mt)
                texts, header = wtg.trigger_texts(mt, ct), ct.header
                out['source'] = 'map'
            except Exception as e:
                mt = None
                out['notes'].append("The map's own trigger files cannot be read by the World Editor 3.0 (%s): Open in "
                                    "World Editor rebuilds them from the script." % _error(e)[:200])
        out['seconds']['read'] = round(time.time() - started, 2)
        objects = None
        if mt is None:
            if language in ('kkwe', 'j2b'):
                out['reason'] = ('The script is compiled (%s): Open in World Editor turns it back into JASS first; the '
                                 'triggers can be shown from that map.' % ('KKWE bytecode' if language == 'kkwe' else
                                                                          'j2b bytecode'))
                return out
            if language == 'none' or raw is None:
                out['reason'] = script_note or 'The map has no script to restore triggers from.'
                return out
            say('Reading the object names')
            objects = _object_names(a)
            say('Restoring the triggers from the script')
            t0 = time.time()
            res, text = _restore(a, language, raw, td, fit, objects)
            out['seconds']['restore'] = round(time.time() - t0, 2)
            import trigger_restore
            ok, reason, _w, _c, _h, rep, proofs, summary = trigger_restore.outcome(res)
            out['restore'] = {'ok': ok, 'reason': reason, 'gui': rep.get('gui', 0), 'text': len(rep.get('text', ())),
                              'gui_clean': rep.get('gui_clean', 0), 'variables': rep.get('variables', 0),
                              'failed_proofs': sorted(k for k, v in proofs.items() if not v), 'summary': summary}
            if reason or not ok:
                out['reason'] = ('No trigger can be restored from the script (%s): Open in World Editor puts the whole '
                                 'script in the custom script.' % reason if reason else
                                 'The restored triggers did not pass every proof (%s): Open in World Editor puts the '
                                 'whole script in the custom script.' % ', '.join(out['restore']['failed_proofs']))
                out['custom_script'] = _cut(_custom_script_alone(text, language), max_chars)
                return out
            mt = res.triggers
            ct = wtg.read_wct(res.wct)
            texts, header = list(ct.texts), res.header
            out['source'] = 'restored'
        say('Building the trigger lines')
        t0 = time.time()
        if objects is None:
            objects = _object_names(a)
        import object_names
        wts = object_names.strings(unprotect._read(a, 'war3map.wts'))
        out['categories'], out['variables'], out['counts'] = _view(mt, texts, td, objects, wts)
        out['custom_script'] = _cut((header or '').replace('\r\n', '\n'), max_chars)
        out['seconds']['display'] = round(time.time() - t0, 2)
    except (Exception, SystemExit) as e:
        out['error'] = _error(e)
        out['source'] = 'none'
    finally:
        out['seconds']['total'] = round(time.time() - started, 2)
    return out
