#!/usr/bin/env python3
"""Print resolved direct and transitive includes for a CMake compile unit."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from clang import cindex


OUTPUT_OPTIONS_WITH_VALUE = {"-o", "-MF", "-MT", "-MQ"}
OUTPUT_OPTIONS_WITHOUT_VALUE = {"-c", "-MD", "-MMD", "-MP"}


def command_source(command: cindex.CompileCommand) -> Path:
    source = Path(command.filename)
    if not source.is_absolute():
        source = Path(command.directory) / source
    return source.resolve()


def parse_arguments(command: cindex.CompileCommand, source: Path) -> list[str]:
    """Keep parsing flags from the compile command, dropping driver outputs."""
    command_arguments = list(command.arguments)
    if not command_arguments:
        raise ValueError("compile command has no arguments")

    result: list[str] = []
    index = 1  # The first argument is the compiler executable.
    command_directory = Path(command.directory)

    while index < len(command_arguments):
        argument = command_arguments[index]
        if argument in OUTPUT_OPTIONS_WITH_VALUE:
            index += 2
            continue
        if argument in OUTPUT_OPTIONS_WITHOUT_VALUE:
            index += 1
            continue

        candidate = Path(argument)
        if not candidate.is_absolute():
            candidate = command_directory / candidate
        if candidate.resolve() == source:
            index += 1
            continue

        result.append(argument)
        index += 1

    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="List the resolved includes of one C++ compile command."
    )
    parser.add_argument("build_directory", type=Path, help="directory containing compile_commands.json")
    parser.add_argument("source", type=Path, help="source file selected from the compilation database")
    args = parser.parse_args()

    build_directory = args.build_directory.resolve()
    source = args.source.resolve()

    if not source.is_file():
        parser.error(f"source file does not exist: {source}")

    try:
        database = cindex.CompilationDatabase.fromDirectory(str(build_directory))
        commands = [
            command
            for command in database.getAllCompileCommands()
            if command_source(command) == source
        ]
    except cindex.CompilationDatabaseError as error:
        print(f"could not read compilation database in {build_directory}: {error}", file=sys.stderr)
        return 2

    if not commands:
        print(f"no compile command found for {source}", file=sys.stderr)
        return 2
    if len(commands) > 1:
        print(f"multiple compile commands found for {source}; use a build directory with one configuration", file=sys.stderr)
        return 2

    command = commands[0]
    try:
        compiler_arguments = parse_arguments(command, source)
        index = cindex.Index.create()
        previous_directory = Path.cwd()
        os.chdir(command.directory)
        try:
            translation_unit = index.parse(str(source), args=compiler_arguments)
        finally:
            os.chdir(previous_directory)
    except (OSError, ValueError, cindex.TranslationUnitLoadError) as error:
        print(f"could not parse {source}: {error}", file=sys.stderr)
        return 2

    errors = [
        diagnostic
        for diagnostic in translation_unit.diagnostics
        if diagnostic.severity >= cindex.Diagnostic.Error
    ]
    if errors:
        for diagnostic in errors:
            print(diagnostic, file=sys.stderr)
        return 1

    found_includes = False
    for inclusion in translation_unit.get_includes():
        source_file = inclusion.location.file
        if source_file is None:
            continue
        found_includes = True
        print(
            f"{source_file.name}:{inclusion.location.line} -> {inclusion.include.name}"
        )

    if not found_includes:
        print(f"no includes found in {source}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
