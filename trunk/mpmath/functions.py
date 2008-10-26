"""
This module defines most special functions and mathematical constants
provided by mpmath. [Exception: elliptic functions are currently
in elliptic.py]

Most of the actual computational code is located in the lib* modules
(libelefun, libhyper, ...); this module simply wraps this code to
handle precision management in a user friendly way, provide type
conversions, etc.

In addition, this module defines a number of functions that would
be inconvenient to define in the lib* modules, due to requiring
high level operations (e.g. numerical quadrature) for the computation,
or the need to support multiple arguments of mixed types.

"""

import libmpf
import libelefun
import libmpc
import libmpi
import gammazeta
import libhyper

from mptypes import (\
    mpnumeric, convert_lossless,
    mpf, make_mpf,
    mpc, make_mpc,
    mpi, make_mpi,
    constant,
    prec_rounding, mp,
    extraprec,
    zero, one, inf, ninf, nan, j, isnan, isinf, isint, eps,
    ComplexResult,
)

class _pi(constant):
    """
    Pi, roughly equal to 3.141592654, represents the area of the unit
    circle, the half-period of trigonometric functions, and many other
    things in mathematics.

    Mpmath can evaluate pi to arbitrary precision:

        >>> from mpmath import *
        >>> mp.dps = 50
        >>> print pi
        3.1415926535897932384626433832795028841971693993751

    This shows digits 99991-100000 of pi:

        >>> mp.dps = 100000
        >>> str(pi)[-10:]
        '5549362464'

    **Possible issues**

    :data:`pi` always rounds to the nearest floating-point
    number when used. This means that exact mathematical identities
    involving pi will generally not be preserved in floating-point
    arithmetic. In particular, multiples of :data:`pi` (except for 
    the trivial case ``0*pi``) are `not` the exact roots of
    :func:`sin`, but differ roughly by the current epsilon:

        >>> mp.dps = 15
        >>> sin(pi)
        mpf('1.2246467991473532e-16')

    One solution is to use the :func:`sinpi` function instead:

        >>> sinpi(1)
        mpf('0.0')

    See the documentation of trigonometric functions for additional
    details.
    """


class _degree(constant): pass

class _e(constant):
    """
    The transcendental number e = 2.718281828... is the base of the
    natural logarithm :func:`ln` and of the exponential function,
    :func:`exp`.

    Mpmath can be evaluate e to arbitrary precision:

        >>> mp.dps = 50
        >>> print e
        2.7182818284590452353602874713526624977572470937

    This shows digits 99991-100000 of e:

        >>> mp.dps = 100000
        >>> str(e)[-10:]
        '2100427165'

    **Possible issues**

    :data:`e` always rounds to the nearest floating-point number
    when used, and mathematical identities involving e may not
    hold in floating-point arithmetic. For example, ``ln(e)``
    might not evaluate exactly to 1.

    In particular, don't use ``e**x`` to compute the exponential
    function. Use ``exp(x)`` instead; this is both faster and more
    accurate.

    """
    pass


class _ln2(constant): pass

class _ln10(constant): pass

class _phi(constant): pass

class _euler(constant): pass

class _catalan(constant): pass

class _khinchin(constant): pass

class _glaisher(constant):
    """
    Glaisher's constant A, also known as the Glaisher-Kinkelin constant,
    is a number approximately equal to 1.282427129 that sometimes
    appears in formulas related to gamma and zeta functions.

    Mpmath can evaluate Glaisher's constant to arbitrary precision:

        >>> from mpmath import *
        >>> mp.dps = 50
        >>> print glaisher
        1.282427129100622636875342568869791727767688927325

    Glaisher's constant is defined in terms of the derivative of the
    Riemann zeta function. We can verify that the value computed by
    :data:`glaisher` is correct using mpmath's facilities for numerical
    differentiation and arbitrary evaluation of the zeta function:

        >>> print exp(mpf(1)/12 - diff(zeta, -1))
        1.282427129100622636875342568869791727767688927325

    Here is an example of an integral that can be evaluated in
    terms of Glaisher's constant:

        >>> mp.dps = 15
        >>> print quad(lambda x: log(gamma(x)), [1, 1.5])
        -0.0428537406502909
        >>> print -0.5 - 7*log(2)/24 + log(pi)/4 + 3*log(glaisher)/2
        -0.042853740650291

    Mpmath computes Glaisher's constant by applying Euler-Maclaurin
    summation to a slowly convergent series. The implementation is
    reasonably efficient up to about 10,000 digits. See the source
    code for additional details.

    References:
    http://mathworld.wolfram.com/Glaisher-KinkelinConstant.html

    """

class _apery(constant): pass

# Mathematical constants
pi = _pi(libelefun.mpf_pi, "pi")
degree = _degree(libelefun.mpf_degree, "degree")
e = _e(libelefun.mpf_e, "e")
ln2 = _ln2(libelefun.mpf_ln2, "ln(2)")
ln10 = _ln10(libelefun.mpf_ln10, "ln(10)")
phi = _phi(libelefun.mpf_phi, "Golden ratio (phi)")
euler = _euler(gammazeta.mpf_euler, "Euler's constant (gamma)")
catalan = _catalan(gammazeta.mpf_catalan, "Catalan's constant")
khinchin = _khinchin(gammazeta.mpf_khinchin, "Khinchin's constant")
glaisher = _glaisher(gammazeta.mpf_glaisher, "Glaisher's constant")
apery = _apery(gammazeta.mpf_apery, "Apery's constant")


def funcwrapper(f):
    def g(*args, **kwargs):
        orig = mp.prec
        try:
            args = [convert_lossless(z) for z in args]
            mp.prec = orig + 10
            v = f(*args, **kwargs)
        finally:
            mp.prec = orig
        return +v
    g.__name__ = f.__name__
    g.__doc__ = f.__doc__
    return g

def mpfunc(name, real_f, complex_f, doc, interval_f=None):
    def f(x, **kwargs):
        if not isinstance(x, mpnumeric):
            x = convert_lossless(x)
        prec, rounding = prec_rounding
        if kwargs:
            prec = kwargs.get('prec', prec)
            if 'dps' in kwargs:
                prec = dps_to_prec(kwargs['dps'])
            rounding = kwargs.get('rounding', rounding)
        if isinstance(x, mpf):
            try:
                return make_mpf(real_f(x._mpf_, prec, rounding))
            except ComplexResult:
                # Handle propagation to complex
                if mp.trap_complex:
                    raise
                return make_mpc(complex_f((x._mpf_, libmpf.fzero), prec, rounding))
        elif isinstance(x, mpc):
            return make_mpc(complex_f(x._mpc_, prec, rounding))
        elif isinstance(x, mpi):
            if interval_f:
                return make_mpi(interval_f(x._val, prec))
        raise NotImplementedError("%s of a %s" % (name, type(x)))

    f.__name__ = name
    f.__doc__ = "Returns the %s of x" % doc
    return f

def altfunc(f, name, desc):
    def g(x):
        orig = mp.prec
        try:
            mp.prec = orig + 10
            return one/f(x)
        finally:
            mp.prec = orig
    g.__name__ = name
    g.__doc__ = "Returns the %s of x, 1/%s(x)" % (desc, f.__name__)
    return g

def altinvfunc(f, name, desc):
    def g(x):
        orig = mp.prec
        try:
            mp.prec = orig + 10
            return f(one/x)
        finally:
            mp.prec = orig
    g.__name__ = name
    g.__doc__ = "Returns the inverse %s of x, %s(1/x)" % (desc, f.__name__)
    return g

