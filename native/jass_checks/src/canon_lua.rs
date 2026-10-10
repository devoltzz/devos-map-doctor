// The Lua parser and its parentheses in Rust.
use std::collections::HashMap;
use std::hash::{BuildHasherDefault, Hasher};
use std::panic;

#[derive(Default)]
struct Fx(u64);

impl Hasher for Fx {
    fn finish(&self) -> u64 {
        self.0
    }
    fn write(&mut self, bytes: &[u8]) {
        let mut h = self.0;
        let mut c = bytes.chunks_exact(8);
        for w in &mut c {
            h = (h.rotate_left(5) ^ u64::from_le_bytes(w.try_into().unwrap())).wrapping_mul(0x517cc1b727220a95);
        }
        for &b in c.remainder() {
            h = (h.rotate_left(5) ^ b as u64).wrapping_mul(0x517cc1b727220a95);
        }
        self.0 = h;
    }
    fn write_u32(&mut self, i: u32) {
        self.0 = (self.0.rotate_left(5) ^ i as u64).wrapping_mul(0x517cc1b727220a95);
    }
    fn write_usize(&mut self, i: usize) {
        self.0 = (self.0.rotate_left(5) ^ i as u64).wrapping_mul(0x517cc1b727220a95);
    }
}

type FxMap<K, V> = HashMap<K, V, BuildHasherDefault<Fx>>;

pub(crate) struct Strs {
    list: Vec<Vec<u8>>,
    map: FxMap<Vec<u8>, u32>,
}

impl Strs {
    pub(crate) fn new() -> Strs {
        Strs { list: Vec::new(), map: FxMap::default() }
    }
    fn intern(&mut self, s: &[u8]) -> u32 {
        if let Some(&k) = self.map.get(s) {
            return k;
        }
        let k = self.list.len() as u32;
        self.list.push(s.to_vec());
        self.map.insert(s.to_vec(), k);
        k
    }
    pub(crate) fn get(&self, k: u32) -> &[u8] {
        &self.list[k as usize]
    }
}

#[derive(Debug)]
pub(crate) enum Fail {
    Syntax,
    Refuse,
}

pub(crate) type R<T> = Result<T, Fail>;

fn push_cp(out: &mut Vec<u8>, cp: u32) {
    if cp < 0x80 {
        out.push(cp as u8);
    } else if cp < 0x800 {
        out.push(0xC0 | (cp >> 6) as u8);
        out.push(0x80 | (cp & 0x3F) as u8);
    } else if cp < 0x10000 {
        out.push(0xE0 | (cp >> 12) as u8);
        out.push(0x80 | ((cp >> 6) & 0x3F) as u8);
        out.push(0x80 | (cp & 0x3F) as u8);
    } else {
        out.push(0xF0 | (cp >> 18) as u8);
        out.push(0x80 | ((cp >> 12) & 0x3F) as u8);
        out.push(0x80 | ((cp >> 6) & 0x3F) as u8);
        out.push(0x80 | (cp & 0x3F) as u8);
    }
}

fn raw_to_wtf(raw: &[u8], out: &mut Vec<u8>) {
    let mut rest = raw;
    loop {
        match std::str::from_utf8(rest) {
            Ok(s) => {
                out.extend_from_slice(s.as_bytes());
                return;
            }
            Err(e) => {
                let v = e.valid_up_to();
                out.extend_from_slice(&rest[..v]);
                let bad = e.error_len().unwrap_or(rest.len() - v);
                for &b in &rest[v..v + bad] {
                    push_cp(out, 0xDC00 + b as u32);
                }
                rest = &rest[v + bad..];
            }
        }
    }
}

fn wtf_to_raw(w: &[u8], out: &mut Vec<u8>) -> R<()> {
    let mut i = 0;
    let n = w.len();
    while i < n {
        let b = w[i];
        if b == 0xED && i + 2 < n && w[i + 1] >= 0xA0 {
            let cp = 0xD000 | ((w[i + 1] as u32 & 0x3F) << 6) | (w[i + 2] as u32 & 0x3F);
            if !(0xDC80..=0xDCFF).contains(&cp) {
                return Err(Fail::Refuse);
            }
            out.push((cp - 0xDC00) as u8);
            i += 3;
        } else {
            out.push(b);
            i += 1;
        }
    }
    Ok(())
}

fn char_len(s: &[u8]) -> u32 {
    s.iter().filter(|&&b| b & 0xC0 != 0x80).count() as u32
}

pub(crate) const NAME: u8 = 0;
pub(crate) const NUMBER: u8 = 1;
pub(crate) const STRING: u8 = 2;
pub(crate) const EOF: u8 = 3;
pub(crate) const K_AND: u8 = 4;
const K_BREAK: u8 = 5;
const K_DO: u8 = 6;
const K_ELSE: u8 = 7;
const K_ELSEIF: u8 = 8;
const K_END: u8 = 9;
const K_FALSE: u8 = 10;
const K_FOR: u8 = 11;
const K_FUNCTION: u8 = 12;
const K_GOTO: u8 = 13;
const K_IF: u8 = 14;
const K_IN: u8 = 15;
const K_LOCAL: u8 = 16;
const K_NIL: u8 = 17;
const K_NOT: u8 = 18;
const K_OR: u8 = 19;
const K_REPEAT: u8 = 20;
const K_RETURN: u8 = 21;
const K_THEN: u8 = 22;
const K_TRUE: u8 = 23;
const K_UNTIL: u8 = 24;
const K_WHILE: u8 = 25;
const O_ADD: u8 = 26;
const O_SUB: u8 = 27;
const O_MUL: u8 = 28;
const O_DIV: u8 = 29;
const O_IDIV: u8 = 30;
const O_MOD: u8 = 31;
const O_POW: u8 = 32;
const O_LEN: u8 = 33;
const O_BAND: u8 = 34;
const O_BXOR: u8 = 35;
const O_BOR: u8 = 36;
const O_SHL: u8 = 37;
const O_SHR: u8 = 38;
const O_EQ: u8 = 39;
const O_NE: u8 = 40;
const O_LE: u8 = 41;
const O_GE: u8 = 42;
const O_LT: u8 = 43;
const O_GT: u8 = 44;
const O_ASSIGN: u8 = 45;
const O_LPAREN: u8 = 46;
const O_RPAREN: u8 = 47;
const O_LBRACE: u8 = 48;
const O_RBRACE: u8 = 49;
const O_LBRACKET: u8 = 50;
const O_RBRACKET: u8 = 51;
const O_DBCOLON: u8 = 52;
const O_SEMI: u8 = 53;
const O_COLON: u8 = 54;
const O_COMMA: u8 = 55;
const O_DOT: u8 = 56;
const O_CONCAT: u8 = 57;
const O_DOTS: u8 = 58;

const KIND_TEXT: [&str; 55] = [
    "and", "break", "do", "else", "elseif", "end", "false", "for", "function", "goto", "if", "in", "local", "nil",
    "not", "or", "repeat", "return", "then", "true", "until", "while", "+", "-", "*", "/", "//", "%", "^", "#", "&",
    "~", "|", "<<", ">>", "==", "~=", "<=", ">=", "<", ">", "=", "(", ")", "{", "}", "[", "]", "::", ";", ":", ",",
    ".", "..", "...",
];

pub(crate) fn kind_text(k: u8) -> &'static str {
    KIND_TEXT[(k - K_AND) as usize]
}

fn keyword(s: &[u8]) -> u8 {
    match s {
        b"and" => K_AND,
        b"break" => K_BREAK,
        b"do" => K_DO,
        b"else" => K_ELSE,
        b"elseif" => K_ELSEIF,
        b"end" => K_END,
        b"false" => K_FALSE,
        b"for" => K_FOR,
        b"function" => K_FUNCTION,
        b"goto" => K_GOTO,
        b"if" => K_IF,
        b"in" => K_IN,
        b"local" => K_LOCAL,
        b"nil" => K_NIL,
        b"not" => K_NOT,
        b"or" => K_OR,
        b"repeat" => K_REPEAT,
        b"return" => K_RETURN,
        b"then" => K_THEN,
        b"true" => K_TRUE,
        b"until" => K_UNTIL,
        b"while" => K_WHILE,
        _ => NAME,
    }
}

fn binary_priority(k: u8) -> Option<(u8, u8)> {
    Some(match k {
        O_ADD | O_SUB => (10, 10),
        O_MUL | O_MOD | O_DIV | O_IDIV => (11, 11),
        O_POW => (14, 13),
        O_BAND => (6, 6),
        O_BOR => (4, 4),
        O_BXOR => (5, 5),
        O_SHL | O_SHR => (7, 7),
        O_CONCAT => (9, 8),
        O_EQ | O_LT | O_LE | O_NE | O_GT | O_GE => (3, 3),
        K_AND => (2, 2),
        K_OR => (1, 1),
        _ => return None,
    })
}

const UNARY_PRIORITY: u8 = 12;
const LEVEL_LIMIT: u32 = 200;
const MAX_LOCALS: usize = 200;
const MAX_UPVALUES: usize = 255;

#[derive(Clone, Copy)]
pub(crate) struct Tok {
    pub(crate) kind: u8,
    pub(crate) line: u32,
    pub(crate) cpos: u32,
    pub(crate) sym: u32,
    val: u32,
}

#[inline]
fn is_blank(c: u8) -> bool {
    matches!(c, b' ' | b'\t' | b'\n' | b'\r' | 0x0b | 0x0c)
}

#[inline]
fn is_word(c: u8) -> bool {
    c.is_ascii_alphanumeric() || c == b'_'
}

fn nl_count(s: &[u8]) -> u32 {
    let mut n = 0;
    let mut i = 0;
    while i < s.len() {
        let c = s[i];
        if c == b'\n' || c == b'\r' {
            n += 1;
            if i + 1 < s.len() && (s[i + 1] == b'\n' || s[i + 1] == b'\r') && s[i + 1] != c {
                i += 1;
            }
        }
        i += 1;
    }
    n
}

fn opener(src: &[u8], pos: usize) -> Option<usize> {
    let mut j = pos + 1;
    while j < src.len() && src[j] == b'=' {
        j += 1;
    }
    if j < src.len() && src[j] == b'[' {
        Some(j - pos - 1)
    } else {
        None
    }
}

fn long_close(src: &[u8], from: usize, level: usize) -> Option<usize> {
    let mut q = from;
    let n = src.len();
    while q < n {
        let rel = src[q..].iter().position(|&c| c == b']')?;
        q += rel;
        let mut j = q + 1;
        while j < n && j - q - 1 < level && src[j] == b'=' {
            j += 1;
        }
        if j - q - 1 == level && j < n && src[j] == b']' {
            return Some(j + 1);
        }
        q += 1;
    }
    None
}

#[inline]
fn is_hex(c: u8) -> bool {
    c.is_ascii_hexdigit()
}

fn number_ok(s: &[u8]) -> bool {
    let n = s.len();
    let at = |j: usize| if j < n { s[j] } else { 0 };
    if n >= 2 && s[0] == b'0' && (s[1] == b'x' || s[1] == b'X') {
        let mut j = 2;
        let d0 = j;
        while is_hex(at(j)) {
            j += 1;
        }
        if j > d0 {
            if at(j) == b'.' {
                j += 1;
                while is_hex(at(j)) {
                    j += 1;
                }
            }
        } else {
            if at(j) != b'.' {
                return false;
            }
            j += 1;
            let d1 = j;
            while is_hex(at(j)) {
                j += 1;
            }
            if j == d1 {
                return false;
            }
        }
        if at(j) == b'p' || at(j) == b'P' {
            let save = j;
            j += 1;
            if at(j) == b'+' || at(j) == b'-' {
                j += 1;
            }
            let d = j;
            while at(j).is_ascii_digit() {
                j += 1;
            }
            if j == d {
                j = save;
            }
        }
        return j == n;
    }
    let mut j = 0;
    if at(0).is_ascii_digit() {
        while at(j).is_ascii_digit() {
            j += 1;
        }
        if at(j) == b'.' {
            j += 1;
            while at(j).is_ascii_digit() {
                j += 1;
            }
        }
    } else if at(0) == b'.' && at(1).is_ascii_digit() {
        j = 1;
        while at(j).is_ascii_digit() {
            j += 1;
        }
    } else {
        return false;
    }
    if at(j) == b'e' || at(j) == b'E' {
        let save = j;
        j += 1;
        if at(j) == b'+' || at(j) == b'-' {
            j += 1;
        }
        let d = j;
        while at(j).is_ascii_digit() {
            j += 1;
        }
        if j == d {
            j = save;
        }
    }
    j == n
}

