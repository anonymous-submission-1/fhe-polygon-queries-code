cmake_minimum_required(VERSION 3.12...3.29)
project(poly_decompose)

find_package(CGAL REQUIRED)
find_package(GDAL REQUIRED)
add_executable(poly_decompose poly_decompose.cpp)
target_link_libraries(poly_decompose CGAL::CGAL GDAL::GDAL)
