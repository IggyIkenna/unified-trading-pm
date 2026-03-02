# Workspace Setup Guide (SSOT)

This is the **single source of truth** for setting up the unified trading system multi-repo workspace on a new machine or after path changes (like iCloud sync).

## Overview

The workspace consists of 52 independent repositories organized under a single parent directory:

```
<WORKSPACE_ROOT>/
├── unified-trading-system-repos/    ← Main multi-repo folder
│   ├── unified-trading-pm/          ← This repo (project management & scripts)
│   ├── unified-trading-services/    ← Core services library
│   ├── unified-config-interface/    ← Config schemas
│   ├── instruments-service/         ← Services...
│   ├── market-data-service/
│   └── ...50 more repos
```

## Quick Setup (New Machine or Colleague)

### 1. Clone the workspace

```bash
# Choose your workspace location based on machine/OS:
# - Mac with iCloud: ~/Documents/Documents - Mac/repos
# - Mac without iCloud: ~/Documents/repos
# - Linux: ~/repos
# - Other laptop: ~/Documents/Documents - MacOld/repos

cd /path/to/your/chosen/workspace
git clone <workspace-url> unified-trading-system-repos
cd unified-trading-system-repos/unified-trading-pm
```

### 2. Run the workspace setup script

```bash
bash scripts/workspace/setup-workspace-root.sh
```

**That's it!** The script will:
- ✅ Prompt for your workspace root path (or auto-detect)
- ✅ Add `UNIFIED_TRADING_WORKSPACE_ROOT` to your shell config (~/.zshrc or ~/.bashrc)
- ✅ Update all 10 Cursor workspace configurations with your path
- ✅ Update Claude Code conversation symlinks and permissions
- ✅ Verify Python interpreter and key repos exist

### 3. Reload shell and verify

```bash
source ~/.zshrc  # or ~/.bashrc on Linux
echo $UNIFIED_TRADING_WORKSPACE_ROOT
```

### 4. (Optional) Migrate Cursor Index

**Skip 30+ minutes of re-indexing!** Copy your existing index:

```bash
bash scripts/migrate-cursor-index.sh
```

See: [index-migration.md](index-migration.md) for details.

### 5. Restart IDEs

Close **both Cursor and Claude Code** completely (Cmd+Q or Ctrl+Q) and reopen. The "Invalid Python interpreter" errors (Cursor) and missing conversations (Claude Code) should be fixed.

---

## Why This System Exists

### Problem 1: iCloud Sync Path Changes
When macOS enables iCloud backup, it moves:
- `/Users/username/Documents/repos` → `/Users/username/Documents/Documents - Mac/repos`

