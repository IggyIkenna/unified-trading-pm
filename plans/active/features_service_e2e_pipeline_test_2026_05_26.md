---
title: "Features-service end-to-end pipeline test (read → calculate → write → read-back) on real GCS data"
created: 2026-05-25
last_updated: 2026-05-25
parent_epic: features_and_ml_master
assigned_vm: vm-ml
name: features-service-e2e-pipeline-test-2026-05-26
priority: P0
status: active
estimate_class: brand-new
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 6
estimate_calibration_note: |
  brand-new (1.0×): a repeatable e2e harness driving read→calc→write→read-back per
  family does not exist yet (smoke_matrix is existence-only). The one bug fix
  (WRITE P0 write_daily_partition) is small; the bulk is net-new harness + real-infra
  validation runs across families.
locked_by: live-defi-rollout
locked_since: 2026-05-25
related_plans:
  - plans/active/features_input_manifest_migration_2026_05_25.md
  - plans/active/issues/cefi_processed_candles_manifest_file_disconnect_2026_05_25.md
---

## Goal

Stand up a **repeatable, real-data end-to-end test** of the full features-service pipeline for every family:

```
discover (v8 manifest) → READ inputs (GCS) → CALCULATE features → WRITE parquet (+ manifest row) → READ-BACK & assert
```

Today the **READ + CALCULATE** halves are proven on real CeFi data (delta_one/volatility/cross_instrument — see
`features_input_manifest_migration_2026_05_25.md`), but the pipeline has **never run clean through WRITE**: the first
instrument that loads hits `write_daily_partition: string index out of range` and writes 0 rows. This plan (a) fixes
that single WRITE blocker, (b) builds a harness that drives the whole chain on a live date, and (c) validates each
family end-to-end against real GCS — writing to **`-test` feature buckets** so prod output is never touched.

**Execution timing:** built today, **run tomorrow (2026-05-26)**. Items below are sequenced so a single operator session
can walk Phase 0 → 5 top to bottom.

**Scope guard — this plan does NOT re-do the read migration.** Read-discovery + dependency-gate fixes are owned by
`features_input_manifest_migration_2026_05_25.md` (delta_one/volatility/cross_instrument shipped; multi_timeframe is a
transitive verify there). This plan consumes those fixes and tests the chain end-to-end. New read-path bugs surfaced
here are filed back into the migration plan, not fixed here.

## Pre-audit (grounded 2026-05-25)

| Surface                  | Fact                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **WRITE P0 location**    | `features_service/delta_one/app/core/feature_writer.py` — `_write_daily_partitions` (L447) → `_try_write_day` (L477) → `_write_parquet` (L524). Error classified at `operation="write_daily_partition"` (L501).                                                                                                                                                                                                                                |
| **Likely root cause**    | `_write_parquet` (L524-548) passes `filename=f"{instrument_id}.parquet"` + `partition={day,feature_group,timeframe}` to `data_sink.write`. `instrument_id` is now the canonical `{venue}:{instrument_type}:{symbol}` (colons). `string index out of range` smells like path/partition templating on an empty or unexpectedly-short segment in the DataSink, OR a `day`/timeframe string slice. Reproduce first, then fix — do not guess-patch. |
| **CLI invocation**       | `python -m features_service.delta_one --operation compute --mode batch --asset-group CEFI --feature-group <group> --start-date <d> --end-date <d>`. `--feature-group ALL` expands the 17 CLI FEATURE_GROUPS (parser.py).                                                                                                                                                                                                                       |
| **Per-family CLIs**      | `features_service/<family>/cli/main.py` for delta_one, volatility, cross_instrument, multi_timeframe, onchain, sports, calendar, commodity.                                                                                                                                                                                                                                                                                                    |
| **Existing harness**     | `scripts/<family>/smoke_matrix.py` (8 families) — **existence-only**, single group per cell, and was using a dead default date. Not an e2e read→calc→write→readback driver. This plan adds the missing e2e driver.                                                                                                                                                                                                                             |
| **Known live test data** | CeFi `processed_candles`, BITGET-FUTURES / BITGET-SPOT, `2026-05-02`/`2026-05-03`, ~5,760–11,520 candle rows/instrument-day. Other CeFi venues + non-CeFi asset_groups are backfill-in-progress (read path skips them honestly).                                                                                                                                                                                                               |
| **Write target**         | `-test` feature buckets via `resolve_bucket_name(..., kind="features...", ...)` / `CLOUD_*` test overrides — never prod feature buckets for a test run.                                                                                                                                                                                                                                                                                        |

