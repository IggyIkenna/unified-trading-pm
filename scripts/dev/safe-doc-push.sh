#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# safe-doc-push.sh -- contention-hardened commit+push for the pure-docs fast path.
#
# WHY THIS EXISTS (2026-08-01, live incident): quickmerge.sh carries ~2000 lines of
# hard-won contention handling (STAGE 0.4 behind-remote reconcile, autostash-pop-conflict
# recovery, sentinel-race backoff+jitter retries) built up over dozens of fixes -- see
# quickmerge_sentinel_race_retry_storm_under_pm_doc_push_contention_2026_07_21.md and its
# siblings. The CLAUDE.md-sanctioned "pure doc/plan-flip -> prek only" fast path (a direct
# git commit, skipping quickmerge/quality-gates.sh entirely for speed) has NONE of that --
# every agent re-improvises the same fetch/reconcile/stage-by-name/retry dance from
# scratch, in-context, burning tokens, every time it collides with another slot. Verified
# live: two concurrent Claude sessions sharing ONE slot's checkout raced on git
# add/commit/push for several minutes, losing an already-decided one-line edit to an
# autostash-pop sweep twice before it landed -- see
# autostash_pop_restores_foreign_wip_into_the_index_2026_07_17.md, which this script
# directly implements the decided fix from.
#
# WHAT THIS DOES (wraps the manual dance in one atomic, retrying command):
#   1. Fetch, then reconcile with whichever mechanism is actually free right now
#      (verified empirically 2026-08-01): a plain merge-pull is a TRUE no-cost
#      fast-forward pre-commit (zero local commits ahead of origin yet) REGARDLESS of
#      whether the named files overlap the incoming diff -- git's own merge machinery
#      already refuses cleanly on a real conflict, no custom overlap-check needed. Once
#      this script's own commit exists (post-commit, inside the retry loop below), a
#      plain merge is NOT free anymore (it would create a real 2-parent merge commit even
#      with zero content overlap, since FF-eligibility is a commit-graph property, not a
#      content one) -- so the retry path uses `pull --rebase --autostash` instead, paired
#      with an UNCONDITIONAL `git restore --staged .` immediately after the pop. That one
#      line is what makes the autostash-pop safe: it can only ever unstage (never touches
#      working-tree content, so it can't destroy anything), which guarantees the index
#      holds only what this script itself explicitly re-adds, regardless of what the pop
#      restaged from a concurrent process sharing this checkout.
#   2. Stage ONLY the caller-named files (never `git add -A`/`.`), then defensively
#      unstage anything else the index picked up -- this script assumes a concurrent
#      process sharing the same checkout WILL stage its own files into the same index
#      routinely, not as a rare edge case (observed live, repeatedly, 2026-08-01).
#   3. Commit, push, retry on transient failures with backoff+jitter (index.lock
#      contention, lost push race against a concurrent slot) -- hard-stop immediately on
#      a genuine content conflict (needs a human, not a robot retry) or a pre-commit hook
#      rejection unrelated to drift.
#
# USAGE:
#   bash scripts/dev/safe-doc-push.sh "<commit message>" --files "path1 path2 ..." [branch]
#   branch defaults to live-defi-rollout. Message becomes the full commit message.
#   Files must already be edited on disk (dirty working tree) before calling this --
#   same convention as `quickmerge.sh "msg" --agent --files '<paths>'`.
#
# SCOPE: pure documentation/plan changes ONLY. check_strict_quickmerge.py already exempts
# docs(plans): commits from the Quickmerge: trailer requirement (the "prek only" carve-out
# in CLAUDE.md's git-discipline section) -- this script is the hardened implementation of
# that carve-out. Do NOT use this for source/code changes: quality-gates.sh is mandatory
# there and this script never runs it. Run from the target repo's root.
#
# EXIT CODES: 0 success (incl. "nothing to commit" -- another slot already landed the
# identical content). 2 bad usage. 3 unresolved rebase conflict (real content collision,
# needs a human). 4 push rejected for a non-drift reason. 5 exhausted retries under
# sustained contention (transient -- just re-run). 6 commit rejected by a pre-commit hook
# for a DETERMINISTIC content reason (plan-hygiene, conflict markers, frontmatter schema,
# terminal-status-archived, ...) -- fix the content; re-running cannot help. Added
# 2026-08-08: exit 5 was previously returned for this case too, which told the next agent
# to retry something that could never succeed (see commit_failure_is_retriable below).

set -uo pipefail

