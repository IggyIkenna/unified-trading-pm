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

# dep_repos per repo from manifest (space-separated dep names)
get_dep_repos() {
  local repo="$1"
  python3 -c "
import json
m = json.load(open('$MANIFEST'))
r = m.get('repositories', {}).get('$repo', {})
deps = r.get('dependencies', [])
names = [d['name'] for d in deps if isinstance(d, dict) and 'name' in d]
print(' '.join(names))
" 2>/dev/null || echo ""
}

updated=0
skipped=0
missing_dir=0

# Process both direct .yml templates and .yml.tmpl templates (with substitution)
for template in "$TEMPLATE_DIR"/*.yml "$TEMPLATE_DIR"/*.yml.tmpl; do
  [ -f "$template" ] || continue
  tbase=$(basename "$template")
  # For .yml.tmpl files, strip .tmpl to get the output filename
  if [[ "$tbase" == *.yml.tmpl ]]; then
    tname="${tbase%.tmpl}"
    is_tmpl=true
  else
    tname="$tbase"
    is_tmpl=false
  fi
  [ -n "$TEMPLATE_FILTER" ] && [ "$tname" != "$TEMPLATE_FILTER" ] && [ "$tbase" != "$TEMPLATE_FILTER" ] && continue

  echo "=== Template: $tbase → $tname ==="
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

    # For .tmpl files: perform substitution; for .yml files: direct copy
    if [ "$is_tmpl" = true ]; then
      dep_repos=$(get_dep_repos "$repo")
      repo_underscore="${repo//-/_}"
      rendered=$(sed -e "s/{{DEP_REPOS}}/${dep_repos}/g" \
                     -e "s/__REPO_NAME__/${repo}/g" \
                     -e "s/__SOURCE_DIR__/${repo_underscore}/g" \
                     "$template")
      # Skip if target already matches rendered output
      if [ -f "$target" ] && [ "$(cat "$target")" = "$rendered" ]; then
        skipped=$((skipped + 1))
        continue
      fi
      if [ "$DRY_RUN" = true ]; then
        echo "  [dry-$([ -f "$target" ] && echo update || echo create)-tmpl] $repo (dep_repos=${dep_repos})"
      else
        echo "$rendered" > "$target"
        echo "  [$([ -f "$target" ] && echo updated || echo created)-tmpl] $repo (dep_repos=${dep_repos})"
      fi
    else
      # Check if target already matches template (skip if identical)
      if [ -f "$target" ] && diff -q "$template" "$target" > /dev/null 2>&1; then
        skipped=$((skipped + 1))
        continue
      fi
      if [ "$DRY_RUN" = true ]; then
        echo "  [dry-$([ -f "$target" ] && echo update || echo create)] $repo"
      else
        cp "$template" "$target"
        echo "  [$([ -f "$target" ] && echo updated || echo created)] $repo"
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
