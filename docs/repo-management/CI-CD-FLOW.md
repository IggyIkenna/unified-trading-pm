# Full CI/CD Flow — SSOT

**SSOT:** This document. Single entry point for dependency alignment, setup, sync-to-main, and conflict resolution.

**Run from workspace root:** All scripts assume you run from the workspace root (parent of unified-trading-pm). cd there
first, then run any script.

Run scripts in this order. Do not skip steps when dependencies or code have changed.

---

## Workspace Lifecycle Overview

Two distinct entry points — do not conflate them:

### New Machine (run once)

```bash
mkdir -p ~/repos/unified-trading-system-repos
cd ~/repos/unified-trading-system-repos

# Self-contained — no prior clone required. Bootstrap clones PM first (Phase 0),
# then reads its manifest to clone everything else and set up the full workspace.
bash <(curl -fsSL https://raw.githubusercontent.com/IggyIkenna/unified-trading-pm/main/scripts/workspace/workspace-bootstrap.sh)

# Or if you already have PM cloned:
bash unified-trading-pm/scripts/workspace/workspace-bootstrap.sh

# Preserve existing repos (skip delete + re-clone — faster for incremental runs):
bash unified-trading-pm/scripts/workspace/workspace-bootstrap.sh --skip-fresh
```

```
Phase 0: Self-seed unified-trading-pm — clones it if missing; pulls origin/main if present.
Phase 1: System deps (Python 3.13, uv, rg, jq)
Phase 2: Fresh clone all repos from workspace-manifest.json
         Default: delete existing dirs + re-clone (clean state guaranteed)
         --skip-fresh: preserve existing dirs (incremental runs)
Phase 3: .venv-workspace via setup-workspace-venv.sh (ruff==0.15.0, basedpyright==1.38.2)
Phase 4: Per-repo setup.sh in topological order (T0 → T1 → T2 → T3)
Phase 5: Import smoke test across all Python repos
```

**No chicken-and-egg:** Phase 0 clones PM automatically. `workspace-manifest.json` in PM is the single source of truth
for repo list, tiers, and versions.

### Day-to-Day (after every version alignment)

```
run-version-alignment.sh --fix      # align pyproject.toml versions + manifest
  └── auto-calls sync-workspace-venv.sh   # refresh .venv-workspace editable installs

run-all-setup.sh --rollout-first    # propagate setup.sh + QG stubs + build infra (Dockerfile, cloudbuild, buildspec) + rebuild per-repo .venv

run-all-quality-gates.sh            # local e2e smoke test (all tiers, parallel within tier)
  └── --repo X / --repos "X Y"      # subset mode — skip alignment + setup checks
  └── --skip-typecheck               # skip basedpyright (fast iteration)
  └── --lint                         # lint only, skip tests (fastest)
  └── --test                         # tests + typecheck only, skip lint

→ if all pass → system-integration-tests → deployment
```

**Two venvs, two responsibilities:**

| venv               | Purpose                                       | PYTHON_CMD / BASEDPYRIGHT_CMD                                   | Rebuilt by                      |
| ------------------ | --------------------------------------------- | --------------------------------------------------------------- | ------------------------------- |
| `.venv-workspace`  | IDE IntelliSense; `RUFF_CMD` in QG only       | **Never** — workspace has extra packages that mask missing deps | `sync-workspace-venv.sh`        |
| `.venv` (per-repo) | QG Python, basedpyright, pytest — CI-faithful | **Always** used for type-checking and test execution            | `run-all-setup.sh` / `setup.sh` |

See `unified-trading-codex/06-coding-standards/quality-gates.md § Tool Version Pinning` for the full rationale.

---

## How Setup and Quality Gates Work for Every Repo

**setup.sh** — One canonical file from PM. It auto-detects repo type (Python vs UI) and branches internally: Python
repos get `uv lock`, venv, path deps; UI repos get `npm install`. No repo-specific customization needed; each repo has
its own `pyproject.toml` or `package.json`.

