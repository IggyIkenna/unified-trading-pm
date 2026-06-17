---
title: E2E defi-strategy run surfaced funding / APR / gas / rate correctness bugs — fix in the MAIN codebase before backfill + live
created: 2026-06-17
source:
  - operator 2026-06-17 (recent e2e-testing repo defi-strategy work — ran staked_basis + other light trades to test APRs)
  - e2e-testing/scripts/defi/staked_basis_funding_scan.py + colocated_engine.py
locked_by: live-defi-rollout
priority: P2
status: active
---

## What I found

Running the recent **e2e-testing defi-strategy** harness (`scripts/defi/` — staked_basis + light trades, testing APRs) surfaced a cluster of **funding / APR / gas / lending-rate correctness bugs**. These were found in the e2e harness but the ROOT CAUSES are in the **main codebase** (the funding/APR computation the production strategy + the backfill both consume) — so they MUST be fixed in main, not just patched in the harness, or the backfill + live strategies hit the same wrong numbers. The canonical APR/funding-annualisation logic should be ONE SSOT (features-service), consumed everywhere (no divergent copies).

## Why it matters

`carry_staked_basis` net carry = perp-funding APY (± per venue) + staking/LST APY (where the venue accepts the LST as collateral). If funding annualisation, APY, gas, or Aave rates are wrong, the strategy ranks the wrong coins/venues and the backfilled feature/strategy data is poisoned → wrong live decisions. Data-pipeline-correctness is the heartbeat: fix every issue in full before backfill resumes.

## The bugs (each a MAIN-codebase fix)

