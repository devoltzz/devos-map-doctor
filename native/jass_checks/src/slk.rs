// The SLK table passes in Rust, the same lines as the Python.
use std::hash::{BuildHasherDefault, Hasher};
use std::panic;

const NONE: i64 = i64::MIN;

#[derive(Default)]
struct Fx(u64);
impl Hasher for Fx {
    fn finish(&self) -> u64 {
        self.0
    }
    fn write(&mut self, bytes: &[u8]) {
        for &b in bytes {
            self.write_u64(b as u64);
        }
    }
    fn write_u64(&mut self, v: u64) {
        self.0 = (self.0.rotate_left(5) ^ v).wrapping_mul(0x51_7c_c1_b7_27_22_0a_95);
    }
    fn write_i64(&mut self, v: i64) {
        self.write_u64(v as u64);
    }
}
type HashMap<K, V> = std::collections::HashMap<K, V, BuildHasherDefault<Fx>>;
type HashSet<K> = std::collections::HashSet<K, BuildHasherDefault<Fx>>;

struct Refuse;
type R<T> = Result<T, Refuse>;

fn split_lines(t: &[u8]) -> Vec<&[u8]> {
    t.split(|&b| b == b'\n').collect()
}

fn campos(l: &[u8]) -> Vec<(usize, usize)> {
    let mut segs: Vec<(usize, usize)> = Vec::with_capacity(8);
    let mut s = 0;
    for (i, &b) in l.iter().enumerate() {
        if b == b';' {
            segs.push((s, i));
            s = i + 1;
        }
    }
    segs.push((s, l.len()));
    let mut out = Vec::with_capacity(segs.len());
    let mut buf: Option<(usize, usize)> = None;
    for &(a, b) in &segs[1..] {
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
    }
    if let Some((bs, _)) = buf {
        out.push((bs, l.len()));
    }
    out
}

fn coord(f: &[u8]) -> R<i64> {
    let mut j = 1;
    while j < f.len() && f[j].is_ascii_digit() {
        j += 1;
    }
    if j < f.len() && f[j] >= 0x80 {
        return Err(Refuse);
    }
    let ds = &f[1..j];
    let first = ds.iter().position(|&c| c != b'0').unwrap_or(ds.len());
    if ds.len() - first > 18 {
        return Err(Refuse);
    }
    let mut v: i64 = 0;
    for &c in ds {
        v = v * 10 + (c - b'0') as i64;
    }
    Ok(v)
}

fn record(l: &[u8]) -> R<(Option<i64>, Option<i64>, Option<(usize, usize)>)> {
    let mut acc = (None, None, None);
    if !l.contains(&b'"') {
        let mut s = match l.iter().position(|&b| b == b';') {
            Some(p) => p + 1,
            None => return Ok(acc),
        };
        loop {
            let e = l[s..].iter().position(|&b| b == b';').map_or(l.len(), |p| s + p);
            field(l, s, e, &mut acc)?;
            if e >= l.len() {
                break;
            }
            s = e + 1;
        }
        return Ok(acc);
    }
    for (a, b) in campos(l) {
        field(l, a, b, &mut acc)?;
    }
    Ok(acc)
}

type Acc = (Option<i64>, Option<i64>, Option<(usize, usize)>);

fn field(l: &[u8], a: usize, b: usize, acc: &mut Acc) -> R<()> {
    let (x, y, k) = (&mut acc.0, &mut acc.1, &mut acc.2);
    {
        let f = &l[a..b];
        if f.is_empty() {
            return Ok(());
        }
        let c0 = f[0];
        if (c0 == b'X' || c0 == b'Y') && f.len() >= 2 {
            if f[1] >= 0x80 {
                return Err(Refuse);
            }
            if f[1].is_ascii_digit() {
                let v = coord(f)?;
                if c0 == b'X' {
                    *x = Some(v);
                } else {
                    *y = Some(v);
                }
            }
        } else if c0 == b'K' {
            *k = Some((a + 1, b));
        }
    }
    Ok(())
}

