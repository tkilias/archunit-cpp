from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def compiled_demo(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    project_directory = Path(__file__).resolve().parent / "include-check"
    build_directory = tmp_path_factory.mktemp("include-check-build")

    subprocess.run(
        [
            "cmake",
            "-S",
            str(project_directory),
            "-B",
            str(build_directory),
            "-G",
            "Ninja",
            "-DCMAKE_CXX_COMPILER=clang++-22",
            "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["cmake", "--build", str(build_directory)],
        check=True,
        capture_output=True,
        text=True,
    )

    return build_directory, project_directory / "src" / "main.cpp"
