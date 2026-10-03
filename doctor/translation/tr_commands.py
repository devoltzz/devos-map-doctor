# Finds the chat commands and the texts a translation by occurrence must leave alone.
import json
import os
import re


HERE = os.path.dirname(os.path.abspath(__file__))
TR_DIR = os.environ.get('TR_DIR') or os.path.join(HERE, 'tr')
os.environ['TR_DIR'] = TR_DIR

QUOTE_DEFAULT = r'(?:【|输入|键入|/)'
QUOTE_END_DEFAULT = r'(?=[】/\s，。,.|]|$)'


def config():
    p = os.path.join(TR_DIR, 'comandos.json')
    c = json.load(open(p, encoding='utf-8')) if os.path.isfile(p) else {}
    return (c.get('canonico_manual', {}), c.get('formas_extra', {}), c.get('quote', QUOTE_DEFAULT),
            c.get('quote_end', QUOTE_END_DEFAULT))


def canonico(en, zh):
    if not zh.startswith('-'):
        return en.strip() + (' ' if zh.endswith(' ') else '')
    s = en.strip()
    s = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', s)
    s = re.sub(r'(?<=[A-Za-z])(?=\d)', ' ', s)
    s = s.lower().replace("'", '')
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return '-' + s + (' ' if zh.endswith(' ') else '')


def e_command(e):
    return e['kind'] == 'command' and (e['text'].startswith('-') or 'chat' in (e.get('uses') or []))
