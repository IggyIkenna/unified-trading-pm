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
    - [Memory Governance (OOM Prevention)](#memory-governance-oom-prevention)
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

| STEP | Topic                                                                                                                                                                                   | This doc anchor                                                                                                                            | Enforcement file (canonical)                                                                                                                                  | CLAUDE.md cross-ref                                                                                                                                                                                                                         |
| ---- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 5.10 | basedpyright type-check                                                                                                                                                                 | [Type Checking Standards](#type-checking-standards-pyrightconfigjson)                                                                      | `scripts/quality-gates-base/base-service.sh`                                                                                                                  | "Key Rules — `basedpyright` not `pyright`"                                                                                                                                                                                                  |
| 5.11 | ruff lint + format                                                                                                                                                                      | [Ruff Version Consistency](#ruff-version-consistency-critical) · [Ruff Configuration](#ruff-configuration)                                 | `scripts/quality-gates-base/base-service.sh`                                                                                                                  | "Key Rules — flat deps + ruff"                                                                                                                                                                                                              |
| 5.22 | basedpyright suppression baseline                                                                                                                                                       | [STEP 5.22: basedpyright Baseline Suppression](#step-522-basedpyright-baseline-suppression-error-policy--escalated-2026-03-10)             | `scripts/quality-gates-base/base-service.sh` + `base-library.sh`                                                                                              | "No `# type: ignore` to hide architectural violations"                                                                                                                                                                                      |
| 5.34 | typed config reloaders                                                                                                                                                                  | (no section here — see enforcement file)                                                                                                   | `scripts/quality-gates-base/base-service.sh`                                                                                                                  | "Service Infrastructure Requirements — Typed config reloaders (STEP 5.34)"                                                                                                                                                                  |
| 5.61 | ServiceBootstrap presence                                                                                                                                                               | (no section here — see enforcement file)                                                                                                   | `scripts/quality-gates-base/base-service.sh`                                                                                                                  | "Service Infrastructure Requirements — ServiceBootstrap (STEP 5.61)"                                                                                                                                                                        |
| 5.62 | Health API + `make_health_router`                                                                                                                                                       | (no section here — see enforcement file)                                                                                                   | `scripts/quality-gates-base/base-service.sh`                                                                                                                  | "Service Infrastructure Requirements — Health API (STEP 5.62)"                                                                                                                                                                              |
| 5.64 | bundled-shard cluster validation AST                                                                                                                                                    | (no section here — see enforcement file)                                                                                                   | `scripts/quality-gates-base/base-service.sh`                                                                                                                  | "Cluster validation MANDATORY at `record_captured` for bundled shards"                                                                                                                                                                      |
| 5.65 | removed-symbol AST-walk                                                                                                                                                                 | [STEP 5.65: Removed-Symbol AST-Walk](#step-565-removed-symbol-ast-walk-citadel--6-extended)                                                | `scripts/quality_gates/check_removed_symbols.py` (driver)                                                                                                     | "Citadel-Grade Planning Standards § 6 Downstream Consumer Updates"                                                                                                                                                                          |
| 5.66 | per-VM shard isolation envvar AST walk                                                                                                                                                  | (no section here — see enforcement file)                                                                                                   | `scripts/quality-gates-base/base-service.sh`                                                                                                                  | "Per-VM shard isolation for concurrent backfills"                                                                                                                                                                                           |
| 5.67 | banned NaN-placeholder method AST-walk                                                                                                                                                  | [STEP 5.67: Banned NaN-Placeholder / Bypass-`record_captured` AST-Walk](#step-567-banned-nan-placeholder--bypass-record_captured-ast-walk) | `scripts/quality_gates/check_banned_placeholder_methods.py` (driver)                                                                                          | "Honest absence vs fake placeholders" + "No double SSOT in data-saving methodology" + "Four-category empty-output decision"                                                                                                                 |
| 5.69 | inline `f"gs://…"` / `f"s3://…"` URI ratchet                                                                                                                                            | (no section here — see enforcement file)                                                                                                   | `scripts/quality_gates/check_inline_bucket_uri.py` (driver)                                                                                                   | "Bucket-name SSOT (b+)"                                                                                                                                                                                                                     |
| 5.70 | explicit `pipeline_mode=` at `record_*` calls                                                                                                                                           | [STEP 5.70: Explicit `pipeline_mode=` at every `record_*` call](#step-570-explicit-pipeline_mode-at-every-record_-call-manifest-v8)        | `scripts/quality_gates/check_pipeline_mode_explicit_at_record_calls.py` (driver)                                                                              | "Live = batch (CRITICAL)" + "Availability manifest v8 — `pipeline_mode` first-class column"                                                                                                                                                 |
| 5.71 | emission-policy paired-callsite (`publish_with_policy` for every `record_captured`)                                                                                                     | (no section here — see enforcement file)                                                                                                   | `scripts/quality-gates-base/base-service.sh` (baseline-aware ratchet)                                                                                         | writegate Phase 6.9 — every `record_captured()` callsite must have a paired `publish_with_policy()` or `publish_with_manifest_lookup()`                                                                                                     |
| 5.72 | UAC chain_env inclusion invariant (`MAINNET_CHAIN_IDS ⊇ CHAIN_GENESIS_DATES ⊇ GAS_FEE_CHAIN_START_DATES`)                                                                               | (no section here — see enforcement file)                                                                                                   | `scripts/quality-gates-base/base-service.sh`                                                                                                                  | `defi-execution-overview.md` § chain-set completeness (DF-7)                                                                                                                                                                                |
| 5.73 | `ManifestWriter.add()` with bundled `data_type` literal — banned                                                                                                                        | (no section here — see enforcement file)                                                                                                   | `scripts/quality-gates-base/base-service.sh`                                                                                                                  | use `record_captured_from_counts()` instead                                                                                                                                                                                                 |
| 5.74 | MDPS bar-boundary truncation bypass static check                                                                                                                                        | (no section here — see enforcement file)                                                                                                   | `scripts/quality-gates-base/base-service.sh`                                                                                                                  | MDPS-only; use `compute_bar_close_boundary()` helper                                                                                                                                                                                        |
| 5.75 | `DataType` enum mode-agnosticism — no `LIVE_`/`BATCH_` prefixes (batch_live_symmetry L1)                                                                                                | (no section here — see enforcement file)                                                                                                   | `scripts/quality-gates-base/base-service.sh`                                                                                                                  | "Batch = Live" + `mode-axis-discipline.md` — DataType values must be mode-agnostic                                                                                                                                                          |
| 5.76 | no service-level `DataType` class redeclarations (batch_live_symmetry L5)                                                                                                               | (no section here — see enforcement file)                                                                                                   | `scripts/quality-gates-base/base-service.sh`                                                                                                                  | import from `unified_api_contracts`; never redeclare locally                                                                                                                                                                                |
| 5.77 | no `mode == "batch"`/`"live"` comparisons outside CLI seam (batch_live_symmetry L2)                                                                                                     | (no section here — see enforcement file)                                                                                                   | `scripts/quality-gates-base/base-service.sh`                                                                                                                  | `mode-axis-discipline.md` AP-1 — mode routing only at CLI entry point                                                                                                                                                                       |
| 5.78 | `RuntimeMode` declared only in UAC `internal/modes.py` (batch_live_symmetry L3)                                                                                                         | (no section here — see enforcement file)                                                                                                   | `scripts/quality-gates-base/base-service.sh`                                                                                                                  | `mode-axis-discipline.md` AP-3 — import from UAC, never redeclare                                                                                                                                                                           |
| 5.79 | dockerfile-base-pin — production Dockerfiles must use `@sha256:digest` not `:tag`                                                                                                       | (no section here — see enforcement file)                                                                                                   | `scripts/quality-gates-base/base-service.sh` (pending-ratchet until Phase 5)                                                                                  | `codex/06-coding-standards/dockerfile-standards.md` — pin SHA for reproducible builds; deployment_and_qg_strategy_implementation_2026_05_13.md Phase 5                                                                                      |
| 5.80 | tarball-manifest-present — `create-code-tarballs.sh` must write sibling `manifest.json`                                                                                                 | (no section here — see enforcement file)                                                                                                   | `scripts/quality-gates-base/base-service.sh` (deployment-service only; pending-ratchet)                                                                       | `codex/05-infrastructure/vm-tarball-deployment.md` — manifest enables SHA-assertion on VM launch                                                                                                                                            |
| 5.81 | tarball-env-block — deployment-api must gate staging/prod tarball uploads behind env-tier check                                                                                         | (no section here — see enforcement file)                                                                                                   | `scripts/quality-gates-base/base-service.sh` (deployment-api only; pending-ratchet)                                                                           | `deployment-and-qg-strategy.md` § env-locking (B-001 Phase 1)                                                                                                                                                                               |
| 5.82 | image-build-on-staging-merge — staging branch workflow must trigger Cloud Build                                                                                                         | (no section here — see enforcement file)                                                                                                   | `scripts/quality-gates-base/base-service.sh` (pending-ratchet until Phase 5)                                                                                  | `deployment-and-qg-strategy.md` § image-build cutover path; deployment_and_qg_strategy_implementation_2026_05_13.md Phase 5                                                                                                                 |
| 5.83 | adapter contract-call regression ratchet (per-file minimum on `classify_venue_error`/`ADAPTER_FETCH_FAILED`/`record_captured`/`record_empty`/`record_failed`)                           | (no section here — see enforcement file)                                                                                                   | `scripts/quality_gates/check_adapter_contract_regression.py` (driver) + `scripts/qg/no_adapter_contract_regression.sh` (wrapper)                              | `lint_sweep_774602ea8_regression_audit_2026_05_20.md` — catches layer-N+1 hygiene-sweep wiping layer-N adapter contracts (kalshi.py + polymarket_clob.py case 2026-05-20). Baseline: `scripts/quality_gates/adapter_contract_baseline.yaml` |
| 5.85 | UAC SourceCapability structured venue metadata guard — every `SourceCapability(...)` in `capability_declarations/_*.py` must have explicit `chain=` and `kind=` kwargs (even if `None`) | (no section here — see enforcement file)                                                                                                   | `scripts/quality_gates/check_uac_source_capability_metadata.py` (checker); wired in `base-library.sh` after STEP 5.83, guarded by `UAC_CANONICAL_EXEMPT=true` | `uac_source_capability_metadata_promotion_2026_05_20.md` Phase 3 — guards regression where new venue declarations omit Phase 2 structured metadata fields. Exit 0 = all 70 venues have explicit chain+kind.                                 |
| L1   | data*type enum contains `LIVE*`/`BATCH\_` prefixed members                                                                                                                              | [STEP L1: DataType Mode-Prefix Ban](#step-l1-datatype-mode-prefix-ban-day-1-enable)                                                        | `scripts/quality-gates-base/base-service.sh` STEP 5.75 (ENABLED 2026-05-14)                                                                                   | "Batch = Live: Unified Pipeline Architecture" — unified DataType enum, no per-mode fork                                                                                                                                                     |
| L2   | mode-conditional branches outside seams                                                                                                                                                 | [STEP L2: Mode-Conditional-Outside-Seam](#step-l2-mode-conditional-outside-seam-enabled)                                                   | `scripts/quality-gates-base/base-service.sh` STEP 5.77 (ENABLED 2026-05-14, 0 violations)                                                                     | `mode-axis-discipline.md` AP-1 — business logic must not branch on `RuntimeMode`                                                                                                                                                            |
| L3   | `RuntimeMode` declared outside UAC SSOT                                                                                                                                                 | [STEP L3: RuntimeMode Single SSOT](#step-l3-runtimemode-single-ssot-enabled-partial)                                                       | `scripts/quality-gates-base/base-service.sh` STEP 5.78 (ENABLED 2026-05-14; UI deliberate-copy DEFERRED)                                                      | `mode-axis-discipline.md` AP-3 — SSOT: `unified_api_contracts.internal.modes.RuntimeMode`                                                                                                                                                   |
| L7   | `record_captured()` missing `assert_available_at_present`                                                                                                                               | [STEP L7: record_captured assert_available_at_present](#step-l7-record_captured-assert_available_at_present-ongoing-sweep)                 | `scripts/quality-gates-base/base-service.sh` (ongoing ratchet)                                                                                                | "`available_at` is per-row, write-time" — UTL guard internal; L7 catches callsites that bypass                                                                                                                                              |

When a STEP appears in CI output (e.g. `STEP 5.62 FAILED: api/main.py missing make_health_router`), open the enforcement
file's matching block for the exact assertion + the CLAUDE.md cross-ref for the rationale + the linked anchor here for
deeper context.

## TL;DR

Every service has `scripts/quality-gates.sh` that runs the exact same checks as GitHub Actions and Cloud Build. It
operates in three phases inside quickmerge: Phase 1 (lint auto-fix only — fast), Phase 2 (lint verify — abort early if
unfixable), Phase 3 (tests + typecheck + codex — run exactly once). **For pre-push workflow always use quickmerge** (it
runs quality gates); run `quality-gates.sh` directly only for local iteration or CI. If quality gates fail, fix the root
cause — never bypass.

## Generated manifest artifacts are NOT a per-QG side-effect (`MANIFEST_STATE_WRITER`)

`quality-gates.sh` must **not** mutate the shared tracked files `workspace-manifest.json` (its `ci_status` field) or
regenerate `WORKSPACE_MANIFEST_DAG.svg` / `DATA_FLOW_DAG.svg` as a side-effect of a normal agent run. Doing so left
every slot worktree perpetually dirty (these files were touched in 50/50 recent commits), which made the FF-pull cron
skip the slot (`[skip:dirty]`), the branch fall behind LDR, direct-to-LDR pushes stop fast-forwarding, and work strand
on tab branches (the 2026-06-01 "70-ahead/68-behind" drift incident).

Contract:

- The ci_status writers in `scripts/quality-gates-base/_ci-status-updater.sh` and the DAG-regen blocks in `base-*.sh`
  are gated behind `MANIFEST_STATE_WRITER` (default `0` → no-op). Per-QG-run agents never write these files.
- **`ci_status`** is owned by **CI dispatch** (authoritative). Local QG decides pass/fail via the `.qg_last_passed_sha`
  sentinel, not the json value; quickmerge gates on the sentinel + the `!= NO_QG` check, not the LOCAL_PASS/FAILING
  value.
- **The DAG SVGs** are regenerated in exactly two controlled places: `quickmerge.sh` at promotion time, and the
  dedicated `scripts/manifest/refresh-manifest-dag.sh` cron (runs with `MANIFEST_STATE_WRITER=1`, commits to LDR from an
  isolated worktree). Only one host runs the cron.

If you genuinely need a one-off regeneration locally, run `MANIFEST_STATE_WRITER=1 bash scripts/quality-gates.sh` or the
dedicated job directly — but never commit the churn from a slot worktree.

## Two-Pass Workflow Model

> **The commit is the per-repo quality boundary (HARD RULE, tightened 2026-06-03; was "before quickmerge").** A **code**
> commit toward the integration branch must be made from a `quality-gates.sh`-green tree: the `prek` pre-commit hook
> (ruff/format/gitleaks/conventional-commit) is the **LIGHT** gate; the full `quality-gates.sh` (Pass 1) is the
> **commit-prerequisite**. This binds the direct **Commit+Push+Flip** path, not only quickmerge. Run it cheaply via
> **QG-sweep batching** (§ below — gate ONCE over a batch → per-shippable-unit commits from that green tree; per-batch,
> not per-commit). Pure doc / plan-flip / markdown commits (e.g. `docs(plans):` flips) take the prek hook only — full QG
> is a source gate.

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

**Two-pass model for agents**: Pass 1 (`quality-gates.sh`) is the ONLY time tests run in the agent workflow. Pass 2
(`quickmerge --agent`) deliberately skips tests — they already passed in Pass 1 and re-running them wastes CI budget
without adding signal. Agents MUST NOT skip Pass 1 to save time; the test gate is the correctness proof.

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

## Dep-content gate — editable deps must be clean + == LDR (`check_dep_content_sync.py`, 2026-06-08)

Local QG resolves internal deps via **editable paths** (`tool.uv.sources … path = "../X", editable = true`), so it tests
against your **working-tree** copy of every dep — an uncommitted or LDR-divergent dep edit (same version) passes locally
but fails at staging, and the version-typed quickmerge gates (STAGE 1.6/1.7) never see it. The pre-test QG step
`scripts/cicd/check_dep_content_sync.py` (wired into `base-service.sh`) closes this: it walks the **transitive**
editable-dep DAG (consumer → mtds → utl/uac) and classifies each dep:

- **dirty OR ahead-of-LDR-unpushed** → **BLOCK** — commit+push the dep to LDR first; local QG is otherwise testing
  against content staging will never see.
- **behind its committed manifest-version ref** → WARN (stale base).
- **clean + == `origin/live-defi-rollout`** → PASS — local-green now means "green vs the shared base".

Rollout mode: WARN-default, `DEP_CONTENT_GATE_BLOCK=1` to enforce. Human-only `--allow-dirty-deps` escape **taints** the
sentinel (`.qg_last_passed_sha` records `DIRTY_DEPS`) so it can never satisfy a quickmerge promotion — mirrors the
`--dep-branch` / `--skip-dep-tier-gate` human-only pattern. Shipped PM@13d6660f8; plan:
`plans/archive/2026_06/quickmerge_dep_content_sync_and_strict_enforcement_2026_06_08.md`.

---

## CI parallel slice jobs + `QG_SLICE` (latency reduction, 2026-06-10)

The remote `quality-gates-v2` check (the required CI gate) used to run the **entire** `quality-gates.sh --no-fix`
monolith in ONE serial job (~12 min; the single "Run quality gates" step measured 715s of 778s). The reusable workflow
`.github/workflows/python-quality-gates-v2.yml` now fans it into a **matrix of parallel slice legs** so wall-time →
`max(slice)` not `sum(slices)` (pytest dominates, so the gate drops to ≈ the pytest leg).

**`QG_SLICE` selector (base-service.sh + base-library.sh).** A new env var partitions the gate with ZERO overlap + ZERO
lost coverage — every check the monolith ran runs in exactly one slice. **Unset = the full monolithic run**
(behaviour-identical for every LOCAL invocation + existing caller — local `quality-gates.sh` is unchanged):

| `QG_SLICE`   | Runs                                                                                                           |
| ------------ | -------------------------------------------------------------------------------------------------------------- |
| `tests`      | ENV + [3] TESTS only (early-exit after pytest)                                                                 |
| `typecheck`  | ENV + [4] TYPE CHECK only (early-exit after basedpyright)                                                      |
| `lint-codex` | ENV + [2] LINT + [3.5]/[3.6] + all of [5] CODEX (incl. pip-audit + bandit) + [5.5]/[5.6] + the stub POST-GATES |
| _(unset)_    | the full gate (every phase) — the only mode any LOCAL/quickmerge run ever uses                                 |

**The slice early-exit `_qg_slice_done` is PHASE-AWARE — typecheck false-green incident (2026-06-10, fixed PM@71a2e103b
/ PR #204).** Each slice exits via `_qg_slice_done <phase>` placed immediately AFTER its phase (`_qg_slice_done tests`
after [3] TESTS; `_qg_slice_done typecheck` after [4] TYPE CHECK), exiting ONLY when `QG_SLICE` equals the just-finished
phase. The original arg-less version matched `tests|typecheck` at the single post-TESTS call site, so
`QG_SLICE=typecheck` exited GREEN **before basedpyright ever ran** — every repo's CI typecheck leg was a silent no-op
(fleet-wide CI false-green; local full runs, `QG_SLICE` unset, were the honest side). **Gotcha for any future slice:**
key the early-exit on the phase NAME and place it after that phase completes — never a bare slice-name match at a shared
call site.

**3-way, not 4-way (pip-audit folds into `lint-codex`):** the entire [5] CODEX section accumulates a SHARED `V`
violation counter (codex + size-checks + pip-audit + bandit → one ceiling check), so pip-audit cannot be split into its
own slice without forking that counter. It rides `lint-codex` — harmless because pip-audit (~3 min, network-bound) runs
in PARALLEL with the dominant pytest leg and is never on the critical path.

**Required-check context is preserved.** The legs emit `Quality Gates (<repo>) / QG slice (tests)` etc. (NOT required).
A `needs:`-all aggregation job **keyed AND display-named `quality-gates-v2`** reports the branch-protection-required
context `Quality Gates (<repo>) / quality-gates-v2` (= `<caller job name> / <reusable job display name>`), green iff
EVERY leg passed (`fail-fast: false` so a failing leg gives full signal but still reds the rollup). **The aggregation
job's `name:` MUST stay literally `quality-gates-v2`** — a friendly label (e.g. `aggregate`) makes the required context
never report → every PR permanently BLOCKED (caught live by the PM canary 2026-06-10).

**Pytest parallelism.** The CI `tests` leg runs `pytest -n auto` (xdist; each leg is alone on its runner — no
shared-host OOM risk). LOCAL stays `-n 1` (the OOM-safe default for the shared dev box); explicit `PYTEST_WORKERS`
overrides both.

**Content-sentinel CI short-circuit.** A `content-gate` job computes the git **TREE hash** (`git rev-parse HEAD^{tree}`
— content-addressed, survives squash/promote re-SHA) folded with the per-repo workflow-file hash, and probes the GHA
cache. A HIT ⟹ every leg skips its work (reports GREEN in seconds); the aggregate still reports the required context (PR
not BLOCKED). The green marker is SAVED only on a real full-green miss (never on a hit / metadata-only). **FAIL-SAFE**:
a miss (incl. GHA cross-branch cache-scope limits) just runs the full gate — it can NEVER false-green or block a PR;
worst case is "no speedup". This kills the redundant byte-identical re-runs (v2 fires on push AND PR to main+staging).
The local `.qg_content_sentinel` / `.qg_last_passed_sha` quickmerge fast-path is UNAFFECTED (CI never reads them; sliced
runs are partial → never write them). SSOT: `plans/archive/2026_06/cicd_v2_latency_reduction_2026_06_10.md`.

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
Step 5: generate workspace-requirements.txt → commit to PM  ← post-cutover
```

Step 5 generates `unified-trading-pm/configs/workspace-requirements.txt` (union of all active repos' deps via
`uv pip compile`; active count derives from `workspace-manifest.json` `repositories` keys excluding `archived_into`).
Developers then run `sync-workspace-venv.sh` to pull the refreshed union. Conflicts in `uv pip compile` signal a version
cascade violation and fail the alignment job.

> **[DELTA 2026-05-22]** **Current state:** Steps 1-4 of `run-version-alignment.sh` are implemented and run. Step 5
> (workspace-requirements.txt generation + PM commit) is not yet wired. **Planned delta:**
> `plans/epics/infrastructure_master.md` — wire Step 5 in `run-version-alignment.sh`. **Target:** Every version
> alignment run produces `configs/workspace-requirements.txt` committed to PM; `sync-workspace-venv.sh` pulls the
> refreshed union.

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

## CODEX_MAX_VIOLATIONS is a ratchet-down, ≤5 ceiling (HARD RULE, operator 2026-06-10)

`CODEX_MAX_VIOLATIONS` (per-repo, in `scripts/quality-gates.sh`) is a **temporary ceiling for PRE-EXISTING lint-codex
violations that only ever shrinks toward 0** — never a budget to grow into. The fleet target is **≤ 5 per repo** (0 is
the ideal); the ratchet contract (`plans/active/codex_violations_ratchet_to_five_2026_06_10.md`):

1. The budget equals the count of CURRENTLY-failing check-classes (each class is a binary `V += 1`; class list SSOT =
   `scripts/quality-gates-base/base-service.sh`).
2. **Every fix ratchets the budget DOWN in the same commit**, with a dated in-file comment naming what cleared and
   citing the driving plan. Never leave a fixed class with a stale higher budget.
3. **A budget BUMP is review-blocking.** A bump caused by a TRANSIENT cross-repo state (e.g. a dep edge removed in
   pyproject but not yet in `workspace-manifest.json` firing manifest-import-alignment) is fixed at the source and
   ratcheted back — not normalised (incident 2026-06-11: deployment-api 24→25→24).
4. **File-size + function-size are first-class violation classes** — a `FUNCTION_SIZE_EXTRA_EXCLUDES` /
   `SIZE_EXTRA_EXCLUDES` glob hiding an oversized file is HIDDEN debt, not an exemption. An exclude is acceptable only
   when (a) scoped to the SPECIFIC carrying module (never a whole package/monolith), and (b) justified in-file with the
   named successor plan + date (see § 2.1 File Size Exceptions).
5. Local == CI counts since the 2026-06-10 `grep -P` → `rg --pcre2` parity fix — a slot proves a ratchet-down locally
   before pushing; CI v2 enforces no regression.

2026-06-11 ratchet state (the big-file splits): registry.py 18,328→YAML+loader (features 0), instruments orchestrator
8,192→16 modules (4), deployment-api DataStatusService 6,663→16 modules (24), seed.py 5,169→JSON+loader (uta pinned 0),
agent-orchestrator server.py 4,505→9 routers (custom gate), MTDS orchestrator 4,219→7 modules (16), strategy
catalog+batch_handler (11→10), MDPS canonical_writer+live_workers (10→7), execution adapters (24→21), deployment-service
8→1, ibkr 4→1, ml-service 5→3.

### Coverage by repo type

| Repo type      | Floor (minimum) | Formula                        |
| -------------- | --------------- | ------------------------------ |
| library        | **80%**         | `max(80, actual_coverage - 1)` |
| service        | **70%**         | `max(70, actual_coverage - 1)` |
| api-service    | **70%**         | `max(70, actual_coverage - 1)` |
| infrastructure | **70%**         | `max(70, actual_coverage - 1)` |
| docs-only      | N/A             | —                              |

**`unified-api-contracts` (UAC) special target — 90% combined (2026-06-10)**: UAC is the T0 schema SSOT; as of
2026-06-10 it runs `branch=True` (combined statement + branch metric) with `fail_under = 90`. The combined metric is
`(lines_covered + branches_covered) / (lines_valid + branches_valid)` — lower than statement-only because branch
coverage is harder. The 90% target is maintained via: (a) targeted tests for all logic modules, and (b) a curated omit
list of pure Pydantic stub packages that have no conditional logic (vendored schema shapes whose coverage adds no signal
— e.g. `external/socket/*`, `external/venus/*`, `external/skybet/*`). See the `[tool.coverage.run] omit` list in
`unified-api-contracts/pyproject.toml` for the canonical omit set. Adding a new stub package to the omit list is
legitimate if: (1) `grep -c "def \|if \|for \|while \|match " <file>` returns 0 (no branching logic), AND (2) the
package has 0 branch hits in `coverage.xml`. Plan: `plans/active/uac_coverage_90pct_2026_06_10.md`.

**`market-data-processing-service` (MDPS) special target — 85% combined (2026-06-10)**: MDPS is a **service** repo (70%
floor) self-elevated to **85% combined** (statement+branch, `branch=True`, `fail_under = 85`). Unlike UAC, MDPS has
almost no pure-stub surface, so the 85% is held almost entirely by **logic + branch-edge tests**, not omit-list shrink:
the only omit is the `__main__.py` entry-point shim (`run_cli()`, no logic). The two modules measured at 0%
(`engine/mock_data_provider.py`, `api/main.py`) are **real runtime logic** (mock_data_provider is imported by
`cli/handlers/process_handler.py`) and were **tested, not omitted**. Actual at lock time: 86.71% (statement 89.7% /
branch 77.3%). The numba-compiled `app/calculators/numba_kernels.py` is left under-covered (needs `NUMBA_DISABLE_JIT=1`
to instrument) — acceptable because 85% clears without it. Plan: `plans/active/mdps_coverage_85pct_2026_06_10.md`.

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
is enforced by `[tool.coverage.report] fail_under` in each repo's `pyproject.toml` — pytest-cov reads it directly (the
base no longer passes `--cov-fail-under` on the CLI; see § "Config SSOT" below).

### Config SSOT — toml is the single home; the base must never shadow it on the CLI (HARD RULE, codified 2026-06-17)

A QG tool's config lives in **exactly one place — `pyproject.toml`** — and the base scripts must NOT pass a CLI flag
that overrides (shadows) that toml value. The shadow is the bug: when both the stub bash var and the toml table carry a
copy of the same setting, they drift silently (the founding incident: MTDS `MIN_COVERAGE=28` in the stub shadowing
`[tool.coverage.report] fail_under=71` in toml via `--cov-fail-under=$MIN_COVERAGE`).

Resolved 2026-06-17 (plan `quality_gates_speed_and_config_ssot_2026_06_09.md`, Phase 1 TIER-A):

- **Coverage** — base-service.sh + base-library.sh **no longer pass `--cov-fail-under`**. pytest-cov reads
  `[tool.coverage.report] fail_under` from toml when the CLI flag is absent (verified: a toml `fail_under` enforces +
  fails the run with no CLI flag). Pre-flip every repo's toml `fail_under` was reconciled to equal its stub
  `MIN_COVERAGE` (zero drift), so the flip was behavior-preserving. `MIN_COVERAGE` survives in the stub ONLY as
  `coverage-floor-guard.sh`'s input for the **system floor (70) + signed-exception** check; it is not the pytest gate.
  The guard warns when the gate is looser than the declared floor (the dangerous drift direction).
- **bandit** — base passes `-c pyproject.toml` so `[tool.bandit]` (skips/excludes) is honored from toml (audited safe:
  no repo's `SOURCE_DIR` carries a finding the existing skips would suppress).
- **pytest test-dir is NOT a shadow** — the base deliberately runs the narrower `tests/unit/` (`PYTEST_UNIT_DIR`, the
  credential-free `--block-network` unit subset), even though toml `testpaths = ["tests"]` is broader. This is a
  functional narrowing (unit vs all), kept on purpose — not a CLI override of the same value.
- **TIER-B knobs stay in the stub (no `[tool.quality-gates]` table — won't-do).** `MAX_DURATION`,
  `CODEX_MAX_VIOLATIONS`, `PYTEST_UNIT_DIR`, pip-audit-ignore lists, `RUN_INTEGRATION`, `PYTEST_WORKERS`, exclude lists
  live in **one home already (the stub)** — there is no competing toml copy, hence no drift and no correctness issue.
  Relocating them to a toml table is cosmetic and would cost a bash-toml parser in both bases + a 22-repo migration; the
  hygiene does not justify the risk. The config-SSOT rule is about **eliminating shadows**, not relocating single-home
  settings.

### Fast tier — NOT BUILT (change-scoped local tier; won't-do, codified 2026-06-17)

A change-scoped "fast tier" (scoping the gate to changed files for the local loop) was designed but **not built**. The
2026-06-17 re-profile showed the only fast-tier-scopable slice left was ~1.1% of wall (size-checks + bandit) — tests
(67%) + basedpyright/typecheck are **always-full by operator decision** (never impact-selected; correctness over a few
minutes), and codex (the one big file-specific phase) is already fast-scoped via the shipped codex `--fast` path. The
wall-time wins were delivered by **per-step optimization** (size-checks batching, the schema-provenance O(n²) fix, the
pip-audit/bandit/actionlint content-hash caches), not by a fast tier. **The merge tier is always authoritative** — it
runs the full gate with full coverage at quickmerge Pass-1 / CI `quality-gates-v2`; nothing local can weaken it.

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
| Domain clients from UDC not UTL            | rg unified_trading_services.\*DomainClient                  | quality-gates-service-template.sh [5]                                                           | ✓ In template                                          |

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

## Library-Repo QG Carveout Patterns

Library repos (UAC, UTL, etc.) use the same `base-library.sh` body as service repos but expose additional per-repo
override variables to suppress false-positive QG checks on files that intentionally break the normal rules. These
carveouts are in the repo's `scripts/quality-gates.sh` config stub above the `source base-library.sh` line.

**These overrides are for library repos only.** Service repos must not use them — service code that needs a size or
import exception should be refactored, not carved out.

### `UAC_CANONICAL_EXEMPT=true`

**What it disables**: The "no internal deep-imports" check that verifies service code never imports from
`unified_api_contracts.canonical.*` directly (only through the public facade `from unified_api_contracts import ...`).

**When valid**: Only for `unified-api-contracts` itself. UAC is the schema/contract owner — it must be allowed to import
its own sub-modules internally.

**Pattern (in `scripts/quality-gates.sh`)**:

```bash
UAC_CANONICAL_EXEMPT=true  # UAC is the schema repo — internal imports are allowed
```

**Never use for service repos.** Service deep-import violations (e.g. `from unified_api_contracts.canonical...`) must be
fixed by switching to the facade import.

---

### `SIZE_EXTRA_EXCLUDES`

**What it does**: Passes additional `! -path <glob>` exclusions to the file-size check so named files are not flagged
for exceeding the 900-line limit.

**When valid**: Closed-set enumerations — venue registries, error code tables, instrument seed catalogues, re-export
facades — where splitting the file would harm grep-ability without reducing complexity. New files should not be added to
this list unless they are provably closed-set enumerations.

**Pattern**:

```bash
SIZE_EXTRA_EXCLUDES=(
    "./unified_api_contracts/__init__.py"       # public re-export facade
    "./unified_api_contracts/registry/defi_reserve_params.py"  # closed-set venue params
    # ... additional closed-set registry files
)
```

**Adding a new entry**: requires a comment explaining WHY the file is a legitimate exception (closed-set enumeration /
generated / provenance doc). Without a comment, the PR is review-blocked.

---

### `GCP_PROJECT_ID_EXCLUDE_GLOBS`

**What it does**: Passes additional exclusion globs to the `GCP_PROJECT_ID` literal-string check that prevents hardcoded
project IDs appearing in source files.

**When valid**: Files that contain GCS bucket names or project IDs purely as documentation — provenance comments,
test-fixture URI shapes, or module-level string constants that document where live data lives. These are NOT runtime
config paths; they never reach `get_storage_client()` or `resolve_bucket_name()`.

**Pattern**:

```bash
GCP_PROJECT_ID_EXCLUDE_GLOBS=(
    "!**/data_source_continuity.py"                 # VIX_PROD_BUCKET/VIX_DEV_BUCKET as constants
    "!**/defi_prediction_instrument_seeds.py"       # docstring cites live GCS paths as provenance
    "!**/registry/generators/cefi.py"               # real_backfill_sample_uri is doc of path shape
)
```

**Never use to suppress actual runtime config.** Bucket lookups at runtime MUST go through `resolve_bucket_name(...)`
(QG STEP 5.69 enforces). This carveout only covers static strings that are documentation artifacts, not lookup keys.

---

### `BROAD_EXCEPT_EXTRA_EXCLUDES`

**What it does**: Passes additional glob patterns to the broad-`except` check (bandit B001 / ruff E722) so named files
are not flagged for `except Exception:` or bare `except:` patterns.

**When valid**: Registry dispatchers and mapping resolvers that must catch all exception types to isolate faults
per-entry (e.g., `venue_context.py`, `mapping_resolver.py`). The catch-all prevents one bad entry from silently dropping
the rest of the registry.

**Pattern**:

```bash
BROAD_EXCEPT_EXTRA_EXCLUDES=("**/venue_context.py" "**/mapping_resolver.py")
```

**New entries require a comment** explaining the catch-all rationale. Do not use to paper over lazy exception handling
in business-logic code — use specific exception types there.

---

### Adding a new library carveout

1. Identify whether it fits an existing category above. If not, file an issue doc in `plans/active/issues/`.
2. Add the variable to the repo's `scripts/quality-gates.sh` stub above the `source base-library.sh` line.
3. Include an inline comment explaining WHY the carveout is legitimate for that specific file/pattern.
4. Update `QUALITY_GATE_BYPASS_AUDIT.md` § 2.x with the same justification.
5. Reference this section in the comment:
   `# See codex/06-coding-standards/quality-gates.md § Library-Repo QG Carveout Patterns`

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

Enforces [`manifest_schema_final_gate_2026_05_09.md`](../../plans/active/manifest_schema_final_gate_2026_05_09.md) Phase
4 "explicit-or-fail" contract + CLAUDE.md [**Live = batch (CRITICAL)**](../../cursor-configs/CLAUDE.md): the only
legitimate difference between batch and live for a given `(asset_group, data_type)` is which SOURCE serves it — so the
manifest must record that source. Manifest schema v8 makes `pipeline_mode` a first-class column; this ratchet keeps it
explicit at the write boundary. Every `ManifestWriter.record_captured()` / `record_empty()` / `record_failed()` /
`record_expected_unattempted()` call (and the legacy `ManifestWriter.add()` path) MUST pass an explicit
`pipeline_mode=PipelineMode.<source>` kwarg matching the UAC `SOURCE_PRIORITY` top entry. Implicit /
orchestrator-inherited `pipeline_mode`, or `**kwargs` that silently swallow it, is the anti-pattern this catches at PR
time.

**Reference incident**: the same 2026-05-05 MDPS data-correctness class as STEP 5.67 — when the manifest can't say which
source produced a row, batch-vs-live reconciliation can't tell whether a divergence is a real alpha gap or just a
slower-source artefact. The pre-audit (PM@`237d00b7` slot 2 sub-agent) found 26 MTDS files / 102 callsites with an
inherited-or-implicit `pipeline_mode`; the slot-2 Phase 4 sweep cleared MDPS / instruments / deployment-api; the residue
is baselined pending the MTDS sweep (gated on the operator's PipelineMode-enum triage) + the features-consolidation
sweep.

### How it works

1. **Record-method name set + whitelist marker** — in
   [`unified-trading-pm/scripts/quality_gates/check_pipeline_mode_explicit_at_record_calls.py`](../../scripts/quality_gates/check_pipeline_mode_explicit_at_record_calls.py):
   `RECORD_METHOD_NAMES` = `record_captured` / `record_empty` / `record_failed` / `record_expected_unattempted` / `add`
   (the legacy path). A call passes if and only if it has a literal `pipeline_mode=` keyword, OR the call's source line
   carries the inline marker `# QG-allow: pipeline-mode-not-applicable` (the rare legitimate exemption — e.g. a
   base-class method that re-forwards `**kwargs`).
2. **Baseline** — `unified-trading-pm/scripts/quality_gates/pipeline_mode_explicit_baseline.yaml` is a **SHRINKING
   ratchet**: each entry is a currently-known occurrence keyed `(repo, file, line, method)` with `status`
   (`pending_phase_4_mtds` / `pending_phase_4_features`) + `successor` (the plan phase that clears it). As of 2026-05-12
   the baseline holds **114** entries (97 market-tick-data-service + 6 features-service + 11 unified-trading-library).
   DELETE an entry the moment its successor sweep ships the explicit kwarg; never ADD one — a new implicit `record_*`
   call is a bug, not a baseline item.
3. **AST walker** — parses every `.py` in scope (excluding `.venv*` / `node_modules` / `build` / `dist` / `__pycache__`
   / `scripts/` / `tests/`) and flags any `ast.Call` whose `func` is an `ast.Attribute` named in `RECORD_METHOD_NAMES`
   and whose keyword set lacks `pipeline_mode` (and whose line lacks the whitelist marker). Counts only real `Call`
   nodes — a docstring / comment / dict-key / string-literal reference to a method name does not trip it (the naive
   `grep -L "pipeline_mode="` approach returned 7 false positives; the AST walk is authoritative).
4. **QG wiring** — `scripts/quality-gates-base/base-service.sh` STEP 5.70 invokes the checker scoped to the calling repo
   (`--workspace-root <ws> --scope <repo> --source-dir <pkg>`). Baselined occurrences → warnings (exit 0); a
   non-baselined occurrence → ERROR + `file:line` + the baseline's `default_successor` → exit 1. A workspace-wide sweep
   (no `--scope`) walks every immediate sub-dir with a `pyproject.toml`. If the checker file is absent (older PM
   checkout), the STEP is skipped clean. Unit tests:
   `scripts/quality_gates/test_check_pipeline_mode_explicit_at_record_calls.py` (11 cases).

### Adding a new occurrence? Don't — fix it instead.

If STEP 5.70 fails on YOUR code, pass `pipeline_mode=PipelineMode.<source>` for the UAC `SOURCE_PRIORITY` top entry of
the `(asset_group, data_type)` you're writing (the source that would actually serve that data in live mode —
`BATCH_DATABENTO` / `BATCH_TARDIS` / `BATCH_API_FOOTBALL` / `BATCH_INSTRUMENTS_SERVICE` for self-published catalog rows,
etc.). The only legitimate baseline edits are **removal** when a successor sweep lands, or updating the `line:` of an
existing baselined occurrence that shifted in the same commit. If a UAC `PipelineMode` enum member genuinely doesn't
exist for your source yet, file the gap (precedent: `mtds_pipeline_mode_sweep_ambiguities_2026_05_12.md`) and stamp the
closest documented workaround (precedent: instruments-service stamps `BATCH_API_FOOTBALL` for footystats pending the
enum extension).

### Composes with

- [**Live = batch (CRITICAL)**](../../cursor-configs/CLAUDE.md) — STEP 5.70 is the static enforcement of "the only
  legitimate batch/live diff is which SOURCE serves a given `(asset_group, data_type)`": no recorded source ⇒
  unverifiable batch-vs-live recon.
- [**Availability manifest v5+**](../../cursor-configs/CLAUDE.md) +
  [`codex/02-data/availability-manifest-and-data-status.md`](../02-data/availability-manifest-and-data-status.md) —
  `pipeline_mode` joins the v8 manifest column set alongside `service_emission_state` / `last_emission_decision_at` /
  `expected_window_completeness_fraction`; Phase 4.DEFAULT-REMOVAL drops the transitional `None` defaults from the 5
  `record_*` signatures so the column is explicit-or-fail.
- STEP 5.67 (banned NaN-placeholder AST-walk) + STEP 5.65 (removed-symbol AST-walk) + STEP 5.64 (bundled-shard cluster
  validation AST-walk) are the implementation precedents — STEP 5.70 follows the same baseline-aware-ratchet +
  `ast.walk()` shape applied to the explicit-pipeline-mode problem.
- `manifest_schema_final_gate_2026_05_09.md` Phase 4.MTDS / Phase 4.FEATURES / Phase 4.DEFAULT-REMOVAL — the successors
  that shrink the baseline to zero; Phase 4.GREP-VERIFY is the phase that shipped this checker + baseline.

---

## SSOT Alignment Validation (Documentation Quality Gates)

**Purpose:** Prevent documentation drift **before commit** by validating alignment across Codex docs, UTD configs, and
Epics.

### What It Catches

The `validate-alignment.py` script runs as a pre-commit hook in `unified-trading-codex` and checks:

1. **Banned Terms**
   - ❌ Non-canonical bucket patterns (e.g., `gs://market-data-raw/` instead of the env-tiered
     `gs://market-data-tick-{category}-{env}-{project_id}/`; resolve via `resolve_bucket_name()`, never inline)
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
local QG runs pre-format all file types before any commit.

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
   - No `google.cloud` imports (use `unified_trading_library` abstractions)
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
run_timeout 120 basedpyright unified_trading_library/
```

**Note:** The `perl` fallback is essential for macOS environments where GNU coreutils may not be installed. If
`run_timeout` is not found (exit 127), run `workspace-bootstrap.sh` to install the standalone binary — do not source
`quality-gates.sh` as a workaround.

### Memory Governance (OOM Prevention)

When 8+ parallel slot agents each run `quality-gates.sh` concurrently, peak memory can exceed available RAM and trigger
the kernel OOM-killer — taking down VS Code and all worker sessions. Memory governance rules are documented in
[`quality-gates-memory-governance.md`](quality-gates-memory-governance.md).

**Key knobs** (see that doc for defaults, per-box recommendations, and macOS compatibility notes):

| Knob             | Declared in             | Default         | Purpose                                               |
| ---------------- | ----------------------- | --------------- | ----------------------------------------------------- |
| `QG_MEM_CAP`     | `base-service.sh`       | `10G`           | Per-subprocess hard cap via `systemd-run` cgroup      |
| `PYTEST_WORKERS` | `base-service.sh`       | `1`             | xdist worker count (was `cpu_count // 4` pre-2026-05) |
| `diagnosticMode` | `.vscode/settings.json` | open files only | IDE basedpyright crawl scope                          |

Read [`quality-gates-memory-governance.md`](quality-gates-memory-governance.md) before adjusting any of these knobs.

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

- Runs `uv lock` when `pyproject.toml` changes (creates/updates `uv.lock`; cross-platform; fast when unchanged). **When
  you bump a dependency FLOOR you MUST commit the regenerated `uv.lock` alongside `pyproject.toml` in the same commit**
  — CI installs the committed lock via `uv sync --frozen` (no re-resolution), so a floor bump without the lock regen
  silently installs the stale lock. A bare `version =` bump needs no lock regen (`--frozen` tolerates it). SSOT:
  `codex/08-workflows/ci-cd-flow.md` § "Dependency promotion".
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

### `PYTEST_UNIT_DIR` override (Phase 8, 2026-05-15)

**Added 2026-05-15 — Phase 8 / slot 6 doc-currency audit.**

Services whose unit tests are NOT under the canonical `tests/unit/` root can override the pytest target directory by
setting `PYTEST_UNIT_DIR` **before** `base-service.sh` runs its test step:

```bash
# In service's scripts/quality-gates.sh — set before sourcing base-service.sh
PYTEST_UNIT_DIR="tests/"   # e.g. features-service: per-family CLIs share root tests/
```

`base-service.sh` line 209 reads: `PYTEST_UNIT_DIR="${PYTEST_UNIT_DIR:-tests/unit/}"` — the default is `tests/unit/`;
override only when the layout genuinely differs.

**When to use**: services with per-family CLI layouts (e.g. `features-service`) where tests live directly under `tests/`
without a `unit/` subdirectory. **Never** use to broaden the pytest scope to include integration tests in the unit pass
— integration tests run in a separate step.

Reference: `features-service/scripts/quality-gates.sh:28` (`PYTEST_UNIT_DIR="tests/"`). Issue doc that surfaced the gap:
`plans/active/issues/features_service_qg_test_path_mismatch_2026_05_15.md`. PM commit: `c7786b2f`.

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

**Service-extended standard** (de-facto pattern for all service repos as of 2026-05-19 audit):

```toml
select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "SIM", "RUF", "G"]
```

Additional categories: **N** (PEP 8 naming), **UP** (pyupgrade modernization), **B** (flake8-bugbear), **C4**
(flake8-comprehensions), **SIM** (flake8-simplify), **RUF** (Ruff-native rules), **G** (flake8-logging-format).

Repos with this extended config: strategy-service, instruments-service, market-tick-data-service, features-service,
unified-api-contracts. Repos with custom reduced configs (track separately): execution-service (individual rule codes),
unified-trading-library (minimal), batch-live-reconciliation-service (missing N,C4,RUF,G). These reduced-config repos
have not been updated to the extended standard because doing so may expose latent violations requiring separate
remediation.

**Baseline floor** (codex minimum — no repo may go below): `["E", "F", "W", "I"]`. deployment-service was missing `W`
and was corrected in PM@slot-4-2026-05-19.

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
include = ["<package_name>"]   # e.g. "unified_trading_library"
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

### Restoring strict basedpyright on a library (the UTL campaign pattern, 2026-06-08)

When a library's `reportUnknown*` strict rules surface a large residual (UTL: 965 errors), the canonical order of ops
(SSOT: `plans/active/utl_full_quality_gates_green_2026_06_01.md`):

1. **Stubs first.** Add type-stub packages to the flat deps + `uv lock` — they auto-resolve a large fraction before any
   hand-annotation. UTL added `pyarrow-stubs>=20` (pyarrow ships no `py.typed`) + expanded
   `boto3-stubs[s3,secretsmanager,logs,sns,sqs]` to cover every boto3 service it uses (965→842, no new errors).
   `pandas-stubs` is already transitive via UAC.
2. **Annotate the residual** module-by-module: explicit param/return/local annotations + `typing.cast()` at untyped-dep
   boundaries + a **local structural `Protocol`** for an untyped SDK object (the cleanest fix for
   `reportUnknownMemberType` on a multi-method client — see `cloud_interface/providers/gcp.py`
   `_GCSBlob`/`_GCSBucket`/`_GCSClient`). When the Protocol set bloats a file past the 900-line limit, extract it to a
   sibling `_*_sdk_protocols.py` with `__all__` (the `__all__` suppresses `reportUnusedClass` cleanly — do NOT add a
   `reportUnusedClass = "none"` global override).
3. **Exemptions are NARROW + per-line + exact-rule only.** A genuinely stub-limited boundary (pyarrow stubs carry
   `Unknown` param types; GCP proto-generated methods) may take a single `# pyright: ignore[exactRule]  # <dep> reason`.
   **Banned:** blanket file-level `# pyright: reportX=false`, broad `# type: ignore` (no rule code), or a global
   pyproject `"none"` downgrade — these "institutionalise the downgrade." Net-new broad/blanket suppressions must be 0.

### Library SHA-sentinel gap (`quickmerge --agent` on a library) — RESOLVED 2026-06-10

`quickmerge --agent`'s Stage-3 fast-path verifies `.qg_last_passed_sha == HEAD`. **Both base scripts now write the SHA
sentinel on a green run**: `base-service.sh` always did; `base-library.sh` gained the parity write 2026-06-10 (see the
`git rev-parse HEAD > .qg_last_passed_sha` block near the content-sentinel write, ~line 1170) — library repos source the
PM template directly, so the fix propagates fleet-wide with no per-repo rollout. The interim hand-bridge
(`git rev-parse HEAD > .qg_last_passed_sha` after a green run) is RETIRED — never hand-write the sentinel; a green
`quality-gates.sh` produces it. History: `plans/archive/issues/base_library_qg_sha_sentinel_gap_2026_06_08.md`.

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
> Batch/live invariant:
> [`../04-architecture/batch-live-architecture.md`](../04-architecture/batch-live-architecture.md). Pre-audit source:
> `batch_live_design_symmetry_preaudit_2026_05_10.md § 1.Tab1`.
>
> Status as of 2026-05-14: L1+L5 enable DAY-1 (0 violations); L2+L3 enable after fix-batch lands (Tab 3, ~21+2
> violations); L4+L6 post-cutover (Block G1). L7 is an ongoing ratchet sweep.

---

### STEP L1: DataType Mode-Prefix Ban (ENABLED as STEP 5.75)

**Status**: ENABLED — STEP 5.75 wired 2026-05-14. 0 violations in pre-audit; gate enabled at zero ratchet cost.

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

**Enforcement**: `scripts/quality-gates-base/base-service.sh` — AST-walk on UAC DataType enum + consumer service enums.
ENABLED as STEP 5.75 in `scripts/quality-gates-base/base-service.sh` (2026-05-14).

**Composes with**: STEP L5 (unified DataType enum, no per-mode fork) · STEP 5.70 (`pipeline_mode` at `record_*`).

---

### STEP L2: Mode-Conditional-Outside-Seam (ENABLED as STEP 5.77)

**Status**: ENABLED — STEP 5.77 wired 2026-05-14. Pre-audit ~21 violations resolved; Tab 3 fix-batch shipped; 0
violations across features/strategy/MDPS/instruments-service.

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

**Enforcement**: `scripts/quality-gates-base/base-service.sh` STEP 5.77 — AST-walk for `If` nodes whose test is a
mode-enum comparison, excluding the 4 seam files. ENABLED 2026-05-14 after Tab 3 fix-batch (0 violations confirmed).

**Composes with**: STEP L3 (RuntimeMode SSOT) · `mode-axis-discipline.md` AP-1 · `batch-live-architecture.md §2`.

---

### STEP L3: RuntimeMode Single SSOT (ENABLED as STEP 5.78, partial)

**Status**: ENABLED (partial) — STEP 5.78 wired 2026-05-14. UAC/UTL clean (UTL re-exports RuntimeMode from UAC
canonical). UI deliberate-copy (`unified-internal-contracts/modes.py`) DEFERRED post-cutover — design call needed.

> **[DELTA 2026-05-22]** **Current state:** UAC + UTL sides clean; UI type `ExecutionMode` redeclaration is a known
> violation exempted by baseline (1 violation suppressed). **Planned delta:**
> `plans/epics/batch_live_symmetry_master.md` Tab 3 — UI imports `RuntimeMode` from UAC schema bundle;
> `rg 'class RuntimeMode'` returns exactly 1 hit. **Target:** `rg 'class RuntimeMode'` returns exactly 1 hit; 0 baseline
> suppressions.

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

**Enforcement**: `scripts/quality-gates-base/base-service.sh` STEP 5.78 — `rg 'class RuntimeMode'` across workspace,
excluding the canonical file. ENABLED 2026-05-14 after Tab 3 fix-batch.

**Composes with**: STEP L2 (mode-conditional branches) · `mode-axis-discipline.md` AP-3 ·
`batch-live-architecture.md §12`.

---

### STEP L7: `record_captured()` assert_available_at_present (ongoing sweep)

**Status**: Ongoing ratchet — baseline shrinks per sweep cycle. Violations added to fix-list; ratchet prevents new ones.

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

**Fix**: pass `assert_available_at_present=True` to `record_captured()`, or ensure the caller sets `available_at` on the
parquet row before calling. Never set `available_at` at read-time.

**Enforcement**: `scripts/quality-gates-base/base-service.sh` — `rg 'record_captured'` + AST-walk for keyword
`assert_available_at_present=False` overrides + raw `ManifestWriter.add()` without stamp check. Ongoing ratchet:
baseline anchored at pre-audit count; new violations fail immediately; existing baseline shrinks as sweep lands.

**Composes with**: STEP 5.67 (banned NaN-placeholder) · STEP 5.70 (`pipeline_mode` explicit) · UAC
`availability_semantics.AVAILABILITY_AT_SEMANTICS` · writegate plan Phase 3.D.5.

---

## STEP 5.79: dockerfile-base-pin

**What it catches**: production Dockerfiles using mutable `:tag` references (including `:latest`) instead of
digest-pinned `@sha256:<hex>` base images.

**Rationale**: Docker image tags are mutable pointers. When an upstream registry owner re-tags an image (common for
`:latest`, `:1.x` tracks), the next pull silently fetches a different layer than what was tested. A `@sha256:` digest is
immutable — the exact layers you tested are the exact layers that run in production.

**Scope**: all repos containing `Dockerfile` or `Dockerfile.*` files (not `.venv`, `build`, `node_modules`).

**Ratchet**: WARN before 2026-05-15 → FAIL (exit 1) from 2026-05-15. Remediation: Phase 5 of
`deployment_and_qg_strategy_implementation_2026_05_13.md`.

**How to comply**:

```dockerfile
# WRONG — mutable tag
FROM python:3.13-slim

# WRONG — latest
FROM python:latest

# CORRECT — digest-pinned
FROM python:3.13-slim@sha256:abc123...
```

**Exemptions checked automatically**:

- `FROM scratch` (no registry layer)
- Multi-stage local alias re-references (`FROM build-stage AS runtime` within the same file)
- `--platform` flag is stripped before checking

**How to find the digest**:

```bash
docker pull python:3.13-slim && docker inspect python:3.13-slim --format '{{index .RepoDigests 0}}'
# or: crane digest python:3.13-slim
```

**Composes with**: `codex/06-coding-standards/dockerfile-standards.md` — full Dockerfile rules;
deployment_and_qg_strategy_implementation_2026_05_13.md Phase 5 (image-build pipeline).

---

## STEP 5.80: tarball-manifest-present

**What it catches**: `deployment-service/scripts/vm/create-code-tarballs.sh` that does NOT write a sibling
`<repo>@<commit-sha>.manifest.json` alongside each tarball upload to GCS.

**Scope**: `deployment-service` only. All other repos: auto-skip.

**Rationale**: VMs launched from tarballs must assert at boot-time that the tarball they're running matches a known
commit SHA — preventing stale re-deploy. Without the sibling manifest (containing `repo`, `commit_sha`,
`pyproject_version`, `git_status_clean`, `created_at`, `created_by`), the VM boot assertion has no source of truth to
compare against and silently skips.

**Ratchet**: WARN before 2026-05-15 → FAIL from 2026-05-15. Remediation: Phase 3 of
`deployment_and_qg_strategy_implementation_2026_05_13.md`.

**Compliant pattern** in `create-code-tarballs.sh`:

```bash
# After uploading tarball to GCS, write sibling manifest
cat > "/tmp/${REPO_NAME}@${COMMIT_SHA}.manifest.json" <<EOF
{
  "repo": "${REPO_NAME}",
  "commit_sha": "${COMMIT_SHA}",
  "pyproject_version": "${VERSION}",
  "git_status_clean": ${GIT_CLEAN},
  "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "created_by": "create-code-tarballs.sh"
}
EOF
gsutil cp "/tmp/${REPO_NAME}@${COMMIT_SHA}.manifest.json" "gs://${BUCKET}/tarballs/"
```

**Composes with**: `codex/05-infrastructure/vm-tarball-deployment.md`; STEP 5.81 (env-block).

---

## STEP 5.81: tarball-env-block

**What it catches**: `deployment-api` Python source that contains tarball-deploy code but lacks an environment-tier
guard preventing staging/prod uploads without an explicit override.

**Scope**: `deployment-api` only. All other repos: auto-skip.

**Rationale**: tarballs deployed to staging/prod must be intentional. Without a gate, an operator can accidentally call
the tarball-deploy endpoint against production with the wrong commit — no confirmation, no blast-radius check, no audit
trail. The env-tier block forces `DEPLOYMENT_ENV` to be checked before any staging/prod tarball upload proceeds.

**Ratchet**: WARN before 2026-05-17 → FAIL from 2026-05-17. Remediation: Phase 1 of
`deployment_and_qg_strategy_implementation_2026_05_13.md`.

**Compliant pattern** (deployment-api Python source must contain one of):

```python
DEPLOYMENT_ENV = config.deployment_env  # from UnifiedCloudConfig
staging_override: bool  # explicit caller flag
allow_tarball: bool     # opt-in gate
```

**Check logic**: QG greps for
`DEPLOYMENT_ENV|deployment_env|staging_override|prod_override| allow_tarball|tarball_override|env_tier_check` alongside
tarball-related code. If tarball code exists but no env guard is found → FAIL.

**Composes with**: `deployment-and-qg-strategy.md` § env-locking (B-001 Phase 1); STEP 5.80.

---

## STEP 5.82: image-build-on-staging-merge

**What it catches**: repos with a staging-branch GitHub Actions workflow that do NOT also trigger a Cloud Build image
build on merge to staging.

**Rationale**: if staging deploys consume a Docker image from Artifact Registry but the workflow only deploys (no build
step), the image used is whatever was last built — potentially many cycles stale. The staging image MUST be freshly
built from the exact commit being staged before the deploy runs.

**Ratchet**: WARN before 2026-05-17 → FAIL from 2026-05-17. Remediation: Phase 5 of
`deployment_and_qg_strategy_implementation_2026_05_13.md`.

**Check logic**: QG looks for any staging-branch trigger in `.github/workflows/`, then verifies at least one workflow
file in the same directory references Cloud Build (`cloudbuild`, `cloud-build`, `gcloud builds`,
`google-github-actions/deploy-cloudrun`, `buildTrigger`). FAIL if staging trigger present + no build invocation found.

**Compliant patterns**:

```yaml
# Option A: gcloud builds submit in workflow
- run: gcloud builds submit --config cloudbuild.yaml

# Option B: google-github-actions/deploy-cloudrun (builds inline)
- uses: google-github-actions/deploy-cloudrun@v2
```

**Repos currently showing PENDING-RATCHET warning** (as of 2026-05-15 audit): check `deployment-api`,
`execution-service`, and any repo with a `.github/workflows/deploy-staging.yml`.

**Composes with**: `deployment-and-qg-strategy.md` § image-build cutover path; STEP 5.81.

---

## quality-gates.sh Boilerplate DRY Consolidation Proposal

> **Status**: PENDING OPERATOR ACK — doc-only. No code change to base-service.sh until operator approves. Audited
> 2026-05-15 (slot 8). Rollout via `rollout-quality-gates-unified.py` once acked.

### Finding 1: UEI Lifecycle block (14 repos duplicate, 5 repos stale)

The canonical 15-line lifecycle block appears verbatim in every repo's `quality-gates.sh`:

```bash
log_section "[5.X/6] UEI LIFECYCLE EVENT ENFORCEMENT (STARTED/STOPPED/FAILED)"
if rg -q 'fastapi_uei_lifespan\s*\(' --type py "$SOURCE_DIR" 2>/dev/null; then
    log_success "UEI lifecycle: fastapi_uei_lifespan (canonical HTTP wiring in UTL)"
elif rg -q 'ServiceBootstrap\s*\(' --type py "$SOURCE_DIR" 2>/dev/null; then
    log_success "UEI lifecycle: ServiceBootstrap (canonical CLI wiring in UTL)"
else
    for event in STARTED STOPPED FAILED; do
        # -U: allow multiline call sites (e.g. log_event(\n  "STARTED", ...))
        run_timeout 30 rg "log_event.*\"${event}\"" "${SOURCE_DIR}" --type py -U -q \
            || log_warn "Missing log_event('${event}') in ${SERVICE_NAME} — see codex 03-observability/lifecycle-events.md"
    done
fi
```

**Repos with canonical pattern (14)**: batch-live-reconciliation-service, client-reporting-api, deployment-api,
deployment-service, e2e-testing, execution-service, features-service, ibkr-gateway-infra, instruments-service,
market-data-processing-service, pnl-attribution-service, position-balance-monitor-service, strategy-service,
system-integration-tests, trading-agent-service, unified-trading-api.

**Repos with OLD pattern — missing fastapi/ServiceBootstrap check (5)**: alerting-service, market-tick-data-service,
ml-inference-service, ml-training-service, risk-and-exposure-service.

Old pattern (4 lines, no UTL shortcut check):

```bash
log_section "[5.X/6] UEI LIFECYCLE EVENT ENFORCEMENT (STARTED/STOPPED/FAILED)"
for event in STARTED STOPPED FAILED; do
    run_timeout 30 rg "log_event.*\"${event}\"" "${SOURCE_DIR}" --type py -q \
        || log_warn "Missing log_event('${event}') in ${SERVICE_NAME} — ..."
done
```

**Proposal**: move canonical block into `scripts/quality-gates-base/base-service.sh` directly after STEP 5.62
(health-router check). Remove from all per-repo `quality-gates.sh` files. Update 5 stale repos to canonical pattern as
part of same rollout. One code change, one propagation pass.

**REQUIRES OPERATOR ACK** before implementation.

---

### Finding 2: PERIPHERAL_DIR block pattern (2 repos, potentially expanding)

`features-service` and `market-tick-data-service` both have a PERIPHERAL_DIR block pattern (checking
`e2e-testing/scripts/` subdirs for import health). The pattern is unique to primary consumers of peripheral script
directories (per CLAUDE.md hard rule). Each block is custom to the specific peripheral dir path and primary consumer —
NOT a candidate for base-service.sh consolidation, because the path is repo-specific.

**Action**: keep per-repo. Document in CLAUDE.md § "Peripheral Script Directories" that the block lives in the primary
consumer's `quality-gates.sh`, not base-service.sh.

---

### Finding 3: PYTEST_UNIT_DIR opt-in (1 repo — features-service)

`features-service` sets `PYTEST_UNIT_DIR="tests/"` before the `source base-service.sh` line to override the default
`tests/unit/` path. This covers per-family test layouts (350+ files spread across `tests/<family>/unit/`). This is
intentional and repo-specific.

**Action**: document opt-in pattern — see § "PYTEST_UNIT_DIR per-family override" below.

---

### PYTEST_UNIT_DIR per-family override

Some services organise tests as `tests/<family>/unit/` rather than the default `tests/unit/`. The flat `tests/unit/`
default in `base-service.sh` will only collect ~46 tests (the cross-cutting unit tests); per-family tests are silently
skipped.

**To override**: set `PYTEST_UNIT_DIR` BEFORE the `source base-service.sh` line:

```bash
PYTEST_UNIT_DIR="tests/"           # collect all tests recursively
source "${WORKSPACE_ROOT}/unified-trading-pm/scripts/quality-gates-base/base-service.sh"
```

**When to use**: only when tests are structured as `tests/<family>/unit/` AND the default `tests/unit/` path would miss
them. Verify by counting: if `find tests/unit/ -name 'test_*.py' | wc -l` returns <5% of
`find tests/ -name 'test_*.py' | wc -l`, add the override.

**Side effect**: `PYTEST_UNIT_DIR="tests/"` also collects `tests/integration/` — integration tests run unless
`RUN_INTEGRATION=false` guards them (base-service.sh skips integration folder by name when `RUN_INTEGRATION=false`;
spot-check that the integration-test exclusion logic still holds).

> **[DELTA 2026-05-22 — features-service cefi/ subdir QG coverage]** **Current state:** features-service
> `quality-gates.sh` runs with `PYTEST_UNIT_DIR="tests/"` collecting all per-family tests recursively (reference:
> `features-service/scripts/quality-gates.sh:28`). This includes the `cefi/` subdomain added by
> `phase5_features_streaming_carry_staked_basis_mvp_2026_05_19.md` Phase A:
> `features_service/cefi/calculators/perp_funding_rates.py` +
> `features_service/cefi/live/perp_funding_compute_runner.py` + `tests/cefi/unit/test_perp_funding_rates.py` (6-case
> unit tests) + `tests/cefi/unit/test_live_runner.py`. **Confirmed:** features-service@e43f8370 QG passes with all cefi/
> unit tests included (7085 tests pass at features-service@a4fadcf2). The `cefi/` subdomain is NOT a peripheral dir — it
> is wired into the main `quality-gates.sh` via `PYTEST_UNIT_DIR="tests/"`. No additional QG wiring needed. **Note:**
> `@pytest.mark.requires_credentials` integration tests in `tests/cefi/integration/` are skipped by default (no real
> venue credentials in CI). These tests are skipped, not excluded — they will run when credentials land per
> `BLOCKED-CREDENTIALS` workflow.

---

## STEP 5.94 + 5.95 — grep-able-rule ratchets (fallback-imports · DTZ · TID251) — SHIPPED 2026-06-10

Three CLAUDE.md rules that previously relied on agent memory are CI-enforced count-ratchets (PM@71a2e103b; plan
`plans/archive/2026_06/harden_grepable_rules_into_ci_gates_2026_06_02.md`):

- **STEP 5.94** — `scripts/quality_gates/check_no_fallback_imports.py` (AST): flags
  `try: import X / except ImportError:` fallback shims (incl. re-raise wrappers + imports-only try-bodies with
  broad/bare except). Per-line opt-out: `# noqa: fallback-import` + reason. Baseline:
  `no_fallback_imports_baseline.yaml` (seed 75 fleet-wide).
- **STEP 5.95** — `scripts/quality_gates/check_ruff_rule_ratchet.py`: ruff `--isolated` runs of the pinned **DTZ** set
  (DTZ001-007/011/012/901 — UTC-datetimes-always) + **TID251** banned-api (`google.cloud`/`boto3` direct imports —
  cloud-agnostic-I/O; UTL `cloud_interface/` path-exempt). Config SSOT:
  `scripts/pyproject-templates/canonical-tool-sections.toml`. Baseline: `ruff_rule_ratchet_baseline.yaml` (seed 180
  dtz + 211 tid251). Per-line opt-out: ruff `# noqa: DTZ00x|TID251` + one-line reason — **on the `from`/call line the
  rule reports** (a parenthesized-import continuation line does NOT suppress; pair with `RUF100` in repos whose own ruff
  config doesn't enable the rule, e.g. `# noqa: TID251, RUF100 -- reason`).

Mechanics (both): SHRINKING per-repo baselines — counts only ratchet DOWN (`--update-baseline` after fixing sites); a
count above baseline = a NEW violation landed → fix it, never raise the number. **Scoped `--update-baseline` only
rewrites the rows it scanned** — unobserved repos carry forward verbatim (the 2026-06-10 incident: an early version
treated unobserved repos as seen=0 and the down-clamp zeroed 24 repos' rows; fixed same day + baselines restored).
Enforcement needs NO per-repo rollout: the steps live in `base-service.sh`/`base-library.sh`, sourced (local) /
PM-cloned (CI) by every repo's `quality-gates.sh` stub.

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

---

## Proposed STEP 5.83+ Additions (PENDING OPERATOR APPROVAL)

> **Status**: PROPOSAL — doc-only. Each STEP below requires operator approval before being added to `base-service.sh`.
> None of these are active enforcement today. Authored 2026-05-15 (slot 8). Approval mechanism: operator comments
> `[approve-step-5.83]` / `[approve-step-5.84]` / etc. in ping file.

### STEP 5.83: no-bare-noqa — `# noqa` suppressions must specify error code

**What it catches**: `# noqa` without an error code suppresses ALL ruff warnings on a line. This creates a permanent
blind spot: future ruff rules that fire on the same line are silently suppressed. Current workspace has 1,376 `# noqa`
suppressions; unknown fraction are bare (without code).

**Scope**: All service repos (`SOURCE_DIR/`), excluding `scripts/` subdirectories.

**Ratchet plan**: WARN immediately, ERROR after 2026-06-01 (one sprint to clean up).

**Compliant pattern**:

```python
from some_module import thing  # noqa: E402  — module-level import at top (intentional)
```

**Non-compliant pattern**:

```python
from some_module import thing  # noqa  — ❌ bare noqa, suppresses everything
```

**How to comply**: `rg "# noqa$" --type py SOURCE_DIR/` to find bare noqa; add specific error code or remove.

**Estimated remediation**: ~2 AI-hours per repo for top 5 offenders (mtds: 297, unified-trading-api: 206,
execution-service: 188, UTL: 163, strategy-service: 154). Total workspace effort: ~5 AI-days.

**Composes with**: STEP 2/6 LINT (ruff); deprecated-pattern sweep issue doc `deprecated_pattern_sweep_2026_05_15.md`.

---

### STEP 5.84: no-bare-exit — `sys.exit(1)` must be preceded by `log_event FAILED`

**What it catches**: Services that exit with error code without emitting the required FAILED lifecycle event. This
breaks STARTED/STOPPED/FAILED monitoring — the VM zombie watchdog sees the process die but no FAILED event was emitted,
so alerting doesn't fire and the orchestrator cannot classify the failure.

**Scope**: All service source (`SOURCE_DIR/`), excluding `tests/`, `scripts/`, and `cli/` exit-on-help patterns.

**Ratchet plan**: WARN immediately (current workspace has ~127 violations), ERROR after 2026-06-15.

**Compliant pattern**:

```python
from unified_trading_library.events import log_event
log_event(service_name, "FAILED", error=str(e), stack_trace=traceback.format_exc())
sys.exit(1)
```

**Non-compliant pattern**:

```python
sys.exit(1)  # ❌ — no FAILED event emitted before exit
```

**How to comply**: Search `rg "sys\.exit\([^0]" --type py SOURCE_DIR/`; each bare exit should have a preceding
`log_event(..., "FAILED")` call in the same except/error branch.

**False-positive exclusion**: CLI `--help` exit paths, `argparse` `sys.exit(0)`, and script-mode `main()` returns that
feed into `sys.exit(run(...))` are excluded (STEP applies to service logic paths only).

**Composes with**: STEP 6/6 PRODUCTION READINESS (ServiceBootstrap lifecycle); exit-code audit findings.

---

### STEP 5.85: no-print-in-source — `print()` calls banned in service source code

**What it catches**: `print()` statements in service source code (not tests, not scripts, not CLI) emit to stdout,
bypassing the structured `log_event` system. These show up in container logs untagged, making correlation impossible and
breaking the observability contract.

**Scope**: `SOURCE_DIR/` only (not `tests/`, `scripts/`, `e2e-testing/`).

**Ratchet plan**: ERROR immediately — no grace period. Current violation count is low (< 20 across workspace).

**Compliant pattern**:

```python
import logging
logger = logging.getLogger(__name__)
logger.info("Processing %s records", count)
```

**Non-compliant pattern**:

```python
print(f"Processing {count} records")  # ❌ — use logger.info
```

**Exception**: `if __name__ == "__main__"` blocks in CLI scripts may use `print()` for human-readable output (e.g.
`print(json.dumps(result, indent=2))`).

**How to comply**: `rg "^\s+print\(" --type py SOURCE_DIR/` — fix by replacing with `logger.info/warning/error`.

**Composes with**: STEP 6/6 event logging; `no-setup-cloud-logging` rule (use UTL setup_events instead).

---

**Activation sequence (proposed)**:

1. Operator approves individual STEPs via ping ack
2. Each approved STEP added to `base-service.sh` as WARN with ratchet date
3. Rollout via `rollout-quality-gates-unified.py` to all 15 service repos
4. STEP transitions to ERROR on ratchet date after teams have remediated

---

## QG-sweep batching + shared-host concurrency (codified 2026-06-02)

`quality-gates.sh` is expensive (~100–500s/run; worse under host contention). When shipping MANY related code items —
especially across multiple repos and/or via parallel code-only sub-agents — do **not** run a full QG before every small
edit. Batch the GATE, not the commits.

### The technique (batch the gate, keep per-unit commits)

1. **Make ALL the code edits for the batch first.** Code-only sub-agents are told to edit + verify with `basedpyright`
   on the touched files only (fast, no fan-out) and report diffs — **NOT** run full `quality-gates.sh`, **NOT** commit.
   This parallelizes safely (basedpyright is light; it does not spawn the pytest-xdist worker fan-out that saturates
   RAM).
2. **Run `quality-gates.sh` ONCE per repo over the whole batch.** One green sweep validates every edit in that repo at
   once, instead of N sequential full gates.
3. **THEN make per-shippable-unit commits + plan-flips from that green tree.** Commit + Push + Flip stays fully intact —
   the COMMITS are still one-per-item (each with its own `docs(plans):` flip), only the GATE RUNS are batched. A single
   green sentinel covers the tree; you cut N commits from it.

This preserves the merge-prerequisite contract (the touched code IS gated green before it lands) and the
false-progress-prevention of per-item flips, while removing the repeated multi-minute QG cost.

### Shared-host QG concurrency (HARD)

The dev host is **shared across every slot** (slot 1 in `.tabs/1`, slot 2 in `.tabs/2`, … are separate process trees on
the SAME machine). Two consequences:

- **Run ≤2 full QGs at once** (raised from 1 → 2, operator 2026-06-05 — see the governor floor change below).
  `quality-gates.sh`'s own "keep parallel QGs to 2 slots max" warning is **host-wide, not per-slot**. Exceeding it (e.g.
  2 background QG agents + your own runs → ~30 concurrent pytest/basedpyright procs) makes the gates OOM-kill each other
  — symptom: exit **144** mid-`TESTS`, no `ALL QUALITY GATES PASSED`, no sentinel. Full QGs serialize; code-only
  `basedpyright`-only agents parallelize.
- **Never bulk-kill `pytest` / `quality-gates.sh` / `basedpyright` processes** (by pattern, or by PPID=1 "orphan"
  sweep). They may belong to **another slot's** session — killing them is the process-space form of "don't touch outside
  your clear context" (incident 2026-06-02: a PPID/pattern reap killed slot-1's pytest under a `claude` process in
  `.tabs/1`). To stop only YOUR background work, `TaskStop` your tracked task-ids — never a blanket `pkill`.

### Sanctioned timeout overrides (host contention only)

When a QG fails ONLY on a timing META-gate — all substantive gates green — these are the sanctioned overrides:

- `IGNORE_TIMEOUT=true bash scripts/quality-gates.sh` — skips the `<MAX_DURATION>s` (default 300) wall-clock gate.
  `MAX_DURATION` is also env-overridable (docs note "set to 600 for PM/codex").
- `PYRIGHT_TIMEOUT=<n>` — raises basedpyright's inner `run_timeout` (default 120s) when type-check is slow under load.

These are legitimate because the timing gate is a performance budget, not a quality check — on a quiet host the same QG
completes well under it (e.g. an MTDS run that took 425s under contention runs ~99s solo). The gate still runs every
substantive STEP and writes the sentinel on a true pass. Do NOT use them to mask an actual gate failure.

## Resource governance under multi-slot load (codified 2026-06-02)

> Plan: `plans/active/quality_gates_resource_contention_speedup_2026_06_02.md`. The shared-host concurrency rule above
> is the **manual** discipline ("humans/agents keep full QGs to 1–2"); the mechanisms below **automate** it inside
> `quality-gates-base/base-service.sh` so it holds even when N slots gate unattended.

**The anti-pattern (measured, not theoretical):** `pytest -n auto` per slot, or **uncapped native BLAS/OMP thread
pools** per slot, on a shared host is **oversubscription, not speedup**. Measured 2026-06-02 on the 24-core dev box:
ml-service's gate spawned **100+ threads / ~13 effective cores** from numpy/sklearn/lightgbm/xgboost (the `pytest -n`
default was already `1` — the fan-out was native thread pools, NOT xdist). When several slots do this at once the box
swaps and every run slows. Adding parallelism makes the aggregate worse.

### The four levers (all in `base-service.sh`, sourced live by every repo's `quality-gates.sh`)

1. **Host concurrency governor — `quality-gates-base/qg-host-governor.sh`.** A `flock` token bucket of **K** tokens (K =
   `max(2, floor(physical_cores/4))`, override `QG_HOST_CONCURRENCY`; the **floor was raised 1 → 2 on 2026-06-05** so a
   shared host always permits 2 concurrent full QGs — on the macOS operator host `lscpu`+`nproc` are both absent → cores
   degrades to 4 → `floor(4/4)=1`, and the min-2 floor lifts it to exactly 2). `qg_governor_acquire` is called before
   the heavy phases (`[3] TESTS`) and `qg_governor_release` after `[4] TYPE CHECK`; at most K QG heavy-phases run
   concurrently **across all slots**, the rest queue. The held process is `nice -n10` + `ionice -c2 -n7` so it never
   starves interactive work. `flock` auto-frees on process death (no stuck tokens). No-op when
   `QG_GOVERNOR_DISABLE=true` or `flock(1)` is absent. Introspect: `bash qg-host-governor.sh --status`. This converts
   N-way thrash into orderly queueing → aggregate p95 drops with **no added parallelism**.
2. **Thread-pool caps.** `base-service.sh` exports `OMP_NUM_THREADS` / `OPENBLAS_NUM_THREADS` / `MKL_NUM_THREADS` /
   `NUMEXPR_NUM_THREADS` = `${QG_THREAD_CAP:-2}` — caps the native fan-out above. Capping `pytest -n` alone is
   insufficient when the parallelism is BLAS/OMP, not xdist. Per-repo override: `export QG_THREAD_CAP=N` before
   `source base-service.sh`.
3. **Coverage off the hot path.** `--cov` (per-line instrumentation) is a large CPU/RAM cost. Iterative/`--quick` runs
   skip it; the coverage floor is still **enforced on the full gate run** (quickmerge Pass 1). The merge-gate coverage
   requirement is unchanged — only _when_ it is paid.
4. **Shared caches.** `RUFF_CACHE_DIR` (and the basedpyright cache, already keyed per-service in `$TMPDIR`) are
   repointed to host-shared dirs so the first slot to run warms them for all — the default in-worktree
   `.ruff_cache`/`.pytest_cache` defeats cross-slot reuse.

### Per-repo resource baseline + 2× drift guard

`scripts/dev/measure-qg-baseline.sh --env local|vm [--jobs N]` records per-repo wall/RSS/CPU to
`scripts/dev/qg_resource_baseline.json` (keyed repo × {local,vm}; RSS + CPU are parallelism-invariant so `--jobs>1`
stays accurate, only wall can inflate — validated on this box at j=4 with <3% deviation). `base-service.sh` then WARNs
(never fails) when a run's wall-clock exceeds **2× its committed baseline** — an early resource-regression signal during
code-freeze. Aggregate cross-slot contention is measured separately by `scripts/dev/benchmark-qg-under-load.sh`.

### VM-sizing (data-driven, not a guess)

The binding constraint is **peak RSS**, not cores. Measured ceiling (local, full gates): **unified-trading-library 5.27
GB**, then execution/features ~1.9 GB — so a _single_ heavy gate overshoots the current `m7i.xlarge` 2 GB/slot budget by
up to 2.6×. **Decision (operator 2026-06-02): keep QG LOCAL on 16 GB workers, no fleet change** — the governor caps
K=`max(2, floor(vCPU/4))`=2 on a 4-vCPU worker (floor raised 1 → 2, operator 2026-06-05) so two concurrent peaks (~10.6
GB) still fit 16 GB; sizing rule `per-VM RAM ≥ peak-per-run-RSS × K`. Central self-hosted-runner QG (Option B) was
**rejected** — it breaks the local pass/fail feedback loop. ADR: `adr-qg-offload-self-hosted-runners-2026-06-02.md`.

### Both base files are governed

The governance (governor + thread caps + ruff cache + green sentinel + coverage-off-hot-path) is wired into **both**
`base-service.sh` (17 service repos) **and** `base-library.sh` (UAC + unified-trading-library — the 5.27 GB ceiling, so
it matters most there). `base-ui.sh` (TS repos) is out of scope (no pytest fan-out).

### Do-less-work levers — decisions (2026-06-02)

- **Green sentinel (`qg-repo-green-sentinel`) — SHIPPED, default ON.** Skips TESTS + TYPE CHECK when the working tree is
  **byte-identical** (conservative content hash: HEAD + working diff + untracked-minus-artifacts + gate scripts + tool
  versions) to the last FULL green run; light codex/production checks still run. **Safe by construction:** no sentinel /
  malformed hash / any content change → normal full run; only an exact 64-char match skips. `.qg_content_sentinel` is
  separate from quickmerge's `.qg_last_passed_sha`. Escape: `QG_SENTINEL_DISABLE=true`.
- **Selective testing (`qg-selective-tests`) — AUDITED, NOT enabled (operator 2026-06-02).** Evaluated `pytest-testmon`
  / import-graph changed-files→affected-tests mapping. **Decision: keep running the FULL test suite** — not ready to
  bypass any test; a missed-test false-negative is strictly worse than slowness, and the green sentinel + governor
  already remove most of the cost without ever skipping a test on changed content. Revisit only behind
  `QG_SELECTIVE=true` default-off once proven sound.
- **basedpyright scope (`qg-basedpyright-scope`) — AUDITED, no scoping (data-driven).** Measured basedpyright at **~5.4
  s / 9.6 CPU-s** (NOT the "biggest CPU spike" the original plan assumed) — scoping to changed packages saves ~nothing
  while risking missed cross-file type errors. **Keep full-tree analysis.** Cache already shared
  (`$TMPDIR/basedpyright-cache/$SERVICE_NAME`). The real basedpyright lever is _strictness_ (warn-only by default unless
  `BASEDPYRIGHT_MAX_ERRORS` is set) — a separate policy decision, not a speed one.
