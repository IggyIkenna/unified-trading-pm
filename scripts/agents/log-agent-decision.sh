#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# log-agent-decision.sh — Append an agent decision record as JSONL.
#
# Usage:
#   bash scripts/agents/log-agent-decision.sh <workflow> <repo> <action> <reasoning> <outcome> <commit_sha>
#
# Writes one JSON line per call to:
#   plans/audit/agent_decisions/YYYY-MM-DD.jsonl
#
# All fields are required. Empty strings are accepted but logged as-is.

set -euo pipefail

if [ "$#" -ne 6 ]; then
    echo "Usage: $0 <workflow> <repo> <action> <reasoning> <outcome> <commit_sha>" >&2
    exit 1
fi

WORKFLOW="$1"
REPO="$2"
ACTION="$3"
REASONING="$4"
OUTCOME="$5"
COMMIT_SHA="$6"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PM_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DECISIONS_DIR="$PM_ROOT/plans/audit/agent_decisions"

mkdir -p "$DECISIONS_DIR"

TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
DATE_FILE="$(date -u +%Y-%m-%d)"
OUTPUT_FILE="$DECISIONS_DIR/${DATE_FILE}.jsonl"

# Use python for safe JSON serialisation (no jq dependency)
python3 -c "
import json, sys
record = {
    'timestamp': sys.argv[1],
    'workflow': sys.argv[2],
    'repo': sys.argv[3],
    'action': sys.argv[4],
    'reasoning': sys.argv[5],
    'outcome': sys.argv[6],
    'commit_sha': sys.argv[7],
}
print(json.dumps(record, ensure_ascii=False))
" "$TIMESTAMP" "$WORKFLOW" "$REPO" "$ACTION" "$REASONING" "$OUTCOME" "$COMMIT_SHA" >> "$OUTPUT_FILE"

echo "Logged decision to $OUTPUT_FILE"