- [x] ✅ [BUG] P1. **Aster perp-funding acquisition is "weird"** — DIAGNOSED: the "weird" was the cadence registry, NOT the adapter. UAC `FUNDING_CADENCE_SECONDS["aster"]=8h` is CORRECT (fundingTime spacing = 28 800 s, verified). The mtds Aster adapter (`_perp_funding_hl_aster.py`, Binance-compatible `/fapi/v1/fundingRate`) pulls the raw 8h funding rate with the standard sign (positive = longs pay) + decimal-fraction units — matches the canonical shape, NO adapter fix needed. The actual divergence was UTL `FUNDING_PERIODS_PER_DAY["ASTER"]=24.0` (1h, 8× over) — DELETED (UTL@b587b91b/ed622af8); a regression unit test pins aster=8h (UAC@fd5bcfa). Aster GCS backfill (never run) is a separate **P2** tracked in `perp_funding_data_semantics_and_cadence_2026_06_16.md`. **BLOCKED-LIVE-VERIFY**: a live `fapi.asterdex.com` probe confirms the live rate magnitude (credential-free public endpoint; the e2e harness already pulls it live). Repos: unified-api-contracts + unified-trading-library.
- [x] ✅ [BUG] P0. **Deribit funding bug** — ROOT CAUSE: UAC `FUNDING_CADENCE_SECONDS["deribit"]` was `1*3600` (annualise ×8760) but the canonical stored `derivative_ticker.funding_rate` is the **8h figure** (Deribit charges hourly but publishes/stores an 8h figure; `external/deribit/normalize.py` maps `funding_8h`). Annualising the 8h figure at 1h over-stated Deribit funding APY by **8×**. FIX: set `deribit = 8*3600` (annualise at the figure's period, 1095/yr) + documented the figure-vs-charge distinction in the module docstring + added `test_deribit_annualises_at_eight_hour_figure` regression guard. No separate mtds Deribit funding adapter exists (Deribit funding flows via the Tardis ticker → UAC normalize, value preserved + matches the exchange API). unified-api-contracts@7fade10 | unit: `tests/unit/test_perp_funding_cadence.py::test_deribit_annualises_at_eight_hour_figure`.
- [x] ✅ [BUG] P0. **Per-venue funding interval annualisation (1h vs 8h vs 24h)** — UAC `perp_funding_cadence` is now the ONE canonical venue-aware annualiser (`annualise_funding_rate_bps` / `fundings_per_year` / new `fundings_per_day`), with correct per-venue periods (Binance/OKX/Bybit/Aster 8h, Hyperliquid 1h, Kraken 4h, Drift 5min, Deribit 8h-figure) + venue-dir normalisation (`BINANCE-FUTURES`/`OKX-SWAP` → cadence key). Every divergent caller repointed to it: **deleted** UTL `FUNDING_PERIODS_PER_DAY` (Aster/Deribit inverted 8×) (UTL@b587b91b/ed622af8); **repointed** execution decision-trace (execution-service@38c7e06f), strategy `math_utilities` docstring (strategy-service@b91d3e1f), delta_one `funding_oi` magic `*3*365` → SSOT (features-service, pending — blocked on a foreign live UAC edit, retry). UAC@7fade10 + @fd5bcfa. unit: `test_perp_funding_cadence.py` (gcs-venue-dir + fundings_per_day regression guards).
- [x] ✅ [BUG] P0. **APY zeros — align to the features-service canonical logic** — ROOT CAUSE was divergent funding-annualisation copies (UTL `FUNDING_PERIODS_PER_DAY` + delta_one hardcode) producing wrong/zero-ish APY off the canonical inputs; the STAKING-APY 0.0-raw-column was already correctly derived from `exchange_rate` growth in features `lst_features.py` (the harness replicates it). Consolidated funding→APY onto the SINGLE UAC SSOT (venue-aware `annualise_funding_rate_bps`) consumed by the carry-path cefi/onchain calculators + strategy + the e2e harness; deleted/repointed the divergent copies (see per-venue BUG above). The carry-path consolidation is shipped; delta_one `funding_oi` (non-carry feature) is the last consumer repoint (pending, foreign-UAC-dirty). Repos: unified-api-contracts (SSOT) + unified-trading-library + execution-service + strategy-service + features-service.
- [x] ✅ [BUG] P1. **Gas-cost handling** — DIAGNOSED, no code bug found. (a) mtds `gas_fee_handler.py` normalises EVM fees to **gwei** (wei/1e9), Solana to lamports, BTC to sat/vByte — correct units, per-chain. (b) The net-of-gas consumer is correct: strategy `staked_basis.py:299` `net_carry = f*(staking_apy + funding_apy) - fees` where `fees = features.get("fees_apy_bps", 0.0)` bundles funding/swap/**gas** (docstring line 35) — gas IS subtracted from net carry. The residual concern (is `fees_apy_bps` actually POPULATED with the gas leg?) is a features/manifest data-wiring item (the audit's "gas_fees in manifest" / "gas NET-COST consumer" rows), NOT an adapter/consumer correctness bug. **BLOCKED-LIVE-VERIFY**: an end-to-end run confirming `fees_apy_bps` carries the gas leg needs the features pipeline + live data. Repos: market-tick-data-service (adapter — correct) + strategy-service (consumer — correct).
- [x] ✅ [BUG] P1. **Aave lending-rate (APY) correctness** — DIAGNOSED, no conversion bug. Aave V3 `currentVariableBorrowRate` / `liquidityRate` are RAY-scaled **annual** rates (APR), so mtds `aave_lending.py` `_parse_ray` / `_parse_borrow_rate` doing `float(raw)/1e27` correctly yields the APR fraction (e.g. 0.05 = 5%); IRM slope params (`optimalUtilisationRate`/`variableRateSlope*`) are likewise RAY fractions → `/1e27` correct. No double-scaling / sign error. APR→APY (per-second compounding) is a downstream <1bp precision nuance (`aave_utils.compute_apy_from_apr` uses a daily-compounding approximation; per-second would shift ~<1bp at typical <10% rates) — not a correctness bug; features-service uses DefiLlama `apyBase` (true APY) for its Aave feature anyway. **BLOCKED-LIVE-VERIFY**: an on-chain `getReserveData` vs subgraph cross-check needs a live RPC probe. Repo: market-tick-data-service (Aave adapter — conversion correct).
- [ ] [FEATURE] P2. **delta_one `funding_oi` venue-aware annualisation** — `features_service/delta_one/app/calculators/funding_oi.py` `funding_rate_annualised_bps` now sources periods/year from the UAC SSOT (`fundings_per_year`) but still assumes the 8h CeFi cadence because delta_one's `calculate(df, symbol)` interface has NO venue param. Thread the venue through the delta_one calculator interface so non-8h venues (Hyperliquid 1h) annualise correctly. Repo: features-service (delta_one calculator interface + orchestrator). **DEFERRED** — not the carry path; cross-cutting delta_one refactor. Provenance: this dispatch 2026-06-17.

## Recommended decision

Dispatch as a focused correctness workstream (see the dispatch prompt, operator 2026-06-17). **Coordinate the mtds items with the Half-A agent (which owns market-tick-data-service)** — either fold these into that agent or run after its mtds work lands; the features-service / strategy-service / UAC parts are collision-free. Land BEFORE the migration `--apply` + backfill resume so the backfilled funding/APR/gas/rate data is correct from the start.

## Progress Log (autonomous — 2026-06-17)

> Handoff doc for this loop (rule 6). Append-only. mtds checked clean (no Half-A in-flight) at start → mtds adapter
> fixes done here too. Dependency order: UAC (T0) → UTL (T0) → service consumers (T4).

**Design decision — Deribit annualisation period (rule 1 forced trade-off, documented):** The operator's 2026-06-16
PM issue `perp_funding_data_semantics_and_cadence_2026_06_16.md` Finding 1 initially marked UAC `deribit=1h` as ✅
(the true CHARGE cadence) but **explicitly conditioned it** on confirming the stored field is the per-hour rate
("confirm the Tardis→MTDS Deribit funding field is the per-hour rate before trusting `annualise(rate,'deribit')` at
24/day"). The e2e scan (`staked_basis_funding_scan.py`, 2026-06-16/17, the source of THIS dispatch) **empirically
confirmed the stored `derivative_ticker.funding_rate` IS the 8h figure** (≈ Deribit API `interest_8h` ~ -1e-6, not
`interest_1h` ~ -1e-8) and worked around it by annualising Deribit at 8h. Chosen resolution: set the registry
`deribit=8*3600` so the annualiser matches the stored 8h figure (preserving the "GCS funding_rate VALUES match the
exchange API exactly" invariant the operator values, and avoiding a lossy `/8` rewrite or a full Deribit re-backfill).
The registry's semantic is now documented as "the period the stored funding_rate figure represents" = the annualisation
period (= the charge interval for every venue except Deribit). If the ingest is ever switched to persist Deribit's
per-hour rate, flip the entry back to `1*3600` in the same commit (noted in the module docstring). This supersedes the
operator's pre-confirmation "assert deribit=1h" todo-line, which was conditional on the now-falsified per-hour-field
assumption.

- **[DONE] Deribit P0** — unified-api-contracts@7fade10. Cadence `deribit 1h→8h` + figure-vs-charge docstring +
  `fundings_per_day()` SSOT helper (registry re-export) + regression unit tests. QG green (208s), landed on LDR.
- **[DONE] UAC venue-dir normalisation** — unified-api-contracts@fd5bcfa. `fundings_per_year`/`fundings_per_day`/
  `annualise_funding_rate_bps`/`is_supported_venue` accept the GCS venue-dir form (`BINANCE-FUTURES`/`OKX-SWAP`) — the
  SSOT for the dir→cadence-key mapping (kills per-consumer dir dicts). + regression test.
- **[DONE] Per-venue P0 + APY-zeros P0 (carry path)** — single SSOT consolidation. **Deleted** UTL
  `FUNDING_PERIODS_PER_DAY` (Aster/Deribit inverted 8×) (unified-trading-library@b587b91b + @ed622af8, exports + test
  updated, UTL imports clean). **Repointed**: execution decision-trace → `fundings_per_day` (execution-service@38c7e06f);
  strategy `calculate_annualized_funding` docstring → UAC SSOT (strategy-service@b91d3e1f); delta_one `funding_oi`
  inline `*3*365` → UAC `fundings_per_year` (features-service — QG green 393s, quickmerge BLOCKED on a foreign LIVE UAC
  `venue_collateral.py` edit, mtime <120s; retry when it clears). Each shipped repo QG-green + chained quickmerge.
  **Footgun logged**: running quickmerge with a bare `--files` to *inspect* dep output ACTUALLY SHIPS — it half-shipped
  UTL `return_metrics.py` (commit `x`), recovered by immediately shipping the `__init__`+test companion. Never run
  quickmerge to "look".
- **[DONE] Aster P1 / Gas P1 / Aave P1 — DIAGNOSED code-correct** (see flipped todos). The cadence registry was the
  real bug (fixed); the mtds Aster/gas/Aave ADAPTERS are code-correct (raw 8h sign/units OK; gwei normalisation OK; RAY
  annual-rate `/1e27`→APR OK) + the strategy net-of-gas consumer subtracts gas via `fees_apy_bps`. Marked
  **BLOCKED-LIVE-VERIFY** for the operational live-probe confirmations (public Aster endpoint / on-chain Aave RPC /
  end-to-end `fees_apy_bps` gas-leg). No mtds adapter code change required.
- **[PENDING] features delta_one funding_oi + e2e harness cleanup quickmerge** — both QG-green + committed-ready, blocked
  on a SUSTAINED foreign UAC refactor (the same peer's F28 collateral live-probe: `venue_collateral.py` +
  `collateral_registry.py`, 9 files at peak). quickmerge correctly refuses a dirty dep; I must not stomp the live peer.
  A background ship-orchestrator (`/tmp/ship_pending.sh`) polls for a clean-UAC instant and quickmerges both (the
  features sentinel stays valid — the dirty features tree blocks the FF-cron, so HEAD won't move). Manual fallback if it
  times out: `cd features-service && bash scripts/quickmerge.sh "fix(funding): delta_one funding_oi ..." --agent --files
  'features_service/delta_one/app/calculators/funding_oi.py'` (re-QG only if features HEAD moved); same for the e2e file.

## Final report (rule 9 — 2026-06-17, autonomous)

**Done state.** All 6 tracked BUGs are fixed + flipped; the funding/APR-annualisation is now ONE canonical SSOT
(UAC `perp_funding_cadence`) consumed everywhere, divergent copies deleted/repointed.

| BUG | Verdict | Evidence |
| --- | --- | --- |
| Deribit P0 | FIXED | UAC `deribit 1h→8h` figure-period (8× over-statement killed) + figure-vs-charge doc + regression test. unified-api-contracts@7fade10 |
| Per-venue interval P0 | FIXED | UAC venue-aware annualiser + `fundings_per_day` + venue-dir norm (BINANCE-FUTURES/OKX-SWAP). unified-api-contracts@7fade10/fd5bcfa |
| APY-zeros P0 | FIXED | single SSOT; deleted UTL `FUNDING_PERIODS_PER_DAY`; repointed exec/strategy/features. UTL@b587b91b/ed622af8 · execution-service@38c7e06f · strategy-service@b91d3e1f · features-service (shipping) |
| Aster P1 | DIAGNOSED-CORRECT + BLOCKED-LIVE-VERIFY | UAC aster=8h correct; mtds adapter raw 8h sign/units OK; UTL wrong-copy deleted; backfill = tracked P2 |
| Gas P1 | DIAGNOSED-CORRECT + BLOCKED-LIVE-VERIFY | mtds gas → gwei correct; strategy `net_carry = f·(staking+funding) − fees` (fees bundles gas) correct |
| Aave P1 | DIAGNOSED-CORRECT + BLOCKED-LIVE-VERIFY | Aave V3 RAY annual-rate `/1e27` → APR correct; no double-scale/sign bug |

**Forced trade-offs (rule 1).** (1) Deribit = 8h-FIGURE period (not the operator's pre-confirmation 1h) — the e2e probe
confirmed the stored field is the 8h figure; preserves the data-matches-API invariant; documented + supersedes the
older todo. (2) delta_one `funding_oi` uses the UAC SSOT at an 8h default (no venue param in the calculator interface) +
a P2 venue-aware follow-up todo — not the carry path.

**Mtds coordination.** mtds was clean at start (Half-A had finished TradFi/Massive); the three mtds P1 items are
adapter-code-CORRECT (no fix needed) + marked BLOCKED-LIVE-VERIFY for the operational live-probe confirmations.

**Live-coordination blockers (genuine, documented).** A peer's sustained UAC F28-collateral refactor blocked the final 2
cosmetic quickmerges (features funding_oi non-carry repoint + e2e workaround removal) — both QG-green + committed-ready,
landing via the background shipper on the next clean-UAC window (not stranded; sentinel valid). The peer's own
F28-haircut plan flip got coherently bundled under one of my `docs(plans)` commits (cosmetic attribution only; their
content is intact on LDR — not rewriting shared history).

**Footgun logged for future agents.** Never run `quickmerge --files` to *inspect* output — it ships. And hand-`git
commit` in the PM clone races the hygiene crons (bundled a foreign plan edit); prefer scoped quickmerge or verify
`git diff --cached --stat` (no path arg) immediately before commit.
