---
title: "Wave3x Track D — zero-activity-bar adapter audit findings (MTDS / MDPS / features-service)"
created: 2026-05-11
author: harsh-wave3x-tab (slot 3)
source:
  - plans/active/wave3x_residual_ssots_2026_05_08.md (Track D)
  - plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md (anti-sequencing audit row for this plan)
  - 6 read-only audit sub-agents spawned 2026-05-11 (MTDS core / MTDS DeFi / MTDS tradfi-prediction-sports / MDPS / features-service ×2)
locked_by: live-defi-rollout
locked_since: 2026-05-11
---

# Wave3x Track D — zero-activity-bar adapter audit findings

> **Severity**: P0 (two current correctness bugs surfaced) + the case-D wiring itself is P1 substantial-deferred-work.
> **Blast radius**: MTDS (CeFi/sports honest-coverage sentinel currently DOA), MDPS (canonical-writer/write-gate path
> dead on live path; 1440-NaN-bar incident class STILL live in TradFi OHLCV passthrough), features-service (8 families;
> case-D not wired), UAC (`EmptyConfirmedReason` taxonomy — one candidate new reason). **Suggested owner**: anti-sequencing
> decision → Ikenna slot 5 (v7/v8 schema) + slot 1 (escalation). MTDS blank-reason fix + MDPS dead-write-gate fix →
> writegate Phase 2.A/2.E owner + Harsh slot 5 (live-pipeline) + Harsh slot 6 (QG sweep). features-service case-D wiring
> → defer post-cutover OR fold into a Wave 3.M follow-up plan.

## TL;DR — the anti-sequencing question (the reason Track D had to run before the 2026-05-15 Phase 2 freeze)

Per [`code_freeze_migrate_backfill_sequencing_2026_05_10.md`](../code_freeze_migrate_backfill_sequencing_2026_05_10.md)
anti-sequencing audit row: *"`wave3x_residual_ssots_2026_05_08.md` Track D — if audit finds new shard atom dimension or
new error reason needed → manifest schema bump → another Phase 2.1."*

**Audit conclusion:**

1. **No NEW manifest row-key / shard-atom dimension is forced by Track D.** The `zero_activity` marker case-D needs is a
   **value-axis** addition to the per-row parquet schema (analogous to the existing MDPS `market_state='closed'` marker),
   NOT a new manifest column. The manifest already distinguishes `captured` / `empty_confirmed` / `attempted_failed` /
   `expected_unattempted`; case-D rows are `captured` (real bar count > 0) at the **same** shard coordinate the populated
   rows would land at. Confirmed by D1 (MTDS core), D2 (MTDS DeFi), D4 (MDPS) sub-agents.
   - One nuance from D3 (MTDS tradfi/prediction/sports): prediction case-D writes carry-forward bars per individual
     `market_id` and sports per `fixture_id` — but **both grains are ALREADY in the canonical shard-atom matrix**
     (`(sports, source, data_type, league_id, fixture_id or day-aggregate, day)` and prediction's bundled
     `canonical_question_group` + the in-memory cluster-counts accumulator already keyed by market_id). So the
     implementation needs to thread the existing grains through; the manifest **schema** doesn't change. No v8 bump.

2. **One candidate NEW `EmptyConfirmedReason` value surfaced (D4 / MDPS)**: `EXPECTED_KNOWN_SOURCE_GAP` for *mid-history*
   accepted gaps that don't fit `EXPECTED_PRE_SOURCE_COVERAGE_START` — specifically the **VIX 15m gap** (2025-11-13 →
   today−60d, currently written as a NaN-OHLC placeholder parquet which is wrong) and sports `KNOWN_COVERAGE_GAPS`
   ranges. **This is an `error-reason taxonomy` change → anti-sequencing-relevant per the audit's trigger list.**
   **DECISION NEEDED (Ikenna slot 5 + slot 1)**: add `EXPECTED_KNOWN_SOURCE_GAP` to UAC `EmptyConfirmedReason` in the
   Phase 1 schema window (before 2026-05-15 freeze) OR defer post-cutover. It's a tiny additive enum value; recommend
   adding it in Phase 1 since it has a real consumer (the VIX gap NaN-placeholder fix + the broader honest-absence
   reason-taxonomy completeness). NOT urgent if deferred — the VIX gap currently mis-writes a NaN parquet either way;
   that's a separate bug to fix.
   ✅ **SHIPPED 2026-05-11** (operator decision A1 routed enum-add to Phase 1) — UAC@174f401 by slot 6 ikenna-v8-schema-tab.
   `EmptyConfirmedReason.EXPECTED_KNOWN_SOURCE_GAP = "EXPECTED_KNOWN_SOURCE_GAP"` lands in
   `unified_api_contracts/canonical/crosscutting/honest_coverage.py` + `EMPTY_CONFIRMED_REASONS` frozenset +
   `LegacyBlankErrorReasonError` message updated; 1 unit test in `tests/unit/test_honest_coverage.py`
   (`test_expected_known_source_gap_value_present`) asserts the value + prefix. Sister case-D consumer wiring (MDPS
   `_maybe_write_vix_gap_placeholder` → `record_empty(reason=EXPECTED_KNOWN_SOURCE_GAP)`) is still **deferred** to P0-2
   below (writegate Phase 2.A scope; MDPS triple-SSOT cleanup is bigger).

3. **Case-D itself (the actual zero-activity-bar adapter wiring) is substantial deferred work** — ~30 adapters/handlers
   across MTDS + MDPS + 8 features families need it, plus a NEW UTL zero-activity-bar primitive, plus the
   `instrument_catalog` reference wired at adapter construction (Wave 2/3 of writegate Phase 3.D.5, currently "pending").
   This is NOT going to land before 2026-05-15. **DECISION (Ikenna slot 5 + slot 1)**: defer the case-D *implementation*
   post-cutover (or fold into a named Wave 3.M follow-up plan), since (a) it forces no schema change so deferring is
   sequencing-safe, and (b) the more urgent gap is the **current bugs below**, not the missing case-D enrichment.

