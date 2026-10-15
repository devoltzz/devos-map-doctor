# The diagnostic copy: a map that logs what it started and never finished, and the Lua errors, to CustomMapData while it is played; and the reader of that log.
import os
import re
import shutil



FOLDER = 'DevosMapDoctor'
LOG_VERSION = 'DMD1'
RING = 1000
EVENTS = 300
OPEN_MAX = 80
SCAN_MAX = 4000
INTERVAL = 1.0
LEAF = 64
INIT_FUNCTIONS = 500
INIT_CALLS = 1500
INIT_BUDGET = 3000
WAITS = re.compile(r'\b(TriggerSleepAction|PolledWait|TriggerWaitForSound|TriggerSyncReady|SyncSelections|'
                   r'TriggerWaitOnSleeps|WaitForCondition)\s*\(')
RX_FUNC = re.compile(r'^(\s*)(constant\s+)?function\s+([A-Za-z_]\w*)\s+takes\s+.*?\s+returns\s+(\w+)')
RX_LOCAL = re.compile(r'^\s*local\s')
RX_RETURN = re.compile(r'^(\s*)return\b')
RX_END = re.compile(r'^(\s*)endfunction\b')
RX_CODE = re.compile(r'\bfunction\s+([A-Za-z_]\w*)')
RX_EXEC = re.compile(r'\bExecuteFunc\s*\(\s*"([A-Za-z_]\w*)"\s*\)')
RX_CALL = re.compile(r'^\s*call\s+([A-Za-z_]\w*)\s*\(')
ALWAYS = ('main', 'config', 'InitCustomTriggers', 'RunInitializationTriggers', 'InitGlobals', 'CreateAllUnits',
          'CreateAllItems', 'InitCustomPlayerSlots', 'InitCustomTeams', 'InitAllyPriorities', 'CreateRegions',
          'CreateCameras', 'InitSounds', 'InitUpgrades', 'InitTechTree', 'CreateAllDestructables')


class DiagnoseError(Exception):
    pass


def _safe_name(path):
    base = os.path.splitext(os.path.basename(path))[0]
    s = re.sub(r'[^A-Za-z0-9_-]+', '_', base).strip('_')
    if s == base and len(s) <= 40:
        return s or 'map'
    import zlib
    return '%s_%04x' % ((s or 'map')[:34], zlib.crc32(base.encode('utf-8')) & 0xFFFF)


def _jass_str(s):
    return s.replace('\\', '\\\\').replace('"', '\\"').replace('\r', ' ').replace('\n', ' ')


def _newline(text):
    crlf = text.count('\r\n')
    cr = text.count('\r') - crlf
    lf = text.count('\n') - crlf
    return max((crlf, '\r\n'), (lf, '\n'), (cr, '\r'))[1]


def _functions(lines):
    out = []
    cur = None
    for i, l in enumerate(lines):
        if cur is None:
            m = RX_FUNC.match(l)
            if m:
                cur = [m.group(3), bool(m.group(2)), m.group(4), i]
        elif RX_END.match(l):
            out.append((cur[0], cur[1], cur[2], cur[3], i))
            cur = None
    return out


def _entries(lines, funcs):
    names = set(f[0] for f in funcs)
    out = set(n for n in ALWAYS if n in names)
    out.update(n for n in names if n.startswith('InitTrig_'))
    for l in lines:
        if l.lstrip().startswith('//'):
            continue
        refs = list(RX_CODE.finditer(l))
        if RX_FUNC.match(l):
            refs = refs[1:]
        for m in refs:
            if m.group(1) in names:
                out.add(m.group(1))
        for m in RX_EXEC.finditer(l):
            if m.group(1) in names:
                out.add(m.group(1))
    by = dict((f[0], f) for f in funcs)
    for root in ('main', 'InitCustomTriggers', 'config'):
        f = by.get(root)
        if not f:
            continue
        for l in lines[f[3] + 1:f[4]]:
            m = RX_CALL.match(l)
            if m and m.group(1) in names:
                out.add(m.group(1))
    return out


def _prefix(text):
    k = 1
    while True:
        p = 'DMD_' if k == 1 else 'DMD%d_' % k
        if not re.search(r'\b' + p, text):
            return p
        k += 1


def _lookup(prefix, names):
    funcs = []
    count = [0]

    def leaf_body(lo, hi, ind):
        if lo == hi:
            return ['%sreturn "%s"' % (ind, _jass_str(names[lo - 1]))]
        mid = (lo + hi) // 2
        return (['%sif id <= %d then' % (ind, mid)] + leaf_body(lo, mid, ind + '    ') + ['%selse' % ind] +
                leaf_body(mid + 1, hi, ind + '    ') + ['%sendif' % ind])

    def gen(lo, hi):
        count[0] += 1
        name = '%sN%d' % (prefix, count[0])
        if hi - lo + 1 <= LEAF:
            body = leaf_body(lo, hi, '    ')
        else:
            mid = (lo + hi) // 2
            a, b = gen(lo, mid), gen(mid + 1, hi)
            body = ['    if id <= %d then' % mid, '        return %s(id)' % a, '    endif', '    return %s(id)' % b]
        funcs.append(['function %s takes integer id returns string' % name] + body +
                     ['    return ""', 'endfunction'])
        return name

    top = gen(1, len(names)) if names else None
    out = []
    for f in funcs:
        out += f
    out += ['function %sN takes integer id returns string' % prefix,
            '    if id < 1 or id > %d then' % len(names), '        return "?"', '    endif']
    out += ['    return %s(id)' % top] if top else []
    out += ['    return "?"', 'endfunction']
    return out


