#!/bin/bash
# Test Orchestrator - Uses standalone agent CLI
# Tests with 2 small repos

set -e

# Helper function: Run command with timeout (macOS compatible)
run_with_timeout() {
    local timeout=$1
    shift
    perl -e 'alarm shift; exec @ARGV' "$timeout" "$@"
}

# Configuration
WORKSPACE="/Users/ikennaigboaka/Documents/repos/unified-trading-system-repos"
LOG_DIR="/tmp/cursor-agent-test-$(date +%Y%m%d-%H%M%S)"
STATE_FILE="/tmp/quality-gates-state-test.txt"
PARSER="$WORKSPACE/.cursor/plans/tasks_claude_code/simple-parser.py"

# Test with 2 small repos
REPOS=(
    "unified-config-interface"
    "unified-events-interface"
)

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
GRAY='\033[0;90m'
BOLD='\033[1m'
NC='\033[0m'

# Ensure PATH includes standalone agent CLI
export PATH="$HOME/.local/bin:$PATH"

# Verify agent command works
if ! command -v agent &> /dev/null; then
    echo -e "${RED}❌ agent command not found${NC}"
    echo -e "${YELLOW}Install: curl https://cursor.com/install -fsS | bash${NC}"
    echo -e "${YELLOW}Then add to PATH: export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}"
    exit 1
fi

# Always use API key from Secret Manager (works across machines)
echo -e "${GRAY}🔐 Fetching API key from Secret Manager...${NC}"
if command -v gcloud &> /dev/null; then
    export CURSOR_API_KEY=$(gcloud secrets versions access latest --secret=cursor-api-key --project="${GCP_PROJECT_ID:?GCP_PROJECT_ID required}" 2>/dev/null)
    if [ -n "$CURSOR_API_KEY" ]; then
        echo -e "${GREEN}✅ API key loaded${NC}"
    else
        echo -e "${RED}❌ Failed to get API key from Secret Manager${NC}"
        echo -e "${YELLOW}Fallback: Checking local authentication...${NC}"
        if ! agent status &>/dev/null; then
            echo -e "${RED}❌ Not authenticated. Run: agent login${NC}"
            exit 1
        fi
        echo -e "${GREEN}✅ Using local authentication${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  gcloud not found, using local authentication...${NC}"
    if ! agent status &>/dev/null; then
        echo -e "${RED}❌ Not authenticated. Run: agent login${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Using local authentication${NC}"
fi
echo ""

# Create log directory
mkdir -p "$LOG_DIR"

echo -e "${BOLD}=========================================="
echo "Test Orchestrator"
echo -e "==========================================${NC}"
echo ""
echo -e "${GRAY}Testing with: ${REPOS[*]}${NC}"
echo -e "${GRAY}Workspace: $WORKSPACE${NC}"
echo -e "${GRAY}Log directory: $LOG_DIR${NC}"
echo ""

