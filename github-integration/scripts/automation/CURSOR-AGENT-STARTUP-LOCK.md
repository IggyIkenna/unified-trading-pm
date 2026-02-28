# Cursor Agent Startup Lock - The Right Way

## Problem

Multiple `cursor agent` processes running in parallel cause race conditions on `~/.cursor/cli-config.json`:

```
ENOENT: no such file or directory, rename
  '/Users/user/.cursor/cli-config.json.tmp' ->
  '/Users/user/.cursor/cli-config.json'
```

## Wrong Solutions

### ❌ Lock entire agent run

**Problem**: Only 1 agent runs at a time (serial execution)

- 7 agents × 5 minutes each = 35 minutes total
- Wastes parallelism

### ❌ Retry entire agent run

**Problem**: Agents fail and waste time retrying (minutes per retry)

- 13 agents × 3 retries × 5 min = hours wasted

### ❌ No locking

**Problem**: Race conditions cause random failures

## ✅ Correct Solution: Brief Startup Lock

**Key insight**: The config file access only happens during the first ~5 seconds of agent startup, not during the entire
run.

### How it works:

```bash
# safe-cursor-agent.sh
1. Acquire lock (mkdir - atomic)
2. Start cursor agent in background
3. Hold lock for 10 seconds (covers config access)
4. Release lock (other agents can now start)
5. Wait for agent to complete (runs freely in parallel)
```

### Performance:

**Startup staggering:**

- Agent 1: starts immediately, releases lock after 10s
- Agent 2: waits ~0s, starts at 10s, releases at 20s
- Agent 3: waits ~10s, starts at 20s, releases at 30s
- Agent 7: waits ~60s, starts at 60s, releases at 70s

**Total time:**

- Staggered startup: 70 seconds (7 agents × 10s)
- Parallel execution: All 7 agents run simultaneously after startup
- Total: 70s + 5min = ~6 minutes (vs 35 minutes for serial)

### Benefits:

✅ Prevents race conditions (one startup at a time) ✅ Maintains parallelism (agents run together after startup) ✅
Predictable timing (no retries, no failures) ✅ Scales well (N agents = N × 10s startup + parallel run)

## Implementation

```bash
# Configuration
LOCK_TIMEOUT=120   # Must be > STARTUP_DELAY × max_parallel
STARTUP_DELAY=10   # Hold lock for 10s per agent

# Acquire lock (wait up to LOCK_TIMEOUT)
acquire_lock()

# Start background timer to release lock after STARTUP_DELAY
(sleep 10; release_lock) &

# Run agent synchronously (blocking)
cursor agent "$@"

# Timer releases lock after 10s, agent continues running freely
```

**Key improvement:** Agent runs **synchronously** (not backgrounded) to ensure config file access happens immediately
while lock is held. A background timer releases the lock after 10s, allowing the next agent to start while current agent
continues running.

**CRITICAL**: `LOCK_TIMEOUT` must be large enough for all agents to queue:

- Formula: `LOCK_TIMEOUT > STARTUP_DELAY × max_parallel`
- Example: 10 agents × 10s = 100s minimum (use 120s for margin)
- Too small → later agents timeout before acquiring lock

**Why synchronous is better:**

- ❌ **Background immediately**: Agent process might not start for 100ms, config access happens after lock released
- ✅ **Synchronous + timer**: Config access happens immediately while lock is held, timer releases for next agent

## Testing

```bash
# 7 agents in parallel
./run-cleanup-batch-fix.sh --max-parallel 7

Expected:
- Agent 1 starts: 0s
- Agent 2 starts: 10s
- Agent 3 starts: 20s
...
- All run together after startup
- No ENOENT errors
- Total time: ~6 minutes (not 35)
```

## Why This Works

The config file race condition is a **startup-only** problem:

1. **Startup** (0-5 seconds):
   - Read `cli-config.json`
   - Validate settings
   - Write updated config
   - **← RACE CONDITION HAPPENS HERE**

2. **Main execution** (5 seconds - 5 minutes):
   - Runs agent logic
   - No config file access
   - **← NO RACE CONDITION**

By locking only the first 10 seconds (with margin), we:

- Serialize the problematic part (startup)
- Parallelize the bulk of the work (main execution)

## Alternative Considered

**Isolated config per agent**:

```bash
CURSOR_USER_DATA_DIR="/tmp/agent-$$/config" cursor agent "$@"
```

**Issue**: Cursor CLI doesn't support `CURSOR_USER_DATA_DIR` (or similar env vars). We verified this with
`cursor agent --help` - no config directory options.

## Summary

| Approach         | Parallelism | Failures       | Time (7 agents)           |
| ---------------- | ----------- | -------------- | ------------------------- |
| No lock          | ✅ Full     | ❌ Random      | ~5-10 min (with failures) |
| Lock entire run  | ❌ None     | ✅ None        | ~35 min                   |
| Retry logic      | ⚠️ Degraded | ⚠️ Wastes time | ~10-15 min (retries)      |
| **Startup lock** | ✅ **Full** | ✅ **None**    | ✅ **~6 min**             |

**Result**: Best of all worlds - no failures, full parallelism, minimal overhead.