struct Cell {
    i: usize,
    x: i64,
    y: i64,
    k: Option<(usize, usize)>,
}

fn cells(lines: &[&[u8]]) -> R<Vec<Cell>> {
    let mut out = Vec::new();
    let (mut cx, mut cy) = (NONE, NONE);
    for (i, l) in lines.iter().enumerate() {
        if !l.starts_with(b"C;") {
            continue;
        }
        let (x, y, k) = record(l)?;
        if let Some(v) = x {
            cx = v;
        }
        if let Some(v) = y {
            cy = v;
        }
        out.push(Cell { i, x: cx, y: cy, k });
    }
    Ok(out)
}

fn strip_quotes(v: &[u8]) -> &[u8] {
    let mut a = 0;
    let mut b = v.len();
    while a < b && v[a] == b'"' {
        a += 1;
    }
    while b > a && v[b - 1] == b'"' {
        b -= 1;
    }
    &v[a..b]
}

fn replace_k(line: &[u8], old: &[u8], new: &[u8]) -> R<Vec<u8>> {
    let mut pat = Vec::with_capacity(old.len() + 1);
    pat.push(b'K');
    pat.extend_from_slice(old);
    let pos = match line.windows(pat.len()).position(|w| w == &pat[..]) {
        Some(p) => p,
        None => return Ok(line.to_vec()),
    };
    let end = pos + pat.len();
    if end < line.len() && (0x80..=0xBF).contains(&line[end]) {
        return Err(Refuse);
    }
    let mut out = Vec::with_capacity(line.len() + new.len());
    out.extend_from_slice(&line[..pos]);
    out.push(b'K');
    out.extend_from_slice(new);
    out.extend_from_slice(&line[end..]);
    Ok(out)
}

struct W(Vec<u8>);
impl W {
    fn int(&mut self, v: i64) {
        self.0.extend_from_slice(&v.to_le_bytes());
    }
    fn bytes(&mut self, b: &[u8]) {
        self.0.extend_from_slice(&(b.len() as u32).to_le_bytes());
        self.0.extend_from_slice(b);
    }
}

struct Rd<'a> {
    b: &'a [u8],
    p: usize,
}
impl<'a> Rd<'a> {
    fn int(&mut self) -> R<i64> {
        if self.p + 8 > self.b.len() {
            return Err(Refuse);
        }
        let mut a = [0u8; 8];
        a.copy_from_slice(&self.b[self.p..self.p + 8]);
        self.p += 8;
        Ok(i64::from_le_bytes(a))
    }
    fn bytes(&mut self) -> R<&'a [u8]> {
        if self.p + 4 > self.b.len() {
            return Err(Refuse);
        }
        let mut a = [0u8; 4];
        a.copy_from_slice(&self.b[self.p..self.p + 4]);
        let n = u32::from_le_bytes(a) as usize;
        self.p += 4;
        if self.p + n > self.b.len() {
            return Err(Refuse);
        }
        let s = &self.b[self.p..self.p + n];
        self.p += n;
        Ok(s)
    }
    fn count(&mut self) -> R<usize> {
        let n = self.int()?;
        if n < 0 || n as usize > self.b.len() {
            return Err(Refuse);
        }
        Ok(n as usize)
    }
}

fn put_changes(w: &mut W, changed: &[(usize, Vec<u8>)], trocas: &[(i64, i64, &[u8], Vec<u8>)]) {
    w.int(changed.len() as i64);
    for (i, l) in changed {
        w.int(*i as i64);
        w.bytes(l);
    }
    w.int(trocas.len() as i64);
    for (y, x, v, novo) in trocas {
        w.int(*y);
        w.int(*x);
        w.bytes(v);
        w.bytes(novo);
    }
}

