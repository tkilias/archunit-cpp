from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest


InterfaceAssertion = Callable[[str | Path, str | Path, str | Path], None]


def test_directory_contains_only_interface_classes(
    assert_interfaces: InterfaceAssertion, compiled_demo: tuple[Path, Path]
) -> None:
    build_directory, source_file = compiled_demo

    assert_interfaces(
        build_directory,
        source_file,
        source_file.parent.parent / "include" / "demo" / "contracts",
    )


def test_directory_rejects_method_implementations(
    assert_interfaces: InterfaceAssertion, compiled_demo: tuple[Path, Path]
) -> None:
    build_directory, source_file = compiled_demo

    with pytest.raises(AssertionError, match="has an implementation"):
        assert_interfaces(
            build_directory,
            source_file,
            source_file.parent.parent / "include" / "demo" / "implementations",
        )


def test_directory_rejects_data_members(
    assert_interfaces: InterfaceAssertion, compiled_demo: tuple[Path, Path]
) -> None:
    build_directory, source_file = compiled_demo

    with pytest.raises(AssertionError, match="has data member state"):
        assert_interfaces(
            build_directory,
            source_file,
            source_file.parent.parent / "include" / "demo" / "implementations",
        )


def test_directory_rejects_classes_without_pure_virtual_methods(
    assert_interfaces: InterfaceAssertion, compiled_demo: tuple[Path, Path]
) -> None:
    build_directory, source_file = compiled_demo

    with pytest.raises(AssertionError, match="must declare at least one pure virtual method"):
        assert_interfaces(
            build_directory,
            source_file,
            source_file.parent.parent / "include" / "demo" / "implementations",
        )
