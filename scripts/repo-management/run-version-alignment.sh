#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# run-version-alignment.sh — Check and optionally fix dependency alignment
#
# Run BEFORE run-all-setup.sh. Ensures pyproject.toml, workspace-manifest.json,
# and workspace-constraints.toml are aligned. If conflicts exist, fix them first.
#
# Usage:
#   bash unified-trading-pm/scripts/repo-management/run-version-alignment.sh         # check only
#   bash unified-trading-pm/scripts/repo-management/run-version-alignment.sh --fix   # apply fixes
#
# Workflow (from scripts/manifest/README-DEPENDENCY-ALIGNMENT.md):
#   1. generate-derived-manifest.py   → derived from pyproject.toml
#   2. generate_canonical_dependency_manifest.py → canonical from workspace-constraints.toml
#   3. check-dependency-alignment.py → compare derived vs manifest + canonical
#   3.5. validate-uv-sources.py → every internal dep has [tool.uv.sources.*] editable = true
#   3.6. validate-internal-editable.py → internal deps must be editable, not from Artifact Registry
#   4. validate-dependency-conflicts.py → verify constraints resolve (uv pip compile)
#   5. fix-internal-dependency-alignment.py --apply (if internal misalignment)
#   6. fix_external_dependency_alignment.py --apply (if external misalignment)

set -euo pipefail

APPLY_FIXES=false
STRICT=false
UI_ONLY=false
for arg in "$@"; do
  case $arg in
    --fix) APPLY_FIXES=true ;;
    --strict) STRICT=true ;;
    --ui-only) UI_ONLY=true ;;  # Skip Python alignment steps; run only 0.5+0.6 (symlinks + UI dep drift)
    --help | -h)
      echo "Usage: bash run-version-alignment.sh [--fix] [--strict] [--ui-only]"
      echo "  --fix      Apply fixes (internal + external alignment)"
      echo "  --strict   Treat broken symlinks / UI dep drift as a fatal error (default: warn)"
      echo "  --ui-only  Run only pre-checks (0.5 symlinks + 0.6 UI dep drift); skip Python alignment"
      exit 0
      ;;
  esac
done

# Resolve workspace root from cwd (must run from workspace root)
if [ -f "$(pwd)/unified-trading-pm/workspace-manifest.json" ]; then
  WORKSPACE_ROOT="$(pwd)"
elif [ -f "$(pwd)/workspace-manifest.json" ]; then
  WORKSPACE_ROOT="$(cd .. && pwd)"
else
  echo "Error: Run from workspace root. Expected unified-trading-pm/workspace-manifest.json"
  echo "  cd /path/to/unified-trading-system-repos"
  echo "  bash unified-trading-pm/scripts/repo-management/run-version-alignment.sh"
  exit 1
fi
PM_ROOT="$WORKSPACE_ROOT/unified-trading-pm"
export WORKSPACE_ROOT
cd "$PM_ROOT"

# Use workspace venv Python (has tomli_w and all manifest tools installed).
# Falls back to system python3.13 if venv not found.
VENV_PYTHON="$WORKSPACE_ROOT/.venv-workspace/bin/python3.13"
if [ -x "$VENV_PYTHON" ]; then
  PYTHON="$VENV_PYTHON"
else
  PYTHON="python3.13"
fi

