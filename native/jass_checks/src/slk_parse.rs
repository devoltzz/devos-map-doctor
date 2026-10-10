// The SLK and INI files cut into fields in Rust, the same as the Python.
use std::collections::HashMap;
use std::panic;

struct Refuse;
type R<T> = Result<T, Refuse>;

struct Out {
    ints: Vec<u32>,
    text: Vec<u8>,
    first: bool,
}

impl Out {
    fn new(cap: usize) -> Out {
        Out { ints: Vec::with_capacity(1024), text: Vec::with_capacity(cap), first: true }
    }
    fn s(&mut self, b: &[u8]) {
        if !self.first {
            self.text.push(b'\n');
        }
        self.first = false;
        self.text.extend_from_slice(b);
    }
    fn n(&mut self, v: usize) -> R<()> {
        if v > u32::MAX as usize {
            return Err(Refuse);
        }
        self.ints.push(v as u32);
        Ok(())
    }
    fn finish(self) -> Vec<u8> {
        let mut b = Vec::with_capacity(4 + self.ints.len() * 4 + self.text.len());
        b.extend_from_slice(&(self.ints.len() as u32).to_le_bytes());
        for v in &self.ints {
            b.extend_from_slice(&v.to_le_bytes());
        }
        b.extend_from_slice(&self.text);
        b
    }
}

fn lines(t: &[u8]) -> impl Iterator<Item = &[u8]> {
    t.split(|&b| b == b'\n').map(|l| {
        let mut e = l.len();
        while e > 0 && l[e - 1] == b'\r' {
            e -= 1;
        }
        &l[..e]
    })
}

fn coord(d: &[u8]) -> R<i64> {
    if d.is_empty() || d.len() > 64 || !d.iter().all(|c| c.is_ascii_digit()) {
        return Err(Refuse);
    }
    let first = d.iter().position(|&c| c != b'0').unwrap_or(d.len());
    if d.len() - first > 6 {
        return Err(Refuse);
    }
    let mut v: i64 = 0;
    for &c in d {
        v = v * 10 + (c - b'0') as i64;
    }
    Ok(v)
}

fn fields(l: &[u8], out: &mut Vec<(usize, usize)>) {
    out.clear();
    let mut buf: Option<(usize, usize)> = None;
    let mut a = 2;
    loop {
        let b = match l[a..].iter().position(|&c| c == b';') {
            Some(i) => a + i,
            None => l.len(),
        };
        let p = &l[a..b];
        let q = p.iter().filter(|&&c| c == b'"').count();
        if let Some((bs, bq)) = buf {
            let nq = bq + q;
            if nq % 2 == 0 {
                out.push((bs, b));
                buf = None;
            } else {
                buf = Some((bs, nq));
            }
        } else if p.starts_with(b"K\"") && q % 2 == 1 {
            buf = Some((a, q));
        } else {
            out.push((a, b));
        }
        if b >= l.len() {
            break;
        }
        a = b + 1;
    }
    if let Some((bs, _)) = buf {
        out.push((bs, l.len()));
    }
}

struct Row<'a> {
    y: i64,
    cells: Vec<(i64, &'a [u8])>,
    at: HashMap<i64, usize>,
}

fn op_slk(raw: &[u8]) -> R<Vec<u8>> {
    let mut rows: Vec<Row> = Vec::new();
    let mut by_y: HashMap<i64, usize> = HashMap::new();
    let mut cur_y: i64 = 0;
    let mut fs: Vec<(usize, usize)> = Vec::with_capacity(16);
    for line in lines(raw) {
        if !line.starts_with(b"C;") {
            continue;
        }
        fields(line, &mut fs);
        let mut x: Option<i64> = None;
        let mut y: Option<i64> = None;
        let mut k: Option<&[u8]> = None;
        for &(a, b) in fs.iter() {
            let p = &line[a..b];
            match p.first() {
                Some(b'X') => x = Some(coord(&p[1..])?),
                Some(b'Y') => y = Some(coord(&p[1..])?),
                Some(b'K') => {
                    let mut v = &p[1..];
                    if v.len() >= 2 && v[0] == b'"' && v[v.len() - 1] == b'"' {
                        v = &v[1..v.len() - 1];
                    }
                    k = Some(v);
                }
                _ => {}
            }
        }
        if let Some(v) = y {
            cur_y = v;
        }
        let (x, k) = match (x, k) {
            (Some(x), Some(k)) => (x, k),
            _ => continue,
        };
        let ri = match by_y.get(&cur_y) {
            Some(&i) => i,
            None => {
                rows.push(Row { y: cur_y, cells: Vec::new(), at: HashMap::new() });
                by_y.insert(cur_y, rows.len() - 1);
                rows.len() - 1
            }
        };
        let row = &mut rows[ri];
        match row.at.get(&x) {
            Some(&ci) => row.cells[ci].1 = k,
            None => {
                row.at.insert(x, row.cells.len());
                row.cells.push((x, k));
            }
        }
    }
    let mut out = Out::new(raw.len());
    let hi = match by_y.get(&1) {
        Some(&i) => i,
        None => {
            out.n(0)?;
            return Ok(out.finish());
        }
    };
    out.n(1)?;
    let header = &rows[hi];
    let maxx = header.cells.iter().map(|c| c.0).max().unwrap_or(0);
    let nh = if maxx >= 1 { maxx as usize } else { 0 };
    out.n(nh)?;
    let mut name_of: HashMap<i64, u32> = HashMap::new();
    let mut names: Vec<&[u8]> = Vec::new();
    for &(cx, ck) in &header.cells {
        if !ck.is_empty() {
            name_of.insert(cx, names.len() as u32);
            names.push(ck);
        }
    }
    out.n(names.len())?;
    for i in 1..=nh as i64 {
        match header.at.get(&i) {
            Some(&ci) => out.s(header.cells[ci].1),
            None => out.s(b""),
        }
    }
    for nm in &names {
        out.s(nm);
    }
    let mut order: Vec<usize> = (0..rows.len()).filter(|&i| i != hi).collect();
    order.sort_by_key(|&i| rows[i].y);
    let mut kept: Vec<usize> = Vec::with_capacity(order.len());
    for &i in &order {
        if rows[i].at.contains_key(&1) {
            kept.push(i);
        }
    }
    out.n(kept.len())?;
    let mut sel: Vec<(u32, &[u8])> = Vec::new();
    for &i in &kept {
        let row = &rows[i];
        sel.clear();
        for &(cx, ck) in &row.cells {
            if let Some(&ni) = name_of.get(&cx) {
                sel.push((ni, ck));
            }
        }
        out.n(sel.len())?;
        out.s(row.cells[row.at[&1]].1);
        for &(ni, ck) in &sel {
            out.ints.push(ni);
            out.s(ck);
        }
    }
    Ok(out.finish())
}

