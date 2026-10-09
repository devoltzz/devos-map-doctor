# The simulated game engine the simulator runs a map in: the natives of Warcraft III in Lua.
import io
import os
import re
import sys
import time

from doctor.port import sim_project

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = sim_project.finds()
LUA_ROUTE = next(
    (
        p
        for p in (HERE, os.path.join(HERE, 'simulator'), getattr(sys, '_MEIPASS', HERE))
        if os.path.isfile(os.path.join(p, 'rt_core.lua'))
    ),
    HERE,
)
from doctor.script import jass2lua
from doctor.port import mock_engine
try:
    import injeta_ac_boot
except ImportError:
    injeta_ac_boot = None

REF = os.path.normpath(os.path.join(HERE, '..', 'ref', '3.0'))
if not os.path.isfile(os.path.join(REF, 'common.j')):
    from doctor.script import pjass
    REF = pjass.game_scripts_dir(REF) or REF
COMMON = os.path.join(REF, 'common.j')
BLIZZ = os.path.join(REF, 'blizzard.j')
PREFIX = '// [BISEC] desligado: '
PROF_TETO = 40

TIMER_GLOBALS = '''integer PRB_q40=0
integer PRB_q40_n=0
integer PRB_q70=0
integer PRB_q70_n=0
integer PRB_nloop=0
integer PRB_qloop1=0
integer PRB_qloop_ult=0
'''
TIMER_DRIVER = '''function PRB_cb40 takes nothing returns nothing
    set PRB_q40=AC_tmr_quadro
    set PRB_q40_n=PRB_q40_n+1
endfunction
function PRB_cb70 takes nothing returns nothing
    set PRB_q70=AC_tmr_quadro
    set PRB_q70_n=PRB_q70_n+1
endfunction
function PRB_cbloop takes nothing returns nothing
    set PRB_nloop=PRB_nloop+1
    if PRB_nloop==1 then
        set PRB_qloop1=AC_tmr_quadro
    endif
    set PRB_qloop_ult=AC_tmr_quadro
endfunction
function PRB_timer takes nothing returns nothing
    call AC_cb_liga(40,0,function PRB_cb40)
    call AC_cb_liga(41,0,function PRB_cbloop)
    call AC_cb_liga(42,0,function PRB_cb70)
    call AC_tmr_wait(40000,40,0)
    call AC_tmr_loop(30,41,0)
    call AC_tmr_wait(70000,42,0)
    set AC_tmr_motor=CreateTimer()
    call TimerStart(AC_tmr_motor,0.01,true,function AC_tmr_passo)
endfunction
'''

GROUPS = {
    'a': ('call AC_attr_init()', 'AC_CB_ATTR_ASAA', 'AC_CB_ATTR_PTY'),
    'b': ('AC_tmr_loop(30,AC_CB_ON_UPDATE', 'AC_tmr_loop(5000,AC_CB_UNI_COLETA',
          'set AC_tmr_motor=CreateTimer()', 'TimerStart(AC_tmr_motor'),
    'c': ('call AC_uid_init()', 'AC_uni_registra_triggers()', 'call AC_uni_init()'),
    'd': ('AC_CB_BUFF_REMOVE',),
}

LIGACOES = [
    ('call AC_cb_liga(AC_CB_CONTAGEM,1,function ACs_cbx1_1)',
     'call AC_cb_liga(AC_CB_CONTAGEM,1,function ACs_cb_reservado)'),
    ('call AC_cb_liga(AC_CB_COLETA_UNIDADE,1,function ACs_cbx1_2)',
     'call AC_cb_liga(AC_CB_COLETA_UNIDADE,1,function ACs_tmr_coleta)'),
    ('call AC_cb_liga(AC_CB_ON_UPDATE,0,function ACs_cbx0_1)',
     'call AC_cb_liga(AC_CB_ON_UPDATE,0,function ACs_jogo_on_update)'),
    ('call AC_cb_liga(AC_CB_UNI_ENTRA,0,function ACs_cbx0_2)',
     'call AC_cb_liga(AC_CB_UNI_ENTRA,0,function ACs_cb_reservado)'),
    ('call AC_cb_liga(AC_CB_UNI_SAI,0,function ACs_cbx0_3)',
     'call AC_cb_liga(AC_CB_UNI_SAI,0,function ACs_cb_reservado)'),
    ('call AC_cb_liga(AC_CB_UNI_COLETA,0,function ACs_cbx0_4)',
     'call AC_cb_liga(AC_CB_UNI_COLETA,0,function ACs_uni_cb_coleta)'),
]

