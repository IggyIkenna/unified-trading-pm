#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
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
#   bash unified-trading-pm/scripts/repo-management/run-all-setup.sh --check              # verify only, no install
#   bash unified-trading-pm/scripts/repo-management/run-all-setup.sh --rollout-first      # propagate templates first
#   bash unified-trading-pm/scripts/repo-management/run-all-setup.sh --sync-git           # fetch + report drift vs active_feature_branch (from manifest)
#   bash unified-trading-pm/scripts/repo-management/run-all-setup.sh --sync-git=main      # fetch + report drift vs origin/main
#   bash unified-trading-pm/scripts/repo-management/run-all-setup.sh --sync-git=staging   # fetch + report drift vs origin/staging
#   bash unified-trading-pm/scripts/repo-management/run-all-setup.sh --repos=unified-features-interface,market-tick-data-service
#   bash unified-trading-pm/scripts/repo-management/run-all-setup.sh --repos=unified-features-interface --force
#
# Run from workspace root (parent of unified-trading-pm):
#   cd /path/to/unified-trading-system-repos
#   bash unified-trading-pm/scripts/repo-management/run-all-setup.sh

set -uo pipefail  # no -e: background job exit codes collected via wait

CHECK_ONLY=false
ROLLOUT_FIRST=false
SYNC_GIT=false
SYNC_GIT_BRANCH=""
FORCE=false
REPO_FILTER=""
for arg in "$@"; do
  case $arg in
    --check) CHECK_ONLY=true ;;
    --rollout-first) ROLLOUT_FIRST=true ;;
    --force) FORCE=true ;;
    --sync-git) SYNC_GIT=true ;;
    --sync-git=*) SYNC_GIT=true; SYNC_GIT_BRANCH="${arg#--sync-git=}" ;;
    --repos=*) REPO_FILTER="${arg#--repos=}" ;;
    --help | -h)
      echo "Usage: bash run-all-setup.sh [--check] [--rollout-first] [--force] [--sync-git[=BRANCH]] [--repos=REPO1,REPO2,...]"
      echo "  --check              Run setup.sh --check only (verify, no install)"
      echo "  --rollout-first      Propagate setup.sh + quality-gates.sh + quickmerge.sh + build infra first"
      echo "                       Rollout failures are non-fatal — setup continues with warnings"
      echo "  --force              Force reinstall: wipe and recreate each repo's .venv from scratch"
      echo "                       Passes --force to each repo's setup.sh. Use on fresh machines or"
      echo "                       after dependency changes to ensure a clean, reproducible environment."
      echo "  --sync-git[=BRANCH]  git fetch all repos, then report drift against a reference branch"
      echo "                       BRANCH: main | staging | feature (default) | any-branch-name"
      echo "                       'feature' (default) reads active_feature_branch from workspace-manifest.json"
      echo "                       Never merges — read-only. Useful on new machines to see stale repos."
      echo "  --repos=REPO1,REPO2  Only run setup for the listed repos (comma-separated)."
      echo "                       Tier ordering is preserved — filtered repos still run in correct tier order."
      echo "                       Example: --repos=unified-features-interface,market-tick-data-service"
      echo ""
      echo "Run from workspace root (parent of unified-trading-pm):"
      echo "  cd /path/to/unified-trading-system-repos"
      echo "  bash unified-trading-pm/scripts/repo-management/run-all-setup.sh"
      exit 0
      ;;
  esac
done

