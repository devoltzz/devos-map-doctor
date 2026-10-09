# Puts a script in a normal form and undoes what a map optimizer did to the game functions.
import re

from doctor.script import jass_ast as existing


REF_SCRIPTS = ('common.j', 'blizzard.j')
_RAWCODE_CHARS = frozenset(b'0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz')
_PURE_PREFIXES = ('Get', 'Is', 'Convert', 'BlzGet', 'BlzIs', 'I2', 'R2', 'S2', 'Load', 'Have', 'StringLength',
                  'SubString', 'StringCase', 'StringHash', 'OrderId', 'UnitId', 'AbilityId', 'Sin', 'Cos', 'Tan',
                  'Asin', 'Acos', 'Atan', 'SquareRoot', 'Pow', 'Deg2Rad', 'Rad2Deg', 'Version')
_PURE_NAMES = frozenset(('Player', 'Condition', 'Filter'))
_CREATED_TYPES = frozenset(('location', 'group', 'force', 'rect', 'region', 'timer', 'trigger', 'effect'))
_DEPTH = 16
PLAYERS = {12: {'GetBJMaxPlayers': 12, 'GetBJPlayerNeutralVictim': 13, 'GetBJPlayerNeutralExtra': 14,
                'GetBJMaxPlayerSlots': 16, 'GetPlayerNeutralPassive': 15, 'GetPlayerNeutralAggressive': 12},
           24: {'GetBJMaxPlayers': 24, 'GetBJPlayerNeutralVictim': 25, 'GetBJPlayerNeutralExtra': 26,
                'GetBJMaxPlayerSlots': 28, 'GetPlayerNeutralPassive': 27, 'GetPlayerNeutralAggressive': 24}}
NEUTRAL_PLAYERS = {12: 'PLAYER_NEUTRAL_AGGRESSIVE', 13: 'bj_PLAYER_NEUTRAL_VICTIM', 14: 'bj_PLAYER_NEUTRAL_EXTRA',
                   15: 'PLAYER_NEUTRAL_PASSIVE'}
FIRST_EDITOR_OF_24 = 6060


