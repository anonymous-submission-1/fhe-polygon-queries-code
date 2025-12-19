from ..shared.sharedcontext import *
from ..geometry.point import *
from ..operations.crypto_operations import *

from shapely import Polygon as PlainPolygon, MultiPolygon as PlainMultiPolygon


def edge_orientation(poly: PlainPolygon | PlainMultiPolygon, point: Point | MultiPoint) -> Ciphertext:
    #print("\n\n Calculating point in polygon")

    cc = get_shared_context().cc
    secKey = get_shared_context().secretKey

    if isinstance(poly, PlainPolygon):
        polygons = PlainMultiPolygon([poly])
    elif isinstance(poly, PlainMultiPolygon):
        polygons = poly

    result = []

    for ind, p in enumerate(polygons.geoms):

        info("\nSub-polygon " + str(ind) + " (" + str(len(p.exterior.coords) - 1) + " edges)")

        edge_result = get_shared_context().ciph_zero

        for i in range(1, len(p.exterior.coords)):
            info("Edge " +  str(i))
            info(p.exterior.coords[i])
            debug(decrypt(point.x))
            debug(decrypt(point.y))

            # Extract current edge
            v1 = PlainPoint(p.exterior.coords[i-1])
            v2 = PlainPoint(p.exterior.coords[i])

            # Check if point is within

            # Consider a triangle of v1 -> v2 -> point
            # Now calculate the determinant of this triangle as (vH.x - vL.x) * (P.y - vL.y) - (vH.y - vL.y) * (P.x - vL.x)
            # The sign of this result determines the orientation of the triangle -> i.e. if the point is on the "within" side of the vertex

            term1 = cc.EvalMult(v1.x - v2.x, cc.EvalSub(point.y, v2.y))
            term2 = cc.EvalMult(v1.y - v2.y, cc.EvalSub(point.x, v2.x))
            orientation = cc.EvalSub(term1, term2)

            debug("orient: " + decrypt(orientation))

            # Scale determinant (orientation) by 1/dist(v1_v2)
            sc = 1 / (v1.distance(v2))
            info("scale:" + str(sc))
            orientation = cc.EvalMult(orientation, sc)

            debug("orient_sc: " + decrypt(orientation))
            orientation = greater_than(orientation, 0)
            debug("orient_sign: " + decrypt(orientation))

            edge_result = cc.EvalAdd(edge_result, orientation)
            debug("edge_result: " + decrypt(edge_result))

        #edge_result = cc.EvalBootstrap(edge_result, 2, 12)
        info("edge_result: " + decrypt(edge_result))
        num_edges = len(p.exterior.coords)
        res = cc.EvalMult(edge_result, 1/num_edges)
        #print("scale: ", 1/num_edges)
        debug("res_scaled: " + decrypt(res))
        res = less_than(res, 0.5/num_edges, True)
        debug("res: " + decrypt(res))
        debug("\n")

        result.append(res)

    while len(result) > 1:
        temp = []
        for i in range(0, len(result), 2):
            if i + 1 < len(result):
                temp.append(eval_or(result[i], result[i + 1]))
            else:
                temp.append(result[i])
        result = temp

    return result[0]