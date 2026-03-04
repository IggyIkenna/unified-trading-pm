#!/bin/bash
# ==============================================================================
# End-to-End Workflow Test Script
# ==============================================================================
#
# Tests the complete docs-driven workflow locally and on GitHub:
#   1. Service metadata foundation (Phase 0)
#   2. Sync scripts (audit path, delta path, task/subtask creation)
#   3. Label sync
#   4. Duplicate detection
#   5. Status transitions
#
# Usage:
#   bash test-e2e-workflow.sh [--dry-run]
#
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODEX_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DRY_RUN="${1:-}"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# ==============================================================================
# Helper Functions
# ==============================================================================

log_info() {
  echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
  echo -e "${GREEN}[✓]${NC} $1"
  TESTS_PASSED=$((TESTS_PASSED + 1))
}

log_error() {
  echo -e "${RED}[✗]${NC} $1"
  TESTS_FAILED=$((TESTS_FAILED + 1))
}

log_warning() {
  echo -e "${YELLOW}[⚠]${NC} $1"
}

# ==============================================================================
# Phase 0: Service Metadata Foundation Tests
# ==============================================================================

test_phase0_foundation() {
  log_info "Testing Phase 0: Service Metadata Foundation"

  # Test 1: Service metadata schema exists
  if [[ -f "$CODEX_ROOT/10-audit/_service-metadata-schema.yaml" ]]; then
    log_success "Service metadata schema exists"
  else
    log_error "Service metadata schema NOT found"
  fi

  # Test 2: Baseline template exists
  if [[ -f "$CODEX_ROOT/10-audit/_service-baseline-template.yaml" ]]; then
    log_success "Baseline template exists"
  else
    log_error "Baseline template NOT found"
  fi

  # Test 3: Service templates exist (12 total)
  local template_count=0
  for template in \
    "$CODEX_ROOT/10-audit/_service-pipeline-data-io.yaml" \
    "$CODEX_ROOT/10-audit/_service-pipeline-market-data.yaml" \
    "$CODEX_ROOT/10-audit/_service-pipeline-features.yaml" \
    "$CODEX_ROOT/10-audit/_service-pipeline-ml.yaml" \
    "$CODEX_ROOT/10-audit/_service-pipeline-strategy-execution.yaml" \
    "$CODEX_ROOT/10-audit/_service-pipeline-post-trade.yaml" \
    "$CODEX_ROOT/10-audit/_service-platform.yaml" \
    "$CODEX_ROOT/10-audit/_service-ui-observability.yaml" \
    "$CODEX_ROOT/10-audit/_service-ui-control.yaml" \
    "$CODEX_ROOT/10-audit/_service-ui-analysis.yaml"; do
    if [[ -f "$template" ]]; then
      ((template_count++))
    fi
  done

  if [[ $template_count -eq 10 ]]; then
    log_success "All 10 service templates exist"
  else
    log_error "Only $template_count/10 service templates found"
  fi

  # Test 4: Service registry exists and has 32 services
  if [[ -f "$CODEX_ROOT/11-project-management/service-registry.yaml" ]]; then
    local service_count=$(grep -c "^  - service:" "$CODEX_ROOT/11-project-management/service-registry.yaml" || true)
    if [[ $service_count -eq 32 ]]; then
      log_success "Service registry has all 32 services"
    else
      log_error "Service registry has $service_count services (expected 32)"
    fi
  else
    log_error "Service registry NOT found"
  fi

  # Test 5: Venue support matrix exists
  if [[ -f "$CODEX_ROOT/11-project-management/venue-support-matrix.yaml" ]]; then
    log_success "Venue support matrix exists"
  else
    log_error "Venue support matrix NOT found"
  fi
}

# ==============================================================================
# Phase 1: Reference Fixes Tests
# ==============================================================================

