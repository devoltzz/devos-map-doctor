// The tokens of the Lua lexer for lua_ast in Rust, the same as the Python.
use crate::canon_lua::{kind_text, lex, Strs, EOF, K_AND, STRING};
use std::panic;

const SEP: &[u8] = b"\x00";

fn tokens(src: &[u8]) -> Option<Vec<u8>> {
    let mut st = Strs::new();
    let lx = lex(src, &mut st).ok()?;
    let mut ints: Vec<u32> = Vec::with_capacity(3 + 3 * lx.toks.len() + 3 * lx.comments.len());
    let mut esc: Vec<u32> = Vec::new();
    let mut texts: Vec<u8> = Vec::with_capacity(src.len() + 3 * lx.toks.len());
    ints.push(lx.toks.len() as u32);
    ints.push(lx.comments.len() as u32);
    ints.push(0);
    for (k, t) in lx.toks.iter().enumerate() {
        if k > 0 {
            texts.extend_from_slice(SEP);
        }
        if t.kind <= STRING {
            let s = st.get(t.sym);
            if t.kind == STRING && (s[0] == b'"' || s[0] == b'\'') && s.contains(&b'\\') {
                esc.push(k as u32);
            }
            texts.extend_from_slice(s);
        } else if t.kind >= K_AND {
            texts.extend_from_slice(kind_text(t.kind).as_bytes());
        } else if t.kind != EOF {
            return None;
        }
        ints.push(t.kind as u32);
        ints.push(t.line);
        ints.push(t.cpos);
    }
    let mut blob: Vec<u8> = Vec::new();
    for (k, &(text, line)) in lx.comments.iter().enumerate() {
        let b = st.get(text);
        ints.push(line);
        ints.push(lx.ctok[k]);
        ints.push(b.len() as u32);
        blob.extend_from_slice(b);
    }
    ints[2] = esc.len() as u32;
    ints.extend_from_slice(&esc);
    let mut out = Vec::with_capacity(4 * ints.len() + blob.len() + texts.len());
    for v in ints {
        out.extend_from_slice(&v.to_le_bytes());
    }
    out.extend_from_slice(&blob);
    out.extend_from_slice(&texts);
    Some(out)
}

#[no_mangle]
pub extern "C" fn lua_lex_tokens(text: *const u8, len: usize, out: *mut *mut u8, out_len: *mut usize) -> i32 {
    if text.is_null() || out.is_null() || out_len.is_null() {
        return 1;
    }
    let data = unsafe { std::slice::from_raw_parts(text, len) };
    match panic::catch_unwind(|| tokens(data)) {
        Ok(Some(v)) => {
            let mut b = v.into_boxed_slice();
            unsafe {
                *out_len = b.len();
                *out = b.as_mut_ptr();
            }
            std::mem::forget(b);
            0
        }
        _ => 1,
    }
}
