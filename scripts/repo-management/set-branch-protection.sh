#!/usr/bin/env bash
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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"  # scripts/repo-management -> scripts -> unified-trading-pm
MANIFEST="$PM_ROOT/workspace-manifest.json"
GH_ORG="${GH_ORG:-IggyIkenna}"
DRY_RUN=false

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
ok()      { echo -e "${GREEN}✅ $1${NC}"; }
warn()    { echo -e "${YELLOW}⚠️  $1${NC}"; }
fail()    { echo -e "${RED}❌ $1${NC}"; }
section() { echo -e "\n${BLUE}══ $1 ══${NC}"; }

for arg in "$@"; do
  [[ "$arg" == "--dry-run" ]] && DRY_RUN=true
done

[[ "$DRY_RUN" == true ]] && warn "DRY-RUN mode — no changes will be made"

# Resolve target repos from manifest (service + api-service types, excluding PM and codex)
TARGET_REPOS=$(python3 - "$MANIFEST" <<'EOF'
import json, sys
data = json.load(open(sys.argv[1]))
repos = data.get("repositories", {})
ROLLOUT_TIERS = {"service", "api"}
for name, info in repos.items():
    tier = str(info.get("arch_tier", ""))
    if tier in ROLLOUT_TIERS or any(t in tier for t in ROLLOUT_TIERS):
        if name not in ("unified-trading-pm", "unified-trading-codex"):
            print(name)
EOF
)

TOTAL=$(echo "$TARGET_REPOS" | wc -l | tr -d ' ')
section "Setting branch protection on $TOTAL repos"

PASS=0; FAIL=0; SKIP=0

for REPO in $TARGET_REPOS; do
  SLUG="$GH_ORG/$REPO"

  if [[ "$DRY_RUN" == true ]]; then
    echo "  [dry-run] would set protection on $SLUG"
    ((PASS++)) || true
    continue
  fi

  # Set branch protection: require "agent-audit" status check, strict, no admin bypass,
  # allow auto-merge (auto-merge is enabled at repo level separately).
  RESPONSE=$(gh api \
    --method PUT \
    "repos/$SLUG/branches/main/protection" \
    --field "required_status_checks[strict]=true" \
    --field "required_status_checks[contexts][]=agent-audit" \
    --field "enforce_admins=false" \
    --field "required_pull_request_reviews=null" \
    --field "restrictions=null" \
    --field "allow_force_pushes=false" \
    --field "allow_deletions=false" \
    2>&1) && RC=0 || RC=$?

  if [[ $RC -eq 0 ]]; then
    # Also enable auto-merge at repo level
    gh api --method PATCH "repos/$SLUG" \
      --field "allow_auto_merge=true" \
      --field "delete_branch_on_merge=false" \
      >/dev/null 2>&1 || true
    ok "$REPO"
    ((PASS++)) || true
  else
    fail "$REPO — $RESPONSE"
    ((FAIL++)) || true
  fi
done

section "Summary"
echo "  Pass : $PASS"
echo "  Fail : $FAIL"
echo "  Skip : $SKIP"
echo "  Total: $TOTAL"

if [[ $FAIL -gt 0 ]]; then
  warn "$FAIL repos failed — check output above. May need admin token (GH_PAT with admin:repo scope)."
  exit 1
fi

ok "Branch protection rollout complete ($PASS/$TOTAL)"