fn utf8esc(mut x: u32, out: &mut Vec<u8>) {
    if x < 0x80 {
        out.push(x as u8);
        return;
    }
    let mut buf = Vec::new();
    let mut mfb: u32 = 0x3f;
    loop {
        buf.push((0x80 | (x & 0x3f)) as u8);
        x >>= 6;
        mfb >>= 1;
        if x <= mfb {
            break;
        }
    }
    buf.push(((!mfb << 1) | x) as u8);
    buf.reverse();
    out.extend_from_slice(&buf);
}

fn unescape(body: &[u8]) -> R<Vec<u8>> {
    let mut raw = Vec::with_capacity(body.len());
    let n = body.len();
    let mut pos = 0;
    loop {
        let i = match body[pos..].iter().position(|&c| c == b'\\') {
            Some(r) => pos + r,
            None => break,
        };
        if i + 1 >= n {
            break;
        }
        wtf_to_raw(&body[pos..i], &mut raw)?;
        let c = body[i + 1];
        let mut j = i + 2;
        match c {
            b'a' => raw.push(7),
            b'b' => raw.push(8),
            b'f' => raw.push(12),
            b'n' => raw.push(10),
            b'r' => raw.push(13),
            b't' => raw.push(9),
            b'v' => raw.push(11),
            b'\\' => raw.push(92),
            b'"' => raw.push(34),
            b'\'' => raw.push(39),
            b'\n' | b'\r' => {
                raw.push(10);
                if j < n && (body[j] == b'\n' || body[j] == b'\r') && body[j] != c {
                    j += 1;
                }
            }
            b'x' => {
                for k in [i + 2, i + 3] {
                    if k >= n || !is_hex(body[k]) {
                        return Err(Fail::Syntax);
                    }
                }
                let h = |c: u8| (c as char).to_digit(16).unwrap() as u8;
                raw.push(h(body[i + 2]) * 16 + h(body[i + 3]));
                j = i + 4;
            }
            b'z' => {
                while j < n && is_blank(body[j]) {
                    j += 1;
                }
            }
            b'0'..=b'9' => {
                j = i + 1;
                let mut v: u32 = 0;
                while j < i + 4 && j < n && body[j].is_ascii_digit() {
                    v = v * 10 + (body[j] - b'0') as u32;
                    j += 1;
                }
                if v > 255 {
                    return Err(Fail::Syntax);
                }
                raw.push(v as u8);
            }
            b'u' => {
                if j >= n || body[j] != b'{' {
                    return Err(Fail::Syntax);
                }
                j += 1;
                if j >= n || !is_hex(body[j]) {
                    return Err(Fail::Syntax);
                }
                let mut v: u32 = 0;
                while j < n && is_hex(body[j]) {
                    v = v * 16 + (body[j] as char).to_digit(16).unwrap();
                    if v > 0x10FFFF {
                        return Err(Fail::Syntax);
                    }
                    j += 1;
                }
                if j >= n || body[j] != b'}' {
                    return Err(Fail::Syntax);
                }
                utf8esc(v, &mut raw);
                j += 1;
            }
            _ => return Err(Fail::Syntax),
        }
        pos = j;
    }
    wtf_to_raw(&body[pos..], &mut raw)?;
    let mut out = Vec::with_capacity(raw.len());
    raw_to_wtf(&raw, &mut out);
    Ok(out)
}

fn long_value(text: &[u8]) -> Vec<u8> {
    let level = text[1..].iter().position(|&c| c == b'[').unwrap();
    let mut body = &text[level + 2..text.len() - level - 2];
    if !body.is_empty() && (body[0] == b'\n' || body[0] == b'\r') {
        let c = body[0];
        body = if body.len() > 1 && (body[1] == b'\n' || body[1] == b'\r') && body[1] != c { &body[2..] } else { &body[1..] };
    }
    if !body.contains(&b'\r') {
        return body.to_vec();
    }
    let mut out = Vec::with_capacity(body.len());
    let mut i = 0;
    while i < body.len() {
        let c = body[i];
        if c == b'\n' || c == b'\r' {
            out.push(b'\n');
            if i + 1 < body.len() && (body[i + 1] == b'\n' || body[i + 1] == b'\r') && body[i + 1] != c {
                i += 1;
            }
        } else {
            out.push(c);
        }
        i += 1;
    }
    out
}

pub(crate) struct Lexed {
    pub(crate) toks: Vec<Tok>,
    pub(crate) comments: Vec<(u32, u32)>,
    pub(crate) ctok: Vec<u32>,
}

pub(crate) fn lex(src: &[u8], st: &mut Strs) -> R<Lexed> {
    let n = src.len();
    let mut toks: Vec<Tok> = Vec::with_capacity(n / 5 + 8);
    let mut comments = Vec::new();
    let mut ctok = Vec::new();
    let mut line: u32 = 1;
    let mut pos = 0usize;
    let mut cpos: u32 = 0;
    let ascii = src.is_ascii();
    let clen = |s: &[u8]| if ascii { s.len() as u32 } else { char_len(s) };
    while pos < n {
        let c = src[pos];
        let start = pos;
        if is_blank(c) {
            let mut j = pos + 1;
            while j < n && is_blank(src[j]) {
                j += 1;
            }
            let s = &src[pos..j];
            if s.iter().any(|&b| b == b'\n' || b == b'\r') {
                line += nl_count(s);
            }
            cpos += (j - pos) as u32;
            pos = j;
            continue;
        }
        let kind;
        let mut val = 0u32;
        let end;
        if c.is_ascii_alphabetic() || c == b'_' {
            let mut j = pos + 1;
            while j < n && is_word(src[j]) {
                j += 1;
            }
            kind = keyword(&src[pos..j]);
            end = j;
        } else if c == b'-' && pos + 1 < n && src[pos + 1] == b'-' {
            let mut j = pos + 2;
            let long = if j < n && src[j] == b'[' { opener(src, j) } else { None };
            if let Some(level) = long {
                match long_close(src, j + level + 2, level) {
                    Some(e) => j = e,
                    None => return Err(Fail::Syntax),
                }
            } else {
                while j < n && src[j] != b'\n' && src[j] != b'\r' {
                    j += 1;
                }
            }
            let s = &src[pos..j];
            comments.push((st.intern(s), line));
            ctok.push(toks.len() as u32);
            if long.is_some() {
                line += nl_count(s);
            }
            cpos += clen(s);
            pos = j;
            continue;
        } else if c == b'[' {
            if let Some(level) = opener(src, pos) {
                match long_close(src, pos + level + 2, level) {
                    Some(e) => end = e,
                    None => return Err(Fail::Syntax),
                }
                kind = STRING;
                val = st.intern(&long_value(&src[pos..end]));
            } else {
                if pos + 1 < n && src[pos + 1] == b'=' {
                    return Err(Fail::Syntax);
                }
                kind = O_LBRACKET;
                end = pos + 1;
            }
        } else if c.is_ascii_digit() || (c == b'.' && pos + 1 < n && src[pos + 1].is_ascii_digit()) {
            let mut j;
            if c == b'0' && pos + 1 < n && (src[pos + 1] == b'x' || src[pos + 1] == b'X') {
                j = pos + 2;
                while j < n {
                    let d = src[j];
                    if d == b'p' || d == b'P' {
                        j += 1;
                        if j < n && (src[j] == b'+' || src[j] == b'-') {
                            j += 1;
                        }
                    } else if is_hex(d) || d == b'.' {
                        j += 1;
                    } else {
                        break;
                    }
                }
            } else {
                j = if c == b'.' { pos + 2 } else { pos + 1 };
                while j < n {
                    let d = src[j];
                    if d == b'e' || d == b'E' {
                        j += 1;
                        if j < n && (src[j] == b'+' || src[j] == b'-') {
                            j += 1;
                        }
                    } else if is_hex(d) || d == b'.' {
                        j += 1;
                    } else {
                        break;
                    }
                }
            }
            if !number_ok(&src[pos..j]) {
                return Err(Fail::Syntax);
            }
            kind = NUMBER;
            end = j;
        } else if c == b'"' || c == b'\'' {
            let mut j = pos + 1;
            let mut escapes = false;
            loop {
                if j >= n {
                    return Err(Fail::Syntax);
                }
                let d = src[j];
                if d == c {
                    j += 1;
                    break;
                }
                if d == b'\n' || d == b'\r' {
                    return Err(Fail::Syntax);
                }
                if d == b'\\' {
                    escapes = true;
                    j += 1;
                    if j >= n {
                        return Err(Fail::Syntax);
                    }
                    let e = src[j];
                    if e == b'z' {
                        j += 1;
                        while j < n && is_blank(src[j]) {
                            j += 1;
                        }
                    } else if e == b'\r' || e == b'\n' {
                        j += 1;
                        if j < n && (src[j] == b'\r' || src[j] == b'\n') && src[j] != e {
                            j += 1;
                        }
                    } else {
                        j += 1;
                    }
                    continue;
                }
                j += 1;
            }
            end = j;
            kind = STRING;
            let body = &src[pos + 1..end - 1];
            val = if escapes { st.intern(&unescape(body)?) } else { st.intern(body) };
        } else {
            let at = |k: usize| if k < n { src[k] } else { 0 };
            let (k, l) = match (c, at(pos + 1), at(pos + 2)) {
                (b'.', b'.', b'.') => (O_DOTS, 3),
                (b'.', b'.', _) => (O_CONCAT, 2),
                (b'=', b'=', _) => (O_EQ, 2),
                (b'~', b'=', _) => (O_NE, 2),
                (b'<', b'=', _) => (O_LE, 2),
                (b'>', b'=', _) => (O_GE, 2),
                (b'<', b'<', _) => (O_SHL, 2),
                (b'>', b'>', _) => (O_SHR, 2),
                (b'/', b'/', _) => (O_IDIV, 2),
                (b':', b':', _) => (O_DBCOLON, 2),
                (b'+', _, _) => (O_ADD, 1),
                (b'-', _, _) => (O_SUB, 1),
                (b'*', _, _) => (O_MUL, 1),
                (b'/', _, _) => (O_DIV, 1),
                (b'%', _, _) => (O_MOD, 1),
                (b'^', _, _) => (O_POW, 1),
                (b'#', _, _) => (O_LEN, 1),
                (b'&', _, _) => (O_BAND, 1),
                (b'~', _, _) => (O_BXOR, 1),
                (b'|', _, _) => (O_BOR, 1),
                (b'<', _, _) => (O_LT, 1),
                (b'>', _, _) => (O_GT, 1),
                (b'=', _, _) => (O_ASSIGN, 1),
                (b'(', _, _) => (O_LPAREN, 1),
                (b')', _, _) => (O_RPAREN, 1),
                (b'{', _, _) => (O_LBRACE, 1),
                (b'}', _, _) => (O_RBRACE, 1),
                (b']', _, _) => (O_RBRACKET, 1),
                (b';', _, _) => (O_SEMI, 1),
                (b':', _, _) => (O_COLON, 1),
                (b',', _, _) => (O_COMMA, 1),
                (b'.', _, _) => (O_DOT, 1),
                (0xED, b1, b2) if b1 >= 0xA0 && !(0xDC80..=0xDCFF).contains(&(0xD000 | ((b1 as u32 & 0x3F) << 6) | (b2 as u32 & 0x3F))) => {
                    return Err(Fail::Refuse)
                }
                _ => return Err(Fail::Syntax),
            };
            kind = k;
            end = pos + l;
        }
        let s = &src[start..end];
        let sym = if kind <= STRING { st.intern(s) } else { 0 };
        toks.push(Tok { kind, line, cpos, sym, val });
        cpos += if kind == STRING { clen(s) } else { s.len() as u32 };
        if kind == STRING && s.iter().any(|&b| b == b'\n' || b == b'\r') {
            line += nl_count(s);
        }
        pos = end;
    }
    for _ in 0..3 {
        toks.push(Tok { kind: EOF, line, cpos, sym: 0, val: 0 });
    }
    Ok(Lexed { toks, comments, ctok })
}

