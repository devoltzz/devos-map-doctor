# Checks BLP textures: headers, mipmaps past the end of file, sizes an older game refuses.
import io
import struct



MIP_LEVELS = 16
HEADER = 156
PALETTE = 1024


def _levels(w, h):
    n = 1
    while w > 1 or h > 1:
        w, h = max(w >> 1, 1), max(h >> 1, 1)
        n += 1
    return n


def _issue(code, level, text, **data):
    return dict(data, code=code, level=level, text=text)


def _game_key(version):
    if not version:
        return None
    from doctor.data import wc3_versions
    v = wc3_versions.normalize(version)
    if not v or v == wc3_versions.REFORGED:
        return None
    return wc3_versions._key(v)


def inspect(data):
    data = bytes(data)
    if len(data) < HEADER + 4:
        raise ValueError('too short for a BLP (%d bytes)' % len(data))
    magic = data[:4]
    if magic not in (b'BLP0', b'BLP1', b'BLP2'):
        raise ValueError('not a BLP (it starts with %r)' % magic)
    if magic == b'BLP2':
        content = struct.unpack_from('<I', data, 4)[0]
        _enc, alpha, _sample, mips = struct.unpack_from('<BBBB', data, 8)
        w, h = struct.unpack_from('<II', data, 12)
        offsets = struct.unpack_from('<16I', data, 20)
        sizes = struct.unpack_from('<16I', data, 84)
        return dict(version=2, content=content, alpha_bits=alpha, width=w, height=h, has_mips=mips, offsets=offsets,
                    sizes=sizes, jpeg_header=0, data_at=148 + 1024)
    content, alpha, w, h, extra, mips = struct.unpack_from('<6I', data, 4)
    offsets = struct.unpack_from('<16I', data, 28)
    sizes = struct.unpack_from('<16I', data, 92)
    jh = struct.unpack_from('<I', data, HEADER)[0] if content == 0 else 0
    info = dict(version=int(magic[3:]), content=content, alpha_bits=alpha, width=w, height=h, has_mips=mips,
                offsets=offsets, sizes=sizes, jpeg_header=jh)
    info['data_at'] = HEADER + 4 + (jh if content == 0 else PALETTE)
    return info


def _jpeg_size(data, info, i):
    from PIL import Image
    h0 = HEADER + 4
    jpg = data[h0:h0 + info['jpeg_header']] + data[info['offsets'][i]:info['offsets'][i] + info['sizes'][i]]
    try:
        with Image.open(io.BytesIO(jpg)) as im:
            return im.size
    except Exception:
        return None


def _jpeg_alpha_opaque(data, info, i):
    from PIL import Image
    h0 = HEADER + 4
    jpg = data[h0:h0 + info['jpeg_header']] + data[info['offsets'][i]:info['offsets'][i] + info['sizes'][i]]
    try:
        with Image.open(io.BytesIO(jpg)) as im:
            if len(im.getbands()) != 4:
                return None
            lo, hi = im.getchannel(3).getextrema()
    except Exception:
        return None
    return lo == hi


