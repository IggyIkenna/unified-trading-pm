#!/usr/bin/env bash
# CANONICAL SETUP — unified-trading-system
#
# Single source of truth for repo-local development environment setup.
# Copy to scripts/setup.sh in every repo. Idempotent — safe to re-run.
#
# SSOT: unified-trading-pm/scripts/setup.sh
# Codex: unified-trading-codex/06-coding-standards/setup-standards.md
#
# Usage:
#   bash scripts/setup.sh              # Full setup (idempotent)
#   bash scripts/setup.sh --check      # Verify setup without changes
#   bash scripts/setup.sh --force      # Force reinstall (ignores cache)
#   bash scripts/setup.sh --isolated   # Standalone repo setup (no workspace deps)
#   source scripts/setup.sh            # Setup + activate venv in current shell
#
# What this script does (in order):
#   1. Validate Python version (>=3.13,<3.14 — or repo-specific override)
#   2. Validate architecture (Apple Silicon: reject x86_64 Python on ARM)
#   3. Create .venv if missing (uv venv)
#   4. Activate .venv
#   5. Bootstrap uv (the only pip install allowed)
#   6. Run uv lock if pyproject.toml changed (skip if uv.lock is current)
#   7. Install local path dependencies from .dependency-matrix.json
#   8. Install project + dev deps (uv pip install -e ".[dev]")
#   9. Verify ripgrep available (required by quality-gates.sh)
#  10. Verify ruff version matches workspace standard (0.15.0)
#  11. Import smoke test (python -c "import <package>")
#  12. Detect GCP credentials (informational, non-blocking)
#
# Idempotency:
#   - .venv creation: skipped if .venv/ exists and Python version matches
#   - uv lock: skipped if uv.lock is newer than pyproject.toml
#   - Dep install: skipped if .setup-stamp is newer than pyproject.toml + uv.lock
#   - Each step prints SKIP or OK, never re-does work unnecessarily
#
# CI detection:
#   In CI (GITHUB_ACTIONS, CI, CLOUD_BUILD set), steps 1-8 are skipped —
#   CI environments manage their own Python, venv, and deps.
#   Steps 9-11 (verification) always run.
#
# Exit codes:
#   0 = success
#   1 = fatal (wrong Python, missing deps, import failure)
#   2 = check mode found issues (--check)

set -e

# ── REPO-SPECIFIC SETTINGS (edit per repo) ──────────────────────────────────
# Override these in each repo's copy. Only PACKAGE_NAME is required.
PACKAGE_NAME="${PACKAGE_NAME:-}"        # e.g. "unified_api_contracts" — auto-detected from pyproject.toml if empty
REQUIRED_PYTHON="${REQUIRED_PYTHON:-3.13}"  # Major.minor — read from pyproject.toml if possible
REQUIRED_RUFF="${REQUIRED_RUFF:-0.15.0}"
# ── END REPO-SPECIFIC ───────────────────────────────────────────────────────

# ── COLORS + LOGGING ────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log_ok()   { echo -e "${GREEN}  [OK] $1${NC}"; }
log_skip() { echo -e "${BLUE}  [SKIP] $1${NC}"; }
log_warn() { echo -e "${YELLOW}  [WARN] $1${NC}"; }
log_fail() { echo -e "${RED}  [FAIL] $1${NC}"; }
log_step() { echo -e "\n${BLUE}[$STEP_NUM] $1${NC}"; STEP_NUM=$((STEP_NUM + 1)); }
STEP_NUM=1

# ── PARSE ARGUMENTS ─────────────────────────────────────────────────────────
CHECK_ONLY=false
FORCE=false
ISOLATED=false
for arg in "$@"; do
    case $arg in
        --check) CHECK_ONLY=true ;;
        --force) FORCE=true ;;
        --isolated) ISOLATED=true ;;
        --help|-h)
            echo "Usage: bash scripts/setup.sh [--check|--force|--isolated|--help]"
            echo ""
            echo "  --check      Verify environment without making changes"
            echo "  --force      Force reinstall (ignores stamp cache)"
            echo "  --isolated   Standalone repo setup (no workspace deps)"
            echo "  --help       Show this message"
            echo ""
            echo "Idempotent. Safe to re-run. Skips steps already completed."
            echo ""
            echo "Flags can be combined: bash scripts/setup.sh --check --isolated"
            exit 0
            ;;
    esac
done

