#!/usr/bin/env bash
# Epic: ci_master
# Lifecycle: permanent
# Delete-when: NA
# Rolls out canonical workflow templates to workspace repos.
#
# Two-tier template structure:
#   1. unified-trading-pm/scripts/workflow-templates/      — GENERIC; copied to every Python service repo
#   2. unified-trading-pm/scripts/workflow-templates-ui/   — UI-ONLY; copied to unified-trading-system-ui ONLY
#
# Target: <repo>/.github/workflows/<template-name>.yml
#
# Generic per-repo workflows (tier 1):
#   - quality-gates-v2.yml.tmpl      (the required CI check, DEP_REPOS substituted)
#
# fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md todo 7 (2026-08-07):
# request-major-bump.yml, major-bump-issue-handler.yml, update-dependency-version.yml,
# semver-agent.yml.tmpl, main-backmerge-to-ldr.yml, staging-backmerge-to-ldr.yml, and
# version-registry-notify.yml were all full-content flat-copy templates this script used to
# propagate -- DELETED from this directory once every fleet repo was converted to a thin
# `uses: unified-trading-ci/...` caller stub (see that plan for the migration + per-repo
# verification). Their canonical source is now `unified-trading-ci/.github/workflows/`,
# edited directly there -- this script no longer has anything to do with them.
# staging-lock-check.yml (todo 11, 2026-08-08): the same conversion, held back from todo 7
# because its `check-staging-lock` job is a literal branch-protection required-status-check
# context on 16 repos -- converting it needed those 16 rulesets' context strings updated
# FIRST (to "check-staging-lock / check-staging-lock", the caller/callee-prefixed form a
# workflow_call caller always reports) plus a real triggered-PR canary before it was safe.
# Both done; DELETED from this directory once all 24 fleet repos were converted.
#
# RETIRED workflows (workspace-qg.yml / python-quality-gates.yml / version-bump.yml) are
# guarded by _is_retired() below — even if a stale template reappears here, it is NEVER
# rolled out (a blanket rollout would otherwise resurrect dead CI fleet-wide). The stale
# `workspace-qg.yml.tmpl` was deleted 2026-06-07 (workspace-qg retired 2026-05-29).
# `tab-mirror-to-ldr.yml` was RETIRED 2026-06-11 (Path-B slots live on LDR — no tab branch
# to mirror; the `*/15` sweep was ~2,400 no-op invocations/day fleet-wide).
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
#   bash rollout-workflow-templates.sh --template quality-gates-v2.yml.tmpl
#   bash rollout-workflow-templates.sh --repo instruments-service --template quality-gates-v2.yml.tmpl
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

# ── Pre-flight: action-pin existence gate ─────────────────────────────────────
# Before fanning a template across the fleet, verify every `uses: owner/repo@ref` pin
# in the templates RESOLVES to a real ref — a phantom floating tag (e.g.
# astral-sh/setup-uv@v8, which is pin-only @v8.2.0) would otherwise break "Set up job"
# in every repo this rolls to (incident 2026-06-10). The gate is network-graceful: it
# no-ops (exit 0) when gh is offline/unauthenticated, so an offline rollout is not blocked.
PIN_GATE="$SCRIPT_DIR/../validation/check-action-pins.py"
if [ -f "$PIN_GATE" ]; then
  echo "Pre-flight: verifying template action pins resolve..."
  if ! python3 "$PIN_GATE" --dir "$TEMPLATE_DIR"; then
    echo "ABORT: a workflow template references an action ref that does not resolve — fix the pin before rollout." >&2
    exit 1
  fi
  if [ -d "$UI_TEMPLATE_DIR" ] && ! python3 "$PIN_GATE" --dir "$UI_TEMPLATE_DIR"; then
    echo "ABORT: a UI workflow template references an action ref that does not resolve — fix the pin before rollout." >&2
    exit 1
  fi
fi

