#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# QG coverage-snapshot writer (Phase 8.E of deployment_and_qg_strategy_implementation_2026_05_13).
#
# Walks every repo in workspace-manifest.json; for each repo with a
# coverage.xml on disk (output of the most-recent quality-gates run),
# parses per-surface aggregates against coverage_targets.yaml and emits
# one JSON line per (repo, surface) tuple to stdout.
#
# Caller pipes stdout into coverage_snapshot_to_parquet.py for daily GCS write.
#
# execution:
#   owner:   qg-snapshot cron VM (deployment-service/scripts/vm/launch-qg-snapshot-vm.sh)
#   cadence: daily 06:30 UTC (chained after snapshot.sh)
#   verifier: gs://{pid}-deployment-events/coverage_snapshot/ gains new blobs
#   last_executed: 2026-05-17 (local smoke from slot-8 — see deployment_and_qg_strategy_implementation_2026_05_13 Phase 8.E flip)
#
# Usage (standalone smoke):
#   WORKSPACE_ROOT=/path/to/workspace \
#   PROJECT_ID=central-element-323112 \
#   bash scripts/quality_gates/coverage_snapshot.sh | \
#     python3 scripts/quality_gates/coverage_snapshot_to_parquet.py --project-id $PROJECT_ID

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/../../.." && pwd)}"
MANIFEST="$WORKSPACE_ROOT/unified-trading-pm/workspace-manifest.json"
SNAPSHOT_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

if [[ ! -f "$MANIFEST" ]]; then
    echo "ERROR: workspace-manifest.json not found at $MANIFEST" >&2
    exit 1
fi

REPOS="$(python3 -c "
import json
with open('$MANIFEST') as f:
    d = json.load(f)
for name in d['repositories']:
    print(name)
")"

REPO_COUNT=$(echo "$REPOS" | wc -l | tr -d ' ')
echo "Coverage snapshot starting: $REPO_COUNT repos, snapshot_at=$SNAPSHOT_AT" >&2

TOTAL=0; HAD_XML=0; NO_XML=0
while IFS= read -r repo; do
    repo_path="$WORKSPACE_ROOT/$repo"
    coverage_xml="$repo_path/coverage.xml"
    if [[ ! -f "$coverage_xml" ]]; then
        ((NO_XML++)) || true
        continue
    fi
    ((HAD_XML++)) || true
    # Emit JSON lines for this repo using the existing check_coverage_targets.py
    # but only the parse + aggregate path — we don't want it to fail this script.
    python3 "$SCRIPT_DIR/coverage_snapshot_emit.py" \
        --workspace-root "$WORKSPACE_ROOT" \
        --repo "$repo" \
        --coverage-xml "$coverage_xml" \
        --snapshot-at "$SNAPSHOT_AT" || true
    ((TOTAL++)) || true
done <<< "$REPOS"

echo "Coverage snapshot complete: repos_with_xml=$HAD_XML repos_without_xml=$NO_XML" >&2
