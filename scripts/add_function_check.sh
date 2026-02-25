#!/bin/bash

# Function to add function size check to quality-gates.sh
add_function_check() {
    local file=$1
    local temp_file=$(mktemp)
    
    # Create the function check block
    cat > /tmp/function_check.txt << 'EOF'

# Check 10b: Function size limit (max 50 lines per function)
if [ "$USE_RG" = true ]; then
    echo -n "Checking function size (max 50 lines)... "
    FUNCTION_VIOLATIONS=""
    for f in $(find . -name "*.py" ! -path "./.venv/*" ! -path "./deps/*" ! -path "./.git/*" ! -path "./build/*" ! -path "./scripts/*" 2>/dev/null); do
        if [ -f "$f" ]; then
            # Use awk to count lines between function definitions
            violations=$(awk '
                /^[[:space:]]*def [^_]|^[[:space:]]*async def [^_]/ {
                    if (func_start > 0 && NR - func_start > 50) {
                        print FILENAME ":" func_start ":" func_name " (" (NR - func_start) " lines, max 50)"
                    }
                    func_start = NR
                    func_name = $0
                    gsub(/^[[:space:]]*/, "", func_name)
                    next
                }
                /^[[:space:]]*def |^[[:space:]]*class |^$/ {
                    if (func_start > 0 && NR - func_start > 50) {
                        print FILENAME ":" func_start ":" func_name " (" (NR - func_start) " lines, max 50)"
                    }
                    func_start = 0
                }
                END {
                    if (func_start > 0 && NR - func_start > 50) {
                        print FILENAME ":" func_start ":" func_name " (" (NR - func_start) " lines, max 50)"
                    }
                }
            ' FILENAME="$f" "$f" 2>/dev/null || true)
            if [ -n "$violations" ]; then
                FUNCTION_VIOLATIONS="${FUNCTION_VIOLATIONS}\n$violations"
            fi
        fi
    done
    if [ -n "$FUNCTION_VIOLATIONS" ]; then
        echo -e "${RED}FAIL${NC}"
        echo -e "${YELLOW}Functions exceed 50-line limit (split by SRP):${NC}"
        echo -e "$FUNCTION_VIOLATIONS"
        CODEX_VIOLATIONS=$((CODEX_VIOLATIONS + 1))
    else
        echo -e "${GREEN}PASS${NC}"
    fi
fi

EOF
    
    # Find the line with "# Check 11:" and insert before it
    awk '
    /^# Check 11:/ {
        # Read and insert the function check block
        while ((getline line < "/tmp/function_check.txt") > 0) {
            print line
        }
        close("/tmp/function_check.txt")
    }
    {print}
    ' "$file" > "$temp_file"
    
    # Replace original file
    mv "$temp_file" "$file"
    chmod +x "$file"
    
    # Clean up temp file
    rm -f /tmp/function_check.txt
    
    echo "Function size check added to $file"
}

# Add to all repos that need it
cd /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos

for repo in unified-trade-execution-interface unified-ml-interface execution-algo-library unified-trading-deployment-v3 batch-audit-ui; do
    if [ -f "$repo/scripts/quality-gates.sh" ]; then
        if ! grep -q "Function size limit" "$repo/scripts/quality-gates.sh"; then
            echo "Adding function size check to $repo..."
            add_function_check "$repo/scripts/quality-gates.sh"
        else
            echo "$repo already has function size check"
        fi
    fi
done

echo "Function size checks addition completed"