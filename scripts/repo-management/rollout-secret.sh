#!/usr/bin/env bash
# rollout-secret.sh — Set a GitHub Actions secret across all workspace repos
#
# Reads workspace-manifest.json; for each repo with a github_url, sets
# the given secret name to the given value (or reads from env if VALUE not passed).
#
# Usage:
#   bash unified-trading-pm/scripts/repo-management/rollout-secret.sh SECRET_NAME SECRET_VALUE
#   bash unified-trading-pm/scripts/repo-management/rollout-secret.sh SECRET_NAME  # reads from env var of same name
#   bash unified-trading-pm/scripts/repo-management/rollout-secret.sh --check SECRET_NAME  # verify only
#
# Examples:
#   bash unified-trading-pm/scripts/repo-management/rollout-secret.sh ANTHROPIC_API_KEY sk-ant-xxx
#   ANTHROPIC_API_KEY=sk-ant-xxx bash unified-trading-pm/scripts/repo-management/rollout-secret.sh ANTHROPIC_API_KEY
#   bash unified-trading-pm/scripts/repo-management/rollout-secret.sh --check ANTHROPIC_API_KEY
#
# Requires: gh CLI authenticated (gh auth login)
# Run from: workspace root (parent of unified-trading-pm)

set -euo pipefail

CHECK_ONLY=false
if [[ "${1:-}" == "--check" ]]; then
  CHECK_ONLY=true
  shift
fi

SECRET_NAME="${1:-}"
SECRET_VALUE="${2:-${!SECRET_NAME:-}}"  # arg 2, or env var of same name

if [[ -z "$SECRET_NAME" ]]; then
  echo "Usage: bash rollout-secret.sh [--check] SECRET_NAME [SECRET_VALUE]"
  exit 1
fi

if [[ "$CHECK_ONLY" == "false" && -z "$SECRET_VALUE" ]]; then
  echo "Error: SECRET_VALUE not provided and \$$SECRET_NAME not set in environment."
  echo "  Pass value as arg 2, or: export $SECRET_NAME=... before running."
  exit 1
fi

# Resolve workspace root
if [ -f "$(pwd)/unified-trading-pm/workspace-manifest.json" ]; then
  WORKSPACE_ROOT="$(pwd)"
elif [ -f "$(pwd)/workspace-manifest.json" ]; then
  WORKSPACE_ROOT="$(cd .. && pwd)"
else
  echo "Error: Run from workspace root. Expected unified-trading-pm/workspace-manifest.json"
  exit 1
fi
MANIFEST="$WORKSPACE_ROOT/unified-trading-pm/workspace-manifest.json"
ORG="${GH_ORG:-IggyIkenna}"

if ! command -v gh &>/dev/null; then
  echo "gh CLI required. Run: brew install gh && gh auth login"
  exit 1
fi

if [[ "$CHECK_ONLY" == "true" ]]; then
  echo "━━━ Checking $SECRET_NAME across workspace repos (org=$ORG) ━━━"
else
  echo "━━━ Rolling out $SECRET_NAME to workspace repos (org=$ORG) ━━━"
fi
echo ""

OK=0
FAIL=0
SKIP=0
FAILED=()

for repo in $(jq -r '.repositories | keys[]' "$MANIFEST" 2>/dev/null | sort); do
  url=$(jq -r --arg r "$repo" '.repositories[$r].github_url // ""' "$MANIFEST")
  if [[ -z "$url" || "$url" == "null" ]]; then
    SKIP=$((SKIP + 1))
    continue
  fi

  if [[ "$CHECK_ONLY" == "true" ]]; then
    if gh secret list --repo "$ORG/$repo" 2>/dev/null | grep -q "^$SECRET_NAME"; then
      echo "  ✅ $repo"
      OK=$((OK + 1))
    else
      echo "  ❌ $repo — missing"
      FAIL=$((FAIL + 1))
      FAILED+=("$repo")
    fi
  else
    if echo "$SECRET_VALUE" | gh secret set "$SECRET_NAME" --repo "$ORG/$repo" 2>/dev/null; then
      echo "  ✅ $repo"
      OK=$((OK + 1))
    else
      echo "  ❌ $repo — failed to set"
      FAIL=$((FAIL + 1))
      FAILED+=("$repo")
    fi
  fi
done

echo ""
echo "  OK: $OK | Failed: $FAIL | Skipped (no github_url): $SKIP"

if [[ ${#FAILED[@]} -gt 0 ]]; then
  echo ""
  echo "  Failed repos:"
  for r in "${FAILED[@]}"; do echo "    - $r"; done
fi

[[ $FAIL -eq 0 ]]