for ((i=0; i<${#REPOS[@]}; i++)); do
    repo="${REPOS[i]}"
    repo_num=$((i+1))
    
    echo -e "${BLUE}[$repo_num/${#REPOS[@]}]${NC} Processing ${BOLD}$repo${NC}..."
    
    # Check directory exists
    if [ ! -d "$WORKSPACE/$repo" ]; then
        echo -e "  ${RED}❌ Directory not found${NC}"
        echo ""
        continue
    fi
    
    cd "$WORKSPACE/$repo"
    
    # Audit
    echo -e "  ${GRAY}🔍 Auditing...${NC}"
    
    if ! command -v basedpyright &> /dev/null; then
        echo -e "  ${YELLOW}⚠️  basedpyright not found, assuming errors exist${NC}"
        ERRORS=999
    else
        # Parse "X errors, Y warnings, Z notes" format (macOS compatible)
        # Use 30 second timeout to prevent hanging
        ERRORS=$(run_with_timeout 30 basedpyright --level warning 2>&1 | tail -1 | sed -E 's/^([0-9]+) errors.*/\1/')
        EXIT_CODE=$?
        if [ $EXIT_CODE -eq 142 ] || [ $EXIT_CODE -eq 124 ]; then
            echo -e "  ${YELLOW}⚠️  basedpyright timed out (>30s), assuming errors exist${NC}"
            ERRORS=999
        elif ! [[ "$ERRORS" =~ ^[0-9]+$ ]]; then
            ERRORS=0
        fi
    fi
    
    if [ "$ERRORS" -eq 0 ]; then
        echo -e "  ${GREEN}✅ No errors, skipping${NC}"
        echo ""
        continue
    fi
    
    echo -e "  ${YELLOW}Found $ERRORS errors${NC}"
    echo -e "  ${GRAY}🔧 Launching agent (2-5 minutes)...${NC}"
    
    # Prepare prompt with workspace context and edit restrictions
    PROMPT="WORKSPACE CONTEXT:
- Workspace root: $WORKSPACE
- Target repo: $repo/
- You have READ access to entire workspace (codex, dependencies, workspace rules)
- You can ONLY EDIT files in $repo/ directory

TASK:
Fix all basedpyright errors. Apply:
1) No empty fallbacks (fail loud if config missing)
2) No Type Any (use specific types like dict[str, str])
3) No decorators (manual retry with for loop)
4) Read unified-trading-codex/06-coding-standards/ for canonical patterns
5) Read workspace .cursorrules and .cursor/rules/*.mdc for standards

IMPORTANT: Only run basedpyright 2-3 times total (not every 5 files):
- Once at start to see errors
- Once mid-way to check progress
- Once at end to verify 0 errors
Target: 0 errors.

CRITICAL RESTRICTIONS:
- ONLY edit files in $repo/ directory
- DO NOT edit unified-trading-codex/, unified-trading-library/, or other repos
- You can read everything, but edit only $repo/
"
    
    # Run standalone agent with pretty printing
    LOG_FILE="$LOG_DIR/$repo.log"
    START_TIME=$(date +%s)
    
    # Use API key if set, otherwise use existing auth
    # Always use stream-json with streaming for live output
    if [ -n "$CURSOR_API_KEY" ]; then
        # With pretty printing (live progress) - workspace root for full context
        agent --api-key "$CURSOR_API_KEY" --print --model auto --trust --force \
            --output-format stream-json \
            --stream-partial-output \
            --workspace "$WORKSPACE" \
            "$PROMPT" 2>&1 | \
            python3 "$PARSER"
        EXIT_CODE=${PIPESTATUS[0]}
    else
        # With pretty printing (live progress) - workspace root for full context
        agent --print --model auto --trust --force \
            --output-format stream-json \
            --stream-partial-output \
            --workspace "$WORKSPACE" \
            "$PROMPT" 2>&1 | \
            python3 "$PARSER"
        EXIT_CODE=${PIPESTATUS[0]}
    fi
    
    # Note: Output is shown live via parser, not saved to log
    # If you need logs, redirect parser output: | tee "$LOG_FILE"
    
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo -e "  ${GREEN}✅ Agent completed (${DURATION}s)${NC}"
    else
        echo -e "  ${RED}❌ Agent failed (exit $EXIT_CODE, ${DURATION}s)${NC}"
        echo -e "  ${GRAY}Last 5 lines:${NC}"
        tail -5 "$LOG_FILE" | sed 's/^/    /'
        echo ""
        continue
    fi
    
    # Verify
    echo -e "  ${GRAY}🔍 Verifying...${NC}"
    
    if command -v basedpyright &> /dev/null; then
        # Parse "X errors, Y warnings, Z notes" format (macOS compatible)
        # Use 30 second timeout to prevent hanging
        NEW_ERRORS=$(run_with_timeout 30 basedpyright --level warning 2>&1 | tail -1 | sed -E 's/^([0-9]+) errors.*/\1/')
        EXIT_CODE=$?
        if [ $EXIT_CODE -eq 142 ] || [ $EXIT_CODE -eq 124 ]; then
            echo -e "  ${YELLOW}⚠️  basedpyright verification timed out${NC}"
            NEW_ERRORS=999
        elif ! [[ "$NEW_ERRORS" =~ ^[0-9]+$ ]]; then
            NEW_ERRORS=0
        fi
        
        if [ "$NEW_ERRORS" -eq 0 ]; then
            echo -e "  ${GREEN}✅ Fixed: $ERRORS → 0 errors${NC}"
        else
            echo -e "  ${YELLOW}⚠️  Partial: $ERRORS → $NEW_ERRORS errors${NC}"
        fi
    fi
    
    echo -e "  ${GRAY}📄 Log: $LOG_FILE${NC}"
    echo ""
done

echo -e "${BOLD}=========================================="
echo "Test Complete"
echo -e "==========================================${NC}"
echo ""
echo -e "${GRAY}Logs: $LOG_DIR${NC}"
echo ""
echo -e "${GREEN}✅ Test completed!${NC}"
echo ""
echo -e "${YELLOW}Next:${NC} If successful, run full orchestrator.sh"
echo ""
