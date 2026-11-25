from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest


IncludeAssertion = Callable[[str | Path, str | Path, str | Path], None]


def test_asserts_direct_include(
    assert_include: IncludeAssertion, compiled_demo: tuple[Path, Path]
) -> None:
    build_directory, source_file = compiled_demo

    assert_include(build_directory, source_file, "demo/api.hpp")


def test_transitive_include_does_not_satisfy_direct_assertion(
    assert_include: IncludeAssertion, compiled_demo: tuple[Path, Path]
) -> None:
    build_directory, source_file = compiled_demo

    with pytest.raises(AssertionError, match="does not directly include"):
        assert_include(build_directory, source_file, "demo/detail/value.hpp")


def test_failure_shows_resolved_direct_includes(
    assert_include: IncludeAssertion, compiled_demo: tuple[Path, Path]
) -> None:
    build_directory, source_file = compiled_demo

    with pytest.raises(AssertionError, match="demo/api.hpp"):
        assert_include(build_directory, source_file, "demo/missing.hpp")
