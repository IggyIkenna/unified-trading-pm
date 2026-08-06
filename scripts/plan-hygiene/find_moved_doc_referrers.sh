#!/usr/bin/env bash
# Epic: agent_operating_framework_master
# Lifecycle: RECURRING — invoked by /plan-reconcile Phase 1 hunter 9 on every run.
# Delete-when: check_reference_paths.py grows a per-move (non-ratcheted) mode that reports
#              itemized dangling referrers for a specific archival/rename, making this redundant.
#
# ── Why this exists ───────────────────────────────────────────────────────────────────────────
# When a plan/codex doc is archived or renamed, the 6-step archival ritual requires updating every
# referrer corpus-wide. The existing gate does NOT reliably catch a missed one, for two measured
# reasons (verified by reading the code, 2026-08-02, re-confirmed 2026-08-06):
#
#   (a) run_hygiene_sweep.sh invokes check_reference_paths.py with --quiet, which suppresses the
#       itemized per-file violation list. Only a binary pass/fail reaches the sweep output, so a
#       reconcile pass has nothing to adjudicate even when the gate is red.
#   (b) it is a SHRINKING-RATCHET check with real slack. A single move that breaks 3-80 referrers
#       can land entirely inside that slack without pushing the corpus-wide total over the ceiling,
#       especially if unrelated fixes elsewhere offset it in the same window.
#
# Net: for INLINE BODY-TEXT references — the dominant shape, since an archival breaks citations
# scattered through OTHER docs' prose, not just their `related:` frontmatter — the standing gate
# gives no per-move specificity. This script closes that gap by diffing actual git moves and
# grepping the live tree for each old path. It is deterministic and ungated by any ratchet: the
# old path is gone, the new one exists, and a grep hit names exactly which doc and line.
#
# ── Traps hit while getting this right (do not re-learn these) ────────────────────────────────
#  1. Frontmatter referrers (`related:`/`depends_on:`/`supersedes:`) are ALREADY caught reliably by
#     /plan-reconcile's own Phase 0 inventory parse. Do not treat those hits as new findings — this
#     script exists for the body-text gap only.
#  2. The "archived doc cited by bare basename from an active doc" signal is FAR too noisy to gate
#     on — a 2026-08-06 run produced 470 such blocks, nearly all legitimate. The archival discipline
#     explicitly permits citing an archived doc as a historical FACT; only a live PATH pointer is a
#     defect. That check is emitted separately below and is ADVISORY.
#  3. A doc that "moved" but whose old path still exists (moved back, or re-created) is not a
#     finding — skip it, or you report churn as breakage.
#  4. Some dangling refs are deliberate historical/provenance citations to a doc that was MERGED
#     away rather than archived (e.g. a codex SSOT's own summary recording what it absorbed).
#     Those are correct as written. Read the hit before "fixing" it.
#
# Usage:  bash scripts/plan-hygiene/find_moved_doc_referrers.sh [SINCE]      # default: 14 days ago
#         SINCE is any git --since expression, e.g. 2026-07-25 or "3 days ago".
# Exit:   0 always (reporting tool; the caller adjudicates). Hard findings are printed under
#         "OLD-PATH REF" — each is a live path pointer whose target provably moved.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT" || exit 1

SINCE="${1:-14 days ago}"
TMPDIR_BASE="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_BASE"' EXIT
OLDPATHS="$TMPDIR_BASE/oldpaths.txt"

# Collect old paths from both renames (R) and deletions (D) — an archival shows up as either,
# depending on whether git detected the rename.
{
  git log --diff-filter=R --name-status --since="$SINCE" -- plans/ codex/ 2>/dev/null | awk '/^R/{print $2}'
  git log --diff-filter=D --name-only --since="$SINCE" -- plans/ codex/ 2>/dev/null | grep -E '^(plans|codex)/.*\.md$'
} | sort -u >"$OLDPATHS"

echo "find_moved_doc_referrers: $(wc -l <"$OLDPATHS") moved/deleted doc path(s) since $SINCE"
echo

hard=0
while IFS= read -r old; do
  [ -n "$old" ] || continue
  # Trap 3: the path still resolves — not a move that broke anything.
  [ -e "$old" ] && continue

  base="$(basename "$old")"
  newloc="$(find plans codex -name "$base" -not -path '*/node_modules/*' 2>/dev/null | head -1)"

  # HARD finding: a live, leading-slash path pointer to the old location.
  hits="$(grep -rn --include='*.md' -F "/$old" \
    plans/active plans/epics codex cursor-configs agents CLAUDE.md 2>/dev/null | head -20)"
  if [ -n "$hits" ]; then
    echo "### OLD-PATH REF: $old"
    echo "    now at: ${newloc:-<NOT FOUND — merged away or deleted outright>}"
    printf '    %s\n' "$hits"
    echo
    hard=$((hard + 1))
  fi
done <"$OLDPATHS"

echo "───────────────────────────────────────────────────────────────"
echo "HARD findings (live path pointers to a moved target): $hard"
echo
echo "NOTE: bare-basename citations of archived docs from active docs are deliberately NOT"
echo "reported — see trap 2 in this script's header. Citing an archived doc as a historical"
echo "FACT is permitted by the archival discipline; only a live PATH pointer is a defect."
echo
echo "Complement this with the itemized existence list the sweep hides:"
echo "  python3 scripts/plan-hygiene/check_reference_paths.py        # WITHOUT --quiet"
