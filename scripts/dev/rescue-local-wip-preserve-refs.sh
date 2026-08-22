#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# rescue-local-wip-preserve-refs.sh — push local-only wip-preserve cascade/regate refs
# to refs/heads/wip-preserve/ on origin before they can be lost to clone deletion or
# host wipe.
#
# Problem (wip_preserve_refs_silently_unrecovered_2026_07_29.md § "Tier 2"):
#   quickmerge.sh creates LOCAL-ONLY refs via `git update-ref`, never pushed:
#     refs/wip-preserve/cascade-<repo>-<sha12>          (cascade_dep_branch)
#     refs/wip-preserve/quickmerge-stage5-regate-<sha12> (STAGE 5 regate guard)
#   Standard fetch refspec (+refs/heads/*:refs/remotes/origin/*) cannot match them.
#   They die silently if the clone is deleted or the host wiped — no trace anywhere.
#
# Fix: for every local cascade/regate ref whose sha is NOT already an ancestor of
#   origin/<branch>, push it to refs/heads/wip-preserve/ on origin FIRST, then
#   classify. This converts the fragile local-only tier into the durable remote tier
#   where OrphanRefVerifyWatchdog and the daily remote sweep already operate.
#
#   Refs whose sha IS already an ancestor are safe (content is on the branch) — they
#   are reported but not pushed. This matches the plan's "rescue before classifying"
#   contract: push = make durable; classification happens via the remote sweep.
#
# Usage: bash rescue-local-wip-preserve-refs.sh [options]
#   --workspace PATH   root of unified-trading-system-repos (default: auto-detect)
#   --branch BRANCH    integration branch (default: live-defi-rollout)
#   --dry-run          print what would be pushed; do not push
#   --quiet            suppress per-ref lines for ANCESTOR refs (still logs PUSH/ERROR)
#
# Done when: this sweep finds zero local cascade/regate refs carrying content NOT
# already on origin/<branch>. The operator ruling (2026-08-06) mandates this runs
# daily on every host; the daily scheduled AO job (wip_preserve_refs_silently_
# unrecovered-001) will call this script per-host via SSM.
#
# Ref: /plans/active/issues/wip_preserve_refs_silently_unrecovered_2026_07_29.md

set -uo pipefail

# ── arg parsing ──────────────────────────────────────────────────────────────
WORKSPACE=""
BRANCH="live-defi-rollout"
DRY_RUN=0
QUIET=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workspace)  WORKSPACE="$2"; shift 2 ;;
    --branch)     BRANCH="$2";    shift 2 ;;
    --dry-run)    DRY_RUN=1;      shift   ;;
    --quiet)      QUIET=1;        shift   ;;
    -h|--help)
      sed -n '/^# Usage:/,/^[^#]/{ /^#/!q; s/^# \?//p }' "$0"
      exit 0 ;;
    *) echo "[rescue] unknown flag: $1" >&2; exit 1 ;;
  esac
done

# ── workspace root auto-detect ────────────────────────────────────────────────
if [[ -z "$WORKSPACE" ]]; then
  # Climb from this script's location: scripts/dev/ -> scripts/ -> repo root -> ws root
  _script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  _candidate="$(cd "$_script_dir/../../.." && pwd)"
  if [[ -d "$_candidate/.tabs" ]]; then
    WORKSPACE="$_candidate"
  elif [[ -d "${HOME}/unified-trading-system-repos/.tabs" ]]; then
    WORKSPACE="${HOME}/unified-trading-system-repos"
  else
    echo "[rescue] ERROR: could not locate workspace root (expected .tabs/ sibling). Pass --workspace." >&2
    exit 1
  fi
fi

TABS_ROOT="$WORKSPACE/.tabs"
[[ -d "$TABS_ROOT" ]] || { echo "[rescue] ERROR: no .tabs/ directory at $TABS_ROOT" >&2; exit 1; }

echo "[rescue] workspace=$WORKSPACE  branch=$BRANCH  dry_run=$DRY_RUN"
echo ""

# ── counters ──────────────────────────────────────────────────────────────────
total_refs=0
pushed=0
already_remote=0
skipped_ancestor=0
errors=0

# ── helpers ───────────────────────────────────────────────────────────────────