# ── RESOLVE PATHS ───────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_NAME=$(basename "$PROJECT_ROOT")
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$PROJECT_ROOT/.." && pwd)}"
cd "$PROJECT_ROOT"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  setup.sh — $REPO_NAME${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# ── AUTO-DETECT PACKAGE_NAME ────────────────────────────────────────────────
if [ -z "$PACKAGE_NAME" ] && [ -f "pyproject.toml" ]; then
    # Try [project] name field first, convert dashes to underscores
    PACKAGE_NAME=$(grep -A 1 '^\[project\]' pyproject.toml | grep '^name' | sed 's/.*= *"//;s/".*//' | tr '-' '_' 2>/dev/null || echo "")
fi

# ── AUTO-DETECT REQUIRED_PYTHON from pyproject.toml ─────────────────────────
if [ -f "pyproject.toml" ]; then
    PYVER=$(grep 'requires-python' pyproject.toml | grep -oE '[0-9]+\.[0-9]+' | head -1 2>/dev/null || echo "")
    [ -n "$PYVER" ] && REQUIRED_PYTHON="$PYVER"
fi

# ── CI DETECTION ────────────────────────────────────────────────────────────
IN_CI=false
if [ -n "${GITHUB_ACTIONS:-}" ] || [ -n "${CI:-}" ] || [ -n "${CLOUD_BUILD:-}" ]; then
    IN_CI=true
    echo -e "  ${YELLOW}CI detected — skipping venv/deps setup (CI manages its own env)${NC}"
fi

SETUP_STAMP="$PROJECT_ROOT/.setup-stamp"
ISSUES=0

# ── [1] PYTHON VERSION ─────────────────────────────────────────────────────
log_step "Python version (requires $REQUIRED_PYTHON)"

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

if [ -n "$PYTHON_CMD" ]; then
    log_ok "Python $VER ($PYTHON_CMD)"
else
    log_fail "Python $REQUIRED_PYTHON not found"
    echo "  Install: pyenv install ${REQUIRED_PYTHON}.0 && pyenv local ${REQUIRED_PYTHON}.0"
    echo "  Or: brew install python@${REQUIRED_PYTHON}"
    ISSUES=$((ISSUES + 1))
    [ "$CHECK_ONLY" = true ] || exit 1
fi

# ── [2] ARCHITECTURE CHECK (Apple Silicon) ──────────────────────────────────
log_step "Architecture check"

if [[ "$OSTYPE" == "darwin"* ]] && [ -n "$PYTHON_CMD" ]; then
    ARCH=$(uname -m)
    PY_ARCH=$("$PYTHON_CMD" -c "import platform; print(platform.machine())" 2>/dev/null || echo "unknown")
    if [ "$ARCH" = "arm64" ] && [ "$PY_ARCH" = "x86_64" ]; then
        log_fail "Python is x86_64 (Rosetta) on ARM64 Mac — native ARM64 required"
        echo "  Fix: brew install python@${REQUIRED_PYTHON} (native ARM64)"
        ISSUES=$((ISSUES + 1))
        [ "$CHECK_ONLY" = true ] || exit 1
    else
        log_ok "Architecture: $ARCH / Python: $PY_ARCH"
    fi
else
    log_skip "Not macOS or no Python — skipping arch check"
fi

# ── [3] VENV CREATION ──────────────────────────────────────────────────────
log_step "Virtual environment (.venv)"

if [ "$IN_CI" = true ]; then
    log_skip "CI mode — venv managed by CI"
elif [ "$CHECK_ONLY" = true ]; then
    [ -d ".venv" ] && log_ok ".venv exists" || { log_fail ".venv missing"; ISSUES=$((ISSUES + 1)); }
elif [ -d ".venv" ] && [ "$FORCE" != true ]; then
    # Verify venv Python matches required version
    VENV_PY=$(".venv/bin/python" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1 || echo "")
    if [ "$VENV_PY" = "$REQUIRED_PYTHON" ]; then
        log_skip ".venv exists (Python $VENV_PY)"
    else
        log_warn ".venv has Python $VENV_PY, need $REQUIRED_PYTHON — recreating"
        rm -rf .venv
        command -v uv &>/dev/null && uv venv .venv --python "$PYTHON_CMD" || "$PYTHON_CMD" -m venv .venv
        log_ok "Recreated .venv with Python $REQUIRED_PYTHON"
    fi
else
    command -v uv &>/dev/null && uv venv .venv --python "$PYTHON_CMD" 2>/dev/null || "$PYTHON_CMD" -m venv .venv
    log_ok "Created .venv"
fi

# ── [4] ACTIVATE VENV ──────────────────────────────────────────────────────
log_step "Activate .venv"

if [ "$IN_CI" = true ]; then
    log_skip "CI mode"
elif [ "$CHECK_ONLY" = true ]; then
    log_skip "Check mode — not activating"
elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    log_ok "Activated (.venv/bin/python)"
elif [ -f ".venv/Scripts/activate" ]; then
    source .venv/Scripts/activate
    log_ok "Activated (.venv/Scripts/python)"
else
    log_fail "No .venv/bin/activate found"
    ISSUES=$((ISSUES + 1))
    [ "$CHECK_ONLY" = true ] || exit 1
fi

# ── [5] BOOTSTRAP UV ───────────────────────────────────────────────────────
log_step "Bootstrap uv"

if [ "$IN_CI" = true ]; then
    log_skip "CI mode"
elif [ "$CHECK_ONLY" = true ]; then
    command -v uv &>/dev/null && log_ok "uv available" || { log_fail "uv not found"; ISSUES=$((ISSUES + 1)); }
elif command -v uv &>/dev/null; then
    log_skip "uv already installed"
else
    pip install uv --quiet 2>/dev/null
    log_ok "Installed uv"
fi

# ── [6] UV LOCK ─────────────────────────────────────────────────────────────
log_step "uv lock sync"

if [ "$IN_CI" = true ]; then
    log_skip "CI mode"
elif [ "$CHECK_ONLY" = true ]; then
    [ -f "uv.lock" ] && log_ok "uv.lock present" || log_warn "uv.lock missing"
elif [ ! -f "pyproject.toml" ]; then
    log_skip "No pyproject.toml"
elif [ -f "uv.lock" ] && [ "uv.lock" -nt "pyproject.toml" ] && [ "$FORCE" != true ]; then
    log_skip "uv.lock is current (newer than pyproject.toml)"
else
    uv lock 2>/dev/null && log_ok "uv.lock synced" || log_warn "uv lock failed (non-fatal)"
fi

# ── [7] LOCAL PATH DEPENDENCIES ─────────────────────────────────────────────
log_step "Local path dependencies"

if [ "$IN_CI" = true ] || [ "$CHECK_ONLY" = true ]; then
    log_skip "CI/check mode"
elif [ "$ISOLATED" = true ]; then
    log_skip "Isolated mode — skipping workspace path deps"
    if [ -f ".dependency-matrix.json" ]; then
        DEPS=$(command -v jq &>/dev/null && jq -r '.dependencies[].name' .dependency-matrix.json 2>/dev/null || echo "")
        if [ -n "$DEPS" ]; then
            log_warn "This repo depends on: $DEPS"
            log_warn "In isolated mode, install them from Artifact Registry (uv pip install <dep>)"
            log_warn "Some tests requiring these deps will fail — this is expected"
        fi
    fi
elif [ -f ".dependency-matrix.json" ] && command -v jq &>/dev/null; then
    DEPS=$(jq -r '.dependencies[].name' .dependency-matrix.json 2>/dev/null || echo "")
    if [ -n "$DEPS" ]; then
        for dep in $DEPS; do
            DEP_PATH="$WORKSPACE_ROOT/$dep"
            if [ -d "$DEP_PATH" ] && [ -f "$DEP_PATH/pyproject.toml" ]; then
                uv pip install -e "$DEP_PATH" --quiet 2>/dev/null && log_ok "$dep" || log_warn "$dep install failed"
            else
                log_warn "$dep not found at $DEP_PATH — install from Artifact Registry if needed"
            fi
        done
    else
        log_skip "No dependencies in .dependency-matrix.json"
    fi
else
    log_skip "No .dependency-matrix.json or jq not available"
fi

# ── [8] PROJECT DEPS ───────────────────────────────────────────────────────
log_step "Project dependencies"

if [ "$IN_CI" = true ]; then
    log_skip "CI mode"
elif [ "$CHECK_ONLY" = true ]; then
    log_skip "Check mode"
elif [ ! -f "pyproject.toml" ]; then
    log_skip "No pyproject.toml"
elif [ -f "$SETUP_STAMP" ] && [ "$SETUP_STAMP" -nt "pyproject.toml" ] && [ "$FORCE" != true ]; then
    if [ ! -f "uv.lock" ] || [ "$SETUP_STAMP" -nt "uv.lock" ]; then
        log_skip "Dependencies up to date (stamp is current)"
    else
        uv pip install -e ".[dev]" --quiet 2>/dev/null || uv pip install -e . --quiet 2>/dev/null
        touch "$SETUP_STAMP"
        log_ok "Dependencies installed (uv.lock changed)"
    fi
else
    uv pip install -e ".[dev]" --quiet 2>/dev/null || uv pip install -e . --quiet 2>/dev/null
    touch "$SETUP_STAMP"
    log_ok "Dependencies installed"
fi

# ── [9] RIPGREP CHECK ──────────────────────────────────────────────────────
log_step "ripgrep (required by quality-gates.sh)"

if command -v rg &>/dev/null; then
    log_ok "ripgrep $(rg --version 2>&1 | head -1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' || echo 'installed')"
else
    log_fail "ripgrep not found — install: brew install ripgrep"
    ISSUES=$((ISSUES + 1))
fi

# ── [10] RUFF VERSION ──────────────────────────────────────────────────────
log_step "ruff version (workspace standard: $REQUIRED_RUFF)"

RUFF_CMD=""
[ -f ".venv/bin/ruff" ] && RUFF_CMD=".venv/bin/ruff"
[ -z "$RUFF_CMD" ] && command -v ruff &>/dev/null && RUFF_CMD="ruff"

if [ -n "$RUFF_CMD" ]; then
    RUFF_VER=$("$RUFF_CMD" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || echo "unknown")
    if [ "$RUFF_VER" = "$REQUIRED_RUFF" ]; then
        log_ok "ruff $RUFF_VER"
    else
        log_warn "ruff $RUFF_VER (expected $REQUIRED_RUFF)"
    fi
else
    log_warn "ruff not found — will be installed with dev deps"
fi

# ── [11] IMPORT SMOKE TEST ─────────────────────────────────────────────────
log_step "Import smoke test"

if [ -n "$PACKAGE_NAME" ]; then
    SMOKE_PYTHON="${PYTHON_CMD:-python3}"
    [ -f ".venv/bin/python" ] && SMOKE_PYTHON=".venv/bin/python"
    if $SMOKE_PYTHON -c "import $PACKAGE_NAME" 2>/dev/null; then
        log_ok "import $PACKAGE_NAME"
    else
        if [ "$ISOLATED" = true ]; then
            log_warn "import $PACKAGE_NAME FAILED (isolated mode — missing workspace deps may cause this)"
        else
            log_fail "import $PACKAGE_NAME FAILED"
            ISSUES=$((ISSUES + 1))
        fi
    fi
else
    log_skip "PACKAGE_NAME not set and could not auto-detect"
fi

# ── [12] GCP CREDENTIALS (informational) ───────────────────────────────────
log_step "GCP credentials (informational)"

if [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ] && [ -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    log_ok "GOOGLE_APPLICATION_CREDENTIALS set"
elif ls "$PROJECT_ROOT"/central-element-*.json &>/dev/null 2>&1; then
    log_ok "Service account JSON found in repo root"
else
    log_warn "No GCP credentials detected (set GOOGLE_APPLICATION_CREDENTIALS or place SA JSON in repo root)"
fi

# ── [13] KNOWN CAVEATS (per-repo) ─────────────────────────────────────────
# If AGENTS.md exists, print a summary of known caveats for this repo.
# This helps AI agents and new developers understand what to expect.
if [ -f "AGENTS.md" ]; then
    log_step "Known caveats (from AGENTS.md)"
    # Extract lines between "## Known" and the next "##" heading
    CAVEATS=$(sed -n '/^## Known/,/^## /{/^## Known/d;/^## /d;/^$/d;p}' AGENTS.md 2>/dev/null | head -10)
    if [ -n "$CAVEATS" ]; then
        echo -e "  ${YELLOW}${CAVEATS}${NC}"
    else
        log_ok "AGENTS.md present (no known caveats section)"
    fi
fi

# ── SUMMARY ─────────────────────────────────────────────────────────────────
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
if [ "$ISSUES" -gt 0 ]; then
    echo -e "${RED}  $ISSUES issue(s) found${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    [ "$CHECK_ONLY" = true ] && exit 2 || exit 1
else
    echo -e "${GREEN}  Setup complete — $REPO_NAME ready${NC}"
    if [ "$ISOLATED" = true ]; then
        echo -e "${YELLOW}  [ISOLATED MODE] Some tests may fail due to missing workspace deps${NC}"
    fi
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
fi

# ── SOURCE/EXECUTE DETECTION ────────────────────────────────────────────────
if [[ "${BASH_SOURCE[0]:-}" != "${0}" ]] 2>/dev/null || [[ "$ZSH_EVAL_CONTEXT" == *:file:* ]] 2>/dev/null; then
    echo -e "  ${GREEN}venv active in current shell${NC}"
else
    echo -e "  ${YELLOW}Activate venv: source .venv/bin/activate${NC}"
    echo -e "  ${YELLOW}Or re-run with: source scripts/setup.sh${NC}"
fi
echo ""
echo "  Next steps:"
echo "    bash scripts/quality-gates.sh          # Run quality gates"
echo "    bash scripts/quickmerge.sh \"message\"   # Full merge pipeline"
if [ "$ISOLATED" = true ]; then
    echo ""
    echo "  Isolated mode notes:"
    echo "    - Workspace path deps were skipped; install from Artifact Registry if needed"
    echo "    - Cross-repo integration tests will fail — this is expected"
    echo "    - See AGENTS.md (if present) for repo-specific caveats"
fi
echo ""
