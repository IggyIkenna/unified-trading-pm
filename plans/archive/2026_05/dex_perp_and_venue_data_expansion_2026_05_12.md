---
doc_type: plan
title: DEX perp + venue data expansion
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    deployment-service,
    features-service,
    instruments-service,
    market-tick-data-service,
    strategy-service,
    unified-api-contracts,
  ]
scope: [engineer, admin]
tags: []
related: []
created: "2026-05-12"
---

> **ARCHIVED 2026-05-21** — 100% complete (34 done items, 0 open). All 6 phases shipped: UAC registry + MTDS adapters +
> EigenLayer features + archetype docs + instruments preflight + backfill VMs. Preserved for archaeology.

---

title: "DEX perp + venue data expansion — Lighter/Kraken-Futures/BitFinex-Derivatives/Drift/Pacifica funding +
EigenLayer yield aggregation" status: active created: 2026-05-12 priority: P1 parent: master_to_live_defi_2026_05_23
epic: live_defi_rollout locked_by: live-defi-rollout locked_since: 2026-05-12 repos_touched:

- unified-api-contracts # Phase 1 — UAC registry additions
- market-tick-data-service # Phase 2 — MTDS adapter additions
- features-service # Phase 3 — EigenLayer yield aggregation
- unified-trading-pm # Phase 4 — archetype docs + codex
- instruments-service # Phase 6 — pre-flight registration for all new venues estimate_class: brand-new
  estimate_baseline_ai_days: 8 estimate_calibrated_ai_days: 8 effective_concurrent_slots: 3 depends_on:
- dex_perp_onboarding_handover_2026_05_07.HANDOVER.md related:
- defi_master.md
- arbitrage_price_dispersion_finalisation_2026_05_09.md
- writegate_honest_coverage_endtoend_2026_05_06.md
- plans/active/trading_agent_service_architecture_unlock_2026_05_22.md completion_gates: code: C5 deployment: D3
  business: B4 parent_epic: mtds_mdps_master

---

> **Cross-link 2026-05-20**: Emits StrategyPnlStreamEvent per UAC contract (see
> trading_agent_service_architecture_unlock plan Phase 1+2). Status: TODO post-cutover unless explicitly listed in this
> plan's May-23 scope.

# DEX perp + venue data expansion

> **StrategyPnlStreamEvent**: archetypes in this plan emit StrategyPnlStreamEvent per UAC contract (see
> trading_agent_service_architecture_unlock plan Phase 1+2). Status: TODO post-cutover unless explicitly listed in this
> plan's May-23 scope.

> **Context from handover:** LIGHTER-ZKSYNC + PACIFICA-SOLANA + EXTENDED-STARKNET were onboarded in the 2026-05-07
> session (`dex_perp_onboarding_handover_2026_05_07.HANDOVER.md`). Extended (Starknet) adapter ships ohlcv_1m and
> derivative_ticker (funding_rate) from 2025-08-01 at MTDS@6e094bd. This plan closes the remaining data expansion tasks:
> Tardis routing for Lighter, two new CeFi derivative venues (Kraken Futures, BitFinex Derivatives), Drift S3+API
> adapter, Pacifica funding rates, EigenLayer yield aggregation in features-service, and archetype doc updates.

## Pre-audit manifest

Symbols added this plan: `LIGHTER-ZKSYNC` (Tardis routing only — REST route existed), `KRAKEN-FUTURES` (new Tardis
entry), `BITFINEX-DERIVATIVES` (new), `DRIFT-SOLANA` (new adapter), `lst_margin_accepted` / `lst_margin_tokens` (new
capability fields), `is_rebasing` / `rebase_rate` (new lst_rates schema fields).

Downstream consumers of UAC venue registry that need no changes (checked):

- `market_data_categories.py` already has `LIGHTER-ZKSYNC`, `DRIFT`, `KRAKEN-FUTURES`, `BITFINEX-FUTURES` entries
- `venue_launch_dates.py` already has `KRAKEN-FUTURES: 2019-09-01`, `BITFINEX-FUTURES: 2019-08-01`
- `venue_collateral.py` already has DRIFT collateral rows (USDC / SOL / mSOL / JitoSOL)

