"""
This module implements basic floating-point operations: normalization,
comparison, addition, subtraction, multiplication, division, integer
powers.

"""

from util import *


fzero = (0, 0, 0)
fone = (1, 0, 1)
ftwo = (1, 1, 1)
ften = (5, 1, 3)
fhalf = (1, -1, 1)


def normalize(man, exp, prec, rounding):
    """Normalize the binary floating-point number represented by
    man * 2**exp to the specified precision level, rounding if the
    number of bits in the mantissa exceeds prec. The mantissa is also
    stripped of trailing zero bits, and its bits are counted. The
    returned value is a tuple (man, exp, bc)."""

    if not man:
        return (0, 0, 0)
    if prec < 100:
        bc = bitcount2(man)
    else:
        bc = bitcount(man)
    if bc > prec:
        man = rshift(man, bc-prec, rounding)
        exp += (bc - prec)

        # If shifting to a power of two, the bitcount may be wrong
        # and has to be redone. Check last 3 bits to avoid recounting
        # in most cases.
        if man & 7:
            bc = prec
        else:
            bc = bitcount(man)

    # Strip trailing zeros
    if not man & 1:
        tr = trailing_zeros(man)
        if tr:
            man >>= tr
            exp += tr
            bc -= tr
    #assert bitcount(man) <= prec
    if not man:
        return (0, 0, 0)
    return (man, exp, bc)


def feq(s, t):
    """Floating-point equality testing. The numbers are assumed to
    be normalized, meaning that this simply performs tuple comparison."""
    return s == t


def fcmp(s, t):
    """Floating-point comparison. Return -1 if s < t, 0 if s == t,
    and 1 if s > t."""

    # An inequality between two numbers s and t is determined by looking
    # at the value of s-t. A full floating-point subtraction is relatively
    # slow, so we first try to look at the exponents and signs of s and t.
    sman, sexp, sbc = s
    tman, texp, tbc = t

    # Very easy cases: check for 0's and opposite signs
    if not tman: return cmp(sman, 0)
    if not sman: return cmp(0, tman)
    if sman > 0 and tman < 0: return 1
    if sman < 0 and tman > 0: return -1

    # In this case, the numbers likely have the same magnitude
    if sexp == texp: return cmp(sman, tman)

    # The numbers have the same sign but different exponents. In this
    # case we try to determine if they are of different magnitude by
    # checking the position of the highest set bit in each number.
    a = sbc + sexp
    b = tbc + texp
    if sman > 0:
        if a < b: return -1
        if a > b: return 1
    else:
        if a < b: return 1
        if a < b: return -1

    # The numbers have similar magnitude but different exponents.
    # So we subtract and check the sign of resulting mantissa.
    return cmp(fsub(s, t, 5, ROUND_FLOOR)[0], 0)


def fpos(x, prec, rounding):
    return normalize(x[0], x[1], prec, rounding)


