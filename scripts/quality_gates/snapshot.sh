#!/usr/bin/env bash
# QG snapshot writer (B-018 Phase 4.A).
#
# Runs `bash scripts/quality-gates.sh --quick` for every repo in
# workspace-manifest.json. Emits one JSON line per repo to stdout;
# caller pipes that into snapshot_to_parquet.py.
#
# execution:
#   owner:   qg-snapshot cron VM (deployment-service/scripts/vm/launch-qg-snapshot-vm.sh)
#   cadence: daily 06:00 UTC via Cloud Scheduler
#   verifier: gs://{pid}-deployment-events/quality_gates_snapshot/ gains new blobs
#   last_executed: 2026-05-14 (local smoke + full workspace run: 36 repos, 36 parquets → gs://central-element-323112-deployment-events/quality_gates_snapshot/)
#
# Usage (standalone smoke):
#   WORKSPACE_ROOT=/home/hk/unified-trading-system-repos \
#   PROJECT_ID=central-element-323112 \
#   bash scripts/quality_gates/snapshot.sh | \
#     python3 scripts/quality_gates/snapshot_to_parquet.py
#
# Plan: deployment_and_qg_strategy_implementation_2026_05_13.md Phase 4.A.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$SCRIPT_DIR/../../.." && pwd)}"
MANIFEST="$WORKSPACE_ROOT/unified-trading-pm/workspace-manifest.json"
SNAPSHOT_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
PARALLEL="${PARALLEL:-8}"

if [[ ! -f "$MANIFEST" ]]; then
    echo "ERROR: workspace-manifest.json not found at $MANIFEST" >&2
    exit 1
fi

RUN_DIR="$(mktemp -d)"
trap 'rm -rf "$RUN_DIR"' EXIT

# Extract repo names from workspace-manifest.json
REPOS="$(python3 -c "
import json, sys
with open('$MANIFEST') as f:
    d = json.load(f)
for name in d['repositories']:
    print(name)
")"

REPO_COUNT=$(echo "$REPOS" | wc -l | tr -d ' ')
echo "QG snapshot starting: $REPO_COUNT repos, parallelism=$PARALLEL, snapshot_at=$SNAPSHOT_AT" >&2

# Per-repo runner (called by xargs -P).
# Outputs one JSON line to RUN_DIR/result-{repo}.json.
run_one_repo() {
    local repo="$1"
    local workspace_root="$2"
    local snapshot_at="$3"
    local run_dir="$4"

    local repo_path="$workspace_root/$repo"
    local result_file="$run_dir/result-${repo}.json"
    local log_file="$run_dir/log-${repo}.txt"

    # Repo not on disk
    if [[ ! -d "$repo_path" ]]; then
        printf '{"repo":"%s","qg_status":"skipped","pull_sha":null,"failing_step":"repo_not_found_on_disk","first_error_line":null,"duration_seconds":0,"snapshot_at":"%s"}\n' \
            "$repo" "$snapshot_at" > "$result_file"
        return 0
    fi

    # Repo has no quality-gates.sh
    if [[ ! -f "$repo_path/scripts/quality-gates.sh" ]]; then
        printf '{"repo":"%s","qg_status":"skipped","pull_sha":null,"failing_step":"no_quality_gates_sh","first_error_line":null,"duration_seconds":0,"snapshot_at":"%s"}\n' \
            "$repo" "$snapshot_at" > "$result_file"
        return 0
    fi

    local pull_sha
    pull_sha="$(git -C "$repo_path" rev-parse HEAD 2>/dev/null || echo "unknown")"

    local start_ts end_ts duration_seconds exit_code
    start_ts="$(date +%s)"
    if bash "$repo_path/scripts/quality-gates.sh" --quick > "$log_file" 2>&1; then
        exit_code=0
    else
        exit_code=$?
    fi
    end_ts="$(date +%s)"
    duration_seconds=$((end_ts - start_ts))

    if [[ $exit_code -eq 0 ]]; then
        printf '{"repo":"%s","qg_status":"green","pull_sha":"%s","failing_step":null,"first_error_line":null,"duration_seconds":%d,"snapshot_at":"%s"}\n' \
            "$repo" "$pull_sha" "$duration_seconds" "$snapshot_at" > "$result_file"
    else
        # Extract the last STEP marker seen (pattern: "STEP N.N" or "[STEP N.N]").
        # Use `rg --pcre2` not `grep -oP` — macOS BSD grep has no `-P` (ci_local_qg_parity
        # 2026-06-10), which would silently make this report "unknown" on every macOS slot.
        local failing_step first_error
        failing_step="$(rg --pcre2 -o '(STEP\s+\d+\.\d+|\[\d+\.\d+\])' "$log_file" 2>/dev/null | tail -1 || echo "unknown")"
        # First line containing ERROR/FAILED/error: (capped to 200 chars, escaped for JSON)
        first_error="$(grep -m1 -iE 'error|FAILED' "$log_file" 2>/dev/null | head -c 200 | \
            python3 -c "import sys,json; print(json.dumps(sys.stdin.read().strip()))" 2>/dev/null || echo '""')"
        printf '{"repo":"%s","qg_status":"red","pull_sha":"%s","failing_step":"%s","first_error_line":%s,"duration_seconds":%d,"snapshot_at":"%s"}\n' \
            "$repo" "$pull_sha" "$failing_step" "$first_error" "$duration_seconds" "$snapshot_at" > "$result_file"
    fi
}

export -f run_one_repo

# Run in parallel (xargs -P N)
echo "$REPOS" | xargs -P "$PARALLEL" -I{} bash -c \
    'run_one_repo "$@"' _ {} "$WORKSPACE_ROOT" "$SNAPSHOT_AT" "$RUN_DIR"

# Collect + emit results in deterministic repo order
TOTAL=0; GREEN=0; RED=0; SKIPPED=0
while IFS= read -r repo; do
    result_file="$RUN_DIR/result-${repo}.json"
    if [[ -f "$result_file" ]]; then
        cat "$result_file"
        status="$(python3 -c "import json,sys; print(json.load(open('$result_file'))['qg_status'])" 2>/dev/null || echo "unknown")"
        ((TOTAL++)) || true
        case "$status" in green) ((GREEN++)) || true ;; red) ((RED++)) || true ;; *) ((SKIPPED++)) || true ;; esac
    fi
done <<< "$REPOS"

echo "QG snapshot complete: total=$TOTAL green=$GREEN red=$RED skipped=$SKIPPED" >&2
