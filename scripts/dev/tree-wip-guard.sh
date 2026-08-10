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

# ─── autostash chain-breaker ─────────────────────────────────────────────────
#
# THE HOLE THIS CLOSES (measured 2026-08-10 slot-1, 107 files — the autostash CHAIN
# re-applies an ever-staler snapshot). Every `git pull --rebase --autostash` stashes the
# dirty tree, rebases, and pops it back. If the tree was ALREADY carrying stale content
# from a PREVIOUS autostash cycle, each new cycle re-applies and re-preserves it. Nothing
# ever compares the popped content against origin, so a revert is indistinguishable from
# an edit. After enough cycles the stash list holds dozens of autostash entries, each a
# snapshot of the same aging content. The fix: (1) after a successful pop, detect files
# the pop restored that differ from origin and quarantine them to a NAMED stash instead
# of leaving them in the working tree, so the next cycle does NOT re-stash them; and
# (2) bound the autostash backlog so a runaway chain self-arrests.
#
# SSOT: /plans/active/issues/multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md

# autostash_guard_quarantine_stale_pop — after a successful autostash pop +
# `git restore --staged .`, check every dirty tracked file NOT in the protected set
# against origin/<branch>. Any that differ from origin were restored by the autostash
# from a pre-pull snapshot and are NOT the caller's intended edit — quarantine them to a
# named stash (never dropped, always recoverable) and restore the origin version so the
# next reconcile cycle starts from a clean base.
#
# $1: space-separated protected paths (the caller's --files, or "" for none)
# $2: remote branch ref, e.g. "origin/live-defi-rollout"
# Returns 0 (advisory — a push that has already landed must not retroactively fail).
autostash_guard_quarantine_stale_pop() {
  local protected="${1:-}" branch="${2:-origin/live-defi-rollout}" dirty file quarantined=()
  dirty="$(git diff --name-only 2>/dev/null)"
  [ -n "$dirty" ] || return 0

  while IFS= read -r file; do
    [ -n "$file" ] || continue
    case " $protected " in *" $file "*) continue ;; esac
    git ls-files --error-unmatch -- "$file" >/dev/null 2>&1 || continue
    if git cat-file -e "$branch:$file" 2>/dev/null; then
      git diff --quiet "$branch" -- "$file" 2>/dev/null && continue
    fi
    quarantined+=("$file")
  done <<<"$dirty"

  [ ${#quarantined[@]} -gt 0 ] || return 0

  local stash_msg="safety-snapshot: stale reapplied-autostash — $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  if git stash push -m "$stash_msg" -- "${quarantined[@]}" 2>/dev/null; then
    local f
    for f in "${quarantined[@]}"; do
      if git cat-file -e "$branch:$f" 2>/dev/null; then
        git checkout "$branch" -- "$f" 2>/dev/null || true
      else
        rm -f "$f" 2>/dev/null || true
      fi
    done
    {
      echo "  🛑 autostash pop restored stale/foreign content in ${#quarantined[@]} file(s)"
      echo "     — quarantined to stash (not dropped — recover with 'git stash show -p stash@{0}')"
      printf '     - %s\n' "${quarantined[@]}"
      echo "     These files were NOT in this run's --files; the autostash pop re-applied them from a"
      echo "     pre-pull snapshot that already carried stale content (the autostash CHAIN — see"
      echo "     multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md)."
      echo "     Each file has been replaced with the origin/${branch##*/} version to break the chain."
    } >&2
  fi
  return 0
}

# autostash_guard_bound_backlog — call BEFORE any reconcile that may create a new
# autostash entry. When the backlog is large (>=5 autostash entries), warns and prints
# the list. When it is extreme (>=10), ALSO quarantines the current dirty tree into a
# named stash BEFORE the pull, so no NEW autostash entry is created on top of the pile.
# The chain self-arrests because the next pull has a clean tree, producing no new entry.
#
# $1: space-separated protected paths (the caller's --files, or "" for none) — these
#     are the work being SHIPPED and must NEVER be quarantined, even in the extreme
#     case (dogfooded live 2026-08-10 slot-9: an extreme pile quarantined the caller's
#     own plan-flip edit, the ship then falsely reported "already matches HEAD").
# $2: remote branch ref (for the quarantine fallback, default origin/live-defi-rollout)
# Returns 0 (advisory — never blocks the caller).
autostash_guard_bound_backlog() {
  local protected="${1:-}" branch="${2:-origin/live-defi-rollout}" entries entry_list count
  entry_list="$(git stash list 2>/dev/null | grep -i 'autostash\|safety-snapshot.*stale reapplied' || true)"
  [ -n "$entry_list" ] || return 0
  count="$(printf '%s\n' "$entry_list" | wc -l)"
  if [ "$count" -ge 5 ]; then
    {
      echo "  ⚠ ${count} autostash/safety-snapshot entries in the stash list — the autostash CHAIN may be active."
      echo "     These entries are parked, not dropped. Inspect with 'git stash list' and drop old ones:"
      echo "       git stash drop 'stash@{N}'   # drop one"
      echo "     SSOT: multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md"
      if [ "$count" -ge 10 ]; then
        echo "  🛑 ${count} entries is extreme — quarantining current dirty tree into a named stash"
        echo "     BEFORE the pull so no new autostash entry is created on top of the pile."
      fi
    } >&2
  fi
  if [ "$count" -ge 10 ]; then
    local current_dirty f to_quarantine=()
    current_dirty="$(git diff --name-only 2>/dev/null)"
    if [ -n "$current_dirty" ]; then
      # Skip the caller's named files: they are the work being shipped and must survive
      # untouched even in the extreme case (see the dogfood note above).
      while IFS= read -r f; do
        [ -n "$f" ] || continue
        case " $protected " in *" $f "*) continue ;; esac
        to_quarantine+=("$f")
      done <<<"$current_dirty"
      if [ ${#to_quarantine[@]} -gt 0 ]; then
        local stash_msg="safety-snapshot: pre-reconcile quarantine (${count} autostash entries) — $(date -u +%Y-%m-%dT%H:%M:%SZ)"
        if git stash push -m "$stash_msg" -- "${to_quarantine[@]}" 2>/dev/null; then
          for f in "${to_quarantine[@]}"; do
            [ -n "$f" ] || continue
            if git cat-file -e "$branch:$f" 2>/dev/null; then
              git checkout "$branch" -- "$f" 2>/dev/null || true
            fi
          done
          echo "  ✓ current dirty tree quarantined; the next pull will start clean (no new autostash entry)." >&2
        fi
      fi
    fi
  fi
  return 0
}
