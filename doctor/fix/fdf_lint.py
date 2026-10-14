# Checks the frame files (.fdf, .toc) of a map for what makes the game skip a frame or a whole file.
import os
import re
import shutil



FRAME_TYPES = frozenset((
    'BACKDROP', 'BASE', 'BUTTON', 'CHATDISPLAY', 'CHECKBOX', 'CONTROL', 'DIALOG', 'EDITBOX', 'FRAME', 'GLUEBUTTON',
    'GLUECHECKBOX', 'GLUEEDITBOX', 'GLUEPOPUPMENU', 'GLUETEXTBUTTON', 'HIGHLIGHT', 'LISTBOX', 'LISTBOXITEM',
    'LISTBUTTON', 'MENU', 'MESSAGE', 'MODEL', 'POPUPMENU', 'RADIOGROUP', 'SCROLL', 'SCROLLBAR', 'SIMPLEBUTTON',
    'SIMPLECHECKBOX', 'SIMPLEFRAME', 'SIMPLEGRID', 'SIMPLEMESSAGEFRAME', 'SIMPLESTATUSBAR', 'SIMPLETOP',
    'SLASHCHATBOX', 'SLIDER', 'SPRITE', 'STATUSBAR', 'TEXT', 'TEXTAREA', 'TEXTBUTTON', 'TIMERTEXT'))
KEYWORDS = frozenset(k.lower() for k in (
    'Alpha AlphaMode Anchor Backdrop BackdropBackground BackdropBackgroundInsets BackdropBackgroundSize '
    'BackdropBlendAll BackdropBottomFile BackdropCornerFile BackdropCornerFlags BackdropCornerSize BackdropEdgeFile '
    'BackdropHalfSides BackdropLeftFile BackdropMirrored BackdropRightFile BackdropTileBackground BackdropTopFile '
    'BackgroundArt BarTexture ButtonPushedTextOffset ButtonText ChatDisplayBorderSize ChatDisplayEditBox '
    'ChatDisplayLineHeight ChatDisplayScrollBar CheckBoxCheckHighlight CheckBoxDisabledCheckHighlight Checked '
    'CheckedTexture ControlBackdrop ControlDisabledBackdrop ControlDisabledPushedBackdrop ControlFocusHighlight '
    'ControlMouseOverHighlight ControlPushedBackdrop ControlShortcutKey ControlStyle CursorSprite DecorateFileNames '
    'DialogBackdrop DialogCancelButton DialogOkButton DisabledText DisabledTexture DoNotRegisterName EditBorderSize '
    'EditCursorColor EditHighlightColor EditHighlightInitial EditMaxChars EditSetFocus EditText EditTextColor '
    'EditTextFrame EditTextHeight EditTextOffset File Font FontCharSpacing FontColor FontDisabledColor FontFlags '
    'FontHeight FontHighlightColor FontJustificationH FontJustificationOffset FontJustificationV FontShadowColor '
    'FontShadowOffset Frame FrameFont Height HighlightAlphaFile HighlightAlphaMode HighlightColor '
    'HighlightOutlineOffset HighlightText HighlightType ID IncludeFile Layer LayerStyle ListBoxBorder ListBoxItem '
    'ListBoxItemHeight ListBoxScrollBar ListBoxStyle MenuBorder MenuItem MenuItemHeight MenuTextHighlightColor '
    'NAMED NormalText NormalTexture PopupArrowFrame PopupButtonInset PopupMenuFrame PopupTitleFrame PushedTexture '
    'ScrollBarDecButtonFrame ScrollBarIncButtonFrame SetAllPoints SetPoint SliderInitialValue SliderLayoutHorizontal '
    'SliderLayoutVertical SliderMaxValue SliderMinValue SliderStepSize SliderThumbButtonFrame SpriteCamera '
    'SpriteScale StatusBarSprite String StringList TabFocusDefault TabFocusNext TabFocusPush TexCoord Text '
    'TextAreaInset TextAreaLineGap TextAreaLineHeight TextAreaMaxLines TextAreaScrollBar TextLength Texture ToolTip '
    'UseActiveContext UseBackdrop UseHighlight Width').split())
KEYWORDS |= frozenset(k.lower() for k in ''.split())
BLOCK_KEYWORDS = ('frame', 'string', 'texture', 'layer', 'stringlist')
RX_ACTION = re.compile(r'[A-Za-z][A-Za-z0-9_]*\Z')


