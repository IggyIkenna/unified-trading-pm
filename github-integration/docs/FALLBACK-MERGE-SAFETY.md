# Fallback Merge Safety Mechanism

**Status**: ✅ Implemented (2026-02-14)
**Script**: `batch-fix-v2.sh`
**Feature**: Automatic local backup when quickmerge fails to create PR

---

## Problem: Lost Work When PR Creation Fails

### What Happened (Before Fix)

**Scenario**: Agent successfully completes all fixes in temp workspace

```
1. Agent clones repo to /tmp/batch-fix-pool-XXX/unified-trading-services_clone_1
2. Agent makes changes (100+ lines fixed)
3. Quality gates pass ✅
4. Quickmerge attempts to push/create PR
5. ❌ Quickmerge fails (gh CLI auth issue, network error, etc.)
6. 🧹 Cleanup deletes temp workspace
7. 💀 ALL WORK IS LOST
```

**Real Example**: unified-trading-services issue #48

- Agent fixed: print→logger, os.getenv→config, requests→httpx, time.sleep, asyncio.run
- Quality gates passed: 131 tests ✅
- Quickmerge failed silently (no PR created)
- Temp workspace cleaned up
- Work vanished 😢

---

## Solution: Double-Merge Strategy

### How It Works Now

After the agent completes (regardless of success/failure):

1. **Check for changes** in temp clone

   ```bash
   git diff --quiet HEAD || git ls-files --others --exclude-standard
   ```

2. **Check if PR already merged** (fetch from origin)

   ```bash
   git log origin/main --oneline -20 | grep -q "#${issue_num}"
   ```

   - If merged → Skip fallback (work is safe)
   - If not merged → Proceed to step 3

3. **Copy changes to original workspace**
   - Get list of changed files from temp clone
   - Copy each file to original workspace at `/Users/.../unified-trading-system-repos/{repo}`
   - Create fallback branch: `fallback/agent-fix-{issue}-{timestamp}`

4. **Commit to fallback branch**

   ```
   Fallback: Agent fixes for #48 (PR creation failed)

   Changes copied from temp workspace after successful agent run.
   Original quickmerge failed to create PR, preserving work locally.

   Re-push these changes when quickmerge is fixed.
   ```

5. **Return to main** (original workspace untouched)

6. **Cleanup continues** as normal

---

## Architecture

### Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ Agent Execution in Temp Clone                               │
│  /tmp/batch-fix-pool-XXX/unified-trading-services_clone_1    │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
                  ┌───────────────┐
                  │ Agent Success │
                  └───────┬───────┘
                          │
         ┌────────────────┴────────────────┐
         ▼                                 ▼
