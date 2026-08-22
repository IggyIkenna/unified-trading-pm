#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Report plans exceeding line-count caps.
#
# TWO-TIER policy (operator ruling 2026-07-24 -- replaces the old three-tier umbrella-exemption
# model): NO exceptions in the enforcement.
#   - plans/epics/*.md (real epics, the long-lived master trackers): flat 2000L HARD cap.
#   - everything else in plans/active/*.md: flat 500L soft-warn / 1000L HARD cap.
# There is no longer an `umbrella: true` frontmatter escape hatch, and no `locked_by AND >100
# todos` escape hatch, for a plan living in plans/active/ -- a legitimately large hub/coordinator
# doc either fits under 1000L, gets split, or gets promoted to a REAL epic in plans/epics/ (which
# then gets the epic tier, not a free pass). The old exemption let umbrella-marked plans in
# plans/active/ grow to 2000L unflagged; several did, and became debt indistinguishable from a
# plan that just never got trimmed. `umbrella: true` frontmatter may still exist on old docs but is
# no longer read by this script -- it is inert.
#
# A SECOND DOCUMENTED EXCEPTION (operator ruling 2026-08-02, plan_reconcile_parked_operator_decisions_2026_08_02.md
# na-eligibility-audit item 17, option A / run-1 recommendation): a commit whose staged diff to an
# already-over-cap LIVE doc (real open todos, not archival-eligible) is confined to APPENDING a small
# dated audit-verdict marker -- no checkbox added/removed/changed -- is allowed through in SCOPED mode.
# Root problem this closes: SCOPED mode has no baseline tolerance (a file THIS commit touches must not be
# over cap, full stop), so once a live, still-open-todo doc crossed 1000L, EVERY future commit to it --
# including a trivial 4-line na-eligibility-audit verdict marker with zero content change -- was
# permanently blocked, forcing every future audit run to silently skip writing its incremental-skip
# anchor onto the largest, most expensive-to-re-read docs in the corpus (confirmed empirically on 4 live
# docs 2026-08-02: lst_rate_honest_coverage_2026_07-21.md, data_completion_to_100_all_ag_2026_06_21.md,
# instruments_completion_tracker_2026_07_06.md, master_data_canonicalisation_migration_catalogue_2026_06_07.md).
# Narrowly scoped: only fires when (a) the file is already over cap before this commit (a doc newly
# crossing the cap in this commit is NOT covered -- that is a real regression, blocked as before), (b) the
# staged diff has zero deleted lines, (c) the staged diff adds no more than 10 lines, and (d) none of the
# added lines match a checkbox pattern (`- [ ]`/`- [x]`) -- so this can never be used to sneak in new
# tracked work on an over-cap doc, only a small append like a dated verdict/Progress-Log marker.
#
# A THIRD DOCUMENTED EXCEPTION (operator ruling 2026-08-09,
# plan_hygiene_broken_link_gate_vs_line_cap_gate_deadlock_2026_08_08.md option (a)): a bounded,
# same-line LINK-REPOINT edit on an already-over-cap LIVE doc is also allowed through in SCOPED
# mode, alongside the small-marker-append exception above. Root problem this closes: the corpus-wide
# broken-link gate (validate_plan_links.py, unconditional, HARD) can force a one-line path fix
# (e.g. /plans/active/issues/<x>.md -> /plans/archive/2026_08/issues/<x>.md, after <x> archives)
# inside an over-cap referrer doc -- but a same-line text substitution ALWAYS shows DELETED>=1 in
# `git diff --numstat` (git diffs at line granularity, never character granularity), so the
# small-marker-append exception's DELETED=0 requirement can never fire for this shape of edit,
# deadlocking the two gates against each other with no escape hatch (live-verified 2026-08-08: a
# real `sed -i 's#...#...#'` link-repoint on a 1007L over-cap doc produced `git diff --numstat` =
# `1  1  ...`, confirmed not assumed). Narrowly scoped: only fires when (a) the file is already over
# cap before this commit (automatically implied here -- see below), (b) the staged diff's ADDED line
# count is <= its DELETED count (never grows the file), and (c) every changed (+/-) content line,
# after normalizing any /plans/active/... or /plans/archive/<YYYY_MM>/... path segment to a common
# token, is identical between the removed and added sides -- i.e. the ONLY difference on every
# touched line is a path-token substitution, never new prose. Condition (a) needs no separate
# PRE_COMMIT_LINES check the marker-append branch uses: since ADDED<=DELETED, pre-commit line count
# (lines - ADDED + DELETED) is always >= the current (already-over-cap) line count.
#
# A FOURTH DOCUMENTED EXCEPTION (operator ruling 2026-08-15, BLK-d942f2f7, unified-trading-pm
# promote_qg_failure PR #3197): a staged diff to an already-over-cap doc that is byte-identical
# modulo whitespace (`git diff --cached -w -- <file>` empty) is allowed through in SCOPED mode.
# Root problem this closes: the corpus-wide prosewrap-padding gate (check_prosewrap_padding.sh,
# also a shrinking ratchet that can never regress) sometimes needs its repair script
# (fix_prosewrap_padding.py) run against a doc that happens to already be over the line-cap for
# unrelated reasons -- the repair only de-indents existing lines, never adds/removes/reorders
# content, so it cannot make the line-cap violation any worse, but the marker-append and
# link-repoint exceptions above don't cover it (no path-token substitution, and a de-indent can
# show up as ADDED>0/DELETED>0 with no bearing on either exception's shape). Strictly safer than
# the link-repoint exception: content is byte-identical, not merely a bounded path substitution.
#
# A FIFTH DOCUMENTED EXCEPTION (operator ruling 2026-08-15, BLK-a2710376, cross_cutting satellite
# batch 13 dispatch): a staged diff to an already-over-cap doc confined to a SINGLE contiguous hunk
# (one `@@` block) that replaces exactly ONE pre-existing todo's checkbox line with exactly ONE new
# checkbox line (a real `- [ ]` -> `- [x]` flip, plus its evidence text) is allowed through. Root
# problem this closes: a real checkbox flip always shows as delete-old-line(s)+add-new-line(s) in
# git diff, so it can never satisfy the marker-append exception (DELETED=0) or the link-repoint
# exception (content must be path-token-identical on every changed line) -- meaning NO checkbox
# could ever be flipped again on a doc once it crossed the hard cap, a previously-undiscovered
# deadlock of the same shape as the 2026-08-08 link-repoint deadlock, but for the checkbox-flip
# case specifically (only surfaced once a live doc first crossed 1000L while still carrying open
# todos, 2026-08-15). Narrowly scoped so it does NOT reopen the 2026-08-02 anti-sneak-in-new-work
# loophole (that ruling targeted the UNSCOPED marker-append exception adding arbitrary new checkbox
# lines anywhere in the file): (a) the diff must be exactly ONE hunk -- confined to one todo block,
# never scattered edits across the file -- and (b) exactly one checkbox line is removed and exactly
# one checkbox line is added within that hunk (a genuine 1-for-1 flip, never a net add/remove of
# todo count). A second, unrelated todo edited in the same commit needs its own separate commit.
#
# ONE DOCUMENTED EXCEPTION (operator ruling 2026-07-30): a doc with ZERO OPEN TODOS archives via
# the normal 6-step ritual regardless of how far over its cap it is. The cap exists to stop a LIVE
# plan growing into an unreadable hub; it has no purpose on a finished doc that is on its way OUT
# of plans/active/. Blocking that archival is actively counterproductive -- on 2026-07-30 this
# gate refused a completion marker on a 1509L zero-open-todo doc, which left the doc `active` so
# every /plan-reconcile, /ag-closeout-audit and /na-eligibility-audit run re-reads all 1509 lines
# of it forever. Gated on zero open todos VERIFIED against the /plan-reconcile Phase-2
# HARD-evidence bar (one open todo -> it is a live plan, cap applies normally: split or fold), and
# on the commit being the archival move itself. Once under plans/archive/ the doc is outside this
# script's globs anyway (status: complete / nature: record docs are unbounded by design, same as
# the extracted-history case in the SCOPED-mode note below). SSOT:
# /codex/12-agent-workflow/plan-completion-and-archival-discipline.md
# section "The line-cap does NOT block archival of an already-done doc". Never delete content from
# a done plan just to get it under a cap.
#
# Usage: bash scripts/plan-hygiene/check_line_caps.sh [--quiet] [--update-baseline] [file ...]
# No files given -> full-corpus glob (plans/active/*.md + plans/epics/*.md), gated by the
# shrinking-ratchet baseline (see below).
# Files given -> check ONLY those (the prek hook's STAGED plans/epics), no baseline involved: a
# file THIS commit touches must not be over its tier's cap, full stop (RULE-11 blast-radius
# safety, same convention as check_frontmatter.sh's optional file-list arg) -- pre-existing debt
# in files you're not editing is a corpus-wide concern, not this commit's.
# Exit 0 (full-corpus mode) = HARD-failure count <= baseline (see line_caps_baseline.yaml).
# Exit 1 = count exceeds baseline -- a NEW plan/epic crossed its cap, or an existing one got worse.
# This is a SHRINKING ratchet (same pattern as check_reference_paths.py/reference_paths_baseline.yaml):
# pre-existing debt from before the baseline was seeded is tolerated so this check can be a real
# hard gate without immediately blocking the shared pipeline over violations nobody introduced today.
# --update-baseline: after fixing a flagged plan/epic, persist the new (lower) count (full-corpus
# mode only). Refuses to raise the baseline -- if the live count is higher than what's on disk, the
# run still fails.

