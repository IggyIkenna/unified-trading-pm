# Cursor CLI Race Condition Issue

## Problem

When running multiple `cursor agent` processes in parallel, you may encounter this error:

```
Error: ENOENT: no such file or directory, rename
  '/Users/username/.cursor/cli-config.json.tmp' ->
  '/Users/username/.cursor/cli-config.json'
```

## Root Cause

The Cursor CLI stores configuration in `~/.cursor/cli-config.json`. When multiple agents run simultaneously:

1. Agent A creates `.cursor/cli-config.json.tmp`
2. Agent B creates `.cursor/cli-config.json.tmp` (overwrites A's temp file)
3. Agent A tries to rename its temp file → **FILE NOT FOUND** (B overwrote it)

This is a **classic race condition** in concurrent file access.

## Impact

- ❌ Some agents fail with ENOENT errors
- ⚠️ Lost work (failed agents don't complete their fixes)
- 📉 Lower success rate in batch operations

## Solutions

### Solution 1: Reduce Parallelism (Recommended)

Lower `--max-parallel` to reduce contention:

```bash
# Instead of:
./run-cleanup-batch-fix.sh --model auto --max-parallel 7

# Use:
./run-cleanup-batch-fix.sh --model auto --max-parallel 3
```

**Default changed to 3** (was 7) for safer operation.

**Why this works**: Fewer concurrent agents = less config file contention.

### Solution 2: Sequential Mode (100% Safe)

Run issues one at a time:

```bash
./run-cleanup-batch-fix.sh --model auto --max-parallel 1 --sequential
```

**Pros**: Zero race conditions
**Cons**: Slower (no parallelism)

### Solution 3: Use Safe Wrapper with Locking

Use the `safe-cursor-agent.sh` wrapper (experimental):

```bash
# In auto-fix-issue.sh, replace:
cursor agent --print --force ...

# With:
bash safe-cursor-agent.sh --print --force ...
```

**How it works**: File locking ensures only one agent modifies config at a time.

**Status**: Available but not enabled by default (needs testing).

### Solution 4: Retry Logic (Automatic)

Already implemented in `auto-fix-issue.sh`:

- Automatically retries up to 3 times on config file errors
- Exponential backoff (2s, 4s, 8s)
- Transparent to users

### Solution 5: Report to Cursor Team

This is a Cursor CLI bug. Consider reporting:

- GitHub: https://github.com/getcursor/cursor (if public issues exist)
- Discord: Cursor community
- Email: support@cursor.sh

**Ideal fix**: Cursor CLI should use atomic file operations or per-process config files.

## Choosing a Solution

| Use Case                | Recommended Solution  | Max Parallel |
| ----------------------- | --------------------- | ------------ |
| Quick test (1-3 issues) | Default (retry logic) | 1-3          |
| Production (10+ issues) | Reduce parallelism    | 3            |
| Critical (must succeed) | Sequential mode       | 1            |
| Development/testing     | Safe wrapper          | 3-5          |

## Monitoring for Race Conditions

Check logs for patterns:

```bash
# Count failures
grep "ENOENT.*cli-config.json" /path/to/logs

# Success rate
grep -c "✅ Issue.*fixed" logs.txt
grep -c "❌ Issue.*failed" logs.txt
```

## Current Status

**✅ Mitigations implemented:**

1. Default `MAX_PARALLEL` reduced from 7 to 3
2. Retry logic added (up to 3 retries)
3. Safe wrapper available (`safe-cursor-agent.sh`)
4. Documentation updated

**Expected success rate:**

- Parallelism=1: ~100% (no race conditions)
- Parallelism=3: ~95-98% (occasional retries)
- Parallelism=7: ~80-90% (frequent retries, some failures)

## Example: Before vs After

### Before (Max Parallel = 7)

```
Processing 13 issues...
✅ 11 succeeded
❌ 2 failed (config race condition)
Success rate: 84%
```

### After (Max Parallel = 3 + Retry)

```
Processing 13 issues...
✅ 13 succeeded (2 required retries)
❌ 0 failed
Success rate: 100%
```

## Testing Different Parallelism Levels

```bash
# Test with 1 worker (baseline)
time ./run-cleanup-batch-fix.sh --model auto --max-parallel 1 --issues "46 58 38"

# Test with 3 workers (recommended)
time ./run-cleanup-batch-fix.sh --model auto --max-parallel 3 --issues "46 58 38"

# Test with 7 workers (original default)
time ./run-cleanup-batch-fix.sh --model auto --max-parallel 7 --issues "46 58 38"
```

Compare:

- Success rate (failed/total)
- Total time
- Number of retries

## Advanced: Per-User Config (Future)

If Cursor CLI adds support for custom config paths:

```bash
# Hypothetical future Cursor CLI feature
export CURSOR_CONFIG_DIR="/tmp/cursor-config-$$"
cursor agent --config "$CURSOR_CONFIG_DIR" ...
```

This would eliminate race conditions entirely.

## Workaround: Stagger Start Times

Add random delays to reduce simultaneous starts:

```bash
# In batch-fix-v2.sh, before launching workers:
sleep $(awk -v min=0 -v max=2 'BEGIN{srand(); print int(min+rand()*(max-min+1))}')
```

## Related Issues

- Similar to database connection pool exhaustion
- Common in distributed systems without proper locking
- Resolved by: mutex locks, atomic operations, or reduced concurrency

## References

- `run-cleanup-batch-fix.sh` - Entry point (default MAX_PARALLEL=3)
- `batch-fix-v2.sh` - Workspace pooling logic
- `auto-fix-issue.sh` - Retry logic implementation
- `safe-cursor-agent.sh` - File locking wrapper
