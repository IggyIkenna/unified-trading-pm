#!/usr/bin/env bash
# Purge from git history all files matching .gitignore patterns (credentials, secrets, build artifacts).
# Run AFTER rollout-ignore-files.sh --execute so each repo has the canonical .gitignore.
#
# PREREQUISITES:
#   - git-filter-repo installed (pip install git-filter-repo or brew install git-filter-repo)
#   - Run from unified-trading-pm (or set PM_REPO)
#
# DESTRUCTIVE: Rewrites history. All clones must re-clone or git fetch --all && git reset --hard origin/main.
# Force push required. Coordinate with team before running.
#
# Usage:
#   bash scripts/purge-gitignore-from-history.sh              # dry-run: show what would be purged
#   bash scripts/purge-gitignore-from-history.sh --execute    # run purge (no push)
#   bash scripts/purge-gitignore-from-history.sh --execute --push  # purge + force push
#
# Per-repo: run from that repo's directory:
#   git filter-repo --paths-from-file /path/to/gitignore-purge-paths.txt --invert-paths --force
#   git remote add origin <url>  # filter-repo removes origin; re-add before push
#   git push --force-with-lease origin main

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_REPO="$(cd "$SCRIPT_DIR/.." && pwd)"
WORKSPACE_ROOT="$(cd "$PM_REPO/.." && pwd)"
PATHS_FILE="$PM_REPO/scripts/gitignore-purge-paths.txt"

EXECUTE=false
PUSH=false
for arg in "$@"; do
  case "$arg" in
    --execute) EXECUTE=true ;;
    --push) PUSH=true ;;
  esac
done

SKIP_REPOS=("unified-trading-pm" "deployment-api-temp")

get_repos() {
  find "$WORKSPACE_ROOT" -maxdepth 2 -name ".git" -type d 2>/dev/null \
    | sed 's|/.git||' \
    | sort -u
}

run_purge() {
  local repo="$1"
  local name
  name="$(basename "$repo")"
  local origin_url
  origin_url="$(cd "$repo" && git remote get-url origin 2>/dev/null || true)"
  (cd "$repo" && git filter-repo --paths-from-file "$PATHS_FILE" --invert-paths --force 2>&1) || { echo "  FAILED: $name"; return 1; }
  echo "  Purged: $name"
  if [[ -n "$origin_url" ]] && $PUSH; then
    (cd "$repo" && git remote add origin "$origin_url" 2>/dev/null || true)
    (cd "$repo" && git push --force-with-lease origin main 2>&1) && echo "  Pushed" || echo "  Push FAILED"
  fi
}

main() {
  echo "Purge gitignore-matched files from git history"
  echo "Paths file: $PATHS_FILE"
  echo "Execute: $EXECUTE | Push: $PUSH"
  echo ""

  if [[ ! -f "$PATHS_FILE" ]]; then
    echo "ERROR: Paths file not found: $PATHS_FILE"
    exit 1
  fi

  if ! command -v git-filter-repo &>/dev/null; then
    echo "ERROR: git-filter-repo not found. Install: pip install git-filter-repo"
    exit 1
  fi

  for repo in $(get_repos); do
    name="$(basename "$repo")"
    if printf '%s\n' "${SKIP_REPOS[@]}" | grep -qx "$name"; then
      continue
    fi
    echo "[$name]"
    if $EXECUTE; then
      run_purge "$repo"
    else
      echo "  (dry-run: would purge; use --execute to run)"
    fi
    echo ""
  done

  if ! $EXECUTE; then
    echo "Dry-run complete. Use --execute to purge, --execute --push to purge and push."
  fi
}

main "$@"
