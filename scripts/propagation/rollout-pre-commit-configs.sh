#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Rolls out canonical pre-commit configs to all workspace repos.
# Templates: unified-trading-pm/scripts/pre-commit-templates/
# Selects template based on repo type from workspace-manifest.json.
#
# Usage:
#   bash rollout-pre-commit-configs.sh [--dry-run] [--repo NAME]

set -euo pipefail

WORKSPACE_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
TEMPLATE_DIR="$WORKSPACE_ROOT/unified-trading-pm/scripts/pre-commit-templates"
MANIFEST="$WORKSPACE_ROOT/unified-trading-pm/workspace-manifest.json"

DRY_RUN=false
REPO_FILTER=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true; shift ;;
    --repo) REPO_FILTER="$2"; shift 2 ;;
    *) echo "Unknown flag: $1"; exit 1 ;;
  esac
done

[ -f "$MANIFEST" ] || { echo "Manifest not found: $MANIFEST"; exit 1; }
[ -d "$TEMPLATE_DIR" ] || { echo "Template dir not found: $TEMPLATE_DIR"; exit 1; }

# Determine template for a repo based on manifest type/arch_tier and filesystem signals.
# Args: repo_name
# Outputs template filename to stdout.
get_template() {
  local repo="$1"

  # Special cases: PM and codex are docs repos
  if [ "$repo" = "unified-trading-pm" ] || [ "$repo" = "unified-trading-codex" ]; then
    echo "docs.pre-commit-config.yaml"
    return
  fi

  # Read type and arch_tier from manifest
  local repo_type arch_tier
  repo_type=$(python3 -c "
import json, sys
m = json.load(open('$MANIFEST'))
info = m.get('repositories', {}).get('$repo', {})
print(info.get('type', ''))
" 2>/dev/null || echo "")
  arch_tier=$(python3 -c "
import json, sys
m = json.load(open('$MANIFEST'))
info = m.get('repositories', {}).get('$repo', {})
print(info.get('arch_tier', ''))
" 2>/dev/null || echo "")

  # UI repos: arch_tier=ui, or type=ui, or has package.json without pyproject.toml
  if [ "$arch_tier" = "ui" ] || [ "$repo_type" = "ui" ]; then
    echo "ui.pre-commit-config.yaml"
    return
  fi

  # UI detection by filesystem (package.json present, no pyproject.toml)
  if [ -f "$WORKSPACE_ROOT/$repo/package.json" ] && [ ! -f "$WORKSPACE_ROOT/$repo/pyproject.toml" ]; then
    echo "ui.pre-commit-config.yaml"
    return
  fi

  # Library repos: arch_tier is a number (tier 0/1/2/3) or "library", or type contains "library" or "interface"
  case "$repo_type" in
    library|interface) echo "python-library.pre-commit-config.yaml"; return ;;
  esac
  case "$arch_tier" in
    0|1|2|3|library) echo "python-library.pre-commit-config.yaml"; return ;;
  esac
  # Name-based library/interface detection
  case "$repo" in
    *-library|*-interface) echo "python-library.pre-commit-config.yaml"; return ;;
  esac

  # Service and API repos
  case "$repo_type" in
    service|api-service|api|batch-service) echo "python-service.pre-commit-config.yaml"; return ;;
  esac

  # Infrastructure repos (deployment-service, ibkr-gateway-infra) use service template
  case "$repo_type" in
    infrastructure|devops) echo "python-service.pre-commit-config.yaml"; return ;;
  esac

  # Test harness repos use service template
  case "$repo_type" in
    test-harness) echo "python-service.pre-commit-config.yaml"; return ;;
  esac

  # Fallback: if pyproject.toml exists, use service template; otherwise ui
  if [ -f "$WORKSPACE_ROOT/$repo/pyproject.toml" ]; then
    echo "python-service.pre-commit-config.yaml"
  elif [ -f "$WORKSPACE_ROOT/$repo/package.json" ]; then
    echo "ui.pre-commit-config.yaml"
  else
    echo "python-service.pre-commit-config.yaml"
  fi
}

# Get all repo names from manifest
REPOS=$(python3 -c "import json; [print(r) for r in json.load(open('$MANIFEST')).get('repositories',{})]")

updated=0
skipped=0
created=0

for repo in $REPOS; do
  [ -n "$REPO_FILTER" ] && [ "$repo" != "$REPO_FILTER" ] && continue

  repo_dir="$WORKSPACE_ROOT/$repo"
  [ -d "$repo_dir" ] || { echo "  [skip] $repo (dir not found)"; skipped=$((skipped+1)); continue; }

  template_file=$(get_template "$repo")
  template_path="$TEMPLATE_DIR/$template_file"

  if [ ! -f "$template_path" ]; then
    echo "  [err]  $repo: template not found: $template_file"
    skipped=$((skipped+1))
    continue
  fi

  # Propagate PM's canonical .gitleaks.toml as a REAL FILE COPY (never a symlink — a
  # sibling-repo-relative symlink resolves fine in the operator's local multi-repo layout but is a
  # dangling ENOENT in any standalone single-repo CI checkout, where the sibling unified-trading-pm
  # directory does not exist; this exact regression broke unified-trading-system-ui's e2e build on
  # 2026-07-28, re-introducing a bug already fixed once via commit a4ec4985 on 2026-06-23).
  # PM itself owns the canonical .gitleaks.toml — skip copying it onto itself.
  # Deliberately runs BEFORE the .pre-commit-config.yaml "already current" continue below — this is
  # an independent propagation concern and must not go dead just because the template hasn't
  # changed (this exact ordering bug is why agent-orchestrator/strategy-service/unified-trading-
  # library were STILL silently symlinked despite this script running regularly).
  if [ "$repo" != "unified-trading-pm" ]; then
    leaks_src="$WORKSPACE_ROOT/unified-trading-pm/.gitleaks.toml"
    leaks_target="$repo_dir/.gitleaks.toml"
    # -L check is required, not just the diff: a symlink whose target happens to resolve locally
    # (operator's sibling-repo layout) diffs byte-identical to leaks_src, so content comparison
    # ALONE can never detect "this is still a symlink and needs to become a real file".
    if [ -L "$leaks_target" ] || [ ! -f "$leaks_target" ] || ! diff -q "$leaks_src" "$leaks_target" >/dev/null 2>&1; then
      if [ "$DRY_RUN" = true ]; then
        echo "  [dry]  $repo <- .gitleaks.toml (copy)"
      else
        # Remove a stale symlink/file if any, then copy the real content.
        rm -f "$leaks_target"
        cp "$leaks_src" "$leaks_target"
        echo "  [ok]   $repo <- .gitleaks.toml (copy)"
      fi
    fi
  fi

  target="$repo_dir/.pre-commit-config.yaml"

  # Check if already current (byte-for-byte identical)
  if [ -f "$target" ] && diff -q "$template_path" "$target" >/dev/null 2>&1; then
    skipped=$((skipped+1))
    continue
  fi

  template_label="${template_file%.pre-commit-config.yaml}"

  if [ -f "$target" ]; then
    action="updated"
  else
    action="created"
    created=$((created+1))
  fi

  if [ "$DRY_RUN" = true ]; then
    echo "  [dry]  $repo <- $template_label ($action)"
  else
    cp "$template_path" "$target"
    echo "  [ok]   $repo <- $template_label ($action)"
  fi
  updated=$((updated+1))
done

echo ""
echo "Done: $updated repos updated/created, $skipped skipped (already current or missing dir)"
if [ "$created" -gt 0 ]; then
  echo "  ($created new .pre-commit-config.yaml files created)"
fi