def _finding(code, severity, file, line, text):
    return {'code': code, 'severity': severity, 'file': file, 'line': line, 'text': text}


def tokens(text):
    out = []
    i, n, line = 0, len(text), 1
    while i < n:
        c = text[i]
        if c == '\n':
            line += 1
            i += 1
            continue
        if c in ' \t\r﻿':
            i += 1
            continue
        d = text[i:i + 2]
        if d == '//':
            j = text.find('\n', i)
            i = n if j < 0 else j
            continue
        if d == '/*':
            j = text.find('*/', i + 2)
            end = n if j < 0 else j + 2
            line += text.count('\n', i, end)
            i = end
            continue
        if c == '"':
            j = i + 1
            while j < n and text[j] not in '"\r\n':
                j += 1
            closed = j < n and text[j] == '"'
            if not closed:
                k = text.find('"', j)
                if 0 <= k and text.count('\n', j, k) <= 3:
                    out.append(('str', text[i:k + 1], line))
                    line += text.count('\n', i, k)
                    i = k + 1
                    continue
            out.append(('str', text[i:j + (1 if closed else 0)], line))
            i = j + (1 if closed else 0)
            continue
        if c in '{},':
            out.append(('punct', c, line))
            i += 1
            continue
        j = i
        while j < n and text[j] not in ' \t\r\n{},"':
            j += 1
        out.append(('word', text[i:j], line))
        i = j
    return out


def is_action(word):
    return bool(RX_ACTION.match(word)) and word != word.upper()


def events(toks):
    ev = []
    cur = None
    expect = True
    for t in toks:
        kind, val = t[0], t[1]
        if kind == 'word' and expect and is_action(val):
            if cur is not None:
                ev.append(('action', cur[0], cur[1], True))
            cur = [t, []]
            expect = False
            continue
        if kind == 'punct':
            if val == ',':
                expect = True
            elif val == '{':
                ev.append(('open', cur[0] if cur else None, cur[1] if cur else []))
                cur = None
                expect = True
            else:
                if cur is not None:
                    ev.append(('action', cur[0], cur[1], False))
                    cur = None
                ev.append(('close', t[2]))
                expect = True
            continue
        if cur is None:
            continue
        if kind == 'word' and not expect and is_action(val) and val.lower() in KEYWORDS:
            ev.append(('action', cur[0], cur[1], False))
            ev.append(('missing', t))
            cur = [t, []]
            continue
        cur[1].append(t)
        expect = False
    if cur is not None:
        ev.append(('action', cur[0], cur[1], False))
    return ev


def _unq(tok):
    v = tok[1]
    return v[1:-1] if v.startswith('"') and v.endswith('"') and len(v) >= 2 else v


def group(frame_type):
    return 'simple' if frame_type.startswith('SIMPLE') else 'frame'


def definitions(text):
    names, depth = set(), 0
    for e in events(tokens(text)):
        if e[0] == 'open':
            if depth == 0 and e[1] is not None and e[1][1].lower() in ('frame', 'string', 'texture'):
                a = [x for x in e[2] if x[0] == 'str']
                pick = a[1] if e[1][1].lower() == 'frame' and len(a) > 1 else (a[0] if a else None)
                if pick is not None:
                    names.add(_unq(pick).lower())
            depth += 1
        elif e[0] == 'close':
            depth = max(0, depth - 1)
    return names


def _norm(path):
    return path.replace('/', '\\').lstrip('\\')


