#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# setup-dev-environment.sh — Automated dev environment setup for unified trading system.
#
# SSOT: unified-trading-pm/scripts/workspace/setup-dev-environment.sh
# Plan: unified-trading-pm/plans/active/dev_environment_automated_onboarding_2026_03_10.md
#
# Run from workspace root:
#   bash unified-trading-pm/scripts/workspace/setup-dev-environment.sh
#
# What this script does:
#   Step  1 — check_prerequisites  : python3.13, node 22+, docker, git, uv, gcloud, aws, gh
#   Step  2 — setup_venv           : source or create .venv-workspace via workspace-bootstrap.sh
#   Step  3 — fix_broken_symlinks  : run fix-broken-symlinks.sh --all (if present)
#   Step  4 — setup_env_dev        : copy .env.dev.template → .env.dev if absent
#   Step  5 — configure_gcp_dev    : gcloud config for dev project (idempotent)
#   Step  6 — check_aws_testnet    : verify AWS profile or print setup instructions
#   Step  7 — install_dependencies : uv pip install -e for all repos T0→T1→T2→T3
#   Step  8 — verify_imports       : python -c "import ..." sanity check for T0-T2
#   Step  9 — provision_dev_infra  : RETIRED seed-dev-project.sh; points to Terraform (see deployment-service/docs/dev-environment.md)
#   Step 10 — run_smoke_test       : python smoke-test-dev.py (if present)
#   Step 11 — print_summary        : quick-start commands + warnings
#
# Idempotent. Safe to re-run.
#
# Environment reference: unified-trading-pm/docs/dev-environment-vars.md
# VCR cassettes:         unified-trading-pm/scripts/dev/vcr_cassettes/
# AWS testnet setup:     unified-trading-pm/docs/aws-testnet-setup.md (Phase 2)

set -euo pipefail

# ── COLORS + LOGGING ────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

log_ok()    { echo -e "${GREEN}  [OK]   $*${NC}"; }
log_skip()  { echo -e "${BLUE}  [SKIP] $*${NC}"; }
log_warn()  { echo -e "${YELLOW}  [WARN] $*${NC}"; WARNINGS+=("$*"); }
log_fail()  { echo -e "${RED}  [FAIL] $*${NC}"; ERRORS+=("$*"); }
log_info()  { echo -e "${BLUE}  [INFO] $*${NC}"; }
log_step()  { echo -e "\n${BOLD}${CYAN}━━━ Step $1: $2 ━━━${NC}"; }

WARNINGS=()
ERRORS=()

# ── LOCATE WORKSPACE ROOT ────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
PM_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WORKSPACE_ROOT="$(cd "$PM_ROOT/.." && pwd)"

cd "$WORKSPACE_ROOT"
log_info "Workspace root: $WORKSPACE_ROOT"
log_info "PM root:        $PM_ROOT"

# ── STEP 1: CHECK PREREQUISITES ─────────────────────────────────────────────
log_step 1 "Check prerequisites (python3.13, node 22+, docker, git, uv, gcloud, aws, gh)"

check_tool() {
    local tool="$1"
    local install_hint="$2"
    local version_cmd="${3:-}"

    if command -v "$tool" &>/dev/null; then
        if [[ -n "$version_cmd" ]]; then
            local ver
            ver=$(eval "$version_cmd" 2>/dev/null || echo "unknown")
            log_ok "$tool found ($ver)"
        else
            log_ok "$tool found"
        fi
        return 0
    else
        log_fail "$tool not found — $install_hint"
        return 1
    fi
}

PREREQ_FAIL=false

# Python 3.13+
if command -v python3 &>/dev/null; then
    PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0.0")
    PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
    PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
    if [[ "$PY_MAJOR" -ge 3 && "$PY_MINOR" -ge 13 ]]; then
        log_ok "python3 found ($PY_VER)"
    else
        log_fail "python3 found but version $PY_VER < 3.13 — install via: brew install python@3.13"
        PREREQ_FAIL=true
    fi
else
    log_fail "python3 not found — install via: brew install python@3.13"
    PREREQ_FAIL=true
fi

