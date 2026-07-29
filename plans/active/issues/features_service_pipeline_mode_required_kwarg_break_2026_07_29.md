---
doc_type: issue
title:
  "unified-api-contracts@fa25a345 made pipeline_mode a REQUIRED kwarg on build_cefi_partition_path/
  build_tradfi_partition_path — breaks features-service calendar (FRED/tradfi) + volatility (CeFi) call sites, 12 tests
  RED on live-defi-rollout"
summary: >-
  While shipping an unrelated onchain/lst_yields backfill script, `bash scripts/quality-gates.sh --no-fix` on
  features-service (editable-path dep on unified-api-contracts, so it reads UAC HEAD directly) surfaced 12 pre-existing
  test failures across two unrelated feature families — confirmed NOT caused by the onchain change (verified by direct
  re-run of the failing tests in isolation; the onchain script is a new untracked .sh file with zero Python-import
  surface). Root cause: `unified-api-contracts@fa25a345` ("fix: add required pipeline_mode param to
  build_cefi_partition_path/build_tradfi_partition_path") flipped `pipeline_mode` from optional (`pipeline_mode: str |
  None = None`, back-compat default) to a required keyword-only argument, per the module docstring's own note:
  "pipeline_mode is likewise REQUIRED as of 2026-07-29 — the old back-compat ... now fails loudly (TypeError) at the
  call site instead". Two features-service call sites were never updated for the new signature and now fail loudly
  exactly as designed: `features_service/calendar/adapters/mtds_fred_reader.py:120` (calls `build_tradfi_partition_path`
  with no `pipeline_mode`) and `features_service/volatility/engine/orchestrator.py:314` (calls
  `build_cefi_partition_path` with no `pipeline_mode`). This blocks `quickmerge --agent` for EVERY features-service
  commit right now (the `.qg_last_passed_sha` sentinel never gets written on a red full-suite run), not just onchain
  work — filed as a repo-blocker per `unified-trading-pm/agents/RULES.md` § 4b.
status: resolved
nature: issue
asset_group: [defi, tradfi, cefi]
stage: [data]
repos: [features-service, unified-api-contracts]
scope: [engineer, admin]
tags:
  [features-service, unified-api-contracts, pipeline_mode, breaking-change, qg-red, repo-blocker, calendar, volatility]
related:
  [
    /plans/active/issues/defi_lst_yields_coverage_extension_gcs_verified_2026_07_28.md,
    /codex/02-data/pipeline-mode-partition.md,
  ]
created: 2026-07-29
parent_epic: infrastructure_master
source:
  [data_engineering slot-7, 2026-07-29, discovered while shipping defi_lst_yields_coverage_extension_gcs_verified-001]
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: brand-new
estimate_baseline_ai_days: 0.15
estimate_calibrated_ai_days: 0.15
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-29
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by: features-service@d7da0ec7
---

# `pipeline_mode` required-kwarg break in features-service — found while shipping an unrelated onchain change

## What I found

`bash scripts/quality-gates.sh --no-fix` on `features-service` (`live-defi-rollout` HEAD, editable path dep on
`unified-api-contracts`) fails 12 tests, all tracing to the same root cause:

```
ValueError: pipeline_mode must be a non-empty string
```

or

```
ERROR ... build_cefi_partition_path() missing 1 required keyword-only argument: 'pipeline_mode'
```

**Verified pre-existing / not caused by my change**: my in-flight work was a brand-new untracked `.sh` script
(`scripts/lst_yields_full_backfill_supervisor.sh`, onchain feature family) with zero Python import surface — it cannot
affect test collection or execution for `calendar`/`volatility` tests. Re-ran the failing tests directly in isolation
and confirmed the same failures with no relation to the onchain change.

**Root cause**: `unified-api-contracts@fa25a345` ("fix: add required pipeline_mode param to
build_cefi_partition_path/build_tradfi_partition_path") changed `pipeline_mode` from optional
(`pipeline_mode: str | None = None`) to a required keyword-only parameter on both functions. The module's own updated
docstring (`unified_api_contracts/canonical/partition_paths.py`) states this explicitly: "TradFi: ... pipeline_mode is
likewise REQUIRED as of 2026-07-29 — the old back-compat default is retired; a caller omitting pipeline_mode now fails
loudly (TypeError) at the call site instead [of silently omitting the segment]." This is a deliberate, documented
breaking change — but two features-service call sites were not migrated:

1. `features_service/calendar/adapters/mtds_fred_reader.py:120` — `build_tradfi_partition_path(...)` called with no
   `pipeline_mode` kwarg. Breaks all 8 tests in `tests/calendar/unit/test_mtds_fred_reader.py`.
2. `features_service/volatility/engine/orchestrator.py:314` — `build_cefi_partition_path(...)` called with no
   `pipeline_mode` kwarg. Breaks all 4 tests in `tests/volatility/unit/test_orchestrator_gcs.py::TestListChainFiles`.

## Why it matters

- Blocks `quickmerge --agent` for EVERY features-service commit (the full-suite `quality-gates.sh` sentinel never writes
  green), not just onchain/lst_yields work — any worker touching ANY features-service file right now hits this.
- `mtds_fred_reader.py` is the TradFi FRED-series reader (macro/calendar features); `volatility/engine/orchestrator.py`
  is the CeFi volatility feature orchestrator's GCS chain-file lister — both are live production read paths, not just
  test fixtures, so the underlying reads are ALSO broken at runtime for both asset groups, not merely in CI.

## Recommended fix (NOT done in this doc — deliberate craft-scope boundary, see below)

Both call sites need a `pipeline_mode=` argument threading from their caller context (the correct value depends on which
pipeline_mode partition the reader is actually targeting — `pipeline_mode-partition.md` SSOT governs the
`{mode}_{source}[_{transport}]` scheme). This is a judgment call about WHICH pipeline_mode each reader should target
(likely `batch` for both, but needs confirmation against how the corresponding WRITER path actually partitions TradFi
FRED data and CeFi volatility source data — not asserted here), not a mechanical fix — hence routed to
`backend_engineer` rather than fixed inline by this `data_engineering`-scoped session (craft-scope boundary: this
session's task is onchain DeFi LST backfill, not calendar/volatility TradFi/CeFi code).

## Todos

- [x] [BACKEND] P1. Fix `features_service/calendar/adapters/mtds_fred_reader.py:120` — thread the correct
      `pipeline_mode` value into the `build_tradfi_partition_path(...)` call (confirm against the FRED writer's actual
      partition scheme; likely `batch`, but verify — don't guess). Repo: features-service. **Done when**: all 8 tests in
      `tests/calendar/unit/test_mtds_fred_reader.py` pass. — ✅ features-service@d7da0ec7. Confirmed (not guessed): FRED
      has no `_VENUE_OVERRIDES` entry in UTL's `pipeline_mode_resolver.py` and no `("tradfi","yield_curve"/"ohlcv_1d")`
      `SOURCE_PRIORITY` entry, so `derive_pipeline_mode_for_row` resolves it to `BATCH_DATABENTO` (`batch_databento`),
      NOT a literal `"batch"`/`"batch_fred"` — verified empirically by calling the resolver directly. This confirms
      hardcoding a pipeline_mode value would have been WRONG; the reader's own mode-agnostic bare-prefix design (list
      once, filter by accepted `batch_*`/`live_*` family) was already correct and just needed the bare prefix restored
      via a probe-and-strip (pipeline_mode is now a required kwarg on `build_tradfi_partition_path`, so `None` no longer
      produces it directly). All 13 tests in `tests/calendar/unit/test_mtds_fred_reader.py` pass (8 required + 5 more).
- [x] [BACKEND] P1. Fix `features_service/volatility/engine/orchestrator.py:314` — thread the correct `pipeline_mode`
      value into the `build_cefi_partition_path(...)` call (confirm against the CeFi volatility writer's actual
      partition scheme). Repo: features-service. **Done when**: all 4 tests in
      `tests/volatility/unit/test_orchestrator_gcs.py::TestListChainFiles` pass and full `bash scripts/quality-gates.sh`
      is green on features-service. — ✅ features-service@d7da0ec7. Same probe-and-strip fix mirroring the FRED reader
      (the surrounding code already threads the real per-row `derive_pipeline_mode_for_row(...)` value into the
      canonical path when known; only the bare-path derivation at line 314 needed the required-kwarg fix). All 4 tests
      in `TestListChainFiles` pass; full `bash scripts/quality-gates.sh` on features-service is green (17976 passed, 209
      skipped, 0 failed). Also found + fixed an unrelated pre-existing regression blocking the same full-suite gate
      (accidentally-deleted `calendar_features` PATH_REGISTRY row) —
      `/plans/archive/issues/utl_path_registry_calendar_features_accidental_deletion_2026_07_29.md` (resolved,
      unified-trading-library@52161ee7).

## Evidence

- `bash scripts/quality-gates.sh --no-fix` on features-service `live-defi-rollout` HEAD:
  `12 failed, 17963 passed, 209 skipped` (2026-07-29).
- `unified-api-contracts` commit `fa25a345` ("fix: add required pipeline_mode param to
  build_cefi_partition_path/build_tradfi_partition_path") + updated docstring in
  `unified_api_contracts/canonical/partition_paths.py` confirming this is an intentional, documented 2026-07-29 breaking
  change.
- Direct isolated re-run of
  `tests/calendar/unit/test_mtds_fred_reader.py::test_reader_returns_empty_when_nothing_captured` and
  `tests/volatility/unit/test_orchestrator_gcs.py::TestListChainFiles::test_filters_by_venue` reproduces both failure
  signatures with tracebacks pointing directly at the two call sites above.
