# Finds the text in the images of a map and draws the translation in its place.
import hashlib
import io
import os
import re
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from doctor.translation import machine_translate as mt


IMAGE_EXT = ('.blp', '.tga', '.png', '.jpg', '.jpeg')
MIN_SIDE = 24
MIN_CHARS, MIN_CONF = 2, 0.8
OCR_DET = 'ocr-det-ppocrv6-small'
OCR_REC = {'zh': 'ocr-rec-ppocrv6-small', 'ja': 'ocr-rec-ppocrv6-small', 'vi': 'ocr-rec-ppocrv6-small',
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


def encode(name, im, original, fiel=False):
    low = name.lower()
    if low.endswith('.blp'):
        from doctor.models import blpwrite
        if fiel:
            try:
                tabela = blpwrite.qtable_from_bytes(original) if original[:4] == b'BLP1' else None
            except Exception:
                tabela = None
            if tabela:
                alpha = 8 if im.getextrema()[3][0] < 255 else 0
                return blpwrite.blp_jpeg_bytes(im, 100, alpha, qtable=tabela)[1]
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


OCR_PARALLEL = 2
OCR_SIDE = 256  # small images (64x64 icons, 128x32 labels) are read enlarged to this: the reader misses small letters


def read_image(ocr, pic):
    # the reader sees the image over a dark background (light letters on a transparent image are invisible on the
    # black the alpha would leave) and, when it is small, enlarged; the boxes come back in the image's own pixels
    w, h = pic.size
    k = max(1, min(4, OCR_SIDE // max(1, max(w, h))))
    big = pic.resize((w * k, h * k), Image.LANCZOS) if k > 1 else pic
    flat = Image.new('RGBA', big.size, (40, 40, 40, 255))
    flat.alpha_composite(big.convert('RGBA'))
    out = []
    for r in ocr(flat):
        x0, y0, x1, y1 = r['box']
        r = dict(r)
        r['box'] = (int(x0 // k), int(y0 // k), int(-(-x1 // k)), int(-(-y1 // k)))
        out.append(r)
    return out


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
        datas[n] = b
        del im
    if not images:
        return []
    par = OCR_PARALLEL if sys.platform != 'emscripten' else 1
    if ocr is None:
        det, rec = ocr_models(lang, p)
        total = max(1, min(8, os.cpu_count() or 1))
        ocr = image_ocr.OCR(det, rec, threads=max(1, total // par))
    out = []
    sets = tile_sets(images)

    def read_set(members):
        pic = stitch([decode(m, datas[m]) for m in members])
        return pic.size, [r for r in read_image(ocr, pic) if keep_line(r['text'], lang, r['conf'])]
    if par > 1:
        from concurrent.futures import ThreadPoolExecutor
        pool = ThreadPoolExecutor(par)
        results = pool.map(read_set, sets)
    else:
        pool, results = None, map(read_set, sets)
    try:
        for k, (members, (size, lines)) in enumerate(zip(sets, results)):
            p('Reading the text in images: %d of %d' % (k + 1, len(sets)))
            if lines:
                out.append({'members': members, 'sha': digest([datas[m] for m in members]), 'size': size,
                            'lines': lines})
    finally:
        if pool is not None:
            pool.shutdown(wait=True, cancel_futures=True)
    return out


def _joiner(lang):
    return '' if lang in mt.SPACELESS else ' '


RX_FRAME = re.compile(r'^(.*?)(\d+)(\)?\.[^.\\/]+)$')
MIN_FRAMES = 3


def frame_sets(found, names, read):
    # an animation kept as numbered images (an overhead title: thwj_00000.blp .. thwj_00007.blp, "GHWJ (1).blp" ..):
    # its text is the same on every frame, so every frame gets the reading most frames agree on (the effects make the
    # reader see 骨女 for 骨灰 now and then), and the frames it missed get that text at the box most frames had;
    # otherwise the title would flicker between the translation and the original. Only frames with one block of text.
    groups = {}
    for n in names:
        m = RX_FRAME.match(n)
        if m:
            groups.setdefault((m.group(1).lower(), m.group(3).lower()), []).append(n)
    by_name = {r['members'][0]: r for r in found if len(r['members']) == 1}
    extra = []
    for _k, members in groups.items():
        if len(members) < MIN_FRAMES:
            continue
        hits = [by_name[n] for n in members if n in by_name]
        single = [r for r in hits if len(blocks(r['lines'])) == 1]
        if len(single) < max(2, (len(members) + 2) // 3) or len(single) < len(hits):
            continue
        size = single[0]['size']
        if any(r['size'] != size for r in single):
            continue
        texts = [''.join(ln['text'] for ln in r['lines']) for r in single]
        text = max(set(texts), key=texts.count)
        if texts.count(text) * 5 < len(texts) * 3:
            continue  # numbered images that say different things (icons T302, T304, ...) are not an animation
        boxes = [tuple(r['lines'][0]['box']) for r in single if len(r['lines']) == 1]
        if not boxes:
            continue
        box = tuple(int(np.median([b[i] for b in boxes])) for i in range(4))
        for r in single:
            if len(r['lines']) == 1:
                r['lines'][0]['text'] = text
        for n in members:
            if n in by_name:
                continue
            try:
                d = read(n)
                if not d or decode(n, d).size != tuple(size):
                    continue
            except Exception:
                continue
            extra.append({'members': [n], 'sha': digest([d]), 'size': size,
                          'lines': [{'box': box, 'text': text, 'conf': 0.0}]})
    return found + extra


def add_entries(mtext, read, names, lang, progress=None, min_side=MIN_SIDE):
    found = frame_sets(scan(read, names, lang, progress, min_side), names, read)
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


RX_ID = re.compile(r'^img:([0-9a-f]{12}):(.+):((?:\d++,\d++,\d++,\d++(?:;|$))+)$')


def entry_from_id(ident, text, read):
    m = RX_ID.match(ident or '')
    if not m:
        raise ValueError('not an image entry')
    if not isinstance(text, str):
        raise ValueError('the entry has no original text')
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
    font = map_font(read)
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
        new, _styles = render(big, lines, font)
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
    font = map_font(read)
    for (key, sha), entries in sorted(sets.items()):
        members = key.split('|')
        item = {'key': key, 'members': members, 'entries': entries, 'error': None}
        try:
            pic = _set_picture(read, members, sha)
            new, _styles = render(pic, _lines_of(entries), font)
            item.update(size=pic.size, original=_png64(pic), preview=_png64(new))
        except Exception as e:
            item['error'] = str(e) or type(e).__name__
        out.append(item)
    return out


def preview(read, entries):
    m = RX_ID.match(entries[0]['id'])
    pic = _set_picture(read, m.group(2).split('|'), m.group(1))
    new, _styles = render(pic, _lines_of(entries), map_font(read))
    return _png64(new)


FONT_MIN = 6
SS = 4  # the text is drawn this many times larger, then reduced (smooth edges at small sizes)
MIN_SQUEEZE = 0.78  # English is longer than Chinese: letters are narrowed down to this before the size drops
# fonts a map may carry for its own UI; the text is redrawn in it when it has Latin letters, so it matches the map
MAP_FONTS = ('fonts.ttf', 'Fonts\\FRIZQT__.TTF', 'Fonts\\frizqt__.ttf', 'Fonts\\FZXS12.TTF')
_fonts = {}


def _font(size, data=None):
    k = (id(data), size)
    if k not in _fonts:
        if len(_fonts) > 256:
            _fonts.clear()
        _fonts[k] = ImageFont.truetype(io.BytesIO(data), size) if data else ImageFont.load_default(size=size)
    return _fonts[k]


def _has_latin(data):
    try:
        f = ImageFont.truetype(io.BytesIO(data), 40)
        a, missing = f.getmask('A'), f.getmask('\U0010fffd')
        return a.getbbox() is not None and (a.size != missing.size or bytes(a) != bytes(missing))
    except Exception:
        return False


def map_font(read):
    for n in MAP_FONTS:
        try:
            b = read(n)
        except Exception:
            b = None
        if b and _has_latin(b):
            return b
    return None


def _lum(c):
    return 0.299 * c[..., 0] + 0.587 * c[..., 1] + 0.114 * c[..., 2]


def _dilate(m, r):
    if r <= 0 or not m.any():
        return m
    from PIL import ImageFilter
    im = Image.fromarray(m.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(2 * r + 1))
    return np.asarray(im) > 127


def _diffuse(a, m, rounds=None):
    # fills the masked pixels from the pixels around them (each step averages the four neighbours): the ornaments
    # around the text stay as they are, the hole takes their colours smoothly
    if not m.any():
        return a.copy()
    # premultiplied: the colour of transparent pixels (often white) must not bleed into the fill
    a = a.copy()
    a[..., :3] *= a[..., 3:] / 255.0
    ring = _dilate(m, 2) & ~m
    a[m] = a[ring].mean(0) if ring.any() else 128.0
    ys, xs = np.where(m)
    if rounds is None:
        rounds = int(min(600, 3 * max(ys.max() - ys.min(), xs.max() - xs.min()) + 40))
    for _ in range(rounds):
        p = np.pad(a, ((1, 1), (1, 1), (0, 0)), mode='edge')
        a[m] = ((p[:-2, 1:-1] + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:]) * 0.25)[m]
    al = np.maximum(a[..., 3:], 1e-3) / 255.0
    a[..., :3] = np.where(a[..., 3:] > 0, a[..., :3] / al, 0)
    return a


def _glyphs_by_tone(sub, inner):
    # light letters (the usual: white or gold with a dark rim): the brightest opaque pixels in the box, and the rim
    # around them, which is darker than the plate under the text
    L = _lum(sub)
    opaque = inner & (sub[..., 3] > 128)
    if opaque.sum() < 16:
        return np.zeros(inner.shape, bool)
    base = np.median(L[opaque])
    fill = opaque & (L >= max(np.percentile(L[opaque], 80), base + 50))
    if fill.sum() >= 8:
        # only the letters' own colour (a bright icon next to the text is another colour)
        c = np.median(sub[fill][:, :3], axis=0)
        fill &= np.abs(sub[..., :3] - c).sum(-1) < 90
    near = _dilate(fill, 3) & inner
    rim = near & ~fill & ((L < base - 25) | (sub[..., 3] < 128))
    return fill | (rim & _dilate(fill, 3))


def _lettering_only(sub, inner):
    # an image whose opaque part is only letters: see-through around and between them, and most opaque pixels near
    # a see-through one (strokes), unlike a button or plate (one solid shape with see-through corners)
    opaque = inner & (sub[..., 3] >= 30)
    n = opaque.sum()
    if n < 16 or n > 0.85 * inner.sum():
        return False
    edge = opaque & _dilate(inner & ~opaque, 2)
    return edge.sum() > 0.2 * n   # strokes: 王牌数码 tags 0.27; buttons and plates 0.07-0.09


def _glyphs(a, box, pad=4):
    # the pixels of the letters (fill and outline) in the box: those far from what the box would be without them
    # (the box filled from its border)
    h, w = a.shape[:2]
    x0, y0, x1, y1 = box
    X0, Y0, X1, Y1 = max(0, x0 - pad), max(0, y0 - pad), min(w, x1 + pad), min(h, y1 + pad)
    sub = a[Y0:Y1, X0:X1]
    inner = np.zeros(sub.shape[:2], bool)
    inner[max(0, y0 - Y0):y1 - Y0, max(0, x0 - X0):x1 - X0] = True
    plain = _diffuse(sub, inner, 300)
    d = np.abs(sub[..., :3] - plain[..., :3]).sum(-1) + np.abs(sub[..., 3] - plain[..., 3])
    # and far from the image smoothed by a median wider than a stroke: strokes vanish under it, while shapes larger
    # than the letters (a band, a frame line the box happens to cross) stay and are not taken for letters
    from PIL import ImageFilter
    k = int(np.clip((y1 - y0) // 3, 5, 15)) | 1
    med = np.asarray(Image.fromarray(np.clip(sub, 0, 255).astype(np.uint8), 'RGBA').filter(
        ImageFilter.MedianFilter(k))).astype(np.float32)
    dm = np.abs(sub[..., :3] - med[..., :3]).sum(-1) + np.abs(sub[..., 3] - med[..., 3])
    core = (d > 70) & (dm > 50) & inner
    # the letters are the strokes found that way plus what touches them (a stroke's middle can equal its median)
    found = _dilate(core, 2) & (d > 70) & inner
    if (~inner).sum() >= 0.1 * inner.size and found.sum() > 0.6 * inner.sum() and (y1 - y0) < 0.45 * h:
        # a band of text across part of an icon (a card's name at its foot), letters over most of it: the band goes
        found = inner.copy()
    elif (~inner).sum() < 0.1 * inner.size and _lettering_only(sub, inner):
        # the whole image is a label cut out of a see-through background (王牌数码's difficulty tags): all that shows
        # is lettering, fill and outline alike
        found = inner & (sub[..., 3] >= 30)
    elif (~inner).sum() < 0.1 * inner.size or found.sum() > 0.6 * inner.sum():
        # no border to fill the box from (it is the whole image), or "letters" over most of it (a plate barely taller
        # than its text): the letters by their tone instead
        found = _glyphs_by_tone(sub, inner)
    m = np.zeros((h, w), bool)
    m[Y0:Y1, X0:X1] = found
    if m.sum() < 8:
        m[max(0, y0):y1, max(0, x0):x1] = True
    return m


def _style(a, m):
    # the original's look: fill colour at the top and at the bottom of the letters (gradients), outline colour and width
    vis = m & (a[..., 3] >= 30)
    if vis.sum() >= 4:
        m = vis  # see-through pixels have no colour one can see (lettering on a transparent sheet: they are white at
        # alpha 0, and measuring them gave an invisible fill)
    L = _lum(a)
    px = L[m]
    rows = np.arange(a.shape[0])[:, None]
    hi = m & (L >= np.percentile(px, 55))
    lo = m & (L <= np.percentile(px, 15))
    solid = lo & (a[..., 3] > 128)
    if solid.sum() >= 4:
        lo = solid  # the rim's colour from its opaque pixels (see-through ones would make the outline vanish)
    ys = np.where(hi.any(1))[0]
    mid = (ys.min() + ys.max()) / 2.0 if len(ys) else a.shape[0] / 2.0
    up, dn = a[hi & (rows < mid)], a[hi & (rows >= mid)]
    allhi = a[hi] if hi.any() else a[m]
    top = up.mean(0) if len(up) else allhi.mean(0)
    bot = dn.mean(0) if len(dn) else allhi.mean(0)
    outline = a[lo].mean(0) if lo.any() else np.array([0, 0, 0, 255], np.float32)
    has_outline = float(_lum(allhi.mean(0)[None])[0] - _lum(outline[None])[0]) > 60
    if not has_outline:
        # light letters with no dark rim of their own (or dark letters): a thin rim of the opposite tone keeps them
        # readable over the filled-in background
        outline = np.array([0, 0, 0, 255] if _lum(top[None])[0] > 110 else [255, 255, 255, 255], np.float32)
    dark = m & (L < np.percentile(px, 50) - 40)
    bright = m & (L >= np.percentile(px, 50))
    per = (_dilate(bright, 1) & ~bright).sum()
    width = float(np.clip(dark.sum() / max(1, per) * 1.2, 1, 4)) if has_outline else 1.0
    for c in (top, bot):
        c[3] = 255 if c[3] > 200 else c[3]
    return {'top': top, 'bot': bot, 'outline': outline, 'width': width, 'ink': hi if hi.any() else m}


def _layout(text, font, avail, ink_h):
    # a wide, short place (a plate, a title bar) takes one narrowed line rather than two small ones
    # the largest size whose letters are as tall as the original's (squeezed sideways before shrinking), on 1 or 2
    # lines; returns (size, lines, squeeze)
    words = text.split()
    best = None
    for n in range(1, min(2, len(words)) + 1):
        cands = [[text]] if n == 1 else [[' '.join(words[:k]), ' '.join(words[k:])] for k in range(1, len(words))]
        for lines in cands:
            target = ink_h / n * (0.92 if n == 1 else 0.86)
            probe = _font(100, font)
            hb = probe.getbbox('H')
            size = max(FONT_MIN, int(100 * target / max(1, hb[3] - hb[1])))
            sq = 1.0
            while size > FONT_MIN:
                f = _font(size, font)
                wmax = max(f.getlength(x) for x in lines) or 1
                sq = min(1.0, avail / wmax)
                if sq >= MIN_SQUEEZE:
                    break
                size -= 1
            score = size * (1.0 if n == 1 else (0.7 if avail > 3.5 * ink_h else 0.9))
            if best is None or score > best[0]:
                best = (score, size, lines, sq)
    return best[1], best[2], best[3]


def _draw(out, plan, size, font):
    # draws one text in the style measured from the original: outline layer, then the fill with its gradient
    h, w = out.shape[:2]
    st, lines, sq, (bx0, bx1), (r0, r1) = plan['style'], plan['lines'], plan['sq'], plan['span'], plan['rows']
    f = _font(size, font)
    hb = f.getbbox('H')
    cap = hb[3] - hb[1]
    gap = cap * 0.35
    total = cap * len(lines) + gap * (len(lines) - 1)
    top = (r0 + r1) / 2.0 * SS - total / 2.0
    ow = int(round(st['width'] * SS))
    # the text stays inside the image (two lines centred on letters near an edge would be cut): descenders and the
    # outline included
    below = max(0, f.getbbox('gjpqy')[3] - hb[3]) if any(c in 'gjpqy' for c in lines[-1]) else 0
    top = min(top, h * SS - (total + below + ow + SS))
    top = max(top, ow + SS)
    glyph = Image.new('L', (w * SS, h * SS), 0)
    rim = Image.new('L', (w * SS, h * SS), 0)
    asc, desc = f.getmetrics()
    for i, line in enumerate(lines):
        o = 2 * ow + 4
        tw, th = int(f.getlength(line)) + 2 * o, asc + desc + 2 * o
        lg, lr = Image.new('L', (tw, th), 0), Image.new('L', (tw, th), 0)
        ImageDraw.Draw(lg).text((o, o), line, font=f, fill=255)
        ImageDraw.Draw(lr).text((o, o), line, font=f, fill=255, stroke_width=ow, stroke_fill=255)
        nw = max(1, int(tw * sq))
        if nw != tw:
            lg, lr = lg.resize((nw, th), Image.LANCZOS), lr.resize((nw, th), Image.LANCZOS)
        x = int((bx0 + bx1) / 2.0 * SS - nw / 2.0)
        y = int(top + i * (cap + gap) - o - hb[1])
        glyph.paste(lg, (x, y), lg)
        rim.paste(lr, (x, y), lr)
    g = (np.asarray(glyph.resize((w, h), Image.LANCZOS)).astype(np.float32) / 255)[..., None]
    r = (np.asarray(rim.resize((w, h), Image.LANCZOS)).astype(np.float32) / 255)[..., None]
    t = np.clip((np.arange(h)[:, None] - top / SS) / max(1.0, total / SS), 0, 1)[..., None]
    fill = st['top'][None, None, :] * (1 - t) + st['bot'][None, None, :] * t
    oc = st['outline'][None, None, :]
    al = r * (oc[..., 3:] / 255.0)
    out[..., :3] = out[..., :3] * (1 - al) + oc[..., :3] * al
    out[..., 3:] = np.maximum(out[..., 3:], r * oc[..., 3:])
    out[..., :3] = out[..., :3] * (1 - g) + fill[..., :3] * g
    out[..., 3:] = np.maximum(out[..., 3:], g * fill[..., 3:])


def _room(a, span, rows, hole=None):
    # how wide the new text may be: the letters' own span, widened on each side while the background (already without
    # the letters) stays plain along their rows; it stops at a frame's edge or an ornament, up to 1.5 letter heights out
    h, w = a.shape[:2]
    r0, r1 = rows
    band = a[r0:r1]
    if band.shape[0] < 2:
        return span
    gx = np.abs(np.diff(band, axis=1)).sum(-1)
    gy = np.abs(np.diff(band, axis=0)).sum(-1)
    e = np.zeros(w)
    e[:-1] += gx.mean(0)
    e += gy.mean(0)
    if hole is not None:
        # the erased letters' place (and the faint seam at its edge) is room by definition
        cols = _dilate(hole[r0:r1].any(0)[None, :].repeat(3, 0), 2)[1]
        e[cols] = 0
    # empty (transparent) columns are not room: whatever the game shows there (a tick box, the screen's edge) is not
    # in the picture
    e[band[..., 3].mean(0) < 30] = np.inf
    x0, x1 = span
    inside = e[x0:x1]
    inside = inside[np.isfinite(inside)]
    thr = (np.median(inside) if len(inside) else 0) * 3 + 12
    reach = int(1.5 * (r1 - r0))
    while x0 > 0 and span[0] - x0 < reach and e[x0 - 1] < thr:
        x0 -= 1
    while x1 < w - 1 and x1 - span[1] < reach and e[x1] < thr:
        x1 += 1
    margin = max(1, int((r1 - r0) * 0.1))
    if x0 < span[0]:
        x0 = min(span[0], x0 + margin)
    if x1 > span[1]:
        x1 = max(span[1], x1 - margin)
    return x0, x1


def render(im, items, font=None):
    # items: (box, text, group). Each box loses its letters (filled from around them) and gets the text in the same
    # look (fill gradient, outline), in `font` (a map's own font file) or the default one; lines of one group share
    # the smallest size among them
    a = np.asarray(im.convert('RGBA')).astype(np.float32).copy()
    h, w = a.shape[:2]
    plans = []
    for k, it in enumerate(items):
        (x0, y0, x1, y1), text = it[0], it[1]
        x0, y0, x1, y1 = max(0, x0), max(0, y0), min(w, x1), min(h, y1)
        if x1 - x0 < 2 or y1 - y0 < 2:
            continue
        m = _glyphs(a, (x0, y0, x1, y1))
        st = _style(a, m)
        ys, xs = np.where(st['ink'].any(1))[0], np.where(st['ink'].any(0))[0]
        rows = (ys.min(), ys.max() + 1) if len(ys) else (y0, y1)
        cols = (xs.min(), xs.max() + 1) if len(xs) else (x0, x1)
        pad = 8
        X0, Y0, X1, Y1 = max(0, x0 - pad), max(0, y0 - pad), min(w, x1 + pad), min(h, y1 + pad)
        hole = _dilate(m, 2)[Y0:Y1, X0:X1]
        ring = np.ones((Y1 - Y0, X1 - X0), bool)
        ring[2:-2, 2:-2] = False
        if (a[Y0:Y1, X0:X1, 3][ring] < 30).mean() > 0.8:
            # lettering on a transparent sheet: everything one can see in the box is lettering (its shadow and rim
            # too, which the glyph mask can miss and which would show under the new text)
            hole = hole | (a[Y0:Y1, X0:X1, 3] > 0)
        a[Y0:Y1, X0:X1] = _diffuse(a[Y0:Y1, X0:X1], hole)
        full_hole = np.zeros((h, w), bool)
        full_hole[Y0:Y1, X0:X1] = hole
        plans.append({'hole': full_hole, 'text': text, 'style': st, 'rows': rows, 'span': (max(1, cols[0] - 1), min(w - 1, cols[1] + 1)),
                      'group': it[2] if len(it) > 2 else k})
    for p in plans:
        p['span'] = _room(a, p['span'], p['rows'], p.pop('hole'))
    sizes = {}
    for p in plans:
        if p['text']:
            avail = (p['span'][1] - p['span'][0] - 2 * p['style']['width']) * SS * 0.95
            p['size'], p['lines'], p['sq'] = _layout(p['text'], font, avail, (p['rows'][1] - p['rows'][0]) * SS)
            sizes[p['group']] = min(sizes.get(p['group'], p['size']), p['size'])
    styles = []
    for p in plans:
        if p['text']:
            size = sizes[p['group']]
            if size < p['size']:
                f = _font(size, font)
                wmax = max(f.getlength(x) for x in p['lines']) or 1
                avail = (p['span'][1] - p['span'][0] - 2 * p['style']['width']) * SS * 0.95
                p['sq'] = min(1.0, avail / wmax)
            _draw(a, p, size, font)
            styles.append('redraw')
        else:
            styles.append('erase')
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA'), styles
