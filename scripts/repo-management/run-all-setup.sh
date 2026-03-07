#!/usr/bin/env bash
# run-all-setup.sh — Run setup.sh in all repos (dependency order)
#
# Run AFTER version alignment (run-version-alignment.sh) succeeds.
# SSOT: unified-trading-pm/scripts/repo-management/run-all-setup.sh
#
# Usage:
#   bash unified-trading-pm/scripts/repo-management/run-all-setup.sh
#   bash unified-trading-pm/scripts/repo-management/run-all-setup.sh --check  # verify only
#   bash unified-trading-pm/scripts/repo-management/run-all-setup.sh --rollout-first  # propagate templates first
#
# Prerequisites:
#   - Version alignment complete (no conflicts)
#   - Run from workspace root (parent of unified-trading-pm)
#
# Run from workspace root:
#   cd /path/to/unified-trading-system-repos
#   bash unified-trading-pm/scripts/repo-management/run-all-setup.sh

set -euo pipefail

CHECK_ONLY=false
ROLLOUT_FIRST=false
for arg in "$@"; do
  case $arg in
    --check) CHECK_ONLY=true ;;
    --rollout-first) ROLLOUT_FIRST=true ;;
    --help | -h)
      echo "Usage: bash run-all-setup.sh [--check] [--rollout-first]"
      echo "  --check         Run setup.sh --check only (verify, no install)"
      echo "  --rollout-first Run rollout-quality-gates-unified.py first (propagate setup.sh + quality-gates.sh)"
      echo ""
      echo "Run from workspace root (parent of unified-trading-pm):"
      echo "  cd /path/to/unified-trading-system-repos"
      echo "  bash unified-trading-pm/scripts/repo-management/run-all-setup.sh"
      exit 0
      ;;
  esac
done

# Resolve workspace root from cwd (must run from workspace root)
if [ -f "$(pwd)/unified-trading-pm/workspace-manifest.json" ]; then
  WORKSPACE_ROOT="$(pwd)"
elif [ -f "$(pwd)/workspace-manifest.json" ]; then
  WORKSPACE_ROOT="$(cd .. && pwd)"
else
  echo "Error: Run from workspace root. Expected unified-trading-pm/workspace-manifest.json"
  echo "  cd /path/to/unified-trading-system-repos"
  echo "  bash unified-trading-pm/scripts/repo-management/run-all-setup.sh"
  exit 1
fi
MANIFEST="$WORKSPACE_ROOT/unified-trading-pm/workspace-manifest.json"

# Optional: propagate setup.sh + quality-gates.sh to all repos first
if [ "$ROLLOUT_FIRST" = true ]; then
  echo "━━━ Phase 0: Rollout templates (setup.sh + quality-gates.sh) ━━━"
  python3.13 "$WORKSPACE_ROOT/unified-trading-pm/scripts/propagation/rollout-quality-gates-unified.py" || exit 1
  echo ""
fi

echo "━━━ Run setup in all repos (topological order) ━━━"
echo "  Workspace: $WORKSPACE_ROOT"
echo "  Mode: $([ "$CHECK_ONLY" = true ] && echo 'CHECK' || echo 'INSTALL')"
echo ""

# Topological order from manifest
ORDERED_REPOS=$(python3.13 -c "
import json
with open('$MANIFEST') as f:
    data = json.load(f)
topo = data.get('topologicalOrder', {}).get('levels', [])
for level in sorted(topo, key=lambda l: l.get('level', 999)):
    for repo in level.get('repos', []):
        print(repo)
" 2>/dev/null)

OK=0
SKIP=0
FAIL=0
FAILED_REPOS=()

for repo in $ORDERED_REPOS; do
  REPO_PATH="$WORKSPACE_ROOT/$repo"
  if [ ! -d "$REPO_PATH" ]; then
    continue
  fi

  if [ ! -f "$REPO_PATH/scripts/setup.sh" ]; then
    echo "  [SKIP] $repo (no setup.sh)"
    SKIP=$((SKIP + 1))
    continue
  fi

  echo -n "  $repo ... "
  SETUP_LOG=$(mktemp)
  if [ "$CHECK_ONLY" = true ]; then
    if (cd "$REPO_PATH" && WORKSPACE_ROOT="$WORKSPACE_ROOT" bash scripts/setup.sh --check 2>&1) >"$SETUP_LOG"; then
      echo "OK"
      OK=$((OK + 1))
    else
      echo "FAIL"
      FAIL=$((FAIL + 1))
      FAILED_REPOS+=("$repo")
      echo "    --- output ---"
      tail -30 "$SETUP_LOG" | sed 's/^/    /'
      echo "    ---"
    fi
  else
    if (cd "$REPO_PATH" && WORKSPACE_ROOT="$WORKSPACE_ROOT" bash scripts/setup.sh 2>&1) >"$SETUP_LOG"; then
      echo "OK"
      OK=$((OK + 1))
    else
      echo "FAIL"
      FAIL=$((FAIL + 1))
      FAILED_REPOS+=("$repo")
      echo "    --- output ---"
      tail -30 "$SETUP_LOG" | sed 's/^/    /'
      echo "    ---"
    fi
  fi
  rm -f "$SETUP_LOG"
done

echo ""
echo "  OK: $OK | Skipped: $SKIP | Failed: $FAIL"
if [ ${#FAILED_REPOS[@]} -gt 0 ]; then
  echo ""
  echo "  Failed repos:"
  for r in "${FAILED_REPOS[@]}"; do
    echo "  - $r"
  done
fi
[ "$FAIL" -eq 0 ]
