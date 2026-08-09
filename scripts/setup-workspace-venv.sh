#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# setup-workspace-venv.sh — Create/refresh .venv-workspace with all workspace
# packages installed as editable.
#
# SSOT: unified-trading-pm/scripts/setup-workspace-venv.sh
#
# Usage:
#   bash unified-trading-pm/scripts/setup-workspace-venv.sh          # Create venv + install
#   bash unified-trading-pm/scripts/setup-workspace-venv.sh --force  # Recreate venv from scratch
#   bash unified-trading-pm/scripts/setup-workspace-venv.sh --check  # Verify only
#
# What this script does:
#   1. Creates .venv-workspace at WORKSPACE_ROOT with Python 3.13 (if missing)
#   2. Installs workspace tools: ruff, basedpyright, pytest
#   3. Reads workspace-manifest.json and installs every repo that has a
#      pyproject.toml as editable: uv pip install -e <repo>
#      Installation is done in topological order (T0 -> T1 -> T2 -> T3).
#
# Why editable installs matter:
#   Editable installs (uv pip install -e <path>) mean Python imports resolve
#   directly from the source tree. Without this, pip may pull a wheel from
#   PyPI/Artifact Registry and changes to local source files will not be
#   reflected in the shared venv.
#
# Idempotent — safe to re-run. Uses --force to recreate from scratch.

set -e

# ── PATH EXTENSIONS ──────────────────────────────────────────────────────────
for p in /opt/homebrew/bin /usr/local/bin "$HOME/.local/bin" "$HOME/.pyenv/shims"; do
    [ -d "$p" ] && case ":$PATH:" in *":$p:"*) ;; *) export PATH="$p:$PATH" ;; esac
done

# ── COLORS + LOGGING ────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log_ok()   { echo -e "${GREEN}  [OK] $1${NC}"; }
log_skip() { echo -e "${BLUE}  [SKIP] $1${NC}"; }
log_warn() { echo -e "${YELLOW}  [WARN] $1${NC}"; }
log_fail() { echo -e "${RED}  [FAIL] $1${NC}"; }
log_step() { echo -e "\n${BLUE}==> $1${NC}"; }

# ── PARSE ARGUMENTS ─────────────────────────────────────────────────────────
FORCE=false
CHECK_ONLY=false
for arg in "$@"; do
    case $arg in
        --force)  FORCE=true ;;
        --check)  CHECK_ONLY=true ;;
        --help|-h)
            echo "Usage: bash unified-trading-pm/scripts/setup-workspace-venv.sh [--force|--check]"
            echo ""
            echo "  --force  Recreate .venv-workspace from scratch"
            echo "  --check  Verify all workspace packages are editable (no changes)"
            exit 0
            ;;
    esac
done

# ── RESOLVE PATHS ───────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
PM_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
WORKSPACE_ROOT="$(cd "$PM_ROOT/.." && pwd)"
MANIFEST_PATH="$PM_ROOT/workspace-manifest.json"
VENV_DIR="$WORKSPACE_ROOT/.venv-workspace"
REQUIRED_PYTHON="3.13"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  setup-workspace-venv.sh${NC}"
echo -e "${BLUE}  Workspace: $WORKSPACE_ROOT${NC}"
echo -e "${BLUE}  Venv:      $VENV_DIR${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

ISSUES=0

# ── [1] CHECK MANIFEST ───────────────────────────────────────────────────────
log_step "Workspace manifest"
if [ ! -f "$MANIFEST_PATH" ]; then
    log_fail "workspace-manifest.json not found at $MANIFEST_PATH"
    exit 1
fi
log_ok "manifest: $MANIFEST_PATH"

# ── [2] ENSURE UV AVAILABLE ──────────────────────────────────────────────────
log_step "uv"
if ! command -v uv &>/dev/null; then
    log_fail "uv not found — install: pip install uv  or  brew install uv"
    exit 1
fi
log_ok "$(uv --version 2>&1 | head -1)"