sqrt = mpfunc('sqrt', libelefun.mpf_sqrt, libmpc.mpc_sqrt, "principal square root", libmpi.mpi_sqrt)
sqrt.__doc__ = """
sqrt(x) computes the principal square root of x. For positive
real numbers, this is simply the  positive square root. For
arbitrary complex numbers, the principal square root is
defined to satisfy sqrt(x) = exp(ln(x)/2).

For all mpmath numbers x, calling sqrt(x) is equivalent to
performing x**0.5.

**Examples**

Basic examples and limits::

    >>> from mpmath import *
    >>> mp.dps = 15
    >>> print sqrt(10)
    3.16227766016838
    >>> print sqrt(100)
    10.0
    >>> print sqrt(-4)
    (0.0 + 2.0j)
    >>> print sqrt(1+1j)
    (1.09868411346781 + 0.455089860562227j)
    >>> print sqrt(inf)
    +inf

Square root evaluation is fast at huge precision::

    >>> mp.dps = 50000
    >>> a = sqrt(3)
    >>> str(a)[-10:]
    '9329332814'

:func:`sqrt` supports interval arguments::

    >>> mp.dps = 15
    >>> print sqrt(mpi(16, 100))
    [4.0, 10.0]
    >>> print sqrt(mpi(2))
    [1.4142135623730949234, 1.4142135623730951455]
    >>> print sqrt(mpi(2)) ** 2
    [1.9999999999999995559, 2.0000000000000004441]

"""

cbrt = mpfunc('cbrt', libelefun.mpf_cbrt, libmpc.mpc_cbrt, "principal cubic root")
cbrt.__doc__ = """
cbrt(x) computes the cube root of x. This function is faster and
more accurate than raising to a floating-point fraction::

    >>> from mpmath import *
    >>> mp.dps = 15
    >>> 125**(mpf(1)/3)
    mpf('4.9999999999999991')
    >>> cbrt(125)
    mpf('5.0')

Every nonzero complex number has three cube roots. This function
returns the cube root defined by exp(ln(x)/3) where the principal
branch of the natural logarithm is used. Note that this does not
give a real cube root for negative real numbers::

    >>> print cbrt(-1)
    (0.5 + 0.866025403784439j)

"""

exp = mpfunc('exp', libelefun.mpf_exp, libmpc.mpc_exp, "exponential function", libmpi.mpi_exp)
ln = mpfunc('ln', libelefun.mpf_log, libmpc.mpc_log, "natural logarithm", libmpi.mpi_log)

cos = mpfunc('cos', libelefun.mpf_cos, libmpc.mpc_cos, "cosine", libmpi.mpi_cos)
sin = mpfunc('sin', libelefun.mpf_sin, libmpc.mpc_sin, "sine", libmpi.mpi_sin)
tan = mpfunc('tan', libelefun.mpf_tan, libmpc.mpc_tan, "tangent", libmpi.mpi_tan)
cosh = mpfunc('cosh', libelefun.mpf_cosh, libmpc.mpc_cosh, "hyperbolic cosine")
sinh = mpfunc('sinh', libelefun.mpf_sinh, libmpc.mpc_sinh, "hyperbolic sine")
tanh = mpfunc('tanh', libelefun.mpf_tanh, libmpc.mpc_tanh, "hyperbolic tangent")

acos = mpfunc('acos', libelefun.mpf_acos, libmpc.mpc_acos, "inverse cosine")
asin = mpfunc('asin', libelefun.mpf_asin, libmpc.mpc_asin, "inverse sine")
atan = mpfunc('atan', libelefun.mpf_atan, libmpc.mpc_atan, "inverse tangent")
asinh = mpfunc('asinh', libelefun.mpf_asinh, libmpc.mpc_asinh, "inverse hyperbolic sine")
acosh = mpfunc('acosh', libelefun.mpf_acosh, libmpc.mpc_acosh, "inverse hyperbolic cosine")
atanh = mpfunc('atanh', libelefun.mpf_atanh, libmpc.mpc_atanh, "inverse hyperbolic tangent")

sec = altfunc(cos, 'sec', 'secant')
csc = altfunc(sin, 'csc', 'cosecant')
cot = altfunc(tan, 'cot', 'cotangent')
sech = altfunc(cosh, 'sech', 'hyperbolic secant')
csch = altfunc(sinh, 'csch', 'hyperbolic cosecant')
coth = altfunc(tanh, 'coth', 'hyperbolic cotangent')

asec = altinvfunc(acos, 'asec', 'secant')
acsc = altinvfunc(asin, 'acsc', 'cosecant')
acot = altinvfunc(atan, 'acot', 'cotangent')
asech = altinvfunc(acosh, 'asech', 'hyperbolic secant')
acsch = altinvfunc(asinh, 'acsch', 'hyperbolic cosecant')
acoth = altinvfunc(atanh, 'acoth', 'hyperbolic cotangent')

floor = mpfunc('floor', libmpf.mpf_floor, libmpc.mpc_floor, "")
floor.__doc__ = """Computes the floor function of x. Note: returns a floating-point
number, not a Python int. If x is larger than the precision, it will be rounded,
not necessarily in the floor direction."""

ceil = mpfunc('ceil', libmpf.mpf_ceil, libmpc.mpc_ceil, "")
ceil.__doc__ = """Computes the ceiling function of x. Note: returns a floating-point
number, not a Python int. If x is larger than the precision, it will be rounded,
not necessarily in the floor direction."""

@funcwrapper
def nthroot(x, n):
    """
    nthroot(x, n) computes the principal nth root of x, x^(1/n). Here
    n must be an integer, and can be negative [x^(-1/n) is 1/(x^(1/n))].
    For n = 2 or n = 3, this function is equivalent to calling
    :func:`sqrt` or :func:`cbrt`. In general, nthroot(x, n) is defined
    to compute exp(ln(x)/n).

    :func:`nthroot` is implemented to use Newton's method for small n.
    At high precision, this makes x^(1/n) not much more expensive than
    the regular exponentiation, x^n. For very large n, it falls back to
    use the exponential function.

    :func:`nthroot` is faster and more accurate than raising to a
    floating-point fraction::
    
        >>> from mpmath import *
        >>> mp.dps = 15
        >>> 16807 ** (mpf(1)/5)
        mpf('7.0000000000000009')
        >>> nthroot(16807, 5)
        mpf('7.0')

    """
    n = int(n)
    if isinstance(x, mpf):
        try:
            return make_mpf(libelefun.mpf_nthroot(x._mpf_, n, *prec_rounding))
        except ComplexResult:
            if mp.trap_complex:
                raise
            x = (x._mpf_, libmpf.fzero)
    else:
        x = x._mpc_
    return make_mpc(libmpc.mpc_nthroot(x, n, *prec_rounding))

def hypot(x, y):
    """Returns the Euclidean distance sqrt(x*x + y*y). Both x and y
    must be real."""
    x = convert_lossless(x)
    y = convert_lossless(y)
    return make_mpf(libmpf.mpf_hypot(x._mpf_, y._mpf_, *prec_rounding))

def ldexp(x, n):
    """Calculate mpf(x) * 2**n efficiently. No rounding is performed."""
    x = convert_lossless(x)
    return make_mpf(libmpf.mpf_shift(x._mpf_, n))

def frexp(x):
    """Convert x to a scaled number y in the range [0.5, 1). Returns
    (y, n) such that x = y * 2**n. No rounding is performed."""
    x = convert_lossless(x)
    y, n = libmpf.mpf_frexp(x._mpf_)
    return make_mpf(y), n

def sign(x):
    """Return sign(x), defined as x/abs(x), or 0 for x = 0."""
    x = convert_lossless(x)
    if not x or isnan(x):
        return x
    if isinstance(x, mpf):
        return cmp(x, 0)
    return x / abs(x)

