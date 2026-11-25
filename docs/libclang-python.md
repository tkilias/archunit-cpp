# Clang Python bindings with Podman

The repository's `Dockerfile` builds an Ubuntu 24.04 image with LLVM/Clang 22's Python bindings, CMake, Ninja, the Clang compiler, and Poetry. The image includes both the `clang.cindex` Python module and its `libclang` shared library. The test runner uses Poetry to install the project and its `pytest-plugin` extra from the mounted checkout.

## Prepare the project-local Podman command

From the project root in Bash, source the helper to create the project-local storage directories and define the `podman_arch_unit` alias:

```sh
source scripts/podman-local.sh
```

The alias works from any current directory after it is loaded. Source the script again in a new shell.

## Build and run

Run these commands from the project root. The alias keeps Podman's image storage, runtime state, and temporary files under `.podman/` in the project directory:

```sh
podman_arch_unit build -t archunit-cpp-libclang .
podman_arch_unit run --rm \
  --userns=keep-id:uid=0,gid=0 \
  --security-opt label=disable \
  -v "$PWD:/workspace:ro" \
  -w /workspace \
  archunit-cpp-libclang
```

The repository is bind-mounted read-only at `/workspace`. These user namespace and label options let the rootless container read a checkout under this host's private home directory. The default container command runs `poetry install --extras pytest-plugin` and then the pytest plugin tests. Poetry installs pytest and registers the plugin from the checkout; its virtual environment can access the image's system-installed Clang bindings. The tests' shared fixture configures and compiles the CMake sample project under `tests/include-check` in pytest's temporary directory, then uses its `compile_commands.json` to check direct includes.

## Use the pytest assertion

The installable plugin provides an `assert_include` fixture. It asserts that the C++ source directly includes a header whose resolved path ends in the supplied suffix:

```python
def test_main_includes_api(assert_include, build_directory, source_file):
    assert_include(build_directory, source_file, "demo/api.hpp")
```

The fixture uses the matching command from `compile_commands.json`. A transitive include does not satisfy the assertion. Install the project with the `pytest-plugin` extra to use the entry point in another pytest project.

The `.podman/` directory is ignored by Git. The VFS storage driver keeps the setup independent of host overlay filesystem support.

## Use the bindings interactively

Start a shell in the image with the same project-local Podman directories:

```sh
podman_arch_unit run --rm -it --entrypoint /bin/bash archunit-cpp-libclang
```

Inside the container, use Python 3.12:

```sh
python3.12 -c 'from clang import cindex; print(cindex.Index.create())'
```

The bindings call `libclang` at runtime. The image installs `python3-clang-22`, which pulls in the matching LLVM 22 runtime libraries.