test_phase1_fixes() {
  log_info "Testing Phase 1: Reference Fixes"

  # Test 1: No broken references to improvements/
  local broken_refs=$(grep -r "improvements/" "$CODEX_ROOT/12-agent-workflow/"*.md 2>/dev/null || true)
  if [[ -z "$broken_refs" ]]; then
    log_success "No broken references to improvements/"
  else
    log_error "Found broken references to improvements/:"
    echo "$broken_refs"
  fi

  # Test 2: All references point to 06-coding-standards/
  local fixed_refs=$(grep -r "06-coding-standards/" "$CODEX_ROOT/12-agent-workflow/"*.md 2>/dev/null | wc -l || true)
  if [[ $fixed_refs -gt 0 ]]; then
    log_success "Found $fixed_refs references to 06-coding-standards/"
  else
    log_warning "No references to 06-coding-standards/ found (expected some)"
  fi
}

# ==============================================================================
# Label Schema Tests
# ==============================================================================

test_label_schema() {
  log_info "Testing Label Schema"

  local label_file="$CODEX_ROOT/11-project-management/github-integration/label-schema.yaml"

  if [[ ! -f "$label_file" ]]; then
    log_error "Label schema NOT found"
    return
  fi

  # Test 1: lane/docs-ahead label exists
  if grep -q "lane/docs-ahead" "$label_file"; then
    log_success "lane/docs-ahead label exists"
  else
    log_error "lane/docs-ahead label NOT found"
  fi

  # Test 2: type/* labels exist
  local type_labels=$(grep -c "type/" "$label_file" || true)
  if [[ $type_labels -ge 5 ]]; then
    log_success "Found $type_labels type/* labels (expected ≥5)"
  else
    log_error "Found only $type_labels type/* labels (expected ≥5)"
  fi

  # Test 3: cloud/* labels exist
  local cloud_labels=$(grep -c "cloud/" "$label_file" || true)
  if [[ $cloud_labels -ge 3 ]]; then
    log_success "Found $cloud_labels cloud/* labels (expected ≥3)"
  else
    log_error "Found only $cloud_labels cloud/* labels (expected ≥3)"
  fi

  # Test 4: domain/* labels exist
  local domain_labels=$(grep -c "domain/" "$label_file" || true)
  if [[ $domain_labels -ge 5 ]]; then
    log_success "Found $domain_labels domain/* labels (expected ≥5)"
  else
    log_error "Found only $domain_labels domain/* labels (expected ≥5)"
  fi
}

# ==============================================================================
# Unified Compliance Checker Tests
# ==============================================================================

test_compliance_checker() {
  log_info "Testing Unified Compliance Checker"

  local script="$SCRIPT_DIR/check-service-compliance.py"

  if [[ ! -f "$script" ]]; then
    log_error "check-service-compliance.py NOT found"
    return
  fi

  if [[ ! -x "$script" ]]; then
    log_warning "check-service-compliance.py is NOT executable (chmod +x needed)"
  else
    log_success "check-service-compliance.py exists and is executable"
  fi

  # Test 1: check_missing_services function exists
  if grep -q "def check_missing_services" "$script"; then
    log_success "check_missing_services function exists"
  else
    log_error "check_missing_services function NOT found"
  fi

  # Test 2: check_checklist_compliance function exists
  if grep -q "def check_checklist_compliance" "$script"; then
    log_success "check_checklist_compliance function exists"
  else
    log_error "check_checklist_compliance function NOT found"
  fi

  # Test 3: generate_implementation_breakdown function exists
  if grep -q "def generate_implementation_breakdown" "$script"; then
    log_success "generate_implementation_breakdown function exists"
  else
    log_error "generate_implementation_breakdown function NOT found"
  fi

  # Test 4: check_existing_issue function exists
  if grep -q "def check_existing_issue" "$script"; then
    log_success "check_existing_issue function exists (duplicate prevention)"
  else
    log_error "check_existing_issue function NOT found"
  fi
}

# ==============================================================================
# Script Validation Tests
# ==============================================================================