@extraprec(5)
def arg(x):
    """Returns the complex argument (phase) of x. The returned value is
    an mpf instance. The argument is here defined to satisfy
    -pi < arg(x) <= pi. On the negative real half-axis, it is taken to
    be +pi."""
    x = mpc(x)
    return atan2(x.imag, x.real)

def log(x, b=None):
    """Returns the base-b logarithm of x. If b is unspecified, return
    the natural (base-e) logarithm. log(x, b) is defined as
    log(x)/log(b). log(0) raises ValueError.

    The natural logarithm is real if x > 0 and complex if x < 0 or if x
    is complex. The principal branch of the complex logarithm is chosen,
    for which Im(log(x)) = -pi < arg(x) <= pi. """
    if b is None:
        return ln(x)
    wp = mp.prec + 20
    return ln(x, prec=wp) / ln(b, prec=wp)

def log10(x):
    """Base-10 logarithm. Equivalent to log(x,10)."""
    return log(x, 10)

def power(x, y):
    """Converts x and y to mpf or mpc and returns x**y = exp(y*log(x))."""
    return convert_lossless(x) ** convert_lossless(y)

def modf(x,y):
    """Converts x and y to mpf or mpc and returns x % y"""
    x = convert_lossless(x)
    y = convert_lossless(y)
    return x % y

def degrees(x):
    """Convert x given in radians to degrees"""
    return x / degree

def radians(x):
    """Convert x given in degrees to radians"""
    return x * degree

def atan2(y,x):
    """atan2(y, x) has the same magnitude as atan(y/x) but accounts for
    the signs of y and x. (Defined for real x and y only.)"""
    x = convert_lossless(x)
    y = convert_lossless(y)
    return make_mpf(libelefun.mpf_atan2(y._mpf_, x._mpf_, *prec_rounding))


cospi = mpfunc('cospi', gammazeta.mpf_cos_pi, gammazeta.mpc_cos_pi, 'computes cos(pi*x) accurately')
sinpi = mpfunc('sinpi', gammazeta.mpf_sin_pi, gammazeta.mpc_sin_pi, 'computes sin(pi*x) accurately')

zeta = mpfunc('zeta', gammazeta.mpf_zeta, gammazeta.mpc_zeta, 'Riemann zeta function')

zeta.__doc__ = """
    Computes the Riemann zeta function, zeta(s). The Riemann zeta
    function is defined for Re(s) > 1 by::

                         -s     -s     -s
        zeta(s) = 1  +  2   +  3   +  4   + ...

    and for Re(s) <= 1 by analytic continuation. It has a pole
    at s = 1.

    **Examples**

    Some exact values of the zeta function are::

        >>> from mpmath import *
        >>> mp.dps = 15
        >>> print zeta(2)
        1.64493406684823
        >>> print pi**2 / 6
        1.64493406684823
        >>> print zeta(0)
        -0.5
        >>> print zeta(-1)
        -0.0833333333333333
        >>> print zeta(-2)
        0.0

    :func:`zeta` supports arbitrary precision evaluation and
    complex arguments::

        >>> mp.dps = 50
        >>> print zeta(pi)
        1.1762417383825827588721504519380520911697389900217
        >>> print zeta(1+2j)  # doctest: +NORMALIZE_WHITESPACE
        (0.5981655697623817367034568491742186771747764868876 -
        0.35185474521784529049653859679690026505229177886045j)

    The Riemann zeta function has so-called nontrivial zeros on
    the critical line s = 1/2 + j*t::

        >>> mp.dps = 15
        >>> print findroot(zeta, 0.5+14j)
        (0.5 + 14.1347251417347j)
        >>> print findroot(zeta, 0.5+21j)
        (0.5 + 21.0220396387716j)
        >>> print findroot(zeta, 0.5+25j)
        (0.5 + 25.0108575801457j)

    For large positive s, zeta(s) rapidly approaches 1::

        >>> print zeta(30)
        1.00000000093133
        >>> print zeta(100)
        1.0
        >>> print zeta(inf)
        1.0

    The following series converges and in fact has a simple
    closed form value::

        >>> print sumsh(lambda k: zeta(k) - 1, [2, inf])
        1.0

    **Algorithm**

    The primary algorithm is Borwein's algorithm for the Dirichlet
    eta function. Three separate implementations are used: for general
    real arguments, general complex arguments, and for integers. The
    reflection formula is applied to arguments in the negative
    half-plane. For very large real arguments, either direct
    summation or the Euler prime product is used.

    It should be noted that computation of zeta(s) gets very slow
    when s is far away from the real axis.

    **References**

    * http://mathworld.wolfram.com/RiemannZetaFunction.html

    * http://www.cecm.sfu.ca/personal/pborwein/PAPERS/P155.pdf

"""

gamma = mpfunc('gamma', gammazeta.mpf_gamma, gammazeta.mpc_gamma, "gamma function")
factorial = mpfunc('factorial', gammazeta.mpf_factorial, gammazeta.mpc_factorial, "factorial")
fac = factorial

def psi(m, z):
    """
    Gives the polygamma function of order m of z, psi^(m)(z). Special
    cases are the digamma function (psi0), trigamma function (psi1),
    tetragamma (psi2) and pentagamma (psi4) functions.

    The parameter m should be a nonnegative integer.
    """
    z = convert_lossless(z)
    m = int(m)
    if isinstance(z, mpf):
        return make_mpf(gammazeta.mpf_psi(m, z._mpf_, *prec_rounding))
    else:
        return make_mpc(gammazeta.mpc_psi(m, z._mpc_, *prec_rounding))

def psi0(z):
    """Shortcut for psi(0,z) (the digamma function)"""
    return psi(0, z)

def psi1(z):
    """Shortcut for psi(1,z) (the trigamma function)"""
    return psi(1, z)

def psi2(z):
    """Shortcut for psi(2,z) (the tetragamma function)"""
    return psi(2, z)

def psi3(z):
    """Shortcut for psi(3,z) (the pentagamma function)"""
    return psi(3, z)

polygamma = psi
digamma = psi0
trigamma = psi1
tetragamma = psi2
pentagamma = psi3

harmonic = mpfunc('harmonic', gammazeta.mpf_harmonic, gammazeta.mpc_harmonic,
    "nth harmonic number")

harmonic.__doc__ = """
    If `n` is an integer, harmonic(`n`) gives a floating-point
    approximation of the `n`-th harmonic number
    H(`n`) = 1 + 1/2 + 1/3 + ... + 1/`n`::

        >>> from mpmath import *
        >>> mp.dps = 15    
        >>> for n in range(8):
        ...     print n, harmonic(n)
        ...
        0 0.0
        1 1.0
        2 1.5
        3 1.83333333333333
        4 2.08333333333333
        5 2.28333333333333
        6 2.45
        7 2.59285714285714

    The infinite harmonic series 1 + 1/2 + 1/3 + ... diverges::

        >>> print harmonic(inf)
        +inf

    :func:`harmonic` is evaluated using the digamma function rather
    than by summing the harmonic series term by term. It can therefore
    be computed quickly for arbitrarily large `n`, and even for
    nonintegral arguments::

        >>> print harmonic(10**100)
        230.835724964306
        >>> print harmonic(0.5)
        0.613705638880109
        >>> print harmonic(3+4j)
        (2.24757548223494 + 0.850502209186044j)

    :func:`harmonic` supports arbitrary precision evaluation::

        >>> mp.dps = 50
        >>> print harmonic(11)
        3.0198773448773448773448773448773448773448773448773
        >>> print harmonic(pi)
        1.8727388590273302654363491032336134987519132374152

    The harmonic series diverges, but at a glacial pace. It is possible
    to calculate the exact number of terms required before the sum
    exceeds a given amount, say 100::

        >>> mp.dps = 50
        >>> v = 10**findroot(lambda x: harmonic(10**x) - 100, 10)
        >>> print v
        15092688622113788323693563264538101449859496.864101
        >>> v = int(ceil(v))
        >>> print v
        15092688622113788323693563264538101449859497
        >>> print harmonic(v-1)
        99.999999999999999999999999999999999999999999942747
        >>> print harmonic(v)
        100.000000000000000000000000000000000000000000009

    """

