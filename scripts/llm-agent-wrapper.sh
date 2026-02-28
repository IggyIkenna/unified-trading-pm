#!/bin/bash
# LLM-Agnostic Agent Wrapper
# Detects available LLM tools and uses the best one for fixing issues
#
# Usage: ./llm-agent-wrapper.sh <repo-name> <error-log-file> <prompt>
#
# Supports:
# - Cursor CLI agent (model: auto - FREE with Ultra)
# - Claude Code CLI (Anthropic API)
# - Aider (OpenAI/Anthropic API)
#
# Preference order: Cursor (free) > Claude Code > Aider

set -e

REPO_NAME="$1"
ERROR_LOG="$2"
PROMPT="$3"

WORKSPACE_ROOT="/Users/ikennaigboaka/Documents/repos/unified-trading-system-repos"
PARSER="$WORKSPACE_ROOT/.cursor/plans/tasks_claude_code/simple-parser.py"

# Read error log
ERROR_CONTEXT=$(cat "$ERROR_LOG")

# Enhanced prompt with error context (same pattern as run-agent.sh)
FULL_PROMPT="WORKSPACE CONTEXT:
- Workspace root: $WORKSPACE_ROOT
- Target repo: $REPO_NAME/
- You have READ access to entire workspace (codex, dependencies, workspace rules)
- You can ONLY EDIT files in $REPO_NAME/ directory
- Read unified-trading-codex/ for standards
- Read workspace .cursorrules and .cursor/rules/*.mdc
- Read path dependencies (../unified-trading-services, etc.)

TASK FOR $REPO_NAME:
Fix CI/CD issues reported by pre-push hook (act simulation)

ERROR OUTPUT:
$ERROR_CONTEXT

USER TASK:
$PROMPT

CRITICAL RESTRICTIONS:
- ONLY edit files in $REPO_NAME/ directory
- DO NOT edit unified-trading-codex/, unified-trading-services/, or other repos
- You can read everything, but edit only $REPO_NAME/

IMPORTANT: Only run basedpyright/quality-gates 2-3 times total (not every file) to avoid hanging:
- Once at start to see errors
- Once mid-way to check progress
- Once at end to verify 0 errors
"

# Detect available LLM tools
detect_llm_tool() {
    # Preference 1: Cursor CLI agent (FREE with Ultra)
    # Check for API key (CURSOR_API_KEY or GCP_PROJECT_ID for Secret Manager fetch)
    if command -v agent >/dev/null 2>&1 && { [ -n "${CURSOR_API_KEY:-}" ] || [ -n "${GCP_PROJECT_ID:-}" ]; }; then
        echo "cursor"
        return
    fi
    
    # Preference 2: Claude Code CLI
    if command -v claude >/dev/null 2>&1 && [ -n "$ANTHROPIC_API_KEY" ]; then
        echo "claude"
        return
    fi
    
    # Preference 3: Aider
    if command -v aider >/dev/null 2>&1; then
        echo "aider"
        return
    fi
    
    echo "none"
}

LLM_TOOL=$(detect_llm_tool)

case "$LLM_TOOL" in
    cursor)
        echo "🤖 Using Cursor CLI agent (model: auto - FREE)"
        
        # Get API key (never use world-readable temp file)
        if [ -z "${CURSOR_API_KEY:-}" ]; then
            PROJECT_ID="${GCP_PROJECT_ID:?GCP_PROJECT_ID must be set to fetch cursor-api-key}"
            CURSOR_API_KEY=$(gcloud secrets versions access latest --secret=cursor-api-key --project="$PROJECT_ID")
            export CURSOR_API_KEY
        fi
        
        # Set up environment
        export PATH="$HOME/.local/bin:$PATH"
        
        # Use agent CLI with same flags as run-agent.sh
        agent --api-key "$CURSOR_API_KEY" \
            --print \
            --model auto \
            --trust \
            --force \
            --output-format stream-json \
            --stream-partial-output \
            --workspace "$WORKSPACE_ROOT" \
            "$FULL_PROMPT" \
            2>&1 | python3 "$PARSER"
        ;;
    
    claude)
        echo "🤖 Using Claude Code CLI"
        
        # Use Claude Code CLI
        claude \
            --model claude-sonnet-4-5-20250929 \
            --dangerously-skip-permissions \
            "$FULL_PROMPT"
        ;;
    
    aider)
        echo "🤖 Using Aider"
        
        # Change to repo directory for Aider
        cd "$WORKSPACE_ROOT/$REPO_NAME"
        
        # Use Aider
        aider \
            --model sonnet \
            --yes-always \
            --message "$FULL_PROMPT"
        ;;
    
    none)
        echo "❌ No LLM tool available"
        echo ""
        echo "Install one of:"
        echo "  - Cursor CLI agent: Check if 'agent' command exists"
        echo "    - Set: export GCP_PROJECT_ID=your-project (to fetch from Secret Manager)"
        echo "    - Or: export CURSOR_API_KEY=\$(gcloud secrets versions access latest --secret=cursor-api-key --project=\$GCP_PROJECT_ID)"
        echo ""
        echo "  - Claude Code CLI: claude --version"
        echo "    - Set: export ANTHROPIC_API_KEY=sk-ant-..."
        echo ""
        echo "  - Aider: pip install aider-chat"
        echo "    - Set: export OPENAI_API_KEY=... or ANTHROPIC_API_KEY=..."
        exit 1
        ;;
esac

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo "✅ LLM agent completed successfully"
else
    echo "❌ LLM agent failed (exit code: $exit_code)"
fi

exit $exit_code