All hardcoded paths break:
- **Cursor:** "Invalid Python interpreter" errors
- **Claude Code:** Missing conversation history (can't find old chats)

### Problem 2: Multiple Machines
Different developers/machines have different workspace locations:
- One laptop: `/Users/username/Documents/repos`
- Another laptop: `/Users/username/Documents/Documents - MacOld/repos`
- Linux server: `/home/username/repos`

Hardcoded paths don't transfer.

### Solution: Single Environment Variable + Automated Setup
`UNIFIED_TRADING_WORKSPACE_ROOT` is set once in your shell config. The setup script automatically:
- Updates all Cursor workspace configs
- Creates Claude Code conversation symlinks
- Updates Claude Code permissions

To switch machines, just update one variable and re-run the script.

---

## Manual Setup (If Script Fails)

### 1. Add to shell config manually

Edit `~/.zshrc` (Mac/zsh) or `~/.bashrc` (Linux/bash):

```bash
# macOS zsh
echo 'export UNIFIED_TRADING_WORKSPACE_ROOT="/Users/YOUR_USERNAME/Documents/Documents - Mac/repos"' >> ~/.zshrc
source ~/.zshrc

# Linux bash
echo 'export UNIFIED_TRADING_WORKSPACE_ROOT="/home/YOUR_USERNAME/repos"' >> ~/.bashrc
source ~/.bashrc
```

### 2. Update workspace configs manually

```bash
cd ${UNIFIED_TRADING_WORKSPACE_ROOT}/unified-trading-system-repos/.cursor/workspace-configs

# Replace old paths with new (adjust sed syntax for OS)
# macOS:
for file in *.code-workspace; do
    sed -i '' 's|/OLD/PATH|'"${UNIFIED_TRADING_WORKSPACE_ROOT}"'|g' "$file"
done

# Linux:
for file in *.code-workspace; do
    sed -i 's|/OLD/PATH|'"${UNIFIED_TRADING_WORKSPACE_ROOT}"'|g' "$file"
done
```

---

## Switching Between Machines

When you move to a different laptop:

### 1. Update the variable (one line edit)

Edit `~/.zshrc` or `~/.bashrc` and change:
```bash
export UNIFIED_TRADING_WORKSPACE_ROOT="/path/for/this/machine"
```

### 2. Re-run the setup script
```bash
source ~/.zshrc  # Reload
cd ${UNIFIED_TRADING_WORKSPACE_ROOT}/unified-trading-pm
bash scripts/workspace/setup-workspace-root.sh
```

### 3. Restart both IDEs

All workspace configs and Claude Code conversations will automatically use the new path.

---

## Workspace Configurations

10 themed workspace configurations exist in `.cursor/workspace-configs/`:

| Workspace | Description |
|-----------|-------------|
| `unified-trading-system-repos.code-workspace` | Default complete workspace |
| `workspace-complete.code-workspace` | All 52 repos |
| `workspace-data-pipeline.code-workspace` | Data ingestion repos |
| `workspace-features.code-workspace` | Feature engineering repos |
| `workspace-ml.code-workspace` | ML training/inference repos |
| `workspace-trading.code-workspace` | Trading/execution repos |
| `workspace-libraries.code-workspace` | Shared library repos |
| `workspace-infrastructure.code-workspace` | Infrastructure repos |
| `workspace-full-pipeline.code-workspace` | Complete pipeline view |
| `workspace-uis.code-workspace` | UI repos |

All automatically reference `UNIFIED_TRADING_WORKSPACE_ROOT`.

---

## Python Virtual Environment

The workspace uses a **single shared venv** for all repos: `.venv-workspace/`

### Initial setup (first time only):
```bash
cd ${UNIFIED_TRADING_WORKSPACE_ROOT}/unified-trading-system-repos
bash .cursor/workspace-configs/setup-workspace-venv-complete.sh
```

This installs:
- Python 3.13
- All development tools (ruff, basedpyright, pytest, uv)
- All local repos as editable installs

Cursor workspace configs point to:
```
${UNIFIED_TRADING_WORKSPACE_ROOT}/unified-trading-system-repos/.venv-workspace/bin/python
```

---

## Disk Space Management

### Agent Chat Cleanup

Cursor stores agent chat transcripts in `~/.cursor/projects`. Old chats (>24 hours) can be cleaned:

```bash
cd ${UNIFIED_TRADING_WORKSPACE_ROOT}/unified-trading-pm
bash scripts/cleanup-agent-chats.sh
```

**Expected sizes:**
- Cursor total: ~1GB
- Cursor projects: ~270MB (after cleanup)

### Automate Cleanup (Optional)

Add to crontab to run daily at 3 AM:
```bash
crontab -e
# Add this line:
0 3 * * * bash /full/path/to/unified-trading-pm/scripts/cleanup-agent-chats.sh
```

---

## Troubleshooting

### "Invalid Python interpreter" error after setup

**Cause:** Cursor hasn't reloaded the workspace configs yet.

**Fix:**
1. Verify variable is set: `echo $UNIFIED_TRADING_WORKSPACE_ROOT`
2. Verify Python exists: `ls -la ${UNIFIED_TRADING_WORKSPACE_ROOT}/unified-trading-system-repos/.venv-workspace/bin/python`
3. Close Cursor completely (Cmd+Q / Ctrl+Q)
4. Reopen Cursor
5. Open one of the workspace configs explicitly: File > Open Workspace from File

### "800GB System Settings storage" on Mac

This is **not from Cursor**. It's macOS purgeable space:
- iCloud optimized storage
- Time Machine local snapshots
- System caches

macOS will automatically free this when needed. Check actual usage:
```bash
df -h /
```

Cursor's actual footprint: ~1GB.

### Script says "unified-trading-system-repos not found"

You're not in the right directory. The script expects to be run from:
```
<workspace-root>/unified-trading-system-repos/unified-trading-pm/
```

Navigate there first:
```bash
cd /path/to/workspace/unified-trading-system-repos/unified-trading-pm
bash scripts/workspace/setup-workspace-root.sh /path/to/workspace
```

### Workspace configs not updating

The script looks for `*.code-workspace` files in:
```
${UNIFIED_TRADING_WORKSPACE_ROOT}/unified-trading-system-repos/.cursor/workspace-configs/
```

If they don't exist, clone the full workspace or copy from another machine.

### Different shell (fish, tcsh, etc.)

The script only supports bash and zsh. For other shells, manually:
1. Add `export UNIFIED_TRADING_WORKSPACE_ROOT="/your/path"` to your shell config
2. Manually update `.code-workspace` files with find/replace

---

## For Team Collaboration

### New team member setup:
1. Clone the workspace repos
2. Run `bash scripts/workspace/setup-workspace-root.sh`
3. Enter their machine's workspace path when prompted
4. Restart Cursor

**No manual path editing needed!**

### Sharing workspace configs:
The workspace configs are git-tracked in `unified-trading-pm`. When you pull updates, re-run:
```bash
bash scripts/workspace/setup-workspace-root.sh
```

This ensures your local path is maintained while adopting config structure changes.

---

## Related Scripts

| Script | Purpose |
|--------|---------|
| `scripts/workspace/setup-workspace-root.sh` | Main setup script (this guide) |
| `scripts/migration/cleanup-agent-chats.sh` | Clean old Cursor agent transcripts |
| `scripts/workspace/sync-rules-pull.sh` | Pull latest cursor rules from PM repo |
| `scripts/workspace/sync-workspace.sh` | Check rule sync status |

---

## Architecture Context

This workspace contains 52 repositories organized by tier:

- **Tier 0** (leaf libraries): No dependencies on other internal repos
- **Tier 1** (core services): Depends on Tier 0
- **Tier 2** (domain libraries): Depends on Tier 0 + Tier 1
- **Tier 3** (domain clients): Depends on Tier 0-2
- **Services**: Python services (import Tier 0-3 libs only, never other services)
- **APIs**: HTTP boundaries (import Tier 0-1 only)
- **UIs**: TypeScript frontends (never import Python)

See: `workspace-manifest.json` and `WORKSPACE_MANIFEST_DAG.svg` for full dependency graph.

---

## Summary

**One command to set up any machine:**
```bash
bash unified-trading-pm/scripts/workspace/setup-workspace-root.sh
```

**One variable to change when switching machines:**
```bash
export UNIFIED_TRADING_WORKSPACE_ROOT="/new/path"
```

**One command to update all configs:**
```bash
bash unified-trading-pm/scripts/workspace/setup-workspace-root.sh
```

For questions or issues, see the PM repo or update this doc (SSOT).
