#!/bin/bash
# Run ZetaSQL WASI tests
# This script sets up the test environment and runs all tests

set -e

# Get script directory
SCRIPT_DIR=$(dirname "${BASH_SOURCE[0]}")
PROJECT_ROOT=$(realpath "${SCRIPT_DIR}/..")
WASM_FILE="$PROJECT_ROOT/build/zetasql.opt.wasm"
VENV_DIR="$PROJECT_ROOT/.venv"
PROTO_DIR="$PROJECT_ROOT/build/zetasql-proto"
PROTO_PB_DIR="$PROJECT_ROOT/build/generated_pb"

echo "ZetaSQL WASI Test Runner"
echo "========================"
echo ""

# Step 1: Check if WASM binary exists
if [ ! -f "$WASM_FILE" ]; then
  echo "❌ Error: WASM binary not found: $WASM_FILE"
  echo ""
  echo "Please build the project first:"
  echo "  ./scripts/build.sh"
  exit 1
fi

echo "✓ WASM binary found: $(ls -lh "$WASM_FILE" | awk '{print $5}')"

# Step 2: Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
  echo ""
  echo "Creating Python virtual environment..."
  python3 -m venv "$VENV_DIR"
  echo "✓ Virtual environment created"
fi

# Step 3: Activate virtual environment
source "$VENV_DIR/bin/activate"

# Step 4: Install/upgrade dependencies
echo ""
echo "Installing test dependencies..."
pip install -q --upgrade pip
pip install -q -r "$PROJECT_ROOT/requirements-test.txt"
echo "✓ Dependencies installed"

# Step 5: Generate protobuf code if needed
if [ ! -d "$PROTO_PB_DIR/zetasql" ]; then
  echo ""
  echo "Generating protobuf code..."
  
  # Check if proto directory exists
  if [ ! -d "$PROTO_DIR" ]; then
    echo "❌ Error: Proto directory not found: $PROTO_DIR"
    echo ""
    echo "Please run './scripts/build.sh' first to generate proto files."
    exit 1
  fi
  
  # Check if protoc is installed
  if ! command -v protoc &> /dev/null; then
    echo "❌ Error: protoc not found"
    echo ""
    echo "Please install Protocol Buffer compiler:"
    echo "  Ubuntu/Debian: sudo apt-get install protobuf-compiler"
    echo "  macOS: brew install protobuf"
    exit 1
  fi
  
  # Create output directory
  mkdir -p "$PROTO_PB_DIR"
  
  # Find all .proto files
  PROTO_FILES=$(find "$PROTO_DIR" -name "*.proto" | grep -v "/testdata/" | sort)
  PROTO_COUNT=$(echo "$PROTO_FILES" | wc -l)
  
  echo "  Found $PROTO_COUNT proto files"
  
  # Generate Python code
  # Include system protobuf path for google/protobuf/*.proto dependencies
  protoc \
    --python_out="$PROTO_PB_DIR" \
    --proto_path="$PROTO_DIR" \
    --proto_path="/usr/include" \
    $PROTO_FILES
  
  echo "  Generated Python code in: $PROTO_PB_DIR"
  
  # Create __init__.py files for all directories
  find "$PROTO_PB_DIR" -type d -exec touch {}/__init__.py \;
  
  echo "✓ Protobuf code generation complete"
else
  echo "✓ Protobuf code exists"
fi

# Step 6: Run tests
echo ""
echo "Running tests..."
echo "========================"
echo ""

cd "$PROJECT_ROOT"
pytest tests/ -v "$@"

# Capture exit code
TEST_EXIT_CODE=$?

echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
  echo "✅ All tests passed!"
else
  echo "❌ Some tests failed"
fi

exit $TEST_EXIT_CODE
