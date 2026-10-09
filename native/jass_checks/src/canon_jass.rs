// The JASS parser, its normal form and its parentheses in Rust.
use std::cell::Cell;
use std::collections::{HashMap, HashSet};
use std::hash::{BuildHasherDefault, Hasher};
use std::panic;
use std::sync::{Arc, Mutex};

#[derive(Default, Clone, Copy)]
pub struct FxHasher(u64);
const SEED: u64 = 0x51_7c_c1_b7_27_22_0a_95;

impl FxHasher {
    #[inline]
    fn add(&mut self, w: u64) {
        self.0 = (self.0.rotate_left(5) ^ w).wrapping_mul(SEED);
    }
}

impl Hasher for FxHasher {
    #[inline]
    fn write(&mut self, bytes: &[u8]) {
        let mut b = bytes;
        while b.len() >= 8 {
            self.add(u64::from_le_bytes([b[0], b[1], b[2], b[3], b[4], b[5], b[6], b[7]]));
            b = &b[8..];
        }
        if b.len() >= 4 {
            self.add(u32::from_le_bytes([b[0], b[1], b[2], b[3]]) as u64);
            b = &b[4..];
        }
        for &x in b {
            self.add(x as u64);
        }
    }
    #[inline]
    fn write_u8(&mut self, i: u8) {
        self.add(i as u64)
    }
    #[inline]
    fn write_usize(&mut self, i: usize) {
        self.add(i as u64)
    }
    #[inline]
    fn finish(&self) -> u64 {
        self.0
    }
}

type Fx = BuildHasherDefault<FxHasher>;
type FxMap<K, V> = HashMap<K, V, Fx>;
type FxSet<K> = HashSet<K, Fx>;

const DEEP: u32 = 3000;

thread_local! {
    static DEPTH: Cell<u32> = const { Cell::new(0) };
    static REFUSE: Cell<bool> = const { Cell::new(false) };
}

struct Guard;

impl Guard {
    #[inline]
    fn enter() -> Guard {
        DEPTH.with(|d| {
            let v = d.get() + 1;
            d.set(v);
            if v > DEEP {
                REFUSE.with(|r| r.set(true));
            }
        });
        Guard
    }
}

impl Drop for Guard {
    #[inline]
    fn drop(&mut self) {
        DEPTH.with(|d| d.set(d.get() - 1));
    }
}

#[inline]
fn refused() -> bool {
    REFUSE.with(|r| r.get())
}

fn refuse() {
    REFUSE.with(|r| r.set(true));
}

fn reset_refusal() {
    REFUSE.with(|r| r.set(false));
    DEPTH.with(|d| d.set(0));
}

#[derive(Clone)]
pub enum S<'a> {
    B(&'a [u8]),
    O(Arc<[u8]>),
}

impl<'a> std::ops::Deref for S<'a> {
    type Target = [u8];
    #[inline]
    fn deref(&self) -> &[u8] {
        match self {
            S::B(b) => b,
            S::O(o) => o,
        }
    }
}

fn owned(v: Vec<u8>) -> S<'static> {
    S::O(Arc::from(v))
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Op {
    And,
    Or,
    Eq,
    Ne,
    Lt,
    Le,
    Gt,
    Ge,
    Add,
    Sub,
    Mul,
    Div,
    Not,
}

impl Op {
    fn prec(self) -> u32 {
        match self {
            Op::And => 1,
            Op::Or => 2,
            Op::Eq | Op::Ne | Op::Lt | Op::Le | Op::Gt | Op::Ge => 3,
            Op::Add | Op::Sub => 5,
            Op::Mul | Op::Div => 6,
            Op::Not => 0,
        }
    }
    fn text(self) -> &'static [u8] {
        match self {
            Op::And => b"and",
            Op::Or => b"or",
            Op::Eq => b"==",
            Op::Ne => b"!=",
            Op::Lt => b"<",
            Op::Le => b"<=",
            Op::Gt => b">",
            Op::Ge => b">=",
            Op::Add => b"+",
            Op::Sub => b"-",
            Op::Mul => b"*",
            Op::Div => b"/",
            Op::Not => b"not",
        }
    }
    fn code(self) -> i32 {
        self as i32
    }
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum LK {
    Integer,
    Real,
    Str,
    Raw,
    Bool,
    Null,
}

pub type P<'a> = Arc<E<'a>>;