ORDER_IDS = {
    'smart': 851971, 'stop': 851972, 'stunned': 851973, 'cancel': 851976, 'setrally': 851980, 'getitem': 851981,
    'attack': 851983, 'attackground': 851984, 'attackonce': 851985, 'move': 851986, 'AImove': 851988,
    'patrol': 851990, 'holdposition': 851993, 'build': 851994, 'humanbuild': 851995, 'orcbuild': 851996,
    'nightelfbuild': 851997, 'undeadbuild': 851998, 'resumebuild': 851999, 'skillmenu': 852000, 'dropitem': 852001,
    'moveslot1': 852002, 'moveslot2': 852003, 'moveslot3': 852004, 'moveslot4': 852005, 'moveslot5': 852006,
    'moveslot6': 852007, 'useslot1': 852008, 'useslot2': 852009, 'useslot3': 852010, 'useslot4': 852011,
    'useslot5': 852012, 'useslot6': 852013, 'detectaoe': 852015, 'resumeharvesting': 852017, 'harvest': 852018,
    'returnresources': 852020, 'autoharvestgold': 852021, 'autoharvestlumber': 852022, 'neutraldetectaoe': 852023,
    'repair': 852024, 'repairon': 852025, 'repairoff': 852026, 'revive': 852039, 'selfdestruct': 852040,
    'selfdestructon': 852041, 'selfdestructoff': 852042, 'board': 852043, 'forceboard': 852044, 'load': 852046,
    'unload': 852047, 'unloadall': 852048, 'unloadallinstant': 852049, 'loadcorpse': 852050,
    'loadcorpseinstant': 852053, 'unloadallcorpses': 852054, 'defend': 852055, 'undefend': 852056, 'dispel': 852057,
    'flare': 852060, 'heal': 852063, 'healon': 852064, 'healoff': 852065, 'innerfire': 852066, 'innerfireon': 852067,
    'innerfireoff': 852068, 'invisibility': 852069, 'militiaconvert': 852071, 'militia': 852072,
    'militiaoff': 852073, 'polymorph': 852074, 'slow': 852075, 'slowon': 852076, 'slowoff': 852077,
    'tankdroppilot': 852079, 'tankloadpilot': 852080, 'tankpilot': 852081, 'townbellon': 852082,
    'townbelloff': 852083, 'avatar': 852086, 'unavatar': 852087, 'blizzard': 852089, 'divineshield': 852090,
    'undivineshield': 852091, 'holybolt': 852092, 'massteleport': 852093, 'resurrection': 852094,
    'thunderbolt': 852095, 'thunderclap': 852096, 'waterelemental': 852097, 'berserk': 852100, 'bloodlust': 852101,
    'bloodluston': 852102, 'bloodlustoff': 852103, 'devour': 852104, 'evileye': 852105, 'ensnare': 852106,
    'ensnareon': 852107, 'ensnareoff': 852108, 'healingward': 852109, 'lightningshield': 852110, 'purge': 852111,
    'standdown': 852113, 'stasistrap': 852114, 'chainlightning': 852119, 'earthquake': 852121, 'farsight': 852122,
    'mirrorimage': 852123, 'shockwave': 852125, 'spiritwolf': 852126, 'stomp': 852127, 'whirlwind': 852128,
    'windwalk': 852129, 'unwindwalk': 852130, 'ambush': 852131, 'autodispel': 852132, 'autodispelon': 852133,
    'autodispeloff': 852134, 'barkskin': 852135, 'barkskinon': 852136, 'barkskinoff': 852137, 'bearform': 852138,
    'unbearform': 852139, 'corrosivebreath': 852140, 'loadarcher': 852142, 'mounthippogryph': 852143,
    'cyclone': 852144, 'detonate': 852145, 'eattree': 852146, 'entangle': 852147, 'entangleinstant': 852148,
    'faeriefire': 852149, 'faeriefireon': 852150, 'faeriefireoff': 852151, 'ravenform': 852155,
    'unravenform': 852156, 'recharge': 852157, 'rechargeon': 852158, 'rechargeoff': 852159, 'rejuvination': 852160,
    'renew': 852161, 'renewon': 852162, 'renewoff': 852163, 'roar': 852164, 'root': 852165, 'unroot': 852166,
    'entanglingroots': 852171, 'flamingarrowstarg': 852173, 'flamingarrows': 852174, 'unflamingarrows': 852175,
    'forceofnature': 852176, 'immolation': 852177, 'unimmolation': 852178, 'manaburn': 852179,
    'metamorphosis': 852180, 'scout': 852181, 'sentinel': 852182, 'starfall': 852183, 'tranquility': 852184,
    'acolyteharvest': 852185, 'antimagicshell': 852186, 'blight': 852187, 'cannibalize': 852188, 'cripple': 852189,
    'curse': 852190, 'curseon': 852191, 'curseoff': 852192, 'freezingbreath': 852195, 'possession': 852196,
    'raisedead': 852197, 'raisedeadon': 852198, 'raisedeadoff': 852199, 'requestsacrifice': 852201,
    'restoration': 852202, 'restorationon': 852203, 'restorationoff': 852204, 'sacrifice': 852205,
    'stoneform': 852206, 'unstoneform': 852207, 'unholyfrenzy': 852209, 'unsummon': 852210, 'web': 852211,
    'webon': 852212, 'weboff': 852213, 'wispharvest': 852214, 'auraunholy': 852215, 'auravampiric': 852216,
    'animatedead': 852217, 'carrionswarm': 852218, 'darkritual': 852219, 'darksummoning': 852220,
    'deathanddecay': 852221, 'deathcoil': 852222, 'deathpact': 852223, 'dreadlordinferno': 852224,
    'frostarmor': 852225, 'frostnova': 852226, 'sleep': 852227, 'darkconversion': 852228, 'darkportal': 852229,
    'fingerofdeath': 852230, 'firebolt': 852231, 'inferno': 852232, 'gold2lumber': 852233, 'lumber2gold': 852234,
    'spies': 852235, 'rainofchaos': 852237, 'rainoffire': 852238, 'request_hero': 852239, 'disassociate': 852240,
    'revenge': 852241, 'soulpreservation': 852242, 'coldarrowstarg': 852243, 'coldarrows': 852244,
    'uncoldarrows': 852245, 'creepanimatedead': 852246, 'creepdevour': 852247, 'creepheal': 852248,
    'creephealon': 852249, 'creephealoff': 852250, 'creepthunderbolt': 852252, 'creepthunderclap': 852253,
    'poisonarrowstarg': 852254, 'poisonarrows': 852255, 'unpoisonarrows': 852256, 'scrollofspeed': 852285,
    'frostarmoron': 852458, 'frostarmoroff': 852459, 'awaken': 852466, 'nagabuild': 852467, 'mount': 852469,
    'dismount': 852470, 'cloudoffog': 852473, 'controlmagic': 852474, 'magicdefense': 852478,
    'magicundefense': 852479, 'magicleash': 852480, 'phoenixfire': 852481, 'phoenixmorph': 852482,
    'spellsteal': 852483, 'spellstealon': 852484, 'spellstealoff': 852485, 'banish': 852486, 'drain': 852487,
    'flamestrike': 852488, 'summonphoenix': 852489, 'ancestralspirit': 852490, 'ancestralspirittarget': 852491,
    'corporealform': 852493, 'uncorporealform': 852494, 'disenchant': 852495, 'etherealform': 852496,
    'unetherealform': 852497, 'spiritlink': 852499, 'unstableconcoction': 852500, 'healingwave': 852501,
    'hex': 852502, 'voodoo': 852503, 'ward': 852504, 'autoentangle': 852505, 'autoentangleinstant': 852506,
    'coupletarget': 852507, 'coupleinstant': 852508, 'decouple': 852509, 'grabtree': 852511, 'manaflareon': 852512,
    'manaflareoff': 852513, 'phaseshift': 852514, 'phaseshifton': 852515, 'phaseshiftoff': 852516,
    'phaseshiftinstant': 852517, 'taunt': 852520, 'vengeance': 852521, 'vengeanceon': 852522, 'vengeanceoff': 852523,
    'vengeanceinstant': 852524, 'blink': 852525, 'fanofknives': 852526, 'shadowstrike': 852527,
    'spiritofvengeance': 852528, 'absorb': 852529, 'avengerform': 852531, 'unavengerform': 852532, 'burrow': 852533,
    'unburrow': 852534, 'devourmagic': 852536, 'flamingattacktarg': 852539, 'flamingattack': 852540,
    'unflamingattack': 852541, 'replenish': 852542, 'replenishon': 852543, 'replenishoff': 852544,
    'replenishlife': 852545, 'replenishlifeon': 852546, 'replenishlifeoff': 852547, 'replenishmana': 852548,
    'replenishmanaon': 852549, 'replenishmanaoff': 852550, 'carrionscarabs': 852551, 'carrionscarabson': 852552,
    'carrionscarabsoff': 852553, 'carrionscarabsinstant': 852554, 'impale': 852555, 'locustswarm': 852556,
    'breathoffrost': 852560, 'frenzy': 852561, 'frenzyon': 852562, 'frenzyoff': 852563, 'mechanicalcritter': 852564,
    'mindrot': 852565, 'neutralinteract': 852566, 'preservation': 852568, 'sanctuary': 852569, 'shadowsight': 852570,
    'spellshield': 852571, 'spellshieldaoe': 852572, 'spirittroll': 852573, 'steal': 852574,
    'attributemodskill': 852576, 'blackarrow': 852577, 'blackarrowon': 852578, 'blackarrowoff': 852579,
    'breathoffire': 852580, 'charm': 852581, 'doom': 852583, 'drunkenhaze': 852585, 'howlofterror': 852588,
    'manashieldon': 852589, 'manashieldoff': 852590, 'monsoon': 852591, 'silence': 852592, 'stampede': 852593,
    'summongrizzly': 852594, 'summonquillbeast': 852595, 'summonwareagle': 852596, 'tornado': 852597,
    'wateryminion': 852598, 'channel': 852600, 'parasite': 852601, 'parasiteon': 852602, 'parasiteoff': 852603,
    'submerge': 852604, 'unsubmerge': 852605, 'neutralspell': 852630, 'militiaunconvert': 852651,
    'clusterrockets': 852652, 'robogoblin': 852656, 'unrobogoblin': 852657, 'summonfactory': 852658,
    'acidbomb': 852662, 'chemicalrage': 852663, 'healingspray': 852664, 'transmute': 852665, 'lavamonster': 852667,
    'soulburn': 852668, 'volcano': 852669, 'incineratearrow': 852670, 'incineratearrowon': 852671,
    'incineratearrowoff': 852672}
_ORDER_NAMES = dict((v, k) for k, v in ORDER_IDS.items())
_ORDERS_BY_ID = {'IssueImmediateOrderById': 'IssueImmediateOrder', 'IssuePointOrderById': 'IssuePointOrder',
                 'IssuePointOrderByIdLoc': 'IssuePointOrderLoc', 'IssueTargetOrderById': 'IssueTargetOrder',
                 'IssueInstantPointOrderById': 'IssueInstantPointOrder',
                 'IssueInstantTargetOrderById': 'IssueInstantTargetOrder',
                 'GroupImmediateOrderById': 'GroupImmediateOrder', 'GroupPointOrderById': 'GroupPointOrder',
                 'GroupPointOrderByIdLoc': 'GroupPointOrderLoc', 'GroupTargetOrderById': 'GroupTargetOrder'}


def players_of(editor_version):
    if editor_version is None:
        return None
    return 24 if editor_version >= FIRST_EDITOR_OF_24 else 12


def bare(e):
    while type(e) is existing.Paren:
        e = e.inner
    return e


def integer_text(value):
    raw = (value & 0xFFFFFFFF).to_bytes(4, 'big')
    if all(b in _RAWCODE_CHARS for b in raw):
        return "'%s'" % raw.decode('ascii')
    return str(value)


def integer_node(value):
    text = integer_text(value)
    if text[0] == "'":
        return existing.Literal('rawcode', text)
    if value < 0:
        return existing.Unary('-', existing.Literal('integer', str(-value)))
    return existing.Literal('integer', text)


