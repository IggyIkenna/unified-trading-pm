#!/usr/bin/env bash
# WORKSPACE BOOTSTRAP — unified-trading-system
#
# Bootstraps a COMPLETE workspace from scratch on a fresh machine.
# Self-contained — requires only git + bash. Downloads unified-trading-pm
# first if not already present, then reads workspace-manifest.json for
# everything else.
#
# SSOT: docs/repo-management/CI-CD-FLOW.md (this script wraps it)
# Codex: unified-trading-pm/codex/06-coding-standards/setup-standards.md (codex repo archived → folded into PM)
#
# Prerequisites (only these, nothing else):
#   - git (with SSH key configured for github.com, OR use --https)
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
#   # Use HTTPS instead of SSH (no SSH key required):
#   bash unified-trading-pm/scripts/workspace/workspace-bootstrap.sh --https
#
#   # Preserve existing repos (skip delete + re-clone):
#   bash unified-trading-pm/scripts/workspace/workspace-bootstrap.sh --skip-fresh
#
#   # Skip system deps (if already installed):
#   bash unified-trading-pm/scripts/workspace/workspace-bootstrap.sh --skip-system
#
#   # Skip pre-flight auth checks:
#   bash unified-trading-pm/scripts/workspace/workspace-bootstrap.sh --skip-auth-check
#
# What this script does:
#   Pre-flight — Auth checks: GitHub org access, GCP ADC, act secrets
#   Phase 0    — Clone unified-trading-pm if not already present (self-seeding)
#   Phase 1    — System dependencies (Python 3.13, uv, ripgrep, jq)
#   Phase 2    — Clone all repos from workspace-manifest.json
#              (fresh clone by default; --skip-fresh to preserve existing dirs)
#   Phase 3    — Version alignment (run-version-alignment.sh --fix)
#   Phase 4    — Create/update workspace venv (.venv-workspace) via setup-workspace-venv.sh
#   Phase 5    — Invoke run-all-setup.sh per-repo setup (CI/CD Phase 2)
#   Phase 6    — Import smoke test across all Python repos
#
# Idempotent. Safe to re-run.

set -e

# ── COLORS + LOGGING ────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'
log_ok()   { echo -e "${GREEN}  [OK]   $1${NC}"; }
log_skip() { echo -e "${BLUE}  [SKIP] $1${NC}"; }
log_warn() { echo -e "${YELLOW}  [WARN] $1${NC}"; }
log_fail() { echo -e "${RED}  [FAIL] $1${NC}"; }
log_info() { echo -e "${BLUE}  [INFO] $1${NC}"; }
log_phase() { echo -e "\n${BOLD}${CYAN}━━━ Phase $1: $2 ━━━${NC}"; }

# ── PARSE ARGUMENTS ─────────────────────────────────────────────────────────
CHECK_ONLY=false
SKIP_SYSTEM=false
SKIP_FRESH=false
SKIP_AUTH_CHECK=false
USE_HTTPS=false
WORKSPACE_ROOT=""

