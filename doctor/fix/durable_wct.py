# Keeps a readable copy of a cheat pack in the map's triggers, so a save in the World Editor keeps it.
import re



TAG = 'DOCTOR-DURABLE'


def _comment(lua):
    return '--' if lua else '//'


def _sentinels(label, lua):
    c = _comment(lua)
    return '%s %s:%s:start' % (c, TAG, label), '%s %s:%s:end' % (c, TAG, label)


def _eol(text):
    return '\r\n' if text.count('\r\n') * 2 > text.count('\n') else '\n'


def block_of(text, label, lua=False):
    start, end = _sentinels(label, lua)
    i = (text or '').find(start)
    if i < 0:
        return None
    j = text.find(end, i + len(start))
    if j < 0:
        raise ValueError(
            'the sentinel %r has no end line: the block was edited by hand; remove it and try again' % start
        )
    return text[i + len(start):j].strip('\r\n')


def put(text, label, code, lua=False, indent=''):
    text = text or ''
    start, end = _sentinels(label, lua)
    eol = _eol(text) if text else '\n'
    code = code.replace('\r\n', '\n').strip('\n')
    new = start + eol + eol.join(indent + ln if ln.strip() else ln for ln in code.split('\n')) + eol + indent + end
    i = text.find(start)
    if i >= 0:
        j = text.find(end, i + len(start))
        if j < 0:
            raise ValueError('the sentinel %r has no end line: the block was edited by hand; remove it and try again'
                             % start)
        return text[:i] + new + text[j + len(end):]
    if not text.strip():
        return new + eol
    return text.rstrip('\r\n') + eol + eol + new + eol


def take(text, label, lua=False):
    text = text or ''
    start, end = _sentinels(label, lua)
    i = text.find(start)
    if i < 0:
        return text, False
    j = text.find(end, i + len(start))
    if j < 0:
        raise ValueError(
            'the sentinel %r has no end line: the block was edited by hand; remove it and try again' % start
        )
    k = j + len(end)
    if text[k:k + 2] == '\r\n':
        k += 2
    elif text[k:k + 1] == '\n':
        k += 1
    ls = text.rfind('\n', 0, i) + 1
    before = text[:ls if not text[ls:i].strip() else i]
    after = text[k:]
    if not before.strip():
        return after.lstrip('\r\n'), True
    if not after.strip():
        return before.rstrip('\r\n'), True
    return before + after, True


RX_INIT_JASS = re.compile(
    r'(?m)^[ \t]*function[ \t]+InitTrig_\w+[ \t]+takes[ \t]+nothing[ \t]+returns[ \t]+nothing[ \t]*\r?\n'
)
RX_INIT_LUA = re.compile(r'(?m)^[ \t]*function[ \t]+InitTrig_\w+[ \t]*\([ \t]*\)[ \t]*\r?\n')


def _after_locals(text, pos, lua):
    n = len(text)
    while pos < n:
        e = text.find('\n', pos)
        e = n if e < 0 else e + 1
        line = text[pos:e].strip()
        if not line or line.startswith('//') and not lua or line.startswith('--') and lua \
                or (not lua and line.startswith('local ')):
            pos = e
            continue
        break
    return pos


def put_entry(text, label, statement, lua=False):
    if block_of(text, label, lua) is not None:
        return put(text, label, statement, lua, indent='    ')
    m = (RX_INIT_LUA if lua else RX_INIT_JASS).search(text)
    if not m:
        return None
    pos = _after_locals(text, m.end(), lua)
    start, end = _sentinels(label, lua)
    eol = _eol(text)
    indent = '    '
    block = indent + start + eol + indent + statement.strip() + eol + indent + end + eol
    return text[:pos] + block + text[pos:]


def _entry_label(label):
    return label + ':entry'


def write(wct, code, label, entry=None, lua=False):
    from doctor.triggers import wtg
    ct = wtg.read_wct(wct)
    if ct.version < 1:
        raise ValueError('a Reign of Chaos war3map.wct (version 0) has no custom script header')
    ct.header = put(ct.header or '', label, code, lua)
    info = {'header': True, 'entry': None, 'entry_reason': None}
    if entry is not None:
        el = _entry_label(label)
        done = False
        for i, t in enumerate(ct.texts):
            if t is None:
                continue
            new = put_entry(t, el, entry, lua)
            if new is not None:
                ct.texts[i] = new
                info['entry'] = 'trigger #%d' % i
                done = True
                break
        if not done:
            info['entry_reason'] = ('the map has no custom text trigger with an InitTrig_ function: the code is kept, '
                                    'but nothing calls it after the next save in the World Editor')
    return wtg.write_wct(ct), info


def read(wct, label, lua=False):
    from doctor.triggers import wtg
    ct = wtg.read_wct(wct)
    el = _entry_label(label)
    out = {'header': block_of(ct.header or '', label, lua), 'entry': None, 'trigger': None}
    for i, t in enumerate(ct.texts):
        if t is not None:
            b = block_of(t, el, lua)
            if b is not None:
                out['entry'], out['trigger'] = b.strip(), i
                break
    return out


def remove(wct, label, lua=False):
    from doctor.triggers import wtg
    ct = wtg.read_wct(wct)
    gone = False
    if ct.header:
        ct.header, g = take(ct.header, label, lua)
        gone = gone or g
        ct.header = ct.header or None
    for i, t in enumerate(ct.texts):
        if t is not None:
            ct.texts[i], g = take(t, _entry_label(label), lua)
            gone = gone or g
    return wtg.write_wct(ct), gone
