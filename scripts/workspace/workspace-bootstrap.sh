#!/usr/bin/env bash
# WORKSPACE BOOTSTRAP — unified-trading-system
#
# Bootstraps a COMPLETE workspace from scratch on a fresh VM or new machine.
# Clones all repos, installs system deps, creates workspace venv, and runs
# setup.sh in dependency order (T0 → T1 → T2 → T3 → services → UIs).
#
# SSOT: unified-trading-pm/scripts/workspace-bootstrap.sh
# Codex: unified-trading-codex/06-coding-standards/setup-standards.md
#
# Prerequisites:
#   - git (with SSH key configured for github.com)
#   - bash 4+ or zsh
#   - macOS (Homebrew) or Linux (apt/yum)
#
# Usage:
#   # Clone this repo first, then run bootstrap:
#   git clone git@github.com:IggyIkenna/unified-trading-pm.git
#   bash unified-trading-pm/scripts/workspace-bootstrap.sh
#
#   # Or with a custom workspace root:
#   bash unified-trading-pm/scripts/workspace-bootstrap.sh /path/to/workspace
#
#   # Check mode (verify existing workspace):
#   bash unified-trading-pm/scripts/workspace-bootstrap.sh --check
#
#   # Skip system deps (if already installed):
#   bash unified-trading-pm/scripts/workspace-bootstrap.sh --skip-system
#
# What this script does:
#   Phase 1 — System dependencies (Python 3.13, uv, ripgrep, jq, basedpyright)
#   Phase 2 — Clone all repos from workspace-manifest.json (skip existing)
#   Phase 3 — Create workspace venv (.venv-workspace)
#   Phase 4 — Run setup.sh per repo in topological order (T0 first)
#   Phase 5 — Verify all repos pass import smoke test
#
# Idempotent. Safe to re-run. Skips repos already cloned and deps already installed.

set -e

# ── COLORS + LOGGING ────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'
log_ok() { echo -e "${GREEN}  [OK] $1${NC}"; }
log_skip() { echo -e "${BLUE}  [SKIP] $1${NC}"; }
log_warn() { echo -e "${YELLOW}  [WARN] $1${NC}"; }
log_fail() { echo -e "${RED}  [FAIL] $1${NC}"; }
log_phase() { echo -e "\n${BOLD}${CYAN}━━━ Phase $1: $2 ━━━${NC}"; }

# ── PARSE ARGUMENTS ─────────────────────────────────────────────────────────
CHECK_ONLY=false
SKIP_SYSTEM=false
WORKSPACE_ROOT=""

for arg in "$@"; do
  case $arg in
    --check) CHECK_ONLY=true ;;
    --skip-system) SKIP_SYSTEM=true ;;
    --help | -h)
      echo "Usage: bash workspace-bootstrap.sh [WORKSPACE_ROOT] [--check|--skip-system|--help]"
      echo ""
      echo "  WORKSPACE_ROOT   Path to workspace (default: parent of this script's repo)"
      echo "  --check          Verify existing workspace without changes"
      echo "  --skip-system    Skip system dependency installation"
      echo "  --help           Show this message"
      exit 0
      ;;
    -*)
      echo "Unknown flag: $arg"
      exit 1
      ;;
    *) WORKSPACE_ROOT="$arg" ;;
  esac
done

# ── RESOLVE PATHS ───────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
PM_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [ -z "$WORKSPACE_ROOT" ]; then
  WORKSPACE_ROOT="$(cd "$PM_ROOT/.." && pwd)"
fi

MANIFEST="$PM_ROOT/workspace-manifest.json"
GITHUB_ORG="IggyIkenna"

echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}  Workspace Bootstrap — unified-trading-system${NC}"
echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "  Workspace: $WORKSPACE_ROOT"
echo -e "  Mode: $([ "$CHECK_ONLY" = true ] && echo 'CHECK' || echo 'BOOTSTRAP')"

# ── PHASE 1: SYSTEM DEPENDENCIES ───────────────────────────────────────────
log_phase 1 "System Dependencies"

REQUIRED_PYTHON="3.13"
SYSTEM_ISSUES=0

check_cmd() {
  local name="$1" cmd="$2" install_hint="$3"
  if command -v "$cmd" &>/dev/null; then
    log_ok "$name ($cmd)"
    return 0
  else
    log_fail "$name not found — $install_hint"
    SYSTEM_ISSUES=$((SYSTEM_ISSUES + 1))
    return 1
  fi
}

