// The canonical form of the trigger proof in Rust, the same text as the Python.
use std::collections::{HashMap, HashSet};
use std::panic;

type Tok = Vec<u8>;

pub enum Re {
    Text(Vec<u8>),
    NoParse,
    Refuse,
}

#[derive(Clone, Copy, PartialEq)]
enum Lang {
    Jass,
    Lua,
}

fn is_ws(t: &[u8], i: usize) -> usize {
    match t[i] {
        b' ' | b'\t' => 1,
        0xEF if t.len() >= i + 3 && t[i + 1] == 0xBB && t[i + 2] == 0xBF => 3,
        _ => 0,
    }
}

fn char_len(t: &[u8], i: usize) -> usize {
    let b = t[i];
    let n = if b < 0x80 {
        1
    } else if b >= 0xF0 {
        4
    } else if b >= 0xE0 {
        3
    } else if b >= 0xC0 {
        2
    } else {
        1
    };
    if n > 1 && i + n <= t.len() && std::str::from_utf8(&t[i..i + n]).is_ok() {
        n
    } else {
        1
    }
}

fn is_word_b(b: u8) -> bool {
    b.is_ascii_alphanumeric() || b == b'_'
}

fn digits(t: &[u8], i: usize) -> usize {
    let mut k = i;
    while k < t.len() && t[k].is_ascii_digit() {
        k += 1;
    }
    k
}

fn hexes(t: &[u8], i: usize) -> usize {
    let mut k = i;
    while k < t.len() && t[k].is_ascii_hexdigit() {
        k += 1;
    }
    k
}

fn quoted(t: &[u8], i: usize, q: u8, lines: bool) -> Option<usize> {
    let mut k = i + 1;
    while k < t.len() {
        let c = t[k];
        if c == q {
            return Some(k + 1);
        }
        if c == b'\\' {
            if k + 1 >= t.len() {
                return None;
            }
            k += 1 + char_len(t, k + 1);
            continue;
        }
        if lines && (c == b'\r' || c == b'\n') {
            return None;
        }
        k += 1;
    }
    None
}

fn long_bracket(t: &[u8], i: usize) -> Option<usize> {
    if t.get(i) != Some(&b'[') {
        return None;
    }
    let mut k = i + 1;
    while k < t.len() && t[k] == b'=' {
        k += 1;
    }
    if t.get(k) != Some(&b'[') {
        return None;
    }
    let eq = k - i - 1;
    let mut j = k + 1;
    while j < t.len() {
        if t[j] == b']' && j + eq + 1 < t.len() && t[j + 1..j + 1 + eq].iter().all(|&c| c == b'=') && t[j + 1 + eq] == b']'
        {
            return Some(j + eq + 2);
        }
        j += 1;
    }
    None
}

fn line_breaks(t: &[u8]) -> usize {
    let mut n = 0;
    let mut i = 0;
    while i < t.len() {
        if t[i] == b'\r' {
            n += 1;
            if i + 1 < t.len() && t[i + 1] == b'\n' {
                i += 1;
            }
        } else if t[i] == b'\n' {
            n += 1;
        }
        i += 1;
    }
    n
}

