#!/bin/bash
# Parallel agent launcher for Claude Code
# Usage: ./run-parallel-agents.sh <repo1> <repo2> <repo3> <repo4> "<prompt>"
#
# Example:
# ./run-parallel-agents.sh unified-config-interface unified-events-interface instruments-service market-tick-data-handler "Fix all basedpyright errors"
#
# Features:
# - Launches up to 4 agents in parallel (max recommended)
# - Each agent gets full workspace context
# - Each agent restricted to edit only its target repo
# - Logs saved to /tmp/agent-{repo}.log
# - Pretty-printed output for each agent

set -e

# Parse arguments
REPOS=()
PROMPT=""

# Last argument is the prompt (in quotes)
for arg in "$@"; do
    PROMPT="$arg"
done

# All other arguments are repo names
for arg in "${@:1:$#-1}"; do
    REPOS+=("$arg")
done

# Validate
if [ ${#REPOS[@]} -eq 0 ]; then
    echo "Error: No repos specified"
    echo "Usage: $0 <repo1> [repo2] [repo3] [repo4] \"<prompt>\""
    exit 1
fi

if [ ${#REPOS[@]} -gt 4 ]; then
    echo "Error: Maximum 4 repos in parallel (got ${#REPOS[@]})"
    echo "Run in batches of 4"
    exit 1
fi

# Set up environment
export PATH="$HOME/.local/bin:$PATH"

# Get API key from temp file (should already exist)
if [ ! -f /tmp/cursor_key.txt ]; then
    echo "Getting API key from Secret Manager..."
    gcloud secrets versions access latest --secret=cursor-api-key --project=central-element-323112 > /tmp/cursor_key.txt
fi

export CURSOR_API_KEY=$(cat /tmp/cursor_key.txt)

# Workspace root
WORKSPACE_ROOT="/Users/ikennaigboaka/Documents/repos/unified-trading-system-repos"
PARSER="$WORKSPACE_ROOT/.cursor/plans/tasks_claude_code/simple-parser.py"

echo "=========================================="
echo "Launching ${#REPOS[@]} agents in parallel"
echo "=========================================="
echo ""

# Launch agents in parallel
PIDS=()
for repo in "${REPOS[@]}"; do
    echo "🚀 Launching agent for: $repo"
    
    # Enhanced prompt with workspace context and edit restrictions
    ENHANCED_PROMPT="WORKSPACE CONTEXT:
- Workspace root: $WORKSPACE_ROOT
- Target repo: $repo/
- You have READ access to entire workspace (codex, dependencies, workspace rules)
- You can ONLY EDIT files in $repo/ directory
- Read unified-trading-codex/ for standards
- Read workspace .cursorrules and .cursor/rules/*.mdc
- Read path dependencies (../unified-cloud-services, etc.)

TASK FOR $repo:
$PROMPT

CRITICAL RESTRICTIONS:
- ONLY edit files in $repo/ directory
- DO NOT edit unified-trading-codex/, unified-cloud-services/, or other repos
- You can read everything, but edit only $repo/

IMPORTANT: Only run basedpyright 2-3 times total (not every 5 files) to avoid hanging:
- Once at start to see errors
- Once mid-way to check progress
- Once at end to verify 0 errors
"
    
    # Launch agent in background, save output to log
    (
        agent --api-key "$CURSOR_API_KEY" \
            --print \
            --model auto \
            --trust \
            --force \
            --output-format stream-json \
            --stream-partial-output \
            --workspace "$WORKSPACE_ROOT" \
            "$ENHANCED_PROMPT" \
            2>&1 | python3 "$PARSER" | tee "/tmp/agent-${repo}.log"
    ) &
    
    PIDS+=($!)
    echo "   PID: $! | Log: /tmp/agent-${repo}.log"
    echo ""
    
    # Stagger launches by 2 seconds to avoid thundering herd
    if [ ${#PIDS[@]} -lt ${#REPOS[@]} ]; then
        sleep 2
    fi
done

echo "=========================================="
echo "All ${#REPOS[@]} agents launched!"
echo "=========================================="
echo ""
echo "Monitor logs:"
for repo in "${REPOS[@]}"; do
    echo "  tail -f /tmp/agent-${repo}.log"
done
echo ""
echo "Waiting for all agents to complete..."
echo ""

# Wait for all agents to complete
for i in "${!PIDS[@]}"; do
    pid=${PIDS[$i]}
    repo=${REPOS[$i]}
    
    echo "⏳ Waiting for $repo (PID: $pid)..."
    wait $pid
    exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo "✅ $repo completed successfully"
    else
        echo "❌ $repo failed (exit code: $exit_code)"
    fi
    echo ""
done

echo "=========================================="
echo "All agents completed!"
echo "=========================================="
echo ""
echo "Review logs:"
for repo in "${REPOS[@]}"; do
    echo "  cat /tmp/agent-${repo}.log"
done
echo ""
echo "Verify results:"
for repo in "${REPOS[@]}"; do
    echo "  cd $repo && basedpyright --level warning 2>&1 | tail -1"
done