echo "━━━ Version alignment ━━━"
echo ""
echo "Checks performed (dry run = report only; --fix = apply auto-fixes):"
echo "  [0]     Tracked-but-gitignored audit          — informational only"
echo "  [0.5]   Broken symlinks                       — manual: rm <path> && ln -sf <target> <path>"
echo "  [0.55]  Agent symlinks (check-import-patterns) — auto-fix with --fix"
echo "  [0.6]   UI npm dep drift (pkg.json vs lock)   — manual: cd <repo> && npm install"
echo "  [0.7]   Canonical npm version alignment       — auto-fix with --fix"
echo "  [0.8]   uv.lock drift (pyproject newer / uncommitted changes) — warn or --strict fatal"
echo "  [0.9]   Dependency caps (repos pinned to old dep versions) — informational"
echo "  [1–2]   Derived + canonical manifests         — generated (prerequisite)"
echo "  [3]     Dependency alignment (internal+external)— auto-fix with --fix"
echo "  [3.5]   [tool.uv.sources] editable entries   — auto-fix with --fix"
echo "  [3.6]   Internal deps editable (not registry) — manual: uv sync in each repo"
echo "  [3.7]   Import-vs-deps audit (direct imports need dep + source) — auto-fix with --fix"
echo "  [4]     Constraint resolution (uv pip compile)— manual: validate-dependency-conflicts.py --regenerate"
echo ""
echo "Downstream CI (not run here; alignment must pass first):"
echo "  • Cloud Build (GCP): library pre-checks, Docker builds — add-cloudbuild-prechecks.py"
echo "  • Code Build (AWS): UI buildspec.aws.yaml — rollout-ui-build-infra.py"
echo "  Run: bash run-all-setup.sh --rollout-first  to propagate build infra."
echo ""

# 0. Audit tracked-but-gitignored files (informational; never blocks)
echo "[0/4] Auditing tracked files matched by .gitignore..."
bash "$PM_ROOT/scripts/audit_tracked_ignored.sh" 2>/dev/null || true
echo ""

# 0.5. Broken symlink check across all repos in workspace
echo "[0.5/4] Checking for broken symlinks across all workspace repos..."
BROKEN_SYMLINKS=()
while IFS= read -r -d '' link; do
  target=$(readlink "$link")
  if [ ! -e "$link" ]; then
    BROKEN_SYMLINKS+=("  $link -> $target")
  fi
done < <(find "$WORKSPACE_ROOT" \
  -not \( -path "*/.venv*" -prune \) \
  -not \( -path "*/.git*" -prune \) \
  -not \( -path "*/node_modules*" -prune \) \
  -not \( -path "*/build*" -prune \) \
  -not \( -path "*/archive*" -prune \) \
  -not \( -path "*/_archived*" -prune \) \
  -type l -print0 2>/dev/null)

if [ "${#BROKEN_SYMLINKS[@]}" -gt 0 ]; then
  echo ""
  echo "  [WARN] Broken symlinks found (${#BROKEN_SYMLINKS[@]}):"
  for s in "${BROKEN_SYMLINKS[@]}"; do echo "$s"; done
  echo ""
  echo "  To fix: rm <path> and re-target with: ln -sf <new-target> <path>"
  echo "  Pass --strict to treat broken symlinks as a fatal error."
  if [ "${STRICT:-false}" = true ]; then
    exit 1
  fi
else
  echo "  [OK] No broken symlinks"
fi
echo ""

# 0.55. Required symlink presence check — verify .cursor/scripts/check-import-patterns.py
#        exists (as a symlink, not a local copy) in all Python manifest repos
echo "[0.55/4] Checking .cursor/scripts/check-import-patterns.py symlinks in Python repos..."
MISSING_SYMLINKS=()
STALE_COPIES=()
# Only check manifest repos (not arbitrary on-disk dirs) — matches rollout-agent-symlinks.sh scope
_manifest_python_repos=$(python3 - "$PM_ROOT/workspace-manifest.json" "$WORKSPACE_ROOT" <<'PYEOF'
import json, sys, os
with open(sys.argv[1]) as f:
    manifest = json.load(f)
workspace = sys.argv[2]
repos = manifest.get("repositories", {})
for name, _ in repos.items():
    if name == "unified-trading-pm":
        continue
    repo_dir = os.path.join(workspace, name)
    if os.path.isfile(os.path.join(repo_dir, "pyproject.toml")):
        print(name)
PYEOF
)
while IFS= read -r repo_name; do
    [ -z "$repo_name" ] && continue
    repo_dir="$WORKSPACE_ROOT/$repo_name"
    script_path="$repo_dir/.cursor/scripts/check-import-patterns.py"
    if [ -L "$script_path" ]; then
        : # correct — symlink exists
    elif [ -f "$script_path" ]; then
        STALE_COPIES+=("  $repo_name: local copy (not symlink) — run rollout-agent-symlinks.sh")
    else
        MISSING_SYMLINKS+=("  $repo_name: missing — run rollout-agent-symlinks.sh")
    fi
