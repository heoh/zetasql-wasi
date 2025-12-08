# ZetaSQL on WASI

This repository contains the build configuration and patches required to port [ZetaSQL](https://github.com/google/zetasql) to WebAssembly (WASI).

## Architecture

This project does not contain the ZetaSQL source code directly. Instead, it acts as a "build recipe" that:
1. Downloads a specific version of ZetaSQL (defined in `ZETASQL_VERSION`).
2. Applies a series of patches (in `patches/`) to make it compatible with WASI.
3. Builds the project using Bazel.

## Development Workflow

We use a Git-based workflow for managing patches. You can treat the `_work/zetasql` directory as a normal Git repository, and use scripts to sync your changes with the `patches/` directory.

### 1. Setup Development Environment

Run the setup script to clone ZetaSQL and apply existing patches:

```bash
./scripts/setup_dev.sh
```

This will create a `_work/zetasql` directory.

### 2. Make Changes

Go to the working directory and make your changes. **Commit your changes** as you would in any Git project.

```bash
cd _work/zetasql
# Edit files...
git add .
git commit -m "Fix: Disable unsupported syscalls for WASI"
```

### 3. Export Patches

When you are done, run the export script to generate patch files from your commits:

```bash
./scripts/export_patches.sh
```

This will:
- Generate `.patch` files in `patches/` corresponding to your new commits.

### 4. Build

Now you can build the project with your changes applied. From the `_work/zetasql` directory:

```bash
bazel build --config=wasi //zetasql/tools/execute_query:execute_query_wasi
```

## Updating ZetaSQL Version

1. Update the commit hash in `ZETASQL_VERSION`.
2. Run `./scripts/setup_dev.sh` to reset the workspace and attempt to re-apply patches.
3. Resolve any merge conflicts in `_work/zetasql`, commit the fixes, and run `./scripts/export_patches.sh`.
