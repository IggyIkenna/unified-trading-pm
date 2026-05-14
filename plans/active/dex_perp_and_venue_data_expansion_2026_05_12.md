---
title:
  "DEX perp + venue data expansion — Lighter/Kraken-Futures/BitFinex-Derivatives/Drift/Pacifica funding + EigenLayer
  yield aggregation"
type: plan
status: active
created: 2026-05-12
deadline: 2026-05-23
asset_group: cefi,defi
priority: P1
parent: master_to_live_defi_2026_05_23
epic: live_defi_rollout
locked_by: live-defi-rollout
locked_since: 2026-05-12
repos_touched:
  - unified-api-contracts # Phase 1 — UAC registry additions
  - market-tick-data-service # Phase 2 — MTDS adapter additions
  - features-service # Phase 3 — EigenLayer yield aggregation
  - unified-trading-pm # Phase 4 — archetype docs + codex
  - instruments-service # Phase 6 — pre-flight registration for all new venues
estimate_class: brand-new
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 8
effective_concurrent_slots: 3
depends_on:
  - dex_perp_onboarding_handover_2026_05_07.HANDOVER.md
related:
  - defi_master_2026_05_07.md
  - arbitrage_price_dispersion_finalisation_2026_05_09.md
  - writegate_honest_coverage_endtoend_2026_05_06.md
completion_gates:
  code: C5
  deployment: D3
  business: B4
---

# DEX perp + venue data expansion

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

- [ ] [UAC] P2. **Add `is_rebasing` + `rebase_rate` to `lst_rates` schema.** In UAC `canonical/domain/defi/` or wherever
      lst_rates schema lives: add `is_rebasing: bool` (stETH=True, wstETH=False) and `rebase_rate: float | None` (daily
      rebase multiplier from Lido oracle for stETH; None for non-rebasing). Both tokens captured under same data_type,
      distinguished by `is_rebasing` flag.

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

