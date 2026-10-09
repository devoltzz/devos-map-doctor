



do



local BITS = math.maxinteger > 2147483647 and 24 or 12
local B, MASCARA = 1 << BITS, (1 << BITS) - 1
local floor, tointeger, schar, sbyte, sformat = math.floor, math.tointeger, string.char, string.byte, string.format
local mt = {}
mt.__index = mt

local function poda(a)
  local n = #a
  while n > 1 and a[n] == 0 do a[n] = nil n = n - 1 end
  if n == 0 then a[1] = 0 end
  return a
end

local function cria(t) return setmetatable(poda(t), mt) end

local function de_inteiro(x)
  x = tointeger(x) or floor(x)
  if x < 0 then x = -x end
  local t = {}
  repeat t[#t + 1] = x & MASCARA x = x >> BITS until x == 0
  return cria(t)
end

local function compara(a, b)
  if #a ~= #b then return #a < #b and -1 or 1 end
  for i = #a, 1, -1 do
    if a[i] ~= b[i] then return a[i] < b[i] and -1 or 1 end
  end
  return 0
end

local function soma(a, b)
  local r, vai = {}, 0
  for i = 1, math.max(#a, #b) do
    local t = (a[i] or 0) + (b[i] or 0) + vai
    r[i] = t & MASCARA
    vai = t >> BITS
  end
  if vai > 0 then r[#r + 1] = vai end
  return cria(r)
end

local function subtrai(a, b)
  local r, em = {}, 0
  for i = 1, #a do
    local t = a[i] - (b[i] or 0) - em
    if t < 0 then t = t + B em = 1 else em = 0 end
    r[i] = t
  end
  return cria(r)
end

local function multiplica(a, b)
  local r = {}
  for i = 1, #a + #b do r[i] = 0 end
  for i = 1, #a do
    local ai, vai = a[i], 0
    if ai ~= 0 then
      for j = 1, #b do
        local t = r[i + j - 1] + ai * b[j] + vai
        r[i + j - 1] = t & MASCARA
        vai = t >> BITS
      end
      local k = i + #b
      while vai > 0 do
        local t = r[k] + vai
        r[k] = t & MASCARA
        vai = t >> BITS
        k = k + 1
      end
    end
  end
  return cria(r)
end

local function desloca_esq(a, s)
  if s == 0 then local c = {} for i = 1, #a do c[i] = a[i] end c[#a + 1] = 0 return c end
  local r, vai = {}, 0
  for i = 1, #a do
    local t = (a[i] << s) | vai
    r[i] = t & MASCARA
    vai = t >> BITS
  end
  r[#a + 1] = vai
  return r
end

local function desloca_dir(a, s, n)
  local r = {}
  for i = 1, n do
    local t = a[i] >> s
    if s > 0 and i < n then t = t | ((a[i + 1] << (BITS - s)) & MASCARA) end
    r[i] = t
  end
  return r
end


local function divide(a, b)
  if compara(a, b) < 0 then return cria({ 0 }), cria({ table.unpack(a) }) end
  local n = #b
  if n == 1 then
    local d, q, resto = b[1], {}, 0
    for i = #a, 1, -1 do
      local t = (resto << BITS) | a[i]
      q[i] = t // d
      resto = t % d
    end
    return cria(q), cria({ resto })
  end
  local s, topo = 0, b[n]
  while topo < (B >> 1) do topo = topo << 1 s = s + 1 end
  local v = desloca_esq(b, s)
  v[#v] = nil
  local u = desloca_esq(a, s)
  local m = #a - n
  local q = {}
  local vn, vn1 = v[n], v[n - 1]
  for j = m, 0, -1 do
    local num = (u[j + n + 1] << BITS) | u[j + n]
    local qh, rh = num // vn, num % vn
    while qh >= B or qh * vn1 > ((rh << BITS) | u[j + n - 1]) do
      qh = qh - 1
      rh = rh + vn
      if rh >= B then break end
    end
    local em, vai = 0, 0
    for i = 1, n do
      local p = qh * v[i] + vai
      vai = p >> BITS
      local t = u[i + j] - (p & MASCARA) - em
      if t < 0 then t = t + B em = 1 else em = 0 end
      u[i + j] = t
    end
    local t = u[j + n + 1] - vai - em
    if t < 0 then
      u[j + n + 1] = t + B
      qh = qh - 1
      local c = 0
      for i = 1, n do
        local w = u[i + j] + v[i] + c
        u[i + j] = w & MASCARA
        c = w >> BITS
      end
      u[j + n + 1] = (u[j + n + 1] + c) & MASCARA
    else
      u[j + n + 1] = t
    end
    q[j + 1] = qh
  end
  return cria(q), cria(desloca_dir(u, s, n))
end

local function novo(x)
  if getmetatable(x) == mt then return cria({ table.unpack(x) }) end
  if type(x) == "number" then return de_inteiro(x) end
  if type(x) == "string" then
    local r = de_inteiro(0)
    local dez = de_inteiro(10)
    for d in x:gmatch("%d") do r = soma(multiplica(r, dez), de_inteiro(tonumber(d))) end
    return r
  end
  return de_inteiro(0)
end

local function de_bytes(s)
  local r, acc, nb = {}, 0, 0
  for i = #s, 1, -1 do
    acc = acc | (sbyte(s, i) << nb)
    nb = nb + 8
    while nb >= BITS do
      r[#r + 1] = acc & MASCARA
      acc = acc >> BITS
      nb = nb - BITS
    end
  end
  if nb > 0 or #r == 0 then r[#r + 1] = acc end
  return cria(r)
end

local function para_bytes(a)
  local t, acc, nb = {}, 0, 0
  for i = 1, #a do
    acc = acc | (a[i] << nb)
    nb = nb + BITS
    while nb >= 8 do
      t[#t + 1] = schar(acc & 0xFF)
      acc = acc >> 8
      nb = nb - 8
    end
  end
  if nb > 0 then t[#t + 1] = schar(acc & 0xFF) end
  local s = table.concat(t):reverse()
  s = s:gsub("^%z+", "")
  return s
end

local function arg(x) if getmetatable(x) == mt then return x end return novo(x) end

function mt.add(a, b) return soma(a, arg(b)) end
function mt.sub(a, b) b = arg(b) if compara(a, b) < 0 then return de_inteiro(0) end return subtrai(a, b) end
function mt.mul(a, b) return multiplica(a, arg(b)) end
function mt.div(a, b) return (divide(a, arg(b))) end
function mt.mod(a, b) local _, r = divide(a, arg(b)) return r end
function mt.powmod(a, e, m)
  e, m = arg(e), arg(m)
  local r = de_inteiro(1)
  local _, base = divide(a, m)
  for i = 1, #e do
    local w = e[i]
    for _ = 1, BITS do
      if w & 1 == 1 then local _, x = divide(multiplica(r, base), m) r = x end
      w = w >> 1
      local _, y = divide(multiplica(base, base), m)
      base = y
    end
  end
  return r
end
function mt.cmp(a, b) return compara(a, arg(b)) end
function mt.tobin(a) return para_bytes(a) end
function mt.tohex(a)
  return (para_bytes(a):gsub(".", function(c) return sformat("%02x", sbyte(c)) end))
end
function mt.tostring(a)
  if #a == 1 and a[1] == 0 then return "0" end
  local partes, x, mil = {}, a, de_inteiro(1000000)
  while not (#x == 1 and x[1] == 0) do
    local q, r = divide(x, mil)
    local v = 0
    for i = #r, 1, -1 do v = v * B + r[i] end
    partes[#partes + 1] = v
    x = q
  end
  local s = tostring(partes[#partes])
  for i = #partes - 1, 1, -1 do s = s .. sformat("%06d", partes[i]) end
  return s
end
mt.__tostring = mt.tostring
mt.__add, mt.__sub, mt.__mul, mt.__mod, mt.__idiv = mt.add, mt.sub, mt.mul, mt.mod, mt.div
mt.__eq = function(a, b) return compara(a, b) == 0 end
mt.__lt = function(a, b) return compara(a, b) < 0 end
mt.__le = function(a, b) return compara(a, b) <= 0 end




local function sha1(msg)
  local orig = __ydwe_original_de and __ydwe_original_de(msg, 1)
  if orig then return orig end
  msg = tostring(msg or "")
  local h0, h1, h2, h3, h4 = 0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476, 0xC3D2E1F0
  local len = #msg
  msg = msg .. schar(0x80) .. string.rep(schar(0), (55 - len) % 64) .. string.pack(">I8", len * 8)
  local function rol(x, n) return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF end
  for bloco = 1, #msg, 64 do
    local w = {}
    for i = 0, 15 do w[i] = string.unpack(">I4", msg, bloco + i * 4) end
    for i = 16, 79 do w[i] = rol(w[i - 3] ~ w[i - 8] ~ w[i - 14] ~ w[i - 16], 1) end
    local a, b, c, d, e = h0, h1, h2, h3, h4
    for i = 0, 79 do
      local f, k
      if i < 20 then f = (b & c) | ((~b) & d) k = 0x5A827999
      elseif i < 40 then f = b ~ c ~ d k = 0x6ED9EBA1
      elseif i < 60 then f = (b & c) | (b & d) | (c & d) k = 0x8F1BBCDC
      else f = b ~ c ~ d k = 0xCA62C1D6 end
      local t = (rol(a, 5) + (f & 0xFFFFFFFF) + e + k + w[i]) & 0xFFFFFFFF
      e, d, c, b, a = d, c, rol(b, 30), a, t
    end
    h0 = (h0 + a) & 0xFFFFFFFF h1 = (h1 + b) & 0xFFFFFFFF h2 = (h2 + c) & 0xFFFFFFFF
    h3 = (h3 + d) & 0xFFFFFFFF h4 = (h4 + e) & 0xFFFFFFFF
  end
  return string.pack(">I4I4I4I4I4", h0, h1, h2, h3, h4)
end

__ydwe_bignum = {
  new = novo, bin = de_bytes, hex = function(s)

    if getmetatable(s) == mt then s = para_bytes(s) end
    return (tostring(s or ""):gsub(".", function(c) return sformat("%02X", sbyte(c)) end))
  end,
  powmod = function(a, e, m) return arg(a):powmod(e, m) end,
  tostring = function(a) return arg(a):tostring() end,
  tobin = function(a) return arg(a):tobin() end,
  sha1 = sha1,
}
end
