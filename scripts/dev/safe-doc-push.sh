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
# EXIT CODE 10 (2026-08-10, pm_repo_commit_rate_exceeds_precommit_hook_duration): retries were
# exhausted AND the caller's named files no longer match what they handed this script -- their
# edits were reverted mid-run (measured twice on 2026-08-10). Distinct from 5 precisely because
# the remedy is opposite: 5 means "re-run, your content is intact"; 10 means "RECOVER FIRST, a
# re-run would push whatever is on disk now". See _sdp_warn_if_content_vanished.
#
# EXIT CODES: 0 success -- verified end-to-end (incl. "nothing to commit" -- another slot
# already landed the identical content; every success path, including that fallback, only
# reports 0 after independently confirming `git log --oneline -1 -- <path>` is non-empty for
# every named file and, post-push, that `git branch -r --contains HEAD` includes the target
# branch -- see verify_committed/verify_pushed below). 2 bad usage. 3 unresolved rebase
# conflict (real content collision, needs a human). 4 push rejected for a non-drift reason, OR
# `git push` exited 0 but verify_pushed found origin/<branch> does not actually contain HEAD.
# 5 exhausted retries under sustained contention (transient -- just re-run). 6 commit rejected by a pre-commit hook
# for a DETERMINISTIC content reason (plan-hygiene, conflict markers,
# frontmatter schema, terminal-status-archived, ...) -- fix the content; re-running cannot
# help -- OR `git commit` exited 0 but verify_committed found no commit reachable from HEAD
# touching a named file (a stubbed/mocked commit call, or a deeper git-state anomaly; added
# 2026-08-09, safe_doc_push_reports_success_having_committed_nothing_2026_08_09 todo 2). Added
# 2026-08-08: exit 5 was previously returned for this case too, which told the next agent
# to retry something that could never succeed (see commit_failure_is_retriable below). 8 this
# checkout is under SUSTAINED FOREIGN WRITE -- LOCK_CONTENTION_MAX consecutive index.lock
# failures (on either `git add` or `git commit`) before MAX_ATTEMPTS is even reached.
# Retrying in place cannot converge while a peer process keeps re-taking the lock faster than
# this script's own retries clear it -- the script prints a documented escape hatch (land the
# named files from a separate clone, what unblocked the incident this todo comes from) instead
# of looping to MAX_ATTEMPTS and reporting a generic "transient, re-run" message. Added
# 2026-08-09, safe_doc_push_reports_success_having_committed_nothing_2026_08_09 todo 4. 9 the
# push succeeded (final_ok=true) but this run leaves behind an orphaned
# `~/.cache/prek/patches/*.patch` file created since this script started -- prek's own
# patch-based stash/restore of unstaged out-of-scope edits normally cleans itself up around
# every hook run; a patch still sitting there after a successful push means some restore step
# never happened, which is exactly the silent-data-loss signature this immediate safety net
# exists to catch loudly instead of letting it pass as an unremarked exit 0 (see
# safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09.md). The push itself already
# landed -- inspect the listed patch file(s) before assuming loss (their content may already be
# back in the working tree), do not delete them until confirmed safe. Added 2026-08-10.
# 12 every named file was ALREADY byte-identical to HEAD before this script touched anything,
# so this run had nothing of yours to ship and cannot certify that what is in HEAD is what you
# intended. Previously this exited 0 with "✅ Named files already match HEAD (a concurrent
# session landed identical content)" -- measured 2026-08-10 reporting exactly that for a todo
# whose content had been destroyed before the script hashed it. The two causes ("a peer landed
# it first" / "your edit was reverted first") are indistinguishable from inside this process,
# so it resolves to neither; the message prints the command that tells them apart. Set
# SDP_ALLOW_NOOP=1 to accept it as a deliberate idempotent re-run. 13 the push landed but a
# named file that HAD a real diff at entry is still byte-identical to the PRE-RUN HEAD -- your
# change is not in the commit that shipped (measured twice 2026-08-10, once with the file left
# dirty on disk so no revert-detection could have caught it). Recover per the printed guidance;
# a bare re-run may or may not re-land it depending on which of the two shapes occurred.
#
# ON PREK'S OWN PATCH RESTORE RELIABILITY (2026-08-10, re-scoped per
# safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09.md todo 3): the live
# incident that motivated exit code 9 above was originally suspected to be a prek-level defect
# -- patch restore wired only to the FIRST hook invocation of a `git commit` call, dropped on
# an internal same-process retry. A deliberate reproduction (prek 0.4.12, a hook that fails
# once then passes, an unrelated unstaged edit present throughout, run both with and without an
# inter-attempt delay) could NOT reproduce that failure mode: prek printed a matching
# save/restore pair around every sequential `git commit` invocation and the unrelated edit
# survived intact every time. Do not file this upstream against prek -- there is no confirmed
# defect to file. The actual risk is the cross-process race documented in
# prek_stash_restore_race_destroys_shared_checkout_wip_2026_08_08.md (a CONCURRENT process
# sharing this checkout interleaves its own prek stash/restore window with this script's),
# which is what the checksum safety net below (_prek_race_snapshot/_prek_race_check, inside
# locked_git_commit) already guards against, independent of root cause.

set -uo pipefail

# _SDP_RUN_START_EPOCH -- captured as the very first thing after set -uo pipefail, before any
# fetch/pull/commit (i.e. before prek could possibly create a patch as part of THIS run).
# check_orphaned_prek_patches (near EOF) compares every *.patch file's mtime against this to
# tell "created during this run" apart from a pre-existing orphan from some earlier, unrelated
# session -- this script only warns about patches IT could plausibly be responsible for.
_SDP_RUN_START_EPOCH="$(date +%s)"
# Absolute path of THIS script, resolved before any `cd`, so isolated mode can re-exec
# exactly the code the caller invoked rather than the worktree checkout's copy.
_SDP_SELF="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)/$(basename "${BASH_SOURCE[0]}")"

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

