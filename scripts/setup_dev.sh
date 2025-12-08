#!/bin/bash
set -e

# Get the directory of the script
SCRIPT_DIR=$(dirname "${BASH_SOURCE[0]}")
ROOT_DIR=$(realpath "${SCRIPT_DIR}/..")
WORK_DIR="${ROOT_DIR}/_work/zetasql"
PATCHES_DIR="${ROOT_DIR}/patches"

# Read ZETASQL_VERSION
source "${ROOT_DIR}/ZETASQL_VERSION"

if [ -z "$COMMIT_HASH" ]; then
    echo "Error: COMMIT_HASH not defined in ZETASQL_VERSION"
    exit 1
fi

echo "Target ZetaSQL Commit: $COMMIT_HASH"

# 1. Prepare Workspace
if [ ! -d "$WORK_DIR" ]; then
    echo "Cloning ZetaSQL into $WORK_DIR..."
    mkdir -p "$(dirname "$WORK_DIR")"
    git clone https://github.com/google/zetasql.git "$WORK_DIR"
fi

cd "$WORK_DIR"

# 2. Reset to target version
echo "Resetting workspace to $COMMIT_HASH..."
git fetch origin
git reset --hard "$COMMIT_HASH"
git clean -fd

# 3. Apply Patches
if [ -d "$PATCHES_DIR" ] && [ "$(ls -A $PATCHES_DIR/*.patch 2>/dev/null)" ]; then
    echo "Applying patches from $PATCHES_DIR..."
    
    # Use git am for applying patches as commits
    # We use 'git am --keep-cr' to handle potential line ending issues
    # We use '--3way' to help with simple conflicts
    git am --3way --keep-cr "$PATCHES_DIR"/*.patch
    
    echo "All patches applied successfully!"
else
    echo "No patches found in $PATCHES_DIR."
fi

echo ""
echo "Development environment ready."
echo "You can now build with Bazel:"
echo "  cd $(realpath "$WORK_DIR")"
echo "  bazel build --config=wasi //zetasql/tools/execute_query:execute_query_wasi"
echo ""
echo "When finished making changes, run from the root directory:"
echo "  ./scripts/export_patches.sh"
