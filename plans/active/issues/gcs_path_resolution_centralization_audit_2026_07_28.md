---
doc_type: issue
title:
  GCS path resolution is not centralized — recurring "hand-rolled prefix drifts from canonical shape" bug class,
  workspace-wide audit in progress
summary: >-
  Root-caused via the MDPS `subprocess-per-date` timeout investigation (2026-07-28): a hand-rolled GCS existence-check
  prefix silently omitted the `pipeline_mode=` hive segment, making skip-existing/resume logic ALWAYS report "nothing
  found" for every pipeline_mode-partitioned category. Fixed forward, but a 4-agent audit (CEFI-scoped so far) found
  this is a genuinely recurring pattern — 3 more confirmed instances, plus a confirmed-stale UTL path-registry template
  consumed live by multiple services. No single canonical function resolves read/write paths workspace-wide; every
  service hand-rolls its own. Operator has directed extending the audit to DEFI/TRADFI/SPORTS/PREDICTION (batch + paper
  + live) and designing genuine centralization, under /autonomous.
status: open
nature: issue
asset_group: [cefi, defi, tradfi, sports, prediction]
stage: [meta]
repos:
  [
    unified-trading-library,
    unified-api-contracts,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    strategy-service,
    execution-service,
    instruments-service,
  ]
scope: [engineer, admin]
tags: [gcs, path-resolution, pipeline-mode, silent-failure, canonical-paths, centralization]
related:
  [
    /plans/active/issues/mdps_t1_recon_job_oom_failing_7_days_2026_07_26.md,
    /plans/active/issues/delta_one_cefi_candle_reader_never_threads_pipeline_mode_2026_07_27.md,
    /plans/active/issues/gcs_path_resolution_centralization_audit_sports_prediction_2026_07_28.md,
  ]
created: 2026-07-28
last_updated: 2026-07-29
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  found while root-causing mdps_t1_recon_job_oom_failing_7_days_2026_07_26.md Update 13's subprocess-per-date timeout;
  4-agent CEFI-scoped audit dispatched 2026-07-28 per operator directive, then scope-expanded to
  defi/tradfi/sports/prediction + batch/paper/live under /autonomous.
resolved_by:
depends_on: []
---

# GCS path resolution centralization audit

## Origin

Found while root-causing the MDPS `subprocess-per-date` 30-min-timeout bug
(`/plans/active/issues/mdps_t1_recon_job_oom_failing_7_days_2026_07_26.md` Update 13, 2026-07-28):
`market_data_processing_service/app/core/orchestration_scanner.py::_check_existing_outputs` built its GCS
existence-check prefix as `processed_candles/by_date/day={date}/timeframe={tf}/data_type={dt}/`, omitting the
`pipeline_mode=` hive segment the 2026-07-20 LOCKED canonical shape requires. Because GCS prefix listing is a literal
string match, this was never a crash — it silently returned "nothing exists here" on every call, so skip-existing never
worked for any pipeline_mode-partitioned category and every retry redid all prior work from scratch. Fixed:
`market-data-processing-service@df02dd0`.

**This is a recurring pattern, not a one-off**: the SAME bug class was already found+fixed ONCE before (2026-07-26,
`_list_blobs_scoped_by_venue`, the raw-tick LISTING side) — meaning this was at least the third independent occurrence
before today's audit even started.

Operator's directive (2026-07-28, verbatim intent): "worth doing a full audit of everything across the codebase to
ensure we don't mix GCS prefixes... centralise all checks to use UTL or UAC — something probably exists already that
maps inputs to paths read and write." Then, after the first (CEFI-scoped) pass landed: "we did this cefi analysis, need
to do defi tradfi sports and prediction too — ideally they use centralised functions to resolve paths, it's not just
about pipeline_mode, it's making sure every read and write path (batch, paper, live) uses the right path per what
canonically the data is supposed to be read and written from/to." Invoked under `/autonomous`.

## The canonical SSOT (as it exists today — itself found to have gaps)

