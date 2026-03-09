#!/usr/bin/env bash
# run-all-setup.sh — Run setup.sh in all repos (topological tier order, parallel within tier)
#
# Repos within the same manifest tier have no mutual dependencies and run in parallel.
# Each tier waits for all repos in the previous tier to complete before starting the next.
#
# Run AFTER version alignment (run-version-alignment.sh) succeeds.
# SSOT: unified-trading-pm/scripts/repo-management/run-all-setup.sh
#
# Usage:
#   bash unified-trading-pm/scripts/repo-management/run-all-setup.sh
#   bash unified-trading-pm/scripts/repo-management/run-all-setup.sh --check         # verify only, no install
#   bash unified-trading-pm/scripts/repo-management/run-all-setup.sh --rollout-first # propagate templates first
#
# Run from workspace root (parent of unified-trading-pm):
#   cd /path/to/unified-trading-system-repos
#   bash unified-trading-pm/scripts/repo-management/run-all-setup.sh

set -uo pipefail  # no -e: background job exit codes collected via wait

CHECK_ONLY=false
ROLLOUT_FIRST=false
for arg in "$@"; do
  case $arg in
    --check) CHECK_ONLY=true ;;
    --rollout-first) ROLLOUT_FIRST=true ;;
    --help | -h)
      echo "Usage: bash run-all-setup.sh [--check] [--rollout-first]"
      echo "  --check         Run setup.sh --check only (verify, no install)"
      echo "  --rollout-first Propagate setup.sh + quality-gates.sh templates first"
      echo ""
      echo "Run from workspace root (parent of unified-trading-pm):"
      echo "  cd /path/to/unified-trading-system-repos"
      echo "  bash unified-trading-pm/scripts/repo-management/run-all-setup.sh"
      exit 0
      ;;
  esac
done

# ── Resolve workspace root ────────────────────────────────────────────────────
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

# Prefer workspace venv python; fall back to python3
PYTHON="$WORKSPACE_ROOT/.venv-workspace/bin/python3"
[ -x "$PYTHON" ] || PYTHON="python3"

# ── Optional: propagate templates first ──────────────────────────────────────
if [ "$ROLLOUT_FIRST" = true ]; then
  echo "━━━ Phase 0: Rollout templates (setup.sh + quality-gates.sh) ━━━"
  "$PYTHON" "$WORKSPACE_ROOT/unified-trading-pm/scripts/propagation/rollout-quality-gates-unified.py" || exit 1
  echo ""
fi

echo "━━━ Run setup in all repos (topological tier order, parallel within tier) ━━━"
echo "  Workspace: $WORKSPACE_ROOT"
echo "  Mode: $([ "$CHECK_ONLY" = true ] && echo 'CHECK' || echo 'INSTALL')"
echo ""

# ── Parse manifest into "LEVEL:repo1 repo2 ..." lines ────────────────────────
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

OK=0
SKIP=0
FAIL=0
FAILED_REPOS=()

# ── Process tier by tier; repos within a tier run in parallel ─────────────────
while IFS=: read -r LEVEL REPOS_STR; do
  # shellcheck disable=SC2206
  ALL_REPOS=($REPOS_STR)

  # Pre-filter: skip missing dirs / repos without setup.sh before forking
  RUNNABLE=()
  for repo in "${ALL_REPOS[@]}"; do
    rp="$WORKSPACE_ROOT/$repo"
    if [ ! -d "$rp" ] || [ ! -f "$rp/scripts/setup.sh" ]; then
      echo "  [SKIP] $repo"
      SKIP=$((SKIP + 1))
    else
      RUNNABLE+=("$repo")
    fi
  done

  [ ${#RUNNABLE[@]} -eq 0 ] && continue

  echo "  ── Tier $LEVEL (${#RUNNABLE[@]} repo(s) in parallel) ──"

  # Launch all runnable repos in this tier as background jobs
  PIDS=()
  LAUNCHED=()
  for repo in "${RUNNABLE[@]}"; do
    rp="$WORKSPACE_ROOT/$repo"
    log=$(mktemp)
    (
      setup_cmd="bash scripts/setup.sh"
      [ "$CHECK_ONLY" = true ] && setup_cmd="bash scripts/setup.sh --check"
      if (cd "$rp" && WORKSPACE_ROOT="$WORKSPACE_ROOT" $setup_cmd 2>&1) >"$log"; then
        echo "  [OK]   $repo"
        rm -f "$log"
        exit 0
      else
        echo "  [FAIL] $repo"
        echo "    --- output ---"
        tail -30 "$log" | sed 's/^/    /'
        echo "    ---"
        rm -f "$log"
        exit 1
      fi
    ) &
    PIDS+=($!)
    LAUNCHED+=("$repo")
  done

  # Wait for all jobs in this tier and tally results
  TIER_FAIL=0
  for i in "${!PIDS[@]}"; do
    if wait "${PIDS[$i]}"; then
      OK=$((OK + 1))
    else
      FAIL=$((FAIL + 1))
      TIER_FAIL=$((TIER_FAIL + 1))
      FAILED_REPOS+=("${LAUNCHED[$i]}")
    fi
  done

  [ "$TIER_FAIL" -gt 0 ] && echo "  Tier $LEVEL: $TIER_FAIL failure(s)"
  echo ""

done <<< "$LEVEL_DATA"

# ── Summary ───────────────────────────────────────────────────────────────────
echo "  OK: $OK | Skipped: $SKIP | Failed: $FAIL"
if [ ${#FAILED_REPOS[@]} -gt 0 ]; then
  echo ""
  echo "  Failed repos:"
  for r in "${FAILED_REPOS[@]}"; do
    echo "    - $r"
  done
fi

[ "$FAIL" -eq 0 ]
