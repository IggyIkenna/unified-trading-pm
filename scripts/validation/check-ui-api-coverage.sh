#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# check-ui-api-coverage.sh — Verify UI integration tests cover all mapped API endpoints.
#
# Reads ui-api-mapping.json and checks that each UI's integration test file
# references all endpoints listed in the mapping. Reports gaps as warnings.
# Exit 0 always (advisory — does not fail QG).
#
# Usage:
#   bash unified-trading-pm/scripts/validation/check-ui-api-coverage.sh [WORKSPACE_ROOT]

set -euo pipefail

WORKSPACE_ROOT="${1:-$(cd "$(dirname "$0")/../../.." && pwd)}"
MAPPING_FILE="$WORKSPACE_ROOT/unified-trading-pm/scripts/propagation/ui-api-mapping.json"

if [ ! -f "$MAPPING_FILE" ]; then
  echo "ERROR: ui-api-mapping.json not found at $MAPPING_FILE"
  exit 0
fi

TOTAL_UIS=0
MISSING_TEST_FILE=0
INCOMPLETE_COVERAGE=0
FULL_COVERAGE=0
WARNINGS=""

# Parse the JSON mapping using python (available in all envs)
UI_NAMES=$(python3 -c "
import json, sys
with open('$MAPPING_FILE') as f:
    data = json.load(f)
for ui in sorted(data.keys()):
    print(ui)
")

for UI_NAME in $UI_NAMES; do
  TOTAL_UIS=$((TOTAL_UIS + 1))

  # Extract mapping info
  API_NAME=$(python3 -c "
import json
with open('$MAPPING_FILE') as f:
    data = json.load(f)
entry = data['$UI_NAME']
print(entry.get('api_name', ''))
")
  ENDPOINT_COUNT=$(python3 -c "
import json
with open('$MAPPING_FILE') as f:
    data = json.load(f)
entry = data['$UI_NAME']
eps = entry.get('endpoints', []) + entry.get('endpoints_inference', [])
print(len(eps))
")

  # Find integration test file
  TEST_FILE="$WORKSPACE_ROOT/$UI_NAME/tests/integration/api.integration.test.ts"

  if [ ! -f "$TEST_FILE" ]; then
    MISSING_TEST_FILE=$((MISSING_TEST_FILE + 1))
    WARNINGS="${WARNINGS}  MISSING: $UI_NAME — no integration test file at tests/integration/api.integration.test.ts\n"
    continue
  fi

  # Check each endpoint
  MISSING_EPS=""
  TESTED_COUNT=0

  ENDPOINTS=$(python3 -c "
import json
with open('$MAPPING_FILE') as f:
    data = json.load(f)
entry = data['$UI_NAME']
for ep in entry.get('endpoints', []) + entry.get('endpoints_inference', []):
    print(ep)
")

  while IFS= read -r EP; do
    [ -z "$EP" ] && continue
    # Normalize: strip path params for grep matching
    # Convert /results/{result_id} to /results/ for fuzzy matching
    EP_PATTERN=$(echo "$EP" | sed 's/{[^}]*}/[^"]*/' | sed 's|/|\\\\\/|g')

    # Check if the endpoint (or a close variant) appears in the test file
    if grep -qE "(fetchApi|fetch)\(.*$EP_PATTERN" "$TEST_FILE" 2>/dev/null; then
      TESTED_COUNT=$((TESTED_COUNT + 1))
    elif grep -q "$(echo "$EP" | sed 's/{[^}]*}//g' | tr '/' '\n' | tail -1)" "$TEST_FILE" 2>/dev/null; then
      # Fuzzy match: last path segment appears somewhere
      TESTED_COUNT=$((TESTED_COUNT + 1))
    else
      MISSING_EPS="${MISSING_EPS}    - $EP\n"
    fi
  done <<< "$ENDPOINTS"

  if [ -n "$MISSING_EPS" ]; then
    INCOMPLETE_COVERAGE=$((INCOMPLETE_COVERAGE + 1))
    WARNINGS="${WARNINGS}  INCOMPLETE: $UI_NAME ($TESTED_COUNT/$ENDPOINT_COUNT endpoints covered)\n"
    WARNINGS="${WARNINGS}    Untested endpoints:\n$MISSING_EPS"
  else
    FULL_COVERAGE=$((FULL_COVERAGE + 1))
  fi
done

echo "========================================"
echo "UI-API Integration Test Coverage Report"
echo "========================================"
echo ""
echo "Total UIs:              $TOTAL_UIS"
echo "Full coverage:          $FULL_COVERAGE"
echo "Incomplete coverage:    $INCOMPLETE_COVERAGE"
echo "Missing test file:      $MISSING_TEST_FILE"
echo ""

if [ -n "$WARNINGS" ]; then
  echo "Warnings:"
  echo -e "$WARNINGS"
fi

echo "Source: $MAPPING_FILE"
echo ""

# Always exit 0 — advisory only
exit 0
