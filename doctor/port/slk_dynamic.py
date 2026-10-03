# Gives EXExecuteScript a field table for the map functions that pass the field name.
import re

from doctor.port import class1


TABLE_NAMES = ('unit', 'ability', 'item')
JASS_TAB = {'unit': 'DB_TAB_UNIT', 'ability': 'DB_TAB_ABILITY', 'item': 'DB_TAB_ITEM'}
RX_PREFIX_MATCH = re.compile(
    r'^"\(require\s*\(?\s*(?:\'|\\")jass\.slk(?:\'|\\")\s*\)?\s*\)\.(unit|ability|item)\[\s*"$'
)
RX_FUNC = re.compile(r'(?m)^[ \t]*(?:constant[ \t]+)?function[ \t]+(\w+)[ \t]+takes[ \t]+(.*?)[ \t]+returns')
RX_FIELD = re.compile(r'^\s*"([A-Za-z][A-Za-z0-9]*)"\s*$')


def split_comma(arg):
    out, max_depth, begin, i, n = [], 0, 0, 0, len(arg)
    while i < n:
        c = arg[i]
        if c == '"':
            i = class1.skip_string(arg, i)
            continue
        if c == "'":
            i = class1.skip_rawcode(arg, i)
            continue
        if c in '([':
            max_depth += 1
        elif c in ')]':
            max_depth -= 1
        elif c == ',' and max_depth == 0:
            out.append(arg[begin:i])
            begin = i + 1
        i += 1
    out.append(arg[begin:])
    return out


def embrulhos(body_text):
    defs = [(m.start(), m.group(1), [p.strip().split()[-1] for p in m.group(2).split(',')
                                     if p.strip() and p.strip() != 'nothing'])
            for m in RX_FUNC.finditer(body_text)]
    out = {}
    pos = 0
    for line in class1.masked_lines(body_text):
        begin = pos
        pos += len(line) + 1
        if 'EXExecuteScript(' not in line or 'jass.slk' not in line:
            continue
        for _a, _b, arg in class1.find_calls(line) or []:
            if 'jass.slk' not in arg or class1.site_parts(arg)[0] is not None:
                continue
            pieces = class1.split_more(arg)
            m = RX_PREFIX_MATCH.match(pieces[0].strip()) if pieces else None
            if not m or len(pieces) != 4:
                continue
            field_id = pieces[3].strip()
            owner = [d for d in defs if d[0] <= begin]
            if owner and field_id in owner[-1][2]:
                out[owner[-1][1]] = (m.group(1), owner[-1][2].index(field_id))
    return out


def dynamic_fields(body_text):
    out = dict((t, set()) for t in TABLE_NAMES)
    scrambled = embrulhos(body_text)
    for fname, (tab, k) in scrambled.items():
        for m in re.finditer(r'\b%s\s*\(' % re.escape(fname), body_text):
            start_line = body_text.rfind('\n', 0, m.start()) + 1
            if re.match(r'[ \t]*(?:constant[ \t]+)?function\b', body_text[start_line:m.start()]):
                continue
            end_pos = (
                class1.on_close(body_text, m.end() - 1)
                if hasattr(class1, 'on_close')
                else _closes(body_text, m.end() - 1)
            )
            if end_pos < 0:
                continue
            args = split_comma(body_text[m.end():end_pos])
            if len(args) > k:
                lit = RX_FIELD.match(args[k])
                if lit:
                    out[tab].add(lit.group(1).lower())
    return dict((t, v) for t, v in out.items() if v), sorted(scrambled)


def _closes(body_text, opens):
    max_depth, i, n = 0, opens, len(body_text)
    while i < n:
        c = body_text[i]
        if c == '"':
            i = class1.skip_string(body_text, i)
            continue
        if c == "'":
            i = class1.skip_rawcode(body_text, i)
            continue
        if c == '(':
            max_depth += 1
        elif c == ')':
            max_depth -= 1
            if max_depth == 0:
                return i
        elif c == '\n':
            return -1
        i += 1
    return -1


