# Finds the script texts that are compared, so they get one translation everywhere.
import collections
import re

from doctor.translation import kr_inventory as ki
from doctor.translation import tr_apply as ta
from doctor.translation import tr_extract as tx


RX_EXTERNO = re.compile(r'GetPlayerName\s*\(|GetEventPlayerChatString\s*\(|GetEventPlayerChatStringMatched\s*\(|'
                        r'DzGetTriggerSyncData\s*\(|GetLocalizedString\s*\(')
RX_WINDOW = re.compile(r'SubString(?:BJ)?\s*\(\s*Get(?:Unit|Item|Object|Hero|Ability|Destructable)?Name\s*\(')


def other_lado(line_str, pos, lit):
    end_pos = pos + 1 + len(lit) + 1
    after_diag = line_str[end_pos:].lstrip()
    before = line_str[:pos].rstrip()
    if after_diag.startswith(('==', '!=')):
        m = re.match(r'(?:==|!=)\s*(.{0,160})', after_diag)
        return m.group(1) if m else ''
    if before.endswith(('==', '!=')):
        left = before[:-2][-400:]
        m = re.search(r'(?:\belseif\b|\bif\b|\band\b|\bor\b|\bnot\b|\breturn\b|=|\()\s*([^()]*(?:\([^()]*\))*[^()]*)$',
                      left)
        return (m.group(1) if m else left[-160:])
    return ''


RX_ASSIGN = re.compile(r'^\s*(?:set\s+(\w+)\s*(?:\[[^\]]*\])?\s*=|local\s+string\s+(\w+)\s*=)\s*(.+?)\s*$')


def _scopes(line_list):
    of_line, local_vars, current = [], collections.defaultdict(set), None
    for line in line_list:
        m = tx.RX_FUNCTION.match(line)
        if m:
            current = m.group(1)
            header = re.match(r'.*?takes\s+(.*?)\s+returns', line)
            if header and header.group(1).strip() != 'nothing':
                local_vars[current].update(p.split()[-1] for p in header.group(1).split(',') if p.split())
        elif current is not None:
            lo = re.match(r'\s*local\s+\w+\s+(?:array\s+)?(\w+)', line)
            if lo:
                local_vars[current].add(lo.group(1))
        of_line.append(current)
        if current is not None and tx.RX_END_FUNCTION.match(line):
            current = None
    return of_line, local_vars


def _var_key(fname, fn, local_vars):
    return (fn, fname) if fn is not None and fname in local_vars.get(fn, ()) else fname


def external_variables(line_list, scopes=None):
    of_line, local_vars = scopes or _scopes(line_list)
    vals = collections.defaultdict(list)
    for i, line in enumerate(line_list):
        m = RX_ASSIGN.match(line)
        if m:
            vals[_var_key(m.group(1) or m.group(2), of_line[i], local_vars)].append(m.group(3))
    return {n for n, rs in vals.items()
            if any(RX_EXTERNO.search(r) for r in rs) and all(RX_EXTERNO.search(r) or r in ('""', 'null') for r in rs)}


def measure(jtexto, entries, tr):
    comparados = {e['text'] for e in entries if e['kind'] == 'command' and not e['text'].startswith('-')
                  and 'chat' not in (e.get('uses') or [])}
    data_bytes = collections.defaultdict(list)
    for e in entries:
        if not e['src'].endswith('.j') and e['id'] in tr:
            data_bytes[e['text']].append(e['src'].split('/')[-1] + '[' + (e.get('key') or '') + ']')
    by = {lit: {'externo': 0, 'inner': 0, 'window': 0, 'clusters': collections.Counter(), 'exemplo': ''}
          for lit in comparados}
    line_list, _sep = tx.line_break(jtexto, jass=True)
    scopes = _scopes(line_list)
    external_vars = external_variables(line_list, scopes)
    for ln, line in enumerate(line_list):
        for pos, lit in ki.literals(line):
            if lit not in by:
                continue
            cat = ta.classifica_occurrence(line, pos, lit, False)
            g = cat.split(':', 1)[0]
            by[lit]['clusters'][g] += 1
            if g == 'caution':
                lado = other_lado(line, pos, lit)
                var = re.match(r'[\s(]*(\w+)\s*(?:\[[^\]]*\])?\s*\)*\s*$', lado or '')
                if lado and (RX_EXTERNO.search(lado) or
                             (var and _var_key(var.group(1), scopes[0][ln], scopes[1]) in external_vars)):
                    by[lit]['externo'] += 1
                elif lado and RX_WINDOW.search(lado):
                    by[lit]['window'] += 1
                    if not by[lit]['exemplo']:
                        by[lit]['exemplo'] = line.strip()[:200]
                elif lado:
                    by[lit]['inner'] += 1
                    if not by[lit]['exemplo']:
                        by[lit]['exemplo'] = line.strip()[:200]
    for lit, d in by.items():
        d['datum'] = data_bytes.get(lit, [])
        d['screen'] = d['clusters'].get('screen', 0)
        if d['window'] and not d['inner']:
            d['rec'] = 'window'
        elif d['inner'] and (d['screen'] or d['datum']):
            d['rec'] = 'all_entries'
        else:
            d['rec'] = 'keep'
    return by