# NOTE (2026-08-10): `.git` is a DIRECTORY in a normal clone but a FILE in a linked
# worktree (`gitdir: ...`), so the original `[[ ! -d .git ]]` refused to run anywhere
# inside a worktree. That silently broke the isolated-worktree mode added the same day
# -- the parent set the worktree up correctly, re-exec'd this script inside it, and the
# child exited 2 ("not a repo root"), so EVERY invocation failed. Caught by the
# concurrency harness (scripts/dev/test-safe-doc-push-concurrency.sh), which runs its
# workers from a worktree and saw 6/6 rc=2 before this fix. Ask git what the root is
# instead of pattern-matching the filesystem, and require that we are AT that root.
_sdp_toplevel="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "$_sdp_toplevel" ]]; then
  echo "Refusing: not inside a git working tree ($(pwd))." >&2
  exit 2
fi
if [[ "$(pwd -P)" != "$(cd "$_sdp_toplevel" && pwd -P)" ]]; then
  echo "Refusing: run from the repo root ($_sdp_toplevel), not $(pwd)." >&2
  exit 2
fi

# pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10 (F4): fingerprint the caller's
# named files AT ENTRY so a non-success exit can tell "your content is still on disk, this really
# was transient" apart from "your edits were reverted out from under you". Measured twice on
# 2026-08-10: an exhausted-retries run printed "this is transient, not a defect. Re-run." while the
# caller's uncommitted TRACKED file had been reverted to HEAD content by an autostash/prek cycle
# (untracked files in the same --files list survived). An agent that believes that message re-runs
# and pushes nothing. Content was recoverable from stash@{0} both times, but only by going to look.
# ---------------------------------------------------------------------------
# ISOLATED-WORKTREE MODE (default since 2026-08-10) --
# pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md F6 + the operator
# ruling the same day ("we should do these because it's never gonna get better otherwise").
#
# WHY: every remaining data-loss mode in that doc is a property of the SHARED INDEX, not of
# this script's logic. A peer session dirties the checkout; prek saves those unstaged files
# to a patch, runs the hook chain, and on restore-conflict reverts the hook's own autofix
# ("Hook changes conflicted with the saved unstaged changes"); autostash push/pop pairs from
# two processes interleave so the wrong entry is popped. Measured 2026-08-10: the caller's
# uncommitted edits were destroyed THREE times in one session -- twice by this script, once
# by quickmerge.sh -- and one recovery came back a PARTIAL, earlier version. No amount of
# in-place hardening fixes this: the hazard is that two processes share one index.
#
# WHAT: stage+commit in a throwaway `git worktree` checked out at origin/<branch>, into which
# we COPY the caller's named files. Consequences that matter:
#   - This script no longer writes to the caller's working tree AT ALL, so it cannot destroy
#     their edits. The original files stay exactly where the caller left them, whatever happens.
#   - prek's patch save/restore only ever sees our own files -- no foreign unstaged WIP to
#     conflict with, so the F6 revert-and-rerun loop cannot form.
#   - The worktree starts AT origin/<branch>, so it is never "behind" -> the drift gate is
#     satisfied structurally, and prettier-autostage stops declining to format (F3).
# The worktree leaf is named `unified-trading-pm` deliberately: 13 call sites across 11
# quality_gates scripts resolve the PM root as `<workspace>/unified-trading-pm`, so any other
# name makes them report a path failure AS A CONTENT VIOLATION (F7). Fixing those is F7's own
# todo; naming the leaf correctly side-steps it for this path today.
#
# Escape hatch: SDP_ISOLATED=0 restores the legacy shared-index behaviour (this is the
# DOCUMENTED escape hatch per safe_doc_push_isolation_rewrites_slot_commit_identity_2026_08_10).
# The default isolated-worktree mode now propagates the caller's slot identity into the worktree
# (see the isolation branch below), so SDP_ISOLATED=0 is only needed to force the shared index
# (e.g. a worktree-add failure). On ANY setup failure we fall back to the legacy path rather
# than refusing to push -- degraded, never blocked.
_SDP_ISOLATION_ROOT=""
_sdp_cleanup_isolation() {
  [[ -z "$_SDP_ISOLATION_ROOT" ]] && return 0
  local wt="${_sdp_iso_wt:-$_SDP_ISOLATION_ROOT/unified-trading-pm}"
  git worktree remove --force "$wt" 2>/dev/null || true
  git worktree prune 2>/dev/null || true
}

# Depth guard (defense in depth, 2026-08-10). The env-var handshake below is the PRIMARY
# recursion stop; this is the backstop for when that handshake breaks. It broke once already:
# a comment placed between a trailing `\` and the `bash` call silently detached the env
# assignments, so the child re-entered isolation forever -- 116 nested invocations and 721
# stray worktrees from a single 6-worker test run before it was killed by hand. A counter that
# survives any env-propagation bug is the only thing that bounds that blast radius.
_SDP_ISO_DEPTH="${SDP_ISO_DEPTH:-0}"
if [[ "$_SDP_ISO_DEPTH" -ge 1 ]]; then
  if [[ -z "${SDP_IN_ISOLATION:-}" ]]; then
    echo "❌ isolation recursion detected (depth=$_SDP_ISO_DEPTH) — the SDP_IN_ISOLATION handshake is broken." >&2
    echo "   Refusing to nest further. This is a defect in this script, not in your invocation." >&2
    exit 11
  fi
fi

# HOST GATE (2026-08-10, operator ruling — same rule quickmerge already applies).
# Isolation defends against ONE hazard: two processes sharing a single checkout, whose prek
# patch save/restore and autostash push/pop interleave and silently revert the loser's
# uncommitted edits. That needs a SHARED INDEX. It is a laptop condition — interactive sessions
# have no allocation mechanism and routinely share a .tabs/N checkout. On the agent-orchestrator
# VM the dispatcher runs ONE task per slot and each slot is its own clone, so there is no second
# writer and isolation buys nothing while costing a full ~7,155-file worktree checkout on EVERY
# doc push (and AO's doc pushes are constant — every checkbox flip is one).
#
# What the VM does NOT lose by turning this off: isolation never addressed push contention on
# the shared branch, which is the race AO actually has. That is handled by the per-repo+branch
# push mutex, the rebase-and-retry loop, the advisory drift gate (which removed the livelock),
# and the exit-10 content-vanished guard — all host-independent and all still active here.
#
# Host label reuses slot-identity-lib.sh's existing signal rather than inventing one.
_sdp_host_label() {
  local h="${ORCHESTRATOR_VM_ID:-${VM_NAME:-$(git config --global slotIdentity.host 2>/dev/null || true)}}"
  echo "${h:-laptop}"
}
_sdp_isolation_default() { [[ "$(_sdp_host_label)" == "laptop" ]] && echo 1 || echo 0; }
_SDP_ISOLATED_EFFECTIVE="${SDP_ISOLATED:-$(_sdp_isolation_default)}"

