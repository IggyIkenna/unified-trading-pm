#!/usr/bin/env bash
# ADMIN ONLY: Force-sync all workspace repos — local main overwrites remote main.
#
# What this does per repo:
#   1. git checkout main
#   2. git add -A (stage all local changes)
#   3. git commit -m "<message>" (if anything staged)
#   4. Disable GitHub branch protection via API (admin-only)
#   5. git push --force origin main (local wins, no conflict resolution)
#   6. Re-enable branch protection
#
# Branch protection is restored even on failure (trap-based cleanup).
#
# Usage:
#   bash admin-force-sync-all-to-main.sh --admin-confirm [OPTIONS]
#
# Options:
#   --admin-confirm       REQUIRED. Acknowledge this overwrites remote main.
#   --message MSG         Commit message for staged changes (default: "chore: admin force-sync")
#   --dry-run             Show what would run; make no changes.
#   --limit N             Process only the first N repos.
#   --repo NAME           Process only one specific repo.
#   --filter PATTERN      Glob filter on repo name (e.g. unified-*, *-service).
#   --skip-protection     Skip the GitHub API protect/unprotect cycle
#                         (use if protection is already disabled or not set).
#   --no-commit           Skip git add / git commit; only force-push current HEAD.
#   --repos "a b c"       Space-separated list of repo names to process.
#
# Prerequisites:
#   - gh CLI authenticated as an admin of all target repos.
#   - jq installed.
#
# Run from: workspace root OR unified-trading-pm/scripts/repo-management/

set -euo pipefail

# ---------------------------------------------------------------------------
# Resolve workspace root
# ---------------------------------------------------------------------------
if [ -f "$(pwd)/unified-trading-pm/workspace-manifest.json" ]; then
  WORKSPACE_ROOT="$(pwd)"
elif [ -f "$(pwd)/workspace-manifest.json" ]; then
  WORKSPACE_ROOT="$(cd .. && pwd)"
else
  echo "ERROR: Run from workspace root. Expected unified-trading-pm/workspace-manifest.json"
  echo "  cd /path/to/unified-trading-system-repos"
  echo "  bash unified-trading-pm/scripts/repo-management/admin-force-sync-all-to-main.sh --admin-confirm"
  exit 1
fi

PM_ROOT="$WORKSPACE_ROOT/unified-trading-pm"
MANIFEST="$PM_ROOT/workspace-manifest.json"

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
ADMIN_CONFIRM=false
DRY_RUN=false
LIMIT=""
REPO_FILTER=""
FILTER_PATTERN=""
REPOS_LIST=""
COMMIT_MSG="chore: admin force-sync"
SKIP_PROTECTION=false
NO_COMMIT=false

# ---------------------------------------------------------------------------
# Parse args
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --admin-confirm)   ADMIN_CONFIRM=true; shift ;;
    --dry-run)         DRY_RUN=true; shift ;;
    --limit)           LIMIT="$2"; shift 2 ;;
    --repo)            REPO_FILTER="$2"; shift 2 ;;
    --filter)          FILTER_PATTERN="$2"; shift 2 ;;
    --repos)           REPOS_LIST="$2"; shift 2 ;;
    --message)         COMMIT_MSG="$2"; shift 2 ;;
    --skip-protection) SKIP_PROTECTION=true; shift ;;
    --no-commit)       NO_COMMIT=true; shift ;;
    *) echo "Unknown flag: $1"; shift ;;
  esac
done

# ---------------------------------------------------------------------------
# Safety gate — must pass --admin-confirm
# ---------------------------------------------------------------------------
if [[ "$ADMIN_CONFIRM" != "true" ]]; then
  cat <<'EOF'
ADMIN FORCE-SYNC: Overwrites remote main with your local state for every repo.
This CANNOT be undone without a reflog recovery on the server side.

  You MUST pass --admin-confirm to proceed.

  bash admin-force-sync-all-to-main.sh --admin-confirm [--dry-run] [--limit N] ...

EOF
  exit 1
fi

# ---------------------------------------------------------------------------
# Prerequisite checks
# ---------------------------------------------------------------------------
if ! command -v jq &>/dev/null; then
  echo "ERROR: jq not found. Install jq to parse workspace-manifest.json."
  exit 1
fi

if [[ ! -f "$MANIFEST" ]]; then
  echo "ERROR: Missing $MANIFEST"
  exit 1
fi

if [[ "$SKIP_PROTECTION" == "false" ]] && ! command -v gh &>/dev/null; then
  echo "ERROR: gh CLI not found. Install gh or pass --skip-protection."
  exit 1