fn token_end(t: &[u8], q: usize, lang: Lang) -> Result<usize, ()> {
    let c = t[q];
    let n = t.len();
    let nx = |k: usize| -> u8 { if k < n { t[k] } else { 0 } };
    if lang == Lang::Lua {
        if c == b'-' && nx(q + 1) == b'-' {
            if let Some(e) = long_bracket(t, q + 2) {
                return Ok(e);
            }
            let mut k = q + 2;
            while k < n && t[k] != b'\r' && t[k] != b'\n' {
                k += 1;
            }
            return Ok(k);
        }
    } else if c == b'/' && nx(q + 1) == b'/' {
        let mut k = q + 2;
        while k < n && t[k] != b'\r' && t[k] != b'\n' {
            k += 1;
        }
        return Ok(k);
    }
    if c == b'\r' {
        return Ok(if nx(q + 1) == b'\n' { q + 2 } else { q + 1 });
    }
    if c == b'\n' {
        return Ok(q + 1);
    }
    if lang == Lang::Lua && c == b'[' {
        if let Some(e) = long_bracket(t, q) {
            return Ok(e);
        }
    }
    if c == b'"' || c == b'\'' {
        if let Some(e) = quoted(t, q, c, lang == Lang::Lua) {
            return Ok(e);
        }
        return Ok(q + 1);
    }
    if c.is_ascii_alphabetic() || c == b'_' {
        let mut k = q + 1;
        while k < n && is_word_b(t[k]) {
            k += 1;
        }
        if k < n && t[k] >= 0x80 {
            return Err(());
        }
        return Ok(k);
    }
    if c == b'0' && (nx(q + 1) == b'x' || nx(q + 1) == b'X') && nx(q + 2).is_ascii_hexdigit() {
        return Ok(hexes(t, q + 2));
    }
    if lang == Lang::Jass && c == b'$' && nx(q + 1).is_ascii_hexdigit() {
        return Ok(hexes(t, q + 1));
    }
    if c.is_ascii_digit() {
        let d = digits(t, q);
        if d < n && t[d] >= 0x80 {
            return Err(());
        }
        if nx(d) == b'.' {
            let mut e = digits(t, d + 1);
            if e < n && t[e] >= 0x80 {
                return Err(());
            }
            if lang == Lang::Lua && (nx(e) == b'e' || nx(e) == b'E') {
                let mut k = e + 1;
                if nx(k) == b'+' || nx(k) == b'-' {
                    k += 1;
                }
                if nx(k).is_ascii_digit() {
                    e = digits(t, k);
                    if e < n && t[e] >= 0x80 {
                        return Err(());
                    }
                }
            }
            return Ok(e);
        }
        return Ok(d);
    }
    if c == b'.' && nx(q + 1).is_ascii_digit() {
        let e = digits(t, q + 1);
        if e < n && t[e] >= 0x80 {
            return Err(());
        }
        return Ok(e);
    }
    if c == b'.' && nx(q + 1) >= 0x80 {
        return Err(());
    }
    if lang == Lang::Lua {
        if c == b'.' && nx(q + 1) == b'.' {
            return Ok(if nx(q + 2) == b'.' { q + 3 } else { q + 2 });
        }
        if (c == b'=' || c == b'~' || c == b'<' || c == b'>') && nx(q + 1) == b'=' {
            return Ok(q + 2);
        }
        if c == b':' && nx(q + 1) == b':' {
            return Ok(q + 2);
        }
        if c == b'/' && nx(q + 1) == b'/' {
            return Ok(q + 2);
        }
    } else if (c == b'=' || c == b'!' || c == b'<' || c == b'>') && nx(q + 1) == b'=' {
        return Ok(q + 2);
    }
    if c >= 0x80 {
        return Err(());
    }
    Ok(q + 1)
}

pub fn tokens(t: &[u8], lua: bool) -> Result<Vec<Tok>, ()> {
    let lang = if lua { Lang::Lua } else { Lang::Jass };
    let mut out = Vec::new();
    let mut i = 0;
    let n = t.len();
    while i < n {
        let mut q = i;
        loop {
            if q >= n {
                break;
            }
            let w = is_ws(t, q);
            if w == 0 {
                break;
            }
            q += w;
        }
        if q >= n {
            break;
        }
        let e = token_end(t, q, lang)?;
        let tok = &t[q..e];
        let comment = if lua { tok.starts_with(b"--") } else { tok.starts_with(b"//") };
        if tok == b"\n" || tok == b"\r\n" || tok == b"\r" {
            out.push(b"\n".to_vec());
        } else if comment {
            for _ in 0..line_breaks(tok) {
                out.push(b"\n".to_vec());
            }
        } else {
            out.push(tok.to_vec());
        }
        i = e;
    }
    Ok(out)
}