def number(e):
    e = bare(e)
    sign = 1
    while type(e) is existing.Unary and e.op in '-+':
        sign = -sign if e.op == '-' else sign
        e = bare(e.operand)
    if type(e) is existing.Literal and (
        e.kind in ('integer', 'real') or (e.kind == 'rawcode' and len(e.text) in (3, 6))
    ):
        return ('real' if e.kind == 'real' else 'integer'), sign * e.value
    return None


def same(a, b):
    a, b = bare(a), bare(b)
    na, nb = number(a), number(b)
    if na is not None or nb is not None:
        return na == nb
    ta = type(a)
    if ta is not type(b):
        return False
    if ta is existing.Name or ta is existing.FuncRef:
        return a.name == b.name
    if ta is existing.Literal:
        return a.kind == b.kind and a.text == b.text
    if ta is existing.Call:
        return a.name == b.name and len(a.args) == len(b.args) and all(same(x, y) for x, y in zip(a.args, b.args))
    if ta is existing.Index:
        return same(a.base, b.base) and same(a.index, b.index)
    if ta is existing.Unary:
        return a.op == b.op and same(a.operand, b.operand)
    if ta is existing.Binary:
        return a.op == b.op and same(a.left, b.left) and same(a.right, b.right)
    return False


class OneLiner(object):
    __slots__ = ('name', 'params', 'body', 'statement', 'return_type', 'linear', 'pure_head')

    def __init__(self, name, params, body, statement, return_type):
        self.name, self.params, self.body, self.statement, self.return_type = name, params, body, statement, return_type
        self.linear = self.pure_head = False


class Reference(object):
    def __init__(self, texts=(), players=None):
        self.constants, self.one_liners, self.returns, self.global_types, self.extends = {}, {}, {}, {}, {}
        self.returned_by, self.natives, self.pure, self.empty = {}, set(), set(), set()
        self.functions, self.signatures = {}, {}
        self._wrappers, self._flat, self._versions = None, {}, None
        self.players, self.mode = players, PLAYERS.get(players, {})
        for text in texts:
            try:
                script = existing.parse(text) if text else None
            except existing.JassSyntaxError:
                script = None
            if script is not None:
                self._take(script)

    def _take(self, script):
        self.extends.update((d.name, d.base) for d in script.types)
        for f in script.natives:
            self.returns.setdefault(f.name, f.return_type)
            self.natives.add(f.name)
            if f.name in _PURE_NAMES or (f.name.startswith(_PURE_PREFIXES) and 'Random' not in f.name and
                                         f.return_type not in _CREATED_TYPES):
                self.pure.add(f.name)
        for g in script.globals:
            self.global_types.setdefault(g.name, g.type)
            if g.is_constant and not g.is_array and g.initializer is not None and g.name not in self.constants:
                v = bare(_Normalizer(self, frozenset()).expr(g.initializer))
                if number(v) is not None or (type(v) is existing.Literal and v.kind in ('boolean', 'string')) or (
                        type(v) is existing.Call and v.name.startswith('Convert') and v.name in self.natives and
                        all(number(a) is not None for a in v.args)):
                    self.constants[g.name] = v
        for f in script.functions:
            self.returns.setdefault(f.name, f.return_type)
            if f.name not in self.functions:
                self.functions[f.name] = f
                self.signatures.setdefault((f.return_type, tuple(t for t, _n in f.params)), []).append(f.name)
            body = [s for s in f.body if type(s) is not existing.CommentStmt]
            if not body and not f.locals and not f.params and f.return_type == 'nothing':
                self.empty.add(f.name)
            if f.locals or len(body) != 1 or f.name in self.one_liners:
                continue
            s = body[0]
            if type(s) is existing.ReturnStmt and s.value is not None:
                one = OneLiner(f.name, [n for _t, n in f.params], s.value, False, f.return_type)
            elif type(s) is existing.CallStmt and f.return_type == 'nothing':
                one = OneLiner(f.name, [n for _t, n in f.params], s.call, True, f.return_type)
            else:
                continue
            self._classify(one)
            self.one_liners[f.name] = one
            v = bare(one.body)
            if not one.params and type(v) is existing.Name and v.name not in self.constants:
                self.returned_by.setdefault(v.name, []).append(f.name)

    def _classify(self, one):
        params = set(one.params)
        events = []

        def walk(e):
            e = bare(e)
            t = type(e)
            if t is existing.Name:
                if e.name in params:
                    events.append(e.name)
                elif e.name not in self.constants:
                    events.append(('read', e.name))
            elif t is existing.Index:
                walk(e.base)
                walk(e.index)
            elif t is existing.Unary:
                walk(e.operand)
            elif t is existing.Binary:
                walk(e.left)
                walk(e.right)
            elif t is existing.Call:
                for a in e.args:
                    walk(a)
                if e.name not in self.pure:
                    events.append(('call', e.name))

        walk(one.body)
        uses = [x for x in events if not isinstance(x, tuple)]
        last = max([k for k, x in enumerate(events) if not isinstance(x, tuple)] + [-1])
        lead = events[:last + 1]
        one.pure_head = not any(isinstance(x, tuple) and x[0] == 'call' for x in lead)
        one.linear = uses == list(one.params) and not any(isinstance(x, tuple) for x in lead)

    def wrappers(self):
        if self._wrappers is None:
            out = {}
            for one in self.one_liners.values():
                body = bare(_Normalizer(self, frozenset(one.params)).expr(one.body))
                h = head(body)
                if h is not None:
                    out.setdefault(h, []).append((one, body))
            self._wrappers = out
        return self._wrappers


def head(e):
    e = bare(e)
    t = type(e)
    if t is existing.Call:
        return 'call', e.name
    if t is existing.Binary:
        return 'binary', e.op
    if t is existing.Name:
        return 'name', e.name
    return None


def kept_head(e, ref):
    e = bare(e)
    if type(e) is not existing.Call:
        return None
    name = e.name
    if name in ref.one_liners or name in _ORDERS_BY_ID or name == 'OrderId' or (not e.args and name in ref.mode):
        return None
    return 'call', name


def unify(pattern, e, params):
    out = {}

    def go(p, x):
        p, x = bare(p), bare(x)
        if type(p) is existing.Name and p.name in params:
            if p.name in out:
                return same(out[p.name], x)
            out[p.name] = x
            return True
        if number(p) is not None or number(x) is not None:
            return same(p, x)
        tp = type(p)
        if tp is not type(x):
            return False
        if tp is existing.Call:
            return p.name == x.name and len(p.args) == len(x.args) and all(go(a, b) for a, b in zip(p.args, x.args))
        if tp is existing.Binary:
            return p.op == x.op and go(p.left, x.left) and go(p.right, x.right)
        if tp is existing.Index:
            return go(p.base, x.base) and go(p.index, x.index)
        if tp is existing.Unary:
            return p.op == x.op and go(p.operand, x.operand)
        return same(p, x)

    return out if go(pattern, e) and all(n in out for n in params) else None


