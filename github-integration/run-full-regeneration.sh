#!/usr/bin/env bash
#
# Full Project Regeneration
#
# This script:
# 1. Wipes the GitHub project (background, waits for completion)
# 2. Generates all Epic/Task/Subtask issues
# 3. Runs the code standards diff checker
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=====================================================================${NC}"
echo -e "${BLUE}Full Project Regeneration${NC}"
echo -e "${BLUE}=====================================================================${NC}"
echo ""

# ============================================================================
# PHASE 1: Wipe Project
# ============================================================================
echo -e "${BLUE}[1/3] Wiping GitHub Project${NC}"
echo "----------------------------------------------------------------------"
echo ""

bash "$SCRIPT_DIR/wipe-project-background.sh"

echo ""
echo -e "${YELLOW}⏳ Waiting 5 seconds for GitHub API to settle...${NC}"
sleep 5

# ============================================================================
# PHASE 2: Generate Epics/Tasks/Subtasks
# ============================================================================
echo ""
echo -e "${BLUE}[2/3] Generating Epic/Task/Subtask Issues${NC}"
echo "----------------------------------------------------------------------"
echo ""

python3 "$SCRIPT_DIR/create-service-epics.py" --all-services

if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}❌ Epic generation failed!${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}⏳ Waiting 5 seconds for issues to be created...${NC}"
sleep 5

# ============================================================================
# PHASE 3: Run Code Standards Diff Checker
# ============================================================================
echo ""
echo -e "${BLUE}[3/3] Running Code Standards Diff Checker${NC}"
echo "----------------------------------------------------------------------"
echo ""

echo -e "${YELLOW}Scanning all services for coding standards violations...${NC}"
echo ""

# Get list of all service repos
SERVICES=(
    "instruments-service"
    "market-tick-data-handler"
    "market-data-processing-service"
    "features-calendar-service"
    "features-volatility-service"
    "features-delta-one-service"
    "features-onchain-service"
    "strategy-service"
    "ml-training-service"
    "ml-inference-service"
    "execution-services"
    "unified-trading-services"
    "unified-trading-deployment-v2"
)

TOTAL_VIOLATIONS=0

for service in "${SERVICES[@]}"; do
    echo -e "\n${BLUE}Scanning: $service${NC}"

    # Run diff checker (dry-run first to count violations)
    VIOLATIONS=$(python3 "$SCRIPT_DIR/run-diff-checker.py" --repo "IggyIkenna/$service" --dry-run 2>/dev/null | grep -c "Found violation" || echo "0")

    if [ "$VIOLATIONS" -gt 0 ]; then
        echo -e "  ${YELLOW}⚠️  Found $VIOLATIONS violations - creating issues${NC}"
        python3 "$SCRIPT_DIR/run-diff-checker.py" --repo "IggyIkenna/$service"
        TOTAL_VIOLATIONS=$((TOTAL_VIOLATIONS + VIOLATIONS))
    else
        echo -e "  ${GREEN}✅ No violations found${NC}"
    fi
done

# ============================================================================
# SUMMARY
# ============================================================================
echo ""
echo -e "${BLUE}=====================================================================${NC}"
echo -e "${BLUE}Regeneration Complete!${NC}"
echo -e "${BLUE}=====================================================================${NC}"
echo ""

echo -e "${GREEN}✅ Phase 1: Project wiped${NC}"
echo -e "${GREEN}✅ Phase 2: Epic/Task/Subtask issues created${NC}"
echo -e "${GREEN}✅ Phase 3: Code standards violations scanned${NC}"
echo ""

if [ $TOTAL_VIOLATIONS -gt 0 ]; then
    echo -e "${YELLOW}📊 Total coding standards violations found: $TOTAL_VIOLATIONS${NC}"
else
    echo -e "${GREEN}🎉 No coding standards violations found!${NC}"
fi

echo ""
echo -e "${BLUE}View project:${NC} https://github.com/users/IggyIkenna/projects/1"
echo ""