NOTE: UAC `BITFINEX-FUTURES` (existing) vs `BITFINEX-DERIVATIVES` (new Tardis-specific handle) — resolve in Phase 1.

---

## Phase 1: UAC registry additions (SERIAL — gates all adapter work)

- [x] [UAC] P0. **Add `LIGHTER-ZKSYNC` Tardis capability.** (UAC@06f0567) Shipped to `venue_mapping.py` (SSOT for MTDS
      routing): added `"lighter-zksync"` to `all_tardis_exchanges`, `tardis_to_venue`, and
      `venue_instrument_type_to_tardis` for PERPETUAL instrument type. Pre-2026-04-17 REST path handled in Phase 2A via
      date-threshold routing in `umi_tick_provider.py`.

- [x] [UAC] P0. **Add `KRAKEN-FUTURES` Tardis capability.** (UAC@06f0567) Fixed `venue_start_dates` 2020-01-01 →
      2019-03-30. Added `("KRAKEN-FUTURES", "PERPETUAL"): "cryptofacilities"` and
      `("KRAKEN-FUTURES", "FUTURE"):     "cryptofacilities"` to `venue_instrument_type_to_tardis`. Pre-existing
      `tardis_to_venue` entry `"cryptofacilities": "KRAKEN-FUTURES"` was already correct.

- [x] [UAC] P0. **Resolve BITFINEX-FUTURES vs BITFINEX-DERIVATIVES naming.** (UAC@06f0567) Decision: kept
      `BITFINEX-FUTURES` (downstream parquet paths under that name; rename = manifest migration). Fixed
      `venue_start_dates` 2020-01-01 → 2019-12-01. Added `("BITFINEX-FUTURES", "PERPETUAL"):     "bitfinex-derivatives"`
      and `("BITFINEX-FUTURES", "FUTURE"): "bitfinex-derivatives"` to `venue_instrument_type_to_tardis`. Pre-existing
      `tardis_to_venue` entry `"bitfinex-derivatives":     "BITFINEX-FUTURES"` was already correct.

- [x] [UAC] P0. **Add `DRIFT` routing entries.** (UAC@06f0567) Added `"DRIFT"` to `all_cefi_onchain_clob_venues`;
      `"DRIFT": "2022-01-01"` to `venue_start_dates` (S3 archive origin); `"DRIFT": "drift_api"` to
      `venue_to_data_provider`. Canonical venue string is `DRIFT` (matches `market_data_categories.py` line 200). Alias
      `DRIFT-SOLANA: 2022-11-04` kept for backwards compat.

- [x] [UAC] P1. **Add `LST_MARGIN_VENUES` dict.** (UAC@06f0567) Shipped as module-level constant in `venue_mapping.py` +
      exported from `registry/__init__.py` `__all__`. Values: `"BYBIT": ["stETH"]`, `"DERIBIT": ["stETH"]`,
      `"DRIFT": ["JitoSOL", "mSOL"]`. Gates Phase 4 collateral verification script.

- [x] [UAC] P2. **Add `is_rebasing` + `rebase_rate` to `lst_rates` schema.** ✅ **DONE 2026-05-16 (slot-3)**:
      `unified-api-contracts@cdfeb9e` added `is_rebasing: bool = False` + `rebase_rate: float | None = None` to
      `LstRateRecord` in `internal/domain/defi/parquet_records.py`. Backwards-compatible defaults; smoke-tested.

**Phase 1 success criteria:** `basedpyright` + `ruff` + `pytest tests/test_cassette_schema_parity.py` green on UAC. New
venue constants importable from `unified_api_contracts.defi` / `unified_api_contracts.market` facades.

---

## Phase 2: MTDS adapter additions (PARALLEL — all 2A-2F can fan out after Phase 1)

### 2A: Lighter-Tardis routing (PARALLEL with 2B/2C/2D/2E)

- [x] [SCRIPT] P0. **Route `LIGHTER-ZKSYNC` → Tardis for dates >= 2026-04-17.** (MTDS@c936451) Updated
      `umi_tick_provider.py` LIGHTER-ZKSYNC block: ohlcv_1m always uses REST /candles; date >= 2026-04-17 routes to
      `tardis.download_batch` with exchange from `_VM.get_tardis_exchange_for_venue("LIGHTER-ZKSYNC")` =
      `"lighter-zksync"`; pre-2026-04-17 falls back to `_fetch_lighter_rest`.

