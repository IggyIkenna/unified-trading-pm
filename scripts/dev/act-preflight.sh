#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# act-preflight.sh — wraps `act` invocation against a repo's quality-gates.yml workflow
# so developers can validate CI locally before pushing.
#
# Phase 2 P0 of deployment_and_qg_strategy_implementation_2026_05_13.md.
#
# Usage:
#   bash unified-trading-pm/scripts/dev/act-preflight.sh --repo <name>
#   bash unified-trading-pm/scripts/dev/act-preflight.sh --repo deployment-api --workflow workspace-qg.yml
#   bash unified-trading-pm/scripts/dev/act-preflight.sh --repo all              # iterate every service repo
#
# Defaults:
#   --workflow      quality-gates-v2.yml
#   --architecture  linux/amd64
#   --image         catthehacker/ubuntu:act-22.04 (pinned via .actrc per-repo if present)
#
# Output: /tmp/act-preflight-{repo}-{sha}.log + EXIT_CODE summary to stdout.
#
# Pre-reqs: `act` installed (https://github.com/nektos/act) + docker daemon running.

set -euo pipefail

REPO=""
WORKFLOW="quality-gates-v2.yml"
ARCH="linux/amd64"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && cd .. && pwd)}"

usage() {
    cat <<EOF
Usage: $0 --repo <name|all> [--workflow <yml>] [--architecture <arch>]

  --repo <name>      Repo name (e.g. deployment-api) OR 'all' for every service repo
  --workflow <yml>   Workflow filename under .github/workflows/ (default: quality-gates-v2.yml)
  --architecture <a> Container architecture (default: linux/amd64)

Reports: per-repo {EXIT_CODE, log file path, duration}.
Exit code: 0 = all repos passed; 1 = ≥1 failed; 2 = arg / pre-flight error.
EOF
    exit 2
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --repo) REPO="$2"; shift 2 ;;
        --workflow) WORKFLOW="$2"; shift 2 ;;
        --architecture) ARCH="$2"; shift 2 ;;
        --help|-h) usage ;;
        *) echo "Unknown arg: $1" >&2; usage ;;
    esac
done

if [[ -z "$REPO" ]]; then
    echo "ERROR: --repo is required" >&2
    usage
fi

# Pre-flight: act + docker
if ! command -v act >/dev/null 2>&1; then
    echo "ERROR: 'act' not installed. Install: https://github.com/nektos/act" >&2
    exit 2
fi
if ! docker info >/dev/null 2>&1; then
    echo "ERROR: docker daemon not running" >&2
    exit 2
fi

# Resolve target repos
TARGET_REPOS=()
if [[ "$REPO" == "all" ]]; then
    for d in "$WORKSPACE_ROOT"/*/; do
        repo=$(basename "$d")
        # Skip non-Python repos + UI repos
        case "$repo" in
            unified-trading-system-ui|deployment-ui|user-management-ui) continue ;;
            unified-trading-pm) continue ;;  # PM has different QG semantics
        esac
        if [[ -f "$d/.github/workflows/$WORKFLOW" ]]; then
            TARGET_REPOS+=("$repo")
        fi
    done
    if [[ ${#TARGET_REPOS[@]} -eq 0 ]]; then
        echo "ERROR: --repo all resolved 0 target repos for workflow '$WORKFLOW' under $WORKSPACE_ROOT" >&2
        echo "       (check --workflow matches an actual .github/workflows/ filename before trusting a green exit)" >&2
        exit 2
    fi
else
    if [[ ! -d "$WORKSPACE_ROOT/$REPO" ]]; then
        echo "ERROR: repo not found at $WORKSPACE_ROOT/$REPO" >&2
        exit 2
    fi
    if [[ ! -f "$WORKSPACE_ROOT/$REPO/.github/workflows/$WORKFLOW" ]]; then
        echo "ERROR: workflow not found at $WORKSPACE_ROOT/$REPO/.github/workflows/$WORKFLOW" >&2
        exit 2
    fi
    TARGET_REPOS=("$REPO")
fi

echo "=== act-preflight ==="
echo "Workspace: $WORKSPACE_ROOT"
echo "Workflow:  $WORKFLOW"
echo "Arch:      $ARCH"
echo "Targets:   ${#TARGET_REPOS[@]} repo(s): ${TARGET_REPOS[*]}"
echo ""

OVERALL_EXIT=0
SUMMARY=()

for repo in "${TARGET_REPOS[@]}"; do
    repo_path="$WORKSPACE_ROOT/$repo"
    sha=$(cd "$repo_path" && git rev-parse --short HEAD 2>/dev/null || echo "nogit")
    log_file="/tmp/act-preflight-${repo}-${sha}.log"

    echo "--- $repo (@$sha) ---"
    echo "  workflow: $WORKFLOW"
    echo "  log:      $log_file"

    start_ts=$(date +%s)
    set +e
    (cd "$repo_path" && act -W ".github/workflows/$WORKFLOW" --container-architecture "$ARCH") > "$log_file" 2>&1
    exit_code=$?
    set -e
    duration=$(( $(date +%s) - start_ts ))

    if [[ $exit_code -eq 0 ]]; then
        echo "  ✅ PASS in ${duration}s"
    else
        echo "  ❌ FAIL exit=$exit_code in ${duration}s (see $log_file)"
        OVERALL_EXIT=1
    fi
    SUMMARY+=("$repo: exit=$exit_code, ${duration}s, $log_file")
done

echo ""
echo "=== Summary ==="
for line in "${SUMMARY[@]}"; do
    echo "  $line"
done

exit $OVERALL_EXIT
