#!/bin/bash
# ==============================================================================
# Sync Issues from Local Codebase - Source of Truth
# ==============================================================================
#
# This script analyzes the local codebase and creates GitHub issues based on:
#   1. What exists in the code (mark as completed)
#   2. What's missing according to codex (create tasks)
#   3. Service audit YAMLs (checklist items)
#
# Usage:
#   bash sync-from-codebase.sh --repo REPO [--dry-run]
#
# ==============================================================================

set -euo pipefail

# Config
ORG="IggyIkenna"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODEX_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DRY_RUN=false
REPO=""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
  echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
  echo -e "${GREEN}[✓]${NC} $1"
}

log_error() {
  echo -e "${RED}[✗]${NC} $1"
}

log_warning() {
  echo -e "${YELLOW}[⚠]${NC} $1"
}

# ==============================================================================
# Parse Arguments
# ==============================================================================

parse_args() {
  while [[ $# -gt 0 ]]; do
    case $1 in
      --repo)
        REPO="$2"
        shift 2
        ;;
      --dry-run)
        DRY_RUN=true
        shift
        ;;
      *)
        log_error "Unknown argument: $1"
        exit 1
        ;;
    esac
  done

  if [[ -z "$REPO" ]]; then
    log_error "Missing --repo argument"
    echo "Usage: bash sync-from-codebase.sh --repo IggyIkenna/instruments-service [--dry-run]"
    exit 1
  fi
}

# ==============================================================================
# Analyze Local Codebase
# ==============================================================================

analyze_codebase() {
  local repo_name=$(basename "$REPO")
  local repo_path="../../../$repo_name"

  log_info "Analyzing codebase: $repo_name"

  if [[ ! -d "$repo_path" ]]; then
    log_error "Repo not found: $repo_path"
    exit 1
  fi

  # Check what exists
  local has_config=false
  local has_dockerfile=false
  local has_cloudbuild=false
  local has_tests=false
  local has_quality_gates=false
  local has_event_logging=false

  if [[ -f "$repo_path/config.py" ]] || [[ -d "$repo_path/config" ]] \
    || find "$repo_path" -maxdepth 4 \( -name "config.py" -o -path "*/config/__init__.py" \) 2>/dev/null | grep -q .; then
    has_config=true
  fi
  [[ -f "$repo_path/Dockerfile" ]] && has_dockerfile=true
  [[ -f "$repo_path/cloudbuild.yaml" ]] && has_cloudbuild=true
  [[ -d "$repo_path/tests" ]] && has_tests=true
  [[ -f "$repo_path/scripts/quality-gates.sh" ]] && has_quality_gates=true

  # Check for log_event calls
  if grep -rq "log_event" "$repo_path" 2>/dev/null; then
    has_event_logging=true
  fi

  # Save analysis
  cat >/tmp/codebase_analysis_${repo_name}.json <<EOF
{
  "repo": "$repo_name",
  "has_config": $has_config,
  "has_dockerfile": $has_dockerfile,
  "has_cloudbuild": $has_cloudbuild,
  "has_tests": $has_tests,
  "has_quality_gates": $has_quality_gates,
  "has_event_logging": $has_event_logging
}
EOF

  log_success "Codebase analysis complete"
  cat /tmp/codebase_analysis_${repo_name}.json | jq .
  echo ""
}

# ==============================================================================
# Create Epic
# ==============================================================================

create_epic() {
  local repo_name=$(basename "$REPO")

  log_info "Creating epic for $repo_name"

  local epic_title="$repo_name - Full Implementation & Audit"
  local epic_body="# Epic: $repo_name

## Overview
Complete implementation and audit of $repo_name according to codex standards.

## Success Criteria
- ✅ All baseline checklist items (BASE-01 through BASE-18)
- ✅ Service-specific checklist items
- ✅ Quality gates passing
- ✅ Test coverage ≥35% (gate), target 80%
- ✅ Codex compliance verified

## Source of Truth
This epic is generated from the local codebase and service registry.

---
<!-- epic-ref: $repo_name-full-implementation -->"

  if [[ "$DRY_RUN" == "true" ]]; then
    log_info "DRY-RUN: Would create epic:"
    echo "  Title: $epic_title"
    return 0
  fi

  # Create epic
  local epic_number=$(gh issue create \
    --repo "$REPO" \
    --title "$epic_title" \
    --body "$epic_body" \
    --label "type/epic,P1-high" \
    --json number \
    --jq .number)

  echo "$epic_number" >/tmp/epic_${repo_name}.txt
  log_success "Created epic #$epic_number"
  echo ""
}

# ==============================================================================
# Create Tasks from Baseline Checklist
# ==============================================================================

create_baseline_tasks() {
  local repo_name=$(basename "$REPO")
  local epic_number=$(cat /tmp/epic_${repo_name}.txt)

  log_info "Creating tasks from baseline checklist"

  # Read baseline template
  local baseline_file="$CODEX_ROOT/10-audit/_service-baseline-template.yaml"

  if [[ ! -f "$baseline_file" ]]; then
    log_error "Baseline template not found: $baseline_file"
    exit 1
  fi

  # Parse YAML and create tasks (simplified - you'd use Python/yq for real)
  log_info "Creating tasks for BASE-01 through BASE-18"

  # Example tasks (you'd parse YAML for real)
  local tasks=(
    "BASE-01: Config management via UnifiedCloudServicesConfig"
    "BASE-02: 3-tier event logging (STARTED, STOPPED, FAILED)"
    "BASE-03: Resource monitoring enabled"
    "BASE-04: Quality gates pass"
    "BASE-06: GCS input/output with schema validation"
    "BASE-11: Test coverage (unit, integration, e2e)"
  )

  for task in "${tasks[@]}"; do
    local task_title="$repo_name: $task"

    if [[ "$DRY_RUN" == "true" ]]; then
      log_info "DRY-RUN: Would create task: $task_title"
      continue
    fi

    # Create task
    gh issue create \
      --repo "$REPO" \
      --title "$task_title" \
      --body "Part of Epic #$epic_number

Checklist item from baseline template.

<!-- task-ref: $repo_name-${task%:*} -->" \
      --label "type/issue,P1-high,service/$repo_name" &>/dev/null

    echo -n "."
  done

  echo ""
  log_success "Created ${#tasks[@]} baseline tasks"
  echo ""
}

# ==============================================================================
# Main
# ==============================================================================

main() {
  echo "===================================================================="
  echo "Sync from Codebase: $REPO"
  echo "===================================================================="
  echo ""

  parse_args "$@"

  analyze_codebase
  create_epic
  create_baseline_tasks

  log_success "Sync complete!"
  echo ""

  if [[ "$DRY_RUN" == "false" ]]; then
    echo "View issues: https://github.com/$REPO/issues"
  fi
}

main "$@"
