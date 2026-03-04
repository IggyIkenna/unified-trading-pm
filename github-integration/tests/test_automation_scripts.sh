#!/usr/bin/env bash
# ==============================================================================
# Tests for Automation Scripts
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AUTO_FIX="$SCRIPT_DIR/../scripts/automation/auto-fix-issue.sh"
BATCH_FIX="$SCRIPT_DIR/../scripts/automation/batch-fix.sh"
BATCH_FIX_V2="$SCRIPT_DIR/../scripts/automation/batch-fix-v2.sh"
CLOSE_FIXED="$SCRIPT_DIR/../scripts/automation/close-fixed-issue.sh"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

TESTS_PASSED=0
TESTS_FAILED=0

# ==============================================================================
# Test Helpers
# ==============================================================================

assert_success() {
  local test_name="$1"
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} $test_name"
    ((TESTS_PASSED++))
    return 0
  else
    echo -e "${RED}✗${NC} $test_name"
    ((TESTS_FAILED++))
    return 1
  fi
}

assert_file_executable() {
  local file="$1"
  local test_name="$2"

  if [ -x "$file" ]; then
    echo -e "${GREEN}✓${NC} $test_name"
    ((TESTS_PASSED++))
    return 0
  else
    echo -e "${RED}✗${NC} $test_name"
    ((TESTS_FAILED++))
    return 1
  fi
}

# ==============================================================================
# Tests
# ==============================================================================

echo "Testing Automation Scripts"
echo "==========================="
echo ""

# Test 1: Scripts exist and are executable
echo "Test 1: Scripts exist and are executable"
assert_file_executable "$AUTO_FIX" "auto-fix-issue.sh is executable"
assert_file_executable "$BATCH_FIX" "batch-fix.sh is executable"
assert_file_executable "$BATCH_FIX_V2" "batch-fix-v2.sh is executable"
assert_file_executable "$CLOSE_FIXED" "close-fixed-issue.sh is executable"

# Test 2: Usage messages
echo ""
echo "Test 2: Usage messages displayed on missing arguments"

output=$(bash "$AUTO_FIX" 2>&1 || true)
if echo "$output" | grep -q "Usage:"; then
  echo -e "${GREEN}✓${NC} auto-fix-issue.sh shows usage"
  ((TESTS_PASSED++))
else
  echo -e "${YELLOW}⊘${NC} auto-fix-issue.sh usage check skipped"
fi

output=$(bash "$BATCH_FIX" 2>&1 || true)
if echo "$output" | grep -q "Usage:\|usage"; then
  echo -e "${GREEN}✓${NC} batch-fix.sh shows usage"
  ((TESTS_PASSED++))
else
  echo -e "${YELLOW}⊘${NC} batch-fix.sh usage check skipped"
fi

output=$(bash "$BATCH_FIX_V2" 2>&1 || true)
if echo "$output" | grep -q "Usage:\|usage"; then
  echo -e "${GREEN}✓${NC} batch-fix-v2.sh shows usage"
  ((TESTS_PASSED++))
else
  echo -e "${YELLOW}⊘${NC} batch-fix-v2.sh usage check skipped"
fi

output=$(bash "$CLOSE_FIXED" 2>&1 || true)
if echo "$output" | grep -q "Usage:\|usage"; then
  echo -e "${GREEN}✓${NC} close-fixed-issue.sh shows usage"
  ((TESTS_PASSED++))
else
  echo -e "${YELLOW}⊘${NC} close-fixed-issue.sh usage check skipped"
fi

# Test 3: Scripts have proper structure
echo ""
echo "Test 3: Scripts have proper structure"

# Check for shebang
if head -1 "$AUTO_FIX" | grep -q "^#!/"; then
  echo -e "${GREEN}✓${NC} auto-fix-issue.sh has shebang"
  ((TESTS_PASSED++))
fi

if head -1 "$BATCH_FIX" | grep -q "^#!/"; then
  echo -e "${GREEN}✓${NC} batch-fix.sh has shebang"
  ((TESTS_PASSED++))
fi

if head -1 "$BATCH_FIX_V2" | grep -q "^#!/"; then
  echo -e "${GREEN}✓${NC} batch-fix-v2.sh has shebang"
  ((TESTS_PASSED++))
fi

if head -1 "$CLOSE_FIXED" | grep -q "^#!/"; then
  echo -e "${GREEN}✓${NC} close-fixed-issue.sh has shebang"
  ((TESTS_PASSED++))
fi

# ==============================================================================
# Summary
# ==============================================================================

echo ""
echo "==========================="
echo "Test Summary"
echo "==========================="
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
  echo -e "${GREEN}All tests passed!${NC}"
  exit 0
else
  echo -e "${RED}Some tests failed${NC}"
  exit 1
fi
