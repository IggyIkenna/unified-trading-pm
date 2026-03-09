# Quality Gates Base Scripts

Centralized quality-gate logic for all Python repos in the unified-trading workspace.

## Overview

Every Python repo's `scripts/quality-gates.sh` is a thin config stub that sources one of these base scripts. The base
script contains the full gate logic — only the repo-specific variables (service name, source dir, coverage threshold,
deps) live in each repo.

To add a new check for **all** service repos, edit `base-service.sh` only. No per-repo changes needed.

## Files

```
quality-gates-base/
├── base-service.sh   # Services (FastAPI apps, workers, APIs) — sourced by 27 service repos
├── base-library.sh   # Libraries and interfaces — sourced by 17 library/interface repos
└── README.md         # This file
```

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

### LIBRARY repos (~10 lines)

```bash
#!/usr/bin/env bash
# Repo-specific settings only. Body: unified-trading-pm/scripts/quality-gates-base/base-library.sh
SOURCE_DIR="<package_dir>"
MIN_COVERAGE=<N>
LOCAL_DEPS=()
WORKSPACE_ROOT="$(cd "$(git rev-parse --show-toplevel)/.." && pwd)"
source "${WORKSPACE_ROOT}/unified-trading-pm/scripts/quality-gates-base/base-library.sh"
```

Required variables: `SOURCE_DIR`, `MIN_COVERAGE`

Optional variables: `PACKAGE_NAME` (used for basedpyright cache), `PYTEST_WORKERS` (default: 2), `LOCAL_DEPS` (default:
empty array)

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

1. Edit the appropriate base script (`base-service.sh` or `base-library.sh`) in this directory
2. Test on one repo first: `bash scripts/quality-gates.sh --quick` from within the repo
3. Commit to `unified-trading-pm` with message `feat(quality-gates): add <check-name> check`
4. All repos immediately pick up the new check on next run — no per-repo commits needed

## New Repo Setup

For a new **service** repo, copy the SERVICE stub template above, filling in:

- `SERVICE_NAME` — the repo directory name (e.g. `"my-new-service"`)
- `SOURCE_DIR` — the Python package directory name (e.g. `"my_new_service"`)
- `MIN_COVERAGE` — set to `(actual coverage - 1%)` after first test run

For a new **library** repo, copy the LIBRARY stub template above, filling in:

- `SOURCE_DIR` — the Python package directory name (e.g. `"my_new_library"`)
- `MIN_COVERAGE` — set to `(actual coverage - 1%)` after first test run