enum Key {
    Pos,
    Name(u32),
    Expr(E),
}

struct FuncBody {
    params: Vec<u32>,
    vararg: bool,
    body: Block,
}

enum E {
    Name(u32, u32),
    Str { text: Option<u32>, value: u32, line: u32 },
    Num(u32, u32),
    Nil(u32),
    Bool(bool, u32),
    Vararg(u32),
    Index { base: Box<E>, key: Box<E>, dot: bool, line: u32 },
    Call { func: Box<E>, args: Vec<E>, method: Option<u32>, line: u32 },
    Func(Box<FuncBody>, u32),
    Unary { op: u8, operand: Box<E>, line: u32 },
    Binary { op: u8, left: Box<E>, right: Box<E>, line: u32 },
    Paren(Box<E>, u32),
    Table(Vec<(Key, E)>, u32),
}

impl E {
    fn line(&self) -> u32 {
        match self {
            E::Name(_, l) | E::Num(_, l) | E::Nil(l) | E::Bool(_, l) | E::Vararg(l) | E::Func(_, l) => *l,
            E::Paren(_, l) | E::Table(_, l) => *l,
            E::Str { line, .. } | E::Index { line, .. } | E::Call { line, .. } => *line,
            E::Unary { line, .. } | E::Binary { line, .. } => *line,
        }
    }
}

enum S {
    Local { names: Vec<u32>, attribs: Vec<Option<u32>>, values: Vec<E> },
    Assign { targets: Vec<E>, values: Vec<E> },
    Call(E),
    Function { name: u32, is_local: bool, f: Box<FuncBody> },
    If(Vec<(Option<E>, Block)>),
    While(E, Block),
    NumFor { var: u32, start: E, stop: E, step: Option<E>, body: Block },
    GenFor { names: Vec<u32>, exprs: Vec<E>, body: Block },
    Repeat(Block, E),
    Do(Block),
    Return(Vec<E>),
    Break,
    Goto(u32),
    Label(u32),
}

struct Stmt {
    k: S,
    line: u32,
    span: (u32, u32),
    lead: (u32, u32),
    inner: Vec<u32>,
    comment: Option<u32>,
}

struct Block {
    stmts: Vec<Stmt>,
    end: (u32, u32),
}

fn dismantle(mut es: Vec<E>, mut bs: Vec<Block>) {
    loop {
        if let Some(e) = es.pop() {
            match e {
                E::Index { base, key, .. } => {
                    es.push(*base);
                    es.push(*key);
                }
                E::Call { func, args, .. } => {
                    es.push(*func);
                    es.extend(args);
                }
                E::Func(f, _) => bs.push(f.body),
                E::Unary { operand, .. } => es.push(*operand),
                E::Binary { left, right, .. } => {
                    es.push(*left);
                    es.push(*right);
                }
                E::Paren(i, _) => es.push(*i),
                E::Table(fields, _) => {
                    for (k, v) in fields {
                        if let Key::Expr(x) = k {
                            es.push(x);
                        }
                        es.push(v);
                    }
                }
                _ => {}
            }
            continue;
        }
        if let Some(b) = bs.pop() {
            for s in b.stmts {
                match s.k {
                    S::Local { values, .. } | S::Return(values) => es.extend(values),
                    S::Assign { targets, values } => {
                        es.extend(targets);
                        es.extend(values);
                    }
                    S::Call(e) => es.push(e),
                    S::Function { f, .. } => bs.push(f.body),
                    S::If(br) => {
                        for (c, b) in br {
                            if let Some(c) = c {
                                es.push(c);
                            }
                            bs.push(b);
                        }
                    }
                    S::While(c, b) | S::Repeat(b, c) => {
                        es.push(c);
                        bs.push(b);
                    }
                    S::NumFor { start, stop, step, body, .. } => {
                        es.push(start);
                        es.push(stop);
                        if let Some(x) = step {
                            es.push(x);
                        }
                        bs.push(body);
                    }
                    S::GenFor { exprs, body, .. } => {
                        es.extend(exprs);
                        bs.push(body);
                    }
                    S::Do(b) => bs.push(b),
                    _ => {}
                }
            }
            continue;
        }
        break;
    }
}

fn depth(root: &Block) -> usize {
    enum N<'a> {
        E(&'a E),
        B(&'a Block),
    }
    let mut stack: Vec<(N, usize)> = vec![(N::B(root), 1)];
    let mut max = 0;
    while let Some((n, d)) = stack.pop() {
        max = max.max(d);
        let d = d + 1;
        match n {
            N::E(e) => match e {
                E::Index { base, key, .. } => {
                    stack.push((N::E(base), d));
                    stack.push((N::E(key), d));
                }
                E::Call { func, args, .. } => {
                    stack.push((N::E(func), d));
                    stack.extend(args.iter().map(|a| (N::E(a), d)));
                }
                E::Func(f, _) => stack.push((N::B(&f.body), d)),
                E::Unary { operand, .. } => stack.push((N::E(operand), d)),
                E::Binary { left, right, .. } => {
                    stack.push((N::E(left), d));
                    stack.push((N::E(right), d));
                }
                E::Paren(i, _) => stack.push((N::E(i), d)),
                E::Table(fields, _) => {
                    for (k, v) in fields {
                        if let Key::Expr(x) = k {
                            stack.push((N::E(x), d));
                        }
                        stack.push((N::E(v), d));
                    }
                }
                _ => {}
            },
            N::B(b) => {
                for s in &b.stmts {
                    let d2 = d + 1;
                    max = max.max(d);
                    match &s.k {
                        S::Local { values, .. } | S::Return(values) => {
                            stack.extend(values.iter().map(|x| (N::E(x), d2)))
                        }
                        S::Assign { targets, values } => {
                            stack.extend(targets.iter().map(|x| (N::E(x), d2)));
                            stack.extend(values.iter().map(|x| (N::E(x), d2)));
                        }
                        S::Call(e) => stack.push((N::E(e), d2)),
                        S::Function { f, .. } => stack.push((N::B(&f.body), d2)),
                        S::If(br) => {
                            for (c, b) in br {
                                if let Some(c) = c {
                                    stack.push((N::E(c), d2));
                                }
                                stack.push((N::B(b), d2));
                            }
                        }
                        S::While(c, b) | S::Repeat(b, c) => {
                            stack.push((N::E(c), d2));
                            stack.push((N::B(b), d2));
                        }
                        S::NumFor { start, stop, step, body, .. } => {
                            stack.push((N::E(start), d2));
                            stack.push((N::E(stop), d2));
                            if let Some(x) = step {
                                stack.push((N::E(x), d2));
                            }
                            stack.push((N::B(body), d2));
                        }
                        S::GenFor { exprs, body, .. } => {
                            stack.extend(exprs.iter().map(|x| (N::E(x), d2)));
                            stack.push((N::B(body), d2));
                        }
                        S::Do(b) => stack.push((N::B(b), d2)),
                        _ => {}
                    }
                }
            }
        }
    }
    max
}

#[derive(Clone, Copy, PartialEq)]
enum Var {
    Global,
    Local(Option<u32>),
}

struct FS {
    vararg: bool,
    actvar: Vec<(u32, Option<u32>)>,
    nactive: usize,
    vars: FxMap<u32, Vec<u32>>,
    upvals: FxMap<u32, Option<u32>>,
    blocks: Vec<(usize, bool, usize, usize)>,
    labels: Vec<(u32, u32, usize)>,
    gotos: Vec<(u32, u32, usize)>,
}

impl FS {
    fn new(vararg: bool) -> FS {
        FS {
            vararg,
            actvar: Vec::new(),
            nactive: 0,
            vars: FxMap::default(),
            upvals: FxMap::default(),
            blocks: Vec::new(),
            labels: Vec::new(),
            gotos: Vec::new(),
        }
    }
}

const BREAK_NAME: u32 = u32::MAX;

struct Parser<'a> {
    t: Vec<Tok>,
    i: usize,
    st: &'a mut Strs,
    ncomments: usize,
    ctok: Vec<u32>,
    ci: usize,
    level: u32,
    fss: Vec<FS>,
    inner: Vec<Vec<u32>>,
    pending: Vec<usize>,
    env: u32,
    s_const: u32,
    s_close: u32,
    s_self: u32,
    comment_lines: Vec<u32>,
}

#[inline]
fn block_end(k: u8) -> bool {
    matches!(k, K_ELSE | K_ELSEIF | K_END | K_UNTIL | EOF)
}

impl<'a> Parser<'a> {
    #[inline]
    fn k(&self) -> u8 {
        self.t[self.i].kind
    }
    #[inline]
    fn kat(&self, j: usize) -> u8 {
        self.t[j].kind
    }
    #[inline]
    fn line(&self) -> u32 {
        self.t[self.i].line
    }
    fn fs(&mut self) -> &mut FS {
        self.fss.last_mut().unwrap()
    }

    fn end_line(&self, i: usize) -> u32 {
        let t = &self.t[i];
        if t.kind == STRING {
            let s = self.st.get(t.sym);
            if s.iter().any(|&b| b == b'\n' || b == b'\r') {
                return t.line + nl_count(s);
            }
        }
        t.line
    }

    fn checknext(&mut self, k: u8) -> R<()> {
        if self.k() != k {
            return Err(Fail::Syntax);
        }
        self.i += 1;
        Ok(())
    }

    fn checkname(&mut self) -> R<u32> {
        let t = self.t[self.i];
        if t.kind != NAME {
            return Err(Fail::Syntax);
        }
        self.i += 1;
        Ok(t.sym)
    }

    fn take(&mut self, j: usize) -> (u32, u32) {
        let start = self.ci;
        while self.ci < self.ncomments && self.ctok[self.ci] as usize <= j {
            self.ci += 1;
        }
        (start as u32, (self.ci - start) as u32)
    }

    fn chunk(&mut self) -> R<Block> {
        let mut fs = FS::new(true);
        fs.upvals.insert(self.env, None);
        self.fss.push(fs);
        self.inner.push(Vec::new());
        self.enterblock(false);
        let body = self.statlist()?;
        if self.k() != EOF {
            dismantle(vec![], vec![body]);
            return Err(Fail::Syntax);
        }
        if let Err(e) = self.leaveblock() {
            dismantle(vec![], vec![body]);
            return Err(e);
        }
        Ok(body)
    }

    fn statlist(&mut self) -> R<Block> {
        let mut body = Block { stmts: Vec::new(), end: (0, 0) };
        let r = self.statlist_into(&mut body);
        match r {
            Ok(()) => Ok(body),
            Err(e) => {
                dismantle(vec![], vec![body]);
                Err(e)
            }
        }
    }

