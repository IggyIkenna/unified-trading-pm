# 02: Background Agents Setup

**Status**: ⬜ Not Started  
**Priority**: P0 (Critical for parallel work)  
**Estimated Time**: 1-2 hours (debugging required)  
**Expected Benefit**: 3-4x faster multi-repo operations

---

## 📖 Overview

Background agents (cloud VM agents) enable parallel execution of tasks but currently don't work in your 30+ repo workspace. This document diagnoses the issue and provides solutions.

### Current State
- 30+ repo workspace in Cursor
- Background agents fail to start or hang
- Must use sequential execution (slow)

### Target State
- Background agents work reliably
- Can launch 4 parallel agents for cross-repo work
- 3-4x faster for multi-repo operations

### Known Issue
Per workspace rules: "Cursor background agents (cloud VM) have issues with 30+ repo workspaces."

---

## 🔗 Dependencies

**None** - Independent of other optimizations.

---

## 🚧 Blockers

- [ ] Root cause of background agent failure unknown
- [ ] May require workspace configuration changes
- [ ] May require Cursor version update

---

## 🔍 Diagnosis Steps

### Step 1: Verify Current Behavior

1. Open Cursor in your main workspace
2. Try to launch a background agent:
   ```
   Launch a background agent to read all .cursorrules files in the workspace
   ```
3. Observe behavior:
   - Does it start?
   - Does it hang?
   - Does it error?
   - What's the error message?

### Step 2: Check Cursor Version

```bash
# Get Cursor version
/Applications/Cursor.app/Contents/MacOS/Cursor --version

# Check if update available
# Cursor → Check for Updates
```

**Required**: Cursor version ≥ 0.40 (background agents introduced in 0.40)

### Step 3: Check Workspace Size

```bash
cd /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos

# Count repos
ls -d */ | wc -l

# Check total size
du -sh .

# Check .cursorignore
cat .cursorignore | head -20
```

**Known limits**:
- 30+ repos may exceed background agent capacity
- Large repos (>1GB each) can cause issues
- Missing .cursorignore can include too many files

### Step 4: Test with Smaller Workspace

Use workspace groups (already configured in ~/.zshrc):

```bash
# Test with smaller workspace (7-12 repos)
cursor-data  # Opens data pipeline workspace (9 repos)

# In Cursor, try background agent again
# If it works → workspace size is the issue
```

---

## 🛠️ Solution Options

### Option 1: Use Workspace Groups (Recommended)

**Per workspace rules**: Use themed workspaces (7-12 repos each) instead of 30+ repo workspace.

**Implementation**:

1. Identify which epic you're working on
2. Use corresponding workspace shortcut:

```bash
# Data pipeline work
cursor-data

# Features engineering work
cursor-features

# ML training/inference work
cursor-ml

# Trading/execution work
cursor-trading

# Library refactoring work
cursor-libs

# UI work
cursor-uis

# Cross-pipeline work
cursor-pipeline

# Infrastructure/quality gates work
cursor-infra
```

3. Each workspace includes:
   - Foundation repos (codex, deployment-v2, deployment-v3, cloud-services, events, config)
   - Relevant service repos for that epic
   - 7-12 repos total (under background agent limit)

**Pros**:
- ✅ Background agents work reliably
- ✅ Faster Cursor startup
- ✅ Cleaner workspace organization
- ✅ Foundation repos always available

**Cons**:
- ⚠️ Must switch workspaces for different epics
- ⚠️ Can't see all 30+ repos at once

### Option 2: Optimize Main Workspace

If you must use 30+ repo workspace:

**Step 1: Improve .cursorignore**

```bash
cd /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos

# Add to .cursorignore
cat >> .cursorignore << 'EOF'

# Reduce workspace size for background agents
**/node_modules/
**/.venv*/
**/venv/
**/__pycache__/
**/.pytest_cache/
**/.ruff_cache/
**/dist/
**/build/
**/*.egg-info/
**/uv.lock
**/.DS_Store

# Exclude large data files
**/*.parquet
**/*.csv
**/*.json.gz
**/*.tar.gz

# Exclude logs
**/*.log
**/logs/

EOF
```

**Step 2: Reduce Repo Count**

Archive repos you're not actively working on:

```bash
# Move inactive repos to archive folder
mkdir -p ~/Documents/repos/archived-repos

# Example: Archive old UI repos
mv backtest-ui ~/Documents/repos/archived-repos/
mv batch-audit-ui ~/Documents/repos/archived-repos/
```

