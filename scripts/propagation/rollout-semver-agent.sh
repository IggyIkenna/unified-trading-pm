#!/usr/bin/env bash
# Rolls out semver-agent.yml to all workspace repos with repo-specific substitution.
# Template: unified-trading-pm/scripts/workflow-templates/semver-agent.yml.tmpl
# Substitutions: __REPO_NAME__ → repo-name, __SOURCE_DIR__ → repo_name (underscored)
#
# Usage:
#   bash rollout-semver-agent.sh [--dry-run] [--repo NAME]

set -euo pipefail
WORKSPACE_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
TEMPLATE="$WORKSPACE_ROOT/unified-trading-pm/scripts/workflow-templates/semver-agent.yml.tmpl"
MANIFEST="$WORKSPACE_ROOT/unified-trading-pm/workspace-manifest.json"

DRY_RUN=false
REPO_FILTER=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true; shift ;;
    --repo) REPO_FILTER="$2"; shift 2 ;;
    *) shift ;;
  esac
done

[ -f "$TEMPLATE" ] || { echo "Template not found: $TEMPLATE"; exit 1; }

REPOS=$(python3 -c "import json; [print(r) for r in json.load(open('$MANIFEST')).get('repositories',{})]")

updated=0
for repo in $REPOS; do
  [ -n "$REPO_FILTER" ] && [ "$repo" != "$REPO_FILTER" ] && continue
  [ "$repo" = "unified-trading-pm" ] && continue
  [ "$repo" = "unified-trading-codex" ] && continue  # codex has custom semver

  target_dir="$WORKSPACE_ROOT/$repo/.github/workflows"
  [ -d "$target_dir" ] || continue

  # Convert repo-name to source_dir (replace - with _)
  source_dir=$(echo "$repo" | tr '-' '_')

  if [ "$DRY_RUN" = true ]; then
    echo "  [dry] $repo → SERVICE_NAME=$repo SOURCE_DIR=$source_dir"
  else
    sed "s|__REPO_NAME__|${repo}|g; s|__SOURCE_DIR__|${source_dir}|g" "$TEMPLATE" > "$target_dir/semver-agent.yml"
    echo "  [ok]  $repo"
  fi
  updated=$((updated+1))
done
echo "Done: $updated repos updated"