# Parse --repos filter into a comma-delimited string for simple matching
# Format: ",repo1,repo2,repo3," — leading/trailing commas enable substring match
REPO_FILTER_STR=""
REPO_FILTER_COUNT=0
if [ -n "$REPO_FILTER" ]; then
  REPO_FILTER_STR=",$REPO_FILTER,"
  IFS=',' read -ra _FILTER_REPOS <<< "$REPO_FILTER"
  REPO_FILTER_COUNT=${#_FILTER_REPOS[@]}
fi

_in_repo_filter() {
  [ -z "$REPO_FILTER_STR" ] && return 0  # no filter = accept all
  [[ "$REPO_FILTER_STR" == *",$1,"* ]]
}

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

# Use system python3 for manifest JSON parsing (no workspace venv dependency)
PYTHON="python3"

# ── Pre-flight checks ─────────────────────────────────────────────────────────
echo "━━━ Pre-flight checks ━━━"
PREFLIGHT_WARN=false

# Warn if UV_PYTHON_DOWNLOADS is not set to "never" (guards against uv auto-downloading Python)
if [ "${UV_PYTHON_DOWNLOADS:-}" = "never" ]; then
  echo "  [OK]   UV_PYTHON_DOWNLOADS=never"
else
  echo "  [WARN] UV_PYTHON_DOWNLOADS is not 'never' (current: '${UV_PYTHON_DOWNLOADS:-unset}')"
  echo "         Without this, uv may auto-download CPython and venvs break when that cache is wiped."
  echo "         Add to ~/.bashrc (Linux) or ~/.zshrc (macOS): export UV_PYTHON_DOWNLOADS=never"
  PREFLIGHT_WARN=true
fi

[ "$PREFLIGHT_WARN" = true ] && echo ""
echo ""

# ── Optional: git fetch + drift report (read-only, no merge) ─────────────────
if [ "$SYNC_GIT" = true ]; then
  echo "━━━ git fetch (all repos, parallel) ━━━"
  # Collect all repo dirs that have a .git directory
  FETCH_REPOS=()
  for d in "$WORKSPACE_ROOT"/*/; do
    [ -d "$d/.git" ] && FETCH_REPOS+=("$d")
  done
  echo "  Fetching ${#FETCH_REPOS[@]} repos..."

  # Fetch in parallel, suppress output; record failures
  FETCH_PIDS=()
  for rp in "${FETCH_REPOS[@]}"; do
    (git -C "$rp" fetch origin --quiet 2>/dev/null) &
    FETCH_PIDS+=($!)
  done
  FETCH_FAIL=0
  for i in "${!FETCH_PIDS[@]}"; do
    wait "${FETCH_PIDS[$i]}" || FETCH_FAIL=$((FETCH_FAIL + 1))
  done
  [ "$FETCH_FAIL" -gt 0 ] && echo "  [WARN] $FETCH_FAIL repo(s) could not fetch (no remote / network issue)"

  # Resolve the reference branch to compare against
  if [ -z "$SYNC_GIT_BRANCH" ] || [ "$SYNC_GIT_BRANCH" = "feature" ]; then
    # Default: active_feature_branch from manifest (same SSOT as quickmerge)
    SYNC_TARGET=$(python3 -c \
      "import json; m=json.load(open('$MANIFEST')); print(m.get('active_feature_branch','main'))" \
      2>/dev/null || echo "main")
    echo "  Branch: origin/$SYNC_TARGET (active_feature_branch from manifest)"
  else
    SYNC_TARGET="$SYNC_GIT_BRANCH"
    echo "  Branch: origin/$SYNC_TARGET"
  fi

  # Report which repos are behind/diverged relative to origin/$SYNC_TARGET
  BEHIND=()
  for rp in "${FETCH_REPOS[@]}"; do
    repo_name="$(basename "$rp")"
    branch=$(git -C "$rp" symbolic-ref --short HEAD 2>/dev/null || true)
    [ -z "$branch" ] && continue
    remote_ref="origin/$SYNC_TARGET"
    if ! git -C "$rp" rev-parse --verify "$remote_ref" &>/dev/null; then
      BEHIND+=("  $repo_name ($branch): origin/$SYNC_TARGET not found — branch may not exist in this repo")
      continue
    fi
    behind=$(git -C "$rp" rev-list --count "HEAD..${remote_ref}" 2>/dev/null || echo 0)
    ahead=$(git -C "$rp"  rev-list --count "${remote_ref}..HEAD" 2>/dev/null || echo 0)
    if [ "$behind" -gt 0 ] && [ "$ahead" -eq 0 ]; then
      BEHIND+=("  $repo_name ($branch): $behind commit(s) behind origin/$SYNC_TARGET — run: cd $repo_name && git pull --ff-only origin $SYNC_TARGET")
    elif [ "$behind" -gt 0 ] && [ "$ahead" -gt 0 ]; then
      BEHIND+=("  $repo_name ($branch): diverged — $behind behind / $ahead ahead of origin/$SYNC_TARGET (manual merge needed)")
    fi
  done

  if [ "${#BEHIND[@]}" -gt 0 ]; then
    echo ""
    echo "  [WARN] Repos with drift from origin/$SYNC_TARGET (${#BEHIND[@]}):"
    for b in "${BEHIND[@]}"; do echo "$b"; done
    echo ""
    echo "  Note: setup will continue with current local state — pull manually if needed."
  else
    echo "  [OK] All repos are up to date with origin/$SYNC_TARGET"
  fi
  echo ""
fi

# ── Optional: propagate templates first ──────────────────────────────────────
ROLLOUT_WARNINGS=()
if [ "$ROLLOUT_FIRST" = true ]; then
  echo "━━━ Phase 0: Rollout templates (setup.sh + quality-gates.sh + quickmerge.sh + build infra) ━━━"
  "$PYTHON" "$WORKSPACE_ROOT/unified-trading-pm/scripts/propagation/rollout-quality-gates-unified.py" --skip-missing \
    || ROLLOUT_WARNINGS+=("rollout-quality-gates-unified.py (non-fatal — templates may be stale in some repos)")
  "$PYTHON" "$WORKSPACE_ROOT/unified-trading-pm/scripts/propagation/rollout-quickmerge.py" \
    || ROLLOUT_WARNINGS+=("rollout-quickmerge.py (non-fatal — quickmerge.sh may be stale in some repos)")
  "$PYTHON" "$WORKSPACE_ROOT/unified-trading-pm/scripts/propagation/rollout-ui-build-infra.py" \
    || ROLLOUT_WARNINGS+=("rollout-ui-build-infra.py (non-fatal — UI build infra may be stale in some repos)")
  if [ "${#ROLLOUT_WARNINGS[@]}" -gt 0 ]; then
    echo ""
    echo "  [WARN] Phase 0 rollout had non-fatal failures:"
    for w in "${ROLLOUT_WARNINGS[@]}"; do echo "    - $w"; done
    echo "  Setup will continue. Re-run with --rollout-first after fixing the above."
  fi
  echo ""
fi

echo "━━━ Run setup in all repos (topological tier order, parallel within tier) ━━━"
echo "  Workspace: $WORKSPACE_ROOT"
echo "  Mode: $([ "$CHECK_ONLY" = true ] && echo 'CHECK' || ([ "$FORCE" = true ] && echo 'FORCE REINSTALL' || echo 'INSTALL'))"
[ -n "$REPO_FILTER_STR" ] && echo "  Filter: $REPO_FILTER ($REPO_FILTER_COUNT repo(s))"
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

  # Pre-filter: skip missing dirs / repos without setup.sh / repos not in --repos filter
  RUNNABLE=()
  for repo in "${ALL_REPOS[@]}"; do
    # If --repos filter is set, skip repos not in the filter
    if ! _in_repo_filter "$repo"; then
      continue
    fi
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
      [ "$FORCE" = true ] && setup_cmd="bash scripts/setup.sh --force"
      if (cd "$rp" && WORKSPACE_ROOT="$WORKSPACE_ROOT" $setup_cmd 2>&1) >"$log"; then
        echo "  [OK]   $repo"
        rm -f "$log"
        exit 0
      else
        echo "  [FAIL] $repo"
        echo "    --- output ---"
        cat "$log" | sed 's/^/    /'
        echo "    ---"
        rm -f "$log"
        exit 1
      fi
    ) </dev/null &
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
