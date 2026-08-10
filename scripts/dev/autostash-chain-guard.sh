#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# autostash-chain-guard.sh -- guard for the autostash CHAIN (2026-08-10 slot-1 finding,
# multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md).
#
# THE CHAIN: every `git pull --rebase --autostash` (which both ship scripts run internally,
# several times per push) stashes the dirty tree and pops it back. If the tree is ALREADY
# carrying stale content -- old versions that REVERT content committed on origin/$BRANCH --
# each cycle re-applies and re-preserves it, so the snapshot ages forward indefinitely and
# `git stash list` accumulates autostash entries. Nothing ever compares the popped content
# against origin, so a revert is indistinguishable from an edit. Measured 2026-08-10 (slot-1):
# 107 files dirty, 97 reverting content committed hours earlier, 9 archived plans resurrected
# as untracked under plans/active/.
#
# TWO FUNCTIONS (sourced by quickmerge.sh + safe-doc-push.sh):
#
#   autostash_chain_guard_quarantine_reverts <branch> [caller-files as one space-separated string]
#     Detect working-tree content that REVERTS content already committed on origin/<branch>
#     (tracked file whose blob is an ANCESTOR blob for that path but != origin tip; a deletion
#     of a file still tracked on origin; or an untracked file whose blob is reachable from
#     origin = a resurrected archived plan). Foreign stale files are QUARANTINED to a named
#     stash (recoverable; the working tree returns to origin content so the next autostash
#     cycle has nothing stale to re-apply). A CALLER-NAMED file (one being shipped this run)
#     is never auto-quarantined: if it is itself a stale revert, the guard REFUSES (returns 1)
#     so the caller reconsiders shipping a silent revert.
#     Returns 0 = tree is clean of stale reverts (or only foreign content was quarantined —
#     the sanctioned outcome). Returns 1 = a caller-named file would ship a silent revert;
#     the caller MUST block.
#
#   autostash_chain_guard_bound_backlog <branch> [max=5]
#     Prune accumulated git-generated `autostash` entries that are PROVABLY REDUNDANT (their
#     diff reverse-applies cleanly to the current tree -- the changes are already present, so
#     dropping loses nothing). Never drops a named stash (a peer's WIP) or a non-redundant
#     entry. Bounds the backlog so the chain cannot age.
#
# Always returns safely under `set -e` / `set -uo pipefail` (no bare failing command at
# function level; every fallible git call is guarded by `||` / `if`).

# Detect + quarantine stale-reverting working-tree content. Must be called AFTER the caller's
# `git restore --staged .` (index == HEAD) so `git ls-files -m/-d` reflects the working tree
# only. $1 = branch; $2 = space-separated caller-named files (may be empty).
autostash_chain_guard_quarantine_reverts() {
  local branch="${1:-${BRANCH:-}}"
  local caller_list="${2:-}"
  local -a quarantine=() refused=()
  local file blob tip
  local origin_blobset=""
  local scanned_untracked=0

  # --- Tracked files dirty in the working tree (modified OR deleted vs the index). ---------
  while IFS= read -r file; do
    [ -z "$file" ] && continue
    if _autostash_guard_is_stale_tracked_revert "$branch" "$file"; then
      if _autostash_guard_is_caller_named "$file" "$caller_list"; then
        refused+=("$file")
      else
        quarantine+=("$file")
      fi
    fi
  done < <( { git ls-files -m 2>/dev/null; git ls-files -d 2>/dev/null; } | sort -u )

  # --- Untracked files whose content is already committed somewhere on origin (resurrection).
  # Lazily build the reachable-blob set once; only touched when untracked files exist.
  while IFS= read -r file; do
    [ -z "$file" ] && continue
    blob="$(git hash-object -- "$file" 2>/dev/null)" || continue
    if [ "$scanned_untracked" = "0" ]; then
      origin_blobset="$(git rev-list --objects "origin/$branch" 2>/dev/null | awk '{print $1}' | sort -u)"
      scanned_untracked=1
    fi
    if printf '%s\n' "$origin_blobset" | grep -qx "$blob"; then
      if _autostash_guard_is_caller_named "$file" "$caller_list"; then
        refused+=("$file")
      else
        quarantine+=("$file")
      fi
    fi
  done < <(git ls-files --others --exclude-standard 2>/dev/null)

  if [ "${#quarantine[@]}" -gt 0 ]; then
    local label="stale-autostash-revert:$(date -u +%Y%m%dT%H%M%SZ)"
    # shellcheck disable=SC2086  # array is a deliberate pathspec list
    if git stash push -u -q -m "$label" -- "${quarantine[@]}" 2>/dev/null; then
      echo "  ⚠️  autostash-chain guard: quarantined ${#quarantine[@]} stale file(s) to named stash '$label' (content REVERTED content committed on origin/$branch) — tree restored to origin content, NOT applied silently."
      echo "      recover with: git stash show -p '$label'   |   git stash apply '$label'"
    else
      echo "  ⚠️  autostash-chain guard: FAILED to quarantine ${#quarantine[@]} stale file(s) — resolve the working tree manually before continuing" >&2
    fi
  fi

  if [ "${#refused[@]}" -gt 0 ]; then
    echo "  ❌ autostash-chain guard REFUSED: caller-named file(s) would REVERT content committed on origin/$branch (a silent revert):" >&2
    printf '      %s\n' "${refused[@]}" >&2
    echo "      Revert it deliberately (or drop it from --files) and retry." >&2
    return 1
  fi
  return 0
}