**Manifest version: v8 only.** All discovery + read-back go through `read_availability_index()` against the canonical
`-prd` bucket (100% schema_version 8). No pinned/legacy version anywhere in the chain.

## Phased DAG (QG gate between phases)

```
Phase 0 (env + golden dataset)
   └─> Phase 1 (WRITE P0 fix)  ──┐
                                 ├─> Phase 2 (delta_one full e2e on real data, → -test bucket)
                                 │       └─> Phase 3 (multi_timeframe — reads delta_one -test output)
                                 ├─> Phase 4 (volatility + cross_instrument full e2e)
                                 └─> Phase 5 (e2e harness + manifest-emission assertions + QG wiring)
```

Phases 2 and 4 are PARALLEL once Phase 1 is green. Phase 3 is SEQUENTIAL after Phase 2 (transitive input dependency).

### Phase 0 — Environment + golden test dataset `[P0]`

- [ ] [SETUP] P0. Fresh env check: `cd features-service && bash scripts/setup.sh`; confirm `unified_api_contracts` +
      `unified_trading_library` import. Confirm ADC to `central-element-323112`.
- [ ] [AUDIT] P0. Resolve the live golden test window from the v8 manifest (NOT a hardcoded date): latest date with
      `capture_status="captured"` `processed_candles` rows for CeFi. Record the exact
      `(date, venues, instruments,     data_types)` set the e2e run should reproduce — this is the assertion baseline
      for Phases 2-4.
- [ ] [SETUP] P0. Point feature output at `-test` buckets for this run (env overrides / `resolve_bucket_name` test
      kind). Verify a throwaway write+read round-trips to the test bucket before any real feature write.

### Phase 1 — Fix the WRITE P0 blocker `[P0]`

- [ ] 🔴 [BUG] P0. **Reproduce** `write_daily_partition: string index out of range` on one loaded BITGET perp
      (`--feature-group technical_indicators`, golden date, 1 instrument). Capture the full stack_trace from
      `classify_and_emit_error` (it currently swallows into `_emit_rejected`) — add a temporary re-raise / debug log if
      needed to see the failing frame.
- [ ] 🔴 [BUG] P0. **Root-cause + fix** in `feature_writer.py` (or the DataSink path-templating it calls). Most likely
      the colon-bearing canonical `instrument_id` or an empty partition segment breaks a string slice. Fix the actual
      defect; do NOT mask it by sanitising the id away from canonical `{venue}:{instrument_type}:{symbol}` (that would
      desync from the MDPS/read side). Add a unit test with a colon-bearing instrument_id + a single-day frame.
- [ ] [VALIDATE] P0. Re-run the repro: ≥1 BITGET perp writes a non-empty parquet to the `-test` bucket; per-day
      `INSTRUMENT_DAY_PROCESSED` event emitted with `rows_written>0`. QG green.

### Phase 2 — delta_one full e2e (reference path) `[P0]`

- [ ] [VALIDATE] P0. Run `--operation compute --mode batch --asset-group CEFI --feature-group ALL` on the golden window
      for the captured BITGET universe. Assert: every captured instrument either writes features OR skips with a typed
      honest-absence reason; **zero** unhandled 404 / NoneType / write exceptions; "N/N completed" matches the captured
      count from Phase 0.
- [ ] [VALIDATE] P0. **Read-back assertion.** Re-read the written `-test` parquets: non-null feature columns, row count
      ≈ input candle count, `timestamp`/`timestamp_out` present and monotonic (point-in-time guard holds), a sampled
      feature in range (e.g. `rsi_14 ∈ [0,100]`). Sample-inspect one parquet by eye.
- [ ] [VALIDATE] P0. **Manifest emission assertion.** Confirm each successful write co-emits a v8 manifest row
      (`capture_status="captured"`, `service_name="features-service"`, nonzero count) for the `-test` feature bucket —
      the write half of honest-coverage, mirroring the MDPS writer contract.

### Phase 3 — multi_timeframe (transitive on delta_one output) `[P1]`

