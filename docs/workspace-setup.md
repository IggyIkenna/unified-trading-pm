# Workspace Setup Guide

Single source of truth for setting up the unified trading system workspace.

---

## Prerequisites

You need these before starting:

- **git** with SSH key configured for github.com (`ssh -T git@github.com` should work)
- **bash 4+** or **zsh** (macOS ships zsh by default)
- **macOS** (Homebrew) or **Linux** (apt/yum)

The bootstrap script installs everything else (Python 3.13, uv, ripgrep, jq, basedpyright).

---

## New Machine Setup (end-to-end)

### Step 1: Clone this repo

Pick a workspace directory. All 63 repos will live side-by-side here.

```bash
# Pick ONE of these (or your own location):
#   Mac with iCloud:    ~/Documents/Documents - Mac/repos
#   Mac without iCloud: ~/Documents/repos
#   Linux:              ~/repos

mkdir -p /your/chosen/path/unified-trading-system-repos
cd /your/chosen/path/unified-trading-system-repos
git clone git@github.com:IggyIkenna/unified-trading-pm.git
```

### Step 2: Bootstrap the workspace

This single script does everything: installs system deps, clones all 63 repos from the manifest, creates the workspace venv, and runs per-repo setup in dependency order.

```bash
bash unified-trading-pm/scripts/workspace/workspace-bootstrap.sh
```

What it does (5 phases):

| Phase | What happens |
|-------|-------------|
| 1. System deps | Installs Python 3.13, uv, ripgrep, jq via Homebrew/apt |
| 2. Clone repos | Reads `workspace-manifest.json`, clones all 63 repos via SSH |
| 3. Workspace venv | Creates `.venv-workspace/` with ruff, basedpyright, pytest, and all repo deps |
| 4. Per-repo setup | Runs `scripts/setup.sh` in each repo (topological order: T0 first) |
| 5. Smoke test | Verifies `import <package>` works for every Python repo |

Safe to re-run. Skips repos already cloned and deps already installed.

### Step 3: Set up workspace paths and IDE configs

```bash
bash unified-trading-pm/scripts/workspace/setup-workspace-root.sh
```

This script auto-detects your workspace path and:
- Adds `export UNIFIED_TRADING_WORKSPACE_ROOT="/your/path"` to `~/.zshrc` or `~/.bashrc`
- Updates all Cursor `.code-workspace` files with your machine's path
- Creates Claude Code conversation symlinks (so old chats carry over between machines)
- Updates Claude Code permissions in `~/.claude/settings.json`

### Step 4: Set up Cursor rules and plans (symlinks)

```bash
# Symlink rules (edits go directly to git-tracked cursor-rules/)
bash unified-trading-pm/scripts/workspace/setup-cursor-rules-symlink.sh

# Symlink plans (edits go directly to git-tracked plans/cursor-plans/)
bash unified-trading-pm/scripts/workspace/setup-cursor-plans-symlink.sh
```

After this, your workspace looks like:

```
unified-trading-system-repos/           <- open this in Cursor
├── .cursor/
│   ├── rules/ -> unified-trading-pm/cursor-rules/          <- SYMLINK
│   └── plans/ -> unified-trading-pm/plans/cursor-plans/    <- SYMLINK
├── .claude/
│   └── CLAUDE.md                       <- Claude Code project instructions
├── .venv-workspace/                    <- shared venv (python, ruff, basedpyright, all deps)
├── unified-trading-pm/                 <- this repo
│   ├── cursor-rules/                   <- git-tracked rules (symlinked from .cursor/rules/)
│   ├── cursor-configs/                 <- git-tracked workspace configs
│   └── workspace-manifest.json         <- registry of all 63 repos
├── unified-trading-codex/
├── instruments-service/
└── ...60 more repos
```

### Step 5: Reload shell and restart IDEs

```bash
source ~/.zshrc   # or ~/.bashrc
```

Close and reopen **both Cursor and Claude Code** (Cmd+Q). This resolves "Invalid Python interpreter" errors in Cursor.

### Step 6: Verify

```bash
# Environment
echo $UNIFIED_TRADING_WORKSPACE_ROOT           # should print your path
which python                                    # .venv-workspace/bin/python
which ruff                                      # .venv-workspace/bin/ruff
which basedpyright                              # .venv-workspace/bin/basedpyright

# Cursor rules symlink works
ls -la .cursor/rules                            # should show -> .../unified-trading-pm/cursor-rules
ls .cursor/rules/*.mdc | wc -l                  # should be ~103

# Plans symlink works
ls -la .cursor/plans                            # should show -> .../unified-trading-pm/plans/cursor-plans

# Quality gates pass on PM repo
cd unified-trading-pm && bash scripts/quality-gates.sh
```

---

## How Rules and Plans Work

Both `.cursor/rules/` and `.cursor/plans/` are **symlinks** into the PM repo:

```
.cursor/rules/ -> unified-trading-pm/cursor-rules/          (symlink)
.cursor/plans/ -> unified-trading-pm/plans/cursor-plans/     (symlink)
```