fn ws_head(b: &[u8]) -> usize {
    match b.first() {
        Some(9..=13) | Some(28..=32) => 1,
        Some(0xC2) if b.len() >= 2 && (b[1] == 0x85 || b[1] == 0xA0) => 2,
        Some(0xE1) if b.len() >= 3 && b[1] == 0x9A && b[2] == 0x80 => 3,
        Some(0xE2) if b.len() >= 3
            && ((b[1] == 0x80 && (b[2] <= 0x8A && b[2] >= 0x80 || b[2] == 0xA8 || b[2] == 0xA9 || b[2] == 0xAF))
                || (b[1] == 0x81 && b[2] == 0x9F)) => 3,
        Some(0xE3) if b.len() >= 3 && b[1] == 0x80 && b[2] == 0x80 => 3,
        _ => 0,
    }
}

fn ws_tail(b: &[u8]) -> usize {
    let n = b.len();
    if n >= 1 && matches!(b[n - 1], 9..=13 | 28..=32) {
        return 1;
    }
    if n >= 2 && ws_head(&b[n - 2..]) == 2 {
        return 2;
    }
    if n >= 3 && ws_head(&b[n - 3..]) == 3 {
        return 3;
    }
    0
}

fn strip(mut b: &[u8]) -> &[u8] {
    loop {
        let k = ws_head(b);
        if k == 0 {
            break;
        }
        b = &b[k..];
    }
    loop {
        let k = ws_tail(b);
        if k == 0 {
            break;
        }
        b = &b[..b.len() - k];
    }
    b
}

fn section(line: &[u8]) -> Option<&[u8]> {
    if line.first() != Some(&b'[') {
        return None;
    }
    let j = 1 + line[1..].iter().position(|&c| c == b']')?;
    if j < 2 {
        return None;
    }
    let mut rest = &line[j + 1..];
    while !rest.is_empty() {
        let k = ws_head(rest);
        if k == 0 {
            return None;
        }
        rest = &rest[k..];
    }
    Some(&line[1..j])
}

fn op_ini(raw: &[u8], quotes: bool) -> R<Vec<u8>> {
    let mut secs: Vec<(&[u8], Vec<(&[u8], &[u8])>)> = Vec::new();
    let mut idx: HashMap<&[u8], usize> = HashMap::new();
    let mut cur: Option<usize> = None;
    for line in lines(raw) {
        if line.is_empty() || line.starts_with(b"//") || line.starts_with(b";") {
            continue;
        }
        if let Some(name) = section(line) {
            cur = Some(match idx.get(name) {
                Some(&i) => i,
                None => {
                    secs.push((name, Vec::new()));
                    idx.insert(name, secs.len() - 1);
                    secs.len() - 1
                }
            });
            continue;
        }
        let ci = match cur {
            Some(i) => i,
            None => continue,
        };
        let eq = match line.iter().position(|&c| c == b'=') {
            Some(i) => i,
            None => continue,
        };
        let k = strip(&line[..eq]);
        let mut v = strip(&line[eq + 1..]);
        if quotes && v.len() >= 2 && v[0] == b'"' && v[v.len() - 1] == b'"' {
            v = &v[1..v.len() - 1];
        }
        secs[ci].1.push((k, v));
    }
    let mut out = Out::new(raw.len());
    out.n(secs.len())?;
    for (name, kv) in &secs {
        out.n(kv.len())?;
        out.s(name);
        for (k, _) in kv {
            out.s(k);
        }
        for (_, v) in kv {
            out.s(v);
        }
    }
    Ok(out.finish())
}

fn run(op: u32, raw: &[u8]) -> R<Vec<u8>> {
    match op {
        1 => op_slk(raw),
        2 => op_ini(raw, true),
        3 => op_ini(raw, false),
        _ => Err(Refuse),
    }
}

#[no_mangle]
pub extern "C" fn slk_parse(op: u32, raw: *const u8, len: usize, out: *mut *mut u8, out_len: *mut usize) -> i32 {
    if (raw.is_null() && len > 0) || out.is_null() || out_len.is_null() {
        return 3;
    }
    let t: &[u8] = if len == 0 { &[] } else { unsafe { std::slice::from_raw_parts(raw, len) } };
    match panic::catch_unwind(|| run(op, t)) {
        Ok(Ok(v)) => {
            let mut b = v.into_boxed_slice();
            unsafe {
                *out_len = b.len();
                *out = b.as_mut_ptr();
            }
            std::mem::forget(b);
            0
        }
        Ok(Err(Refuse)) => 1,
        Err(_) => 3,
    }
}
