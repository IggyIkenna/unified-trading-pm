---
doc_type: issue
title: Bare `read_availability_index()` callers reachable on the 1.58 GB defi index — OOM-risk audit
summary: >-
  Systematic audit of every `read_availability_index()` call site across the workspace for callers that are reachable
  with a defi-asset-group bucket AND call the reader WITHOUT a `columns=`/`filters=` projection kwarg. The defi prod
  consolidated availability index is 1.58 GB on disk (likely several GB once decoded into a pandas DataFrame); any such
  bare caller is one cache-miss/cold-start away from an OOM on a memory-constrained Cloud Run job or VM. ~35-40
  bare+defi-reachable call sites found across 8 repos; no QG gate currently enforces the projection pattern (prose-only
  convention in codex/02-data docs).
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos:
  [
    unified-trading-library,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    ml-service,
    strategy-service,
    deployment-api,
    deployment-service,
    instruments-service,
    batch-live-reconciliation-service,
    e2e-testing,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags: [data-pipeline, manifest, oom, defi, performance, audit, read-availability-index]
related:
  [
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
    /plans/active/issues/manifest_completeness_full_corpus_map_build_2026_07_20.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-07-27
parent_epic: infrastructure_master
priority: P1
source:
  [
    "data_pipeline_check_mdps_features_2026_07_20.md todo (line ~577), dispatched task
    data_pipeline_check_mdps_features-020, slot-7 2026-07-27",
  ]
assigned_vm: planning
execution_scope: orchestrator-agent
priority_class: infra
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
assigned_role: infra
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
locked_since:
---

# Bare `read_availability_index()` callers reachable on the 1.58 GB defi index

## What I found

The parent plan (`data_pipeline_check_mdps_features_2026_07_20.md`) flagged: "the defi-prd availability index is 1.58
GB. Any `read_availability_index` caller on defi without a column/filter projection is one cache-miss from an OOM." — a
SECOND, standalone P0 independent of the F1/F2/F3 read-path amplification fix (already closed, see
`manifest_completeness_full_corpus_map_build_2026_07_20.md`). This doc is the full-corpus audit that todo asked for.

**Method**: grepped every `read_availability_index(` call site across all repos (excluding tests), classified each by
(a) whether it passes a projection kwarg at the call site and (b) whether it is reachable with a defi-asset-group bucket
(generic/shared service+library code that runs across all asset groups IS defi-reachable; scripts hardcoded to a
non-defi bucket constant, e.g. sports/cefi/tradfi/prediction-only migration scripts, are NOT and are excluded).

**Confirmed UTL signature** (`unified_trading_library/manifest_writer/_read_index.py:314`):
`read_availability_index(bucket, columns=None, filters=None)` — no `date_window` kwarg on the real function (a
`date_window` kwarg exists only on deployment-api's own wrapper `manifest_source.read_manifest_index`, sometimes
imported under the alias `read_availability_index` — see the deployment-api section below).

### Bare + defi-reachable call sites, by repo

**unified-trading-library** (used everywhere — highest blast radius):

- `feature_service_base/manifest_discovery.py:59,99,224,274` — 4 sites (`read_manifest_rows`,
  `get_captured_instruments`, `check_dependency_via_manifest`, `resolve_spot_perp_from_manifest`); shared by
  delta_one/volatility/onchain/cross_instrument. onchain's `dependency_checker.py:214` calls `read_manifest_rows` from a
  function whose docstring says explicitly "For DEFI".
- `manifest_writer/_queries.py:54,115,297,388`, `_maintenance.py:72,158,405,530`, `_writer_io.py:156` — internal
  ManifestWriter machinery, generic across all buckets.
- `manifest_completeness.py:375`, `dependency_check.py:143`, `instruments_preflight/runner.py:118`,
  `pipeline_e2e_check/shard_verify.py:154`, `pipeline_e2e_check/prod_precheck.py:58` — generic bucket-param helpers.
- `manifest_freshness.py:362` — own comment at line 353 already warns "full-schema read_availability_index() costs up to
  ~6.5 GB peak"; call shape not fully confirmed projected — needs a direct look.

**market-tick-data-service**:

- `reader.py:839` (`_resolve_pipeline_mode_from_manifest`) — invoked on every `read_shard()` across all consumers.
  **VERIFIED by direct read (not just the audit agent's report)**: downstream code reads
  `{"venue","data_type","instrument_type","date","capture_status"}` (line 846) PLUS a conditional
  `"pipeline_mode" in manifest.columns` / `manifest.loc[mask, "pipeline_mode"]` read at line 861-864 for the CF-3
  pipeline_mode-lift fallback — **`pipeline_mode` MUST be included in any projected columns list here**, or the lift
  silently stops firing (no crash, no error — a silent behavior regression). Correct fix:
  `columns=["venue","data_type","instrument_type","date","capture_status","pipeline_mode"]`.
- `engine/orchestrator/__init__.py:509` (`_run_preflight_availability_check`) — every MTDS backfill VM's date-loop
  start; same incident class as `mtds_backfill_vm_startup_oom_rc137_2026_07_14`.
- `scripts/pipeline_e2e_check.py:1998` — bare fallback branch (medium confidence, not primary path).

**ml-service** (live/hot path):

- `inference/app/core/manifest_inference_guard.py:46` (`check_manifest_for_inference`) — per LIVE INFERENCE request;
  docstring explicit `asset_group: cefi/defi/tradfi/sports/prediction`.
- `training/app/core/manifest_gap_handler.py:54` (`apply_manifest_quality_flags`) — same defi-explicit docstring.

**deployment-api** (user-facing dashboard — single highest-blast-radius chokepoint):

- `services/manifest_source.py:164` — bare fallback inside `read_manifest_index()`, executed whenever
  `date_window is None` OR the pushdown branch returns empty/raises. This function is re-exported/aliased as the
  effective `read_availability_index` for ~10 other deployment-api modules (`data_status_service.py:449`,
  `services/data_status/instrument_coverage.py:191`, `shard_detail/_venue_detail.py:354`,
  `data_status_drilldown/_csv_export.py:477`, `data_query_service.py:747`, `shard_detail/_shard_core.py:525`,
  `data_status_drilldown/_core.py:171,388`) — fixing the ONE fallback branch here fixes all of these transitively.
  `DRILLDOWN_COLUMNS` is already defined in this same file (line 74) and already used on the pushdown branch — the fix
  is to reuse it on the fallback branch too, not invent a new projection.
- `routes/data_status/_catalogue.py:186` — imports the RAW UTL function directly (bypasses the wrapper), bare.
- `routes/data_status/_live_coverage.py:457` — lazily imports raw UTL `read_availability_index`, bare, `asset_group` is
  a generic parameter.
- Already safe (verified, NOT findings): `_axis_census.py:225`, `health_consolidator.py:752`,
  `census_manifest_data_type_2026_07_24.py:65` — all already pass `columns=`.

**features-service**:

- `common/__init__.py:99` (`resolve_latest_captured_date`), `common/manifest_window_guard.py:115`,
  `common/manifest_leg_guard.py:98` — all explicitly documented `asset_group: cefi/defi/tradfi/sports/prediction`.
- `volatility/engine/orchestrator.py:276`, `volatility/core/orchestration_service.py:168`,
  `volatility/core/data_loader.py:364`, `delta_one/app/core/dependency_checker.py:619` — generic per-family engine code,
  defi-adjacent.
- Smoke scripts (medium confidence, CI-runner OOM risk not prod): `scripts/cross_instrument/smoke_matrix.py:133`,
  `scripts/multi_timeframe/smoke_matrix.py:132`, `scripts/volatility/smoke_matrix.py:134`,
  `scripts/onchain/smoke_matrix.py:158`, `scripts/delta_one/smoke_matrix.py:142`.

**instruments-service**:

- `engine/orchestrator/venue_core.py:222` (`_get_manifest_high_watermarks`) — VERIFIED via `defi.py:229,246`
  (`_get_defi_manifest_high_watermarks() → _get_manifest_high_watermarks("DEFI")`) and unit test
  `test_orchestrator_gaps.py:216,238` confirming `asset_group="DEFI"` reaches this exact path.
- `engine/orchestrator/process_completeness.py:468` (`_detect_thin_day_venues`) — medium confidence; bare read always
  happens regardless of which bucket is passed, even though it then filters internally.
- `cli/main.py:78,150` — generic CLI entry points; defi-reachable via `--asset-group defi`. Medium confidence.

**strategy-service**:

- `manifest_allocation_guard.py:170` (`check_allocation_manifest`) — docstring explicit
  `cefi/defi/tradfi/sports/prediction`.

**batch-live-reconciliation-service**:

- `stages/stage0_manifest_reason_check.py:177` — module docstring: "the bucket is already scoped to one asset_group"
  (generic, batch-vs-live comparison per asset_group).

**deployment-service** (CLI):

- `cli/utils/manifest_reader.py:245,585,674` (`get_completion(service, asset_group, ...)` and similar) — `asset_group`
  generic parameter. Medium-high confidence, operator-invoked (`--asset-group defi`).

**e2e-testing** (medium confidence, not deep-read): `scripts/build_smoke/live_manifest_reader.py:98`,
`scripts/strategy/backtest_from_wizard_config.py:192`.

**unified-trading-pm** (audit/QG tooling, not production, low urgency):
`plans/audit/results/ available_at_fill_rate_audit_2026_07_13.py:51`, `scripts/qg/honest_coverage_ratchet.py:66`.

### No enforcing QG gate exists

Checked `unified-trading-pm/scripts/quality_gates/` in full — only
`check_manifest_writer_missing_write_before_return.py` and `check_no_category_kwarg_at_manifest_write.py` exist, both
about the WRITER side, not reader-projection. The projection pattern is documented as prose-only guidance in several
`codex/02-data/` docs ( `reconciliation-census-and-compute-tiers.md:120,323`, `shard-coverage-classification.md:159`,
`honest-coverage-model.md:149`, `chart-candle-delivery-flow.md:255`) but never codified into an automated check.

## Why it matters

The defi prod availability index (1.58 GB on disk) is the largest of any asset group's consolidated index. Any of the
~35-40 bare call sites above, when invoked in a defi context (live inference request, dashboard data-status query, MTDS
backfill VM startup, MDPS preflight check), decodes the WHOLE index into a pandas DataFrame — a real OOM risk on
memory-constrained Cloud Run jobs / VMs, matching the ALREADY-DOCUMENTED incident class
`mtds_backfill_vm_startup_oom_rc137_2026_07_14`. deployment-api's `manifest_source.py:164` fallback is the single
highest-blast-radius chokepoint (feeds ~10 dashboard endpoints).

**IMPORTANT CAVEAT for whoever picks up a fix todo below**: do NOT blindly copy a proposed `columns=[...]` list without
independently reading the function's own downstream column usage first — the audit that produced this doc initially
proposed a columns list for `reader.py:839` that OMITTED `pipeline_mode`, which IS read downstream for the CF-3 fallback
lift (silent behavior regression, not a crash). Each fix below needs the SAME direct-read verification before shipping,
not a mechanical column-list copy.

## Recommended decision

- [ ] [SCRIPT] P0. **market-tick-data-service** — `reader.py:839` `_resolve_pipeline_mode_from_manifest`: project
      `read_availability_index(bucket, columns=["venue","data_type","instrument_type","date","capture_status","pipeline_mode"])`
      (verified column set — includes `pipeline_mode` for the CF-3 lift). Add/extend a regression test asserting the
      CF-3 lift still fires with a projected manifest frame.
- [ ] [SCRIPT] P0. **market-tick-data-service** — `engine/orchestrator/__init__.py:509`
      `_run_preflight_availability_check`: project to the columns actually read in the function body
      (`date`/`capture_status`/`instrument_count`/`error_reason` for the skip-mask,
      `venue`/`data_type`/`instrument_id`/`underlying`/`quote_asset`/`margin_type` in the per-row atom loop) — re-verify
      by direct read before shipping, same incident class as `mtds_backfill_vm_startup_oom_rc137_2026_07_14`.
- [x] ✅ [SCRIPT] P0. **ml-service** — `inference/app/core/manifest_inference_guard.py:46`
      `check_manifest_for_inference` — **SHIPPED 2026-07-27 (slot-10)**, `ml-service@0bd5e6a`. Confirmed by direct read
      (not the guessed default): `_filter_to_day` reads `date`/`asset_group`; `_classify_day_rows` reads
      `capture_status` — no other columns touched anywhere in the module. Projected
      `columns=["date","asset_group","capture_status"]` exactly. Added a regression test
      (`test_read_availability_index_is_column_projected`) pinning the exact call signature so a future edit to either
      function is forced to also update the projection. Full test file green (12 tests) + `quality-gates.sh` green
      (302s).
- [ ] [SCRIPT] P1. **ml-service** — `training/app/core/manifest_gap_handler.py:54` `apply_manifest_quality_flags`: same
      treatment as the inference guard above.
- [ ] [SCRIPT] P0. **deployment-api** — `services/manifest_source.py:164`: reuse the already-defined `DRILLDOWN_COLUMNS`
      (line 74, already used on the pushdown branch) on the bare fallback branch too. Single highest-blast-radius fix
      (feeds ~10 downstream dashboard endpoints transitively).
- [ ] [SCRIPT] P1. **deployment-api** — `routes/data_status/_catalogue.py:186` +
      `routes/data_status/_live_coverage.py:457`: project both raw-UTL-import call sites; read each caller's actual
      downstream column usage first.
- [ ] [SCRIPT] P1. **unified-trading-library** — `feature_service_base/manifest_discovery.py:59,99,224,274` (4 call
      sites, shared by delta_one/volatility/onchain/cross_instrument — onchain is defi-adjacent): project each to its
      own actual column usage (read each of the 4 functions individually — they differ; do not assume one column list
      fits all 4).
- [ ] [SCRIPT] P1. **unified-trading-library** — `manifest_freshness.py:362`: the module's own comment already flags the
      ~6.5 GB peak risk; confirm current call shape by direct read and project if still bare.
- [ ] [SCRIPT] P2. **unified-trading-library** — `manifest_writer/_queries.py` (4 sites) + `_maintenance.py` (4 sites) +
      `_writer_io.py:156`: internal ManifestWriter query/maintenance helpers; lower urgency (less frequently invoked
      than the hot-path findings above) but same fix pattern.
- [ ] [SCRIPT] P1. **features-service** — `common/__init__.py:99`, `common/manifest_window_guard.py:115`,
      `common/manifest_leg_guard.py:98`: project each to its actual column usage (shared across ALL feature families
      including onchain/defi).
- [ ] [SCRIPT] P2. **features-service** — `volatility/engine/orchestrator.py:276`,
      `volatility/core/orchestration_service.py:168`, `volatility/core/data_loader.py:364`,
      `delta_one/app/core/dependency_checker.py:619`: project each to its actual column usage.
- [ ] [SCRIPT] P1. **strategy-service** — `manifest_allocation_guard.py:170` `check_allocation_manifest`: project to its
      actual column usage.
- [ ] [SCRIPT] P1. **instruments-service** — `engine/orchestrator/venue_core.py:222` `_get_manifest_high_watermarks`:
      project to its actual column usage (confirmed defi-reachable via `defi.py:229,246` +
      `test_orchestrator_gaps.py:216,238`).
- [ ] [SCRIPT] P2. **instruments-service** — `engine/orchestrator/process_completeness.py:468`
      `_detect_thin_day_venues`: project to its actual column usage.
- [ ] [SCRIPT] P2. **batch-live-reconciliation-service** — `stages/stage0_manifest_reason_check.py:177`: project to its
      actual column usage.
- [ ] [SCRIPT] P2. **deployment-service** — `cli/utils/manifest_reader.py:245,585,674`: project each to its actual
      column usage (operator-invoked CLI, lower urgency than the live/hot-path findings above).
- [ ] [SCRIPT] P3. **features-service** smoke scripts (cross_instrument/multi_timeframe/volatility/onchain/delta_one
      `smoke_matrix.py`), **e2e-testing** (`build_smoke/live_manifest_reader.py:98`,
      `strategy/backtest_from_wizard_config.py:192`), **unified-trading-pm**
      (`plans/audit/results/     available_at_fill_rate_audit_2026_07_13.py:51`,
      `scripts/qg/honest_coverage_ratchet.py:66`): lower-urgency CI/audit-tooling call sites; project if convenient when
      touching these files for other reasons, not worth a dedicated dispatch on their own.
- [ ] [SCRIPT] P2. **unified-trading-pm** — author a QG check (mirroring the existing writer-side
      `check_manifest_writer_missing_write_before_return.py` pattern) that flags a NEW bare
      `read_availability_index(bucket)` call site with no `columns=`/`filters=` kwarg in production (non-test,
      non-scripts) code, baseline-ratcheted against the current corpus so existing bare calls don't block CI but no NEW
      ones can land silently. This closes the "no enforcing gate exists" gap for good, not just this one-time audit's
      findings.