def bernoulli(n):
    """
    Computes the nth Bernoulli number, B(n), for any integer n >= 0.

    The Bernoulli numbers are rational numbers, but this function
    returns a floating-point approximation. To obtain an exact
    fraction, use :func:`bernfrac` instead.

    **Examples**

    Numerical values of the first few Bernoulli numbers::

        >>> from mpmath import *
        >>> mp.dps = 15
        >>> for n in range(15):
        ...     print n, bernoulli(n)
        ...
        0 1.0
        1 -0.5
        2 0.166666666666667
        3 0.0
        4 -0.0333333333333333
        5 0.0
        6 0.0238095238095238
        7 0.0
        8 -0.0333333333333333
        9 0.0
        10 0.0757575757575758
        11 0.0
        12 -0.253113553113553
        13 0.0
        14 1.16666666666667

    Bernoulli numbers can be approximated with arbitrary precision::

        >>> mp.dps = 50
        >>> print bernoulli(100)
        -2.8382249570693706959264156336481764738284680928013e+78

    Arbitrarily large n are supported::

        >>> mp.dps = 15
        >>> print bernoulli(10**20 + 2)
        3.09136296657021e+1876752564973863312327

    The Bernoulli numbers are related to the Riemann zeta function
    at integer arguments::

        >>> print -bernoulli(8) * (2*pi)**8 / (2*fac(8))
        1.00407735619794
        >>> print zeta(8)
        1.00407735619794

    **Algorithm**

    For small n (n < 3000) :func:`bernoulli` uses a recurrence
    formula due to Ramanujan. All results in this range are cached,
    so sequential computation of small Bernoulli numbers is
    guaranteed to be fast.

    For larger n, B(n) is evaluated in terms of the Riemann zeta
    function.
    """
    return make_mpf(gammazeta.mpf_bernoulli(int(n), *prec_rounding))

bernfrac = gammazeta.bernfrac

stieltjes_cache = {}

def stieltjes(n):
    """
    For a nonnegative integer `n`, stieltjes(`n`) computes the
    nth Stieltjes constant, defined as the nth coefficient
    in the Laurent series expansion of the Riemann zeta function
    around the pole at s = 1::

                            oo
                            ___     n
                    1      \    (-1)                n
        zeta(s) = ----- +   )   ----- (gamma ) (s-1)
                  s - 1    /___  n!         n
                           n = 0

    Here gamma_n is the nth Stieltjes constant.

    **Examples**

    The zeroth Stieltjes constant is just Euler's constant::

        >>> from mpmath import *
        >>> mp.dps = 15
        >>> print stieltjes(0)
        0.577215664901533

    Some more values are::

        >>> print stieltjes(1)
        -0.0728158454836767
        >>> print stieltjes(10)
        0.000205332814909065
        >>> print stieltjes(30)
        0.00355772885557316

    An alternative way to compute gamma_1::

        >>> print diff(extradps(25)(lambda x: 1/(x-1) - zeta(x)), 1)
        -0.0728158454836767

    :func:`stieltjes` supports arbitrary precision evaluation,
    and caches computed results::

        >>> mp.dps = 50
        >>> print stieltjes(2)
        -0.0096903631928723184845303860352125293590658061013408

    **Algorithm**

    The calculation is done using numerical
    integration of the Riemann zeta function. The method should
    work for any `n` and dps, but soon becomes quite slow in
    practice. The code has been tested with n = 50 and dps = 100;
    that computation took about 2 minutes.

    **References**

    * http://mathworld.wolfram.com/StieltjesConstants.html
    * http://pi.lacim.uqam.ca/piDATA/stieltjesgamma.txt

    """
    n = int(n)
    if n == 0:
        return +euler
    if n < 0:
        raise ValueError("Stieltjes constants defined for n >= 0")
    if n in stieltjes_cache:
        prec, s = stieltjes_cache[n]
        if prec >= mp.prec:
            return +s
    from quadrature import quadgl
    def f(x):
        r = exp(pi*j*x)
        return (zeta(r+1) / r**n).real
    orig = mp.prec
    try:
        p = int(log(factorial(n), 2) + 35)
        mp.prec += p
        u = quadgl(f, [-1, 1])
        v = mpf(-1)**n * factorial(n) * u / 2
    finally:
        mp.prec = orig
    stieltjes_cache[n] = (mp.prec, v)
    return +v

def isnpint(x):
    if not x:
        return True
    if isinstance(x, mpf):
        sign, man, exp, bc = x._mpf_
        return sign and exp >= 0
    if isinstance(x, mpc):
        return not x.imag and isnpint(x.real)

def gammaprod(a, b):
    """
    Given iterables `a` and `b`, ``gammaprod(a, b)`` computes the
    product / quotient of gamma functions::

        gamma(a[0]) * gamma(a[1]) * ... * gamma(a[p])
        ---------------------------------------------
        gamma(b[0]) * gamma(b[1]) * ... * gamma(b[q])

    **Handling of poles**

    Unlike direct calls to :func:`gamma`, :func:`gammaprod` considers
    the entire product as a limit and evaluates this limit properly if
    any of the numerator or denominator arguments are nonpositive
    integers such that poles of the gamma function are encountered.

    In particular:

    * If there are equally many poles in the numerator and the
      denominator, the limit is a rational number times the remaining,
      regular part of the product.

    * If there are more poles in the numerator, :func:`gammaprod`
      returns ``+inf``.

    * If there are more poles in the denominator, :func:`gammaprod`
      returns zero (``0``).

    **Examples**

    1/gamma(x) evaluated at x = 0::

        >>> from mpmath import *
        >>> mp.dps = 15
        >>> gammaprod([], [0])
        mpf('0.0')

    A limit::

        >>> gammaprod([-4], [-3])
        mpf('-0.25')
        >>> limit(lambda x: gamma(x-1)/gamma(x), -3, direction=1)
        mpf('-0.25')
        >>> limit(lambda x: gamma(x-1)/gamma(x), -3, direction=-1)
        mpf('-0.25')

    """
    a = [convert_lossless(x) for x in a]
    b = [convert_lossless(x) for x in b]
    poles_num = []
    poles_den = []
    regular_num = []
    regular_den = []
    for x in a: [regular_num, poles_num][isnpint(x)].append(x)
    for x in b: [regular_den, poles_den][isnpint(x)].append(x)
    # One more pole in numerator or denominator gives 0 or inf
    if len(poles_num) < len(poles_den): return mpf(0)
    if len(poles_num) > len(poles_den): return mpf('+inf')
    # All poles cancel
    # lim G(i)/G(j) = (-1)**(i+j) * gamma(1-j) / gamma(1-i)
    p = mpf(1)
    orig = mp.prec
    try:
        mp.prec = orig + 15
        while poles_num:
            i = poles_num.pop()
            j = poles_den.pop()
            p *= (-1)**(i+j) * gamma(1-j) / gamma(1-i)
        for x in regular_num: p *= gamma(x)
        for x in regular_den: p /= gamma(x)
    finally:
        mp.prec = orig
    return +p

