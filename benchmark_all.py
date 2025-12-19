# benchmark_runner.py
import argparse
import json
import fcntl
from time import time
from datetime import datetime
import uuid
import os
import logging

from shapely.geometry import MultiPoint as PlainMultiPoint, shape, Polygon as PlainPolygon, MultiPolygon as PlainMultiPolygon

import fhepolygonqueries
from fhepolygonqueries.operations import ray_casting, winding_number, edge_orientation
from fhepolygonqueries.shared.scale import scale_down_plain_geometry
from fhepolygonqueries import create_shared_context, get_shared_context

from openfhe import SecurityLevel
from openfhe import Serialize, SerializeEvalMultKeyString, SerializeEvalAutomorphismKeyString, BINARY

logging.basicConfig(level=logging.DEBUG)

# ---------------------------------------------------------------------------
# Loading utilities
# ---------------------------------------------------------------------------
def load_polygons(path):
    with open(path, "r") as f:
        data = json.load(f)
    features = data.get("features", []) if data.get("type") == "FeatureCollection" else [data]
    geometries = []
    for feature in features:
        geom = feature.get("geometry", {})
        if geom.get("type") == "Polygon":
            coords = geom["coordinates"]
            geometries.append(PlainPolygon(coords[0], coords[1:] if len(coords) > 1 else None))
        elif geom.get("type") == "MultiPolygon":
            polys = [PlainPolygon(c[0], c[1:] if len(c) > 1 else None) for c in geom["coordinates"]]
            geometries.append(PlainMultiPolygon(polys))
    return geometries

def load_points(filename):
    with open(filename, "r") as f:
        data = json.load(f)
    geom = data["features"][0]["geometry"]
    return list(shape(geom).geoms)

# ---------------------------------------------------------------------------
# Output file handling
# ---------------------------------------------------------------------------
def init_results_file(folder="results"):
    os.makedirs(folder, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    uid = str(uuid.uuid4())[:8]
    path = os.path.join(folder, f"benchmark_{timestamp}_{uid}.json")
    with open(path, "w") as f:
        f.write("[]")
    return path

def append_result(filepath, result):
    with open(filepath, "r+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        data = json.load(f)
        data.append(result)
        f.seek(0)
        json.dump(data, f, indent=2)
        f.truncate()
        fcntl.flock(f, fcntl.LOCK_UN)

# ---------------------------------------------------------------------------
# Benchmarking
# ---------------------------------------------------------------------------
def run_single_benchmark(cc, secKey, points, poly, algo, batch_size, scale, first, poly_id, test_mode):
    start = time()
    result = algo(scale_down_plain_geometry(poly), points)
    elapsed = time() - start

    decrypted = cc.Decrypt(secKey, result).GetCKKSPackedValue()
    decrypted_vals = [v.real for v in decrypted]

    cc_ser = Serialize(cc, BINARY)
    pub_ser = Serialize(get_shared_context().publicKey, BINARY)
    sec_ser = Serialize(secKey, BINARY)
    ciph_ser = Serialize(points.x, BINARY)
    mult_ser = SerializeEvalMultKeyString(BINARY, "")
    auto_ser = SerializeEvalAutomorphismKeyString(BINARY, "")

    return {
        "poly_id": poly_id,
        "algo": algo.__name__,
        "batch_size": batch_size,
        "parameters": {
            "scaleMod": scale,
            "firstMod": first,
            "level": args.level,
            "testing_mode": test_mode,
        },
        "results": {
            "decrypted_values": decrypted_vals,
            "avg_runtime_sec": elapsed,
            "memory": {
                "cc": len(cc_ser),
                "pubkey": len(pub_ser),
                "secKey": len(sec_ser),
                "ciph": len(ciph_ser),
                "multKey": len(mult_ser),
                "automorphismKey": len(auto_ser),
            }
        }
    }

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(description="Encrypted Polygon-in-Polygon Benchmark Runner")

    parser.add_argument("--batch_size", type=int, default=32,
                        help="Batch size for encryption (global, affects CKKS context)")
    parser.add_argument("--results_folder", type=str, default="results",
                        help="Where to store result files")

    parser.add_argument("--algorithms", type=str, nargs="+",
                        choices=["Ray Casting", "Edge Orientation", "Winding Number"],
                        default=["Ray Casting", "Edge Orientation", "Winding Number"],
                        help="Algorithms to benchmark")

    parser.add_argument("--test_mode", action="store_true",
                        help="Use test mode (fast, insecure settings)")

    parser.add_argument("--scale", type=int, default=45,
                        help="CKKS scale modulus (first = scale + 3)")
    parser.add_argument("--level", type=int, default=48,
                        help="Multiplicative depth / level parameter")

    parser.add_argument("--num_polygons", type=int,
                        help="Limit number of polygons to test (default: all)")

    return parser.parse_args()

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    args = parse_args()

    scale = args.scale
    first = scale + 1 #min(scale + 1, 60)
    level = args.level
    batch_size = args.batch_size

    logging.info(f"Global context: scale={scale}, first={first}, level={level}, batch_size={batch_size}")

    # Load polygons and points
    logging.info("Loading polygons and points...")
    all_polygons = load_polygons("data/polygon_sanfrancisco.geojson")
    all_polygons_decomposed = load_polygons("data/polygon_sanfrancisco_decomposed.geojson")
    all_points = load_points("data/data_taxis_20000_trim.geojson")

    # Determine number of polygons used
    total_polys = len(all_polygons)
    num_polys = args.num_polygons if args.num_polygons else total_polys
    num_polys = min(num_polys, total_polys)
    logging.info(f"Testing {num_polys} polygons out of {total_polys}")

    # Resolve algorithms
    algorithm_map = {
        "Ray Casting": ray_casting,
        "Edge Orientation": edge_orientation,
        "Winding Number": winding_number
    }
    chosen_algorithms = {name: algorithm_map[name] for name in args.algorithms}

    # Create CKKS context once
    logging.info("Creating CKKS crypto context...")
    secKey = create_shared_context(
        -122.5192, 37.697, 0.2,
        scaleMod=scale,
        firstMod=first,
        batch_size=batch_size,
        levels=level,
        sec_level=SecurityLevel.HEStd_NotSet if args.test_mode else SecurityLevel.HEStd_128_classic
    )
    cc = get_shared_context().cc

    # Encrypt points once
    logging.info("Encrypting points once...")
    encrypted_points = fhepolygonqueries.MultiPoint(
        PlainMultiPoint(all_points[: batch_size])
    )

    # Prepare results file
    output_file = init_results_file(args.results_folder)
    logging.info(f"Writing results incrementally to {output_file}")

    # Benchmark loop
    logging.info(f"Running {len(chosen_algorithms)} algorithms on {num_polys} polygons")
    points = encrypted_points

    for poly_id in range(num_polys):
        for algo_name, algo_func in chosen_algorithms.items():
            try:
                poly = (
                    all_polygons_decomposed[poly_id]
                    if algo_func == edge_orientation
                    else all_polygons[poly_id]
                )

                logging.info(f"Running {algo_name} on polygon {poly_id} (batch={batch_size})")

                result = run_single_benchmark(
                    cc, secKey, points, poly,
                    algo_func, batch_size, scale, first, poly_id, args.test_mode
                )
                append_result(output_file, result)

            except Exception as e:
                logging.error(f"Error running {algo_name} on polygon {poly_id}: {e}")
                continue

    logging.info("All benchmarks completed.")
