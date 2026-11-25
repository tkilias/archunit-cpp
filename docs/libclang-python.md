# Clang Python bindings with Podman

The repository's `Dockerfile` builds an Ubuntu 24.04 image with LLVM/Clang 22's Python bindings, CMake, Ninja, the Clang compiler, and pytest. The image includes both the `clang.cindex` Python module and its `libclang` shared library.

## Build and run

Run these commands from the project root. Podman's image storage, runtime state, and temporary files are kept under `.podman/` in the project directory:

```sh
mkdir -p .podman/storage .podman/run .podman/tmp
TMPDIR="$PWD/.podman/tmp" podman \
  --root "$PWD/.podman/storage" \
  --runroot "$PWD/.podman/run" \
  --tmpdir "$PWD/.podman/tmp" \
  --storage-driver=vfs \
  build -t archunit-cpp-libclang .
TMPDIR="$PWD/.podman/tmp" podman \
  --root "$PWD/.podman/storage" \
  --runroot "$PWD/.podman/run" \
  --tmpdir "$PWD/.podman/tmp" \
  --storage-driver=vfs \
  run --rm archunit-cpp-libclang
```

The default container command configures and compiles a small CMake C++ project, runs the pytest plugin tests, then uses `clang.cindex` and its generated `compile_commands.json` to print the resolved direct and transitive includes. The sample source includes `demo/api.hpp`, which itself includes `demo/detail/value.hpp`. Output resembles:

```text
/opt/examples/include-check/src/main.cpp:1 -> /opt/examples/include-check/include/demo/api.hpp
/opt/examples/include-check/include/demo/api.hpp:3 -> /opt/examples/include-check/include/demo/detail/value.hpp
```

To run the example manually rather than through the image's default command:

```sh
TMPDIR="$PWD/.podman/tmp" podman \
  --root "$PWD/.podman/storage" \
  --runroot "$PWD/.podman/run" \
  --tmpdir "$PWD/.podman/tmp" \
  --storage-driver=vfs \
  run --rm --entrypoint /bin/sh archunit-cpp-libclang -c 'set -eu
build_dir=$(mktemp -d)
cmake -S /opt/examples/include-check -B "$build_dir" -G Ninja \
  -DCMAKE_CXX_COMPILER=clang++-22 -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
cmake --build "$build_dir"
python3.12 /opt/examples/list_includes.py \
  "$build_dir" /opt/examples/include-check/src/main.cpp
'
```

From an interactive container shell, the script can inspect another CMake build directory and source file. Use paths as they appear inside the container:

```sh
python3.12 /opt/examples/list_includes.py <build-directory> <source-file>
```

It reports resolved include paths recursively. It requires exactly one matching compile command so that the compile flags are unambiguous.

## Use the pytest assertion

The installable plugin provides an `assert_include` fixture. It asserts that the C++ source directly includes a header whose resolved path ends in the supplied suffix:

```python
def test_main_includes_api(assert_include, build_directory, source_file):
    assert_include(build_directory, source_file, "demo/api.hpp")
```

The fixture uses the matching command from `compile_commands.json`. A transitive include does not satisfy the assertion. Install the project with the `pytest-plugin` extra to use the entry point in another pytest project.

The `.podman/` directory is ignored by Git. The VFS storage driver keeps the setup independent of host overlay filesystem support.

## Use the local Podman store from Bash

Source the helper script from the project root (or by giving its path) to define a `podman_arch_unit` alias that uses this project's `.podman/` storage, runtime, and temporary directories:

```sh
source scripts/podman-local.sh
podman_arch_unit ps
```

The alias works from any current directory after it is loaded. Source the script again in a new shell.

## Use the bindings interactively

Start a shell in the image with the same project-local Podman directories:

```sh
TMPDIR="$PWD/.podman/tmp" podman \
  --root "$PWD/.podman/storage" \
  --runroot "$PWD/.podman/run" \
  --tmpdir "$PWD/.podman/tmp" \
  --storage-driver=vfs \
  run --rm -it --entrypoint /bin/bash archunit-cpp-libclang
```

Inside the container, use Python 3.12:

```sh
python3.12 -c 'from clang import cindex; print(cindex.Index.create())'
```

The bindings call `libclang` at runtime. The image installs `python3-clang-22`, which pulls in the matching LLVM 22 runtime libraries.
