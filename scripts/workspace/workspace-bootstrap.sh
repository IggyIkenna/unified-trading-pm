#!/usr/bin/env bash
# WORKSPACE BOOTSTRAP — unified-trading-system
#
# Bootstraps a COMPLETE workspace from scratch on a fresh machine.
# Self-contained — requires only git + bash. Downloads unified-trading-pm
# first if not already present, then reads workspace-manifest.json for
# everything else.
#
# SSOT: docs/repo-management/CI-CD-FLOW.md (this script wraps it)
# Codex: unified-trading-codex/06-coding-standards/setup-standards.md
#
# Prerequisites (only these, nothing else):
#   - git (with SSH key configured for github.com)
#   - bash 4+ or zsh
#   - macOS (Homebrew) or Linux (apt/yum)
#
# Usage (run this from your chosen workspace directory):
#   mkdir -p ~/repos/unified-trading-system-repos
#   cd ~/repos/unified-trading-system-repos
#   bash <(curl -fsSL https://raw.githubusercontent.com/IggyIkenna/unified-trading-pm/main/scripts/workspace/workspace-bootstrap.sh)
#
#   # Or if you already have PM cloned:
#   bash unified-trading-pm/scripts/workspace/workspace-bootstrap.sh
#
#   # Custom workspace root:
#   bash unified-trading-pm/scripts/workspace/workspace-bootstrap.sh /path/to/workspace
#
#   # Check mode (verify without changes):
#   bash unified-trading-pm/scripts/workspace/workspace-bootstrap.sh --check
#
#   # Preserve existing repos (skip delete + re-clone):
#   bash unified-trading-pm/scripts/workspace/workspace-bootstrap.sh --skip-fresh
#
#   # Skip system deps (if already installed):
#   bash unified-trading-pm/scripts/workspace/workspace-bootstrap.sh --skip-system
#
# What this script does:
#   Phase 0 — Clone unified-trading-pm if not already present (self-seeding)
#   Phase 1 — System dependencies (Python 3.13, uv, ripgrep, jq)
#   Phase 2 — Fresh clone all repos from workspace-manifest.json
#             (deletes existing dirs and re-clones for a clean state;
#              use --skip-fresh to preserve existing repos instead)
#   Phase 3 — Version alignment (run-version-alignment.sh --fix)
#   Phase 4 — Create workspace venv (.venv-workspace) via setup-workspace-venv.sh
#   Phase 5 — Invoke run-all-setup.sh (CI/CD Phase 2)
#   Phase 6 — Import smoke test across all Python repos

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
SKIP_FRESH=false
USE_HTTPS=false
WORKSPACE_ROOT=""

for arg in "$@"; do
  case $arg in
    --check) CHECK_ONLY=true ;;
    --skip-system) SKIP_SYSTEM=true ;;
    --skip-fresh) SKIP_FRESH=true ;;
    --https) USE_HTTPS=true ;;
    --help | -h)
      echo "Usage: bash workspace-bootstrap.sh [WORKSPACE_ROOT] [flags]"
      echo ""
      echo "  WORKSPACE_ROOT   Path to workspace (default: current directory)"
      echo "  --check          Verify existing workspace without changes"
      echo "  --skip-system    Skip system dependency installation"
      echo "  --skip-fresh     Preserve existing repo dirs (skip delete + re-clone)"
      echo "  --https          Clone via HTTPS instead of SSH (use with gh auth login or a PAT)"
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
GITHUB_ORG="IggyIkenna"

# Build clone URL based on protocol flag
clone_url() { # clone_url <repo>
  if [ "$USE_HTTPS" = true ]; then
    echo "https://github.com/${GITHUB_ORG}/${1}.git"
  else
    echo "git@github.com:${GITHUB_ORG}/${1}.git"
  fi
}

# Support running from workspace root (not from inside PM).
# Detect whether we are running from inside an already-cloned PM or from workspace root.
if [ -z "$WORKSPACE_ROOT" ]; then
  # If this script is inside unified-trading-pm/scripts/workspace/, workspace root is two levels up
  if echo "$SCRIPT_DIR" | grep -q "unified-trading-pm/scripts/workspace"; then
    WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
  else
    # Running via curl pipe or from workspace root directly
    WORKSPACE_ROOT="$(pwd)"
  fi
fi

PM_ROOT="$WORKSPACE_ROOT/unified-trading-pm"
MANIFEST="$PM_ROOT/workspace-manifest.json"

echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}  Workspace Bootstrap — unified-trading-system${NC}"
echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "  Workspace: $WORKSPACE_ROOT"
echo -e "  Mode: $([ "$CHECK_ONLY" = true ] && echo 'CHECK' || ([ "$SKIP_FRESH" = true ] && echo 'BOOTSTRAP (preserve existing)' || echo 'BOOTSTRAP (fresh clone)'))"

# ── PRE-FLIGHT: AUTH + ACCESS CHECKS ─────────────────────────────────────────
# Verify all required credentials are in place BEFORE doing any work.
# These checks are informational — auth issues are reported but not fatal so the
# developer can resolve them in one shot from the summary at the end.
# Required:
#   1. GitHub access — SSH key or HTTPS (gh auth login) with access to IggyIkenna org
#   2. GCP auth     — gcloud ADC configured for datadodo@gmail.com (project: odum-research)
#   3. act secrets  — ~/.act-secrets present for local GitHub Actions runs
GITHUB_ORG_CHECK="IggyIkenna"
REQUIRED_GCP_ACCOUNT="datadodo@gmail.com"
REQUIRED_GCP_PROJECT="odum-research"
REQUIRED_ACT_SECRETS="$HOME/.act-secrets"
AUTH_ISSUES=0

log_phase "PRE" "Auth & Access Checks"

# 1. GitHub access
echo -e "  Checking GitHub access to ${GITHUB_ORG_CHECK}..."
GH_AUTH_OK=false
if [ "$USE_HTTPS" = true ]; then
  if command -v gh &>/dev/null && gh auth status &>/dev/null 2>&1; then
    GH_USER=$(gh api user --jq '.login' 2>/dev/null || echo "unknown")
    # Check org membership
    if gh api "orgs/${GITHUB_ORG_CHECK}/members/${GH_USER}" &>/dev/null 2>&1; then
      log_ok "GitHub HTTPS: authenticated as $GH_USER, member of ${GITHUB_ORG_CHECK}"
      GH_AUTH_OK=true
    else
      log_warn "GitHub HTTPS: authenticated as $GH_USER but NOT a member of ${GITHUB_ORG_CHECK}"
      echo -e "  ${YELLOW}Fix:${NC}"
      echo -e "    1. Ask an admin to add $GH_USER to the IggyIkenna org"
      echo -e "    2. Or request the same repo access that CosmicTrader has"
      AUTH_ISSUES=$((AUTH_ISSUES + 1))
    fi
  else
    log_fail "GitHub HTTPS: not authenticated (gh auth status failed)"
    echo -e "  ${RED}Fix:${NC}"
    echo -e "    gh auth login    (follow prompts, select HTTPS)"
    echo -e "    Then re-run bootstrap"
    AUTH_ISSUES=$((AUTH_ISSUES + 1))
  fi
else
  # SSH mode: test connection to github.com
  SSH_OUTPUT=$(ssh -T git@github.com 2>&1 || true)
  if echo "$SSH_OUTPUT" | grep -q "successfully authenticated"; then
    GH_SSH_USER=$(echo "$SSH_OUTPUT" | grep -oE 'Hi [^!]+' | sed 's/Hi //')
    # Check org access by attempting to list repos (requires gh CLI or API)
    if command -v gh &>/dev/null; then
      GH_ACCESS=$(gh api "orgs/${GITHUB_ORG_CHECK}/repos" --jq '.[0].name' 2>/dev/null || echo "")
      if [ -n "$GH_ACCESS" ]; then
        log_ok "GitHub SSH: authenticated as $GH_SSH_USER, org access confirmed"
        GH_AUTH_OK=true
      else
        log_warn "GitHub SSH: key works but could not confirm ${GITHUB_ORG_CHECK} org access"
        echo -e "  ${YELLOW}Fix:${NC} Ask admin to verify $GH_SSH_USER has same repo access as CosmicTrader"
        AUTH_ISSUES=$((AUTH_ISSUES + 1))
      fi
    else
      log_ok "GitHub SSH: key authenticated as $GH_SSH_USER (install gh CLI to verify org access)"
      GH_AUTH_OK=true
    fi
  else
    log_fail "GitHub SSH: authentication failed"
    echo -e "  ${RED}Fix:${NC}"
    echo -e "    ssh-keygen -t ed25519 -C \"your@email.com\"   # generate key"
    echo -e "    cat ~/.ssh/id_ed25519.pub                     # copy to GitHub Settings > SSH keys"
    echo -e "    ssh -T git@github.com                         # verify"
    echo -e "    Or use --https flag with: gh auth login"
    AUTH_ISSUES=$((AUTH_ISSUES + 1))
  fi
