#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Workspace Quickmerge Validation — run quickmerge --unit-only per repo in dependency order
#
# Reads workspace-manifest.json topologicalOrder; for each repo: run quickmerge --unit-only --no-pr.
# On failure: skip all repos that depend on the failed repo.
# Output: artifacts/quickmerge-matrix.json
#
# Usage: bash unified-trading-pm/scripts/validate-workspace-quickmerge.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MANIFEST="$WORKSPACE_ROOT/unified-trading-pm/workspace-manifest.json"
ARTIFACTS_DIR="$WORKSPACE_ROOT/unified-trading-pm/artifacts"
MATRIX_FILE="$ARTIFACTS_DIR/quickmerge-matrix.json"
DEP_BRANCH=""

# Parse --dep-branch (pass through to quickmerge when deps have local changes)
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dep-branch)
      DEP_BRANCH="$2"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

mkdir -p "$ARTIFACTS_DIR"

# This validator deliberately clones only workspace-manifest.json's topological levels[0:3]
# (a small canary subset — 4 of 26 manifest repos as of 2026-08-16) to keep the 6-hourly smoke
# check fast, never the full fleet. quickmerge.sh's own STAGE 1.5 dependency-alignment check
# requires every non-archived manifest repo on disk, so run unmodified here it reports a false
# "aligned: false" for every legitimately-uncloned fleet repo — indistinguishable from real PM
# dependency drift. QUICKMERGE_SKIP_DEP_ALIGNMENT is quickmerge.sh's opt-in escape hatch for
# exactly this partial-workspace case (2026-08-16 /ci-reconcile root-cause fix); nothing else
# in the fleet sets it, so real full-workspace ships are unaffected.
export QUICKMERGE_SKIP_DEP_ALIGNMENT=1

# Build topological order from manifest
get_sorted_repos() {
  jq -r '.topologicalOrder.levels[].repos[]' "$MANIFEST" 2>/dev/null || true
}

# Get repos that depend on $1 (from repositories.*.dependencies)
get_dependents() {
  local repo="$1"
  jq -r --arg r "$repo" '
    .repositories | to_entries[]
    | select(.value.dependencies[]?.name == $r)
    | .key
  ' "$MANIFEST" 2>/dev/null || true
}

# Check if repo exists in workspace
repo_exists() {
  [ -d "$WORKSPACE_ROOT/$1" ]
}

# Check if repo has quickmerge
has_quickmerge() {
  [ -f "$WORKSPACE_ROOT/$1/scripts/quickmerge.sh" ]
}

# Portable: temp file works on bash 3.2 (macOS) and 4+ (Linux) — no OS detection needed
RESULTS_FILE=$(mktemp)
trap "rm -f $RESULTS_FILE" EXIT

SORTED_REPOS=()
while IFS= read -r r; do
  [ -n "$r" ] && SORTED_REPOS+=("$r")
done < <(get_sorted_repos)

FAILED_REPOS=""
for repo in "${SORTED_REPOS[@]}"; do
  if [[ " $FAILED_REPOS " = *" $repo "* ]]; then
    echo "${repo}|SKIPPED|0|dependency failed" >> "$RESULTS_FILE"
    continue
  fi

  if ! repo_exists "$repo"; then
    echo "${repo}|SKIPPED|0|repo not in workspace" >> "$RESULTS_FILE"
    continue
  fi

  if ! has_quickmerge "$repo"; then
    echo "${repo}|SKIPPED|0|no scripts/quickmerge.sh" >> "$RESULTS_FILE"
    continue
  fi

  echo ""
  echo "=========================================="
  echo "[$repo] Running quickmerge --unit-only"
  echo "=========================================="
  # errexit disabled around this one call: under `set -e`, a non-zero subshell exit here
  # terminates the script immediately (before `ec=$?` is ever reached), skipping the
  # RESULTS_FILE write + dependent-skip cascade for every repo after the first failure.
  set +e
  if [ -n "$DEP_BRANCH" ]; then
    (cd "$WORKSPACE_ROOT/$repo" && bash scripts/quickmerge.sh "chore: workspace validation" --unit-only --dep-branch "$DEP_BRANCH" 2>&1)
  else
    (cd "$WORKSPACE_ROOT/$repo" && bash scripts/quickmerge.sh "chore: workspace validation" --unit-only 2>&1)
  fi
  ec=$?
  set -e
  if [ $ec -eq 0 ]; then
    echo "${repo}|PASS|0|" >> "$RESULTS_FILE"
  else
    echo "${repo}|FAIL|${ec:-1}|" >> "$RESULTS_FILE"
    FAILED_REPOS="$FAILED_REPOS $repo"
    while IFS= read -r dep; do
      [ -n "$dep" ] && FAILED_REPOS="$FAILED_REPOS $dep"
    done < <(get_dependents "$repo")
  fi
done

# Build JSON matrix from results
echo "{ \"repos\": [" > "$MATRIX_FILE"
first=true
while IFS='|' read -r repo status exit_code skipped_reason; do
  [ "$first" = true ] && first=false || echo -n "," >> "$MATRIX_FILE"
  echo "" >> "$MATRIX_FILE"
  reason_escaped=$(echo "$skipped_reason" | sed 's/"/\\"/g')
  printf '  { "repo": "%s", "status": "%s", "exit_code": %s, "skipped_reason": "%s" }' \
    "$repo" "$status" "${exit_code:-0}" "$reason_escaped" >> "$MATRIX_FILE"
done < "$RESULTS_FILE"
echo "" >> "$MATRIX_FILE"
echo "] }" >> "$MATRIX_FILE"

# Summary
echo ""
echo "=========================================="
echo "Workspace Quickmerge Validation Summary"
echo "=========================================="
PASS_CNT=0
FAIL_CNT=0
SKIP_CNT=0
while IFS='|' read -r repo status _; do
  case "$status" in
    PASS) PASS_CNT=$((PASS_CNT + 1)) ;;
    FAIL) FAIL_CNT=$((FAIL_CNT + 1)) ;;
    *) SKIP_CNT=$((SKIP_CNT + 1)) ;;
  esac
  echo "  $repo: $status"
done < "$RESULTS_FILE"
echo ""
echo "PASS: $PASS_CNT | FAIL: $FAIL_CNT | SKIPPED: $SKIP_CNT"
echo "Matrix: $MATRIX_FILE"

[ "$FAIL_CNT" -gt 0 ] && exit 1
exit 0