done <<< "$_manifest_python_repos"

if [ "${#MISSING_SYMLINKS[@]}" -gt 0 ] || [ "${#STALE_COPIES[@]}" -gt 0 ]; then
    [ "${#MISSING_SYMLINKS[@]}" -gt 0 ] && echo "  [WARN] Missing check-import-patterns.py symlinks (${#MISSING_SYMLINKS[@]}):" && \
        for s in "${MISSING_SYMLINKS[@]}"; do echo "$s"; done
    [ "${#STALE_COPIES[@]}" -gt 0 ] && echo "  [WARN] Stale local copies (should be symlinks) (${#STALE_COPIES[@]}):" && \
        for s in "${STALE_COPIES[@]}"; do echo "$s"; done
    if [ "$APPLY_FIXES" = true ]; then
        echo "  Applying fix: running rollout-agent-symlinks.sh..."
        bash "$PM_ROOT/scripts/rollout-agent-symlinks.sh" 2>&1 || true
    else
        echo "  Fix: bash unified-trading-pm/scripts/rollout-agent-symlinks.sh"
        if [ "${STRICT:-false}" = true ]; then
            exit 1
        fi
    fi
else
    echo "  [OK] All Python repos have check-import-patterns.py symlinks"
fi
echo ""

# 0.6. UI dep-drift check — detect UI repos where package.json is newer than package-lock.json
#      (means npm install hasn't been run since package.json was last edited).
echo "[0.6/4] Checking UI repos for npm dep drift (package.json newer than package-lock.json)..."
UI_DRIFT=()
while IFS= read -r pkg_json; do
  repo_dir="$(dirname "$pkg_json")"
  lock_file="$repo_dir/package-lock.json"
  # Only check pure UI repos (no pyproject.toml, not workspace root)
  [ "$repo_dir" = "$WORKSPACE_ROOT" ] && continue
  [ -f "$repo_dir/pyproject.toml" ] && continue
  if [ ! -f "$lock_file" ]; then
    UI_DRIFT+=("  $(basename "$repo_dir"): no package-lock.json — run: cd $(basename "$repo_dir") && npm install")
  elif [ "$pkg_json" -nt "$lock_file" ]; then
    UI_DRIFT+=("  $(basename "$repo_dir"): package.json newer than package-lock.json — run: cd $(basename "$repo_dir") && npm install")
  fi
done < <(find "$WORKSPACE_ROOT" -maxdepth 2 -name "package.json" \
  -not \( -path "*/node_modules/*" -prune \) \
  -not \( -path "*/.venv*" -prune \) \
  -not \( -path "*/unified-trading-pm/*" -prune \) \
  -not \( -path "*/archive/*" -prune \) \
  -not \( -path "*/_archived*" -prune \) 2>/dev/null)

if [ "${#UI_DRIFT[@]}" -gt 0 ]; then
  echo ""
  echo "  [WARN] UI repos with stale node_modules (${#UI_DRIFT[@]}):"
  for d in "${UI_DRIFT[@]}"; do echo "$d"; done
  echo ""
  echo "  Fix: cd <repo> && npm install   OR   bash unified-trading-pm/scripts/repo-management/run-all-setup.sh --rollout-first"
  if [ "${STRICT:-false}" = true ]; then
    exit 1
  fi
else
  echo "  [OK] All UI repos have up-to-date package-lock.json"
fi
echo ""

# 0.7. Canonical npm version check — enforce workspace-npm-constraints.json across UI repos
echo "[0.7/4] Checking UI repos for npm version alignment (canonical constraints)..."
if [ "$APPLY_FIXES" = true ]; then
  if ! "$PYTHON" scripts/propagation/rollout-npm-versions.py --apply 2>&1; then
    echo "  [WARN] npm version update failed (non-fatal) — check output above"
  fi
