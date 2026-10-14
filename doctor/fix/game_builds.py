# The builds of Warcraft III and the World Editor number each one writes.
import json
import os


HERE = os.path.dirname(os.path.abspath(__file__))

NAME = 'game_builds.json'
_TABLE = {}


def _roots():
    try:
        from doctor.data import wc3_versions
        return wc3_versions._ref_roots()
    except Exception:
        return [os.path.normpath(os.path.join(HERE, '..', 'ref'))]


def patch_label(patch):
    parts = str(patch or '').lstrip('vV').split('_')
    return '.'.join(parts)


def builds():
    if 'b' not in _TABLE:
        rows = []
        for root in _roots():
            p = os.path.join(root, NAME)
            if os.path.isfile(p):
                with open(p, encoding='utf-8') as f:
                    data = json.load(f)
                cols = data.get('columns') or ['expansion', 'date', 'patch', 'version', 'editor']
                for r in data.get('builds') or []:
                    d = dict(zip(cols, r))
                    d['label'] = patch_label(d.get('patch'))
                    rows.append(d)
                break
        _TABLE['b'] = rows
    return list(_TABLE['b'])


def _game_version_text(game_version):
    if isinstance(game_version, str):
        return game_version.strip()
    try:
        return '.'.join(str(int(x)) for x in game_version)
    except (TypeError, ValueError):
        return ''


def by_version(game_version):
    want = _game_version_text(game_version)
    for b in builds():
        if b['version'] == want:
            return b
    return None


def by_editor(editor):
    try:
        n = int(editor)
    except (TypeError, ValueError):
        return []
    return [b for b in builds() if b['editor'] == n]


def _years(rows):
    ys = sorted({b['date'][:4] for b in rows if b.get('date')})
    if not ys:
        return ''
    return ys[0] if len(ys) == 1 else '%s-%s' % (ys[0], ys[-1])


def describe(editor, game_version=None):
    rows = []
    exact = False
    if game_version:
        b = by_version(game_version)
        if b is not None:
            rows, exact = [b], True
    if not rows:
        rows = by_editor(editor)
    if not rows:
        return None
    first, last = rows[0]['label'], rows[-1]['label']
    years = _years(rows)
    if len(rows) == 1 or first == last:
        what = 'World Editor %s' % first
        if exact:
            what += ' (build %s)' % rows[0]['version']
    else:
        what = 'World Editor %s to %s' % (first, last)
    text = 'saved by %s%s' % (what, ' (%s)' % years if years else '')
    return {'text': text, 'first': first, 'last': last, 'exact': exact, 'builds': rows, 'years': years}


def describe_w3i(w3i_bytes):
    import struct
    if not w3i_bytes or len(w3i_bytes) < 12:
        return None
    fmt, _saves, editor = struct.unpack_from('<iii', w3i_bytes, 0)
    gv = None
    if fmt >= 28 and len(w3i_bytes) >= 28:
        gv = list(struct.unpack_from('<4i', w3i_bytes, 12))
    return describe(editor, gv)