def _rebuilt(e, names):
    t = type(e)
    if t is existing.Paren:
        return _rebuilt(e.inner, names)
    if t is existing.Name:
        return names.get(e.name, e)
    if t is existing.Index:
        return existing.Index(_rebuilt(e.base, names), _rebuilt(e.index, names))
    if t is existing.Unary:
        return existing.Unary(e.op, _rebuilt(e.operand, names))
    if t is existing.Binary:
        return existing.Binary(e.op, _rebuilt(e.left, names), _rebuilt(e.right, names))
    if t is existing.Call:
        return existing.Call(e.name, [_rebuilt(a, names) for a in e.args])
    return e


class _Normalizer(object):
    def __init__(self, ref, stable, simple=None, holes=None, depth=0, aliases=None, frozen=None):
        self.ref, self.stable, self.simple, self.holes, self.depth = ref, stable, simple or {}, holes or {}, depth
        self.aliases, self.frozen = aliases or {}, frozen or {}
        self.inlined = set()

    def expr(self, e):
        t = type(e)
        if t is existing.Paren:
            return self.expr(e.inner)
        if t is existing.Name:
            if e.name not in self.stable:
                if e.name in self.ref.constants:
                    return self.ref.constants[e.name]
                if e.name in self.frozen:
                    return self.frozen[e.name]
            return e
        if t is existing.Literal:
            if e.kind == 'integer' or (e.kind == 'rawcode' and len(e.text) in (3, 6)):
                return integer_node(e.value)
            return e
        if t is existing.Index:
            return existing.Index(self.expr(e.base), self.expr(e.index))
        if t is existing.Unary:
            return self.unary(e.op, self.expr(e.operand))
        if t is existing.Binary:
            return self.binary(e.op, self.expr(e.left), self.expr(e.right))
        if t is existing.Call:
            return self.call(e.name, [self.expr(a) for a in e.args])
        return e

    def unary(self, op, x):
        b = bare(x)
        if op == 'not':
            if type(b) is existing.Unary and b.op == 'not':
                return b.operand
            if type(b) is existing.Literal and b.kind == 'boolean':
                return existing.Literal('boolean', 'false' if b.text == 'true' else 'true')
        elif op == '+' and number(b) is not None:
            return x
        return existing.Unary(op, x)

    def binary(self, op, left, right):
        lb, rb = bare(left), bare(right)
        if op in ('==', '!='):
            for a, b in ((lb, rb), (rb, lb)):
                literal = type(a) is existing.Literal and a.kind == 'boolean'
                if type(b) is existing.Literal and b.kind == 'boolean' and not literal:
                    return a if (b.text == 'true') == (op == '==') else self.unary('not', a)
                if type(b) is existing.Literal and b.kind == 'null' and self.boolean(a):
                    return a if op == '!=' else self.unary('not', a)
        if op == '+' and number(lb) is not None and number(rb) is None:
            if number(lb)[1] < 0:
                positive = lb
                while type(positive) is existing.Unary:
                    positive = bare(positive.operand)
                return existing.Binary('-', right, positive)
            return existing.Binary('+', right, left)
        if op in ('and', 'or') and type(rb) is existing.Binary and rb.op == op:
            return self.binary(op, self.binary(op, left, rb.left), rb.right)
        return existing.Binary(op, left, right)

    def boolean(self, e):
        e = bare(e)
        t = type(e)
        if t is existing.Binary:
            return e.op in ('and', 'or', '==', '!=', '<', '<=', '>', '>=')
        if t is existing.Unary:
            return e.op == 'not'
        if t is existing.Call:
            return self.ref.returns.get(e.name) == 'boolean'
        return t is existing.Literal and e.kind == 'boolean'

    def pure(self, e):
        e = bare(e)
        t = type(e)
        if t is existing.Name:
            return self.holes[e.name][0] if e.name in self.holes else True
        if t is existing.Literal or t is existing.FuncRef:
            return True
        if t is existing.Index:
            return self.pure(e.base) and self.pure(e.index)
        if t is existing.Unary:
            return self.pure(e.operand)
        if t is existing.Binary:
            return self.pure(e.left) and self.pure(e.right)
        if t is existing.Call:
            return e.name in self.ref.pure and all(self.pure(a) for a in e.args)
        return False

    def fixed(self, e):
        e = bare(e)
        if type(e) is existing.Literal or number(e) is not None:
            return True
        if type(e) is existing.Name:
            return self.holes[e.name][1] if e.name in self.holes else e.name in self.stable
        return False

    def call(self, name, args):
        name = self.aliases.get(name, name)
        if not args and name in self.ref.mode:
            return integer_node(self.ref.mode[name])
        if name == 'OrderId' and len(args) == 1:
            a = bare(args[0])
            if type(a) is existing.Literal and a.kind == 'string' and a.text[1:-1] in ORDER_IDS:
                return integer_node(ORDER_IDS[a.text[1:-1]])
        elif name in _ORDERS_BY_ID and len(args) >= 2:
            order = number(args[1])
            if order is not None and order[0] == 'integer' and order[1] in _ORDER_NAMES:
                return existing.Call(
                    _ORDERS_BY_ID[name],
                    [args[0], existing.Literal('string', '"%s"' % _ORDER_NAMES[order[1]])] + list(args[2:]),
                )
        if self.depth >= _DEPTH:
            return existing.Call(name, args)
        if not args and name in self.simple:
            self.inlined.add(name)
            self.depth += 1
            try:
                return self.expr(self.simple[name])
            finally:
                self.depth -= 1
        one = self.ref.one_liners.get(name)
        if one is None or len(args) != len(one.params) or not (
                one.linear or (one.pure_head and all(self.pure(a) for a in args)) or all(self.fixed(a) for a in args)):
            return existing.Call(name, args)
        marks = dict((p, existing.Name('\x00%d' % k)) for k, p in enumerate(one.params))
        holes = dict(('\x00%d' % k, (self.pure(a), self.fixed(a))) for k, a in enumerate(args))
        inner = _Normalizer(self.ref, frozenset(), None, holes, self.depth + 1)
        body = inner.expr(_rebuilt(one.body, marks))
        return self._filled(body, dict(('\x00%d' % k, a) for k, a in enumerate(args)))

    def _filled(self, e, values):
        t = type(e)
        if t is existing.Name:
            return values.get(e.name, e)
        if t is existing.Index:
            return existing.Index(self._filled(e.base, values), self._filled(e.index, values))
        if t is existing.Unary:
            return self.unary(e.op, self._filled(e.operand, values))
        if t is existing.Binary:
            return self.binary(e.op, self._filled(e.left, values), self._filled(e.right, values))
        if t is existing.Call:
            return existing.Call(e.name, [self._filled(a, values) for a in e.args])
        return e