fn re_num(s: &[u8]) -> bool {
    let n = s.len();
    let mut i = 0;
    if i < n && s[i] == b'-' {
        i += 1;
    }
    let d0 = i;
    while i < n && s[i].is_ascii_digit() {
        i += 1;
    }
    if i > d0 {
        if i < n && s[i] == b'.' {
            i += 1;
            while i < n && s[i].is_ascii_digit() {
                i += 1;
            }
        }
    } else {
        if !(i < n && s[i] == b'.') {
            return false;
        }
        i += 1;
        let d1 = i;
        while i < n && s[i].is_ascii_digit() {
            i += 1;
        }
        if i == d1 {
            return false;
        }
    }
    if i < n && (s[i] == b'e' || s[i] == b'E') {
        let mut j = i + 1;
        if j < n && (s[j] == b'-' || s[j] == b'+') {
            j += 1;
        }
        let d2 = j;
        while j < n && s[j].is_ascii_digit() {
            j += 1;
        }
        if j > d2 {
            i = j;
        }
    }
    i == n
}

fn re_num_exact(s: &[u8]) -> R<bool> {
    if s.iter().all(|&c| c < 0x80) {
        return Ok(re_num(s));
    }
    let t: Vec<u8> = s.iter().map(|&c| if c >= 0x80 { b'0' } else { c }).collect();
    if re_num(&t) {
        Err(Refuse)
    } else {
        Ok(false)
    }
}

fn op_numeros(lines: &[&[u8]], w: &mut W) -> R<()> {
    let cs = cells(lines)?;
    let mut conta: HashMap<i64, (u64, u64)> = HashMap::default();
    for c in &cs {
        let k = match c.k {
            Some(r) => &lines[c.i][r.0..r.1],
            None => continue,
        };
        if c.y == 1 {
            continue;
        }
        let e = conta.entry(c.x).or_insert((0, 0));
        if k.starts_with(b"\"") {
            e.1 += 1;
        } else {
            e.0 += 1;
        }
    }
    let numericas: HashSet<i64> = conta.iter().filter(|(_, &(n, t))| n >= 10 && n > t * 9).map(|(&x, _)| x).collect();
    let mut changed: Vec<(usize, Vec<u8>)> = Vec::new();
    let mut trocas = Vec::new();
    for c in &cs {
        let v = match c.k {
            Some(r) => &lines[c.i][r.0..r.1],
            None => continue,
        };
        if c.y == 1 || !numericas.contains(&c.x) || !v.starts_with(b"\"") {
            continue;
        }
        let corpo = strip_quotes(v);
        if !re_num_exact(corpo)? {
            continue;
        }
        let mut novo: &[u8] = corpo;
        if corpo.ends_with(b".") {
            let mut e = corpo.len();
            while e > 0 && corpo[e - 1] == b'.' {
                e -= 1;
            }
            novo = &corpo[..e];
        }
        let novo: Vec<u8> = if novo.is_empty() || novo == b"-" { b"0".to_vec() } else { novo.to_vec() };
        let nl = replace_k(lines[c.i], v, &novo)?;
        changed.push((c.i, nl));
        trocas.push((c.y, c.x, v, novo));
    }
    let mut xs: Vec<i64> = numericas.into_iter().collect();
    xs.sort();
    w.int(xs.len() as i64);
    for x in xs {
        w.int(x);
    }
    put_changes(w, &changed, &trocas);
    Ok(())
}

fn op_nomes(lines: &[&[u8]], w: &mut W) -> R<()> {
    let cs = cells(lines)?;
    let mut ordem: Vec<i64> = Vec::new();
    let mut nomes: HashMap<i64, &[u8]> = HashMap::default();
    for c in &cs {
        if let Some(r) = c.k {
            if c.y == 1 {
                if nomes.insert(c.x, strip_quotes(&lines[c.i][r.0..r.1])).is_none() {
                    ordem.push(c.x);
                }
            }
        }
    }
    w.int(ordem.len() as i64);
    for x in ordem {
        w.int(x);
        w.bytes(nomes[&x]);
    }
    Ok(())
}

