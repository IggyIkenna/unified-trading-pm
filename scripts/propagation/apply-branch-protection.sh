#!/usr/bin/env bash
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

# ----- parse args -----
DRY_RUN=false
SINGLE_REPO=""
BRANCHES_CSV="live-defi-rollout,staging,main"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true; shift ;;
    --repo)    SINGLE_REPO="$2"; shift 2 ;;
    --branches) BRANCHES_CSV="$2"; shift 2 ;;
    -h|--help)
      sed -n '3,30p' "$0"; exit 0 ;;
    *)
      echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

IFS=',' read -r -a BRANCHES <<< "$BRANCHES_CSV"

# ----- resolve paths -----
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WORKSPACE_ROOT="$(cd "$PM_ROOT/.." && pwd)"
MANIFEST="$PM_ROOT/workspace-manifest.json"
TEMPLATE="$PM_ROOT/ops/branch-protection-template.json"

[[ -f "$MANIFEST" ]] || { echo "manifest missing: $MANIFEST" >&2; exit 1; }
[[ -f "$TEMPLATE" ]] || { echo "template missing: $TEMPLATE" >&2; exit 1; }
command -v gh  >/dev/null || { echo "gh CLI not installed" >&2; exit 1; }
command -v jq  >/dev/null || { echo "jq not installed"     >&2; exit 1; }

gh auth status >/dev/null 2>&1 || { echo "gh not authenticated — run: gh auth login" >&2; exit 1; }

# ----- build the cleaned payload (strip _comment_* metadata) -----
PAYLOAD_JSON=$(jq 'with_entries(select(.key | startswith("_comment") | not))' "$TEMPLATE")

# ----- determine target repos -----
if [[ -n "$SINGLE_REPO" ]]; then
  REPOS=("$SINGLE_REPO")
else
  # Types that carry quality-gates.sh per base-service.sh strict check
  TYPES_RE='^(service|api-service|library|infrastructure|devops|test-harness)$'
  REPOS=($(jq -r --arg re "$TYPES_RE" '.repositories | to_entries[] | select(.value.type | test($re)) | .key' "$MANIFEST" | sort))
fi

echo "apply-branch-protection.sh  dry_run=$DRY_RUN  repos=${#REPOS[@]}  branches=${BRANCHES[*]}"
echo "template: $TEMPLATE"
echo

# ----- resolve owner -----
# All repos live under IggyIkenna/<name>. Override via env if that ever changes.
OWNER="${GH_OWNER:-IggyIkenna}"

apply_one () {
  local repo="$1" branch="$2"
  local url="/repos/${OWNER}/${repo}/branches/${branch}/protection"

  # Does the branch exist?
  if ! gh api "/repos/${OWNER}/${repo}/branches/${branch}" >/dev/null 2>&1; then
    printf "  %-22s  %-18s  SKIP (branch absent)\n" "$repo" "$branch"
    return 0
  fi

  if [[ "$DRY_RUN" == true ]]; then
    printf "  %-22s  %-18s  DRY-RUN: PUT %s\n" "$repo" "$branch" "$url"
    return 0
  fi

  # PUT the protection. gh api reads JSON from stdin with --input -.
  if echo "$PAYLOAD_JSON" \
      | gh api --method PUT "$url" \
          -H "Accept: application/vnd.github+json" \
          --input - >/dev/null 2>/tmp/apply-branch-protection.stderr; then
    printf "  %-22s  %-18s  OK\n" "$repo" "$branch"
  else
    printf "  %-22s  %-18s  FAIL  %s\n" "$repo" "$branch" "$(tail -1 /tmp/apply-branch-protection.stderr 2>/dev/null)"
    return 1
  fi
}

ERRORS=0
for repo in "${REPOS[@]}"; do
  for branch in "${BRANCHES[@]}"; do
    if ! apply_one "$repo" "$branch"; then
      ERRORS=$((ERRORS+1))
    fi
  done
done

echo
if (( ERRORS > 0 )); then
  echo "FINISHED with $ERRORS failures"
  exit 1
fi
echo "FINISHED — ${#REPOS[@]} repos × ${#BRANCHES[@]} branches"