_scan_repo() {
  local repo_dir="$1" label="$2"

  local local_refs
  local_refs=$(git -C "$repo_dir" for-each-ref \
    --format='%(refname)' \
    'refs/wip-preserve/cascade-*' \
    'refs/wip-preserve/quickmerge-stage5-regate-*' 2>/dev/null) || return 0
  [[ -z "$local_refs" ]] && return 0

  # One fetch per repo to refresh origin/<branch> tracking ref
  git -C "$repo_dir" fetch --quiet origin "$BRANCH" 2>/dev/null || true

  while IFS= read -r refname; do
    [[ -z "$refname" ]] && continue
    total_refs=$((total_refs + 1))

    # Resolve to full sha (the refname's embedded sha12 is truncated; use rev-parse)
    local sha
    sha=$(git -C "$repo_dir" rev-parse "$refname" 2>/dev/null) || {
      echo "[rescue] ERROR [$label] $refname: rev-parse failed"
      errors=$((errors + 1))
      continue
    }

    # Leaf = part after refs/wip-preserve/ → remote ref = refs/heads/wip-preserve/<leaf>
    local leaf="${refname#refs/wip-preserve/}"
    local remote_ref="refs/heads/wip-preserve/$leaf"

    # Already on branch → nothing to rescue
    if git -C "$repo_dir" merge-base --is-ancestor "$sha" "origin/$BRANCH" 2>/dev/null; then
      [[ "$QUIET" -eq 0 ]] && echo "[rescue] ANCESTOR [$label] $refname (${sha:0:12}) — already on origin/$BRANCH"
      skipped_ancestor=$((skipped_ancestor + 1))
      continue
    fi

    # NOT on branch → push to make durable
    if [[ "$DRY_RUN" -eq 1 ]]; then
      echo "[rescue] DRY-RUN [$label] would push $refname (${sha:0:12}) -> $remote_ref"
      pushed=$((pushed + 1))
      continue
    fi

    local push_out push_rc
    push_out=$(git -C "$repo_dir" push origin "${sha}:${remote_ref}" 2>&1)
    push_rc=$?

    if [[ $push_rc -eq 0 ]]; then
      if echo "$push_out" | grep -qi "up.to.date\|up to date"; then
        echo "[rescue] ALREADY-REMOTE [$label] $refname (${sha:0:12}) — $remote_ref already present on origin"
        already_remote=$((already_remote + 1))
      else
        echo "[rescue] PUSHED [$label] $refname (${sha:0:12}) -> $remote_ref"
        pushed=$((pushed + 1))
      fi
    else
      # Check if the remote ref already points to this exact sha (idempotent already-pushed)
      local existing
      existing=$(git -C "$repo_dir" ls-remote origin "$remote_ref" 2>/dev/null | awk '{print $1}')
      if [[ "${existing:-}" == "$sha" ]]; then
        echo "[rescue] ALREADY-REMOTE [$label] $refname (${sha:0:12}) — $remote_ref already at same sha"
        already_remote=$((already_remote + 1))
      else
        echo "[rescue] ERROR [$label] $refname (${sha:0:12}) push to $remote_ref failed: $push_out"
        errors=$((errors + 1))
      fi
    fi
  done <<< "$local_refs"
}

# ── main sweep: slot clones ───────────────────────────────────────────────────
echo "=== Sweeping slot clones under $TABS_ROOT ==="
for slot_dir in "$TABS_ROOT"/*/; do
  [[ -d "$slot_dir" ]] || continue
  slot_name="$(basename "$slot_dir")"
  for repo_dir in "$slot_dir"*/; do
    [[ -e "$repo_dir/.git" ]] || continue
    repo_name="$(basename "$repo_dir")"
    _scan_repo "$repo_dir" "slot=$slot_name/$repo_name"
  done
done

# ── main sweep: root clones ───────────────────────────────────────────────────
# quickmerge running from a root clone cascades into WORKSPACE/<ancestor>,
# so cascade refs can also appear in the root clone tree.
echo ""
echo "=== Sweeping root clones under $WORKSPACE ==="
for repo_dir in "$WORKSPACE"/*/; do
  # Skip .tabs/ and non-git directories
  [[ "$(basename "$repo_dir")" == ".tabs" ]] && continue
  [[ -e "$repo_dir/.git" ]] || continue
  repo_name="$(basename "$repo_dir")"
  _scan_repo "$repo_dir" "root/$repo_name"
done

# ── summary ───────────────────────────────────────────────────────────────────
echo ""
echo "=== rescue-local-wip-preserve-refs summary (dry_run=$DRY_RUN) ==="
echo "  total local-only refs scanned : $total_refs"
echo "  skipped (already on branch)   : $skipped_ancestor"
echo "  pushed to origin (rescued)    : $pushed"
echo "  already-remote (idempotent)   : $already_remote"
echo "  errors                        : $errors"

if [[ $errors -gt 0 ]]; then
  echo ""
  echo "WARNING: $errors ref(s) failed to push — review output above."
  exit 1
fi

not_rescued=$((total_refs - skipped_ancestor - pushed - already_remote))
if [[ $not_rescued -ne 0 ]]; then
  echo ""
  echo "WARNING: $not_rescued ref(s) were not accounted for — possible logic error."
  exit 1
fi

echo ""
if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "Dry-run complete. Re-run without --dry-run to push."
else
  echo "Done. All local-only cascade/regate refs with content not on $BRANCH have been pushed to origin."
fi
