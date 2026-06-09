#!/usr/bin/env bash
# ADMIN ONLY: Force-sync all workspace repos — local HEAD overwrites remote main.
#
# What this does per repo (in topological tier order, parallel within each tier):
#   1. git add -A  (stage all local changes — files added, modified, deleted)
#   2. ruff check/format + prettier --write (pre-format before staging to avoid spurious diffs)
#   3. git add -A + git commit --no-verify -m "<message>"  (--no-verify: formatting already done)
#   3. Disable GitHub branch protection + rulesets via API
#   4. git push --force origin HEAD:main  (works from any branch; local wins)
#   5. Restore branch protection + rulesets immediately after push
#
# Identity gate: only the repo admin (IggyIkenna) may run this script.
# Protections are restored even on failure (trap-based cleanup).
#
# SSOT: unified-trading-pm/scripts/repo-management/admin-force-sync-all-to-main.sh
#
# Usage:
#   bash admin-force-sync-all-to-main.sh --admin-confirm [OPTIONS]
#
# Options:
#   --admin-confirm       REQUIRED. Acknowledge this overwrites remote main.
#   --message MSG         Commit message for staged changes (default: "chore: admin force-sync")
#   --dry-run             Show what would run; make no changes.
#   --limit N             Process only the first N repos.
#   --repo NAME           Process only one specific repo.
#   --filter PATTERN      Glob filter on repo name (e.g. unified-*, *-service).
#   --repos "a b c"       Space-separated list of repo names to process.
#   --skip-protection     Skip the GitHub API protect/unprotect cycle.
#   --no-commit           Skip git add / git commit; only force-push current HEAD.
#   --preserve-local      (default) Stage, commit, push — skip switching to main. Stay on current
#   --switch-to-main     After push, switch local branch to main (old behavior)
#                        branch. All changes committed and pushed; nothing lost.
#   --feat-branch         Force-push to the active feature branch read from
#                        workspace-manifest.json (.active_feature_branch). Admin
#                        overrides branch protection on that branch, same as main.
#   --stag-branch         Force-push to the staging branch ("staging"). Admin
#                        overrides branch protection on staging, same as main.
#   --switch-only         Local branch switch ONLY — no commit, no push, no protection changes.
#                        Runs git checkout -B TARGET_BRANCH in every repo. Overrides all sync
#                        behaviour. Incompatible with: --message, --no-commit, --skip-protection,
#                        --switch-to-main, --preserve-local.
#
# Prerequisites:
#   - gh CLI authenticated as IggyIkenna (admin of all target repos).
#   - jq installed.
#
# Run from: workspace root

set -euo pipefail

# ---------------------------------------------------------------------------
# Resolve workspace root
# ---------------------------------------------------------------------------
if [ -f "$(pwd)/unified-trading-pm/workspace-manifest.json" ]; then
  WORKSPACE_ROOT="$(pwd)"
elif [ -f "$(pwd)/workspace-manifest.json" ]; then
  WORKSPACE_ROOT="$(cd .. && pwd)"
else
  echo "ERROR: Run from workspace root. Expected unified-trading-pm/workspace-manifest.json"
  echo "  cd /path/to/unified-trading-system-repos"
  echo "  bash unified-trading-pm/scripts/repo-management/admin-force-sync-all-to-main.sh --admin-confirm"
  exit 1
fi

PM_ROOT="$WORKSPACE_ROOT/unified-trading-pm"
MANIFEST="$PM_ROOT/workspace-manifest.json"

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
ADMIN_CONFIRM=false
DRY_RUN=false
LIMIT=""
REPO_FILTER=""
FILTER_PATTERN=""
REPOS_LIST=""
COMMIT_MSG="chore: admin force-sync"
SKIP_PROTECTION=false
NO_COMMIT=false
SKIP_CHECKOUT=true
MAX_WORKERS=${MAX_WORKERS:-8}
TARGET_BRANCH="main"
SWITCH_ONLY=false
_SO_CONFLICT=""

