# Full CI/CD Flow — SSOT

**SSOT:** This document. Single entry point for dependency alignment, setup, sync-to-main, and conflict resolution.

**Run from workspace root:** All scripts assume you run from the workspace root (parent of unified-trading-pm). cd there
first, then run any script.

Run scripts in this order. Do not skip steps when dependencies or code have changed.

---

## How Setup and Quality Gates Work for Every Repo

**setup.sh** — One canonical file from PM. It auto-detects repo type (Python vs UI) and branches internally: Python
repos get `uv lock`, venv, path deps; UI repos get `npm install`. No repo-specific customization needed; each repo has
its own `pyproject.toml` or `package.json`.

**quality-gates.sh** — Propagated from templates by repo type. `rollout-quality-gates-unified.py` (or
`run-all-setup.sh --rollout-first`) copies the right template per `workspace-manifest.json` type: library → library
template; service/api-service → service template; ui → TypeScript (npm typecheck, lint, smoketest). Repos never need to
know each other's dependencies.

**Rollout** — Copies `setup.sh` + `quality-gates.sh` into each repo. Run when templates change in PM, or use
`--rollout-first` for first-time bootstrap.

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

**Unresolvable:** Tier violations and constraint conflicts are reported and exit 1. Resolve manually (e.g. update
manifest, relax constraints) before proceeding.

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

Runs `scripts/setup.sh` per repo in topological order. `setup.sh` runs `uv lock` when pyproject.toml is newer than
uv.lock. With `--rollout-first`, propagates `setup.sh` + `quality-gates.sh` from PM to all repos before running setup.

**After:** Commit and push any changed `pyproject.toml`, `uv.lock`, `workspace-manifest.json` so agents and CI get
identical deps.

**Ref:** `scripts/repo-management/README-ALIGNMENT-AND-SETUP.md`

---

## Phase 2b: Workspace Venv (aggregate-workspace-deps.py)

After Phase 2, install all repo dependencies into the shared workspace venv (`.venv-workspace`). Required for cross-repo
imports, quality gates from workspace root, and agent tooling.

```bash
# From workspace root (after run-all-setup.sh)
source .venv-workspace/bin/activate
python unified-trading-pm/scripts/workspace/aggregate-workspace-deps.py

# Re-resolve from scratch (ignore existing lock)
python unified-trading-pm/scripts/workspace/aggregate-workspace-deps.py --resolve
```

**When:** Run after Phase 2 completes. `workspace-bootstrap.sh` invokes this automatically; for incremental runs after
`run-all-setup.sh`, run it manually if you use the workspace venv.

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

**`--filter PATTERN`** — Sync only repos matching glob (e.g. `unified-*`, `*-service`). Use with `--dep-branch` when
path deps have local changes.

**When to use `--dep-branch`:** If quickmerge fails with `DEPENDENCY CONFLICT DETECTED` (path deps differ from
origin/main), re-run with `--dep-branch NAME`. Quickmerge will cascade changes to that branch in dependency order.

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

**Why:** Running quality gates on conflicted repos confirms our branch is valid before we merge. Avoids losing good work
from main by resolving conflicts with a broken local state.

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

## Admin Operations (Special Circumstances Only)

> **WARNING:** These operations bypass normal CI/CD flow and branch protections. Use only when the standard sync-to-main
> flow cannot be used (e.g. remote main has diverged from local after a bad merge, workspace recovery after destructive
> remote changes, or emergency local-state promotion).

### Force-Push All Repos to Main (Admin Only)

**Script:** `scripts/repo-management/admin-force-sync-all-to-main.sh` **Access:** IggyIkenna only (identity gate via
`gh api user`). All other users are rejected.

Overwrites `origin/main` with the current local state for all (or selected) repos. Works from **any local branch** — no
checkout to `main` required. Auto-stages and commits all local changes (including untracked files and deletions) before
pushing, so the push reflects true local state. After a successful push, automatically switches the local branch to
`main` to avoid post-sync branch confusion.

