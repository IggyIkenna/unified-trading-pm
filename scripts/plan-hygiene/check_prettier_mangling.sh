#!/usr/bin/env bash
# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: NA
# Prettier emphasis-mangling gate — catches underscore identifiers that prettier (<3.9.5, with
# proseWrap: always) deterministically rewrites as asterisks in prose, e.g.:
#   data_type  -> data*type      asset_group -> asset*group     schema_version -> schema*version
#   LIVE_/BATCH_ -> LIVE*/BATCH\_ (meaning-inverting in normative text, quality-gates.md L1 row)
# Root cause + repair recipe + the four trigger classes:
#   plans/active/issues/prettier_emphasis_mangling_corpus_corruption_2026_07_14.md
# Reference repairs: unified-trading-pm@169a8c8cd @65420c363 @f54f0e9d6 (13 codex SSOTs,
# operator-approved 2026-07-14). Primary fix is the >=3.9.5 version guard in
# scripts/hooks/prettier-autostage.sh; this gate is the backstop so a host that slips through
# (old global binary, hook not installed) cannot LAND mangled text on the integration branch.
#
# Pattern notes: curated, low-false-positive signature. Legit constructs it must NOT flag:
#   globs (`data_type=*/`, `venue=*`), escaped wildcards (`\*_manifest_...`), arithmetic (8*3600),
#   bold (**WORD**), and docs QUOTING the mangled forms inside fenced code blocks (the issue doc).
# Fenced code blocks are therefore skipped entirely before matching.
# Usage: check_prettier_mangling.sh [--quiet] [files...]
#   no files -> scans plans/**.md (active+epics+audit) + codex/**.md
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
  while IFS= read -r f; do FILES+=("$f"); done < <(
    find "$PM_DIR/plans/active" "$PM_DIR/plans/epics" "$PM_DIR/plans/audit" "$PM_DIR/codex" \
      -name '*.md' 2>/dev/null
  )
fi

# Curated mangle signature. Each alternative is a token that only exists as formatter damage
# in BARE PROSE (inline code spans + fenced blocks are stripped before matching, so genuine
# backticked wildcards like `ticks_migrated*\*.parquet` and docs quoting the mangled forms as
# examples never self-flag; a mangle hiding INSIDE a code span is out of scope for this gate —
# the >=3.9.5 version guard in prettier-autostage.sh is the primary stop):
#   {mode}*{source} / asset*group / schema*version / pipeline*mode / instrument*type / data*type
#   record*captured|failed|empty / last*updated / "x*y_z < v9"-shaped version exprs
# Extend this list when a new mangled family is found (add the mangled form, never the clean one).
PAT='\{mode\}\*\{source\}|asset\*group|schema\*version|pipeline\*mode|instrument\*type|data\*type|record\*(captured|failed|empty)|last\*updated|[a-z]\*[a-z_]+ < v9'

RC=0
for f in "${FILES[@]}"; do
  [ -f "$f" ] || continue
  # Preprocess: blank out fenced code blocks (``` ... ```), then inline code spans (`...`),
  # keeping line numbers stable (fences emit empty lines; spans are removed in-line).
  HITS=$(awk 'BEGIN{fence=0} /^[[:space:]]*```/{fence=!fence; print ""; next} {print fence?"":$0}' "$f" \
    | sed 's/`[^`]*`//g' \
    | grep -nE "$PAT" 2>/dev/null) || true
  if [ -n "$HITS" ]; then
    RC=1
    if [ "$QUIET" -eq 0 ]; then
      echo "❌ prettier emphasis-mangling in $f (underscore rewritten as asterisk — see plans/active/issues/prettier_emphasis_mangling_corpus_corruption_2026_07_14.md for the repair recipe):"
      printf '%s\n' "$HITS" | sed 's/^/    /'
    fi
  fi
done

if [ "$RC" -eq 0 ] && [ "$QUIET" -eq 0 ]; then
  echo "✅ no prettier emphasis-mangling in ${#FILES[@]} file(s)"
fi
exit "$RC"
