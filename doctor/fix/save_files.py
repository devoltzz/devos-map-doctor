# Reads Warcraft III save games (.w3z, .w3v): the container, its checks, the map and the game.
import json
import os
import struct
import zlib


KINDS = {'.w3z': 'saved game', '.w3v': 'campaign cache (game caches)'}
REPLAY_MAGIC = b'Warcraft III recorded game\x1a\x00'
MPQ_MAGIC = b'MPQ\x1a'
HEADER_V1 = struct.Struct('<28sIIIII4sIHHII')
BLOCK_V1 = struct.Struct('<III')
MAX_PAYLOAD = 512 * 1024 * 1024
MPQ_SCAN = 64 * 1024 * 1024


class SaveError(Exception):
    pass


def kind_of(path):
    return KINDS.get(os.path.splitext(str(path))[1].lower())


def _fold(x):
    return (x ^ (x >> 16)) & 0xffff


def _game_of_build(build):
    try:
        from doctor.fix import game_builds
        rows = game_builds.by_editor(build)
    except Exception:
        return None
    if not rows:
        return None
    first, last = rows[0].get('label'), rows[-1].get('label')
    return first if first == last else '%s to %s' % (first, last)


def _container(data):
    if data.startswith(REPLAY_MAGIC):
        return 'replay'
    for off in range(0, min(len(data), MPQ_SCAN), 512):
        if data[off:off + 4] == MPQ_MAGIC:
            return 'mpq'
    return None


def read_replay_container(data):
    if len(data) < HEADER_V1.size or not data.startswith(REPLAY_MAGIC):
        raise SaveError('not a replay container (no "Warcraft III recorded game" header)')
    (_magic, hsize, fsize, hver, dsize, nblocks, product, version, build, flags, length,
     crc) = HEADER_V1.unpack_from(data, 0)
    if hver != 1 or hsize < HEADER_V1.size:
        raise SaveError('header version %d (size %d): only version 1 (the games from 1.07 on) is read' % (hver, hsize))
    if dsize > MAX_PAYLOAD:
        raise SaveError('the header asks for %d decompressed bytes' % dsize)
    head = bytearray(data[:HEADER_V1.size])
    head[0x40:0x44] = b'\0\0\0\0'
    header = {'header_size': hsize, 'file_size': fsize, 'header_version': hver, 'decompressed_size': dsize,
              'blocks': nblocks, 'product': product[::-1].decode('latin-1'), 'version': version, 'build': build,
              'flags': flags, 'length_ms': length, 'game': _game_of_build(build)}
    checks = {'header_crc': zlib.crc32(bytes(head)) == crc, 'file_size': fsize == len(data), 'bad_blocks': [],
              'truncated': False}
    out = bytearray()
    blocks = []
    off = hsize
    for i in range(nblocks):
        if off + BLOCK_V1.size > len(data):
            checks['truncated'] = True
            break
        csize, bsize, ck = BLOCK_V1.unpack_from(data, off)
        body = data[off + BLOCK_V1.size:off + BLOCK_V1.size + csize]
        bh = bytearray(data[off:off + BLOCK_V1.size])
        bh[8:12] = b'\0\0\0\0'
        ok = (_fold(zlib.crc32(bytes(bh))) | _fold(zlib.crc32(body)) << 16) == ck
        try:
            raw = zlib.decompressobj().decompress(body)
        except zlib.error as e:
            raw = b''
            ok = False
            checks.setdefault('errors', []).append('block %d: %s' % (i, e))
        if not ok:
            checks['bad_blocks'].append(i)
        if len(body) < csize:
            checks['truncated'] = True
        blocks.append({'index': i, 'offset': off, 'compressed': csize, 'decompressed': bsize, 'read': len(raw),
                       'checksum_ok': ok})
        out += raw
        off += BLOCK_V1.size + csize
        if len(out) > MAX_PAYLOAD:
            raise SaveError('the blocks give more than %d bytes' % MAX_PAYLOAD)
    if len(out) < dsize:
        checks['truncated'] = True
    return {'header': header, 'checks': checks, 'blocks': blocks, 'payload': bytes(out[:dsize])}


def decode_settings(enc):
    out = bytearray()
    for p in range(0, len(enc), 8):
        mask = enc[p]
        for q, c in enumerate(enc[p + 1:p + 8]):
            out.append(c if mask & (1 << (q + 1)) else (c - 1) & 0xff)
    return bytes(out)


def _cstr(data, off):
    end = data.find(b'\0', off)
    if end < 0:
        raise SaveError('no string end at %d' % off)
    return data[off:end], end + 1


def _text(b):
    return b.decode('utf-8', 'replace')


