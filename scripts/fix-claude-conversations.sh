#!/usr/bin/env bash
# fix-claude-conversations.sh — Replace symlink with actual copy of conversations
# Claude Code doesn't always follow symlinks correctly

set -euo pipefail

echo "🔧 Fixing Claude Code conversations..."
echo ""

# Check Claude Code is closed
if pgrep -x "claude-code" >/dev/null 2>&1; then
    echo "⚠️  Claude Code is running!"
    echo "Please close Claude Code (Cmd+Q) and run this script again."
    exit 1
fi

OLD_DIR="$HOME/.claude/projects/-Users-${USER}-Documents-repos-unified-trading-system-repos"
NEW_DIR="$HOME/.claude/projects/-Users-${USER}-Documents-Documents - Mac-repos-unified-trading-system-repos"

# Check old conversations exist
if [ ! -d "$OLD_DIR" ]; then
    echo "❌ Old conversations not found: $OLD_DIR"
    exit 1
fi

echo "✅ Found old conversations: $(du -sh "$OLD_DIR" | awk '{print $1}')"

# Remove symlink if it exists
if [ -L "$NEW_DIR" ]; then
    echo "📝 Removing symlink..."
    rm "$NEW_DIR"
fi

# Copy if needed
if [ ! -d "$NEW_DIR" ] || [ -L "$NEW_DIR" ]; then
    echo "📋 Copying conversations to new location..."
    cp -R "$OLD_DIR" "$NEW_DIR"
    echo "✅ Copied $(ls "$NEW_DIR"/*.jsonl 2>/dev/null | wc -l | xargs) conversations"
else
    echo "✅ New directory already exists"
fi

echo ""
echo "✅ Done! Open Claude Code and check your conversations."
