#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Verify GH_PAT repository secret exists in all workspace repos
#
# Reads workspace-manifest.json; for each repo with github_url, runs:
#   gh secret list --repo ORG/REPO
# and checks if GH_PAT is present.
#
# Usage:
#   bash unified-trading-pm/scripts/repo-management/verify-gh-pat-secrets.sh
#   bash unified-trading-pm/scripts/repo-management/verify-gh-pat-secrets.sh --org IggyIkenna
#
# Requires: gh CLI authenticated (gh auth login)
# Exit: 0 if all have GH_PAT, 1 otherwise

set -euo pipefail

# Resolve workspace root from cwd (must run from workspace root)
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

while [[ $# -gt 0 ]]; do
  case "$1" in
    --org)
      ORG="$2"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

if [[ ! -f "$MANIFEST" ]]; then
  echo "Missing $MANIFEST"
  exit 1
fi

if ! command -v gh &>/dev/null; then
  echo "gh CLI required. Run: brew install gh && gh auth login"
  exit 1
fi

echo "Verifying GH_PAT in workspace repos (org=$ORG)..."
echo ""

missing=0
has=0
for repo in $(jq -r '.repositories | keys[]' "$MANIFEST" 2>/dev/null); do
  url=$(jq -r --arg r "$repo" '.repositories[$r].github_url // ""' "$MANIFEST")
  [[ -z "$url" || "$url" == "null" ]] && continue

  if gh secret list --repo "$ORG/$repo" 2>/dev/null | grep -q "GH_PAT"; then
    echo "  ✅ $repo"
    ((has++)) || true
  else
    echo "  ❌ $repo"
    ((missing++)) || true
  fi
done

echo ""
echo "Summary: $has with GH_PAT, $missing missing"
[[ $missing -gt 0 ]] && exit 1
exit 0
