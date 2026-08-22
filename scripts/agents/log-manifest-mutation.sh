#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
set -euo pipefail

# log-manifest-mutation.sh — Append a JSON audit line to plans/audit/manifest-mutations.jsonl
#
# Usage:
#   bash scripts/agents/log-manifest-mutation.sh <workflow_name> <changes_summary>
#
# Environment:
#   GITHUB_ACTOR    — the actor (set automatically in GHA)
#   GITHUB_SHA      — the commit SHA (set automatically in GHA)
#
# Designed to be called from manifest-mutating workflows after each manifest write.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
AUDIT_FILE="$REPO_ROOT/plans/audit/manifest-mutations.jsonl"

WORKFLOW="${1:-unknown}"
CHANGES_SUMMARY="${2:-no summary provided}"
ACTOR="${GITHUB_ACTOR:-local}"
COMMIT_SHA="${GITHUB_SHA:-$(git -C "$REPO_ROOT" rev-parse HEAD 2>/dev/null || echo 'unknown')}"
TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Ensure the audit directory exists
mkdir -p "$(dirname "$AUDIT_FILE")"

# Append JSON line (use python3 for safe JSON encoding)
python3 -c "
import json, sys
entry = {
    'timestamp': '$TIMESTAMP',
    'workflow': '$WORKFLOW',
    'actor': '$ACTOR',
    'changes_summary': sys.argv[1],
    'commit_sha': '$COMMIT_SHA'
}
print(json.dumps(entry, ensure_ascii=False))
" "$CHANGES_SUMMARY" >> "$AUDIT_FILE"

echo "Logged manifest mutation: workflow=$WORKFLOW actor=$ACTOR sha=${COMMIT_SHA:0:8}"
