#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# tree-wip-guard.sh -- notice when a ship's reconcile ate uncommitted work it was never asked
# to touch.
#
# THE HOLE THIS CLOSES (measured 2026-08-10, on the author of the other fixes). Every loss guard
# built during that session -- quickmerge's `_QM_ENTRY_FINGERPRINT`, safe-doc-push's
# `_sdp_fingerprint_named` and its exit-10 content-vanished check -- fingerprints ONLY the files
# passed in `--files`. That is the work you are shipping. Nothing watched the REST of the tree.
#
# So: an edit to `scripts/quickmerge.sh` that was not part of that run's `--files` collided with
# a peer's upstream change to the same file, `git pull --rebase --autostash` stashed it, the pop
# resolved against the incoming version, and the edit was gone. No warning, no non-zero exit, no
# exit 10 -- the run reported success, because by its own definition it had succeeded. It was
# found minutes later by accident while checking something unrelated.
#
# That is the general case, not an edge case. On a shared checkout an agent nearly always has
# unrelated WIP in the tree while shipping one specific thing; a guard scoped to `--files` is
# blind to exactly the work its owner is least expecting to lose.
#
# WHAT THIS DOES AND DOES NOT DO. It cannot prevent the collision -- `--autostash` is doing what
# it was told, and refusing to reconcile whenever the tree is dirty would block nearly every ship
# on a busy repo. It converts a SILENT loss into a LOUD, recoverable one: snapshot every modified
# tracked file before the reconcile, re-check after, and report anything that changed and was not
# in `--files`, alongside the stash ref that still holds it. Recoverability is the property that
# matters -- the content was never actually destroyed, only detached from where anyone would look.
#
# Deliberately advisory (never exits non-zero on its own): a ship that has already pushed must not
# be failed retroactively over a neighbouring file, and turning this into a hard gate would make
# every dirty-tree ship a coin flip. Callers decide what to do with the finding.
#
# Usage:
#   snap="$(wip_guard_snapshot)"                       # before the reconcile
#   wip_guard_report "$snap" "$FILES_ARG"              # after it (space-separated named files)

# Restore parked work WITHOUT silently reverting whoever else changed the file.
#
# THE FAILURE THIS MAKES IMPOSSIBLE (not merely discouraged). On finding an eaten edit the
# instinct is `git show 'stash@{N}:path' > path` — restore the whole file. That is exactly wrong
# in the case that produced the loss: the edit was eaten BECAUSE someone else changed the same
# file, so a wholesale restore reinstates your version and silently deletes theirs. Measured
# 2026-08-10: the recovery was one keystroke from reverting a peer's shipped fix, avoided only
# by noticing in time. Advice in a warning string does not stop a tired agent at 2am.
#
# So this decides mechanically, on content, not on intent:
#   * current == the version the stash was taken against  -> nobody else touched it, restore is
#     safe, do it.
#   * current differs                                     -> someone else DID touch it. Never
#     clobber: run a real 3-way merge (base = stash's parent) so their change survives, and let
#     git write conflict markers if the two genuinely collide.
#
# Exit 0 = restored cleanly (either path). Exit 1 = merged WITH CONFLICTS, hand-resolve. Exit 2 =
# could not determine a base, nothing written — refusing beats guessing.
wip_guard_restore() {
  local stash_ref="$1" path="$2"
  local base_f cur_f stash_f rc
  [ -n "$stash_ref" ] && [ -n "$path" ] || { echo "usage: wip_guard_restore <stash-ref> <path>" >&2; return 2; }

  base_f="$(mktemp)"; stash_f="$(mktemp)"; cur_f="$(mktemp)"
  # `<stash>^1` is the commit the stash was created from — the content both sides diverged from.
  if ! git show "${stash_ref}^1:${path}" > "$base_f" 2>/dev/null; then
    echo "  ✖ cannot resolve the pre-stash version of ${path} (${stash_ref}^1) — refusing to guess." >&2
    rm -f "$base_f" "$stash_f" "$cur_f"; return 2
  fi
  if ! git show "${stash_ref}:${path}" > "$stash_f" 2>/dev/null; then
    echo "  ✖ ${path} is not in ${stash_ref} — nothing parked to restore." >&2
    rm -f "$base_f" "$stash_f" "$cur_f"; return 2
  fi
  [ -f "$path" ] && cp "$path" "$cur_f" || cp "$base_f" "$cur_f"

  if cmp -s "$cur_f" "$base_f"; then
    cp "$stash_f" "$path"
    echo "  ✓ restored ${path} — nobody else changed it since it was parked." >&2
    rm -f "$base_f" "$stash_f" "$cur_f"; return 0
  fi

  # Someone else changed it. A 3-way merge keeps BOTH sides; a copy would delete theirs.
  git merge-file -L "yours (parked)" -L "common base" -L "theirs (current)" \
    "$stash_f" "$base_f" "$cur_f" >/dev/null 2>&1
  rc=$?
  cp "$stash_f" "$path"
  if [ "$rc" -eq 0 ]; then
    echo "  ✓ ${path} — someone else changed it too; 3-way merged, both changes kept." >&2
    rm -f "$base_f" "$stash_f" "$cur_f"; return 0
  fi
  echo "  ⚠ ${path} — someone else changed the SAME lines; merged with conflict markers." >&2
  echo "    Resolve by hand. A wholesale restore here would have deleted their work outright." >&2
  rm -f "$base_f" "$stash_f" "$cur_f"; return 1
}