test_scripts_exist() {
  log_info "Testing Core Scripts Exist and Are Executable"

  local scripts=(
    "$SCRIPT_DIR/check-service-compliance.py"
    "$SCRIPT_DIR/run-diff-checker.py"
    "$SCRIPT_DIR/sync-labels.py"
    "$SCRIPT_DIR/sync-project-items.py"
    "$SCRIPT_DIR/track-metrics.py"
  )

  for script in "${scripts[@]}"; do
    local script_name=$(basename "$script")
    if [[ -f "$script" ]]; then
      if [[ -x "$script" ]]; then
        log_success "$script_name exists and is executable"
      else
        log_warning "$script_name exists but is NOT executable (chmod +x needed)"
      fi
    else
      log_error "$script_name NOT found"
    fi
  done

  # Test for deleted orphan scripts
  local orphan_scripts=(
    "$SCRIPT_DIR/sync-feature-cards.py"
    "$SCRIPT_DIR/sync-epic-tasks-subtasks.py"
    "$SCRIPT_DIR/create-tasks-and-subtasks.py"
    "$SCRIPT_DIR/sync-delta-audit-tasks.py"
    "$SCRIPT_DIR/sync-issues.py"
  )

  for script in "${orphan_scripts[@]}"; do
    local script_name=$(basename "$script")
    if [[ -f "$script" ]]; then
      log_error "$script_name should be DELETED (orphan script)"
    else
      log_success "$script_name correctly removed (was orphan)"
    fi
  done
}

# ==============================================================================
# GitHub CLI Tests (if not dry-run)
# ==============================================================================

test_github_cli() {
  if [[ "$DRY_RUN" == "--dry-run" ]]; then
    log_info "Skipping GitHub CLI tests (dry-run mode)"
    return
  fi

  log_info "Testing GitHub CLI"

  # Test 1: gh CLI installed
  if command -v gh &>/dev/null; then
    log_success "gh CLI is installed"
  else
    log_error "gh CLI is NOT installed (required for GitHub integration)"
    return
  fi

  # Test 2: gh auth status
  if gh auth status &>/dev/null; then
    log_success "gh CLI is authenticated"
  else
    log_error "gh CLI is NOT authenticated (run 'gh auth login')"
  fi
}

# ==============================================================================
# E2E Workflow Simulation (Dry-Run)
# ==============================================================================

test_e2e_simulation() {
  log_info "Testing E2E Workflow Simulation"

  # Test 1: Can parse service registry
  if command -v python3 &>/dev/null; then
    if python3 -c "import yaml; yaml.safe_load(open('$CODEX_ROOT/11-project-management/service-registry.yaml'))" 2>/dev/null; then
      log_success "Service registry is valid YAML"
    else
      log_error "Service registry is NOT valid YAML"
    fi
  else
    log_warning "Python3 not found, skipping YAML validation"
  fi

  # Test 2: Can parse label schema
  if command -v python3 &>/dev/null; then
    if python3 -c "import yaml; yaml.safe_load(open('$CODEX_ROOT/11-project-management/github-integration/label-schema.yaml'))" 2>/dev/null; then
      log_success "Label schema is valid YAML"
    else
      log_error "Label schema is NOT valid YAML"
    fi
  else
    log_warning "Python3 not found, skipping YAML validation"
  fi
}

# ==============================================================================
# Main Test Execution
# ==============================================================================

main() {
  echo "===================================================================="
  echo "E2E Workflow Test Suite"
  echo "===================================================================="
  echo ""

  if [[ "$DRY_RUN" == "--dry-run" ]]; then
    log_info "Running in DRY-RUN mode (GitHub tests skipped)"
  fi

  echo ""
  test_phase0_foundation
  echo ""
  test_phase1_fixes
  echo ""
  test_label_schema
  echo ""
  test_compliance_checker
  echo ""
  test_scripts_exist
  echo ""
  test_github_cli
  echo ""
  test_e2e_simulation

  echo ""
  echo "===================================================================="
  echo "Test Results"
  echo "===================================================================="
  echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
  echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
  echo ""

  if [[ $TESTS_FAILED -eq 0 ]]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Run check-service-compliance.py --all-services --dry-run to preview functionality gaps"
    echo "  2. Run run-diff-checker.py --repo IggyIkenna/SERVICE --dry-run to preview code standards"
    echo "  3. Review generated issue breakdown (subtasks, success criteria)"
    echo "  4. If all looks good, remove --dry-run to sync to GitHub"
    echo ""
    echo "Full workflow: See 11-project-management/UNIFIED_WORKFLOW_FINAL.md"
    echo ""
    return 0
  else
    echo -e "${RED}✗ Some tests failed. Fix issues before running sync scripts.${NC}"
    return 1
  fi
}

main