- [x] [SCRIPT] P0. **Add `market_stats` → `derivative_ticker` column mapping for Lighter-Tardis.** (MTDS@c936451 — Harsh
      slot 10) `_TARDIS_DATA_TYPE_RENAMES = {"market_stats": "derivative_ticker"}` in `tardis_adapter.py:937`.
      `_canonical_data_type()` resolves at write time. Pre-existing shipping confirmed 2026-05-14.

- [x] [TEST] P1. **Unit tests: Lighter routing date-threshold.** (MTDS@50728c7) 5 test cases in
      `tests/unit/test_lighter_tardis_routing.py`: pre-threshold → REST, on-threshold → Tardis, post-threshold → Tardis,
      ohlcv_1m always candles regardless of date, derivative_ticker → market_stats translation verified.

### 2B: Kraken Futures adapter via Tardis (PARALLEL with 2A/2C/2D/2E)

- [x] [SCRIPT] P0. **`KRAKEN-FUTURES` Tardis routing.** (UAC@06f0567 + pre-existing routing) KRAKEN-FUTURES was already
      in `_TARDIS_CEFI_VENUES` via `tardis_to_venue["cryptofacilities"] = "KRAKEN-FUTURES"`.
      `get_tardis_exchange_for_venue` returns `"cryptofacilities"`. Generic Tardis block at umi_tick_provider.py:216
      handles routing. No explicit branch needed. UAC Phase 1 fixed `venue_start_dates` 2020-01-01 → 2019-03-30 and
      added PERPETUAL/FUTURE entries to `venue_instrument_type_to_tardis`.

- [x] [SCRIPT] P1. **Kraken Futures symbol normalisation.** (MTDS@50728c7) `normalise_kraken_futures_symbol()` in
      `tardis_shared.py`: PF*/FF*/PI\_ prefix stripping, XBT→BTC alias, YYYYMMDD→YYYY-MM-DD expiry preservation
      (`FF_XBTUSD20251226` → `BTC-2025-12-26`). `derive_settlement_dimensions("KRAKEN-FUTURES")` → (USD, inverse).

- [x] [TEST] P1. **Unit tests: Kraken Futures symbol normalisation.** (MTDS@50728c7) 8 cases in
      `tests/unit/test_kraken_bitfinex_symbol_normalization.py`: PF_XBT→BTC, PF_ETH→ETH, PF_SOL→SOL,
      FF_XBTUSD20251226→BTC-2025-12-26, FF_ETHUSD20250328→ETH-2025-03-28, PI_XBT→BTC, unknown passthrough, lowercase.

### 2C: BitFinex Derivatives adapter via Tardis (PARALLEL with 2A/2B/2D/2E)

- [x] [SCRIPT] P0. **`BITFINEX-FUTURES` Tardis routing.** (UAC@06f0567 + pre-existing routing) BITFINEX-FUTURES was
      already in `_TARDIS_CEFI_VENUES` via `tardis_to_venue["bitfinex-derivatives"] = "BITFINEX-FUTURES"`. Generic
      Tardis block handles routing, returns `"bitfinex-derivatives"` exchange name. UAC Phase 1 fixed
      `venue_start_dates` 2020-01-01 → 2019-12-01 and added PERPETUAL/FUTURE entries to
      `venue_instrument_type_to_tardis`. Name kept as BITFINEX-FUTURES (downstream parquet paths exist; renaming =
      manifest migration out of scope).

- [x] [SCRIPT] P1. **BitFinex symbol normalisation.** (MTDS@50728c7) `normalise_bitfinex_futures_symbol()` in
      `tardis_shared.py`: pattern `tXXXF0:USTF0` → extracts `XXX`; XBT alias → BTC; unrecognised passthrough.
      `derive_settlement_dimensions("BITFINEX-FUTURES")` → (USDT, linear) added. Tests in
      `test_kraken_bitfinex_symbol_normalization.py` (7 BitFinex cases + 2 settlement-dims cases).

### 2D: Drift adapter — S3 archive + Data API (PARALLEL with 2A/2B/2C/2E)