for arg in "$@"; do
  case $arg in
    --check)           CHECK_ONLY=true ;;
    --skip-system)     SKIP_SYSTEM=true ;;
    --skip-fresh)      SKIP_FRESH=true ;;
    --skip-auth-check) SKIP_AUTH_CHECK=true ;;
    --https)           USE_HTTPS=true ;;
    --help | -h)
      echo "Usage: bash workspace-bootstrap.sh [WORKSPACE_ROOT] [options]"
      echo ""
      echo "  WORKSPACE_ROOT      Path to workspace (default: parent of this script's repo)"
      echo "  --check             Verify existing workspace without changes"
      echo "  --https             Use HTTPS clone URLs (no SSH key required)"
      echo "  --skip-fresh        Preserve existing repo dirs (skip re-clone)"
      echo "  --skip-system       Skip system dependency installation"
      echo "  --skip-auth-check   Skip pre-flight auth verification"
      echo "  --help              Show this message"
      echo ""
      echo "Bootstrap URL (from any empty directory):"
      echo "  bash <(curl -fsSL https://raw.githubusercontent.com/IggyIkenna/unified-trading-pm/main/scripts/workspace/workspace-bootstrap.sh)"
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
# When run via bash <(curl ...), BASH_SOURCE[0] may be empty or /dev/fd/XX.
# We detect this and fall back to CWD-relative paths.
SCRIPT_SOURCE="${BASH_SOURCE[0]:-$0}"
if [[ "$SCRIPT_SOURCE" == /dev/fd/* ]] || [[ "$SCRIPT_SOURCE" == "-bash" ]] || [[ "$SCRIPT_SOURCE" == "bash" ]]; then
  # Running via process substitution — script lives in unified-trading-pm
  SCRIPT_DIR_RESOLVED="$(pwd)/unified-trading-pm/scripts/workspace"
  PM_ROOT_RESOLVED="$(pwd)/unified-trading-pm"
else
  SCRIPT_DIR_RESOLVED="$(cd "$(dirname "$SCRIPT_SOURCE")" && pwd)"
  PM_ROOT_RESOLVED="$(cd "$SCRIPT_DIR_RESOLVED/../.." && pwd)"
fi

if [ -z "$WORKSPACE_ROOT" ]; then
  # When PM is already cloned: parent of PM root
  # When run via curl (PM not yet cloned): CWD
  if [ -d "$PM_ROOT_RESOLVED" ]; then
    WORKSPACE_ROOT="$(cd "$PM_ROOT_RESOLVED/.." && pwd)"
  else
    WORKSPACE_ROOT="$(pwd)"
  fi
fi

GITHUB_ORG="IggyIkenna"

clone_url() {
  local repo="$1"
  if [ "$USE_HTTPS" = true ]; then
    echo "https://github.com/${GITHUB_ORG}/${repo}.git"
  else
    echo "git@github.com:${GITHUB_ORG}/${repo}.git"
  fi
}

echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}  Workspace Bootstrap — unified-trading-system${NC}"
echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "  Workspace : $WORKSPACE_ROOT"
echo -e "  Protocol  : $([ "$USE_HTTPS" = true ] && echo 'HTTPS' || echo 'SSH')"
echo -e "  Mode      : $([ "$CHECK_ONLY" = true ] && echo 'CHECK' || echo 'BOOTSTRAP')"

# ── PRE-FLIGHT: AUTH & ACCESS CHECKS ────────────────────────────────────────
GITHUB_ORG_CHECK="IggyIkenna"
REQUIRED_GCP_ACCOUNT="datadodo@gmail.com"
REQUIRED_GCP_PROJECT="odum-research"
REQUIRED_ACT_SECRETS="$HOME/.act-secrets"
AUTH_ISSUES=0

if [ "$SKIP_AUTH_CHECK" = false ] && [ "$CHECK_ONLY" = false ]; then
  log_phase "PRE" "Auth & Access Checks"

  # 0. Load a workflow-capable GH_TOKEN (GH_PAT from Secret Manager) so gh + git can edit
  #    .github/workflows. The keyring login token lacks 'workflow' scope — see
  #    scripts/workspace/load-gh-token.sh + CLAUDE.md § "Workflow-capable GH_TOKEN everywhere".
  # 0a. Proactively refresh the .act-secrets GH_PAT cache from Secret Manager so it rarely
  #     goes stale (P2 493) — complements load-gh-token.sh's runtime validity-probe. No-op if
  #     SM is unavailable (leaves any existing file untouched).
  if [ -f "${WORKSPACE_ROOT:-..}/unified-trading-pm/scripts/workspace/generate-act-secrets.sh" ]; then
    bash "${WORKSPACE_ROOT:-..}/unified-trading-pm/scripts/workspace/generate-act-secrets.sh" --refresh >/dev/null 2>&1 || true
  fi
  if [ -f "${WORKSPACE_ROOT:-..}/unified-trading-pm/scripts/workspace/load-gh-token.sh" ]; then
    # shellcheck disable=SC1091
    source "${WORKSPACE_ROOT:-..}/unified-trading-pm/scripts/workspace/load-gh-token.sh" || true
    [ -n "${GH_TOKEN:-}" ] && log_ok "GH_TOKEN loaded (workflow-capable PAT)" || log_warn "GH_TOKEN not loaded — workflow edits via gh/HTTPS will be blocked"
  fi

  # 1. GitHub — SSH connectivity or HTTPS token
  if [ "$USE_HTTPS" = true ]; then
    if command -v gh &>/dev/null; then
      if gh auth status &>/dev/null; then
        log_ok "GitHub CLI authenticated (HTTPS mode)"
      else
        log_fail "GitHub CLI not authenticated — run: gh auth login"
        echo "  Required for HTTPS clone + org API checks"
        AUTH_ISSUES=$((AUTH_ISSUES + 1))
      fi
    else
      log_warn "GitHub CLI (gh) not found — HTTPS clones may fail for private repos"
      echo "  Install: brew install gh  OR  apt install gh"
      echo "  Then:    gh auth login"
    fi
  else
    if ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
      log_ok "GitHub SSH authenticated"
    else
      log_fail "GitHub SSH not authenticated"
      echo "  Run: ssh -T git@github.com  to diagnose"
      echo "  Fix: Add ~/.ssh/id_ed25519.pub to GitHub → Settings → SSH keys"
      echo "  Or:  Use --https flag for token-based cloning"
      AUTH_ISSUES=$((AUTH_ISSUES + 1))
    fi
  fi

  # 2. GitHub org membership — verify access parity with ${GITHUB_ORG_CHECK}
  if command -v gh &>/dev/null && gh auth status &>/dev/null 2>&1; then
    GH_USER=$(gh api user --jq '.login' 2>/dev/null || echo "")
    if [ -n "$GH_USER" ]; then
      # Check org membership
      ORG_STATUS=$(gh api "orgs/${GITHUB_ORG_CHECK}/members/${GH_USER}" --silent 2>&1 && echo "member" || echo "not-member")
      if [ "$ORG_STATUS" = "member" ]; then
        log_ok "GitHub org ${GITHUB_ORG_CHECK} membership confirmed (@${GH_USER})"
      else
        log_fail "Not a member of GitHub org: ${GITHUB_ORG_CHECK} (@${GH_USER})"
        echo "  Contact: @IggyIkenna to request org membership"
        echo "  Required: read access to all ${GITHUB_ORG_CHECK}/* repos"
        AUTH_ISSUES=$((AUTH_ISSUES + 1))
      fi
    else
      log_warn "Could not determine GitHub username — skipping org check"
    fi
  else
    log_info "GitHub CLI not available — skipping org membership check"
    log_info "Ensure your SSH key or token has access to: github.com/${GITHUB_ORG_CHECK}/*"
  fi

  # 3. GCP Application Default Credentials (ADC)
  if command -v gcloud &>/dev/null; then
    ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null | head -1 || echo "")
    if [ "$ACTIVE_ACCOUNT" = "$REQUIRED_GCP_ACCOUNT" ]; then
      log_ok "GCP ADC active account: $REQUIRED_GCP_ACCOUNT"
    elif [ -n "$ACTIVE_ACCOUNT" ]; then
      log_fail "GCP ADC active account: $ACTIVE_ACCOUNT (expected: $REQUIRED_GCP_ACCOUNT)"
      echo "  Fix: gcloud auth login --update-adc"
      echo "  Then: gcloud config set account $REQUIRED_GCP_ACCOUNT"
      AUTH_ISSUES=$((AUTH_ISSUES + 1))
    else
      log_fail "No GCP ADC credentials found"
      echo "  Fix: gcloud auth application-default login"
      echo "  Account required: $REQUIRED_GCP_ACCOUNT"
      AUTH_ISSUES=$((AUTH_ISSUES + 1))
    fi

    ACTIVE_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")
    if [ "$ACTIVE_PROJECT" = "$REQUIRED_GCP_PROJECT" ]; then
      log_ok "GCP project: $REQUIRED_GCP_PROJECT"
    else
      log_fail "GCP project: $ACTIVE_PROJECT (expected: $REQUIRED_GCP_PROJECT)"
      echo "  Fix: gcloud config set project $REQUIRED_GCP_PROJECT"
      AUTH_ISSUES=$((AUTH_ISSUES + 1))
    fi
  else
    log_warn "gcloud CLI not found — GCP auth checks skipped"
    echo "  Install: https://cloud.google.com/sdk/docs/install"
    echo "  Required GCP account: $REQUIRED_GCP_ACCOUNT"
    echo "  Required GCP project: $REQUIRED_GCP_PROJECT"
  fi

  # 4. AWS CLI credentials
  if command -v aws &>/dev/null; then
    AWS_IDENTITY=$(aws sts get-caller-identity --output text 2>/dev/null || echo "")
    if [ -n "$AWS_IDENTITY" ]; then
      AWS_ACCT=$(echo "$AWS_IDENTITY" | awk '{print $1}')
      log_ok "AWS credentials active (account: $AWS_ACCT)"
    else
      log_warn "AWS CLI installed but no credentials configured"
      echo "  Fix: aws configure"
      echo "  Or:  set AWS_PROFILE=<profile> if using named profiles"
      AUTH_ISSUES=$((AUTH_ISSUES + 1))
    fi
  else
    log_warn "AWS CLI not found — AWS auth check skipped (installed in Phase 1)"
  fi

  # 5. act secrets file (~/.act-secrets)
  if [ -f "$REQUIRED_ACT_SECRETS" ]; then
    log_ok "act secrets found: $REQUIRED_ACT_SECRETS"
  else
    log_fail "act secrets not found: $REQUIRED_ACT_SECRETS"
    echo "  Required for local GitHub Actions testing via 'act'"
    echo "  Create: touch ~/.act-secrets  and populate with required secrets"
    echo "  See: unified-trading-pm/docs/workspace-setup.md#act-secrets"
    AUTH_ISSUES=$((AUTH_ISSUES + 1))
  fi

  if [ "$AUTH_ISSUES" -gt 0 ]; then
    log_warn "$AUTH_ISSUES auth issue(s) — fix above before proceeding, OR re-run with --skip-auth-check"
    echo ""
    read -r -p "  Continue anyway? [y/N] " CONTINUE_ANYWAY
    if [[ ! "$CONTINUE_ANYWAY" =~ ^[Yy]$ ]]; then
      echo "  Aborted. Fix auth issues and re-run."
      exit 1
    fi
  else
    log_ok "All auth checks passed"
  fi
fi

# ── PHASE 0: SELF-SEEDING (clone PM if not already present) ─────────────────
log_phase 0 "Self-Seeding (clone unified-trading-pm)"

PM_ROOT="$WORKSPACE_ROOT/unified-trading-pm"
MANIFEST="$PM_ROOT/workspace-manifest.json"

cd "$WORKSPACE_ROOT"
if [ -d "$PM_ROOT" ]; then
  log_skip "unified-trading-pm already cloned"
else
  if [ "$CHECK_ONLY" = true ]; then
    log_fail "unified-trading-pm not found"
    echo "  Clone: git clone $(clone_url unified-trading-pm)"
    exit 1
  fi
  echo "  Cloning unified-trading-pm..."
  if git clone "$(clone_url unified-trading-pm)" "unified-trading-pm" 2>/dev/null; then
    log_ok "unified-trading-pm cloned"
  else
    log_fail "Failed to clone unified-trading-pm"
    if [ "$USE_HTTPS" = false ]; then
      echo "  SSH failed. Try: bash $0 --https"
    else
      echo "  HTTPS failed. Ensure gh auth login or GITHUB_TOKEN is set."
    fi
    exit 1
  fi
fi

# Now that PM is available, re-resolve paths if running via curl
if [[ "${SCRIPT_SOURCE}" == /dev/fd/* ]] || [[ "${SCRIPT_SOURCE}" == "-bash" ]] || [[ "${SCRIPT_SOURCE}" == "bash" ]]; then
  SCRIPT_DIR_RESOLVED="$PM_ROOT/scripts/workspace"
fi

# ── PHASE 1: SYSTEM DEPENDENCIES ────────────────────────────────────────────
log_phase 1 "System Dependencies"

REQUIRED_PYTHON_FULL="3.13.9"   # exact patch version — must match exactly
REQUIRED_PYTHON_MM="3.13"       # major.minor for brew/pyenv installs
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

# Detect OS / arch for install hints
OS_TYPE="$(uname -s)"
ARCH_TYPE="$(uname -m)"

# Git
check_cmd "git" "git" "install: brew install git / sudo apt install git"

# ── Python 3.13.9 (exact version required) ───────────────────────────────────
# Strategy: find any python that reports exactly 3.13.9, then offer uv install.
# uv is the preferred install method — works on macOS (Intel + Apple Silicon M1–M5)
# and Linux (x86_64 + arm64) without needing pyenv or Homebrew for Python.

python_version_full() {
  # Outputs full x.y.z version of a python binary, or empty string
  local cmd="$1"
  "$cmd" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 2>/dev/null || true
}

PYTHON_CMD=""

# 1. Check candidates on PATH + common install locations
for candidate in \
    "python${REQUIRED_PYTHON_MM}" \
    "python3" \
    "python" \
    "$HOME/.local/share/uv/python/cpython-${REQUIRED_PYTHON_FULL}-*/bin/python" \
    "$HOME/.pyenv/versions/${REQUIRED_PYTHON_FULL}/bin/python" \
    "$HOME/.local/share/mise/installs/python/${REQUIRED_PYTHON_FULL}/bin/python" \
    "/opt/homebrew/bin/python${REQUIRED_PYTHON_MM}" \
    "/usr/local/bin/python${REQUIRED_PYTHON_MM}" \
    "/usr/bin/python${REQUIRED_PYTHON_MM}"; do
  # Expand globs (uv path may have arch suffix)
  for expanded in $candidate; do
    [ -x "$expanded" ] || command -v "$expanded" &>/dev/null || continue
    VER=$(python_version_full "$expanded")
    if [ "$VER" = "$REQUIRED_PYTHON_FULL" ]; then
      PYTHON_CMD="$expanded"
      break 2
    fi
  done
done

# 2. Also check `uv python find` if uv is available
if [ -z "$PYTHON_CMD" ] && command -v uv &>/dev/null; then
  UV_PY=$(uv python find "${REQUIRED_PYTHON_FULL}" 2>/dev/null || true)
  if [ -n "$UV_PY" ] && [ -x "$UV_PY" ]; then
    VER=$(python_version_full "$UV_PY")
    [ "$VER" = "$REQUIRED_PYTHON_FULL" ] && PYTHON_CMD="$UV_PY"
  fi
fi

if [ -n "$PYTHON_CMD" ]; then
  log_ok "Python $REQUIRED_PYTHON_FULL ($PYTHON_CMD)"
  # Warn if Python is from uv's own managed cache — venvs break when cache is wiped
  if echo "$PYTHON_CMD" | grep -q "\.local/share/uv/python"; then
    log_warn "Python resolved from uv's internal cache: $PYTHON_CMD"
    echo "  All venvs will have home = $(dirname "$PYTHON_CMD") in pyvenv.cfg."
    echo "  If ~/.local/share/uv/python/ is ever cleared, all 50+ venvs break."
    echo "  Recommended: install via pyenv and add these to ~/.bashrc / ~/.profile:"
    echo "    export PYENV_ROOT=\"\$HOME/.pyenv\""
    echo "    export PATH=\"\$PYENV_ROOT/bin:\$PYENV_ROOT/shims:\$PATH\""
    echo "    export UV_PYTHON=\"\$PYENV_ROOT/versions/$REQUIRED_PYTHON_FULL/bin/python3.13\""
    echo "    export UV_PYTHON_PREFERENCE=system"
    echo "    export UV_PYTHON_DOWNLOADS=never"
    echo "    export PYENV_VIRTUALENV_DISABLE_PROMPT=1"
  fi
  # Rehash pyenv shims so this version is visible as python3.13 etc. (no-op if no pyenv)
  command -v pyenv &>/dev/null && pyenv rehash 2>/dev/null || true
else
  # Show what version the system has
  CURRENT_PY_VER=""
  for cmd in python3 python; do
    command -v "$cmd" &>/dev/null && CURRENT_PY_VER=$(python_version_full "$cmd") && break
  done
  [ -n "$CURRENT_PY_VER" ] && log_warn "Python found: $CURRENT_PY_VER (need exactly $REQUIRED_PYTHON_FULL)" \
                            || log_warn "Python not found (need $REQUIRED_PYTHON_FULL)"

  echo ""
  echo "  ┌─ Install Python $REQUIRED_PYTHON_FULL ─────────────────────────────────────────"
  echo "  │  Recommended (cross-platform, no root required):"
  echo "  │    uv python install ${REQUIRED_PYTHON_FULL}    # installs managed Python"
  echo "  │"
  if [ "$OS_TYPE" = "Darwin" ]; then
    echo "  │  macOS alternatives:"
    echo "  │    brew install python@${REQUIRED_PYTHON_MM}  # Homebrew (may not be exact patch)"
    echo "  │    pyenv install ${REQUIRED_PYTHON_FULL} && pyenv global ${REQUIRED_PYTHON_FULL}"
    echo "  │    mise use -g python@${REQUIRED_PYTHON_FULL}"
    echo "  │"
    if [ "$ARCH_TYPE" = "arm64" ]; then
      echo "  │  Apple Silicon (M1–M5): all methods above work natively."
    else
      echo "  │  Intel Mac: all methods above work."
    fi
  else
    echo "  │  Linux alternatives:"
    echo "  │    pyenv install ${REQUIRED_PYTHON_FULL} && pyenv global ${REQUIRED_PYTHON_FULL}"
    echo "  │    mise use -g python@${REQUIRED_PYTHON_FULL}"
    echo "  │"
    echo "  │  Ubuntu/Debian (may not have exact patch):"
    echo "  │    sudo add-apt-repository ppa:deadsnakes/ppa"
    echo "  │    sudo apt update && sudo apt install python3.13"
    echo "  │    (use pyenv/uv for exact ${REQUIRED_PYTHON_FULL} patch version)"
  fi
  echo "  │"
  echo "  │  After installing, re-run: bash bootstrap.sh"
  echo "  └────────────────────────────────────────────────────────────────────"
  echo ""

  if [ "$CHECK_ONLY" = true ] || [ "$SKIP_SYSTEM" = true ]; then
    SYSTEM_ISSUES=$((SYSTEM_ISSUES + 1))
  elif command -v uv &>/dev/null; then
    echo "  uv is available — attempting: uv python install ${REQUIRED_PYTHON_FULL}"
    if uv python install "${REQUIRED_PYTHON_FULL}" 2>&1; then
      UV_PY=$(uv python find "${REQUIRED_PYTHON_FULL}" 2>/dev/null || true)
      if [ -n "$UV_PY" ] && [ -x "$UV_PY" ]; then
        PYTHON_CMD="$UV_PY"
        log_ok "Python $REQUIRED_PYTHON_FULL installed via uv ($PYTHON_CMD)"
      else
        log_fail "uv install succeeded but python not found — re-run bootstrap"
        SYSTEM_ISSUES=$((SYSTEM_ISSUES + 1))
      fi
    else
      log_fail "uv python install ${REQUIRED_PYTHON_FULL} failed — install manually"
      SYSTEM_ISSUES=$((SYSTEM_ISSUES + 1))
    fi
  else
    log_fail "Python $REQUIRED_PYTHON_FULL not found — install uv first, then re-run"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    SYSTEM_ISSUES=$((SYSTEM_ISSUES + 1))
  fi
fi

# Keep REQUIRED_PYTHON for compat with downstream sections that reference it
REQUIRED_PYTHON="$REQUIRED_PYTHON_MM"

# ── Pyenv health check ────────────────────────────────────────────────────────
# If pyenv is installed, verify the global version exists and shims are valid.
# A missing global version breaks ALL pyenv shims and makes every prompt
# silently wipe VIRTUAL_ENV via pyenv-virtualenv's sh-activate hook.
if command -v pyenv &>/dev/null; then
  PYENV_GLOBAL_VER=$(pyenv global 2>/dev/null | head -1 || echo "")
  if [ -n "$PYENV_GLOBAL_VER" ] && [ "$PYENV_GLOBAL_VER" != "system" ] && \
     [ ! -d "$HOME/.pyenv/versions/$PYENV_GLOBAL_VER" ]; then
    log_warn "pyenv global '$PYENV_GLOBAL_VER' is set but $HOME/.pyenv/versions/$PYENV_GLOBAL_VER does not exist"
    echo "  This breaks pyenv shims and silently wipes VIRTUAL_ENV on every prompt."
    if [ "$CHECK_ONLY" = false ] && [ "$SKIP_SYSTEM" = false ]; then
      echo "  Attempting: pyenv install $REQUIRED_PYTHON_FULL && pyenv global $REQUIRED_PYTHON_FULL"
      pyenv install "$REQUIRED_PYTHON_FULL" 2>/dev/null && \
        pyenv global "$REQUIRED_PYTHON_FULL" && \
        pyenv rehash && \
        log_ok "pyenv $REQUIRED_PYTHON_FULL installed and set as global" || \
        log_warn "pyenv auto-install failed — run manually: pyenv install $REQUIRED_PYTHON_FULL && pyenv global $REQUIRED_PYTHON_FULL"
    else
      echo "  Fix: pyenv install $REQUIRED_PYTHON_FULL && pyenv global $REQUIRED_PYTHON_FULL && pyenv rehash"
    fi
    SYSTEM_ISSUES=$((SYSTEM_ISSUES + 1))
  elif [ -n "$PYENV_GLOBAL_VER" ] && [ "$PYENV_GLOBAL_VER" != "system" ]; then
    # Global version exists — rehash to ensure shims are current
    pyenv rehash 2>/dev/null || true
    log_ok "pyenv global: $PYENV_GLOBAL_VER (shims refreshed)"
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

# awscli
install_cmd "AWS CLI" "aws" "awscli" "awscli" || true

if [ "$SYSTEM_ISSUES" -gt 0 ]; then
  log_warn "$SYSTEM_ISSUES system dependency issue(s) — some steps may fail"
fi

# ── PHASE 2: CLONE REPOS ─────────────────────────────────────────────────────
log_phase 2 "Clone Repositories"

if [ ! -f "$MANIFEST" ]; then
  log_fail "Manifest not found: $MANIFEST"
  echo "  Clone unified-trading-pm first: git clone $(clone_url unified-trading-pm)"
  exit 1
fi

# Extract repo names + topological order from manifest
if command -v jq &>/dev/null; then
  REPOS=$(jq -r '.repositories | keys[]' "$MANIFEST" 2>/dev/null)
  ORDERED_REPOS=$(jq -r '
    .repositories
    | to_entries
    | sort_by(.value.tier // 99, .key)
    | .[].key
  ' "$MANIFEST" 2>/dev/null || echo "$REPOS")
elif [ -n "$PYTHON_CMD" ]; then
  REPOS=$("$PYTHON_CMD" -c "
import json, sys
with open('$MANIFEST') as f:
    data = json.load(f)
for name in sorted(data.get('repositories', {}).keys()):
    print(name)
" 2>/dev/null)
  ORDERED_REPOS=$("$PYTHON_CMD" -c "
import json
with open('$MANIFEST') as f:
    data = json.load(f)
repos = data.get('repositories', {})
ordered = sorted(repos.keys(), key=lambda r: (repos[r].get('tier', 99), r))
for name in ordered:
    print(name)
" 2>/dev/null || echo "$REPOS")
else
  log_fail "Need jq or Python to parse manifest"
  exit 1
fi

CLONE_OK=0
CLONE_SKIP=0
CLONE_FAIL=0

cd "$WORKSPACE_ROOT"
for repo in $REPOS; do
  # Skip PM — already cloned in Phase 0
  [ "$repo" = "unified-trading-pm" ] && { log_skip "unified-trading-pm (Phase 0)"; CLONE_SKIP=$((CLONE_SKIP + 1)); continue; }

  if [ -d "$repo" ]; then
    if [ "$SKIP_FRESH" = true ]; then
      log_skip "$repo (exists)"
      CLONE_SKIP=$((CLONE_SKIP + 1))
    elif [ "$CHECK_ONLY" = true ]; then
      log_ok "$repo (exists)"
      CLONE_SKIP=$((CLONE_SKIP + 1))
    else
      # Fresh clone: remove and re-clone for clean state
      log_info "Re-cloning $repo (use --skip-fresh to preserve)"
      rm -rf "$repo"
      if git clone "$(clone_url "$repo")" "$repo" 2>/dev/null; then
        log_ok "$repo (fresh clone)"
        CLONE_OK=$((CLONE_OK + 1))
      else
        log_warn "$repo clone failed (may not exist on GitHub yet)"
        CLONE_FAIL=$((CLONE_FAIL + 1))
      fi
    fi
  elif [ "$CHECK_ONLY" = true ]; then
    log_fail "$repo (missing)"
    CLONE_FAIL=$((CLONE_FAIL + 1))
  else
    if git clone "$(clone_url "$repo")" "$repo" 2>/dev/null; then
      log_ok "$repo"
      CLONE_OK=$((CLONE_OK + 1))
    else
      log_warn "$repo clone failed (may not exist on GitHub yet)"
      CLONE_FAIL=$((CLONE_FAIL + 1))
    fi
  fi
done

echo -e "\n  Cloned: $CLONE_OK | Existing: $CLONE_SKIP | Failed: $CLONE_FAIL"

# ── PHASE 2.5: READINESS-REF FILES ───────────────────────────────────────────
# Create .readiness-ref (committed text file) in each repo pointing to its
# canonical checklist in unified-trading-pm/codex/ (the unified-trading-codex repo
# is ARCHIVED — folded into PM at codex/). Path is RELATIVE so it works
# on GHA runners where workspace root differs from local machines.
# The companion .readiness symlink is gitignored and created fresh by
# setup-workspace.sh.

if [ "$CHECK_ONLY" = false ]; then
  log_phase "2.5" "Readiness-Ref Files (.readiness-ref)"
  READINESS_OK=0
  READINESS_SKIP=0

  for repo in $REPOS; do
    REPO_PATH="$WORKSPACE_ROOT/$repo"
    [ -d "$REPO_PATH" ] || continue

    READINESS_REF_FILE="$REPO_PATH/.readiness-ref"
    READINESS_REF_CONTENT="../unified-trading-pm/codex/10-audit/repos/${repo}.yaml"

    if [ -f "$READINESS_REF_FILE" ]; then
      EXISTING=$(cat "$READINESS_REF_FILE")
      if [ "$EXISTING" = "$READINESS_REF_CONTENT" ]; then
        READINESS_SKIP=$((READINESS_SKIP + 1))
        continue
      fi
    fi

    echo "$READINESS_REF_CONTENT" > "$READINESS_REF_FILE"
    git -C "$REPO_PATH" add .readiness-ref 2>/dev/null || true
    READINESS_OK=$((READINESS_OK + 1))

    # Add .readiness (symlink version) to .gitignore if not already present
    GITIGNORE="$REPO_PATH/.gitignore"
    if [ -f "$GITIGNORE" ]; then
      if ! grep -q "^\.readiness$" "$GITIGNORE" 2>/dev/null; then
        echo ".readiness" >> "$GITIGNORE"
        git -C "$REPO_PATH" add .gitignore 2>/dev/null || true
      fi
    else
      echo ".readiness" > "$GITIGNORE"
      git -C "$REPO_PATH" add .gitignore 2>/dev/null || true
    fi
  done

  echo -e "\n  Readiness-ref created/updated: $READINESS_OK | Already correct: $READINESS_SKIP"
fi

# ── PHASE 3: VERSION ALIGNMENT ────────────────────────────────────────────────
log_phase 3 "Version Alignment"

VERSION_ALIGN_SCRIPT="$PM_ROOT/scripts/repo-management/run-version-alignment.sh"
if [ "$CHECK_ONLY" = true ]; then
  if [ -f "$VERSION_ALIGN_SCRIPT" ]; then
    log_info "Check mode — skipping version alignment fix"
  else
    log_warn "run-version-alignment.sh not found"
  fi
elif [ -f "$VERSION_ALIGN_SCRIPT" ]; then
  echo "  Running version alignment (including validate-uv-sources.py --fix)..."
  VA_LOG=$(mktemp /tmp/version-align-XXXXXX.log)
  if (cd "$WORKSPACE_ROOT" && bash "$VERSION_ALIGN_SCRIPT" --fix 2>&1 | tee "$VA_LOG" | tail -30); then
    log_ok "Version alignment complete (full log: $VA_LOG)"
  else
    log_warn "Version alignment had issues (non-fatal — continuing)"
    echo "  Full log: $VA_LOG"
    echo "  Key step: validate-uv-sources.py --fix adds missing [tool.uv.sources.*] entries"
  fi
else
  log_warn "run-version-alignment.sh not found — skipping"
fi

# ── PHASE 4: WORKSPACE VENV ───────────────────────────────────────────────────
log_phase 4 "Workspace Virtual Environment"

WORKSPACE_VENV="$WORKSPACE_ROOT/.venv-workspace"
VENV_SETUP_SCRIPT="$PM_ROOT/scripts/setup-workspace-venv.sh"

if [ "$CHECK_ONLY" = true ]; then
  if [ -d "$WORKSPACE_VENV" ]; then
    log_ok ".venv-workspace exists"
    VENV_PYTHON="$WORKSPACE_VENV/bin/python"
    if [ -f "$VENV_PYTHON" ]; then
      VENV_VER=$("$VENV_PYTHON" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
      log_ok "Python $VENV_VER in .venv-workspace"
    fi
  else
    log_fail ".venv-workspace missing"
  fi
elif [ -f "$VENV_SETUP_SCRIPT" ] && [ -n "$PYTHON_CMD" ]; then
  echo "  Running setup-workspace-venv.sh..."
  if bash "$VENV_SETUP_SCRIPT" 2>&1 | tail -10; then
    log_ok "Workspace venv ready (.venv-workspace)"
  else
    log_warn "Workspace venv setup had issues — falling back to manual creation"
    if [ ! -d "$WORKSPACE_VENV" ]; then
      if command -v uv &>/dev/null; then
        uv venv "$WORKSPACE_VENV" --python "$PYTHON_CMD" 2>/dev/null && log_ok "Created .venv-workspace (uv fallback)"
      else
        "$PYTHON_CMD" -m venv "$WORKSPACE_VENV" && log_ok "Created .venv-workspace (stdlib fallback)"
      fi
    fi
  fi
else
  # Manual fallback when setup-workspace-venv.sh not available
  if [ -d "$WORKSPACE_VENV" ]; then
    log_skip ".venv-workspace exists"
  elif [ -n "$PYTHON_CMD" ]; then
    if command -v uv &>/dev/null; then
      uv venv "$WORKSPACE_VENV" --python "$PYTHON_CMD" 2>/dev/null && log_ok "Created .venv-workspace"
    else
      "$PYTHON_CMD" -m venv "$WORKSPACE_VENV" && log_ok "Created .venv-workspace (stdlib venv)"
    fi
    # Install pinned tools
    if [ -d "$WORKSPACE_VENV" ] && command -v uv &>/dev/null; then
      uv pip install --python "$WORKSPACE_VENV/bin/python" \
        "ruff==0.15.0" "basedpyright==1.38.2" "pytest>=8.0.0" \
        --quiet 2>/dev/null && log_ok "Workspace tools installed" || log_warn "Tool install failed"
    fi
  else
    log_fail "Cannot create venv — Python $REQUIRED_PYTHON not found"
  fi
fi

# ── INSTALL SHARED SCRIPTS INTO .venv-workspace/bin ─────────────────────────
# Makes run_timeout (and any future shared scripts) available as system
# binaries in any subshell without sourcing quality-gates.sh.
if [ -d "$WORKSPACE_VENV/bin" ] && [ -d "$PM_ROOT/scripts/shared" ]; then
  for _script in "$PM_ROOT/scripts/shared/"*; do
    _name=$(basename "$_script")
    cp "$_script" "$WORKSPACE_VENV/bin/$_name"
    chmod +x "$WORKSPACE_VENV/bin/$_name"
  done
  log_ok "Shared scripts installed to .venv-workspace/bin (run_timeout etc.)"
fi

# Install git hooks in all repos
echo ""
echo "=== Phase 4: Installing git hooks ==="
if [ -f "$SCRIPT_DIR_RESOLVED/install-hooks.sh" ]; then
  bash "$SCRIPT_DIR_RESOLVED/install-hooks.sh"
else
  echo "WARNING: install-hooks.sh not found — skipping hook installation"
fi

# ── PHASE 5: PER-REPO SETUP (CI/CD Phase 2) ──────────────────────────────────
log_phase 5 "Per-Repo Setup (CI/CD Phase 2)"

SETUP_FAIL=0

if [ "$CHECK_ONLY" = true ]; then
  if (cd "$WORKSPACE_ROOT" && bash "$PM_ROOT/scripts/repo-management/run-all-setup.sh" --check 2>&1 | tail -20); then
    log_ok "Setup check passed (all repos)"
  else
    log_fail "Setup check failed"
    SETUP_FAIL=1
  fi
else
  echo -e "\n  ${BLUE}Invoking run-all-setup.sh --rollout-first (CI/CD Phase 2)${NC}"
  if (cd "$WORKSPACE_ROOT" && bash "$PM_ROOT/scripts/repo-management/run-all-setup.sh" --rollout-first 2>&1 | tail -30); then
    log_ok "Setup complete (all repos)"
  else
    log_warn "Setup had issues (non-fatal — continuing)"
    SETUP_FAIL=1
  fi
fi

# ── PHASE 6: WORKSPACE SYMLINKS ───────────────────────────────────────────────
log_phase 6 "Workspace Symlinks (.cursor/, bootstrap.sh)"

if [ "$CHECK_ONLY" = false ]; then
  SYMLINK_SCRIPTS=(
    "setup-cursor-rules-symlink.sh"
    "setup-cursor-plans-symlink.sh"
    "setup-workspace-config-symlink.sh"
  )
  for s in "${SYMLINK_SCRIPTS[@]}"; do
    SCRIPT_PATH="$PM_ROOT/scripts/workspace/$s"
    if [ -f "$SCRIPT_PATH" ]; then
      if bash "$SCRIPT_PATH" 2>&1 | grep -E '^\[(OK|SKIP)\]' | head -3; then
        log_ok "$s"
      else
        log_warn "$s had issues (non-fatal)"
      fi
    else
      log_warn "$s not found — skipping"
    fi
  done

  # Ensure workspace root bootstrap.sh symlink
  BOOTSTRAP_SYMLINK="$WORKSPACE_ROOT/bootstrap.sh"
  BOOTSTRAP_TARGET="unified-trading-pm/scripts/workspace/workspace-bootstrap.sh"
  if [ -L "$BOOTSTRAP_SYMLINK" ]; then
    CURRENT_TARGET=$(readlink "$BOOTSTRAP_SYMLINK")
    if [ "$CURRENT_TARGET" = "$BOOTSTRAP_TARGET" ]; then
      log_skip "bootstrap.sh symlink already correct"
    else
      rm "$BOOTSTRAP_SYMLINK"
      (cd "$WORKSPACE_ROOT" && ln -sf "$BOOTSTRAP_TARGET" bootstrap.sh)
      log_ok "bootstrap.sh symlink updated"
    fi
  elif [ -f "$BOOTSTRAP_SYMLINK" ]; then
    rm "$BOOTSTRAP_SYMLINK"
    (cd "$WORKSPACE_ROOT" && ln -sf "$BOOTSTRAP_TARGET" bootstrap.sh)
    log_ok "bootstrap.sh replaced with symlink"
  else
    (cd "$WORKSPACE_ROOT" && ln -sf "$BOOTSTRAP_TARGET" bootstrap.sh)
    log_ok "bootstrap.sh symlink created"
  fi
else
  # Check mode: verify symlinks
  for name in rules plans workspace-configs; do
    LINK="$WORKSPACE_ROOT/.cursor/$name"
    if [ -L "$LINK" ]; then
      log_ok ".cursor/$name symlink exists ($(readlink "$LINK"))"
    else
      log_warn ".cursor/$name not a symlink"
    fi
  done
fi

# ── PHASE 7: IMPORT SMOKE TEST (all repos) ───────────────────────────────────
log_phase 7 "Import Smoke Test (all Python repos)"

SMOKE_OK=0
SMOKE_FAIL=0
SMOKE_SKIP=0
SMOKE_FAILURES=""

for repo in $ORDERED_REPOS; do
  REPO_PATH="$WORKSPACE_ROOT/$repo"
  PYPROJECT="$REPO_PATH/pyproject.toml"
  [ -f "$PYPROJECT" ] || continue

  # Auto-detect package name from [project] name
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

# ── FINAL SUMMARY ─────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
TOTAL_ISSUES=$((AUTH_ISSUES + SYSTEM_ISSUES + CLONE_FAIL + SETUP_FAIL + SMOKE_FAIL))
if [ "$TOTAL_ISSUES" -gt 0 ]; then
  echo -e "${BOLD}  Bootstrap complete with $TOTAL_ISSUES issue(s) — see above${NC}"
else
  echo -e "${BOLD}${GREEN}  Bootstrap complete — workspace ready${NC}"
fi
echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  Workspace root : $WORKSPACE_ROOT"
echo "  Activate venv  : source $WORKSPACE_VENV/bin/activate"
echo ""
echo "  Quick start:"
echo "    1. source $WORKSPACE_VENV/bin/activate"
echo "    2. code $WORKSPACE_ROOT/.cursor/workspace-configs/unified-trading-system-repos.code-workspace"
echo "       (or open via Cursor: File > Open Workspace from File)"
echo ""
echo "  Re-verify workspace at any time:"
echo "    bash bootstrap.sh --check"
echo ""
echo "  Add new repos / re-sync:"
echo "    bash bootstrap.sh --skip-fresh"
echo ""
echo "  Parallel-agent flow — provision per-tab worktrees (recommended for ≥3 parallel tabs):"
echo "    bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --init --slots 8"
echo "    (each tab gets an isolated working tree at .tabs/<N>/ on branch tab/\$USER/<N>;"
echo "     cross-tab .git/index races become unrepresentable by construction)"
echo "    SSOT: unified-trading-pm/codex/05-infrastructure/per-tab-worktrees.md"
echo ""
echo "  ── Linux / pyenv recommended shell config (~/.bashrc or ~/.profile) ──"
echo "  If using pyenv, add these to prevent uv from downloading its own Python"
echo "  (broken uv Python cache = all 50+ venvs break simultaneously):"
echo ""
echo "    export PYENV_ROOT=\"\$HOME/.pyenv\""
echo "    export PATH=\"\$PYENV_ROOT/bin:\$PYENV_ROOT/shims:\$PATH\""
echo "    export UV_PYTHON=\"\$PYENV_ROOT/versions/$REQUIRED_PYTHON_FULL/bin/python3.13\""
echo "    export UV_PYTHON_PREFERENCE=system    # uv uses PATH/pyenv Python, not its own"
echo "    export UV_PYTHON_DOWNLOADS=never      # prevents uv auto-download of CPython"
echo "    export PYENV_VIRTUALENV_DISABLE_PROMPT=1  # prevents prompt clobbering VIRTUAL_ENV"
echo ""
echo "  (macOS: not needed — Homebrew Python is on PATH and uv respects it)"
echo ""