- [ ] [VALIDATE] P1. Point multi_timeframe input at the delta_one `-test` output from Phase 2; run its CLI on the golden
      window. Confirm it discovers + reads delta_one features and computes multi-timeframe aggregates end-to-end (no
      code change expected — this is the transitive unblock the migration plan's Phase 4 names). Read-back assert as in
      Phase 2.

### Phase 4 — volatility + cross_instrument full e2e `[P1]` (PARALLEL with Phase 2)

- [ ] [VALIDATE] P1. **volatility** full e2e on the golden window (processed-candle path only — raw options/futures
      chain is gated/not-backfilled per migration plan Phase 2). read → calc → write `-test` → read-back assert. Honest
      absence for un-backfilled chain inputs must skip, not crash.
- [ ] [VALIDATE] P1. **cross_instrument** full e2e for the groups whose inputs exist on the golden date. Note the 5
      groups needing raw normalized book/trade schema (book_depth_bands, liquidity_walls, liquidation_clusters,
      flow_interaction, composite_sr) will honestly skip — that is the tracked P2 data-surface gap in the migration
      plan, not a failure here. Read-back assert the groups that do compute.

### Phase 5 — e2e harness + governance `[P1]`

- [ ] [SCRIPT] P1. Add a reusable driver `scripts/e2e/run_pipeline_e2e.py` (or extend per-family `smoke_matrix.py`)
      that, for a given `(asset_group, family, date)`, runs discover→read→calc→write(`-test`)→read-back and asserts the
      Phase 2 checks. Live-date resolver (no hardcoded date). One command per family; exit non-zero on any unhandled
      error.
- [ ] [SCRIPT] P1. Wire the e2e driver into features-service `quality-gates.sh` as a smoke step (mock/`-test` bucket,
      one family one date) so the chain can't silently regress. Per the "peripheral scripts under primary-consumer QG"
      HARD RULE.
- [ ] [DOC] P1. Update `codex/02-data/data-lineage-MTDS-features-ml.md` (+ availability-manifest doc if touched) to
      record the features WRITE-side manifest-emission contract proven in Phase 2.

## Success criteria

- **B3 (data-pipeline KPI):** for the golden window, ≥ **99.9%** of v8-`captured` CeFi instruments either compute+write
  features OR record a typed honest-absence reason — **zero** silent failures, unhandled 404s, NoneType crashes, or
  write exceptions.
- delta_one, volatility, cross_instrument, multi_timeframe each complete **read → calculate → write → read-back** on
  real recent GCS data, output in `-test` buckets, with a co-emitted v8 manifest row per successful write.
- `write_daily_partition: string index out of range` is root-caused + fixed + unit-tested (colon-bearing instrument_id).
- `bash scripts/quality-gates.sh` exit 0 (features-service); e2e driver wired into QG smoke and green on the golden
  date.

## Full-execution criterion (per "Plans Run To Actual Completion" HARD RULE)

- ✅ The e2e driver runs to completion on real GCS for the golden window, per family, with parquet + manifest written to
  `-test` buckets and read back with assertions passing.
  - **What ran:**
    `python -m features_service.<family> --operation compute --mode batch --asset-group CEFI     --feature-group ALL --start-date <golden> --end-date <golden>` +
    `scripts/e2e/run_pipeline_e2e.py`, on vm-ml / operator host with ADC to `central-element-323112`.
  - **Verification:** `read_availability_index(<test-feature-bucket>)` shows `features-service` `captured` rows; sampled
    `-test` parquet read back with non-null features in range.
- **Handoff exception:** prod-bucket feature writes + full multi-asset-group coverage deferred to the backfill landing +
  `features_and_ml_master` Phase 3 (honest-absence recording). Justification: non-CeFi inputs are backfill-in-progress;
  this plan proves the chain is correct on the data that exists today and auto-extends as backfill lands.

## Continuous verification

- e2e driver wired into features-service QG smoke (Phase 5) — runs on a rolling live date each QG pass.
- Grep guard already in the migration plan (no `instrument_type=`/`@LIN`, no `max_results` on discovery) protects the
  read half; this plan's QG smoke protects the write + read-back half.

## Notes / cross-refs

- Read-path fixes + the downstream findings (Bitfinex empty `instrument_type`, MTDS dual-write, the CeFi manifest↔file
  disconnect) are owned by `features_input_manifest_migration_2026_05_25.md` +
  `issues/cefi_processed_candles_manifest_file_disconnect_2026_05_25.md`. This plan does not duplicate them.
- Composes with HARD RULE _Data Pipeline Correctness Is The Heartbeat_ (the WRITE half is the other half of honest
  coverage; an un-emitted manifest row on a real feature write is the same class of divergence as a phantom `captured`).
- `onchain`/`sports` reads are the reference manifest-driven model; do not regress them when adding the shared harness.