```bash
# All repos — dry run first to inspect what would be committed + pushed
bash unified-trading-pm/scripts/repo-management/admin-force-sync-all-to-main.sh --dry-run

# All repos — force push (disables + restores branch protection automatically)
bash unified-trading-pm/scripts/repo-management/admin-force-sync-all-to-main.sh

# Single repo
bash unified-trading-pm/scripts/repo-management/admin-force-sync-all-to-main.sh --repo unified-trading-pm

# Multiple specific repos (comma-separated)
bash unified-trading-pm/scripts/repo-management/admin-force-sync-all-to-main.sh --repos "unified-trading-pm,unified-events-interface"

# Skip staging/committing (push current committed HEAD as-is)
bash unified-trading-pm/scripts/repo-management/admin-force-sync-all-to-main.sh --no-commit

# Skip branch protection disable/restore (if already disabled or not configured)
bash unified-trading-pm/scripts/repo-management/admin-force-sync-all-to-main.sh --skip-protection
```

**What it does per repo:**

1. `git add -A` — stages all modifications, deletions, and untracked files (from any local branch)
2. `git commit -m "chore: force-sync local state"` — commits staged changes (pre-commit hooks run normally)
3. Disables branch protection + rulesets
4. `git push --force origin HEAD:main` — pushes current HEAD to remote main (works from any branch)
5. Restores branch protection immediately after push
6. `git checkout -B main` — resets local `main` pointer to current HEAD and switches to it

**When to use:**

| Situation                                                | Use                                                          |
| -------------------------------------------------------- | ------------------------------------------------------------ |
| Remote main diverged (bad merge, external push)          | Default — all repos                                          |
| Working on a feature branch with committed local changes | Works automatically — push from any branch                   |
| Untracked/unstaged local files not on remote             | Runs automatically — no extra flags needed                   |
| PM plans archive/active out of sync on remote            | Delete from disk first, then run — deletions are auto-staged |
| Emergency workspace recovery                             | Default — all repos                                          |

**When NOT to use:** Do not use as a substitute for `sync-all-to-main.sh` in normal workflow. Force-push skips quality
gates, PR review, and semver-agent. Always prefer Phase 3 (quickmerge) for standard changes.

---

## Troubleshooting

| Failure                                    | Fix                                                                                                                                                                                  |
| ------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Prettier (pre-commit)**                  | Quickmerge auto-runs Prettier before commit. If it still fails, run `npx prettier --write .` in the repo, then re-run quickmerge.                                                    |
| **Act simulation (GH_PAT)**                | Quickmerge **fails** (does not skip) when act fails. SSOT: unified-trading-pm/docs/repo-management/act-secrets-setup.md. Run generate-act-secrets.sh, edit .act-secrets, add GH_PAT. |
| **Type check (.venv-workspace not found)** | PM `pyrightconfig.json` uses `.venv` (repo-local). Ensure `bash scripts/setup.sh` ran so `.venv` exists.                                                                             |

## Feature Branch Flow

Use a feature branch when you have local changes in dependency repos that haven't been pushed to main yet.

```bash
# Standard: direct to main (no local dep changes)
bash unified-trading-pm/scripts/quickmerge.sh "feat: my change"

# Feature branch: local dep changes present
bash unified-trading-pm/scripts/quickmerge.sh "feat: my change" --dep-branch feat/my-feature
```

**What `--dep-branch feat/my-feature` does (STAGE 0 — Cascade):**

1. Reads `workspace-manifest.json` to find all transitive ancestors of the current repo (full DAG walk upward)
2. For each ancestor that exists locally: stashes local changes, creates/switches to `feat/my-feature` branch, pops
   stash
3. Only ancestors are touched — siblings and unrelated repos are left alone
4. Then proceeds with normal quickmerge stages (Stage 1: dependency validation now passes because deps are on the same
   branch)

**Version bump rules on feature branches:**

- `semver-agent.yml` and the disabled `version-bump.yml` only fire on `main` or `staging` — never on `feat/*`
- `pyproject.toml` versions are **never** bumped on feature branches
- Version bumping only happens when the PR from `feat/*` merges to `main` and semver-agent fires

**Flow:**

```
feat/my-feature branch
  → quickmerge (--dep-branch feat/my-feature)
    → STAGE 0: cascade ancestors to feat/my-feature
    → STAGE 1-5: QG + PR to main
  → PR auto-merges to main
  → semver-agent.yml fires on main push
    → Claude-Haiku reads commit + API diff → decides patch/minor/major
    → bumps pyproject.toml on main
    → dispatches version-bump to PM → PM manifest updated
    → cascade dispatches to dependents
```

