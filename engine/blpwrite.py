# Writes BLP1 textures with JPEG compression.
import io
import struct

from PIL import Image, ImageChops



QTABLE = [
    40,
    28,
    30,
    35,
    30,
    25,
    40,
    35,
    33,
    35,
    45,
    43,
    40,
    48,
    60,
    100,
    65,
    60,
    55,
    55,
    60,
    123,
    88,
    93,
    73,
    100,
    145,
    128,
    153,
    150,
    143,
    128,
    140,
    138,
    160,
    180,
    230,
    195,
    160,
    170,
    218,
    173,
    138,
    140,
    200,
    255,
    203,
    218,
    238,
    245,
    255,
    255,
    255,
    155,
    193,
    255,
    255,
    255,
    250,
    255,
    230,
    253,
    255,
    248,
]


def _scaled_table(scale):
    return [max(1, min(255, int(round(v * scale)))) for v in QTABLE]


def _patch_component_ids(data):
    out = bytearray(data)
    p = 2
    while p + 4 <= len(out):
        if out[p] != 0xFF:
            break
        m = out[p + 1]
        ln = struct.unpack('>H', bytes(out[p + 2:p + 4]))[0]
        if m == 0xC0:
            n = out[p + 9]
            for i in range(n):
                out[p + 10 + i * 3] = i
        elif m == 0xDA:
            n = out[p + 4]
            for i in range(n):
                out[p + 5 + i * 2] = i
            break
        p += 2 + ln
    return bytes(out)


def _jpeg_bgra(im, quality):
    r, g, b, a = im.split()
    cmyk = Image.merge('CMYK', tuple(ImageChops.invert(c) for c in (b, g, r, a)))
    buf = io.BytesIO()
    cmyk.save(buf, 'JPEG', qtables=[_scaled_table(quality / 100.0)] * 4, subsampling=0)
    data = _patch_component_ids(buf.getvalue())
    out = bytearray(data[:2])
    p = 2
    while p + 4 <= len(data):
        if data[p] != 0xFF:
            out += data[p:]
            break
        marker = data[p + 1]
        if marker == 0xDA:
            out += data[p:]
            break
        seglen = struct.unpack('>H', data[p + 2:p + 4])[0]
        seg = data[p:p + 2 + seglen]
        if not (marker == 0xEE and seg[4:9] == b'Adobe'):
            out += seg
        p += 2 + seglen
    return bytes(out)


def save_blp(im, path, quality=90, alpha_bits=None, mipmaps=True, extra=None):
    im = im.convert('RGBA')
    w, h = im.size
    if alpha_bits is None:
        alpha_bits = 8 if im.getextrema()[3][0] < 255 else 0
    if alpha_bits == 0:
        r, g, b, a = im.split()
        im = Image.merge('RGBA', (r, g, b, Image.new('L', im.size, 255)))
    levels = []
    cur = im
    while True:
        levels.append(_jpeg_bgra(cur, quality if not levels else int(quality * 1.3)))
        if not mipmaps or (cur.width == 1 and cur.height == 1) or len(levels) == 16:
            break
        cur = cur.resize((max(1, cur.width // 2), max(1, cur.height // 2)), Image.LANCZOS)
    header_size = 156 + 4
    offs = []
    sizes = []
    pos = header_size
    for lv in levels:
        offs.append(pos)
        sizes.append(len(lv))
        pos += len(lv)
    offs += [0] * (16 - len(offs))
    sizes += [0] * (16 - len(sizes))
    hdr = b'BLP1' + struct.pack('<IIIIII', 0, alpha_bits, w, h, 4 if extra is None else extra, 1 if mipmaps else 0)
    hdr += struct.pack('<16I', *offs) + struct.pack('<16I', *sizes) + struct.pack('<I', 0)
    with open(path, 'wb') as f:
        f.write(hdr)
        for lv in levels:
            f.write(lv)
    return len(levels), pos

