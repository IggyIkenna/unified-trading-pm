#!/usr/bin/env bash
# ==============================================================================
# Quality Gates for GitHub Integration Scripts
# ==============================================================================
#
# This script runs all quality checks for github-integration scripts:
#   - Python script tests
#   - Bash script tests
#   - Script executable checks
#   - Documentation checks
#
# Usage:
#   bash scripts/quality-gates.sh
#   bash scripts/quality-gates.sh --no-tests  # Skip tests, only check structure
#
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Flags
RUN_TESTS=true

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-tests)
            RUN_TESTS=false
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}GitHub Integration Scripts: Quality Gates${NC}"
echo -e "${BLUE}======================================================================${NC}"
echo ""

CHECKS_PASSED=0
CHECKS_FAILED=0

# ==============================================================================
# Check 1: Script Structure
# ==============================================================================

echo -e "${BLUE}Check 1: Script Structure${NC}"
echo ""

# Check that all Python scripts have shebang
echo "Checking Python scripts have shebang..."
PYTHON_SCRIPTS=$(find "$PROJECT_ROOT/scripts" -name "*.py" -type f)
for script in $PYTHON_SCRIPTS; do
    first_line=$(head -1 "$script")
    if [[ "$first_line" != "#!/usr/bin/env python3" ]]; then
        echo -e "${RED}✗${NC} Missing shebang: $(basename $script)"
        ((CHECKS_FAILED++))
    else
        ((CHECKS_PASSED++))
    fi
done

# Check that all bash scripts have shebang
echo "Checking bash scripts have shebang..."
BASH_SCRIPTS=$(find "$PROJECT_ROOT/scripts" -name "*.sh" -type f)
for script in $BASH_SCRIPTS; do
    first_line=$(head -1 "$script")
    if [[ "$first_line" != "#!/usr/bin/env bash" ]] && [[ "$first_line" != "#!/bin/bash" ]]; then
        echo -e "${RED}✗${NC} Missing shebang: $(basename $script)"
        ((CHECKS_FAILED++))
    else
        ((CHECKS_PASSED++))
    fi
done

echo -e "${GREEN}✓${NC} Script structure checks complete"
echo ""

# ==============================================================================
# Check 2: Script Permissions
# ==============================================================================

echo -e "${BLUE}Check 2: Script Permissions${NC}"
echo ""

echo "Checking Python scripts are executable..."
for script in $PYTHON_SCRIPTS; do
    if [[ ! -x "$script" ]]; then
        echo -e "${YELLOW}⚠${NC} Not executable: $(basename $script)"
        chmod +x "$script"
        echo -e "${GREEN}✓${NC} Fixed: $(basename $script)"
    fi
    ((CHECKS_PASSED++))
done

echo "Checking bash scripts are executable..."
for script in $BASH_SCRIPTS; do
    if [[ ! -x "$script" ]]; then
        echo -e "${YELLOW}⚠${NC} Not executable: $(basename $script)"
        chmod +x "$script"
        echo -e "${GREEN}✓${NC} Fixed: $(basename $script)"
    fi
    ((CHECKS_PASSED++))
done

echo -e "${GREEN}✓${NC} Script permissions checks complete"
echo ""

# ==============================================================================
# Check 3: Documentation
# ==============================================================================

echo -e "${BLUE}Check 3: Documentation${NC}"
echo ""

# Check that docs directory exists
if [[ ! -d "$PROJECT_ROOT/docs" ]]; then
    echo -e "${RED}✗${NC} Missing docs directory"
    ((CHECKS_FAILED++))
else
    echo -e "${GREEN}✓${NC} docs/ directory exists"
    ((CHECKS_PASSED++))
fi

# Check that README exists
if [[ ! -f "$PROJECT_ROOT/docs/README.md" ]]; then
    echo -e "${YELLOW}⚠${NC} Missing docs/README.md"
else
    echo -e "${GREEN}✓${NC} docs/README.md exists"
    ((CHECKS_PASSED++))
fi

# Check that CROSS_CUTTING_ATTACHMENT.md exists
if [[ ! -f "$PROJECT_ROOT/docs/CROSS_CUTTING_ATTACHMENT.md" ]]; then
    echo -e "${RED}✗${NC} Missing docs/CROSS_CUTTING_ATTACHMENT.md"
    ((CHECKS_FAILED++))
else
    echo -e "${GREEN}✓${NC} docs/CROSS_CUTTING_ATTACHMENT.md exists"
    ((CHECKS_PASSED++))
fi

echo ""

# ==============================================================================
# Check 4: Tests
# ==============================================================================

if [[ "$RUN_TESTS" == "true" ]]; then
    echo -e "${BLUE}Check 4: Running Tests${NC}"
    echo ""

    # Run Python tests
    echo "Running Python tests..."
    if python3 "$PROJECT_ROOT/tests/test_scripts.py" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Python tests passed"
        ((CHECKS_PASSED++))
    else
        echo -e "${RED}✗${NC} Python tests failed"
        python3 "$PROJECT_ROOT/tests/test_scripts.py"
        ((CHECKS_FAILED++))
    fi

    # Run bash tests
    echo "Running bash tests..."
    if bash "$PROJECT_ROOT/tests/test_manage_project.sh" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Bash tests passed"
        ((CHECKS_PASSED++))
    else
        echo -e "${RED}✗${NC} Bash tests failed"
        bash "$PROJECT_ROOT/tests/test_manage_project.sh"
        ((CHECKS_FAILED++))
    fi

    # Run automation tests
    echo "Running automation tests..."
    if bash "$PROJECT_ROOT/tests/test_automation_scripts.sh" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Automation tests passed"
        ((CHECKS_PASSED++))
    else
        echo -e "${RED}✗${NC} Automation tests failed"
        bash "$PROJECT_ROOT/tests/test_automation_scripts.sh"
        ((CHECKS_FAILED++))
    fi

    echo ""
else
    echo -e "${YELLOW}⊘${NC} Tests skipped (--no-tests flag)"
    echo ""
fi

# ==============================================================================
# Summary
# ==============================================================================

echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}Quality Gates Summary${NC}"
echo -e "${BLUE}======================================================================${NC}"
echo ""
echo -e "Checks Passed: ${GREEN}$CHECKS_PASSED${NC}"
echo -e "Checks Failed: ${RED}$CHECKS_FAILED${NC}"
echo ""

if [[ $CHECKS_FAILED -eq 0 ]]; then
    echo -e "${GREEN}✓ All quality gates passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some quality gates failed${NC}"
    exit 1
fi