const JASS_KEYWORDS: &[&[u8]] = &[
    b"if", b"elseif", b"not", b"and", b"or", b"return", b"exitwhen", b"then", b"else", b"set", b"call", b"while",
    b"until", b"do", b"local", b"in",
];
const LUA_KEYWORDS: &[&[u8]] = &[
    b"and", b"break", b"do", b"else", b"elseif", b"end", b"false", b"for", b"function", b"goto", b"if", b"in",
    b"local", b"nil", b"not", b"or", b"repeat", b"return", b"then", b"true", b"until", b"while",
];
const LUA_STATEMENT: &[&[u8]] = &[
    b"if", b"while", b"for", b"return", b"local", b"function", b"repeat", b"break", b"end", b"else", b"elseif",
    b"until", b"goto",
];

fn among(t: &[u8], set: &[&[u8]]) -> bool {
    set.iter().any(|s| *s == t)
}

fn is_word(t: &[u8]) -> bool {
    !t.is_empty() && is_word_b(t[0])
}

fn is_string(t: &[u8]) -> bool {
    match t.first() {
        Some(b'"') => true,
        Some(b'\'') => t.len() > 1,
        Some(b'[') => {
            let mut k = 1;
            while k < t.len() && t[k] == b'=' {
                k += 1;
            }
            k < t.len() && t[k] == b'['
        }
        _ => false,
    }
}

fn norm_literal(t: &[u8]) -> Vec<u8> {
    match t.first() {
        Some(b'\'') => {
            if t.len() == 6 && t[5] == b'\'' && t[1..5].iter().all(|c| c.is_ascii_alphanumeric()) && !t[1].is_ascii_digit()
            {
                t[1..5].to_vec()
            } else {
                t.to_vec()
            }
        }
        Some(b'$') => {
            let mut v = b"0x".to_vec();
            v.extend_from_slice(&t[1..]);
            v
        }
        Some(&c) if (c.is_ascii_digit() || c == b'.') && t.contains(&b'.') && t != b"." => {
            let a = digits(t, 0);
            if a < t.len() && t[a] == b'.' {
                let b = digits(t, a + 1);
                let end_ok = b == t.len() || (b + 1 == t.len() && t[b] == b'\n');
                if end_ok {
                    let mut v = if a == 0 { b"0".to_vec() } else { t[..a].to_vec() };
                    v.push(b'.');
                    let mut frac = &t[a + 1..b];
                    while let Some((&b'0', rest)) = frac.split_last().map(|(l, r)| (l, r)) {
                        frac = rest;
                    }
                    v.extend_from_slice(frac);
                    return v;
                }
            }
            t.to_vec()
        }
        _ => t.to_vec(),
    }
}

fn close(toks: &[Tok], i: usize, open: &[u8], cl: &[u8]) -> isize {
    let mut depth = 0i64;
    for j in i..toks.len() {
        if toks[j] == open {
            depth += 1;
        } else if toks[j] == cl {
            depth -= 1;
            if depth == 0 {
                return j as isize;
            }
        }
    }
    -1
}

fn is_atom(ts: &[Tok]) -> bool {
    if ts.len() == 1 {
        let t = &ts[0][..];
        return !(t == b"not" || t == b"-" || t == b"#" || t == b"\n")
            && (is_word(t) || is_string(t) || t.is_empty() || t[0] == b'.' || t[0] == b'$');
    }
    ts.len() >= 4
        && is_word(&ts[0])
        && !ts[0][0].is_ascii_digit()
        && ts[1] == b"["
        && close(ts, 1, b"[", b"]") == ts.len() as isize - 1
}

fn call_paren(toks: &[Tok], i: usize) -> bool {
    let prev: &[u8] = if i > 0 { &toks[i - 1] } else { b"" };
    (is_word(prev) && !among(prev, JASS_KEYWORDS)) || prev == b")" || prev == b"]"
}

fn strip_parens(toks: &mut Vec<Tok>) {
    let mut i = 0;
    while i < toks.len() {
        if toks[i] == b"(" {
            let j = close(toks, i, b"(", b")");
            if j > 0 {
                let j = j as usize;
                let inner = &toks[i + 1..j];
                if !inner.is_empty() && inner[0] == b"(" && close(inner, 0, b"(", b")") == inner.len() as isize - 1 {
                    toks.remove(j - 1);
                    toks.remove(i + 1);
                    continue;
                }
                if !inner.is_empty() && !call_paren(toks, i) && is_atom(inner) {
                    toks.remove(j);
                    toks.remove(i);
                    i = i.saturating_sub(1);
                    continue;
                }
            }
        }
        i += 1;
    }
}