# ── Pre-flight: template-content YAML lint ────────────────────────────────────
# Beyond pin resolution, verify each template still PARSEs as valid YAML after
# the prettier pass the pre-commit hook applies — a bare `{{PLACEHOLDER}}` token
# is deterministically reformatted by prettier into the invalid `{ { PLACEHOLDER } }`
# (a nested flow-mapping key), which GitHub silently refuses to schedule (2026-08-05
# runs-on incident, workflow_template_runs_on_placeholder_prettier_mangled_fleetwide_2026_08_07.md).
# This gate simulates prettier on a scratch copy then yaml.safe_loads the result, so
# a future mangled placeholder fails HERE at rollout time instead of shipping broken
# to every consuming repo. `.tmpl` templates get their known substitution tokens
# replaced with representative values first (unknown `{{...}}` tokens survive and are
# caught). Prettier-unavailable fallback is parse-only (still catches an
# already-mangled committed template) — never blocks an offline rollout, mirroring
# check-action-pins.py's convention.
YAML_GATE="$SCRIPT_DIR/../validation/check-template-yaml.py"
if [ -f "$YAML_GATE" ]; then
  echo "Pre-flight: verifying template content parses as YAML after prettier..."
  if ! python3 "$YAML_GATE" --dir "$TEMPLATE_DIR"; then
    echo "ABORT: a workflow template fails to parse as YAML after prettier — fix the template before rollout." >&2
    exit 1
  fi
  if [ -d "$UI_TEMPLATE_DIR" ] && ! python3 "$YAML_GATE" --dir "$UI_TEMPLATE_DIR"; then
    echo "ABORT: a UI workflow template fails to parse as YAML after prettier — fix the template before rollout." >&2
    exit 1
  fi
fi

# ── RETIRED-workflow guard ────────────────────────────────────────────────────
# A blanket rollout (no --template) iterates EVERY file in the template dir and
# creates-if-missing in every repo. A stale template for a RETIRED workflow would
# therefore RE-CREATE that dead workflow fleet-wide (incident 2026-06-07: a leftover
# `workspace-qg.yml.tmpl` would have recreated the retired `workspace-qg.yml` — retired
# 2026-05-29, superseded by `quality-gates-v2`). Belt-and-suspenders: even if a retired
# template reappears in this dir, never roll it out. The real fix is deleting the stale
# template; this denylist is the guard so the mistake can't silently propagate again.
RETIRED_WORKFLOWS="workspace-qg.yml python-quality-gates.yml quality-gates.yml version-bump.yml tab-mirror-to-ldr.yml"
_is_retired() {
  local name="$1"
  for r in $RETIRED_WORKFLOWS; do [ "$name" = "$r" ] && return 0; done
  return 1
}

# ── Size-sanity write guard (ao_local_mock_server_workflow_truncation_and_e2e_port_
# collision_2026_08_07) ─────────────────────────────────────────────────────────────────────
# This script is the ONLY known code path anywhere in the workspace that writes
# `.github/workflows/*.yml` across multiple repos in one pass. 2026-08-07 incident: 5 of
# the exact templates this script manages (main-backmerge-to-ldr.yml,
# major-bump-issue-handler.yml, request-major-bump.yml, staging-backmerge-to-ldr.yml,
# update-dependency-version.yml) were found truncated to ~13-15% of their real size in 22
# repos simultaneously. ROOT-CAUSED 2026-08-07 (follow-up session): a concurrent
# `git pull --rebase --autostash` from a DIFFERENT process sharing the same checkout (e.g.
# another slot/session's `quickmerge.sh`) can silently discard uncommitted local edits to
# files it never touches itself — empirically reproduced live (see
# `plans/active/issues/ao_local_mock_server_workflow_truncation_and_e2e_port_collision_2026_08_07.md`
# for the full evidence trail). This guard is defense-in-depth regardless of trigger:
# refuses (does not write) when new content would shrink an EXISTING target to under half
# its current size — a legitimate template edit changes a few substituted tokens or adds/
# removes a job, never collapses the file by more than half. A brand-new target (nothing to
# compare against) always writes normally.
_write_target() {
  local content="$1" target="$2" old_bytes new_bytes
  if [ -f "$target" ]; then
    old_bytes=$(wc -c < "$target" | tr -d ' ')
    new_bytes=$(printf '%s' "$content" | wc -c | tr -d ' ')
    if [ "$old_bytes" -gt 0 ] && [ "$new_bytes" -lt $((old_bytes / 2)) ]; then
      echo "  [REFUSED — new content is ${new_bytes}B, existing $target is ${old_bytes}B (>50% shrink); not writing. Investigate before forcing." >&2
      return 1
    fi
  fi
  printf '%s\n' "$content" > "$target"
  return 0
}