**quality-gates.sh** — A ~10-line config stub per repo (sets `SERVICE_NAME`/`PACKAGE_NAME`, `SOURCE_DIR`,
`MIN_COVERAGE`, `RUN_INTEGRATION`, `LOCAL_DEPS`) that sources the appropriate base script from PM:
`unified-trading-pm/scripts/quality-gates-base/base-{service,library,codex}.sh`. Gate logic lives only in those base
scripts — never in per-repo files. UI repos have a minimal TypeScript stub (npm typecheck, lint, smoketest).

To add or change a gate check: edit the PM base script. It applies instantly to all repos — no rollout needed. To change
the stub interface (new required variable): edit the codex scaffold template, run rollout, commit stubs.

**Rollout** — `run-all-setup.sh --rollout-first` runs three propagation scripts:

1. `rollout-quality-gates-unified.py` — copies `setup.sh`, `quality-gates.sh`, writes QG config stubs
2. `rollout-quickmerge.py` — copies `quickmerge.sh`
3. `rollout-ui-build-infra.py` — generates `Dockerfile`, `cloudbuild.yaml`, `buildspec.aws.yaml` for UI/batch/API repos

Run when `setup.sh` changes in PM, when the stub interface changes, when build infra templates change, or use
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

**Test-harness repos (e.g. `system-integration-tests`):** These repos use plain-string dep format in
`workspace-manifest.json` (e.g. `"unified-trading-library"` not `{"name": "unified-trading-library", "version": "..."}`)
and have no `pyproject.toml` editable deps pointing to internal services. This is intentional — SIT has zero Python
imports from services (codex SSOT constraint: `unified-trading-codex/05-infrastructure/sit-standards.md`). The alignment
scanner (`check-dependency-alignment.py`) silently skips plain-string manifest deps, so these repos will always report
`"aligned": true` regardless of changes to their `pyproject.toml`. No alignment action is needed or expected for them.

**Ref:** `scripts/repo-management/README-ALIGNMENT-AND-SETUP.md`, `scripts/manifest/README-DEPENDENCY-ALIGNMENT.md`

---

## Phase 2: Run Setup (venvs + uv.lock ↔ tomls)

Update VM venvs and uv.lock in every repo so they match pyproject.toml.

```bash
# Standard: run setup.sh in each repo
bash unified-trading-pm/scripts/repo-management/run-all-setup.sh

# First-time bootstrap or after setup.sh / stub interface changes: rollout first, then setup
bash unified-trading-pm/scripts/repo-management/run-all-setup.sh --rollout-first
```