# Leave a notice IN THE CHECKOUT for whoever owns the work that was moved.
#
# WHY THIS IS SEPARATE FROM wip_guard_report. That function writes to the SHIPPING run's stderr,
# which reaches the person who ran the push — fine when the eaten edit was their own. It is
# useless for the other half of the problem: when your reconcile parks a PEER's uncommitted work
# (or you stash it deliberately to unblock a gate), that peer is in a different session and sees
# nothing at all. The only trace is a stash entry in a checkout they have no reason to inspect.
# Measured 2026-08-10: a peer's conflicted WIP was parked under a descriptive stash name and the
# only thing that would ever have told them was a human remembering to say so.
#
# `.parked-wip` sits beside `.agent-claim`, which `slot-git-status-report.sh` already reads on its
# 5-minute cycle — so surfacing it there reaches whoever is actually working in this checkout,
# without inventing a new channel or requiring a commit. Append-only: two parks before anyone
# reads it must not silently overwrite the first.
wip_guard_park_notice() {
  local stash_ref="$1"; shift
  local root notice
  root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
  notice="$root/.parked-wip"
  {
    echo "── uncommitted work parked $(date '+%Y-%m-%d %H:%M:%S') by ${SLOT_ID_EXPECTED_NAME:-a ship script} ──"
    echo "   files: $*"
    echo "   recover: git show '${stash_ref}:<path>'   then RE-APPLY YOUR HUNK BY HAND."
    echo "   Do NOT restore the whole file: it was parked because someone else changed it too,"
    echo "   and a wholesale restore silently reverts their work."
    echo "   SSOT: /codex/05-infrastructure/per-tab-worktrees.md"
    echo ""
  } >> "$notice" 2>/dev/null || true
  echo "  📝 left a recovery notice for this checkout's owner at .parked-wip" >&2
}

# Print "<blob-hash>  <path>" for every MODIFIED TRACKED file. Untracked files are excluded on
# purpose: git's autostash does not touch them by default, and including them would flag every
# scratch file an agent happens to have lying around.
wip_guard_snapshot() {
  git status --porcelain --untracked-files=no 2>/dev/null | awk '$1 ~ /^(M|MM|AM|RM)$/ || $1 == "M" {
    # porcelain: XY <path>; path starts at col 4, may contain spaces
    print substr($0, 4)
  }' | while IFS= read -r _wg_f; do
    [ -n "$_wg_f" ] || continue
    [ -f "$_wg_f" ] || continue
    printf '%s  %s\n' "$(git hash-object -- "$_wg_f" 2>/dev/null || echo MISSING)" "$_wg_f"
  done
}

# Compare a snapshot against the tree now. Anything whose content moved, and which was NOT among
# the named files this run was allowed to change, is reported.
wip_guard_report() {
  local snap="$1" named="${2:-}" changed=0 line hash path now
  [ -n "$snap" ] || return 0

  while IFS= read -r line; do
    [ -n "$line" ] || continue
    hash="${line%% *}"
    path="${line#*  }"
    # Named files are legitimately rewritten by this run (prettier, autofix hooks, the commit).
    case " $named " in *" $path "*) continue ;; esac
    if [ -f "$path" ]; then
      now="$(git hash-object -- "$path" 2>/dev/null || echo MISSING)"
      [ "$now" = "$hash" ] && continue
      echo "  ⚠ $path — your uncommitted edit is GONE (content changed during the reconcile)" >&2
    else
      echo "  ⚠ $path — your uncommitted edit is GONE (file removed during the reconcile)" >&2
    fi
    changed=1
  done <<<"$snap"

  [ "$changed" = "1" ] || return 0

  echo "  These files were NOT part of this run's --files, so nothing here was going to commit them." >&2
  echo "  They are recoverable, not destroyed — the reconcile stashed them. Recover with:" >&2
  echo "    git stash list        # find the autostash entry from this run" >&2
  echo "    git show 'stash@{N}:<path>'   # inspect, then re-apply your hunk BY HAND" >&2
  echo "  Re-apply by hand, not by restoring the whole file: the collision means someone else" >&2
  echo "  changed it too, and a wholesale restore would silently revert THEIR work." >&2
  echo "  SSOT: /plans/active/issues/pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md" >&2
  return 0
}