    fn statlist_into(&mut self, body: &mut Block) -> R<()> {
        if self.ci < self.ncomments && (self.ctok[self.ci] as usize) < self.i {
            let (a, n) = self.take(self.i - 1);
            self.inner.last_mut().unwrap().extend(a..a + n);
        }
        loop {
            let i = self.i;
            let kind = self.kat(i);
            if !self.pending.is_empty() && kind != O_SEMI && kind != O_DBCOLON {
                self.close_labels(kind)?;
            }
            if block_end(kind) {
                break;
            }
            let depth = 1 + self.pending.len() as u32;
            if kind == O_SEMI {
                if self.level + depth > LEVEL_LIMIT {
                    return Err(Fail::Syntax);
                }
                self.i = i + 1;
                continue;
            }
            let lead = if self.ci < self.ncomments && self.ctok[self.ci] as usize <= i { self.take(i) } else { (0, 0) };
            self.inner.push(Vec::new());
            self.level += depth;
            if self.level > LEVEL_LIMIT {
                return Err(Fail::Syntax);
            }
            let k = self.statement(kind)?;
            self.level -= depth;
            let mut inner = self.inner.pop().unwrap();
            let last = self.i - 1;
            let mut comment = None;
            if self.ci < self.ncomments {
                if self.ctok[self.ci] as usize <= last {
                    let (a, n) = self.take(last);
                    inner.extend(a..a + n);
                }
                if self.ci < self.ncomments {
                    let mut j = self.i;
                    while self.kat(j) == O_SEMI {
                        j += 1;
                    }
                    if self.ctok[self.ci] as usize <= j && self.comment_lines[self.ci] == self.end_line(last) {
                        comment = Some(self.ci as u32);
                        self.ci += 1;
                    }
                }
            }
            let lt = &self.t[last];
            let lend =
                lt.cpos + if lt.kind <= STRING { char_len(self.st.get(lt.sym)) } else { kind_text(lt.kind).len() as u32 };
            body.stmts.push(Stmt { k, line: self.t[i].line, span: (self.t[i].cpos, lend), lead, inner, comment });
            if kind == K_RETURN {
                break;
            }
        }
        if self.ci < self.ncomments && self.ctok[self.ci] as usize <= self.i {
            body.end = self.take(self.i);
        }
        Ok(())
    }

    fn statement(&mut self, kind: u8) -> R<S> {
        match kind {
            K_IF => self.if_stat(),
            K_WHILE => self.while_stat(),
            K_DO => {
                self.i += 1;
                let body = self.block()?;
                if self.k() != K_END {
                    dismantle(vec![], vec![body]);
                    return Err(Fail::Syntax);
                }
                self.i += 1;
                Ok(S::Do(body))
            }
            K_FOR => self.for_stat(),
            K_REPEAT => self.repeat_stat(),
            K_FUNCTION => self.function_stat(),
            K_LOCAL => self.local_stat(),
            O_DBCOLON => self.label_stat(),
            K_RETURN => self.return_stat(),
            K_BREAK => {
                let line = self.line();
                self.i += 1;
                let fs = self.fs();
                let n = fs.nactive;
                fs.gotos.push((BREAK_NAME, line, n));
                Ok(S::Break)
            }
            K_GOTO => {
                let line = self.line();
                self.i += 1;
                let name = self.checkname()?;
                let fs = self.fs();
                let n = fs.nactive;
                fs.gotos.push((name, line, n));
                let gi = fs.gotos.len() - 1;
                self.findlabel(gi)?;
                Ok(S::Goto(name))
            }
            _ => self.exprstat(),
        }
    }

    fn block(&mut self) -> R<Block> {
        self.enterblock(false);
        let body = self.statlist()?;
        if let Err(e) = self.leaveblock() {
            dismantle(vec![], vec![body]);
            return Err(e);
        }
        Ok(body)
    }

    fn enterblock(&mut self, isloop: bool) {
        let fs = self.fs();
        let e = (fs.nactive, isloop, fs.labels.len(), fs.gotos.len());
        fs.blocks.push(e);
    }

    fn leaveblock(&mut self) -> R<()> {
        let (nact, isloop, firstlabel, firstgoto) = *self.fs().blocks.last().unwrap();
        if isloop {
            let n = self.fs().nactive;
            self.findgotos(BREAK_NAME, n)?;
        }
        let fs = self.fs();
        fs.blocks.pop();
        if fs.nactive > nact {
            for idx in (nact..fs.nactive).rev() {
                let name = fs.actvar[idx].0;
                let stack = fs.vars.get_mut(&name).unwrap();
                stack.pop();
                if stack.is_empty() {
                    fs.vars.remove(&name);
                }
            }
            fs.actvar.truncate(nact);
            fs.nactive = nact;
        }
        fs.labels.truncate(firstlabel);
        if fs.gotos.len() > firstgoto {
            if fs.blocks.is_empty() {
                return Err(Fail::Syntax);
            }
            let mut i = firstgoto;
            while i < self.fs().gotos.len() {
                let fs = self.fs();
                if fs.gotos[i].2 > nact {
                    fs.gotos[i].2 = nact;
                }
                if !self.findlabel(i)? {
                    i += 1;
                }
            }
        }
        Ok(())
    }

    fn findlabel(&mut self, gi: usize) -> R<bool> {
        let fs = self.fs();
        let name = fs.gotos[gi].0;
        let first = fs.blocks.last().unwrap().2;
        for k in first..fs.labels.len() {
            if fs.labels[k].0 == name {
                if fs.gotos[gi].2 < fs.labels[k].2 {
                    return Err(Fail::Syntax);
                }
                fs.gotos.remove(gi);
                return Ok(true);
            }
        }
        Ok(false)
    }

    fn findgotos(&mut self, name: u32, nact: usize) -> R<()> {
        let fs = self.fs();
        let mut i = fs.blocks.last().unwrap().3;
        while i < fs.gotos.len() {
            if fs.gotos[i].0 == name {
                if fs.gotos[i].2 < nact {
                    return Err(Fail::Syntax);
                }
                fs.gotos.remove(i);
            } else {
                i += 1;
            }
        }
        Ok(())
    }

    fn new_localvar(&mut self, name: u32) -> R<()> {
        let fs = self.fs();
        if fs.actvar.len() >= MAX_LOCALS {
            return Err(Fail::Syntax);
        }
        fs.actvar.push((name, None));
        Ok(())
    }

    fn adjustlocalvars(&mut self, n: usize) {
        let fs = self.fs();
        for idx in fs.nactive..fs.nactive + n {
            let name = fs.actvar[idx].0;
            fs.vars.entry(name).or_default().push(idx as u32);
        }
        fs.nactive += n;
    }

    fn resolve(&mut self, f: usize, name: u32) -> R<Var> {
        let fs = &self.fss[f];
        if let Some(stack) = fs.vars.get(&name) {
            if let Some(&top) = stack.last() {
                return Ok(Var::Local(fs.actvar[top as usize].1));
            }
        }
        if let Some(&v) = fs.upvals.get(&name) {
            return Ok(Var::Local(v));
        }
        if f == 0 {
            return Ok(Var::Global);
        }
        let v = self.resolve(f - 1, name)?;
        let a = match v {
            Var::Global => return Ok(Var::Global),
            Var::Local(a) => a,
        };
        let fs = &mut self.fss[f];
        if fs.upvals.len() >= MAX_UPVALUES {
            return Err(Fail::Syntax);
        }
        fs.upvals.insert(name, a);
        Ok(v)
    }

    fn singlevar(&mut self, name: u32) -> R<()> {
        let f = self.fss.len() - 1;
        if !self.fss[f].vars.contains_key(&name) && self.resolve(f, name)? == Var::Global {
            self.resolve(f, self.env)?;
        }
        Ok(())
    }

    fn check_assignable(&mut self, name: u32) -> R<()> {
        let fs = self.fss.last().unwrap();
        let var = match fs.vars.get(&name) {
            Some(stack) if !stack.is_empty() => Some(fs.actvar[*stack.last().unwrap() as usize].1),
            _ => fs.upvals.get(&name).copied(),
        };
        if let Some(Some(_)) = var {
            return Err(Fail::Syntax);
        }
        Ok(())
    }

    fn if_stat(&mut self) -> R<S> {
        let mut branches: Vec<(Option<E>, Block)> = Vec::new();
        let r = self.if_branches(&mut branches);
        if let Err(e) = r {
            let mut es = vec![];
            let mut bs = vec![];
            for (c, b) in branches {
                if let Some(c) = c {
                    es.push(c);
                }
                bs.push(b);
            }
            dismantle(es, bs);
            return Err(e);
        }
        Ok(S::If(branches))
    }

    fn if_branches(&mut self, branches: &mut Vec<(Option<E>, Block)>) -> R<()> {
        loop {
            self.i += 1;
            let cond = self.subexpr(0)?;
            if self.k() != K_THEN {
                dismantle(vec![cond], vec![]);
                return Err(Fail::Syntax);
            }
            self.i += 1;
            let b = match self.block() {
                Ok(b) => b,
                Err(e) => {
                    dismantle(vec![cond], vec![]);
                    return Err(e);
                }
            };
            branches.push((Some(cond), b));
            if self.k() != K_ELSEIF {
                break;
            }
        }
        if self.k() == K_ELSE {
            self.i += 1;
            let b = self.block()?;
            branches.push((None, b));
        }
        self.checknext(K_END)
    }

    fn while_stat(&mut self) -> R<S> {
        self.i += 1;
        let cond = self.subexpr(0)?;
        self.enterblock(true);
        if self.k() != K_DO {
            dismantle(vec![cond], vec![]);
            return Err(Fail::Syntax);
        }
        self.i += 1;
        let body = match self.block() {
            Ok(b) => b,
            Err(e) => {
                dismantle(vec![cond], vec![]);
                return Err(e);
            }
        };
        if self.k() != K_END {
            dismantle(vec![cond], vec![body]);
            return Err(Fail::Syntax);
        }
        self.i += 1;
        if let Err(e) = self.leaveblock() {
            dismantle(vec![cond], vec![body]);
            return Err(e);
        }
        Ok(S::While(cond, body))
    }

    fn repeat_stat(&mut self) -> R<S> {
        self.i += 1;
        self.enterblock(true);
        self.enterblock(false);
        let body = self.statlist()?;
        if self.k() != K_UNTIL {
            dismantle(vec![], vec![body]);
            return Err(Fail::Syntax);
        }
        self.i += 1;
        let cond = match self.subexpr(0) {
            Ok(c) => c,
            Err(e) => {
                dismantle(vec![], vec![body]);
                return Err(e);
            }
        };
        let r = self.leaveblock().and_then(|_| self.leaveblock());
        if let Err(e) = r {
            dismantle(vec![cond], vec![body]);
            return Err(e);
        }
        Ok(S::Repeat(body, cond))
    }

    fn for_stat(&mut self) -> R<S> {
        self.i += 1;
        self.enterblock(true);
        let name = self.checkname()?;
        let kind = self.k();
        let mut es: Vec<E> = Vec::new();
        let r = if kind == O_ASSIGN {
            self.for_num(name, &mut es)
        } else if kind == O_COMMA || kind == K_IN {
            self.for_gen(name, &mut es)
        } else {
            Err(Fail::Syntax)
        };
        let stmt = match r {
            Ok(s) => s,
            Err(e) => {
                dismantle(es, vec![]);
                return Err(e);
            }
        };
        let r = self.checknext(K_END).and_then(|_| self.leaveblock());
        if let Err(e) = r {
            dismantle_stmt(stmt);
            return Err(e);
        }
        Ok(stmt)
    }

    fn hidden(&mut self, names: [&[u8]; 3]) -> R<()> {
        for h in names {
            let s = self.st.intern(h);
            self.new_localvar(s)?;
        }
        Ok(())
    }

    fn for_num(&mut self, name: u32, es: &mut Vec<E>) -> R<S> {
        self.hidden([b"(for index)", b"(for limit)", b"(for step)"])?;
        self.new_localvar(name)?;
        self.i += 1;
        es.push(self.subexpr(0)?);
        self.checknext(O_COMMA)?;
        es.push(self.subexpr(0)?);
        let mut has_step = false;
        if self.k() == O_COMMA {
            self.i += 1;
            es.push(self.subexpr(0)?);
            has_step = true;
        }
        let body = self.forbody(1)?;
        let step = if has_step { es.pop() } else { None };
        let stop = es.pop().unwrap();
        let start = es.pop().unwrap();
        Ok(S::NumFor { var: name, start, stop, step, body })
    }

    fn for_gen(&mut self, name: u32, es: &mut Vec<E>) -> R<S> {
        self.hidden([b"(for generator)", b"(for state)", b"(for control)"])?;
        self.new_localvar(name)?;
        let mut names = vec![name];
        while self.k() == O_COMMA {
            self.i += 1;
            let n = self.checkname()?;
            names.push(n);
            self.new_localvar(n)?;
        }
        self.checknext(K_IN)?;
        self.explist_into(es)?;
        let body = self.forbody(names.len())?;
        let exprs = std::mem::take(es);
        Ok(S::GenFor { names, exprs, body })
    }

