#!/bin/bash
# Full Orchestrator - Processes all 24 repos
# Uses standalone agent CLI (10 parallel, no race conditions)

set -e

# Helper function: Run command with timeout (macOS compatible)
run_with_timeout() {
    local timeout=$1
    shift
    perl -e 'alarm shift; exec @ARGV' "$timeout" "$@"
}

# Configuration
WORKSPACE="/Users/ikennaigboaka/Documents/repos/unified-trading-system-repos"
LOG_DIR="/tmp/cursor-agent-logs-$(date +%Y%m%d-%H%M%S)"
MAX_PARALLEL=10  # Can run 10+ safely with standalone agent
PARSER="$WORKSPACE/unified-trading-codex/11-project-management/github-integration/scripts/utilities/parse-agent-logs.py"

# All 24 repos
REPOS=(
    "instruments-service"
    "market-tick-data-handler"
    "market-data-processing-service"
    "pnl-attribution-service"
    "features-calendar-service"
    "features-delta-one-service"
    "features-volatility-service"
    "features-onchain-service"
    "ml-training-service"
    "ml-inference-service"
    "strategy-service"
    "execution-services"
    "risk-and-exposure-service"
    "position-balance-monitor-service"
    "unified-trading-library"
    "unified-config-interface"
    "unified-events-interface"
    "unified-market-interface"
    "unified-trade-execution-interface"
    "unified-domain-client"
    "execution-algo-library"
    "alerting-service"
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
echo "Quality Gates Orchestrator (Full)"
echo -e "==========================================${NC}"
echo ""
echo -e "${GRAY}Repos: ${#REPOS[@]}${NC}"
echo -e "${GRAY}Max parallel: $MAX_PARALLEL${NC}"
echo -e "${GRAY}Workspace: $WORKSPACE${NC}"
echo -e "${GRAY}Log directory: $LOG_DIR${NC}"
echo ""

# Process in batches
for ((i=0; i<${#REPOS[@]}; i+=MAX_PARALLEL)); do
    batch=("${REPOS[@]:i:MAX_PARALLEL}")
    batch_num=$((i/MAX_PARALLEL + 1))
    total_batches=$(( (${#REPOS[@]} + MAX_PARALLEL - 1) / MAX_PARALLEL ))

    echo -e "${BLUE}━━━ Batch $batch_num/$total_batches (${#batch[@]} repos) ━━━${NC}"
    echo ""

    for ((j=0; j<${#batch[@]}; j++)); do
        repo="${batch[j]}"
        repo_num=$((i+j+1))

        (  # Run in background for parallel execution

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
    echo -e "  ${GRAY}🔧 Launching cursor agent (2-5 minutes)...${NC}"

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

    # Run cursor agent
    LOG_FILE="$LOG_DIR/$repo.log"
    START_TIME=$(date +%s)

            # Run standalone agent with pretty printing
            # Use API key if set, otherwise use existing auth
            # Always use stream-json with streaming for live output
            if [ -n "$CURSOR_API_KEY" ]; then
                if [ -f "$PARSER" ]; then
                    # With pretty printing (live progress) - workspace root for full context
                    agent --api-key "$CURSOR_API_KEY" --print --model auto --trust --force \
                        --output-format stream-json \
                        --stream-partial-output \
                        --workspace "$WORKSPACE" \
                        "$PROMPT" 2>&1 | \
                        python3 "$PARSER" | tee "$LOG_FILE"
                    EXIT_CODE=${PIPESTATUS[0]}
                else
                    # Without parser (raw stream-json output) - workspace root for full context
                    agent --api-key "$CURSOR_API_KEY" --print --model auto --trust --force \
                        --output-format stream-json \
                        --stream-partial-output \
                        --workspace "$WORKSPACE" \
                        "$PROMPT" | tee "$LOG_FILE"
                    EXIT_CODE=${PIPESTATUS[0]}
                fi
            else
                if [ -f "$PARSER" ]; then
                    # With pretty printing (live progress) - workspace root for full context
                    agent --print --model auto --trust --force \
                        --output-format stream-json \
                        --stream-partial-output \
                        --workspace "$WORKSPACE" \
                        "$PROMPT" 2>&1 | \
                        python3 "$PARSER" | tee "$LOG_FILE"
                    EXIT_CODE=${PIPESTATUS[0]}
                else
                    # Without parser (raw stream-json output) - workspace root for full context
                    agent --print --model auto --trust --force \
                        --output-format stream-json \
                        --stream-partial-output \
                        --workspace "$WORKSPACE" \
                        "$PROMPT" | tee "$LOG_FILE"
                    EXIT_CODE=${PIPESTATUS[0]}
                fi
            fi

    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))

    if [ $EXIT_CODE -eq 0 ]; then
        echo -e "  ${GREEN}✅ Cursor agent completed (${DURATION}s)${NC}"
    else
        echo -e "  ${RED}❌ Cursor agent failed (exit $EXIT_CODE, ${DURATION}s)${NC}"
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

        ) &  # Background process
    done

    # Wait for batch to complete
    echo -e "${GRAY}Waiting for batch $batch_num...${NC}"
    wait
    echo ""
done

# Calculate final stats
FIXED=$(grep -c ":fixed$" "$STATE_FILE" 2>/dev/null || echo 0)
FAILED=$(grep -c ":failed:" "$STATE_FILE" 2>/dev/null || echo 0)
PARTIAL=$(grep -c ":partial:" "$STATE_FILE" 2>/dev/null || echo 0)
SKIPPED=$(grep -c ":skipped$" "$STATE_FILE" 2>/dev/null || echo 0)

echo -e "${BOLD}=========================================="
echo "Summary"
echo -e "==========================================${NC}"
echo ""
echo -e "Total:          ${#REPOS[@]}"
echo -e "${GREEN}Fixed:          $FIXED${NC}"
echo -e "${YELLOW}Partial:        $PARTIAL${NC}"
echo -e "${GRAY}Skipped:        $SKIPPED${NC}"
echo ""
echo -e "${GRAY}Logs: $LOG_DIR${NC}"
echo ""

if [ $FAILED -eq 0 ] && [ $PARTIAL -eq 0 ]; then
    echo -e "${GREEN}${BOLD}🎉 All repos fixed!${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  Some repos need review:${NC}"
    grep -E ":partial:" "$STATE_FILE" 2>/dev/null | sed 's/^/  - /' || true
    exit 1
fi
