# Quality Gates Base Scripts

Centralized quality-gate logic for repos that use the source-based pattern.

## Overview

Two repos use this pattern — `unified-trading-pm` sources `base-service.sh`, `unified-trading-codex` sources
`base-codex.sh`. All other Python repos use standalone copies of the codex templates rolled out by
`rollout-quality-gates-unified.py`.

To add a new check for PM's quality gates, edit `base-service.sh`. For all other repos, edit the codex template
(`unified-trading-codex/06-coding-standards/quality-gates-service-template.sh` or `quality-gates-library-template.sh`)
and re-run the rollout.

## Files

```
quality-gates-base/
├── base-service.sh   # Used by: unified-trading-pm/scripts/quality-gates.sh only
├── base-codex.sh     # Used by: unified-trading-codex/scripts/quality-gates.sh only
└── README.md         # This file
```

Note: `base-library.sh` was deleted — it had no callers. Library repos use standalone codex template copies.

## Stub Templates

### SERVICE repos (~12 lines)

```bash
#!/usr/bin/env bash
# Repo-specific settings only. Body: unified-trading-pm/scripts/quality-gates-base/base-service.sh
SERVICE_NAME="<repo-name>"
SOURCE_DIR="<package_dir>"
MIN_COVERAGE=<N>
RUN_INTEGRATION=false
PYTEST_WORKERS=${PYTEST_WORKERS:-2}
LOCAL_DEPS=()
WORKSPACE_ROOT="$(cd "$(git rev-parse --show-toplevel)/.." && pwd)"
source "${WORKSPACE_ROOT}/unified-trading-pm/scripts/quality-gates-base/base-service.sh"
```

Required variables: `SERVICE_NAME`, `SOURCE_DIR`, `MIN_COVERAGE`, `RUN_INTEGRATION`

Optional variables: `PYTEST_WORKERS` (default: 2), `LOCAL_DEPS` (default: empty array)

### CODEX / DOCS repos (~8 lines)

```bash
#!/usr/bin/env bash
# Repo-specific settings only. Body: unified-trading-pm/scripts/quality-gates-base/base-codex.sh
SERVICE_NAME="unified-trading-codex"
WORKSPACE_ROOT="$(cd "$(git rev-parse --show-toplevel)/.." && pwd)"
source "${WORKSPACE_ROOT}/unified-trading-pm/scripts/quality-gates-base/base-codex.sh"
```

Required variables: `SERVICE_NAME`

Runs: markdown lint, prettier formatting check, link validation (non-blocking), codex structure checks. Skips:
basedpyright, pytest, ruff source lint, pip-audit, bandit.

## Path Resolution

`git rev-parse --show-toplevel` returns the invoking repo root (e.g. `/workspace/features-calendar-service`). Parent
directory (`..`) is always the workspace root where `unified-trading-pm` is a sibling. This works in local dev and CI
(Cloud Build / AWS CodeBuild) where workspace is checked out flat.

## Version Guard

Each base script defines `REQUIRED_BASE_VERSION="1.0"`. Stubs may optionally declare `EXPECTED_BASE_VERSION="1.0"`
before sourcing. If the versions differ, a warning is printed:

```
⚠️  Stub expects base v1.0 but base is v2.0
```

### Version Bump Protocol

Increment `REQUIRED_BASE_VERSION` in the base script on any **breaking** change to the base interface (e.g. renaming a
required variable, removing a gate section). Announce the bump in a PM commit with a migration guide so stub maintainers
can update `EXPECTED_BASE_VERSION` when ready.

Non-breaking additions (new checks, new optional variables with defaults) do NOT require a version bump.

## Usage

```bash
# From within any repo:
bash scripts/quality-gates.sh           # Auto-fix then verify
bash scripts/quality-gates.sh --no-fix  # Verify only (CI mode)
bash scripts/quality-gates.sh --quick   # Unit tests only (skip integration)
bash scripts/quality-gates.sh --lint    # Lint only
bash scripts/quality-gates.sh --test    # Tests only
bash scripts/quality-gates.sh --skip-typecheck  # Skip basedpyright
```

## Adding a New Gate Check

**For PM or codex only** (source-based repos):

1. Edit `base-service.sh` (PM) or `base-codex.sh` (codex) in this directory
2. Test: `bash scripts/quality-gates.sh --quick` from within the repo
3. Commit to `unified-trading-pm`

**For all other repos** (template-based, 58 repos):

1. Edit `unified-trading-codex/06-coding-standards/quality-gates-service-template.sh` or
   `quality-gates-library-template.sh`
2. Commit to `unified-trading-codex`
3. Re-run rollout: `python3 unified-trading-pm/scripts/propagation/rollout-quality-gates-unified.py`

## New Repo Setup

For a new **service** or **library** repo: use `rollout-quality-gates-unified.py` — it adds `scripts/quality-gates.sh`,
`scripts/setup.sh`, `.cursorignore`, `.gitignore`, and `QUALITY_GATE_BYPASS_AUDIT.md` from the codex templates
automatically.

For a new **docs-only** repo (no Python source), copy the CODEX stub template above, filling in:

- `SERVICE_NAME` — the repo directory name (e.g. `"my-standards-repo"`)
