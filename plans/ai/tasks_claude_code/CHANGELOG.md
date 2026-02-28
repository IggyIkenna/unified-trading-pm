# Changelog

## 2025-02-24 (v10.1): Prevent Zombie basedpyright Processes

### Fix: Add Timeouts to Prevent Hanging

**Problem**: basedpyright processes became zombies, consuming 100% CPU when:
- Orchestrator scripts ran basedpyright to count errors
- Agents ran basedpyright frequently during work
- Processes didn't complete and became orphaned when parent exited

**Solution**: 
1. Added `run_with_timeout()` helper function (Perl-based, macOS compatible)
2. Wrap all basedpyright calls with 30-second timeout
3. Updated agent prompts to run basedpyright only 2-3 times (not every 5 files)

**Files Updated**:
- `orchestrator-test.sh` - Added timeout helper, wrapped basedpyright calls
- `orchestrator-simple.sh` - Added timeout helper, wrapped basedpyright calls
- `run-agent.sh` - Updated prompt to limit basedpyright frequency
- `run-parallel-agents.sh` - Updated prompt to limit basedpyright frequency
- `CLAUDE_CODE_TASK.md` - Added timeout helper for Claude Code, updated all prompts, added kill-zombies.sh step
- `kill-zombies.sh` - New cleanup utility (created)

**Benefits**:
- ✅ No more zombie processes consuming CPU
- ✅ Faster execution (fewer basedpyright runs)
- ✅ Graceful handling of slow type checks
- ✅ Clear timeout warnings when basedpyright hangs
- ✅ Works for both Claude Code orchestration AND direct script execution

**Protection Layers**:
1. **Orchestrator scripts**: Timeout wrapper for all basedpyright calls (30s limit)
2. **Agent prompts**: Reduced frequency (2-3 times total, not every 5 files)
3. **Claude Code task**: Timeout helper function + updated prompts + kill-zombies.sh at start
4. **Cleanup utility**: `kill-zombies.sh` to manually clean up if needed

---

## 2025-02-24 (v10): Parallel Execution with Full Workspace Context

### Major Update: 4x Faster with Full Context

**Problem**: 
- Sequential execution: 60 minutes for 24 repos
- Single-repo workspace: Can't see codex standards or path dependencies

**Solution**: Parallel execution with workspace root
```bash
# New: 4 repos in parallel, full workspace context
bash run-parallel-agents.sh repo1 repo2 repo3 repo4 "prompt"

# Each agent:
--workspace /path/to/workspace-root  # Full context!
"ONLY edit files in repo1/ directory"  # Edit restriction in prompt
```

**Benefits**:
1. ✅ **4x faster**: 15-20 min (vs 60 min sequential)
2. ✅ **Full context**: Agents see codex, dependencies, workspace rules
3. ✅ **No conflicts**: Each agent edits only its target repo
4. ✅ **Better fixes**: Access to canonical patterns from codex
5. ✅ **Path dependencies**: Agents see unified-trading-services/, etc.

**Files**:
- Updated: `run-agent.sh` - Now uses workspace root + target repo parameter
- Created: `run-parallel-agents.sh` - Launches up to 4 agents in parallel
- Updated: `orchestrator-test.sh` - Workspace root + enhanced prompts + `--force` flag
- Updated: `orchestrator-simple.sh` - Workspace root + enhanced prompts + `--force` flag (all 4 agent variants)
- Updated: `CLAUDE_CODE_TASK.md` - Complete parallel execution workflow
- Updated: `CLAUDE_CODE_CONFIG.md` - Explains workspace context benefits

**Usage**:
```bash
# Single repo (full context)
bash run-agent.sh unified-config-interface "Fix errors"

# Parallel (4 repos, full context each)
bash run-parallel-agents.sh repo1 repo2 repo3 repo4 "Fix errors"

# Or use orchestrator scripts (now with workspace root + --force)
bash orchestrator-test.sh  # Test with 2 repos
bash orchestrator-simple.sh  # All 24 repos (10 parallel)
```

**Time Savings**: 40-45 minutes (67% faster!)

---

## 2025-02-24 (v9): Simplified Config (dangerouslySkipPermissions)

### Updated to Use Config File (Simplest Approach)

**Config file** (`~/.claude/config.json`):
```json
{
  "dangerouslySkipPermissions": true
}
```

**Benefits**:
- ✅ Applies to ALL sessions (persistent)
- ✅ No need for command-line flags
- ✅ Just launch: `claude --model claude-sonnet-4-5-20250929`
- ✅ No prompts ever!

**Files updated**:
- `~/.claude/config.json` - Simplified to single setting
- `CLAUDE_CODE_CONFIG.md` - Updated to recommend config file
- `CLAUDE_CODE_TASK.md` - Removed flag from launch command

**Result**: Simplest possible workflow - just launch and paste! 🚀

---

## 2025-02-24 (v8): Fixed Launch Command (Correct Flags)