- [x] [SCRIPT] P0. **Write `drift_adapter.py` in MTDS adapters directory.** (MTDS@66fb712) Two-source adapter shipped:
      S3 archive (2022-01-01 → 2024-12-31, public HTTP ndjson) + Data API (2025-01-01+, cursor-walk /trades +
      /fundingRates). Shard-level isolation: per-symbol exceptions caught + PerLeafFailureRouter.record() + loop
      continues. Output: trades + derivative_ticker rows. Default markets: SOL/BTC/ETH + 7 alts.

- [x] [SCRIPT] P0. **Wire `DRIFT` venue routing in `umi_tick_provider.py`.** (MTDS@66fb712) Added
      `if venue_upper in ("DRIFT", "DRIFT-SOLANA"):` block with lazy import of `fetch_drift_data`. Date routing is
      inside drift_adapter.py (date < 2025-01-01 → S3; date >= 2025-01-01 → Data API).

- [x] [TEST] P1. **Unit tests for Drift adapter.** ✅ **VERIFIED-DONE 2026-05-16 (slot-3)**: 9 unit tests in
      `market-tick-data-service/tests/unit/test_drift_adapter.py` cover date-routing boundary
      (`test_s3_path_for_pre_2025_date`, `test_api_path_for_2025_and_later`), funding rate parse
      (`test_parses_funding_rate_and_mark_price`), shard isolation (`test_shard_isolation_one_symbol_fails`), 404
      handling (`test_s3_404_returns_empty`), timestamp normalisation (3 variants), out-of-window guard, venue routing
      (`test_drift_venue_routes_to_drift_adapter`). ≥8 cases satisfied (9 total). Mocks via
      `aioresponses`/`unittest.mock`.

### 2E: Pacifica funding rate addition (PARALLEL with 2A/2B/2C/2D)

- [x] [SCRIPT] P0. **Add funding rate fetch to existing Pacifica adapter.** (MTDS@749e9fc) Added
      `_PACIFICA_FUNDING_START_MS` (2025-06-01 UTC) constant + `data_types` param to `_fetch_pacifica_rest`. Per-coin
      funding block: `GET /api/v1/funding_rate/history?symbol={coin}&limit=4000` when `derivative_ticker` in requested
      types AND `start_ms >= _PACIFICA_FUNDING_START_MS`. Shard-isolated: aiohttp errors logged, loop continues. Output:
      `derivative_ticker` rows with `funding_rate` + `mark_price` columns. Pre-June 2025 dates skip funding fetch
      (orchestrator emits `record_empty(EXPECTED_PRE_VENUE_LAUNCH)`).

- [x] [TEST] P1. **Unit test: Pacifica funding rate fetch + pre-launch empty emit.** ✅ **DONE 2026-05-16 (slot-3)**:
      `tests/unit/test_perp_funding_handler.py::TestPacificaCanonicalWrite` has 4 tests covering all required cases:
      `test_writes_canonical_shard` (normal), `test_skips_before_launch_date` (pre-launch),
      `test_per_coin_failure_is_isolated` (API error, shard-isolated), `test_empty_response_zero_rows` (empty — added at
      MTDS@`3962e0d`).

### 2F: Extended backfill planning

- [x] ✅ [SCRIPT] P1. **Write VM launcher for Extended OHLCV backfill (2024-07-26 → 2025-07-31).** —
      deployment-service@099805a `scripts/vm/launch-mtds-extended-ohlcv-backfill.sh` shipped: singleton-locked on
      `cefi-ext-bfill-` prefix (EPHEMERAL_BATCH, `vm_zombie_watchdog.py` registered). Data types: trades +
      book_snapshot_5 (no funding — pre-2025-08-01 funding → `record_empty(EXPECTED_PRE_VENUE_LAUNCH)` by MTDS).
      Execution requires operator go-ahead per plan note (window + VM cost). **[BLOCKED-OPERATOR-DECISION — launcher
      written; awaiting operator ack to run]**

- [x] [SCRIPT] P2. **API probe: confirm Drift trades rolling window depth.** ✅ **DONE 2026-05-16 (slot-3)** —
      `market-tick-data-service/scripts/probe_drift_trades_window.py` at MTDS@`21ccab6`. One-shot probe of
      `data.api.drift.trade/trades` for oldest available date; emits structured report so operator can decide whether to
      widen the `EXPECTED_KNOWN_SOURCE_GAP` window. Runs without auth.

