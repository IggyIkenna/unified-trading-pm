# Agent Automation: Two Approaches

**Fix pyright errors across 24 repos - 100% FREE with your subscriptions!**

---

## 🎯 Choose Your Approach

### Option 1: Claude Code with Parallel Agents (Recommended) ⭐

**Smart orchestration + 4x faster**:

```bash
# Launch Claude Code
claude --model claude-sonnet-4-5-20250929

# Paste the task prompt from CLAUDE_CODE_TASK.md
# It will launch 4 agents in parallel per batch
```

**Pros**:

- Smart orchestration (can adapt, resume, analyze)
- 4x faster (parallel execution)
- Full workspace context (codex, dependencies, rules)
- No conflicts (each agent edits only its repo)

**Time**: 15-20 minutes (6 batches × 3 min) **Cost**: $0 (FREE)

---

### Option 2: Bash Orchestrator (Fully Automated)

**Run the script, it does everything**:

```bash
# Test with 2 repos (5-10 min)
bash unified-trading-pm/plans/tasks/claude-code/orchestrator-test.sh

# Full run with 24 repos (30-60 min)
bash unified-trading-pm/plans/tasks/claude-code/orchestrator-simple.sh
```

**Pros**: Fully automated, no manual steps, 10 parallel agents, **now with full workspace context + enhanced prompts +
`--force` flag** **Cons**: Less smart (can't adapt or resume) **Cost**: $0 (FREE)

**Note**: As of v10, orchestrator scripts now use the same improvements as Claude Code approach:

- ✅ Full workspace context (`--workspace /path/to/workspace-root`)
- ✅ Enhanced prompts with edit restrictions
- ✅ `--force` flag for auto-approval
- ✅ Timeouts to prevent zombie basedpyright processes (v10.1)

---

## 💰 Cost Summary

| Component                                    | Cost                            |
| -------------------------------------------- | ------------------------------- |
| Claude Code CLI (claude-sonnet-4-5-20250929) | **$0** (FREE with Claude Pro)   |
| Agent CLI (model: auto)                      | **$0** (FREE with Cursor Ultra) |
| **Total**                                    | **$0** (100% FREE!)             |

**vs All-Cursor**: $80+ (infinite savings!)

---

## 🧟 Zombie Process Management

If you see high CPU usage from Node processes:

```bash
# Kill all zombie basedpyright and agent processes
bash unified-trading-pm/plans/tasks/claude-code/kill-zombies.sh
```

**Prevention**: As of v10.1, all scripts now include:

- 30-second timeouts for basedpyright calls (orchestrator scripts)
- Agent prompts limit basedpyright runs to 2-3 times total
- Claude Code task includes kill-zombies.sh at start + timeout helper

**See**: `ZOMBIE_PREVENTION.md` for complete details

---

## 📁 Files

**Main**:

- `README.md` (this file) - Overview
- `START.md` - Quick start guide
- `CLAUDE_CODE_TASK.md` - Claude Code approach ⭐ **v10: Parallel + full context (2025-02-24)**
- `CLAUDE_CODE_CONFIG.md` - Configuration guide
- `run-agent.sh` - Single repo wrapper (workspace root)
- `../../../scripts/agents/run-parallel-agents.sh` - Parallel wrapper (up to 4 agents) ⭐ **SSOT:
  unified-trading-pm/scripts/agents/**
- `orchestrator-test.sh` - Bash approach (test)
- `orchestrator-simple.sh` - Bash approach (full)
- `simple-parser.py` - Pretty output parser
- `CHANGELOG.md` - What changed and why ⭐ **v10**
- `STRUCTURE_COMPARISON.md` - Before vs After

**Reference**:

- `PARALLEL_EXECUTION_GUIDE.md` - Parallel execution explained ⭐ **NEW**
- `reference/COMPLETE_GUIDE.md` - Comprehensive documentation
- `reference/CLAUDE_CODE_ORCHESTRATION.md` - Pattern explanation
- `reference/REPO_NAMING_GUIDE.md` - Repo vs package naming

---

## 🚀 Quick Start

**Simplest** (bash):

```bash
bash unified-trading-pm/plans/tasks/claude-code/orchestrator-test.sh
```

**Smartest + Fastest** (Claude Code with parallel):

```bash
claude --model claude-sonnet-4-5-20250929
# Then paste CLAUDE_CODE_TASK.md (v10: 4 agents in parallel!)
```

**Both are FREE!** 🎉