fn ends_expression(t: &[u8]) -> bool {
    t == b")" || t == b"]" || t == b"}" || t == b"nil" || t == b"true" || t == b"false" || t == b"end" || is_string(t)
        || (is_word(t) && !among(t, LUA_KEYWORDS))
}

fn statement_ends(toks: &[Tok], k: usize, lang: Lang) -> bool {
    if k >= toks.len() || toks[k] == b"\n" || toks[k] == b";" {
        return true;
    }
    let t = &toks[k][..];
    lang == Lang::Lua && (among(t, LUA_STATEMENT) || (is_word(t) && !t[0].is_ascii_digit() && !among(t, LUA_KEYWORDS)))
}

fn strip_right_sides(toks: &mut Vec<Tok>, lang: Lang) {
    let mut i = 1;
    while i < toks.len() {
        if toks[i] == b"(" && (toks[i - 1] == b"=" || toks[i - 1] == b"return") {
            let j = close(toks, i, b"(", b")");
            if j > 0 && statement_ends(toks, j as usize + 1, lang) {
                toks.remove(j as usize);
                toks.remove(i);
                continue;
            }
        }
        i += 1;
    }
}

fn lines(toks: Vec<Tok>) -> Vec<Vec<Tok>> {
    let mut out = Vec::new();
    let mut cur = Vec::new();
    for t in toks {
        if t == b"\n" || t == b";" {
            if !cur.is_empty() {
                out.push(std::mem::take(&mut cur));
            }
        } else {
            cur.push(t);
        }
    }
    if !cur.is_empty() {
        out.push(cur);
    }
    out
}

fn lua_lines(toks: Vec<Tok>) -> Vec<Vec<Tok>> {
    let mut out: Vec<Vec<Tok>> = Vec::new();
    let mut cur: Vec<Tok> = Vec::new();
    for t in toks {
        if t == b"\n" || t == b";" {
            continue;
        }
        if !cur.is_empty()
            && (among(&t, LUA_STATEMENT)
                || (is_word(&t) && !t[0].is_ascii_digit() && !among(&t, LUA_KEYWORDS)
                    && ends_expression(cur.last().unwrap())))
        {
            out.push(std::mem::take(&mut cur));
        }
        let brk = t == b"then" || t == b"do" || t == b"else";
        cur.push(t);
        if brk {
            out.push(std::mem::take(&mut cur));
        }
    }
    if !cur.is_empty() {
        out.push(cur);
    }
    out
}

fn join(toks: &[Tok], out: &mut Vec<u8>) {
    let mut word = false;
    for t in toks {
        if word && !t.is_empty() && is_word_b(t[0]) {
            out.push(b' ');
        }
        out.extend_from_slice(t);
        word = !t.is_empty() && is_word_b(*t.last().unwrap());
    }
}

fn block_end(toks: &[Tok], i: usize, lang: Lang) -> isize {
    if lang == Lang::Jass {
        for j in i + 1..toks.len() {
            if toks[j] == b"endfunction" {
                return j as isize + 1;
            }
            if toks[j] == b"function" && toks[j - 1] == b"\n" {
                return -1;
            }
        }
        return -1;
    }
    let mut depth = 0i64;
    for j in i..toks.len() {
        let t = &toks[j][..];
        if t == b"function" || t == b"if" || t == b"do" || t == b"repeat" {
            depth += 1;
        } else if t == b"end" || t == b"until" {
            depth -= 1;
            if depth == 0 {
                return j as isize + 1;
            }
        }
    }
    -1
}