def fadd(s, t, prec, rounding):
    """Floating-point addition. Given two tuples s and t containing the
    components of floating-point numbers, return their sum rounded to 'prec'
    bits using the 'rounding' mode, represented as a tuple of components."""

    #  General algorithm: we set min(s.exp, t.exp) = 0, perform exact integer
    #  addition, and then round the result.
    #                   exp = 0
    #                       |
    #                       v
    #          11111111100000   <-- s.man (padded with zeros from shifting)
    #      +        222222222   <-- t.man (no shifting necessary)
    #          --------------
    #      =   11111333333333

    # We assume that s has the higher exponent. If not, just switch them:
    if t[1] > s[1]:
        s, t = t, s

    sman, sexp, sbc = s
    tman, texp, tbc = t

    # Check if one operand is zero. Zero always has exp = 0; if the
    # other operand has a large exponent, its mantissa will unnecessarily
    # be shifted a huge number of bits if we don't check for this case.
    if not tman:
        return normalize(sman, sexp, prec, rounding)
    if not sman:
        return normalize(tman, texp, prec, rounding)

    # More generally, if one number is huge and the other is small,
    # and in particular, if their mantissas don't overlap at all at
    # the current precision level, we can avoid work.

    #       precision
    #    |            |
    #     111111111
    #  +                 222222222
    #     ------------------------
    #  #  1111111110000...

    # However, if the rounding isn't to nearest, correct rounding mandates
    # the result should be adjusted up or down.

    if sexp - texp > 10:
        bitdelta = (sbc + sexp) - (tbc + texp)
        if bitdelta > prec + 5:
            if rounding > 4:     # nearby rounding
                return normalize(sman, sexp, prec, rounding)

            # shift s and add a dummy bit outside the precision range to
            # force rounding up or down
            offset = min(bitdelta + 3, prec+3)
            sman <<= offset
            if tman > 0:
                sman += 1
            else:
                sman -= 1
            return normalize(sman, sexp-offset, prec, rounding)

    # General case
    return normalize(tman+(sman<<(sexp-texp)), texp, prec, rounding)


def fsub(s, t, prec, rounding):
    """Floating-point subtraction"""
    return fadd(s, (-t[0], t[1], t[2]), prec, rounding)


def fneg(s, prec, rounding):
    """Floating-point negation. In addition to changing sign, rounds to
    the specified precision."""
    return normalize(-s[0], s[1], prec, rounding)


def fneg_noround(s):
    """Negate without normalizing"""
    return (-s[0], s[1], s[2])


def fabs(s, prec, rounding):
    man, exp, bc = s
    if man < 0:
        return normalize(-man, exp, prec, rounding)
    return normalize(man, exp, prec, rounding)


def fmul(s, t, prec, rounding):
    """Floating-point multiplication"""

    sman, sexp, sbc = s
    tman, texp, tbc = t

    # This is very simple. A possible optimization would be to throw
    # away some bits when prec is much smaller than sbc+tbc
    return normalize(sman*tman, sexp+texp, prec, rounding)


def fdiv(s, t, prec, rounding):
    """Floating-point division"""
    sman, sexp, sbc = s
    tman, texp, tbc = t

    # Perform integer division between mantissas. The mantissa of s must
    # be padded appropriately to preserve accuracy.
    
    # Note: this algorithm does produce slightly wrong rounding in corner
    # cases. Padding with a few extra bits makes the chance very small.
    # Changing '12' to something lower will reveal the error in the
    # test_standard_float test case
    extra = prec - sbc + tbc + 12
    if extra < 12:
        extra = 12

    return normalize((sman<<extra)//tman, sexp-texp-extra, prec, rounding)

def fdiv2_noround(s):
    """Quickly divide by two without rounding"""
    man, exp, bc = s
    if not man:
        return s
    return man, exp-1, bc


def fpow(s, n, prec, rounding):
    """Compute s**n, where n is an integer"""
    n = int(n)
    if n == 0: return fone
    if n == 1: return normalize(s[0], s[1], prec, rounding)
    if n == 2: return fmul(s, s, prec, rounding)
    if n == -1: return fdiv(fone, s, prec, rounding)
    if n < 0:
        return fdiv(fone, fpow(s, -n, prec+3, ROUND_FLOOR), prec, rounding)
    # Now we perform binary exponentiation. Need to estimate precision
    # to avoid rounding from temporary operations. Roughly log_2(n)
    # operations are performed.
    prec2 = prec + int(4*math.log(n, 2) + 4)
    man, exp, bc = normalize(s[0], s[1], prec2, ROUND_FLOOR)
    pm, pe, pbc = fone
    while n:
        if n & 1:
            pm, pe, pbc = normalize(pm*man, pe+exp, prec2, ROUND_FLOOR)
            n -= 1
        man, exp, bc = normalize(man*man, exp+exp, prec2, ROUND_FLOOR)
        n = n // 2
    return normalize(pm, pe, prec, rounding)
