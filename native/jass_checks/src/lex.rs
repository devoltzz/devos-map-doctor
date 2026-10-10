// The JASS tokenizers of the obfuscator and of the KKWE compiler in Rust, the same tokens as their regular expressions.
use std::panic;

const NOT_DONE: i32 = 1;
const INTERNAL: i32 = 3;

const O_COM: u8 = 0;
const O_STR: u8 = 1;
const O_RAW: u8 = 2;
const O_NUM: u8 = 3;
const O_ID: u8 = 4;
const O_NL: u8 = 5;
const O_WS: u8 = 6;
const O_OP: u8 = 7;

const K_NL: u8 = 0;
const K_REAL: u8 = 1;
const K_HEX: u8 = 2;
const K_INT: u8 = 3;
const K_RAW: u8 = 4;
const K_STR: u8 = 5;
const K_ID: u8 = 6;
const K_OP: u8 = 7;
const K_END: u8 = 8;

struct NotDone;

#[inline]
fn at(t: &[u32], i: usize) -> u32 {
    if i < t.len() {
        t[i]
    } else {
        u32::MAX
    }
}

#[inline]
fn is_digit(c: u32) -> bool {
    (0x30..=0x39).contains(&c)
}

#[inline]
fn is_hex(c: u32) -> bool {
    is_digit(c) || (0x41..=0x46).contains(&c) || (0x61..=0x66).contains(&c)
}

#[inline]
fn is_alpha_(c: u32) -> bool {
    (0x41..=0x5A).contains(&c) || (0x61..=0x7A).contains(&c) || c == 0x5F
}

#[inline]
fn is_word(c: u32) -> bool {
    is_alpha_(c) || is_digit(c)
}

#[inline]
fn wide(c: u32) -> bool {
    c >= 0x80 && c != u32::MAX
}

fn digits(t: &[u32], mut i: usize) -> Result<usize, NotDone> {
    while i < t.len() && is_digit(t[i]) {
        i += 1;
    }
    if wide(at(t, i)) {
        return Err(NotDone);
    }
    Ok(i)
}

fn quoted(t: &[u32], i: usize, q: u32) -> Option<usize> {
    let n = t.len();
    let mut j = i + 1;
    while j < n {
        let c = t[j];
        if c == q {
            return Some(j + 1);
        }
        if c == 0x5C {
            if j + 1 >= n {
                return None;
            }
            j += 2;
        } else {
            j += 1;
        }
    }
    None
}

fn obfuscator_tokens(t: &[u32]) -> Result<(Vec<u8>, Vec<u32>), NotDone> {
    let n = t.len();
    let mut kinds = Vec::with_capacity(n / 3 + 1);
    let mut ends: Vec<u32> = Vec::with_capacity(n / 3 + 1);
    let mut i = 0usize;
    while i < n {
        let c = t[i];
        let (k, e) = if c == 0x2F && at(t, i + 1) == 0x2F {
            let mut j = i + 2;
            while j < n && t[j] != 0x0A {
                j += 1;
            }
            (O_COM, j)
        } else if c == 0x22 || c == 0x27 {
            match quoted(t, i, c) {
                Some(e) => (if c == 0x22 { O_STR } else { O_RAW }, e),
                None => (O_OP, i + 1),
            }
        } else if c == 0x30 && (at(t, i + 1) == 0x78 || at(t, i + 1) == 0x58) && is_hex(at(t, i + 2)) {
            let mut j = i + 2;
            while j < n && is_hex(t[j]) {
                j += 1;
            }
            (O_NUM, j)
        } else if c == 0x24 && is_hex(at(t, i + 1)) {
            let mut j = i + 1;
            while j < n && is_hex(t[j]) {
                j += 1;
            }
            (O_NUM, j)
        } else if is_digit(c) {
            let j = digits(t, i)?;
            if at(t, j) == 0x2E {
                (O_NUM, digits(t, j + 1)?)
            } else {
                (O_NUM, j)
            }
        } else if c == 0x2E && (is_digit(at(t, i + 1)) || wide(at(t, i + 1))) {
            if wide(at(t, i + 1)) {
                return Err(NotDone);
            }
            (O_NUM, digits(t, i + 1)?)
        } else if is_alpha_(c) {
            let mut j = i + 1;
            while j < n && is_word(t[j]) {
                j += 1;
            }
            if wide(at(t, j)) {
                return Err(NotDone);
            }
            (O_ID, j)
        } else if c == 0x0A {
            (O_NL, i + 1)
        } else if c == 0x0D && at(t, i + 1) == 0x0A {
            (O_NL, i + 2)
        } else if c == 0x20 || c == 0x09 || c == 0x0D || c == 0x0C || c == 0x0B {
            let mut j = i + 1;
            while j < n && matches!(t[j], 0x20 | 0x09 | 0x0D | 0x0C | 0x0B) {
                j += 1;
            }
            (O_WS, j)
        } else if wide(c) {
            return Err(NotDone);
        } else {
            (O_OP, i + 1)
        };
        kinds.push(k);
        ends.push(e as u32);
        i = e;
    }
    Ok((kinds, ends))
}