else
  if ! "$PYTHON" scripts/propagation/rollout-npm-versions.py 2>&1; then
    echo ""
    echo "  Fix: python3 unified-trading-pm/scripts/propagation/rollout-npm-versions.py --apply"
    echo "  Or:  bash unified-trading-pm/scripts/repo-management/run-version-alignment.sh --fix"
    if [ "${STRICT:-false}" = true ]; then
      exit 1
    fi
  fi
fi
echo ""

# 0.8. uv.lock drift detection — stale lockfile (pyproject.toml newer) or uncommitted changes
# Branch context: reads active_feature_branch from workspace-manifest.json (default comparison target).
# Each drift message includes the repo's current branch so you know whether drift is expected
# (e.g. on a feature branch with in-progress dep changes) vs unexpected (stale on main).
echo "[0.8/4] Checking uv.lock staleness and uncommitted changes across all repos..."
ACTIVE_BRANCH="$(python3 -c "
import json, sys
try:
    m = json.load(open('$PM_ROOT/workspace-manifest.json'))
    print(m.get('active_feature_branch', 'main'))
except Exception:
    print('main')
" 2>/dev/null || echo "main")"
LOCK_DRIFT=()
while IFS= read -r lock_file; do
  repo_dir="$(dirname "$lock_file")"
  repo_name="$(basename "$repo_dir")"
  [ "$repo_dir" = "$WORKSPACE_ROOT" ] && continue
  pyproject="$repo_dir/pyproject.toml"
  repo_branch="$(git -C "$repo_dir" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")"
  branch_tag="branch: $repo_branch"
  # uv lock --check: exit 1 means lock is out of sync with pyproject.toml
  # Prefer this over timestamp comparison (-nt) which gives false positives when
  # pyproject.toml is edited but uv lock produces no content changes.
  if [ -f "$pyproject" ] && ! (cd "$repo_dir" && uv lock --check 2>/dev/null); then
    LOCK_DRIFT+=("  $repo_name: uv.lock out of sync with pyproject.toml ($branch_tag) — run: cd $repo_name && uv lock")
  fi
  # uncommitted changes to uv.lock on the working tree
  if git -C "$repo_dir" status --porcelain uv.lock 2>/dev/null | grep -q 'uv\.lock'; then
    LOCK_DRIFT+=("  $repo_name: uv.lock has uncommitted local changes ($branch_tag)")
  fi
done < <(find "$WORKSPACE_ROOT" -maxdepth 2 -name "uv.lock" \
  -not \( -path "*/.venv*" -prune \) \
  -not \( -path "*/unified-trading-pm/*" -prune \) \
  -not \( -path "*/archive/*" -prune \) \
  -not \( -path "*/_archived*" -prune \) 2>/dev/null)

if [ "${#LOCK_DRIFT[@]}" -gt 0 ]; then
  echo ""
  echo "  [WARN] uv.lock drift detected (${#LOCK_DRIFT[@]} issue(s)) — active_feature_branch=${ACTIVE_BRANCH}:"
  for d in "${LOCK_DRIFT[@]}"; do echo "$d"; done
  echo ""
  echo "  Fix: cd <repo> && uv lock   (regenerate from pyproject.toml)"
  echo "  Pass --strict to treat uv.lock drift as a fatal error."
  if [ "${STRICT:-false}" = true ]; then
    exit 1
  fi
else
  echo "  [OK] All uv.lock files are up to date"
fi
echo ""

# --ui-only: pre-checks complete — skip Python alignment steps
if [ "$UI_ONLY" = true ]; then
  echo "  --ui-only: skipping Python alignment steps (1–4)."
  echo ""
  echo "  Next: bash unified-trading-pm/scripts/repo-management/run-all-setup.sh  (to reinstall stale UI deps)"
  exit 0
fi

