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
      2019-03-30. Added `("KRAKEN-FUTURES", "PERPETUAL"): "cryptofacilities"` and `("KRAKEN-FUTURES", "FUTURE"):
      "cryptofacilities"` to `venue_instrument_type_to_tardis`. Pre-existing `tardis_to_venue` entry
      `"cryptofacilities": "KRAKEN-FUTURES"` was already correct.

- [x] [UAC] P0. **Resolve BITFINEX-FUTURES vs BITFINEX-DERIVATIVES naming.** (UAC@06f0567) Decision: kept
      `BITFINEX-FUTURES` (downstream parquet paths under that name; rename = manifest migration). Fixed
      `venue_start_dates` 2020-01-01 → 2019-12-01. Added `("BITFINEX-FUTURES", "PERPETUAL"):
      "bitfinex-derivatives"` and `("BITFINEX-FUTURES", "FUTURE"): "bitfinex-derivatives"` to
      `venue_instrument_type_to_tardis`. Pre-existing `tardis_to_venue` entry `"bitfinex-derivatives":
      "BITFINEX-FUTURES"` was already correct.

- [x] [UAC] P0. **Add `DRIFT` routing entries.** (UAC@06f0567) Added `"DRIFT"` to `all_cefi_onchain_clob_venues`;
      `"DRIFT": "2022-01-01"` to `venue_start_dates` (S3 archive origin); `"DRIFT": "drift_api"` to
      `venue_to_data_provider`. Canonical venue string is `DRIFT` (matches `market_data_categories.py` line 200). Alias
      `DRIFT-SOLANA: 2022-11-04` kept for backwards compat.

- [x] [UAC] P1. **Add `LST_MARGIN_VENUES` dict.** (UAC@06f0567) Shipped as module-level constant in `venue_mapping.py`
      + exported from `registry/__init__.py` `__all__`. Values: `"BYBIT": ["stETH"]`, `"DERIBIT": ["stETH"]`,
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

- [x] [SCRIPT] P0. **Add `market_stats` → `derivative_ticker` column mapping for Lighter-Tardis.** (MTDS@78bde77)
      Added `_TARDIS_DATA_TYPE_RENAMES = {"market_stats": "derivative_ticker"}` class attr to `TardisAdapter` +
      updated `_canonical_data_type` to check the dict. Fixed `df["data_type"]` assignment in `_write_symbol_batch`
      to use `_canonical_data_type(data_type)` so parquet column value matches GCS path. Added
      `derivative_ticker→market_stats` translation in LIGHTER-ZKSYNC routing block of `umi_tick_provider.py` so
      callers use canonical data_type and the adapter remaps transparently.

- [x] [TEST] P1. **Unit tests: Lighter routing date-threshold.** (MTDS@7fcc8b7) 5 cases in
      `test_umi_tick_provider_routes.py::TestLighterZksyncRouting`: ohlcv_1m→candles always; pre-threshold→REST;
      post-threshold→Tardis; derivative_ticker→market_stats translation; mixed types partial translation.

### 2B: Kraken Futures adapter via Tardis (PARALLEL with 2A/2C/2D/2E)

- [x] [SCRIPT] P0. **`KRAKEN-FUTURES` Tardis routing.** (UAC@06f0567 + pre-existing routing) KRAKEN-FUTURES was already
      in `_TARDIS_CEFI_VENUES` via `tardis_to_venue["cryptofacilities"] = "KRAKEN-FUTURES"`. `get_tardis_exchange_for_venue`
      returns `"cryptofacilities"`. Generic Tardis block at umi_tick_provider.py:216 handles routing. No explicit branch
      needed. UAC Phase 1 fixed `venue_start_dates` 2020-01-01 → 2019-03-30 and added PERPETUAL/FUTURE entries to
      `venue_instrument_type_to_tardis`.

- [ ] [SCRIPT] P1. **Kraken Futures symbol normalisation.** Strip `PF_` prefix (perps) and `FF_` prefix (dated), extract
      underlying coin (e.g. `PF_XBTUSD` → `BTC`). Dated futures include expiry in filename — preserve expiry suffix in
      instrument_id as `BTC-20251226`. Add UAC constant for Tardis→canonical symbol map. Emit
      `record_empty(EXPECTED_INSTRUMENT_NOT_LISTED)` for symbols absent from instruments-service.
      **DEFERRED**: Requires UAC + MTDS dual-repo changes + careful coordination re on-disk symbol column convention.
      Multi-repo scope → Ikenna slot preferred. Successor: this plan Phase 2B (leave open; next Ikenna touch).

- [ ] [TEST] P1. **Unit tests: Kraken Futures symbol normalisation.** Test perp + dated + unknown symbol edge cases. ≥6
      cases. **DEFERRED**: Blocked by implementation above.

