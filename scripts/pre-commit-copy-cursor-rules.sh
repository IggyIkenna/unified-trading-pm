#!/usr/bin/env bash
# Pre-commit: copy cursor rules from PM into this repo's .cursor/rules
# SSOT: unified-trading-pm/cursor-rules
# Flow: change rules in PM -> propagate to workspace (local dev) -> pre-commit copies into each repo (for background agents)
# Exits 1 if rules source not found — commit blocked until repo is in workspace layout.

set -e
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

SOURCE=""
if [ -d "$ROOT/cursor-rules" ]; then
  SOURCE="$ROOT/cursor-rules"
elif [ -d "$ROOT/../unified-trading-pm/cursor-rules" ]; then
  SOURCE="$ROOT/../unified-trading-pm/cursor-rules"
fi

if [ -z "$SOURCE" ]; then
  echo "ERROR: cursor rules not found. Repo must be in workspace with unified-trading-pm as sibling."
  echo "  Expected: $ROOT/cursor-rules (PM) or $ROOT/../unified-trading-pm/cursor-rules"
  exit 1
fi

rm -rf "$ROOT/.cursor/rules"
mkdir -p "$ROOT/.cursor"
cp -r "$SOURCE" "$ROOT/.cursor/rules"
git add "$ROOT/.cursor/rules"
