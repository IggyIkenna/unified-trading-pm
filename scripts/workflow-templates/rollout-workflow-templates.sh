#!/usr/bin/env bash
# Rolls out canonical workflow templates to workspace repos.
#
# Two-tier template structure:
#   1. unified-trading-pm/scripts/workflow-templates/      — GENERIC; copied to every Python service repo
#   2. unified-trading-pm/scripts/workflow-templates-ui/   — UI-ONLY; copied to unified-trading-system-ui ONLY
#
# Target: <repo>/.github/workflows/<template-name>.yml
#
# Generic per-repo workflows (tier 1):
#   - request-major-bump.yml        (thin caller -> PM reusable workflow)
#   - major-bump-issue-handler.yml   (canonical flat copy)
#   - staging-lock-check.yml         (canonical flat copy)
#   - update-dependency-version.yml  (canonical flat copy)
#   - tab-mirror-to-ldr.yml          (auto-FF push tab/** -> live-defi-rollout)
#   - quality-gates-v2.yml.tmpl      (the required CI check, DEP_REPOS substituted)
#   - semver-agent.yml.tmpl          (per-repo semver-agent invocation)
#
# RETIRED workflows (workspace-qg.yml / python-quality-gates.yml / version-bump.yml) are
# guarded by _is_retired() below — even if a stale template reappears here, it is NEVER
# rolled out (a blanket rollout would otherwise resurrect dead CI fleet-wide). The stale
# `workspace-qg.yml.tmpl` was deleted 2026-06-07 (workspace-qg retired 2026-05-29).
#
# UI-only workflows (tier 2) — added 2026-05-15 to fix dead-copies-everywhere bug:
#   - uac-registry-sync.yml          (receives uac-registry-updated dispatch in UI repo)
#   - uic-openapi-sync.yml           (receives uac-openapi-updated dispatch in UI repo)
#
# Usage:
#   bash rollout-workflow-templates.sh [--dry-run] [--repo NAME] [--template NAME]
#
# Examples:
#   bash rollout-workflow-templates.sh --dry-run
#   bash rollout-workflow-templates.sh --repo instruments-service
#   bash rollout-workflow-templates.sh --template staging-lock-check.yml
#   bash rollout-workflow-templates.sh --repo instruments-service --template request-major-bump.yml
#   bash rollout-workflow-templates.sh --repo unified-trading-system-ui  # UI templates only

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
TEMPLATE_DIR="$SCRIPT_DIR"
# UI-only templates live in a sibling dir. The rollout pass for UI targets
# `unified-trading-system-ui` ONLY — these workflows receive
# `repository_dispatch` events from UAC and regenerate types in the UI repo.
# Putting them in `scripts/workflow-templates/` (this dir) would propagate dead
# copies to every Python service repo. Fixed 2026-05-15 after that bug landed.
UI_TEMPLATE_DIR="$SCRIPT_DIR/../workflow-templates-ui"
UI_TARGET_REPO="unified-trading-system-ui"
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

# ── RETIRED-workflow guard ────────────────────────────────────────────────────
# A blanket rollout (no --template) iterates EVERY file in the template dir and
# creates-if-missing in every repo. A stale template for a RETIRED workflow would
# therefore RE-CREATE that dead workflow fleet-wide (incident 2026-06-07: a leftover
# `workspace-qg.yml.tmpl` would have recreated the retired `workspace-qg.yml` — retired
# 2026-05-29, superseded by `quality-gates-v2`). Belt-and-suspenders: even if a retired
# template reappears in this dir, never roll it out. The real fix is deleting the stale
# template; this denylist is the guard so the mistake can't silently propagate again.
RETIRED_WORKFLOWS="workspace-qg.yml python-quality-gates.yml quality-gates.yml version-bump.yml"
_is_retired() {
  local name="$1"
  for r in $RETIRED_WORKFLOWS; do [ "$name" = "$r" ] && return 0; done
  return 1
}

REPOS=$(python3 -c "import json; [print(r) for r in json.load(open('$MANIFEST')).get('repositories',{})]")

