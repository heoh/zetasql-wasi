def _binaryen_repo_impl(repository_ctx):
    os_name = repository_ctx.os.name.lower()
    arch = repository_ctx.os.arch.lower()
    
    version = "version_124"
    
    platform = ""
    if "linux" in os_name:
        platform = "linux"
    elif "mac" in os_name or "darwin" in os_name:
        platform = "macos"
    elif "windows" in os_name:
        platform = "windows"
    else:
        fail("Unsupported OS: " + os_name)
        
    cpu = ""
    if arch == "amd64" or arch == "x86_64":
        cpu = "x86_64"
    elif arch == "arm64" or arch == "aarch64":
        cpu = "arm64"
    else:
        fail("Unsupported Architecture: " + arch)

    # Handle specific naming conventions for binaryen releases
    # Linux aarch64 is usually named aarch64-linux
    if platform == "linux" and cpu == "arm64":
         cpu = "aarch64"

    filename = "binaryen-{version}-{cpu}-{platform}.tar.gz".format(
        version = version,
        cpu = cpu,
        platform = platform,
    )
    
    url = "https://github.com/WebAssembly/binaryen/releases/download/{version}/{filename}".format(
        version = version,
        filename = filename,
    )

    repository_ctx.report_progress("Downloading binaryen from " + url)
    repository_ctx.download_and_extract(
        url = url,
        stripPrefix = "binaryen-" + version,
    )

    executable_extension = ""
    if platform == "windows":
        executable_extension = ".exe"

    repository_ctx.file("BUILD.bazel", """
filegroup(
    name = "wasm_opt",
    srcs = ["bin/wasm-opt{extension}"],
    visibility = ["//visibility:public"],
)
""".format(extension = executable_extension))

binaryen_repo = repository_rule(
    implementation = _binaryen_repo_impl,
)

def _binaryen_extension_impl(module_ctx):
    binaryen_repo(name = "binaryen")

binaryen_extension = module_extension(
    implementation = _binaryen_extension_impl,
)
