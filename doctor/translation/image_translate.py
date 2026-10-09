# Finds the text in the images of a map and draws the translation in its place.
import hashlib
import io
import os
import re
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from doctor.translation import machine_translate as mt


IMAGE_EXT = ('.blp', '.tga', '.png', '.jpg', '.jpeg')
MIN_SIDE = 64
MIN_CHARS, MIN_CONF = 2, 0.8
OCR_DET = 'ocr-det-ppocrv6-small'
OCR_REC = {'zh': 'ocr-rec-ppocrv6-small', 'existing': 'ocr-rec-ppocrv6-small', 'vi': 'ocr-rec-ppocrv6-small',
           'ko': 'ocr-rec-korean-ppocrv5', 'ru': 'ocr-rec-eslav-ppocrv5', 'th': 'ocr-rec-th-ppocrv5'}
OCR_ZIPS = {
    'ocr-det-ppocrv6-small': {'size': 8031280,
                                'sha256': '41966d3be91c7b7667256cbd282838c2b08ab60b4012219d1086c0dc7662e6c5'},
    'ocr-rec-ppocrv6-small': {'size': 18531923,
                                'sha256': '50e61a663e13cce8e5742e02fdfb3919eb408c2f3185efc4bd6dd19092742f26'},
    'ocr-rec-korean-ppocrv5': {'size': 8340214,
                                 'sha256': 'cd76e3ebeee68bbea4e5b10761b88e81ef5f231971fac2feecb15647a8ef4649'},
    'ocr-rec-eslav-ppocrv5': {'size': 7300128,
                                'sha256': 'c161a47f69b82a59108cb0fc3431a00b4b9b762e51fd46f40e923d6abba485cd'},
    'ocr-rec-th-ppocrv5': {'size': 7274808,
                             'sha256': 'efd1b217372c5a16dc232a87579a3dec05bc906c4be716e0163110cab320779d'},
}
RX_TILE = re.compile(r'^(.*?)(TL|TR|BL|BR|TopLeft|TopRight|BottomLeft|BottomRight)(\.[^.]+)$', re.I)
TILE_POS = {'tl': 'TL', 'tr': 'TR', 'bl': 'BL', 'br': 'BR', 'topleft': 'TL', 'topright': 'TR', 'bottomleft': 'BL',
            'bottomright': 'BR'}
RX_GLYPHS = re.compile(r'(?i)(?:^|[\\/_])fonts?[\\/_$]|damage_?skin|digits?[\\/_.]|numbers?[\\/_.]')


def _nothing(*_a, **_k):
    pass


def ocr_complete(d):
    return os.path.isfile(os.path.join(d, 'model.onnx'))


def ocr_models(lang, progress=None):
    out = []
    for name in (OCR_DET, OCR_REC[lang]):
        if not ocr_complete(mt.model_path(name)):
            (progress or _nothing)('Downloading the text reader')
            mt.download(name, progress, complete=ocr_complete, table=OCR_ZIPS)
        out.append(os.path.join(mt.model_path(name), 'model.onnx'))
    return out


def ocr_info(lang):
    if lang not in OCR_REC:
        return None
    names = (OCR_DET, OCR_REC[lang])
    missing = [n for n in names if not ocr_complete(mt.model_path(n))]
    return {'installed': not missing, 'size': sum((OCR_ZIPS.get(n) or {}).get('size', 0) for n in missing)}


def decode(name, data):
    if name.lower().endswith('.blp'):
        from doctor.models import blpread
        im, _info = blpread.read_bytes(data)
        return im.convert('RGBA')
    im = Image.open(io.BytesIO(data))
    im.load()
    return im.convert('RGBA')


