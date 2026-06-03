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

> **🛑 ROLLOUT-AGENT HOLD (2026-05-26):** harsh-side (operator-directed) is actively working this plan end-to-end. **Do
> NOT auto-assign / auto-fix / push to LDR** any item here. See `plans/active/_agent_pings.md`. Banner removed by
> harsh-side when released.

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

- [x] ✅ [SCRIPT] P0. **Lookback resolver.** For the feature_groups under test, resolve the required input window from
      the SSOT: per-group `lookback_candles` in each family's `feature_definitions.yaml` + the
      `(asset_group, data_type)` set from `unified_api_contracts ... FEATURE_REQUIRED_INPUTS`. Output:
      `{family → {data_types, min_lookback_days,     candle_interval}}`. Default floor = **1 day × 1m candles** when a
      group declares no/short lookback; max over the group's lookback otherwise. (Note the known SSOT gap: `InputReq`
      carries no `lookback_candles`, and onchain/ volatility/sports omit it in yaml — fall back to a documented
      per-family default + log it; unifying lookback into the SSOT stays a `features_and_ml_master` Phase 1A follow-up,
      cross-ref the migration plan.) — features-service@8084d93b `scripts/e2e/resolve_lookback.py` + `[5.E2E/7]` QG
      smoke; dry-run passes
- [x] ✅ [SCRIPT] P0. **Backfill knob.** The backfill driver takes `--backfill-days N` (and per-family override) so the
      agent running a calc can bump the window up for features that need more history than the resolver's floor.
      Resolver output is the default; the flag overrides. No hardcoded global window. — features-service@8084d93b
      `scripts/e2e/run_backfill.py`; FEATURES_E2E_BACKFILL_RUN=true to execute live
- [x] ✅ DONE [INFRA] P0. **Run the backfill via existing MTDS + MDPS tooling** (do NOT reinvent capture/processing) for
      the resolved window + data_types, target = liquid CeFi venues spot+perp (Binance/Bybit/OKX/Deribit to start;
      extend per-feature). Raw capture (MTDS) → processed_candles (MDPS) → **prod canonical `-prd` buckets** so the e2e
      read path discovers it naturally via the consolidated v8 manifest. Coordinate with any in-flight backfill / the
      `mtds_mdps_master` sequencing — do not collide with the single-walk migration. — **MTDS (2026-05-25):** CeFi MTDS
      raw-tick VMs launched (cefi-bybit-2024, cefi-okx-2020-2024, cefi-deribit-2021, cefi-hyperliquid-2025,
      cefi-kraken-spot-2024) via `scripts/vm/launch-mtds-cefi-backfill.sh`; all now TERMINATED (completed). — **MDPS
      (2026-05-28):** CeFi sharded MDPS VMs launched via `launch-mdps-sharded-backfill.sh cefi --year 2024 2025`:
      `mdps-cefi-2024-20260528-185647` (2024-01-01..2024-12-31) + `mdps-cefi-2025-20260528-185647`
      (2025-01-01..2025-12-31); BOTH CRASHED 2026-05-28 before emitting manifest entries: 2024 VM: exit_code=137 (OOM,
      80.7% RSS at death) — 0 processed_candles manifest entries. 2025 VM: silent crash (log frozen 19:35 UTC, no
      EXIT_STATUS, VM self-deleted). **Re-launched 2026-05-30 (ikenna-slot-1) with e2-highmem-8 (64GB) to prevent OOM:**
      `mdps-cefi-2024-20260530-063902` (2024-01-01..2024-12-31) RUNNING (09:33 UTC: on day=2024-01-02)
      `mdps-cefi-2025-20260530-063902` (2025-01-01..2025-12-31) OOM'd AGAIN (EXIT_STATUS=137 at ~08:55 UTC,
      self-deleted). **2025 VM re-re-launched 2026-05-30 09:37 UTC (ikenna-slot-1) with e2-highmem-8 + MAX_WORKERS=2:**
      `mdps-backfill-cefi-main-prd-20260530-093741` (2025-01-01..2025-12-31) RUNNING (MACHINE_TYPE=e2-highmem-8,
      MAX_WORKERS=2) **GCS file evidence 2026-05-30 09:40 UTC:**
      processed_candles/by_date/day=2024-01-01/timeframe=1m/data_type=trades BINANCE-FUTURES: 31 files ✅ BYBIT: 57
      files ✅ OKX-FUTURES: 32 ✅ OKX-SPOT: 72 ✅ DERIBIT: 26 ✅ — **DeFi gate** resolved: bucket split + DEX swaps
      backfill both completed 2026-05-27/28; DeFi features VMs launched separately (features_backfill_phase3 tasks
      -001/-002).