install_cmd() {
  local name="$1" cmd="$2" brew_pkg="$3" apt_pkg="$4"
  if command -v "$cmd" &>/dev/null; then
    log_skip "$name already installed"
    return 0
  fi
  if [ "$CHECK_ONLY" = true ] || [ "$SKIP_SYSTEM" = true ]; then
    log_fail "$name not found"
    SYSTEM_ISSUES=$((SYSTEM_ISSUES + 1))
    return 1
  fi
  if command -v brew &>/dev/null; then
    brew install "$brew_pkg" && log_ok "Installed $name via Homebrew" && return 0
  elif command -v apt-get &>/dev/null; then
    sudo apt-get install -y "$apt_pkg" && log_ok "Installed $name via apt" && return 0
  fi
  log_fail "Cannot install $name — install manually"
  SYSTEM_ISSUES=$((SYSTEM_ISSUES + 1))
  return 1
}

# Git
check_cmd "git" "git" "install: brew install git / sudo apt install git"

# Python 3.13
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
  log_ok "Python $REQUIRED_PYTHON ($PYTHON_CMD)"
else
  if [ "$CHECK_ONLY" = true ] || [ "$SKIP_SYSTEM" = true ]; then
    log_fail "Python $REQUIRED_PYTHON not found"
    echo "  Install: brew install python@${REQUIRED_PYTHON}"
    echo "  Or: pyenv install ${REQUIRED_PYTHON}.0 && pyenv local ${REQUIRED_PYTHON}.0"
    SYSTEM_ISSUES=$((SYSTEM_ISSUES + 1))
  else
    echo "  Attempting to install Python ${REQUIRED_PYTHON}..."
    if command -v brew &>/dev/null; then
      brew install "python@${REQUIRED_PYTHON}" && PYTHON_CMD="python${REQUIRED_PYTHON}"
    fi
    if [ -z "$PYTHON_CMD" ]; then
      log_fail "Python $REQUIRED_PYTHON not found and auto-install failed"
      echo "  Install manually: brew install python@${REQUIRED_PYTHON}"
      SYSTEM_ISSUES=$((SYSTEM_ISSUES + 1))
    else
      log_ok "Installed Python $REQUIRED_PYTHON"
    fi
  fi
fi

# uv
install_cmd "uv" "uv" "uv" "uv" || true
if ! command -v uv &>/dev/null && [ -n "$PYTHON_CMD" ] && [ "$CHECK_ONLY" != true ] && [ "$SKIP_SYSTEM" != true ]; then
  "$PYTHON_CMD" -m pip install uv --quiet 2>/dev/null && log_ok "Installed uv via pip" || true
fi

# ripgrep
install_cmd "ripgrep" "rg" "ripgrep" "ripgrep" || true

# jq
install_cmd "jq" "jq" "jq" "jq" || true

if [ "$SYSTEM_ISSUES" -gt 0 ]; then
  log_warn "$SYSTEM_ISSUES system dependency issue(s) — some steps may fail"
fi

# ── PHASE 2: CLONE REPOS ──────────────────────────────────────────────────
log_phase 2 "Clone Repositories"

if [ ! -f "$MANIFEST" ]; then
  log_fail "Manifest not found: $MANIFEST"
  echo "  Clone unified-trading-pm first: git clone git@github.com:${GITHUB_ORG}/unified-trading-pm.git"
  exit 1
fi

# Extract repo names from manifest using Python (jq may not be installed yet)
if command -v jq &>/dev/null; then
  REPOS=$(jq -r '.repositories | keys[]' "$MANIFEST" 2>/dev/null)