# Node 22+
if command -v node &>/dev/null; then
    NODE_VER=$(node --version 2>/dev/null | sed 's/v//' || echo "0")
    NODE_MAJOR=$(echo "$NODE_VER" | cut -d. -f1)
    if [[ "$NODE_MAJOR" -ge 22 ]]; then
        log_ok "node found (v$NODE_VER)"
    else
        log_warn "node v$NODE_VER found but v22+ recommended — upgrade via: brew upgrade node"
    fi
else
    log_warn "node not found — install via: brew install node (required for UI repos)"
fi

# git
check_tool git "install via: brew install git" "git --version | head -1" || PREREQ_FAIL=true

# docker
if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
    log_ok "docker found and daemon running"
elif command -v docker &>/dev/null; then
    log_warn "docker found but daemon not running — start Docker Desktop before running services"
else
    log_warn "docker not found — install Docker Desktop: https://www.docker.com/products/docker-desktop"
fi

# uv
if check_tool uv "install via: curl -LsSf https://astral.sh/uv/install.sh | sh" "uv --version"; then
    : # ok
else
    PREREQ_FAIL=true
fi

# gcloud (optional but needed for GCP auth)
if command -v gcloud &>/dev/null; then
    log_ok "gcloud found ($(gcloud --version 2>/dev/null | head -1 || echo 'unknown'))"
else
    log_warn "gcloud not found — install: https://cloud.google.com/sdk/docs/install"
fi

# aws CLI (optional)
if command -v aws &>/dev/null; then
    log_ok "aws CLI found ($(aws --version 2>/dev/null || echo 'unknown'))"
else
    log_warn "aws CLI not found — install: https://aws.amazon.com/cli/ (needed for TradFi testnet)"
fi

# gh CLI (optional)
if command -v gh &>/dev/null; then
    log_ok "gh CLI found"
else
    log_warn "gh CLI not found — install via: brew install gh (needed for quickmerge)"
fi

if [[ "$PREREQ_FAIL" == "true" ]]; then
    echo -e "\n${RED}Prerequisites missing. Fix the FAIL items above and re-run.${NC}"
    exit 1
fi

# ── STEP 2: WORKSPACE VENV ───────────────────────────────────────────────────
log_step 2 "Workspace venv"

VENV_DIR="$WORKSPACE_ROOT/.venv-workspace"
VENV_PYTHON="$VENV_DIR/bin/python"

if [[ -f "$VENV_PYTHON" ]]; then
    log_ok ".venv-workspace already exists"
else
    log_info ".venv-workspace not found — creating via workspace-bootstrap.sh --skip-fresh"
    BOOTSTRAP="$PM_ROOT/scripts/workspace/workspace-bootstrap.sh"
    if [[ -f "$BOOTSTRAP" ]]; then
        bash "$BOOTSTRAP" --skip-fresh
    else
        log_info "workspace-bootstrap.sh not found — creating venv directly"
        uv venv "$VENV_DIR" --python python3.13
        # Install core workspace tools
        "$VENV_DIR/bin/pip" install --quiet uv
    fi
fi

# Activate venv for the rest of this script
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
log_ok "Activated .venv-workspace ($(python --version))"

# ── STEP 3: FIX BROKEN SYMLINKS ──────────────────────────────────────────────
log_step 3 "Fix broken symlinks"

FIX_SYMLINKS_SCRIPT="$PM_ROOT/scripts/workspace/fix-broken-symlinks.sh"
if [[ -f "$FIX_SYMLINKS_SCRIPT" ]]; then
    log_info "Running fix-broken-symlinks.sh --all ..."
    if bash "$FIX_SYMLINKS_SCRIPT" --all 2>/dev/null; then
        log_ok "Broken symlinks fixed"
    else
        log_warn "fix-broken-symlinks.sh exited non-zero — review output above"
    fi
else
    # Symlinks were verified clean on 2026-03-10 (131 symlinks, 0 broken).
    # fix-broken-symlinks.sh is created by broken_symlinks_remediation plan when needed.
    log_skip "fix-broken-symlinks.sh not found — symlink health was verified clean on 2026-03-10"
    log_info "  If you encounter broken symlinks, run:"
    log_info "    bash unified-trading-pm/scripts/workspace/setup-pre-flight-symlinks.sh"
    log_info "    bash unified-trading-pm/scripts/workspace/fix-per-repo-cursor-rules-symlinks.sh"
fi

# ── STEP 4: .env.dev ─────────────────────────────────────────────────────────
log_step 4 ".env.dev setup"