# ── Post-rollout main<->live-defi-rollout parity check ────────────────────────
# (rollout-process gap flagged by agent_orchestrator_stale_pm_workflow_ref_blocks_
# promotion_2026_08_06.md todo 4; operator ruling 2026-08-08, NA-corpus blocker
# digest round 5, id=54.)
#
# This script only ever writes into whichever branch happens to be checked out
# locally per repo (see the file header) — it never verifies that a repo's `main`
# and `live-defi-rollout` branches actually carry the SAME content for the
# workflow files it manages. When a shared-CI-repo-extraction/rollout event lands
# a new/moved workflow file on `live-defi-rollout` without that repo's `main`
# picking it up too (main only receives it via the SEPARATE
# `main-backmerge-to-ldr.yml` mechanism, which this script never triggers), the
# gap sits silent until the repo's next LDR->main promotion attempt discovers it
# as a dangling/missing workflow reference.
#
# PARITY_PAIRS is populated during the rollout loops below with every (repo,
# rendered-filename) pair the rollout genuinely targets (i.e. survived the
# missing-.github/workflows-dir and UI-gates-repo skip checks) — including files
# this run left "already current" locally, since main/LDR drift is a fact about
# the REMOTE branches, independent of what this pass just wrote on disk.
PARITY_PAIRS=()

check_main_ldr_parity() {
  local n="${#PARITY_PAIRS[@]}"
  if [ "$n" -eq 0 ]; then
    return 0
  fi
  echo "=== Post-rollout parity check: origin/main vs origin/live-defi-rollout (${n} file(s)) ==="
  local mismatches=0 pair repo tname repo_dir path
  local main_content ldr_content main_rc ldr_rc
  # Group by repo so each repo is fetched exactly once, however many workflow
  # files the rollout touched there.
  local -A fetch_ok=()
  for pair in "${PARITY_PAIRS[@]}"; do
    repo="${pair%%|*}"
    tname="${pair#*|}"
    repo_dir="$WORKSPACE_ROOT/$repo"
    path=".github/workflows/$tname"

    if [ -z "${fetch_ok[$repo]+x}" ]; then
      # Network-graceful (mirrors check-action-pins.py's own convention): a repo
      # whose fetch fails (offline, no network) is WARNED and skipped, never
      # hard-failed, so an offline rollout run is not blocked by this check.
      if git -C "$repo_dir" fetch origin main live-defi-rollout --quiet 2>/dev/null; then
        fetch_ok[$repo]=1
      else
        fetch_ok[$repo]=0
        echo "  [WARN — fetch failed for $repo; skipping parity check for this repo] " >&2
      fi
    fi
    [ "${fetch_ok[$repo]}" = "1" ] || continue

    if main_content=$(git -C "$repo_dir" show "origin/main:$path" 2>/dev/null); then
      main_rc=0
    else
      main_rc=$?
    fi
    if ldr_content=$(git -C "$repo_dir" show "origin/live-defi-rollout:$path" 2>/dev/null); then
      ldr_rc=0
    else
      ldr_rc=$?
    fi

    # Neither branch carries this file yet (e.g. a brand-new template not pushed
    # anywhere) — nothing to compare, not a parity gap.
    if [ "$main_rc" -ne 0 ] && [ "$ldr_rc" -ne 0 ]; then
      continue
    fi
    if [ "$main_rc" -eq 0 ] && [ "$ldr_rc" -eq 0 ] && [ "$main_content" = "$ldr_content" ]; then
      continue
    fi

    mismatches=$((mismatches + 1))
    echo "  [MISMATCH] $repo: $path"
    [ "$main_rc" -ne 0 ] && echo "    main: MISSING"
    [ "$ldr_rc" -ne 0 ] && echo "    live-defi-rollout: MISSING"
    if [ "$main_rc" -eq 0 ] && [ "$ldr_rc" -eq 0 ]; then
      diff <(printf '%s\n' "$main_content") <(printf '%s\n' "$ldr_content") | head -10 | sed 's/^/    /'
    fi
  done
  echo ""
  if [ "$mismatches" -gt 0 ]; then
    echo "PARITY CHECK FAILED: $mismatches file(s) differ between origin/main and origin/live-defi-rollout." >&2
    echo "main-backmerge-to-ldr.yml will not deliver these automatically -- reconcile the drift (usually a direct" >&2
    echo "push or a manual backmerge PR) before the next LDR->main promotion attempt hits it as a dangling ref." >&2
    return 1
  fi
  echo "Parity check: ${n} file(s) across the rollout's target set, 0 mismatches."
  return 0
}