### 2C: BitFinex Derivatives adapter via Tardis (PARALLEL with 2A/2B/2D/2E)

- [x] [SCRIPT] P0. **`BITFINEX-FUTURES` Tardis routing.** (UAC@06f0567 + pre-existing routing) BITFINEX-FUTURES was
      already in `_TARDIS_CEFI_VENUES` via `tardis_to_venue["bitfinex-derivatives"] = "BITFINEX-FUTURES"`. Generic Tardis
      block handles routing, returns `"bitfinex-derivatives"` exchange name. UAC Phase 1 fixed `venue_start_dates`
      2020-01-01 → 2019-12-01 and added PERPETUAL/FUTURE entries to `venue_instrument_type_to_tardis`. Name kept as
      BITFINEX-FUTURES (downstream parquet paths exist; renaming = manifest migration out of scope).

- [ ] [SCRIPT] P1. **BitFinex symbol normalisation.** Pattern `tXXXF0:USTF0` → extract `XXX` as coin. Handle edge cases:
      XBTF0 → BTC (BitFinex uses XBT not BTC). Add normalisation constant to UAC.
      **DEFERRED**: Requires UAC + MTDS dual-repo changes + careful coordination re on-disk symbol column convention.
      Multi-repo scope → Ikenna slot preferred. Successor: this plan Phase 2C (leave open; next Ikenna touch).

### 2D: Drift adapter — S3 archive + Data API (PARALLEL with 2A/2B/2C/2E)

- [x] [SCRIPT] P0. **Write `drift_adapter.py` in MTDS adapters directory.** (MTDS@66fb712) 360-line adapter with
      two-source routing: S3 archive URL pattern
      `https://drift-historical-data-v2.s3.eu-west-1.amazonaws.com/program/.../market/{SYMBOL}-PERP/tradeRecords/{YYYY}/{YYYYMMDD}`;
      Data API `GET https://data.api.drift.trade/trades?marketName={SYMBOL}-PERP` and
      `/fundingRates?marketName={SYMBOL}-PERP`. `_DRIFT_API_START = "2025-01-01"` date boundary. Shard-level isolation
      via `PerLeafFailureRouter`. Classify errors via `classify_venue_error()` + emit `ADAPTER_FETCH_FAILED`.
      Entry point: `async def fetch_drift_data(date, data_types, instrument_ids, writer, ...)`.

- [x] [SCRIPT] P0. **Wire `DRIFT` venue routing in `umi_tick_provider.py`.** (MTDS@66fb712) Added
      `if venue_upper in ("DRIFT", "DRIFT-SOLANA"):` branch (lines 180-191) importing and calling `fetch_drift_data`
      from `drift_adapter`. Date routing (< / >= 2025-01-01) handled inside the adapter itself.

- [x] [TEST] P1. **Unit tests for Drift adapter.** (MTDS@7fcc8b7) 8 cases in `test_drift_adapter.py`: _parse_trade_row
      unix-seconds normalisation; ms-direct path; out-of-window→None; _parse_funding_row parse; S3 path for pre-2025;
      S3 404→empty; Data API path for 2025+ with trades+derivative_ticker; shard isolation one-symbol-fails. Used
      unittest.mock.patch on `_make_session` (no external library needed).

### 2E: Pacifica funding rate addition (PARALLEL with 2A/2B/2C/2D)

- [x] [SCRIPT] P0. **Add funding rate fetch to existing Pacifica adapter.** (MTDS@749e9fc) Added
      `_PACIFICA_FUNDING_START_MS` (2025-06-01 UTC) constant + `data_types` param to `_fetch_pacifica_rest`. Per-coin
      funding block: `GET /api/v1/funding_rate/history?symbol={coin}&limit=4000` when `derivative_ticker` in requested
      types AND `start_ms >= _PACIFICA_FUNDING_START_MS`. Shard-isolated: aiohttp errors logged, loop continues. Output:
      `derivative_ticker` rows with `funding_rate` + `mark_price` columns. Pre-June 2025 dates skip funding fetch
      (orchestrator emits `record_empty(EXPECTED_PRE_VENUE_LAUNCH)`).

- [x] [TEST] P1. **Unit test: Pacifica funding rate fetch + pre-launch empty emit.** (MTDS@7fcc8b7) 4 cases in
      `test_pacifica_candles.py`: normal fetch (date >= 2025-06-01 → /funding_rate/history called, 2 rows returned);
      pre-launch (date < 2025-06-01 → endpoint NOT called); empty response → 0 rows; aiohttp error → caught,
      no propagation (shard isolation).

### 2F: Extended backfill planning