def beta(x, y):
    """Beta function, B(x,y) = gamma(x)*gamma(y)/gamma(x+y)"""
    x = convert_lossless(x)
    y = convert_lossless(y)
    return gammaprod([x, y], [x+y])

def binomial(n, k):
    """Binomial coefficient, C(n,k) = n!/(k!*(n-k)!)."""
    return gammaprod([n+1], [k+1, n-k+1])

def rf(x, n):
    """Rising factorial (Pochhammer symbol), x^(n)"""
    return gammaprod([x+n], [x])

def ff(x, n):
    """Falling factorial, x_(n)"""
    return gammaprod([x+1], [x-n+1])


#---------------------------------------------------------------------------#
#                                                                           #
#                          Hypergeometric functions                         #
#                                                                           #
#---------------------------------------------------------------------------#

class _mpq(tuple):
    @property
    def _mpf_(self):
        return (mpf(self[0])/self[1])._mpf_
    def __add__(self, other):
        if isinstance(other, _mpq):
            a, b = self
            c, d = other
            return _mpq((a*d+b*c, b*d))
        return NotImplemented
    def __sub__(self, other):
        if isinstance(other, _mpq):
            a, b = self
            c, d = other
            return _mpq((a*d-b*c, b*d))
        return NotImplemented

mpq_1 = _mpq((1,1))
mpq_0 = _mpq((0,1))

def parse_param(x):
    if isinstance(x, tuple):
        p, q = x
        return [[p, q]], [], []
    if isinstance(x, (int, long)):
        return [[x, 1]], [], []
    x = convert_lossless(x)
    if isinstance(x, mpf):
        return [], [x._mpf_], []
    if isinstance(x, mpc):
        return [], [], [x._mpc_]

def _as_num(x):
    if isinstance(x, list):
        return _mpq(x)
    return x

def hypsum(ar, af, ac, br, bf, bc, x):
    prec, rnd = prec_rounding
    if hasattr(x, "_mpf_") and not (ac or bc):
        v = libhyper.hypsum_internal(ar, af, ac, br, bf, bc, x._mpf_, None, prec, rnd)
        return make_mpf(v)
    else:
        if hasattr(x, "_mpc_"):
            re, im = x._mpc_
        else:
            re, im = x._mpf_, libmpf.fzero
        v = libhyper.hypsum_internal(ar, af, ac, br, bf, bc, re, im, prec, rnd)
        return make_mpc(v)

def eval_hyp2f1(a,b,c,z):
    prec, rnd = prec_rounding
    ar, af, ac = parse_param(a)
    br, bf, bc = parse_param(b)
    cr, cf, cc = parse_param(c)
    absz = abs(z)
    if absz == 1:
        # TODO: determine whether it actually does, and otherwise
        # return infinity instead
        print "Warning: 2F1 might not converge for |z| = 1"
    if absz <= 1:
        # All rational
        if ar and br and cr:
            return sum_hyp2f1_rat(ar[0], br[0], cr[0], z)
        return hypsum(ar+br, af+bf, ac+bc, cr, cf, cc, z)
    # Use 1/z transformation
    a = (ar and _as_num(ar[0])) or convert_lossless(a)
    b = (br and _as_num(br[0])) or convert_lossless(b)
    c = (cr and _as_num(cr[0])) or convert_lossless(c)
    orig = mp.prec
    try:
        mp.prec = orig + 15
        h1 = eval_hyp2f1(a, mpq_1-c+a, mpq_1-b+a, 1/z)
        h2 = eval_hyp2f1(b, mpq_1-c+b, mpq_1-a+b, 1/z)
        #s1 = G(c)*G(b-a)/G(b)/G(c-a) * (-z)**(-a) * h1
        #s2 = G(c)*G(a-b)/G(a)/G(c-b) * (-z)**(-b) * h2
        f1 = gammaprod([c,b-a],[b,c-a])
        f2 = gammaprod([c,a-b],[a,c-b])
        s1 = f1 * (-z)**(mpq_0-a) * h1
        s2 = f2 * (-z)**(mpq_0-b) * h2
        v = s1 + s2
    finally:
        mp.prec = orig
    return +v

def sum_hyp0f1_rat(a, z):
    prec, rnd = prec_rounding
    if hasattr(z, "_mpf_"):
        return make_mpf(libhyper.mpf_hyp0f1_rat(a, z._mpf_, prec, rnd))
    else:
        return make_mpc(libhyper.mpc_hyp0f1_rat(a, z._mpc_, prec, rnd))

def sum_hyp1f1_rat(a, b, z):
    prec, rnd = prec_rounding
    if hasattr(z, "_mpf_"):
        return make_mpf(libhyper.mpf_hyp1f1_rat(a, b, z._mpf_, prec, rnd))
    else:
        return make_mpc(libhyper.mpc_hyp1f1_rat(a, b, z._mpc_, prec, rnd))

def sum_hyp2f1_rat(a, b, c, z):
    prec, rnd = prec_rounding
    if hasattr(z, "_mpf_"):
        return make_mpf(libhyper.mpf_hyp2f1_rat(a, b, c, z._mpf_, prec, rnd))
    else:
        return make_mpc(libhyper.mpc_hyp2f1_rat(a, b, c, z._mpc_, prec, rnd))


#---------------------------------------------------------------------------#
#                      And now the user-friendly versions                   #
#---------------------------------------------------------------------------#

def hyper(a_s, b_s, z):
    """
    Hypergeometric function pFq::

          [ a_1, a_2, ..., a_p |    ]
      pFq [                    |  z ]
          [ b_1, b_2, ..., b_q |    ]

    The parameter lists a_s and b_s may contain real or complex numbers.
    Exact rational parameters can be given as tuples (p, q).
    """
    p = len(a_s)
    q = len(b_s)
    z = convert_lossless(z)
    degree = p, q
    if degree == (0, 1):
        br, bf, bc = parse_param(b_s[0])
        if br:
            return sum_hyp0f1_rat(br[0], z)
        return hypsum([], [], [], br, bf, bc, z)
    if degree == (1, 1):
        ar, af, ac = parse_param(a_s[0])
        br, bf, bc = parse_param(b_s[0])
        if ar and br:
            a, b = ar[0], br[0]
            return sum_hyp1f1_rat(a, b, z)
        return hypsum(ar, af, ac, br, bf, bc, z)
    if degree == (2, 1):
        return eval_hyp2f1(a_s[0], a_s[1], b_s[0], z)
    ars, afs, acs, brs, bfs, bcs = [], [], [], [], [], []
    for a in a_s:
        r, f, c = parse_param(a)
        ars += r
        afs += f
        acs += c
    for b in b_s:
        r, f, c = parse_param(b)
        brs += r
        bfs += f
        bcs += c
    return hypsum(ars, afs, acs, brs, bfs, bcs, z)

def hyp0f1(a, z):
    """Hypergeometric function 0F1. hyp0f1(a,z) is equivalent
    to hyper([], [a], z); see documentation for hyper() for more
    information."""
    return hyper([], [a], z)

def hyp1f1(a,b,z):
    """Hypergeometric function 1F1. hyp1f1(a,b,z) is equivalent
    to hyper([a], [b], z); see documentation for hyper() for more
    information."""
    return hyper([a], [b], z)

def hyp2f1(a,b,c,z):
    """Hypergeometric function 2F1. hyp2f1(a,b,c,z) is equivalent
    to hyper([a,b], [c], z); see documentation for hyper() for more
    information."""
    return hyper([a,b], [c], z)