REPOS=$(python3 -c "import json; [print(r) for r in json.load(open('$MANIFEST')).get('repositories',{})]")

# Phase-2 (D13): look up version_source per repo for __VERSION_SOURCE__ substitution.
# Returns "pyproject.toml" (legacy) for all repos not yet flipped; "git-tag" for the canary+fleet.
get_version_source() {
  local repo="$1"
  MANIFEST_PATH="$MANIFEST" python3 -c "
import json, os
m = json.load(open(os.environ['MANIFEST_PATH']))
repos = m.get('repositories', {})
print(repos.get('$repo', {}).get('version_source', 'pyproject.toml'))
" 2>/dev/null || echo "pyproject.toml"
}

# Branch that triggers push: CI for this repo ({{CI_TRIGGER_BRANCH}} placeholder).
# Default "main" for all ldr_main repos — no change to any existing rendered file.
# Set to "live-defi-rollout" for ldr_terminal repos (manifest field `ci_trigger_branch`)
# so their quality-gates-v2 gate fires on LDR pushes instead of a main-promotion PR
# that no longer exists for those repos.
get_ci_trigger_branch() {
  local repo="$1"
  MANIFEST_PATH="$MANIFEST" python3 -c "
import json, os
m = json.load(open(os.environ['MANIFEST_PATH']))
repos = m.get('repositories', {})
print(repos.get('$repo', {}).get('ci_trigger_branch', 'main'))
" 2>/dev/null || echo "main"
}

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

# Extra dep_repos NOT expressible via the pyproject `path = "../<repo>"` editable-deps closure
# get_dep_repos() walks above. That closure can only ever contain repos that are genuine `uv
# sync`-installed packages of the caller; it has no way to express "clone this sibling on disk
# too, but never install it" — the exact shape needed when a repo loads another repo's files by
# raw file path (importlib.util.spec_from_file_location) rather than importing it as a package.
# SOURCE OF TRUTH = extra-dep-repos.txt (`<repo>: <space-separated extra repo names>`, one repo
# per line, # comments ignored) — a short, explicit, git-tracked override, mirroring the
# self-hosted-qg-repos.txt allowlist pattern just below.
get_extra_dep_repos() {
  local repo="$1" overrides="$SCRIPT_DIR/extra-dep-repos.txt"
  [ -f "$overrides" ] || return 0
  local line rest
  while IFS= read -r line || [ -n "$line" ]; do
    line="${line%%#*}"
    case "$line" in
      "$repo":*) rest="${line#*:}"; printf '%s ' "$rest" ;;
    esac
  done < "$overrides"
}

# Whether `repo` gets quality-gates-v2's real test/lint job on self-hosted runners.
# SOURCE OF TRUTH = self-hosted-qg-repos.txt (one repo name per line, # comments ignored) — a
# short, explicit, git-tracked allowlist rather than a derived rule, since this is a deliberate
# per-repo infra decision (a self-hosted runner pool must already exist + be verified healthy for
# that repo BEFORE it's added here; adding a repo with no pool hangs its promotion gate forever).
# github_actions_operator_gated_followups_2026_07_17.md.
get_qg_runner_labels() {
  local repo="$1" allowlist="$SCRIPT_DIR/self-hosted-qg-repos.txt"
  if [ -f "$allowlist" ] && grep -qxF "$repo" "$allowlist" 2>/dev/null; then
    printf '["self-hosted","glue"]'
  else
    printf ''
  fi
}