def _jass_runtime(p, log_path, header, init_dir=None):
    g = ['hashtable %sht = InitHashtable()' % p,
         'integer array %sri' % p, 'real array %srt' % p, 'integer array %srn' % p,
         'integer %srh = 0' % p, 'integer %src = 0' % p, 'integer %scn = 0' % p, 'integer %stotal = 0' % p,
         'integer %sflushes = 0' % p, 'boolean %smain_done = false' % p,
         'timer %sclock = null' % p, 'timer %stick = null' % p]
    f = '''function {p}T takes nothing returns real
    if {p}clock == null then
        return 0.0
    endif
    return TimerGetElapsed({p}clock)
endfunction
function {p}I takes integer id returns nothing
    local integer c = LoadInteger({p}ht, id, 0)
    if c == LoadInteger({p}ht, id, 1) and not HaveSavedBoolean({p}ht, id, 3) then
        set {p}cn = {p}cn + 1
        call SaveInteger({p}ht, -1, {p}cn, id)
        call SaveBoolean({p}ht, id, 3, true)
    endif
    call SaveInteger({p}ht, id, 0, c + 1)
    call SaveReal({p}ht, id, 2, {p}T())
    set {p}total = {p}total + 1
    if {p}rc > 0 and {p}ri[{p}rh] == id then
        set {p}rn[{p}rh] = {p}rn[{p}rh] + 1
        return
    endif
    set {p}rh = {p}rh + 1
    if {p}rh >= {ring} then
        set {p}rh = 0
    endif
    set {p}ri[{p}rh] = id
    set {p}rt[{p}rh] = {p}T()
    set {p}rn[{p}rh] = 1
    if {p}rc < {ring} then
        set {p}rc = {p}rc + 1
    endif
endfunction
function {p}O takes integer id returns nothing
    call SaveInteger({p}ht, id, 1, LoadInteger({p}ht, id, 1) + 1)
endfunction
function {p}F takes nothing returns nothing
    local integer i = 1
    local integer k = 0
    local integer n = 0
    local integer id
    local integer c
    local integer o
    set {p}flushes = {p}flushes + 1
    call PreloadGenClear()
    call PreloadGenStart()
    call Preload("{header} t=" + R2S({p}T()) + " flush=" + I2S({p}flushes) + " calls=" + I2S({p}total))
    if {p}main_done then
        call Preload("main_done")
    endif
    loop
        exitwhen i > {p}cn or i > {scan}
        set id = LoadInteger({p}ht, -1, i)
        set c = LoadInteger({p}ht, id, 0)
        set o = LoadInteger({p}ht, id, 1)
        if c > o then
            set n = n + 1
            call SaveInteger({p}ht, -1, n, id)
            if k < {open_max} then
                call Preload("open " + {p}N(id) + " " + I2S(c) + " " + I2S(o) + " " + R2S(LoadReal({p}ht, id, 2)))
                set k = k + 1
            endif
        else
            call RemoveSavedBoolean({p}ht, id, 3)
        endif
        set i = i + 1
    endloop
    loop
        exitwhen i > {p}cn
        set n = n + 1
        call SaveInteger({p}ht, -1, n, LoadInteger({p}ht, -1, i))
        set i = i + 1
    endloop
    set {p}cn = n
    set k = {p}rc
    if k > {events} then
        set k = {events}
    endif
    set i = {p}rh - k + 1
    if i < 0 then
        set i = i + {ring}
    endif
    loop
        exitwhen k <= 0
        call Preload("ev " + R2S({p}rt[i]) + " " + {p}N({p}ri[i]) + " " + I2S({p}rn[i]))
        set i = i + 1
        if i >= {ring} then
            set i = 0
        endif
        set k = k - 1
    endloop
    call PreloadGenEnd("{path}")
endfunction
function {p}Start takes nothing returns nothing
    if {p}clock != null then
        return
    endif
    set {p}clock = CreateTimer()
    call TimerStart({p}clock, 1000000.0, false, null)
    set {p}tick = CreateTimer()
    call TimerStart({p}tick, {interval}, true, function {p}F)
endfunction
'''.format(p=p, ring=RING, scan=SCAN_MAX, open_max=OPEN_MAX, events=EVENTS, interval=repr(float(INTERVAL)),
           header=_jass_str(header), path=_jass_str(log_path))
    if init_dir is not None:
        g += ['boolean %slive = true' % p, 'integer %snw = 0' % p]
        f += '''function {p}G takes nothing returns boolean
    if not {p}live then
        return false
    endif
    set {p}nw = {p}nw + 1
    if {p}nw > {budget} then
        if {p}nw == {budget} + 1 then
            call PreloadGenClear()
            call PreloadGenStart()
            call Preload("DMD1 init z budget")
            call PreloadGenEnd("{dir}\\\\z_budget.pld")
        endif
        return false
    endif
    return true
endfunction
'''.format(p=p, budget=INIT_BUDGET, dir=_jass_str(init_dir))
    return g, f.splitlines()


def _string_state(lines):
    is_open = False
    before, after = [], []
    for l in lines:
        before.append(is_open)
        if is_open or '"' in l:
            i, n = 0, len(l)
            while i < n:
                c = l[i]
                if is_open:
                    if c == '\\':
                        i += 2
                        continue
                    if c == '"':
                        is_open = False
                elif c == '"':
                    is_open = True
                elif c == '/' and l[i + 1:i + 2] == '/':
                    break
                i += 1
        after.append(is_open)
    return before, after


