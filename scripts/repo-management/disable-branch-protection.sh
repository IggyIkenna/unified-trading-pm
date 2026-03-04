#!/usr/bin/env bash
# Disable branch protection (legacy API) and repo-level rulesets (GitHub Rulesets API) for all workspace repos.
# Requires: gh CLI, jq (for rulesets). Run: gh auth login
#
# Usage:
#   bash scripts/repo-management/disable-branch-protection.sh              # dry-run
#   bash scripts/repo-management/disable-branch-protection.sh --execute   # actually disable
#   GITHUB_OWNER=MyOrg bash scripts/repo-management/disable-branch-protection.sh --execute
#
# Run from unified-trading-pm or workspace root.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WORKSPACE_ROOT="$(cd "$PM_ROOT/.." && pwd)"
OWNER="${GITHUB_OWNER:-IggyIkenna}"

EXECUTE=false
if [[ "${1:-}" == "--execute" ]]; then
  EXECUTE=true
fi

# Repos to skip (no GitHub, or special cases)
SKIP_REPOS=("deployment-api-temp")

get_repos() {
  find "$WORKSPACE_ROOT" -maxdepth 2 -name ".git" -type d 2>/dev/null \
    | sed 's|/.git||' \
    | sort -u
}

# Parse owner/repo from remote URL (git@github.com:owner/repo.git or https://github.com/owner/repo.git)
get_owner_repo() {
  local repo_dir="$1"
  local url
  url="$(cd "$repo_dir" && git remote get-url origin 2>/dev/null || true)"
  if [[ -z "$url" ]] || [[ "$url" != *"github.com"* ]]; then
    echo ""
    return
  fi
  echo "$url" | sed 's|.*github.com[:/]||' | sed 's|\.git$||'
}

disable_protection() {
  local full_repo="$1"
  local branch="$2"
  local out
  if $EXECUTE; then
    out="$(gh api -X DELETE "repos/${full_repo}/branches/${branch}/protection" 2>&1)" || true
    if [[ "$out" == *"Branch not protected"* ]] || [[ "$out" == *"404"* ]]; then
      echo "  $branch: (no protection)"
    elif [[ -z "$out" ]]; then
      echo "  $branch: disabled"
    else
      echo "  $branch: $out"
    fi
  else
    echo "  Would DELETE protection on $branch"
  fi
}

# Delete repo-level rulesets (GitHub Rulesets API). Org/Enterprise rulesets are skipped.
disable_rulesets() {
  local full_repo="$1"
  local rulesets
  rulesets="$(gh api "repos/${full_repo}/rulesets" 2>/dev/null)" || true
  if [[ -z "$rulesets" ]] || [[ "$rulesets" == "[]" ]]; then
    echo "  rulesets: (none)"
    return
  fi
  local ids
  ids="$(echo "$rulesets" | jq -r '.[] | select(.source_type=="Repository") | .id' 2>/dev/null)" || true
  if [[ -z "$ids" ]]; then
    echo "  rulesets: (none repo-level, or jq missing)"
    return
  fi
  for id in $ids; do
    if $EXECUTE; then
      local out
      out="$(gh api -X DELETE "repos/${full_repo}/rulesets/${id}" 2>&1)" || true
      if [[ -z "$out" ]]; then
        echo "  ruleset $id: deleted"
      else
        echo "  ruleset $id: $out"
      fi
    else
      echo "  Would DELETE ruleset $id"
    fi
  done
}

main() {
  echo "Disable branch protection for workspace repos"
  echo "Owner: $OWNER"
  echo "Execute: $EXECUTE"
  echo ""

  if ! command -v gh &>/dev/null; then
    echo "ERROR: gh CLI not found. Install: brew install gh && gh auth login" >&2
    exit 1
  fi

  if ! gh auth status &>/dev/null; then
    echo "ERROR: gh not authenticated. Run: gh auth login" >&2
    exit 1
  fi

  for repo_dir in $(get_repos); do
    local name
    name="$(basename "$repo_dir")"
    if printf '%s\n' "${SKIP_REPOS[@]}" | grep -qx "$name"; then
      continue
    fi
    local full_repo
    full_repo="$(get_owner_repo "$repo_dir")"
    if [[ -z "$full_repo" ]]; then
      echo "[$name] (no origin or not GitHub)"
      continue
    fi
    if [[ "$full_repo" != "$OWNER/"* ]]; then
      echo "[$name] (skip: $full_repo not under $OWNER)"
      continue
    fi
    echo "[$name] ($full_repo)"
    disable_protection "$full_repo" "staging"
    disable_protection "$full_repo" "main"
    if [[ "$(cd "$repo_dir" && git rev-parse --abbrev-ref HEAD 2>/dev/null)" == "master" ]]; then
      disable_protection "$full_repo" "master"
    fi
    disable_rulesets "$full_repo"
  done

  if ! $EXECUTE; then
    echo ""
    echo "Dry-run complete. Run with --execute to disable protection."
  fi
}

main "$@"
