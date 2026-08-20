# unified-trading-pm

Project management, workspace tooling, and shared configuration for the Unified Trading System. This is Level 0 (root)
in the workspace topology — the SSOT template host and workspace management repo.

---

## Quick Start

```bash
# 1. Clone into the workspace root alongside sibling repos
cd ~/repos/unified-trading-system-repos
git clone git@github.com:IggyIkenna/unified-trading-pm.git

# 2. Set up workspace paths and IDE config
bash unified-trading-pm/scripts/workspace/setup-workspace-root.sh

# 3. Symlink .cursor/rules/ to this repo's git-tracked rules — no separate sync step;
#    edits under .cursor/rules/ directly modify tracked files, committed via quickmerge like any other change
bash unified-trading-pm/scripts/workspace/setup-cursor-rules-symlink.sh

# 4. (Optional) Full workspace bootstrap — clones all repos, installs deps
bash unified-trading-pm/scripts/workspace/workspace-bootstrap.sh
```

Full setup guide: [docs/workspace-setup.md](docs/workspace-setup.md) | IDE coordination:
[docs/both-ides-setup.md](docs/both-ides-setup.md)

---

## Repo Layout

```
unified-trading-pm/
├── workspace-manifest.json        SSOT registry of all 60+ repos (types, deps, versions)
├── manifest_warnings.yaml         Bad-release annotations (append-only)
├── WORKSPACE_MANIFEST_DAG.svg     Visual dependency DAG (auto-generated)
│
├── docs/                          All documentation
│   ├── workspace-setup.md         Full workspace setup guide
│   ├── both-ides-setup.md         Cursor + Claude Code IDE coordination
│   └── index-migration.md         Cursor index migration guide
│
├── scripts/                       Workspace automation
│   ├── setup.sh                   SSOT template: environment bootstrap
│   ├── quality-gates.sh           SSOT template: lint + test pipeline
│   ├── quickmerge.sh              SSOT template: git + PR automation
│   ├── _workspace-lib.sh          Shared bash helpers
│   ├── workspace/                 Workspace setup, sync, and bootstrap
│   ├── propagation/               SSOT template rollout to all repos (4 scripts)
│   ├── validation/                Code quality, import, and dep checks (10 scripts)
│   ├── manifest/                  DAG generator and SBOM tools
│   ├── agents/                    LLM agent wrappers (3 scripts)
│   ├── repo-management/           GitHub repo and collaborator setup
│   └── migration/                 One-off migrations and cleanups (4 scripts)
│
├── cursor-configs/                VS Code workspace profiles
│
├── plans/                         Project planning and execution
│   ├── active/                    Currently executing plans
│   ├── cicd/                      CI/CD infrastructure plans
│   ├── cursor-plans/              Cursor agent prompts and architecture plans
│   └── tasks/                     Agent task definitions (cursor/ + claude-code/)
│
├── github-integration/            GitHub Projects automation and issue management
├── security/                      Internal security advisories (append-only)
├── templates/                     Per-repo setup templates (AGENTS.md)
└── tests/                         pytest + bats tests
```

---

## Day-to-Day Workflow

### Push changes to the team

```bash
cd unified-trading-pm
bash scripts/quickmerge.sh "feat: describe your change"
```

Quickmerge validates the manifest and commits directly to the shared `live-defi-rollout` branch (no branch/PR for
the default flow; `--hotfix` opens a PR against `main` instead — see `/codex/08-workflows/ci-cd-flow.md`).

### Pull the team's latest

```bash
cd unified-trading-pm && git pull
```

`.cursor/rules/` is a symlink into this repo's tracked rules (`setup-cursor-rules-symlink.sh`), so a `git pull` alone
picks up rule changes — there is no separate sync step.

---

## Key Scripts

| Script                                            | Purpose                                                                    |
| ------------------------------------------------- | -------------------------------------------------------------------------- |
| `scripts/quickmerge.sh "msg"`                     | Main command — validates manifest, commits directly to `live-defi-rollout` |
| `scripts/workspace/setup-cursor-rules-symlink.sh` | Symlink `.cursor/rules/` into this repo's tracked rules                    |
| `scripts/workspace/workspace-bootstrap.sh`        | Full workspace setup from scratch                                          |
| `scripts/manifest/generate_workspace_dag.py`      | Regenerate DAG SVG from manifest                                           |
| `scripts/quality-gates.sh`                        | Run full lint + type-check + test pipeline                                 |

---

## Required Workspace Structure

This repo **must** be a sibling directory alongside all other system repos:

```
~/repos/unified-trading-system-repos/     <- workspace root (open in Cursor)
├── .cursor/rules/                        <- symlink into unified-trading-pm/.cursor/rules/
├── unified-trading-pm/                   <- THIS repo (codex/ here is the standards SSOT; unified-trading-codex is ARCHIVED)
├── instruments-service/                  <- service repo
├── .tabs/<N>/                            <- per-operator-slot worktrees (one clone of every active repo each, on live-defi-rollout)
└── ...60+ other repos
```

---

## See Also

- [docs/workspace-setup.md](docs/workspace-setup.md) — full workspace setup guide
- [docs/both-ides-setup.md](docs/both-ides-setup.md) — Cursor + Claude Code IDE setup
- `codex/05-infrastructure/` — infrastructure docs, versioning, CI/CD diagrams (this repo — `unified-trading-codex` is
  ARCHIVED)
