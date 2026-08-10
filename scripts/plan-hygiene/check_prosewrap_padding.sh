#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# Prettier proseWrap continuation-padding gate — catches a SECOND, distinct prettier corruption
# class from check_prettier_mangling.sh's emphasis-mangling check: the workspace `.prettierrc`
# (proseWrap: always, printWidth: 120) has a non-idempotent reflow bug for wrapped paragraphs
# nested as a 2nd+ block inside a list item. Reformatting the SAME already-wrapped paragraph
# repeatedly (e.g. one `docs(plans):` commit per unrelated todo-flip, each running prettier over
# the whole file via prettier-autostage.sh) does not converge — each pass ADDS leading-space
# padding to the paragraph's continuation lines instead of re-deriving a stable wrap. Confirmed
# reproducible with prettier 3.9.5 AND 3.9.6 (latest at time of investigation), with or WITHOUT an
# inline backtick code span present — so despite the originating issue doc's framing, this is not
# specifically an inline-code-unbreakable-token bug, it's a broader list-item-continuation
# idempotency bug in prettier's markdown proseWrap printer. Root-cause + repro recipe:
# plans/archive/issues/prettier_prosewrap_mangles_long_inline_code_spans_2026_07_31.md
#
# Corpus impact discovered while root-causing (2026-08-03): NOT limited to the 2 originally-
# flagged instances — a corpus-wide survey found 80+ active plan/issue/codex docs already carrying
# this padding (up to 1290 leading spaces on one line in
# plans/active/tradfi_satellite_ao_dispatch_batch2_2026_07_25.md, a content mirror of the doc that
# introduced the original 2 flagged instances, repeatedly reformatted across many more commits).
# See plans/active/issues/prosewrap_padding_corpus_wide_1290_space_2026_08_03.md for the full
# scope + tracked remediation todos — NOT fixed by this gate; this gate only stops the bleeding.
#
# Because the corpus already carries this debt, this is a SHRINKING RATCHET (same shape as
# check_line_caps.sh / check_archive_candidates.sh / check_reference_paths.py): a live count
# EXCEEDING the baseline means a NEW instance landed (or an existing one got worse) — fix it, don't
# raise the baseline. Lower the baseline as flagged lines get hand-repaired.
#
# Two independent detectors (either one flags a line — union, deduped per file:line):
#   (1) A backtick-delimited inline-code span containing 3+ consecutive spaces (real inline code —
#       identifiers, CLI flags, commit shas — never legitimately contains a 3+ space run; matches
#       the original issue doc's own example: `market-tick-data-     service@92037f45`).
#   (2) A non-blank, non-table (`^\s*|`), non-fenced-code-block line with a leading-whitespace run
#       >= INDENT_THRESHOLD (14) spaces. Calibrated 2026-08-03 against the live corpus: the deepest
#       LEGITIMATE list-continuation indent found anywhere in plans/active + plans/epics + codex
#       (excluding already-known-corrupted docs) was 10 spaces; the smallest REAL corruption
#       instance observed (the very first, single-pass case) was 18 spaces. 14 sits with margin on
#       both sides of that gap.
#
# Usage: check_prosewrap_padding.sh [--quiet] [--update-baseline] [files...]
#   no files -> scans plans/active + plans/epics + plans/audit + codex (plans/archive excluded —
#     historical record, out of repair scope, same convention as check_prettier_mangling.sh)
#   check_prosewrap_padding.sh --only <path> [<path> ...]
#
# ``--only <paths>`` (2026-08-09, precommit migration): this ratchet previously had NO
# precommit-time presence, only the full corpus-wide baseline mode — so a docs(plans) commit
# introducing a NEW prosewrap-padding instance had zero enforcement at commit time and only
# surfaced hours/days later when an unrelated commit happened to trigger the next full
# quality-gates.sh run, misattributed to that unrelated commit's SHA. Same fast-path-blind-to-
# full-gate pattern as the other checks migrated this evening (check_todo_regression.sh,
# check_effort_signal_ratchet.py, check_evidence_backed_completion.py).
#
# Deliberately NOT "does this staged file's TOTAL violation count exceed the corpus baseline" —
# the baseline is corpus-wide (4472 at time of writing); a handful of violations in 1-2 staged
# files would never approach it, defeating the point. Instead --only compares, PER STAGED FILE,
# the SET of violation signatures (detector-type + matched content, not line number — line
# numbers shift on every edit) at the current working-tree content vs `git show HEAD:<path>`'s
# content, using the exact same detector (_detect_hits below) for both sides so the two modes
# can never define "a violation" differently. Only a signature new in the current content (not
# present at HEAD) is flagged — a violation already sitting in the file at HEAD is pre-existing
# debt covered by the full-sweep ratchet, not this commit's problem, matching the shape of
# check_effort_signal_ratchet.py's --only mode.
set -uo pipefail
# Force byte-wise (locale-independent) collation for every sort/comm call below. Under a
# UTF-8-aware locale, sort/comm invoke strcoll() on multibyte content; a locale/glibc
# combination that trips on that content fails with "sort: string comparison failed:
# Illegal byte sequence" and — because the callers below don't check sort's exit code —
# the failure is silent, degrading into a truncated/empty comparison set that false-flags
# byte-identical HEAD content as a NEW violation. LC_ALL=C makes sort/comm compare raw
# bytes, which is also strictly correct here since these comparisons only need exact-match
# set membership, never locale-aware ordering.
export LC_ALL=C
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PM_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
BASELINE_PATH="$SCRIPT_DIR/prosewrap_padding_baseline.yaml"

