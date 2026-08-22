#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# spawn-local-slot.sh — spawn a Claude session in a local tmux pointed at the VM dashboard.
#
# Operator: Ikenna laptop (local-mac backend). Workers boot in a local tmux session named
# `orch-slot-<N>` (mirrors VM convention), run `claude --dangerously-skip-permissions`, and
# heartbeat back to the VM dashboard at https://api.agent-orchestrator.odum-research.com.
#
# Pre-req: tmux installed (`brew install tmux`).
#
# Usage:
#   bash unified-trading-pm/scripts/dev/spawn-local-slot.sh <SLOT_ID> <PROMPT_FILE>
#   bash unified-trading-pm/scripts/dev/spawn-local-slot.sh 1 /tmp/slot1_prompt.md
#
# Or paste a prompt inline:
#   echo "...prompt..." > /tmp/slot1.md && bash .../spawn-local-slot.sh 1 /tmp/slot1.md
#
# Attach to see live output:
#   tmux attach -t orch-slot-1

set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: $0 <SLOT_ID> <PROMPT_FILE>" >&2
  exit 1
fi

SLOT_ID="$1"
PROMPT_FILE="$2"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-/Users/ikennaigboaka/Code/unified-trading-system-repos}"
SESSION="orch-slot-${SLOT_ID}"
CWD="${WORKSPACE_ROOT}/.tabs/${SLOT_ID}"
ORCH_URL="${ORCH_URL:-https://api.agent-orchestrator.odum-research.com}"

if [[ ! -d "$CWD" ]]; then
  echo "error: worktree $CWD does not exist; run setup-tab-worktrees.sh --add-slot $SLOT_ID first" >&2
  exit 1
fi
if [[ ! -f "$PROMPT_FILE" ]]; then
  echo "error: prompt file $PROMPT_FILE not found" >&2
  exit 1
fi
if ! command -v tmux >/dev/null 2>&1; then
  echo "error: tmux not installed; run 'brew install tmux'" >&2
  exit 1
fi
if ! command -v claude >/dev/null 2>&1; then
  echo "error: claude CLI not installed; install Claude Code first" >&2
  exit 1
fi

# Kill any existing session for this slot (idempotent re-spawn).
tmux kill-session -t "$SESSION" 2>/dev/null || true

# Create detached session, claude running in the worktree.
tmux new-session -d -s "$SESSION" -c "$CWD" "claude --dangerously-skip-permissions"

# Wait briefly for claude TUI to be ready, then paste the prompt.
sleep 3
tmux load-buffer -b "boot-${SLOT_ID}" "$PROMPT_FILE"
tmux paste-buffer -t "$SESSION" -b "boot-${SLOT_ID}" -d
sleep 1
tmux send-keys -t "$SESSION" Enter

echo "Spawned local tmux session: $SESSION (cwd=$CWD)"
echo "Attach: tmux attach -t $SESSION"
echo "Kill:   tmux kill-session -t $SESSION"
echo ""
echo "Worker is on local-mac. Dashboard heartbeats target: $ORCH_URL"
echo "Boot prompt was loaded from: $PROMPT_FILE"
