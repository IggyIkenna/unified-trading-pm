#!/usr/bin/env bash
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

# Colour output (same palette as setup.sh)
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
ok()    { echo -e "${GREEN}  [OK] $1${NC}"; }
warn()  { echo -e "${YELLOW}  [WARN] $1${NC}"; }
error() { echo -e "${RED}  [ERROR] $1${NC}"; }
step()  { echo -e "${BLUE}$1${NC}"; }

# Use workspace venv Python (has tomli_w and all manifest tools installed).
# Falls back to system python3.13 if venv not found.
VENV_PYTHON="$WORKSPACE_ROOT/.venv-workspace/bin/python3.13"
if [ -x "$VENV_PYTHON" ]; then
  PYTHON="$VENV_PYTHON"
else
  PYTHON="python3.13"
fi

echo -e "${BLUE}━━━ Version alignment ━━━${NC}"
echo ""
echo "Checks performed (dry run = report only; --fix = apply auto-fixes):"
echo -e "  [0]     Tracked-but-gitignored audit          — informational only"
echo -e "  [0.5]   Broken symlinks                       — ${YELLOW}manual: rm <path> && ln -sf <target> <path>${NC}"
echo -e "  [0.6]   UI npm dep drift (pkg.json vs lock)   — ${YELLOW}manual: cd <repo> && npm install${NC}"
echo -e "  [0.7]   Canonical npm version alignment       — ${YELLOW}auto-fix with --fix${NC}"
echo -e "  [0.8]   uv.lock drift (pyproject newer / uncommitted changes) — ${YELLOW}warn or --strict fatal${NC}"
echo -e "  [1–2]   Derived + canonical manifests         — generated (prerequisite)"
echo -e "  [3]     Dependency alignment (internal+external)— ${YELLOW}auto-fix with --fix${NC}"
echo -e "  [3.5]   [tool.uv.sources] editable entries   — ${YELLOW}auto-fix with --fix${NC}"
echo -e "  [3.6]   Internal deps editable (not registry) — ${RED}manual: uv sync in each repo${NC}"
echo -e "  [4]     Constraint resolution (uv pip compile)— ${RED}manual: validate-dependency-conflicts.py --regenerate${NC}"
echo ""
echo "Downstream CI (not run here; alignment must pass first):"
echo "  • Cloud Build (GCP): library pre-checks, Docker builds — add-cloudbuild-prechecks.py"
echo "  • Code Build (AWS): UI buildspec.aws.yaml — rollout-ui-build-infra.py"
echo "  Run: bash run-all-setup.sh --rollout-first  to propagate build infra."
echo ""

# 0. Audit tracked-but-gitignored files (informational; never blocks)
step "[0/4] Auditing tracked files matched by .gitignore..."
bash "$PM_ROOT/scripts/audit_tracked_ignored.sh" 2>/dev/null || true
echo ""

# 0.5. Broken symlink check across all repos in workspace
step "[0.5/4] Checking for broken symlinks across all workspace repos..."
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
  -type l -print0 2>/dev/null)

if [ "${#BROKEN_SYMLINKS[@]}" -gt 0 ]; then
  echo ""
  warn "Broken symlinks found (${#BROKEN_SYMLINKS[@]}):"
  for s in "${BROKEN_SYMLINKS[@]}"; do echo "$s"; done
  echo ""
  echo "  To fix: rm <path> and re-target with: ln -sf <new-target> <path>"
  echo "  Pass --strict to treat broken symlinks as a fatal error."
  if [ "${STRICT:-false}" = true ]; then
    exit 1
  fi
else
  ok "No broken symlinks"
fi
echo ""

# 0.55. Required symlink presence check — verify .cursor/scripts/check-import-patterns.py
#        exists (as a symlink, not a local copy) in all Python manifest repos
step "[0.55/4] Checking .cursor/scripts/check-import-patterns.py symlinks in Python repos..."
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
    if [ "${#MISSING_SYMLINKS[@]}" -gt 0 ]; then
        warn "Missing check-import-patterns.py symlinks (${#MISSING_SYMLINKS[@]}):"
        for s in "${MISSING_SYMLINKS[@]}"; do echo "$s"; done
    fi
    if [ "${#STALE_COPIES[@]}" -gt 0 ]; then
        warn "Stale local copies (should be symlinks) (${#STALE_COPIES[@]}):"
        for s in "${STALE_COPIES[@]}"; do echo "$s"; done
    fi
    echo "  Fix: bash unified-trading-pm/scripts/rollout-agent-symlinks.sh"
    if [ "${STRICT:-false}" = true ]; then
        exit 1
    fi
else
    ok "All Python repos have check-import-patterns.py symlinks"
fi
echo ""

# 0.6. UI dep-drift check — detect UI repos where package.json is newer than package-lock.json
#      (means npm install hasn't been run since package.json was last edited).
step "[0.6/4] Checking UI repos for npm dep drift (package.json newer than package-lock.json)..."
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
  -not \( -path "*/unified-trading-pm/*" -prune \) 2>/dev/null)

if [ "${#UI_DRIFT[@]}" -gt 0 ]; then
  echo ""
  warn "UI repos with stale node_modules (${#UI_DRIFT[@]}):"
  for d in "${UI_DRIFT[@]}"; do echo "$d"; done
  echo ""
  echo "  Fix: cd <repo> && npm install   OR   bash unified-trading-pm/scripts/repo-management/run-all-setup.sh --rollout-first"
  if [ "${STRICT:-false}" = true ]; then
    exit 1
  fi
else
  ok "All UI repos have up-to-date package-lock.json"
fi
echo ""

