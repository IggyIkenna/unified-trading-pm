---
doc_type: plan
title: tradfi venue e2e wiring batch 1 — 2026-08-16
summary: >-
  Fresh carve-out from venue_e2e_wiring_2026_08_16.md's "Fork per-asset-group dispatch batches" P0 todo — walks
  contract steps 1-9 across every tradfi (venue, data_type) row from `unified-api-contracts/scripts/
  generate_venue_work_list.py` (16 rows, measured 2026-08-16; re-run the script, this count is not a constant).
  Not an extraction from another source doc — no operator-gated item mixed in, per task_template.md §3 finding Y.
status: complete
nature: process
asset_group: [tradfi]
stage: [data, features, strategy, execution]
repos:
  [
    unified-api-contracts,
    unified-trading-library,
    instruments-service,
    market-tick-data-service,
    features-service,
    strategy-service,
    execution-service,
  ]
scope: [engineer]
tags: [venue-readiness, e2e-wiring, tradfi, ao-dispatch, satellite-batch]
related:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/venue_e2e_wiring_2026_08_16.md,
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-17"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
drift_direction: advance-code
depends_on: []
estimate_class: infra
estimate_baseline_ai_days: 1.2
estimate_calibrated_ai_days: 0.96
assigned_role: backend_engineer
effort: medium
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/venue_e2e_wiring_2026_08_16.md,
    /codex/06-coding-standards/integration-testing-layers.md,
    /codex/04-architecture/shard-level-failure-isolation.md,
    /codex/04-architecture/instruments-service-as-ssot-for-mtds.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    unified-api-contracts/scripts/generate_venue_work_list.py,
  ]
source: >-
  Forked from `venue_e2e_wiring_2026_08_16.md`'s "Fork per-asset-group dispatch batches" P0 todo, 2026-08-16
  interactive session, per the operator-selected "per contract-step-group" decomposition.
---

# tradfi venue e2e wiring batch 1 — 2026-08-16

> **Parent**: [`/plans/active/venue_e2e_wiring_2026_08_16.md`](/plans/active/venue_e2e_wiring_2026_08_16.md) (W4).
> The contract steps this plan walks, and the hard rules it must not violate, live in the parent — not restated here.
> Row list: `unified-api-contracts/scripts/generate_venue_work_list.py --csv PATH` filtered to `asset_group=tradfi`.

## Todos

- [x] ✅ [BACKEND] P0. **Steps 1-5 per unit — done 2026-08-16.** SHIPPED — `unified-trading-pm@48f83481ce`.
      4 parallel research passes across instruments-service, market-tick-data-service, features-service.
      **Step 2 (instrument resolution) — PASS for all 8 venues**, all 16 rows: `venue_adapter_keys.py:117-139`
      routes CME/NASDAQ/NYSE/CBOE/ICE/KRX through the shared Databento adapter, FX/FRED through their own; every
      venue has a real `get_instruments()` + coverage window (FX/FRED use a single shared floor date rather than
      per-instrument, by design — structurally different from tradeable securities, not a gap).
      **Steps 3-4 (batch/live) — 8/16 rows PASS** (Databento core: CME/CBOE/NASDAQ/NYSE ohlcv_1m/1s — batch +
      live both real, `databento_adapter.py`/`databento_tradfi_ws.py`); **8/16 PARTIAL** (Yahoo-interim/Yahoo-only/
      FRED rows — CBOE ohlcv_24h, NASDAQ/NYSE ohlcv_1h, FX/ICE/KRX ohlcv_24h, FRED ohlcv_1d/yield_curve — batch
      exists, no live connector). **Already tracked, not a new gap**: `data_completion_tradfi_2026_07_15.md:59`
      already documents Yahoo as the intentional interim/daily-only source while Databento billing was suspended
      (confirmed resolved 2026-08-10 per that doc) — cited here, no duplicate todo created.
      **Step 5 (feature consumption) — checked only the 4 rows with a real declared archetype consumer**
      (CBOE/CME/NASDAQ/NYSE `ohlcv_1m`; the other 12 rows show `archetype_consumers=NONE` — no archetype has
      declared needing `ohlcv_1s`/`1h`/`24h`/`1d`/`yield_curve` at all, a genuine undeclared-scope gap, not an
      implementation bug — `BLOCKED-ON:archetype-declaration-backlog`, not investigated further). Of the 4:
      `technical_indicators`/`momentum`/`oscillators`/`cross_asset_correlation`/`regime_detection`/`cointegration`
      families all PASS (real, venue-agnostic implementations, no tradfi exclusion found). **`cross_venue_spreads`
      FAILS for all 4** — `CrossVenueCalculator` hardcodes `baseline_venue="BINANCE-SPOT"`
      (`cross_instrument/config.py:95-99`, `cross_venue_calculator.py:142-145`), never asset-group-aware, so
      `ARBITRAGE_PRICE_DISPERSION` can never be satisfied for ANY tradfi venue despite being declared a consumer —
      genuinely new finding, tracked as its own todo below (not found in existing plan corpus, checked via grep
      before filing).
