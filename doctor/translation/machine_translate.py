# Translates the texts of a map into English on this computer, with an open translation model.
import collections
import hashlib
import json
import os
import re
import shutil
import sys
import time
import unicodedata
import zipfile

from doctor.translation import machine_translate_terms as terms
from doctor.translation import translation_io


MODELS = {
    'zh': {'fast': 'opus-mt-zh-en', 'best': 'opus-mt-tc-bible-big-zhx-en'},
    'ko': {'fast': 'opus-mt-ko-en', 'best': 'opus-mt-tc-big-ko-en'},
    'existing': {'fast': 'opus-mt-ja-en'},
    'ru': {'fast': 'opus-mt-ru-en', 'best': 'opus-mt-tc-big-zle-en'},
    'vi': {'fast': 'opus-mt-vi-en'},
    'th': {'fast': 'opus-mt-th-en'},
}
LANGUAGE_NAMES = {
    'zh': 'Chinese',
    'ko': 'Korean',
    'existing': 'Japanese',
    'ru': 'Russian',
    'vi': 'Vietnamese',
    'th': 'Thai',
}
MODELS_REPOSITORY = 'devoltzz/devos-map-doctor'
MODELS_TAG = 'translation-models'
MODEL_ZIPS = {
    'opus-mt-zh-en': {'size': 70627821,
                        'sha256': '0101b0e01b6832058c3029e6ebaaa4c8f4009986842dd34b34797575f4e84342'},
    'opus-mt-tc-bible-big-zhx-en': {'size': 220840555,
                                      'sha256': '84e657ff0ea2922d8e8a96cd1d9d8934f7a2339c1e8ce7f0c9da2ab9f8902f0c'},
    'opus-mt-ko-en': {'size': 67837388,
                        'sha256': '131f20ecbb16db60db0ec56e125ea3d1197c73a07532355ceae1818af03ddec8'},
    'opus-mt-tc-big-ko-en': {'size': 200954655,
                               'sha256': 'c8db454c2a564ddf668f7b965e0632d9fba2b277eaaf9c0850bf7fd3edfb41d1'},
    'opus-mt-ja-en': {'size': 64098277,
                        'sha256': 'a2d2b1aa3fa212aa2513d80583c317ea491b89216f7566d31edda98d591c86fb'},
    'opus-mt-ru-en': {'size': 67208583,
                        'sha256': 'd46482ea351118aee2995564b39e1e97ce5e70090ba78b236900636e35e8c56f'},
    'opus-mt-tc-big-zle-en': {'size': 221033629,
                                'sha256': '70a33489ca526bb33de7d5f837dc3619669c09888e9e9c1546f128f7e7ec6a60'},
    'opus-mt-vi-en': {'size': 61892596,
                        'sha256': '8be5f796d732efad4e5c1e34f72293dc40cffbbb406c688428dd67f86bc31a04'},
    'opus-mt-th-en': {'size': 67820863,
                        'sha256': 'a87cc13aae797e415a674232e056a73e758eb48e00ffec851789ac8d2d45bcae'},
}
MODEL_FILES = ('model.bin', 'config.json', 'source.spm', 'target.spm')
VOCABULARIES = (('shared_vocabulary.json',), ('source_vocabulary.json', 'target_vocabulary.json'))

HAN = '\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff'
KANA = '\u3040-\u30ff\u31f0-\u31ff'
HANGUL = '\uac00-\ud7a3\u1100-\u11ff\u3130-\u318f'
SCRIPT_OF = {
    'zh': re.compile('[' + HAN + ']'),
    'existing': re.compile('[' + HAN + KANA + ']'),
    'ko': re.compile('[' + HANGUL + HAN + ']'),
    'ru': re.compile('[\u0400-\u04ff]'),
    'th': re.compile('[\u0e00-\u0e7f]'),
    'vi': re.compile('[\u0102\u0103\u0110\u0111\u01a0\u01a1\u01af\u01b0\u1ea0-\u1ef9]'),
}
SPACELESS = ('zh', 'existing', 'th')