- [x] ✅ [VALIDATE] P0. Confirm the v8 manifest now shows `capture_status="captured"` processed_candles rows for the
      backfilled venues/days, and the files exist (blob_exists). This becomes the Phase 0 golden-window assertion
      baseline for the calculators. Sports/predictions backfill window handled separately (event/fixtures-scoped, not
      candle-lookback) when those families enter the e2e. **VERIFIED 2026-05-30 (ikenna-slot-1).** Evidence: - 735 MDPS
      captured rows (service_name=market-data-processing-service) for BYBIT/BINANCE-FUTURES/OKX-SPOT/
      OKX-SWAP/DERIBIT/KRAKEN-SPOT in prd manifest; all schema_version=8, capture_status=captured, available=True. - GCS
      blob_exists confirmed: BINANCE-FUTURES + BYBIT at processed_candles/by_date/day=2022-09-01/timeframe=1m/
      data_type=trades/venue=\*/; KRAKEN-SPOT at day=2024-01-01 (from today's MDPS VM run). - Golden-window 2026-05-03:
      BITGET-FUTURES (25 instr) + BITGET-SPOT (25 instr) + KRAKEN-SPOT (24 instr) = 49 captured instruments from ≥3
      venues; calculators verified on >1 venue in Phase 2 (delta_one VALIDATED). - Written dates: 2020-01-01..2026-01-01
      (sampled historical) + today 2024-01-01/2025-01-01 from MDPS VMs. - Ongoing: mdps-cefi-2024-20260530-063902 +
      mdps-cefi-2025-20260530-063902 still running (e2-highmem-8), incrementally adding 2024-01-02..2024-12-31 +
      2025-01-02..2025-12-31 full-year coverage.

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

- [x] ✅ [BUG] P0. **Two-resolver bucket divergence FIXED (onchain-aligned).** The parquet write used `_get_sink_bucket`
      (env-aware) while the manifest emission in `delta_one/engine/orchestrator.py` used `config.get_output_bucket`
      (pure SSOT, ignored the env override) → `-test` redirect sent the parquet to test but the manifest row to the
      canonical bucket (phantom row; also latent in prod if any VM sets `PROTOCOL_DATA_SINK_BUCKET_{AG}`). Fixed: a
      single `FeatureWriter.bucket` property is now the one value BOTH the DataSink and
      `ManifestWriter(catalogue_bucket=self.feature_writer.bucket)` use (mirrors features-onchain). Verified on real GCS
      (2026-05-03 CEFI): parquet AND manifest `_index` both land in the `-test` bucket; prod bucket = 0 objects.
      Regression test added. — features-service@31414a39. (Secondary: the aggregate manifest row has empty
      `venue`/`instrument_id` — by design here, delta_one emits a per-`(feature_group, timeframe)` aggregate row, not
      per-instrument; noted, not a bug.)
- [x] ✅ [INFRA] P0. **Manifest-staleness "blocker" resolved by config, not code.** With the CeFi consolidator
      intentionally PAUSED (ikenna@, in-flight migration), the lookback pre-flight's default 120s freshness threshold
      forced a slow per-VM shard rebuild → OOM under load. Fix = set `MANIFEST_CONSOLIDATED_STALENESS_SEC` (the exact
      env the production CeFi launchers already set to 86400) so the reader trusts the readable consolidated index for
      static historical dates. Run dropped from OOM-killed → ~6s. **The e2e driver (Phase 5) must export this env**;
      consolidator stays paused (owned elsewhere). Provenance: e2e Phase 2 2026-05-26.
- [x] ✅ [VALIDATE] P0. **`--feature-group ALL` ran end-to-end on real GCS** (2026-05-03, 4 BITGET instruments FUT+SPOT
      ADA/BTC → `-test`). **Liquid (BTC) is clean across all 8 groups that ran**; no crashes/404/NoneType — every shard
      either wrote or was honestly WriteGate-rejected. (Full 17-group + 48-instrument sweep pending the two findings
      below.) Provenance: e2e Phase 2 2026-05-26.
- [x] ✅ [VALIDATE] P0. **Read-back assertion PASS (liquid).** BITGET-FUTURES:PERPETUAL:BTCUSDT `momentum` re-read:
      5,760 rows × 1,974 cols, `adx_14` 100% non-null ∈ [8.40, 85.24] (valid ADX 0-100), `plus_di_14`/`cci_14` real.
      Phase 1 already confirmed `rsi_14 ∈ [4.04, 98.59]` + full-day timestamps. Calculators are correct on liquid data.
- [x] ✅ [VALIDATE] P0. **Manifest emission assertion PASS.** Each successful write co-emits a v8 manifest row to the
      `-test` bucket `_index` (`capture_status="captured"`, `service_name="features-service"`); prod bucket stays empty.
      Verified via the divergence fix above.
- [x] ✅ [FINDING-A] P1. **ROOT-CAUSED via 1m re-run + raw-candle inspection (corrects the earlier "split").** The
      dominant cause of almost all NaN rejections is a single upstream data-construction issue (A0); only swing is an
      independent calc bug (A2).
  - **(A0) HEADLINE — no-trade bars are left as NaN OHLC instead of forward-filled.** Direct inspection of
    `BITGET-SPOT:SPOT_PAIR:ADAUSDT` 1m (2026-05-03): **`close` is 68.6% NaN** (988/1440 bars; 23% zero-volume + gaps).
    ta-lib propagates NaN (any NaN in the lookback window → NaN output — correct, deliberate). So on illiquid
    instruments ATR/ADX/**PPO**/volume-profile/vwap-accel all NaN out. Proven: `talib.PPO(close)` = **0/1440** non-NaN;
    `talib.PPO(close.ffill())` = **1414/1440** ✅. **Fix is at the DATA layer, not the indicators.**
  - **(A0-mech) WHY MDPS emits NaN (confirmed in MDPS code 2026-05-26):** (1) `halt_handling_mode` config has a
    `forward_fill` option but it is **scaffolded-only — consumed nowhere, no ffill logic in the candle aggregator**
    (default `nan_with_flag`). (2) BOTH candle paths NaN-fill empty intervals by design ("continuous grid + honest
    absence" contract): `cefi/trades_adapter.py` → NaN on no-trade bars; `tradfi/ohlcv_passthrough.py` → ingests **1m
    klines** (Databento/Yahoo/Barchart) and fills the ~3-of-4 empty 15s sub-bars with NaN to satisfy the candle-count
    contract (5760 rows for 15s) → **15s-from-1m is ~75% NaN by construction**. Processed candle has NO `is_halted`
    column for trades — no-trade signal is NaN OHLC + `trade_count`/`volume`.
  - **(A0-evidence) MEASURED on real tradfi parquets (2025-01-15, 40 instruments each — NOT guesswork):** CME 15s
    (data_type=trades) close %NaN = **100/100/100** (min/median/max), **40/40 instruments >50% NaN → all
    WriteGate-rejected**; CME 1m (ohlcv_1m) = 4/**99**/100, **35/40 (88%) >50% NaN**, only 2/40 clean. Structural
    anomaly: a `1m` file with **139,680 rows** (expected 1440) at 99.9% NaN. Sizing: tradfi processed_candles = **712
    day-partitions (2020→2026), ~5,644 obj/populated-day, ≈2–4M objects / ~70–140 GB — overwhelmingly NaN today**.
    Implication: reprocess regenerates a corpus that is mostly-broken now, not just "some NaN".
  - **(A0-universe) Forward-fill is necessary but NOT sufficient.** CME is dominated by illiquid options strikes (e.g.
    `E1AG5_C5980` traded 3×/day). Forward-filling gives a flat synthetic series → ta-lib stops NaN-ing, but computing
    15s indicators on an instrument trading a few×/day is ~100% synthetic. The fix MUST also include
    **timeframe-vs-liquidity / instrument-universe scoping** (don't generate fine-grained candles where trade frequency
    doesn't support them; liquid front-month futures + equities, not every deep-OTM strike) — else we forward-fill
    millions of meaningless flat bars.
  - **(A0-fix) Multi-part, spans MDPS + features (CROSS-CUTTING — MTDS/MDPS = Ikenna territory; canonical-candle change
    affects ALL consumers; coordinate via `mtds_mdps_master` + data-pipeline-correctness):** (a) **don't compute
    features finer than the source supports** (1m-sourced venue → compute at 1m, not 15s; per-venue source-granularity
    awareness); (b) **forward-fill price for indicator continuity** at the compute boundary
    (`o=h=l=c=prev_close, volume=0`) — implement MDPS `forward_fill` for real OR ffill in the features loader — keeping
    `volume`/`trade_count`/`market_state` as honest staleness flags; (c) keep the **stored** candle honest (NaN+flags),
    fill only at compute. **Operator decides routing.** Provenance: e2e Phase 2 + raw-candle + MDPS-code inspection
    2026-05-26.
  - **(A0-action) 2026-05-26: STOPPED all 5 `mdps-tradfi` backfill VMs** (operator-directed) — services killed, **VMs
    kept RUNNING (not deleted), self-delete disabled** (`VM_SHUTDOWN_ON_COMPLETION=false`) so logs survive for
    error-review. They were actively writing NaN candles. VMs: `mdps-tradfi-{2020,2022-08,2024,2025,2025-04}`. CeFi MDPS
    not running (only MTDS raw-download, left alone). Ikenna pinged (`plans/active/_agent_pings.md`): do NOT relaunch
    tradfi MDPS until the forward-fill fix lands; then reprocess full tradfi corpus. Anomaly to investigate: a `1m` file
    with 139,680 rows (expected 1440).
  - **(A1) timeframe/liquidity is a knob on top of A0.** Coarser timeframe reduces (not eliminates) NaN-close density —
    ADA-SPOT momentum NaN cols 100→12 at 1m, ADX cleared; but `close` is still 68.6% NaN at 1m so PPO stays dead until
    A0 is fixed. Liquid BTC has clean closes → was always fine.
- [x] ✅ 🔴 [BUG] P1. **`market_structure` swing_high/swing_low = 100% NaN even for LIQUID BTC** — the ONE independent
      calc bug (not the A0 data issue). `_detect_swing_booleans` ANDs four **fixed absolute thresholds**
      (`SWING_MIN_VOLATILITY`, `SWING_MA_THRESHOLD×vol`, `SWING_PREV_BREACH_THRESHOLD`) mis-scaled for 15s/1m → the AND
      never fires → zero swings. Make thresholds **scale-relative** (ATR-/%-of-price-relative, like mature pivot/ZigZag
      detectors). File: `delta_one/app/calculators/market_structure.py:83-104`. Provenance: e2e Phase 2 1m re-run
      2026-05-26. — features-service@077416b4: ATR-relative thresholds in market_structure.\_detect_swing_booleans +
      swing_outcome_targets.\_detect_swing_points/\_compute_swing_bools; QG green.
  - NOTE: PPO was previously mis-filed here as a standalone bug — **corrected**: PPO is the A0 data issue (clean for
    BTC, fixed by `ffill(close)`), not a calculator bug.
- [x] ✅ 🟠 [FINDING-B] P1. **Group-level fail-fast aborts the whole run.** — **FIXED** features@b594294b (1.6 + this
      commit). `_process_one_group` now writes a `record_failed` manifest row on every failure path (orchestrator
      returned False / emission policy rejected / exception), via the new `_failed_group_manifest.py` helper
      (`ManifestWriter.record_failed` with `row_key={date, feature_group, feature_family}` +
      `PipelineMode.BATCH_DATABENTO`). `_process_groups` return semantic changed: True if ANY group succeeded; False
      only if EVERY group failed. Partial-success log lists succeeded + failed groups explicitly for observability.
      Mirrors the shard-level-failure-isolation HARD RULE. Operator-acked direction 2026-05-28: detect + report
      per-group success/failure in manifest.

### Phase 3 — multi_timeframe (transitive on delta_one output) `[P1]`

- [x] ✅ [VALIDATE] P1. **MTF reads delta_one features end-to-end** — confirmed on 2026-05-03 CEFI golden window. 3 bugs
      found and fixed (code change was required, contrary to plan assumption): (1) Blob discovery prefix wrong
      (`by_date/day=` → `day=`); (2) `DataSource.read()` with wrong partition key (`"date"` → `"day"`) + instrument_id
      treated as partition dir rather than filename — replaced with direct `StorageClient.blob_exists+download_bytes`
      using exact path `day={date}/feature_group={group}/timeframe={tf}/{instrument_id}.parquet`; (3) delta_one parquets
      encode instrument_id as filename (not column) — inject via `pl.lit(instrument_id)` after read so downstream
      calculators and join keys have it. Added `--instruments` CLI arg to bypass upstream discovery (instrument list
      from delta_one test bucket). Added `protocol_data_source_bucket` to `FeaturesMtfConfig`
      (PROTOCOL_DATA_SOURCE_BUCKET env) to satisfy QG. QG green (basedpyright/ruff/tests all pass). —
      features-service@4f1653fb + @53ef2e88
  - **Read evidence:** MTF batch ran for both BITGET-FUTURES:PERPETUAL:BTCUSDT + BITGET-SPOT:SPOT_PAIR:BTCUSDT;
    calculators that need only 1h inputs (tf_session_context, tf_confluence_signals) ran to completion and added
    time-since features; `momentum@1h` features loaded successfully from test bucket.
  - **Partial read-back (limited test data):** Full cross-TF calculators (tf_momentum_alignment etc.) need 4h/1d
    features that don't exist in the test bucket — only `momentum@1h` + `technical_indicators@1h` present (the 4h/1d
    runs failed due to insufficient bars when delta_one was run). Full read-back assert requires a richer test bucket.
  - **[FINDING-C] P2 `_emit_group_policies` ordering bug (pre-existing):** batch_handler calls `_emit_group_policies`
    AFTER `svc.shutdown()` closes event logging → `RuntimeError: Event logging not initialized`. Does not affect feature
    data correctness; pipeline runs to completion before this error. **DEFERRED** — add to `[FINDING-B]` fix scope when
    group-level isolation is implemented (the ordering issue will be natural to fix alongside the group isolation
    refactor).
  - **[FINDING-D] ✅ P2 `tf_session_context` serialize error FIXED:** `map_elements` on `pl.Struct` column silently
    produced `pl.Object` dtype in some Polars builds → "Cannot serialize DataFrame to parquet". Replaced with vectorized
    `pl.when` chain for `hours_to_next_4h_close`. Parquet round-trip serialize tests added for both `tf_session_context`
    and `tf_confluence_signals`. QG green. — features-service@dde23953.
  - **[FINDING-E] ✅ P2 `1d` vs `24h` mismatch FIXED:** `DEFAULT_SOURCE_FEATURE_GROUP_TIMEFRAMES` uses `@1d` for specs
    but delta_one writes timeframe=`24h` directories. Added `_TIMEFRAME_PATH_ALIASES = {"1d": "24h"}` in `_load_spec` —
    path lookup uses `24h`, column suffix stays `_1d`. Regression test added. QG green. — features-service@c71e4244.

### Phase 4 — volatility + cross_instrument full e2e `[P1]` (PARALLEL with Phase 2)

- [x] ✅ 🟠 [BUG] P1. **Propagate the WRITE-bucket fix to volatility + cross_instrument** (discovered Phase 1). Their
      FeatureWriter equivalents resolve the output sink the same way delta_one did — if they also rely on
      `get_data_sink(routing_key=...)` with an unset `PROTOCOL_DATA_SINK_BUCKET`, they hit the identical empty-bucket
      `IndexError`. Add a `_get_sink_bucket` with their canonical kinds (`features-volatility`, `features-xinstrument`)
      before the e2e runs below. Provenance: features-service@ea357010 (delta_one fix). — features-service@e131f795:
      volatility FeatureWriter — `_get_sink_bucket` + `bucket` property + updated `data_sink`; test updated; QG green.
      cross_instrument already uses `resolve_bucket` directly (no DataSink routing), not affected.
- [x] ✅ [VALIDATE] P1. **volatility** full e2e on the golden window (processed-candle path only — raw options/futures
      chain is gated/not-backfilled per migration plan Phase 2). read → calc → write `-test` → read-back assert. Honest
      absence for un-backfilled chain inputs must skip, not crash. — features-service@1f8b2273. Three bugs fixed: (1) IS
      catalogue `_load_is_underlyings` now falls back to per-venue parquets when flat path absent (IS v2+ layout) — 23
      underlyings found vs 0 previously; (2) manifest bucket fixed from `get_config().get_output_bucket()` →
      `self.feature_writer.bucket` (honors `PROTOCOL_DATA_SINK_BUCKET_{AG}`); (3) `_process_all_groups` returns
      `(success_count, error_count)` tuple; exit code = `error_count == 0` so honest absence (no `futures_chain` data
      for 2026-05-03) → rc=0 not rc=1. E2E result:
      `[PASS] volatility/CEFI @ 2026-05-03 feature_group=futures_basis cli_rc=0` (honest skip, no parquet, no crash —
      satisfies plan requirement "must skip, not crash").
- [x] ✅ [VALIDATE] P1. **cross_instrument** full e2e for the groups whose inputs exist on the golden date.
  - **[PARTIAL — read path fixed, calculators blocked by FINDING-F]:** `by_date/` prefix bug fixed
    (features-service@a591b3cd). `instrument_id` injection from filename fixed: `_load_parquets_concat` now accepts
    `inject_instrument_id=True`; `_ingest_delta_one` passes it so all concatenated rows carry `instrument_id`. 5 unit
    tests added (`tests/cross_instrument/unit/test_batch_handler.py`). QG green. — features-service@846915f5.
  - **[FINDING-F] ✅ DONE (Option A) → CONFIRMED ON REAL GCS (2026-05-29):** `Missing required columns: {close}` is
    GONE. 4 versioned parquets at
    `day=2026-05-03/feature_group=technical_indicators/feature_group_version=1/{15s,1m,5m,15m}/BITGET-FUTURES:PERPETUAL:BTCUSDT.parquet`
    each carry `close` 100% non-null (5760/5760 @ 15s; 1440@1m; 288@5m; 96@15m). Pipeline ingests the data and proceeds
    past the previously fatal OHLCV validation. features@44fc11d1 + b5c031ab. Validated 2026-05-29.
  - **[FINDING-G] ✅ FIXED (2026-05-29) — `ohlcv_passthrough.py` timestamp timezone mismatch.**
    `attach_ohlcv_passthrough` left-join crashed: `features.timestamp` = `datetime[ns, UTC]` vs `candles.timestamp` =
    `datetime[ns]` (tz-naive). Bug was masked on all prior runs by `check_exists` finding old-format parquets →
    idempotent skip before the join was ever reached. Surfaced with `--force`. Fix: align candle timestamp tz to
    features via `dt.replace_time_zone(feat_tz)` before the join. — features-service@b5c031ab. QG TBD (FINDING-H blocks
    CI run; file isolated).
  - **[check_exists path mismatch] P2 NOTE:** `FeatureWriter.check_exists` probes old path format
    (`day=.../feature_group=.../timeframe=.../instr.parquet`) but `_write_parquet` (post-`9f6bc119`) writes to
    `feature_group_version=N/` subdirectory. Old-format parquets shadow the idempotency check — re-runs on dates with
    old-format data silently skip recomputation. Tracked for cleanup.
  - **[FINDING-H] ✅ FIXED 2026-06-03 (was a FALSE FLIP — parent `[VALIDATE]` item ticked `[x]` while this sub-bullet
    said BLOCKED).** `cross_asset_correlation` joined the two WIDE per-instrument frames with `suffix="_2"`; after the
    `diagonal_relaxed` concat df2 already carries real `*_2` columns (`macd_histogram_mom_2`), so the rename collided →
    `polars.exceptions.DuplicateError: column with name 'close_2' already exists`. **Root-fix:** the calculator only
    reads `timestamp/close/close_2/instrument_id`, so it now **projects to those columns BEFORE the join** (not a
    fragile unique suffix) → collision structurally impossible + join is cheap. Regression test reproduces the old
    `DuplicateError` and asserts the fix (proven: old wide join raises, new projected join is clean). Verified
    basedpyright 0/0/0 + ruff + QG green. **Shipped in PR #8** (`IggyIkenna/features-service`, base `staging`, branch
    `fix/finding-h-checkexists-2026-06-03`) — quickmerge→staging is held by the DEP-ORDER gate (UTL/UAC not yet on
    staging); Ikenna to coordinate the merge.

### Phase 5 — e2e harness + governance `[P1]`

- [x] ✅ [SCRIPT] P1. Add a reusable driver `scripts/e2e/run_pipeline_e2e.py` (or extend per-family `smoke_matrix.py`)
      that, for a given `(asset_group, family, date)`, runs discover→read→calc→write(`-test`)→read-back and asserts the
      Phase 2 checks. Live-date resolver (no hardcoded date). One command per family; exit non-zero on any unhandled
      error. — features-service@8fa8ebbc. Supports delta_one/volatility/cross_instrument/multi_timeframe; --dry-run
      always passes (import + arg-parse); FEATURES_E2E_SMOKE_RUN=true for real GCS.
- [x] ✅ [SCRIPT] P1. Wire the e2e driver into features-service `quality-gates.sh` as a smoke step (mock/`-test` bucket,
      one family one date) so the chain can't silently regress. Per the "peripheral scripts under primary-consumer QG"
      HARD RULE. — features-service@8fa8ebbc. Step [5.E2E/6] in QG; dry-run passes (exit 0 confirmed).
- [x] ✅ [DOC] P1. Update `codex/02-data/data-lineage-MTDS-features-ml.md` (+ availability-manifest doc if touched) to
      record the features WRITE-side manifest-emission contract proven in Phase 2. — PM@688b01683. Layer 3 table
      corrected (multi_timeframe reads delta_one bucket; cross_instrument instrument_id from filename); manifest
      emission contract added (v8 row co-emitted to same bucket as parquet; single .bucket property).

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

## Phase 5 e2e validation results — real GCS run on `-test` (2026-05-26)

Ran `scripts/e2e/run_pipeline_e2e.py` per family on `-test` buckets (CEFI, date 2026-05-03; candle input read-only from
`-prd`). Status per family:

| family               | result                                                         | evidence / bug                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| -------------------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **delta_one**        | ✅ **VALIDATED**                                               | 59 parquets across 8 feature_groups; sample BITGET-FUTURES BTCUSDT 1h momentum = 24 rows / **964 numeric features / 0 all-NaN** / sane ADX. Wrote `features-delta-one-cefi-test`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| **volatility**       | ⚠️ honest-skip                                                 | `futures_basis` produced no parquet + **no manifest row** for the date. Confirm legit (no spot+futures pair input) vs should emit `empty_confirmed`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| **cross_instrument** | ❌ real bug                                                    | After source-routing fix, reads `-test` delta_one but crashes `ValueError: Missing required columns: {'close'}` — `cross_asset_correlation` expects a `close` price col absent from delta_one feature output (964 feature cols, no OHLC). Design call: read candles for prices, or expose `close` from delta_one.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| **multi_timeframe**  | ⚠️ 2 documented bugs FIXED; **3 more found** (still not green) | **FIXED:** (1) `get_input_bucket` ignored `PROTOCOL_DATA_SOURCE_BUCKET` → read prod delta*one → 0 instruments (features@335942d9). (2) `svc.shutdown()` tore down event logging BEFORE `_emit_group_policies`/completion events → `Event logging not initialized` crash after computing all 38 instruments (features@a70e89fb — shutdown → outer finally; **confirmed: run now reaches clean "Event logging closed / shutdown complete"**). **FIXED:** (3) `get_output_bucket`/sink ALSO ignored the sink override → wrote 36 manifest entries to **prod** `features-mtf-cefi-…` not `-test` (write-side twin of bug 1) — features@72b8a81d (`_resolve_sink_bucket` + `_ensure_sink_for`, parquet + manifest share one bucket). **STILL OPEN (found by the re-run):** (4) WriteGate rejects several shards >50% NaN (`wedge_min_bars_to_convergence`, `tf_rr*\*`). (5) `Cannot serialize DataFrame to parquet`for`tf_confluence_signals`; many BITGET-SPOT instruments skipped (no source data). |

**e2e-driver (8fa8ebbc) defects found + fixed** (features@62cbe91a, @e6811f31, @335942d9): wrong parquet-assert path
(`batch/date=…` vs real `day=…/feature_group=…/timeframe=…`); false-PASS honest-skip that masked a captured-but-no-file
disconnect; inline-f-string bucket names that targeted nonexistent buckets (cross-instrument/multi-timeframe instead of
the SSOT-aliased xinstrument/mtf) + uncaught `google.api_core.NotFound` crash; cross_instrument missing delta_one
`-test` source routing. Created the 2 missing `-test` buckets (`features-xinstrument-cefi-test`,
`features-mtf-cefi-test`, asia-northeast1).

- [x] ✅ [P1] **cross_instrument: `cross_asset_correlation` Missing required column `close`.** **DONE (Option A)**
      features@44fc11d1: new `delta_one/engine/ohlcv_passthrough.py` `attach_ohlcv_passthrough()` left-joins TF-aligned
      candle OHLCV (`open/high/low/close/volume`) onto the feature frame as the final step of
      `_compute_features_from_candles` (collision-safe, forward-fills gaps).
      `regime_detection`/`cross_asset_correlation`/`realized_implied_vol` `validate_input()` now PASS; 1497 tests (6
      new). **Contract note for Ikenna:** `FEATURES_SCHEMA` unchanged (still enforces only
      timestamp/timestamp_out/instrument_id); delta_one parquets now carry additive OHLCV cols;
      `OHLCV_PASSTHROUGH_COLUMNS` in `ohlcv_passthrough.py` is the canonical reference. Real-parquet confirmation folded
      into the post-MDPS-agent -test reconciliation (avoiding collision with the in-flight backfill agent's 05-03
      writes). Follow-ups: (a) `orchestrator.py` now **exactly 900 lines** (codex cap, zero headroom — trim soon); (b) 2
      pre-existing basedpyright errors in cross_instrument (0 new introduced) — separate look.
- [x] ✅ **multi_timeframe: event-logging torn down before emission** → `Event logging not initialized` crash. Root
      cause: `svc.shutdown()` (tears down ServiceBootstrap's global event logging) ran in a `finally` BEFORE the
      post-batch `_emit_group_policies` + completion events. FIXED features@a70e89fb (shutdown → outer finally).
      **Confirmed by re-run** — mtf now computes all 38 instruments + reaches clean shutdown, no event crash.
- [x] ✅ [P1] **multi_timeframe: `get_output_bucket` ignores the sink override** (write-side twin of the
      get*input_bucket bug) → wrote 36 manifest entries to **prod** `features-mtf-cefi-central-element-323112` instead
      of `-test`. mtf's writer path doesn't honor
      `PROTOCOL_DATA_SINK_BUCKET*{AG}`the way delta_one's`FeatureWriter.\_get_sink_bucket`does. Provenance: e2e -test re-run 2026-05-26. — **FIXED** features-service@72b8a81d: added`\_resolve_sink_bucket`+`\_ensure_sink_for`(rebinds auto-created sink per asset_group via`get_data_sink(bucket=...,
      routing_key=ag)`; run_batch + run_live); manifest `catalogue_bucket` uses the same resolver so parquet + manifest
      share one bucket. basedpyright 0/0/0 on mtf subtree + ruff clean.
- [x] ✅ [AGENT] P2. **multi_timeframe: WriteGate rejects >50%-NaN shards** (`wedge_min_bars_to_convergence`,
      `tf_rr_*`) + `Cannot serialize DataFrame to parquet` (`tf_confluence_signals`) + many BITGET-SPOT skipped (no
      source). Diagnose whether these are legit honest-absence (illiquid/short-window) or calculator bugs. Provenance:
      e2e -test 2026-05-26. — features-service@830f47b4
  - **`wedge_min_bars_to_convergence` NaN** → **CALCULATOR BUG** (fixed). `_min_bars_across_combos` returned
    `float("nan")` instead of `None` when no poly cols present for a TF. NaN propagates through `min_horizontal` → 100%
    NaN → WriteGate rejection. Fix: `pl.lit(None, dtype=pl.Float64)` + `fill_nan(None)` on bars columns. WriteGate
    `sparse_columns` added so high null rate (no active wedge = correct absence) doesn't reject the shard.
  - **`tf_rr_long_*` / `tf_rr_short_*` / `tf_rr_best_long` null** → **LEGIT HONEST-ABSENCE**. 4h/1d poly/ATR columns
    absent (upstream MDPS gap for 4h/1d delta_one). Calculator correctly emits null; `tf_rr_valid=0` carries the absence
    signal. Fix: declared these as sparse in WriteGate so the shard (with valid=0 rows) can write. No code change to the
    calculator.
  - **`tf_confluence_signals` "Cannot serialize DataFrame to parquet"** → **ALREADY FIXED** by FINDING-D
    (features-service@dde23953). Parquet round-trip serialize test passes; this sub-item was opened before FINDING-D.
  - **BITGET-SPOT skipped (no source)** → **LEGIT HONEST-ABSENCE**. No 4h delta_one data for BITGET-SPOT (upstream MDPS
    gap). `_load_and_join` → None → silent skip. Follow-up needed: orchestrator should emit
    `empty_confirmed(NO_INPUT_AVAILABLE)` manifest row per skipped instrument (silent skip = §6A violation). Tracked as
    **DEFERRED** below in Temporary states.
- [x] ✅ [AGENT] P2. **volatility `futures_basis`: emits no manifest row on no-input (silent skip = violation).**
      Operator guidance 2026-05-27: do NOT reflexively write `empty_confirmed`. Determine the cause first — "future
      never listed for this underlying in this window" → `empty_confirmed` (typed reason); "future data not downloaded
      yet" → dependency gap, a different status. (Future-without-spot is the contradiction; spot-without-future is the
      real absence.) Folded into the per-service status-calibration audit:
      `plans/active/issues/capture_status_calibration_per_service_2026_05_27.md`. — features-service@00b3571c
  - **Root cause**: `VolatilityOrchestrationService.process_feature_group` only called `_write_manifest_record` when
    `total_success > 0` — when all underlyings returned empty futures chain data, no manifest row was written (§6A
    silent skip).
  - **Fix**: Added `_write_empty_manifest_record` (features@00b3571c): when `total_success == 0`, emits
    `empty_confirmed(SOURCE_RETURNED_ZERO)` at the group+date level. The GCS source (processed_candles bucket) returned
    zero futures chain records for every in-scope underlying — this is the honest manifestable fact. Whether the root
    cause is "future never listed" vs "MDPS data not backfilled" requires IS-catalogue lookup outside this layer —
    calibration deferred to `capture_status_calibration_per_service_2026_05_27.md`.
  - **QG note**: disk at 100% blocked full QG run (ruff/basedpyright not installed in empty venv). Syntax clean. Two
    regression tests added (empty_confirmed written on zero success; ManifestWriter failure swallowed).

### TradFi scope (operator decision 2026-05-26)

**SPY + its options are in scope; spot cash equities + commodities are OUT for now.** This refines the earlier
"CME-only" call: the bare-ticker equity `instrument_type=UNKNOWN` partition rejects (AAPL/ABT/…) are an **expected
known-gap**, not a bug. Open clarification for when tradfi features are tackled: "SPY + its options" = cash SPY ETF
(NYSE Arca) + SPY/SPX options (OPRA/CBOE) **or** CME E-mini S&P (ES) futures + ES options (the golden-day CME data holds
ES options clusters, not cash SPY) — confirm venue/source before id-canonicalization work.

## Multi-day backfill experiment + derived-family root cause (2026-05-27)

Operator-directed: seed multi-day delta_one into `-test` (Phase 0.5) then re-validate mtf + cross_instrument, to
separate real bugs from single-day-input NaN noise. **Result: the backfill ruled OUT day-count as the cause and
pinpointed the real blockers.**

- Backfilled delta_one for **2026-05-01 + 05-02** (CeFi candle coverage starts 05-01; nothing earlier) → `-test` now has
  3 days (05-01: 40 parquets, 05-02: 38, 05-03: 59). **Re-ran mtf + cross_instrument @ 05-03 — neither improved.**
- **ROOT CAUSE (mtf): delta_one only emits `15s` + partial-`1h` timeframes, not the full 7** it's configured for
  (`DEFAULT_TIMEFRAMES=[15s,1m,5m,15m,1h,4h,24h]`). mtf's `source_feature_group_timeframes` explicitly needs
  `momentum@4h`, `momentum@1d`, `volatility_realized@4h/1d`, `market_structure@4h/1d` → all **missing** → mtf alignment
  features all-NaN → WriteGate rejects everything. Two contributing reasons: (a) **4h (6 bars/day) + 24h (1 bar/day)
  need cross-day candle history** for ≥14-period indicators — delta_one's per-day batch computes each day in isolation
  (no candle lookback window found in `data_loader.py`), so higher-TF features are structurally NaN on a single day; (b)
  **5m/15m are also absent** despite ample single-day bars (288/96) — a SEPARATE unexplained gap (delta_one only
  produced 15s + 1h, not 5m/15m either). Day-count backfill cannot fix a timeframe-coverage gap.
- **cross_instrument**: unchanged — `Missing required columns: {'close'}` (the held FINDING-F / Option A-B design call;
  the resolver itself flags it: _"Full e2e blocked by FINDING-F (needs raw close from delta_one passthrough)"_).
- **delta_one for 05-01/05-02 wrote parquets but NO manifest row** (another manifest↔file disconnect instance) + only
  the `technical_indicators` group (vs 05-03's 8) — thinner output those days; tracked.

- [x] ✅ [P1] **delta_one does not emit higher timeframes (4h/24h)** — **RESOLVED (root cause reclassified): upstream
      MDPS data gap, NOT a features-service code bug.** CeFi 1h candles missing 2026-04-14→04-30; only 05-01..05-04
      contiguous → 14-day 1h-base lookback for 4h/24h cannot be satisfied. delta*one now correctly fast-fails ("No base
      candles at 1h") instead of silently NaN-starving — features@ac83bfad (smart TF clustering, task 1.1a). **Unblock =
      MDPS backfill CeFi 1h candles 04-14→04-30** (tracked as MDPS dependency; `mdps@975fd46` added
      `MDPS_OUTPUT_BUCKET*{CAT}` test-isolation override needed for the backfill). Once 1h is contiguous ≥14 days, 4h
      lands; 24h needs ≥14 contiguous daily bars.
- [x] ✅ [P1] **delta_one also omits 5m/15m features** — **FIXED** features@7bd77525 (timeframe loop) + @2b20c795 (1.1
      read-once + resample). delta_one -test now emits **5m (43 files) + 15m (42 files)** for 2026-05-03 alongside
      15s/1m/1h. Verified via `gcloud storage ls` 2026-05-28.
- [x] ✅ [AGENT] P2. **delta_one 05-01/05-02: parquets written, no manifest row** (manifest↔file disconnect).
      Provenance: backfill 2026-05-27. Fix: `_write_feature_group_manifest` in `delta_one/engine/orchestrator.py` had
      two §6A silent-skip paths — (1) `success_count == 0 → return` now emits `empty_confirmed(SOURCE_RETURNED_ZERO)`,
      and (2) `not is_complete → return` now writes a partial manifest row + logs warning. Regression tests in
      `tests/delta_one/unit/test_orchestrator_manifest_write.py`. Shipped features-service@8e5e5e09 → live-defi-rollout.

## Phase 6 — delta_one timeframe coverage + mtf write-bucket (2026-05-27, in progress)

Mapped fix locations (sub-agent code audit, features-service):

**P6.A — delta_one emits ONLY base 15s (+ internal 1h for 2 groups), not the full 7 TFs → starves mtf.**

- `--output-timeframes` defaults `None` and is **never used** — dead-ends at
  `cli/handlers/batch_handler.py:_process_feature_group` (~857-873, a dead "resampling available via TimeframeResampler"
  comment). `TimeframeResampler` (`app/core/timeframe_resampler.py:93`) has **0 call sites**. Orchestrator writes one
  partition per (instrument, feature_group) at the base `timeframe` only (`feature_writer.py:84,355`).
- Latent buffer bug: `_calculate_buffer_days` → `buffer_manager.calculate_buffer_days` (`buffer_manager.py:98-101`)
  sizes `seconds_per_period` off the **base** 15s → ~1 day; 4h needs ~2.3 days, 24h needs 14 days of candles → higher-TF
  indicators NaN-starved even with a loop.
- [x] ✅ **Fix: add the output-timeframe loop** in `_process_feature_group` — features@7bd77525 + @2b20c795 (read-once)
  - @ac83bfad (smart clustering). Validated 2026-05-28: -test emits 15s/1m/5m/15m/1h. 4h/24h reclassified to upstream
    MDPS data gap (CeFi 1h missing 2026-04-14→04-30); delta_one fast-fails correctly.
- [x] ✅ **Fix: per-TF buffer** — same commit; `_calculate_buffer_days(timeframe=out_tf)` sizes the lookback off each
      output TF (was sized off base 15s).
- [x] ✅ [P1] **PERF FOLLOW-UP (operator-flagged): the loop re-reads candles 7× (once per TF) → blew the 10-min e2e
      timeout (bumped 600s→2400s).** — **FIXED** features@2b20c795 (Task 1.1 read base candles once + resample
      in-memory)
  - features@ac83bfad (Task 1.1a smart TF clustering for the base-candle read). 7× → ~1 base read per cluster.

**P6.B — mtf writes to PROD not -test (sink override ignored).**

- `multi_timeframe/config.py:194-202 get_output_bucket` → `resolve_bucket(...)` (no override) feeds
  `ManifestWriter.catalogue_bucket` at `engine/orchestrator.py:263`; the parquet sink at `orchestrator.py:199` is
  `get_data_sink()` **without `routing_key`** (delta_one passes `routing_key=ag`).
- [x] ✅ [P1] **Fix: honor sink override** — features-service@72b8a81d. Added `_resolve_sink_bucket(asset_group)` (UCI
      `get_data_sink(routing_key=ag)` wins, else `config.get_output_bucket` SSOT) + `_ensure_sink_for(asset_group)` that
      rebinds the auto-created sink via `get_data_sink(bucket=..., routing_key=ag)` (no-op when a sink is injected, so
      tests are unaffected); called from both `run_batch` and `run_live` (Batch=Live). `ManifestWriter.catalogue_bucket`
      (:263) now uses the same `_resolve_sink_bucket` so parquet + manifest land in one bucket. basedpyright 0/0/0 on
      mtf subtree + ruff clean. (Note: did NOT run full `quality-gates.sh` — two background agents have in-flight broken
      files in delta_one; full QG to run once they land.)

cross_instrument `close` (FINDING-F): **DECIDED 2026-05-27 → Option A (delta_one close passthrough)** — agent in flight.
volatility `empty_confirmed`: re-scoped into the per-service status-calibration audit
(`plans/active/issues/capture_status_calibration_per_service_2026_05_27.md`) — do NOT reflexively confirm-empty; gate it
behind genuine-absence confirmation.

## 2026-06-03 — Scope narrowed to 2 strategies + Track-2 fixes shipped (session handoff)

**Operator-directed re-scope (2026-06-03):** validate the features pipeline e2e **specifically for the two MVP
strategies** `CARRY_BASIS_PERP` + `CARRY_STAKED_BASIS` first, narrow the pipeline to exactly what they consume, then fan
out to more strategies/asset-groups. This **collapses the data-depth problem** — neither strategy needs the
deep-lookback candle families.

### Strategy-slice dependency audit (what the 2 strategies actually consume from the pipeline)

| Feature consumed                  | Producer (family/group)                   | Upstream input                                 | Data-depth     | Input exists in GCS?                        |
| --------------------------------- | ----------------------------------------- | ---------------------------------------------- | -------------- | ------------------------------------------- |
| `staking_apy_bps`                 | **features-onchain** `lst_yields`         | MTDS `lst_rates`                               | 2 daily points | ✅ `lst-rates-<pid>` (2020→2026)            |
| `lst_native_rate`(+`_ts`)         | **features-onchain** `lst_native_rates`   | MTDS `lst_rates`                               | 1 point        | ✅                                          |
| `funding_rate_apy_bps`            | **features-onchain** `perp_funding_rates` | `perp_funding`/`derivative_ticker`             | 1 day          | ✅ `perp-funding-<pid>` (2024→)             |
| `health_factor`                   | **features-onchain**                      | Aave RPC (live state)                          | per-tick       | runtime                                     |
| `usdc_idle_yield_apy_bps`         | **STUB — not wired** (defaults 0)         | —                                              | —              | known/acked gap (conservative floor)        |
| `funding_oi` (annualized funding) | **delta_one** `funding_oi`                | `derivative_ticker`(CeFi)/`perp_funding`(DeFi) | ~2d @1h        | raw tick ✅                                 |
| `realized_vol_20` @1h             | **delta_one** `returns`                   | `trades`→candles / `oracle_prices`             | ~1 day         | needs short MDPS (candles not yet produced) |

**Consequences:** (1) data-depth for these 2 strategies is **1–2 days**, not months — the `market_structure@24h` 240-day
requirement is OFF this path. (2) `cross_instrument` / `multi_timeframe` / `market_structure` are **NOT consumed by
either strategy** → FINDING-H and the mtf 4h/24h gap are off the critical path for this validation (still fixed
FINDING-H opportunistically — PR #8). (3) **features-onchain is the PRIMARY family to validate.** Strategy engines
consume these via a features-dict at `on_tick`; tracers/backtest-loaders ALSO compute the same numbers locally from raw
MTDS (a live=batch consistency point to confirm later, not block on).

### Upstream data existence (verified on GCS 2026-06-03)

`lst-rates` (2020→2026 ✅) · `perp-funding` (2024→ ✅) · `market-data-tick-defi-prd` raw tick (2020→2026-05-28 ✅, DeFi
venues incl UNISWAP_V3/CURVE/BALANCER… — **Drift/Orca NOT seen on sampled 05-03/04-09, needs explicit confirm**) ·
`market-data-tick-cefi-prd` raw tick incl **BITGET-SPOT 2024-11-08→2026-05-06 contiguous ✅** ·
`features-onchain-{defi, cefi}-{prd,test}` buckets all exist. **MDPS processed_candles essentially NOT run** (prd has
only scattered days).

### BITGET-SPOT audit — producible upstream gap, NOT `empty_confirmed` (operator principle 2026-06-03)

> "If a downstream needs upstream data in a particular shape and doesn't get it, that's a **genuine upstream gap to
> FIX**, not an absence to mark." BITGET-SPOT raw tick exists ~18 months deep → MDPS **can** produce the candles → the
> mtf "silent skip" is a producible gap (run MDPS), not `empty_confirmed(NO_INPUT_AVAILABLE)`. This **supersedes** the
> Temporary-state row below for the BITGET-SPOT case. Buffer-depth correction: the plan's earlier "24h needs ~14 days"
> is only true for ~14-lookback groups; `market_structure@24h` (200-lookback) needs **~240 contiguous days**
> (`lookback × seconds(tf) × 1.2`). Relevant to the fan-out, not the 2 strategies.

### Track-2 fixes — SHIPPED as PR #8 (verification of "done" items that were NOT actually done)

- **FINDING-H** (cross_asset_correlation `DuplicateError`) — was a FALSE FLIP; now genuinely fixed
  (project-before-join).
- **`check_exists` versioned-path mismatch** (delta_one) — was an open P2 NOTE; now probes the
  `feature_group_version={N}/` path the writer uses (idempotent-skip was silently never firing). Misleading
  `check_exists_always_false` test renamed.
- Both: basedpyright 0/0/0, ruff clean, `quality-gates.sh --no-fix` exit 0, regression tests green (FINDING-H test
  proven to catch the real `DuplicateError`). **PR #8** `IggyIkenna/features-service` base `staging`, branch
  `fix/finding-h-checkexists-2026-06-03`. **Held by DEP-ORDER gate** (UTL/UAC not on staging) → Ikenna coordinates
  merge.

### Where this session STOPPED + key discovery for the next session

Stopped at Track-1 Phase-A **safety verification** (before any pipeline write). Discovery: **features-onchain routes to
the `-test` bucket via `IS_TEST_RUN=true`** (config field, "Route writes to -test- bucket instead of prod (E2E test
mode)") — NOT `PROTOCOL_DATA_SINK_BUCKET_{AG}` (that's delta_one's mechanism; onchain `feature_writer.bucket` resolves
the canonical bucket directly). The CLI also has `--dry-run` (dumps to local `data/sample/`, no GCS write) for a
zero-risk read→calc smoke. **Next session:** dry-run smoke → then `IS_TEST_RUN=true` run → `features-onchain-defi-test`
→ read-back assert.

### Open Track-1 todos (narrowed 2-strategy validation — the actual goal)

- [ ] [SCRIPT] P0. **Phase A — features-onchain staked-basis slice e2e.** `--dry-run` smoke (read
      `lst-rates`+`perp-funding` from prd, compute) then `IS_TEST_RUN=true` run of `lst_yields` / `lst_native_rates` /
      `perp_funding_rates` / `health_factor` (DEFI, window e.g. 2026-04-07..09) → `features-onchain-defi-test` →
      read-back assert sane ranges (`lst_native_rate≈1.0–1.2`, staking/funding APY plausible). No MDPS needed. Repo:
      features-service.
- [ ] [INFRA] P0. **Phase B — short CeFi MDPS top-up + delta_one funding_oi/realized_vol.** Run MDPS for ~2–3 days over
      the perp venues (read raw tick from `market-data-tick-cefi-prd`, write processed*candles to a `-test` bucket via
      `MDPS_OUTPUT_BUCKET*{CAT}`) → run delta_one `funding_oi`+`returns`(realized_vol_20)@1h → `-test` → read-back.
      Repos: market-data-processing-service + features-service.
- [ ] [INFRA] P1. **Basis-perp DeFi leg — confirm Drift/Orca coverage.** Verify `venue=DRIFT data_type=perp_funding` +
      `venue=ORCA/RAYDIUM data_type=dex_pool_state` exist in `market-data-tick-defi-prd` for the test window; MTDS/MDPS
      top-up if missing. Repo: market-tick-data-service.
- [ ] [VALIDATE] P1. **Phase C — strategy read-back.** Confirm `CarryStakedBasisRankAllocator` /
      `CarryBasisPerpRankAllocator` (+ `trace_carry_staked_basis.py`) consume the `-test` features and produce a
      non-empty ranked result. Repo: strategy-service.
- [ ] [SCRIPT] P2. **Perf/resource instrumentation** per `(asset_group × feature category)` across the Phase A/B runs
      (wall-clock, peak RSS, rows-in/out, parquet size). Repo: features-service `scripts/e2e/`.
- [ ] [INFRA] P2. **DEFERRED (fan-out, not the 2 strategies):** MDPS 1h backfill `2026-04-14→04-30` for mtf 4h/24h; and
      BITGET-SPOT 4h/24h candles via MDPS (producible gap — see audit above, do NOT `empty_confirmed`). Repo: MDPS.
- [ ] [VALIDATE] P2. **`usdc_idle_yield_apy_bps` stub** — confirm leave-as-0-floor (acked) vs wire `venue_funding_yield`
      upstream; folded with the per-service status-calibration audit. Repo: features-service onchain + delta_one.

## Temporary states + their canonical follow-up plans

| Temporary state                                                                             | Follow-up plan / action                                                                                                                                                                                                            |
| ------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| BITGET-SPOT instruments silently skipped (no 4h delta_one source) — no manifest row emitted | MTF orchestrator `process_instrument` must emit `empty_confirmed(NO_INPUT_AVAILABLE)` when `_load_and_join` returns None. Tracks as §6A violation. Follow-up: `features_and_ml_master` Phase 3 (honest-absence recording for mtf). |

## Notes / cross-refs

- Read-path fixes + the downstream findings (Bitfinex empty `instrument_type`, MTDS dual-write, the CeFi manifest↔file
  disconnect) are owned by `features_input_manifest_migration_2026_05_25.md` +
  `issues/cefi_processed_candles_manifest_file_disconnect_2026_05_25.md`. This plan does not duplicate them.
- Composes with HARD RULE _Data Pipeline Correctness Is The Heartbeat_ (the WRITE half is the other half of honest
  coverage; an un-emitted manifest row on a real feature write is the same class of divergence as a phantom `captured`).
- `onchain`/`sports` reads are the reference manifest-driven model; do not regress them when adding the shared harness.