fi

# 2. GCP auth (gcloud ADC)
echo -e "  Checking GCP auth (required: ${REQUIRED_GCP_ACCOUNT})..."
if command -v gcloud &>/dev/null; then
  GCP_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null | head -1 || echo "")
  GCP_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")
  ADC_FILE="$HOME/.config/gcloud/application_default_credentials.json"
  if [ "$GCP_ACCOUNT" = "$REQUIRED_GCP_ACCOUNT" ] && [ -f "$ADC_FILE" ]; then
    log_ok "GCP: authenticated as $GCP_ACCOUNT, ADC configured (project: ${GCP_PROJECT:-unset})"
    if [ "$GCP_PROJECT" != "$REQUIRED_GCP_PROJECT" ]; then
      log_warn "GCP project is '${GCP_PROJECT}', expected '${REQUIRED_GCP_PROJECT}'"
      echo -e "  ${YELLOW}Fix:${NC} gcloud config set project ${REQUIRED_GCP_PROJECT}"
    fi
  elif [ -n "$GCP_ACCOUNT" ] && [ "$GCP_ACCOUNT" != "$REQUIRED_GCP_ACCOUNT" ]; then
    log_warn "GCP: authenticated as $GCP_ACCOUNT — expected ${REQUIRED_GCP_ACCOUNT}"
    echo -e "  ${YELLOW}Fix:${NC}"
    echo -e "    gcloud auth login --account ${REQUIRED_GCP_ACCOUNT}"
    echo -e "    gcloud auth application-default login --account ${REQUIRED_GCP_ACCOUNT}"
    echo -e "    gcloud config set project ${REQUIRED_GCP_PROJECT}"
    AUTH_ISSUES=$((AUTH_ISSUES + 1))
  elif [ ! -f "$ADC_FILE" ]; then
    log_warn "GCP: account OK but Application Default Credentials not configured"
    echo -e "  ${YELLOW}Fix:${NC}"
    echo -e "    gcloud auth application-default login"
    AUTH_ISSUES=$((AUTH_ISSUES + 1))
  else
    log_fail "GCP: gcloud found but not authenticated"
    echo -e "  ${RED}Fix:${NC}"
    echo -e "    gcloud auth login --account ${REQUIRED_GCP_ACCOUNT}"
    echo -e "    gcloud auth application-default login"
    echo -e "    gcloud config set project ${REQUIRED_GCP_PROJECT}"
    AUTH_ISSUES=$((AUTH_ISSUES + 1))
  fi
else
  log_warn "GCP: gcloud not installed — install after bootstrap for GCP service access"
  echo -e "  ${YELLOW}Fix:${NC}"
  echo -e "    macOS: brew install --cask google-cloud-sdk"
  echo -e "    Linux: https://cloud.google.com/sdk/docs/install"
  echo -e "    Then:  gcloud auth login --account ${REQUIRED_GCP_ACCOUNT}"
  echo -e "           gcloud auth application-default login"
  echo -e "           gcloud config set project ${REQUIRED_GCP_PROJECT}"
  AUTH_ISSUES=$((AUTH_ISSUES + 1))
fi

# 3. act secrets file
echo -e "  Checking act secrets (${REQUIRED_ACT_SECRETS})..."
if [ -f "$REQUIRED_ACT_SECRETS" ]; then
  SECRET_COUNT=$(grep -c "=" "$REQUIRED_ACT_SECRETS" 2>/dev/null || echo 0)
  log_ok "act secrets: $REQUIRED_ACT_SECRETS ($SECRET_COUNT entries)"
else
  log_warn "act secrets not found at $REQUIRED_ACT_SECRETS"
  echo -e "  ${YELLOW}Fix:${NC}"
  echo -e "    cp unified-trading-pm/docs/act-secrets-template ~/.act-secrets"
  echo -e "    # Then fill in your ANTHROPIC_API_KEY, GH_PAT, GCP credentials"
  echo -e "  (Required for local GitHub Actions runs via 'act')"
  AUTH_ISSUES=$((AUTH_ISSUES + 1))
fi

if [ "$AUTH_ISSUES" -gt 0 ]; then
  echo ""
  log_warn "$AUTH_ISSUES auth issue(s) detected — continuing bootstrap (fix before running services)"
else
  log_ok "All auth checks passed"
fi
echo ""

# ── PHASE 0: SELF-SEED — clone unified-trading-pm if not present ─────────────
# This is the only step that doesn't require PM to already be cloned.
# All subsequent phases read workspace-manifest.json from PM.
log_phase 0 "Seed — unified-trading-pm"

