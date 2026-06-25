---
scope: [engineer, admin]
last_reviewed: 2026-06-25
---

# Workspace Setup

> **CI/CD pipeline SSOT:** `codex/08-workflows/ci-cd-flow.md`. This doc covers the **workspace bootstrap, venv
> management, dependency alignment, quality-gate mechanics, and mock-infrastructure setup** — the parts not covered by
> the CI/CD flow codex.

---

## Linux Prerequisites (before bootstrap)

On Linux with pyenv, add these to `~/.bashrc` **before** running the bootstrap. Without them `uv` auto-downloads its
own CPython into `~/.local/share/uv/python/`; all 50+ venvs point to that cache, and when the cache is cleaned every
venv breaks simultaneously. The pyenv-virtualenv hook also silently wipes `VIRTUAL_ENV` on every prompt if the global
pyenv version does not exist on disk.

```bash
# ~/.bashrc additions (Linux + pyenv)
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PYENV_ROOT/shims:$PATH"
eval "$(pyenv init -)"
# eval "$(pyenv virtualenv-init -)"   # only if you use pyenv-virtualenv

# Force uv to use pyenv Python — never auto-download its own CPython
export UV_PYTHON="$PYENV_ROOT/versions/3.13.9/bin/python3.13"
export UV_PYTHON_PREFERENCE=system    # resolve version specs via PATH/pyenv shims
export UV_PYTHON_DOWNLOADS=never      # hard-block uv from downloading CPython

export PYENV_VIRTUALENV_DISABLE_PROMPT=1
```

After editing: `source ~/.bashrc && pyenv install 3.13.9 && pyenv global 3.13.9 && pyenv rehash`

Not needed on macOS — Homebrew Python is on PATH and uv respects it.

---

## New Machine (run once)

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

Bootstrap phases:
```
Phase 0: Self-seed unified-trading-pm (clones if missing; pulls origin/main if present)
Phase 1: System deps (Python 3.13, uv, rg, jq)
Phase 2: Fresh clone all repos from workspace-manifest.json
         Default: delete existing dirs + re-clone (clean state guaranteed)
         --skip-fresh: preserve existing dirs (incremental runs)
Phase 3: .venv-workspace via setup-workspace-venv.sh (ruff==0.15.0, basedpyright==1.38.2)
Phase 4: Per-repo setup.sh in topological order (T0 → T1 → T2 → T3)
Phase 5: Import smoke test across all Python repos
```

`workspace-manifest.json` in PM is the single source of truth for repo list, tiers, and versions.

---

## Day-to-Day (after any dep or code change)

```
run-version-alignment.sh --fix      # align pyproject.toml versions + manifest
  └── auto-calls sync-workspace-venv.sh   # refresh .venv-workspace editable installs

run-all-setup.sh --rollout-first    # propagate setup.sh + QG stubs + build infra (Dockerfile, cloudbuild, buildspec) + rebuild per-repo .venv

run-all-quality-gates.sh            # local e2e smoke test (all tiers, parallel within tier)
  └── --repo X / --repos "X Y"      # subset mode
  └── --skip-typecheck               # fast iteration
  └── --lint                         # lint only
  └── --test                         # tests + typecheck only, skip lint
```

**Shipping code:** Pass 1 = `bash scripts/quality-gates.sh` (full gate). Pass 2 = `bash scripts/quickmerge.sh "msg"
--agent --files <paths>` (pushes to `live-defi-rollout`; Tier-C bot drains LDR→staging every 15 min).
SSOT: `codex/08-workflows/ci-cd-flow.md § Two-Pass Workflow Model`.

**Two venvs, two responsibilities:**

| venv               | Purpose                                        | Rebuilt by                                |
|--------------------|------------------------------------------------|-------------------------------------------|
| `.venv-workspace`  | IDE IntelliSense; `RUFF_CMD` in QG only        | `sync-workspace-venv.sh`                  |
| `.venv` (per-repo) | QG Python, basedpyright, pytest — CI-faithful  | `run-all-setup.sh` / `setup.sh`           |

