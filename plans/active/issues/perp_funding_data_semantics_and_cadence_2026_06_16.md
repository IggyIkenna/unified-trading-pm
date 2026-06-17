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

- [x] ✅ [DATA] P1. Audit every consumer of UTL `return_metrics.FUNDING_PERIODS_PER_DAY`; repoint to UAC; delete it
      (no parallel registry); UAC unit test. **DONE 2026-06-17** via the e2e correctness dispatch
      (`e2e_defi_strategy_funding_apr_gas_correctness_2026_06_17.md`): UTL dict DELETED (unified-trading-library@b587b91b/
      ed622af8), execution decision-trace repointed (execution-service@38c7e06f), strategy docstring repointed
      (strategy-service@b91d3e1f), delta_one funding_oi repointed (features-service, pending peer-UAC-dirt), UAC
      regression tests (aster=8h, deribit=8h-figure, venue-dir norm) (unified-api-contracts@7fade10/fd5bcfa).
      **NB the test asserts deribit=8h-FIGURE, not 1h** — superseded by the next todo's confirmation.
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
- [ ] [DATA] P2. Genesis is PER-(venue, data_type), not per-venue — encode it. Aster API availability (verified
      2026-06-16): funding **2023-07-22**, OHLCV/klines **2023-01-01** (both pre-date the `venue_launch_dates`
      ASTER=2024-09-25 floor — Astherus pre-rebrand history; pick a trust floor), mark/index via klines/premiumIndex,
      trades partial (id/time-paginated), **open_interest + L2 book = live-capture-only (no historical endpoint →
      forward-only)**. Canonize the Aster native API INTO the Tardis CEX benchmark schemas (klines→OHLCV,
      aggTrades→`trades`, premiumIndex+funding+OI→`derivative_ticker`, depth-WS→`book_snapshot_5`) so downstream can't
      tell it's not Tardis; record genesis per data_type with `captured`/`expected_unattempted` honest-absence for the
      forward-only ones. **Repo: market-tick-data-service + unified-api-contracts.**
- [ ] [DATA] P3. Aster margining model (`venue_collateral.py`): USDC (0% haircut, CROSS) / USDT (1%) only — rejects
      spot-coin AND LST collateral. So Aster supports a stablecoin-margined funding-short ONLY (no same-venue
      cash-and-carry, no staking leg). Re-verify against live Aster docs before sizing; the ETH staked-basis needs
      Bybit/OKX/Deribit (stETH/wstETH cross-margin). **Repo: unified-api-contracts (registry verification).**
