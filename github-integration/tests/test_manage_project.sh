#!/usr/bin/env bash
# ==============================================================================
# Tests for manage-project.sh
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANAGE_PROJECT="$SCRIPT_DIR/../scripts/project-management/manage-project.sh"

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

assert_exit_code() {
    local expected=$1
    local actual=$2
    local test_name="$3"

    if [ "$actual" -eq "$expected" ]; then
        echo -e "${GREEN}✓${NC} $test_name (exit code: $actual)"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} $test_name (expected: $expected, got: $actual)"
        ((TESTS_FAILED++))
        return 1
    fi
}

# ==============================================================================
# Tests
# ==============================================================================

echo "Testing manage-project.sh"
echo "=========================="
echo ""

# Test 1: Script exists and is executable
echo "Test 1: Script exists and is executable"
if [ -x "$MANAGE_PROJECT" ]; then
    assert_success "Script is executable"
else
    echo -e "${RED}✗${NC} Script not executable: $MANAGE_PROJECT"
    ((TESTS_FAILED++))
fi

# Test 2: Help message works
echo ""
echo "Test 2: Help message"
output=$(bash "$MANAGE_PROJECT" 2>&1 || true)
echo "$output" | grep -q "Unified GitHub Project Management Script"
assert_success "Help message displayed"

# Test 3: Missing required arguments
echo ""
echo "Test 3: Error handling - missing arguments"
output=$(bash "$MANAGE_PROJECT" create 2>&1 || true)
echo "$output" | grep -q "Missing required option"
test_result=$?
assert_exit_code 0 $test_result "Create without --name shows error message"

output=$(bash "$MANAGE_PROJECT" wipe 2>&1 || true)
echo "$output" | grep -q "Missing required option"
test_result=$?
assert_exit_code 0 $test_result "Wipe without --project-number shows error message"

# Test 4: Invalid command
echo ""
echo "Test 4: Error handling - invalid command"
output=$(bash "$MANAGE_PROJECT" invalid-command 2>&1 || true)
echo "$output" | grep -q "Unknown command"
test_result=$?
assert_exit_code 0 $test_result "Invalid command shows error message"

# Test 5: Dry-run mode (no actual operations)
echo ""
echo "Test 5: Dry-run mode"
# This would require mocking gh CLI, skip for now
echo -e "${YELLOW}⊘${NC} Dry-run test skipped (requires gh CLI mocking)"

# ==============================================================================
# Summary
# ==============================================================================

echo ""
echo "=========================="
echo "Test Summary"
echo "=========================="
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
