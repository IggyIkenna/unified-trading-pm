#!/usr/bin/env bash
#
# Safe Cursor Agent Wrapper - Brief Startup Lock
#
# The race condition only happens during cursor agent STARTUP when it reads/writes
# ~/.cursor/cli-config.json. This takes ~2-5 seconds.
#
# Solution: Lock for 10 seconds at startup, then release and let agent run freely.
# This allows 7+ agents to run in parallel with minimal serialization.
#
# Usage: bash safe-cursor-agent.sh [cursor agent arguments...]

set -euo pipefail

LOCK_DIR="/tmp/cursor-agent-startup.lock"
LOCK_TIMEOUT=120 # Max seconds to wait for lock (must be > STARTUP_DELAY × max_parallel)
STARTUP_DELAY=10 # Keep lock for 10s (covers config file access at startup)

# Acquire lock with timeout using mkdir (atomic operation)
acquire_lock() {
  local start_time=$(date +%s)

  while true; do
    # Try to create lock directory (atomic operation)
    if mkdir "$LOCK_DIR" 2>/dev/null; then
      return 0 # Lock acquired
    fi

    # Check timeout
    local elapsed=$(($(date +%s) - start_time))
    if [ $elapsed -ge $LOCK_TIMEOUT ]; then
      echo "ERROR: Failed to acquire startup lock after ${LOCK_TIMEOUT}s" >&2
      return 1
    fi

    # Check if lock is stale (older than 15 seconds - something went wrong)
    if [ -d "$LOCK_DIR" ]; then
      local lock_age=$(($(date +%s) - $(stat -f %m "$LOCK_DIR" 2>/dev/null || stat -c %Y "$LOCK_DIR" 2>/dev/null || echo 0)))
      if [ $lock_age -gt 15 ]; then
        # Stale lock, remove it
        rmdir "$LOCK_DIR" 2>/dev/null || true
        continue
      fi
    fi

    # Wait before retry (with small jitter)
    sleep $(awk 'BEGIN{srand(); print 0.1 + (rand() * 0.1)}')
  done
}

# Release lock
release_lock() {
  rmdir "$LOCK_DIR" 2>/dev/null || true
}

# Acquire lock
if ! acquire_lock; then
  exit 1
fi

# Start a background timer to release the lock after STARTUP_DELAY
# This runs in parallel with the agent
(
  sleep "$STARTUP_DELAY"
  release_lock
) &
TIMER_PID=$!

# Run cursor agent synchronously (blocking)
# The lock will be released by the background timer after STARTUP_DELAY
cursor agent "$@"
EXIT_CODE=$?

# Clean up: kill the timer if agent finished early (lock might already be released, that's ok)
kill $TIMER_PID 2>/dev/null || true
wait $TIMER_PID 2>/dev/null || true

# Make sure lock is released (in case agent finished before timer)
release_lock

exit $EXIT_CODE