def _nothing(*_a, **_k):
    pass


def detect_language(texts):
    count = collections.Counter()
    for t in texts:
        if re.search('[' + KANA + ']', t):
            count['existing'] += 1
        elif re.search('[' + HANGUL + ']', t):
            count['ko'] += 1
        elif re.search('[' + HAN + ']', t):
            count['zh'] += 1
        elif SCRIPT_OF['ru'].search(t):
            count['ru'] += 1
        elif SCRIPT_OF['th'].search(t):
            count['th'] += 1
        elif SCRIPT_OF['vi'].search(t):
            count['vi'] += 1
    if not count:
        return ''
    lang, n = count.most_common(1)[0]
    if lang == 'zh' and count['existing'] * 4 >= n:
        lang = 'existing'
    return lang


def models_dir():
    if os.environ.get('DMD_MODELS_DIR'):
        return os.environ['DMD_MODELS_DIR']
    if sys.platform.startswith('linux'):
        base = os.environ.get('XDG_DATA_HOME') or os.path.join(os.path.expanduser('~'), '.local', 'share')
    else:
        base = os.environ.get('LOCALAPPDATA') or os.environ.get('APPDATA') or os.path.expanduser('~')
    return os.path.join(base, 'DevosMapDoctor', 'models')


def model_path(name):
    return os.path.join(models_dir(), name)


def complete(d):
    return all(os.path.isfile(os.path.join(d, f)) for f in MODEL_FILES) and \
        any(all(os.path.isfile(os.path.join(d, f)) for f in v) for v in VOCABULARIES)


def installed(name):
    return complete(model_path(name))


def model_for(lang, quality='best'):
    m = MODELS.get(lang) or {}
    return m.get(quality) or m.get('fast')


def info(lang):
    out = {'language': lang or '', 'name': LANGUAGE_NAMES.get(lang, ''), 'models': [], 'ocr': None}
    try:
        from doctor.translation import image_translate
        out['ocr'] = image_translate.ocr_info(lang)
    except Exception:
        pass
    for q in ('best', 'fast'):
        name = (MODELS.get(lang) or {}).get(q)
        if name:
            out['models'].append({'quality': q, 'model': name, 'size': (MODEL_ZIPS.get(name) or {}).get('size', 0),
                                  'installed': installed(name)})
    return out


def model_url(name):
    base = os.environ.get('DMD_MODELS_URL') or 'https://github.com/%s/releases/download/%s' % (MODELS_REPOSITORY,
                                                                                               MODELS_TAG)
    return base.rstrip('/') + '/' + name + '.zip'


CA_FILES = ('/etc/ssl/certs/ca-certificates.crt', '/etc/pki/tls/certs/ca-bundle.crt', '/etc/ssl/ca-bundle.pem',
            '/etc/ssl/cert.pem', '/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem')


def _ssl_context():
    import ssl
    ctx = ssl.create_default_context()
    if not ctx.cert_store_stats().get('x509_ca'):
        for f in CA_FILES:
            if os.path.isfile(f):
                try:
                    ctx.load_verify_locations(cafile=f)
                    break
                except (OSError, ssl.SSLError):
                    continue
    return ctx


