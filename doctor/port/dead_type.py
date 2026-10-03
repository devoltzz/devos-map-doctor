# Removes dead platform code whose type no longer exists on Warcraft III 3.0.
import re


RX_FUNC = re.compile(r'(?m)^[ \t]*(?:constant[ \t]+)?function[ \t]+([A-Za-z_]\w*)[ \t]+takes\b')
RX_END = re.compile(r'(?m)^[ \t]*endfunction\b[^\n]*\n?')
RX_TYPE_CHECK = re.compile(r'(?m)^[ \t]*type[ \t]+([A-Za-z_]\w*)[ \t]+extends[ \t]+([A-Za-z_]\w*)[^\n]*\n?')
RX_NATIVE = re.compile(r'(?m)^[ \t]*(?:constant[ \t]+)?native[ \t]+([A-Za-z_]\w*)[ \t]+takes[^\n]*\n?')
RX_LITERAL = re.compile(r'"((?:[^"\\\n]|\\.)*)"')
RX_ID = re.compile(r'[A-Za-z_]\w*')
RX_COMMENT = re.compile(r'//[^\n]*')


def functions(body_text):
    out = []
    pos = 0
    for m in RX_FUNC.finditer(body_text):
        if m.start() < pos:
            continue
        begin = body_text.rfind('\n', 0, m.start()) + 1
        f = RX_END.search(body_text, m.end())
        if not f:
            break
        out.append((m.group(1), begin, f.end()))
        pos = f.end()
    return out


def _without_text(s):
    return RX_COMMENT.sub('', RX_LITERAL.sub('""', s))


def live_ones(body_text, fs=None):
    fs = functions(body_text) if fs is None else fs
    name_list = set(n for n, _i, _f in fs)
    refs = {}
    for n, i, f in fs:
        body = body_text[i:f]
        body = body.split('\n', 1)[1] if '\n' in body else ''
        refs.setdefault(n, set()).update(x for x in RX_ID.findall(_without_text(body)) if x in name_list and x != n)
    roots = set(x for x in ('main', 'config') if x in name_list)
    for lit in RX_LITERAL.findall(body_text):
        roots.update(x for x in RX_ID.findall(lit) if x in name_list)
    outside, pos = [], 0
    for _n, i, f in fs:
        outside.append(body_text[pos:i])
        pos = f
    outside.append(body_text[pos:])
    roots.update(x for x in RX_ID.findall(_without_text(''.join(outside))) if x in name_list)
    alive = set(roots)
    work_queue = list(roots)
    while work_queue:
        for x in refs.get(work_queue.pop(), ()):
            if x not in alive:
                alive.add(x)
                work_queue.append(x)
    return alive


def engine_types(common_j):
    return set(m.group(1) for m in RX_TYPE_CHECK.finditer(common_j)) | {
        'handle',
        'integer',
        'real',
        'boolean',
        'string',
        'code',
        'nothing',
    }


def applies(body_text, engine_type_set):
    info = {'types': [], 'kept': [], 'functions': [], 'globals_block': [], 'natives': [], 'failures': []}
    proprios = [m.group(1) for m in RX_TYPE_CHECK.finditer(body_text) if m.group(1) not in engine_type_set]
    if not proprios:
        return body_text, info
    fs = functions(body_text)
    alive = live_ones(body_text, fs)
    body = dict((n, body_text[i:f]) for n, i, f in fs)
    new = body_text
    for X in proprios:
        rx = re.compile(r'\b%s\b' % re.escape(X))
        rx_global = re.compile(
            r'(?m)^[ \t]*(?:constant[ \t]+)?%s[ \t]+(?:array[ \t]+)?([A-Za-z_]\w*)[^\n]*\n?' % re.escape(X)
        )
        globals_block = [m.group(1) for m in rx_global.finditer(new)]
        rx_uso = re.compile(r'\b(?:%s)\b' % '|'.join([re.escape(X)] + [re.escape(g) for g in globals_block]))
        if any(rx_uso.search(_without_text(body[n])) for n in alive if n in body):
            info['kept'].append(X)
            continue
        out_path = set(n for n in body if n not in alive and rx_uso.search(_without_text(body[n])))
        changed = True
        while changed:
            changed = False
            for n in body:
                if n in out_path or n in alive:
                    continue
                if any(x in out_path for x in RX_ID.findall(_without_text(body[n].split('\n', 1)[-1]))):
                    out_path.add(n)
                    changed = True
        current_funcs = functions(new)
        pieces, pos = [], 0
        for n, i, f in current_funcs:
            if n in out_path:
                pieces.append(new[pos:i])
                pos = f
        pieces.append(new[pos:])
        new = ''.join(pieces)
        nat = [m.group(1) for m in RX_NATIVE.finditer(new) if rx.search(m.group(0))]
        new = RX_NATIVE.sub(lambda m: '' if rx.search(m.group(0)) else m.group(0), new)
        new = rx_global.sub('', new)
        new = RX_TYPE_CHECK.sub(lambda m: '' if m.group(1) == X else m.group(0), new)
        info['types'].append(X)
        info['functions'] += sorted(out_path)
        info['globals_block'] += globals_block
        info['natives'] += nat
        if rx.search(_without_text(new)):
            info['failures'].append('the type %s still appears after the output' % X)
        unresolved = set(n for n, _i, _f in functions(new))
        orphans = set(x for n, i, f in functions(new) for x in RX_ID.findall(_without_text(new[i:f].split('\n', 1)[-1]))
                      if x in out_path and x not in unresolved)
        if orphans:
            info['failures'].append(
                'a function that stays calls a function that left: %s' % ', '.join(sorted(orphans)[:5])
            )
    if info['failures']:
        return body_text, info
    return new, info


def report_data(info):
    if info['types'] or info['kept']:
        print(
            '0f dead type: %d type(s) removed (%s): %d function(s), %d global(s), %d native(s); kept (used): %s'
            % (
                len(info['types']),
                ', '.join(info['types']) or '-',
                len(info['functions']),
                len(info['globals_block']),
                len(info['natives']),
                ', '.join(info['kept']) or '-',
            )
        )
    else:
        print('0f dead type: no own type of the platform')
