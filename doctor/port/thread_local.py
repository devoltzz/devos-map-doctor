# Finds the threads and the handle-creating calls reached from code that runs on one machine only (they desync).
import re


RX_FUNCTION = re.compile(r'(?m)^[ \t]*function[ \t]+(\w+)[ \t]+takes\b')
RX_CALL = re.compile(r'\b(\w+)[ \t]*\(')
RX_EXEC = re.compile(r'\bExecuteFunc[ \t]*\([ \t]*"(\w+)"')
THREAD = re.compile(r'\b(TriggerEvaluate|TriggerExecute|TriggerExecuteWait|ConditionalTriggerExecute|ExecuteFunc|'
                    r'ForForce|ForGroup|ForGroupBJ|EnumItemsInRect|EnumItemsInRectBJ|EnumDestructablesInRect|'
                    r'EnumDestructablesInRectAll|EnumDestructablesInCircleBJ)[ \t]*\(')
CREATES = re.compile(
    r'\b(CreateTrigger|CreateTimer|CreateGroup|CreateForce|Location|Rect|RectFromLoc|CreateRegion|'
    r'InitHashtable|AddSpecialEffect|AddSpecialEffectLoc|AddSpecialEffectTarget|CreateTextTag|CreateUnit|'
    r'CreateUnitByName|CreateUnitAtLoc|CreateItem|CreateDestructable|BlzCreateFrame|BlzCreateSimpleFrame|'
    r'BlzCreateFrameByType|Condition|Filter|TriggerAddAction|TriggerAddCondition|CreateSound|'
    r'CreateLeaderboard|CreateMultiboard|DialogCreate|DialogAddButton|CreateImage|AddLightning|'
    r'AddLightningEx|CreateFogModifierRect|CreateFogModifierRadius|CreateQuest|CreateTimerDialog|'
    r'GetUnitLoc|GetSpellTargetLoc|GetRectCenter|CreateMinimapIcon|CreateMinimapIconOnUnit|'
    r'TriggerRegister\w+|BlzTriggerRegister\w+|CreateCameraSetup|CreateUnitPool|CreateItemPool|'
    r'AddWeatherEffect|BlzCreateUnitWithSkin|BlzCreateItemWithSkin|CreateTrackable|CreateUbersplat)'
    r'[ \t]*\('
)
RX_LOCAL_BODY = re.compile(r'\b(?:call|return)[ \t]+(\w+)[ \t]*\(')
RX_COMMENT = re.compile(r'//[^\r\n]*')


def functions(body_text):
    pos = [(m.start(), m.group(1)) for m in RX_FUNCTION.finditer(body_text)]
    out = {}
    for k, (a, fname) in enumerate(pos):
        b = pos[k + 1][0] if k + 1 < len(pos) else len(body_text)
        out[fname] = RX_COMMENT.sub('', body_text[a:b])
    return out


RX_LINE = re.compile(r'[^\r\n]*(?:\r\n|\r|\n)|[^\r\n]+$')
RX_LOCAL = re.compile(r'\bGetLocalPlayer[ \t]*\([ \t]*\)')
RX_LOCAL_NE = re.compile(r'\bGetLocalPlayer[ \t]*\([ \t]*\)[ \t]*!=|!=[ \t]*GetLocalPlayer[ \t]*\([ \t]*\)')


def local_regions(body):
    nameless = RX_COMMENT.sub(lambda m: ' ' * len(m.group()), body)
    out, stack = [], []
    for m in RX_LINE.finditer(nameless):
        txt_ln = m.group().strip()
        if re.match(r'if\b', txt_ln):
            if stack:
                stack[-1]['plain_globals'] = False
            stack.append(
                {
                    'loc': bool(RX_LOCAL.search(txt_ln)),
                    'ne': bool(RX_LOCAL_NE.search(txt_ln)),
                    'begin': m.end(),
                    'plain_globals': True,
                    'ret': False,
                }
            )
        elif not stack:
            continue
        elif re.match(r'(elseif|else)\b', txt_ln):
            stack[-1]['plain_globals'] = False
        elif re.match(r'endif\b', txt_ln):
            b = stack.pop()
            if b['loc']:
                out.append((b['begin'], m.start()))
                if b['ne'] and b['plain_globals'] and b['ret']:
                    out.append((m.end(), len(body)))
        elif re.match(r'return\b', txt_ln):
            stack[-1]['ret'] = True
        elif txt_ln and not re.match(r'set[ \t]+\w+[ \t]*=[ \t]*null\b', txt_ln):
            stack[-1]['plain_globals'] = False
    out.sort()
    joined_ones = []
    for a, b in out:
        if joined_ones and a <= joined_ones[-1][1]:
            joined_ones[-1] = (joined_ones[-1][0], max(b, joined_ones[-1][1]))
        else:
            joined_ones.append((a, b))
    return joined_ones


