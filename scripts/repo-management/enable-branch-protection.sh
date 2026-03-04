#!/usr/bin/env bash
# Enable branch protection (legacy API) for feat→staging→main flow.
#
# Policy:
#   - staging: require PR (from feat/*), require quality-gates; auto-merge when CI passes
#   - main: require PR (from staging), require quality-gates + integration-tests; auto-merge when CI passes
#   - No direct push to staging or main
#
# Aligns with: feature-branch-workflow.md, always-use-quickmerge.mdc, integration-testing-layers.md
#
# Usage:
#   bash scripts/repo-management/enable-branch-protection.sh              # dry-run (both branches)
#   bash scripts/repo-management/enable-branch-protection.sh --execute    # actually enable
#   bash scripts/repo-management/enable-branch-protection.sh --execute --main-only    # main only
#   bash scripts/repo-management/enable-branch-protection.sh --execute --staging-only # staging only
#   GITHUB_OWNER=MyOrg bash scripts/repo-management/enable-branch-protection.sh --execute
#
# Env vars:
#   MAIN_STATUS_CHECKS  Comma-separated (default: quality-gates,integration-tests)
#   STAGING_STATUS_CHECKS  (default: quality-gates)
#
# Run from unified-trading-pm or workspace root.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WORKSPACE_ROOT="$(cd "$PM_ROOT/.." && pwd)"
OWNER="${GITHUB_OWNER:-IggyIkenna}"
STAGING_CHECKS="${STAGING_STATUS_CHECKS:-quality-gates}"
MAIN_CHECKS="${MAIN_STATUS_CHECKS:-quality-gates,integration-tests}"

EXECUTE=false
MAIN_ONLY=false
STAGING_ONLY=false
for arg in "$@"; do
  case "$arg" in
    --execute) EXECUTE=true ;;
    --main-only) MAIN_ONLY=true ;;
    --staging-only) STAGING_ONLY=true ;;
  esac
done
[[ "$MAIN_ONLY" = true && "$STAGING_ONLY" = true ]] && { echo "Cannot use both --main-only and --staging-only"; exit 1; }
[[ "$MAIN_ONLY" = false && "$STAGING_ONLY" = false ]] && PROTECT_BOTH=true || PROTECT_BOTH=false

SKIP_REPOS=("deployment-api-temp")

get_repos() {
  find "$WORKSPACE_ROOT" -maxdepth 2 -name ".git" -type d 2>/dev/null \
    | sed 's|/.git||' \
    | sort -u
}

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

# Build protection JSON for a branch with given status check contexts (comma-separated)
protection_json() {
  local checks="$1"
  local -a contexts
  IFS=',' read -ra contexts <<< "$checks"
  jq -n \
    --argjson ctx "$(printf '%s\n' "${contexts[@]}" | jq -R . | jq -s .)" \
    '{required_status_checks: {strict: true, contexts: $ctx}, enforce_admins: true, required_pull_request_reviews: {required_approving_review_count: 0, dismiss_stale_reviews: true}, restrictions: null, allow_force_pushes: false, allow_deletions: false}'
}

enable_protection() {
  local full_repo="$1"
  local branch="$2"
  local checks="$3"
  local json
  json="$(jq -n --arg checks "$checks" '
    ($checks | split(",")) as $ctx |
    {required_status_checks: {strict: true, contexts: $ctx}, enforce_admins: true, required_pull_request_reviews: {required_approving_review_count: 0, dismiss_stale_reviews: true}, restrictions: null, allow_force_pushes: false, allow_deletions: false}
  ')"
  if $EXECUTE; then
    local out
    out="$(echo "$json" | gh api -X PUT "repos/${full_repo}/branches/${branch}/protection" --input - 2>&1)" || true
    if [[ -z "$out" ]]; then
      echo "  $branch: enabled"
    else
      echo "  $branch: $out"
    fi
  else
    echo "  Would PUT protection on $branch (contexts: $checks)"
  fi
}

main() {
  echo "Enable branch protection (feat→staging→main flow)"
  echo "Owner: $OWNER"
  echo "Execute: $EXECUTE"
  echo "Staging checks: $STAGING_CHECKS | Main checks: $MAIN_CHECKS"
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
    if [[ "$PROTECT_BOTH" = true || "$STAGING_ONLY" = true ]]; then
      enable_protection "$full_repo" "staging" "$STAGING_CHECKS"
    fi
    if [[ "$PROTECT_BOTH" = true || "$MAIN_ONLY" = true ]]; then
      enable_protection "$full_repo" "main" "$MAIN_CHECKS"
    fi
  done

  if ! $EXECUTE; then
    echo ""
    echo "Dry-run complete. Run with --execute to enable."
  fi
}

main "$@"
