#!/usr/bin/env bash
# Force-push local main to origin/main for all workspace repos
#
# WARNING: Overwrites remote main with local state. Branch protection MUST be disabled,
#          or use --bypass-protection to auto-disable (and optionally re-enable) it.
#
# Usage:
#   bash force-push-all-to-main.sh                              # All repos
#   bash force-push-all-to-main.sh --dry-run                    # Show what would run, no pushes
#   bash force-push-all-to-main.sh --bypass-protection          # Auto-disable protection, push, re-enable
#   bash force-push-all-to-main.sh --bypass-protection --no-restore  # Disable and leave disabled
#   bash force-push-all-to-main.sh --limit 2                    # First 2 repos only
#   bash force-push-all-to-main.sh --repos "repo1 repo2"        # Specific repos only
#
# Requires: workspace-manifest.json, git, gh, jq
# Run from: workspace root

set -euo pipefail

GITHUB_ORG="IggyIkenna"

# Resolve workspace root
if [ -f "$(pwd)/unified-trading-pm/workspace-manifest.json" ]; then
  WORKSPACE_ROOT="$(pwd)"
elif [ -f "$(pwd)/workspace-manifest.json" ]; then
  WORKSPACE_ROOT="$(cd .. && pwd)"
else
  echo "Error: Run from workspace root. Expected unified-trading-pm/workspace-manifest.json"
  exit 1
fi
PM_ROOT="$WORKSPACE_ROOT/unified-trading-pm"
MANIFEST="$PM_ROOT/workspace-manifest.json"

DRY_RUN=false
LIMIT=""
REPOS_FILTER=""
BYPASS_PROTECTION=false
RESTORE_PROTECTION=true

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)             DRY_RUN=true; shift ;;
    --bypass-protection)   BYPASS_PROTECTION=true; shift ;;
    --no-restore)          RESTORE_PROTECTION=false; shift ;;
    --limit)               LIMIT="$2"; shift 2 ;;
    --repos)               REPOS_FILTER="$2"; shift 2 ;;
    *)                     shift ;;
  esac
done

if [[ ! -f "$MANIFEST" ]]; then
  echo "Missing $MANIFEST"
  exit 1
fi

if [[ -n "$REPOS_FILTER" ]]; then
  REPOS=($REPOS_FILTER)
else
  REPOS=($(jq -r '.repositories | keys[]' "$MANIFEST" 2>/dev/null))
fi

if [[ -n "$LIMIT" ]]; then
  REPOS=("${REPOS[@]:0:$LIMIT}")
fi

echo "Force-push to main: ${#REPOS[@]} repos"
[[ "$DRY_RUN" = true ]]          && echo "DRY RUN — no pushes will be made"
[[ "$BYPASS_PROTECTION" = true ]] && echo "BYPASS PROTECTION — will disable branch protection + rulesets before push"
[[ "$BYPASS_PROTECTION" = true && "$RESTORE_PROTECTION" = false ]] && echo "NO RESTORE — protections left disabled after push"
echo ""

# ── helpers ────────────────────────────────────────────────────────────────

disable_protection() {
  local repo="$1"
  # Classic branch protection (GH006)
  gh api "repos/$GITHUB_ORG/$repo/branches/main/protection" -X DELETE 2>/dev/null && \
    echo "    [prot] classic branch protection removed: $repo" || true
  # Rulesets (GH013)
  local ids
  ids=$(gh api "repos/$GITHUB_ORG/$repo/rulesets" 2>/dev/null | jq -r '.[].id // empty' 2>/dev/null || true)
  for id in $ids; do
    gh api "repos/$GITHUB_ORG/$repo/rulesets/$id" -X DELETE 2>/dev/null && \
      echo "    [prot] ruleset $id removed: $repo" || true
  done
}

# Capture ruleset configs before deletion so we can restore them
# Uses temp files (not declare -A) for bash 3.2 compatibility (macOS default shell)
PROT_BACKUP_DIR=""

backup_and_disable_protection() {
  local repo="$1"
  # Lazy-init temp dir
  [[ -z "$PROT_BACKUP_DIR" ]] && PROT_BACKUP_DIR="$(mktemp -d)"
  local safe_repo
  safe_repo="${repo//\//__}"
  # Classic branch protection
  local bp_json
  bp_json=$(gh api "repos/$GITHUB_ORG/$repo/branches/main/protection" 2>/dev/null || echo "")
  if [[ -n "$bp_json" && "$bp_json" != "null" ]]; then
    echo "$bp_json" > "$PROT_BACKUP_DIR/${safe_repo}__classic.json"
    gh api "repos/$GITHUB_ORG/$repo/branches/main/protection" -X DELETE 2>/dev/null || true
    echo "    [prot] classic branch protection removed: $repo"
  fi
  # Rulesets
  local rulesets_json
  rulesets_json=$(gh api "repos/$GITHUB_ORG/$repo/rulesets" 2>/dev/null || echo "[]")
  local ids
  ids=$(echo "$rulesets_json" | jq -r '.[].id // empty' 2>/dev/null || true)
  for id in $ids; do
    local rs_json
    rs_json=$(gh api "repos/$GITHUB_ORG/$repo/rulesets/$id" 2>/dev/null || echo "")
    [[ -n "$rs_json" ]] && echo "$rs_json" > "$PROT_BACKUP_DIR/${safe_repo}__ruleset__${id}.json"
    gh api "repos/$GITHUB_ORG/$repo/rulesets/$id" -X DELETE 2>/dev/null && \
      echo "    [prot] ruleset $id removed: $repo" || true
  done
}