INDENT_THRESHOLD=14

# Shared detector — reads from the file given as $1, or from stdin if called with no args (used
# for `git show HEAD:<path>` content, which has no filesystem path of its own). Prints
# "FNR:type:content" per violating line; callers needing a HEAD-vs-current SIGNATURE (--only
# mode) strip the leading "FNR:" since line numbers shift between the two versions.
_detect_hits() {
  awk -v thresh="$INDENT_THRESHOLD" '
    /^[[:space:]]*```/ { fence = !fence; next }
    fence { next }
    {
      # Detector 1: 3+ consecutive spaces inside a backtick-delimited span, anywhere on the line
      # (runs on the RAW line — table rows can legitimately pad backtick spans for column
      # alignment, so skip table rows for this detector too).
      is_table = ($0 ~ /^[[:space:]]*\|/)
      if (!is_table) {
        s = $0
        while (match(s, /`[^`]*`/)) {
          span = substr(s, RSTART, RLENGTH)
          if (span ~ /   /) {
            print FNR":backtick-padding:" span
            break
          }
          s = substr(s, RSTART + RLENGTH)
        }
      }

      # Detector 2: over-indented continuation line (non-blank, non-table, outside fences).
      if (!is_table && $0 !~ /^[[:space:]]*$/) {
        match($0, /^ */)
        if (RLENGTH >= thresh) {
          print FNR":over-indent(" RLENGTH "):" substr($0, RLENGTH + 1, 50)
        }
      }
    }
  ' "$@"
}