fn compiler_tokens(t: &[u32]) -> Result<Vec<u32>, NotDone> {
    let n = t.len();
    let mut out: Vec<u32> = Vec::with_capacity(n / 2 + 8);
    let mut line: u32 = 1;
    let mut last_nl = true;
    let mut i = 0usize;
    while i < n {
        let c = t[i];
        if matches!(c, 0x20 | 0x09 | 0x0D | 0x0C | 0x0B) {
            let mut j = i + 1;
            while j < n && matches!(t[j], 0x20 | 0x09 | 0x0D | 0x0C | 0x0B) {
                j += 1;
            }
            i = j;
            continue;
        }
        if c == 0x0A {
            if !last_nl {
                out.extend_from_slice(&[K_NL as u32, i as u32, (i + 1) as u32, line]);
                last_nl = true;
            }
            line += 1;
            i += 1;
            continue;
        }
        if c == 0x2F && at(t, i + 1) == 0x2F {
            let mut j = i + 2;
            while j < n && t[j] != 0x0A {
                j += 1;
            }
            i = j;
            continue;
        }
        let (k, e) = if is_digit(c) {
            let j = digits(t, i)?;
            if at(t, j) == 0x2E {
                (K_REAL, digits(t, j + 1)?)
            } else if c == 0x30 && (at(t, i + 1) == 0x78 || at(t, i + 1) == 0x58) && is_hex(at(t, i + 2)) {
                let mut j = i + 2;
                while j < n && is_hex(t[j]) {
                    j += 1;
                }
                (K_HEX, j)
            } else {
                (K_INT, j)
            }
        } else if c == 0x2E && (is_digit(at(t, i + 1)) || wide(at(t, i + 1))) {
            if wide(at(t, i + 1)) {
                return Err(NotDone);
            }
            (K_REAL, digits(t, i + 1)?)
        } else if c == 0x24 && is_hex(at(t, i + 1)) {
            let mut j = i + 1;
            while j < n && is_hex(t[j]) {
                j += 1;
            }
            (K_HEX, j)
        } else if c == 0x27 || c == 0x22 {
            match quoted(t, i, c) {
                Some(e) => (if c == 0x27 { K_RAW } else { K_STR }, e),
                None => return Err(NotDone),
            }
        } else if is_alpha_(c) {
            let mut j = i + 1;
            while j < n && is_word(t[j]) {
                j += 1;
            }
            (K_ID, j)
        } else if matches!(c, 0x3D | 0x21 | 0x3C | 0x3E) && at(t, i + 1) == 0x3D {
            (K_OP, i + 2)
        } else if matches!(c, 0x2D | 0x2B | 0x2A | 0x2F | 0x3D | 0x3C | 0x3E | 0x28 | 0x29 | 0x5B | 0x5D | 0x2C) {
            (K_OP, i + 1)
        } else {
            return Err(NotDone);
        };
        out.extend_from_slice(&[k as u32, i as u32, e as u32, line]);
        last_nl = false;
        if k == K_STR {
            line += t[i..e].iter().filter(|&&x| x == 0x0A).count() as u32;
        }
        i = e;
    }
    out.extend_from_slice(&[K_END as u32, n as u32, n as u32, line]);
    Ok(out)
}

fn give(b: Vec<u8>, out: *mut *mut u8, out_len: *mut usize) {
    let mut b = b.into_boxed_slice();
    unsafe {
        *out_len = b.len();
        *out = b.as_mut_ptr();
    }
    std::mem::forget(b);
}

#[no_mangle]
pub extern "C" fn jass_lex(text: *const u8, len: usize, mode: i32, out: *mut *mut u8, out_len: *mut usize) -> i32 {
    if (text.is_null() && len > 0) || out.is_null() || out_len.is_null() || len % 4 != 0 || !(0..=1).contains(&mode) {
        return INTERNAL;
    }
    let raw: &[u8] = if len == 0 { &[] } else { unsafe { std::slice::from_raw_parts(text, len) } };
    let r = panic::catch_unwind(|| {
        let t: Vec<u32> = raw.chunks_exact(4).map(|c| u32::from_le_bytes([c[0], c[1], c[2], c[3]])).collect();
        if t.len() > u32::MAX as usize - 2 {
            return Err(NotDone);
        }
        if mode == 0 {
            let (kinds, ends) = obfuscator_tokens(&t)?;
            let mut b = Vec::with_capacity(4 + kinds.len() * 5);
            b.extend_from_slice(&(kinds.len() as u32).to_le_bytes());
            b.extend_from_slice(&kinds);
            for e in ends {
                b.extend_from_slice(&e.to_le_bytes());
            }
            Ok(b)
        } else {
            let v = compiler_tokens(&t)?;
            let mut b = Vec::with_capacity(v.len() * 4);
            for x in v {
                b.extend_from_slice(&x.to_le_bytes());
            }
            Ok(b)
        }
    });
    match r {
        Ok(Ok(b)) => {
            give(b, out, out_len);
            0
        }
        Ok(Err(NotDone)) => NOT_DONE,
        Err(_) => INTERNAL,
    }
}