set -euo pipefail
QUIET=""
UPDATE_BASELINE=""
FILES=()
for _arg in "$@"; do
  case "$_arg" in
    --quiet) QUIET="--quiet" ;;
    --update-baseline) UPDATE_BASELINE="1" ;;
    *) FILES+=("$_arg") ;;
  esac
done
PM_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
HARD_FAILURES=0
EPIC_CAP=2000
PLAN_HARD_CAP=1000
PLAN_SOFT_CAP=500
BASELINE_PATH="$(dirname "$0")/line_caps_baseline.yaml"
BASELINE_COUNT="$(grep -E '^hard_count:' "$BASELINE_PATH" | sed -E 's/^hard_count:[[:space:]]*//')"
BASELINE_COUNT="${BASELINE_COUNT:-0}"
SCOPED=""
[ "${#FILES[@]}" -gt 0 ] && SCOPED="1"

echo "Line-count check (plans: soft=${PLAN_SOFT_CAP}, hard=${PLAN_HARD_CAP} | epics: hard=${EPIC_CAP} -- no exceptions):"
echo ""

if [ -n "$SCOPED" ]; then
  TARGETS=("${FILES[@]}")
else
  TARGETS=("$PM_DIR/plans/active"/*.md "$PM_DIR/plans/epics"/*.md)
fi

for f in "${TARGETS[@]}"; do
  name="$(basename "$f")"
  [ "$name" = "INDEX.md" ] && continue
  [ "$name" = "README.md" ] && continue
  [[ "$name" == _* ]] && continue           # _agent_pings.md etc
  [[ "$name" == *.HANDOVER.md ]] && continue
  [[ "$name" == *_SUPERSEDED_*.md ]] && continue   # frozen-in-place, not live
  [ -f "$f" ] || continue                   # a staged file can be a deletion (no longer on disk)
  # This check is scoped to plans/active/ + plans/epics/ ONLY (see the policy comment at the top
  # of this file) -- full-corpus mode's own glob already enforces that, but SCOPED mode (the prek
  # pre-commit hook, called with the staged file list as args) iterates whatever paths it's given
  # with no directory filter, so staging a plans/archive/ record doc alongside an active plan wrongly
  # subjected the archive doc to the same 1000L active-plan cap it was never meant to carry -- the
  # entire point of extracting a Progress Log/history section INTO plans/archive/ is to get it OUT
  # of the enforced-cap flow (status: complete / nature: record docs are unbounded by design). Caught
  # 2026-07-24 when a legitimate archive-bound history file failed this gate.
  [[ "$f" != *"plans/active/"* && "$f" != *"plans/epics/"* ]] && continue

  lines=$(wc -l < "$f")
  todos=$(grep -c "^- \[.\]" "$f" 2>/dev/null || true)
  todos="${todos:-0}"

  # Path-substring match (not a `*/plans/epics/*` case pattern) so this is correct regardless of
  # whether $f is absolute ($PM_DIR/plans/epics/x.md, the real full-corpus/precommit shape) or a
  # bare relative path (plans/epics/x.md, e.g. someone running this script by hand from repo root)
  # -- a leading-anchor pattern silently misclassified the latter as a PLAN_HARD_CAP=1000 file
  # instead of an EPIC_CAP=2000 file (caught 2026-07-24 by testing both invocation shapes).
  if [[ "$f" == *"plans/epics/"* ]]; then
    if [ "$lines" -gt "$EPIC_CAP" ]; then
      echo "  HARD    $name  ${lines}L  todos=${todos}  (epic, over ${EPIC_CAP}L cap — split it)"
      HARD_FAILURES=$(( HARD_FAILURES + 1 ))
    fi
    continue
  fi

  if [ "$lines" -gt "$PLAN_HARD_CAP" ]; then
    SMALL_MARKER_APPEND=""
    LINK_REPOINT_EDIT=""
    WHITESPACE_ONLY_REPAIR=""
    SINGLE_TODO_FLIP=""
    if [ -n "$SCOPED" ]; then
      # Whitespace-only-repair exception (operator ruling 2026-08-15,
      # BLK-d942f2f7, unified-trading-pm promote_qg_failure PR #3197): a staged diff to an
      # already-over-cap doc that is byte-identical modulo whitespace (`git diff --cached -w`
      # empty) is allowed through -- e.g. the fix_prosewrap_padding.py repair, which only
      # de-indents existing lines and never adds/removes/reorders content. Strictly safer than
      # the link-repoint exception below (zero semantic content change, not just a bounded
      # path-token substitution), so no ADDED<=DELETED / path-normalization reasoning is needed --
      # a pure-whitespace diff can never grow the file's line count either.
      if [ -z "$(git -C "$PM_DIR" diff --cached -w -- "$f" 2>/dev/null)" ]; then
        WHITESPACE_ONLY_REPAIR="1"
      else
        # Combined whitespace + link-repoint case: a single file can need BOTH the
        # prosewrap de-indent repair AND an unrelated archival path-repoint in the
        # same commit (the reference-path gate applies to a staged file's full
        # content, not just its diff, so the path fix can't be deferred to a later
        # commit while the file is being touched at all). Neither exception alone
        # covers the union. Every changed (+/-) line, after normalizing path
        # segments AND stripping all whitespace, must match between removed/added --
        # strictly a superset of what each exception already tolerates alone.
        # NOTE: whitespace is stripped PER-LINE via sed, never via `tr -d` on the whole
        # multi-line stream -- `tr` would delete the newlines too, merging every line
        # into one blob and destroying line-by-line correspondence (caught live,
        # BLK-d942f2f7 follow-up). The path-token regex also tolerates an OPTIONAL
        # leading slash (`/?plans/...`) since this exception exists precisely to also
        # cover repointing a corpus bare-filename-reference violation (no leading
        # slash) to the leading-slash canonical form in the same edit.
        RAW_DIFF_WS="$(git -C "$PM_DIR" diff --cached -- "$f" 2>/dev/null || true)"
        # `|| true` on each grep: pipefail makes a genuinely-empty match (e.g. zero deleted lines,
        # the exact shape the small-marker-append exception below exists to handle) fail the whole
        # pipeline and, under `set -e`, silently abort the entire script BEFORE the marker-append
        # exception ever runs -- caught live 2026-08-15 (a real 0-deletion marker-append commit on
        # this file hit this exact abort). An empty match correctly yields an empty $REMOVED_WS_PATH/
        # $ADDED_WS_PATH either way; only the premature exit was the bug.
        REMOVED_WS_PATH="$(echo "$RAW_DIFF_WS" | { grep -E '^-[^-]' || true; } | sed -E 's/^-//' \
          | sed -E 's#/?plans/(active|archive/[0-9]{4}_[0-9]{2})/#/plans/__PATH__/#g' \
          | sed -E 's/[[:space:]]+//g' | sort)"
        ADDED_WS_PATH="$(echo "$RAW_DIFF_WS" | { grep -E '^\+[^+]' || true; } | sed -E 's/^\+//' \
          | sed -E 's#/?plans/(active|archive/[0-9]{4}_[0-9]{2})/#/plans/__PATH__/#g' \
          | sed -E 's/[[:space:]]+//g' | sort)"
        if [ -n "$REMOVED_WS_PATH" ] && [ "$REMOVED_WS_PATH" = "$ADDED_WS_PATH" ]; then
          WHITESPACE_ONLY_REPAIR="1"
        fi
      fi
      # Small-marker-append exception (see policy comment above): only when this diff is a bounded,
      # non-checkbox append to a doc ALREADY over cap before this commit.
      DIFF_NUMSTAT="$(git -C "$PM_DIR" diff --cached --numstat -- "$f" 2>/dev/null || true)"
      ADDED="$(echo "$DIFF_NUMSTAT" | awk '{print $1}')"
      DELETED="$(echo "$DIFF_NUMSTAT" | awk '{print $2}')"
      if [ -n "$ADDED" ] && [ -n "$DELETED" ] && [ "$DELETED" = "0" ] && [ "$ADDED" -le 10 ] 2>/dev/null; then
        PRE_COMMIT_LINES=$(( lines - ADDED ))
        if [ "$PRE_COMMIT_LINES" -ge "$PLAN_HARD_CAP" ]; then
          ADDED_CHECKBOX_LINES="$(git -C "$PM_DIR" diff --cached -- "$f" 2>/dev/null | grep -cE '^\+\s*-\s*\[.\]' || true)"
          ADDED_CHECKBOX_LINES="${ADDED_CHECKBOX_LINES:-0}"
          [ "$ADDED_CHECKBOX_LINES" = "0" ] && SMALL_MARKER_APPEND="1"
        fi
      fi
      # Link-repoint exception (see policy comment above): only when neither the marker-append
      # exception already fired, AND this diff never grows the file (ADDED<=DELETED), AND every
      # changed line's only difference (after normalizing an /plans/active/... or
      # /plans/archive/<YYYY_MM>/... path segment to a common token) is that path token -- i.e. a
      # pure same-line link-repoint, never new prose.
      if [ -z "$SMALL_MARKER_APPEND" ] && [ -n "$ADDED" ] && [ -n "$DELETED" ] \
        && [ "$DELETED" -gt 0 ] 2>/dev/null && [ "$ADDED" -le "$DELETED" ] 2>/dev/null; then
        RAW_DIFF="$(git -C "$PM_DIR" diff --cached -- "$f" 2>/dev/null || true)"
        # Same `|| true` fix as the whitespace-only-repair block above: an empty match (e.g.
        # ADDED=0 with DELETED>0) must not abort the script under pipefail+set -e.
        REMOVED_NORM="$(echo "$RAW_DIFF" | { grep -E '^-[^-]' || true; } | sed -E 's/^-//' \
          | sed -E 's#/plans/(active|archive/[0-9]{4}_[0-9]{2})/#/plans/__PATH__/#g' | sort)"
        ADDED_NORM="$(echo "$RAW_DIFF" | { grep -E '^\+[^+]' || true; } | sed -E 's/^\+//' \
          | sed -E 's#/plans/(active|archive/[0-9]{4}_[0-9]{2})/#/plans/__PATH__/#g' | sort)"
        if [ -n "$REMOVED_NORM" ] && [ "$REMOVED_NORM" = "$ADDED_NORM" ]; then
          LINK_REPOINT_EDIT="1"
        fi
      fi
      # Single-todo-checkbox-flip exception (see policy comment above, operator ruling 2026-08-15,
      # BLK-a2710376): only when neither exception above already fired, the file was already over
      # cap BEFORE this commit too (mirrors the marker-append PRE_COMMIT_LINES guard -- a doc newly
      # crossing the cap via this same commit is a real regression, not covered), the diff is
      # exactly one hunk, and exactly one checkbox line is removed and exactly one is added within
      # it.
      if [ -z "$SMALL_MARKER_APPEND" ] && [ -z "$LINK_REPOINT_EDIT" ] && [ -n "$ADDED" ] && [ -n "$DELETED" ]; then
        PRE_COMMIT_LINES_FLIP=$(( lines - ADDED + DELETED ))
        if [ "$PRE_COMMIT_LINES_FLIP" -ge "$PLAN_HARD_CAP" ]; then
          RAW_DIFF_FLIP="$(git -C "$PM_DIR" diff --cached -- "$f" 2>/dev/null || true)"
          HUNK_COUNT="$(echo "$RAW_DIFF_FLIP" | { grep -cE '^@@ ' || true; })"
          HUNK_COUNT="${HUNK_COUNT:-0}"
          REMOVED_CHECKBOXES="$(echo "$RAW_DIFF_FLIP" | { grep -cE '^-\s*-\s*\[.\]' || true; })"
          REMOVED_CHECKBOXES="${REMOVED_CHECKBOXES:-0}"
          ADDED_CHECKBOXES="$(echo "$RAW_DIFF_FLIP" | { grep -cE '^\+\s*-\s*\[.\]' || true; })"
          ADDED_CHECKBOXES="${ADDED_CHECKBOXES:-0}"
          if [ "$HUNK_COUNT" = "1" ] && [ "$REMOVED_CHECKBOXES" = "1" ] && [ "$ADDED_CHECKBOXES" = "1" ]; then
            SINGLE_TODO_FLIP="1"
          fi
        fi
      fi
    fi
    if [ -n "$WHITESPACE_ONLY_REPAIR" ]; then
      echo "  SOFT    $name  ${lines}L  todos=${todos}  (over cap pre-existing; allowed — whitespace-only repair, \`git diff -w\` empty, operator ruling 2026-08-15)"
    elif [ -n "$SMALL_MARKER_APPEND" ]; then
      echo "  SOFT    $name  ${lines}L  todos=${todos}  (over cap pre-existing; allowed — small non-checkbox marker append only, operator ruling 2026-08-02)"
    elif [ -n "$LINK_REPOINT_EDIT" ]; then
      echo "  SOFT    $name  ${lines}L  todos=${todos}  (over cap pre-existing; allowed — bounded same-line link-repoint edit only, operator ruling 2026-08-09)"
    elif [ -n "$SINGLE_TODO_FLIP" ]; then
      echo "  SOFT    $name  ${lines}L  todos=${todos}  (over cap pre-existing; allowed — single-todo checkbox flip, one hunk, operator ruling 2026-08-15 BLK-a2710376)"
    else
      echo "  HARD    $name  ${lines}L  todos=${todos}"
      HARD_FAILURES=$(( HARD_FAILURES + 1 ))
    fi
  elif [ "$lines" -gt "$PLAN_SOFT_CAP" ]; then
    echo "  SOFT    $name  ${lines}L  todos=${todos}"
  fi
done

echo ""

if [ -n "$SCOPED" ]; then
  if [ "$HARD_FAILURES" -gt 0 ]; then
    echo "❌ check_line_caps: ${HARD_FAILURES} staged plan(s)/epic(s) over cap — split before committing"
    exit 1
  fi
  [ "$QUIET" != "--quiet" ] && echo "✅ check_line_caps: staged plan(s)/epic(s) within cap"
  exit 0
fi

if [ "$UPDATE_BASELINE" = "1" ]; then
  if [ "$HARD_FAILURES" -gt "$BASELINE_COUNT" ]; then
    echo "❌ check_line_caps: refusing to raise baseline from ${BASELINE_COUNT} to ${HARD_FAILURES} — fix the new/worse violation(s) instead"
    exit 1
  fi
  sed -i.bak -E "s/^hard_count:.*/hard_count: ${HARD_FAILURES}/" "$BASELINE_PATH" && rm -f "${BASELINE_PATH}.bak"
  echo "Baseline updated: hard_count=${HARD_FAILURES} (was ${BASELINE_COUNT})"
  exit 0
fi

if [ "$HARD_FAILURES" -gt "$BASELINE_COUNT" ]; then
  echo "❌ check_line_caps: ${HARD_FAILURES} plan(s)/epic(s) over cap (baseline ${BASELINE_COUNT}) — a NEW violation landed, see plans/active/issues/plan_line_cap_remediation_2026_07_23.md"
  exit 1
elif [ "$HARD_FAILURES" -gt 0 ]; then
  [ "$QUIET" != "--quiet" ] && echo "✅ check_line_caps: ${HARD_FAILURES} pre-existing violation(s), within baseline (${BASELINE_COUNT}) — not a regression"
  exit 0
else
  [ "$QUIET" != "--quiet" ] && echo "✅ check_line_caps: no hard violations"
  exit 0
fi
