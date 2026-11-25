"""Pytest fixture for asserting direct C++ include dependencies."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Callable

import pytest
from clang import cindex

from .core import IncludeCheckError, parse_translation_unit, read_includes


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


@pytest.fixture
def assert_interfaces() -> Callable[[str | Path, str | Path, str | Path], None]:
    """Return an assertion that classes in a directory are interfaces only.

    Call as ``assert_interfaces(build_dir, source_file, header_directory)``.
    The source file must include the headers to inspect and have a compile
    command in the build directory. Each class must declare a pure virtual
    method; a bodyless virtual destructor declaration is also allowed. Other
    methods, method definitions, and data members are rejected.
    """
    class_kinds = {
        cindex.CursorKind.CLASS_DECL,
        cindex.CursorKind.STRUCT_DECL,
        cindex.CursorKind.CLASS_TEMPLATE,
        cindex.CursorKind.CLASS_TEMPLATE_PARTIAL_SPECIALIZATION,
    }
    method_kinds = {
        cindex.CursorKind.CXX_METHOD,
        cindex.CursorKind.CONSTRUCTOR,
        cindex.CursorKind.DESTRUCTOR,
        cindex.CursorKind.CONVERSION_FUNCTION,
        cindex.CursorKind.FUNCTION_TEMPLATE,
    }

    def check(
        build_directory: str | Path,
        source_file: str | Path,
        header_directory: str | Path,
    ) -> None:
        directory = Path(header_directory).resolve()
        if not directory.is_dir():
            raise AssertionError(f"header directory does not exist: {directory}")
        try:
            translation_unit = parse_translation_unit(build_directory, source_file)
        except IncludeCheckError as error:
            pytest.fail(str(error), pytrace=False)

        classes: dict[str, cindex.Cursor] = {}
        all_methods: list[cindex.Cursor] = []

        def visit(cursor: cindex.Cursor) -> None:
            if cursor.kind in class_kinds and cursor.is_definition() and cursor.location.file:
                class_file = Path(cursor.location.file.name).resolve()
                try:
                    class_file.relative_to(directory)
                except ValueError:
                    pass
                else:
                    classes[cursor.get_usr()] = cursor
            if cursor.kind in method_kinds:
                all_methods.append(cursor)
            for child in cursor.get_children():
                visit(child)

        visit(translation_unit.cursor)

        failures: list[str] = []
        for usr, class_cursor in sorted(classes.items()):
            class_name = class_cursor.displayname or class_cursor.spelling or "<anonymous>"
            member_methods = [
                child
                for child in class_cursor.get_children()
                if child.kind in method_kinds
            ]
            pure_methods = [
                method
                for method in member_methods
                if method.kind != cindex.CursorKind.DESTRUCTOR
                and method.is_pure_virtual_method()
            ]
            if not pure_methods:
                failures.append(
                    f"{class_cursor.location.file}:{class_cursor.location.line}: "
                    f"{class_name} must declare at least one pure virtual method"
                )

            for member in class_cursor.get_children():
                if member.kind in {cindex.CursorKind.FIELD_DECL, cindex.CursorKind.VAR_DECL}:
                    failures.append(
                        f"{member.location.file}:{member.location.line}: "
                        f"{class_name} has data member {member.spelling}"
                    )

            related_methods = [
                method
                for method in all_methods
                if method.semantic_parent is not None
                and method.semantic_parent.get_usr() == usr
            ]
            seen_method_locations: set[tuple[str, int, str]] = set()
            for method in related_methods:
                location_file = (
                    method.location.file.name if method.location.file is not None else "<unknown>"
                )
                location = (location_file, method.location.line, method.spelling)
                if location in seen_method_locations:
                    continue
                seen_method_locations.add(location)

                allowed_destructor = (
                    method.kind == cindex.CursorKind.DESTRUCTOR
                    and method.is_virtual_method()
                    and not method.is_definition()
                )
                pure_virtual = (
                    method.kind != cindex.CursorKind.DESTRUCTOR
                    and method.is_pure_virtual_method()
                )
                if method.is_definition():
                    failures.append(
                        f"{location_file}:{method.location.line}: "
                        f"{class_name}::{method.spelling} has an implementation"
                    )
                elif not (allowed_destructor or pure_virtual):
                    failures.append(
                        f"{location_file}:{method.location.line}: "
                        f"{class_name}::{method.spelling} must be pure virtual"
                    )

        if failures:
            raise AssertionError(
                "classes must be interface-only declarations:\n" + "\n".join(failures)
            )

    return check