# ---------------------------------------------------------------------------
# Parse args
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --admin-confirm)   ADMIN_CONFIRM=true; shift ;;
    --dry-run)         DRY_RUN=true; shift ;;
    --limit)           LIMIT="$2"; shift 2 ;;
    --repo)            REPO_FILTER="$2"; shift 2 ;;
    --filter)          FILTER_PATTERN="$2"; shift 2 ;;
    --repos)           REPOS_LIST="$2"; shift 2 ;;
    --message)         _SO_CONFLICT+="${_SO_CONFLICT:+ }--message"; COMMIT_MSG="$2"; shift 2 ;;
    --skip-protection) _SO_CONFLICT+="${_SO_CONFLICT:+ }--skip-protection"; SKIP_PROTECTION=true; shift ;;
    --no-commit)       _SO_CONFLICT+="${_SO_CONFLICT:+ }--no-commit"; NO_COMMIT=true; shift ;;
    --preserve-local)  _SO_CONFLICT+="${_SO_CONFLICT:+ }--preserve-local"; SKIP_CHECKOUT=true; shift ;;
    --switch-to-main)  _SO_CONFLICT+="${_SO_CONFLICT:+ }--switch-to-main"; SKIP_CHECKOUT=false; shift ;;
    --switch-only)     SWITCH_ONLY=true; shift ;;
    --max-workers)     MAX_WORKERS="$2"; shift 2 ;;
    --feat-branch)     TARGET_BRANCH="__feat__"; shift ;;
    --stag-branch)     TARGET_BRANCH="staging"; shift ;;
    --force-version-override) FORCE_VERSION_OVERRIDE=true; shift ;;
    *) echo "Unknown flag: $1"; shift ;;
  esac
done

FORCE_VERSION_OVERRIDE="${FORCE_VERSION_OVERRIDE:-false}"

# ---------------------------------------------------------------------------
# Resolve --feat-branch to actual branch name from manifest
# ---------------------------------------------------------------------------
if [[ "$TARGET_BRANCH" == "__feat__" ]]; then
  _feat=$(jq -r '.active_feature_branch // empty' "$WORKSPACE_ROOT/unified-trading-pm/workspace-manifest.json" 2>/dev/null || true)
  if [[ -z "$_feat" ]]; then
    echo "ERROR: --feat-branch: no active_feature_branch found in workspace-manifest.json"
    exit 1
  fi
  TARGET_BRANCH="$_feat"
fi

# --switch-only conflict check — must come after __feat__ resolution so TARGET_BRANCH is set
if [[ "$SWITCH_ONLY" == "true" && -n "$_SO_CONFLICT" ]]; then
  echo "ERROR: --switch-only cannot be combined with: $_SO_CONFLICT"
  exit 1
fi

# --preserve-local means "don't auto-switch to main after pushing main".
# When targeting a non-main branch (--feat-branch, --stag-branch), always
# checkout to TARGET_BRANCH as a final step so all repos land on that branch.
if [[ "$TARGET_BRANCH" != "main" ]]; then
  SKIP_CHECKOUT=false
fi

# ---------------------------------------------------------------------------
# Safety gate 1: --admin-confirm required (skipped for --switch-only)
# ---------------------------------------------------------------------------
if [[ "$SWITCH_ONLY" != "true" && "$ADMIN_CONFIRM" != "true" ]]; then
  cat <<'EOF'
ADMIN FORCE-SYNC: Overwrites remote main with your local HEAD for every repo.
This CANNOT be undone without reflog recovery on the server side.

  You MUST pass --admin-confirm to proceed.

  bash admin-force-sync-all-to-main.sh --admin-confirm [--dry-run] [--limit N] ...

EOF
  exit 1
fi

# ---------------------------------------------------------------------------
# Safety gate 2: authenticated GitHub user must be IggyIkenna (skipped for --switch-only)
# ---------------------------------------------------------------------------
GH_USER=""
if [[ "$SWITCH_ONLY" != "true" ]]; then
  if ! command -v gh &>/dev/null; then
    echo "ERROR: gh CLI not found. Install gh CLI first."
    exit 1
  fi
  GH_USER=$(gh api user --jq .login 2>/dev/null || echo "")
  if [[ "$GH_USER" != "IggyIkenna" ]]; then
    echo "ERROR: This script may only be run by IggyIkenna (repo admin)."
    echo "       Authenticated as: '${GH_USER:-<unauthenticated>}'"
    exit 1
  fi
fi