# ── [3] FIND PYTHON 3.13 ────────────────────────────────────────────────────
log_step "Python $REQUIRED_PYTHON"
PYTHON_CMD=""
for cmd in "python${REQUIRED_PYTHON}" python3 python; do
    if command -v "$cmd" &>/dev/null; then
        VER=$("$cmd" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
        if [ "$VER" = "$REQUIRED_PYTHON" ]; then
            PYTHON_CMD="$cmd"
            break
        fi
    fi
done
if [ -z "$PYTHON_CMD" ]; then
    log_fail "Python $REQUIRED_PYTHON not found"
    echo "  Install: brew install python@${REQUIRED_PYTHON}"
    exit 1
fi
log_ok "$PYTHON_CMD ($VER)"

# ── [4] CREATE / VERIFY VENV ────────────────────────────────────────────────
log_step "Virtual environment (.venv-workspace)"
if [ "$CHECK_ONLY" = true ]; then
    if [ -d "$VENV_DIR" ] && [ -f "$VENV_DIR/bin/python" ]; then
        log_ok ".venv-workspace exists"
    else
        log_fail ".venv-workspace missing or broken"
        ISSUES=$((ISSUES + 1))
    fi
elif [ "$FORCE" = true ]; then
    rm -rf "$VENV_DIR"
    uv venv "$VENV_DIR" --python "$PYTHON_CMD" 2>/dev/null
    log_ok "Recreated .venv-workspace"
elif [ -d "$VENV_DIR" ] && [ -f "$VENV_DIR/bin/python" ]; then
    VENV_PY=$("$VENV_DIR/bin/python" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1 || echo "")
    if [ "$VENV_PY" = "$REQUIRED_PYTHON" ]; then
        log_skip ".venv-workspace exists (Python $VENV_PY)"
    else
        log_warn ".venv-workspace has Python $VENV_PY, need $REQUIRED_PYTHON — recreating"
        rm -rf "$VENV_DIR"
        uv venv "$VENV_DIR" --python "$PYTHON_CMD" 2>/dev/null
        log_ok "Recreated .venv-workspace with Python $REQUIRED_PYTHON"
    fi
else
    uv venv "$VENV_DIR" --python "$PYTHON_CMD" 2>/dev/null
    log_ok "Created .venv-workspace"
fi

VENV_PYTHON="$VENV_DIR/bin/python"

# ── [5] INSTALL WORKSPACE TOOLS ─────────────────────────────────────────────
log_step "Workspace tools (ruff, basedpyright, pytest)"
if [ "$CHECK_ONLY" = true ]; then
    for tool in ruff basedpyright pytest; do
        if "$VENV_PYTHON" -c "import $tool" 2>/dev/null || [ -f "$VENV_DIR/bin/$tool" ]; then
            log_ok "$tool"
        else
            log_warn "$tool not installed"
        fi
    done
else
    uv pip install --python "$VENV_PYTHON" \
        "ruff==0.15.0" \
        "basedpyright==1.38.2" \
        "pytest>=8.0.0" \
        --quiet 2>/dev/null && log_ok "Tools installed (ruff==0.15.0, basedpyright==1.38.2)" || log_warn "Tool install had issues (non-fatal)"
fi

# ── [5.5] COLLECT PER-REPO uv OVERRIDES ─────────────────────────────────────
# Each workspace repo may declare its own [tool.uv].override-dependencies in
# pyproject.toml (CVE-floor bumps, the requests>=2.33.0-vs-betfairlightweight
# conflict, etc — see
# .cursor/rules/dependencies/requests-betfairlightweight-workspace-resolution.mdc).
# `uv pip install -e <path>` installs each repo standalone with no calling-project
# [tool.uv] context, so neither the target's own override nor a sibling repo's is
# consulted — the exact gap every ad-hoc `uv pip install -e ../<dep>` sibling-install
# in this workspace already works around by declaring its own copy of the override
# (see the comment in features-service/pyproject.toml). Union every repo's overrides
# once so the fix applies uniformly across the editable-install loop below.
OVERRIDES_FILE=""
if [ "$CHECK_ONLY" != true ]; then
    log_step "Collecting per-repo uv overrides"
    OVERRIDES_FILE=$(mktemp)
    trap 'rm -f "$OVERRIDES_FILE"' EXIT
    "$PYTHON_CMD" - "$WORKSPACE_ROOT" <<'PYEOF' > "$OVERRIDES_FILE"
import glob
import os
import sys
import tomllib

workspace_root = sys.argv[1]
seen = set()
for pp in sorted(glob.glob(os.path.join(workspace_root, "*", "pyproject.toml"))):
    try:
        with open(pp, "rb") as f:
            data = tomllib.load(f)
    except Exception:
        continue
    for line in data.get("tool", {}).get("uv", {}).get("override-dependencies", []):
        if line not in seen:
            seen.add(line)
            print(line)
PYEOF
    N_OVERRIDES=$(wc -l < "$OVERRIDES_FILE" | tr -d ' ')
    log_ok "$N_OVERRIDES override(s) collected across workspace repos"
fi

# ── [6] INSTALL WORKSPACE REPOS AS EDITABLE ─────────────────────────────────
# Read all repos from workspace-manifest.json in topological order and install
# each one that has a pyproject.toml as editable. Editable install means Python
# imports resolve directly from the source tree — wheels from PyPI/Artifact
# Registry cannot override local source.
log_step "Workspace packages (editable installs)"

# Parse topological order from manifest using Python (always available at this point)
ORDERED_REPOS=$("$PYTHON_CMD" - <<'PYEOF'
import json, sys
manifest_path = sys.argv[1] if len(sys.argv) > 1 else ""
try:
    with open(manifest_path) as f:
        data = json.load(f)
    topo = data.get("topologicalOrder", {})
    levels = topo.get("levels", [])
    ordered = []
    for level in sorted(levels, key=lambda l: l.get("level", 999)):
        for repo in level.get("repos", []):
            ordered.append(repo)
    # Fallback: any repos in manifest not already in topo order
    all_repos = set(data.get("repositories", {}).keys())
    ordered_set = set(ordered)
    for repo in sorted(all_repos - ordered_set):
        ordered.append(repo)
    print("\n".join(ordered))
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)
PYEOF
"$MANIFEST_PATH" 2>/dev/null || echo "")