# Direct `runs-on:` value for the 8 templates that hardcode the glue pool inline (not via a
# reusable-workflow `self_hosted_runner_labels` input like quality-gates-v2/semver-agent's OWN
# job list before this fix) — main-backmerge-to-ldr.yml, major-bump-issue-handler.yml,
# request-major-bump.yml, staging-backmerge-to-ldr.yml, staging-lock-check.yml,
# update-dependency-version.yml, version-registry-notify.yml, and semver-agent.yml.tmpl's own
# `semver:` job. Added 2026-08-05 (self_hosted_runner_public_repo_revert_2026_08_05.md):
# these were unconditionally `[self-hosted, glue]` for EVERY repo regardless of visibility —
# 17 of the ~23 repos on self-hosted-qg-repos.txt turned out to be PUBLIC GitHub repos, where
# GitHub Actions on GitHub-hosted runners is unmetered. Same allowlist as
# get_qg_runner_labels() (a repo's self-hosted-vs-not decision is ONE fact, not one per
# workflow file) — differs only in the empty-case fallback, since these substitute directly
# into `runs-on:` and need a valid YAML value, not a JSON-string input meant for a callee's own
# `|| '["ubuntu-latest"]'` fallback.
get_runs_on_value() {
  local repo="$1" allowlist="$SCRIPT_DIR/self-hosted-qg-repos.txt"
  if [ -f "$allowlist" ] && grep -qxF "$repo" "$allowlist" 2>/dev/null; then
    printf '[self-hosted, glue]'
  else
    printf 'ubuntu-latest'
  fi
}