MSG=""
BRANCH="live-defi-rollout"
FILES=()

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 \"<commit message>\" --files \"path1 path2 ...\" [branch]" >&2
  exit 2
fi
MSG="$1"
shift

while [[ $# -gt 0 ]]; do
  case "$1" in
    --files)
      shift
      # shellcheck disable=SC2206
      FILES=($1)
      shift
      ;;
    *)
      BRANCH="$1"
      shift
      ;;
  esac
done

if [[ ${#FILES[@]} -eq 0 ]]; then
  echo "Refusing: --files '<space-separated paths>' is required -- this script never stages by wildcard." >&2
  exit 2
fi

if [[ ! -d .git ]]; then
  echo "Refusing: run from a repo root (no .git here: $(pwd))." >&2
  exit 2
fi

# push-host-governor.sh (2026-08-09, cross-slot push contention): stubs defined FIRST so a
# missing/stale PM checkout can never break this script (no `set -e` here, but keep the same
# always-defined convention as quickmerge.sh for consistency) -- source only OVERRIDES them.
# This script's own header already requires "Run from the target repo's root", so cwd's parent
# is this host's workspace root (the sibling-repos layout every slot clone shares) -- same rule
# qg-host-governor.sh's _qg_shared_root and quickmerge.sh's WORKSPACE_ROOT both use.
push_gov_acquire_validate() { :; }
push_gov_release_validate() { :; }
push_gov_acquire_push() { :; }
push_gov_release_push() { :; }
_SDP_REPO_NAME="$(basename "$(pwd)")"
# WORKSPACE_ROOT (not a script-local name): push-host-governor.sh's _push_gov_shared_root
# reads this exact env var to find the host-shared lock dir -- must be set before sourcing.
WORKSPACE_ROOT="$(cd .. && pwd)"
_SDP_PUSH_GOV_FILE="$WORKSPACE_ROOT/unified-trading-pm/scripts/dev/push-host-governor.sh"
if [[ -f "$_SDP_PUSH_GOV_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$_SDP_PUSH_GOV_FILE"
fi

# Whole-run validation-phase gate (2026-08-09, operator ruling: "hardening safe-doc-push to
# look like quickmerge, just less tests, same concurrency rigor"): acquired HERE, covering the
# entire script from this point through the final exit, NOT just the commit-hook-chain call
# the way quickmerge.sh's own (narrower) use of this same gate does -- quickmerge already has a
# SEPARATE, per-repo-aware whole-run gate (qg-host-governor.sh's total-instance gate, PM<=4 /
# other repos<=1 / host-wide<=6) for its heavy QG phase, so widening ITS use of this gate too
# would double-count the same contention under two different caps. This script has no such
# gate of its own -- it IS the fast, low-resource docs path, so it gets its own flat K=8 budget
# (default; PUSH_GOV_VALIDATE_CONCURRENCY overrides), independent of and not competing with the
# quality-gates caps. Auto-releases on process exit if the script hits one of its many `exit N`
# paths before reaching the explicit release near EOF (see push-host-governor.sh's own header).
push_gov_acquire_validate

for f in "${FILES[@]}"; do
  if [[ ! -e "$f" ]]; then
    # Not on disk -- still acceptable if git knows this path, e.g. the source half of a
    # `git mv` rename (already gone from the index, since git mv folds it into the
    # destination's R100 status) or a plain staged deletion. Check both the index and
    # HEAD's tree so either shape passes.
    if ! git ls-files --error-unmatch -- "$f" >/dev/null 2>&1 && ! git cat-file -e "HEAD:$f" 2>/dev/null; then
      echo "Refusing: named path does not exist: $f" >&2
      exit 2
    fi
  fi
done

is_named() {
  local candidate="$1"
  local _f
  for _f in "${FILES[@]}"; do
    [[ "$candidate" == "$_f" ]] && return 0
  done
  return 1
}

# KNOWN_RENAME_SOURCES -- captured ONCE, right here, before the loop below (or any
# fetch/pull/rebase) touches the tree. This is the only point where the caller's staged
# rename is guaranteed to still be intact and unambiguous (a clean R100 pair). Every
# reconcile step downstream (merge-pull's own conflict handling, rebase, autostash
# pop-against-a-moved-HEAD) can decompose that pair into a staged ADD of the destination
# plus an UNSTAGED delete of the source -- observed live: when the concurrent commit that
# forces reconciliation ALSO touched the source path's content, the autostash pop can no
# longer cleanly re-apply the rename as one unit, so the deletion half comes back unstaged
# instead of re-detectable via `git diff --cached -M`. Capturing once up front and
# reasserting unconditionally before every commit sidesteps re-detecting a rename whose
# staged shape is not guaranteed to survive reconciliation.
KNOWN_RENAME_SOURCES=()
while IFS=$'\t' read -r _status _src _dst; do
  [[ -z "$_status" ]] && continue
  case "$_status" in
    R*)
      if is_named "$_dst"; then
        KNOWN_RENAME_SOURCES+=("$_src")
      fi
      ;;
  esac
done < <(git diff --cached --name-status -M 2>/dev/null)

# reassert_renames -- re-stage the deletion of every KNOWN_RENAME_SOURCES path that is
# currently missing from disk, regardless of whether the index still shows it as a clean
# staged rename, an unstaged delete, or nothing at all (a `git restore --staged .` resets
# the index to match HEAD but never touches the working tree, so the source's absence from
# disk survives every reconcile step even when its staged/unstaged shape does not).
# `git add -- <path>` correctly stages a deletion for a path that is tracked but missing
# from the working tree (default behaviour since git 2.0 for an EXPLICITLY named path) --
# this is what actually lands the deletion in the next commit, whatever state it was in.
reassert_renames() {
  [[ ${#KNOWN_RENAME_SOURCES[@]} -eq 0 ]] && return 0
  local src
  for src in "${KNOWN_RENAME_SOURCES[@]}"; do
    if [[ -e "$src" ]]; then
      # Source is back on disk (e.g. a concurrent process restored it) -- not our rename
      # to finish; leave it alone rather than guess.
      continue
    fi
    echo "  -> re-staging deletion of rename source (would otherwise leave the doc at both paths): $src"
    git add -- "$src" 2>/dev/null || true
  done
}

# Pre-commit hooks whose failure is a genuine RACE against a concurrent slot -- the retry
# loop's own fetch+pull clears them, so retrying is correct. Everything else is a
# DETERMINISTIC content failure that will fail identically on all 6 attempts.
RETRIABLE_HOOK_IDS="check-branch-drift"

# commit_failure_is_retriable <err-file> -- classify a `git commit` rejection.
#
# Bug fixed 2026-08-08: this script previously funnelled EVERY commit failure into
# backoff+continue, so a deterministic pre-commit content failure (plan-hygiene conflict
# markers / frontmatter schema / terminal-status-archived / todo format / line caps) was
# retried 6 times and then reported as "Exhausted N attempts under sustained contention --
# this is transient, not a defect. Re-run." That message is actively harmful: it is wrong,
# it buries the hook's own actionable remedy under 6 repetitions, it costs ~6 full prek runs,
# and it tells the next agent to re-run something that cannot succeed. Measured live during
# the 2026-08-08 sports canonicalisation push (a stale conflict marker + a terminal-status
# archival violation, both reported as "transient contention"). The script's own header has
# ALWAYS documented the intended behaviour -- "hard-stop immediately on ... a pre-commit hook
# rejection unrelated to drift" -- it was simply never implemented.
#
# NOT a fleet-wide defect: `quickmerge.sh` (this script's 2000-line hardened sibling) has
# always got this right -- see its "Distinguish a branch-drift RACE (retryable) from a
# genuine content-level pre-commit failure (lint/type/etc -- pulling can never fix this, so
# fail fast, never loop blindly)" block, which exits 1 with an actionable remedy when
# `behind == 0`. This script was extracted 2026-08-01 as the pure-docs fast path and simply
# did not carry that logic across. Checked 2026-08-08; quickmerge needs no change.
#
# Classification is by prek's own `- hook id: <id>` lines, not by message text: if every
# failing hook is in RETRIABLE_HOOK_IDS it is a race (retry); if ANY other hook failed it is
# deterministic (fail fast). This is strictly more precise than quickmerge's behind-count
# heuristic, which needs one extra loop to converge when drift and a content failure
# coincide. A commit rejection with no parseable hook id is treated as retriable, preserving
# the old behaviour for genuinely unknown/racy failures.
# Returns 0 = retriable, 1 = deterministic.
commit_failure_is_retriable() {
  local err_file="$1" hook_ids id
  hook_ids="$(sed -n 's/^- hook id: //p' "$err_file" 2>/dev/null || true)"
  [[ -z "$hook_ids" ]] && return 0
  while IFS= read -r id; do
    [[ -z "$id" ]] && continue
    if [[ " $RETRIABLE_HOOK_IDS " != *" $id "* ]]; then
      return 1
    fi
  done <<<"$hook_ids"
  return 0
}

unstage_foreign_paths() {
  local staged f
  staged="$(git diff --cached --name-only)"
  [[ -z "$staged" ]] && return 0
  while IFS= read -r f; do
    [[ -z "$f" ]] && continue
    if ! is_named "$f"; then
      echo "  -> unstaging foreign path picked up from a concurrent process sharing this checkout: $f"
      git restore --staged -- "$f"
    fi
  done <<<"$staged"
}

# autostash_rebase_reconcile -- `git pull --rebase --autostash` PLUS verification that the
# autostash actually popped. Bug fixed 2026-08-08 (see
# autostash_pop_can_silently_discard_uncommitted_foreign_edits_2026_08_07.md): under heavy
# contention, git's own post-rebase autostash pop can itself fail/conflict without failing the
# overall `pull --rebase` command -- the rebase succeeds, but the caller's pre-existing edits
# stay parked in refs/stash instead of landing back in the working tree. The old code's blind
# `git restore --staged .` right after did nothing to detect this: with the edits still in the
# stash, `git add` stages nothing, the "already matches HEAD" heuristic below is satisfied on a
# false premise, and the script reports success while silently dropping the whole commit.
# Returns 0 on success (rebase done, any autostash cleanly restored or none existed).
# Returns 1 on failure -- caller should treat this as "needs a human", same as a rebase conflict.
autostash_rebase_reconcile() {
  local before_stash after_stash
  before_stash="$(git rev-parse -q --verify refs/stash 2>/dev/null || echo none)"
  if ! git pull --rebase --autostash origin "$BRANCH" -q 2>/tmp/_sdp_rebase_err; then
    git rebase --abort 2>/dev/null || true
    echo "  rebase conflicted -- this is a genuine content collision, not contention. Resolve manually:" >&2
    cat /tmp/_sdp_rebase_err >&2
    return 1
  fi
  after_stash="$(git rev-parse -q --verify refs/stash 2>/dev/null || echo none)"
  if [[ "$after_stash" != "$before_stash" ]]; then
    echo "  autostash did not auto-pop (a new stash entry is still present after the rebase) -- attempting an explicit pop"
    if ! git stash pop -q 2>/tmp/_sdp_stash_pop_err; then
      echo "  explicit stash pop ALSO failed -- this is a genuine unresolved conflict, not contention:" >&2
      cat /tmp/_sdp_stash_pop_err >&2
      echo "  your edits are safe in the stash (run 'git stash list' to find them) -- resolve manually." >&2
      return 1
    fi
    echo "  explicit pop succeeded -- edits restored to the working tree"
  fi
  git restore --staged . 2>/dev/null || true
  return 0
}

backoff() {
  local attempt="$1"
  sleep "$((1 + RANDOM % 3 + attempt))"
}

# locked_git_commit -- serialise `git commit` (which runs the prek/pre-commit hook chain
# synchronously) against any OTHER concurrent commit in this SAME checkout, in this or any
# other process (e.g. quickmerge.sh, which wraps its own commit calls the same way).
# prek_stash_restore_race_destroys_shared_checkout_wip_2026_08_08: prek stashes unstaged
# changes to a patch at hook-batch START and restores it at the END; two overlapping
# `git commit` calls in one checkout can interleave those windows, and the first session's
# restore silently reverts a second session's newer edit to HEAD -- no error, no conflict
# marker, no stash entry to recover from. A flock scoped to this checkout's .git dir closes
# the interleaving window without touching prek itself. Mirrors the existing cascade-lock
# convention elsewhere in this repo (quickmerge.sh's flock around its ancestor-checkout
# critical section) -- same FD-open/flock/unlock/FD-close shape, same graceful degrade to
# unlocked if flock(1) is unavailable. Held ONLY around the single `git commit` call below,
# never across this script's own attempt loop, so a retry re-acquires+releases cleanly each
# time -- no self-deadlock on this script's own retries.
# _prek_race_snapshot -- checksum every already-unstaged file (working tree vs index) right
# before a `git commit` call, i.e. exactly the set prek's own stash captures at hook-batch
# start. Emits one "<path>\t<hash>" line per file to stdout.
_prek_race_snapshot() {
  local f
  git diff --name-only 2>/dev/null | while IFS= read -r f; do
    [[ -z "$f" || ! -f "$f" ]] && continue
    printf '%s\t%s\n' "$f" "$(git hash-object -- "$f" 2>/dev/null)"
  done
}

# _prek_race_check -- compare a snapshot from _prek_race_snapshot against the CURRENT state.
# prek_stash_restore_race_destroys_shared_checkout_wip_2026_08_08 (todo 3, "make the loss
# loud"): a changed checksum here means a file that already had unstaged WIP before this
# commit call now holds DIFFERENT content -- the silent-revert signature (a concurrent
# session's prek restore reinstating a stale patch over a newer edit). Prints the changed
# paths and returns 1 when any are found; there is no safe auto-fix (we don't know which
# version is "right", and must never overwrite foreign WIP), so the caller hard-stops.
_prek_race_check() {
  local before="$1" path hash_before hash_after changed=()
  while IFS=$'\t' read -r path hash_before; do
    [[ -z "$path" ]] && continue
    if [[ -f "$path" ]]; then
      hash_after="$(git hash-object -- "$path" 2>/dev/null)"
    else
      hash_after="__deleted__"
    fi
    [[ "$hash_after" != "$hash_before" ]] && changed+=("$path")
  done <<<"$before"
  if [[ ${#changed[@]} -gt 0 ]]; then
    printf '%s\n' "${changed[@]}"
    return 1
  fi
  return 0
}

locked_git_commit() {
  local lock_fd=222 lock_file rc before_snapshot race_files
  lock_file="$(git rev-parse --git-dir 2>/dev/null)/quickmerge-commit.lock"
  before_snapshot="$(_prek_race_snapshot)"
  # push-host-governor.sh (2026-08-09): host-wide validation-phase token (K=8 default) around
  # the hook-chain-running commit call, nested OUTSIDE the pre-existing per-checkout flock below
  # (same split as quickmerge.sh's _qm_locked_git_commit).
  push_gov_acquire_validate
  if [[ -z "$lock_file" || "$lock_file" == "/quickmerge-commit.lock" ]]; then
    git commit "$@"
    rc=$?
  elif command -v flock >/dev/null 2>&1 && eval "exec ${lock_fd}>\"\$lock_file\"" 2>/dev/null; then
    flock "$lock_fd"
    git commit "$@"
    rc=$?
    flock -u "$lock_fd" 2>/dev/null || true
    eval "exec ${lock_fd}>&-" 2>/dev/null || true
  else
    git commit "$@"
    rc=$?
  fi
  push_gov_release_validate
  if [[ -n "$before_snapshot" ]] && ! race_files="$(_prek_race_check "$before_snapshot")"; then
    echo "❌ prek stash/restore race detected — these unstaged file(s) changed content DURING the commit (not something this script did):" >&2
    echo "$race_files" | sed 's/^/  - /' >&2
    echo "  A concurrent commit's prek restore likely reinstated a stale snapshot over a newer edit." >&2
    echo "  See plans/active/issues/prek_stash_restore_race_destroys_shared_checkout_wip_2026_08_08.md — do NOT re-run blindly; inspect the file(s) above (git diff / reflog on whoever owns that edit) before continuing." >&2
    return 1
  fi
  return "$rc"
}

MAX_ATTEMPTS=6
committed=false
final_ok=false

# push-host-governor.sh (2026-08-09): the whole retry loop below IS this script's git-remote
# critical section (fetch -> reconcile -> commit -> push) -- acquire the per-repo+branch mutex
# once, outside the loop, so this script's own retries never contend with THEMSELVES, and so
# every fetch/rebase/push attempt inside sees a base no other slot is concurrently mutating.
# Released once, right after the loop, on success or exhausted-retries alike; a hard `exit`
# from inside the loop (rebase conflict, non-drift push failure, a deterministic hook
# rejection) auto-releases via the OS closing the FD on process death.
push_gov_acquire_push "$_SDP_REPO_NAME" "$BRANCH"

for attempt in $(seq 1 "$MAX_ATTEMPTS"); do
  echo "── attempt ${attempt}/${MAX_ATTEMPTS} ──"

  if ! git fetch -q origin "$BRANCH" 2>/tmp/_sdp_fetch_err; then
    echo "  fetch failed, retrying:"; cat /tmp/_sdp_fetch_err
    backoff "$attempt"
    continue
  fi

  if [[ "$committed" == false ]]; then
    ahead="$(git rev-list --count "origin/${BRANCH}..HEAD" 2>/dev/null || echo 0)"

    if [[ "$ahead" -eq 0 ]]; then
      # Pre-commit case: a plain merge-pull is a true no-cost fast-forward here,
      # regardless of file overlap -- git refuses cleanly on a real conflict.
      if ! git pull origin "$BRANCH" --no-edit -q 2>/tmp/_sdp_pull_err; then
        if grep -qiE "divergent branches|would be overwritten|Please commit your changes|Need to specify how to reconcile" /tmp/_sdp_pull_err; then
          echo "  merge-pull can't fast-forward (real divergence) -- falling back to rebase+autostash"
          if ! autostash_rebase_reconcile; then
            exit 3
          fi
        else
          echo "  pull failed:"; cat /tmp/_sdp_pull_err
          backoff "$attempt"
          continue
        fi
      fi
    else
      # Defensive: shouldn't normally happen pre-commit, but handle the same as the
      # post-commit case if it does (e.g. a prior failed attempt left a local commit).
      if ! autostash_rebase_reconcile; then
        exit 3
      fi
    fi

    git add -- "${FILES[@]}"
    unstage_foreign_paths
    reassert_renames

    if ! git diff --cached --quiet -- "${FILES[@]}"; then
      : # there is something to commit
    else
      echo "  nothing staged for the named files -- checking if content already matches HEAD"
      if git diff --quiet -- "${FILES[@]}" 2>/dev/null; then
        echo "✅ Named files already match HEAD (a concurrent session landed identical content) -- treating as success."
        final_ok=true
        break
      fi
    fi

    if ! locked_git_commit -q -m "$MSG" 2>/tmp/_sdp_commit_err; then
      if grep -qi "nothing to commit" /tmp/_sdp_commit_err; then
        echo "✅ Nothing to commit -- already landed. Treating as success."
        final_ok=true
        break
      fi
      if grep -qi "index.lock" /tmp/_sdp_commit_err; then
        echo "  index.lock contention (another process is writing this instant) -- short wait, retry"
        sleep 2
        continue
      fi
      if grep -qi "prek stash/restore race detected" /tmp/_sdp_commit_err; then
        # prek_stash_restore_race_destroys_shared_checkout_wip_2026_08_08 (todo 3): a
        # DETECTED silent revert, not contention -- retrying only invites another race on
        # the same file. Hard-stop with the diagnosis locked_git_commit already printed.
        echo >&2
        cat /tmp/_sdp_commit_err >&2
        exit 7
      fi
      if ! commit_failure_is_retriable /tmp/_sdp_commit_err; then
        {
          echo
          echo "❌ COMMIT REJECTED BY A PRE-COMMIT HOOK -- this is a DETERMINISTIC content failure, NOT contention."
          echo "   Retrying will fail identically. Do NOT re-run this script until the content is fixed."
          echo "   Failing hook(s): $(sed -n 's/^- hook id: //p' /tmp/_sdp_commit_err | paste -sd', ' -)"
          echo "   The hook's own output (its remedy line is the thing to act on):"
          echo
          cat /tmp/_sdp_commit_err
        } >&2
        exit 6
      fi
      echo "  commit blocked by a retriable hook (branch drift re-detected mid-race) -- reconciling and retrying:"
      cat /tmp/_sdp_commit_err
      backoff "$attempt"
      continue
    fi
    committed=true
  fi

  if git push origin "HEAD:${BRANCH}" 2>/tmp/_sdp_push_err; then
    echo "✅ Pushed $(git rev-parse --short HEAD) -> ${BRANCH}"
    final_ok=true
    break
  fi

  if grep -qiE "non-fast-forward|rejected|fetch first" /tmp/_sdp_push_err; then
    echo "  origin moved during this attempt -- reconciling (post-commit: rebase+autostash) and retrying"
    if ! autostash_rebase_reconcile; then
      exit 3
    fi
    backoff "$attempt"
    continue
  fi

  echo "❌ Push failed for a non-drift reason:"; cat /tmp/_sdp_push_err >&2
  exit 4
done
push_gov_release_push

if [[ "$final_ok" != true ]]; then
  {
    echo "❌ Exhausted ${MAX_ATTEMPTS} attempts. Deterministic pre-commit content failures now exit 6 BEFORE"
    echo "   reaching here, so this path means a genuine race (fetch/pull/push contention) that did not settle."
    echo "   Re-running is reasonable -- but READ the last error below first rather than assuming transience:"
    echo
    for _last in /tmp/_sdp_commit_err /tmp/_sdp_push_err /tmp/_sdp_pull_err /tmp/_sdp_fetch_err; do
      if [[ -s "$_last" ]]; then
        echo "   --- last ${_last##*/_sdp_} ---"
        sed 's/^/   /' "$_last"
      fi
    done
  } >&2
  exit 5
fi
