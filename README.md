# fhe-polygon-queries

Anonymous code submission for paper "Efficient Point-In-Polygon Queries using Fully Homomorphic Encryption"

## Prerequisites

For this project, we utilized the OpenFHE python wrapper. Source code and manual installation instructions can be found [here](https://github.com/openfheorg/openfhe-python).
The library is also available through pip.

Then, install the following Python packages:
- openfhe==1.4.2.0.22.4
- shapely

For plotting, optionally install:
- matplotlib
- pandas
- geopandas

## Usage

Run script `benchmark_all.py` to recreate the measurements for all algorithms on all polygons. 
Example: `python3 benchmark_all.py --batch_size 65536 --algorithms "Edge Orientation" --level 53 --scale 49`