# Reads the text drawn in an image (the PaddleOCR models through onnxruntime).
import math
import os

import numpy as np
from PIL import Image



DET_LIMIT = 736
DET_THRESH, BOX_THRESH, UNCLIP, MIN_SIZE = 0.3, 0.5, 1.6, 3
MIN_SIDE, MAX_SIDE, WH_RATIO, MIN_HEIGHT = 30, 2000, 8, 30
REC_H, REC_W, REC_BATCH = 48, 320, 6
TEXT_SCORE = 0.5


def flatten(im):
    im = im.convert('RGBA')
    a = np.asarray(im).astype(np.float32)
    alpha = a[:, :, 3:4] / 255.0
    opaque = a[:, :, 3] > 0
    if opaque.any():
        lum = (0.299 * a[:, :, 0] + 0.587 * a[:, :, 1] + 0.114 * a[:, :, 2])[opaque].mean()
        bg = 0.0 if lum > 127 else 255.0
    else:
        bg = 255.0
    rgb = a[:, :, :3] * alpha + bg * (1 - alpha)
    return Image.fromarray(np.clip(rgb + 0.5, 0, 255).astype(np.uint8), 'RGB')


def _resize(arr, w, h):
    return np.asarray(Image.fromarray(arr).resize((max(1, w), max(1, h)), Image.BILINEAR))


def _components(mask):
    parent = []

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    runs = []
    prev = []
    for y in range(mask.shape[0]):
        row = mask[y]
        if not row.any():
            prev = []
            continue
        d = np.diff(np.concatenate(([0], row.view(np.int8), [0])))
        starts, ends = np.flatnonzero(d == 1), np.flatnonzero(d == -1) - 1
        cur = []
        j = 0
        for s, e in zip(starts.tolist(), ends.tolist()):
            rid = len(parent)
            parent.append(rid)
            while j < len(prev) and prev[j][1] < s - 1:
                j += 1
            k = j
            while k < len(prev) and prev[k][0] <= e + 1:
                a, b = find(prev[k][2]), find(rid)
                if a != b:
                    parent[b] = a
                k += 1
            cur.append((s, e, rid))
            runs.append((y, s, e, rid))
        prev = cur
    boxes = {}
    for y, s, e, rid in runs:
        r = find(rid)
        b = boxes.get(r)
        if b is None:
            boxes[r] = [s, y, e, y]
        else:
            b[0] = min(b[0], s)
            b[1] = min(b[1], y)
            b[2] = max(b[2], e)
            b[3] = max(b[3], y)
    return list(boxes.values())