---

## Version Bump Rules (Semver-Agent Only)

`semver-agent.yml` is the **sole owner** of version bumping. `version-bump.yml` is disabled (`if: false`).

**When it fires:** push to `main` or `staging` only (never on `feat/*`).

**What it does:**

1. Reads current version from `pyproject.toml`
2. Reads merge commit message + `git diff HEAD~1 -- <source_dir>/__init__.py`
3. Decides bump magnitude:
   - `feat!:` or `BREAKING CHANGE:` → minor (pre-1.0.0) or major (post-1.0.0)
   - `feat:` or new public export → minor
   - `fix:` or no API change → patch
4. Updates `pyproject.toml` + prepends to `CHANGELOG.md`
5. Commits `chore: bump version to X.Y.Z [skip ci]` → pushes to same branch
6. Dispatches `version-updated` to PM → PM updates `workspace-manifest.json`

**Pre-1.0.0 rule:** breaking changes bump MINOR (never auto-cross to 1.0.0). 1.0.0 is set manually.

---

## PM Manifest as Remote SSOT

`workspace-manifest.json` on `origin/main` is the source of truth for all service versions.

**Before quickmerging to staging or main:**

1. Pull latest PM: `cd unified-trading-pm && git pull --ff-only`
2. Run alignment: `bash unified-trading-pm/scripts/repo-management/run-version-alignment.sh --fix`
3. If constraints are unsatisfiable (e.g. `>=1.1.5,<1.0.0`): fix-internal-dependency-alignment.py now uses
   `<{next_major}.0.0` as upper bound — re-run alignment after updating PM.

**Exception:** PM repo itself — when quickmerging PM, the manifest on the current branch is the SSOT. No external
manifest check is needed.

---

## Autonomous Agent GHA Flow

After a PR merges to `main` in any service repo:

```
push to main
  → quality-gates.yml (required status check)
  → plan-alignment-agent.yml (advisory PR comment — never blocks)
  → semver-agent.yml
      claude-haiku reads commit message + API diff
      → bumps pyproject.toml + CHANGELOG
      → pushes chore: bump version [skip ci] to main
      → dispatches version-updated to PM
  → PM: update-repo-version.yml receives dispatch
      → updates versions or staging_versions in workspace-manifest.json
      → dispatches dependency-update to downstream repos
  → each dependent: receives dep-update, creates PR updating its own pyproject.toml constraint
```

**Overnight orchestrator** (`overnight-agent-orchestrator.yml`, cron `0 1 * * *`):

- Dispatches `agent-audit.yml` per repo in T0→T1→T2→T3 tier order
- Each tier waits for the previous tier to complete before starting
- Retries up to 3x on failure with prior failure context

---

## Circular Reference Resolution

PM plans and manifest versions are updated incrementally — not all at once at staging-to-main time.

**How it works:**

1. Service repo merges to `main` → semver-agent bumps version → dispatches to PM
2. PM receives `version-updated` dispatch → updates `workspace-manifest.json` → pushes to main
3. By the time `staging-to-main.yml` fires, PM manifest already reflects current versions from each service
4. PM does NOT need to batch-update all versions at promotion time — it's been receiving incremental updates

**Repo updates PM plans (future todo `repos-update-pm-plans-in-gha`):** Service `agent-audit.yml` will also update the
relevant PM plan todos (cloning PM sibling → updating plan status → pushing to current PM branch). This will eliminate
any remaining ordering dependency at staging time.

---

## References

| Doc                                                     | Purpose                                                                |
| ------------------------------------------------------- | ---------------------------------------------------------------------- |
| **This doc**                                            | Full CI/CD flow SSOT                                                   |
| `scripts/repo-management/README-ALIGNMENT-AND-SETUP.md` | Phase 1–2 detail                                                       |
| `docs/repo-management/sync-to-main-flow.md`             | Phase 3 detail                                                         |
| `scripts/manifest/README-DEPENDENCY-ALIGNMENT.md`       | Internal alignment                                                     |
| **Codex**                                               | `06-coding-standards/setup-standards.md`, `dependency-management.md`   |
| **Cursor rules**                                        | `dependency-alignment-and-setup-flow.mdc`, `always-use-quickmerge.mdc` |