@funcwrapper
def lower_gamma(a,z):
    """Lower incomplete gamma function gamma(a, z)"""
    # XXX: may need more precision
    return hyp1f1(1, 1+a, z) * z**a * exp(-z) / a

@funcwrapper
def upper_gamma(a,z):
    """Upper incomplete gamma function Gamma(a, z)"""
    return gamma(a) - lower_gamma(a, z)

erf = mpfunc("erf", libhyper.mpf_erf, libhyper.mpc_erf,
    "Error function, erf(z)")

erf.__doc__ = """
Computes the error function, erf(z). The error function is
the antiderivative of the Gaussian function exp(-t^2). More
precisely::

                   z
                    -
              2    |          2
   erf(z) = -----  |   exp( -t ) dt
              1/2  |
            pi    -
                   0

**Basic examples**

Simple values and limits include::

    >>> from mpmath import *
    >>> mp.dps = 15
    >>> print erf(0)
    0.0
    >>> print erf(1)
    0.842700792949715
    >>> print erf(-1)
    -0.842700792949715
    >>> print erf(inf)
    1.0
    >>> print erf(-inf)
    -1.0

For large real z, erf(z) approaches 1 very rapidly::

    >>> print erf(3)
    0.999977909503001
    >>> print erf(5)
    0.999999999998463

The error function is an odd function::

    >>> nprint(taylor(erf, 0, 5))
    [0.0, 1.12838, 0.0, -0.376126, 0.0, 0.112838]

:func:`erf` implements arbitrary-precision evaluation and
supports complex numbers::

    >>> mp.dps = 50
    >>> print erf(0.5)
    0.52049987781304653768274665389196452873645157575796
    >>> mp.dps = 25
    >>> print erf(1+j)
    (1.316151281697947644880271 + 0.1904534692378346862841089j)

**Related functions**

See also :func:`erfc`, which is more accurate for large z,
and :func:`erfi` which gives the antiderivative of exp(t^2).

The Fresnel integrals :func:`fresnels` and :func:`fresnelc`
are also related to the error function.
"""


erfc = mpfunc("erfc", libhyper.mpf_erfc, libhyper.mpc_erfc,
    "Complementary error function, erfc(z) = 1-erf(z)")

erfc.__doc__ = """
Computes the complementary error function, erfc(z) = 1-erf(z).
This function avoids cancellation that occurs when naively
computing the complementary error function as 1-erf(z)::

    >>> from mpmath import *
    >>> mp.dps = 15
    >>> print 1 - erf(10)
    0.0
    >>> print erfc(10)
    2.08848758376254e-45

:func:`erfc` works accurately even for ludicrously large
arguments::

    >>> print erfc(10**10)
    4.3504398860243e-43429448190325182776

"""

@funcwrapper
def erfi(z):
    """
    Computes the imaginary error function, erfi(z). The imaginary
    error function is defined in analogy with the error function,
    but with a positive sign in the integrand::

                       z
                        -
                  2    |         2
       erf(z) = -----  |   exp( t ) dt
                  1/2  |
                pi    -
                       0

    Whereas the error function rapidly converges to 1 as z grows,
    the imaginary error function rapidly diverges to infinity.
    The functions are related as erfi(z) = -j*erf(z*j).

    **Examples**

    Basic values and limits::

        >>> from mpmath import *
        >>> mp.dps = 15
        >>> print erfi(0)
        0.0
        >>> print erfi(1)
        1.65042575879754
        >>> print erfi(-1)
        -1.65042575879754
        >>> print erfi(inf)
        +inf
        >>> print erfi(-inf)
        -inf

    Note the symmetry between erf and erfi::

        >>> print erfi(3j)
        (0.0 + 0.999977909503001j)
        >>> print erf(3)
        0.999977909503001
        >>> print erf(1+2j)
        (-0.536643565778565 - 5.04914370344703j)
        >>> print erfi(2+1j)
        (-5.04914370344703 - 0.536643565778565j)

    **Possible issues**

    The current implementation of :func:`erfi` is much less efficient
    and accurate than the one for erf.

    """
    return (2/sqrt(pi)*z) * sum_hyp1f1_rat((1,2),(3,2), z**2)

@funcwrapper
def npdf(x, mu=0, sigma=1):
    """
    npdf(x, mu=0, sigma=1) -- probability density function of a
    normal distribution with mean value mu and variance sigma^2.

    Elementary properties of the probability distribution can
    be verified using numerical integration::

        >>> from mpmath import *
        >>> mp.dps = 15
        >>> print quad(npdf, [-inf, inf])
        1.0
        >>> print quad(lambda x: npdf(x, 3), [3, inf])
        0.5
        >>> print quad(lambda x: npdf(x, 3, 2), [3, inf])
        0.5

    See also :func:`ncdf`, which gives the cumulative
    distribution.
    """
    sigma = convert_lossless(sigma)
    return exp(-(x-mu)**2/(2*sigma**2)) / (sigma*sqrt(2*pi))

@funcwrapper
def ncdf(x, mu=0, sigma=1):
    """
    ncdf(x, mu=0, sigma=1) -- cumulative distribution function of
    a normal distribution with mean value mu and variance sigma^2.

    See also :func:`npdf`, which gives the probability density.

    Elementary properties include::

        >>> from mpmath import *
        >>> mp.dps = 15
        >>> print ncdf(pi, mu=pi)
        0.5
        >>> print ncdf(-inf)
        0.0
        >>> print ncdf(+inf)
        1.0

    The cumulative distribution is the integral of the density
    function having identical mu and sigma::

        >>> mp.dps = 15
        >>> print diff(ncdf, 2)
        0.053990966513188
        >>> print npdf(2)
        0.053990966513188
        >>> print diff(lambda x: ncdf(x, 1, 0.5), 0)
        0.107981933026376
        >>> print npdf(0, 1, 0.5)
        0.107981933026376

    """
    a = (x-mu)/(sigma*sqrt(2))
    if a < 0:
        return erfc(-a)/2
    else:
        return (1+erf(a))/2

@funcwrapper
def ei(z):
    """
    Computes the exponential integral, Ei(z). The exponential
    integral is defined as the following integral (which,
    at t = 0, must be interpreted as a Cauchy principal value)::

                z
                 -    t
                |    e
       Ei(z) =  |   ---- dt
                |    t
               -
               -oo

    For real z, it can be thought of as behaving roughly
    like Ei(z) ~= exp(z) + log(abs(z)).

    This function should not be confused with the family of
    related functions denoted by E1, E2, ... which are also
    called exponential integrals.

    **Basic examples**

    Some basic values and limits are::

        >>> from mpmath import *
        >>> mp.dps = 15
        >>> print ei(0)
        -inf
        >>> print ei(1)
        1.89511781635594
        >>> print ei(inf)
        +inf
        >>> print ei(-inf)
        0.0

    For z < 0, the defining integral can be evaluated
    numerically as a reference::

        >>> print ei(-4)
        -0.00377935240984891
        >>> print quad(lambda t: exp(t)/t, [-inf, -4])
        -0.00377935240984891

    :func:`ei` supports complex arguments and arbitrary
    precision evaluation::

        >>> mp.dps = 50
        >>> mp.dps = 50
        >>> print ei(pi)
        10.928374389331410348638445906907535171566338835056
        >>> mp.dps = 25
        >>> print ei(3+4j)
        (-4.154091651642689822535359 + 4.294418620024357476985535j)

    **Related functions**

    The exponential integral is closely related to the logarithmic
    integral. See :func:`li` for additional information.

    The exponential integral is related to the hyperbolic
    and trigonometric integrals (see :func:`chi`, :func:`shi`,
    :func:`ci`, :func:`si`) similarly to how the ordinary
    exponential function is related to the hyperbolic and
    trigonometric functions::

        >>> mp.dps = 15
        >>> print ei(3)
        9.93383257062542
        >>> print chi(3) + shi(3)
        9.93383257062542
        >>> print ci(3j) - j*si(3j) - pi*j/2
        (9.93383257062542 + 0.0j)

    Beware that logarithmic corrections, as in the last example
    above, are required to obtain the correct branch in general.
    For details, see [1].

    The exponential integral is also a special case of the
    hypergeometric function 2F2::

        >>> z = 0.6
        >>> print z*hyper([1,1],[2,2],z) + (ln(z)-ln(1/z))/2 + euler
        0.769881289937359
        >>> print ei(z)
        0.769881289937359

    **References**

    [1] Relations between Ei and other functions:
        http://functions.wolfram.com/GammaBetaErf/ExpIntegralEi/27/01/

    [2] Abramowitz & Stegun, section 5:
        http://www.math.sfu.ca/~cbm/aands/page_228.htm

    """
    if z == inf:
        return z
    if z == -inf:
        return -mpf(0)
    if not z:
        return -inf
    v = z*hypsum([[1,1],[1,1]],[],[],[[2,1],[2,1]],[],[],z) + \
        (log(z)-log(1/z))/2 + euler
    if isinstance(z, mpf) and z < 0:
        return v.real
    return v

