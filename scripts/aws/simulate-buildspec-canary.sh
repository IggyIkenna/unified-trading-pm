#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
#
# Simulate buildspec.aws.yaml for 3 canary repos (codebuild-canary-run gate).
# Runs the equivalent of AWS CodeBuild phases locally without AWS/CodeBuild.
#
# Canary repos: instruments-service, unified-cloud-interface, unified-trading-library
# Gate: All 3 exit 0. Document result in aws_migration.md.
#
# Usage:
#   bash scripts/aws/simulate-buildspec-canary.sh [repo]
#   bash scripts/aws/simulate-buildspec-canary.sh   # all 3
#   bash scripts/aws/simulate-buildspec-canary.sh unified-cloud-interface  # single repo
#
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
WS_ROOT="${WORKSPACE_ROOT:-$(dirname "$PM_ROOT")}"

RED='\033[0;31m'; GREEN='\033[0;32m'; BLUE='\033[0;34m'; NC='\033[0m'
log_section() { echo -e "\n${BLUE}=== $1 ===${NC}"; }
log_ok() { echo -e "${GREEN}✅ $1${NC}"; }
log_fail() { echo -e "${RED}❌ $1${NC}"; }

run_library_canary() {
  local repo=$1
  local pkg=$2  # underscore form, e.g. unified_cloud_interface
  local dir="$WS_ROOT/$repo"

  log_section "Canary: $repo (library)"
  if [ ! -d "$dir" ]; then
    log_fail "Repo not found: $dir"
    return 1
  fi
  cd "$dir"

  # Install phase
  pip install uv 2>/dev/null || pip install --user uv || true
  command -v uv >/dev/null || { log_fail "uv not found"; return 1; }

  # Pre_build phase
  uv pip install -e . || { log_fail "uv pip install failed"; return 1; }

  # Build phase: lint
  ruff check --line-length 120 "$pkg/" || { log_fail "ruff check failed"; return 1; }

  # Build phase: tests (unit only — integration needs VCR/live creds)
  if [ -d "tests/unit" ]; then
    pytest tests/unit/ -v --tb=short -x -q || { log_fail "pytest failed"; return 1; }
  elif [ -d "tests" ]; then
    pytest tests/ -v --tb=short -x -q || { log_fail "pytest failed"; return 1; }
  else
    echo "No tests directory, skipping"
  fi

  # Build phase: wheel
  uv pip install build 2>/dev/null || pip install build
  python -m build --wheel --outdir dist/ || { log_fail "build failed"; return 1; }

  log_ok "$repo canary PASSED"
  return 0
}

run_service_canary() {
  local repo="instruments-service"
  local dir="$WS_ROOT/$repo"

  log_section "Canary: $repo (service — quality-gates)"
  if [ ! -d "$dir" ]; then
    log_fail "Repo not found: $dir"
    return 1
  fi
  cd "$dir"

  # Simulate buildspec: install uv, run quality-gates inside "container"
  # We run quality-gates.sh directly (same as docker run would)
  pip install uv 2>/dev/null || pip install --user uv || true
  command -v uv >/dev/null || { log_fail "uv not found"; return 1; }

  if [ -f "scripts/quality-gates.sh" ]; then
    CLOUD_BUILD=true CLOUD_MOCK_MODE=true CLOUD_PROVIDER=aws \
      bash scripts/quality-gates.sh --no-fix --quick || { log_fail "quality-gates failed"; return 1; }
  else
    log_fail "scripts/quality-gates.sh not found"
    return 1
  fi

  log_ok "$repo canary PASSED"
  return 0
}

main() {
  local target="${1:-all}"
  local failed=0

  log_section "Buildspec canary simulation (codebuild-canary-run)"
  echo "Workspace root: $WS_ROOT"

  case "$target" in
    unified-cloud-interface)
      run_library_canary "unified-cloud-interface" "unified_cloud_interface" || failed=1
      ;;
    unified-trading-library)
      run_library_canary "unified-trading-library" "unified_trading_library.events" || failed=1
      ;;
    instruments-service)
      run_service_canary || failed=1
      ;;
    all)
      run_library_canary "unified-cloud-interface" "unified_cloud_interface" || failed=1
      run_library_canary "unified-trading-library" "unified_trading_library.events" || failed=1
      run_service_canary || failed=1
      ;;
    *)
      echo "Usage: $0 [unified-cloud-interface|unified-trading-library|instruments-service|all]"
      exit 1
      ;;
  esac

  if [ $failed -eq 0 ]; then
    log_ok "All canary repos PASSED"
    exit 0
  else
    log_fail "One or more canaries FAILED"
    exit 1
  fi
}

main "$@"
