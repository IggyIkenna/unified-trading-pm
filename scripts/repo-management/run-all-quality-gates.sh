#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# run-all-quality-gates.sh — Full pre-push validation pipeline
#
# Runs in order:
#   1. run-version-alignment.sh  — check dep alignment across all pyproject.toml
#   2. run-all-setup.sh --check  — verify all repos have deps installed
#   3. quality-gates.sh --no-fix — topological tier order, parallel within tier
#
# All repos:    bash scripts/quality-gates.sh --no-fix (Python and UI)
# UI template:  unified-trading-pm/codex/06-coding-standards/quality-gates-ui-template.sh
# Codex:        skip (docs-only, no QG)
# SSOT:         workspace-manifest.json topologicalOrder
#
# Usage:
#   bash unified-trading-pm/scripts/repo-management/run-all-quality-gates.sh
#   bash unified-trading-pm/scripts/repo-management/run-all-quality-gates.sh --repo unified-cloud-interface
#   bash unified-trading-pm/scripts/repo-management/run-all-quality-gates.sh --repos "unified-cloud-interface unified-trading-library"
#   bash unified-trading-pm/scripts/repo-management/run-all-quality-gates.sh --skip-alignment --skip-setup
#   bash unified-trading-pm/scripts/repo-management/run-all-quality-gates.sh --sequential
#   bash unified-trading-pm/scripts/repo-management/run-all-quality-gates.sh --dry-run
#   bash unified-trading-pm/scripts/repo-management/run-all-quality-gates.sh --skip-typecheck
#   bash unified-trading-pm/scripts/repo-management/run-all-quality-gates.sh --lint
#
# Run from workspace root:
#   cd /path/to/unified-trading-system-repos
#   bash unified-trading-pm/scripts/repo-management/run-all-quality-gates.sh

set -uo pipefail  # no -e: background job exit codes collected via wait

# ── Resolve workspace root ────────────────────────────────────────────────────
if [ -f "$(pwd)/unified-trading-pm/workspace-manifest.json" ]; then
  WORKSPACE_ROOT="$(pwd)"
elif [ -f "$(pwd)/workspace-manifest.json" ]; then
  WORKSPACE_ROOT="$(cd .. && pwd)"
else
  echo "Error: Run from workspace root. Expected unified-trading-pm/workspace-manifest.json"
  echo "  cd /path/to/unified-trading-system-repos"
  echo "  bash unified-trading-pm/scripts/repo-management/run-all-quality-gates.sh"
  exit 1
fi
PM_ROOT="$WORKSPACE_ROOT/unified-trading-pm"
MANIFEST="$PM_ROOT/workspace-manifest.json"

PYTHON="$WORKSPACE_ROOT/.venv-workspace/bin/python3"
[ -x "$PYTHON" ] || PYTHON="python3"

# ── Parse arguments ───────────────────────────────────────────────────────────
SKIP_ALIGNMENT=false
SKIP_SETUP=false
SEQUENTIAL=false
DRY_RUN=false
SKIP_TYPECHECK=false
LINT_ONLY=false
TEST_ONLY=false
FROM_TIER=0
REPO_LIST=()  # empty = all repos

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-alignment)  SKIP_ALIGNMENT=true; shift ;;
    --skip-setup)      SKIP_SETUP=true; shift ;;
    --sequential)      SEQUENTIAL=true; shift ;;
    --dry-run)         DRY_RUN=true; shift ;;
    --skip-typecheck)  SKIP_TYPECHECK=true; shift ;;
    --lint)            LINT_ONLY=true; shift ;;
    --test)            TEST_ONLY=true; shift ;;
    --from-tier)       FROM_TIER="$2"; shift 2 ;;
    --repo)            REPO_LIST+=("$2"); shift 2 ;;
    --repos)           read -ra _r <<< "$2"; REPO_LIST+=("${_r[@]}"); shift 2 ;;
    --help | -h)
      echo "Usage: bash run-all-quality-gates.sh [options]"
      echo "  --repo NAME            Run QG for a single repo"
      echo "  --repos \"a b c\"        Run QG for a space-separated list of repos"
      echo "  --skip-alignment       Skip version alignment check"
      echo "  --skip-setup           Skip setup --check across all repos"
      echo "  --sequential           Run QG one repo at a time (default: parallel within tier)"
      echo "  --dry-run              Print what would run, do not execute"
      echo "  --skip-typecheck       Skip basedpyright type check (pass-through to quality-gates.sh)"
      echo "  --lint                 Run lint only, skip tests (pass-through to quality-gates.sh)"
      echo "  --test                 Run tests + typecheck only, skip lint (pass-through to quality-gates.sh)"
      echo "  --from-tier N         Run QG from tier N upwards (skip tiers 0..N-1)"
      exit 0
      ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