def _roots_of(fs, branches):
    roots = []
    for fname, c in fs.items():
        if fname.startswith('KK_loc_'):
            m = RX_LOCAL_BODY.search(c)
            if m and m.group(1) in fs:
                roots.append((m.group(1), fname))
        elif branches and RX_LOCAL.search(c):
            for a, b in local_regions(c):
                for g in set(RX_CALL.findall(c[a:b])) | set(RX_EXEC.findall(c[a:b])):
                    if g in fs and g != fname:
                        roots.append((g, 'local branch of ' + fname))
    return roots


def audit(body_text, creation=False, branches=False):
    fs = functions(body_text)
    roots = _roots_of(fs, branches)
    file_path = {}
    work_queue = [(r, [loc]) for r, loc in roots]
    while work_queue:
        f, cpath = work_queue.pop(0)
        if f in file_path or f not in fs:
            continue
        file_path[f] = cpath
        c = fs[f]
        next_item = set(m.group(1) for m in RX_CALL.finditer(c))
        next_item |= set(RX_EXEC.findall(c))
        for g in next_item:
            if g in fs and g not in file_path:
                work_queue.append((g, cpath + [f]))
    matches = []
    for f in sorted(file_path):
        ths = sorted(set(m.group(1) for m in THREAD.finditer(fs[f])))
        if creation:
            ths += sorted(set('+' + m.group(1) for m in CREATES.finditer(fs[f])))
        if ths:
            matches.append((f, ths, ' <- '.join([f] + list(reversed(file_path[f])))))
    if branches:
        for f in sorted(fs):
            if f in file_path or not RX_LOCAL.search(fs[f]):
                continue
            segments = ''.join(fs[f][a:b] for a, b in local_regions(fs[f]))
            ths = sorted(set(m.group(1) for m in THREAD.finditer(segments)))
            if creation:
                ths += sorted(set('+' + m.group(1) for m in CREATES.finditer(segments)))
            if ths:
                matches.append((f, ths, f + ' (local branch)'))
    return matches


def local_closure(body_text, branches=False):
    fs = functions(body_text)
    seen = set()
    work_queue = [g for g, _q in _roots_of(fs, branches)]
    while work_queue:
        f = work_queue.pop()
        if f in seen or f not in fs:
            continue
        seen.add(f)
        work_queue.extend(g for g in set(RX_CALL.findall(fs[f])) | set(RX_EXEC.findall(fs[f])) if g not in seen)
    return seen


RX_SLOT = re.compile(
    r'set[ \t]+st___prototype(\d+)\[(\d+)\][ \t]*=[ \t]*CreateTrigger\(\)\s*'
    r'call[ \t]+TriggerAddAction\([ \t]*st___prototype\1\[\2\][ \t]*,[ \t]*function[ \t]+(\w+)[ \t]*\)'
)
RX_ST_LIT = re.compile(r'\b(TriggerEvaluate|TriggerExecute)[ \t]*\([ \t]*st___prototype(\d+)\[[ \t]*\(?[ \t]*(\d+)'
                       r'[ \t]*\)?[ \t]*\][ \t]*\)')
