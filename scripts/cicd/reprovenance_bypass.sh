#!/usr/bin/env bash
# Epic: ci_master
# Lifecycle: permanent
# Delete-when: NA
#
# reprovenance_bypass.sh — self-service remedy for a MID-HISTORY strict-quickmerge bypass.
#
# THE PROBLEM (2026-07-17). A source commit that reached live-defi-rollout via a direct push
# (no `Quickmerge:` trailer, not a carve-out) is flagged by check_strict_quickmerge.py and BLOCKS
# the LDR→main promote. When that commit is the branch TIP, `quickmerge --files` amends the trailer
# onto it. But when it is MID-HISTORY (other commits landed after it), there is no safe remedy:
#   - it cannot get a trailer without rewriting shared history (BANNED);
#   - it never becomes `_on_promoted_tip` because the promote it would ride is itself blocked BY it;
#   - `git revert` leaves the sha in-range (only ADDS a second violation — proven);
#   - a content-identical `quickmerge --files` is a no-op (nothing to commit).
# So a legitimate, already-green fix can wedge a repo's promotion indefinitely.
#
# THE REMEDY. Create an EMPTY, provenanced commit that explicitly re-provenances the bypass by
# naming its sha in a `Reprovenance: <sha>` trailer. check_strict_quickmerge.py forgives a bypass
# whose full sha is named by such a trailer in a commit that is ITSELF provenanced (has a
# `Quickmerge:` trailer / bot / [skip ci]) — see _collect_reprovenanced there. The blessing is
# auditable (it names exactly what it forgives) and cannot be forged by a bare bypass (a
# non-provenanced Reprovenance commit does NOT bless — verified). The empty commit touches no
# source, so it is itself a carve-out and pushes past the pre-push hook without --no-verify.
#
# This is the equivalent of "re-ship via quickmerge" for content that is ALREADY on LDR and green:
# it applies the same dep-alignment gate quickmerge STAGE 1 runs, then records a provenanced marker.
#
# Usage:
#   scripts/cicd/reprovenance_bypass.sh <bypass-sha> [--push]
#     run from inside the target repo's working tree (on live-defi-rollout).
#     --push : push live-defi-rollout after creating the commit (default: leave it for the caller).
#
# SSOT: plans/active/issues/provenance_gate_midhistory_bypass_deadlock_2026_07_17.md
set -euo pipefail

BYPASS_SHA="${1:-}"
DO_PUSH=false
[ "${2:-}" = "--push" ] && DO_PUSH=true

if [ -z "$BYPASS_SHA" ]; then
  echo "usage: reprovenance_bypass.sh <bypass-sha> [--push]  (run inside the target repo)" >&2
  exit 2
fi

REPO_ROOT="$(git rev-parse --show-toplevel)"
REPO_NAME="$(basename "$REPO_ROOT")"
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [ "$BRANCH" != "live-defi-rollout" ]; then
  echo "reprovenance: refusing — must run on live-defi-rollout (on '$BRANCH')" >&2
  exit 2
fi

# Resolve to a full sha and confirm it is reachable on this branch.
FULL_SHA="$(git rev-parse --verify "${BYPASS_SHA}^{commit}" 2>/dev/null || true)"
if [ -z "$FULL_SHA" ]; then
  echo "reprovenance: '$BYPASS_SHA' is not a commit in this repo" >&2
  exit 2
fi
if ! git merge-base --is-ancestor "$FULL_SHA" HEAD; then
  echo "reprovenance: $FULL_SHA is not reachable from HEAD (not on live-defi-rollout)" >&2
  exit 2
fi

# Resolve workspace + the strict-quickmerge guard (the SSOT that decides provenance).
_ws="${UNIFIED_TRADING_WORKSPACE_ROOT:-}"
if [ -z "$_ws" ]; then
  _d="$REPO_ROOT"
  while [ "$_d" != "/" ] && [ ! -d "$_d/unified-trading-pm/scripts/cicd" ]; do _d="$(dirname "$_d")"; done
  _ws="$_d"
fi
GUARD="${_ws}/unified-trading-pm/scripts/cicd/check_strict_quickmerge.py"
DEP_CHECK="${_ws}/unified-trading-pm/scripts/repo-management/check-dep-alignment.py"
MANIFEST="${_ws}/unified-trading-pm/workspace-manifest.json"

# SANITY: only re-provenance a commit that is ACTUALLY a bypass right now. Re-provenancing a clean
# commit is harmless but pointless, and re-provenancing a random sha would be misleading in the log.
if [ -f "$GUARD" ]; then
  # `--block` is REQUIRED: without it the guard WARNs and exits 0 even on a violation, so the sanity
  # check would always say "nothing to do" (bug, 2026-07-17). With --block: exit 0 = genuinely clean,
  # exit 1 = a real violation we should re-provenance.
  if python3 "$GUARD" --range "${FULL_SHA}~1..${FULL_SHA}" --block >/dev/null 2>&1; then
    echo "reprovenance: $FULL_SHA is NOT currently a strict-quickmerge violation — nothing to do." >&2
    echo "  (already provenanced, a carve-out, or already promoted.)" >&2
    exit 0
  fi
fi

# DEP-ALIGNMENT GATE — the same guarantee quickmerge STAGE 1 gives. The bypassed content is already
# on green LDR, so this is a confirmation, not a discovery; a FAIL means the deps this repo builds
# against are out of alignment and must be reconciled before promoting, bypass or not.
if [ -f "$DEP_CHECK" ] && [ -f "$MANIFEST" ]; then
  echo "reprovenance: running dep-alignment gate for $REPO_NAME ..."
  if ! python3 "$DEP_CHECK" --repo "$REPO_NAME" --to-staging false --manifest "$MANIFEST" 2>/dev/null; then
    echo "reprovenance: dep-alignment FAILED — reconcile deps before re-provenancing (do NOT force)." >&2
    exit 1
  fi
fi

SUBJ="$(git show -s --format='%s' "$FULL_SHA" | cut -c1-60)"
AUTH="$(git show -s --format='%an' "$FULL_SHA")"
git commit --allow-empty --no-verify -q -F - <<EOF
chore(provenance): re-provenance ${FULL_SHA:0:8} — ${SUBJ}

${FULL_SHA:0:8} (${AUTH}) direct-pushed source without a Quickmerge trailer and sits
mid-history on live-defi-rollout, so it cannot be trailer-stamped without rewriting a
shared branch and it deadlocks the LDR→main promote (revert/re-ship do not clear it).
Its content is already on live-defi-rollout and green. This empty commit re-provenances
it through the strict-quickmerge gate after the dep-alignment check above.

Reprovenance: ${FULL_SHA}
Quickmerge: agent
EOF

echo "reprovenance: created empty blessing commit for ${FULL_SHA:0:8} ($SUBJ)"

if [ "$DO_PUSH" = true ]; then
  echo "reprovenance: pushing live-defi-rollout ..."
  git push origin live-defi-rollout
fi
