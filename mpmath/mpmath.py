from lib import *
from decimal import Decimal

class mpnumeric(object):
    """Base class for mpf and mpc. Calling mpnumeric(x) returns an mpf
    if x can be converted to an mpf (if it is a float, int, mpf, ...),
    and an mpc if x is complex."""
    def __new__(cls, val):
        if isinstance(val, cls):
            return val
        if isinstance(val, complex):
            return mpc(val)
        return mpf(val)

class context(type):
    """Metaclass for mpf and mpc. Holds global working precision."""

    _prec = 53
    _dps = 15
    _rounding = ROUND_HALF_EVEN

    def _setprec(self, n):
        self._prec = max(1, int(n))
        self._dps = max(1, int(round(int(n)/LOG2_10)-1))

    prec = property(lambda self: self._prec, _setprec)

    def _setdps(self, n):
        self._prec = max(1, int(round((int(n)+1)*LOG2_10)))
        self._dps = max(1, int(n))

    dps = property(lambda self: self._dps, _setdps)

    def round_up(self): self._rounding = ROUND_UP
    def round_down(self): self._rounding = ROUND_DOWN
    def round_floor(self): self._rounding = ROUND_FLOOR
    def round_ceiling(self): self._rounding = ROUND_CEILING
    def round_half_down(self): self._rounding = ROUND_HALF_DOWN
    def round_half_up(self): self._rounding = ROUND_HALF_UP
    def round_half_even(self): self._rounding = ROUND_HALF_EVEN

    round_default = round_half_even


inttypes = (int, long)

def _convert(x):
    """Convet x to mpf data"""
    if isinstance(x, float):
        return float_from_pyfloat(x, mpf._prec, mpf._rounding)
    if isinstance(x, inttypes):
        return float_from_int(x, mpf._prec, mpf._rounding)
    if isinstance(x, (Decimal, str)):
        return decimal_to_binary(x, mpf._prec, mpf._rounding)
    raise TypeError("cannot create mpf from " + repr(x))


