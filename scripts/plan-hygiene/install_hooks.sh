#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Install plan-hygiene checks as git pre-push hook in unified-trading-pm.
# Runs check_todo_regression.sh + check_frontmatter.sh before every push.
# Safe to re-run — idempotent (overwrites existing hook with the same content).
# Usage: bash scripts/plan-hygiene/install_hooks.sh [--dry-run]

set -euo pipefail
DRY_RUN="${1:-}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PM_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

HOOKS_DIR="$PM_DIR/.git/hooks"
# Handle worktrees: .git may be a file pointing to the real git dir
if [ -f "$PM_DIR/.git" ]; then
  GIT_DIR=$(awk '/^gitdir:/{print $2}' "$PM_DIR/.git")
  HOOKS_DIR="$GIT_DIR/hooks"
fi

HOOK_FILE="$HOOKS_DIR/pre-push"

HOOK_CONTENT=$(cat <<'HOOK'
#!/usr/bin/env bash
# Auto-installed by scripts/plan-hygiene/install_hooks.sh
# Runs plan hygiene hard checks before every push.
set -euo pipefail
REPO_ROOT="$(git rev-parse --show-toplevel)"
SCRIPT_DIR="$REPO_ROOT/scripts/plan-hygiene"

echo "[pre-push] Running plan hygiene checks..."

FAILED=0

if ! bash "$SCRIPT_DIR/check_todo_regression.sh" --quiet; then
  echo "[pre-push] ❌ check_todo_regression failed — fix regressions before pushing"
  FAILED=1
fi

if ! bash "$SCRIPT_DIR/check_frontmatter.sh" --quiet; then
  echo "[pre-push] ❌ check_frontmatter failed — fix violations before pushing"
  FAILED=1
fi

if [ "$FAILED" -gt 0 ]; then
  echo "[pre-push] Push blocked. Run: bash scripts/plan-hygiene/run_hygiene_sweep.sh"
  exit 1
fi

echo "[pre-push] ✅ Plan hygiene checks passed."
exit 0
HOOK
)

if [ "$DRY_RUN" = "--dry-run" ]; then
  echo "DRY-RUN: would write pre-push hook to $HOOK_FILE"
  echo ""
  echo "$HOOK_CONTENT"
  exit 0
fi

mkdir -p "$HOOKS_DIR"
echo "$HOOK_CONTENT" > "$HOOK_FILE"
chmod +x "$HOOK_FILE"
echo "✅ Installed pre-push hook: $HOOK_FILE"
echo "   Runs: check_todo_regression.sh + check_frontmatter.sh before every push"
