#!/usr/bin/env python3
"""Print resolved direct and transitive includes for a CMake compile unit."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pytest_libclang_include.core import (
    CompilationDatabaseError,
    TranslationUnitParseError,
    read_includes,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="List the resolved includes of one C++ compile command."
    )
    parser.add_argument(
        "build_directory", type=Path, help="directory containing compile_commands.json"
    )
    parser.add_argument(
        "source", type=Path, help="source file selected from the compilation database"
    )
    args = parser.parse_args()

    source = args.source.resolve()
    try:
        includes = read_includes(args.build_directory, source)
    except CompilationDatabaseError as error:
        print(error, file=sys.stderr)
        return 2
    except TranslationUnitParseError as error:
        print(error, file=sys.stderr)
        return 1

    for inclusion in includes:
        print(
            f"{inclusion.including_file}:{inclusion.line} -> "
            f"{inclusion.included_file}"
        )

    if not includes:
        print(f"no includes found in {source}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
