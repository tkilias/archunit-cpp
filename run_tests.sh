#!/bin/sh
set -eu

cd /workspace
poetry install --extras pytest-plugin --no-interaction
poetry run pytest -p no:cacheprovider