def _init_plan(lines, funcs, sb):
    by = dict((f[0], f) for f in funcs)
    roots = [n for n in ALWAYS if n in by] + sorted((n for n in by if n.startswith('InitTrig_')),
                                                    key=lambda n: by[n][3])
    rootset = set(roots)
    hot = set()
    cache = {}

    def scan(name):
        if name in cache:
            return cache[name]
        f = by[name]
        depth = 0
        calls, refs = [], []
        for i in range(f[3] + 1, f[4]):
            l = lines[i]
            s = l.strip()
            if s.startswith('//') or sb[i]:
                continue
            if re.match(r'loop\b', s):
                depth += 1
            elif re.match(r'endloop\b', s):
                depth = max(depth - 1, 0)
            m = RX_CALL.match(l)
            if m:
                calls.append((m.group(1), depth > 0, i))
            for m in RX_EXEC.finditer(l):
                calls.append((m.group(1), depth > 0, None))
            for m in RX_CODE.finditer(l):
                refs.append(m.group(1))
        cache[name] = (calls, refs)
        return cache[name]

    order, seen = [], set()

    def add(n):
        if n in by and n not in seen and not by[n][1]:
            seen.add(n)
            order.append(n)

    for n in roots:
        add(n)
    i = 0
    while i < len(order):
        calls, _refs = scan(order[i])
        for callee, in_loop, _line in calls:
            if in_loop:
                hot.add(callee)
            else:
                add(callee)
        i += 1
    tier1 = len(order)
    for n in list(order[:tier1]):
        for ref in scan(n)[1]:
            add(ref)
    order = [n for n in order if n not in hot or n in rootset]
    skipped = max(len(order) - INIT_FUNCTIONS, 0)
    order = order[:INIT_FUNCTIONS]
    calls_marked = {}
    skipped_calls = 0
    for n in order:
        if n not in rootset:
            continue
        for callee, in_loop, line in scan(n)[0]:
            if line is None or in_loop:
                continue
            if len(calls_marked) >= INIT_CALLS:
                skipped_calls += 1
                continue
            calls_marked[line] = ('%s -> %s' % (n, callee), len(calls_marked))
    return {'funcs': order, 'calls': calls_marked, 'hot': len(hot & set(by)), 'skipped_funcs': skipped,
            'skipped_calls': skipped_calls}


def _init_marker(p, init_dir, kind, label, stem, ind='    '):
    return ['%sif %sG() then' % (ind, p),
            '%s    call PreloadGenClear()' % ind,
            '%s    call PreloadGenStart()' % ind,
            '%s    call Preload("%s")' % (ind, _jass_str('DMD1 init %s %s' % (kind, label))),
            '%s    call PreloadGenEnd("%s")' % (ind, _jass_str('%s\\%s.pld' % (init_dir, stem))),
            '%sendif' % ind]


def instrument_jass(text, log_path, header, mode='entry', init_dir=None):
    nl = _newline(text)
    lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    funcs = _functions(lines)
    by = dict((f[0], f) for f in funcs)
    if 'main' not in by:
        raise DiagnoseError('the script has no main function')
    p = _prefix(text)
    init = mode == 'init'
    if init and not init_dir:
        raise DiagnoseError('the init mode needs the folder of the marker files')
    entries = _entries(lines, funcs)
    chosen = [f for f in funcs if not f[1] and (mode == 'all' or f[0] in entries)]
    if not chosen:
        raise DiagnoseError('no function of the script can be marked')
    ids = {}
    names = []
    for f in chosen:
        body = '\n'.join(lines[f[3] + 1:f[4]])
        names.append(f[0] + ('~w' if WAITS.search(body) else ''))
        ids[f[0]] = len(names)
    sb, sa = _string_state(lines)
    plan = _init_plan(lines, funcs, sb) if init else None
    inits = dict((n, i) for i, n in enumerate(plan['funcs'])) if init else {}
    work = dict((f[0], f) for f in chosen)
    for n in inits:
        work.setdefault(n, by[n])
    for f in sorted(work.values(), key=lambda f: -f[3]):
        name, _c, returns, a, b = f
        n = ids.get(name)
        ix = inits.get(name)

        def exits(ind):
            x = []
            if ix is not None:
                x += _init_marker(p, init_dir, 'x', name, 'x%d' % ix, ind)
            if n is not None:
                x.append('%scall %sO(%d)' % (ind, p, n))
            if name == 'main':
                x.append('%sset %smain_done = true' % (ind, p))
                if init:
                    x.append('%sset %slive = false' % (ind, p))
            return x

        out = []
        for i in range(a + 1, b):
            l = lines[i]
            m = None if sb[i] else RX_RETURN.match(l)
            if m:
                out += exits(m.group(1))
            out.append(l)
            if init and i in plan['calls'] and name in plan['funcs'] and not sb[i] and not sa[i]:
                label, num = plan['calls'][i]
                out += _init_marker(p, init_dir, 's', label, 's%d' % num, re.match(r'\s*', l).group(0))
        if returns == 'nothing':
            out += exits('    ')
        k = 0
        while k < len(out) and (RX_LOCAL.match(out[k]) or not out[k].strip() or out[k].lstrip().startswith('//')):
            k += 1
        while k > 0 and not RX_LOCAL.match(out[k - 1]):
            k -= 1
        mark = []
        if name == 'main':
            mark.append('    call %sStart()' % p)
        if ix is not None:
            if name in ('config', 'main'):
                mark += _init_marker(p, init_dir, 'b', name, 'b_%s' % name)
            mark += _init_marker(p, init_dir, 'e', name, 'e%d' % ix)
        if n is not None:
            mark.append('    call %sI(%d)' % (p, n))
        out = out[:k] + mark + out[k:]
        lines[a + 1:b] = '\n'.join(out).split('\n')
    glob, runtime = _jass_runtime(p, log_path, header + ' functions=%d' % len(names), init_dir if init else None)
    runtime = _lookup(p, names) + runtime
    gi = next((i for i, l in enumerate(lines) if re.match(r'^\s*globals\b', l)), None)
    ge = next((i for i, l in enumerate(lines) if re.match(r'^\s*endglobals\b', l)), None)
    first = next(i for i, l in enumerate(lines) if RX_FUNC.match(l))
    if gi is not None and ge is not None and gi < ge < first:
        lines[ge:ge] = glob
        first += len(glob)
    else:
        lines[first:first] = ['globals'] + glob + ['endglobals']
        first += len(glob) + 2
    lines[first:first] = runtime
    info = {'functions': len(funcs), 'marked': len(names), 'entries': len(entries), 'prefix': p}
    if init:
        info['init'] = {'functions': len(plan['funcs']), 'calls': len(plan['calls']), 'hot': plan['hot'],
                        'skipped_functions': plan['skipped_funcs'], 'skipped_calls': plan['skipped_calls']}
    return nl.join(lines), info


