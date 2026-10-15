# Large RLE TGA textures saved uncompressed so Reforged draws them.
import struct



RLE_LIMIT = 600000


def without_rle(data_bytes, out_limit=RLE_LIMIT):
    if not data_bytes or len(data_bytes) < 18 or data_bytes[2] not in (9, 10, 11):
        return None
    w, h = struct.unpack_from('<HH', data_bytes, 12)
    if w * h <= out_limit:
        return None
    from doctor.viewers import map_card
    w, h, rgba, _fmt = map_card.tga_decode(data_bytes)
    return map_card.tga_bytes(w, h, rgba)


def map_own(name_list, ler, log=None, out_limit=RLE_LIMIT):
    out = {}
    seen = set()
    failures = []
    for n in name_list:
        k = n.replace('/', '\\').lower()
        if not k.endswith('.tga') or k in seen:
            continue
        seen.add(k)
        try:
            new = without_rle(ler(n), out_limit)
        except Exception as e:
            failures.append('%s (%s)' % (n, type(e).__name__))
            new = None
        if new is not None:
            out[n] = new
    if log and out:
        log('   %d large RLE TGA texture(s) saved uncompressed (Reforged draws them white): %s'
            % (len(out), ', '.join(sorted(out)[:6])))
    if log and failures:
        log('   %d TGA texture(s) could not be read and stay as they are (one may show white): %s'
            % (len(failures), ', '.join(failures[:6])))
    return out
