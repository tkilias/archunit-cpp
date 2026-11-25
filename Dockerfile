FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl gnupg \
    && curl -fsSL https://apt.llvm.org/llvm-snapshot.gpg.key \
        | gpg --dearmor -o /usr/share/keyrings/apt.llvm.org.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/apt.llvm.org.gpg] https://apt.llvm.org/noble/ llvm-toolchain-noble-22 main" \
        > /etc/apt/sources.list.d/llvm.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends python3-clang-22 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

CMD ["python3.12", "-c", "from clang import cindex; index = cindex.Index.create(); unit = index.parse('smoke.cpp', unsaved_files=[('smoke.cpp', 'int answer() { return 42; }')]); errors = [d for d in unit.diagnostics if d.severity >= cindex.Diagnostic.Error]; assert not errors, errors; print('clang.cindex and libclang are working')"]
