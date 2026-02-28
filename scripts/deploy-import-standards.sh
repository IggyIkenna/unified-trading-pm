#!/bin/bash
#
# Deploy import standards to multiple repositories
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Base directory
BASE_DIR="/Users/ikennaigboaka/Documents/repos/unified-trading-system-repos"

# Target repositories
REPOS=(
    "unified-events-interface"
    "unified-domain-client" 
    "unified-market-interface"
    "unified-trade-execution-interface"
    "unified-ml-interface"
    "execution-algo-library"
)

# Track results
declare -a RESULTS

for repo in "${REPOS[@]}"; do
    echo -e "${BLUE}=======================================================${NC}"
    echo -e "${BLUE}Deploying import standards to $repo${NC}"
    echo -e "${BLUE}=======================================================${NC}"
    
    repo_path="$BASE_DIR/$repo"
    
    if [ ! -d "$repo_path" ]; then
        echo -e "${RED}❌ Repository not found: $repo_path${NC}"
        RESULTS+=("$repo: NOT_FOUND")
        continue
    fi
    
    cd "$repo_path"
    
    # Step 1: Copy import checker script
    echo -e "${YELLOW}Step 1: Copying import checker script...${NC}"
    mkdir -p .cursor/scripts
    cp "$BASE_DIR/.cursor/scripts/check-import-patterns.py" .cursor/scripts/
    chmod +x .cursor/scripts/check-import-patterns.py
    
    # Step 2: Check if quality gates exist and integrate
    if [ -f "scripts/quality-gates.sh" ]; then
        echo -e "${YELLOW}Step 2: Integrating into quality gates...${NC}"
        
        # Check if import pattern check is already integrated
        if grep -q "IMPORT PATTERN STANDARDS" scripts/quality-gates.sh; then
            echo -e "${GREEN}✅ Import pattern check already integrated${NC}"
        else
            # Add import pattern check after linting
            # This is a simplified version - for production, we'd need more sophisticated integration
            echo -e "${YELLOW}⚠️  Manual integration needed for quality gates${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  No quality-gates.sh found${NC}"
    fi
    
    # Step 3: Update pre-commit config if it exists
    if [ -f ".pre-commit-config.yaml" ]; then
        echo -e "${YELLOW}Step 3: Updating pre-commit config...${NC}"
        
        # Check if import pattern check is already in pre-commit
        if grep -q "check-import-patterns" .pre-commit-config.yaml; then
            echo -e "${GREEN}✅ Import pattern check already in pre-commit config${NC}"
        else
            # Add to pre-commit (simplified - would need proper YAML parsing in production)
            echo -e "${YELLOW}⚠️  Manual integration needed for pre-commit config${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  No .pre-commit-config.yaml found${NC}"
    fi
    
    # Step 4: Run import checker to find violations
    echo -e "${YELLOW}Step 4: Checking for import violations...${NC}"
    
    if python3 .cursor/scripts/check-import-patterns.py > /tmp/${repo}_violations.txt 2>&1; then
        echo -e "${GREEN}✅ No import violations found${NC}"
        RESULTS+=("$repo: NO_VIOLATIONS")
    else
        violations=$(grep "Found .* import pattern violations" /tmp/${repo}_violations.txt | grep -oE '[0-9]+' | head -1)
        echo -e "${YELLOW}Found $violations import violations${NC}"
        
        # Step 5: Auto-fix violations
        echo -e "${YELLOW}Step 5: Auto-fixing violations...${NC}"
        if python3 .cursor/scripts/check-import-patterns.py --fix > /tmp/${repo}_fixes.txt 2>&1; then
            echo -e "${GREEN}✅ Violations auto-fixed${NC}"
            RESULTS+=("$repo: FIXED_$violations")
        else
            echo -e "${RED}❌ Auto-fix failed${NC}"
            RESULTS+=("$repo: FIX_FAILED")
        fi
    fi
    
    echo ""
done

# Generate summary report
echo -e "${BLUE}=======================================================${NC}"
echo -e "${BLUE}DEPLOYMENT SUMMARY${NC}"
echo -e "${BLUE}=======================================================${NC}"

for result in "${RESULTS[@]}"; do
    repo=$(echo "$result" | cut -d':' -f1)
    status=$(echo "$result" | cut -d':' -f2)
    
    case $status in
        "NOT_FOUND")
            echo -e "$repo: ${RED}❌ Repository not found${NC}"
            ;;
        "NO_VIOLATIONS")
            echo -e "$repo: ${GREEN}✅ No violations found${NC}"
            ;;
        "FIXED_"*)
            violations=$(echo "$status" | cut -d'_' -f2)
            echo -e "$repo: ${GREEN}✅ Fixed $violations violations${NC}"
            ;;
        "FIX_FAILED")
            echo -e "$repo: ${RED}❌ Auto-fix failed${NC}"
            ;;
        *)
            echo -e "$repo: ${YELLOW}⚠️  Unknown status: $status${NC}"
            ;;
    esac
done

echo -e "${BLUE}=======================================================${NC}"
echo -e "${GREEN}Import standards deployment completed!${NC}"
echo -e "${YELLOW}Manual integration may be needed for quality gates and pre-commit configs.${NC}"