    fn forbody(&mut self, nvars: usize) -> R<Block> {
        self.adjustlocalvars(3);
        self.checknext(K_DO)?;
        self.enterblock(false);
        self.adjustlocalvars(nvars);
        let body = self.block()?;
        if let Err(e) = self.leaveblock() {
            dismantle(vec![], vec![body]);
            return Err(e);
        }
        Ok(body)
    }

    fn function_stat(&mut self) -> R<S> {
        self.i += 1;
        let name = self.checkname()?;
        self.singlevar(name)?;
        let mut full = self.st.get(name).to_vec();
        let mut is_method = false;
        while self.k() == O_DOT {
            self.i += 1;
            let n = self.checkname()?;
            full.push(b'.');
            full.extend_from_slice(self.st.get(n));
        }
        if self.k() == O_COLON {
            self.i += 1;
            let n = self.checkname()?;
            full.push(b':');
            full.extend_from_slice(self.st.get(n));
            is_method = true;
        }
        let f = self.funcbody(is_method)?;
        let full = self.st.intern(&full);
        if full == name {
            if let Err(e) = self.check_assignable(name) {
                dismantle(vec![], vec![f.body]);
                return Err(e);
            }
        }
        Ok(S::Function { name: full, is_local: false, f: Box::new(f) })
    }

    fn local_stat(&mut self) -> R<S> {
        self.i += 1;
        if self.k() == K_FUNCTION {
            self.i += 1;
            let name = self.checkname()?;
            self.new_localvar(name)?;
            self.adjustlocalvars(1);
            let f = self.funcbody(false)?;
            return Ok(S::Function { name, is_local: true, f: Box::new(f) });
        }
        let mut names = Vec::new();
        let mut attribs = Vec::new();
        let mut close = false;
        loop {
            let name = self.checkname()?;
            self.new_localvar(name)?;
            let mut attrib = None;
            if self.k() == O_LT {
                self.i += 1;
                let a = self.checkname()?;
                self.checknext(O_GT)?;
                if a != self.s_const && a != self.s_close {
                    return Err(Fail::Syntax);
                }
                if a == self.s_close {
                    if close {
                        return Err(Fail::Syntax);
                    }
                    close = true;
                }
                self.fs().actvar.last_mut().unwrap().1 = Some(a);
                attrib = Some(a);
            }
            names.push(name);
            attribs.push(attrib);
            if self.k() != O_COMMA {
                break;
            }
            self.i += 1;
        }
        let mut values = Vec::new();
        if self.k() == O_ASSIGN {
            self.i += 1;
            if let Err(e) = self.explist_into(&mut values) {
                dismantle(values, vec![]);
                return Err(e);
            }
        }
        self.adjustlocalvars(names.len());
        Ok(S::Local { names, attribs, values })
    }

    fn label_stat(&mut self) -> R<S> {
        let line = self.line();
        self.i += 1;
        let name = self.checkname()?;
        let fs = self.fs();
        let first = fs.blocks.last().unwrap().2;
        if fs.labels[first..].iter().any(|lb| lb.0 == name) {
            return Err(Fail::Syntax);
        }
        self.checknext(O_DBCOLON)?;
        let fs = self.fs();
        let n = fs.nactive;
        fs.labels.push((name, line, n));
        let idx = fs.labels.len() - 1;
        self.pending.push(idx);
        Ok(S::Label(name))
    }

    fn close_labels(&mut self, kind: u8) -> R<()> {
        while let Some(idx) = self.pending.pop() {
            let fs = self.fs();
            if matches!(kind, K_ELSE | K_ELSEIF | K_END | EOF) {
                fs.labels[idx].2 = fs.blocks.last().unwrap().0;
            }
            let (name, _, nact) = fs.labels[idx];
            self.findgotos(name, nact)?;
        }
        Ok(())
    }

    fn return_stat(&mut self) -> R<S> {
        self.i += 1;
        let kind = self.k();
        let mut values = Vec::new();
        if !(block_end(kind) || kind == O_SEMI) {
            if let Err(e) = self.explist_into(&mut values) {
                dismantle(values, vec![]);
                return Err(e);
            }
        }
        if self.k() == O_SEMI {
            self.i += 1;
        }
        Ok(S::Return(values))
    }

    fn exprstat(&mut self) -> R<S> {
        let e = self.suffixedexp()?;
        let kind = self.k();
        if kind == O_ASSIGN || kind == O_COMMA {
            let mut targets = vec![e];
            let r = self.assignment(&mut targets);
            match r {
                Ok(values) => Ok(S::Assign { targets, values }),
                Err(x) => {
                    dismantle(targets, vec![]);
                    Err(x)
                }
            }
        } else if matches!(e, E::Call { .. }) {
            Ok(S::Call(e))
        } else {
            dismantle(vec![e], vec![]);
            Err(Fail::Syntax)
        }
    }

    fn assignment(&mut self, targets: &mut Vec<E>) -> R<Vec<E>> {
        self.check_target(0, targets)?;
        while self.k() == O_COMMA {
            self.i += 1;
            let e = self.suffixedexp()?;
            let over = targets.len() as u32 + self.level > LEVEL_LIMIT;
            targets.push(e);
            if over {
                return Err(Fail::Syntax);
            }
            self.check_target(targets.len() - 1, targets)?;
        }
        self.checknext(O_ASSIGN)?;
        let mut values = Vec::new();
        if let Err(x) = self.explist_into(&mut values) {
            dismantle(values, vec![]);
            return Err(x);
        }
        Ok(values)
    }

    fn check_target(&mut self, k: usize, targets: &[E]) -> R<()> {
        match &targets[k] {
            E::Name(n, _) => {
                let n = *n;
                self.check_assignable(n)
            }
            E::Index { .. } => Ok(()),
            _ => Err(Fail::Syntax),
        }
    }

    fn explist_into(&mut self, out: &mut Vec<E>) -> R<()> {
        out.push(self.subexpr(0)?);
        while self.k() == O_COMMA {
            self.i += 1;
            out.push(self.subexpr(0)?);
        }
        Ok(())
    }

    fn subexpr(&mut self, limit: u8) -> R<E> {
        self.level += 1;
        if self.level > LEVEL_LIMIT {
            return Err(Fail::Syntax);
        }
        let i = self.i;
        let kind = self.kat(i);
        let mut e = if matches!(kind, K_NOT | O_SUB | O_LEN | O_BXOR) {
            self.i = i + 1;
            let operand = self.subexpr(UNARY_PRIORITY)?;
            E::Unary { op: kind, operand: Box::new(operand), line: self.t[i].line }
        } else {
            self.simpleexp()?
        };
        loop {
            let op = self.k();
            let p = match binary_priority(op) {
                Some(p) if p.0 > limit => p,
                _ => break,
            };
            self.i += 1;
            let right = match self.subexpr(p.1) {
                Ok(r) => r,
                Err(x) => {
                    dismantle(vec![e], vec![]);
                    return Err(x);
                }
            };
            let line = e.line();
            e = E::Binary { op, left: Box::new(e), right: Box::new(right), line };
        }
        self.level -= 1;
        Ok(e)
    }

    fn simpleexp(&mut self) -> R<E> {
        let i = self.i;
        let t = self.t[i];
        match t.kind {
            NAME | O_LPAREN => self.suffixedexp(),
            NUMBER => {
                self.i = i + 1;
                Ok(E::Num(t.sym, t.line))
            }
            STRING => {
                self.i = i + 1;
                Ok(E::Str { text: Some(t.sym), value: t.val, line: t.line })
            }
            K_NIL => {
                self.i = i + 1;
                Ok(E::Nil(t.line))
            }
            K_TRUE | K_FALSE => {
                self.i = i + 1;
                Ok(E::Bool(t.kind == K_TRUE, t.line))
            }
            O_DOTS => {
                if !self.fss.last().unwrap().vararg {
                    return Err(Fail::Syntax);
                }
                self.i = i + 1;
                Ok(E::Vararg(t.line))
            }
            O_LBRACE => self.table(),
            K_FUNCTION => {
                self.i = i + 1;
                let f = self.funcbody(false)?;
                Ok(E::Func(Box::new(f), t.line))
            }
            _ => self.suffixedexp(),
        }
    }

    fn suffixedexp(&mut self) -> R<E> {
        let i = self.i;
        let t = self.t[i];
        let line = t.line;
        let mut e = match t.kind {
            NAME => {
                self.i = i + 1;
                self.singlevar(t.sym)?;
                E::Name(t.sym, line)
            }
            O_LPAREN => {
                self.i = i + 1;
                let inner = self.subexpr(0)?;
                if self.k() != O_RPAREN {
                    dismantle(vec![inner], vec![]);
                    return Err(Fail::Syntax);
                }
                self.i += 1;
                E::Paren(Box::new(inner), line)
            }
            _ => return Err(Fail::Syntax),
        };
        loop {
            let (x, more) = self.suffix(e, line)?;
            e = x;
            if !more {
                return Ok(e);
            }
        }
    }

    fn suffix(&mut self, e: E, line: u32) -> R<(E, bool)> {
        match self.k() {
            O_DOT => {
                self.i += 1;
                let j = self.i;
                let name = match self.checkname() {
                    Ok(n) => n,
                    Err(x) => {
                        dismantle(vec![e], vec![]);
                        return Err(x);
                    }
                };
                let mut q = Vec::with_capacity(self.st.get(name).len() + 2);
                q.push(b'"');
                q.extend_from_slice(self.st.get(name));
                q.push(b'"');
                let text = self.st.intern(&q);
                let key = E::Str { text: Some(text), value: name, line: self.t[j].line };
                Ok((E::Index { base: Box::new(e), key: Box::new(key), dot: true, line }, true))
            }
            O_LBRACKET => {
                self.i += 1;
                let key = match self.subexpr(0) {
                    Ok(k) => k,
                    Err(x) => {
                        dismantle(vec![e], vec![]);
                        return Err(x);
                    }
                };
                if self.k() != O_RBRACKET {
                    dismantle(vec![e, key], vec![]);
                    return Err(Fail::Syntax);
                }
                self.i += 1;
                Ok((E::Index { base: Box::new(e), key: Box::new(key), dot: false, line }, true))
            }
            O_COLON => {
                self.i += 1;
                let name = match self.checkname() {
                    Ok(n) => n,
                    Err(x) => {
                        dismantle(vec![e], vec![]);
                        return Err(x);
                    }
                };
                let mut args = Vec::new();
                if let Err(x) = self.funcargs(&mut args) {
                    args.push(e);
                    dismantle(args, vec![]);
                    return Err(x);
                }
                Ok((E::Call { func: Box::new(e), args, method: Some(name), line }, true))
            }
            O_LPAREN | STRING | O_LBRACE => {
                let mut args = Vec::new();
                if let Err(x) = self.funcargs(&mut args) {
                    args.push(e);
                    dismantle(args, vec![]);
                    return Err(x);
                }
                Ok((E::Call { func: Box::new(e), args, method: None, line }, true))
            }
            _ => Ok((e, false)),
        }
    }

    fn funcargs(&mut self, args: &mut Vec<E>) -> R<()> {
        let i = self.i;
        let t = self.t[i];
        match t.kind {
            O_LPAREN => {
                self.i = i + 1;
                if self.kat(i + 1) != O_RPAREN {
                    self.explist_into(args)?;
                }
                self.checknext(O_RPAREN)
            }
            STRING => {
                self.i = i + 1;
                args.push(E::Str { text: Some(t.sym), value: t.val, line: t.line });
                Ok(())
            }
            O_LBRACE => {
                args.push(self.table()?);
                Ok(())
            }
            _ => Err(Fail::Syntax),
        }
    }