LUA_BLOCK = r'''
-- [Devo's Map Doctor] diagnostic copy: the callbacks the game runs inside pcall, the errors and the last events
-- written to CustomMapData\%(path)s once a second
do
  local dmd_header = "%(header)s"
  local dmd_names, dmd_ring, dmd_head, dmd_count, dmd_errs, dmd_errn = {}, {}, 0, 0, {}, {}
  local dmd_clock, dmd_total, dmd_flushes, dmd_main_done = nil, 0, 0, false
%(init_defs)s
  local function dmd_t() if dmd_clock then return TimerGetElapsed(dmd_clock) end return 0.0 end
  local function dmd_clean(s)
    s = tostring(s):gsub('[\r\n]+', ' | '):gsub('"', "'"):gsub('\\', '/')
    return s:sub(1, 220)
  end
  local function dmd_err(where, e)
    local k = dmd_clean(e)
    if not dmd_errn[k] then dmd_errn[k] = 0; dmd_errs[#dmd_errs + 1] = {k, dmd_t(), where} end
    dmd_errn[k] = dmd_errn[k] + 1
  end
  local function dmd_ev(name)
    dmd_total = dmd_total + 1
    local last = dmd_ring[dmd_head]
    if dmd_count > 0 and last and last[2] == name then last[3] = last[3] + 1 return end
    dmd_head = dmd_head %% %(ring)d + 1
    dmd_ring[dmd_head] = {dmd_t(), name, 1}
    if dmd_count < %(ring)d then dmd_count = dmd_count + 1 end
  end
  local function dmd_wrap(kind, f)
    if type(f) ~= "function" then return f end
    return function(...)
      local name = dmd_names[f] or kind
      dmd_ev(name)
      local r = table.pack(pcall(f, ...))
      if not r[1] then dmd_err(name, r[2]) return nil end
      return table.unpack(r, 2, r.n)
    end
  end
  local function dmd_flush()
    dmd_flushes = dmd_flushes + 1
    PreloadGenClear()
    PreloadGenStart()
    Preload(dmd_header .. " t=" .. string.format("%%.3f", dmd_t()) .. " flush=" .. dmd_flushes .. " calls=" .. dmd_total)
    if dmd_main_done then Preload("main_done") end
    for i = 1, math.min(#dmd_errs, 80) do
      local e = dmd_errs[i]
      Preload("err " .. dmd_errn[e[1]] .. " " .. string.format("%%.3f", e[2]) .. " " .. dmd_clean(e[3]) .. ": " .. e[1])
    end
    local k = math.min(dmd_count, %(events)d)
    local i = dmd_head - k
    for _ = 1, k do
      i = i %% %(ring)d + 1
      local x = dmd_ring[i]
      if x then Preload("ev " .. string.format("%%.3f", x[1]) .. " " .. dmd_clean(x[2]) .. " " .. x[3]) end
    end
    PreloadGenEnd("%(path)s")
  end
  local function dmd_hooks()
    for k, v in pairs(_G) do
      if type(v) == "function" and type(k) == "string" then dmd_names[v] = k end
    end
    for _, n in ipairs({"TriggerAddAction", "ForGroup", "ForForce", "EnumItemsInRect", "EnumDestructablesInRect"}) do
      local old = _G[n]
      if old then
        _G[n] = function(a, b, c) if c ~= nil then return old(a, b, dmd_wrap(n, c)) end return old(a, dmd_wrap(n, b)) end
      end
    end
    for _, n in ipairs({"Condition", "Filter"}) do
      local old = _G[n]
      if old then _G[n] = function(f) return old(dmd_wrap(n, f)) end end
    end
    local ts = TimerStart
    if ts then TimerStart = function(t, d, per, f) return ts(t, d, per, dmd_wrap("TimerStart", f)) end end
  end
  local function dmd_wrap_config(f)
    return function(...)
      dmd_mark("b", "config", "b_config")
      local ok, e = pcall(f, ...)
      if not ok then dmd_err("config", e) dmd_mark("r", "config", "r_config") else dmd_mark("x", "config", "x_config") end
    end
  end
  local function dmd_wrap_main(f)
    return function(...)
      if not dmd_clock then
        dmd_clock = CreateTimer()
        TimerStart(dmd_clock, 1000000.0, false, nil)
        local tick = CreateTimer()
        TimerStart(tick, %(interval)s, true, function()
          local ok, e = pcall(dmd_flush)
          if not ok then dmd_err("the log writer", e) end
        end)
        dmd_hooks()
      end
      dmd_mark("b", "main", "b_main")
      dmd_ev("main")
      local ok, e = pcall(f, ...)
      if not ok then dmd_err("main", e) dmd_mark("r", "main", "r_main") else dmd_main_done = true dmd_mark("x", "main", "x_main") end
      dmd_live = false
    end
  end
%(tail)s
end
'''
LUA_INIT_OFF = '''  local dmd_live = true
  local function dmd_mark() end'''
LUA_INIT_ON = '''  local dmd_live, dmd_nw, dmd_idx = true, 0, 0
  local dmd_dir = "%(init_dir)s"
  local function dmd_put(kind, label, stem)
    PreloadGenClear()
    PreloadGenStart()
    Preload("DMD1 init " .. kind .. " " .. label)
    PreloadGenEnd(dmd_dir .. stem .. ".pld")
  end
  local function dmd_mark(kind, label, stem)
    if not dmd_live then return end
    dmd_nw = dmd_nw + 1
    if dmd_nw > %(budget)d then
      if dmd_nw == %(budget)d + 1 then dmd_put("z", "budget", "z_budget") end
      return
    end
    dmd_put(kind, label, stem)
  end
  local function dmd_init_wrap(name, f)
    if dmd_idx >= %(cap)d then return f end
    dmd_idx = dmd_idx + 1
    local stem = tostring(dmd_idx)
    return function(...)
      if not dmd_live then return f(...) end
      dmd_mark("e", name, "e" .. stem)
      local r = table.pack(f(...))
      dmd_mark("x", name, "x" .. stem)
      return table.unpack(r, 1, r.n)
    end
  end'''