BODIES = ['AC_boot', 'AC_tmr_passo', 'ACs_jogo_on_update', 'ACs_uni_cb_coleta', 'ACs_uni_coleta',
          'ACs_tmr_coleta', 'ACs_uni_entra', 'ACs_uni_sai', 'ACs_uni_trg_morte', 'ACs_uni_trg_dono',
          'AC_attr_init', 'ACs_cbx0_1', 'ACs_cbx0_4', 'ACs_cbx1_2', 'ACs_cb_0', 'ACs_cb_1',
          'ACs_cb_reservado', 'ACs_buff_remove_zero']


def read_data(p):
    return io.open(p, 'rb').read().decode('utf-8', 'surrogateescape')


def secao(txt, begin, end_pos):
    a = txt.index(begin) + len(begin)
    b = txt.index(end_pos, a)
    return txt[a:b]


def relink(txt, clusters):
    key_names = [k for g in clusters for k in GROUPS[g]]
    out = []
    n = 0
    for line in txt.split('\n'):
        if PREFIX in line and any(k in line for k in key_names):
            line = line.replace(PREFIX, '', 1)
            n += 1
        out.append(line)
    return '\n'.join(out), n


def fixable(txt):
    old_ones = [txt.count(v) for v, _ in LIGACOES]
    added = [txt.count(n) for _, n in LIGACOES]
    if not any(old_ones) and all(c == 1 for c in added):
        return txt, 'ja no disco'
    n = 0
    for old, new in LIGACOES:
        c = txt.count(old)
        if c != 1:
            raise SystemExit('conserto: %d ocorrencias de %r (esperado 1)' % (c, old))
        txt = txt.replace(old, new)
        n += 1
    return txt, n


def build_jass(layer, variante):
    glob = secao(layer, '//@CAMADA_GLOBALS', '//@FIM_CAMADA_GLOBALS')
    func = secao(layer, '//@CAMADA_FUNCTIONS', '//@FIM_CAMADA_FUNCTIONS')
    info = {}
    if variante == 'timer':
        info['bisec_restantes'] = func.count(PREFIX)
        return 'globals\n' + TIMER_GLOBALS + glob + '\nendglobals\n' + func + '\n' + TIMER_DRIVER, info
    if variante in GROUPS:
        func, info['religadas'] = relink(func, [variante])
    elif variante in ('religado', 'repair'):
        func, info['religadas'] = relink(func, list(GROUPS))
        if variante == 'repair':
            func, info['ligacoes_trocadas'] = fixable(func)
    elif variante != 'current':
        raise SystemExit('variante desconhecida: %s' % variante)
    info['bisec_restantes'] = func.count(PREFIX)
    reserved = ''
    if not re.search(r'(?m)^function\s+ACs_cb_reservado\s+takes', func):
        reserved = 'function ACs_cb_reservado takes nothing returns nothing\nendfunction\n'
    if injeta_ac_boot is None:
        raise SystemExit('a prova de despacho do framework `ac` precisa do `port/tools/injeta_ac_boot.py` do projeto '
                         '(o Dream KK); projeto: %s' % PROJ)
    step_on = getattr(injeta_ac_boot, 'LIGA_YDHT', '')
    driver = (reserved +
              'function PRB_boot takes nothing returns nothing\n'
              '    local hashtable YDHT=InitHashtable()\n'
              + step_on + '\n'
              + injeta_ac_boot.CHAMADA + '\n'
              'endfunction\n')
    return 'globals\n' + glob + '\nendglobals\n' + func + '\n' + driver, info


def gen_stubs(common_src):
    p = jass2lua.Parser(jass2lua.lex(common_src)).parse()
    line_list = []
    for fname, f in p.natives.items():
        ret = f.ret
        if fname.startswith('Convert') and ret not in mock_engine.PRIM:
            line_list.append('%s = function(i) return __conv(%s, i) end' % (fname, jass2lua.lua_string(ret)))
            continue
        body = {'nothing': 'end', 'integer': 'return 0 end', 'real': 'return 0.0 end',
                'boolean': 'return false end', 'string': 'return "" end'}.get(
            ret, 'return __newh(%s) end' % jass2lua.lua_string(ret))
        line_list.append('if %s == nil then %s = function(...) %s end' % (fname, fname, body))
    return '\n'.join(line_list)