### Corrected Claude Code Launch Command

**Problem**: Documentation incorrectly showed `--yolo` flag (which doesn't exist in Claude Code CLI).

**Correct flags**:
```bash
# Option 1: Skip all permissions (fastest)
claude --model claude-sonnet-4-5-20250929 --dangerously-skip-permissions

# Option 2: Bypass permissions mode (safer alternative)
claude --model claude-sonnet-4-5-20250929 --permission-mode bypassPermissions
```

**From Claude Code help**:
- `--dangerously-skip-permissions`: Bypass all permission checks (recommended only for sandboxes)
- `--permission-mode bypassPermissions`: Permission mode to bypass checks

**Files updated**:
- `CLAUDE_CODE_CONFIG.md` - Corrected launch commands
- `CLAUDE_CODE_TASK.md` - Updated "Just Paste and Go" section

---

## 2025-02-24 (v7): Claude Code Config + Explicit Rules Reading

### Stop Constant Approval Prompts

**Created**: `~/.claude/config.json` with auto-approve settings:
```json
{
  "autoApprove": {
    "bash": true,
    "read": true,
    "write": true,
    "mcp": true
  },
  "trustWorkspaces": ["/Users/ikennaigboaka/Documents/repos/unified-trading-system-repos"]
}
```

**Result**: Claude Code no longer asks for approval on every command!

### Make Claude Code Follow Cursor Rules

**Problem**: Claude Code does NOT automatically read `.cursorrules`, `.cursor/rules/*.mdc`, or `unified-trading-codex/`.

**Solution**: Updated prompt to explicitly tell Claude Code to read rules first:
```
CRITICAL - READ THESE FIRST (Claude Code):
1. .cursorrules
2. .cursor/rules/no-empty-fallbacks.mdc
3. .cursor/rules/no-type-any-use-specific.mdc
4. unified-trading-codex/06-coding-standards/README.md
```

**Files**:
- Created: `CLAUDE_CODE_CONFIG.md` (configuration guide)
- Updated: `CLAUDE_CODE_TASK.md` (added "READ THESE FIRST" section)
- Created: `~/.claude/config.json` (auto-approve config)

**Result**: Claude Code reads standards + no approval prompts!

---

## 2025-02-23 (v6): Added --force Flag for Shell Command Approval

### Fixed Shell Command Rejection

**Problem**: Agent was rejecting shell commands (like `basedpyright`) even with `--trust` flag. The agent's thinking showed "shell command was rejected".

**Root Cause**: `--trust` only trusts the workspace for file operations, but doesn't auto-approve shell commands.

**Solution**: Added `--force` flag to agent CLI command:
```bash
agent --api-key "$CURSOR_API_KEY" --print --model auto --trust --force ...
```

**What --force does**:
- Auto-approves shell commands (basedpyright, git, etc.)
- Allows agent to run verification commands
- No manual approval needed for each command

**Files updated**:
- `run-agent.sh` - Added `--force` flag
- `CLAUDE_CODE_TASK.md` - Updated Quick Reference with `--force`

**Result**: Agent can now run shell commands without rejection!

---

## 2025-02-23 (v5): Wrapper Script for Claude Code Shell Issues

### Created run-agent.sh Wrapper

**Problem**: Claude Code's shell has persistent issues with complex command chaining, even with temp file approach. Getting "unknown file attribute" errors with semicolons and long commands.

**Solution**: Created simple wrapper script that Claude Code can call:
```bash
bash /path/to/run-agent.sh "<workspace>" "<prompt>"
```

**Benefits**:
- ✅ No complex shell chaining (single bash command)
- ✅ All environment setup inside script
- ✅ Works around Claude Code's shell limitations
- ✅ Still uses pretty printing (simple-parser.py)
- ✅ Still FREE (agent uses model: auto)

**Files**:
- Created: `run-agent.sh` (wrapper script)
- Updated: `CLAUDE_CODE_TASK.md` (STEP 3-10 use wrapper)

---

## 2025-02-23 (v4): GCloud Command Fix for Claude Code

### Fixed API Key Retrieval

**Problem**: `gcloud secrets` command was failing in Claude Code's shell with "unknown file attribute" error.

**Solution**: Save to temp file first, then read:
```bash
# Before (fails in Claude Code)
export CURSOR_API_KEY=$(gcloud secrets versions access latest --secret=cursor-api-key --project=central-element-323112)

# After (works in Claude Code)
gcloud secrets versions access latest --secret=cursor-api-key --project=central-element-323112 > /tmp/cursor_key.txt
export CURSOR_API_KEY=$(cat /tmp/cursor_key.txt)
# Clean up when done
rm /tmp/cursor_key.txt
```

**Why**: Claude Code's shell environment has issues with command substitution for `gcloud`. Temp file approach is more reliable.

**Files updated**: CLAUDE_CODE_TASK.md (Quick Reference + STEP 3 + STEP 4)

---

## 2025-02-23 (v3): Model Name Correction

### Fixed Model Reference

**Changed**: "Sonnet 4.5" → "claude-sonnet-4-5-20250929" (full model name with date)

**Why**: More precise, matches actual model identifier

**Files updated**: All .md files in tasks_claude_code/

### Note on Terminal Output Issue

The terminal output (lines 73-107) showing raw JSON and "commands being rejected" was from an **old run before these changes**. That run had:
- Truncated commands (no env vars)
- No pipe to simple-parser.py
- Hook/permission issues

**That's exactly why we made v1 and v2 changes!** The updated task should work correctly now.

---

## 2025-02-23 (v2): Complete Task Structure Alignment

### Added Missing Structure

Aligned `CLAUDE_CODE_TASK.md` with `.cursor/plans/tasks/TEMPLATE.md` structure:

**Now includes**:
1. ✅ **Backup branches** - Create before changes, push to remote
2. ✅ **Context files** - Agent reads cursor rules automatically
3. ✅ **Resume pattern** - Save session IDs, resume with targeted guidance (50%+ token savings)
4. ✅ **Verification steps** - basedpyright + quality gates
5. ✅ **Success criteria** - Checklist per repo
6. ✅ **Token tracking** - Per repo and total
7. ✅ **Safeguards** - What to never do, what must do
8. ✅ **Progress tracking** - Repo X/24, errors fixed, time
9. ✅ **Commit workflow** - quickmerge after success
10. ✅ **Final summary** - Overall metrics after all repos

**Structure now matches**:
- Orchestration role (Claude Code)
- Execution role (agent CLI)
- Context (what agent reads)
- Safeguards (enforced patterns)
- Step-by-step workflow
- Resume pattern with benefits
- Success criteria checklist
- Token tracking at multiple levels

### Why This Matters

**Before**: Simple command execution, no structure  
**After**: Complete task framework matching proven `.cursor/plans/tasks/` pattern

**Benefits**:
- Backup branches prevent data loss
- Resume pattern saves 50%+ tokens on iterations
- Success criteria ensure completeness
- Token tracking shows actual costs
- Safeguards prevent anti-patterns

---

## 2025-02-23 (v1): Environment Variable Pattern

### Problem
Claude Code was truncating long `agent` CLI commands, causing the pipe to `simple-parser.py` to be dropped. This resulted in raw JSON output instead of pretty-printed output.

### Solution
Break long commands into environment variables:

```bash
# Before (truncated by Claude Code)
agent --api-key "$CURSOR_API_KEY" --print --model auto --trust --output-format stream-json --stream-partial-output --workspace /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/unified-config-interface "Fix..." 2>&1 | python3 /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/.cursor/plans/tasks_claude_code/simple-parser.py

# After (clean, no truncation)
export WORKSPACE=/Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/unified-config-interface
export PARSER=/Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/.cursor/plans/tasks_claude_code/simple-parser.py

agent --api-key "$CURSOR_API_KEY" --print --model auto --trust --output-format stream-json --stream-partial-output --workspace "$WORKSPACE" "Fix..." 2>&1 | python3 "$PARSER"
```

### Files Updated

**Main Documentation**:
- ✅ `CLAUDE_CODE_TASK.md` - Added Quick Reference section, updated all steps
- ✅ `README.md` - Updated file references
- ✅ `START.md` - Already correct

**Reference Documentation**:
- ✅ `reference/CLAUDE_CODE_ORCHESTRATION.md` - Updated all command examples
- ✅ `reference/COMPLETE_GUIDE.md` - Added environment variable explanation
- ✅ `reference/REPO_NAMING_GUIDE.md` - No changes needed

**Scripts**:
- ✅ `orchestrator-test.sh` - Already uses environment variables
- ✅ `orchestrator-simple.sh` - Already uses environment variables
- ✅ `simple-parser.py` - No changes needed

### Benefits

1. **No truncation** - Claude Code can execute full commands
2. **Readable** - Shorter, cleaner command syntax
3. **Maintainable** - Easy to modify paths
4. **Standard** - Consistent pattern across all tasks

### Usage

**For Claude Code CLI**:
```bash
claude --model sonnet

# Paste the updated prompt from CLAUDE_CODE_TASK.md
# It now includes environment variable setup in STEP 3
```

**For Bash Scripts**:
```bash
# Scripts already use this pattern
./orchestrator-test.sh
./orchestrator-simple.sh
```

---

## Previous Updates

### 2025-02-22: Pretty Printing
- Added `simple-parser.py` for clean output
- Added `--output-format stream-json --stream-partial-output` flags
- Consolidated 24 docs into 6 essential files

### 2025-02-21: Agent CLI Discovery
- Discovered standalone `agent` CLI (vs `cursor agent`)
- Updated authentication to use `CURSOR_API_KEY`
- Added Secret Manager integration

### 2025-02-20: Initial Setup
- Created task structure
- Set up bash orchestrators
- Documented Claude Code orchestration pattern
