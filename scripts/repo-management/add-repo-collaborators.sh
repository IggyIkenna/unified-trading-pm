#!/usr/bin/env bash
# Add datadodo and CosmicTrader as collaborators (read or write) to the 11 repos.
# Requires: gh CLI installed and authenticated (gh auth login).
# Usage:
#   bash scripts/repo-management/add-repo-collaborators.sh              # write (push) for both
#   bash scripts/repo-management/add-repo-collaborators.sh --read        # read (pull) for both
#   GITHUB_OWNER=MyOrg bash scripts/repo-management/add-repo-collaborators.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MANIFEST="$PM_ROOT/workspace-manifest.json"

REPOS=(
  alerting-service
  deployment-api
  deployment-service
  execution-analytics-ui
  features-multi-timeframe-service
  ml-training-ui
  system-integration-tests
  unified-api-contracts
  unified-cloud-interface
  unified-trading-ui-auth
)

COLLABORATORS=(datadodo CosmicTrader)

# push = write (read+write), pull = read-only
PERMISSION="push"
DRY_RUN=""
OWNER="${GITHUB_OWNER:-IggyIkenna}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --read)
      PERMISSION="pull"
      shift
      ;;
    --write)
      PERMISSION="push"
      shift
      ;;
    --dry-run)
      DRY_RUN="1"
      shift
      ;;
    *)
      echo "Usage: $0 [--read|--write] [--dry-run]" >&2
      echo "  --read     grant read-only (pull)" >&2
      echo "  --write    grant read+write (push); default" >&2
      echo "  --dry-run  print commands only" >&2
      echo "  GITHUB_OWNER=owner $0  override repo owner" >&2
      exit 1
      ;;
  esac
done

if ! command -v gh &>/dev/null; then
  echo "Error: gh CLI not found. Install: https://cli.github.com/" >&2
  exit 1
fi

if [[ -z "$DRY_RUN" ]] && ! gh auth status &>/dev/null; then
  echo "Error: gh not authenticated. Run: gh auth login" >&2
  exit 1
fi

echo "Owner: $OWNER | Permission: $PERMISSION (write=push, read=pull)"
echo "Collaborators: ${COLLABORATORS[*]}"
echo "Repos: ${REPOS[*]}"
if [[ -n "$DRY_RUN" ]]; then
  echo "[DRY RUN] No API calls will be made."
fi
echo ""

FAILED=0
for repo in "${REPOS[@]}"; do
  for user in "${COLLABORATORS[@]}"; do
    if [[ -n "$DRY_RUN" ]]; then
      echo "Would add: $user to $OWNER/$repo with $PERMISSION"
      continue
    fi
    # PUT returns 204 (already collaborator) or 201 (invitation sent)
    err=""
    if ! err=$(gh api -X PUT "repos/$OWNER/$repo/collaborators/$user" -f permission="$PERMISSION" --silent 2>&1); then
      # Surface API error: 404 = repo missing or no admin, 422 = invalid user, etc.
      echo "FAIL: $OWNER/$repo -> $user | $err" >&2
      FAILED=1
    else
      echo "OK: $OWNER/$repo -> $user ($PERMISSION)"
    fi
  done
done

if [[ $FAILED -eq 1 ]]; then
  echo "" >&2
  echo "Some adds failed. Common causes:" >&2
  echo "  404 = repo does not exist under $OWNER (create it or set GITHUB_OWNER)" >&2
  echo "  403 = no admin rights on the repo" >&2
  echo "  422 = user not found or invalid" >&2
  exit 1
fi

echo ""
echo "Done. Users will receive an invite email if they did not already have access."