@funcwrapper
def li(z):
    """
    Computes the Logarithmic integral, li(z).

    The logarithmic integral is defined as the integral from 0 to z
    of 1/ln(t). It has a singularity at z = 1.

    Note that there is a second logarithmic integral defined by
    Li(z) = integral from 2 to z of 1/ln(t). This "offset
    logarithmic integral" can be computed as Li(z) = li(z) - li(2).

    **Examples**

    Some basic values and limits::

        >>> from mpmath import *
        >>> mp.dps = 30
        >>> print li(0)
        0.0
        >>> print li(1)
        -inf
        >>> print li(1)
        -inf
        >>> print li(2)
        1.04516378011749278484458888919
        >>> print findroot(li, 2)
        1.45136923488338105028396848589
        >>> print li(inf)
        +inf

    The logarithmic integral can be evaluated for arbitrary
    complex arguments::

        >>> mp.dps = 20
        >>> print li(3+4j)
        (3.1343755504645775265 + 2.6769247817778742392j)

    The logarithmic integral is related to the exponential integral::

        >>> print ei(log(3))
        2.1635885946671919729
        >>> print li(3)
        2.1635885946671919729

    The logarithmic integral grows like O(x/ln(x))::

        >>> mp.dps = 15
        >>> x = 10**100
        >>> print x/log(x)
        4.34294481903252e+97
        >>> print li(x)
        4.3619719871407e+97

    The prime number theorem states that the number of primes less
    than x is asymptotic to li(x). For example, it is known that
    there are exactly 1,925,320,391,606,803,968,923 prime numbers
    less than 10^23 [1]. The logarithmic integral provides a very
    accurate estimate::

        >>> print li(2) + li(10**23)
        1.92532039161405e+21

    A definite integral is::

        >>> print quad(li, [0, 1])
        -0.693147180559945
        >>> print -ln(2)
        -0.693147180559945

    **References**

    [1] http://mathworld.wolfram.com/PrimeCountingFunction.html

    [2] http://mathworld.wolfram.com/LogarithmicIntegral.html

    """
    if not z:
        return z
    if z == 1:
        return -inf
    return ei(log(z))

@funcwrapper
def ci(z):
    """Cosine integral, Ci(z)"""
    if z == inf:
        return 1/z
    if not z:
        return -inf
    z2 = -(z/2)**2
    return euler + log(z) + \
        z2*hypsum([[1,1],[1,1]],[],[],[[2,1],[2,1],[3,2]],[],[],z2)

@funcwrapper
def si(z):
    """Sine integral, Si(z)"""
    if z == inf:
        return pi/2
    if z == -inf:
        return -pi/2
    z2 = -(z/2)**2
    return z*hypsum([[1,2]],[],[],[[3,2],[3,2]],[],[],z2)

@funcwrapper
def chi(z):
    """Hyperbolic cosine integral, Chi(z)"""
    if not z:
        return -inf
    z2 = (z/2)**2
    return euler + log(z) + \
        z2*hypsum([[1,1],[1,1]],[],[],[[2,1],[2,1],[3,2]],[],[],z2)

@funcwrapper
def shi(z):
    """Hyperbolic sine integral, Shi(z)"""
    z2 = (z/2)**2
    return z*hypsum([[1,2]],[],[],[[3,2],[3,2]],[],[],z2)

@funcwrapper
def fresnels(z):
    """Fresnel integral S, S(z)"""
    if z == inf:
        return mpf(0.5)
    if z == -inf:
        return mpf(-0.5)
    return pi*z**3/6*hypsum([[3,4]],[],[],[[3,2],[7,4]],[],[],-pi**2*z**4/16)

@funcwrapper
def fresnelc(z):
    """Fresnel integral C, C(z)"""
    if z == inf:
        return mpf(0.5)
    if z == -inf:
        return mpf(-0.5)
    return z*hypsum([[1,4]],[],[],[[1,2],[5,4]],[],[],-pi**2*z**4/16)

@funcwrapper
def airyai(z):
    """Airy function, Ai(z)"""
    if z == inf:
        return 1/z
    if z == -inf:
        return mpf(0)
    z3 = z**3 / 9
    a = sum_hyp0f1_rat((2,3), z3) / (cbrt(9) * gamma(mpf(2)/3))
    b = z * sum_hyp0f1_rat((4,3), z3) / (cbrt(3) * gamma(mpf(1)/3))
    return a - b

@funcwrapper
def airybi(z):
    """Airy function, Bi(z)"""
    if z == inf:
        return z
    if z == -inf:
        return mpf(0)
    z3 = z**3 / 9
    rt = nthroot(3, 6)
    a = sum_hyp0f1_rat((2,3), z3) / (rt * gamma(mpf(2)/3))
    b = z * rt * sum_hyp0f1_rat((4,3), z3) / gamma(mpf(1)/3)
    return a + b

@funcwrapper
def ellipe(m):
    """Complete elliptic integral of the second kind, E(m). Note that
    the argument is the parameter m = k^2, not the modulus k."""
    if m == 1:
        return m
    return pi/2 * sum_hyp2f1_rat((1,2),(-1,2),(1,1), m)

@funcwrapper
def ellipk(m):
    """Complete elliptic integral of the first kind, K(m). Note that
    the argument is the parameter m = k^2, not the modulus k."""
    # Poor implementation:
    # return pi/2 * sum_hyp2f1_rat((1,2),(1,2),(1,1), m)
    if m == 1:
        return inf
    if isnan(m):
        return m
    if isinf(m):
        return 1/m
    s = sqrt(m)
    a = (1-s)/(1+s)
    v = pi/4*(1+a)/agm(1,a)
    if isinstance(m, mpf) and m < 1:
        return v.real
    return v

@funcwrapper
def agm(a, b=1):
    """
    agm(a, b) computes the arithmetic-geometric mean of a and b,
    defined as the limit of the iteration a, b = (a+b)/2, sqrt(a*b).

    This function can be called with a single argument, computing
    agm(a,1) = agm(1,a).

    **Examples**

    A formula for gamma(1/4)::

        >>> from mpmath import *
        >>> mp.dps = 15
        >>> print gamma(0.25)
        3.62560990822191
        >>> print sqrt(2*sqrt(2*pi**3)/agm(1,sqrt(2)))
        3.62560990822191

    **Possible issues**

    :func:`agm` may not give an appropriate branch for complex
    arguments a and b.

    """
    if not a or not b:
        return a*b
    weps = eps * 16
    half = mpf(0.5)
    while abs(a-b) > weps:
        a, b = (a+b)*half, (a*b)**half
    return a

