#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# record-manifest-mutation.sh — Append a manifest mutation record to the audit log.
#
# Called by manifest-mutating workflows to create an audit trail of all
# changes to workspace-manifest.json.
#
# Usage:
#   bash scripts/audit/record-manifest-mutation.sh \
#     --workflow update-repo-version.yml \
#     --actor semver-agent \
#     --mutation-type version-bump \
#     --fields-changed '["repos.unified-trading-library.version"]' \
#     --old-value-hash abc123 \
#     --new-value-hash def456 \
#     --commit-sha 1234567
#
# Output: appends to plans/audit/manifest_mutations.jsonl
#
# Designed to be sourced by GHA workflows:
#   source scripts/audit/record-manifest-mutation.sh  (for function use)
#   OR called directly as a script

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
OUT_FILE="$PM_ROOT/plans/audit/manifest_mutations.jsonl"

# ── Parse args ───────────────────────────────────────────────────────────────
WORKFLOW="" ACTOR="" MUTATION_TYPE="" FIELDS_CHANGED="[]"
OLD_VALUE_HASH="" NEW_VALUE_HASH="" COMMIT_SHA=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workflow)        WORKFLOW="$2";        shift 2 ;;
    --actor)           ACTOR="$2";           shift 2 ;;
    --mutation-type)   MUTATION_TYPE="$2";   shift 2 ;;
    --fields-changed)  FIELDS_CHANGED="$2";  shift 2 ;;
    --old-value-hash)  OLD_VALUE_HASH="$2";  shift 2 ;;
    --new-value-hash)  NEW_VALUE_HASH="$2";  shift 2 ;;
    --commit-sha)      COMMIT_SHA="$2";      shift 2 ;;
    *) echo "ERROR: Unknown arg: $1" >&2; exit 1 ;;
  esac
done

# ── Validate ─────────────────────────────────────────────────────────────────
MISSING=""
[[ -z "$WORKFLOW" ]]      && MISSING="$MISSING --workflow"
[[ -z "$ACTOR" ]]         && MISSING="$MISSING --actor"
[[ -z "$MUTATION_TYPE" ]] && MISSING="$MISSING --mutation-type"
[[ -z "$COMMIT_SHA" ]]    && MISSING="$MISSING --commit-sha"

if [[ -n "$MISSING" ]]; then
  echo "ERROR: Missing required args:$MISSING" >&2
  exit 1
fi

# ── Write record ─────────────────────────────────────────────────────────────
mkdir -p "$(dirname "$OUT_FILE")"

TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

python3 -c "
import json

record = {
    'timestamp': '$TIMESTAMP',
    'workflow': '$WORKFLOW',
    'actor': '$ACTOR',
    'mutation_type': '$MUTATION_TYPE',
    'fields_changed': json.loads('''$FIELDS_CHANGED'''),
    'old_value_hash': '$OLD_VALUE_HASH',
    'new_value_hash': '$NEW_VALUE_HASH',
    'commit_sha': '$COMMIT_SHA'
}

print(json.dumps(record, separators=(',', ':')))
" >> "$OUT_FILE"

echo "Recorded manifest mutation to: $OUT_FILE"