# dep_repos per repo (space-separated dep names), as the TRANSITIVE EDITABLE CLOSURE.
#
# SOURCE OF TRUTH = each repo's pyproject `path = "../<repo>"` editable deps — NOT
# workspace-manifest.json. The manifest's `dependencies` list was found INCOMPLETE
# (2026-06-01): e.g. system-integration-tests' manifest closure was 10 but its
# pyproject closure is 12 (missing alerting-service + client-reporting-api), which is
# exactly why SIT's quality-gates-v2 install failed on
# `metadata for alerting-service==0.1.0 @ editable+../alerting-service`. The manifest
# also carried a phantom (`ml-service` → `unified-trading-deployment`). pyproject is
# what `uv sync` actually resolves, so deriving from it makes CI clone precisely the
# editable siblings the install needs.
#
# TRANSITIVE: walks the full editable tree (uv sync resolves path-sourced deps
# recursively; a missing transitive dep fails install with "Distribution not found
# at file:///..."). For any node lacking a pyproject (e.g. a not-checked-out sub-repo
# referenced indirectly), fall back to that node's manifest deps so the closure is
# never silently truncated.
get_dep_repos() {
  local repo="$1"
  WS_ROOT="$WORKSPACE_ROOT" MANIFEST_PATH="$MANIFEST" python3 -c "
import json, os, re

ws = os.environ['WS_ROOT']
manifest_path = os.environ['MANIFEST_PATH']
self_repo = '$repo'

try:
    repos = json.load(open(manifest_path)).get('repositories', {})
except Exception:
    repos = {}

_PATH_RE = re.compile(r'path\s*=\s*\"\.\./([^\"]+)\"')

def manifest_deps(name):
    r = repos.get(name, {})
    return [d['name'] for d in r.get('dependencies', []) if isinstance(d, dict) and 'name' in d]

def pyproject_deps(name):
    p = os.path.join(ws, name, 'pyproject.toml')
    if not os.path.isfile(p):
        return None  # signal: no pyproject for this node → caller falls back to manifest
    out = []
    with open(p) as fh:
        for line in fh:
            mm = _PATH_RE.search(line)
            if mm:
                dep = mm.group(1).strip().strip('/').split('/')[0]
                if dep and dep not in out:
                    out.append(dep)
    return out

def direct_deps(name):
    py = pyproject_deps(name)
    return py if py is not None else manifest_deps(name)

# Transitive closure via BFS, preserving discovery order; exclude self-reference.
visited = []
queue = list(direct_deps(self_repo))
while queue:
    dep = queue.pop(0)
    if dep in visited or dep == self_repo:
        continue
    visited.append(dep)
    queue.extend(direct_deps(dep))
print(' '.join(visited))
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

  # Never roll out a RETIRED workflow (would resurrect dead CI fleet-wide).
  if _is_retired "$tname"; then
    echo "=== Template: $tbase → $tname  [SKIPPED — retired workflow; delete this stale template] ==="
    continue
  fi

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

# ── UI-ONLY TEMPLATES ────────────────────────────────────────────────────────
# Process templates from $UI_TEMPLATE_DIR — these go ONLY to $UI_TARGET_REPO,
# never to Python service repos (they'd be dead copies receiving no dispatch).
if [ -d "$UI_TEMPLATE_DIR" ] && [ -z "$REPO_FILTER" -o "$REPO_FILTER" = "$UI_TARGET_REPO" ]; then
  ui_target_dir="$WORKSPACE_ROOT/$UI_TARGET_REPO/.github/workflows"
  if [ ! -d "$ui_target_dir" ]; then
    echo "WARN: UI repo workflows dir not found at $ui_target_dir — skipping UI templates" >&2
  else
    for template in "$UI_TEMPLATE_DIR"/*.yml; do
      [ -f "$template" ] || continue
      tname=$(basename "$template")
      [ -n "$TEMPLATE_FILTER" ] && [ "$tname" != "$TEMPLATE_FILTER" ] && continue
      if _is_retired "$tname"; then
        echo "=== UI Template: $tname  [SKIPPED — retired workflow] ==="
        continue
      fi
      echo "=== UI Template: $tname → $UI_TARGET_REPO ==="
      target="$ui_target_dir/$tname"
      if [ -f "$target" ] && diff -q "$template" "$target" > /dev/null 2>&1; then
        skipped=$((skipped + 1))
        echo "  [skipped — already current] $UI_TARGET_REPO"
        continue
      fi
      if [ "$DRY_RUN" = true ]; then
        echo "  [dry-$([ -f "$target" ] && echo update || echo create)] $UI_TARGET_REPO"
      else
        cp "$template" "$target"
        echo "  [$([ -f "$target" ] && echo updated || echo created)] $UI_TARGET_REPO"
      fi
      updated=$((updated + 1))
    done
  fi
fi

echo "Summary:"
echo "  Updated/created: $updated"
echo "  Already current: $skipped"
echo "  No .github/workflows/: $missing_dir"
if [ "$DRY_RUN" = true ]; then
  echo "  (dry-run mode -- no files were modified)"
fi