def tests(f):
    if f.locals or f.params or f.return_type != 'boolean':
        return None
    body = [s for s in f.body if type(s) is not existing.CommentStmt]
    if len(body) < 2:
        return None
    last = body[-1]
    end = bare(last.value) if type(last) is existing.ReturnStmt and last.value is not None else None
    if type(end) is not existing.Literal or end.kind != 'boolean':
        return None
    conj = end.text == 'true'
    out = []
    for s in body[:-1]:
        if type(s) is not existing.IfStmt or len(s.branches) != 1:
            return None
        cond, inner = s.branches[0]
        inner = [x for x in inner if type(x) is not existing.CommentStmt]
        ret = bare(inner[0].value) if len(inner) == 1 and type(inner[0]) is existing.ReturnStmt and \
            inner[0].value is not None else None
        if type(ret) is not existing.Literal or ret.kind != 'boolean' or (ret.text == 'true') == conj:
            return None
        cond = bare(cond)
        if conj:
            if type(cond) is not existing.Unary or cond.op != 'not':
                return None
            cond = cond.operand
        out.append(cond)
    return ('and' if conj else 'or'), out


def fold_conditions(script):
    done = []
    for f in script.functions:
        t = tests(f)
        if t is None:
            continue
        op, conds = t
        e = conds[0]
        for c in conds[1:]:
            e = existing.Binary(op, e, c)
        f.body = [existing.ReturnStmt(e, f.body[-1].line)]
        done.append(f.name)
    return done


def _simple_functions(script):
    out = {}
    for f in script.functions:
        if f.params or f.locals or f.return_type != 'boolean':
            continue
        body = [s for s in f.body if type(s) is not existing.CommentStmt]
        if len(body) == 1 and type(body[0]) is existing.ReturnStmt and body[0].value is not None:
            out[f.name] = body[0].value
    return out


def _statements(body, n):
    out = []
    for s in body:
        t = type(s)
        if t is existing.SetStmt:
            s.target, s.value = n.expr(s.target), n.expr(s.value)
        elif t is existing.CallStmt:
            if not s.call.args and s.call.name in n.ref.empty:
                continue
            e = bare(n.expr(s.call))
            s.call = e if type(e) is existing.Call else existing.Call(s.call.name, [n.expr(a) for a in s.call.args])
            if s.call.name == 'DestroyBoolExpr' and len(s.call.args) == 1 and \
                    type(bare(s.call.args[0])) is existing.Literal and bare(s.call.args[0]).kind == 'null':
                continue
        elif t is existing.IfStmt:
            s.branches = [(None if c is None else n.expr(c), _statements(b, n)) for c, b in s.branches]
            if len(s.branches) > 1 and s.branches[-1][0] is None and not [
                    x for x in s.branches[-1][1] if type(x) is not existing.CommentStmt]:
                s.branches = s.branches[:-1]
        elif t is existing.LoopStmt:
            s.body = _statements(s.body, n)
        elif t is existing.ExitWhenStmt:
            s.cond = n.expr(s.cond)
        elif t is existing.ReturnStmt and s.value is not None:
            s.value = n.expr(s.value)
        elif t is existing.DebugStmt:
            inner = _statements([s.stmt], n)
            if not inner:
                continue
        out.append(s)
    return out


def normalize(script, ref=None, inline=True, aliases=None):
    ref = ref if ref is not None else reference()
    aliases = aliases or {}
    with existing._tree_work():
        fold_conditions(script)
        simple = _simple_functions(script) if inline else {}
        inlined = set()
        for item in script.items:
            t = type(item)
            if t is existing.Globals:
                n = _Normalizer(ref, frozenset(), simple, aliases=aliases)
                for d in item.decls:
                    if d.initializer is not None:
                        d.initializer = n.expr(d.initializer)
                inlined |= n.inlined
            elif t is existing.Function and not item.is_native and item.name not in aliases:
                names = frozenset([p for _t, p in item.params] + [d.name for d in item.locals])
                n = _Normalizer(ref, names, dict((k, v) for k, v in simple.items() if k != item.name),
                                aliases=aliases)
                for d in item.locals:
                    if d.initializer is not None:
                        d.initializer = n.expr(d.initializer)
                item.body = _statements(item.body, n)
                inlined |= n.inlined
        maybe = inlined | set(f.name for f in script.functions if f.name in aliases)
        if maybe:
            named = set(x.name for f in script.functions if f.name not in aliases for x in existing.walk(f)
                        if type(x) in (existing.FuncRef, existing.Call))
            gone = maybe - named
            if gone:
                script.items = [i for i in script.items if not (type(i) is existing.Function and i.name in gone)]
                script.functions = [f for f in script.functions if f.name not in gone]
    return script


def _mentions(node):
    return set(x.name for x in existing.walk(node) if type(x) is existing.Name)


class _Globals(object):
    def __init__(self, script, text=None):
        self.types = dict((g.name, g.type) for g in script.globals if not g.is_array)
        found = _native_globals(text) if text is not None else None
        if found is not None:
            frozen, temps = found
            self.frozen = dict((g, existing.Literal('null', 'null')) for g in frozen)
            self.uses = dict((g, [True]) for g in temps)
            return
        assigned = {}
        self.uses = {}
        always = set(f.name for f in script.functions if not f.params and not f.locals and f.return_type == 'boolean'
                     and [(type(s), getattr(bare(s.value), 'text', None) if type(s) is existing.ReturnStmt and
                           s.value is not None else None) for s in f.body if type(s) is not existing.CommentStmt] ==
                     [(existing.ReturnStmt, 'true')])
        for f in script.functions:
            heads = [_mentions(d.initializer) if d.initializer is not None else set() for d in f.locals]
            heads += [_mentions(s) for s in f.body if type(s) is not existing.CommentStmt]
            body = [None] * len(f.locals) + [s for s in f.body if type(s) is not existing.CommentStmt]
            own = set(p for _t, p in f.params) | set(d.name for d in f.locals)
            for x in existing.walk(f):
                if type(x) is existing.SetStmt:
                    t = bare(x.target)
                    assigned.setdefault(t.name if type(t) is existing.Name else bare(t.base).name, []).append(x.value)
            seen = set()
            for k, names in enumerate(heads):
                for g in names - seen - own:
                    if g in self.types:
                        s = body[k]
                        first = (type(s) is existing.SetStmt and type(bare(s.target)) is existing.Name and
                                 bare(s.target).name == g and g not in _mentions(s.value))
                        self.uses.setdefault(g, []).append(first)
                seen |= names
        self.frozen = {}
        for g in script.globals:
            if g.is_array or g.is_constant or g.type not in ('boolexpr', 'filterfunc', 'conditionfunc'):
                continue
            v = bare(g.initializer) if g.initializer is not None else None
            values = assigned.get(g.name)
            if values is None:
                if v is None or (type(v) is existing.Literal and v.kind == 'null'):
                    self.frozen[g.name] = existing.Literal('null', 'null')
            elif len(values) == 1:
                c = bare(values[0])
                a = (
                    bare(c.args[0])
                    if type(c) is existing.Call and c.name in ('Filter', 'Condition') and len(c.args) == 1
                    else None
                )
                if type(a) is existing.FuncRef and a.name in always:
                    self.frozen[g.name] = existing.Literal('null', 'null')

    def temp(self, name):
        return name in self.types and name not in self.frozen and all(self.uses.get(name, [False]))


_STANDARD_NATIVE = [None]


def _standard_native():
    if _STANDARD_NATIVE[0] is None:
        _STANDARD_NATIVE[0] = False
        try:
            from doctor.script import jass_native
            _STANDARD_NATIVE[0] = jass_native.load_standard() or False
        except Exception:
            _STANDARD_NATIVE[0] = False
    return _STANDARD_NATIVE[0]


