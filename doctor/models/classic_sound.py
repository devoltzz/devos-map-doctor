# Converts the FLAC and OGG sounds of a map to MP3 through ffmpeg and points every reference at the new file.
import os
import re
import shutil



TYPES = ('flac', 'ogg')
KBPS, CHANNELS, SAMPLE_RATE = 128, 2, 44100


def name_new(n):
    high = n[-4:].isupper()
    if n.lower().endswith('.ogg'):
        return n[:-4] + ('.MP3' if high else '.mp3')
    return n[:-5] + ('F.MP3' if high else 'f.mp3')


def _is_mp3(d):
    return d[:3] == b'ID3' or (len(d) > 1 and d[0] == 0xFF and d[1] & 0xE0 == 0xE0)


def converte(entry, output, log=print, types=TYPES, ffmpeg=None):
    from doctor.models import audio_shrink
    from doctor.fix import editor_lock
    from doctor.models import dds_to_blp
    from doctor.mpq import mpqadd
    from doctor.mpq import mpqread
    entry, output = os.path.abspath(entry), os.path.abspath(output)
    if entry == output:
        raise SystemExit('the output must be another file (the input never changes)')
    types = tuple(t for t in TYPES if t in set(types))
    a = mpqread.Archive(entry)
    name_list, low = [], set()
    for n in editor_lock.map_names(a):
        if n.lower() not in low:
            low.add(n.lower())
            name_list.append(n)
    targets = [n for n in name_list if n.lower().rsplit('.', 1)[-1] in types and '.' in n]
    details = {'ok': False, 'replaced': 0, 'matrix': {}, 'no_ffmpeg': False, 'sounds': len(targets)}
    shutil.copyfile(entry, output)
    if not targets:
        details['ok'] = True
        return details
    if not audio_shrink.find_ffmpeg(ffmpeg):
        details['no_ffmpeg'] = True
        details['ok'] = True
        log('[sound] no ffmpeg: %d FLAC/OGG sound(s) stay as they are' % len(targets))
        return details
    write_out, to_delete, replaced = [], [], {}
    for n in targets:
        new = name_new(n)
        if new.lower() in low:
            details['matrix'][n] = {'action_code': 'retained', 'reason': '%s already exists in the map' % new}
            continue
        d = editor_lock._read(a, n)
        if d is None:
            continue
        try:
            mp3 = audio_shrink.reencode(d, n.rsplit('.', 1)[-1].lower(), kbps=KBPS, channels=CHANNELS, rate=SAMPLE_RATE,
                                        ffmpeg=ffmpeg)
        except Exception as e:
            details['matrix'][n] = {
                'action_code': 'not touched',
                'reason': 'ffmpeg does not read it (%s)' % str(e)[:80],
            }
            continue
        write_out.append((new, mp3))
        to_delete.append(n)
        replaced[n.lower().replace('/', '\\')] = new
        details['matrix'][n] = {
            'action_code': 'converted_file',
            'new': new,
            'bytes_before': len(d),
            'bytes_after': len(mp3),
        }
        log('[sound] %s -> %s (%d -> %d B)' % (n, new, len(d), len(mp3)))
    if not write_out:
        details['ok'] = True
        return details
    rx = dds_to_blp._rx_repoint(to_delete)

    def swap(m):
        s = m.group(0)
        if s.lower().endswith(b'.ogg'):
            return s[:-4] + (b'.MP3' if s[-4:].isupper() else b'.mp3')
        return s[:-5] + (b'F.MP3' if s[-5:].isupper() else b'f.mp3')
    rx_ext = re.compile(rb'\.(?:' + b'|'.join(t.encode() for t in types) + rb')', re.IGNORECASE)
    to_delete_low = set(x.lower() for x in to_delete)
    for n in name_list:
        if n.lower() in to_delete_low:
            continue
        d = editor_lock._read(a, n)
        if not d or not rx_ext.search(d):
            continue
        new = rx.sub(swap, d)
        if new != d:
            if len(new) != len(d):
                raise SystemExit('ABORTS (sound): the repointing changed the size of %s' % n)
            write_out.append((n, new))
            details['matrix'].setdefault(n, {})['action_code'] = 'retargeted'
    mpqadd.add_files(output, write_out, to_delete=to_delete, log=lambda *x: None)
    b = mpqread.Archive(output)
    bad_ones = [n for n, _d in write_out if n.lower().endswith('.mp3') and not _is_mp3(editor_lock._read(b, n) or b'')]
    for n in name_list:
        if n.lower() in to_delete_low:
            continue
        dd = editor_lock._read(b, n)
        if dd and rx_ext.search(dd) and rx.search(dd):
            bad_ones.append('a reference left in %s' % n)
    if bad_ones:
        raise SystemExit('ABORTS (sound): %s' % bad_ones[:5])
    details['replaced'] = len(to_delete)
    details['ok'] = True
    return details
