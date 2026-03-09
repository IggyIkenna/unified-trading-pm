#!/usr/bin/env bash
# run-all-quality-gates.sh — Run quality gates in all repos (topological order, parallel within tier)
#
# SSOT: workspace-manifest.json topologicalOrder
# Python repos: bash scripts/quality-gates.sh --no-fix
# UI repos: npm run typecheck && npm run lint && npm run build
# Codex: skip (docs-only, no QG)
#
# Usage:
#   bash unified-trading-pm/scripts/repo-management/run-all-quality-gates.sh
#   bash unified-trading-pm/scripts/repo-management/run-all-quality-gates.sh --sequential  # one at a time
#
# Run from workspace root:
#   cd /path/to/unified-trading-system-repos
#   bash unified-trading-pm/scripts/repo-management/run-all-quality-gates.sh

set -uo pipefail

SEQUENTIAL=false
for arg in "$@"; do
  case $arg in
    --sequential) SEQUENTIAL=true ;;
    --help | -h)
      echo "Usage: bash run-all-quality-gates.sh [--sequential]"
      echo "  --sequential  Run one repo at a time (default: parallel within tier)"
      exit 0
      ;;
  esac
done

# Resolve workspace root
if [ -f "$(pwd)/unified-trading-pm/workspace-manifest.json" ]; then
  WORKSPACE_ROOT="$(pwd)"
elif [ -f "$(pwd)/workspace-manifest.json" ]; then
  WORKSPACE_ROOT="$(cd .. && pwd)"
else
  echo "Error: Run from workspace root. Expected unified-trading-pm/workspace-manifest.json"
  exit 1
fi
MANIFEST="$WORKSPACE_ROOT/unified-trading-pm/workspace-manifest.json"
PYTHON="${WORKSPACE_ROOT}/.venv-workspace/bin/python3"
[ -x "$PYTHON" ] || PYTHON="python3"

# Parse topological order
LEVEL_DATA=$("$PYTHON" -c "
import json
with open('$MANIFEST') as f:
    data = json.load(f)
topo = data.get('topologicalOrder', {}).get('levels', [])
for level in sorted(topo, key=lambda l: l.get('level', 999)):
    lvl = level.get('level', '?')
    repos = ' '.join(level.get('repos', []))
    if repos:
        print(f'{lvl}:{repos}')
" 2>/dev/null)

if [ -z "$LEVEL_DATA" ]; then
  echo "Error: Could not parse topological order from $MANIFEST"
  exit 1
fi

echo "━━━ Run quality gates in topological order ━━━"
echo "  Workspace: $WORKSPACE_ROOT"
echo "  Mode: $([ "$SEQUENTIAL" = true ] && echo 'SEQUENTIAL' || echo 'PARALLEL within tier')"
echo ""

OK=0
SKIP=0
FAIL=0
FAILED_REPOS=()

run_qg() {
  local repo="$1"
  local rp="$WORKSPACE_ROOT/$repo"
  local log="$2"
  if [ -f "$rp/scripts/quality-gates.sh" ]; then
    (cd "$rp" && WORKSPACE_ROOT="$WORKSPACE_ROOT" UNIFIED_TRADING_WORKSPACE_ROOT="${UNIFIED_TRADING_WORKSPACE_ROOT:-$WORKSPACE_ROOT}" bash scripts/quality-gates.sh --no-fix 2>&1) < /dev/null >"$log"
    return $?
  elif [ -f "$rp/package.json" ]; then
    (cd "$rp" && npm run typecheck 2>&1 && npm run lint 2>&1 && npm run build 2>&1) < /dev/null >"$log"
    return $?
  else
    return 0
  fi
}

while IFS=: read -r LEVEL REPOS_STR; do
  ALL_REPOS=($REPOS_STR)
  RUNNABLE=()
  for repo in "${ALL_REPOS[@]}"; do
    rp="$WORKSPACE_ROOT/$repo"
    if [ ! -d "$rp" ]; then
      echo "  [SKIP] $repo (not found)"
      SKIP=$((SKIP + 1))
    elif [ "$repo" = "unified-trading-codex" ]; then
      echo "  [SKIP] $repo (docs-only, no QG)"
      SKIP=$((SKIP + 1))
    else
      RUNNABLE+=("$repo")
    fi
  done

  [ ${#RUNNABLE[@]} -eq 0 ] && continue

  echo "  ── Tier L$LEVEL (${#RUNNABLE[@]} repo(s)) ──"

  if [ "$SEQUENTIAL" = true ]; then
    for repo in "${RUNNABLE[@]}"; do
      rp="$WORKSPACE_ROOT/$repo"
      log=$(mktemp)
      if run_qg "$repo" "$log"; then
        echo "  [OK]   $repo"
        OK=$((OK + 1))
      else
        echo "  [FAIL] $repo"
        tail -25 "$log" | sed 's/^/    /'
        FAIL=$((FAIL + 1))
        FAILED_REPOS+=("$repo")
      fi
      rm -f "$log"
    done
  else
    PIDS=()
    LAUNCHED=()
    LOGS=()
    for repo in "${RUNNABLE[@]}"; do
      log=$(mktemp)
      LOGS+=("$log")
      (
        if run_qg "$repo" "$log"; then
          echo "  [OK]   $repo"
          exit 0
        else
          echo "  [FAIL] $repo"
          tail -15 "$log" | sed 's/^/    /'
          exit 1
        fi
      ) &
      PIDS+=($!)
      LAUNCHED+=("$repo")
    done
    for i in "${!PIDS[@]}"; do
      if wait "${PIDS[$i]}"; then
        OK=$((OK + 1))
      else
        FAIL=$((FAIL + 1))
        FAILED_REPOS+=("${LAUNCHED[$i]}")
      fi
    done
    for log in "${LOGS[@]}"; do rm -f "$log"; done
  fi
  echo ""
done <<< "$LEVEL_DATA"

echo "━━━ Summary ━━━"
echo "  OK: $OK | Skipped: $SKIP | Failed: $FAIL"
if [ ${#FAILED_REPOS[@]} -gt 0 ]; then
  echo ""
  echo "  Failed repos:"
  for r in "${FAILED_REPOS[@]}"; do
    echo "    - $r"
  done
fi

[ "$FAIL" -eq 0 ]