    fn table(&mut self) -> R<E> {
        let line = self.line();
        self.i += 1;
        let mut fields: Vec<(Key, E)> = Vec::new();
        let r = self.fields(&mut fields);
        if let Err(x) = r {
            dismantle(vec![E::Table(fields, 0)], vec![]);
            return Err(x);
        }
        Ok(E::Table(fields, line))
    }

    fn fields(&mut self, fields: &mut Vec<(Key, E)>) -> R<()> {
        while self.k() != O_RBRACE {
            let kind = self.k();
            if kind == NAME && self.kat(self.i + 1) == O_ASSIGN {
                let name = self.t[self.i].sym;
                self.i += 2;
                let v = self.subexpr(0)?;
                fields.push((Key::Name(name), v));
            } else if kind == O_LBRACKET {
                self.i += 1;
                let key = self.subexpr(0)?;
                if self.k() != O_RBRACKET || self.kat(self.i + 1) != O_ASSIGN {
                    dismantle(vec![key], vec![]);
                    return Err(Fail::Syntax);
                }
                self.i += 2;
                let v = match self.subexpr(0) {
                    Ok(v) => v,
                    Err(x) => {
                        dismantle(vec![key], vec![]);
                        return Err(x);
                    }
                };
                fields.push((Key::Expr(key), v));
            } else {
                let v = self.subexpr(0)?;
                fields.push((Key::Pos, v));
            }
            let kind = self.k();
            if kind != O_COMMA && kind != O_SEMI {
                break;
            }
            self.i += 1;
        }
        self.checknext(O_RBRACE)
    }

    fn funcbody(&mut self, is_method: bool) -> R<FuncBody> {
        self.fss.push(FS::new(false));
        self.enterblock(false);
        if is_method {
            self.new_localvar(self.s_self)?;
            self.adjustlocalvars(1);
        }
        self.checknext(O_LPAREN)?;
        let mut params = Vec::new();
        let mut vararg = false;
        if self.k() != O_RPAREN {
            loop {
                let t = self.t[self.i];
                if t.kind == NAME {
                    params.push(t.sym);
                    self.i += 1;
                    self.new_localvar(t.sym)?;
                } else if t.kind == O_DOTS {
                    self.i += 1;
                    vararg = true;
                } else {
                    return Err(Fail::Syntax);
                }
                if vararg || self.k() != O_COMMA {
                    break;
                }
                self.i += 1;
            }
        }
        self.adjustlocalvars(params.len());
        self.fs().vararg = vararg;
        self.checknext(O_RPAREN)?;
        let body = self.statlist()?;
        let r = self.checknext(K_END).and_then(|_| self.leaveblock());
        if let Err(x) = r {
            dismantle(vec![], vec![body]);
            return Err(x);
        }
        self.fss.pop();
        Ok(FuncBody { params, vararg, body })
    }
}

fn dismantle_stmt(s: S) {
    let st = Stmt { k: s, line: 0, span: (0, 0), lead: (0, 0), inner: vec![], comment: None };
    dismantle(vec![], vec![Block { stmts: vec![st], end: (0, 0) }]);
}

struct Tree {
    body: Block,
    comments: Vec<(u32, u32)>,
}

fn parse(src: &[u8], st: &mut Strs) -> R<Tree> {
    let lx = lex(src, st)?;
    let env = st.intern(b"_ENV");
    let s_const = st.intern(b"const");
    let s_close = st.intern(b"close");
    let s_self = st.intern(b"self");
    let comment_lines: Vec<u32> = lx.comments.iter().map(|c| c.1).collect();
    let mut p = Parser {
        t: lx.toks,
        i: 0,
        st,
        ncomments: lx.comments.len(),
        ctok: lx.ctok,
        ci: 0,
        level: 1,
        fss: Vec::new(),
        inner: Vec::new(),
        pending: Vec::new(),
        env,
        s_const,
        s_close,
        s_self,
        comment_lines,
    };
    let body = p.chunk()?;
    Ok(Tree { body, comments: lx.comments })
}

fn ser_e(o: &mut Vec<i32>, e: &E) {
    match e {
        E::Name(s, l) => o.extend_from_slice(&[0, *s as i32, *l as i32]),
        E::Str { text, value, line } => {
            o.extend_from_slice(&[1, text.map_or(-1, |t| t as i32), *value as i32, *line as i32])
        }
        E::Num(t, l) => o.extend_from_slice(&[2, *t as i32, *l as i32]),
        E::Nil(l) => o.extend_from_slice(&[3, *l as i32]),
        E::Bool(b, l) => o.extend_from_slice(&[if *b { 4 } else { 5 }, *l as i32]),
        E::Vararg(l) => o.extend_from_slice(&[6, *l as i32]),
        E::Index { base, key, dot, line } => {
            ser_e(o, base);
            if let (true, E::Str { text: Some(t), value, line: kl }) = (*dot, &**key) {
                o.extend_from_slice(&[7, *value as i32, *t as i32, *kl as i32, *line as i32]);
            } else {
                ser_e(o, key);
                o.extend_from_slice(&[8, *dot as i32, *line as i32]);
            }
        }
        E::Call { func, args, method, line } => {
            ser_e(o, func);
            for a in args {
                ser_e(o, a);
            }
            match method {
                Some(m) => o.extend_from_slice(&[10, args.len() as i32, *m as i32, *line as i32]),
                None => o.extend_from_slice(&[9, args.len() as i32, *line as i32]),
            }
        }
        E::Func(f, l) => {
            ser_block(o, &f.body);
            o.push(11);
            ser_params(o, f);
            o.push(*l as i32);
        }
        E::Unary { op, operand, line } => {
            ser_e(o, operand);
            o.extend_from_slice(&[12, *op as i32, *line as i32]);
        }
        E::Binary { op, left, right, line } => {
            ser_e(o, left);
            ser_e(o, right);
            o.extend_from_slice(&[13, *op as i32, *line as i32]);
        }
        E::Paren(i, l) => {
            ser_e(o, i);
            o.extend_from_slice(&[14, *l as i32]);
        }
        E::Table(fields, l) => {
            for (k, v) in fields {
                match k {
                    Key::Pos => {
                        ser_e(o, v);
                        o.push(15);
                    }
                    Key::Name(s) => {
                        ser_e(o, v);
                        o.extend_from_slice(&[16, *s as i32]);
                    }
                    Key::Expr(x) => {
                        ser_e(o, x);
                        ser_e(o, v);
                        o.push(17);
                    }
                }
            }
            o.extend_from_slice(&[18, fields.len() as i32, *l as i32]);
        }
    }
}

fn ser_params(o: &mut Vec<i32>, f: &FuncBody) {
    o.push(f.params.len() as i32);
    o.extend(f.params.iter().map(|&p| p as i32));
    o.push(f.vararg as i32);
}

fn ser_block(o: &mut Vec<i32>, b: &Block) {
    for s in &b.stmts {
        ser_stmt(o, s);
    }
    o.extend_from_slice(&[41, b.stmts.len() as i32]);
    if b.end.1 > 0 {
        o.extend_from_slice(&[42, b.end.0 as i32, b.end.1 as i32]);
    }
}

fn ser_stmt(o: &mut Vec<i32>, s: &Stmt) {
    match &s.k {
        S::Local { names, attribs, values } => {
            for v in values {
                ser_e(o, v);
            }
            o.extend_from_slice(&[20, names.len() as i32]);
            for (n, a) in names.iter().zip(attribs) {
                o.extend_from_slice(&[*n as i32, a.map_or(-1, |a| a as i32)]);
            }
            o.push(values.len() as i32);
        }
        S::Assign { targets, values } => {
            for v in targets.iter().chain(values) {
                ser_e(o, v);
            }
            o.extend_from_slice(&[21, targets.len() as i32, values.len() as i32]);
        }
        S::Call(e) => {
            ser_e(o, e);
            o.push(22);
        }
        S::Function { name, is_local, f } => {
            ser_block(o, &f.body);
            o.extend_from_slice(&[23, *name as i32, *is_local as i32]);
            ser_params(o, f);
        }
        S::If(br) => {
            let mut nc = 0;
            let mut has_else = 0;
            for (c, b) in br {
                match c {
                    Some(c) => {
                        ser_e(o, c);
                        nc += 1;
                    }
                    None => has_else = 1,
                }
                ser_block(o, b);
            }
            o.extend_from_slice(&[24, nc, has_else]);
        }
        S::While(c, b) => {
            ser_e(o, c);
            ser_block(o, b);
            o.push(25);
        }
        S::NumFor { var, start, stop, step, body } => {
            ser_e(o, start);
            ser_e(o, stop);
            if let Some(x) = step {
                ser_e(o, x);
            }
            ser_block(o, body);
            o.extend_from_slice(&[26, *var as i32, step.is_some() as i32]);
        }
        S::GenFor { names, exprs, body } => {
            for x in exprs {
                ser_e(o, x);
            }
            ser_block(o, body);
            o.extend_from_slice(&[27, names.len() as i32]);
            o.extend(names.iter().map(|&n| n as i32));
            o.push(exprs.len() as i32);
        }
        S::Repeat(b, c) => {
            ser_block(o, b);
            ser_e(o, c);
            o.push(28);
        }
        S::Do(b) => {
            ser_block(o, b);
            o.push(29);
        }
        S::Return(values) => {
            for v in values {
                ser_e(o, v);
            }
            o.extend_from_slice(&[30, values.len() as i32]);
        }
        S::Break => o.push(31),
        S::Goto(n) => o.extend_from_slice(&[32, *n as i32]),
        S::Label(n) => o.extend_from_slice(&[33, *n as i32]),
    }
    o.extend_from_slice(&[s.line as i32, s.span.0 as i32, s.span.1 as i32]);
    if s.lead.1 > 0 || !s.inner.is_empty() || s.comment.is_some() {
        o.extend_from_slice(&[40, s.lead.0 as i32, s.lead.1 as i32, s.inner.len() as i32]);
        o.extend(s.inner.iter().map(|&c| c as i32));
        o.push(s.comment.map_or(-1, |c| c as i32));
    }
}

fn serialize(tree: &Tree, st: &Strs) -> R<Vec<u8>> {
    let mut seen = [false; 128];
    let mut high = vec![false; 0x400];
    for s in &st.list {
        for (k, &b) in s.iter().enumerate() {
            if b < 128 {
                seen[b as usize] = true;
            } else if b == 0xED && k + 2 < s.len() && (0xA0..=0xAF).contains(&s[k + 1]) {
                high[(((s[k + 1] as usize) & 0x0F) << 6) | (s[k + 2] as usize & 0x3F)] = true;
            }
        }
    }
    let sep: u32 = match (1..128u8).chain(std::iter::once(0u8)).find(|&b| !seen[b as usize]) {
        Some(b) => b as u32,
        None => match (0..0x400).find(|&k| !high[k]) {
            Some(k) => 0xD800 + k as u32,
            None => return Err(Fail::Refuse),
        },
    };
    let mut sep_bytes = Vec::new();
    push_cp(&mut sep_bytes, sep);
    let mut ints: Vec<i32> = Vec::with_capacity(16 + tree.comments.len() * 2);
    ints.push(tree.comments.len() as i32);
    for &(t, l) in &tree.comments {
        ints.push(t as i32);
        ints.push(l as i32);
    }
    ser_block(&mut ints, &tree.body);
    let blob_len: usize =
        st.list.iter().map(|s| s.len()).sum::<usize>() + st.list.len().saturating_sub(1) * sep_bytes.len();
    let pad = (4 - blob_len % 4) % 4;
    let mut out = Vec::with_capacity(16 + blob_len + pad + ints.len() * 4);
    for v in [st.list.len() as u32, sep as u32, blob_len as u32, ints.len() as u32] {
        out.extend_from_slice(&v.to_le_bytes());
    }
    for (k, s) in st.list.iter().enumerate() {
        if k > 0 {
            out.extend_from_slice(&sep_bytes);
        }
        out.extend_from_slice(s);
    }
    out.extend(std::iter::repeat(0u8).take(pad));
    for v in ints {
        out.extend_from_slice(&v.to_le_bytes());
    }
    Ok(out)
}

