#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent tombstone/redirect notice — this script hard-refuses to run
# Delete-when: NA (keep as a permanent redirect pointer to the ruleset model)
# set-branch-protection.sh
#
# ⛔ DEPRECATED (2026-06-07, M2) — DO NOT RUN.
# This script set CLASSIC branch protection requiring the ancient "agent-audit" status
# check (a context NO run has emitted for many months). Re-running it would REPLACE each
# repo's live ruleset-derived required check with a DEAD context → dead-lock all non-admin
# merges fleet-wide. Branch protection is now the RULESET model: required check
# "Quality Gates (<repo>) / quality-gates-v2" on main + "check-staging-lock" on staging,
# managed by scripts/repo-management/pin_branch_protection_rulesets.py (SSOT) and
# terraform/github-branch-protection/main.tf. Use those; this script is kept only as a
# tombstone and hard-refuses to run.
#
# Requires: gh CLI authenticated with repo admin scope (GH_PAT or gh auth login)

set -euo pipefail

echo "⛔ set-branch-protection.sh is DEPRECATED and disabled (M2, 2026-06-07)." >&2
echo "   Classic branch protection with the 'agent-audit' context is retired. Use the ruleset model:" >&2
echo "   scripts/repo-management/pin_branch_protection_rulesets.py + terraform/github-branch-protection/." >&2
echo "   Required check is 'Quality Gates (<repo>) / quality-gates-v2' (main) + 'check-staging-lock' (staging)." >&2
exit 1