INSTRUMENT = r'''
__prb = { prof = 0, prof_max = 0, recursoes = 0, cadeia = nil, erros = {}, nerros = 0,
          conta = {}, fora = {}, fora_modo = __PRB_FORA }
local P = __prb
-- 1) arrays JASS com o teto do motor: todo acesso passa pelo proxy (tabela vazia + deposito)
local LIM = 32768
local function marca(nome, k, rw)
  local e = P.fora[nome]
  if not e then e = { w = 0, r = 0, primeiro = k, maior = k } P.fora[nome] = e end
  e[rw] = e[rw] + 1
  if k > e.maior then e.maior = k end
end
function __prb_arr(nome, tipo)
  -- [28/09/2026, o dragonball] o padrao do tipo por `if`: o `(tipo == "b" and false) or nil` do Lua da' nil (o `and`
  -- com `false` cai no `or`), e o array booleano nao atribuido devolvia nil. No motor ele vale false: o
  -- `if ( bIsData[index] == false )` do mapa (a carga do save JN) dava falso no simulador e a carga nao rodava.
  local padrao = nil
  if tipo == "i" then padrao = 0 elseif tipo == "r" then padrao = 0.0 elseif tipo == "b" then padrao = false end
  local dep = {}
  return setmetatable({}, {
    __index = function(_, k)
      if math.type(k) == "integer" and (k < 0 or k >= LIM) then
        marca(nome, k, "r")
        if P.fora_modo == "ignora" then return padrao end
      end
      local v = dep[k]
      if v == nil then return padrao end
      return v
    end,
    __newindex = function(_, k, v)
      if math.type(k) == "integer" and (k < 0 or k >= LIM) then
        marca(nome, k, "w")
        if P.fora_modo == "ignora" then return end
      end
      dep[k] = v
    end })
end
-- 2) erros do motor simulado
local logerr = __logerr
function __logerr(msg, fn)
  P.nerros = P.nerros + 1
  local s = tostring(msg)
  if #P.erros < 12 then
    local novo = true
    for _, e in ipairs(P.erros) do if e == s:sub(1, 300) then novo = false break end end
    if novo then P.erros[#P.erros + 1] = s:sub(1, 300) end
  end
  return logerr(msg, fn)
end
'''

INSTRUMENT_POS = r'''
local P = __prb
-- 3) nome de cada funcao global (para a cadeia da recursao)
local nome_de = {}
for k, v in pairs(_G) do if type(v) == "function" then nome_de[v] = k end end
-- 4) contadores nos corpos
for _, n in ipairs(__PRB_CORPOS) do
  local f = rawget(_G, n)
  if type(f) == "function" then
    P.conta[n] = 0
    local g = function(...) P.conta[n] = P.conta[n] + 1 return f(...) end
    rawset(_G, n, g)
    nome_de[g] = n
  end
end
-- 5) o aninhamento de TriggerEvaluate
local te = TriggerEvaluate
local function id_do_trigger(t)
  local cbt = rawget(_G, "AC_cbt")
  if cbt == nil then return "?" end
  for i = 0, 64 do if cbt[i] == t then return tostring(i) end end
  return "fora do AC_cbt"
end
function TriggerEvaluate(t)
  P.prof = P.prof + 1
  if P.prof > P.prof_max then P.prof_max = P.prof end
  if P.prof > __PRB_TETO then
    P.recursoes = P.recursoes + 1
    if P.cadeia == nil then
      local c = {}
      for nivel = 2, 40 do
        local d = debug.getinfo(nivel, "f")
        if d == nil then break end
        local n = nome_de[d.func]
        if n and n ~= "TriggerEvaluate" and n ~= "pcall" and (#c == 0 or c[#c] ~= n) then c[#c + 1] = n end
        if #c >= 8 then break end
      end
      P.cadeia = "id " .. id_do_trigger(t) .. ": " .. table.concat(c, " <- ")
    end
    P.prof = P.prof - 1
    error("RECURSAO: TriggerEvaluate aninhado > " .. __PRB_TETO, 0)
  end
  local ok, r = pcall(te, t)
  P.prof = P.prof - 1
  if not ok then error(r, 0) end
  return r
end
'''


