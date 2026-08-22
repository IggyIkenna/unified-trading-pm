#!/bin/bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Kill zombie basedpyright and agent-CLI processes — moved from plans/tasks/claude-code/ 2026-07-27
# (that directory's guide docs were archived as superseded; this script's local-process-cleanup
# function is still live, distinct in scope from scripts/dev/dev-stop.sh's port-based UI/API cleanup).

echo "🔍 Finding zombie processes..."

# Find basedpyright processes
BASEDPYRIGHT_PIDS=$(ps aux | grep "basedpyright/index.js" | grep -v grep | awk '{print $2}')
if [ -n "$BASEDPYRIGHT_PIDS" ]; then
    echo "🧟 Found zombie basedpyright processes: $BASEDPYRIGHT_PIDS"
    echo "$BASEDPYRIGHT_PIDS" | xargs kill -9 2>/dev/null || true
    echo "✅ Killed basedpyright zombies"
else
    echo "✅ No basedpyright zombies found"
fi

# Find agent processes
AGENT_PIDS=$(ps aux | grep "cursor-agent.*index.js" | grep -v grep | awk '{print $2}')
if [ -n "$AGENT_PIDS" ]; then
    echo "🧟 Found zombie agent processes: $AGENT_PIDS"
    echo "$AGENT_PIDS" | xargs kill -9 2>/dev/null || true
    echo "✅ Killed agent zombies"
else
    echo "✅ No agent zombies found"
fi

# Find claude processes
CLAUDE_PIDS=$(ps aux | grep "claude --model" | grep -v grep | awk '{print $2}')
if [ -n "$CLAUDE_PIDS" ]; then
    echo "🧟 Found Claude Code processes: $CLAUDE_PIDS"
    echo "$CLAUDE_PIDS" | xargs kill -9 2>/dev/null || true
    echo "✅ Killed Claude Code processes"
else
    echo "✅ No Claude Code processes found"
fi

echo ""
echo "✅ All zombies eliminated!"