ENV_TEMPLATE="$WORKSPACE_ROOT/.env.dev.template"
# Fallback: copy from PM repo if not at workspace root
PM_ENV_TEMPLATE="$PM_ROOT/templates/.env.dev.template"
ENV_DEV="$WORKSPACE_ROOT/.env.dev"

if [[ ! -f "$ENV_TEMPLATE" ]] && [[ -f "$PM_ENV_TEMPLATE" ]]; then
    cp "$PM_ENV_TEMPLATE" "$ENV_TEMPLATE"
    log_ok "Copied .env.dev.template from PM repo to workspace root"
fi

if [[ ! -f "$ENV_TEMPLATE" ]]; then
    log_fail ".env.dev.template not found at $ENV_TEMPLATE — workspace may be incomplete"
    ERRORS+=(".env.dev.template missing")
elif [[ -f "$ENV_DEV" ]]; then
    log_skip ".env.dev already exists — not overwriting"
else
    cp "$ENV_TEMPLATE" "$ENV_DEV"
    log_ok "Copied .env.dev.template → .env.dev"
    echo -e "${YELLOW}  ACTION NEEDED: Edit $ENV_DEV${NC}"
    echo -e "${YELLOW}    - Set GCP_PROJECT_ID to your dev project ID${NC}"
    echo -e "${YELLOW}    - Set GOOGLE_APPLICATION_CREDENTIALS if not using ADC${NC}"
    echo -e "${YELLOW}    - Reference: unified-trading-pm/docs/dev-environment-vars.md${NC}"
fi

# ── STEP 5: GCP DEV CONFIGURATION ────────────────────────────────────────────
log_step 5 "GCP dev configuration"

if command -v gcloud &>/dev/null; then
    # Read project from .env.dev if it exists
    # Default: central-element-323112 (single GCP project; dev resources use -dev suffix via Terraform)
    # See: deployment-service/docs/dev-environment.md
    GCP_PROJECT_VALUE="central-element-323112"
    if [[ -f "$ENV_DEV" ]]; then
        PARSED_PROJECT=$(grep -E '^GCP_PROJECT_ID=' "$ENV_DEV" 2>/dev/null | cut -d= -f2 | tr -d '[:space:]' || true)
        if [[ -n "$PARSED_PROJECT" ]]; then
            GCP_PROJECT_VALUE="$PARSED_PROJECT"
        fi
    fi

    # Create or activate dev config (idempotent)
    if gcloud config configurations describe unified-trading-dev &>/dev/null 2>&1; then
        log_skip "gcloud configuration 'unified-trading-dev' already exists"
    else
        gcloud config configurations create unified-trading-dev --no-activate 2>/dev/null || true
        log_ok "Created gcloud configuration 'unified-trading-dev'"
    fi

    gcloud config configurations activate unified-trading-dev 2>/dev/null || true
    gcloud config set project "$GCP_PROJECT_VALUE" 2>/dev/null || true
    log_ok "gcloud project set to $GCP_PROJECT_VALUE"

    # Check ADC
    if gcloud auth application-default print-access-token &>/dev/null 2>&1; then
        log_ok "GCP Application Default Credentials active"
    else
        log_warn "GCP ADC not configured — run: gcloud auth application-default login"
        log_info "  Services with CLOUD_MOCK_MODE=true will still work without ADC"
    fi
else
    log_skip "gcloud not installed — skipping GCP configuration"
fi

# ── STEP 6: AWS CLI INSTALL + AUTH CHECK ─────────────────────────────────────
log_step 6 "AWS CLI install + auth check"

# Install if missing
if ! command -v aws &>/dev/null; then
    log_info "aws CLI not found — installing via Homebrew..."
    if command -v brew &>/dev/null; then
        brew install awscli && log_ok "aws CLI installed via Homebrew"
    elif command -v apt-get &>/dev/null; then
        sudo apt-get install -y awscli && log_ok "aws CLI installed via apt"
    else
        log_warn "Cannot auto-install aws CLI — install manually: https://aws.amazon.com/cli/"
    fi
fi

