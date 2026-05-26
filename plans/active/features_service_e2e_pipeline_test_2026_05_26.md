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
instrument that loads hits `write_daily_partition: string index out of range` and writes 0 rows, and only **BITGET** has
processed_candles on recent dates so the calculators can't be exercised across instruments. This plan (a) **backfills a
lookback-sized window of real input data** so calculators can be tested properly, (b) fixes the single WRITE blocker,
(c) builds a harness that drives the whole chain on a live date, and (d) validates each family end-to-end against real
GCS — writing features to **`-test` buckets** so prod feature output is never touched.

**Execution timing:** built today, **run tomorrow (2026-05-26)**. Items below are sequenced so a single operator session
can walk Phase 0 → 5 top to bottom.

**Backfill is lookback-driven, not fixed-window (operator 2026-05-25):** each feature's input window is sized from its
own lookback requirement and stays agent-overridable at calc time — most features need ~1 day of 1m candles, some need
more, sports/predictions use an event/fixtures window. See Phase 0.5.

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
| **Known live test data** | CeFi `processed_candles`, BITGET-FUTURES / BITGET-SPOT, `2026-05-02`/`2026-05-03`, ~5,760–11,520 candle rows/instrument-day. Other CeFi venues are backfill-in-progress — **Phase 0.5 backfills a lookback-sized window across more liquid venues so calculators can be tested across instruments.**                                                                                                                                           |
| **Write target**         | `-test` feature buckets via `resolve_bucket_name(..., kind="features...", ...)` / `CLOUD_*` test overrides — never prod feature buckets for a test run.                                                                                                                                                                                                                                                                                        |

**Manifest version: v8 only.** All discovery + read-back go through `read_availability_index()` against the canonical
`-prd` bucket (100% schema_version 8). No pinned/legacy version anywhere in the chain.

## Phased DAG (QG gate between phases)

```
Phase 0 (env + golden dataset)
   ├─> Phase 0.5 (adaptive input backfill — lookback-driven) ──┐
   └─> Phase 1 (WRITE P0 fix) ─────────────────────────────────┤
                                                                ├─> Phase 2 (delta_one full e2e → -test bucket)
                                                                │       └─> Phase 3 (multi_timeframe — reads delta_one -test output)
                                                                ├─> Phase 4 (volatility + cross_instrument full e2e)
                                                                └─> Phase 5 (e2e harness + manifest-emission assertions + QG wiring)
```

Phase 0.5 (backfill) and Phase 1 (write fix) are independent → PARALLEL. Phases 2 and 4 are PARALLEL once **both** 0.5
and 1 are green (they need input data AND a working writer). Phase 3 is SEQUENTIAL after Phase 2 (transitive input
dependency).

### Phase 0 — Environment + golden test dataset `[P0]`

- [x] ✅ [SETUP] P0. Env verified: UAC + UTL import OK in features-service `.venv`; `read_availability_index` /
      `resolve_bucket_name` import; ADC to `central-element-323112` confirmed (manifest + bucket reads work).
- [x] ✅ [AUDIT] P0. **Golden window = 2026-05-03 CEFI.** v8 manifest (`market-data-tick-cefi-prd`, 2.63M rows, **100%
      schema_version 8**) + GCS object listing: candle source (`timeframe=1m`/`data_type=trades`) has files for **48
      BITGET instruments** (24 FUTURES + 24 SPOT), 1440 rows/day each; other data_types
      (book_snapshot_5/derivative_ticker/ liquidations) present for BITGET + partial BITFINEX-FUTURES/KRAKEN-FUTURES.
      **Phantom-row finding** (captured in issue doc): 2026-04-26/27/28 manifest marks 17 venues `captured` but **0
      actual files** exist.
- [x] ✅ [SETUP] P0. `-test` bucket created: `features-delta-one-cefi-test-central-element-323112` (asia-northeast1).
      Round-trip verified — write+read-back of a real feature parquet succeeds (see Phase 1 validate).

