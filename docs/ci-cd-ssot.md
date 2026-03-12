# CI/CD Single Source of Truth

> **Canonical owner**: `unified-trading-pm` (PM repo) **Referenced by**: `.cursor/rules/ci-cd/ci-rollout-ownership.mdc`,
> `unified-trading-codex/05-infrastructure/`

This document is the definitive reference for how CI/CD works in this workspace. Before touching any CI workflow,
quality gate, or dependency install, read this.

---

## 1. Ownership Map — What Lives Where

Everything that runs across multiple repos is owned in PM and propagated. Never fix a per-repo file when the real fix
belongs here.

### Quality Gate Logic (instantly inherited — no rollout needed)

| File                                              | Owns                                                    |
| ------------------------------------------------- | ------------------------------------------------------- |
| `scripts/quality-gates-base/base-service.sh`      | Gate logic for all Python service/API repos (~50 repos) |
| `scripts/quality-gates-base/base-library.sh`      | Gate logic for library/interface repos                  |
| `scripts/quality-gates-base/base-ui.sh`           | Gate logic for TypeScript/React UI repos (14 repos)     |
| `scripts/quality-gates-base/.prettierignore-base` | Shared prettier ignore rules (inherited by all repos)   |

Per-repo `scripts/quality-gates.sh` is a **~10-line config stub only** (sets `SERVICE_NAME`, `SOURCE_DIR`,
`MIN_COVERAGE`). It sources the base script live from PM at runtime. Changes to base scripts propagate to all repos
immediately — no commit, no rollout needed.

### CI Workflow Files (require rollout — static YAML per repo)

Per-repo `.github/workflows/quality-gates.yml` files are thin callers:

```yaml
jobs:
  quality-gates:
    uses: IggyIkenna/unified-trading-pm/.github/workflows/python-quality-gates.yml@<active_branch>
    with:
      dep_repos: "unified-trading-library unified-config-interface"
    secrets:
      GH_PAT: ${{ secrets.GH_PAT }}
```

The reusable workflows that contain all the real CI logic:

| Reusable workflow                            | Owns                                                                                              |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `.github/workflows/python-quality-gates.yml` | Full CI job for Python repos (Python setup, uv, tools, dep clone, install, run QG, record status) |
| `.github/workflows/ui-quality-gates.yml`     | Full CI job for UI repos (Node.js setup, PM clone, npm ci, run QG)                                |

The `@<active_branch>` ref is pinned to `active_feature_branch` from `workspace-manifest.json` and re-pinned
automatically by `.github/workflows/rollout-action-ref.yml` on every push to `main`/`staging`.

### Rollout Scripts (run when per-repo files need updating)

| Script                                                                      | What it patches                                                | When to run                                                      |
| --------------------------------------------------------------------------- | -------------------------------------------------------------- | ---------------------------------------------------------------- |
| `scripts/propagation/rollout-quality-gates-ci-workflows.py`                 | Per-repo `.github/workflows/quality-gates.yml`                 | Any change to CI workflow shape, env vars, or branch refs        |
| `scripts/propagation/rollout-quality-gates-ci-workflows.py --workflow-call` | Full regeneration of thin callers from manifest `dependencies` | When reusable workflow structure changes                         |
| `scripts/propagation/rollout-quality-gates-unified.py`                      | Per-repo `scripts/quality-gates.sh` stubs                      | Only when base script adds a new required stub variable          |
| `scripts/propagation/rollout-action-ref.yml` (GHA)                          | `@<ref>` in all thin callers                                   | Auto-fires on `workspace-manifest.json` push to `main`/`staging` |

### Other PM-Owned Propagation Scripts

| Script                                                                                   | What it owns                                                          |
| ---------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| `scripts/repo-management/run-version-alignment.sh`                                       | Version cascade: workspace-manifest, pyproject.toml, imports, uv.lock |
| `scripts/validation/check-workflow-tokens.py`                                            | Validates GH_PAT usage across all repo workflows                      |
| `scripts/propagation/rollout-quickmerge.py` + `.github/workflows/rollout-quickmerge.yml` | Quickmerge-based batch commits across all repos                       |

---

## 2. The No-Direct-Install Principle

**Never run `pip install`, `uv pip install`, or `npm install <package>` to add a new dependency to a repo — in a local
shell, agent session, or CI step.**