## 🔴 P0 — Current correctness bugs surfaced by the audit (NOT case-D — these are live now)

### P0-1 — MTDS orchestrator `record_empty(row_key=...)` without `reason=` → honest-coverage sentinel pass silently aborts

**Found by D1 + D3.** `market_tick_data_service/engine/orchestrator.py:2671` (sports sentinel), `:2808` (Tier-3
per-instrument sentinel), `:2849` (Tier-2 venue-level sentinel) + `market_tick_data_service/scripts/rebuild_prediction_manifest.py:351`
(defensive branch) call `record_empty(row_key=...)` with **no `reason=` kwarg**. UTL `ManifestWriter.record_empty`
raises `LegacyBlankErrorReasonError` on blank reason (guard added UTL@68b3804a 2026-05-07; these callsites date
2026-04-21). The sentinel pass is wrapped in `try: … except Exception: logger.warning("Manifest write failed
(non-blocking)")` (orchestrator `~:2222` / `~:2880`) → **the first such call raises → the entire honest-coverage
sentinel pass aborts silently for that date** → no `empty_confirmed` / `attempted_failed` rows land for CeFi or sports
on any date that hits a zero-data shard. The DeFi `cli/handlers/*_handler.py` path DOES pass `reason=` (it's not
affected); only the orchestrator's CeFi/sports/tradfi sentinel path is broken.
- **Fix**: pass `reason="SOURCE_RETURNED_ZERO"` (or the calendar/lifecycle `EXPECTED_*` where the orchestrator already
  knows it — e.g. `is_non_trading_day` → `EXPECTED_HOLIDAY`/`EXPECTED_WEEKEND`/`EXPECTED_PARTIAL_HALF_DAY`). Also: stop
  swallowing the manifest-write exception in the wrapping `except` — a `LegacyBlankErrorReasonError` should be loud, not
  "non-blocking".
- **Owner**: ✅ **SHIPPED 2026-05-11 by Harsh slot 6** — `market-tick-data-service@3da026d`: the 4 `record_empty` callsites
  now pass `reason="SOURCE_RETURNED_ZERO"`; an `except (LegacyBlankErrorReasonError, UnknownEmptyConfirmedReasonError):
  raise` was added before the swallowing `except` so manifest-contract violations are loud, not "non-blocking". Verified
  ruff-clean + zero new basedpyright + 12 sentinel tests pass. (Originally routed to writegate Phase 2.E + slot 5; operator
  moved it to slot 6's added scope 2026-05-11 — slot 5 / the writegate Phase 2.E owner: P0-1 is DONE, nothing pending.
  The deeper "every `(shard_key, day)` in the expected universe gets a manifest row" item (TradFi non-trading-day
  pre-skip emits `record_expected_empty(reason=EXPECTED_HOLIDAY/...)`) is still writegate Phase 2.E scope — slot 6's fix
  was scoped to the missing-`reason=` + exception-swallowing, not the full expected-universe-row coverage.)
- **Related**: D3 also flagged that MTDS emits **no** `record_expected_empty` / `record_expected_unattempted` anywhere —
  TradFi non-trading-day pre-skip just `continue`s with no manifest row, contrary to CLAUDE.md "every `(shard_key, day)`
  in the expected universe gets a manifest row." Same fix surface (writegate Phase 2.E).

### P0-2 — MDPS canonical-writer / `record_captured` / 4-pillar-write-gate path is DEAD on the live path; TradFi OHLCV passthrough still emits the 1440-NaN-bar incident shape

**Found by D4 — this is the highest-priority MDPS finding.**

- **The `record_captured`/write-gate path is unreachable.** `market_data_processing_service` runtime orchestrator is
  `CandleOrchestrationService(CandleOrchestrationWriter)`. `CandleOrchestrationWriter._write_candles`
  (`orchestration_writer.py:328`, the LEGACY `storage_client.upload_bytes`-direct implementation with **no
  `ManifestWriter` call at all**) overrides `CandleWriteMixin._write_candles` (`candle_write_mixin.py:93`, the NEW path
  that routes to `canonical_writer.write_candle_parquet` → `ManifestWriter.record_captured(df=…)` → UTL 4-pillar
  write-gate) **by Python MRO**. Net: **every candle MDPS writes today gets ZERO manifest record (`record_captured` /
  `record_empty` / `record_failed`) and ZERO NaN-ratio / cluster-coverage write-gate** — the entire honest-coverage
  infrastructure in `canonical_writer.py` + `candle_write_mixin.py` is dead code in production. `OrchestrationCoordinator`
  (`orchestration_coordinator.py`) is never instantiated at runtime (0 hits for `OrchestrationCoordinator(`).
- **TradFi OHLCV passthrough still produces the 1440-NaN-bar shape.** `tradfi/ohlcv_passthrough.py:266
  _create_full_day_empty_output` returns `n_candles` rows (1440 for 1m, 96 for 15m) of all-NaN OHLC + `volume=NaN` +
  `market_state='closed'` on `tick_data.empty` — the **literal 2026-05-05 incident shape**, still in the live path.
  TradFi OHLCV adapters are the ONLY adapters that don't use `BaseCandleAdapter._make_empty_candle_output()` (the honest
  true-empty primitive) on empty input.
- **Banned/placeholder methods still present**: `_create_closed_market_candle` (duplicated in `orchestration_writer.py:65`
  AND `batch_workers.py:94` — double-SSOT, emits NaN-OHLC closed-market rows for TradFi non-trading days, written via the
  no-manifest legacy path), `_handle_empty_tick_data` (`batch_workers.py:192` — CLAUDE.md "No double SSOT" explicitly
  bans `_create_empty_output()` + `_handle_empty_tick_data()` co-existence), `_maybe_write_vix_gap_placeholder`
  (`orchestration_writer.py:417` — writes closed-market NaN candles for VIX 15m gap dates, contradicting the CLAUDE.md
  VIX-15m-source-layering rule "the gap is an accepted gap (denominator clip), not a coverage hole").
