from ..shared.sharedcontext import *
from ..geometry.point import *
from ..operations.crypto_operations import *

from shapely import Polygon as PlainPolygon, MultiPolygon as PlainMultiPolygon


def ray_casting(poly: PlainPolygon | PlainMultiPoint, point: Point | MultiPoint) -> Ciphertext:
    #print("\n\n Calculating point in polygon")

    cc = get_shared_context().cc
    secKey = get_shared_context().secretKey

    if isinstance(poly, PlainMultiPolygon):
        poly = poly.geoms[0]

    edge_result = []

    for i in range(1, len(poly.exterior.coords)):
        info("Edge " +  str(i))
        info(poly.exterior.coords[i])
        debug(decrypt(point.x))
        debug(decrypt(point.y))

        # Extract current edge
        v1 = PlainPoint(poly.exterior.coords[i-1])
        v2 = PlainPoint(poly.exterior.coords[i])

        minY = min(v1.y, v2.y)
        maxY = max(v1.y, v2.y)

        #if minY == maxY:
        #    continue

        #print(minY, maxY)

        #v1, v2 = extend_line_to_borders(v1, v2)

        # Determine lower edge
        vH = None
        vL = None
        if minY == v1.y:
            vL = v1
            vH = v2
        else:
            vH = v1
            vL = v2

        debug("Level1: " + str(point.x.GetLevel()))

        # Check if point is within y-bounds of vertice
        comp1 = greater_than(point.y, minY)
        debug("Level2: " + str(comp1.GetLevel()))
        comp2 = less_than(point.y, maxY) #less_or_equal(point.y, maxY)
        ybounds = cc.EvalMult(comp1, comp2)
        debug("Level3: " + str(ybounds.GetLevel()))

        debug("comp1: " + decrypt(comp1))
        debug("comp2: " + decrypt(comp2))
        debug("ybounds: " + decrypt(ybounds))

        # Check if point is within

        # Consider a triangle of v1 -> v2 -> point
        # Now calculate the determinant of this triangle as (vH.x - vL.x) * (P.y - vL.y) - (vH.y - vL.y) * (P.x - vL.x)
        # The sign of this result determines the orientation of the triangle -> i.e. if the point is on the "within" side of the vertex

        term1 = cc.EvalMult(vH.x - vL.x, cc.EvalSub(point.y, vL.y))
        term2 = cc.EvalMult(vH.y - vL.y, cc.EvalSub(point.x, vL.x))
        orientation = cc.EvalSub(term1, term2)

        # Scale determinant (orientation) by 1/dist(v1_v2)
        sc = 1 / (vL.distance(vH))
        print("Scale: ", sc)
        orientation = cc.EvalMult(orientation, sc)

        debug("Orientation: " + decrypt(orientation))
        debug("Level4: " + str(orientation.GetLevel()))
        orientation = greater_than(orientation, 0)
        debug("orientation sign: " + decrypt(orientation))
        debug("Level5: " + str(orientation.GetLevel()))

        res = cc.EvalMult(orientation, ybounds)
        debug("Level6: " + str(res.GetLevel()))
        #print("orientation", orientation.GetLevel())
        #print("res", res.GetLevel())
        #print("res", cc.Decrypt(secKey, res))
        debug("res: " + decrypt(res))
        #res = cc.EvalBootstrap(res)
        edge_result.append(res)

    while len(edge_result) > 1:
        temp = []

        for i in range(0, len(edge_result), 2):
            if i + 1 < len(edge_result):
                temp.append(eval_xor(edge_result[i], edge_result[i + 1]))
            else:
                temp.append(edge_result[i])

        edge_result = temp
    #print("result: ", cc.Decrypt(secKey, edge_result[0]))
    debug("Level7: " + str(edge_result[0].GetLevel()))
    return edge_result[0]