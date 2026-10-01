# Reads BLP textures (JPEG and palettized, every mip level).
import io
import os
import struct

import numpy as np
from PIL import Image


MAGICOS = (b'BLP1', b'BLP2')


class BLPError(Exception):
    pass


def header_text(path):
    with open(path, 'rb') as f:
        d = f.read(1024)
    return header_bytes(d, path, os.path.getsize(path))


def header_bytes(d, path='<bytes>', byte_size=None):
    byte_size = len(d) if byte_size is None else byte_size
    d = d[:1024]
    if len(d) < 160:
        raise BLPError('%s: too short to be a BLP (%d bytes)' % (path, len(d)))
    magic = d[:4]
    if magic not in MAGICOS:
        raise BLPError('%s: magic %r is neither BLP1 nor BLP2' % (path, magic))
    if magic == b'BLP1':
        compr, alpha, w, h, kind, mips = struct.unpack_from('<IIIIII', d, 4)
        offs = struct.unpack_from('<16I', d, 28)
        sizes = struct.unpack_from('<16I', d, 92)
        jh = struct.unpack_from('<I', d, 156)[0]
        info = dict(version_num=1, compression=compr, alpha_bits=alpha, map_width=w, map_height=h,
                    kind=kind, mips=mips, offsets=offs, sizes=sizes, jpeg_header=jh,
                    data_em=160 + jh)
    else:
        compr, alpha, atipo, mips = struct.unpack_from('<BBBB', d, 4)
        w, h = struct.unpack_from('<II', d, 8)
        offs = struct.unpack_from('<16I', d, 12)
        sizes = struct.unpack_from('<16I', d, 76)
        info = dict(version_num=2, compression=compr, alpha_bits=alpha, alpha_type=atipo,
                    map_width=w, map_height=h, kind=atipo, mips=mips, offsets=offs, sizes=sizes,
                    jpeg_header=0, data_em=148)
    if not (0 < info['map_width'] <= 8192 and 0 < info['map_height'] <= 8192):
        raise BLPError('%s: dimensoes implausiveis %dx%d' % (path, info['map_width'], info['map_height']))
    info['file_name'] = path
    info['bytes'] = byte_size
    info['format'] = _name_format(info)
    return info


def _name_format(info):
    if info['version_num'] == 1:
        if info['compression'] == 0:
            return 'BLP1/JPEG'
        if info['compression'] == 1:
            return 'BLP1/paletted'
        return 'BLP1/compr=%d (desconhecido)' % info['compression']
    if info['compression'] == 1:
        return 'BLP2/paletted'
    if info['compression'] == 2:
        return {0: 'BLP2/DXT1', 1: 'BLP2/DXT3', 7: 'BLP2/DXT5'}.get(
            info.get('alpha_type'), 'BLP2/DXT?=%d' % info.get('alpha_type', -1))
    if info['compression'] == 3:
        return 'BLP2/BGRA'
    return 'BLP2/compr=%d (desconhecido)' % info['compression']


def _data_bytes(d, info, mip=0, path='<bytes>'):
    off, sz = info['offsets'][mip], info['sizes'][mip]
    if sz == 0:
        raise BLPError('%s: mipmap %d vazio' % (path, mip))
    return d[off:off + sz]


def _jpeg_blp_para_rgba(jpg, w, h, tem_alpha):
    im = Image.open(io.BytesIO(jpg))
    im.load()
    if im.mode == 'CMYK':
        raw_bytes = np.frombuffer(im.tobytes(), dtype=np.uint8).reshape(im.size[1], im.size[0], 4)
        b = 255 - raw_bytes[:, :, 0]
        g = 255 - raw_bytes[:, :, 1]
        r = 255 - raw_bytes[:, :, 2]
        a = 255 - raw_bytes[:, :, 3]
    elif im.mode == 'RGB':
        raw_bytes = np.frombuffer(im.tobytes(), dtype=np.uint8).reshape(im.size[1], im.size[0], 3)
        r, g, b = raw_bytes[:, :, 0], raw_bytes[:, :, 1], raw_bytes[:, :, 2]
        a = np.full(r.shape, 255, np.uint8)
    else:
        rgba = im.convert('RGBA')
        return rgba, False
    if not tem_alpha:
        a = np.full(r.shape, 255, np.uint8)
    out = np.dstack([r, g, b, a]).astype(np.uint8)
    if im.size != (w, h):
        out = np.array(Image.fromarray(out, 'RGBA').resize((w, h), Image.LANCZOS))
    return Image.fromarray(out, 'RGBA'), True


