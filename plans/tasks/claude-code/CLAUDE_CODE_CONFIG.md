# Claude Code Configuration

## 🚀 Quick Start (TL;DR)

**One-time setup** (already done):

```json
~/.claude/config.json:
{
  "dangerouslySkipPermissions": true
}
```

**Launch Claude Code**:

```bash
claude --model claude-sonnet-4-5-20250929
```

Then paste the prompt from `CLAUDE_CODE_TASK.md` (lines 57-200).

**Done!** No prompts, agent CLI reads cursor rules automatically. 🎉

---

## 🛑 Stop Constant Approval Prompts

### Option 1: Launch with --dangerously-skip-permissions (Fastest, No Config Needed)

```bash
claude --model claude-sonnet-4-5-20250929 --dangerously-skip-permissions
```

**What --dangerously-skip-permissions does**:

- Bypasses ALL permission checks (bash, read, write, MCP)
- No prompts, fully non-interactive
- Fastest way to run
- Recommended only for trusted workspaces

**Alternative** (safer):

```bash
claude --model claude-sonnet-4-5-20250929 --permission-mode bypassPermissions
```

**Use this for**: Quick runs, automation, when you trust the workspace

---

### Option 2: Config File (Persistent) ✅ **RECOMMENDED**

**Already created**: `~/.claude/config.json`

```json
{
  "dangerouslySkipPermissions": true
}
```

**What this does**:

- Applies to ALL Claude Code sessions (persistent)
- No need for `--dangerously-skip-permissions` flag
- Just launch: `claude --model claude-sonnet-4-5-20250929`
- No prompts ever!

**Result**: Claude Code will skip all permission checks globally!

---

## 📋 Making Claude Code Follow Cursor Rules

### ❌ The Problem

Claude Code does NOT automatically read:

- `.cursorrules`
- `.cursor/rules/*.mdc`
- `unified-trading-codex/`

**You must tell it explicitly in your prompt!**

### ✅ The Solution

The updated `CLAUDE_CODE_TASK.md` now includes:

```
CRITICAL - READ THESE FIRST (Claude Code):
Before starting, read these files to understand the standards:
1. /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/.cursorrules
2. /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/.cursor/rules/no-empty-fallbacks.mdc
3. /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/.cursor/rules/no-type-any-use-specific.mdc
4. /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/unified-trading-/codex/06-coding-standards/README.md
```

**This forces Claude Code to read your standards before orchestrating!**

---

## 🤖 Agent CLI Workspace Context

### Full Workspace Root (Recommended)

**New pattern** (v10+): Agent CLI uses workspace root:

```bash
--workspace /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos
```

**Benefits**:

- ✅ Reads workspace `.cursorrules` (workspace-level rules)
- ✅ Reads `.cursor/rules/*.mdc` (all standards)
- ✅ Reads `unified-trading-codex/` (canonical patterns)
- ✅ Sees path dependencies (`unified-trading-library/`, etc.)
- ✅ Full context for better fixes

**Edit Restriction**: Prompt tells agent to ONLY edit target repo:

```
"You can read everything, but ONLY edit files in unified-config-interface/ directory"
```

**Result**: Full context + no conflicts = perfect for parallel execution!

### Workspace-scoped context (less context, same rules)

**To give Claude/Cursor only the repos that matter for a given epic**, open a **themed workspace file** instead of the
full repo root:

```bash
cursor .cursor/workspace-configs/workspace-trading.code-workspace
# or workspace-data-pipeline, workspace-ml, workspace-libraries, etc.
```

**What this does**:

- Cursor’s **multi-root workspace** = only the folders listed in that `.code-workspace` file.
- File tree, search, and “files in workspace” are limited to those roots (e.g. trading repos + .cursor + codex +
  deployment-v3 + .github + .venv-workspace).
- **You do not need different “doc Claudes” per workspace.** The same `.cursorrules` and `.cursor/rules/*.mdc` apply;
  Cursor still loads them from the `.cursor` folder that is one of the roots.
- **Claude Code CLI**: When you run the agent with `--workspace <path>`, point it at the **same workspace file** (or the
  parent folder that contains only the themed roots). Then the agent’s view of “what files exist” is already scoped to
  that workspace.

**Summary**: Open the themed `.code-workspace` (e.g. `workspace-trading`) → Cursor/Claude see only those folders +
shared .cursor/codex/deployment. No extra config per workspace.

### Claude Code CLI

- ❌ Does NOT automatically read cursor rules
- ❌ Needs explicit file paths in prompt
- ✅ Can read files when told to
- ✅ Can then enforce standards when orchestrating
- ✅ Launches agent CLI which DOES read rules automatically