def _native_globals(text):
    nat = _standard_native()
    if not nat:
        return None
    if text[:1] == existing._BOM:
        text = text[1:]
    enc = existing._native_bytes(text)
    if enc is None:
        return None
    data, latin = enc
    try:
        found = nat[0](data)
    except Exception:
        return None
    if found is None:
        return None
    codec = 'latin-1' if latin else 'utf-8'
    return tuple([x.decode(codec, 'surrogateescape') if not latin else x.decode(codec) for x in items]
                 for items in found)


def _replace_names(node, names):
    for x in existing.walk(node):
        t = type(x)
        if t is existing.SetStmt:
            x.target, x.value = _rebuilt(x.target, names), _rebuilt(x.value, names)
        elif t is existing.CallStmt:
            x.call = _rebuilt(x.call, names)
        elif t is existing.IfStmt:
            x.branches = [(None if c is None else _rebuilt(c, names), b) for c, b in x.branches]
        elif t is existing.ExitWhenStmt:
            x.cond = _rebuilt(x.cond, names)
        elif t is existing.ReturnStmt and x.value is not None:
            x.value = _rebuilt(x.value, names)
        elif t is existing.LocalDecl and x.initializer is not None:
            x.initializer = _rebuilt(x.initializer, names)


def _without_null_sets(body, locals_, after=frozenset(), looped=False, undone=None):
    out = []
    for k, st in enumerate(body):
        t = type(st)
        if t is existing.SetStmt and type(bare(st.target)) is existing.Name and bare(st.target).name in locals_ and \
                type(bare(st.value)) is existing.Literal and bare(st.value).kind == 'null':
            x = bare(st.target).name
            nxt = next(
                (
                    s
                    for s in body[k + 1 :]
                    if not (
                        type(s) is existing.SetStmt
                        and type(bare(s.target)) is existing.Name
                        and bare(s.target).name in locals_
                        and type(bare(s.value)) is existing.Literal
                        and bare(s.value).kind == 'null'
                    )
                ),
                None,
            )
            if (type(nxt) is existing.ReturnStmt and (nxt.value is None or x not in _mentions(nxt.value))) or (
                    not looped and x not in after and not any(x in _mentions(s) for s in body[k + 1:])):
                if undone is not None:
                    undone.append('null')
                continue
        later = after | set().union(*[_mentions(s) for s in body[k + 1:]]) if body[k + 1:] else after
        if t is existing.IfStmt:
            st.branches = [(c, _without_null_sets(b, locals_, later, looped, undone)) for c, b in st.branches]
        elif t is existing.LoopStmt:
            st.body = _without_null_sets(st.body, locals_, later, True, undone)
        out.append(st)
    return out


def _direct_returns(body, temp, undone=None):
    out = []
    for st in body:
        t = type(st)
        if t is existing.IfStmt:
            st.branches = [(c, _direct_returns(b, temp, undone)) for c, b in st.branches]
        elif t is existing.LoopStmt:
            st.body = _direct_returns(st.body, temp, undone)
        elif t is existing.ReturnStmt and st.value is not None and type(bare(st.value)) is existing.Name and out:
            prev = out[-1]
            g = bare(st.value).name
            if (
                type(prev) is existing.SetStmt
                and type(bare(prev.target)) is existing.Name
                and bare(prev.target).name == g
                and temp(g)
                and g not in _mentions(prev.value)
            ):
                out[-1] = existing.ReturnStmt(prev.value, st.line)
                if undone is not None:
                    undone.append('return')
                continue
        out.append(st)
    return out


def _flat(f, normalizer, names=None, temp=None, undone=None):
    g = existing.parse(existing.unparse(f, comments=False)).functions[0]
    if names:
        _replace_names(g, names)
    params = set(p for _t, p in g.params)
    body = [existing.SetStmt(existing.Name(d.name), d.initializer) for d in g.locals if d.initializer is not None]
    body = _statements(body + [s for s in g.body if type(s) is not existing.CommentStmt], normalizer)
    locals_ = dict((d.name, d.type) for d in g.locals)
    while body and type(body[0]) is existing.SetStmt and type(bare(body[0].target)) is existing.Name:
        x = bare(body[0].target).name
        rest = existing.Function()
        rest.body = body[1:]
        reads = [y for y in existing.walk(rest) if type(y) is existing.Name and y.name == x]
        sets = [
            y
            for y in existing.walk(rest)
            if type(y) is existing.SetStmt and type(bare(y.target)) is existing.Name and bare(y.target).name == x
        ]
        k = next((i for i, st in enumerate(body[1:]) if x in _mentions(st)), None)
        if x not in locals_ or len(reads) != 1 or sets or k is None or not normalizer.pure(body[0].value) or not all(
                type(st) is existing.SetStmt and normalizer.pure(st.value) for st in body[1:1 + k]):
            break
        _replace_names(rest, {x: body[0].value})
        body = rest.body
        del locals_[x]
    body = _without_null_sets(body, locals_, undone=undone)
    if temp is not None:
        body = _direct_returns(body, temp, undone)
    out = []
    for st in body:
        if type(st) is existing.CallStmt and st.call.name == 'DestroyBoolExpr' and len(st.call.args) == 1 and \
                type(bare(st.call.args[0])) is existing.Name and bare(st.call.args[0]).name in params:
            continue
        out.append(st)
    return out, locals_


class _Twin(object):
    def __init__(self, b_names, f_locals, f_params, globals_, known, own=None, bound=None):
        self.b_names, self.f_locals, self.f_params = b_names, f_locals, f_params
        self.globals, self.known = globals_, known
        self.map, self.taken = {}, set()
        self.own, self.bound, self.new = own or {}, bound if bound is not None else {}, {}

    def name(self, b, f):
        if b in self.own:
            g = self.bound.get(b, self.new.get(b))
            if g is not None:
                return g == f
            if f in self.f_locals or f in self.f_params or self.globals.types.get(f) != self.own[b] or \
                    f in self.bound.values() or f in self.new.values():
                return False
            self.new[b] = f
            return True
        if b in self.b_names:
            if b in self.map:
                return self.map[b] == f
            t = self.b_names[b]
            if f in self.taken:
                return False
            if self.f_locals.get(f) == t or (f not in self.f_locals and f not in self.f_params and
                                              self.globals.types.get(f) == t and self.globals.temp(f)):
                self.map[b] = f
                self.taken.add(f)
                return True
            return False
        return b == f and f not in self.f_locals and f not in self.f_params

    def expr(self, b, f):
        b, f = bare(b), bare(f)
        if number(b) is not None or number(f) is not None:
            return same(b, f)
        t = type(b)
        if t is not type(f):
            return False
        if t is existing.Name:
            return self.name(b.name, f.name)
        if t is existing.Call:
            return (b.name == f.name or self.known.get(f.name) == b.name) and len(b.args) == len(f.args) and all(
                self.expr(x, y) for x, y in zip(b.args, f.args))
        if t is existing.Index:
            return self.expr(b.base, f.base) and self.expr(b.index, f.index)
        if t is existing.Unary:
            return b.op == f.op and self.expr(b.operand, f.operand)
        if t is existing.Binary:
            return b.op == f.op and self.expr(b.left, f.left) and self.expr(b.right, f.right)
        if t is existing.FuncRef:
            return b.name == f.name
        return t is existing.Literal and b.kind == f.kind and b.text == f.text

    def body(self, bs, fs):
        if len(bs) != len(fs):
            return False
        for b, f in zip(bs, fs):
            t = type(b)
            if t is not type(f):
                return False
            if t is existing.SetStmt:
                ok = self.expr(b.target, f.target) and self.expr(b.value, f.value)
            elif t is existing.CallStmt:
                ok = self.expr(b.call, f.call)
            elif t is existing.IfStmt:
                ok = len(b.branches) == len(f.branches) and all(
                    ((c1 is None) == (c2 is None)) and (c1 is None or self.expr(c1, c2)) and self.body(
                        [x for x in b1 if type(x) is not existing.CommentStmt],
                        [x for x in b2 if type(x) is not existing.CommentStmt])
                    for (c1, b1), (c2, b2) in zip(b.branches, f.branches))
            elif t is existing.LoopStmt:
                ok = self.body([x for x in b.body if type(x) is not existing.CommentStmt],
                               [x for x in f.body if type(x) is not existing.CommentStmt])
            elif t is existing.ExitWhenStmt:
                ok = self.expr(b.cond, f.cond)
            elif t is existing.ReturnStmt:
                ok = (b.value is None) == (f.value is None) and (b.value is None or self.expr(b.value, f.value))
            else:
                ok = False
            if not ok:
                return False
        return True