# 0.9. Dependency cap check — repos with dependency_caps entries are pinned to old versions
echo "[0.9/4] Checking for repos with active dependency version caps..."
CAPPED_REPOS=$("$PYTHON" - "$PM_ROOT/workspace-manifest.json" <<'PYEOF'
import json, sys
with open(sys.argv[1]) as f:
    manifest = json.load(f)
repos = manifest.get("repositories", {})
found = False
for name, data in sorted(repos.items()):
    caps = data.get("dependency_caps", {})
    if caps:
        for dep, cap in caps.items():
            print(f"  {name}: {dep} capped at {cap} — pinned to old version, update needed")
        found = True
if not found:
    print("  [OK] No dependency caps active")
PYEOF
)
echo "$CAPPED_REPOS"
echo ""

# 0.95. Self-version parity — pyproject.toml version must match manifest versions[repo]
echo "[0.95/4] Checking pyproject.toml vs manifest version parity..."
SELF_VERSION_DRIFT=$("$PYTHON" - "$PM_ROOT/workspace-manifest.json" "$WORKSPACE_ROOT" <<'PYEOF'
import json, sys, re
from pathlib import Path

manifest_path = sys.argv[1]
workspace = Path(sys.argv[2])

with open(manifest_path) as f:
    manifest = json.load(f)

versions = manifest.get("versions", {})
repos = manifest.get("repositories", {})
drifted = []

for repo_name in sorted(repos):
    if repo_name.startswith("_"):
        continue
    manifest_ver = versions.get(repo_name, "")
    if not manifest_ver or manifest_ver.startswith("_"):
        continue

    # Find pyproject.toml version
    pyproject = workspace / repo_name / "pyproject.toml"
    if not pyproject.is_file():
        # Try package.json for UI repos
        pkg_json = workspace / repo_name / "package.json"
        if pkg_json.is_file():
            try:
                pkg = json.loads(pkg_json.read_text())
                local_ver = pkg.get("version", "")
            except Exception:
                continue
        else:
            continue
    else:
        content = pyproject.read_text()
        m = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
        local_ver = m.group(1) if m else ""

    if local_ver and local_ver != manifest_ver:
        drifted.append(f"  {repo_name}: pyproject={local_ver} manifest={manifest_ver}")

if drifted:
    print(f"  [WARN] Self-version drift ({len(drifted)} repo(s)):")
    for d in drifted:
        print(d)
    print()
    print("  Fix: update versions[repo] in workspace-manifest.json to match pyproject.toml")
    print("  Or:  bash run-version-alignment.sh --fix  (auto-syncs manifest from pyproject.toml)")
else:
    print("  [OK] All repo versions match manifest")
PYEOF
)
echo "$SELF_VERSION_DRIFT"
if echo "$SELF_VERSION_DRIFT" | grep -q "\[WARN\]"; then
  SELF_VERSION_HAS_DRIFT=true
  if [ "$APPLY_FIXES" = true ]; then
    echo "  Applying --fix: syncing manifest versions from pyproject.toml..."
    "$PYTHON" - "$PM_ROOT/workspace-manifest.json" "$WORKSPACE_ROOT" <<'PYEOF'
import json, sys, re
from pathlib import Path

manifest_path = sys.argv[1]
workspace = Path(sys.argv[2])

with open(manifest_path) as f:
    manifest = json.load(f)

versions = manifest.get("versions", {})
repos = manifest.get("repositories", {})
fixed = 0

for repo_name in sorted(repos):
    if repo_name.startswith("_"):
        continue
    manifest_ver = versions.get(repo_name, "")
    if not manifest_ver or manifest_ver.startswith("_"):
        continue

    pyproject = workspace / repo_name / "pyproject.toml"
    if pyproject.is_file():
        content = pyproject.read_text()
        m = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
        local_ver = m.group(1) if m else ""
    else:
        pkg_json = workspace / repo_name / "package.json"
        if pkg_json.is_file():
            try:
                local_ver = json.loads(pkg_json.read_text()).get("version", "")
            except Exception:
                continue
        else:
            continue

    if local_ver and local_ver != manifest_ver:
        versions[repo_name] = local_ver
        if "version" in repos[repo_name]:
            repos[repo_name]["version"] = local_ver
        print(f"  Fixed: {repo_name} {manifest_ver} → {local_ver}")
        fixed += 1

with open(manifest_path, "w") as f:
    json.dump(manifest, f, indent=2)
    f.write("\n")
