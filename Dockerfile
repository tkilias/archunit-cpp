FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    POETRY_HOME=/opt/poetry \
    POETRY_VIRTUALENVS_OPTIONS_SYSTEM_SITE_PACKAGES=true \
    PATH="/opt/poetry/bin:${PATH}"

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl gnupg \
    && curl -fsSL https://apt.llvm.org/llvm-snapshot.gpg.key \
        | gpg --dearmor -o /usr/share/keyrings/apt.llvm.org.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/apt.llvm.org.gpg] https://apt.llvm.org/noble/ llvm-toolchain-noble-22 main" \
        > /etc/apt/sources.list.d/llvm.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        clang-22 cmake ninja-build python3-clang-22 python3.12-venv \
    && curl -fsSL https://install.python-poetry.org \
        | python3 - --version 2.5.1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

CMD ["/bin/sh", "/workspace/run_tests.sh"]
