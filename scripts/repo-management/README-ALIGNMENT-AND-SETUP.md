# Version Alignment + Run-All-Setup Workflow

**SSOT for CI/CD pipeline:** `unified-trading-pm/codex/08-workflows/ci-cd-flow.md`. **SSOT for workspace setup:**
`unified-trading-pm/codex/05-infrastructure/workspace-setup.md` (alignment + setup + bootstrap + mock-infra).

**This doc:** Phase 1–2 only. Referenced by Codex and cursor rules.

Run **version alignment first**, then **setup in all repos**. Do not run setup if alignment has conflicts.

## 1. Version alignment (run first)

```bash
cd /path/to/unified-trading-system-repos
bash unified-trading-pm/scripts/repo-management/run-version-alignment.sh
```

If misalignment is reported:

```bash
bash unified-trading-pm/scripts/repo-management/run-version-alignment.sh --fix
```

This script:

- Generates derived-dependency-manifest.json from all pyproject.toml
- Generates canonical-dependency-manifest.json from workspace-constraints.toml
- Compares derived vs manifest + canonical
- Validates constraints resolve (uv pip compile)
- With --fix: applies internal (tier-aware) and external alignment fixes

**Internal alignment SSOT:** unified-trading-pm/scripts/manifest/README-DEPENDENCY-ALIGNMENT.md

## 2. Run setup in all repos (after alignment OK)

```bash
bash unified-trading-pm/scripts/repo-management/run-all-setup.sh
```

First-time bootstrap or after template changes (propagate setup.sh + quality-gates.sh first):

```bash
bash unified-trading-pm/scripts/repo-management/run-all-setup.sh --rollout-first
```

Verify only (no install):

```bash
bash unified-trading-pm/scripts/repo-management/run-all-setup.sh --check
```

This runs scripts/setup.sh in each repo in **topological tier order** (T0 → T1 → T2 → services → UIs). Repos within the
same tier have no mutual dependencies and run **in parallel**; each tier waits for the previous tier to complete before
starting. With `--rollout-first`, propagates setup.sh + quality-gates.sh templates to all repos before running setup.

### uv.lock and agents

- **setup.sh** runs uv lock when pyproject.toml is newer than uv.lock.
- **run-all-setup** therefore updates uv.lock in every repo where deps changed.
- **uv.lock is committed** (never in .gitignore) — agents and CI get identical deps via git pull.
- After run-all-setup, **commit and push** any changed uv.lock files so other devs and agents receive them.

## 3. Alternative: workspace-bootstrap

For a full bootstrap (clone + workspace venv + setup):

```bash
bash unified-trading-pm/scripts/workspace/workspace-bootstrap.sh --skip-system
```

Use when repos are already cloned and you want Phase 4 (setup) + Phase 5 (import smoke test).

---

## References

| Doc                        | Location                                                                               |
| -------------------------- | -------------------------------------------------------------------------------------- |
| **Workspace setup (SSOT)** | codex/05-infrastructure/workspace-setup.md                                             |
| **CI/CD pipeline (SSOT)**  | codex/08-workflows/ci-cd-flow.md                                                       |
| **Codex**                  | unified-trading-codex/06-coding-standards/setup-standards.md, dependency-management.md |
| **Cursor rule**            | cursor-rules/dependencies/dependency-alignment-and-setup-flow.mdc                      |
| **Internal alignment**     | scripts/manifest/README-DEPENDENCY-ALIGNMENT.md                                        |
| **uv.lock**                | cursor-rules/dependencies/uv-lock-file.mdc                                             |
