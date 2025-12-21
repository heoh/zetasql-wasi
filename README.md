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

Build the WASM binary and proto files:

```bash
./scripts/build.sh
```

This will create the `build/` directory with:
- `zetasql.wasm` - WASM binary
- `zetasql.opt.wasm` - Optimized WASM binary
- `zetasql-proto/` - Proto file collection

### 5. Test

Run tests to verify the WASM binary works correctly:

```bash
./scripts/test.sh
```

This will:
- Create a Python virtual environment (`.venv/`) if it doesn't exist
- Install test dependencies
- Generate Python protobuf code
- Run all tests using pytest

The test suite validates:
- Expression evaluation (literals, functions, parameters)
- Query execution (SELECT, WHERE, JOIN, aggregations)
- DML operations (INSERT, UPDATE, DELETE)
- SQL analysis and parsing
- SQL formatting and table extraction

### 6. Prepare Release

Create distribution-ready release artifacts:

```bash
./scripts/prepare_release.sh
```

This will create the `release/` directory with:
- `zetasql.wasm` - Optimized WASM binary (renamed from build)
- `zetasql-proto.tar.gz` - Proto file tarball
- `*.sha256` - Checksum files

## Build Output

### Build Directory (`build/`)

Intermediate build artifacts for development and testing:

- **`zetasql.wasm`** - Standard WASM binary (~100-200MB)
- **`zetasql.opt.wasm`** - Optimized WASM binary (~50-100MB, optimized with wasm-opt)
- **`zetasql-proto/`** - Directory containing ~70 proto files

### Release Directory (`release/`)

Distribution-ready artifacts for end users:

- **`zetasql.wasm`** - Optimized WASM binary
- **`zetasql-proto.tar.gz`** - Proto file collection (tarball)
- **`*.sha256`** - SHA256 checksum files

See [docs/RELEASE_USAGE.md](docs/RELEASE_USAGE.md) for detailed usage instructions and guidance on creating language-specific wrapper packages.

## Testing

The project includes a comprehensive test suite that validates the WASM binary functionality.

### Running Tests

```bash
./scripts/test.sh
```

The test script automatically:
1. Checks for the built WASM binary
2. Creates a Python virtual environment if needed
3. Installs test dependencies
4. Generates Python protobuf code
5. Runs all tests with pytest

### Test Requirements

- Python 3.7+
- protoc (Protocol Buffer compiler)
- Built WASM binary (`build/zetasql.opt.wasm`)

## Updating ZetaSQL Version

1. Update the commit hash in `ZETASQL_VERSION`.
2. Run `./scripts/setup_dev.sh` to reset the workspace and attempt to re-apply patches.
3. Resolve any merge conflicts in `_work/zetasql`, commit the fixes, and run `./scripts/export_patches.sh`.
4. Rebuild with `./scripts/build.sh` and prepare release with `./scripts/prepare_release.sh`.
