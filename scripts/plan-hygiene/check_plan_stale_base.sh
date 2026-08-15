#!/usr/bin/env bash
# Epic: observability_master
# Lifecycle: PERMANENT — precommit guard
# Delete-when: never (delete only if plan editing stops being multi-session)
#
# Refuse to commit a plan/codex doc whose staged content is MISSING a change that
# already exists on origin — i.e. a silent revert of someone else's work.
#
# WHY THIS EXISTS (measured twice, 2026-08-14 and 2026-08-15)
# -----------------------------------------------------------
# On a shared multi-session checkout the destructive sequence is:
#
#   1. You read plans/active/foo.md.
#   2. A peer edits the SAME file and pushes.
#   3. You write your version of the whole file and stage it.
#   4. Full-file staging OVERWRITES — it does not merge. The peer's edit is gone,
#      with NO conflict, NO warning, and a perfectly clean `git status`.
#
# Both measured near-misses were caught by hand, not by a tool:
#   * 2026-08-14 — a peer's two better todos nearly replaced by a staler rewrite.
#     `check_todo_regression.sh` caught it (origin=9, current=8).
#   * 2026-08-15 — a peer's corrected launcher census (a PROSE blockquote fixing
#     "158" to "12") nearly dropped by an edit that simultaneously ADDED two todos.
#     `check_todo_regression.sh` passed clean: the total todo count GREW. Counting
#     todos cannot see prose, and cannot see a same-count swap.
#
# WHAT IT ACTUALLY CHECKS, and why not the obvious thing
# ------------------------------------------------------
# The obvious check — "does HEAD:<file> differ from origin:<file>?" — was the first
# implementation and it was WRONG: after `safe-doc-push.sh` (which commits from an
# isolated worktree) your local HEAD legitimately lags origin for files you just
# pushed yourself, so it fired on almost every commit. A guard that cries wolf gets
# ignored, which is worse than no guard.
#
# So this measures the danger directly: take the lines origin ADDED relative to your
# HEAD, and confirm each one survives in your STAGED content. Present => you have the
# peer's change. Absent => you are about to erase it.
#
# Comparison is whitespace-NORMALISED (whole file collapsed to single-spaced text,
# matched as substrings) because prettier re-wraps prose: the same sentence can be
# split across different line boundaries upstream and locally. A naive line-equality
# check would report false positives on every re-wrap — the same class of mistake as
# the HEAD-vs-origin version.
#
# Usage:
#   bash scripts/plan-hygiene/check_plan_stale_base.sh --only <path> [<path> ...]
#   bash scripts/plan-hygiene/check_plan_stale_base.sh            # all staged docs
set -uo pipefail

ORIGIN_REF="${STALE_BASE_ORIGIN_REF:-origin/live-defi-rollout}"
# Short added lines ("---", "), "- [ ] "), markdown scaffolding) carry no identity and
# collide across a document, so matching them proves nothing either way.
MIN_SIGNIFICANT_LEN="${STALE_BASE_MIN_LEN:-40}"

if [[ "${1:-}" == "--only" ]]; then
  shift
  FILES=("$@")
else
  mapfile -t FILES < <(git diff --cached --name-only --diff-filter=ACM -- 'plans/**/*.md' 'codex/**/*.md')
fi

if [[ ${#FILES[@]} -eq 0 ]]; then
  echo "✅ check_plan_stale_base: no staged plan/codex docs"
  exit 0
fi

# A missing origin ref means we cannot compare. FAIL OPEN and say so loudly — blocking
# every commit because a ref is absent would be worse than the risk, but staying silent
# would let the guard rot into a no-op nobody notices.
if ! git rev-parse --verify --quiet "$ORIGIN_REF" >/dev/null; then
  echo "⚠️  check_plan_stale_base: ${ORIGIN_REF} not present locally — SKIPPED (guard inactive)."
  echo "   Run 'git fetch origin' so this check can protect you."
  exit 0
fi

# Collapse all whitespace so a re-wrapped paragraph matches its unwrapped twin.
normalise() { tr '\n' ' ' | tr -s '[:space:]' ' '; }

FAILURES=0
CHECKED=0
for f in "${FILES[@]}"; do
  [[ -f "$f" ]] || continue
  git cat-file -e "${ORIGIN_REF}:${f}" 2>/dev/null || continue
  git cat-file -e "HEAD:${f}" 2>/dev/null || continue
  CHECKED=$((CHECKED + 1))

  # Compare the content that would actually be COMMITTED. If the file has staged
  # changes that is the index; otherwise it is the working tree. Reading the index
  # unconditionally is wrong for an unstaged file — there the index still equals
  # HEAD, so every upstream line reads as "missing" and the guard fires on content
  # the author never touched. (Found by running this check on its own repo.)
  if git diff --cached --quiet -- "$f" 2>/dev/null; then
    staged_norm="$(normalise <"$f")"
  else
    staged_norm="$(git show ":${f}" 2>/dev/null | normalise)"
  fi

  missing=0
  first_missing=""
  while IFS= read -r line; do
    text="${line:1}"
    norm="$(printf '%s' "$text" | tr -s '[:space:]' ' ' | sed 's/^ //; s/ $//')"
    ((${#norm} >= MIN_SIGNIFICANT_LEN)) || continue
    if [[ "$staged_norm" != *"$norm"* ]]; then
      missing=$((missing + 1))
      [[ -n "$first_missing" ]] || first_missing="$norm"
    fi
  done < <(git diff "HEAD" "$ORIGIN_REF" -- "$f" | grep '^+' | grep -v '^+++')

  if [[ $missing -gt 0 ]]; then
    FAILURES=$((FAILURES + 1))
    echo "❌ SILENT REVERT: ${f}"
    echo "   ${missing} line(s) that exist on ${ORIGIN_REF} are ABSENT from your staged version."
    echo "   Committing this erases a peer's change with no conflict signal."
    echo
    echo "   First missing line:"
    echo "     ${first_missing:0:160}"
    echo
    echo "   See everything you would destroy:"
    echo "     git diff HEAD ${ORIGIN_REF} -- ${f}"
    echo "   Reconcile, then re-apply your edit on top:"
    echo "     git pull --rebase --autostash"
    echo "   Then VERIFY BOTH survived — the peer's change AND yours."
    echo
  fi
done

if [[ $FAILURES -gt 0 ]]; then
  echo "❌ check_plan_stale_base: ${FAILURES} staged doc(s) would silently revert upstream content"
  exit 1
fi

echo "✅ check_plan_stale_base: ${CHECKED} staged doc(s) contain all upstream content"
exit 0
