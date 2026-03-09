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
#   4. validate-dependency-conflicts.py → verify constraints resolve (uv pip compile)
#   5. fix-internal-dependency-alignment.py --apply (if internal misalignment)
#   6. fix_external_dependency_alignment.py --apply (if external misalignment)

set -euo pipefail

APPLY_FIXES=false
STRICT=false
for arg in "$@"; do
  case $arg in
    --fix) APPLY_FIXES=true ;;
    --strict) STRICT=true ;;
    --help | -h)
      echo "Usage: bash run-version-alignment.sh [--fix] [--strict]"
      echo "  --fix     Apply fixes (internal + external alignment)"
      echo "  --strict  Treat broken symlinks as a fatal error (default: warn)"
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

# 4. Validate constraints resolve
echo "[4/4] Validating constraints..."


if ! "$PYTHON" scripts/manifest/validate-dependency-conflicts.py 2>/dev/null; then
  echo "  Constraints have conflicts. Run: $PYTHON scripts/manifest/validate-dependency-conflicts.py --regenerate"
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

echo "  Next: bash unified-trading-pm/scripts/repo-management/run-all-setup.sh"
