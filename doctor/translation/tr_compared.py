# Finds the script texts that are compared, so they get one translation everywhere.
import collections
import re

from doctor.translation import kr_inventory as ki
from doctor.translation import tr_apply as ta
from doctor.translation import tr_extract as tx


RX_EXTERNO = re.compile(r'GetPlayerName\s*\(|GetEventPlayerChatString\s*\(|GetEventPlayerChatStringMatched\s*\(|'
                        r'DzGetTriggerSyncData\s*\(|GetLocalizedString\s*\(')
RX_WINDOW = re.compile(r'SubString(?:BJ)?\s*\(\s*Get(?:Unit|Item|Object|Hero|Ability|Destructable)?Name\s*\(')


def other_lado(ln, pos, lit):
    end_pos = pos + 1 + len(lit) + 1
    after_diag = ln[end_pos:].lstrip()
    before = ln[:pos].rstrip()
    if after_diag.startswith(('==', '!=')):
        m = re.match(r'(?:==|!=)\s*(.{0,160})', after_diag)
        return m.group(1) if m else ''
    if before.endswith(('==', '!=')):
        left = before[:-2][-400:]
        m = re.search(r'(?:\bif\b|\band\b|\bor\b|\breturn\b|=|\()\s*([^()]*(?:\([^()]*\))*[^()]*)$', left)
        return (m.group(1) if m else left[-160:])
    return ''


def measure(jtexto, entries, tr):
    comparados = {e['text'] for e in entries if e['kind'] == 'command' and not e['text'].startswith('-')
                  and 'chat' not in (e.get('uses') or [])}
    data_bytes = collections.defaultdict(list)
    for e in entries:
        if not e['src'].endswith('.j') and e['id'] in tr:
            data_bytes[e['text']].append(e['src'].split('/')[-1] + '[' + (e.get('key') or '') + ']')
    por = {lit: {'externo': 0, 'inner': 0, 'window': 0, 'clusters': collections.Counter(), 'exemplo': ''}
           for lit in comparados}
    line_list, _sep = tx.quebra(jtexto, jass=True)
    for line in line_list:
        for pos, lit in ki.literals(line):
            if lit not in por:
                continue
            cat = ta.classifica_occurrence(line, pos, lit, False)
            g = cat.split(':', 1)[0]
            por[lit]['clusters'][g] += 1
            if g == 'caution':
                lado = other_lado(line, pos, lit)
                if lado and RX_EXTERNO.search(lado):
                    por[lit]['externo'] += 1
                elif lado and RX_WINDOW.search(lado):
                    por[lit]['window'] += 1
                    if not por[lit]['exemplo']:
                        por[lit]['exemplo'] = line.strip()[:200]
                elif lado:
                    por[lit]['inner'] += 1
                    if not por[lit]['exemplo']:
                        por[lit]['exemplo'] = line.strip()[:200]
    for lit, d in por.items():
        d['datum'] = data_bytes.get(lit, [])
        d['screen'] = d['clusters'].get('screen', 0)
        if d['window'] and not d['inner']:
            d['rec'] = 'window'
        elif d['inner'] and (d['screen'] or d['datum']):
            d['rec'] = 'all_entries'
        else:
            d['rec'] = 'keep'
    return por