cd "$WORKSPACE_ROOT"
if [ -d "$PM_ROOT/.git" ]; then
  if [ "$CHECK_ONLY" = true ]; then
    log_ok "unified-trading-pm present"
  else
    # Pull latest manifest so Phase 2 uses current repo list
    echo -e "  Pulling latest unified-trading-pm..."
    git -C "$PM_ROOT" fetch origin --quiet 2>/dev/null || true
    git -C "$PM_ROOT" reset --hard origin/main --quiet 2>/dev/null \
      && log_ok "unified-trading-pm updated to origin/main" \
      || log_warn "Could not pull unified-trading-pm — using local state"
  fi
elif [ "$CHECK_ONLY" = true ]; then
  log_fail "unified-trading-pm missing from $WORKSPACE_ROOT"
  exit 1
else
  echo -e "  Cloning unified-trading-pm ($([ "$USE_HTTPS" = true ] && echo 'HTTPS' || echo 'SSH'))..."
  if git clone "$(clone_url unified-trading-pm)" "$PM_ROOT" 2>/dev/null; then
    log_ok "unified-trading-pm cloned"
  else
    if [ "$USE_HTTPS" = true ]; then
      log_fail "Failed to clone unified-trading-pm — run: gh auth login  (or set a PAT in git credentials)"
    else
      log_fail "Failed to clone unified-trading-pm — check SSH key: ssh -T git@github.com"
    fi
    exit 1
  fi
fi

if [ ! -f "$MANIFEST" ]; then
  log_fail "workspace-manifest.json not found at $MANIFEST"
  exit 1
fi
log_ok "manifest: $MANIFEST"

# Create a convenience symlink at workspace root so future runs are just: bash bootstrap.sh
# The symlink is relative (portable across machines) and outside any git repo.
BOOTSTRAP_SYMLINK="$WORKSPACE_ROOT/bootstrap.sh"
if [ "$CHECK_ONLY" != true ] && [ ! -L "$BOOTSTRAP_SYMLINK" ]; then
  ln -sf unified-trading-pm/scripts/workspace/workspace-bootstrap.sh "$BOOTSTRAP_SYMLINK"
  log_ok "bootstrap.sh symlink created (future runs: bash bootstrap.sh)"
fi

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

# ── PHASE 2: CLONE REPOS (fresh by default) ───────────────────────────────
# Default: delete existing repo dirs and re-clone for a guaranteed clean state.
# Use --skip-fresh to preserve existing dirs (faster, for incremental runs).
# unified-trading-pm itself is never deleted here — it was handled in Phase 0.
log_phase 2 "Clone Repositories ($([ "$SKIP_FRESH" = true ] && echo 'preserve existing' || echo 'fresh — delete + re-clone'))"

# Extract repo names from manifest using Python (jq may not be available yet)
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
  # Never delete unified-trading-pm — already seeded in Phase 0
  if [ "$repo" = "unified-trading-pm" ]; then
    log_skip "$repo (seeded in Phase 0)"
    CLONE_SKIP=$((CLONE_SKIP + 1))
    continue
  fi

  if [ "$CHECK_ONLY" = true ]; then
    [ -d "$repo/.git" ] && log_ok "$repo" || { log_fail "$repo (missing)"; CLONE_FAIL=$((CLONE_FAIL + 1)); }
    continue
  fi

  # Fresh mode (default): delete and re-clone
  if [ "$SKIP_FRESH" = false ] && [ -d "$repo" ]; then
    echo -e "  ${YELLOW}[FRESH]${NC} $repo — removing and re-cloning..."
    rm -rf "$repo"
  fi

  if [ -d "$repo/.git" ]; then
    log_skip "$repo (exists, --skip-fresh)"
    CLONE_SKIP=$((CLONE_SKIP + 1))
  else
    if git clone "$(clone_url "$repo")" "$repo" --quiet 2>/dev/null; then
      log_ok "$repo"
      CLONE_OK=$((CLONE_OK + 1))
    else
      log_warn "$repo clone failed (may not exist on GitHub yet)"
      CLONE_FAIL=$((CLONE_FAIL + 1))
    fi
  fi
done

echo -e "\n  Cloned: $CLONE_OK | Preserved: $CLONE_SKIP | Failed: $CLONE_FAIL"

