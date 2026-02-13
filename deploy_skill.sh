#!/bin/bash
#
# Deploy script for Holo RSS Reader Skill
# Usage: ./deploy_skill.sh <target-path>
#

set -e

# Get the directory where this script is located (project root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Global venv path - use $HOME
GLOBAL_VENV="$HOME/.openclaw/.venv"

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

# Read dependencies from pyproject.toml
echo "Reading dependencies from pyproject.toml..."
DEPS=$(python3 -c "
import tomllib
with open('$SCRIPT_DIR/pyproject.toml', 'rb') as f:
    data = tomllib.load(f)
    deps = data.get('project', {}).get('dependencies', [])
    print(' '.join(deps))
")

if [ -z "$DEPS" ]; then
    echo "No dependencies found, skipping installation"
else
    echo "Dependencies: $DEPS"
    # Install to global venv
    echo "Installing dependencies to global venv..."
    uv pip install --python "$GLOBAL_VENV/bin/python" $DEPS
fi

# Create target directory
mkdir -p "$TARGET_PATH"

# Files and directories to copy
DEPLOY_ITEMS=(
    "SKILL.md"
    "scripts"
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

# Remove cache
rm -rf "$TARGET_PATH"/**/__pycache__ 2>/dev/null || true

echo ""
echo "✅ Deployment complete!"