# Repo-filter mode: skip workspace-wide pre-flight steps
if [[ ${#REPO_LIST[@]} -gt 0 ]]; then
  SKIP_ALIGNMENT=true
  SKIP_SETUP=true
fi

echo "━━━ Pre-push validation pipeline ━━━"
echo "  Workspace: $WORKSPACE_ROOT"
[[ "$DRY_RUN" = true ]] && echo "  Mode: DRY-RUN"
echo ""

# ── Phase 1: Version alignment ────────────────────────────────────────────────
if [[ "$SKIP_ALIGNMENT" = false ]]; then
  echo "━━━ Phase 1: Version alignment ━━━"
  if [[ "$DRY_RUN" = true ]]; then
    echo "  [dry] bash unified-trading-pm/scripts/repo-management/run-version-alignment.sh"
  else
    bash "$PM_ROOT/scripts/repo-management/run-version-alignment.sh" || {
      echo ""
      echo "  FAILED. Fix: bash unified-trading-pm/scripts/repo-management/run-version-alignment.sh --fix"
      exit 1
    }
  fi
  echo ""
fi

# ── Phase 2: Setup check ──────────────────────────────────────────────────────
if [[ "$SKIP_SETUP" = false ]]; then
  echo "━━━ Phase 2: Setup check ━━━"
  if [[ "$DRY_RUN" = true ]]; then
    echo "  [dry] bash unified-trading-pm/scripts/repo-management/run-all-setup.sh --check"
  else
    bash "$PM_ROOT/scripts/repo-management/run-all-setup.sh" --check || {
      echo ""
      echo "  FAILED. Run: bash unified-trading-pm/scripts/repo-management/run-all-setup.sh"
      exit 1
    }
  fi
  echo ""
fi

# ── Phase 3: Quality gates (parallel within tier) ─────────────────────────────
echo "━━━ Phase 3: Quality gates ━━━"
echo "  Mode: $([ "$SEQUENTIAL" = true ] && echo 'SEQUENTIAL' || echo 'PARALLEL within tier')"
[[ "$SKIP_TYPECHECK" = true ]] && echo "  Typecheck: SKIPPED"
[[ "$LINT_ONLY" = true ]]      && echo "  Tests: SKIPPED (lint only)"
[[ "$TEST_ONLY" = true ]]      && echo "  Lint: SKIPPED (test only)"
[[ -n "${FROM_TIER:-}" ]]         && echo "  From tier: $FROM_TIER (skipping tiers 0..$((FROM_TIER-1)))"
echo ""

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

[ -z "$LEVEL_DATA" ] && { echo "Error: Could not parse topological order from $MANIFEST"; exit 1; }

is_codex_repo() { [[ "$(basename "$1")" == "unified-trading-codex" ]]; }

run_qg() {
  local repo="$1" rp="$WORKSPACE_ROOT/$1"
  # Per-slot worktrees (`.tabs/<N>/<repo>/`) carry `.git` as a FILE (git-worktree
  # link), not a directory — accept either shape so worktree-based slot QG
  # sweeps don't silently skip every repo. Reference: slot 3 codefreeze-audit
  # 2026-05-12 Day-4 finding (first run skipped 26/26 repos because of dir-only
  # check). Main-checkout `.git/` directory case keeps identical semantics.
  [[ ! -d "$rp/.git" && ! -f "$rp/.git" ]] && { echo "  [SKIP] $repo — not found"; return 0; }
  is_codex_repo "$rp"    && { echo "  [SKIP] $repo — docs-only"; return 0; }

  local log; log=$(mktemp)

  local qg_args=(--no-fix)
  [[ "$SKIP_TYPECHECK" = true ]] && qg_args+=(--skip-typecheck)
  [[ "$LINT_ONLY" = true ]]      && qg_args+=(--lint)
  [[ "$TEST_ONLY" = true ]]      && qg_args+=(--test)

  if [[ -f "$rp/scripts/quality-gates.sh" ]]; then
    if (cd "$rp" && WORKSPACE_ROOT="$WORKSPACE_ROOT" bash scripts/quality-gates.sh "${qg_args[@]}" 2>&1) >"$log" 2>&1; then
      # Extract coverage: pytest TOTAL line or vitest/istanbul "All files" line
      local cov_pct=""
      local cov_line; cov_line=$(grep -E '^TOTAL\s+[0-9]' "$log" | tail -1)
      if [[ -n "$cov_line" ]]; then
        cov_pct=$(echo "$cov_line" | awk '{print $NF}')
      else
        # vitest/istanbul: "All files | 85.71 | ..." — take first numeric column
        local js_line; js_line=$(grep -E '^\s*All files\s*\|' "$log" | tail -1)
        if [[ -n "$js_line" ]]; then
          cov_pct=$(echo "$js_line" | awk -F'|' '{gsub(/ /,"",$2); print $2"%"}')
        fi
      fi
      if [[ -n "$cov_pct" ]]; then
        echo "  [OK]   $repo  (coverage: $cov_pct)"
      else
        echo "  [OK]   $repo  (no cov)"
      fi
      rm -f "$log"; return 0
    fi
  else
    echo "  [SKIP] $repo — no quality-gates.sh (run rollout-quality-gates-unified.py)"; rm -f "$log"; return 0
  fi

  # On failure: show coverage line if present, then last 20 lines of output
  local cov_line; cov_line=$(grep -E '^TOTAL\s+[0-9]' "$log" | tail -1)
  if [[ -n "$cov_line" ]]; then
    local cov_pct; cov_pct=$(echo "$cov_line" | awk '{print $NF}')
    echo "  [FAIL] $repo  (coverage: $cov_pct)"
  else
    echo "  [FAIL] $repo"
  fi
  tail -20 "$log" | sed 's/^/    /'
  rm -f "$log"
  return 1
}

OK=0; FAIL=0; FAILED_REPOS=()

run_list() {
  local repos=("$@")
  if [[ "$SEQUENTIAL" = true ]] || [[ "$DRY_RUN" = true ]]; then
    for repo in "${repos[@]}"; do
      [[ "$DRY_RUN" = true ]] && { echo "  [dry]  $repo"; OK=$((OK+1)); continue; }
      if run_qg "$repo"; then OK=$((OK+1)); else FAIL=$((FAIL+1)); FAILED_REPOS+=("$repo"); fi
    done
  else
    PIDS=(); LAUNCHED=()
    for repo in "${repos[@]}"; do
      run_qg "$repo" </dev/null & PIDS+=($!); LAUNCHED+=("$repo")
    done
    for i in "${!PIDS[@]}"; do
      if wait "${PIDS[$i]}"; then OK=$((OK+1))
      else FAIL=$((FAIL+1)); FAILED_REPOS+=("${LAUNCHED[$i]}"); fi
    done
  fi
}

if [[ ${#REPO_LIST[@]} -gt 0 ]]; then
  # Explicit repo list — run directly, no tier structure
  echo "  ── ${#REPO_LIST[@]} repo(s) specified ──"
  run_list "${REPO_LIST[@]}"
  echo ""
else
  # Full workspace — tier-by-tier from manifest, parallel within tier
  while IFS=: read -r LEVEL REPOS_STR; do
    [[ -n "${FROM_TIER:-}" && "$LEVEL" -lt "$FROM_TIER" ]] && continue
    ALL_REPOS=($REPOS_STR)
    echo "  ── Tier $LEVEL (${#ALL_REPOS[@]} repo(s)$([ "$SEQUENTIAL" = false ] && echo ', parallel' || echo '')) ──"
    run_list "${ALL_REPOS[@]}"
    echo ""
  done <<< "$LEVEL_DATA"
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo "━━━ Results ━━━"
echo "  OK: $OK | Failed: $FAIL"
if [[ ${#FAILED_REPOS[@]} -gt 0 ]]; then
  echo "  Failed:"; for r in "${FAILED_REPOS[@]}"; do echo "    ✗ $r"; done
  echo "  Fix: cd <repo> && bash scripts/quality-gates.sh --no-fix"
  exit 1
fi
echo "  All quality gates passed."
