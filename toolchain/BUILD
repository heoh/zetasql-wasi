load("@rules_cc//cc:defs.bzl", "cc_toolchain")
load(":wasi_cc_toolchain_config.bzl", "wasi_cc_toolchain_config")

package(default_visibility = ["//visibility:public"])

# Target platform for wasm32-wasi builds.
platform(
    name = "wasm32-wasi",
    constraint_values = [
        "@platforms//cpu:wasm32",
        "@platforms//os:wasi",
    ],
)

# WASI toolchain registration
toolchain(
    name = "wasi_cc_toolchain",
    exec_compatible_with = [
        "@platforms//os:linux",
        "@platforms//cpu:x86_64",
    ],
    target_compatible_with = [
        "@platforms//os:wasi",
        "@platforms//cpu:wasm32",
    ],
    toolchain = ":wasi_cc",
    toolchain_type = "@bazel_tools//tools/cpp:toolchain_type",
)

wasi_cc_toolchain_config(
    name = "wasi_cc_config",
    clang_path = "wrappers/clang",
    wasm_ld_path = "wrappers/wasm-ld",
    ar_path = "wrappers/llvm-ar",
    nm_path = "wrappers/llvm-nm",
    objdump_path = "wrappers/llvm-objdump",
    strip_path = "wrappers/llvm-strip",
    sysroot_path = "external/+_repo_rules+wasi_sdk/share/wasi-sysroot",
)

cc_toolchain(
    name = "wasi_cc",
    all_files = ":wasi_all_files",
    ar_files = ":wasi_ar_files",
    compiler_files = ":wasi_compiler_files",
    dwp_files = ":empty",
    linker_files = ":wasi_linker_files",
    objcopy_files = ":empty",
    strip_files = ":empty",
    supports_param_files = True,
    toolchain_config = ":wasi_cc_config",
    toolchain_identifier = "wasi-toolchain",
)

filegroup(
    name = "wasi_all_files",
    srcs = [
        ":wasi_ar_files",
        ":wasi_compiler_files",
        ":wasi_linker_files",
        "@wasi_sdk//:all_files",
    ],
)

filegroup(
    name = "wasi_compiler_files",
    srcs = [
        "wrappers/clang",
        "@wasi_sdk//:compiler_files",
    ],
)

filegroup(
    name = "wasi_linker_files",
    srcs = [
        "wrappers/clang",
        "wrappers/wasm-ld",
        "@wasi_sdk//:linker_files",
    ],
)

filegroup(
    name = "wasi_ar_files",
    srcs = [
        "wrappers/llvm-ar",
        "@wasi_sdk//:ar_files",
    ],
)

filegroup(name = "empty")