# A tracked file's working-tree content is a stale revert iff it matches an ANCESTOR blob of
# origin/$branch at that path but NOT the origin tip, or the file is deleted although origin
# still tracks it.
_autostash_guard_is_stale_tracked_revert() {
  local branch="$1" file="$2"
  local wt tip c blob
  tip="$(git rev-parse "origin/$branch:$file" 2>/dev/null)" || return 1  # not on origin → nothing committed to revert
  if [ ! -f "$file" ]; then
    return 0  # deleted although live on origin → revert of committed content
  fi
  wt="$(git hash-object -- "$file" 2>/dev/null)" || return 1
  if [ "$wt" = "$tip" ]; then
    return 1  # matches origin tip → clean, not a revert
  fi
  # wt != tip: is wt an ancestor blob reachable from origin/$branch for this path?
  while IFS= read -r c; do
    [ -z "$c" ] && continue
    blob="$(git rev-parse "$c:$file" 2>/dev/null)" || continue
    if [ "$blob" = "$wt" ]; then
      return 0
    fi
  done < <(git rev-list "origin/$branch" -n 200 -- "$file" 2>/dev/null)
  return 1
}

_autostash_guard_is_caller_named() {
  local file="$1" caller_list="$2" x
  # shellcheck disable=SC2086  # intentional word-split: caller_list is a space-separated path list
  for x in $caller_list; do
    if [ "$x" = "$file" ]; then
      return 0
    fi
  done
  return 1
}

# Bound the autostash backlog: drop git-generated `autostash` entries whose changes are already
# present in the current tree (provably redundant). Never touches named stashes or a
# non-redundant entry. $1 = branch (unused, kept for symmetry); $2 = max retained (default 5).
autostash_chain_guard_bound_backlog() {
  local branch="${1:-${BRANCH:-}}"
  local max="${2:-5}"
  local -a autos=()
  local line ref i n drop
  while IFS= read -r line; do
    case "$line" in
      *": autostash") ref="${line%%:*}"; autos+=("$ref") ;;
    esac
  done < <(git stash list 2>/dev/null)
  n="${#autos[@]}"
  if [ "$n" -le "$max" ]; then
    return 0
  fi
  drop=0
  # Drop from the HIGHEST original index down so earlier ref names stay valid as the list shrinks.
  for ((i = n - 1; i >= 0 && drop < n - max; i--)); do
    ref="${autos[$i]}"
    # Provably redundant == the entry's diff reverse-applies cleanly to the current tree.
    # Empty / untracked-only / conflicted entries fail this and are kept (never risk a peer's WIP).
    if git stash show -p "$ref" 2>/dev/null | git apply --reverse --check - 2>/dev/null; then
      if git stash drop -q "$ref" 2>/dev/null; then
        drop=$((drop + 1))
        echo "  ✔ autostash-chain guard: pruned redundant autostash entry $ref"
      fi
    fi
  done
  return 0
}