def _palette(d, base):
    words = np.frombuffer(d, dtype=np.uint8, count=1024, offset=base).reshape(256, 4)
    return words[:, [2, 1, 0, 3]].copy()


def _alpha_separate(d, base, w, h, bits):
    if bits == 0:
        return None
    if bits == 8:
        return np.frombuffer(d, dtype=np.uint8, count=w * h, offset=base).reshape(h, w)
    if bits == 1:
        n = ((w + 7) // 8) * h
        bits1 = np.unpackbits(np.frombuffer(d, dtype=np.uint8, count=n, offset=base))
        return (bits1[:w * h].reshape(h, w) * 255).astype(np.uint8)
    if bits == 4:
        n = (w * h + 1) // 2
        b4 = np.frombuffer(d, dtype=np.uint8, count=n, offset=base)
        alto = (b4 >> 4) & 0x0F
        baixo = b4 & 0x0F
        inter = np.empty(n * 2, np.uint8)
        inter[0::2] = alto
        inter[1::2] = baixo
        return (inter[:w * h].reshape(h, w) * 17).astype(np.uint8)
    raise BLPError('alphaBits %d not supported in a palettized BLP' % bits)


def _paletted_bytes(d, info, mip, base_pal):
    w, h = info['map_width'], info['map_height']
    for n in range(mip):
        w, h = max(1, w // 2), max(1, h // 2)
    words = _palette(d, base_pal)
    idx = np.frombuffer(d, dtype=np.uint8, count=w * h, offset=info['offsets'][mip]).reshape(h, w)
    rgba = words[idx]
    alfa = _alpha_separate(d, info['offsets'][mip] + w * h, w, h, info['alpha_bits'])
    if alfa is not None:
        rgba = rgba.copy()
        rgba[:, :, 3] = alfa
    return Image.fromarray(np.ascontiguousarray(rgba), 'RGBA')


def _colors_dxt(c0, c1, com_alpha):
    def expande(v):
        r = (v >> 11) & 0x1F
        g = (v >> 5) & 0x3F
        b = v & 0x1F
        return np.array([(r * 255 + 15) // 31, (g * 255 + 31) // 63, (b * 255 + 15) // 31], np.float32)

    a = expande(c0)
    b = expande(c1)
    colors = np.zeros((4, 3), np.float32)
    colors[0] = a
    colors[1] = b
    if c0 > c1 or not com_alpha:
        colors[2] = (2 * a + b) / 3.0
        colors[3] = (a + 2 * b) / 3.0
    else:
        colors[2] = (a + b) / 2.0
        colors[3] = 0.0
    return colors, (c0 <= c1 and com_alpha)


def _blocks_dxt1(d, off, w, h, com_alpha=True):
    img = np.zeros((h, w, 4), np.uint8)
    nb_x = (w + 3) // 4
    nb_y = (h + 3) // 4
    p = off
    for by in range(nb_y):
        for bx in range(nb_x):
            c0, c1, bits = struct.unpack_from('<HHI', d, p)
            p += 8
            colors, transparente = _colors_dxt(c0, c1, com_alpha)
            for i in range(16):
                y = by * 4 + i // 4
                x = bx * 4 + i % 4
                if y >= h or x >= w:
                    continue
                evidence = (bits >> (2 * i)) & 0x03
                img[y, x, :3] = colors[evidence].astype(np.uint8)
                img[y, x, 3] = 0 if (transparente and evidence == 3) else 255
    return img


def _blocks_dxt3(d, off, w, h):
    img = _blocks_dxt1(d, off + 8, w, h, com_alpha=False)
    nb_x = (w + 3) // 4
    nb_y = (h + 3) // 4
    p = off
    for by in range(nb_y):
        for bx in range(nb_x):
            alfa = np.frombuffer(d, dtype=np.uint8, count=8, offset=p).reshape(2, 4)
            p += 8
            for i in range(16):
                y = by * 4 + i // 4
                x = bx * 4 + i % 4
                if y >= h or x >= w:
                    continue
                v = alfa[i // 8, i % 8 // 2]
                v = (v >> 4) & 0x0F if (i % 2 == 0) else v & 0x0F
                img[y, x, 3] = v * 17
    return img


def _blocks_dxt5(d, off, w, h):
    img = _blocks_dxt1(d, off + 8, w, h, com_alpha=False)
    nb_x = (w + 3) // 4
    nb_y = (h + 3) // 4
    p = off
    for by in range(nb_y):
        for bx in range(nb_x):
            a0, a1 = d[p], d[p + 1]
            idx = struct.unpack_from('<Q', d, p)[0] >> 16
            p += 8
            tab = [a0, a1]
            if a0 > a1:
                tab += [((7 - i) * a0 + i * a1) // 7 for i in range(1, 7)]
            else:
                tab += [((5 - i) * a0 + i * a1) // 5 for i in range(1, 5)] + [0, 255]
            for i in range(16):
                y = by * 4 + i // 4
                x = bx * 4 + i % 4
                if y >= h or x >= w:
                    continue
                img[y, x, 3] = tab[(idx >> (3 * i)) & 0x07]
    return img


def read_data(path, mip=0, info=None):
    info = info or header_text(path)
    with open(path, 'rb') as f:
        return le_bytes(f.read(), mip, info, path)


def le_bytes(data_bytes, mip=0, info=None, path='<bytes>'):
    info = info or header_bytes(data_bytes, path)
    if mip and (mip >= 16 or not info['sizes'][mip]):
        raise BLPError('%s: has no mipmap %d' % (path, mip))
    v, c = info['version_num'], info['compression']
    if v == 1 and c == 0:
        cab_jpeg = b''
        if info['jpeg_header']:
            cab_jpeg = data_bytes[160:160 + info['jpeg_header']]
        jpg = cab_jpeg + _data_bytes(data_bytes, info, mip, path)
        im, ok = _jpeg_blp_para_rgba(jpg, info['map_width'], info['map_height'], True)
        if not ok:
            im = im.convert('RGBA')
        return im, info
    if (v == 1 and c == 1):
        return _paletted_bytes(data_bytes, info, mip, 156), info
    if v == 2 and c == 1:
        return _paletted_bytes(data_bytes, info, mip, 148), info
    if v == 2:
        w, h = info['map_width'], info['map_height']
        for _ in range(mip):
            w, h = max(1, w // 2), max(1, h // 2)
        off = info['offsets'][mip]
        d = data_bytes[off:off + (info['sizes'][mip] or (w * h * 4))]
        if c == 3:
            arr = np.frombuffer(d, dtype=np.uint8, count=w * h * 4).reshape(h, w, 4)
            return Image.fromarray(np.ascontiguousarray(arr[:, :, [2, 1, 0, 3]]), 'RGBA'), info
        if c == 2:
            at = info.get('alpha_type', 0)
            if at == 0:
                arr = _blocks_dxt1(d, 0, w, h, com_alpha=True)
            elif at == 1:
                arr = _blocks_dxt3(d, 0, w, h)
            elif at == 7:
                arr = _blocks_dxt5(d, 0, w, h)
            else:
                raise BLPError('%s: alphaType %d is not a known DXT' % (path, at))
            return Image.fromarray(arr, 'RGBA'), info
    raise BLPError('%s: format not supported (%s)' % (path, info['format']))


def le_melhor(path):
    info = header_text(path)
    try:
        return read_data(path, 0, info)
    except Exception:
        for m in range(16):
            if not info['sizes'][m]:
                continue
            try:
                return read_data(path, m, info)
            except Exception:
                continue
        raise