`unified-trading-library/unified_trading_library/config_interface/paths/registry.py` — `PATH_REGISTRY` dict of
`DataSetSpec` entries, each with a `path_template`; consumed via `build_path(name, **partition_values)`,
`build_canonical_candle_path(...)`, `build_canonical_candle_object_path(...)`, `derive_candle_object_path(...)` (the
last two also live in MDPS's `canonical_writer_shaping.py`, delegating to the registry). **No single helper spans every
dataset for existence-checking** — this is the architecture gap the operator is pointing at. Each new dataset gets a
bespoke prefix-builder, which is structurally why this bug class keeps recurring (UTL audit agent's finding).

## Audit round 1 (CEFI-scoped) — COMPLETE, 4 parallel agents, all returned 2026-07-28

### Confirmed bugs (not yet fixed, beyond today's `_check_existing_outputs` fix)

1. **`unified-trading-library/unified_trading_library/config_interface/paths/registry.py:18-24`** — `"raw_tick_data"`
   `path_template` is **stale/wrong**:
   `raw_tick_data/by_date/day={date}/data_type={data_type}/instrument_type={instrument_type}/venue={venue}/` has NO
   `pipeline_mode=`/`asset_group=` segment and wrong key order. Real objects (live-verified via `gcloud storage ls` on
   `gs://market-data-tick-cefi-prd-central-element-323112/`, **independently confirmed by 3 of 4 agents**):
   `raw_tick_data/by_date/day={date}/pipeline_mode={pm}/asset_group={ag}/venue={V}/instrument_type={IT}/data_type={DT}/{id}.parquet`.
   **Consumed live**: `unified_trading_library/domain_client/clients/market_data.py:56-65`
   `MarketTickDomainClient.get_tick_data()` calls `build_path("raw_tick_data", ...)` directly — would build a wrong
   prefix. Live-vs-dead-code severity for this exact call site NOT fully resolved (caller census incomplete, one agent's
   budget ran out). **This is the highest-leverage single fix** — one registry correction instead of N per-caller fixes,
   and it's the root cause "just call `build_path()`" doesn't yet work for `raw_tick_data` callers. Two more registry
   rows in the same bucket family (`l2_book_checkpoints`, `liquidation_clusters`, `registry.py:295-308`) show the same
   missing-`pipeline_mode=` pattern — **not GCS-verified, flagged likely-same-bug, unconfirmed**.

2. **`features-service/features_service/delta_one/app/core/dependency_checker.py:648`** — `_discover_instruments()`
   hand-rolls `processed_candles/by_date/day={date}/timeframe={timeframe}/` (no `pipeline_mode=`). Called from
   `validate_lookback_candles()` (line 486) whenever `instruments=None`. Because `LookbackValidationReport.valid`
   defaults `True` and only flips `False` via `add_insufficient()`, an empty discovery list produces a **VACUOUS PASS**
   (0/0 "validated") — the validator silently reports success while validating nothing. This is a **known-open gap**:
   `/plans/active/issues/delta_one_cefi_candle_reader_never_threads_pipeline_mode_2026_07_27.md` todo 4 already asked
   for exactly this audit and this call site wasn't caught then. Reachability of `instruments=None` in the common bulk
   CLI path traced but not fully proven end-to-end.

3. **`market-tick-data-service/market_tick_data_service/cli/handlers/deribit_options_chain_handler.py::_write_shard`
   (~line 515-556)** — calls UAC `build_cefi_partition_path(...)` and uses the result **directly** for the GCS
   read/write, with NO post-hoc `pipeline_mode=` insertion — every sibling CeFi writer
   (`engine/orchestrator/symbol_rules.py:535`, `live/websocket_runner.py:124`,
   `cli/handlers/book_microstructure_handler.py:193`) does this insertion; this one doesn't. Writes the manifest row
   with `pipeline_mode=PipelineMode.LIVE_DERIBIT` but the OBJECT PATH doesn't carry it — a genuine path≠manifest
   divergence. Impact currently unclear: 6 sampled dates (2026-05-15/06-15/07-15/07-26/07-27/07-28) found ZERO Deribit
   options_chain objects at either shape — this data_type may be dormant right now, but the writer is structurally
   broken for whenever it next fires.

4. **`market-tick-data-service/market_tick_data_service/cli/handlers/_perp_funding_kalshi_polymarket.py:135,160,320-322`**
   — same missing-`pipeline_mode=` pattern, but with an explicit code comment claiming "the CeFi GCS partition path...
   carries no pipeline_mode segment (unlike DeFi's), so this write path doesn't need it." **This comment may itself be
   stale** — contradicts the 2026-06-01 operator ruling (cited in `symbol_rules.py:487,514-521`) that pipeline_mode is
   canonical-in-path AND primary for cefi/tradfi/prediction. Needs an explicit ruling: deliberate exception, or the same
   bug wearing a self-justifying comment?

### Confirmed dead/duplicate code (not live bugs, but landmines — fix or delete, don't just leave)

- `market_data_processing_service/app/core/orchestration_scheduling.py:262-306`
  `OrchestrationSchedulingMixin._check_existing_outputs` — unreferenced duplicate of the function fixed today, STILL
  carries the broken pre-fix prefix. Zero production callers (only test-only subclasses).
- `market_data_processing_service/config.py:210-240` `get_raw_tick_path()` — zero production callers, same stale order
  as the registry (no `pipeline_mode=`/`asset_group=`).
- `market_data_processing_service/app/core/data_source.py:64` `GCSDataSource` class — zero production instantiations
  (only `LiveDataSource` is instantiated).
- `market_data_processing_service/app/core/output_path_helpers.py:75-101` `build_processed_candle_path()` — zero
  production callers; its own docstring says prefer `build_canonical_candle_object_path`.
- `features-service/features_service/cross_instrument/app/calculators/adv.py:194-214` `_candidate_paths()` — wrong
  timeframe token (`24h` vs real `1d`) + missing `instrument_type=`. Zero live callers found (`RollingAdvReader`/
  `compute_rolling_adv` unused) — a landmine for the first real caller, not an active bug.
- `execution-service/execution_service/utils/loader.py` + `utils/io/loader.py` — byte-for-byte identical dead files,
  `MarketDataLoader.build_path()` missing 3 segments (`pipeline_mode=`, `instrument_type=`, `venue=` — the worst-broken
  prefix found in the whole audit). Zero instantiation call sites, not even exported from `utils/__init__.py`.
- `market-tick-data-service/market_tick_data_service/market_interface/adapters/cefi/tardis_shared.py::build_partition_path`
  (line 434) — a SECOND, independently-maintained copy of UAC's `build_cefi_partition_path`, explicitly documented as
  mirroring it "byte-for-byte." Not dead (used by the Tardis bulk-download lane) but a drift-risk duplicate.

### Confirmed-safe / positive baseline (don't re-flag these later)

- MDPS write path (`candle_write_mixin.py`, `output_path_helpers.py::build_canonical_candle_object_path`,
  `canonical_writer_shaping.py::derive_candle_object_path`) — all correctly delegate to the UTL registry SSOT.
- MDPS's now-fixed `orchestration_scanner.py::_check_existing_outputs` / `_list_blobs_scoped_by_venue` — correctly
  enumerate every candidate `pipeline_mode` via `_candidate_pipeline_mode_values()`.
- Several **day-only-prefix + substring-match-on-full-blob-name** patterns across MDPS/MTDS/strategy-service — robust to
  `pipeline_mode=` position BY CONSTRUCTION (a shallow prefix is a true string-prefix of every real object shape
  regardless of what comes after `day=`). This is a genuinely good, cheap, defensive pattern worth naming as a positive
  convention.
- `features-service/delta_one/app/core/data_loader.py:430-476` `_resolve_blob_paths` — a well-documented 3-tier
  canonical-first probe built on `candle_read_prefixes()`/`build_canonical_candle_path()`.
- `strategy-service/strategy_service/engine/core/canonical_adv_ranked_universe_provider.py:313-360` — shallow `day={D}/`
  prefix + full listing + substring match, sidesteps the whole bug class by construction.
- `instruments-service`'s sports domain — correctly uses UAC's `candidate_parquet_paths()`
  (`unified-api-contracts/unified_api_contracts/canonical/domain/sports/gcs_paths.py`), pipeline_mode-aware and
  legacy-fallback-aware. Some standing orchestrator files (`sports_fixtures.py:217-218`,
  `sports_reference_core.py:64-65`, `weather.py:268-269`, `footystats.py:799-800`) hand-roll the SAME correct dual
  canonical/legacy shape instead of calling the shared helper — not a bug today, but the same duplication pattern that
  caused the original MDPS bug; low-priority follow-up to consolidate onto the one helper.
- `market_tick_data_service/reader.py`, `instrument_availability_paths.py`, `rebuild_*_manifest.py`,
  `reconcile_market_tick_manifest.py`, `check_tradfi_manifest_disk_consistency.py::build_shard_prefixes` — all either
  day-level-list-then-parse or deliberately dual-shape-aware. Correct.

### Not fully verified in round 1

- `MarketTickDomainClient.get_tick_data()`'s real reachability — RESOLVED 2026-07-28, see P0 flip above (zero real
  callers workspace-wide).
- `l2_book_checkpoints`/`liquidation_clusters` registry rows — RESOLVED 2026-07-28 in round 2 below (confirmed dead, no
  writer/consumer anywhere).
- MDPS's live-mode async persistence worker — RESOLVED 2026-07-28 in round 2 below (confirmed dead; live mode's real
  candle writes go through the same code batch uses).
- Deribit options_chain / Kalshi-Polymarket-perp findings (MTDS, above) are code-confirmed but not GCS-verified for
  real-world blast radius (sparse/possibly-dormant data_types; a full corpus walk was deliberately avoided per the
  workspace's single-walk/heavy-I/O rule).
- Full line-by-line audit of MTDS's 100+ one-off migration scripts was NOT performed (spot-checks showed
  dual-shape-awareness is the norm post-2026-07-20; deprioritized vs. LIVE standing code).

## Audit round 2 (DEFI-scoped) — COMPLETE, 4 parallel agents, all returned 2026-07-28

Same methodology as round 1 (MTDS / MDPS / downstream consumers [features-service, strategy-service, execution-service]
/ UTL+instruments-service), scoped to `asset_group=defi`, explicitly covering batch/paper/live per the operator's
expanded directive.

### Confirmed bugs

1. **[CRITICAL — live, data-correctness, not just empty-read/retry cost — FIXED 2026-07-28,
   `execution-service@70f8bcdf988691263512b01b0efde69b68dd4b68`, see Todos below for the full fix + corrected
   blast-radius writeup] `execution-service/execution_service/data/defi_data_loader.py:131-140`**
   (`DeFiDataLoader._gcs_path`) builds the PRE-MIGRATION legacy shape
   (`raw_tick_data/by_date/day={D}/data_type={DT}/instrument_type={IT}/venue={V}/symbol={S}/{id}.parquet`) — the sibling
   `canonical_paths.py` module's own docstring documents this shape as broken since the reader-fallback window closed
   ~2026-06-15 (today is 2026-07-28). Live-verified: real DeFi objects nest `pipeline_mode=`/`asset_group=` between
   `day=` and any `data_type=`/`venue=` segment; this exact prefix never matches. **Live-wired** into `venues/aave.py`,
   `venues/morpho.py`, `venues/etherfi.py`, `engine/handlers/flash_loan_handler.py` for oracle prices, lending rate
   indices, risk params, reward availability. Failure degrades SILENTLY to hardcoded `DEFAULT_RISK_PARAMS`/default
   prices (a `logger.warning`, no error) — real historical DeFi market data never actually gets used. Primarily
   batch/backtest-scoped per the module's docstring; not fully verified whether live/paper trading calls this on a hot
   path vs. only backtest setup. **Highest-priority fix in this whole audit** — the only finding across both rounds
   where wrong data silently substitutes for real data, vs. an empty-read that just costs a retry. A second, CORRECT
   `DeFiDataLoader` already exists in the same repo at `execution_service/data/loaders/defi.py` (uses
   `canonical_paths.build_candidate_raw_tick_paths` properly) — same class name, different module, real misimport risk
   on top of the bug itself.
2. **`market_tick_data_service/reader.py:367-373`** (`CanonicalParquetReader._build_shard_bases`) builds DeFi
   chain-scoped read prefixes as `asset_group=defi/chain={C}/venue={V}/...` — REVERSED vs. the real write shape
   `asset_group=defi/venue={V}/chain={C}/...` (verified live + against UAC's `build_defi_partition_path()`, the write
   SSOT). No current production caller passes `chain=` for a DeFi read (dormant today), but it's a public method on a
   publicly-exported reader class. The codex SSOT (`defi-canonical-naming-ssot.md` gotcha #8) already documents+fixes
   the IDENTICAL bug in the live WRITER (`mtds@0fcfa803`) but never flagged this second, independent occurrence in the
   reader.
3. **`market_data_processing_service/app/core/cloud_data_provider.py:222-225`** (`_load_instruments_by_venue`,
   explicit-`venue` branch) omits `pipeline_mode=`/`asset_group=`, always misses. Dormant (both production callers pass
   `venue=None`, routing through a safe branch) but `venue` is a documented public parameter.
4. **`features-service/features_service/onchain/app/calculators/eigen_rewards_calculator.py:51-55`**
   (`_mtds_eigen_rewards_blob_candidates`) — two exact-path guesses, both missing `pipeline_mode=`. `blob_exists` always
   False → silently falls through to the DefiLlama vendor-API fallback even when real MTDS data exists. Batch.
5. **`features-service/features_service/onchain/collectors/parquet_dust_loader.py:132-136`** — hand-rolled list prefix
   missing the registry's `onchain/` root segment (the writer correctly uses `build_path("lst_seasonal_rewards", ...)`;
   reader disagrees by construction). Currently dormant/unwired (`Phase6Driver`'s `dust_loader=` has zero real
   production call sites) — will silently fail the moment it's wired up as designed.

### Confirmed dead/duplicate code (landmines — fix or delete, don't just leave)

6. **MDPS's entire live-mode async-persistence adapter chain is dead**: `AsyncGCSDataSink`/`GCSDataSink`
   (`app/core/data_sink.py`), `LiveDataSource`/`GCSDataSource` (`app/core/data_source.py`), and the
   persistence-queue/thread machinery in `cli/handlers/live_mode_handler.py`. Zero production callers — live mode's real
   candle writes go through the SAME `CandleWriteMixin._write_candles()` batch uses (safe). **Resolves round 1's
   flagged-open MDPS live-mode question.** The dead code is ALSO badly broken (no canonical prefix, `date=` not `day=`,
   random UUID filename instead of `{instrument_id}.parquet`) — a silent-corruption landmine if ever rewired. Recommend
   deletion, not fix-forward.
7. **`l2_book_checkpoints`/`liquidation_clusters`/`liquidity_features_1m` PATH_REGISTRY rows are CONFIRMED DEAD** — zero
   live GCS objects in any asset_group's bucket, zero writer code anywhere in the workspace, and their only consumers
   (`unified_trading_library/domain_client/clients/liquidity.py`'s 3 client classes) are never instantiated outside
   their own definition file. **Resolves round 1's open question** — cleanup, not a live bug.
8. `features-service/features_service/onchain/adapters/{onchain_writer,onchain_loader}.py`'s `build_path()` methods
   hand-roll a stale shape (missing `onchain/` root); their `DataSinkAdapter`/`DataSourceAdapter` subclasses have zero
   production instantiation (test-only).
9. `instruments-service/instruments_service/engine/orchestrator/writers.py` hand-rolls the `instrument_availability/`
   path (currently byte-identical to the registry's `"instruments"` template — no live drift today, but no shared-code
   guarantee against future drift).

### Confirmed-safe / positive baseline

- `raw_tick_data`/`processed_candles`/`instruments` PATH_REGISTRY templates independently re-verified correct for DeFi
  (live GCS-checked against real `asset_group=defi` objects).
- MTDS's `market_interface/adapters/defi/canonical_write.py::write_defi_rows()` is the real DeFi-write SSOT — ~35
  handlers funnel through it correctly; the live WS writer (`live/websocket_runner.py::live_tick_blob_path`) is correct
  and self-guards via `canonical_path_violations(require_pipeline_mode=True)`.
- MDPS's `_check_existing_outputs`/`_list_blobs_scoped_by_venue` (fixed 2026-07-28) +
  `canonical_writer_shaping.py::derive_candle_object_path()` verified correct for DeFi, including chain-split venue
  handling.
- features-service's `onchain/app/core/data_loader.py`, `onchain/adapters/mtds_canonical_reader.py`,
  `onchain/app/core/feature_writer.py`, `cross_instrument/engine/raw_data_loader.py`,
  `onchain/calculators/perp_funding_rates_defi.py` all correctly delegate to registry/UAC SSOTs.
- strategy-service's `canonical_*_provider.py` family (dex_pool/vault/perp_funding/adv_ranked_universe/spot_mark/
  dated_future_mark) reads MTDS/MDPS's GCS corpus directly rather than through features-service — a DELIBERATE,
  codex-cited T4 integration pattern (not a service→service violation), using the safe day-prefix+needle-filter
  convention throughout.
- execution-service's `canonical_paths.py::build_candidate_raw_tick_paths`, `defi_lateral_loader.py`, the CORRECT
  `data/loaders/defi.py::DeFiDataLoader`, and `providers/solana_amm_depth_provider.py` are confirmed-safe reference
  exemplars.
- instruments-service's DeFi venue/chain naming verified consistent with UAC's declared vocabulary — no drift found.

### Structural gaps flagged (not proven actively firing — needs follow-up, not a guess-fix)

- `onchain_features`/`lst_seasonal_rewards` PATH_REGISTRY templates carry NO `pipeline_mode=` segment at all (unlike
  `raw_tick_data`/`processed_candles`/`instruments`). Real onchain raw data is captured under 2+ different
  pipeline_modes (`batch_onchain_rpc`, `batch_onchain_subgraph`) — if the feature-compute step ever derives the same
  `feature_group`+`day` from both source modes, they'd silently overwrite each other. Not proven active.
- `PATH_REGISTRY["instruments"].bucket_template` has no `-prd-` env tier (would 404 via a literal
  `build_bucket("instruments", ...)`) — already guarded by a standing QG
  (`market-tick-data-service/scripts/quality_gates/check_reader_writer_bucket_parity.py`, STEP 5.91, "C6 incident"
  class); zero live callers found. Corroborated independently by 2 of the 4 round-2 agents.
- `_candidate_pipeline_mode_values()` (MDPS `orchestration_scanner.py:119-146`) omits `Mode.REPLAY`, unlike UAC's
  analogous helper. DeFi has real registered `REPLAY_*` pipeline modes; spot-checked 6 recent dates, zero live
  `replay_*` DeFi objects found today (dormant), but will silently misbehave the moment a DeFi replay re-fetch runs.
- MDPS `dependency_checker.py`'s `max_results=1000/2000` listing cap on whole-day DeFi `raw_tick_data` scans (now 6+
  pipeline_mode sources × multi-venue) — whether this is ever hit in practice is unverified (a full recursive
  day-listing did not complete in-session; abandoned per single-walk/heavy-I/O discipline).

