# Writes BLP1 textures, JPEG or paletted.
import io
import struct

from PIL import Image, ImageChops



QTABLE = [
    40,
    28,
    25,
    40,
    60,
    100,
    128,
    153,
    30,
    30,
    35,
    48,
    65,
    145,
    150,
    138,
    35,
    33,
    40,
    60,
    100,
    143,
    173,
    140,
    35,
    43,
    55,
    73,
    128,
    218,
    200,
    155,
    45,
    55,
    93,
    140,
    170,
    255,
    255,
    193,
    60,
    88,
    138,
    160,
    203,
    255,
    255,
    230,
    123,
    160,
    195,
    218,
    255,
    255,
    255,
    253,
    180,
    230,
    238,
    245,
    255,
    250,
    255,
    248,
]


LUMA_K = [16, 11, 10, 16, 24, 40, 51, 61, 12, 12, 14, 19, 26, 58, 60, 55, 14, 13, 16, 24, 40, 57, 69, 56,
          14, 17, 22, 29, 51, 87, 80, 62, 18, 22, 37, 56, 68, 109, 103, 77, 24, 35, 55, 64, 81, 104, 113, 92,
          49, 64, 78, 87, 103, 121, 120, 101, 72, 92, 95, 98, 112, 100, 103, 99]
QTABLE_HIGH = [max(1, (v * 20 + 50) // 100) for v in LUMA_K]


def _scaled_table(scale, base=None):
    return [max(1, min(255, int(round(v * scale)))) for v in (QTABLE if base is None else base)]


def _patch_component_ids(data):
    out = bytearray(data)
    p = 2
    while p + 4 <= len(out):
        if out[p] != 0xFF:
            break
        m = out[p + 1]
        txt_ln = struct.unpack('>H', bytes(out[p + 2:p + 4]))[0]
        if m == 0xC0:
            n = out[p + 9]
            for i in range(n):
                out[p + 10 + i * 3] = i
        elif m == 0xDA:
            n = out[p + 4]
            for i in range(n):
                out[p + 5 + i * 2] = i
            break
        p += 2 + txt_ln
    return bytes(out)


def _jpeg_bgra(im, quality, base=None):
    r, g, b, a = im.split()
    cmyk = Image.merge('CMYK', tuple(ImageChops.invert(c) for c in (b, g, r, a)))
    buf = io.BytesIO()
    cmyk.save(buf, 'JPEG', qtables=[_scaled_table(quality / 100.0, base)] * 4, subsampling=0)
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


def blp_jpeg_bytes(im, quality=90, alpha_bits=None, mipmaps=True, extra=None, qtable=None):
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
        levels.append(_jpeg_bgra(cur, quality if not levels else int(quality * 1.3), qtable))
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
    return len(levels), hdr + b''.join(levels)


def save_blp(im, path, quality=90, alpha_bits=None, mipmaps=True, extra=None):
    n, data_bytes = blp_jpeg_bytes(im, quality, alpha_bits, mipmaps, extra)
    with open(path, 'wb') as f:
        f.write(data_bytes)
    return n, len(data_bytes)

