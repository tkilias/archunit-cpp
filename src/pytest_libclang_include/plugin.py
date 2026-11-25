"""Pytest fixture for asserting direct C++ include dependencies."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Callable

import pytest

from .core import IncludeCheckError, read_includes


def _path_parts(path: str | Path) -> tuple[str, ...]:
    normalized = str(path).replace("\\", "/").strip("/")
    return tuple(part for part in PurePosixPath(normalized).parts if part not in ("", "."))


def _matches_suffix(path: Path, expected_suffix: str | Path) -> bool:
    expected_parts = _path_parts(expected_suffix)
    actual_parts = path.parts
    return bool(expected_parts) and len(actual_parts) >= len(expected_parts) and (
        actual_parts[-len(expected_parts) :] == expected_parts
    )


@pytest.fixture
def assert_include() -> Callable[[str | Path, str | Path, str | Path], None]:
    """Return an assertion for a directly included header.

    Call the fixture as ``assert_include(build_dir, source_file, "demo/api.hpp")``.
    The expected header is matched as a normalized suffix of its resolved path.
    """

    def check(
        build_directory: str | Path,
        source_file: str | Path,
        expected_header_suffix: str | Path,
    ) -> None:
        source = Path(source_file).resolve()
        try:
            includes = read_includes(build_directory, source)
        except IncludeCheckError as error:
            pytest.fail(str(error), pytrace=False)

        direct_includes = sorted(
            {record.included_file for record in includes if record.including_file == source},
            key=lambda path: path.as_posix(),
        )
        if not any(_matches_suffix(path, expected_header_suffix) for path in direct_includes):
            rendered_includes = ", ".join(path.as_posix() for path in direct_includes) or "<none>"
            raise AssertionError(
                f"{source} does not directly include {str(expected_header_suffix)!r}; "
                f"resolved direct includes: {rendered_includes}"
            )

    return check