## Audit round 3 (TRADFI-scoped) — COMPLETE, 2 agents, both returned 2026-07-28

Better news than round 2: **no CRITICAL live-firing bug found**. TradFi's core write/read paths (`raw_tick_data`,
`processed_candles`, the live-mode WS write path, execution-service's actually-live `data/loader.py::UCSDataLoader`) are
all independently re-verified correct. Findings below are dormant landmines, dead code, and one genuine
architecture-hygiene gap.

### Confirmed bugs (code-level, none proven live-firing)

1. **`unified-trading-library/unified_trading_library/pipeline_mode_resolver.py`** has no venue-override entry for
   `FRED`/`ECB`/`OFR`/`IBKR`/`OpenBB`, and UAC's `SOURCE_PRIORITY` has no `"yield_curve"`/`"ohlcv_1d"` entries either —
   so `derive_pipeline_mode_for_row()` for these venues silently falls through to the generic
   `_ASSET_GROUP_FALLBACKS["tradfi"] = BATCH_DATABENTO`, mis-stamping `pipeline_mode=batch_databento` on data Databento
   never touched. Live-verified: **zero FRED/ECB/OFR/IBKR/OpenBB objects exist anywhere** on the sampled date — either
   never run in prod, or ran on an unsampled date. Code-confirmed landmine, not a proven incident.
