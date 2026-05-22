---
title: Global Ledger Architecture
type: architecture
status: active
created: 2026-05-21
last_reviewed: 2026-05-22
scope: [engineer, admin]
---

# Global Ledger Architecture

> **[DELTA 2026-05-22]** **Current state:** Discovery phase active
> (`global_ledger_pnl_attribution_discovery_2026_05_21.md`). The architecture described below is the target model —
> implementation sub-plans are spawned from the discovery. **Planned delta:** Full PnL attribution architecture per
> `plans/epics/global_ledger_pnl_attribution_master.md`. **Target architecture:** Four SSOT ledgers + four derived
> materialised views + one filtered view, as documented below.

## Overview

The Global Ledger is the canonical event-sourced accounting layer from which position, exposure, PnL, and PnL
attribution for **all clients and all archetypes** are derived. It spans 5 services as writers and many more as readers.

Epic: `plans/epics/global_ledger_pnl_attribution_master.md`. Discovery:
`plans/active/global_ledger_pnl_attribution_discovery_2026_05_21.md`.

**UAC home:** `unified_api_contracts.canonical.crosscutting.ledger/`

---

## Event Taxonomy

Every row in InstructionLedger or PassiveLedger is one of two origins:

| Origin                 | Event types                                                                                                                                                                                                               |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `instruction` (active) | trade, swap, transfer, stake, unstake, supply, withdraw, borrow, repay, bridge, wrap, unwrap, early_exercise, cash_out, deposit, withdrawal_to_bank, custody_move, fx_conversion                                          |
| `passive` (automatic)  | funding, rebase, interest_accrual, staking_reward, validator_reward, mev_reward, airdrop, dividend, coupon, expiry_settlement, sports_resolution, prediction_resolution, liquidation, slashing, gas_refund, auto_compound |

---

## Four SSOT Ledgers (Append-Only, Event-Sourced)

| Ledger            | Writer                                                         | Cardinality             | Notes                                                                                 |
| ----------------- | -------------------------------------------------------------- | ----------------------- | ------------------------------------------------------------------------------------- |
| InstructionLedger | execution-service                                              | ~thousands/day          | Append-only; enrichments arrive as separate rows with `parent_event_id`               |
| PassiveLedger     | execution-service synthesiser + on-chain/venue listeners       | ~thousands–millions/day | Synthesisable from instrument metadata + clock for backtest parity                    |
| TreasuryLedger    | execution-service (operator-tools subset)                      | ~tens/day               | Cohort of InstructionLedger; may be own table for accounting SLA — discovery decision |
| PricingLedger     | MTDS (price/mid/IV/greeks) + instruments-service (carry rates) | ~millions/day           | Instrument-agnostic write; client/strategy-agnostic                                   |

---

## Four Derived Ledgers (Materialised Views)

| Ledger               | Definition                                                                                                                                | Owner module                                                         |
| -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| PositionLedger       | `Σ delta` per `(client_id, account, asset_canonical_id)` over time                                                                        | `strategy_service/position/`                                         |
| ExposureLedger       | PositionLedger ⨝ PricingLedger → notional + delta-adj + vega + theta exposure by underlying/venue/client                                  | `strategy_service/risk/core/exposure_aggregator.py`                  |
| PnLLedger            | Δ(cash + MTM value of positions) per period                                                                                               | `strategy_service/pnl/engine/`                                       |
| PnLAttributionLedger | Decomposition: delta-PnL + gamma-PnL + theta-PnL + vega-PnL + carry-PnL + funding-PnL + settlement-PnL + fees + slippage + gas + residual | `strategy_service/pnl/engine/breakdown.py` + `reward_attribution.py` |

---

## One Filtered View

**RiskView** — filtered slice of PassiveLedger (liquidation, slashing, margin-call, kill-switch-trip) augmented with
Position + Exposure snapshot at event time. Consumed by alerting-service + DART monitoring surface.

---

## Service Writer / Reader Map

**Writers (5 services)**:

- `execution-service` — InstructionLedger (active execution path) + PassiveLedger (synthesiser + on-chain listener) +
  TreasuryLedger
- `MTDS` — PricingLedger (price/mid/IV/greeks)
- `instruments-service` — PricingLedger (carry rates per instrument)
- `strategy-service` — PositionLedger + ExposureLedger + PnLLedger + PnLAttributionLedger (derived compute)

**Readers (many services)**:

- DART / deployment-api — PnL + PnLAttribution for operator dashboard
- alerting-service — RiskView for liquidation/slashing alerting
- client-reporting-api — PnL + PnLAttribution for per-client reporting
- strategy-service backtest + live engines — reads PricingLedger for historical MTM

---

## VM Prefix Additions (Subject to Discovery Confirmation)

Net-new runtime artifacts from the discovery plan declare VM prefixes in
`deployment-service/scripts/vm/vm_zombie_watchdog.py`:

| VM prefix           | LifecycleClass        | Notes                                                                                            |
| ------------------- | --------------------- | ------------------------------------------------------------------------------------------------ |
| `ledger-reconcile-` | `SCHEDULED_RECURRING` | Nightly venue-vs-ledger reconciliation; may absorb into `batch-live-recon-cron-`                 |
| `passive-listener-` | `LONG_LIVED_LIVE`     | On-chain emission listening if dedicated; discovery decides vs MTDS/execution-service absorption |

Derived ledger compute runs on existing `strategy-paper-*` / `strategy-live-*` / `client-reporting-cutover-*` prefixes.

---

## Continuous Verification

| Surface                                              | Verification                      | Cadence      |
| ---------------------------------------------------- | --------------------------------- | ------------ |
| InstructionLedger ⟷ venue execution reports          | Daily reconciliation cron         | T+1 daily    |
| PassiveLedger synthesiser ⟷ on-chain/venue emissions | Per-event divergence check        | Per emission |
| PricingLedger ⟷ MTDS canonical prices                | Snapshot cross-check              | Hourly       |
| Derived ledgers ⟷ SSOT replay                        | Backfill replay = production view | Pre-deploy   |
| RiskView liquidation rows ⟷ alerting-service pages   | End-to-end smoke                  | Per event    |

---

## Composes With

- `codex/04-architecture/client-funds-isolation.md` — HARD RULE: funds never cross client boundaries; ledger rows always
  carry `client_id`
- `codex/04-architecture/per-client-isolation-architecture.md` — each ClientWorker computes derived ledgers in isolation
- `codex/04-architecture/client-reporting-architecture.md` — client-reporting-api consumes PnL + PnLAttribution
- `plans/epics/execution_master.md` — InstructionLedger + PassiveLedger writers (active path)
- `plans/epics/strategy_master.md` — PositionLedger + ExposureLedger + PnLLedger + PnLAttributionLedger compute home
- `plans/epics/mtds_mdps_master.md` — PricingLedger authoring
