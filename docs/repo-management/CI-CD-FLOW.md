# Full CI/CD Flow — SSOT

**SSOT:** This document. Single entry point for dependency alignment, setup, sync-to-main, and conflict resolution.

**Run from workspace root:** All scripts assume you run from the workspace root (parent of unified-trading-pm). cd there first, then run any script.

Run scripts in this order. Do not skip steps when dependencies or code have changed.

---

## How Setup and Quality Gates Work for Every Repo

**setup.sh** — One canonical file from PM. It auto-detects repo type (Python vs UI) and branches internally: Python repos get `uv lock`, venv, path deps; UI repos get `npm install`. No repo-specific customization needed; each repo has its own `pyproject.toml` or `package.json`.

**quality-gates.sh** — Propagated from templates by repo type. `rollout-quality-gates-unified.py` (or `run-all-setup.sh --rollout-first`) copies the right template per `workspace-manifest.json` type: library → library template; service/api-service → service template; ui → TypeScript (npm typecheck, lint, smoketest). Repos never need to know each other's dependencies.

**Rollout** — Copies `setup.sh` + `quality-gates.sh` into each repo. Run when templates change in PM, or use `--rollout-first` for first-time bootstrap.

---

## Phase 1: Dependency Alignment (manifest ↔ pyproject.toml)

Align workspace manifest with pyproject.toml in each repo. Fix any fixable misalignments; flag unresolvable ones.

```bash
cd /path/to/unified-trading-system-repos

# 1. Check alignment
bash unified-trading-pm/scripts/repo-management/run-version-alignment.sh

# 2. If misaligned, fix (tier-aware; tier violations are flagged, not auto-fixed)
bash unified-trading-pm/scripts/repo-management/run-version-alignment.sh --fix

# 3. Re-check until clean (or until only unresolvable remain)
bash unified-trading-pm/scripts/repo-management/run-version-alignment.sh
```

**Unresolvable:** Tier violations and constraint conflicts are reported and exit 1. Resolve manually (e.g. update manifest, relax constraints) before proceeding.

**Ref:** `scripts/repo-management/README-ALIGNMENT-AND-SETUP.md`, `scripts/manifest/README-DEPENDENCY-ALIGNMENT.md`

---

## Phase 2: Run Setup (venvs + uv.lock ↔ tomls)

Update VM venvs and uv.lock in every repo so they match pyproject.toml.

```bash
# Standard: run setup.sh in each repo
bash unified-trading-pm/scripts/repo-management/run-all-setup.sh

# First-time bootstrap or after template changes: rollout templates first, then setup
bash unified-trading-pm/scripts/repo-management/run-all-setup.sh --rollout-first
```

Runs `scripts/setup.sh` per repo in topological order. `setup.sh` runs `uv lock` when pyproject.toml is newer than uv.lock. With `--rollout-first`, propagates `setup.sh` + `quality-gates.sh` from PM to all repos before running setup.

**After:** Commit and push any changed `pyproject.toml`, `uv.lock`, `workspace-manifest.json` so agents and CI get identical deps.

**Ref:** `scripts/repo-management/README-ALIGNMENT-AND-SETUP.md`

---

## Phase 2b: Workspace Venv (aggregate-workspace-deps.py)

After Phase 2, install all repo dependencies into the shared workspace venv (`.venv-workspace`). Required for cross-repo imports, quality gates from workspace root, and agent tooling.

```bash
# From workspace root (after run-all-setup.sh)
source .venv-workspace/bin/activate
python unified-trading-pm/scripts/workspace/aggregate-workspace-deps.py

# Re-resolve from scratch (ignore existing lock)
python unified-trading-pm/scripts/workspace/aggregate-workspace-deps.py --resolve
```

**When:** Run after Phase 2 completes. `workspace-bootstrap.sh` invokes this automatically; for incremental runs after `run-all-setup.sh`, run it manually if you use the workspace venv.

**Ref:** `scripts/workspace/aggregate-workspace-deps.py` (docstring)

---

## Phase 3: Sync to Main (quickmerge)

Push local changes to main via quickmerge (PR + auto-merge). Only run if there are changes to push.

```bash
# Standard sync
bash unified-trading-pm/scripts/repo-management/sync-all-to-main.sh

# When path deps (unified-*-interface, etc.) have local changes — avoids DEPENDENCY CONFLICT
bash unified-trading-pm/scripts/repo-management/sync-all-to-main.sh --dep-branch "chore/sync-all"

# Sync only repos matching a glob
bash unified-trading-pm/scripts/repo-management/sync-all-to-main.sh --filter "unified-*" --dep-branch "chore/sync-all"
```

**`--filter PATTERN`** — Sync only repos matching glob (e.g. `unified-*`, `*-service`). Use with `--dep-branch` when path deps have local changes.

**When to use `--dep-branch`:** If quickmerge fails with `DEPENDENCY CONFLICT DETECTED` (path deps differ from origin/main), re-run with `--dep-branch NAME`. Quickmerge will cascade changes to that branch in dependency order.

**Per-repo flow:**

1. Fetch origin/main
2. Merge origin/main into local
3. **If merge conflict** → abort, FAIL, exit. Do **not** continue.
4. If no conflict and local has changes → run quickmerge (quality gates + PR + auto-merge)

**Unresolvable conflict:** When sync reports `merge conflict with origin/main` for a repo:

