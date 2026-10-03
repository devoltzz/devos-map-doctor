# Reads the names of the objects of a map (units, items, abilities) for the trigger names.
import re

from doctor.data import objbin
from doctor.data import slk
from doctor.data import slk_patch


FILES = (('w3u', 'unam', False), ('w3t', 'unam', False), ('w3a', 'anam', True), ('w3q', 'gnam', True),
         ('w3h', 'fnam', False), ('w3b', 'bnam', False))
RX_GAME_STRINGS = re.compile(r'_locales\\enus\.w3mod:units\\\w+strings\.txt$')
RX_WTS = re.compile(rb'STRING\s+(\d+)\s*(?://[^\n]*\n\s*)?\{\r?\n(.*?)\r?\n\}', re.S)
RX_COLOR = re.compile(r'\|c[0-9a-fA-F]{8}|\|r|\|n', re.I)
_GAME = None


def game_names():
    global _GAME
    if _GAME is None:
        _GAME = {}
        try:
            from doctor.data import casc_wc3
            casc = casc_wc3.CascWC3()
            try:
                for key in sorted(casc.file_set):
                    if RX_GAME_STRINGS.search(key):
                        for section, fields in slk.parse_ini_bytes(casc.read_data(casc.file_set[key][0])).items():
                            name = fields.get('Name') or fields.get('name')
                            if name and len(section) == 4:
                                _GAME.setdefault(section, name.split(',')[0].strip('"'))
            finally:
                casc.on_close()
        except Exception:
            _GAME = {}
    return _GAME


def strings(wts):
    return dict((int(m.group(1)), m.group(2).decode('utf-8', 'replace')) for m in RX_WTS.finditer(wts or b''))


def clean(name):
    return ' '.join(RX_COLOR.sub('', name).split())


def profile_names(read, texts):
    out = {}
    for file_name in slk_patch.PROFILES:
        data = read(file_name)
        if not data:
            continue
        try:
            sections = slk.parse_ini_bytes(data)
        except Exception:
            continue
        for section, fields in sections.items():
            name = fields.get('Name') or fields.get('name')
            if name and len(section) == 4:
                value = name.split(',')[0].strip('"')
                m = re.match(r'TRIGSTR_(\d+)$', value)
                out.setdefault(section, texts.get(int(m.group(1)), value) if m else value)
    return out


def names(read, game=True):
    base = game_names() if game else {}
    texts = strings(read('war3map.wts'))
    own = dict((k, clean(v)) for k, v in profile_names(read, texts).items() if clean(v))
    out = dict(base)
    out.update(own)
    known = dict(base)
    known.update(own)
    for extension, field, levels in FILES:
        found, made_from = {}, {}
        for file_name in ('war3map.' + extension, 'war3mapSkin.' + extension):
            data = read(file_name)
            if not data:
                continue
            try:
                _version, tables, _end = objbin.read_data(data, levels)
            except Exception:
                continue
            for table in tables:
                for original, new, mods in table:
                    ident = new if new.strip('\x00') else original
                    made_from[ident] = original
                    for mod in mods:
                        if mod[0] == field and mod[4] and ident not in found:
                            value = mod[4].decode('utf-8', 'replace')
                            m = re.match(r'TRIGSTR_(\d+)$', value)
                            found[ident] = texts.get(int(m.group(1)), value) if m else value
        for ident, original in made_from.items():
            name = found.get(ident) or own.get(ident) or known.get(original)
            if name:
                out[ident] = clean(name)
    return out