Never run pytest directly against `.venv-workspace` — the workspace venv has extra packages that mask missing deps.
See `codex/06-coding-standards/quality-gates.md § Tool Version Pinning` for full rationale.

---

## How Setup and Quality Gates Work

**setup.sh** — One canonical file from PM. Auto-detects repo type (Python vs UI) and branches internally: Python repos
get `uv lock`, venv, path deps; UI repos get `npm install`. No repo-specific customization needed.

**quality-gates.sh** — A ~10-line config stub per repo (sets `SERVICE_NAME`/`PACKAGE_NAME`, `SOURCE_DIR`,
`MIN_COVERAGE`, `RUN_INTEGRATION`, `LOCAL_DEPS`) that sources the appropriate base script from PM:
`unified-trading-pm/scripts/quality-gates-base/base-{service,library,codex}.sh`. Gate logic lives only in those base
scripts — never in per-repo files.

To add or change a gate check: edit the PM base script (applies instantly to all repos — no rollout needed). To change
the stub interface (new required variable): edit the codex scaffold template, run rollout, commit stubs.

**Rollout** — `run-all-setup.sh --rollout-first` runs three propagation scripts:
1. `rollout-quality-gates-unified.py` — copies `setup.sh`, `quality-gates.sh`, writes QG config stubs
2. `rollout-quickmerge.py` — copies `quickmerge.sh`
3. `rollout-ui-build-infra.py` — generates `Dockerfile`, `cloudbuild.yaml`, `buildspec.aws.yaml`

Run when `setup.sh` changes in PM, when the stub interface changes, or use `--rollout-first` on first bootstrap.

---

## Phase 1: Dependency Alignment (manifest ↔ pyproject.toml)

```bash
cd /path/to/unified-trading-system-repos

# 1. Check alignment
bash unified-trading-pm/scripts/repo-management/run-version-alignment.sh

# 2. If misaligned, fix (tier-aware; tier violations are flagged, not auto-fixed)
bash unified-trading-pm/scripts/repo-management/run-version-alignment.sh --fix

# 3. Re-check until clean
bash unified-trading-pm/scripts/repo-management/run-version-alignment.sh
```

**Unresolvable:** Tier violations and constraint conflicts are reported and exit 1. Resolve manually before proceeding.

**Test-harness repos (e.g. `system-integration-tests`):** Use plain-string dep format in `workspace-manifest.json` and
have no `pyproject.toml` editable deps. The alignment scanner silently skips plain-string manifest deps → always
reports `"aligned": true`. No alignment action needed.

**Ref:** `scripts/repo-management/README-ALIGNMENT-AND-SETUP.md`, `scripts/manifest/README-DEPENDENCY-ALIGNMENT.md`

---

## Phase 2: Run Setup (venvs + uv.lock ↔ tomls)

```bash
# Standard: run setup.sh in each repo
bash unified-trading-pm/scripts/repo-management/run-all-setup.sh

# First-time or after setup.sh / stub interface changes: rollout first. --force for hard reinstall.
bash unified-trading-pm/scripts/repo-management/run-all-setup.sh --rollout-first --force
```

