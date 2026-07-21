---
doc_type: plan
title: live-defi-rollout-may-23-2026
summary:
status: complete
nature: record
asset_group: defi
stage: [meta]
repos: [alerting-service, deployment-api, execution-service]
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

## Deferred work — migrated to: `plans/active/defi_consolidated_closeout_2026_07_18.md` — successor:

defi_consolidated_closeout_2026_07_18 (the 13 open success-criteria items — live carry-archetype trading, 6-venue perp
universe live, cross-venue spot/perp/future legs, custody, live alerting, live observability, auto-recovery, kill
switches, batch-vs-live reconciliation, AWS↔GCP parity — trace forward through the 2026-05-08 supersession into
`defi_master_2026_05_07.md` (itself now archived, no longer on disk). That file's DeFi-live scope is now consolidated
into this active plan, which explicitly self-describes as aggregating "every open defi + defi-touching IS/MTDS
plan/issue into ONE ordered pass" — the direct-line living DeFi umbrella. Verified via grep — real successor, not a
guess.

# Epic — Live DeFi Rollout (May 23 2026)

> **🔴 SUPERSEDED 2026-05-08** — folded into [`defi_master_2026_05_07.md`](../active/defi_master_2026_05_07.md) §
> "May-23 deliverable" per operator direction (3-layer master+epic+cutover-master collapses to 2-layer). This file is
> archived; content remains verbatim for archaeology. **Edit the master, not this file.**

## Why this epic exists

This is the **headline live deliverable** for May 23 2026: real wallet, real capital, real fills, ≥7 continuous days of
production trading. It absorbs all CARRY archetypes (staked-basis, vanilla-basis, cross-venue carry) — the operator's
2026-05-08 direction lifted carry out of price-arbitrage scope and folded it here, since carry's hedge legs span CME +
CeFi + DeFi spot/perp/future combos and the live infra is what actually unlocks it.

## End-state at May 23 (success criteria)

- [ ] **Live trading on real wallet** for **carry archetypes** (staked-basis carry + vanilla-basis carry + cross-venue
      carry) for ≥7 continuous days, on representative capital (size TBD per operator).
- [ ] **Six perp venues live**: Bybit, Deribit, Binance, OKX (CeFi) + Hyperliquid, Aster (DeFi DEXs). Hedge legs route
      across all six.
- [ ] **Cross-venue spot/perp/future legs live** for carry: CME futures + ETF + DeFi spot + CeFi perp + DeFi perp combos
      tradable end-to-end through the unified pipeline.
- [ ] **Custody integrated**: Copper for DeFi side (codex `copper-custody-integration.md`); CEFFU for Binance
      institutional flow (manual handoff acceptable per Q&A 3 of master plan); cross-wallet transfer paths verified.
- [ ] **Live alerting active**: data freshness + P&L deviation + position breaches + circuit-breaker trips + kill-switch
      activations all alert through alerting-service to operator + DART.
- [ ] **Live observability complete**: every VM emits structured events to GCS event stream; deployment-UI tails events
      without SSH; per-instrument progress events with row counts so silent-success-with-zero-output is detectable.
- [ ] **Auto-recovery wired** for known transient failure classes (RPC blip, CEX rate-limit, oracle staleness) per codex
      `autonomous-recovery-matrix.md`.
- [ ] **Kill switches wired** per archetype: position-limit breach, P&L drawdown threshold, oracle-feed-stale,
      counterparty-exposure cap. Operator-pullable from DART.
- [ ] **Batch-vs-live reconciliation running**: per-archetype P&L diff + per-trade fill comparison nightly.
- [ ] **AWS↔GCP parity**: live trading + monitoring runnable on AWS for at least one carry archetype (cloud-parity
      proof; full-scale AWS NOT required).

## What's IN scope

- All three carry-family archetypes: `carry_staked_basis` (lead — recursive LST + perp short hedge), `carry_basis_perp`
  (vanilla basis), `cross_venue_carry` (CME futures vs CeFi/DeFi spot/perp combos).
- Custody (Copper + CEFFU manual handoff), live treasury flows, cross-wallet transfer paths.
- Live trading guardrails: circuit breakers, kill switches, alerting rules, auto-recovery for transient failures.
- 6-venue perp universe (CeFi 4 + DeFi DEX 2) + CME futures + ETF spot venues + DeFi spot DEXs (LST oracles for
  staked-basis variant).
- AWS↔GCP parity proof at live-trading layer (single archetype, not full scale).
- DART manual-trade lane wired so operator can run trades pre-automation (3-day manual → 7-day automated default per Q&A
  5 of master plan).
- Live observability + event streaming + per-instrument progress events.

## What's OUT of scope (shipping later)

- Full strategy mesh launch (only carry archetypes go live; `leveraged_funding_arb` archetype CAN slip if Week 3 is
  tight per master plan risk register).
- Full AWS scale (only single-archetype proof needed).
- ML-driven DeFi archetypes (DeFi stays rules-based this cycle).
- Other archetype families (price-arb, prediction, sports — those have their own epics, mostly batch-only this cycle).

## Sub-plans this epic consumes

| Path                                                                                                                                                                         | Role                                                                                                             | Status |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- | ------ |
| [`active/defi_master_2026_05_07`](../active/defi_master_2026_05_07.md)                                                                                                       | DeFi pipeline umbrella (folds defi_e2e + defi_pipeline_extension + leveraged_leg + carry_staked_basis archetype) | Active |
| [`active/defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07`](../active/defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md)                           | DeFi archetype canonicalisation + venue matrix                                                                   | Active |
| [`active/aws_migration_defi_first_2026_05_07`](../active/aws_migration_defi_first_2026_05_07.md)                                                                             | AWS↔GCP parity for DeFi-first migration (data + batch + live-trading layer)                                      | Active |
| [`active/alerting_service_live_rules_2026_05_07`](../active/alerting_service_live_rules_2026_05_07.md)                                                                       | Live alerting rules (was the only Group F service with no plan pre-2026-05-06 audit)                             | Active |
| [`active/fund_administration_service_and_pooled_subscription_redemption_2026_04_20`](../active/fund_administration_service_and_pooled_subscription_redemption_2026_04_20.md) | Fund admin + capital flow (treasury / subs+reds)                                                                 | Active |
| [`cefi_master_2026_05_07`](./cefi_master_2026_05_07.md)                                                                                                                      | CeFi venues for hedge legs (Bybit / Deribit / Binance / OKX); shared with `cefi_ml` epic                         | Active |
| [`strategy_and_dart_master_2026_05_07`](./strategy_and_dart_master_2026_05_07.md)                                                                                            | Strategy v2 + DART manual-trade lane                                                                             | Active |
| [`instruments_live_master_2026_05_08`](./instruments_live_master_2026_05_08.md)                                                                                              | Live instrument refresh / lifecycle for active venues                                                            | Active |
| [`active/live_pipeline_mtds_mdps_features_2026_05_08`](../active/live_pipeline_mtds_mdps_features_2026_05_08.md)                                                             | Live pipeline activation (MTDS/MDPS/features) — gates live-mode P&L attribution                                  | Active |
| [`infrastructure_master_2026_05_07`](./infrastructure_master_2026_05_07.md)                                                                                                  | Infrastructure umbrella (deployment, observability, AWS) — also referenced from cross_cutting epic               | Active |

## Cross-epic handshakes

- **Depends on:** `cross_cutting_may_23_2026` for strategy catalogue completeness (carry archetypes × all venue combos
  enumerated), strategy IDs, client wiring, UI replication of manual-trade DART, infrastructure baseline.
- **Provides to:** `cefi_ml_may_23_2026` shares the CeFi venue connectivity (Bybit / Deribit / Binance / OKX) — both
  epics live across the same 4 CeFi venues by May 23. Coordination point: same `execution-service` adapters, same
  alerting rules, same kill-switch wiring; ML signal vs rules-based archetype differ only at the strategy-decision
  layer.
- **Blocks:** Nothing else on May 23 — this is the headline. Subsequent archetype launches (post-May-23) wait for live
  proof here.

## Cross-cutting concerns inherited

See [`cross_cutting_may_23_2026.epic.md`](./cross_cutting_may_23_2026.epic.md) for the full list. Specific to this epic:

- **Strategy catalogue (HARD)**: every carry archetype × venue combo enumerated, so the universe is visible even for
  archetypes not launching this cycle.
- **Strategy IDs**: stable, traceable per-archetype IDs so live trades + reconciliation can attribute correctly.
- **Clients**: client/account configuration wired for live-trading capital allocation.
- **UI replication (DART)**: every live trade is also reproducible as a manual trade through DART for operator control.
- **Infrastructure**: deployment maturity, environments, speed, stability — ALL non-negotiable for live trading.

## Open questions

- [ ] **Manual-trade gating duration** (Q&A 5 of master plan). Default 3-day manual → 7-day automated. Resolve before
      May 18.
- [ ] **research-service repo decision** (Q&A 6 of master plan). Default: fold into deployment-api unless scope grows.
- [ ] **Is `leveraged_funding_arb` strictly required for May 23, or is it the fallback if carry slips?** Master plan
      risk register says it can slip; confirm whether to keep it on this epic's end-state or drop to a follow-up.

## See also

- [`master_to_live_defi_2026_05_23`](../active/master_to_live_defi_2026_05_23.md) — May-23 cutover master
  (umbrella-of-epics)
- [`codex/04-architecture/copper-custody-integration.md`](../../codex/04-architecture/copper-custody-integration.md)
- [`codex/04-architecture/alerting-batch-live.md`](../../codex/04-architecture/alerting-batch-live.md)
- [`codex/04-architecture/autonomous-recovery-matrix.md`](../../codex/04-architecture/autonomous-recovery-matrix.md)
