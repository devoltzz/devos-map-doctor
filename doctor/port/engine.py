# Rewrites the calls that behave differently on the Warcraft III 3.0 engine.
import re

from doctor.port import ui_local
from doctor.port import swap_calls


DAMAGE_SWAPS = {'UnitDamageTarget': 'KK_dano_alvo', 'UnitDamageTargetBJ': 'KK_dano_alvo_bj',
                'EXGetEventDamageData': 'KK_dano_dado'}
DAMAGE_KEYS = {
    'UnitDamageTarget': 'damage_target',
    'UnitDamageTargetBJ': 'target_damage_bj',
    'EXGetEventDamageData': 'damage_dealt',
}

RX_DESTROYS = re.compile(r'\bcall[ \t]+DestroyTimer[ \t]*\(')
RX_TYPE_CHECK = re.compile(r'(?<![\w.])IsUnitType\s*\(')
RX_TEXT = re.compile(r'//[^\n]*|"(?:[^"\\]|\\.)*"|\'(?:[^\'\\\n]|\\.){1,4}\'', re.S)


def _outside_text(body_text):
    import bisect
    begin, end_pos = [], []
    for m in RX_TEXT.finditer(body_text):
        if m.group(0)[0] != '/':
            begin.append(m.start())
            end_pos.append(m.end())

    def outside(p):
        k = bisect.bisect_right(begin, p) - 1
        return k < 0 or p >= end_pos[k]
    return outside


def swap_destroy(body_text):
    if 'DestroyTimer' not in body_text:
        return body_text, 0
    outside = _outside_text(body_text)
    n = [0]

    def sub(m):
        if not outside(m.start()):
            return m.group(0)
        n[0] += 1
        return 'call KK_tmr_destroi('
    return RX_DESTROYS.sub(sub, body_text), n[0]


def dead_swap(body_text):
    replacements = []
    outside = _outside_text(body_text) if 'UNIT_TYPE_DEAD' in body_text else None
    for m in RX_TYPE_CHECK.finditer(body_text):
        if outside is None or not outside(m.start()):
            continue
        opens = m.end() - 1
        end_pos = ui_local.on_close(body_text, opens)
        if end_pos < 0:
            continue
        core_part = body_text[opens + 1:end_pos]
        if '\n' in core_part:
            continue
        args = ui_local.arguments(core_part)
        if len(args) != 2 or core_part[args[1][0]:args[1][1]].strip() != 'UNIT_TYPE_DEAD':
            continue
        replacements.append((m.start(), end_pos + 1, 'KK_unid_morta(%s)' % core_part[args[0][0]:args[0][1]].strip()))
    return ui_local.apply_replacements(body_text, replacements), len(replacements)


RX_FILE_HASH = re.compile(r'^([ \t]*)if[ \t]+EXLoadFileHashKey\(\s*"((?:[^"\\]|\\.)*)"\s*\)\s*!=\s*"[0-9A-Fa-f]*"'
                          r'[ \t]+then[ \t]*$')


def strip_file_hash_checks(body_text):
    if 'EXLoadFileHashKey' not in body_text:
        return body_text, []
    line_list = body_text.split('\n')
    removed = []
    i = 0
    while i < len(line_list):
        m = RX_FILE_HASH.match(line_list[i].rstrip('\r'))
        if not m:
            i += 1
            continue
        level, j = 0, i + 1
        while j < len(line_list):
            s = line_list[j].strip()
            if re.match(r'if\b', s):
                level += 1
            elif re.match(r'endif\b', s):
                if level == 0:
                    break
                level -= 1
            elif level == 0 and re.match(r'else(if)?\b', s):
                j = -1
                break
            j += 1
        if j < 0 or j >= len(line_list):
            i += 1
            continue
        cr = '\r' if line_list[i].endswith('\r') else ''
        line_list[i] = '%s// [port] removed the anti-tamper check: %s%s' % (m.group(1), m.group(2), cr)
        for k in range(i + 1, j + 1):
            line_list[k] = '%s//%s%s' % (m.group(1), line_list[k].strip(), '\r' if line_list[k].endswith('\r') else '')
        removed.append(m.group(2))
        i = j + 1
    return '\n'.join(line_list), removed


def applies(body_text, expected_count=None, to_report=False):
    failures = []
    info = {'failures': failures}
    line_list = body_text.count('\n')
    body_text, n_dt = swap_destroy(body_text)
    body_text, n_dead = dead_swap(body_text)
    body_text, info['file_hash_checks'] = strip_file_hash_checks(body_text)
    info['destroy_timer'] = n_dt
    info['dead_unit'] = n_dead
    body_text, i_damage = swap_calls.applies(body_text, DAMAGE_SWAPS)
    failures.extend(i_damage['failures'])
    for native, hash_key in DAMAGE_KEYS.items():
        info[hash_key] = i_damage['by_native'][native]
    for k, v in (expected_count or {}).items():
        if v is not None and info.get(k) != v:
            failures.append('%s: measured %d, expected %d' % (k, info.get(k), v))
    if body_text.count('\n') != line_list:
        failures.append('the number of lines changed')
    if to_report and not failures:
        report_data(info)
    return body_text, info


def report_data(info):
    print('Reforged engine: %d `DestroyTimer` of the map -> KK_tmr_destroi (pause first); %d `IsUnitType(x, '
          'UNIT_TYPE_DEAD)` -> KK_unid_morta (removed counts as dead)' % (info['destroy_timer'], info['dead_unit']))
    print('  trigger damage (not physical): %d UnitDamageTarget -> KK_dano_alvo, %d UnitDamageTargetBJ -> '
          'KK_dano_alvo_bj, %d EXGetEventDamageData -> KK_dano_dado'
          % (info.get('damage_target', 0), info.get('target_damage_bj', 0), info.get('damage_dealt', 0)))
    if info.get('file_hash_checks'):
        print('  anti-tamper: %d file hash check(s) removed (%s): a port never matches the original hashes'
              % (len(info['file_hash_checks']), ', '.join(info['file_hash_checks'])))