### The Full Flow (Parallel Execution)

```
1. Claude Code (orchestrator)
   └─ Reads rules explicitly (from prompt)
   └─ Understands standards

2. Claude Code launches: 4 agent CLI instances in parallel
   ├─ Agent 1 (repo A): workspace root, edit only repo A
   ├─ Agent 2 (repo B): workspace root, edit only repo B
   ├─ Agent 3 (repo C): workspace root, edit only repo C
   └─ Agent 4 (repo D): workspace root, edit only repo D

   Each agent:
   └─ Reads .cursorrules (workspace root)
   └─ Reads .cursor/rules/*.mdc (workspace root)
   └─ Reads unified-trading-codex/ (standards)
   └─ Sees path dependencies (unified-trading-library/, etc.)
   └─ Edits ONLY its target repo (no conflicts!)

Result: Full context + parallel execution + no conflicts!
```

### Why This Works

**Different repos = Zero conflict risk**:

- Agent 1 edits `unified-config-interface/` only
- Agent 2 edits `unified-trading-library/` only
- Agent 3 edits `instruments-service/` only
- Agent 4 edits `market-tick-data-handler/` only

**All agents see same context**:

- Same workspace root
- Same codex standards
- Same workspace rules
- Same path dependencies

**Result**: 4x faster with full context and zero conflicts!

---

## 🎯 Best Practice Workflow

1. **Configure Claude Code** (one-time):

   ```bash
   # Config file already created at ~/.claude/config.json
   # Restart Claude Code to pick up changes
   ```

2. **Launch Claude Code with explicit instructions**:

   ```bash
   claude --model claude-sonnet-4-5-20250929

   # Paste prompt from CLAUDE_CODE_TASK.md
   # It now includes "READ THESE FIRST" section
   ```

3. **Claude Code reads rules** → **Launches agent CLI** → **Agent also reads rules** → **Double enforcement!**

---

## 🔄 Restart Claude Code

If you have Claude Code running, restart it to pick up the new config:

```bash
# Exit current session (Ctrl+C or type /exit)
# Then restart:
claude --model claude-sonnet-4-5-20250929
```

---

## ✅ Summary

**To stop questions**:

- ✅ Config file created: `~/.claude/config.json`
- ✅ Restart Claude Code to apply

**To follow cursor rules**:

- ✅ Updated prompt includes "READ THESE FIRST"
- ✅ Claude Code will read rules before starting
- ✅ Agent CLI automatically reads rules from workspace

**Result**: No more constant prompts + Standards enforced! 🚀

---

## 🐍 Workspace Venv Auto-Activation

Claude Code needs the workspace venv so that `python`, `ruff`, `basedpyright`, `uv`, and `pytest` resolve to the correct
versions (`ruff==0.15.0`, `basedpyright`, Python 3.13) without manual setup.

### Three-layer approach (all three active):

**Layer 1 — Shell alias (strongest, inherited by all subprocesses)**

```bash
# In ~/.zshrc — already added
ccw                  # claude + venv, skip permissions, default model
ccw-sonnet           # claude-sonnet-4-6 + venv
ccw-opus             # claude-opus-4-6 + venv
ccw-think            # claude-sonnet-4-5 + venv + thinking budget 10k
```

Use `ccw` instead of `claude` when working from the unified-trading-system-repos workspace. The shell function `source`s
the venv before invoking `claude`, so every bash subprocess inherits the activated PATH automatically.

**Layer 2 — `.claude/settings.json` (env vars, automatic for any claude invocation)**

Located at `unified-trading-system-repos/.claude/settings.json`:

```json
{
  "env": {
    "VIRTUAL_ENV": ".../.venv-workspace",
    "PATH": ".../.venv-workspace/bin:..."
  }
}
```

This is picked up by `claude` regardless of how it was launched (CLI, IDE, scripts). It ensures `VIRTUAL_ENV` is set and
`.venv-workspace/bin` is first in PATH.

**Layer 3 — `CLAUDE.md` (session instruction, fallback check)**

`CLAUDE.md` at workspace root tells Claude Code to verify `which python` and `which ruff` at the start of every session,
and to run `source .venv-workspace/bin/activate` if they aren't resolving to the workspace venv.

### Verification

```bash
# In any Claude Code bash call — should all point to .venv-workspace/bin/
which python         # .venv-workspace/bin/python
python --version     # Python 3.13.x
which ruff           # .venv-workspace/bin/ruff
ruff --version       # ruff 0.15.0
which basedpyright   # .venv-workspace/bin/basedpyright
```