if [ -z "$ORDERED_REPOS" ]; then
    # Fallback: use jq if Python parse failed
    if command -v jq &>/dev/null; then
        ORDERED_REPOS=$(jq -r '.repositories | keys[]' "$MANIFEST_PATH" 2>/dev/null || echo "")
    fi
fi

if [ -z "$ORDERED_REPOS" ]; then
    log_fail "Could not read repository list from manifest"
    exit 1
fi

EDITABLE_OK=0
EDITABLE_SKIP=0
EDITABLE_FAIL=0

for repo in $ORDERED_REPOS; do
    REPO_PATH="$WORKSPACE_ROOT/$repo"

    # Support folder_name override from manifest
    FOLDER_NAME=$("$PYTHON_CMD" -c "
import json
with open('$MANIFEST_PATH') as f:
    data = json.load(f)
entry = data.get('repositories', {}).get('$repo', {})
print(entry.get('folder_name', ''))
" 2>/dev/null || echo "")
    if [ -n "$FOLDER_NAME" ]; then
        REPO_PATH="$WORKSPACE_ROOT/$FOLDER_NAME"
    fi

    if [ ! -f "$REPO_PATH/pyproject.toml" ]; then
        EDITABLE_SKIP=$((EDITABLE_SKIP + 1))
        continue
    fi

    if [ "$CHECK_ONLY" = true ]; then
        # Check whether it is installed as editable (direct URL or egg-link)
        PKG=$(grep -A 1 '^\[project\]' "$REPO_PATH/pyproject.toml" 2>/dev/null | grep '^name' | sed 's/.*= *"//;s/".*//' | tr '-' '_' 2>/dev/null || echo "")
        if [ -n "$PKG" ]; then
            LOC=$(uv pip show --python "$VENV_PYTHON" "$PKG" 2>/dev/null | grep '^Location:' | awk '{print $2}' || echo "")
            if echo "$LOC" | grep -q "$REPO_PATH"; then
                log_ok "$repo (editable)"
                EDITABLE_OK=$((EDITABLE_OK + 1))
            elif [ -n "$LOC" ]; then
                log_warn "$repo installed at $LOC (not editable — should be $REPO_PATH)"
                ISSUES=$((ISSUES + 1))
                EDITABLE_FAIL=$((EDITABLE_FAIL + 1))
            else
                log_skip "$repo (not installed)"
                EDITABLE_SKIP=$((EDITABLE_SKIP + 1))
            fi
        else
            EDITABLE_SKIP=$((EDITABLE_SKIP + 1))
        fi
    else
        EXTRA_INSTALL_ARGS=()
        if [ -n "$OVERRIDES_FILE" ]; then
            EXTRA_INSTALL_ARGS=(--overrides "$OVERRIDES_FILE")
        fi
        if uv pip install --python "$VENV_PYTHON" -e "$REPO_PATH" --reinstall --quiet "${EXTRA_INSTALL_ARGS[@]}" 2>/dev/null; then
            EDITABLE_OK=$((EDITABLE_OK + 1))
        else
            log_warn "$repo editable install failed (non-fatal)"
            EDITABLE_FAIL=$((EDITABLE_FAIL + 1))
        fi
    fi
done

if [ "$CHECK_ONLY" = true ]; then
    echo -e "\n  Editable: $EDITABLE_OK | Non-editable/missing: $EDITABLE_FAIL | Skipped: $EDITABLE_SKIP"
else
    log_ok "Editable installs: $EDITABLE_OK | Skipped (no pyproject.toml): $EDITABLE_SKIP | Failed: $EDITABLE_FAIL"
fi

# ── SUMMARY ──────────────────────────────────────────────────────────────────
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
if [ "$ISSUES" -gt 0 ]; then
    echo -e "${RED}  $ISSUES issue(s) found${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    [ "$CHECK_ONLY" = true ] && exit 2 || exit 1
else
    echo -e "${GREEN}  .venv-workspace ready — all workspace packages installed as editable${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
fi
echo ""
echo "  Activate: source $VENV_DIR/bin/activate"
echo ""
