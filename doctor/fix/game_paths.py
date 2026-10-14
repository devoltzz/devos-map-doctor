# The paths of the installed game in every layer of its storage, for the checks that compare with it.
import re



RX_LAYER = re.compile(r'\Awar3\.w3mod:(?:(?:_locales\\)?[^\\:]+\.w3mod:)*')
_OPEN = []


def norm(path):
    return path.replace('/', '\\').lstrip('\\').lower()


class GameFiles(object):
    def __init__(self, casc):
        self.casc = casc
        self._by = {}
        for key in casc.file_set:
            m = RX_LAYER.match(key)
            short = key[m.end():] if m else key
            self._by.setdefault(short, []).append(key)

    def has(self, path):
        return norm(path) in self._by

    def names(self):
        return set(self._by)

    def _order(self, keys):
        def rank(k):
            if k.startswith('war3.w3mod:_hd.w3mod:'):
                return 1
            if '_locales\\enus.w3mod:' in k:
                return 2
            return 0 if k.count('.w3mod:') == 1 else 3
        return sorted(keys, key=rank)

    def read(self, path):
        for key in self._order(self._by.get(norm(path), ())):
            try:
                return self.casc.read_data(key)
            except Exception:
                continue
        return None

    def glob(self, ext):
        return sorted(n for n in self._by if n.endswith(ext))


def open_game(casc=None):
    if casc is None:
        try:
            from doctor.mpq import import_lint
            casc = import_lint.game_storage()
        except Exception:
            casc = None
    if casc is None:
        return None
    for c, g in _OPEN:
        if c is casc:
            return g
    g = GameFiles(casc)
    _OPEN.insert(0, (casc, g))
    del _OPEN[2:]
    return g
