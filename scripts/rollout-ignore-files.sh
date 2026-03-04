#!/usr/bin/env bash
# Roll out unified-trading-pm .cursorignore and .gitignore to all workspace repos.
# SSOT: unified-trading-pm has the most exhaustive ignore rules.
#
# Usage:
#   bash scripts/rollout-ignore-files.sh              # dry-run (default)
#   bash scripts/rollout-ignore-files.sh --execute    # copy files
#
# Run from workspace root or unified-trading-pm.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_REPO="$(cd "$SCRIPT_DIR/.." && pwd)"
WORKSPACE_ROOT="$(cd "$PM_REPO/.." && pwd)"
CANONICAL_CURSORIGNORE="$PM_REPO/.cursorignore"
CANONICAL_GITIGNORE="$PM_REPO/.gitignore"

EXECUTE=false
if [[ "${1:-}" == "--execute" ]]; then
  EXECUTE=true
fi

# Repos to skip (no .git, or special cases)
SKIP_REPOS=(
  "unified-trading-pm"  # source repo
  "deployment-api-temp"
)

get_repos() {
  find "$WORKSPACE_ROOT" -maxdepth 2 -name ".git" -type d 2>/dev/null \
    | sed 's|/.git||' \
    | xargs -I{} dirname {}/. \
    | sort -u
}

copy_if_different() {
  local src="$1"
  local dst="$2"
  if [[ ! -f "$src" ]]; then
    echo "  ERROR: Source missing: $src"
    return 1
  fi
  if [[ -f "$dst" ]] && diff -q "$src" "$dst" >/dev/null 2>&1; then
    echo "  (unchanged)"
    return 0
  fi
  if $EXECUTE; then
    cp "$src" "$dst"
    echo "  COPIED"
  else
    echo "  WOULD COPY (use --execute to apply)"
  fi
}

main() {
  echo "Rollout: .cursorignore and .gitignore from unified-trading-pm"
  echo "Workspace root: $WORKSPACE_ROOT"
  echo "Execute: $EXECUTE"
  echo ""

  for repo in $(get_repos); do
    local name
    name="$(basename "$repo")"
    if printf '%s\n' "${SKIP_REPOS[@]}" | grep -qx "$name"; then
      continue
    fi
    echo "[$name]"
    echo -n "  .cursorignore: "
    copy_if_different "$CANONICAL_CURSORIGNORE" "$repo/.cursorignore"
    echo -n "  .gitignore: "
    copy_if_different "$CANONICAL_GITIGNORE" "$repo/.gitignore"
    echo ""
  done

  if ! $EXECUTE; then
    echo "Dry-run complete. Run with --execute to apply changes."
  fi
}

main "$@"