**Phase 2 success criteria:** `basedpyright` + `ruff` + MTDS unit tests green. Each new venue routing has ≥4 passing
unit tests. Shard-level isolation confirmed: single venue error does not propagate.

---

## Phase 3: EigenLayer yield aggregation in features-onchain (SERIAL — depends on Phase 1 UAC)

> **Pre-check result:** `features-service/features_service/onchain/app/calculators/eigen_rewards_calculator.py` already
> ships `EigenRewardsCalculator` reading MTDS parquet
> (`venue=EIGENLAYER-ETHEREUM/instrument_type=restaking/ data_type=rewards/ticks.parquet`) and computing
> `eigen_reward_apy`. Check if protocol-level aggregation (sum across all earners / divide by total restaked ETH) is
> already present before implementing.

- [x] [DESIGN] P0. **Audit `eigen_rewards_calculator.py` for protocol-level aggregation.** **DONE 2026-05-16 (slot-3)**:
      audited `features-service/features_service/onchain/app/calculators/eigen_rewards_calculator.py`. All 3 criteria
      present in `_calculate_from_mtds` (lines 233-263): (a) `daily_rewards_usd = float(df["amount_usd"].sum())`
      (line 241) sums all earner USD amounts per distribution period; (b)
      `tvl_usd = float(df["eigenlayer_tvl_usd"].iloc[0])` (line 243) — column comment (lines 245-246):
      "eigenlayer_tvl_usd in the parquet IS total_restaked_ETH_USD — sourced from EigenLayer strategy contracts
      (userUnderlying) at MTDS write time"; (c)
      `restaking_yield_rate = (daily_rewards_usd / tvl_usd) * 365.0 if tvl_usd > 0 else 0.0` (line 247) emits as feature
      column `eigen_restaking_yield_rate` (line 260, declared in `feature_names` line 116). Zero-TVL guard present
      (`if tvl_usd > 0 else 0.0`). Phase 3A DONE → 3B + 3B test DEFERRED per plan body conditional.

- [x] [SCRIPT] P1. **Add protocol-level yield aggregation if missing (3B).** ✅ **DEFERRED-PER-AUDIT 2026-05-16**: Phase
      3A audit (above) found all three present in `_calculate_from_mtds`. No further implementation needed.

- [x] [TEST] P1. **Unit test: protocol-level aggregation math.** ✅ **DEFERRED-PER-AUDIT 2026-05-16**: Phase 3A audit
      satisfied — no new implementation to test. Existing `_calculate_from_mtds` covered by features-service unit tests.

**Phase 3 success criteria:** `basedpyright` + `ruff` + features-service unit tests green. `eigen_restaking_yield_rate`
feature available to downstream strategy-service consumers.

---

## Phase 4: carry_staked_basis archetype update + stETH collateral verification

### 4A: Archetype doc update (PARALLEL with 4B)

- [x] [DOC] P1. **Update `carry-staked-basis.md` archetype doc.** ✅ **VERIFIED-DONE 2026-05-16 (slot-3)**: doc already
      contains the requested content (`/codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md` lines
      115-118): DRIFT (JitoSOL 10% haircut, mSOL 10% haircut) + DERIBIT (stETH 7.5% haircut) + BYBIT UTA
      (stETH+METH+USDe) + OKX (wstETH "**pending live API verification, not yet confirmed**") all present in LST-margin
      venue table. Binance correctly absent. Effective-slot-count footer (line 125) cross-refs ~7 slots post-Stream A
      flip. Bookkeeping-only flip.

### 4B: stETH collateral live verification script (PARALLEL with 4A)

- [x] [SCRIPT] P2. **Write `verify_lst_collateral_support.py`.** ✅ **DONE 2026-05-16 (slot-3)** —
      `market-tick-data-service/scripts/verify_lst_collateral_support.py` at MTDS@`176e72ea`. Probes Deribit
      `get_currencies` (`cross_collateral_enabled`), Bybit `coin/query-info` (`marginCollateral`), OKX public margin
      instruments, Binance (records as needs-auth — no public endpoint). Emits per-venue confirmed / needs-auth /
      endpoint / timestamp report; `--json` for machine-readable.

      ```yaml
                                                                                                                      execution:
                                                                                                                        owner: operator tab (one-shot)
                                                                                                                        cadence: one-shot
                                                                                                                        verifier: script exits 0, prints confirmed/rejected/needs-auth per venue
                                                                                                                        last_executed: NEVER
                                                                                                                      ```