def download(name, progress=None, complete=None, table=None):
    import urllib.request
    p = progress or _nothing
    complete = complete or globals()['complete']
    want = (MODEL_ZIPS if table is None else table).get(name) or {}
    os.makedirs(models_dir(), exist_ok=True)
    part = model_path(name) + '.zip.part'
    url = model_url(name)
    h = hashlib.sha256()
    got = 0
    if os.path.isfile(url):
        src = open(url, 'rb')
        total = os.path.getsize(url)
    else:
        src = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'DevosMapDoctor'}),
                                     timeout=60, context=_ssl_context())
        total = int(src.headers.get('Content-Length') or 0) or want.get('size') or 0
    try:
        with src, open(part, 'wb') as out:
            last = 0
            while True:
                chunk = src.read(1 << 20)
                if not chunk:
                    break
                out.write(chunk)
                h.update(chunk)
                got += len(chunk)
                if total and got - last >= (4 << 20):
                    last = got
                    p('Downloading the translation model: %d of %d MB' % (got >> 20, total >> 20))
        if want and (got != want['size'] or h.hexdigest() != want['sha256']):
            raise OSError('the download of %s is incomplete or damaged' % name)
        tmp = model_path(name) + '.new'
        shutil.rmtree(tmp, ignore_errors=True)
        with zipfile.ZipFile(part) as z:
            for info in z.infolist():
                base = os.path.basename(info.filename)
                if not base or base != info.filename.split('/')[-1] or '..' in info.filename:
                    continue
                with z.open(info) as f, open(os.path.join(_mk(tmp), base), 'wb') as o:
                    shutil.copyfileobj(f, o)
        if not complete(tmp):
            raise OSError('the %s model is missing files' % name)
        shutil.rmtree(model_path(name), ignore_errors=True)
        os.replace(tmp, model_path(name))
    finally:
        if os.path.exists(part):
            os.remove(part)


def _mk(d):
    os.makedirs(d, exist_ok=True)
    return d


class Engine(object):
    def __init__(self, name, threads=0):
        import ctranslate2
        import sentencepiece
        d = model_path(name)
        self.name = name
        self.translator = ctranslate2.Translator(d, device='cpu', compute_type='int8',
                                                 intra_threads=threads or max(1, min(8, os.cpu_count() or 1)))
        self.src = sentencepiece.SentencePieceProcessor(model_file=os.path.join(d, 'source.spm'))
        self.tgt = sentencepiece.SentencePieceProcessor(model_file=os.path.join(d, 'target.spm'))

    def translate(self, texts, progress=None, batch=32, beam=4, n=1):
        p = progress or _nothing
        out = [None] * len(texts)
        order = sorted(range(len(texts)), key=lambda i: len(texts[i]))
        for start in range(0, len(order), batch):
            ids = order[start:start + batch]
            toks = [self.src.encode(texts[i], out_type=str)[:400] + ['</s>'] for i in ids]
            res = self.translator.translate_batch(
                toks, beam_size=max(beam, n), num_hypotheses=n, max_batch_size=batch,
                max_decoding_length=min(512, 3 * max(map(len, toks)) + 16), repetition_penalty=1.1,
                no_repeat_ngram_size=4)
            for i, t, r in zip(ids, toks, res):
                hyps = [self.tgt.decode([x for x in h if x != '</s>']) for h in r.hypotheses]
                out[i] = hyps if n > 1 else hyps[0]
            p(min(len(order), start + batch), len(order))
        return out


PROTECT = re.compile(r'(\|[cC][0-9a-fA-F]{8}|\|[rRnN]|%(?:\d+\$)?[sd]|\\[n"\\]|\r\n|[\r\n]|'
                     r'<[A-Za-z0-9]{4},[A-Za-z0-9]+(?:,%)?>)')
COLOR = re.compile(r'\|[cC][0-9a-fA-F]{8}$|\|[rR]$')
SPLIT = re.compile(r'([\u3002\uff01\uff1f\uff1b!?;\u2026]+|[\u3010\u3011\[\]\uff08\uff09()\u300a\u300b\u300c\u300d'
                   r'\u300e\u300f\u201c\u201d\u3008\u3009])')
PUNCT = {'\u3002': '.', '\uff01': '!', '\uff1f': '?', '\uff1b': ';', '\u2026': '...', '\u3010': '[', '\u3011': ']',
         '\uff08': '(', '\uff09': ')', '\u300a': '<', '\u300b': '>', '\u300c': "'", '\u300d': "'", '\u300e': "'",
         '\u300f': "'", '\u201c': "'", '\u201d': "'", '\u3008': '<', '\u3009': '>', '\uff0c': ',', '\u3001': ',',
         '\uff1a': ':', '\uff5e': '~', '\u3000': ' ', '\u00b7': '\u00b7'}
