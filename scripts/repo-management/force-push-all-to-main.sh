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
#   bash force-push-all-to-main.sh --max-workers 8              # Parallel workers (default 8)
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
MAX_WORKERS=${MAX_WORKERS:-8}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)             DRY_RUN=true; shift ;;
    --bypass-protection)   BYPASS_PROTECTION=true; shift ;;
    --no-restore)          RESTORE_PROTECTION=false; shift ;;
    --limit)               LIMIT="$2"; shift 2 ;;
    --repos)               REPOS_FILTER="$2"; shift 2 ;;
    --max-workers)         MAX_WORKERS="$2"; shift 2 ;;
    *)                     shift ;;
  esac
done

if [[ ! -f "$MANIFEST" ]]; then
  echo "Missing $MANIFEST"
  exit 1
fi

# Build level-ordered repo list from manifest topologicalOrder.
# Falls back to alphabetical keys[] if topologicalOrder is absent.
# When --repos is specified, skip topology and use the explicit list.
USE_TOPO=false
if [[ -z "$REPOS_FILTER" ]]; then
  TOPO_CHECK=$(python3.13 -c "
import json, sys
with open('$MANIFEST') as f: data = json.load(f)
levels = data.get('topologicalOrder', {}).get('levels', [])
print('yes' if levels else 'no')
" 2>/dev/null || echo "no")
  [[ "$TOPO_CHECK" = "yes" ]] && USE_TOPO=true
fi

if [[ -n "$REPOS_FILTER" ]]; then
  REPOS=($REPOS_FILTER)
elif [[ "$USE_TOPO" = false ]]; then
  REPOS=($(jq -r '.repositories | keys[]' "$MANIFEST" 2>/dev/null))
fi

if [[ -n "$LIMIT" && "$USE_TOPO" = false ]]; then
  REPOS=("${REPOS[@]:0:$LIMIT}")
fi

TOTAL=$(
  if [[ "$USE_TOPO" = true ]]; then
    python3.13 -c "
import json
with open('$MANIFEST') as f: data = json.load(f)
levels = data.get('topologicalOrder', {}).get('levels', [])
print(sum(len(l.get('repos',[])) for l in levels))
" 2>/dev/null
  else
    echo "${#REPOS[@]}"
  fi
)

echo "Force-push to main: $TOTAL repos (max-workers=$MAX_WORKERS, topo-order=$USE_TOPO)"
[[ "$DRY_RUN" = true ]]          && echo "DRY RUN — no pushes will be made"
[[ "$BYPASS_PROTECTION" = true ]] && echo "BYPASS PROTECTION — will disable branch protection + rulesets before push"
[[ "$BYPASS_PROTECTION" = true && "$RESTORE_PROTECTION" = false ]] && echo "NO RESTORE — protections left disabled after push"
echo ""

# ── helpers ────────────────────────────────────────────────────────────────

# Init backup dir eagerly so parallel subshells share the same path
PROT_BACKUP_DIR=""
if [[ "$BYPASS_PROTECTION" = true ]]; then
  PROT_BACKUP_DIR="$(mktemp -d)"
  export PROT_BACKUP_DIR
fi

backup_and_disable_protection() {
  local repo="$1"
  [[ -z "$PROT_BACKUP_DIR" ]] && return
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

# ── per-repo worker ─────────────────────────────────────────────────────────

push_repo() {
  local repo="$1" result_file="$2"
  local dir="$WORKSPACE_ROOT/$repo"
  local log; log=$(mktemp)

  {
    if [[ ! -d "$dir" ]]; then
      echo "(skip) $repo — not in workspace"
      echo "SKIP:$repo" >"$result_file"
      return
    fi
    if [[ ! -d "$dir/.git" ]]; then
      echo "(skip) $repo — not a git repo"
      echo "SKIP:$repo" >"$result_file"
      return
    fi

    # Ensure we're on main
    (cd "$dir" && git checkout main 2>/dev/null) || true

    # Stage ALL local changes
    (cd "$dir" && git add -A)

    if [[ "$DRY_RUN" = true ]]; then
      echo "  [dry] $repo"
      (cd "$dir" && git status -sb | head -1)
      (cd "$dir" && git diff --cached --stat)
      echo "OK:$repo" >"$result_file"
      return
    fi

    if ! (cd "$dir" && git diff --cached --quiet 2>/dev/null); then
      staged_summary=$(cd "$dir" && git diff --cached --stat | tail -1)
      (cd "$dir" && git commit -m "chore: force-sync local state" --no-verify 2>/dev/null) && \
        echo "    [commit] $repo — $staged_summary" || \
        echo "    [commit] WARN: commit failed for $repo (continuing)"
    fi

    if [[ "$BYPASS_PROTECTION" = true ]]; then
      backup_and_disable_protection "$repo"
    fi

    echo -n "  $repo ... "
    if (cd "$dir" && git push --force origin main 2>&1); then
      echo "OK"
      echo "OK:$repo" >"$result_file"
    else
      echo "FAIL"
      echo "FAIL:$repo" >"$result_file"
    fi

    if [[ "$BYPASS_PROTECTION" = true && "$RESTORE_PROTECTION" = true ]]; then
      restore_protection "$repo"
    fi
  } >"$log" 2>&1

  cat "$log"
  rm -f "$log"
}

export -f push_repo backup_and_disable_protection restore_protection
export GITHUB_ORG WORKSPACE_ROOT DRY_RUN BYPASS_PROTECTION RESTORE_PROTECTION PROT_BACKUP_DIR

# ── parallel batch helper ────────────────────────────────────────────────────
# Runs a list of repos in parallel (up to MAX_WORKERS), writes results to RESULT_DIR.
# Populates global failed / failed_repos — does NOT abort on failure (collect-all).

run_batch() {
  local -a batch=("$@")
  local -a pids=()

  for repo in "${batch[@]}"; do
    rf="$RESULT_DIR/${repo//\//__}.result"

    while [[ ${#pids[@]} -ge $MAX_WORKERS ]]; do
      wait "${pids[0]}" 2>/dev/null || true
      pids=("${pids[@]:1}")
    done

    push_repo "$repo" "$rf" &
    pids+=("$!")
  done

  for pid in "${pids[@]+"${pids[@]}"}"; do
    wait "$pid" 2>/dev/null || true
  done
}

# ── main loop ────────────────────────────────────────────────────────────────

RESULT_DIR="$(mktemp -d)"
trap 'cleanup; rm -rf "$RESULT_DIR"' EXIT

failed=0
failed_repos=()

if [[ "$USE_TOPO" = true ]]; then
  # Level-sequential, parallel within each level
  NUM_LEVELS=$(python3.13 -c "
import json
with open('$MANIFEST') as f: data = json.load(f)
levels = data.get('topologicalOrder', {}).get('levels', [])
print(len(levels))
" 2>/dev/null)

  for level_idx in $(seq 0 $((NUM_LEVELS - 1))); do
    level_repos=($(python3.13 -c "
import json
with open('$MANIFEST') as f: data = json.load(f)
levels = sorted(data.get('topologicalOrder', {}).get('levels', []), key=lambda l: l.get('level', 999))
repos = levels[$level_idx].get('repos', []) if $level_idx < len(levels) else []
for r in repos: print(r)
" 2>/dev/null))

    [[ ${#level_repos[@]} -eq 0 ]] && continue
    level_num=$((level_idx + 1))
    echo "── Level $level_num (${#level_repos[@]} repos, max $MAX_WORKERS parallel) ──"
    run_batch "${level_repos[@]}"

    # Collect failures for this level (informational only — push continues across levels)
    for repo in "${level_repos[@]}"; do
      rf="$RESULT_DIR/${repo//\//__}.result"
      [[ -f "$rf" ]] || continue
      result=$(cat "$rf")
      [[ "$result" == FAIL:* ]] && { r="${result#FAIL:}"; ((failed++)) || true; failed_repos+=("$r"); }
    done
  done
else
  # Flat parallel — explicit --repos list or no topology in manifest
  run_batch "${REPOS[@]}"

  for rf in "$RESULT_DIR"/*.result; do
    [[ -f "$rf" ]] || continue
    result=$(cat "$rf")
    [[ "$result" == FAIL:* ]] && { r="${result#FAIL:}"; ((failed++)) || true; failed_repos+=("$r"); }
  done
fi

echo ""
if [[ $failed -gt 0 ]]; then
  echo "Failed: $failed"
  for r in "${failed_repos[@]}"; do echo "  - $r"; done
  exit 1
fi
echo "Done."
exit 0
