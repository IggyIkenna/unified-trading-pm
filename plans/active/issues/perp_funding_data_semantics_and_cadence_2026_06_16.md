---
title:
  "Perp funding data-semantics + cadence: registry inconsistency, funding_timestamp one-settlement offset, no historical
  cadence tracker"
created: 2026-06-16
status: active
priority: P1
locked_by: live-defi-rollout
source:
  - 2026-06-16 carry_staked_basis funding-carry scan (e2e-testing/scripts/defi/staked_basis_funding_scan.py) — empirical
    exchange-API spot-checks vs GCS derivative_ticker
parent_epic: mtds_mdps_master
---

# Perp funding data-semantics + cadence (2026-06-16)

Three related correctness gaps in how perp **funding** is annualised and time-stamped across the workspace, found while
building a `carry_staked_basis` funding-carry analysis that reads `data_type=derivative_ticker` funding from GCS and
cross-checks against the venue APIs. Funding is a P0 input to `carry_staked_basis` net-carry — a cadence error mis-ranks
the whole book.

## What I found

### Finding 1 — two funding-cadence registries disagree; one is wrong (P1, data-correctness)

Two SSOTs encode per-venue funding cadence and they **disagree**:

- `unified_api_contracts/registry/perp_funding_cadence.py` → `FUNDING_CADENCE_SECONDS` (consumed by
  `annualise_funding_rate_bps`, features-service, risk): **aster = 8h, deribit = 1h**.
- `unified-trading-library/unified_trading_library/return_metrics.py:58` → `FUNDING_PERIODS_PER_DAY`: **ASTER = 24.0
  (1h), DERIBIT = 3.0 (8h)** — the inverse for both.

**Empirically resolved against the exchange APIs (2026-06-16):**

| Venue       | API probe                                                                  | True cadence    | UAC `perp_funding_cadence` | UTL `FUNDING_PERIODS_PER_DAY` |
| ----------- | -------------------------------------------------------------------------- | --------------- | -------------------------- | ----------------------------- |
| Binance     | `fapi/v1/fundingRate` `fundingTime` spacing = 28 800 s                     | 8h (3/day)      | 8h ✅                      | 3.0 ✅                        |
| **Aster**   | `fapi.asterdex.com/fapi/v1/fundingRate` `fundingTime` spacing = 28 800 s   | **8h (3/day)**  | 8h ✅                      | **24.0 ❌ (8× over)**         |
| **Deribit** | `public/get_funding_rate_history` returns **hourly** rows w/ `interest_1h` | **1h (24/day)** | 1h ✅                      | **3.0 ❌ (8× under)**         |
| Hyperliquid | `info fundingHistory` spacing = 3 600 s                                    | 1h (24/day)     | 1h ✅                      | 24.0 ✅                       |
| OKX         | `funding-rate-history` `fundingTime` spacing = 28 800 s                    | 8h (3/day)      | 8h ✅                      | 3.0 ✅                        |

So **`perp_funding_cadence` (UAC) is correct; `FUNDING_PERIODS_PER_DAY` (UTL) is wrong for Aster (8× over-states) and
Deribit (8× under-states).** Any consumer of `FUNDING_PERIODS_PER_DAY` mis-annualises Aster/Deribit funding by 8×.
`strategy-service/.../trace_carry_staked_basis.py` and `return_metrics.py` are the suspected consumers — audit + repoint
to the UAC SSOT, then delete `FUNDING_PERIODS_PER_DAY` (no parallel registries).

