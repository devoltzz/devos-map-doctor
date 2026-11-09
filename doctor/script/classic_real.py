# How the JASS compiler of the classic game reads a real literal, and the text that gives back a value.
import struct
from fractions import Fraction
from functools import lru_cache


RULES = {1: (1, 'z', 'z'), 2: (1, 'z', 'z'), 3: (0, 'z', 'n'), 4: (1, 'z', 'z'), 5: (-3, 'n', 'z')}
MEASURED_DIGITS = max(RULES)
SAFE_DIGITS = 9


def _f32(x, mode):
    if x == 0:
        return Fraction(0)
    neg = x < 0
    a = -x if neg else x
    e = a.numerator.bit_length() - a.denominator.bit_length()
    if Fraction(2) ** e > a:
        e -= 1
    q = Fraction(2) ** (e - 23)
    m = a / q
    lo = m.numerator // m.denominator
    rem = m - lo
    up = {'n': rem > Fraction(1, 2) or (rem == Fraction(1, 2) and lo % 2 == 1), 'z': False, 'u': rem > 0}[mode]
    r = (lo + up) * q
    return -r if neg else r


def _bits(x):
    return struct.unpack('<i', struct.pack('<f', float(x)))[0]


def _value(bits):
    return Fraction(struct.unpack('<f', struct.pack('<i', bits))[0])


@lru_cache(maxsize=None)
def _factor(n):
    nearest = _bits(_f32(Fraction(1, 10 ** n), 'n'))
    return _value(nearest + RULES[n][0])


@lru_cache(maxsize=4096)
def bits_of(text):
    t = text.strip()
    neg = t.startswith('-')
    t = t.lstrip('-+')
    whole, dot, frac = t.partition('.')
    if not dot or not frac:
        return None
    n = len(frac)
    if n not in RULES:
        return None
    _k, mul, add = RULES[n]
    v = _f32(Fraction(int(whole or '0')) + _f32(Fraction(int(frac)) * _factor(n), mul), add)
    return _bits(-v if neg else v)


@lru_cache(maxsize=4096)
def text_for(bits):
    v = _value(bits)
    neg = v < 0
    a = -v if neg else v
    for n in range(1, MEASURED_DIGITS + 1):
        base = int(a * 10 ** n)
        for total in range(max(0, base - 2), base + 3):
            whole, frac = divmod(total, 10 ** n)
            t = '%s%d.%0*d' % ('-' if neg else '', whole, n, frac)
            if bits_of(t) == bits:
                return t
    return None
