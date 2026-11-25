#!/bin/sh
set -eu

PYTHONPATH=/opt/src python3.12 -m pytest \
    -p pytest_libclang_include.plugin \
    /opt/tests
