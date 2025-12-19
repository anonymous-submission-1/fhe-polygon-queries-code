from openfhe import Ciphertext

from ..shared.sharedcontext import get_shared_context
import math

from logging import debug

####################################

high_poly_0 = [
    0.0, 0.637264256439317, 0.0, -0.213842328443467, 0.0, 0.130067088964233,
    0.0, -0.094900503288337, 0.0, 0.076054068544858, 0.0, -0.064781178309292,
    0.0, 0.057798275228846, 0.0, -0.527466599100892
]

# Second polynomial (P[1])
high_poly_1 = [
    0.0, 0.638633544172149, 0.0, -0.214296203226736, 0.0, 0.130336316666621,
    0.0, -0.095089434109897, 0.0, 0.076197435568149, 0.0, -0.064894720203208,
    0.0, 0.057890429276374, 0.0, -0.526431900775910
]

# Third polynomial (P[2])
high_poly_2 = [
    0.0, 0.655827163667683, 0.0, -0.219992078841666, 0.0, 0.133710987614404,
    0.0, -0.097453181948996, 0.0, 0.077986273025004, 0.0, -0.066306069214147,
    0.0, 0.059029928660978, 0.0, -0.513428948233223
]

# Fourth polynomial (P[3])
high_poly_3 = [
    0.0, 0.848272020265017, 0.0, -0.283222947336856, 0.0, 0.170537464912271,
    0.0, -0.122545679263150, 0.0, 0.096213959131427, 0.0, -0.079856884718538,
    0.0, 0.069051721704207, 0.0, -0.366243208559666
]

# Fifth polynomial (P[4])
high_poly_4 = [
    0.0, 1.266251221054401, 0.0, -0.403857211586635, 0.0, 0.221703806600361,
    0.0, -0.138374487201497, 0.0, 0.089632575481289, 0.0, -0.058041955517619,
    0.0, 0.036787620739050, 0.0, -0.022472368209582, 0.0, 0.013044586623723,
    0.0, -0.007081628411702, 0.0, 0.003520197348144, 0.0, -0.001550510193022,
    0.0, 0.000569322069022, 0.0, -0.000152676931906
]


###################################

"""mid_poly_0 = [
    0, 0.665093739948, 0, -0.228170738557,
    0, 0.146103684734, 0, -0.537737925966
]

mid_poly_1 = [
    0, 0.779910673744, 0, -0.264336161987,
    0, 0.165121807135, 0, -0.453144953208
]

mid_poly_2 = [
    0, 1.265546590016, 0, -0.401757188872,
    0, 0.218178903398, 0, -0.133488712988,
    0, 0.083510896154, 0, -0.050895730803,
    0, 0.040417362536
]"""

mid_poly_0 = [
    0, 0.652224297748, 0, -0.224048864800,
    0, 0.143846107528, 0, -0.549115368008
]

mid_poly_1 = [
    0, 0.791157867100, 0, -0.264550978267,
    0, 0.159818415478, 0, -0.115398500128,
    0, 0.091154157986, 0, -0.076259368082,
    0, 0.066633773313, 0, -0.407742986433
]

mid_poly_2 = [
    0, 1.265455164874, 0, -0.401497385850,
    0, 0.217869401480, 0, -0.133225775322,
    0, 0.083411363696, 0, -0.051074694030,
    0, 0.029474724919, 0, -0.019486096223
]



###################################


####

low_poly_0 = [
    0.0, 1.27249864309, 0.0, -0.42227937450, 0.0, 0.25094021159,
    0.0, -0.17685903546, 0.0, 0.13519896360, 0.0, -0.10765440484,
    0.0, 0.08889467315, 0.0, -0.07438935861, 0.0, 0.06318058487,
    0.0, -0.05416884920, 0.0, 0.04691395023, 0.0, -0.04055666857,
    0.0, 0.03497999233, 0.0, -0.12558553554
]

####

poly_2x = [
    0, 1.125, 0, -0.125
]

####################################

def rotate_across(ciph: list[Ciphertext]) -> list[Ciphertext]:
    cc = get_shared_context().cc
    batch_size = get_shared_context().batch_size
    mask_left = cc.MakeCKKSPackedPlaintext([1] + [0] * (batch_size - 1))
    mask_right = cc.MakeCKKSPackedPlaintext([0] + [1] * (batch_size - 1))

    rot_ciph = [cc.EvalRotate(c, -1) for c in ciph]

    result = rot_ciph[:]

    result[0] = cc.EvalAdd(cc.EvalMult(rot_ciph[-1], mask_left), cc.EvalMult(rot_ciph[0], mask_right))
    for i in range(1, len(ciph)):
        # Combine first element (rotated from last element) of left batch with other elements from right batch
        result[i] = cc.EvalAdd(cc.EvalMult(rot_ciph[i-1], mask_left), cc.EvalMult(rot_ciph[i], mask_right))

    return result