LUA_TAIL_AFTER = '''  if config then config = dmd_wrap_config(config) end
  main = dmd_wrap_main(main)'''
LUA_TAIL_BEFORE = '''  local dmd_mt = getmetatable(_G) or {}
  local dmd_old = dmd_mt.__newindex
  dmd_mt.__newindex = function(t, k, v)
    if type(v) == "function" and (k == "main" or k == "config") then
      v = (k == "main") and dmd_wrap_main(v) or dmd_wrap_config(v)
    end
    if dmd_old then return dmd_old(t, k, v) end
    rawset(t, k, v)
  end
  setmetatable(_G, dmd_mt)'''
LUA_TAIL_BEFORE_INIT = '''  local dmd_mt = getmetatable(_G) or {}
  local dmd_old = dmd_mt.__newindex
  dmd_mt.__newindex = function(t, k, v)
    if type(v) == "function" and type(k) == "string" then
      if k == "main" then v = dmd_wrap_main(v)
      elseif k == "config" then v = dmd_wrap_config(v)
      else v = dmd_init_wrap(k, v) end
    end
    if dmd_old then return dmd_old(t, k, v) end
    rawset(t, k, v)
  end
  setmetatable(_G, dmd_mt)
  dmd_mark("b", "script", "b_script")'''


def instrument_lua(text, log_path, header, before=False, interval=INTERVAL, ring=RING, init_dir=None):
    if not re.search(r'(?<![\w.:])function\s+main\s*\(|(?<![\w.:])main\s*=(?!=)', text):
        raise DiagnoseError('the script has no main function')
    if init_dir:
        before = True
        defs = LUA_INIT_ON % {'init_dir': init_dir.replace('\\', '\\\\') + '\\\\', 'budget': INIT_BUDGET,
                              'cap': INIT_FUNCTIONS}
        tail = LUA_TAIL_BEFORE_INIT
    else:
        defs = LUA_INIT_OFF
        tail = LUA_TAIL_BEFORE if before else LUA_TAIL_AFTER
    block = LUA_BLOCK % {'path': log_path.replace('\\', '\\\\'), 'header': header.replace('"', "'"),
                         'ring': int(ring), 'events': min(EVENTS, int(ring)), 'interval': repr(float(interval)),
                         'tail': tail, 'init_defs': defs}
    nl = _newline(text)
    block = block.replace('\n', nl)
    info = {'functions': 0, 'marked': 0, 'entries': 0, 'where': 'start' if before else 'end'}
    if init_dir:
        info['init'] = {'functions': INIT_FUNCTIONS, 'calls': 0, 'hot': 0, 'skipped_functions': 0, 'skipped_calls': 0}
    if before:
        head = block.lstrip('\r\n') + nl
        shift = head.count('\n') + (head.count('\r') if nl == '\r' else 0)
        head = head.replace('"' + header.replace('"', "'") + '"',
                            '"' + header.replace('"', "'") + ' lineshift=%d"' % shift, 1)
        return head + text, info
    return text.rstrip('\r\n') + nl + block, info


def make(path, out_path, mode='entry', doctor='', progress=None):
    p = progress or (lambda *_a: None)
    out = {'state': 'failed', 'error': None, 'language': None, 'log': None, 'init_folder': None, 'marked': 0,
           'functions': 0, 'entries': 0, 'mode': mode, 'syntax': None, 'output': None}
    if os.path.normcase(os.path.abspath(path)) == os.path.normcase(os.path.abspath(out_path)):
        out['error'] = 'The output must be a new file: the map itself is never written.'
        return out
    from doctor.fix import cheatpacks
    from doctor.viewers import map_files
    from doctor.mpq import mpqadd
    p('Reading the script')
    s = map_files.script(path)
    lang = s.get('language')
    out['language'] = lang
    if lang not in ('jass', 'lua'):
        out['error'] = {'kkwe': 'The script is the KK platform\'s compiled form: port the map first (Port), then make '
                                'the diagnostic copy of the ported map.',
                        'j2b': 'The script is compiled (j2b): port the map first (Port), then make the diagnostic copy '
                               'of the ported map.'}.get(lang, 'The map script is empty or unreadable.')
        return out
    if cheatpacks._api(mpqadd, 'format', 'format')(path) != 0:
        out['error'] = 'The archive header is not a normal MPQ v1 header (a protected map): fix it first (Fix map).'
        return out
    name = s.get('name')
    try:
        data = cheatpacks._read_file(cheatpacks._open_map(path), name) or b''
    except BaseException as e:
        if isinstance(e, KeyboardInterrupt):
            raise
        data = b''
    text = data.decode('utf-8', 'surrogateescape')
    if not text.strip():
        out['error'] = 'The map script is empty or unreadable.'
        return out
    if mode not in ('entry', 'all', 'init'):
        out['error'] = 'Unknown mode "%s" (entry, all or init).' % mode
        return out
    log_name = _safe_name(out_path)
    log_path = FOLDER + '\\' + log_name + '.pld'
    init_dir = FOLDER + '\\' + log_name + '_init' if mode == 'init' else None
    header = '%s lang=%s mode=%s map=%s doctor=%s' % (
        LOG_VERSION,
        lang,
        mode if lang == 'jass' or init_dir else 'calls',
        log_name,
        re.sub(r'\s+', '_', doctor or '-'),
    )
    p('Marking the functions')
    try:
        if lang == 'jass':
            new, info = instrument_jass(text, log_path, header, mode, init_dir)
        else:
            new, info = instrument_lua(text, log_path, header, init_dir=init_dir)
    except DiagnoseError as e:
        out['error'] = 'The diagnostic copy was not made: %s.' % e
        return out
    out.update(info)
    out['log'] = log_path
    out['init_folder'] = init_dir
    p('Checking the syntax')
    if lang == 'jass':
        ok, det, sem = cheatpacks._pjass_check(new, path, original=text, mesclado=new)
        if sem is True:
            ok = False
    else:
        ok, det = cheatpacks._lua_check(new)
        if not ok:
            new, info = instrument_lua(text, log_path, header, before=True, init_dir=init_dir)
            out.update(info)
            ok, det = cheatpacks._lua_check(new)
    out['syntax'] = {'ok': bool(ok), 'detail': det}
    if not ok:
        out['error'] = 'The marked script does not pass the syntax check: %s' % det
        return out
    p('Writing the map')
    parte = cheatpacks._parte(out_path)
    try:
        shutil.copyfile(path, parte)
        with cheatpacks._calado():
            cheatpacks._adiciona(parte, [(name, new.encode('utf-8', 'surrogateescape'))], [])
        p('Checking the result')
        if cheatpacks._read_file(cheatpacks._open_map(parte), name) != new.encode('utf-8', 'surrogateescape'):
            raise RuntimeError('the script did not come back from the map as it was written')
        conf = cheatpacks._check_map(path, parte, [name])
        dif = conf.get('different') or conf.get('different') or conf.get('differs') or []
        missing = conf.get('missing_items') or conf.get('missing') or []
        if dif or missing:
            raise RuntimeError('the check: %d file(s) different, %d missing' % (len(dif), len(missing)))
        os.replace(parte, out_path)
    except BaseException as e:
        if isinstance(e, KeyboardInterrupt):
            raise
        if os.path.isfile(parte):
            os.remove(parte)
        out['error'] = 'The diagnostic copy was not written: %s' % cheatpacks._error_text(e)
        return out
    out['state'] = 'done'
    out['output'] = out_path
    return out


