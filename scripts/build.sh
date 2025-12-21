#!/bin/bash
# Build ZetaSQL WASI release artifacts
# This script builds the optimized WASM binary and proto tarball for distribution

set -e

echo "Building ZetaSQL WASI release artifacts..."
echo ""

# Get script directory
SCRIPT_DIR=$(dirname "${BASH_SOURCE[0]}")
PROJECT_ROOT=$(realpath "${SCRIPT_DIR}/..")
BUILD_DIR="$PROJECT_ROOT/build"

# Check if _work/zetasql exists
if [ ! -d "$PROJECT_ROOT/_work/zetasql" ]; then
  echo "Error: ZetaSQL source not found in _work/zetasql"
  echo "Please run scripts/setup_dev.sh first to set up the development environment."
  exit 1
fi

cd "$PROJECT_ROOT/_work/zetasql"

# Step 1: Initialize build directory
echo ""
echo "Step 1/5: Initializing build directory..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Step 2: Build optimized WASM binary
echo ""
echo "Step 2/5: Building optimized WASM binary..."
bazel build --config=wasi //zetasql/local_service:local_service_wasi_opt

# Step 3: Copy WASM binary
echo ""
echo "Step 3/5: Copying WASM binary..."
cp bazel-bin/zetasql/local_service/local_service_wasi $BUILD_DIR/zetasql.wasm
cp bazel-bin/zetasql/local_service/local_service_wasi.opt.wasm $BUILD_DIR/zetasql.opt.wasm

# Step 4: Build generated proto files
echo ""
echo "Step 4/5: Building generated proto files..."
bazel build //zetasql/parser:parse_tree //zetasql/resolved_ast:resolved_ast

# Step 5: Collect proto files
echo ""
echo "Step 5/5: Collecting proto files..."
PROTO_DIR="$PROJECT_ROOT/build/zetasql-proto"

# Clean and prepare directory
rm -rf "$PROTO_DIR"
mkdir -p "$PROTO_DIR"

# Copy only .proto files from source directories (preserving directory structure)
cd "$PROJECT_ROOT/_work/zetasql"

# 1. Copy all .proto files from zetasql/ (excluding bazel-* symlinks)
find zetasql -type f -name "*.proto" ! -path "*/bazel-*/*" ! -name "*_test.proto" | while read -r proto_file; do
  target_dir="$PROTO_DIR/$(dirname "$proto_file")"
  mkdir -p "$target_dir"
  cp "$proto_file" "$target_dir/"
done

# 2. Copy generated proto files from bazel-bin/zetasql/
find bazel-bin/zetasql -type f -name "*.proto" 2>/dev/null | while read -r proto_file; do
  # Remove bazel-bin/ prefix to get target path
  relative_path="${proto_file#bazel-bin/}"
  target_dir="$PROTO_DIR/$(dirname "$relative_path")"
  mkdir -p "$target_dir"
  cp "$proto_file" "$target_dir/"
done

echo "  Collected $(find "$PROTO_DIR" -name "*.proto" | wc -l) proto files"

# Display results
cd "$PROJECT_ROOT"
echo ""
echo "✅ Build complete!"
echo ""
echo "Build artifacts created in build/:"
echo "  - zetasql.wasm ($(ls -lh build/zetasql.wasm | awk '{print $5}'))"
echo "  - zetasql.opt.wasm ($(ls -lh build/zetasql.opt.wasm | awk '{print $5}'))"
echo "  - zetasql-proto/ (contains $(find "$PROTO_DIR" -name "*.proto" | wc -l) proto files)"
