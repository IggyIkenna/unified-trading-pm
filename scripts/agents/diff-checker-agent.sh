#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Diff Checker Agent
# Reads deployment-v3/configs/checklist.{service}.yaml
# Compares to actual service code
# Outputs GitHub issue JSON for gaps
# Usage: ./diff-checker-agent.sh [service-name] [--dry-run]

set -euo pipefail
WORKSPACE_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
DEPLOYMENT_V3="$WORKSPACE_ROOT/deployment-service"
MANIFEST="$WORKSPACE_ROOT/unified-trading-pm/workspace-manifest.json"
TARGET_SERVICE="${1:-}"
DRY_RUN="${2:-}"

echo "Diff Checker Agent"
echo "Deployment: $DEPLOYMENT_V3"
echo ""

if [ ! -d "$DEPLOYMENT_V3" ]; then
  echo "ERROR: deployment-service not found"
  exit 1
fi

if ! command -v jq &>/dev/null; then
  echo "ERROR: jq required"
  exit 1
fi

# Get services to check
if [ -n "$TARGET_SERVICE" ] && [ "$TARGET_SERVICE" != "--dry-run" ]; then
  SERVICES=("$TARGET_SERVICE")
else
  # Get all services from manifest
  mapfile -t SERVICES < <(jq -r '.repositories | to_entries[] | select(.value.type == "service") | select(.value.status != "future") | .key' "$MANIFEST" 2>/dev/null || true)
fi

ISSUES_FILE="/tmp/diff-checker-issues.json"
echo "[]" >"$ISSUES_FILE"

for service in "${SERVICES[@]}"; do
  CHECKLIST="$DEPLOYMENT_V3/configs/checklist.${service}.yaml"
  SERVICE_DIR="$WORKSPACE_ROOT/$service"

  [ ! -f "$CHECKLIST" ] && echo "SKIP: No checklist for $service" && continue
  [ ! -d "$SERVICE_DIR" ] && echo "SKIP: $service not in workspace" && continue

  echo "Checking: $service"
  GAPS=()

  # Check 1: Has quality-gates.sh?
  [ ! -f "$SERVICE_DIR/scripts/quality-gates.sh" ] && GAPS+=("Missing scripts/quality-gates.sh")

  # Check 2: Has quickmerge.sh?
  [ ! -f "$SERVICE_DIR/scripts/quickmerge.sh" ] && GAPS+=("Missing scripts/quickmerge.sh")

  # Check 3: Has .github/workflows/quality-gates.yml?
  [ ! -f "$SERVICE_DIR/.github/workflows/quality-gates.yml" ] && GAPS+=("Missing .github/workflows/quality-gates.yml")

  # Check 4: Has Dockerfile?
  [ ! -f "$SERVICE_DIR/Dockerfile" ] && GAPS+=("Missing Dockerfile")

  # Check 5: Has 8 canonical docs?
  for doc in "README.md" "docs/ARCHITECTURE.md" "docs/CONFIGURATION.md" "QUALITY_GATE_BYPASS_AUDIT.md"; do
    [ ! -f "$SERVICE_DIR/$doc" ] && GAPS+=("Missing $doc")
  done

  # Check 6: Has pyproject.toml?
  [ ! -f "$SERVICE_DIR/pyproject.toml" ] && GAPS+=("Missing pyproject.toml")

  if [ ${#GAPS[@]} -gt 0 ]; then
    echo "  Found ${#GAPS[@]} gaps for $service:"
    for gap in "${GAPS[@]}"; do
      echo "    - $gap"
    done
    if [ "$DRY_RUN" != "--dry-run" ]; then
      # Create GitHub issue JSON
      ISSUE=$(jq -n \
        --arg title "[$service] Service readiness gaps" \
        --arg body "$(printf "## Service Readiness Gaps: %s\n\n%s" "$service" "$(printf '%s\n' "${GAPS[@]}" | sed 's/^/- /')")" \
        --argjson labels '["service-readiness","auto-generated"]' \
        '{title: $title, body: $body, labels: $labels}')
      jq --argjson issue "$ISSUE" '. += [$issue]' "$ISSUES_FILE" >/tmp/issues_tmp.json && mv /tmp/issues_tmp.json "$ISSUES_FILE"
    fi
  else
    echo "  ✅ No gaps for $service"
  fi
done

ISSUE_COUNT=$(jq '. | length' "$ISSUES_FILE")
echo ""
echo "Generated $ISSUE_COUNT issues → $ISSUES_FILE"
if [ "$ISSUE_COUNT" -gt 0 ] && [ "$DRY_RUN" != "--dry-run" ]; then
  echo "To create issues on GitHub, run:"
  echo "  cat $ISSUES_FILE | jq -c '.[]' | while read issue; do gh api repos/IggyIkenna/unified-trading-pm/issues -X POST -H 'Content-Type: application/json' -d \"\$issue\"; done"
fi