print(f"  {fixed} version(s) synced to manifest")
PYEOF
  fi
else
  SELF_VERSION_HAS_DRIFT=false
fi
echo ""

# 0.96. Remote version drift — compare local PM manifest against remote PM manifest (fast, one fetch)
echo "[0.96/4] Checking remote PM manifest for version drift..."
(cd "$PM_ROOT" && git fetch origin main --quiet 2>/dev/null) || :
(cd "$PM_ROOT" && git fetch origin staging --quiet 2>/dev/null) || :
REMOTE_DRIFT=$("$PYTHON" - "$PM_ROOT" "$PM_ROOT/workspace-manifest.json" <<'PYEOF'
import json, sys, subprocess
from pathlib import Path

pm_dir = Path(sys.argv[1])
local_manifest_path = sys.argv[2]

with open(local_manifest_path) as f:
    local_manifest = json.load(f)

local_versions = local_manifest.get("versions", {})
drifted = []

for branch in ["main", "staging"]:
    try:
        result = subprocess.run(
            ["git", "-C", str(pm_dir), "show", f"origin/{branch}:workspace-manifest.json"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            continue
        remote_manifest = json.loads(result.stdout)

        # Check versions map
        for repo, remote_ver in sorted(remote_manifest.get("versions", {}).items()):
            if repo.startswith("_"):
                continue
            local_ver = local_versions.get(repo, "")
            if remote_ver and local_ver and remote_ver != local_ver:
                drifted.append(f"  {repo}: local={local_ver} origin/{branch}={remote_ver}")

        # Check staging_versions
        for repo, staging_ver in sorted(remote_manifest.get("staging_versions", {}).items()):
            if repo.startswith("_") or not staging_ver:
                continue
            local_ver = local_versions.get(repo, "")
            if staging_ver and local_ver and staging_ver != local_ver:
                entry = f"  {repo}: local={local_ver} origin/{branch} staging_versions={staging_ver}"
                if entry not in drifted:
                    drifted.append(entry)
    except Exception:
        pass

# Deduplicate by repo name
seen = set()
unique = []
for d in drifted:
    repo = d.strip().split(":")[0]
    if repo not in seen:
        seen.add(repo)
        unique.append(d)

if unique:
    print(f"  [WARN] Remote version drift ({len(unique)} repo(s)):")
    print("  Someone (or a workflow) bumped versions on remote that your local doesn't have.")
    print()
    for d in unique:
        print(d)
    print()
    print("  Fix: cd unified-trading-pm && git pull origin main  (sync manifest)")
    print("  Then: bash run-version-alignment.sh --fix  (align local pyproject.toml versions)")
else:
    print("  [OK] No remote version drift detected")
PYEOF
)
echo "$REMOTE_DRIFT"
echo ""

# 1 & 2. Generate derived + canonical manifests (parallel)
echo "[1/4] Generating derived + canonical manifests (parallel)..."
"$PYTHON" scripts/manifest/generate-derived-manifest.py &
PID_DERIVED=$!
"$PYTHON" scripts/manifest/generate_canonical_dependency_manifest.py &
PID_CANON=$!
wait $PID_DERIVED $PID_CANON

# 3. Check alignment
echo "[3/4] Checking alignment..."
ALIGN_JSON=$("$PYTHON" scripts/manifest/check-dependency-alignment.py --json 2>/dev/null || true)
HAS_INTERNAL=$(echo "$ALIGN_JSON" | "$PYTHON" -c "import json,sys; d=json.load(sys.stdin); print('1' if any(i.get('type','').startswith('internal_') for i in d.get('issues',[])) else '0')" 2>/dev/null || echo '0')
HAS_EXTERNAL=$(echo "$ALIGN_JSON" | "$PYTHON" -c "import json,sys; d=json.load(sys.stdin); print('1' if any(i.get('type')=='external_version_mismatch' for i in d.get('issues',[])) else '0')" 2>/dev/null || echo '0')
if ! "$PYTHON" scripts/manifest/check-dependency-alignment.py; then
  echo ""
  echo "  Misalignment found. Options:"
  echo "    - Run with --fix to apply: bash run-version-alignment.sh --fix"
  echo "    - Or fix manually: fix-internal-dependency-alignment.py --apply, fix_external_dependency_alignment.py --apply"
  if [ "$APPLY_FIXES" = true ]; then
    echo ""
    echo "  Applying fixes (internal=$HAS_INTERNAL external=$HAS_EXTERNAL)..."
    [ "$HAS_INTERNAL" = '1' ] && "$PYTHON" scripts/manifest/fix-internal-dependency-alignment.py --apply 2>&1 || true
    [ "$HAS_EXTERNAL" = '1' ] && "$PYTHON" scripts/manifest/fix_external_dependency_alignment.py --apply 2>&1 || true
    "$PYTHON" scripts/manifest/generate-derived-manifest.py
    echo "  Re-checking..."
    "$PYTHON" scripts/manifest/check-dependency-alignment.py
  else
    exit 1
  fi
fi

# 3.5. Validate [tool.uv.sources] editable entries
echo "[3.5/4] Validating [tool.uv.sources] editable entries..."
if [ "$APPLY_FIXES" = true ]; then
  "$PYTHON" scripts/manifest/validate-uv-sources.py --fix || true
else
  if ! "$PYTHON" scripts/manifest/validate-uv-sources.py; then
    echo ""
    echo "  Missing [tool.uv.sources.*] editable entries. Run with --fix to auto-add."
    exit 1
  fi
fi


# 3.6. Validate internal deps are editable (not from Artifact Registry)
echo "[3.6/5] Validating internal deps are editable (not from Artifact Registry)..."
if ! "$PYTHON" scripts/manifest/validate-internal-editable.py; then
  echo ""
  echo "  Internal deps must be path/editable. Run: uv sync in each repo."
  exit 1
fi

# 3.7. Validate every direct import of an internal library has dep + uv source
echo "[3.7/5] Validating direct imports have deps + uv sources..."
if [ "$APPLY_FIXES" = true ]; then
  "$PYTHON" scripts/manifest/validate-import-deps.py --fix || true
else
  if ! "$PYTHON" scripts/manifest/validate-import-deps.py; then
    echo ""
    echo "  Services import internal libraries without declaring them in pyproject.toml."
    echo "  Run with --fix to auto-add missing [project.dependencies] + [tool.uv.sources] entries."
    exit 1
  fi
fi

# 4. Validate constraints resolve
echo "[4/5] Validating constraints..."


if ! "$PYTHON" scripts/manifest/validate-dependency-conflicts.py; then
  echo ""
  echo "  Constraints did not resolve (see uv output above). To refresh constraints then re-check:"
  echo "    cd \"$PM_ROOT\" && $PYTHON scripts/manifest/validate-dependency-conflicts.py --regenerate"
  echo "  From workspace root (copy-paste):"
  echo "    $PYTHON \"$PM_ROOT/scripts/manifest/validate-dependency-conflicts.py\" --regenerate"
  exit 1
fi

echo ""
echo "  Alignment OK."

# After --fix: refresh workspace venv so editable installs reflect updated dep versions.
# Per-repo .venv rebuilds happen in run-all-setup.sh (next step).
if [ "$APPLY_FIXES" = true ]; then
  SYNC_SCRIPT="$PM_ROOT/scripts/workspace/sync-workspace-venv.sh"
  if [ -f "$SYNC_SCRIPT" ]; then
    echo ""
    echo "  Refreshing .venv-workspace (dep versions changed by --fix)..."
    bash "$SYNC_SCRIPT" 2>&1 | grep -E '^\s+\[(OK|WARN|FAIL|SKIP)\]|━' || true
    echo ""
  fi
fi

# Always regenerate canonical manifest + SVG at end-of-run — guarantees the visual
# is fresh whether constraints were just fixed or simply re-validated.
"$PYTHON" scripts/manifest/generate_canonical_dependency_manifest.py

echo "  Next: bash unified-trading-pm/scripts/repo-management/run-all-setup.sh"