# Parse topological order from manifest for smoke test (Phase 6)
ORDERED_REPOS=""
if command -v python3 &>/dev/null; then
  ORDERED_REPOS=$(python3 -c "
import json
with open('$MANIFEST') as f:
    data = json.load(f)
levels = data.get('topologicalOrder', {}).get('levels', [])
for level in sorted(levels, key=lambda l: l.get('level', 999)):
    for repo in level.get('repos', []):
        print(repo)
" 2>/dev/null || echo "")
fi
[ -z "$ORDERED_REPOS" ] && ORDERED_REPOS="$REPOS"

# ── PHASE 3: VERSION ALIGNMENT ────────────────────────────────────────────
log_phase 3 "Version Alignment"

if [ "$CHECK_ONLY" = true ]; then
  if (cd "$WORKSPACE_ROOT" && bash "$PM_ROOT/scripts/repo-management/run-version-alignment.sh" 2>&1 | tail -20); then
    log_ok "Version alignment: all deps in sync"
  else
    log_warn "Version alignment found issues (run: bash unified-trading-pm/scripts/repo-management/run-version-alignment.sh --fix)"
  fi
else
  echo -e "  Running version alignment --fix across all repos..."
  if (cd "$WORKSPACE_ROOT" && bash "$PM_ROOT/scripts/repo-management/run-version-alignment.sh" --fix 2>&1 | grep -E '^\s+\[(OK|WARN|FAIL|SKIP)\]|━|Fixing|up to date' | tail -30); then
    log_ok "Version alignment complete"
  else
    log_warn "Version alignment had issues (non-fatal — continuing)"
  fi
fi

# ── PHASE 4: WORKSPACE VENV ───────────────────────────────────────────────
# Delegates entirely to setup-workspace-venv.sh — single source of truth for
# workspace venv creation, pinned tool install (ruff==0.15.0, basedpyright==1.38.2),
# and editable installs from workspace-manifest.json in topological order.
# sync-workspace-venv.sh is a thin wrapper around the same script for day-to-day refresh.
log_phase 4 "Workspace Virtual Environment"

WORKSPACE_VENV="$WORKSPACE_ROOT/.venv-workspace"
SETUP_VENV_SCRIPT="$PM_ROOT/scripts/setup-workspace-venv.sh"

if [ ! -f "$SETUP_VENV_SCRIPT" ]; then
  log_fail "setup-workspace-venv.sh not found at $SETUP_VENV_SCRIPT"
else
  if [ "$CHECK_ONLY" = true ]; then
    bash "$SETUP_VENV_SCRIPT" --check 2>&1 | grep -E '^\s+\[(OK|WARN|FAIL|SKIP)\]' || true
  else
    bash "$SETUP_VENV_SCRIPT" 2>&1 | grep -E '^\s+\[(OK|WARN|FAIL|SKIP)\]|━' || true
    [ -d "$WORKSPACE_VENV" ] && log_ok ".venv-workspace ready" || log_warn ".venv-workspace setup had issues (check above)"
  fi
fi

# ── PHASE 5: REPO SETUP (CI/CD Phase 2) ─────────────────────────────────────
# Wraps docs/repo-management/CI-CD-FLOW.md — invokes run-all-setup.sh
SETUP_FAIL=0
log_phase 5 "Per-Repo Setup (CI/CD Phase 2)"

if [ "$CHECK_ONLY" = true ]; then
  if (cd "$WORKSPACE_ROOT" && bash "$PM_ROOT/scripts/repo-management/run-all-setup.sh" --check 2>&1 | tail -20); then
    log_ok "Setup check passed (all repos)"
  else
    log_fail "Setup check failed"
    exit 1
  fi
else
  echo -e "\n  ${BLUE}Invoking run-all-setup.sh --rollout-first (CI/CD Phase 2)${NC}"
  if (cd "$WORKSPACE_ROOT" && bash "$PM_ROOT/scripts/repo-management/run-all-setup.sh" --rollout-first 2>&1 | tail -30); then
    log_ok "Setup complete (all repos)"
  else
    SETUP_FAIL=1
    log_warn "Setup had issues (non-fatal — continuing)"
  fi
fi

# ── PHASE 6: IMPORT SMOKE TEST (all repos) ────────────────────────────────
log_phase 6 "Import Smoke Test (all Python repos)"

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

# ── FINAL SUMMARY ─────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
TOTAL_ISSUES=$((AUTH_ISSUES + SYSTEM_ISSUES + CLONE_FAIL + SETUP_FAIL + SMOKE_FAIL))
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
echo "    bash unified-trading-pm/scripts/workspace/workspace-bootstrap.sh --check"
echo ""
