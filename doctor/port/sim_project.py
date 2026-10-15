# The project settings of the simulator (none in the program: the defaults).
import os
import sys



def parameter(fname, default_value=None, proj=None):
    import json
    p = proj or finds()
    file_ = os.path.join(p, 'port', 'simulador.json') if p else None
    if file_ and os.path.isfile(file_):
        try:
            with open(file_, encoding='utf-8') as f:
                d = json.load(f)
            if not isinstance(d, dict):
                raise ValueError('the content is not a JSON object')
        except ValueError as e:
            raise ValueError('%s: %s' % (file_, e))
        return d.get(fname, default_value)
    return default_value


def finds(argv=None):
    for a in (sys.argv[1:] if argv is None else argv):
        if a.startswith('--proj='):
            return os.path.abspath(a.split('=', 1)[1])
    p = os.environ.get('KK_PROJETO')
    if p:
        return os.path.abspath(p)
    p = os.getcwd()
    while True:
        if os.path.isdir(os.path.join(p, 'port')):
            return p
        parent = os.path.dirname(p)
        if parent == p:
            return None
        p = parent