fn strip_parens(e: E) -> E {
    let mut e = e;
    loop {
        match e {
            E::Paren(i, _) => e = *i,
            x => return x,
        }
    }
}

fn tx_values(vs: Vec<E>, targets: Option<usize>, st: &mut Strs) -> Vec<E> {
    let n = vs.len();
    let mut out = Vec::with_capacity(n);
    for (k, v) in vs.into_iter().enumerate() {
        if k + 1 < n {
            out.push(tx(v, st));
            continue;
        }
        let was_paren = matches!(v, E::Paren(..));
        let inner = strip_parens(v);
        let cuts = matches!(inner, E::Call { .. } | E::Vararg(_));
        let keep = cuts && was_paren && targets.map_or(true, |t| t > n);
        let x = tx(inner, st);
        out.push(if keep { E::Paren(Box::new(x), 0) } else { x });
    }
    out
}

fn tx(e: E, st: &mut Strs) -> E {
    match e {
        E::Paren(i, _) => tx(*i, st),
        E::Binary { op, left, right, .. } => {
            let l = tx(*left, st);
            let r = tx(*right, st);
            if op == O_CONCAT {
                if let (E::Str { text: lt, value: lv, .. }, E::Str { text: rt, value: rv, .. }) = (&l, &r) {
                    let q = |t: &Option<u32>| t.map_or(false, |t| st.get(t).first() == Some(&b'"'));
                    let text = if q(lt) && q(rt) {
                        let (a, b) = (st.get(lt.unwrap()), st.get(rt.unwrap()));
                        let mut s = a[..a.len() - 1].to_vec();
                        s.extend_from_slice(&b[1..]);
                        Some(s)
                    } else {
                        None
                    };
                    let mut v = st.get(*lv).to_vec();
                    v.extend_from_slice(st.get(*rv));
                    let text = text.map(|s| st.intern(&s));
                    let value = st.intern(&v);
                    return E::Str { text, value, line: 0 };
                }
            }
            E::Paren(Box::new(E::Binary { op, left: Box::new(l), right: Box::new(r), line: 0 }), 0)
        }
        E::Unary { op, operand, .. } => E::Unary { op, operand: Box::new(tx(*operand, st)), line: 0 },
        E::Call { func, args, method, .. } => {
            let f = tx(*func, st);
            E::Call { func: Box::new(f), args: tx_values(args, None, st), method, line: 0 }
        }
        E::Index { base, key, dot, .. } => {
            let b = tx(*base, st);
            E::Index { base: Box::new(b), key: Box::new(tx(*key, st)), dot, line: 0 }
        }
        E::Table(fields, line) => {
            let last = fields.iter().rposition(|(k, _)| matches!(k, Key::Pos));
            let fields = fields
                .into_iter()
                .enumerate()
                .map(|(k, (key, v))| {
                    let key = match key {
                        Key::Expr(x) => Key::Expr(tx(x, st)),
                        other => other,
                    };
                    let v = if Some(k) == last { tx_values(vec![v], None, st).pop().unwrap() } else { tx(v, st) };
                    (key, v)
                })
                .collect();
            E::Table(fields, line)
        }
        E::Func(mut f, l) => {
            tx_block(&mut f.body, st);
            E::Func(f, l)
        }
        other => other,
    }
}

fn tx_block(b: &mut Block, st: &mut Strs) {
    for s in b.stmts.iter_mut() {
        let k = std::mem::replace(&mut s.k, S::Break);
        s.k = match k {
            S::Local { names, attribs, values } => {
                let n = names.len();
                S::Local { names, attribs, values: tx_values(values, Some(n), st) }
            }
            S::Assign { targets, values } => {
                let n = targets.len();
                let targets = targets.into_iter().map(|x| tx(x, st)).collect();
                S::Assign { targets, values: tx_values(values, Some(n), st) }
            }
            S::Call(e) => S::Call(tx(e, st)),
            S::Return(values) => S::Return(tx_values(values, None, st)),
            S::If(br) => {
                let mut br: Vec<(Option<E>, Block)> = br.into_iter().map(|(c, b)| (c.map(|c| tx(c, st)), b)).collect();
                for (_, b) in br.iter_mut() {
                    tx_block(b, st);
                }
                S::If(br)
            }
            S::While(c, mut b) => {
                let c = tx(c, st);
                tx_block(&mut b, st);
                S::While(c, b)
            }
            S::Repeat(mut b, c) => {
                let c = tx(c, st);
                tx_block(&mut b, st);
                S::Repeat(b, c)
            }
            S::NumFor { var, start, stop, step, mut body } => {
                let start = tx(start, st);
                let stop = tx(stop, st);
                let step = step.map(|x| tx(x, st));
                tx_block(&mut body, st);
                S::NumFor { var, start, stop, step, body }
            }
            S::GenFor { names, exprs, mut body } => {
                let exprs = tx_values(exprs, Some(3), st);
                tx_block(&mut body, st);
                S::GenFor { names, exprs, body }
            }
            S::Function { name, is_local, mut f } => {
                tx_block(&mut f.body, st);
                S::Function { name, is_local, f }
            }
            S::Do(mut b) => {
                tx_block(&mut b, st);
                S::Do(b)
            }
            other => other,
        };
    }
}

const INDENT: &[u8] = b"    ";

fn is_name(s: &[u8]) -> bool {
    !s.is_empty()
        && (s[0].is_ascii_alphabetic() || s[0] == b'_')
        && s.iter().all(|&c| is_word(c))
        && keyword(s) == NAME
}

fn quote(v: &[u8], out: &mut Vec<u8>) {
    out.push(b'"');
    let mut i = 0;
    while i < v.len() {
        let b = v[i];
        let len = if b < 0x80 { 1 } else if b < 0xE0 { 2 } else if b < 0xF0 { 3 } else { 4 };
        let len = len.min(v.len() - i);
        let cp: u32 = match len {
            1 => b as u32,
            2 => ((b as u32 & 0x1F) << 6) | (v[i + 1] as u32 & 0x3F),
            3 => ((b as u32 & 0x0F) << 12) | ((v[i + 1] as u32 & 0x3F) << 6) | (v[i + 2] as u32 & 0x3F),
            _ => {
                ((b as u32 & 0x07) << 18)
                    | ((v[i + 1] as u32 & 0x3F) << 12)
                    | ((v[i + 2] as u32 & 0x3F) << 6)
                    | (v[i + 3] as u32 & 0x3F)
            }
        };
        if cp == b'"' as u32 || cp == b'\\' as u32 {
            out.push(b'\\');
            out.push(b);
        } else if cp == 10 {
            out.extend_from_slice(b"\\n");
        } else if cp < 32 || cp == 127 {
            out.extend_from_slice(format!("\\{:03}", cp).as_bytes());
        } else if (0xDC80..=0xDCFF).contains(&cp) {
            out.extend_from_slice(format!("\\{:03}", cp - 0xDC00).as_bytes());
        } else {
            out.extend_from_slice(&v[i..i + len]);
        }
        i += len;
    }
    out.push(b'"');
}

fn needs_paren(child: &E, priority: u8, left: bool) -> bool {
    match child {
        E::Binary { op, .. } => {
            let (cl, cr) = binary_priority(*op).unwrap();
            if left {
                priority > cr
            } else {
                cl <= priority
            }
        }
        E::Unary { .. } => left && priority > UNARY_PRIORITY,
        _ => false,
    }
}

fn words(parts: &[&[u8]]) -> Vec<u8> {
    let mut out = Vec::new();
    for p in parts {
        if p.is_empty() {
            continue;
        }
        if !out.is_empty() {
            out.push(b' ');
        }
        out.extend_from_slice(p);
    }
    out
}

fn paren(s: Vec<u8>) -> Vec<u8> {
    let mut p = Vec::with_capacity(s.len() + 2);
    p.push(b'(');
    p.extend(s);
    p.push(b')');
    p
}

struct Printer<'a> {
    st: &'a Strs,
    comments: &'a [(u32, u32)],
    lvl: std::cell::Cell<usize>,
}

impl<'a> Printer<'a> {
    fn exprs(&self, vs: &[E]) -> Vec<u8> {
        let mut out = Vec::new();
        for (k, v) in vs.iter().enumerate() {
            if k > 0 {
                out.extend_from_slice(b", ");
            }
            out.extend(self.expr(v));
        }
        out
    }

    fn expr(&self, e: &E) -> Vec<u8> {
        match e {
            E::Name(s, _) => self.st.get(*s).to_vec(),
            E::Str { text: Some(t), .. } | E::Num(t, _) => self.st.get(*t).to_vec(),
            E::Str { text: None, value, .. } => {
                let mut o = Vec::new();
                quote(self.st.get(*value), &mut o);
                o
            }
            E::Nil(_) => b"nil".to_vec(),
            E::Bool(b, _) => {
                if *b {
                    b"true".to_vec()
                } else {
                    b"false".to_vec()
                }
            }
            E::Vararg(_) => b"...".to_vec(),
            E::Call { .. } | E::Index { .. } => self.suffixed(e),
            E::Binary { .. } => self.binary(e),
            E::Unary { op, operand, .. } => {
                let mut s = self.expr(operand);
                if let E::Binary { op: bop, .. } = &**operand {
                    if binary_priority(*bop).unwrap().0 <= UNARY_PRIORITY {
                        s = paren(s);
                    }
                }
                if *op == K_NOT {
                    return words(&[b"not", &s]);
                }
                let mut o = kind_text(*op).as_bytes().to_vec();
                if *op == O_SUB && s.first() == Some(&b'-') {
                    o.push(b' ');
                }
                o.extend(s);
                o
            }
            E::Paren(i, _) => paren(self.expr(i)),
            E::Table(fields, _) => self.table(fields),
            E::Func(f, _) => self.function(b"function", f, self.lvl.get()),
        }
    }

    fn suffixed(&self, e: &E) -> Vec<u8> {
        let mut chain = Vec::new();
        let mut e = e;
        loop {
            match e {
                E::Call { func, .. } => {
                    chain.push(e);
                    e = func;
                }
                E::Index { base, .. } => {
                    chain.push(e);
                    e = base;
                }
                _ => break,
            }
        }
        let mut s = self.expr(e);
        if !matches!(e, E::Name(..) | E::Paren(..)) {
            s = paren(s);
        }
        for n in chain.iter().rev() {
            match n {
                E::Index { key, dot, .. } => {
                    let name = if *dot {
                        match &**key {
                            E::Str { value, .. } => Some(self.st.get(*value)),
                            E::Name(x, _) => Some(self.st.get(*x)),
                            _ => None,
                        }
                        .filter(|v| is_name(v))
                    } else {
                        None
                    };
                    match name {
                        Some(v) => {
                            s.push(b'.');
                            s.extend_from_slice(v);
                        }
                        None => {
                            let k = self.expr(key);
                            s.push(b'[');
                            if k.first() == Some(&b'[') {
                                s.push(b' ');
                            }
                            s.extend(k);
                            s.push(b']');
                        }
                    }
                }
                E::Call { args, method, .. } => {
                    if let Some(m) = method {
                        s.push(b':');
                        s.extend_from_slice(self.st.get(*m));
                    }
                    s.push(b'(');
                    s.extend(self.exprs(args));
                    s.push(b')');
                }
                _ => unreachable!(),
            }
        }
        s
    }

    fn binary(&self, e: &E) -> Vec<u8> {
        let mut spine = Vec::new();
        let mut e = e;
        while let E::Binary { left, .. } = e {
            spine.push(e);
            e = left;
        }
        let mut s = self.expr(e);
        let mut left = e;
        for n in spine.iter().rev() {
            if let E::Binary { op, right, .. } = n {
                let (lp, rp) = binary_priority(*op).unwrap();
                if needs_paren(left, lp, true) {
                    s = paren(s);
                }
                let mut r = self.expr(right);
                if needs_paren(right, rp, false) {
                    r = paren(r);
                }
                s = words(&[&s, kind_text(*op).as_bytes(), &r]);
            }
            left = n;
        }
        s
    }