- [ ] [SCRIPT] P1. **Write VM launcher for Extended OHLCV backfill (2024-07-26 → 2025-07-31).** Under
      `deployment-service/scripts/vm/` — singleton-locked launcher, register VM prefix in `vm_zombie_watchdog.py`. OHLCV
      backfill: API serves historical from 2024-07-26. Funding backfill: only from 2025-08-01 (already captured).
      Pre-2025-08-01 funding dates: emit `record_empty(EXPECTED_PRE_VENUE_LAUNCH)`.

- [x] [SCRIPT] P2. **API probe: confirm Drift trades rolling window depth.** One-shot script (not a continuous job) to
      probe `data.api.drift.trade/trades` for oldest available date. If rolling window < full 2025-01-01 coverage,
      document gap range + emit `record_empty(EXPECTED_KNOWN_SOURCE_GAP)` for affected dates.
      (MTDS@21ccab6 — `scripts/probe_drift_trades_window.py`; binary search + gap-range output + EXPECTED_KNOWN_SOURCE_GAP guidance)

**Phase 2 success criteria:** `basedpyright` + `ruff` + MTDS unit tests green. Each new venue routing has ≥4 passing
unit tests. Shard-level isolation confirmed: single venue error does not propagate.

---

## Phase 3: EigenLayer yield aggregation in features-onchain (SERIAL — depends on Phase 1 UAC)

> **Pre-check result:** `features-service/features_service/onchain/app/calculators/eigen_rewards_calculator.py` already
> ships `EigenRewardsCalculator` reading MTDS parquet
> (`venue=EIGENLAYER-ETHEREUM/instrument_type=restaking/ data_type=rewards/ticks.parquet`) and computing
> `eigen_reward_apy`. Check if protocol-level aggregation (sum across all earners / divide by total restaked ETH) is
> already present before implementing.

- [x] [DESIGN] P0. **Audit `eigen_rewards_calculator.py` for protocol-level aggregation.** (features-service@6e7409be)
      Audit complete: (a) ✅ `df["amount_usd"].sum()` aggregates all earner amounts; (b) ✅ `eigenlayer_tvl_usd` in
      parquet IS `total_restaked_ETH_USD` — sourced via `userUnderlying()` at MTDS write time (no live RPC needed at
      calculator time; adding one would be architecturally wrong); (c) ❌ `restaking_yield_rate` column was missing
      (only `eigen_reward_apy` existed). → 3B implemented.

- [x] [SCRIPT] P1. **Add protocol-level yield aggregation if missing (3B).** (features-service@6e7409be)
      Added `eigen_restaking_yield_rate = (daily_rewards_usd / tvl_usd) * 365` (decimal rate, not percentage) to
      `_calculate_from_mtds()` and to `feature_names` for MTDS path. Uses existing `eigenlayer_tvl_usd` from parquet
      (= total_restaked_ETH_USD). No `userUnderlying()` RPC needed: data is already in MTDS parquet from collection time.

- [x] [TEST] P1. **Unit test: protocol-level aggregation math.** (features-service@6e7409be) 4 cases added to
      `tests/onchain/unit/test_eigen_rewards_calculator.py`: yield_rate = apy/100 arithmetic check; zero-TVL guard;
      feature_names includes it for MTDS path only; output column present and positive for non-zero inputs.

**Phase 3 success criteria:** `basedpyright` + `ruff` + features-service unit tests green. `eigen_restaking_yield_rate`
feature available to downstream strategy-service consumers.

---

## Phase 4: carry_staked_basis archetype update + stETH collateral verification

### 4A: Archetype doc update (PARALLEL with 4B)

- [x] [DOC] P1. **Update `carry-staked-basis.md` archetype doc.** (PM@e502de33) Matrix table already had DRIFT/JitoSOL+mSOL,
      Deribit/stETH, Bybit/stETH+METH. Updated OKX row to explicitly label "pending live API verification, not yet confirmed"
      (was "haircut TBD per Stream A live probe" — same meaning, now explicit). Binance row already correct
      (BTC/ETH/BNB/etc. only, no LST margin). Codex doc reflects current state.

### 4B: stETH collateral live verification script (PARALLEL with 4A)

- [x] [SCRIPT] P2. **Write `verify_lst_collateral_support.py`.** (MTDS@176e72e) Shipped under
      `market-tick-data-service/scripts/verify_lst_collateral_support.py`. Probes: (1) Deribit
      `/api/v2/public/get_currencies` — `cross_collateral_enabled` for STETH; (2) Bybit
      `/v5/asset/coin/query-info` — `collateralSwitch`/`isMarginCoin` for STETH+METH; (3) OKX
      `/api/v5/public/currencies` — WSTETH listed (collateral discount-rate needs auth); (4) Binance
      `/papi/v1/margin/allCrossMarginPairs`. Output: CONFIRMED/REJECTED/NEEDS_AUTH_TO_VERIFY/ERROR per token.
      No auth required for discovery phase.

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

