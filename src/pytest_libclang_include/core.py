"""Compilation-database parsing shared by the pytest plugin and CLI example."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from clang import cindex


OUTPUT_OPTIONS_WITH_VALUE = {"-o", "-MF", "-MT", "-MQ"}
OUTPUT_OPTIONS_WITHOUT_VALUE = {"-c", "-MD", "-MMD", "-MP"}


class IncludeCheckError(RuntimeError):
    """Raised when a translation unit cannot be parsed for include checks."""


class CompilationDatabaseError(IncludeCheckError):
    """Raised when the compilation database has no unique command for a source."""


class TranslationUnitParseError(IncludeCheckError):
    """Raised when libclang reports an error while parsing a source file."""


@dataclass(frozen=True)
class IncludeRecord:
    including_file: Path
    line: int
    included_file: Path


def _command_source(command: cindex.CompileCommand) -> Path:
    source = Path(command.filename)
    if not source.is_absolute():
        source = Path(command.directory) / source
    return source.resolve()


def _parse_arguments(command: cindex.CompileCommand, source: Path) -> list[str]:
    """Keep parse flags from a driver command, dropping compile outputs."""
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


def read_includes(build_directory: str | Path, source_file: str | Path) -> list[IncludeRecord]:
    """Parse a source with its compile command and return resolved include events."""
    build_directory = Path(build_directory).resolve()
    source_file = Path(source_file).resolve()
    if not source_file.is_file():
        raise IncludeCheckError(f"source file does not exist: {source_file}")

    try:
        database = cindex.CompilationDatabase.fromDirectory(str(build_directory))
        commands = [
            command
            for command in database.getAllCompileCommands()
            if _command_source(command) == source_file
        ]
    except cindex.CompilationDatabaseError as error:
        raise CompilationDatabaseError(
            f"could not read compilation database in {build_directory}: {error}"
        ) from error

    if not commands:
        raise CompilationDatabaseError(
            f"no compile command found for {source_file} in {build_directory}"
        )
    if len(commands) > 1:
        raise CompilationDatabaseError(
            f"multiple compile commands found for {source_file}; "
            "use a build directory with one configuration"
        )

    command = commands[0]
    try:
        compiler_arguments = _parse_arguments(command, source_file)
        index = cindex.Index.create()
        previous_directory = Path.cwd()
        os.chdir(command.directory)
        try:
            translation_unit = index.parse(str(source_file), args=compiler_arguments)
        finally:
            os.chdir(previous_directory)
    except (OSError, ValueError, cindex.LibclangError, cindex.TranslationUnitLoadError) as error:
        raise TranslationUnitParseError(f"could not parse {source_file}: {error}") from error

    errors = [
        diagnostic
        for diagnostic in translation_unit.diagnostics
        if diagnostic.severity >= cindex.Diagnostic.Error
    ]
    if errors:
        details = "\n".join(str(diagnostic) for diagnostic in errors)
        raise TranslationUnitParseError(
            f"Clang reported errors while parsing {source_file}:\n{details}"
        )

    includes: list[IncludeRecord] = []
    for inclusion in translation_unit.get_includes():
        including_file = inclusion.location.file
        if including_file is None:
            continue
        includes.append(
            IncludeRecord(
                including_file=Path(including_file.name).resolve(),
                line=inclusion.location.line,
                included_file=Path(inclusion.include.name).resolve(),
            )
        )
    return includes
