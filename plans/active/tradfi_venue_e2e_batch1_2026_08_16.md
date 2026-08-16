---
doc_type: plan
title: tradfi venue e2e wiring batch 1 — 2026-08-16
summary: >-
  Fresh carve-out from venue_e2e_wiring_2026_08_16.md's "Fork per-asset-group dispatch batches" P0 todo — walks
  contract steps 1-9 across every tradfi (venue, data_type) row from `unified-api-contracts/scripts/
  generate_venue_work_list.py` (16 rows, measured 2026-08-16; re-run the script, this count is not a constant).
  Not an extraction from another source doc — no operator-gated item mixed in, per task_template.md §3 finding Y.
status: active
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
last_updated: "2026-08-16"
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
- [ ] [BACKEND] P1. **Gap: `CrossVenueCalculator` hardcodes `baseline_venue="BINANCE-SPOT"`, never tradfi-aware**
      (`features-service/cross_instrument/config.py:95-99`, `cross_venue_calculator.py:142-145`) — every tradfi
      row hits the "baseline venue not found" branch and returns empty features, so `ARBITRAGE_PRICE_DISPERSION`
      can never be satisfied for CBOE/CME/NASDAQ/NYSE despite `ohlcv_1m` being a declared input. Done-when: the
      calculator is asset-group-aware (a tradfi-appropriate baseline, or a per-AG baseline config) and a fresh run
      shows non-empty features for at least one tradfi venue, or the exclusion is confirmed intentional
      (ARBITRAGE_PRICE_DISPERSION genuinely doesn't apply to tradfi) with a cited reason.
- [ ] [BACKEND] P0. **Steps 6-8 per unit — strategy and execution**, across tradfi's 16 rows. **Gated by the
      step-5 result above**: only CBOE/CME/NASDAQ/NYSE `ohlcv_1m` have any real feature output today (via the
      PASSING feature_groups, not `cross_venue_spreads`), the other 12 rows stay `BLOCKED-ON:
      archetype-declaration-backlog`. Scope this todo to those 4 rows: does a position adapter resolve in
      batch/live/paper; are these venues declared in the archetype/slot catalogues for
      `ML_DIRECTIONAL_CONTINUOUS`/`RULES_DIRECTIONAL_CONTINUOUS`/`TSMOM_BTC_CTA`/`STAT_ARB_*`/`VOL_CROSS_ASSET_
      SPREAD`/`VOL_DISPERSION`; does an execution adaptor handle every `InstructionActionV2` those archetypes
      emit — per the prediction batch's finding, verify real routing, not just a declared mapping. Done-when: a
      real per-row verdict, plus `BLOCKED-ON` markers for the other 12 rows.
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