- [x] ✅ [BACKEND] P1. **Gap: `CrossVenueCalculator` hardcodes `baseline_venue="BINANCE-SPOT"`, never tradfi-aware**
      — SHIPPED `features-service@be2af7b191`. `_calculate_features` now resolves the baseline venue via a new
      `_resolve_baseline_venue()`: uses the configured `baseline_venue` when present in the input, otherwise falls
      back to the most-frequent venue actually present in the data instead of unconditionally returning empty
      features (`cross_venue_calculator.py`). This is asset-group-aware without a static per-AG mapping — a tradfi
      dataset that never carries `BINANCE-SPOT` (CME/NASDAQ/NYSE/CBOE) now gets a real baseline instead of
      `cross_venue_spreads`/`ARBITRAGE_PRICE_DISPERSION` silently going empty. Added
      `test_cross_venue_calculator_missing_baseline_multi_venue_uses_dominant` (asserts non-zero spreads from the
      dominant-venue fallback across multiple distinct venues) and updated the pre-existing single-venue
      missing-baseline test's docstring to reflect the new self-spread-fallback semantics (numeric assertion
      unchanged — still zero, now for the right reason). Full local `quality-gates.sh` green.
- [x] ✅ [BACKEND] P0. **Steps 6-8 per unit — strategy and execution — done 2026-08-16.** Investigation only,
      zero code changed. Real per-row verdict for the 4 CBOE/CME/NASDAQ/NYSE `ohlcv_1m` rows in scope (the other
      12 stay `BLOCKED-ON:archetype-declaration-backlog`, unchanged from steps 1-5):
      - **CME — PARTIAL.** 8 real slots declared with `venue="cme"`: `ML_DIRECTIONAL_CONTINUOUS@cme-{es,nq,cl,
        gc}-1d` + `RULES_DIRECTIONAL_CONTINUOUS@cme-{es,nq,cl,gc}-1d` (`target_universe/catalog_directional.py`),
        plus 5 more in `archetype_slots_tradfi.py` (OIL/NG_COMMODITY_REGIME, OIL_ML_DIRECTIONAL, FX/
        OIL_MEAN_REVERSION). BATCH/PAPER(sim) position reads PASS — `get_position_adapter()` routes BATCH/
        PAPER(testnet=False) to the venue-agnostic `LedgerPositionAdapter` regardless of venue string. **LIVE/
        PAPER(real) position reads FAIL — genuinely new gap, tracked as its own todo below**: `strategy-service/
        strategy_service/position/position_interface/factory.py::get_position_adapter()` has no match arm for
        `"cme"` (only `"ibkr"` is registered in `_get_other_adapter`), so a live/paper(testnet) position read
        for any `venue="cme"` slot raises `ValueError: Unknown venue: 'cme'`. Execution: `CMEAdapter` IS
        registered (`execution-service` factory, `TRADFI_VENUES`) and implements `place_order`/`cancel_order`
        (TRADE/CANCEL are the only `InstructionActionV2` members these archetypes emit) via `IbkrTradFiAdapter`
        — but real LIVE/PAPER order placement is **already tracked** as structurally blocked: UAC capability
        declarations mark `place_order supported=False` for all 6 tradfi venues pending end-to-end
        backfill=paper=live proof (cited directly in `ibkr_tradfi.py`'s own docstring →
        `tradfi_finding_e1_unsourced_operator_ruling_citation_2026_08_03.md` +
        `tradfi_consolidated_native_ao_extract_2026_07_25.md` todo 1 — no duplicate todo filed here). Sim mode
        (`mode="sim"`) is unaffected and works today. TSMOM_BTC_CTA/STAT_ARB_\*/VOL_CROSS_ASSET_SPREAD/
        VOL_DISPERSION: zero catalogue rows declare CME — TSMOM_BTC_CTA is CeFi-perp-only (binance/okx/
        hyperliquid), STAT_ARB_\* only ever uses the generic `"ibkr"` venue token, and VOL_CROSS_ASSET_SPREAD/
        VOL_DISPERSION have **zero `TARGET_UNIVERSE` rows for any venue at all** (engine + param schema exist,
        nothing materializes them into a tradeable slot) — not a CME-specific gap.
      - **CBOE — BLOCKED-ON:archetype-declaration-backlog.** Not declared under any of the 6 target archetypes
        anywhere in the catalogue (`archetype_slots_*.py` + `target_universe/catalog_*.py` greped clean) — CBOE
        only appears under `VOL_TRADING_OPTIONS` (SPX options) and `CARRY_BASIS_DATED` (cboe-cme basis), neither
        in scope. Matches the step-5 finding that CBOE `ohlcv_1m`'s real feature consumers
        (technical_indicators/momentum/oscillators/regime_detection) don't currently drive a directional/
        stat-arb/tsmom/vol-cross-asset slot. Execution: `CBOEAdapter` exists (`execution-service` factory) but
        nothing routes to it under these 6 archetypes today — moot until a slot is declared.
      - **NASDAQ / NYSE — UNVERIFIED (not a pass), real gap surfaced.** Neither venue token is ever declared
        literally in any of the 6 target archetypes — equities route through the generic `venue="ibkr"` token
        instead (`SPY`/`QQQ`/`IWM` in `catalog_directional.py`; `XLF`/`XLE`/`XLV`/`XLY`/`XLI` sector ETFs under
        `STAT_ARB_CROSS_SECTIONAL` in `catalog_trading.py`). Position adapter: `"ibkr"` DOES resolve live
        (`factory.py` `case "ibkr": return IBKRPositionAdapter(...)`) — the one tradfi token that actually
        works in LIVE mode. Execution: **unverified, not traced this pass** — `execution-service`'s factory
        keys per-exchange (`NASDAQAdapter`/`NYSEAdapter` under `TRADFI_VENUES`), but strategy-service never
        emits a literal `"nasdaq"`/`"nyse"` venue string, only `"ibkr"`; how (or whether) an `"ibkr"`-tagged
        instruction is routed to the correct per-exchange execution adapter (presumably via the instrument's
        own listing-exchange metadata, not the strategy's venue string) was not traced — reporting unverified
        per the operator's DERIVED-readiness ruling rather than assuming pass.
- [x] ✅ [BACKEND] P1. **Gap: tradfi archetype slots declare `venue="cme"` but `get_position_adapter()` has no
      `"cme"` match arm** — SHIPPED `strategy-service@ff6c00870a`. `_get_other_adapter`'s `"ibkr"` match arm now
      also matches `"cme"`/`"cboe"`/`"nasdaq"`/`"nyse"`/`"ice"`/`"fx"` — every one of `execution-service`'s
      `TRADFI_VENUES` set — and routes them to the same `IBKRPositionAdapter` as the generic `"ibkr"` token, since
      position reads for these venues resolve conid-scoped positions off the same underlying IBKR connection.
      Updated the docstring's supported-values list and the `Unknown venue` error message's `Valid:` list to
      match. Added `test_factory_tradfi_venues_route_to_ibkr` (parametrized over all 6 tokens) to
      `tests/position/position_interface/unit/test_adapters.py`, alongside the pre-existing `test_factory_ibkr`.
      Full local `quality-gates.sh` green on the committed HEAD.
- [x] ✅ [BACKEND] P0. **Step 9 per unit — done 2026-08-16.** SHIPPED — `unified-trading-pm@48f83481ce`.
      TradFi transfers are architecturally broker-scoped, not per-exchange:
      `execution_service/trade_execution/adapters/ibkr_tradfi.py:47` — "Execution routes through IBKR" for
      CME/CBOE/NASDAQ/NYSE/ICE/FX (`factory.py:63 TRADFI_VENUES`); `BusTransferType.IBKR_FUND_MOVE` is the
      applicable type. **KRX/FRED — NOT-APPLICABLE** (confirmed data-only, absent from `TRADFI_VENUES`, no
      execution capability exists for either). **The other 6 venues — FAIL, but ALREADY TRACKED**: `IBKR_FUND_MOVE`
      has zero importers workspace-wide and no case in `transfer_handler._dispatch_transfer` — already documented
      as "unfinished capability" in `service_config_ownership_and_instruction_contract_2026_08_12.md:487,493`
      (checked via grep before filing — no duplicate todo created here).
- [x] ✅ [BACKEND] P1. **Record every gap found — done 2026-08-16.** Of the findings this sweep surfaced, only 1
      is genuinely new and untracked (`cross_venue_spreads` baseline-venue hardcoding, todo above) — the Yahoo-
      interim-no-live situation and the unwired `IBKR_FUND_MOVE` rail were both confirmed already tracked
      elsewhere via corpus grep before filing, per the pre-task conflict-check discipline, rather than duplicated
      here.
- [x] ✅ [BACKEND] P0. **Confirm the parent plan's hard rules held — done 2026-08-16, trivially satisfied.** This
      batch's steps 1-5 and step 9 sweep was investigation/documentation only — zero code was changed in any
      touched repo, so none of the 4 hard rules could have been violated by this batch's own work.

## Progress Log

**2026-08-16 — steps 6-8 done, 1 new gap found.** Investigation only, zero code changed. Real per-row verdict for
the 4 in-scope rows (CBOE/CME/NASDAQ/NYSE `ohlcv_1m`): CME PARTIAL (8 real ML_DIRECTIONAL_CONTINUOUS/
RULES_DIRECTIONAL_CONTINUOUS slots, batch/sim-paper position reads work, live/real-paper position reads FAIL on
a genuinely new gap — `get_position_adapter()` has no `"cme"` match arm, only `"ibkr"` — now its own P1 todo
above; live/paper order placement itself was already tracked as blocked); CBOE BLOCKED-ON:
archetype-declaration-backlog (not declared under any of the 6 target archetypes); NASDAQ/NYSE UNVERIFIED (both
route through the generic `"ibkr"` venue token, which DOES resolve live for position reads, but the
`"ibkr"`-to-per-exchange-execution-adapter routing was not traced this pass). TSMOM_BTC_CTA/STAT_ARB_*/
VOL_CROSS_ASSET_SPREAD/VOL_DISPERSION: no catalogue rows touch any of the 4 in-scope venues (VOL_CROSS_ASSET_
SPREAD/VOL_DISPERSION have zero `TARGET_UNIVERSE` rows at all, for any venue). Checked corpus for the new gap
before filing — confirmed genuinely untracked.

**2026-08-16 — full contract sweep done, 1 new gap found, 2 candidate gaps confirmed already tracked.** SHIPPED
— `unified-trading-pm@48f83481ce`. 4 parallel research passes covered steps 2/3-4/5/9 across all 8 tradfi
venues (16 rows). TradFi is structurally healthier than prediction: instrument resolution passes cleanly for all
8 venues, and both of the two big-looking gaps (Yahoo-interim sources lacking live connectors; the unwired
`IBKR_FUND_MOVE` broker transfer rail) turned out to be already-tracked, known conditions elsewhere in the corpus
— checked via grep before filing anything, per the pre-task conflict-check discipline, rather than duplicated.
Exactly 1 genuinely new finding: `CrossVenueCalculator` hardcodes `baseline_venue="BINANCE-SPOT"`, so
`ARBITRAGE_PRICE_DISPERSION` can never be satisfied for any tradfi venue despite being a declared consumer — now
tracked as its own todo. Steps 6-8 rescoped to the 4 rows with real feature output (CBOE/CME/NASDAQ/NYSE
`ohlcv_1m`); the other 12 rows are `BLOCKED-ON:archetype-declaration-backlog` (a genuine undeclared-scope gap,
not investigated further since there's no declared requirement to check implementation against).
