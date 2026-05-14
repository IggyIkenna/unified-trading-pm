#!/usr/bin/env bash
# Rolls out canonical workflow templates to all workspace repos.
#
# Templates in: unified-trading-pm/scripts/workflow-templates/
# Target: <repo>/.github/workflows/<template-name>.yml
#
# This script is the SSOT rollout mechanism for the generic per-repo workflows:
#   - request-major-bump.yml        (thin caller -> PM reusable workflow)
#   - major-bump-issue-handler.yml   (canonical flat copy)
#   - staging-lock-check.yml         (canonical flat copy)
#   - update-dependency-version.yml  (canonical flat copy)
#   - tab-mirror-to-ldr.yml          (auto-FF push tab/** -> live-defi-rollout)
#
# Usage:
#   bash rollout-workflow-templates.sh [--dry-run] [--repo NAME] [--template NAME]
#
# Examples:
#   bash rollout-workflow-templates.sh --dry-run
#   bash rollout-workflow-templates.sh --repo instruments-service
#   bash rollout-workflow-templates.sh --template staging-lock-check.yml
#   bash rollout-workflow-templates.sh --repo instruments-service --template request-major-bump.yml

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
TEMPLATE_DIR="$SCRIPT_DIR"
MANIFEST="$WORKSPACE_ROOT/unified-trading-pm/workspace-manifest.json"

DRY_RUN=false
REPO_FILTER=""
TEMPLATE_FILTER=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true; shift ;;
    --repo) REPO_FILTER="$2"; shift 2 ;;
    --template) TEMPLATE_FILTER="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 [--dry-run] [--repo NAME] [--template NAME]"
      echo ""
      echo "Rolls out canonical workflow templates to all workspace repos."
      echo ""
      echo "Options:"
      echo "  --dry-run     Show what would be copied without making changes"
      echo "  --repo NAME   Only update a specific repo"
      echo "  --template NAME  Only roll out a specific template file"
      exit 0
      ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [ ! -f "$MANIFEST" ]; then
  echo "ERROR: workspace-manifest.json not found at $MANIFEST"
  exit 1
fi

REPOS=$(python3 -c "import json; [print(r) for r in json.load(open('$MANIFEST')).get('repositories',{})]")

updated=0
skipped=0
missing_dir=0

for template in "$TEMPLATE_DIR"/*.yml; do
  [ -f "$template" ] || continue
  tname=$(basename "$template")
  [ -n "$TEMPLATE_FILTER" ] && [ "$tname" != "$TEMPLATE_FILTER" ] && continue

  echo "=== Template: $tname ==="
  for repo in $REPOS; do
    [ -n "$REPO_FILTER" ] && [ "$repo" != "$REPO_FILTER" ] && continue

    # PM owns the templates -- skip self
    [ "$repo" = "unified-trading-pm" ] && continue

    target_dir="$WORKSPACE_ROOT/$repo/.github/workflows"
    target="$target_dir/$tname"

    # Skip repos without .github/workflows/ (e.g., UI repos, codex, etc.)
    if [ ! -d "$target_dir" ]; then
      missing_dir=$((missing_dir + 1))
      continue
    fi

    # Check if target already matches template (skip if identical)
    if [ -f "$target" ] && diff -q "$template" "$target" > /dev/null 2>&1; then
      skipped=$((skipped + 1))
      continue
    fi

    if [ "$DRY_RUN" = true ]; then
      if [ -f "$target" ]; then
        echo "  [dry-update] $repo"
      else
        echo "  [dry-create] $repo"
      fi
    else
      cp "$template" "$target"
      if [ -f "$target" ]; then
        echo "  [updated] $repo"
      else
        echo "  [created] $repo"
      fi
    fi
    updated=$((updated + 1))
  done
  echo ""
done

echo "Summary:"
echo "  Updated/created: $updated"
echo "  Already current: $skipped"
echo "  No .github/workflows/: $missing_dir"
if [ "$DRY_RUN" = true ]; then
  echo "  (dry-run mode -- no files were modified)"
fi