OPTIMIZER_VERSIONS = """
globals
    timer opt_timer
    real opt_x
    real opt_y
endglobals
function PolledWait takes real duration returns nothing
    local real timeRemaining
    local real st = TimerGetElapsed(opt_timer)
    if st <= 0 then
        set opt_timer = CreateTimer()
        call TimerStart(opt_timer, 1000000, false, null)
    endif
    if (duration > 0) then
        loop
            set timeRemaining = duration - TimerGetElapsed(opt_timer) + st
            exitwhen timeRemaining <= 0
            if (timeRemaining > bj_POLLED_WAIT_SKIP_THRESHOLD) then
                call TriggerSleepAction(0.1 * timeRemaining)
            else
                call TriggerSleepAction(bj_POLLED_WAIT_INTERVAL)
            endif
        endloop
    endif
endfunction
function EnumDestructablesInCircleBJFilter takes nothing returns boolean
    local real dx = GetDestructableX(GetFilterDestructable()) - opt_x
    local real dy = GetDestructableY(GetFilterDestructable()) - opt_y
    return dx * dx + dy * dy <= bj_enumDestructableRadius
endfunction
function EnumDestructablesInCircleBJFilter__2 takes nothing returns boolean
    local destructable d = GetFilterDestructable()
    local real dx = GetDestructableX(d) - opt_x
    local real dy = GetDestructableY(d) - opt_y
    return dx * dx + dy * dy <= bj_enumDestructableRadius
endfunction
function EnumDestructablesInCircleBJ takes real radius, location loc, code actionFunc returns nothing
    local rect r
    if (radius >= 0) then
        set opt_x = GetLocationX(loc)
        set opt_y = GetLocationY(loc)
        set bj_enumDestructableRadius = radius * radius
        set r = Rect(opt_x - radius, opt_y - radius, opt_x + radius, opt_y + radius)
        call EnumDestructablesInRect(r, filterEnumDestructablesInCircleBJ, actionFunc)
        call RemoveRect(r)
    endif
endfunction
function EnumDestructablesInCircleBJ__2 takes real radius, location loc, code actionFunc returns nothing
    local rect r
    if (radius >= 0) then
        set opt_x = GetLocationX(loc)
        set opt_y = GetLocationY(loc)
        set bj_enumDestructableRadius = radius * radius
        set r = Rect(opt_x - bj_enumDestructableRadius, opt_y - bj_enumDestructableRadius, \
opt_x + bj_enumDestructableRadius, opt_y + bj_enumDestructableRadius)
        call EnumDestructablesInRect(r, filterEnumDestructablesInCircleBJ, actionFunc)
        call RemoveRect(r)
    endif
endfunction
function PolarProjectionBJ takes location source, real dist, real angle returns location
    local real x = angle * bj_DEGTORAD
    return Location(GetLocationX(source) + dist * Cos(x), GetLocationY(source) + dist * Sin(x))
endfunction
function GetUnitsOfTypeIdAll takes integer unitid returns group
    local group g = CreateGroup()
    call GroupEnumUnitsOfType(g, UnitId2String(unitid), null)
    return g
endfunction
function UnitDropItem takes unit inUnit, integer inItemID returns item
    local item droppedItem
    if (inItemID == -1) then
        return null
    endif
    set droppedItem = CreateItem(inItemID, GetUnitX(inUnit) + GetRandomReal(-32, 32), \
GetUnitY(inUnit) + GetRandomReal(-32, 32))
    call SetItemDropID(droppedItem, GetUnitTypeId(inUnit))
    call UpdateStockAvailability(droppedItem)
    return droppedItem
endfunction
function WidgetDropItem takes widget inWidget, integer inItemID returns item
    if (inItemID == -1) then
        return null
    endif
    return CreateItem(inItemID, GetWidgetX(inWidget) + GetRandomReal(-32, 32), \
GetWidgetY(inWidget) + GetRandomReal(-32, 32))
endfunction
function GetRandomSubGroup takes integer count, group sourceGroup returns group
    set bj_randomSubGroupGroup = CreateGroup()
    set bj_randomSubGroupWant = count
    set bj_randomSubGroupTotal = CountUnitsInGroup(sourceGroup)
    if (bj_randomSubGroupWant <= 0 or bj_randomSubGroupTotal <= 0) then
        return bj_randomSubGroupGroup
    endif
    set bj_randomSubGroupChance = I2R(bj_randomSubGroupWant) / I2R(bj_randomSubGroupTotal)
    call ForGroup(sourceGroup, function GetRandomSubGroupEnum)
    return bj_randomSubGroupGroup
endfunction
"""


def _versions(ref):
    if ref._versions is None:
        script = existing.parse(OPTIMIZER_VERSIONS)
        own = dict((g.name, g.type) for g in script.globals)
        out = {}
        for f in script.functions:
            name = f.name.split('__')[0]
            if name not in ref.functions:
                continue
            names = frozenset([p for _t, p in f.params] + [d.name for d in f.locals])
            fs, locals_ = _flat(f, _Normalizer(ref, names))
            out.setdefault((f.return_type, tuple(t for t, _n in f.params)), []).append((name, fs, locals_, f))
        ref._versions = out, own
    return ref._versions


