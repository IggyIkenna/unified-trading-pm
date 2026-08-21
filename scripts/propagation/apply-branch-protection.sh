#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent tombstone/redirect notice — this script hard-refuses to run
# Delete-when: NA (keep as a permanent redirect pointer to the ruleset model)
#
# apply-branch-protection.sh — Apply canonical branch protection to workspace repos.
#
# Source of truth: unified-trading-pm/ops/branch-protection-template.json
# Policy doc:       unified-trading-pm/ops/coverage-override-policy.md
#
# What it enforces per branch:
#   - required_status_checks: strict, contexts=[quality-gates]
#   - required_pull_request_reviews: 0 approving reviews (autonomous CI: green gate = the review), stale dismissal on
#   - required_conversation_resolution: true
#   - allow_force_pushes / allow_deletions: false
#   - enforce_admins: false  ← admin bypass escape hatch (see policy doc)
#
# Usage:
#   bash scripts/propagation/apply-branch-protection.sh [--dry-run] [--repo NAME] [--branches B1,B2]
#
# Defaults:
#   - All repos listed in workspace-manifest.json with type in {service,api-service,library,infrastructure,devops,test-harness}
#   - Branches: live-defi-rollout, staging, main  (applied in that order)
#
# Pre-flight:
#   - gh CLI installed + authenticated (gh auth login)
#   - Token scope 'repo' (covers branch protection on repos you admin)
#   - Branch must exist remotely; missing branches are reported and skipped
#
# Idempotent: GitHub's PUT endpoint replaces the full protection spec, so
# running this repeatedly produces the same end state.

set -euo pipefail

# ⛔ DEPRECATED (2026-06-07, M2) — DO NOT RUN. This applies CLASSIC branch protection from
# ops/branch-protection-template.json whose context is the stale generic "quality-gates"
# (a DEAD context — the live check is the per-repo "Quality Gates (<repo>) / quality-gates-v2").
# Re-running it would dead-lock non-admin merges fleet-wide. Branch protection is now the RULESET
# model — use scripts/repo-management/pin_branch_protection_rulesets.py (SSOT) +
# terraform/github-branch-protection/main.tf. This script is a tombstone and hard-refuses to run.
echo "⛔ apply-branch-protection.sh is DEPRECATED and disabled (M2, 2026-06-07) — use the ruleset model" >&2
echo "   (scripts/repo-management/pin_branch_protection_rulesets.py)." >&2
exit 1
