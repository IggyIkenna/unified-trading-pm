# Quality Gates Base Scripts

Centralized quality-gate logic for repos that use the source-based pattern.

## Overview

All Python repos use source stubs that point to this directory. Each repo's `scripts/quality-gates.sh` is a ~10-line
config stub that sets repo-specific variables and sources the appropriate base script.

To add a new check for **all service repos**, edit `base-service.sh` here — no rollout needed. To add a new check for
**all library repos**, edit `base-library.sh` here — no rollout needed. To add a new check for **codex only**, edit
`base-codex.sh` here.

## Files

```
quality-gates-base/
├── base-service.sh   # 28 service repos (FastAPI apps, workers, APIs)
├── base-library.sh   # 17 library/interface repos
├── base-codex.sh     # 1 docs-only repo (unified-trading-codex)
└── README.md         # This file
```

UI repos (~12) are out of scope — already have minimal JS/TS stubs and a separate toolchain.

## Stub Templates

### LIBRARY repos (~10 lines)

```bash
#!/usr/bin/env bash
# Repo-specific settings only. Body: unified-trading-pm/scripts/quality-gates-base/base-library.sh
PACKAGE_NAME="<repo-name>"
SOURCE_DIR="<package_dir>"
MIN_COVERAGE=<N>
PYTEST_WORKERS=${PYTEST_WORKERS:-2}
LOCAL_DEPS=()
WORKSPACE_ROOT="$(cd "$(git rev-parse --show-toplevel)/.." && pwd)"
source "${WORKSPACE_ROOT}/unified-trading-pm/scripts/quality-gates-base/base-library.sh"
```

Required variables: `PACKAGE_NAME`, `SOURCE_DIR`, `MIN_COVERAGE`

Optional variables: `PYTEST_WORKERS` (default: 2), `LOCAL_DEPS` (default: empty array)

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

**For all service repos** (28 repos):

1. Edit `base-service.sh` in this directory
2. Commit to `unified-trading-pm`
3. No rollout needed — all repos source this file directly

**For all library repos** (17 repos):

1. Edit `base-library.sh` in this directory
2. Commit to `unified-trading-pm`
3. No rollout needed — all repos source this file directly

## New Repo Setup

For a new **service** repo: copy the SERVICE stub template above, set `SERVICE_NAME`, `SOURCE_DIR`, `MIN_COVERAGE`,
`RUN_INTEGRATION`, and optionally `LOCAL_DEPS`. The body is inherited from `base-service.sh`.

For a new **library** repo: copy the LIBRARY stub template above, set `PACKAGE_NAME`, `SOURCE_DIR`, `MIN_COVERAGE`, and
optionally `LOCAL_DEPS`. The body is inherited from `base-library.sh`.

For a new **docs-only** repo (no Python source), copy the CODEX stub template above, filling in:

- `SERVICE_NAME` — the repo directory name (e.g. `"my-standards-repo"`)
