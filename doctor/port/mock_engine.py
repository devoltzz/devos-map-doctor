# The natives of the simulated game engine: units, timers, triggers, frames and files in Lua.
import os

from doctor.port import sim_project

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = sim_project.finds() or HERE
COMMON = os.path.join(HERE, 'ref', 'mock', 'common.j')
BLIZZ = os.path.join(HERE, 'ref', 'mock', 'Blizzard.j')

PRIM = {'integer', 'real', 'string', 'boolean', 'code', 'nothing'}

MOCK_PRELUDE = r'''
-- ===== motor simulado =====
__mock = { files = {}, tooltips = {}, timers = {}, triggers = {}, units = {}, now = 0.0, nextid = 1048576, chat = {},
           texttags = {} }  -- [F5:paladinr] texttags = textos flutuantes vivos
local M = __mock
__ds_trace = nil
-- [F5:priest] "next presence tag" do motor, simulado. O log de dessincronizacao do 3.0.0 (ipse #1)
-- compara a cada turno o topo de uma pilha de numeros livres: objeto que nasce tira o numero do topo
-- (ou um novo), objeto destruido devolve o seu. Liberar os mesmos objetos em outra ordem muda o topo
-- sem mudar a contagem de nascimentos (partida do Priest, 13/09: birth igual, presence diferente).
-- Aqui: pilha LIFO; objeto do motor e habilidade dada a unidade tiram numero, destruir devolve.
-- M.pres.hash acumula a sequencia (numero, objeto) e fica diferente depois da primeira troca de ordem.
M.pres = { prox = 1, livres = {}, hash = 0 }
M.PRES_TIPOS = { unit = true, item = true, destructable = true, timer = true, trigger = true, group = true,
  force = true, location = true, rect = true, region = true, effect = true, texttag = true, lightning = true,
  image = true, ubersplat = true, sound = true, dialog = true, button = true, fogmodifier = true,
  hashtable = true, multiboard = true, leaderboard = true, quest = true, questitem = true, timerdialog = true,
  trackable = true, unitpool = true, itempool = true, boolexpr = true, triggeraction = true,
  triggercondition = true, event = true }
local function pres_tira(marca)
  local p = M.pres
  local n = #p.livres
  local tag
  if n > 0 then tag = p.livres[n] p.livres[n] = nil else tag = p.prox p.prox = p.prox + 1 end
  p.hash = (p.hash * 31 + tag * 7 + (marca or 0)) % 4294967296
  return tag
end
local function pres_devolve(tag)
  if tag == nil then return end
  local p = M.pres
  p.livres[#p.livres + 1] = tag
  p.hash = (p.hash * 31 + tag) % 4294967296
end
__pres_tira, __pres_devolve = pres_tira, pres_devolve
function __pres_proximo() local p = M.pres local n = #p.livres if n > 0 then return p.livres[n] end return p.prox end
function __pres_hash() return M.pres.hash end
-- numeros de handle que o coletor simulado devolveu (so na maquina onde ele rodou; ver __gc_simulado)
M.hlivres = {}
-- [F5:priest] fim
-- [F5:herocw] fila de numeros livres do motor. Ligada por __mock.gc_handles (desligada por
-- padrao, para nao mexer em quem ja usava o mock). Com ela ligada o mock imita o Reforged: o
-- handle e objeto do Lua, o coletor recolhe quando quiser e o motor devolve o numero para a fila;
-- o proximo handle criado pega aquele numero de volta. Vale so para os tipos que sao do Lua --
-- unidade, item e destrutivel sao do motor (quem os destroi e o jogo, na mesma hora em todas as
-- maquinas), e evento/acao/condicao de gatilho pertencem ao gatilho.
M.livres = {}
M.gc_handles = false
local TIPOS_DO_LUA = {
  location = true, rect = true, region = true, timer = true, trigger = true, group = true,
  force = true, boolexpr = true, texttag = true, quest = true, questitem = true,
  defeatcondition = true, timerdialog = true, leaderboard = true, multiboard = true,
  multiboarditem = true, fogmodifier = true, effect = true, lightning = true, image = true,
  ubersplat = true, sound = true, dialog = true, button = true, unitpool = true, itempool = true,
  trackable = true, camerasetup = true, hashtable = true, gamecache = true, weathereffect = true,
  minimapicon = true,
}
M.livres_tipo = {}   -- quantos numeros voltaram para a fila por tipo de handle (diagnostico)
M.gc_tipo = {}       -- desses, quantos vieram do coletor (o mapa nunca mandou destruir)
local function devolve_numero(h, tab)
  local l = M.livres
  l[#l + 1] = h.__h
  local k = h.__kind or "?"
  tab[k] = (tab[k] or 0) + 1
end
-- Handle que o mapa manda destruir devolve o numero NA HORA, igual em todas as maquinas (e o que a
-- nativa Destroy* faz). O coletor so decide a hora do que o mapa NAO destruiu -- e e so ai que as
-- maquinas discordam. Por isso __gc so devolve o numero se ninguem destruiu o handle.
M.gc_rastro = {}     -- com M.rastro_gc, de onde veio o handle que o coletor levou (ate 8 exemplos)
local traceback_real = debug and debug.traceback  -- o mapa troca _G.debug pelo modulo dele
local META_GC = { __gc = function(h)
  if h.__morto then return end
  devolve_numero(h, M.gc_tipo)
  if h.__nasceu_em and #M.gc_rastro < 8 then M.gc_rastro[#M.gc_rastro + 1] = h.__kind .. " " .. h.__nasceu_em end
end }
function __mock_destroy_devolve_numero()
  local nomes = { "DestroyTimer", "DestroyTrigger", "DestroyGroup", "DestroyForce", "RemoveLocation",
    "RemoveRect", "RemoveRegion", "DestroyBoolExpr", "DestroyCondition", "DestroyFilter",
    "DestroyTextTag", "DestroyEffect", "DestroyLightning", "DestroyImage", "DestroyUbersplat",
    "DestroyFogModifier", "DestroyQuest", "DestroyQuestItem", "DestroyDefeatCondition",
    "DestroyTimerDialog", "DestroyLeaderboard", "DestroyMultiboard", "MultiboardReleaseItem",
    "DestroySound", "DialogDestroy", "RemoveWeatherEffect", "DestroyCameraSetup",
    "DestroyUnitPool", "DestroyItemPool", "DestroyTrackable", "DestroyMinimapIcon" }
  for _, n in ipairs(nomes) do
    local f = rawget(_G, n)
    if type(f) == "function" then
      rawset(_G, n, function(h, ...)
        if type(h) == "table" and h.__h and not h.__morto then
          h.__morto = true
          devolve_numero(h, M.livres_tipo)
        end
        return f(h, ...)
      end)
      -- o mapa roda com _ENV = __JENV, que e uma COPIA das globais feita no carregamento: sem isto
      -- a nativa trocada aqui so valeria para o runtime, nao para o codigo do mapa
      if type(__JENV) == "table" and rawget(__JENV, n) ~= nil then rawset(__JENV, n, rawget(_G, n)) end
    end
  end
end
-- [F5:herocw] fim
M.byid = {}   -- [F5:craft] id -> handle, para o truque I2U do mapa
local function newh(kind, extra)
  -- [F5:priest] __seq: ordem de criacao, igual em todas as maquinas (a ordem sincronizada do jogo).
  -- __h: numero de handle (GetHandleId), que o coletor de lixo simulado pode reaproveitar numa maquina
  -- so. Sem coletor simulado os dois sao o mesmo numero.
  local seq = M.nextid
  M.nextid = M.nextid + 1
  local hid = seq
  local livres = M.hlivres
  if #livres > 0 then hid = livres[#livres] livres[#livres] = nil end
  -- [F5:herocw] fila de numeros livres do motor (so com M.gc_handles ligado)
  if hid == seq and #M.livres > 0 then hid = table.remove(M.livres, 1) end
  local h = { __h = hid, __seq = seq, __kind = kind }
  if M.gc_handles and TIPOS_DO_LUA[kind] then
    setmetatable(h, META_GC)
    if M.rastro_gc and traceback_real then h.__nasceu_em = (traceback_real("", 2) or ""):gsub("%s+", " ") end
  end
  M.byid[h.__h] = h      -- [F5:craft]
  if M.PRES_TIPOS[kind] then h.__pres = pres_tira(seq) end
  -- [F5:priest] fim
  if __ds_trace then
    local linha = "+" .. kind .. " " .. h.__seq
    -- [KK:diag] Nos handles de `player` o traco leva TAMBEM de onde veio. `Player(i)` e' memoizado
    -- por indice, entao um handle de player NOVO significa "este indice foi pedido pela primeira
    -- vez aqui" -- e a origem na linha do traco nomeia o chamador. Foi assim que a divergencia que
    -- sobrou no lockstep da base KK (875 linhas) foi reduzida a ordem de primeira chamada de
    -- `Player(i)`. Sao poucos handles, entao o traco cresce pouco.
    -- [KK R1, 2.o teste] `__DS_ORIGEM` (tabela tipo -> true) pede a origem de outros tipos tambem
    -- (`_prova_perfil_rede.py`: os quadros de interface que uma maquina cria e a outra nao).
    if (kind == "player" or (__DS_ORIGEM and __DS_ORIGEM[kind])) and traceback_real then
      linha = linha .. " origem=" .. (traceback_real("", 2) or ""):gsub("%s+", " ")
    end
    __ds_trace[#__ds_trace + 1] = linha
  end -- [F5:priest] __seq
  if extra then for k, v in pairs(extra) do h[k] = v end end
  return h
end
__newh = newh
-- [F5:craft] o mapa converte id de handle em unidade com ConvertFogState + SaveFogStateHandle +
-- LoadUnitHandle (truque classico do JASS, usado em war3map.j:57265 para achar a unidade cujo
-- inventario esta aberto). No motor de verdade a tabela de hash guarda o id e reinterpreta o tipo na
-- leitura; aqui basta devolver o handle que tem aquele id.
function ConvertFogState(i)
  if type(i) == "number" and M.byid[i] ~= nil then return M.byid[i] end
  return newh("fogstate")
end
function GetHandleId(h) if h == nil then return 0 end if type(h) == "table" then return h.__h or 0 end return 0 end
-- [F5:dmgaudit] constantes convertidas (ConvertDamageType(14), ConvertAttackType(6)...): no jogo a mesma
-- chamada devolve sempre o mesmo objeto e GetHandleId dele e o proprio numero. O stub antigo criava um
-- handle novo (com numero novo) a cada chamada, entao DT_Dep[GetHandleId(BlzGetEventDamageType())] nunca
-- batia e o pipeline de dano do mapa nao distinguia dano fisico de magico no simulador.
M.conv = {}
function __conv(kind, i)
  local key = kind .. ":" .. tostring(i)
  local h = M.conv[key]
  if h == nil then h = { __h = i, __kind = kind } M.conv[key] = h end
  return h
end
-- [F5:dmgaudit] fim
local players = {}
-- [KK:diag] Os 16 objetos de jogador existem no MOTOR desde o carregamento do mapa, entao
-- `GetHandleId(Player(i))` e' FIXO e nao depende de qual indice foi pedido primeiro. A criacao
-- preguicosa (so ao pedir) fazia o numero sintetico depender da ORDEM das chamadas e inventava
-- diferenca no lockstep: com `GetLocalPlayer()` rodando antes de `Player(0)`, os numeros saem
-- trocados entre as duas maquinas sem que nada de errado tenha acontecido no mapa.
-- Medido na base KK: 420 linhas de diff que eram todas isso (ver ANDAMENTO_KK.md, rodada 7).
function Player(i) if i > 15 then i = i - 12 end
  if not players.prontos then
    for k = 0, 15 do
      if not players[k] then
        players[k] = newh("player", { id = k, team = ((k == 8 or k == 9) and -1 or ((k >= 10) and 1 or 0)) })
      end
    end
    players.prontos = true
  end
  return players[i] end
__MOCK_LOCAL = __MOCK_LOCAL or 0
function GetLocalPlayer() return Player(__MOCK_LOCAL) end
function GetPlayerId(p) return p and p.id or -1 end
function GetPlayerName(p) return "Player" .. tostring(p and p.id or 0) .. "#1234" end
function GetPlayerController(p) if p and p.id < 8 then return MAP_CONTROL_USER end return MAP_CONTROL_COMPUTER end
function GetPlayerSlotState(p) if p and p.id < 2 then return PLAYER_SLOT_STATE_PLAYING end return PLAYER_SLOT_STATE_EMPTY end
function GetPlayerRace(p) return RACE_HUMAN end
function GetPlayerStartLocation(p) return 0 end
function GetPlayerColor(p) return PLAYER_COLOR_RED end
function IsPlayerAlly(a, b) return a == b end
function IsPlayerEnemy(a, b) return a ~= b end
function IsUnitAlly(u, p) return u and u.owner == p end
function IsUnitEnemy(u, p) return u and u.owner ~= p end
-- [F5:desyncyone] antes devolvia sempre true: com isso CountPlayersInForceBJ sem ForForce contaria
-- os 16 slots. A forca do mock e { list = {...} }, entao da para responder de verdade.
function IsPlayerInForce(p, f)
  if not f or not f.list then return false end
  for _, q in ipairs(f.list) do if q == p then return true end end
  return false
end
-- [F5:desyncyone] fim
-- [R1F1:enhance] estado de jogador: substituido pela versao do anticheat (mesma ideia, mais __mock_recurso)
-- [R1F1:anticheat] inicio: ouro e madeira de verdade no simulador.
-- O stub devolvia 0 para GetPlayerState e SetPlayerState nao fazia nada, entao o recurso do jogador
-- era invisivel aqui -- e sem ele nao da para medir nem a sonda de recurso do anti-cheat nem os
-- codigos GreedIsGood/KeyserSoze/LeafItToMe. Agora cada jogador tem uma gaveta de estados; o valor
-- e inteiro, como no motor. `__mock_recurso` mexe no valor SEM passar pela nativa: e assim que o
-- motor do jogo entrega o que o codigo digitado no chat deu.
function GetPlayerState(p, s)
  if p == nil then return 0 end
  p.state = p.state or {}
  return p.state[s] or 0
end
function SetPlayerState(p, s, v)
  if p == nil then return end
  p.state = p.state or {}
  p.state[s] = math.floor(tonumber(v) or 0)
end
function __mock_recurso(p, s, delta)
  if p == nil then return end
  p.state = p.state or {}
  p.state[s] = (p.state[s] or 0) + math.floor(tonumber(delta) or 0)
end
-- [R1F1:anticheat] fim
function GetPlayerStructureCount(p, inc) return 0 end
function GetPlayerUnitCount(p, inc) return 0 end
function GetPlayerTypedUnitCount(p, n, a, b) return 0 end
function GetPlayerTechCount(p, id, r) return 0 end
function GetPlayerTechMaxAllowed(p, id) return -1 end
function GetPlayerTechResearched(p, id, r) return false end

-- medido em jogo: este mapa (w3i v28) roda no layout classico de 16 slots
function GetBJMaxPlayers() return 12 end
function GetBJPlayerNeutralVictim() return 13 end
function GetBJPlayerNeutralExtra() return 14 end
function GetBJMaxPlayerSlots() return 16 end
function GetPlayerNeutralPassive() return 15 end
function GetPlayerNeutralAggressive() return 12 end
function GetCameraTargetPositionLoc() return __newh("location", { x = 0, y = 0 }) end  -- [F5:herocw] nativa: ponto novo
function VersionGet() return VERSION_FROZEN_THRONE end
function VersionCompatible(v) return true end
function VersionSupported(v) return true end
-- hashtables
local hts = {}
function InitHashtable() local h = newh("hashtable") hts[h] = {} return h end
-- [F5:castleboss] a hashtable do motor tem UMA GAVETA POR TIPO: inteiro, real, booleano, texto e
-- handle sao cinco slots distintos na MESMA chave (pai, chave). O mapa conta com isso -- o
-- GS_Suspend, por exemplo, guarda um booleano e um timer na chave 1 da mesma unidade, e o
-- RemoveSavedHandle do FIX6 so pode apagar o timer. Com uma gaveta so, o mock apagava os dois e a
-- suspensao nunca expirava.
local function hget(ht, a, b, tp) local t = hts[ht] if not t then return nil end local r = t[a] if not r then return nil end local s = r[tp] if not s then return nil end return s[b] end
local function hset(ht, a, b, v, tp) local t = hts[ht] if not t then return end local r = t[a] if not r then r = {} t[a] = r end local s = r[tp] if not s then if v == nil then return end s = {} r[tp] = s end s[b] = v end
function SaveInteger(ht, a, b, v) hset(ht, a, b, v, 1) end
-- [F5:cards] o motor guarda real de hashtable em float32: SaveReal(ht, a, b, 0.01) volta 0.0099999997764826
-- para o Lua de double. Guardar o double cru escondia o "0%" do codice de cartas (R2I(0.99999997764826) = 0).
-- --real64 volta ao comportamento antigo, para comparar.
if __MOCK_REAL64 then
function SaveReal(ht, a, b, v) hset(ht, a, b, v, 2) end
else
function SaveReal(ht, a, b, v) if math.type(v) then v = (string.unpack("<f", string.pack("<f", v))) end hset(ht, a, b, v, 2) end
end
-- [F5:cards] fim
function SaveBoolean(ht, a, b, v) hset(ht, a, b, v, 3) end
function SaveStr(ht, a, b, v) hset(ht, a, b, v, 4) return true end
function LoadInteger(ht, a, b) return hget(ht, a, b, 1) or 0 end
function LoadReal(ht, a, b) return hget(ht, a, b, 2) or 0.0 end
function LoadBoolean(ht, a, b) return hget(ht, a, b, 3) or false end
function LoadStr(ht, a, b) local v = hget(ht, a, b, 4) if v == nil then return nil end return v end
function HaveSavedInteger(ht, a, b) return hget(ht, a, b, 1) ~= nil end
function HaveSavedReal(ht, a, b) return hget(ht, a, b, 2) ~= nil end
function HaveSavedBoolean(ht, a, b) return hget(ht, a, b, 3) ~= nil end
function HaveSavedString(ht, a, b) return hget(ht, a, b, 4) ~= nil end
function HaveSavedHandle(ht, a, b) return hget(ht, a, b, 5) ~= nil end
function RemoveSavedInteger(ht, a, b) hset(ht, a, b, nil, 1) end
function RemoveSavedReal(ht, a, b) hset(ht, a, b, nil, 2) end
function RemoveSavedBoolean(ht, a, b) hset(ht, a, b, nil, 3) end
function RemoveSavedString(ht, a, b) hset(ht, a, b, nil, 4) end
function RemoveSavedHandle(ht, a, b) hset(ht, a, b, nil, 5) end
-- [F5:castleboss] fim
function FlushParentHashtable(ht) hts[ht] = {} end
function FlushChildHashtable(ht, a) local t = hts[ht] if t then t[a] = nil end end
-- [F5:perf] tamanho das hashtables (sonda de sessao longa): devolve lista {id, pais, filhos}
function __mock_ht_stats()
  local out = {}
  for h, t in pairs(hts) do
    local pais, filhos = 0, 0
    for _, r in pairs(t) do pais = pais + 1 for _, gav in pairs(r) do for _ in pairs(gav) do filhos = filhos + 1 end end end -- [F5:castleboss] gaveta por tipo
    out[#out + 1] = { h.__h, pais, filhos }
  end
  table.sort(out, function(a, b) return a[3] > b[3] end)
  return out
end
function __mock_ht_pais(ht)
  local t = hts[ht]
  local out = {}
  if t then for k in pairs(t) do out[#out + 1] = k end end
  return out
end
function __mock_ht_filhos(ht, pai)
  local t = hts[ht]
  local out = {}
  if t and t[pai] then for _, gav in pairs(t[pai]) do for k in pairs(gav) do out[#out + 1] = k end end end -- [F5:castleboss] gaveta por tipo
  table.sort(out, function(a, b) return tostring(a) < tostring(b) end)
  return out
end
-- [F5:perf] fim
for _, k in ipairs({"Player","Widget","Destructable","Item","Unit","Ability","Timer","Trigger","TriggerCondition","TriggerAction",
  "TriggerEvent","Force","Group","Location","Rect","BooleanExpr","Sound","Effect","UnitPool","ItemPool","Quest","QuestItem",
  "DefeatCondition","TimerDialog","Leaderboard","Multiboard","MultiboardItem","Trackable","Dialog","Button","TextTag","Lightning",
  -- [KK R1, 2.o teste] "Frame", nao "FrameHandle": a nativa e' `SaveFrameHandle`/`LoadFrameHandle`. Com
  -- "FrameHandle" saiam `SaveFrameHandleHandle`/`LoadFrameHandleHandle`, e as de verdade caiam no stub
  -- generico -- `LoadFrameHandle` criava um handle NOVO a cada leitura (o `DB_fh` da camada nunca
  -- devolvia o quadro guardado, e todo `DzFrame*` num trecho local aparecia como divergencia no lockstep)
  "Image","Ubersplat","Region","FogState","FogModifier","Hashtable","Frame"}) do
  -- [F5:castleboss] todo Save*Handle escreve a MESMA gaveta de handle (slot 5), como no motor
  _G["Save" .. k .. "Handle"] = function(ht, a, b, v) hset(ht, a, b, v, 5) return true end
  _G["Load" .. k .. "Handle"] = function(ht, a, b) return hget(ht, a, b, 5) end
end
function SaveAgentHandle(ht, a, b, v) hset(ht, a, b, v, 5) return true end
-- [DS] o load TIPADO do motor (jassdoc, testado na 2.0.3: "you cannot put an item into a widget hashtable and
-- retrieve it as a unit type. The load handle function will return null"). O mock devolvia o que estivesse na
-- gaveta: o `KK_mis_sloop` (o projetil que e' UNIDADE, as orbes da A0Z2/A0Z3/A0Z4) pegava a unidade pelo
-- `LoadEffectHandle` e a movia como EFEITO (`DzSetEffectPos` -> a leitura local `DB_ef`), um ramo que o motor
-- nao toma. So' o efeito, por ora (o resto dos tipos continua permissivo: `port/analysis/DESYNC_GODSLAYER.md`).
do
  local lef = LoadEffectHandle
  function LoadEffectHandle(ht, a, b)
    local v = lef(ht, a, b)
    if type(v) == "table" and v.__kind ~= nil and v.__kind ~= "effect" then return nil end
    return v
  end
end

-- strings
function I2S(i) return string.format("%d", math.tointeger(i) or math.floor(i)) end
function R2S(r) return string.format("%.3f", r) end
function R2SW(r, w, p) return string.format("%" .. w .. "." .. p .. "f", r) end
function S2I(s) if s == nil then return 0 end local n = tonumber(s:match("^%s*(-?%d+)")) return n or 0 end
function S2R(s) if s == nil then return 0.0 end local n = tonumber(s:match("^%s*(-?[%d%.]+)")) return n or 0.0 end
function R2I(r) if r >= 0 then return math.floor(r) else return math.ceil(r) end end
function I2R(i) return i * 1.0 end
function StringLength(s) return s and #s or 0 end
function SubString(s, a, b) if s == nil then return nil end return s:sub(a + 1, b) end
function StringCase(s, up) if s == nil then return nil end if up then return s:upper() end return s:lower() end
function StringHash(s)
  s = s or ""
  local h = 0
  for i = 1, #s do h = (h * 31 + s:byte(i)) & 0xFFFFFFFF end
  if h >= 0x80000000 then h = h - 0x100000000 end
  return h
end
function GetLocalizedString(s) return s end
function GetLocalizedHotkey(s) return 0 end
function UnitId(s) if s == nil or #s ~= 4 then return 0 end return string.unpack(">I4", s) end
function UnitId2String(i) if i == 0 then return "" end return string.pack(">I4", i & 0xFFFFFFFF) end
function AbilityId(s) return 0 end
function AbilityId2String(i) return "" end
function GetObjectName(id) return "obj" end
function GetAbilityName(id) local rec = __slk_raw.ability[string.pack(">I4", id & 0xFFFFFFFF)] return rec and rec.name or "" end
function GetUnitName(u) return u and "unit" or nil end
function GetItemName(i) return "item" end
function GetItemTypeId(i) return i and i.typeid or 0 end
math.randomseed(12345)
-- o sorteio do motor e nativo: nao pode passar por math.random, que o mapa redireciona de
-- volta para ca (no jogo de verdade GetRandomInt nao tem nada a ver com o math.random do Lua)
local _sorteio = math.random
function GetRandomInt(a, b) if b < a then return a end return _sorteio(a, b) end
function GetRandomReal(a, b) return a + (b - a) * _sorteio() end
function SetRandomSeed(s) end
-- watchdog: aborta callbacks que passam de N instrucoes (loop infinito)
local WATCHDOG = 20000000
local wd_depth = 0
local function wd_hook()
  error("watchdog: loop longo demais em " .. tostring(debug.traceback("", 2)):sub(1, 1200), 0)
end
function __wd_on()
  debug.sethook(wd_hook, "", WATCHDOG)
end
function __wd_off() debug.sethook() end
function __wd_call(f, ...)
  wd_depth = wd_depth + 1
  __wd_on()
  local ok, e = pcall(f, ...)
  wd_depth = wd_depth - 1
  if wd_depth > 0 then __wd_on() else __wd_off() end
  return ok, e
end
function Sin(x) return math.sin(x) end
function Cos(x) return math.cos(x) end
function Tan(x) return math.tan(x) end
function Atan(x) return math.atan(x) end
function Atan2(y, x) return math.atan(y, x) end
function SquareRoot(x) return math.sqrt(math.max(0, x)) end
function Pow(a, b) return a ^ b end
function Deg2Rad(d) return math.rad(d) end
function Rad2Deg(r) return math.deg(r) end
function MathRound(r) return math.floor(r + 0.5) end
function ModuloInteger(a, b) return math.fmod(a, b) end
function ModuloReal(a, b) return math.fmod(a, b) end

-- timers
-- M.nasc: cada callback que o motor executa (temporizador, condicao, acao, filtro, enumeracao,
-- ExecuteFunc). No motor do 3.0.0 cada um e uma thread e conta no "next birth tag"; as duas maquinas
-- do mock_lockstep.py tem de chegar ao mesmo numero no mesmo tique.
M.nasc = 0
function CreateTimer() local t = newh("timer", { elapsed = 0.0 }) return t end
function TimerStart(t, timeout, periodic, func) if t == nil then return end t.timeout = timeout t.periodic = periodic t.func = func t.due = M.now + timeout t.start = M.now M.timers[t] = true end
function PauseTimer(t) if t then M.timers[t] = nil end end
function ResumeTimer(t) if t and t.func then M.timers[t] = true end end
-- [3.o teste da R1, relatos T6/T7] FIEL AO MOTOR (jassdoc `common.j:12358`, @bug): "Destroying does not pause
-- timer, so if call of its callback is scheduled, then callback is called with GetExpiredTimer being null".
-- O relogio destruido SEM `PauseTimer` continua agendado; o retorno roda com `GetExpiredTimer()` nulo (o
-- periodico, para sempre; o de disparo unico, uma vez). Antes o mock o tirava da fila: a Q do Priest e a G
-- do Berserker (periodo 0 + Flush + Destroy sem pausa) passavam na sonda e travavam o jogo.
M.retornos_nulos = 0
function DestroyTimer(t) if t then t.destruido = true end end
function TimerGetElapsed(t) if not t or not t.start then return 0.0 end return M.now - t.start end
function TimerGetRemaining(t) if not t or not t.due then return 0.0 end return math.max(0, t.due - M.now) end
function TimerGetTimeout(t) return t and t.timeout or 0.0 end
__expired = nil
-- [28/09/2026, o crash do Sacred Tree R1 e do Dream R2-F1] FIEL AO MOTOR (jassdoc `common.j:12447`, @bug): "Might crash
-- the game if called when there is no expired timer". Num gatilho de EVENTO (unidade, dano, morte, chat, sincronia,
-- tecla, ordem, dialogo...) o motor le o dado do evento como se fosse o de um relogio e o jogo FECHA -- o relatorio de
-- crash do Sacred Tree R1 (atacar/matar monstro) e' isso: o `KK_fx_de()` do `-fx` chamava a nativa em todo contexto, e
-- o mock devolvia nulo (a sonda passava). A regra geral: a nativa so' vale DENTRO do retorno de um relogio (`TimerStart`,
-- ou o gatilho de evento de relogio), inclusive no que ele chama (`TriggerExecute`, `ForGroup`, `ExecuteFunc`...), e
-- nunca num gatilho de evento disparado de dentro dele. `__ctx` e' o contexto mais interno: "relogio" (o retorno do
-- relogio e o gatilho de evento de relogio), "evento" (os disparos de evento do mock: o bloco no fim do MOCK_PRELUDE) ou
-- nil (a carga, a cena chamando o mapa direto). Fora do "relogio": um ERRO por sitio distinto (a sonda nao passa) e
-- `M.expirado_fora` conta todas as chamadas.
__ctx = nil
M.expirado_fora = 0
M.expirado_fora_sitios = {}
function GetExpiredTimer()
  if __ctx ~= "relogio" then
    M.expirado_fora = M.expirado_fora + 1
    local tb = debug.traceback("", 2)
    local fns = {}
    for nome in tb:gmatch("function '([%w_]+)'") do
      fns[#fns + 1] = nome
      if #fns >= 4 then break end
    end
    local sitio = #fns > 0 and table.concat(fns, " <- ") or tb:sub(1, 300)
    if not M.expirado_fora_sitios[sitio] then
      M.expirado_fora_sitios[sitio] = true
      __logerr("MOTOR_FIEL: GetExpiredTimer() fora do retorno de um relogio (contexto: " .. tostring(__ctx or "carga/cena")
               .. "; o jogo FECHA, jassdoc @bug) em " .. sitio)
    end
    return nil
  end
  return __expired
end
-- [R1F2:stutter] inicio: linha do tempo de custo por tique.
-- Liga com --perftick=ARQ. Para cada passo do simulador mede o tempo de PAREDE gasto em cada
-- callback de temporizador do motor (que e onde mora todo ciclo periodico do mapa e do runtime) e
-- guarda (a) o acumulado por callback, (b) os N passos mais caros com a decomposicao, (c) o custo
-- por segundo de jogo. A chave do callback e "arquivo:linha em que a funcao foi definida" -- no
-- war3map.lua gerado essa linha identifica o bloco (o relatorio imprime o trecho em volta).
-- Sem --perftick nada disso roda: o caminho normal fica identico ao da tools_R1F1.
__PERF_ON = false
__PERF_ACC = {}      -- chave -> { ms, n, max, tmax }
__PERF_PICOS = {}    -- passos mais caros: { t, ms, itens = { {chave, ms}, ... } }
__PERF_SEG = {}      -- segundo de jogo -> ms gastos em callback
__PERF_NPASSO, __PERF_MS = 0, 0
__PERF_PICOS_MAX = 60
__PERF_MIN_ITEM = 0.05   -- ms: item mais barato que isso nao entra na decomposicao do pico
local perf_chave = setmetatable({}, { __mode = "k" })
-- todo callback de temporizador passa pelo `__wrap_motor` do rt_core (contagem de thread do motor),
-- entao `t.func` e SEMPRE a mesma closure: a funcao de verdade e o upvalue `f` dela. Desembrulha
-- ate tres niveis antes de perguntar onde a funcao foi definida.
-- so desembrulha o que tem EXATAMENTE a forma do __wrap_motor (upvalues `f` e `nome`): uma closure
-- qualquer do mapa que capture um local chamado `f` nao pode ser confundida com o embrulho.
local function perf_desembrulha(f)
  for _ = 1, 3 do
    local cand, tem_nome = nil, false
    for i = 1, 6 do
      local n, v = debug.getupvalue(f, i)
      if n == nil then break end
      if n == "f" and type(v) == "function" then cand = v end
      if n == "nome" then tem_nome = true end
    end
    if cand == nil or not tem_nome then return f end
    f = cand
  end
  return f
end
-- nome da funcao, quando ela for global do mapa (__JENV) ou do runtime (_G): e o rotulo que serve
-- para funcao vinda de chunk carregado por load(), onde o numero de linha nao diz nada.
local perf_nomes = nil
local function perf_nome(f)
  if perf_nomes == nil then
    perf_nomes = setmetatable({}, { __mode = "k" })
    for k, v in pairs(_G) do if type(v) == "function" and perf_nomes[v] == nil then perf_nomes[v] = k end end
    if __JENV ~= nil then
      for k, v in pairs(__JENV) do if type(v) == "function" then perf_nomes[v] = k end end
    end
  end
  return perf_nomes[f]
end
-- TriggerRegisterTimerEvent do mock poe a MESMA closure em todos os temporizadores de gatilho: o
-- gatilho de verdade e o upvalue `t` dela. Troca pela primeira acao do gatilho, que e a funcao do
-- mapa (tambem embrulhada pelo __wrap_motor).
local function perf_acao_do_gatilho(f)
  for i = 1, 6 do
    local n, v = debug.getupvalue(f, i)
    if n == nil then break end
    if n == "t" and type(v) == "table" and type(v.actions) == "table" and v.actions[1] ~= nil then
      return v.actions[1]
    end
  end
  return nil
end
function __perf_chave_de(f0)
  local k = perf_chave[f0]
  if k ~= nil then return k end
  k = "?"
  if type(f0) == "function" and type(debug) == "table" then
    local ok, f = pcall(perf_desembrulha, f0)
    if not ok then f = f0 end
    local oka, acao = pcall(perf_acao_do_gatilho, f)
    if oka and type(acao) == "function" then
      local okd, f2 = pcall(perf_desembrulha, acao)
      if okd then f = f2 else f = acao end
    end
    local ok2, d = pcall(debug.getinfo, f, "S")
    if ok2 and type(d) == "table" then
      -- o nome do chunk FAZ PARTE da chave: os trechos Lua do mapa (p9_code, p15_code...) sao
      -- carregados por load() e tem numeracao de linha propria, que colide com a do war3map.lua
      k = tostring(d.short_src) .. ":" .. tostring(d.linedefined)
    end
    local okn, nome = pcall(perf_nome, f)
    if okn and nome ~= nil then k = k .. " <" .. tostring(nome) .. ">" end
  end
  perf_chave[f0] = k
  return k
end
function __perf_conta(chave, dt, t)
  local a = __PERF_ACC[chave]
  if a == nil then a = { ms = 0, n = 0, max = 0, tmax = 0 } __PERF_ACC[chave] = a end
  a.ms = a.ms + dt
  a.n = a.n + 1
  if dt > a.max then a.max = dt a.tmax = t end
end
local function perf_fecha(t0, itens, agora)
  local ms = (__wall() - t0) * 1000
  __PERF_NPASSO = __PERF_NPASSO + 1
  __PERF_MS = __PERF_MS + ms
  local s = math.floor(agora)
  __PERF_SEG[s] = (__PERF_SEG[s] or 0) + ms
  local n = #__PERF_PICOS
  local pior = (n >= __PERF_PICOS_MAX) and __PERF_PICOS[n].ms or -1
  if ms > pior then
    local finos = {}
    for i = 1, #itens, 2 do
      if itens[i + 1] >= __PERF_MIN_ITEM then finos[#finos + 1] = { itens[i], itens[i + 1] } end
    end
    table.sort(finos, function(a, b) return a[2] > b[2] end)
    __PERF_PICOS[n + 1] = { t = agora, ms = ms, itens = finos }
    table.sort(__PERF_PICOS, function(a, b) return a.ms > b.ms end)
    if #__PERF_PICOS > __PERF_PICOS_MAX then __PERF_PICOS[#__PERF_PICOS] = nil end
  end
end
-- [R1F2:stutter] fim
function __mock_advance(seconds, step)
  local target = M.now + seconds
  while M.now < target do
    M.now = M.now + step
    local perf_t0, perf_itens                                   -- [R1F2:stutter]
    if __PERF_ON then perf_t0 = __wall() perf_itens = {} end     -- [R1F2:stutter]
    __mock_deliver_sync()
    if __mock_decay_tick then __mock_decay_tick() end
    local fired = {}
    for t in pairs(M.timers) do if t.due and t.due <= M.now then fired[#fired + 1] = t end end
    table.sort(fired, function(a, b) return a.__seq < b.__seq end) -- [F5:priest] ordem de criacao, nao numero de handle
    for _, t in ipairs(fired) do
      if M.timers[t] then
        if t.periodic then t.due = t.due + t.timeout else M.timers[t] = nil end
        -- [R1F2:stutter] o corpo do `if t.func` e o mesmo; com --perftick ele fica cronometrado
        -- [3.o teste] relogio destruido sem pausa: o retorno roda com `GetExpiredTimer()` nulo (ver DestroyTimer)
        if t.destruido and t.func then M.retornos_nulos = M.retornos_nulos + 1 end
        local pctx = __ctx __ctx = "relogio"   -- [28/09/2026] o retorno do relogio: o GetExpiredTimer() vale (ver acima)
        if t.func and __PERF_ON then
          M.nasc = M.nasc + 1 __expired = (not t.destruido) and t or nil
          local w0 = __wall()
          local ok, e = __wd_call(t.func)
          local dt = (__wall() - w0) * 1000
          local ch = __perf_chave_de(t.func) .. " @" .. string.format("%.2f", t.timeout or -1) .. "s"
          __perf_conta(ch, dt, M.now)
          perf_itens[#perf_itens + 1] = ch
          perf_itens[#perf_itens + 1] = dt
          __expired = nil if not ok then __logerr("timer: " .. tostring(e)) end
        elseif t.func then M.nasc = M.nasc + 1 __expired = (not t.destruido) and t or nil local ok, e = __wd_call(t.func) __expired = nil if not ok then __logerr("timer: " .. tostring(e)) end end
        -- [R1F2:aspd2] gatilhos registrados com TriggerRegisterTimerExpireEvent (independem da callback)
        if t.expira then
          local pe = __trigger_event
          __expired = t __trigger_event = EVENT_GAME_TIMER_EXPIRED
          for _, tg in ipairs(t.expira) do __mock_fire(tg) end
          __trigger_event = pe __expired = nil
        end
        __ctx = pctx
      end
    end
    if __mock_vida_tick then __mock_vida_tick() end -- [F5:priest] tempo de vida de unidade (cenario --priest-e)
    if __mock_tt_tick then __mock_tt_tick() end -- [C2] texto flutuante de vida curta
    if __mock_cheat_tick then __mock_cheat_tick() end -- [R1F1:anticheat] efeito continuo dos codigos
    if __PERF_ON then perf_fecha(perf_t0, perf_itens, M.now) end -- [R1F2:stutter]
  end
end

-- ===== traco de dessincronizacao =====
-- Chamada que muda o estado da simulacao tem de sair igual em todas as maquinas. Aqui elas sao
-- gravadas em ordem; rodar o mesmo mapa com jogadores locais diferentes e comparar os dois tracos
-- mostra exatamente onde o codigo local escapou para o estado de jogo.
__DS_NATIVAS = {
  "CreateUnit", "CreateUnitAtLoc", "CreateUnitByName", "RemoveUnit", "KillUnit", "SetUnitX", "SetUnitY",
  "SetUnitPosition", "SetUnitState", "SetUnitScale", "SetUnitFlyHeight", "SetUnitMoveSpeed", "SetUnitOwner",
  "UnitAddAbility", "UnitRemoveAbility", "SetUnitAbilityLevel", "UnitMakeAbilityPermanent", "SetHeroLevel",
  "AddHeroXP", "SetHeroXP", "ModifyHeroSkillPoints", "SetPlayerState", "SetPlayerHandicapXP", "SetPlayerHandicap",
  "CreateItem", "UnitAddItem", "UnitAddItemToSlotById", "UnitRemoveItem", "RemoveItem", "SetItemCharges",
  "IssueImmediateOrder", "IssueTargetOrder", "IssuePointOrder", "IssueImmediateOrderById", "IssueTargetOrderById",
  "IssuePointOrderById", "PauseUnit", "ShowUnit", "SetUnitInvulnerable", "UnitDamageTarget", "ForceAddPlayer",
  "ForceRemovePlayer", "GetRandomInt", "GetRandomReal", "SetUnitPathing", "SetUnitAnimation", "SelectUnit",
  "CreateFogModifierRect", "FogModifierStart", "CustomDefeatBJ", "RemovePlayer", "SetPlayerAbilityAvailable",
  "TimerStart", "PauseTimer", "ResumeTimer", "DestroyTimer", "EnableTrigger", "DisableTrigger",
  "DestroyTrigger", "TriggerRegisterTimerEvent", "TriggerRegisterTimerEventSingle", "SetPlayerTechResearched",
}

local function ds_arg(v)
  local tv = type(v)
  if tv == "number" then
    if math.type(v) == "integer" then return tostring(v) end
    return string.format("%.4f", v)
  elseif tv == "string" then return v
  elseif tv == "boolean" then return tostring(v)
  elseif tv == "table" then return (v.__kind or "h") .. "#" .. tostring(v.__seq or v.__h) -- [F5:priest] __seq
  elseif tv == "nil" then return "nil"
  end
  return "<" .. tv .. ">"
end

function __ds_wrap()
  for _, n in ipairs(__DS_NATIVAS) do
    local f = rawget(_G, n)
    if type(f) == "function" then
      rawset(_G, n, function(...)
        local a = table.pack(...)
        local r = f(...)
        if __ds_trace then
          local parts = {}
          for i = 1, a.n do parts[i] = ds_arg(a[i]) end
          local linha = n .. "(" .. table.concat(parts, ",") .. ")"
          local d = debug.getinfo(2, "Sl")
          if d and (d.short_src or ""):find("rt_c") then d = debug.getinfo(3, "Sl") end
          if d then linha = linha .. " @" .. tostring(d.currentline) end
          if r ~= nil then linha = linha .. " -> " .. ds_arg(r) end
          __ds_trace[#__ds_trace + 1] = linha
        end
        return r
      end)
    end
  end
end

function __ds_dump()
  if not __ds_trace then return "" end
  -- fecha com a lista de temporizadores vivos: um a mais de um lado ja e assimetria de estado
  local vivos = {}
  for t in pairs(__mock.timers) do vivos[#vivos + 1] = t end
  table.sort(vivos, function(x, y) return x.__seq < y.__seq end) -- [F5:priest] __seq
  __ds_trace[#__ds_trace + 1] = "== temporizadores vivos: " .. #vivos
  for _, t in ipairs(vivos) do
    __ds_trace[#__ds_trace + 1] = string.format("   timer#%d periodico=%s intervalo=%.3f vence=%.3f",
      t.__seq, tostring(t.periodic), t.timeout or -1, t.due or -1) -- [F5:priest] __seq
  end
  return table.concat(__ds_trace, "\n")
end

-- triggers
__trigger = nil
__trigger_unit = nil
__trigger_player = nil
function CreateTrigger() return newh("trigger", { actions = {}, conds = {}, enabled = true, events = {} }) end
-- [F5:dmgaudit] gatilho destruido sai da lista de eventos (antes continuava sendo disparado)
function DestroyTrigger(t) if t then t.actions = {} t.conds = {} if M.trig_events then M.trig_events[t] = nil end for _, s in pairs(M.dmg_trigs or {}) do s[t] = nil end end end
-- [F5:dmgaudit] fim
function EnableTrigger(t) if t then t.enabled = true end end
function DisableTrigger(t) if t then t.enabled = false end end
function IsTriggerEnabled(t) return t and t.enabled or false end
function TriggerAddAction(t, f) if t then t.actions[#t.actions + 1] = f return newh("triggeraction") end end
function TriggerAddCondition(t, b) if t and b then t.conds[#t.conds + 1] = b return newh("triggercondition") end end
function TriggerRemoveAction(t, a) end
function TriggerRemoveCondition(t, c) end
function TriggerClearActions(t) if t then t.actions = {} end end
function TriggerClearConditions(t) if t then t.conds = {} end end
-- (08/10/2026) o tipo do common.j: conditionfunc/filterfunc (estendem boolexpr); o simulador confere os tipos
function Condition(f) return newh("conditionfunc", { fn = f }) end
function Filter(f) return newh("filterfunc", { fn = f }) end
function DestroyBoolExpr(b) end
DestroyCondition, DestroyFilter = DestroyBoolExpr, DestroyBoolExpr
function And(a, b) return newh("boolexpr", { fn = function() return (a.fn == nil or a.fn()) and (b.fn == nil or b.fn()) end }) end
function Or(a, b) return newh("boolexpr", { fn = function() return (a.fn and a.fn()) or (b.fn and b.fn()) end }) end
function Not(a) return newh("boolexpr", { fn = function() return not (a.fn and a.fn()) end }) end
function GetTriggeringTrigger() return __trigger end
function GetTriggerUnit() return __trigger_unit end
__killing_unit = nil
function GetKillingUnit() return __killing_unit end
function GetDyingUnit() return __trigger_unit end
function IsSuspendedXP(u) return u and u.suspended or false end
function SuspendHeroXP(u, f) if u then u.suspended = f end end
function GetHeroXP(u) return u and u.xp or 0 end
-- [F5:repick] o mock somava XP e nunca subia de nivel, entao o caminho de aprender skill do mapa
-- (que depende de nivel -> ponto de skill -> SelectHeroSkill) nunca rodava aqui. Curva simples: o
-- que importa medir nao e a curva do motor, e sim se o mapa concede as skills no nivel alcancado.
function __mock_xp_nivel(n) return (100 * (n - 1) * n) // 2 end
function AddHeroXP(u, xp, show)
  if u == nil then return end
  if u.suspended then return end
  u.xp = (u.xp or 0) + (xp or 0)
  local voltas = 0
  while (u.level or 1) < 400 and u.xp >= __mock_xp_nivel((u.level or 1) + 1) do
    u.level = (u.level or 1) + 1
    u.points = (u.points or 0) + 1
    voltas = voltas + 1
    __mock_unit_event(u, EVENT_PLAYER_HERO_LEVEL)
    if voltas > 500 then break end
  end
end
-- [F5:repick] fim
function SetHeroXP(u, xp, show) if u then u.xp = xp end end
function GetPlayerHandicapXP(p) return p and p.handicapxp or 1.0 end
function SetPlayerHandicapXP(p, v) if p then p.handicapxp = v end end
function GetPlayerTeam(p) if p == nil then return -1 end return p.team or 0 end
-- medido em jogo: o motor ignora SetPlayerTeam nos slots neutros (12..15)
function SetPlayerTeam(p, t) if p and p.id < 12 then p.team = t end end
function __mock_kill(u, killer)
  local fired = 0
  local pu, pk, pp = __trigger_unit, __killing_unit, __trigger_player
  __trigger_unit, __killing_unit, __trigger_player = u, killer, u.owner
  local gat = {} for t in pairs(M.trig_events or {}) do gat[#gat + 1] = t end
  table.sort(gat, function(x, y) return x.__seq < y.__seq end) -- [F5:priest] __seq
  -- [F5:perf] no motor a unidade JA esta morta quando o evento dispara, e GetTriggerEventId() devolve o
  -- evento registrado. Sem isso o mapa cai no ramo errado de gatilho de morte (Trig_UI_Task cria a
  -- interface de tarefa a cada morte) e o mock inventa um vazamento que o jogo nao tem.
  local pe = __trigger_event
  u.life = 0
  -- [F5:perf] fim
  for _, t in ipairs(gat) do
    for _, ev in ipairs(t.events) do
      if (ev[1] == "playerunit" or ev[1] == "unit") and ev[2] == EVENT_PLAYER_UNIT_DEATH or ev[2] == EVENT_UNIT_DEATH then
        __trigger_event = ev[2]                                             -- [F5:perf]
        if TriggerEvaluate(t) then TriggerExecute(t) end
        fired = fired + 1
        break
      end
    end
  end
  -- [C2] (frente C2, fase 2) a morte de WIDGET: o gatilho registrado com `TriggerRegisterDeathEvent(t, u)` para ESTA
  -- unidade (o `unit_on_life_vanish` do mapa, que notifica o `on_life_vanish` -- a explosao do `烧伤`, a do `静电爆发`).
  -- O motor o dispara na morte; o mock nao disparava. SOB PEDIDO (`__MOCK_MORTE_WIDGET = true` na cena), para nao
  -- mudar a saida das sondas das outras frentes no meio da rodada.
  if __MOCK_MORTE_WIDGET then
    for _, t in ipairs(gat) do
      for _, ev in ipairs(t.events) do
        if ev[1] == "death" and ev[2] == u then
          __trigger_event = EVENT_WIDGET_DEATH
          if TriggerEvaluate(t) then TriggerExecute(t) end
          fired = fired + 1
          break
        end
      end
    end
  end
  __trigger_event = pe                                                      -- [F5:perf]
  __mock_decay_add(u)
  __trigger_unit, __killing_unit, __trigger_player = pu, pk, pp
  return fired
end
-- [R1F2:astrologer2] inicio: RENASCIMENTO DE HEROI.
-- O mock nao tinha ReviveHero (caia no stub do common.j, que so devolve false) nem os eventos
-- EVENT_PLAYER_HERO_REVIVE_START/FINISH -- e o relato do tema e "a F some da barra DEPOIS DE
-- RENASCER". Sem isso nao havia como rodar o cenario nem provar o conserto.
-- O mapa revive por ReviveHero (war3map.j:46075/46235/46237/46240).
function ReviveHero(u, x, y, eyecandy)
  if type(u) ~= "table" or (u.typeid or 0) == 0 then return false end
  if UnitAlive(u) then return false end
  u.x, u.y = x or u.x, y or u.y
  __mock_unit_event(u, EVENT_PLAYER_HERO_REVIVE_START)
  u.life = u.maxlife or 1.0
  u.__decay = nil
  __mock_unit_event(u, EVENT_PLAYER_HERO_REVIVE_FINISH)
  return true
end
function ReviveHeroLoc(u, l, eyecandy)
  return ReviveHero(u, l and l.x or 0.0, l and l.y or 0.0, eyecandy)
end
-- [R1F2:astrologer2] fim
function GetTriggerPlayer() return __trigger_player or Player(0) end
function TriggerEvaluate(t)
  if not t or not t.enabled then return false end
  local prev = __trigger __trigger = t
  local r = true
  for _, c in ipairs(t.conds) do
    if c.fn then M.nasc = M.nasc + 1 local ok, v = pcall(c.fn) if not ok then __logerr("cond: " .. tostring(v)) v = false end if not v then r = false break end end
  end
  __trigger = prev
  return r
end
function TriggerExecute(t)
  if not t then return end
  local prev = __trigger __trigger = t
  for _, a in ipairs(t.actions) do M.nasc = M.nasc + 1 local ok, e = __wd_call(a) if not ok then __logerr("action: " .. tostring(e)) end end
  __trigger = prev
end
function TriggerExecuteWait(t) TriggerExecute(t) end
function TriggerSyncStart() end
function TriggerSyncReady() end
function TriggerWaitForSound(s, o) end
function TriggerSleepAction(s) end
function PolledWait(s) end
function __mock_fire(t, unit, player)
  if not t then return end
  local pu, pp = __trigger_unit, __trigger_player
  __trigger_unit, __trigger_player = unit, player
  if TriggerEvaluate(t) then TriggerExecute(t) end
  __trigger_unit, __trigger_player = pu, pp
end
local function reg(t, kind, arg, filtro)
  if t then
    t.events[#t.events + 1] = { kind, arg, filtro } M.trig_events = M.trig_events or {} M.trig_events[t] = true
    -- [F5:dmgaudit] indice dos gatilhos de evento de dano (o mapa registra o mesmo gatilho para cada unidade)
    if (kind == "unit" or kind == "playerunit") and (arg == EVENT_UNIT_DAMAGING or arg == EVENT_UNIT_DAMAGED
        or arg == EVENT_PLAYER_UNIT_DAMAGING or arg == EVENT_PLAYER_UNIT_DAMAGED) then
      local k = (arg == EVENT_UNIT_DAMAGING or arg == EVENT_PLAYER_UNIT_DAMAGING) and EVENT_UNIT_DAMAGING or EVENT_UNIT_DAMAGED
      M.dmg_trigs[k] = M.dmg_trigs[k] or {}
      M.dmg_trigs[k][t] = true
    end
    -- [F5:dmgaudit] fim
  end
  return newh("event")
end
-- [F5:perf] o motor emite a ordem "undefend" (852056) para a unidade removida; e assim que o indexador do
-- framework (unit.unitindex) percebe a remocao, pelo FILTRO do evento EVENT_PLAYER_UNIT_ISSUED_ORDER.
-- Sem isso o mock nunca desindexa unidade e o framework parece vazar (u so cresce), o que o jogo real nao faz.
__mock_order_id = 0
function __mock_unit_removed(u)
  if not u or not M.trig_events then return end
  local gat = {} for t in pairs(M.trig_events) do gat[#gat + 1] = t end
  table.sort(gat, function(x, y) return x.__seq < y.__seq end)
  local pu, pf, po, pp, po2 = __trigger_unit, __filter_unit, __mock_order_id, __trigger_player, __ordem_id
  __trigger_unit, __filter_unit, __mock_order_id, __trigger_player, __ordem_id = u, u, 852056, u.owner, 852056
  for _, t in ipairs(gat) do
    for _, ev in ipairs(t.events) do
      if ev[1] == "playerunit" and ev[2] == EVENT_PLAYER_UNIT_ISSUED_ORDER then
        local passa = true
        local f = ev[3]
        if f and f.fn then M.nasc = M.nasc + 1 local ok, v = pcall(f.fn) if not ok then __logerr("order filter: " .. tostring(v)) end passa = (v ~= false and v ~= nil) end
        if passa and TriggerEvaluate(t) then TriggerExecute(t) end
        break
      end
    end
  end
  __trigger_unit, __filter_unit, __mock_order_id, __trigger_player, __ordem_id = pu, pf, po, pp, po2
end
-- cadaver: o motor remove a unidade morta (nao heroi) depois do tempo de decomposicao (~88 s)
M.decay = {}
function __mock_decay_tick()
  local q = M.decay
  if #q == 0 or q[1][2] > M.now then return end
  local i = 1
  while i <= #q and q[i][2] <= M.now do
    local u = q[i][1]
    if u.typeid ~= 0 and (u.life or 0) <= 0 then RemoveUnit(u) end
    i = i + 1
  end
  local resto = {}
  for k = i, #q do resto[#resto + 1] = q[k] end
  M.decay = resto
end
function __mock_decay_add(u) if u and not u.hero then M.decay[#M.decay + 1] = { u, M.now + 88.0 } end end
-- [F5:perf] fim
-- [F5:repick] evento generico de unidade (aprender skill etc.), com a skill aprendida no contexto
function __mock_unit_event(u, evid, extra)
  if u == nil or evid == nil then return 0 end
  local fired = 0
  local pu, pp, pe = __trigger_unit, __trigger_player, __trigger_event
  local ps, psl = __learned_skill, __learned_skill_level
  __trigger_unit, __trigger_player, __trigger_event = u, u.owner, evid
  if extra then
    __learned_skill = extra.skill or 0
    __learned_skill_level = extra.skilllevel or 0
  end
  local gat = {} for t in pairs(M.trig_events or {}) do gat[#gat + 1] = t end
  table.sort(gat, function(x, y) return x.__seq < y.__seq end)
  for _, t in ipairs(gat) do
    for _, ev in ipairs(t.events) do
      if (ev[1] == "playerunit" or ev[1] == "unit") and ev[2] == evid then
        if TriggerEvaluate(t) then TriggerExecute(t) end
        fired = fired + 1
        break
      end
    end
  end
  __trigger_unit, __trigger_player, __trigger_event = pu, pp, pe
  __learned_skill, __learned_skill_level = ps, psl
  return fired
end
-- [F5:repick] fim
__trigger_event = nil
-- [R1F2:aspd2] contexto do evento de ataque do motor (EVENT_PLAYER_UNIT_ATTACKED): sem ele
-- GetAttacker caia no stub automatico de common.j, que devolve um handle novo a cada chamada, e o
-- cronometro de ataques do -aspd nunca via golpe nenhum
__attacker = nil
function GetAttacker() return __attacker end
function GetTriggerEventId() return __trigger_event end
function TriggerRegisterTimerEvent(t, timeout, periodic)
  local tm = CreateTimer() TimerStart(tm, timeout, periodic, function() local pe = __trigger_event __trigger_event = EVENT_GAME_TIMER_EXPIRED __mock_fire(t) __trigger_event = pe end) return reg(t, "timer", tm)
end
-- [R1F2:aspd2] o evento de "temporizador expirou" nao pode morar em tm.func: TimerStart REESCREVE
-- tm.func, e o sistema de buff do mapa faz exatamente isso (registra o evento no temporizador e so
-- depois chama StartTimerBJ, que passa callback nula). Com o embrulho antigo nenhum buff com duracao
-- chegava a acabar no simulador. Agora a lista de gatilhos fica ao lado da callback e __mock_advance
-- dispara as duas, na mesma ordem de antes (callback primeiro, gatilhos depois).
function TriggerRegisterTimerExpireEvent(t, tm)
  if tm then tm.expira = tm.expira or {} tm.expira[#tm.expira + 1] = t end
  return reg(t, "timerexpire", tm)
end
function TriggerRegisterPlayerUnitEvent(t, p, ev, f) return reg(t, "playerunit", ev, f) end
function TriggerRegisterUnitEvent(t, u, ev) return reg(t, "unit", ev) end
function TriggerRegisterPlayerEvent(t, p, ev) return reg(t, "player", ev) end
-- [R1F1:comandos] o 4o parametro (casamento EXATO) passa a ser guardado: sem ele o simulador
-- tratava todo registro de chat como prefixo, e "-skills" respondia a um registro de "-skill".
function TriggerRegisterPlayerChatEvent(t, p, s, e) return reg(t, "chat", s, e == true) end
function TriggerRegisterEnterRegion(t, r, f) M.enter_triggers = M.enter_triggers or {} M.enter_triggers[#M.enter_triggers + 1] = { t, f } return reg(t, "enter", r) end
function TriggerRegisterLeaveRegion(t, r, f) return reg(t, "leave", r) end
function TriggerRegisterGameEvent(t, e) return reg(t, "game", e) end
function TriggerRegisterVariableEvent(t, v, o, l) return reg(t, "var", v) end
function TriggerRegisterDialogEvent(t, d) return reg(t, "dialog", d) end
function TriggerRegisterDialogButtonEvent(t, b) return reg(t, "button", b) end
function TriggerRegisterPlayerAllianceChange(t, p, a) return reg(t, "ally", a) end
function TriggerRegisterPlayerStateEvent(t, p, s, o, l) return reg(t, "pstate", s) end
function TriggerRegisterUnitStateEvent(t, u, s, o, l) return reg(t, "ustate", s) end
function TriggerRegisterUnitInRange(t, u, r, f) return reg(t, "range", r) end
function TriggerRegisterDeathEvent(t, w) return reg(t, "death", w) end
function TriggerRegisterFilterUnitEvent(t, u, e, f) return reg(t, "filterunit", e) end
function TriggerRegisterTrackableHitEvent(t, tr) return reg(t, "hit", tr) end
function TriggerRegisterTrackableTrackEvent(t, tr) return reg(t, "track", tr) end
function TriggerRegisterGameStateEvent(t, s, o, l) return reg(t, "gstate", s) end
function TriggerRegisterUpgradeCommandEvent(t, id) return reg(t, "upg", id) end
function TriggerRegisterCommandEvent(t, id, o) return reg(t, "cmd", id) end
-- [F5:itemtip] o quadro fica guardado no evento ({kind, evento, quadro}) para a sonda achar o gatilho
function BlzTriggerRegisterFrameEvent(t, f, e) local r = reg(t, "frame", e) if t and t.events[#t.events] then t.events[#t.events][3] = f end return r end
function BlzTriggerRegisterPlayerSyncEvent(t, p, prefix, s) M.sync_triggers = M.sync_triggers or {} M.sync_triggers[prefix] = M.sync_triggers[prefix] or {} local lst = M.sync_triggers[prefix] for _, x in ipairs(lst) do if x == t then return reg(t, "sync", prefix) end end table.insert(lst, t) return reg(t, "sync", prefix) end
function BlzTriggerRegisterPlayerKeyEvent(t, p, k, m, d) return reg(t, "key", k) end
-- [F5:qol] tecla no simulador
-- ConvertOsKeyType devolvia um handle NOVO a cada chamada (stub de common.j), entao o oskeytype
-- guardado no registro do evento nunca era igual ao da tecla apertada e nao havia como disparar
-- uma tecla no mock. No motor o oskeytype e constante por codigo: aqui tambem.
__oskey = {}
function ConvertOsKeyType(i)
  local k = math.tointeger(i) or i
  local h = __oskey[k]
  if h == nil then h = newh("oskeytype") h.oskey = k __oskey[k] = h end
  return h
end
-- BlzIsLocalClientActive: o stub de common.j devolvia false (retorno padrao de boolean) e com isso
-- DzIsWindowActive() era falso no mock, o que desligava TODO callback de tecla do mapa (a tecla ~
-- do mapa inclusive). A janela do cliente simulado esta ativa.
function BlzIsLocalClientActive() return true end
__tecla_atual = nil
function BlzGetTriggerPlayerKey() return __tecla_atual end
function BlzGetTriggerPlayerKeyModifiers() return 0 end
function BlzGetTriggerPlayerIsKeyDown() return true end
--- Aperta uma tecla (codigo de tecla virtual, igual ao oskeytype) para o jogador `p`.
function __mock_key(key, p)
  local alvo = ConvertOsKeyType(key)
  local pp, pe, pk = __trigger_player, __trigger_event, __tecla_atual
  __trigger_player = p or Player(0)
  __tecla_atual = alvo
  local gat = {} for t in pairs(M.trig_events or {}) do gat[#gat + 1] = t end
  table.sort(gat, function(x, y) return x.__h < y.__h end)
  local n = 0
  for _, t in ipairs(gat) do
    for _, ev in ipairs(t.events) do
      if ev[1] == "key" and ev[2] == alvo then
        __mock_fire(t, nil, __trigger_player)
        n = n + 1
        break
      end
    end
  end
  __trigger_player, __trigger_event, __tecla_atual = pp, pe, pk
  if __ds_trace then __ds_trace[#__ds_trace + 1] = "@tecla " .. tostring(key) .. " por " .. tostring(p and p.id) end
  return n
end
-- pings do minimapa: o mock conta para a sonda conferir cor, posicao e quantidade
M.pings = {}
function PingMinimapEx(x, y, dur, r, g, b, extra)
  M.pings[#M.pings + 1] = { x = x, y = y, dur = dur, r = r, g = g, b = b }
end
function PingMinimap(x, y, dur) PingMinimapEx(x, y, dur, 255, 0, 0, false) end
-- [/F5:qol]
__sync_data, __sync_prefix = "", ""
M.sync_queue = {}
function BlzSendSyncData(prefix, data)
  if #data > 255 then __logerr("BlzSendSyncData: dados com " .. #data .. " bytes (" .. prefix .. ")") end
  M.sync_queue[#M.sync_queue + 1] = { prefix, data }
  return true
end
function __mock_deliver_sync()
  local q = M.sync_queue
  if #q == 0 then return end
  M.sync_queue = {}
  for _, item in ipairs(q) do
    local prefix, data = item[1], item[2]
    local ts = M.sync_triggers and M.sync_triggers[prefix]
    if ts then
      local pd, pp = __sync_data, __sync_prefix
      __sync_data, __sync_prefix = data, prefix
      -- [28/09/2026] o remetente e' o jogador LOCAL da maquina simulada (era sempre o Player(0): no mapa cujo slot 0
      -- e' computador -- o dragonball, humanos nos slots 1..10 --, o receptor gravava o dado no indice errado)
      for _, t in ipairs(ts) do __mock_fire(t, nil, Player(__MOCK_LOCAL or 0)) end
      __sync_data, __sync_prefix = pd, pp
    end
  end
end
function BlzGetTriggerSyncData() return __sync_data end
function BlzGetTriggerSyncPrefix() return __sync_prefix end

-- ExecuteFunc
function ExecuteFunc(name) local f = _G[name] if type(f) == "function" then M.nasc = M.nasc + 1 local ok, e = __wd_call(f) if not ok then __logerr("ExecuteFunc " .. name .. ": " .. tostring(e)) end end end

-- unidades / grupos / forcas
local NEUTRAL = 24
function CreateUnit(p, id, x, y, face)
  local sid = string.pack(">I4", (id or 0) & 0xFFFFFFFF)
  -- [F5:repick] heroi nasce com 1 ponto de skill, como no motor (o mapa subtrai esse 1 na criacao)
  local u = newh("unit", { owner = p, typeid = id, x = x, y = y, face = face, abil = {}, life = 100.0, mana = 100.0, level = 1, str = 10, agi = 10, int = 10, hero = (sid:sub(1, 1):match("%u") ~= nil), xp = 0, points = ((sid:sub(1, 1):match("%u") ~= nil) and 1 or 0) })
  -- [F5:aspd] inicio: intervalo de ataque (cool1 do SLK) e bonus nativo de velocidade
  do
    local rec = __slk_raw and __slk_raw.unit and __slk_raw.unit[sid]
    u.cool = rec and tonumber(rec.cool1) or 1.5
    u.aspd_bonus = 0.0
  end
  -- [F5:aspd] fim
  -- [F5:priest] no cenario --priest-e a unidade dummy ganha o Locust do SLK (abillist com Aloc): e o que
  -- faz o runtime pendurar o modelo como efeito (DzSetUnitModel) e a varredura de modelos correr.
  -- [F6:elementalist] o Locust da ficha do objeto vale SEMPRE, nao so no cenario --priest-e: e ele que
  -- faz o runtime pendurar o modelo como efeito quando nenhum tipo de unidade usa aquele arquivo
  -- (DzSetUnitModel). Sem isso o simulador nunca exercitava esse caminho -- as orbes do Elementalist e
  -- as bolas do Mago do Raio saiam sem modelo nenhum no mock e a medicao nao via o elo.
  do
    local rec = __slk_raw and __slk_raw.unit and __slk_raw.unit[sid]
    if rec and rec.abillist and string.find(rec.abillist, "Aloc", 1, true) then u.abil[1097625443] = 1 end
  end
  -- [F6:elementalist] fim
  -- [F5:dmgaudit] armadura da ficha do objeto: e ela que o motor usa para mitigar o dano depois
  -- do evento DAMAGING (unitbalance.slk, coluna def). Sem isto todo alvo do mock tem armadura 0.
  if __slk_get then
    local d = tonumber(__slk_get("unit", sid, "def") or "")
    if d then u.armor = d + 0.0 end
    -- [R1F2:dpsmeter] classificacao da ficha (coluna `type`: "giant", "undead", "mechanical"...).
    -- E ela que responde IsUnitType(u, UNIT_TYPE_GIANT), e o medidor de dano por jogador
    -- (war3map.j:40319-40335) SO conta dano em alvo GIANT: sem isto o acumulador do painel nunca
    -- rodava no simulador.
    u.classif = __slk_get("unit", sid, "type") or ""
  end
  M.units[u] = true
  if M.enter_triggers then
    for _, e in ipairs(M.enter_triggers) do
      local t, f = e[1], e[2]
      local pu = __filter_unit __filter_unit = u
      local pass = true
      if f and f.fn then local ok, v = pcall(f.fn) if not ok then __logerr("enter filter: " .. tostring(v)) end pass = v ~= false end
      __filter_unit = pu
      if pass then __mock_fire(t, u, p) end
    end
  end
  return u
end
CreateUnitByName = function(p, name, x, y, face) return CreateUnit(p, 1748908148, x, y, face) end
function CreateUnitAtLoc(p, id, l, f) return CreateUnit(p, id, l and l.x or 0, l and l.y or 0, f) end
function RemoveUnit(u) if u and u.typeid ~= 0 then M.units[u] = nil u.typeid = 0 u.abil = {} __mock_unit_removed(u) end end
function KillUnit(u) if u then u.life = 0 __mock_decay_add(u) end end
function ShowUnit(u, f) end
function GetUnitTypeId(u) return u and u.typeid or 0 end
function GetOwningPlayer(u) return u and u.owner or nil end
function GetUnitX(u) return u and u.x or 0.0 end
function GetUnitY(u) return u and u.y or 0.0 end
function SetUnitX(u, x) if u then u.x = x end end
function SetUnitY(u, y) if u then u.y = y end end
function SetUnitPosition(u, x, y) if u then u.x = x u.y = y end end
function SetUnitPositionLoc(u, l) if u and l then u.x = l.x u.y = l.y end end
-- [F5:herocw] no motor GetUnitLoc e nativa e cria o ponto direto; passar por Location fazia o mock
-- segurar o handle pelo caminho da secao 40 e esconder o defeito (o mock era mais simples que o motor).
function GetUnitLoc(u) return newh("location", { x = GetUnitX(u), y = GetUnitY(u) }) end
function GetUnitState(u, s)
  if not u then return 0.0 end
  if s == UNIT_STATE_LIFE then return u.life or 0.0 end
  if s == UNIT_STATE_MAX_LIFE then return u.maxlife or u.life or 0.0 end
  if s == UNIT_STATE_MANA then return u.mana or 0.0 end
  return u.maxmana or u.mana or 0.0
end
-- como no motor de verdade: escrever MAX_LIFE ou MAX_MANA aqui nao faz nada
function SetUnitState(u, s, v)
  if not u then return end
  if s == UNIT_STATE_LIFE then u.life = v
  elseif s == UNIT_STATE_MANA then u.mana = v end
end
function BlzSetUnitMaxHP(u, v) if u then u.maxlife = v + 0.0 if (u.life or 0) > v then u.life = v + 0.0 end end end
function BlzGetUnitMaxHP(u) return u and math.floor(u.maxlife or u.life or 0) or 0 end
function BlzSetUnitMaxMana(u, v) if u then u.maxmana = v + 0.0 if (u.mana or 0) > v then u.mana = v + 0.0 end end end
function BlzGetUnitMaxMana(u) return u and math.floor(u.maxmana or u.mana or 0) or 0 end
function GetWidgetLife(w) return w and w.life or 0.0 end
-- [F5:perf] UnitAlive (nativa do 3.0 usada pelas skills): o stub generico devolvia false para tudo
function UnitAlive(u) return u ~= nil and (u.typeid or 0) ~= 0 and (u.life or 0.0) > 0.405 end
-- [F5:perf] fim
function SetWidgetLife(w, v) if w then w.life = v end end
function GetUnitFlyHeight(u) return 0.0 end
function GetUnitDefaultFlyHeight(u) return 0.0 end
function SetUnitFlyHeight(u, h, r) end
function GetUnitFacing(u) return u and u.face or 0.0 end
function SetUnitFacing(u, f) if u then u.face = f end end
function GetUnitMoveSpeed(u) return 270.0 end
function GetUnitDefaultMoveSpeed(u) return 270.0 end
function SetUnitMoveSpeed(u, s) end
-- [F5:repick] esta redefinicao (mais abaixo no prelude) e a que vale e apagava a versao que le o
-- SLK. Agora: heroi -> nivel do heroi (como no motor); resto -> coluna do SLK do tipo de unidade.
function GetUnitLevel(u)
  if not u then return 0 end
  if u.hero then return u.level or 1 end
  local rec = __slk_raw.unit[string.pack(">I4", (u.typeid or 0) & 0xFFFFFFFF)]
  return rec and tonumber(rec.level) or (u.level or 1)
end
-- [F5:repick] fim
function GetHeroLevel(u) return u and u.level or 0 end
function SetHeroLevel(u, l, s) if u then u.level = l end end
-- [4.o teste da R1] MOTOR FIEL: com `includeBonuses`, o motor soma ao atributo o verde das habilidades de bonus
-- (os campos Istr/Iagi/Iint das `Aamk`/`AIab`...: a `ASAA` do motor de atributos). Antes o simulador nunca
-- somava, e a conta da D do Swordsman (`AGI - parcela do "主属性"`) dava negativo e virava o principal a cada
-- segundo -- o mesmo que o jogo fazia com o verde de atributo quebrado (T4-2).
function __mock_verde(u, campo)
  local t = 0
  if not u or not u.abilh or not campo then return 0 end
  for id, a in pairs(u.abilh) do
    if u.abil[id] and a.fields and type(a.fields[campo]) == "number" then t = t + a.fields[campo] end
  end
  return t
end
function GetHeroStr(u, b) if not u then return 0 end return (u.str or 0) + (b and __mock_verde(u, ABILITY_ILF_STRENGTH_BONUS_ISTR) or 0) end
function GetHeroAgi(u, b) if not u then return 0 end return (u.agi or 0) + (b and __mock_verde(u, ABILITY_ILF_AGILITY_BONUS) or 0) end
function GetHeroInt(u, b) if not u then return 0 end return (u.int or 0) + (b and __mock_verde(u, ABILITY_ILF_INTELLIGENCE_BONUS) or 0) end
function SetHeroStr(u, v, p) if u then u.str = v end end
function SetHeroAgi(u, v, p) if u then u.agi = v end end
function SetHeroInt(u, v, p) if u then u.int = v end end
-- [F5:repick] havia um segundo "function GetHeroXP(u) return 0 end" aqui que apagava o de cima:
-- o XP do heroi lido pelo mapa era sempre 0 e a carga de perfil nunca subia de nivel no mock.
-- [F5:repick] pontos de skill, aprendizado e disponibilidade de habilidade por jogador.
-- O motor recusa SelectHeroSkill sem ponto, no nivel maximo da habilidade e quando ela foi
-- desabilitada para o dono (SetPlayerAbilityAvailable false). O mock nao tinha nada disso: os
-- 45 SelectHeroSkill da carga de perfil nao faziam nada e o defeito do -repick ficava invisivel.
__abil_niveis = {}
__abil_bloqueada = {}
__learned_skill = 0
__learned_skill_level = 0
function __mock_niveis_abil(id)
  local n = __abil_niveis[id]
  if n == nil then
    local rec = __slk_raw.ability and __slk_raw.ability[string.pack(">I4", (id or 0) & 0xFFFFFFFF)]
    n = (rec and tonumber(rec.levels)) or 1
    __abil_niveis[id] = n
  end
  return n
end
function __mock_abil_bloqueada(p, id)
  local t = __abil_bloqueada[p]
  return t ~= nil and t[id] == true
end
function GetLearnedSkill() return __learned_skill end
function GetLearnedSkillLevel() return __learned_skill_level end
function GetHeroSkillPoints(u) return (u and u.points) or 0 end
function UnitModifySkillPoints(u, n)
  if u == nil then return false end
  u.points = math.max(0, (u.points or 0) + (n or 0))
  return true
end
function ModifyHeroSkillPoints(u, method, n)
  if u == nil then return false end
  n = n or 0
  if method == bj_MODIFYMETHOD_SUB then n = -n
  elseif method == bj_MODIFYMETHOD_SET then u.points = math.max(0, n) return true end
  u.points = math.max(0, (u.points or 0) + n)
  return true
end
function SelectHeroSkill(u, id)
  if u == nil or id == nil then return end
  if (u.points or 0) <= 0 then return end
  if __mock_abil_bloqueada(u.owner, id) then return end
  local nivel = u.abil[id] or 0
  if nivel >= __mock_niveis_abil(id) then return end
  u.abil[id] = nivel + 1
  u.points = u.points - 1
  __mock_unit_event(u, EVENT_PLAYER_HERO_SKILL, { skill = id, skilllevel = nivel + 1 })
end
-- [F5:repick] fim
-- [R1F2:dpsmeter] UNIT_TYPE_GIANT sai da coluna `type` da ficha do objeto (ver CreateUnit)
function IsUnitType(u, t) if not u then return false end if t == UNIT_TYPE_DEAD then return u.life <= 0 end if t == UNIT_TYPE_HERO then return u.hero == true end if t == UNIT_TYPE_GIANT then return u.classif ~= nil and string.find(u.classif, "giant", 1, true) ~= nil end return false end
function IsUnitIllusion(u) return false end
function IsUnitVisible(u, p) return true end
-- [R1F1:anticheat] inicio: nevoa de guerra simplificada.
-- O stub devolvia SEMPRE true, e com isso a sonda do ISeeDeadPeople nunca podia ser exercitada (nem
-- para acusar nem para calar). Modelo: o ponto e visivel quando alguma unidade do jogador (ou de um
-- aliado, que neste mapa sao todos os slots 0..7, SetPlayerAllianceStateVisionBJ) esta a menos de
-- __MOCK_VISAO do ponto -- ou quando o jogador esta com o codigo de revelar ligado.
__MOCK_VISAO = 1800.0
function IsVisibleToPlayer(x, y, p)
  if p == nil then return true end
  if __mock_cheat_on and __mock_cheat_on(p, "vision") then return true end
  local pid = p.id or 0
  for u in pairs(M.units) do
    if u.typeid ~= 0 and u.owner ~= nil then
      local oid = u.owner.id or 0
      if oid == pid or (pid < 8 and oid < 8) then
        local dx, dy = (u.x or 0) - x, (u.y or 0) - y
        if dx * dx + dy * dy <= __MOCK_VISAO * __MOCK_VISAO then return true end
      end
    end
  end
  return false
end
-- [R1F1:anticheat] fim
-- [R1F1:musketeer2] inicio ---------------------------------------------------------------
-- IsUnitInRangeXY devolvia SEMPRE true: o mock era mais simples que o motor e todo filtro fino
-- de area do mapa virava no-op. O idioma do mapa e "GroupEnumUnitsInRange(g, x, y, R + 75, null)"
-- (rede larga) seguido de "IsUnitInRangeXY(u, x, y, R)" (peneira), entao com o no-op o alcance
-- medido saia 75 unidades maior que o real em TODA skill de area -- e o tema da W do Musketeer e
-- justamente medir alcance. O motor compara a distancia descontando o tamanho de colisao do alvo;
-- o mock nao modela colisao, entao aqui e a distancia pura (medida conservadora, nunca maior que
-- a do motor).
function IsUnitInRangeXY(u, x, y, r)
  if u == nil or x == nil or y == nil or r == nil then return false end
  local dx, dy = u.x - x, u.y - y
  return (dx * dx + dy * dy) <= (r * r)
end
-- [R1F1:musketeer2] fim ------------------------------------------------------------------
function IsUnitInGroup(u, g) return g and g.set and g.set[u] == true end
function IsUnitSelected(u, p) return false end
-- [F5:itemtip] o stub automatico devolvia false e DzIsWindowActive() barrava a dica do inventario nativo
-- (P61MatchNativeInventorySlot); em jogo a janela de quem mexe o mouse esta ativa
function IsUnitHidden(u) return false end
-- [F5:castleboss] pausa e invulnerabilidade modeladas: no motor existe UM SO estado de pausa
-- por unidade (PauseUnit escreve nele, IsUnitPaused le), e SetUnitInvulnerable liga/desliga a
-- habilidade 'Avul' que os filtros do mapa (GS_IsUnitAliveBJ) consultam. Sem isso o mock nao
-- enxerga duas contabilidades de pausa brigando pelo mesmo bit do motor.
function IsUnitPaused(u) return u ~= nil and u.pausado == true end
function SetUnitInvulnerable(u, b)
  if not u then return end
  u.invul = (b == true)
  if u.invul then u.abil[1098282348] = 1 else u.abil[1098282348] = nil end
end
-- [F5:castleboss]
function IsUnitInvisible(u, p) return false end
function IsUnitFogged(u, p) return false end
function IsUnitMasked(u, p) return false end
function IsUnitDetected(u, p) return false end
function IsUnitIdType(id, t) return false end
function IsUnitRace(u, r) return false end
-- [F5:aspd] inicio: como no motor, habilidade que nao existe na tabela de dados nao entra (o mock aceitava
-- qualquer codigo, e foi assim que o 'Adkx' da F4 "funcionava" aqui); habilidade de velocidade de ataque
-- (classe AIas, campo Isx1 = DataA1) soma o bonus nativo da unidade, que o motor prende em -80%..+400%.
-- [R1F2:aspd2] a soma do bonus nativo saiu daqui para __mock_aspd_engine, que ve tambem a ficha do tipo,
-- os itens do inventario e as auras AOae dos aliados por perto (era so isto que faltava no simulador).
-- Nao se modela se Inc/DecUnitAbilityLevel reaplica um campo escrito por BlzSetAbilityRealLevelField:
-- isso nao foi medido no jogo, e a correcao do 0x51 nao depende disso.
__mock_abil_rejeitadas = {}
local function __mock_abil_rec(id)
  local tab = __slk_raw and __slk_raw.ability
  if tab == nil or next(tab) == nil then return nil, true end
  return tab[string.pack(">I4", (id or 0) & 0xFFFFFFFF)], false
end
-- [R1F2:morpheus2] inicio: a habilidade CHAOS (code 'Acha') do Reforged troca o TIPO da unidade
-- mantendo o handle -- e o unico mecanismo que faz no Reforged o que a Metamorfose do japi fazia no
-- 1.28 (YDWEUnitTransform). Sem isto o simulador nao consegue medir a transformacao de chefe: o
-- mock aceitava a habilidade e nao acontecia nada. O que o motor faz na troca e o que esta aqui:
-- tipo, lista de habilidades do tipo (abilList), vida/mana maximas, intervalo de ataque e armadura
-- passam a ser os do tipo NOVO; a vida e a mana atuais sao presas ao novo maximo.
local function __mock_abil_lista(sid)
  local rec = __slk_raw and __slk_raw.unit and __slk_raw.unit[sid]
  local s = rec and rec.abillist or ""
  local l = {}
  for c in string.gmatch(s or "", "[^,]+") do
    if #c == 4 then l[#l + 1] = string.unpack(">I4", c) end
  end
  return l
end
function __mock_chaos(u, alvo)
  if u == nil or alvo == nil or #alvo ~= 4 then return false end
  local novo = string.unpack(">I4", alvo)
  local velho = string.pack(">I4", (u.typeid or 0) & 0xFFFFFFFF)
  local rec = __slk_raw and __slk_raw.unit and __slk_raw.unit[alvo]
  if rec == nil then return false end
  for _, a in ipairs(__mock_abil_lista(velho)) do UnitRemoveAbility(u, a) end
  u.typeid = novo
  for _, a in ipairs(__mock_abil_lista(alvo)) do UnitAddAbility(u, a) end
  local hp = tonumber(rec.hp)
  if hp and hp > 0 then
    u.maxlife = hp + 0.0
    if (u.life or 0) > u.maxlife then u.life = u.maxlife end
  end
  local mn = tonumber(rec.manan)
  if mn and mn > 0 then
    u.maxmana = mn + 0.0
    if (u.mana or 0) > u.maxmana then u.mana = u.maxmana end
  end
  u.cool = tonumber(rec.cool1) or u.cool
  local d = tonumber(rec.def or "")
  if d then u.armor = d + 0.0 end
  return true
end
-- [R1F2:morpheus2] fim
function UnitAddAbility(u, id)
  if not u then return false end
  if u.abil[id] then return false end
  local rec, semtabela = __mock_abil_rec(id)
  if rec == nil and not semtabela then
    local sid = string.pack(">I4", (id or 0) & 0xFFFFFFFF)
    __mock_abil_rejeitadas[sid] = (__mock_abil_rejeitadas[sid] or 0) + 1
    return false
  end
  u.abil[id] = 1
  u.aspd_own_tick = nil   -- [R1F2:aspd2] o bonus do motor tem de ser refeito ainda neste tique
  -- [R1F2:morpheus2] Chaos: a unidade vira o tipo do campo UnitID1 no instante em que ganha a skill
  if rec and rec.code == "Acha" and rec.unitid1 then __mock_chaos(u, rec.unitid1) end
  return true
end
function UnitRemoveAbility(u, id)
  if not u or not u.abil[id] then return false end
  u.abil[id] = nil
  u.aspd_own_tick = nil   -- [R1F2:aspd2]
  return true
end
function BlzGetUnitAttackCooldown(u, w) if not u then return 0.0 end return (u.cool or 0.0) + 0.0 end
function BlzSetUnitAttackCooldown(u, v, w) if u then u.cool = (tonumber(v) or 0.0) + 0.0 end end
-- [R1F2:aspd2] inicio: a velocidade de ataque que o PROPRIO MOTOR aplica.
--
-- Ate a R1 F1 o simulador so somava o bonus de uma habilidade AIas passada por UnitAddAbility. O motor
-- de verdade aplica muito mais, e e por isso que o Battle Mage continuou rapido em jogo com o intervalo
-- escrito preso em 0,20 s. Aqui entram as tres fontes que este mapa usa:
--
--   1. a ficha do TIPO da unidade (abilList/heroAbilList do unitabilities.slk);
--   2. a ficha dos ITENS que estao no inventario (abilList do itemdata.slk);
--   3. AURAS (codigo AOae) de OUTRAS unidades aliadas dentro do alcance -- as quatro "Elf's Tear"
--      (S004/S005/S006/S007, buff B098) sao exatamente isso.
--
-- Regra do motor reproduzida: habilidades com o MESMO buff nao empilham (vale a maior), buffs
-- diferentes somam, e o total e preso em -80%..+400%. Para nao mudar o comportamento do simulador em
-- nada que nao seja velocidade de ataque, so as habilidades de codigo AIas/AOae/Absk entram por (1),
-- (2) e (3): o resto da abilList continua invisivel, como antes. Tudo com cache por tique do
-- simulador, para o custo nao aparecer nas medicoes dos outros temas.
__MOCK_ASPD_MOTOR = nil          -- id -> { chave, val = {por nivel}, maior, aura = alcance, buff }
__MOCK_ASPD_BUFFS = nil          -- id do buff -> maior valor de aura que o produz
__mock_aura_fontes = nil         -- { {u=, alcance=, buff=, val=} } recalculado uma vez por tique
__mock_aura_tick = nil

function __mock_aspd_tab()
  if __MOCK_ASPD_MOTOR ~= nil then return __MOCK_ASPD_MOTOR, __MOCK_ASPD_BUFFS end
  local t, b = {}, {}
  local raw = __slk_raw and __slk_raw.ability
  if raw == nil or next(raw) == nil then return t, b end   -- sem ficha ainda: monta na proxima chamada
  for sid, rec in pairs(raw) do
    local code = tostring(rec.code or "")
    local letra = nil
    if code == "AIas" or code == "AOae" then letra = "a" elseif code == "Absk" then letra = "b" end
    if letra ~= nil and #sid == 4 then
      local val, maior = {}, 0.0
      for lv = 1, 6 do
        local v = tonumber(rec["data" .. letra .. lv])
        if v ~= nil and v > 0 then val[lv] = v if v > maior then maior = v end end
      end
      if maior > 0 then
        local id = string.unpack(">I4", sid)
        local bid = rec.buffid1
        local chave = -id
        if bid ~= nil and #tostring(bid) == 4 then chave = string.unpack(">I4", tostring(bid)) end
        local alvos = tostring(rec.targs1 or "")
        local area = tonumber(rec.area1) or 0
        local aura = nil
        if code == "AOae" and area > 0
           and (string.find(alvos, "friend", 1, true) or string.find(alvos, "ally", 1, true)) then
          aura = area
          if (b[chave] or 0) < maior then b[chave] = maior end
        end
        t[id] = { chave = chave, val = val, maior = maior, aura = aura,
                  buff = (chave > 0) and chave or nil }
      end
    end
  end
  __MOCK_ASPD_MOTOR, __MOCK_ASPD_BUFFS = t, b
  return t, b
end

-- habilidades de velocidade que a unidade carrega: as proprias, as da ficha do TIPO e as dos ITENS
-- (cache por tique; o inventario e o tipo mudam raramente e o tique do mock e 0,03125 s)
function __mock_aspd_proprias(u)
  local tab = __mock_aspd_tab()
  if u.aspd_own ~= nil and u.aspd_own_tick == M.now then return u.aspd_own end
  local saida = {}
  for id, lv in pairs(u.abil or {}) do if tab[id] then saida[id] = lv or 1 end end
  local rec = __slk_raw and __slk_raw.unit and __slk_raw.unit[string.pack(">I4", (u.typeid or 0) & 0xFFFFFFFF)]
  local listas = rec and ((rec.abillist or "") .. "," .. (rec.heroabillist or "")) or ""
  for s = 0, 5 do
    local it = u.inv and u.inv[s]
    if it ~= nil and it.typeid ~= 0 and it.dono == u then
      local ir = __slk_raw and __slk_raw.item and __slk_raw.item[string.pack(">I4", it.typeid & 0xFFFFFFFF)]
      listas = listas .. "," .. tostring(ir and ir.abillist or "")
    end
  end
  for cod in string.gmatch(listas, "[^,]+") do
    cod = cod:match("^%s*(.-)%s*$")
    if #cod == 4 then
      local id = string.unpack(">I4", cod)
      if tab[id] and saida[id] == nil then saida[id] = 1 end
    end
  end
  u.aspd_own, u.aspd_own_tick = saida, M.now
  return saida
end

-- fontes de aura vivas no mapa, uma vez por tique (sao pouquissimas; sem elas o laco nem roda)
function __mock_aura_fontes_lista()
  if __mock_aura_tick == M.now and __mock_aura_fontes ~= nil then return __mock_aura_fontes end
  local tab = __mock_aspd_tab()
  local out = {}
  if next(tab) ~= nil then
    for s in pairs(M.units) do
      if s.typeid ~= 0 then
        for id in pairs(__mock_aspd_proprias(s)) do
          local e = tab[id]
          if e ~= nil and e.aura ~= nil and e.buff ~= nil then
            out[#out + 1] = { u = s, alcance = e.aura, buff = e.buff, val = e.maior }
          end
        end
      end
    end
  end
  __mock_aura_fontes, __mock_aura_tick = out, M.now
  return out
end

-- buffs de aura que alcancam a unidade (inclusive os dela mesma): e a marca que o motor deixa, e e
-- por ela que o runtime enxerga a aura de um aliado
function __mock_aura_buffs(u)
  if u.aura_tick == M.now and u.aura_buffs ~= nil then return u.aura_buffs end
  local out = {}
  for _, f in ipairs(__mock_aura_fontes_lista()) do
    local s = f.u
    local amigo = (s == u) or (s.owner == u.owner)
    if not amigo and s.owner ~= nil and u.owner ~= nil then
      amigo = (GetPlayerController(s.owner) == GetPlayerController(u.owner))
    end
    if amigo then
      local dx, dy = (s.x or 0) - (u.x or 0), (s.y or 0) - (u.y or 0)
      if dx * dx + dy * dy <= f.alcance * f.alcance and (out[f.buff] or 0) < f.val then
        out[f.buff] = f.val
      end
    end
  end
  u.aura_buffs, u.aura_tick = out, M.now
  return out
end

-- bonus total que o motor aplica na unidade, com a regra de buff do motor
function __mock_aspd_engine(u)
  if u == nil or u.typeid == 0 then return 0.0 end
  local tab = __mock_aspd_tab()
  local melhor = {}
  for id, lv in pairs(__mock_aspd_proprias(u)) do
    local e = tab[id]
    local v = e.val[lv] or e.maior
    if (melhor[e.chave] or 0) < v then melhor[e.chave] = v end
  end
  for b, v in pairs(__mock_aura_buffs(u)) do
    if (melhor[b] or 0) < v then melhor[b] = v end
  end
  local soma = (u.aspd_bonus or 0.0)
  for _, v in pairs(melhor) do soma = soma + v end
  return soma
end
-- intervalo real entre ataques como o motor calcula: intervalo / (1 + bonus), bonus preso em -80%..+400%
function __mock_attack_interval(u)
  if not u then return 0.0 end
  local f = 1.0 + __mock_aspd_engine(u)
  if f < 0.2 then f = 0.2 elseif f > 5.0 then f = 5.0 end
  return (u.cool or 0.0) / f
end
-- [F5:aspd] fim
-- Ataca `n` vezes de verdade, andando com o relogio do simulador o intervalo REAL de cada golpe (ele e
-- recalculado a cada golpe, entao uma mudanca no meio -- ulti que acaba, aura que chega -- aparece).
-- O evento de ataque do motor dispara em cada golpe, que e o que o -aspd mede.
function __mock_auto_ataca(u, alvo, n)
  local t = {}
  for _ = 1, (n or 10) do
    local iv = __mock_attack_interval(u)
    if iv <= 0 then break end
    __mock_advance(iv, iv)
    local pa = __attacker
    __attacker = u
    __mock_unit_event(alvo, EVENT_PLAYER_UNIT_ATTACKED)   -- e ele que o -aspd cronometra
    __attacker = pa
    __mock_damage(u, alvo, 1.0, true)
    t[#t + 1] = iv
  end
  return t
end
-- [R1F2:aspd2] fim
function GetUnitAbilityLevel(u, id)
  if not u then return 0 end
  local lv = u.abil[id]
  if lv then return lv end
  -- [R1F2:aspd2] habilidade de velocidade vinda da ficha do TIPO / de ITEM, e o buff de uma aura que
  -- alcanca a unidade: no motor as tres aparecem em GetUnitAbilityLevel, e e assim que o runtime ve.
  -- Dois lookups no caso comum (id que nao e nenhuma das duas coisas), que e o unico que importa.
  local tab, buffs = __mock_aspd_tab()
  if tab[id] ~= nil then
    if __mock_aspd_proprias(u)[id] ~= nil then return 1 end
  elseif buffs[id] ~= nil then
    if __mock_aura_buffs(u)[id] ~= nil then return 1 end
  end
  return 0
end
function SetUnitAbilityLevel(u, id, l) if u and u.abil[id] then u.abil[id] = l u.aspd_own_tick = nil end return l end  -- [R1F2:aspd2]
function IncUnitAbilityLevel(u, id) if u and u.abil[id] then u.abil[id] = u.abil[id] + 1 u.aspd_own_tick = nil return u.abil[id] end return 0 end  -- [R1F2:aspd2]
function DecUnitAbilityLevel(u, id) if u and u.abil[id] then u.abil[id] = u.abil[id] - 1 u.aspd_own_tick = nil return u.abil[id] end return 0 end  -- [R1F2:aspd2]
function UnitMakeAbilityPermanent(u, p, id) return true end
-- [F5:repick] a disponibilidade e POR JOGADOR e sobrevive ao heroi: e disso que o -repick sofre
function SetPlayerAbilityAvailable(p, id, a)
  if p == nil or id == nil then return end
  local t = __abil_bloqueada[p]
  if t == nil then t = {} __abil_bloqueada[p] = t end
  t[id] = (a == false) or nil
end
-- [F5:repick] fim
-- [R1F1:comandos] recarga de habilidade por unidade: implementacao unificada no bloco [R1F1:itemcast] (juncao)
function BlzGetUnitAbility(u, id) if not u or not u.abil[id] then return nil end u.abilh = u.abilh or {} local a = u.abilh[id] if not a then a = newh("ability", { id = id, fields = {} }) u.abilh[id] = a end return a end
function BlzSetAbilityIntegerLevelField(a, f, l, v) if a then a.fields[f] = v end return true end
function BlzSetAbilityRealLevelField(a, f, l, v) if a then a.fields[f] = v end return true end
-- [R1F2:astrologer2] inicio: campo de habilidade por nivel LE O DADO DO MAPA quando ninguem escreveu.
-- Os dois getters devolviam 0 para toda habilidade em que o mapa nao tivesse escrito antes. So que
-- o mapa LE esses campos para montar a propria contabilidade de recarga: Trig_AbilActions
-- (war3map.j:40636) faz "recarga real = YDWEGetUnitAbilityDataReal(u, skill, nivel, 105)", que cai em
-- BlzGetAbilityRealLevelField(ab, ABILITY_RLF_COOLDOWN, nivel-1). Com 0 ali, o mapa conclui "esta
-- skill nao tem recarga" e manda YDWESetUnitAbilityState(...,1,0.00) -- no simulador TODA skill de
-- heroi ficava sem recarga, e nao dava para medir o "-25%" do item I0J7 na W.
-- O motor repete o ultimo nivel definido quando o SLK tem menos colunas que niveis (a W tem 10
-- niveis e so Cool1..Cool6): a busca desce de nivel ate achar, como BlzGetAbilityCooldown ja fazia.
__ABIL_CAMPO_SLK = {
  [1633903726] = "cool",     -- 'acdn' ABILITY_RLF_COOLDOWN
  [1633902963] = "cast",     -- 'acas' ABILITY_RLF_CASTING_TIME
  [1633973618] = "dur",      -- 'adur' ABILITY_RLF_DURATION_NORMAL
  [1634231413] = "herodur",  -- 'ahdu' ABILITY_RLF_DURATION_HERO
  [1633776229] = "area",     -- 'aare' ABILITY_RLF_AREA_OF_EFFECT
  [1634885998] = "rng",      -- 'aran' ABILITY_RLF_CAST_RANGE
  [1634558835] = "cost",     -- 'amcs' ABILITY_ILF_MANA_COST
}
function __abil_campo_slk(a, f, l)
  if a == nil or a.id == nil then return nil end
  local nome = __ABIL_CAMPO_SLK[(type(f) == "table" and f.__h) or f]
  if nome == nil or __slk_get == nil then return nil end
  local n = (l or 0) + 1
  while n >= 1 do
    local v = __slk_get("ability", a.id, nome .. tostring(n))
    if v ~= nil and v ~= "" then return tonumber(v) end
    n = n - 1
  end
  return nil
end
function BlzGetAbilityIntegerLevelField(a, f, l)
  if a == nil then return 0 end
  if a.fields[f] ~= nil then return a.fields[f] end
  local v = __abil_campo_slk(a, f, l)
  return v and math.floor(v) or 0
end
function BlzGetAbilityRealLevelField(a, f, l)
  if a == nil then return 0.0 end
  if a.fields[f] ~= nil then return a.fields[f] end
  return __abil_campo_slk(a, f, l) or 0.0
end
-- [R1F2:astrologer2] fim
-- [F5:dmgaudit] inicio: evento de dano do motor no simulador
-- O stub antigo devolvia true sem fazer nada: nenhum gatilho de dano do mapa rodava aqui, e o pipeline
-- de dano (Trig_HurtFunc006A) ficava invisivel. Agora cada UnitDamageTarget:
--   (1) registra a chamada em __dmg_log com o valor que a skill PEDIU (antes de qualquer multiplicador),
--       o tipo de ataque/dano e a profundidade (dano nascido dentro de outro evento de dano = aninhado);
--   (2) com __dmg_pipeline ligado, dispara os gatilhos EVENT_UNIT_DAMAGING / EVENT_PLAYER_UNIT_DAMAGING
--       (o pipeline do mapa mexe no valor por BlzSetEventDamage), aplica a mitigacao do alvo
--       (t.__mit(ev) devolve o fator; sem ela, 1.0 = alvo sem armadura nem resistencia), dispara os
--       gatilhos DAMAGED com o valor liquido e desconta a vida -- a ordem do motor 1.31+/Reforged.
-- __dmg_pipeline fica desligado por padrao para nao mudar o comportamento dos outros testes.
__dmg_log = {}
__dmg_pipeline = false
__dmg_ev = nil
__dmg_depth = 0
M.dmg_trigs = {}
local function dmg_fire(evkind, ev)
  local gat = {}
  for t in pairs(M.dmg_trigs[evkind] or {}) do if t.enabled ~= false then gat[#gat + 1] = t end end
  table.sort(gat, function(x, y) return x.__h < y.__h end)
  local pe = __trigger_event
  __trigger_event = evkind
  for _, t in ipairs(gat) do __mock_fire(t, ev.tgt, ev.tgt.owner) end
  __trigger_event = pe
end
function UnitDamageTarget(u, t, d, a, r, at, dt, wt)
  if t == nil or t.typeid == 0 then return false end
  local rec = { src = u, tgt = t, amount = d, at = at, dt = dt, wt = wt, attack = (a and true or false),
                t = M.now, depth = __dmg_depth }
  __dmg_log[#__dmg_log + 1] = rec
  -- [R1F1:anticheat] inicio: invulnerabilidade e o codigo WhosYourDaddy.
  -- No motor a unidade invulneravel simplesmente nao perde vida, e o codigo whosyourdaddy faz duas
  -- coisas ao mesmo tempo: deixa as unidades do jogador invulneraveis E faz o dano delas matar de um
  -- golpe. O stub anterior ignorava as duas, entao o mock era mais permissivo que o motor.
  if t.invul or (__mock_cheat_on and __mock_cheat_on(t.owner, "god")) then
    rec.final, rec.liquido, rec.fator = 0.0, 0.0, 0.0
    return true
  end
  if u ~= nil and __mock_cheat_on and __mock_cheat_on(u.owner, "god") then
    rec.final, rec.liquido, rec.fator = d, t.life or 0.0, 1.0
    t.life = 0.0
    __mock_decay_add(t)
    return true
  end
  -- Unidade com Locust nunca entra no pipeline de dano do mapa (YDWEAnyUnitDamagedFilter so registra
  -- quem NAO tem 'Aloc'), entao o dano nela e sempre cru -- e o motor o aplica mesmo com o pipeline
  -- do mock desligado. Sem isto a sonda de dano do anti-cheat lia "invulneravel" num boneco sadio.
  if not __dmg_pipeline and t.abil and t.abil[1097625443] then
    local fator = __mock_mitigacao(t, at, dt)
    rec.fator, rec.final, rec.liquido = fator, d, d * fator
    rec.vida_antes = t.life
    t.life = (t.life or 0) - d * fator
    rec.vida_depois = t.life
    return true
  end
  -- [R1F1:anticheat] fim
  if not __dmg_pipeline then return true end
  local ev = { src = u, tgt = t, amount = d, at = at, dt = dt, wt = wt, attack = rec.attack }
  local pev = __dmg_ev
  __dmg_ev = ev
  __dmg_depth = __dmg_depth + 1
  dmg_fire(EVENT_UNIT_DAMAGING, ev)
  rec.final = ev.amount
  -- [F5:dmgaudit] mitigacao DEPOIS do evento DAMAGING, como o motor faz: tabela ataque x armadura
  -- (toda 1.00 neste mapa, war3mapMisc.txt) e valor de armadura do alvo com DefenseArmor=0.02.
  local fator = __mock_mitigacao(t, at, dt)
  rec.fator = fator
  ev.amount = ev.amount * fator
  dmg_fire(EVENT_UNIT_DAMAGED, ev)
  rec.liquido = ev.amount
  rec.vida_antes = t.life
  if ev.amount > 0 then t.life = (t.life or 0) - ev.amount end
  rec.vida_depois = t.life
  __dmg_depth = __dmg_depth - 1
  __dmg_ev = pev
  return true
end
-- [F5:dmgaudit] modelo de armadura do motor no simulador, independente do runtime do mapa
-- [R1F2:dpsmeter] o motor corta por armadura tambem o tipo de ataque "Spells" (ATTACK_TYPE_NORMAL).
-- So `DAMAGE_TYPE_UNIVERSAL` escapa do valor de armadura; o tipo de ATAQUE decide a tabela ataque x
-- armadura (`DamageBonus*` do war3mapMisc.txt, toda em 1.00 neste mapa), nao o corte pelo valor.
-- A prova esta no proprio mapa: `Trig_H05H_onInitFunc025Conditions` (war3map.j:100876-100878) da
-- `dano x 2` com ATTACK_TYPE_MAGIC no alvo principal e `dano x 1` com ATTACK_TYPE_NORMAL nos alvos
-- de respingo -- se "Spells" ignorasse armadura, o respingo bateria 20x mais forte que o alvo
-- principal num chefe de armadura 1000. `__MOCK_NORMAL_IGNORA_ARMADURA = true` volta a suposicao
-- da F5, para medir o "antes".
__MOCK_DEFESA = 0.02
__MOCK_NORMAL_IGNORA_ARMADURA = false
function __mock_mitigacao(t, at, dt)
  if t == nil then return 1.0 end
  if dt == DAMAGE_TYPE_UNIVERSAL then return 1.0 end
  if at == ATTACK_TYPE_NORMAL and __MOCK_NORMAL_IGNORA_ARMADURA then return 1.0 end
  local a = t.armor or 0.0
  if a >= 0.0 then return 1.0 / (1.0 + __MOCK_DEFESA * a) end
  return 2.0 - (1.0 - __MOCK_DEFESA) ^ (-a)
end
function BlzGetUnitArmor(u) if u == nil then return 0.0 end return u.armor or 0.0 end
function BlzSetUnitArmor(u, v) if u then u.armor = v + 0.0 end end
-- [F5:dmgaudit] fim

-- [R1F1:anticheat] inicio ========================================================================
-- Recarga de habilidade por unidade (BlzGet/SetUnitAbilityCooldownRemaining, nativas do 3.0). O
-- stub automatico devolvia 0 sempre, e com isso a sonda de recarga do anti-cheat nunca podia nem
-- acusar nem calar. Aqui a recarga anda com o relogio do simulador, como no motor.
-- (juncao R1F1) as nativas de recarga vivem no bloco [R1F1:itemcast], que consulta __mock_cheat_on(u.owner, "cooldown")

-- Emulacao dos codigos nativos do Warcraft III. Eles nao existem como nativa nenhuma: o motor os le
-- do chat e aplica direto no estado, sem passar por script. E exatamente isso que se reproduz aqui.
__mock_cheats = {}
function __mock_cheat_on(p, qual)
  if p == nil then return false end
  local t = __mock_cheats[p.id or -1]
  return t ~= nil and t[qual] == true
end
--- Liga um codigo para o jogador pid. `n` e o numero opcional (greedisgood 500 etc.).
function __mock_cheat(codigo, pid, n)
  local c = string.lower(tostring(codigo))
  local p = Player(pid or 0)
  local t = __mock_cheats[pid or 0]
  if t == nil then t = {} __mock_cheats[pid or 0] = t end
  n = tonumber(n) or 500
  if c == "whosyourdaddy" then
    t.god = true
    -- o codigo tambem deixa invulneravel tudo o que o jogador ja tem
    for u in pairs(M.units) do if u.owner == p then u.invul = true end end
    return "whosyourdaddy ligado para o slot " .. tostring(pid)
  elseif c == "thereisnospoon" then
    t.mana = true
    return "thereisnospoon ligado para o slot " .. tostring(pid)
  elseif c == "thedudeabides" then
    t.cooldown = true
    return "thedudeabides ligado para o slot " .. tostring(pid)
  elseif c == "iseedeadpeople" then
    t.vision = true
    return "iseedeadpeople ligado para o slot " .. tostring(pid)
  elseif c == "greedisgood" then
    __mock_recurso(p, PLAYER_STATE_RESOURCE_GOLD, n)
    __mock_recurso(p, PLAYER_STATE_RESOURCE_LUMBER, n)
    return "greedisgood " .. n .. " no slot " .. tostring(pid)
  elseif c == "keysersoze" then
    __mock_recurso(p, PLAYER_STATE_RESOURCE_GOLD, n)
    return "keysersoze " .. n .. " no slot " .. tostring(pid)
  elseif c == "leafittome" then
    __mock_recurso(p, PLAYER_STATE_RESOURCE_LUMBER, n)
    return "leafittome " .. n .. " no slot " .. tostring(pid)
  end
  return "codigo desconhecido: " .. tostring(codigo)
end
--- Efeito continuo dos codigos, um por tique do simulador (o motor faz o mesmo a cada quadro).
function __mock_cheat_tick()
  if next(__mock_cheats) == nil then return end
  for pid, t in pairs(__mock_cheats) do
    if t.mana or t.god then
      local p = Player(pid)
      for u in pairs(M.units) do
        if u.owner == p and u.typeid ~= 0 then
          if t.mana then u.mana = u.maxmana or u.mana or 0.0 end
          if t.god then u.invul = true end
        end
      end
    end
  end
end
-- [R1F1:anticheat] fim ===========================================================================
function GetEventDamage() return __dmg_ev and __dmg_ev.amount or 0.0 end
function BlzSetEventDamage(v) if __dmg_ev then __dmg_ev.amount = v end end
function GetEventDamageSource() return __dmg_ev and __dmg_ev.src or nil end
function BlzGetEventDamageTarget() return __dmg_ev and __dmg_ev.tgt or nil end
function BlzGetEventIsAttack() return __dmg_ev and __dmg_ev.attack or false end
function BlzGetEventAttackType() return __dmg_ev and __dmg_ev.at or ATTACK_TYPE_NORMAL end
function BlzGetEventDamageType() return __dmg_ev and __dmg_ev.dt or DAMAGE_TYPE_NORMAL end
function BlzGetEventWeaponType() return __dmg_ev and __dmg_ev.wt or WEAPON_TYPE_WHOKNOWS end
function BlzSetEventAttackType(v) if __dmg_ev then __dmg_ev.at = v end return true end
function BlzSetEventDamageType(v) if __dmg_ev then __dmg_ev.dt = v end return true end
function BlzSetEventWeaponType(v) if __dmg_ev then __dmg_ev.wt = v end return true end
-- [F5:dmgaudit] fim
function UnitDamagePoint(u, d, r, x, y, dmg, a, ra, at, dt, wt) return true end
function CreateGroup() return newh("group", { set = {}, list = {} }) end
function DestroyGroup(g) end
function GroupClear(g) if g then g.set = {} g.list = {} end end
function GroupAddUnit(g, u) if g and u and not g.set[u] then g.set[u] = true g.list[#g.list + 1] = u return true end return false end
function GroupRemoveUnit(g, u) if g and u and g.set[u] then g.set[u] = nil for i, x in ipairs(g.list) do if x == u then table.remove(g.list, i) break end end return true end return false end
function FirstOfGroup(g) return g and g.list[1] or nil end
__filter_unit = nil
__enum_unit = nil
function GetFilterUnit() return __filter_unit end
function GetEnumUnit() return __enum_unit end
function ForGroup(g, f) if not g then return end for _, u in ipairs(g.list) do M.nasc = M.nasc + 1 local p = __enum_unit __enum_unit = u local ok, e = pcall(f) __enum_unit = p if not ok then __logerr("ForGroup: " .. tostring(e)) end end end
local function enum_units(g, pred, f)
  if not g then return end
  g.set = {} g.list = {}
  -- o motor de verdade enumera na ordem interna dele, igual em todas as maquinas; pairs sobre
  -- tabela com chave de objeto sai na ordem do endereco de memoria, que muda a cada processo
  local todas = {}
  for u in pairs(M.units) do todas[#todas + 1] = u end
  table.sort(todas, function(x, y) return x.__seq < y.__seq end) -- [F5:priest] __seq
  for _, u in ipairs(todas) do
    if u.typeid ~= 0 and pred(u) and not (M.vida_temporizada and u.abil[1097625443]) then -- [F5:priest] Locust ('Aloc') fica fora da enumeracao no cenario --priest-e, como no motor
      local pass = true
      if f and f.fn then M.nasc = M.nasc + 1 local pu = __filter_unit __filter_unit = u local ok, v = pcall(f.fn) __filter_unit = pu if not ok then __logerr("enum filter: " .. tostring(v)) end pass = (v ~= false) end
      if pass then g.set[u] = true g.list[#g.list + 1] = u end
    end
  end
end
function GroupEnumUnitsInRange(g, x, y, r, f) enum_units(g, function(u) return (u.x - x) ^ 2 + (u.y - y) ^ 2 <= r * r end, f) end
-- [F6:thanatos] o retangulo era ignorado: toda enumeracao por area devolvia o mapa inteiro, entao
-- skill de sala de chefe (que escolhe o alvo dentro da sala) pegava qualquer unidade e o numero de
-- callbacks do filtro era o total de unidades do mapa. Agora a area vale, como no motor.
function GroupEnumUnitsInRect(g, r, f)
  if r == nil or r.minx == nil then enum_units(g, function(u) return true end, f) return end
  enum_units(g, function(u) return (u.x or 0) >= r.minx and (u.x or 0) <= r.maxx and (u.y or 0) >= r.miny and (u.y or 0) <= r.maxy end, f)
end
function GroupEnumUnitsOfPlayer(g, p, f) enum_units(g, function(u) return u.owner == p end, f) end
function GroupEnumUnitsOfType(g, n, f) end
function GroupEnumUnitsSelected(g, p, f) end
function GroupEnumUnitsInRangeOfLoc(g, l, r, f) end
function BlzGroupGetSize(g) return g and #g.list or 0 end
function BlzGroupUnitAt(g, i) return g and g.list[i + 1] or nil end
function CreateForce() return newh("force", { list = {} }) end
function DestroyForce(f) end
-- [F5:desyncyone] o motor nao repete jogador na forca e ForceRemovePlayer tira mesmo
function ForceAddPlayer(f, p)
  if not f then return end
  for _, q in ipairs(f.list) do if q == p then return end end
  f.list[#f.list + 1] = p
end
function ForceRemovePlayer(f, p)
  if not f then return end
  for i = 1, #f.list do if f.list[i] == p then table.remove(f.list, i) return end end
end
-- [F5:desyncyone] fim
function ForceClear(f) if f then f.list = {} end end
function ForceEnumPlayers(f, b) if f then f.list = {} for i = 0, 27 do f.list[#f.list + 1] = Player(i) end end end
__enum_player = nil
function GetEnumPlayer() return __enum_player end
function ForForce(f, fn) if not f then return end for _, p in ipairs(f.list) do M.nasc = M.nasc + 1 local q = __enum_player __enum_player = p local ok, e = pcall(fn) __enum_player = q if not ok then __logerr("ForForce: " .. tostring(e)) end end end
function Location(x, y) return newh("location", { x = x, y = y }) end
function RemoveLocation(l) end
function MoveLocation(l, x, y) if l then l.x = x l.y = y end end
function GetLocationX(l) return l and l.x or 0.0 end
function GetLocationY(l) return l and l.y or 0.0 end
-- [R1F2:astrologer2] inicio: ALTURA DO TERRENO no simulador.
-- O mock era PLANO (GetLocationZ = 0.0 e todo efeito nascendo em z = 0), e o motor nao e: no
-- Dream S5 1.0K 94,5% dos 231.361 pontos do war3map.w3e tem Z > 0 e a MEDIANA e 224,75
-- (port/tools_astrologer2/w3e_z.py). Com o mock plano, "efeito preso no Z absoluto 0" e
-- "efeito no chao" sao a mesma coisa, e o relato "a animacao da F so e vista de terrenos mais
-- altos" nao tinha como ser medido.
-- __TERRENO e a grade gerada do w3e de verdade (posta pelo Python logo depois deste prelude);
-- sem ela o mock volta a ser plano, como antes.
__TERRENO = nil
__MOCK_TERRENO_PLANO = false
function __terreno_z(x, y)
  local t = __TERRENO
  if t == nil or __MOCK_TERRENO_PLANO then return 0.0 end
  local passo = t.passo * 128.0
  local fx = ((x or 0.0) - t.offx) / passo
  local fy = ((y or 0.0) - t.offy) / passo
  local i, j = math.floor(fx), math.floor(fy)
  local dx, dy = fx - i, fy - j
  if i < 0 then i, dx = 0, 0.0 elseif i >= t.largura - 1 then i, dx = t.largura - 2, 1.0 end
  if j < 0 then j, dy = 0, 0.0 elseif j >= t.altura - 1 then j, dy = t.altura - 2, 1.0 end
  local a = t.z[j + 1][i + 1]
  local b = t.z[j + 1][i + 2]
  local c = t.z[j + 2][i + 1]
  local d = t.z[j + 2][i + 2]
  return (a * (1 - dx) + b * dx) * (1 - dy) + (c * (1 - dx) + d * dx) * dy
end
function GetLocationZ(l) if l == nil then return 0.0 end return __terreno_z(l.x or 0.0, l.y or 0.0) end
-- [R1F2:astrologer2] fim
-- [R1F2:save2] inicio: TERRENO.
-- No motor `GetTerrainType`/`GetTerrainCliffLevel` respondem com o que esta no `war3map.w3e`; no
-- simulador nao havia nativa nenhuma e o stub automatico devolvia 0 em todo ponto -- uma amostra
-- degenerada, que faria o bloco [R1F2:save2] tirar o terreno da chave e o cenario nunca seria
-- exercitado. Aqui o terreno e um padrao deterministico do ladrilho (128 unidades), que e o que o
-- teste precisa: mesmo ponto, mesmo valor, em toda sessao e nas duas maquinas do lockstep.
local TERRENOS = { 1281190228, 1148216148, 1147564116, 1281190996, 1147564372, 1282239572 }
local function __mock_tile(x, y)
  local i = math.floor((tonumber(x) or 0) / 128.0)
  local j = math.floor((tonumber(y) or 0) / 128.0)
  return ((i * 73 + j * 151) % 1000003 + 1000003) % 1000003
end
function GetTerrainType(x, y) return TERRENOS[(__mock_tile(x, y) % 6) + 1] end
function GetTerrainCliffLevel(x, y) return 2 + (__mock_tile(x, y) % 5) end
function SetTerrainType(x, y, t, v, a, s) end
-- [R1F2:save2] fim
function Rect(a, b, c, d) return newh("rect", { minx = a, miny = b, maxx = c, maxy = d }) end
function RemoveRect(r) end
function SetRect(r, a, b, c, d) if r then r.minx, r.miny, r.maxx, r.maxy = a, b, c, d end end
function GetRectMinX(r) return r and r.minx or 0 end
function GetRectMinY(r) return r and r.miny or 0 end
function GetRectMaxX(r) return r and r.maxx or 0 end
function GetRectMaxY(r) return r and r.maxy or 0 end
-- [F6:thanatos] o centro do retangulo era sempre 0,0: quem nasce "no centro da sala" nascia na
-- origem do mapa e ficava fora de toda area de efeito
function GetRectCenterX(r) if r and r.minx then return (r.minx + r.maxx) / 2.0 end return 0.0 end
function GetRectCenterY(r) if r and r.miny then return (r.miny + r.maxy) / 2.0 end return 0.0 end
-- [F5:herocw] GetWorldBounds tambem e nativa e devolve um retangulo novo a cada chamada
function GetWorldBounds() return newh("rect", { minx = -32000, miny = -32000, maxx = 32000, maxy = 32000 }) end
function GetPlayableMapRect() return Rect(-32000, -32000, 32000, 32000) end
function GetEntireMapRect() return Rect(-32000, -32000, 32000, 32000) end
function CreateRegion() return newh("region") end
function RegionAddRect(r, rc) end
-- itens: no chao (dono nil, visivel) ou no inventario (dono = unidade, invisivel)
M.items = {}
-- [F5:perf] a nativa recebe inteiro: com rawcode em texto (o mapa carrega o codigo do item da hashtable,
-- que no mock nao separa Save/LoadInteger de Save/LoadStr) toda conta com GetItemTypeId levantava erro
-- dentro do callback de EnumItemsInRect, e o xpcall do runtime montava um traceback por item.
function CreateItem(id, x, y)
  if type(id) == "string" then id = (#id == 4) and string.unpack(">I4", id) or 0 end
  local it = newh("item", { typeid = id, x = x, y = y, visible = true }) M.items[it] = true return it
end
-- [F5:perf] fim
-- [F5:craft]+[F5:itemtip] o motor guarda item em ESPACO de inventario (0..5, como UnitItemInSlot), com
-- carga, e recusa inventario cheio. Sem isso o simulador nao ve os materiais que estao no heroi, nao
-- conta carga de item empilhavel, e a dica do inventario nativo (Trig_UI_ItemColumnFunc002MMT) le nil.
local function inv_tira(i)
  local u = i and i.dono
  if u and u.inv then for s = 0, 5 do if u.inv[s] == i then u.inv[s] = nil end end end
  if u then u.aspd_own_tick = nil end   -- [R1F2:aspd2] item saiu: refazer o bonus do motor
  if i then i.dono = nil end
end
function __mock_tira_da_casa(i) inv_tira(i) end
function UnitInventorySize(u) return (u and u.invsize) or 6 end
-- alias do itemtip: primeira casa livre, 1-based (nil se cheio)
function __mock_slot_livre(u) if u == nil then return nil end u.inv = u.inv or {} for s = 0, UnitInventorySize(u) - 1 do local it = u.inv[s] if it == nil or it.typeid == 0 or it.dono ~= u then return s + 1 end end return nil end
-- espaco de inventario e 0..tamanho-1, como no motor (UnitItemInSlotBJ passa indice-1)
function UnitItemInSlot(u, s) if u == nil or u.inv == nil then return nil end local it = u.inv[s] if it and it.typeid ~= 0 and it.dono == u then return it end return nil end
-- [F5:craft] o motor recusa o item em mais casos que o inventario cheio (item que a unidade nao pode
-- carregar, por exemplo). __mock_falha_additem(n) faz as proximas n chamadas devolverem false, para
-- testar o caminho de "a entrega falhou" sem depender de encher inventario.
function __mock_falha_additem(n) M.falha_additem = n end
function UnitAddItem(u, i)
  if u == nil or i == nil then return false end
  if (M.falha_additem or 0) > 0 then M.falha_additem = M.falha_additem - 1 return false end
  u.inv = u.inv or {}
  for s = 0, UnitInventorySize(u) - 1 do
    local it = u.inv[s]
    if it == nil or it.typeid == 0 or it.dono ~= u then
      inv_tira(i)
      u.inv[s] = i i.dono = u i.visible = false
      u.aspd_own_tick = nil   -- [R1F2:aspd2] item entrou: refazer o bonus do motor
      return true
    end
  end
  return false
end
function UnitAddItemById(u, id) local it = CreateItem(id, u and u.x or 0.0, u and u.y or 0.0) UnitAddItem(u, it) return it end
-- [R1F2:save2] inicio: as outras tres nativas de criar item existem no motor e o mapa nao as usa,
-- mas um `.pld` com codigo injetado usa -- e o bloco [R1F2:save2] as embrulha. Sem elas aqui o
-- embrulho nao tinha o que embrulhar e o cenario de proveniencia nao valia.
function CreateItemLoc(id, l) return CreateItem(id, l and l.x or 0.0, l and l.y or 0.0) end
function BlzCreateItemWithSkin(id, x, y, skin) return CreateItem(id, x, y) end
function UnitAddItemToSlotById(u, id, s)
  if u == nil then return false end
  u.inv = u.inv or {}
  local atual = u.inv[s]
  if atual ~= nil and atual.typeid ~= 0 and atual.dono == u then return false end
  local it = CreateItem(id, u.x or 0.0, u.y or 0.0)
  u.inv[s] = it it.dono = u it.visible = false
  return true
end
-- [R1F2:save2] fim
function UnitRemoveItem(u, i) inv_tira(i) if i then i.visible = true end end
function UnitRemoveItemFromSlot(u, s)
  if u == nil or u.inv == nil then return nil end
  local i = u.inv[s] if i then u.inv[s] = nil i.dono = nil i.visible = true u.aspd_own_tick = nil end -- [R1F2:aspd2]
  return i
end
function UnitDropItemPoint(u, i, x, y) inv_tira(i) if i then i.x = x i.y = y i.visible = true end return true end
function UnitDropItemSlot(u, i, s) inv_tira(i) return true end
function RemoveItem(i) if i then inv_tira(i) M.items[i] = nil i.typeid = 0 i.cargas = 0 end end
function GetItemCharges(i) return (i and i.cargas) or 0 end
function SetItemCharges(i, v) if i then i.cargas = v end end
function GetItemPlayer(i) return (i and i.dono_p) or Player(15) end
function SetItemPlayer(i, p, b) if i then i.dono_p = p end end
-- [F5:craft]+[F5:itemtip] fim
-- [R1F1:enhance] VENDA DE LOJA (EVENT_PLAYER_UNIT_SELL_ITEM) e TIPO DE ITEM.
-- O mock deixava GetSoldItem/GetBuyingUnit/GetSellingUnit/GetItemType nos stubs automaticos de
-- common.j: cada chamada devolvia um handle NOVO, entao nenhum gatilho de loja do mapa tinha como
-- rodar (e o aprimoramento inteiro entra por uma compra na loja do ferreiro). Aqui o contexto do
-- evento e de verdade e GetItemType sai da coluna `class` do itemdata.slk, como no motor.
__sold_item, __buying_unit, __selling_unit = nil, nil, nil
function GetSoldItem() return __sold_item end
function GetBuyingUnit() return __buying_unit end
function GetSellingUnit() return __selling_unit end
local CLASSE_ITEM = { permanent = 0, charged = 1, powerup = 2, artifact = 3, purchasable = 4,
                      campaign = 5, miscellaneous = 6, unknown = 7 }
function GetItemType(i)
  local n = 7
  if i ~= nil and (i.typeid or 0) ~= 0 and __slk_raw and __slk_raw.item then
    local rec = __slk_raw.item[string.pack(">I4", i.typeid & 0xFFFFFFFF)]
    local c = rec and rec.class
    if c then n = CLASSE_ITEM[tostring(c):lower()] or 7 end
  end
  return ConvertItemType(n)
end
--- Compra de item numa loja, do jeito do motor: o item nasce, entra no inventario do comprador e
--- o evento EVENT_PLAYER_UNIT_SELL_ITEM dispara em TODOS os gatilhos registrados, na ordem de
--- registro (o gancho do framework vem antes do gg_trg_Shop do mapa, como no war3map.j).
--- `loja` e opcional (so alimenta GetSellingUnit). Devolve "n gatilho(s)".
function __mock_vender(comprador, codigo, loja)
  if comprador == nil then return "sem comprador" end
  local id = codigo
  if type(id) == "string" then id = (#id == 4) and string.unpack(">I4", id) or 0 end
  local it = CreateItem(id, comprador.x or 0.0, comprador.y or 0.0)
  UnitAddItem(comprador, it)
  local ps, pb, pv = __sold_item, __buying_unit, __selling_unit
  __sold_item, __buying_unit, __selling_unit = it, comprador, loja
  local n = __mock_unit_event(loja or comprador, EVENT_PLAYER_UNIT_SELL_ITEM)
  __sold_item, __buying_unit, __selling_unit = ps, pb, pv
  return tostring(n) .. " gatilho(s)"
end
-- [R1F1:enhance] fim
function GetItemX(i) return i and i.x or 0.0 end
function GetItemY(i) return i and i.y or 0.0 end
function SetItemPosition(i, x, y) if i then i.x = x i.y = y inv_tira(i) i.visible = true end end
function SetItemVisible(i, v) if i then i.visible = v and true or false end end
function IsItemVisible(i) return i ~= nil and i.visible == true end
function IsItemOwned(i) return i ~= nil and i.dono ~= nil end
__enum_item = nil
function GetEnumItem() return __enum_item end
function GetFilterItem() return __enum_item end
-- item no chao dentro do retangulo, na ordem de criacao (o motor enumera na ordem dele, igual em todas
-- as maquinas); cada filtro e cada callback conta em M.nasc
function EnumItemsInRect(r, filtro, f)
  if not r then return end
  local lista = {}
  for it in pairs(M.items) do
    if it.typeid ~= 0 and it.dono == nil and it.x >= (r.minx or 0) and it.x <= (r.maxx or 0) and
       it.y >= (r.miny or 0) and it.y <= (r.maxy or 0) then lista[#lista + 1] = it end
  end
  table.sort(lista, function(a, b) return a.__seq < b.__seq end) -- [F5:priest] __seq
  for _, it in ipairs(lista) do
    local p = __enum_item
    __enum_item = it
    local passa = true
    if filtro and filtro.fn then M.nasc = M.nasc + 1 local ok, v = pcall(filtro.fn) passa = ok and v ~= false end
    if passa and f then M.nasc = M.nasc + 1 local ok, e = pcall(f) if not ok then __logerr("EnumItemsInRect: " .. tostring(e)) end end
    __enum_item = p
  end
end
-- [F6:elementalist] POSICAO de efeito especial. O mock devolvia um handle sem posicao e deixava
-- BlzGetLocalSpecialEffectX/Y/Z no stub generico (0.0), entao EXGetEffectX/Y/Z respondia 0 para todo
-- efeito e GS_GetEffectLoc/GS_MoveEffect nao diziam nada: TODO projetil deste mapa (que e um efeito
-- especial movido por temporizador) parecia estar na origem do mapa. Sem isso nao da para medir onde
-- uma skill explode, quem ela pega nem se ela le a posicao de um efeito JA DESTRUIDO (padrao comum
-- neste mapa: `DestroyEffect(GS_AddSpecialEffectLoc(...))` e depois `EXGetEffectX(bj_lastCreatedEffect)`).
-- `__efeito_lido_morto` conta essas leituras; a posicao continua sendo devolvida (o motor de verdade
-- pode zerar), para nao trocar um mock otimista por um mock pessimista sem medicao em jogo.
M.efeitos = {}
__efeito_lido_morto = 0
__efeito_ultimo_morto = nil
function AddSpecialEffect(m, x, y)
  local e = newh("effect")
  -- [R1F2:astrologer2] o motor cria o efeito na ALTURA DO TERRENO do ponto, nao em z = 0; com o
  -- mock plano nao dava para ver que o mapa depois o prende no Z absoluto 0 (EXGetEffectZ mentindo)
  e.template, e.x, e.y, e.z, e.vivo = m, x or 0.0, y or 0.0, __terreno_z(x, y), true
  M.efeitos[e] = true
  return e
end
function AddSpecialEffectLoc(m, l) return AddSpecialEffect(m, l and l.x or 0.0, l and l.y or 0.0) end
function AddSpecialEffectTarget(m, u, a)
  local e = AddSpecialEffect(m, u and u.x or 0.0, u and u.y or 0.0)
  e.preso = u
  return e
end
function DestroyEffect(e) if e ~= nil then e.vivo = false M.efeitos[e] = nil end end
-- com __mock_efeito_morto_zera = true a nativa passa a responder 0 para efeito ja destruido, que e o
-- comportamento pessimista do motor (handle liberado): serve para medir quem depende disso
__mock_efeito_morto_zera = false
local function efe_pos(e, campo)
  if e == nil then return 0.0 end
  if not e.vivo then
    __efeito_lido_morto = __efeito_lido_morto + 1
    __efeito_ultimo_morto = e.template
    if __mock_efeito_morto_zera then return 0.0 end
  end
  if e.preso ~= nil and campo ~= "z" then return e.preso[campo] or 0.0 end
  return e[campo] or 0.0
end
function BlzGetLocalSpecialEffectX(e) return efe_pos(e, "x") end
function BlzGetLocalSpecialEffectY(e) return efe_pos(e, "y") end
function BlzGetLocalSpecialEffectZ(e) return efe_pos(e, "z") end
function BlzSetSpecialEffectX(e, v) if e ~= nil then e.x = v end end
function BlzSetSpecialEffectY(e, v) if e ~= nil then e.y = v end end
function BlzSetSpecialEffectZ(e, v) if e ~= nil then e.z = v end end
function BlzSetSpecialEffectPosition(e, x, y, z) if e ~= nil then e.x, e.y, e.z = x, y, z end end
function BlzSetSpecialEffectAlpha(e, a) if e ~= nil then e.alpha = a end end
function BlzSetSpecialEffectColor(e, r, g, b) if e ~= nil then e.cor = { r, g, b } end end
-- [F6:elementalist] fim
-- [F5:paladinr] texto flutuante com vida no mock: sem isso nao da para contar quantos ficaram vivos.
-- M.texttags guarda os vivos (chave = handle) com texto, posicao e se e permanente; o motor de
-- verdade so apaga em DestroyTextTag ou quando a vida (SetTextTagLifespan) acaba, e como o mapa
-- marca TODO texto como permanente (patch p101) so DestroyTextTag apaga.
function CreateTextTag()
  local h = newh("texttag")
  h.texto, h.perm, h.vivo = "", false, true
  h.nasceu = M.now
  M.texttags[h] = true
  return h
end
function DestroyTextTag(t)
  if t == nil then return end
  t.vivo = false
  M.texttags[t] = nil
end
function SetTextTagText(t, s, h) if t then t.texto = s t.tam = h end end -- [C2] e o tamanho (o `jump` do escudo)
function SetTextTagPos(t, x, y, z) if t then t.x, t.y, t.z = x, y, z end end
function SetTextTagPosUnit(t, u, z) if t and u then t.x, t.y, t.z = u.x, u.y, z end end
-- o motor recusa fracao em parametro declarado `integer` ("number has no integer representation"):
-- SetTextTagColor e a unica nativa de texto flutuante com parametro inteiro, e e onde o mapa manda
-- cor*2.55 (100*2.55 = 254.99999999999997). O mock era mais simples que o motor e aceitava.
local function __inteiro(nome, i, v)
  if type(v) == "number" and v % 1 ~= 0 then
    error(string.format("bad argument #%d to '%s' (number has no integer representation)", i, nome), 3)
  end
  return v
end
__inteiro_arg = __inteiro
function SetTextTagColor(t, r, g, b, a)
  __inteiro("SetTextTagColor", 2, r) __inteiro("SetTextTagColor", 3, g)
  __inteiro("SetTextTagColor", 4, b) __inteiro("SetTextTagColor", 5, a)
  if t then t.cor = { r, g, b, a } end
end
function SetTextTagPermanent(t, f) if t then t.perm = f end end
function SetTextTagLifespan(t, s) if t then t.vida = s end end
-- [C2] o texto de vida curta sai sozinho no fim da vida (o motor faz isso com o texto NAO permanente: o
-- `BLOCK(n)` do escudo usa `life=1.5`). Sem isto o simulador contava como vazamento o que o jogo tira.
function __mock_tt_tick()
  for tt in pairs(M.texttags) do
    if not tt.perm and tt.vida and tt.vida > 0 and M.now - (tt.nasceu or M.now) >= tt.vida then
      tt.vivo = false
      M.texttags[tt] = nil
    end
  end
end
function SetTextTagVisibility(t, f) if t then t.visivel = f end end
-- conta os textos vivos; devolve total, permanentes e uma amostra
function __mock_texttags()
  local total, perm, amostra = 0, 0, {}
  local lista = {}
  for t in pairs(M.texttags) do lista[#lista + 1] = t end
  table.sort(lista, function(a, b) return a.__h < b.__h end)
  for _, t in ipairs(lista) do
    total = total + 1
    if t.perm then perm = perm + 1 end
    if #amostra < 8 then
      amostra[#amostra + 1] = string.format("#%d t=%.1fs perm=%s texto=%s", t.__h, t.nasceu or -1,
        tostring(t.perm), tostring(t.texto))
    end
  end
  return total, perm, table.concat(amostra, "\n  ")
end
-- [F5:paladinr] fim
function CreateDestructable(id, x, y, f, s, v) return newh("destructable", { typeid = id }) end
function CreateDestructableZ(id, x, y, z, f, s, v) return newh("destructable", { typeid = id }) end
function CreateDeadDestructable(id, x, y, f, s, v) return newh("destructable", { typeid = id }) end
function CreateDeadDestructableZ(id, x, y, z, f, s, v) return newh("destructable", { typeid = id }) end
function CreateFogModifierRect(p, s, r, a, b) return newh("fogmodifier") end
function CreateFogModifierRadius(p, s, x, y, r, a, b) return newh("fogmodifier") end
function CreateFogModifierRadiusLoc(p, s, l, r, a, b) return newh("fogmodifier") end
function CreateSound(a, b, c, d, e, f) return newh("sound") end
function CreateMIDISound(a, b, c) return newh("sound") end
function CreateMultiboard() return newh("multiboard") end
function MultiboardGetItem(m, r, c) return newh("multiboarditem") end
function CreateLeaderboard() return newh("leaderboard") end
function CreateTimerDialog(t) return newh("timerdialog") end
function DialogCreate() return newh("dialog") end
-- [F5:craft] o botao clicado do dialogo e estado do motor, nao um handle novo a cada chamada
function __mock_click(d, b) M.dialogo = d M.botao = b end
-- [F5:craft] fim
function CreateQuest() return newh("quest") end
function QuestCreateItem(q) return newh("questitem") end
function CreateDefeatCondition() return newh("defeatcondition") end
function CreateTrackable(m, x, y, f) return newh("trackable") end
function CreateImage(a, b, c, d, e, f, g, h, i, j, k) return newh("image") end
function CreateUbersplat(a, b, c, d, e, f, g, h, i, j) return newh("ubersplat") end
function AddLightning(a, b, c, d, e, f) return newh("lightning") end
function AddLightningEx(a, b, c, d, e, f, g, h) return newh("lightning") end
function CreateUnitPool() return newh("unitpool") end
function CreateItemPool() return newh("itempool") end
function InitGameCache(n) return newh("gamecache", { store = {} }) end
function StoreString(c, m, k, v) if c then c.store[m .. "\0" .. k] = v end return true end
function GetStoredString(c, m, k) if not c then return "" end return c.store[m .. "\0" .. k] or "" end
function SyncStoredString(c, m, k) end
function FlushGameCache(c) end
function SaveGameCache(c) return true end
function GetCameraMargin(m) return 0.0 end
-- [F6:elementalist] limites de camera do mapa de verdade (war3map.w3i: canto inferior esquerdo
-- -30720,-27904 e superior direito 27648,30848). Sem eles GetCameraBoundMin/Max caiam no stub
-- generico que devolve 0, e o mapa guarda esses valores em yd_MapMinX/MaxX/MinY/MaxY (war3map.j
-- 10505-10508). Todo movimento do mapa passa por RMinBJ(RMaxBJ(v, yd_MapMin), yd_MapMax)
-- (GS_moveunit, GS_PolarProjectionBJ, GS_SetUnitPositionLoc): com 0 em tudo, min(max(v,0),0) = 0 e
-- TODO projetil, orbita e reposicionamento ia parar em (0,0) dentro do simulador.
function GetCameraBoundMinX() return -30720.0 end
function GetCameraBoundMinY() return -27904.0 end
function GetCameraBoundMaxX() return 27648.0 end
function GetCameraBoundMaxY() return 30848.0 end
-- [F6:elementalist] fim
function GetCameraEyePositionX() return 0.0 end
function GetCameraEyePositionY() return -1000.0 end
function GetCameraEyePositionZ() return 1500.0 end
function GetCameraTargetPositionX() return 0.0 end
function GetCameraTargetPositionY() return 0.0 end
function GetCameraTargetPositionZ() return 0.0 end
function GetCameraField(f) return 1.22 end
function CreateCameraSetup() return newh("camerasetup") end
function BlzGetLocalClientWidth() return 1920 end
function BlzGetLocalClientHeight() return 1080 end
-- o mouse na tela (o pixel, Y de cima para baixo; o teste muda `__sim_mouse`): o centro da tela de 1920 x 1080. O quadro
-- vai de 0 a 0,6 na altura; na largura 0,8 e' a area 4:3 do meio (a conta do Reforged em tela larga)
__sim_mouse = { x = 960, y = 540 }
function BlzGetMouseScreenPosX() return __sim_mouse.x end
function BlzGetMouseScreenPosY() return __sim_mouse.y end
function BlzPixelToFrameX(px) return 0.4 + (px - 960) * 0.6 / 1080 end
function BlzPixelToFrameY(py) return (1080 - py) * 0.6 / 1080 end
function BlzSetMousePos(x, y) __sim_mouse.x, __sim_mouse.y = x, y end
function BlzGetTriggerPlayerMouseButton() return MOUSE_BUTTON_TYPE_LEFT end
function BlzIsMouseButtonPressed(b) return false end

-- frames
local origins = {}
function BlzGetOriginFrame(k, i) local key = tostring(k) .. ":" .. tostring(i) local f = origins[key] if not f then f = newh("frame", { name = "origin" }) origins[key] = f end return f end
function BlzCreateFrameByType(t, n, p, tpl, id) return newh("frame", { ftype = t, name = n, parent = p, tpl = tpl, visible = true, text = "" }) end
function BlzCreateFrame(n, p, pr, id) return newh("frame", { name = n, parent = p, visible = true, text = "" }) end
function BlzCreateSimpleFrame(n, p, id) return newh("frame", { name = n, parent = p, visible = true, text = "" }) end
function BlzDestroyFrame(f) end
function BlzGetFrameByName(n, id) return nil end
function BlzLoadTOCFile(p) return true end
function BlzFrameSetVisible(f, v) if f then f.visible = v end end
function BlzFrameIsVisible(f) return f and f.visible or false end
function BlzFrameSetText(f, t) if f then f.text = t end end
function BlzFrameGetText(f) return f and f.text or "" end
function BlzFrameAddText(f, t) end
function BlzFrameSetEnable(f, e) end
function BlzFrameGetEnable(f) return true end
function BlzFrameGetParent(f) return f and f.parent or nil end
function BlzFrameGetName(f) return f and f.name or "" end
function BlzFrameGetHeight(f) return 0.1 end
function BlzFrameGetAlpha(f) return 255 end
function BlzFrameGetValue(f) return 0.0 end
function BlzFrameGetTextSizeLimit(f) return 0 end
-- [F5:statusui] geometria de quadro: sem isto BlzFrameSetSize/SetPoint/SetFont/SetTextAlignment caem
-- nos stubs vazios do gen_stubs e nao da para medir largura, ancoragem nem alinhamento no simulador --
-- que e justamente onde esta o defeito do rotulo do escudo (quadro de TEXTO de 0.001 de largura, que
-- no motor quebra a palavra uma letra por linha). So guarda o que foi pedido; nao desenha nada.
function BlzFrameSetSize(f, w, h) if f then f.w = w f.h = h end end
function BlzFrameSetPoint(f, p, rel, rp, x, y)
  if not f then return end
  f.points = f.points or {}
  f.points[#f.points + 1] = { p = p, rel = rel, rp = rp, x = x, y = y }
end
function BlzFrameSetAbsPoint(f, p, x, y)
  if not f then return end
  f.points = f.points or {}
  f.points[#f.points + 1] = { p = p, abs = true, x = x, y = y }
end
function BlzFrameClearAllPoints(f) if f then f.points = {} end end
function BlzFrameSetAllPoints(f, rel) if f then f.allpoints = rel end end
function BlzFrameSetFont(f, file, h, flag) if f then f.font = file f.fonth = h f.fontflag = flag end end
function BlzFrameSetTextAlignment(f, v, h) if f then f.alinv = v f.alinh = h end end
-- BlzFrameSetParent fica como estava (stub vazio do gen_stubs): guardar o pai de verdade mudaria o
-- que BlzFrameGetParent responde nos quadros que o runtime reparenteia para fora da area 4:3.
-- [/F5:statusui]
function BlzGetTriggerFrame() return nil end
function BlzGetTriggerFrameEvent() return nil end
function BlzGetTriggerFrameValue() return 0.0 end
function BlzGetTriggerFrameText() return "" end

-- Preload / Preloader : sistema de arquivos em memoria + canal de tooltips
local gen = {}
function PreloadGenClear() gen = {} end
function PreloadGenStart() gen = {} end
function Preload(s) gen[#gen + 1] = s end
-- [R1F2:stutter] PreloadGenEnd e o unico ponto em que o jogo ESCREVE ARQUIVO em disco (perfil,
-- backup do wipe, arquivo do detector, log do --trace). No mock e uma copia de tabela; em jogo e
-- I/O sincrono no meio do quadro. --arquivos=ARQ anota cada escrita (tempo de jogo, caminho,
-- linhas, bytes) para a conta de "quantos arquivos e quantos bytes por minuto".
__PRELOAD_LOG = nil
function PreloadGenEnd(path)
  if __PRELOAD_LOG ~= nil then
    local n, bytes = #gen, 0
    for i = 1, n do bytes = bytes + #tostring(gen[i]) + 1 end
    __PRELOAD_LOG[#__PRELOAD_LOG + 1] = string.format("%.3f\t%s\t%d\t%d", M.now, tostring(path), n, bytes)
  end
  M.files[path] = { table.unpack(gen) } gen = {}
end
function PreloadStart() end
function PreloadEnd(t) end
function PreloadEndEx() end
-- [R1F2:save2] inicio: o `.pld` e um SCRIPT JASS que o motor executa inteiro no `Preloader` -- nao
-- so as linhas de dica. E o exploit classico de Preload, e e a hipotese de como os saves editados
-- passaram. O simulador so interpretava `BlzSetAbility*Tooltip`, entao o cenario nao existia aqui.
--
-- Agora ele executa TAMBEM um punhado de nativas com argumentos literais -- o suficiente para o
-- cenario de injecao do tema: criar item, criar unidade, dar item a uma unidade, mexer em recurso,
-- subir nivel de heroi e agendar qualquer uma dessas coisas com `TimerStart` apontando para uma
-- funcao declarada no proprio arquivo. NAO e um interpretador de JASS: e um reconhecedor das
-- formas que um arquivo de trapaca usa.
--
-- IMPORTANTE: quem executa o `.pld` no jogo e o MOTOR, e nenhum embrulho Lua do runtime ve essas
-- chamadas -- e por isso que o item injetado nasce sem proveniencia e que o anti-cheat nao "perdoa"
-- a janela de recurso. Para o simulador reproduzir isso, tudo aqui chama a nativa CRUA
-- (`__rawnat`), nunca a global embrulhada.
local function pld_nat(nome)
  local rn = __rawnat
  local f = rn and rn[nome]
  if type(f) == "function" then return f end
  return _G[nome]
end
local function pld_num(s)
  if s == nil then return nil end
  s = s:gsub("^%s+", ""):gsub("%s+$", "")
  local r = s:match("^'(....)'$")
  if r then return string.unpack(">I4", r) end
  return tonumber(s)
end
local function pld_unidade(arg)
  -- `Player(N)` -> o primeiro heroi daquele jogador; senao a primeira unidade humana que existir
  local pid = tonumber(arg and arg:match("Player%s*%(%s*(%d+)%s*%)") or nil)
  local env = __JENV
  local herois = env and env.udg_Hero
  if herois ~= nil then
    if pid ~= nil then
      local u = herois[pid + 1]
      if u ~= nil and GetUnitTypeId(u) ~= 0 then return u end
    end
    for i = 1, 16 do
      local u = herois[i]
      if u ~= nil and GetUnitTypeId(u) ~= 0 then return u end
    end
  end
  return nil
end
local function pld_estado(nome)
  if nome:find("LUMBER") then return PLAYER_STATE_RESOURCE_LUMBER end
  if nome:find("FOOD") then return PLAYER_STATE_RESOURCE_FOOD_USED end
  return PLAYER_STATE_RESOURCE_GOLD
end
local function pld_executa(s)
  local fez = 0
  for fn, args in s:gmatch("call%s+([%w_]+)%s*%((.-)%)%s*$") do
    local a = {}
    for campo in (args .. ","):gmatch("(.-),%s*") do a[#a + 1] = campo end
    local ok, e = pcall(function()
      if fn == "CreateItem" then
        pld_nat("CreateItem")(pld_num(a[1]), tonumber(a[2]) or 0.0, tonumber(a[3]) or 0.0)
        fez = fez + 1
      elseif fn == "UnitAddItemById" then
        local u = pld_unidade(a[1])
        if u ~= nil then
          -- no motor e UMA nativa; aqui a crua do mock e feita de duas, entao a criacao tem de
          -- ser a crua tambem, senao o item nasceria COM proveniencia
          local it = pld_nat("CreateItem")(pld_num(a[2]), GetUnitX(u), GetUnitY(u))
          UnitAddItem(u, it)
          fez = fez + 1
        end
      elseif fn == "SetPlayerState" then
        local pid = tonumber(a[1]:match("Player%s*%(%s*(%d+)%s*%)") or "0") or 0
        pld_nat("SetPlayerState")(Player(pid), pld_estado(a[2] or ""), tonumber(a[3]) or 0)
        fez = fez + 1
      elseif fn == "SetHeroLevel" then
        local u = pld_unidade(a[1])
        if u ~= nil then pld_nat("SetHeroLevel")(u, tonumber(a[2]) or 1, false) fez = fez + 1 end
      elseif fn == "CreateUnit" then
        local pid = tonumber(a[1]:match("Player%s*%(%s*(%d+)%s*%)") or "0") or 0
        pld_nat("CreateUnit")(Player(pid), pld_num(a[2]), tonumber(a[3]) or 0.0,
                              tonumber(a[4]) or 0.0, tonumber(a[5]) or 0.0)
        fez = fez + 1
      end
    end)
    if not ok then __logerr("pld injetado: " .. tostring(e)) end
  end
  return fez
end
function Preloader(path)
  local lines = M.files[path]
  if not lines then return end
  local corpo = {}       -- funcoes declaradas no arquivo: nome -> linhas
  local atual = nil
  for _, s in ipairs(lines) do
    for fn, id, val in s:gmatch("call (BlzSetAbility%a*Tooltip)%('(....)',\"(.-)\",0%)") do
      val = val:gsub("\\(.)", "%1")
      local code = string.unpack(">I4", id)
      -- [reorganizacao 4b, 26/09/2026] as SEIS dicas (a rota M16, `kk_jn.j`, usa as seis; o save do KK, so' as duas
      -- primeiras): cada linha vai para a nativa do nome dela. Antes, tudo que nao era a Tooltip caia na Extended
      local set = _G[fn]
      if fn == "BlzSetAbilityTooltip" then BlzSetAbilityTooltip(code, val, 0)
      elseif type(set) == "function" then set(code, val, 0)
      else BlzSetAbilityExtendedTooltip(code, val, 0) end
    end
    -- as linhas de perfil vem dentro de `")` ... `//`: so o que esta FORA delas e codigo solto
    for linha in (tostring(s) .. "\n"):gmatch("(.-)\n") do
      local nome = linha:match("^%s*function%s+([%w_]+)%s+takes")
      if nome then atual = {} corpo[nome] = atual
      elseif linha:match("^%s*endfunction") then atual = nil
      elseif linha:match("^%s*call%s+") and not linha:match("BlzSetAbility%a*Tooltip") then
        if atual then atual[#atual + 1] = linha
        else
          local dur, alvo = linha:match("call%s+TimerStart%s*%(.-,%s*([%d%.]+)%s*,.-function%s+([%w_]+)")
          if dur and alvo then
            local tt = CreateTimer()
            TimerStart(tt, tonumber(dur) or 1.0, false, function()
              PauseTimer(tt)
              local ls = corpo[alvo]
              if ls then for k = 1, #ls do pld_executa(ls[k]) end end
            end)
          else
            pld_executa(linha)
          end
        end
      end
    end
  end
end
-- [R1F2:save2] fim
-- [F6:dmgfix1] inicio: dica de habilidade POR NIVEL no simulador.
-- O motor guarda um texto por nivel (o 3o argumento e o nivel, base 0) e os dados de objeto podem
-- trazer um texto por nivel (`Ubertip="nivel 1","nivel 2",...`). O mock guardava um texto so por
-- habilidade e ignorava o nivel, entao nao dava para conferir nem a dica por nivel nem a
-- restauracao nivel a nivel do canal de perfil. Agora a chave do armazenamento inclui o nivel e o
-- padrao vem da lista `ubertip_lv`/`tip_lv` do `__slk_raw` quando ela existe.
local function tt_default(code, field, l)
  local rec = __slk_raw.ability[string.pack(">I4", code & 0xFFFFFFFF)]
  if rec == nil then return "Tool tip missing!" end
  local lista = rec[field .. "_lv"]
  if type(lista) == "table" then
    local i = (tonumber(l) or 0) + 1
    if i < 1 then i = 1 end
    if i > #lista then i = #lista end
    return lista[i]
  end
  if rec[field] then return rec[field] end
  return "Tool tip missing!"
end
function BlzSetAbilityTooltip(code, s, l) M.tooltips[code .. ":t:" .. tostring(tonumber(l) or 0)] = s return true end
function BlzGetAbilityTooltip(code, l)
  return M.tooltips[code .. ":t:" .. tostring(tonumber(l) or 0)] or tt_default(code, "tip", l)
end
function BlzSetAbilityExtendedTooltip(code, s, l) M.tooltips[code .. ":u:" .. tostring(tonumber(l) or 0)] = s return true end
function BlzGetAbilityExtendedTooltip(code, l)
  return M.tooltips[code .. ":u:" .. tostring(tonumber(l) or 0)] or tt_default(code, "ubertip", l)
end
-- [F6:dmgfix1] fim
function BlzSetAbilityIcon(c, s) end
function BlzGetAbilityIcon(c) return "" end
-- [reorganizacao 4b, 26/09/2026] as outras quatro dicas guardam texto como as duas primeiras (eram no-op, e a leitura
-- devolvia ""): o canal do save da M16 (`kk_jn.j`) usa as seis. O padrao vem do `__slk_raw` (untip, unubertip,
-- researchtip, researchubertip), senao "Tool tip missing!", como no jogo
function BlzSetAbilityActivatedTooltip(c, s, l) M.tooltips[c .. ":a:" .. tostring(tonumber(l) or 0)] = s return true end
function BlzGetAbilityActivatedTooltip(c, l)
  return M.tooltips[c .. ":a:" .. tostring(tonumber(l) or 0)] or tt_default(c, "untip", l)
end
function BlzSetAbilityActivatedExtendedTooltip(c, s, l) M.tooltips[c .. ":ae:" .. tostring(tonumber(l) or 0)] = s return true end
function BlzGetAbilityActivatedExtendedTooltip(c, l)
  return M.tooltips[c .. ":ae:" .. tostring(tonumber(l) or 0)] or tt_default(c, "unubertip", l)
end
function BlzSetAbilityResearchTooltip(c, s, l) M.tooltips[c .. ":r:" .. tostring(tonumber(l) or 0)] = s return true end
function BlzGetAbilityResearchTooltip(c, l)
  return M.tooltips[c .. ":r:" .. tostring(tonumber(l) or 0)] or tt_default(c, "researchtip", l)
end
function BlzSetAbilityResearchExtendedTooltip(c, s, l) M.tooltips[c .. ":re:" .. tostring(tonumber(l) or 0)] = s return true end
function BlzGetAbilityResearchExtendedTooltip(c, l)
  return M.tooltips[c .. ":re:" .. tostring(tonumber(l) or 0)] or tt_default(c, "researchubertip", l)
end

function DisplayTextToPlayer(p, x, y, s) M.chat[#M.chat + 1] = tostring(s) end
function DisplayTimedTextToPlayer(p, x, y, d, s) M.chat[#M.chat + 1] = tostring(s) end
__mock_chat_string = nil
function GetEventPlayerChatString() return __mock_chat_string or "" end
function __mock_say(p, msg)
  local fired = 0
  local pp = __trigger_player
  __trigger_player = p or Player(0)
  __mock_chat_string = msg
  local gat = {} for t in pairs(M.trig_events or {}) do gat[#gat + 1] = t end
  table.sort(gat, function(x, y) return x.__seq < y.__seq end) -- [F5:priest] __seq
  for _, t in ipairs(gat) do
    for _, ev in ipairs(t.events) do
      -- [R1F1:comandos] casamento exato quando o registro pediu (o motor so dispara a mensagem
      -- inteira); sem ele continua valendo o prefixo, que e o comportamento do motor com false.
      if ev[1] == "chat" and (ev[2] == "" or (ev[3] and msg:lower() == ev[2]:lower())
          or ((not ev[3]) and msg:sub(1, #ev[2]):lower() == ev[2]:lower())) then
        if TriggerEvaluate(t) then TriggerExecute(t) end
        fired = fired + 1
        break
      end
    end
  end
  __trigger_player = pp
  __mock_chat_string = nil
  return fired
end
-- [F5:lmage] evento de dano de verdade.
-- O mapa registra EVENT_UNIT_DAMAGING em cada unidade (YDWEAnyUnitDamagedFilter) e, dentro de
-- Trig_HurtFunc006A, so avisa "dano de ataque" (GS_ExecuteTrigger("攻击伤害") -> on_atk) quando
-- EXGetEventDamageData(2) -> BlzGetEventIsAttack() responde verdadeiro. Sem este bloco o
-- simulador nunca exercita esse portao, que e justamente o unico elo da skill D que ele nao via.
-- [F5:lmage]+[F5:dmgaudit] __mock_damage do lmage sobre o pipeline de dano do dmgaudit (um modelo so):
-- dispara DAMAGING (o mapa le/escreve o dano), aplica a mitigacao do alvo, dispara DAMAGED e desconta
-- a vida. Devolve (gatilhos DAMAGING registrados, dano que saiu da vida do alvo).
function __mock_damage(fonte, alvo, quanto, eh_ataque)
  local pp = __dmg_pipeline
  __dmg_pipeline = true
  local antes = (alvo and alvo.life) or 0
  local n = 0
  for _ in pairs(M.dmg_trigs[EVENT_UNIT_DAMAGING] or {}) do n = n + 1 end
  UnitDamageTarget(fonte, alvo, quanto, eh_ataque ~= false, false, ATTACK_TYPE_HERO, DAMAGE_TYPE_NORMAL, WEAPON_TYPE_METAL_HEAVY_BASH)
  __dmg_pipeline = pp
  return n, antes - ((alvo and alvo.life) or 0)
end
-- [F5:lmage] fim
function ClearTextMessages() end
-- [F5:castui] inicio
-- Modelo do motor do Reforged para pausa, animacao e ordens, que o mock nao tinha:
--   PauseUnit(u,true)      -> u.pausado: a barra de comandos da unidade selecionada fica PRETA
--   BlzPauseUnitEx(u,true) -> u.stun_ex: a barra continua, mas a ANIMACAO congela (secao 32)
--   SetUnitAnimation*      -> so registra quando a animacao nao esta congelada
--   IssueXOrder*           -> dispara EVENT_PLAYER_UNIT_ISSUED_*_ORDER nos gatilhos registrados
-- As duas primeiras linhas sao o que separa o defeito da correcao; as outras medem o custo.
function PauseUnit(u, f) if u then u.pausado = (f == true) end end
function BlzPauseUnitEx(u, f) if u then u.stun_ex = (f == true) end end
function SetUnitPropWindow(u, r) if u then u.prop = r + 0.0 end end
function GetUnitPropWindow(u) return u and (u.prop or 1.0472) or 0.0 end
-- sondas: o que o jogador VE
function __castui_barra_preta(u) return u ~= nil and u.pausado == true end
function __castui_anim(u) return u and u.anim or nil end
function __castui_anim_n(u) return u and (u.anim_n or 0) or 0 end
local function anima(u, a)
  if not u then return end
  if u.stun_ex then u.anim_perdida = (u.anim_perdida or 0) + 1 return end
  u.anim = a u.anim_n = (u.anim_n or 0) + 1
end
function SetUnitAnimation(u, a) anima(u, a) end
function SetUnitAnimationByIndex(u, i) anima(u, i) end
function QueueUnitAnimation(u, a) anima(u, a) end
function AddUnitAnimationProperties(u, a, b) end
function ResetUnitAnimation(u) anima(u, "stand") end
-- ordens: evento sincronizado, na ordem do handle do gatilho (como __mock_say)
__ordem_id, __ordem_alvo, __ordem_x, __ordem_y = 0, nil, 0.0, 0.0
function GetIssuedOrderId() return __ordem_id or __mock_order_id or 0 end  -- [F5:castui]+[F5:perf]
function GetOrderedUnit() return __trigger_unit end
function GetOrderTargetUnit() return __ordem_alvo end
function GetOrderPointX() return __ordem_x end
function GetOrderPointY() return __ordem_y end
local function dispara_ordem(u, oid, ev)
  if not u then return false end
  M.ordens = (M.ordens or 0) + 1
  if u.pausado then M.ordens_ignoradas = (M.ordens_ignoradas or 0) + 1 return false end
  u.ordem = oid
  local po, pu = __ordem_id, __trigger_unit
  __ordem_id = oid
  local gat = {} for t in pairs(M.trig_events or {}) do gat[#gat + 1] = t end
  table.sort(gat, function(x, y) return x.__h < y.__h end)
  for _, t in ipairs(gat) do
    for _, e in ipairs(t.events) do
      if e[1] == "playerunit" and e[2] == ev then __mock_fire(t, u, u.owner) break end
    end
  end
  __ordem_id, __trigger_unit = po, pu
  return true
end
function IssueImmediateOrderById(u, oid) return dispara_ordem(u, oid, EVENT_PLAYER_UNIT_ISSUED_ORDER) end
function IssueTargetOrderById(u, oid, alvo)
  local pa = __ordem_alvo __ordem_alvo = alvo
  local r = dispara_ordem(u, oid, EVENT_PLAYER_UNIT_ISSUED_TARGET_ORDER)
  __ordem_alvo = pa return r
end
function IssuePointOrderById(u, oid, x, y)
  local px, py = __ordem_x, __ordem_y __ordem_x, __ordem_y = x, y
  local r = dispara_ordem(u, oid, EVENT_PLAYER_UNIT_ISSUED_POINT_ORDER)
  __ordem_x, __ordem_y = px, py return r
end
function IssueImmediateOrder(u, s) return IssueImmediateOrderById(u, OrderId(s)) end
function IssueTargetOrder(u, s, alvo) return IssueTargetOrderById(u, OrderId(s), alvo) end
function IssuePointOrder(u, s, x, y) return IssuePointOrderById(u, OrderId(s), x, y) end
-- [F5:castui] fim
function print(...) local t = {} for i = 1, select("#", ...) do t[i] = tostring((select(i, ...))) end M.chat[#M.chat + 1] = "print: " .. table.concat(t, "\t") end
-- [F5:skin] nome da unidade, nome proprio e skin
-- O mock devolvia "unit" em todo GetUnitName e nao tinha nome proprio nem skin, entao o relato do nome
-- com skin nao aparecia aqui. No motor, GetUnitName e o nome da barra de experiencia ("Level N <nome>")
-- e GetHeroProperName o nome de cima do painel do heroi; os dois nascem do tipo (Name e o primeiro de
-- Propernames) e BlzSetUnitName / BlzSetHeroProperName trocam por unidade. Se o motor tambem troca os
-- nomes quando BlzSetUnitSkin troca a skin nao da para medir fora do jogo, entao os dois comportamentos
-- ficam disponiveis: __MOCK_SKIN_RENOMEIA = true faz a troca de skin levar os nomes da skin junto (o
-- pior caso compativel com o relato). __mock_nomes_log = {} grava cada troca com a pilha de quem chamou.
__MOCK_SKIN_RENOMEIA = __MOCK_SKIN_RENOMEIA or false
__mock_nomes_log = nil
do
  local function tipo_rec(id)
    if id == nil or id == 0 or __slk_raw == nil then return nil end
    local sid = string.pack(">I4", id & 0xFFFFFFFF)
    return (__slk_raw.unit and __slk_raw.unit[sid]) or (__slk_raw.ability and __slk_raw.ability[sid])
      or (__slk_raw.item and __slk_raw.item[sid])
  end
  local function tipo_nome(id) local r = tipo_rec(id) return r and r.name or "" end
  local function tipo_proprio(id)
    local r = tipo_rec(id)
    local s = r and r.propernames
    if s == nil or s == "" then return "" end
    return s:match("^%s*([^,]-)%s*,") or s:match("^%s*(.-)%s*$")
  end
  local function pilha()
    local t = {}
    for nivel = 3, 14 do
      local d = debug.getinfo(nivel, "n")
      if d == nil then break end
      if d.name then t[#t + 1] = d.name end
    end
    return table.concat(t, "<")
  end
  local function anota(nat, u, v)
    if __mock_nomes_log then
      __mock_nomes_log[#__mock_nomes_log + 1] = string.format("t=%.3f %s(u#%s, %s) <- %s", M.now, nat,
        tostring(u and u.__h), tostring(v), pilha())
    end
  end
  function GetObjectName(id) return tipo_nome(id) end
  function GetUnitName(u)
    if u == nil then return nil end
    if u.nome ~= nil then return u.nome end
    return tipo_nome(u.typeid)
  end
  function GetHeroProperName(u)
    if u == nil then return nil end
    if u.nomeproprio ~= nil then return u.nomeproprio end
    return tipo_proprio(u.typeid)
  end
  function BlzSetUnitName(u, s) if u then u.nome = s anota("BlzSetUnitName", u, s) end end
  function BlzSetHeroProperName(u, s) if u then u.nomeproprio = s anota("BlzSetHeroProperName", u, s) end end
  function BlzGetUnitSkin(u) return u and (u.skin or u.typeid) or 0 end
  function BlzSetUnitSkin(u, id)
    if u == nil then return end
    u.skin = id
    anota("BlzSetUnitSkin", u, string.pack(">I4", (id or 0) & 0xFFFFFFFF))
    if __MOCK_SKIN_RENOMEIA then
      u.nome = tipo_nome(id)
      u.nomeproprio = tipo_proprio(id)
    end
  end
end
-- [F5:skin] fim

-- [F5:priest] destruir devolve o numero da pilha do "presence" e deixa o numero de handle para o coletor.
-- No Lua do Reforged o numero de handle de um objeto destruido so volta para a fila quando o objeto Lua e
-- recolhido pelo coletor de lixo, e o coletor passa em hora diferente em cada maquina (partida do Priest:
-- o campo h do detector diverge desde 228 s e o heroi nasce com numero diferente em cada maquina).
-- __gc_simulado() faz isso numa maquina so: coleta de verdade no Lua do simulador e devolve o numero de
-- quem ja foi recolhido; o proximo objeto criado ali reaproveita o menor numero livre.
M.mortos = setmetatable({}, { __mode = "v" })
M.mortos_ids = {}
function __mock_morre(h)
  if type(h) ~= "table" or h.__morto then return end
  h.__morto = true
  if h.__abpres then
    local ids = {}
    for id in pairs(h.__abpres) do ids[#ids + 1] = id end
    table.sort(ids)
    for _, id in ipairs(ids) do pres_devolve(h.__abpres[id]) end
    h.__abpres = nil
  end
  pres_devolve(h.__pres)
  h.__pres = nil
  M.mortos[h.__h] = h
  M.mortos_ids[#M.mortos_ids + 1] = h.__h
end
do
  local DESTROI = { "DestroyTimer", "RemoveUnit", "RemoveItem", "DestroyTrigger", "DestroyGroup", "DestroyForce",
    "RemoveLocation", "RemoveRect", "RemoveRegion", "DestroyEffect", "DestroyTextTag", "DestroyLightning",
    "DestroyImage", "DestroyUbersplat", "DestroyBoolExpr", "DestroyCondition", "DestroyFilter", "DialogDestroy",
    "DestroyFogModifier", "DestroyMultiboard", "DestroyLeaderboard", "DestroyQuest", "DestroyTimerDialog",
    "RemoveDestructable", "DestroyUnitPool", "DestroyItemPool" }
  for _, nome in ipairs(DESTROI) do
    local f = rawget(_G, nome) or function() end
    rawset(_G, nome, function(h, ...) local r = f(h, ...) __mock_morre(h) return r end)
  end
  for _, nome in ipairs({ "TriggerRemoveAction", "TriggerRemoveCondition" }) do
    local f = rawget(_G, nome) or function() end
    rawset(_G, nome, function(t, x, ...) local r = f(t, x, ...) __mock_morre(x) return r end)
  end
  local add, rem = UnitAddAbility, UnitRemoveAbility
  function UnitAddAbility(u, id)
    local r = add(u, id)
    if r and type(u) == "table" then
      u.__abpres = u.__abpres or {}
      u.__abpres[id] = pres_tira(u.__seq)
    end
    return r
  end
  function UnitRemoveAbility(u, id)
    local r = rem(u, id)
    if r and type(u) == "table" and u.__abpres then
      pres_devolve(u.__abpres[id])
      u.__abpres[id] = nil
    end
    return r
  end
end
function __gc_simulado()
  collectgarbage("collect")
  collectgarbage("collect")
  local livres, resto = 0, {}
  for _, hid in ipairs(M.mortos_ids) do
    if M.mortos[hid] == nil then
      M.hlivres[#M.hlivres + 1] = hid
      livres = livres + 1
    else
      resto[#resto + 1] = hid
    end
  end
  M.mortos_ids = resto
  -- o menor numero sai primeiro (newh tira do fim da lista)
  table.sort(M.hlivres, function(a, b) return a > b end)
  return livres
end
-- [X] (frente X do Lua nao portado, peca 6) O NUMERO DE HANDLE RECICLADO COMO NO MOTOR, sob pedido. Sem isto o
-- simulador NUNCA devolve o numero de uma unidade removida (e o dos outros tipos so' com o coletor da F5): nenhuma
-- sonda via o dado do `YDHT` que fica para quem nasce com o numero de um morto -- mais permissivo que o motor.
-- `__mock_recicla_liga(politica, passo)`: o numero de todo objeto DESTRUIDO (`__mock_morre`: RemoveUnit,
-- DestroyTimer, ...) volta a fila quando o coletor do Lua do simulador o recolhe, isto e', quando nenhuma variavel,
-- hashtable ou grupo o segura (o criterio do motor). Diferenca que sobra: a variavel LOCAL nao anulada segura o
-- numero para sempre no motor e aqui nao (recicla MAIS: o limite de cima do risco). `politica`: "menor" (o menor
-- numero livre primeiro, a do `__gc_simulado`) ou "pilha" (o ultimo destruido primeiro); `passo`: de quantos em
-- quantos segundos simulados o coletor passa. Sem chamar, nada muda. Devolve a funcao que conta os devolvidos.
function __mock_recicla_liga(politica, passo)
  if M.recicla_ligada then return function() return M.reciclados or 0 end end
  M.recicla_ligada = true
  M.reciclados = 0
  -- o `byid` segurava todo objeto para sempre (o truque I2U do mapa so' precisa dos vivos)
  setmetatable(M.byid, { __mode = "v" })
  local pilha = politica == "pilha"
  passo = passo or 5.0
  local adv0 = __mock_advance
  local acum = 0.0
  function __mock_advance(s, p)
    local resto = s
    while resto > 1e-9 do
      local c = math.min(resto, 1.0)
      adv0(c, p)
      resto = resto - c
      acum = acum + c
      if acum >= passo then
        acum = 0.0
        if pilha then
          collectgarbage("collect") collectgarbage("collect")
          local fica = {}
          for _, hid in ipairs(M.mortos_ids) do
            if M.mortos[hid] == nil then M.hlivres[#M.hlivres + 1] = hid M.reciclados = M.reciclados + 1
            else fica[#fica + 1] = hid end
          end
          M.mortos_ids = fica
        else
          M.reciclados = M.reciclados + (__gc_simulado() or 0)
        end
      end
    end
  end
  return function() return M.reciclados end
end
-- tempo de vida (UnitApplyTimedLife) so com M.vida_temporizada (cenario --priest-e do mock_lockstep.py): no
-- motor a unidade morre no fim do prazo e o evento de morte dispara
M.vida_temporizada = false
M.vida_fila = {}
function UnitApplyTimedLife(u, buff, dur)
  if not M.vida_temporizada or type(u) ~= "table" then return end
  M.vida_fila[#M.vida_fila + 1] = { u, M.now + (dur or 0.0) }
end
function __mock_vida_tick()
  if not M.vida_temporizada or #M.vida_fila == 0 then return end
  local resto, vence = {}, {}
  for _, e in ipairs(M.vida_fila) do
    if e[2] <= M.now then vence[#vence + 1] = e[1] else resto[#resto + 1] = e end
  end
  M.vida_fila = resto
  for _, u in ipairs(vence) do
    if u.typeid ~= 0 and (u.life or 0) > 0 then __mock_kill(u, nil) end
  end
end
-- [F5:priest] fim

-- [F6:invul] inicio -----------------------------------------------------------------------------
-- O mock nao tinha CONJURACAO: GetSpellAbilityId e companhia eram stubs vazios, entao nao havia como
-- perguntar "o jogador consegue lancar outra skill enquanto a trava segura o heroi?". Aqui esta o
-- caminho do motor, na ordem em que ele acontece:
--
--   1) a ORDEM de conjuracao. Unidade pausada NO MOTOR nao recebe ordem nenhuma -- era assim no 1.28
--      e o mock ja faz isso (dispara_ordem ignora ordem em u.pausado). Unidade segurada por
--      software (pausa da F5) recebe a ordem normalmente.
--   2) a CONJURACAO: EVENT_PLAYER_UNIT_SPELL_EFFECT com o contexto do feitico, que e onde o mapa
--      despacha a skill (Trig_AbilActions -> ExecuteFunc("Trig_<id>Actions")).
--
-- O "stop" que o gatilho de ordem da F5 re-emite NAO cancela a conjuracao aqui, de proposito: o
-- jogador relatou que, com esse gatilho ja no ar, a skill sai assim mesmo. Modelar o contrario faria
-- o simulador discordar do jogo (e do relato) e esconder justamente o furo que ha para fechar.
__spell_abil, __spell_alvo, __spell_x, __spell_y = 0, nil, 0.0, 0.0
function GetSpellAbilityId() return __spell_abil end
function GetSpellAbilityUnit() return __trigger_unit end
function GetSpellAbility() return __conv("ability", __spell_abil) end
function GetSpellTargetUnit() return __spell_alvo end
function GetSpellTargetX() return __spell_x end
function GetSpellTargetY() return __spell_y end
function GetSpellTargetLoc() return newh("location", { x = __spell_x, y = __spell_y }) end

-- custo de mana da habilidade na unidade. No motor o custo e COBRADO antes de o evento de
-- conjuracao chegar ao mapa -- e por isso que recusar a skill no evento deixa a mana gasta.
-- O .slk so tem coluna de custo ate onde o autor preencheu; acima disso o motor cai no ultimo
-- nivel que existe, e o modelo faz o mesmo.
function BlzGetUnitAbilityManaCost(u, id, nivel)
  local tab = __slk_raw and __slk_raw.ability
  local rec = tab and tab[string.pack(">I4", (id or 0) & 0xFFFFFFFF)]
  if rec == nil then return 0 end
  local n = (nivel or 0) + 1
  while n >= 1 do
    local v = rec["cost" .. n]
    if v ~= nil then return math.floor(tonumber(v) or 0) end
    n = n - 1
  end
  return 0
end
function BlzGetAbilityManaCost(id, nivel) return BlzGetUnitAbilityManaCost(nil, id, nivel) end

-- lanca como o jogador lanca. Devolve: ordem aceita, conjuracao despachada, motivo.
__MOCK_RECARGA_SKILL = true   -- [R1F2:astrologer2] o motor comeca a recarga ao conjurar
function __mock_lanca(u, abil, alvo, x, y)
  if u == nil then return false, false, "sem unidade" end
  local id = (type(abil) == "string") and UnitId(abil) or abil
  local ordem = 852000 + (id % 1000)          -- um id de ordem qualquer, so para o evento de ordem
  u.ordem = nil
  local aceita
  if alvo ~= nil then aceita = IssueTargetOrderById(u, ordem, alvo)
  elseif x ~= nil then aceita = IssuePointOrderById(u, ordem, x, y)
  else aceita = IssueImmediateOrderById(u, ordem) end
  if not aceita then return false, false, "pausada no motor: a ordem nao chega na unidade" end
  -- o motor cobra a mana AQUI, antes do evento
  local niv = GetUnitAbilityLevel(u, id)
  if niv < 1 then niv = 1 end
  u.mana = (u.mana or 0.0) - BlzGetUnitAbilityManaCost(u, id, niv - 1)
  local nome = "Trig_" .. __id2s(id) .. "Actions"
  local antes = (__exec_por_nome and __exec_por_nome[nome]) or 0
  local pa, pal, px, py = __spell_abil, __spell_alvo, __spell_x, __spell_y
  __spell_abil, __spell_alvo = id, alvo
  __spell_x, __spell_y = x or GetUnitX(u), y or GetUnitY(u)
  -- [R1F2:astrologer2] A RECARGA DA SKILL comeca aqui, como no motor (o __mock_usa_item_real ja
  -- fazia isso para ITEM; para skill de heroi o mock nao comecava recarga nenhuma, e ai
  -- "BlzGetUnitAbilityCooldownRemaining" respondia 0 o tempo todo). Sem isso nao da para medir o
  -- "-25% de recarga" do item I0J7 na W: o mapa le a recarga que FALTA e a multiplica por 0,75.
  -- O mock continua NAO recusando a ordem por recarga (as sondas lancam de proposito em sequencia).
  if __MOCK_RECARGA_SKILL then
    local cheio = BlzGetUnitAbilityCooldown(u, id, niv - 1)
    if cheio and cheio > 0.0 then BlzStartUnitAbilityCooldown(u, id, cheio) end
  end
  -- [3.o teste da R1] o motor dispara CANALIZACAO e CONJURACAO antes do EFEITO em TODA skill. O mock so'
  -- disparava o efeito, e a skill que prepara estado na canalizacao ficava sem ele: a R da Musketeer (A11L)
  -- cria o relogio de carga no `Trig_Abil_Cast` (EVENT_PLAYER_UNIT_SPELL_CHANNEL, o gatilho 0x153BC143 da
  -- skill) e so' dispara os projeteis no efeito se ele existir. O fim (ENDCAST) nao e' modelado: o mock nao
  -- tem duracao de canalizacao.
  __mock_unit_event(u, EVENT_PLAYER_UNIT_SPELL_CHANNEL)
  __mock_unit_event(u, EVENT_PLAYER_UNIT_SPELL_CAST)
  __mock_unit_event(u, EVENT_PLAYER_UNIT_SPELL_EFFECT)
  __spell_abil, __spell_alvo, __spell_x, __spell_y = pa, pal, px, py
  local depois = (__exec_por_nome and __exec_por_nome[nome]) or 0
  if depois > antes then return true, true, "conjurou" end
  return true, false, "o mapa recusou a conjuracao"
end

-- A BARRA DE COMANDOS. O motor desenha as habilidades que a unidade TEM, na casa que o dado de
-- objeto manda, menos as escondidas (BlzUnitHideAbility / BlzUnitDisableAbility com hideUI). Casa de
-- habilidade escondida continua RESERVADA e sai preta (RELATORIO da F3, secao das casas do painel):
-- e por isso que "sumiu da barra" e "foi removida do heroi" sao coisas diferentes e precisam de
-- medida separada. Habilidade desabilitada SEM esconder continua desenhada, so nao aceita ordem.
do
  local add, rem = UnitAddAbility, UnitRemoveAbility
  function UnitAddAbility(u, id)
    local r = add(u, id)
    if r and type(u) == "table" then
      u.__abordem = u.__abordem or {}
      u.__abordem[#u.__abordem + 1] = id
    end
    return r
  end
  function UnitRemoveAbility(u, id)
    local r = rem(u, id)
    if r and type(u) == "table" and u.__abordem then
      for i = 1, #u.__abordem do
        if u.__abordem[i] == id then table.remove(u.__abordem, i) break end
      end
      if u.__abil_off then u.__abil_off[id] = nil end
    end
    return r
  end
end
function BlzGetUnitAbilityByIndex(u, i)
  if type(u) ~= "table" or u.__abordem == nil then return nil end
  local id = u.__abordem[(i or 0) + 1]
  if id == nil then return nil end
  return __conv("ability", id)
end
function BlzGetAbilityId(ab) return (type(ab) == "table" and (ab.id or ab.__h)) or 0 end  -- [F6] junção: objeto de BlzGetUnitAbility tem .id, o de __conv tem __h
function BlzUnitDisableAbility(u, id, desabilita, esconde)
  if type(u) ~= "table" then return end
  u.__abil_off = u.__abil_off or {}
  if desabilita or esconde then
    u.__abil_off[id] = { desabilita and true or false, esconde and true or false }
  else
    u.__abil_off[id] = nil
  end
end
function BlzUnitHideAbility(u, id, esconde)
  if type(u) ~= "table" then return end
  u.__abil_off = u.__abil_off or {}
  local e = u.__abil_off[id]
  if esconde then u.__abil_off[id] = { e and e[1] or false, true }
  elseif e then u.__abil_off[id] = { e[1], false } if not e[1] then u.__abil_off[id] = nil end end
end
-- USAR ITEM, com a regra do motor que importa aqui: a carga do item so e gasta se a ordem de usar
-- for aceita. Unidade pausada no motor nao recebe a ordem (1.28) e unidade com a habilidade de
-- inventario DESABILITADA tambem nao -- nos dois casos o item continua na mochila. Se a ordem passa,
-- o motor gasta a carga ANTES de mandar o evento de conjuracao, e ai nao ha mais como devolver.
__MOCK_AINV = 1095331446   -- 'AInv'
function __mock_usa_item(u, abil, alvo, x, y)
  if u == nil then return false, false, "sem unidade", 0 end
  u.itens_gastos = u.itens_gastos or 0
  if u.pausado then return false, false, "pausada no motor: a ordem nao chega", u.itens_gastos end
  local off = u.__abil_off and u.__abil_off[__MOCK_AINV]
  if off ~= nil and off[1] then
    return false, false, "inventario desabilitado: o item nem chega a ser usado", u.itens_gastos
  end
  u.itens_gastos = u.itens_gastos + 1          -- carga gasta pelo motor, antes do evento
  local ok, cast = __mock_lanca(u, abil, alvo, x, y)
  return ok, cast, "o motor aceitou a ordem e gastou a carga", u.itens_gastos
end

-- o que o jogador VE na casa de uma habilidade: "icone", "PRETA" (tem a habilidade, escondida:
-- a casa fica reservada e vazia) ou "-" (a habilidade nao esta no heroi: a casa some)
function __invul_casa(u, id)
  if type(u) ~= "table" or not u.abil[id] then return "-" end
  local e = u.__abil_off and u.__abil_off[id]
  if e and e[2] then return "PRETA" end
  if e and e[1] then return "icone(off)" end
  return "icone"
end
-- [F6:invul] fim --------------------------------------------------------------------------------
-- [R1F1:itemcast] inicio ------------------------------------------------------------------------
-- O mock nao tinha RECARGA de habilidade nem o evento EVENT_PLAYER_UNIT_USE_ITEM: o
-- __mock_usa_item da F6 so contava "cargas gastas" e chamava __mock_lanca. Quer dizer: justamente o
-- que este exploit rouba -- a recarga do item -- nao existia aqui, e por isso a F6 nao o viu.
--
-- O caminho do motor, na ordem que o PROPRIO MAPA revela (Trig_ItemEve_06Actions, registrado em
-- EVENT_PLAYER_UNIT_USE_ITEM, LE a chave 0x7533BDB3 que o ramo de item do Trig_AbilActions
-- (EVENT_PLAYER_UNIT_SPELL_EFFECT) acabou de ESCREVER -- logo o SPELL_EFFECT vem antes):
--
--   1) ORDEM. Unidade pausada no motor nao recebe ordem (1.28); 'AInv' desabilitada idem; item em
--      recarga tambem nao (o motor nem aceita a ordem).
--   2) EVENTO DE ORDEM. O gatilho da F5 ([F5:castui]) re-emite "stop" em quem esta segurado por
--      software: a ordem que fica na unidade vira 851972 e a conjuracao do item e INTERROMPIDA.
--   3) EVENT_PLAYER_UNIT_SPELL_EFFECT -> Trig_AbilActions, ramo de item (slk.ability[id].item == 1):
--      o mapa aplica o EFEITO, ExecuteFunc("Trig_" .. GetAbilityName(id) .. "Actions") -- para o
--      anel de reset, GetAbilityName('A079') == "I0B1", ou seja Trig_I0B1Actions.
--   4) EVENT_PLAYER_UNIT_USE_ITEM -> os 16 gatilhos do mapa + o gancho do framework (carga).
--   5) COMMIT DO MOTOR: a RECARGA do item so comeca se a conjuracao NAO foi interrompida. E o
--      degrau que o "stop" da trava rouba -- e o item volta a ficar disponivel na hora, para sempre.
--
-- __MOCK_ITEM_USEITEM_SEM_COMMIT troca o degrau 4 de lado (USE_ITEM tambem fica de fora quando a
-- conjuracao e interrompida), que e a outra ordem possivel de eventos do motor. As duas medicoes
-- estao no relatorio: a correcao nao depende da ordem, porque ela se ancora na TRAVA e nao no evento.
--
-- ONDE O MOCK ERA MAIS OTIMISTA QUE O MOTOR (a regra do CLAUDE.md: quando o simulador passa e o
-- jogo falha, conserte o mock). A F6 fechou este mesmo furo desabilitando a habilidade de
-- inventario do heroi (BlzUnitDisableAbility(u,'AInv',true,false)) e MODELOU no mock que isso barra
-- a ordem de usar item -- foi a unica parte daquela correcao que o relatorio da F6 marcou como "nao
-- da para medir fora do jogo" (secao "O que nao da para medir", item 4). A R1 foi publicada com ela
-- ligada e o exploit CONTINUA em jogo: o proprio relato deste tema e a medicao que faltava. Ou
-- seja, no Reforged desabilitar 'AInv' NAO impede o uso do item (o clique ordena a habilidade DO
-- ITEM, que e outra habilidade na unidade). O padrao passa a ser esse; com
-- __MOCK_AINV_BARRA_ITEM = true volta a premissa da F6, para comparacao.
__ITEMCAST_STOP = 851972
__MOCK_AINV_BARRA_ITEM = false
__MOCK_ITEM_USEITEM_SEM_COMMIT = false

-- global __nome (e nao local): o escopo principal esta no limite de 200 locais do Lua 5.3
function __mock_cool_tab(u) u.__cool = u.__cool or {} return u.__cool end
function BlzGetAbilityCooldown(id, nivel)
  local tab = __slk_raw and __slk_raw.ability
  local rec = tab and tab[string.pack(">I4", (id or 0) & 0xFFFFFFFF)]
  if rec == nil then return 0.0 end
  local n = (nivel or 0) + 1
  while n >= 1 do
    local v = rec["cool" .. n]
    if v ~= nil then return (tonumber(v) or 0.0) + 0.0 end
    n = n - 1
  end
  return 0.0
end
function BlzGetUnitAbilityCooldown(u, id, nivel) return BlzGetAbilityCooldown(id, nivel) end
function BlzGetUnitAbilityCooldownRemaining(u, id)
  if type(u) ~= "table" then return 0.0 end
  -- (juncao R1F1) codigo thedudeabides emulado pelo tema anticheat: recarga sempre zero
  if __mock_cheat_on ~= nil and __mock_cheat_on(u.owner, "cooldown") then return 0.0 end
  local ate = __mock_cool_tab(u)[id]
  if ate == nil then return 0.0 end
  if ate <= M.now then __mock_cool_tab(u)[id] = nil return 0.0 end
  return ate - M.now
end
function BlzGetUnitAbilityCooldownPercent(u, id)
  local cheio = BlzGetUnitAbilityCooldown(u, id, 0)
  if cheio <= 0.0 then return 0.0 end
  return 100.0 * BlzGetUnitAbilityCooldownRemaining(u, id) / cheio
end
function BlzStartUnitAbilityCooldown(u, id, cd)
  if type(u) ~= "table" then return end
  cd = tonumber(cd) or 0.0
  if cd <= 0.0 then __mock_cool_tab(u)[id] = nil return end
  __mock_cool_tab(u)[id] = M.now + cd
end
function BlzEndUnitAbilityCooldown(u, id) if type(u) == "table" then __mock_cool_tab(u)[id] = nil end end
function BlzSetUnitAbilityCooldownRemaining(u, id, d) BlzStartUnitAbilityCooldown(u, id, d) end
function BlzAdjustUnitAbilityCooldownRemaining(u, id, d)
  BlzStartUnitAbilityCooldown(u, id, BlzGetUnitAbilityCooldownRemaining(u, id) + (tonumber(d) or 0.0))
end

-- contexto do evento de item (o mock so tinha os stubs, que devolviam nil/0)
__manip_item, __manip_unit = nil, nil
function GetManipulatedItem() return __manip_item end
function GetManipulatingUnit() return __manip_unit end

-- a habilidade que o item lanca: cooldownID (ou abilList) do itemdata.slk, os 4 primeiros caracteres
-- [28/09/2026, Dream KK R2-F1, `R2F1_BUGS.md` §2.7] o `__slk_get` da rota JASS indexa a tabela pelo CODIGO de 4 letras (o
-- `it.typeid` e' numero: devolvia nil para todo item) e o `UnitId` do MOTOR_FIEL e' o do motor (0 para rawcode): o
-- SPELL_EFFECT do item saia com a habilidade 0 e o ramo de item do `Trig_AbilActions` nunca rodava numa sonda. Agora o
-- codigo vai como texto e volta pelo `string.unpack`. (O `|n` que o SLK trazia no fim do codigo sai no passo de dados,
-- `common/scripts/slk_fix.py`; aqui os 4 primeiros caracteres ja' o ignoravam.)
function __mock_item_abil(it)
  if type(it) ~= "table" or __slk_get == nil then return 0 end
  local sid = string.pack(">I4", (it.typeid or 0) & 0xFFFFFFFF)
  local s = tostring(__slk_get("item", sid, "cooldownid")
    or __slk_get("item", sid, "abillist") or "")
  s = string.sub(s, 1, 4)
  if #s < 4 then return 0 end
  return (string.unpack(">I4", s))
end

-- Usar item como o jogador usa. Devolve uma tabela com cada degrau medido separadamente, porque
-- e a diferenca entre eles que e o exploit: efeito=true e recarga=0 num uso durante a trava.
function __mock_usa_item_real(u, it)
  local r = { ordem = false, efeito = false, useitem = 0, interrompido = false,
              recarga = 0.0, abil = 0, carga_antes = 0, carga_depois = 0, motivo = "" }
  if u == nil or it == nil then r.motivo = "sem unidade ou sem item" return r end
  local abil = __mock_item_abil(it)
  r.abil = abil
  r.carga_antes = GetItemCharges(it)
  if u.pausado then r.motivo = "pausada no motor: a ordem nao chega" r.carga_depois = r.carga_antes return r end
  local off = u.__abil_off and u.__abil_off[__MOCK_AINV]
  if __MOCK_AINV_BARRA_ITEM and off ~= nil and off[1] then
    r.motivo = "inventario desabilitado: o item nem chega a ser usado"
    r.carga_depois = r.carga_antes
    return r
  end
  local offi = u.__abil_off and u.__abil_off[abil]
  if offi ~= nil and offi[1] then
    r.motivo = "habilidade do item desabilitada: o item nem chega a ser usado"
    r.carga_depois = r.carga_antes
    return r
  end
  if BlzGetUnitAbilityCooldownRemaining(u, abil) > 0.0 then
    r.motivo = "item em recarga: o motor recusa a ordem"
    r.carga_depois = r.carga_antes
    return r
  end
  -- 1/2) a ordem e o evento de ordem (a pausa por software responde com "stop")
  u.ordem = nil
  r.ordem = IssueImmediateOrderById(u, 852000 + (abil % 1000))
  if not r.ordem then r.motivo = "pausada no motor: a ordem nao chega" r.carga_depois = r.carga_antes return r end
  r.interrompido = (u.ordem == __ITEMCAST_STOP)
  -- 3) o efeito: Trig_AbilActions, ramo de item -> Trig_<nome da habilidade>Actions
  local nome = "Trig_" .. tostring(GetAbilityName(abil)) .. "Actions"
  local antes = (__exec_por_nome and __exec_por_nome[nome]) or 0
  local pa, pal, px, py = __spell_abil, __spell_alvo, __spell_x, __spell_y
  __spell_abil, __spell_alvo = abil, nil
  __spell_x, __spell_y = GetUnitX(u), GetUnitY(u)
  __mock_unit_event(u, EVENT_PLAYER_UNIT_SPELL_EFFECT)
  __spell_abil, __spell_alvo, __spell_x, __spell_y = pa, pal, px, py
  r.efeito = ((__exec_por_nome and __exec_por_nome[nome]) or 0) > antes
  -- 4) EVENT_PLAYER_UNIT_USE_ITEM (os 16 gatilhos + o gancho do framework)
  if not (r.interrompido and __MOCK_ITEM_USEITEM_SEM_COMMIT) then
    local pi, pu = __manip_item, __manip_unit
    __manip_item, __manip_unit = it, u
    r.useitem = __mock_unit_event(u, EVENT_PLAYER_UNIT_USE_ITEM)
    __manip_item, __manip_unit = pi, pu
  end
  -- 5) o commit do motor: a recarga so comeca se a conjuracao nao foi interrompida
  if not r.interrompido then
    BlzStartUnitAbilityCooldown(u, abil, BlzGetUnitAbilityCooldown(u, abil, 0))
  end
  r.recarga = BlzGetUnitAbilityCooldownRemaining(u, abil)
  r.carga_depois = GetItemCharges(it)
  r.motivo = r.interrompido and "conjuracao interrompida pelo stop da trava" or "uso completo"
  return r
end

-- UnitUseItem* por script: o mapa nao chama nenhuma das cinco hoje (contado no war3map.j), mas o
-- mock as deixava como stub devolvendo false, e ai a varredura "item por script durante a trava"
-- nao media nada. Aqui elas usam o item pelo mesmo caminho do jogador.
function UnitUseItem(u, it) return __mock_usa_item_real(u, it).ordem end
function UnitUseItemPoint(u, it, x, y) return UnitUseItem(u, it) end
function UnitUseItemPointLoc(u, it, l) return UnitUseItem(u, it) end
function UnitUseItemTarget(u, it, alvo) return UnitUseItem(u, it) end
function UnitUseItemDestructable(u, it, d) return UnitUseItem(u, it) end
-- [R1F1:itemcast] fim ---------------------------------------------------------------------------

-- [28/09/2026] o CONTEXTO dos disparos de evento do mock, para o `GetExpiredTimer()` fiel ao motor (o bloco dele, perto
-- do `DestroyTimer`): cada disparo de gatilho de EVENTO roda com `__ctx = "evento"`, e o gatilho de evento de relogio
-- (`__trigger_event` = EVENT_GAME_TIMER_EXPIRED no `__mock_fire`) com "relogio"; o contexto de fora volta depois, mesmo
-- com erro. Os disparos: o `__mock_fire` (dano, sincronia, tecla, ordem, entrada, dialogo, relogio), a morte, o evento de
-- unidade, a remocao e o chat.
do
  local function no_contexto(nome, qual)
    local f = _G[nome]
    if type(f) ~= "function" then return end
    _G[nome] = function(...)
      local pc = __ctx
      __ctx = qual and qual() or "evento"
      local r = table.pack(pcall(f, ...))
      __ctx = pc
      if not r[1] then error(r[2], 0) end
      return table.unpack(r, 2, r.n)
    end
  end
  no_contexto("__mock_fire", function()
    return (__trigger_event ~= nil and __trigger_event == EVENT_GAME_TIMER_EXPIRED) and "relogio" or "evento"
  end)
  for _, n in ipairs({ "__mock_kill", "__mock_unit_event", "__mock_unit_removed", "__mock_say" }) do no_contexto(n) end
end
'''

