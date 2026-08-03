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
    /plans/archive/issues/manifest_completeness_full_corpus_map_build_2026_07_20.md,
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
context_scope:
  [
    unified-trading-library/unified_trading_library/manifest_writer/_read_index.py,
    deployment-api/deployment_api/services/manifest_source.py,
    /codex/02-data/honest-coverage-model.md,
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
    /plans/archive/issues/read_availability_index_slim_path_silent_empty_return_2026_07_27.md,
    features-service/features_service/volatility/core/orchestration_service.py,
  ]
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

- [x] ✅ [SCRIPT] P0. **DONE 2026-07-27 (slot-15)** — `market-tick-data-service@2031aa4b`. **market-tick-data-service**
      — `reader.py:839` `_resolve_pipeline_mode_from_manifest`: projected
      `read_availability_index(bucket, columns=["venue","data_type","instrument_type","date","capture_status","pipeline_mode"])`
      (verified column set by direct read of the function body — includes `pipeline_mode` for the CF-3 lift at lines
      862-864). Added 2 regression tests: one pins the exact call signature so a future edit can't silently drop back to
      a bare call, the other proves the CF-3 lift still fires when fed a genuinely narrow manifest DataFrame carrying
      only the projected columns (not a wider convenience frame that happens to satisfy the column-membership check).
      `quality-gates.sh` green (241s, on the 2nd attempt — the 1st clean pass's sentinel was invalidated by quickmerge's
      own auto-rebase against a concurrently-pushing branch), shipped via quickmerge --agent.
- [x] ✅ [SCRIPT] P0. **DONE 2026-07-27 (slot-12)** — `market-tick-data-service@27bdba6c`. **market-tick-data-service**
      — `engine/orchestrator/__init__.py:509` `_run_preflight_availability_check`: projected to the columns actually
      read in the function body, confirmed by direct read (`date`/`capture_status`/`instrument_count`/`error_reason` for
      the skip-mask, `venue`/`data_type`/`instrument_id`/`underlying`/`quote_asset`/`margin_type` in the per-row atom
      loop) — same incident class as `mtds_backfill_vm_startup_oom_rc137_2026_07_14`. The column list lives as
      `_PREFLIGHT_AVAILABILITY_COLUMNS` in `engine/orchestrator/preflight.py` (alongside its sibling constants) rather
      than inline, to keep `__init__.py` under the 900-line file-size cap. New regression test
      (`test_preflight_projects_columns_to_avoid_full_index_load`) asserts the projection is applied AND that behavior
      is unchanged. Full `quality-gates.sh` green (7094 tests passed, multiple independent runs), shipped via quickmerge
      --agent (5 attempts — 4 blocked by a fast-moving shared branch drift / one transient fleet-contention
      PM-integration-test kill, each confirmed transient and resolved by rebase+retry, not a code defect).
- [x] ✅ [SCRIPT] P0. **ml-service** — `inference/app/core/manifest_inference_guard.py:46`
      `check_manifest_for_inference` — **SHIPPED 2026-07-27 (slot-10)**, `ml-service@0bd5e6a`. Confirmed by direct read
      (not the guessed default): `_filter_to_day` reads `date`/`asset_group`; `_classify_day_rows` reads
      `capture_status` — no other columns touched anywhere in the module. Projected
      `columns=["date","asset_group","capture_status"]` exactly. Added a regression test
      (`test_read_availability_index_is_column_projected`) pinning the exact call signature so a future edit to either
      function is forced to also update the projection. Full test file green (12 tests) + `quality-gates.sh` green
      (302s).