RX_PRELOAD = re.compile(r'call\s+Preload\(\s*"((?:[^"\\]|\\.)*)"\s*\)')
RX_LUA_LINE = re.compile(r"(war3map\.lua|\[string '[^']*'\]|\[string \"[^\"]*\"\]):(\d+):")


def documents():
    if os.name == 'nt':
        try:
            import ctypes
            buf = ctypes.c_wchar_p()
            guid = (ctypes.c_byte * 16).from_buffer_copy(
                bytes.fromhex('d0 9a d3 fd 8f 23 af 46 ad b4 6c 85 48 03 69 c7'.replace(' ', '')))
            if ctypes.windll.shell32.SHGetKnownFolderPath(guid, 0, None, ctypes.byref(buf)) == 0:
                p = buf.value
                ctypes.windll.ole32.CoTaskMemFree(buf)
                if p:
                    return p
        except Exception:
            pass
    return os.path.join(os.path.expanduser('~'), 'Documents')


def game_folder():
    return os.path.join(documents(), 'Warcraft III')


def log_folder():
    base = os.path.join(game_folder(), 'CustomMapData')
    return os.path.join(base, FOLDER)


RX_INIT = re.compile(r'^DMD\d+ init (\w) (.*)$')
INIT_TOLERANCE_NS = 50000000
INIT_STAGES = ('script', 'config', 'main')
INIT_STAGE_GAP_NS = 300 * 10 ** 9


def init_folder_of(path):
    if os.path.isdir(path):
        return path
    stem = os.path.splitext(path)[0]
    d = stem + '_init'
    return d if os.path.isdir(d) else None


def _describe_init(e):
    k, lab = e['kind'], e['label']
    return {'b': 'began %s' % lab, 'e': 'entered %s' % lab, 'x': 'returned from %s' % lab,
            's': 'the call %s returned' % lab, 'r': '%s raised an error' % lab, 'z': 'the marker budget ran out'}.get(
        k, '%s %s' % (k, lab))


def read_init(folder):
    out = {'folder': folder, 'files': 0, 'events': [], 'stale': 0, 'open': [], 'last': [], 'begin': {},
           'config': 'not started', 'main': 'not started', 'budget': False, 'findings': []}
    ev = []
    try:
        names = sorted(os.listdir(folder))
    except OSError as e:
        out['findings'] = [('bad', 'The marker folder could not be read: %s' % e)]
        return out
    for f in names:
        if not f.lower().endswith('.pld'):
            continue
        fp = os.path.join(folder, f)
        try:
            st = os.stat(fp)
            with open(fp, 'rb') as fh:
                lines = parse_log(fh.read())['lines']
        except OSError:
            continue
        out['files'] += 1
        m = RX_INIT.match(lines[0]) if lines else None
        if m:
            ev.append({'kind': m.group(1), 'label': m.group(2), 'ns': st.st_mtime_ns, 'file': f})
    begins = dict((e['label'], e['ns']) for e in ev if e['kind'] == 'b')
    out['begin'] = begins
    stages = [begins[s] for s in INIT_STAGES if s in begins]
    first = None
    if stages:
        k = max(range(len(stages)), key=lambda i: stages[i])
        first = stages[k]
        for b in reversed(stages[:k]):
            if 0 <= first - b <= INIT_STAGE_GAP_NS:
                first = b
            else:
                break
    if first is not None:
        keep = [e for e in ev if e['ns'] >= first - INIT_TOLERANCE_NS]
        out['stale'] = len(ev) - len(keep)
        ev = keep
    ev.sort(key=lambda e: (e['ns'], e['file']))
    out['events'] = ev
    entered, exited, raised = {}, {}, {}
    for e in ev:
        k, lab = e['kind'], e['label']
        if k == 'e' or (k == 'b' and lab in ('config', 'main')):
            entered[lab] = max(entered.get(lab, 0), e['ns'])
        elif k == 'x':
            exited[lab] = max(exited.get(lab, 0), e['ns'])
        elif k == 'r':
            raised[lab] = max(raised.get(lab, 0), e['ns'])
        elif k == 'z':
            out['budget'] = True
    opens = [(ns, lab) for lab, ns in entered.items() if lab not in raised and (lab not in exited or exited[lab] < ns)]
    opens.sort(reverse=True)
    out['open'] = [lab for _ns, lab in opens]
    for lab in ('config', 'main'):
        if lab in raised:
            st = 'raised'
        elif lab in exited and (lab not in entered or exited[lab] >= entered[lab]):
            st = 'returned'
        elif lab in entered:
            st = 'open'
        else:
            st = 'not started'
        out[lab] = st
    if ev:
        top = ev[-1]['ns']
        out['last'] = [e for e in ev if e['ns'] == top][-4:]
    out['findings'] = _init_findings(out)
    return out


