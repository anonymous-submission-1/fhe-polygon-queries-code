from .sharedcontext import get_shared_context
import shapely

def scale_down_coords(coords: list[float]) -> list[float]:
    x, y = coords

    scaled_x = scale_down_x(x) #x - get_shared_context().min_x) / (get_shared_context().max_x - get_shared_context().min_x)
    scaled_y = scale_down_y(y) #(y - get_shared_context().min_y) / (get_shared_context().max_y - get_shared_context().min_y)

    return [scaled_x, scaled_y]

def scale_down_x(x: float) -> float:
    x = x - get_shared_context().offset_x
    scaled_x = x / get_shared_context().scale
    scaled_x = min(max(0.0, scaled_x), 1.0)
    #x = max(get_shared_context().min_x, min(get_shared_context().max_x, x))
    #scaled_x = (x - get_shared_context().min_x) / (get_shared_context().max_x - get_shared_context().min_x)
    return scaled_x

def scale_down_y(y: float) -> float:
    y = y - get_shared_context().offset_y
    scaled_y = y / get_shared_context().scale
    scaled_y = min(max(0.0, scaled_y), 1.0)
    #y = max(get_shared_context().min_y, min(get_shared_context().max_y, y))
    #scaled_y = (y - get_shared_context().min_y) / (get_shared_context().max_y - get_shared_context().min_y)
    return scaled_y


def scale_up_coords(scaled_coords: list[float]) -> list[float]:
    scaled_x, scaled_y = scaled_coords

    original_x = scale_up_x(scaled_x)
    original_y = scale_up_y(scaled_y)

    return [original_x, original_y]

def scale_up_x(scaled_x: float) -> float:
    scaled_x = scaled_x  * get_shared_context().scale
    original_x = scaled_x + get_shared_context().offset_x
    #original_x = scaled_x * (get_shared_context().max_x - get_shared_context().min_x) + get_shared_context().min_x
    return original_x

def scale_up_y(scaled_y: float) -> float:
    scaled_y = scaled_y * get_shared_context().scale
    original_y = scaled_y + get_shared_context().offset_y
    #original_y = scaled_y * (get_shared_context().max_y - get_shared_context().min_y) + get_shared_context().min_y
    return original_y


#############


def scale_down_plain_geometry(geom):
    off_x = get_shared_context().offset_x
    off_y = get_shared_context().offset_y
    sc = get_shared_context().scale
    # shapely.transform
    # shapely.transform(LineString([(2, 2), (4, 4)]), lambda x: x * [2, 3])
    # scale_coordinates = lambda coords: [(coords[0] - offset_x) * scale_factor, (coords[1] - offset_y) * scale_factor]
    #return shapely.transform(geom, lambda x: [(x[0] - off_x) * sc, (x[1] - off_y) * sc])
    return shapely.transform(geom, lambda x: (x - [off_x, off_y]) / sc)

def scale_up_plain_geometry(geom):
    off_x = get_shared_context().offset_x
    off_y = get_shared_context().offset_y
    sc = get_shared_context().scale

    return shapely.transform(geom, lambda x: (x * sc) + [off_x, off_y])

