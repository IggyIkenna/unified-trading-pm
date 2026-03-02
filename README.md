# unified-trading-pm

Project management, workspace tooling, and shared Cursor configuration for the Unified Trading System.

---

## 🚀 Quick Start (New Machine Setup)

Setting up the workspace on a new machine or after path changes (like iCloud sync)?

```bash
cd /path/to/workspace/unified-trading-pm
bash scripts/setup-workspace-root.sh
```

**One command sets up BOTH IDEs:** Cursor + Claude Code workspace configs, conversation history, Python paths.
📖 **Full docs:** [WORKSPACE_SETUP.md](WORKSPACE_SETUP.md) | [BOTH_IDES_SETUP.md](BOTH_IDES_SETUP.md)

---

## Required Workspace Structure

This repo **must** be cloned as a sibling directory alongside all other system repos.
Scripts infer the workspace root as the **parent directory** of `unified-trading-pm/`.

```
~/repos/unified-trading-system-repos/     ← workspace root (open THIS in Cursor)
├── .cursor/
│   └── rules/                            ← your local Cursor rules (IDE reads here)
├── .cursorrules                          ← workspace-level Cursor config
│
├── unified-trading-pm/                   ← THIS repo (must be a sibling, not the root)
│   ├── cursor-rules/                     ← git-tracked source of truth for rules
│   ├── cursor-configs/                   ← git-tracked workspace configs
│   ├── workspace-manifest.json           ← canonical repo registry
│   ├── manifest_warnings.yaml            ← bad-release annotations
│   ├── scripts/                          ← workspace automation scripts
│   └── plans/ai/                         ← AI execution plans
│
├── unified-trading-codex/                ← standards and specifications
├── unified-trading-deployment-v3/        ← deployment configs
├── instruments-service/                  ← service repo
└── ...38+ other repos
```

**The scripts will error if:**
- `unified-trading-pm/` IS the workspace root (not a sibling)
- No `.cursor/` directory exists at the workspace root
- No known sibling repos exist (wrong clone location)
- `unified-trading-pm/` is not a git repo

---

## First-Time Setup (New Machine)

```bash
# 1. Clone all repos into a shared workspace root
mkdir -p ~/repos/unified-trading-system-repos
cd ~/repos/unified-trading-system-repos
git clone git@github.com:IggyIkenna/unified-trading-pm.git
git clone git@github.com:IggyIkenna/unified-trading-codex.git
# ... clone other repos

# 2. Open the workspace root in Cursor (creates .cursor/ automatically)
cursor .

# 3. Pull the team's latest Cursor rules into your local .cursor/rules/
cd unified-trading-pm && git pull
./scripts/sync-rules-pull.sh

# 4. (Optional) Set up a GCP dev project
cd unified-trading-deployment-v3
./scripts/setup-dev-project.sh <your-dev-project-id>
```

---

## Day-to-Day Workflow

### Push rule/script/manifest changes to the team

```bash
cd unified-trading-pm
bash scripts/quickmerge.sh "feat: describe your change"
```

This is the **only command you need**. Quickmerge automatically:
1. Syncs your local `.cursor/rules/` → `cursor-rules/` (Stage 0)
2. Validates `workspace-manifest.json` is valid JSON
3. Creates a branch, commits all changes, opens a PR with auto-merge

### Pull the team's latest changes

```bash
cd unified-trading-pm && git pull
./scripts/sync-rules-pull.sh    # copies cursor-rules/ → your .cursor/rules/
```

Restart Cursor (or `Developer: Reload Window`) for new rules to take effect.

### Check what's different between your local rules and the repo

```bash
cd unified-trading-pm && ./scripts/sync-workspace.sh
```

---

## Contents

| Path | Purpose |
|---|---|
| `workspace-manifest.json` | Canonical registry of all 38+ repos — types, deps, versions, doc standards |
| `manifest_warnings.yaml` | Additive-only bad-release annotations (never delete entries) |
| `cursor-rules/` | Git-tracked source of truth for all `.cursor/rules/*.mdc` files |
| `cursor-configs/` | `.cursorrules` and `*.code-workspace` files |
| `scripts/` | Workspace automation: drift checkers, rollback helper, sync, setup |
| `plans/ai/` | AI agent execution plans (current and historical) |
| `plans/` | Human project plans, epics, milestones |
| `archive/` | Deprecated content preserved for reference |

---

## Scripts Reference

| Script | What it does |
|---|---|
| `quickmerge.sh "msg"` | **Main command.** Syncs rules + commits + PR. Use for all pm changes. |
| `sync-rules-pull.sh` | Pull team rules from `cursor-rules/` → `.cursor/rules/` |
| `sync-rules-push.sh` | Standalone push (rarely needed — quickmerge does this automatically) |
| `sync-workspace.sh` | Show diff between local rules and repo rules |
| `rollback.sh <repo> <version>` | Safety-checked deployment rollback helper |
| `completeness-checker-agent.sh` | Check Codex completeness vs workspace-manifest |
| `diff-checker-agent.sh` | Check code-to-spec drift |

---

## See Also

- `unified-trading-codex/05-infrastructure/workspace-setup.md` — full workspace setup guide
- `unified-trading-codex/05-infrastructure/versioning-rollback.md` — versioning and rollback model
- `unified-trading-codex/05-infrastructure/quickmerge-architecture.md` — CI/CD pipeline diagrams
