# Lists what a map calls that Warcraft III 3.0 does not have.
import re



FAMILIES = [
    ('DzAPI_Map / platform store (not portable: a stub)', r'^DzAPI_Map_\w+$'),
    ('DzAPI frames/UI (Dz*)', r'^Dz[A-Z]\w*$'),
    ('JAPI/M16 (EX*)', r'^EX[A-Z]\w*$'),
    ('JN (plataforma JN)', r'^JN[A-Z]\w*$'),
    ('YDWE/JAPI RequestExtra*Data', r'^RequestExtra\w+Data$'),
    ('YDWE (framework chines)', r'^(?:YD|yd)\w*$'),
    ('BzAPI (framework chines Bz)', r'^Bz[A-Z]\w*$'),
    ('Blizzard Reforged (Blz*)', r'^Blz[A-Z]\w*$'),
    ('JASS of the archive / of the port', r'^(?:CWGP|SCARED|RT)_\w+$'),
]


def read_data(file_path):
    with open(file_path, 'rb') as f:
        return f.read().decode('latin-1')


def declare_natives(txt):
    out = {}
    for m in re.finditer(r'^[ \t]*(?:constant\s+)?native\s+([A-Za-z_]\w*)\s+takes\s+(.*?)\s+returns\s+(.*?)\s*$',
                         txt, re.M):
        out[m.group(1)] = (m.group(2).strip(), m.group(3).strip(),
                           txt.count('\n', 0, m.start(1)) + 1)
    return out


def declara_functions(txt):
    out = {}
    for m in re.finditer(r'^[ \t]*(?:constant\s+)?function\s+([A-Za-z_]\w*)\s+takes\s+(.*?)\s+returns\s+(.*?)\s*$',
                         txt, re.M):
        out[m.group(1)] = (m.group(2).strip(), m.group(3).strip())
    return out


KEYWORDS = frozenset('''if elseif return exitwhen not and or loop call set local debug function takes returns then
else endif endloop endfunction globals endglobals constant native type extends array true false null nothing'''.split())


def family(fname):
    for rot, rx in FAMILIES:
        if re.match(rx, fname):
            return rot
    return 'other_entries'

