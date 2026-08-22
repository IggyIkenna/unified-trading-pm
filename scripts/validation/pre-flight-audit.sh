#!/bin/bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Pre-Flight Audit for Quick Merge
# Runs BEFORE quality gates to catch issues early
#
# Stage 1: Check uncommitted changes in path dependencies
# Stage 2: Quality audit checks
#
# Usage: ./pre-flight-audit.sh <repo-name>

set -e

REPO_NAME="$1"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
REPO_DIR="$WORKSPACE_ROOT/$REPO_NAME"

cd "$REPO_DIR"

echo "=========================================="
echo "Pre-Flight Audit: $REPO_NAME"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0

# ==========================================
# Stage 1: Check Uncommitted Path Dependencies
# ==========================================

echo "Stage 1: Checking path dependencies for uncommitted changes..."
echo ""

# Read path dependencies from pyproject.toml
PATH_DEPS=()
if [ -f "pyproject.toml" ]; then
    # Extract path dependencies (e.g., unified-trading-library = { path = "../unified-trading-library", editable = true })
    while IFS= read -r line; do
        if [[ "$line" =~ path[[:space:]]*=[[:space:]]*\"\.\.\/([^\"]+)\" ]]; then
            dep="${BASH_REMATCH[1]}"
            PATH_DEPS+=("$dep")
        fi
    done < pyproject.toml
fi

if [ ${#PATH_DEPS[@]} -eq 0 ]; then
    echo "  ✅ No path dependencies found"
else
    echo "  Found ${#PATH_DEPS[@]} path dependencies:"
    for dep in "${PATH_DEPS[@]}"; do
        echo "    - $dep"
    done
    echo ""

    # Check each dependency for uncommitted changes
    for dep in "${PATH_DEPS[@]}"; do
        dep_path="$WORKSPACE_ROOT/$dep"

        if [ ! -d "$dep_path" ]; then
            echo -e "  ${YELLOW}⚠️  $dep: Directory not found (skipping)${NC}"
            continue
        fi

        cd "$dep_path"

        # Check for uncommitted changes
        if [ -n "$(git status --porcelain)" ]; then
            echo -e "  ${RED}❌ $dep: HAS UNCOMMITTED CHANGES${NC}"
            echo "     Changes:"
            git status --short | sed 's/^/       /'
            echo ""
            echo "     ACTION REQUIRED:"
            echo "       cd $dep_path"
            echo "       git add -A"
            echo "       git commit -m \"fix: update before downstream merge\""
            echo "       bash scripts/quickmerge.sh \"fix: update before downstream merge\""
            echo ""
            ERRORS=$((ERRORS + 1))
        else
            echo -e "  ${GREEN}✅ $dep: Clean (no uncommitted changes)${NC}"
        fi

        cd "$REPO_DIR"
    done
fi

echo ""

# Fail fast: uncommitted dep changes must be resolved before quality audit
if [ "$ERRORS" -gt 0 ]; then
    echo -e "${RED}❌ Pre-Flight Audit FAILED: $ERRORS dep(s) have uncommitted changes.${NC}"
    echo "Resolve the ACTION REQUIRED steps above, then re-run quickmerge."
    echo ""
    exit 1
fi

# ==========================================
# Stage 2: Quality Audit
# ==========================================

echo "Stage 2: Quality audit..."
echo ""

# Check quality gate audit factors (if script exists)
AUDIT_FACTORS="$WORKSPACE_ROOT/.cursor/scripts/check-audit-factors.sh"

if [ -f "$AUDIT_FACTORS" ]; then
    echo "  Running quality gate audit factors check..."
    if bash "$AUDIT_FACTORS" "$REPO_NAME"; then
        echo -e "  ${GREEN}✅ Audit factors check passed${NC}"
    else
        echo -e "  ${RED}❌ Audit factors check failed${NC}"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "  Creating quick audit factors check..."

    # Quick inline checks for common issues
    echo "  Checking for common violations..."

    # Check 1: E722 in global ignore
    if grep -q "^ignore = \[.*\"E722\"" pyproject.toml 2>/dev/null; then
        echo -e "    ${RED}❌ E722 (bare except) in global ignore${NC}"
        echo "       Move to per-file-ignores for scripts/* only"
        ERRORS=$((ERRORS + 1))
    else
        echo -e "    ${GREEN}✅ E722 not in global ignore${NC}"
    fi

    # Check 2: Hardcoded project IDs in tests
    if grep -rE "central-element-[0-9]+" tests/ 2>/dev/null | grep -v "# test-project acceptable" > /dev/null; then
        echo -e "    ${YELLOW}⚠️  Hardcoded GCP project ID found in tests${NC}"
        echo "       Use 'test-project' in tests instead"
    else
        echo -e "    ${GREEN}✅ No hardcoded project IDs in tests${NC}"
    fi

    # Check 3: Large files (>1500 lines) — exclude .venv, archive, site-packages
    large_files=$(find . -name "*.py" -not -path "./tests/*" -not -path "./scripts/*" -not -path "./.venv*" -not -path "*/.venv*" -not -path "*/site-packages/*" -not -path "*/archive/*" -not -path "./archive/*" -exec wc -l {} + 2>/dev/null | awk '$1 > 1500 && $2 != "total" {print $2}' | head -5)
    if [ -n "$large_files" ]; then
        echo -e "    ${YELLOW}⚠️  Large files found (>1500 lines):${NC}"
        echo "$large_files" | sed 's/^/       /'
        echo "       Consider splitting large files"
    else
        echo -e "    ${GREEN}✅ No files >1500 lines${NC}"
    fi

    # Check 4: Directories with >30 files (exclude gitignored, .cursor, .venv, archive, cursor-rules)
    big_dirs=""
    while IFS= read -r dir; do
        git check-ignore -q "$dir" 2>/dev/null && continue
        [[ "$dir" == ./.cursor* ]] && continue
        [[ "$dir" == */.venv* ]] && continue
        [[ "$dir" == */archive* ]] && continue
        [[ "$dir" == */cursor-rules* ]] && continue
        count=$(find "$dir" -maxdepth 1 -type f 2>/dev/null | wc -l | tr -d ' ')
        if [ "$count" -gt 30 ] 2>/dev/null; then
            big_dirs="${big_dirs}${dir} (${count} files)
"
        fi
    done < <(find . -type d -not -path './.git*' 2>/dev/null)
    if [ -n "$big_dirs" ]; then
        echo -e "    ${YELLOW}⚠️  Directories with >30 files:${NC}"
        echo "$big_dirs" | sed 's/^/       /'
        echo "       Consider splitting into subdirectories"
    else
        echo -e "    ${GREEN}✅ No directories >30 files${NC}"
    fi
fi

echo ""

# ==========================================
# Summary
# ==========================================

echo "=========================================="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ Pre-Flight Audit PASSED${NC}"
    echo "=========================================="
    exit 0
else
    echo -e "${RED}❌ Pre-Flight Audit FAILED ($ERRORS errors)${NC}"
    echo "=========================================="
    echo ""
    echo "Fix the issues above before running quickmerge."
    echo ""
    exit 1
fi