LONG = {'zh': 24, 'existing': 30, 'ko': 40}
CLAUSE = re.compile(r'(\s*[，,、：:]\s*)')
OPENING = '([<'
CLOSING = ')]>.,!?;:'
RX_MULT_ZH = re.compile(r'(\d+(?:\.\d+)?)[ \t]*([\u767e\u5343\u4e07\u4ebf])')
MULT_ZH = {'\u767e': 100, '\u5343': 1000, '\u4e07': 10000, '\u4ebf': 100000000}


def _ascii_punct(s):
    out = []
    for c in s:
        if c in PUNCT:
            out.append(PUNCT[c])
        elif '\uff01' <= c <= '\uff5e':
            out.append(chr(ord(c) - 0xfee0))
        else:
            out.append(c)
    return ''.join(out)


def _expand_mult(m):
    v = float(m.group(1)) * MULT_ZH[m.group(2)]
    return '%d' % round(v) if abs(v - round(v)) < 1e-6 else ('%f' % v).rstrip('0').rstrip('.')


class Plan(object):
    def __init__(self, lang, text=''):
        self.lang = lang
        self.text = text
        self.script = SCRIPT_OF[lang]
        self.parts = []

    def needs(self, s):
        return bool(self.script.search(s))

    def add_core(self, s):
        m = re.match(r'^(\s*[^\w]*)(.*?)([^\w]*\s*)$', s, re.S)
        if m.group(1):
            self.parts.append(('lit', _ascii_punct(m.group(1))))
        if m.group(2):
            self.parts.append(('mt', m.group(2)) if self.needs(m.group(2)) else ('lit', _ascii_punct(m.group(2))))
        if m.group(3):
            self.parts.append(('lit', _ascii_punct(m.group(3))))

    def add_text(self, s):
        for i, chunk in enumerate(SPLIT.split(s)):
            if not chunk:
                continue
            if i % 2:
                self.parts.append(('lit', _ascii_punct(chunk)))
                continue
            core = chunk.strip()
            lead = chunk[:len(chunk) - len(chunk.lstrip())]
            trail = chunk[len(chunk.rstrip()):]
            m = re.match(r'^([^\w]*)(.*?)([^\w]*)$', core, re.S)
            pre, mid, post = m.group(1), m.group(2), m.group(3)
            if lead:
                self.parts.append(('lit', _ascii_punct(lead)))
            if pre:
                self.parts.append(('lit', _ascii_punct(pre)))
            if mid and self.needs(mid):
                if len(mid) > LONG.get(self.lang, 90):
                    for k, cl in enumerate(CLAUSE.split(mid)):
                        if k % 2:
                            self.parts.append(('lit', _ascii_punct(cl)))
                        elif cl.strip():
                            self.add_core(cl)
                else:
                    self.parts.append(('mt', mid))
            elif mid:
                self.parts.append(('lit', _ascii_punct(mid)))
            if post:
                self.parts.append(('lit', _ascii_punct(post)))
            if trail:
                self.parts.append(('lit', _ascii_punct(trail)))


def plan(text, lang):
    pl = Plan(lang, text)
    pieces = PROTECT.split(text)
    i = 0
    n = len(pieces)
    while i < n:
        s = pieces[i]
        if i % 2:
            pl.parts.append(('code', s))
            i += 1
            continue
        run = [s]
        codes = []
        j = i
        while (j + 2 < n and COLOR.match(pieces[j + 1]) and _tiny(pieces[j], pl) and _tiny(pieces[j + 2], pl)):
            codes.append(pieces[j + 1])
            run.append(pieces[j + 2])
            j += 2
        if len(run) >= 3:
            pl.parts.append(('run', ''.join(run), codes))
            i = j + 1
            continue
        if s:
            pl.add_text(s)
        i += 1
    return pl


def _tiny(s, pl):
    return 1 <= len(s) <= 2 and all(pl.script.match(c) for c in s)


def segments_of(pl):
    return [p[1] for p in pl.parts if p[0] in ('mt', 'run')]