# All eligible-for-detector-2 lines (non-blank, non-table, outside fences) reduced to
# "leading whitespace stripped, first 50 chars" -- the SAME content-preview shape
# _detect_hits' over-indent branch prints, but for EVERY line, not just ones that
# happen to cross INDENT_THRESHOLD. Used by --only below to recognize pre-existing
# prose that merely crossed the threshold on THIS pass (see rec. (A) comment there).
_all_content_previews() {
  awk '
    /^[[:space:]]*```/ { fence = !fence; next }
    fence { next }
    {
      is_table = ($0 ~ /^[[:space:]]*\|/)
      if (!is_table && $0 !~ /^[[:space:]]*$/) {
        match($0, /^ */)
        print substr($0, RLENGTH + 1, 50)
      }
    }
  ' "$@"
}

if [ "${1:-}" = "--only" ]; then
  shift
  QUIET=0
  ONLY_FILES=()
  for a in "$@"; do
    case "$a" in
      --quiet) QUIET=1 ;;
      *) ONLY_FILES+=("$a") ;;
    esac
  done
  FLAGGED_FILES=0
  for f in "${ONLY_FILES[@]}"; do
    [ -f "$f" ] || continue
    case "$f" in
      */plans/archive/*|plans/archive/*) continue ;;
    esac
    rel="$(cd "$(dirname "$f")" && pwd)/$(basename "$f")"
    rel="${rel#"$PM_DIR"/}"
    head_content="$(git -C "$PM_DIR" show "HEAD:$rel" 2>/dev/null)"

    # Detector 1 (backtick-padding): compare against HEAD's own violations only -- this
    # detector isn't threshold-based, so it isn't subject to the rec. (A) gap below.
    cur_backtick="$(_detect_hits "$f" | grep ':backtick-padding:' | sed -E 's/^[0-9]+://' | sort -u)"
    head_backtick="$(printf '%s' "$head_content" | _detect_hits | grep ':backtick-padding:' | sed -E 's/^[0-9]+://' | sort -u)"
    new_backtick=""
    [ -n "$cur_backtick" ] && new_backtick="$(comm -23 <(printf '%s\n' "$cur_backtick") <(printf '%s\n' "$head_backtick") 2>/dev/null || true)"

    # Detector 2 (over-indent): 2026-08-09 rec. (A),
    # prosewrap_padding_precommit_gate_blocks_already_affected_files_2026_08_09.md.
    # prettier-autostage's mandatory reformat is a non-idempotent, MONOTONIC reflow for a
    # paragraph nested 2+ deep in a checkbox list item -- every pass can shift a line's
    # indent further, INCLUDING lines that sat comfortably under INDENT_THRESHOLD at HEAD
    # and only cross it because of THIS pass's reflow (comparing HEAD's own violations,
    # as detector 1 does, misses this case -- HEAD never flagged that line in the first
    # place, so a naive comm(1) still reads it as brand new). Instead: a current
    # over-indent hit is "new" only if its TEXT (leading whitespace stripped) does not
    # appear ANYWHERE in HEAD's content -- i.e. genuinely worker-authored, not prose that
    # already existed at HEAD (at any indent, flagged there or not) and merely got
    # reflowed past the threshold this pass.
    cur_overindent="$(_detect_hits "$f" | grep ':over-indent(' | sed -E 's/^[0-9]+:over-indent\([0-9]+\)://' | sort -u)"
    head_all_content="$(printf '%s' "$head_content" | _all_content_previews | sort -u)"
    new_overindent=""
    [ -n "$cur_overindent" ] && new_overindent="$(comm -23 <(printf '%s\n' "$cur_overindent") <(printf '%s\n' "$head_all_content") 2>/dev/null || true)"

    new_sigs="$(printf '%s\n%s\n' "$new_backtick" "$new_overindent" | grep -v '^$' || true)"

    if [ -n "$new_sigs" ]; then
      FLAGGED_FILES=$(( FLAGGED_FILES + 1 ))
      if [ "$QUIET" -eq 0 ]; then
        N=$(printf '%s\n' "$new_sigs" | grep -c .)
        echo "${f#"$PM_DIR"/} (${N} new line(s)):"
        printf '%s\n' "$new_sigs" | sed 's/^/    /'
      fi
    fi
  done
  if [ "$FLAGGED_FILES" -gt 0 ]; then
    echo "❌ check_prosewrap_padding (--only): ${FLAGGED_FILES} staged file(s) with a NEW prosewrap-padding instance — see plans/archive/issues/prettier_prosewrap_mangles_long_inline_code_spans_2026_07_31.md for the repair recipe."
    echo "   scripts/plan-hygiene/fix_prosewrap_padding.py <file> automates that repair — but it is WHOLE-FILE scoped, so it will also rewrite pre-existing corruption elsewhere in the file (measured: up to 51 lines in one active plan). Run it, then review the diff and keep only the lines this commit introduced; do not stage the incidental rest, or you widen the conflict surface on the busiest file class in the repo. It is deliberately NOT auto-wired here for that reason."
    exit 1
  fi
  [ "$QUIET" -eq 0 ] && echo "✅ check_prosewrap_padding (--only): 0 new violation(s) in staged files"
  exit 0
fi

QUIET=0
UPDATE_BASELINE=""
FILES=()
for a in "$@"; do
  case "$a" in
    --quiet) QUIET=1 ;;
    --update-baseline) UPDATE_BASELINE="1" ;;
    *) FILES+=("$a") ;;
  esac
done
if [ "${#FILES[@]}" -eq 0 ]; then
  while IFS= read -r f; do FILES+=("$f"); done < <(
    find "$PM_DIR/plans/active" "$PM_DIR/plans/epics" "$PM_DIR/plans/audit" "$PM_DIR/codex" \
      -name '*.md' 2>/dev/null
  )
fi

BASELINE_COUNT="$(grep -E '^violation_count:' "$BASELINE_PATH" 2>/dev/null | sed -E 's/^violation_count:[[:space:]]*//')"
BASELINE_COUNT="${BASELINE_COUNT:-0}"

TOTAL=0
FOUND=()
for f in "${FILES[@]}"; do
  [ -f "$f" ] || continue
  case "$f" in
    */plans/archive/*|plans/archive/*) continue ;;
  esac

  HITS="$(_detect_hits "$f")" || true

  if [ -n "$HITS" ]; then
    N=$(printf '%s\n' "$HITS" | grep -c .)
    TOTAL=$(( TOTAL + N ))
    if [ "$QUIET" -eq 0 ]; then
      FOUND+=("${f#"$PM_DIR"/} (${N} line(s)):")
      while IFS= read -r h; do FOUND+=("    $h"); done <<< "$HITS"
    fi
  fi
done

if [ "$QUIET" -eq 0 ]; then
  echo "Prettier proseWrap continuation-padding (prosewrap_padding gate):"
  echo ""
  for line in "${FOUND[@]:-}"; do
    [ -n "$line" ] && echo "  $line"
  done
  echo ""
fi

OK=1
[ "$TOTAL" -gt "$BASELINE_COUNT" ] && OK=0

if [ "$QUIET" -eq 0 ]; then
  if [ "$OK" -eq 1 ]; then
    echo "✅ check_prosewrap_padding: ${TOTAL} violating line(s) (baseline ${BASELINE_COUNT})"
  else
    echo "❌ check_prosewrap_padding: ${TOTAL} violating line(s) (baseline ${BASELINE_COUNT}) — a NEW prosewrap-padding instance landed (or an existing one grew). See plans/archive/issues/prettier_prosewrap_mangles_long_inline_code_spans_2026_07_31.md for the repair recipe. Never raise the baseline."
  fi
fi

if [ -n "$UPDATE_BASELINE" ]; then
  NEW_COUNT="$TOTAL"
  if [ "$BASELINE_COUNT" -gt 0 ] && [ "$NEW_COUNT" -gt "$BASELINE_COUNT" ]; then
    NEW_COUNT="$BASELINE_COUNT"
  fi
  cat > "$BASELINE_PATH" <<EOF
# Baseline for check_prosewrap_padding.sh — prettier proseWrap continuation-padding corruption
# (see plans/archive/issues/prettier_prosewrap_mangles_long_inline_code_spans_2026_07_31.md for the
# root cause + repro recipe, and
# plans/active/issues/prosewrap_padding_corpus_wide_1290_space_2026_08_03.md for the corpus-wide
# remediation backlog this baseline tracks down over time).
#
# This is a SHRINKING ratchet (same shape as line_caps_baseline.yaml / archive_candidates_baseline.
# yaml / reference_paths_baseline.yaml). violation_count is the number of pre-existing violating
# lines the gate tolerates. A live count EXCEEDING this fails the check — a NEW instance landed (or
# an existing one grew further under repeated prettier passes), fix it, don't raise the number.
# LOWER it (re-run \`check_prosewrap_padding.sh --update-baseline\`) as flagged lines get hand-
# repaired. NEVER hand-raise it.
violation_count: ${NEW_COUNT}
EOF
  [ "$QUIET" -eq 0 ] && echo "Baseline updated: ${NEW_COUNT}"
fi

exit $(( 1 - OK ))
