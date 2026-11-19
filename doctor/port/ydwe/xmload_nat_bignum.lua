



do
  local N = __xm_nat or {}
  __xm_nat = N
  local function C() return __xm_ctx end
  local function val(id) local c = C() return c.BIG[id] or 0.0 end
  local function live(id) return id ~= nil and id ~= 0 and C().BIG[id] ~= nil end
  local function new(v) return C().new_big(v) end
  local function op(a, o, b)
    local f = C().BIG_OP[o]
    if f == nil then return 0.0 end
    return f(a, b)
  end
  local function cmp(a, o, b)
    local f = C().BIG_CMP[o]
    return f ~= nil and f(a, b) or false
  end
  local function clamp_int(v)
    v = math.floor(v)
    if v ~= v then return 0 end
    if v > 2147483647 then return 2147483647 end
    if v < -2147483648 then return -2147483648 end
    return math.tointeger(v) or 0
  end
  N.XMStringToBigNum = function(s)
    local v = tonumber(s ~= nil and tostring(s):match('^%s*(.-)%s*$') or '')
    return new(v or 0.0)
  end
  N.XMBigNumCreateInt = function(n) return new((n or 0) + 0.0) end
  N.XMBigNumOperation2 = function(a, o, b)
    if not live(a) or not live(b) then return new(0.0) end
    return new(op(val(a), o, val(b)))
  end
  N.XMBigNumOperationInt2 = function(a, o, r)
    if not live(a) then return new(0.0) end
    return new(op(val(a), o, (r or 0) + 0.0))
  end
  N.XMBigNumCompareInt = function(a, o, r)
    if not live(a) then return false end
    return cmp(val(a), o, (r or 0) + 0.0)
  end
  N.XMBigNumCompareReal = function(a, o, r)
    if not live(a) then return false end
    return cmp(val(a), o, (r or 0.0) + 0.0)
  end
  N.XMBigNumDiv = function(a, b)
    local d = val(b)
    if d == 0 then return 0.0 end
    return val(a) / d + 0.0
  end
  N.XMBigNumFloor = function(a) return new(math.floor(val(a)) + 0.0) end
  N.XMBigNumMod = function(a, b)
    local d = val(b)
    if d == 0 then return new(0.0) end
    return new(math.fmod(val(a), d))
  end

  N.XMBigNumRandomSync = function(lo, hi)
    local a, b = val(lo), val(hi)
    if b < a then a, b = b, a end
    return new(C().common.GetRandomReal(a, b) + 0.0)
  end
  N.HaveSavedXMBignum = function(t, p, c) return C().common.HaveSavedInteger(t, p, c) end
  N.RemoveSavedXMBignum = function(t, p, c) C().common.RemoveSavedInteger(t, p, c) end
end