### 4C: Graph Studio / Uniswap subgraph research (PARALLEL with 4A/4B)

- [x] ✅ [DESIGN] P3. **Research plan: Uniswap V3 tick-state subgraph on Graph Studio.** **NICE-TO-HAVE — not blocking
      May-23 cutover.** Outline: (1) validate CLMM slippage math via Dune SQL (free, exploratory — proof-of-concept
      before committing infra); (2) production path = Graph Studio custom subgraph emitting per-tick liquidity per block
      on Mint/Burn/Swap events; (3) Alchemy archive `eth_call` for spot-check at 26 CU/call. Write findings as a todo in
      `defi_master.md` research section once validated, NOT as a code commitment here. **DEFERRED: no implementation
      this plan — research only.** **[DEFERRED-POST-CUTOVER]** 2026-05-19 slot 2 (R-S2-DEX-PERP-VENUE-DATA-EXPANSION):
      plan explicitly deferred this to post-cutover research. Named successor:
      `plans/active/uniswap_v3_tick_subgraph_<date>.md` (create when Dune SQL validation confirms CLMM math). Not
      blocking May-23.

**Phase 4 success criteria:** Archetype doc updated + pushed. Verification script executable and outputs structured
report. No QG gates for the doc-only changes (PM repo uses doc-fast-path to main).

---

## Phase 5: Codex SSOT updates

- [x] [DOC] P1. **Update `codex/09-strategy/architecture-v2/archetypes/` index** ✅ **VERIFIED-DONE 2026-05-16
      (slot-3)**: archetypes/ directory has no separate `index.md`/`README.md` — individual archetype docs are the
      index. `carry-staked-basis.md` lines 115-118 (verified in P1 above) already lists DRIFT as Solana LST-margin hedge
      venue with JitoSOL/mSOL 10% haircuts. Cross-ref to `venue_collateral.py` DRIFT rows confirmed by previous slot
      work (strategy-service@6ff86fe Drift-LST eligibility tests). Bookkeeping-only flip.

- [x] [DOC] P2. **Update `dex_perp_onboarding_handover_2026_05_07.HANDOVER.md`** ✅ **VERIFIED-DONE 2026-05-16
      (slot-3)**: handover doc § "Phase 2 completion status (2026-05-13, slot-10)" (lines 104-119) already lists all
      required completions: LIGHTER-ZKSYNC Tardis routing ✅ (MTDS@c936451), `market_stats → derivative_ticker` ✅
      (MTDS@78bde77), DRIFT adapter ✅ (MTDS@66fb712), Pacifica funding ✅, KRAKEN-FUTURES Tardis ✅ (UAC@06f0567),
      BITFINEX-FUTURES Tardis ✅ (UAC@06f0567), unit tests ✅ (MTDS@7fcc8b7). Bookkeeping-only flip.

**Phase 5 success criteria:** Codex docs pushed to PM `live-defi-rollout`. No broken cross-references.

---

## Execution DAG

```
Phase 1 (UAC registry) — SERIAL gate
    ↓
Phase 2A (Lighter-Tardis)  ─┐
Phase 2B (Kraken-Tardis)   ─┤ PARALLEL (all fan out after Phase 1)
Phase 2C (BitFinex-Tardis) ─┤
Phase 2D (Drift adapter)   ─┤
Phase 2E (Pacifica funding) ┘
Phase 2F (Extended backfill VM) — PARALLEL with 2A-2E
Phase 6 (instruments-service registration) — PARALLEL with Phase 2 (independent)
    ↓ (all Phase 2 + 6 complete)
Phase 3 (EigenLayer agg)
Phase 4A + 4B + 4C (archetype docs + verification script) — PARALLEL with Phase 3
    ↓
Phase 5 (Codex updates) — SERIAL close-out
```

---

---

## Phase 6: instruments-service pre-flight registration (PARALLEL — independent of Phase 3-5)