class OCR(object):
    def __init__(self, det_path, rec_path, threads=0):
        import onnxruntime as ort
        so = ort.SessionOptions()
        so.intra_op_num_threads = threads or max(1, min(8, os.cpu_count() or 1))
        so.log_severity_level = 3
        prov = ['CPUExecutionProvider']
        self.det = ort.InferenceSession(det_path, so, providers=prov)
        self.rec = ort.InferenceSession(rec_path, so, providers=prov)
        meta = self.rec.get_modelmeta().custom_metadata_map
        chars = meta['character'].splitlines() if 'character' in meta else \
            open(os.path.splitext(rec_path)[0] + '.txt', encoding='utf-8').read().splitlines()
        self.chars = ['blank'] + chars + [' ']

    def detect(self, rgb):
        h0, w0 = rgb.shape[:2]
        img, sx, sy = rgb, 1.0, 1.0
        if max(h0, w0) > MAX_SIDE:
            r = MAX_SIDE / float(max(h0, w0))
            img = _resize(img, int(w0 * r), int(h0 * r))
        h, w = img.shape[:2]
        if min(h, w) < MIN_SIDE:
            r = MIN_SIDE / float(min(h, w))
            img = _resize(img, int(math.ceil(w * r)), int(math.ceil(h * r)))
        h1, w1 = img.shape[:2]
        sx, sy = w0 / float(w1), h0 / float(h1)
        pad = 0
        if h1 <= MIN_HEIGHT or w1 / float(h1) > WH_RATIO:
            new_h = max(int(w1 / WH_RATIO), MIN_HEIGHT) * 2
            pad = int(abs(new_h - h1) / 2)
            img = np.pad(img, ((pad, pad), (0, 0), (0, 0)), mode='edge')
        h, w = img.shape[:2]
        r = DET_LIMIT / float(min(h, w)) if min(h, w) < DET_LIMIT else 1.0
        rh, rw = max(32, int(round(int(h * r) / 32.0) * 32)), max(32, int(round(int(w * r) / 32.0) * 32))
        x = _resize(img[:, :, ::-1].copy(), rw, rh).astype(np.float32)
        x = ((x / 255.0 - 0.5) / 0.5).transpose(2, 0, 1)[None].astype(np.float32)
        pred = self.det.run(None, {self.det.get_inputs()[0].name: x})[0][0, 0]
        mask = pred > DET_THRESH
        dil = mask.copy()
        dil[:-1, :] |= mask[1:, :]
        dil[:, :-1] |= mask[:, 1:]
        dil[:-1, :-1] |= mask[1:, 1:]
        out = []
        ph, pw = pred.shape
        for x0, y0, x1, y1 in _components(dil):
            bw, bh = x1 - x0, y1 - y0
            if min(bw, bh) < MIN_SIZE:
                continue
            score = float(pred[y0:y1 + 1, x0:x1 + 1].mean())
            if score < BOX_THRESH:
                continue
            d = bw * bh * UNCLIP / (2.0 * (bw + bh))
            if min(bw, bh) + 2 * d < MIN_SIZE + 2:
                continue
            ex0, ey0, ex1, ey1 = x0 - d, y0 - d, x1 + d, y1 + d
            bx0 = np.clip(round(ex0 / pw * w), 0, w)
            bx1 = np.clip(round(ex1 / pw * w), 0, w)
            by0 = np.clip(round(ey0 / ph * h), 0, h) - pad
            by1 = np.clip(round(ey1 / ph * h), 0, h) - pad
            out.append((int(max(0, round(bx0 * sx))), int(max(0, round(by0 * sy))),
                        int(min(w0, round(bx1 * sx))), int(min(h0, round(by1 * sy))), score))
        out = [b for b in out if b[2] - b[0] >= 2 and b[3] - b[1] >= 2]
        out.sort(key=lambda b: b[1])
        lines, last = [], None
        for b in out:
            if last is None or b[1] - last >= 10:
                lines.append([])
            lines[-1].append(b)
            last = b[1]
        return [b for line in lines for b in sorted(line, key=lambda b: b[0])]

    def recognize(self, crops):
        res = [('', 0.0)] * len(crops)
        order = np.argsort([c.shape[1] / float(c.shape[0]) for c in crops])
        for s in range(0, len(crops), REC_BATCH):
            ids = order[s:s + REC_BATCH]
            ratio = max([REC_W / float(REC_H)] + [crops[i].shape[1] / float(crops[i].shape[0]) for i in ids])
            width = int(REC_H * ratio)
            batch = []
            for i in ids:
                c = crops[i]
                rw = min(width, int(math.ceil(REC_H * c.shape[1] / float(c.shape[0]))))
                x = _resize(c, rw, REC_H).astype(np.float32).transpose(2, 0, 1) / 255.0
                x = (x - 0.5) / 0.5
                padded = np.zeros((3, REC_H, width), dtype=np.float32)
                padded[:, :, :rw] = x
                batch.append(padded)
            preds = self.rec.run(None, {self.rec.get_inputs()[0].name: np.stack(batch)})[0]
            idx, prob = preds.argmax(axis=2), preds.max(axis=2)
            for k, i in enumerate(ids):
                chars, confs, last = [], [], -1
                for t in range(idx.shape[1]):
                    c = int(idx[k, t])
                    if c != last and c != 0:
                        chars.append(self.chars[c] if c < len(self.chars) else '')
                        confs.append(float(prob[k, t]))
                    last = c
                res[i] = (''.join(chars), float(np.mean(confs)) if confs else 0.0)
        return res

    def __call__(self, im):
        rgb = np.asarray(flatten(im))
        boxes = self.detect(rgb)
        if not boxes:
            return []
        bgr = rgb[:, :, ::-1]
        crops = []
        for x0, y0, x1, y1, _s in boxes:
            c = np.ascontiguousarray(bgr[y0:y1, x0:x1])
            if c.shape[0] >= 1.5 * c.shape[1]:
                c = np.ascontiguousarray(np.rot90(c))
            crops.append(c)
        out = []
        for (x0, y0, x1, y1, _s), (t, conf) in zip(boxes, self.recognize(crops)):
            if t.strip() and conf >= TEXT_SCORE:
                out.append({'box': (x0, y0, x1, y1), 'text': t, 'conf': conf})
        return out