def encode(name, im, original):
    low = name.lower()
    if low.endswith('.blp'):
        from doctor.models import blpwrite
        fd, tmp = tempfile.mkstemp(suffix='.blp')
        os.close(fd)
        try:
            alpha = 8 if im.getextrema()[3][0] < 255 else 0
            blpwrite.save_blp(im, tmp, 100, alpha)
            with open(tmp, 'rb') as f:
                return f.read()
        finally:
            os.remove(tmp)
    buf = io.BytesIO()
    if low.endswith('.tga'):
        old = Image.open(io.BytesIO(original))
        keep_alpha = old.mode in ('RGBA', 'LA') or 'A' in old.getbands()
        (im if keep_alpha else im.convert('RGB')).save(buf, 'TGA', compression=old.info.get('compression'))
    elif low.endswith('.png'):
        im.save(buf, 'PNG')
    else:
        im.convert('RGB').save(buf, 'JPEG', quality=95)
    return buf.getvalue()


def tile_sets(images):
    groups = {}
    for n, size in images.items():
        m = RX_TILE.match(n)
        if m:
            groups.setdefault((m.group(1).lower(), m.group(3).lower(), size), {})[TILE_POS[m.group(2).lower()]] = n
    used, out = set(), []
    for _k, g in sorted(groups.items()):
        if set(g) == {'TL', 'TR', 'BL', 'BR'}:
            out.append([g['TL'], g['TR'], g['BL'], g['BR']])
            used.update(g.values())
    out += [[n] for n in sorted(images) if n not in used]
    return out