def rotate_left_across(ciph: list[Ciphertext]) -> list[Ciphertext]:
    cc = get_shared_context().cc
    batch_size = get_shared_context().batch_size
    mask_left = cc.MakeCKKSPackedPlaintext([1] + [0] * (batch_size - 1))
    mask_right = cc.MakeCKKSPackedPlaintext([0] + [1] * (batch_size - 1))

    rot_ciph = [cc.EvalRotate(c, 1) for c in ciph]

    result = rot_ciph[:]

    result[0] = cc.EvalAdd(cc.EvalMult(rot_ciph[-1], mask_left), cc.EvalMult(rot_ciph[0], mask_right))
    for i in range(1, len(ciph)):
        # Combine first element (rotated from last element) of left batch with other elements from right batch
        result[i] = cc.EvalAdd(cc.EvalMult(rot_ciph[i-1], mask_left), cc.EvalMult(rot_ciph[i], mask_right))

    return result

########################################################################################################################

def combine_ciphertexts(ciph: list[Ciphertext]):
    """
    Combines the first values of a list of ciphertexts into a new one (e.g. [[1, 1], [2, 2]] -> [1, 2]
    :param ciph: List of ciphertexts
    :return:
    """
    cc = get_shared_context().cc
    if len(ciph) > get_shared_context().batch_size:
        raise ValueError("Number of points cannot exceed batch size")

    mask = get_shared_context().mask_one_zeros

    new_ciph = cc.EvalMult(ciph[0], mask)

    for i in range(1, len(ciph)):
        mask = cc.EvalRotate(mask, -1)

        new_ciph = cc.EvalAdd(new_ciph, cc.EvalMult(ciph[i], mask))

    return new_ciph

########################################################################################################################

# Takes a number between -1 and 1 and returns the sign (-1, 0 or 1)
def sign(ciph: Ciphertext, low_precision: bool = False) -> Ciphertext:
    cc = get_shared_context().cc

    if low_precision:

        # Low precision mode:
        # Poly degrees: 27

        # # user setting parameters
        # #long alpha = 4;         // precision parameter alpha
        # #long max_factor = 1;    // max_factor = 1 for comparison operation. max_factor > 1 for max/ReLU operation
        # #long maxdeg = 63;               // 31 or 63
        # #bool is_comp = true;    // true: comparison operation, false: max/ReLU operation
        # #long level = 22;                // total level consumption D. just for compute_min_multdepth_update

        result = cc.EvalChebyshevSeries(ciph, mid_poly_0, -1, 1)
        result = cc.EvalChebyshevSeries(result, mid_poly_1, -1, 1)
        result = cc.EvalChebyshevSeries(result, mid_poly_2, -1, 1)
        result = cc.EvalChebyshevSeries(result, poly_2x, -1, 1)

        return result

    else:
        #debug("Sign function:")
        # High precision mode:
        result = cc.EvalChebyshevSeries(ciph, high_poly_0, -1, 1)
        # print(cc.Decrypt(get_shared_context().secretKey, result), result.GetLevel())
        result = cc.EvalChebyshevSeries(result, high_poly_1, -1, 1)
        # print(cc.Decrypt(get_shared_context().secretKey, result), result.GetLevel())
        #result = cc.EvalBootstrap(result, 2, 12)
        #debug(str(cc.Decrypt(get_shared_context().secretKey, result)) + str(result.GetLevel()))

        result = cc.EvalChebyshevSeries(result, high_poly_2, -1, 1)
        # print(cc.Decrypt(get_shared_context().secretKey, result), result.GetLevel())
        result = cc.EvalChebyshevSeries(result, high_poly_3, -1, 1)
        # print(cc.Decrypt(get_shared_context().secretKey, result), result.GetLevel())
        #result = cc.EvalBootstrap(result, 2, 12)
        #debug(str(cc.Decrypt(get_shared_context().secretKey, result)) + str(result.GetLevel()))

        result = cc.EvalChebyshevSeries(result, high_poly_4, -1, 1)
        # print(cc.Decrypt(get_shared_context().secretKey, result), result.GetLevel())
        result = cc.EvalChebyshevSeries(result, poly_2x, -1, 1)

        #result = cc.EvalBootstrap(result, 2, 12)
        #debug("DONE")


        return result

