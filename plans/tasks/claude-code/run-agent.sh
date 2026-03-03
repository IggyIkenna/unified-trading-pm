#!/bin/bash
# Wrapper for Claude Code to run agent CLI with full workspace context
# Usage: ./run-agent.sh <target-repo-name> <prompt>
#
# Example: ./run-agent.sh unified-config-interface "Fix all basedpyright errors"
#
# Key features:
# - Uses workspace root for full context (codex, dependencies, workspace rules)
# - Restricts edits to target repo only (via prompt instruction)
# - Enables parallel execution (different repos = no conflicts)

set -e

TARGET_REPO="$1"
PROMPT="$2"

# Workspace root (contains all repos, codex, and workspace rules)
WORKSPACE_ROOT="/Users/ikennaigboaka/Documents/repos/unified-trading-system-repos"

# Set up environment
export PATH="$HOME/.local/bin:$PATH"

# Get API key (never use world-readable temp file)
if [ -z "${CURSOR_API_KEY:-}" ]; then
    PROJECT_ID="${GCP_PROJECT_ID:?GCP_PROJECT_ID must be set to fetch cursor-api-key from Secret Manager}"
    CURSOR_API_KEY=$(gcloud secrets versions access latest --secret=cursor-api-key --project="$PROJECT_ID")
    export CURSOR_API_KEY
fi

# Set parser path
PARSER="/Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/.cursor/plans/tasks_claude_code/simple-parser.py"

# Enhanced prompt with workspace context and edit restrictions
ENHANCED_PROMPT="WORKSPACE CONTEXT:
- Workspace root: $WORKSPACE_ROOT
- Target repo: $TARGET_REPO/
- You have READ access to entire workspace (codex, dependencies, workspace rules)
- You can ONLY EDIT files in $TARGET_REPO/ directory
- Read unified-trading-codex/ for standards
- Read workspace .cursorrules and .cursor/rules/*.mdc
- Read path dependencies (../unified-trading-library, etc.)

TASK:
$PROMPT

CRITICAL RESTRICTIONS:
- ONLY edit files in $TARGET_REPO/ directory
- DO NOT edit unified-trading-codex/, unified-trading-library/, or other repos
- You can read everything, but edit only $TARGET_REPO/

IMPORTANT: Only run basedpyright 2-3 times total (not every 5 files) to avoid hanging:
- Once at start to see errors
- Once mid-way to check progress
- Once at end to verify 0 errors
"

# Run agent with pretty printing
agent --api-key "$CURSOR_API_KEY" \
    --print \
    --model auto \
    --trust \
    --force \
    --output-format stream-json \
    --stream-partial-output \
    --workspace "$WORKSPACE_ROOT" \
    "$ENHANCED_PROMPT" \
    2>&1 | python3 "$PARSER"