- [ ] [TEST] P1. **Unit tests for Drift adapter.** Mock S3 HTTP + Data API responses. Test date-routing boundary,
      funding rate parse, shard-level isolation (one failed instrument doesn't abort loop). ≥8 cases. Use `responses`
      library for HTTP mocking (consistent with DeFi unit test pattern per CLAUDE.md).

### 2E: Pacifica funding rate addition (PARALLEL with 2A/2B/2C/2D)

- [x] [SCRIPT] P0. **Add funding rate fetch to existing Pacifica adapter.** (MTDS@749e9fc) Added
      `_PACIFICA_FUNDING_START_MS` (2025-06-01 UTC) constant + `data_types` param to `_fetch_pacifica_rest`. Per-coin
      funding block: `GET /api/v1/funding_rate/history?symbol={coin}&limit=4000` when `derivative_ticker` in requested
      types AND `start_ms >= _PACIFICA_FUNDING_START_MS`. Shard-isolated: aiohttp errors logged, loop continues. Output:
      `derivative_ticker` rows with `funding_rate` + `mark_price` columns. Pre-June 2025 dates skip funding fetch
      (orchestrator emits `record_empty(EXPECTED_PRE_VENUE_LAUNCH)`).

- [ ] [TEST] P1. **Unit test: Pacifica funding rate fetch + pre-launch empty emit.** ≥4 cases: normal fetch, empty
      response, pre-launch date, API error (→ record_failed not record_empty).

### 2F: Extended backfill planning

- [ ] [SCRIPT] P1. **Write VM launcher for Extended OHLCV backfill (2024-07-26 → 2025-07-31).** Under
      `deployment-service/scripts/vm/` — singleton-locked launcher, register VM prefix in `vm_zombie_watchdog.py`. OHLCV
      backfill: API serves historical from 2024-07-26. Funding backfill: only from 2025-08-01 (already captured).
      Pre-2025-08-01 funding dates: emit `record_empty(EXPECTED_PRE_VENUE_LAUNCH)`.

- [ ] [SCRIPT] P2. **API probe: confirm Drift trades rolling window depth.** One-shot script (not a continuous job) to
      probe `data.api.drift.trade/trades` for oldest available date. If rolling window < full 2025-01-01 coverage,
      document gap range + emit `record_empty(EXPECTED_KNOWN_SOURCE_GAP)` for affected dates.

**Phase 2 success criteria:** `basedpyright` + `ruff` + MTDS unit tests green. Each new venue routing has ≥4 passing
unit tests. Shard-level isolation confirmed: single venue error does not propagate.

---

## Phase 3: EigenLayer yield aggregation in features-onchain (SERIAL — depends on Phase 1 UAC)

> **Pre-check result:** `features-service/features_service/onchain/app/calculators/eigen_rewards_calculator.py` already
> ships `EigenRewardsCalculator` reading MTDS parquet
> (`venue=EIGENLAYER-ETHEREUM/instrument_type=restaking/ data_type=rewards/ticks.parquet`) and computing
> `eigen_reward_apy`. Check if protocol-level aggregation (sum across all earners / divide by total restaked ETH) is
> already present before implementing.

- [ ] [DESIGN] P0. **Audit `eigen_rewards_calculator.py` for protocol-level aggregation.** Read the full calculator
      implementation. Verify: (a) does it sum all earner amounts per distribution period? (b) does it fetch
      `total_restaked_ETH` via `userUnderlying()` on EigenLayer strategy contract? (c) does it compute
      `restaking_yield_rate = EIGEN_distributed_USD / total_restaked_ETH_USD` annualised? If all three present → mark
      this phase done with evidence. If any missing → implement in 3B.

- [ ] [SCRIPT] P1. **Add protocol-level yield aggregation if missing (3B).** In `eigen_rewards_calculator.py`: aggregate
      per-earner EIGEN amounts to protocol total per distribution period. Add `userUnderlying()` RPC call to EigenLayer
      strategy contract (use Alchemy/RPC URL from UAC `CHAIN_RPC_TEMPLATES`). Compute
      `restaking_yield_rate = (EIGEN_distributed_USD / total_restaked_ETH_USD) * 365` as annualised rate. Emit as new
      feature column `eigen_restaking_yield_rate`. Follow existing `OnChainCalculator` pattern. **DEFERRED if Phase 3A
      audit finds all three already implemented.**

- [ ] [TEST] P1. **Unit test: protocol-level aggregation math.** Mock RPC + MTDS parquet. Assert `restaking_yield_rate`
      = expected value given fixture data. ≥4 cases including zero-TVL guard.

**Phase 3 success criteria:** `basedpyright` + `ruff` + features-service unit tests green. `eigen_restaking_yield_rate`
feature available to downstream strategy-service consumers.

---

## Phase 4: carry_staked_basis archetype update + stETH collateral verification

### 4A: Archetype doc update (PARALLEL with 4B)

- [ ] [DOC] P1. **Update `carry-staked-basis.md` archetype doc.** In
      `unified-trading-pm/codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md`: add Drift/JitoSOL+mSOL as
      Solana-native hedge leg option (alongside existing Bybit/Deribit stETH entries). LST-margin venue summary: Bybit
      (stETH UTA), Deribit (stETH), Drift (JitoSOL+mSOL). Mark OKX as "pending live API verification" (not confirmed).
      Mark Binance as "no LST margin — USDC/BTC/ETH only".

### 4B: stETH collateral live verification script (PARALLEL with 4A)

- [ ] [SCRIPT] P2. **Write `verify_lst_collateral_support.py`.** One-shot diagnostic (not a continuous job). Place under
      `market-tick-data-service/scripts/verify_lst_collateral_support.py`. Queries: (1) Deribit
      `/api/v2/public/get_currencies` — check `cross_collateral_enabled` for STETH; (2) Bybit
      `/v5/account/collateral-info` — check STETH marginable status; (3) OKX portfolio margin collateral list endpoint;
      (4) Binance multi-assets mode collateral list. Output: structured report (venue / token / confirmed / needs-auth /
      API endpoint / timestamp). Execution owner: one-shot operator tab. No VM launcher needed.

      ```yaml
      execution:
        owner: operator tab (one-shot)
        cadence: one-shot
        verifier: script exits 0, prints confirmed/rejected/needs-auth per venue
        last_executed: NEVER
      ```

### 4C: Graph Studio / Uniswap subgraph research (PARALLEL with 4A/4B)

- [ ] [DESIGN] P3. **Research plan: Uniswap V3 tick-state subgraph on Graph Studio.** **NICE-TO-HAVE — not blocking
      May-23 cutover.** Outline: (1) validate CLMM slippage math via Dune SQL (free, exploratory — proof-of-concept
      before committing infra); (2) production path = Graph Studio custom subgraph emitting per-tick liquidity per block
      on Mint/Burn/Swap events; (3) Alchemy archive `eth_call` for spot-check at 26 CU/call. Write findings as a todo in
      `defi_master_2026_05_07.md` research section once validated, NOT as a code commitment here. **DEFERRED: no
      implementation this plan — research only.**

**Phase 4 success criteria:** Archetype doc updated + pushed. Verification script executable and outputs structured
report. No QG gates for the doc-only changes (PM repo uses doc-fast-path to main).

---

## Phase 5: Codex SSOT updates

- [ ] [DOC] P1. **Update `codex/09-strategy/architecture-v2/archetypes/` index** to reflect Drift as a Solana LST-margin
      hedge venue for `carry_staked_basis`. Cross-reference venue collateral SSOT (`venue_collateral.py` already has
      DRIFT rows).

- [ ] [DOC] P2. **Update `dex_perp_onboarding_handover_2026_05_07.HANDOVER.md`** with Phase 2 completion status: Tardis
      routing live for Lighter + Kraken Futures + BitFinex; Drift adapter shipped.

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