def model_input(s, lang):
    s = unicodedata.normalize('NFKC', s)
    if lang in ('zh', 'existing'):
        s = RX_MULT_ZH.sub(_expand_mult, s)
    if lang == 'ko':
        s = RX_ENHANCE_KO.sub(r'+\1', s)
        s = RX_MULT_KO.sub(_expand_mult_ko, s)
    return inject(s, lang)


RX_MULT_KO = re.compile(r'(\d+(?:\.\d+)?)\s*(\ucc9c\ub9cc|\ubc31\ub9cc|\uc2ed\ub9cc|\ub9cc|\uc5b5)(?!\ud07c)')
MULT_KO = {'\ucc9c\ub9cc': 10 ** 7, '\ubc31\ub9cc': 10 ** 6, '\uc2ed\ub9cc': 10 ** 5, '\ub9cc': 10 ** 4,
           '\uc5b5': 10 ** 8}


def _expand_mult_ko(m):
    v = float(m.group(1)) * MULT_KO[m.group(2)]
    return '%d' % round(v) if abs(v - round(v)) < 1e-6 else ('%f' % v).rstrip('0').rstrip('.')


RX_ENHANCE_KO = re.compile(r'(?<![\d.])\+?(\d+)\s*\uac15(?!\ud654)')
_TERMS = {}


def _terms(lang):
    if lang not in _TERMS:
        _TERMS[lang] = sorted(terms.TERMS.get(lang, []), key=lambda t: -len(t[0]))
    return _TERMS[lang]


def glossary(s, lang):
    k = unicodedata.normalize('NFKC', s.strip())
    for src, en in _terms(lang):
        if k == src:
            return en
    return None


def inject(s, lang):
    if lang not in terms.TERMS:
        return s
    pad = ' ' if lang in SPACELESS else ''
    for src, en in _terms(lang):
        if len(src) >= 2 and src in s:
            s = s.replace(src, pad + en + pad)
    return ' '.join(s.split()) if pad else s


def split_verb(s, lang):
    for src, en in terms.VERBS.get(lang, []):
        if s.startswith(src) and SCRIPT_OF[lang].search(s[len(src):]):
            return en, s[len(src):].strip()
    for src, en in terms.SUFFIX_VERBS.get(lang, []):
        if s.endswith(src) and SCRIPT_OF[lang].search(s[:-len(src)]):
            return en, s[:-len(src)].strip()
    return None


def translate_sources(sources, lang, engine, progress=None):
    out, verb, todo = {}, {}, collections.OrderedDict()
    for s in sources:
        g = glossary(s, lang)
        if g:
            out[s] = g
            continue
        v = split_verb(s, lang)
        if v:
            verb[s] = v
            if not glossary(v[1], lang):
                i = model_input(v[1], lang)
                if SCRIPT_OF[lang].search(i):
                    todo.setdefault(i, []).append(v[1])
                else:
                    out.setdefault(v[1], i)
            continue
        i = model_input(s, lang)
        if not SCRIPT_OF[lang].search(i):
            out[s] = i
            continue
        todo.setdefault(i, []).append(s)
    inputs = list(todo)
    outs = engine.translate(inputs, progress) if inputs else []
    bad = [k for k, (i, o) in enumerate(zip(inputs, outs)) if not good_output(i, o)]
    if bad:
        if progress:
            progress(len(inputs), len(inputs))
        alts = engine.translate([inputs[k] for k in bad], None, beam=8, n=8)
        for k, hyps in zip(bad, alts):
            ok = [h for h in hyps if good_output(inputs[k], h)]
            if ok:
                outs[k] = ok[0]
            elif '\u2047' in outs[k] or outs[k].strip().rstrip('.').lower() in JUNK:
                outs[k] = ''
    by_src = {}
    for i, o in zip(inputs, outs):
        for s in todo[i]:
            by_src[s] = clean_output(s, o)
    for s in sources:
        if s in out:
            continue
        if s in verb:
            en, rest = verb[s]
            r = glossary(rest, lang) or by_src.get(rest) or out.get(rest)
            if r:
                r = re.sub(r'^(?:the|a|an)\s+', '', r, flags=re.I)
                out[s] = en + ' ' + r
            continue
        out[s] = by_src.get(s)
    return out, len(inputs)