if command -v aws &>/dev/null; then
    # Check default credentials first
    if aws sts get-caller-identity &>/dev/null 2>&1; then
        ACCOUNT=$(aws sts get-caller-identity --query 'Account' --output text 2>/dev/null || echo "unknown")
        REGION=$(aws configure get region 2>/dev/null || echo "not set")
        log_ok "AWS credentials active (account: $ACCOUNT, region: $REGION)"
        # Warn if region is not Tokyo (closest to Binance)
        if [[ "$REGION" != "ap-northeast-1" ]]; then
            log_warn "AWS region '$REGION' — expected ap-northeast-1 (Tokyo, closest to Binance)"
            log_info "  Fix: aws configure  → set region ap-northeast-1"
        fi
    else
        log_warn "AWS credentials not configured or expired"
        log_info "  Run: aws configure"
        log_info "  Region: ap-northeast-1 (Tokyo — closest to Binance exchange)"
    fi

    # Also check named dev profile if present
    if aws --profile unified-trading-dev sts get-caller-identity &>/dev/null 2>&1; then
        DEV_ACCOUNT=$(aws --profile unified-trading-dev sts get-caller-identity --query 'Account' --output text 2>/dev/null || echo "unknown")
        log_ok "AWS profile 'unified-trading-dev' active (account: $DEV_ACCOUNT)"
    else
        log_info "AWS profile 'unified-trading-dev' not configured (optional — see docs/aws-testnet-setup.md)"
    fi
else
    log_warn "aws CLI still not found — install manually: https://aws.amazon.com/cli/"
fi

# ── STEP 7: INSTALL REPO DEPENDENCIES ────────────────────────────────────────
log_step 7 "Install repo dependencies (T0→T1→T2→T3 order)"

# Topological order from workspace-manifest.json (L2-L6 = Python libraries/interfaces)
# L2: T0 foundation (no inter-library deps)
T0_REPOS=(
    "unified-api-contracts"
    "unified-cloud-interface"
    "unified-trading-library"
)

# L3: T1 services runtime
T1_REPOS=(
    "unified-config-interface"
    "unified-trading-library"
)

# L4: T2 domain client + calc library
T2_REPOS=(
    "unified-features-interface"
)

# L5-L6: T3 interfaces
T3_REPOS=(
    "unified-market-interface"
    "unified-reference-data-interface"
)

install_repo() {
    local repo="$1"
    local tier_label="$2"
    local repo_path="$WORKSPACE_ROOT/$repo"

    if [[ ! -d "$repo_path" ]]; then
        log_warn "$repo not found at $repo_path — skipping"
        return
    fi

    if [[ ! -f "$repo_path/pyproject.toml" ]]; then
        log_skip "$repo has no pyproject.toml — skipping"
        return
    fi

    if uv pip install -e "$repo_path" --quiet 2>/dev/null; then
        log_ok "[$tier_label] $repo installed"
    else
        log_fail "[$tier_label] $repo install failed"
    fi
}

# Install in strict topological order
log_info "Installing T0 libraries (L2)..."
for repo in "${T0_REPOS[@]}"; do install_repo "$repo" "T0"; done

log_info "Installing T1 libraries (L3)..."
for repo in "${T1_REPOS[@]}"; do install_repo "$repo" "T1"; done

log_info "Installing T2 libraries (L4)..."
for repo in "${T2_REPOS[@]}"; do install_repo "$repo" "T2"; done

log_info "Installing T3 interfaces (L5-L6)..."
for repo in "${T3_REPOS[@]}"; do install_repo "$repo" "T3"; done

# ── STEP 8: VERIFY IMPORTS ────────────────────────────────────────────────────
log_step 8 "Verify T0-T2 library imports"

run_import_check() {
    local label="$1"
    local import_stmt="$2"
    if python -c "$import_stmt" 2>/dev/null; then
        log_ok "$label importable"
    else
        log_fail "$label import failed"
    fi
}

# Core T0 libraries
run_import_check "unified_trading_library.events" \
    "from unified_trading_library.events import setup_events, log_event"

run_import_check "unified_api_contracts" \
    "import unified_api_contracts"

run_import_check "unified_api_contracts.internal" \
    "from unified_api_contracts import internal"

# T1 libraries
run_import_check "unified_config_interface (UnifiedCloudConfig)" \
    "from unified_config_interface import UnifiedCloudConfig"

run_import_check "unified_trading_library" \
    "import unified_trading_library"

# T2 libraries
run_import_check "unified_features_interface" \
    "import unified_features_interface"

# T3 interfaces (best-effort)
run_import_check "unified_market_interface" \
    "import unified_market_interface"

