#!/usr/bin/env bash
# rollout-semver-agent.sh — Roll out semver-agent.yml to repos that still have version-bump.yml.
#
# The semver-agent.yml template (scripts/propagation/templates/semver-agent.yml) already
# correctly fires on staging push. This script copies it to repos and removes the old
# version-bump.yml (which is simpler regex-only and fires on main).
#
# Usage:
#   bash scripts/rollout-semver-agent.sh [--repo NAME] [--dry-run] [--no-commit]
#
# Options:
#   --repo NAME    Only roll out to this specific repo (default: all repos in manifest)
#   --dry-run      Show what would be done without making changes
#   --no-commit    Apply changes but don't commit (for review)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PM_DIR="${WORKSPACE_ROOT}/unified-trading-pm"
TEMPLATE="${PM_DIR}/scripts/propagation/templates/semver-agent.yml"
MANIFEST="${PM_DIR}/workspace-manifest.json"

DRY_RUN=false
NO_COMMIT=false
TARGET_REPO=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --repo) TARGET_REPO="$2"; shift 2 ;;
    --dry-run) DRY_RUN=true; shift ;;
    --no-commit) NO_COMMIT=true; shift ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [ ! -f "$TEMPLATE" ]; then
  echo "ERROR: Template not found: $TEMPLATE"
  exit 1
fi

echo "=== Semver Agent Rollout ==="
echo "Template: $TEMPLATE"
echo "Dry run: $DRY_RUN"
echo ""

# Get list of repos
if [ -n "$TARGET_REPO" ]; then
  REPOS="$TARGET_REPO"
else
  REPOS=$(python3 -c "
import json
m = json.load(open('${MANIFEST}'))
for name, data in m.get('repositories', {}).items():
    repo_type = data.get('type', 'service')
    # Library repos use wheel builds not Docker; they also use version-bump
    print(name)
")
fi

ROLLED=0
SKIPPED=0
ALREADY_DONE=0

for REPO in $REPOS; do
  REPO_DIR="${WORKSPACE_ROOT}/${REPO}"
  if [ ! -d "$REPO_DIR" ]; then
    echo "  SKIP $REPO: directory not found at $REPO_DIR"
    SKIPPED=$((SKIPPED+1))
    continue
  fi

  WORKFLOWS_DIR="${REPO_DIR}/.github/workflows"
  if [ ! -d "$WORKFLOWS_DIR" ]; then
    echo "  SKIP $REPO: no .github/workflows/ directory"
    SKIPPED=$((SKIPPED+1))
    continue
  fi

  TARGET_FILE="${WORKFLOWS_DIR}/semver-agent.yml"
  OLD_FILE="${WORKFLOWS_DIR}/version-bump.yml"

  # Check if already rolled out
  if [ -f "$TARGET_FILE" ] && [ ! -f "$OLD_FILE" ]; then
    echo "  DONE $REPO: semver-agent.yml present, version-bump.yml already removed"
    ALREADY_DONE=$((ALREADY_DONE+1))
    continue
  fi

  echo "  ROLL $REPO:"

  if $DRY_RUN; then
    [ -f "$OLD_FILE" ] && echo "       would remove: version-bump.yml"
    echo "       would copy: semver-agent.yml from template"
    ROLLED=$((ROLLED+1))
    continue
  fi

  # Copy template
  cp "$TEMPLATE" "$TARGET_FILE"
  echo "       copied semver-agent.yml"

  # Remove old version-bump.yml
  if [ -f "$OLD_FILE" ]; then
    rm "$OLD_FILE"
    echo "       removed version-bump.yml"
  fi

  if $NO_COMMIT; then
    echo "       (--no-commit: changes applied but not committed)"
    ROLLED=$((ROLLED+1))
    continue
  fi

  # Commit to the repo.
  # IMPORTANT: use a ONE-SHOT transient identity via `git -c …` — NOT persistent
  # `git config`. `.tabs/<N>/<repo>` worktrees SHARE the main clone's `.git/config`, so a
  # persistent `git config user.email "semver-rollout[bot]@…"` here leaks the bot identity
  # into every slot worktree of this repo (agent commits then masquerade as the bot — the
  # 2026-06-03 fleet misconfig). The bot identity is needed only for THIS commit.
  # SSOT: codex/05-infrastructure/per-tab-worktrees.md § "Commit attribution".
  cd "$REPO_DIR"
  _bot_name="semver-rollout[bot]"
  _bot_email="semver-rollout[bot]@users.noreply.github.com"

  git add ".github/workflows/semver-agent.yml" 2>/dev/null || true
  git rm ".github/workflows/version-bump.yml" --cached 2>/dev/null || true
  if ! git diff --staged --quiet 2>/dev/null; then
    git -c user.name="$_bot_name" -c user.email="$_bot_email" commit -m "feat: roll out semver-agent.yml, retire version-bump.yml [skip ci]

semver-agent.yml fires on staging push (not main), uses Claude Haiku for
commit analysis + API diff detection, blocks staging-to-main on label mismatch.
Replaces version-bump.yml (simple regex bumper, now disabled in PM).

Co-Authored-By: semver-rollout[bot] <semver-rollout[bot]@users.noreply.github.com>"
    echo "       committed"
  else
    echo "       nothing to commit"
  fi
  cd "${WORKSPACE_ROOT}"

  ROLLED=$((ROLLED+1))
done

echo ""
echo "=== Summary ==="
echo "  Rolled out:   $ROLLED"
echo "  Already done: $ALREADY_DONE"
echo "  Skipped:      $SKIPPED"
