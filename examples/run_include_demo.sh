#!/bin/sh
set -eu

build_directory="$(mktemp -d)"
trap 'rm -rf "$build_directory"' EXIT

cmake \
    -S /opt/examples/include-check \
    -B "$build_directory" \
    -G Ninja \
    -DCMAKE_CXX_COMPILER=clang++-22 \
    -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
cmake --build "$build_directory"
python3.12 /opt/examples/list_includes.py \
    "$build_directory" \
    /opt/examples/include-check/src/main.cpp
