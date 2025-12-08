#!/bin/bash
set -e

# Get the directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR="${SCRIPT_DIR}/.."
WORK_DIR="${ROOT_DIR}/_work/zetasql"
PATCHES_DIR="${ROOT_DIR}/patches"

# Read ZETASQL_VERSION
source "${ROOT_DIR}/ZETASQL_VERSION"

if [ ! -d "$WORK_DIR" ]; then
    echo "Error: Work directory $WORK_DIR does not exist. Run setup_dev.sh first."
    exit 1
fi

cd "$WORK_DIR"

# Verify we are ahead of the base commit
if [ -z "$(git log $COMMIT_HASH..HEAD --oneline)" ]; then
    echo "No new commits found since $COMMIT_HASH."
    echo "Syncing patches (clearing existing patches)..."
else
    echo "Exporting patches from $WORK_DIR..."
fi

# Clean old patches
rm -f "$PATCHES_DIR"/*.patch

# Generate new patches
# --start-number 1 ensures patches start with 0001
git format-patch --no-numbered "$COMMIT_HASH" -o "$PATCHES_DIR" --start-number 1

# Remove 'From <hash>' and 'Date:' header lines to avoid patch changes on rebases
for patch in "$PATCHES_DIR"/*.patch; do
    if [ -f "$patch" ]; then
        sed -i -e '/^From [0-9a-f]\{40\} /d' -e '/^Date: /d' "$patch"
    fi
done

echo "Patches exported to $PATCHES_DIR"
echo "Done!"
