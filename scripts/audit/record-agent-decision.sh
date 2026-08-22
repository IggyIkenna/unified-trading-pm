#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# record-agent-decision.sh — Append an agent decision record to the daily JSONL file.
#
# Usage:
#   bash scripts/audit/record-agent-decision.sh \
#     --workflow semver-agent.yml \
#     --repo unified-trading-library \
#     --agent-type claude-haiku \
#     --decision bump-minor \
#     --reasoning "feat! commit detected, bumped 0.2.3 -> 0.3.0" \
#     --files-changed '["pyproject.toml","CHANGELOG.md"]' \
#     --commit-sha abc1234 \
#     --success true
#
# On failure, add: --error-message "description of failure"
#
# Output: appends to plans/audit/agent_decisions/{YYYY-MM-DD}.jsonl

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DECISIONS_DIR="$PM_ROOT/plans/audit/agent_decisions"

# ── Parse args ───────────────────────────────────────────────────────────────
WORKFLOW="" REPO="" AGENT_TYPE="" DECISION="" REASONING="" FILES_CHANGED="[]"
COMMIT_SHA="" SUCCESS="" ERROR_MESSAGE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workflow)       WORKFLOW="$2";       shift 2 ;;
    --repo)           REPO="$2";           shift 2 ;;
    --agent-type)     AGENT_TYPE="$2";     shift 2 ;;
    --decision)       DECISION="$2";       shift 2 ;;
    --reasoning)      REASONING="$2";      shift 2 ;;
    --files-changed)  FILES_CHANGED="$2";  shift 2 ;;
    --commit-sha)     COMMIT_SHA="$2";     shift 2 ;;
    --success)        SUCCESS="$2";        shift 2 ;;
    --error-message)  ERROR_MESSAGE="$2";  shift 2 ;;
    *) echo "ERROR: Unknown arg: $1" >&2; exit 1 ;;
  esac
done

# ── Validate ─────────────────────────────────────────────────────────────────
MISSING=""
[[ -z "$WORKFLOW" ]]   && MISSING="$MISSING --workflow"
[[ -z "$REPO" ]]       && MISSING="$MISSING --repo"
[[ -z "$AGENT_TYPE" ]] && MISSING="$MISSING --agent-type"
[[ -z "$DECISION" ]]   && MISSING="$MISSING --decision"
[[ -z "$REASONING" ]]  && MISSING="$MISSING --reasoning"
[[ -z "$SUCCESS" ]]    && MISSING="$MISSING --success"

if [[ -n "$MISSING" ]]; then
  echo "ERROR: Missing required args:$MISSING" >&2
  exit 1
fi

if [[ "$SUCCESS" != "true" && "$SUCCESS" != "false" ]]; then
  echo "ERROR: --success must be true or false (got: $SUCCESS)." >&2
  exit 1
fi

# ── Build record ─────────────────────────────────────────────────────────────
mkdir -p "$DECISIONS_DIR"

TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
TODAY="$(date -u +%Y-%m-%d)"
OUT_FILE="$DECISIONS_DIR/${TODAY}.jsonl"

python3 -c "
import json

record = {
    'timestamp': '$TIMESTAMP',
    'workflow': '$WORKFLOW',
    'repo': '$REPO',
    'agent_type': '$AGENT_TYPE',
    'decision': '$DECISION',
    'reasoning_summary': $(python3 -c "import json; print(json.dumps('$REASONING'))"),
    'files_changed': json.loads('''$FILES_CHANGED'''),
    'commit_sha': '$COMMIT_SHA',
    'success': $SUCCESS
}

error_msg = '''$ERROR_MESSAGE'''
if error_msg:
    record['error_message'] = error_msg

print(json.dumps(record, separators=(',', ':')))
" >> "$OUT_FILE"

echo "Recorded decision to: $OUT_FILE"
