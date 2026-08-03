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
# plans/active/issues/prettier_prosewrap_mangles_long_inline_code_spans_2026_07_31.md
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
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PM_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
BASELINE_PATH="$SCRIPT_DIR/prosewrap_padding_baseline.yaml"

INDENT_THRESHOLD=14

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

  HITS="$(awk -v thresh="$INDENT_THRESHOLD" '
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
  ' "$f")" || true

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
    echo "❌ check_prosewrap_padding: ${TOTAL} violating line(s) (baseline ${BASELINE_COUNT}) — a NEW prosewrap-padding instance landed (or an existing one grew). See plans/active/issues/prettier_prosewrap_mangles_long_inline_code_spans_2026_07_31.md for the repair recipe. Never raise the baseline."
  fi
fi

if [ -n "$UPDATE_BASELINE" ]; then
  NEW_COUNT="$TOTAL"
  if [ "$BASELINE_COUNT" -gt 0 ] && [ "$NEW_COUNT" -gt "$BASELINE_COUNT" ]; then
    NEW_COUNT="$BASELINE_COUNT"
  fi
  cat > "$BASELINE_PATH" <<EOF
# Baseline for check_prosewrap_padding.sh — prettier proseWrap continuation-padding corruption
# (see plans/active/issues/prettier_prosewrap_mangles_long_inline_code_spans_2026_07_31.md for the
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