This means:
- **Edits in `.cursor/rules/` directly modify git-tracked files** in unified-trading-pm
- **No sync scripts needed** — there's no copy to get out of sync
- **`git pull` in unified-trading-pm immediately gives you the team's latest** rules and plans
- **Conflict resolution is standard git** — if two developers edit the same rule, git merge handles it

### Multi-developer workflow

| Scenario | What happens |
|----------|-------------|
| You add a new rule, teammate adds a different rule | Both push via quickmerge. `git pull` gives you both. No conflict. |
| You both edit different lines of the same rule | Git auto-merges. No conflict. |
| You both edit the same lines of the same rule | Git merge conflict. Resolve locally, then re-push. |

---

## Day-to-Day Workflow

### Push your changes

```bash
cd unified-trading-pm
bash scripts/quickmerge.sh "feat: describe your change"
```

Quickmerge runs a 4-stage pipeline:
1. **Stage 1**: Dependency validation
2. **Stage 2**: Pre-flight audit
3. **Stage 3**: Quality gates (ruff + basedpyright + pytest)
4. **Stage 4**: Creates PR with auto-merge enabled

Rule edits are committed directly (no sync step) because `.cursor/rules/` is a symlink.

### Pull team's latest

```bash
cd unified-trading-pm && git pull
# Done — symlinks mean you immediately see the team's changes
```

### Work on any service repo

Each repo has the same quickmerge template:

```bash
cd instruments-service   # or any repo
bash scripts/quickmerge.sh "fix: describe your change"
```

---

## Switching Machines

When you move to a different laptop or the workspace path changes (e.g., iCloud sync):

```bash
# 1. Re-run setup (auto-detects new path)
cd /new/path/unified-trading-system-repos/unified-trading-pm
bash scripts/workspace/setup-workspace-root.sh

# 2. Re-create symlinks
bash scripts/workspace/setup-cursor-rules-symlink.sh
bash scripts/workspace/setup-cursor-plans-symlink.sh

# 3. Reload shell and restart both IDEs
source ~/.zshrc
```

The setup script detects old paths in workspace configs and replaces them with the new path.

---

## What Each Script Does

| Script | When to run | What it does |
|--------|-------------|-------------|
| `workspace-bootstrap.sh` | New machine (once) | Clones all repos, installs deps, creates venv |
| `setup-workspace-root.sh` | New machine or path change | Sets env var, updates IDE configs |
| `setup-cursor-rules-symlink.sh` | New machine (once) | Symlinks `.cursor/rules/` to `cursor-rules/` |
| `setup-cursor-plans-symlink.sh` | New machine (once) | Symlinks `.cursor/plans/` to `plans/cursor-plans/` |
| `quickmerge.sh` | To push changes | Full pipeline: lint + test + PR |

---

## Troubleshooting

### "Invalid Python interpreter" in Cursor

1. Check: `ls .venv-workspace/bin/python` — does it exist?
2. If not: `bash unified-trading-pm/scripts/workspace/workspace-bootstrap.sh --skip-system`
3. If yes: Close Cursor completely (Cmd+Q) and reopen

### quality-gates.sh fails with "uv pip install failed"

PM uses the workspace venv, not a local `.venv`. Make sure `.venv-workspace/` exists:

```bash
cd $UNIFIED_TRADING_WORKSPACE_ROOT/unified-trading-system-repos
ls .venv-workspace/bin/python
```

If missing, re-run the bootstrap script.

### .cursor/rules/ is a directory instead of a symlink

If you had the old copy-based setup, migrate to symlinks:

```bash
bash unified-trading-pm/scripts/workspace/setup-cursor-rules-symlink.sh
```

This script migrates any local-only rules into cursor-rules/ before creating the symlink.

### Script can't find workspace root

Make sure the env var is set:

```bash
echo $UNIFIED_TRADING_WORKSPACE_ROOT
```

If empty, re-run:

```bash
bash unified-trading-pm/scripts/workspace/setup-workspace-root.sh
source ~/.zshrc
```

---

## Workspace dependency pinning

Canonical external dependency versions and propagation: see **unified-trading-codex** `06-coding-standards/dependency-management.md` (§ Workspace-wide dependency pinning) and `unified-trading-pm/workspace-constraints.toml`. Scripts: `resolve-canonical-versions.py`, `propagate-canonical-versions.py`, `aggregate-workspace-deps.py`.

### Canonical deps flow

Prerequisite: ensure `uv` is installed (`pip install uv` once; workspace-bootstrap.sh does this if missing). Then run from **workspace root** (with `.venv-workspace` activated or Python 3.13 + uv on PATH):

```bash
# 1) Generate canonical constraints (tightest range per external package)
python unified-trading-pm/scripts/workspace/resolve-canonical-versions.py

# 2) Apply to all repos and run uv lock per repo
python unified-trading-pm/scripts/propagation/propagate-canonical-versions.py --apply
# Optional: add --commit to git add/commit pyproject.toml + uv.lock per repo

# 3) Install workspace venv and freeze exact versions to requirements.lock
python unified-trading-pm/scripts/workspace/aggregate-workspace-deps.py --resolve
```

Without `--resolve`, aggregate-workspace-deps uses the existing `.venv-workspace/requirements.lock` for a fast re-install.
