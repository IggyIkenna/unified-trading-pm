---
title: Global Ledger Architecture
type: architecture
status: active
created: 2026-05-21
last_reviewed: 2026-05-22
scope: [engineer, admin]
---

# Global Ledger Architecture

> **[DELTA 2026-05-23]** **UAC schema Phase 2 DONE** — `LedgerRow` + 4 SSOT ledger aliases + 5 StrEnum enums shipped at
> `unified-api-contracts@008e59ce`. `parent_event_id` linkage + `accrual_period` conventions codified in class
> docstring. Cross-client HARD RULE enforced by **structural single-`client_id` field** (schema default makes
> same-client intent the only representable intent) + **`TransferCoordinator.execute()` runtime gate** at
> `execution-service/transfer_coordinator.py:241` (raises `CrossClientTransferForbiddenError`). Note: enforcement is NOT
> via `@model_validator` — see `codex/04-architecture/client-funds-isolation.md` for the authoritative enforcement
> table. Five-service audit complete (2026-05-23); gap analysis in
> `plans/audit/results/global_ledger_audit_*_2026_05_23.md`. Migration sub-plan forthcoming (Phase 5-6 of discovery).
> **Discovery plan:** `plans/active/global_ledger_pnl_attribution_discovery_2026_05_21.md`.

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

## UAC Contract

```python
from unified_api_contracts.canonical.crosscutting.ledger import (
    LedgerRow,
    InstructionLedger,  # = LedgerRow (semantic alias, not a subclass)
    PassiveLedger,
    TreasuryLedger,
    PricingLedger,
    CrossClientTransferForbiddenError,
    assert_no_cross_client_transfer,
    EventOrigin, EventType, AssetClass, Direction, OptionRight,
)
```

Enum value surfaces: see `codex/02-data/ledger-event-taxonomy.md`.

## Current-State Gaps (Audit 2026-05-23)

Five-service audit (`plans/audit/results/global_ledger_audit_*_2026_05_23.md`) found:

| Service              | Key P0 gap                                                                                                                                       |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| execution-service    | Emission bypasses `_resolve_policy_output_data_type`; `client_id` absent from `log_event`; `build_attribution_rows()` stub                       |
| strategy-service     | `unrealized_pnl` always 0 (MarkPrice not bridged); fees not deducted; PnL time-series API always 404                                             |
| MTDS                 | `dividend_rate` MISSING; `rho` MISSING; `mid` must be derived from book_snapshot                                                                 |
| instruments-service  | `exercise_style`, `settlement_style`, `dividend_schedule` absent from `InstrumentRecord`; `rocket_pool.py` missing `source_archive_url_template` |
| client-reporting-api | `realised_pnl` hardcoded "0.00"; no canonical ledger joins; 10 HIGH severity gaps                                                                |

These gaps drive the writer-side gap analysis in Phase 4 of the discovery plan and will be addressed in the migration
sub-plan.

## `rebase_rate` — delta-computation strategy (Phase 2 DESIGN spec)

**Applicable instruments**: LST/LRT only (`is_rebasing=True` in `InstrumentRecord`). `None` for all others.

### Decision: MTDS-derived, per-consecutive-snapshot delta

| Option                          | Formula                                                | Recommendation                                                                                                          |
| ------------------------------- | ------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------- |
| **Per-snapshot delta (chosen)** | `(rate_t - rate_{t-1}) / rate_{t-1}` annualised        | Reflects latest rate; consistent cadence with MTDS tick frequency; smooth LST curve makes per-snapshot noise negligible |
| Daily-checkpoint delta          | `(eod_rate_t - eod_rate_{t-1}) / eod_rate_{t-1}` × 365 | Adds 12–24h latency; requires MTDS to distinguish "end-of-day" snapshot — not available in IS `lst_rates` schema        |

| Owner-repo option         | Pros                                                                                                    | Recommendation                                                                                                                 |
| ------------------------- | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| **MTDS-derived (chosen)** | Consistent with `dividend_yield` architecture; IS stays pure reference data; no IS↔MTDS contract drift | ✓                                                                                                                              |
| IS-write-time             | Closer to source; no MTDS state                                                                         | Violates IS reference-only contract (`codex/04-architecture/instruments-service-as-ssot-for-mtds.md`); blurs contract boundary |

### Formula (operator-ACK pending 2026-05-24)

```
annualised_rebase_rate = ((rate_current - rate_prev) / rate_prev)
                         × (seconds_per_year / (t_current - t_prev).total_seconds())
```

Where:

- `rate_current`, `rate_prev` = consecutive `exchange_rate` rows from IS `lst_rates` for the same
  `(instrument_id, chain)`
- `t_current - t_prev` = elapsed time between snapshots (IS write timestamps)
- `seconds_per_year = 365.25 × 86400`
- Result stored as annualised continuous rate (dimensionless); emitted on `PricingLedger.MARK_UPDATE` row

### Invariant: IS cumulative column stays untouched

`lst_rates.exchange_rate` (cumulative) is the SSOT. The derived `rebase_rate` lives only in `PricingLedger`. Any code
that writes a derived `delta_exchange_rate` column back to IS `lst_rates` is a HARD RULE violation.

### Edge cases

| Case                             | Handling                                                     |
| -------------------------------- | ------------------------------------------------------------ |
| First snapshot (no prior row)    | Emit `None` — insufficient history for delta                 |
| Gap > 48h between snapshots      | Emit `None` — stale; IS feed outage or instrument delisted   |
| Negative delta (rebase rate < 0) | Valid for negative-rebase LRTs; emit as-is (can be negative) |
| Non-LST instrument               | Emit `None`                                                  |

**SSOT**: `codex/04-architecture/global-ledger-architecture.md` (this section) +
`codex/02-data/ledger-event-taxonomy.md` § `rebase_rate`. **CODE gated on operator-ACK**: see
`plans/active/pricing_ledger_carry_rates_mtds_2026_06_01.md` Phase 2 risk callout.

---

## Composes With

- `codex/04-architecture/client-funds-isolation.md` — HARD RULE: funds never cross client boundaries; ledger rows always
  carry `client_id`
- `codex/04-architecture/per-client-isolation-architecture.md` — each ClientWorker computes derived ledgers in isolation
- `codex/04-architecture/client-reporting-architecture.md` — client-reporting-api consumes PnL + PnLAttribution
- `codex/02-data/ledger-event-taxonomy.md` — EventOrigin / EventType / AssetClass / Direction / OptionRight enum values
- `plans/epics/execution_master.md` — InstructionLedger + PassiveLedger writers (active path)
- `plans/epics/strategy_master.md` — PositionLedger + ExposureLedger + PnLLedger + PnLAttributionLedger compute home
- `plans/epics/mtds_mdps_master.md` — PricingLedger authoring