@funcwrapper
def jacobi(n, a, b, x):
    """Jacobi polynomial P_n^(a,b)(x)."""
    return binomial(n+a,n) * hyp2f1(-n,1+n+a+b,a+1,(1-x)/2)

@funcwrapper
def legendre(n, x):
    """Legendre polynomial P_n(x)."""
    if isint(n):
        n = int(n)
    if x == -1:
        # TODO: hyp2f1 should handle this
        if x == int(x):
            return (-1)**(n + (n>=0)) * mpf(-1)
        return inf
    return hyp2f1(-n,n+1,1,(1-x)/2)

@funcwrapper
def chebyt(n, x):
    """Chebyshev polynomial of the first kind T_n(x)."""
    return hyp2f1(-n,n,0.5,(1-x)/2)

@funcwrapper
def chebyu(n, x):
    """Chebyshev polynomial of the second kind U_n(x)."""
    return (n+1) * hyp2f1(-n, n+2, 1.5, (1-x)/2)

@funcwrapper
def jv(v, x):
    """Bessel function J_v(x)."""
    if isint(v):
        if isinstance(x, mpf):
            return make_mpf(libhyper.mpf_besseljn(int(v), x._mpf_, mp.prec))
        if isinstance(x, mpc):
            return make_mpc(libhyper.mpc_besseljn(int(v), x._mpc_, mp.prec))
    hx = x/2
    return hx**v * hyp0f1(v+1, -hx**2) / factorial(v)

jn = jv

def j0(x):
    """Bessel function J_0(x)."""
    return jv(0, x)

def j1(x):
    """Bessel function J_1(x)."""
    return jv(1, x)

@funcwrapper
def lambertw(z, k=0, approx=None):
    """
    The Lambert W function W(z) is defined as the inverse function
    of w*exp(w). In other words, the value of W(z) is such that
    z = W(z)*exp(W(z)) for any complex number z.

    The Lambert W function is a multivalued function with infinitely
    many branches. Each branch gives a separate solution of the
    equation w*exp(w). All branches are supported by :func:`lambertw`:

    * ``lambertw(z)`` gives the principal solution (branch 0)

    * ``lambertw(z, k)`` gives the solution on branch k

    The Lambert W function has two partially real branches: the
    principal branch (k = 0) is real for real z > -1/e, and the
    k = -1 branch is real for -1/e < z < 0. All branches except
    k = 0 have a logarithmic singularity at 0.

    **Basic examples**

    The Lambert W equation is the inverse of w*exp(w)::

        >>> from mpmath import *
        >>> mp.dps = 35
        >>> w = lambertw(1)
        >>> print w
        0.56714329040978387299996866221035555
        >>> print w*exp(w)
        1.0

    Any branch gives a valid inverse::

        >>> w = lambertw(1, k=3)
        >>> print w    # doctest: +NORMALIZE_WHITESPACE
        (-2.8535817554090378072068187234910812 + 
          17.113535539412145912607826671159289j)
        >>> print w*exp(w)
        (1.0 + 3.5075477124212226194278700785075126e-36j)

    **Applications to equation-solving**

    The Lambert W function can give the value of the infinite power
    tower z^(z^(z^(...)))::

        >>> def tower(z, n):
        ...     if n == 0:
        ...         return z
        ...     return z ** tower(z, n-1)
        ...
        >>> tower(0.5, 100)
        0.641185744504986
        >>> mp.dps = 50
        >>> print -lambertw(-log(0.5))/log(0.5)
        0.6411857445049859844862004821148236665628209571911

    **Properties**

    The Lambert W function grows roughly like the natural logarithm
    for large arguments::

        >>> mp.dps = 15
        >>> print lambertw(1000)
        5.2496028524016
        >>> print log(1000)
        6.90775527898214
        >>> print lambertw(10**100)
        224.843106445119
        >>> print log(10**100)
        230.258509299405

    The principal branch of the Lambert W function has a rational
    Taylor series expansion around 0::

        >>> nprint(taylor(lambertw, 0, 6), 10)
        [0.0, 1.0, -1.0, 1.5, -2.666666667, 5.208333333, -10.8]

    Some special values and limits are::

        >>> mp.dps = 15
        >>> print lambertw(0)
        0.0
        >>> print lambertw(1)
        0.567143290409784
        >>> print lambertw(e)
        1.0
        >>> print lambertw(inf)
        +inf
        >>> print lambertw(0, k=-1)
        -inf
        >>> print lambertw(0, k=3)
        -inf
        >>> print lambertw(inf, k=3)
        +inf

    The k = 0 and k = -1 branches join at z = -1/e where W(z) = -1
    for both branches. Since -1/e can only be represented approximately
    with mpmath numbers, evaluating the Lambert W function at this point
    only gives -1 approximately::

        >>> mp.dps = 25
        >>> print lambertw(-1/e, 0)
        -0.999999999999837133022867
        >>> print lambertw(-1/e, -1)
        -1.00000000000016286697718

    If -1/e happens to round in the negative direction, there might be
    a small imaginary part::

        >>> mp.dps = 15
        >>> print lambertw(-1/e)
        (-1.0 + 8.22007971511612e-9j)

    **Possible issues**

    The evaluation can become inaccurate very close to the branch point
    at -1/e. In some corner cases, :func:`lambertw` might currently
    fail to converge, or can end up on the wrong branch.

    **Algorithm**

    Halley's iteration is used to invert w*exp(w), using a first-order
    asymptotic approximation (O(log(w)) or O(w)) as the initial estimate.

    The definition, implementation and choice of branches is based
    on Corless et al, "On the Lambert W function", Adv. Comp. Math. 5
    (1996) 329-359, available online here:
    http://www.apmaths.uwo.ca/~djeffrey/Offprints/W-adv-cm.pdf

    TODO: use a series expansion when extremely close to the branch point
    at -1/e and make sure that the proper branch is chosen there
    """
    if isnan(z):
        return z
    mp.prec += 20
    # We must be extremely careful near the singularities at -1/e and 0
    u = exp(-1)
    if abs(z) <= u:
        if not z:
            # w(0,0) = 0; for all other branches we hit the pole
            if not k:
                return z
            return -inf
        if not k:
            w = z
        # For small real z < 0, the -1 branch behaves roughly like log(-z)
        elif k == -1 and not z.imag and z.real < 0:
            w = log(-z)
        # Use a simple asymptotic approximation.
        else:
            w = log(z)
            # The branches are roughly logarithmic. This approximation
            # gets better for large |k|; need to check that this always
            # works for k ~= -1, 0, 1.
            if k: w += k * 2*pi*j
    elif k == 0 and z.imag and abs(z) <= 0.6:
        w = z
    else:
        if z == inf: return z
        if z == -inf: return nan
        # Simple asymptotic approximation as above
        w = log(z)
        if k: w += k * 2*pi*j
    # Use Halley iteration to solve w*exp(w) = z
    two = mpf(2)
    weps = ldexp(eps, 15)
    for i in xrange(100):
        ew = exp(w)
        wew = w*ew
        wewz = wew-z
        wn = w - wewz/(wew+ew-(w+two)*wewz/(two*w+two))
        if abs(wn-w) < weps*abs(wn):
            return wn
        else:
            w = wn
    print "Warning: Lambert W iteration failed to converge:", z
    return wn

if __name__ == '__main__':
    import doctest
    doctest.testmod()