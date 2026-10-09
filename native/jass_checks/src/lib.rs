// The JASS script checks of script_checks.py in Rust (no dependencies): the same parser, rules and result, as a library the engine loads.
use std::collections::{HashMap, HashSet};
use std::panic;

mod canon;
mod canon_jass;
mod canon_lua;
mod slk;

#[derive(Clone, Copy, PartialEq)]
enum K {
    Word,
    Nl,
    Comment,
    Num,
    Str,
    Raw,
    Other,
    Eof,
}

#[derive(Clone, Copy)]
struct Tok {
    k: K,
    s: usize,
    e: usize,
}

fn char_len(b: u8) -> usize {
    if b < 0x80 {
        1
    } else if b >> 5 == 0b110 {
        2
    } else if b >> 4 == 0b1110 {
        3
    } else if b >> 3 == 0b11110 {
        4
    } else {
        1
    }
}

fn is_word_start(b: u8) -> bool {
    b.is_ascii_alphabetic() || b == b'_'
}
fn is_word(b: u8) -> bool {
    b.is_ascii_alphanumeric() || b == b'_'
}

fn tokenize(t: &[u8]) -> Vec<Tok> {
    let n = t.len();
    let mut out = Vec::with_capacity(n / 3 + 8);
    let mut i = 0;
    loop {
        loop {
            if i < n && (t[i] == b' ' || t[i] == b'\t') {
                i += 1;
            } else if i + 2 < n + 0 && i + 3 <= n && t[i] == 0xEF && t[i + 1] == 0xBB && t[i + 2] == 0xBF {
                i += 3;
            } else {
                break;
            }
        }
        if i >= n {
            break;
        }
        let s = i;
        let c = t[i];
        let (k, e) = if is_word_start(c) {
            let mut j = i + 1;
            while j < n && is_word(t[j]) {
                j += 1;
            }
            (K::Word, j)
        } else if c == b'(' || c == b')' || c == b',' {
            (K::Other, i + 1)
        } else if c == b'\r' {
            (K::Nl, if i + 1 < n && t[i + 1] == b'\n' { i + 2 } else { i + 1 })
        } else if c == b'\n' {
            (K::Nl, i + 1)
        } else if (c == b'=' || c == b'!' || c == b'<' || c == b'>') && i + 1 < n && t[i + 1] == b'=' {
            (K::Other, i + 2)
        } else if c == b'/' && i + 1 < n && t[i + 1] == b'/' {
            let mut j = i + 2;
            while j < n && t[j] != b'\r' && t[j] != b'\n' {
                j += 1;
            }
            (K::Comment, j)
        } else if matches!(c, b'-' | b'+' | b'*' | b'/' | b'<' | b'>' | b'=' | b'[' | b']') {
            (K::Other, i + 1)
        } else if let Some(e) = number(t, i) {
            (K::Num, e)
        } else if c == b'"' || c == b'\'' {
            match quoted(t, i, c) {
                Some(e) => (if c == b'"' { K::Str } else { K::Raw }, e),
                None => (K::Other, i + 1),
            }
        } else {
            (K::Other, i + char_len(c).min(n - i))
        };
        out.push(Tok { k, s, e });
        i = e;
    }
    out.push(Tok { k: K::Eof, s: n, e: n });
    out
}

fn hex_run(t: &[u8], i: usize) -> usize {
    let mut j = i;
    while j < t.len() && t[j].is_ascii_hexdigit() {
        j += 1;
    }
    j
}
fn dec_run(t: &[u8], i: usize) -> usize {
    let mut j = i;
    while j < t.len() && t[j].is_ascii_digit() {
        j += 1;
    }
    j
}

fn number(t: &[u8], i: usize) -> Option<usize> {
    let n = t.len();
    let c = t[i];
    if c == b'0' && i + 1 < n && (t[i + 1] == b'x' || t[i + 1] == b'X') {
        let j = hex_run(t, i + 2);
        if j > i + 2 {
            return Some(j);
        }
    }
    if c == b'$' {
        let j = hex_run(t, i + 1);
        if j > i + 1 {
            return Some(j);
        }
    }
    if c.is_ascii_digit() {
        let j = dec_run(t, i);
        if j < n && t[j] == b'.' {
            return Some(dec_run(t, j + 1));
        }
    }
    if c == b'.' {
        let j = dec_run(t, i + 1);
        if j > i + 1 {
            return Some(j);
        }
    }
    if c.is_ascii_digit() {
        return Some(dec_run(t, i));
    }
    None
}