RX_END = re.compile(r'[.!?\u3002\uff01\uff1f]$')


JUNK = frozenset(('about us', 'contact us', 'home', 'main page', 'shh', 'see also', 'external links', 'references',
                  'notes', 'school', 'category'))


def good_output(i, o):
    if '\u2047' in o or not o.strip() or o.strip().rstrip('.').lower() in JUNK:
        return False
    from doctor.translation import tr_pair_check
    o = fix_numbers(i, o)
    a = collections.Counter(tr_pair_check.numbers(tr_pair_check.without_thousands(i)))
    b = collections.Counter(tr_pair_check.numbers(tr_pair_check.without_thousands(o), origin=False))
    return set((a - b) + (b - a)) <= {'1'}


RX_LANG_TAG = re.compile(r'>>\w+<<\s*')


def clean_output(src, out):
    out = ' '.join(RX_LANG_TAG.sub('', out).split())
    if out.startswith('Category:') and ':' not in src and '\uff1a' not in src:
        out = out[len('Category:'):].strip()
    if not re.search('[(\uff08]', src):
        out = re.sub(r'\s*\([^()]*\)', '', out).strip() or out
    if out.endswith('.') and not out.endswith('...') and not RX_END.search(src.strip()):
        out = out[:-1]
    return out


def _spread(words, codes):
    k = len(codes) + 1
    n = len(words)
    at = collections.defaultdict(list)
    for c_i, code in enumerate(codes):
        at[min(n, max(1, round((c_i + 1) * n / k)))].append(code)
    out = []
    for w_i, w in enumerate(words):
        if at.get(w_i):
            out.append(''.join(at[w_i]) + w)
        else:
            out.append(w)
    s = ' '.join(out)
    if at.get(n):
        s += ''.join(at[n])
    return s


def assemble(pl, tr):
    items = []
    for p in pl.parts:
        if p[0] == 'code':
            items.append(('code', p[1]))
        elif p[0] == 'lit':
            items.append(('lit', p[1]))
        elif p[0] == 'mt':
            t = tr.get(p[1])
            items.append(('mt', t) if t else ('lit', p[1]))
        else:
            t = tr.get(p[1])
            if not t:
                return None
            items.append(('mt', _spread(t.split(), p[2])))
    out = []
    last_vis = None
    pending = []
    for kind, s in items:
        if kind == 'code':
            pending.append(s)
            if s.lower() in ('|n', '\\n', '\n', '\r\n', '\r'):
                last_vis = None
            continue
        if not s:
            continue
        if kind == 'mt' and last_vis is not None and last_vis[1].rstrip()[-1:] in (',', ';'):
            s = _lower_first(s)
        if last_vis is not None and ('mt' in (kind, last_vis[0])) and _needs_space(last_vis[1], s):
            k = 0
            while k < len(pending) and pending[k].lower() == '|r':
                k += 1
            out.extend(pending[:k])
            pending = pending[k:]
            out.append(' ')
        out.extend(pending)
        pending = []
        out.append(s)
        last_vis = (kind, s)
    out.extend(pending)
    return ''.join(out)


CLAUSE_WORDS = set('and but or the a an it its this that these those then when if with for to of in on at by each '
                   'every deal deals increase increases increased reduce reduces reduced slow slows slowed lasts last '
                   'can will also while after before which who and makes make causes cause gives give gains gain '
                   'restores restore recovers recover heals heal is are was were has have'.split())


def _lower_first(s):
    w = re.match(r'[A-Za-z]+', s)
    if w and w.group(0).lower() in CLAUSE_WORDS and not w.group(0).isupper():
        return s[0].lower() + s[1:]
    return s