pub enum E<'a> {
    Name(S<'a>, u32),
    Index(P<'a>, P<'a>, u32),
    Call(S<'a>, Vec<P<'a>>, u32),
    FuncRef(S<'a>, u32),
    Lit(LK, S<'a>, u32),
    Unary(Op, P<'a>, u32),
    Binary(Op, P<'a>, P<'a>, u32),
    Paren(P<'a>, u32),
}

impl<'a> E<'a> {
    fn line(&self) -> u32 {
        match self {
            E::Name(_, l)
            | E::Index(_, _, l)
            | E::Call(_, _, l)
            | E::FuncRef(_, l)
            | E::Lit(_, _, l)
            | E::Unary(_, _, l)
            | E::Binary(_, _, _, l)
            | E::Paren(_, l) => *l,
        }
    }
}

pub struct IfS<'a> {
    branches: Vec<(Option<P<'a>>, Vec<St<'a>>)>,
    line: u32,
    comment: Option<S<'a>>,
    branch_lines: Vec<u32>,
    branch_comments: Vec<Option<S<'a>>>,
    end_line: u32,
    end_comment: Option<S<'a>>,
}

pub enum St<'a> {
    Set { target: P<'a>, value: P<'a>, line: u32, comment: Option<S<'a>> },
    Call { call: P<'a>, line: u32, comment: Option<S<'a>> },
    If(Box<IfS<'a>>),
    Loop { body: Vec<St<'a>>, line: u32, comment: Option<S<'a>>, end_line: u32, end_comment: Option<S<'a>> },
    Exit { cond: P<'a>, line: u32, comment: Option<S<'a>> },
    Ret { value: Option<P<'a>>, line: u32, comment: Option<S<'a>> },
    Comment { text: S<'a>, line: u32 },
    Debug { stmt: Box<St<'a>>, line: u32 },
}

pub struct Decl<'a> {
    name: S<'a>,
    ty: S<'a>,
    is_array: bool,
    is_constant: bool,
    init: Option<P<'a>>,
    line: u32,
    comment: Option<S<'a>>,
    leading: Vec<S<'a>>,
}

pub struct Globals<'a> {
    decls: Vec<Decl<'a>>,
    line: u32,
    end_line: u32,
    comment: Option<S<'a>>,
    end_comment: Option<S<'a>>,
    leading: Vec<S<'a>>,
    end_comments: Vec<S<'a>>,
}

pub struct Func<'a> {
    name: S<'a>,
    params: Vec<(S<'a>, S<'a>)>,
    ret: S<'a>,
    locals: Vec<Decl<'a>>,
    body: Vec<St<'a>>,
    line: u32,
    end_line: u32,
    is_native: bool,
    is_constant: bool,
    comment: Option<S<'a>>,
    end_comment: Option<S<'a>>,
    leading: Vec<S<'a>>,
}

pub struct TypeD<'a> {
    name: S<'a>,
    base: S<'a>,
    line: u32,
    comment: Option<S<'a>>,
    leading: Vec<S<'a>>,
}

pub enum Item<'a> {
    Type(TypeD<'a>),
    Globals(Globals<'a>),
    Func(Func<'a>),
}

pub struct Script<'a> {
    items: Vec<Item<'a>>,
    comments: Vec<(S<'a>, u32)>,
    end_comments: Vec<S<'a>>,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
enum Kw {
    Globals,
    Endglobals,
    Native,
    Constant,
    Type,
    Extends,
    Function,
    Endfunction,
    Takes,
    Returns,
    Nothing,
    Local,
    Array,
    Set,
    Call,
    If,
    Then,
    Elseif,
    Else,
    Endif,
    Loop,
    Endloop,
    Exitwhen,
    Return,
    Debug,
    And,
    Or,
    Not,
    True,
    False,
    Null,
}

fn keyword(w: &[u8]) -> Option<Kw> {
    Some(match w {
        b"globals" => Kw::Globals,
        b"endglobals" => Kw::Endglobals,
        b"native" => Kw::Native,
        b"constant" => Kw::Constant,
        b"type" => Kw::Type,
        b"extends" => Kw::Extends,
        b"function" => Kw::Function,
        b"endfunction" => Kw::Endfunction,
        b"takes" => Kw::Takes,
        b"returns" => Kw::Returns,
        b"nothing" => Kw::Nothing,
        b"local" => Kw::Local,
        b"array" => Kw::Array,
        b"set" => Kw::Set,
        b"call" => Kw::Call,
        b"if" => Kw::If,
        b"then" => Kw::Then,
        b"elseif" => Kw::Elseif,
        b"else" => Kw::Else,
        b"endif" => Kw::Endif,
        b"loop" => Kw::Loop,
        b"endloop" => Kw::Endloop,
        b"exitwhen" => Kw::Exitwhen,
        b"return" => Kw::Return,
        b"debug" => Kw::Debug,
        b"and" => Kw::And,
        b"or" => Kw::Or,
        b"not" => Kw::Not,
        b"true" => Kw::True,
        b"false" => Kw::False,
        b"null" => Kw::Null,
        _ => return None,
    })
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
enum K {
    Ident,
    Kw(Kw),
    Nl,
    Comment,
    LP,
    RP,
    Comma,
    LB,
    RB,
    Assign,
    Op(Op),
    Num,
    Str,
    Raw,
    Other,
    Eof,
}

#[derive(Clone, Copy)]
struct Tok {
    k: K,
    s: u32,
    e: u32,
}

#[inline]
fn is_word(c: u8) -> bool {
    c.is_ascii_alphanumeric() || c == b'_'
}

fn char_len(src: &[u8], i: usize) -> usize {
    let c = src[i];
    let n = if c < 0x80 {
        return 1;
    } else if c & 0xE0 == 0xC0 {
        2
    } else if c & 0xF0 == 0xE0 {
        3
    } else if c & 0xF8 == 0xF0 {
        4
    } else {
        return 1;
    };
    if i + n <= src.len() && std::str::from_utf8(&src[i..i + n]).is_ok() {
        n
    } else {
        1
    }
}

fn py_chars(b: &[u8]) -> usize {
    let mut n = 0;
    let mut rest = b;
    loop {
        match std::str::from_utf8(rest) {
            Ok(s) => return n + s.chars().count(),
            Err(e) => {
                let good = e.valid_up_to();
                n += unsafe { std::str::from_utf8_unchecked(&rest[..good]) }.chars().count();
                let bad = e.error_len().unwrap_or(rest.len() - good);
                n += bad;
                rest = &rest[good + bad..];
            }
        }
    }
}

const BOM: &[u8] = b"\xEF\xBB\xBF";

fn tokenize(src: &[u8]) -> Vec<Tok> {
    let n = src.len();
    let mut out: Vec<Tok> = Vec::with_capacity(n / 3 + 1);
    let mut i = 0usize;
    let at = |j: usize| -> u8 {
        if j < n {
            src[j]
        } else {
            0
        }
    };
    loop {
        loop {
            if i < n && (src[i] == b' ' || src[i] == b'\t') {
                i += 1;
            } else if i + 3 <= n && &src[i..i + 3] == BOM {
                i += 3;
            } else {
                break;
            }
        }
        if i >= n {
            break;
        }
        let st = i;
        let c = src[i];
        let k = match c {
            b'A'..=b'Z' | b'a'..=b'z' | b'_' => {
                i += 1;
                while i < n && is_word(src[i]) {
                    i += 1;
                }
                match keyword(&src[st..i]) {
                    Some(kw) => K::Kw(kw),
                    None => K::Ident,
                }
            }
            b'(' => {
                i += 1;
                K::LP
            }
            b')' => {
                i += 1;
                K::RP
            }
            b',' => {
                i += 1;
                K::Comma
            }
            b'\r' => {
                i += 1;
                if at(i) == b'\n' {
                    i += 1;
                }
                K::Nl
            }
            b'\n' => {
                i += 1;
                K::Nl
            }
            b'=' | b'!' | b'<' | b'>' if at(i + 1) == b'=' => {
                i += 2;
                K::Op(match c {
                    b'=' => Op::Eq,
                    b'!' => Op::Ne,
                    b'<' => Op::Le,
                    _ => Op::Ge,
                })
            }
            b'/' if at(i + 1) == b'/' => {
                i += 2;
                while i < n && src[i] != b'\r' && src[i] != b'\n' {
                    i += 1;
                }
                K::Comment
            }
            b'-' | b'+' | b'*' | b'/' | b'<' | b'>' | b'=' | b'[' | b']' => {
                i += 1;
                match c {
                    b'-' => K::Op(Op::Sub),
                    b'+' => K::Op(Op::Add),
                    b'*' => K::Op(Op::Mul),
                    b'/' => K::Op(Op::Div),
                    b'<' => K::Op(Op::Lt),
                    b'>' => K::Op(Op::Gt),
                    b'=' => K::Assign,
                    b'[' => K::LB,
                    _ => K::RB,
                }
            }
            b'0' if (at(i + 1) == b'x' || at(i + 1) == b'X') && at(i + 2).is_ascii_hexdigit() => {
                i += 3;
                while i < n && src[i].is_ascii_hexdigit() {
                    i += 1;
                }
                K::Num
            }
            b'$' if at(i + 1).is_ascii_hexdigit() => {
                i += 2;
                while i < n && src[i].is_ascii_hexdigit() {
                    i += 1;
                }
                K::Num
            }
            b'0'..=b'9' => {
                while i < n && src[i].is_ascii_digit() {
                    i += 1;
                }
                if at(i) == b'.' {
                    i += 1;
                    while i < n && src[i].is_ascii_digit() {
                        i += 1;
                    }
                }
                K::Num
            }
            b'.' if at(i + 1).is_ascii_digit() => {
                i += 2;
                while i < n && src[i].is_ascii_digit() {
                    i += 1;
                }
                K::Num
            }
            b'"' | b'\'' => {
                let mut j = i + 1;
                let mut closed = false;
                while j < n {
                    let d = src[j];
                    if d == c {
                        closed = true;
                        break;
                    }
                    if d == b'\\' {
                        if j + 1 >= n {
                            break;
                        }
                        j += 2;
                    } else {
                        j += 1;
                    }
                }
                if closed {
                    i = j + 1;
                    if c == b'"' {
                        K::Str
                    } else {
                        K::Raw
                    }
                } else {
                    i += 1;
                    K::Other
                }
            }
            _ => {
                i += char_len(src, i);
                K::Other
            }
        };
        out.push(Tok { k, s: st as u32, e: i as u32 });
    }
    out.push(Tok { k: K::Eof, s: n as u32, e: n as u32 });
    out
}

fn line_breaks(t: &[u8]) -> u32 {
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

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Fail {
    Syntax,
    Deep,
}

type R<T> = Result<T, Fail>;

#[derive(Clone, Copy, PartialEq, Eq)]
enum Enders {
    Function,
    If,
    Else,
    Loop,
}

impl Enders {
    fn has(self, k: K) -> bool {
        match self {
            Enders::Function => k == K::Kw(Kw::Endfunction),
            Enders::If => matches!(k, K::Kw(Kw::Elseif) | K::Kw(Kw::Else) | K::Kw(Kw::Endif)),
            Enders::Else => k == K::Kw(Kw::Endif),
            Enders::Loop => k == K::Kw(Kw::Endloop),
        }
    }
}

struct Parser<'a> {
    src: &'a [u8],
    toks: Vec<Tok>,
    i: usize,
    line: u32,
    depth: u32,
}

fn is_handler(k: K) -> bool {
    matches!(
        k,
        K::Kw(Kw::Set) | K::Kw(Kw::Call) | K::Kw(Kw::If) | K::Kw(Kw::Loop) | K::Kw(Kw::Exitwhen) | K::Kw(Kw::Return)
            | K::Kw(Kw::Debug)
    )
}

fn binop(k: K) -> Option<Op> {
    match k {
        K::Kw(Kw::And) => Some(Op::And),
        K::Kw(Kw::Or) => Some(Op::Or),
        K::Op(op) => Some(op),
        _ => None,
    }
}

impl<'a> Parser<'a> {
    #[inline]
    fn cur(&self) -> Tok {
        self.toks[self.i]
    }
    #[inline]
    fn text(&self, t: Tok) -> S<'a> {
        S::B(&self.src[t.s as usize..t.e as usize])
    }
    fn enter(&mut self) -> R<()> {
        self.depth += 1;
        if self.depth > DEEP {
            Err(Fail::Deep)
        } else {
            Ok(())
        }
    }
    fn expect(&mut self, k: K) -> R<()> {
        if self.cur().k != k {
            return Err(Fail::Syntax);
        }
        self.i += 1;
        Ok(())
    }
    fn identifier(&mut self) -> R<S<'a>> {
        let t = self.cur();
        if t.k == K::Ident {
            self.i += 1;
            Ok(self.text(t))
        } else {
            Err(Fail::Syntax)
        }
    }
    fn end_of_line(&mut self) -> R<Option<S<'a>>> {
        let mut t = self.cur();
        let mut comment = None;
        if t.k == K::Comment {
            comment = Some(self.text(t));
            self.i += 1;
            t = self.cur();
        }
        if t.k == K::Nl {
            self.i += 1;
            self.line += 1;
        } else if t.k != K::Eof {
            return Err(Fail::Syntax);
        }
        Ok(comment)
    }

    fn script(&mut self) -> R<Script<'a>> {
        let mut s = Script { items: Vec::new(), comments: Vec::new(), end_comments: Vec::new() };
        let mut pending: Vec<S<'a>> = Vec::new();
        loop {
            let mut t = self.cur();
            match t.k {
                K::Nl => {
                    self.i += 1;
                    self.line += 1;
                    continue;
                }
                K::Eof => break,
                K::Comment => {
                    s.comments.push((self.text(t), self.line));
                    pending.push(self.text(t));
                    self.i += 1;
                    self.end_of_line()?;
                    continue;
                }
                _ => {}
            }
            let line = self.line;
            let is_constant = t.k == K::Kw(Kw::Constant);
            if is_constant {
                self.i += 1;
                t = self.cur();
            }
            let leading = std::mem::take(&mut pending);
            let item = match t.k {
                K::Kw(Kw::Function) => {
                    let mut f = self.function(line, is_constant)?;
                    f.leading = leading;
                    Item::Func(f)
                }
                K::Kw(Kw::Native) => {
                    let mut f = self.native(line, is_constant)?;
                    f.leading = leading;
                    Item::Func(f)
                }
                K::Kw(Kw::Globals) if !is_constant => {
                    let mut g = self.globals_block()?;
                    g.leading = leading;
                    Item::Globals(g)
                }
                K::Kw(Kw::Type) if !is_constant => {
                    let mut d = self.type_decl()?;
                    d.leading = leading;
                    Item::Type(d)
                }
                _ => return Err(Fail::Syntax),
            };
            s.items.push(item);
        }
        s.end_comments = pending;
        Ok(s)
    }

    fn type_decl(&mut self) -> R<TypeD<'a>> {
        let line = self.line;
        self.i += 1;
        let name = self.identifier()?;
        self.expect(K::Kw(Kw::Extends))?;
        let base = self.identifier()?;
        let comment = self.end_of_line()?;
        Ok(TypeD { name, base, line, comment, leading: Vec::new() })
    }

    fn globals_block(&mut self) -> R<Globals<'a>> {
        let mut g = Globals {
            decls: Vec::new(),
            line: self.line,
            end_line: self.line,
            comment: None,
            end_comment: None,
            leading: Vec::new(),
            end_comments: Vec::new(),
        };
        self.i += 1;
        g.comment = self.end_of_line()?;
        let mut pending: Vec<S<'a>> = Vec::new();
        loop {
            let t = self.cur();
            match t.k {
                K::Nl => {
                    self.i += 1;
                    self.line += 1;
                    continue;
                }
                K::Comment => {
                    pending.push(self.text(t));
                    self.i += 1;
                    self.end_of_line()?;
                    continue;
                }
                K::Kw(Kw::Endglobals) => {
                    g.end_line = self.line;
                    g.end_comments = pending;
                    self.i += 1;
                    g.end_comment = self.end_of_line()?;
                    return Ok(g);
                }
                K::Eof => return Err(Fail::Syntax),
                _ => {}
            }
            let line = self.line;
            let is_constant = t.k == K::Kw(Kw::Constant);
            if is_constant {
                self.i += 1;
            }
            let ty = self.identifier()?;
            let is_array = self.cur().k == K::Kw(Kw::Array);
            if is_array {
                self.i += 1;
            }
            let name = self.identifier()?;
            let mut init = None;
            if self.cur().k == K::Assign {
                self.i += 1;
                init = Some(self.expression(0)?);
            }
            let leading = std::mem::take(&mut pending);
            let comment = self.end_of_line()?;
            g.decls.push(Decl { name, ty, is_array, is_constant, init, line, comment, leading });
        }
    }

    fn signature(&mut self, f: &mut Func<'a>) -> R<()> {
        f.name = self.identifier()?;
        self.expect(K::Kw(Kw::Takes))?;
        if self.cur().k == K::Kw(Kw::Nothing) {
            self.i += 1;
        } else {
            loop {
                let ptype = self.identifier()?;
                let pname = self.identifier()?;
                f.params.push((ptype, pname));
                if self.cur().k != K::Comma {
                    break;
                }
                self.i += 1;
            }
        }
        self.expect(K::Kw(Kw::Returns))?;
        if self.cur().k == K::Kw(Kw::Nothing) {
            self.i += 1;
        } else {
            f.ret = self.identifier()?;
        }
        f.comment = self.end_of_line()?;
        Ok(())
    }

    fn new_func(line: u32, is_native: bool, is_constant: bool) -> Func<'a> {
        Func {
            name: S::B(b""),
            params: Vec::new(),
            ret: S::B(b"nothing"),
            locals: Vec::new(),
            body: Vec::new(),
            line,
            end_line: line,
            is_native,
            is_constant,
            comment: None,
            end_comment: None,
            leading: Vec::new(),
        }
    }

    fn native(&mut self, line: u32, is_constant: bool) -> R<Func<'a>> {
        self.i += 1;
        let mut f = Self::new_func(line, true, is_constant);
        self.signature(&mut f)?;
        Ok(f)
    }

    fn function(&mut self, line: u32, is_constant: bool) -> R<Func<'a>> {
        self.i += 1;
        let mut f = Self::new_func(line, false, is_constant);
        self.signature(&mut f)?;
        let mut pending: Vec<St<'a>> = Vec::new();
        loop {
            let t = self.cur();
            match t.k {
                K::Nl => {
                    self.i += 1;
                    self.line += 1;
                }
                K::Comment => {
                    pending.push(St::Comment { text: self.text(t), line: self.line });
                    self.i += 1;
                    self.end_of_line()?;
                }
                K::Kw(Kw::Local) => {
                    let mut d = self.local_decl()?;
                    d.leading = pending
                        .iter()
                        .map(|c| match c {
                            St::Comment { text, .. } => text.clone(),
                            _ => unreachable!(),
                        })
                        .collect();
                    pending.clear();
                    f.locals.push(d);
                }
                _ => break,
            }
        }
        f.body = self.block(pending, Enders::Function)?;
        f.end_line = self.line;
        self.i += 1;
        f.end_comment = self.end_of_line()?;
        Ok(f)
    }

    fn local_decl(&mut self) -> R<Decl<'a>> {
        let line = self.line;
        self.i += 1;
        let ty = self.identifier()?;
        let is_array = self.cur().k == K::Kw(Kw::Array);
        if is_array {
            self.i += 1;
        }
        let name = self.identifier()?;
        let mut init = None;
        if self.cur().k == K::Assign {
            self.i += 1;
            init = Some(self.expression(0)?);
        }
        let comment = self.end_of_line()?;
        Ok(Decl { name, ty, is_array, is_constant: false, init, line, comment, leading: Vec::new() })
    }

    fn block(&mut self, mut body: Vec<St<'a>>, enders: Enders) -> R<Vec<St<'a>>> {
        self.enter()?;
        loop {
            let t = self.cur();
            if t.k == K::Nl {
                self.i += 1;
                self.line += 1;
                continue;
            }
            if is_handler(t.k) {
                let s = self.statement(t.k)?;
                body.push(s);
            } else if enders.has(t.k) {
                self.depth -= 1;
                return Ok(body);
            } else if t.k == K::Comment {
                body.push(St::Comment { text: self.text(t), line: self.line });
                self.i += 1;
                self.end_of_line()?;
            } else {
                return Err(Fail::Syntax);
            }
        }
    }

    fn statement(&mut self, k: K) -> R<St<'a>> {
        match k {
            K::Kw(Kw::Set) => self.set_stmt(),
            K::Kw(Kw::Call) => self.call_stmt(),
            K::Kw(Kw::If) => self.if_stmt(),
            K::Kw(Kw::Loop) => self.loop_stmt(),
            K::Kw(Kw::Exitwhen) => self.exitwhen_stmt(),
            K::Kw(Kw::Return) => self.return_stmt(),
            K::Kw(Kw::Debug) => self.debug_stmt(),
            _ => Err(Fail::Syntax),
        }
    }

    fn set_stmt(&mut self) -> R<St<'a>> {
        let line = self.line;
        self.i += 1;
        let mut target: P<'a> = Arc::new(E::Name(self.identifier()?, line));
        if self.cur().k == K::LB {
            self.i += 1;
            let index = self.expression(0)?;
            target = Arc::new(E::Index(target, index, line));
            self.expect(K::RB)?;
        }
        self.expect(K::Assign)?;
        let value = self.expression(0)?;
        let comment = self.end_of_line()?;
        Ok(St::Set { target, value, line, comment })
    }

    fn call_stmt(&mut self) -> R<St<'a>> {
        let line = self.line;
        self.i += 1;
        let name = self.identifier()?;
        self.expect(K::LP)?;
        let args = self.arguments()?;
        let call = Arc::new(E::Call(name, args, line));
        let comment = self.end_of_line()?;
        Ok(St::Call { call, line, comment })
    }

    fn if_stmt(&mut self) -> R<St<'a>> {
        let line = self.line;
        self.i += 1;
        let cond = self.expression(0)?;
        self.expect(K::Kw(Kw::Then))?;
        let comment = self.end_of_line()?;
        let mut s = IfS {
            branches: Vec::new(),
            line,
            comment: comment.clone(),
            branch_lines: vec![line],
            branch_comments: vec![comment],
            end_line: line,
            end_comment: None,
        };
        let body = self.block(Vec::new(), Enders::If)?;
        s.branches.push((Some(cond), body));
        loop {
            let t = self.cur();
            let branch_line = self.line;
            self.i += 1;
            if t.k == K::Kw(Kw::Elseif) {
                let cond = self.expression(0)?;
                self.expect(K::Kw(Kw::Then))?;
                let c = self.end_of_line()?;
                s.branch_comments.push(c);
                s.branch_lines.push(branch_line);
                let body = self.block(Vec::new(), Enders::If)?;
                s.branches.push((Some(cond), body));
            } else if t.k == K::Kw(Kw::Else) {
                let c = self.end_of_line()?;
                s.branch_comments.push(c);
                s.branch_lines.push(branch_line);
                let body = self.block(Vec::new(), Enders::Else)?;
                s.branches.push((None, body));
            } else {
                s.end_line = branch_line;
                s.end_comment = self.end_of_line()?;
                return Ok(St::If(Box::new(s)));
            }
        }
    }

    fn loop_stmt(&mut self) -> R<St<'a>> {
        let line = self.line;
        self.i += 1;
        let comment = self.end_of_line()?;
        let body = self.block(Vec::new(), Enders::Loop)?;
        let end_line = self.line;
        self.i += 1;
        let end_comment = self.end_of_line()?;
        Ok(St::Loop { body, line, comment, end_line, end_comment })
    }

    fn exitwhen_stmt(&mut self) -> R<St<'a>> {
        let line = self.line;
        self.i += 1;
        let cond = self.expression(0)?;
        let comment = self.end_of_line()?;
        Ok(St::Exit { cond, line, comment })
    }

    fn return_stmt(&mut self) -> R<St<'a>> {
        let line = self.line;
        self.i += 1;
        let k = self.cur().k;
        let mut value = None;
        if k != K::Nl && k != K::Eof && k != K::Comment {
            value = Some(self.expression(0)?);
        }
        let comment = self.end_of_line()?;
        Ok(St::Ret { value, line, comment })
    }

    fn debug_stmt(&mut self) -> R<St<'a>> {
        let line = self.line;
        self.i += 1;
        let k = self.cur().k;
        if !is_handler(k) || k == K::Kw(Kw::Debug) {
            return Err(Fail::Syntax);
        }
        let stmt = self.statement(k)?;
        Ok(St::Debug { stmt: Box::new(stmt), line })
    }

    fn expression(&mut self, min_precedence: u32) -> R<P<'a>> {
        self.enter()?;
        let mut left = self.unary()?;
        loop {
            match binop(self.cur().k) {
                Some(op) if op.prec() >= min_precedence => {
                    self.i += 1;
                    let right = self.expression(op.prec() + 1)?;
                    let line = left.line();
                    left = Arc::new(E::Binary(op, left, right, line));
                }
                _ => break,
            }
        }
        self.depth -= 1;
        Ok(left)
    }

    fn unary(&mut self) -> R<P<'a>> {
        self.enter()?;
        let r = self.unary_inner();
        self.depth -= 1;
        r
    }

    fn unary_inner(&mut self) -> R<P<'a>> {
        let i = self.i;
        let t = self.toks[i];
        let line = self.line;
        match t.k {
            K::Ident => {
                let nxt = self.toks[i + 1].k;
                if nxt == K::LP {
                    self.i = i + 2;
                    let args = self.arguments()?;
                    return Ok(Arc::new(E::Call(self.text(t), args, line)));
                }
                if nxt == K::LB {
                    self.i = i + 2;
                    let index = self.expression(0)?;
                    let e = Arc::new(E::Index(Arc::new(E::Name(self.text(t), line)), index, line));
                    self.expect(K::RB)?;
                    return Ok(e);
                }
                self.i = i + 1;
                Ok(Arc::new(E::Name(self.text(t), line)))
            }
            K::LP => {
                self.i = i + 1;
                let inner = self.expression(0)?;
                self.expect(K::RP)?;
                Ok(Arc::new(E::Paren(inner, line)))
            }
            K::Num => {
                self.i = i + 1;
                let text = self.text(t);
                let kind = if text.contains(&b'.') { LK::Real } else { LK::Integer };
                Ok(Arc::new(E::Lit(kind, text, line)))
            }
            K::Str | K::Raw => {
                self.i = i + 1;
                let text = self.text(t);
                self.line += line_breaks(&text);
                Ok(Arc::new(E::Lit(if t.k == K::Str { LK::Str } else { LK::Raw }, text, line)))
            }
            K::Kw(Kw::Not) => {
                self.i = i + 1;
                let operand = self.expression(5)?;
                Ok(Arc::new(E::Unary(Op::Not, operand, line)))
            }
            K::Op(op @ (Op::Sub | Op::Add)) => {
                self.i = i + 1;
                let operand = self.unary()?;
                Ok(Arc::new(E::Unary(op, operand, line)))
            }
            K::Kw(Kw::True) | K::Kw(Kw::False) => {
                self.i = i + 1;
                Ok(Arc::new(E::Lit(LK::Bool, self.text(t), line)))
            }
            K::Kw(Kw::Null) => {
                self.i = i + 1;
                Ok(Arc::new(E::Lit(LK::Null, self.text(t), line)))
            }
            K::Kw(Kw::Function) => {
                self.i = i + 1;
                let name = self.identifier()?;
                Ok(Arc::new(E::FuncRef(name, line)))
            }
            _ => Err(Fail::Syntax),
        }
    }

    fn arguments(&mut self) -> R<Vec<P<'a>>> {
        if self.cur().k == K::RP {
            self.i += 1;
            return Ok(Vec::new());
        }
        let mut args = vec![self.expression(0)?];
        loop {
            match self.cur().k {
                K::Comma => {
                    self.i += 1;
                    args.push(self.expression(0)?);
                }
                K::RP => {
                    self.i += 1;
                    return Ok(args);
                }
                _ => return Err(Fail::Syntax),
            }
        }
    }
}