2. **`execution-service/execution_service/data/loader.py:127-128`** (`UCSDataLoader._resolve_trades_category`) maps
   TradFi `instrument_type=="INDEX"` → `"indices"` (plural); the real canonical token is `index` (singular,
   live-verified). `canonical_paths.py`'s legacy-category map has neither, so the canonical UAC probe is skipped
   entirely — legacy-path-only, same broken-shape-since-2026-06-15 class as round 2's execution-service CRITICAL
   finding. **Not proven live-firing**: INDEX has no `trades` data_type at all (only OHLCV candles), so `load_trades()`
   likely never gets called for it. A SECOND, differently-wrong INDEX mapping exists in the same repo
   (`loader_base.py::_infer_tradfi_category()` maps INDEX → `"futures_chain"`, no INDEX branch) — two independently
   wrong fallbacks for the same case, unclear which (if either) ever fires.
3. **`unified-trading-library/unified_trading_library/domain_client/clients/features.py`**'s
   `FeaturesCalendarDomainClient` calls the env-less `build_bucket("calendar_features", ...)` — `registry.py`'s
   `calendar_features` row is missing the `-prd-` tier every sibling FOLD-A row got (confirmed 404). Dead code (same
   unused `domain_client` layer as round 1's `MarketTickDomainClient`), so not live-firing.

### `corporate_actions` PATH_REGISTRY row — CONFIRMED ORPHANED (both agents independently corroborated)

4. Zero code references anywhere outside the registry file itself, zero live GCS objects
   (`instruments-store-tradfi-prd-.../corporate_actions/` doesn't exist) — same class as round 1/2's confirmed-dead
   rows. WORSE than just dead: the REAL, separately-wired corporate-actions producer
   (`features-service/.../calendar/cli/handlers/corporate_actions_handler.py`) doesn't use this registry row at all — it
   hand-rolls its own `calendar/corporate_actions/`+`calendar/earnings_results/` shape (contradicting the registry's
   single-shard `extra_files` design) via a correctly-resolved bucket. That real handler's own output has never actually
   landed in prod either (`features-calendar-prd-.../` contains only `_index/`) — flagging as a fact (launch status
   unclear), not a verdict. `instruments-service/.../ibkr.py::get_corporate_actions()` (a third, unrelated
   corporate-actions fetch method) is also confirmed dead, zero callers.

### Confirmed dead/duplicate code

5. `features-service/features_service/volatility/io/loader.py::VolatilityLoader.build_path()` — hand-rolled legacy
   shape, zero callers (the live volatility reader is the different
   `volatility/core/data_loader.py::VolatilityDataLoader`, confirmed-safe, canonical-first).
6. `execution-service/execution_service/data/loaders/__init__.py`'s `UCSDataLoader` (composing the broken round-2
   `DeFiDataLoader`) is a THIRD same-named class, never imported by production — the live one is the different
   `execution_service.data.loader.UCSDataLoader`. Extends round 2's naming-collision finding.
7. `FeaturesCalendarDomainClient`/`FeaturesOnchainDomainClient`/`FeaturesDeltaOneDomainClient`/
   `FeaturesVolatilityDomainClient` (all in `domain_client/clients/features.py`) — confirmed unused anywhere, same dead
   layer as round 1.

### Confirmed-safe / positive baseline (the majority of TradFi's surface)

- `raw_tick_data`/`processed_candles` registry templates + the live-mode WS writer independently re-verified correct for
  TradFi.
- `execution-service/execution_service/data/loader.py::UCSDataLoader.load_trades()` — the PRIMARY, widely-imported live
  trades reader (validator, backtest engine, book/trades builders) — correctly delegates through
  `canonical_paths.build_candidate_raw_tick_paths`, asset-group-parameterized so TradFi already got the same fix
  CEFI/DEFI needed.
- MTDS `symbol_rules.py`/`tradfi_shared.py` partition-path builders, `reader.py`,
  `check_tradfi_manifest_disk_consistency.py` — all correct, GCS-verified (including the v6 futures-chain tail shape).
- `features-service/.../calendar/adapters/mtds_fred_reader.py` — correctly uses the singular `index` token (contrast
  with execution-service's finding 2).
- `volatility_features`/`delta_one_features` registry rows have the `-prd-` tier correctly hardcoded (unlike
  `calendar_features`).
- strategy-service has **no TradFi-specific canonical GCS reader at all yet** — confirmed-safe by absence, nothing to
  fix.
- MDPS's `_KNOWN_BATCH_SOURCES_BY_AG[TRADFI]` correctly excludes Barchart (fully retired from the live pipeline_mode
  vocabulary, only stale in comments/one-off migration scripts).

### Architecture-hygiene gap (not a bug — feeds the existing P1 centralization-design todo, no new todo needed)

TradFi has **3 independent, currently-correct, mutually-agreeing partition-path implementations**
(`unified-api-contracts::build_tradfi_partition_path`, MTDS `symbol_rules.py`, MTDS `tradfi_shared.py`) — the worst
duplication ratio found across all 3 rounds so far, byte-identity only enforced by one dedicated test. A textbook case
for the centralization design this whole audit is ultimately building toward.

## What's NOT done yet (the operator's expanded scope)

**All 5 audit rounds are complete** — CEFI/DEFI/TRADFI here, SPORTS/PREDICTION (rounds 4-5) in the split-off
continuation doc `/plans/active/issues/gcs_path_resolution_centralization_audit_sports_prediction_2026_07_28.md` (this
parent doc hit 586+ lines — split rather than grow past the plan line cap). What remains is the accumulated per-finding
fix todos across both docs (1 CRITICAL already shipped, several P1/P2 dormant bugs + dead-code cleanups still open) and
the operator's third ask — **a genuine centralization design**, not just point-fixes (does a true "resolve me the
read/write path for dataset X, given these partition keys" universal function need to be built, or does one already
exist that services should be migrated onto) — which is the item that actually closes the recurring-bug-class problem
going forward. Still open, tracked as a todo below.

## Todos

- [x] [SCRIPT] P0. **Fix the UTL `raw_tick_data` path-registry template** — DONE 2026-07-28,
      `unified-trading-library@2943224b`. `path_template`/`partition_keys` now match the real, live, 3-agent-confirmed
      shape:
      `raw_tick_data/by_date/day={date}/pipeline_mode={pipeline_mode}/asset_group={category}/venue={venue}/instrument_type={instrument_type}/data_type={data_type}/`.
      `build_path("raw_tick_data", ...)` now REQUIRES `pipeline_mode=` (KeyError without it), mirroring
      `processed_candles`/`instruments`. Regression test added:
      `tests/config_interface/unit/test_paths_registry_smoke.py::test_raw_tick_data_template_now_requires_pipeline_mode`
      (mirrors `test_processed_candles_template_now_requires_pipeline_mode`). Checked `l2_book_checkpoints`
      (registry.py:303-309) and `liquidation_clusters` (registry.py:310-316) for the same gap: BOTH have it too (no
      `pipeline_mode=`/`asset_group=` placeholder in either template) — but unlike `raw_tick_data`, neither has a
      3-agent-verified live shape or a confirmed real writer (grepped MTDS/features-service: only
      `domain_client/clients/liquidity.py` consumes them, same dead-abstraction layer as `MarketTickDomainClient`; no
      writer found). NOT fixed in this pass — guessing the shape without live-GCS verification risks a confidently-wrong
      fix, worse than the current silent-empty-prefix failure. Tracked as a new P1 todo below. (repo:
      unified-trading-library)

