#include <iostream>
#include <vector>
#include <list>
#include <string>
#include <cassert>

#include <CGAL/Exact_predicates_inexact_constructions_kernel.h>
#include <CGAL/Partition_traits_2.h>
#include <CGAL/partition_2.h>

#include <ogrsf_frmts.h>

// ---- CGAL typedefs ----
typedef CGAL::Exact_predicates_inexact_constructions_kernel          K;
typedef CGAL::Partition_traits_2<K>                                  Traits;
typedef Traits::Polygon_2                                            Polygon_2;
typedef Traits::Point_2                                              Point_2;
typedef std::list<Polygon_2>                                         Polygon_list;

// ---- Helpers: OGR <-> CGAL ----

// Convert an OGRLinearRing (exterior ring) to a CGAL simple Polygon_2.
// Assumes the ring is closed; ignores the final duplicate closing point if present.
static bool OGRRingToCGALPolygon(const OGRLinearRing* ring, Polygon_2& out_poly) {
    if (!ring) return false;
    int n = ring->getNumPoints();
    if (n < 4) return false; // need at least 3 unique points + closing point

    out_poly.clear();
    // Add all but the last point if it's the same as the first (OGR rings are usually closed)
    int end = n;
    if (ring->getX(0) == ring->getX(n-1) &&
        ring->getY(0) == ring->getY(n-1)) {
        end = n - 1;
    }

    for (int i = 0; i < end; ++i) {
        out_poly.push_back(Point_2(ring->getX(i), ring->getY(i)));
    }

    // Ensure CCW orientation for CGAL partitioning routines
    if (out_poly.is_clockwise_oriented()) {
        out_poly.reverse_orientation();
    }
    return out_poly.is_simple();
}

// Convert a CGAL Polygon_2 to an OGRPolygon with a single exterior ring (no holes).
static OGRPolygon* CGALPolygonToOGRPolygon(const Polygon_2& poly) {
    if (poly.size() < 3) return nullptr;
    auto* ogrPoly = new OGRPolygon();
    auto* extRing = new OGRLinearRing();

    for (auto it = poly.vertices_begin(); it != poly.vertices_end(); ++it) {
        extRing->addPoint(CGAL::to_double(it->x()), CGAL::to_double(it->y()));
    }
    // close ring
    const auto first = *poly.vertices_begin();
    extRing->addPoint(CGAL::to_double(first.x()), CGAL::to_double(first.y()));

    ogrPoly->addRingDirectly(extRing);
    return ogrPoly;
}

// Partition a simple polygon into convex parts using CGAL’s optimal_convex_partition_2.
static void convexPartition(const Polygon_2& poly, Polygon_list& out_parts) {
    out_parts.clear();
    // Precondition: simple polygon, CCW orientation
    Polygon_2 p = poly;
    if (p.is_clockwise_oriented()) p.reverse_orientation();

    CGAL::optimal_convex_partition_2(p.vertices_begin(),
                                     p.vertices_end(),
                                     std::back_inserter(out_parts));

    // Sanity check (best effort; returns false if invalid)
    bool ok = CGAL::partition_is_valid_2(p.vertices_begin(), p.vertices_end(),
                                         out_parts.begin(), out_parts.end());
    if (!ok) {
        std::cerr << "Warning: partition validity check failed for a polygon.\n";
    }
}

static void copyFields(OGRFeature* src, OGRFeature* dst) {
    if (!src || !dst) return;
    int fieldCount = src->GetFieldCount();
    for (int i = 0; i < fieldCount; ++i) {
        dst->SetField(i, src->GetRawFieldRef(i));
    }
}

