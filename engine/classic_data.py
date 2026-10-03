# Writes the object data the old game inherited and Warcraft III 3.0 gives differently.
import hashlib
import os

import objects


CLASSIC_HERITAGE = 'custom_v1'
DEFAULT_RULES = (('war3map.w3t', 'item', ('icla', 'iuse')), ('war3map.w3a', 'ability', ('areq',)))


def regras_padrao(extract, ext_en=None):
    regras = []
    for file_, obj_kind, codes in DEFAULT_RULES:
        cands = ([os.path.join(ext_en, file_)] if ext_en else []) + [os.path.join(extract, file_)]
        entry = next((c for c in cands if os.path.isfile(c)), None)
        if entry:
            regras.append((file_, entry, obj_kind, dict((c, None) for c in codes)))
    return tuple(regras)


def _sha(b):
    return hashlib.sha256(b).hexdigest()[:16]


def _key(o):
    return o[2] if o[2].strip('\0') else o[1]


def _text(v):
    return v.decode('utf-8') if isinstance(v, (bytes, bytearray)) else v


def applies(regras, root, data_bytes, expected_count=None, gravar=True, current=None, classic=None):
    failures = []
    info = {'regras': [], 'counts': {}, 'medido': {}}
    if current is None:
        current = objects.GameBase(balance=None)
    if classic is None:
        classic = objects.GameBase(casc=current.casc, balance=CLASSIC_HERITAGE)
    to_write = []
    for file_, entry, obj_kind, locks in regras:
        rot = '%s (%s)' % (file_, os.path.relpath(entry, root).replace(os.sep, '/'))
        d = open(entry, 'rb').read()
        with_levels = objects.uses_levels(file_)
        try:
            ver, objs, _pos = objects.read_objects_bytes(d, with_levels, file_, with_end=True)
        except objects.ObjectError as e:
            failures.append('%s: cannot read: %s' % (rot, e))
            continue
        if objects.write_objects_bytes(ver, objs, with_levels) + d[_pos:] != d:
            failures.append('%s: the round trip through the writer does NOT return the file byte for byte' % rot)
            continue
        codes = tuple(locks)
        listing, nameless = objects.divergent_inheritance(objs, obj_kind, codes, current, classic)
        for code_part in codes:
            medido = dict(
                (ch, _text(classic_val)) for ch, _o, c, _t, classic_val, _current_val in listing if c == code_part
            )
            locked = locks[code_part]
            if locked is None:
                info['medido'][code_part] = medido
            elif medido != locked:
                leftover = sorted(set(medido) - set(locked))
                missing = sorted(set(locked) - set(medido))
                field_value = sorted(k for k in set(medido) & set(locked) if medido[k] != locked[k])
                failures.append(
                    '%s: rule `%s` in CASC gave %d object(s), the lock has %d (%s more, %s fewer, '
                    'different value %s) -- the game data changed: measure before saving'
                    % (rot, code_part, len(medido), len(locked), leftover[:6], missing[:6], field_value[:6])
                )
            info['counts'][code_part] = len(medido)
        new_ones = objects.add_modifications(objs, listing, current.metadata(obj_kind))
        file_data_bytes = objects.write_objects_bytes(ver, new_ones, with_levels)
        try:
            ver2, objs2, pos2 = objects.read_objects_bytes(file_data_bytes, with_levels, file_, with_end=True)
        except objects.ObjectError as e:
            failures.append('%s: the written file could not be read back: %s' % (rot, e))
            continue
        list_ids = set(ch for ch, *_r in listing)
        differs = set()
        for o1, o2 in zip(objs, objs2):
            if o1 != o2:
                differs.add(_key(o1))
                if o1[:3] != o2[:3] or o2[3][:len(o1[3])] != o1[3]:
                    failures.append('%s: object %s changed beyond the end of the modifications' % (rot, _key(o1)))
        if len(objs2) != len(objs) or pos2 != len(file_data_bytes) or differs != list_ids:
            failures.append('%s: reread %d objects / %d of %d bytes; %d objects differ, the list has %d'
                            % (rot, len(objs2), pos2, len(file_data_bytes), len(differs), len(list_ids)))
        rest, _without2 = objects.divergent_inheritance(objs2, obj_kind, codes, current, classic)
        if rest:
            failures.append('%s: after the fix the rule still gives %d: %s' % (rot, len(rest), rest[:3]))
        output = os.path.join(data_bytes, file_)
        igual = os.path.exists(output) and open(output, 'rb').read() == file_data_bytes
        info['regras'].append(
            {
                'file_name': file_,
                'entry': os.path.relpath(entry, root),
                'entry_bytes': len(d),
                'input_sha': _sha(d),
                'objects': len(objs),
                'no_classic': len(nameless),
                'touched_geosets': len(list_ids),
                'modifications': len(listing),
                'bytes': len(file_data_bytes),
                'sha': _sha(file_data_bytes),
                'output': os.path.relpath(output, root),
                'status': 'was already written' if igual else ('saved' if gravar else 'to write'),
            }
        )
        if not igual:
            to_write.append((output, file_data_bytes))
    info['medidas'] = dict(info['counts'])
    if expected_count is not None and info['counts'] != dict(expected_count):
        failures.append('counts %s, the kk_monta expected ones are %s' % (info['counts'], dict(expected_count)))
    if failures or not gravar:
        return failures, info
    os.makedirs(data_bytes, exist_ok=True)
    for output, file_data_bytes in to_write:
        with open(output, 'wb') as f:
            f.write(file_data_bytes)
    return failures, info


def report_data(info):
    for r in info['regras']:
        print('classic data: %s <- %s (%d B, sha %s): %d objects, %d touched, %d modifications -> %d B (+%d), sha %s, '
              '%s' % (r['output'].replace(os.sep, '/'), r['entry'].replace(os.sep, '/'), r['entry_bytes'],
                      r['input_sha'], r['objects'], r['touched_geosets'], r['modifications'], r['bytes'],
                      r['bytes'] - r['entry_bytes'], r['sha'], r['status']))
    print('classic data: counts %s' % info['counts'])
    for code_part, medido in sorted(info.get('medido', {}).items()):
        print('classic data: `%s` WITHOUT LOCK, measured (%d): %s' % (code_part, len(medido), medido))
