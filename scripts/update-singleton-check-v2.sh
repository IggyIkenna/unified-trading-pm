#!/bin/bash
# Update singleton check to be smarter - only check files with get_ functions
# This avoids false positives on pure static factories (like CloudAuthFactory)

REPOS=(
    "features-delta-one-service"
    "features-calendar-service"
    "features-volatility-service"
    "features-onchain-service"
    "ml-training-service"
    "ml-inference-service"
    "strategy-service"
    "execution-services"
    "position-balance-monitor-service"
    "risk-and-exposure-service"
    "market-data-processing-service"
    "unified-cloud-services"
    "unified-config-interface"
    "unified-events-interface"
    "unified-market-interface"
    "unified-trade-execution-interface"
    "instruments-service"
    "market-tick-data-handler"
)

WORKSPACE_ROOT="/Users/ikennaigboaka/Documents/repos/unified-trading-system-repos"

# Improved check that only validates files with get_ factory functions
IMPROVED_CHECK='
FACTORY_FILES=$(find . -name "factory.py" -o -name "adapter_loader.py" -o -name "*_factory.py" 2>/dev/null | grep -v "__pycache__" | grep -v ".venv" | grep -v "deps/" | grep -v "build/")

if [ -z "$FACTORY_FILES" ]; then
    echo -e "${GREEN}N/A (no factory files)${NC}"
else
    VIOLATIONS=0
    for file in $FACTORY_FILES; do
        # Only check files that have get_ factory functions (not pure static factories)
        if ! grep -q "^def get_\|^    def get_" "$file"; then
            continue  # Skip files without get_ functions
        fi
        
        # Check for cache declaration
        if ! grep -q "_ADAPTER_CACHE.*Dict\|_adapter_cache.*Dict\|_instance_cache.*Dict\|_client_cache.*dict\|_ADAPTER_CACHE.*dict\|_adapter_cache.*dict\|_instance_cache.*dict" "$file"; then
            echo -e "${RED}FAIL${NC}"
            echo -e "${YELLOW}Missing adapter/client cache declaration in: $file${NC}"
            echo -e "${YELLOW}Required: _ADAPTER_CACHE: Dict[str, BaseAdapter] = {}${NC}"
            VIOLATIONS=$((VIOLATIONS + 1))
        # Check for cache usage (check before create)
        elif ! grep -q "if.*in _.*_cache\|if.*in _.*CACHE\|if.*in .*_cache\|if.*in .*CACHE" "$file"; then
            echo -e "${RED}FAIL${NC}"
            echo -e "${YELLOW}Missing cache check in: $file${NC}"
            echo -e "${YELLOW}Required: if cache_key in _ADAPTER_CACHE: return _ADAPTER_CACHE[cache_key]${NC}"
            VIOLATIONS=$((VIOLATIONS + 1))
        fi
    done
    
    if [ $VIOLATIONS -eq 0 ]; then
        echo -e "${GREEN}PASS${NC}"
    fi
fi
'

for repo in "${REPOS[@]}"; do
    QUALITY_GATES="$WORKSPACE_ROOT/$repo/scripts/quality-gates.sh"
    
    if [ ! -f "$QUALITY_GATES" ]; then
        echo "⚠️  $repo: No quality-gates.sh found, skipping"
        continue
    fi
    
    # Check if has the old check
    if ! grep -q "singleton adapter caching" "$QUALITY_GATES"; then
        echo "⚠️  $repo: No singleton check found, skipping"
        continue
    fi
    
    # Replace the FACTORY_FILES loop with improved version
    # This is a bit tricky - we'll use sed to replace between specific markers
    
    # Use perl for multi-line replacement
    perl -i -0pe 's/FACTORY_FILES=\$\(find.*?\n.*?\nif \[ -z "\$FACTORY_FILES" \]; then.*?fi\s*\n\s*if \[ \$VIOLATIONS -eq 0 \]; then.*?fi\s*\nfi/$ENV{IMPROVED_CHECK}/s' "$QUALITY_GATES"
    
    echo "✅ $repo: Updated to improved singleton check"
done

echo ""
echo "✅ Singleton checks updated to avoid false positives on static factories"