Runs `scripts/setup.sh` per repo in topological order. `setup.sh` **always** runs `uv lock` (timestamp skip was removed
— sibling version bumps don't touch `pyproject.toml`, so timestamps are unreliable). With `--rollout-first`, propagates
`setup.sh` + QG config stubs from PM to all repos before running setup.

**After:** Commit and push any changed `pyproject.toml`, `uv.lock`, `workspace-manifest.json` so agents and CI get
identical deps.

**Ref:** `scripts/repo-management/README-ALIGNMENT-AND-SETUP.md`

---

## Phase 2b: Workspace Venv Sync

After Phase 2, refresh `.venv-workspace` so editable installs reflect updated dep versions. This is automatic when using
`--fix` — `run-version-alignment.sh --fix` calls `sync-workspace-venv.sh` at the end. For manual refresh:

```bash
bash unified-trading-pm/scripts/workspace/sync-workspace-venv.sh          # refresh (idempotent)
bash unified-trading-pm/scripts/workspace/sync-workspace-venv.sh --check  # verify only
bash unified-trading-pm/scripts/workspace/sync-workspace-venv.sh --force  # full recreate
```

**What it does:** Creates `.venv-workspace` if missing, installs pinned tools (`ruff==0.15.0`, `basedpyright==1.38.2`),
then reinstalls all repos from `workspace-manifest.json` as editable in topological order.

**What it does NOT do:** It does not rebuild per-repo `.venv`. That is Phase 2 (`run-all-setup.sh`).

**Ref:** `scripts/workspace/setup-workspace-venv.sh` (underlying implementation, also called by
`workspace-bootstrap.sh`)

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

## Build Order Assumptions

Cloud Build and the deployment pipeline assume the following:

- **Dependencies built first:** Library and interface dependencies must be built and pushed to Artifact Registry before
  any service that depends on them. The manifest defines the build order.
- **Manifest up to date:** `workspace-manifest.json` must reflect the current versions of all internal dependencies. Run
  `run-version-alignment.sh --fix` before building.
- **Validation before build:** Quality gates and validation run before the build step. A failed validation blocks the
  build.

## Mock Infrastructure & Emulator Setup

All CI tests run credential-free with `CLOUD_PROVIDER=local CLOUD_MOCK_MODE=true`. Protocol-faithful emulators replace
live GCP/AWS services. This section documents how to activate each layer.

### Environment Variables

| Variable                 | Default | Purpose                                                  |
| ------------------------ | ------- | -------------------------------------------------------- |
| `CLOUD_PROVIDER`         | `gcp`   | Set to `local` for credential-free CI                    |
| `CLOUD_MOCK_MODE`        | `false` | Set to `true` for in-memory mock providers               |
| `PUBSUB_EMULATOR_HOST`   | —       | `localhost:8085` — GCP Pub/Sub emulator                  |
| `STORAGE_EMULATOR_HOST`  | —       | `http://localhost:4443` — GCS emulator (fake-gcs-server) |
| `BIGQUERY_EMULATOR_HOST` | —       | `localhost:9050` — BigQuery emulator                     |

### GCP Emulators (Docker)

```bash
# Pub/Sub (google-cloud-pubsub SDK auto-detects PUBSUB_EMULATOR_HOST)
docker run -d -p 8085:8085 gcr.io/google.com/cloudsdktool/google-cloud-cli \
  gcloud beta emulators pubsub start --host-port=0.0.0.0:8085 --project=mock-project

# GCS — fake-gcs-server (supports bucket lifecycle, ACLs, signed URLs)
docker run -d -p 4443:4443 fsouza/fake-gcs-server:latest -scheme http -port 4443

# BigQuery emulator (known gap: window functions not fully supported)
docker run -d -p 9050:9050 ghcr.io/goccy/bigquery-emulator:latest \
  --project=mock-project --dataset=trading_analytics
```

Or start all at once via:

```bash
docker compose -f unified-trading-pm/docker/docker-compose.mock.yml --profile gcp-emulators up
```

### AWS Moto (No Docker Required)

AWS services are mocked at the SDK level using `moto`. No emulator process or credentials needed:

- Tests in `unified-cloud-interface/tests/integration/test_aws_mode.py` use `@mock_aws` decorator
- S3, Secrets Manager, SQS all covered (26 tests)

### Credential-Free CI Gate

The `network_block_plugin.py` pytest plugin blocks all socket connections at the OS level:

```bash
# Activate in CI to prove zero live network calls
CLOUD_PROVIDER=local CLOUD_MOCK_MODE=true pytest --block-network -m "not sandbox"
```

Tests that legitimately connect to local emulators use `@pytest.mark.allow_network`. Each opt-out emits a WARNING in CI
logs — the count should stay minimal and stable.

Plugin location: `unified-trading-pm/scripts/dev/network_block_plugin.py`

### Cassette Parity & Drift Detection

- **Parity test** (every commit): `cd unified-api-contracts && pytest tests/test_cassette_schema_parity.py` — validates
  all 74+ cassette YAMLs against UAC Pydantic models. 256 tests, zero network calls.
- **Drift detection** (nightly 02:00 UTC): `.github/workflows/cassette-drift-check.yml` re-records cassettes against
  real APIs and diffs against committed YAMLs. Schema-level diff only — creates GitHub issue + Telegram alert on drift.
  Alerting-only, not CI-blocking.

### Local Demo Mode

Start the full system locally (no credentials required):

```bash
bash unified-trading-pm/scripts/demo-mode.sh --seed --open-browser
# With GCP emulators:
bash unified-trading-pm/scripts/demo-mode.sh --seed --gcp-emulators --open-browser
```

This starts all T2/T3 services with `CLOUD_MOCK_MODE=true`, seeds fixture data, and opens the UI.

See `unified-trading-pm/docker/docker-compose.mock.yml` for the full service definition.

### Implementation Reference

Full hardening details: `unified-trading-pm/plans/archive/cicd_mock_hardening_2026_03_11.plan.md` (Plan #60)

## Quick Reference: Full Flow

### New machine (once)

| Step | Command                                                            | When                                                  |
| ---- | ------------------------------------------------------------------ | ----------------------------------------------------- |
| 0    | `git clone git@github.com:IggyIkenna/unified-trading-pm.git`       | Manual — PM is the seed; bootstrap reads its manifest |
| 1    | `bash unified-trading-pm/scripts/workspace/workspace-bootstrap.sh` | Fresh machine only                                    |

### Day-to-day (after any dep or code change)

| Step | Command                                                                      | When                                                                                                 |
| ---- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| 1    | `run-version-alignment.sh`                                                   | Always first when deps may have changed                                                              |
| 2    | `run-version-alignment.sh --fix`                                             | If step 1 reports misalignment (auto-calls `sync-workspace-venv.sh`)                                 |
| 3    | `run-all-setup.sh` (`--rollout-first` if setup.sh or stub interface changed) | After alignment OK — rebuilds per-repo `.venv`                                                       |
| 4    | Commit + push pyproject.toml, uv.lock, manifest                              | After run-all-setup                                                                                  |
| 5    | `run-all-quality-gates.sh`                                                   | Local e2e smoke test; use `--repo X` for subset; `--lint` / `--skip-typecheck` to speed up iteration |
| 6    | `sync-all-to-main.sh` (`--dep-branch NAME` if DEPENDENCY CONFLICT)           | When pushing to main                                                                                 |
| 7a   | If sync fails: merge conflict → resolve manually, re-run sync                | Per conflicted repo                                                                                  |
| 7b   | If sync fails: `run-all-quality-gates.sh --repo X` on conflicted repos       | Verify our version passes before fixing                                                              |

**If all pass → system-integration-tests → deployment**

---

## Deviation from Main

- **No deviation:** Repo is clean or matches origin/main → sync skips (OK, no changes).
- **Deviation:** Local has uncommitted or unpushed changes → sync runs quickmerge.
- **Unresolvable:** Merge conflict → sync FAILs, exits. Resolve manually, then re-run.

---

## Workspace Scripts (scripts/workspace/)

| Script                                | Purpose                                                                                                                                             | When it runs                                                                                                         |
| ------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| **workspace-bootstrap.sh**            | New machine setup: system deps, clone all repos from manifest, workspace venv (via setup-workspace-venv.sh), per-repo setup, smoke test.            | Once, on fresh machine.                                                                                              |
| **sync-workspace-venv.sh**            | Day-to-day `.venv-workspace` refresh: pinned tools + editable installs from manifest. Thin wrapper over `setup-workspace-venv.sh`.                  | Auto-called by `run-version-alignment.sh --fix`. Run manually after `git pull` on PM.                                |
| **setup-workspace-venv.sh**           | Underlying venv setup logic: creates venv, installs `ruff==0.15.0` + `basedpyright==1.38.2`, installs all repos as editable in topo order.          | Called by both `workspace-bootstrap.sh` (Phase 3) and `sync-workspace-venv.sh`. Single source of truth.              |
| **validate-workspace-constraints.py** | Validates `workspace-constraints.toml` resolves without dependency conflicts (runs `uv pip compile`). Caches result by file hash.                   | Called by `validate-dependency-conflicts.py` during Phase 1 (step 4 of run-version-alignment.sh).                    |
| **resolve-canonical-versions.py**     | Derives `workspace-constraints.toml` from all repo `pyproject.toml` files (topological order). Picks tightest constraint per package.               | **Not** called by `--fix`. Called only by `validate-dependency-conflicts.py --regenerate` when constraints conflict. |
| **aggregate-workspace-deps.py**       | Legacy: installs all repo deps into `.venv-workspace` using `workspace-constraints.toml`. Superseded by `setup-workspace-venv.sh` for standard use. | Only if explicitly needed for constraint-based resolution outside the standard flow.                                 |

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

| Failure                     | Fix                                                                                                                                                                                                                                                             |
| --------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Prettier (pre-commit)**   | Quickmerge auto-runs Prettier before commit. If it still fails, run `npx prettier --write .` in the repo, then re-run quickmerge.                                                                                                                               |
| **Act simulation (GH_PAT)** | Quickmerge **fails** (does not skip) when act fails. SSOT: unified-trading-pm/docs/repo-management/act-secrets-setup.md. Run generate-act-secrets.sh, edit .act-secrets, add GH_PAT.                                                                            |
| **Type check fails**        | Each repo owns `[tool.basedpyright]` in its `pyproject.toml` — that is the CI type-check config. The workspace-root `pyrightconfig.json` is an IDE-only helper (not used by CI or QG scripts). Ensure `bash scripts/setup.sh` ran so the repo's `.venv` exists. |

## Feature Branch Flow

Use a feature branch when you have local changes in dependency repos that haven't been pushed to main yet.

```bash
# Standard: direct to main (no local dep changes)
bash unified-trading-pm/scripts/quickmerge.sh "feat: my change"

# Feature branch: local dep changes present
bash unified-trading-pm/scripts/quickmerge.sh "feat: my change" --dep-branch feat/my-feature

# Agent / Claude Code sessions — always pass --agent (skips act simulation + tests; lint+format+typecheck+codex only)
bash unified-trading-pm/scripts/quickmerge.sh "feat: my change" --agent
```

**Two-pass model (REQUIRED for all code changes):**

- **Pass 1** — `bash scripts/quality-gates.sh` — full run (lint, tests, typecheck, codex, security). Cannot be skipped.
- **Pass 2** — `bash scripts/quickmerge.sh "msg" --agent` — lightweight (lint+format+typecheck+codex, no tests, no act).
  Only run after Pass 1 is green.

`--agent` is **required** in all Claude Code / GHA agent sessions. `--quick` skips act only (tests still run) and is the
human shorthand for interactive use. Never use quickmerge as a substitute for Pass 1 — it does not run the full test
suite. SSOT: `unified-trading-codex/06-coding-standards/quality-gates.md § Two-Pass Workflow Model`.

**What `--dep-branch feat/my-feature` does (STAGE 0 — Cascade):**

1. Reads `workspace-manifest.json` to find all transitive ancestors of the current repo (full DAG walk upward)
2. For each ancestor that exists locally: stashes local changes, creates/switches to `feat/my-feature` branch, pops
   stash
3. Only ancestors are touched — siblings and unrelated repos are left alone
4. Then proceeds with normal quickmerge stages (Stage 1: dependency validation now passes because deps are on the same
   branch)

**Version bump rules on feature branches:**

- `semver-agent.yml` and the disabled `version-bump.yml` only fire on `staging` — never on `feat/*` or `main`
- `pyproject.toml` versions are **never** bumped on feature branches or at main merge
- Version bumping happens exactly once: when the PR from `feat/*` merges to `staging`

**Flow:**

```
feat/my-feature branch
  → quickmerge --to-staging (--dep-branch feat/my-feature)
    → STAGE 0: dep alignment check (check-dep-alignment.py — staging or main reference)
    → STAGE 1-5: QG + PR to staging (GitHub auto-merge queue holds if staging locked)
  → PR auto-merges to staging
  → semver-agent.yml fires on staging push
    → Claude-Haiku reads commit + API diff → decides patch/minor/major
    → bumps pyproject.toml on staging
    → dispatches version-bump to PM → PM updates staging_versions + staging_commits
    → cascade dispatches to dependents
  → SIT runs (10-min quiet debounce) → staging-to-main.yml on pass
    → promotes staging_versions → versions (no re-bump on main)
    → main merge commit uses [skip ci] — semver-agent does NOT re-run
```

---

## Version Bump Rules (Semver-Agent Only)

`semver-agent.yml` is the **sole owner** of version bumping. `version-bump.yml` is disabled (`if: false`).

**When it fires:** push to `staging` only (never on `feat/*` or `main`). Version is decided once at staging merge. Main
merge uses `[skip ci]` — no re-bump.

**What it does:**

1. Reads current version from `pyproject.toml`
2. Reads merge commit message + `git diff HEAD~1 -- <source_dir>/__init__.py`
3. Decides bump magnitude:
   - `feat!:` or `BREAKING CHANGE:` → minor (pre-1.0.0) or major (post-1.0.0)
   - `feat:` or new public export → minor
   - `fix:` or no API change → patch
4. Updates `pyproject.toml` + prepends to `CHANGELOG.md`
5. Commits `chore: bump version to X.Y.Z [skip ci]` → pushes to staging
6. Dispatches `version-bump` to PM with `{ repo, version, branch: "staging", commit_sha }` → PM updates
   `staging_versions[repo]` and `staging_commits[repo]`

**Pre-1.0.0 rule:** breaking changes bump MINOR (never auto-cross to 1.0.0). 1.0.0 is set manually.

**Manifest fields:**

| Field                    | When set                                        | What it means                                             |
| ------------------------ | ----------------------------------------------- | --------------------------------------------------------- |
| `staging_versions[repo]` | After semver-agent fires on staging push        | In-flight version, not yet SIT-validated                  |
| `versions[repo]`         | After SIT passes + staging-to-main.yml promotes | Stable version on main                                    |
| `staging_commits[repo]`  | Written alongside staging_versions              | Exact commit SHA under test in current SIT run            |
| `main_commits.history`   | After each SIT pass                             | Rolling last 5 promoted staging sets (rollback reference) |

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

After a PR merges to `staging` in any service repo:

```
push to staging
  → quality-gates.yml (required status check) → dispatches qg-passed to PM
  → plan-alignment-agent.yml (advisory PR comment — never blocks)
  → semver-agent.yml (fires on staging push only)
      claude-haiku reads commit message + API diff
      → bumps pyproject.toml + CHANGELOG on staging
      → pushes chore: bump version [skip ci] to staging
      → dispatches version-bump to PM (payload: repo, version, branch=staging, commit_sha)
  → PM: update-repo-version.yml receives dispatch
      → updates staging_versions[repo] = version
      → updates staging_commits[repo] = commit_sha
      → dispatches dependency-update to downstream repos
  → each dependent: receives dep-update, creates PR updating its own pyproject.toml constraint
  → PM: cloud-build-router.yml receives qg-passed dispatch
      → routes to uts-staging-ikenna Cloud Build
      → builds Docker image tagged {semver}-staging
      → updates deployed_versions.staging in manifest

After SIT passes → staging-to-main.yml:
  → promotes staging_versions → versions (no re-bump)
  → appends staging_commits to main_commits.history (keep last 5)
  → clears staging_commits + staging_status.locked
  → merges staging → main with [skip ci] commit message (semver-agent does NOT re-run)
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

## Staging Lock Lifecycle

SIT owns the staging lock. The lock is set when SIT **starts** (not when a major bump happens). Unlock on either pass or
fail so engineers can push fixes without waiting.

```
feat/* passes QG → quickmerge --to-staging → PR to staging (GitHub auto-merge queue)

GitHub auto-merge queue: staging-gate check
  PASS    if staging_status.locked == false
  PENDING if staging_status.locked == true  ← PRs queue here during SIT

SIT debounce (GHA concurrency group, 10-min quiet):
  staging push → triggers smoke-test-gate.yml
  concurrency group (cancel-in-progress: true) cancels prior run if new push arrives within 10 min
  after 10-min quiet → job proceeds (batch covers all repos pushed in that window)

SIT START:
  → reads staging_commits from PM manifest (exact SHA set)
  → dispatches sit-lock to PM (payload: { commit_shas: {...} })
  → PM's sit-gate.yml: sets locked=true, locked_since=utcnow(), locked_reason="SIT running"
  → SIT clones each repo at its staging_commits[repo] SHA — not latest HEAD

SIT PASS:
  → dispatches staging-validated to PM
  → staging-to-main.yml:
      appends staging_commits to main_commits.history (keep last 5)
      promotes staging_versions → versions
      clears staging_commits, staging_status.locked=false

SIT FAIL:
  → dispatches sit-failed to PM
  → sit-unlock.yml: sets locked=false, reason="SIT failed — open for fixes"
  → Queued PRs to staging can now merge (gate passes again)
  → Engineers push fix to feat/* → quickmerge --to-staging → new SIT run
```

**Workflows involved:**

| Workflow                    | Trigger                      | Action                                       |
| --------------------------- | ---------------------------- | -------------------------------------------- |
| `sit-gate.yml` (PM)         | `sit-lock` dispatch          | Sets lock + records staging_commits SHAs     |
| `sit-unlock.yml` (PM)       | `sit-failed` dispatch        | Clears lock, reason = "SIT failed"           |
| `staging-to-main.yml` (PM)  | `staging-validated` dispatch | Promotes versions + clears lock on pass      |
| `smoke-test-gate.yml` (SIT) | push to staging              | Debounce → lock → run tests → unlock/promote |

**quickmerge --to-staging behavior when locked:** Informs the user that staging is locked and PR creation will proceed.
GitHub's auto-merge queue holds the PR until the lock clears. Does not abort.

---

## SIT Batching

Multiple `feat/*` PRs merging to staging within 10 minutes form a **batch** — a single SIT run covers the full batch.

**How it works:**

- `smoke-test-gate.yml` has a GHA concurrency group:
  ```yaml
  concurrency:
    group: sit-staging
    cancel-in-progress: true
  ```
- The job sleeps 600s at start. If a new staging push arrives within 10 min, the prior run is cancelled and a new run
  starts (resetting the clock).
- After 10-min quiet, the job proceeds and tests ALL repos currently on staging — not just the last-pushed one.
- SIT reads `staging_commits` from the PM manifest to get the exact SHA set to test.

**Result:** Two repos pushed to staging 3 min apart → one SIT run covering both. No partial-set testing.

---

## Dependency Reference Rules

When checking if a repo's direct deps are aligned before a push or quickmerge, the reference branch depends on context:

```
for each direct dep:
    if dep is in manifest.staging_versions AND (push target is staging OR --to-staging flag):
        compare to origin/staging
    else:
        compare to origin/main
```

**Why:** When a library is promoted to staging but not yet merged to main, its `pyproject.toml` on `origin/main` still
shows the old version. Checking against `origin/staging` avoids a chicken-and-egg block where valid staging work is
refused because its dep hasn't been promoted to main yet.

**Enforcement points:**

1. **quickmerge Stage 0** — `check-dep-alignment.py` runs before cascade; exits 1 if misaligned
2. **git pre-push hook** — same check, fires on `git push origin staging` only; no-op for `feat/*`
3. **Script:**
   `scripts/repo-management/check-dep-alignment.py --repo <name> --to-staging <true|false> --manifest <path>`
4. **Hook source:** `scripts/hooks/pre-push` (installed to all repos by `scripts/workspace/install-hooks.sh`)

---

## Multi-Project Cloud Build

Three isolated GCP projects — one per environment. Build triggered by QG pass (not raw push).

### Routing Table

| Branch    | GCP Project          | Image Tag Format         |
| --------- | -------------------- | ------------------------ |
| `feat/*`  | `uts-dev-ikenna`     | `{semver}-{branch-slug}` |
| `staging` | `uts-staging-ikenna` | `{semver}-staging`       |
| `main`    | `uts-prod-ikenna`    | `{semver}`               |

### Trigger Flow

```
QG passes in any repo
  → quality-gates.yml dispatches qg-passed to PM
      payload: { repo, branch, commit_sha, version, repo_type }
  → PM: cloud-build-router.yml receives dispatch
      → determines GCP project + image tag from branch
      → authenticates with env-specific SA key (GCP_SA_KEY_DEV / _STAGING / _PROD)
      → triggers Cloud Build in the correct project
```

### Artifact Types

- **Library repos** (`repo_type == "library"`) → Python wheel build (not Docker). Wheel pushed to Artifact Registry.
- **Service/API/UI repos** → Docker image build. Image pushed to AR with immutable tag.

### Image Tag Immutability

**Tags are never overwritten.** To fix a bad image at the same semver, bump the version first (creates a new tag).

### uv.lock Frozen

All service Dockerfiles use `uv sync --frozen --no-dev`. `uv.lock` is the reproducibility SSOT. `pyproject.toml`
`>=X.Y.Z` ranges are API compatibility contracts — never pinned in pyproject.toml (let uv.lock handle it).

```dockerfile
RUN uv sync --frozen --no-dev
```

### Terraform

GCP project provisioning: `unified-trading-pm/terraform/environments/{dev,staging,prod}/main.tf`

Each environment creates: `google_project_service` (cloudbuild, artifactregistry, run, secretmanager), AR repository
`unified-trading`, Cloud Build SA with AR Writer + Cloud Run Developer + Secret Manager Accessor IAM roles.

GitHub secrets required: `GCP_SA_KEY_DEV`, `GCP_SA_KEY_STAGING`, `GCP_SA_KEY_PROD`.

---

## Rollback

Images are kept indefinitely in staging and prod Artifact Registry. Dev AR has a 90-day lifecycle cleanup policy.

**Rollback procedure:**

```bash
# Via deployment-api
POST /deployments/{service}/rollback
Body: { "image_tag": "0.3.165", "environment": "prod" }
```

This triggers `gcloud run deploy --image {ar_host}/{project}/{repo}/{service}:{tag}` and updates
`deployed_versions.prod.{repo}` in the PM manifest.

**Finding known-good tags:** `main_commits.history` in `workspace-manifest.json` contains the last 5 staging sets
promoted to main — each entry has the exact `commit_shas` and the tag formula produces the known-good image tag.

**Deployment UI (Phase 7 — future):** Will expose a version dropdown per service per environment, reading
`deployed_versions` + AR tag list, with a "Last known good" shortcut from `main_commits.history[0]`.

---

## References

| Doc                                                     | Purpose                                                                |
| ------------------------------------------------------- | ---------------------------------------------------------------------- |
| **This doc**                                            | Full CI/CD flow SSOT                                                   |
| `scripts/repo-management/README-ALIGNMENT-AND-SETUP.md` | Phase 1–2 detail                                                       |
| `docs/repo-management/sync-to-main-flow.md`             | Phase 3 detail                                                         |
| `scripts/manifest/README-DEPENDENCY-ALIGNMENT.md`       | Internal alignment                                                     |
| `scripts/repo-management/check-dep-alignment.py`        | Dep reconciliation gate (Phase 4)                                      |
| `scripts/hooks/pre-push`                                | Git pre-push hook for dep check on staging pushes                      |
| `.github/workflows/sit-gate.yml`                        | Sets staging lock at SIT start                                         |
| `.github/workflows/sit-unlock.yml`                      | Clears staging lock on SIT failure                                     |
| `.github/workflows/cloud-build-router.yml`              | Routes qg-passed to correct GCP Cloud Build project                    |
| `terraform/environments/`                               | GCP project provisioning (dev/staging/prod)                            |
| **Codex**                                               | `06-coding-standards/setup-standards.md`, `dependency-management.md`   |
| **Cursor rules**                                        | `dependency-alignment-and-setup-flow.mdc`, `always-use-quickmerge.mdc` |