# After an isolated push, a file that was UNTRACKED in the caller's tree is now tracked on
# origin -- while the caller still has an untracked file sitting at that same path. The next
# `git pull` / `git merge --ff-only` then refuses with "The following untracked working tree
# files would be overwritten by merge ... Please move or remove them", which READS LIKE A
# CONFLICT and is not one. Reported live on 2026-08-10 by a peer session, minutes after
# isolation shipped: "trivial once understood, but the failure mode reads like a real conflict
# at first glance."
#
# Remove ONLY the provably redundant copies -- untracked here AND byte-identical to the blob
# that just landed. A copy that DIFFERS is left exactly where it is and warned about: it is
# newer content, and this script's whole premise is that it never destroys what it did not
# write. (Byte-identity is checked against the pushed blob, not assumed from the fact that we
# copied the file in: the caller may have edited it while the child was running.)
_sdp_reconcile_caller_duplicates() {
  local f blob_local blob_remote removed=0
  for f in "${FILES[@]}"; do
    [ -f "$f" ] || continue
    # Only an UNTRACKED file can produce the ff-only "would be overwritten" refusal.
    [ -z "$(git ls-files -- "$f" 2>/dev/null)" ] || continue
    # The worktree shares this repo's object store and refs, so the child's push already
    # advanced origin/<branch> here -- no fetch needed. If it does not resolve, do nothing.
    blob_remote="$(git rev-parse -q --verify "origin/${BRANCH}:${f}" 2>/dev/null)" || continue
    [ -n "$blob_remote" ] || continue
    blob_local="$(git hash-object -- "$f" 2>/dev/null)"
    if [ "$blob_local" = "$blob_remote" ]; then
      rm -f -- "$f" && removed=$((removed + 1))
      echo "  ✓ removed now-redundant untracked copy of $f — identical to what landed; it arrives TRACKED on your next ff-pull"
    else
      echo "  ⚠ $f is untracked here and DIFFERS from what landed — left in place. A following ff-pull will refuse to overwrite it; that is a stale duplicate, NOT a conflict: move it aside, pull, then re-apply." >&2
    fi
  done
  [ "$removed" -gt 0 ] && echo "  (isolated mode commits from a private checkout, so a NEW file never becomes tracked in your own tree)"
  return 0
}

if [[ "$_SDP_ISOLATED_EFFECTIVE" != "0" && -z "${SDP_IN_ISOLATION:-}" ]]; then
  _sdp_iso_parent="${TMPDIR:-/tmp}/sdp-iso-$$"
  _sdp_origin_repo="$(pwd)"
  # Propagate the CALLER's slot identity into the isolated worktree path
  # (safe_doc_push_isolation_rewrites_slot_commit_identity_2026_08_10, confirmed live slot 31).
  # fix-commit-identity.sh derives the label PURELY from the PATH: an isolated worktree at
  # $TMPDIR/sdp-iso-$$/unified-trading-pm (no `.tabs/<N>/` segment) resolves `main` and actively
  # REWRITES a slot worker's `[slot-N·host]` author to `[main·host]`. Build the worktree path WITH
  # the caller's `.tabs/<N>/` segment (leaf dir stays `unified-trading-pm` — F7 requires that name)
  # so the hook derives the caller's label and no-ops (commit lands on the FIRST attempt with the
  # correct author). The identity lib path is derived relative to THIS script (which always has
  # access to it); the label resolves against the caller repo path.
  _sdp_identity_lib="$(dirname "$_SDP_SELF")/../hooks/slot-identity-lib.sh"
  _sdp_slot_seg=""
  if [ -f "$_sdp_identity_lib" ]; then
    # shellcheck disable=SC1090
    . "$_sdp_identity_lib"
    slot_identity_resolve "$_sdp_origin_repo"
    if [[ "${SLOT_ID_LABEL:-main}" =~ ^slot-([0-9]+)$ ]]; then
      _sdp_slot_seg="/.tabs/${BASH_REMATCH[1]}"
    fi
  fi
  _sdp_iso_wt="$_sdp_iso_parent${_sdp_slot_seg}/unified-trading-pm"
  if git fetch -q origin "$BRANCH" 2>/dev/null &&
    git worktree add --detach -q "$_sdp_iso_wt" "origin/$BRANCH" 2>/dev/null; then
    _SDP_ISOLATION_ROOT="$_sdp_iso_parent"
    trap _sdp_cleanup_isolation EXIT
    _sdp_copy_ok=true
    for _f in "${FILES[@]}"; do
      if [[ ! -f "$_f" ]]; then
        # A named path absent from the caller tree but PRESENT at origin/$BRANCH is a DELETION
        # (the normal case: a plan archived with `git mv`), NOT a caller typo. Propagate it by
        # removing it from the worktree -- `git add -- <path>` then stages the deletion, exactly
        # as documented below for tracked-but-missing paths.
        #
        # Without this, an archival move landed its ADD and silently dropped its DELETE, and the
        # push still reported success. Measured 2026-08-10: a resolved issue stayed in
        # plans/active/ alongside its archived copy, where AO would have kept dispatching it.
        # Archiving a completed plan is a mandated routine operation, so this misfired quietly
        # every time anyone did it from isolated mode.
        if git rev-parse -q --verify "origin/${BRANCH}:${_f}" >/dev/null 2>&1; then
          if rm -f -- "$_sdp_iso_wt/$_f"; then
            echo "  isolation: propagating deletion of $_f (absent here, tracked on origin/$BRANCH)"
          else
            echo "  isolation: could not propagate deletion of $_f" >&2
            _sdp_copy_ok=false
          fi
          continue
        fi
        # A named path absent from the caller tree AND absent from origin/$BRANCH is neither a
        # deletion (nothing to propagate) nor a copy (nothing to copy) -- it is a caller error:
        # the path exists nowhere this push could stage it from. Fail loudly with the path
        # named; a silent continue here drops the path from the commit while still reporting
        # success (the create-only archival class this issue documents). Same shape the
        # shared-index path rejects with exit 2 ("Refusing: named path does not exist").
        echo "  isolation: FAILED: named path exists in neither the caller tree nor origin/$BRANCH: $_f" >&2
        exit 2
      fi
      mkdir -p "$_sdp_iso_wt/$(dirname "$_f")" 2>/dev/null || true
      cp "$_f" "$_sdp_iso_wt/$_f" || _sdp_copy_ok=false
    done
    if [[ "$_sdp_copy_ok" == true ]]; then
      echo "🔒 isolated-worktree mode: committing from a private index at origin/$BRANCH"
      echo "   (your working tree is NOT touched by this script — see F6 in"
      echo "    plans/active/issues/pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md)"
      # Belt-and-suspenders: also pre-stamp the worktree config so the hook no-ops even if the
      # inherited caller config is stale (the PATH-derived label now matches by construction).
      if [ -n "${SLOT_ID_EXPECTED_NAME:-}" ] && [ -n "${SLOT_ID_CANON_EMAIL:-}" ]; then
        git -C "$_sdp_iso_wt" config extensions.worktreeConfig true 2>/dev/null || true
        git -C "$_sdp_iso_wt" config --worktree user.name "$SLOT_ID_EXPECTED_NAME" 2>/dev/null \
          || git -C "$_sdp_iso_wt" config user.name "$SLOT_ID_EXPECTED_NAME"
        git -C "$_sdp_iso_wt" config --worktree user.email "$SLOT_ID_CANON_EMAIL" 2>/dev/null \
          || git -C "$_sdp_iso_wt" config user.email "$SLOT_ID_CANON_EMAIL"
      fi
      cd "$_sdp_iso_wt" || exit 2
      # Re-exec THIS script (the one the caller actually invoked), NOT the worktree's copy.
      # The worktree is checked out at origin/<branch>, so running its copy would silently
      # substitute origin's version of this script for the caller's -- a local fix would be
      # ignored, and a caller whose branch predates a fix would run the OLD code with no
      # indication. Measured 2026-08-10: with the worktree's copy, 6/6 concurrency workers
      # failed rc=2 because origin's copy still had the pre-fix `[[ ! -d .git ]]` guard.
      # Only the working DIRECTORY changes here.
      #
      # The env assignments MUST sit on the same logical line as `bash` (no comment between a
      # trailing `\` and the command): a `\` continuing onto a COMMENT binds the assignments
      # to an empty command, `bash` then runs WITHOUT them, the child does not see
      # SDP_IN_ISOLATION, and it re-enters isolation forever. Measured 2026-08-10: 116 nested
      # invocations and 721 stray worktrees from one 6-worker run.
      SDP_IN_ISOLATION=1 SDP_ISO_DEPTH=$((_SDP_ISO_DEPTH + 1)) SDP_CALLER_REPO="$_sdp_origin_repo" bash "$_SDP_SELF" "$MSG" --files "${FILES[*]}" "$BRANCH"
      _sdp_rc=$?
      cd "$_sdp_origin_repo" || true
      [ "$_sdp_rc" = "0" ] && _sdp_reconcile_caller_duplicates
      exit "$_sdp_rc"
    fi
    echo "  isolation: could not stage caller files into the worktree — falling back to shared index" >&2
    _sdp_cleanup_isolation
    _SDP_ISOLATION_ROOT=""
  else
    echo "  isolation: worktree setup unavailable — falling back to shared index" >&2
  fi
