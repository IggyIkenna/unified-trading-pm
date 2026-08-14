#!/usr/bin/env bash
# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: NA
# Prettier emphasis-mangling gate — catches underscore identifiers that prettier (<3.9.5, with
# proseWrap: always) deterministically rewrites as asterisks in prose, e.g.:
#   data_type  -> data*type      asset_group -> asset*group     schema_version -> schema*version
#   LIVE_/BATCH_ -> LIVE*/BATCH\_ (meaning-inverting in normative text, quality-gates.md L1 row)
# Root cause + repair recipe + the four trigger classes:
#   plans/archive/issues/prettier_emphasis_mangling_corpus_corruption_2026_07_14.md
# Reference repairs: unified-trading-pm@169a8c8cd @65420c363 @f54f0e9d6 (13 codex SSOTs,
# operator-approved 2026-07-14). Primary fix is the >=3.9.5 version guard in
# scripts/hooks/prettier-autostage.sh; this gate is the backstop so a host that slips through
# (old global binary, hook not installed) cannot LAND mangled text on the integration branch.
#
# Pattern notes: curated, low-false-positive signature. Legit constructs it must NOT flag:
#   globs (`data_type=*/`, `venue=*`), escaped wildcards (`\*_manifest_...`), arithmetic (8*3600),
#   bold (**WORD**), and docs QUOTING the mangled forms inside fenced code blocks (the issue doc).
# Fenced code blocks are therefore skipped entirely before matching.
# Usage: check_prettier_mangling.sh [--quiet] [--strict] [files...]
#   no files -> scans plans/**.md (active+epics+audit) + codex/**.md
#   --strict -> ALSO applies a broader, noisier heuristic (any `alnum*identifier` span) on top of
#     the curated signature below. Catches mangled families the curated list hasn't been extended
#     to yet (e.g. `defi*delta_one_funding_oi_...` from the 2026-08-01 recurrence, which the
#     curated list missed) at the cost of more false positives on legit `word*word`-shaped text.
#     Opt-in only — NOT wired into the default precommit gate (raw_npx_prettier_bypasses_version_
#     guard_recurs_mangling_2026_08_01.md's own todo 2: widen without raising the default gate's
#     false-positive rate). Use for periodic/manual deeper corpus sweeps.
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PM_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

QUIET=0
STRICT=0
FILES=()
for a in "$@"; do
  case "$a" in
    --quiet) QUIET=1 ;;
    --strict) STRICT=1 ;;
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
#   record*captured|failed|empty / last*updated / task*id / dispatch*id / ORCHESTRATOR*\* /
#   "x*y_z < v9"-shaped version exprs
# Extend this list when a new mangled family is found (add the mangled form, never the clean one).
# task*id / dispatch*id / ORCHESTRATOR*\* added 2026-08-14 (plan_reconciler_findings_ao_2026_08_10.md
# "run_hygiene_sweep.sh prettier check reported PASS despite 5 confirmed live instances" follow-up) —
# these 3 identifier families weren't in the curated list yet, so the default (non-strict) sweep
# missed them even though --strict's broader alnum*identifier heuristic would have caught them.
PAT='\{mode\}\*\{source\}|asset\*group|schema\*version|pipeline\*mode|instrument\*type|data\*type|record\*(captured|failed|empty)|last\*updated|task\*id|dispatch\*id|ORCHESTRATOR\*\\\*|[a-z]\*[a-z_]+ < v9'

# --strict-only broader heuristic (2026-08-01, raw_npx_prettier_bypasses_version_guard_recurs_
# mangling_2026_08_01.md todo 2): any `alnum` immediately followed by `*` immediately followed by
# an identifier char. Naturally excludes bold markdown (`**` — second `*` isn't `[a-zA-Z_]`),
# globs (`prefix=*` — char before `*` usually isn't alnum, or nothing legit follows), and
# arithmetic (`8*3600` — digits after `*` don't match `[a-zA-Z_]`). Still noisier than the curated
# list (a real `n*items`-shaped expression in bare prose would false-positive) — that tradeoff is
# why this only runs under --strict, never the default precommit gate.
STRICT_PAT='[a-zA-Z0-9]\*[a-zA-Z_]+'

RC=0
for f in "${FILES[@]}"; do
  [ -f "$f" ] || continue
  # plans/archive/** copies are explicitly out of repair scope (left as historical record —
  # see the issue doc's "Affected inventory" section) when this script's own default file-discovery
  # glob runs (no args: plans/active + plans/epics + plans/audit + codex, archive excluded). But an
  # explicit-paths invocation (e.g. the precommit hook passing staged files) bypassed that exclusion,
  # permanently blocking any future edit to an already-mangled archived doc for pre-existing,
  # out-of-scope corruption unrelated to the edit. Apply the same exclusion here for consistency.
  case "$f" in
    */plans/archive/*|plans/archive/*) continue ;;
  esac
  # Preprocess: blank out fenced code blocks (``` ... ```), then inline code spans (`...`),
  # keeping line numbers stable (fences emit empty lines; spans are removed in-line).
  STRIPPED=$(awk 'BEGIN{fence=0} /^[[:space:]]*```/{fence=!fence; print ""; next} {print fence?"":$0}' "$f" \
    | sed 's/`[^`]*`//g')
  HITS=$(printf '%s\n' "$STRIPPED" | grep -nE "$PAT" 2>/dev/null) || true
  if [ -n "$HITS" ]; then
    RC=1
    if [ "$QUIET" -eq 0 ]; then
      echo "❌ prettier emphasis-mangling in $f (underscore rewritten as asterisk — see plans/archive/issues/prettier_emphasis_mangling_corpus_corruption_2026_07_14.md for the repair recipe):"
      printf '%s\n' "$HITS" | sed 's/^/    /'
    fi
  fi
  if [ "$STRICT" -eq 1 ]; then
    STRICT_HITS=$(printf '%s\n' "$STRIPPED" | grep -nE "$STRICT_PAT" 2>/dev/null) || true
    if [ -n "$STRICT_HITS" ]; then
      RC=1
      if [ "$QUIET" -eq 0 ]; then
        echo "⚠️  --strict broader heuristic hit in $f (review for mangling — may be a legit alnum*identifier span):"
        printf '%s\n' "$STRICT_HITS" | sed 's/^/    /'
      fi
    fi
  fi
done

if [ "$RC" -eq 0 ] && [ "$QUIET" -eq 0 ]; then
  echo "✅ no prettier emphasis-mangling in ${#FILES[@]} file(s)"
fi
exit "$RC"
