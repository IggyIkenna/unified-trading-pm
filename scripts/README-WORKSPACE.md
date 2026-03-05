# Workspace Management Scripts

These scripts help set up and maintain the unified trading system multi-repo workspace across different machines.

## Quick Start (New Machine Setup)

```bash
cd /path/to/workspace/unified-trading-pm
bash scripts/workspace/setup-workspace-root.sh
```

This one command:

- ✅ Sets `UNIFIED_TRADING_WORKSPACE_ROOT` in your shell config
- ✅ Updates all Cursor workspace configurations
- ✅ Verifies Python interpreter exists
- ✅ Works on both macOS and Linux

**Full documentation:** [../docs/workspace-setup.md](../docs/workspace-setup.md) ← SSOT

---

## Scripts

### `setup-workspace-root.sh`

**Purpose:** Configure workspace root path and update all IDE settings

**Usage:**

```bash
# Interactive (prompts for path)
bash scripts/workspace/setup-workspace-root.sh

# Direct path
bash scripts/workspace/setup-workspace-root.sh /Users/username/Documents/repos

# From anywhere (using env var)
bash ${UNIFIED_TRADING_WORKSPACE_ROOT}/unified-trading-pm/scripts/workspace/setup-workspace-root.sh
```

**What it does:**

1. Detects your shell (zsh/bash) and OS (macOS/Linux)
2. Adds/updates `UNIFIED_TRADING_WORKSPACE_ROOT` in `~/.zshrc` or `~/.bashrc`
3. Updates all 10 `.code-workspace` files in `.cursor/workspace-configs/`
4. Verifies Python interpreter and key repos exist
5. Provides next steps for shell reload and Cursor restart

**Cross-platform:**

- ✅ macOS (zsh + bash)
- ✅ Linux (bash)
- ✅ Handles different `sed` syntax automatically

---

### `cleanup-agent-chats.sh`

**Purpose:** Delete old Cursor agent chat transcripts to save disk space

**Usage:**

```bash
# Delete files older than 24 hours
bash scripts/cleanup-agent-chats.sh

# Dry run (see what would be deleted)
bash scripts/cleanup-agent-chats.sh --dry-run
```

**What it does:**

- Finds all `*.jsonl` files in `~/.cursor/projects` older than 24 hours
- Shows count and total size
- Deletes them (or shows dry-run preview)
- Reports space saved

**Expected results:**

- Typical cleanup: 20-50MB saved
- Cursor projects folder after cleanup: ~270MB

**Automate with cron:**

```bash
crontab -e
# Add this line (runs daily at 3 AM):
0 3 * * * /full/path/to/unified-trading-pm/scripts/cleanup-agent-chats.sh
```

---

### `line-count-by-language.sh`

**Purpose:** Count lines of code for the whole workspace by language (Python, TypeScript, bash, etc.), ignore venv/node_modules, and split **test** vs **non-test** files.

