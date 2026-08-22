#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# launch-tab-precompact-session.sh — start (or attach to) a tmux-wrapped `claude`
# CLI session for one tab/slot, so precompact-watcher.py can reach it via
# `tmux send-keys` (the extension chat panel has no exposed pty — CLI-in-a-terminal
# only, incl. Cursor/VS Code's own integrated terminal). SSOT:
# codex/05-infrastructure/local-tmux-precompact-watcher.md
#
# Usage: bash scripts/dev/launch-tab-precompact-session.sh <tab-dir> [session-name]
# Example: bash scripts/dev/launch-tab-precompact-session.sh ~/Code/unified-trading-system-repos/.tabs/3 claude-tab3

set -euo pipefail

TAB_DIR="${1:?Usage: launch-tab-precompact-session.sh <tab-dir> [session-name]}"
SESSION="${2:-claude-$(basename "$TAB_DIR")}"

if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux not found. Install it first: brew install tmux" >&2
  exit 1
fi

if [ ! -d "$TAB_DIR" ]; then
  echo "Tab directory not found: $TAB_DIR" >&2
  exit 1
fi

# Exact-match target (bare -t prefix-matches, e.g. claude-tab1 also matches
# claude-tab10 — same class of bug tmux_spawn.py's exact_target() exists to avoid).
if tmux has-session -t "=$SESSION" 2>/dev/null; then
  echo "Session '$SESSION' already running. Attaching..."
  exec tmux attach -t "=$SESSION"
fi

echo "Starting new tmux session '$SESSION' in $TAB_DIR ..."
tmux new-session -d -s "$SESSION" -c "$TAB_DIR" "claude"

echo "Session '$SESSION' started."
echo ""
echo "Attach with:   tmux attach -t $SESSION"
echo "Detach with:   Ctrl-b d   (session keeps running)"
echo ""
echo "Start the watcher (separate terminal, once per session):"
echo "  python3 $(cd "$(dirname "$0")" && pwd)/precompact-watcher.py $SESSION"
