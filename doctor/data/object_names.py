# Reads the names of the objects of a map (units, items, abilities) for the trigger names.
import re

from doctor.data import objbin
from doctor.data import slk
from doctor.data import slk_patch


FILES = (('w3u', 'unam', False), ('w3t', 'unam', False), ('w3a', 'anam', True), ('w3q', 'gnam', True),
         ('w3h', 'fnam', False), ('w3b', 'bnam', False), ('w3d', 'dnam', True))
RX_GAME_STRINGS = re.compile(r'_locales\\enus\.w3mod:units\\\w+strings\.txt$')
RX_COLOR = re.compile(r'\|c[0-9a-fA-F]{8}|\|r|\|n', re.I)
_GAME = None
_RX_STRING_B = re.compile(rb'^(?:\xef\xbb\xbf)?(?i:STRING)[ \t]+(\d+)')
_RX_STRING_S = re.compile(r'^(?:﻿)?(?i:STRING)[ \t]+(\d+)')
_RX_SKIP_B = re.compile(rb'^[ \t]*(?://[^\r\n]*)?\r?$')
_RX_SKIP_S = re.compile(r'^[ \t]*(?://[^\r\n]*)?\r?$')
_RX_OPEN_B = re.compile(rb'^[ \t]*\{')
_RX_OPEN_S = re.compile(r'^[ \t]*\{')
_RX_CLOSE_B = re.compile(rb'^\}[ \t]*\r?$')
_RX_CLOSE_S = re.compile(r'^\}[ \t]*\r?$')


class WtsEntry(object):
    __slots__ = ('_d', '_s', '_e', '_n', '_s2', '_e2')

    def __init__(self, data, start, end, number_span, body_span):
        self._d, self._s, self._e, self._n, (self._s2, self._e2) = data, start, end, number_span, body_span

    def group(self, n=0):
        if n == 1:
            return self._d[self._n[0]:self._n[1]]
        if n == 2:
            return self._d[self._s2:self._e2]
        return self._d[self._s:self._e]

    def start(self, n=0):
        return self._n[0] if n == 1 else self._s2 if n == 2 else self._s

    def end(self, n=0):
        return self._n[1] if n == 1 else self._e2 if n == 2 else self._e


def wts_entries(data):
    bts = isinstance(data, (bytes, bytearray))
    rx_string, rx_skip, rx_open, rx_close = (_RX_STRING_B, _RX_SKIP_B, _RX_OPEN_B, _RX_CLOSE_B) if bts else \
        (_RX_STRING_S, _RX_SKIP_S, _RX_OPEN_S, _RX_CLOSE_S)
    nl = b'\n' if bts else '\n'
    cr = b'\r' if bts else '\r'
    lines = data.split(nl)
    offs, off = [], 0
    for ln in lines:
        offs.append(off)
        off += len(ln) + 1
    out = []
    i, n = 0, len(lines)
    while i < n:
        m = rx_string.match(lines[i])
        if not m:
            i += 1
            continue
        start, number = offs[i], (offs[i] + m.start(1), offs[i] + m.end(1))
        j = i + 1
        while j < n and rx_skip.match(lines[j]):
            j += 1
        if j >= n or not rx_open.match(lines[j]):
            i += 1
            continue
        body_start = offs[j] + len(lines[j]) + 1
        k = j + 1
        while k < n and not rx_close.match(lines[k]):
            k += 1
        if k >= n:
            break
        body_end = max(body_start, offs[k] - 1)
        if body_end > body_start and data[body_end - 1:body_end] == cr:
            body_end -= 1
        out.append(WtsEntry(data, start, offs[k] + len(lines[k]), number, (body_start, body_end)))
        i = k + 1
    return out


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
                            name = _name_field(fields)
                            if name and len(section) == 4:
                                _GAME.setdefault(section, first_value(name))
            finally:
                casc.on_close()
        except Exception:
            _GAME = {}
    return _GAME


def _name_field(fields):
    for key in ('Name', 'name', 'Bufftip', 'EditorName'):
        if fields.get(key):
            return fields[key]
    return None


def strings(wts):
    return dict((int(m.group(1)), m.group(2).decode('utf-8', 'replace')) for m in wts_entries(wts or b''))


def clean(name):
    return ' '.join(RX_COLOR.sub('', name).split())


def first_value(value):
    m = re.match(r'\s*"([^"]*)"', value or '')
    return m.group(1) if m else (value or '').split(',')[0].strip('"')


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
            name = _name_field(fields)
            if name and len(section) == 4:
                value = first_value(name)
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