fn space_at(p: &[u8], i: usize) -> usize {
    let c = p[i];
    if matches!(c, b'\t' | b'\n' | 0x0b | 0x0c | b'\r' | 0x1c..=0x1f | b' ') {
        return 1;
    }
    let r = &p[i..];
    if r.starts_with(&[0xC2, 0x85]) || r.starts_with(&[0xC2, 0xA0]) {
        return 2;
    }
    if r.len() >= 3 {
        let (a, b, d) = (r[0], r[1], r[2]);
        let ok = (a == 0xE1 && b == 0x9A && d == 0x80)
            || (a == 0xE2 && b == 0x80 && ((0x80..=0x8A).contains(&d) || d == 0xA8 || d == 0xA9 || d == 0xAF))
            || (a == 0xE2 && b == 0x81 && d == 0x9F)
            || (a == 0xE3 && b == 0x80 && d == 0x80);
        if ok {
            return 3;
        }
    }
    0
}

fn id_com_n(p: &[u8]) -> Option<Vec<u8>> {
    let n = p.len();
    let mut i = 0;
    while i < n {
        let s = space_at(p, i);
        if s == 0 {
            break;
        }
        i += s;
    }
    if i + 4 > n || !p[i..i + 4].iter().all(|c| c.is_ascii_alphanumeric()) {
        return None;
    }
    let g1 = i + 4;
    let mut j = g1;
    while j + 2 <= n && &p[j..j + 2] == b"|n" {
        j += 2;
    }
    if j == g1 {
        return None;
    }
    let g2 = j;
    while j < n {
        let s = space_at(p, j);
        if s == 0 {
            return None;
        }
        j += s;
    }
    let mut out = p[..g1].to_vec();
    out.extend_from_slice(&p[g2..]);
    Some(out)
}

fn op_listas(lines: &[&[u8]], arg: &mut Rd, w: &mut W) -> R<()> {
    let n = arg.count()?;
    let mut alvo = HashSet::default();
    for _ in 0..n {
        alvo.insert(arg.int()?);
    }
    let cs = cells(lines)?;
    let mut changed: Vec<(usize, Vec<u8>)> = Vec::new();
    let mut trocas = Vec::new();
    for c in &cs {
        let v = match c.k {
            Some(r) => &lines[c.i][r.0..r.1],
            None => continue,
        };
        if c.y == 1 || !v.starts_with(b"\"") || !v.windows(2).any(|w| w == b"|n") || !alvo.contains(&c.x) {
            continue;
        }
        if !(v.ends_with(b"\"") && v.len() > 1) {
            continue;
        }
        let mut mudou = false;
        let mut novo = vec![b'"'];
        for (j, p) in v[1..v.len() - 1].split(|&b| b == b',').enumerate() {
            if j > 0 {
                novo.push(b',');
            }
            match id_com_n(p) {
                Some(q) => {
                    if q != p {
                        mudou = true;
                    }
                    novo.extend_from_slice(&q);
                }
                None => novo.extend_from_slice(p),
            }
        }
        if !mudou {
            continue;
        }
        novo.push(b'"');
        let nl = replace_k(lines[c.i], v, &novo)?;
        changed.push((c.i, nl));
        trocas.push((c.y, c.x, v, novo));
    }
    put_changes(w, &changed, &trocas);
    Ok(())
}

fn op_colunas(lines: &[&[u8]], w: &mut W) -> R<()> {
    let cs = cells(lines)?;
    let mut ordem: Vec<i64> = Vec::new();
    let mut out: HashMap<i64, &[u8]> = HashMap::default();
    let mut usadas: HashSet<i64> = HashSet::default();
    for c in &cs {
        let k = c.k.map(|r| &lines[c.i][r.0..r.1]);
        match k {
            Some(k) if c.y == 1 && !k.is_empty() => {
                if out.insert(c.x, strip_quotes(k)).is_none() {
                    ordem.push(c.x);
                }
            }
            Some(_) if c.y != NONE && c.y > 1 => {
                usadas.insert(c.x);
            }
            _ => {}
        }
    }
    w.int(ordem.len() as i64);
    for &x in &ordem {
        w.int(x);
        w.bytes(out[&x]);
    }
    let vazias: Vec<i64> = ordem.iter().copied().filter(|x| !usadas.contains(x)).collect();
    w.int(vazias.len() as i64);
    for x in vazias {
        w.int(x);
    }
    Ok(())
}