fn function_spans(toks: &[Tok], lang: Lang) -> Vec<(Tok, usize, usize)> {
    let mut spans = Vec::new();
    let n = toks.len();
    let mut i = 0;
    let follow: &[u8] = if lang == Lang::Jass { b"takes" } else { b"(" };
    while i < n {
        let j = if (toks[i] == b"constant" || toks[i] == b"local") && i + 1 < n && toks[i + 1] == b"function" {
            i + 1
        } else {
            i
        };
        if toks[j] == b"function" && j + 2 < n && is_word(&toks[j + 1]) && toks[j + 2] == follow {
            let end = block_end(toks, j, lang);
            if end < 0 {
                break;
            }
            spans.push((toks[j + 1].clone(), i, end as usize));
            i = end as usize;
            continue;
        }
        i += 1;
    }
    spans
}

fn simple_expr(body: &[Tok], lang: Lang) -> Option<Vec<Tok>> {
    let mut b: Vec<&Tok> = body.iter().filter(|t| t.as_slice() != b"\n").collect();
    if b.first().map(|t| t.as_slice() == b"constant").unwrap_or(false) {
        b.remove(0);
    }
    let eq = |k: usize, s: &[u8]| -> bool { b.get(k).map(|t| t.as_slice() == s).unwrap_or(false) };
    let expr: Vec<Tok>;
    if lang == Lang::Jass {
        if !(b.len() >= 6 && eq(2, b"takes") && eq(3, b"nothing") && eq(4, b"returns") && eq(5, b"boolean")) {
            return None;
        }
        if b.last().map(|t| t.as_slice()) != Some(b"endfunction") || !eq(6, b"return") {
            return None;
        }
        if b.len() < 8 {
            return None;
        }
        expr = b[7..b.len() - 1].iter().map(|t| (*t).clone()).collect();
    } else {
        if !(eq(2, b"(") && eq(3, b")")) || !eq(4, b"return") || b.last().map(|t| t.as_slice()) != Some(b"end") {
            return None;
        }
        if b.len() < 6 {
            return None;
        }
        let mut e: Vec<Tok> = b[5..b.len() - 1].iter().map(|t| (*t).clone()).collect();
        if e.last().map(|t| t.as_slice()) == Some(b";") {
            e.pop();
        }
        expr = e;
    }
    let stmt: &[&[u8]] = &[b"return", b"end", b"local", b"set", b"call", b"if", b"loop"];
    if expr.is_empty() || expr.iter().any(|t| among(t, stmt) || (lang == Lang::Lua && t == b"function")) {
        return None;
    }
    Some(expr)
}

fn inline_simple(toks: Vec<Tok>, lang: Lang) -> Vec<Tok> {
    let spans = function_spans(&toks, lang);
    let mut order: Vec<Tok> = Vec::new();
    let mut simple: HashMap<Tok, Vec<Tok>> = HashMap::new();
    let mut headers: HashSet<usize> = HashSet::new();
    for (name, s, e) in &spans {
        headers.insert(if toks[*s] == b"function" { s + 1 } else { s + 2 });
        if let Some(ex) = simple_expr(&toks[*s..*e], lang) {
            if !simple.contains_key(name) {
                order.push(name.clone());
            }
            simple.insert(name.clone(), ex);
        }
    }
    if simple.is_empty() {
        return toks;
    }
    let subst = |seq: &[Tok], offset: Option<usize>, simple: &HashMap<Tok, Vec<Tok>>| -> Vec<Tok> {
        let mut out = Vec::with_capacity(seq.len());
        let mut i = 0;
        while i < seq.len() {
            let t = &seq[i];
            if let Some(ex) = simple.get(t) {
                if i + 2 < seq.len() + 0 && seq[i + 1] == b"(" && seq[i + 2] == b")"
                    && !(i > 0 && seq[i - 1] == b"function")
                    && offset.map(|o| !headers.contains(&(o + i))).unwrap_or(true)
                {
                    if ex[0] == b"(" && close(ex, 0, b"(", b")") == ex.len() as isize - 1 {
                        out.extend(ex.iter().cloned());
                    } else {
                        out.push(b"(".to_vec());
                        out.extend(ex.iter().cloned());
                        out.push(b")".to_vec());
                    }
                    i += 3;
                    continue;
                }
            }
            out.push(t.clone());
            i += 1;
        }
        out
    };
    for _ in 0..8 {
        let mut new: HashMap<Tok, Vec<Tok>> = HashMap::new();
        for name in &order {
            new.insert(name.clone(), subst(&simple[name], None, &simple));
        }
        if new == simple {
            break;
        }
        simple = new;
    }
    let mut valued: HashSet<Tok> = HashSet::new();
    let mut called: HashSet<Tok> = HashSet::new();
    for (i, t) in toks.iter().enumerate() {
        if simple.contains_key(t) && !headers.contains(&i) {
            let prev_fn = i > 0 && toks[i - 1] == b"function";
            let next_paren = i + 1 < toks.len() && toks[i + 1] == b"(";
            if lang == Lang::Jass && prev_fn {
                valued.insert(t.clone());
            } else if lang == Lang::Lua && !next_paren && !prev_fn {
                valued.insert(t.clone());
            } else if i + 2 < toks.len() && toks[i + 1] == b"(" && toks[i + 2] == b")" {
                called.insert(t.clone());
            }
        }
    }
    let mut out = Vec::with_capacity(toks.len());
    let mut pos = 0;
    for (name, s, e) in &spans {
        out.extend(subst(&toks[pos..*s], Some(pos), &simple));
        if !simple.contains_key(name) || valued.contains(name) || !called.contains(name) {
            out.extend(subst(&toks[*s..*e], Some(*s), &simple));
        }
        pos = *e;
    }
    out.extend(subst(&toks[pos..], Some(pos), &simple));
    out
}