int main(int argc, char** argv) {
    if (argc < 3) {
        std::cerr << "Usage: " << argv[0] << " <input.geojson> <output.geojson>\n";
        return 1;
    }
    const std::string inPath  = argv[1];
    const std::string outPath = argv[2];

    GDALAllRegister();

    // ---- Open input ----
    GDALDatasetUniquePtr poDS(static_cast<GDALDataset*>(
        GDALOpenEx(inPath.c_str(), GDAL_OF_READONLY | GDAL_OF_VECTOR, nullptr, nullptr, nullptr)
    ));
    if (!poDS) {
        std::cerr << "Failed to open input: " << inPath << "\n";
        return 1;
    }

    if (poDS->GetLayerCount() < 1) {
        std::cerr << "No layers found in input.\n";
        return 1;
    }

    OGRLayer* inLayer = poDS->GetLayer(0);
    if (!inLayer) {
        std::cerr << "Failed to get input layer.\n";
        return 1;
    }

    // ---- Create output dataset & layer (GeoJSON) ----
    GDALDriver* driver = GetGDALDriverManager()->GetDriverByName("GeoJSON");
    if (!driver) {
        std::cerr << "GeoJSON driver not available in GDAL.\n";
        return 1;
    }

    // Remove existing output if present
    driver->Delete(outPath.c_str());

    GDALDataset* outDS = driver->Create(outPath.c_str(), 0, 0, 0, GDT_Unknown, nullptr);
    if (!outDS) {
        std::cerr << "Failed to create output: " << outPath << "\n";
        return 1;
    }

    // Copy spatial reference if available
    OGRSpatialReference* srs = inLayer->GetSpatialRef();
    OGRLayer* outLayer = outDS->CreateLayer(inLayer->GetName(), srs, wkbMultiPolygon, nullptr);
    if (!outLayer) {
        std::cerr << "Failed to create output layer.\n";
        GDALClose(outDS);
        return 1;
    }

    // Copy fields (schema)
    OGRFeatureDefn* inDefn = inLayer->GetLayerDefn();
    for (int i = 0; i < inDefn->GetFieldCount(); ++i) {
        OGRFieldDefn fld(inDefn->GetFieldDefn(i));
        if (outLayer->CreateField(&fld) != OGRERR_NONE) {
            std::cerr << "Warning: failed to copy field '" << fld.GetNameRef() << "'.\n";
        }
    }

    // ---- Iterate features ----
    inLayer->ResetReading();
    OGRFeatureUniquePtr feat;
    long processed = 0;

    while ((feat.reset(inLayer->GetNextFeature()), feat.get() != nullptr)) {
        OGRGeometry* geom = feat->GetGeometryRef();
        if (!geom) {
            std::cerr << "Skipping feature without geometry.\n";
            continue;
        }

        OGRwkbGeometryType gType = wkbFlatten(geom->getGeometryType());
        if (gType != wkbPolygon && gType != wkbMultiPolygon) {
            std::cerr << "Skipping non-polygonal geometry type.\n";
            continue;
        }

        // Collect all convex parts across all polygonal components into one MultiPolygon
        auto* multiOut = new OGRMultiPolygon();

        auto processSinglePolygon = [&](OGRPolygon* ogrPoly) {
            // Use only the exterior ring (holes ignored; see note above)
            const OGRLinearRing* ext = ogrPoly->getExteriorRing();
            if (!ext) return;

            Polygon_2 cgalPoly;
            if (!OGRRingToCGALPolygon(ext, cgalPoly)) {
                std::cerr << "Skipping non-simple or invalid exterior ring.\n";
                return;
            }

            Polygon_list parts;
            convexPartition(cgalPoly, parts);

            for (const auto& part : parts) {
                OGRPolygon* partOgr = CGALPolygonToOGRPolygon(part);
                if (partOgr) {
                    multiOut->addGeometryDirectly(partOgr);
                }
            }
        };

        if (gType == wkbPolygon) {
            processSinglePolygon(geom->toPolygon());
        } else if (gType == wkbMultiPolygon) {
            auto* mp = geom->toMultiPolygon();
            for (int i = 0; i < mp->getNumGeometries(); ++i) {
                OGRGeometry* subg = mp->getGeometryRef(i);
                if (subg && wkbFlatten(subg->getGeometryType()) == wkbPolygon) {
                    processSinglePolygon(subg->toPolygon());
                }
            }
        }

        // Create output feature with same attributes
        OGRFeature* outFeat = OGRFeature::CreateFeature(outLayer->GetLayerDefn());
        copyFields(feat.get(), outFeat);
        outFeat->SetGeometryDirectly(multiOut); // takes ownership

        if (outLayer->CreateFeature(outFeat) != OGRERR_NONE) {
            std::cerr << "Failed to create output feature.\n";
        }
        OGRFeature::DestroyFeature(outFeat);
        ++processed;
    }

    GDALClose(outDS);
    std::cout << "Processed " << processed << " feature(s) into " << outPath << "\n";
    return 0;
}