def _needs_space(left, right):
    a, b = left[-1], right[0]
    if a.isspace() or b.isspace():
        return False
    if a in OPENING or b in CLOSING:
        return False
    left_ok = a.isalnum() or a in ')]>.!?;:,%\'"'
    right_ok = b.isalnum() or b in OPENING
    return left_ok and right_ok


def entry_plans(e, lang):
    tx = e.get('_tx') or {}
    text = e['text']
    if tx.get('comma') and not tx.get('quoted'):
        return [plan(x, lang) for x in text.split(',')], 'comma'
    if tx.get('quoted') and '","' in text:
        return [plan(x, lang) for x in text.split('","')], 'quoted'
    return [plan(text, lang)], None


NUMBER_WORDS = {
    'one': 1,
    'two': 2,
    'three': 3,
    'four': 4,
    'five': 5,
    'six': 6,
    'seven': 7,
    'eight': 8,
    'nine': 9,
    'ten': 10,
    'eleven': 11,
    'twelve': 12,
    'fifteen': 15,
    'twenty': 20,
    'thirty': 30,
    'forty': 40,
    'fifty': 50,
    'sixty': 60,
    'seventy': 70,
    'eighty': 80,
    'ninety': 90,
    'hundred': 100,
    'once': 1,
    'twice': 2,
    'thrice': 3,
    'double': 2,
    'triple': 3,
}
RX_NUMBER_WORD = re.compile(r'\b(?:(twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)-(one|two|three|four|'
                            r'five|six|seven|eight|nine)|(' + '|'.join(NUMBER_WORDS) + r'))\b', re.I)
RX_BIG_NUMBER = re.compile(r'(\d+(?:\.\d+)?)\s*(thousand|million|billion)\b', re.I)
BIG = {'thousand': 10 ** 3, 'million': 10 ** 6, 'billion': 10 ** 9}


def fix_numbers(src, out):
    from doctor.translation import tr_pair_check
    missing = collections.Counter(tr_pair_check.numbers(tr_pair_check.without_thousands(src))) - \
        collections.Counter(tr_pair_check.numbers(tr_pair_check.without_thousands(out), origin=False))
    if not missing:
        return out

    def big(m):
        v = float(m.group(1)) * BIG[m.group(2).lower()]
        v = '%d' % round(v) if abs(v - round(v)) < 1e-6 else str(v)
        if missing.get(v):
            missing[v] -= 1
            return v
        return m.group(0)

    def put(m):
        if m.group(1):
            v = str(NUMBER_WORDS[m.group(1).lower()] + NUMBER_WORDS[m.group(2).lower()])
            word = ''
        else:
            v = str(NUMBER_WORDS[m.group(3).lower()])
            word = ' times' if m.group(3).lower() in ('once', 'twice', 'thrice') else ''
        if missing.get(v):
            missing[v] -= 1
            return v + word
        return m.group(0)
    return RX_NUMBER_WORD.sub(put, RX_BIG_NUMBER.sub(big, out))


RX_THOUSANDS = re.compile(r'(?<![\d.,])\d{1,3}(?:,\d{3})+(?![\d,]|\.\d)')


def entry_translation(e, lang, tr):
    plans, join = entry_plans(e, lang)
    parts = []
    for pl in plans:
        s = assemble(pl, tr)
        if s is None:
            return None
        s = fix_numbers(pl.text, s)
        if '++' in s and '++' not in pl.text:
            s = s.replace('++', '+')
        if join == 'comma':
            s = RX_THOUSANDS.sub(lambda m: m.group(0).replace(',', ''), s).replace(',', ';')
        parts.append(s)
    return {'comma': ',', 'quoted': '","'}.get(join, '').join(parts)