**Requires:** [cloc](https://github.com/AlDanial/cloc) — `brew install cloc`

**Usage:**

```bash
# From workspace root (or set UNIFIED_TRADING_WORKSPACE_ROOT):
bash unified-trading-pm/scripts/line-count-by-language.sh
```

**What it does:**

- **Full codebase** — breakdown by language (Python, TypeScript, JavaScript, bash, etc.), excluding `.venv`, `node_modules`, `build`, `dist`, `.git`, etc.
- **Test files only** — same breakdown for files matching: `test_*.py`, `*_test.py`, `tests/`, `__tests__/`, `*.test.ts`, `*.spec.ts`, `test_*.sh`, `*_test.sh`
- **Non-test (source) only** — same breakdown for everything that is not a test file

**Excluded dirs:** `.venv`, `.venv-workspace`, `node_modules`, `build`, `dist`, `__pycache__`, `.git`, `.ruff_cache`, `.mypy_cache`, `htmlcov`

---

### `migrate-cursor-index.sh`

**Purpose:** Copy Cursor codebase index from old path to new path - skip 30+ minutes of re-indexing!

**Usage:**

```bash
# Close Cursor first, then run:
bash scripts/migrate-cursor-index.sh
```

**What it does:**

- Checks Cursor is closed (prevents corruption)
- Finds your old workspace index (e.g., 262MB)
- Copies to new workspace index location
- Preserves: agent-tools, terminals, assets, transcripts
- Saves 30-45 minutes of re-indexing

**When to use:**

- After iCloud moves your files (Documents → Documents - Mac)
- When switching between machines with different paths
- Any time workspace root path changes

**See:** `INDEX_MIGRATION.md` for full details

**What it does:**

- Finds all `*.jsonl` files in `~/.cursor/projects` older than 24 hours
- Shows count and total size
- Deletes them (or shows dry-run preview)
- Reports space saved

**Expected results:**

- Typical cleanup: 20-50MB saved
- Cursor projects folder after cleanup: ~270MB

**Automate with cron:**

```bash
crontab -e
# Add this line (runs daily at 3 AM):
0 3 * * * /full/path/to/unified-trading-pm/scripts/cleanup-agent-chats.sh
```

---

## Common Workflows

### Switching to a Different Machine

**Before:** Copy workspace to new machine

```bash
# On new machine:
cd /path/to/workspace/unified-trading-pm
bash scripts/workspace/setup-workspace-root.sh
# Enter the workspace path for THIS machine when prompted
source ~/.zshrc
# Restart Cursor
```

### After iCloud Sync Path Change

macOS iCloud moved your files from `/Users/.../Documents/repos` to `/Users/.../Documents/Documents - Mac/repos`?

```bash
cd ${UNIFIED_TRADING_WORKSPACE_ROOT}/unified-trading-pm
bash scripts/workspace/setup-workspace-root.sh
# Update the path when prompted
source ~/.zshrc
# Restart Cursor
```

### Team Member Onboarding

**New colleague setup:**

1. Clone the workspace repos
2. Run: `bash scripts/workspace/setup-workspace-root.sh`
3. Enter their machine's workspace path
4. Restart Cursor

Done! No manual path editing needed.

---

## Related Scripts (Other Purposes)

These scripts are in the same directory but serve different purposes:

| Script                                      | Purpose                                                 | Category         |
| ------------------------------------------- | ------------------------------------------------------- | ---------------- |
| `setup-cursor-rules-symlink.sh`             | Symlink .cursor/rules/ to cursor-rules/                 | Setup (one-time) |
| `setup-cursor-plans-symlink.sh`             | Symlink .cursor/plans/ to plans/cursor-plans/           | Setup (one-time) |
| `check-import-patterns.py`                  | Validate import patterns                                | Code quality     |
| `check-circular-imports.py`                 | Detect circular dependencies                            | Code quality     |
| `coding-standards-align-agent.sh`           | AI agent for coding standards                           | AI workflows     |
| `repo-management/verify-gh-pat-secrets.sh`  | Verify GH_PAT in all workspace repos                    | Auth/CI          |
| `repo-management/force-push-all-to-main.sh` | Force-push local main to origin (branch protection off) | Repo ops         |
| `repo-management/audit-reflog-resets.sh`   | Audit all repos for reset/reset --hard in reflog        | Safety / review  |

**Schedule (macOS):** `bash unified-trading-pm/scripts/repo-management/launchd/install-audit-reflog.sh` then `launchctl load ~/Library/LaunchAgents/com.unified-trading.audit-reflog.plist`. Runs every 10 min. Uses `run-audit-reflog-with-alert.sh` (macOS notification on failure). **Cancel:** `launchctl unload ~/Library/LaunchAgents/com.unified-trading.audit-reflog.plist`. **Full doc:** `docs/audit-reflog-scheduled-job.md`

---


## Troubleshooting

### "unified-trading-system-repos not found"

You're not in the right directory. Navigate to:

```bash
cd /path/to/workspace/unified-trading-system-repos/unified-trading-pm
bash scripts/workspace/setup-workspace-root.sh
```

### Variable not set after running script

Did you reload your shell?

```bash
source ~/.zshrc   # macOS zsh
source ~/.bashrc  # Linux bash
```

Verify:

```bash
echo $UNIFIED_TRADING_WORKSPACE_ROOT
```

### "Invalid Python interpreter" still showing

1. Verify Python exists:

   ```bash
   ls -la ${UNIFIED_TRADING_WORKSPACE_ROOT}/unified-trading-system-repos/.venv-workspace/bin/python
   ```

2. Close Cursor completely (Cmd+Q / Ctrl+Q)

3. Reopen Cursor

4. Open workspace explicitly: File > Open Workspace from File

### Script fails on Linux with sed error

The script auto-detects Linux and uses GNU sed syntax. If it still fails:

- Ensure `sed` is installed: `which sed`
- Try manually updating the workspace configs (see WORKSPACE_SETUP.md)

---

## For Maintainers

### Adding a new workspace config

1. Create `.code-workspace` file in `.cursor/workspace-configs/`
2. Use placeholder path: `/PLACEHOLDER/unified-trading-system-repos/.venv-workspace/bin/python`
3. Run `setup-workspace-root.sh` to populate with actual path

### Testing the script

```bash
# Dry run the cleanup script
bash scripts/cleanup-agent-chats.sh --dry-run

# Test setup script in non-interactive mode
bash scripts/workspace/setup-workspace-root.sh /some/test/path
```

### Updating for new shells

To support fish/tcsh/other shells, update `detect_shell_config()` function in `setup-workspace-root.sh`.

---

## Documentation Links

- **SSOT:** [../WORKSPACE_SETUP.md](../WORKSPACE_SETUP.md) - Complete workspace setup guide
- **Codex:** `unified-trading-codex/05-infrastructure/workspace-setup.md`
- **Rule:** `.cursor/rules/workspace-root-variable.mdc`
- **Old location:** `.cursor/workspace-configs/WORKSPACE_PATH_SETUP.md` (deprecated, kept for reference)