- **`schemas/output_schemas.py:57-66` makes OHLCV columns `nullable=True` for ALL data types incl. `trades`/`ohlcv`** —
  so `ParquetSchemaEnforcer` (the only validator in the live legacy path) does NOT reject all-NaN OHLC candles. The 4-pillar
  NaN-ratio gate WOULD catch them — but per the dead-path finding above, that gate is dead code.
- **Triple-SSOT for the candle pipeline**: (a) `CandleOrchestrationService` legacy `_write_candles` (live, no manifest),
  (b) `CandleOrchestrationService` canonical-writer path (dead code, has manifest+gate), (c) `CandleProcessingService` +
  `app/calculators/*` + `numba_kernels.py` (a separate streaming paradigm with its own NaN-OHLC generators and no
  manifest hooks; runtime-usage unclear — needs operator confirmation).
- **Reader-layout robustness — OK.** `live_workers.py` correctly handles per-instrument `{instrument_id}.parquet`, the
  legacy `ticks.parquet` chain-bundle sentinel, DeFi multi-instrument files, predicate-pushdown for large bundles. The
  2026-05-05 reader-drift *root cause* is fixed; the residual is the TradFi NaN-parquet write (above), not the reader.
- **Fix path**: (1) delete the legacy `orchestration_writer.py:328 _write_candles` (+ `:413 _write_candles_to_gcs`) so
  `CandleWriteMixin._write_candles` (canonical_writer → record_captured → write-gate) wins; (2) `tradfi/ohlcv_passthrough.py`
  return `_make_empty_candle_output()` on empty + caller routes to `record_empty`; (3) delete the duplicated
  `_create_closed_market_candle` + replace with `record_expected_empty(reason=EXPECTED_HOLIDAY/EXPECTED_WEEKEND)`; (4)
  `_maybe_write_vix_gap_placeholder` → `record_empty(reason=EXPECTED_KNOWN_SOURCE_GAP)` (pending the new-reason decision)
  or `record_expected_empty`; (5) flip `output_schemas.py` OHLCV nullability for `trades`/`ohlcv` to required (Phase
  2.B-ish — coordinate with `hard_schema_enforcement_2026_05_08.md`); (6) resolve the triple-SSOT — confirm which of
  (b)/(c) is live, delete the other two. This is **writegate Phase 2.A** scope (`_create_empty_output()` deletion +
  v3-path deletion) + the live-pipeline plan's MDPS phase. Cross-cutting; NOT slot-3's repo to fix.
- **Owner**: writegate Phase 2.A owner + Harsh slot 5 (live-pipeline MDPS phase) + Harsh slot 6 (QG sweep — add an
  AST/grep gate for `_create_empty_output` / `_handle_empty_tick_data` / `_create_full_day_empty_output` / direct
  `upload_bytes` candle writes that bypass `record_captured`).

## Per-asset-group case-D coverage map (the actual Track D deliverable)

> Categories per CLAUDE.md "Four-category empty-output decision": **A** = source returned 0 → `record_empty(reason=)`;
> **B** = source returned data, all off-day after interval filter → `record_failed(UpstreamTimestampBiasError)`; **C** =
> rows in window, all dropped on NaN/malformed fields → `record_failed(MalformedTickFieldError)`; **D** = source 0 BUT
> catalog says instrument alive AND day within venue hours → **NEW** write zero-activity carry-forward bars +
> `record_captured`. Case-D is wired in **ZERO** places workspace-wide today (`instrument_catalog` not threaded to any
> adapter; no UTL zero-activity-bar primitive exists).

### MTDS core tick path (CeFi spot/perp/options + book + derivative_ticker) — D1