fi

_sdp_fingerprint_named() {
  local f
  for f in "${FILES[@]}"; do
    if [[ -f "$f" ]]; then
      printf '%s  %s\n' "$(git hash-object -- "$f" 2>/dev/null || echo MISSING)" "$f"
    else
      printf 'ABSENT  %s\n' "$f"
    fi
  done
}
_SDP_ENTRY_FINGERPRINT="$(_sdp_fingerprint_named)"

# ── WHAT WAS IN HEAD WHEN WE STARTED (F8, 2026-08-11) ────────────────────────────────────────
# _SDP_ENTRY_FINGERPRINT answers "is your file still what you handed me". That is not the
# question that matters, and it is exactly the gap four measured losses slipped through on
# 2026-08-10: the question is "did YOUR change reach the branch". A commit that simply dropped a
# named file leaves the worktree fingerprint INTACT -- nothing was reverted on disk, the file
# just never got committed -- so every existing check passes and the run reports success having
# shipped nothing of yours. Recording HEAD's blob for each named path AT ENTRY closes that: if
# you had a real diff at entry and HEAD's blob for that path is STILL the entry one after the
# push, your change did not land, whatever `git push`, verify_committed and verify_pushed said.
#
# Deliberately NOT "HEAD's blob must equal your entry blob": the pre-commit hook chain
# legitimately rewrites named files (prettier/prosewrap reflow, autofixers), so a landed change
# routinely differs from what you handed over. "Still byte-identical to the PRE-RUN HEAD" is the
# precise statement of "nothing of yours landed", and is immune to that.
_sdp_head_blob() { git rev-parse -q --verify "HEAD:$1" 2>/dev/null || echo ABSENT; }
_SDP_ENTRY_HEAD_BLOBS=""
for _sdp_hf in "${FILES[@]}"; do
  _SDP_ENTRY_HEAD_BLOBS="${_SDP_ENTRY_HEAD_BLOBS}$(_sdp_head_blob "$_sdp_hf")  ${_sdp_hf}
"
done
# Field lookup into either fingerprint ($1 path, $2 the fingerprint text). Paths cannot contain
# spaces here -- `--files` is a space-separated list, so a spaced path is already
# unrepresentable at this script's interface.
_sdp_blob_of() { printf '%s\n' "$2" | awk -v f="$1" '$2 == f { print $1; exit }'; }

# Whole-tree snapshot. The fingerprint above covers only the NAMED files -- the work being
# shipped. An uncommitted edit elsewhere in the tree can still be eaten by the reconcile's
# autostash and vanish silently (measured 2026-08-10, /codex/05-infrastructure/per-tab-worktrees.md
# "When a ship eats work it was never asked to touch"). Isolated mode makes this a non-issue by
# not touching the caller's tree at all, but the shared-index fallback and the AO VM (isolation
# off by host gate) both still run through here.
_SDP_WIP_SNAPSHOT=""
if [ -f "${_SDP_SELF%/*}/tree-wip-guard.sh" ]; then
  # shellcheck source=/dev/null
  source "${_SDP_SELF%/*}/tree-wip-guard.sh" 2>/dev/null || true
  declare -F wip_guard_snapshot >/dev/null 2>&1 && _SDP_WIP_SNAPSHOT="$(wip_guard_snapshot)"