class mpf(mpnumeric):

    __metaclass__ = context

    def __new__(cls, val=fzero):
        if isinstance(val, mpf):
            return _make_mpf(normalize(val.val[0], val.val[1], \
                cls._prec, cls._rounding))
        elif isinstance(val, tuple):
            return _make_mpf(normalize(val[0], val[1], cls._prec, \
                cls._rounding))
        else:
            return _make_mpf(_convert(val))

    man = property(lambda self: self.val[0])
    exp = property(lambda self: self.val[1])
    bc = property(lambda self: self.val[2])

    def __repr__(s):
        st = "mpf('%s')"
        return st % binary_to_decimal(s.val, mpf._dps+2)

    def __str__(s):
        return binary_to_decimal(s.val, mpf._dps)

    def __hash__(s):
        try:
            # Try to be compatible with hash values for floats and ints
            return hash(float(s))
        except OverflowError:
            # We must unfortunately sacrifice compatibility with ints here. We
            # could do hash(man << exp) when the exponent is positive, but
            # this would cause unreasonable inefficiency for large numbers.
            return hash(self.val)

    def __int__(s):
        return float_to_int(s.val)

    def __float__(s):
        return float_to_pyfloat(s.val)

    def __complex__(s):
        return float(s) + 0j

    def __eq__(s, t):
        if not isinstance(t, mpf):
            if isinstance(t, complex_types):
                return mpc(s) == t
            if isinstance(t, str):
                return False
            try:
                t = mpf(t)
            except Exception:
                return False
        return s.val == t.val

    def __ne__(s, t):
        if not isinstance(t, mpf):
            if isinstance(t, complex_types):
                return mpc(s) != t
            if isinstance(t, str):
                return True
            try:
                t = mpf(t)
            except Exception:
                return True
            t = mpf(t)
        return s.val != t.val

    def __cmp__(s, t):
        if not isinstance(t, mpf):
            t = mpf(t)
        return fcmp(s.val, t.val)

    def __abs__(s):
        return _make_mpf(fabs(s.val, mpf._prec, mpf._rounding))

    def __pos__(s):
        return mpf(s)

    def __neg__(s):
        return _make_mpf(fneg(s.val, mpf._prec, mpf._rounding))

    def __add__(s, t):
        if not isinstance(t, mpf):
            if isinstance(t, inttypes):
                return _make_mpf(fadd(s.val, (t, 0, bitcount(t)), mpf._prec, mpf._rounding))
            if isinstance(t, complex_types):
                return mpc(s) + t
            t = mpf(t)
        return _make_mpf(fadd(s.val, t.val, mpf._prec, mpf._rounding))

    __radd__ = __add__

    def __sub__(s, t):
        if not isinstance(t, mpf):
            if isinstance(t, inttypes):
                return _make_mpf(fsub(s.val, (t, 0, bitcount(t)), mpf._prec, mpf._rounding))
            if isinstance(t, complex_types):
                return mpc(s) - t
            t = mpf(t)
        return _make_mpf(fsub(s.val, t.val, mpf._prec, mpf._rounding))

    def __rsub__(s, t):
        if not isinstance(t, mpf):
            if isinstance(t, inttypes):
                return _make_mpf(fsub((t, 0, bitcount(t)), s.val, mpf._prec, mpf._rounding))
            if isinstance(t, complex_types):
                return t - mpc(s)
            t = mpf(t)
        return _make_mpf(fsub(t.val, s.val, mpf._prec, mpf._rounding))

    def __mul__(s, t):
        if not isinstance(t, mpf):
            if isinstance(t, inttypes):
                return _make_mpf(normalize(s.val[0]*t, s.val[1], mpf._prec, mpf._rounding))
            if isinstance(t, complex_types):
                return mpc(s) * t
            t = mpf(t)
        return _make_mpf(fmul(s.val, t.val, mpf._prec, mpf._rounding))

    __rmul__ = __mul__

    def __div__(s, t):
        if not isinstance(t, mpf):
            if isinstance(t, inttypes):
                return _make_mpf(fdiv(s.val, (t, 0, bitcount(t)), mpf._prec, mpf._rounding))
            if isinstance(t, complex_types):
                return mpc(s) / t
            t = mpf(t)
        return _make_mpf(fdiv(s.val, t.val, mpf._prec, mpf._rounding))

    def __rdiv__(s, t):
        if not isinstance(t, mpf):
            if isinstance(t, inttypes):
                return _make_mpf(fdiv((t, 0, bitcount(t)), s.val, mpf._prec, mpf._rounding))
            if isinstance(t, complex_types):
                return t / mpc(s)
            t = mpf(t)
        return _make_mpf(fdiv(t.val, s.val, mpf._prec, mpf._rounding))

    def __pow__(s, t):
        if isinstance(t, inttypes):
            return _make_mpf(fpow(s.val, t, mpf._prec, mpf._rounding))
        if not isinstance(t, mpf):
            if isinstance(t, complex_types):
                return power(s, t)
            t = mpf(t)
        if t.val == fhalf:
            return sqrt(s)
        intt = int(t)
        if t == intt:
            return _make_mpf(fpow(s.val, intt, mpf._prec, mpf._rounding))
        return power(s, t)

    def sqrt(s):
        return sqrt(s)

    def ae(s, t, rel_eps=None, abs_eps=None):
        """
        Determine whether the difference between s and t is smaller
        than a given epsilon ("ae" is short for "almost equal").

        Both a maximum relative difference and a maximum difference
        ('epsilons') may be specified. The absolute difference is
        defined as |s-t| and the relative difference is defined
        as |s-t|/max(|s|, |t|).

        If only one epsilon is given, both are set to the same value.
        If none is given, both epsilons are set to 2**(-prec+m) where
        prec is the current working precision and m is a small integer.
        """
        if not isinstance(t, mpf):
            t = mpf(t)
        if abs_eps is None and rel_eps is None:
            rel_eps = abs_eps = _make_mpf((1, -mpf._prec+4, 1))
        if abs_eps is None:
            abs_eps = rel_eps
        elif rel_eps is None:
            rel_eps = abs_eps
        diff = abs(s-t)
        if diff <= abs_eps:
            return True
        abss = abs(s)
        abst = abs(t)
        if abss < abst:
            err = diff/abst
        else:
            err = diff/abss
        return err <= rel_eps

    def almost_zero(s, prec):
        """Quick check if |s| < 2**-prec. May return a false negative
        if s is very close to the threshold."""
        return s.bc + s.exp < prec




def _make_mpf(tpl, construct=object.__new__, cls=mpf):
    a = construct(cls)
    a.val = tpl
    return a


class constant(mpf):

    def __new__(cls, func):
        a = object.__new__(cls)
        a.func = func
        return a

    @property
    def val(self):
        return self.func(mpf._prec, mpf._rounding)


pi = constant(fpi)
e = constant(lambda p, r: fexp(fone, p, r))
cgamma = constant(fgamma)
clog2 = constant(flog2)
clog10 = constant(flog10)


def hypot(x, y):
    x = mpf(x)
    y = mpf(y)
    return mpf(fhypot(x.val, y.val, mpf._prec, mpf._rounding))