> Note — Deribit funding normalisation: Deribit charges **hourly** (`interest_1h`) but also publishes an `interest_8h`
> figure. Whatever MTDS stores in the Deribit `derivative_ticker.funding_rate` must be annualised at the cadence that
> matches that figure (1h if it's the per-hour rate). Confirm the Tardis→MTDS Deribit funding field is the per-hour rate
> before trusting `annualise(rate, "deribit")` at 24/day.

### Finding 2 — `funding_timestamp` is offset by one settlement vs the venue's official `fundingTime` (P1)

GCS `derivative_ticker.funding_rate` **values match the exchange API exactly** (verified Binance BTCUSDT 2026-04-29:
`+0.00001305 / −0.00002840 / +0.00003571` identical) — the data is clean. **But** the pairing is offset: grouping the
GCS rows by `funding_timestamp` and taking the rate yields each rate paired with the **next** settlement, whereas the
venue's official `fundingTime` is the settlement instant the rate is **charged at**. Concretely the rate Binance charges
at 08:00 appears in GCS under `funding_timestamp` 16:00.

Consequence: you **cannot currently read exact discrete per-settlement funding** off the parquet by grouping on
`funding_timestamp` — it mislabels at day boundaries (and double-counts the boundary rate). The analysis harness works
around it with the **day-mean of the rate column** (offset-robust, matches what features-service effectively does), but
that is a workaround, not the target. **We should be able to use exact discrete funding** (per-settlement, correctly
time-stamped to the charge instant) — for accurate realised-funding accounting and for using `predicted_funding_rate`
(already a column) to gauge entry on venues that publish a forward rate. Likely fix: have the MTDS adapter persist the
funding settlement as `(fundingTime = charge instant, fundingRate = rate charged then)` matching the venue API, OR add a
canonical `funding_settlement` data_type with one row per settlement. Audit `funding_timestamp` semantics across
adapters (Tardis cefi, hyperliquid, the OKX `next_funding_timestamp` mapping) and document the canonical meaning.

### Finding 3 — `perp_funding_cadence` is STATIC; no historical cadence tracker (P2)

`FUNDING_CADENCE_SECONDS` is a single static dict — it has **no historical versioning**, so a venue changing its funding
interval over time (e.g. a pair moving 8h→4h, or a venue-wide change) is invisible and would silently mis-annualise
historical windows. We need a **historical funding-cadence tracker in GCS**, sourced either canonically (from venue docs
via a maintained script) or **inferred from the observed frequency of funding_timestamp/`fundingTime` updates** in the
captured data (the data already lets us count settlements/day per instrument per day). The analysis harness already
records observed `n_settlements` per shard as a cross-check seed for this.

## Why it matters

`carry_staked_basis` ranks the entire perp book by annualised funding; an 8× cadence error on Aster/Deribit, a
boundary-mislabelled discrete read, or a silently-stale static cadence all corrupt the ranking → wrong coins selected,
wrong net carry, wrong promote decision. This is the data-pipeline-correctness heartbeat for the CeFi funding leg.

## Recommended decision / todos

- [x] ✅ [DATA] P1. Audit every consumer of UTL `return_metrics.FUNDING_PERIODS_PER_DAY`; repoint to UAC; delete it (no
      parallel registry); UAC unit test. **DONE 2026-06-17** via the e2e correctness dispatch
      (`e2e_defi_strategy_funding_apr_gas_correctness_2026_06_17.md`): UTL dict DELETED
      (unified-trading-library@b587b91b/ ed622af8), execution decision-trace repointed (execution-service@38c7e06f),
      strategy docstring repointed (strategy-service@b91d3e1f), delta_one funding_oi repointed (features-service,
      pending peer-UAC-dirt), UAC regression tests (aster=8h, deribit=8h-figure, venue-dir norm)
      (unified-api-contracts@7fade10/fd5bcfa). **NB the test asserts deribit=8h-FIGURE, not 1h** — superseded by the
      next todo's confirmation.
- [x] ✅ [DATA] P1. Confirm the MTDS Deribit `derivative_ticker.funding_rate` figure. **CONFIRMED 2026-06-17 (e2e
      empirical probe): it is the 8h FIGURE** (≈ API `interest_8h` ~ -1e-6, not `interest_1h` ~ -1e-8), NOT the per-hour
      rate. Resolution: UAC `FUNDING_CADENCE_SECONDS["deribit"]` corrected `1h → 8h` so `annualise(rate,"deribit")`
      matches the stored 8h figure (preserves the data-matches-API invariant; the prior 1h over-stated Deribit APY 8×).
      Documented in the `perp_funding_cadence.py` module docstring (figure-vs-charge distinction). The codex/02-data doc
      update rides the codex-audit below.
- [ ] [DATA] P1. Make exact discrete per-settlement funding readable: persist funding settlements time-stamped to the
      charge instant (matching venue `fundingTime`), or add a canonical per-settlement funding data_type. Document the
      canonical `funding_timestamp` meaning across adapters. **Repo: market-tick-data-service + unified-api-contracts.**
- [ ] [DATA] P2. Add a historical funding-cadence tracker in GCS (canonical-from-docs or inferred from observed
      settlement frequency) so historical annualisation survives a venue cadence change. **Repo: unified-api-contracts +
      market-tick-data-service.**
- [ ] [DATA] P2. Backfill Aster perp funding into GCS — the handler + public endpoint work
      (`fapi.asterdex.com/fapi/v1/fundingRate`, no auth, 8h); only the backfill VM was never run for Aster. **Repo:
      market-tick-data-service + deployment-service** (`launch-mtds-perp-funding-backfill-vm.sh` with `--perp-protocols`
      incl. aster, start 2024-09-25).
- [ ] [DATA] P2. Genesis is PER-(venue, data*type), not per-venue — encode it. Aster API availability (verified
      2026-06-16): funding **2023-07-22**, OHLCV/klines **2023-01-01** (both pre-date the `venue_launch_dates`
      ASTER=2024-09-25 floor — Astherus pre-rebrand history; pick a trust floor), mark/index via klines/premiumIndex,
      trades partial (id/time-paginated), **open_interest + L2 book = live-capture-only (no historical endpoint →
      forward-only)**. Canonize the Aster native API INTO the Tardis CEX benchmark schemas (klines→OHLCV,
      aggTrades→`trades`, premiumIndex+funding+OI→`derivative_ticker`, depth-WS→`book_snapshot_5`) so downstream can't
      tell it's not Tardis; record genesis per data_type with `captured`/`expected_unattempted` honest-absence for the
      forward-only ones. **Repo: market-tick-data-service + unified-api-contracts.** **— derivative_ticker + genesis leg
      ✅ DONE 2026-06-17 (operator "fully hook up"): `uac@61d5838` (BATCH_ASTER/ LIVE_ASTER/REPLAY_ASTER members + aster
      capability + `(cefi,derivative_ticker)` source priority), `utl@3b4bd6b8` (`ASTER→BATCH_ASTER` venue override =
      self-archive source `aster`, not Tardis), `mtds@5978627` (`venue_data_types` += `derivative_ticker`;
      `_perp_funding_hl_aster._write_aster_derivative_ticker` emits `CanonicalDerivativeTicker` at `asset_group=cefi`,
      source-aware `batch_aster`/`live_aster`, shard-isolated from the funding leg; genesis per-(venue,data_type) in
      `expected_start_dates.yaml`).** **— trades leg ✅ DONE 2026-06-17 (operator "yeah wire it"): `mtds@889b131` —
      `_perp_funding_hl_aster._write_aster_trades` fetches `/fapi/v1/aggTrades` (paginated by `fromId`, day-windowed)
      per symbol, maps onto `AsterTrade`→`normalize_aster_trade`→`CanonicalTrade`, writes `data_type=trades` at
      `asset_group=cefi`, `source=aster`, source-aware `batch_aster`/`live_aster`, shard-isolated from the funding leg
      (Live=Batch, one run). `trades` is in the cefi `_LEGAL_DATA_TYPES` + Aster `venue_data_types.yaml`; genesis
      `2021-08-30` already in `expected_start_dates.yaml`. NO UTL change (the `ASTER→BATCH_ASTER` override is
      data_type-independent). Unit test `test_writes_canonical_trades_shard_cefi` asserts the cefi shard path +
      `m`→buy/sell mapping. NB the trades write rides `_collect_aster` (funding-genesis-gated) → it covers the
      **2024-09-25-forward** window; the pre-funding-genesis trades window (2021-08-30→2024-09-25) needs a standalone
      trades collect (todo below). `fetch_klines`+`fetch_depth` adapter scaffolds also landed (one-step-from-ready for
      the OHLCV+book write legs).** \*\*— OHLCV/klines leg: DESIGN DECISION 2026-06-17 —
      `ohlcv*_`is NOT canonized into the cefi tick-data write     (intentional, documented).**`ohlcv*1m`/`ohlcv_15m`/`ohlcv_24h` are registered in UAC (`market_data_categories.py`/     `schema_spec.py`) but are a **TradFi-only** data_type: NOT in the cefi `\_LEGAL_DATA_TYPES` (`tardis_shared.py:73`—     the cefi path builder hard-rejects it), NOT in ANY cefi venue's`venue_data_types.yaml`, NOT in cefi     `SOURCE_PRIORITY`, with NO cefi consumer (MDPS consumes `CanonicalOhlcvBar`for TradFi only; CeFi strategies derive     candles from`trades`). The two reference CeFi venues (BINANCE-FUTURES/BYBIT) deliberately omit ohlcv. Introducing     an orphaned cefi `ohlcv*_`would create dead surface + false expected-absent rows — the exact anti-pattern the Aster    `venue_data_types.yaml`comment warns against. The`fetch_klines`adapter fetch +`normalize_aster_kline` transform     ARE ready; see the tight remaining todo below for the exact one-step write if a cefi ohlcv consumer is ever wired.     **— book/`book_snapshot_5`leg: batch honest-absence ALREADY CORRECT (no change needed); live WS connector is the     tight remaining unit.** Aster book is`L2_MBP`→`book_snapshot_5`(NOT tbbo);`/fapi/v1/depth` is a live snapshot     only (Binance-compatible, no historical depth) → batch is forward-only honest-absent, already encoded     (`expected_start_dates.yaml`ASTER`book_snapshot_5:
      null`+ absent from Aster's batch`data_types` → no false     expected-absent). A live Aster **trades** WS connector exists (`live/connectors/aster_ws.py`); a live **book** WS     connector does not yet. `fetch_depth`
      scaffold landed. See the tight live-book todo below. **Repo: market-tick-data-service + unified-api-contracts.**
- [ ] [DATA] P3. Aster **pre-funding-genesis trades window** (2021-08-30 → 2024-09-25): the canonical Aster `trades`
      write rides `_collect_aster` which is funding-genesis-gated (2024-09-25), so it only covers the forward window. To
      capture the earlier trades history (genesis 2021-08-30, `expected_start_dates.yaml`), add a **standalone trades
      collect** (a `--cefi-operations trades` op or a dedicated handler) that runs aggTrades on the trades genesis floor
      independent of the funding floor — reusing `_write_aster_trades` (already trades-genesis-agnostic). **Repo:
      market-tick-data-service.**
- [ ] [DATA] P3. Aster **OHLCV/klines→`ohlcv_*` cefi write** (ONLY if/when a cefi ohlcv consumer is wired — currently
      orphaned, see the design decision above): the `AsterAdapter.fetch_klines` fetch + `normalize_aster_kline`
      (`AsterKline`→`CanonicalOhlcvBar`) transform are ready. Remaining one-step: extend the cefi `_LEGAL_DATA_TYPES`
      (`tardis_shared.py`) + add `ohlcv_*` to Aster's `venue_data_types.yaml` data_types + cefi `SOURCE_PRIORITY` +
      genesis `2023-01-01` (klines) in `expected_start_dates.yaml`, then a `_write_aster_ohlcv` mirroring
      `_write_aster_trades`. Do NOT wire until a cefi consumer exists (else dead surface + false expected-absent).
      **Repo: market-tick-data-service + unified-api-contracts.**
- [ ] [DATA] P3. Aster **live `book_snapshot_5` WS connector** (forward-only; batch is correctly honest-absent already):
      add a live Aster depth-WS/poll book connector mirroring `live/connectors/aster_ws.py` (the existing live trades
      connector) → parse depth into the 5-level `bid_px_0X`/`bid_sz_0X`/`ask_px_0X`/`ask_sz_0X` shape
      (`normalize_aster_orderbook`), write via `MTDSShardManifestRecorder.record_captured` at
      `data_type=book_snapshot_5`, `pipeline_mode=live_aster`, `source=aster`; register via
      `register_ws_feed_connector(venue="ASTER", …)`. `AsterAdapter.fetch_depth` (`/fapi/v1/depth` snapshot) is the REST
      fallback building block. **Repo: market-tick-data-service.**
- [ ] [DATA] P3. Aster margining model (`venue_collateral.py`): USDC (0% haircut, CROSS) / USDT (1%) only — rejects
      spot-coin AND LST collateral. So Aster supports a stablecoin-margined funding-short ONLY (no same-venue
      cash-and-carry, no staking leg). Re-verify against live Aster docs before sizing; the ETH staked-basis needs
      Bybit/OKX/Deribit (stETH/wstETH cross-margin). **Repo: unified-api-contracts (registry verification).**

## Progress Log — Aster canonicalization remaining legs (2026-06-17, autonomous)

Continuing the line-111 "canonize Aster native API INTO the Tardis CEX schemas" todo. derivative_ticker leg already
landed (uac@61d5838 / utl@3b4bd6b8 / mtds@5978627). This session drives the remaining trades / ohlcv / book legs.

**Verified system reality (read, not assumed):**

- `trades` IS in the cefi tick-data `_LEGAL_DATA_TYPES` (`tardis_shared.py:73`), IS in Aster's `venue_data_types.yaml`
  list, genesis already set (`expected_start_dates.yaml` ASTER `trades: 2021-08-30`). UTL
  `_VENUE_OVERRIDES["ASTER"] = BATCH_ASTER` is data_type-independent → trades resolves source-aware
  `batch_aster`/`live_aster` with NO UTL change. **BUT** no canonical-cefi trades WRITE path exists today (neither Aster
  NOR Hyperliquid — both declared, neither written; the perp_funding handler only writes
  `perp_funding`+`derivative_ticker`). The transform `normalize_aster_trade(AsterTrade)` exists in UAC; aggTrades
  returns the `AsterAggTrade` shape (p/q/T/m).
- `ohlcv_*` (`ohlcv_1m`/`ohlcv_15m`/`ohlcv_24h`) is **NOT** in the cefi `_LEGAL_DATA_TYPES`, **NOT** in ANY cefi venue's
  `venue_data_types.yaml`, **NOT** in cefi `SOURCE_PRIORITY`, and has **NO cefi consumer** — it is a **TradFi-only**
  data_type (CME/CBOE via Databento/Barchart; MDPS consumes `CanonicalOhlcvBar` for TradFi only). The two reference CeFi
  venues (BINANCE-FUTURES / BYBIT) do **NOT** wire ohlcv at all — CeFi strategies derive candles from `trades`. The UAC
  transform `normalize_aster_kline(AsterKline)` exists.
- Aster `book` is `book_type: L2_MBP` → canonical type is **`book_snapshot_5`** (NOT tbbo — tbbo is the TradFi L1 top of
  book). `/fapi/v1/depth` is a **live snapshot only** (Binance-Futures-compatible, no historical depth endpoint).
  `expected_start_dates.yaml` ASTER `book_snapshot_5: null` + the `venue_data_types.yaml` comment already encode the
  forward-only / live-capture-only honest absence (NOT listed in Aster's batch `data_types` → no false expected-absent
  rows). A live Aster **trades** WS connector exists (`live/connectors/aster_ws.py`); NO live book/depth connector yet.

**Design decisions (AUTONOMOUS rule 1 — least-bad path consistent with the documented intent AND the system as wired):**

1. **trades → WIRE FULLY** (in scope, legal, genesis-ready). Mirror `_write_aster_derivative_ticker`: a best-effort,
   shard-isolated `_write_aster_trades` called from `_collect_aster` (Live=Batch single pass), fetching aggTrades per
   symbol for the day, `normalize_aster_trade`→`CanonicalTrade`, written to `data_type=trades` at `asset_group=cefi`,
   `source=aster`, source-aware `batch_aster`/`live_aster`. + per-(venue,data_type,source) manifest row.
2. **ohlcv → DO NOT introduce an orphaned cefi `ohlcv_*` data_type; leave a tight todo.** Wiring a brand-new cefi
   data_type that no cefi venue carries, that `_LEGAL_DATA_TYPES` rejects, that has zero consumer, and that the two
   reference CeFi venues deliberately omit, is the exact anti-pattern (false expected-absent + dead surface). The
   mission authorizes "if disproportionate, leave a tight todo." Adapter scaffold (`fetch_klines`) IS added so the data
   path is one method from ready; the canonical write is the tight remaining step (below). Klines genesis 2023-01-01
   captured in the todo.
3. **book → batch honest-absence is ALREADY correct (live-capture-only); live WS book connector is a tight todo.** No
   batch change needed (already `null` genesis + absent from batch `data_types`). The live depth-WS connector is a
   separate live-infra unit (a new `aster_book_ws` connector + live-manifest wiring) — tight todo below.