def _init_findings(r):
    f = []
    ev = r['events']
    if not ev:
        f.append(
            (
                'bad',
                'No marker file: the script never started (a script that does not compile looks like this), or '
                'this folder belongs to another map or to a copy that was not played.',
            )
        )
        return f
    m, c = r['main'], r['config']
    if m == 'raised' or c == 'raised':
        f.append(('bad', '%s raised an error: the load went on without the rest of it.' %
                  ('main' if m == 'raised' else 'config')))
    if m == 'returned':
        f.append(('ok', 'main returned: the script\'s load finished (%d marker file(s), %d function(s) entered).'
                  % (len(ev), sum(1 for e in ev if e['kind'] == 'e'))))
    elif r['open']:
        f.append(('bad', 'The script\'s load stopped inside %s: it was entered and never returned. Open frames, '
                         'innermost first: %s. A function that carries no marker (a hot one called from a loop, or one '
                         'past the caps) may be what it was inside.' % (r['open'][0], ', '.join(r['open'][:8]))))
    elif m == 'not started' and c == 'returned':
        f.append(('warn', 'config ran to its end but main never started: the stop is in the engine\'s own load phase '
                          '(object data, terrain, imported files), not inside a script function.'))
    elif m == 'not started' and 'script' in r['begin'] and c == 'not started':
        f.append(('bad', 'The script\'s own top level started but config never did: the stop is in the code at the top '
                         'level of the script (outside every function), or the script failed to load.'))
    elif m != 'returned':
        f.append(('warn', 'main did not return and no frame is open: the markers stop, but the last one is not an '
                          'entry; see the newest marker.'))
    if r['last']:
        idade = _idade(r['last'][-1]['ns'] / 1e9)
        if idade:
            f.append(idade)
        f.append(('muted', 'The newest marker on disk: %s%s.' % (
            '; '.join(_describe_init(e) for e in r['last'][:3]),
            ' (written in the same tick: their order is not known)' if len(r['last']) > 1 else '')))
    if r['budget']:
        f.append(('warn', 'The marker budget (%d writes) ran out: what the script did after that point is not shown.'
                  % INIT_BUDGET))
    if r['stale']:
        f.append(('muted', '%d older file(s) from an earlier run were left out.' % r['stale']))
    f.append(('muted', 'The Doctor cannot tell a hang from a crash: the game closing by itself leaves the same files.'))
    return f