pub fn parse(src: &[u8]) -> R<Script<'_>> {
    let mut p = Parser { src, toks: tokenize(src), i: 0, line: 1, depth: 0 };
    p.script()
}

fn needs_parens(child: Op, parent: Op, right: bool) -> bool {
    let (p, q) = (child.prec(), parent.prec());
    p < q || (right && p == q && !(child == parent && matches!(child, Op::Add | Op::Mul | Op::And | Op::Or)))
}

fn ue(e: &E, out: &mut Vec<u8>) {
    let _g = Guard::enter();
    if refused() {
        return;
    }
    match e {
        E::Name(n, _) => out.extend_from_slice(n),
        E::Call(n, args, _) => {
            out.extend_from_slice(n);
            out.push(b'(');
            for (k, a) in args.iter().enumerate() {
                if k > 0 {
                    out.extend_from_slice(b", ");
                }
                ue(a, out);
            }
            out.push(b')');
        }
        E::Lit(_, t, _) => out.extend_from_slice(t),
        E::Binary(..) => {
            let mut chain: Vec<&E> = Vec::new();
            let mut x = e;
            while let E::Binary(_, l, _, _) = x {
                chain.push(x);
                x = l;
            }
            chain.reverse();
            let op_of = |b: &E| match b {
                E::Binary(op, ..) => *op,
                _ => unreachable!(),
            };
            let wraps: Vec<bool> =
                (0..chain.len()).map(|k| k + 1 < chain.len() && needs_parens(op_of(chain[k]), op_of(chain[k + 1]), false)).collect();
            for _ in wraps.iter().filter(|w| **w) {
                out.push(b'(');
            }
            ue(x, out);
            for (k, b) in chain.iter().enumerate() {
                if let E::Binary(op, _, r, _) = b {
                    out.push(b' ');
                    out.extend_from_slice(op.text());
                    out.push(b' ');
                    let wrap = match &**r {
                        E::Binary(rop, ..) => needs_parens(*rop, *op, true),
                        _ => false,
                    };
                    if wrap {
                        out.push(b'(');
                    }
                    ue(r, out);
                    if wrap {
                        out.push(b')');
                    }
                }
                if wraps[k] {
                    out.push(b')');
                }
            }
        }
        E::Paren(inner, _) => {
            out.push(b'(');
            ue(inner, out);
            out.push(b')');
        }
        E::Index(b, i, _) => {
            ue(b, out);
            out.push(b'[');
            ue(i, out);
            out.push(b']');
        }
        E::Unary(op, x, _) => {
            let wrap = match &**x {
                E::Binary(bop, ..) => *op != Op::Not || bop.prec() < 5,
                _ => false,
            };
            if *op == Op::Not {
                out.extend_from_slice(b"not ");
            } else {
                out.extend_from_slice(op.text());
            }
            if wrap {
                out.push(b'(');
            }
            ue(x, out);
            if wrap {
                out.push(b')');
            }
        }
        E::FuncRef(n, _) => {
            out.extend_from_slice(b"function ");
            out.extend_from_slice(n);
        }
    }
}

fn indent(out: &mut Vec<u8>, ind: usize) {
    for _ in 0..ind {
        out.extend_from_slice(b"    ");
    }
}

fn end_line(out: &mut Vec<u8>, comment: &Option<S>, comments: bool) {
    if comments {
        if let Some(c) = comment {
            if !c.is_empty() {
                out.push(b' ');
                out.extend_from_slice(c);
            }
        }
    }
    out.push(b'\n');
}

fn ustmt(s: &St, ind: usize, out: &mut Vec<u8>, comments: bool, prefix: &[u8]) {
    let _g = Guard::enter();
    if refused() {
        return;
    }
    match s {
        St::Call { call, comment, .. } => {
            indent(out, ind);
            out.extend_from_slice(prefix);
            out.extend_from_slice(b"call ");
            ue(call, out);
            end_line(out, comment, comments);
        }
        St::Set { target, value, comment, .. } => {
            indent(out, ind);
            out.extend_from_slice(prefix);
            out.extend_from_slice(b"set ");
            ue(target, out);
            out.extend_from_slice(b" = ");
            ue(value, out);
            end_line(out, comment, comments);
        }
        St::If(s) => {
            for (k, (cond, body)) in s.branches.iter().enumerate() {
                indent(out, ind);
                if k == 0 {
                    out.extend_from_slice(prefix);
                    out.extend_from_slice(b"if ");
                    ue(cond.as_ref().unwrap(), out);
                    out.extend_from_slice(b" then");
                } else if let Some(c) = cond {
                    out.extend_from_slice(b"elseif ");
                    ue(c, out);
                    out.extend_from_slice(b" then");
                } else {
                    out.extend_from_slice(b"else");
                }
                let c = if k == 0 {
                    s.comment.clone()
                } else if k < s.branch_comments.len() {
                    s.branch_comments[k].clone()
                } else {
                    None
                };
                end_line(out, &c, comments);
                for b in body {
                    ustmt(b, ind + 1, out, comments, b"");
                }
            }
            indent(out, ind);
            out.extend_from_slice(b"endif");
            end_line(out, &s.end_comment, comments);
        }
        St::Loop { body, comment, end_comment, .. } => {
            indent(out, ind);
            out.extend_from_slice(prefix);
            out.extend_from_slice(b"loop");
            end_line(out, comment, comments);
            for b in body {
                ustmt(b, ind + 1, out, comments, b"");
            }
            indent(out, ind);
            out.extend_from_slice(b"endloop");
            end_line(out, end_comment, comments);
        }
        St::Exit { cond, comment, .. } => {
            indent(out, ind);
            out.extend_from_slice(prefix);
            out.extend_from_slice(b"exitwhen ");
            ue(cond, out);
            end_line(out, comment, comments);
        }
        St::Ret { value, comment, .. } => {
            indent(out, ind);
            out.extend_from_slice(prefix);
            out.extend_from_slice(b"return");
            if let Some(v) = value {
                out.push(b' ');
                ue(v, out);
            }
            end_line(out, comment, comments);
        }
        St::Comment { text, .. } => {
            if comments {
                indent(out, ind);
                out.extend_from_slice(text);
                out.push(b'\n');
            }
        }
        St::Debug { stmt, .. } => {
            let mut p = prefix.to_vec();
            p.extend_from_slice(b"debug ");
            ustmt(stmt, ind, out, comments, &p);
        }
    }
}

fn decl_text(d: &Decl, out: &mut Vec<u8>) {
    if d.is_constant {
        out.extend_from_slice(b"constant ");
    }
    out.extend_from_slice(&d.ty);
    out.extend_from_slice(if d.is_array { b" array " } else { b" " });
    out.extend_from_slice(&d.name);
    if let Some(i) = &d.init {
        out.extend_from_slice(b" = ");
        ue(i, out);
    }
}

fn uitem(item: &Item, out: &mut Vec<u8>, comments: bool) {
    let leading = match item {
        Item::Func(f) => &f.leading,
        Item::Globals(g) => &g.leading,
        Item::Type(t) => &t.leading,
    };
    if comments {
        for c in leading {
            out.extend_from_slice(c);
            out.push(b'\n');
        }
    }
    match item {
        Item::Func(f) => {
            if f.is_constant {
                out.extend_from_slice(b"constant ");
            }
            out.extend_from_slice(if f.is_native { b"native " } else { b"function " });
            out.extend_from_slice(&f.name);
            out.extend_from_slice(b" takes ");
            if f.params.is_empty() {
                out.extend_from_slice(b"nothing");
            }
            for (k, (t, n)) in f.params.iter().enumerate() {
                if k > 0 {
                    out.extend_from_slice(b", ");
                }
                out.extend_from_slice(t);
                out.push(b' ');
                out.extend_from_slice(n);
            }
            out.extend_from_slice(b" returns ");
            out.extend_from_slice(&f.ret);
            end_line(out, &f.comment, comments);
            if f.is_native {
                return;
            }
            for d in &f.locals {
                if comments {
                    for c in &d.leading {
                        out.extend_from_slice(b"    ");
                        out.extend_from_slice(c);
                        out.push(b'\n');
                    }
                }
                out.extend_from_slice(b"    local ");
                decl_text(d, out);
                end_line(out, &d.comment, comments);
            }
            for s in &f.body {
                ustmt(s, 1, out, comments, b"");
            }
            out.extend_from_slice(b"endfunction");
            end_line(out, &f.end_comment, comments);
        }
        Item::Globals(g) => {
            out.extend_from_slice(b"globals");
            end_line(out, &g.comment, comments);
            for d in &g.decls {
                if comments {
                    for c in &d.leading {
                        out.extend_from_slice(b"    ");
                        out.extend_from_slice(c);
                        out.push(b'\n');
                    }
                }
                out.extend_from_slice(b"    ");
                decl_text(d, out);
                end_line(out, &d.comment, comments);
            }
            if comments {
                for c in &g.end_comments {
                    out.extend_from_slice(b"    ");
                    out.extend_from_slice(c);
                    out.push(b'\n');
                }
            }
            out.extend_from_slice(b"endglobals");
            end_line(out, &g.end_comment, comments);
        }
        Item::Type(t) => {
            out.extend_from_slice(b"type ");
            out.extend_from_slice(&t.name);
            out.extend_from_slice(b" extends ");
            out.extend_from_slice(&t.base);
            end_line(out, &t.comment, comments);
        }
    }
}

pub fn unparse(s: &Script, comments: bool) -> Vec<u8> {
    let mut out = Vec::new();
    for (k, item) in s.items.iter().enumerate() {
        if k > 0 {
            if let Item::Func(f) = item {
                if !f.is_native {
                    out.push(b'\n');
                }
            }
        }
        uitem(item, &mut out, comments);
    }
    if comments {
        for c in &s.end_comments {
            out.extend_from_slice(c);
            out.push(b'\n');
        }
    }
    out
}

fn wrap32(v: u32) -> i64 {
    v as i32 as i64
}

fn int_value(text: &[u8]) -> Option<i64> {
    let hex = |d: &[u8]| -> u32 {
        let mut v: u32 = 0;
        for &c in d {
            v = v.wrapping_mul(16).wrapping_add((c as char).to_digit(16).unwrap_or(0));
        }
        v
    };
    if text.first() == Some(&b'$') {
        return Some(wrap32(hex(&text[1..])));
    }
    if text.len() >= 2 && (&text[..2] == b"0x" || &text[..2] == b"0X") {
        return Some(wrap32(hex(&text[2..])));
    }
    if text.len() > 1 && text[0] == b'0' && text.iter().all(|c| (b'0'..=b'7').contains(c)) {
        let mut v: u32 = 0;
        for &c in text {
            v = v.wrapping_mul(8).wrapping_add((c - b'0') as u32);
        }
        return Some(wrap32(v));
    }
    if text.len() > 4300 || !text.iter().all(|c| c.is_ascii_digit()) || text.is_empty() {
        return None;
    }
    let mut v: u32 = 0;
    for &c in text {
        v = v.wrapping_mul(10).wrapping_add((c - b'0') as u32);
    }
    Some(wrap32(v))
}

fn unescape(body: &[u8]) -> Vec<u8> {
    let mut out = Vec::with_capacity(body.len());
    let mut i = 0;
    while i < body.len() {
        let c = body[i];
        if c == b'\\' && i + 1 < body.len() {
            let d = body[i + 1];
            out.push(match d {
                b'n' => b'\n',
                b't' => b'\t',
                b'r' => b'\r',
                b'b' => 8,
                b'f' => 12,
                _ => d,
            });
            i += 2;
        } else {
            out.push(c);
            i += 1;
        }
    }
    out
}