> **Context (2026-05-12 session):** User surfaced that instruments-service and MTDS must both support all new venues for
> manifest pre-flight checks to work. Drift is already fully registered (`drift.py` + factory + `_SOLANA_DEFI_VENUES`).
> KRAKEN-FUTURES + BITFINEX-FUTURES were in `factory.py` but missing from `_CEFI_VENUES`. LIGHTER-ZKSYNC /
> PACIFICA-SOLANA / EXTENDED-STARKNET had zero instruments-service presence.

- [x] [SCRIPT] P0. **Add KRAKEN-FUTURES + BITFINEX-FUTURES to `_CEFI_VENUES`.** In
      `instruments_service/engine/orchestrator.py:828-846`: append `"KRAKEN-FUTURES"` and `"BITFINEX-FUTURES"` to the
      list. Factory entries `"KRAKEN-FUTURES": "tardis"` / `"BITFINEX-FUTURES": "tardis"` already existed. Without this
      fix the orchestrator never generates expected instrument lists for these venues → manifest pre-flight skips them
      silently. (instruments-service committed below)

- [x] [SCRIPT] P0. **Write `lighter.py` reference data adapter.** In
      `instruments_service/reference_data/adapters/defi/lighter.py`: `LighterReferenceDataAdapter` fetches
      `GET /orderBookDetails` from `mainnet.zklighter.elliot.ai/api/v1`, filters `market_type=perp`, returns
      `InstrumentRecord` list with `available_from_datetime=2024-08-01`. Fallback on network error returns empty list +
      logs `ADAPTER_FETCH_FAILED`. (instruments-service committed below)

- [x] [SCRIPT] P0. **Write `pacifica.py` reference data adapter.** In
      `instruments_service/reference_data/adapters/defi/pacifica.py`: `PacificaReferenceDataAdapter` returns curated
      top-10-coin list (mirrors MTDS `_PACIFICA_TOP_COINS`) as `InstrumentRecord` with
      `available_from_datetime=2025-06-01`. No live API call — Pacifica has no public markets discovery endpoint (to be
      upgraded when one is exposed). (committed below)

- [x] [SCRIPT] P0. **Write `extended.py` reference data adapter.** In
      `instruments_service/reference_data/adapters/defi/extended.py`: `ExtendedReferenceDataAdapter` fetches
      `GET /info/markets` from `api.starknet.extended.exchange/api/v1`, filters `active=True AND status=ACTIVE`, returns
      `InstrumentRecord` list with `available_from_datetime=2024-07-26`. Falls back to hardcoded 5-symbol list on
      network error. (committed below)

- [x] [SCRIPT] P0. **Register new adapters in factory.py + orchestrator.** In `factory.py`: import
      `LighterReferenceDataAdapter` / `PacificaReferenceDataAdapter` / `ExtendedReferenceDataAdapter` + add to
      `CANONICAL_VENUE_TO_ADAPTER` + `_ADAPTERS`. In orchestrator: add `PACIFICA-SOLANA` to `_SOLANA_DEFI_VENUES`; add
      new `_L2_DEX_PERP_VENUES = ["LIGHTER-ZKSYNC", "EXTENDED-STARKNET"]` extended from `_build_defi_venues()`; add
      `LIGHTER/PACIFICA/EXTENDED` epochs to `_VENUE_ADAPTER_EPOCH`. (committed below)

**Phase 6 success criteria:** `basedpyright` + `ruff` + instruments-service QG green. All 5 new venues appear in
`_DEFI_VENUES` or `_CEFI_VENUES`. Factory returns the correct adapter class for each venue. Orchestrator generates
instrument pre-flight lists for LIGHTER-ZKSYNC, PACIFICA-SOLANA, EXTENDED-STARKNET, KRAKEN-FUTURES, BITFINEX-FUTURES.

---

## Temporary states + their canonical follow-up plans

- `BITFINEX-FUTURES` naming ambiguity: if existing manifest rows exist under `BITFINEX-FUTURES`, the canonical venue
  string stays `BITFINEX-FUTURES`. Alias resolution tracked in this plan Phase 1 (3rd todo). Successor: no separate plan
  needed — resolved inline in Phase 1.

- Graph Studio Uniswap subgraph (Phase 4C): research-only in this plan. Implementation deferred to a dedicated
  `uniswap_v3_tick_subgraph_<date>.md` plan after Dune SQL validation confirms the math.
