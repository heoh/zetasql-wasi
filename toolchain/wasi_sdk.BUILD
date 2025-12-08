# BUILD file for WASI SDK external repository

package(default_visibility = ["//visibility:public"])

filegroup(
    name = "all_files",
    srcs = glob(["**/*"]),
)

filegroup(
    name = "compiler_files",
    srcs = glob([
        "bin/clang*",
        "bin/llvm-*",
        "lib/clang/**/*",
        "share/wasi-sysroot/**/*",
    ]),
)

filegroup(
    name = "linker_files",
    srcs = glob([
        "bin/clang*",
        "bin/wasm-ld",
        "bin/lld",
        "bin/llvm-*",
        "lib/clang/**/*",
        "lib/wasi-sysroot/**/*",
        "share/wasi-sysroot/**/*",
    ]),
)

filegroup(
    name = "ar_files",
    srcs = glob([
        "bin/llvm-ar",
    ]),
)
