# Reads and removes the native declarations of a platform map script.
import re


RX_NATIVE = re.compile(r'^\s*native\s+([A-Za-z_]\w*)\s+takes\s')
RX_FUNCTION_DEF = re.compile(r'(?m)^function\s+([A-Za-z_]\w*)\s+takes\s')
RX_NATIVE_TEXT = re.compile(r'(?m)^\s*native\s+([A-Za-z_]\w*)\s+takes\s')
ENGINE_COMMENT = '// natives of the ENGINE declared by the map (see parte_0_mapa_natives.j)'


def defined_in_layer(blizzard_text):
    return set(RX_FUNCTION_DEF.findall(blizzard_text))


def drop_emulated(body_text, defined_ones):
    line_list = body_text.split('\n')
    declaradas = {}
    for i, line in enumerate(line_list):
        m = RX_NATIVE.match(line)
        if m:
            declaradas.setdefault(m.group(1), []).append(i)
    tgt = set(defined_ones) & set(declaradas)
    info = {'line_list': len(line_list), 'defined_ones': len(defined_ones), 'declaradas': declaradas, 'tgt': tgt,
            'uncovered': set(declaradas) - set(defined_ones), 'taken_out': 0, 'failures': []}

    outside = []
    taken_out = 0
    for line in line_list:
        m = RX_NATIVE.match(line)
        if m and m.group(1) in tgt:
            taken_out += 1
            continue
        outside.append(line)
    info['taken_out'] = taken_out

    if len(line_list) - len(outside) != len(tgt):
        info['failures'].append('removed %d lines for %d names' % (len(line_list) - len(outside), len(tgt)))
        return body_text, info
    if taken_out != len(tgt):
        info['failures'].append('%d lines removed for %d names (name declared twice?)' % (taken_out, len(tgt)))
        return body_text, info
    sobrou = set()
    for line in outside:
        m = RX_NATIVE.match(line)
        if m:
            sobrou.add(m.group(1))
    if sobrou & tgt:
        info['failures'].append('leftover declarations of target names: %s' % sorted(sobrou & tgt)[:10])
        return body_text, info
    if len(line_list) - len(outside) != taken_out:
        info['failures'].append('the line difference is not only from the `native`s')
        return body_text, info
    return '\n'.join(outside), info


def report_strip(info, origin):
    print('origin            : %s (%d lines)' % (origin, info['line_list']))
    print('blizzard.j        : %d functions defined' % info['defined_ones'])
    print('war3map.j         : %d natives declared' % len(info['declaradas']))
    print('to remove         : %d (defined in blizzard.j AND declared in the map)' % len(info['tgt']))
    if info['uncovered']:
        print('NOT covered by blizzard.j: %d -> %s'
              % (len(info['uncovered']), ', '.join(sorted(info['uncovered'])[:10])))


def inject_engine(body_text, natives_text):
    info = {'injetadas': [], 'failures': []}
    native_lines = [line for line in natives_text.split('\n') if re.match(r'^\s*native\s+', line)]
    if not native_lines:
        return body_text, info
    for line in native_lines:
        if not RX_NATIVE.match(line):
            info['failures'].append('`native` line without a complete signature: %s' % line.strip()[:120])
    if info['failures']:
        return body_text, info
    body = body_text.split('\n')
    ig = [i for i, line in enumerate(body) if line.strip() == 'globals']
    if not ig:
        info['failures'].append('could not find the first `globals` in war3map.j to put the natives before')
        return body_text, info
    i = ig[0]
    existing = set(RX_NATIVE_TEXT.findall(body_text))
    added = [line for line in native_lines if RX_NATIVE.match(line).group(1) not in existing]
    if added:
        body = body[:i] + [ENGINE_COMMENT] + added + [''] + body[i:]
        body_text = '\n'.join(body)
        info['injetadas'] = [RX_NATIVE.match(line).group(1) for line in added]
    return body_text, info


def report_engine(info):
    if info['injetadas']:
        print('engine natives injected at the top of war3map.j: %d -> %s'
              % (len(info['injetadas']), ', '.join(info['injetadas'])))