RX_SC_LIT = re.compile(r'\bsc___prototype(\d+)_(evaluate|execute)[ \t]*\([ \t]*(\d+)[ \t]*(,[ \t]*|(?=\)))')
RX_SC_ANY = re.compile(r'\bsc___prototype\d+_(?:evaluate|execute)[ \t]*\(')
RX_REF = re.compile(r'\bfunction[ \t]+(\w+)')
RX_EXEC_LIT = re.compile(r'\bExecuteFunc[ \t]*\([ \t]*"(\w+)"[ \t]*\)')
COPY = 'KKH_'
WAITS = re.compile(r'\b(TriggerSleepAction|PolledWait|TriggerWaitOnSleeps|GetTriggeringTrigger|GetTriggerEvalCount|'
                   r'GetTriggerExecCount)[ \t]*\(')


def _gaps_of(body_text):
    pos = [(m.start(), m.group(1)) for m in RX_FUNCTION.finditer(body_text)]
    out = {}
    for k, (a, fname) in enumerate(pos):
        end_pos = re.compile(r'(?m)^[ \t]*endfunction\b[^\r\n]*(?:\r\n|\r|\n|$)').search(body_text, a)
        out[fname] = (a, end_pos.end() if end_pos else (pos[k + 1][0] if k + 1 < len(pos) else len(body_text)))
    return out