def translate_entries(entries, lang, engine, progress=None, language=''):
    p = progress or _nothing
    plans = {}
    wanted = collections.OrderedDict()
    for e in entries:
        if not SCRIPT_OF[lang].search(e['text']):
            continue
        pls, _join = entry_plans(e, lang)
        plans[e['id']] = pls
        for pl in pls:
            for s in segments_of(pl):
                wanted.setdefault(s, None)
    sources = list(wanted)
    t0 = time.time()

    def step(done, total):
        el = time.time() - t0
        left = el / done * (total - done) if done else 0
        p('Translating: %d of %d pieces, about %d s left' % (done, total, left))
    tr, n_inputs = translate_sources(sources, lang, engine, step)
    result, rejected = {}, collections.Counter()
    for e in entries:
        if e['id'] not in plans:
            continue
        t = entry_translation(e, lang, tr)
        if t is None:
            rejected['not translated'] += 1
            continue
        t, _n = translation_io.unglue(e['text'], t, language)
        errs = translation_io.check_entry(e, t, language)
        if errs:
            rejected[errs[0].split(' (')[0]] += 1
            continue
        result[e['id']] = t
    return result, {'pieces': n_inputs, 'seconds': round(time.time() - t0, 1), 'rejected': dict(rejected)}


def translate_map(path, out_file, progress=None, only=None, quality='best', lang=None, threads=0, images=False):
    p = progress or _nothing
    rep = {'state': None, 'error': None, 'file': None, 'entries': 0, 'language': '', 'model': None, 'translated': 0,
           'left': 0, 'rejected': {}, 'pieces': 0, 'seconds': 0, 'images': None}
    try:
        p('reading map')
        a = translation_io._open(path)
        mt = translation_io.collect(a, p)
    except (Exception, SystemExit) as e:
        rep.update(state='failed', error='cannot read the map (%s)' % translation_io._error(e))
        return rep
    if only is not None:
        mt.entries, _extra = translation_io._only(mt.entries, only)
    rep['entries'] = len(mt.entries)
    if not mt.entries:
        rep['state'] = 'no_text'
        return rep
    lang = lang or detect_language(e['text'] for e in mt.entries)
    rep['language'] = lang
    if lang not in MODELS:
        rep.update(state='failed', error='the texts are not in a language the local translation knows (Chinese, '
                                         'Korean, Japanese, Russian, Vietnamese or Thai)')
        return rep
    name = model_for(lang, quality)
    rep['model'] = name
    try:
        if not installed(name):
            p('Downloading the translation model')
            download(name, p)
        p('Loading the translation model')
        engine = Engine(name, threads)
    except Exception as e:
        rep.update(state='failed', error='cannot get the translation model %s (%s)' % (name, translation_io._error(e)))
        return rep
    if images:
        n, _lang, err = translation_io.add_images(mt, path, p)
        rep['images'] = {'entries': n, 'error': err}
        rep['entries'] = len(mt.entries)
    result, info = translate_entries(mt.entries, lang, engine, p)
    rep.update(info)
    order = {'w3i': 0, 'wts': 1, 'object': 2, 'profile': 3, 'fdf': 4, 'script': 5, 'image': 6}
    entries = []
    for e in sorted(mt.entries, key=lambda e: order[e['source']]):
        x = translation_io.public(e)
        x['translation'] = result.get(e['id'], '')
        entries.append(x)
    rep['translated'] = sum(1 for x in entries if x['translation'])
    rep['left'] = len(entries) - rep['translated']
    doc = collections.OrderedDict([('format', translation_io.FORMAT), ('version', translation_io.VERSION),
                                   ('map', os.path.basename(path)), ('map_name', mt.map_name), ('language', ''),
                                   ('machine', {'model': name, 'from': lang}),
                                   ('help', list(translation_io.HELP)), ('entries', entries)])
    p('writing')
    part = out_file + '.part'
    try:
        with open(part, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(doc, f, ensure_ascii=False, indent=1)
        with open(part, encoding='utf-8') as f:
            if json.load(f) != json.loads(json.dumps(doc)):
                raise ValueError('the file did not read back the same')
        os.replace(part, out_file)
    except Exception as e:
        if os.path.exists(part):
            os.remove(part)
        rep.update(state='failed', error='cannot write the file (%s)' % translation_io._error(e))
        return rep
    rep.update(state='done', file=out_file)
    return rep