fi

# Detect GitHub owner from manifest
GH_OWNER=$(jq -r '.github_owner // .owner // empty' "$MANIFEST" 2>/dev/null || true)
if [[ -z "$GH_OWNER" ]]; then
  # Fall back: derive from first repo remote
  FIRST_REPO=$(jq -r '.repositories | keys[0]' "$MANIFEST" 2>/dev/null || true)
  if [[ -n "$FIRST_REPO" && -d "$WORKSPACE_ROOT/$FIRST_REPO/.git" ]]; then
    REMOTE_URL=$(cd "$WORKSPACE_ROOT/$FIRST_REPO" && git remote get-url origin 2>/dev/null || true)
    GH_OWNER=$(echo "$REMOTE_URL" | sed -E 's|.*[:/]([^/]+)/[^/]+\.git.*|\1|')
  fi
fi
if [[ -z "$GH_OWNER" ]] && [[ "$SKIP_PROTECTION" == "false" ]]; then
  echo "ERROR: Could not determine GitHub owner from manifest. Pass --skip-protection or add 'github_owner' to workspace-manifest.json."
  exit 1
fi

# ---------------------------------------------------------------------------
# Build repo list in dependency order
# ---------------------------------------------------------------------------
if [[ -n "$REPOS_LIST" ]]; then
  REPOS=($REPOS_LIST)
elif [[ -n "$REPO_FILTER" ]]; then
  REPOS=("$REPO_FILTER")
else
  ORDERED=($(jq -r '.topologicalOrder.levels[].repos[]' "$MANIFEST" 2>/dev/null || true))
  REPO_KEYS=($(jq -r '.repositories | keys[]' "$MANIFEST" 2>/dev/null))
  # Append any keys not already in topological order
  for r in "${REPO_KEYS[@]}"; do
    found=false
    for o in "${ORDERED[@]:-}"; do [[ "$o" == "$r" ]] && found=true && break; done
    [[ "$found" == "false" ]] && ORDERED+=("$r")
  done
  REPOS=("${ORDERED[@]}")
fi

# Apply glob filter
if [[ -n "$FILTER_PATTERN" ]]; then
  FILTERED=()
  for r in "${REPOS[@]}"; do
    [[ "$r" == $FILTER_PATTERN ]] && FILTERED+=("$r")
  done
  REPOS=("${FILTERED[@]}")
fi

[[ -n "$LIMIT" ]] && REPOS=("${REPOS[@]:0:$LIMIT}")

# ---------------------------------------------------------------------------
# Branch protection helpers
# ---------------------------------------------------------------------------

# Temp dir: per-repo files store protection state (bash 3.2 compatible, no assoc arrays).
#   ${key}.repo                  — original repo name (for cleanup reverse-mapping)
#   ${key}.classic.json          — classic branch protection JSON (if it existed)
#   ${key}.rulesets              — newline-separated ruleset IDs that were active (now disabled)
#   ${key}.ruleset_<id>.json     — full GET JSON for each disabled ruleset (for exact restore)
PROT_TMPDIR=$(mktemp -d "/tmp/admin_sync_prot_XXXXXX")

_repo_key() { printf '%s' "$1" | tr '/' '_' | tr '-' '_'; }

_disable_protection() {
  local repo="$1"
  local key; key=$(_repo_key "$repo")

  # Record repo name for cleanup reverse-mapping
  printf '%s' "$repo" > "$PROT_TMPDIR/${key}.repo"

  if [[ "$SKIP_PROTECTION" == "true" ]]; then
    return 0
  fi

  # 1. Classic branch protection (DELETE — 404 is fine, means none was set)
  local prot_json
  prot_json=$(gh api "repos/$GH_OWNER/$repo/branches/main/protection" 2>/dev/null || echo "NONE")
  if [[ "$prot_json" != "NONE" ]]; then
    printf '%s\n' "$prot_json" > "$PROT_TMPDIR/${key}.classic.json"
    gh api -X DELETE "repos/$GH_OWNER/$repo/branches/main/protection" &>/dev/null || true
  fi

  # 2. GitHub Rulesets — disable every active ruleset
  #    (GH013 "Repository rule violations" errors come from rulesets, not classic protection)
  local rulesets_json
  rulesets_json=$(gh api "repos/$GH_OWNER/$repo/rulesets" 2>/dev/null || echo "[]")
  printf '%s\n' "$rulesets_json" \
    | jq -r '.[] | select(.enforcement == "active") | .id' 2>/dev/null \
    | while IFS= read -r rid; do
        [[ -z "$rid" ]] && continue
        # Fetch and save full ruleset JSON BEFORE disabling (for exact restore)
        gh api "repos/$GH_OWNER/$repo/rulesets/$rid" 2>/dev/null \
          > "$PROT_TMPDIR/${key}.ruleset_${rid}.json" || true
        # Disable enforcement
        gh api -X PUT "repos/$GH_OWNER/$repo/rulesets/$rid" \
          --field enforcement=disabled &>/dev/null || true
        printf '%s\n' "$rid" >> "$PROT_TMPDIR/${key}.rulesets"
      done
}

