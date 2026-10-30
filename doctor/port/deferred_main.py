# Moves the map's own start out of the loading screen: it runs after the game starts, a piece per frame.
import re


SLICE = 100
KEEPS = ('SetCameraBounds', 'SetDayNightModels', 'SetTerrainFogEx', 'SetTerrainFog', 'NewSoundEnvironment',
         'SetAmbientDaySound', 'SetAmbientNightSound', 'SetMapMusic', 'SetWaterBaseColor')
CUTS = ('CreateUnits', 'CreateAllUnits', 'InitBlizzard')
MARK = '// [KK framework] step 9c: after the loading screen'
RX_CALL0 = re.compile(r'^call[ \t]+(\w+)[ \t]*\([ \t]*\)[ \t]*(//.*)?$')
RX_CALL = re.compile(r'^call[ \t]+(\w+)[ \t]*\(')


def _lines(s, ends=False):
    return re.findall(r'[^\n]*\n|[^\n]+', s) if ends else s.split('\n')


def _remove(line):
    return line.strip(' \t\r\n')


def _body(body_text, fname):
    m = re.search(
        r'(?m)^function[ \t]+%s[ \t]+takes[ \t]+nothing[ \t]+returns[ \t]+nothing[ \t]*\r?$' % fname, body_text
    )
    if not m:
        return None
    begin = body_text.index('\n', m.end()) + 1
    end_pos = re.compile(r'(?m)^[ \t]*endfunction\b').search(body_text, begin)
    return m.start(), begin, end_pos.start()


def _ica_locals(body_text, nl):
    pos = _body(body_text, 'main')
    if pos is None:
        return body_text, 0, None
    header, begin, end_pos = pos
    body = body_text[begin:end_pos]
    decl = []
    name_list = []
    line_list = []
    for brute in _lines(body, True):
        m = re.match(r'^([ \t]*)local[ \t]+(\w+)[ \t]+(array[ \t]+)?(\w+)[ \t]*(=[^\r\n]*)?(\r?\n)?$', brute)
        if not m:
            line_list.append(brute)
            continue
        kind, arr, fname, ini_v = m.group(2), m.group(3), m.group(4), m.group(5)
        decl.append('%s %sKK_mn_%s' % (kind, 'array ' if arr else '', fname))
        name_list.append(fname)
        if ini_v:
            line_list.append('%sset %s%s%s' % (m.group(1), fname, ini_v, m.group(6) or ''))
    if not name_list:
        return body_text, 0, None
    body = ''.join(line_list)
    for fname in name_list:
        pieces = re.split(r'("(?:[^"\\]|\\.)*"|\'[^\']*\')', body)
        body = ''.join(p if k % 2 else re.sub(r'(?<![\w$])%s(?!\w)' % re.escape(fname), 'KK_mn_' + fname, p)
                       for k, p in enumerate(pieces))
    eg = re.search(r'(?m)^endglobals[ \t]*\r?$', body_text)
    if not eg or eg.start() > header:
        return body_text, 0, 'no globals block before main'
    body_text = body_text[:begin] + body + body_text[end_pos:]
    body_text = body_text[:eg.start()] + ''.join(d + nl for d in decl) + body_text[eg.start():]
    return body_text, len(name_list), None


def applies(body_text, sector_slice=SLICE, local_vars=False):
    info = {
        'failures': [],
        'mantidas': 0,
        'frames': 0,
        'deferred_ones': 0,
        'slices': 0,
        'trigger_list': 0,
        'local_vars': 0,
    }
    if local_vars and MARK not in body_text:
        body_text, n, failure = _ica_locals(body_text, '\r\n' if '\r\n' in body_text else '\n')
        if failure:
            info['failures'].append(failure)
            return body_text, info
        info['local_vars'] = n
    if MARK in body_text:
        info['failures'].append('step 9c already ran on this text (the deferred main' + "'" + 's marker is there)')
        return body_text, info
    nl = '\r\n' if '\r\n' in body_text else '\n'
    pos = _body(body_text, 'InitCustomTriggers')
    line_list = []
    if pos is not None:
        header, begin, end_pos = pos
        line_list = [
            _remove(line)
            for line in _lines(body_text[begin:end_pos])
            if _remove(line) and not _remove(line).startswith('//')
        ]
    if line_list and all(RX_CALL0.match(line) for line in line_list):
        calls = [RX_CALL0.match(line).group(1) for line in line_list]
        block_list = [calls[i:i + sector_slice] for i in range(0, len(calls), sector_slice)]
        funcs = ''.join('function KK_adia_gat_%d takes nothing returns nothing%s    %s%s%sendfunction%s'
                        % (k + 1, nl, MARK, nl, ''.join('    call %s()%s' % (c, nl) for c in b), nl)
                        for k, b in enumerate(block_list))
        new = ''.join('    call ExecuteFunc("KK_adia_gat_%d")%s' % (k + 1, nl) for k in range(len(block_list)))
        body_text = body_text[:header] + funcs + body_text[header:begin] + new + body_text[end_pos:]
        info['slices'] = len(block_list)
        info['trigger_list'] = len(calls)
    pos = _body(body_text, 'main')
    if pos is None:
        info['failures'].append('main does not exist')
        return body_text, info
    header, begin, end_pos = pos
    keep = []
    frames = [[]]
    for brute in _lines(body_text[begin:end_pos]):
        line = _remove(brute)
        if not line:
            continue
        if line.startswith('local '):
            info['failures'].append('a local in main: %s' % line)
            return body_text, info
        m = RX_CALL.match(line)
        if m and m.group(1) in KEEPS:
            keep.append('    ' + line)
            continue
        m0 = RX_CALL0.match(line)
        if m0 and m0.group(1) in CUTS and frames[-1]:
            frames.append([])
        if m0:
            frames[-1].append(
                '    call ExecuteFunc("%s")%s' % (m0.group(1), (' ' + m0.group(2)) if m0.group(2) else '')
            )
        else:
            frames[-1].append('    ' + line)
        if not line.startswith('//'):
            info['deferred_ones'] += 1
    frames = [q for q in frames if q]
    if len(frames) == 1:
        frames.append(['    // ' + MARK[3:] + ': the end (the clock)'])
    n = len(frames)
    funcs = []
    for k in range(n, 0, -1):
        body = ['function KK_adia_%d takes nothing returns nothing' % k]
        if k < n:
            body += ['    ' + MARK,
                     '    call TimerStart(GetExpiredTimer(), 0.00, false, function KK_adia_%d)' % (k + 1)]
        else:
            body += ['    local timer t=GetExpiredTimer()', '    ' + MARK, '    call PauseTimer(t)',
                     '    call DestroyTimer(t)', '    set t=null']
        body += frames[k - 1] + ['endfunction']
        funcs.append(nl.join(body) + nl)
    new_main = (nl.join(keep + ['    ' + MARK + ' (%d frame(s))' % n,
                                '    call TimerStart(CreateTimer(), 0.00, false, function KK_adia_1)']) + nl)
    body_text = body_text[:header] + ''.join(funcs) + body_text[header:begin] + new_main + body_text[end_pos:]
    info['mantidas'] = len(keep)
    info['frames'] = n
    return body_text, info


def report_data(info):
    print('9c deferred main: %d environment line(s) stay in main; %d deferred in %d frame(s) after the start; '
          'InitCustomTriggers: %d trigger(s) in %d slice(s)' % (info['mantidas'], info['deferred_ones'], info['frames'],
                                                               info['trigger_list'], info['slices']))