This creates invisible state: one dev's machine has it, another's doesn't. CI uses a fresh venv on every run. The
version alignment script won't see it. You get "works on my machine" failures and drift between developers.

### Flat Dependencies Rule

**Every repo has exactly one dependency list: `[project.dependencies]`. No `[project.optional-dependencies]` exists
anywhere — not `dev`, not `test`, not any group.**

All deps are mandatory and declared flat. Tests run locally, in Cloud Build, Code Build, and GitHub Actions. Every
environment needs every dependency. Optional groups create silent omissions and version conflicts between environments.
There is no deployment scenario where we build per-role images. The complexity is pointless.

### Correct Flow for Adding a Dependency

```
1. Edit pyproject.toml   →   add to [project.dependencies] ONLY — never optional-dependencies
2. Edit imports          →   use the new package in source code
3. Update manifest       →   if it's a new internal/sibling dep, add to dependencies[] in
                              workspace-manifest.json for that repo
4. Run uv lock           →   cd <repo> && uv lock   (updates uv.lock)
5. Run setup             →   uv sync                (installs locally — no extras)
6. Run QG                →   bash scripts/quality-gates.sh
```

Step 3 is required for internal workspace deps — the version alignment script and CI dep-clone step both read from
`workspace-manifest.json`.

### Version Alignment Will Catch It

`bash unified-trading-pm/scripts/repo-management/run-version-alignment.sh` runs four checks:

- Manifest versions match `pyproject.toml` versions
- Imports in source match declared deps
- `uv.lock` is in sync with `pyproject.toml`
- All sibling repos needed by this repo are declared in manifest

If you install something directly without updating these, the alignment script will flag the mismatch on the next run.

---

## 3. The Two-Pass Quickmerge Model

All commits go through quickmerge, never raw `git push`:

```
Pass 1: bash scripts/quality-gates.sh          # Full: lint + typecheck + tests + codex + security
Pass 2: bash scripts/quickmerge.sh "msg" --agent  # Lightweight: lint + format + typecheck + codex
```

In Claude Code / agent sessions: always use `--agent`. Never `--dep-branch`. Branch is read automatically from
`active_feature_branch` in `workspace-manifest.json`.

---

## 4. Branch Model and CI Triggers

| Branch                               | Purpose                          | CI trigger                |
| ------------------------------------ | -------------------------------- | ------------------------- |
| `feat/*`                             | Feature work                     | QG on PR only             |
| `live-defi-rollout` (current active) | Active feature branch            | QG on PR + push           |
| `staging`                            | Convergence for breaking changes | SIT validates before main |
| `main`                               | Always stable                    | QG + cascade              |

The `uses: ...@<active_branch>` in thin callers means CI always runs against the latest reusable workflow on the active
feature branch. When a branch merges, `rollout-action-ref.yml` updates all thin callers to the new active branch
automatically.

---

## 5. Adding a New Repo

1. Add the repo to `workspace-manifest.json` with correct `type`, `dependencies`, `arch_tier`
2. Run `scripts/propagation/rollout-quality-gates-unified.py --repo <name>` to write the QG stub
3. Run `scripts/propagation/rollout-quality-gates-ci-workflows.py --workflow-call --repo <name>` to write the thin CI
   caller
4. Add `uv.lock`, `pyproject.toml` with `[project.dependencies]` and `[project.optional-dependencies.dev]`
5. Add Dockerfile using the shared base image pattern (see `.cursor/rules/ci-cd/cicd-setup.mdc`)
6. First commit via quickmerge creates the branch and PR

---

## 6. Where NOT to Edit

| Tempting but wrong                                 | Correct place                                           |
| -------------------------------------------------- | ------------------------------------------------------- |
| Add a gate check to per-repo `quality-gates.sh`    | `scripts/quality-gates-base/base-service.sh`            |
| Fix a CI env var in one repo's `quality-gates.yml` | `python-quality-gates.yml` reusable workflow            |
| Add `pip install ruff` to a CI step                | Update `setup-python-tools/action.yml` composite action |
| Fix prettier ignore in one repo                    | `scripts/quality-gates-base/.prettierignore-base`       |
| Hardcode a version in one repo's workflow          | `workspace-manifest.json` + version alignment           |