def _idade(mtime):
    import time
    s = time.time() - mtime
    quando = time.strftime('%Y-%m-%d %H:%M', time.localtime(mtime))
    if s > 86400:
        return ('warn', 'These files were written on %s, %d day(s) ago: if the copy was played after that, the game '
                        'did not get to write them this time, and they are from an earlier run.' % (quando, s // 86400))
    return ('muted', 'Written on %s.' % quando)


def logs(limit=20):
    pasta = log_folder()
    out = []
    if os.path.isdir(pasta):
        for f in os.listdir(pasta):
            p = os.path.join(pasta, f)
            try:
                if f.lower().endswith('.pld') and os.path.isfile(p):
                    st = os.stat(p)
                    out.append({'path': p, 'name': f, 'modified': st.st_mtime, 'bytes': st.st_size, 'kind': 'log'})
                elif f.endswith('_init') and os.path.isdir(p):
                    sts = []
                    for x in os.listdir(p):
                        if x.lower().endswith('.pld'):
                            try:
                                sts.append(os.stat(os.path.join(p, x)))
                            except OSError:
                                pass
                    if sts:
                        out.append({'path': p, 'name': f, 'modified': max(x.st_mtime for x in sts),
                                    'bytes': sum(x.st_size for x in sts), 'kind': 'init'})
            except OSError:
                continue
    out.sort(key=lambda x: -x['modified'])
    return out[:limit]


LOG_CAP = 64 << 20


def _unescape(s):
    return re.sub(r'\\(.)', r'\1', s)


def _num(s, kind=float):
    try:
        return kind(s)
    except (TypeError, ValueError):
        return None


def parse_log(data):
    if isinstance(data, bytes):
        data = data.decode('utf-8', 'replace')
    lines = [_unescape(m.group(1)) for m in RX_PRELOAD.finditer(data)]
    header = {}
    if lines and lines[0].startswith('DMD'):
        parts = lines[0].split()
        header['version'] = parts[0]
        for x in parts[1:]:
            if '=' in x:
                k, v = x.split('=', 1)
                header[k] = v
    return {'header': header, 'lines': lines}


def read_log(path):
    out = {'path': path, 'error': None, 'open': [], 'errors': [], 'events': [], 'findings': [], 'main_done': False,
           'init': None}
    folder = init_folder_of(path)
    if os.path.isdir(path):
        return _init_only(out, path)
    try:
        if os.path.getsize(path) > LOG_CAP:
            out['error'] = 'This file is too big to be a log of a diagnostic copy (%d MB).' % (
                os.path.getsize(path) >> 20
            )
            return out
        with open(path, 'rb') as f:
            raw = f.read()
    except OSError as e:
        if folder:
            return _init_only(out, folder)
        out['error'] = 'The log could not be read: %s' % e
        return out
    pl = parse_log(raw)
    h = pl['header']
    if not h.get('version', '').startswith('DMD'):
        out['error'] = 'This is not a log of a diagnostic copy (it does not start with the DMD line).'
        return out
    out.update(map=h.get('map'), language=h.get('lang'), mode=h.get('mode'), doctor=h.get('doctor'),
               time=_num(h.get('t')), flushes=_num(h.get('flush'), int), calls=_num(h.get('calls'), int),
               functions=_num(h.get('functions'), int))
    for l in pl['lines'][1:]:
        parts = l.split(' ')
        if l == 'main_done':
            out['main_done'] = True
        elif parts[0] == 'open' and len(parts) >= 5:
            name = parts[1]
            out['open'].append({'name': name.replace('~w', ''), 'waits': name.endswith('~w'),
                                'started': _num(parts[2], int), 'finished': _num(parts[3], int),
                                'last': _num(parts[4])})
        elif parts[0] == 'err' and len(parts) >= 4:
            rest = l.split(' ', 3)[3]
            shift = _num(h.get('lineshift'), int) or 0
            if shift:
                rest = RX_LUA_LINE.sub(lambda m: '%s:%d:' % (m.group(1), max(int(m.group(2)) - shift, 1)), rest)
            where, _sep, msg = rest.partition(': ')
            out['errors'].append({'times': _num(parts[1], int), 'first': _num(parts[2]), 'where': where,
                                  'message': msg or rest})
        elif parts[0] == 'ev' and len(parts) >= 4:
            out['events'].append({'time': _num(parts[1]), 'name': parts[2].replace('~w', ''),
                                  'times': _num(parts[3], int)})
    out['findings'] = _findings(out)
    try:
        out['findings'].insert(0, _idade(os.path.getmtime(path)))
    except OSError:
        pass
    if folder:
        out['init'] = read_init(folder)
        out['findings'] += [(st, 'Load markers: ' + t) for st, t in out['init']['findings']
                            if not t.startswith('The Doctor cannot tell')]
    return out


def _init_only(out, folder):
    r = read_init(folder)
    name = os.path.basename(folder.rstrip('\\/'))
    out.update(map=name[:-5] if name.endswith('_init') else name, mode='init', init=r, findings=r['findings'])
    return out


def _findings(r):
    f = []
    stopped = [o for o in r['open'] if not o['waits']]
    waiting = [o for o in r['open'] if o['waits']]
    if r.get('language') == 'jass':
        if not r['main_done']:
            deep = sorted((o for o in r['open'] if (o['last'] or 0) <= 0.001), key=lambda o: o['name'] != 'main')
            inner = [o['name'] for o in deep if o['name'] != 'main']
            f.append(('bad', 'The map\'s main function never finished: everything the map sets up after that point '
                             'never ran.' + (' Still open from the start: %s (the last one is where it stopped).'
                                             % ', '.join(inner[-6:]) if inner else '')))
        else:
            f.append(('ok', 'The map\'s main function finished: the map set itself up.'))
        if stopped:
            f.append(('bad', '%d function(s) started more times than they finished and do not wait: their thread most '
                             'likely stopped inside them (the instruction limit, a division by zero, a null value a '
                             'native refuses): %s.' % (len(stopped), ', '.join(
                                 '%s (%d of %d finished)' % (o['name'], o['finished'] or 0, o['started'] or 0)
                                 for o in stopped[:8]))))
        if waiting:
            f.append(('warn', '%d function(s) are still open but wait (TriggerSleepAction, PolledWait): they may '
                              'simply be waiting: %s.' % (len(waiting), ', '.join(o['name'] for o in waiting[:8]))))
        if not stopped and r['main_done']:
            f.append(('ok', 'None of the marked functions stopped halfway.'))
    else:
        if r['errors']:
            f.append(
                ('bad', '%d different Lua error(s); the first: %s' % (len(r['errors']), r['errors'][0]['message']))
            )
        else:
            f.append(('ok', 'No Lua error in the callbacks, main or config.'))
        if not r['main_done']:
            f.append(('bad', 'The map\'s main function did not finish.'))
    if r.get('time') is not None:
        f.append(('muted', 'The log was last written at %.1f s of game time (%s writes, %s marked calls).'
                  % (r['time'], r.get('flushes'), r.get('calls'))))
    return f


def text(r):
    if r.get('error'):
        return r['error']
    out = ['Diagnostic log of %s (%s, Doctor %s)' % (r.get('map'), r.get('language'), r.get('doctor'))]
    for _s, t in r['findings']:
        out.append('- ' + t)
    if r['errors']:
        out.append('Lua errors:')
        out += ['  %dx at %.1f s, %s: %s' % (e['times'] or 0, e['first'] or 0, e['where'], e['message'])
                for e in r['errors']]
    if r['open']:
        out.append('Open functions (started, finished, last start):')
        out += ['  %s%s %s %s %.2f' % (o['name'], ' (waits)' if o['waits'] else '', o['started'], o['finished'],
                                       o['last'] or 0) for o in r['open']]
    if r['events']:
        out.append('The last events (time, function, times in a row):')
        out += ['  %.2f %s x%s' % (e['time'] or 0, e['name'], e['times']) for e in r['events'][-40:]]
    ini = r.get('init')
    if ini and ini['events']:
        out.append('Load markers (%d file(s); the newest 25, oldest first; the order is the files\' write times):'
                   % ini['files'])
        out += ['  ' + _describe_init(e) for e in ini['events'][-25:]]
    return '\n'.join(out)