- [x] [SCRIPT] P0. **Complete the `MarketTickDomainClient.get_tick_data()` caller census** and fix or confirm-dead —
      DONE 2026-07-28, `unified-trading-library@2943224b`. Caller census: grepped `get_tick_data\b` workspace-wide
      (excluding tests/.venv) — 3 hits, all inside `unified-trading-library` itself
      (`domain_client/clients/market_data.py`, `domain/standardized_service.py`, `domain/market_data_client.py`, the
      latter two independent hand-rolled implementations, not calling this method) — zero real external callers anywhere
      in the 10+-repo workspace, so the signature change is breaking-change-safe. Fixed
      `MarketTickDomainClient.get_tick_data()` to require `pipeline_mode: str` and pass `category=asset_group` into
      `build_path()`, mirroring `MarketCandleDomainClient.get_candles()`'s established convention exactly. No test
      coverage existed for this specific class (confirmed via grep — `tests/unit/test_domain_clients.py`'s
      `get_tick_data` tests target the DIFFERENT `MarketTickDataDomainClient` class in `domain/market_data_client.py`),
      so nothing broke. `tests/unit/test_domain_client_catalog.py:13`'s `raw_tick_data` mock checked — it fully
      monkey-patches `get_spec()` with its own synthetic spec, isolated from the real registry, so it's unaffected by
      the template change; no update needed. (repo: unified-trading-library)

- [x] [SCRIPT] P1. **Verify + fix (or confirm-dead) the `l2_book_checkpoints`/`liquidation_clusters` registry
      templates** — RESOLVED 2026-07-28 by the round-2 DEFI audit (see "Confirmed dead/duplicate code" item 7 above):
      confirmed dead, zero writer anywhere in the workspace, zero live GCS objects, zero real consumers. Also found a
      THIRD dead row in the same family, `liquidity_features_1m`. Deletion tracked in a new P2 todo below rather than
      fixed-forward (nothing needs these). (repo: unified-trading-library)

- [x] [SCRIPT] P0. **Fix the CRITICAL live execution-service `defi_data_loader.py` bug** — DONE 2026-07-28,
      `execution-service@70f8bcdf988691263512b01b0efde69b68dd4b68`. Rewrote `_gcs_path`/`_load_parquet_from_gcs` into
      the canonical-first/legacy-fallback candidate-list pattern (mirroring `data/loaders/defi.py`), routed through
      `canonical_paths.build_candidate_raw_tick_paths` + UCS instead of raw `gcsfs`. Found + fixed 3 MORE independent
      bugs beyond the path shape while live-verifying each data category: (1) `lending_indices` queried aToken/debtToken
      symbols instead of the real bare-reserve-symbol MTDS key; (2) `risk_params`/
      `flash_loan_availability`/`utilization` call sites passed a slash-joined `"{venue}/{instrument}"` string into a
      single param, mangling venue/symbol extraction; (3) flash-loan reads queried a `flash_loan_availability` data_type
      MTDS has never written (real token is `flash_loan_events`) — AND `risk_params`/
      `flash_loan_availability`/`rewards`/`utilization` were never even CALLED from `load_data_for_date` at all, so
      their getters always returned hardcoded defaults regardless of the path bug. `risk_params`/ `flash_loan_events`
      live-verified as genuinely absent from GCS as of 2026-07-28 (checked 6+ days) — wired best-effort per the task's
      graceful-fallback guidance, not fabricated. **Blast-radius correction** (more precise than this todo's original
      framing): `venues/aave.py`/`morpho.py`/`etherfi.py` — the classes actually named in this todo — have **zero
      production callers anywhere in execution-service** (real live DeFi execution uses a _different_
      `defi_execution.protocols.*` connector family that never touches this loader). The ONE genuinely live-wired
      consumer is `engine/handlers/flash_loan_handler.py` (registered in the mode-agnostic instruction-routing table) —
      its `get_flash_loan_availability()` call was silently falling back to a conservative 100k liquidity limit instead
      of real on-chain data. New follow-up todo below covers the naming collision + confirming whether
      aave.py/morpho.py/etherfi.py are dead code worth deleting. (repo: execution-service)

- [ ] [SCRIPT] P2. **Confirm + act on execution-service's `venues/aave.py`/`morpho.py`/`etherfi.py` dead-code question,
      and resolve the `DeFiDataLoader` naming collision** — found while shipping the P0 fix above: these 3
      venue-connector classes (the ones the original CRITICAL-bug report assumed were live-wired) have zero production
      callers anywhere in execution-service; real live DeFi execution goes through a different
      `defi_execution.protocols.*` connector family that never instantiates them. If confirmed genuinely dead, delete
      rather than maintain (workspace's "no shims" rule); if some other entry point does construct them, find it and
      correct the blast-radius record. Separately, two classes are STILL both named `DeFiDataLoader`
      (`data/defi_data_loader.py`, `data/loaders/defi.py`) — decide rename vs. consolidate. Needs a real operator/design
      judgment call, not a guessable fix. (repo: execution-service)

- [ ] [SCRIPT] P1. **Fix `market_tick_data_service/reader.py:367-373`'s DeFi chain/venue segment-order bug** —
      `CanonicalParquetReader._build_shard_bases` builds `asset_group=defi/chain={C}/venue={V}/...`, reversed vs. the
      real write shape `asset_group=defi/venue={V}/chain={C}/...`. Dormant today (no live caller passes `chain=`), but a
      landmine on a public method. Fix the segment order in `_make_base`, update the matching docstring
      (`reader.py:26-28`) and unit-test contract
      (`tests/market_interface/unit/test_canonical_parquet_reader.py:702-763`, currently asserting the WRONG order).
      Also add a follow-up note to `/codex/02-data/defi-canonical-naming-ssot.md` gotcha #8 — it documents the identical
      bug's fix in the live WRITER (`mtds@0fcfa803`) but never flagged this second, independent reader-side occurrence.
      (repo: market-tick-data-service, unified-trading-pm for the codex note)

- [ ] [SCRIPT] P1. **Delete MDPS's dead live-mode async-persistence adapter chain** — `AsyncGCSDataSink`/`GCSDataSink`
      (`app/core/data_sink.py`), `LiveDataSource`/`GCSDataSource` (`app/core/data_source.py`), and the
      persistence-queue/thread machinery in `cli/handlers/live_mode_handler.py` (~lines 94-133, 313-380). Zero
      production callers — confirmed via full call-graph trace (round-2 DEFI audit finding 6): live mode's real candle
      writes go through `CandleWriteMixin._write_candles()`, the same method batch uses. The dead code is also badly
      broken (wrong prefix, `date=` not `day=`, random UUID filename) — delete rather than fix-forward, nothing needs
      it. Update/remove the tests that exercise `_persistence_worker` directly (`tests/unit/test_live_mode_handler.py`,
      `tests/unit/test_live_mode_handler_coverage.py`) since they test dead code. (repo: market-data-processing-service)

- [ ] [SCRIPT] P1. **Fix the two features-service missing-`pipeline_mode=`/wrong-prefix bugs found in round 2** — (a)
      `onchain/app/calculators/eigen_rewards_calculator.py:51-55`'s `_mtds_eigen_rewards_blob_candidates` omits
      `pipeline_mode=` from both exact-path guesses (batch, currently silently falls through to the DefiLlama vendor
      API); (b) `onchain/collectors/parquet_dust_loader.py:132-136`'s list prefix is missing the registry's `onchain/`
      root segment vs. what the writer actually writes (currently dormant/unwired — `Phase6Driver`'s `dust_loader=` has
      zero real production callers, so this is a landmine for whenever it IS wired up). Add regression tests for both
      (fail pre-fix, pass post-fix). (repo: features-service)

- [ ] [SCRIPT] P2. **Delete the confirmed-dead PATH_REGISTRY rows + their dead consumer classes** —
      `l2_book_checkpoints`/`liquidation_clusters`/`liquidity_features_1m`/`corporate_actions`
      (`unified_trading_library/config_interface/paths/registry.py:303-323`, `:65-73`) plus their only consumers
      (`unified_trading_library/domain_client/clients/liquidity.py`'s `L2BookCheckpointClient`/
      `LiquidationClustersClient`/`LiquidityFeaturesClient`; the whole `domain_client/clients/features.py` family —
      `FeaturesCalendarDomainClient`/`FeaturesOnchainDomainClient`/`FeaturesDeltaOneDomainClient`/
      `FeaturesVolatilityDomainClient` — never instantiated outside their own file).
      `instruments-service/.../ibkr.py::get_corporate_actions()` is a separate, also-dead corporate-actions fetch method
      (zero callers). Also fold in
      `features-service/features_service/onchain/adapters/{onchain_writer,onchain_loader}.py`'s and
      `volatility/io/loader.py::VolatilityLoader`'s dead `build_path()` methods (test-only, stale shape), and
      `execution-service/execution_service/data/loaders/__init__.py`'s never-imported `UCSDataLoader` (a third
      same-named class — see the P0 fix's naming-collision note). (repo: unified-trading-library, features-service,
      instruments-service, execution-service)