- [x] ✅ [SCRIPT] P1. **DONE 2026-07-27 (slot-11)** — `ml-service@f615de1`. **ml-service** —
      `training/app/core/manifest_gap_handler.py:54` `apply_manifest_quality_flags`: same treatment as the inference
      guard above. Confirmed by direct read (not the guessed default): `_filter_manifest_to_window` reads
      `date`/`asset_group`; `_build_per_day_status` reads `date`/`capture_status`/`error_reason` — no other columns
      touched anywhere in the module. Projected `columns=["date","asset_group","capture_status","error_reason"]`
      exactly. Added a regression test (`test_read_availability_index_is_column_projected`) pinning the exact call
      signature (mirrors the inference guard's existing pattern), so a future edit to either function is forced to also
      update the projection. Full `quality-gates.sh` green (227s, 2111 tests passed), shipped via quickmerge --agent.
- [x] ✅ [SCRIPT] P0. **deployment-api** — `services/manifest_source.py:164` — **SHIPPED 2026-07-27 (slot-10)**,
      `deployment-api@489d747`. Reused the already-defined `DRILLDOWN_COLUMNS` (line 74) on the bare fallback branch,
      matching the pushdown branch above it exactly (no `filters=` — this IS the unfiltered stale-tolerant full read).
      Single highest-blast-radius fix in this audit (feeds ~10 downstream dashboard endpoints transitively). Updated the
      one existing test asserting the exact call signature (`test_live_mode_delegates_to_utl_reader`); full test file
      green (9 tests) + `quality-gates.sh` green (260s).
- [x] ✅ [SCRIPT] P1. **DONE 2026-07-27 (slot-10)** — `deployment-api@d143a44`. **deployment-api** —
      `routes/data_status/_catalogue.py:186` + `routes/data_status/_live_coverage.py:457`: both raw-UTL-import call
      sites projected via the existing `DRILLDOWN_COLUMNS` (`services/manifest_source.py`) — reused rather than a new
      bespoke list, matching the pattern the `services/manifest_source.py:164` fix above already established. Column
      coverage confirmed by direct read of each caller's downstream usage: `_catalogue.py` needs
      `instrument_id`/`venue`/`instrument_type`/`data_type` (narrow + row fields), `written_at` (the dedup latest-wins
      sort key — dropping it would silently degrade dedup to insertion order),
      `capture_status`/`error_reason`/`attempted_at` (row fields), and `league_id`/`source` (`is_mvp_for_manifest_row`'s
      sports MVP axes); `_live_coverage.py` needs every field `_build_live_row` reads
      (`venue`/`chain`/`data_type`/`instrument_type`/`instrument_id`/`league_id`/`timeframe`/`feature_group`/
      `capture_status`/`attempted_at`) plus `pipeline_mode` (the live-shard filter column) — all present in
      `DRILLDOWN_COLUMNS`; deliberately did NOT add `name`/`base_asset`/`market_group` since those are not real
      `availability_index.parquet` schema columns (confirmed against UTL `_V8_COLUMNS`) and requesting an absent column
      would trigger the slim reader's full-schema fallback on every shard, defeating the projection. Added a regression
      test per call site (`test_manifest_read_is_column_projected`,
      `test_live_status_manifest_read_is_column_projected`) pinning the exact `columns=DRILLDOWN_COLUMNS` call
      signature. Full `quality-gates.sh` green (4984 passed, 16 skipped), shipped via quickmerge --agent.
- [x] ✅ [SCRIPT] P1. **DONE 2026-07-27 (slot-15)** — `unified-trading-library@60a84d4a`. **unified-trading-library** —
      `feature_service_base/manifest_discovery.py:59,99,224,274` (4 call sites, shared by
      delta_one/volatility/onchain/cross_instrument — onchain is defi-adjacent): the first site (`read_manifest_rows`,
      then line 59) was already fixed by a prior slot's commit `06190d77` before this task picked it up. Projected the
      remaining 3 to their own actual column usage (read each function individually, not a mechanical shared list):
      `get_captured_instruments` →
      `columns=["capture_status","date","data_type","venue","instrument_type","instrument_id"]` (confirmed via
      `compose_instrument_ids`'s downstream column reads); `check_dependency_via_manifest` →
      `columns=["date","data_type","capture_status"]` + a `date` (and conditional `data_type`) row-group pushdown filter
      (both required/optional args map directly to equality filters); `resolve_spot_perp_from_manifest` →
      `columns=["date","capture_status","venue","instrument_type","instrument_id"]` + a `date` filter. Added a
      regression test per function pinning the exact `columns=`/`filters=` call signature so a future edit can't
      silently drop back to a bare call. Full `quality-gates.sh` green (244s-272s, 2 runs), shipped via quickmerge
      --agent.
- [x] ✅ [SCRIPT] P1. **DONE 2026-07-27 (slot-8)** — no code change needed, already fixed. **unified-trading-library** —
      `manifest_freshness.py:362` (`ManifestFreshnessCache._refresh_locked`): verified by direct read — the call is
      ALREADY projected (`columns=[*_ROW_KEY_COLUMNS, "capture_status", "error_reason"], filters=filters`), shipped in a
      prior commit (`unified-trading-library@0fc088a9`, "fix(manifest): ManifestFreshnessCache uses slim column-pruned
      read_availability_index, not the ~6.5GB full-schema path" — same `mtds_backfill_vm_startup_oom_rc137_2026_07_14`
      incident class as the other findings in this audit). A regression test already exists and pins the exact
      projection (`tests/unit/test_manifest_freshness.py::test_bulk_load_uses_slim_column_path` — asserts `columns=` is
      present and contains `capture_status`/`error_reason`/the row-key columns). Not bare; nothing to fix.
- [x] ✅ [SCRIPT] P2. **DONE 2026-07-30 (slot-6)** — `unified-trading-library@6b0d0847`. **unified-trading-library** —
      of the 9 bare sites across `_queries.py`/`_maintenance.py`/`_writer_io.py:156`, projected the 4 that are genuinely
      safe (confirmed by direct read of each function's own downstream column usage, per this doc's caution):
      `_queries.py` `check_data_available` → `columns=["date","venue"]`; `read_capture_status_counts` →
      `columns=["data_type","date","capture_status","error_reason"]` (`asset_group` kwarg is dead — never used in the
      function body, confirmed by direct read); `_maintenance.py` `purge_venue_before_date`'s first (dry-run/count-only)
      read → `columns=["venue","date"]` (the real `dry_run=False` write-back re-fetches a fresh, unprojected index via
      `merge_canonical_with_outstanding_shards()` and never reuses this one); `emit_migration_manifest_updates`'s
      snapshot read → `columns=["date","venue","service_name","data_type"]` (only feeds `_remove_legacy_entries()`'s
      length-based `legacy_removed` estimate; the real write-back similarly re-fetches fresh). Left the remaining 5
      sites bare, WITH an in-code comment explaining why at each: `reconcile_manifest()`, `rebuild_manifest()`,
      `rebuild_manifest_from_canonical_paths()`, and `merge_manifest_from_canonical_paths()` all return or write the
      read DataFrame VERBATIM (full schema) on at least one code path (a dry-run return, an early blob-listing-failure
      return, or the actual GCS write-back) — projecting would silently truncate the manifest schema on that path, a
      correctness regression, not a memory win; `_writer_io.py:156` `lookup()` already needs ~25 of the ~30 V8 schema
      columns to build `ManifestRow` plus any of `_ROW_KEY_COLUMNS` the caller's `row_key` specifies, so a projection
      would buy negligible memory savings while adding real risk of dropping a column a future schema addition needs.
      Also fixed a latent test-isolation gap this exposed: `test_manifest_writer_coverage_counts.py`'s
      `_reset_module_state` fixture cleared `_INDEX_CACHE` but not `_INDEX_SLIM_CACHE` — invisible while
      `read_capture_status_counts()` used the full-schema path, but once it started resolving through the slim-cache
      path a stale cached count leaked across tests sharing the `"test-bucket"` name. Added
      `tests/unit/test_manifest_writer_bare_reads_column_projection.py` pinning the exact `columns=` call signature per
      fixed site (4 tests). Full `quality-gates.sh` green (149s, 2 runs — pre-commit + post-commit sentinel re-verify),
      shipped via quickmerge --agent.
- [x] ✅ [SCRIPT] P1. **DONE 2026-07-27 (slot-12)** — `features-service@e23d4da7`. **features-service** —
      `common/__init__.py:99`, `common/manifest_window_guard.py:115`, `common/manifest_leg_guard.py:98`: projected each
      to its actual column usage, confirmed by direct read (not a mechanical shared list):
      `resolve_latest_captured_date` → `columns=["date","capture_status","data_type"]`; `check_window_manifest` →
      `columns=["date","capture_status","schema_version"]` (`schema_version` required so `_warn_on_v9_schema_drift`'s
      GAP-4 mixed-version WARN keeps firing — dropping it would silently disable that drift check);
      `_read_single_leg_status` → `columns=["date","capture_status"]`. `asset_group` deliberately excluded from all
      three: it is not in UTL's reader-side `_V8_COLUMNS` full-schema list, so requesting it would trigger the slim
      reader's costly full-schema-fallback on any shard lacking it (defeating the projection) — both guards already
      treat its absence as a no-op (own docstring: "the bucket already scopes to one asset_group"), so exclusion matches
      existing production behavior, not a regression. Added a regression test per call site
      (`test_read_availability_index_is_column_projected`) pinning the exact `columns=` call signature. Full
      `quality-gates.sh` green (2 runs — pre-commit + post-commit sentinel re-verify), shipped via quickmerge --agent.
- [x] ✅ [SCRIPT] P2. **DONE 2026-07-30 (slot-3)** — `features-service@edf80c88`. **features-service** —
      `volatility/engine/orchestrator.py:276` (now `:286`, line shifted),
      `volatility/core/orchestration_service.py:168`, `volatility/core/data_loader.py:364`,
      `delta_one/app/core/dependency_checker.py:619` (now `:756`, line shifted): projected each to its actual column
      usage, confirmed by direct read (not a mechanical shared list) — `volatility/engine/orchestrator.py`
      `_list_chain_files` → `columns=["date","venue","data_type","instrument_type","capture_status","instrument_id"]` +
      a `date` filter (`asset_group` deliberately excluded: confirmed by direct read of UTL's `_read_index.py`
      `_V8_COLUMNS` that `asset_group` is absent from the schema in ANY version and never synthesized by the reader, so
      the function's own `"asset_group" in row.index` check is unreachable regardless of projection — unlike the
      `strategy-service` sibling fix's precedent where `asset_group` was a real functional filter, here it is dead
      weight); `orchestration_service.py` `_list_chain_files` (a near-identical twin with no `asset_group` logic) → same
      columns + filter; `data_loader.py` `_resolve_spot_perp` →
      `columns=["venue","instrument_type","instrument_id","data_type",     "capture_status","date"]` + a `date` filter
      (matches the function's own existing post-read column-select exactly; simplified that now-redundant reselection to
      `index.astype(str)` as part of the same change, which also brought the method back under the 50-line QG
      method-size cap); `dependency_checker.py` `_build_captured_index` →
      `columns=["date","venue","instrument_id","data_type","capture_status"]`, deliberately **no** `filters=` (unlike
      this doc's other date-scoped fixes) since this call scans ALL dates to build a reusable lookback index, not one
      specific date. Added a regression test per call site (`test_read_availability_index_is_column_projected`,
      mirroring the established naming convention) pinning the exact `columns=`/`filters=` call signature; the
      `orchestration_service.py` call site had zero prior test coverage at all, so a new
      `tests/volatility/unit/test_core_orchestration_service.py` was added rather than folding into the
      similarly-named-but-unrelated `test_orchestration_service.py` (which tests a different class,
      `feature_group_service.VolatilityOrchestrationService` — see the follow-up todo below). Full `quality-gates.sh`
      green (17979 passed, 209 skipped, 2 runs — pre-commit + post-commit sentinel re-verify).
- [x] [SCRIPT] P1. ✅ **DONE 2026-07-27 (slot-3)** — `strategy-service@b26bb306`. **strategy-service** —
      `manifest_allocation_guard.py:170` `check_allocation_manifest`: projected to
      `columns=["date", "asset_group",     "capture_status", "schema_version"]` + `filters=[("date", "==", date_str)]`.
      **`asset_group` deliberately KEPT** (unlike the features-service sibling fix's guards) — here it is a REAL
      functional filter (`matching = manifest[date_mask & (manifest["asset_group"]...)]`), not a presence-only no-op;
      dropping it would silently widen the match to every asset_group for the date, returning the wrong capture_status —
      a correctness regression, not a safe exclusion. `asset_group` is not in UTL's `_V8_COLUMNS`, so this projection
      falls back to a full-schema decode per legacy (pre-v9) shard (`_read_parquet_columns_safe`'s per-shard
      `ValueError` fallback) — a real, accepted cost while the corpus is still mostly pre-migration; the `filters=` date
      pushdown is the dominant memory lever regardless (row-group skip, not post-decode) and applies on both paths.
      Added `test_read_availability_index_is_column_projected` pinning the exact `columns=`/`filters=` call signature —
      17/17 tests passing. Full `quality-gates.sh` green, shipped via quickmerge --agent.
- [x] ✅ [SCRIPT] P1. **DONE 2026-07-28 (slot-4)** — `instruments-service@1a6dad1b`. **instruments-service** —
      `engine/orchestrator/venue_core.py:222` `_get_manifest_high_watermarks`: projected to
      `columns=["venue", "instrument_count", "date"]` — confirmed by direct read of the loop body (only these 3 columns
      are ever accessed: `index_df["venue"]`, `index_df["instrument_count"]`, `index_df["date"]`). Added
      `test_read_availability_index_is_column_projected` pinning the exact `columns=` call signature so a future edit
      can't silently drop back to a bare call. Also synced `uv.lock` to `pyproject.toml`'s `fastapi>=0.137.0` constraint
      (the stale lock pinned 0.135.1, which broke `conftest.py`'s UTL import chain and blocked tests from even
      collecting — pre-existing drift, unrelated to this fix, fixed as a prerequisite to running QG at all). Full
      `quality-gates.sh` green (126s, 2nd run against committed HEAD for the sentinel), shipped via quickmerge --agent.
- [x] ✅ [SCRIPT] P2. **DONE 2026-07-30 (slot-2)** — no code change needed, already fixed. **instruments-service** —
      `engine/orchestrator/process_completeness.py:468` (now `:474`) `_detect_thin_day_venues`: verified by direct read
      — the call is ALREADY projected (`columns=sorted(_required)` where
      `_required = {"asset_group", "capture_status", "venue", "date", "instrument_count"}`), shipped in a prior commit
      (`instruments-service@5134a5f0`, "fix(sports): bound memory in daily-enum sports historical-index reads",
      2026-07-27) as a side effect of the `sports_is_daily_enum_backfill_oom_at_32gi_ceiling_2026_07_27.md` fix — same
      incident class as `mtds_backfill_vm_startup_oom_rc137_2026_07_14`. Confirmed the projected columns match the
      function's own downstream usage exactly (asset_group/capture_status/date drive the CeFi-history mask; venue groups
      the history; date/instrument_count feed the per-venue median groupby — no other column is touched anywhere in the
      function). Not bare; nothing to fix.
- [x] ✅ [SCRIPT] P2. **DONE 2026-07-30 (slot-2)** — `batch-live-reconciliation-service@11cec2c`.
      **batch-live-reconciliation-service** — `stages/stage0_manifest_reason_check.py:177`
      `check_manifest_reason_agreement`: projected to `columns=["date","pipeline_mode","capture_status","error_reason"]`
      — confirmed by direct read of `_get_sides()` (the only reader of the returned DataFrame): `date` for the row
      filter, `pipeline_mode` for the batch/live split (incl. the `"pipeline_mode" not in manifest_df.columns` pre-v8
      fallback check), `capture_status` + `error_reason` for the per-side status/reason extraction — no other column is
      touched anywhere in the module. `asset_group` deliberately excluded (module docstring already states "the bucket
      is already scoped to one asset_group", and it is not a real schema column per UTL's `_V8_COLUMNS`). No `filters=`
      added — the real production caller (`stage0_data_pipeline_recon.py`) always passes a single-date list today, but
      the function's own contract accepts an arbitrary `dates: list[str]` (exercised by the existing
      `test_multiple_dates_mixed_outcomes` test), so a single-date equality filter would silently break the multi-date
      case; scope stayed to the todo's literal ask (column projection only). Added
      `test_read_availability_index_is_column_projected` pinning the exact `columns=` call signature. Full
      `quality-gates.sh` green (36s, 2 runs — pre-commit + post-commit sentinel re-verify), shipped via quickmerge
      --agent.
- [x] ✅ [SCRIPT] P2. **DONE 2026-07-30 (slot-12)** — `deployment-service@b1480a1`. **deployment-service** —
      `cli/utils/manifest_reader.py`: projected all 5 bare `read_availability_index()` call sites in the file (not just
      the 3 originally cited at `:245,585,674` — `is_available`/`get_manifest_status` are the same file, same bug class,
      fixed in the same commit per the findings-triage "in your file" rule): `is_available` → `columns=["date"]` (return
      value is never inspected, cheapest single column); `get_completion` → `columns=["date","service_name","venue"]`;
      `get_manifest_status` → `columns=["date","venue","service_name","league_id"]` (verified by direct read that
      `_build_league_breakdown` also needs `league_id` — easy to miss); `get_venue_detail` → `columns=["venue","date"]`;
      `get_coverage_summary` → `columns=["date","venue","instrument_count"]`. Each column set confirmed by direct read
      of the function body's downstream usage (per the doc's caution above). Added 5 regression tests
      (`tests/unit/test_manifest_reader_column_projection.py`) pinning the exact `columns=` call signature per site so a
      future edit can't silently drop back to a bare call. `quality-gates.sh` green (199s), shipped via quickmerge
      --agent.
- [ ] [SCRIPT] P3. **features-service** smoke scripts (cross_instrument/multi_timeframe/volatility/onchain/delta_one
      `smoke_matrix.py`), **e2e-testing** (`build_smoke/live_manifest_reader.py:98`,
      `strategy/backtest_from_wizard_config.py:192`), **unified-trading-pm**
      (`plans/audit/results/     available_at_fill_rate_audit_2026_07_13.py:51`,
      `scripts/qg/honest_coverage_ratchet.py:66`): lower-urgency CI/audit-tooling call sites; project if convenient when
      touching these files for other reasons, not worth a dedicated dispatch on their own.
- [x] ✅ [SCRIPT] P2. **DONE 2026-07-31 (slot-5, checkbox flip verified slot-9)** — `unified-trading-pm@dbce7a24c`.
      **unified-trading-pm** — added `scripts/quality_gates/check_bare_read_availability_index.py` (AST-walk,
      production-code-only, mirrors `check_manifest_writer_missing_write_before_return.py`'s shrinking-ratchet pattern
      exactly: `Finding`/`BaselineEntry` dataclasses, `baseline_key = (repo, file, line, function)`,
      `# QG-allow: bare-read-availability-index` inline escape) + a bootstrapped 24-entry
      `read_availability_index_bare_call_baseline.yaml` (classified `wrapper_alias_already_projected_internally` /
      `intentionally_bare_verbatim_schema_required` / `pending_triage`) + `test_check_bare_read_availability_index.py`
      regression tests + `base-service.sh` STEP 5.106 wiring. Re-verified 2026-07-31 (slot-9): re-ran a full
      workspace-wide sweep (`--workspace-root <ws>`, no `--scope`) against current HEAD post-FF-pull — output is exactly
      the 24 baselined WARNs enumerated in the yaml, `0 new occurrences`, confirming the baseline still matches reality
      after the intervening commits since bootstrap. This closes the "no enforcing gate exists" gap — a NEW bare call
      site now fails CI instead of landing silently.
- [ ] [SCRIPT] P3. **features-service** — investigate whether
      `features_service/volatility/core/orchestration_service.py`'s `VolatilityFeaturesOrchestrator` class is dead code:
      it defines a near-identical (but simpler, no `asset_group`/ `pipeline_mode` derivation) twin of
      `features_service/volatility/engine/orchestrator.py`'s class of the SAME name. Grepped the whole repo (excluding
      tests/`__pycache__`): nothing outside its own file + `core/__init__.py`'s re-export imports it — every sibling
      caller (`cli/handlers/batch_handler.py`, `engine/feature_group_service.py`, etc.) imports
      `data_loader`/`feature_writer`/`dependency_checker` from `core/`, never `orchestration_service`. Found while
      fixing todo above (2026-07-30, slot-3) — this file's `_list_chain_files` had ZERO existing test coverage,
      consistent with genuinely-unreferenced code. Not deleted here (out of scope for a column-projection fix, and
      grep-based "unused" is not proof — `FeatureProcessingResult` in this same file WAS deliberately collapsed to a
      cross-import from `engine/orchestrator.py` back in 2026-05-11 per `features_service_qg_cleanup` Phase 1.2e, so the
      class itself may be a leftover the same cleanup missed). **Done when**: confirmed genuinely dead (no dynamic
      import / plugin-registry / CLI entry-point reference beyond static grep) and deleted, OR confirmed it has a real
      caller and this todo is closed as not-applicable.

- [ ] [SCRIPT] P1. **instruments-service** — 3 NEW bare `read_availability_index(bucket)` call sites in
      `instruments_service/cli/main.py` (lines 82 `_run_coverage_status()`, 154 `_run_refresh_league_entity_coverage()`,
      294 `_run_reprocess_shards()`), introduced by CLI subcommand additions landed 2026-08-03 (after the 2026-07-31
      gate-add + re-verify sweep found 0 new occurrences) — confirmed via
      `check_bare_read_availability_index.py --scope instruments-service` on a clean-tree HEAD unrelated to any other
      in-flight diff. Each needs `columns=`/`filters=` added per this doc's caution (confirm via a DIRECT read of each
      function's downstream column usage, do not guess/copy a list from another site), or a
      `# QG-allow: bare-read-availability-index` marker if genuinely unprojectable. Currently blocking
      `quality-gates.sh` for ANY instruments-service change (a repo-blocker was declared for this — see this doc's
      Progress Log below).

## Progress Log

- **context-scout 2026-08-03**: populated/refreshed context_scope (6 entries) — added
  `features-service/features_service/volatility/core/orchestration_service.py`, the target of the sole remaining P3
  dead-code-investigation todo.
- **2026-08-03 (slot-8)**: hit this gate's STEP 5.106 failure while shipping an unrelated Pyth oracle_prices fix
  (`defi_satellite_ao_dispatch_batch3-013`) — verified pre-existing via a clean re-run of
  `check_bare_read_availability_index.py --scope instruments-service` (no diff of mine touches `cli/main.py`; my commit
  `8a5fcdce` only touches `reference_data/adapters/defi/pyth.py` + its test). Added the 3-site todo above (new since the
  2026-07-31 zero-new-occurrences re-verify — these came from CLI subcommands added 2026-08-03) and declared a
  repo-blocker (`qg_red`) rather than fixing this out-of-scope regression inline.
