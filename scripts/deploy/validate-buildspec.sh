#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# validate-buildspec.sh — Validates buildspec.aws.yaml files across the workspace.
#
# Checks for:
#   1. Required phases (install, build, post_build)
#   2. Correct base image references (unified-trading-library from ECR)
#   3. Required env var declarations (AWS_DEFAULT_REGION, IMAGE_TAG)
#   4. Quality gates execution inside Docker
#   5. YAML syntax validity
#
# Usage:
#   bash scripts/deploy/validate-buildspec.sh                    # check all repos
#   bash scripts/deploy/validate-buildspec.sh <repo-path>        # check single repo
#
# Exit codes: 0 = all valid, 1 = validation failures found

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

log_ok()   { echo -e "${GREEN}  [OK]   $1${NC}"; }
log_fail() { echo -e "${RED}  [FAIL] $1${NC}"; }
log_warn() { echo -e "${YELLOW}  [WARN] $1${NC}"; }
log_info() { echo -e "${BLUE}  [INFO] $1${NC}"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WORKSPACE_ROOT="$(cd "$PM_ROOT/.." && pwd)"

ERRORS=0
WARNINGS=0
CHECKED=0

validate_buildspec() {
  local buildspec="$1"
  local repo_name
  repo_name=$(basename "$(dirname "$buildspec")")
  CHECKED=$((CHECKED + 1))

  echo -e "\n${BOLD}Validating: $repo_name/buildspec.aws.yaml${NC}"

  # 1. YAML syntax check (basic — look for version field)
  if ! grep -q '^version:' "$buildspec"; then
    log_fail "$repo_name: Missing 'version:' field — not a valid buildspec"
    ERRORS=$((ERRORS + 1))
    return
  fi
  log_ok "$repo_name: YAML has version field"

  # 2. Required phases
  local missing_phases=""
  for phase in "install:" "build:" "post_build:"; do
    if ! grep -q "^  $phase" "$buildspec" 2>/dev/null; then
      # Also check without leading spaces (different indent levels)
      if ! grep -qE "^\s+${phase}" "$buildspec" 2>/dev/null; then
        missing_phases="$missing_phases $phase"
      fi
    fi
  done

  if [ -n "$missing_phases" ]; then
    log_fail "$repo_name: Missing required phases:$missing_phases"
    ERRORS=$((ERRORS + 1))
  else
    log_ok "$repo_name: All required phases present (install, build, post_build)"
  fi

  # 3. Check for env var declarations
  if grep -q 'AWS_DEFAULT_REGION' "$buildspec"; then
    log_ok "$repo_name: AWS_DEFAULT_REGION declared"
  else
    log_fail "$repo_name: Missing AWS_DEFAULT_REGION env var"
    ERRORS=$((ERRORS + 1))
  fi

  if grep -q 'IMAGE_TAG' "$buildspec"; then
    log_ok "$repo_name: IMAGE_TAG exported"
  else
    log_warn "$repo_name: IMAGE_TAG not found in exported-variables"
    WARNINGS=$((WARNINGS + 1))
  fi

  # 4. Check for correct base image pattern
  # Services should reference unified-trading-library from ECR
  if [ "$repo_name" != "unified-trading-library" ]; then
    if grep -q 'unified-trading-library' "$buildspec"; then
      log_ok "$repo_name: References unified-trading-library base image"
    else
      log_warn "$repo_name: No unified-trading-library base image reference (may be standalone)"
      WARNINGS=$((WARNINGS + 1))
    fi
  fi

  # 5. Check for quality gates execution
  if grep -q 'quality-gates' "$buildspec"; then
    log_ok "$repo_name: Quality gates execution found"
  else
    log_fail "$repo_name: No quality-gates.sh execution — builds must run QG"
    ERRORS=$((ERRORS + 1))
  fi

  # 6. Check for CLOUD_MOCK_MODE in QG run
  if grep -q 'CLOUD_MOCK_MODE=true' "$buildspec"; then
    log_ok "$repo_name: CLOUD_MOCK_MODE=true set for QG run"
  else
    log_warn "$repo_name: CLOUD_MOCK_MODE not set — QG may fail without credentials"
    WARNINGS=$((WARNINGS + 1))
  fi

  # 7. Check for ECR login in install phase
  if grep -q 'ecr get-login-password' "$buildspec"; then
    log_ok "$repo_name: ECR authentication present"
  else
    log_warn "$repo_name: No ECR login — may fail to push images"
    WARNINGS=$((WARNINGS + 1))
  fi

  # 8. Check that docker push uses --all-tags
  if grep -q 'docker push' "$buildspec"; then
    if grep -q '\-\-all-tags' "$buildspec"; then
      log_ok "$repo_name: docker push --all-tags (pushes version + latest)"
    else
      log_warn "$repo_name: docker push without --all-tags"
      WARNINGS=$((WARNINGS + 1))
    fi
  fi

  # 9. Check version extraction pattern
  if grep -q "pyproject.toml" "$buildspec" && grep -q 'VERSION=' "$buildspec"; then
    log_ok "$repo_name: Version extracted from pyproject.toml"
  elif grep -q "package.json" "$buildspec" && grep -q 'VERSION=' "$buildspec"; then
    log_ok "$repo_name: Version extracted from package.json"
  else
    log_warn "$repo_name: Version extraction pattern not found"
    WARNINGS=$((WARNINGS + 1))
  fi
}

# ── MAIN ──────────────────────────────────────────────────────────────────────

echo -e "${BOLD}${BLUE}Buildspec Validator — unified-trading-system${NC}"
echo ""

if [ $# -gt 0 ]; then
  # Single repo mode
  BUILDSPEC="$1/buildspec.aws.yaml"
  if [ ! -f "$BUILDSPEC" ]; then
    echo "No buildspec.aws.yaml found at: $BUILDSPEC"
    exit 1
  fi
  validate_buildspec "$BUILDSPEC"
else
  # Scan all repos
  log_info "Scanning workspace: $WORKSPACE_ROOT"
  FOUND=0
  for buildspec in "$WORKSPACE_ROOT"/*/buildspec.aws.yaml; do
    [ -f "$buildspec" ] || continue
    FOUND=$((FOUND + 1))
    validate_buildspec "$buildspec"
  done

  if [ "$FOUND" -eq 0 ]; then
    log_warn "No buildspec.aws.yaml files found in workspace"
    exit 0
  fi
fi

# ── SUMMARY ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${BLUE}━━━ Summary ━━━${NC}"
echo -e "  Checked:  $CHECKED"
echo -e "  Errors:   $ERRORS"
echo -e "  Warnings: $WARNINGS"

if [ "$ERRORS" -gt 0 ]; then
  echo -e "\n${RED}${BOLD}FAIL: $ERRORS error(s) found${NC}"
  exit 1
else
  echo -e "\n${GREEN}${BOLD}PASS: All buildspec files valid${NC}"
  exit 0
fi
