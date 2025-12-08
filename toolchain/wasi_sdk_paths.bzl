"""Repository rule to configure WASI SDK paths."""

def _wasi_sdk_toolchain_impl(repository_ctx):
    # Get the path to the WASI SDK from the workspace
    wasi_sdk = repository_ctx.path(Label("@wasi_sdk//:BUILD")).dirname

    wasi_sdk_path = str(wasi_sdk)
    sysroot_include = wasi_sdk_path + "/share/wasi-sysroot/include"
    clang_include = wasi_sdk_path + "/lib/clang/18/include"

    # Create paths.bzl with absolute paths
    repository_ctx.file("paths.bzl", """# Auto-generated paths for WASI SDK
WASI_SDK_PATH = "{wasi_sdk_path}"
WASI_SYSROOT = "{wasi_sdk_path}/share/wasi-sysroot"
WASI_SYSROOT_INCLUDE = "{sysroot_include}"
WASI_CLANG_INCLUDE = "{clang_include}"
""".format(
        wasi_sdk_path = wasi_sdk_path,
        sysroot_include = sysroot_include,
        clang_include = clang_include,
    ))

    # Create BUILD file
    repository_ctx.file("BUILD", """
package(default_visibility = ["//visibility:public"])
""")

wasi_sdk_toolchain = repository_rule(
    implementation = _wasi_sdk_toolchain_impl,
    attrs = {},
)