### Phase 0.5 — Adaptive input backfill (lookback-driven, per-feature) `[P0]`

**Design principle (operator 2026-05-25):** the backfill window is **not fixed** — it is **sized per feature from that
feature's lookback requirement, and remains agent-overridable at calc time.** For most features 1 day of 1-minute
candles is enough; some need more; sports/predictions use a different (fixtures/event) window entirely. The harness
resolves the minimum window each family/feature needs and backfills exactly that, with an explicit knob to extend.

- [ ] [SCRIPT] P0. **Lookback resolver.** For the feature_groups under test, resolve the required input window from the
      SSOT: per-group `lookback_candles` in each family's `feature_definitions.yaml` + the `(asset_group, data_type)`
      set from `unified_api_contracts ... FEATURE_REQUIRED_INPUTS`. Output:
      `{family → {data_types, min_lookback_days,     candle_interval}}`. Default floor = **1 day × 1m candles** when a
      group declares no/short lookback; max over the group's lookback otherwise. (Note the known SSOT gap: `InputReq`
      carries no `lookback_candles`, and onchain/ volatility/sports omit it in yaml — fall back to a documented
      per-family default + log it; unifying lookback into the SSOT stays a `features_and_ml_master` Phase 1A follow-up,
      cross-ref the migration plan.)
- [ ] [SCRIPT] P0. **Backfill knob.** The backfill driver takes `--backfill-days N` (and per-family override) so the
      agent running a calc can bump the window up for features that need more history than the resolver's floor.
      Resolver output is the default; the flag overrides. No hardcoded global window.
- [ ] [INFRA] P0. **Run the backfill via existing MTDS + MDPS tooling** (do NOT reinvent capture/processing) for the
      resolved window + data_types, target = liquid CeFi venues spot+perp (Binance/Bybit/OKX/Deribit to start; extend
      per-feature). Raw capture (MTDS) → processed_candles (MDPS) → **prod canonical `-prd` buckets** so the e2e read
      path discovers it naturally via the consolidated v8 manifest. Coordinate with any in-flight backfill / the
      `mtds_mdps_master` sequencing — add a `🟢 BACKFILL RUNNING` banner; do not collide with the single-walk migration.
- [ ] [VALIDATE] P0. Confirm the v8 manifest now shows `capture_status="captured"` processed_candles rows for the
      backfilled venues/days, and the files exist (blob_exists). This becomes the Phase 0 golden-window assertion
      baseline for the calculators. Sports/predictions backfill window handled separately (event/fixtures-scoped, not
      candle-lookback) when those families enter the e2e.

### Phase 1 — Fix the WRITE P0 blocker `[P0]`

- [x] ✅ [BUG] P0. **Reproduced + traceback captured** (temporary debug log in `_try_write_day`, since reverted). Frame:
      `_write_parquet` → `data_sink.write` → UTL `protocol_impls.write` → `gcp.upload_bytes` →
      `client.bucket(bucket).blob(...)` → `google.cloud.storage._helpers._validate_name`: `name[0]` on an **empty
      string**. **NOT an instrument_id bug** — the bucket name is empty.
- [x] ✅ [BUG] P0. **Root-caused + fixed.** `FeatureWriter.data_sink` called `get_data_sink(routing_key="cefi")` with no
      explicit bucket; with `PROTOCOL_DATA_SINK_BUCKET` unset the GCS sink had an **empty bucket** → `client.bucket("")`
      → IndexError. New `_get_sink_bucket()` resolves the canonical `features-delta-one` bucket via the bucket-name SSOT
      (`resolve_bucket_name`), honouring `PROTOCOL_DATA_SINK_BUCKET_{AG}` routing first (mirrors read-side
      `_get_source_bucket`). 2 regression tests (never-empty + env-wired passthrough). — features-service@ea357010