fn raw_value(text: &[u8]) -> i64 {
    let mut v: u32 = 0;
    let body = if text.len() >= 2 { &text[1..text.len() - 1] } else { &text[..0] };
    for b in unescape(body) {
        v = v.wrapping_mul(256).wrapping_add(b as i8 as i32 as u32);
    }
    wrap32(v)
}

fn real_value(text: &[u8]) -> f64 {
    let s = std::str::from_utf8(text).unwrap_or("");
    let r = if s.starts_with('.') { format!("0{}", s).parse::<f64>() } else { s.parse::<f64>() };
    match r {
        Ok(v) => v,
        Err(_) => {
            refuse();
            0.0
        }
    }
}

#[derive(Clone, Copy, PartialEq, Debug)]
enum Num {
    Int(i64),
    Real(f64),
}

fn bare<'x, 'a>(mut e: &'x P<'a>) -> &'x P<'a> {
    while let E::Paren(inner, _) = &**e {
        e = inner;
    }
    e
}

fn is_rawcode_num(t: &[u8]) -> bool {
    let n = py_chars(t);
    n == 3 || n == 6
}

fn number(e: &P) -> Option<Num> {
    let mut e = bare(e);
    let mut neg = false;
    while let E::Unary(op @ (Op::Sub | Op::Add), x, _) = &**e {
        if *op == Op::Sub {
            neg = !neg;
        }
        e = bare(x);
    }
    match &**e {
        E::Lit(LK::Integer, t, _) => {
            let v = match int_value(t) {
                Some(v) => v,
                None => {
                    refuse();
                    0
                }
            };
            Some(Num::Int(if neg { -v } else { v }))
        }
        E::Lit(LK::Raw, t, _) if is_rawcode_num(t) => {
            let v = raw_value(t);
            Some(Num::Int(if neg { -v } else { v }))
        }
        E::Lit(LK::Real, t, _) => {
            let v = real_value(t);
            Some(Num::Real(if neg { -v } else { v }))
        }
        _ => None,
    }
}

const RAWCODE_CHARS: &[u8] = b"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";

fn lit<'a>(kind: LK, text: Vec<u8>) -> P<'a> {
    Arc::new(E::Lit(kind, owned(text), 0))
}

fn integer_node<'a>(value: i64) -> P<'a> {
    let raw = ((value as u64) & 0xFFFF_FFFF) as u32;
    let bytes = raw.to_be_bytes();
    if bytes.iter().all(|b| RAWCODE_CHARS.contains(b)) {
        let mut t = vec![b'\''];
        t.extend_from_slice(&bytes);
        t.push(b'\'');
        return lit(LK::Raw, t);
    }
    if value < 0 {
        return Arc::new(E::Unary(Op::Sub, lit(LK::Integer, (-value).to_string().into_bytes()), 0));
    }
    lit(LK::Integer, value.to_string().into_bytes())
}

const PURE_PREFIXES: [&[u8]; 28] = [
    b"Get", b"Is", b"Convert", b"BlzGet", b"BlzIs", b"I2", b"R2", b"S2", b"Load", b"Have", b"StringLength",
    b"SubString", b"StringCase", b"StringHash", b"OrderId", b"UnitId", b"AbilityId", b"Sin", b"Cos", b"Tan", b"Asin",
    b"Acos", b"Atan", b"SquareRoot", b"Pow", b"Deg2Rad", b"Rad2Deg", b"Version",
];
const PURE_NAMES: [&[u8]; 3] = [b"Player", b"Condition", b"Filter"];
const CREATED_TYPES: [&[u8]; 8] = [b"location", b"group", b"force", b"rect", b"region", b"timer", b"trigger", b"effect"];
const NORMAL_DEPTH: u32 = 16;

struct OneLiner {
    params: Vec<Vec<u8>>,
    body: P<'static>,
    linear: bool,
    pure_head: bool,
}

#[derive(Default)]
pub struct Reference {
    constants: FxMap<Box<[u8]>, P<'static>>,
    one_liners: FxMap<Box<[u8]>, OneLiner>,
    returns: FxMap<Box<[u8]>, Box<[u8]>>,
    natives: FxSet<Box<[u8]>>,
    pure: FxSet<Box<[u8]>>,
    empty: FxSet<Box<[u8]>>,
}

fn contains_sub(h: &[u8], n: &[u8]) -> bool {
    h.windows(n.len()).any(|w| w == n)
}

impl Reference {
    fn build(texts: &[&'static [u8]]) -> Option<Reference> {
        let mut r = Reference::default();
        for t in texts {
            if t.is_empty() {
                continue;
            }
            match parse(t) {
                Ok(s) => r.take(s),
                Err(Fail::Syntax) => continue,
                Err(Fail::Deep) => return None,
            }
            if refused() {
                return None;
            }
        }
        Some(r)
    }

    fn take(&mut self, script: Script<'static>) {
        for item in &script.items {
            if let Item::Func(f) = item {
                if f.is_native {
                    self.returns.entry(Box::from(&f.name[..])).or_insert_with(|| Box::from(&f.ret[..]));
                    self.natives.insert(Box::from(&f.name[..]));
                    let n: &[u8] = &f.name;
                    if PURE_NAMES.contains(&n)
                        || (PURE_PREFIXES.iter().any(|p| n.starts_with(p))
                            && !contains_sub(n, b"Random")
                            && !CREATED_TYPES.contains(&&f.ret[..]))
                    {
                        self.pure.insert(Box::from(n));
                    }
                }
            }
        }
        for item in &script.items {
            if let Item::Globals(g) = item {
                for d in &g.decls {
                    if !(d.is_constant && !d.is_array && d.init.is_some() && !self.constants.contains_key(&d.name[..])) {
                        continue;
                    }
                    let v: P<'static> = {
                        let mut n = Norm::new(self, FxSet::default(), None, None);
                        let x = n.expr(d.init.as_ref().unwrap());
                        bare(&x).clone()
                    };
                    let ok = number(&v).is_some()
                        || matches!(&*v, E::Lit(LK::Bool | LK::Str, _, _))
                        || match &*v {
                            E::Call(name, args, _) => {
                                name.starts_with(b"Convert")
                                    && self.natives.contains(&name[..])
                                    && args.iter().all(|a| number(a).is_some())
                            }
                            _ => false,
                        };
                    if ok {
                        self.constants.insert(Box::from(&d.name[..]), v);
                    }
                }
            }
        }
        for item in &script.items {
            let f = match item {
                Item::Func(f) if !f.is_native => f,
                _ => continue,
            };
            self.returns.entry(Box::from(&f.name[..])).or_insert_with(|| Box::from(&f.ret[..]));
            let body: Vec<&St> = f.body.iter().filter(|s| !matches!(s, St::Comment { .. })).collect();
            if body.is_empty() && f.locals.is_empty() && f.params.is_empty() && &f.ret[..] == b"nothing" {
                self.empty.insert(Box::from(&f.name[..]));
            }
            if !f.locals.is_empty() || body.len() != 1 || self.one_liners.contains_key(&f.name[..]) {
                continue;
            }
            let params: Vec<Vec<u8>> = f.params.iter().map(|(_t, n)| n.to_vec()).collect();
            let one_body = match body[0] {
                St::Ret { value: Some(v), .. } => v.clone(),
                St::Call { call, .. } if &f.ret[..] == b"nothing" => call.clone(),
                _ => continue,
            };
            let mut one = OneLiner { params, body: one_body, linear: false, pure_head: false };
            self.classify(&mut one);
            self.one_liners.insert(Box::from(&f.name[..]), one);
        }
    }

    fn classify(&self, one: &mut OneLiner) {
        enum Ev<'x> {
            Use(&'x [u8]),
            Read,
            Call,
        }
        let params: FxSet<&[u8]> = one.params.iter().map(|p| &p[..]).collect();
        let mut events: Vec<Ev> = Vec::new();
        fn walk<'x>(e: &'x P<'static>, params: &FxSet<&[u8]>, r: &Reference, events: &mut Vec<Ev<'x>>) {
            let _g = Guard::enter();
            if refused() {
                return;
            }
            let e = bare(e);
            match &**e {
                E::Name(n, _) => {
                    if params.contains(&n[..]) {
                        events.push(Ev::Use(n));
                    } else if !r.constants.contains_key(&n[..]) {
                        events.push(Ev::Read);
                    }
                }
                E::Index(b, i, _) => {
                    walk(b, params, r, events);
                    walk(i, params, r, events);
                }
                E::Unary(_, x, _) => walk(x, params, r, events),
                E::Binary(_, a, b, _) => {
                    walk(a, params, r, events);
                    walk(b, params, r, events);
                }
                E::Call(n, args, _) => {
                    for a in args {
                        walk(a, params, r, events);
                    }
                    if !r.pure.contains(&n[..]) {
                        events.push(Ev::Call);
                    }
                }
                _ => {}
            }
        }
        let body = one.body.clone();
        walk(&body, &params, self, &mut events);
        let uses: Vec<&[u8]> = events
            .iter()
            .filter_map(|x| match x {
                Ev::Use(n) => Some(*n),
                _ => None,
            })
            .collect();
        let last = events.iter().rposition(|x| matches!(x, Ev::Use(_)));
        let lead = match last {
            Some(k) => &events[..k + 1],
            None => &events[..0],
        };
        one.pure_head = !lead.iter().any(|x| matches!(x, Ev::Call));
        one.linear = uses.len() == one.params.len()
            && uses.iter().zip(one.params.iter()).all(|(a, b)| *a == &b[..])
            && !lead.iter().any(|x| !matches!(x, Ev::Use(_)));
    }
}

const ORDERS_BY_ID: [(&[u8], &[u8]); 10] = [
    (b"IssueImmediateOrderById", b"IssueImmediateOrder"),
    (b"IssuePointOrderById", b"IssuePointOrder"),
    (b"IssuePointOrderByIdLoc", b"IssuePointOrderLoc"),
    (b"IssueTargetOrderById", b"IssueTargetOrder"),
    (b"IssueInstantPointOrderById", b"IssueInstantPointOrder"),
    (b"IssueInstantTargetOrderById", b"IssueInstantTargetOrder"),
    (b"GroupImmediateOrderById", b"GroupImmediateOrder"),
    (b"GroupPointOrderById", b"GroupPointOrder"),
    (b"GroupPointOrderByIdLoc", b"GroupPointOrderLoc"),
    (b"GroupTargetOrderById", b"GroupTargetOrder"),
];

fn order_id(name: &[u8]) -> Option<i64> {
    ORDERS.iter().find(|(n, _)| *n == name).map(|(_, v)| *v)
}

fn order_name(id: i64) -> Option<&'static [u8]> {
    ORDERS.iter().rev().find(|(_, v)| *v == id).map(|(n, _)| *n)
}

struct Norm<'r, 'a> {
    rf: &'r Reference,
    stable: FxSet<Vec<u8>>,
    simple: Option<&'r FxMap<Vec<u8>, P<'a>>>,
    skip: Option<&'r [u8]>,
    holes: FxMap<Vec<u8>, (bool, bool)>,
    depth: u32,
    inlined: FxSet<Vec<u8>>,
}

impl<'r, 'a> Norm<'r, 'a> {
    fn new(
        rf: &'r Reference,
        stable: FxSet<Vec<u8>>,
        simple: Option<&'r FxMap<Vec<u8>, P<'a>>>,
        skip: Option<&'r [u8]>,
    ) -> Self {
        Norm { rf, stable, simple, skip, holes: FxMap::default(), depth: 0, inlined: FxSet::default() }
    }