fn self_trigger(toks: &[Tok]) -> Option<Tok> {
    for i in 0..toks.len() {
        if toks[i] == b"function" && i + 1 < toks.len() && toks[i + 1].starts_with(b"InitTrig_") {
            return Some(toks[i + 1][9..].to_vec());
        }
    }
    for i in 0..toks.len() {
        if toks[i].starts_with(b"gg_trg_") && i + 2 < toks.len() && toks[i + 1] == b"=" && toks[i + 2] == b"CreateTrigger"
        {
            return Some(toks[i][7..].to_vec());
        }
    }
    None
}

thread_local! {
    static INJECTED: std::cell::RefCell<Option<Re>> = const { std::cell::RefCell::new(None) };
}

fn reparen(toks: &[Tok], lang: Lang, inline: bool) -> Result<Option<Vec<Tok>>, ()> {
    let joined = toks.join(&b' ');
    let injected = INJECTED.with(|c| c.borrow_mut().take());
    let r = if let Some(r) = injected {
        r
    } else if lang == Lang::Lua {
        crate::canon_lua::reparen_re(&joined)
    } else {
        crate::canon_jass::reparen_re(&joined, inline)
    };
    match r {
        Re::Text(t) => Ok(Some(tokens(&t, lang == Lang::Lua)?)),
        Re::NoParse => Ok(None),
        Re::Refuse => Err(()),
    }
}

pub fn canonical(text: &[u8], lua: bool, inline: bool, self_name: Option<&[u8]>) -> Result<Vec<u8>, ()> {
    let lang = if lua { Lang::Lua } else { Lang::Jass };
    let mut toks = tokens(text, lua)?;
    let mut tree = if lang == Lang::Jass { reparen(&toks, lang, inline)? } else { None };
    if tree.is_none() && inline {
        toks = inline_simple(toks, lang);
    }
    if lang == Lang::Lua {
        tree = reparen(&toks, lang, false)?;
    }
    let me: Option<Tok> = match self_name {
        Some(s) => Some(s.to_vec()),
        None => self_trigger(&toks),
    };
    let own: Option<Tok> = match me {
        Some(s) if !s.is_empty() => {
            let mut v = b"gg_trg_".to_vec();
            v.extend_from_slice(&s);
            Some(v)
        }
        _ => None,
    };
    let from_tree = tree.is_some();
    let src = tree.unwrap_or(toks);
    let mut names: HashMap<Tok, Tok> = HashMap::new();
    let mut out: Vec<Tok> = Vec::with_capacity(src.len());
    for t in src {
        if (t.starts_with(b"Trig_") || t.starts_with(b"InitTrig_")) && is_word(&t) {
            let k = names.len() + 1;
            let v = names.entry(t).or_insert_with(|| format!("F{}", k).into_bytes()).clone();
            out.push(v);
        } else if own.as_ref().map(|o| *o == t).unwrap_or(false) {
            out.push(b"gg_trg_SELF".to_vec());
        } else {
            out.push(norm_literal(&t));
        }
    }
    if !from_tree {
        strip_right_sides(&mut out, lang);
        strip_parens(&mut out);
    }
    let ls = if lang == Lang::Lua { lua_lines(out) } else { lines(out) };
    let mut res = Vec::new();
    for (k, l) in ls.iter().enumerate() {
        if k > 0 {
            res.push(b'\n');
        }
        join(l, &mut res);
    }
    Ok(res)
}