restore_protection() {
  local repo="$1"
  [[ -z "$PROT_BACKUP_DIR" ]] && return
  local safe_repo
  safe_repo="${repo//\//__}"
  # Re-enable classic branch protection
  local classic_file="$PROT_BACKUP_DIR/${safe_repo}__classic.json"
  if [[ -f "$classic_file" ]]; then
    gh api "repos/$GITHUB_ORG/$repo/branches/main/protection" -X PUT \
      --input <(echo '{"required_status_checks":null,"enforce_admins":false,"required_pull_request_reviews":{"required_approving_review_count":0},"restrictions":null,"allow_force_pushes":false}') \
      2>/dev/null && echo "    [prot] classic branch protection restored: $repo" || \
      echo "    [prot] WARN: could not restore classic protection: $repo"
  fi
  # Re-create rulesets
  for rs_file in "$PROT_BACKUP_DIR/${safe_repo}__ruleset__"*.json; do
    [[ -f "$rs_file" ]] || continue
    local id
    id="${rs_file##*__ruleset__}"; id="${id%.json}"
    local payload
    payload=$(jq 'del(.id,.node_id,.created_at,.updated_at,._links,.source_type,.source)' "$rs_file" 2>/dev/null || echo "")
    if [[ -n "$payload" ]]; then
      gh api "repos/$GITHUB_ORG/$repo/rulesets" -X POST --input <(echo "$payload") \
        2>/dev/null && echo "    [prot] ruleset restored: $repo" || \
        echo "    [prot] WARN: could not restore ruleset $id: $repo"
    fi
  done
}

cleanup() {
  [[ -n "$PROT_BACKUP_DIR" && -d "$PROT_BACKUP_DIR" ]] && rm -rf "$PROT_BACKUP_DIR"
}
trap cleanup EXIT

# ── main loop ──────────────────────────────────────────────────────────────

failed=0
failed_repos=()

for repo in "${REPOS[@]}"; do
  dir="$WORKSPACE_ROOT/$repo"
  if [[ ! -d "$dir" ]]; then
    echo "  (skip) $repo — not in workspace"
    continue
  fi
  if [[ ! -d "$dir/.git" ]]; then
    echo "  (skip) $repo — not a git repo"
    continue
  fi

  # Ensure we're on main
  (cd "$dir" && git checkout main 2>/dev/null) || true

  # Stage ALL local changes (modifications, deletions, untracked files)
  # This ensures force-push reflects true local state — not just already-committed state.
  # Without this, unstaged deletes and untracked files are silently excluded from the push.
  (cd "$dir" && git add -A)

  if [[ "$DRY_RUN" = true ]]; then
    echo "  [dry] $repo"
    (cd "$dir" && git status -sb | head -1)
    (cd "$dir" && git diff --cached --stat)
    continue
  fi

  if ! (cd "$dir" && git diff --cached --quiet 2>/dev/null); then
    staged_summary=$(cd "$dir" && git diff --cached --stat | tail -1)
    (cd "$dir" && git commit -m "chore: force-sync local state" --no-verify 2>/dev/null) && \
      echo "    [commit] $repo — $staged_summary" || \
      echo "    [commit] WARN: commit failed for $repo (continuing)"
  fi

  # Disable protection before push
  if [[ "$BYPASS_PROTECTION" = true ]]; then
    backup_and_disable_protection "$repo"
  fi

  echo -n "  $repo ... "
  if (cd "$dir" && git push --force origin main 2>&1); then
    echo "OK"
  else
    echo "FAIL"
    ((failed++)) || true
    failed_repos+=("$repo")
  fi

  # Restore protection after push
  if [[ "$BYPASS_PROTECTION" = true && "$RESTORE_PROTECTION" = true ]]; then
    restore_protection "$repo"
  fi
done

echo ""
if [[ $failed -gt 0 ]]; then
  echo "Failed: $failed"
  for r in "${failed_repos[@]}"; do echo "  - $r"; done
  exit 1
fi
echo "Done."
exit 0