# 0.7. Canonical npm version check — enforce workspace-npm-constraints.json across UI repos
step "[0.7/4] Checking UI repos for npm version alignment (canonical constraints)..."
if [ "$APPLY_FIXES" = true ]; then
  if ! "$PYTHON" scripts/propagation/rollout-npm-versions.py --apply 2>&1; then
    warn "npm version update failed (non-fatal) — check output above"
  fi
else
  if ! "$PYTHON" scripts/propagation/rollout-npm-versions.py 2>&1; then
    echo ""
    warn "npm version misalignment detected — auto-fixable"
    echo "  Fix: python3 unified-trading-pm/scripts/propagation/rollout-npm-versions.py --apply"
    echo "  Or:  bash unified-trading-pm/scripts/repo-management/run-version-alignment.sh --fix"
    if [ "${STRICT:-false}" = true ]; then
      exit 1
    fi
  fi
fi
echo ""

# 0.8. uv.lock drift detection — stale lockfile (pyproject.toml newer) or uncommitted changes
step "[0.8/4] Checking uv.lock staleness and uncommitted changes across all repos..."
LOCK_DRIFT=()
while IFS= read -r lock_file; do
  repo_dir="$(dirname "$lock_file")"
  repo_name="$(basename "$repo_dir")"
  [ "$repo_dir" = "$WORKSPACE_ROOT" ] && continue
  pyproject="$repo_dir/pyproject.toml"
  # pyproject.toml newer than uv.lock → lockfile needs regeneration
  if [ -f "$pyproject" ] && [ "$pyproject" -nt "$lock_file" ]; then
    LOCK_DRIFT+=("  $repo_name: pyproject.toml newer than uv.lock — run: cd $repo_name && uv lock")
  fi
  # uncommitted changes to uv.lock on the working tree
  if git -C "$repo_dir" status --porcelain uv.lock 2>/dev/null | grep -q 'uv\.lock'; then
    LOCK_DRIFT+=("  $repo_name: uv.lock has uncommitted local changes")
  fi
done < <(find "$WORKSPACE_ROOT" -maxdepth 2 -name "uv.lock" \
  -not \( -path "*/.venv*" -prune \) \
  -not \( -path "*/unified-trading-pm/*" -prune \) 2>/dev/null)

if [ "${#LOCK_DRIFT[@]}" -gt 0 ]; then
  echo ""
  warn "uv.lock drift detected (${#LOCK_DRIFT[@]} issue(s)):"
  for d in "${LOCK_DRIFT[@]}"; do echo "$d"; done
  echo ""
  echo "  Fix: cd <repo> && uv lock   (regenerate from pyproject.toml)"
  echo "  Pass --strict to treat uv.lock drift as a fatal error."
  if [ "${STRICT:-false}" = true ]; then
    exit 1
  fi
else
  ok "All uv.lock files are up to date"
fi
echo ""

# --ui-only: pre-checks complete — skip Python alignment steps
if [ "$UI_ONLY" = true ]; then
  ok "--ui-only: pre-checks complete. Skipping Python alignment steps (1–4)."
  echo ""
  echo "  Next: bash unified-trading-pm/scripts/repo-management/run-all-setup.sh  (to reinstall stale UI deps)"
  exit 0
fi

# 1 & 2. Generate derived + canonical manifests (parallel)
step "[1/4] Generating derived + canonical manifests (parallel)..."
"$PYTHON" scripts/manifest/generate-derived-manifest.py &
PID_DERIVED=$!
"$PYTHON" scripts/manifest/generate_canonical_dependency_manifest.py &
PID_CANON=$!
wait $PID_DERIVED $PID_CANON

# 3. Check alignment
step "[3/4] Checking alignment..."
ALIGN_JSON=$("$PYTHON" scripts/manifest/check-dependency-alignment.py --json 2>/dev/null || true)
HAS_INTERNAL=$(echo "$ALIGN_JSON" | "$PYTHON" -c "import json,sys; d=json.load(sys.stdin); print('1' if any(i.get('type','').startswith('internal_') for i in d.get('issues',[])) else '0')" 2>/dev/null || echo '0')
HAS_EXTERNAL=$(echo "$ALIGN_JSON" | "$PYTHON" -c "import json,sys; d=json.load(sys.stdin); print('1' if any(i.get('type')=='external_version_mismatch' for i in d.get('issues',[])) else '0')" 2>/dev/null || echo '0')
if ! "$PYTHON" scripts/manifest/check-dependency-alignment.py; then
  echo ""
  warn "Misalignment found — auto-fixable with --fix"
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
step "[3.5/4] Validating [tool.uv.sources] editable entries..."
if [ "$APPLY_FIXES" = true ]; then
  "$PYTHON" scripts/manifest/validate-uv-sources.py --fix || true
else
  if ! "$PYTHON" scripts/manifest/validate-uv-sources.py; then
    echo ""
    warn "Missing [tool.uv.sources.*] editable entries — auto-fixable with --fix"
    exit 1
  fi
fi


# 3.6. Validate internal deps are editable (not from Artifact Registry)
step "[3.6/5] Validating internal deps are editable (not from Artifact Registry)..."
if ! "$PYTHON" scripts/manifest/validate-internal-editable.py; then
  echo ""
  error "Internal deps must be path/editable — manual fix required"
  echo "  Fix: cd <repo> && uv sync   (in each failing repo)"
  exit 1
fi

# 4. Validate constraints resolve
step "[4/5] Validating constraints..."

if ! "$PYTHON" scripts/manifest/validate-dependency-conflicts.py 2>/dev/null; then
  echo ""
  error "Constraints have conflicts — manual fix required"
  echo "  Fix: $PYTHON scripts/manifest/validate-dependency-conflicts.py --regenerate"
  exit 1
fi

echo ""
ok "Alignment OK."

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

echo "  Next: bash unified-trading-pm/scripts/repo-management/run-all-setup.sh"
