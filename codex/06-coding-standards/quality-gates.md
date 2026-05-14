---
scope: [engineer]
---

# Quality Gates

> **FLAT-DEPS BANNER (codified 2026-05-12 per TS-5 audit)** — the workspace is on **flat-deps-only**: every
> `pyproject.toml` has ONE `[project.dependencies]` block; no `[project.optional-dependencies]`, no `.[dev]` extras.
> Multiple inline examples below still show legacy `uv pip install -e ".[dev]"` / `[project.optional-dependencies] dev`
> shapes (pre-2026-05 patterns); they will be scrubbed inline. New work: use the flat `dependencies` block + plain
> `uv pip install -e .` per CLAUDE.md § "Dependencies + builds". Verification:
> `grep optional-dependencies */pyproject.toml` returns 0 hits.

## Table of Contents

1. [TL;DR](#tldr)
2. [Two-Pass Workflow Model](#two-pass-workflow-model)
   - [Three-Phase Internal Model (inside quickmerge Stage 3)](#three-phase-internal-model-inside-quickmerge-stage-3)
3. [Tool Version Pinning and Environment Isolation](#tool-version-pinning-and-environment-isolation)
   - [Three Environments, Three Purposes](#three-environments-three-purposes)
   - [Tool Resolution Rules (Enforced in QG Templates)](#tool-resolution-rules-enforced-in-qg-templates)
   - [Pinned Versions (Canonical)](#pinned-versions-canonical)
   - [Workspace Venv Sync (Day-to-Day)](#workspace-venv-sync-day-to-day)
   - [Version Alignment Pipeline — Step 5 (Workspace Venv)](#version-alignment-pipeline--step-5-workspace-venv)
4. [Canonical Code Limits (BLOCKING)](#canonical-code-limits-blocking--all-enforced-in-quality-gatessh)
   - [Coverage by repo type](#coverage-by-repo-type)
   - [Coverage floor exceptions](#coverage-floor-exceptions-approved-repos-only)
5. [Audit Alignment (Independent Audit 2026-03-01)](#audit-alignment-independent-audit-2026-03-01)
6. [Quality Gate Bypass Audit Methodology](#quality-gate-bypass-audit-methodology)
   - [Two-Level Audit System](#two-level-audit-system)
   - [Per-Repo Audit File (Required)](#per-repo-audit-file-required)
   - [Suppression Categories](#suppression-categories)
   - [Enforcement](#enforcement)
7. [SSOT Alignment Validation (Documentation Quality Gates)](#ssot-alignment-validation-documentation-quality-gates)
   - [What It Catches](#what-it-catches)
   - [Pre-Commit Hook (Blocks Bad Commits)](#pre-commit-hook-blocks-bad-commits)
   - [GitHub Actions (PR Checks)](#github-actions-pr-checks)
   - [Manual Validation](#manual-validation)
   - [Troubleshooting](#troubleshooting)
8. [Canonical Template](#canonical-template-new)
9. [Repo-Type-Specific Base Scripts](#repo-type-specific-base-scripts)
10. [Quality Gate Performance](#quality-gate-performance)
    - [`--skip-typecheck` Flag](#--skip-typecheck-flag)
    - [Three-Phase Pattern (current)](#three-phase-pattern-current)
    - [BASEDPYRIGHT_CACHE_DIR](#basedpyright_cache_dir)
    - [run_timeout Helper](#run_timeout-helper)
11. [Python Version Consistency](#python-version-consistency)
    - [Run Quality Gates = Single Command (No Setup First)](#run-quality-gates--single-command-no-setup-first)
    - [Quickmerge Activates Venv](#quickmerge-activates-venv)
    - [CI Reads Python from pyproject.toml](#ci-reads-python-from-pyprojecttoml)
    - [Local Python Detection (when running quality-gates directly)](#local-python-detection-when-running-quality-gates-directly)
12. [What quality-gates.sh Does](#what-quality-gatessh-does)
    - [Step 0: Config Validation](#step-0-config-validation)
    - [Step 1: Auto-Fix (Phase 1)](#step-1-auto-fix-phase-1)
    - [Step 2: Linting (Phase 2)](#step-2-linting-phase-2)
    - [Step 3: Tests](#step-3-tests)
13. [Usage](#usage)
14. [Two-Phase Workflow](#two-phase-workflow)
15. [Ruff Version Consistency](#ruff-version-consistency-critical)
    - [Three-Stage Consistency Model](#three-stage-consistency-model)
    - [Verifying Consistency](#verifying-consistency)
    - [Updating Ruff Version](#updating-ruff-version)
16. [Ruff Configuration](#ruff-configuration)
17. [Type Checking Standards (pyrightconfig.json)](#type-checking-standards-pyrightconfigjson)
18. [Library pyproject.toml: basedpyright Config](#library-pyprojecttoml-basedpyright-config)
19. [STEP 5.22: basedpyright Baseline Suppression](#step-522-basedpyright-baseline-suppression-error-policy--escalated-2026-03-10)
    - [Policy (effective 2026-03-10)](#policy-effective-2026-03-10)
    - [How the gate counts suppressions](#how-the-gate-counts-suppressions)
    - [Remediation steps](#remediation-steps)
    - [Pre-commit formatter note](#pre-commit-formatter-note)
    - [SSOT](#ssot)
20. [CI Parity](#ci-parity-implemented)
    - [Key Parity Rules](#key-parity-rules)
    - [Package Manager Standard: UV](#package-manager-standard-uv)
    - [Cloud Build Architecture: Test-in-Image](#cloud-build-architecture-test-in-image)
    - [Shared Libraries: Idempotent Package Publishing](#shared-libraries-idempotent-package-publishing)
21. [When Quality Gates Fail](#when-quality-gates-fail)
22. [Running All Quality Gates](#running-all-quality-gates)
23. [Security Gates](#security-gates-implemented--blocking-in-all-repos)
    - [pip-audit — OSS vulnerability scan (BLOCKING)](#1-pip-audit--oss-vulnerability-scan-blocking)
    - [Internal advisory check (BLOCKING)](#2-internal-advisory-check-blocking)
    - [SBOM audit trail (non-blocking)](#3-sbom-audit-trail-non-blocking)
    - [Bandit B108 — hardcoded temp paths (Python)](#4-bandit-b108--hardcoded-temp-paths-python)
24. [Dead Code Detection (vulture)](#dead-code-detection-vulture-advisory--warnfail-thresholds)
    - [Thresholds](#thresholds)
    - [Installing vulture](#installing-vulture)
    - [Suppressing false positives with .vulture-whitelist.py](#suppressing-false-positives-with-vulture-whitelistpy)
    - [Common false-positive patterns](#common-false-positive-patterns)
    - [pyproject.toml configuration (optional)](#pyprojecttoml-configuration-optional)
    - [Running vulture manually](#running-vulture-manually)
25. [AWS CodeBuild Parity](#aws-codebuild-parity)
    - [Identical Gate Logic](#identical-gate-logic)
    - [Structural Differences](#structural-differences)
    - [Environment Variables](#environment-variables)
    - [Service-Specific Mock Variables (GCP only)](#service-specific-mock-variables-gcp-only)
    - [GCP Emulator Configuration](#gcp-emulator-configuration)
    - [AWS Moto Integration Tests](#aws-moto-integration-tests)
    - [Credential-Free CI Gate](#credential-free-ci-gate-network_block_plugin)
    - [Cassette Parity Testing (H5.2)](#cassette-parity-testing-h52)
    - [Cassette Drift Detection (H5.1)](#cassette-drift-detection-h51)
    - [Parity Rules](#parity-rules)
    - [Library Repos: Simpler Buildspec](#library-repos-simpler-buildspec)
    - [Adding AWS CodeBuild to a New Repo](#adding-aws-codebuild-to-a-new-repo)
26. [Anti-Patterns](#anti-patterns)

## QG STEP cross-reference

CLAUDE.md and `unified-trading-pm/scripts/quality-gates-base/base-service.sh` reference QG steps by `STEP 5.X`
identifiers. The table below maps each canonical step number to its location in this doc + the canonical enforcement
file. Steps without a dedicated section here are enforced inline in `base-service.sh` and documented in CLAUDE.md "Key
Rules (Quick Reference)" / "Service Infrastructure Requirements".

| STEP | Topic                                  | This doc anchor                                                                                                                            | Enforcement file (canonical)                                         | CLAUDE.md cross-ref                                                                                                         |
| ---- | -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| 5.10 | basedpyright type-check                | [Type Checking Standards](#type-checking-standards-pyrightconfigjson)                                                                      | `scripts/quality-gates-base/base-service.sh`                         | "Key Rules — `basedpyright` not `pyright`"                                                                                  |
| 5.11 | ruff lint + format                     | [Ruff Version Consistency](#ruff-version-consistency-critical) · [Ruff Configuration](#ruff-configuration)                                 | `scripts/quality-gates-base/base-service.sh`                         | "Key Rules — flat deps + ruff"                                                                                              |
| 5.22 | basedpyright suppression baseline      | [STEP 5.22: basedpyright Baseline Suppression](#step-522-basedpyright-baseline-suppression-error-policy--escalated-2026-03-10)             | `scripts/quality-gates-base/base-service.sh` + `base-library.sh`     | "No `# type: ignore` to hide architectural violations"                                                                      |
| 5.34 | typed config reloaders                 | (no section here — see enforcement file)                                                                                                   | `scripts/quality-gates-base/base-service.sh`                         | "Service Infrastructure Requirements — Typed config reloaders (STEP 5.34)"                                                  |
| 5.61 | ServiceBootstrap presence              | (no section here — see enforcement file)                                                                                                   | `scripts/quality-gates-base/base-service.sh`                         | "Service Infrastructure Requirements — ServiceBootstrap (STEP 5.61)"                                                        |
| 5.62 | Health API + `make_health_router`      | (no section here — see enforcement file)                                                                                                   | `scripts/quality-gates-base/base-service.sh`                         | "Service Infrastructure Requirements — Health API (STEP 5.62)"                                                              |
| 5.64 | bundled-shard cluster validation AST   | (no section here — see enforcement file)                                                                                                   | `scripts/quality-gates-base/base-service.sh`                         | "Cluster validation MANDATORY at `record_captured` for bundled shards"                                                      |
| 5.65 | removed-symbol AST-walk                | [STEP 5.65: Removed-Symbol AST-Walk](#step-565-removed-symbol-ast-walk-citadel--6-extended)                                                | `scripts/quality_gates/check_removed_symbols.py` (driver)            | "Citadel-Grade Planning Standards § 6 Downstream Consumer Updates"                                                          |
| 5.66 | per-VM shard isolation envvar AST walk | (no section here — see enforcement file)                                                                                                   | `scripts/quality-gates-base/base-service.sh`                         | "Per-VM shard isolation for concurrent backfills"                                                                           |
| 5.67 | banned NaN-placeholder method AST-walk | [STEP 5.67: Banned NaN-Placeholder / Bypass-`record_captured` AST-Walk](#step-567-banned-nan-placeholder--bypass-record_captured-ast-walk) | `scripts/quality_gates/check_banned_placeholder_methods.py` (driver) | "Honest absence vs fake placeholders" + "No double SSOT in data-saving methodology" + "Four-category empty-output decision" |
| 5.69 | inline `f"gs://…"` / `f"s3://…"` URI ratchet | (no section here — see enforcement file)                                                                                                   | `scripts/quality_gates/check_inline_bucket_uri.py` (driver)          | "Bucket-name SSOT (b+)"                                                                                                     |
| 5.70 | explicit `pipeline_mode=` at `record_*` calls | [STEP 5.70: Explicit `pipeline_mode=` at every `record_*` call](#step-570-explicit-pipeline_mode-at-every-record_-call-manifest-v8) | `scripts/quality_gates/check_pipeline_mode_explicit_at_record_calls.py` (driver) | "Live = batch (CRITICAL)" + "Availability manifest v8 — `pipeline_mode` first-class column"                                 |
| L1   | data_type enum contains `LIVE_`/`BATCH_` prefixed members | [STEP L1: DataType Mode-Prefix Ban](#step-l1-datatype-mode-prefix-ban-day-1-enable) | `scripts/quality-gates-base/base-service.sh` (pending wire-in) | "Batch = Live: Unified Pipeline Architecture" — unified DataType enum, no per-mode fork |
| L2   | mode-conditional branches outside seams | [STEP L2: Mode-Conditional-Outside-Seam](#step-l2-mode-conditional-outside-seam-fix-required-21-violations) | `scripts/quality-gates-base/base-service.sh` (pending wire-in) | `mode-axis-discipline.md` AP-1 — business logic must not branch on `RuntimeMode` |
| L3   | `RuntimeMode` declared outside UAC SSOT | [STEP L3: RuntimeMode Single SSOT](#step-l3-runtimemode-single-ssot-fix-required-2-violations) | `scripts/quality-gates-base/base-service.sh` (pending wire-in) | `mode-axis-discipline.md` AP-3 — SSOT: `unified_api_contracts.internal.modes.RuntimeMode` |
| L7   | `record_captured()` missing `assert_available_at_present` | [STEP L7: record_captured assert_available_at_present](#step-l7-record_captured-assert_available_at_present-ongoing-sweep) | `scripts/quality-gates-base/base-service.sh` (ongoing ratchet) | "`available_at` is per-row, write-time" — UTL guard internal; L7 catches callsites that bypass |

When a STEP appears in CI output (e.g. `STEP 5.62 FAILED: api/main.py missing make_health_router`), open the enforcement
file's matching block for the exact assertion + the CLAUDE.md cross-ref for the rationale + the linked anchor here for
deeper context.

## TL;DR

Every service has `scripts/quality-gates.sh` that runs the exact same checks as GitHub Actions and Cloud Build. It
operates in three phases inside quickmerge: Phase 1 (lint auto-fix only — fast), Phase 2 (lint verify — abort early if
unfixable), Phase 3 (tests + typecheck + codex — run exactly once). **For pre-push workflow always use quickmerge** (it
runs quality gates); run `quality-gates.sh` directly only for local iteration or CI. If quality gates fail, fix the root
cause — never bypass.

## Two-Pass Workflow Model

The recommended workflow separates a **full validation pass** from a **lightweight pre-PR pass**:

| Pass                    | Command                                    | What runs                                         | When                           |
| ----------------------- | ------------------------------------------ | ------------------------------------------------- | ------------------------------ |
| **Pass 1 — full**       | `bash scripts/quality-gates.sh`            | lint, format, tests, typecheck, codex, security   | Before you consider work done  |
| **Pass 2 — quickmerge** | `bash scripts/quickmerge.sh "msg" --agent` | lint, format, typecheck, codex (no tests, no act) | Immediately before PR creation |

**Why two passes?** Tests are the slowest gate (5-60s). Running them again in quickmerge when they already passed in
Pass 1 wastes time. Quickmerge's internal QG pass with `--agent` is a fast final check that nothing was broken by the
auto-format step.

**`--agent` flag** (for agents and CI): implies `--skip-tests` + skip act. Quickmerge becomes
lint/format/typecheck/codex only — the same things that could silently break during commit staging.

**`--quick` flag** (human shortcut): skip act only; tests still run. Use when you want act simulation skipped but want
test re-validation.

```bash
# Agent/CI workflow (two-pass)
bash scripts/quality-gates.sh                           # Pass 1: full validation
bash scripts/quickmerge.sh "feat: ..." --agent          # Pass 2: lint+format+typecheck+codex only, no act

# Agent/CI — also skip typecheck in quickmerge (ran in pass 1)
bash scripts/quickmerge.sh "feat: ..." --agent --skip-typecheck

# Human — skip act only (tests re-run in quickmerge)
bash scripts/quickmerge.sh "feat: ..." --quick

# Human — full quickmerge including act simulation
bash scripts/quickmerge.sh "feat: ..."
```

### Three-Phase Internal Model (inside quickmerge Stage 3)

Quickmerge's Stage 3 runs quality gates in three phases to eliminate redundant test/typecheck runs:

| Phase                   | Flags                  | What runs                                     | Purpose                               |
| ----------------------- | ---------------------- | --------------------------------------------- | ------------------------------------- |
| **1 — lint auto-fix**   | `--lint --fix`         | ruff format + ruff check --fix / eslint --fix | Auto-repair fixable issues            |
| **2 — lint verify**     | `--no-fix --lint`      | ruff check / eslint (no fix)                  | Abort early if unfixable lint remains |
| **3 — full minus lint** | `--no-fix --skip-lint` | tests + typecheck + codex / tests + build     | Run slow gates exactly once           |

**Why three phases?** Tests and typecheck are unaffected by linter auto-fixes. The old two-phase model (full+fix →
full+no-fix) ran tests twice. The three-phase model runs lint cheaply first, aborts fast on unfixable lint, then runs
tests/typecheck exactly once.

**New flags added to base scripts:**

- `--skip-lint` — skip ruff/eslint entirely (Python + UI)
- `--fix` — enable ESLint auto-fix (UI; Python already defaults to auto-fix)

**Status:** [IMPLEMENTED] in all service and library repos.

**Canonical Base Scripts:** `unified-trading-pm/scripts/quality-gates-base/` (base-service.sh, base-library.sh,
base-codex.sh, base-ui.sh). Per-repo `scripts/quality-gates.sh` files are **config stubs only** — never full
implementations. **All repo types** (Python services, libraries, codex, and TypeScript UI repos) use this stub
architecture. See
[Coding Standards README § Quality Gates Structure](./README.md#quality-gates-structure-centralized-base-scripts).

---

## Tool Version Pinning and Environment Isolation

### Three Environments, Three Purposes

| Environment            | What it owns                                                                                                                                                                                                                              | Used by                                                                       | Rule                                                                                                                  |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `.venv-workspace`      | Union of all active repo deps (count derives from `workspace-manifest.json` `repositories` keys excluding `archived_into`; **27 active as of 2026-05-09** after features-\* consolidation); pinned `ruff==0.15.0`, `basedpyright==1.38.2` | IDE cross-repo IntelliSense; `RUFF_CMD` in QG templates                       | **Never** used as `PYTHON_CMD` or `BASEDPYRIGHT_CMD` in QG — it has extra packages that mask missing dep declarations |
| `.venv` (per-repo)     | Exact deps from `pyproject.toml` + `[dev]`                                                                                                                                                                                                | QG `PYTHON_CMD`, `BASEDPYRIGHT_CMD`, pytest, bandit; CI/GHA `agent-audit.yml` | **Always** the source of truth for type-checking and test execution                                                   |
| GHA runner (container) | Fresh install from `pyproject.toml` on every run                                                                                                                                                                                          | `overnight-agent-orchestrator` → `agent-audit.yml`; CI quality gates          | No `.venv-workspace` — QG template falls through to `.venv` (correct)                                                 |

### Tool Resolution Rules (Enforced in QG Templates)

```
RUFF_CMD:         .venv-workspace/bin/ruff  →  .venv/bin/ruff  →  ruff
                  (consistent pinned version; ruff is a pure binary, never loads packages)

BASEDPYRIGHT_CMD: .venv/bin/basedpyright  →  basedpyright
                  (NEVER workspace venv — basedpyright resolves types via site-packages;
                   workspace has extra packages that mask missing pyproject.toml declarations)

PYTHON_CMD:       .venv/bin/python  →  python3
                  (NEVER workspace venv — test isolation requires exact per-repo deps)
```

**Why this split matters:** A repo that imports `X` but doesn't declare `X` in `pyproject.toml` will typecheck clean
locally (workspace has `X`) but fail in CI (fresh install doesn't). The per-repo rule closes this "works on my machine"
hole.

### Pinned Versions (Canonical)

| Tool           | Pinned version | Enforced by                                  |
| -------------- | -------------- | -------------------------------------------- |
| `ruff`         | `0.15.0`       | QG template version check (warn if mismatch) |
| `basedpyright` | `1.38.2`       | QG template version check (warn if mismatch) |

Both checks warn (not fail) on mismatch so a stale venv doesn't block CI — but they are visible in QG output and must be
resolved before merging.

Per-repo `pyproject.toml` dev deps must declare `basedpyright==1.38.2` and `ruff==0.15.0`.

### Workspace Venv Sync (Day-to-Day)

After any version alignment run or `git pull` on `unified-trading-pm`:

```bash
bash unified-trading-pm/scripts/workspace/sync-workspace-venv.sh          # refresh (idempotent)
bash unified-trading-pm/scripts/workspace/sync-workspace-venv.sh --check  # verify only
bash unified-trading-pm/scripts/workspace/sync-workspace-venv.sh --force  # full recreate
```

This is distinct from `workspace-bootstrap.sh`, which is the **new machine** entry point (clone repos + system deps +
venv + per-repo setup). `sync-workspace-venv.sh` is for day-to-day refresh only.

### Version Alignment Pipeline — Step 5 (Workspace Venv)

The version alignment pipeline in `run-version-alignment.sh` has a Step 5 (pending implementation):

```
Step 1: bump versions
Step 2: update workspace-manifest.json
Step 3: dispatch version-cascade to downstream repos
Step 4: validate all repos aligned
Step 5: generate workspace-requirements.txt → commit to PM  ← planned
```

Step 5 generates `unified-trading-pm/configs/workspace-requirements.txt` (union of all active repos' deps via
`uv pip compile`; active count derives from `workspace-manifest.json` `repositories` keys excluding `archived_into`).
Developers then run `sync-workspace-venv.sh` to pull the refreshed union. Conflicts in `uv pip compile` signal a version
cascade violation and fail the alignment job.

---

## Canonical Code Limits (BLOCKING — all enforced in quality-gates.sh)

| Limit                           | Value                         | Variable in template                      |
| ------------------------------- | ----------------------------- | ----------------------------------------- |
| Min test coverage               | **70% service / 80% library** | `MIN_COVERAGE=max(floor, actual-1)`       |
| Max file lines                  | **900** (warn at 700)         | `MAX_FILE_LINES=900; FILE_WARN_LINES=700` |
| Max function lines              | **200**                       | `MAX_FUNCTION_LINES=200`                  |
| Max method lines (inside class) | **50**                        | `MAX_METHOD_LINES=50`                     |
| Max class lines                 | **900**                       | `MAX_CLASS_LINES=900`                     |
| McCabe complexity               | **10**                        | `max-complexity = 10` in ruff             |

### Coverage by repo type

| Repo type      | Floor (minimum) | Formula                        |
| -------------- | --------------- | ------------------------------ |
| library        | **80%**         | `max(80, actual_coverage - 1)` |
| service        | **70%**         | `max(70, actual_coverage - 1)` |
| api-service    | **70%**         | `max(70, actual_coverage - 1)` |
| infrastructure | **70%**         | `max(70, actual_coverage - 1)` |
| docs-only      | N/A             | —                              |

**Rule:** `MIN_COVERAGE = max(floor, actual_coverage - 1)`. The `-1` allows one percentage point of natural churn; the
floor is an absolute minimum that cannot be undercut.

To recalibrate all repos: `python3 scripts/propagation/rollout-quality-gates-unified.py --recalibrate`

Any repo below its floor must either raise coverage or document the exception in `QUALITY_GATE_BYPASS_AUDIT.md`.

### Coverage floor exceptions (approved repos only)

Only the following four repos are approved permanent exceptions to the standard coverage floors. All other repos **must
meet or exceed their floor** — lowering MIN_COVERAGE below the type floor is not permitted without explicit approval and
a corresponding entry in `MIN_COVERAGE_OVERRIDES` in `rollout-quality-gates-unified.py`.

| Repo                       | Approved floor           | Reason                                                                               |
| -------------------------- | ------------------------ | ------------------------------------------------------------------------------------ |
| `unified-trading-pm`       | N/A — skipped by rollout | PM repo has its own quality-gates; not overwritten                                   |
| `unified-trading-codex`    | N/A — skipped by rollout | Codex repo has its own quality-gates; not overwritten                                |
| `system-integration-tests` | 0%                       | Pure test-harness repo — no production source package to measure                     |
| `ibkr-gateway-infra`       | 51%                      | Gateway client wraps proprietary IBKR API; most paths require live broker connection |

**Prohibited workarounds** (must not be used to bypass the floor):

- Lowering `MIN_COVERAGE` below the type floor in `quality-gates.sh`
- Adding entry-point or service-runner files to `MIN_COVERAGE_OVERRIDES` in the rollout script
- Adding `# pragma: no cover` to non-entry-point code to inflate coverage numbers

**Approved** (does not require exception):

- `# pragma: no cover` on CLI `if __name__ == "__main__":` guards and `__main__.py` launch blocks only

Size checks run via Python AST (function/class/method) and `wc -l` (file) in Step 5 of every quality-gates.sh. Coverage
is enforced by `--cov-fail-under=$MIN_COVERAGE` in pytest (Step 3).

**Sports vertical (Phase 3):** Per-service Step A naming checks — run before D1. Zero hits required:
`rg 'BaseSportsAdapter' .` (deleted in Phase 1); `rg 'from footballbets' .`;
`rg 'postgresql|psycopg2|sqlalchemy' . --type py` in pipeline services; `rg 'dict\[str, str\]' .` in execution-service
sports adapters (formerly USEI, old untyped protocol). See `.cursor/rules/sports-migration-standards.mdc` and
`04-architecture/sports-integration-plan.md` § Phase 3.

**Alignment Validation:** Pre-commit hook in `unified-trading-codex` blocks commits that violate SSOT alignment
(non-canonical bucket names, outdated event names, non-MVP venues).

---

## Audit Alignment (Independent Audit 2026-03-01)

Quality gates and codex checks are aligned with the findings of the independent strict audit. Use this table to ensure
every audit finding has a corresponding gate or codex rule; add missing checks to the canonical template and roll out to
all 57+ repos via parallel agents if needed.

| Audit finding                              | Codex / QG check                                            | Template / location                                                                             | Notes                                                  |
| ------------------------------------------ | ----------------------------------------------------------- | ----------------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| Service-as-package import (violation)      | No service repo may depend on another service as path dep   | Step 5: `check-no-service-deps.py` (see below) or rg on pyproject.toml vs manifest service list | Add to template; script in unified-trading-pm/scripts/ |
| Bare except                                | `rg "except:"` in production                                | quality-gates-service-template.sh [5] CODEX COMPLIANCE                                          | ✓ In template                                          |
| except Exception with pass/return (silent) | Log or re-raise required                                    | Cursor rule + code review; optional rg `except Exception:` then next line `pass`/`return`       | Document in codex; strict repos can add rg             |
| Fallback config (os.getenv with "")        | `rg 'os\.getenv\s*\([^)]+,\s*""\s*\)'`                      | quality-gates-service-template.sh [5]                                                           | ✓ In template                                          |
| print() in production                      | `rg "print\("` excluding tests/scripts                      | quality-gates-service-template.sh [5]                                                           | ✓ In template                                          |
| Imports inside functions                   | `rg "^[[:space:]]+import \|^[[:space:]]+from"` in source    | quality-gates-service-template.sh [5]                                                           | ✓ In template; E402 in ruff                            |
| Files >900 (warn 700) / >1500 block        | MAX_FILE_LINES=900, Step 5 size check                       | quality-gates-service-template.sh [5] size step                                                 | ✓ In template; audit used 1500 for “oversized”         |
| GCP_PROJECT_ID                             | Use GCP_PROJECT_ID only                                     | quality-gates-service-template.sh [5] rg GCP_PROJECT_ID                                         | ✓ In template                                          |
| Hardcoded central-element-\*               | `rg "central-element-323112"`                               | quality-gates-service-template.sh [5]                                                           | ✓ In template                                          |
| Coverage min 40% / 70%                     | --cov-fail-under=$MIN_COVERAGE; MIN_COVERAGE=70 in template | quality-gates-service-template.sh [3]                                                           | ✓ In template; all repos must set fail_under           |
| No dict[str, Any] in public API            | rg ": Any\|-> Any\|\[Any\]"                                 | quality-gates-service-template.sh [5]                                                           | ✓ In template                                          |
| Raw response.json()                        | rg response.json() without model_validate                   | quality-gates-service-template.sh [5]                                                           | ✓ In template                                          |
| Domain clients from UDC not UTS            | rg unified_trading_services.\*DomainClient                  | quality-gates-service-template.sh [5]                                                           | ✓ In template                                          |

**Service-import check (add to template):** For repos with `type: service` in workspace-manifest.json, quality-gates.sh
MUST fail if pyproject.toml (or [tool.uv.sources]) lists any other **service** repo as a path dependency. Canonical
script: `unified-trading-pm/scripts/check-no-service-deps.py` — reads manifest, detects current repo type, and exits 1
if a service has path dep on another service. Template step: run this script when present (same pattern as
check-import-patterns.py).

**Rollout:** Align all 57+ repos with the canonical template (quality-gates-service-template.sh for services,
quality-gates-library-template.sh for libraries). Use parallel agents to: (1) copy or diff each repo’s
scripts/quality-gates.sh against template, (2) add missing CODEX COMPLIANCE steps and MIN_COVERAGE, (3) add
check-no-service-deps.py invocation for service repos, (4) document exceptions in QUALITY_GATE_BYPASS_AUDIT.md only. See
INDEPENDENT_CODE_AUDIT_2026-03-01.md § 8.5 Codex and quality gates alignment.

---

## Quality Gate Bypass Audit Methodology

### Two-Level Audit System

Quality gate bypass tracking operates at two levels:

1. **Per-repo** (`{repo}/QUALITY_GATE_BYPASS_AUDIT.md`): Documents every individual suppression (`# type: ignore`,
   `# noqa`, file size exception) with file, line, and justification. **Every repo must have this file** — it is a
   required artifact per the service and library setup checklists.

2. **Codex aggregate** (`10-audit/QUALITY_GATE_BYPASS_AUDIT.md`): Cross-repo summary with category breakdown, hotspot
   analysis, and priority actions. Updated quarterly via workspace-wide scan.

### Per-Repo Audit File (Required)

Every repo must have `QUALITY_GATE_BYPASS_AUDIT.md` at its root with at minimum:

```markdown
# Quality Gate Bypass Audit — {repo-name}

## 2.1 File Size Exceptions

None.

## 2.2 Ruff Exceptions

None.

## 2.3 Basedpyright Exceptions

None.
```

Repos with active suppressions must expand each section with a table documenting: File, Line, Suppression, Category, and
Justification. See `10-audit/QUALITY_GATE_BYPASS_AUDIT.md` for the full category taxonomy and acceptable vs must-fix
classifications.

### Suppression Categories

| Category                | Acceptable?              | Action                        |
| ----------------------- | ------------------------ | ----------------------------- |
| LIBRARY_STUB_MISSING    | Yes (with documentation) | Document library + reasoning  |
| OVERLOAD_PATTERN        | Yes (with documentation) | Document intentional overload |
| ARCHITECTURAL_VIOLATION | **No**                   | Must fix — hiding real errors |
| OPTIONAL_CHAINING       | Fix                      | Add None checks               |
| UNION_NARROWING         | Fix                      | Narrow types explicitly       |

### Enforcement

- `scripts/quality-gates.sh` Step 5 references `QUALITY_GATE_BYPASS_AUDIT.md` sections 2.1/2.2/2.3 for whitelists
- Cursor rules (`strict-quality-gates.mdc`, `quality-gates-audit-factors.mdc`) enforce documentation
- Setup checklists require creating this file as part of repo scaffolding
- Quarterly workspace-wide scans update the codex aggregate

---

## STEP 5.65: Removed-Symbol AST-Walk (Citadel § 6 EXTENDED)

Enforces CLAUDE.md
[**Citadel-Grade Planning Standards § 6 Downstream Consumer Updates (extended 2026-05-08)**](../../cursor-configs/CLAUDE.md):
when a refactor REMOVES or RENAMES a publicly-imported Python symbol — function, class, constant, module path — every
workspace consumer must be updated in the same plan. The rule applies to shared libraries (UAC, UTL, UCI, UEI) AND to
any service / peripheral repo whose public symbol is imported elsewhere.

**Reference incident (2026-05-01 → 2026-05-08, 7-day silent rot)**: strategy-service V1-RETIRE Phase 2 removed
`get_strategy_factories` from `strategy_service.cli.handlers.batch_utils`. The peripheral consumer at
`e2e-testing/scripts/defi/colocated_engine.py:306` continued importing it; QG never ran on that script (it lived outside
any service's `quality-gates.sh`); the operator only discovered the breakage when running the harness manually a week
later. STEP 5.65 closes that gap.

### How it works

1. **Manifest of removed symbols** — `unified-trading-pm/scripts/quality_gates/removed_symbols_manifest.yaml` is the
   workspace SSOT. Each entry declares:
   - `symbol`: fully-qualified dotted path (`module.submodule.name`).
   - `removed_at`: ISO date the refactor commit landed.
   - `removed_by_commit`: short SHA of the refactor commit.
   - `successor`: replacement symbol path, or `"DELETED — no successor"`.
   - `reason`: 1-line plan reference (e.g. "V1-RETIRE Phase 2", "writegate Phase 2.A").
   - `status`: `removed` (errors / fail CI) | `pending_removal` (warnings — scheduled for migration but live callsites
     remain in flight) | `renamed` (alias of `removed`).
2. **AST walker** —
   [`unified-trading-pm/scripts/quality_gates/check_removed_symbols.py`](../../scripts/quality_gates/check_removed_symbols.py)
   parses every `.py` file in scope (excluding `.venv*` / `node_modules` / `build` / `__pycache__` / `dist` / archived
   trees). It checks three patterns per file:
   - `from <module> import <name>` where `<module>.<name>` matches a manifest entry.
   - `import <module>` where `<module>` is a removed module path.
   - Attribute access `<Receiver>.<method>(...)` where `<method>` is the last component of a manifest entry whose symbol
     has ≥3 dotted components (`module.Class.method` form), AND the receiver name matches the class name
     case-insensitively (or as snake_case — e.g. `manifest_writer.add` matches `ManifestWriter.add`). The strict
     receiver-match rule eliminates false positives like `set.add()` / `args.client` / `list.append()`.
3. **QG wiring** — `scripts/quality-gates-base/base-service.sh` STEP 5.65 invokes the checker scoped to the calling
   repo. `removed` findings fail QG (exit 1); `pending_removal` findings surface as warnings (exit 0, informational
   only). A workspace-wide sweep (no `--scope`) can be run from the workspace root to verify cross-repo cleanliness
   before landing a refactor.

### Adding a new manifest entry (when YOUR plan removes a public symbol)

In the same logical unit as the refactor commit (per
[**Commit + Push + Flip Plan Checkboxes**](../../cursor-configs/CLAUDE.md) HARD RULE):

1. Land the refactor + update every downstream consumer YOU can find via `git grep <symbol>` (Citadel § 6 Pre-Audit).
2. Add an entry to `removed_symbols_manifest.yaml` with the 6 required fields above.
3. Run `python unified-trading-pm/scripts/quality_gates/check_removed_symbols.py` from workspace root and confirm zero
   `[ERROR]` findings — any remaining error means a consumer was missed in step 1; fix it before pushing.
4. Commit the manifest update alongside the refactor.

### Maintenance burden + cadence

- The manifest grows over time but never shrinks except via deliberate cleanup of `pending_removal → removed → archive`
  transitions. Workspace-wide sweep cadence: every Plans Run To Actual Completion / Post-Plan-Phase Codex Audit pass
  reviews recent entries for status promotion.
- Adding the manifest schema to a service's QG via STEP 5.65 takes ~4 seconds per repo of overhead (per the smoke run on
  `strategy-service`); workspace-wide scan completes in <2 min on a multi-core dev machine via the `ProcessPoolExecutor`
  parallelism.
- When `pending_removal` migrates to `removed` (the successor migration plan ships), no manifest schema change is needed
  — just edit `status:` to `removed`. Reviewers at that PR confirm zero remaining workspace callsites in the QG output.

### Composes with

- [**Peripheral Script Directories Under Primary-Consumer QG**](../../cursor-configs/CLAUDE.md) — STEP 5.65 covers
  whatever Python files appear in the scoped scan; the peripheral-script rule ensures peripheral dirs (e.g.
  `e2e-testing/scripts/`) are wired to a primary-consumer service's QG so STEP 5.65 actually runs over them.
- [**Runbook Execution-Owner SSOT**](../../cursor-configs/CLAUDE.md) — STEP 5.65 catches static-import drift; the
  execution-owner SSOT catches runtime drift (e.g. external API changes).
- QG STEP 5.64 (bundled-shard cluster validation AST-walk) is the implementation precedent — STEP 5.65 follows the same
  `ast.walk()` shape applied to a different symbol-detection problem.

---

## STEP 5.67: Banned NaN-Placeholder / Bypass-`record_captured` AST-Walk

Enforces CLAUDE.md [**Honest absence vs fake placeholders**](../../cursor-configs/CLAUDE.md) +
[**No double SSOT in data-saving methodology**](../../cursor-configs/CLAUDE.md) +
[**Four-category empty-output decision**](../../cursor-configs/CLAUDE.md): the `_create_empty_output()`-style
placeholder methods — which emit NaN-OHLC placeholder bars that LOOK populated and pass the availability manifest as
`captured` — are **banned** from `base_adapter` and any equivalent base class. So is a direct `*.upload_bytes(...)`
candle write that bypasses `record_captured` (and therefore the 4-pillar write-gate + the manifest row).

**Reference incidents**: 2026-05-05 MDPS 1440-NaN-bar (1440 `open=high=low=close=None` placeholder bars per day per
`(venue, data_type)` persisted for years before hand-inspection caught them — the manifest said `captured` the whole
time); Track D audit 2026-05-11 (`tradfi/ohlcv_passthrough.py:_create_full_day_empty_output` still in the live path;
`CandleProcessingService` triple-SSOT; legacy `orchestration_writer._write_candles` overriding the canonical
`record_captured` path by MRO).

### How it works

1. **Banned-name set + candle-write path fragments** — in
   [`unified-trading-pm/scripts/quality_gates/check_banned_placeholder_methods.py`](../../scripts/quality_gates/check_banned_placeholder_methods.py):
   `BANNED_METHOD_NAMES = {_create_empty_output, _create_full_day_empty_output, _create_closed_market_candle, _maybe_write_vix_gap_placeholder}`
   — names that _describe synthesising a fake empty/closed/placeholder candle_. ( `_handle_empty_tick_data` was in the
   set on day 1 but DROPPED 2026-05-11 PM after writegate Phase 2.A reformed it into the canonical honest-handler that
   routes through `record_empty_for_shard` — it's now the _recommended_ method name, so flagging it would be noise.)
   `CANDLE_WRITE_PATH_FRAGMENTS = (orchestration_writer, output_writer, candle_write, candle_processing, ohlcv_passthrough)`
   — modules whose path indicates a candle-write context.
2. **Baseline** — `unified-trading-pm/scripts/quality_gates/banned_placeholder_methods_baseline.yaml` is a **SHRINKING
   ratchet**: every entry is a CURRENTLY-KNOWN occurrence (`status: pending_removal`) the gate tolerates as a WARNING
   (exit-clean). Per-entry keys: `repo`, `file` (repo-relative), `method` (banned name OR `upload_bytes`), `status`,
   `successor`. As of 2026-05-11 PM the baseline holds **2** entries (was 8 — writegate Phase 2.A P0-2 surgery deleted 4
   occurrences and reformed `_maybe_write_vix_gap_placeholder`). REMOVE an entry the moment its successor
   deletes/renames the occurrence; never ADD entries — a new placeholder method is a bug, not a baseline item.
3. **AST walker** — parses every `.py` file in scope (excluding `.venv*` / `node_modules` / `build` / `dist` /
   `__pycache__` / `scripts/` / `tests/` / archived trees) and flags: (a) `def`/`async def <name>` for `<name>` in the
   banned set; (b) `ast.Call` to `*.upload_bytes(...)` (attribute-method form) in a module whose path matches a
   candle-write fragment.
4. **QG wiring** — `scripts/quality-gates-base/base-service.sh` STEP 5.67 invokes the checker scoped to the calling repo
   (`--workspace-root <ws> --scope <repo> --source-dir <pkg>`). Baselined occurrences → warnings (exit 0); a
   non-baselined occurrence → ERROR + `file:line` + the baseline's `default_successor` → exit 1. A workspace-wide sweep
   (no `--scope`) walks every immediate sub-dir with a `pyproject.toml`. If the checker file is absent (older PM
   checkout), the STEP is skipped clean. Unit tests: `scripts/quality_gates/test_check_banned_placeholder_methods.py`.

### Adding a new banned occurrence? Don't — fix it instead.

There is no "add a new entry" workflow (unlike STEP 5.65's manifest, which grows). If STEP 5.67 fails on YOUR code, the
correct response is: delete the placeholder method and emit `record_empty(reason=...)` /
`record_expected_empty(reason=…)` / `record_captured()` per the
[Four-category empty-output decision](../../cursor-configs/CLAUDE.md), OR (for an `upload_bytes` flag) route the candle
write through the canonical `CandleWriteMixin._write_candles` → `canonical_writer` → `record_captured` path. The only
legitimate baseline edit is **removal** of an entry when its `successor` lands, OR (rare) updating the `file:` path of
an existing baselined occurrence that moved files in the same commit that moves it.

### Maintenance burden + cadence

- The baseline only shrinks. Workspace-wide sweep cadence: every Post-Plan-Phase Codex Audit / Plans Run To Actual
  Completion pass checks whether any `pending_removal` entry's successor has landed (→ remove the entry).
- Residual baseline as of 2026-05-11 PM: `orchestration_writer.py:_maybe_write_vix_gap_placeholder` (REFORMED — now
  routes through `record_empty_for_shard(reason=EXPECTED_KNOWN_SOURCE_GAP)`; only the misnomer name keeps it flagged; a
  cosmetic rename in writegate Phase 2.A clears it) + `output_writer_service.py:upload_bytes` (DEAD CODE —
  `OutputWriterService` is not instantiated on any live path; deleting the dead class clears it).

### Composes with

- [**Honest absence vs fake placeholders**](../../cursor-configs/CLAUDE.md) — this STEP is the static enforcement of
  that rule's "Empty placeholders that look populated are worse than missing data" principle. The runtime defence is the
  4-pillar `record_captured` write-gate; STEP 5.67 catches the placeholder-method shape at PR time.
- [**Four-category empty-output decision**](../../cursor-configs/CLAUDE.md) — the banned methods are exactly the
  anti-pattern that decision replaces (A: `record_empty(reason=…)` / B: `record_failed(UpstreamTimestampBiasError)` / C:
  `record_failed(MalformedTickFieldError)` / D: zero-activity bars + `record_captured`).
- STEP 5.65 (removed-symbol AST-walk) + STEP 5.64 (bundled-shard cluster validation AST-walk) are the implementation
  precedents — STEP 5.67 follows the same baseline-aware-ratchet + `ast.walk()` shape applied to the placeholder-method
  detection problem.
- Track D audit findings doc (`plans/archive/issues/wave3x_track_d_findings_2026_05_11.md` P0-2) — the audit that seeded
  the baseline; writegate Phase 2.A is the successor that shrinks it.

---

## STEP 5.70: Explicit `pipeline_mode=` at every `record_*` call (manifest v8)

Enforces [`manifest_schema_final_gate_2026_05_09.md`](../../plans/active/manifest_schema_final_gate_2026_05_09.md) Phase 4
"explicit-or-fail" contract + CLAUDE.md [**Live = batch (CRITICAL)**](../../cursor-configs/CLAUDE.md): the only legitimate
difference between batch and live for a given `(asset_group, data_type)` is which SOURCE serves it — so the manifest must
record that source. Manifest schema v8 makes `pipeline_mode` a first-class column; this ratchet keeps it explicit at the
write boundary. Every `ManifestWriter.record_captured()` / `record_empty()` / `record_failed()` /
`record_expected_unattempted()` call (and the legacy `ManifestWriter.add()` path) MUST pass an explicit
`pipeline_mode=PipelineMode.<source>` kwarg matching the UAC `SOURCE_PRIORITY` top entry. Implicit / orchestrator-inherited
`pipeline_mode`, or `**kwargs` that silently swallow it, is the anti-pattern this catches at PR time.

**Reference incident**: the same 2026-05-05 MDPS data-correctness class as STEP 5.67 — when the manifest can't say which
source produced a row, batch-vs-live reconciliation can't tell whether a divergence is a real alpha gap or just a
slower-source artefact. The pre-audit (PM@`237d00b7` slot 2 sub-agent) found 26 MTDS files / 102 callsites with an
inherited-or-implicit `pipeline_mode`; the slot-2 Phase 4 sweep cleared MDPS / instruments / deployment-api; the residue
is baselined pending the MTDS sweep (gated on the operator's PipelineMode-enum triage) + the features-consolidation sweep.

### How it works

1. **Record-method name set + whitelist marker** — in
   [`unified-trading-pm/scripts/quality_gates/check_pipeline_mode_explicit_at_record_calls.py`](../../scripts/quality_gates/check_pipeline_mode_explicit_at_record_calls.py):
   `RECORD_METHOD_NAMES` = `record_captured` / `record_empty` / `record_failed` / `record_expected_unattempted` / `add`
   (the legacy path). A call passes if and only if it has a literal `pipeline_mode=` keyword, OR the call's source line
   carries the inline marker `# QG-allow: pipeline-mode-not-applicable` (the rare legitimate exemption — e.g. a base-class
   method that re-forwards `**kwargs`).
2. **Baseline** — `unified-trading-pm/scripts/quality_gates/pipeline_mode_explicit_baseline.yaml` is a **SHRINKING ratchet**:
   each entry is a currently-known occurrence keyed `(repo, file, line, method)` with `status` (`pending_phase_4_mtds` /
   `pending_phase_4_features`) + `successor` (the plan phase that clears it). As of 2026-05-12 the baseline holds **114**
   entries (97 market-tick-data-service + 6 features-service + 11 unified-trading-library). DELETE an entry the moment its
   successor sweep ships the explicit kwarg; never ADD one — a new implicit `record_*` call is a bug, not a baseline item.
3. **AST walker** — parses every `.py` in scope (excluding `.venv*` / `node_modules` / `build` / `dist` / `__pycache__` /
   `scripts/` / `tests/`) and flags any `ast.Call` whose `func` is an `ast.Attribute` named in `RECORD_METHOD_NAMES` and
   whose keyword set lacks `pipeline_mode` (and whose line lacks the whitelist marker). Counts only real `Call` nodes — a
   docstring / comment / dict-key / string-literal reference to a method name does not trip it (the naive
   `grep -L "pipeline_mode="` approach returned 7 false positives; the AST walk is authoritative).
4. **QG wiring** — `scripts/quality-gates-base/base-service.sh` STEP 5.70 invokes the checker scoped to the calling repo
   (`--workspace-root <ws> --scope <repo> --source-dir <pkg>`). Baselined occurrences → warnings (exit 0); a non-baselined
   occurrence → ERROR + `file:line` + the baseline's `default_successor` → exit 1. A workspace-wide sweep (no `--scope`)
   walks every immediate sub-dir with a `pyproject.toml`. If the checker file is absent (older PM checkout), the STEP is
   skipped clean. Unit tests: `scripts/quality_gates/test_check_pipeline_mode_explicit_at_record_calls.py` (11 cases).

### Adding a new occurrence? Don't — fix it instead.

If STEP 5.70 fails on YOUR code, pass `pipeline_mode=PipelineMode.<source>` for the UAC `SOURCE_PRIORITY` top entry of the
`(asset_group, data_type)` you're writing (the source that would actually serve that data in live mode — `BATCH_DATABENTO`
/ `BATCH_TARDIS` / `BATCH_API_FOOTBALL` / `BATCH_INSTRUMENTS_SERVICE` for self-published catalog rows, etc.). The only
legitimate baseline edits are **removal** when a successor sweep lands, or updating the `line:` of an existing baselined
occurrence that shifted in the same commit. If a UAC `PipelineMode` enum member genuinely doesn't exist for your source
yet, file the gap (precedent: `mtds_pipeline_mode_sweep_ambiguities_2026_05_12.md`) and stamp the closest documented
workaround (precedent: instruments-service stamps `BATCH_API_FOOTBALL` for footystats pending the enum extension).

### Composes with

- [**Live = batch (CRITICAL)**](../../cursor-configs/CLAUDE.md) — STEP 5.70 is the static enforcement of "the only
  legitimate batch/live diff is which SOURCE serves a given `(asset_group, data_type)`": no recorded source ⇒ unverifiable
  batch-vs-live recon.
- [**Availability manifest v5+**](../../cursor-configs/CLAUDE.md) + [`codex/02-data/availability-manifest-and-data-status.md`](../02-data/availability-manifest-and-data-status.md)
  — `pipeline_mode` joins the v8 manifest column set alongside `service_emission_state` /
  `last_emission_decision_at` / `expected_window_completeness_fraction`; Phase 4.DEFAULT-REMOVAL drops the transitional
  `None` defaults from the 5 `record_*` signatures so the column is explicit-or-fail.
- STEP 5.67 (banned NaN-placeholder AST-walk) + STEP 5.65 (removed-symbol AST-walk) + STEP 5.64 (bundled-shard cluster
  validation AST-walk) are the implementation precedents — STEP 5.70 follows the same baseline-aware-ratchet + `ast.walk()`
  shape applied to the explicit-pipeline-mode problem.
- `manifest_schema_final_gate_2026_05_09.md` Phase 4.MTDS / Phase 4.FEATURES / Phase 4.DEFAULT-REMOVAL — the successors
  that shrink the baseline to zero; Phase 4.GREP-VERIFY is the phase that shipped this checker + baseline.

---

## SSOT Alignment Validation (Documentation Quality Gates)

**Purpose:** Prevent documentation drift **before commit** by validating alignment across Codex docs, UTD configs, and
Epics.

### What It Catches

The `validate-alignment.py` script runs as a pre-commit hook in `unified-trading-codex` and checks:

1. **Banned Terms**
   - ❌ Non-canonical bucket patterns (e.g., `gs://market-data-raw/` instead of
     `gs://market-data-tick-{category}-{project_id}/`)
   - ❌ `os.getenv()` in service code (use `UnifiedCloudServicesConfig`)

2. **Lifecycle Event Names**
   - ❌ Non-canonical event names in observability docs (e.g., `INGESTING_DATA` instead of `DATA_INGESTION_STARTED`)
   - ✅ Only canonical events from `03-observability/lifecycle-events.md`

3. **MVP Scope**
   - ❌ Non-MVP venues referenced in active epics (e.g., DYDX, OKX)
   - ✅ Only MVP venues from `11-project-management/mvp-universe.yaml`

4. **Bucket Naming Patterns**
   - ❌ Hardcoded bucket names (e.g., `gs://features-sports/`)
   - ✅ Parameterized patterns (e.g., `gs://features-{category}-{project_id}/`)

5. **Venue Name Canonicalization**
   - ❌ Generic names (e.g., `BINANCE` instead of `BINANCE-SPOT`/`BINANCE-FUTURES`)
   - ✅ Canonical names from `configs/venues.yaml`

6. **Sharding Dimensions**
   - ❌ Drift between `configs/sharding.{service}.yaml` and service `.cursorrules`
   - ✅ Dimensions match across both sources

7. **Start Dates**
   - ❌ Mismatches between `configs/expected_start_dates.yaml` and Codex docs
   - ✅ All references align

### Pre-Commit Hook (Blocks Bad Commits)

The validation runs **automatically** via pre-commit hook in `unified-trading-codex`:

```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: alignment-validation
      name: Validate SSOT Alignment
      entry: python scripts/validate-alignment.py --check-drift
      language: python
      pass_filenames: false
      always_run: true
      additional_dependencies: [pyyaml]
```

**Behavior:**

- Exit 0 → Commit allowed
- Exit 1 → Commit **BLOCKED** with detailed drift report

**Example blocked commit:**

```bash
$ git commit -m "Update market-data epic"

Validate SSOT Alignment..........................................................Failed
- hook id: alignment-validation
- exit code: 1

================================================================================
SSOT Alignment Validation (Drift Detection)
================================================================================

⚠️  Drift detected: 2 issues found

Banned Term (example):
  - some-epic.md:42 - Non-canonical bucket pattern
```

### GitHub Actions (PR Checks)

Validation also runs in CI for every PR:

```yaml
# .github/workflows/alignment-validation.yml
name: Alignment Validation
on:
  pull_request:
    branches: [main]
```

**On failure:**

- PR check marked as failed
- Bot posts comment with instructions
- Blocks auto-merge until fixed

### Manual Validation

Run the validation script manually:

```bash
cd unified-trading-codex
python scripts/validate-alignment.py --check-drift
```

**Exit codes:**

- `0` - All sources aligned ✅
- `1` - Drift detected ⚠️

### Troubleshooting

**Problem:** Pre-commit hook blocks my commit

**Solution:**

1. Read the drift report carefully - it shows exact file:line violations
2. Fix the issues (use suggested replacements if provided)
3. Try committing again

**Problem:** I need to commit historical documentation with non-canonical patterns

**Solution:** Historical docs may be exempt. Only active epics/docs are checked. Update validation script's allowed
paths if needed.

**Problem:** False positive on a legitimate use case

**Solution:** Update the validation script's allowed paths or patterns. All checks have configurable exceptions.

**Problem:** `MM` git status on a file after `git add`, or
`[WARNING] Stashed changes conflicted with hook auto-fixes... Rolling back fixes.`

**Root cause:** `ruff` and `prettier` reformat the same file differently in sequence. The `prek` stash system stashes
other unstaged files, hooks modify the staged file, then prek tries to restore and conflicts arise.

**Solution — Formatter Conflict Resolution Protocol:**

1. **Pre-format ALL formatters before `git add`:**
   ```bash
   npx prettier --write <file>          # JSON, YAML, MD, etc.
   .venv/bin/ruff format <file>         # Python only
   .venv/bin/ruff check <file> --fix    # Python only
   ```
2. **Isolate the commit** — stage ONLY the target file; do NOT `git add -A` when other unstaged files exist.
3. **If `MM` persists after a commit attempt** — hooks modified the file; re-stage and retry:
   ```bash
   git add <file>
   git commit -m "..."
   ```
4. **For `.basedpyright-baseline.json`** — always run `npx prettier --write` AFTER `--writebaseline`, BEFORE `git add`:
   ```bash
   .venv/bin/basedpyright <src>/ --baselinefile .basedpyright-baseline.json --writebaseline
   npx prettier --write .basedpyright-baseline.json
   git add .basedpyright-baseline.json
   git commit -m "..."
   ```

**Prevention:** The QG template `quality-gates-service-template.sh` step [1] AUTO-FIX now runs prettier before ruff so
local QG runs pre-format all file types before any commit. The canonical rule is in
`unified-trading-pm/cursor-rules/documentation/prettier-docs-formatting.mdc`.

---

## Canonical Template (NEW)

All `scripts/quality-gates.sh` files MUST align to the canonical template at:

```
unified-trading-pm/codex/06-coding-standards/quality-gates-template.sh
```

**Required Features:**

1. **Environment Validation**
   - Python 3.13 version check (fail if not `>=3.13,<3.14`)
   - `uv.lock` existence check
   - `.venv` virtual environment detection
   - `ripgrep` availability check (REQUIRED - exit 1 if missing)
   - Ruff 0.15.0 version verification

2. **Test Execution**
   - Git-aware mode (test only changed files when uncommitted changes detected)
   - `pytest-xdist` for parallel test execution (`-n auto`)
   - `pytest-cov` for coverage reporting (`--cov-fail-under=70`)
   - All 4 test tiers: unit, integration, e2e, smoke
   - Quick mode support (`--quick` skips e2e/smoke)

3. **Lifecycle Event Validation**
   - MUST verify `tests/unit/test_event_logging.py` exists
   - Test validates all 11 mandatory lifecycle events in source code:
     - STARTED, VALIDATION_STARTED, VALIDATION_COMPLETED, VALIDATION_FAILED
     - DATA_INGESTION_STARTED, DATA_INGESTION_COMPLETED
     - PROCESSING_STARTED, PROCESSING_COMPLETED
     - UPLOAD_STARTED, UPLOAD_COMPLETED
     - STOPPED, FAILED

4. **Coding Standards Enforcement (Chapter 6)**
   - No `print()` statements (use `logger.info()`)
   - No `os.getenv()` outside `config.py` (use config classes)
   - No naive `datetime.now()` (use `datetime.now(timezone.utc)`)
   - No bare `except:` (use specific exceptions or decorators)
   - No `google.cloud` imports (use `unified_trading_services` abstractions)
   - No `requests` in async code (use `aiohttp`)
   - No `asyncio.run()` in loops (use `asyncio.gather()`)
   - No `time.sleep()` in async functions (use `asyncio.sleep()`)

5. **Test Comprehensiveness Checks**
   - `test_config.py` must exist and be >50 lines (not just import checks)
   - `test_startup_validation.py` recommended
   - No placeholder tests (`assert True`, `pass`, empty functions)

**Migration Guide:**

When aligning existing `quality-gates.sh` to template:

1. Copy template structure (environment, linting, testing, codex compliance phases)
2. Update `SOURCE_DIR` and `TEST_PATHS` variables for your service
3. Add missing checks (ripgrep, Python version, test comprehensiveness)
4. Remove legacy patterns (manual `.venv` creation, old pytest flags)
5. Test locally: `bash scripts/quality-gates.sh`
6. Verify CI parity: Check GitHub Actions and Cloud Build use same checks

## Repo-Type-Specific Base Scripts

All per-repo `scripts/quality-gates.sh` are thin config stubs sourcing a shared base from PM. The base scripts are the
SSOT — never copy gate logic into a per-repo file.

| Repo type                  | Base script (in unified-trading-pm)          | Notes                                                                      |
| -------------------------- | -------------------------------------------- | -------------------------------------------------------------------------- |
| Service                    | `scripts/quality-gates-base/base-service.sh` | Full Python checks: ruff, pytest, basedpyright, codex compliance           |
| API service                | `scripts/quality-gates-base/base-service.sh` | Same as service — API services use the service base                        |
| Library                    | `scripts/quality-gates-base/base-library.sh` | Same checks as service; unit-only tests by default                         |
| Docs-only / infrastructure | `scripts/quality-gates-base/base-codex.sh`   | Markdown lint, prettier check, link validation; no pytest, no basedpyright |

**Stub templates** for each repo type are documented in `unified-trading-pm/scripts/quality-gates-base/README.md`. For a
new repo: copy the appropriate stub template, set the required variables, and commit. Do not copy any gate logic from
another repo.

---

## Quality Gate Performance

Quality gates must complete within 120 seconds to maintain developer productivity. Several performance optimizations are
available for environments where type checking is slow or when doing rapid iterations.

### --skip-typecheck Flag

Skip the type checking phase when you need faster iterations:

```bash
bash scripts/quality-gates.sh --skip-typecheck
```

**When to Use:**

- Rapid development iterations where type errors are not the focus
- CI environments where type checking is done separately
- Emergency hotfixes where speed is critical

**When NOT to Use:**

- Before creating PRs (type checking is required)
- In production deployments
- When making significant refactoring changes

### Three-Phase Pattern (current)

Quickmerge runs quality gates in three phases internally — no manual invocation needed:

```bash
# Phase 1: lint auto-fix (fast — ruff/eslint --fix, no tests/typecheck/build)
bash scripts/quality-gates.sh --lint --fix

# Phase 2: lint verify — abort if unfixable lint remains
bash scripts/quality-gates.sh --no-fix --lint

# Phase 3: full gates minus lint — tests + typecheck + codex run exactly once
bash scripts/quality-gates.sh --no-fix --skip-lint
```

**Benefits:**

- Lint failures caught fast in Phase 2 before slow tests start
- Tests and typecheck run exactly once (not twice as in the old two-phase model)
- ~2-3 minutes saved per quickmerge run on a typical service repo

### BASEDPYRIGHT_CACHE_DIR

All quality gate templates automatically set up caching for basedpyright to improve performance:

```bash
export BASEDPYRIGHT_CACHE_DIR="${TMPDIR:-/tmp}/basedpyright-cache/${SERVICE_NAME:-$(basename "$PWD")}"
mkdir -p "$BASEDPYRIGHT_CACHE_DIR"
```

**Cache Benefits:**

- Significantly faster subsequent runs on the same codebase
- Reduces type checking time from 60-120s to 10-30s on repeat runs
- Automatically cleans up via TMPDIR on system restart

### run_timeout Helper

`run_timeout` is available in two forms — both use identical logic:

**1. Shell function (inside quality-gates.sh):** Each repo's `quality-gates.sh` sources
`unified-trading-pm/scripts/quality-gates-base/base-service.sh`, which defines:

```bash
run_timeout() {
    local secs=$1; shift
    if command -v timeout &>/dev/null; then timeout "$secs" "$@"
    elif command -v gtimeout &>/dev/null; then gtimeout "$secs" "$@"
    elif command -v perl &>/dev/null; then perl -e 'alarm shift; exec @ARGV' -- "$secs" "$@"
    else "$@"; fi
}
```

**2. Standalone binary (`.venv-workspace/bin/run_timeout`):** Installed by `workspace-bootstrap.sh` from
`unified-trading-pm/scripts/shared/run_timeout`. Available in any shell context — background subshells, CI steps, agent
tasks — without sourcing `quality-gates.sh`. Use this when calling `basedpyright` outside of the quality-gates pipeline.

**Cross-Platform Support:**

- Linux: Uses `timeout` command
- macOS: Uses `gtimeout` (via `brew install coreutils`) or `perl` fallback
- Prevents infinite hangs in type checking
- 120-second timeout prevents zombie processes

**Usage:**

```bash
run_timeout 120 basedpyright unified_trading_services/
```

**Note:** The `perl` fallback is essential for macOS environments where GNU coreutils may not be installed. If
`run_timeout` is not found (exit 127), run `workspace-bootstrap.sh` to install the standalone binary — do not source
`quality-gates.sh` as a workaround.

---

## Python Version Consistency

**CRITICAL:** All environments (local, GitHub Actions, Cloud Build) MUST use the same Python version.

| Environment            | Configuration                                                       | Python Version       |
| ---------------------- | ------------------------------------------------------------------- | -------------------- |
| **pyproject.toml**     | `requires-python = ">=3.13,<3.14"`                                  | Source of truth      |
| **GitHub Actions**     | `python-version-file: 'pyproject.toml'`                             | Reads from pyproject |
| **Quickmerge (local)** | Activates `.venv` before quality gates; else derives from pyproject | Matches pyproject    |
| **Quality-gates.sh**   | Inherits from quickmerge (venv already activated) or user-managed   | -                    |

### Run Quality Gates = Single Command (No Setup First)

`./scripts/quality-gates.sh` is self-contained. It automatically:

- Runs `uv lock` when `pyproject.toml` changes (creates/updates `uv.lock`; cross-platform; fast when unchanged)
- Creates `.venv` if missing (uv venv, respects `pyproject.toml` requires-python)
- Activates venv
- Bootstraps uv (`pip install uv` — the only pip install)
- Installs unified-trading-services from workspace if present
- Installs project deps via `uv pip install -e ".[dev]"`
- Runs ruff + pytest

No need to run setup, `uv sync`, or `source .venv/bin/activate` beforehand. Skips venv creation in CI (GitHub Actions,
Cloud Build use their own setup).

### Quickmerge Activates Venv

Quickmerge sources `.venv/bin/activate` (macOS/Linux) or `.venv/Scripts/activate` (Windows) before running quality
gates. If no venv exists, quality-gates.sh creates it.

### CI Reads Python from pyproject.toml

All `quality-gates.yml` workflows use `python-version-file: 'pyproject.toml'` so CI stays in sync with the project.

### Local Python Detection (when running quality-gates directly)

Quality-gates.sh creates and activates venv when run locally. No manual setup needed.

**Install Python 3.13+**:

```bash
# Option 1: pyenv (recommended)
pyenv install 3.13.0
pyenv local 3.13.0

# Option 2: Homebrew
brew install python@3.13
```

**See also**: `.cursor/rules/python-version-consistency.mdc`

---

## What quality-gates.sh Does

### Step 0: Config Validation

- Checks `cloudbuild.yaml` for unescaped shell variables (`$VAR` instead of `$$VAR`)
- Verifies `pyproject.toml` Python version matches expected (`>=3.13,<3.14` for all services)

### Step 1: Auto-Fix (Phase 1)

Only runs when `--no-fix` is NOT passed (default behavior):

```bash
# Format all source files
ruff format {source_dir}/ tests/

# Fix auto-fixable lint issues
ruff check --fix {source_dir}/ tests/
```

This handles import sorting, trailing whitespace, unused imports, and formatting. Most issues are resolved here.

### Step 2: Linting (Phase 2)

Always runs. Verifies no remaining issues:

```bash
ruff check {source_dir}/ tests/
```

If this fails after auto-fix, the issue requires manual intervention (e.g., undefined variable, bare except).

### Step 3: Tests

Runs all test categories in sequence:

```bash
# Unit tests
pytest tests/unit/ -v --tb=short --timeout=60

# Integration tests (excluding performance, API, live, download tests)
pytest tests/integration/ -v --tb=short --timeout=120 \
    --ignore=tests/integration/test_performance.py \
    -k "not api and not live and not download"

# E2E tests
pytest tests/e2e/ -v --tb=short --timeout=180

# Smoke tests (shard combinatorics)
pytest tests/smoke/ -v --tb=short --timeout=180
```

Missing test directories are silently skipped.

---

## Usage

```bash
cd {service-directory}

# Full run (auto-fix + verify + tests) -- default
bash scripts/quality-gates.sh

# Verify only (no auto-fix) -- CI mode
bash scripts/quality-gates.sh --no-fix

# Linting only (no tests)
bash scripts/quality-gates.sh --lint

# Tests only (no linting)
bash scripts/quality-gates.sh --test

# Quick mode (unit tests only)
bash scripts/quality-gates.sh --quick
```

---

## Two-Phase Workflow

The standard workflow runs quality gates twice:

```bash
# Phase 1: Auto-fix
bash scripts/quality-gates.sh

# Phase 2: Verify
bash scripts/quality-gates.sh --no-fix
```

Quickmerge runs both phases internally before creating branches or PRs. If Phase 2 fails, the script exits immediately
and does NOT proceed with the merge.

---

## Ruff Version Consistency [CRITICAL]

**All three stages MUST use the exact same ruff version** to prevent formatting conflicts and CI failures:

| Stage              | Environment      | Version Source                             | Current        |
| ------------------ | ---------------- | ------------------------------------------ | -------------- |
| **Local**          | Development      | `pyproject.toml` dev deps                  | `ruff==0.15.0` |
| **Local**          | Pre-commit hooks | `.pre-commit-config.yaml`                  | `v0.15.0`      |
| **GitHub Actions** | PR validation    | `quality-gates.yml`                        | `ruff==0.15.0` |
| **Cloud Build**    | Image validation | Docker image includes ruff in `[dev]` deps | `ruff==0.15.0` |

### Three-Stage Consistency Model

1. **Local Stage**: Developer runs `quality-gates.sh` which uses ruff from venv (installed via `pyproject.toml` dev
   deps). Pre-commit hooks use version from `.pre-commit-config.yaml`.

2. **GitHub Actions Stage**: PR validation runs `quality-gates.yml` which installs `ruff==0.15.0` explicitly.

3. **Cloud Build Stage**: Tests run INSIDE the Docker image, which includes ruff from
   `uv pip install --system -e ".[dev]"` (pulls from `pyproject.toml`).

### Verifying Consistency

```bash
cd deployment-service
./scripts/check-ruff-versions.sh
```

This script verifies:

- `pyproject.toml` dev deps have `ruff==0.15.0`
- `.pre-commit-config.yaml` has `rev: v0.15.0`
- GitHub Actions workflows install `ruff==0.15.0`

### Updating Ruff Version

When updating ruff, change it in ALL locations:

1. `pyproject.toml` in every service: `"ruff==X.Y.Z"` in dev deps
2. `.pre-commit-config.yaml` in every service: `rev: vX.Y.Z`
3. Reinstall hooks: `pre-commit install --install-hooks`
4. Rebuild Docker images (Cloud Build will pick up new version from `[dev]` deps)

Convenience script:

```bash
cd deployment-service
./scripts/update-precommit-hooks.sh
```

**Why this matters**: Different ruff versions format code differently. If local uses 0.14.0 but CI uses 0.15.0, code
that passes locally will fail in CI.

---

## Ruff Configuration

Standard `pyproject.toml` ruff config:

```toml
[tool.ruff]
line-length = 120
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "W", "I"]
ignore = [
    "E501",  # Line too long - handled by ruff format
    "E722",  # Bare except - allowed in scripts only
]

[tool.ruff.lint.per-file-ignores]
"scripts/*" = ["E722"]
```

Rule categories:

- **E**: pycodestyle errors
- **F**: pyflakes (undefined names, unused imports)
- **W**: pycodestyle warnings
- **I**: isort (import sorting)

---

## Type Checking Standards (pyrightconfig.json)

All repos MUST use `typeCheckingMode: "strict"` in `pyrightconfig.json`. **All diagnostic rules must be `"error"`** —
including `reportAny`, `reportUnknownMemberType`, `reportUnknownVariableType`, `reportUnknownParameterType`,
`reportUnknownArgumentType`, and `reportMissingParameterType`. No cloud SDK exceptions: use
`# pyright: ignore[reportXxx]` inline for unavoidable third-party stub gaps rather than relaxing the global config.

**Standard pyrightconfig.json for all repos:**

```json
{
  "typeCheckingMode": "strict",
  "reportMissingTypeStubs": false,
  "reportAny": "error",
  "reportUnknownMemberType": "error",
  "reportUnknownVariableType": "error",
  "reportUnknownParameterType": "error",
  "reportUnknownArgumentType": "error",
  "reportMissingParameterType": "error"
}
```

**NEVER use `--level warning`** in quality-gates.sh basedpyright invocations. The correct invocation is:

```bash
run_timeout 120 basedpyright "$SOURCE_DIR/"
```

`--level warning` suppresses `information`-level output but also masks warnings configured as blocking in
pyrightconfig.json. Always let pyrightconfig.json control the severity.

## Library pyproject.toml: basedpyright Config

**Python libraries** MUST include `[tool.basedpyright]` with `typeCheckingMode = "strict"` and all diagnostic rules set
to `"error"`. Quality gates verify this config exists and basedpyright enforces it.

Add to `pyproject.toml`:

```toml
[tool.basedpyright]
include = ["<package_name>"]   # e.g. "unified_trading_services"
exclude = ["tests", "**/__pycache__", ".venv*", "build", "dist"]
pythonVersion = "3.13"
typeCheckingMode = "strict"
reportMissingTypeStubs = false
reportAny = "error"
reportUnknownVariableType = "error"
reportUnknownParameterType = "error"
reportUnknownMemberType = "error"
reportUnknownArgumentType = "error"
reportMissingParameterType = "error"
```

**Template:** `quality-gates-library-template.sh` runs a config check; see `instruments-service/pyproject.toml` for
reference.

---

## STEP 5.22: basedpyright Baseline Suppression [ERROR policy — escalated 2026-03-10]

`.basedpyright-baseline.json` silently hides type errors from CI by telling basedpyright to ignore previously-known
violations. The baseline mechanism is intended for one-time migration only — never for ongoing suppression.

### Policy (effective 2026-03-10)

| Baseline state                        | STEP 5.22 result |
| ------------------------------------- | ---------------- |
| File absent                           | PASS (clean)     |
| Present + 0 suppressed errors         | PASS (harmless)  |
| Present + N suppressed errors (N > 0) | **ERROR (FAIL)** |

Documentation in `QUALITY_GATE_BYPASS_AUDIT.md` does **not** exempt baseline suppression. The previous
WARN-if-documented policy has been removed. Any non-zero suppression is a hard block.

### How the gate counts suppressions

The gate uses the `files` key of the baseline JSON (the format written by `basedpyright --writebaseline`):

```json
{ "files": { "./path/to/file.py": [{ "code": "reportXxx", ... }] } }
```

Total suppressed = sum of error-entry lists across all files. If the baseline exists but `files` is empty (or the file
contains only an empty object), count = 0 and the gate passes.

### Remediation steps

1. Run basedpyright without the baseline flag to see all suppressed errors:
   ```bash
   .venv-workspace/bin/basedpyright <source_dir>/
   ```
2. Fix each type error. Common patterns: add explicit return types, replace `Any` with specific types, remove
   `# type: ignore` comments that paper over real issues.
3. Once basedpyright reports 0 errors, delete the baseline file:
   ```bash
   rm .basedpyright-baseline.json
   git rm .basedpyright-baseline.json
   ```
4. If the baseline currently has 0 suppressed errors, it is safe to delete without fixing anything.

### Pre-commit formatter note

When writing a new baseline (during initial migration only), always run prettier immediately after:

```bash
.venv-workspace/bin/basedpyright <src>/ --baselinefile .basedpyright-baseline.json --writebaseline
npx prettier --write .basedpyright-baseline.json
git add .basedpyright-baseline.json
```

The `prettier` step prevents `MM` git conflicts from the pre-commit hook reformatting the JSON.

### SSOT

The gate logic lives in:

- `unified-trading-pm/scripts/quality-gates-base/base-service.sh` — STEP 5.22 block
- `unified-trading-pm/scripts/quality-gates-base/base-library.sh` — STEP 5.22 block

---

## CI Parity [IMPLEMENTED]

Quality gates are identical across all three stages:

```
Local (scripts/quality-gates.sh)
  = GitHub Actions (.github/workflows/quality-gates.yml)
  = Cloud Build (cloudbuild.yaml - tests run inside Docker image)
```

### Key Parity Rules

- **Same Python version** (3.13) across all services
- **Same ruff version** (`0.15.0`) - see Ruff Version Consistency section
- **Same test commands** (pytest with identical flags)
- **Same timeout values** (60s unit, 120s integration, 180s e2e)
- **No bypasses**: No `|| true` or `continue-on-error: true` in CI
- **Pytest exit code 5**: (no tests collected) treated as success, not failure

### Package Manager Standard: UV

**All environments use `uv` for faster, deterministic installs:**

```bash
# Dockerfiles
RUN uv pip install --system -e ".[dev]"

# Local (if not in venv)
uv pip install -e ".[dev]"

# CI (GitHub Actions)
uv pip install -e ".[dev]"
```

**Why UV over pip:**

- 10-100x faster than pip
- Deterministic resolution
- Better error messages
- Handles `pyproject.toml` native build systems

### Cloud Build Architecture: Test-in-Image

**Cloud Build tests the artifact you deploy** - no git clones:

```yaml
steps:
  # Step 1: Configure Docker auth
  - name: "gcr.io/cloud-builders/gcloud"
    id: "configure-docker"
    args: ["auth", "configure-docker", "asia-northeast1-docker.pkg.dev", "--quiet"]

  # Step 2: Ensure artifact repo exists
  - name: "gcr.io/cloud-builders/gcloud"
    id: "ensure-repo"
    entrypoint: "bash"
    args:
      [
        "-c",
        "gcloud artifacts repositories describe {repo} --location=asia-northeast1 || gcloud artifacts repositories
        create {repo} ...",
      ]

  # Step 3: Pull base image (auth required for FROM directive)
  - name: "gcr.io/cloud-builders/docker"
    id: "pull-base-image"
    args:
      ["pull", "asia-northeast1-docker.pkg.dev/$PROJECT_ID/unified-trading-services/unified-trading-services:latest"]
    waitFor: ["configure-docker"]

  # Step 4: Build image (includes code + tests + dev deps)
  - name: "gcr.io/cloud-builders/docker"
    id: "build"
    args: ["build", "-t", "{image}:$SHORT_SHA", "."]
    waitFor: ["pull-base-image", "ensure-repo"]

  # Step 5: Run quality gates INSIDE image
  # CRITICAL: Use --entrypoint "" to clear the image's default ENTRYPOINT (python -m service).
  # Then run /bin/bash -c "..." explicitly. --entrypoint bash does NOT work reliably in Cloud Build.
  - name: "gcr.io/cloud-builders/docker"
    id: "quality-gates"
    entrypoint: "bash"
    args:
      - "-c"
      - |
        docker run --rm --entrypoint "" \
          -e CLOUD_BUILD=true -e CLOUD_MOCK_MODE=true -e GCP_PROJECT_ID=$PROJECT_ID \
          {image}:$SHORT_SHA \
          /bin/bash -c "scripts/quality-gates.sh --no-fix --quick"
    waitFor: ["build"]

  # Step 6: Push ONLY if tests pass
  - name: "gcr.io/cloud-builders/docker"
    id: "push"
    args: ["push", "{image}"]
    waitFor: ["quality-gates"]
```

**Benefits:**

- Tests the exact artifact that deploys to production
- No GitHub token needed (no private repo clones)
- Faster builds (~2-3 min saved)
- Guaranteed prod parity

**Image Requirements:**

- `Dockerfile` must include: `RUN uv pip install --system -e ".[dev]"`
- Dev deps include: `pytest`, `pytest-xdist`, `ruff==0.15.0`
- Image must copy: source code, tests, `scripts/quality-gates.sh`

### Shared Libraries: Idempotent Package Publishing

**For shared libraries** (`unified-trading-services`, `unified-trading-library`, etc.), Cloud Build must publish Python
packages to Artifact Registry **idempotently** and **enforce version uniqueness**.

**Problem:** Artifact Registry rejects duplicate package versions (400 Bad Request). Without proper handling:

- Re-running builds on same commit → fails
- Changing code without version bump → stale package published
- No feedback loop for version management

**Solution:** Two-step validation in `cloudbuild.yaml`:

```yaml
# Step 7: Store build metadata (version -> commit mapping)
- name: "gcr.io/google.com/cloudsdktool/cloud-sdk:alpine"
  id: "store-metadata"
  entrypoint: "bash"
  args:
    - "-c"
    - |
      set -e
      apk add --no-cache python3

      # Extract version from wheel
      WHEEL_FILE=$(ls dist/*.whl)
      VERSION=$(echo $WHEEL_FILE | sed -n 's/.*-\([0-9.]*\)-.*/\1/p')

      # Store version->commit mapping in GCS
      echo "{\"version\":\"$VERSION\",\"commit\":\"$COMMIT_SHA\",\"short_sha\":\"$SHORT_SHA\",\"build_id\":\"$BUILD_ID\",\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" > /tmp/build-metadata.json

      gsutil cp /tmp/build-metadata.json \
        gs://$PROJECT_ID-build-metadata/unified-trading-services/versions/$VERSION.json || true

      echo "✓ Stored build metadata for version $VERSION"
  waitFor: ["build-wheel"]

# Step 8: Publish with version validation
- name: "gcr.io/google.com/cloudsdktool/cloud-sdk:alpine"
  id: "publish-python"
  entrypoint: "bash"
  args:
    - "-c"
    - |
      set -e
      apk add --no-cache python3 py3-pip jq
      pip3 install --break-system-packages twine keyrings.google-artifactregistry-auth

      # Extract version from wheel
      WHEEL_FILE=$(ls dist/*.whl)
      VERSION=$(echo $WHEEL_FILE | sed -n 's/.*-\([0-9.]*\)-.*/\1/p')

      # Check if version exists in Artifact Registry
      if gcloud artifacts versions list \
        --package=unified-trading-services \
        --repository=unified-libraries \
        --location=asia-northeast1 \
        --format="value(name)" 2>/dev/null | grep -q "/$VERSION\$"; then

        # Version exists - validate it's from same commit
        if gsutil cp gs://$PROJECT_ID-build-metadata/unified-trading-services/versions/$VERSION.json /tmp/existing-metadata.json 2>/dev/null; then
          EXISTING_COMMIT=$(jq -r '.commit' /tmp/existing-metadata.json)

          if [ "$EXISTING_COMMIT" = "$COMMIT_SHA" ]; then
            echo "✓ Version $VERSION already published from commit $COMMIT_SHA (idempotent rebuild)"
            exit 0
          else
            echo "❌ ERROR: Version $VERSION already exists with DIFFERENT code!"
            echo ""
            echo "You changed code but forgot to bump the version in pyproject.toml"
            echo "Current commit:   $COMMIT_SHA (short: $SHORT_SHA)"
            echo "Published commit: $EXISTING_COMMIT"
            echo ""
            echo "Action required: Bump version in pyproject.toml (e.g., 1.5.0 -> 1.5.1)"
            exit 1
          fi
        else
          # Metadata not found (old version) - fail safe
          echo "⚠️  Version $VERSION exists but no metadata found (old build?)"
          echo "Action required: Bump version in pyproject.toml to be safe"
          exit 1
        fi
      fi

      # Version doesn't exist - upload
      echo "Version $VERSION not found. Uploading to Artifact Registry..."
      python3 -m twine upload \
        --repository-url https://asia-northeast1-python.pkg.dev/$PROJECT_ID/unified-libraries/ \
        --non-interactive \
        dist/*.whl

      echo "✓ Successfully uploaded version $VERSION from commit $COMMIT_SHA"
  waitFor: ["store-metadata"]
```

**Behavior:**

| Scenario                         | Version Exists? | Same Commit? | Result                      |
| -------------------------------- | --------------- | ------------ | --------------------------- |
| New version                      | No              | -            | ✅ Upload                   |
| Rebuild same commit              | Yes             | Yes          | ✅ Skip (idempotent)        |
| Code changed, version NOT bumped | Yes             | No           | ❌ **FAIL** with error      |
| Old version (no metadata)        | Yes             | -            | ❌ Fail safe (require bump) |

**Benefits:**

- **Idempotent rebuilds**: Same commit can be built multiple times (CI retries, local testing)
- **Version enforcement**: Forces developer to bump version when code changes
- **Stale package prevention**: Catches "forgot to bump version" mistakes before merge
- **Clear feedback**: Actionable error messages guide developers

**Requirements:**

- GCS bucket: `gs://{PROJECT_ID}-build-metadata/` (create once per project)
- Cloud Build service account needs: `roles/storage.objectAdmin` on metadata bucket
- Version metadata stored indefinitely (negligible cost; enables audit trail)

**Related Cursor Rule:** `.cursor/rules/library-versioning.mdc`

---

## When Quality Gates Fail

The correct response is: **diagnose -> fix root cause -> re-run**.

### Linting Failures

1. Run Phase 1 first (auto-fix): `bash scripts/quality-gates.sh`
2. If Phase 2 still fails: read the ruff error messages
3. Common issues:
   - Undefined variable -> fix the typo or add the import
   - Bare `except:` -> catch specific exception
   - Unused import -> remove it (or ruff auto-fixed it)

### Test Failures

1. Read the pytest output for the specific failure
2. Fix the implementation or the test
3. NEVER skip the test, add `pytest.skip()`, or exclude the file
4. NEVER add `|| true` to bypass
5. If a dependency is missing (e.g., `pytest-xdist`), add it to dev deps

### Config Validation Failures

1. Fix `cloudbuild.yaml` shell variable escaping (`$` -> `$$`)
2. Fix `pyproject.toml` Python version to match expected

---

## Running All Quality Gates

To verify all 13 services pass:

```bash
cd deployment-service
bash scripts/run-all-quality-gates.sh --sequential
```

Timeout: 8-15 minutes for full sequential run. Use timeout >= 30 minutes for CI/agent runs.

---

## Security Gates [IMPLEMENTED — BLOCKING in all repos]

pip-audit and internal advisories run in every `scripts/quality-gates.sh`; failures increment `CODEX_VIOLATIONS`. Bandit
(library repos such as `unified-trading-library`) is documented below.

### 1. pip-audit — OSS vulnerability scan (BLOCKING)

Checks all installed Python packages against the OSV database.

```bash
pip-audit --format json -o /tmp/pip-audit-output.json
```

Required in `pyproject.toml` dev deps: `pip-audit>=2.7.0`

### 2. Internal advisory check (BLOCKING)

Checks installed package versions against known internal vulnerabilities.

**Source of truth:** `unified-trading-pm/security/internal-advisories.yaml` **Checker script:**
`unified-trading-pm/scripts/check-internal-advisories.sh`

To flag a vulnerability: append an entry to `internal-advisories.yaml` — append-only, never remove. To resolve: add
`fixed_in: "<version>"` to the existing entry.

```yaml
advisories:
  - id: INTERNAL-YYYY-NNN
    package: unified-trading-services
    affected_versions: "<2.0.0"
    fixed_in: "2.0.0"
    severity: HIGH # CRITICAL | HIGH | MEDIUM | LOW
    description: "..."
    reported_at: "2026-02-27"
    reported_by: "github-username"
```

### 3. SBOM audit trail (non-blocking)

pip-audit JSON output is stored to GCS after each run via `unified-trading-pm/scripts/sbom-store.py`. Upload failure
does not fail the build.

**Env vars:** `GCP_PROJECT_ID`, `SBOM_BUCKET` (default: `uts-sbom-audit`), `SERVICE_NAME`

**Full security docs:** `07-security/dependency-scanning.md`

### 4. Bandit B108 — hardcoded temp paths (Python)

`bandit` runs in library quality gates (see `unified-trading-library`). **B108** flags literals like `"/tmp"` because
predictable temp paths are a common source of insecure temporary-file patterns.

**Rules:**

- **Never** embed `"/tmp"` (or other fixed temp paths) in Python source for defaults or disk probes.
- **Do** use `tempfile.gettempdir()` for the OS temp directory root — respects `TMPDIR` on Linux and other Unix, and
  yields the correct layout on macOS (typically under `/var/folders/...`, not `/tmp`).
- **Disk usage sampling** (`shutil.disk_usage`): default to root + temp + user home, e.g.
  `( "/", tempfile.gettempdir(), str(Path.home()) )`, dedupe, then skip paths that do not exist. Do **not** hardcode
  `"/home"` (Linux-only).
- **Creating temp files**: use `tempfile.mkstemp`, `tempfile.NamedTemporaryFile`, or `tempfile.TemporaryDirectory` — not
  string paths under `/tmp`.

**Reference implementation:** `unified_trading_library.lifecycle.resource_profiler._default_disk_paths`.

---

## Dead Code Detection (vulture) [ADVISORY — WARN/FAIL thresholds]

`vulture` detects unused Python code: unreachable functions, dead classes, and variables that are defined but never
read. It runs automatically in both `base-service.sh` and `base-library.sh` when the tool is installed.

### Thresholds

| Unused items found | Result                                                       |
| ------------------ | ------------------------------------------------------------ |
| 0–20               | PASS — logged silently                                       |
| 21–100             | WARN — printed to console; does not fail the build           |
| >100               | FAIL — build exits 1; catastrophic dead code must be removed |

Confidence threshold: `--min-confidence 80` (ignores low-confidence guesses such as `__all__` entries and
`abstractmethod` implementations).

### Installing vulture

```bash
uv pip install vulture
```

Add `vulture` to `[project.dependencies]` in `pyproject.toml` (flat deps only — no optional groups):

```toml
[project.dependencies]
vulture = ">=2.13"
```

### Suppressing false positives with .vulture-whitelist.py

Some names are intentionally "unused" from vulture's static perspective: Click command callbacks, pytest fixtures,
abstract method stubs, Pydantic validators, and protocol implementations. Suppress these by creating a
`.vulture-whitelist.py` at the repo root:

```python
# .vulture-whitelist.py — vulture whitelist for intentionally unused names
# Each line uses an attribute access pattern that vulture recognises as "used".
# Do NOT import anything here — this file is parsed by vulture statically.

_.on_click           # Click callback
_.pytest_configure   # pytest plugin hook
_.validate_value     # Pydantic field validator
_.health_check       # Abstract method implementation in protocol stub
```

The whitelist file is auto-detected by the quality gate — if `.vulture-whitelist.py` exists in the repo root it is
passed to vulture automatically. No changes to `quality-gates.sh` are required.

### Common false-positive patterns

| Pattern                                  | Why vulture flags it         | Whitelist entry       |
| ---------------------------------------- | ---------------------------- | --------------------- |
| `@app.route("/health")`                  | Called via HTTP, not Python  | `_.health`            |
| `@pytest.fixture`                        | Called by pytest framework   | `_.my_fixture`        |
| `class MyProtocol(Protocol):`            | Structural subtype           | `_.my_method`         |
| `@click.command` / `@click.pass_context` | CLI entry point              | `_.cli`               |
| `__all__ = [...]` exports                | Imported by downstream repos | add name to whitelist |

### pyproject.toml configuration (optional)

Vulture respects a `[tool.vulture]` section in `pyproject.toml` for project-level defaults:

```toml
[tool.vulture]
min_confidence = 80
paths = ["my_service/"]
ignore_names = ["test_*", "setUp", "tearDown"]
```

Note: the quality gate always passes `--min-confidence 80` on the command line, which takes precedence over
`pyproject.toml` defaults. Use `pyproject.toml` only for `ignore_names` and `ignore_decorators`.

### Running vulture manually

```bash
# Basic run
vulture my_service/ --min-confidence 80

# With whitelist
vulture my_service/ .vulture-whitelist.py --min-confidence 80

# Show only unused functions and classes (not variables)
vulture my_service/ --min-confidence 80 | grep -E "unused (function|class|method)"
```

---

## AWS CodeBuild Parity

Every service repo contains both `cloudbuild.yaml` (GCP Cloud Build) and `buildspec.aws.yaml` (AWS CodeBuild). Both
files execute the **identical gate logic** via `scripts/quality-gates.sh --no-fix --quick`. This section documents the
structural differences and the shared contract that keeps both platforms in sync.

### Identical Gate Logic

Both CI platforms run the same script inside the Docker image:

```bash
scripts/quality-gates.sh --no-fix --quick
```

This guarantees that a build passing on GCP will also pass on AWS and vice versa. The script itself is the single SSOT
for all gate logic — neither `cloudbuild.yaml` nor `buildspec.aws.yaml` add extra checks; they only differ in platform
mechanics.

### Structural Differences

| Aspect                  | GCP Cloud Build (`cloudbuild.yaml`)                                           | AWS CodeBuild (`buildspec.aws.yaml`)                                                               |
| ----------------------- | ----------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| **File**                | `cloudbuild.yaml`                                                             | `buildspec.aws.yaml`                                                                               |
| **Registry**            | GCP Artifact Registry (`asia-northeast1-docker.pkg.dev/$PROJECT_ID/...`)      | AWS ECR (`$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$REPO_NAME`)                   |
| **Auth**                | `gcloud auth configure-docker` (ADC / service account)                        | `aws ecr get-login-password` piped to `docker login`                                               |
| **Build steps**         | Explicit named steps with `waitFor` DAG                                       | Ordered `phases`: `install` → `pre_build` → `build` → `post_build`                                 |
| **Gate execution**      | `docker run --rm --entrypoint "" -e CLOUD_BUILD=true ... /bin/bash -c "..."`  | `docker run --rm --entrypoint "" -e CLOUD_BUILD=true -e CLOUD_PROVIDER=aws ... /bin/bash -c "..."` |
| **Scan**                | GCP Container Analysis (async CVE scan, blocks on CRITICAL)                   | Not included by default — add ECR image scanning in account settings                               |
| **Post-build dispatch** | Not included                                                                  | Optional: GitHub dispatch via `GH_PAT` secret (non-blocking `\|\| true`)                           |
| **Package publish**     | Artifact Registry Python repo (twine + keyrings.google-artifactregistry-auth) | AWS CodeArtifact (twine with `aws codeartifact login`; skipped if `$CODEARTIFACT_DOMAIN` unset)    |
| **Timeout**             | `timeout: "1800s"` at root                                                    | No global timeout in spec; set on CodeBuild project console                                        |
| **Build cache**         | Implicit layer cache in Cloud Build workers                                   | `cache: paths: ["/root/.cache/uv/**/*"]` — uv cache persisted across builds                        |

### Environment Variables

Both platforms inject environment variables used by `quality-gates.sh` when running inside Docker:

| Variable             | GCP (`-e` in `docker run`)               | AWS (`-e` in `docker run`)                | Purpose                                       |
| -------------------- | ---------------------------------------- | ----------------------------------------- | --------------------------------------------- |
| `CLOUD_BUILD`        | `true`                                   | `true`                                    | Signals CI context; skips venv creation in QG |
| `CLOUD_MOCK_MODE`    | `true`                                   | `true`                                    | Disables live cloud calls; uses mock sinks    |
| `GCP_PROJECT_ID`     | `$PROJECT_ID` (Cloud Build substitution) | Not set (AWS has no project concept)      | GCP config; irrelevant on AWS path            |
| `CLOUD_PROVIDER`     | Not set (defaults to `gcp`)              | `aws`                                     | Selects cloud provider branch in cloud config |
| `AWS_DEFAULT_REGION` | Not set                                  | `ap-northeast-1` (env var in buildspec)   | AWS region for ECR and SDK calls              |
| `AWS_ACCOUNT_ID`     | Not set                                  | Must be set in CodeBuild project env vars | Required for ECR image URI construction       |

### Service-Specific Mock Variables (GCP only)

GCP `cloudbuild.yaml` files inject additional mock bucket/topic variables needed to satisfy config validation at image
startup. AWS buildspec files rely on `CLOUD_MOCK_MODE=true` alone, since the UCI mock layer intercepts all cloud SDK
calls before any env var is read:

```bash
# GCP cloudbuild.yaml quality-gates step (execution-service example)
-e EXECUTION_STORE_GCS_BUCKET=mock-execution-bucket \
-e INSTRUMENTS_STORE_GCS_BUCKET=mock-instruments-bucket \
-e STRATEGY_STORE_BUCKET=mock-strategy-bucket
```

AWS services that require bucket/topic names during config validation should add the same `-e` flags to the `docker run`
command in the `build` phase.

### GCP Emulator Configuration

For Layer 1.5 integration tests requiring protocol-faithful GCP services, set these env vars before running tests. The
GCP SDKs auto-detect and redirect to the emulator.

| Service  | Env Var                                       | Docker Image                                      | Port |
| -------- | --------------------------------------------- | ------------------------------------------------- | ---- |
| Pub/Sub  | `PUBSUB_EMULATOR_HOST=localhost:8085`         | `gcr.io/google.com/cloudsdktool/google-cloud-cli` | 8085 |
| GCS      | `STORAGE_EMULATOR_HOST=http://localhost:4443` | `fsouza/fake-gcs-server:latest`                   | 4443 |
| BigQuery | `BIGQUERY_EMULATOR_HOST=localhost:9050`       | `ghcr.io/goccy/bigquery-emulator:latest`          | 9050 |

**Known BigQuery emulator gap**: Window functions (ROW_NUMBER, RANK, etc.) are not fully supported in the community
emulator. Test only the subset of BQ features used in production paths.

Start all emulators at once:

```bash
docker compose -f unified-trading-pm/docker/docker-compose.mock.yml --profile gcp-emulators up
```

Fixtures auto-skip when the emulator is not reachable — no test failures in environments without Docker.

### AWS Moto Integration Tests

AWS services are intercepted at the SDK level using `moto` — no credentials, no network, no emulator process:

```python
from moto import mock_aws

@mock_aws
def test_s3_upload():
    # Creates real S3 bucket structure in memory
    import boto3
    client = boto3.client("s3", region_name="us-east-1")
    client.create_bucket(Bucket="test-bucket")
    ...
```

Coverage: `unified-cloud-interface/tests/integration/test_aws_mode.py` — 26 tests covering S3StorageClient,
AWSSecretClient, SQSQueueClient.

Add to test deps in `pyproject.toml`:

```toml
[project.optional-dependencies]
dev = [
  "moto[s3,secretsmanager,sqs]>=5.0.0,<6.0.0",
  ...
]
```

### Credential-Free CI Gate (network_block_plugin)

The `network_block_plugin.py` pytest plugin intercepts `socket.socket.connect` at the OS level, blocking all network
connections regardless of HTTP library:

```bash
# Activate in CI — proves zero live API calls
CLOUD_PROVIDER=local CLOUD_MOCK_MODE=true pytest --block-network -m "not sandbox"
```

**Opt-out pattern** for tests that legitimately connect to local emulators:

```python
@pytest.mark.allow_network  # emulator connection only — not a live API
def test_pubsub_emulator_roundtrip(pubsub_emulator_host):
    ...
```

Each `@pytest.mark.allow_network` opt-out emits a WARNING in CI logs. Monitor the count — it should be stable and
explained.

Plugin location: `unified-api-contracts/unified_api_contracts/testing/network_block_plugin.py`

### Cassette Parity Testing (H5.2)

Every committed cassette YAML is validated against its corresponding UAC Pydantic model on every commit:

```bash
cd unified-api-contracts && pytest tests/test_cassette_schema_parity.py
# 256 tests, zero network calls, ~2s runtime
```

Failures mean a cassette records a response shape that violates the current UAC contract — fix the cassette or the
model.

### Cassette Drift Detection (H5.1)

Nightly at 02:00 UTC, `cassette-drift-check.yml` re-records cassettes against real exchange APIs and diffs them against
committed YAMLs. On schema-level drift:

- Creates GitHub issue in `unified-api-contracts`
- Sends Telegram alert

This is **alerting-only** — not CI-blocking. Human review required to update stale cassettes.

### Parity Rules

1. **Same script, same flags**: Both platforms MUST call `scripts/quality-gates.sh --no-fix --quick`. Any deviation
   requires a documented exception in `QUALITY_GATE_BYPASS_AUDIT.md`.
2. **Same Docker image**: Both platforms build from the same `Dockerfile`. The image under test is identical.
3. **Same Python version**: `buildspec.aws.yaml` sets `runtime-versions: python: "3.13"` to match `pyproject.toml`.
4. **No AWS-specific bypasses**: `|| true` in CodeBuild post-build steps MUST carry a comment explaining that the step
   is non-blocking by design (e.g., optional GitHub dispatch, optional CodeArtifact publish).
5. **ECR repo auto-creation**: `aws ecr describe-repositories ... || aws ecr create-repository ...` in `pre_build`
   mirrors GCP's `gcloud artifacts repositories describe ... || gcloud artifacts repositories create ...` in the
   `ensure-repo` step.

### Library Repos: Simpler Buildspec

Library repos (T0–T3) use a leaner `buildspec.aws.yaml` that does not build a Docker image. Quality gates run directly
in the CodeBuild environment:

```yaml
version: 0.2
env:
  variables:
    CLOUD_PROVIDER: aws
phases:
  install:
    runtime-versions:
      python: "3.13"
    commands:
      - pip install uv
      - uv pip install -e ".[dev]" --system
  pre_build:
    commands:
      - bash scripts/quickmerge.sh --quality-gates-only
  build:
    commands:
      - bash scripts/quality-gates.sh
artifacts:
  files:
    - "**/*"
```

This is equivalent to the GitHub Actions `quality-gates.yml` workflow for libraries — no Docker build, no image push.

### Adding AWS CodeBuild to a New Repo

1. Copy `unified-trading-pm/codex/06-coding-standards/quality-gates-service-template.sh` as the repo's
   `scripts/quality-gates.sh`.
2. Copy an existing service `buildspec.aws.yaml` (e.g., `execution-service/buildspec.aws.yaml`) and update:
   - `REPO_NAME` will be derived automatically via `basename $(pwd)`.
   - Add any service-specific mock `-e` flags to the `docker run` command.
3. Set in the CodeBuild project console (not in `buildspec.aws.yaml`): `AWS_ACCOUNT_ID`, and optionally `GH_PAT`,
   `CODEARTIFACT_DOMAIN`.
4. Verify `CLOUD_PROVIDER=aws` is in `env.variables` so `UnifiedCloudConfig` selects the AWS code path.

---

## STEP entries — batch/live symmetry (L1-L7)

> Full SSOT for the mode-axis cartesian product + anti-patterns: [`mode-axis-discipline.md`](mode-axis-discipline.md).
> Batch/live invariant: [`../04-architecture/batch-live-architecture.md`](../04-architecture/batch-live-architecture.md).
> Pre-audit source: `batch_live_design_symmetry_preaudit_2026_05_10.md § 1.Tab1`.
>
> Status as of 2026-05-14: L1+L5 enable DAY-1 (0 violations); L2+L3 enable after fix-batch lands (Tab 3, ~21+2
> violations); L4+L6 post-cutover (Block G1). L7 is an ongoing ratchet sweep.

---

### STEP L1: DataType Mode-Prefix Ban (DAY-1 ENABLE)

**Status**: DAY-1 ENABLE — 0 violations found in pre-audit.

**What it catches**: `DataType` enum members with `LIVE_` or `BATCH_` prefix, e.g.:

```python
# FORBIDDEN
class DataType(StrEnum):
    LIVE_OHLCV_1H = "live_ohlcv_1h"
    BATCH_OHLCV_1H = "batch_ohlcv_1h"
```

**Why**: Batch and live share IDENTICAL schemas, data_types, and fields. The only diff is which SOURCE serves a given
`(asset_group, data_type)`. A per-mode DataType fork creates two diverging schemas — FORBIDDEN per the batch=live
invariant.

**Fix**: use a single `DataType.OHLCV_1H` member. The source is tracked by `pipeline_mode` column in the manifest (STEP
5.70), not by the data_type name.

**Enforcement**: `scripts/quality-gates-base/base-service.sh` — AST-walk on UAC DataType enum + consumer service
enums. Wire-in pending (pre-audit confirmed 0 violations so gate enables at zero ratchet cost on Day-1).

**Composes with**: STEP L5 (unified DataType enum, no per-mode fork) · STEP 5.70 (`pipeline_mode` at `record_*`).

---

### STEP L2: Mode-Conditional-Outside-Seam (FIX-REQUIRED, ~21 violations)

**Status**: FIX-REQUIRED — ~21 violations across service codebase. Enable AFTER fix-batch lands (Tab 3 scope).

**What it catches**: `if runtime_mode == "live":` / `if runtime_mode == RuntimeMode.LIVE:` / `if mode == "batch":`
branches inside business logic (i.e., outside the 4 seams defined in `batch-live-architecture.md §2`).

```python
# FORBIDDEN — mode conditional inside business logic
if runtime_mode == "live":
    signal = compute_live_signal(tick)
else:
    signal = compute_batch_signal(bar)
```

**The 4 allowed seams** (from `batch-live-architecture.md §2`):

1. Data source seam — `RuntimeMode` branch selects GCS Parquet reader vs Redis Stream subscriber.
2. Feature seam — `RuntimeMode` branch selects GCS feature Parquet vs embedded UTL `feature_calculator`.
3. ML inference seam — `RuntimeMode` branch selects GCS prediction Parquet vs Redis/PubSub topic.
4. Execution fills seam — `BatchExecutionMode` branch (batch); `OperationalMode` branch (live: real vs paper).

**Fix**: move the mode branch to the seam. The function called from the seam receives a canonical `FeatureVector` /
`FillResult` regardless of which seam produced it — zero mode-conditional in the function body.

**Pre-audit violation count**: ~21 (exact list in `batch_live_design_symmetry_preaudit_2026_05_10.md § 1.Tab1`).

**Enforcement**: `scripts/quality-gates-base/base-service.sh` — AST-walk for `If` nodes whose test is a mode-enum
comparison, excluding the 4 seam files. Wire-in pending Tab 3 fix-batch.

**Composes with**: STEP L3 (RuntimeMode SSOT) · `mode-axis-discipline.md` AP-1 · `batch-live-architecture.md §2`.

---

### STEP L3: RuntimeMode Single SSOT (FIX-REQUIRED, 2 violations)

**Status**: FIX-REQUIRED — 2 violations. Enable AFTER fix-batch lands (Tab 3 scope).

**What it catches**: `RuntimeMode` declared outside the UTL canonical / UAC re-export path:

```typescript
// FORBIDDEN — UI redeclaration (violation #1)
type ExecutionMode = "live" | "batch";  // unified-trading-system-ui/context/...

# FORBIDDEN — local UAC re-declaration (violation #2 — should be a re-export, not a redeclaration)
class RuntimeMode(StrEnum):  # in a non-canonical UAC file
    ...
```

**SSOT**: `unified_api_contracts.internal.modes.RuntimeMode`. All consumers import from there. Tab 3 ships:
- UAC re-exports `RuntimeMode` from UTL canonical (fixing UAC-internal violation).
- UI imports `RuntimeMode` from UAC schema bundle (fixing UI redeclaration — see `batch-live-architecture.md §12`).

**Enforcement**: `scripts/quality-gates-base/base-service.sh` — `rg 'class RuntimeMode'` across workspace, excluding
the canonical file. Wire-in pending Tab 3 fix-batch.

**Composes with**: STEP L2 (mode-conditional branches) · `mode-axis-discipline.md` AP-3 · `batch-live-architecture.md
§12`.

---

### STEP L7: `record_captured()` assert_available_at_present (ongoing sweep)

**Status**: Ongoing ratchet — baseline shrinks per sweep cycle. Violations added to fix-list; ratchet prevents new
ones.

**What it catches**: `record_captured()` callsites that do NOT pass `assert_available_at_present=True` (or the
equivalent UTL-internal guard). The UTL `record_captured()` implementation calls `assert_available_at_present`
internally by default; L7 catches callsites that bypass via keyword arg override or call a raw `ManifestWriter.add()`
directly.

**Why**: `available_at` is a **per-row, write-time** stamp equal to live-pipeline-arrival. Incorrect stamps introduce
lookahead bias in backtests (a row appears to have been available earlier than it was) — silent, hard-to-detect
correctness bug. See CLAUDE.md "`available_at` is per-row, write-time, equal to live-pipeline-arrival".

**Known violations** (pre-audit 2026-05-10):
- `market-tick-data-service/market_tick_data_service/io/storage_dispatch_worker.py:49`
- `market-tick-data-service/market_tick_data_service/pipeline/output_writer_service.py:318`
- `market-tick-data-service/market_tick_data_service/pipeline/orchestration_writer.py:388`
- `unified-trading-library/unified_trading_library/domain/standardized_service.py:100,299` (UTL internal — verify if
  bypass is intentional or inadvertent)

**Fix**: pass `assert_available_at_present=True` to `record_captured()`, or ensure the caller sets `available_at` on
the parquet row before calling. Never set `available_at` at read-time.

**Enforcement**: `scripts/quality-gates-base/base-service.sh` — `rg 'record_captured'` + AST-walk for keyword
`assert_available_at_present=False` overrides + raw `ManifestWriter.add()` without stamp check. Ongoing ratchet:
baseline anchored at pre-audit count; new violations fail immediately; existing baseline shrinks as sweep lands.

**Composes with**: STEP 5.67 (banned NaN-placeholder) · STEP 5.70 (`pipeline_mode` explicit) · UAC
`availability_semantics.AVAILABILITY_AT_SEMANTICS` · writegate plan Phase 3.D.5.

---

## Anti-Patterns

```bash
# WRONG: bypass failures
ruff check . || true

# WRONG: skip tests
pytest tests/ -k "not test_that_fails"

# WRONG: disable in CI
continue-on-error: true

# WRONG: comment out failing tests
# def test_event_logging():
#     ...

# CORRECT: fix the issue
ruff check .  # Fix what ruff reports
pytest tests/ -v  # Fix what fails
```