MOTOR_FIEL = r'''
local M32 = 0xFFFFFFFF
local function mix(a, b, c)
  a = (a - b) & M32 a = (a - c) & M32 a = a ~ (c >> 13)
  b = (b - c) & M32 b = (b - a) & M32 b = b ~ ((a << 8) & M32)
  c = (c - a) & M32 c = (c - b) & M32 c = c ~ (b >> 13)
  a = (a - b) & M32 a = (a - c) & M32 a = a ~ (c >> 12)
  b = (b - c) & M32 b = (b - a) & M32 b = b ~ ((a << 16) & M32)
  c = (c - a) & M32 c = (c - b) & M32 c = c ~ (b >> 5)
  a = (a - b) & M32 a = (a - c) & M32 a = a ~ (c >> 3)
  b = (b - c) & M32 b = (b - a) & M32 b = b ~ ((a << 10) & M32)
  c = (c - a) & M32 c = (c - b) & M32 c = c ~ (b >> 15)
  return a, b, c
end
local DESLOC = { 0, 8, 16, 24, 0, 8, 16, 24, 8, 16, 24 }
-- O StringHash do REFORGED, pelo MODELO HIBRIDO (26/09/2026; `common/scripts/sstrhash.py`,
-- `stringhash_hibrido_bytes`, a mesma decodificacao): o lookup2 sobre a sequencia em que o byte ASCII entra
-- como esta' (1 byte; a-z -> A-Z e / -> \ como no 1.28) e o caractere nao-ASCII como a unidade UTF-16LE. Cabe
-- em todo ponto medido em jogo: "掉落总数" = -1970465554 (22/09/2026, o rt_natives.lua da 1.0L) e os nomes
-- `u<hash>`/`chr_<hash>` dos saves gravados em jogo pelos ports da M16 -- "JN_DATA_1" = 1234034213 (DLR), "1"
-- = 1132341824 (Heaven), "test" = -310027398 (Innocent), "devoltz#11953" = 461077761 (a pasta da conta nos
-- tres). Texto so' ASCII da' o 1.28; texto sem ASCII, o UTF-16. As duas medidas com minuscula mostram a dobra
-- de caixa do 1.28. NAO medido: o texto MISTO (ASCII + nao-ASCII) e o `/`.
-- Historia: a R49 tinha posto o 1.28 aqui; o 1.o teste da R1 (22/09/2026) trocou pelo UTF-16 do texto
-- INTEIRO (a constante que o compilador chines pre-calcula para chave CJK nao bate com a nativa: a tabela de
-- drop saia vazia no jogo e cheia na sonda). Esse modelo errava o texto com ASCII; fica para comparar as provas
-- (`__SH_MODELO = "utf16"`, `KK_SH_MODELO=utf16`), e `"bloco"` e' o outro modelo que cabe nas medidas (o texto
-- INTEIRO em UTF-16 quando tem um caractere nao-ASCII; so' difere no texto misto). Byte UTF-8 invalido vira
-- U+FFFD (o hash do byte solto nao-ASCII nao e' confiavel). `__SH_DOBRA = false` (`KK_SH_DOBRA=0`) desliga a
-- dobra de caixa: so' para comparar, a medida a desmente.
-- a sequencia de bytes que o lookup2 le, pelo modelo (`__SH_MODELO`: "hibrido", "utf16" ou "bloco")
local function __sh_seq(s)
  local modelo = __SH_MODELO or "hibrido"
  local dobra = __SH_DOBRA ~= false
  local ascii_byte = modelo == "hibrido"
  if modelo == "bloco" then
    ascii_byte = not s:find("[\128-\255]")
  end
  local out, i, n = {}, 1, #s
  while i <= n do
    local c = s:byte(i)
    if c < 0x80 and ascii_byte then
      if dobra then
        if c >= 0x61 and c <= 0x7A then c = c - 0x20 elseif c == 0x2F then c = 0x5C end
      end
      out[#out + 1] = c
      i = i + 1
    else
      local cp, len = nil, 1
      if c < 0x80 then cp = c
      elseif c >= 0xC2 and c <= 0xDF and i + 1 <= n then
        local c2 = s:byte(i + 1)
        if c2 >= 0x80 and c2 <= 0xBF then cp = ((c & 0x1F) << 6) | (c2 & 0x3F) len = 2 end
      elseif c >= 0xE0 and c <= 0xEF and i + 2 <= n then
        local c2, c3 = s:byte(i + 1, i + 2)
        if c2 >= 0x80 and c2 <= 0xBF and c3 >= 0x80 and c3 <= 0xBF then
          cp = ((c & 0x0F) << 12) | ((c2 & 0x3F) << 6) | (c3 & 0x3F) len = 3
        end
      elseif c >= 0xF0 and c <= 0xF4 and i + 3 <= n then
        local c2, c3, c4 = s:byte(i + 1, i + 3)
        if c2 >= 0x80 and c2 <= 0xBF and c3 >= 0x80 and c3 <= 0xBF and c4 >= 0x80 and c4 <= 0xBF then
          cp = ((c & 0x07) << 18) | ((c2 & 0x3F) << 12) | ((c3 & 0x3F) << 6) | (c4 & 0x3F) len = 4
        end
      end
      if cp == nil then cp = 0xFFFD len = 1 end
      -- a dobra na UNIDADE: so' nos modelos que levam o ASCII como unidade UTF-16 (o de 22/09/2026 dobrava todo
      -- codigo); no hibrido o ASCII ja' foi dobrado no byte e o nao-ASCII nao dobra
      if dobra and not ascii_byte then
        if cp >= 0x61 and cp <= 0x7A then cp = cp - 0x20 elseif cp == 0x2F then cp = 0x5C end
      end
      if cp >= 0x10000 then
        local v = cp - 0x10000
        local hi, lo = 0xD800 + (v >> 10), 0xDC00 + (v & 0x3FF)
        out[#out + 1] = hi & 0xFF out[#out + 1] = hi >> 8 out[#out + 1] = lo & 0xFF out[#out + 1] = lo >> 8
      else
        out[#out + 1] = cp & 0xFF out[#out + 1] = cp >> 8
      end
      i = i + len
    end
  end
  return out
end
local __sh_memo, __sh_memo_n = {}, 0
function StringHash(s)
  s = s or ""
  local v = __sh_memo[s]
  if v ~= nil then return v end
  local k = __sh_seq(s)
  local n = #k
  local a, b, c = 0x9E3779B9, 0x9E3779B9, 0
  local i = 1
  while n - (i - 1) >= 12 do
    a = (a + (k[i] | (k[i + 1] << 8) | (k[i + 2] << 16) | (k[i + 3] << 24))) & M32
    b = (b + (k[i + 4] | (k[i + 5] << 8) | (k[i + 6] << 16) | (k[i + 7] << 24))) & M32
    c = (c + (k[i + 8] | (k[i + 9] << 8) | (k[i + 10] << 16) | (k[i + 11] << 24))) & M32
    a, b, c = mix(a, b, c)
    i = i + 12
  end
  c = (c + n) & M32
  local j = 0
  while i <= n do
    j = j + 1
    local sh = DESLOC[j]
    if j <= 4 then a = (a + (k[i] << sh)) & M32
    elseif j <= 8 then b = (b + (k[i] << sh)) & M32
    else c = (c + (k[i] << sh)) & M32 end
    i = i + 1
  end
  a, b, c = mix(a, b, c)
  if c >= 0x80000000 then c = c - 0x100000000 end
  if __sh_memo_n > 200000 then __sh_memo, __sh_memo_n = {}, 0 end
  __sh_memo[s] = c
  __sh_memo_n = __sh_memo_n + 1
  return c
end
-- [KK 1.0 R1] as nativas de bit do Reforged (`common.j` 3.0: BlzBitOr/And/Xor), que o `DB_SH` usa: o
-- `gen_stubs` as deixava devolvendo 0 e o hash saia 0 para todo texto.
local function __s32(v) v = v & 0xFFFFFFFF if v >= 0x80000000 then return v - 0x100000000 end return v end
function BlzBitOr(a, b) return __s32((a or 0) | (b or 0)) end
function BlzBitAnd(a, b) return __s32((a or 0) & (b or 0)) end
function BlzBitXor(a, b) return __s32((a or 0) ~ (b or 0)) end
function UnitId2String(i) return nil end
function UnitId(s) return 0 end
-- `IsUnitOwnedByPlayer` so' existia no `VIPSKIN_PRELUDE` (cenario da rota Lua): aqui caia no stub que
-- devolve false, e a escolha de heroi na taverna (`Trig_ChooseHero`, cru 37731) nunca passava.
function IsUnitOwnedByPlayer(u, p) return u ~= nil and p ~= nil and u.owner == p end
-- `GroupEnumUnitsInRangeOfLoc` era VAZIA no `mock_test.py`: a skill que escolhe o alvo "unidades num
-- raio do ponto" (o YDWE gera isso) nao achava ninguem na sonda, e o dano saia 0 so' aqui.
function GroupEnumUnitsInRangeOfLoc(g, l, r, f)
  if l == nil then return end
  return GroupEnumUnitsInRange(g, l.x or 0.0, l.y or 0.0, r, f)
end
-- tambem stubs (0.0/false) no `mock_test.py`: o efeito preso numa unidade le a posicao por aqui
function GetWidgetX(w) return w and w.x or 0.0 end
function GetWidgetY(w) return w and w.y or 0.0 end
function IsUnitInRange(u, o, d)
  if u == nil or o == nil then return false end
  return ((u.x or 0) - (o.x or 0)) ^ 2 + ((u.y or 0) - (o.y or 0)) ^ 2 <= d * d
end
-- R49: `GetUnitState` do `mock_test.py` devolvia a MANA MAXIMA para todo estado que nao fosse
-- vida/mana -- inclusive os `ConvertUnitState(0x12/0x15/0x20...)` do japi. O motor devolve 0: o
-- dano de skill escalado por "ataque" saia, na sonda, escalado pela mana maxima.
local __gus_mock = GetUnitState
function GetUnitState(u, s)
  if s == UNIT_STATE_LIFE or s == UNIT_STATE_MAX_LIFE or s == UNIT_STATE_MANA or s == UNIT_STATE_MAX_MANA then
    return __gus_mock(u, s)
  end
  return 0.0
end
-- R49: arma pela ficha do objeto (unitweapons.slk: dmgplus1, dice1, sides1). Eram stubs que
-- devolviam 0 -- a `part_14_states.j` le o ataque por elas.
local function __slk_num(u, campo, padrao)
  local sid = string.pack(">I4", (u.typeid or 0) & 0xFFFFFFFF)
  local rec = __slk_raw and __slk_raw.unit and __slk_raw.unit[sid]
  local v = rec and tonumber(rec[campo])
  if v == nil then return padrao end
  return v
end
function BlzGetUnitBaseDamage(u, w)
  if not u then return 0 end
  if u.basedmg == nil then u.basedmg = math.floor(__slk_num(u, "dmgplus1", 0)) end
  return u.basedmg
end
function BlzSetUnitBaseDamage(u, v, w) if u then u.basedmg = math.floor(v) end end
function BlzGetUnitDiceNumber(u, w)
  if not u then return 0 end
  if u.dice == nil then u.dice = math.floor(__slk_num(u, "dice1", 1)) end
  return u.dice
end
function BlzSetUnitDiceNumber(u, v, w) if u then u.dice = math.floor(v) end end
function BlzGetUnitDiceSides(u, w)
  if not u then return 0 end
  if u.sides == nil then u.sides = math.floor(__slk_num(u, "sides1", 1)) end
  return u.sides
end
function BlzSetUnitDiceSides(u, v, w) if u then u.sides = math.floor(v) end end
-- o alcance como o jassdoc descreve: o getter devolve 0; o setter no indice 1 SOMA ao alcance
function BlzGetUnitWeaponRealField(u, f, i) return 0.0 end
function BlzSetUnitWeaponRealField(u, f, i, v)
  if u == nil then return false end
  if i == 1 then u.range_add = (u.range_add or 0.0) + v return true end
  return false
end
-- [KK 1.0 F1] o time dos slots NEUTROS (12..15) como o motor devolve: 0. Medido em jogo pelo port Lua
-- (log `DEATH ... owner=12 team=0`), e o motor ignora `SetPlayerTeam` nesses slots. O `mock_test.py`
-- cria os jogadores 10..15 com time 1, que e' o efeito do gancho `fix_neutral_teams` da rota Lua
-- (rt_natives.lua) -- e a rota JASS NAO tem esse gancho. Com o 1 o simulador escondia o bug de XP: o
-- gatilho de morte do mapa exige `GetPlayerTeam(dono) != 0` e, no jogo, recusava toda morte de monstro.
local __gpt_mock = GetPlayerTeam
function GetPlayerTeam(p)
  if p ~= nil and p.id ~= nil and p.id >= 12 then return 0 end
  return __gpt_mock(p)
end
-- [28/09/2026, o dragonball] o LIMITE do `BlzSendSyncData` do motor: o dado acima de 255 bytes chega CORTADO (jassdoc:
-- prefixo e dado "Limited to something like 255 bytes"; `common/docs/reforged-limits.md`). O `mock_test.py` entregava o
-- texto inteiro e so' contava o erro: a carga do save do dragonball (o `DATA1_<n>` em Base64, 304 bytes num personagem
-- leve, pelo `DzSyncData`) passava aqui e falhava no jogo -- o "Recent Load" abria (o dado chegou com mais de 5
-- caracteres), a carga leu lixo e o heroi nao nasceu. O pacote sai com os primeiros 255 bytes, e o erro continua contado.
-- (Recusar o pacote inteiro tambem quebraria, de outro jeito: sem o dialogo; o sintoma do jogo e' o do corte.)
local __envia_sync_mock = BlzSendSyncData
function BlzSendSyncData(prefix, data)
  data = data or ""
  if #data > 255 then
    __logerr("BlzSendSyncData: dados com " .. #data .. " bytes (" .. tostring(prefix) .. "): o motor corta em 255")
    data = data:sub(1, 255)
  end
  return __envia_sync_mock(prefix, data)
end
-- [28/09/2026, o dragonball] `UnitDropItemSlot` MOVE o item para a casa `slot` (0..5) do inventario da propria unidade
-- (jassdoc: "Moves an item inside unit's inventory to specified slot. If this slot contains an item, their positions are
-- swapped"; true mesmo se ja' esta' la'; false com unidade/item invalido, item fora do inventario ou casa invalida). O
-- `mock_test.py` TIRAVA o item do inventario: a carga do dragonball (`UnitAddItemByIdSwapped` + `UnitDropItemSlotBJ` em
-- cada casa do bau, das bolsas e do livro de skills) esvaziava os conteineres so' no simulador.
function UnitDropItemSlot(u, it, slot)
  if u == nil or it == nil or u.inv == nil or it.dono ~= u or it.typeid == 0 then return false end
  local tam = UnitInventorySize(u)
  if slot == nil or slot < 0 or slot >= tam then return false end
  local de = nil
  for s = 0, tam - 1 do if u.inv[s] == it then de = s break end end
  if de == nil then return false end
  if de ~= slot then
    local outro = u.inv[slot]
    u.inv[slot] = it
    if outro ~= nil and outro.dono == u and outro.typeid ~= 0 then u.inv[de] = outro else u.inv[de] = nil end
  end
  return true
end
'''
STRINGHASH_VECTORS = [('掉落总数', -1970465554), ('JN_DATA_1', 1234034213), ('1', 1132341824),
                      ('devoltz#11953', 461077761), ('test', -310027398)]