fn quoted(t: &[u8], i: usize, q: u8) -> Option<usize> {
    let n = t.len();
    let mut j = i + 1;
    while j < n {
        let b = t[j];
        if b == q {
            return Some(j + 1);
        }
        if b == b'\\' {
            if j + 1 >= n {
                return None;
            }
            j += 1 + char_len(t[j + 1]).min(n - j - 1);
            continue;
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

#[derive(Clone, Copy, PartialEq)]
enum Lit {
    Integer,
    Real,
    Str,
    Raw,
    Boolean,
    Null,
}

enum Expr {
    Name { name: String },
    Index { base: Box<Expr>, index: Box<Expr> },
    Call { name: String, args: Vec<Expr>, line: usize },
    FuncRef { name: String },
    Literal { kind: Lit, text: Vec<u8> },
    Unary { op: &'static str, operand: Box<Expr> },
    Binary { op: &'static str, left: Box<Expr>, right: Box<Expr> },
    Paren { inner: Box<Expr> },
}

enum Stmt {
    Set { target: Expr, value: Expr, line: usize },
    Call { call: Expr, line: usize },
    If { branches: Vec<(Option<Expr>, Vec<Stmt>)> },
    Loop { body: Vec<Stmt> },
    ExitWhen { cond: Expr },
    Return { value: Option<Expr> },
    Comment,
    Debug { stmt: Box<Stmt> },
}

struct LocalDecl {
    name: String,
    init: Option<Expr>,
    line: usize,
}

struct GlobalDecl {
    name: String,
    typ: String,
    is_array: bool,
    is_constant: bool,
    has_init: bool,
    init: Option<Expr>,
}

struct Function {
    name: String,
    params: Vec<String>,
    locals: Vec<LocalDecl>,
    body: Vec<Stmt>,
}

struct Script {
    functions: Vec<Function>,
    natives: Vec<Function>,
    globals: Vec<GlobalDecl>,
}

const KEYWORDS: [&str; 31] = [
    "globals", "endglobals", "native", "constant", "type", "extends", "function", "endfunction", "takes", "returns",
    "nothing", "local", "array", "set", "call", "if", "then", "elseif", "else", "endif", "loop", "endloop", "exitwhen",
    "return", "debug", "and", "or", "not", "true", "false", "null",
];
const BLOCK_WORDS: [&str; 11] =
    ["endfunction", "endif", "endloop", "else", "elseif", "globals", "endglobals", "function", "native", "type", "constant"];
const MAX_DEPTH: usize = 100_000;

struct Fail;
type R<T> = Result<T, Fail>;

struct P<'a> {
    t: &'a [u8],
    toks: Vec<Tok>,
    i: usize,
    line: usize,
    depth: usize,
}

fn prec(op: &[u8]) -> Option<u32> {
    Some(match op {
        b"and" => 1,
        b"or" => 2,
        b"==" | b"!=" | b"<" | b"<=" | b">" | b">=" => 3,
        b"+" | b"-" => 5,
        b"*" | b"/" => 6,
        _ => return None,
    })
}

fn op_static(op: &[u8]) -> &'static str {
    match op {
        b"and" => "and",
        b"or" => "or",
        b"==" => "==",
        b"!=" => "!=",
        b"<" => "<",
        b"<=" => "<=",
        b">" => ">",
        b">=" => ">=",
        b"+" => "+",
        b"-" => "-",
        b"*" => "*",
        _ => "/",
    }
}

impl<'a> P<'a> {
    fn tok(&self, k: usize) -> Tok {
        self.toks[k.min(self.toks.len() - 1)]
    }
    fn txt(&self, k: usize) -> &'a [u8] {
        let t = self.tok(k);
        &self.t[t.s..t.e]
    }
    fn cur(&self) -> &'a [u8] {
        self.txt(self.i)
    }
    fn kind(&self) -> K {
        self.tok(self.i).k
    }
    fn is(&self, w: &str) -> bool {
        self.kind() != K::Eof && self.cur() == w.as_bytes()
    }
    fn is_nl(&self) -> bool {
        self.kind() == K::Nl
    }
    fn is_keyword(w: &[u8]) -> bool {
        KEYWORDS.iter().any(|k| k.as_bytes() == w)
    }
    fn is_ident_tok(&self, k: usize) -> bool {
        let t = self.tok(k);
        t.k == K::Word && !Self::is_keyword(&self.t[t.s..t.e])
    }
    fn expect(&mut self, w: &str) -> R<()> {
        if !self.is(w) {
            return Err(Fail);
        }
        self.i += 1;
        Ok(())
    }
    fn identifier(&mut self) -> R<String> {
        if self.is_ident_tok(self.i) {
            let s = String::from_utf8_lossy(self.cur()).into_owned();
            self.i += 1;
            return Ok(s);
        }
        Err(Fail)
    }
    fn end_of_line(&mut self) -> R<()> {
        if self.kind() == K::Comment {
            self.i += 1;
        }
        if self.is_nl() {
            self.i += 1;
            self.line += 1;
        } else if self.kind() != K::Eof {
            return Err(Fail);
        }
        Ok(())
    }

    fn script(&mut self) -> R<Script> {
        let mut s = Script { functions: vec![], natives: vec![], globals: vec![] };
        loop {
            match self.kind() {
                K::Nl => {
                    self.i += 1;
                    self.line += 1;
                    continue;
                }
                K::Eof => break,
                K::Comment => {
                    self.i += 1;
                    self.end_of_line()?;
                    continue;
                }
                _ => {}
            }
            let is_constant = self.is("constant");
            if is_constant {
                self.i += 1;
            }
            if self.is("function") {
                let f = self.function()?;
                s.functions.push(f);
            } else if self.is("native") {
                let f = self.native()?;
                s.natives.push(f);
            } else if self.is("globals") && !is_constant {
                self.globals_block(&mut s.globals)?;
            } else if self.is("type") && !is_constant {
                self.i += 1;
                self.identifier()?;
                self.expect("extends")?;
                self.identifier()?;
                self.end_of_line()?;
            } else {
                return Err(Fail);
            }
        }
        Ok(s)
    }

    fn globals_block(&mut self, out: &mut Vec<GlobalDecl>) -> R<()> {
        self.i += 1;
        self.end_of_line()?;
        loop {
            match self.kind() {
                K::Nl => {
                    self.i += 1;
                    self.line += 1;
                    continue;
                }
                K::Comment => {
                    self.i += 1;
                    self.end_of_line()?;
                    continue;
                }
                K::Eof => return Err(Fail),
                _ => {}
            }
            if self.is("endglobals") {
                self.i += 1;
                self.end_of_line()?;
                return Ok(());
            }
            let is_constant = self.is("constant");
            if is_constant {
                self.i += 1;
            }
            let typ = self.identifier()?;
            let is_array = self.is("array");
            if is_array {
                self.i += 1;
            }
            let name = self.identifier()?;
            let mut init = None;
            if self.is("=") {
                self.i += 1;
                init = Some(self.expression(0)?);
            }
            let has_init = init.is_some();
            out.push(GlobalDecl { name, typ, is_array, is_constant, has_init, init });
            self.end_of_line()?;
        }
    }

    fn signature(&mut self, f: &mut Function) -> R<()> {
        f.name = self.identifier()?;
        self.expect("takes")?;
        if self.is("nothing") {
            self.i += 1;
        } else {
            loop {
                self.identifier()?;
                let pname = self.identifier()?;
                f.params.push(pname);
                if !self.is(",") {
                    break;
                }
                self.i += 1;
            }
        }
        self.expect("returns")?;
        if self.is("nothing") {
            self.i += 1;
        } else {
            self.identifier()?;
        }
        self.end_of_line()
    }

    fn native(&mut self) -> R<Function> {
        self.i += 1;
        let mut f = Function { name: String::new(), params: vec![], locals: vec![], body: vec![] };
        self.signature(&mut f)?;
        Ok(f)
    }

    fn function(&mut self) -> R<Function> {
        self.i += 1;
        let mut f = Function { name: String::new(), params: vec![], locals: vec![], body: vec![] };
        self.signature(&mut f)?;
        let mut pending: Vec<Stmt> = vec![];
        loop {
            match self.kind() {
                K::Nl => {
                    self.i += 1;
                    self.line += 1;
                }
                K::Comment => {
                    pending.push(Stmt::Comment);
                    self.i += 1;
                    self.end_of_line()?;
                }
                _ if self.is("local") => {
                    let d = self.local_decl()?;
                    f.locals.push(d);
                }
                _ => break,
            }
        }
        f.body = self.block(pending, &["endfunction"])?;
        self.i += 1;
        self.end_of_line()?;
        Ok(f)
    }

    fn local_decl(&mut self) -> R<LocalDecl> {
        let line = self.line;
        self.i += 1;
        self.identifier()?;
        if self.is("array") {
            self.i += 1;
        }
        let name = self.identifier()?;
        let mut init = None;
        if self.is("=") {
            self.i += 1;
            init = Some(self.expression(0)?);
        }
        self.end_of_line()?;
        Ok(LocalDecl { name, init, line })
    }

    fn statement_word(&self) -> Option<u8> {
        if self.kind() != K::Word {
            return None;
        }
        Some(match self.cur() {
            b"set" => 1,
            b"call" => 2,
            b"if" => 3,
            b"loop" => 4,
            b"exitwhen" => 5,
            b"return" => 6,
            b"debug" => 7,
            _ => return None,
        })
    }

    fn statement(&mut self, w: u8) -> R<Stmt> {
        self.depth += 1;
        if self.depth > MAX_DEPTH {
            return Err(Fail);
        }
        let r = match w {
            1 => self.set_stmt(),
            2 => self.call_stmt(),
            3 => self.if_stmt(),
            4 => self.loop_stmt(),
            5 => {
                self.i += 1;
                let cond = self.expression(0)?;
                self.end_of_line()?;
                Ok(Stmt::ExitWhen { cond })
            }
            6 => {
                self.i += 1;
                let k = self.kind();
                let value = if k != K::Nl && k != K::Eof && k != K::Comment { Some(self.expression(0)?) } else { None };
                self.end_of_line()?;
                Ok(Stmt::Return { value })
            }
            _ => {
                self.i += 1;
                match self.statement_word() {
                    Some(w2) if w2 != 7 => {
                        let s = self.statement(w2)?;
                        Ok(Stmt::Debug { stmt: Box::new(s) })
                    }
                    _ => Err(Fail),
                }
            }
        };
        self.depth -= 1;
        r
    }

    fn block(&mut self, mut body: Vec<Stmt>, enders: &[&str]) -> R<Vec<Stmt>> {
        loop {
            if self.is_nl() {
                self.i += 1;
                self.line += 1;
                continue;
            }
            if let Some(w) = self.statement_word() {
                let s = self.statement(w)?;
                body.push(s);
                continue;
            }
            if self.kind() == K::Word && enders.iter().any(|e| self.cur() == e.as_bytes()) {
                return Ok(body);
            }
            if self.kind() == K::Comment {
                body.push(Stmt::Comment);
                self.i += 1;
                self.end_of_line()?;
                continue;
            }
            let _ = BLOCK_WORDS;
            return Err(Fail);
        }
    }

    fn set_stmt(&mut self) -> R<Stmt> {
        let line = self.line;
        self.i += 1;
        let name = self.identifier()?;
        let mut target = Expr::Name { name };
        if self.is("[") {
            self.i += 1;
            let index = self.expression(0)?;
            target = Expr::Index { base: Box::new(target), index: Box::new(index) };
            self.expect("]")?;
        }
        self.expect("=")?;
        let value = self.expression(0)?;
        self.end_of_line()?;
        Ok(Stmt::Set { target, value, line })
    }

    fn call_stmt(&mut self) -> R<Stmt> {
        let line = self.line;
        self.i += 1;
        let name = self.identifier()?;
        self.expect("(")?;
        let args = self.arguments()?;
        self.end_of_line()?;
        Ok(Stmt::Call { call: Expr::Call { name, args, line }, line })
    }

    fn if_stmt(&mut self) -> R<Stmt> {
        self.i += 1;
        let cond = self.expression(0)?;
        self.expect("then")?;
        self.end_of_line()?;
        let mut branches = vec![];
        let body = self.block(vec![], &["elseif", "else", "endif"])?;
        branches.push((Some(cond), body));
        loop {
            let t = self.cur();
            self.i += 1;
            if t == b"elseif" {
                let cond = self.expression(0)?;
                self.expect("then")?;
                self.end_of_line()?;
                let body = self.block(vec![], &["elseif", "else", "endif"])?;
                branches.push((Some(cond), body));
            } else if t == b"else" {
                self.end_of_line()?;
                let body = self.block(vec![], &["endif"])?;
                branches.push((None, body));
            } else {
                self.end_of_line()?;
                return Ok(Stmt::If { branches });
            }
        }
    }

    fn loop_stmt(&mut self) -> R<Stmt> {
        self.i += 1;
        self.end_of_line()?;
        let body = self.block(vec![], &["endloop"])?;
        self.i += 1;
        self.end_of_line()?;
        Ok(Stmt::Loop { body })
    }

    fn expression(&mut self, min: u32) -> R<Expr> {
        self.depth += 1;
        if self.depth > MAX_DEPTH {
            return Err(Fail);
        }
        let mut left = self.unary()?;
        loop {
            if self.kind() == K::Eof {
                break;
            }
            let op = self.cur();
            let p = match prec(op) {
                Some(p) if p >= min => p,
                _ => break,
            };
            self.i += 1;
            let right = self.expression(p + 1)?;
            left = Expr::Binary { op: op_static(op), left: Box::new(left), right: Box::new(right) };
        }
        self.depth -= 1;
        Ok(left)
    }

    fn unary(&mut self) -> R<Expr> {
        self.depth += 1;
        if self.depth > MAX_DEPTH {
            return Err(Fail);
        }
        let r = self.unary_inner();
        self.depth -= 1;
        r
    }

    fn unary_inner(&mut self) -> R<Expr> {
        let i = self.i;
        let tk = self.tok(i);
        if tk.k == K::Eof {
            return Err(Fail);
        }
        let t = self.txt(i);
        let c = t[0];
        if self.is_ident_tok(i) {
            let nxt = self.tok(i + 1);
            let nt = &self.t[nxt.s..nxt.e];
            let name = String::from_utf8_lossy(t).into_owned();
            let line = self.line;
            if nxt.k != K::Eof && nt == b"(" {
                self.i = i + 2;
                let args = self.arguments()?;
                return Ok(Expr::Call { name, args, line });
            }
            if nxt.k != K::Eof && nt == b"[" {
                self.i = i + 2;
                let index = self.expression(0)?;
                self.expect("]")?;
                return Ok(Expr::Index { base: Box::new(Expr::Name { name }), index: Box::new(index) });
            }
            self.i = i + 1;
            return Ok(Expr::Name { name });
        }
        if t == b"(" {
            self.i = i + 1;
            let inner = self.expression(0)?;
            self.expect(")")?;
            return Ok(Expr::Paren { inner: Box::new(inner) });
        }
        if c.is_ascii_digit() || ((c == b'.' || c == b'$') && t.len() > 1) {
            self.i = i + 1;
            let kind = if t.contains(&b'.') { Lit::Real } else { Lit::Integer };
            return Ok(Expr::Literal { kind, text: t.to_vec() });
        }
        if c == b'"' || c == b'\'' {
            if t.len() < 2 {
                return Err(Fail);
            }
            self.i = i + 1;
            self.line += line_breaks(t);
            return Ok(Expr::Literal { kind: if c == b'"' { Lit::Str } else { Lit::Raw }, text: t.to_vec() });
        }
        if tk.k == K::Word {
            match t {
                b"not" => {
                    self.i = i + 1;
                    let e = self.expression(5)?;
                    return Ok(Expr::Unary { op: "not", operand: Box::new(e) });
                }
                b"true" | b"false" => {
                    self.i = i + 1;
                    return Ok(Expr::Literal { kind: Lit::Boolean, text: t.to_vec() });
                }
                b"null" => {
                    self.i = i + 1;
                    return Ok(Expr::Literal { kind: Lit::Null, text: t.to_vec() });
                }
                b"function" => {
                    self.i = i + 1;
                    let name = self.identifier()?;
                    return Ok(Expr::FuncRef { name });
                }
                _ => {}
            }
        }
        if t == b"-" || t == b"+" {
            self.i = i + 1;
            let e = self.unary()?;
            return Ok(Expr::Unary { op: if t == b"-" { "-" } else { "+" }, operand: Box::new(e) });
        }
        Err(Fail)
    }

    fn arguments(&mut self) -> R<Vec<Expr>> {
        if self.is(")") {
            self.i += 1;
            return Ok(vec![]);
        }
        let mut args = vec![self.expression(0)?];
        loop {
            if self.is(",") {
                self.i += 1;
                args.push(self.expression(0)?);
            } else if self.is(")") {
                self.i += 1;
                return Ok(args);
            } else {
                return Err(Fail);
            }
        }
    }
}

#[derive(Clone, Copy)]
enum N<'a> {
    L(&'a LocalDecl),
    S(&'a Stmt),
    E(&'a Expr),
}

fn push_children<'a>(n: N<'a>, out: &mut Vec<N<'a>>) {
    match n {
        N::L(d) => {
            if let Some(e) = &d.init {
                out.push(N::E(e));
            }
        }
        N::S(s) => match s {
            Stmt::Set { target, value, .. } => {
                out.push(N::E(target));
                out.push(N::E(value));
            }
            Stmt::Call { call, .. } => out.push(N::E(call)),
            Stmt::If { branches } => {
                for (c, body) in branches {
                    if let Some(c) = c {
                        out.push(N::E(c));
                    }
                    for st in body {
                        out.push(N::S(st));
                    }
                }
            }
            Stmt::Loop { body } => {
                for st in body {
                    out.push(N::S(st));
                }
            }
            Stmt::ExitWhen { cond } => out.push(N::E(cond)),
            Stmt::Return { value } => {
                if let Some(v) = value {
                    out.push(N::E(v));
                }
            }
            Stmt::Comment => {}
            Stmt::Debug { stmt } => out.push(N::S(stmt)),
        },
        N::E(e) => match e {
            Expr::Index { base, index } => {
                out.push(N::E(base));
                out.push(N::E(index));
            }
            Expr::Call { args, .. } => {
                for a in args {
                    out.push(N::E(a));
                }
            }
            Expr::Unary { operand, .. } => out.push(N::E(operand)),
            Expr::Binary { left, right, .. } => {
                out.push(N::E(left));
                out.push(N::E(right));
            }
            Expr::Paren { inner } => out.push(N::E(inner)),
            _ => {}
        },
    }
}

fn walk_from<'a>(start: Vec<N<'a>>, mut visit: impl FnMut(N<'a>)) {
    let mut stack: Vec<N<'a>> = start.into_iter().rev().collect();
    let mut kids: Vec<N<'a>> = Vec::new();
    while let Some(n) = stack.pop() {
        visit(n);
        kids.clear();
        push_children(n, &mut kids);
        for k in kids.iter().rev() {
            stack.push(*k);
        }
    }
}

fn walk_function<'a>(f: &'a Function, visit: impl FnMut(N<'a>)) {
    let mut start: Vec<N<'a>> = f.locals.iter().map(N::L).collect();
    start.extend(f.body.iter().map(N::S));
    walk_from(start, visit);
}

fn walk_expr<'a>(e: &'a Expr, visit: impl FnMut(N<'a>)) {
    walk_from(vec![N::E(e)], visit);
}

fn bprec(op: &str) -> u32 {
    prec(op.as_bytes()).unwrap_or(0)
}

fn needs_parens(child: &str, parent: &str, right: bool) -> bool {
    let (p, q) = (bprec(child), bprec(parent));
    p < q || (right && p == q && !(child == parent && matches!(child, "+" | "*" | "and" | "or")))
}

fn ue(e: &Expr) -> String {
    match e {
        Expr::Name { name, .. } => name.clone(),
        Expr::Call { name, args, .. } => {
            let parts: Vec<String> = args.iter().map(ue).collect();
            format!("{}({})", name, parts.join(", "))
        }
        Expr::Literal { text, .. } => String::from_utf8_lossy(text).into_owned(),
        Expr::Binary { .. } => {
            let mut chain: Vec<&Expr> = vec![];
            let mut cur = e;
            while let Expr::Binary { left, .. } = cur {
                chain.push(cur);
                cur = left;
            }
            chain.reverse();
            let mut text = ue(cur);
            for k in 0..chain.len() {
                if let Expr::Binary { op, right, .. } = chain[k] {
                    let mut r = ue(right);
                    if let Expr::Binary { op: rop, .. } = &**right {
                        if needs_parens(rop, op, true) {
                            r = format!("({})", r);
                        }
                    }
                    text = format!("{} {} {}", text, op, r);
                    if k + 1 < chain.len() {
                        if let Expr::Binary { op: pop, .. } = chain[k + 1] {
                            if needs_parens(op, pop, false) {
                                text = format!("({})", text);
                            }
                        }
                    }
                }
            }
            text
        }
        Expr::Paren { inner } => format!("({})", ue(inner)),
        Expr::Index { base, index } => format!("{}[{}]", ue(base), ue(index)),
        Expr::Unary { op, operand } => {
            let mut inner = ue(operand);
            if let Expr::Binary { op: bop, .. } = &**operand {
                if *op != "not" || bprec(bop) < 5 {
                    inner = format!("({})", inner);
                }
            }
            if *op == "not" {
                format!("not {}", inner)
            } else {
                format!("{}{}", op, inner)
            }
        }
        Expr::FuncRef { name } => format!("function {}", name),
    }
}

fn unescape(body: &[u8]) -> Vec<u8> {
    let mut out = Vec::with_capacity(body.len());
    let mut i = 0;
    while i < body.len() {
        if body[i] == b'\\' && i + 1 < body.len() {
            let c = body[i + 1];
            let mapped = match c {
                b'n' => Some(b'\n'),
                b't' => Some(b'\t'),
                b'r' => Some(b'\r'),
                b'b' => Some(0x08),
                b'f' => Some(0x0C),
                b'"' => Some(b'"'),
                b'\\' => Some(b'\\'),
                b'\'' => Some(b'\''),
                _ => None,
            };
            let l = char_len(c).min(body.len() - i - 1);
            match mapped {
                Some(m) => out.push(m),
                None => out.extend_from_slice(&body[i + 1..i + 1 + l]),
            }
            i += 1 + l;
        } else {
            out.push(body[i]);
            i += 1;
        }
    }
    out
}

fn creator(name: &str) -> Option<(&'static str, &'static str)> {
    const LOC: [&str; 16] = [
        "Location", "GetUnitLoc", "GetSpellTargetLoc", "GetOrderPointLoc", "GetRectCenter", "GetRandomLocInRect",
        "PolarProjectionBJ", "OffsetLocation", "GetUnitRallyPoint", "GetPlayerStartLocationLoc",
        "GetCameraTargetPositionLoc", "GetCameraEyePositionLoc", "CameraSetupGetDestPositionLoc", "GetDestructableLoc",
        "GetItemLoc", "GetLocationOf",
    ];
    const GRP: [&str; 12] = [
        "CreateGroup", "GetUnitsInRangeOfLocAll", "GetUnitsInRangeOfLocMatching", "GetUnitsInRectAll",
        "GetUnitsInRectMatching", "GetUnitsInRectOfPlayer", "GetUnitsOfPlayerAll", "GetUnitsOfPlayerMatching",
        "GetUnitsOfPlayerAndTypeId", "GetUnitsOfTypeIdAll", "GetUnitsSelectedAll", "GetRandomSubGroup",
    ];
    const FRC: [&str; 6] =
        ["CreateForce", "GetPlayersAllies", "GetPlayersEnemies", "GetPlayersMatching", "GetPlayersByMapControl", "GetForceOfPlayer"];
    const EFX: [&str; 9] = [
        "AddSpecialEffect", "AddSpecialEffectLoc", "AddSpecialEffectTarget", "AddSpellEffect", "AddSpellEffectLoc",
        "AddSpellEffectById", "AddSpellEffectByIdLoc", "AddSpellEffectTarget", "AddSpellEffectTargetById",
    ];
    if LOC.contains(&name) {
        Some(("location", "RemoveLocation"))
    } else if GRP.contains(&name) {
        Some(("group", "DestroyGroup"))
    } else if FRC.contains(&name) {
        Some(("force", "DestroyForce"))
    } else if EFX.contains(&name) {
        Some(("effect", "DestroyEffect"))
    } else {
        None
    }
}

fn is_destroyer(name: &str) -> bool {
    matches!(name, "RemoveLocation" | "DestroyGroup" | "DestroyForce" | "DestroyEffect")
}

const SYNC: [&str; 25] = [
    "ForGroup", "ForGroupBJ", "ForForce", "EnumDestructablesInRect", "EnumItemsInRect", "GroupEnumUnitsInRange",
    "GroupEnumUnitsInRangeOfLoc", "GroupEnumUnitsInRect", "GroupEnumUnitsOfPlayer", "GroupEnumUnitsOfType",
    "GroupEnumUnitsSelected", "GroupEnumUnitsInRangeCounted", "GroupEnumUnitsInRectCounted", "ForceEnumPlayers",
    "ForceEnumAllies", "ForceEnumEnemies", "EnumDestructablesInRectAll", "EnumItemsInRectBJ", "Filter", "Condition",
    "GetUnitsInRangeOfLocMatching", "GetUnitsInRectMatching", "GetUnitsOfPlayerMatching", "GetPlayersMatching",
    "ForGroupBJ",
];
const HEATS: [&str; 4] = ["hot", "repeat", "once", "unused"];

fn is_true(e: &Expr) -> bool {
    match e {
        Expr::Literal { text, .. } => text == b"true",
        Expr::Name { name, .. } => name == "true",
        _ => false,
    }
}

fn refs(e: &Expr) -> Vec<String> {
    let mut out = vec![];
    walk_expr(e, |n| {
        if let N::E(Expr::FuncRef { name }) = n {
            out.push(name.clone());
        }
    });
    out
}

fn trigger_key(e: &Expr, fname: &str, own: &HashSet<&str>) -> String {
    let mut base = e;
    loop {
        match base {
            Expr::Index { base: b, .. } => base = b,
            Expr::Paren { inner } => base = inner,
            _ => break,
        }
    }
    let text = ue(e);
    if let Expr::Name { name, .. } = base {
        if own.contains(name.as_str()) {
            return format!("\u{1}{}\u{1}{}", fname, text);
        }
    }
    text
}

fn heat_of(s: &Script) -> HashMap<String, &'static str> {
    let funcs: HashSet<&str> = s.functions.iter().map(|f| f.name.as_str()).collect();
    let mut edges: HashMap<&str, HashSet<String>> = funcs.iter().map(|n| (*n, HashSet::new())).collect();
    let mut hot_roots: HashSet<String> = HashSet::new();
    let mut cb_roots: HashSet<String> = HashSet::new();
    let mut trig_actions: HashMap<String, HashSet<String>> = HashMap::new();
    let mut periodic: HashSet<String> = HashSet::new();
    for f in &s.functions {
        let mut own: HashSet<&str> = f.params.iter().map(|p| p.as_str()).collect();
        own.extend(f.locals.iter().map(|l| l.name.as_str()));
        let mut calls: Vec<&Expr> = vec![];
        let mut sets: Vec<&Expr> = vec![];
        walk_function(f, |n| match n {
            N::E(e @ Expr::Call { .. }) => calls.push(e),
            N::S(Stmt::Set { value, .. }) => sets.push(value),
            _ => {}
        });
        for c in calls {
            if let Expr::Call { name, args, .. } = c {
                let name = name.as_str();
                if funcs.contains(name) {
                    edges.get_mut(f.name.as_str()).unwrap().insert(name.to_string());
                } else if name == "ExecuteFunc" && !args.is_empty() {
                    if let Expr::Literal { kind: Lit::Str, text } = &args[0] {
                        let v = unescape(&text[1..text.len() - 1]);
                        let v = String::from_utf8_lossy(&v).into_owned();
                        if funcs.contains(v.as_str()) {
                            edges.get_mut(f.name.as_str()).unwrap().insert(v);
                        }
                    }
                }
                if (name == "TriggerAddAction" || name == "TriggerAddCondition") && args.len() == 2 {
                    let k = trigger_key(&args[0], &f.name, &own);
                    trig_actions.entry(k).or_default().extend(refs(&args[1]));
                } else if name == "TriggerRegisterTimerEvent" && args.len() == 3 && is_true(&args[2]) {
                    periodic.insert(trigger_key(&args[0], &f.name, &own));
                } else if name == "TriggerRegisterTimerEventPeriodic" && !args.is_empty() {
                    periodic.insert(trigger_key(&args[0], &f.name, &own));
                } else if name == "TimerStart" && args.len() == 4 && is_true(&args[2]) {
                    hot_roots.extend(refs(&args[3]));
                }
                if SYNC.contains(&name) {
                    for a in args {
                        for r in refs(a) {
                            if funcs.contains(r.as_str()) {
                                edges.get_mut(f.name.as_str()).unwrap().insert(r);
                            }
                        }
                    }
                } else {
                    for a in args {
                        let take = match a {
                            Expr::FuncRef { .. } => true,
                            Expr::Call { name: an, .. } => an == "Condition" || an == "Filter",
                            _ => false,
                        };
                        if take {
                            for r in refs(a) {
                                if funcs.contains(r.as_str()) {
                                    cb_roots.insert(r);
                                }
                            }
                        }
                    }
                }
            }
        }
        for v in sets {
            for r in refs(v) {
                if funcs.contains(r.as_str()) {
                    cb_roots.insert(r);
                }
            }
        }
    }
    for trig in &periodic {
        if let Some(a) = trig_actions.get(trig) {
            hot_roots.extend(a.iter().cloned());
        }
    }
    for acts in trig_actions.values() {
        cb_roots.extend(acts.iter().cloned());
    }
    let reach = |roots: Vec<&str>| -> HashSet<String> {
        let mut seen: HashSet<String> = HashSet::new();
        let mut stack: Vec<String> = roots.into_iter().filter(|r| funcs.contains(r)).map(|r| r.to_string()).collect();
        while let Some(n) = stack.pop() {
            if seen.contains(&n) {
                continue;
            }
            if let Some(es) = edges.get(n.as_str()) {
                stack.extend(es.iter().cloned());
            }
            seen.insert(n);
        }
        seen
    };
    let hot = reach(hot_roots.iter().map(|s| s.as_str()).collect());
    let rep = reach(cb_roots.iter().map(|s| s.as_str()).collect());
    let once = reach(["main", "config"].iter().copied().filter(|n| funcs.contains(n)).collect());
    funcs
        .iter()
        .map(|n| {
            let h = if hot.contains(*n) {
                "hot"
            } else if rep.contains(*n) {
                "repeat"
            } else if once.contains(*n) {
                "once"
            } else {
                "unused"
            };
            (n.to_string(), h)
        })
        .collect()
}

struct Leak {
    rule: &'static str,
    creator: String,
    line: usize,
    extra: Option<(&'static str, String)>,
    function: String,
    heat: &'static str,
}

fn leaks_of(f: &Function, map_funcs: &HashSet<String>) -> Vec<Leak> {
    let mut out: Vec<Leak> = vec![];
    let mut want_destroy = false;
    walk_function(f, |n| {
        if let N::S(Stmt::Set { target, value, .. }) = n {
            if ue(target) == "bj_wantDestroyGroup" && is_true(value) {
                want_destroy = true;
            }
        }
    });
    let locals: HashSet<&str> = f.locals.iter().map(|l| l.name.as_str()).collect();
    let mut created_order: Vec<String> = vec![];
    let mut created: HashMap<String, (String, usize)> = HashMap::new();
    let mut escaped: HashSet<String> = HashSet::new();
    walk_function(f, |n| match n {
        N::S(Stmt::Call { call: Expr::Call { name, .. }, line }) => {
            if creator(name).is_some() {
                out.push(Leak {
                    rule: "discarded",
                    creator: name.clone(),
                    line: *line,
                    extra: None,
                    function: String::new(),
                    heat: "",
                });
            }
        }
        N::L(d) => {
            if let Some(Expr::Call { name, .. }) = &d.init {
                if creator(name).is_some() {
                    if !created.contains_key(&d.name) {
                        created_order.push(d.name.clone());
                    }
                    created.insert(d.name.clone(), (name.clone(), d.line));
                }
            }
        }
        N::S(Stmt::Set { target, value, line }) => {
            let tgt = ue(target);
            if let Expr::Call { name, .. } = value {
                if creator(name).is_some() && locals.contains(tgt.as_str()) && !created.contains_key(&tgt) {
                    created_order.push(tgt.clone());
                    created.insert(tgt.clone(), (name.clone(), *line));
                }
            }
            if let Expr::Name { name, .. } = value {
                if locals.contains(name.as_str()) && !locals.contains(tgt.as_str()) {
                    escaped.insert(name.clone());
                }
            }
        }
        N::S(Stmt::Return { value: Some(v) }) => {
            walk_expr(v, |m| {
                if let N::E(Expr::Name { name, .. }) = m {
                    escaped.insert(name.clone());
                }
            });
        }
        N::E(Expr::Call { name, args, line }) => {
            for a in args {
                if let Expr::Call { name: an, line: aline, .. } = a {
                    if let Some((kind, destroyer)) = creator(an) {
                        if matches!(kind, "location" | "group" | "force")
                            && name != destroyer
                            && creator(name).is_none()
                            && !(kind == "group" && want_destroy)
                        {
                            out.push(Leak {
                                rule: "inline",
                                creator: an.clone(),
                                line: if *aline != 0 { *aline } else { *line },
                                extra: Some(("into", name.clone())),
                                function: String::new(),
                                heat: "",
                            });
                        }
                    }
                }
            }
            if is_destroyer(name) || map_funcs.contains(name) || name.starts_with("Save") || name == "ExecuteFunc" {
                for a in args {
                    if let Expr::Name { name: an, .. } = a {
                        if locals.contains(an.as_str()) {
                            escaped.insert(an.clone());
                        }
                    }
                }
            }
        }
        _ => {}
    });
    for name in created_order {
        if !escaped.contains(&name) {
            let (cr, line) = created[&name].clone();
            out.push(Leak {
                rule: "never_destroyed",
                creator: cr,
                line,
                extra: Some(("local", name)),
                function: String::new(),
                heat: "",
            });
        }
    }
    out
}

fn json_str(s: &str, out: &mut String) {
    out.push('"');
    for ch in s.chars() {
        match ch {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            c if (c as u32) < 0x20 => out.push_str(&format!("\\u{:04x}", c as u32)),
            c => out.push(c),
        }
    }
    out.push('"');
}

fn check(text: &[u8]) -> Result<String, i32> {
    let toks = tokenize(text);
    let mut p = P { t: text, toks, i: 0, line: 1, depth: 0 };
    let s = match p.script() {
        Ok(s) => s,
        Err(Fail) => return Err(if p.depth > MAX_DEPTH { 2 } else { 1 }),
    };
    let heat = heat_of(&s);
    let map_funcs: HashSet<String> = heat.keys().cloned().collect();
    let globals_: HashSet<&str> = s.globals.iter().map(|g| g.name.as_str()).collect();
    let mut leaks: Vec<Leak> = vec![];
    for f in &s.functions {
        for mut x in leaks_of(f, &map_funcs) {
            x.function = f.name.clone();
            x.heat = heat[&f.name];
            leaks.push(x);
        }
    }
    leaks.sort_by_key(|x| (HEATS.iter().position(|h| *h == x.heat).unwrap_or(9), x.line));
    let mut called: HashSet<String> = HashSet::new();
    let mut note = |n: N| match n {
        N::E(Expr::Call { name, args, .. }) => {
            called.insert(name.clone());
            if name == "ExecuteFunc" && !args.is_empty() {
                if let Expr::Literal { kind: Lit::Str, text } = &args[0] {
                    called.insert(String::from_utf8_lossy(&unescape(&text[1..text.len() - 1])).into_owned());
                }
            }
        }
        N::E(Expr::FuncRef { name }) => {
            called.insert(name.clone());
        }
        _ => {}
    };
    for g in &s.globals {
        if let Some(e) = &g.init {
            walk_expr(e, &mut note);
        }
    }
    for f in s.natives.iter().chain(s.functions.iter()) {
        walk_function(f, &mut note);
    }
    let mut start: Vec<(&str, &str)> = vec![];
    for (name, code) in [("InitGlobals", "init_globals_not_called"), ("RunInitializationTriggers", "init_triggers_not_called")] {
        if map_funcs.contains(name) && !called.contains(name) {
            start.push((code, name));
        }
    }
    let mut assigned: HashSet<String> = HashSet::new();
    let mut reads: HashMap<String, usize> = HashMap::new();
    for f in &s.functions {
        let mut targets: HashSet<*const Expr> = HashSet::new();
        walk_function(f, |n| {
            if let N::S(Stmt::Set { target, .. }) = n {
                let tgt: &Expr = match target {
                    Expr::Index { base, .. } => base,
                    t => t,
                };
                if let Expr::Name { name, .. } = tgt {
                    assigned.insert(name.clone());
                    targets.insert(tgt as *const Expr);
                }
            }
        });
        walk_function(f, |n| {
            if let N::E(e @ Expr::Name { name, .. }) = n {
                if globals_.contains(name.as_str()) && !targets.contains(&(e as *const Expr)) {
                    *reads.entry(name.clone()).or_insert(0) += 1;
                }
            }
        });
    }
    let mut never: Vec<(String, String, usize)> = vec![];
    for g in &s.globals {
        if !g.is_constant && !g.has_init {
            if let Some(r) = reads.get(&g.name) {
                if !assigned.contains(&g.name) {
                    let typ = if g.is_array { format!("{} array", g.typ) } else { g.typ.clone() };
                    never.push((g.name.clone(), typ, *r));
                }
            }
        }
    }
    never.sort_by(|a, b| b.2.cmp(&a.2).then_with(|| a.0.cmp(&b.0)));
    let mut o = String::with_capacity(4096);
    o.push_str("{\"leaks\": [");
    for (i, x) in leaks.iter().take(200).enumerate() {
        if i > 0 {
            o.push_str(", ");
        }
        o.push_str("{\"rule\": ");
        json_str(x.rule, &mut o);
        o.push_str(", \"creator\": ");
        json_str(&x.creator, &mut o);
        o.push_str(&format!(", \"line\": {}", x.line));
        if let Some((k, v)) = &x.extra {
            o.push_str(", ");
            json_str(k, &mut o);
            o.push_str(": ");
            json_str(v, &mut o);
        }
        o.push_str(", \"function\": ");
        json_str(&x.function, &mut o);
        o.push_str(", \"heat\": ");
        json_str(x.heat, &mut o);
        o.push('}');
    }
    o.push_str("], \"start\": [");
    for (i, (code, name)) in start.iter().enumerate() {
        if i > 0 {
            o.push_str(", ");
        }
        o.push_str("{\"code\": ");
        json_str(code, &mut o);
        o.push_str(", \"name\": ");
        json_str(name, &mut o);
        o.push('}');
    }
    o.push_str("], \"never_assigned\": [");
    for (i, (name, typ, r)) in never.iter().take(40).enumerate() {
        if i > 0 {
            o.push_str(", ");
        }
        o.push_str("{\"name\": ");
        json_str(name, &mut o);
        o.push_str(", \"type\": ");
        json_str(typ, &mut o);
        o.push_str(&format!(", \"reads\": {}}}", r));
    }
    o.push_str("], \"heat\": {");
    for (i, h) in HEATS.iter().enumerate() {
        if i > 0 {
            o.push_str(", ");
        }
        o.push_str(&format!("\"{}\": {}", h, heat.values().filter(|v| *v == h).count()));
    }
    o.push_str("}, \"counts\": {");
    o.push_str(&format!(
        "\"leaks\": {}, \"never_assigned\": {}, \"start\": {}",
        leaks.len(),
        never.len(),
        start.len()
    ));
    for h in HEATS {
        o.push_str(&format!(", \"leaks_{}\": {}", h, leaks.iter().filter(|x| x.heat == h).count()));
    }
    o.push_str("}}");
    Ok(o)
}

#[no_mangle]
pub extern "C" fn jass_checks(text: *const u8, len: usize, out: *mut *mut u8, out_len: *mut usize) -> i32 {
    if text.is_null() || out.is_null() || out_len.is_null() {
        return 3;
    }
    let data: Vec<u8> = unsafe { std::slice::from_raw_parts(text, len) }.to_vec();
    let worker = std::thread::Builder::new().stack_size(512 << 20).spawn(move || {
        panic::catch_unwind(|| {
            let t: &[u8] = if data.starts_with(&[0xEF, 0xBB, 0xBF]) { &data[3..] } else { &data[..] };
            check(t)
        })
    });
    let r = match worker {
        Ok(h) => match h.join() {
            Ok(Ok(r)) => r,
            _ => Err(3),
        },
        Err(_) => Err(3),
    };
    match r {
        Ok(json) => {
            let mut b = json.into_bytes().into_boxed_slice();
            unsafe {
                *out_len = b.len();
                *out = b.as_mut_ptr();
            }
            std::mem::forget(b);
            0
        }
        Err(code) => code,
    }
}

fn crypt_table() -> Vec<u32> {
    let mut t = vec![0u32; 0x500];
    let mut seed: u32 = 0x0010_0001;
    for i in 0..0x100usize {
        let mut idx = i;
        while idx < 0x500 {
            seed = (seed * 125 + 3) % 0x2AAAAB;
            let hi = (seed & 0xFFFF) << 16;
            seed = (seed * 125 + 3) % 0x2AAAAB;
            t[idx] = hi | (seed & 0xFFFF);
            idx += 0x100;
        }
    }
    t
}

#[inline]
fn upper_mpq(c: u8) -> u8 {
    if (0x61..=0x7A).contains(&c) {
        c - 32
    } else if c == 0x2F {
        0x5C
    } else {
        c
    }
}

#[inline]
fn hash_more(crypt: &[u32], st: [u32; 4], bytes: &[u8]) -> [u32; 4] {
    let (mut a1, mut b1, mut a2, mut b2) = (st[0], st[1], st[2], st[3]);
    for &c0 in bytes {
        let c = upper_mpq(c0) as u32;
        a1 = crypt[(0x100 + c) as usize] ^ a1.wrapping_add(b1);
        b1 = c.wrapping_add(a1).wrapping_add(b1).wrapping_add(b1 << 5).wrapping_add(3);
        a2 = crypt[(0x200 + c) as usize] ^ a2.wrapping_add(b2);
        b2 = c.wrapping_add(a2).wrapping_add(b2).wrapping_add(b2 << 5).wrapping_add(3);
    }
    [a1, b1, a2, b2]
}

struct Part {
    ascii: bool,
    var: [Option<Vec<u8>>; 3],
}

fn read_parts(buf: &[u8], pos: &mut usize) -> Option<Vec<Part>> {
    let rd_u32 = |b: &[u8], p: &mut usize| -> Option<u32> {
        let v = u32::from_le_bytes(b.get(*p..*p + 4)?.try_into().ok()?);
        *p += 4;
        Some(v)
    };
    let n = rd_u32(buf, pos)? as usize;
    let mut out = Vec::with_capacity(n);
    for _ in 0..n {
        let flags = *buf.get(*pos)?;
        *pos += 1;
        let mut var: [Option<Vec<u8>>; 3] = [None, None, None];
        let ascii = flags & 0x80 != 0;
        let labels: Vec<usize> = if ascii { vec![0] } else { (0..3).filter(|l| flags & (1 << l) != 0).collect() };
        for l in labels {
            let len = rd_u32(buf, pos)? as usize;
            var[l] = Some(buf.get(*pos..*pos + len)?.to_vec());
            *pos += len;
        }
        out.push(Part { ascii, var });
    }
    Some(out)
}

#[inline]
fn spelling(p: &Part, label: usize) -> Option<&Vec<u8>> {
    if p.ascii {
        p.var[0].as_ref()
    } else {
        p.var[label].as_ref()
    }
}

#[no_mangle]
pub extern "C" fn mpq_name_search(
    buf: *const u8,
    len: usize,
    pairs: *const u64,
    npairs: usize,
    out: *mut *mut u8,
    out_len: *mut usize,
) -> i32 {
    if buf.is_null() || out.is_null() || out_len.is_null() || (pairs.is_null() && npairs > 0) {
        return 1;
    }
    let r = panic::catch_unwind(|| {
        let b = unsafe { std::slice::from_raw_parts(buf, len) };
        let set: std::collections::HashSet<u64> =
            unsafe { std::slice::from_raw_parts(pairs, npairs) }.iter().copied().collect();
        let mut pos = 0usize;
        let folders = read_parts(b, &mut pos)?;
        let names = read_parts(b, &mut pos)?;
        let exts = read_parts(b, &mut pos)?;
        let crypt = crypt_table();
        let start = [0x7FED7FEDu32, 0xEEEEEEEEu32, 0x7FED7FEDu32, 0xEEEEEEEEu32];
        let mut hits: Vec<u32> = Vec::new();
        for (i, f) in folders.iter().enumerate() {
            for label in 0..3usize {
                let fs = match spelling(f, label) {
                    Some(s) => s,
                    None => continue,
                };
                let st_f = hash_more(&crypt, start, fs);
                for (j, n) in names.iter().enumerate() {
                    if f.ascii && n.ascii && label > 0 {
                        continue;
                    }
                    let ns = match spelling(n, label) {
                        Some(s) => s,
                        None => continue,
                    };
                    let st_n = hash_more(&crypt, st_f, ns);
                    for (k, e) in exts.iter().enumerate() {
                        let es = match spelling(e, label) {
                            Some(s) => s,
                            None => continue,
                        };
                        let st = hash_more(&crypt, st_n, es);
                        if set.contains(&(((st[0] as u64) << 32) | st[2] as u64)) {
                            hits.extend_from_slice(&[i as u32, j as u32, k as u32, label as u32]);
                        }
                    }
                }
            }
        }
        Some(hits)
    });
    match r {
        Ok(Some(hits)) => {
            let count = hits.len() / 4;
            let mut bytes: Vec<u8> = Vec::with_capacity(hits.len() * 4);
            for h in hits {
                bytes.extend_from_slice(&h.to_le_bytes());
            }
            let mut boxed = bytes.into_boxed_slice();
            unsafe {
                *out_len = count;
                *out = boxed.as_mut_ptr();
            }
            std::mem::forget(boxed);
            0
        }
        _ => 1,
    }
}

#[no_mangle]
pub extern "C" fn jass_free(p: *mut u8, len: usize) {
    if !p.is_null() {
        unsafe {
            drop(Box::from_raw(std::slice::from_raw_parts_mut(p, len)));
        }
    }
}