def game_record(payload):
    try:
        map_path, off = _cstr(payload, 0)
        if payload[off:off + 6] != b'\0\0\xff\xff\xff\xff':
            return {'map': _text(map_path), 'error': 'unexpected bytes after the map path: %s' %
                    payload[off:off + 6].hex()}
        name, off = _cstr(payload, off + 6)
        off += 1
        enc, off = _cstr(payload, off)
        s = decode_settings(enc)
        settings = {}
        if len(s) >= 13:
            settings = {'flags': struct.unpack_from('<I', s, 0)[0], 'width': struct.unpack_from('<H', s, 5)[0],
                        'height': struct.unpack_from('<H', s, 7)[0],
                        'map_checksum': '%08x' % struct.unpack_from('<I', s, 9)[0]}
            m, o = _cstr(s, 13)
            h, o = _cstr(s, o)
            settings.update({'map': _text(m), 'host': _text(h)})
            rest = s[o + 1:]
            if len(rest) >= 20:
                settings['map_sha1'] = rest[:20].hex()
        players = struct.unpack_from('<I', payload, off)[0] if off + 4 <= len(payload) else None
        return {'map': _text(map_path), 'game_name': _text(name), 'settings': settings, 'players': players,
                'state_offset': off + 4, 'state_bytes': max(0, len(payload) - off - 4)}
    except (SaveError, struct.error) as e:
        return {'error': str(e)}


def _mpq_names(path):
    from doctor.mpq import mpqread
    a = mpqread.Archive(path)
    names = mpqread.listfile_names(a)
    out = []
    for n in names:
        try:
            b = a.read(n)
        except Exception:
            b = None
        out.append((n, len(b) if b is not None else None))
    return a, out


def read(path):
    with open(path, 'rb') as f:
        data = f.read()
    r = {'path': path, 'kind': kind_of(path), 'size': len(data), 'container': _container(data), 'notes': []}
    if r['kind'] is None:
        r['notes'].append('the extension is not .w3z or .w3v')
    if r['container'] == 'replay':
        r.update(read_replay_container(data))
        p = r['payload']
        if r['kind'] == KINDS['.w3z']:
            r['record'] = game_record(p)
        elif not p.strip(b'\0'):
            r['notes'].append('the cache is empty (%d zero bytes)' % len(p))
    elif r['container'] == 'mpq':
        _a, r['mpq_files'] = _mpq_names(path)
        r['notes'].append('an MPQ archive (the classic games\' saves, no sample measured): the files of its (listfile)')
    else:
        r['notes'].append('neither the replay container nor an MPQ archive: not a save this version reads')
    return r


def diag(path):
    r = read(path)
    out = dict((k, v) for k, v in r.items() if k != 'payload')
    lines = ['%s: %s, %d bytes' % (os.path.basename(path), r['kind'] or 'unknown kind', r['size'])]
    if r['container'] == 'replay':
        h, c = r['header'], r['checks']
        lines.append('container: the replay format (header version %d, product %s, version %d, build %d%s)' % (
            h['header_version'], h['product'], h['version'], h['build'],
            ', game %s' % h['game'] if h['game'] else ''))
        lines.append('payload: %d bytes in %d blocks; header CRC %s; block checksums %s%s' % (
            h['decompressed_size'], h['blocks'], 'ok' if c['header_crc'] else 'WRONG',
            'ok' if not c['bad_blocks'] else 'WRONG in %s' % c['bad_blocks'],
            '; TRUNCATED' if c['truncated'] else ''))
        rec = r.get('record') or {}
        if rec.get('map'):
            lines.append('map: %s' % rec['map'])
        if rec.get('game_name'):
            lines.append('game: %s, %s players; state: %d bytes (not parsed)' % (
                rec['game_name'], rec.get('players'), rec.get('state_bytes') or 0))
        if rec.get('error'):
            lines.append('game record: %s' % rec['error'])
    elif r['container'] == 'mpq':
        lines.append('container: an MPQ archive, %d listed files' % len(r['mpq_files']))
    lines.extend(r['notes'])
    out['lines'] = lines
    out['ok'] = r['container'] == 'replay' and r['checks']['header_crc'] and not r['checks']['bad_blocks'] and \
        not r['checks']['truncated'] or r['container'] == 'mpq'
    return out


def files(path):
    r = read(path)
    if r['container'] == 'replay':
        return [('header.json', None), ('payload.bin', len(r['payload']))]
    if r['container'] == 'mpq':
        return list(r['mpq_files'])
    return []


def _safe_join(root, name):
    parts = [p for p in name.replace('\\', '/').split('/') if p not in ('', '.', '..')]
    if not parts or ':' in parts[0]:
        raise SaveError('a name outside the folder: %s' % name)
    return os.path.join(root, *parts)


def extract(path, to):
    if not to:
        raise SaveError('extract needs a folder (--to=)')
    os.makedirs(to, exist_ok=True)
    written = []
    r = read(path)
    if r['container'] == 'replay':
        p = os.path.join(to, 'payload.bin')
        with open(p, 'wb') as f:
            f.write(r['payload'])
        written.append(p)
        meta = dict((k, v) for k, v in r.items() if k not in ('payload',))
        p = os.path.join(to, 'header.json')
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=1, ensure_ascii=False)
        written.append(p)
    elif r['container'] == 'mpq':
        a, names = _mpq_names(path)
        for n, _size in names:
            try:
                b = a.read(n)
            except Exception:
                continue
            p = _safe_join(to, n)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, 'wb') as f:
                f.write(b)
            written.append(p)
    else:
        raise SaveError('not a save this version reads')
    return written