def stitch(pictures):
    if len(pictures) == 1:
        return pictures[0]
    w, h = pictures[0].size
    big = Image.new('RGBA', (2 * w, 2 * h))
    for k, p in enumerate(pictures):
        big.paste(p, ((k % 2) * w, (k // 2) * h))
    return big


def unstitch(big, n):
    if n == 1:
        return [big]
    w, h = big.size[0] // 2, big.size[1] // 2
    return [big.crop(((k % 2) * w, (k // 2) * h, (k % 2) * w + w, (k // 2) * h + h)) for k in range(4)]


def set_key(members):
    return '|'.join(members)


def digest(datas):
    h = hashlib.sha1()
    for d in datas:
        h.update(d)
    return h.hexdigest()[:12]


def keep_line(text, lang, conf):
    return conf >= MIN_CONF and len(mt.SCRIPT_OF[lang].findall(text)) >= MIN_CHARS


def blocks(lines):
    out = []
    for ln in sorted(lines, key=lambda r: (r['box'][1], r['box'][0])):
        x0, y0, x1, y1 = ln['box']
        for b in out:
            bx0, by0, bx1, by1 = b[-1]['box']
            h = min(y1 - y0, by1 - by0)
            over = min(x1, bx1) - max(x0, bx0)
            if -0.5 * h <= y0 - by1 < 0.6 * h and over >= 0.5 * min(x1 - x0, bx1 - bx0) and \
                    0.6 < (y1 - y0) / float(by1 - by0) < 1.67:
                b.append(ln)
                break
        else:
            out.append([ln])
    return out


def split_text(text, widths):
    n = len(widths)
    words = text.split()
    if n == 1 or len(words) < 2:
        return [text] + [''] * (n - 1)
    total = float(sum(len(w) for w in words) + len(words) - 1)
    share = [w / float(sum(widths)) for w in widths]
    out, k, acc = [[] for _ in range(n)], 0, 0.0
    target = share[0] * total
    for i, w in enumerate(words):
        left = len(words) - i
        if out[k] and acc + len(w) / 2.0 > target and k < n - 1 and left >= n - k - 1:
            k += 1
            target = acc + share[k] * total
        out[k].append(w)
        acc += len(w) + 1
    return [' '.join(x) for x in out]


def scan(read, names, lang, progress=None, min_side=MIN_SIDE, ocr=None):
    from doctor.translation import image_ocr
    p = progress or _nothing
    images, datas = {}, {}
    for n in names:
        if not n.lower().endswith(IMAGE_EXT) or RX_GLYPHS.search(n):
            continue
        try:
            b = read(n)
            if not b:
                continue
            im = decode(n, b)
        except Exception:
            continue
        if max(im.size) < min_side:
            continue
        images[n] = im.size
        datas[n] = (b, im)
    if not images:
        return []
    if ocr is None:
        det, rec = ocr_models(lang, p)
        ocr = image_ocr.OCR(det, rec)
    out = []
    sets = tile_sets(images)
    for k, members in enumerate(sets):
        p('Reading the text in images: %d of %d' % (k + 1, len(sets)))
        pic = stitch([datas[m][1] for m in members])
        lines = [r for r in ocr(pic) if keep_line(r['text'], lang, r['conf'])]
        if lines:
            out.append({'members': members, 'sha': digest([datas[m][0] for m in members]), 'size': pic.size,
                        'lines': lines})
    return out


def _joiner(lang):
    return '' if lang in mt.SPACELESS else ' '


def add_entries(mtext, read, names, lang, progress=None, min_side=MIN_SIDE):
    found = scan(read, names, lang, progress, min_side)
    n = 0
    for r in found:
        key = set_key(r['members'])
        w, h = r['size']
        for b in blocks(r['lines']):
            boxes = [ln['box'] for ln in b]
            ident = 'img:%s:%s:%s' % (r['sha'], key, ';'.join('%d,%d,%d,%d' % bx for bx in boxes))
            mtext.add(id=ident, source='image', file=r['members'][0],
                      context='image %dx%d%s, %d line(s) at %d,%d' % (
                          w, h, ' (the four tiles of a loading screen)' if len(r['members']) > 1 else '', len(b),
                          boxes[0][0], boxes[0][1]),
                      text=_joiner(lang).join(ln['text'] for ln in b), _kind='tip', _members=r['members'],
                      _boxes=boxes, _sha=r['sha'])
            n += 1
    return n


RX_ID = re.compile(r'^img:([0-9a-f]{12}):(.+):((?:\d+,\d+,\d+,\d+;?)+)$')


def entry_from_id(ident, text, read):
    m = RX_ID.match(ident or '')
    if not m:
        raise ValueError('not an image entry')
    members = m.group(2).split('|')
    datas = []
    for n in members:
        b = read(n)
        if not b:
            raise ValueError('the map has no image %s' % n)
        datas.append(b)
    if digest(datas) != m.group(1):
        raise ValueError('the image in the map is not the one in the file')
    boxes = [tuple(int(x) for x in s.split(',')) for s in m.group(3).split(';') if s]
    return {'id': ident, 'source': 'image', 'file': members[0], 'context': '', 'text': text, '_kind': 'tip',
            '_members': members, '_boxes': boxes, '_sha': m.group(1)}


def build_files(items, read):
    by_set = {}
    for e, tr in items:
        by_set.setdefault(tuple(e['_members']), []).append((e, tr))
    out = {}
    for members, its in sorted(by_set.items()):
        datas = [read(n) for n in members]
        pics = [decode(n, d) for n, d in zip(members, datas)]
        big = stitch(pics)
        lines = []
        for e, tr in its:
            widths = [b[2] - b[0] for b in e['_boxes']]
            lines += [(bx, t, e['id']) for bx, t in zip(e['_boxes'], split_text(tr, widths))]
        new, _styles = render(big, lines)
        for n, d, old, pic in zip(members, datas, pics, unstitch(new, len(members))):
            if np.array_equal(np.asarray(old), np.asarray(pic)):
                continue
            out[n] = encode(n, pic, d)
    return out


REVIEW_SIDE = 360


def _png64(im, side=REVIEW_SIDE):
    import base64
    w, h = im.size
    k = min(1.0, float(side) / max(w, h))
    small = im.resize((max(1, int(w * k)), max(1, int(h * k))), Image.LANCZOS) if k < 1 else im
    if max(small.size) < 160:
        f = max(2, -(-160 // max(small.size)))
        small = small.resize((small.size[0] * f, small.size[1] * f), Image.NEAREST)
    buf = io.BytesIO()
    small.save(buf, 'PNG')
    return base64.b64encode(buf.getvalue()).decode('ascii')


def _set_picture(read, members, sha):
    datas = [read(n) for n in members]
    if any(d is None for d in datas):
        raise ValueError('the map has no image %s' % ', '.join(n for n, d in zip(members, datas) if d is None))
    if digest(datas) != sha:
        raise ValueError('the image in the map is not the one in the file')
    return stitch([decode(n, d) for n, d in zip(members, datas)])


def _lines_of(entries):
    out = []
    for e in entries:
        boxes = [tuple(int(x) for x in s.split(',')) for s in RX_ID.match(e['id']).group(3).split(';') if s]
        if e.get('translation'):
            out += [(bx, t, e['id']) for bx, t in zip(boxes, split_text(e['translation'],
                                                                         [b[2] - b[0] for b in boxes]))]
    return out


def review(read, doc):
    sets = {}
    for t in doc.get('entries') or []:
        m = RX_ID.match(t.get('id') or '') if isinstance(t, dict) else None
        if m:
            sets.setdefault((m.group(2), m.group(1)), []).append(
                {'id': t['id'], 'text': t.get('text') or '', 'translation': t.get('translation') or ''})
    out = []
    for (key, sha), entries in sorted(sets.items()):
        members = key.split('|')
        item = {'key': key, 'members': members, 'entries': entries, 'error': None}
        try:
            pic = _set_picture(read, members, sha)
            new, _styles = render(pic, _lines_of(entries))
            item.update(size=pic.size, original=_png64(pic), preview=_png64(new))
        except Exception as e:
            item['error'] = str(e) or type(e).__name__
        out.append(item)
    return out


def preview(read, entries):
    m = RX_ID.match(entries[0]['id'])
    pic = _set_picture(read, m.group(2).split('|'), m.group(1))
    new, _styles = render(pic, _lines_of(entries))
    return _png64(new)


FONT_MIN = 8


def _font(size):
    return ImageFont.load_default(size=size)


def _ring(a, x0, y0, x1, y1, pad=3):
    h, w = a.shape[:2]
    X0, Y0, X1, Y1 = max(0, x0 - pad), max(0, y0 - pad), min(w, x1 + pad), min(h, y1 + pad)
    region = a[Y0:Y1, X0:X1].reshape(-1, 4)
    inside = np.zeros((Y1 - Y0, X1 - X0), bool)
    inside[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0] = True
    return region[~inside.reshape(-1)]


def _coons(a, x0, y0, x1, y1):
    h, w = a.shape[:2]
    tx0, ty0, tx1, ty1 = max(0, x0 - 1), max(0, y0 - 1), min(w - 1, x1), min(h - 1, y1)
    bw, bh = x1 - x0, y1 - y0
    if bw < 1 or bh < 1:
        return
    top = a[ty0, x0:x1].copy()
    bot = a[ty1, x0:x1].copy()
    left = a[y0:y1, tx0].copy()
    right = a[y0:y1, tx1].copy()

    def smooth(v):
        if len(v) < 5:
            return v
        k = np.ones(5) / 5.0
        return np.stack([np.convolve(np.pad(v[:, c], 2, mode='edge'), k, 'valid') for c in range(4)], 1)
    top, bot, left, right = smooth(top), smooth(bot), smooth(left), smooth(right)
    u = (np.arange(bw) + 0.5) / bw
    v = (np.arange(bh) + 0.5) / bh
    U, V = u[None, :, None], v[:, None, None]
    c00, c10, c01, c11 = a[ty0, tx0], a[ty0, tx1], a[ty1, tx0], a[ty1, tx1]
    patch = ((1 - V) * top[None] + V * bot[None] + (1 - U) * left[:, None] + U * right[:, None]
             - ((1 - U) * (1 - V) * c00 + U * (1 - V) * c10 + (1 - U) * V * c01 + U * V * c11))
    a[y0:y1, x0:x1] = np.clip(patch, 0, 255)


def _fit(draw, text, bw, bh):
    words = text.split()
    for lines_n in (1, 2):
        size = max(FONT_MIN, int(bh * 0.85 / lines_n))
        while size >= FONT_MIN:
            f = _font(size)
            if lines_n == 1:
                lines = [text]
            else:
                best = None
                for cut in range(1, len(words)):
                    a, b = ' '.join(words[:cut]), ' '.join(words[cut:])
                    wmax = max(draw.textlength(a, font=f), draw.textlength(b, font=f))
                    if best is None or wmax < best[0]:
                        best = (wmax, [a, b])
                if best is None:
                    break
                lines = best[1]
            if max(draw.textlength(x, font=f) for x in lines) <= bw * 1.02:
                return f, lines
            size -= 1
    return _font(FONT_MIN), [text]


def render(im, items):
    a = np.asarray(im.convert('RGBA')).astype(np.float32).copy()
    plan = []
    group = {}
    for k, it in enumerate(items):
        group[k] = it[2] if len(it) > 2 else k
    for k, it in enumerate(items):
        (x0, y0, x1, y1), text = it[0], it[1]
        ring = _ring(a, x0, y0, x1, y1)
        if not len(ring):
            continue
        bg = np.median(ring, axis=0)
        spread = float(np.mean(np.abs(ring[:, :3] - bg[:3])))
        box = a[y0:y1, x0:x1].reshape(-1, 4)
        dist = np.abs(box[:, :3] - bg[:3]).sum(1) + np.abs(box[:, 3] - bg[3])
        ink = box[dist > max(60.0, 3.0 * spread)]
        color = tuple(int(c) for c in (np.median(ink, axis=0) if len(ink) else (255, 255, 255, 255)))
        style = 'replace' if spread < 18 else 'band'
        _coons(a, x0, y0, x1, y1)
        tint = tuple(int(c * 0.3) for c in np.mean(ring[:, :3], axis=0)) + (255,)
        plan.append(((x0, y0, x1, y1), text, style, color, bg, tint, group[k]))
    out = Image.fromarray(a.astype(np.uint8), 'RGBA')
    over = Image.new('RGBA', out.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    styles = []
    fits = {}
    for k, ((x0, y0, x1, y1), text, _st, _c, _b, _t, g) in enumerate(plan):
        if text:
            fits[k] = _fit(d, text, x1 - x0, y1 - y0)
    smallest = {}
    for k, (f, _lines) in fits.items():
        g = plan[k][6]
        smallest[g] = min(smallest.get(g, f.size), f.size)
    for (x0, y0, x1, y1), text, style, color, bg, tint, _g in plan:
        if style == 'band':
            pad = max(2, int((y1 - y0) * 0.08))
            d.rounded_rectangle((x0 - pad, y0 - pad, x1 + pad, y1 + pad), radius=max(2, int((y1 - y0) * 0.2)),
                                fill=tint)
    for k, ((x0, y0, x1, y1), text, style, color, bg, _tint, g) in enumerate(plan):
        bw, bh = x1 - x0, y1 - y0
        if not text:
            styles.append(style)
            continue
        f, lines = fits[k]
        if smallest[g] < f.size:
            f = _font(smallest[g])
        lh = f.size * 1.1
        total = lh * len(lines)
        if style == 'band':
            lum = 0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2]
            fill = color[:3] + (255,) if color[3] > 0 and lum > 90 else (255, 255, 255, 255)
            stroke = (0, 0, 0, 255)
        else:
            fill = color if color[3] > 0 else (255, 255, 255, 255)
            lum = 0.299 * fill[0] + 0.587 * fill[1] + 0.114 * fill[2]
            stroke = (0, 0, 0, 255) if lum > 110 else (255, 255, 255, 255)
            if bg[3] < 30:
                stroke = (0, 0, 0, 255) if lum > 110 else (255, 255, 255, 255)
        sw = max(1, f.size // 12)
        y = y0 + (bh - total) / 2.0
        for line in lines:
            tw = d.textlength(line, font=f)
            d.text((x0 + (bw - tw) / 2.0, y), line, font=f, fill=fill, stroke_width=sw, stroke_fill=stroke)
            y += lh
        styles.append(style)
    return Image.alpha_composite(out, over), styles