run_import_check "unified_reference_data_interface" \
    "import unified_reference_data_interface"

# ── STEP 9: PROVISION DEV INFRASTRUCTURE ─────────────────────────────────────
# RETIRED: seed-dev-project.sh (2026-03-13) — replaced by Terraform + VCR cassettes
# Canonical provisioning: cd deployment-service/terraform/gcp && terraform apply -var="environment=dev"
# See: deployment-service/docs/dev-environment.md
log_step 9 "Provision dev infrastructure"
log_skip "seed-dev-project.sh RETIRED — dev infra provisioned via Terraform (see deployment-service/docs/dev-environment.md)"
log_info "  Run: cd deployment-service/terraform/gcp && terraform apply -var=\"environment=dev\" -var=\"project_id=central-element-323112\""
log_info "  VCR cassettes replace synthetic data seeding for CI/local testing"

# ── STEP 10: RUN SMOKE TEST ───────────────────────────────────────────────────
log_step 10 "Smoke test"

SMOKE_SCRIPT="$PM_ROOT/scripts/dev/smoke-test-dev.py"
if [[ -f "$SMOKE_SCRIPT" ]]; then
    log_info "Running smoke-test-dev.py ..."
    if python "$SMOKE_SCRIPT" 2>&1; then
        log_ok "Smoke test passed"
    else
        log_warn "Smoke test reported failures — review output above"
    fi
else
    log_skip "smoke-test-dev.py not found — pending Phase 4 of onboarding plan"
    log_info "  Basic import verification was done in Step 8 above"
fi

# ── STEP 11: PRINT SUMMARY ─────────────────────────────────────────────────────
log_step 11 "Summary"

echo ""
echo -e "${BOLD}${GREEN}Dev environment setup complete.${NC}"
echo ""
echo -e "${CYAN}━━━ Quick Start ━━━${NC}"
echo -e "  ${BOLD}Activate venv:${NC}    source $VENV_DIR/bin/activate"
echo -e "  ${BOLD}Python version:${NC}   $(python --version 2>/dev/null || echo 'n/a')"
echo -e "  ${BOLD}Env file:${NC}         $ENV_DEV"
echo ""
echo -e "${CYAN}━━━ Dev Environment Config ━━━${NC}"
echo -e "  CLOUD_MOCK_MODE=true    → in-memory GCS/PubSub (no live credentials needed)"
echo -e "  USE_SECRET_MANAGER=false → API keys read from .env.dev directly"
echo -e "  VCR_MODE=playback        → committed cassettes used (no live API calls)"
echo -e "  RUNTIME_MODE=batch       → batch execution mode"
echo ""

if [[ ${#WARNINGS[@]} -gt 0 ]]; then
    echo -e "${CYAN}━━━ Warnings (non-fatal) ━━━${NC}"
    for w in "${WARNINGS[@]}"; do
        echo -e "  ${YELLOW}[WARN]${NC} $w"
    done
    echo ""
fi

if [[ ${#ERRORS[@]} -gt 0 ]]; then
    echo -e "${CYAN}━━━ Errors (action required) ━━━${NC}"
    for e in "${ERRORS[@]}"; do
        echo -e "  ${RED}[FAIL]${NC} $e"
    done
    echo ""
    echo -e "${YELLOW}Some items require attention. Review the FAIL messages above.${NC}"
else
    echo -e "${GREEN}All required checks passed.${NC}"
fi

echo ""
echo -e "${CYAN}━━━ Next Steps ━━━${NC}"
echo -e "  1. Edit $ENV_DEV"
echo -e "     - Set GCP_PROJECT_ID to your dev GCP project"
echo -e "     - Run 'gcloud auth application-default login' if not done"
echo -e "     - Reference: unified-trading-pm/docs/dev-environment-vars.md"
echo ""
echo -e "  2. Run a service smoke test (when Phase 4 is implemented):"
echo -e "     python unified-trading-pm/scripts/dev/smoke-test-dev.py"
echo ""
echo -e "  3. For AWS/TradFi testnet setup:"
echo -e "     See: unified-trading-pm/docs/aws-testnet-setup.md"
echo ""
echo -e "  4. For testnet API keys (Binance, Deribit, etc.):"
echo -e "     See: unified-trading-pm/docs/testnet-api-keys.md"
echo ""
