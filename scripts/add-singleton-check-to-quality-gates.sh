#!/bin/bash
# Add singleton adapter pattern check to all service quality gates
# This script adds the check after the last codex compliance check and before the summary

set -e

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
    "unified-trading-services"
    "unified-config-interface"
    "unified-events-interface"
)

SINGLETON_CHECK='
# Check: Singleton adapter pattern
echo -n "Checking for singleton adapter caching... "

FACTORY_FILES=$(find . -name "factory.py" -o -name "adapter_loader.py" -o -name "*_factory.py" 2>/dev/null | grep -v "__pycache__" | grep -v ".venv" | grep -v "deps/" | grep -v "build/")

if [ -z "$FACTORY_FILES" ]; then
    echo -e "${GREEN}N/A (no factory files)${NC}"
else
    VIOLATIONS=0
    for file in $FACTORY_FILES; do
        # Check for cache declaration (_ADAPTER_CACHE, _adapter_cache, _instance_cache, *_client_cache)
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
    else
        echo -e "${YELLOW}See: .cursor/rules/singleton-adapter-pattern.mdc${NC}"
        echo -e "${YELLOW}Codex: unified-trading-codex/03-observability/README.md#lazy-loading${NC}"
        CODEX_VIOLATIONS=$((CODEX_VIOLATIONS + VIOLATIONS))
    fi
fi
'

WORKSPACE_ROOT="/Users/ikennaigboaka/Documents/repos/unified-trading-system-repos"

for repo in "${REPOS[@]}"; do
    QUALITY_GATES="$WORKSPACE_ROOT/$repo/scripts/quality-gates.sh"
    
    if [ ! -f "$QUALITY_GATES" ]; then
        echo "⚠️  $repo: No quality-gates.sh found, skipping"
        continue
    fi
    
    # Check if already has singleton check
    if grep -q "Singleton Adapter Pattern\|singleton adapter caching" "$QUALITY_GATES"; then
        echo "✅ $repo: Already has singleton check"
        continue
    fi
    
    # Find the line number where we should insert (before "# Summary" line)
    LINE_NUM=$(grep -n "^# Summary$" "$QUALITY_GATES" | head -1 | cut -d: -f1)
    
    if [ -z "$LINE_NUM" ]; then
        echo "⚠️  $repo: Could not find '# Summary' marker, skipping"
        continue
    fi
    
    # Create temp file with inserted check
    {
        head -n $((LINE_NUM - 1)) "$QUALITY_GATES"
        echo "$SINGLETON_CHECK"
        tail -n +$LINE_NUM "$QUALITY_GATES"
    } > "$QUALITY_GATES.tmp"
    
    # Replace original file
    mv "$QUALITY_GATES.tmp" "$QUALITY_GATES"
    
    echo "✅ $repo: Added singleton pattern check"
done

echo ""
echo "✅ Singleton pattern check added to all eligible repos"