# ---------------------------------------------------------------------------
# Safety gate 3: Version drift check (skipped for --switch-only and --feat-branch)
# Blocks force-push to main/staging if remote has version bumps your local doesn't have.
# Override with --force-version-override (loud warning, requires explicit intent).
# ---------------------------------------------------------------------------
if [[ "$SWITCH_ONLY" != "true" && "$DRY_RUN" != "true" && "$TARGET_BRANCH" != "__feat__" ]]; then
  # Only check for main and staging targets — feature branches are free-form
  RESOLVED_TARGET="$TARGET_BRANCH"
  [[ "$RESOLVED_TARGET" == "__feat__" ]] && RESOLVED_TARGET=""

  if [[ "$RESOLVED_TARGET" == "main" || "$RESOLVED_TARGET" == "staging" ]]; then
    echo ""
    echo "━━━ Safety gate 3: Version drift check (target: $RESOLVED_TARGET) ━━━"
    DRIFT_FOUND=false
    DRIFT_REPOS=""

    PYTHON_CHECK="${WORKSPACE_ROOT}/.venv-workspace/bin/python3"
    [ -x "$PYTHON_CHECK" ] || PYTHON_CHECK="python3"

    # Fast manifest-based check: one fetch of PM remote, compare manifests.
    # PM manifest is the SSOT — if someone bumped a version, it's in remote PM's
    # staging_versions or versions. No need to fetch 70 individual repos.
    PM_DIR="$WORKSPACE_ROOT/unified-trading-pm"
    (cd "$PM_DIR" && git fetch origin main --quiet 2>/dev/null) || true
    (cd "$PM_DIR" && git fetch origin staging --quiet 2>/dev/null) || true

    DRIFT_OUTPUT=$("$PYTHON_CHECK" - "$MANIFEST" "$PM_DIR" "$RESOLVED_TARGET" <<'PYEOF'
import json, sys, subprocess
from pathlib import Path

local_manifest_path = sys.argv[1]
pm_dir = Path(sys.argv[2])
target_branch = sys.argv[3]

with open(local_manifest_path) as f:
    local_manifest = json.load(f)

local_versions = local_manifest.get("versions", {})
drifted = []

# Fetch remote PM manifest from main (staging_versions are recorded here by update-repo-version.yml)
for branch in ["main", "staging"]:
    try:
        result = subprocess.run(
            ["git", "-C", str(pm_dir), "show", f"origin/{branch}:workspace-manifest.json"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            continue
        remote_manifest = json.loads(result.stdout)

        # Check versions map (remote main may have promoted versions we don't have locally)
        remote_versions = remote_manifest.get("versions", {})
        for repo, remote_ver in sorted(remote_versions.items()):
            if repo.startswith("_"):
                continue
            local_ver = local_versions.get(repo, "")
            if remote_ver and local_ver and remote_ver != local_ver:
                drifted.append(f"{repo}|local={local_ver}|origin/{branch} versions={remote_ver}")

        # Check staging_versions (bumped on staging, not yet promoted to main)
        remote_staging_versions = remote_manifest.get("staging_versions", {})
        for repo, staging_ver in sorted(remote_staging_versions.items()):
            if repo.startswith("_") or not staging_ver:
                continue
            local_ver = local_versions.get(repo, "")
            if staging_ver and local_ver and staging_ver != local_ver:
                key = f"{repo}|local={local_ver}|origin/{branch} staging_versions={staging_ver}"
                if key not in drifted:
                    drifted.append(key)
    except Exception:
        pass

# Deduplicate (same repo may appear from both branches)
seen = set()
unique = []
for d in drifted:
    repo = d.split("|")[0]
    if repo not in seen:
        seen.add(repo)
        unique.append(d)

if unique:
    print("DRIFT")
    for d in unique:
        print(d)
else:
    print("OK")
PYEOF
    ) || true

    if echo "$DRIFT_OUTPUT" | head -1 | grep -q "DRIFT"; then
      DRIFT_FOUND=true
      echo ""
      echo "  ⚠️  VERSION DRIFT DETECTED — remote has version bumps your local doesn't have!"
      echo "  Force-pushing will REVERT these remote bumps."
      echo ""
      echo "$DRIFT_OUTPUT" | tail -n +2 | while IFS='|' read -r repo local_ver remote_ver; do
        echo "  ❌ $repo: $local_ver → $remote_ver (WOULD BE REVERTED)"
      done
      echo ""
      echo "  Fix options:"
      echo "    1. Pull remote versions: git fetch origin staging && git checkout origin/staging -- pyproject.toml"
      echo "    2. Run version alignment: bash unified-trading-pm/scripts/repo-management/run-version-alignment.sh"
      echo "    3. Override: re-run with --force-version-override (explicitly accept reversion)"
      echo ""

      if [[ "$FORCE_VERSION_OVERRIDE" != "true" ]]; then
        echo "  BLOCKED. Pass --force-version-override to proceed anyway."
        exit 1
      else
        echo "  ⚠️  --force-version-override: proceeding despite version drift (you accepted the risk)"
      fi
    else
      echo "  [OK] No version drift — safe to force-push"
    fi
    echo ""
  fi
fi

# ---------------------------------------------------------------------------
# Prerequisite checks
# ---------------------------------------------------------------------------
if ! command -v jq &>/dev/null; then
  echo "ERROR: jq not found. Install: brew install jq"
  exit 1
fi

if [[ ! -f "$MANIFEST" ]]; then
  echo "ERROR: Missing $MANIFEST"
  exit 1
fi

GH_OWNER=$(jq -r '.github_owner // .owner // empty' "$MANIFEST" 2>/dev/null || true)
if [[ -z "$GH_OWNER" ]]; then
  FIRST_REPO=$(jq -r '.repositories | keys[0]' "$MANIFEST" 2>/dev/null || true)
  if [[ -n "$FIRST_REPO" && -d "$WORKSPACE_ROOT/$FIRST_REPO/.git" ]]; then
    REMOTE_URL=$(cd "$WORKSPACE_ROOT/$FIRST_REPO" && git remote get-url origin 2>/dev/null || true)
    GH_OWNER=$(echo "$REMOTE_URL" | sed -E 's|.*[:/]([^/]+)/[^/]+\.git.*|\1|')
  fi
fi
if [[ -z "$GH_OWNER" && "$SKIP_PROTECTION" == "false" ]]; then
  echo "ERROR: Could not determine GitHub owner. Pass --skip-protection or add 'github_owner' to workspace-manifest.json."
  exit 1
fi

# ---------------------------------------------------------------------------
# Build repo list in topological tier order
# ---------------------------------------------------------------------------
if [[ -n "$REPOS_LIST" ]]; then
  REPOS=($REPOS_LIST)
  USE_TOPO=false
elif [[ -n "$REPO_FILTER" ]]; then
  REPOS=("$REPO_FILTER")
  USE_TOPO=false
else
  USE_TOPO=true
  # Also build flat list for --limit / --filter
  REPOS=($(jq -r '.topologicalOrder.levels[].repos[]' "$MANIFEST" 2>/dev/null || \
           jq -r '.repositories | keys[]' "$MANIFEST" 2>/dev/null))
fi

# Apply glob filter
if [[ -n "$FILTER_PATTERN" ]]; then
  FILTERED=()
  for r in "${REPOS[@]}"; do
    [[ "$r" == $FILTER_PATTERN ]] && FILTERED+=("$r")
  done
  REPOS=("${FILTERED[@]}")
  USE_TOPO=false
fi

[[ -n "$LIMIT" ]] && { REPOS=("${REPOS[@]:0:$LIMIT}"); USE_TOPO=false; }

# ---------------------------------------------------------------------------
# Branch protection helpers (saves + restores exact ruleset JSON)
# ---------------------------------------------------------------------------
PROT_TMPDIR=$(mktemp -d "/tmp/admin_sync_prot_XXXXXX")

_repo_key() { printf '%s' "$1" | tr '/' '_' | tr '-' '_'; }

_disable_protection() {
  local repo="$1"
  local key; key=$(_repo_key "$repo")
  printf '%s' "$repo" > "$PROT_TMPDIR/${key}.repo"
  [[ "$SKIP_PROTECTION" == "true" ]] && return 0

  # Classic branch protection
  local prot_json
  prot_json=$(gh api "repos/$GH_OWNER/$repo/branches/$TARGET_BRANCH/protection" 2>/dev/null || echo "NONE")
  if [[ "$prot_json" != "NONE" ]]; then
    printf '%s\n' "$prot_json" > "$PROT_TMPDIR/${key}.classic.json"
    gh api -X DELETE "repos/$GH_OWNER/$repo/branches/$TARGET_BRANCH/protection" &>/dev/null || true
    sleep 1  # wait for GitHub to propagate the protection removal before force-push
  fi

  # Rulesets — disable every active ruleset, save exact JSON for restore
  local rulesets_json
  rulesets_json=$(gh api "repos/$GH_OWNER/$repo/rulesets" 2>/dev/null || echo "[]")
  printf '%s\n' "$rulesets_json" \
    | jq -r '.[] | select(.enforcement == "active") | .id' 2>/dev/null \
    | while IFS= read -r rid; do
        [[ -z "$rid" ]] && continue
        gh api "repos/$GH_OWNER/$repo/rulesets/$rid" 2>/dev/null \
          > "$PROT_TMPDIR/${key}.ruleset_${rid}.json" || true
        gh api -X PUT "repos/$GH_OWNER/$repo/rulesets/$rid" \
          --field enforcement=disabled &>/dev/null || true
        sleep 1  # wait for ruleset disable to propagate
        printf '%s\n' "$rid" >> "$PROT_TMPDIR/${key}.rulesets"
      done
}

_restore_protection() {
  local repo="$1"
  local key; key=$(_repo_key "$repo")

  # Restore classic branch protection
  local classicfile="$PROT_TMPDIR/${key}.classic.json"
  if [[ -f "$classicfile" ]]; then
    local has_url
    has_url=$(jq -r '.url // empty' "$classicfile" 2>/dev/null || true)
    if [[ -n "$has_url" ]]; then
      local put_body
      put_body=$(jq '{
        required_status_checks: (
          if .required_status_checks then (
            if ((.required_status_checks.checks // []) | length) > 0 then {
              strict: .required_status_checks.strict,
              checks: .required_status_checks.checks
            } else {
              strict: .required_status_checks.strict,
              contexts: (.required_status_checks.contexts // [])
            } end
          ) else null end
        ),
        enforce_admins: (
          if (.enforce_admins | type) == "object" then (.enforce_admins.enabled // false)
          else (.enforce_admins // false) end
        ),
        required_pull_request_reviews: (
          if .required_pull_request_reviews then {
            dismiss_stale_reviews: (.required_pull_request_reviews.dismiss_stale_reviews // false),
            require_code_owner_reviews: (.required_pull_request_reviews.require_code_owner_reviews // false),
            required_approving_review_count: (.required_pull_request_reviews.required_approving_review_count // 0)
          } else null end
        ),
        restrictions: (
          if .restrictions then {
            users: ([.restrictions.users[]?.login] // []),
            teams: ([.restrictions.teams[]?.slug] // []),
            apps:  ([.restrictions.apps[]?.slug]  // [])
          } else null end
        ),
        required_linear_history: (
          if (.required_linear_history | type) == "object" then (.required_linear_history.enabled // false)
          else (.required_linear_history // false) end
        ),
        allow_force_pushes: (
          if (.allow_force_pushes | type) == "object" then (.allow_force_pushes.enabled // false)
          else (.allow_force_pushes // false) end
        ),
        allow_deletions: (
          if (.allow_deletions | type) == "object" then (.allow_deletions.enabled // false)
          else (.allow_deletions // false) end
        )
      }' "$classicfile" 2>/dev/null) || true
      if [[ -n "$put_body" ]]; then
        gh api -X PUT "repos/$GH_OWNER/$repo/branches/$TARGET_BRANCH/protection" \
          --input - <<< "$put_body" &>/dev/null || \
          echo "  WARN: $repo — could not restore classic branch protection"
      fi
    fi
    rm -f "$classicfile"
  fi

  # Re-enable rulesets from saved exact JSON
  local rulesetsfile="$PROT_TMPDIR/${key}.rulesets"
  if [[ -f "$rulesetsfile" ]]; then
    while IFS= read -r rid; do
      [[ -z "$rid" ]] && continue
      local rulesetjson="$PROT_TMPDIR/${key}.ruleset_${rid}.json"
      if [[ -f "$rulesetjson" && -s "$rulesetjson" ]]; then
        local restore_body
        restore_body=$(jq 'del(.id, .source, .source_type, .created_at, .updated_at, .node_id, ._links)
                          | .enforcement = "active"' "$rulesetjson" 2>/dev/null) || true
        if [[ -n "$restore_body" ]]; then
          gh api -X PUT "repos/$GH_OWNER/$repo/rulesets/$rid" \
            --input - <<< "$restore_body" &>/dev/null || \
            echo "  WARN: $repo — could not restore ruleset $rid"
        fi
        rm -f "$rulesetjson"
      else
        gh api -X PUT "repos/$GH_OWNER/$repo/rulesets/$rid" \
          --field enforcement=active &>/dev/null || \
          echo "  WARN: $repo — could not re-enable ruleset $rid"
      fi
    done < "$rulesetsfile"
    rm -f "$rulesetsfile"
  fi

  rm -f "$PROT_TMPDIR/${key}.repo"
}

# Trap: restore all protections if script exits early (Ctrl-C, error, etc.)
_cleanup() {
  for repofile in "$PROT_TMPDIR"/*.repo; do
    [[ -f "$repofile" ]] || continue
    local repo; repo=$(cat "$repofile")
    local key; key=$(_repo_key "$repo")
    if [[ -f "$PROT_TMPDIR/${key}.classic.json" || -f "$PROT_TMPDIR/${key}.rulesets" ]]; then
      echo "  CLEANUP: restoring protection for $repo ..."
      _restore_protection "$repo" || true
    else
      rm -f "$repofile"
    fi
  done
  rm -rf "$PROT_TMPDIR"
}
trap _cleanup EXIT INT TERM

# ---------------------------------------------------------------------------
# Per-repo worker (runs in subshell for parallelism)
# ---------------------------------------------------------------------------
RESULT_DIR="$(mktemp -d)"
trap '_cleanup; rm -rf "$RESULT_DIR"' EXIT INT TERM

sync_repo() {
  local repo="$1"
  local rf="$RESULT_DIR/${repo//\//__}.result"
  local dir="$WORKSPACE_ROOT/$repo"

  if [[ ! -d "$dir" || ! -d "$dir/.git" ]]; then
    echo "  (skip) $repo — not in workspace"
    echo "SKIP:$repo" > "$rf"
    return
  fi

  if [[ "$DRY_RUN" == "true" ]]; then
    echo "  [dry]  $repo"
    echo "OK:$repo" > "$rf"
    return
  fi

  echo -n "  $repo ... "

  # Stage + commit all local changes (works from any branch)
  # Pre-format with ruff + prettier BEFORE git add so colleagues see no spurious formatting diffs.
  # --no-verify on commit: skip pre-commit hooks — formatting is already done; hooks would only
  # leave reformatted files unstaged and cause force-push to use old HEAD.
  if [[ "$NO_COMMIT" == "false" ]]; then
    # 1. Pre-format Python files with ruff (fix + format)
    # Use --extend-exclude (not --exclude) so CLI additions APPEND to pyproject.toml excludes
    # instead of replacing them. This preserves repo-level excludes like typings/, .cursor/, etc.
    if [[ -f "$dir/pyproject.toml" || -f "$dir/ruff.toml" ]]; then
      (cd "$dir" && "$WORKSPACE_ROOT/.venv-workspace/bin/ruff" check . --fix \
        --extend-exclude .venv --extend-exclude .venv-workspace --extend-exclude '*.egg-info' \
        --extend-exclude node_modules --extend-exclude build --extend-exclude dist \
        --extend-exclude typings --extend-exclude .cursor \
        -q >/dev/null 2>&1) || true
      (cd "$dir" && "$WORKSPACE_ROOT/.venv-workspace/bin/ruff" format . \
        --extend-exclude .venv --extend-exclude .venv-workspace --extend-exclude '*.egg-info' \
        --extend-exclude node_modules --extend-exclude build --extend-exclude dist \
        --extend-exclude typings --extend-exclude .cursor \
        -q >/dev/null 2>&1) || true
    fi
    # 2. Pre-format JS/TS/YAML/JSON/MD files with prettier
    # Pin to 3.6.2 — matches the pre-commit additional_dependency pin so IDE/sync/hook all agree.
    # npx 3.8.1 (system) vs hook 3.6.2 produces different output, causing re-touches every run.
    if [[ -f "$dir/package.json" || -f "$dir/.prettierrc" || -f "$dir/.prettierrc.json" || -f "$dir/prettier.config.js" ]]; then
      (cd "$dir" && npx --yes prettier@3.6.2 --write . \
        --ignore-path .gitignore \
        >/dev/null 2>&1) || true
    elif compgen -G "$dir/**/*.{yaml,yml,json,md}" &>/dev/null 2>&1; then
      (cd "$dir" && npx --yes prettier@3.6.2 --write \
        --ignore-path .gitignore \
        "**/*.yaml" "**/*.yml" "**/*.json" "**/*.md" \
        >/dev/null 2>&1) || true
    fi
    # 3. Stage all (now-formatted) changes and commit with --no-verify
    (cd "$dir" && git add -A 2>/dev/null) || true
    if [[ -n "$(cd "$dir" && git status --porcelain 2>/dev/null)" ]]; then
      (cd "$dir" && git commit --no-verify -m "$COMMIT_MSG" 2>/dev/null) || true
      # Second pass: catch any auto-generated files the formatter may have produced
      if [[ -n "$(cd "$dir" && git status --porcelain 2>/dev/null)" ]]; then
        (cd "$dir" && git add -A && git commit --no-verify -m "$COMMIT_MSG (fixup)" 2>/dev/null) || true
      fi
    fi
  fi

  # Disable branch protection
  _disable_protection "$repo"

  # Force-push current HEAD → remote target branch (works from any local branch)
  local push_err; push_err=$(mktemp)
  if (cd "$dir" && git push --force origin HEAD:"$TARGET_BRANCH" 2>"$push_err"); then
    echo "OK"
    echo "OK:$repo" > "$rf"
    # Switch local branch to target after successful push (avoids post-sync branch confusion)
    # Skip when --preserve-local: stay on current branch; changes are committed and pushed
    if [[ "$SKIP_CHECKOUT" != "true" ]]; then
      local current_branch
      current_branch=$(cd "$dir" && git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
      if [[ -n "$current_branch" && "$current_branch" != "$TARGET_BRANCH" ]]; then
        (cd "$dir" && git checkout -B "$TARGET_BRANCH" 2>/dev/null) \
          && echo "    [checkout] $repo — switched local branch to $TARGET_BRANCH" \
          || echo "    [checkout] WARN: could not switch to $TARGET_BRANCH for $repo"
      fi
    fi
  else
    echo "FAIL"
    echo "  --- push error ---"
    cat "$push_err" | sed 's/^/    /'
    echo "  ------------------"
    echo "FAIL:$repo" > "$rf"
  fi
  rm -f "$push_err"

  # Restore branch protection immediately after push
  _restore_protection "$repo"
}


# ---------------------------------------------------------------------------
# --switch-only worker: local git checkout only, no commit / push / protection
# ---------------------------------------------------------------------------
switch_repo() {
  local repo="$1"
  local rf="$RESULT_DIR/${repo//\//__}.result"
  local dir="$WORKSPACE_ROOT/$repo"

  if [[ ! -d "$dir" || ! -d "$dir/.git" ]]; then
    echo "  (skip) $repo — not in workspace"
    echo "SKIP:$repo" > "$rf"
    return
  fi

  if [[ "$DRY_RUN" == "true" ]]; then
    echo "  [dry]  $repo → $TARGET_BRANCH"
    echo "OK:$repo" > "$rf"
    return
  fi

  echo -n "  $repo ... "
  local current_branch
  current_branch=$(cd "$dir" && git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
  if [[ "$current_branch" == "$TARGET_BRANCH" ]]; then
    echo "already on $TARGET_BRANCH"
    echo "OK:$repo" > "$rf"
    return
  fi
  if (cd "$dir" && git checkout -B "$TARGET_BRANCH" 2>/dev/null); then
    echo "→ $TARGET_BRANCH"
    echo "OK:$repo" > "$rf"
  else
    echo "FAIL (could not switch to $TARGET_BRANCH)"
    echo "FAIL:$repo" > "$rf"
  fi
}

export -f sync_repo switch_repo _disable_protection _restore_protection _repo_key
export GH_OWNER WORKSPACE_ROOT DRY_RUN NO_COMMIT SKIP_CHECKOUT COMMIT_MSG SKIP_PROTECTION PROT_TMPDIR RESULT_DIR TARGET_BRANCH SWITCH_ONLY

# ---------------------------------------------------------------------------
# Parallel batch runner
# ---------------------------------------------------------------------------
run_batch() {
  local -a batch=("$@")
  local -a pids=()

  for repo in "${batch[@]}"; do
    while [[ ${#pids[@]} -ge $MAX_WORKERS ]]; do
      wait "${pids[0]}" 2>/dev/null || true
      pids=("${pids[@]:1}")
    done
    if [[ "$SWITCH_ONLY" == "true" ]]; then
      switch_repo "$repo" &
    else
      sync_repo "$repo" &
    fi
    pids+=("$!")
  done

  for pid in "${pids[@]+"${pids[@]}"}"; do
    wait "$pid" 2>/dev/null || true
  done
}

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
echo "============================================================"
if [[ "$SWITCH_ONLY" == "true" ]]; then
  echo " BRANCH SWITCH: switching all repos to $TARGET_BRANCH (local only)"
else
  echo " ADMIN FORCE-SYNC: local HEAD -> remote $TARGET_BRANCH"
fi
echo " User   : ${GH_USER:-$(whoami)}"
echo " Owner  : ${GH_OWNER:-N/A}"
echo " Target : $TARGET_BRANCH"
if [[ "$SWITCH_ONLY" != "true" ]]; then
  echo " Commit : $( [[ "$NO_COMMIT" == "true" ]] && echo "(skipped)" || echo "\"$COMMIT_MSG\"" )"
  echo " Workers: $MAX_WORKERS per tier"
  echo " Protect: $( [[ "$SKIP_PROTECTION" == "true" ]] && echo "skip (--skip-protection)" || echo "via GitHub API (save + restore)" )"
fi
[[ "$DRY_RUN" == "true" ]]    && echo " MODE   : DRY RUN — no changes will be made"
[[ "$SWITCH_ONLY" == "true" ]] && echo " MODE   : SWITCH ONLY — no commit, no push, local checkout only"
echo "============================================================"
echo ""

# ---------------------------------------------------------------------------
# Main: topological tier order, parallel within each tier
# ---------------------------------------------------------------------------
if [[ "$USE_TOPO" == "true" ]]; then
  NUM_LEVELS=$(jq '[.topologicalOrder.levels[].level] | max + 1' "$MANIFEST" 2>/dev/null || echo "0")
  LEVEL_COUNT=$(jq '.topologicalOrder.levels | length' "$MANIFEST" 2>/dev/null || echo "0")

  for level_idx in $(seq 0 $((LEVEL_COUNT - 1))); do
    level_repos=($(jq -r --argjson idx "$level_idx" \
      '.topologicalOrder.levels[$idx].repos[]' "$MANIFEST" 2>/dev/null || true))

    [[ ${#level_repos[@]} -eq 0 ]] && continue

    # Apply glob filter and limit within topo mode
    if [[ -n "$FILTER_PATTERN" ]]; then
      FILTERED_LEVEL=()
      for r in "${level_repos[@]}"; do
        [[ "$r" == $FILTER_PATTERN ]] && FILTERED_LEVEL+=("$r")
      done
      level_repos=("${FILTERED_LEVEL[@]}")
      [[ ${#level_repos[@]} -eq 0 ]] && continue
    fi

    level_num=$((level_idx + 1))
    echo "── Tier $level_num (${#level_repos[@]} repos, max $MAX_WORKERS parallel) ──"
    run_batch "${level_repos[@]}"
    echo ""
  done
else
  echo "── Processing ${#REPOS[@]} repos (max $MAX_WORKERS parallel) ──"
  run_batch "${REPOS[@]}"
  echo ""
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
ok=0; fail=0; skip=0
FAILED_REPOS=()

for rf in "$RESULT_DIR"/*.result; do
  [[ -f "$rf" ]] || continue
  result=$(cat "$rf")
  case "$result" in
    OK:*)   ((ok++)) ;;
    FAIL:*) ((fail++)); FAILED_REPOS+=("${result#FAIL:}") ;;
    SKIP:*) ((skip++)) ;;
  esac
done

echo "============================================================"
echo " Done: $ok OK  |  $fail FAIL  |  $skip skipped"
if [[ $fail -gt 0 ]]; then
  echo " Failed repos:"
  for r in "${FAILED_REPOS[@]}"; do echo "   - $r"; done
  echo "============================================================"
  exit 1
fi

# ---------------------------------------------------------------------------
# Version-coherence gate (2026-06-09 — FIX 2). A force-sync overwrites source with the
# synced branch's content and can REVERT a semver bump — leaving source pyproject.version
# BELOW the manifest value (the UTL-0.4.0 phantom incident: manifest 0.4.0, source reverted
# to 0.3.167, no installable 0.4.0 → fleet dep cascade jam). Assert source==manifest for
# every repo BEFORE declaring success; BLOCK on any split.
# ---------------------------------------------------------------------------
if [[ "$DRY_RUN" != "true" ]]; then
  echo "Verifying version coherence (source pyproject.version == manifest) post-force-sync..."
  COH_PY="${WORKSPACE_ROOT}/.venv-workspace/bin/python3"
  [[ -x "$COH_PY" ]] || COH_PY="python3"
  if ! "$COH_PY" "$PM_ROOT/scripts/cicd/assert_version_coherence.py"; then
    echo "============================================================"
    echo " ❌ VERSION-COHERENCE GATE FAILED — the force-sync reverted a semver bump."
    echo "    Reconcile source pyproject.version FORWARD to the manifest (see table above),"
    echo "    re-run, and do NOT promote until coherent (FIX 2 /"
    echo "    plans/active/staging_clean_start_and_stale_pr_hygiene_2026_06_08.md)."
    echo "============================================================"
    exit 1
  fi
  echo "  ✅ Version coherence OK (source == manifest fleet-wide)."
fi
echo "============================================================"
exit 0