updated=0
skipped=0
missing_dir=0
refused=0

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

    # Skip UI repos whose quality-gates-v2.yml already calls ui-quality-gates-v2.yml.
    # The Python fleet template would overwrite their UI-specific gate with the bare
    # Python template, clobbering the ui-quality-gates-v2.yml call (incident 2026-06-27:
    # UTS-UI bf378ac8 + deployment-ui d2d74af5 required 3 worker dispatches to restore).
    if [ "$tname" = "quality-gates-v2.yml" ] && [ -f "$target" ] && \
       grep -q "ui-quality-gates-v2.yml" "$target" 2>/dev/null; then
      skipped=$((skipped + 1))
      echo "  [skipped — UI-gates repo; quality-gates-v2.yml already calls ui-quality-gates-v2.yml] $repo"
      continue
    fi

    # Track (repo, file) for the post-rollout main<->live-defi-rollout parity
    # check — every repo this template genuinely targets, regardless of whether
    # this run's local write changes anything (see check_main_ldr_parity above).
    PARITY_PAIRS+=("$repo|$tname")

    # For .tmpl files: perform substitution; for .yml files: direct copy
    if [ "$is_tmpl" = true ]; then
      dep_repos=$(get_dep_repos "$repo")
      extra_dep_repos=$(get_extra_dep_repos "$repo")
      if [ -n "$extra_dep_repos" ]; then
        # Union + de-dupe, preserving order (pyproject closure first, then extras) — a repo can
        # legitimately appear in both (already-transitive) without being cloned twice.
        dep_repos=$(printf '%s\n' $dep_repos $extra_dep_repos | awk 'NF && !seen[$0]++' | tr '\n' ' ' | sed 's/ *$//')
      fi
      repo_underscore="${repo//-/_}"
      version_source=$(get_version_source "$repo")
      ci_trigger_branch=$(get_ci_trigger_branch "$repo")
      qg_runner_labels=$(get_qg_runner_labels "$repo")
      runs_on_value=$(get_runs_on_value "$repo")
      rendered=$(sed -e "s/{{DEP_REPOS}}/${dep_repos}/g" \
                     -e "s/__REPO_NAME__/${repo}/g" \
                     -e "s/__SOURCE_DIR__/${repo_underscore}/g" \
                     -e "s/__VERSION_SOURCE__/${version_source}/g" \
                     -e "s/{{CI_TRIGGER_BRANCH}}/${ci_trigger_branch}/g" \
                     -e "s#{{QG_RUNNER_LABELS}}#${qg_runner_labels}#g" \
                     -e "s#__RUNS_ON__#${runs_on_value}#g" \
                     "$template")
      # Skip if target already matches rendered output
      if [ -f "$target" ] && [ "$(cat "$target")" = "$rendered" ]; then
        skipped=$((skipped + 1))
        continue
      fi
      if [ "$DRY_RUN" = true ]; then
        echo "  [dry-$([ -f "$target" ] && echo update || echo create)-tmpl] $repo (dep_repos=${dep_repos})"
      else
        _existed=false; [ -f "$target" ] && _existed=true
        if _write_target "$rendered" "$target"; then
          echo "  [$([ "$_existed" = true ] && echo updated || echo created)-tmpl] $repo (dep_repos=${dep_repos})"
        else
          refused=$((refused + 1))
          continue
        fi
      fi
    else
      # "Flat copy" templates still get the __RUNS_ON__ substitution (2026-08-05,
      # get_runs_on_value() above) — a no-op sed pass for any template that doesn't contain
      # the placeholder, so this stays byte-identical to a real `cp` for those. Compare
      # rendered content (not `diff` against the raw template) so the skip-if-unchanged check
      # is still correct for templates that DO substitute.
      #
      # __RUNS_ON__ (double-underscore, matching __REPO_NAME__/__SOURCE_DIR__), NOT
      # {{RUNS_ON}} (2026-08-07 fix, cicd escalation agt-62ba62): prettier's YAML formatter
      # deterministically reformats a bare `{{RUNS_ON}}` flow-mapping-lookalike into the
      # broken `{ { RUNS_ON } }` (verified: nested flow-mapping used as an unhashable key —
      # invalid YAML, GitHub silently stops scheduling the workflow) — and this repo's
      # prettier-autostage pre-commit hook re-applies that mangling on every commit, so the
      # `{{...}}` form can never survive a commit here. A bare `__RUNS_ON__` token is a plain
      # YAML scalar prettier does not touch.
      runs_on_value=$(get_runs_on_value "$repo")
      rendered=$(sed -e "s#__RUNS_ON__#${runs_on_value}#g" "$template")
      if [ -f "$target" ] && [ "$(cat "$target")" = "$rendered" ]; then
        skipped=$((skipped + 1))
        continue
      fi
      if [ "$DRY_RUN" = true ]; then
        echo "  [dry-$([ -f "$target" ] && echo update || echo create)] $repo"
      else
        _existed=false; [ -f "$target" ] && _existed=true
        if _write_target "$rendered" "$target"; then
          echo "  [$([ "$_existed" = true ] && echo updated || echo created)] $repo"
        else
          refused=$((refused + 1))
          continue
        fi
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
      PARITY_PAIRS+=("$UI_TARGET_REPO|$tname")
      target="$ui_target_dir/$tname"
      if [ -f "$target" ] && diff -q "$template" "$target" > /dev/null 2>&1; then
        skipped=$((skipped + 1))
        echo "  [skipped — already current] $UI_TARGET_REPO"
        continue
      fi
      if [ "$DRY_RUN" = true ]; then
        echo "  [dry-$([ -f "$target" ] && echo update || echo create)] $UI_TARGET_REPO"
      else
        _existed=false; [ -f "$target" ] && _existed=true
        if ! _write_target "$(cat "$template")" "$target"; then
          refused=$((refused + 1))
          continue
        fi
        echo "  [$([ "$_existed" = true ] && echo updated || echo created)] $UI_TARGET_REPO"
      fi
      updated=$((updated + 1))
    done
  fi
fi

echo "Summary:"
echo "  Updated/created: $updated"
echo "  Already current: $skipped"
echo "  No .github/workflows/: $missing_dir"
echo "  Refused (would shrink an existing file >50%): $refused"
if [ "$DRY_RUN" = true ]; then
  echo "  (dry-run mode -- no files were modified)"
fi
echo ""

parity_failed=false
if ! check_main_ldr_parity; then
  parity_failed=true
fi

if [ "$refused" -gt 0 ]; then
  echo "REFUSED $refused write(s) -- see [REFUSED -- ...] lines above. Investigate before re-running (a legitimate" >&2
  echo "template change never shrinks a file by more than half; this is the size-sanity guard added after the" >&2
  echo "2026-08-07 workflow-truncation incident)." >&2
fi

if [ "$refused" -gt 0 ] || [ "$parity_failed" = true ]; then
  exit 1
fi