fi

# Print a loud, actionable warning if the named files no longer match what the caller handed us.
# Returns 1 when content changed (caller should NOT report a plain transient failure).
_sdp_warn_if_content_vanished() {
  local now
  now="$(_sdp_fingerprint_named)"
  [[ "$now" == "$_SDP_ENTRY_FINGERPRINT" ]] && return 0
  {
    echo
    echo "🛑 YOUR EDITS ARE NO LONGER ON DISK AS YOU HANDED THEM TO THIS SCRIPT."
    echo "   The named file(s) changed content DURING this run — this is NOT a plain transient failure,"
    echo "   and re-running will push whatever is on disk now (possibly nothing you intended)."
    echo
    diff <(printf '%s\n' "$_SDP_ENTRY_FINGERPRINT") <(printf '%s\n' "$now") | sed 's/^/   /' || true
    echo
    echo "   RECOVER BEFORE RE-RUNNING. Your content is most likely parked in a stash entry:"
    git stash list 2>/dev/null | head -5 | sed 's/^/     /'
    echo "     Inspect:  git stash show -p 'stash@{0}'"
    echo "     Extract ONE file (safer than popping — these autostashes often hold a peer session's WIP):"
    echo "       git show 'stash@{0}:<path>' > <path>"
    echo "   See plans/active/issues/pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md (F4)."
  } >&2
  return 1
}

# _sdp_all_named_noop_at_entry -- true when EVERY named file was already byte-identical to HEAD
# before this script touched anything, i.e. this run had nothing of the caller's to ship.
_sdp_all_named_noop_at_entry() {
  local _f _disk _head
  for _f in "${FILES[@]}"; do
    _disk="$(_sdp_blob_of "$_f" "$_SDP_ENTRY_FINGERPRINT")"
    _head="$(_sdp_blob_of "$_f" "$_SDP_ENTRY_HEAD_BLOBS")"
    case "$_disk" in ABSENT | MISSING | "") return 1 ;; esac
    [[ "$_disk" == "$_head" ]] || return 1
  done
  return 0
}

# _sdp_guard_already_landed_claim -- gate on the two "already landed, treating as success"
# short-circuits below. Measured 2026-08-10, the worst shape in this whole class: this script
# exited 0 printing "✅ Named files already match HEAD (a concurrent session landed identical
# content)" for a todo that had been reverted before the script ever hashed it. "Matches HEAD"
# was true -- for the exact opposite reason to the one being reported.
#
# The discriminator is WHEN the file became identical to HEAD:
#   * identical only NOW, having had a real diff at entry -> a peer genuinely landed our content
#     while we ran. That claim is sound, and this guard passes it through.
#   * identical ALREADY at entry -> this script never saw a change to ship. That is either "a
#     peer landed it before we started" or "your edit was destroyed before we started", and
#     nothing inside this process can tell those apart -- so it must not resolve to a silent 0.
#     An autonomous run would otherwise record a green push and move on with the work gone.
_sdp_guard_already_landed_claim() {
  _sdp_all_named_noop_at_entry || return 0
  if [[ "${SDP_ALLOW_NOOP:-0}" == "1" ]]; then
    echo "  ⚠️  every named file was already identical to HEAD at entry -- SDP_ALLOW_NOOP=1, accepting as a deliberate idempotent re-run."
    return 0
  fi
  {
    echo
    echo "🛑 NOTHING OF YOURS SHIPPED, AND THIS SCRIPT CANNOT TELL YOU WHY."
    echo "   Every named file was ALREADY byte-identical to HEAD when this run started:"
    printf '%s\n' "$_SDP_ENTRY_FINGERPRINT" | sed 's/^/     /'
    echo
    echo "   Two causes produce that state and they are indistinguishable from in here:"
    echo "     (a) a peer session landed your identical content before you invoked this -- fine;"
    echo "     (b) your edit was reverted before this script hashed it -- your work is GONE."
    echo "   Reporting (a) unconditionally is what made a real (b) invisible on 2026-08-10."
    echo
    echo "   TELL THEM APART -- does HEAD actually contain the change you intended?"
    for _f in "${FILES[@]}"; do
      echo "     git log -1 --format='%h %an %ad %s' -- $_f"
    done
    echo "   If it does: nothing to do, re-run with SDP_ALLOW_NOOP=1 to make that explicit."
    echo "   If it does NOT: your content was destroyed. Recover before re-writing it --"
    git stash list 2>/dev/null | head -5 | sed 's/^/     /'
    echo "       git show 'stash@{0}:<path>' > <path>       # extract ONE file, never blind-pop"
    echo "       ls -t ~/.cache/prek/patches/ | head"
    echo "   See plans/active/issues/pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md (F8)."
  } >&2
  return 1
}