Runs `scripts/setup.sh` per repo in topological order. `setup.sh` always runs `uv lock` (timestamp skip was removed
— sibling version bumps don't touch `pyproject.toml`, so timestamps are unreliable). With `--rollout-first`,
propagates `setup.sh` + QG stubs from PM before running setup.

After: commit and push any changed `pyproject.toml`, `uv.lock`, `workspace-manifest.json` so agents and CI get
identical deps.

---

## Phase 2b: Workspace Venv Sync

After Phase 2, refresh `.venv-workspace` so editable installs reflect updated dep versions. Automatic when using
`--fix` — `run-version-alignment.sh --fix` calls `sync-workspace-venv.sh` at the end. For manual refresh:

```bash
bash unified-trading-pm/scripts/workspace/sync-workspace-venv.sh          # refresh (idempotent)
bash unified-trading-pm/scripts/workspace/sync-workspace-venv.sh --check  # verify only
bash unified-trading-pm/scripts/workspace/sync-workspace-venv.sh --force  # full recreate
```

Creates `.venv-workspace` if missing, installs pinned tools (`ruff==0.15.0`, `basedpyright==1.38.2`), then reinstalls
all repos from `workspace-manifest.json` as editable in topological order. Does NOT rebuild per-repo `.venv`
(that is Phase 2).

---

## Build Order Assumptions

Cloud Build and the deployment pipeline assume:
- **Dependencies built first:** Library and interface dependencies must be built and pushed to Artifact Registry before
  any service that depends on them. The manifest defines the build order.
- **Manifest up to date:** `workspace-manifest.json` must reflect current versions of all internal dependencies. Run
  `run-version-alignment.sh --fix` before building.
- **Validation before build:** Quality gates and validation run before the build step. A failed validation blocks the
  build.

---

## Mock Infrastructure & Emulator Setup

All CI tests run credential-free with `CLOUD_PROVIDER=local CLOUD_MOCK_MODE=true`. Protocol-faithful emulators replace
live GCP/AWS services.

### Environment Variables

| Variable                 | Default | Purpose                                                   |
|--------------------------|---------|-----------------------------------------------------------|
| `CLOUD_PROVIDER`         | `gcp`   | Set to `local` for credential-free CI                     |
| `CLOUD_MOCK_MODE`        | `false` | Set to `true` for in-memory mock providers                |
| `PUBSUB_EMULATOR_HOST`   | —       | `localhost:8085` — GCP Pub/Sub emulator                   |
| `STORAGE_EMULATOR_HOST`  | —       | `http://localhost:4443` — GCS emulator (fake-gcs-server)  |
| `BIGQUERY_EMULATOR_HOST` | —       | `localhost:9050` — BigQuery emulator                      |

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

Or start all at once:

```bash
docker compose -f unified-trading-pm/docker/docker-compose.mock.yml --profile gcp-emulators up
```

### AWS Moto (No Docker Required)

AWS services are mocked at the SDK level using `moto`. No emulator process or credentials needed:
- Tests in `unified-cloud-interface/tests/integration/test_aws_mode.py` use `@mock_aws` decorator
- S3, Secrets Manager, SQS all covered (26 tests)

### Credential-Free CI Gate

```bash
CLOUD_PROVIDER=local CLOUD_MOCK_MODE=true pytest --block-network -m "not sandbox"
```

The `network_block_plugin.py` pytest plugin blocks all socket connections at the OS level. Tests that legitimately
connect to local emulators use `@pytest.mark.allow_network`. Each opt-out emits a WARNING in CI logs — the count
should stay minimal and stable.

Plugin location: `unified-trading-pm/scripts/dev/network_block_plugin.py`

### Cassette Parity & Drift Detection

- **Parity test** (every commit): `cd unified-api-contracts && pytest tests/test_cassette_schema_parity.py` —
  validates all 74+ cassette YAMLs against UAC Pydantic models. 256 tests, zero network calls.
- **Drift detection** (nightly 02:00 UTC): `.github/workflows/cassette-drift-check.yml` re-records cassettes against
  real APIs and diffs against committed YAMLs. Schema-level diff only — creates GitHub issue + Slack alert on drift.
  Alerting-only, not CI-blocking.

### Local Demo Mode

```bash
bash unified-trading-pm/scripts/demo-mode.sh --seed --open-browser
# With GCP emulators:
bash unified-trading-pm/scripts/demo-mode.sh --seed --gcp-emulators --open-browser
```

Starts all T2/T3 services with `CLOUD_MOCK_MODE=true`, seeds fixture data, and opens the UI.

---

## Workspace Scripts (`scripts/workspace/`)

| Script                                | Purpose                                                                                                    |
|---------------------------------------|------------------------------------------------------------------------------------------------------------|
| **workspace-bootstrap.sh**            | New machine setup: system deps, clone all repos from manifest, workspace venv, per-repo setup, smoke test. |
| **sync-workspace-venv.sh**            | Day-to-day `.venv-workspace` refresh: pinned tools + editable installs. Thin wrapper over setup-workspace-venv.sh. |
| **setup-workspace-venv.sh**           | Underlying venv setup logic: creates venv, installs ruff+basedpyright, installs all repos as editable.     |
| **validate-workspace-constraints.py** | Validates `workspace-constraints.toml` resolves without conflicts (runs `uv pip compile`). Hash-cached.    |
| **resolve-canonical-versions.py**     | Derives `workspace-constraints.toml` from all repo `pyproject.toml` files. Called only by `--regenerate`. |
| **sync-gitignore-cursorignore.py**    | Writes `.gitignore` + `.cursorignore` to every repo from PM central templates. Calls `untrack-ignored-files.py`. |
| **untrack-ignored-files.py**          | Removes newly-ignored files from git index. `--dry-run`: report only. `--untrack`: apply.                  |

---

## Gitignore Sync & Untrack

Central `.gitignore` and `.cursorignore` templates live in `unified-trading-pm/scripts/templates/`.

```bash
# Sync .gitignore + .cursorignore to all repos, then untrack newly-ignored files
python3 unified-trading-pm/scripts/workspace/sync-gitignore-cursorignore.py
```

1. Reads `scripts/templates/.gitignore.central` and `.cursorignore.central` from PM.
2. Writes `.gitignore` and `.cursorignore` to every workspace repo. Per-repo exception blocks are preserved across
   re-syncs.
3. Calls `untrack-ignored-files.py --untrack` — removes newly-ignored files from git index.

To add patterns that only apply to one repo, edit that repo's `.gitignore` under:
```
# --- Repo-specific exceptions (add below; sync preserves this section) ---
!tests/fixtures/*.csv
```

**Dry-run:** `python3 unified-trading-pm/scripts/workspace/untrack-ignored-files.py --dry-run`

After running: commit the changed `.gitignore` files and any `git rm --cached` removals in each affected repo, then
push via quickmerge.

---

## Pre-Commit Standardization

4 canonical pre-commit templates in PM, rolled out to all repos:

| Template         | Repos             | Hooks                                                |
|------------------|-------------------|------------------------------------------------------|
| `python-service` | T4+ services/APIs | branch-drift, ruff check, ruff format, basedpyright  |
| `python-library` | T0-T3 libraries   | branch-drift, ruff check, ruff format, basedpyright  |
| `ui`             | UI repos          | branch-drift, eslint, prettier                       |
| `docs`           | PM, codex         | branch-drift, prettier                               |

All templates include `check-branch-drift.sh` which blocks commits if local branch is behind origin.

Rollout: `bash unified-trading-pm/scripts/propagation/rollout-pre-commit-configs.sh`

---

## qg-common.sh Shared Foundation

74-line shared foundation file (`unified-trading-pm/scripts/quality-gates-base/qg-common.sh`) sourced by all 4 base
QG scripts. Provides:
- Color constants + `log_info`/`log_warn`/`log_error`/`log_pass`/`log_fail` functions
- `run_timeout` wrapper
- ci-status update function (writes to manifest with `fcntl.flock`)
- Version alignment gate sourcing

No per-repo setup needed — base scripts source it automatically.

---

## YAML Syntax Validation

All YAML files are validated before any commit reaches remote.

| Tool                     | What it checks                                                   | Location                                    |
|--------------------------|------------------------------------------------------------------|---------------------------------------------|
| `actionlint`             | `.github/workflows/*.yml` syntax, action refs, expression types  | Cached binary in quality-gates.yml          |
| `yamllint`               | Generic YAML structure in all `.yml` files                       | `base-service.sh`                           |
| `validate-cloudbuild.py` | `cloudbuild.yaml` Cloud Build syntax + substitution vars         | `scripts/validation/validate-cloudbuild.py` |
| `validate-buildspec.py`  | `buildspec.aws.yaml` CodeBuild syntax + phases/artifacts         | `scripts/validation/validate-buildspec.py`  |

Validation runs before `git push` (pre-push hook) and inside `quality-gates.sh --no-fix` in CI. Any YAML syntax
error blocks the PR from passing `quality-gates-v2`.

---

## Background Agent Cursor Rules Inheritance

### Persistent (committed to all repos)

| File                | Symlink target                                       | Purpose                                              |
|---------------------|------------------------------------------------------|------------------------------------------------------|
| `.claude/CLAUDE.md` | `../../unified-trading-pm/cursor-configs/CLAUDE.md`  | Claude Code workspace instructions                   |
| `AGENTS.md`         | `../unified-trading-pm/AGENTS.md`                    | Workspace-generic agent instructions                 |

Rollout: `scripts/rollout-agent-symlinks.sh`

### Ephemeral (setup at GHA runtime)

Cursor rules are not committed to repos (they clutter Cursor IDE). At GHA runtime:
```bash
# setup-workspace-from-manifest.sh copies rules:
cp unified-trading-pm/cursor-rules/*.mdc $WORKSPACE_ROOT/.cursor/rules/
```

**MANDATORY:** `.cleanup-cursor-rules.sh` must run **before quickmerge** to prevent cursor rules from being committed.

### Sub-Agent Rule Inheritance

Every sub-agent invocation must include:
1. Full paste of `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` at the top of the prompt, OR
2. `"Before any action, read unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md and follow ALL rules strictly."`

Always pass `WORKSPACE_ROOT` path explicitly. For tests: `cd <repo> && bash scripts/quality-gates.sh`.

---

## Version Alignment Gate (3 Layers)

**Layer 1 — Pre-commit (`check-branch-drift.sh`):** Blocks commit if local branch is behind origin. Instant.
Override: `SKIP_BRANCH_DRIFT=1` (human-only).

**Layer 2 — Quality gates (`version-alignment-gate.sh`):** Checks self version + dependency versions vs remote PM
manifest. ~3s overhead. Blocks QG if drift detected. Override: `--skip-version-alignment` (human-only).

**Layer 3 — Admin force-sync:** Reads all repos' versions from remote PM manifest. Blocks if remote has bumps your
local manifest doesn't have. Override: `--force-version-override` (human-only).

**Quickmerge stage 1.6 — Dependency version canary:** Warning only (does not block). Alerts if dependencies have
been bumped on LDR/main since your last pull.

---

## Admin Operations (Special Circumstances Only)

> **WARNING:** Force-push bypasses normal CI/CD flow. Use only when the standard quickmerge→LDR flow cannot be used.

**Script:** `scripts/repo-management/admin-force-sync-all-to-main.sh`
**Access:** IggyIkenna only (identity gate via `gh api user`).

```bash
# Dry run first
bash unified-trading-pm/scripts/repo-management/admin-force-sync-all-to-main.sh --admin-confirm --dry-run

# Force push
bash unified-trading-pm/scripts/repo-management/admin-force-sync-all-to-main.sh --admin-confirm

# Single repo
bash unified-trading-pm/scripts/repo-management/admin-force-sync-all-to-main.sh --admin-confirm --repo unified-trading-pm
```

When NOT to use: do not substitute for quickmerge in normal workflow. Force-push skips quality gates, PR review, and
semver-agent. Always prefer quickmerge→LDR for standard changes.

---

## References

| Doc                                                     | Purpose                                              |
|---------------------------------------------------------|------------------------------------------------------|
| `codex/08-workflows/ci-cd-flow.md`                      | CI/CD pipeline SSOT (LDR-trunk model, quickmerge)    |
| `codex/06-coding-standards/quality-gates.md`            | QG config, parity matrix, tool version pinning       |
| `scripts/repo-management/README-ALIGNMENT-AND-SETUP.md` | Phase 1–2 command detail                             |
| `scripts/workspace/setup-workspace-venv.sh`             | Underlying venv setup implementation                 |
| `scripts/dev/network_block_plugin.py`                   | Credential-free CI network block plugin              |
| `docker/docker-compose.mock.yml`                        | Full mock service stack definition                   |
