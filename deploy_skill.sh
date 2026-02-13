#!/bin/bash
#
# Deploy script for Holo RSS Reader Skill
# Usage: ./deploy_skill.sh <target-path>
#

set -e

# Get the directory where this script is located (project root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 <target-path>"
    exit 1
fi

TARGET_PATH="$1"

# Resolve target path
if [[ "$TARGET_PATH" != /* ]]; then
    echo "Error: Target path must be absolute"
    exit 1
fi

echo "Deploying Holo RSS Reader to: $TARGET_PATH"

# Create target directory
mkdir -p "$TARGET_PATH"

# Files and directories to copy (independent of project)
DEPLOY_ITEMS=(
    "SKILL.md"
    "scripts"
    "pyproject.toml"
)

# Copy each item
for item in "${DEPLOY_ITEMS[@]}"; do
    if [ -e "$SCRIPT_DIR/$item" ]; then
        echo "Copying $item..."
        rm -rf "$TARGET_PATH/$item" 2>/dev/null || true
        cp -r "$SCRIPT_DIR/$item" "$TARGET_PATH/"
    else
        echo "Warning: $item not found, skipping"
    fi
done

# Remove deploy script, cache and unnecessary files
rm -f "$TARGET_PATH/scripts/deploy_skill.sh" 2>/dev/null || true
rm -f "$TARGET_PATH/scripts/__init__.py" 2>/dev/null || true
rm -rf "$TARGET_PATH"/*/__pycache__ 2>/dev/null || true
rm -f "$TARGET_PATH/uv.lock" 2>/dev/null || true

# Install dependencies
echo "Installing dependencies..."
cd "$TARGET_PATH"
uv sync

# Remove pyproject.toml after installation (not needed at runtime)
rm -f "$TARGET_PATH/pyproject.toml"
rm -f "$TARGET_PATH/uv.lock"
rm -rf "$TARGET_PATH"/*.egg-info

echo ""
echo "✅ Deployment complete!"
