from openfhe import Ciphertext, CryptoContext, PublicKey
from shapely.io import from_wkt

from ..shared.sharedcontext import get_shared_context
from ..shared.scale import scale_down_coords, scale_up_x, scale_up_y, scale_up_coords, scale_down_x, scale_down_y
from shapely import Point as PlainPoint
from shapely import MultiPoint as PlainMultiPoint


class Point():
    def __init__(self, geom=None):
        self.x: Ciphertext | None = None
        self.y: Ciphertext | None = None
        self.cc: CryptoContext = get_shared_context().cc
        self.publicKey: PublicKey = get_shared_context().publicKey

        if geom is not None:
            self.encrypt(geom)

    def set_coords(self, x: Ciphertext, y: Ciphertext):
        self.x = x
        self.y = y

    def encrypt(self, geom: str | PlainPoint):
        plain_geometry = None
        if isinstance(geom, str):
            plain_geometry = from_wkt(geom)
        if isinstance(geom, PlainPoint):
            plain_geometry = geom

        x_coords = [scale_down_x(plain_geometry.x)] * get_shared_context().batch_size
        y_coords = [scale_down_y(plain_geometry.y)] * get_shared_context().batch_size

        self.x = self.cc.Encrypt(self.publicKey, self.cc.MakeCKKSPackedPlaintext(x_coords))
        self.y = self.cc.Encrypt(self.publicKey, self.cc.MakeCKKSPackedPlaintext(y_coords))

    def decrypt(self, privKey):
        x_coords = [scale_up_x(c.real) for c in self.cc.Decrypt(self.x, privKey).GetCKKSPackedValue()]
        y_coords = [scale_up_y(c.real) for c in self.cc.Decrypt(self.y, privKey).GetCKKSPackedValue()]

        print(x_coords, type(x_coords))
        print(y_coords, type(y_coords))

        return PlainPoint([x_coords[0], y_coords[0]])

class MultiPoint:
    def __init__(self, geom=None):
        self.x : Ciphertext | None = None
        self.y : Ciphertext | None = None
        self.cc : CryptoContext = get_shared_context().cc
        self.publicKey : PublicKey = get_shared_context().publicKey

        if geom is not None:
            if isinstance(geom, str) or isinstance(geom, PlainMultiPoint):
                self.encrypt(geom)
            if isinstance(geom, list):
                if all(isinstance(g, Point) for g in geom):
                    self.from_points(geom)

    def encrypt(self, geom: str | PlainMultiPoint):
        plain_geometry = None
        if isinstance(geom, str):
            plain_geometry = from_wkt(geom)
        if isinstance(geom, PlainMultiPoint):
            plain_geometry = geom

        x_coords, y_coords = map(list, zip(*[scale_down_coords([point.x, point.y]) for point in plain_geometry.geoms]))

        self.x = self.cc.Encrypt(self.publicKey, self.cc.MakeCKKSPackedPlaintext(x_coords))
        self.y = self.cc.Encrypt(self.publicKey, self.cc.MakeCKKSPackedPlaintext(y_coords))

    def from_points(self, geom: list[Point]):
        """
        - Check if len(points) not bigger than batchsize
        - Go through points (for i in range(len(geom)))
            - Rotate mask_one_zeros i times
            - Multiply x and y coords of ith point by mask
            - Add to result ciph new_x and new_y
        - Set self.x and self.y from new_x and new_y
        :param geom:
        :return:
        """
        cc = get_shared_context().cc
        if len(geom) > get_shared_context().batch_size:
            raise ValueError("Number of points cannot exceed batch size")

        mask = get_shared_context().mask_one_zeros

        new_x = cc.EvalMult(geom[0].x, mask)
        new_y = cc.EvalMult(geom[0].y, mask)

        for i in range(1, len(geom)):
            mask = cc.EvalRotate(mask, -1)

            new_x = cc.EvalAdd(new_x, cc.EvalMult(geom[i].x, mask))
            new_y = cc.EvalAdd(new_y, cc.EvalMult(geom[i].y, mask))

        self.x = new_x
        self.y = new_y



    def decrypt(self, privKey):
        x_coords = [scale_up_x(c.real) for c in self.cc.Decrypt(self.x, privKey).GetCKKSPackedValue()]
        y_coords = [scale_up_y(c.real) for c in self.cc.Decrypt(self.y, privKey).GetCKKSPackedValue()]

        print(x_coords, type(x_coords))
        print(y_coords, type(y_coords))

        return PlainMultiPoint(list(zip(x_coords, y_coords)))

    def geoms(self, index: int) -> Point:
        """
        Goal: get single point from multipoint
        Get index (e.g. 2)
        Generate plain mask (e.g. [0, 0, 1, 0]
        Multiply x and y ciphertexts with the mask
        Calculate EvalSum for both
        Create new point object and return
        """
        pass