def functions_by_name(fields, field_const):
    L = [
        '',
        '// ==============================================================================================',
        "// EXExecuteScript IN THE GAME: reads `(require'jass.slk').<tabela>[<id>].<campo>` by the field NAME (the",
        '// map wrapper that passes the field in a parameter). Generated with the table (`common/kk/slk_dinamico.py`).',
        '// ==============================================================================================',
        'function DB_ex_acha takes string s,string sub,integer desde returns integer',
        '    local integer n=StringLength(s)',
        '    local integer k=StringLength(sub)',
        '    local integer i=desde',
        '    loop',
        '        exitwhen i+k>n',
        '        if SubString(s,i,i+k)==sub then',
        '            return i',
        '        endif',
        '        set i=i+1',
        '    endloop',
        '    return -1',
        'endfunction',
        '',
        'function DB_ex_rawcode takes string s returns integer',
        '    local string asc=" !\\"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\\\]^_`'
        'abcdefghijklmnopqrstuvwxyz{|}~"',
        '    local integer v=0',
        '    local integer i=0',
        '    local integer c',
        '    if StringLength(s)!=4 then',
        '        return 0',
        '    endif',
        '    loop',
        '        exitwhen i>=4',
        '        set c=DB_ex_acha(asc,SubString(s,i,i+1),0)',
        '        if c<0 then',
        '            return 0',
        '        endif',
        '        set v=v*256+c+32',
        '        set i=i+1',
        '    endloop',
        '    return v',
        'endfunction',
        '',
        'function DB_slk_campo takes integer tabela,string campo returns integer',
        '    local string c=StringCase(campo,true)',
    ]
    for t in TABLE_NAMES:
        if not fields.get(t):
            continue
        L.append('    if tabela==%s then' % JASS_TAB[t])
        for c in fields[t]:
            L.append('        if c=="%s" then' % c.upper())
            L.append('            return %s' % field_const(t, c))
            L.append('        endif')
        L.append('    endif')
    L += ['    return -1',
          'endfunction',
          '',
          'function EXExecuteScript takes string s returns string',
          '    local integer p=DB_ex_acha(s,"jass.slk",0)',
          '    local integer a',
          '    local integer b',
          '    local integer tabela',
          '    local integer id',
          '    local integer campo',
          '    local string nome',
          '    local string ids',
          '    if p<0 then',
          '        return ""',
          '    endif',
          '    set a=DB_ex_acha(s,").",p)',
          '    if a<0 then',
          '        return ""',
          '    endif',
          '    set b=DB_ex_acha(s,"[",a)',
          '    if b<0 then',
          '        return ""',
          '    endif',
          '    set nome=SubString(s,a+2,b)',
          '    if nome=="unit" then',
          '        set tabela=DB_TAB_UNIT',
          '    elseif nome=="ability" then',
          '        set tabela=DB_TAB_ABILITY',
          '    elseif nome=="item" then',
          '        set tabela=DB_TAB_ITEM',
          '    else',
          '        return ""',
          '    endif',
          '    set a=DB_ex_acha(s,"]",b)',
          '    if a<0 or SubString(s,a+1,a+2)!="." then',
          '        return ""',
          '    endif',
          '    set ids=SubString(s,b+1,a)',
          '    if StringLength(ids)==6 and SubString(ids,0,1)=="\'" then',
          '        set ids=SubString(ids,1,5)',
          '    endif',
          '    set id=S2I(ids)',
          '    if id==0 or I2S(id)!=ids then',
          '        set id=DB_ex_rawcode(ids)',
          '    endif',
          '    set campo=DB_slk_campo(tabela,SubString(s,a+2,StringLength(s)))',
          '    if campo<0 then',
          '        return ""',
          '    endif',
          '    return DB_slk_get(tabela,id,campo)',
          'endfunction',
          '']
    return L
