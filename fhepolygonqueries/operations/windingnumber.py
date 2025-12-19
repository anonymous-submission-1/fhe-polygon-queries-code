from ..shared.sharedcontext import *
from ..geometry.point import *
from ..operations.crypto_operations import *

from shapely import Polygon as PlainPolygon
import math

def winding_number(poly: PlainPolygon, point: Point | MultiPoint) -> Ciphertext:
    cc = get_shared_context().cc
    secKey = get_shared_context().secretKey

    result = get_shared_context().ciph_zero

    for i in range(1, len(poly.exterior.coords)):
        info(f"Edge {i}")

        v1 = PlainPoint(poly.exterior.coords[i-1])
        v2 = PlainPoint(poly.exterior.coords[i])

        info(f"{v1}, {v2}")

        debug(decrypt(point.x))
        debug(decrypt(point.y))

        v1_diff_x = cc.EvalSub(v1.x, point.x)
        v1_diff_y = cc.EvalSub(v1.y, point.y)
        v2_diff_x = cc.EvalSub(v2.x, point.x)
        v2_diff_y = cc.EvalSub(v2.y, point.y)

        dot = cc.EvalAdd(cc.EvalMult(v1_diff_x, v2_diff_x), cc.EvalMult(v1_diff_y, v2_diff_y))

        debug("dot" + decrypt(dot))

        v1_len = cc.EvalAdd(cc.EvalSquare(v1_diff_x), cc.EvalSquare(v1_diff_y))
        v2_len = cc.EvalAdd(cc.EvalSquare(v2_diff_x), cc.EvalSquare(v2_diff_y))

        denom1 = sqrt(v1_len)
        denom2 = sqrt(v2_len)
        debug("denom1" + decrypt(denom1))
        debug("denom2" + decrypt(denom2))

        #denom = cc.EvalMult(v1_len, v2_len)
        #debug("denom" + str(cc.Decrypt(secKey, denom)) + str(denom.GetLevel()))
        #denom = sqrt(denom)
        #denom = cc.EvalChebyshevFunction(math.sqrt, cc.EvalMult(v1_len, v2_len), 0.00001, 1.5, 1007)
        #debug("denom sqrt" + str(cc.Decrypt(secKey, denom)) + str(denom.GetLevel()))
        #denom1 = cc.EvalBootstrap(denom1, 2, 21)
        #denom2 = cc.EvalBootstrap(denom2, 2, 21)
        #debug("denom sqrt" + str(cc.Decrypt(secKey, denom)) + str(denom.GetLevel()))


        #debug("num    " + decrypt(dot) + str(dot.GetLevel()))
        #debug("denom1  " + decrypt(denom1) + str(denom1.GetLevel()))
        #debug("denom2  " + decrypt(denom2) + str(denom2.GetLevel()))

        div1 = divide(dot, denom1, 100_000, 4031, 21)
        div2 = divide(get_shared_context().ciph_one, denom2, 100_000, 4031, 21)


        #angle = divide(dot, denom, scale=10_000)


        info("divide1 " + decrypt(div1))
        info("divide2 " + decrypt(div2))

        #angle = cc.EvalBootstrap(angle, 2, 17)
        #div1 = cc.EvalBootstrap(div1, 2, 21)
        #div2 = cc.EvalBootstrap(div2, 2, 21)

        #debug("angle1 boot" + str(cc.Decrypt(secKey, div1)) + str(div1.GetLevel()))
        #debug("angle2 boot" + str(cc.Decrypt(secKey, div2)) + str(div2.GetLevel()))

        #arccos = cc.EvalChebyshevFunction(math.acos, angle, -1, 1, 1007)
        div = cc.EvalMult(div1, div2)
        debug("div" + decrypt(div))
        div = cc.EvalBootstrap(div, 2, 21)
        debug("div_boot: " + decrypt(div))
        arccos = acos(div)

        info("arccos" + decrypt(arccos) + "\n")

        result = cc.EvalAdd(result, arccos)



    #print("Result", cc.Decrypt(secKey, result), result.GetLevel())
    #result = cc.EvalBootstrap(result, 2, 21)
    info("res1: " + decrypt(result))
    result = greater_than(cc.EvalMult(result, 0.1), 0.62831)
    info("res2: " + decrypt(result))

    return result