- [ ] [SCRIPT] P2. **Fix the FRED/ECB/OFR `pipeline_mode` provenance-fallback mis-stamp** —
      `unified_trading_library/pipeline_mode_resolver.py` has no venue-override for `FRED`/`ECB`/`OFR`/`IBKR`/`OpenBB`,
      and UAC `SOURCE_PRIORITY` has no `yield_curve`/`ohlcv_1d` entries, so resolution silently falls through to
      `_ASSET_GROUP_FALLBACKS["tradfi"]=BATCH_DATABENTO` — mis-stamping real FRED/ECB/OFR data as Databento-sourced.
      Code-confirmed, not proven live-firing (zero real objects found for these venues on the sampled date — may never
      have run in prod). Add the missing venue-overrides/source-priority entries. (repo: unified-trading-library,
      unified-api-contracts)

- [ ] [SCRIPT] P2. **Fix execution-service's TradFi INDEX category mapping (2 independently-wrong mappings)** —
      `execution_service/data/loader.py:127-128`'s `_resolve_trades_category` maps `INDEX`→`"indices"` (plural; real
      canonical token is singular `index`), and the separate `loader_base.py::_infer_tradfi_category()` maps
      `INDEX`→`"futures_chain"` (no INDEX branch at all) — two different wrong fallbacks for the same case in the same
      repo. Not proven live-firing (INDEX has no `trades` data_type, only OHLCV candles). Fix both to the
      confirmed-correct singular `index` token; trace which (if either) path is actually reachable before declaring
      done. (repo: execution-service)

- [ ] [SCRIPT] P2. **Fix `calendar_features` PATH_REGISTRY row's missing `-prd-` env tier** —
      `unified_trading_library/config_interface/paths/registry.py`'s `calendar_features` bucket_template
      (`features-calendar-{project_id}`) is missing the env tier every sibling FOLD-A row got in the 2026-07-18 fold
      migration (confirmed 404 vs. the real `features-calendar-prd-{project_id}` bucket). Currently dead (the only
      consumer, `FeaturesCalendarDomainClient`, is unused) — low urgency but a 1-line fix while in the file for the
      dead-code-cleanup todo above. (repo: unified-trading-library)

- [ ] [SCRIPT] P2. **Investigate the `onchain_features`/`lst_seasonal_rewards` `pipeline_mode`-collision structural
      gap** — neither PATH_REGISTRY template has a `pipeline_mode=` segment, unlike every other DeFi-relevant template.
      Real onchain raw data is captured under 2+ pipeline_modes (`batch_onchain_rpc`, `batch_onchain_subgraph`); if the
      feature-compute step ever derives the same `feature_group`+`day` from both, they'd silently overwrite each other.
      Not proven active — first determine whether this collision can actually happen given the current onchain
      feature-compute orchestrator's mode-selection logic, then decide fix vs. confirm-safe. (repo: features-service,
      unified-trading-library)

- [ ] [SCRIPT] P2. **Add `Mode.REPLAY` to MDPS's `_candidate_pipeline_mode_values()`**
      (`app/core/orchestration_scanner.py:119-146`) — currently enumerates only `(Mode.BATCH, Mode.LIVE)`, unlike UAC's
      analogous `_canonical_pipeline_mode_prefixes()` which deliberately includes `Mode.REPLAY` "to avoid
      false-phantoming replay-captured cells." DeFi has real registered `REPLAY_*` pipeline modes; dormant today
      (spot-checked 6 recent dates, zero live `replay_*` DeFi objects), but will silently misbehave (treat existing
      replay data as "not existing," redo work) the moment a DeFi replay re-fetch runs. (repo:
      market-data-processing-service)

- [ ] [SCRIPT] P2. **Decide + act on the two duplicate `raw_tick_data` path builders found during the `get_tick_data()`
      caller census** — `unified_trading_library/domain/standardized_service.py:125-127`
      (`f"raw_tick_data/by_date/day={date_str}/data_type={data_type}/{instrument}.parquet"`) and
      `unified_trading_library/domain/market_data_client.py:236`
      (`f"raw_tick_data/by_date/day={date_str}/data_type={data_type}"`) — two MORE independent, mutually-disagreeing,
      hand-rolled `raw_tick_data` path implementations, neither delegating to the registry SSOT. Both live in the same
      domain-client/domain layer already shown dead for `MarketTickDomainClient.get_tick_data()` (zero real callers
      workspace-wide) — `tests/unit/test_domain_clients.py`'s `TestMarketTickDataDomainClient` exercises
      `market_data_client.py`'s class directly, so confirm whether ANY real service imports
      `MarketTickDataDomainClient`/`StandardizedService` before deciding delete-as-dead vs. fix-to-delegate. (repo:
      unified-trading-library)

