#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Parallel agent launcher for Claude Code
#
# SSOT: unified-trading-pm/scripts/agents/run-parallel-agents.sh
#
# Launches up to 4 Claude Code / Cursor agents in parallel, each targeting a
# separate repo with full workspace context and per-repo edit restrictions.
#
# Usage (run from workspace root):
#   bash unified-trading-pm/scripts/agents/run-parallel-agents.sh <repo1> [repo2] [repo3] [repo4] "<prompt>"
#
# Examples:
#   bash unified-trading-pm/scripts/agents/run-parallel-agents.sh \
#       unified-config-interface unified-trading-library \
#       instruments-service market-tick-data-handler \
#       "Fix all basedpyright errors"
#
# Features:
# - Launches up to 4 agents in parallel (max recommended)
# - Each agent gets full workspace context via --workspace
# - Each agent restricted to edit only its target repo (via prompt)
# - Logs saved to /tmp/agent-{repo}.log
# - Detects available LLM tool: Cursor agent > Claude Code > (error)
#
# Prerequisites:
#   Cursor agent:    command -v agent  &&  CURSOR_API_KEY or GCP_PROJECT_ID set
#   Claude Code:     command -v claude &&  ANTHROPIC_API_KEY set

set -euo pipefail

# ── Resolve paths relative to this script (portable across users/machines) ──
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PM_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
WORKSPACE_ROOT="$(cd "$PM_DIR/.." && pwd)"
PARSER="$PM_DIR/plans/tasks/claude-code/simple-parser.py"

# ── Parse arguments (last arg = prompt, all prior = repo names) ──────────────
REPOS=()
PROMPT=""

for arg in "$@"; do
    PROMPT="$arg"
done

for arg in "${@:1:$#-1}"; do
    REPOS+=("$arg")
done

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

# ── Detect available LLM tool ────────────────────────────────────────────────
detect_llm_tool() {
    # Preference 1: Cursor CLI agent (FREE with Ultra)
    if command -v agent >/dev/null 2>&1 && { [ -n "${CURSOR_API_KEY:-}" ] || [ -n "${GCP_PROJECT_ID:-}" ]; }; then
        echo "cursor"
        return
    fi
    # Preference 2: Claude Code CLI
    if command -v claude >/dev/null 2>&1 && [ -n "${ANTHROPIC_API_KEY:-}" ]; then
        echo "claude"
        return
    fi
    echo "none"
}

LLM_TOOL=$(detect_llm_tool)

if [ "$LLM_TOOL" = "none" ]; then
    echo "❌ No LLM tool available. Set one of:"
    echo "  Cursor agent: export CURSOR_API_KEY=...  (or GCP_PROJECT_ID to fetch from Secret Manager)"
    echo "  Claude Code:  export ANTHROPIC_API_KEY=sk-ant-..."
    exit 1
fi

# ── Fetch Cursor API key from Secret Manager if needed ──────────────────────
if [ "$LLM_TOOL" = "cursor" ] && [ -z "${CURSOR_API_KEY:-}" ]; then
    PROJECT_ID="${GCP_PROJECT_ID:?GCP_PROJECT_ID must be set to fetch cursor-api-key from Secret Manager}"
    echo "Getting Cursor API key from Secret Manager..."
    CURSOR_API_KEY=$(gcloud secrets versions access latest --secret=cursor-api-key --project="$PROJECT_ID")
    export CURSOR_API_KEY
fi

# ── Launch ───────────────────────────────────────────────────────────────────
echo "=========================================="
echo "Launching ${#REPOS[@]} agents in parallel  [tool: $LLM_TOOL]"
echo "Workspace: $WORKSPACE_ROOT"
echo "=========================================="
echo ""

PIDS=()
for repo in "${REPOS[@]}"; do
    echo "🚀 Launching agent for: $repo"

    # Inject mandatory rules preamble (agents in --print mode CANNOT read files from disk)
    RULES_PREAMBLE=$(bash "$SCRIPT_DIR/inject-mandatory-rules.sh" "$WORKSPACE_ROOT" "$repo" 2>/dev/null) || {
        echo "❌ Failed to inject mandatory rules for $repo — aborting (agents must not run without rules)"
        exit 1
    }

    ENHANCED_PROMPT="${RULES_PREAMBLE}

TASK FOR $repo:
$PROMPT
"

    case "$LLM_TOOL" in
        cursor)
            (
                export PATH="$HOME/.local/bin:$PATH"
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
            ;;
        claude)
            (
                claude \
                    --dangerously-skip-permissions \
                    --print \
                    "$ENHANCED_PROMPT" \
                    2>&1 | tee "/tmp/agent-${repo}.log"
            ) &
            ;;
    esac

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

# ── Wait for completion ──────────────────────────────────────────────────────
FAILED=0
for i in "${!PIDS[@]}"; do
    pid=${PIDS[$i]}
    repo=${REPOS[$i]}
    echo "⏳ Waiting for $repo (PID: $pid)..."
    if wait "$pid"; then
        echo "✅ $repo completed successfully"
    else
        echo "❌ $repo failed (exit code: $?)"
        FAILED=$((FAILED + 1))
    fi
    echo ""
done

echo "=========================================="
echo "All agents completed! (${FAILED} failed)"
echo "=========================================="
echo ""
echo "Review logs:"
for repo in "${REPOS[@]}"; do
    echo "  cat /tmp/agent-${repo}.log"
done
echo ""
echo "Verify results (from workspace root):"
for repo in "${REPOS[@]}"; do
    echo "  (cd $WORKSPACE_ROOT/$repo && run_timeout 120 basedpyright . 2>&1 | tail -1)"
done

[ "$FAILED" -eq 0 ]