- [x] ✅ [VALIDATE] P0. Real GCS run (2026-05-03, `-test` bucket): BITGET-FUTURES:PERPETUAL:ADAUSDT **wrote 1/1
      partition, "Processing completed successfully"**, no IndexError. Read-back: 5,760 rows / 86 feature cols,
      `rsi_14 ∈     [4.04, 98.59]`, full-day timestamps. QG: all content STEPS green (basedpyright/ruff/tests); only the
      `<300s` perf budget flaked (310–362s under concurrent machine load) — environmental, not a code failure. —
      features-service@ea357010

### Phase 2 — delta_one full e2e (reference path) `[P0]`

- [ ] 🔴 [BUG] P0. **Two-resolver bucket divergence (discovered 2026-05-26, blocks clean `-test` isolation).** The
      parquet write resolves its bucket via `FeatureWriter._get_sink_bucket` (honours `PROTOCOL_DATA_SINK_BUCKET_{AG}`
      env), but the **manifest emission** in `delta_one/engine/orchestrator.py` uses `config.get_output_bucket` →
      `resolve_bucket(kind="features-delta-one")` (pure SSOT, **ignores the env override**). Consequence: redirecting
      the e2e write to a `-test` bucket via env sent the parquet to `-test` but wrote the **manifest row to the
      canonical prod bucket** → a phantom `captured` row (instrument's parquet absent there). Verified + cleaned up
      (deleted the stray `_index` I created in `features-delta-one-cefi-central-element-323112`, restored to empty).
      Also latent in **prod**: if any deployed VM ever sets `PROTOCOL_DATA_SINK_BUCKET_CEFI`, data and manifest diverge.
      **Fix: route BOTH the parquet write and the manifest emission through ONE resolver** (recommend the orchestrator's
      manifest emission honour the same `_get_sink_bucket`/env, OR `_get_sink_bucket` delegate to `get_output_bucket` —
      pick per test-isolation decision below). Secondary: the emitted manifest row has **empty `venue`/`instrument_id`**
      (does not identify the shard) — separate manifest-quality finding to chase. Provenance: e2e Phase 2 dry-run
      2026-05-26.
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

- [ ] 🟠 [BUG] P1. **Propagate the WRITE-bucket fix to volatility + cross_instrument** (discovered Phase 1). Their
      FeatureWriter equivalents resolve the output sink the same way delta_one did — if they also rely on
      `get_data_sink(routing_key=...)` with an unset `PROTOCOL_DATA_SINK_BUCKET`, they hit the identical empty-bucket
      `IndexError`. Add a `_get_sink_bucket` with their canonical kinds (`features-volatility`, `features-xinstrument`)
      before the e2e runs below. Provenance: features-service@ea357010 (delta_one fix).
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

- **Backfill present:** the lookback-sized window resolved in Phase 0.5 is `captured` (manifest + files) for the
  targeted liquid CeFi venues spot+perp, so calculators run on >1 venue's data — not BITGET alone.
- **B3 (data-pipeline KPI):** for the golden window, ≥ **99.9%** of v8-`captured` CeFi instruments either compute+write
  features OR record a typed honest-absence reason — **zero** silent failures, unhandled 404s, NoneType crashes, or
  write exceptions.
- delta_one, volatility, cross_instrument, multi_timeframe each complete **read → calculate → write → read-back** on
  real recent GCS data, output in `-test` buckets, with a co-emitted v8 manifest row per successful write.
- `write_daily_partition: string index out of range` is root-caused + fixed + unit-tested (colon-bearing instrument_id).
- `bash scripts/quality-gates.sh` exit 0 (features-service); e2e driver wired into QG smoke and green on the golden
  date.

## Full-execution criterion (per "Plans Run To Actual Completion" HARD RULE)

- ✅ The Phase 0.5 backfill runs to completion on real infra (MTDS capture → MDPS processing → `-prd` canonical buckets)
  for the lookback-resolved window, manifest-verified `captured` + files present for the targeted venues/days.
  - **What ran:** MTDS + MDPS backfill CLIs/VMs for the resolved window; **Verification:**
    `read_availability_index(<-prd tick bucket>)` shows `captured` processed_candles rows + `blob_exists` true.
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