class mpc(mpnumeric):

    def __new__(cls, real=0, imag=0):
        s = object.__new__(cls)
        if isinstance(real, (complex, mpc)):
            real, imag = real.real, real.imag
        s.real = mpf(real)
        s.imag = mpf(imag)
        return s

    def __repr__(s):
        r = repr(s.real)[4:-1]
        i = repr(s.imag)[4:-1]
        return "mpc(real=%s, imag=%s)" % (r, i)

    def __str__(s):
        return "(%s + %sj)" % (s.real, s.imag)

    def __complex__(s):
        return complex(float(s.real), float(s.imag))

    def __pos__(s):
        return mpc(s.real, s.imag)

    def __abs__(s):
        return hypot(s.real, s.imag)

    def __eq__(s, t):
        if not isinstance(t, mpc):
            if isinstance(t, str):
                return False
            t = mpc(t)
        return s.real == t.real and s.imag == t.imag

    def _compare(*args):
        raise TypeError("no ordering relation is defined for complex numbers")

    __gt__ = _compare
    __le__ = _compare
    __gt__ = _compare
    __ge__ = _compare

    def __nonzero__(s):
        return s.real != 0 or s.imag != 0

    def conjugate(s):
        return mpc(s.real, -s.imag)

    def __add__(s, t):
        if not isinstance(t, mpc):
            t = mpc(t)
        return mpc(s.real+t.real, s.imag+t.imag)

    __radd__ = __add__

    def __neg__(s):
        return mpc(-s.real, -s.imag)

    def __sub__(s, t):
        if not isinstance(t, mpc):
            t = mpc(t)
        return mpc(s.real-t.real, s.imag-t.imag)

    def __rsub__(s, t):
        return (-s) + t

    def __mul__(s, t):
        if not isinstance(t, mpc):
            t = mpc(t)
        a = s.real; b = s.imag; c = t.real; d = t.imag
        if b == d == 0:
            return mpc(a*c, 0)
        else:
            return mpc(a*c-b*d, a*d+b*c)

    __rmul__ = __mul__

    def __div__(s, t):
        if not isinstance(t, mpc):
            t = mpc(t)
        a = s.real; b = s.imag; c = t.real; d = t.imag
        mag = c*c + d*d
        return mpc((a*c+b*d)/mag, (b*c-a*d)/mag)

    def __rdiv__(s, t):
        return mpc(t) / s

    def __pow__(s, n):
        if n == 0: return mpc(1)
        if n == 1: return +s
        if n == -1: return 1/s
        if n == 2: return s*s
        if isinstance(n, (int, long)) and n > 0:
            # TODO: should increase working precision here
            w = mpc(1)
            while n:
                if n & 1:
                    w = w*s
                    n -= 1
                s = s*s
                n //= 2
            return w
        if n == 0.5:
            return sqrt(s)
        return power(s, n)

    # TODO: refactor and merge with mpf.ae
    def ae(s, t, rel_eps=None, abs_eps=None):
        if not isinstance(t, mpc):
            t = mpc(t)
        if abs_eps is None and rel_eps is None:
            abs_eps = rel_eps = _make_mpf((1, -mpf._prec+4, 1))
        if abs_eps is None:
            abs_eps = rel_eps
        elif rel_eps is None:
            rel_eps = abs_eps
        diff = abs(s-t)
        if diff <= abs_eps:
            return True
        abss = abs(s)
        abst = abs(t)
        if abss < abst:
            err = diff/abst
        else:
            err = diff/abss
        return err <= rel_eps



complex_types = (complex, mpc)


def _make_mpc(tpl, construct=object.__new__, cls=mpc):
    a = construct(cls)
    a.real, a.imag = map(_make_mpf, tpl)
    return a

j = mpc(0,1)


def sqrt(x):
    x = mpnumeric(x)
    if isinstance(x, mpf) and x.val[0] >= 0:
        return _make_mpf(fsqrt(x.val, mpf._prec, mpf._rounding))
    x = mpc(x)
    return _make_mpc(fcsqrt(x.real.val, x.imag.val, mpf._prec, mpf._rounding))


# Functions that map reals to real and complexes to complexes
def entire_function(name, real_f, complex_f):
    def f(x):
        x = mpnumeric(x)
        if isinstance(x, mpf):
            return _make_mpf(real_f(x.val, mpf._prec, mpf._rounding))
        else:
            return _make_mpc(complex_f(x.real.val, x.imag.val, mpf._prec, mpf._rounding))
    f.__name__ = name
    return f

exp = entire_function('exp', fexp, fcexp)
cos = entire_function('cos', fcos, fccos)
sin = entire_function('sin', fsin, fcsin)
cosh = entire_function('cosh', fcosh, fccosh)
sinh = entire_function('sinh', fsinh, fcsinh)