type Job = Box<dyn FnOnce() + Send>;
static WORKER: std::sync::Mutex<Option<std::sync::mpsc::Sender<Job>>> = std::sync::Mutex::new(None);

pub fn on_big_stack<R: Send + 'static>(f: impl FnOnce() -> R + Send + 'static) -> Option<R> {
    let (tx, rx) = std::sync::mpsc::sync_channel::<Option<R>>(1);
    let job: Job = Box::new(move || {
        let r = panic::catch_unwind(panic::AssertUnwindSafe(f)).ok();
        let _ = tx.send(r);
    });
    {
        let mut w = WORKER.lock().unwrap_or_else(|e| e.into_inner());
        if w.is_none() {
            let (s, r) = std::sync::mpsc::channel::<Job>();
            let ok = std::thread::Builder::new().stack_size(512 << 20).spawn(move || {
                while let Ok(job) = r.recv() {
                    job();
                }
            });
            if ok.is_err() {
                return None;
            }
            *w = Some(s);
        }
        if w.as_ref().unwrap().send(job).is_err() {
            *w = None;
            return None;
        }
    }
    rx.recv().ok().flatten()
}

fn give(v: Vec<u8>, out: *mut *mut u8, out_len: *mut usize) {
    let mut b = v.into_boxed_slice();
    unsafe {
        *out_len = b.len();
        *out = b.as_mut_ptr();
    }
    std::mem::forget(b);
}

#[no_mangle]
pub extern "C" fn gui_canonical(text: *const u8, len: usize, lang: i32, inline: i32, self_name: *const u8,
                                self_len: usize, out: *mut *mut u8, out_len: *mut usize) -> i32 {
    run(text, len, lang, inline, self_name, self_len, None, out, out_len)
}

#[no_mangle]
pub extern "C" fn gui_canonical_test(text: *const u8, len: usize, lang: i32, inline: i32, self_name: *const u8,
                                     self_len: usize, rp: *const u8, rp_len: usize, state: i32, out: *mut *mut u8,
                                     out_len: *mut usize) -> i32 {
    let inj = if state == 0 && !rp.is_null() {
        Re::Text(unsafe { std::slice::from_raw_parts(rp, rp_len) }.to_vec())
    } else {
        Re::NoParse
    };
    run(text, len, lang, inline, self_name, self_len, Some(inj), out, out_len)
}

#[allow(clippy::too_many_arguments)]
fn run(text: *const u8, len: usize, lang: i32, inline: i32, self_name: *const u8, self_len: usize, inj: Option<Re>,
       out: *mut *mut u8, out_len: *mut usize) -> i32 {
    if text.is_null() || out.is_null() || out_len.is_null() {
        return 3;
    }
    let data: Vec<u8> = unsafe { std::slice::from_raw_parts(text, len) }.to_vec();
    let me: Option<Vec<u8>> = if self_name.is_null() {
        None
    } else {
        Some(unsafe { std::slice::from_raw_parts(self_name, self_len) }.to_vec())
    };
    if lang == 0 && !crate::canon_jass::reference_ready() {
        return 2;
    }
    let r = on_big_stack(move || {
        INJECTED.with(|c| *c.borrow_mut() = inj);
        canonical(&data, lang == 1, inline != 0, me.as_deref())
    });
    match r {
        Some(Ok(v)) => {
            give(v, out, out_len);
            0
        }
        Some(Err(())) => 4,
        None => 3,
    }
}