def lint_text(text, name='x.fdf', resolve=None, known=None):
    f = []
    mains = {}
    includes = []
    inherits = []
    stack = []
    for e in events(tokens(text)):
        if e[0] == 'close':
            if not stack:
                f.append(_finding('fdf_braces', 'warning', name, e[1], 'A `}` closes a block that was never opened.'))
            else:
                stack.pop()
            continue
        if e[0] == 'missing':
            if any(x[0] == 'stringlist' for x in stack):
                continue
            f.append(_finding('fdf_missing_comma', 'warning', name, e[1][2], 'The action %s starts where an argument '
                              'should be: the comma that ends the action before it is missing.' % e[1][1]))
            continue
        in_list = any(s[0] == 'stringlist' for s in stack)
        if e[0] == 'action':
            kw, args = e[1], e[2]
            key = kw[1].lower()
            if in_list:
                continue
            if key == 'includefile':
                strs = [a for a in args if a[0] == 'str']
                if strs:
                    includes.append((kw[2], _unq(strs[0])))
                continue
            if key not in KEYWORDS:
                f.append(_finding('fdf_keyword', 'info', name, kw[2], 'The action %s is not in the list of known fdf '
                                  'actions (a typo, or one the game knows and the list does not).' % kw[1]))
            continue
        kw, args = e[1], e[2]
        if kw is None:
            stack.append(('', None))
            continue
        key, line = kw[1].lower(), kw[2]
        strs = [a for a in args if a[0] == 'str']
        ftype = None
        if key == 'frame' and args:
            raw = args[0][1]
            if args[0][0] != 'str' or not raw.endswith('"') or len(raw) < 2:
                f.append(_finding('fdf_frame_type', 'warning', name, line,
                                  'The type of the frame (%s) is not written in quotes.' % raw))
            else:
                ftype = raw[1:-1]
                if ftype != ftype.upper():
                    f.append(_finding('fdf_frame_type', 'info', name, line, 'The frame type "%s" is not in '
                                      'capitals ("%s" is what the game\'s own files write).' % (ftype, ftype.upper())))
                    ftype = ftype.upper()
                if ftype not in FRAME_TYPES:
                    f.append(_finding('fdf_frame_type', 'warning', name, line,
                                      'The frame type "%s" is not one the game has.' % ftype))
            outer = next((s[1] for s in reversed(stack) if s[1]), None)
            if ftype and outer and group(ftype) == 'simple' and group(outer) == 'frame':
                f.append(_finding('fdf_hierarchy', 'warning', name, line, 'The simple frame "%s" is inside the frame '
                                  'type "%s": the two groups cannot be parent and child.' % (ftype, outer)))
        elif key not in BLOCK_KEYWORDS and not in_list:
            f.append(_finding('fdf_keyword', 'info', name, line, 'The action %s opens a block, which only Frame, '
                              'String, Texture, Layer and StringList do.' % kw[1]))
        if not stack and key in ('frame', 'string', 'texture'):
            mname = (_unq(strs[1]) if len(strs) > 1 else None) if key == 'frame' else (_unq(strs[0]) if strs else None)
            if mname is not None:
                k = mname.lower()
                if k in mains:
                    f.append(_finding('fdf_duplicate_mainframe', 'warning', name, line, 'Two frames named "%s" are '
                                      'defined in this file (the first at line %d): the game ignores the rest of the '
                                      'file from the second.' % (mname, mains[k])))
                else:
                    mains[k] = line
        if key in ('frame', 'string', 'texture'):
            for i, a in enumerate(args):
                if a[0] == 'word' and a[1].upper() == 'INHERITS':
                    rest = [x for x in args[i + 1:] if x[0] == 'str']
                    if rest:
                        inherits.append((line, _unq(rest[0])))
        stack.append((key, ftype))
    if stack:
        f.append(
            _finding('fdf_braces', 'warning', name, 0, '%d block(s) opened with `{` are never closed.' % len(stack))
        )
    if resolve is not None:
        for line, inc in includes:
            if resolve(_norm(inc)) is None:
                f.append(_finding('fdf_include_missing', 'warning', name, line,
                                  'IncludeFile "%s": neither the map nor the game has this file.' % inc))
    if known is not None:
        defined = set(mains)
        for line, parent in inherits:
            if parent.lower() not in defined and parent.lower() not in known:
                f.append(_finding('fdf_inherits_missing', 'warning', name, line,
                                  'INHERITS "%s": no FDF file of the map or of the game defines this frame.' % parent))
    return f


def lint_toc(data, name='x.toc', exists=None):
    f = []
    if data and not data.endswith((b'\n', b'\r')):
        f.append(_finding('toc_final_line', 'warning', name, data.count(b'\n') + 1,
                          'The TOC does not end with a line break: the game does not read its last line.'))
    if exists is not None:
        for i, ln in enumerate(data.decode('utf-8', 'replace').splitlines(), 1):
            ln = ln.strip().lstrip('﻿')
            if ln and not ln.startswith('//') and not exists(_norm(ln)):
                f.append(_finding('toc_missing_file', 'warning', name, i,
                                  'The TOC names "%s", which neither the map nor the game has.' % ln))
    return f


def conserta_toc(data):
    from doctor.fix import fdf_fix
    return (getattr(fdf_fix, 'fix_toc', None) or getattr(fdf_fix, 'fix_toc'))(data)


def _ext(n, e):
    return n.lower().endswith(e)