struct Out {
    blob: Vec<u8>,
    n: usize,
    b_line: Option<(usize, usize)>,
}

impl Out {
    fn new(cap: usize) -> Out {
        Out { blob: Vec::with_capacity(cap), n: 0, b_line: None }
    }
    fn start(&mut self) {
        if self.n > 0 {
            self.blob.push(b'\n');
        }
        self.n += 1;
    }
    fn line(&mut self, l: &[u8]) {
        self.start();
        let s = self.blob.len();
        self.blob.extend_from_slice(l);
        if self.b_line.is_none() && l.starts_with(b"B;") {
            self.b_line = Some((s, self.blob.len()));
        }
    }
    fn num(&mut self, v: i64) {
        let mut buf = [0u8; 20];
        let mut i = buf.len();
        let neg = v < 0;
        let mut u = v.unsigned_abs();
        loop {
            i -= 1;
            buf[i] = b'0' + (u % 10) as u8;
            u /= 10;
            if u == 0 {
                break;
            }
        }
        if neg {
            self.blob.push(b'-');
        }
        self.blob.extend_from_slice(&buf[i..]);
    }
    fn cell(&mut self, x: i64, y: i64, k: &[u8]) -> R<()> {
        if x == NONE || y == NONE {
            return Err(Refuse);
        }
        self.start();
        self.blob.extend_from_slice(b"C;X");
        self.num(x);
        self.blob.extend_from_slice(b";Y");
        self.num(y);
        self.blob.extend_from_slice(b";K");
        self.blob.extend_from_slice(k);
        Ok(())
    }
    fn finish(mut self, n: i64, w: &mut W) -> R<()> {
        if let Some((s, e)) = self.b_line {
            if let Some(nl) = fix_b(&self.blob[s..e], n)? {
                self.blob.splice(s..e, nl);
            }
        }
        w.int(self.n as i64);
        w.bytes(&self.blob);
        Ok(())
    }
}

fn fix_b(l: &[u8], n: i64) -> R<Option<Vec<u8>>> {
    if n == NONE {
        return Err(Refuse);
    }
    let mut i = 0;
    while i < l.len() {
        if l[i] == b'X' && i + 1 < l.len() {
            let c = l[i + 1];
            if c >= 0x80 {
                return Err(Refuse);
            }
            if c.is_ascii_digit() {
                let mut j = i + 1;
                while j < l.len() && l[j].is_ascii_digit() {
                    j += 1;
                }
                if j < l.len() && l[j] >= 0x80 {
                    return Err(Refuse);
                }
                let mut nl = l[..i].to_vec();
                nl.extend_from_slice(format!("X{}", n).as_bytes());
                nl.extend_from_slice(&l[j..]);
                return Ok(Some(nl));
            }
        }
        i += 1;
    }
    Ok(None)
}

fn op_filtra(text_len: usize, lines: &[&[u8]], arg: &mut Rd, w: &mut W) -> R<()> {
    let n = arg.int()?;
    let m = arg.count()?;
    let mut novo_x: HashMap<i64, i64> = HashMap::default();
    for _ in 0..m {
        let a = arg.int()?;
        let b = arg.int()?;
        novo_x.insert(a, b);
    }
    let mut saida = Out::new(text_len + text_len / 4);
    let (mut cx, mut cy) = (NONE, NONE);
    for l in lines {
        if !l.starts_with(b"C;") {
            saida.line(l);
            continue;
        }
        let (x, y, k) = record(l)?;
        if let Some(v) = x {
            cx = v;
        }
        if let Some(v) = y {
            cy = v;
        }
        let nx = match novo_x.get(&cx) {
            Some(&v) => v,
            None => continue,
        };
        let k = match k {
            Some(r) => &l[r.0..r.1],
            None => continue,
        };
        saida.cell(nx, cy, k)?;
    }
    saida.finish(n, w)
}