def log(x, base=None):
    if base is not None:
        mpf.prec += 3
        a = log(x) / log(base)
        mpf.prec -= 3
        return +a
    x = mpnumeric(x)
    if not x:
        raise ValueError, "logarithm of 0"
    if isinstance(x, mpf) and x.val[0] > 0:
        return _make_mpf(flog(x.val, mpf._prec, mpf._rounding))
    else:
        x = mpc(x)
        mpf._prec += 6
        mag = abs(x)
        phase = atan2(x.imag, x.real)
        mpf._prec -= 6
        return mpc(log(mag), phase)

def power(x, y):
    # TODO: accurate estimate for extra precision needed
    mpf._prec += 10
    t = exp(y * log(x))
    mpf._prec -= 10
    return +t

def tan(x):
    x = mpnumeric(x)
    if isinstance(x, mpf):
        return _make_mpf(ftan(x.val, mpf._prec, mpf._rounding))
    # the complex division can cause enormous cancellation.
    # TODO: handle cancellation robustly
    mpf._prec += 20
    t = sin(x) / cos(x)
    mpf._prec -= 20
    return +t

def atan(x):
    x = mpnumeric(x)
    if isinstance(x, mpf):
        return _make_mpf(fatan(x.val, mpf._prec, mpf._rounding))
    # TODO: maybe get this to agree with Python's cmath atan about the
    # branch to choose on the imaginary axis
    # TODO: handle cancellation robustly
    mpf._prec += 10
    t = (0.5j)*(log(1-1j*x) - log(1+1j*x))
    mpf._prec -= 10
    return +t

def atan2(y,x):
    """atan2(y, x) has the same magnitude as atan(y/x) but accounts for
    the signs of y and x. (For real arguments only.)"""
    x = mpf(x)
    y = mpf(y)
    if y < 0:
        return -atan2(-y, x)
    if not x and not y:
        return mpf(0)
    if y > 0 and x == 0:
        mpf._prec += 2
        t = pi/2
        mpf._prec -= 2
        return t
    mpf._prec += 2
    if x > 0:
        a = atan(y/x)
    else:
        a = pi - atan(-y/x)
    mpf._prec -= 2
    return +a

# TODO: robustly deal with cancellation in all of the following functions

def _asin_complex(z):
    mpf._prec += 10
    t = -1j * log(1j * z + sqrt(1 - z*z))
    mpf._prec -= 10
    return +t

def asin(x):
    x = mpnumeric(x)
    if isinstance(x, mpf) and abs(x) <= 1:
        return _asin_complex(x).real
    return _asin_complex(x)

def _acos_complex(z):
    mpf._prec += 10
    t = pi/2 + 1j * log(1j * z + sqrt(1 - z*z))
    mpf._prec -= 10
    return +t

def acos(x):
    x = mpnumeric(x)
    if isinstance(x, mpf) and abs(x) <= 1:
        return _acos_complex(x).real
    return _acos_complex(x)

def tanh(x):
    x = mpnumeric(x)
    oldprec = mpf._prec
    a = abs(x)
    mpf._prec += 10
    high = a.exp + a.bc
    if high < -10:
        if high < (-(mpf._prec-10) * 0.3):
            return x - (x**3)/3 + 2*(x**5)/15
        mpf._prec += (-high)
    a = exp(2*x)
    t = (a-1)/(a+1)
    mpf._prec = oldprec
    return +t

def asinh(x):
    x = mpnumeric(x)
    oldprec = mpf._prec
    a = abs(x)
    mpf._prec += 10
    high = a.exp + a.bc
    if high < -10:
        if high < (-(mpf._prec-10) * 0.3):
            return x - (x**3)/6 + 3*(x**5)/40
        mpf._prec += (-high)
    t = log(x + sqrt(x**2 + 1))
    mpf._prec = oldprec
    return +t

def acosh(x):
    x = mpnumeric(x)
    mpf._prec += 10
    t = log(x + sqrt(x-1)*sqrt(x+1))
    mpf._prec -= 10
    return +t

def atanh(x):
    x = mpnumeric(x)
    oldprec = mpf._prec
    a = abs(x)
    mpf._prec += 10
    high = a.exp + a.bc
    if high < -10:
        #print mpf._prec, x, x-(x**3)/3+(x**5)/5
        if high < (-(mpf._prec-10) * 0.3):
            return x - (x**3)/3 + (x**5)/5
        mpf._prec += (-high)
    t = 0.5*(log(1+x)-log(1-x))
    mpf._prec = oldprec
    return +t


__all__ = ["mpnumeric", "mpf", "mpc", "pi", "e", "cgamma", "clog2", "clog10", "j",
  "sqrt", "hypot", "exp", "log", "cos", "sin", "tan", "atan", "atan2", "power",
  "asin", "acos", "sinh", "cosh", "tanh", "asinh", "acosh", "atanh"]