def check(data, version=None):
    data = bytes(data)
    if data[:4] == b'BLX1':
        return []
    try:
        info = inspect(data)
    except (ValueError, struct.error) as e:
        return [_issue('blp_unreadable', 'warning', 'The texture header does not parse (%s).' % e)]
    out = []
    n, w, h = len(data), info['width'], info['height']
    game = _game_key(version)
    content, alpha_bits = info['content'], info['alpha_bits']
    jh = info['jpeg_header']
    if info['version'] == 2:
        for i, (off, size) in enumerate(zip(info['offsets'], info['sizes'])):
            if size and off + size > n:
                out.append(
                    _issue('blp_mip_past_eof', 'warning', 'Mip level %d runs past the end of the file.' % i, mip=i)
                )
                break
        return out
    if content not in (0, 1):
        out.append(
            _issue('blp_alpha_bits', 'warning', 'Unknown content type %d: the game reads it as a JPEG.' % content)
        )
    if content == 0 and alpha_bits not in (0, 8):
        out.append(_issue('blp_alpha_bits', 'info', 'A JPEG texture with %d alpha bits (it can only have 0 or 8; the '
                          'specification says to read it as 0, not measured in the game).' % alpha_bits,
                          alpha_bits=alpha_bits))
    elif content == 1 and alpha_bits not in (0, 1, 4, 8):
        out.append(_issue('blp_alpha_bits', 'warning', 'A paletted texture with %d alpha bits (0, 1, 4 or 8 only).'
                          % alpha_bits, alpha_bits=alpha_bits))
    past = (HEADER + 4 + jh > n) if content == 0 else (HEADER + 4 + PALETTE > n)
    if past:
        out.append(_issue('blp_header_past_eof', 'warning',
                          'The %s runs past the end of the file: the game reads outside its buffer (Dr Super Good\'s '
                          'BLP specification; not measured here).' % ('JPEG header' if content == 0 else 'palette')))
    if content == 0 and jh > 624:
        out.append(_issue('blp_jpeg_header_big', 'warning',
                          'The JPEG header is %d bytes; above 624 the game 1.27b is "prone to image corruption and '
                          'crashes" (Dr Super Good\'s BLP specification; not measured here).' % jh, size=jh))
    expect = min(_levels(w, h), MIP_LEVELS) if info['has_mips'] else 1
    present = [i for i in range(MIP_LEVELS) if info['sizes'][i]]
    beyond = [i for i in present if info['offsets'][i] + info['sizes'][i] > n]
    if beyond:
        out.append(_issue('blp_mip_past_eof', 'warning',
                          'Mip level %d starts or ends past the end of the file: the game reads outside its buffer '
                          '(Dr Super Good\'s BLP specification; not measured here).' % beyond[0], mips=beyond))
    missing = [i for i in range(expect) if not info['sizes'][i]]
    if info['has_mips'] and missing:
        out.append(
            _issue(
                'blp_mip_chain',
                'warning',
                'The texture has mipmaps but %d of its %d levels are empty (first: %d): the game draws a missing '
                'level as transparent black (Dr Super Good\'s BLP specification).' % (len(missing), expect, missing[0]),
                missing=missing,
                expected=expect,
            )
        )
    elif not info['has_mips'] and len(present) > 1:
        out.append(_issue('blp_mip_chain', 'info', 'The texture says it has no mipmaps but stores %d levels.'
                          % len(present), levels=len(present)))
    if not info['sizes'][0]:
        if not info['has_mips'] or not missing:
            out.append(_issue('blp_mip_chain', 'warning', 'The full size level (0) is empty.'))
    fake = [i for i in present if info['offsets'][i] in [info['offsets'][j] for j in present if j < i]]
    if fake:
        out.append(
            _issue(
                'blp_mip_fake',
                'info',
                '%d mip levels share the data of another one (a "fake" mipmap: not valid by the specification, '
                'but the game\'s own icons do it; mdx-m3-viewer\'s BLP sanity test).' % len(fake),
                mips=fake,
            )
        )
    wrong, short = [], []
    for i in present:
        if i in beyond or i in fake or i >= expect:
            continue
        lw, lh = max(w >> i, 1), max(h >> i, 1)
        if content == 0:
            dims = _jpeg_size(data, info, i)
            if dims is None:
                short.append((i, 'the JPEG of level %d does not decode' % i))
            elif dims != (lw, lh):
                wrong.append((i, 'the JPEG of level %d is %dx%d, the level is %dx%d' % (i, dims[0], dims[1], lw, lh)))
        else:
            px = lw * lh
            need = px + (px * alpha_bits + 7) // 8
            if info['sizes'][i] < need:
                short.append((i, 'level %d declares %d bytes, its %dx%d pixels need %d' % (
                    i, info['sizes'][i], lw, lh, need)))
            elif info['sizes'][i] > need:
                wrong.append((i, 'level %d declares %d bytes, its %dx%d pixels need %d' % (
                    i, info['sizes'][i], lw, lh, need)))
    if short:
        out.append(_issue('blp_mip_size', 'warning',
                          '%d mip levels cannot be read as they are (%s): the game reads the bytes the level needs, '
                          'whatever it declares, so it can read outside the level (Dr Super Good\'s BLP specification; '
                          'not measured here).' % (len(short), short[0][1]), mips=[i for i, _t in short]))
    if wrong:
        out.append(_issue('blp_mip_size', 'info',
                          '%d mip levels are not the size they claim (%s): the game crops or pads a JPEG level (older '
                          'Mac builds stop with a fatal error); common in textures made by other tools.'
                          % (len(wrong), wrong[0][1]), mips=[i for i, _t in wrong]))
    big = w > 512 or h > 512
    if big and game is not None and game < (1, 27, 2):
        out.append(_issue('blp_too_big', 'warning',
                          'The texture is %dx%d: before patch 1.27b the game does not support a side above 512 pixels '
                          '(Dr Super Good\'s BLP specification).' % (w, h), width=w, height=h))
    elif big and game is not None and game < (1, 29, 0):
        out.append(_issue('blp_mip_over_512', 'info',
                          'The texture is %dx%d: before patch 1.29 the largest level the game uses is 512 pixels, the '
                          'rest is dead weight.' % (w, h), width=w, height=h))
    if content == 0 and alpha_bits == 0 and present and not beyond:
        last = max(i for i in present if i < expect or i == 0)
        flat = _jpeg_alpha_opaque(data, info, last)
        if flat is False:
            out.append(
                _issue(
                    'blp_jpeg_alpha',
                    'info',
                    'A JPEG texture with 0 alpha bits whose alpha band is not flat: the game still blends model '
                    'textures with it (Dr Super Good\'s BLP specification asks for 0xFF).',
                )
            )
    return out