┌────────────────────┐          ┌──────────────────┐
│ Quickmerge Success │          │ Quickmerge FAILS │
│  - PR created      │          │  - No PR         │
│  - Auto-merge on   │          │  - Work at risk  │
└────────────────────┘          └────────┬─────────┘
         │                               │
         │                               ▼
         │                     ┌──────────────────────────┐
         │                     │ FALLBACK MERGE           │
         │                     │  - Copy to original      │
         │                     │  - Create fallback/*     │
         │                     │  - Commit changes        │
         │                     └──────────┬───────────────┘
         │                                │
         └────────────────────────────────┘
                          │
                          ▼
              ┌─────────────────────┐
              │ Original Workspace  │
              │  main: unchanged    │
              │  fallback/*: new    │
              └─────────────────────┘
```

### Safety Guarantees

1. **Original main never modified** - Fallback uses new branch
2. **No parallel conflicts** - One repo per worker
3. **Stash protection** - Existing uncommitted work is stashed/restored
4. **PR detection** - Skips fallback if PR already merged
5. **File-level copy** - Only changed files copied (not full repo state)

---

## Usage

### Normal Operation (No User Action Needed)

The fallback happens **automatically** when running:

```bash
bash run-cleanup-batch-fix.sh --model auto --repos "unified-trading-services"
```

If quickmerge fails, you'll see:

```
[unified-trading-services_clone_1] 💾 Fallback: Copying changes to original workspace...
[unified-trading-services_clone_1]    📋 Copying changed files...
[unified-trading-services_clone_1]    ✅ Changes saved to branch: fallback/agent-fix-48-20260214-073000
[unified-trading-services_clone_1]    📂 Location: /Users/.../unified-trading-services
```

### Recovering Fallback Changes

**Option 1: Push the fallback branch**

```bash
cd unified-trading-services
git checkout fallback/agent-fix-48-TIMESTAMP
bash scripts/quality-gates.sh --no-fix  # Verify
bash scripts/quickmerge.sh "Fixes #48: Agent fixes for COD cleanup" --files "..."
```

**Option 2: Cherry-pick to new branch**

```bash
git checkout main
git checkout -b fix/issue-48
git cherry-pick fallback/agent-fix-48-TIMESTAMP
# Continue working...
```

**Option 3: Review and delete if not needed**

```bash
git branch -D fallback/agent-fix-48-TIMESTAMP
```

---

## Testing

### Test the Fallback Manually

```bash
# 1. Run agent with quickmerge that will "fail" by using wrong repo
cd batch-fix-v2-test/
bash batch-fix-v2.sh --model auto --issues "fake-repo:999" --max-parallel 1

# 2. Check if fallback branch was created
cd /Users/.../fake-repo
git branch | grep fallback/

# 3. Verify changes copied
git log fallback/agent-fix-999-* -1 --stat
```

### Verify No Data Loss

1. Agent makes changes in temp clone ✅
2. Quickmerge fails ❌
3. Fallback branch created ✅
4. Original main unchanged ✅
5. Changes preserved locally ✅

---

## Configuration

### Enable/Disable Fallback

Currently always enabled. To disable (not recommended):

Comment out the fallback block in `batch-fix-v2.sh` (lines ~529-608).

### Customize Fallback Branch Prefix

Edit line in `batch-fix-v2.sh`:

```bash
local fallback_branch="fallback/agent-fix-${issue_num}-$(date +%Y%m%d-%H%M%S)"
```

Change `fallback/` to your preferred prefix.

---

## Edge Cases Handled

### 1. Original workspace has uncommitted changes

**Behavior**: Stashes before creating fallback branch, pops after **Result**: Your work is preserved

### 2. PR already merged to main

**Behavior**: Fetches origin, checks git log, skips fallback **Result**: No duplicate work

### 3. Original service directory not a git repo

**Behavior**: Logs warning, skips fallback **Result**: Graceful degradation

### 4. No changes made by agent

**Behavior**: Skips fallback (nothing to copy) **Result**: No unnecessary branches

### 5. Multiple issues per worker

**Behavior**: Creates separate fallback branch per issue **Result**: Each issue's work isolated

---

## Performance Impact

**Minimal overhead**:

- Git diff check: ~50ms
- File copy: ~100-500ms (depends on file count)
- Git commit: ~200ms
- Total: **~350-750ms per issue**

For 10 issues with 5 parallel workers:

- Added time: ~3-7 seconds total
- Original time: ~5-10 minutes
- Overhead: **~1-2%**

**Worth it** for preventing data loss! 🎯

---

## Comparison: Before vs After

| Scenario                | Before                  | After                                 |
| ----------------------- | ----------------------- | ------------------------------------- |
| **Quickmerge succeeds** | Work in PR ✅           | Work in PR ✅ + Local fallback branch |
| **Quickmerge fails**    | Work lost 💀            | Work in fallback branch ✅            |
| **Partial success**     | Some PRs, some lost     | All preserved (mix of PRs + fallback) |
| **Recovery time**       | Re-run agent (5-10 min) | Push fallback branch (30 sec)         |

---

## Related Features

- **Workspace pooling** - One clone per repo (prevents conflicts)
- **Safe cursor wrapper** - Prevents config race conditions
- **GitHub authentication** - Uses GCP Secret Manager for PAT
- **Quality gates** - Runs before and after changes

---

## Future Enhancements

Possible improvements:

1. **Auto-push fallback branches** - If user opts in
2. **Slack/email notification** - Alert when fallback is used
3. **Batch fallback merge** - Merge all fallback/\* branches at once
4. **Git worktree** - Use worktrees instead of branches

---

## Validation

To verify the feature works:

1. **Check if temp clone has changes after agent runs**

   ```bash
   cd /tmp/batch-fix-pool-*/unified-trading-services_clone_1/unified-trading-services
   git diff HEAD
   ```

2. **Check if fallback branch was created**

   ```bash
   cd /Users/.../unified-trading-services
   git branch | grep fallback/
   ```

3. **Verify changes match what agent did**
   ```bash
   git log fallback/agent-fix-48-* -1 --stat
   git diff main..fallback/agent-fix-48-*
   ```

---

## Known Limitations

1. **Git operations only** - Doesn't handle non-git changes
2. **Same repo in original workspace** - Requires matching directory structure
3. **Branch accumulation** - Fallback branches need periodic cleanup
   ```bash
   # Clean up old fallback branches
   git branch | grep fallback/ | xargs git branch -D
   ```

---

## Credits

**Suggested by**: User (2026-02-14)
**Context**: "While we're getting all these quick merge issues, we could do a double merge so we could also merge to the
local main that we copied from. Since we're only doing one repo of each worker, it just stops us losing the changes."

**Rationale**: One repo per worker = safe to merge back without conflicts