_GAME_NAMES = []


def game_frame_names(g):
    for gg, names in _GAME_NAMES:
        if gg is g:
            return names
    names = set()
    for n in g.glob('.fdf'):
        d = g.read(n)
        if d:
            names |= definitions(d.decode('utf-8', 'replace'))
    _GAME_NAMES.insert(0, (g, names))
    del _GAME_NAMES[2:]
    return names


def lint(path, progress=None, casc=None):
    p = progress or (lambda *_a, **_k: None)
    from doctor.fix import unprotect
    from doctor.models import model_check
    out = {'files': {}, 'counts': {}, 'fixable': 0, 'game': False, 'scanned': 0}
    a, err = model_check._open(path)
    if a is None:
        out['error'] = err
        return out
    p('Finding the file names')
    names = sorted((n for n in model_check._names(a) if _ext(n, '.fdf') or _ext(n, '.toc')), key=str.lower)
    if not names:
        return out
    from doctor.fix import game_paths
    g = game_paths.open_game(casc)
    out['game'] = g is not None
    cache = {}

    def resolve(pth):
        k = pth.lower()
        if k not in cache:
            d = unprotect._read(a, pth)
            if d is None and g is not None:
                d = g.read(pth)
                if d is None and g.has(pth):
                    d = b''
            cache[k] = d
        return cache[k]

    p('Checking the frame files')
    texts = {}
    known = None
    if g is not None:
        known = set(game_frame_names(g))
        for n in names:
            if _ext(n, '.fdf'):
                d = unprotect._read(a, n)
                if d is not None:
                    texts[n] = d.decode('utf-8', 'replace')
                    known |= definitions(texts[n])
    for n in names:
        d = unprotect._read(a, n)
        if d is None:
            continue
        out['scanned'] += 1
        if _ext(n, '.toc'):
            found = lint_toc(d, n, (lambda q: resolve(q) is not None) if g is not None else None)
        else:
            found = lint_text(
                texts.get(n) or d.decode('utf-8', 'replace'), n, resolve if g is not None else None, known
            )
        if found:
            out['files'][n] = found
            for x in found:
                out['counts'][x['code']] = out['counts'].get(x['code'], 0) + 1
                if x['code'] == 'toc_final_line':
                    out['fixable'] += 1
    return out


def fix(path_in, path_out, progress=None):
    p = progress or (lambda *_a, **_k: None)
    res = {'state': 'failed', 'fixed': 0, 'files': []}
    if os.path.abspath(path_in) == os.path.abspath(path_out):
        res['error'] = 'The output must be a new file.'
        return res
    from doctor.fix import unprotect
    from doctor.models import model_check
    from doctor.mpq import mpqadd
    p('Reading the map')
    a, err = model_check._open(path_in)
    if a is None:
        res['error'] = err
        return res
    names = model_check._names(a)
    repl = []
    for n in names:
        if not _ext(n, '.toc'):
            continue
        d = unprotect._read(a, n)
        if d is None:
            continue
        new, changed = conserta_toc(d)
        if changed:
            repl.append((n, new))
            res['files'].append({'file': n})
    if not repl:
        res['state'] = 'nothing_to_do'
        return res
    part = model_check._part(path_out)
    try:
        p('Writing the new map')
        shutil.copyfile(path_in, part)
        no_room = []
        with unprotect.quiet():
            mpqadd.add_files(part, repl, log=lambda *_a, **_k: None, no_slot=no_room)
        if no_room:
            raise RuntimeError('no room in the hash table for %s' % ', '.join(no_room))
        b, err = model_check._open(part)
        if b is None:
            raise RuntimeError(err)
        for n, new in repl:
            if unprotect._read(b, n) != new:
                raise RuntimeError('%s was not read back fixed' % n)
        done = set(n.lower() for n, _d in repl)
        for n in names:
            if n.lower() in done:
                continue
            x = unprotect._read(a, n)
            if x is not None and unprotect._read(b, n) != x:
                raise RuntimeError('%s changed' % n)
        del a, b
        os.replace(part, path_out)
    except Exception as e:
        try:
            os.remove(part)
        except OSError:
            pass
        res.update(error='The check of the new map failed (%s).' % (str(e) or type(e).__name__), fixed=0, files=[])
        return res
    res['state'] = 'done'
    res['fixed'] = len(repl)
    res['lines'] = ['%s: a final line break added, so the game reads the last line.' % f['file'] for f in res['files']]
    return res
