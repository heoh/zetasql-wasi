#!/bin/bash
# Prepare ZetaSQL WASI release artifacts from build outputs
# This script creates distribution-ready release files from build/ directory

set -e

echo "Preparing ZetaSQL WASI release artifacts..."
echo ""

# Get script directory
SCRIPT_DIR=$(dirname "${BASH_SOURCE[0]}")
PROJECT_ROOT=$(realpath "${SCRIPT_DIR}/..")
BUILD_DIR="$PROJECT_ROOT/build"
RELEASE_DIR="$PROJECT_ROOT/release"

# Check if build artifacts exist
if [ ! -d "$BUILD_DIR" ]; then
  echo "Error: Build directory not found: $BUILD_DIR"
  echo "Please run scripts/build.sh first to build the artifacts."
  exit 1
fi

if [ ! -f "$BUILD_DIR/zetasql_local_service_wasi.opt.wasm" ]; then
  echo "Error: Optimized WASM binary not found: $BUILD_DIR/zetasql_local_service_wasi.opt.wasm"
  echo "Please run scripts/build.sh first to build the artifacts."
  exit 1
fi

if [ ! -d "$BUILD_DIR/zetasql_local_service_proto" ]; then
  echo "Error: Proto directory not found: $BUILD_DIR/zetasql_local_service_proto"
  echo "Please run scripts/build.sh first to build the artifacts."
  exit 1
fi

# Step 1: Create release directory
echo "Step 1/4: Creating release directory..."
rm -rf "$RELEASE_DIR"
mkdir -p "$RELEASE_DIR"

# Step 2: Copy and rename WASM binary
echo ""
echo "Step 2/4: Copying WASM binary..."
cp "$BUILD_DIR/zetasql_local_service_wasi.opt.wasm" "$RELEASE_DIR/zetasql_local_service_wasi.wasm"

# Step 3: Create proto tarball
echo ""
echo "Step 3/4: Creating proto tarball..."
tar -czf "$RELEASE_DIR/zetasql_local_service_proto.tar.gz" -C "$BUILD_DIR/zetasql_local_service_proto" zetasql

# Step 4: Generate checksums
echo ""
echo "Step 4/4: Generating checksums..."
cd "$RELEASE_DIR"
sha256sum zetasql_local_service_wasi.wasm > zetasql_local_service_wasi.wasm.sha256
sha256sum zetasql_local_service_proto.tar.gz > zetasql_local_service_proto.tar.gz.sha256

# Display results
cd "$PROJECT_ROOT"
echo ""
echo "✅ Release preparation complete!"
echo ""
echo "Release artifacts created in release/:"
echo "  - zetasql_local_service_wasi.wasm ($(ls -lh release/zetasql_local_service_wasi.wasm | awk '{print $5}'))"
echo "  - zetasql_local_service_proto.tar.gz ($(ls -lh release/zetasql_local_service_proto.tar.gz | awk '{print $5}'))"
echo ""
echo "Checksums:"
cat release/zetasql_local_service_wasi.wasm.sha256
cat release/zetasql_local_service_proto.tar.gz.sha256
echo ""
echo "Next steps:"
echo "  1. Verify checksums: cd release && sha256sum -c *.sha256"
echo "  2. Upload to GitHub Releases"
