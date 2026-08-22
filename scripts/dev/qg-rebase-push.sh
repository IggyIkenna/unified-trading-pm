#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
#
# qg-rebase-push.sh — close the "local QG green but CI red" gap for per-repo LDR pushes.
#
# WHY THIS EXISTS (verified 2026-05-25):
#   Local `quality-gates.sh` and CI's `workspace-qg` run the BYTE-IDENTICAL base-library
#   (`unified-trading-pm/scripts/quality-gates-base/base-library.sh` — diffed, 0 lines).
#   There is NO rule divergence. Every observed "local green → CI red" case was a STALE
#   TREE: QG ran on a tree that differed from the commit that actually got pushed, because
#   a rebase (or a concurrent agent editing the same file) pulled NEW violations in AFTER
#   the QG run. The pushed commit was therefore never QG'd as-is.
#
# THE ONLY ORDERING THAT MAKES LOCAL-GREEN PREDICT CI-GREEN:
#   fetch → rebase onto origin/<branch> → QG on the rebased tree → push (no rebase between
#   QG and push). If the push is rejected because origin moved during QG, re-do the whole
#   cycle so the pushed commit always passed QG on its exact tree.
#
# USAGE:  cd <repo> && bash <ws>/unified-trading-pm/scripts/dev/qg-rebase-push.sh [branch] [-- qg-args...]
#   branch defaults to live-defi-rollout. Extra args after `--` pass through to quality-gates.sh.
#   Requires a CLEAN working tree (commit your work first — never autostash foreign WIP into a rebase).
set -uo pipefail

BRANCH="live-defi-rollout"
QG_ARGS=()
_seen_dashdash=false
for arg in "$@"; do
    if [[ "$_seen_dashdash" == true ]]; then
        QG_ARGS+=("$arg")
    elif [[ "$arg" == "--" ]]; then
        _seen_dashdash=true
    else
        BRANCH="$arg"
    fi
done

if [[ ! -f scripts/quality-gates.sh ]]; then
    echo "❌ Run from a repo root with scripts/quality-gates.sh (cwd: $(pwd))." >&2
    exit 2
fi

# A clean tree is mandatory: an autostash rebase over foreign-dirty WIP is the exact
# footgun the workspace rules forbid (see CLAUDE.md autostash-conflict recovery).
if [[ -n "$(git status --porcelain)" ]]; then
    echo "❌ Working tree not clean — commit your work first. Refusing to rebase over dirty/foreign files." >&2
    git status --short >&2
    exit 2
fi

for attempt in 1 2 3; do
    git fetch -q origin "$BRANCH"
    if ! git rebase "origin/$BRANCH"; then
        git rebase --abort 2>/dev/null || true
        echo "❌ Rebase onto origin/$BRANCH conflicted — resolve manually, then re-run." >&2
        exit 3
    fi

    echo "── quality-gates.sh on the rebased tree ($(git rev-parse --short HEAD), attempt $attempt) ──"
    if ! bash scripts/quality-gates.sh "${QG_ARGS[@]+"${QG_ARGS[@]}"}"; then
        echo "❌ quality-gates.sh FAILED on the rebased tree — fix the violations before pushing." >&2
        exit 1
    fi

    if git push origin "HEAD:$BRANCH" 2>/tmp/_qgrp_push.err; then
        echo "✅ Pushed $(git rev-parse --short HEAD) → $BRANCH — QG-green on the exact pushed tree."
        exit 0
    fi
    if grep -qiE "non-fast-forward|rejected|fetch first" /tmp/_qgrp_push.err; then
        echo "⚠  origin/$BRANCH moved during QG — re-rebasing + re-running QG (concurrent push)..."
        continue
    fi
    echo "❌ Push failed for a non-fast-forward reason:" >&2
    cat /tmp/_qgrp_push.err >&2
    exit 4
done

echo "❌ origin/$BRANCH kept moving across 3 cycles — too much concurrent churn; retry shortly." >&2
exit 5
