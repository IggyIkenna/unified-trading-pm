---
doc_type: plan
title: price-arbitrage-may-23-2026
summary:
status: complete
nature: record
asset_group: tradfi
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-08
plan_type: epic
owner: ikenna
last_updated: 2026-05-08
locked_by: live-defi-rollout
locked_since: 2026-05-08
parent: master_to_live_defi_2026_05_23
deadline: 2026-05-23
---

## Deferred work — migrated to: `plans/active/tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md` — successor:

tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20 (the 9 open success-criteria/open-question items — CME
same-day-expiry arb backtest, ETF↔future arb backtest, cross-venue ETF arb, backtest fidelity, TradFi data pipeline
clean, 2-year config grid, cross-venue ETF universe pick, backtest window pick — trace forward through the 2026-05-08
supersession into `tradfi_master_2026_05_07.md` (itself now archived) and land in this active plan, which explicitly
carries forward "the two folded May-23 deliverables (S&P prediction 'deliverable A' + price-arbitrage 'deliverable B')"
as its own scope: same-day-expiry arb, ETF↔future arb, cross-venue ETF arb, and the Group F backtest harness. Verified
by direct grep — this is the real living successor, not a guess.

# Epic — Price Arbitrage (CME futures + ETFs) (May 23 2026)

> **🔴 SUPERSEDED 2026-05-08** — folded into [`tradfi_master_2026_05_07.md`](./tradfi_master_2026_05_07.md) § "May-23
> deliverable B — Price arbitrage" per operator direction. This file is archived; content remains verbatim for
> archaeology. **Edit the master, not this file.**

## Why this epic exists

The price-arbitrage archetype family ships **backtest-only** for May 23. It covers:

- CME futures **same-day-expiry arbitrage** across ES / MES / micro variants (and BTC futures equivalents on CME).
- **ETF↔future arbitrage** — TradFi ETF spot vs CME futures carry/arb.
- **Cross-venue ETF arbitrage** — ETF on one venue vs the CME future, where the ETF is listed somewhere off CME.

Carry-as-archetype-family was originally drafted into this epic but was **moved to `live_defi_rollout_may_23_2026`** per
operator direction 2026-05-08 — carry's hedge legs span CME + CeFi + DeFi spot/perp/future combos and the live infra is
where it lands. This epic is now **price arbitrage only**, fully backtest.

## End-state at May 23 (success criteria)

- [ ] **Full backtest of CME same-day-expiry arbitrage** (ES vs MES + variants, BTC futures variants) running on 2-year
      representative history.
- [ ] **Full backtest of ETF↔future arbitrage** for the SP500 ETF set (SPY/IVV/VOO) vs ES futures.
- [ ] **Full backtest of cross-venue ETF arbitrage** (ETF venue × CME futures) wherever the ETFs are tradable.
- [ ] **Backtest fidelity**: real matching engine, real fees, real exchange-specific microstructure (CME tick rules, ETF
      NBBO, half-day calendar). Per Group F item 17 of master plan readiness.
- [ ] **Strategy + execution layers PROGRESSED, not gated** — no live trading, but the strategy/execution code paths
      exercise the unified pipeline correctly so when this archetype goes live post-May-23, the seam is small.
- [ ] **TradFi data pipeline clean** for all required instruments (ES/MES, BTC futures, SPY/IVV/VOO ETFs, half-day
      calendar, expiry calendar) across the backtest window.
- [ ] **2-year batch backtest config grid** for both arb archetypes — P&L variance per config dimension captured.

## What's IN scope

- Same-day-expiry arbitrage on CME (ES/MES/micros + BTC futures equivalents).
- ETF↔future carry/arb on CME and cross-venue ETF combinations.
- TradFi ETF backfill + futures continuous-contract rolling.
- Backtest fidelity for matching engine + fees + microstructure.
- Strategy + execution layers exercised through unified pipeline (batch-only).

## What's OUT of scope (shipping later)

- **Live trading** — backtest-only this cycle.
- **Carry-family archetypes** (staked-basis, vanilla-basis, cross-venue carry) — moved to `live_defi_rollout` epic.
- **Spot-vs-perp carry** for crypto — also moved to `live_defi_rollout` epic.
- **Production deployment** of the arb signal — backtest deliverable only.

## Sub-plans this epic consumes

| Path                                                                                                                                   | Role                                               | Status |
| -------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------- | ------ |
| [`tradfi_master_2026_05_07`](./tradfi_master_2026_05_07.md)                                                                            | TradFi data pipeline umbrella (CME futures + ETFs) | Active |
| [`active/instruments_and_market_tick_data_completion_2026_05_01`](../active/instruments_and_market_tick_data_completion_2026_05_01..md | Instruments + MTDS completion (CME + ETF backfill) | Active |
| [`strategy_and_dart_master_2026_05_07`](./strategy_and_dart_master_2026_05_07.md)                                                      | Strategy v2 + backtest harness                     | Active |
| [`active/writegate_honest_coverage_endtoend_2026_05_06`](../active/writegate_honest_coverage_endtoend_2026_05_06.md)                   | Write-gate / honest-coverage umbrella              | Active |

## Cross-epic handshakes

- **Depends on:** `cross_cutting_may_23_2026` for strategy catalogue (price-arb archetypes × all venue combos
  enumerated). `sp_prediction_may_23_2026` shares the ES/MES + ETF instrument + MTDS data — both epics rely on the same
  TradFi backfill clean.
- **Provides to:** Carry archetypes in `live_defi_rollout_may_23_2026` lift their backtest fidelity work from this
  epic's matching-engine + fee + calendar work.

## Cross-cutting concerns inherited

See [`cross_cutting_may_23_2026.epic.md`](./cross_cutting_may_23_2026.epic.md). Specific to this epic:

- **Strategy catalogue (HARD)**: price-arb archetypes × venue combos enumerated.
- **Infrastructure**: backtest harness, batch deployment maturity, matching-engine fidelity.

## Open questions

- [ ] **Cross-venue ETF universe**: which non-CME venues for the ETF leg? US-listed ETF + CME future is the obvious
      pair; international? CFD venues? Operator-pick.
- [ ] **Backtest window**: 2-year confirmed, or shorter to focus on recent regime?

## See also

- [`master_to_live_defi_2026_05_23`](../active/master_to_live_defi_2026_05_23.md) — May-23 cutover master
- [`/codex/04-architecture/backtest-groups.md`](/codex/04-architecture/backtest-groups.md)
- [`/codex/04-architecture/batch-live-symmetry.md`](/codex/04-architecture/batch-live-symmetry.md)
