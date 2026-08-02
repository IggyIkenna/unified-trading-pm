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
# sustained contention (transient -- just re-run).

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

for f in "${FILES[@]}"; do
  if [[ ! -e "$f" ]]; then
    echo "Refusing: named path does not exist: $f" >&2
    exit 2
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

backoff() {
  local attempt="$1"
  sleep "$((1 + RANDOM % 3 + attempt))"
}

MAX_ATTEMPTS=6
committed=false
final_ok=false

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
          if ! git pull --rebase --autostash origin "$BRANCH" -q 2>/tmp/_sdp_rebase_err; then
            git rebase --abort 2>/dev/null || true
            echo "  rebase conflicted -- this is a genuine content collision, not contention. Resolve manually:"
            cat /tmp/_sdp_rebase_err >&2
            exit 3
          fi
          git restore --staged . 2>/dev/null || true
        else
          echo "  pull failed:"; cat /tmp/_sdp_pull_err
          backoff "$attempt"
          continue
        fi
      fi
    else
      # Defensive: shouldn't normally happen pre-commit, but handle the same as the
      # post-commit case if it does (e.g. a prior failed attempt left a local commit).
      if ! git pull --rebase --autostash origin "$BRANCH" -q 2>/tmp/_sdp_rebase_err; then
        git rebase --abort 2>/dev/null || true
        echo "  rebase conflicted -- genuine content collision, resolve manually:"
        cat /tmp/_sdp_rebase_err >&2
        exit 3
      fi
      git restore --staged . 2>/dev/null || true
    fi

    git add -- "${FILES[@]}"
    unstage_foreign_paths

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

    if ! git commit -q -m "$MSG" 2>/tmp/_sdp_commit_err; then
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
      echo "  commit blocked (likely a pre-commit hook, e.g. branch drift re-detected mid-race):"
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
    if ! git pull --rebase --autostash origin "$BRANCH" -q 2>/tmp/_sdp_rebase_err; then
      git rebase --abort 2>/dev/null || true
      echo "  rebase conflicted on retry -- genuine content collision, resolve manually:"
      cat /tmp/_sdp_rebase_err >&2
      exit 3
    fi
    git restore --staged . 2>/dev/null || true
    backoff "$attempt"
    continue
  fi

  echo "❌ Push failed for a non-drift reason:"; cat /tmp/_sdp_push_err >&2
  exit 4
done

if [[ "$final_ok" != true ]]; then
  echo "❌ Exhausted ${MAX_ATTEMPTS} attempts under sustained contention -- this is transient, not a defect. Re-run." >&2
  exit 5
fi