STRINGHASH_MODELS = ('hibrido', 'utf16', 'block_entry')


def load_engine(L, common_src, blizz_src, outside):
    lua = L.LuaRuntime()
    g = lua.globals()
    load_data = lua.eval('function(s, nome) local f, e = load(s, nome, "t") if not f then error(e) end f() end')
    load_data(io.open(os.path.join(LUA_ROUTE, 'rt_core.lua'), 'rb').read(), '=rt_core')
    g.__MOCK_LOCAL = 0
    g.__MOCK_REAL64 = False
    lua.execute(mock_engine.MOCK_PRELUDE.encode('utf-8'))
    slk_data = os.path.join(PROJ, 'port', 'out', 'slk_data.lua') if PROJ else ''
    if slk_data and os.path.isfile(slk_data):
        load_data(open(slk_data, 'rb').read(), '=slk_data')
        lua.execute(b'if __slk_get == nil then function __slk_get(t, sid, c) '
                    b'local tab = __slk_raw and __slk_raw[t] local r = tab and tab[sid] '
                    b'return r and r[c] end end')
    lua.execute(gen_stubs(common_src).encode('utf-8', 'surrogateescape'))
    model = os.environ.get('KK_SH_MODELO', 'hibrido')
    if model not in STRINGHASH_MODELS:
        raise SystemExit('KK_SH_MODELO=%s: use um de %s' % (model, ', '.join(STRINGHASH_MODELS)))
    g.__SH_MODELO = model
    g.__SH_DOBRA = os.environ.get('KK_SH_DOBRA', '1') != '0'
    lua.execute(MOTOR_FIEL.encode('utf-8'))
    sh = lua.globals().StringHash
    vectors = [(t, e) for t, e in STRINGHASH_VECTORS
               if (model != 'utf16' or not any(ord(ch) < 0x80 for ch in t))
               and (g.__SH_DOBRA or t.upper() == t)]
    wrong = [(t, e, sh(t)) for t, e in vectors if sh(t) != e]
    if wrong:
        raise SystemExit('StringHash do motor simulado NAO bate com o motor: %r' % wrong)
    tr = jass2lua.Transpiler(common_src, '', '', overrides={})
    tr.load_reference(common_src)
    pc = jass2lua.Parser(jass2lua.lex(common_src)).parse()
    tr.scope = {}
    tr.prog = pc
    lua.execute(tr.emit_globals(pc.globals).encode('utf-8', 'surrogateescape'))
    rb = jass2lua.Transpiler(common_src, '', blizz_src, overrides={}).run()
    load_data((rb['lua_functions'] + '\n' + rb['lua_globals']).encode('utf-8', 'surrogateescape'), '=blizzard')
    g.__PRB_FORA = outside
    lua.execute(INSTRUMENT.encode('utf-8'))
    return lua