def _reference_flat(ref, b):
    b_own = frozenset([p for _t, p in b.params] + [d.name for d in b.locals])
    one = ref.one_liners.get(b.name)
    if one is None:
        return _flat(b, _Normalizer(ref, b_own))
    call = bare(one.body)
    inner = ref.functions.get(call.name) if type(call) is existing.Call else None
    if inner is None or inner.name in ref.one_liners or len(call.args) != len(inner.params):
        return None
    args = [bare(a) for a in call.args]
    if not all(type(a) is existing.Literal or (type(a) is existing.Name and a.name in b_own) for a in args):
        return None
    taken = set(b_own)
    names = dict((p, a) for (_t, p), a in zip(inner.params, args))
    if taken & set(d.name for d in inner.locals):
        return None
    own = frozenset(b_own | set(d.name for d in inner.locals))
    return _flat(inner, _Normalizer(ref, own), names)


_LONGEST_COPY = 80


class Copies(dict):
    def __init__(self):
        dict.__init__(self)
        self.versions, self.optimized = set(), False


def copies(script, ref=None, text=None):
    ref = ref if ref is not None else reference()
    out = Copies()
    if not ref.functions:
        return out
    versions = out.versions
    with existing._tree_work():
        globals_ = _Globals(script, text)
        by_signature, own_globals = _versions(ref)
        bound, used = {}, {}
        for _round in range(3):
            found = False
            for f in script.functions:
                if f.name in out or f.name in ref.functions or len(f.body) > _LONGEST_COPY:
                    continue
                signature = (f.return_type, tuple(t for t, _n in f.params))
                names = ref.signatures.get(signature, ()) if f.params else ()
                alternatives = by_signature.get(signature, ())
                if not names and not alternatives:
                    continue
                params = set(p for _t, p in f.params)
                own = frozenset([p for _t, p in f.params] + [d.name for d in f.locals])
                undone = []
                fs, f_locals = _flat(f, _Normalizer(ref, own, aliases=out, frozen=globals_.frozen), None,
                                     lambda g: g not in own and globals_.temp(g), undone)
                if not fs:
                    continue
                candidates = []
                for name in names:
                    if name in ref.empty:
                        continue
                    if name not in ref._flat:
                        ref._flat[name] = _reference_flat(ref, ref.functions[name])
                    if ref._flat[name] is not None:
                        candidates.append((name, ref._flat[name][0], ref._flat[name][1], ref.functions[name], False))
                candidates += [(name, bs, b_locals, b, True) for name, bs, b_locals, b in alternatives]
                for name, bs, b_locals, b, version in candidates:
                    twin = _Twin(dict(b_locals), f_locals, params, globals_, out, own_globals if version else None,
                                 bound)
                    twin.map.update((bp, fp) for (_t, bp), (_t2, fp) in zip(b.params, f.params))
                    twin.taken.update(params)
                    twin.b_names.update((bp, t) for t, bp in b.params)
                    if twin.body(bs, fs):
                        out[f.name] = name
                        if version:
                            versions.add(f.name)
                            bound.update(twin.new)
                            used[f.name] = set(bound.values()) & _mentions(f)
                        if version or undone or any(g not in f_locals for g in twin.map.values() if g not in params):
                            out.optimized = True
                        found = True
                        break
            if not found:
                break
        while used:
            mine = set(g for v in used.values() for g in v)
            spoiled = set(g for f in script.functions if f.name not in versions for g in mine & _mentions(f))
            gone = [name for name, v in used.items() if v & spoiled]
            if not gone:
                break
            for name in gone:
                del used[name], out[name]
                versions.discard(name)
    return out


_PLAYER_CALL = re.compile(r'"[^"\\]*(?:\\.[^"\\]*)*"|//[^\n]*|\'[^\'\n]*\'|\bPlayer[ \t]*\([ \t]*'
                          r'(\$[0-9A-Fa-f]+|0[xX][0-9A-Fa-f]+|[0-9]+)[ \t]*\)', re.S)


def symbolic_players(text):
    count = [0]

    def one(m):
        literal = m.group(1)
        if literal is None:
            return m.group(0)
        try:
            value = int(literal[1:], 16) if literal[0] == '$' else int(literal, 16) if literal[:2] in ('0x', '0X') \
                else int(literal, 8) if len(literal) > 1 and literal[0] == '0' else int(literal)
        except ValueError:
            return m.group(0)
        name = NEUTRAL_PLAYERS.get(value)
        if name is None:
            return m.group(0)
        count[0] += 1
        return 'Player(%s)' % name

    return _PLAYER_CALL.sub(one, text), count[0]


def _game_calls(text, names):
    nat = _standard_native()
    enc = existing._native_bytes(text) if nat else None
    if enc is not None:
        data, latin = enc
        codec = 'latin-1' if latin else 'utf-8'
        try:
            done = nat[1](data, dict((k.encode(codec), v.encode(codec)) for k, v in names.items()))
        except Exception:
            done = None
        if done is not None:
            new, calls, used = done
            return (new.decode(codec) if latin else new.decode(codec, 'surrogateescape'), calls,
                    set(x.decode(codec) if latin else x.decode(codec, 'surrogateescape') for x in used))
    return _game_calls_python(text, names)


def _game_calls_python(text, names):
    out, last, prev, calls = [], 0, None, 0
    used = set()
    tokens = list(existing._TOKEN_RE.finditer(text))
    for k, m in enumerate(tokens):
        tok = m.group(1)
        if tok in names:
            nxt = tokens[k + 1].group(1) if k + 1 < len(tokens) else ''
            if prev == 'function' and nxt == 'takes':
                pass
            elif nxt == '(' or prev == 'function':
                out.append(text[last:m.start(1)])
                out.append(names[tok])
                last = m.end(1)
                calls += 1
            else:
                used.add(tok)
        elif tok[:1] == '"' and tok[1:-1] in names:
            used.add(tok[1:-1])
        prev = tok
    out.append(text[last:])
    return ''.join(out), calls, used


def standard(text, players=None):
    report = {'players': players, 'neutral_players': 0, 'copies': {}, 'versions': [], 'calls': 0, 'removed': []}
    if players == 12:
        text, report['neutral_players'] = symbolic_players(text)
    try:
        script = existing.parse(text)
    except existing.JassSyntaxError:
        return text, report
    found = copies(script, reference(players=players), text)
    if not found or not found.optimized:
        return text, report
    spans = dict((f.name, (f.line, f.end_line)) for f in script.functions if f.name in found)
    text, report['calls'], used = _game_calls(text, found)
    report['copies'] = dict(found)
    report['versions'] = sorted(found.versions)
    gone = sorted((spans[name] for name in found if name not in used), reverse=True)
    report['removed'] = sorted(name for name in found if name not in used)
    if gone:
        lines = text.split('\n')
        for first, end in gone:
            del lines[first - 1:end]
        text = '\n'.join(lines)
    return text, report


_REFERENCE = {}


def reference(ref_dir=None, players=None):
    ref = _REFERENCE.get((ref_dir, players))
    if ref is None:
        from doctor.triggers import triggerdata
        ref = _REFERENCE[(ref_dir, players)] = Reference([triggerdata.game_script(n, ref_dir) for n in REF_SCRIPTS],
                                                         players)
    return ref


def normal_expr(e, ref=None, stable=frozenset()):
    with existing._tree_work():
        return _Normalizer(ref if ref is not None else reference(), frozenset(stable)).expr(e)