_restore_protection() {
  local repo="$1"
  local key; key=$(_repo_key "$repo")

  # 1. Restore classic branch protection (if it existed)
  local classicfile="$PROT_TMPDIR/${key}.classic.json"
  if [[ -f "$classicfile" ]]; then
    # Validate the saved JSON looks like real branch protection (has 'url' field)
    local has_url
    has_url=$(jq -r '.url // empty' "$classicfile" 2>/dev/null || true)
    if [[ -n "$has_url" ]]; then
      local put_body
      # enforce_admins: handle both object form {"enabled":true} and raw boolean
      put_body=$(jq '{
        required_status_checks: (
          if .required_status_checks then (
            # GitHub anyOf: use "checks" (app-aware) when present, else "contexts" (legacy).
            # Sending both causes HTTP 422 "No subschema in anyOf matched".
            if ((.required_status_checks.checks // []) | length) > 0 then {
              strict: .required_status_checks.strict,
              checks: .required_status_checks.checks
            } else {
              strict: .required_status_checks.strict,
              contexts: (.required_status_checks.contexts // [])
            } end
          ) else null end
        ),
        enforce_admins: (
          if (.enforce_admins | type) == "object" then (.enforce_admins.enabled // false)
          else (.enforce_admins // false) end
        ),
        required_pull_request_reviews: (
          if .required_pull_request_reviews then {
            dismiss_stale_reviews: (.required_pull_request_reviews.dismiss_stale_reviews // false),
            require_code_owner_reviews: (.required_pull_request_reviews.require_code_owner_reviews // false),
            required_approving_review_count: (.required_pull_request_reviews.required_approving_review_count // 1)
          } else null end
        ),
        restrictions: (
          if .restrictions then {
            users: ([.restrictions.users[]?.login] // []),
            teams: ([.restrictions.teams[]?.slug] // []),
            apps:  ([.restrictions.apps[]?.slug]  // [])
          } else null end
        ),
        required_linear_history: (
          if (.required_linear_history | type) == "object" then (.required_linear_history.enabled // false)
          else (.required_linear_history // false) end
        ),
        allow_force_pushes: (
          if (.allow_force_pushes | type) == "object" then (.allow_force_pushes.enabled // false)
          else (.allow_force_pushes // false) end
        ),
        allow_deletions: (
          if (.allow_deletions | type) == "object" then (.allow_deletions.enabled // false)
          else (.allow_deletions // false) end
        )
      }' "$classicfile" 2>/dev/null) || true
      if [[ -n "$put_body" ]]; then
        local api_err
        api_err=$(gh api -X PUT "repos/$GH_OWNER/$repo/branches/main/protection" \
          --input - <<< "$put_body" 2>&1) || \
          echo "  WARN: $repo — could not restore classic branch protection: $api_err"
      fi
    fi
    rm -f "$classicfile"
  fi

  # 2. Re-enable rulesets using their saved full JSON (exact original state)
  local rulesetsfile="$PROT_TMPDIR/${key}.rulesets"
  if [[ -f "$rulesetsfile" ]]; then
    while IFS= read -r rid; do
      [[ -z "$rid" ]] && continue
      local rulesetjson="$PROT_TMPDIR/${key}.ruleset_${rid}.json"
      if [[ -f "$rulesetjson" && -s "$rulesetjson" ]]; then
        # Restore exact original state: PUT back the full saved JSON with enforcement=active
        # (strip read-only fields GitHub rejects on PUT: id, source, source_type, created_at, updated_at)
        local restore_body
        restore_body=$(jq 'del(.id, .source, .source_type, .created_at, .updated_at, .node_id, ._links)
                          | .enforcement = "active"' "$rulesetjson" 2>/dev/null) || true
        if [[ -n "$restore_body" ]]; then
          gh api -X PUT "repos/$GH_OWNER/$repo/rulesets/$rid" \
            --input - <<< "$restore_body" &>/dev/null || \
            echo "  WARN: $repo — could not restore ruleset $rid from saved JSON (check manually)"
        fi
        rm -f "$rulesetjson"
      else
        # Fallback: just flip enforcement back to active
        gh api -X PUT "repos/$GH_OWNER/$repo/rulesets/$rid" \
          --field enforcement=active &>/dev/null || \
          echo "  WARN: $repo — could not re-enable ruleset $rid (check manually)"
      fi
    done < "$rulesetsfile"
    rm -f "$rulesetsfile"
  fi

  rm -f "$PROT_TMPDIR/${key}.repo"
}

# Cleanup trap: restore protections if script exits early (e.g. Ctrl-C)
_cleanup() {
  for repofile in "$PROT_TMPDIR"/*.repo; do
    [[ -f "$repofile" ]] || continue
    local repo; repo=$(cat "$repofile")
    local classicfile rulesetsfile
    local key; key=$(_repo_key "$repo")
    classicfile="$PROT_TMPDIR/${key}.classic.json"
    rulesetsfile="$PROT_TMPDIR/${key}.rulesets"
    if [[ -f "$classicfile" || -f "$rulesetsfile" ]]; then
      echo "  CLEANUP: restoring protection for $repo ..."
      _restore_protection "$repo" || true
    else
      rm -f "$repofile"
    fi
  done
  rm -rf "$PROT_TMPDIR"
}
trap _cleanup EXIT INT TERM

# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
echo "============================================================"
echo " ADMIN FORCE-SYNC: local main -> remote main"
echo " Repos : ${#REPOS[@]}"
echo " Owner : ${GH_OWNER:-N/A}"
echo " Commit: $( [[ "$NO_COMMIT" == "true" ]] && echo "(skipped)" || echo "\"$COMMIT_MSG\"" )"
echo " Bypass: $( [[ "$SKIP_PROTECTION" == "true" ]] && echo "skipped (--skip-protection)" || echo "via GitHub API" )"
[[ "$DRY_RUN" == "true" ]] && echo " MODE  : DRY RUN — no changes will be made"
echo "============================================================"
echo ""

ok=0
fail=0
skip=0
FAILED_REPOS=()
FAILED_REASONS=()

for repo in "${REPOS[@]}"; do
  dir="$WORKSPACE_ROOT/$repo"

  if [[ ! -d "$dir" ]]; then
    echo "  (skip) $repo — directory not found"
    ((skip++)); continue
  fi
  if [[ ! -d "$dir/.git" ]]; then
    echo "  (skip) $repo — not a git repo"
    ((skip++)); continue
  fi

  if [[ "$DRY_RUN" == "true" ]]; then
    echo "  [dry]  $repo"
    continue
  fi

  echo -n "  $repo ... "

  # 1. Stage + commit whatever HEAD is (no checkout required — we push HEAD:main)
  #    This handles repos on feat/* branches without failing on checkout.
  if [[ "$NO_COMMIT" == "false" ]]; then
    (cd "$dir" && git add -A 2>/dev/null) || true
    if [[ -n "$(cd "$dir" && git status --porcelain 2>/dev/null)" ]]; then
      (cd "$dir" && git commit -m "$COMMIT_MSG" 2>/dev/null) || true
    fi
  fi

  # 2. Disable branch protection + rulesets
  _disable_protection "$repo"

  # 3. Force-push current HEAD -> origin main (works from any local branch)
  push_out=$(mktemp)
  if (cd "$dir" && git push --force origin HEAD:main 2>"$push_out"); then
    echo "OK"
    ((ok++))
  else
    echo "FAIL"
    echo "  --- push error ---"
    cat "$push_out" | sed 's/^/    /'
    echo "  ------------------"
    FAILED_REPOS+=("$repo"); FAILED_REASONS+=("git push --force failed")
    ((fail++))
  fi
  rm -f "$push_out"

  # 4. Restore branch protection + rulesets immediately after push
  _restore_protection "$repo"
done

echo ""
echo "============================================================"
echo " Done: $ok OK  |  $fail FAIL  |  $skip skipped"
if [[ $fail -gt 0 ]]; then
  echo " Failed repos:"
  for i in "${!FAILED_REPOS[@]}"; do
    echo "   - ${FAILED_REPOS[$i]}: ${FAILED_REASONS[$i]:-unknown}"
  done
  echo "============================================================"
  exit 1
fi
echo "============================================================"
exit 0
