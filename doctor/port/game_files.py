# Finds and removes the map files that replace the game's own icons, textures and models.
import collections
import os


IMAGE_EXTS = ('.blp', '.tga', '.dds')
TEMPLATE = ('.mdx', '.mdl')


def candidates(game_path):
    fname = game_path.split(':')[-1].replace('/', '\\')
    base, ext = os.path.splitext(fname)
    ext = ext.lower()
    if ext in IMAGE_EXTS:
        return [base + e for e in IMAGE_EXTS]
    if ext in TEMPLATE:
        return [base + e for e in TEMPLATE]
    return []


def shadowed(map_path, casc=None):
    from doctor.mpq import mpqread
    if casc is None:
        from doctor.data import casc_wc3
        casc = casc_wc3.CascWC3()
    a = mpqread.Archive(map_path) if isinstance(map_path, str) else map_path
    seen = set()
    matches = []
    for k in casc.file_set:
        for cn in candidates(k):
            hash_key = cn.lower()
            if hash_key in seen:
                continue
            seen.add(hash_key)
            try:
                if a.find(cn) is not None:
                    matches.append(cn)
            except Exception:
                pass
    return sorted(matches, key=str.lower)


def count_by_folder(name_list):
    return collections.Counter('\\'.join(n.split('\\')[:-1]) or '.' for n in name_list).most_common()


def remove(map_path, name_list):
    if not name_list:
        return 0
    from doctor.mpq import mpqadd
    mpqadd.add_files(map_path, [], list(name_list), log=lambda *a: None)
    return len(name_list)
