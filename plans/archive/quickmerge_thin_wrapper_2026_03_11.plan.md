# Plan: quickmerge as Thin Wrapper Around Quality Gates

**Status:** DONE **Completed:** 2026-03-11 **Commits:** unified-trading-pm `876c3cf`, unified-trading-ui-kit `9231eff`

## Goal

Refactor quickmerge.sh so it is a thin orchestration wrapper — all quality checks live in quality-gates.sh, which
quickmerge delegates to. Remove duplicate logic, fix broken flags, add selective run modes.

## Changes Delivered

### quickmerge.sh (unified-trading-pm canonical → rolled out to 66 repos)

- **--agent flag fixed:** Now sets `SKIP_TESTS="--skip-tests"` after arg parsing, so tests are actually skipped when
  `--agent` is passed (was broken before — flag was set but never acted upon).
- **Stage 3.5 removed:** ~55-line D3 cloud-agnostic gate block was a pure duplicate of base-service.sh steps 5.10+5.11.
  Removed.
- **Stage 4 refactored:** Act simulation replaced from hardcoded logic to delegation:
  `bash scripts/quality-gates.sh --act`. Skipped for `--quick` and `--agent`. Graceful warning if no quality-gates.sh
  present.

### base-service.sh + base-library.sh

- Added `ACT_MODE=false` init and `--act` case to arg parsing.
- Added `[ACT] GitHub Actions Simulation` section before duration check:
  - Auto-installs `act` if missing (brew on macOS, curl on Linux).
  - Discovers secrets from `ACT_SECRETS_FILE`, `.act-secrets`, or `~/.secrets`.
  - Delegates to `act -j quality-gates --container-architecture linux/amd64`.

### unified-trading-ui-kit

- Created `scripts/quality-gates.sh` stub (was the only repo in the manifest with no scripts/ directory at all).
- `quickmerge.sh` created by rollout.

### Rollout

- `rollout-quickmerge.py` synced canonical quickmerge.sh to all 66 non-PM repos.

## Analysis Summary (Pre-Implementation)

- 4 quality-gate base scripts: base-service.sh, base-library.sh, base-ui.sh, base-codex.sh
- base-ui.sh already had --lint/--test/--quick/--no-fix selective modes
- 77-line drift between PM canonical and per-repo copies was resolved by rollout
- Workspace orchestration stages (0, 0.5, 1, 1.5) correctly remain in quickmerge as they require cross-repo git
  operations that quality-gates cannot do alone
