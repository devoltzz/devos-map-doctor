# Reads and rewrites the object data files of a map (war3map.w3u, .w3t, .w3a...).
import importlib.util
import os
import struct
import sys


HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = HERE


def common_module(fname):
    hash_key = '_kk_' + fname
    mod = sys.modules.get(hash_key)
    if mod is None and getattr(sys, 'frozen', False) and not os.path.isfile(os.path.join(SCRIPTS, fname + '.py')):
        mod = sys.modules[hash_key] = importlib.import_module(fname)
    if mod is None:
        spec = importlib.util.spec_from_file_location(hash_key, os.path.join(SCRIPTS, fname + '.py'))
        mod = importlib.util.module_from_spec(spec)
        sys.modules[hash_key] = mod
        spec.loader.exec_module(mod)
    return mod


slk = common_module('slk')

VERSIONS = (1, 2)


class ObjectError(Exception):
    pass


def read_objects_bytes(d, with_levels, fname='(bytes)', with_end=False):
    if len(d) < 12:
        raise ObjectError('%s: short file (%d bytes)' % (fname, len(d)))
    ver = struct.unpack_from('<I', d, 0)[0]
    if ver not in VERSIONS:
        raise ObjectError('%s: version %d not supported (measured in the collection: %s; the Reforged version 3 '
                          'has a different layout per object)' % (fname, ver, VERSIONS))
    pos = 4
    objects = []
    try:
        for table in (0, 1):
            n = struct.unpack_from('<I', d, pos)[0]
            pos += 4
            for _ in range(n):
                orig = d[pos:pos + 4].decode('latin-1')
                new = d[pos + 4:pos + 8].decode('latin-1')
                cnt = struct.unpack_from('<I', d, pos + 8)[0]
                pos += 12
                mods = []
                for _ in range(cnt):
                    field_id = d[pos:pos + 4].decode('latin-1')
                    kind = struct.unpack_from('<I', d, pos + 4)[0]
                    pos += 8
                    level = pointer = 0
                    if with_levels:
                        level, pointer = struct.unpack_from('<II', d, pos)
                        pos += 8
                    if kind == 0:
                        val = struct.unpack_from('<i', d, pos)[0]
                        pos += 4
                    elif kind in (1, 2):
                        val = struct.unpack_from('<f', d, pos)[0]
                        pos += 4
                    elif kind == 3:
                        e = d.index(b'\0', pos)
                        val = d[pos:e]
                        pos = e + 1
                    else:
                        raise ObjectError('%s: value type %d in field %r of object %r (byte %d): the '
                                          'file is not of this format or the level decision is '
                                          'wrong (with_levels=%s)' % (fname, kind, field_id, new or orig,
                                                                      pos - 8, with_levels))
                    end_pos = d[pos:pos + 4]
                    pos += 4
                    if with_end:
                        if len(end_pos) != 4:
                            raise ValueError('truncated end of record')
                        mods.append((field_id, kind, level, pointer, val, end_pos))
                    else:
                        mods.append((field_id, kind, level, pointer, val))
                objects.append((table, orig, new, mods))
    except (struct.error, ValueError) as e:
        raise ObjectError('%s: the file ended in the middle of an object (byte %d of %d; with_levels=%s): %s'
                          % (fname, pos, len(d), with_levels, e))
    if pos > len(d):
        raise ObjectError('%s: read %d bytes past the end (with_levels=%s)' % (fname, pos - len(d), with_levels))
    if pos != len(d) and d[pos:].strip(b'\0'):
        raise ObjectError('%s: %d bytes left over after the last object (with_levels=%s)'
                          % (fname, len(d) - pos, with_levels))
    return ver, objects, pos


def write_objects_bytes(ver, objects, with_levels):
    if ver not in VERSIONS:
        raise ObjectError('write: version %r not supported (%s)' % (ver, VERSIONS))
    out = [struct.pack('<I', ver)]
    for table in (0, 1):
        cluster = [o for o in objects if o[0] == table]
        out.append(struct.pack('<I', len(cluster)))
        for _t, orig, new, mods in cluster:
            ids = (orig + new).encode('latin-1')
            if len(ids) != 8:
                raise ObjectError('write: ids %r/%r do not have 4 characters each' % (orig, new))
            out.append(ids + struct.pack('<I', len(mods)))
            for m in mods:
                field_id, kind, level, pointer, val = m[:5]
                end_pos = m[5] if len(m) > 5 else b'\0\0\0\0'
                field_bytes = field_id.encode('latin-1')
                if len(field_bytes) != 4 or len(end_pos) != 4:
                    raise ObjectError(
                        'write: field %r or end %r of object %r malformed' % (field_id, end_pos, new or orig)
                    )
                out.append(field_bytes + struct.pack('<I', kind))
                if with_levels:
                    out.append(struct.pack('<II', level, pointer))
                if kind == 0:
                    if not isinstance(val, int):
                        raise ObjectError('write: %r of %r is type 0 (int) and got %r' % (field_id, new or orig, val))
                    out.append(struct.pack('<i', val))
                elif kind in (1, 2):
                    out.append(struct.pack('<f', float(val)))
                elif kind == 3:
                    if not isinstance(val, (bytes, bytearray)) or b'\0' in val:
                        raise ObjectError('write: %r of %r is type 3 (text as bytes, without \\0) and got %r'
                                          % (field_id, new or orig, val))
                    out.append(bytes(val) + b'\0')
                else:
                    raise ObjectError('write: value type %r in field %r of object %r' % (kind, field_id, new or orig))
                out.append(end_pos)
    return b''.join(out)