    fn expr(&mut self, e: &P<'a>) -> P<'a> {
        let _g = Guard::enter();
        if refused() {
            return e.clone();
        }
        match &**e {
            E::Paren(inner, _) => self.expr(inner),
            E::Name(n, _) => {
                if !self.stable.contains(&n[..]) {
                    if let Some(c) = self.rf.constants.get(&n[..]) {
                        return c.clone();
                    }
                }
                e.clone()
            }
            E::Lit(k, t, _) => {
                if *k == LK::Integer {
                    match int_value(t) {
                        Some(v) => integer_node(v),
                        None => {
                            refuse();
                            e.clone()
                        }
                    }
                } else if *k == LK::Raw && is_rawcode_num(t) {
                    integer_node(raw_value(t))
                } else {
                    e.clone()
                }
            }
            E::Index(b, i, _) => {
                let b = self.expr(b);
                let i = self.expr(i);
                Arc::new(E::Index(b, i, 0))
            }
            E::Unary(op, x, _) => {
                let x = self.expr(x);
                self.unary(*op, x)
            }
            E::Binary(op, l, r, _) => {
                let l = self.expr(l);
                let r = self.expr(r);
                self.binary(*op, l, r)
            }
            E::Call(n, args, _) => {
                let args: Vec<P<'a>> = args.iter().map(|a| self.expr(a)).collect();
                self.call(n.clone(), args)
            }
            E::FuncRef(..) => e.clone(),
        }
    }

    fn unary(&mut self, op: Op, x: P<'a>) -> P<'a> {
        let b = bare(&x);
        if op == Op::Not {
            if let E::Unary(Op::Not, inner, _) = &**b {
                return inner.clone();
            }
            if let E::Lit(LK::Bool, t, _) = &**b {
                return lit(LK::Bool, if &t[..] == b"true" { b"false".to_vec() } else { b"true".to_vec() });
            }
        } else if op == Op::Add && number(b).is_some() {
            return x;
        }
        Arc::new(E::Unary(op, x, 0))
    }

    fn binary(&mut self, op: Op, left: P<'a>, right: P<'a>) -> P<'a> {
        let _g = Guard::enter();
        if refused() {
            return left;
        }
        let lb = bare(&left).clone();
        let rb = bare(&right).clone();
        if op == Op::Eq || op == Op::Ne {
            for (a, b) in [(&lb, &rb), (&rb, &lb)] {
                let literal = matches!(&**a, E::Lit(LK::Bool, _, _));
                if let E::Lit(LK::Bool, bt, _) = &**b {
                    if !literal {
                        return if (&bt[..] == b"true") == (op == Op::Eq) { a.clone() } else { self.unary(Op::Not, a.clone()) };
                    }
                }
                if matches!(&**b, E::Lit(LK::Null, _, _)) && self.boolean(a) {
                    return if op == Op::Ne { a.clone() } else { self.unary(Op::Not, a.clone()) };
                }
            }
        }
        if op == Op::Add {
            if let Some(nl) = number(&lb) {
                if number(&rb).is_none() {
                    let negative = match nl {
                        Num::Int(v) => v < 0,
                        Num::Real(v) => v < 0.0,
                    };
                    if negative {
                        let mut positive = lb.clone();
                        loop {
                            let next = match &*positive {
                                E::Unary(_, o, _) => bare(o).clone(),
                                _ => break,
                            };
                            positive = next;
                        }
                        return Arc::new(E::Binary(Op::Sub, right, positive, 0));
                    }
                    return Arc::new(E::Binary(Op::Add, right, left, 0));
                }
            }
        }
        if op == Op::And || op == Op::Or {
            if let E::Binary(rop, rl, rr, _) = &*rb {
                if *rop == op {
                    let inner = self.binary(op, left, rl.clone());
                    return self.binary(op, inner, rr.clone());
                }
            }
        }
        Arc::new(E::Binary(op, left, right, 0))
    }

    fn boolean(&self, e: &P<'a>) -> bool {
        match &**bare(e) {
            E::Binary(op, ..) => matches!(op, Op::And | Op::Or | Op::Eq | Op::Ne | Op::Lt | Op::Le | Op::Gt | Op::Ge),
            E::Unary(op, ..) => *op == Op::Not,
            E::Call(n, ..) => self.rf.returns.get(&n[..]).map(|t| &t[..] == b"boolean").unwrap_or(false),
            E::Lit(LK::Bool, ..) => true,
            _ => false,
        }
    }

    fn pure(&self, e: &P<'a>) -> bool {
        let _g = Guard::enter();
        if refused() {
            return false;
        }
        match &**bare(e) {
            E::Name(n, _) => self.holes.get(&n[..]).map(|h| h.0).unwrap_or(true),
            E::Lit(..) | E::FuncRef(..) => true,
            E::Index(b, i, _) => self.pure(b) && self.pure(i),
            E::Unary(_, x, _) => self.pure(x),
            E::Binary(_, l, r, _) => self.pure(l) && self.pure(r),
            E::Call(n, args, _) => self.rf.pure.contains(&n[..]) && args.iter().all(|a| self.pure(a)),
            _ => false,
        }
    }

    fn fixed(&self, e: &P<'a>) -> bool {
        let b = bare(e);
        if matches!(&**b, E::Lit(..)) || number(b).is_some() {
            return true;
        }
        if let E::Name(n, _) = &**b {
            return match self.holes.get(&n[..]) {
                Some(h) => h.1,
                None => self.stable.contains(&n[..]),
            };
        }
        false
    }

    fn call(&mut self, name: S<'a>, args: Vec<P<'a>>) -> P<'a> {
        if &name[..] == b"OrderId" && args.len() == 1 {
            if let E::Lit(LK::Str, t, _) = &**bare(&args[0]) {
                if t.len() >= 2 {
                    if let Some(id) = order_id(&t[1..t.len() - 1]) {
                        return integer_node(id);
                    }
                }
            }
        } else if let Some((_, by_name)) = ORDERS_BY_ID.iter().find(|(n, _)| *n == &name[..]) {
            if args.len() >= 2 {
                if let Some(Num::Int(v)) = number(&args[1]) {
                    if let Some(oname) = order_name(v) {
                        let mut text = vec![b'"'];
                        text.extend_from_slice(oname);
                        text.push(b'"');
                        let mut a = vec![args[0].clone(), lit(LK::Str, text)];
                        a.extend(args[2..].iter().cloned());
                        return Arc::new(E::Call(S::B(by_name), a, 0));
                    }
                }
            }
        }
        if self.depth >= NORMAL_DEPTH {
            return Arc::new(E::Call(name, args, 0));
        }
        if args.is_empty() {
            if let Some(simple) = self.simple {
                if self.skip != Some(&name[..]) {
                    if let Some(body) = simple.get(&name[..]) {
                        self.inlined.insert(name.to_vec());
                        self.depth += 1;
                        let r = self.expr(body);
                        self.depth -= 1;
                        return r;
                    }
                }
            }
        }
        let rf = self.rf;
        let one = match rf.one_liners.get(&name[..]) {
            Some(o) => o,
            None => return Arc::new(E::Call(name, args, 0)),
        };
        if args.len() != one.params.len()
            || !(one.linear
                || (one.pure_head && args.iter().all(|a| self.pure(a)))
                || args.iter().all(|a| self.fixed(a)))
        {
            return Arc::new(E::Call(name, args, 0));
        }
        let hole = |k: usize| -> Vec<u8> {
            let mut h = vec![0u8];
            h.extend_from_slice(k.to_string().as_bytes());
            h
        };
        let mut marks: FxMap<&[u8], P<'a>> = FxMap::default();
        for (k, p) in one.params.iter().enumerate() {
            marks.insert(&p[..], Arc::new(E::Name(owned(hole(k)), 0)));
        }
        let mut holes: FxMap<Vec<u8>, (bool, bool)> = FxMap::default();
        let mut values: FxMap<Vec<u8>, P<'a>> = FxMap::default();
        for (k, a) in args.iter().enumerate() {
            holes.insert(hole(k), (self.pure(a), self.fixed(a)));
            values.insert(hole(k), a.clone());
        }
        let mut inner: Norm<'r, 'a> = Norm::new(rf, FxSet::default(), None, None);
        inner.holes = holes;
        inner.depth = self.depth + 1;
        let body: P<'a> = one.body.clone();
        let rebuilt = rebuilt(&body, &marks);
        let body = inner.expr(&rebuilt);
        self.filled(&body, &values)
    }

    fn filled(&mut self, e: &P<'a>, values: &FxMap<Vec<u8>, P<'a>>) -> P<'a> {
        let _g = Guard::enter();
        if refused() {
            return e.clone();
        }
        match &**e {
            E::Name(n, _) => values.get(&n[..]).cloned().unwrap_or_else(|| e.clone()),
            E::Index(b, i, _) => {
                let b = self.filled(b, values);
                let i = self.filled(i, values);
                Arc::new(E::Index(b, i, 0))
            }
            E::Unary(op, x, _) => {
                let x = self.filled(x, values);
                self.unary(*op, x)
            }
            E::Binary(op, l, r, _) => {
                let l = self.filled(l, values);
                let r = self.filled(r, values);
                self.binary(*op, l, r)
            }
            E::Call(n, args, _) => {
                let a: Vec<P<'a>> = args.iter().map(|x| self.filled(x, values)).collect();
                Arc::new(E::Call(n.clone(), a, 0))
            }
            _ => e.clone(),
        }
    }
}

fn rebuilt<'a>(e: &P<'a>, names: &FxMap<&[u8], P<'a>>) -> P<'a> {
    let _g = Guard::enter();
    if refused() {
        return e.clone();
    }
    match &**e {
        E::Paren(inner, _) => rebuilt(inner, names),
        E::Name(n, _) => names.get(&n[..]).cloned().unwrap_or_else(|| e.clone()),
        E::Index(b, i, _) => Arc::new(E::Index(rebuilt(b, names), rebuilt(i, names), 0)),
        E::Unary(op, x, _) => Arc::new(E::Unary(*op, rebuilt(x, names), 0)),
        E::Binary(op, l, r, _) => Arc::new(E::Binary(*op, rebuilt(l, names), rebuilt(r, names), 0)),
        E::Call(n, args, _) => Arc::new(E::Call(n.clone(), args.iter().map(|a| rebuilt(a, names)).collect(), 0)),
        _ => e.clone(),
    }
}

fn not_comment(s: &St) -> bool {
    !matches!(s, St::Comment { .. })
}

fn tests<'a>(f: &Func<'a>) -> Option<(Op, Vec<P<'a>>)> {
    if !f.locals.is_empty() || !f.params.is_empty() || &f.ret[..] != b"boolean" {
        return None;
    }
    let body: Vec<&St<'a>> = f.body.iter().filter(|s| not_comment(s)).collect();
    if body.len() < 2 {
        return None;
    }
    let end = match body[body.len() - 1] {
        St::Ret { value: Some(v), .. } => bare(v).clone(),
        _ => return None,
    };
    let conj = match &*end {
        E::Lit(LK::Bool, t, _) => &t[..] == b"true",
        _ => return None,
    };
    let mut out = Vec::new();
    for s in &body[..body.len() - 1] {
        let s = match s {
            St::If(s) if s.branches.len() == 1 => s,
            _ => return None,
        };
        let (cond, inner) = &s.branches[0];
        let inner: Vec<&St<'a>> = inner.iter().filter(|x| not_comment(x)).collect();
        let ret = match (inner.len(), inner.first()) {
            (1, Some(St::Ret { value: Some(v), .. })) => bare(v).clone(),
            _ => return None,
        };
        match &*ret {
            E::Lit(LK::Bool, t, _) if (&t[..] == b"true") != conj => {}
            _ => return None,
        }
        let mut c = bare(cond.as_ref()?).clone();
        if conj {
            let operand = match &*c {
                E::Unary(Op::Not, x, _) => x.clone(),
                _ => return None,
            };
            c = operand;
        }
        out.push(c);
    }
    Some((if conj { Op::And } else { Op::Or }, out))
}

fn fold_conditions(script: &mut Script) {
    for item in script.items.iter_mut() {
        let f = match item {
            Item::Func(f) if !f.is_native => f,
            _ => continue,
        };
        if let Some((op, conds)) = tests(f) {
            let mut e = conds[0].clone();
            for c in &conds[1..] {
                e = Arc::new(E::Binary(op, e, c.clone(), 0));
            }
            let line = match f.body.last() {
                Some(St::Set { line, .. })
                | Some(St::Call { line, .. })
                | Some(St::Loop { line, .. })
                | Some(St::Exit { line, .. })
                | Some(St::Ret { line, .. })
                | Some(St::Comment { line, .. })
                | Some(St::Debug { line, .. }) => *line,
                Some(St::If(s)) => s.line,
                None => 0,
            };
            f.body = vec![St::Ret { value: Some(e), line, comment: None }];
        }
    }
}

fn statements<'r, 'a>(body: Vec<St<'a>>, n: &mut Norm<'r, 'a>) -> Vec<St<'a>> {
    let _g = Guard::enter();
    let mut out = Vec::with_capacity(body.len());
    for mut s in body {
        if refused() {
            return out;
        }
        match &mut s {
            St::Set { target, value, .. } => {
                *target = n.expr(target);
                *value = n.expr(value);
            }
            St::Call { call, .. } => {
                let (name, args) = match &**call {
                    E::Call(name, args, _) => (name.clone(), args.clone()),
                    _ => unreachable!(),
                };
                if args.is_empty() && n.rf.empty.contains(&name[..]) {
                    continue;
                }
                let e = n.expr(call);
                let e = bare(&e).clone();
                *call = if matches!(&*e, E::Call(..)) {
                    e
                } else {
                    let a: Vec<P<'a>> = args.iter().map(|a| n.expr(a)).collect();
                    Arc::new(E::Call(name, a, 0))
                };
                if let E::Call(nm, a, _) = &**call {
                    if &nm[..] == b"DestroyBoolExpr" && a.len() == 1 && matches!(&**bare(&a[0]), E::Lit(LK::Null, _, _)) {
                        continue;
                    }
                }
            }
            St::If(ifs) => {
                let branches = std::mem::take(&mut ifs.branches);
                for (c, b) in branches {
                    let c = c.map(|c| n.expr(&c));
                    let b = statements(b, n);
                    ifs.branches.push((c, b));
                }
                if ifs.branches.len() > 1 {
                    let last = &ifs.branches[ifs.branches.len() - 1];
                    if last.0.is_none() && !last.1.iter().any(not_comment) {
                        ifs.branches.pop();
                    }
                }
            }
            St::Loop { body, .. } => {
                let b = std::mem::take(body);
                *body = statements(b, n);
            }
            St::Exit { cond, .. } => {
                *cond = n.expr(cond);
            }
            St::Ret { value: Some(v), .. } => {
                *v = n.expr(v);
            }
            St::Debug { stmt, .. } => {
                let inner = std::mem::replace(&mut **stmt, St::Comment { text: S::B(b""), line: 0 });
                let mut r = statements(vec![inner], n);
                match r.pop() {
                    Some(x) => **stmt = x,
                    None => continue,
                }
            }
            _ => {}
        }
        out.push(s);
    }
    out
}

fn collect_named<'x>(e: &'x P, out: &mut FxSet<&'x [u8]>) {
    let _g = Guard::enter();
    if refused() {
        return;
    }
    match &**e {
        E::FuncRef(n, _) => {
            out.insert(n);
        }
        E::Call(n, args, _) => {
            out.insert(n);
            for a in args {
                collect_named(a, out);
            }
        }
        E::Index(b, i, _) => {
            collect_named(b, out);
            collect_named(i, out);
        }
        E::Unary(_, x, _) => collect_named(x, out),
        E::Binary(_, l, r, _) => {
            collect_named(l, out);
            collect_named(r, out);
        }
        E::Paren(x, _) => collect_named(x, out),
        _ => {}
    }
}

fn collect_named_stmt<'x>(s: &'x St, out: &mut FxSet<&'x [u8]>) {
    let _g = Guard::enter();
    if refused() {
        return;
    }
    match s {
        St::Set { target, value, .. } => {
            collect_named(target, out);
            collect_named(value, out);
        }
        St::Call { call, .. } => collect_named(call, out),
        St::If(s) => {
            for (c, b) in &s.branches {
                if let Some(c) = c {
                    collect_named(c, out);
                }
                for x in b {
                    collect_named_stmt(x, out);
                }
            }
        }
        St::Loop { body, .. } => {
            for x in body {
                collect_named_stmt(x, out);
            }
        }
        St::Exit { cond, .. } => collect_named(cond, out),
        St::Ret { value: Some(v), .. } => collect_named(v, out),
        St::Debug { stmt, .. } => collect_named_stmt(stmt, out),
        _ => {}
    }
}