**Step 3: Request Cursor Support**

If still not working:

1. Go to Cursor → Help → Report Issue
2. Describe: "Background agents don't work in 30+ repo workspace"
3. Include:
   - Cursor version
   - Number of repos
   - Total workspace size
   - Error messages

### Option 3: Use Local Parallel Agents

If background agents never work, use local parallel execution:

**Pattern**: Launch multiple Task tools in same message (local execution)

```
Launch 4 local agents in parallel:

Agent 1: Check instruments-service for pattern X
Agent 2: Check market-tick-data-handler for pattern X
Agent 3: Check market-data-processing-service for pattern X
Agent 4: Check unified-cloud-services for pattern X
```

**Pros**:
- ✅ Works regardless of workspace size
- ✅ No cloud VM dependency

**Cons**:
- ⚠️ Uses your local machine resources
- ⚠️ Slower than cloud VM agents

---

## ✅ Verification

### Test 1: Background Agent Launches

```
Test prompt:

Launch a background agent (run_in_background: true) to:
1. Count total .py files in workspace
2. Report back when done
```

**Expected**: Agent launches, runs in background, reports result.

### Test 2: Parallel Background Agents

```
Test prompt:

Launch 2 background agents in parallel:
- Agent 1: Count .py files in instruments-service
- Agent 2: Count .py files in market-tick-data-handler
```

**Expected**: Both agents run concurrently, both report results.

### Test 3: Resume Background Agent

```
Test prompt:

Resume background agent [agent-id] with feedback:
"Now count .md files instead"
```

**Expected**: Agent resumes with same context, executes new task.

---

## 📊 Success Metrics

- [ ] Background agents launch successfully
- [ ] Can run 2-4 agents in parallel
- [ ] Agents complete tasks without hanging
- [ ] Resume pattern works (saves 40-60% tokens)
- [ ] Cross-repo operations 3-4x faster

---

## 🔄 Rollback Plan

If workspace groups don't work:

1. Continue using main 30+ repo workspace
2. Use local parallel agents (Option 3)
3. Accept slower execution vs background agents
4. Monitor Cursor updates for fixes

---

## 📚 Related Documentation

- Workspace rules: `.cursorrules` → "Background Agents Limitation"
- Workspace configs: `.cursor/workspace-configs/WORKSPACE-RECOMMENDATIONS.md`
- Parallel agents: `.cursor/rules/parallel-agent-execution.mdc`
- Sub-agent workflow: `.cursor/rules/sub-agent-workflow-standard.mdc`

---

## 🐛 Troubleshooting

### Issue: "Background agent failed to start"

**Possible causes**:
1. Workspace too large (30+ repos)
2. Cursor version too old
3. Network issues (cloud VM can't connect)

**Solutions**:
1. Use workspace groups (cursor-data, cursor-features, etc.)
2. Update Cursor to latest version
3. Check internet connection

### Issue: "Background agent hangs indefinitely"

**Possible causes**:
1. Agent trying to read too many files
2. Workspace indexing incomplete
3. Memory limits exceeded

**Solutions**:
1. Add more patterns to .cursorignore
2. Wait for workspace indexing to complete (check status bar)
3. Use smaller workspace groups

### Issue: "Can't resume background agent"

**Possible causes**:
1. Agent ID expired (cloud VM shut down)
2. Agent completed and exited
3. Network disconnection

**Solutions**:
1. Launch fresh agent (can't resume after VM shutdown)
2. Check agent status before resuming
3. Reconnect to internet

---

## 💡 Tips

1. **Start with workspace groups**: Easiest solution, already configured
2. **Test in cursor-data first**: Smallest workspace (9 repos)
3. **Track agent IDs**: Save for resume pattern (40-60% token savings)
4. **Monitor Cursor updates**: Background agents improving in each release
5. **Use .cursorignore aggressively**: Exclude everything not needed for code work

---

## ✏️ Notes

**Current hypothesis**: 30+ repo workspace exceeds background agent capacity.

**Recommended approach**: Use workspace groups for epic-specific work.

**Fallback**: Local parallel agents if background agents never work.

**Expected outcome**: Once working, 3-4x faster for cross-repo operations.

---

## 🧪 Experiment Log

Document your findings here:

### Attempt 1: [Date]
- **Action**: 
- **Result**: 
- **Next step**: 

### Attempt 2: [Date]
- **Action**: 
- **Result**: 
- **Next step**: 

### Attempt 3: [Date]
- **Action**: 
- **Result**: 
- **Next step**: 