RX_ARR = re.compile(r'^(\w+) = (?:__arr_([irb])\(\)|(\{\}))$', re.M)


def name_arrays(lua_globals):
    def swap(m):
        kind = m.group(2) or 'h'
        return '%s = __prb_arr("%s", "%s")' % (m.group(1), m.group(1), kind)
    return RX_ARR.sub(swap, lua_globals)


SCENE = r'''
return function(fase)
  local M = __mock
  if fase == "antes" then
    __prb_u = {}
    for i = 1, 3 do __prb_u[#__prb_u + 1] = CreateUnit(Player(0), 1751543663, 100.0 * i, 0.0, 0.0) end
    __prb_u[#__prb_u + 1] = CreateUnit(Player(12), 1852730990, -300.0, 0.0, 0.0)
  elseif fase == "cria" then
    __prb_u[#__prb_u + 1] = CreateUnit(Player(0), 1751543663, 500.0, 500.0, 0.0)
    __prb_u[#__prb_u + 1] = CreateUnit(Player(1), 1751543663, 600.0, 500.0, 0.0)
  elseif fase == "morre" then
    __mock_kill(__prb_u[1], __prb_u[2])
  elseif fase == "remove" then
    RemoveUnit(__prb_u[3])
  end
end
'''


def run_action(variante, args, common_src, blizz_src, layer):
    import lupa.lua53 as L
    t0 = time.time()
    src, info = build_jass(layer, variante)
    tr = jass2lua.Transpiler(common_src, blizz_src, src, overrides={})
    res = tr.run()
    lua = load_engine(L, common_src, blizz_src, 'ignora' if variante == 'timer' else args['outside'])
    g = lua.globals()
    lua.execute(res['lua_functions'].encode('utf-8', 'surrogateescape'))
    lua.execute(name_arrays(res['lua_globals']).encode('utf-8', 'surrogateescape'))
    g.__PRB_CORPOS = lua.table_from(BODIES)
    g.__PRB_TETO = PROF_TETO
    lua.execute(INSTRUMENT_POS.encode('utf-8'))
    cena = lua.execute(SCENE.encode('utf-8'))
    called = lua.eval(
        'function(n) local ok, e = __wd_call(_G[n]) if not ok then __logerr(n .. ": " .. tostring(e)) end end'
    )
    avanca = lua.eval('function(s, p) __mock_advance(s, p) end')
    step_size = 0.01
    if variante == 'timer':
        seconds = args['seconds'] if args.get('segundos_dado') else 80.0
        called('PRB_timer')
        avanca(seconds, step_size)
        P = g.__prb
        return {
            'variante': variante, 'info': info, 'avisos_transpilador': len(res['warnings']),
            'q40': g.PRB_q40, 'q40_n': g.PRB_q40_n, 'q70': g.PRB_q70, 'q70_n': g.PRB_q70_n,
            'nloop': g.PRB_nloop, 'qloop1': g.PRB_qloop1, 'qloop_ult': g.PRB_qloop_ult,
            'quadro': g.AC_tmr_quadro, 'seconds': seconds, 'nerros': P.nerros,
            'error_list': [P.error_list[i] for i in range(1, len(P.error_list) + 1)],
            'outside': dict((txt(k), (P.outside[k].w, P.outside[k].r, P.outside[k].first, P.outside[k].larger))
                            for k in P.outside.keys()),
            'prof_max': P.prof_max, 'recursoes': P.recursoes, 'dt': time.time() - t0,
        }
    cena('before')
    called('PRB_boot')
    milestones = [(2.0, 'cria'), (3.0, 'morre'), (4.0, 'remove')]
    done = 0.0
    for tgt, fase in milestones + [(args['seconds'], None)]:
        if tgt > done:
            avanca(tgt - done, step_size)
            done = tgt
        if fase:
            cena(fase)
    P = g.__prb
    M = g.__mock
    marks = [M.chat[i] for i in range(1, len(M.chat) + 1)]
    pluralize = {k: P.pluralize[k] for k in P.pluralize.keys()}
    outside = {}
    for k in P.outside.keys():
        e = P.outside[k]
        outside[k] = (e.w, e.r, e.first, e.larger)
    error_list = [P.error_list[i] for i in range(1, len(P.error_list) + 1)]
    quadro = g.AC_tmr_quadro
    return {
        'variante': variante, 'info': info, 'avisos_transpilador': len(res['warnings']),
        'marks': marks, 'nerros': P.nerros, 'error_list': error_list, 'prof_max': P.prof_max,
        'recursoes': P.recursoes, 'chain': P.chain, 'pluralize': pluralize, 'outside': outside,
        'quadro': quadro, 'seconds': args['seconds'], 'dt': time.time() - t0,
    }