fn normalize<'a>(script: &mut Script<'a>, rf: &Reference, inline: bool) {
    fold_conditions(script);
    let mut simple: FxMap<Vec<u8>, P<'a>> = FxMap::default();
    if inline {
        for item in &script.items {
            if let Item::Func(f) = item {
                if f.is_native || !f.params.is_empty() || !f.locals.is_empty() || &f.ret[..] != b"boolean" {
                    continue;
                }
                let body: Vec<&St> = f.body.iter().filter(|s| not_comment(s)).collect();
                if body.len() == 1 {
                    if let St::Ret { value: Some(v), .. } = body[0] {
                        simple.insert(f.name.to_vec(), v.clone());
                    }
                }
            }
        }
    }
    let mut inlined: FxSet<Vec<u8>> = FxSet::default();
    for item in script.items.iter_mut() {
        match item {
            Item::Globals(g) => {
                let mut n = Norm::new(rf, FxSet::default(), Some(&simple), None);
                for d in g.decls.iter_mut() {
                    if let Some(i) = &d.init {
                        d.init = Some(n.expr(i));
                    }
                }
                inlined.extend(n.inlined.drain());
            }
            Item::Func(f) if !f.is_native => {
                let mut names: FxSet<Vec<u8>> = FxSet::default();
                for (_t, p) in &f.params {
                    names.insert(p.to_vec());
                }
                for d in &f.locals {
                    names.insert(d.name.to_vec());
                }
                let own = f.name.clone();
                let mut n = Norm::new(rf, names, Some(&simple), Some(&own[..]));
                for d in f.locals.iter_mut() {
                    if let Some(i) = &d.init {
                        d.init = Some(n.expr(i));
                    }
                }
                let body = std::mem::take(&mut f.body);
                f.body = statements(body, &mut n);
                inlined.extend(n.inlined.drain());
            }
            _ => {}
        }
        if refused() {
            return;
        }
    }
    if inlined.is_empty() {
        return;
    }
    let gone: FxSet<Vec<u8>> = {
        let mut named: FxSet<&[u8]> = FxSet::default();
        for item in &script.items {
            if let Item::Func(f) = item {
                if f.is_native {
                    continue;
                }
                for d in &f.locals {
                    if let Some(i) = &d.init {
                        collect_named(i, &mut named);
                    }
                }
                for s in &f.body {
                    collect_named_stmt(s, &mut named);
                }
            }
        }
        inlined.iter().filter(|x| !named.contains(&x[..])).cloned().collect()
    };
    if !gone.is_empty() {
        script.items.retain(|i| !matches!(i, Item::Func(f) if gone.contains(&f.name[..])));
    }
}

fn parens<'a>(e: &P<'a>) -> P<'a> {
    let _g = Guard::enter();
    if refused() {
        return e.clone();
    }
    match &**e {
        E::Paren(inner, _) => parens(inner),
        E::Binary(op, l, r, _) => {
            let left = parens(l);
            let right = parens(r);
            if *op == Op::Add {
                if let (E::Lit(LK::Str, a, _), E::Lit(LK::Str, b, _)) = (&*left, &*right) {
                    let mut t = a[..a.len() - 1].to_vec();
                    t.extend_from_slice(&b[1..]);
                    return lit(LK::Str, t);
                }
            }
            Arc::new(E::Paren(Arc::new(E::Binary(*op, left, right, 0)), 0))
        }
        E::Unary(op, x, _) => Arc::new(E::Unary(*op, parens(x), 0)),
        E::Call(n, args, _) => Arc::new(E::Call(n.clone(), args.iter().map(parens).collect(), 0)),
        E::Index(b, i, _) => Arc::new(E::Index(parens(b), parens(i), 0)),
        _ => e.clone(),
    }
}

fn parens_stmt(s: &mut St) {
    let _g = Guard::enter();
    if refused() {
        return;
    }
    match s {
        St::Set { target, value, .. } => {
            *target = parens(target);
            *value = parens(value);
        }
        St::Call { call, .. } => *call = parens(call),
        St::If(s) => {
            for (c, _) in s.branches.iter_mut() {
                if let Some(x) = c {
                    *x = parens(x);
                }
            }
            for (_, body) in s.branches.iter_mut() {
                for x in body.iter_mut() {
                    parens_stmt(x);
                }
            }
        }
        St::Loop { body, .. } => {
            for x in body.iter_mut() {
                parens_stmt(x);
            }
        }
        St::Exit { cond, .. } => *cond = parens(cond),
        St::Ret { value: Some(v), .. } => *v = parens(v),
        St::Debug { stmt, .. } => parens_stmt(stmt),
        _ => {}
    }
}

fn jass_parens(script: &mut Script) {
    for item in script.items.iter_mut() {
        match item {
            Item::Globals(g) => {
                for d in g.decls.iter_mut() {
                    if let Some(i) = &d.init {
                        d.init = Some(parens(i));
                    }
                }
            }
            Item::Func(f) => {
                for d in f.locals.iter_mut() {
                    if let Some(i) = &d.init {
                        d.init = Some(parens(i));
                    }
                }
                if !f.is_native {
                    for s in f.body.iter_mut() {
                        parens_stmt(s);
                    }
                }
            }
            Item::Type(_) => {}
        }
    }
}

static REFERENCE: Mutex<Option<Arc<Reference>>> = Mutex::new(None);

fn current_reference() -> Option<Arc<Reference>> {
    REFERENCE.lock().ok().and_then(|g| g.clone())
}

pub fn reference_ready() -> bool {
    current_reference().is_some()
}

pub fn reparen_re(text: &[u8], inline: bool) -> crate::canon::Re {
    use crate::canon::Re;
    let rf = match current_reference() {
        Some(r) => r,
        None => return Re::Refuse,
    };
    reset_refusal();
    let r = panic::catch_unwind(panic::AssertUnwindSafe(|| {
        let mut script = match parse(text) {
            Ok(s) => s,
            Err(Fail::Syntax) => return Re::NoParse,
            Err(Fail::Deep) => return Re::Refuse,
        };
        normalize(&mut script, &rf, inline);
        if refused() {
            return Re::Refuse;
        }
        jass_parens(&mut script);
        if refused() {
            return Re::Refuse;
        }
        let out = unparse(&script, false);
        if refused() {
            return Re::Refuse;
        }
        drop(script);
        Re::Text(out)
    }));
    let refused_late = refused();
    reset_refusal();
    match r {
        Ok(Re::Text(t)) if !refused_late => Re::Text(t),
        Ok(Re::NoParse) => Re::NoParse,
        _ => Re::Refuse,
    }
}

#[allow(dead_code)]
pub fn reparen(text: &[u8], inline: bool) -> Option<Vec<u8>> {
    match reparen_re(text, inline) {
        crate::canon::Re::Text(t) => Some(t),
        _ => None,
    }
}

struct Group {
    h: u32,
    ty: u8,
    n: u32,
    scal: Vec<i32>,
    kids: Vec<i32>,
}

struct Col<'x> {
    map: FxMap<&'x [u8], i32>,
    blob: Vec<u8>,
    offs: Vec<u32>,
    groups: Vec<Group>,
    gindex: Vec<u32>,
    handles: Vec<(u32, u32)>,
    heights: Vec<u32>,
    tmp: Vec<i32>,
}

impl<'x> Col<'x> {
    fn s(&mut self, b: &'x [u8]) -> i32 {
        if let Some(&k) = self.map.get(b) {
            return k;
        }
        self.blob.extend_from_slice(b);
        self.offs.push(self.blob.len() as u32);
        let k = (self.offs.len() - 1) as i32;
        self.map.insert(b, k);
        k
    }
    fn o(&mut self, c: &'x Option<S>) -> i32 {
        match c {
            Some(x) => self.s(x),
            None => 0,
        }
    }
    fn strs_into(&mut self, list: &'x [S], out: &mut Vec<i32>) {
        out.push(list.len() as i32);
        for c in list {
            let k = self.s(c);
            out.push(k);
        }
    }
    fn add(&mut self, ty: u8, scal: &[i32], kids: &[i32]) -> i32 {
        let mut h = 0;
        for &k in kids {
            if k > 0 {
                h = h.max(self.heights[(k - 1) as usize] + 1);
            }
        }
        let slot = (h as usize) * 32 + ty as usize;
        if slot >= self.gindex.len() {
            self.gindex.resize(slot + 32, u32::MAX);
        }
        let g = match self.gindex[slot] {
            u32::MAX => {
                let g = self.groups.len() as u32;
                self.groups.push(Group { h, ty, n: 0, scal: Vec::new(), kids: Vec::new() });
                self.gindex[slot] = g;
                g
            }
            g => g,
        };
        let grp = &mut self.groups[g as usize];
        let idx = grp.n;
        grp.n += 1;
        grp.scal.extend_from_slice(scal);
        grp.kids.extend_from_slice(kids);
        self.handles.push((g, idx));
        self.heights.push(h);
        self.handles.len() as i32
    }
    fn expr(&mut self, e: &'x E) -> i32 {
        match e {
            E::Name(n, l) => {
                let k = self.s(n);
                self.add(1, &[k, *l as i32], &[])
            }
            E::Lit(kind, t, l) => {
                let k = self.s(t);
                self.add(3, &[*kind as i32, k, *l as i32], &[])
            }
            E::FuncRef(n, l) => {
                let k = self.s(n);
                self.add(8, &[k, *l as i32], &[])
            }
            E::Call(n, args, l) => {
                let mut kids = Vec::with_capacity(args.len());
                for a in args {
                    kids.push(self.expr(a));
                }
                let k = self.s(n);
                self.add(2, &[k, *l as i32, args.len() as i32], &kids)
            }
            E::Binary(op, a, b, l) => {
                let x = self.expr(a);
                let y = self.expr(b);
                self.add(4, &[op.code(), *l as i32], &[x, y])
            }
            E::Unary(op, x, l) => {
                let x = self.expr(x);
                self.add(5, &[op.code(), *l as i32], &[x])
            }
            E::Paren(x, l) => {
                let x = self.expr(x);
                self.add(6, &[*l as i32], &[x])
            }
            E::Index(b, i, l) => {
                let x = self.expr(b);
                let y = self.expr(i);
                self.add(7, &[*l as i32], &[x, y])
            }
        }
    }
    fn stmt(&mut self, s: &'x St) -> i32 {
        match s {
            St::Set { target, value, line, comment } => {
                let x = self.expr(target);
                let y = self.expr(value);
                let c = self.o(comment);
                self.add(10, &[*line as i32, c], &[x, y])
            }
            St::Call { call, line, comment } => {
                let x = self.expr(call);
                let c = self.o(comment);
                self.add(11, &[*line as i32, c], &[x])
            }
            St::Exit { cond, line, comment } => {
                let x = self.expr(cond);
                let c = self.o(comment);
                self.add(12, &[*line as i32, c], &[x])
            }
            St::Ret { value, line, comment } => {
                let x = match value {
                    Some(v) => self.expr(v),
                    None => 0,
                };
                let c = self.o(comment);
                self.add(13, &[*line as i32, c], &[x])
            }
            St::Comment { text, line } => {
                let k = self.s(text);
                self.add(14, &[k, *line as i32], &[])
            }
            St::Debug { stmt, line } => {
                let x = self.stmt(stmt);
                self.add(15, &[*line as i32], &[x])
            }
            St::Loop { body, line, comment, end_line, end_comment } => {
                let kids: Vec<i32> = body.iter().map(|x| self.stmt(x)).collect();
                let c = self.o(comment);
                let ec = self.o(end_comment);
                self.add(16, &[*line as i32, c, *end_line as i32, ec, body.len() as i32], &kids)
            }
            St::If(s) => {
                let mut kids = Vec::new();
                for (c, body) in &s.branches {
                    if let Some(c) = c {
                        kids.push(self.expr(c));
                    }
                    for x in body {
                        kids.push(self.stmt(x));
                    }
                }
                let c = self.o(&s.comment);
                let ec = self.o(&s.end_comment);
                let mut scal = vec![s.line as i32, c, s.end_line as i32, ec, s.branches.len() as i32];
                for (k, (c, body)) in s.branches.iter().enumerate() {
                    let bc = self.o(&s.branch_comments[k]);
                    scal.extend_from_slice(&[c.is_some() as i32, body.len() as i32, s.branch_lines[k] as i32, bc]);
                }
                self.add(17, &scal, &kids)
            }
        }
    }
    fn decl(&mut self, d: &'x Decl, global: bool) -> i32 {
        let x = match &d.init {
            Some(i) => self.expr(i),
            None => 0,
        };
        let name = self.s(&d.name);
        let ty = self.s(&d.ty);
        let c = self.o(&d.comment);
        let mut scal = std::mem::take(&mut self.tmp);
        scal.clear();
        if global {
            scal.extend_from_slice(&[name, ty, d.is_array as i32, d.is_constant as i32, d.line as i32, c]);
        } else {
            scal.extend_from_slice(&[name, ty, d.is_array as i32, d.line as i32, c]);
        }
        self.strs_into(&d.leading, &mut scal);
        let r = self.add(if global { 21 } else { 20 }, &scal, &[x]);
        self.tmp = scal;
        r
    }
    fn item(&mut self, item: &'x Item) -> i32 {
        match item {
            Item::Func(f) => {
                let mut kids = Vec::with_capacity(f.locals.len() + f.body.len());
                for d in &f.locals {
                    kids.push(self.decl(d, false));
                }
                for s in &f.body {
                    kids.push(self.stmt(s));
                }
                let name = self.s(&f.name);
                let c = self.o(&f.comment);
                let ec = self.o(&f.end_comment);
                let ret = self.s(&f.ret);
                let mut scal = vec![
                    name,
                    f.line as i32,
                    f.end_line as i32,
                    f.is_native as i32,
                    f.is_constant as i32,
                    c,
                    ec,
                    ret,
                    f.params.len() as i32,
                ];
                for (t, n) in &f.params {
                    let t = self.s(t);
                    let n = self.s(n);
                    scal.extend_from_slice(&[t, n]);
                }
                self.strs_into(&f.leading, &mut scal);
                scal.extend_from_slice(&[f.locals.len() as i32, f.body.len() as i32]);
                self.add(22, &scal, &kids)
            }
            Item::Globals(g) => {
                let kids: Vec<i32> = g.decls.iter().map(|d| self.decl(d, true)).collect();
                let c = self.o(&g.comment);
                let ec = self.o(&g.end_comment);
                let mut scal = vec![g.line as i32, g.end_line as i32, c, ec];
                self.strs_into(&g.end_comments, &mut scal);
                self.strs_into(&g.leading, &mut scal);
                scal.push(g.decls.len() as i32);
                self.add(23, &scal, &kids)
            }
            Item::Type(t) => {
                let name = self.s(&t.name);
                let base = self.s(&t.base);
                let c = self.o(&t.comment);
                let mut scal = vec![name, base, t.line as i32, c];
                self.strs_into(&t.leading, &mut scal);
                self.add(24, &scal, &[])
            }
        }
    }
}