elif [ -n "$PYTHON_CMD" ]; then
  REPOS=$("$PYTHON_CMD" -c "
import json, sys
with open('$MANIFEST') as f:
    data = json.load(f)
for name in sorted(data.get('repositories', {}).keys()):
    print(name)
" 2>/dev/null)
else
  log_fail "Need jq or Python to parse manifest"
  exit 1
fi

CLONE_OK=0
CLONE_SKIP=0
CLONE_FAIL=0

cd "$WORKSPACE_ROOT"
for repo in $REPOS; do
  if [ -d "$repo" ]; then
    log_skip "$repo (exists)"
    CLONE_SKIP=$((CLONE_SKIP + 1))
  elif [ "$CHECK_ONLY" = true ]; then
    log_fail "$repo (missing)"
    CLONE_FAIL=$((CLONE_FAIL + 1))
  else
    if git clone "git@github.com:${GITHUB_ORG}/${repo}.git" "$repo" 2>/dev/null; then
      log_ok "$repo"
      CLONE_OK=$((CLONE_OK + 1))
    else
      log_warn "$repo clone failed (may not exist on GitHub yet)"
      CLONE_FAIL=$((CLONE_FAIL + 1))
    fi
  fi
done

echo -e "\n  Cloned: $CLONE_OK | Existing: $CLONE_SKIP | Failed: $CLONE_FAIL"

# ── PHASE 3: WORKSPACE VENV ───────────────────────────────────────────────
log_phase 3 "Workspace Virtual Environment"

WORKSPACE_VENV="$WORKSPACE_ROOT/.venv-workspace"

if [ "$CHECK_ONLY" = true ]; then
  if [ -d "$WORKSPACE_VENV" ]; then
    log_ok ".venv-workspace exists"
  else
    log_fail ".venv-workspace missing"
  fi
elif [ -d "$WORKSPACE_VENV" ]; then
  log_skip ".venv-workspace exists"
else
  if [ -n "$PYTHON_CMD" ] && command -v uv &>/dev/null; then
    uv venv "$WORKSPACE_VENV" --python "$PYTHON_CMD" 2>/dev/null
    log_ok "Created .venv-workspace"
  elif [ -n "$PYTHON_CMD" ]; then
    "$PYTHON_CMD" -m venv "$WORKSPACE_VENV"
    log_ok "Created .venv-workspace (stdlib venv)"
  else
    log_fail "Cannot create venv — Python $REQUIRED_PYTHON not found"
  fi
fi

# Install workspace-level tools and aggregate all repo dependencies
if [ -d "$WORKSPACE_VENV" ] && [ "$CHECK_ONLY" != true ]; then
  source "$WORKSPACE_VENV/bin/activate" 2>/dev/null || source "$WORKSPACE_VENV/Scripts/activate" 2>/dev/null || true
  if command -v uv &>/dev/null; then
    uv pip install ruff basedpyright --quiet 2>/dev/null && log_ok "Workspace tools (ruff, basedpyright)" || log_warn "Tool install failed"
  fi
  # Aggregate and install all repo dependencies into workspace venv
  AGGREGATE_SCRIPT="$WORKSPACE_ROOT/unified-trading-pm/scripts/workspace/aggregate-workspace-deps.py"
  if [ -f "$AGGREGATE_SCRIPT" ] && [ -n "$PYTHON_CMD" ]; then
    echo -e "\n  ${BLUE}Aggregating workspace dependencies...${NC}"
    if "$PYTHON_CMD" "$AGGREGATE_SCRIPT" --resolve 2>&1 | tail -10; then
      log_ok "Workspace deps aggregated (all repos)"
    else
      log_warn "Dependency aggregation had issues (non-fatal)"
    fi
  fi
fi

# ── PHASE 4: REPO SETUP (topological order) ───────────────────────────────
log_phase 4 "Per-Repo Setup (tier order)"

# Topological order from manifest: T0 → T1 → T2 → services → UIs → infra
# Extract using Python for reliability
if [ -n "$PYTHON_CMD" ]; then
  ORDERED_REPOS=$("$PYTHON_CMD" -c "
import json
with open('$MANIFEST') as f:
    data = json.load(f)
topo = data.get('topologicalOrder', {}).get('levels', [])
for level in sorted(topo, key=lambda l: l['level']):
    for repo in level.get('repos', []):
        print(repo)
" 2>/dev/null)
elif command -v jq &>/dev/null; then
  ORDERED_REPOS=$(jq -r '.topologicalOrder.levels | sort_by(.level) | .[].repos[]' "$MANIFEST" 2>/dev/null)
else
  ORDERED_REPOS=$REPOS
fi

SETUP_OK=0
SETUP_SKIP=0
SETUP_FAIL=0

for repo in $ORDERED_REPOS; do
  REPO_PATH="$WORKSPACE_ROOT/$repo"
  if [ ! -d "$REPO_PATH" ]; then
    continue
  fi

  SETUP_SCRIPT="$REPO_PATH/scripts/setup.sh"
  if [ ! -f "$SETUP_SCRIPT" ]; then
    log_skip "$repo (no setup.sh)"
    SETUP_SKIP=$((SETUP_SKIP + 1))
    continue
  fi

  echo -e "\n  ${BLUE}Setting up: $repo${NC}"
  if [ "$CHECK_ONLY" = true ]; then
    if (cd "$REPO_PATH" && WORKSPACE_ROOT="$WORKSPACE_ROOT" bash scripts/setup.sh --check 2>/dev/null); then
      log_ok "$repo"
      SETUP_OK=$((SETUP_OK + 1))
    else
      log_fail "$repo"
      SETUP_FAIL=$((SETUP_FAIL + 1))
    fi
  else
    if (cd "$REPO_PATH" && WORKSPACE_ROOT="$WORKSPACE_ROOT" bash scripts/setup.sh 2>&1 | tail -5); then
      log_ok "$repo"
      SETUP_OK=$((SETUP_OK + 1))
    else
      log_warn "$repo setup failed (non-fatal — continuing)"
      SETUP_FAIL=$((SETUP_FAIL + 1))
    fi
  fi
done

echo -e "\n  Setup OK: $SETUP_OK | Skipped: $SETUP_SKIP | Failed: $SETUP_FAIL"

# ── PHASE 5: IMPORT SMOKE TEST (all repos) ────────────────────────────────
log_phase 5 "Import Smoke Test (all Python repos)"

SMOKE_OK=0
SMOKE_FAIL=0
SMOKE_SKIP=0
SMOKE_FAILURES=""

for repo in $ORDERED_REPOS; do
  REPO_PATH="$WORKSPACE_ROOT/$repo"
  PYPROJECT="$REPO_PATH/pyproject.toml"
  [ -f "$PYPROJECT" ] || continue

  # Auto-detect package name
  PKG=$(grep -A 1 '^\[project\]' "$PYPROJECT" 2>/dev/null | grep '^name' | sed 's/.*= *"//;s/".*//' | tr '-' '_' 2>/dev/null || echo "")
  if [ -z "$PKG" ]; then
    log_skip "$repo (no package name)"
    SMOKE_SKIP=$((SMOKE_SKIP + 1))
    continue
  fi

  SMOKE_PYTHON="$REPO_PATH/.venv/bin/python"
  [ -f "$SMOKE_PYTHON" ] || SMOKE_PYTHON="${PYTHON_CMD:-python3}"

  if $SMOKE_PYTHON -c "import $PKG" 2>/dev/null; then
    SMOKE_OK=$((SMOKE_OK + 1))
  else
    log_fail "$repo (import $PKG)"
    SMOKE_FAIL=$((SMOKE_FAIL + 1))
    SMOKE_FAILURES="$SMOKE_FAILURES  - $repo: import $PKG\n"
  fi
done

echo -e "\n  Import OK: $SMOKE_OK | Failed: $SMOKE_FAIL | Skipped: $SMOKE_SKIP"

if [ -n "$SMOKE_FAILURES" ]; then
  echo -e "\n  ${RED}Failed imports:${NC}"
  echo -e "$SMOKE_FAILURES"
fi

# ── PHASE 6: CURSOR/CLAUDE SYMLINKS ───────────────────────────────────────
log_phase 6 "IDE Symlinks (Cursor rules + plans)"

bash "$SCRIPT_DIR/setup-cursor-rules-symlink.sh" && log_ok "Cursor rules symlink ready" || log_warn "Cursor rules symlink failed (run manually)"
bash "$SCRIPT_DIR/setup-cursor-plans-symlink.sh" && log_ok "Cursor plans symlink ready" || log_warn "Cursor plans symlink failed (run manually)"

# ── FINAL SUMMARY ─────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
TOTAL_ISSUES=$((SYSTEM_ISSUES + CLONE_FAIL + SETUP_FAIL + SMOKE_FAIL))
if [ "$TOTAL_ISSUES" -gt 0 ]; then
  echo -e "${BOLD}  Bootstrap complete with $TOTAL_ISSUES issue(s)${NC}"
else
  echo -e "${BOLD}${GREEN}  Bootstrap complete — workspace ready${NC}"
fi
echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  Workspace root: $WORKSPACE_ROOT"
echo "  Activate venv:  source $WORKSPACE_VENV/bin/activate"
echo ""
echo "  Next steps:"
echo "    1. source $WORKSPACE_VENV/bin/activate"
echo "    2. cd <any-repo> && bash scripts/setup.sh --check"
echo "    3. bash scripts/quality-gates.sh       # QG for a specific repo"
echo "    4. bash scripts/quickmerge.sh \"msg\"    # Merge workflow"
echo ""
echo "  For a single repo in isolation:"
echo "    cd <repo> && bash scripts/setup.sh --isolated"
echo ""
echo "  To re-verify the whole workspace:"
echo "    bash unified-trading-pm/scripts/workspace-bootstrap.sh --check"
echo ""