def txt(v):
    if isinstance(v, bytes):
        return v.decode('utf-8', 'replace')
    return str(v)


def report_data(r):
    print('=' * 100)
    print('VARIANTE %-10s  (%s)  transpilador: %d avisos  -- %.1fs'
          % (r['variante'], ', '.join('%s=%s' % kv for kv in sorted(r['info'].items())),
             r['avisos_transpilador'], r['dt']))
    last_pos = [txt(m) for m in r['marks'] if txt(m).startswith('BOOT ')]
    print('  marcas de boot: %d  (ultima do AC_boot: %s)'
          % (len(last_pos), ([m for m in last_pos if m.startswith('BOOT b')] or ['-'])[-1]))
    for m in last_pos:
        if not re.match(r'BOOT (b\d|a2?|p|q):', m):
            print('     %s' % m)
    print('  TriggerEvaluate: profundidade maxima %d; recursoes (> %d): %d'
          % (r['prof_max'], PROF_TETO, r['recursoes']))
    if r['chain']:
        print('  1.a RECURSAO: %s' % txt(r['chain']))
    print('  corpos (execucoes em %.0f s simulados; AC_tmr_quadro final = %s):' % (r['seconds'], r['quadro']))
    for k in BODIES:
        if k in r['pluralize'] and r['pluralize'][k]:
            print('     %-22s %d' % (k, r['pluralize'][k]))
    print('  erros no motor simulado: %d' % r['nerros'])
    for e in r['error_list'][:6]:
        print('     - %s' % txt(e).replace('\n', ' | ')[:220])
    if r['outside']:
        print('  indices fora de [0, 32768) (escritas, leituras, 1.o indice, maior):')
        for k, (w, rd, p, m) in sorted(r['outside'].items(), key=lambda kv: -(kv[1][0] + kv[1][1])):
            print('     %-26s w=%-7d r=%-7d primeiro=%-10s maior=%s' % (txt(k), w, rd, p, m))

