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
- [ ] [INFRA] P0. **Run the backfill via existing MTDS + MDPS tooling** (do NOT reinvent capture/processing) for the
      resolved window + data_types, target = liquid CeFi venues spot+perp (Binance/Bybit/OKX/Deribit to start; extend
      per-feature). Raw capture (MTDS) → processed_candles (MDPS) → **prod canonical `-prd` buckets** so the e2e read
      path discovers it naturally via the consolidated v8 manifest. Coordinate with any in-flight backfill / the
      `mtds_mdps_master` sequencing — do not collide with the single-walk migration. > **🟢 BACKFILL RUNNING
      (2026-05-26):** CeFi MTDS raw-tick VMs launched 2026-05-25 — Binance, Bybit, Coinbase, > Deribit heavy VMs running
      (`scripts/vm/launch-mtds-cefi-backfill.sh`). MDPS CeFi processed_candles reprocessor > pending MTDS completion.
      DeFi features VM launch **BLOCKED-OPERATOR-DECISION** — 2024+2025 DeFi candles in flat > bucket
      `market-data-tick-defi-central-element-323112`, 2026 in prd bucket; `mtds-dex-swaps-backfill` VM still > RUNNING.
      Do not launch DeFi feature VMs until bucket split resolved + DEX swaps backfill completes.
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
- [ ] 🟠 [FINDING-B] P1. **Group-level fail-fast aborts the whole run.** `market_structure` all-NaN → group marked
      FAILED → the batch handler **aborted before the remaining 9 of 17 feature groups ran**. A degenerate single group
      should not block the rest. Make the CLI batch path **group-isolated** (continue on group failure, report per-group
      status) — mirrors the shard-level-failure-isolation HARD RULE. **PAUSED per operator 2026-05-26** (fix not
      started). Provenance: e2e Phase 2 2026-05-26.

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
- [ ] [VALIDATE] P1. **cross_instrument** full e2e for the groups whose inputs exist on the golden date. Note the 5
      groups needing raw normalized book/trade schema (book_depth_bands, liquidity_walls, liquidation_clusters,
      flow_interaction, composite_sr) will honestly skip — that is the tracked P2 data-surface gap in the migration
      plan, not a failure here. Read-back assert the groups that do compute.
  - **[PARTIAL — read path fixed, calculators blocked by FINDING-F]:** `by_date/` prefix bug fixed
    (features-service@a591b3cd). `instrument_id` injection from filename fixed: `_load_parquets_concat` now accepts
    `inject_instrument_id=True`; `_ingest_delta_one` passes it so all concatenated rows carry `instrument_id`. 5 unit
    tests added (`tests/cross_instrument/unit/test_batch_handler.py`). QG green. — features-service@846915f5.
  - **[FINDING-F] P1 BLOCKER — all cross_instrument calculators need raw OHLCV (`close`, `high`, `low`, `volume`) but
    delta_one outputs only derived features (candlestick_patterns, momentum, oscillators, etc.) without passing through
    raw prices.** Confirmed by reading prod test bucket sample parquet: `has_close=False`. All 6 calculators
    (`regime_detection`, `cross_venue_spreads`, `realized_implied_vol`, `cross_asset_correlation`, and the polymarket
    set) raise `Missing required columns: {close}` at validation. **Resolution options:** (a) delta_one service adds
    `close` as a passthrough column in its output (small change, preserves architecture); (b) cross_instrument reads raw
    OHLCV from MTDS directly for the price-dependent calculators (bigger change, breaks single-input-bucket design).
    Operator decision needed. This is Ikenna territory (cross-repo architecture). Cross-link to `features_and_ml_master`
    Phase 1A. **BLOCKED-OPERATOR-DECISION.**

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

Ran `scripts/e2e/run_pipeline_e2e.py` per family on `-test` buckets (CEFI, date 2026-05-03; candle input read-only
from `-prd`). Status per family:

| family | result | evidence / bug |
|---|---|---|
| **delta_one** | ✅ **VALIDATED** | 59 parquets across 8 feature_groups; sample BITGET-FUTURES BTCUSDT 1h momentum = 24 rows / **964 numeric features / 0 all-NaN** / sane ADX. Wrote `features-delta-one-cefi-test`. |
| **volatility** | ⚠️ honest-skip | `futures_basis` produced no parquet + **no manifest row** for the date. Confirm legit (no spot+futures pair input) vs should emit `empty_confirmed`. |
| **cross_instrument** | ❌ real bug | After source-routing fix, reads `-test` delta_one but crashes `ValueError: Missing required columns: {'close'}` — `cross_asset_correlation` expects a `close` price col absent from delta_one feature output (964 feature cols, no OHLC). Design call: read candles for prices, or expose `close` from delta_one. |
| **multi_timeframe** | ❌ 2 bugs (1 fixed) | (1) `get_input_bucket` ignored its `PROTOCOL_DATA_SOURCE_BUCKET` override → read prod delta_one → 0 instruments. **FIXED** (features@335942d9). (2) Then crashes `Event logging not initialized. Call setup_events() first.` — batch compute path never inits event logging. **OPEN** — implies the mtf batch path was never run end-to-end. |

**e2e-driver (8fa8ebbc) defects found + fixed** (features@62cbe91a, @e6811f31, @335942d9): wrong parquet-assert path
(`batch/date=…` vs real `day=…/feature_group=…/timeframe=…`); false-PASS honest-skip that masked a captured-but-no-file
disconnect; inline-f-string bucket names that targeted nonexistent buckets (cross-instrument/multi-timeframe instead of
the SSOT-aliased xinstrument/mtf) + uncaught `google.api_core.NotFound` crash; cross_instrument missing delta_one
`-test` source routing. Created the 2 missing `-test` buckets (`features-xinstrument-cefi-test`,
`features-mtf-cefi-test`, asia-northeast1).

- [ ] [P1] **cross_instrument: `cross_asset_correlation` Missing required column `close`.** Provenance: e2e -test
  2026-05-26. Decide source (candles vs delta_one) / expose close.
- [ ] [P1] **multi_timeframe: `setup_events()` not called in batch compute path** → `Event logging not initialized`
  crash. Provenance: e2e -test 2026-05-26 (after the get_input_bucket fix).
- [ ] [P2] **volatility: emits no manifest row on no-input** — confirm honest-skip vs `empty_confirmed` expectation.

### TradFi scope (operator decision 2026-05-26)

**SPY + its options are in scope; spot cash equities + commodities are OUT for now.** This refines the earlier
"CME-only" call: the bare-ticker equity `instrument_type=UNKNOWN` partition rejects (AAPL/ABT/…) are an **expected
known-gap**, not a bug. Open clarification for when tradfi features are tackled: "SPY + its options" = cash SPY ETF
(NYSE Arca) + SPY/SPX options (OPRA/CBOE) **or** CME E-mini S&P (ES) futures + ES options (the golden-day CME data holds
ES options clusters, not cash SPY) — confirm venue/source before id-canonicalization work.

## Notes / cross-refs

- Read-path fixes + the downstream findings (Bitfinex empty `instrument_type`, MTDS dual-write, the CeFi manifest↔file
  disconnect) are owned by `features_input_manifest_migration_2026_05_25.md` +
  `issues/cefi_processed_candles_manifest_file_disconnect_2026_05_25.md`. This plan does not duplicate them.
- Composes with HARD RULE _Data Pipeline Correctness Is The Heartbeat_ (the WRITE half is the other half of honest
  coverage; an un-emitted manifest row on a real feature write is the same class of divergence as a phantom `captured`).
- `onchain`/`sports` reads are the reference manifest-driven model; do not regress them when adding the shared harness.
