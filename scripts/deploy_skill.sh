#!/bin/bash
#
# Deploy script for Holo RSS Reader Skill
# Usage: ./deploy_skill.sh <target-path>
#

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

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
    "holo_rss_reader"
    "scripts"
    "main.py"
    "README.md"
    "SKILL.md"
    "pyproject.toml"
)

# Copy each item
for item in "${DEPLOY_ITEMS[@]}"; do
    if [ -e "$PROJECT_ROOT/$item" ]; then
        echo "Copying $item..."
        rm -rf "$TARGET_PATH/$item" 2>/dev/null || true
        cp -r "$PROJECT_ROOT/$item" "$TARGET_PATH/"
    else
        echo "Warning: $item not found, skipping"
    fi
done

echo ""
echo "✅ Deployment complete!"
echo ""
echo "To use the skill:"
echo "  cd $TARGET_PATH"
echo "  uv sync"
echo "  python main.py --help"
