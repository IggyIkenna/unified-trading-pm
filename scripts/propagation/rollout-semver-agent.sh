#!/usr/bin/env bash
# CANONICAL semver-agent.yml rollout — the ONE tool, the ONE SSOT (2026-06-07).
#
# SSOT template: unified-trading-pm/scripts/workflow-templates/semver-agent.yml.tmpl
#   — the only fully-current copy: has the version-commit step (PM #149), the
#     `quality-gates-v2` trigger (3d13e6b71), the `pm-readiness` checkout (f9deb76f7),
#     `permissions: contents: write`, and Slack (not Telegram). The former
#     `scripts/templates/semver-agent.yml` (dead) + `scripts/propagation/templates/
#     semver-agent.yml` (stale: dead `"Quality Gates"` trigger + broken
#     `../unified-trading-pm` checkout) were DELETED 2026-06-07 to collapse the
#     quadruple template drift. Do NOT re-introduce a second template.
#
# Substitutions: __REPO_NAME__ → repo-name, __SOURCE_DIR__ → repo_name (underscored)
#
# Deploys to EVERY repo in workspace-manifest.json (including the cascade roots
# unified-api-contracts / unified-trading-library / deployment-service — whose missing
# version-commit is the ROOT CAUSE of the dep-cascade jam) — NOT just service/api tiers.
#
# Two-pass ship per repo: writes the rendered workflow, then ships it via
# `quickmerge --agent --files .github/workflows/semver-agent.yml` (Pass-1 QG sentinel +
# Pass-2 staging PR). On agent_orchestrator (no quickmerge/staging yet) it falls back to a
# direct commit+push to live-defi-rollout. Idempotent: a repo whose live workflow already
# byte-matches the rendered output is skipped (no empty commit).
#
# Usage:
#   bash scripts/propagation/rollout-semver-agent.sh [--dry-run] [--repo NAME] [--no-commit]
#
#   --dry-run     render + diff only; never write, commit, or push
#   --repo NAME   single repo (by manifest name)
#   --no-commit   write the rendered file into each repo but do NOT commit/push
#                 (legacy behaviour — for inspecting the rendered output locally)

set -euo pipefail
WORKSPACE_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
PM_ROOT="$WORKSPACE_ROOT/unified-trading-pm"
TEMPLATE="$PM_ROOT/scripts/workflow-templates/semver-agent.yml.tmpl"
MANIFEST="$PM_ROOT/workspace-manifest.json"

DRY_RUN=false
NO_COMMIT=false
REPO_FILTER=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true; shift ;;
    --no-commit) NO_COMMIT=true; shift ;;
    --repo) REPO_FILTER="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

[ -f "$TEMPLATE" ] || { echo "Template not found: $TEMPLATE"; exit 1; }

# Sanity-assert the SSOT really is the current one (fail loud if a regressed template
# is ever swapped in — these are the exact axes that drifted across the dead copies).
for marker in "quality-gates-v2" "pm-readiness" "contents: write" "__REPO_NAME__"; do
  grep -q "$marker" "$TEMPLATE" || { echo "SSOT template missing expected marker: $marker — refusing to roll out a regressed template"; exit 1; }
done

REPOS=$(python3 -c "import json; [print(r) for r in json.load(open('$MANIFEST')).get('repositories',{})]")

updated=0
shipped=0
skipped=0
failed=0
for repo in $REPOS; do
  [ -n "$REPO_FILTER" ] && [ "$repo" != "$REPO_FILTER" ] && continue
  [ "$repo" = "unified-trading-pm" ] && continue          # PM has its own semver-agent
  [ "$repo" = "unified-trading-codex" ] && continue        # archived; not a live repo

  repo_dir="$WORKSPACE_ROOT/$repo"
  target_dir="$repo_dir/.github/workflows"
  [ -d "$target_dir" ] || { echo "  [skip] $repo — not cloned locally"; continue; }

  source_dir=$(echo "$repo" | tr '-' '_')
  rendered=$(sed "s|__REPO_NAME__|${repo}|g; s|__SOURCE_DIR__|${source_dir}|g" "$TEMPLATE")
  target_file="$target_dir/semver-agent.yml"

  # Idempotency: skip if the live workflow already matches the rendered SSOT.
  if [ -f "$target_file" ] && [ "$rendered" = "$(cat "$target_file")" ]; then
    echo "  [same] $repo — semver-agent.yml already matches SSOT"
    skipped=$((skipped+1))
    continue
  fi

  if [ "$DRY_RUN" = true ]; then
    echo "  [dry]  $repo → would render (SERVICE_NAME=$repo SOURCE_DIR=$source_dir):"
    diff <(echo "$rendered") "$target_file" 2>/dev/null | head -20 || echo "    (new file)"
    updated=$((updated+1))
    continue
  fi

  printf '%s\n' "$rendered" > "$target_file"
  echo "  [ok]   $repo — semver-agent.yml rendered"
  updated=$((updated+1))

  [ "$NO_COMMIT" = true ] && continue

  # Ship per-repo. quickmerge (two-pass) on every repo that has it; direct push on
  # agent_orchestrator (still mid-migration: no quickmerge/staging).
  pushd "$repo_dir" >/dev/null
  if [ -f "scripts/quality-gates.sh" ] && [ -f "scripts/quickmerge.sh" ]; then
    # Pass 1 — full QG writes the .qg_last_passed_sha sentinel quickmerge verifies.
    if bash scripts/quality-gates.sh --no-fix >/dev/null 2>&1; then
      if bash scripts/quickmerge.sh "ci(semver): roll out canonical semver-agent.yml (version-commit + quality-gates-v2 trigger + pm-readiness checkout)" \
           --agent --files ".github/workflows/semver-agent.yml" 2>&1 | tail -3; then
        shipped=$((shipped+1))
      else
        echo "  ! quickmerge failed for $repo — check manually"; failed=$((failed+1))
      fi
    else
      echo "  ! quality-gates.sh failed for $repo (Pass 1) — NOT shipping; check manually"; failed=$((failed+1))
    fi
  else
    # agent_orchestrator path: direct commit+push to its integration branch.
    git add .github/workflows/semver-agent.yml
    if git diff --cached --quiet; then
      echo "  [same] $repo — nothing staged"
    elif git commit -m "ci(semver): roll out canonical semver-agent.yml [skip ci]" --quiet && git push origin HEAD 2>&1 | tail -1; then
      shipped=$((shipped+1))
    else
      echo "  ! commit/push failed for $repo — check manually"; failed=$((failed+1))
    fi
  fi
  popd >/dev/null
done

echo ""
echo "Done: rendered=$updated shipped=$shipped already-current=$skipped failed=$failed"
[ "$failed" -gt 0 ] && exit 1 || exit 0
