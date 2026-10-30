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
    info['data_at'] = HEADER + 4 + jh if content == 0 else HEADER + PALETTE
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


def _jpeg_decodes(data, info, i):
    from PIL import Image
    h0 = HEADER + 4
    jpg = data[h0:h0 + info['jpeg_header']] + data[info['offsets'][i]:info['offsets'][i] + info['sizes'][i]]
    try:
        with Image.open(io.BytesIO(jpg)) as im:
            im.load()
        return True
    except Exception:
        return False


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
    stray = [i for i in range(MIP_LEVELS) if not info['sizes'][i] and info['offsets'][i] > n]
    if beyond or stray:
        first = min(beyond + stray)
        out.append(_issue('blp_mip_past_eof', 'warning',
                          'Mip level %d %s past the end of the file: the game reads outside its buffer '
                          '(Dr Super Good\'s BLP specification; not measured here).'
                          % (first, 'starts or ends' if first in beyond else 'is empty but its offset points'),
                          mips=sorted(beyond + stray)))
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
    if content == 0:
        junk = [i for i in present if i >= expect and i not in beyond and i not in fake
                and not _jpeg_decodes(data, info, i)]
        if junk:
            out.append(
                _issue(
                    'blp_mip_extra',
                    'info',
                    'Mip level %d lies beyond the %d-level chain and its JPEG does not decode: the engine most '
                    'likely never reads it (not measured; `fix` drops it).' % (junk[0], expect),
                    mips=junk,
                )
            )
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
        last = max((i for i in present if i < expect or i == 0), default=0)
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


def fix(data):
    data = bytes(data)
    info = inspect(data)
    if info['version'] != 1:
        raise ValueError('only BLP1 (the game\'s format) is repaired')
    n = len(data)
    expect = min(_levels(info['width'], info['height']), MIP_LEVELS) if info['has_mips'] else 1
    jpeg = info['content'] == 0
    for i in range(expect):
        off, size = info['offsets'][i], info['sizes'][i]
        if size and (off + size > n or (jpeg and not _jpeg_decodes(data, info, i))):
            raise ValueError('level %d of the chain cannot be read: not repairable by cutting the tail' % i)
    dropped = [i for i in range(expect, MIP_LEVELS)
               if (info['offsets'][i] or info['sizes'][i])
               and (info['offsets'][i] + info['sizes'][i] > n
                    or (jpeg and info['sizes'][i] and not _jpeg_decodes(data, info, i)))]
    out = dict(dropped=dropped, cut=0, size_before=n, size_after=n)
    if not dropped:
        return data, out
    offs, sizes = list(info['offsets']), list(info['sizes'])
    for i in dropped:
        offs[i] = sizes[i] = 0
    end = max([info['data_at']] + [o + s for o, s in zip(offs, sizes) if s])
    body = bytearray(data[:end])
    struct.pack_into('<16I', body, 28, *offs)
    struct.pack_into('<16I', body, 92, *sizes)
    new = bytes(body)
    again = inspect(new)
    for i in range(expect):
        if again['offsets'][i] != info['offsets'][i] or again['sizes'][i] != info['sizes'][i]:
            raise ValueError('level %d moved' % i)
        a = data[info['offsets'][i]:info['offsets'][i] + info['sizes'][i]]
        b = new[again['offsets'][i]:again['offsets'][i] + again['sizes'][i]]
        if a != b:
            raise ValueError('level %d changed' % i)
        if jpeg and info['sizes'][i] and not _jpeg_decodes(new, again, i):
            raise ValueError('level %d no longer decodes' % i)
    left = [c['code'] for c in check(new) if c['code'] in ('blp_mip_past_eof', 'blp_mip_extra')]
    if left:
        raise ValueError('the repair did not hold: %s' % ', '.join(left))
    out.update(cut=n - len(new), size_after=len(new))
    return new, out


def _nearest_power_of_two(n):
    if n <= 1:
        return 1
    lo = 1 << (n.bit_length() - 1)
    return lo if n - lo <= (lo << 1) - n else lo << 1


def power_of_two(data, quality=90):
    data = bytes(data)
    info = inspect(data)
    w, h = info['width'], info['height']
    to = (_nearest_power_of_two(w), _nearest_power_of_two(h))
    out = {'from': (w, h), 'to': to, 'size_before': len(data), 'size_after': len(data)}
    if info['version'] != 1 or to == (w, h):
        return None, out
    from doctor.models import blpread
    from doctor.models import blpwrite
    from PIL import Image
    try:
        im = blpread.read_bytes(data, 0, None, '<bytes>')[0]
    except Exception as e:
        raise ValueError('the texture does not decode: %s' % e)
    if im.size != (w, h):
        raise ValueError('level 0 decodes as %dx%d, the header says %dx%d' % (im.size + (w, h)))
    extra = struct.unpack_from('<I', data, 20)[0]
    im = im.convert('RGBA')
    alpha = 8 if info['alpha_bits'] and im.getextrema()[3][0] < 250 else 0
    _n, new = blpwrite.blp_jpeg_bytes(im.resize(to, Image.LANCZOS), quality=quality, alpha_bits=alpha, extra=extra)
    again = inspect(new)
    if (again['width'], again['height']) != to or blpread.read_bytes(new, 0, None, '<bytes>')[0].size != to:
        raise ValueError('the new texture is not %dx%d' % to)
    left = [c['code'] for c in check(new) if c['level'] == 'warning' or c['code'] == 'blp_mip_size']
    if left:
        raise ValueError('the new texture still has: %s' % ', '.join(left))
    out['size_after'] = len(new)
    return new, out


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
        ('blp_mip_extra', 'info'),
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
        try:
            issues = check(data, version)
        except Exception as e:
            out['skipped'].append({'file': n, 'reason': 'the check failed (%s: %s)' % (type(e).__name__, e)})
            continue
        out['checked'] += 1
        if issues:
            out['files'].append({'file': n, 'issues': issues})
            for code in sorted(set(i['code'] for i in issues)):
                out['by_code'].setdefault(code, []).append(n)
    p('Done')
    return out
