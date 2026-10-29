# The real progress of a job: nested scopes with counts, which the page learns the length of.
import contextlib
import re
import time


INTERVAL = 0.15
RX_FRACTION = re.compile(r'^(.*?)[\s:]*\(?(\d+)\s*/\s*(\d+)\)?\s*\.{0,3}$')
RX_PERCENT = re.compile(r'^(.*?)[\s:]*(\d{1,3})\s*%\s*\.{0,3}$')
RX_OF = re.compile(r'^(.*?)[\s:]*(\d+)\s+of\s+(\d+)(?!\d)')

_emit = None
_stack = []
_last = [0.0]


def step_on(emit):
    global _emit
    _emit = emit
    del _stack[:]
    _last[0] = 0.0


def unbind():
    global _emit
    _emit = None
    del _stack[:]


def default_on():
    return _emit is not None


def current(default_value=('', '')):
    return (_stack[-1:] or [default_value])[0]


def file_path():
    return '/'.join(n for n, _r in _stack)


def _send(label, done=None, total=None):
    if _emit is None:
        return
    ev = {'type': 'progress', 'label': label, 'path': file_path()}
    if total:
        ev['done'] = max(0, min(int(done or 0), int(total)))
        ev['total'] = int(total)
    try:
        _emit(ev)
    except Exception:
        pass


def _name(body_text):
    t = re.sub(r'\d+', '', str(body_text or '').lower())
    t = re.sub(r'[^a-z_]+', '_', t).strip('_')
    return t[:40] or 'stage'


def topo(fname, label=None):
    del _stack[:]
    _stack.append((fname, label or fname))
    _send(label or fname)


@contextlib.contextmanager
def stage(fname, label=None):
    label = label or current((fname, fname))[1]
    _stack.append((fname, label))
    stack_depth = len(_stack)
    _send(label)
    try:
        yield
    finally:
        x = _stack[stack_depth - 1:stack_depth]
        if x and x[0][0] == fname:
            del _stack[stack_depth - 1:]
            if _stack:
                _send(current()[1])


def step_size(fname, label=None):
    while current()[0].startswith(('c_', 'l_')):
        del _stack[-1:]
    if current()[0].startswith('p_'):
        del _stack[-1:]
    _stack.append(('p_' + fname, label or fname))
    _send(label or fname)


def call_expr():
    if _emit is None:
        return lambda code, total=None: None
    label = current()[1]

    def p(code, total=None):
        c = None if isinstance(code, int) else label_count(code)
        if isinstance(code, int) and isinstance(total, int):
            avanca(code, total)
        elif c:
            avanca(c[1], c[2])
        elif code:
            step_size(_name(code), label)
    return p


def avanca(done, total, label=None):
    if _emit is None or not total:
        return
    current_time = time.time()
    if done < total and current_time - _last[0] < INTERVAL:
        return
    _last[0] = current_time
    _send(label or current()[1], done, total)


def detail(body_text):
    if _emit is None or not body_text:
        return
    _send(str(body_text).strip())


def label_count(body_text):
    t = str(body_text or '').strip()
    m = RX_FRACTION.match(t)
    if m and int(m.group(3)) > 0:
        return m.group(1).strip() or t, int(m.group(2)), int(m.group(3))
    m = RX_OF.match(t)
    if m and int(m.group(3)) > 0:
        return m.group(1).strip() or t, int(m.group(2)), int(m.group(3))
    m = RX_PERCENT.match(t)
    if m and int(m.group(2)) <= 100:
        return m.group(1).strip() or t, int(m.group(2)), 100
    return None


def legacy(body_text, is_stage=True, fase=True):
    if _emit is None:
        return
    c = label_count(body_text)
    if c:
        label, done, total = c
        fname = 'c_' + _name(label)
        if current()[0] != fname:
            if current()[0].startswith(('c_', 'l_')):
                del _stack[-1:]
            _stack.append((fname, label))
            _send(label)
        avanca(done, total, label)
        return
    if len(_stack) <= 1:
        if is_stage:
            topo(_name(body_text), str(body_text).strip())
        else:
            detail(body_text)
        return
    if not fase:
        detail(body_text)
        return
    fname = 'l_' + _name(body_text)
    if current()[0] == fname:
        detail(body_text)
        return
    if current()[0].startswith(('c_', 'l_')):
        del _stack[-1:]
    _stack.append((fname, str(body_text).strip()))
    _send(str(body_text).strip())