fn serialize(s: &Script) -> Vec<u8> {
    let mut col = Col {
        map: FxMap::default(),
        blob: Vec::new(),
        offs: vec![0],
        groups: Vec::new(),
        gindex: Vec::new(),
        handles: Vec::new(),
        heights: Vec::new(),
        tmp: Vec::new(),
    };
    let items: Vec<i32> = s.items.iter().map(|it| col.item(it)).collect();
    let mut trailer: Vec<i32> = vec![s.comments.len() as i32];
    for (t, l) in &s.comments {
        let k = col.s(t);
        trailer.extend_from_slice(&[k, *l as i32]);
    }
    trailer.push(s.end_comments.len() as i32);
    for t in &s.end_comments {
        let k = col.s(t);
        trailer.push(k);
    }
    let mut order: Vec<u32> = (0..col.groups.len() as u32).collect();
    order.sort_by_key(|&g| (col.groups[g as usize].h, col.groups[g as usize].ty));
    let mut base = vec![0i32; col.groups.len()];
    let mut next = 1i32;
    for &g in &order {
        base[g as usize] = next;
        next += col.groups[g as usize].n as i32;
    }
    let handles = &col.handles;
    let remap = |k: i32| -> i32 {
        if k <= 0 {
            0
        } else {
            let (g, idx) = handles[(k - 1) as usize];
            base[g as usize] + idx as i32
        }
    };
    let count = col.offs.len() - 1;
    let total_ints: usize = 1 + col.groups.iter().map(|g| 4 + g.scal.len() + g.kids.len()).sum::<usize>()
        + trailer.len()
        + 1
        + items.len();
    let mut out = Vec::with_capacity(8 + 4 * col.offs.len() + col.blob.len() + 4 * total_ints);
    out.extend_from_slice(&(count as u32).to_le_bytes());
    for o in &col.offs {
        out.extend_from_slice(&o.to_le_bytes());
    }
    out.extend_from_slice(&col.blob);
    while out.len() % 4 != 0 {
        out.push(0);
    }
    let put = |x: i32, out: &mut Vec<u8>| out.extend_from_slice(&x.to_le_bytes());
    put(col.groups.len() as i32, &mut out);
    for &g in &order {
        let grp = &col.groups[g as usize];
        put(grp.ty as i32, &mut out);
        put(grp.n as i32, &mut out);
        put(grp.scal.len() as i32, &mut out);
        put(grp.kids.len() as i32, &mut out);
        for &x in &grp.scal {
            put(x, &mut out);
        }
        for &k in &grp.kids {
            put(remap(k), &mut out);
        }
    }
    for &x in &trailer {
        put(x, &mut out);
    }
    put(items.len() as i32, &mut out);
    for &k in &items {
        put(remap(k), &mut out);
    }
    out
}

fn give(bytes: Vec<u8>, out: *mut *mut u8, out_len: *mut usize) {
    let mut b = bytes.into_boxed_slice();
    unsafe {
        *out_len = b.len();
        *out = b.as_mut_ptr();
    }
    std::mem::forget(b);
}

fn on_big_stack<F: FnOnce() -> Result<Vec<u8>, i32> + Send + 'static>(work: F) -> Result<Vec<u8>, i32> {
    run_big(work).unwrap_or(Err(3))
}

type Job = Box<dyn FnOnce() + Send>;

static WORKERS: Mutex<Vec<std::sync::mpsc::Sender<Job>>> = Mutex::new(Vec::new());

fn start_worker() -> Option<std::sync::mpsc::Sender<Job>> {
    let (tx, rx) = std::sync::mpsc::channel::<Job>();
    std::thread::Builder::new()
        .stack_size(256 << 20)
        .spawn(move || {
            while let Ok(job) = rx.recv() {
                job();
            }
        })
        .ok()?;
    Some(tx)
}

fn run_big<R: Send + 'static, F: FnOnce() -> R + Send + 'static>(work: F) -> Option<R> {
    let (rtx, rrx) = std::sync::mpsc::sync_channel::<Option<R>>(1);
    let job: Job = Box::new(move || {
        let r = panic::catch_unwind(panic::AssertUnwindSafe(|| {
            reset_refusal();
            let r = work();
            reset_refusal();
            r
        }));
        let _ = rtx.send(r.ok());
    });
    let idle = WORKERS.lock().ok().and_then(|mut w| w.pop());
    let worker = match idle {
        Some(w) => w,
        None => start_worker()?,
    };
    let worker = match worker.send(job) {
        Ok(()) => worker,
        Err(std::sync::mpsc::SendError(job)) => {
            let w = start_worker()?;
            w.send(job).ok()?;
            w
        }
    };
    let r = rrx.recv().ok().flatten();
    if let Ok(mut w) = WORKERS.lock() {
        w.push(worker);
    }
    r
}

struct Parsed {
    text: Box<[u8]>,
    script: Option<Script<'static>>,
}

impl Drop for Parsed {
    fn drop(&mut self) {
        self.script = None;
    }
}

fn input(text: *const u8, len: usize) -> Vec<u8> {
    if len == 0 {
        Vec::new()
    } else {
        unsafe { std::slice::from_raw_parts(text, len) }.to_vec()
    }
}

#[no_mangle]
pub extern "C" fn jass_parse_tree(text: *const u8, len: usize, out: *mut *mut u8, out_len: *mut usize) -> i32 {
    if (text.is_null() && len > 0) || out.is_null() || out_len.is_null() {
        return 3;
    }
    let mut owned = Parsed { text: input(text, len).into_boxed_slice(), script: None };
    match on_big_stack(move || {
        let src: &'static [u8] = unsafe { std::slice::from_raw_parts(owned.text.as_ptr(), owned.text.len()) };
        match parse(src) {
            Ok(s) => {
                let b = serialize(&s);
                owned.script = Some(s);
                if owned.text.len() >= 1 << 20 {
                    let _ = std::thread::Builder::new().stack_size(256 << 20).spawn(move || drop(owned));
                }
                Ok(b)
            }
            Err(_) => Err(1),
        }
    }) {
        Ok(b) => {
            give(b, out, out_len);
            0
        }
        Err(c) => c,
    }
}

#[no_mangle]
pub extern "C" fn jass_unparse_text(
    text: *const u8,
    len: usize,
    comments: i32,
    out: *mut *mut u8,
    out_len: *mut usize,
) -> i32 {
    if (text.is_null() && len > 0) || out.is_null() || out_len.is_null() {
        return 3;
    }
    let data = input(text, len);
    match on_big_stack(move || match parse(&data) {
        Ok(s) => {
            let t = unparse(&s, comments != 0);
            if refused() {
                Err(1)
            } else {
                Ok(t)
            }
        }
        Err(_) => Err(1),
    }) {
        Ok(b) => {
            give(b, out, out_len);
            0
        }
        Err(c) => c,
    }
}

#[no_mangle]
pub extern "C" fn canon_jass_reference(
    common: *const u8,
    common_len: usize,
    blizzard: *const u8,
    blizzard_len: usize,
) -> i32 {
    if (common.is_null() && common_len > 0) || (blizzard.is_null() && blizzard_len > 0) {
        return 3;
    }
    let c: &'static [u8] = Box::leak(input(common, common_len).into_boxed_slice());
    let b: &'static [u8] = Box::leak(input(blizzard, blizzard_len).into_boxed_slice());
    let r = match run_big(move || Reference::build(&[c, b])) {
        Some(Some(r)) => r,
        _ => return 3,
    };
    match REFERENCE.lock() {
        Ok(mut g) => {
            *g = Some(Arc::new(r));
            0
        }
        Err(_) => 3,
    }
}

#[no_mangle]
pub extern "C" fn canon_jass_reparen(
    text: *const u8,
    len: usize,
    inline: i32,
    out: *mut *mut u8,
    out_len: *mut usize,
) -> i32 {
    if (text.is_null() && len > 0) || out.is_null() || out_len.is_null() {
        return 3;
    }
    if !reference_ready() {
        return 2;
    }
    let data = input(text, len);
    match on_big_stack(move || match reparen_re(&data, inline != 0) {
        crate::canon::Re::Text(t) => Ok(t),
        crate::canon::Re::NoParse => Err(1),
        crate::canon::Re::Refuse => Err(3),
    }) {
        Ok(b) => {
            give(b, out, out_len);
            0
        }
        Err(c) => c,
    }
}

const ORDERS: [(&[u8], i64); 359] = [
    (b"smart", 851971), (b"stop", 851972), (b"stunned", 851973), (b"cancel", 851976),
    (b"setrally", 851980), (b"getitem", 851981), (b"attack", 851983), (b"attackground", 851984),
    (b"attackonce", 851985), (b"move", 851986), (b"AImove", 851988), (b"patrol", 851990),
    (b"holdposition", 851993), (b"build", 851994), (b"humanbuild", 851995), (b"orcbuild", 851996),
    (b"nightelfbuild", 851997), (b"undeadbuild", 851998), (b"resumebuild", 851999), (b"skillmenu", 852000),
    (b"dropitem", 852001), (b"moveslot1", 852002), (b"moveslot2", 852003), (b"moveslot3", 852004),
    (b"moveslot4", 852005), (b"moveslot5", 852006), (b"moveslot6", 852007), (b"useslot1", 852008),
    (b"useslot2", 852009), (b"useslot3", 852010), (b"useslot4", 852011), (b"useslot5", 852012),
    (b"useslot6", 852013), (b"detectaoe", 852015), (b"resumeharvesting", 852017), (b"harvest", 852018),
    (b"returnresources", 852020), (b"autoharvestgold", 852021), (b"autoharvestlumber", 852022), (b"neutraldetectaoe", 852023),
    (b"repair", 852024), (b"repairon", 852025), (b"repairoff", 852026), (b"revive", 852039),
    (b"selfdestruct", 852040), (b"selfdestructon", 852041), (b"selfdestructoff", 852042), (b"board", 852043),
    (b"forceboard", 852044), (b"load", 852046), (b"unload", 852047), (b"unloadall", 852048),
    (b"unloadallinstant", 852049), (b"loadcorpse", 852050), (b"loadcorpseinstant", 852053), (b"unloadallcorpses", 852054),
    (b"defend", 852055), (b"undefend", 852056), (b"dispel", 852057), (b"flare", 852060),
    (b"heal", 852063), (b"healon", 852064), (b"healoff", 852065), (b"innerfire", 852066),
    (b"innerfireon", 852067), (b"innerfireoff", 852068), (b"invisibility", 852069), (b"militiaconvert", 852071),
    (b"militia", 852072), (b"militiaoff", 852073), (b"polymorph", 852074), (b"slow", 852075),
    (b"slowon", 852076), (b"slowoff", 852077), (b"tankdroppilot", 852079), (b"tankloadpilot", 852080),
    (b"tankpilot", 852081), (b"townbellon", 852082), (b"townbelloff", 852083), (b"avatar", 852086),
    (b"unavatar", 852087), (b"blizzard", 852089), (b"divineshield", 852090), (b"undivineshield", 852091),
    (b"holybolt", 852092), (b"massteleport", 852093), (b"resurrection", 852094), (b"thunderbolt", 852095),
    (b"thunderclap", 852096), (b"waterelemental", 852097), (b"berserk", 852100), (b"bloodlust", 852101),
    (b"bloodluston", 852102), (b"bloodlustoff", 852103), (b"devour", 852104), (b"evileye", 852105),
    (b"ensnare", 852106), (b"ensnareon", 852107), (b"ensnareoff", 852108), (b"healingward", 852109),
    (b"lightningshield", 852110), (b"purge", 852111), (b"standdown", 852113), (b"stasistrap", 852114),
    (b"chainlightning", 852119), (b"earthquake", 852121), (b"farsight", 852122), (b"mirrorimage", 852123),
    (b"shockwave", 852125), (b"spiritwolf", 852126), (b"stomp", 852127), (b"whirlwind", 852128),
    (b"windwalk", 852129), (b"unwindwalk", 852130), (b"ambush", 852131), (b"autodispel", 852132),
    (b"autodispelon", 852133), (b"autodispeloff", 852134), (b"barkskin", 852135), (b"barkskinon", 852136),
    (b"barkskinoff", 852137), (b"bearform", 852138), (b"unbearform", 852139), (b"corrosivebreath", 852140),
    (b"loadarcher", 852142), (b"mounthippogryph", 852143), (b"cyclone", 852144), (b"detonate", 852145),
    (b"eattree", 852146), (b"entangle", 852147), (b"entangleinstant", 852148), (b"faeriefire", 852149),
    (b"faeriefireon", 852150), (b"faeriefireoff", 852151), (b"ravenform", 852155), (b"unravenform", 852156),
    (b"recharge", 852157), (b"rechargeon", 852158), (b"rechargeoff", 852159), (b"rejuvination", 852160),
    (b"renew", 852161), (b"renewon", 852162), (b"renewoff", 852163), (b"roar", 852164),
    (b"root", 852165), (b"unroot", 852166), (b"entanglingroots", 852171), (b"flamingarrowstarg", 852173),
    (b"flamingarrows", 852174), (b"unflamingarrows", 852175), (b"forceofnature", 852176), (b"immolation", 852177),
    (b"unimmolation", 852178), (b"manaburn", 852179), (b"metamorphosis", 852180), (b"scout", 852181),
    (b"sentinel", 852182), (b"starfall", 852183), (b"tranquility", 852184), (b"acolyteharvest", 852185),
    (b"antimagicshell", 852186), (b"blight", 852187), (b"cannibalize", 852188), (b"cripple", 852189),
    (b"curse", 852190), (b"curseon", 852191), (b"curseoff", 852192), (b"freezingbreath", 852195),
    (b"possession", 852196), (b"raisedead", 852197), (b"raisedeadon", 852198), (b"raisedeadoff", 852199),
    (b"requestsacrifice", 852201), (b"restoration", 852202), (b"restorationon", 852203), (b"restorationoff", 852204),
    (b"sacrifice", 852205), (b"stoneform", 852206), (b"unstoneform", 852207), (b"unholyfrenzy", 852209),
    (b"unsummon", 852210), (b"web", 852211), (b"webon", 852212), (b"weboff", 852213),
    (b"wispharvest", 852214), (b"auraunholy", 852215), (b"auravampiric", 852216), (b"animatedead", 852217),
    (b"carrionswarm", 852218), (b"darkritual", 852219), (b"darksummoning", 852220), (b"deathanddecay", 852221),
    (b"deathcoil", 852222), (b"deathpact", 852223), (b"dreadlordinferno", 852224), (b"frostarmor", 852225),
    (b"frostnova", 852226), (b"sleep", 852227), (b"darkconversion", 852228), (b"darkportal", 852229),
    (b"fingerofdeath", 852230), (b"firebolt", 852231), (b"inferno", 852232), (b"gold2lumber", 852233),
    (b"lumber2gold", 852234), (b"spies", 852235), (b"rainofchaos", 852237), (b"rainoffire", 852238),
    (b"request_hero", 852239), (b"disassociate", 852240), (b"revenge", 852241), (b"soulpreservation", 852242),
    (b"coldarrowstarg", 852243), (b"coldarrows", 852244), (b"uncoldarrows", 852245), (b"creepanimatedead", 852246),
    (b"creepdevour", 852247), (b"creepheal", 852248), (b"creephealon", 852249), (b"creephealoff", 852250),
    (b"creepthunderbolt", 852252), (b"creepthunderclap", 852253), (b"poisonarrowstarg", 852254), (b"poisonarrows", 852255),
    (b"unpoisonarrows", 852256), (b"scrollofspeed", 852285), (b"frostarmoron", 852458), (b"frostarmoroff", 852459),
    (b"awaken", 852466), (b"nagabuild", 852467), (b"mount", 852469), (b"dismount", 852470),
    (b"cloudoffog", 852473), (b"controlmagic", 852474), (b"magicdefense", 852478), (b"magicundefense", 852479),
    (b"magicleash", 852480), (b"phoenixfire", 852481), (b"phoenixmorph", 852482), (b"spellsteal", 852483),
    (b"spellstealon", 852484), (b"spellstealoff", 852485), (b"banish", 852486), (b"drain", 852487),
    (b"flamestrike", 852488), (b"summonphoenix", 852489), (b"ancestralspirit", 852490), (b"ancestralspirittarget", 852491),
    (b"corporealform", 852493), (b"uncorporealform", 852494), (b"disenchant", 852495), (b"etherealform", 852496),
    (b"unetherealform", 852497), (b"spiritlink", 852499), (b"unstableconcoction", 852500), (b"healingwave", 852501),
    (b"hex", 852502), (b"voodoo", 852503), (b"ward", 852504), (b"autoentangle", 852505),
    (b"autoentangleinstant", 852506), (b"coupletarget", 852507), (b"coupleinstant", 852508), (b"decouple", 852509),
    (b"grabtree", 852511), (b"manaflareon", 852512), (b"manaflareoff", 852513), (b"phaseshift", 852514),
    (b"phaseshifton", 852515), (b"phaseshiftoff", 852516), (b"phaseshiftinstant", 852517), (b"taunt", 852520),
    (b"vengeance", 852521), (b"vengeanceon", 852522), (b"vengeanceoff", 852523), (b"vengeanceinstant", 852524),
    (b"blink", 852525), (b"fanofknives", 852526), (b"shadowstrike", 852527), (b"spiritofvengeance", 852528),
    (b"absorb", 852529), (b"avengerform", 852531), (b"unavengerform", 852532), (b"burrow", 852533),
    (b"unburrow", 852534), (b"devourmagic", 852536), (b"flamingattacktarg", 852539), (b"flamingattack", 852540),
    (b"unflamingattack", 852541), (b"replenish", 852542), (b"replenishon", 852543), (b"replenishoff", 852544),
    (b"replenishlife", 852545), (b"replenishlifeon", 852546), (b"replenishlifeoff", 852547), (b"replenishmana", 852548),
    (b"replenishmanaon", 852549), (b"replenishmanaoff", 852550), (b"carrionscarabs", 852551), (b"carrionscarabson", 852552),
    (b"carrionscarabsoff", 852553), (b"carrionscarabsinstant", 852554), (b"impale", 852555), (b"locustswarm", 852556),
    (b"breathoffrost", 852560), (b"frenzy", 852561), (b"frenzyon", 852562), (b"frenzyoff", 852563),
    (b"mechanicalcritter", 852564), (b"mindrot", 852565), (b"neutralinteract", 852566), (b"preservation", 852568),
    (b"sanctuary", 852569), (b"shadowsight", 852570), (b"spellshield", 852571), (b"spellshieldaoe", 852572),
    (b"spirittroll", 852573), (b"steal", 852574), (b"attributemodskill", 852576), (b"blackarrow", 852577),
    (b"blackarrowon", 852578), (b"blackarrowoff", 852579), (b"breathoffire", 852580), (b"charm", 852581),
    (b"doom", 852583), (b"drunkenhaze", 852585), (b"howlofterror", 852588), (b"manashieldon", 852589),
    (b"manashieldoff", 852590), (b"monsoon", 852591), (b"silence", 852592), (b"stampede", 852593),
    (b"summongrizzly", 852594), (b"summonquillbeast", 852595), (b"summonwareagle", 852596), (b"tornado", 852597),
    (b"wateryminion", 852598), (b"channel", 852600), (b"parasite", 852601), (b"parasiteon", 852602),
    (b"parasiteoff", 852603), (b"submerge", 852604), (b"unsubmerge", 852605), (b"neutralspell", 852630),
    (b"militiaunconvert", 852651), (b"clusterrockets", 852652), (b"robogoblin", 852656), (b"unrobogoblin", 852657),
    (b"summonfactory", 852658), (b"acidbomb", 852662), (b"chemicalrage", 852663), (b"healingspray", 852664),
    (b"transmute", 852665), (b"lavamonster", 852667), (b"soulburn", 852668), (b"volcano", 852669),
    (b"incineratearrow", 852670), (b"incineratearrowon", 852671), (b"incineratearrowoff", 852672),
];

