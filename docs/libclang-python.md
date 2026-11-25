# Clang Python bindings with Podman

The repository's `Dockerfile` builds an Ubuntu 24.04 image with LLVM/Clang 22's Python bindings. The image includes both the `clang.cindex` Python module and its `libclang` shared library.

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

The default container command creates a Clang index and parses a small C++ translation unit. Success prints:

```text
clang.cindex and libclang are working
```

The `.podman/` directory is ignored by Git. The VFS storage driver keeps the setup independent of host overlay filesystem support.

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
