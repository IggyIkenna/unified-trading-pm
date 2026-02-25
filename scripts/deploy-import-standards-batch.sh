#!/bin/bash
#
# Batch deployment script for import standards
#
set -e

REPOS=(
    "strategy-service"
    "execution-services"
    "position-balance-monitor-service"
    "risk-and-exposure-service"
    "features-calendar-service"
)

echo "Deploying import standards to remaining repositories..."
echo "====================================================="

for repo in "${REPOS[@]}"; do
    echo ""
    echo "Processing: $repo"
    echo "----------------------------------------"
    
    if [ ! -d "$repo" ]; then
        echo "❌ Repository $repo not found, skipping..."
        continue
    fi
    
    # 1. Create .cursor/scripts directory
    echo "📁 Creating .cursor/scripts directory..."
    mkdir -p "$repo/.cursor/scripts/"
    
    # 2. Copy import checker script
    echo "📋 Copying import checker script..."
    cp .cursor/scripts/check-import-patterns.py "$repo/.cursor/scripts/"
    chmod +x "$repo/.cursor/scripts/check-import-patterns.py"
    
    # 3. Find violations before fixing
    echo "🔍 Checking for violations..."
    cd "$repo"
    violation_count=$(python3 .cursor/scripts/check-import-patterns.py 2>&1 | grep "Total violations:" | awk '{print $3}' || echo "0")
    echo "Found $violation_count violations"
    
    # 4. Fix violations
    if [ "$violation_count" != "0" ]; then
        echo "🔧 Fixing violations..."
        python3 .cursor/scripts/check-import-patterns.py --fix > /dev/null 2>&1
        echo "Fixed $violation_count violations"
    fi
    
    # 5. Add to quality gates if they exist
    if [ -f "scripts/quality-gates.sh" ]; then
        echo "⚙️ Updating quality gates..."
        # This is a simplified integration - each repo may need specific adjustments
        if ! grep -q "IMPORT PATTERN STANDARDS" scripts/quality-gates.sh; then
            # Add import check before type checking
            sed -i.bak '/TYPE CHECKING/i\
# ============================================================================\
# IMPORT PATTERN STANDARDS\
# ============================================================================\
echo -e "\\n${BLUE}IMPORT PATTERN STANDARDS${NC}"\
echo "----------------------------------------------------------------------"\
\
IMPORT_STATUS=0\
\
if [ -f ".cursor/scripts/check-import-patterns.py" ]; then\
    echo "Checking external import patterns..."\
    if $PYTHON_CMD .cursor/scripts/check-import-patterns.py --verbose; then\
        echo -e "${GREEN}✅ Import patterns PASSED${NC}"\
    else\
        echo -e "${RED}❌ Import patterns FAILED${NC}"\
        echo -e "${YELLOW}Auto-fix with: $PYTHON_CMD .cursor/scripts/check-import-patterns.py --fix${NC}"\
        IMPORT_STATUS=1\
    fi\
else\
    echo -e "${YELLOW}Import pattern checker not found, skipping...${NC}"\
fi\
\
# ============================================================================\
' scripts/quality-gates.sh
        fi
        
        # Add to summary if not already there
        if ! grep -q "Import.*PASSED" scripts/quality-gates.sh; then
            sed -i.bak '/Linting.*PASSED/a\
if [ $IMPORT_STATUS -eq 0 ]; then\
    echo -e "Imports:  ${GREEN}✅ PASSED${NC}"\
else\
    echo -e "Imports:  ${RED}❌ FAILED${NC}"\
    OVERALL_STATUS=1\
fi
' scripts/quality-gates.sh
        fi
        echo "✅ Quality gates updated"
    else
        echo "⚠️ No quality gates found"
    fi
    
    # 6. Add to pre-commit hooks if they exist
    if [ -f ".pre-commit-config.yaml" ]; then
        echo "🎣 Updating pre-commit hooks..."
        if ! grep -q "check-import-patterns" .pre-commit-config.yaml; then
            # Add import checker before ruff
            sed -i.bak '/repos:/a\
  # Import pattern checker\
  - repo: local\
    hooks:\
      - id: check-import-patterns\
        name: Check external import patterns\
        entry: python3 .cursor/scripts/check-import-patterns.py\
        language: python\
        files: \\.py$\
        pass_filenames: false\
        stages: [commit]\
' .pre-commit-config.yaml
        fi
        echo "✅ Pre-commit hooks updated"
    else
        echo "⚠️ No pre-commit config found"
    fi
    
    # 7. Test that import checker passes
    echo "✅ Testing final state..."
    if python3 .cursor/scripts/check-import-patterns.py > /dev/null 2>&1; then
        echo "✅ Import checker passes"
    else
        echo "❌ Import checker still has violations"
    fi
    
    cd ..
    echo "✅ $repo completed"
done

echo ""
echo "====================================================="
echo "✅ Batch deployment completed!"
echo "====================================================="