def fixable(body_text, turns_done=8):
    info = {'replacements': 0, 'copies': [], 'failures': []}
    nl = '\r\n' if '\r\n' in body_text[:65536] else '\n'
    rx_kkh = re.compile(r'\b%s\w+' % COPY)
    for _goes_back in range(turns_done):
        slots = dict(((n, k), sa) for n, k, sa in RX_SLOT.findall(body_text))
        gaps_found = _gaps_of(body_text)
        closure = local_closure(body_text, branches=True)
        new_ones = []

        def rewrite(body, where):
            def st(m):
                sa = slots.get((m.group(2), m.group(3)))
                if not sa:
                    info['failures'].append(
                        '%s: st___prototype%s[%s] without a trigger' % (where, m.group(2), m.group(3))
                    )
                    return m.group(0)
                new_ones.append((COPY + sa, sa))
                return COPY + sa + '()'

            def sc(m):
                n, method, k = m.group(1), m.group(2), m.group(3)
                sa = slots.get((n, k))
                if not sa:
                    info['failures'].append('%s: sc___prototype%s_%s(%s) without a trigger' % (where, n, method, k))
                    return m.group(0)
                fname = '%ssc%s_%s_%s' % (COPY, n, method, k)
                new_ones.append((fname, ('sc', 'sc___prototype%s_%s' % (n, method), sa)))
                return fname + '('
            def ef(m):
                if m.group(1) not in gaps_found:
                    info.setdefault('without_function', []).append('%s: ExecuteFunc("%s")' % (where, m.group(1)))
                    return 'DoNothing()'
                new_ones.append((COPY + m.group(1), m.group(1)))
                return COPY + m.group(1) + '()'
            new = RX_SC_LIT.sub(sc, RX_ST_LIT.sub(st, body))
            new = RX_EXEC_LIT.sub(ef, new)
            for m in RX_SC_ANY.finditer(new):
                info['failures'].append('%s: non-literal index in %s' % (where, new[m.start():m.start() + 60].strip()))
            return new
        replacements = {}
        for f in sorted(closure, key=lambda x: gaps_found[x][0]):
            if f.startswith('sc___prototype') or f.startswith(COPY + 'sc'):
                continue
            a, b = gaps_found[f]
            new = rewrite(body_text[a:b], f)
            if new != body_text[a:b]:
                replacements[f] = new
        for f in sorted(gaps_found, key=lambda x: gaps_found[x][0]):
            if f in closure or f.startswith('sc___prototype') or f.startswith(COPY + 'sc'):
                continue
            a, b = gaps_found[f]
            body = body_text[a:b]
            if not RX_LOCAL.search(body):
                continue
            new, pos = '', 0
            for ra, rb in local_regions(body):
                new += body[pos:ra] + rewrite(body[ra:rb], f)
                pos = rb
            new += body[pos:]
            if new != body:
                replacements[f] = new
        if info['failures']:
            return body_text, info
        if not replacements:
            break
        point = min(gaps_found[f][0] for f in replacements)
        copies = {}
        moved_ones = set()
        work_queue = list(new_ones)
        while work_queue:
            fname, orig = work_queue.pop()
            if fname in copies:
                continue
            if fname in gaps_found:
                if gaps_found[fname][0] < point:
                    continue
                body = replacements.pop(fname, None) or body_text[gaps_found[fname][0]:gaps_found[fname][1]]
                moved_ones.add(fname)
            elif isinstance(orig, tuple):
                _t, sc_name, sa = orig
                a, b = gaps_found[sc_name]
                body = body_text[a:b]
                header = re.match(r'([ \t]*function[ \t]+)\w+([ \t]+takes[ \t]+)integer[ \t]+i\b[ \t]*(,[ \t]*)?', body)
                if not header:
                    info['failures'].append('%s: unexpected header' % sc_name)
                    continue
                body = (
                    header.group(1)
                    + fname
                    + header.group(2)
                    + ('' if header.group(3) else 'nothing ')
                    + body[header.end() :]
                )
                body = re.sub(r'\b(?:TriggerEvaluate|TriggerExecute)[ \t]*\([ \t]*st___prototype\d+\[[ \t]*i[ \t]*\]'
                              r'[ \t]*\)', COPY + sa + '()', body)
                work_queue.append((COPY + sa, sa))
            else:
                a, b = gaps_found[orig]
                body = body_text[a:b]
                if WAITS.search(body):
                    info['failures'].append('%s: waits or reads its own trigger (%s)'
                                            % (orig, WAITS.search(body).group(1)))
                    continue
                header = body.index('\n')
                body = re.sub(r'(function[ \t]+)%s\b' % re.escape(orig), r'\g<1>' + fname, body[:header], count=1) + \
                    body[header:]
                core_part = body[body.index('\n'):]
                for g in sorted(set(RX_CALL.findall(core_part)) | set(RX_REF.findall(core_part))):
                    if g == orig:
                        body = body[:header] + re.sub(r'\b%s\b' % re.escape(g), fname, body[header:])
                    elif g in gaps_found and gaps_found[g][0] >= point and not g.startswith(COPY):
                        body = body[:header] + re.sub(r'\b%s\b' % re.escape(g), COPY + g, body[header:])
                        work_queue.append((COPY + g, g))
                before = len(new_ones)
                body = rewrite(body, fname)
                work_queue.extend(new_ones[before:])
            copies[fname] = body
            for d in set(rx_kkh.findall(body)):
                if d != fname and d in gaps_found and gaps_found[d][0] >= point and d not in copies:
                    work_queue.append((d, d))
        if info['failures']:
            return body_text, info
        order, done_names = [], set()
        deps = dict((n, set(d for d in rx_kkh.findall(c) if d != n and (d in copies))) for n, c in copies.items())
        pending_ones = set(copies)
        while pending_ones:
            ready_ones = sorted(n for n in pending_ones if deps[n] <= done_names)
            if not ready_ones:
                info['failures'].append('cycle between copies: %s' % ', '.join(sorted(pending_ones)[:6]))
                return body_text, info
            order.extend(ready_ones)
            done_names.update(ready_ones)
            pending_ones.difference_update(ready_ones)
        edits_made = [(gaps_found[f][0], gaps_found[f][1], c) for f, c in replacements.items()]
        edits_made += [(gaps_found[n][0], gaps_found[n][1], '') for n in moved_ones]
        for a, b, c in sorted(edits_made, reverse=True):
            body_text = body_text[:a] + c + body_text[b:]
        info['replacements'] += len(replacements)
        block_entry = (
            '// [KK framework] thread_local.fix: copies for the local code (no trigger; the original stays for the '
            'synchronized code)' + nl + ''.join(copies[n].rstrip('\r\n') + nl for n in order)
        )
        body_text = body_text[:point] + block_entry + body_text[point:]
        info['copies'] += [n for n in order if n not in moved_ones]
    return body_text, info


def report_data(matches, log=print):
    if not matches:
        log('thread in local code: none (the KK_loc_ bodies run no trigger and no thread)')
        return
    log('thread in LOCAL code (born on one machine only: it desyncs): %d function(s)' % len(matches))
    for f, ths, cpath in matches:
        log('   %-40s %s  [%s]' % (f, ', '.join(ths), cpath[:200]))
