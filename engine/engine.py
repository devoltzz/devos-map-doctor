# Rewrites the calls that behave differently on the Warcraft III 3.0 engine.
import re

import ui_local
import swap_calls


DAMAGE_SWAPS = {'UnitDamageTarget': 'KK_dano_alvo', 'UnitDamageTargetBJ': 'KK_dano_alvo_bj',
                'EXGetEventDamageData': 'KK_dano_dado'}
DAMAGE_KEYS = {
    'UnitDamageTarget': 'damage_target',
    'UnitDamageTargetBJ': 'target_damage_bj',
    'EXGetEventDamageData': 'damage_dealt',
}

RX_DESTROYS = re.compile(r'\bcall DestroyTimer\(')
RX_TYPE_CHECK = re.compile(r'(?<![\w.])IsUnitType\s*\(')


def dead_swap(body_text):
    replacements = []
    for m in RX_TYPE_CHECK.finditer(body_text):
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
    for begin, end_pos, new in sorted(replacements, reverse=True):
        body_text = body_text[:begin] + new + body_text[end_pos:]
    return body_text, len(replacements)


def applies(body_text, expected_count=None, to_report=False):
    failures = []
    info = {'failures': failures}
    line_list = body_text.count('\n')
    n_dt = len(RX_DESTROYS.findall(body_text))
    body_text = RX_DESTROYS.sub('call KK_tmr_destroi(', body_text)
    body_text, n_dead = dead_swap(body_text)
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