- [x] [DOC] P1. **Update `codex/09-strategy/architecture-v2/archetypes/` index** to reflect Drift as a Solana LST-margin
      hedge venue for `carry_staked_basis`. (PM@5ec8ff9d) Added Jito+Marinade DRIFT slot examples to
      `architecture-v2/README.md` naming convention examples. `carry-staked-basis.md` already had the full matrix.

- [x] [DOC] P2. **Update `dex_perp_onboarding_handover_2026_05_07.HANDOVER.md`** with Phase 2 completion status.
      (PM@5ec8ff9d) Added "Phase 2 completion status" table: Lighter-Tardis ✅, market_stats mapping ✅, Drift adapter ✅,
      Pacifica funding ✅, Kraken/BitFinex routing ✅, symbol normalisation ⏳ DEFERRED.

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
    ↓ (all Phase 2 complete)
Phase 3 (EigenLayer agg)
Phase 4A + 4B + 4C (archetype docs + verification script) — PARALLEL with Phase 3
    ↓
Phase 5 (Codex updates) — SERIAL close-out
```

---

## Deferred work after 2026-05-13 slot-10 Day-4 session

| Phase / item | Status as of 2026-05-13 | Successor / blocker |
|---|---|---|
| Phase 2A — LIGHTER-ZKSYNC routing + derivative_ticker mapping | ✅ DONE | MTDS@c936451 + MTDS@78bde77 |
| Phase 2D — DRIFT adapter (S3 archive + Data API date-routing) | ✅ DONE | MTDS@66fb712 |
| Phase 2E — DRIFT venue routing in umi_tick_provider.py | ✅ DONE | MTDS@66fb712 |
| Phase 2F P1 — Extended OHLCV backfill VM launcher (2024-07-26→2025-07-31) | ⏳ NOT STARTED | Needs deployment-service VM launcher + singleton-lock + watchdog registration |
| Phase 2F P2 — Drift trades rolling window probe script | ✅ DONE | MTDS@21ccab6 |
| Phase 2B — Kraken Futures symbol normalisation | ⏳ DEFERRED | Requires UAC + MTDS dual-repo — Ikenna slot preferred |
| Phase 2C — BitFinex-Derivatives symbol normalisation | ⏳ DEFERRED | Requires UAC + MTDS dual-repo — Ikenna slot preferred |
| Phase 3A — EigenLayer protocol-level aggregation audit | ✅ DONE | evidence (a)✅ (b)✅-via-parquet (c)❌-missing (RPC-at-calc-time wrong arch) |
| Phase 3B — eigen_restaking_yield_rate feature + 4 unit tests | ✅ DONE | features-service@93ca6219 |
| Phase 4A — carry-staked-basis.md OKX row → "pending live API verification" | ✅ DONE | PM@e502de33 |
| Phase 4B — verify_lst_collateral_support.py diagnostic script | ✅ DONE | MTDS@176e72e |
| Phase 4C — Uniswap V3 Graph Studio research | ⏳ NICE-TO-HAVE P3 | Not blocking. Successor: uniswap_v3_tick_subgraph_<date>.md after Dune validation |
| Phase 5.1 — README.md Drift/JitoSOL+mSOL slot naming examples | ✅ DONE | PM@5ec8ff9d |
| Phase 5.2 — HANDOVER.md Phase 2 completion status table | ✅ DONE | PM@5ec8ff9d |
| Phase 1 UAC P2 — is_rebasing + rebase_rate to lst_rates schema | ⏳ DEFERRED | UAC multi-repo change — Ikenna slot preferred |

**Key blocker for Phase 2F P1**: VM launcher under `deployment-service/scripts/vm/` requires singleton-lock pattern, `vm_zombie_watchdog.py` registration, and tarball refresh — multi-repo scope makes it Ikenna-tier.

---

## Temporary states + their canonical follow-up plans

- `BITFINEX-FUTURES` naming ambiguity: if existing manifest rows exist under `BITFINEX-FUTURES`, the canonical venue
  string stays `BITFINEX-FUTURES`. Alias resolution tracked in this plan Phase 1 (3rd todo). Successor: no separate plan
  needed — resolved inline in Phase 1.

- Graph Studio Uniswap subgraph (Phase 4C): research-only in this plan. Implementation deferred to a dedicated
  `uniswap_v3_tick_subgraph_<date>.md` plan after Dune SQL validation confirms the math.
