#!/bin/bash
# MoltCare-Open Installation Script

set -e

WORKSPACE="${HOME}/.openclaw/workspace"
MEMORY_DIR="${WORKSPACE}/memory"

echo "🦞 Installing MoltCare-Open Framework..."

# Create directories
mkdir -p "${WORKSPACE}"
mkdir -p "${MEMORY_DIR}"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ASSETS_DIR="${SCRIPT_DIR}/../assets"

# Copy core templates
echo "📄 Copying core templates..."
cp "${ASSETS_DIR}/SOUL.md" "${WORKSPACE}/"
cp "${ASSETS_DIR}/AGENTS.md" "${WORKSPACE}/"
cp "${ASSETS_DIR}/USER.md" "${WORKSPACE}/"
cp "${ASSETS_DIR}/MEMORY.md" "${WORKSPACE}/"
cp "${ASSETS_DIR}/HEARTBEAT.md" "${WORKSPACE}/"

# Copy memory templates
echo "📝 Copying memory templates..."
cp "${ASSETS_DIR}/learning-debt.md" "${MEMORY_DIR}/"
cp "${ASSETS_DIR}/constraints.md" "${MEMORY_DIR}/"
cp "${ASSETS_DIR}/preferences.md" "${MEMORY_DIR}/"

# Create today\'s memory file
TODAY=$(date +%Y-%m-%d)
if [ ! -f "${MEMORY_DIR}/${TODAY}.md" ]; then
    echo "📅 Creating today\'s memory file..."
    echo "# ${TODAY} Memory Flush" > "${MEMORY_DIR}/${TODAY}.md"
fi

echo "✅ MoltCare-Open installed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit ${WORKSPACE}/USER.md to configure your profile"
echo "2. Edit ${WORKSPACE}/MEMORY.md to add your high-signal memories"
echo "3. Start using the three-layer trigger system!"
