#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Audit all workspace repos for reset/reset --hard/reset to origin in reflog.
# Reports repos that may have had commits discarded. For manual review.
#
# Usage: bash audit-reflog-resets.sh [--limit N] [--reflog-depth N] [--ignore repo1,repo2]
# Run from: workspace root or unified-trading-pm/scripts/repo-management/
#
# Output: Repos with reset entries, categorized by risk (--hard, to origin, no-op).

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Resolve workspace root from cwd (must run from workspace root)
if [ -f "$(pwd)/unified-trading-pm/workspace-manifest.json" ]; then
  WORKSPACE_ROOT="$(pwd)"
elif [ -f "$(pwd)/workspace-manifest.json" ]; then
  WORKSPACE_ROOT="$(cd .. && pwd)"
else
  echo "Error: Run from workspace root. Expected unified-trading-pm/workspace-manifest.json"
  echo "  cd /path/to/unified-trading-system-repos"
  echo "  bash <script>"
  exit 1
fi
PM_ROOT="$WORKSPACE_ROOT/unified-trading-pm"
MANIFEST="$PM_ROOT/workspace-manifest.json"

REFLOG_DEPTH=50
LIMIT=""
IGNORE_REPOS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --limit) LIMIT="$2"; shift 2 ;;
    --reflog-depth) REFLOG_DEPTH="$2"; shift 2 ;;
    --ignore) IGNORE_REPOS+=(${2//,/ }); shift 2 ;;
    *) shift ;;
  esac
done

# Load ignore list: repo:hash (per-commit) or repo (legacy, whole repo)
IGNORE_FILE="$SCRIPT_DIR/audit-reflog-ignore.txt"
IGNORE_COMMITS=()  # repo:hash
IGNORE_REPOS=()    # legacy: whole repo
[[ -f "$IGNORE_FILE" ]] && while read -r r; do
  [[ -z "$r" || "$r" == \#* ]] && continue
  if [[ "$r" == *:* ]]; then
    IGNORE_COMMITS+=("$r")
  else
    IGNORE_REPOS+=("$r")
  fi
done < "$IGNORE_FILE"


[[ ! -f "$MANIFEST" ]] && { echo "Missing $MANIFEST"; exit 1; }

REPOS=($(jq -r '.repositories | keys[]' "$MANIFEST" 2>/dev/null))
[[ -n "$LIMIT" ]] && REPOS=("${REPOS[@]:0:$LIMIT}")

echo "Audit reflog for resets: ${#REPOS[@]} repos (depth=$REFLOG_DEPTH)"
echo ""

high_risk=()
medium_risk=()
low_risk=()

for repo in "${REPOS[@]}"; do
  # Skip ignored repos (verified/fixed)
  for ign in "${IGNORE_REPOS[@]:-}"; do [[ -n "$ign" && "$repo" = "$ign" ]] && continue 2; done
  dir="$WORKSPACE_ROOT/$repo"
  [[ ! -d "$dir" ]] && continue
  [[ ! -d "$dir/.git" ]] && continue

  reflog=$(git -C "$dir" reflog -n "$REFLOG_DEPTH" 2>/dev/null) || true
  [[ -z "$reflog" ]] && continue

  # High-risk: reset --hard or reset to origin/main.
  # Solved if: commit in origin/main, or equivalent patch, or repo:hash in ignore (intentional discard).
  if echo "$reflog" | grep -qE "reset.*--hard|reset: moving to origin/main|reset: moving to origin/"; then
    unsolved=0
    lines=()
    while IFS= read -r line; do lines+=("$line"); done <<< "$reflog"
    for i in "${!lines[@]}"; do
      line="${lines[$i]}"
      if echo "$line" | grep -qE "reset.*--hard|reset: moving to origin/main|reset: moving to origin/"; then
        next=$((i+1))
        if [[ $next -lt ${#lines[@]} ]]; then
          lost_hash="${lines[$next]%% *}"
          # Per-commit ignore: repo:hash (intentional discard)
          ignored=0
          for ic in "${IGNORE_COMMITS[@]:-}"; do
            [[ -n "$ic" && "$ic" = "$repo:$lost_hash" ]] && ignored=1 && break
          done
          [[ $ignored -eq 1 ]] && continue
          git -C "$dir" fetch origin 2>/dev/null || true
          # Solved if: exact commit in history, OR same patch committed (cherry-pick)
          if git -C "$dir" merge-base --is-ancestor "$lost_hash" origin/main 2>/dev/null; then
            :  # exact commit recovered
          elif out=$(git -C "$dir" cherry -v origin/main "$lost_hash" 2>/dev/null) && [[ "${out:0:1}" == "-" ]]; then
            :  # equivalent patch in origin/main (cherry-picked)
          else
            unsolved=1
            break
          fi
        fi
      fi
    done
    [[ $unsolved -eq 1 ]] && high_risk+=("$repo")
  elif echo "$reflog" | grep -q "reset: moving to origin"; then
    medium_risk+=("$repo")
  elif
    # LOW: real reflog *reset* operations only (verb "reset:" after HEAD@{n}:).
    # Do not match the substring "reset" in commit subjects (e.g. reset_index).
    # Exclude index-only unstage: "reset: moving to HEAD" (no discarded commits).
    reflog_reset_ops=$(echo "$reflog" | grep -E '^[0-9a-f]+ HEAD@\{[0-9]+\}: reset:' || true)
    [[ -z "$reflog_reset_ops" ]] && continue
    nontrivial_resets=$(echo "$reflog_reset_ops" | grep -vE 'reset: moving to HEAD$' || true)
    [[ -n "$nontrivial_resets" ]]
  then
    low_risk+=("$repo")
  fi
done

echo "=== HIGH RISK (reset --hard or reset to origin/main) ==="
if [[ ${#high_risk[@]} -eq 0 ]]; then
  echo "  (none)"
else
  for r in "${high_risk[@]}"; do
    dir="$WORKSPACE_ROOT/$r"
    reflog=$(git -C "$dir" reflog -n "$REFLOG_DEPTH" 2>/dev/null)
    lines=()
    while IFS= read -r line; do lines+=("$line"); done <<< "$reflog"
    for i in "${!lines[@]}"; do
      line="${lines[$i]}"
      if echo "$line" | grep -qE "reset.*--hard|reset: moving to origin/main|reset: moving to origin/"; then
        next=$((i+1))
        if [[ $next -lt ${#lines[@]} ]]; then
          lost_hash="${lines[$next]%% *}"
          echo "  $r ($r:$lost_hash)"
          echo "    $line"
          echo "    To ignore this intentional discard: add $r:$lost_hash to audit-reflog-ignore.txt"
          echo ""
        fi
      fi
    done
  done
fi

echo ""
echo "=== MEDIUM RISK (reset to origin/*) ==="
if [[ ${#medium_risk[@]} -eq 0 ]]; then
  echo "  (none)"
else
  for r in "${medium_risk[@]}"; do
    echo "  $r"
  done
fi

echo ""
echo "=== LOW RISK (other resets, e.g. --soft) ==="
if [[ ${#low_risk[@]} -eq 0 ]]; then
  echo "  (none)"
else
  for r in "${low_risk[@]}"; do
    echo "  $r"
  done
fi

echo ""
echo "Summary: ${#high_risk[@]} high, ${#medium_risk[@]} medium, ${#low_risk[@]} low"
[[ ${#high_risk[@]} -gt 0 ]] && exit 1
exit 0
