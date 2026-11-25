#!/usr/bin/env bash

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    printf 'Source this script in Bash: source %s\n' "$0" >&2
    exit 1
fi

_podman_local_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
mkdir -p "$_podman_local_root/.podman/storage" \
    "$_podman_local_root/.podman/run" \
    "$_podman_local_root/.podman/tmp"

printf -v _podman_local_root_escaped '%q' "$_podman_local_root"
alias podman_arch_unit="TMPDIR=$_podman_local_root_escaped/.podman/tmp command podman --root $_podman_local_root_escaped/.podman/storage --runroot $_podman_local_root_escaped/.podman/run --tmpdir $_podman_local_root_escaped/.podman/tmp --storage-driver=vfs"

unset _podman_local_root _podman_local_root_escaped