    fn table(&self, fields: &[(Key, E)]) -> Vec<u8> {
        let mut o = vec![b'{'];
        for (k, (key, value)) in fields.iter().enumerate() {
            if k > 0 {
                o.extend_from_slice(b", ");
            }
            let v = self.expr(value);
            match key {
                Key::Pos => o.extend(v),
                Key::Name(s) if is_name(self.st.get(*s)) => {
                    o.extend_from_slice(self.st.get(*s));
                    o.extend_from_slice(b" = ");
                    o.extend(v);
                }
                _ => {
                    let kt = match key {
                        Key::Name(s) => {
                            let mut q = Vec::new();
                            quote(self.st.get(*s), &mut q);
                            q
                        }
                        Key::Expr(x) => self.expr(x),
                        Key::Pos => unreachable!(),
                    };
                    o.push(b'[');
                    if kt.first() == Some(&b'[') {
                        o.push(b' ');
                    }
                    o.extend(kt);
                    o.extend_from_slice(b"] = ");
                    o.extend(v);
                }
            }
        }
        o.push(b'}');
        o
    }

    fn function(&self, head: &[u8], f: &FuncBody, level: usize) -> Vec<u8> {
        let mut sig = head.to_vec();
        sig.push(b'(');
        let mut first = true;
        for p in &f.params {
            if !first {
                sig.extend_from_slice(b", ");
            }
            first = false;
            sig.extend_from_slice(self.st.get(*p));
        }
        if f.vararg {
            if !first {
                sig.extend_from_slice(b", ");
            }
            sig.extend_from_slice(b"...");
        }
        sig.push(b')');
        self.compound(&sig, &f.body, b"end", level)
    }

    fn compound(&self, head: &[u8], body: &Block, tail: &[u8], level: usize) -> Vec<u8> {
        let lines = self.lines(body, level + 1);
        let mut o = head.to_vec();
        if lines.is_empty() {
            o.push(b' ');
            o.extend_from_slice(tail);
            return o;
        }
        o.push(b'\n');
        o.extend(join_lines(lines));
        o.push(b'\n');
        for _ in 0..level {
            o.extend_from_slice(INDENT);
        }
        o.extend_from_slice(tail);
        o
    }

    fn stmt(&self, s: &Stmt, level: usize) -> Vec<u8> {
        let old = self.lvl.replace(level);
        let out = self.stmt_at(s, level);
        self.lvl.set(old);
        out
    }

    fn stmt_at(&self, s: &Stmt, level: usize) -> Vec<u8> {
        match &s.k {
            S::Call(e) => self.expr(e),
            S::Assign { targets, values } => {
                let mut o = self.exprs(targets);
                o.extend_from_slice(b" = ");
                o.extend(self.exprs(values));
                o
            }
            S::Local { names, attribs, values } => {
                let mut ns = Vec::new();
                for (k, (n, a)) in names.iter().zip(attribs).enumerate() {
                    if k > 0 {
                        ns.extend_from_slice(b", ");
                    }
                    ns.extend_from_slice(self.st.get(*n));
                    if let Some(a) = a {
                        ns.extend_from_slice(b" <");
                        ns.extend_from_slice(self.st.get(*a));
                        ns.push(b'>');
                    }
                }
                if values.is_empty() {
                    return words(&[b"local", &ns]);
                }
                words(&[b"local", &ns, b"=", &self.exprs(values)])
            }
            S::Function { name, is_local, f } => {
                let kw: &[u8] = if *is_local { b"local function" } else { b"function" };
                let head = words(&[kw, self.st.get(*name)]);
                self.function(&head, f, level)
            }
            S::If(br) => self.if_stmt(br, level),
            S::Return(values) => words(&[b"return", &self.exprs(values)]),
            S::While(c, b) => self.compound(&words(&[b"while", &self.expr(c), b"do"]), b, b"end", level),
            S::NumFor { var, start, stop, step, body } => {
                let mut r = self.expr(start);
                r.extend_from_slice(b", ");
                r.extend(self.expr(stop));
                if let Some(x) = step {
                    r.extend_from_slice(b", ");
                    r.extend(self.expr(x));
                }
                self.compound(&words(&[b"for", self.st.get(*var), b"=", &r, b"do"]), body, b"end", level)
            }
            S::GenFor { names, exprs, body } => {
                let mut ns = Vec::new();
                for (k, n) in names.iter().enumerate() {
                    if k > 0 {
                        ns.extend_from_slice(b", ");
                    }
                    ns.extend_from_slice(self.st.get(*n));
                }
                let head = words(&[b"for", &ns, b"in", &self.exprs(exprs), b"do"]);
                self.compound(&head, body, b"end", level)
            }
            S::Repeat(b, c) => self.compound(b"repeat", b, &words(&[b"until", &self.expr(c)]), level),
            S::Do(b) => self.compound(b"do", b, b"end", level),
            S::Break => b"break".to_vec(),
            S::Goto(n) => words(&[b"goto", self.st.get(*n)]),
            S::Label(n) => {
                let mut o = b"::".to_vec();
                o.extend_from_slice(self.st.get(*n));
                o.extend_from_slice(b"::");
                o
            }
        }
    }

    fn if_stmt(&self, br: &[(Option<E>, Block)], level: usize) -> Vec<u8> {
        let mut parts: Vec<Vec<u8>> = Vec::new();
        for (n, (cond, body)) in br.iter().enumerate() {
            let head = match cond {
                None => b"else".to_vec(),
                Some(c) => {
                    let mut h = if n > 0 { b"elseif ".to_vec() } else { b"if ".to_vec() };
                    h.extend(self.expr(c));
                    h.extend_from_slice(b" then");
                    h
                }
            };
            if n > 0 {
                let mut l = INDENT.repeat(level);
                l.extend(head);
                parts.push(l);
            } else {
                parts.push(head);
            }
            parts.extend(self.lines(body, level + 1));
        }
        let mut l = INDENT.repeat(level);
        l.extend_from_slice(b"end");
        parts.push(l);
        join_lines(parts)
    }

    fn comment_text(&self, c: u32) -> &[u8] {
        self.st.get(self.comments[c as usize].0)
    }

    fn lines(&self, body: &Block, level: usize) -> Vec<Vec<u8>> {
        let ind = INDENT.repeat(level);
        let mut out = Vec::new();
        for (n, s) in body.stmts.iter().enumerate() {
            for c in (s.lead.0..s.lead.0 + s.lead.1).chain(s.inner.iter().copied()) {
                let mut l = ind.clone();
                l.extend_from_slice(self.comment_text(c));
                out.push(l);
            }
            let mut text = self.stmt(s, level);
            if n > 0 && text.first() == Some(&b'(') {
                text.insert(0, b';');
            }
            if let Some(c) = s.comment {
                text.push(b' ');
                text.extend_from_slice(self.comment_text(c));
            }
            let mut l = ind.clone();
            l.extend(text);
            out.push(l);
        }
        for c in body.end.0..body.end.0 + body.end.1 {
            let mut l = ind.clone();
            l.extend_from_slice(self.comment_text(c));
            out.push(l);
        }
        out
    }
}

fn join_lines(lines: Vec<Vec<u8>>) -> Vec<u8> {
    let mut o = Vec::new();
    for (k, l) in lines.into_iter().enumerate() {
        if k > 0 {
            o.push(b'\n');
        }
        o.extend(l);
    }
    o
}

fn unparse(tree: &Tree, st: &Strs) -> Vec<u8> {
    let p = Printer { st, comments: &tree.comments, lvl: std::cell::Cell::new(0) };
    let lines = p.lines(&tree.body, 0);
    if lines.is_empty() {
        return Vec::new();
    }
    let mut o = join_lines(lines);
    o.push(b'\n');
    o
}

const REPAREN_DEPTH: usize = 4000;

fn reparen_wtf(w: &[u8]) -> R<Vec<u8>> {
    let mut st = Strs::new();
    let mut tree = parse(w, &mut st)?;
    if depth(&tree.body) > REPAREN_DEPTH {
        dismantle(vec![], vec![tree.body]);
        return Err(Fail::Refuse);
    }
    tx_block(&mut tree.body, &mut st);
    if depth(&tree.body) > REPAREN_DEPTH {
        dismantle(vec![], vec![tree.body]);
        return Err(Fail::Refuse);
    }
    let out = unparse(&tree, &st);
    dismantle(vec![], vec![tree.body]);
    Ok(out)
}

pub fn reparen_re(text: &[u8]) -> crate::canon::Re {
    use crate::canon::Re;
    let mut w = Vec::with_capacity(text.len());
    raw_to_wtf(text, &mut w);
    match reparen_wtf(&w) {
        Ok(out) => {
            let mut raw = Vec::with_capacity(out.len());
            match wtf_to_raw(&out, &mut raw) {
                Ok(()) => Re::Text(raw),
                Err(_) => Re::Refuse,
            }
        }
        Err(Fail::Syntax) => Re::NoParse,
        Err(Fail::Refuse) => Re::Refuse,
    }
}

#[allow(dead_code)]
pub fn reparen(text: &[u8]) -> Option<Vec<u8>> {
    match reparen_re(text) {
        crate::canon::Re::Text(t) => Some(t),
        _ => None,
    }
}

type Job = Box<dyn FnOnce() + Send>;
static WORKER: std::sync::OnceLock<std::sync::Mutex<Option<std::sync::mpsc::Sender<Job>>>> =
    std::sync::OnceLock::new();

fn on_big_stack<T: Send + 'static>(f: impl FnOnce() -> T + Send + 'static) -> Option<T> {
    let cell = WORKER.get_or_init(|| {
        let (tx, rx) = std::sync::mpsc::channel::<Job>();
        let spawned = std::thread::Builder::new().stack_size(512 << 20).spawn(move || {
            for job in rx {
                job();
            }
        });
        std::sync::Mutex::new(if spawned.is_ok() { Some(tx) } else { None })
    });
    let (rtx, rrx) = std::sync::mpsc::sync_channel(1);
    let job: Job = Box::new(move || {
        let r = panic::catch_unwind(panic::AssertUnwindSafe(f));
        let _ = rtx.send(r.ok());
    });
    {
        let guard = cell.lock().ok()?;
        guard.as_ref()?.send(job).ok()?;
    }
    rrx.recv().ok().flatten()
}

fn run_big<F: FnOnce() -> Result<Vec<u8>, i32> + Send + 'static>(f: F, out: *mut *mut u8, out_len: *mut usize) -> i32 {
    match on_big_stack(f).unwrap_or(Err(3)) {
        Ok(v) => {
            let mut b = v.into_boxed_slice();
            unsafe {
                *out_len = b.len();
                *out = b.as_mut_ptr();
            }
            std::mem::forget(b);
            0
        }
        Err(c) => c,
    }
}

#[no_mangle]
pub extern "C" fn lua_parse_tree(text: *const u8, len: usize, out: *mut *mut u8, out_len: *mut usize) -> i32 {
    if text.is_null() || out.is_null() || out_len.is_null() {
        return 3;
    }
    let data: Vec<u8> = unsafe { std::slice::from_raw_parts(text, len) }.to_vec();
    run_big(
        move || {
            let mut st = Strs::new();
            match parse(&data, &mut st) {
                Ok(tree) => {
                    let r = serialize(&tree, &st);
                    dismantle(vec![], vec![tree.body]);
                    r.map_err(|_| 3)
                }
                Err(Fail::Syntax) => Err(1),
                Err(Fail::Refuse) => Err(3),
            }
        },
        out,
        out_len,
    )
}

#[no_mangle]
pub extern "C" fn canon_lua_reparen(text: *const u8, len: usize, out: *mut *mut u8, out_len: *mut usize) -> i32 {
    if text.is_null() || out.is_null() || out_len.is_null() {
        return 3;
    }
    let data: Vec<u8> = unsafe { std::slice::from_raw_parts(text, len) }.to_vec();
    run_big(
        move || match reparen_wtf(&data) {
            Ok(t) => Ok(t),
            Err(Fail::Syntax) => Err(1),
            Err(Fail::Refuse) => Err(3),
        },
        out,
        out_len,
    )
}