- [ ] [SCRIPT] P1. **Fix `features-service/delta_one/app/core/dependency_checker.py:648`'s vacuous-pass bug** —
      `_discover_instruments()` needs the same `pipeline_mode=`-aware prefix enumeration MDPS's
      `_candidate_pipeline_mode_values()` pattern uses (or better: a shared UTL helper if one gets built per the
      centralization todo below). This closes
      `/plans/active/issues/delta_one_cefi_candle_reader_never_threads_pipeline_mode_2026_07_27.md` todo 4. Add a
      regression test proving a real discovery list is non-empty for a pipeline_mode-partitioned date (fail pre-fix,
      pass post-fix, matching today's established pattern). (repo: features-service)

- [x] [DESIGN] P1. **Rule on the remaining MTDS finding** — RULED + FIXED + SHIPPED 2026-07-29,
      `market-tick-data-service@d2270ac426f652f458f9a6fac14a9519d389fdba`. Verdict: **same stale-bug pattern as
      KALSHI_PERP/POLYMARKET_PERP**, not a genuine carve-out. `_write_shard` called UAC `build_cefi_partition_path(...)`
      and used the result directly for the GCS read/write with no post-hoc `pipeline_mode=` insertion, while the
      manifest record (`recorder.record_captured`/`record_zero_rows`/`record_failed`) already carried
      `pipeline_mode=PipelineMode.LIVE_DERIBIT` — a genuine path≠manifest divergence, structurally identical to the
      Kalshi finding, just not yet independently verified. History check found this is actually a REGRESSION: an earlier
      fix (`deribit_live_options_chain_path_noncanonical_2026_07_21.md` todo 2, `mtds@ec0df878`, 2026-07-26) correctly
      rewrote the path from a totally-broken THIRD shape to the v6 canonical chain-bundle shape, but in doing so DROPPED
      the (mis-positioned) legacy `pipeline_mode=` segment entirely instead of re-inserting a correctly-positioned one —
      so the path has been missing `pipeline_mode=` since that rewrite, not from day one. **Confirmed genuinely
      dormant** (not merely "currently appears dormant"): (a) GCS-verified zero objects at either shape across 9 sampled
      days (2026-07-20 through 2026-07-28) in
      `gs://market-data-tick-cefi-prd-central-element-323112/raw_tick_data/by_date/day=.../`; (b) zero
      `deribit-opts-fwd-*` (the handler's own launcher VM prefix) or `cefi-fwd-daily-cron-*` (the cron host meant to
      fire it daily at 09:15 UTC) VM instances exist now or in `gs://deployment-scripts-central-element-323112/vm-logs/`
      ever; (c) `plans/active/infra_capture_and_devops_leftovers_2026_07_06.md`'s own 2026-07-07 entry documents the
      cron wiring shipped but its required follow-on ("re-launch the existing `cefi-fwd-daily-cron-*` VM ... Follow-on
      (operator action, NOT this task)") was never executed — the crontab that would fire this operation has never
      actually been installed on a live host. So `--operation deribit-options-chain` has never fired in prod, at any
      shape, ever. **Fix** (mirrors `book_microstructure_handler.py`'s pattern, the closest sibling): `_write_shard` now
      takes a required `pipeline_mode: PipelineMode` param, `.replace()`-inserts it directly after `day={D}/` (same
      position as every other CeFi writer — `symbol_rules.py`, `websocket_runner.py`, `book_microstructure_handler.py`),
      and calls `enforce_structural_and_observe_id_form(require_pipeline_mode=True, ...)` as a write-time canonicality
      guard (this file had none before). The 3 callers (`_collect_currency`/`_collect_expiry_shard`) already pass
      `PipelineMode.LIVE_DERIBIT` to the manifest calls unchanged — `_write_shard`'s one call site now passes the SAME
      enum value, so path and manifest are guaranteed identical by construction. Regression tests updated/added in
      `tests/unit/test_deribit_options_chain_handler.py`: flipped the 3 pre-existing `_write_shard` unit tests (which
      had asserted `pipeline_mode=live_deribit` NOT in path — the exact stale assumption this fix corrects) to assert it
      IS present in the correct position, plus a new end-to-end assertion in
      `test_collect_expiry_shard_records_options_chain_instrument_type` proving the real call chain
      (`_collect_expiry_shard` → `_write_shard`) threads the pipeline_mode through, not just the isolated unit. Fixing
      this now (before the first real fire, once the operator re-launches the cron host) avoids a repeat of the Kalshi
      incident (~5 weeks of wrong-shape prod objects before being caught). (repo: market-tick-data-service)

- [x] [SCRIPT] P0. **Fix `_perp_funding_kalshi_polymarket.py`'s missing `pipeline_mode=` insertion** — RULED 2026-07-28
      by round 5, FIXED + SHIPPED 2026-07-29, `market-tick-data-service@52e8f256e6a314b38b3baeeaced919b040a985aa`.
      `_write_cefi_perp_funding_rows` now takes a required `pipeline_mode: str` param and `.replace()`-inserts it into
      both the empty-shard AND per-instrument sharding-loop write paths (both branches were affected).
      `_collect_kalshi_perp` resolves `pipeline_mode` via the SAME
      `perp_funding_handler._resolve_pipeline_mode_for_protocol()` call the manifest record already uses, so path and
      manifest are guaranteed identical by construction, not just convention. Added a write-time
      `enforce_structural_and_observe_id_form(require_pipeline_mode=True, ...)` guard (mirroring
      `book_microstructure_handler.py`'s pattern — this file had ZERO write-time canonicality guard before). Regression
      tests added (`tests/unit/test_perp_funding_kalshi_polymarket.py`): populated-shard shape, empty-shard shape,
      venue-agnostic passthrough (POLYMARKET_PERP), and an end-to-end live-mode test proving `live_kalshi_perp` threads
      through correctly (not hardcoded to batch). QG green (7460 passed, 0 failed). Stale "no pipeline_mode needed"
      comment deleted. Target shape confirmed:
      `raw_tick_data/by_date/day={D}/pipeline_mode=batch_kalshi_perp/asset_group=cefi/venue=KALSHI_PERP/instrument_type=perpetual/data_type=perp_funding/{symbol}.parquet`.
      (repo: market-tick-data-service)

- [x] [DESIGN] P1. **Resolve the MDPS live-mode async-persistence partition-key question** — RESOLVED 2026-07-28 by
      round 2's DEFI audit (see "Confirmed dead/duplicate code" item 6 above, missed flipping this todo at the time —
      caught during the round-5 wrap-up). Answer: the question is moot — `get_data_sink().write(..., partition={...})`'s
      `pipeline_mode=`/`instrument_type=`-less partition dict never lands canonically (confirmed broken: no canonical
      prefix, `date=` not `day=`, random UUID filename), but it's DEAD CODE with zero production callers. MDPS's real
      live-mode candle writes go through the SAME `CandleWriteMixin._write_candles()` batch uses (safe,
      already-verified-correct). Tracked for deletion in the dead-code-cleanup todo below. (repo:
      unified-trading-library, market-data-processing-service)

- [ ] [SCRIPT] P2. **Delete or fix the 6 confirmed dead/duplicate path-construction sites** listed above
      (`OrchestrationSchedulingMixin._check_existing_outputs`, `get_raw_tick_path()`, `GCSDataSource`,
      `build_processed_candle_path()`, `adv.py::_candidate_paths`, `execution-service`'s duplicate
      `MarketDataLoader.build_path()` files) — CLAUDE.md's "delete deprecated code, no shims" rule; each is either truly
      dead (delete) or a landmine waiting for its first real caller (fix to match canonical shape first, or delete if
      genuinely superseded). Low individual risk, real hygiene value, cheap to batch together. (repo:
      market-data-processing-service, features-service, execution-service)

- [x] [SCRIPT] P1. **Round 2 (DEFI-scoped) 4-agent audit** — DONE 2026-07-28, findings documented above (5 confirmed
      bugs incl. 1 CRITICAL-live, 4 confirmed dead/duplicate sites, 4 structural gaps flagged). New follow-up todos
      logged for every finding.

- [x] [SCRIPT] P1. **Round 3 (TRADFI-scoped) 2-agent audit** — DONE 2026-07-28, findings documented above. No CRITICAL
      live-firing bug (unlike round 2) — 3 dormant/unverified code-level bugs, 1 confirmed-orphaned registry row
      (corroborated by both agents), several dead-code sites, and TradFi's worst-in-audit
      3-way-duplicated-but-currently-correct partition-path implementation (architecture-hygiene evidence for the
      centralization design todo). New follow-up todos logged for every finding.

- [x] [SCRIPT] P1. **Extend the audit to SPORTS + PREDICTION** — MOVED 2026-07-28 to
      `/plans/active/issues/gcs_path_resolution_centralization_audit_sports_prediction_2026_07_28.md` (a split-off
      continuation doc, created once this parent doc reached 586 lines) rather than growing this doc past the plan line
      cap. Track rounds 4-5 there, not here.

## Centralization design (the operator's capstone ask) — RULED 2026-07-29

**The mechanism already exists in two layers — the bug class was never "no centralized function exists," it was (a)
callers bypassing it and (b) one structural footgun inside the mechanism itself. No new function needs building; the
remaining work is closing the footgun + finishing the migration.**

Evidence from all 5 rounds: every single "confirmed-safe" pattern found — dozens of them, across CEFI/DEFI/TRADFI/
SPORTS/PREDICTION, batch/paper/live, read AND write — funneled through exactly one of two existing layers:

1. **UTL's `PATH_REGISTRY` + `build_path()`/`build_bucket()`/`build_full_uri()`**
   (`unified-trading-library/unified_trading_library/config_interface/paths/registry.py`) — the dataset-name-keyed
   generic layer (`raw_tick_data`, `processed_candles`, `instruments`, `onchain_features`, `delta_one_features`, …). Now
   that the P0 registry fix landed (`raw_tick_data`'s stale template), every entry actually consumed live is confirmed
   correct across all 5 asset groups.
2. **UAC's asset-group-specific partition-path builders** (`build_cefi_partition_path()`/`build_defi_partition_path()`/
   `build_tradfi_partition_path()`/`candidate_parquet_paths()`,
   `unified-api-contracts/unified_api_contracts/canonical/`) — the write-path-specific layer, paired with
   `execution-service`'s `canonical_paths.py::build_candidate_raw_tick_paths()` wrapper for the
   canonical-first/legacy-fallback READ side. This is what every confirmed-safe writer (MTDS's
   `symbol_rules.py::_build_partition_path_for_asset_group`, `live/websocket_runner.py::live_tick_blob_path`,
   `book_microstructure_handler.py`) and reader (execution-service's `data/loader.py::UCSDataLoader`, features-service's
   `gcs_reader.py`/`mtds_canonical_reader.py`/`raw_data_loader.py`, MDPS's `canonical_writer_shaping.py`) ultimately
   builds on.

**The structural footgun**: layer 2's CeFi/TradFi builders
(`build_cefi_partition_path()`/`build_tradfi_partition_path()`) do NOT accept `pipeline_mode` as a parameter — by
design, since UAC's own partition-path module predates the `pipeline_mode=` hive-segment convention. Every correct
writer compensates with a **manual, easy-to-forget post-hoc `.replace(f"day={D}/", f"day={D}/pipeline_mode={pm}/", 1)`
insertion** immediately after calling the builder. This is NOT a documented contract enforced by the type system or a
runtime check at the builder level — it's a convention every new writer has to independently remember and correctly
implement. **This is exactly why the same bug (skipping the insertion) recurred 3 INDEPENDENT times this audit found and
fixed** (KALSHI_PERP/POLYMARKET_PERP in `_perp_funding_kalshi_polymarket.py`, Deribit in
`deribit_options_chain_handler.py`, plus the original `_check_existing_outputs` bug that started this whole audit) — not
random bad luck, a structural gap in the mechanism itself.

**The actual design fix** (scoped, bounded, SCRIPT-eligible — not a fresh design question): make the `pipeline_mode`
insertion impossible to skip, by EITHER (a) adding `pipeline_mode: str` as a required parameter directly to
`build_cefi_partition_path()`/`build_tradfi_partition_path()` in UAC so the builder inserts it itself (mirrors how
`build_defi_partition_path()` already requires it), or (b) providing one shared MTDS-side wrapper
(`write_cefi_shard(...)`-style) that does builder-call + insertion + the write-time `canonical_path_violations()`/
`enforce_structural_and_observe_id_form()` guard in a single call, and migrating every CeFi/TradFi writer onto it so a
new writer literally cannot ship without going through all three steps. Option (a) is the more durable fix (closes the
gap at the source for every current AND future caller); option (b) is faster but requires everyone to "remember" to call
the wrapper.

**Read side is already closed**: `build_candidate_raw_tick_paths()` (execution-service) and the equivalent
canonical-first/legacy-fallback probing pattern (features-service's various readers, MDPS's
`_candidate_pipeline_mode_values()`-driven scanner) already make omitting `pipeline_mode=` structurally self-correcting
on reads — a caller that doesn't know the exact `pipeline_mode` still finds the right object via the candidate-list
probe. The footgun is write-side only.

**Remaining work is migration, not invention**: the ~16 P1/P2 SCRIPT todos already logged across this doc and the
sports_prediction continuation doc ARE the migration work — every confirmed bug found this audit is a caller that needs
to move onto (or be brought into compliance with) one of the two existing layers. No new todo needed here beyond the one
below for the footgun fix itself.

- [x] [DESIGN] P1. **Design + build genuine centralization** — RULED 2026-07-29 (see the section directly above for the
      full evidence-based writeup): the mechanism already exists (UTL `PATH_REGISTRY`/`build_path()` for dataset-generic
      paths, UAC's per-asset-group partition builders + execution-service's `build_candidate_raw_tick_paths()` for the
      write/read-specific layer) — confirmed by every single one of the dozens of "confirmed-safe" patterns found across
      all 5 rounds. The recurring bug class was never "no centralized function," it was (a) callers bypassing both
      layers (the ~16 already-logged SCRIPT fixes) and (b) one structural footgun:
      `build_cefi_partition_path()`/`build_tradfi_partition_path()` don't accept `pipeline_mode` as a parameter, forcing
      every writer to manually `.replace()`-insert it post-hoc — the exact gap that let the SAME bug recur 3 independent
      times (Kalshi, Deribit, the original `_check_existing_outputs` bug) this audit alone found and fixed. New
      follow-up SCRIPT todo below closes that footgun at the source; everything else needed is already tracked. (repo:
      unified-api-contracts, market-tick-data-service)

- [x] [SCRIPT] P1. **Close the CeFi/TradFi `pipeline_mode` write-side footgun** — DONE 2026-07-29,
      `unified-api-contracts@fa25a345` (added required `pipeline_mode: str` param to `build_cefi_partition_path()`/
      `build_tradfi_partition_path()`, mirroring `build_defi_partition_path()`'s existing contract — every existing
      caller workspace-wide updated, no default value added so the footgun can't silently persist) +
      `market-tick-data-service@94067e1a` (migrated all 5 CeFi call sites —
      `symbol_rules.py::_build_partition_path_for_asset_group`, `live/websocket_runner.py::live_tick_blob_path`,
      `book_microstructure_handler.py`, `_perp_funding_kalshi_polymarket.py`, `deribit_options_chain_handler.py` — onto
      the required-param contract, deleting every now-redundant post-hoc `.replace()` call). One genuine exception
      correctly left in place with a clear comment: `symbol_rules.py`'s TradFi branch still can't delegate to
      `build_tradfi_partition_path()` because the orchestrator carries lowercase legacy series-class instrument_type
      tokens (`rates`/`etf_flows`/`futures_chain`) the UAC `InstrumentType` enum doesn't cover — a pre-existing,
      separate gap, not a re-introduction of the footgun (that branch still correctly inserts `pipeline_mode=` via the
      same explicit derivation, just via `.replace()` rather than the builder param). QG passed (full test suite,
      batch+live smoke matrix green). This is the todo that makes the "insert pipeline_mode after
      `.build_*_partition_path()`" bug class structurally impossible going forward — the last piece of the whole audit.
      (repo: unified-api-contracts, market-tick-data-service)

- [x] [SCRIPT] P1. **Round 1 (CEFI-scoped) 4-agent audit** — DONE 2026-07-28, findings documented above.

## Deferred work after 2026-07-29

Every confirmed-live-firing bug found across all 5 rounds (execution-service's DeFi loader, MTDS's KALSHI_PERP writer,
MTDS's Deribit writer) is fixed and shipped; the centralization design question is RULED; and the write-side
`pipeline_mode` footgun that let the same bug recur 3 times is now closed at the source (both above). **Zero open
`[DESIGN]` judgment calls remain, and the recurring-bug-class problem itself is structurally closed.** What's left is
entirely bounded, independent SCRIPT execution work — point-fixes for already-found instances, not blocked on anyone:

| Item                                                                                                               | State    | Blocked on                                      |
| ------------------------------------------------------------------------------------------------------------------ | -------- | ----------------------------------------------- |
| ~16 P1/P2 SCRIPT fixes (dormant bugs, dead-code cleanup) — see this doc's + the sports_prediction doc's open todos | Not done | nobody — pick up any, independent of each other |

**Recommended next item**: any of the remaining P1s — none is individually higher-leverage than another at this point
(the one structural fix that mattered, the footgun, is done); pick by repo/area convenience.