- **Clean**: `base_adapter.py` (no banned placeholder); `engine/orchestrator.py:1014 PartitionedTickWriter.write_chunk`
  (empty → early-out; off-day → `validate_day_partition_alignment` → `UpstreamTimestampBiasError` = correct case-B; no
  NaN-bar logic — the 2026-05-05 class is guarded here); `umi_tick_provider.py` (every `return pd.DataFrame()` is correct
  honest-absence at the adapter level; VIX 15m layering correct); `hyperliquid_s3.py` (all-hours-empty → `[]` correct; the
  intra-row `None` padding of book levels 4-5 is legit per-real-row depth, NOT a fake placeholder); the 8 live-WS adapters
  (binance/bybit/okx/coinbase/deribit/* — pure normalisers, no batch-empty path).
- **case-A-correct: 2 code paths** (umi_tick_provider + hyperliquid_s3 adapter-level). **needs-case-D: ALL CeFi-tick
  data_types** — ohlcv_1m/ohlcv_15m/trades/book_snapshot_5/book_snapshot_25/derivative_ticker/liquidations(venue-level);
  wired in zero places; the natural seam is `engine/orchestrator.py:2092` (`_process_venue` zero-data branch) +
  `:2792-2849` (sentinel pass) — wire `instrument_catalog` into `process_ticks` + emit synthetic zero-activity bars via
  `PartitionedTickWriter` + `record_captured` when alive-in-hours, else `record_failed` (cefi can't legit-empty at
  instrument-day grain). **case-B/C-bug: 0** (off-day handled; no malformed-field path doing the wrong thing).
- **Bug (P0-1 above)**: 3 orchestrator `record_empty` callsites + rebuild_prediction_manifest lack `reason=`.
- **`_should_skip_shard` note**: doesn't exist as a named function in MTDS — the manifest pre-flight trust is inlined as
  `preflight_captured_dts` / `preflight_captured_atoms` / `_filter_data_types_by_atom_coverage` (`orchestrator.py:1721-1904`).
  (CLAUDE.md "phantom audit" rule references "`_should_skip_shard`" generically; in MTDS it's the atom-aware pre-flight.)

### MTDS DeFi handlers + DeFi adapters — D2

- **Centralized case-D hook**: `cli/handlers/_defi_manifest.py:57 DefiManifestRecorder` (imported by all 19 DeFi handlers
  + solana_defi). Today has only `record_captured`/`record_empty(reason=)`/`record_failed(error=)`; needs a 4th
  `record_zero_activity_captured(...)` method + an `instrument_catalog` reference (its own docstring lines 199-205 flags
  the date-aware classifier as a deferred follow-up of writegate Phase 3.D.5).
- **case-A-correct: 9** event-stream handlers (liquidation_events, liquidations, mev_events, bridge_events,
  governance_events, flash_loan_events, token_transfers, eigenlayer_rewards, position_data; + dex_swaps mostly-A with a
  subgraph-lag-vs-genuine-zero ambiguity flag). **needs-case-D: 9** continuous-series handlers (lst_rates ★ — on the
  `carry_staked_basis` lead-archetype critical path; staking_yields, lending_indices, evm_defi, perp_funding ★ — on
  `leveraged_funding_arb` critical path; gas_fee, vault_share_price, oracle_prices, dex_pools; + partially solana_defi for
  its LST-yield protocol mappings). **case-B/C-bug: 2** (`evm_defi_handler` + `lending_indices_handler._collect_protocol_chain`
  internal-try-returns-0 silently collapses source errors to `record_empty` instead of `record_failed` — case-C
  mis-recorded as case-A). **3 silent-skip-no-manifest-row gaps** (`lst_rates_handler.py:321` pre-token-genesis `continue`,
  `gas_fee_handler.py:182-191` pre-chain-start `continue`, `solana_defi_handler` unknown-protocol `continue`,
  `oracle_prices_handler` block-resolution-fail `continue`) — violate "every `(shard_key, day)` in the expected universe
  gets a manifest row"; should emit `record_empty(reason=EXPECTED_PRE_GENESIS_CHAIN)` etc. — `lending_indices_handler.py:323-332`
  is the reference impl for the pre-genesis case-A pattern.
- **No banned `_create_empty_output()` anywhere in DeFi handlers / `base_defi_adapter.py`** — the 1440-NaN-bar class is
  structurally absent on the DeFi side. The "empty marker" pattern (`write_defi_rows([], ...)` → zero-row parquet +
  `record_empty`) is the honest-absence pattern, not the fake-placeholder pattern.
- **Adjacent findings (flag for the writegate / shard-granularity owner, NOT case-D)**: (a) `write_defi_rows` does NOT add
  an `available_at` column + `DefiManifestRecorder.record_captured` calls `ManifestWriter.add(...)` not `record_captured(...)`,
  so `assert_available_at_present` / `LookaheadBiasError` never runs on DeFi shards → DeFi parquets may lack the per-row
  write-time `available_at` the workspace rule mandates → downstream features-onchain `LookaheadBiasError` strict-mode
  can't verify DeFi inputs; (b) `data_type="lending_indices"` is written by TWO handlers (`lending_indices_handler.py` AND
  `evm_defi_handler.py:55`) → potential double-SSOT (two handlers racing on the same `(protocol, chain, data_type, day)`
  row_key); similarly `liquidations` vs `liquidation_events` look like overlapping data_types; (c) `chain=""` coarse-marker
  manifest rows (`perp_funding_handler` GMX, `oracle_prices_handler` PYTH) → shard-granularity drift (manifest can't
  distinguish per-chain coverage); (d) `lst_rates` is arguably a bundle (one parquet packs all LST tokens) — if you want
  strict per-token cluster coverage you'd add a DeFi entry to `BUNDLED_DATA_TYPES`; currently not done, low priority.

### MTDS TradFi + Prediction + Sports — D3

- **Clean**: `base_tradfi_adapter.py` / `base_prediction_adapter.py` / `base_sports_adapter.py` (no banned placeholder);
  `databento_adapter.py:798-972` (the 2026-05-05 partial-bundle silent-drop is FIXED via the `failed_per_dt` side-channel
  — minor hardening: make `failed_per_dt` required so a new caller can't re-open the silent-drop class); `umi_tick_provider.py`
  VIX 15m route (FIXED — routed to `_fetch_yahoo_vix_15m` BEFORE the Databento `_DATABENTO_SUPPORTED_DATA_TYPES` filter,
  closing the legacy "VIX silently emptied via filter" category-3 bug).
- **case-A-correct: 7** (the 3 base adapters + umi VIX route + umi Databento-supported filter + databento symbol-canonicalisation
  row-drop + rebuild_prediction_manifest skip/freshness). **needs-case-D: 2** in-scope adapters (`polymarket_adapter.py:540-759`
  + `kalshi_adapter.py:189-351` — alive-market-but-source-zero → currently `continue` past the market silently; should
  write zero-activity carry-forward bars (prior mid/best-bid/best-ask) + `record_captured`; per-market lifecycle bounds
  `[market_created_at, settlement_time)` ARE respected — pre-`market_created_at` and post-`settlement_time` are correctly
  case-A `EXPECTED_INSTRUMENT_NOT_LISTED` / `EXPECTED_INSTRUMENT_DELISTED`) **+ 1 cross-cutting** (orchestrator finalize/sentinel
  fan-out — the convergence point for sports/tradfi/prediction case-D). **case-B/C-bug: 0** (databento partial-bundle +
  VIX-15m-filter bugs both fixed).
- **★ Scope re-clarification (D3)**: **sports HISTORICAL capture (footystats / api_football / soccer_football_info /
  understat / transfermarkt / open_meteo) is NOT in MTDS** — it lives in instruments-service / URDI per CLAUDE.md "MTDS is
  for market data only; reference data → instruments-service". The MTDS `market_interface/sports/` is **live odds polling**
  (`get_odds() -> list[CanonicalOdds]`, not a parquet data_type), and `ODDS_SNAPSHOT`/`ODDS_MOVEMENT`/`ARBITRAGE` are NOT
  MTDS data_types. So the sports per-fixture-bundle case-D zero-activity work belongs in instruments-service's per-fixture
  handler, not MTDS. **Track D's sports half should be re-scoped to instruments-service** — flag for the wave3x plan owner.
- **Bug (P0-1 above)**: `engine/orchestrator.py:2671/:2808/:2849` + `rebuild_prediction_manifest.py:351` lack `reason=`;
  TradFi non-trading-day pre-skip `continue`s with no row instead of `record_expected_empty(reason=EXPECTED_HOLIDAY/...)`.
- **Adjacent**: `rebuild_prediction_manifest.py` shard-key omits `canonical_question_group` (uses `(date, venue, chain,
  instrument_type, data_type, underlying)`) — known dual-write (orchestrator owns the canonical bundle via
  `record_captured_from_counts`, rebuild owns per-instrument backfill rows); flagged in CLAUDE.md as the
  `wave2_polymarket_record_captured_from_counts_2026_05_09` successor; not a Track-D bug.

### MDPS (candle-aggregation boundary) — D4

See P0-2 above for the headline findings. Per-adapter case-D map:
- **case-A-correct: 15** — all CeFi MDPS adapters (`trades_adapter`, `book_snapshot_adapter`, `derivative_adapter`,
  `futures_chain_adapter`, `liquidations_adapter`, `options_chain_adapter`), all DeFi (`swap_adapter`, `liquidity_adapter`,
  `fx_rate_adapter`, `market_state_adapter`), all sports (`arbitrage_adapter`, `odds_movement_adapter`, `odds_snapshot_adapter`,
  `bucket_assignment_adapter`), prediction `trades_adapter` — every one uses `BaseCandleAdapter._make_empty_candle_output()`
  on source-empty + typed-error classes (`UpstreamTimestampBiasError` / `MalformedTickFieldError`) for B/C; A/B/C handling
  is uniform and healthy across these. `live_workers.py:613 _process_all_timeframes` does the A/B/C split correctly
  (`record_empty_for_shard(reason=SOURCE_RETURNED_ZERO)` / `record_failed_for_shard`).
- **needs-case-D: ~16** — every adapter emitting a full-day candle grid has the sparse-interval-NaN-instead-of-zero-activity-bar
  gap (the 15 above + the 3 TradFi OHLCV adapters); plus `base_adapter._fill_empty_candles(fill_method="nan")` default for
  price columns is the case-D gap. Natural case-D seat: `live_workers.py:613-810 _process_all_timeframes` (`else:` branch at
  `:748`, currently always `record_empty_for_shard`) — if `instrument_catalog.is_alive(...) and venue_calendar.is_open(...)`
  → new `write_zero_activity_bars(...)` + `record_captured`. Needs `instrument_catalog` wired at adapter/orchestrator
  construction (Wave 2/3 of writegate Phase 3.D.5, "pending").
- **case-B/C-bug: 0** in the adapters. **But case-A-VIOLATION: 3** (the 1440-NaN TradFi `_create_full_day_empty_output`;
  the `_create_closed_market_candle` NaN rows; the VIX gap NaN placeholder) — see P0-2.
- **Q3 (new reason)**: VIX 15m gap → candidate `EXPECTED_KNOWN_SOURCE_GAP` (see TL;DR #2).

### features-service set 1 (common + volatility + cross_instrument + multi_timeframe) — D5

**Commit audited**: `52898f5a` (mid-consolidation; `features_service/common/` is skeleton-only `__init__.py` — the
cross-family lift-to-`common`/UTL is deferred per `features_repo_consolidation_2026_05_08.md` Phase 5. The write-gate IS
already a UTL primitive `FeatureWriteGate`/`WriteGateConfig`, consumed by all 3 subdirs).

- **No banned `_create_empty_output()` anywhere in scope** ✓ (grep: 0 hits).
- **Q2 (new shard atom dimension?)**: NO. Features add `feature_group` (already a v5 manifest column + the new
  `feature_family` kwarg). `zero_activity` / `is_carry_forward` should be a per-row column on the feature parquet, not a
  new shard-key axis.
- **Q3 (new reason?)**: Likely NO — `SOURCE_RETURNED_ZERO` / `EXPECTED_PRE_SOURCE_COVERAGE_START` / `EXPECTED_PRE_GENESIS_CHAIN`
  / `EXPECTED_HOLIDAY` / `EXPECTED_WEEKEND` propagated from upstream cover the feature-relevant cases. (D5 didn't read the
  full `EMPTY_CONFIRMED_REASONS` registry — defer the final call.)
- **case-A-correct: ~6** (volatility kernel calcs return NaN/None ✓; `volatility/core/dependency_checker` fail-fast ✓;
  `cross_instrument/_ingest_delta_one` fail-fast roughly-✓; `multi_timeframe/intraday_regime._empty_output` null-fill ✓;
  `multi_timeframe` PIT/lookahead strict-raise ✓; both base-calculators raise-on-empty + no banned placeholder ✓).
- **needs-case-D: 1** (vol-smile — **but it lands at MTDS/MDPS not features-volatility**: this layer consumes whatever
  chain parquet the upstream wrote; a zero-volume-but-quoted strike is already visible here. If the MDPS bar for an
  illiquid strike is *missing*, that's the upstream's case-D, not this layer's).
- **The bigger "no manifest row on empty" gap (~7 sites — #1/#2/#3/#7/#9/#12/#13)**: every features orchestrator
  (`volatility/engine/orchestrator.py`, `cross_instrument/cli/handlers/batch_handler.py`, `multi_timeframe/engine/orchestrator.py`)
  uses the legacy `ManifestWriter.add(...)` (presence-only) path; the 4-pillar `record_captured` is deferred to
  features_repo_consolidation Phase 5 "multi-day df-flow refactor". Until then: an empty day → **no manifest row at all**
  (manifest can't tell "honest absence" from "service never ran"); a partial/garbage non-empty parquet passes silently.
  And `record_empty` / `record_expected_empty` / `record_failed` are never called from any features orchestrator.
- **case-B/C-bug: ~5**:
  - `volatility/engine/orchestrator.py:340-374` — an empty options-chain parquet → `_make_error_result("Empty data")`
    marks the chain FAILED + drops it from the manifest entirely. Should be `record_empty(reason=SOURCE_RETURNED_ZERO)` —
    as-is it's indistinguishable from a read bug.
  - `volatility/engine/orchestrator.py:734+` — `if not results: return pl.DataFrame()` after groupby conflates case-A
    (no rows) with case-C (rows present, all dropped post-groupby on malformed `timestamp`/`days_to_expiry`).
  - `cross_instrument/app/calculators/paired_dispatch._ingest_delta_one_concat` — silently swallows bucket-unreachable
    `OSError/RuntimeError/ValueError` → `continue` → could mask a category-3 path/reader drift bug as honest absence.
  - **★ `cross_instrument/app/calculators/{cross_asset_correlation.py:330, cross_venue_calculator.py:338,
    cross_instrument_dynamics.py:275, cme_gap.py:160}` `_create_empty_features` / `_empty_result` write `np.zeros(n)` for
    *continuous* features** (`correlation_*=0`, `beta_adjusted_return=0`, `spread_to_*=0`, `cme_gap_*=0`) when input is
    insufficient (<2 bars / <2 instruments / <2 venues / aligned rows < beta_window). `correlation_50 == 0.0` for a
    1-instrument day is a *confidently-wrong label*, not honest absence — manifest sees `captured` row_count=N; downstream
    ML trains on garbage `0`s. **FIX**: `np.full(n, np.nan)` for continuous columns (keep binary event flags at 0). Same
    pattern across all 4 → candidate for a shared helper at the Phase-5 common lift; mirror `multi_timeframe/calculators/
    intraday_regime.py:200 _empty_output` (the right null-fill shape). **Highest-confidence features-side correctness bug.**
  - alignment-mismatch in `volatility/core/feature_writer._check_alignment` + `multi_timeframe` returns False without
    `record_failed(UpstreamTimestampBiasError(...))` — just logs ERROR.
- **`record_empty` documented-but-not-wired**: `paired_dispatch.py` / `paired_spec_resolver.py` docstrings say the caller
  "emits `record_empty(reason=SOURCE_RETURNED_ZERO)`" — no code path does (partial state per `carry_tracer_phase_9` handoff).
- **No dependency pre-flight in cross_instrument or multi_timeframe** — only volatility has a `DependencyChecker`. The
  `FileNotFoundError` in cross_instrument's ingest is a partial substitute; multi_timeframe has nothing structured.
- **`available_at` not stamped** — features use `timestamp_out = timestamp + SYNTHETIC_DELAY_MS` as their availability
  column, not the canonical per-row write-time `available_at` per `unified_trading_library.availability_stamping.stamp_available_at_*`.
  cross_instrument's write-gate has `enable_leakage_check=False` while `enable_pit_check=True`. mtf's PIT check (strict
  raise, correct) only runs when `timestamp` + `timestamp_out` are both present; non-PIT feature groups pass unchecked.

### features-service set 2 (delta_one + calendar + commodity + onchain + sports) — D6

**Commit audited**: `52898f5a` (same mid-consolidation state).

- **No banned `_create_empty_output()` anywhere in scope** ✓.
- **Q2 (new shard atom dimension?)**: NO. onchain key `(asset_group, chain, venue/protocol, data_type, instrument_id_or_protocol_id, day, feature_group)`, delta_one `(asset_group, venue, data_type, instrument_type, instrument_id, day, feature_group, timeframe)`, sports `(asset_group=sports, source, data_type, league_id, day, feature_group)` — all present. Sports `fixture_id` grain is the open implementation question for case-D ("this *specific* fixture was catalog-active, odds source dark for it") but `fixture_id` is already named in the CLAUDE.md shard matrix → documented, not new. `zero_activity` is a per-row flag, not a manifest column.
- **Q3 (new reason?)**: NO new vocabulary needed — the gap is *usage*: onchain/delta_one orchestrators never call `record_empty`/`record_failed`/`record_expected` at all; calendar calls `record_empty` untyped (no `reason=`); sports always uses the catch-all `SOURCE_RETURNED_ZERO` instead of the more-specific `EXPECTED_*`.
- **★ HIGHEST-SEVERITY (D6) — `commodity/cli/handlers/batch_handler.py:251-290` PHANTOM MANIFEST ROW BUG**: `_write_manifest` calls `writer.add(processing_date, row_count=1, feature_group=c, feature_family="commodity")` for **every (commodity, day) in the range regardless of whether `_process_day` succeeded**, then `writer.write()`. A fully-failed run still populates `captured`-shaped rows for the whole range → `_should_skip_shard` then permanently skips them. **FIX**: thread per-day success into `_write_manifest`; `add()` only succeeded days, `record_failed` the rest. Exactly the phantom-row class CLAUDE.md's "Manifest phantom audit" rule warns about.
- **Half-shipped honest-coverage gate (sports)**: `sports/exporters/derived_features_exporter.py` `check_calculator_coverage` computes per-calculator `UPSTREAM_MISSING`/`OUT_OF_COVERAGE`/`READY` verdicts into `quality_tracker` — but `quality_tracker` is NEVER returned to `batch_handler` (only `_log_quality_summary`); the per-calculator `record_failed("upstream_missing:...")` the gate's docstrings (`:637-639/:654/:797/:813/:851`) promise never fires. batch_handler only does coarse shard-level `record_empty(SOURCE_RETURNED_ZERO)`. **FIX**: `export_derived_features` returns `(df, quality_tracker)`; batch_handler emits per-calculator `record_failed`/`record_empty`.
- **Masking-absence bugs (sports calculators consumed by `derived_features_exporter`)**:
  - `sports/calculators/weather_calculator.py:157-160` — `pd.to_numeric(...).fillna(20.0)` for temp, `0.0` wind, `50.0` humidity, `50.0` cloud → derived `weather_severity`/`is_hot`/`is_adverse` compute on fabricated weather. Should leave NaN (contrast: `sports/pipeline/fixture_features.py` correctly keeps weather NULL + `weather_source="none"`).
  - `sports/calculators/odds_calculator.py:300-306` — `pd.to_numeric(home_odds).fillna(0.0)` then `np.where(>0, 1/x, 0.0)` → 0-odds rows get `implied_prob=0.0`/`overround=0.0`/`market_vig=0.0`/`fair_prob=0.0`/`home_edge=0.0` etc. — fabricated zero-valued features that look populated. Should be NaN. (NOTE: the *separate* `odds_features_exporter.py` for the `odds_features` shard does it right — `available_at` from `bm_time`, NaN for missing odds; the bug is in `odds_calculator.py` which feeds `derived_features`.)
  - **Systemic** — `h2h_calculator.py:112-267`, `manager_calculator.py:153-390`, `poisson_xg_calculator.py:173-237` (`fillna(1.0)`), `venue_context.py:255` (`fillna(0.5)`), `meta_features_calculator.py:172-190` (`fillna(_DEFAULT_CONFIDENCE)`), `relative_context_calculator.py:79`, `ht_features.py:300` — pervasive `pd.to_numeric(<historical match stat>, errors="coerce").fillna(<magic>)`. A NaN in a historical-goals column means the stat was malformed/missing; `fillna(0.0)` pretends it was a goalless draw → corrupts H2H aggregates / manager records / Poisson rate estimates. Recommend an audit pass: keep NaN, let pandas `.mean()` skip-NaN. (Contrast the GOOD pattern: `sfi_progressive_calculator.py:460`, `footystats_predictions_calculator.py:95`, `squad_value_calculator.py:268`, `travel_calculator.py:295`, `european_fatigue_calculator.py:274`, `transfer_window_calculator.py:676` all emit all-NaN shape-correct rows on no-upstream.)
- **onchain/delta_one never record honest-absence rows**: `onchain/engine/orchestrator.py:1186` (`days_with_data == 0` → `FEATURE_GROUP_NO_DATA` event + `return False`, no manifest write) and `delta_one/engine/orchestrator.py:602` (no candles / insufficient / >50% NaN → `return False`, manifest only at `:292` when `success_count > 0`). The day silently disappears from data-status (looks "never attempted"). onchain calc-failure handlers (`:511-517` etc.) `return pl.DataFrame()` on `(ConnectionError, TimeoutError, OSError, ValueError)` → conflates case-C (calc failed on present rows) with case-A (source zero). Both have proper `DependencyError(fail_fast=True)` pre-flight ✓ (onchain `batch_handler.py:79`, delta_one `:134`).
- **calendar**: HAS `record_empty(row_key, attempted_at=)` + `record_failed` + lookup-skip — BUT `record_empty` is called with NO typed `reason=` kwarg (unlike sports). Add `reason="SOURCE_RETURNED_ZERO"` (economic_events). The `open=high=low=close=1.0` dummy-OHLCV scaffold in `_generate_time_features` is intentional (time-of-day features need a pandas index) — NOT the banned placeholder pattern, but worth a comment so a casual reader doesn't mistake it.
- **available_at midnight-UTC notes (sports/onchain)**: (a) `sports/cli/handlers/batch_handler.py:146-161 _ensure_timestamp` fills `timestamp` (NOT `available_at`) with midnight-UTC — harmless for the PIT/leakage gate (reads the separately-stamped `available_at`) but it IS the shim writegate Phase 2.C schedules for deletion; **DOUBLE-SSOT**: duplicate definition at `sports/cli/batch_write.py:39`. (b) `sports/cli/handlers/batch_handler.py:270-275 _stamp_available_at` for the `fixtures` table when `kickoff_utc` absent falls back to `available_at = target_date.isoformat()` = midnight UTC (should be `kickoff - 7d`; degenerate-input fallback, low severity). (c) onchain doesn't stamp `available_at` at all — relies on the real on-chain block `timestamp` + an end-of-day PIT boundary; the workspace "available_at is per-row write-time" rule would want an explicit `available_at` column on onchain feature parquets (gap, not a bug).
- **Reference-quality impl**: `sports/pipeline/fixture_features.py:314-371` — `available_at = kickoff_utc` (real per-source rule, falls to `computed_at` for degenerate records), `_null_row` keeps ALL columns NULL + `weather_source="none"`. Other sports calcs should follow this.
- **case-A-correct: ~7** (calendar orchestrator modulo untyped reason; commodity fetch-layer honest-absence + fail-loud; commodity factor base validation; sports `record_empty`/`record_failed` shard-level wiring; sports all-NaN-shape calculators — the good pattern; `sports/pipeline/fixture_features.py` reference quality; `sports/pipeline/_asof.py` pure transform; delta_one `nan_handler` NaN-preservation). **needs-case-D: ~2-3** (sports `odds_features`/`derived_features`/`fixture_features` shards when a catalog-active fixture has no odds → carry-forward prior bookmaker line; onchain `lst_yields`/delta_one illiquid-instrument *would* be case-D but neither service even records the honest-absence row today, so they're 2-3 steps short). **case-B/C-bug: ~6** (commodity phantom-row ★; weather fillna; odds fillna; systemic sports magic-fill; onchain calc-failure-returns-empty; sports can't distinguish no-fixtures from missing-fixtures-parquet → potential case-2 mishandling).
- **No `record_expected`/`record_expected_empty` anywhere in these 5 subdirs** — coverage % denominators are presence-only for onchain/delta_one, shard-attempt-based for calendar/sports.

## Combined per-asset-group case-D coverage tally (all 6 reports)

| Surface | case-A-correct | needs-case-D | case-B/C bug | banned `_create_empty_output()` | Notable current bug |
| --- | --- | --- | --- | --- | --- |
| MTDS core tick path | 2 | all CeFi-tick data_types (0 wired) | 0 | none | P0-1: 3 orchestrator `record_empty` callsites lack `reason=` |
| MTDS DeFi handlers | 9 | 9 | 2 | none | 3 silent-skip-no-manifest-row gaps (lst_rates/gas_fee/solana_defi `continue`) |
| MTDS tradfi/prediction/sports | 7 | 2 (polymarket/kalshi) + 1 cross-cutting | 0 | none | P0-1 (same); sports HISTORICAL capture is in instruments-service NOT MTDS — re-scope |
| MDPS | 15 | ~16 | 0 (but 3 case-A-VIOLATION NaN-placeholder paths) | none, but `_handle_empty_tick_data` + `_create_closed_market_candle` (dup×2) + `_maybe_write_vix_gap_placeholder` are equivalents | P0-2: canonical-writer path DEAD on live path; 1440-NaN TradFi `_create_full_day_empty_output` still live; `output_schemas.py` nullable=True for trades/ohlcv; triple-SSOT candle pipeline |
| features set 1 (common/vol/cross_inst/mtf) | ~6 | 1 (vol-smile, lands at MTDS/MDPS) | ~5 | none | cross_instrument `_create_empty_features` × 4 → `np.zeros(n)` for continuous features (should be `np.full(n, np.nan)`); presence-only manifest (`ManifestWriter.add`); `record_empty` documented-but-not-wired in paired_dispatch |
| features set 2 (delta_one/cal/comm/onchain/sports) | ~7 | ~2-3 | ~6 | none | commodity phantom manifest-row bug ★; sports half-shipped quality-gate; sports calculators `fillna(magic)` masking-absence (weather/odds/h2h/manager/poisson); onchain/delta_one never record honest-absence rows |

**Workspace-wide case-D status: wired in ZERO places.** No `instrument_catalog` is threaded to any adapter/orchestrator; no UTL `zero_activity_bars` primitive exists. Per writegate Phase 3.D.5 the catalog-aware write-gate (Wave 2/3) is "pending" — that's the prerequisite.

## Why this matters / what to do

- **Anti-sequencing**: Track D forces **no manifest schema column / shard-atom change** → the case-D *implementation* can
  safely defer post-cutover. The ONE candidate change with an anti-sequencing flavour is the `EXPECTED_KNOWN_SOURCE_GAP`
  reason — Ikenna slot 5 + slot 1 decide Phase-1-now-vs-defer. Recommend Phase-1-now (tiny additive enum, real consumer).
- **P0-1 (MTDS blank-reason)** and **P0-2 (MDPS dead write-gate + 1440-NaN TradFi passthrough + banned placeholders)** are
  the actually-urgent items — both are LIVE correctness bugs, both are writegate Phase 2.A/2.E scope, both compose with
  Harsh slot 5 (live-pipeline) + Harsh slot 6 (QG sweep). They are NOT slot-3's repos to fix per the Track D read-only
  brief — escalated here for the right owner to pick up.
- **Case-D wiring** = ~30 adapters/handlers + a new UTL `zero_activity_bars` primitive + `instrument_catalog` threading.
  Defer post-cutover OR fold into a named Wave 3.M follow-up plan. Sports half of Track D re-scopes to instruments-service
  (the historical sports capture isn't in MTDS).

## Recommended decision

> **✅ OPERATOR DECISIONS 2026-05-11** (Ikenna, via main orchestrator slot 1):
>
> 1. **`EXPECTED_KNOWN_SOURCE_GAP` enum value → APPROVED for Phase 1** (lands before 2026-05-15 freeze gate). Reason: real consumers exist (VIX 15m mid-history gap currently mis-written as NaN-OHLC placeholder; sports `KNOWN_COVERAGE_GAPS` ranges) and the addition is tiny + additive. Routed for implementation to `manifest_schema_final_gate_2026_05_09.md` (the canonical v8 + UAC `EmptyConfirmedReason` owner per the same-day F3 decision).
> 2. **P0-2 MDPS dead write-gate + 1440-NaN TradFi passthrough → APPROVED for Phase 1** (as early as possible; lands before 2026-05-15 freeze gate). 6-step fix path per § P0-2 above. Routed to: writegate Phase 2.A/2.E owner + Harsh slot 5 (live-pipeline MDPS phase) + Harsh slot 6 (QG AST gate for banned placeholders). Cross-side ping to harsh-main filed.
> 3. **P0-1 MTDS blank-reason** → already SHIPPED 2026-05-11 by Harsh slot 6 at `market-tick-data-service@3da026d` (per § P0-1 above).
> 4. **Case-D implementation** (~30 adapters/handlers) → **deferred post-cutover**. Forces no schema change so sequencing-safe. Wave3x plan owner: re-scope Track D's sports half to instruments-service + add a Wave 3.M follow-up plan for the case-D implementation. Slot-1 will note in master plan's continuous-verification column at next refresh.
>
> Original recommendations preserved below for reference.

1. **Ikenna slot 5 + slot 1**: (a) approve/reject `EXPECTED_KNOWN_SOURCE_GAP` for the Phase 1 schema window; (b) confirm
   case-D implementation defers post-cutover (or name the follow-up plan); (c) note in the
   `code_freeze_migrate_backfill_sequencing` anti-sequencing audit row that Track D's audit found "no new shard atom
   dimension; one candidate new reason (decision pending)".
2. **writegate Phase 2.A/2.E owner + Harsh slot 5**: pick up P0-1 (MTDS orchestrator `record_empty` reason= fix) + P0-2
   (MDPS dead-write-gate + TradFi OHLCV passthrough + banned placeholders). These are the urgent ones.
3. **Harsh slot 6 (QG sweep)**: add an AST/grep QG gate for banned placeholder methods (`_create_empty_output`,
   `_handle_empty_tick_data`, `_create_full_day_empty_output`) + direct-`upload_bytes`-candle-writes-that-bypass-`record_captured`.
4. **wave3x plan owner**: re-scope Track D's sports half to instruments-service; add a "case-D implementation" follow-up
   todo (deferred post-cutover) to wave3x or a new Wave 3.M plan.
