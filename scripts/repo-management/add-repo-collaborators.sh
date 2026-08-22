#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Add datadodo and CosmicTrader as collaborators (read or write) to ALL repos in workspace-manifest.json.
# Repo list is derived entirely from the manifest — no hardcoded list.
# Requires: gh CLI + jq installed and authenticated (gh auth login).
# Usage:
#   bash scripts/repo-management/add-repo-collaborators.sh              # write (push) for both
#   bash scripts/repo-management/add-repo-collaborators.sh --read        # read (pull) for both
#   bash scripts/repo-management/add-repo-collaborators.sh --dry-run     # preview only
#   GITHUB_OWNER=MyOrg bash scripts/repo-management/add-repo-collaborators.sh

set -euo pipefail

# ---------------------------------------------------------------------------
# Resolve workspace root (must run from workspace root or PM subdir)
# ---------------------------------------------------------------------------
if [ -f "$(pwd)/unified-trading-pm/workspace-manifest.json" ]; then
  WORKSPACE_ROOT="$(pwd)"
elif [ -f "$(pwd)/../unified-trading-pm/workspace-manifest.json" ]; then
  WORKSPACE_ROOT="$(cd .. && pwd)"
else
  echo "Error: Run from workspace root. Expected unified-trading-pm/workspace-manifest.json" >&2
  exit 1
fi
MANIFEST="$WORKSPACE_ROOT/unified-trading-pm/workspace-manifest.json"

# ---------------------------------------------------------------------------
# Derive repo list from manifest (no hardcoded list)
# ---------------------------------------------------------------------------
if ! command -v jq &>/dev/null; then
  echo "Error: jq not found. Install: https://stedolan.github.io/jq/" >&2
  exit 1
fi

REPOS=()
while IFS= read -r repo; do
  REPOS+=("$repo")
done < <(jq -r '.repositories | keys[]' "$MANIFEST" | sort)

if [[ ${#REPOS[@]} -eq 0 ]]; then
  echo "Error: No repositories found in manifest: $MANIFEST" >&2
  exit 1
fi

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
      echo "  --dry-run  print commands only, no API calls" >&2
      echo "  GITHUB_OWNER=owner $0  override repo owner (default: IggyIkenna)" >&2
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

echo "Owner:        $OWNER"
echo "Permission:   $PERMISSION (push=read+write, pull=read-only)"
echo "Collaborators: ${COLLABORATORS[*]}"
echo "Repos (${#REPOS[@]} from manifest): ${REPOS[*]}"
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
  echo "  404 = repo does not exist under $OWNER (create it first or set GITHUB_OWNER)" >&2
  echo "  403 = no admin rights on the repo" >&2
  echo "  422 = user not found or invalid" >&2
  exit 1
fi

echo ""
echo "Done. ${#REPOS[@]} repos processed. Users will receive an invite email if they did not already have access."