def greater_than(ciph1: Ciphertext, ciph2: Ciphertext | float, low_precision: bool = False) -> Ciphertext:
    cc = get_shared_context().cc

    result = sign(cc.EvalSub(ciph1, ciph2), low_precision)
    return cc.EvalMult(0.5, cc.EvalAdd(result, 1))


def less_than(ciph1: Ciphertext, ciph2: Ciphertext | float, low_precision: bool = False) -> Ciphertext:
    cc = get_shared_context().cc

    result = sign(cc.EvalSub(ciph2, ciph1), low_precision)
    return cc.EvalMult(0.5, cc.EvalAdd(result, 1))

def equals(ciph1: Ciphertext, ciph2: Ciphertext | float, low_precision: bool = False) -> Ciphertext:
    cc = get_shared_context().cc

    result = sign(cc.EvalSub(ciph1, ciph2), low_precision)
    return cc.EvalSub(1, cc.EvalSquare(result))


def greater_or_equal(ciph1: Ciphertext, ciph2: Ciphertext | float, low_precision: bool = False) -> Ciphertext:
    cc = get_shared_context().cc

    res = greater_than(ciph1, ciph2, low_precision)
    res = greater_than(res, 0.25, True)
    return res

def less_or_equal(ciph1: Ciphertext, ciph2: Ciphertext | float, low_precision: bool = False) -> Ciphertext:
    cc = get_shared_context().cc

    res = less_than(ciph1, ciph2, low_precision)
    res = greater_than(res, 0.25, True)
    return res



########################################################################################################################


def eval_xor(a: Ciphertext, b: Ciphertext) -> Ciphertext:
    # a + b - a*b * (1 + a + b - a*b)
    #ab = cc.EvalMult(a, b)
    #term1 = cc.EvalMult(ab, cc.EvalSub(cc.EvalAdd(cc.EvalAdd(a, 1), b), ab))
    #res = cc.EvalSub(cc.EvalAdd(a, b), term1)

    cc = get_shared_context().cc
    res = cc.EvalSub(a, b)
    res = cc.EvalMult(res, res)

    return res

def eval_not(a: Ciphertext) -> Ciphertext:
    # 1 - a
    return get_shared_context().cc.EvalSub(1, a)

def eval_or(a: Ciphertext, b: Ciphertext) -> Ciphertext:
    # a + b - a*b
    cc = get_shared_context().cc
    res1 = cc.EvalAdd(a, b)
    res2 = cc.EvalMult(a, b)

    return cc.EvalSub(res1, res2)

########################################################################################################################


def divide(a: Ciphertext, b: Ciphertext, scale: int = 100_000, degree: int = 4031, bootstrap_precision: int = 12) -> Ciphertext:
    cc = get_shared_context().cc
    #debug("Level before division: " + str(b.GetLevel()))
    values_sc = cc.EvalMult(b, scale)
    #debug(cc.Decrypt(get_shared_context().secretKey, values_sc))
    res = cc.EvalChebyshevFunction(lambda x: 1 / x, values_sc, 1, scale, degree)
    #debug(cc.Decrypt(get_shared_context().secretKey, res))
    #res = cc.EvalBootstrap(res, 2, bootstrap_precision)
    #debug(cc.Decrypt(get_shared_context().secretKey, res))
    #res = cc.EvalMult(res, scale)
    #debug(cc.Decrypt(get_shared_context().secretKey, res))
    #debug("Level after division: " + str(res.GetLevel()))

    denom = cc.EvalMult(res, scale)

    #debug("Num: " + str(cc.Decrypt(get_shared_context().secretKey, a)))
    #debug("Denom" + str(cc.Decrypt(get_shared_context().secretKey, denom)))

    return cc.EvalMult(a, denom)

## VERMUTLICHES PROBLEM: Nicht genug levelübrig bei Multiplikation mit 100_000, deshalb Overflow


def sqrt(a: Ciphertext, scale: int = 100_000, degree: int = 1007) -> Ciphertext:
    cc = get_shared_context().cc
    res = cc.EvalChebyshevFunction(lambda x: math.sqrt(x), a, 1/scale, 1, degree)
    return res

def acos(a: Ciphertext, degree: int = 1007) -> Ciphertext:
    cc = get_shared_context().cc
    res = cc.EvalChebyshevFunction(lambda x: math.acos(x), a, -1, 1, degree)
    return res


###########################################################

def decrypt(ciph: Ciphertext):
    cc = get_shared_context().cc
    dec = cc.Decrypt(get_shared_context().secretKey, ciph)
    return str(dec.GetCKKSPackedValue()[:4]) + " " + str(dec.GetLogPrecision()) + " bit - " + str(ciph.GetLevel())