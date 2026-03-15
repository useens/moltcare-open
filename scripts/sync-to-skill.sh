#!/bin/bash
# Sync templates to skill/assets before publishing

set -e

echo "🔄 Syncing templates to skill/assets..."

# Core templates
cp templates/core/*.md skill/assets/

# Memory templates
cp templates/memory/*.md skill/assets/

# System templates (HEARTBEAT.md)
cp templates/system/HEARTBEAT.md skill/assets/

echo "✅ Sync complete!"
echo ""
echo "Files synced:"
ls -la skill/assets/
echo ""
echo "Next step:"
echo "  git add skill/assets/"
echo "  git commit -m 'sync: update skill assets from templates'"
echo "  git push origin master  # This will trigger auto-publish"