# _sdp_assert_entry_change_landed -- the post-push ground truth. For every named file that had a
# REAL diff at entry, HEAD's blob must have moved off the pre-run one. Still equal means the
# commit that shipped does not contain your change, however it got there: reverted mid-run
# (worktree fingerprint also drifted) or silently dropped from the index (worktree untouched, so
# _sdp_warn_if_content_vanished is blind to it -- that shape was measured on 2026-08-10 as a
# push containing NEITHER named file while both stayed dirty on disk).
_sdp_assert_entry_change_landed() {
  local _f _disk _entry_head _now_head
  local -a _stuck=()
  for _f in "${FILES[@]}"; do
    _disk="$(_sdp_blob_of "$_f" "$_SDP_ENTRY_FINGERPRINT")"
    _entry_head="$(_sdp_blob_of "$_f" "$_SDP_ENTRY_HEAD_BLOBS")"
    # A path absent/unhashable at entry is a staged deletion or the source half of a rename --
    # "your change landed" is not expressible as a blob move, so it is not asserted here.
    case "$_disk" in ABSENT | MISSING | "") continue ;; esac
    [[ "$_disk" == "$_entry_head" ]] && continue # nothing of ours to land for this path
    _now_head="$(_sdp_head_blob "$_f")"
    [[ "$_now_head" == "$_entry_head" ]] && _stuck+=("$_f")
  done
  [[ ${#_stuck[@]} -eq 0 ]] && return 0
  {
    echo
    echo "🛑 THE PUSH LANDED BUT YOUR CHANGE DID NOT."
    echo "   These named file(s) had a real diff when this run started, and HEAD's content for"
    echo "   them is STILL byte-identical to what it was before the run -- so the commit that"
    echo "   just shipped contains none of your work on them:"
    printf '     %s\n' "${_stuck[@]}"
    echo
    if _sdp_warn_if_content_vanished; then
      echo "   Your files are still intact on disk (unchanged since you handed them over), so this"
      echo "   is the DROPPED-FROM-THE-COMMIT shape, not a revert: re-running should land them."
      echo "   Confirm first:  git diff HEAD -- ${_stuck[*]}"
    else
      echo "   ...and the on-disk content ALSO changed during the run (see above): recover from the"
      echo "   stash BEFORE re-running, or the re-run ships the reverted content."
    fi
    echo "   See plans/active/issues/pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md (F8)."
  } >&2
  return 1
}

# _sdp_certify_success -- the SINGLE gate every success path in this script passes through, so a
# short-circuit added later cannot accidentally bypass either check. Echoes nothing on success;
# returns the exit code the caller should exit with (12 or 13), or 0 to proceed.
_sdp_certify_success() {
  _sdp_guard_already_landed_claim || return 12
  _sdp_assert_entry_change_landed || return 13
  return 0
}

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

# files_exist_in_head -- true only if EVERY named file already has an entry in HEAD's tree.
# safe_doc_push_reports_success_having_committed_nothing_2026_08_09.md: the "nothing staged --
# does content already match HEAD?" fallback below used `git diff --quiet -- files` alone, which
# is quiet (reports no difference) for a file that isn't in the index at all -- true for a
# tracked file whose content genuinely matches HEAD, but ALSO true for a brand-new untracked
# file that was simply never staged (untracked paths are invisible to a plain `git diff`, not
# "no difference"). A path absent from HEAD can never be "already landed"; requiring
# `git cat-file -e HEAD:<path>` for every named file before trusting the diff is what tells the
# two cases apart.
files_exist_in_head() {
  local _f
  for _f in "${FILES[@]}"; do
    git cat-file -e "HEAD:$_f" 2>/dev/null || return 1
  done
  return 0
}

# verify_committed -- ground truth for "is this file genuinely committed", independent of any
# git command's exit code. safe_doc_push_reports_success_having_committed_nothing_2026_08_09
# (todo 2): a `git commit`/fallback path can report success (a 0 exit, or a "nothing to commit"
# message) for reasons that have nothing to do with the named files actually landing -- a
# stubbed/mocked commit call, or a deeper git-state anomaly. `git log --oneline -1 -- <path>` is
# the actual history check: non-empty means SOME commit reachable from HEAD touches this path;
# empty means it never did, no matter what the commit step's own exit code claimed.
verify_committed() {
  local _f _log
  for _f in "${FILES[@]}"; do
    _log="$(git log --oneline -1 -- "$_f" 2>/dev/null)"
    if [[ -z "$_log" ]]; then
      echo "  ❌ verification failed: no commit reachable from HEAD touches named file: $_f" >&2
      return 1
    fi
  done
  return 0
}

# verify_pushed -- ground truth for "did this actually land on the target branch", independent
# of `git push`'s own exit code. `git branch -r --contains HEAD` lists every remote-tracking
# branch whose history includes the current HEAD commit -- origin/$BRANCH must be among them, or
# the push did not genuinely land there regardless of what the push command reported.
verify_pushed() {
  if ! git branch -r --contains HEAD 2>/dev/null | grep -qF "origin/${BRANCH}"; then
    echo "  ❌ verification failed: origin/${BRANCH} does not contain HEAD after push" >&2
    return 1
  fi
  return 0
}

# check_orphaned_prek_patches -- immediate safety net for
# safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09 (todo 2). prek stashes any
# unstaged, out-of-scope edits in the working tree into a `~/.cache/prek/patches/*.patch` file
# before every hook run and restores it after -- live-observed 2026-08-09: on a commit RETRY
# within one `git commit` invocation, that restore step silently did not run, leaving the patch
# orphaned and the edits gone from the working tree with no error and a clean `git status`. This
# does not fix prek's own lifecycle (root cause is prek-internal, per that issue doc's todo 1) --
# it turns a future occurrence from unremarked data loss into a loud, actionable warning: any
# *.patch file in the cache dir with an mtime at or after this run's start (_SDP_RUN_START_EPOCH,
# captured before any commit could have run) was created by THIS invocation and, having survived
# to a successful push, was evidently never restored.
check_orphaned_prek_patches() {
  local dir="${HOME}/.cache/prek/patches" f mtime found=()
  [[ -d "$dir" ]] || return 0
  for f in "$dir"/*.patch; do
    [[ -e "$f" ]] || continue
    mtime="$(stat -c %Y -- "$f" 2>/dev/null || echo 0)"
    if [[ "$mtime" -ge "$_SDP_RUN_START_EPOCH" ]]; then
      found+=("$f")
    fi
  done
  [[ ${#found[@]} -eq 0 ]] && return 0
  {
    echo
    echo "⚠️  ORPHANED PREK PATCH(ES) DETECTED after this run's push succeeded -- possible silent"
    echo "   data loss (prek's own stash/restore lifecycle may not have completed):"
    printf '   - %s\n' "${found[@]}"
    echo "   prek stashes unstaged, out-of-scope edits into a patch before running hooks and"
    echo "   restores them after -- these patch(es) were created during THIS run (mtime >= run"
    echo "   start) but are still sitting here after a successful push, which is the exact"
    echo "   signature of a restore step that never ran. See"
    echo "   plans/active/issues/safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09.md"
    echo "   ACTION: run 'git status --porcelain' and diff each patch above (git apply --stat"
    echo "   <patch>) to check whether its content is ALREADY back in your working tree before"
    echo "   assuming loss -- if genuinely missing, 'git apply <patch>' restores it. Do not delete"
    echo "   any patch file listed above until you've confirmed its content is safe."
  } >&2
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
# fix-commit-identity added 2026-08-10: it is a SELF-CORRECTING hook, not a content verdict.
# It rewrites the worktree's git identity and fails the commit with its own remedy line -- "git
# resolves the author BEFORE this hook, so just RE-RUN your commit — it will land correctly."
# Isolated-worktree mode trips it every time (the throwaway worktree lives outside the slot path,
# so slot-identity derivation yields a different label and the hook corrects it on first use).
# Treating that as deterministic made safe-doc-push exit 6 with "Do NOT re-run this script" over
# a hook that literally asks to be re-run -- measured live while landing the sub-agent rules line.
RETRIABLE_HOOK_IDS="check-branch-drift fix-commit-identity"

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
  # pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10 (F2): prek fails the run
  # when a hook AUTOFIXES a file ("- files were modified by this hook") even though nothing
  # rejected the content -- the documented remedy is re-stage and re-run, which succeeds.
  # Classifying that as deterministic printed "Retrying will fail identically. Do NOT re-run
  # this script" over a run whose every sub-check had reported OK and whose sweep had printed
  # its own "staged files clean" (observed twice, 2026-08-10). Treat it as RETRIABLE: the
  # retry re-stages the autofixed content. If a genuine content violation is ALSO present it
  # is unchanged by the retry and the next attempt exits 6 with the hook's remedy line, so
  # the worst case is one extra attempt rather than a false hard-stop on a fixable tree.
  if grep -qi "files were modified by this hook" "$err_file" 2>/dev/null; then
    return 0
  fi
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
  # autostash chain-breaker (multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md):
  # if the pop restored stale content that reverts origin, quarantine it NOW so the next cycle does
  # NOT re-stash it. Only affects files NOT in this run's --files (the caller's explicit edits).
  if declare -F autostash_guard_quarantine_stale_pop >/dev/null 2>&1; then
    autostash_guard_quarantine_stale_pop "${FILES[*]}" "origin/${BRANCH}" || true
  fi
  return 0
}

backoff() {
  local attempt="$1"
  sleep "$((1 + RANDOM % 3 + attempt))"
}

# LOCK_CONTENTION_MAX / lock_contention_count -- escape-hatch counter for
# safe_doc_push_reports_success_having_committed_nothing_2026_08_09 (todo 4). Retrying an
# index.lock failure in place is correct for a MOMENTARY collision (a peer's single `git add`/
# `git commit` mid-flight), but under SUSTAINED foreign write -- a peer session's own retry
# loop re-taking the lock as fast as this script releases it -- retrying in the SAME checkout
# cannot converge; it just burns MAX_ATTEMPTS and reports a generic "transient, re-run" message
# that sends the caller straight back into the same non-convergent loop. Once consecutive
# index.lock failures (across the `git add` and `git commit` sites below) reach this count,
# stop looping and print the documented recovery instead: land the named files from a separate
# clone -- the exact move that unblocked the live incident this todo comes from.
LOCK_CONTENTION_MAX=3
lock_contention_count=0

print_lock_contention_escape_hatch() {
  cat >&2 <<EOF

❌ ${lock_contention_count} consecutive index.lock failures in this checkout -- this is
   SUSTAINED FOREIGN WRITE (a concurrent process is holding or re-taking the lock faster than
   this script's own retries can clear it), not a momentary collision. Retrying in place
   cannot converge: re-running this script against THIS SAME checkout will very likely hit the
   identical wall again.

   ESCAPE HATCH (what unblocked safe_doc_push_reports_success_having_committed_nothing_2026_08_09,
   the live incident this behavior comes from -- land from a separate clone instead of
   contending for this checkout's lock):

     1. Clone fresh, reusing this checkout's objects so it's cheap:
          git clone --reference "\$(pwd)" "\$(git rev-parse --show-toplevel)" /tmp/safe-doc-push-\$\$
          cd /tmp/safe-doc-push-\$\$ && git checkout -q ${BRANCH}
     2. Re-create the named file(s)' content there (copy from this checkout, or re-apply your
        edit), then re-run from the fresh clone:
          bash scripts/dev/safe-doc-push.sh "<same commit message>" --files "<same paths>" ${BRANCH}
     3. Once it lands, this checkout's own working tree is unaffected -- pull it back in
        (\`git pull --ff-only origin ${BRANCH}\`) at your convenience; there is nothing to
        reconcile here since this attempt never committed anything (see verify_committed
        above -- a false success is refused, not just an unverified one).

   If you'd rather wait it out: check whether \`.git/index.lock\` is stale (a multi-minute-old
   lock file with no process actually holding it is safe to remove) before assuming the peer
   session is still active.
EOF
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
  # pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10 (P0): the pre-commit
  # drift gate is ADVISORY for this script's own commit, because this script provably
  # reconciles AFTER committing (the retry loop below rebases onto origin and re-verifies
  # before every push). Measured 2026-08-10: the hook chain is 118s while PM's commit
  # inter-arrival is 60-80s, so origin moves during EVERY hook run and the gate fired on
  # essentially every attempt -- each failure re-paying the full 118s sweep for an outcome
  # fixed before it started. Scoped to this one call (exported for the `git commit`
  # subprocess, unset immediately after) so it can never leak to an unrelated commit.
  export DRIFT_GATE_ADVISORY=1
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
  unset DRIFT_GATE_ADVISORY
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

# Stage the payload FIRST, before anything that might quarantine or autostash the dirty
# tree. Once staged, the named files are no longer visible to `git diff --name-only` (the
# working tree matches the index for them), so the quarantine step below cannot sweep them
# into a stash that the script then compares against and falsely reports "already matches
# HEAD." The in-loop `git add` + `reassert_renames` below this block re-stage on every
# attempt to recover from any reconcile step that runs `git restore --staged .`.
# ssot: /plans/active/issues/safe_doc_push_isolation_drops_rename_deletions_2026_08_10.md
#       § "Second symptom, same mechanism: a MODIFICATION dropped, and reported as SUCCESS"
echo "  staging payload first (before any quarantine or reconcile may touch the tree)"
git add -- "${FILES[@]}" 2>/dev/null || true
reassert_renames

# autostash chain-breaker: bound the backlog BEFORE creating any new autostash entries
# (multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md). The caller's
# --files are passed as protected so the extreme-pile self-arrest never quarantines the very
# work this run is shipping (dogfooded live 2026-08-10 slot-9).
if declare -F autostash_guard_bound_backlog >/dev/null 2>&1; then
  autostash_guard_bound_backlog "${FILES[*]}" "origin/${BRANCH}" || true
fi

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

    if ! git add -- "${FILES[@]}" 2>/tmp/_sdp_add_err; then
      # safe_doc_push_reports_success_having_committed_nothing_2026_08_09 (todo 3): `git add`'s
      # own exit code was never checked, so an index.lock failure here (the exact incident
      # mechanism -- a peer session's autostash sweep holding the lock) silently produced an
      # empty `git diff --cached`, which fell straight into the SAME "nothing staged ...
      # checking if content already matches HEAD" wording used for the genuinely benign
      # no-op-edit case. That phrasing reads as "probably fine" when it is actually a hard
      # failure to stage at all -- distinguish it here, before ever reaching that branch.
      if grep -qi "index.lock" /tmp/_sdp_add_err; then
        lock_contention_count=$((lock_contention_count + 1))
        echo "  ❌ could not stage named files -- index.lock contention on 'git add' (another process is writing this instant). This is a HARD FAILURE, not the benign 'nothing to stage' case -- short wait, retry (${lock_contention_count}/${LOCK_CONTENTION_MAX} consecutive lock failures)"
        if [[ "$lock_contention_count" -ge "$LOCK_CONTENTION_MAX" ]]; then
          print_lock_contention_escape_hatch
          exit 8
        fi
        sleep 2
        continue
      fi
      echo "  ❌ could not stage named files -- 'git add' failed for a non-lock reason:" >&2
      cat /tmp/_sdp_add_err >&2
      backoff "$attempt"
      continue
    fi
    unstage_foreign_paths
    reassert_renames

    if ! git diff --cached --quiet -- "${FILES[@]}"; then
      : # there is something to commit
    else
      echo "  nothing to stage for the named files (staging completed cleanly, no diff) -- checking if content already matches HEAD"
      if git diff --quiet -- "${FILES[@]}" 2>/dev/null && files_exist_in_head; then
        if verify_committed && verify_pushed; then
          _sdp_certify_success || exit $?
          echo "✅ Named files already match HEAD (a concurrent session landed identical content while this run was in flight) -- treating as success."
          final_ok=true
          break
        fi
        echo "  files_exist_in_head passed but end-to-end verification failed -- not trusting the fallback; retrying"
      else
        echo "  at least one named file is absent from HEAD -- staging genuinely failed, not already-landed; retrying"
      fi
    fi

    if ! locked_git_commit -q -m "$MSG" 2>/tmp/_sdp_commit_err; then
      if grep -qi "nothing to commit" /tmp/_sdp_commit_err; then
        if verify_committed && verify_pushed; then
          _sdp_certify_success || exit $?
          echo "✅ Nothing to commit -- already landed. Treating as success."
          final_ok=true
          break
        fi
        echo "  git reported nothing-to-commit but end-to-end verification failed -- not trusting it; retrying" >&2
      fi
      if grep -qi "index.lock" /tmp/_sdp_commit_err; then
        lock_contention_count=$((lock_contention_count + 1))
        echo "  index.lock contention (another process is writing this instant) -- short wait, retry (${lock_contention_count}/${LOCK_CONTENTION_MAX} consecutive lock failures)"
        if [[ "$lock_contention_count" -ge "$LOCK_CONTENTION_MAX" ]]; then
          print_lock_contention_escape_hatch
          exit 8
        fi
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
    if ! verify_committed; then
      echo "❌ git commit exited 0 but the named file(s) have no commit reachable from HEAD -- refusing to report success (a mocked/stubbed commit call, or a deeper git-state anomaly)." >&2
      exit 6
    fi
    committed=true
  fi

  # Rebase-invalidated evidence citations are reconciled HERE -- after the last rebase, before
  # the push -- because that is the only point where the old->new SHA mapping still exists AND
  # nothing has shipped yet. A pre-commit check cannot catch this: at commit time the citation
  # IS resolvable; the rebase invalidates it afterwards. Best-effort and non-blocking.
  if [[ -f "${_SDP_SELF%/*}/reconcile-sha-citations.sh" ]]; then
    # shellcheck source=/dev/null
    source "${_SDP_SELF%/*}/reconcile-sha-citations.sh" 2>/dev/null || true
    if declare -F reconcile_sha_citations >/dev/null 2>&1; then
      reconcile_sha_citations "$BRANCH" "${FILES[@]}" || true
    fi
  fi

  if git push origin "HEAD:${BRANCH}" 2>/tmp/_sdp_push_err; then
    if verify_pushed; then
      # verify_pushed proves a commit reached the branch. It does NOT prove YOUR change is in
      # it -- that is what this gate adds, and it is the one four measured losses needed.
      _sdp_certify_success || exit $?
      echo "✅ Pushed $(git rev-parse --short HEAD) -> ${BRANCH}"
      if [ -n "${_SDP_WIP_SNAPSHOT:-}" ] && declare -F wip_guard_report >/dev/null 2>&1; then
        wip_guard_report "$_SDP_WIP_SNAPSHOT" "${FILES[*]}" || true
      fi
      final_ok=true
      break
    fi
    echo "❌ git push exited 0 but origin/${BRANCH} does not contain HEAD -- refusing to report success." >&2
    exit 4
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
  # F4: check BEFORE printing the transient wording, so the two cases never get the same advice.
  if ! _sdp_warn_if_content_vanished; then
    echo "❌ Exhausted ${MAX_ATTEMPTS} attempts AND the named file(s) were reverted during the run (see above)." >&2
    echo "   Recover the content first; re-running as-is would NOT re-land your edits." >&2
    exit 10
  fi
  {
    echo "❌ Exhausted ${MAX_ATTEMPTS} attempts. Deterministic pre-commit content failures now exit 6 BEFORE"
    echo "   reaching here, so this path means a genuine race (fetch/pull/push contention) that did not settle."
    echo "   Your named file(s) are byte-identical to what you handed this script, so re-running is safe."
    echo "   READ the last error below first rather than assuming transience:"
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

if ! check_orphaned_prek_patches; then
  echo "❌ Push landed but exiting non-zero (exit 9) because of the orphaned-patch warning above -- this is ACTIONABLE, not a script bug. Do not silently ignore or re-run without inspecting the patch(es)." >&2
  exit 9
fi

exit 0
