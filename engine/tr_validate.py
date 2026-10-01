# Checks that a translation keeps the color codes, line breaks, format codes and numbers.
import os
import re


HERE = os.path.dirname(os.path.abspath(__file__))
TR = os.environ.get('TR_DIR') or os.path.join(HERE, 'tr')
CJK = re.compile(
    '['
    + chr(0xAC00)
    + '-'
    + chr(0xD7A3)
    + chr(0x1100)
    + '-'
    + chr(0x11FF)
    + chr(0x3130)
    + '-'
    + chr(0x318F)
    + chr(0x4E00)
    + '-'
    + chr(0x9FFF)
    + chr(0x3400)
    + '-'
    + chr(0x4DBF)
    + chr(0x3040)
    + '-'
    + chr(0x30FF)
    + ']'
)
AI_WORDS = re.compile(
    r'\bAI\b|\b(?i:artificial intelligence|language model|LLM|GPT|Claude|machine[- ]translat|translated by|translator|translation note|TN:)\b'
)


def codes(s):
    return re.findall(r'\|c[0-9A-Fa-f]{8}|\|r|\|n', s, re.I)


def check(entry, en):
    ko = entry['text']
    errs = []
    if not isinstance(en, str):
        return ['nao e string']
    if en.strip() == '' and ko.strip() != '':
        errs.append('empty')
    if CJK.search(en):
        errs.append('CJK restante')
    fala_de_ia = any(t in ko for t in ('人工智能', '인공지능', '人工知能')) or re.search(r'\bAI\b', ko)
    if AI_WORDS.search(en) and 'AI Protocol' not in en and not fala_de_ia:
        errs.append('mencao a IA/traducao')
    if ('\n' in en or '\r' in en) and '\n' not in ko:
        errs.append('raw line break')
    ck, ce = codes(ko), codes(en)
    if [c.lower() for c in ck] != [c.lower() for c in ce]:
        cko = [c.lower() for c in ck if c.lower() != '|n']
        ceo = [c.lower() for c in ce if c.lower() != '|n']
        if cko != ceo:
            errs.append('different color codes (%s -> %s)' % (' '.join(ck)[:60], ' '.join(ce)[:60]))
    if entry['kind'] in ('name', 'tip') and entry['src'].endswith('.txt'):
        if '"' in en and '"' not in ko:
            errs.append('double quotes in a txt value')
        if entry.get('comma') is False and ',' in en and not entry.get('quoted'):
            pass
    if entry['kind'] in ('script', 'command'):
        if en.count(chr(92) + '"') != ko.count(chr(92) + '"'):
            errs.append('different quote escaping')
        bare = re.sub(r'\\.', '', en)
        if '"' in bare:
            errs.append('unescaped quotes in a JASS literal')
        if chr(92) in re.sub(r'\\[\\"nrt]', '', en):
            errs.append('barra invertida solta')
    if entry['kind'] == 'command':
        if not re.match(r'^-[a-z0-9_-]+ ?$', en):
            errs.append('the command is not in lowercase ASCII (%r)' % en)
        if ko.endswith(' ') != en.endswith(' '):
            errs.append('different trailing space in the command')
    if len(en) > max(60, 3 * len(ko) + 40):
        errs.append('muito longo (%d chars vs %d)' % (len(en), len(ko)))
    return errs
