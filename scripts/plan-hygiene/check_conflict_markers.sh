#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# Conflict-marker hygiene gate — catches committed git conflict markers in plan/issue docs,
# INCLUDING the two forms the frontmatter/todo-format checks miss:
#   (1) MID-LINE markers, e.g. "...NOT a blocker). <<<<<<< Updated upstream"
#       (the other checks only look at line-start `^>>>>>>>`).
#   (2) PRETTIER-MANGLED markers, e.g. "> > > > > > > Stashed changes" — a real `>>>>>>>`
#       reflowed by `prettier --write` into nested-blockquote syntax, which then reads as
#       "valid markdown" and slips past every existing gate.
# Provenance: 2026-06-21 — a committed `<<<<<<< Updated upstream` (mid-line) + a mangled
# `> > > > > > > Stashed changes` survived in solana_defi_legacy_migration_2026_05_27.md, doubled
# a todo, and left a shipped item unflipped. This gate closes that class.
# Usage: check_conflict_markers.sh [--quiet] [files...]
#   no files -> scans plans/active/**.md + plans/active/issues/**.md
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PM_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

QUIET=0
FILES=()
for a in "$@"; do
  case "$a" in
    --quiet) QUIET=1 ;;
    *) FILES+=("$a") ;;
  esac
done
if [ "${#FILES[@]}" -eq 0 ]; then
  while IFS= read -r f; do FILES+=("$f"); done < <(find "$PM_DIR/plans/active" -name '*.md' 2>/dev/null)
fi

# Standard open/close markers (7 angle brackets never appear legitimately in prose, mid-line or
# not) OR the prettier-mangled `> > > > > > >` (>=7 nested blockquote levels — never used in plans).
PAT='(<<<<<<<|>>>>>>>)|(^|[[:space:]])(> ){6,}>'

RC=0
for f in "${FILES[@]}"; do
  [ -f "$f" ] || continue
  HITS=$(grep -nE "$PAT" "$f" 2>/dev/null) || true
  if [ -n "$HITS" ]; then
    RC=1
    if [ "$QUIET" -eq 0 ]; then
      echo "❌ conflict marker(s) in $f:"
      printf '%s\n' "$HITS" | sed 's/^/    /'
    fi
  fi
  # ── Orphaned ======= check (2026-08-10) ──────────────────────────────────────────
  # The `=======` middle-marker was deliberately excluded from PAT because a 7+ `=`
  # run collides with setext-H1 underlines (Title\n=======).  But commit 505bfe3ced
  # proved an ORPHANED `=======` (NOT serving as a setext underline) can reach LDR as
  # partial conflict debris without the open marker.  Flag lines of 7+ `=` signs NOT
  # directly under a non-empty text line.  Separator lines (>=30 `=`) are skipped as
  # a deliberate visual convention.  SSOT: committed_conflict_marker_plan_doc_2026_08_10.
  ORPHANED_EQUALS=$(awk '
    /^={7,}$/ {
      if (length($0) >= 30) next       # skip visual separator lines
      if (NR > 1 && prev !~ /^[[:space:]]*$/ && prev !~ /^={7,}$/) next  # setext underline
      print NR ":" $0
    }
    { prev = $0 }
  ' "$f" 2>/dev/null) || true
  if [ -n "$ORPHANED_EQUALS" ]; then
    RC=1
    if [ "$QUIET" -eq 0 ]; then
      echo "❌ orphaned ======= conflict marker(s) in $f:"
      printf '%s\n' "$ORPHANED_EQUALS" | sed 's/^/    /'
    fi
  fi
done

if [ "$RC" -eq 0 ] && [ "$QUIET" -eq 0 ]; then
  echo "✅ no conflict markers in ${#FILES[@]} plan/issue file(s)"
fi
exit "$RC"
