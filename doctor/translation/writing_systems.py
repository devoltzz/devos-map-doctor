# The writing system of a text (Cyrillic, Vietnamese, CJK...): the source text a translation left.
import re


RX_HAN = re.compile('[㐀-䶿一-鿿豈-﫿]')
RX_KANA = re.compile('[぀-ヿㇰ-ㇿ]')
RX_HANGUL = re.compile('[가-힯ᄀ-ᇿ㄰-㆏]')
RX_CJK = re.compile('[぀-ヿ㐀-鿿豈-﫿가-힯]')
RX_CYRILLIC = re.compile('[Ѐ-ӿ]')
RX_CYRILLIC_SEQ = re.compile('[Ѐ-ӿ]{3,}')
RX_VIETNAMESE = re.compile('[ăĂđĐơƠưƯẠ-ỹ]')
CJK_TARGETS = ('zh', 'ko', 'ja')
LETTER_WEIGHT = 0.3


def target_of(language):
    v = (language or '').strip().lower()
    for code, prefixes in (('zh', ('zh', 'cn', 'chinese')), ('ja', ('ja', 'jp', 'japanese')),
                           ('ko', ('ko', 'kr', 'korean')), ('pt', ('pt', 'portuguese')), ('es', ('es', 'spanish')),
                           ('ru', ('ru', 'russian')), ('vi', ('vi', 'vietnamese'))):
        if v.startswith(prefixes):
            return code
    return 'en'


def cyrillic_real(t):
    if RX_CYRILLIC_SEQ.search(t):
        return True
    letters = [c for c in t if c.isalpha()]
    n = sum(1 for c in letters if RX_CYRILLIC.match(c))
    return n >= 2 and n >= 0.5 * len(letters)


def lang(t):
    if RX_HANGUL.search(t):
        return 'ko'
    if RX_KANA.search(t):
        return 'ja'
    if RX_HAN.search(t):
        return 'zh'
    if cyrillic_real(t):
        return 'ru'
    if RX_VIETNAMESE.search(t):
        return 'vi'
    return None


def units(t):
    cjk = len(RX_CJK.findall(t))
    if cjk:
        return cjk
    lg = lang(t)
    if lg in ('ru', 'vi'):
        return int(round(sum(1 for c in t if c.isalpha()) * LETTER_WEIGHT))
    return 0


def sobrou(orig, transl, tgt='en'):
    lg = lang(orig)
    if lg is None or lg == tgt or not isinstance(transl, str):
        return None
    if lg == 'ru' and tgt != 'ru' and cyrillic_real(transl):
        return 'Russian text left'
    if lg == 'vi' and tgt != 'vi' and RX_VIETNAMESE.search(transl):
        return 'Vietnamese text left'
    if tgt in CJK_TARGETS:
        if lg == 'ko' and RX_HANGUL.search(transl):
            return 'Korean text left'
        if lg == 'ja' and tgt != 'ja' and RX_KANA.search(transl):
            return 'Japanese text left'
    return None


RX_AI = {
    'pt': re.compile(r'\bIA\b|(?i:traduzid[oa]s? (?:por|com)|tradu[çc][ãa]o (?:autom[áa]tica|por)|'
                     r'intelig[êe]ncia artificial|modelo de linguagem|nota d[oa] tradu)'),
    'es': re.compile(r'\bIA\b|(?i:traducid[oa]s? (?:por|con)|traducci[óo]n (?:autom[áa]tica|por)|'
                     r'inteligencia artificial|modelo de lenguaje|nota de(?:l)? tradu)'),
    'ru': re.compile(r'\bИИ\b|(?i:переведен\w*|машинн\w* перевод|искусственн\w* интеллект|нейросет\w*|'
                     r'примечание переводчика)'),
    'vi': re.compile(r'(?i:dịch bởi|bản dịch|dịch máy|trí tuệ nhân tạo|mô hình ngôn ngữ|ghi chú của người dịch)'),
    'zh': re.compile(r'机器翻译|人工智能翻译|翻译：|译者注|由AI'),
    'ko': re.compile(r'기계 번역|번역:|역자 주|AI 번역|인공지능 번역'),
    'ja': re.compile(r'機械翻訳|翻訳：|訳注|AI翻訳'),
}


def new_ai(orig, transl, tgt='en'):
    rx = RX_AI.get(tgt)
    return bool(rx and isinstance(transl, str) and rx.search(transl) and not rx.search(orig or ''))