- Sync **exits** (does not continue to other repos)
- You must resolve manually before re-running

**Ref:** `docs/repo-management/sync-to-main-flow.md`

---

## Phase 4: After Merge Conflicts — Verify Our Version, Then Fix

When sync fails with merge conflicts:

1. **Run quality gates on the conflicted repo(s)** — verify our local version passes before merging:

   ```bash
   bash unified-trading-pm/scripts/repo-management/run-all-quality-gates.sh --repo <repo-name>
   ```

   Or run quality gates only on failed repos from the sync output.

2. **If our version passes** — manually resolve merge conflicts in Cursor:
   - `cd <repo>`
   - Fix conflicts (preserve good work from main where appropriate)
   - Commit, then re-run sync for that repo:
     ```bash
     bash unified-trading-pm/scripts/repo-management/sync-all-to-main.sh --repo <repo-name>
     ```

3. **If our version fails quality gates** — fix quality gate issues first, then resolve conflicts.

**Why:** Running quality gates on conflicted repos confirms our branch is valid before we merge. Avoids losing good work from main by resolving conflicts with a broken local state.

---

## Quick Reference: Full Flow

| Step | Command                                                                    | When                                               |
| ---- | -------------------------------------------------------------------------- | -------------------------------------------------- |
| 1    | `run-version-alignment.sh`                                                 | Always first when deps may have changed            |
| 2    | `run-version-alignment.sh --fix`                                           | If step 1 reports misalignment                     |
| 3    | `run-all-setup.sh` (use `--rollout-first` for bootstrap/template changes)  | After alignment OK                                 |
| 4    | Commit + push pyproject.toml, uv.lock, manifest                            | After run-all-setup                                |
| 4b   | `aggregate-workspace-deps.py` (or `--resolve`)                             | After Phase 2, if using workspace venv             |
| 5    | `sync-all-to-main.sh` (add `--dep-branch NAME` if DEPENDENCY CONFLICT)     | When pushing to main (only if deviation from main) |
| 6a   | If sync fails: merge conflict → resolve manually, re-run sync              | Per conflicted repo                                |
| 6b   | If sync fails: run `run-all-quality-gates.sh --repo X` on conflicted repos | Verify our version passes before fixing conflicts  |

---

## Deviation from Main

- **No deviation:** Repo is clean or matches origin/main → sync skips (OK, no changes).
- **Deviation:** Local has uncommitted or unpushed changes → sync runs quickmerge.
- **Unresolvable:** Merge conflict → sync FAILs, exits. Resolve manually, then re-run.

---

## Workspace Scripts (scripts/workspace/)

| Script                                | Purpose                                                                                                                               | When it runs                                                                                                                                                                                                                                                                     |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **validate-workspace-constraints.py** | Validates `workspace-constraints.toml` resolves without dependency conflicts (runs `uv pip compile`). Caches result by file hash.     | Called by `validate-dependency-conflicts.py` during Phase 1 (step 4 of run-version-alignment.sh). Run when constraints may have changed.                                                                                                                                         |
| **resolve-canonical-versions.py**     | Derives `workspace-constraints.toml` from all repo `pyproject.toml` files (topological order). Picks tightest constraint per package. | **Not** called by `run-version-alignment.sh --fix`. Called only by `validate-dependency-conflicts.py --regenerate` when constraints conflict. Use for intentional sync (e.g. migration); do **not** use to "fix" alignment — use `fix_external_dependency_alignment.py` instead. |
| **aggregate-workspace-deps.py**       | Installs all repo deps into `.venv-workspace`. Uses `workspace-constraints.toml` + path deps.                                         | After Phase 2 (run-all-setup.sh). See Phase 2b above.                                                                                                                                                                                                                            |

**Location:** `unified-trading-pm/scripts/workspace/`

---

---

## Troubleshooting

| Failure                                    | Fix                                                                                                                                                                                  |
| ------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Prettier (pre-commit)**                  | Quickmerge auto-runs Prettier before commit. If it still fails, run `npx prettier --write .` in the repo, then re-run quickmerge.                                                    |
| **Act simulation (GH_PAT)**                | Quickmerge **fails** (does not skip) when act fails. SSOT: unified-trading-pm/docs/repo-management/act-secrets-setup.md. Run generate-act-secrets.sh, edit .act-secrets, add GH_PAT. |
| **Type check (.venv-workspace not found)** | PM `pyrightconfig.json` uses `.venv` (repo-local). Ensure `bash scripts/setup.sh` ran so `.venv` exists.                                                                             |

## References

| Doc                                                     | Purpose                                                                |
| ------------------------------------------------------- | ---------------------------------------------------------------------- |
| **This doc**                                            | Full CI/CD flow SSOT                                                   |
| `scripts/repo-management/README-ALIGNMENT-AND-SETUP.md` | Phase 1–2 detail                                                       |
| `docs/repo-management/sync-to-main-flow.md`             | Phase 3 detail                                                         |
| `scripts/manifest/README-DEPENDENCY-ALIGNMENT.md`       | Internal alignment                                                     |
| **Codex**                                               | `06-coding-standards/setup-standards.md`, `dependency-management.md`   |
| **Cursor rules**                                        | `dependency-alignment-and-setup-flow.mdc`, `always-use-quickmerge.mdc` |