fn op_acrescenta(text_len: usize, lines: &[&[u8]], arg: &mut Rd, w: &mut W) -> R<()> {
    let prox = arg.int()?;
    let np = arg.count()?;
    let mut plano: Vec<(i64, Vec<(i64, &[u8])>)> = Vec::with_capacity(np);
    for _ in 0..np {
        let x4 = arg.int()?;
        let nn = arg.count()?;
        let mut novos = Vec::with_capacity(nn);
        for _ in 0..nn {
            let xn = arg.int()?;
            let nome = arg.bytes()?;
            novos.push((xn, nome));
        }
        plano.push((x4, novos));
    }
    let cel = cells(lines)?;
    let mut nivel4: HashMap<(i64, i64), &[u8]> = HashMap::default();
    for c in &cel {
        if let Some(r) = c.k {
            if c.y != NONE && c.y > 1 {
                nivel4.insert((c.y, c.x), &lines[c.i][r.0..r.1]);
            }
        }
    }
    let novas = |y: i64, out: &mut Out| -> R<usize> {
        let mut n = 0;
        for (x4, novos) in &plano {
            for (xn, nome) in novos {
                if y == 1 {
                    out.start();
                    out.blob.extend_from_slice(b"C;X");
                    out.num(*xn);
                    out.blob.extend_from_slice(b";Y1;K\"");
                    out.blob.extend_from_slice(nome);
                    out.blob.push(b'"');
                    n += 1;
                } else if let Some(k) = nivel4.get(&(y, *x4)) {
                    out.cell(*xn, y, k)?;
                    n += 1;
                }
            }
        }
        Ok(n)
    };
    let mut saida = Out::new(text_len + text_len / 2);
    let mut atual: Option<i64> = None;
    let mut copiadas = 0usize;
    let mut ci = 0;
    for (i, l) in lines.iter().enumerate() {
        if ci < cel.len() && cel[ci].i == i {
            let c = &cel[ci];
            ci += 1;
            if let Some(a) = atual {
                if a != NONE && c.y != a {
                    copiadas += novas(a, &mut saida)?;
                }
            }
            atual = Some(c.y);
            if let Some(r) = c.k {
                saida.cell(c.x, c.y, &l[r.0..r.1])?;
            }
        } else {
            if l.starts_with(b"E") {
                if let Some(a) = atual {
                    if a != NONE {
                        copiadas += novas(a, &mut saida)?;
                        atual = None;
                    }
                }
            }
            saida.line(l);
        }
    }
    if let Some(a) = atual {
        if a != NONE {
            copiadas += novas(a, &mut saida)?;
        }
    }
    w.int(copiadas as i64);
    saida.finish(prox, w)
}

fn run(op: u32, text: &[u8], arg: &[u8]) -> R<Vec<u8>> {
    let lines = split_lines(text);
    let mut w = W(Vec::new());
    let mut rd = Rd { b: arg, p: 0 };
    match op {
        1 => op_numeros(&lines, &mut w)?,
        2 => op_nomes(&lines, &mut w)?,
        3 => op_listas(&lines, &mut rd, &mut w)?,
        4 => op_colunas(&lines, &mut w)?,
        5 => op_filtra(text.len(), &lines, &mut rd, &mut w)?,
        6 => op_acrescenta(text.len(), &lines, &mut rd, &mut w)?,
        _ => return Err(Refuse),
    }
    Ok(w.0)
}

#[no_mangle]
pub extern "C" fn slk_pass(
    op: u32,
    text: *const u8,
    len: usize,
    arg: *const u8,
    arg_len: usize,
    out: *mut *mut u8,
    out_len: *mut usize,
) -> i32 {
    if (text.is_null() && len > 0) || (arg.is_null() && arg_len > 0) || out.is_null() || out_len.is_null() {
        return 3;
    }
    let t: &[u8] = if len == 0 { &[] } else { unsafe { std::slice::from_raw_parts(text, len) } };
    let a: &[u8] = if arg_len == 0 { &[] } else { unsafe { std::slice::from_raw_parts(arg, arg_len) } };
    match panic::catch_unwind(|| run(op, t, a)) {
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
