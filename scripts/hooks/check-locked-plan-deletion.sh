#!/usr/bin/env bash
# Epic: plan_hygiene_master
# Lifecycle: permanent
# Delete-when: NA
#
# Locked-plan-deletion gate — commit-msg stage.
#
# `locked_by:` is the workspace's one explicit "a human is holding this" signal on a
# plan (CLAUDE.md: "blocks archival without [unlock-plan] (ASK, never autonomous)").
# The equivalent check inside quality-gates.sh (STEP "Locked plan deletion check")
# NEVER RUNS for the commit class that actually archives plans: CLAUDE.md's own
# QG-batching rule routes a pure `docs(plans):` commit through prek only, and
# quality-gates.sh's block also read `git log -1` (the PREVIOUS commit) instead of
# the message being written. Both bugs let unified-trading-pm@57ed9271c archive a
# locked doc with no [unlock-plan] and no block.
#
# This hook fixes both by living at prek's `commit-msg` stage — like
# `conventional-pre-commit` (see .pre-commit-config.yaml), NOT `pre-commit` — because
# `.git/COMMIT_EDITMSG` is not reliably the message-to-be until then. It receives the
# commit-message file PATH as $1 (prek's commit-msg-stage contract), never `git log`.
#
# Install: add to .pre-commit-config.yaml as a local hook with `stages: [commit-msg]`.
#
# Pathspec note (verified 2026-07-27 against a real historical case,
# unified-trading-pm@57ed9271c which archived a locked plans/active/issues/ doc):
# `plans/active/*.md` DOES match files inside issues/ on this git version (2.43.0) —
# git's default pathspec `*` crosses `/`, unlike a shell glob. Confirmed:
# `git diff --diff-filter=D --name-only 57ed9271c~1 57ed9271c -- 'plans/active/*.md'`
# lists `plans/active/issues/mtds_uac_adapter_contract_baseline_regression_2026_07_09.md`
# identically to the unfiltered deletion list. A `plans/active/**/*.md` variant was
# considered (an earlier draft of this fix's task doc suggested it) but MEASURED to be
# WRONG — it returns fewer matches (433 vs 696) because it requires at least one
# subdirectory, silently EXCLUDING files directly in plans/active/ (e.g. epics-adjacent
# top-level issue docs). Kept the proven-correct single-star pattern; do not "fix" it
# back to `**` without re-measuring.

set -euo pipefail

COMMIT_MSG_FILE="${1:?usage: check-locked-plan-deletion.sh <commit-msg-file>}"

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || exit 0)"
[[ -z "$REPO_ROOT" ]] && exit 0
cd "$REPO_ROOT"

# Only unified-trading-pm carries a plans/ tree — a no-op elsewhere is correct, not a
# skip-the-check bug.
[[ -d "plans/active" ]] || exit 0

DELETED_PLANS=$(git diff --cached --diff-filter=D --name-only -- 'plans/active/*.md' 2>/dev/null || :)
[[ -z "$DELETED_PLANS" ]] && exit 0

COMMIT_MSG=$(cat "$COMMIT_MSG_FILE" 2>/dev/null || :)

FAILED=0
while IFS= read -r plan_file; do
    [[ -z "$plan_file" ]] && continue
    LOCKED_BY=$(git show "HEAD:$plan_file" 2>/dev/null | grep -oP '^\s*locked_by:\s*\K.*' | head -1 || :)
    # Normalize: a literal "" or '' value means semantically unlocked (the
    # grep extracts the quote characters themselves as a non-empty string,
    # which would false-trip the [[ -n ]] check below).  Strip
    # leading/trailing whitespace, then strip one layer of matching double
    # or single quotes — a bare quoted value like "plan_reconciler" still
    # resolves to a non-empty lock-holder; an empty quoted value ("") does
    # not.  Unbalanced quotes are treated conservatively (stays locked).
    LOCKED_BY=$(echo "$LOCKED_BY" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e 's/^"//; s/"$//' -e "s/^'//; s/'$//")
    if [[ -n "$LOCKED_BY" ]] && ! grep -q '\[unlock-plan\]' <<<"$COMMIT_MSG"; then
        echo "❌ BLOCKED: $plan_file is locked by '$LOCKED_BY'."
        echo "   To delete a locked plan, include [unlock-plan] in your commit message."
        echo "   This prevents agents from accidentally removing plans that are actively being implemented."
        FAILED=1
    fi
done <<<"$DELETED_PLANS"

exit "$FAILED"