fn mentions_e<'x>(e: &'x P, out: &mut FxSet<&'x [u8]>) {
    let _g = Guard::enter();
    if refused() {
        return;
    }
    match &**e {
        E::Name(n, _) => {
            out.insert(n);
        }
        E::Call(_, args, _) => {
            for a in args {
                mentions_e(a, out);
            }
        }
        E::Index(b, i, _) => {
            mentions_e(b, out);
            mentions_e(i, out);
        }
        E::Unary(_, x, _) | E::Paren(x, _) => mentions_e(x, out),
        E::Binary(_, l, r, _) => {
            mentions_e(l, out);
            mentions_e(r, out);
        }
        _ => {}
    }
}

fn mentions_st<'x>(s: &'x St, out: &mut FxSet<&'x [u8]>) {
    let _g = Guard::enter();
    if refused() {
        return;
    }
    match s {
        St::Set { target, value, .. } => {
            mentions_e(target, out);
            mentions_e(value, out);
        }
        St::Call { call, .. } => mentions_e(call, out),
        St::If(s) => {
            for (c, b) in &s.branches {
                if let Some(c) = c {
                    mentions_e(c, out);
                }
                for x in b {
                    mentions_st(x, out);
                }
            }
        }
        St::Loop { body, .. } => {
            for x in body {
                mentions_st(x, out);
            }
        }
        St::Exit { cond, .. } => mentions_e(cond, out),
        St::Ret { value: Some(v), .. } => mentions_e(v, out),
        St::Debug { stmt, .. } => mentions_st(stmt, out),
        _ => {}
    }
}

fn assigned_st<'x, 'a>(s: &'x St<'a>, out: &mut FxMap<&'x [u8], Vec<&'x P<'a>>>) {
    let _g = Guard::enter();
    if refused() {
        return;
    }
    match s {
        St::Set { target, value, .. } => {
            let name: &[u8] = match &**bare(target) {
                E::Name(n, _) => n,
                E::Index(b, _, _) => match &**bare(b) {
                    E::Name(n, _) => n,
                    _ => {
                        refuse();
                        return;
                    }
                },
                _ => {
                    refuse();
                    return;
                }
            };
            out.entry(name).or_default().push(value);
        }
        St::If(s) => {
            for (_c, b) in &s.branches {
                for x in b {
                    assigned_st(x, out);
                }
            }
        }
        St::Loop { body, .. } => {
            for x in body {
                assigned_st(x, out);
            }
        }
        St::Debug { stmt, .. } => assigned_st(stmt, out),
        _ => {}
    }
}

fn globals_info(src: &[u8]) -> Option<(Vec<Vec<u8>>, Vec<Vec<u8>>)> {
    let script = parse(src).ok()?;
    let mut types: FxSet<&[u8]> = FxSet::default();
    let mut globals: Vec<&Decl> = Vec::new();
    let mut funcs: Vec<&Func> = Vec::new();
    for item in &script.items {
        match item {
            Item::Globals(g) => {
                for d in &g.decls {
                    if !d.is_array {
                        types.insert(&d.name);
                    }
                    globals.push(d);
                }
            }
            Item::Func(f) if !f.is_native => funcs.push(f),
            _ => {}
        }
    }
    let mut assigned: FxMap<&[u8], Vec<&P>> = FxMap::default();
    let mut uses: FxMap<&[u8], (bool, bool)> = FxMap::default();
    let mut always: FxSet<&[u8]> = FxSet::default();
    for f in &funcs {
        let body: Vec<&St> = f.body.iter().filter(|s| not_comment(s)).collect();
        if f.params.is_empty() && f.locals.is_empty() && &f.ret[..] == b"boolean" && body.len() == 1 {
            if let St::Ret { value: Some(v), .. } = body[0] {
                if let E::Lit(_, t, _) = &**bare(v) {
                    if &t[..] == b"true" {
                        always.insert(&f.name);
                    }
                }
            }
        }
        for s in &f.body {
            assigned_st(s, &mut assigned);
        }
        let mut own: FxSet<&[u8]> = FxSet::default();
        for (_t, p) in &f.params {
            own.insert(p);
        }
        for d in &f.locals {
            own.insert(&d.name);
        }
        let mut seen: FxSet<&[u8]> = FxSet::default();
        for k in 0..f.locals.len() + body.len() {
            let mut names: FxSet<&[u8]> = FxSet::default();
            let stmt = if k < f.locals.len() {
                if let Some(i) = &f.locals[k].init {
                    mentions_e(i, &mut names);
                }
                None
            } else {
                let s = body[k - f.locals.len()];
                mentions_st(s, &mut names);
                Some(s)
            };
            for g in names.iter() {
                if seen.contains(g) || own.contains(g) || !types.contains(g) {
                    continue;
                }
                let first = match stmt {
                    Some(St::Set { target, value, .. }) => match &**bare(target) {
                        E::Name(n, _) if &n[..] == *g => {
                            let mut m: FxSet<&[u8]> = FxSet::default();
                            mentions_e(value, &mut m);
                            !m.contains(g)
                        }
                        _ => false,
                    },
                    _ => false,
                };
                let u = uses.entry(g).or_insert((false, true));
                u.0 = true;
                u.1 = u.1 && first;
            }
            seen.extend(names);
        }
    }
    if refused() {
        return None;
    }
    let mut frozen: Vec<Vec<u8>> = Vec::new();
    let mut fset: FxSet<&[u8]> = FxSet::default();
    for g in &globals {
        if g.is_array || g.is_constant {
            continue;
        }
        let ty: &[u8] = &g.ty;
        if ty != b"boolexpr" && ty != b"filterfunc" && ty != b"conditionfunc" {
            continue;
        }
        let ok = match assigned.get(&g.name[..]) {
            None => match &g.init {
                None => true,
                Some(v) => matches!(&**bare(v), E::Lit(LK::Null, _, _)),
            },
            Some(values) if values.len() == 1 => match &**bare(values[0]) {
                E::Call(n, args, _) if (&n[..] == b"Filter" || &n[..] == b"Condition") && args.len() == 1 => {
                    match &**bare(&args[0]) {
                        E::FuncRef(r, _) => always.contains(&r[..]),
                        _ => false,
                    }
                }
                _ => false,
            },
            _ => false,
        };
        if ok && fset.insert(&g.name) {
            frozen.push(g.name.to_vec());
        }
    }
    let mut temps: Vec<Vec<u8>> = uses.iter().filter(|(_g, u)| u.0 && u.1).map(|(g, _u)| g.to_vec()).collect();
    temps.sort();
    Some((frozen, temps))
}

fn put_list(items: &[Vec<u8>], out: &mut Vec<u8>) {
    out.extend_from_slice(&(items.len() as u32).to_le_bytes());
    for x in items {
        out.extend_from_slice(&(x.len() as u32).to_le_bytes());
        out.extend_from_slice(x);
    }
}

#[no_mangle]
pub extern "C" fn jass_standard_globals(text: *const u8, len: usize, out: *mut *mut u8, out_len: *mut usize) -> i32 {
    if (text.is_null() && len > 0) || out.is_null() || out_len.is_null() {
        return 3;
    }
    let data = input(text, len);
    match on_big_stack(move || match globals_info(&data) {
        Some((frozen, temps)) => {
            let mut b = Vec::new();
            put_list(&frozen, &mut b);
            put_list(&temps, &mut b);
            Ok(b)
        }
        None => Err(1),
    }) {
        Ok(b) => {
            give(b, out, out_len);
            0
        }
        Err(c) => c,
    }
}

#[no_mangle]
pub extern "C" fn jass_game_calls(
    text: *const u8,
    len: usize,
    names: *const u8,
    names_len: usize,
    out: *mut *mut u8,
    out_len: *mut usize,
) -> i32 {
    if (text.is_null() && len > 0) || (names.is_null() && names_len > 0) || out.is_null() || out_len.is_null() {
        return 3;
    }
    let data = input(text, len);
    let nm = input(names, names_len);
    match on_big_stack(move || {
        let mut map: FxMap<&[u8], &[u8]> = FxMap::default();
        for line in nm.split(|&c| c == b'\n') {
            if line.is_empty() {
                continue;
            }
            let k = line.iter().position(|&c| c == b'\t').ok_or(3)?;
            map.insert(&line[..k], &line[k + 1..]);
        }
        let toks = tokenize(&data);
        let n = toks.len() - 1;
        let tok = |k: usize| -> &[u8] { &data[toks[k].s as usize..toks[k].e as usize] };
        let mut text_out: Vec<u8> = Vec::with_capacity(data.len() + 1024);
        let mut last = 0usize;
        let mut calls: u32 = 0;
        let mut used: Vec<Vec<u8>> = Vec::new();
        let mut used_set: FxSet<Vec<u8>> = FxSet::default();
        let mut prev: &[u8] = b"";
        for k in 0..n {
            let t = tok(k);
            if let Some(new) = map.get(t) {
                let nxt: &[u8] = if k + 1 < n { tok(k + 1) } else { b"" };
                if prev == b"function" && nxt == b"takes" {
                } else if nxt == b"(" || prev == b"function" {
                    text_out.extend_from_slice(&data[last..toks[k].s as usize]);
                    text_out.extend_from_slice(new);
                    last = toks[k].e as usize;
                    calls += 1;
                } else if used_set.insert(t.to_vec()) {
                    used.push(t.to_vec());
                }
            } else if toks[k].k == K::Str {
                let inner = &t[1..t.len() - 1];
                if map.contains_key(inner) && used_set.insert(inner.to_vec()) {
                    used.push(inner.to_vec());
                }
            }
            prev = t;
        }
        text_out.extend_from_slice(&data[last..]);
        let mut b = Vec::with_capacity(text_out.len() + 64);
        b.extend_from_slice(&calls.to_le_bytes());
        put_list(&used, &mut b);
        b.extend_from_slice(&text_out);
        Ok(b)
    }) {
        Ok(b) => {
            give(b, out, out_len);
            0
        }
        Err(c) => c,
    }
}