def summary(result, version=None):
    files = {}
    for f in result.get('files') or ():
        for i in f['issues']:
            files.setdefault((i['code'], i['level']), []).append(f['file'])

    def names(*keys):
        seen = []
        for k in keys:
            for n in files.get(k, ()):
                if n not in seen:
                    seen.append(n)
        return seen
    out = []
    bounds = names(
        ('blp_header_past_eof', 'warning'),
        ('blp_mip_past_eof', 'warning'),
        ('blp_jpeg_header_big', 'warning'),
        ('blp_mip_chain', 'warning'),
        ('blp_mip_size', 'warning'),
        ('blp_unreadable', 'warning'),
        ('blp_alpha_bits', 'warning'),
    )
    if bounds:
        out.append(
            {
                'code': 'texture_bounds',
                'severity': 'warning',
                'files': bounds[:30],
                'count': len(bounds),
                'text': '%d textures have a header or mip levels past the end of the file, a JPEG header above 624 '
                'bytes, missing mip levels or a header that does not parse: the game reads outside its buffer '
                'or draws the missing level transparent black (Dr Super Good\'s BLP specification; not '
                'measured here).' % len(bounds),
            }
        )
    big = names(('blp_too_big', 'warning'))
    if big:
        out.append(
            {
                'code': 'texture_too_big',
                'severity': 'warning',
                'files': big[:30],
                'count': len(big),
                'text': '%d textures have a side above 512 pixels: the specification says the game before patch 1.27b does not support '
                'them.' % len(big),
            }
        )
    odd = names(
        ('blp_mip_fake', 'info'),
        ('blp_mip_size', 'info'),
        ('blp_alpha_bits', 'info'),
        ('blp_jpeg_alpha', 'info'),
        ('blp_mip_over_512', 'info'),
        ('blp_mip_chain', 'info'),
    )
    if odd:
        out.append(
            {
                'code': 'texture_odd',
                'severity': 'info',
                'files': odd[:30],
                'count': len(odd),
                'text': '%d textures are not made the way the specification asks (shared or off-size mip levels, an '
                'unusual alpha depth, a level above 512 pixels); the game\'s own icons do some of it.' % len(odd),
            }
        )
    return out


def scan_map(path, version=None, progress=None):
    from doctor.models import model_check
    p = progress or (lambda *_a, **_k: None)
    out = {'checked': 0, 'files': [], 'by_code': {}, 'skipped': []}
    p('Reading the map')
    a, err = model_check._open(path)
    if a is None:
        out['error'] = err
        return out
    p('Finding the file names')
    names = [n for n in model_check._names(a) if n.lower().endswith('.blp')]
    seen = set()
    for k, n in enumerate(names):
        if k % 100 == 0:
            p('Checking textures %d/%d' % (k, len(names)))
        try:
            r = a.find_locale(n) if a.find(n) else None
        except Exception:
            r = None
        if r is None or r[1] in seen:
            continue
        seen.add(r[1])
        from doctor.fix import unprotect
        data = unprotect._read(a, n)
        if data is None:
            out['skipped'].append({'file': n, 'reason': 'cannot be read'})
            continue
        issues = check(data, version)
        out['checked'] += 1
        if issues:
            out['files'].append({'file': n, 'issues': issues})
            for code in sorted(set(i['code'] for i in issues)):
                out['by_code'].setdefault(code, []).append(n)
    p('Done')
    return out
